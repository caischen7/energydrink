# Wikipedia — brand interest (pageviews)

Monthly English-Wikipedia pageviews per brand, a platform-neutral proxy for
public *curiosity* in a brand over time (a Google-Trends-style signal we can
build ourselves, no API key).

- `brand_interest.csv` — one row per `(brand, month)`: `brand, article, month, views`
- `brand_pages.csv` — one row per brand: `brand, article, total_views_12mo, avg_monthly_views`

Source: [Wikimedia Pageviews API](https://wikimedia.org/api/rest_v1/) — public,
documented, free. Scraper: `data/scrapers/wikipedia.py`.

> ⚠️ **The committed files are GENERATED SAMPLE data** (from
> `data/scripts/generate_sample_data.py`) so the dashboard renders offline.
> Replace them with real measured data by running the scraper where outbound
> network is allowed:
>
> ```bash
> python data/scrapers/wikipedia.py                # -> these files
> python data/scripts/build_dashboard_json.py      # refresh the dashboard
> ```
