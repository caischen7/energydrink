#!/usr/bin/env python3
"""Workstream 0 — emit the PRE-REGISTERED SKU universe for the flavor study.

    python capstone/scripts/build_registry.py            # writes capstone/registry/*_v1.0_<date>.csv
    python capstone/scripts/build_registry.py --check    # re-derive and diff, write nothing

Two registries plus an open-decisions log, each date-stamped and versioned.
Once Cai approves them they are FROZEN: any later change needs a new version
number and a row in capstone/assumptions.md saying what changed and why.

WHY THIS IS A SCRIPT AND NOT A HAND-TYPED CSV
---------------------------------------------
A committee can ask "where did this brand list come from". The answer has to be
a re-runnable derivation from a named source file, not a spreadsheet someone
typed. `--check` re-derives and diffs, so drift between the registry and its
source is detectable rather than invisible.

SOURCES, AND WHAT EACH ONE CAN AND CANNOT SUPPORT
-------------------------------------------------
  data/bq/derived/brand_momentum_real.csv
      22 brands, PDI convenience panel, trailing 12 months vs prior 12, partial
      final month excluded. REVENUE, not units - see LIMITATION 1 below.

  data/scripts/classify_target_consumers.py  (FLAVOR_FAMILIES / flavor_family)
      The taxonomy already in production on this repo's dashboard. The registry
      IMPORTS it rather than restating it: CLAUDE.md records that an earlier
      draft hand-copied these rules, got cherry and mango wrong, and silently
      disagreed with every other page. A second copy is a defect, not a record.

LIMITATION 1 - REVENUE IS NOT VOLUME. The brief asks for "top brands by PDI
volume". This ranks by DOLLARS, because dollars are what the committed source
carries. Red Bull's price per ounce is well above the category's, so a revenue
ranking flatters it relative to a unit ranking. The ordering of the top 10 is
unlikely to change much, but the SHARES would. Confirm with a units query
(SUM(QUANTITY)) before any share number reaches the committee.

LIMITATION 2 - NO RECORDED QUERY. add_bq_panels.py's docstring points at
`data/sql/*.sql` and pos-momentum.js points at `docs/bigquery-findings.md`.
Neither exists in this repo. So the brand file's exact WHERE clause, category
filter and brand-normalisation step are unverified. This is the single biggest
provenance gap in Workstream 0 and it is logged as decision D-07.
"""
import argparse
import csv
import datetime as dt
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_BRANDS = os.path.join(ROOT, "data/bq/derived/brand_momentum_real.csv")
OUT_DIR = os.path.join(ROOT, "capstone/registry")
VERSION = "1.0"
STAMP = dt.date.today().isoformat()

sys.path.insert(0, os.path.join(ROOT, "data/scripts"))
from classify_target_consumers import FLAVOR_FAMILIES, flavor_family  # noqa: E402

# --- Tier A rule -------------------------------------------------------------
# Top N by PDI trailing-12-month revenue. N=10 is chosen because it is the
# smallest cut that both clears 94% of measured category revenue AND contains
# every brand Cai named except Prime - so the cut is defensible on the data and
# does not quietly drop a brand the research question already committed to.
TIER_A_N = 10

# --- Tier B: included for a reason OTHER than size ---------------------------
# Each needs a written justification, because "it felt relevant" is not a
# pre-registration.
TIER_B = {
    "Prime": (
        "Named in the research brief and culturally salient, but it is NOT in "
        "the top-22 PDI list: roughly $1.8M T12M (~0.13% share), read off the "
        "segments payload. Keep it precisely BECAUSE of that gap - it is the "
        "cleanest available test of the high-buzz / low-sales disagreement the "
        "final synthesis is meant to surface. Treat it as a case study, never "
        "as a row in a velocity ranking."
    ),
}

