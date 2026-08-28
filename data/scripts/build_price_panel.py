#!/usr/bin/env python3
"""Build the price panel: cluster x month price, volume, distribution and promo depth.

Feeds data/scripts/price_models.py. Reads pdi_daily_agg (licensed, BigQuery) and
writes two files:

    data/bq/price_panel_sku.csv          SKU x month   — LICENSED, gitignored
    data/bq/derived/price_panel.csv      cluster x month — derived, committed

THERE IS NO PRICE COLUMN IN PDI
-------------------------------
Price is derived as revenue / units. At SKU x month that is a defensible
"realized average unit price": net of promotions, net of pack-size deals, and
net of store-to-store variation. It is NOT shelf price and NOT a posted list
price, and every output here is labelled accordingly.

THE UNIT-VALUE TRAP, AND THE TWO PRICE SERIES THIS WRITES
---------------------------------------------------------
Aggregating revenue/units to a CLUSTER is where naive versions of this analysis
go wrong. Sum revenue and sum units across a cluster and you get a unit-value
index, which moves when the MIX moves even if no product changed price:

    Month 1:  1000 x 12oz @ $2.00              unit value = $2.00
    Month 2:   500 x 12oz @ $2.00
               500 x 24oz @ $4.00              unit value = $3.00

Nothing repriced. The index rose 50% because a bigger pack outsold a smaller
one. Regressing volume on that series measures mix, not price response, and it
is biased toward finding a spurious positive elasticity (periods with more
large-format sales look both higher-priced and higher-revenue).

So this writes TWO price series per cluster-month:

  price_unitvalue   sum(revenue)/sum(units). Simple, and what most people
                    compute. Kept because it is what a reader expects to see,
                    and because the gap between the two series is itself the
                    diagnostic for how much mix is moving.

  price_index       A fixed-weight (Laspeyres) index over the SKUs present in
                    BOTH the base window and the current month:

                        I_t = sum_i (p_it * q_i0) / sum_i (p_i0 * q_i0)

                    Base weights q_i0 are frozen at the base window, so the
                    index moves only when individual SKUs reprice. This is the
                    series the models should use.

  matched_share     Share of cluster revenue covered by the matched basket. When
                    this is low the index is speaking for a small slice, so the
                    models must not treat those months as equally informative.

PROMOTION DEPTH
---------------
QUANTITY_WITH_DISCOUNT / QUANTITY gives a discount rate per cell per month. This
is the most valuable column pair in the table for this problem: price is
endogenous to demand, and an observed promo rate is the closest thing available
to a supply-side shifter.

    NOT YET VERIFIED: whether those columns are actually populated across the
    window, or are null/zero for most rows. --probe checks exactly that and
    costs about $0.05. Run it before trusting any identification strategy that
    leans on promo depth.

    python data/scripts/build_price_panel.py --probe     # are the promo cols real?
    python data/scripts/build_price_panel.py --dry-run   # cost only
    python data/scripts/build_price_panel.py

Reads BigQuery via a pasted OAuth token in BQ_TOKEN. stdlib only.
"""
import argparse
import collections
import csv
import json
import os
import statistics
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKU_OUT = os.path.join(ROOT, "data/bq/price_panel_sku.csv")
CLUSTER_OUT = os.path.join(ROOT, "data/bq/derived/price_panel.csv")
PROJECT = "msbai-capstone-energydrinks"

FIRST, LAST = "2019-01-01", "2025-12-31"

# Base window for the fixed-weight index. Twelve months, so the weights are not
# hostage to one month's promo calendar, and early enough that most of the
# window is forecastable from it.
BASE_FROM, BASE_TO = "2019-01", "2019-12"

# A SKU-month with almost no units gives a wild revenue/units ratio - one
# mis-scanned unit produces a $40 "price". These bounds drop those rows rather
# than letting them set a cluster's mean.
MIN_UNITS = 25
PRICE_LO, PRICE_HI = 0.40, 25.00


