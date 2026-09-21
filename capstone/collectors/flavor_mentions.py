#!/usr/bin/env python3
"""Flavor + brand mention extraction from free text. Workstream 3, item 3.

Shared by every text source, so Reddit and YouTube are scored by identical
rules and their numbers can sit in the same table. Importable as a module;
runnable directly to see what it does to real text:

    python capstone/collectors/flavor_mentions.py --demo data/youtube/comments.csv --limit 40000

THE ALIAS PROBLEM, WHICH IS MOST OF THE WORK
--------------------------------------------
People do not write "Blue Raspberry". They write blue razz, blu razz, bluerazz,
"the blue one". A matcher built on the canonical FLAVOR strings alone finds a
fraction of real mentions and finds it unevenly - flavors with short informal
names lose hardest, which biases the very ranking this feeds. So the alias table
below is the deliverable, and it is deliberately explicit rather than fuzzy:
every alias is written down and auditable, because a committee can ask why a
comment counted and the answer has to be a rule, not an edit distance.

WHAT IS DELIBERATELY NOT DONE
-----------------------------
No stemming, no fuzzy/Levenshtein matching, no embedding similarity. Each would
raise recall and destroy the audit trail - "why did this count" stops having an
answer a human can check. Precision is validated by hand-labelling instead
(Workstream 3 item 4).

NEGATION AND CONTEXT ARE NOT HANDLED HERE. "not a fan of mango" counts as a
mango mention. Mention share measures ATTENTION, not approval; sentiment is
scored separately and the two are reported separately. Conflating them is how a
hated flavor becomes a recommendation.

PRIVACY
-------
Usernames never enter the output and raw comment text is never written to disk
by this module. Callers get counts and per-mention sentiment, keyed by flavor.
"""
import argparse
import collections
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "data/scripts"))
from classify_target_consumers import flavor_family  # noqa: E402

# --- flavor aliases ---------------------------------------------------------
# canonical flavor -> spellings seen in the wild. Lowercase; matched as whole
# words (see WORD below), so "grape" does not fire inside "grapefruit".
#
# Sources for these: the FLAVOR strings in the PDI SKU list, plus the informal
# forms that actually appear in the YouTube corpus. Add to this table rather
# than loosening the matcher.
FLAVOR_ALIASES = {
    "Blue Raspberry": ["blue raspberry", "blue razz", "blu razz", "bluerazz",
                       "blue rasp", "blueraspberry"],
    "Watermelon":     ["watermelon", "water melon", "wtrmln"],
    "Mango":          ["mango", "mangos", "mangoes"],
    "Strawberry":     ["strawberry", "strawberries", "strawb"],
    "Cherry":         ["cherry", "cherries", "black cherry"],
    "Peach":          ["peach", "peaches"],
    "Grape":          ["grape", "grapes"],
    "Orange":         ["orange", "oranges"],
    "Lemon Lime":     ["lemon lime", "lemon-lime", "lemonlime", "lime"],
    "Pineapple":      ["pineapple", "pineapples"],
    "Tropical":       ["tropical", "tropic"],
    "Fruit Punch":    ["fruit punch", "fruitpunch", "punch"],
    "Cotton Candy":   ["cotton candy", "cottoncandy"],
    "Sour":           ["sour", "sour candy", "sour gummy"],
    "Vanilla":        ["vanilla", "vanila"],
    "Coffee":         ["coffee", "latte", "mocha", "espresso"],
    "Cola":           ["cola", "coke flavor", "root beer"],
    "Green Apple":    ["green apple", "greenapple", "sour apple"],
    "Pina Colada":    ["pina colada", "piña colada", "pinacolada"],
    "Dragon Fruit":   ["dragon fruit", "dragonfruit", "pitaya"],
    "Kiwi":           ["kiwi", "kiwis"],
    "Guava":          ["guava"],
    "Passionfruit":   ["passionfruit", "passion fruit"],
    "Coconut":        ["coconut"],
    "Mint":           ["mint", "menthol", "spearmint"],
    "Original":       ["original", "og flavor", "classic flavor", "the original"],
    "Zero Sugar":     ["zero sugar", "sugar free", "sugarfree", "zero ultra"],
}

# --- brand aliases ----------------------------------------------------------
# Mirrors the canonical set in data/scrapers/common.py. Kept here so the text
# pipeline has one table rather than importing a scraper.
BRAND_ALIASES = {
    "Red Bull":  ["red bull", "redbull", "rb"],
    "Monster":   ["monster", "monster energy"],
    "Celsius":   ["celsius"],
    "Alani Nu":  ["alani nu", "alani", "alaninu"],
    "C4":        ["c4", "c4 energy"],
    "Ghost":     ["ghost", "ghost energy"],
    "Rockstar":  ["rockstar", "rock star"],
    "NOS":       ["nos"],
    "Reign":     ["reign"],
    "Bang":      ["bang", "bang energy"],
    "Prime":     ["prime", "prime energy"],
    "Gfuel":     ["gfuel", "g fuel", "g-fuel"],
    "Bucked Up": ["bucked up", "buckedup"],
}

