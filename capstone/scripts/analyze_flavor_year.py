#!/usr/bin/env python3
"""Flavor analysis by year: what actually sells, once the panel ramp is removed.

    python capstone/scripts/analyze_flavor_year.py            # print + write JSON
    python capstone/scripts/analyze_flavor_year.py --quiet    # write JSON only

Writes public/data/flavor_year.json for the Flavor by Year page. stdlib only.

THE PROBLEM THIS SCRIPT EXISTS TO SOLVE
---------------------------------------
The PDI panel is not a fixed sample. It grows from ~8,500 active stores in 2019
to ~19,100 in 2025 - 2.24x. Category units over the same span grow 3.01x. So
per-store volume grew only 1.34x, and roughly three quarters of the apparent
growth is PDI signing chains rather than anyone drinking more.

Every raw annual total is therefore uninterpretable on its own, and a flavor's
"growth" in raw units is mostly a measure of PDI's sales team. Three defences:

  1. UNIT SHARE is the primary popularity metric. If the panel doubles, every
     flavor's raw units roughly double and shares are unchanged. Share is
     immune to the ramp by construction, which is why it leads.

  2. UNITS PER ACTIVE STORE is the velocity metric, and it is reported as an
     index to its own 2019 value so a reader cannot mistake it for a level.

  3. REACH x DEPTH decomposes that velocity:
        reach = stores selling the family / active stores   (distribution)
        depth = units / stores selling the family           (rate where sold)
     units per active store = reach x depth, exactly. The decomposition is the
     point: high reach with low depth is a flavor that is everywhere and moves
     slowly; low reach with high depth is a flavor that sells hard wherever it
     is stocked, which is the white-space signal worth acting on.

SHELF DOMINANCE
---------------
Monster and Red Bull carry the longest lineups, so a family they favour wins a
units ranking partly by having more shelf facings. UNITS PER SKU is reported
alongside every ranking as the control: it asks how hard the average SKU in
that family works, independent of how many the category chose to launch.

WHAT THIS SCRIPT CANNOT DO
--------------------------
It cannot rank by rating BY YEAR. PDI is point-of-sale - revenue, units,
transactions, stores - and carries no rating field of any kind. The only rating
data in this repository is a single Amazon snapshot taken on one day
(2026-05-13), so it has no time dimension at all. Ratings are computed here at
flavor-family level as a cross-section and are kept visibly separate from the
yearly series. See rate_families() for the sample-size problem that follows.
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
import re
import math
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANEL = os.path.join(ROOT, "data/bq/derived/price_panel.csv")
AMAZON = os.path.join(ROOT, "data/amazon/products.csv")
OUT = os.path.join(ROOT, "public/data/flavor_year.json")

sys.path.insert(0, os.path.join(ROOT, "data/scripts"))
from classify_target_consumers import flavor_family  # noqa: E402

# Families that are not flavors. Kept in the totals (they are real sales) but
# excluded from "which flavor wins" rankings, because "Unspecified" winning a
# flavor study would be an artefact of blank FLAVOR fields, not a finding.
NON_FLAVOR = {"Unspecified"}


def load_panel():
    rows = [r for r in csv.DictReader(open(PANEL, encoding="utf-8"))]
    return rows


def yearly(rows, scheme):
    """(cluster, year) -> summed units/rev, averaged skus/stores, plus the
    year's average active-store count as the panel denominator."""
    agg = collections.defaultdict(lambda: collections.defaultdict(float))
    months = collections.defaultdict(set)
    active = collections.defaultdict(list)          # year -> monthly active counts
    seen_month = collections.defaultdict(set)

    for r in rows:
        if r["scheme"] != scheme:
            continue
        y = r["month"][:4]
        k = (r["cluster"], y)
        agg[k]["units"] += float(r["units"] or 0)
        agg[k]["rev"] += float(r["rev"] or 0)
        agg[k]["skus_sum"] += float(r["skus"] or 0)
        agg[k]["stores_sum"] += float(r["stores"] or 0)
        months[k].add(r["month"])
        # stores_active is a property of the MONTH, not of the cluster, so it
        # must be collected once per month or it is counted 15 times.
        if r["month"] not in seen_month[y]:
            seen_month[y].add(r["month"])
            active[y].append(float(r["stores_active"] or 0))

    out = {}
    for k, v in agg.items():
        n = len(months[k]) or 1
        out[k] = {
            "units": v["units"], "rev": v["rev"],
            "skus": v["skus_sum"] / n,           # average monthly lineup size
            "stores": v["stores_sum"] / n,       # average monthly selling stores
            "months": n,
        }
    avg_active = {y: statistics.fmean(v) for y, v in active.items()}
    return out, avg_active