def bq(sql, token, dry=False):
    body = json.dumps({"query": sql, "useLegacySql": False,
                       "dryRun": dry, "timeoutMs": 300000}).encode()
    req = urllib.request.Request(
        f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}/queries",
        data=body, headers={"Authorization": "Bearer " + token,
                            "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))


def rows_of(res, token):
    fields = [f["name"] for f in res["schema"]["fields"]]
    out, job = [], res["jobReference"]["jobId"]
    while True:
        for r in res.get("rows", []):
            out.append(dict(zip(fields, [c["v"] for c in r["f"]])))
        page = res.get("pageToken")
        if not page:
            return out
        u = (f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT}"
             f"/queries/{job}?pageToken={page}&timeoutMs=300000")
        res = json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers={"Authorization": "Bearer " + token}),
            timeout=600))


# Only the columns needed. BigQuery bills by column, which is what keeps a
# 420 GB table near $0.55 rather than the full scan price.
SQL = f"""
SELECT
  d.GTIN,
  FORMAT_DATE('%Y-%m', d.DATE)              AS m,
  SUM(d.TOTAL_REVENUE_AMOUNT)               AS rev,
  SUM(d.QUANTITY)                           AS units,
  SUM(d.TRANSACTION_COUNT)                  AS txns,
  SUM(d.QUANTITY_WITH_DISCOUNT)             AS disc_units,
  SUM(d.TRANSACTION_COUNT_WITH_DISCOUNT)    AS disc_txns,
  COUNT(DISTINCT d.STORE_ID)                AS stores
FROM `{PROJECT}.energy_drinks.pdi_daily_agg` d
WHERE d.DATE BETWEEN '{FIRST}' AND '{LAST}'
GROUP BY d.GTIN, m
"""

DIM = f"""
SELECT GTIN,
       ANY_VALUE(BRAND)             AS brand,
       ANY_VALUE(FLAVOR)            AS flavor,
       ANY_VALUE(PRODUCT_DESCRIPTION) AS descr,
       ANY_VALUE(UNIT_SIZE)         AS size,
       ANY_VALUE(PACK_SIZE)         AS pack,
       ANY_VALUE(PRODUCT_TYPE)      AS ptype,
       ANY_VALUE(SUB_PRODUCT_TYPE)  AS subtype
FROM `{PROJECT}.energy_drinks.pdi_master_gtin`
GROUP BY GTIN
"""

# Does the promo pair actually carry data? Cheap, and it decides whether the
# identification strategy downstream is viable at all.
PROBE = f"""
SELECT FORMAT_DATE('%Y', DATE) AS yr,
       COUNT(*)                                                   AS rows_,
       COUNTIF(QUANTITY_WITH_DISCOUNT IS NULL)                    AS disc_null,
       COUNTIF(QUANTITY_WITH_DISCOUNT > 0)                        AS disc_pos,
       SAFE_DIVIDE(SUM(QUANTITY_WITH_DISCOUNT), SUM(QUANTITY))    AS disc_rate
FROM `{PROJECT}.energy_drinks.pdi_daily_agg`
WHERE DATE BETWEEN '{FIRST}' AND '{LAST}'
GROUP BY yr ORDER BY yr
"""

# Flavor families come from classify_target_consumers.flavor_family, NOT a copy.
# An earlier draft of this file hand-rolled the mapping and got it materially
# wrong: the canonical rules are an ORDERED regex list where cherry -> Berry,
# mango -> Tropical, vanilla and horchata -> Coffee & cream, and there is a
# "Melon & other" family the copy omitted entirely. Duplicating that table would
# mean this panel's clusters silently disagreed with every other page on the
# site. It also needs PRODUCT_DESCRIPTION, because FLAVOR is blank on 499 SKUs.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify_target_consumers import flavor_family  # noqa: E402


def family(flavor, description):
    return flavor_family({"FLAVOR": flavor, "PRODUCT_DESCRIPTION": description})


def months_between(a, b):
    y, mo = int(a[:4]), int(a[5:7])
    ey, em = int(b[:4]), int(b[5:7])
    out = []
    while (y, mo) <= (ey, em):
        out.append(f"{y:04d}-{mo:02d}")
        mo += 1
        if mo == 13:
            y, mo = y + 1, 1
    return out


