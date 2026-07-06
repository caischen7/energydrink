# Open Food Facts — product & nutrition

`products.csv` — energy-drink products with **sugar and caffeine per 100 ml**
and a Nutri-Score, keyed to the same canonical brands as the rest of the
pipeline. Fills the nutrition gap that `data/amazon/products.csv` (price/rating
only) leaves open.

Source: [Open Food Facts](https://world.openfoodfacts.org) — free, open
(ODbL-licensed), public API. Scraper: `data/scrapers/openfoodfacts.py`.

> ⚠️ **The committed file is GENERATED SAMPLE data** (from
> `data/scripts/generate_sample_data.py`), so the dashboard renders on a fresh
> checkout without network access. Replace it with real measured data by running
> the scraper where outbound network is allowed:
>
> ```bash
> python data/scrapers/openfoodfacts.py            # -> this file
> python data/scripts/build_dashboard_json.py      # refresh the dashboard
> ```
