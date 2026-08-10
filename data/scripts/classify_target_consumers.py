#!/usr/bin/env python3
"""
Label every PDI energy-drink SKU with the consumer it is built for.

Reads  data/bq/pdi_unique_products.csv  (2,309 GTINs pulled from pdi_daily_agg)
Writes the same file back with three added columns:

    target_consumer         one of the nine segments below
    target_consumer_detail  a sentence describing who that is
    target_evidence         how the label was reached — this is the important one:

        simmons   MRI-Simmons 2024 measured audience data (7 brands only)
        web       the brand's own published positioning / trade-press reporting
        inferred  deduced from product attributes alone (sugar-free line, pack
                  format, product type). No audience data behind it.

Brand rules win over attribute rules, because a brand's positioning is a stronger
signal than a can size. Attribute rules then catch the long tail of 200-odd
brands nobody has profiled, and split the big brands' zero-sugar lines out of
their sugared parents — those genuinely sell to different people.

Rerunnable: it strips its own columns first, so it never double-appends.
"""
import csv
import os
import re
import sys

SRC = os.path.join(os.path.dirname(__file__), "..", "bq", "pdi_unique_products.csv")

ADDED = ["target_consumer", "target_consumer_detail", "target_evidence"]

# ---------------------------------------------------------------- segments
SEGMENTS = {
    "Mainstream Stimulant Loyalist": (
        "18–34, skewing male, buying on habit and brand. Simmons puts Red Bull at "
        "index 198 for 25–34 and Monster at 177 — the youngest-adult audiences measured."
    ),
    "Zero-Sugar Switcher": (
        "The same mainstream buyer trading down on sugar, plus older and more "
        "female drinkers the sugared lines never reached. Calorie-driven, not fitness-driven."
    ),
    "Gym & Performance": (
        "Fitness enthusiasts, roughly 24–35 and about 70/30 male, buying a "
        "pre-workout in ready-to-drink form. Sold on caffeine dose and aminos."
    ),
    "Fitness Wellness (female-led)": (
        "Millennial and Gen Z women with fitness and wellness goals. Celsius runs "
        "a 50/50 male-female split; Alani Nu was built for this buyer specifically."
    ),
    "Gamer & Creator": (
        "Teens-to-late-20s gamers and creator-community fans. Bought for the "
        "influencer or the flavor drop as much as the caffeine."
    ),
    "Blue-Collar & Value": (
        "Shift workers, drivers, trades and military. Price-per-ounce first: "
        "Rip It sells on 'energy fuel at a price you can swallow'."
    ),
    "Natural & Clean Energy": (
        "Better-for-you buyers who reject the category's stimulant framing — "
        "organic, yerba mate, plant caffeine. Skews older and more affluent."
    ),
    "Coffee Crossover": (
        "Adult coffee drinkers entering the category sideways. Wants caffeine "
        "without the energy-drink identity."
    ),
    "Functional Shot": (
        "35–54, function over refreshment, taken as a dose not a drink. Simmons "
        "shows 5-hour Energy indexing 221 on sports fandom and 175 Black/African American."
    ),
}

# ------------------------------------------------------- brand -> segment
# `simmons` where MRI-Simmons measured the audience directly; `web` where the
# label rests on the brand's published positioning or trade-press reporting.
BRAND = {
    # measured audience
    "Red Bull": ("Mainstream Stimulant Loyalist", "simmons"),
    "Monster": ("Mainstream Stimulant Loyalist", "simmons"),
    "Rockstar": ("Mainstream Stimulant Loyalist", "simmons"),
    "NOS": ("Blue-Collar & Value", "simmons"),
    "Bang": ("Gym & Performance", "simmons"),
    "AMP": ("Mainstream Stimulant Loyalist", "simmons"),
    "Mtn Dew AMP": ("Mainstream Stimulant Loyalist", "simmons"),
    "5-Hour Energy": ("Functional Shot", "simmons"),
    # published positioning
    "Celsius": ("Fitness Wellness (female-led)", "web"),
    "Alani Nu": ("Fitness Wellness (female-led)", "web"),
    "Bloom": ("Fitness Wellness (female-led)", "web"),
    "C4": ("Gym & Performance", "web"),
    "Ghost": ("Gym & Performance", "web"),
    "Ryse": ("Gym & Performance", "web"),
    "REDCON1": ("Gym & Performance", "web"),
    "Bucked Up": ("Gym & Performance", "web"),
    "Cellucor": ("Gym & Performance", "web"),
    "1st Phorm": ("Gym & Performance", "web"),
    "Optimum Nutrition": ("Gym & Performance", "web"),
    "Xyience": ("Gym & Performance", "web"),
    "Adrenaline Shoc": ("Gym & Performance", "web"),
    "3D Energy": ("Gym & Performance", "web"),
    "Gorilla": ("Gym & Performance", "web"),
    "Reign": ("Gym & Performance", "web"),
    "Gatorade Fast Twitch": ("Gym & Performance", "web"),
    "ZOA": ("Gym & Performance", "web"),
    "G FUEL": ("Gamer & Creator", "web"),
    "Prime": ("Gamer & Creator", "web"),
    "G.O.A.T. Fuel": ("Gamer & Creator", "web"),
    "Rip It": ("Blue-Collar & Value", "web"),
    "Venom": ("Blue-Collar & Value", "web"),
    "Full Throttle": ("Blue-Collar & Value", "web"),
    "Raptor": ("Blue-Collar & Value", "web"),
    "Liquid Ice": ("Blue-Collar & Value", "web"),
    "Ol' Glory": ("Blue-Collar & Value", "web"),
    "Bum Energy": ("Blue-Collar & Value", "web"),
    "Adrenaline Rush": ("Blue-Collar & Value", "web"),
    "Guayaki": ("Natural & Clean Energy", "web"),
    "Yachak": ("Natural & Clean Energy", "web"),
    "Mtn Dew Rise": ("Natural & Clean Energy", "web"),
    "Uptime": ("Natural & Clean Energy", "web"),
    "Starbucks Baya": ("Natural & Clean Energy", "web"),
    "Blue Bottle Coffee": ("Coffee Crossover", "web"),
    "Black Rifle Coffee Company": ("Coffee Crossover", "web"),
    "Arizona Energy": ("Blue-Collar & Value", "web"),
    "Mtn Dew (energy)": ("Mainstream Stimulant Loyalist", "web"),
}