def laspeyres(sku_rows, months, base_months):
    """Fixed-weight price index per cluster-month, plus the basket's coverage.

    Returns {(cluster, month): (index, matched_revenue_share)}. Only SKUs with a
    base-window price AND a current-month price contribute, so the index never
    moves because a product entered or left - which is exactly the movement a
    unit-value series mistakes for repricing.
    """
    base_p, base_q = {}, {}
    per_sku = collections.defaultdict(dict)
    for r in sku_rows:
        per_sku[(r["cluster"], r["GTIN"])][r["m"]] = (r["price"], r["units"], r["rev"])

    for key, by_month in per_sku.items():
        ps = [(p, q) for m, (p, q, _v) in by_month.items() if m in base_months]
        if not ps:
            continue
        tot_q = sum(q for _p, q in ps)
        if tot_q <= 0:
            continue
        # Quantity-weighted base price, so a heavily-promoted base month does
        # not set the reference for the whole series.
        base_p[key] = sum(p * q for p, q in ps) / tot_q
        base_q[key] = tot_q / len(ps)

    out = {}
    by_cluster_month = collections.defaultdict(list)
    for (cluster, gtin), by_month in per_sku.items():
        for m, (p, q, v) in by_month.items():
            by_cluster_month[(cluster, m)].append((gtin, p, q, v))

    for (cluster, m), items in by_cluster_month.items():
        num = den = matched_rev = 0.0
        total_rev = sum(v for _g, _p, _q, v in items)
        for gtin, p, _q, v in items:
            key = (cluster, gtin)
            if key not in base_p:
                continue
            num += p * base_q[key]
            den += base_p[key] * base_q[key]
            matched_rev += v
        if den > 0:
            out[(cluster, m)] = (num / den, matched_rev / total_rev if total_rev else 0.0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--probe", action="store_true",
                    help="check whether the promo columns are populated (~$0.05)")
    args = ap.parse_args()

    token = os.environ.get("BQ_TOKEN", "").strip()
    if not token:
        sys.exit("BQ_TOKEN not set. From a shell with gcloud:\n"
                 "  gcloud auth application-default print-access-token")

    if args.probe:
        d = bq(PROBE, token, dry=True)
        print(f"probe scans {int(d['totalBytesProcessed'])/1e9:.1f} GB "
              f"(${int(d['totalBytesProcessed'])/1e12*6.25:.2f})")
        res = bq(PROBE, token)
        print(f"\n{'year':<6}{'rows':>14}{'disc NULL':>14}{'disc > 0':>12}{'disc rate':>11}")
        for r in rows_of(res, token):
            rate = float(r["disc_rate"]) if r["disc_rate"] else 0.0
            print(f"{r['yr']:<6}{int(r['rows_']):>14,}{int(r['disc_null']):>14,}"
                  f"{int(r['disc_pos']):>12,}{rate*100:>10.1f}%")
        print("\nIf disc NULL is ~every row, or the rate is 0, then promo depth is NOT usable\n"
              "and the identification strategy that leans on it has to be abandoned.")
        return

    if args.dry_run:
        for name, sql in (("panel", SQL), ("dimension", DIM)):
            d = bq(sql, token, dry=True)
            b = int(d["totalBytesProcessed"])
            print(f"{name:<10}{b/1e9:>8.1f} GB  ${b/1e12*6.25:.2f}")
        return

    print("querying pdi_daily_agg (GTIN x month) ...", flush=True)
    sku = rows_of(bq(SQL, token), token)
    print(f"  {len(sku):,} GTIN-month rows")
    print("querying pdi_master_gtin ...", flush=True)
    dim = {r["GTIN"]: r for r in rows_of(bq(DIM, token), token)}
    print(f"  {len(dim):,} GTINs")

    months = months_between(FIRST[:7], LAST[:7])
    base_months = set(months_between(BASE_FROM, BASE_TO))

    clean, dropped = [], collections.Counter()
    for r in sku:
        units = float(r["units"] or 0)
        rev = float(r["rev"] or 0)
        if units < MIN_UNITS:
            dropped["thin"] += 1
            continue
        price = rev / units
        if not (PRICE_LO <= price <= PRICE_HI):
            dropped["price out of range"] += 1
            continue
        d = dim.get(r["GTIN"], {})
        clean.append({
            "GTIN": r["GTIN"], "m": r["m"], "rev": rev, "units": units,
            "price": price,
            "txns": float(r["txns"] or 0),
            "disc_units": float(r["disc_units"] or 0),
            "disc_txns": float(r["disc_txns"] or 0),
            "stores": int(r["stores"] or 0),
            "brand": (d.get("brand") or "").strip(),
            "size": (d.get("size") or "").strip(),
            "pack": (d.get("pack") or "").strip(),
            "family": family(d.get("flavor"), d.get("descr")),
            "subtype": (d.get("subtype") or "").strip(),
        })
    print(f"  kept {len(clean):,}; dropped {sum(dropped.values()):,} "
          f"({dict(dropped)})")

    os.makedirs(os.path.dirname(SKU_OUT), exist_ok=True)
    with open(SKU_OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(clean[0].keys()))
        w.writeheader()
        w.writerows(clean)
    print(f"wrote {SKU_OUT}  (LICENSED — gitignored)")

    # ---- cluster x month -------------------------------------------------
    # Three cluster schemes, each answering a different slice of the request.
    # Ingredient clusters are deliberately absent here: they join for only ~a
    # quarter of GTINs, so they belong in their own file with their own coverage
    # statement rather than silently thinning this panel.
    schemes = {
        "family": lambda r: r["family"],
        "size": lambda r: r["size"] or "(unknown)",
        "brand": lambda r: r["brand"] or "(unknown)",
    }

    rows_out = []
    for scheme, keyfn in schemes.items():
        tagged = [dict(r, cluster=keyfn(r)) for r in clean]
        idx = laspeyres(tagged, months, base_months)
        agg = collections.defaultdict(lambda: collections.defaultdict(float))
        skus = collections.defaultdict(set)
        for r in tagged:
            k = (r["cluster"], r["m"])
            a = agg[k]
            a["rev"] += r["rev"]
            a["units"] += r["units"]
            a["txns"] += r["txns"]
            a["disc_units"] += r["disc_units"]
            a["disc_txns"] += r["disc_txns"]
            a["stores"] = max(a["stores"], r["stores"])
            skus[k].add(r["GTIN"])
        for (cluster, m), a in sorted(agg.items()):
            if a["units"] <= 0:
                continue
            i = idx.get((cluster, m), (None, 0.0))
            rows_out.append({
                "scheme": scheme, "cluster": cluster, "month": m,
                "rev": round(a["rev"], 2),
                "units": round(a["units"]),
                "skus": len(skus[(cluster, m)]),
                "stores": int(a["stores"]),
                "price_unitvalue": round(a["rev"] / a["units"], 4),
                "price_index": None if i[0] is None else round(i[0], 5),
                "matched_share": round(i[1], 4),
                "disc_rate": round(a["disc_units"] / a["units"], 4) if a["units"] else 0.0,
                "disc_txn_rate": round(a["disc_txns"] / a["txns"], 4) if a["txns"] else 0.0,
            })

    os.makedirs(os.path.dirname(CLUSTER_OUT), exist_ok=True)
    with open(CLUSTER_OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    print(f"wrote {CLUSTER_OUT}  ({len(rows_out):,} cluster-months)")

    # How far apart are the two price series? That gap IS the mix effect, and if
    # it is large the unit-value series should never be modelled.
    gaps = []
    for r in rows_out:
        if r["price_index"] and r["matched_share"] >= 0.5:
            gaps.append(abs(r["price_index"] - 1) * 100)
    if gaps:
        print(f"\nfixed-weight index moves a median {statistics.median(gaps):.1f}% from base; "
              f"compare with the unit-value series before trusting either.")


if __name__ == "__main__":
    main()
