#!/usr/bin/env python3
"""Build the Flavor Explorer index: monthly PDI revenue per flavor term.

Feeds `explorer.html`, where a reader types a flavor ("mango") and sees that
flavor's convenience-channel sales month by month, overlaid with Google Trends
search interest for the same word.

WHY A PRECOMPUTED INDEX RATHER THAN A BACKEND
---------------------------------------------
The site is static files behind nginx on Cloud Run. There is no server to run a
query against, and there could not be one without shipping PDI - which is
licensed and must not leave the warehouse. So the flavor -> monthly-revenue
mapping is reduced here, in advance, to a small JSON of aggregates. No SKU rows,
no store data, no GTINs reach the browser.

That trades away free-text search. The tool answers for a fixed vocabulary of
flavor terms rather than any string, which is also what keeps it honest: every
term in the vocabulary has a Google Trends series collected for it, so the two
lines on the chart always cover the same term. A free-text box that silently
returned "no trend data" for most inputs would be worse.

HOW A TERM'S SKU SET IS DEFINED
-------------------------------
A SKU belongs to term T if T appears as a whole word in its FLAVOR field or its
PRODUCT_DESCRIPTION. Whole-word matching matters: substring matching puts
"grape" inside "grapefruit" and silently merges two different flavors.

Sets deliberately OVERLAP - "MONSTER MANGO LOCO" is both mango and loco - so
term revenues do not sum to the category. The tool never presents them as a
decomposition.

    python data/scripts/build_flavor_explorer.py --dry-run   # cost only
    python data/scripts/build_flavor_explorer.py

Reads BigQuery via a pasted OAuth token in BQ_TOKEN. stdlib only.
"""
import argparse
import collections
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "public/data/flavor_explorer.json")
PROJECT = "msbai-capstone-energydrinks"

FIRST, LAST = "2019-01-01", "2025-12-31"

# Below this a term is noise: a handful of SKUs whose month-to-month series is
# mostly zeros cannot support a correlation, and showing one invites the reader
# to read meaning into three data points.
MIN_SKUS = 3
MIN_REVENUE = 250_000

# Words that appear in flavor text but are not flavors. Without this the
# vocabulary fills up with packaging and marketing language.
STOP = {
    "energy", "drink", "drinks", "can", "cans", "bottle", "oz", "pack", "single",
    "zero", "sugar", "free", "diet", "light", "original", "regular", "the", "and",
    "with", "new", "flavor", "flavored", "natural", "artificial", "juice", "soda",
    "carbonated", "non", "low", "calorie", "caffeine", "blend", "mix", "style",
    "edition", "limited", "ultra", "max", "extra", "plus", "no", "of", "in", "a",
}

# A term's Google Trends companions. The bare word measures the fruit; the
# qualified phrase measures drink intent. Both are collected because the gap
# between them is itself informative - see explorer.js.
def trend_terms(term):
    return [term, f"{term} energy drink"]


# --- concept flavors -------------------------------------------------------
# Flavors with cultural momentum that the convenience channel has barely
# touched. They are carried DELIBERATELY BELOW the MIN_SKUS/MIN_REVENUE gates,
# because for these the interesting number is the absence of sales next to the
# presence of search - a flavor people look up and cannot buy at a gas station.
#
# Read them with care. Zero PDI revenue means "not sold in this channel's
# sample", not "nobody wants it": most of these sell in grocery, specialty and
# DTC, none of which PDI observes. The page labels them as concepts rather than
# mixing them into the measured vocabulary.
CONCEPTS = [
    ("masala chai",     "spiced tea base; the chai latte is now mainstream in US coffee shops"),
    ("cookies and cream", "top-5 US ice-cream flavor that has never crossed into energy"),
    ("ube",             "purple yam; carried by a decade of visual social media"),
    ("horchata",        "cinnamon-rice; already a fountain staple in the Southwest"),
    ("yuzu",            "Japanese citrus; established in soda and seltzer first"),
    ("dragon fruit",    "already proven in seltzer and tea; near-absent in energy"),
    ("hibiscus",        "agua de jamaica; tart, red, and caffeine-neutral"),
    ("tamarind",        "chamoy/tajin adjacency, strong with young Latino buyers"),
    ("guava",           "top tropical in Latin American beverage, thin in US energy"),
    ("matcha latte",    "the highest-intent search of the tea family"),
    ("birthday cake",   "dessert flavor proven in protein and pre-workout"),
    ("prickly pear",    "Southwest signature; visually distinctive"),
    ("elderflower",     "European soft-drink staple; premium positioning"),
    ("black sesame",    "dessert flavor with a long runway in East Asian retail"),
]


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
    out, job, page = [], res["jobReference"]["jobId"], None
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


