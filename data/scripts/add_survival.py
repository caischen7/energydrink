#!/usr/bin/env python3
"""SKU survival: how long a launch actually lasts, and what year one looked like.

Why this exists
---------------
Every white-space claim on this site is static: "this cell has headroom." The
question a board asks next is not answered anywhere on the page — of the SKUs
that launched into pockets like it, how many were still selling three years
later? Without that, "launch here" is a direction with no base rate attached.

`data/bq/pdi_gtin_by_year.csv` (12,935 GTIN-years, 2016-2026) has been sitting
in the repo unused. Joined to the SKU attribute table it answers exactly that,
at no marginal query cost.

Three things this has to get right, and each one changes the answer
------------------------------------------------------------------
1. LEFT TRUNCATION. PDI's panel coverage ramps hard: total measured revenue is
   $6M in 2016, $22M in 2017, $38M in 2018, then $395M in 2019. A SKU "first
   seen" in 2018 was in all likelihood already selling and simply not covered.
   Treating those as launches would load the sample with mature products and
   flatter survival badly. Launch cohorts therefore start at 2020, the first
   year on a stable coverage base.

2. RIGHT CENSORING. The scrape ends part-way through 2026 ($660M against
   $1,391M for full-year 2025), so a SKU absent in 2026 has not necessarily
   died. 2025 is the last complete year: a SKU still selling in 2025 is alive
   and *censored*, not a survivor-to-infinity, and it is removed from the
   at-risk pool for durations we cannot observe. That is Kaplan-Meier, and the
   naive alternative — dead/alive counted at face value — understates survival.

3. GAPS. SKUs drop out for a year and return. Survival is measured to LAST year
   seen, not to the first gap.

4. WHAT COUNTS AS A LAUNCH. "First year with any revenue" is not a launch date.
   Checked against the data, every SKU that later cleared $1M shows a first year
   of $3-$6 — a barcode appearing in the panel as a stray scan a year or more
   before the product actually shipped. Cohorts built on first-appearance are
   therefore polluted: the real launches all land in the bottom revenue quartile
   of their own cohort, which is why an earlier version of this script reported
   that low first-year revenue predicted success. Launch is defined here as the
   first year a SKU does at least $1,000 AND at least 5% of its eventual peak —
   the first year it is commercially present rather than merely scanned. SKUs
   whose first appearance predates the coverage ramp are still excluded, so a
   2016 product that merely grew in 2021 is not counted as a 2021 launch.

5. MATERIALITY — the one that changes the headline most. Counting a GTIN as
   "alive" because it registered any sale at all puts three-year survival at
   92%, which is not a believable number for CPG and is an artifact: half of
   these SKUs peak under $22K a year across the whole panel, a few stores'
   worth, and the bottom two thirds of them are 1.3% of all dollars. A barcode
   trickling $632 a year is residual stock, not a live product. A SKU is
   counted alive here only in years it does at least 10% of its OWN peak, which
   is scale-free and catches delisting as decay rather than as a hard stop. The
   naive curve is kept alongside, labelled, because the gap between the two IS
   the finding.

Survival is also not the same question as success. A SKU can hold distribution
for years and never matter. The "reached scale" base rate answers the second
question: what share of launches ever cleared $1M a year in the panel. The
survival curve is then repeated for just those SKUs, which is the population a
real launch is actually joining.

A NOTE ON THE YEAR-ONE PREDICTOR. The obvious version of this — compare year-one
revenue for SKUs that survived against those that did not — is invalid when
death is defined relative to a SKU's own peak, because a product that peaks in
year one and decays is marked dead early precisely for having had a big first
year. Run that way it reports survivors earning *less* in year one than
failures, which is an artifact of the definition and not a finding. The
predictor here shares no term with its outcome: it asks whether year-one revenue
predicts having at least $1M of revenue still on the books in year three.

Output: `audiences.opportunity.survival` inside public/data/dashboard.json.

    python data/scripts/add_survival.py          # writes into the aggregate
    python data/scripts/add_survival.py --dry    # print, write nothing

stdlib only.
"""
import argparse
import csv
import json
import os
import statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
YEARS = os.path.join(ROOT, "data/bq/pdi_gtin_by_year.csv")
ATTRS = os.path.join(ROOT, "data/bq/pdi_unique_products.csv")
AGG = os.path.join(ROOT, "public/data/dashboard.json")

