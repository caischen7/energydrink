#!/usr/bin/env python3
"""Build the store map: where the PDI panel sells energy drinks.

Feeds `stores.html`. Reduces `pdi_stores` (the store dimension: STATE, CITY,
ZIP_CODE, LATITUDE, LONGITUDE, STORE_CHAIN_NAME) joined to trailing-12-month
sales from `pdi_daily_agg` into a small JSON of aggregates.

    python data/scripts/build_stores_map.py --dry-run   # cost only
    python data/scripts/build_stores_map.py             # needs BQ_TOKEN
    python data/scripts/build_stores_map.py --sample    # offline placeholder

Reads BigQuery via a pasted OAuth token in BQ_TOKEN, same as
build_flavor_explorer.py. stdlib only. Idempotent.

WHY THE BROWSER NEVER GETS STORE POINTS
---------------------------------------
PDI is licensed and must not leave the warehouse. `build_flavor_explorer.py`
states the rule this file inherits: "No SKU rows, no store data, no GTINs reach
the browser." A map of 18,300 exact store coordinates would break that rule
outright - it is the panel roster, republished, and a competitor could read
PDI's client list straight off it.

So two things happen here, and neither is cosmetic:

1. **Points are binned to a GRID_DEG grid** before they are written. A cell is a
   count and a revenue total, not a store. Exact LATITUDE/LONGITUDE, STORE_ID,
   ZIP_CODE and per-store chain never appear in the output.
2. **Cells holding fewer than MIN_CELL stores are dropped.** A 1-store cell IS
   an exact store location wearing a grid cell's clothes, and its revenue is
   that store's revenue. The threshold is what makes the binning mean anything.

This costs rural coverage - a cell in Wyoming may hold one store and vanish -
and that is the honest trade. `meta.suppressed` reports how many stores were
dropped so the page can say so rather than implying the map is complete.

State rollups are exempt: a state total over hundreds of stores discloses
nothing about any one of them.

WHAT THE MAP CANNOT TELL YOU
----------------------------
PDI is convenience-channel only and roughly an 8.6% sample of it (assumption D1
in docs/ASSUMPTIONS.md, rated LOW confidence - no selection criteria are
published). The panel also GROWS 3.89x across 2019-2025, from 5,148 active
stores to 20,022, so where the map is dense is partly where PDI signed chains
and not only where the category sells.

That is why every metric here is trailing-twelve-month, on ONE window. A map of
change over time would be mostly panel growth, drawn as demand, and there is no
way from inside this data to tell the two apart.
"""
import argparse
import collections
import csv
import json
import math
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "public/data/stores_map.json")
PLANTS = os.path.join(ROOT, "data/osm/bottling_candidates.csv")
PROJECT = "msbai-capstone-energydrinks"

# Trailing twelve months. Matches the window add_segments.py uses so the two
# pages' revenue totals are comparable.
FIRST, LAST = "2025-08-01", "2026-07-31"

GRID_DEG = 0.1    # ~11 km of latitude; ~8.5 km of longitude at 40N
MIN_CELL = 4      # stores per cell, below which the cell is dropped entirely
#
# Both were swept against the sample: 0.05deg suppresses 67% of stores, 0.1deg
# 12%, 0.25deg under 2% but coarse enough to merge neighbouring metros. 0.1/4
# keeps ~88% of stores at a median 7 stores per kept cell.
#
# THAT SWEEP RAN ON SYNTHETIC POINTS. Real retail clusters harder in cities and
# thinner in the countryside, so re-run the sweep on the real rows the first
# time this executes against BigQuery and move the floor if rural coverage
# collapses - meta.stores_suppressed is the number to watch.
TOP_BRANDS = 6    # brands kept per state


