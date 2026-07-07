#!/usr/bin/env python3
"""analyze_sentiment.py — score the scraped review/comment corpora for
sentiment, by brand and by theme (taste, sugar, energy, crash, price, ...).

Offers THREE interchangeable models (pick with --model):

  lexicon     (default, zero install) — a built-in domain-tuned lexicon with
              negation + intensifier handling. Runs anywhere, instantly.
  vader       (pip3 install vaderSentiment) — VADER, tuned for social/review
              text; the same engine build_external_datasets.py uses for Reddit.
  transformer (pip3 install transformers torch) — a pretrained neural model
              (cardiffnlp/twitter-roberta-base-sentiment-latest by default,
              --hf-model to change). Most accurate, slowest, downloads weights.

It reads every review/comment source it can find under data/ (Amazon, Walmart,
retailers, Kroger reviews; YouTube + TikTok comments; Instagram captions),
scores each row pos/neg/neu, tags it with the product themes it mentions, and
writes tidy aggregates for the dashboard / analysis:

  data/analysis/sentiment_by_brand.csv   per (source, brand): n, %pos/neg/neu, mean score
  data/analysis/sentiment_by_theme.csv   per (brand, theme): n, %pos/neg/neu, mean score
  data/analysis/sentiment_rows.csv       per-row scores (--rows to enable; can be large)

Usage (VS Code terminal on macOS):
  python3 data/scripts/analyze_sentiment.py                      # lexicon
  python3 data/scripts/analyze_sentiment.py --model vader
  python3 data/scripts/analyze_sentiment.py --model transformer  # needs GPU/patience
  python3 data/scripts/analyze_sentiment.py --sources amazon walmart --rows

Compare models by running each with --out data/analysis/<model> and diffing.
"""

import argparse
import csv
import glob
import math
import os
import re
import sys
from collections import defaultdict

# --------------------------------------------------------------------------
# Brand normalization (shared alias map)
# --------------------------------------------------------------------------

BRAND_ALIASES = {
    "celsius": "Celsius", "red bull": "Red Bull", "redbull": "Red Bull",
    "monster": "Monster", "monsterenergy": "Monster",
    "liquid i.v.": "Liquid I.V.", "liquid iv": "Liquid I.V.",
    "ghost": "Ghost", "bang": "Bang", "bang energy": "Bang",
    "alani nu": "Alani Nu", "alani": "Alani Nu", "rockstar": "Rockstar",
    "5-hour energy": "5-hour Energy", "5 hour energy": "5-hour Energy",
    "nos": "NOS", "reign": "Reign", "zoa": "Zoa", "prime": "Prime",
    "g fuel": "G Fuel", "gfuel": "G Fuel", "advocare": "AdvoCare",
    "bloom nutrition": "Bloom Nutrition", "bloom": "Bloom Nutrition",
    "c4": "C4", "guru": "GURU", "liquid death": "Liquid Death",
    "pureboost": "Pureboost", "spylt": "Spylt", "xwerks": "Xwerks",
    "zipfizz": "Zipfizz",
}
# (?<!-) / (?!-) block hyphen compounds ("prime-time", "monster-truck")
_BRAND_PATTERNS = sorted(
    ((canon, re.compile(
        r"(?<!-)\b" + re.escape(a).replace(r"\ ", r"\s*") + r"\b(?!-)", re.I))
     for a, canon in BRAND_ALIASES.items()),
    key=lambda kv: -len(kv[1].pattern))


def norm_brand(value):
    if not value:
        return None
    return BRAND_ALIASES.get(str(value).strip().lower(), str(value).strip())


def brand_from_text(text):
    for canon, pat in _BRAND_PATTERNS:
        if pat.search(text or ""):
            return canon
    return None


# --------------------------------------------------------------------------
# Themes — the product attributes consumers talk about
# --------------------------------------------------------------------------

THEMES = {
    "taste": r"\b(taste|tastes|tasty|flavou?r|delicious|yummy|gross|"
             r"disgusting|nasty|smell)\b",
    "sweetness": r"\b(sweet|too sweet|sugary|sugar|aftertaste|artificial|"
                 r"stevia|sucralose|bitter)\b",
    "energy": r"\b(energy|boost|awake|alert|kick|wired|caffeine|focus|"
              r"pre[- ]?workout|pump)\b",
    "crash": r"\b(crash(?:ed|es|ing)?|jitter(?:y|s)?|anxious|anxiety|"
             r"headaches?|heart|palpitations?|nausea|stomach)\b",
    "price": r"\b(price|pricey|expensive|cheap|value|worth|cost|deal|"
             r"overpriced|affordable)\b",
    "health": r"\b(healthy|clean|natural|vitamin|zero sugar|calorie|diet|"
              r"keto|gluten|vegan|ingredient)\b",
    "packaging": r"\b(can|bottle|packaging|leak|dented|label|pack|shipping|"
                 r"arrived)\b",
}
_THEME_PATTERNS = [(t, re.compile(p, re.I)) for t, p in THEMES.items()]