# TERMS THAT LOOK LIKE A HIT AND ARE NOT. Each of these was found firing in the
# YouTube corpus. Without them the counts are wrong in a direction that is easy
# to miss, because the false hits concentrate on a handful of flavors.
#
#   "monster" -> the film/creature sense, and Eminem's "The Monster"
#   "bang"    -> the noise, "bang for your buck", "bang on"
#   "prime"   -> Amazon Prime, "prime time", "in his prime"
#   "nos"     -> nitrous oxide, "nos" in racing talk
#   "rb"      -> RB Leipzig, running back
NOISE = re.compile(
    r"\b(the monster|monster movie|monsters? inc|loch ness|"
    r"bang for your buck|bang on|big bang|bangs?\b(?! energy)|"
    r"amazon prime|prime time|prime video|in his prime|in her prime|prime rib|"
    r"nitrous|nos bottle|"
    r"rb leipzig|running back)\b", re.I)


# TERMS THAT ARE ALSO STANDALONE BEVERAGES OR FOODS.
#
# Found by spot-checking the matcher against the YouTube corpus: "Coffee" came
# back as the #1 flavor at 23% mention share, and hand-reading the first twelve
# hits showed ALL twelve were people discussing coffee as a competing drink
# ("I only have 1 cup of coffee in the morning", "I don't drink coffee or
# soda"). Not one was a coffee-FLAVORED energy drink.
#
# These terms only count when the comment also supplies product context: a
# brand name, or a word that marks the term as describing a flavor. The gate is
# a written rule rather than a threshold, so any single match can be explained.
#
# Terms like "watermelon" or "blue razz" do not need the gate - nobody discusses
# drinking a watermelon as an alternative to an energy drink.
AMBIGUOUS = {"Coffee", "Cola", "Original", "Mint", "Zero Sugar", "Sour",
             "Orange", "Grape", "Cherry", "Lemon Lime"}

# The marker must sit NEAR the term, not merely somewhere in the same comment.
#
# Co-presence was tried first and was not enough: it left "I can only drink
# decaf coffee" counting as a coffee flavor, because a bare `cans?` pattern
# matches the modal verb "can", and "drink a" matched any mention of drinking.
# Both are now gone. What remains only describes a product's taste.
FLAVOR_MARKER = re.compile(
    r"\b(flavou?rs?|flavou?red|tastes?|tasted|tasting|"
    r"(?:a|the|\d+\s*oz)\s+cans?\b|cans? of|"
    r"version|edition|variant)\b", re.I)

# How far a marker or brand may sit from an ambiguous term and still license it.
# 60 characters is about one clause either side - "the coffee flavor one" and
# "Monster's coffee line" pass; a comment that mentions Red Bull in sentence one
# and drinking coffee in sentence four does not.
CONTEXT_WINDOW = 60


def _licensed(clean, match, brands_spans):
    """Is this ambiguous match close enough to a marker or a brand?"""
    lo = max(0, match.start() - CONTEXT_WINDOW)
    hi = min(len(clean), match.end() + CONTEXT_WINDOW)
    if FLAVOR_MARKER.search(clean, lo, hi):
        return True
    return any(bs < hi and be > lo for bs, be in brands_spans)


def _pattern(aliases):
    """Whole-word alternation, longest-first so 'blue razz' wins over 'razz'."""
    parts = sorted((re.escape(a) for a in aliases), key=len, reverse=True)
    return re.compile(r"(?<![a-z0-9])(" + "|".join(parts) + r")(?![a-z0-9])", re.I)


FLAVOR_RX = {k: _pattern(v) for k, v in FLAVOR_ALIASES.items()}
BRAND_RX = {k: _pattern(v) for k, v in BRAND_ALIASES.items()}


def extract(text):
    """-> (flavors, brands, noise_stripped). Sets, not counts: one comment
    saying "mango mango mango" is one person's opinion, not three."""
    if not text:
        return set(), set(), False
    clean, n = NOISE.subn(" ", text)
    brands, spans = set(), []
    for b, rx in BRAND_RX.items():
        m = rx.search(clean)
        if m:
            brands.add(b)
            spans.extend((x.start(), x.end()) for x in rx.finditer(clean))
    flavors = set()
    for f, rx in FLAVOR_RX.items():
        m = rx.search(clean)
        if not m:
            continue
        # Unambiguous flavors count on sight. Ambiguous ones - terms that are
        # also drinks or foods in their own right - need a marker or a brand
        # within CONTEXT_WINDOW characters.
        if f in AMBIGUOUS and not any(
                _licensed(clean, x, spans) for x in rx.finditer(clean)):
            continue
        flavors.add(f)
    return flavors, brands, bool(n)


def to_family(flavor):
    """Roll a matched flavor up to the pre-registered family, using the same
    function the PDI side uses - so Reddit mention share and PDI unit share are
    binned identically and can be compared at all."""
    return flavor_family({"FLAVOR": flavor})