def build_series(agg, avg_active, drop_non_flavor=True):
    """Per-year metric table. Share is computed over the SAME set that is
    ranked, so the shares of a ranking always sum to 100."""
    years = sorted({y for _, y in agg})
    clusters = sorted({c for c, _ in agg})
    if drop_non_flavor:
        clusters = [c for c in clusters if c not in NON_FLAVOR]

    totals = {y: sum(agg[(c, y)]["units"] for c in clusters if (c, y) in agg) for y in years}
    rows = []
    for c in clusters:
        for y in years:
            v = agg.get((c, y))
            if not v or not v["units"]:
                continue
            act = avg_active[y]
            stores = v["stores"] or 1
            reach = v["stores"] / act                    # share of panel carrying it
            depth = v["units"] / stores                  # units per selling store per year
            rows.append({
                "cluster": c, "year": int(y),
                "units": round(v["units"]),
                "rev": round(v["rev"], 2),
                "unit_share_pct": round(v["units"] / totals[y] * 100, 3) if totals[y] else 0,
                "units_per_active_store": round(v["units"] / act, 2),
                "reach_pct": round(reach * 100, 2),
                "depth_units_per_selling_store": round(depth, 2),
                "skus": round(v["skus"], 1),
                "units_per_sku": round(v["units"] / v["skus"], 0) if v["skus"] else None,
                "price_per_unit": round(v["rev"] / v["units"], 4) if v["units"] else None,
            })
    return rows, years, totals


def rate_families():
    """Flavor-family ratings from the committed Amazon snapshot.

    THREE THINGS THAT LIMIT THIS, ALL OF THEM SERIOUS
    -------------------------------------------------
    1. ONE DAY. Every row was captured 2026-05-13, so there is no year
       dimension and none can be manufactured. It is a cross-section.
    2. TINY AND SELF-SELECTED. 75 products, of which the ones carrying a
       readable flavor are fewer still. Amazon's energy-drink assortment skews
       to multipacks, powders and DTC-native brands, and under-represents the
       single-serve convenience sale this study is otherwise about.
    3. REVIEWS ARE NOT A RANDOM SAMPLE. People who review are people with an
       opinion, and the ratings sit in a narrow 4.1-4.7 band where differences
       are mostly noise.

    So this is reported as provisional, never ranked against the PDI series in
    the same chart. The defensible version is Workstream 1: a manual capture
    across retailers with a recorded protocol.

    Variety packs are dropped: "9-Flavor Variety Pack" is not a flavor, and
    letting flavor_family() read a title like that invents a signal.
    """
    if not os.path.exists(AMAZON):
        return None
    variety = re.compile(r"variety pack|sampler|\d+\s*-?\s*flavou?r", re.I)
    prods = []
    for r in csv.DictReader(open(AMAZON, encoding="utf-8")):
        try:
            rating = float(r["rating"])
            n = float(r["ratings_total"] or 0)
        except (TypeError, ValueError):
            continue
        title = r.get("title") or ""
        if variety.search(title):
            continue
        fam = flavor_family({"FLAVOR": "", "PRODUCT_DESCRIPTION": title})
        if fam in NON_FLAVOR:
            continue
        prods.append({"brand": r.get("brand") or "", "family": fam,
                      "rating": rating, "n": n, "title": title})
    if not prods:
        return None

    C = statistics.fmean(p["rating"] for p in prods)          # prior mean
    m_med = statistics.median(p["n"] for p in prods)          # prior weight

    def adjust(group, m):
        n = sum(p["n"] for p in group)
        if n <= 0:
            return None
        R = sum(p["rating"] * p["n"] for p in group) / n       # review-weighted
        return (n * R + m * C) / (n + m)

    by = collections.defaultdict(list)
    for p in prods:
        by[p["family"]].append(p)

    # Sensitivity: the brief asks for it explicitly, and with groups this small
    # the choice of m moves the ranking, which is itself the finding.
    ms = [m_med * f for f in (0.5, 1, 2, 4)]
    fams = []
    for fam, group in by.items():
        n = sum(p["n"] for p in group)
        raw = sum(p["rating"] * p["n"] for p in group) / n if n else None
        fams.append({
            "family": fam, "products": len(group), "reviews": round(n),
            "raw_rating": round(raw, 3) if raw else None,
            "adjusted": round(adjust(group, m_med), 3),
            "sensitivity": {f"m={round(m)}": round(adjust(group, m), 3) for m in ms},
        })
    fams.sort(key=lambda f: -(f["adjusted"] or 0))
    return {
        "prior_mean_C": round(C, 4), "prior_weight_m": round(m_med, 1),
        "n_products": len(prods), "families": fams,
        "capture_date": "2026-05-13", "source": "Amazon product snapshot, committed corpus",
    }