# The join to pdi_master_gtin is what supplies FLAVOR - pdi_daily_agg carries
# PRODUCT_DESCRIPTION but no FLAVOR column. Only the columns actually needed are
# selected: BigQuery bills by column, so naming them keeps a 420 GB table at
# roughly 86 GB scanned.
SQL = f"""
WITH s AS (
  SELECT GTIN,
         FORMAT_DATE('%Y-%m', DATE) AS m,
         SUM(TOTAL_REVENUE_AMOUNT) AS rev,
         SUM(QUANTITY)             AS units
  FROM `{PROJECT}.energy_drinks.pdi_daily_agg`
  WHERE DATE BETWEEN '{FIRST}' AND '{LAST}'
  GROUP BY GTIN, m
)
SELECT s.GTIN, s.m, s.rev, s.units,
       g.PRODUCT_DESCRIPTION AS descr, g.FLAVOR AS flavor, g.canonical_brand AS brand
FROM s
JOIN (
  SELECT GTIN, ANY_VALUE(PRODUCT_DESCRIPTION) PRODUCT_DESCRIPTION,
         ANY_VALUE(FLAVOR) FLAVOR, ANY_VALUE(BRAND) canonical_brand
  FROM `{PROJECT}.energy_drinks.pdi_master_gtin`
  GROUP BY GTIN
) g USING (GTIN)
"""


