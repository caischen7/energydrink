#!/usr/bin/env python3
"""Collect US soft-drink manufacturing capacity from two public federal sources.

Runs on GitHub Actions (.github/workflows/bottling.yml), not here: this
container's egress proxy answers 000/403 for api.census.gov and data.epa.gov,
the same organisation policy that blocks trends.google.com.

TWO SOURCES, BECAUSE THEY ANSWER DIFFERENT QUESTIONS
----------------------------------------------------
  Census CBP    Counts of establishments and employment by state and county for
                NAICS 312111. Authoritative, complete, and anonymous - it tells
                you HOW MUCH capacity is where, never whose.
  EPA FRS       Named, geocoded facilities carrying the same NAICS. Not a
                complete census - a plant appears because it holds an
                environmental permit - but it gives names and coordinates.

Together: CBP for the denominator, FRS for the map pins.

WHAT NAICS 312111 IS, AND THE TWO LIMITS THAT MATTER
----------------------------------------------------
312111 is "Soft Drink Manufacturing". It covers carbonated soft drinks, bottled
water, and energy drinks in one code. THERE IS NO ENERGY-DRINK-ONLY NAICS, so
nothing here separates a Monster line from a Coke line or a water line, and any
count is an upper bound on energy capacity.

Second, and more important for this project: most energy brands DO NOT OWN
PLANTS. Celsius, Bang, Ghost, Alani Nu and the rest are co-packed by
contract manufacturers. So a facility list keyed on brand name will find almost
no energy brands, and the honest use of this data is "where is co-packing
capacity", not "who makes what". A brand-name search over these files will look
like an absence of energy manufacturing; it is an absence of vertical
integration.

  312112  Bottled water manufacturing   -- collected too, as the nearest
                                           neighbour, so the 312111 count can be
                                           read against it
  312113  Ice manufacturing             -- deliberately not collected

    python data/scrapers/bottling_plants.py            # both sources
    python data/scrapers/bottling_plants.py --source census
    python data/scrapers/bottling_plants.py --dry-run  # show the plan, call nothing

stdlib only. No API key: CBP is open at this volume, FRS needs none.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "data/plants")

NAICS = ["312111", "312112"]
CBP_YEAR = os.environ.get("CBP_YEAR", "2022")

# CBP moved the NAICS parameter name between vintages, so both are attempted
# rather than guessed at - a 400 here is cheap and the fallback is free.
CBP_PARAMS = ("NAICS2017", "NAICS2022")


def fetch(url, tries=4):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "bogus-banana/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** attempt * 3)
                continue
            raise
        except urllib.error.URLError:
            if attempt < tries - 1:
                time.sleep(2 ** attempt * 3)
                continue
            raise
    return None


# ------------------------------------------------------------------ census --
def census(level="state"):
    """Establishments and employment by NAICS, per state or county."""
    geo = "state:*" if level == "state" else "county:*&in=state:*"
    rows = []
    for code in NAICS:
        got = None
        for param in CBP_PARAMS:
            url = (f"https://api.census.gov/data/{CBP_YEAR}/cbp?"
                   f"get=NAME,ESTAB,EMP,PAYANN&for={geo}&{param}={code}")
            try:
                got = json.loads(fetch(url))
                break
            except Exception as e:                      # noqa: BLE001
                print(f"  {param}={code} {level}: {type(e).__name__}")
        if not got or len(got) < 2:
            print(f"  no rows for NAICS {code} at {level} level")
            continue
        head = got[0]
        for r in got[1:]:
            d = dict(zip(head, r))
            rows.append({
                "naics": code, "level": level,
                "name": d.get("NAME", ""),
                "state_fips": d.get("state", ""),
                "county_fips": d.get("county", ""),
                "establishments": d.get("ESTAB", ""),
                "employees": d.get("EMP", ""),
                "annual_payroll_k": d.get("PAYANN", ""),
                "year": CBP_YEAR,
            })
        print(f"  NAICS {code} {level}: {len(got)-1} rows")
    return rows


# --------------------------------------------------------------------- epa --
def epa():
    """Named facilities from the EPA Facility Registry Service."""
    rows = []
    for code in NAICS:
        # Envirofacts has changed host and path over time; try the documented
        # forms in order rather than pinning one that may have moved.
        candidates = [
            f"https://data.epa.gov/efservice/frs_program_facility/naics_code/{code}/CSV",
            f"https://data.epa.gov/efservice/frs.frs_program_facility/naics_code/{code}/CSV",
            f"https://enviro.epa.gov/enviro/efservice/frs_program_facility/naics_code/{code}/CSV",
        ]
        text = None
        for u in candidates:
            try:
                text = fetch(u)
                if text and "," in text:
                    print(f"  NAICS {code}: {u.split('/')[2]}")
                    break
            except Exception as e:                      # noqa: BLE001
                print(f"  {u.split('/')[2]} {code}: {type(e).__name__}")
                text = None
        if not text:
            continue
        rdr = csv.DictReader(text.splitlines())
        n = 0
        for d in rdr:
            low = {k.lower(): v for k, v in d.items() if k}
            lat = low.get("latitude83") or low.get("latitude") or ""
            lon = low.get("longitude83") or low.get("longitude") or ""
            rows.append({
                "naics": code,
                "name": low.get("primary_name") or low.get("facility_name") or "",
                "city": low.get("city_name") or low.get("city") or "",
                "state": low.get("state_code") or low.get("state") or "",
                "zip": low.get("postal_code") or "",
                "lat": lat, "lon": lon,
                "registry_id": low.get("registry_id") or "",
            })
            n += 1
        print(f"  NAICS {code}: {n} facilities")
    return rows


def write(name, rows):
    if not rows:
        print(f"  nothing to write for {name}")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)                 # atomic: a killed run cannot truncate
    print(f"wrote {path}  ({len(rows):,} rows)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["census", "epa", "all"], default="all")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        print(f"NAICS {NAICS}, CBP year {CBP_YEAR}")
        print("  census state  -> data/plants/cbp_state.csv")
        print("  census county -> data/plants/cbp_county.csv")
        print("  epa frs       -> data/plants/frs_facilities.csv")
        print("\ndry run — nothing called, nothing written.")
        return

    if args.source in ("census", "all"):
        print("Census CBP, by state:")
        write("cbp_state.csv", census("state"))
        print("Census CBP, by county:")
        write("cbp_county.csv", census("county"))
    if args.source in ("epa", "all"):
        print("EPA Facility Registry Service:")
        write("frs_facilities.csv", epa())

    if not os.path.isdir(OUT_DIR) or not os.listdir(OUT_DIR):
        sys.exit("no data collected — both sources failed")


if __name__ == "__main__":
    main()
