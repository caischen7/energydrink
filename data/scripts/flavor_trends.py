#!/usr/bin/env python3
"""Does flavor chatter move before flavor sales?

The question
------------
If online interest in a flavor leads its shelf performance, that is a forecasting
signal worth having: it would let a launch decision run ahead of the sales data
instead of behind it. If it does not, that is worth knowing too, because the
whole category talks as though it does.

Two series, both derived from data already in this repo:

  CHATTER  YouTube — 68,930 video titles and 150,514 comments, dated 2008-2026.
           Flavor-family terms are matched with the same taxonomy the SKU
           classifier uses, so a flavor means the same thing on both sides.
  SALES    PDI — GTIN-year revenue joined to flavor_family.

How this is set up to avoid fooling itself
------------------------------------------
1. SHARES, NOT COUNTS. Both corpora grow over time - YouTube massively so. Two
   series that both rise will correlate at r > 0.9 while telling you nothing.
   Everything below is each flavor's SHARE of its year, on both sides.

2. CHANGES, NOT LEVELS. Even as shares, a flavor with a persistently high share
   on both sides produces a high correlation that is pure cross-sectional
   overlap, not evidence about timing. The lead/lag test uses year-on-year
   CHANGE in share, which is what "does chatter move first" actually asks.

3. POOLED PANEL, NOT PER-FLAVOR. Seven years gives at most six change
   observations per flavor - far too few for a per-flavor correlation to mean
   anything. Flavors are pooled into one panel, giving 14 x ~6 observations.

4. ALL LAGS REPORTED. Testing several lags and reporting the best one is how a
   null result gets dressed up as a finding. Every lag tested is printed,
   including the ones that disagree.

5. COVERAGE RAMP. PDI measures $38M in 2018 and $395M in 2019, so flavor shares
   before 2019 are not comparable. The panel starts in 2019.

    python data/scripts/flavor_trends.py            # print the analysis
    python data/scripts/flavor_trends.py --write    # embed into the aggregate

stdlib only.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify_target_consumers import FLAVOR_FAMILIES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGG = os.path.join(ROOT, "public/data/dashboard.json")
FIRST_YEAR = 2019          # PDI coverage is not comparable before this
LAST_YEAR = 2025           # 2026 is a partial scrape on both sides

PATTERNS = [(name, re.compile(rx, re.I)) for name, rx in FLAVOR_FAMILIES]

# Terms that match a flavor word but are not about a drink flavor. The same
# problem the share-of-voice work hit with Eminem's "The Monster".
NOISE = re.compile(
    r"apple (music|tv|watch|store|pay|id|iphone)|"
    r"blackberry (phone|bold|curve)|"
    r"orange (county|is the new|juice wrld)|"
    r"cherry (bomb|blossom|picking)|"
    r"grape (street|ape)|"
    r"sour (patch kids movie|grapes)|"
    r"cream (of the crop)",
    re.I,
)


def year_of(s):
    s = (s or "").strip()
    return int(s[:4]) if len(s) >= 4 and s[:4].isdigit() else None


def families(text):
    """Every flavor family named in a string, deduped. Noise phrases removed first."""
    if not text:
        return ()
    t = NOISE.sub(" ", text)
    return tuple({name for name, rx in PATTERNS if rx.search(t)})


def chatter():
    """Flavor mentions per year across video titles and comments."""
    counts = defaultdict(lambda: defaultdict(int))
    n_items = defaultdict(int)

    with open(os.path.join(ROOT, "data/youtube/videos.csv"), newline="") as f:
        for r in csv.DictReader(f):
            y = year_of(r.get("upload_date"))
            if y is None:
                continue
            n_items[y] += 1
            for fam in families(r.get("title")):
                counts[y][fam] += 1

    with open(os.path.join(ROOT, "data/youtube/comments.csv"), newline="") as f:
        for r in csv.DictReader(f):
            y = year_of(r.get("comment_date"))
            if y is None:
                continue
            n_items[y] += 1
            for fam in families(r.get("comment")):
                counts[y][fam] += 1

    return counts, n_items


def sales():
    """PDI revenue per flavor family per year."""
    fam_of = {}
    with open(os.path.join(ROOT, "data/bq/pdi_unique_products.csv"), newline="") as f:
        for r in csv.DictReader(f):
            ff = (r.get("flavor_family") or "").strip()
            if ff and ff not in ("Unknown", "Unspecified"):
                fam_of[r["GTIN"]] = ff

    rev = defaultdict(lambda: defaultdict(float))
    with open(os.path.join(ROOT, "data/bq/pdi_gtin_by_year.csv"), newline="") as f:
        for r in csv.DictReader(f):
            fam = fam_of.get(r["GTIN"])
            if not fam:
                continue
            try:
                rev[int(r["yr"])][fam] += float(r["rev"])
            except ValueError:
                continue
    return rev


def shares(per_year):
    """Convert {year: {fam: n}} to {year: {fam: share of that year}}."""
    out = {}
    for y, d in per_year.items():
        tot = sum(d.values())
        out[y] = {k: v / tot * 100 for k, v in d.items()} if tot else {}
    return out


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None, None
    r = sxy / math.sqrt(sxx * syy)
    # Two-sided p from a t approximation; adequate at these sample sizes.
    if abs(r) >= 1:
        return r, 0.0
    t = abs(r) * math.sqrt((n - 2) / (1 - r * r))
    p = 2 * (1 - _t_cdf(t, n - 2))
    return r, p


def _t_cdf(t, df):
    """Student-t CDF via the incomplete beta, so no scipy dependency."""
    x = df / (df + t * t)
    return 1 - 0.5 * _betainc(df / 2, 0.5, x)


def _betainc(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    # The continued fraction below converges from the left and degrades badly as
    # x approaches 1 - which is exactly where a near-zero correlation lands,
    # since t ~ 0 gives x = df/(df + t^2) ~ 1. Without this reflection a
    # correlation of r = -0.0005 came back with p = 0.105 instead of ~1.0.
    if x > (a + 1) / (a + b + 2):
        return 1 - _betainc(b, a, 1 - x)
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    f, c, d = 1.0, 1.0, 0.0
    for i in range(200):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1 + num * d
        d = 1e-30 if abs(d) < 1e-30 else d
        d = 1 / d
        c = 1 + num / c
        c = 1e-30 if abs(c) < 1e-30 else c
        f *= c * d
        if abs(1 - c * d) < 1e-10:
            break
    return front * (f - 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    ch_counts, n_items = chatter()
    ch = shares(ch_counts)
    sl = shares(sales())

    years = [y for y in range(FIRST_YEAR, LAST_YEAR + 1) if y in ch and y in sl]
    fams = sorted({f for _, rx in FLAVOR_FAMILIES for f in [_]}
                  & set().union(*[set(sl[y]) for y in years]))

    print(f"years {years[0]}-{years[-1]}   flavors {len(fams)}")
    print(f"chatter items per year: " +
          ", ".join(f"{y}:{n_items.get(y,0):,}" for y in years))

    # ---- 1. cross-section: does chatter share look like revenue share at all?
    last = years[-1]
    xs = [ch[last].get(f, 0) for f in fams]
    ys = [sl[last].get(f, 0) for f in fams]
    r_cs, p_cs = pearson(xs, ys)
    print(f"\ncross-section {last}: chatter share vs revenue share across "
          f"{len(fams)} flavors -> r={r_cs:+.2f} p={p_cs:.3f}")

    # ---- 2. pooled lead/lag on year-on-year CHANGES
    print("\nlead/lag, pooled year-on-year change in share:")
    print("  lag  n     r      p     reading")
    lag_rows = []
    for lag in (0, 1, 2):
        xs, ys = [], []
        for f in fams:
            for i in range(1, len(years)):
                y0, y1 = years[i - 1], years[i]
                if y1 + lag > years[-1]:
                    continue
                dch = ch[y1].get(f, 0) - ch[y0].get(f, 0)
                sy0, sy1 = y0 + lag, y1 + lag
                if sy1 not in sl:
                    continue
                dsl = sl[sy1].get(f, 0) - sl[sy0].get(f, 0)
                xs.append(dch)
                ys.append(dsl)
        r, p = pearson(xs, ys)
        reading = ("no usable signal" if r is None or p is None or p > 0.10
                   else "chatter and sales move together" if lag == 0
                   else f"chatter leads sales by {lag} year{'s' if lag > 1 else ''}")
        lag_rows.append({"lag": lag, "n": len(xs),
                         "r": None if r is None else round(r, 3),
                         "p": None if p is None else round(p, 4),
                         "reading": reading})
        print(f"  {lag:>3}  {len(xs):<4}  {r:+.3f}  {p:.3f}  {reading}"
              if r is not None else f"  {lag:>3}  {len(xs):<4}   n/a    n/a  too few")

    # ---- 3. per-flavor, printed so nothing is hidden behind the pooled number
    print("\nper-flavor chatter vs revenue share, latest year:")
    for f in sorted(fams, key=lambda f: -sl[last].get(f, 0)):
        print(f"  {f:<22} chatter {ch[last].get(f,0):5.1f}%   revenue {sl[last].get(f,0):5.1f}%")

    out = {
        "years": years,
        "flavors": fams,
        "chatter": {str(y): {f: round(ch[y].get(f, 0), 2) for f in fams} for y in years},
        "sales": {str(y): {f: round(sl[y].get(f, 0), 2) for f in fams} for y in years},
        "cross_section": {"year": last, "r": None if r_cs is None else round(r_cs, 3),
                          "p": None if p_cs is None else round(p_cs, 4), "n": len(fams)},
        "lags": lag_rows,
        "items_per_year": {str(y): n_items.get(y, 0) for y in years},
    }

    if args.write:
        with open(AGG) as f:
            agg = json.load(f)
        agg["audiences"]["opportunity"]["flavor_trends"] = out
        with open(AGG, "w") as f:
            json.dump(agg, f, separators=(",", ":"))
        print(f"\nwrote flavor_trends -> {AGG}")


if __name__ == "__main__":
    main()
