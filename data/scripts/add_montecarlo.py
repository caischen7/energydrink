#!/usr/bin/env python3
"""Donor pool for a Monte Carlo launch simulation.

What this is, and what it is not
--------------------------------
It answers: "if we launch into this audience x flavor pocket, what range of
five-year revenue have comparable launches actually produced?" It does NOT
predict whether *our* product is good. Nothing in the data knows that. What it
does is replace a single point estimate with the observed distribution of
outcomes for the closest real comparables, so a plan can be judged against a
spread rather than against one flattering number.

Why bootstrap rather than a fitted distribution
-----------------------------------------------
The obvious approach is to fit a lognormal to launch revenue and draw from it.
That would be worse here, for three reasons this dataset makes plain:

  * The revenue distribution is not merely skewed, it is close to degenerate -
    half of these SKUs peak under $22K a year and 3.7% ever clear $1M. A fitted
    lognormal smooths over exactly the lumpiness that matters.
  * Survival and revenue are not independent. Products that die in year two have
    a different year-one shape from products that compound. Sampling them from
    separate distributions would break that link and quietly overstate the
    middle of the range.
  * Year-to-year growth within a surviving SKU is autocorrelated.

Resampling whole observed trajectories preserves all three for free. Each draw
is a real product's actual five years, not a synthetic path. The cost is that
the simulation can only produce futures that resemble the past - which is worth
stating on the page rather than hiding.

The donor pool
--------------
Launches are exactly the population from add_survival.py: commercially present
from 2020 on, first appearance no earlier than 2019. A trajectory is that SKU's
revenue in each of its first five years from launch, zero-filled after death.

Trajectories are truncated at the last complete year (2025), so a 2024 launch
contributes only two observed years. Two wrong ways to handle that, and the one
used here:

  * Zero-padding short trajectories counts "has not happened yet" as "did not
    happen" and drags the whole distribution down.
  * Chaining a second donor onto the uncovered years is worse. It splices a
    product that died in year two onto a survivor's years three to five, which
    manufactures outcomes no real SKU produced and destroys the survival
    structure the bootstrap exists to preserve.

Instead the donor pool is HORIZON-MATCHED: a five-year simulation samples only
launches with five observed years, a three-year simulation samples from those
with three. Every draw is one real product's complete run over exactly the
horizon being asked about. The cost is honest and worth stating - a five-year
horizon can only draw on the 2020-21 cohorts, so it is both a smaller sample and
an older one. The page shows the donor count for whichever horizon is selected.

Scale
-----
PDI is convenience-only and a sample of it, so panel dollars are not market
dollars. A single global lift would be too blunt: measured against the matrix,
the panel-to-all-channel ratio runs from 1x to 64x across cells (median 22x,
pooled 42x), because it is driven by each audience's Passport share. The
per-cell ratios are shipped and the page uses the one matching the selection.
Cells at 1x are the audiences Passport lists no brands for, which the site
deliberately holds at convenience scale rather than inventing a lift for.

Panel dollars are what the simulation actually produces; the all-channel figure
is a clearly-labelled conversion of it, not a second measurement.

    python data/scripts/add_montecarlo.py --dry
    python data/scripts/add_montecarlo.py

stdlib only. Writes `audiences.opportunity.montecarlo`.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_survival import load, FIRST_COHORT, LAST_COMPLETE, SCALE_BAR  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGG = os.path.join(ROOT, "public/data/dashboard.json")

HORIZON = 5          # years simulated
MIN_DONORS = 20      # below this a pool is too thin to sample on its own


def trajectories():
    """Per-launch revenue for years 1..HORIZON, truncated at the last complete year."""
    out = []
    for s in load():
        if not (FIRST_COHORT <= s["launch"] <= LAST_COMPLETE):
            continue
        if s["first_seen"] < FIRST_COHORT - 1:
            continue
        observed = LAST_COMPLETE - s["launch"] + 1          # years we can actually see
        if observed < 1:
            continue
        path = [round(s["rev"].get(s["launch"] + k, 0.0))
                for k in range(min(observed, HORIZON))]
        out.append({
            "p": path,                                       # observed years only
            "a": s["aud"] if s["aud"] != "Unknown" else "",
            "f": s["fam"] if s["fam"] != "Unknown" else "",
            "z": s["size"],
            "b": s["brand"],
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    tr = trajectories()

    # How many donors cover each year of the horizon? A year backed by 30
    # trajectories is a different claim from one backed by 700.
    depth = [sum(1 for t in tr if len(t["p"]) >= k) for k in range(1, HORIZON + 1)]

    with open(AGG) as f:
        agg = json.load(f)
    opp = agg["audiences"]["opportunity"]
    dem = agg["audiences"]["demand"]

    # Panel -> all-channel. A single global factor would be too blunt: the
    # matrix carries both scales per cell and the ratio varies a lot by
    # audience, because Passport share does. Ship the per-cell ratios and let
    # the page use the one that matches the selection, falling back to the
    # pooled figure only when a cell has no measured PDI dollars.
    cell_scale = {}
    for r in opp["matrix"]:
        for c in r["row"]:
            if c.get("rev_pdi", 0) > 0 and c.get("rev", 0) > 0:
                cell_scale[f"{r['aud']}|{c['fam']}"] = round(c["rev"] / c["rev_pdi"], 2)
    pdi = sum(c.get("rev_pdi", 0) for r in opp["matrix"] for c in r["row"])
    allc = sum(c.get("rev", 0) for r in opp["matrix"] for c in r["row"])
    scale = round(allc / pdi, 2) if pdi else 1.0

    out = {
        "horizon": HORIZON,
        "n": len(tr),
        "depth": depth,
        "min_donors": MIN_DONORS,
        "scale": scale,
        "cell_scale": cell_scale,
        "scale_bar": SCALE_BAR,
        "window": {"first_cohort": FIRST_COHORT, "last_complete": LAST_COMPLETE},
        "market_cagr": round(((dem["future"]["market"] / dem["now"]["market"]) ** (1 / 5) - 1) * 100, 2),
        "trajectories": tr,
        "method": (
            "Bootstrap over real launches rather than a fitted distribution. Each trial "
            "resamples one whole observed trajectory from a comparable launch, so survival, "
            "skew and year-to-year autocorrelation come from the data instead of from "
            "assumptions. The donor pool is horizon-matched: a five-year run samples only "
            "launches with five observed years. Zero-padding short trajectories would count "
            "'not yet happened' as 'did not happen'; splicing two donors together would "
            "graft a survivor's later years onto a product that had already died."
        ),
        "caveat": (
            "This is the distribution of outcomes comparable launches produced. It cannot "
            "know whether a specific product is good, and it can only generate futures that "
            "resemble the measured past - convenience-channel, 2020 onward. Read the spread, "
            "not the median."
        ),
    }

    if args.dry:
        print(json.dumps({k: v for k, v in out.items() if k != "trajectories"}, indent=1))
        print(f"\ntrajectories: {len(tr)}")
        print(f"donors covering year k: {depth}")
        tot = sorted(sum(t['p']) for t in tr)
        print(f"5yr panel revenue  p50 ${tot[len(tot)//2]:,}  "
              f"p90 ${tot[int(len(tot)*0.9)]:,}  max ${tot[-1]:,}")
        return

    opp["montecarlo"] = out
    with open(AGG, "w") as f:
        json.dump(agg, f, separators=(",", ":"))
    print(f"wrote {len(tr)} donor trajectories (scale x{scale}) -> {AGG}")


if __name__ == "__main__":
    main()