# ---------------------------------------------------------------------- SQL --
#
# Two scans, not one. Both slice the same twelve months of `pdi_daily_agg`
# partitions and both name only the columns they need - BigQuery bills
# referenced columns x rows, so naming them is what keeps a 420 GB table down to
# roughly 15-20 GB per query. --dry-run prints the real number before you spend.
#
# The store rollup does NOT need GTIN and the brand rollup does NOT need
# LATITUDE: keeping them apart is cheaper than one wide join that carries every
# column through a GROUP BY at store x brand grain.

STORE_SQL = f"""
WITH sales AS (
  SELECT STORE_ID,
         SUM(TOTAL_REVENUE_AMOUNT) AS rev,
         SUM(QUANTITY)             AS units
  FROM `{PROJECT}.energy_drinks.pdi_daily_agg`
  WHERE DATE BETWEEN '{FIRST}' AND '{LAST}'
  GROUP BY STORE_ID
)
SELECT st.STATE            AS state,
       st.LATITUDE         AS lat,
       st.LONGITUDE        AS lon,
       st.STORE_CHAIN_NAME AS chain,
       s.rev, s.units
FROM sales s
JOIN `{PROJECT}.energy_drinks.pdi_stores` st USING (STORE_ID)
WHERE st.LATITUDE IS NOT NULL AND st.LONGITUDE IS NOT NULL
"""

# State x brand, for the per-state top-brand list. Brand lives on the product
# dimension, so this one pays for the GTIN join.
BRAND_SQL = f"""
SELECT st.STATE AS state,
       g.brand  AS brand,
       SUM(d.TOTAL_REVENUE_AMOUNT) AS rev
FROM `{PROJECT}.energy_drinks.pdi_daily_agg` d
JOIN `{PROJECT}.energy_drinks.pdi_stores` st USING (STORE_ID)
JOIN (
  SELECT GTIN, ANY_VALUE(BRAND) AS brand
  FROM `{PROJECT}.energy_drinks.pdi_master_gtin`
  GROUP BY GTIN
) g USING (GTIN)
WHERE d.DATE BETWEEN '{FIRST}' AND '{LAST}'
  AND st.STATE IS NOT NULL
GROUP BY state, brand
"""


def bq(sql, token, dry=False):
    body = json.dumps({"query": sql, "useLegacySql": False,
                       "dryRun": dry, "timeoutMs": 180000}).encode()
    req = urllib.request.Request(
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}/queries",
        data=body, headers={"Authorization": "Bearer " + token,
                            "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=300))


def rows_of(res, token):
    """Collect every page of a query result."""
    fields = [f["name"] for f in res["schema"]["fields"]]
    out, job = [], res["jobReference"]["jobId"]
    while True:
        for r in res.get("rows", []):
            out.append(dict(zip(fields, [c["v"] for c in r["f"]])))
        page = res.get("pageToken")
        if not page:
            return out
        u = (f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}"
             f"/queries/{job}?pageToken={page}&timeoutMs=180000")
        res = json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers={"Authorization": "Bearer " + token}),
            timeout=300))


