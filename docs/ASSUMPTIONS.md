# Assumptions Log

**Analysis:** Bogus Banana — US energy-drink market sizing, audience segmentation and launch recommendation
**Decision it informs:** which consumer to build for, at what flavor, size and price
**Date:** 2026-08-14
**Method:** `analysis-assumptions-log` skill (nimrodfisher/data-analytics-skills), applied by hand

---

## Summary

| Total | Validated | Unvalidated critical | Unvalidated other |
|---|---|---|---|
| 20 | 9 | 3 | 8 |

**Four assumptions are both low-confidence and high-impact.** They are listed again at the
bottom with a validation plan. **Two have now been tested and both failed**: S3 (no structural
break) is contradicted by the women's deceleration, and S2 (damped linear drift) back-tests to a
5.1-point mean absolute error. Both results are published on the site rather than filed here.

Three findings on this site were corrected during the analysis, and **every one was a
denominator problem rather than an arithmetic error** — a figure computed correctly over the
wrong population. That pattern is why this log exists.

---

## Data assumptions

| # | Assumption | Rationale | Confidence | Impact if wrong | Validated | Result |
|---|---|---|---|---|---|---|
| D1 | PDI's ~18k active stores are representative of the 150k US convenience universe | No selection criteria published; store counts and revenue scale plausibly | **Low** | **High** | No | Untestable with data on hand — no external c-store benchmark. Mitigated by anchoring shares on Passport instead |
| D2 | The 131 duplicated barcodes are brand-period splits, not double counts | Extract groups by GTIN *and* canonical brand; PDI reassigns barcodes on rebrand (AMP → Mtn Dew Energy) | High | Medium | **Yes** | Confirmed. Revenue partitions rather than duplicates: both files total $7.124B to the dollar. Product count corrected 2,309 → 2,178 |
| D3 | Blank `FLAVOR` means the metadata is missing, not that the product has no flavor | 21.6% of rows blank, concentrated in bare "MONSTER"/"RED BULL" descriptions | High | Medium | **Yes** | Confirmed. A draft analysis read blank as "unflavored" and was cut in review; flavor work now covers the 52% of revenue where flavor is known |
| D4 | July 2026 is a partial month and must be excluded from trends | Data ends mid-month; including it would fake a collapse | High | Medium | **Yes** | Excluded everywhere. `COMPLETE_THROUGH` guards the dashboard aggregates |
| D5 | Euromonitor Passport is all-channel and brand-complete enough to anchor shares | Its stated methodology covers e-commerce, club and grocery; 10 consistent years | Medium | **High** | Partly | Cross-checked against Mintel channel weights and MULO; the three disagree, which is itself disclosed on the site |
| D6 | Passport's "Others" bucket is small brands, distributed like PDI's tail | No alternative source for sub-threshold brands | **Low** | Medium | No | 9.2% of 2025 value sits in this bucket. See **B6** |
| D7 | The Amazon scrape cannot measure share | Only four search terms (Celsius, Alani Nu, Ghost, Monster) | High | Low | **Yes** | Confirmed — Red Bull appears with 6 listings only because nobody searched it. Used qualitatively only |
| D8 | Mintel's market total and its spend-per-household are independently derived | Published as separate series | Medium | Medium | **Yes** | Dividing one by the other implies 128–135M US households across 7 years vs a Census count near 131–132M. Consistent |

---

## Business logic assumptions

| # | Assumption | Rationale | Confidence | Impact if wrong | Validated | Result |
|---|---|---|---|---|---|---|
| B1 | Nine audiences are the right cut of this category | Built from Simmons demographics (7 brands), published positioning (~35), product attributes (tail) | Medium | **High** | No | The cut is mine, not the data's. A different analyst could defensibly land on 7 or 11 |
| B2 | A brand maps to exactly one audience | Simplifies attribution; most brands do target one buyer | Medium | Medium | No | Known failure: Celsius runs ~50/50 male-female yet sits in "Women (fitness & wellness)" |
| B3 | Zero-sugar lines of mainstream brands sell to a different buyer than the sugared parent | Category evidence that sugar-free skews older and more female | **Low** | Medium | No | No measured data separates Monster Zero buyers from Monster buyers. Creates the "Calorie-cutters" segment entirely |
| B4 | Price band = average realised price over a SKU's life | Transaction data gives revenue ÷ units, not shelf tags | Medium | Medium | **Yes** | Disclosed on the page. These are positioning tiers, not observed price points |
| B5 | Price analysis must be restricted to singles | A multipack price ÷ single-can size invents a premium tier | High | **High** | **Yes** | Confirmed: the guard leaks $4,820 of $3.87B. Without it, 385 of 430 "premium" SKUs were multipacks |
| B6 | Passport's "Others" allocates across audiences in PDI proportion | PDI is the only source that sees the long tail | **Low** | Medium | No | Affects 9.2% of the 2025 split |
| B7 | Calorie-cutters can be carved out of Passport's brand totals using PDI's within-brand ratio | Passport is brand-level, so zero-sugar sits inside the parent brand | **Low** | Low | No | Small segment (3.4%); error is bounded |
| B8 | 860 raw flavor strings collapse to 15 families sensibly | First-match-wins regex, specific patterns ordered above broad ones | Medium | Medium | Partly | "Novelty & branded" was created after review — invented names (Frose Rose, Cosmic Stardust) are a real category, not a rules gap |
| B9 | An "active" SKU is one that sold within the last 6 months | Arbitrary but conventional | Medium | Low | No | Changes the 1,603 active / 706 discontinued split if moved |

