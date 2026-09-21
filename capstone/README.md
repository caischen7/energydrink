# Capstone — which energy-drink flavors are most popular, and which are best rated

Separate from the marketing site in this repo. Nothing here feeds `npm run build`.

```
capstone/
  scripts/build_registry.py     # emits the registries below; --check re-derives and diffs
  run_reddit_deep.py            # ← RUN THIS ONE (--self-test / --dry-run / real)
  .env.example                  # copy to .env, fill in, gitignored
  collectors/
    flavor_mentions.py          # shared flavor/brand extractor + sentiment (WS3.3)
    reddit_collector.py         # Reddit Data API, OAuth, aggregates-only (WS3.2)
    make_label_sample.py        # hand-label sampler for precision (WS3.4)
  validation/                   # label samples to fill in
  REDDIT_API_TERMS.md           # PRECONDITION — unverified, read before any real run
  registry/                     # PRE-REGISTERED, date-stamped, versioned
    brands_v1.0_<date>.csv
    flavor_taxonomy_v1.0_<date>.csv
    flavor_order_probes_v1.0_<date>.csv    # evidence for the taxonomy's precedence rules
    open_decisions_v1.0_<date>.csv         # forks only Cai can settle
  assumptions.md                # append-only
```

## Compliance

- **No retailer scraping.** Amazon/Walmart/Target ratings are collected by hand
  by Cai into the WS1 template; this repo only validates and loads them.
- **No Reddit or YouTube HTML.** Official APIs only, keys from environment
  variables, never hardcoded. The Reddit Data API terms summary is a
  precondition of WS3 and has not been written yet.
- **PDI is licensed** and must not leave the warehouse. Only reduced aggregates
  are committed; see `data/stores/README.md` for the precedent this follows.

## Workstream status

| WS | What | Status |
|---|---|---|
| 0 | SKU universe + flavor taxonomy | **Awaiting approval** — 8 open decisions |
| 1 | Retailer ratings (manual capture → Bayesian adjustment) | Not started |
| 2 | PDI sales velocity | Not started |
| 3 | Reddit + YouTube text | **Collector built, not yet run** — blocked on `REDDIT_API_TERMS.md` and on your approval of the search terms |

## Running the Reddit collector

```bash
python capstone/run_reddit_deep.py --self-test   # no creds, no network — start here
python capstone/run_reddit_deep.py --dry-run     # show the plan, call nothing
python capstone/run_reddit_deep.py               # deep pull, bounded to 2000 posts
```

In VS Code: Run and Debug (Ctrl+Shift+D) → pick a config → F5. Four are
defined in `.vscode/launch.json`, from self-test to an unbounded multi-hour run.

Credentials: copy `capstone/.env.example` to `capstone/.env` and fill it in.
Read `REDDIT_API_TERMS.md` first — it is a precondition, not a formality.

## Reproducing Workstream 0

```bash
python capstone/scripts/build_registry.py          # writes the registries
python capstone/scripts/build_registry.py --check  # drift check, writes nothing
```

Stdlib only. Reads `data/bq/derived/brand_momentum_real.csv` and imports the
taxonomy from `data/scripts/classify_target_consumers.py` rather than restating
it — a second copy of those rules is a defect, not a record. See the script's
docstring for the two limitations that carry into every later workstream.
