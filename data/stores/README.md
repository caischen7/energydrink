# Store map — where the panel sells

The page is `stores.html`; the file it reads is `public/data/stores_map.json`,
built by `data/scripts/build_stores_map.py`.

> ⚠️ **The committed `stores_map.json` is a GENERATED PLACEHOLDER** for the two
> PDI layers (state bubbles and store clusters), so the page renders and can be
> tested on a fresh checkout with no BigQuery token — the same arrangement as
> `data/openfoodfacts/` and `data/wikipedia/`. It carries `"source": "sample"`
> and `stores.html` shows a standing, non-dismissible banner while it does.
>
> **The bottling-plant layer is real** OpenStreetMap data, read straight from
> `data/osm/bottling_candidates.csv`. It is independent of the `--sample`
> switch, so that layer is measured either way.

Replace the placeholder where a BigQuery token is available:

```bash
python data/scripts/build_stores_map.py --dry-run
BQ_TOKEN=$(gcloud auth application-default print-access-token) \
  python data/scripts/build_stores_map.py
```

## Why there is no raw store file in this repo

`pdi_stores` is licensed. `build_flavor_explorer.py` states the rule the whole
`data/bq/` side of this repo follows — "No SKU rows, no store data, no GTINs
reach the browser" — and a map of 18,300 exact store coordinates is the panel
roster republished. So the builder does two things before it writes anything:

1. **Bins stores to a `GRID_DEG` grid.** A published point is a cell holding a
   count and a revenue total, never a store. `STORE_ID`, exact `LATITUDE` /
   `LONGITUDE`, `ZIP_CODE` and per-store chain stay in the warehouse.
2. **Drops cells under `MIN_CELL` stores.** A one-store cell *is* that store's
   location and revenue wearing a grid cell's clothes. `meta.stores_suppressed`
   reports how many stores this costs, and the page prints it, because the
   honest version of this map is one that says where it is blind.

State rollups are exempt: a total over hundreds of stores discloses nothing
about any one of them.

## Read before drawing conclusions

- **PDI is convenience-channel only, and roughly an 8.6% sample of it**
  (assumption D1 in `docs/ASSUMPTIONS.md`, rated **low** confidence — no
  selection criteria are published).
- **The panel grew 3.89× over 2019–2025**, 5,148 → 20,022 active stores. Density
  on this map is partly where PDI signed chains, not only where the category
  sells. That is why every metric is a single trailing-twelve-month window: a
  map of change over time would be mostly panel growth drawn as demand.
- **`STATE`'s encoding is unverified.** Nothing in this repo had ever read the
  column, so `state_code()` accepts both `CA` and `California`. Check which one
  actually comes back on the first real run.
- **`GRID_DEG` and `MIN_CELL` were tuned on synthetic points** (0.05° suppressed
  67% of stores, 0.1° suppressed 12%). Real retail clusters harder in cities and
  thinner in the countryside — re-sweep on real rows and watch
  `meta.stores_suppressed` before trusting rural coverage.