# ------------------------------------------------------------------ states --
#
# code -> (name, centroid lat, centroid lon, spread deg, population millions).
#
# The centroid is where the state's bubble is drawn; `spread` is only used by
# --sample to scatter placeholder cells. Population is also sample-only - the
# real path never uses it, because weighting real revenue by population would be
# assuming the answer the map exists to show.
STATES = {
    "AL": ("Alabama", 32.8, -86.8, 1.6, 5.1),      "AK": ("Alaska", 64.0, -152.0, 3.0, 0.73),
    "AZ": ("Arizona", 34.3, -111.7, 1.8, 7.4),     "AR": ("Arkansas", 34.9, -92.4, 1.5, 3.0),
    "CA": ("California", 37.2, -119.5, 3.2, 39.0), "CO": ("Colorado", 39.0, -105.5, 1.8, 5.9),
    "CT": ("Connecticut", 41.6, -72.7, 0.5, 3.6),  "DE": ("Delaware", 39.0, -75.5, 0.4, 1.0),
    "DC": ("District of Columbia", 38.9, -77.0, 0.1, 0.7),
    "FL": ("Florida", 28.6, -82.4, 2.2, 22.6),     "GA": ("Georgia", 32.6, -83.4, 1.8, 11.0),
    "HI": ("Hawaii", 20.8, -156.3, 1.0, 1.4),      "ID": ("Idaho", 44.4, -114.6, 2.0, 1.9),
    "IL": ("Illinois", 40.0, -89.2, 2.0, 12.6),    "IN": ("Indiana", 39.9, -86.3, 1.5, 6.9),
    "IA": ("Iowa", 42.1, -93.5, 1.4, 3.2),         "KS": ("Kansas", 38.5, -98.4, 1.7, 2.9),
    "KY": ("Kentucky", 37.5, -85.3, 1.6, 4.5),     "LA": ("Louisiana", 31.1, -92.0, 1.4, 4.6),
    "ME": ("Maine", 45.4, -69.2, 1.3, 1.4),        "MD": ("Maryland", 39.0, -76.8, 0.8, 6.2),
    "MA": ("Massachusetts", 42.3, -71.8, 0.7, 7.0), "MI": ("Michigan", 44.3, -85.4, 1.8, 10.0),
    "MN": ("Minnesota", 46.3, -94.3, 2.0, 5.7),    "MS": ("Mississippi", 32.7, -89.7, 1.5, 2.9),
    "MO": ("Missouri", 38.4, -92.5, 1.8, 6.2),     "MT": ("Montana", 47.0, -109.6, 2.4, 1.1),
    "NE": ("Nebraska", 41.5, -99.8, 1.8, 2.0),     "NV": ("Nevada", 39.3, -116.6, 2.2, 3.2),
    "NH": ("New Hampshire", 43.7, -71.6, 0.7, 1.4), "NJ": ("New Jersey", 40.2, -74.7, 0.7, 9.3),
    "NM": ("New Mexico", 34.4, -106.1, 1.9, 2.1),  "NY": ("New York", 42.9, -75.5, 1.8, 19.6),
    "NC": ("North Carolina", 35.5, -79.4, 1.9, 10.8), "ND": ("North Dakota", 47.4, -100.5, 1.6, 0.8),
    "OH": ("Ohio", 40.3, -82.8, 1.5, 11.8),        "OK": ("Oklahoma", 35.6, -97.5, 1.8, 4.1),
    "OR": ("Oregon", 43.9, -120.6, 1.9, 4.2),      "PA": ("Pennsylvania", 40.9, -77.8, 1.6, 13.0),
    "RI": ("Rhode Island", 41.7, -71.6, 0.3, 1.1), "SC": ("South Carolina", 33.9, -80.9, 1.3, 5.4),
    "SD": ("South Dakota", 44.4, -100.2, 1.7, 0.9), "TN": ("Tennessee", 35.8, -86.3, 2.0, 7.1),
    "TX": ("Texas", 31.4, -99.3, 3.4, 30.5),       "UT": ("Utah", 39.3, -111.7, 1.6, 3.4),
    "VT": ("Vermont", 44.1, -72.7, 0.6, 0.65),     "VA": ("Virginia", 37.5, -78.8, 1.8, 8.7),
    "WA": ("Washington", 47.4, -120.4, 1.6, 7.8),  "WV": ("West Virginia", 38.6, -80.6, 1.1, 1.8),
    "WI": ("Wisconsin", 44.6, -89.7, 1.6, 5.9),    "WY": ("Wyoming", 43.0, -107.5, 1.7, 0.58),
}
BY_NAME = {v[0].lower(): k for k, v in STATES.items()}


def state_code(raw):
    """PDI's STATE encoding is unverified - nothing in this repo has ever read
    the column, so it may hold 'CA' or 'California'. Accept either rather than
    silently dropping half the country on a guess."""
    s = (raw or "").strip()
    if not s:
        return None
    if len(s) == 2 and s.upper() in STATES:
        return s.upper()
    return BY_NAME.get(s.lower())


