#!/usr/bin/env python3
"""Flavor + brand mentions from the YouTube corpus. Workstream 3, without Reddit.

    python capstone/collectors/analyze_youtube.py

Writes data/youtube/flavor_pulse_yt_<date>.csv, brand_pulse_yt_<date>.csv and
meta_yt_<date>.csv — the SAME SCHEMA the Reddit collector emits, so the two
sources drop into one table if and when Reddit access is granted.

WHY THIS IS THE PRIMARY TEXT SOURCE, NOT THE FALLBACK
-----------------------------------------------------
Reddit refused API access to a newly registered app (see
capstone/REDDIT_API_TERMS.md for the diagnosis), and a research-access request
is under human review with no guaranteed outcome or date. A thesis cannot wait
on that, and it should not have to: the YouTube corpus is the larger and
deeper source anyway.

  YouTube  125,054 comments · 3,214 videos · 96 search queries · 2007-2026
  Reddit    the existing snapshot is 1,000 posts + 1,000 comments over 19 days,
            brand-level only. A granted-access deep pull would add breadth but
            not a longer window than this.

So Reddit is the robustness check and YouTube is the study. Stating it that way
round is also more honest than presenting whichever source happened to work.

WHAT THE CORPUS IS AND IS NOT
-----------------------------
It is review and taste-test discussion: 96 queries covering brand reviews
("Prime energy review", "NOS energy review"), category questions ("energy
drinks without crash"), and occasion framing ("energy drinks for truck
drivers", "energy drinks hiking"). Video uploads run 2007-2026 with the mass
after 2019.

It is NOT a population sample. People who comment on energy-drink review
videos are enthusiasts, skew young and male, and are self-selected for having
an opinion. Mention share measures ATTENTION among that group, not preference
in the market. That is precisely why it is read against PDI units rather than
instead of them - where the two disagree is the interesting part, and neither
alone is the answer.
"""
import argparse
import csv
import datetime as dt
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flavor_mentions import analyse  # noqa: E402

CORPUS = os.path.join(ROOT, "data/youtube/comments.csv")
VIDEOS = os.path.join(ROOT, "data/youtube/videos.csv")
OUT_DIR = os.path.join(ROOT, "data/youtube")


def corpus_meta():
    """Describe the corpus so the output can state its own provenance."""
    if not os.path.exists(VIDEOS):
        return {}
    csv.field_size_limit(10 ** 7)
    rows = list(csv.DictReader(open(VIDEOS, encoding="utf-8", errors="replace")))
    years = sorted({(r.get("upload_date") or "")[:4] for r in rows} - {""})
    return {"videos": len(rows),
            "search_queries": len({r.get("search_query", "") for r in rows}),
            "upload_years": f"{years[0]}-{years[-1]}" if years else ""}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, help="stop after N comments (for a quick look)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(CORPUS):
        sys.exit(f"missing {CORPUS}")
    csv.field_size_limit(10 ** 7)
    with open(CORPUS, encoding="utf-8", errors="replace") as fh:
        res = analyse(csv.DictReader(fh), limit=a.limit)

    stamp = dt.date.today().isoformat()
    cm = corpus_meta()

    for name, key in (("flavor", "flavors"), ("brand", "brands")):
        path = os.path.join(OUT_DIR, f"{name}_pulse_yt_{stamp}.csv")
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[key][0].keys()))
            w.writeheader()
            w.writerows(res[key])
        print(f"  wrote {os.path.relpath(path, ROOT)}  ({len(res[key])} rows)")

    meta = os.path.join(OUT_DIR, f"meta_yt_{stamp}.csv")
    with open(meta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "value"])
        for k, v in [
            ("source", "YouTube Data API v3 corpus (data/youtube/comments.csv)"),
            ("comments_scanned", res["rows_seen"]),
            ("comments_matched", res["rows_matched"]),
            ("match_rate_pct", res["match_rate_pct"]),
            ("noise_stripped", res["noise_stripped"]),
            ("sentiment_engine", res["engine"]),
            ("videos", cm.get("videos", "")),
            ("search_queries", cm.get("search_queries", "")),
            ("upload_years", cm.get("upload_years", "")),
            ("schema", "matches the Reddit collector's output, so sources combine"),
            ("privacy", "aggregates only; no usernames, ids or raw text stored"),
            ("sampling", "review/taste-test discussion, self-selected and "
                         "enthusiast-skewed; measures attention, not market "
                         "preference. Read against PDI units, never instead of."),
            ("generated_at", dt.datetime.utcnow().isoformat() + "Z"),
        ]:
            w.writerow([k, v])
    print(f"  wrote {os.path.relpath(meta, ROOT)}")

    if not a.quiet:
        print(f"\n  {res['rows_seen']:,} comments · {res['rows_matched']:,} matched "
              f"({res['match_rate_pct']}%) · {cm.get('videos', '?')} videos, "
              f"{cm.get('search_queries', '?')} queries, {cm.get('upload_years', '?')}\n")
        print(f"  {'FLAVOR':<16}{'mentions':>9}{'share%':>8}{'fav%':>7}{'net':>7}")
        for r in res["flavors"][:12]:
            print(f"  {r['name']:<16}{r['mentions']:>9,}{r['mention_share_pct']:>8}"
                  f"{r['fav_share_pct']:>7}{r['net_sentiment']:>7}")


if __name__ == "__main__":
    main()
