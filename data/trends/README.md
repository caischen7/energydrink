# Google Trends exports go here

**You should not need to do anything here.** `.github/workflows/trends.yml`
refreshes this directory on the 2nd of every month, re-runs the search → sales
model, and commits both back. Setup is one repository secret:

    Settings → Secrets and variables → Actions → New repository secret
      SERPAPI_KEY = <your key>

    Settings → Actions → General → Workflow permissions → Read and write

Then Actions → *Refresh Google Trends* → **Run workflow** to prove it, rather
than waiting a month. The model's verdict appears in the run summary.

Without `SERPAPI_KEY` the job falls back to **pytrends**: free, unofficial,
rate-limited, and liable to break whenever Google changes its internals. It is
fine for a first look and a poor thing to depend on. SerpApi's Google Trends
endpoint costs money, but this uses 13 calls a month, which is negligible on
any plan.

## Why it runs on GitHub rather than here

The Claude Code container cannot reach `trends.google.com` — the egress gateway
answers **403 to the CONNECT**, an organisation policy denial rather than a
network fault (`api.github.com` returns 200 from the same shell). GitHub's
runners are not behind that proxy.

## The normalisation trap the collector avoids

Google Trends returns a **0–100 index scaled to the maximum inside the window
you asked for**, not absolute volume. So fetching `2019–2025` and then
`2019–2026` rescales every historical point. Appending "just the new months" to
an existing file therefore splices segments on different scales and produces
jumps that are pure artifact.

`data/scrapers/google_trends.py` refetches the **entire window every run** and
rewrites each file. A few extra API calls, and a whole class of silent error
gone. For the same reason values are comparable *within* a term and meaningless
*across* terms — the model only ever uses within-term change.

## Doing it by hand instead

If you would rather not wire up the Action, export manually:

For each term below: <https://trends.google.com/trends/explore>

1. Enter the search term.
2. Set **Country = United States**.
3. Set **Time range = 2019-01-01 to 2025-12-31**. *(Match the sales window. PDI
   coverage before 2019 is too thin to compare — measured revenue is $38M in
   2018 against $395M in 2019 — and 2026 is a partial scrape.)*
4. Category: **All categories**. Search type: **Web Search**.
5. Click the download arrow on the "Interest over time" panel.
6. Rename the file to the **flavor family**, exactly as spelled below, and save
   it here.

## Terms to export

One file per flavor family. The family name is the filename; the search term is
what you type into Trends. Add `energy drink` to each term — bare "watermelon"
measures the fruit, and the whole point is to measure drink intent.

| Save as | Search term |
| --- | --- |
| `Original.csv` | `energy drink` |
| `Berry.csv` | `berry energy drink` |
| `Citrus.csv` | `citrus energy drink` |
| `Sour & candy.csv` | `sour energy drink` |
| `Tropical.csv` | `tropical energy drink` |
| `Watermelon.csv` | `watermelon energy drink` |
| `Grape.csv` | `grape energy drink` |
| `Punch & mixed fruit.csv` | `fruit punch energy drink` |
| `Peach & stone fruit.csv` | `peach energy drink` |
| `Apple & pear.csv` | `apple energy drink` |
| `Coffee & cream.csv` | `coffee energy drink` |
| `Tea & botanical.csv` | `tea energy drink` |
| `Cola & soda.csv` | `cola energy drink` |

Those names match `FLAVOR_FAMILIES` in `classify_target_consumers.py`, which is
what makes a flavor mean the same thing on the search side and the sales side.
A file whose name does not match a family is ignored rather than guessed at.

The expected format is Google's own export, unedited:

```
Category: All categories

Week,berry energy drink: (United States)
2019-01-06,72
2019-01-13,68
```

Weekly and monthly exports are both handled. The loader averages within each
year, so one viral week cannot carry a year.

## Then

```bash
python data/scripts/trends_model.py --source google
python data/scripts/trends_model.py --source google --write   # into the aggregate
```

## What to expect, honestly

Trends values are a **0–100 index relative to that term's own peak**. They are
comparable *within* a term and meaningless *across* terms — "coffee energy
drink" at 80 is not twice "grape energy drink" at 40. The model therefore only
uses within-term change and never compares levels between families.

**The bigger limit is on the sales side, not this one.** PDI as committed here
is GTIN × *year*. Joining weekly search to annual sales discards 51 of every 52
search observations and leaves seven points per flavor — enough to test whether
a relationship exists, not enough to deploy a forecast. Run against the YouTube
stand-in, the model already fails to beat a persistence baseline (MAE 0.99 vs
0.81), which is the expected result at this granularity.

**If this matters, get monthly PDI.** `pdi_daily_agg` in BigQuery has the
detail; one aggregation to flavor × month over 2019–2025 turns 91 panel rows
into roughly 1,000. That is the change that would make this a real model. Use a
partition filter and dry-run it first — a full scan of that table runs
$0.35–0.55.