BRAND_NOTES = {
    "Ghost": (
        "NORMALISATION HAZARD. The two committed files disagree: segments "
        "carries 'Ghost Energy' ($35.96M) and 'Ghost' ($6.96M) as separate "
        "brands; brand_momentum merges them into 'Ghost' ($42.86M). Pin one "
        "mapping in brand_alias before any brand-level number is quoted. D-06."
    ),
    "Bang": "Declining (-15.6% YoY). Retained: a falling brand is signal for the study, not noise.",
    "Reign": "Declining (-16.7% YoY). Retained for the same reason as Bang.",
    "Alani Nu": "+95.8% YoY, +2.62pp share - the fastest riser in the panel. Flavor-led growth, so high value here.",
    "Red Bull": "Revenue rank #1, but see LIMITATION 1: a units ranking would narrow the gap to Monster.",
    "NOS": "Not named in the brief. Included on the data: #8 by revenue, ahead of both Reign and Bang.",
    "Rockstar": "Not named in the brief. Included on the data: #7 by revenue, ahead of both Reign and Bang.",
}


# --- Open decisions: things only Cai can settle -----------------------------
# Every one of these is a real fork found by auditing the data, not a checklist
# item. "options" is what could be done; "recommendation" is what I would do and
# why; "status" stays OPEN until Cai rules.
DECISIONS = [
    ("D-01", "WS0 taxonomy", "'Melon & other' never fires",
     "Declared as 1 of 14 families but absent from all 1,260 family rows in price_panel.csv. "
     "'Punch & mixed fruit' is ordered earlier and its regex contains `melon`, so it swallows "
     "every melon string; only a bare 'cantaloupe' can reach it, and 'cucumber' loses to "
     "'Tea & botanical' on `mint`.",
     "(a) delete the family; (b) move it above 'Punch & mixed fruit'; (c) keep it documented as dead",
     "(b) if honeydew/cantaloupe flavors matter to white space - melon is a live launch space - "
     "otherwise (a). Do NOT leave a declared family that cannot occur: a committee will ask."),

    ("D-02", "WS0 taxonomy", "'Mango Peach' resolves to Tropical, not Peach",
     "'Tropical' is ordered before 'Peach & stone fruit' and matches `mango`, so the literal "
     "`mango peach` alternative inside the Peach regex is unreachable dead code.",
     "(a) accept Tropical and delete the dead alternative; (b) hoist a two-fruit rule above both",
     "(a). The dead alternative implies an intent the code does not honour, which is worse than "
     "either assignment."),

    ("D-03", "WS0 taxonomy", "Format words beat fruit words",
     "'Grape Slush' -> 'Sour & candy' (not Grape) because `slush` sits in the earlier rule. Same "
     "for 'Blue Razz', 'Cotton Candy'. This is a real choice: it groups by the SENSORY PROMISE "
     "(candy-sweet) rather than the fruit. It materially affects Alani Nu, whose slush line is "
     "a growth driver.",
     "(a) keep format-first; (b) let fruit win and treat candy/slush as a separate flag column",
     "(b) for this study. 'Which flavor sells' is a fruit question; candy-format is a second, "
     "orthogonal attribute and collapsing the two loses the ability to ask either cleanly."),

    ("D-04", "WS0 taxonomy", "Cherry is Berry, not stone fruit",
     "`cherry` sits inside the Berry regex. Botanically a stone fruit; commercially it behaves "
     "like a berry (Cherry Limeade, Cherry Slush). Deliberate in the source, per CLAUDE.md.",
     "(a) keep in Berry; (b) move to Peach & stone fruit",
     "(a) keep. Commercial behaviour beats botany for a go-to-market study - but state it in the "
     "methods note, because a reader will notice."),

    ("D-05", "WS0 brands", "Prime is in the brief but not in the PDI top 22",
     "~$1.8M T12M (~0.13% share) against Bang's $21.9M. PDI also carries 'PRIME ENERGY ...' and "
     "'PRIME ... SPORTS DRINKS' descriptions under one brand string - two different products.",
     "(a) drop Prime; (b) keep as Tier B case study; (c) keep and split energy vs hydration SKUs",
     "(b), and filter to 'PRIME ENERGY' descriptions only if it ever enters a sales ranking. "
     "Prime's hydration line is not an energy drink and must not be summed into one."),

    ("D-06", "WS0 brands", "Ghost is normalised two different ways",
     "segments: 'Ghost Energy' $35.96M + 'Ghost' $6.96M. brand_momentum: 'Ghost' $42.86M. The "
     "sum reconciles, so it is a normalisation difference and not a data difference.",
     "(a) adopt the merged form in brand_alias; (b) keep split if the two are genuinely different lines",
     "(a) merged, unless Ghost sells a non-energy line in this panel - check before freezing."),

    ("D-07", "WS0 provenance", "The brand ranking has no recorded query",
     "add_bq_panels.py points at `data/sql/*.sql`; pos-momentum.js points at "
     "`docs/bigquery-findings.md`. NEITHER EXISTS in this repo. So the category filter, date "
     "window and brand normalisation behind brand_momentum_real.csv are unverified.",
     "(a) re-derive from pdi_daily_agg and commit the SQL; (b) cite the CSV as-is",
     "(a), before the committee sees a number from it. This is the weakest link in WS0: every "
     "brand share here inherits an unaudited WHERE clause."),

    ("D-08", "WS0 brands", "Ranking is by revenue; the brief says volume",
     "brand_momentum_real.csv carries dollars only. Red Bull's price per ounce is above the "
     "category average, so its 37.9% revenue share overstates its unit share.",
     "(a) re-rank on SUM(QUANTITY); (b) keep revenue and relabel every axis 'revenue share'",
     "(a). WS2 ranks on velocity in UNITS per store-week anyway, so the universe should be "
     "selected on the same basis it will be measured on."),
]