def themes_of(text):
    return [t for t, pat in _THEME_PATTERNS if pat.search(text or "")]


# --------------------------------------------------------------------------
# Source registry — where text + brand live in each CSV
# --------------------------------------------------------------------------

# (source, path-or-glob, text_column, brand_column_or_None)
SOURCES = [
    ("amazon", "data/amazon/reviews.csv", "review_text", "brand"),
    ("walmart", "data/walmart/reviews.csv", "review_text", "brand"),
    ("retailers", "data/retailers/reviews.csv", "review_text", "brand"),
    ("kroger", "data/kroger/reviews.csv", "review_text", "brand"),
    ("youtube", "data/youtube/comments.csv", "comment", None),
    ("tiktok", "data/tiktok/comments.csv", "comment", None),
    ("instagram", "data/instagram/posts.csv", "caption", "brand"),
]


# --------------------------------------------------------------------------
# Model 1 — built-in domain lexicon (zero dependencies)
# --------------------------------------------------------------------------

POS_WORDS = {
    "love", "loved", "great", "amazing", "awesome", "best", "delicious",
    "tasty", "refreshing", "perfect", "excellent", "favorite", "smooth",
    "clean", "worth", "recommend", "good", "nice", "enjoy", "enjoyed",
    "fantastic", "addicted", "obsessed", "yummy", "solid", "reliable", "fresh",
}
NEG_WORDS = {
    "hate", "hated", "gross", "disgusting", "nasty", "terrible", "awful",
    "worst", "bad", "bland", "watery", "expensive", "overpriced", "crash",
    "jittery", "headache", "nausea", "sick", "disappointed", "disappointing",
    "waste", "avoid", "stale", "leaked", "dented", "artificial", "bitter",
    "meh", "ripoff", "return", "refund",
}
NEGATORS = {"not", "no", "never", "n't", "without", "hardly", "barely"}
INTENSIFIERS = {"very", "really", "so", "super", "extremely", "absolutely",
                "incredibly", "too"}
_WORD_RE = re.compile(r"[a-z']+")


def lexicon_score(text):
    """Return a compound score in [-1, 1] with negation + intensifier logic."""
    words = _WORD_RE.findall((text or "").lower())
    if not words:
        return 0.0
    total = 0.0
    for i, w in enumerate(words):
        val = 1.0 if w in POS_WORDS else -1.0 if w in NEG_WORDS else 0.0
        if val == 0.0:
            continue
        window = words[max(0, i - 3):i]
        if any(n in window for n in NEGATORS):
            val = -val * 0.8
        if any(n in window for n in INTENSIFIERS):
            val *= 1.5
        total += val
    # squash to [-1, 1]
    return max(-1.0, min(1.0, total / math.sqrt(len(words) + 1)))


# --------------------------------------------------------------------------
# Model wiring
# --------------------------------------------------------------------------

def make_scorer(model, hf_model):
    """Return a function text -> compound score in [-1, 1]."""
    if model == "lexicon":
        return lexicon_score, "lexicon"
    if model == "vader":
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        except ImportError:
            sys.exit("--model vader needs: pip3 install vaderSentiment")
        sia = SentimentIntensityAnalyzer()
        return (lambda t: sia.polarity_scores(t or "")["compound"]), "vader"
    if model == "transformer":
        try:
            from transformers import pipeline
        except ImportError:
            sys.exit("--model transformer needs: pip3 install transformers torch")
        clf = pipeline("sentiment-analysis", model=hf_model, truncation=True)

        def score(t):
            if not (t or "").strip():
                return 0.0
            r = clf(t[:512])[0]
            label = r["label"].lower()
            s = r["score"]
            if "neg" in label or label in ("label_0", "1 star", "2 stars"):
                return -s
            if "neu" in label or label == "label_1":
                return 0.0
            return s
        return score, hf_model
    raise ValueError(model)