# ------------------------------------------------------------------ reduce --

def reduce_rows(store_rows, brand_rows, source):
    """Store rows -> grid cells + state rollups. See the module docstring: this
    is the step that makes the output publishable, so --sample runs through it
    unchanged rather than writing a payload the real path would never produce."""
    cells = collections.defaultdict(lambda: [0, 0.0])
    states = collections.defaultdict(lambda: {"stores": 0, "rev": 0.0, "units": 0.0})
    no_state = 0

    for r in store_rows:
        try:
            lat, lon = float(r["lat"]), float(r["lon"])
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        rev = float(r.get("rev") or 0)
        code = state_code(r.get("state"))
        if code:
            s = states[code]
            s["stores"] += 1
            s["rev"] += rev
            s["units"] += float(r.get("units") or 0)
        else:
            no_state += 1
        c = cells[(math.floor(lat / GRID_DEG), math.floor(lon / GRID_DEG))]
        c[0] += 1
        c[1] += rev

    kept, suppressed, supp_cells = [], 0, 0
    for (ilat, ilon), (n, rev) in cells.items():
        if n < MIN_CELL:
            suppressed += n
            supp_cells += 1
            continue
        kept.append([round((ilat + 0.5) * GRID_DEG, 4),
                     round((ilon + 0.5) * GRID_DEG, 4), n, round(rev)])
    kept.sort(key=lambda c: -c[3])

    by_state = collections.defaultdict(dict)
    for r in brand_rows:
        code = state_code(r.get("state"))
        b = (r.get("brand") or "").strip()
        if code and b:
            by_state[code][b] = by_state[code].get(b, 0.0) + float(r.get("rev") or 0)

    out_states = []
    for code, s in states.items():
        name, lat, lon, _spread, _pop = STATES[code]
        top = sorted(by_state.get(code, {}).items(), key=lambda kv: -kv[1])[:TOP_BRANDS]
        out_states.append({
            "code": code, "name": name, "lat": lat, "lon": lon,
            "stores": s["stores"], "rev": round(s["rev"]), "units": round(s["units"]),
            "rev_per_store": round(s["rev"] / s["stores"]) if s["stores"] else 0,
            "brands": [{"b": b, "r": round(v)} for b, v in top],
        })
    out_states.sort(key=lambda s: -s["rev"])

    total_stores = sum(s["stores"] for s in out_states) + no_state
    return {
        "generated_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "meta": {
            "window": f"trailing 12 months, {FIRST} to {LAST}",
            "grid_deg": GRID_DEG,
            "min_cell": MIN_CELL,
            "stores_mapped": total_stores,
            "stores_suppressed": suppressed,
            "cells_suppressed": supp_cells,
            "cells": len(kept),
            "no_state": no_state,
            "rev_total": round(sum(s["rev"] for s in out_states)),
            "coverage": (
                "PDI is convenience-channel only and roughly an 8.6% sample of that "
                "channel (assumption D1, docs/ASSUMPTIONS.md - LOW confidence, no "
                "selection criteria published). The panel also grew 3.89x across "
                "2019-2025, so density on this map is partly where PDI signed chains "
                "rather than only where the category sells. Read it as the shape of "
                "one panel, not as a census of US convenience retail."
            ),
            "privacy": (
                f"Stores are binned to a {GRID_DEG}-degree grid (~11 km) and cells "
                f"holding fewer than {MIN_CELL} stores are dropped. No store ID, "
                "exact coordinate, ZIP or per-store chain leaves the warehouse."
            ),
        },
        "states": out_states,
        "cells": kept,
        "plants": plants(),
    }


