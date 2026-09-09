#!/usr/bin/env python3
"""Build an EXOGENOUS flavor-attention series from YouTube video metadata.

Writes data/bq/derived/flavor_social.csv  (family x month, committed).

WHY THIS SOURCE, AFTER FOUR OTHERS FAILED
-----------------------------------------
The flavor model in flavor_forecast.py uses only features derived from the PDI
panel itself. The obvious way to beat a persistence baseline is to add a signal
from a DIFFERENT data-generating process. Four candidates were checked first and
none survives contact with its own dates:

  Google Trends   the intended source. `data/trends/` holds no CSVs and the
                  `trends` block in flavor_explorer.json is empty. The container
                  cannot fetch it either: trends.google.com returns 403 to the
                  CONNECT (api.github.com returns 200 from the same shell), so
                  this is an egress policy, not an outage. Refreshed monthly by
                  .github/workflows/trends.yml instead.
  GNPD claims     keyed by CLAIM ("Sugar Free", "Functional - Brain"), which has
                  no flavor dimension at all, and carries two aggregated windows
                  rather than a monthly series. It cannot join to family x month.
  YouTube COMMENTS  every comment before 2025-06 is stamped `<year>-05`: the
                  scraper resolved YouTube's relative "N years ago" into an
                  absolute date against a ~May scrape. 18 distinct months over
                  18 years. Genuine month resolution only from 2025-06.
  Amazon reviews / Instagram posts   122 and 20 rows respectively inside the
                  2019-2025 window, median 1-2 rows a month. Too thin to form a
                  share across 12 families.

Video UPLOAD dates survive the same test: 84 of 84 months covered, 2,496 videos
in window, 31 distinct days-of-month (so not synthesised), median 26 a month.
That is a real monthly series measuring what creators PUBLISHED about, and it is
independent of retail scans.

WHAT IS COUNTED, AND THE TWO BIASES THAT SHAPE IT
-------------------------------------------------
Document frequency: a video counts ONCE for a family if the family matches
anywhere in title + tags + description. Not term frequency - `transcript` is
empty on every row, and a repeated word in a long description would otherwise
let one video outvote ten.

  Selection.  The corpus is a stratified sample over 96 fixed search queries
  ("energy drink review", "G Fuel review"), which are category- and
  brand-oriented, never flavor-oriented. Flavor mentions are therefore
  INCIDENTAL, which is what makes this usable as an attention proxy - the
  corpus was not selected on the thing being measured. But it is attention
  *within those queries*, not all of YouTube.

  Corpus size.  Videos per month range 8-80. So every feature is a SHARE of
  that month's flavor mention-events, never a count, which cancels corpus size
  exactly the way the sales target cancels PDI's store ramp.

THE PROSE REGEXES ARE NOT THE CANONICAL ONES, DELIBERATELY
----------------------------------------------------------
classify_target_consumers.FLAVOR_FAMILIES is written for short product
descriptions and is unsafe on free text: "Original" matches any prose use of
"original"/"classic"/"regular"; "Punch & mixed fruit" matches bare
"fruit"/"blast"/"blend"/"melon"; and "Novelty & branded" is not a text pattern
at all - it is defined as "the FLAVOR field was populated but matched nothing",
which cannot be evaluated against a video title. Several canonical patterns also
lack word boundaries, harmless in "RED BULL WATERMELON 12 OZ" and not in prose
("lime" inside "sublime").

So this file carries its own word-boundary-safe subset and EXCLUDES the three
families it cannot measure honestly rather than emitting a noisy column for
them. Excluded families simply get no social feature; the model falls back to
the panel-only features for those rows.

    python data/scripts/build_social_features.py
    python data/scripts/build_social_features.py --report

stdlib only.
"""
import argparse
import collections
import csv
import os
import re
import sys

csv.field_size_limit(10 ** 9)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIDEOS = os.path.join(ROOT, "data/youtube/videos.csv")
OUT = os.path.join(ROOT, "data/bq/derived/flavor_social.csv")

FIRST, LAST = "2019-01", "2025-12"

# Word-boundary-safe, prose-appropriate. Names match FLAVOR_FAMILIES exactly so
# a family means the same thing on the attention side and the sales side.
PROSE_FAMILIES = [
    ("Watermelon",          r"\bwatermelons?\b"),
    ("Coffee & cream",      r"\bcoffee\b|\bespressos?\b|\blattes?\b|\bmochas?\b|\bvanilla\b|\bcaramel\b"),
    ("Sour & candy",        r"\bsour\b|\bcandy\b|\bgumm(y|ies)\b|\bbubble ?gum\b|\brainbow\b|\bbirthday cake\b"),
    ("Cola & soda",         r"\bcolas?\b|\broot ?beer\b|\bcream ?soda\b|\bginger\b"),
    ("Berry",               r"\bberr(y|ies)\b|\braspberr\w*|\bblueberr\w*|\bstrawberr\w*|\bacai\b|\bcranberr\w*|\bcherr(y|ies)\b"),
    ("Tropical",            r"\btropical\b|\bmangos?\b|\bpineapples?\b|\bpassion ?fruit\b|\bguava\b|\bpapayas?\b|\bdragon ?fruit\b|\bkiwis?\b|\bbananas?\b|\bcoconuts?\b"),
    ("Citrus",              r"\bcitrus\b|\boranges?\b|\blemons?\b|\blimes?\b|\bgrapefruits?\b|\btangerines?\b|\byuzu\b"),
    ("Grape",               r"\bgrapes?\b"),
    ("Apple & pear",        r"\bapples?\b|\bpears?\b"),
    ("Peach & stone fruit", r"\bpeach(es)?\b|\bapricots?\b|\bnectarines?\b|\bplums?\b"),
    ("Tea & botanical",     r"\bteas?\b|\byerba\b|\bmate\b|\bmint\b|\bmatcha\b|\bhibiscus\b|\bginseng\b"),
    ("Punch & mixed fruit", r"\bfruit punch\b|\bpunch\b"),
]
# Measured by the sales panel but NOT by this file. See the docstring.
UNMEASURABLE = ["Original", "Novelty & branded", "Melon & other"]

