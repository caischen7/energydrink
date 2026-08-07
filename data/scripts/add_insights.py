#!/usr/bin/env python3
"""
Fold the cross-source insight set and the data-model (ER) map into dashboard.json.

Kept separate from build_dashboard_json.py for the same reason as add_bq_panels.py: this
content is derived from the licensed capstone BigQuery project rather than the scraped CSV
corpus, and it refreshes on a different cadence.

The findings themselves are aggregate conclusions rather than licensed rows, but they are
written into the nginx-guarded aggregate so the whole intel surface sits behind one gate.

Idempotent - re-running overwrites only the `insights` key.

Run AFTER build_dashboard_json.py, which rewrites the whole file:

    python data/scripts/build_dashboard_json.py
    python data/scripts/add_bq_panels.py
    python data/scripts/add_insights.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "public", "data", "dashboard.json")

INSIGHTS = {
 "generated": "2026-08",
 "sources": [
  {"id": "pdi", "name": "PDI Point-of-Sale", "kind": "Retail scan data",
   "scale": "1.09B rows · 2,178 SKUs · 35,389 stores · 2016-2026",
   "what": "Actual transactions from convenience stores. The only source here that measures money changing hands rather than opinion or intent.",
   "limit": "Convenience channel only - no club, grocery, mass or e-commerce."},
  {"id": "mintel_survey", "name": "Mintel Consumer Survey", "kind": "Stated preference",
   "scale": "539K rows · n=2,000 adults (766 energy-drink consumers)",
   "what": "What consumers say they want, including concepts that do not exist on shelf yet.",
   "limit": "Stated intent over-states behaviour. Question IDs repeat across reports, so filters must match question text."},
  {"id": "gnpd", "name": "Mintel GNPD", "kind": "Product launches",
   "scale": "766 launches · 2018-2026",
   "what": "Every new product introduction with claims, flavours, pack and price. The industry's bets before they show up in sales.",
   "limit": "Launch counts, not sales. A launch is an intention, not a success."},
  {"id": "passport", "name": "Euromonitor Passport", "kind": "Market share",
   "scale": "210 rows · USA · 2016-2025",
   "what": "National brand share by retail value and by volume - all channels, not just c-store.",
   "limit": "Two measures in one table; filter on `measure` or shares double-count."},
  {"id": "simmons", "name": "Simmons Brand Profiles", "kind": "Consumer profiling",
   "scale": "603 rows · 8 brands",
   "what": "Who drinks which brand, indexed against the average US adult, including health and food attitudes.",
   "limit": "Only legacy brands. Celsius, Alani Nu, Ghost and C4 are absent."},
  {"id": "usda", "name": "USDA Branded Foods", "kind": "Formulation",
   "scale": "1,315 energy-drink SKUs with full ingredient lists",
   "what": "What is actually in the can - ingredient decks, sugar, calories, sodium.",
   "limit": "Caffeine is populated on only 0.7% of rows and is unusable."},
  {"id": "mulo", "name": "Mintel MULO", "kind": "Multi-outlet sales",
   "scale": "Brand sales and share, 2025 vs 2026",
   "what": "Broader-channel retail dollars - a cross-check on the c-store view.",
   "limit": "Top brands only."}
 ],
 "insights": [
  {"src": "usda", "tier": "headline", "title": "The shelf is one formula repeated 1,300 times",
   "finding": "Caffeine (78%), B6 (72%), niacin (71%), B12 (71%), potassium (59%), sucralose (58%) and taurine (50%) form a commodity core present in most SKUs.",
   "why": "Differentiation on the current axis is nearly impossible - you would be launching the same liquid with a different label.",
   "metric": "7 ingredients appear in half or more of all energy-drink SKUs"},
  {"src": "usda", "tier": "headline", "title": "Functional ingredients consumers ask for are almost absent",
   "finding": "Ashwagandha 1.0% of SKUs, rhodiola 0.3%, lion's mane 0.1%, reishi 0.2%. Cordyceps, probiotics and any product literally naming itself nootropic or adaptogenic: zero.",
   "why": "This is the clearest supply gap in the dataset - and it sits directly against the top-ranked consumer concept.",
   "metric": "0% of shelf names an adaptogen or nootropic"},
  {"src": "usda", "tier": "support", "title": "Sweetener choice is synthetic by default",
   "finding": "Sucralose 58% and acesulfame-K 42% dominate. Stevia is 12%, monk fruit 3.0%, allulose 0.5%.",
   "why": "A natural-sweetener product is genuinely rare on shelf, not merely under-marketed.",
   "metric": "Natural sweeteners are on under 1 in 8 SKUs"},
  {"src": "mintel_survey", "tier": "headline", "title": "Consumers rank 'natural' above 'sugar-free'",
   "finding": "Top concepts: additional functional benefits 40.7%, natural sweeteners 39.4%, natural caffeine 38.4%, adaptogens 33.9%.",
   "why": "The industry is optimising for sugar-free, which consumers did not rank first.",
   "metric": "39.4% would try a naturally-sweetened energy drink"},
  {"src": "mintel_survey", "tier": "support", "title": "Gen X wants 'natural' more than Gen Z does",
   "finding": "Functional benefits index 51.5% among Gen X vs 33.8% Gen Z; natural sweeteners 49.5% vs 36.5%.",
   "why": "The natural positioning skews older than the category's marketing assumes. Boomers are not published for this question.",
   "metric": "Gen X leads on 6 of the top 7 concepts"},
  {"src": "mintel_survey", "tier": "support", "title": "Function and taste are joint first, not a trade-off",
   "finding": "Top-2-box motivations: boost energy 77.8%, enjoy the taste 77.2%, stay awake 75.0%, improve focus 74.4%.",
   "why": "A functional product that tastes mediocre loses half the motivation set. Both have to be true.",
   "metric": "Taste ties with energy as the #1 reason to drink"},
  {"src": "gnpd", "tier": "headline", "title": "Sugar-free is table stakes, not white space",
   "finding": "72.3% of 2024-26 launches claim sugar-free, up from 48.5% in 2018-20. Cognitive/brain claims went 25.8% to 53.8%.",
   "why": "Launching 'sugar-free' as the differentiator now means matching three quarters of the pipeline.",
   "metric": "+23.8pp sugar-free, +28.0pp cognitive claims"},
  {"src": "gnpd", "tier": "support", "title": "Beauty-function appeared from nothing",
   "finding": "Hair/nails and skin claims went 0% of launches in 2018-20 to 10.6% in 2024-26.",
   "why": "A new segment forming in real time - and precisely Alani Nu's positioning.",
   "metric": "0% to 10.6% in six years"},
  {"src": "pdi", "tier": "headline", "title": "Only 6% of new brands ever reach $1M",
   "finding": "150 brands entered since 2019. Nine reached $1M trailing-12-month revenue. None reached $10M.",
   "why": "This is the base rate to plan against. The realistic ceiling for a c-store entrant is single-digit millions.",
   "metric": "6% reach $1M · 0% reach $10M"},
  {"src": "pdi", "tier": "headline", "title": "You cannot enter with a single SKU",
   "finding": "Median revenue per SKU: $4K for one-SKU brands, $50K at 4-8 SKUs, $1.87M at 25+.",
   "why": "Buyers allocate shelf to blocks, not orphans. Read a broad range as a necessary condition for scale.",
   "metric": "400x spread between 1-SKU and 25+-SKU brands"},
  {"src": "pdi", "tier": "headline", "title": "'Original' flavour is bleeding share to fruit",
   "finding": "Original fell from 36.2% of category revenue in 2019 to 30.1% in 2025. Watermelon rose +4.8pp, Juneberry +4.6pp.",
   "why": "The category is fragmenting toward specific and proprietary fruit flavours. Fruit Punch (-3.8pp) and Blue Razz (-1.5pp) show the losers are the generic ones.",
   "metric": "Original -6.2pp in six years"},
  {"src": "pdi", "tier": "support", "title": "A third of revenue sits in one price band",
   "finding": "$0.25-0.30 per ounce holds 33.9% of single-serve revenue on 177 SKUs - $7.4M revenue per SKU, double any other band.",
   "why": "That is where consumers have shown willingness to pay. Above $0.40/oz is a graveyard: 45 SKUs, 0.4% of revenue.",
   "metric": "$7.4M revenue per SKU at $0.25-0.30/oz"},
  {"src": "pdi", "tier": "support", "title": "Regional strongholds are real",
   "finding": "Guayaki indexes 1,035 in California, 852 in Oregon, 692 in Colorado. Rip It indexes 512 in Michigan.",
   "why": "Regional launches demonstrably work here - a concentrated beachhead is cheaper than national distribution.",
   "metric": "10x national share in a single state"},
  {"src": "simmons", "tier": "headline", "title": "No legacy brand reaches the genuinely health-conscious",
   "finding": "'I consider my diet very healthy' - best brand indexes 91. 'Nutritional value is most important' - 92. Yet the category indexes 181 on 'influenced by the latest health food trends'.",
   "why": "The category attracts trend-followers, not the health-driven. But Celsius and Alani Nu are absent from this panel, so read it as why they are winning rather than as open territory.",
   "metric": "Every health attitude sits below index 100"},
  {"src": "passport", "tier": "support", "title": "Two brands own two thirds of the market",
   "finding": "Monster 38.2% and Red Bull 34.5% of US retail value in 2025; Celsius 10.6%.",
   "why": "A challenger competes for the remaining third, and mostly against other challengers.",
   "metric": "Top 2 = 72.7% of retail value"},
  {"src": "mulo", "tier": "headline", "title": "Alani Nu is the breakout, and social data missed it",
   "finding": "Alani Nu +84% in MULO and +96% in POS. Bang, which the site's mention-share panel ranked a top riser, actually fell 15.6%.",
   "why": "Attention and demand diverge. Sales data should override social signals wherever they disagree.",
   "metric": "+96% POS growth vs a -15.6% brand ranked as 'rising'"},
  {"src": "combined", "tier": "headline", "title": "The convergent thesis: natural + functional, priced at $0.25-0.30/oz",
   "finding": "Four independent sources agree. Consumers rank natural and functional first (Mintel). The shelf is 58% sucralose with near-zero adaptogens (USDA). Health-oriented consumers are unreached by legacy brands (Simmons). The fastest-growing brands already occupy that space (POS + MULO).",
   "why": "This is the only claim in the analysis supported by stated preference, formulation, consumer profiling and actual sales at the same time.",
   "metric": "4 sources · 1 conclusion"},
  {"src": "combined", "tier": "support", "title": "Strawberry is the most over-launched flavour",
   "finding": "9.6% of recent launches are strawberry; it is 0.1% of sales. Lime, berry, cherry and orange follow the same pattern.",
   "why": "Launch activity is a poor guide to demand. Watermelon is the exception - heavily launched and genuinely growing.",
   "metric": "9.6% of launches, 0.1% of sales"}
 ],
 "er": {
  "tables": [
   {"id": "pdi_daily_agg", "label": "pdi_daily_agg", "src": "pdi", "rows": "1.09B",
    "cols": ["GTIN", "STORE_ID", "DATE", "TOTAL_REVENUE_AMOUNT", "QUANTITY", "QUANTITY_WITH_DISCOUNT"],
    "note": "Fact table. Energy drinks only."},
   {"id": "pdi_master_gtin", "label": "pdi_master_gtin", "src": "pdi", "rows": "70.8K",
    "cols": ["GTIN", "BRAND", "FLAVOR", "PACK_SIZE", "UNIT_SIZE", "SUBCATEGORY", "MANUFACTURER_PARENT"],
    "note": "Product dimension. All c-store categories."},
   {"id": "pdi_stores", "label": "pdi_stores", "src": "pdi", "rows": "35.4K",
    "cols": ["STORE_ID", "STATE", "CITY", "ZIP_CODE", "STORE_CHAIN_NAME", "LATITUDE", "LONGITUDE"],
    "note": "Store dimension. 18.3K active."},
   {"id": "pdi_energy_drinks_monthly", "label": "pdi_*_monthly", "src": "pdi", "rows": "13.6K",
    "cols": ["month", "canonical_brand", "stores", "gtins", "units", "revenue"],
    "note": "Pre-aggregated rollup. Use instead of the fact table."},
   {"id": "brand_crosswalk", "label": "brand_crosswalk", "src": "pdi", "rows": "124",
    "cols": ["raw_label", "canonical_brand", "parent_company"],
    "note": "Brand normalisation. Multiple rows per label - dedupe before joining."},
   {"id": "usda_branded_foods", "label": "usda_branded_foods", "src": "usda", "rows": "18.6K",
    "cols": ["gtin_upc", "brand_name", "ingredients", "total_sugars_g", "energy_kcal"],
    "note": "Joins to PDI on barcode, but padding differs."},
   {"id": "gnpd_products", "label": "gnpd_products", "src": "gnpd", "rows": "766",
    "cols": ["brand", "date_published", "flavours", "positioning_claims", "launch_type"],
    "note": "Brand-level join only."},
   {"id": "mintel_survey_data", "label": "mintel_survey_data", "src": "mintel_survey", "rows": "539K",
    "cols": ["question_id", "question_text", "demo_group", "demo_value", "response", "value"],
    "note": "No join key. Question IDs repeat across reports."},
   {"id": "simmons_brand_profiles", "label": "simmons_brand_profiles", "src": "simmons", "rows": "603",
    "cols": ["brand", "column_group", "column_value", "index"],
    "note": "Brand-level join. 8 legacy brands only."},
   {"id": "passport_brand_shares", "label": "passport_brand_shares", "src": "passport", "rows": "210",
    "cols": ["brand", "company_gbo", "measure", "year", "share_pct"],
    "note": "Brand-level join. Filter on measure."},
   {"id": "mintel_mulo_brand_sales", "label": "mintel_mulo_brand_sales", "src": "mulo", "rows": "15",
    "cols": ["brand", "sales_2026_usd_m", "share_change_ppt"],
    "note": "Brand-level join."}
  ],
  "edges": [
   {"a": "pdi_daily_agg", "b": "pdi_master_gtin", "on": "GTIN", "kind": "strong", "label": "GTIN"},
   {"a": "pdi_daily_agg", "b": "pdi_stores", "on": "STORE_ID", "kind": "strong", "label": "STORE_ID"},
   {"a": "pdi_master_gtin", "b": "brand_crosswalk", "on": "BRAND = raw_label", "kind": "fuzzy", "label": "brand name"},
   {"a": "pdi_energy_drinks_monthly", "b": "brand_crosswalk", "on": "canonical_brand", "kind": "strong", "label": "canonical_brand"},
   {"a": "pdi_master_gtin", "b": "usda_branded_foods", "on": "GTIN = gtin_upc", "kind": "fuzzy", "label": "barcode (padding differs)"},
   {"a": "brand_crosswalk", "b": "gnpd_products", "on": "brand", "kind": "fuzzy", "label": "brand name"},
   {"a": "brand_crosswalk", "b": "simmons_brand_profiles", "on": "brand", "kind": "fuzzy", "label": "brand name"},
   {"a": "brand_crosswalk", "b": "passport_brand_shares", "on": "brand", "kind": "fuzzy", "label": "brand name"},
   {"a": "brand_crosswalk", "b": "mintel_mulo_brand_sales", "on": "brand", "kind": "fuzzy", "label": "brand name"},
   {"a": "mintel_survey_data", "b": "gnpd_products", "on": "no key - compared conceptually", "kind": "none", "label": "no join key"}
  ]
 }
}

with open(OUT, encoding="utf-8") as fh:
    data = json.load(fh)
data["insights"] = INSIGHTS
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(data, fh, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

print(f"Added insights ({len(INSIGHTS['insights'])} findings across "
      f"{len(INSIGHTS['sources'])} sources, {len(INSIGHTS['er']['tables'])} tables) -> {OUT}")
