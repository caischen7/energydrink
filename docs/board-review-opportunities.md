# Board review — finding opportunities, not just describing the market

A working session reviewing the live ION_INTEL dashboard (`dashboard.html`) and
deciding what to build next. Same simulated-board format as the original data
roadmap, refreshed with a tighter group for a fast, focused decision.

**Panel:**
- **Dana Whitfield** — board director, former CMO of a national beverage co.;
  reviews from a "what would make me fund this" lens.
- **Marcus Oyelaran** — founder, two prior beverage exits; reviews from "what
  would I actually use to pick my next SKU" lens.
- **Priya Subramaniam** — VP Insights at a CPG manufacturer; reviews from a
  data-rigor / "where would a real shopper-insights team push back" lens.
- **Tom Reyes** — growth/data engineer, advises on what's actually buildable
  with the data and time available tonight.

## What's on the dashboard today

13 panels: market size, concept interest, motivations, share of voice, brand
momentum, rising/cooling, price×quality, category momentum, flavor demand,
review ratings, IG engagement, Reddit pulse, loves-vs-complaints sentiment —
plus a sortable 23-brand matrix. All of it is **descriptive**: it tells you
what's happening. None of it directly answers *where's the open space*.

**Marcus:** "This is a great briefing book. It is not a tool. I can't open
this and walk away with 'build X, here's why, here's the math.' Every panel
answers 'what already exists' — none of them rank a gap."

**Dana:** agrees, adds that two panels are *already* halfway to an opportunity
signal and just aren't framed that way: **Flavor Demand Board** has both
mentions (demand) and `products` (supply) per flavor, and **Loves vs
Complaints** has per-theme negative-sentiment rates (an unmet-need signal).
"You're sitting on a white-space score and not computing it."

**Priya:** the thing missing for a CPG buyer specifically is **formulation** —
caffeine/sugar/calories per brand. "I can't tell from this dashboard whether
the open space is a flavor gap or a *spec* gap (e.g. high-caffeine zero-sugar
is crowded; high-caffeine + zero-sugar + electrolytes might not be)." Also
flags that the market panel has category totals but no **brand-level dollar
share** — can't tell if a flavor gap is in a market a challenger could
actually take share in, or one the incumbents already own by distribution.

**Tom:** on "create new scrapers" — pushes back on naive interpretation.
TikTok has no public metrics API and scraping it violates its ToS even for
research use; not worth the legal exposure for marginal signal. Two
*legitimate*, dual-use-safe sources do the same job better:
- **Google Trends** (`pytrends`, public, ToS-compliant) — real consumer
  *search* demand, which is a cleaner "do people want this" signal than
  YouTube mention-share (mentions can spike from a single viral video; search
  volume is closer to actual consumer intent).
- **SEC EDGAR** (public company filings, free JSON API, fully legitimate) —
  Celsius (CELH) and Monster Beverage (MNST) file real quarterly revenue.
  That's a much harder, citable signal for "is this segment still growing"
  than anything scraped.

## Decision — three things to build tonight

1. **Opportunity Finder** (new panel, *zero new data needed*) — combine
   `flavor_demand` (demand=mentions, supply=products) and
   `voice_of_customer` (negative-sentiment rate = unmet need) into one ranked
   white-space score, displayed as a demand-vs-supply bubble chart plus a
   ranked list. This is the single highest-leverage build: it directly turns
   two existing-but-unused columns into the "where's the opportunity" answer
   Marcus asked for.
2. **Formulation Map** (new panel + new curated data) — caffeine/sugar/
   calories per brand (public label values, cited), plotted as a scatter with
   the "crowded spec" zone shaded, so a buyer can see which caffeine×sugar
   combination is open. Ships with a runnable Open Food Facts loader for
   anyone who wants to extend it per-SKU later.
3. **Competitive $ Share + TAM math** (new panel + new curated data) — real
   US dollar market share by brand (cited, sourced via web search same as the
   category-size figure already in the repo) layered onto the existing
   `market.size`/`market.facts` category data, so a flavor/spec gap can be
   sized in real dollars, not just "more mentions." Ships with a runnable SEC
   EDGAR loader (Celsius + Monster quarterly revenue) for a forward-looking
   growth check.

**Not building tonight:** a TikTok scraper (ToS risk, no real upside over
what Google Trends + SEC EDGAR give us), and a live Reddit re-scrape (the
existing snapshot is a one-time corpus upload, not an API — re-running it
needs the raw export, which isn't something this session can fetch
unattended).

Loaders for Google Trends and SEC EDGAR are shipped runnable but **not**
wired into tonight's build — they need outbound network this environment
doesn't have. Wiring them in is the natural next step once someone runs them
with real network access (see `data/README.md`).