FIRST_COHORT = 2020      # first year on a stable coverage base (see note 1)
LAST_COMPLETE = 2025     # 2026 is a partial scrape (see note 2)
MIN_COHORT_N = 25        # below this a cut is noise, and is reported as such
MATERIAL = 0.10          # a live year does >=10% of the SKU's own peak (see note 5)
LAUNCH_ABS = 1_000       # commercial presence floor, in panel dollars (see note 4)
LAUNCH_REL = 0.05        # ...and at least this share of the SKU's eventual peak
SCALE_BAR = 1_000_000    # "reached scale" = this much panel revenue in some year
Y1_BAR = 100_000         # year-three outcome bar for the year-one predictor;
                         # $1M leaves only 4 events in 763 launches, too thin to rank


# --------------------------------------------------------------- load ------
def load():
    """One record per GTIN: launch year, last year seen, and per-year revenue."""
    rev = defaultdict(dict)
    for r in csv.DictReader(open(YEARS)):
        try:
            y, v = int(r["yr"]), float(r["rev"])
        except (ValueError, KeyError):
            continue
        if v > 0:
            rev[r["GTIN"]][y] = v

    attrs = {}
    for r in csv.DictReader(open(ATTRS)):
        attrs[r["GTIN"]] = r

    out = []
    for g, ys in rev.items():
        if not ys:
            continue
        a = attrs.get(g, {})
        peak = max(ys.values())
        material = [y for y, v in ys.items() if v >= peak * MATERIAL]
        bar = max(LAUNCH_ABS, peak * LAUNCH_REL)
        commercial = [y for y, v in ys.items() if v >= bar]
        if not commercial:
            continue                         # never commercially present
        out.append({
            "gtin": g,
            "first_seen": min(ys),           # first scan of any kind
            "launch": min(commercial),       # first year commercially present
            "last": max(ys),                 # any sale at all - the naive basis
            "last_mat": max(material),       # last year at >=10% of own peak
            "peak": peak,
            "scaled": peak >= SCALE_BAR,
            "rev": ys,
            "brand": a.get("canonical_brand") or a.get("BRAND") or "Unknown",
            "fam": a.get("flavor_family") or "Unknown",
            "aud": a.get("target_consumer") or "Unknown",
            "size": (a.get("UNIT_SIZE") or "").strip(),
        })
    return out


# ----------------------------------------------------------- survival -----
def km(sk, field="last_mat"):
    """Kaplan-Meier survival by whole years since launch.

    A SKU contributes to the at-risk pool at duration k only if the data could
    have observed it living that long: launch + k <= LAST_COMPLETE. A SKU still
    selling in the last complete year is censored — it leaves the pool without
    counting as a death.

    `field` selects the death definition: "last_mat" (default, >=10% of own
    peak) or "last" (any sale — the naive basis, kept for contrast).
    """
    horizon = LAST_COMPLETE - FIRST_COHORT
    surv, out, n_at_1 = 1.0, [], 0
    for k in range(1, horizon + 1):
        at_risk = deaths = 0
        for s in sk:
            if s["launch"] + k > LAST_COMPLETE:
                continue                      # unobservable, not censored-here
            lived = s[field] - s["launch"]
            if lived >= k:
                at_risk += 1                  # survived through k
            elif lived == k - 1:
                at_risk += 1
                deaths += 1                   # died during year k
            # lived < k-1: already dead before this interval, not at risk
        if k == 1:
            n_at_1 = at_risk
        if at_risk == 0:
            break
        surv *= (1 - deaths / at_risk)
        out.append({"yr": k, "surv": round(surv * 100, 1),
                    "at_risk": at_risk, "deaths": deaths})
    return out, n_at_1