def label_of(compound):
    return "pos" if compound >= 0.05 else "neg" if compound <= -0.05 else "neu"


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------

class Agg(object):
    __slots__ = ("n", "pos", "neg", "neu", "total")

    def __init__(self):
        self.n = self.pos = self.neg = self.neu = 0
        self.total = 0.0

    def add(self, compound):
        self.n += 1
        self.total += compound
        lab = label_of(compound)
        setattr(self, lab, getattr(self, lab) + 1)

    def row(self):
        n = self.n or 1
        return {
            "n": self.n,
            "pct_pos": round(100.0 * self.pos / n, 1),
            "pct_neg": round(100.0 * self.neg / n, 1),
            "pct_neu": round(100.0 * self.neu / n, 1),
            "mean_score": round(self.total / n, 4),
        }


def iter_texts(sources, repo="."):
    for src, pathspec, text_col, brand_col in sources:
        for path in sorted(glob.glob(os.path.join(repo, pathspec))):
            if not os.path.exists(path):
                continue
            with open(path, newline="", encoding="utf-8", errors="replace") as f:
                for r in csv.DictReader(f):
                    text = (r.get(text_col) or "").strip()
                    if not text:
                        continue
                    brand = norm_brand(r.get(brand_col)) if brand_col else None
                    if not brand:
                        brand = brand_from_text(text)
                    yield src, brand or "Unknown", text


def write_csv(path, columns, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("  wrote %s (%d rows)" % (path, len(rows)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", choices=["lexicon", "vader", "transformer"],
                    default="lexicon")
    ap.add_argument("--hf-model",
                    default="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    help="transformer backend: HuggingFace model id")
    ap.add_argument("--sources", nargs="+",
                    choices=[s[0] for s in SOURCES],
                    help="limit to these sources (default: all found)")
    ap.add_argument("--rows", action="store_true",
                    help="also write per-row scores (data/analysis/sentiment_rows.csv)")
    ap.add_argument("--limit", type=int, default=0,
                    help="max rows per source (0 = all); handy for a quick pass")
    ap.add_argument("--out", default="data/analysis")
    args = ap.parse_args()

    sources = [s for s in SOURCES
               if not args.sources or s[0] in args.sources]
    score, model_name = make_scorer(args.model, args.hf_model)
    print("Model: %s" % model_name)

    by_brand = defaultdict(Agg)      # (source, brand) -> Agg
    by_theme = defaultdict(Agg)      # (brand, theme) -> Agg
    row_out = []
    counts = defaultdict(int)
    n = 0
    for src, brand, text in iter_texts(sources):
        if args.limit and counts[src] >= args.limit:
            continue
        counts[src] += 1
        compound = score(text)
        by_brand[(src, brand)].add(compound)
        tags = themes_of(text)
        for t in tags:
            by_theme[(brand, t)].add(compound)
        if args.rows:
            row_out.append({
                "source": src, "brand": brand, "label": label_of(compound),
                "score": round(compound, 4), "themes": ";".join(tags),
                "text": text[:300]})
        n += 1
        if n % 20000 == 0:
            print("  scored %d..." % n)
    print("Scored %d texts across %d sources." % (n, len(counts)))

    brand_rows = []
    for (src, brand), agg in sorted(by_brand.items(),
                                    key=lambda kv: (kv[0][0], -kv[1].n)):
        d = {"source": src, "brand": brand, "model": model_name}
        d.update(agg.row())
        brand_rows.append(d)
    write_csv(os.path.join(args.out, "sentiment_by_brand.csv"),
              ["source", "brand", "model", "n", "pct_pos", "pct_neg",
               "pct_neu", "mean_score"], brand_rows)

    theme_rows = []
    for (brand, theme), agg in sorted(by_theme.items(),
                                      key=lambda kv: (kv[0][0], -kv[1].n)):
        d = {"brand": brand, "theme": theme, "model": model_name}
        d.update(agg.row())
        theme_rows.append(d)
    write_csv(os.path.join(args.out, "sentiment_by_theme.csv"),
              ["brand", "theme", "model", "n", "pct_pos", "pct_neg",
               "pct_neu", "mean_score"], theme_rows)

    if args.rows:
        write_csv(os.path.join(args.out, "sentiment_rows.csv"),
                  ["source", "brand", "label", "score", "themes", "text"],
                  row_out)
    print("Done. Compare models by rerunning with --model vader / transformer "
          "and --out data/analysis/<model>.")


if __name__ == "__main__":
    main()
