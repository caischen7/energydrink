# OSM bottling-plant candidates

`bottling_candidates.csv` — 122 candidate soft-drink bottling plants and depots
in the US, extracted from **OpenStreetMap** via the
`bigquery-public-data.geo_openstreetmap` mirror (points + multipolygons,
`planet_features_*`). Query cost was $1.30.

## Read this before using it

**It is not a census.** OSM industrial tagging in the US is sparse and
volunteer-contributed. Only **23 of the 122** carry an explicit
`product`/`industrial`/`man_made` tag; the other 99 were matched on the word
"bottling" appearing in `name` or `operator`. A plant that nobody has mapped is
simply absent, and there is no way to know how many those are.

By parent, on the name match: Coca-Cola 46, Pepsi 38, independent/other 38.

**Known contamination that survived filtering.** Historic buildings, food halls
and distillery tourism carry "Bottling" in their names; the obvious ones
(museums, bars, tap rooms, "Bottlinger Grain") are removed, but the filter is a
word list and will not have caught everything. Two Canadian sites were dropped
by latitude. The bounding box is a rectangle, so a small number of northern
Mexican sites may remain.

**A depot is not a plant.** Several rows tagged `distributor` are distribution
centres, not manufacturing.

## The authoritative sources are elsewhere

For anything load-bearing use `data/plants/`, collected by
`.github/workflows/bottling.yml`:

- **Census CBP** (NAICS 312111) — complete establishment and employment counts
  by state and county. Anonymous: how much capacity, never whose.
- **EPA FRS** — named, geocoded, permit-derived facilities.

Neither separates energy drinks from soda or bottled water: **there is no
energy-drink NAICS code**. And most energy brands are co-packed rather than
owning plants, so this data answers "where is co-packing capacity" and not
"who makes what".
