# Scraping guide — per-site gotchas

Practical notes for running the free scrapers in `data/scripts/`. Read this
before fighting a wall by hand — most "failures" are a known bot barrier with a
documented way around it.

## The one rule: run them on your own machine

Every browser/HTTP scraper here must run from a **residential connection**. The
retail and social sites block datacenter IPs, so **none of these run from a
cloud container** (this repo's CI/cloud sessions hit a domain allowlist and get
`403`/`Access Denied` immediately). Clone the repo locally, run in a VS Code
terminal, commit the resulting CSVs.

```bash
pip3 install playwright && python3 -m playwright install chromium   # once
python3 data/scripts/run_all.py --light        # small run, safest sources first
```

Browser scrapers open a real Chromium window and use a **persistent profile** —
solve a site's challenge **once** and the profile remembers it next time.

## Per-source cheat sheet

| Source | Backend to use | Bot wall | Reviews? | Notes |
| --- | --- | --- | --- | --- |
| **YouTube** | `api` (free key) | none | comments | Set `YOUTUBE_API_KEY`; else falls back to slower `yt-dlp`. Biggest corpus — run first. |
| **Reddit** | `public` (default) | none | n/a | Stdlib JSON, no key. Writes to gitignored `raw_data/` (no usernames). |
| **Amazon** | `browser` | text CAPTCHA | ✅ | Solve the "type the characters" CAPTCHA once. `--review-pages N` for more reviews; `--detail` on by default for descriptions/bullets. |
| **Walmart** | `browser` (or `serpapi`) | PerimeterX press-and-hold | ✅ | `direct` backend is usually blocked. `serpapi` needs `SERPAPI_KEY` (paid past free tier). `--detail` adds `upc`. |
| **Target / Costco / H-E-B** | `scrape_retailers.py` browser | varies (Costco = Akamai sometimes) | ✅ (Target/Costco/H-E-B) | Trader Joe's/Whole Foods/Publix expose **no reviews**. |
| **Kroger** | **`api`** (free) | Akamai — the toughest | ❌ via API | See below. |
| **Instagram** | `--login BURNER` | anonymous access = 403 | n/a | See below. |
| **TikTok** | `browser` | slider/puzzle captcha | n/a | Solve once; profile remembers. |
| **Meta Ad Library** | `browser` | usually none | n/a | Public by design — brand *advertising*, not posts. |

## Instagram — anonymous no longer works

Instagram returns **403 on the anonymous GraphQL endpoint**, which surfaces as a
misleading `@brand does not exist`. The account is fine — you're blocked. The
scraper now aborts with that explanation instead of skipping every profile.

```bash
python3 data/scripts/scrape_instagram.py --login YOUR_BURNER_ACCOUNT
```

⚠️ Use a **throwaway** account — scraping from a logged-in account risks a ban.
Keep volume low (defaults are already conservative). The repo already ships
`data/instagram/posts.csv`; a fresh pull is optional.

## Kroger — use the API, skip the browser

`kroger.com` is behind **Akamai** and serves a hard `Access Denied` (Reference
`#18...`) that **cannot be solved by waiting or clicking** — the browser backend
will just fail. Use Kroger's official free API instead:

1. Create a free app at **developer.kroger.com**.
2. Export credentials:
   ```bash
   export KROGER_CLIENT_ID=...
   export KROGER_CLIENT_SECRET=...
   ```
3. Run — it auto-selects the API and attaches prices for a store:
   ```bash
   python3 data/scripts/scrape_kroger.py --kroger-zip 45202
   ```

Trade-off: the API returns **products + prices but no reviews** (Kroger's API
doesn't expose them). If you specifically need Kroger reviews, the only path is
the browser backend from a residential IP, retried later when the Akamai flag
clears — but Amazon/Walmart/Target already give a strong review corpus, so this
is rarely worth the fight.

## Cross-retailer joins — UPC

Retailer IDs (Amazon ASIN, Walmart itemId, Target TCIN) are **not** portable.
The universal key is the **UPC/GTIN** printed on the can. Walmart's scraper can
capture it with `--detail` (one extra `/ip/` page load per product); it's the
join key for matching the same product across stores. See the ER data model for
the full Product → Listing → Review schema.

## Env vars at a glance

| Var | For | Required? |
| --- | --- | --- |
| `YOUTUBE_API_KEY` | YouTube `api` backend | recommended (else yt-dlp) |
| `SERPAPI_KEY` | Walmart `serpapi` backend | only if you pass `--backend serpapi` |
| `KROGER_CLIENT_ID` / `KROGER_CLIENT_SECRET` | Kroger `api` backend | yes, for Kroger |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Reddit `praw` backend | optional |

Each scraper has offline parse tests: `python3 -m pytest data/scripts/tests/`.