def movers(rows, years):
    """Share change first-year -> last-year, which is the ramp-immune way to
    ask who is actually winning."""
    first, last = str(years[0]), str(years[-1])
    idx = {(r["cluster"], r["year"]): r for r in rows}
    out = []
    for c in sorted({r["cluster"] for r in rows}):
        a, b = idx.get((c, int(first))), idx.get((c, int(last)))
        if not a or not b:
            continue
        # PEAK YEAR. A first-vs-last comparison is the standard way to read this
        # and it is capable of lying outright: Watermelon goes 0.81 -> 5.37 and
        # reads as the second-biggest winner, while its actual peak was 7.35 in
        # 2021 and it has fallen every year but one since. Recording the peak
        # lets the page say "past peak" instead of "winner".
        series = sorted(((r["year"], r["unit_share_pct"]) for r in rows if r["cluster"] == c))
        peak_year, peak_share = max(series, key=lambda t: t[1])
        out.append({
            "cluster": c,
            "peak_year": peak_year, "peak_share": peak_share,
            "past_peak": peak_year < int(years[-1]) and b["unit_share_pct"] < peak_share * 0.95,
            "off_peak_pct": round((b["unit_share_pct"] / peak_share - 1) * 100, 1) if peak_share else 0,
            "share_first": a["unit_share_pct"], "share_last": b["unit_share_pct"],
            "share_delta_pp": round(b["unit_share_pct"] - a["unit_share_pct"], 3),
            "vps_first": a["units_per_active_store"], "vps_last": b["units_per_active_store"],
            "vps_index": round(b["units_per_active_store"] / a["units_per_active_store"] * 100, 1)
            if a["units_per_active_store"] else None,
            "reach_first": a["reach_pct"], "reach_last": b["reach_pct"],
            "depth_first": a["depth_units_per_selling_store"],
            "depth_last": b["depth_units_per_selling_store"],
        })
    out.sort(key=lambda r: -r["share_delta_pp"])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    rows = load_panel()
    fam_agg, active = yearly(rows, "family")
    brand_agg, _ = yearly(rows, "brand")
    fam_rows, years, totals = build_series(fam_agg, active)
    brand_rows, _, _ = build_series(brand_agg, active, drop_non_flavor=False)
    fam_movers = movers(fam_rows, years)
    ratings = rate_families()

    # Category-level context: the ramp, stated as a number rather than implied.
    yr = [str(y) for y in years]
    cat = [{
        "year": int(y),
        "units": round(sum(fam_agg[(c, y)]["units"] for c, yy in fam_agg if yy == y)),
        "active_stores": round(active[y]),
        "units_per_active_store": round(
            sum(fam_agg[(c, y)]["units"] for c, yy in fam_agg if yy == y) / active[y], 2),
    } for y in yr]
    ramp = cat[-1]["active_stores"] / cat[0]["active_stores"]
    raw_growth = cat[-1]["units"] / cat[0]["units"]

    payload = {
        "generated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "PDI convenience panel via data/bq/derived/price_panel.csv",
        "years": [int(y) for y in yr],
        "category": cat,
        "ramp": {
            "active_stores_growth": round(ramp, 3),
            "raw_unit_growth": round(raw_growth, 3),
            "per_store_growth": round(raw_growth / ramp, 3),
            # log(raw) = log(ramp) + log(per_store), so each term's share of
            # log(raw) is its share of the compound growth. An earlier draft
            # used a (1 - 1/x) ratio, which returned 83% and has no such
            # reading - it is not an attribution of anything.
            "coverage_share_of_growth_pct": round(math.log(ramp) / math.log(raw_growth) * 100, 1),
        },
        "families": fam_rows,
        "brands": brand_rows,
        "movers": fam_movers,
        "ratings": ratings,
        "caveats": {
            "no_ratings_in_pdi": (
                "PDI is point-of-sale and carries no rating field. The rating block on this "
                "page is a single Amazon snapshot from 2026-05-13, cross-sectional only, and "
                "cannot be split by year. It is provisional pending a manual multi-retailer "
                "capture with a recorded protocol."),
            "panel_ramp": (
                f"Active stores grow {ramp:.2f}x across {yr[0]}-{yr[-1]} while raw units grow "
                f"{raw_growth:.2f}x, so per-store volume grows only {raw_growth/ramp:.2f}x "
                f"({math.log(ramp)/math.log(raw_growth)*100:.0f}% of the compound growth is coverage). Raw "
                "annual totals mostly measure PDI's coverage. Unit share and per-store velocity "
                "are the metrics to read."),
            "convenience_only": (
                "PDI covers the convenience channel only, and roughly an 8.6% sample of it. "
                "E-commerce, club and natural grocery are invisible, which matters most for "
                "powders, wellness brands and DTC-native flavors."),
            "taxonomy": (
                "Families come from flavor_family() in classify_target_consumers.py, an ordered "
                "first-match rule list. Assignment of multi-fruit names is decided by list "
                "order: 'Grape Slush' is Sour & candy, 'Mango Peach' is Tropical, cherry is "
                "Berry. See capstone/registry for the audit and the open decisions."),
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(payload, fh, separators=(",", ":"))
    os.replace(tmp, OUT)

    if args.quiet:
        print(f"wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT)/1024:.0f} KB)")
        return

    print(f"\nPANEL RAMP  {yr[0]} -> {yr[-1]}")
    print(f"  active stores {cat[0]['active_stores']:,} -> {cat[-1]['active_stores']:,}  ({ramp:.2f}x)")
    print(f"  raw units     {cat[0]['units']:,} -> {cat[-1]['units']:,}  ({raw_growth:.2f}x)")
    print(f"  per store     {cat[0]['units_per_active_store']:.0f} -> "
          f"{cat[-1]['units_per_active_store']:.0f}  ({raw_growth/ramp:.2f}x)")
    print(f"  => {payload['ramp']['coverage_share_of_growth_pct']:.0f}% of the growth is coverage\n")

    print(f"MOST POPULAR BY UNIT SHARE (ramp-immune), {yr[-1]}")
    last = sorted([r for r in fam_rows if r["year"] == int(yr[-1])],
                  key=lambda r: -r["unit_share_pct"])
    print(f"  {'family':<22}{'share%':>8}{'u/store':>9}{'reach%':>8}{'depth':>8}{'SKUs':>7}{'u/SKU':>9}")
    for r in last[:10]:
        print(f"  {r['cluster']:<22}{r['unit_share_pct']:>8.2f}{r['units_per_active_store']:>9.0f}"
              f"{r['reach_pct']:>8.0f}{r['depth_units_per_selling_store']:>8.0f}"
              f"{r['skus']:>7.0f}{r['units_per_sku']:>9,.0f}")

    print(f"\nBIGGEST SHARE MOVERS {yr[0]} -> {yr[-1]} (pp of category units)")
    for r in fam_movers[:5]:
        print(f"  +{r['share_delta_pp']:>6.2f}pp  {r['cluster']:<22}"
              f"{r['share_first']:>6.2f} -> {r['share_last']:>6.2f}   velocity index {r['vps_index']}")
    for r in fam_movers[-4:]:
        print(f"  {r['share_delta_pp']:>7.2f}pp  {r['cluster']:<22}"
              f"{r['share_first']:>6.2f} -> {r['share_last']:>6.2f}   velocity index {r['vps_index']}")

    if ratings:
        print(f"\nRATINGS - CROSS-SECTION ONLY, {ratings['n_products']} products, "
              f"captured {ratings['capture_date']}")
        print(f"  prior C={ratings['prior_mean_C']}  m={ratings['prior_weight_m']}")
        print(f"  {'family':<22}{'adj':>7}{'raw':>7}{'prods':>7}{'reviews':>10}")
        for f in ratings["families"]:
            print(f"  {f['family']:<22}{f['adjusted']:>7.3f}{f['raw_rating']:>7.3f}"
                  f"{f['products']:>7}{f['reviews']:>10,}")
    print()


if __name__ == "__main__":
    main()