def plants():
    """The supply side, and the only REAL geography this page has today.

    122 candidate bottling plants from OpenStreetMap, already committed at
    data/osm/bottling_candidates.csv. Independent of PDI and independent of
    --sample, so this layer is measured even when the store layer is not.

    Read data/osm/README.md before drawing conclusions: it is not a census,
    99 of the 122 were matched on the word "bottling" in a name, and a plant
    nobody has mapped is simply absent."""
    if not os.path.exists(PLANTS):
        return []
    out = []
    for r in csv.DictReader(open(PLANTS)):
        try:
            lat, lon = float(r["lat"]), float(r["lon"])
        except (TypeError, ValueError, KeyError):
            continue
        name = (r.get("name") or "").strip()
        op = (r.get("operator") or "").strip()
        tagged = bool((r.get("product") or r.get("man_made") or
                       r.get("industrial") or "").strip())
        out.append([round(lat, 4), round(lon, 4), name or op or "Unnamed site",
                    op, 1 if tagged else 0])
    return out


# ------------------------------------------------------------------ sample --
#
# A DETERMINISTIC PLACEHOLDER, NOT A MEASUREMENT.
#
# The real store geography lives in `pdi_stores` in BigQuery and is licensed;
# it is not in this repo and cannot be committed. This generator exists so
# `stores.html` renders, can be styled, and can be tested by npm run check
# before anyone has a token - the same reason data/openfoodfacts/ and
# data/wikipedia/ ship generated samples (see their READMEs).
#
# It writes `"source": "sample"`, and stores.js refuses to draw the map without
# a standing banner when it sees that. Nothing here should ever be quoted.
#
# Store counts are scattered on population, which is a crude proxy and wrong in
# exactly the way the real data would be interesting: PDI's panel is chain-led,
# so its real density follows Casey's and Circle K footprints, not people.

BRANDS = ["Red Bull", "Monster", "Celsius", "Alani Nu", "Rockstar", "NOS",
          "C4", "Ghost Energy", "Bang", "Reign", "Prime", "Guayaki",
          "Rip It", "Venom Energy", "Full Throttle"]

# Mild regional tilt so the placeholder is shaped like the finding the real data
# already produced ("Regional strongholds are real" - Guayaki indexes 1,035 in
# California, Rip It 512 in Michigan; data/scripts/add_insights.py:191). The
# magnitudes are invented; only the direction echoes something measured.
TILT = {"Guayaki": {"CA": 9.0, "OR": 7.5, "CO": 6.0, "WA": 4.0},
        "Rip It": {"MI": 5.0, "KY": 3.5, "TN": 3.0},
        "Celsius": {"FL": 2.2, "CA": 1.6}, "Alani Nu": {"KY": 3.0, "TX": 1.5}}

STORES_TOTAL = 18300   # matches the active-store count the ER diagram records


def lcg(seed=20260915):
    """Same constants as data/scripts/test_price_models.py, so every generated
    artefact in this repo is reproducible the same way."""
    state = [seed]

    def rnd():
        state[0] = (1103515245 * state[0] + 12345) % (2 ** 31)
        return state[0] / 2 ** 31
    return rnd