---

## Statistical assumptions

| # | Assumption | Rationale | Confidence | Impact if wrong | Validated | Result |
|---|---|---|---|---|---|---|
| S1 | Mintel's $38.6B central 2030 forecast can be taken as given | It is a published forecast from a recognised source; we forecast the *split*, not the total | Medium | **High** | n/a | Its own 90% band is $30.0–47.2B. Every per-audience dollar scales with wherever the total lands |
| S2 | Audience share drifts approximately linearly, damped 15%/yr for saturation | Keeps trends from running to absurdity over five years | **Low** | **High** | **Yes — failed** | Back-tested (fit 2017–21, predict 2025): **mean absolute error 5.1pp**, with 9pp misses on both women and gym. Damping barely matters (6.2→4.8pp across the full range) — the problem is linear extrapolation of an S-curve |
| S3 | No structural break in the trend window | Standard extrapolation premise | **Low** | **High** | **Partly falsified** | The women's segment gains ran +2.4, +4.1, +2.9, **+1.0pp** — it is decelerating. The forecast implies 1.84pp/yr, 1.8× the last measured year. Now disclosed on both pages |
| S4 | Gamers & creators and Health-conscious adults are held at floors (1.6%, 0.9%) rather than trended | Both sell through e-commerce and natural grocery, invisible in PDI and MULO; trending from blind data drives them to zero | **Low** | Medium | No | Set by hand. Stated on the page rather than hidden |
| S5 | Flavor mix is invariant to channel | PDI is the only source that sees flavor, so the White Space grid lifts convenience flavor proportions to all-channel scale | **Low** | **High** | No | Plausibly wrong in the direction that matters — e-commerce skews to powders and hydration, which likely carry a different flavor mix entirely |
| S6 | Revenue per SKU is a fair proxy for "headroom" for a new entrant | High revenue per SKU means few products share the money | Medium | Medium | No | Ignores that incumbents' per-SKU revenue reflects brand strength, not an opening |
| S7 | The 2-year flavor-cell growth rates are signal, not noise | Used to rank white-space cells | **Low** | Medium | No | Some cells rest on very few SKUs — Women × Punch is 4 SKUs at +279% |

---

## Critical assumptions — unvalidated, high impact

These four decide the recommendation. If a reviewer challenges one thing, it should be here.

### S2 — the 15%/yr damping constant — **VALIDATED, AND IT FAILED**
The back-test has now been run: fit on 2017–2021, predict 2025, compare with the known answer.

| Audience | Predicted 2025 | Actual 2025 | Error |
|---|---|---|---|
| Young adults | 68.9% | 69.7% | −0.8pp |
| Women (fitness & wellness) | 3.1% | 12.1% | **−9.0pp** |
| Gym & fitness | 16.4% | 7.3% | **+9.1pp** |
| Shift workers & military | 0.0% | 1.6% | −1.6pp |
| **Mean absolute error** | | | **5.1pp** |

Damping is not the lever: MAE runs 6.2 / 5.1 / 4.8pp at damping 1.00 / 0.85 / 0.70. Both large
misses are **turning points** — the model under-shot women while that segment was accelerating,
and over-shot gym after it peaked and reversed.

**Consequence:** the 2030 women's figure of 22.4% carries roughly **±9pp of model error** on this
evidence, before Mintel's own $30.0–47.2B band is applied to the total. Direction matters too:
this model over-shoots after a turn, and the segment is now decelerating (**S3**), which puts
22.4% on the optimistic side. This is published on the comparison page.

### S3 — no structural break
**Status: already partly falsified.** The women's segment is decelerating and the forecast leans
against it.
**Validation plan:** re-check on the next Passport release. If the 2026 gain lands near +1.0pp
rather than +1.84pp, the projection needs rebuilding on a saturating curve rather than damped linear.

### S5 — flavor mix invariant to channel
**Risk:** the White Space Finder's dollar figures assume a 16 oz convenience flavor mix holds
in e-commerce, where the format is often a powder.
**Validation plan:** none available in-house. Would need a channel-resolved flavor source —
Circana or a retailer feed. Until then the grid should be read as a *convenience* map scaled up,
not an all-channel map.

### D1 — PDI store representativeness
**Risk:** every flavor, price and lifecycle finding rests on it.
**Validation plan:** compare PDI's implied category total against NACS convenience benchmarks.
Partially mitigated already by anchoring audience shares on Passport rather than PDI.

---

## Assumptions that changed a published number

| Was | Now | Why |
|---|---|---|
| Women 18.4% of 2025 demand | **13.2%** | Used Mintel MULO to stand in for all non-convenience sales; MULO is top-brands-only and over-weights Celsius and Alani Nu. Passport measures 12.1% |
| Women take 51% of growth to 2030 | **43.7%** | Follows from the above; now level with young adults rather than double |
| Price at $0.25–0.30/oz | **$2.50–2.99 per 16 oz can** | That per-ounce band is 79.5% 12 oz cans. On a 16 oz can it means $4.00–4.80, where 7 SKUs have ever earned $0.02M each |
| 2,309 unique products | **2,178** | 2,309 was the row count; 131 barcodes appear twice as brand-period splits |
| Women's trend "has not yet slowed" | Decelerating | Annual gains +2.4, +4.1, +2.9, +1.0pp |

---

## Sign-off

Not yet peer-reviewed. Before this analysis is presented as final, a reviewer should
specifically challenge **S2**, **S3**, **S5** and **D1**, and should run the S2 back-test —
it is the cheapest way to falsify the forecast and it needs no data we do not already hold.
