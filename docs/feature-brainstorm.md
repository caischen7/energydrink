# Founders × VC session — "What features make this tool fundable-grade?"

*Second working session. The advisory board (see `advisory-board.md`) is joined
by three investors to brainstorm features that turn the white-space finder into
a tool a founder could actually raise and build on. Features were chosen for
(a) decision value and (b) buildability on the data we have plus the new
nutrition / market sources.*

## Who joined (investors)

| VC | Firm | Thesis |
|----|------|--------|
| **Nina Patel** | Northstar CPG | Operator-investor, seed→C beverage |
| **Walt Brennan** | Cold Start Capital | Pre-seed CPG; obsessed with "why now" + velocity |
| **Yuki Tanaka** | Aperture Ventures | Functional-health & ingredient-led brands |

## The asks that became features

**Walt (pre-seed):** "Every deck claims a white space. Show me **momentum** —
is the conversation about this angle *accelerating*? A flat line is a no."
→ **Momentum Explorer**: monthly mention volume per brand from our own
YouTube/Amazon/Instagram timestamps, with the fastest riser flagged. (Google
Trends loader ships for the true search-interest upgrade.)

**Yuki (functional):** "Words like 'protein' are cheap. Put it on the
**formulation map** — caffeine vs sugar vs the actual claim. The real white space
is a *spec*, not a vibe. Where's high-caffeine + zero-sugar + a function nobody
ships?" → **Formulation Analyzer**: every flagship plotted by caffeine/oz and
sugar, with the unserved functional quadrant called out.

**Nina (operator-investor):** "I underwrite a **number**. Anchor the white space
to category size and a defensible share, with sources I can check." → **Market
Sizing / TAM**: real US market size + dollar-share, plus an interactive
TAM→SAM→SOM calculator tied to a chosen white space.

**Maya / Dev (founders):** "Keep the **concept builder** — but let these new
views feed it. If I pick 'gut-health' I want to see its momentum, its
formulation gap, and its slice of the TAM on one screen." → integration: the
three new features sit alongside the existing builder and share the same data.

**Grace (gaming):** "Segment eventually — but ship the momentum line first; even
unsegmented it kills flat ideas." → noted; segment tags stay on the roadmap.

## Agreed feature set (this release)

1. **Formulation Analyzer** — caffeine × sugar map of every brand's flagship,
   with the "high-caffeine / zero-sugar / unmet-function" white space. *(new
   nutrition data)*
2. **Momentum Explorer** — 41-month mention-volume trend per brand, fastest
   riser flagged. *(our own timestamps)*
3. **Market Sizing / TAM** — real US size + share, interactive TAM calculator.
   *(new market-context data, sourced)*

Built in parallel by a small **team of agents**, each owning one self-contained
module, then integrated into the dashboard.

## Data the investors still want (added to the roadmap)

- **Velocity / sell-through** (Keepa Amazon BSR history is the cheap proxy) — Walt
  & Nina, still the #1 gap.
- **Per-SKU nutrition at scale** (Open Food Facts loader shipped) — Yuki.
- **Search interest** (Google Trends loader shipped) — Walt.
- **Reddit "I wish it had…"** (loader shipped) — Sofia, Priya.