# --- sentiment --------------------------------------------------------------
# VADER when available, else the lexicon fallback the dashboard aggregator
# already uses, so the two agree. Tuned for social text: it handles negation,
# intensifiers and emoji, which a bag-of-words lexicon does not.
def sentiment_fn():
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        an = SentimentIntensityAnalyzer()
        return lambda t: an.polarity_scores(t)["compound"], "vader"
    except ImportError:
        pos = set("love great best amazing awesome delicious perfect fire "
                  "favorite good bomb goated banger solid refreshing".split())
        neg = set("hate worst awful gross disgusting nasty terrible bad "
                  "trash mid bland chemical syrupy overrated".split())

        def score(t):
            w = re.findall(r"[a-z']+", (t or "").lower())
            p = sum(x in pos for x in w)
            n = sum(x in neg for x in w)
            return 0.0 if p + n == 0 else (p - n) / (p + n)
        return score, "lexicon-fallback (pip install vaderSentiment for VADER)"


# "favorite" mentions - the brief asks for this separately from plain mentions,
# and it is a much stronger signal: someone naming a favourite is stating a
# preference, not just using a word.
FAVORITE = re.compile(
    r"\b(favou?rite|best (?:flavou?r|one|ever)|go[- ]?to|"
    r"i love|my favou?rite|top tier|s[- ]?tier|goated)\b", re.I)


def analyse(rows, text_key="comment", date_key=None, limit=None):
    """Score an iterable of dict rows. Returns aggregates only - never text.

    rows: any iterable of dicts with a text field. Works for Reddit comments,
    Reddit post titles+selftext, and the YouTube corpus alike.
    """
    score, engine = sentiment_fn()
    fl = collections.defaultdict(lambda: {"mentions": 0, "fav": 0, "pos": 0,
                                          "neg": 0, "neu": 0, "sent_sum": 0.0})
    br = collections.defaultdict(lambda: {"mentions": 0, "fav": 0, "pos": 0,
                                          "neg": 0, "neu": 0, "sent_sum": 0.0})
    seen = matched = noise_hits = 0

    for row in rows:
        if limit and seen >= limit:
            break
        seen += 1
        text = row.get(text_key) or ""
        flavors, brands, had_noise = extract(text)
        noise_hits += had_noise
        if not flavors and not brands:
            continue
        matched += 1
        s = score(text)
        fav = bool(FAVORITE.search(text))
        bucket = "pos" if s > 0.05 else "neg" if s < -0.05 else "neu"
        for target, keys in ((fl, flavors), (br, brands)):
            for k in keys:
                d = target[k]
                d["mentions"] += 1
                d["fav"] += fav
                d[bucket] += 1
                d["sent_sum"] += s

    def finish(d):
        out = []
        total = sum(v["mentions"] for v in d.values()) or 1
        for k, v in sorted(d.items(), key=lambda kv: -kv[1]["mentions"]):
            out.append({
                **{"name": k}, **v,
                "mention_share_pct": round(v["mentions"] / total * 100, 2),
                "fav_share_pct": round(v["fav"] / v["mentions"] * 100, 2) if v["mentions"] else 0,
                # Net sentiment as (pos - neg) / mentions, bounded -1..1. The mean
                # compound score is reported too; they disagree when a flavor
                # draws strong opinions in both directions, which is worth seeing.
                "net_sentiment": round((v["pos"] - v["neg"]) / v["mentions"], 3) if v["mentions"] else 0,
                "mean_compound": round(v["sent_sum"] / v["mentions"], 3) if v["mentions"] else 0,
            })
        return out

    return {
        "engine": engine,
        "rows_seen": seen, "rows_matched": matched,
        "match_rate_pct": round(matched / seen * 100, 2) if seen else 0,
        "noise_stripped": noise_hits,
        "flavors": finish(fl), "brands": finish(br),
    }


def _demo(path, limit):
    csv.field_size_limit(10 ** 7)
    with open(path, encoding="utf-8", errors="replace") as fh:
        res = analyse(csv.DictReader(fh), limit=limit)
    print(f"\nengine: {res['engine']}")
    print(f"rows {res['rows_seen']:,}  matched {res['rows_matched']:,} "
          f"({res['match_rate_pct']}%)  noise stripped from {res['noise_stripped']:,}\n")
    for label, key in (("FLAVOR", "flavors"), ("BRAND", "brands")):
        print(f"{label:<14}{'mentions':>10}{'share%':>8}{'fav%':>7}{'net':>7}{'mean':>7}")
        for r in res[key][:14]:
            print(f"  {r['name']:<12}{r['mentions']:>10,}{r['mention_share_pct']:>8}"
                  f"{r['fav_share_pct']:>7}{r['net_sentiment']:>7}{r['mean_compound']:>7}")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--demo", metavar="CSV", help="run over a committed corpus and print")
    ap.add_argument("--limit", type=int, default=40000)
    a = ap.parse_args()
    if a.demo:
        _demo(a.demo, a.limit)
    else:
        ap.print_help()