def rate_at(curve, k):
    for p in curve:
        if p["yr"] == k:
            return p["surv"]
    return None


def scale_rate(sk, within=3):
    """Of launches old enough to judge, what share ever cleared the scale bar?"""
    elig = [s for s in sk if s["launch"] + within <= LAST_COMPLETE]
    if not elig:
        return None
    hit = [s for s in elig if s["peak"] >= SCALE_BAR]
    return {"n": len(elig), "hit": len(hit),
            "pct": round(len(hit) / len(elig) * 100, 1)}


def cut(sk, key, label):
    """Survival by a categorical cut, with thin groups flagged rather than hidden."""
    groups = defaultdict(list)
    for s in sk:
        groups[s[key]].append(s)
    rows = []
    for name, g in groups.items():
        if name in ("Unknown", ""):
            continue
        curve, n = km(g)
        r3 = rate_at(curve, 3)
        sc = scale_rate(g)
        if r3 is None or n < 8:
            continue
        rows.append({"name": name, "n": n, "y1": rate_at(curve, 1),
                     "y2": rate_at(curve, 2), "y3": r3,
                     "scale_pct": sc["pct"] if sc else None,
                     "thin": n < MIN_COHORT_N})
    rows.sort(key=lambda r: (-(r["scale_pct"] or 0), -r["n"]))
    return {"label": label, "rows": rows}


