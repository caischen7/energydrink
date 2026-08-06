#!/usr/bin/env python3
"""
Fold the BigQuery-derived aggregates into public/data/dashboard.json.

Kept separate from build_dashboard_json.py on purpose: that script reduces the
scraped CSV corpus, while these two tables come out of the licensed capstone
BigQuery project via data/sql/*.sql. Different provenance, different refresh
cadence, different access requirements — so they stay decoupled.

Idempotent: re-running just overwrites the two keys it owns.

Run it AFTER build_dashboard_json.py (which rewrites the whole file):

    python data/scripts/build_dashboard_json.py
    python data/scripts/add_bq_panels.py
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DERIVED = os.path.join(ROOT, "data", "bq", "derived")
OUT = os.path.join(ROOT, "public", "data", "dashboard.json")


def rows(name):
    p = os.path.join(DERIVED, name)
    if not os.path.exists(p):
        print(f"  ! missing {name} — skipping")
        return []
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


pos_momentum = [
    {
        "brand": r["brand"],
        "revenue": f(r["t12m_revenue"]),
        "prior_revenue": f(r["prior_12m_revenue"]),
        "yoy": f(r["yoy_pct"]),
        "share": f(r["share_pct"]),
        "share_delta": f(r["share_delta_pp"]),
    }
    for r in rows("brand_momentum_real.csv")
]
launch_claims = [
    {
        "claim": r["claim"],
        "early": f(r["pct_2018_2020"]),
        "late": f(r["pct_2024_2026"]),
        "delta": f(r["delta_pp"]),
        "n": int(f(r["n_total"]) or 0),
    }
    for r in rows("gnpd_claim_trends.csv")
]

with open(OUT, encoding="utf-8") as fh:
    data = json.load(fh)
data["pos_momentum"] = pos_momentum
data["launch_claims"] = launch_claims
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(data, fh, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

print(f"Added pos_momentum ({len(pos_momentum)} brands) + "
      f"launch_claims ({len(launch_claims)} claims) -> {OUT}")