def brand_rows():
    src = list(csv.DictReader(open(SRC_BRANDS, encoding="utf-8")))
    src.sort(key=lambda r: -float(r["t12m_revenue"]))
    rows, cum = [], 0.0
    for i, r in enumerate(src, 1):
        cum += float(r["share_pct"])
        if i > TIER_A_N:
            break
        rows.append({
            "brand_id": r["brand"].lower().replace(" ", "_").replace("(", "").replace(")", ""),
            "brand_canonical": r["brand"],
            "tier": "A",
            "inclusion_rule": f"top {TIER_A_N} by PDI T12M revenue",
            "pdi_rank": i,
            "pdi_t12m_revenue_usd": round(float(r["t12m_revenue"]), 2),
            "pdi_share_pct": r["share_pct"],
            "pdi_cum_share_pct": round(cum, 2),
            "pdi_yoy_pct": r["yoy_pct"],
            "pdi_share_delta_pp": r["share_delta_pp"],
            "in_original_brief": "yes" if r["brand"] not in ("Rockstar", "NOS") else "no",
            "notes": BRAND_NOTES.get(r["brand"], ""),
        })
    for name, why in TIER_B.items():
        rows.append({
            "brand_id": name.lower(), "brand_canonical": name, "tier": "B",
            "inclusion_rule": "strategic - see notes", "pdi_rank": "",
            "pdi_t12m_revenue_usd": "", "pdi_share_pct": "", "pdi_cum_share_pct": "",
            "pdi_yoy_pct": "", "pdi_share_delta_pp": "",
            "in_original_brief": "yes", "notes": why,
        })
    return rows


# Probe strings whose assignment is decided by ORDER rather than by the obvious
# fruit. Each is run through the live flavor_family() so the registry records
# what the code ACTUALLY does, not what the rule list appears to say.
PROBES = [
    "Mango Peach", "Cherry", "Cherry Limeade", "Honeydew Melon", "Cantaloupe",
    "Cucumber Mint", "Vanilla", "Cream Soda", "Strawberry Watermelon",
    "Blue Razz", "Grape Slush", "Tropical Punch", "Orange Mango",
    "Apple Cranberry", "Dragon Fruit", "Cotton Candy", "Frose Rose",
]


