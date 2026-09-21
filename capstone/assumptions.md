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

## Superseded

*(none yet)*

## Pre-registration status

| Registry | Version | Frozen? |
|---|---|---|
| `brands` | 1.0 (2026-09-21) | **No** — 8 open decisions |
| `flavor_taxonomy` | 1.0 (2026-09-21) | **No** — D-01…D-04 open |

Freezing rule: once Cai approves, a change needs a new version number, a row in
**Superseded** above, and the reason. `build_registry.py --check` re-derives
from source and diffs, so drift between a frozen registry and its inputs is
detectable rather than silent.