RX = [(name, re.compile(pat, re.I)) for name, pat in PROSE_FAMILIES]

# The corpus's 96 search queries include ADJACENT BEVERAGE CATEGORIES, and they
# poison the flavor counts in a specific, checkable way: a "yerba mate review"
# video mentions tea and mate, a "kombucha review" mentions ginger, a "protein
# drink review" mentions vanilla, and every "drink alternatives to coffee" video
# mentions coffee. Counting those as ENERGY-DRINK flavor attention is what put
# Tea & botanical at 16.7% of attention against 0.6% of sales, and Coffee &
# cream at 16.1% against 1.2%.
#
# --strict drops queries that explicitly name a non-energy-drink category.
# Ambiguous ones ("functional beverage review", "best drinks for hiking") are
# KEPT: the rule is "names another category", not "might not be an energy
# drink", so the filter stays a stated rule rather than a taste judgement.
# "green tea energy drink" and "matcha energy drink" are kept - those are
# energy drinks.
OFF_CATEGORY = re.compile(
    r"kombucha|sparkling water|yerba mate|protein drink|olipop|poppi|"
    r"prebiotic soda|functional soda|healthy soda|electrolyte|hydration|"
    r"adaptogen|alternatives? to coffee|coffee alternative", re.I)


def months_between(a, b):
    y, mo = int(a[:4]), int(a[5:7])
    ey, em = int(b[:4]), int(b[5:7])
    out = []
    while (y, mo) <= (ey, em):
        out.append(f"{y:04d}-{mo:02d}")
        mo += 1
        if mo == 13:
            mo, y = 1, y + 1
    return out


def scan(strict=False):
    """videos-per-month and family document-frequency-per-month."""
    vids = collections.Counter()
    hits = collections.defaultdict(collections.Counter)
    dropped = 0
    if not os.path.exists(VIDEOS):
        sys.exit(f"missing {VIDEOS}")
    with open(VIDEOS, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            m = (row.get("upload_date") or "")[:7]
            if len(m) != 7 or not (FIRST <= m <= LAST):
                continue
            if strict and OFF_CATEGORY.search(row.get("search_query") or ""):
                dropped += 1
                continue
            text = " ".join((row.get(c) or "") for c in ("title", "tags", "description"))
            if not text.strip():
                continue
            vids[m] += 1
            for fam, rx in RX:
                if rx.search(text):
                    hits[m][fam] += 1
    if strict:
        print(f"--strict dropped {dropped} off-category videos")
    return vids, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="print density diagnostics")
    ap.add_argument("--strict", action="store_true",
                    help="drop videos whose search query names a non-energy-drink category")
    args = ap.parse_args()

    vids, hits = scan(strict=args.strict)
    months = months_between(FIRST, LAST)
    fams = [f for f, _ in PROSE_FAMILIES]

    # Trailing 12-month document frequency. Raw monthly counts are far too thin
    # to share out - Grape is zero in 46 of 84 months - so the unit of
    # observation is a rolling year, which is also the horizon the model cares
    # about. Months before the first full window emit blank, not zero: a zero
    # would assert "no attention" where the truth is "not yet measurable".
    rows = []
    for i, m in enumerate(months):
        win = months[max(0, i - 11):i + 1]
        if len(win) < 12:
            continue
        counts = {f: sum(hits[w][f] for w in win) for f in fams}
        total = sum(counts.values())
        nvid = sum(vids[w] for w in win)
        for f in fams:
            rows.append({
                "family": f,
                "month": m,
                "mentions_12m": counts[f],
                "videos_12m": nvid,
                "soc_share": round(counts[f] / total, 6) if total else "",
            })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["family", "month", "mentions_12m",
                                           "videos_12m", "soc_share"])
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT}  ({len(rows)} rows, {len(set(r['month'] for r in rows))} months, "
          f"{len(fams)} families)")
    print(f"families with no social feature: {', '.join(UNMEASURABLE)}")

    if args.report:
        print(f"\n{'family':22}{'hits':>7}{'zero-mo':>9}{'mean/mo':>9}")
        for f in fams:
            tot = sum(hits[m][f] for m in months)
            zero = sum(1 for m in months if hits[m][f] == 0)
            print(f"{f:22}{tot:7}{zero:9}{tot/len(months):9.2f}")
        print(f"\nvideos in window: {sum(vids.values())}, "
              f"mention-events: {sum(sum(hits[m].values()) for m in months)}")


if __name__ == "__main__":
    main()
