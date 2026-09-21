#!/usr/bin/env python3
"""Draw a random sample of matched texts for hand-labelling. Workstream 3, item 4.

    python capstone/collectors/make_label_sample.py --source data/youtube/comments.csv -n 200

Writes capstone/validation/label_sample_<date>.csv with the match the extractor
made and BLANK columns for Cai to fill in. Filling them in yields precision per
flavor and for sentiment.

WHY THIS IS NOT OPTIONAL HERE
-----------------------------
Spot-checking the extractor against the YouTube corpus found "Coffee" as the
top flavor at 23% mention share, and all twelve hand-read hits were people
discussing coffee as a COMPETING DRINK, not a coffee-flavored product. Context
gating cut that 1,361 -> 176 and the survivors are mostly real, but "mostly" is
not a number. This sampler is how it becomes one.

The sample is RANDOM OVER MATCHES, not over the corpus: measuring precision
means asking "of the things it flagged, how many were right", so the frame is
the matches. Recall would need a different sample drawn over all text, and is
a separate exercise - noted because the two get conflated constantly.

Deterministic: same seed, same sample, so a second labeller can be given the
identical rows.
"""
import argparse
import csv
import datetime as dt
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flavor_mentions import extract  # noqa: E402

OUT_DIR = os.path.join(ROOT, "capstone/validation")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default="data/youtube/comments.csv")
    ap.add_argument("--text-key", default="comment")
    ap.add_argument("-n", type=int, default=200)
    ap.add_argument("--scan", type=int, default=60000, help="rows to scan for matches")
    ap.add_argument("--seed", type=int, default=20260921)
    a = ap.parse_args()

    csv.field_size_limit(10 ** 7)
    path = os.path.join(ROOT, a.source)
    matches = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            if i >= a.scan:
                break
            text = (row.get(a.text_key) or "").strip()
            if not text:
                continue
            flavors, brands, _ = extract(text)
            if flavors:
                matches.append((text, sorted(flavors), sorted(brands)))

    if not matches:
        sys.exit("no matches found — check --source and --text-key")
    random.seed(a.seed)
    sample = random.sample(matches, min(a.n, len(matches)))

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"label_sample_{dt.date.today().isoformat()}.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "text", "predicted_flavors", "predicted_brands",
                    "flavor_correct__y_n", "true_flavors__if_no",
                    "sentiment_true__pos_neu_neg", "notes"])
        for i, (text, fl, br) in enumerate(sample, 1):
            # Text is truncated for readability in a spreadsheet; the labeller
            # is judging whether the flagged flavor is genuinely being
            # described, which one clause either side is enough to decide.
            w.writerow([i, text.replace("\n", " ")[:300], "|".join(fl),
                        "|".join(br), "", "", "", ""])

    print(f"wrote {os.path.relpath(out, ROOT)}")
    print(f"  {len(matches):,} matches found in {a.scan:,} rows scanned")
    print(f"  {len(sample)} sampled with seed {a.seed}")
    print("\nFill in flavor_correct__y_n and sentiment_true__pos_neu_neg, then:")
    print("  precision = (# y) / (# labelled)")
    print("  per-flavor precision from predicted_flavors on the y rows")


if __name__ == "__main__":
    main()