# Brands whose zero-sugar lines sell to a different person than the sugared
# parent. Only applies where the parent is a mainstream sugared brand — a
# sugar-free Ghost is still bought by the same gym-goer.
SPLIT_ON_SUGAR_FREE = {
    "Red Bull", "Monster", "Rockstar", "NOS", "AMP", "Mtn Dew AMP",
    "Full Throttle", "Venom", "Rip It", "Mtn Dew (energy)", "Arizona Energy",
    "Raptor", "Liquid Ice", "Adrenaline Rush", "Ol' Glory", "Bum Energy",
}

SUGAR_FREE = re.compile(
    r"sugar[\s-]?free|zero|diet|low calorie|no sugar|ultra", re.I)
NATURAL = re.compile(r"organic|yerba|mate|kombucha|botanic|plant", re.I)
COFFEE = re.compile(r"coffee|espresso|latte|cold brew|mocha|cappuccino", re.I)
# \b matters on the sizes: without it "2 OZ" matches inside "12 OZ".
SHOT = re.compile(r"\bshot\b|\b2 ?oz\b|\b1\.9\d? ?oz\b|\b2\.5 ?oz\b", re.I)
PERFORMANCE = re.compile(
    r"pre[\s-]?workout|bcaa|amino|creatine|performance|\bpump\b|\bfit\b|protein", re.I)


def blob(row):
    """Everything textual about the SKU, for the attribute rules to read."""
    return " ".join(
        row.get(c, "") or "" for c in
        ("PRODUCT_DESCRIPTION", "FLAVOR", "PRODUCT_TYPE", "SUB_PRODUCT_TYPE",
         "UNIT_SIZE", "PACKAGE", "BRAND")
    )


def classify(row):
    """-> (segment, evidence). Brand first, then attributes."""
    brand = (row.get("canonical_brand") or "").strip()
    text = blob(row)
    ptype = (row.get("PRODUCT_TYPE") or "")
    sub = (row.get("SUB_PRODUCT_TYPE") or "")
    sugar_free = bool(SUGAR_FREE.search(sub) or SUGAR_FREE.search(text))

    hit = BRAND.get(brand)
    if hit:
        seg, ev = hit
        if sugar_free and brand in SPLIT_ON_SUGAR_FREE:
            # the sugar-free line is a different buyer; the split itself is an
            # attribute inference even though the brand label was measured
            return "Zero-Sugar Switcher", "inferred"
        return seg, ev

    # ---- attribute fallback for the ~200 unprofiled brands ----
    if SHOT.search(text) or "Shot" in ptype:
        return "Functional Shot", "inferred"
    if COFFEE.search(text) or "Coffee" in ptype:
        return "Coffee Crossover", "inferred"
    if NATURAL.search(text) or "Organic" in ptype or "Yerba" in ptype:
        return "Natural & Clean Energy", "inferred"
    if PERFORMANCE.search(text):
        return "Gym & Performance", "inferred"
    if sugar_free:
        return "Zero-Sugar Switcher", "inferred"
    return "Mainstream Stimulant Loyalist", "inferred"


def main():
    path = os.path.normpath(SRC)
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("no rows in " + path)

    base = [c for c in rows[0].keys() if c not in ADDED]   # rerunnable
    for r in rows:
        seg, ev = classify(r)
        r["target_consumer"] = seg
        r["target_consumer_detail"] = SEGMENTS[seg]
        r["target_evidence"] = ev

    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=base + ADDED, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"labelled {len(rows)} SKUs -> {path}")


if __name__ == "__main__":
    main()