def months_between(a, b):
    y, mth = int(a[:4]), int(a[5:7])
    ey, em = int(b[:4]), int(b[5:7])
    out = []
    while (y, mth) <= (ey, em):
        out.append(f"{y:04d}-{mth:02d}")
        mth += 1
        if mth == 13:
            y, mth = y + 1, 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("BQ_TOKEN", "").strip()
    if not token:
        sys.exit("BQ_TOKEN not set. Paste a token from:\n"
                 "  gcloud auth application-default print-access-token")

    if args.dry_run:
        d = bq(SQL, token, dry=True)
        b = int(d["totalBytesProcessed"])
        print(f"{b/1e9:.1f} GB  ->  ${b/1e12*6.25:.2f}")
        return

    print("querying pdi_daily_agg ...", flush=True)
    res = bq(SQL, token)
    if not res.get("jobComplete"):
        sys.exit("query did not complete inside the timeout; rerun")
    rows = rows_of(res, token)
    print(f"  {len(rows):,} GTIN-month rows")

    months = months_between(FIRST[:7], LAST[:7])
    midx = {m: i for i, m in enumerate(months)}

    # --- vocabulary comes from FLAVOR, membership from FLAVOR + description --
    # Two different jobs, so two different sources. Taking the VOCABULARY from
    # descriptions fills it with brands and packaging: the first pass returned
    # "red", "bull", "monster", "bang" and "aluminum" as top "flavors". FLAVOR is
    # a curated field ("Mango Peach", "Blue Raspberry") and yields clean terms.
    #
    # MEMBERSHIP still reads the description too, because ~470 SKUs have no
    # FLAVOR value while their description plainly says mango. Narrow vocabulary,
    # broad matching.
    word = re.compile(r"[a-z]+")
    sku_flavor, sku_text, sku_rows = {}, {}, collections.defaultdict(list)
    brand_words = set()
    for r in rows:
        g = r["GTIN"]
        sku_rows[g].append(r)
        if g not in sku_text:
            sku_flavor[g] = {w for w in word.findall((r.get("flavor") or "").lower())
                             if len(w) > 2 and w not in STOP}
            sku_text[g] = {w for w in word.findall(
                f"{r.get('flavor') or ''} {r.get('descr') or ''}".lower())
                if len(w) > 2 and w not in STOP}
        brand_words |= set(word.findall((r.get("brand") or "").lower()))

    # A word that names a brand is not a flavor. "Monster" and "Ghost" appear in
    # flavor text often enough to outrank real fruit otherwise.
    vocab = {w for ws in sku_flavor.values() for w in ws} - brand_words

    term_skus = collections.defaultdict(set)
    for g, ws in sku_text.items():
        for w in ws & vocab:
            term_skus[w].add(g)

    terms = {}
    for term, gtins in term_skus.items():
        if len(gtins) < MIN_SKUS:
            continue
        series = [0.0] * len(months)
        brands, units = collections.Counter(), 0.0
        for g in gtins:
            for r in sku_rows[g]:
                i = midx.get(r["m"])
                if i is None:
                    continue
                series[i] += float(r["rev"] or 0)
                units += float(r["units"] or 0)
                brands[r.get("brand") or "?"] += float(r["rev"] or 0)
        total = sum(series)
        if total < MIN_REVENUE:
            continue
        terms[term] = {
            "skus": len(gtins),
            "total": round(total, 2),
            "units": round(units),
            "rev": [round(v, 2) for v in series],
            "brands": [b for b, _ in brands.most_common(6)],
            "trend_terms": trend_terms(term),
        }

    print(f"  {len(terms)} terms clear {MIN_SKUS} SKUs and ${MIN_REVENUE:,}")

    # --- concept flavors, carried below the gates on purpose ---------------
    # Phrase matching, not tokens: "cookies and cream" is three words and
    # "cookies" alone would drag in unrelated SKUs.
    full_text = {g: f"{r[0].get('flavor') or ''} {r[0].get('descr') or ''}".lower()
                 for g, r in sku_rows.items()}
    concepts = {}
    for phrase, why in CONCEPTS:
        variants = {phrase, phrase.replace(" and ", " & "), phrase.replace(" ", "")}
        gtins = {g for g, t in full_text.items() if any(v in t for v in variants)}
        series = [0.0] * len(months)
        for g in gtins:
            for r in sku_rows[g]:
                i = midx.get(r["m"])
                if i is not None:
                    series[i] += float(r["rev"] or 0)
        concepts[phrase] = {
            "skus": len(gtins),
            "total": round(sum(series), 2),
            "rev": [round(v, 2) for v in series],
            "why": why,
            "trend_terms": trend_terms(phrase),
        }
    empty = sum(1 for d in concepts.values() if d["skus"] == 0)
    print(f"  {len(concepts)} concept flavors ({empty} with no PDI presence at all)")

    # --- the category control ----------------------------------------------
    # THE most important series on the page. If total category revenue already
    # tracks generic "energy drink" search, then a flavor-level correlation may
    # be nothing but shared category seasonality showing up twice. Every
    # per-term result should be read against this one.
    cat = [0.0] * len(months)
    cat_units = 0.0
    for r in rows:
        i = midx.get(r["m"])
        if i is not None:
            cat[i] += float(r["rev"] or 0)
            cat_units += float(r["units"] or 0)
    category = {
        "skus": len(sku_rows),
        "total": round(sum(cat), 2),
        "units": round(cat_units),
        "rev": [round(v, 2) for v in cat],
        "trend_terms": ["energy drink"],
    }
    print(f"  category total ${category['total']/1e9:.2f}B across {category['skus']:,} GTINs")

    # --- brands --------------------------------------------------------------
    brand_rev = collections.defaultdict(lambda: [0.0] * len(months))
    for r in rows:
        i = midx.get(r["m"])
        if i is None:
            continue
        brand_rev[(r.get("brand") or "?").strip()][i] += float(r["rev"] or 0)
    brands = {}
    for b, series in brand_rev.items():
        total = sum(series)
        if total < 20_000_000 or b in ("?", ""):
            continue
        # Trends needs the brand name plus a qualified phrase; "Bang" and "Ghost"
        # are common words and the bare form measures something else entirely.
        brands[b] = {
            "total": round(total, 2),
            "rev": [round(v, 2) for v in series],
            "trend_terms": [b.lower(), f"{b.lower()} energy drink"],
        }
    brands = dict(sorted(brands.items(), key=lambda kv: -kv[1]["total"]))
    print(f"  {len(brands)} brands over $20M")

    payload = {
        "months": months,
        "terms": dict(sorted(terms.items(), key=lambda kv: -kv[1]["total"])),
        "concepts": concepts,
        "category": category,
        "brands": brands,
        "trends": {},          # filled by data/scripts/add_trends_to_explorer.py
        "meta": {
            "source": "PDI convenience POS, pdi_daily_agg",
            "window": f"{FIRST} to {LAST}",
            "coverage": ("Convenience channel only, and roughly 8.6% of that channel. "
                         "Not total market."),
            "overlap": ("Flavor sets overlap - a mango-pineapple SKU counts in both - "
                        "so term revenues do not sum to the category total."),
            "min_skus": MIN_SKUS, "min_revenue": MIN_REVENUE,
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, separators=(",", ":"))
    os.replace(tmp, OUT)                    # atomic: a killed run cannot truncate
    print(f"wrote {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB)")
    print("\ntop terms by revenue:")
    for t, d in list(payload["terms"].items())[:18]:
        print(f"  {t:<16}{d['skus']:>4} SKUs  ${d['total']/1e6:>8,.1f}M")


if __name__ == "__main__":
    main()