# ------------------------------------------------------- year-one signal ---
def year_one(sk):
    """Does year-one revenue predict still being a real product in year three?

    Outcome is an absolute revenue bar in year three, deliberately not anything
    derived from the SKU's own peak — see the note in the module docstring.
    Only SKUs whose third year is observable are eligible.
    """
    elig = [s for s in sk
            if s["launch"] + 3 <= LAST_COMPLETE and s["rev"].get(s["launch"], 0) > 0]
    if len(elig) < 40:
        return None
    for s2 in elig:
        s2["_r1"] = s2["rev"][s2["launch"]]
        s2["_ok"] = s2["rev"].get(s2["launch"] + 3, 0) >= Y1_BAR

    ordered = sorted(elig, key=lambda x: x["_r1"])
    n = len(ordered)
    bands, names = [], ["Bottom quarter", "Second quarter", "Third quarter", "Top quarter"]
    for i in range(4):
        g = ordered[i * n // 4:(i + 1) * n // 4]
        if not g:
            continue
        bands.append({
            "band": names[i],
            "n": len(g),
            "r1_lo": round(g[0]["_r1"]), "r1_hi": round(g[-1]["_r1"]),
            "r1_med": round(statistics.median(x["_r1"] for x in g)),
            "pct": round(sum(1 for x in g if x["_ok"]) / len(g) * 100, 1),
        })
    half = len(bands) // 2
    lo = sum(b["n"] * b["pct"] for b in bands[:half]) / max(sum(b["n"] for b in bands[:half]), 1)
    hi = sum(b["n"] * b["pct"] for b in bands[half:]) / max(sum(b["n"] for b in bands[half:]), 1)
    # The highest first-year revenue above which nothing has ever failed to
    # register - i.e. the ceiling of the last all-zero band. A launch gate.
    dead = [b for b in bands if b["pct"] == 0]
    return {
        "n": n,
        "bands": bands,
        "top_half": round(hi, 1),
        "bottom_half": round(lo, 1),
        "lift": round(hi / lo, 1) if lo else None,
        "floor": dead[-1]["r1_hi"] if dead and dead[-1] is bands[len(dead) - 1] else None,
        "hits": sum(1 for x in elig if x["_ok"]),
        "bar": Y1_BAR,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    all_sk = load()
    sk = [s for s in all_sk
          if FIRST_COHORT <= s["launch"] <= LAST_COMPLETE
          and s["first_seen"] >= FIRST_COHORT - 1]
    curve, n1 = km(sk)                       # materiality basis (headline)
    naive, _ = km(sk, field="last")           # any-sale basis (contrast)
    big = [s2 for s2 in sk if s2["scaled"]]   # launches that became real products
    big_curve, big_n = km(big)

    # Cohort-by-cohort, so a reader can see the rate is not one year's accident.
    cohorts = []
    for y in range(FIRST_COHORT, LAST_COMPLETE):
        g = [s for s in sk if s["launch"] == y]
        if len(g) < MIN_COHORT_N:
            continue
        c, n = km(g)
        cohorts.append({"year": y, "n": n, "y1": rate_at(c, 1),
                        "y2": rate_at(c, 2), "y3": rate_at(c, 3)})

    out = {
        "window": {"first_cohort": FIRST_COHORT, "last_complete": LAST_COMPLETE},
        "n_launches": n1,
        "n_excluded_pre": sum(1 for s in all_sk
                              if s["launch"] < FIRST_COHORT or s["first_seen"] < FIRST_COHORT - 1),
        "launch_rule": f"first year at >= ${LAUNCH_ABS:,} and >= {int(LAUNCH_REL*100)}% of the SKU's peak",
        "curve": curve,
        "naive": naive,
        "naive_y3": rate_at(naive, 3),
        "y1": rate_at(curve, 1), "y2": rate_at(curve, 2),
        "y3": rate_at(curve, 3), "y5": rate_at(curve, 5),
        "scale": scale_rate(sk),
        "scaled_curve": big_curve,
        "scaled_n": big_n,
        "scaled_y3": rate_at(big_curve, 3),
        "scale_bar": SCALE_BAR,
        "material_pct": int(MATERIAL * 100),
        "cohorts": cohorts,
        "by_fam": cut(sk, "fam", "Flavor family"),
        "by_aud": cut(sk, "aud", "Target audience"),
        "year_one": year_one(sk),
        "method": (
            "Kaplan-Meier on PDI GTIN-year revenue. Launch cohorts start at "
            f"{FIRST_COHORT} because panel coverage before then is too thin to tell a "
            "launch from a gap in measurement - measured revenue runs $6M in 2016 and "
            "$38M in 2018 against $395M in 2019. "
            f"{LAST_COMPLETE} is the last complete year; 2026 is a partial scrape, so a "
            "SKU still selling in 2025 is treated as alive and censored rather than "
            "counted as a death. Survival is measured to the last year a GTIN was seen, "
            "so a one-year gap does not end a life."
        ),
        "caveat": (
            "Convenience channel only, and a sample of it. A SKU that left convenience "
            "for grocery or DTC reads here as a death. The rate is therefore a floor on "
            "survival, and is most reliable for brands whose route to market is the "
            "cooler."
        ),
    }

    if args.dry:
        print(json.dumps({k: v for k, v in out.items()
                          if k not in ("curve", "by_fam", "by_aud")}, indent=1))
        print("curve:", [(p["yr"], p["surv"], p["at_risk"]) for p in curve])
        for c in (out["by_fam"], out["by_aud"]):
            print(f"\n{c['label']}:")
            for r in c["rows"]:
                print(f"  {r['name'][:26]:28} n={r['n']:4}  y3={r['y3']}%"
                      + ("  (thin)" if r["thin"] else ""))
        return

    with open(AGG) as f:
        agg = json.load(f)
    agg["audiences"]["opportunity"]["survival"] = out
    with open(AGG, "w") as f:
        json.dump(agg, f, separators=(",", ":"))
    print(f"wrote survival for {n1} launches -> {AGG}")
    print(f"  year 1 {out['y1']}%  year 2 {out['y2']}%  year 3 {out['y3']}%")


if __name__ == "__main__":
    main()
