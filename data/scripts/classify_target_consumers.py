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

ADDED = ["target_consumer", "target_age", "target_gender", "target_notes",
         "flavor_family"]

# ------------------------------------------------- audience -> age/gender/note
# Age bands for the Simmons-measured brands are the ones that actually
# over-index in MRI-Simmons 2024 (index >150 vs all US adults).
AUDIENCE = {
    "Young adults": (
        "18-34", "Male-skewing",
        "Drinks it out of habit and brand loyalty. 25-34s are about twice as "
        "likely as the average adult to drink Red Bull, and 1.8x for Monster."),
    "Calorie-cutters": (
        "25-44", "Mixed",
        "The same mainstream drinker cutting sugar, not chasing fitness. "
        "The zero-sugar lines reach older and more female buyers than the sugared ones."),
    "Gym & fitness": (
        "24-35", "Male-skewing (~70/30)",
        "Wants a pre-workout they can drink from a can. Buys on caffeine dose, "
        "aminos and zero sugar. Roughly 7 in 10 are men."),
    "Women (fitness & wellness)": (
        "18-34", "Female-skewing",
        "Millennial and Gen Z women with fitness and wellness goals. Slim cans, "
        "fruit flavors, wellness language instead of extreme-sports language."),
    "Gamers & creators": (
        "16-27", "Male-skewing",
        "Buys the influencer and the flavour drop as much as the caffeine. "
        "Mostly reached online, so convenience stores understate this group."),
    "Shift workers & military": (
        "25-44", "Male-skewing",
        "Price per ounce decides it. Drivers, trades and deployed personnel "
        "buying the cheapest effective can on the shelf."),
    "Health-conscious adults": (
        "30-55", "Mixed",
        "Rejects the stimulant framing entirely. Wants organic, yerba mate or "
        "plant caffeine, and skews older and better-off than the category."),
    "Coffee drinkers": (
        "30-55", "Mixed",
        "Wants the caffeine without identifying as an energy-drink drinker. "
        "Comes in through cold brew and canned coffee rather than the energy aisle."),
    "Older functional users": (
        "35-54", "Male-skewing",
        "Takes it as a dose, not a drink. Heavily skewed toward avid sports "
        "fans, who are more than twice as likely as average to buy it."),
}

# Where a brand's own measured audience differs from its group, say so on the
# row itself rather than making the reader infer it from the group note.
BRAND_NOTE = {
    "Rockstar":
        "Reads as a young brand but its drinkers are concentrated in the 35-44 "
        "band, who are about 1.8x more likely than average to drink it.",
    "NOS":
        "Skews distinctly male - about three quarters of drinkers are in "
        "male-headed households - and concentrates in the 25-34 band.",
    "Bang":
        "The youngest audience measured in the category: 18-24s are nearly "
        "twice as likely as the average adult to drink it.",
    "5-Hour Energy":
        "Taken as a dose, not a drink. Avid sports fans are over twice as "
        "likely as average to buy it, and Black/African American adults 1.75x.",
    "Red Bull":
        "25-34s are about twice as likely as the average adult to drink it - "
        "the youngest-skewing large brand in the category.",
    "Monster":
        "25-34s are about 1.8x as likely as average to drink it, with a "
        "noticeable skew toward lower-income households.",
    "Celsius":
        "Read as a women's brand, but consumption is close to an even 50/50 "
        "split between men and women.",
    "Alani Nu":
        "Built specifically for Millennial and Gen Z women, and the audience "
        "matches the intent more closely than any other brand here.",
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


# ------------------------------------------------------------- flavor families
# 860 distinct raw flavor strings collapse to 14 families. Order matters: the
# first pattern to match wins, so the specific ones (Sour/candy, Cola) sit above
# the broad fruit buckets that would otherwise swallow them.
FLAVOR_FAMILIES = [
    ("Original", r"\borig|classic|\bthe original\b|regular"),
    ("Coffee & cream", r"coffee|espresso|latte|mocha|cappuccino|vanilla|cream(?!sicle)|caramel|horchata"),
    ("Sour & candy", r"sour|candy|gummy|bubble ?gum|cotton|razz|slush|freeze|rainbow|"
                      r"swedish fish|birthday cake|sherbet|sorbet|marshmallow|s'?more"),
    ("Cola & soda", r"cola|root ?beer|dr\.? ?pepper|cream ?soda|ginger"),
    ("Watermelon", r"watermelon"),
    ("Berry", r"berry|berries|raspberry|blueberry|strawberr|blackberry|acai|cranberr|juneberry|cherry"),
    ("Tropical", r"tropical|mango|pineapple|passion|guava|coconut|papaya|dragon ?fruit|kiwi|banana|hawaii"),
    ("Citrus", r"citrus|orange|lemon|lime|grapefruit|tangerine|clementine|yuzu"),
    ("Grape", r"grape"),
    ("Apple & pear", r"apple|pear"),
    ("Peach & stone fruit", r"peach|apricot|nectarine|plum|mango peach"),
    ("Punch & mixed fruit", r"punch|fruit|melon|mixed|blast|blend|medley"),
    ("Tea & botanical", r"tea|mate|yerba|mint|menthol|lavender|hibiscus|ginseng|matcha"),
    ("Melon & other", r"melon|cucumber|honeydew|cantaloupe"),
]
FLAVOR_RX = [(name, re.compile(rx, re.I)) for name, rx in FLAVOR_FAMILIES]


def flavor_family(row):
    """
    Group the raw flavor into one of 14 families.

    FLAVOR is blank on 499 of 2,309 SKUs, so fall back to the product
    description, which usually names the flavor inline
    ("RED BULL WATERMELON ENERGY DRINK 12 OZ CAN").
    """
    raw = (row.get("FLAVOR") or "").strip()
    text = raw or (row.get("PRODUCT_DESCRIPTION") or "")
    if not text.strip():
        return "Unspecified"
    for name, rx in FLAVOR_RX:
        if rx.search(text):
            return name
    # A named flavor that matches nothing is not a gap in the rules — it is an
    # invented name (Frose Rose, Cosmic Stardust, Witch's Brew). That is Mintel's
    # "branded flavors" trend, so it gets its own family rather than a junk bucket.
    return "Novelty & branded" if raw else "Unspecified"


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
        brand = (r.get("canonical_brand") or "").strip()
        # a brand-specific note only applies while the SKU still sits in that
        # brand's own audience - a sugar-free Monster is a calorie-cutter now
        if brand in BRAND_NOTE and aud == BRAND.get(brand):
            note = BRAND_NOTE[brand]
        r["target_consumer"] = aud
        r["target_age"] = age
        r["target_gender"] = gender
        r["target_notes"] = note
        r["flavor_family"] = flavor_family(r)

    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=base + ADDED, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"labelled {len(rows)} SKUs -> {path}")


if __name__ == "__main__":
    main()
