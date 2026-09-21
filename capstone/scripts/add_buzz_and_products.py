#!/usr/bin/env python3
"""Fold YouTube buzz and top-product rankings into public/data/flavor_year.json.

    python capstone/scripts/add_buzz_and_products.py

Idempotent; rewrites the two keys it owns. Run after analyze_flavor_year.py and
analyze_youtube.py. stdlib only.

WHY BUZZ AND SALES BELONG ON ONE PAGE BUT NOT ONE AXIS
------------------------------------------------------
The study's whole question is where stated preference and revealed preference
disagree. PDI says what people bought; YouTube says what they talk about. The
interesting flavors are the ones where those two diverge, so the page reports a
RATIO of the two shares rather than plotting dollars against mentions - they
share no unit and a dual axis would let the chart say anything.

Both are converted to SHARE first, which is what makes them comparable at all:
one is a share of category units, the other a share of flavor mentions. Neither
is a count of the same thing, and the page says so.

THE ROLLUP, AND ITS ONE JUDGEMENT CALL
--------------------------------------
YouTube mentions are specific flavors (Mango, Strawberry); PDI is families
(Tropical, Berry). The former roll up to the latter through the SAME
flavor_family() the PDI side uses, so the two are binned identically.

"Zero Sugar" is dropped from the rollup. It is in the alias table because it is
worth counting, but it is a positioning attribute rather than a flavor, and
flavor_family() sends it to "Novelty & branded" where it would silently inflate
a family it has nothing to do with. It stays in the raw YouTube CSV.

WHAT THE PRODUCT RANKING CAN AND CANNOT SAY
-------------------------------------------
PDI's PRODUCT_DESCRIPTION is sparse on exactly the best sellers: several of the
top SKUs read only "MONSTER" or "RED BULL", with no size or flavor. Two Monster
rows at $79.2M and $57.1M cannot be distinguished from each other at all.

That is not hidden here. Each row is flagged `resolved` or not, and the page
reports how much of the top-20 revenue sits behind an uninformative label. A
product ranking that quietly presented those as distinct products would be
inventing precision the source does not have.
"""
import collections
import csv
import datetime as dt
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "capstone/collectors"))
from flavor_mentions import to_family  # noqa: E402

TARGET = os.path.join(ROOT, "public/data/flavor_year.json")
DASH = os.path.join(ROOT, "public/data/dashboard.json")

# Counted in the corpus, but not flavors. See the docstring.
NOT_A_FLAVOR = {"Zero Sugar", "Original"}

# Floors below which a buzz-to-sales ratio is arithmetic, not a finding.
MIN_SALES_SHARE = 0.5     # percent of category units
MIN_MENTIONS = 150        # YouTube mentions for the family


def latest(pattern):
    hits = sorted(glob.glob(os.path.join(ROOT, pattern)))
    return hits[-1] if hits else None


def buzz(pdi_last_year):
    """YouTube mention share per PDI family, against that family's unit share."""
    path = latest("data/youtube/flavor_pulse_yt_*.csv")
    if not path:
        return None
    rows = list(csv.DictReader(open(path, encoding="utf-8")))

    fam = collections.defaultdict(lambda: {"mentions": 0, "fav": 0, "pos": 0,
                                           "neg": 0, "neu": 0, "sent": 0.0})
    dropped = []
    for r in rows:
        if r["name"] in NOT_A_FLAVOR:
            dropped.append(r["name"])
            continue
        d = fam[to_family(r["name"])]
        d["mentions"] += int(r["mentions"])
        d["fav"] += int(r["fav"])
        for k in ("pos", "neg", "neu"):
            d[k] += int(r[k])
        d["sent"] += float(r["mean_compound"]) * int(r["mentions"])

    total = sum(v["mentions"] for v in fam.values()) or 1
    sales = {r["cluster"]: r["unit_share_pct"] for r in pdi_last_year}

    out = []
    for k, v in fam.items():
        buzz_share = v["mentions"] / total * 100
        sold = sales.get(k)
        out.append({
            "family": k,
            "mentions": v["mentions"],
            "buzz_share_pct": round(buzz_share, 2),
            "sales_share_pct": sold,
            # >1 means more discussed than bought. Reported as a ratio because
            # the two shares are shares OF DIFFERENT THINGS and a difference in
            # percentage points between them would be meaningless.
            "buzz_to_sales": round(buzz_share / sold, 2) if sold else None,
            # A ratio is only as stable as its denominator. Cola & soda holds
            # 0.031% of units, so ANY buzz divides into a 159x ratio that says
            # far more about the denominator than about consumer interest. Any
            # family under MIN_SALES_SHARE or MIN_MENTIONS is marked unstable
            # and the page ranks it separately rather than letting an artefact
            # lead the chart.
            "stable": bool(sold and sold >= MIN_SALES_SHARE
                           and v["mentions"] >= MIN_MENTIONS),
            "fav_share_pct": round(v["fav"] / v["mentions"] * 100, 1) if v["mentions"] else 0,
            "net_sentiment": round((v["pos"] - v["neg"]) / v["mentions"], 3) if v["mentions"] else 0,
        })
    # Stable rows first, by ratio; unstable ones after, so the chart is led
    # by families the comparison can actually support.
    out.sort(key=lambda r: (not r["stable"], -(r["buzz_to_sales"] or 0)))
    return {"families": out, "total_mentions": total,
            "min_sales_share": MIN_SALES_SHARE, "min_mentions": MIN_MENTIONS,
            "n_unstable": sum(1 for r in out if not r["stable"]),
            "excluded": sorted(set(dropped)),
            "source": os.path.relpath(path, ROOT)}


