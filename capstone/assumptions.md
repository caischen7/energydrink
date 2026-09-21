# Assumptions log — flavor popularity & rating study

Every analytical choice that could have gone another way. One row per
assumption, with what it rests on, what it would change if wrong, and whether
it has been tested. Append-only: supersede rows, do not delete them.

Maintained by Cai. Entries below were added during **Workstream 0**
(2026-09-21) and are unratified until Cai signs off.

| # | Assumption | Rests on | If wrong | Confidence | Tested? |
|---|---|---|---|---|---|
| A-01 | The PDI convenience panel is an acceptable frame for "most popular" | It is the only measured sell-through available | Every popularity ranking is convenience-only, and misses e-commerce, club and natural-grocery entirely | **Low–Med** | No |
| A-02 | Top-10-by-revenue is an acceptable SKU universe | Covers 94.89% of measured T12M revenue and contains 8 of the 9 brands in the brief | A flavor that only exists on brand 11+ is invisible to the study | Med | Partly — coverage computed, unit-basis not |
| A-03 | Revenue rank ≈ unit rank for the top 10 | Price-per-ounce differences are large between brands but not large enough to reorder the head | Red Bull's 37.9% overstates its unit share; the universe could be mis-selected | **Low** | **No — see D-08** |
| A-04 | `brand_momentum_real.csv` measures the energy-drink category correctly | It is committed and the dashboard ships it | Every brand share in WS0 inherits an unaudited filter | **Low** | **No — see D-07, the query does not exist in this repo** |
| A-05 | The production `flavor_family()` is the right taxonomy to pre-register | It is already in use on the dashboard; a second copy would drift | A taxonomy tuned for a marketing page may be wrong for a flavor study | Med | Partly — audited for dead families and collisions |
| A-06 | First-match-over-an-ordered-list is acceptable as the "mutually exclusive" rule | It does guarantee exclusivity, which is what the brief asks for | Exclusivity is real but precedence is arbitrary at the margins; multi-fruit names land by list position | Med | **Yes — 17 probes, see flavor_order_probes CSV** |
| A-07 | Commercial behaviour beats botany (cherry → Berry) | How the flavor is merchandised and named | Stone-fruit demand looks smaller than it is | Med | No — D-04 |
| A-08 | A blank `FLAVOR` can be recovered from `PRODUCT_DESCRIPTION` | 499 of 2,309 SKUs have a blank FLAVOR and the description usually names it inline | Up to 21.6% of SKUs are mis-familied or land in Unspecified | Med | No — recovery rate not measured |
| A-09 | Prime belongs in the study as a case study, not a ranking row | Named in the brief; ~0.13% PDI share | Either a distorted ranking (if included) or a blind spot on the buzz-vs-sales question (if dropped) | Med | Partly — share computed from segments |
| A-10 | Prime Energy and Prime Hydration must not be summed | PDI carries both under one brand string, e.g. "PRIME ENERGY ... CAN" vs "PRIME ... SPORTS DRINKS" | A sports drink is counted as an energy drink | **High** | Yes — both description forms observed |

### Added during the flavor-by-year analysis (2026-09-21)

| # | Assumption | Rests on | If wrong | Confidence | Tested? |
|---|---|---|---|---|---|
| A-11 | Unit **share** is the right popularity metric for a growing panel | Share is invariant to panel size by construction: if coverage doubles, every family's units roughly double and shares do not move | Rankings would be a measure of PDI's sales team | **High** | **Yes** — shares sum to 100 in all 7 years (`npm run check -- facts`) |
| A-12 | Coverage's share of growth is the **log** split, 73% | `log(raw) = log(ramp) + log(per-store)`, so each term's share of `log(raw)` is its share of compound growth | An earlier `(1 − 1/x)` ratio gave 83% and has no interpretation | **High** | Yes — decomposition checked multiplicatively, 2.24 × 1.34 = 3.01 |
| A-13 | Average monthly `stores_active` is the right annual denominator | It is a property of the month, not the cluster, and is collected once per month | Double-counting it 14× would deflate every velocity by the same factor (ordering safe, levels wrong) | Med | Yes — guarded in `yearly()` |
| A-14 | Average monthly SKU count represents the year's lineup | Lineups change mid-year; the mean is the typical shelf | Units-per-SKU mis-states how hard a facing works | Med | No |
| A-15 | `units_per_active_store = reach × depth` is exact, not approximate | Algebraically it is: (stores/active) × (units/stores) = units/active | The scatter's decomposition would be decorative | **High** | **Yes** — reconstruction asserted to 2% for every row |
| A-16 | Peak year matters more than first-vs-last | 4 of the 4 families that "gained" since 2019 are past peak; Watermelon is 27% below a 2021 peak | A go-to-market brief would chase a declining flavor | **High** | Yes — computed per family |
| A-17 | "Novelty & branded" is kept in rankings but is not a flavor direction | It is the fallback for invented names, and at 13.7% it is too big to hide | Reading it as a flavor would send the brief chasing a naming convention | Med | No |
| A-18 | The Amazon snapshot cannot support a rating ranking | 51 products, one day, one retailer; whole spread 0.22★; one family has n=2 reviews | Presenting it as "highest rated" would be the study's weakest claim | **High** | **Yes** — sensitivity to m computed and published |

## Superseded

| # | Was | Now | Why |
|---|---|---|---|
| A-12 | Coverage = 83% of growth, via `(1 − 1/ramp)/(1 − 1/raw)` | **73%**, via `log(ramp)/log(raw)` | The original is an ad-hoc ratio that does not attribute anything. The decomposition is multiplicative, so the log split is the standard and interpretable one. Corrected before publication. |

## Pre-registration status

| Registry | Version | Frozen? |
|---|---|---|
| `brands` | 1.0 (2026-09-21) | **No** — 8 open decisions |
| `flavor_taxonomy` | 1.0 (2026-09-21) | **No** — D-01…D-04 open |

Freezing rule: once Cai approves, a change needs a new version number, a row in
**Superseded** above, and the reason. `build_registry.py --check` re-derives
from source and diffs, so drift between a frozen registry and its inputs is
detectable rather than silent.
