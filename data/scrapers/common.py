"""Shared helpers for the energy-drink scrapers.

Stdlib only (urllib) so the scrapers run anywhere Python does — no pandas,
no requests. Keeps brand names consistent with the existing cleaned datasets
(`data/scripts/build_clean_datasets.py` uses the same canonical names) so a
freshly scraped source joins cleanly onto `combined/brand_summary.csv`.
"""
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
# data/scrapers/common.py -> repo root is two levels up from this file's dir.
SCRAPERS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.dirname(SCRAPERS_DIR)
ROOT = os.path.dirname(DATA_DIR)


def data_path(*parts):
    return os.path.join(DATA_DIR, *parts)


# --------------------------------------------------------------------------
# Brand normalization — kept in sync with build_clean_datasets.py BRAND_ALIASES
# so every source resolves to one canonical name across the whole pipeline.
# --------------------------------------------------------------------------
BRAND_ALIASES = {
    "celsius": "Celsius", "celsiusofficial": "Celsius",
    "red bull": "Red Bull", "redbull": "Red Bull",
    "monster": "Monster", "monsterenergy": "Monster", "monster energy": "Monster",
    "liquid i.v.": "Liquid I.V.", "liquid iv": "Liquid I.V.",
    "ghost": "Ghost", "ghost energy": "Ghost",
    "bang": "Bang", "bangenergy": "Bang", "bang energy": "Bang",
    "alani nu": "Alani Nu", "alaninutrition": "Alani Nu", "alani": "Alani Nu",
    "rockstar": "Rockstar", "rockstarenergy": "Rockstar", "rockstar energy": "Rockstar",
    "5-hour energy": "5-hour Energy", "5 hour energy": "5-hour Energy",
    "5-hour": "5-hour Energy",
    "nos": "NOS",
    "reign": "Reign", "reignbodyfuel": "Reign", "reign total body fuel": "Reign",
    "zoa": "Zoa", "zoaenergy": "Zoa",
    "prime": "Prime", "drinkprime": "Prime", "prime energy": "Prime",
    "g fuel": "G Fuel", "gfuel": "G Fuel",
    "advocare": "AdvoCare", "advocare spark": "AdvoCare",
    "bloom nutrition": "Bloom Nutrition", "bloom": "Bloom Nutrition",
    "c4": "C4", "c4 energy": "C4", "cellucor": "C4",
    "guru": "GURU",
    "liquid death": "Liquid Death",
    "pureboost": "Pureboost",
    "spylt": "Spylt",
    "xwerks": "Xwerks",
    "zipfizz": "Zipfizz",
}

# The 23 canonical brands the rest of the pipeline already tracks.
CANONICAL_BRANDS = [
    "5-hour Energy", "AdvoCare", "Alani Nu", "Bang", "Bloom Nutrition", "C4",
    "Celsius", "G Fuel", "GURU", "Ghost", "Liquid Death", "Liquid I.V.",
    "Monster", "NOS", "Prime", "Pureboost", "Red Bull", "Reign", "Rockstar",
    "Spylt", "Xwerks", "Zipfizz", "Zoa",
]

# English-Wikipedia article titles for the brands that have a page. Used by the
# Wikipedia pageviews scraper. Brands without a stable article are omitted.
WIKI_ARTICLES = {
    "5-hour Energy": "5-hour Energy",
    "Alani Nu": "Alani Nu",
    "Bang": "Bang Energy",
    "C4": "Cellucor",
    "Celsius": "Celsius (drink)",
    "G Fuel": "Gamma Labs",
    "Ghost": "Ghost (lifestyle brand)",
    "Liquid Death": "Liquid Death",
    "Liquid I.V.": "Liquid I.V.",
    "Monster": "Monster Energy",
    "NOS": "NOS (drink)",
    "Prime": "Prime (drink)",
    "Red Bull": "Red Bull",
    "Reign": "Reign (drink)",
    "Rockstar": "Rockstar (drink)",
    "Zoa": "Zoa (drink)",
}


def norm_brand(value):
    """Map a raw brand string to its canonical name (or a cleaned passthrough)."""
    if value is None:
        return None
    key = str(value).strip().lower()
    if not key:
        return None
    if key in BRAND_ALIASES:
        return BRAND_ALIASES[key]
    # brands cells are often "Red Bull, Red Bull GmbH" — try the first token too
    first = key.split(",")[0].strip()
    if first in BRAND_ALIASES:
        return BRAND_ALIASES[first]
    return str(value).strip()


def match_known_brand(text):
    """Return the first canonical brand whose alias appears in free text, else None.

    Used to attribute an arbitrary product/title to a tracked brand when the
    source's own brand field is missing or noisy.
    """
    low = (text or "").lower()
    # longest aliases first so "5 hour energy" wins over a bare "energy"
    for alias in sorted(BRAND_ALIASES, key=len, reverse=True):
        if alias in low:
            return BRAND_ALIASES[alias]
    return None


# --------------------------------------------------------------------------
# HTTP — a small, polite JSON getter with retries + backoff. Public APIs only.
# --------------------------------------------------------------------------
USER_AGENT = os.environ.get(
    "SCRAPER_USER_AGENT",
    "BogusBanana-market-research/1.0 (educational; contact: energydrinks@example.com)",
)


def http_get(url, params=None, retries=4, backoff=2.0, timeout=30):
    """GET a URL and return the decoded body text. Retries with exponential backoff.

    Handles gzip and 429/5xx politely (honours Retry-After when present).
    Raises the last error if every attempt fails.
    """
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    last_err = None
    for attempt in range(retries):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504):
                wait = float(e.headers.get("Retry-After", 0)) or backoff * (2 ** attempt)
                _log(f"  {e.code} on attempt {attempt + 1}; sleeping {wait:.0f}s")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            wait = backoff * (2 ** attempt)
            _log(f"  {type(e).__name__} on attempt {attempt + 1}; sleeping {wait:.0f}s")
            time.sleep(wait)
    raise last_err if last_err else RuntimeError(f"GET failed: {url}")


def http_get_json(url, params=None, **kw):
    return json.loads(http_get(url, params=params, **kw))


def _log(msg):
    print(msg, file=sys.stderr, flush=True)


def write_csv(path, fieldnames, rows):
    """Write dict rows to a CSV, creating parent dirs. Returns row count."""
    import csv
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    _log(f"  wrote {path} ({len(rows)} rows)")
    return len(rows)