def products():
    """Top SKUs by trailing-12-month revenue, with a resolvability flag."""
    if not os.path.exists(DASH):
        return None
    d = json.load(open(DASH, encoding="utf-8"))
    seg = d.get("segments")
    if not seg:
        return None

    rows = []
    for c in seg["cats"]:
        for p in c.get("prod", []):
            desc = (p.get("d") or "").strip()
            # A description is uninformative when it is only the brand name -
            # no size, no flavor, nothing to tell two SKUs apart.
            bare = re.sub(r"[^A-Z ]", "", desc.upper()).strip()
            resolved = bool(re.search(r"\d|\bOZ\b", desc, re.I)) and len(desc) > len(p.get("b", "")) + 4
            rows.append({
                "brand": p.get("b", ""), "desc": desc or "(blank)",
                "flavor": p.get("fl", "") or "", "size": p.get("sz", "") or "",
                "revenue": p.get("r", 0), "stores": p.get("st", 0),
                "segment": c["name"], "resolved": resolved,
            })
    rows.sort(key=lambda r: -r["revenue"])
    top = rows[:20]
    unresolved_rev = sum(r["revenue"] for r in top if not r["resolved"])
    total_rev = sum(r["revenue"] for r in top) or 1
    return {
        "top": top,
        "n_products": len(rows),
        "unresolved_share_pct": round(unresolved_rev / total_rev * 100, 1),
        "window": seg.get("window", ""),
    }


def main():
    payload = json.load(open(TARGET, encoding="utf-8"))
    last = payload["years"][-1]
    pdi_last = [r for r in payload["families"] if r["year"] == last]

    payload["buzz"] = buzz(pdi_last)
    payload["products"] = products()
    payload["buzz_products_generated_at"] = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    tmp = TARGET + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(payload, fh, separators=(",", ":"))
    os.replace(tmp, TARGET)

    b, p = payload["buzz"], payload["products"]
    print(f"wrote {os.path.relpath(TARGET, ROOT)} ({os.path.getsize(TARGET)/1024:.0f} KB)")
    if b:
        print(f"\n  BUZZ vs SALES ({b['total_mentions']:,} mentions, excluded {b['excluded']})")
        print(f"  {'family':<22}{'buzz%':>7}{'sales%':>8}{'ratio':>7}")
        for r in b["families"]:
            flag = "" if r["stable"] else "   <- unstable, small denominator"
            print(f"  {r['family']:<22}{r['buzz_share_pct']:>7}"
                  f"{r['sales_share_pct'] if r['sales_share_pct'] is not None else '-':>8}"
                  f"{r['buzz_to_sales'] if r['buzz_to_sales'] else '-':>7}{flag}")
    if p:
        print(f"\n  TOP PRODUCTS — {p['unresolved_share_pct']}% of top-20 revenue "
              f"sits behind a description too sparse to identify the SKU")


if __name__ == "__main__":
    main()