def sample_rows():
    rnd = lcg()
    pop_total = sum(v[4] for v in STATES.values())
    store_rows, brand_rows = [], []

    for code, (_name, clat, clon, spread, pop) in sorted(STATES.items()):
        n = max(12, round(STORES_TOTAL * pop / pop_total))
        # Cluster into "metros" so the grid cells clear MIN_CELL the way real
        # retail does - stores bunch in towns. Uniform scatter would suppress
        # nearly every cell and silently produce an empty map.
        metros = max(2, round(n / 90))
        anchors = [(clat + (rnd() - 0.5) * spread * 1.5,
                    clon + (rnd() - 0.5) * spread * 2.4) for _ in range(metros)]
        state_rev = 0.0
        for i in range(n):
            alat, alon = anchors[i % metros]
            rev = 24000 + rnd() * 96000 + (rnd() ** 3) * 180000
            state_rev += rev
            store_rows.append({
                "state": code,
                "lat": alat + (rnd() - 0.5) * 0.28,
                "lon": alon + (rnd() - 0.5) * 0.36,
                "rev": rev,
                "units": 9000 + rnd() * 34000,
            })

        # Brand revenue is a SPLIT of the revenue the stores above actually
        # generated, not an independent draw. An earlier version drew the two
        # separately and the placeholder shipped a California where Red Bull
        # alone billed $545M inside a $246M state - the kind of contradiction
        # that makes a reader distrust the real numbers on every other page.
        w = {}
        for b in BRANDS:
            base = {"Red Bull": 3.4, "Monster": 3.0, "Celsius": 1.1,
                    "Alani Nu": 0.9, "Rockstar": 0.7, "NOS": 0.6}.get(b, 0.28)
            w[b] = base * TILT.get(b, {}).get(code, 1.0) * (0.75 + rnd() * 0.5)
        wsum = sum(w.values())
        for b in BRANDS:
            brand_rows.append({"state": code, "brand": b,
                               "rev": state_rev * w[b] / wsum})

    return store_rows, brand_rows


# -------------------------------------------------------------------- main --

def write(payload):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.replace(tmp, OUT)
    m = payload["meta"]
    print(f"wrote {os.path.relpath(OUT, ROOT)}  "
          f"({os.path.getsize(OUT)/1024:.0f} KB, source={payload['source']})")
    print(f"  {len(payload['states'])} states, {m['cells']:,} cells, "
          f"{m['stores_mapped']:,} stores")
    print(f"  suppressed {m['stores_suppressed']:,} stores in "
          f"{m['cells_suppressed']:,} cells under the {MIN_CELL}-store floor")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="print the BigQuery cost and exit")
    ap.add_argument("--sample", action="store_true",
                    help="generate the offline placeholder, no BigQuery")
    args = ap.parse_args()

    if args.sample:
        store_rows, brand_rows = sample_rows()
        write(reduce_rows(store_rows, brand_rows, "sample"))
        print("\n  NOTE: placeholder data. stores.html shows a banner while "
              "source=sample.\n  Rerun without --sample, with BQ_TOKEN set, for "
              "the real panel.")
        return

    token = os.environ.get("BQ_TOKEN", "").strip()
    if not token:
        sys.exit("Set BQ_TOKEN to an OAuth access token:\n"
                 "  gcloud auth application-default print-access-token")

    if args.dry_run:
        total = 0
        for label, sql in (("stores", STORE_SQL), ("brands", BRAND_SQL)):
            b = int(bq(sql, token, dry=True)["totalBytesProcessed"])
            total += b
            print(f"  {label:7s} {b/1e9:6.1f} GB  ->  ${b/1e12*6.25:.2f}")
        print(f"  {'total':7s} {total/1e9:6.1f} GB  ->  ${total/1e12*6.25:.2f}")
        return

    print("querying pdi_stores x pdi_daily_agg ...", flush=True)
    res = bq(STORE_SQL, token)
    if not res.get("jobComplete"):
        sys.exit("store query did not complete inside the timeout; rerun")
    store_rows = rows_of(res, token)
    print(f"  {len(store_rows):,} stores with coordinates")

    print("querying state x brand ...", flush=True)
    res = bq(BRAND_SQL, token)
    if not res.get("jobComplete"):
        sys.exit("brand query did not complete inside the timeout; rerun")
    brand_rows = rows_of(res, token)
    print(f"  {len(brand_rows):,} state-brand rows")

    payload = reduce_rows(store_rows, brand_rows, "pdi")
    if not payload["states"]:
        sys.exit("no rows survived state normalisation - check STATE's encoding "
                 "against state_code() before trusting this")
    if payload["meta"]["no_state"]:
        print(f"  WARNING: {payload['meta']['no_state']:,} stores had an "
              f"unrecognised STATE and are in the cells but not the rollups")
    write(payload)


if __name__ == "__main__":
    main()
