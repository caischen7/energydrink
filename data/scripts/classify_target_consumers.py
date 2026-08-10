#!/usr/bin/env python3
"""
Label every PDI energy-drink SKU with the consumer it is built for.

Reads  data/bq/pdi_unique_products.csv  (2,309 GTINs pulled from pdi_daily_agg)
Writes the same file back with four added columns describing who buys it:

    target_consumer   the audience in plain words — "Gym & fitness",
                      "Women 18-34", "Shift workers & military", ...
    target_age        the age band that over-indexes
    target_gender     Male-skewing / Female-skewing / Mixed
    target_notes      one line on what that buyer wants

Ages and gender come from MRI-Simmons 2024 where the brand was measured
(Red Bull, Monster, Rockstar, NOS, Bang, AMP, 5-hour Energy); from the brand's
published positioning elsewhere; and from product attributes for the long tail
of small brands.

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

ADDED = ["target_consumer", "target_age", "target_gender", "target_notes"]

# ------------------------------------------------- audience -> age/gender/note
# Age bands for the Simmons-measured brands are the ones that actually
# over-index in MRI-Simmons 2024 (index >150 vs all US adults).
AUDIENCE = {
    "Young adults": (
        "18-34", "Male-skewing",
        "Habit and brand loyalty. Red Bull indexes 198 on 25-34, Monster 177."),
    "Calorie-cutters": (
        "25-44", "Mixed",
        "Same mainstream drinker cutting sugar. Reaches older and more female buyers."),
    "Gym & fitness": (
        "24-35", "Male-skewing (~70/30)",
        "Ready-to-drink pre-workout. Buys on caffeine dose, aminos, zero sugar."),
    "Women (fitness & wellness)": (
        "18-34", "Female-skewing",
        "Millennial and Gen Z women. Slim cans, fruit flavors, wellness framing."),
    "Gamers & creators": (
        "16-27", "Male-skewing",
        "Bought for the influencer or flavor drop as much as the caffeine."),
    "Shift workers & military": (
        "25-44", "Male-skewing",
        "Price per ounce first. Drivers, trades, deployed personnel."),
    "Health-conscious adults": (
        "30-55", "Mixed",
        "Rejects the stimulant framing. Organic, yerba mate, plant caffeine."),
    "Coffee drinkers": (
        "30-55", "Mixed",
        "Wants the caffeine without the energy-drink identity."),
    "Older functional users": (
        "35-54", "Male-skewing",
        "A dose, not a drink. 5-hour Energy indexes 221 on sports fandom."),
}

# ------------------------------------------------------ brand -> audience
BRAND = {
    # --- audience measured directly in MRI-Simmons 2024 ---
    "Red Bull": "Young adults",
    "Monster": "Young adults",
    "Rockstar": "Young adults",          # note: skews 35-44, not young; see AGE_OVERRIDE
    "NOS": "Shift workers & military",
    "Bang": "Gym & fitness",
    "AMP": "Young adults",
    "Mtn Dew AMP": "Young adults",
    "5-Hour Energy": "Older functional users",
    # --- audience from the brand's published positioning ---
    "Celsius": "Women (fitness & wellness)",
    "Alani Nu": "Women (fitness & wellness)",
    "Bloom": "Women (fitness & wellness)",
    "C4": "Gym & fitness",
    "Ghost": "Gym & fitness",
    "Ryse": "Gym & fitness",
    "REDCON1": "Gym & fitness",
    "Bucked Up": "Gym & fitness",
    "Cellucor": "Gym & fitness",
    "1st Phorm": "Gym & fitness",
    "Optimum Nutrition": "Gym & fitness",
    "Xyience": "Gym & fitness",
    "Adrenaline Shoc": "Gym & fitness",
    "3D Energy": "Gym & fitness",
    "Gorilla": "Gym & fitness",
    "Reign": "Gym & fitness",
    "Gatorade Fast Twitch": "Gym & fitness",
    "ZOA": "Gym & fitness",
    "G FUEL": "Gamers & creators",
    "Prime": "Gamers & creators",
    "G.O.A.T. Fuel": "Gamers & creators",
    "Rip It": "Shift workers & military",
    "Venom": "Shift workers & military",
    "Full Throttle": "Shift workers & military",
    "Raptor": "Shift workers & military",
    "Liquid Ice": "Shift workers & military",
    "Ol' Glory": "Shift workers & military",
    "Bum Energy": "Shift workers & military",
    "Adrenaline Rush": "Shift workers & military",
    "Arizona Energy": "Shift workers & military",
    "Guayaki": "Health-conscious adults",
    "Yachak": "Health-conscious adults",
    "Mtn Dew Rise": "Health-conscious adults",
    "Uptime": "Health-conscious adults",
    "Starbucks Baya": "Health-conscious adults",
    "Blue Bottle Coffee": "Coffee drinkers",
    "Black Rifle Coffee Company": "Coffee drinkers",
    "Mtn Dew (energy)": "Young adults",
}

# Where Simmons contradicts the audience's default age band, the measured
# number wins — Rockstar reads as a young brand but indexes 183 on 35-44.
AGE_OVERRIDE = {
    "Rockstar": "35-44",
    "NOS": "25-44",
    "Bang": "18-34",
}

# Brands whose zero-sugar lines sell to a different person than the sugared
# parent. Only applies to mainstream sugared brands — a sugar-free Ghost is
# still bought by the same gym-goer.
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
    """-> (audience, age). Brand first, then product attributes."""
    brand = (row.get("canonical_brand") or "").strip()
    text = blob(row)
    ptype = row.get("PRODUCT_TYPE") or ""
    sub = row.get("SUB_PRODUCT_TYPE") or ""
    sugar_free = bool(SUGAR_FREE.search(sub) or SUGAR_FREE.search(text))

    aud = BRAND.get(brand)
    if aud:
        if sugar_free and brand in SPLIT_ON_SUGAR_FREE:
            return "Calorie-cutters", AUDIENCE["Calorie-cutters"][0]
        return aud, AGE_OVERRIDE.get(brand, AUDIENCE[aud][0])

    # ---- attribute fallback for the ~190 brands with no published audience ----
    if SHOT.search(text) or "Shot" in ptype:
        aud = "Older functional users"
    elif COFFEE.search(text) or "Coffee" in ptype:
        aud = "Coffee drinkers"
    elif NATURAL.search(text) or "Organic" in ptype or "Yerba" in ptype:
        aud = "Health-conscious adults"
    elif PERFORMANCE.search(text):
        aud = "Gym & fitness"
    elif sugar_free:
        aud = "Calorie-cutters"
    else:
        aud = "Young adults"
    return aud, AUDIENCE[aud][0]


def main():
    path = os.path.normpath(SRC)
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("no rows in " + path)

    # drop any columns from a previous run, including the older schema
    stale = set(ADDED) | {"target_consumer_detail", "target_evidence"}
    base = [c for c in rows[0].keys() if c not in stale]

    for r in rows:
        aud, age = classify(r)
        _, gender, note = AUDIENCE[aud]
        r["target_consumer"] = aud
        r["target_age"] = age
        r["target_gender"] = gender
        r["target_notes"] = note

    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=base + ADDED, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"labelled {len(rows)} SKUs -> {path}")


if __name__ == "__main__":
    main()
