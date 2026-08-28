#!/usr/bin/env python3
"""Put the White Space Finder's headroom on ONE comparable basis.

THE DEFECT
----------
`opportunity.matrix` cells carry two dollar figures:

    rev_pdi   revenue measured in PDI convenience
    rev       that figure lifted to all-channel scale by an audience-specific
              Euromonitor Passport factor

The factors are not close to each other. They run:

    Young adults 64.2   Women 30.1   Gym 22.1   Calorie-cutters 22.0
    Shift workers 8.8   Health-conscious 3.3
    Gamers 1.0          Coffee drinkers 1.0     Older functional 1.0

(the last three because Passport lists no brands for them, so they stay at
convenience scale).

The page then colours every cell by

    head = rps / medRPS,  where rps = rev / skus

`rev` is scaled; `skus` is the raw convenience SKU count. So the numerator
carries an audience-specific multiplier of between 1 and 64 that has nothing to
do with whether the pocket has room in it. Three audiences are multiplied by 1
and compared against rows multiplied by 64.

The result is the exact opposite of what a white-space finder is for. Measured:

    audience                  mean fill (current)   mean fill (one basis)
    Coffee drinkers                 0.020                  0.448
    Health-conscious adults         0.028                  0.207
    Older functional users          0.001                  0.043
    Shift workers & military        0.481                  0.669

Coffee drinkers renders as an entirely pale row - "no headroom anywhere" - and
on a comparable basis it has three saturated cells. The ranked `under` list is
worse: all 14 entries come from the four highest-factor audiences (Young adults,
Women, Gym, Calorie-cutters). Not one comes from an audience scaled by 1.0. That
list was ordering by the scaling factor, not by headroom.

`medRPS` was also unreproducible: stored $1.82M, against $0.28M for the median
of all cells, $1.60M for scaled-only and $0.012M for unscaled-only.

THE FIX
-------
Colour and rank by MEASURED revenue per SKU (`rev_pdi / skus`). Every row is
then on one basis - PDI convenience - which is the only source that sees flavor
at all, and is what the flavor proportions already come from. The scaled `rev`
stays as the number printed in the cell, because for reading absolute size it
is the better figure and it carries its own caveat.

`under` is re-ranked by an explicit rule, replacing a score formula that could
not be reproduced from the values it shipped with (head spanned 7.9-77.9 while
every score landed between 138.9 and 166.6). The superseded list is kept at
`under_legacy` for audit, the same way `demand.alt_mulo` preserves the
superseded MULO estimate.

    python data/scripts/fix_whitespace_scale.py            # report only
    python data/scripts/fix_whitespace_scale.py --write

stdlib only. Idempotent: rerunning recomputes from rev_pdi/skus, which the
script never modifies.
"""
import argparse
import json
import os
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGG = os.path.join(ROOT, "public/data/dashboard.json")

# A cell needs enough behind it to be an opportunity rather than a rounding
# error. One SKU earning everything is somebody's franchise, not an opening -
# the drill-down says so in words, and this keeps such cells out of the ranking.
MIN_SKUS = 3
MIN_REV = 250_000


def measured_rps(c):
    return c["rev_pdi"] / c["skus"] if c.get("skus") else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    with open(AGG) as f:
        agg = json.load(f)
    O = agg["audiences"]["opportunity"]
    unscaled = set(O["scaled"]["unscaled"])

    cells = [(r["aud"], c) for r in O["matrix"] for c in r["row"] if c.get("rev")]
    eligible = [(a, c) for a, c in cells if c["skus"] >= MIN_SKUS and c["rev_pdi"] >= MIN_REV]
    med = statistics.median([measured_rps(c) for a, c in eligible])

    print(f"cells with sales      {len(cells)}")
    print(f"eligible for ranking  {len(eligible)}  (>={MIN_SKUS} SKUs, >=${MIN_REV:,} measured)")
    print(f"median measured rps   ${med/1e6:.3f}M   (was medRPS ${O['medRPS']/1e6:.2f}M, "
          f"unreproducible)\n")

    # Per-cell measured headroom, written next to the existing fields rather
    # than over them: the scaled dollars stay correct for reading size.
    for _a, c in cells:
        c["rps_pdi"] = round(measured_rps(c), 2)
        c["head_pdi"] = round(measured_rps(c) / med, 3) if med else None

    print(f"{'audience':<28}{'fill now':>10}{'fill fixed':>12}{'delta':>8}")
    for r in O["matrix"]:
        cs = [c for c in r["row"] if c.get("rev")]
        if not cs:
            continue
        now = sum(min(1, (c["rps"] / O["medRPS"]) / 4) for c in cs) / len(cs)
        fix = sum(min(1, c["head_pdi"] / 4) for c in cs) / len(cs)
        flag = "   <- was scaled x1" if r["aud"] in unscaled else ""
        print(f"{r['aud']:<28}{now:>10.3f}{fix:>12.3f}{fix-now:>+8.3f}{flag}")

    # Re-rank. Headroom first, growth as the tie-break, both stated rather than
    # blended into an opaque score.
    ranked = sorted(
        ({"aud": a, "fam": c["fam"], "rev25": c["rev"], "rev_pdi": c["rev_pdi"],
          "skus": c["skus"], "rps": c["rps_pdi"], "head": c["head_pdi"],
          "cagr2y": c.get("cagr")} for a, c in eligible),
        key=lambda e: (-e["head"], -(e["cagr2y"] if e["cagr2y"] is not None else -999)),
    )[:14]

    print(f"\n{'RE-RANKED WHITE SPACE':<40}{'head':>7}{'skus':>6}{'measured':>11}{'cagr':>9}")
    for e in ranked:
        cagr = "      —" if e["cagr2y"] is None else f"{e['cagr2y']:>6.1f}%"
        print(f"  {e['aud'][:20]:<20}{e['fam'][:17]:<18}{e['head']:>6.1f}x{e['skus']:>6}"
              f"{e['rev_pdi']/1e6:>10.1f}M  {cagr}")

    before = {(e["aud"], e["fam"]) for e in O["under"]}
    after = {(e["aud"], e["fam"]) for e in ranked}
    print(f"\n{len(after - before)} of 14 ranked cells are new; "
          f"{len(before - after)} dropped out")
    auds_before = {e["aud"] for e in O["under"]}
    auds_after = {e["aud"] for e in ranked}
    print(f"  audiences represented: {len(auds_before)} -> {len(auds_after)}")

    if args.write:
        O["under_legacy"] = O["under"]
        O["under"] = ranked
        O["medRPS_pdi"] = round(med, 2)
        O["headroom_note"] = (
            "Headroom is measured PDI convenience revenue per SKU, not the "
            "all-channel scaled figure. The scaled dollars carry an "
            "audience-specific Passport factor between 1.0 and 64.2, so colouring "
            "by them ranked audiences by their scaling factor rather than by how "
            "contested the pocket is. The scaled figure is still what each cell "
            "prints, because for absolute size it is the better number."
        )
        with open(AGG, "w") as f:
            json.dump(agg, f, separators=(",", ":"))
        print(f"\nwrote medRPS_pdi, per-cell head_pdi and the re-ranked list -> {AGG}")
        print("superseded ranking kept at opportunity.under_legacy")


if __name__ == "__main__":
    main()