def taxonomy_rows():
    """One row per family, in PRECEDENCE order - which is the whole mechanism.

    Mutual exclusivity here is not a property of the regexes (they overlap
    heavily); it is produced by first-match-wins over an ordered list. So the
    registry records the ORDER as the rule, and names which earlier family
    shadows each one."""
    observed = set()
    try:
        panel = os.path.join(ROOT, "data/bq/derived/price_panel.csv")
        observed = {r["cluster"] for r in csv.DictReader(open(panel, encoding="utf-8"))
                    if r["scheme"] == "family"}
    except OSError:
        pass

    rows = []
    for i, (name, rx) in enumerate(FLAVOR_FAMILIES, 1):
        shadowed_by = [n for n, _ in FLAVOR_FAMILIES[:i - 1]
                       if any(flavor_family({"FLAVOR": p}) == n
                              and __import__("re").search(rx, p, __import__("re").I)
                              for p in PROBES)]
        rows.append({
            "precedence": i,
            "family_id": name.lower().replace(" & ", "_").replace(" ", "_"),
            "family_name": name,
            "match_regex": rx,
            "matched_against": "FLAVOR, falling back to PRODUCT_DESCRIPTION when FLAVOR is blank",
            "observed_in_pdi_panel": "yes" if name in observed else "NO - never fires",
            "shadowed_by": "; ".join(shadowed_by),
            "status": "active" if name in observed else "DEAD - see D-01",
        })
    for name, note in (
        ("Novelty & branded", "Fallback when FLAVOR is non-empty but matches no rule "
                              "(Frose Rose, Cosmic Stardust). Mintel's 'branded flavors' trend."),
        ("Unspecified", "FLAVOR and PRODUCT_DESCRIPTION both empty, or FLAVOR empty and the "
                        "description names no flavor. 499 of 2,309 SKUs have a blank FLAVOR."),
    ):
        rows.append({
            "precedence": "fallback", "family_id": name.lower().replace(" & ", "_").replace(" ", "_"),
            "family_name": name, "match_regex": "", "matched_against": "",
            "observed_in_pdi_panel": "yes" if name in observed else "unknown",
            "shadowed_by": "", "status": "active - " + note,
        })
    return rows


def probe_rows():
    """The order-collision audit, as evidence attached to the registry."""
    import re
    out = []
    for p in PROBES:
        got = flavor_family({"FLAVOR": p})
        also = [n for n, rx in FLAVOR_FAMILIES if re.search(rx, p, re.I) and n != got]
        out.append({
            "probe_flavor": p, "assigned_family": got,
            "also_matches": "; ".join(also),
            "decided_by_order": "yes" if also else "no",
        })
    return out


def write(name, rows, check):
    path = os.path.join(OUT_DIR, f"{name}_v{VERSION}_{STAMP}.csv")
    if check:
        prior = sorted(f for f in os.listdir(OUT_DIR) if f.startswith(name + "_v"))
        if not prior:
            print(f"  {name}: no prior version to diff")
            return
        old = list(csv.DictReader(open(os.path.join(OUT_DIR, prior[-1]), encoding="utf-8")))
        same = [dict(r) for r in old] == [{k: str(v) for k, v in r.items()} for r in rows]
        print(f"  {name}: {'unchanged' if same else 'DIFFERS from ' + prior[-1]}")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {os.path.relpath(path, ROOT)}  ({len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff against the newest version; write nothing")
    args = ap.parse_args()

    brands = brand_rows()
    write("brands", brands, args.check)
    write("flavor_taxonomy", taxonomy_rows(), args.check)
    write("flavor_order_probes", probe_rows(), args.check)
    write("open_decisions", [
        {"decision_id": d[0], "workstream": d[1], "item": d[2], "evidence": d[3],
         "options": d[4], "recommendation": d[5], "status": "OPEN", "resolved_by": "",
         "resolved_date": ""} for d in DECISIONS], args.check)

    if not args.check:
        a = [b for b in brands if b["tier"] == "A"]
        print(f"\n  Tier A: {len(a)} brands, {a[-1]['pdi_cum_share_pct']}% of PDI T12M revenue")
        print(f"  Tier B: {len(brands) - len(a)}")
        print(f"  {len(DECISIONS)} decisions OPEN - registry is NOT frozen until they are ruled on")


if __name__ == "__main__":
    main()
