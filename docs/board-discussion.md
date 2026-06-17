# Board working session — "What should the opportunity tool do?"

*Transcript of the kickoff session. The board was shown the first cut of the
Market Intelligence dashboard, built on the Amazon + Instagram + YouTube data we
have today (75 products, 552 reviews, 120 social posts, 3,214 videos, 125,054
comments across 23 brands). Goal: agree what the tool helps a founder decide,
and what data we still need.*

---

## 1. What the data is already telling us

**Andre (data):** Before anyone gets excited — let's be clear what this is. We
have *attention and sentiment* data (social + reviews), not *sales* data. So the
tool is a **demand-signal and white-space finder**, not a revenue forecaster.
Within that, the signal is strong. The cleanest finding: huge gaps between what
consumers talk about and what the shelf actually offers.

**Maya (better-for-you):** The protein number jumps out — 1,600+ mentions, three
products. That's the single widest gap in the catalog. People are clearly asking
"why isn't this also protein," and almost nobody answers.

**Tariq (hydration):** Same story for electrolytes/hydration — over a thousand
mentions, ~13% of the shelf. Energy and hydration are converging and the
incumbents are slow.

**Dev (gut health):** And gut health is the purest white space on the board:
~450 mentions, *zero* products positioning on it. That's the Olipop/Poppi
playbook arriving in energy. If the tool does nothing else, surfacing
zero-supply / high-demand cells is the killer feature.

**Sofia (nootropic):** I'd add nuance — "focus" mentions are inflated by people
describing the *effect* of caffeine, not asking for nootropics specifically. The
tool should let me read the actual quotes behind a number, or I won't trust it.

> **Decision:** every metric in the tool must be *drillable to source quotes.*
> A number with no evidence behind it is a liability.

---

## 2. Where the board pushed back on the tool

**Priya (brand):** White space in *formulation* is only half a business. The
pain-point list is the gold here — "tastes artificial," "too sweet," "crash,"
"feels addictive." That's not a formula gap, that's **copy**. I want a view that
turns complaints about incumbents into positioning angles. Give me the language
consumers already use so I can put it on the can.

**Grace (gaming):** And segment it. "The market" doesn't exist — gamers,
gym-goers, and wellness moms want opposite things. The YouTube data has search
queries and segments; the tool flattens them today. I want to filter every gap
by audience.

**Jordan (women's wellness):** Agreed. Alani didn't win on formula, it won on
*who it was for*. Share-of-voice by brand is useful, but I want share-of-voice by
**audience** and by **platform** — TikTok vs Instagram vs YouTube behave nothing
alike.

**Marcus (protein RTD):** Careful with the protein hype, though. Protein + acid +
carbonation is a formulation nightmare and a cold-chain question. The tool should
flag *feasibility*, not just demand. A "hard to make" white space is still worth
knowing, but label it.

**Helena (adaptogens):** My whole category — adaptogens, calm energy — barely
registers in mention counts because consumers don't know the words yet. Low
mention volume isn't low opportunity; it can be an *early* opportunity. The tool
shouldn't punish nascent language. Maybe show trend/velocity, not just volume.

---

## 3. The reality check

**Sam (distribution):** Everything here is consumer chatter. None of it tells me
whether a SKU actually *sells through* on a shelf. A drink can have a million
TikToks and rot in the cooler. Before I'd greenlight, I need velocity per point
of distribution and where these brands physically are. The tool is a great
*hypothesis generator* — it is not yet a *go decision*.

**Nina (investor):** From a capital lens: show me price architecture against
ratings. If the dashboard can point to a price band that's crowded at the bottom
and thin at the premium end — with quality complaints in the crowded band — that's
an arbitrage I can underwrite. The pricing scatter is the most investor-legible
view you have. Lead with it.

**Andre:** And we should be honest about scrape bias. Amazon over-indexes the
big subscribe-and-save brands; YouTube over-indexes review channels. The tool
must show *which platform* a signal came from so nobody mistakes "loud on
YouTube" for "big in market."

---

## 4. What we agreed the tool should do (v1 requirements)

1. **White-space finder** — rank functional attributes by demand-vs-supply gap;
   surface zero-supply/high-demand cells loudly. ✅ *built*
2. **Pain → positioning** — rank consumer complaints about incumbents with the
   real quotes, framed as copy angles. ✅ *built*
3. **Pricing arbitrage** — price vs rating scatter with band density, to find the
   thin premium / crowded value zones. ✅ *built*
4. **Brand leaderboard / share of voice** — who owns attention, by platform. ✅ *built*
5. **Flavor demand vs supply** — which flavors are over- and under-served. ✅ *built*
6. **Evidence drill-down** — every figure links to sample source text. ✅ *built (quotes on cards)*
7. **Audience/segment filters** — *backlog, needs richer segment tagging.*
8. **Trend/velocity over time** — *backlog, needs time-series collection.*

---

## 5. Data the board wants next (prioritized roadmap)

Ranked by the board's vote on *impact ÷ effort*:

| Priority | Data source | Why the board wants it | Champion |
|---|---|---|---|
| **P0** | **Retail sales & velocity** (SPINS / NielsenIQ / IRI, or Amazon BSR over time) | Converts "demand signal" into "does it sell." The single biggest gap. | Sam, Nina |
| **P0** | **Nutrition / ingredient panels** (per SKU: caffeine mg, sugar g, calories, protein g, key actives) | Lets the tool reason about real formulation gaps & feasibility, not just words. | Maya, Marcus, Andre |
| **P1** | **TikTok** (posts, sounds, hashtags, view/like velocity) | Where the category actually breaks out now; YouTube/IG miss it. | Grace, Jordan, Priya |
| **P1** | **Time-series / trend data** (mentions & ratings by week) | Distinguish nascent (Helena's adaptogens) from dying; show momentum. | Helena, Sofia |
| **P1** | **Audience/segment tags** on social + reviews (gamer, gym, wellness, student, parent) | Make every gap filterable by who wants it. | Grace, Jordan |
| **P2** | **Retail pricing & promo** (shelf price by channel, $/serving, promo depth) | True price architecture & margin, vs Amazon multipack noise. | Nina, Sam |
| **P2** | **Reddit & review long-form** (r/energydrinks, Amazon 1–3★ deep dives) | Highest-signal complaints & DIY "I wish it had…" requests. | Sofia, Priya |
| **P2** | **Google/Amazon search volume** (keyword demand & trend) | Leading indicator of demand before social catches up. | Andre, Dev |
| **P3** | **Distribution footprint** (which retailers carry which SKU) | Whitespace by *channel*, not just by attribute. | Sam |
| **P3** | **Ad spend / SOV paid** (Meta/YouTube ad library) | Separate organic love from bought attention. | Priya, Andre |

---

## 6. Closing positions

- **Maya:** "Lead the founder to *protein energy that doesn't taste like chalk* —
  the gap is real, just flag the formulation difficulty."
- **Dev:** "Gut-health energy is the cleanest zero-supply white space on the
  board. First mover wins the word."
- **Nina:** "I'll fund whoever can pair a top-3 white space with a thin premium
  price band and a pain point to name the brand after. The tool can show all
  three on one screen — so show them on one screen."
- **Sam:** "Great hypotheses. Now go get me sell-through data before we bet a
  production run on it."
- **Andre:** "Ship v1 as a *hypothesis generator*, label the bias, and make every
  number clickable to its evidence. Then we earn the right to add sales data."

*Consensus: the dashboard ships as a white-space hypothesis generator built on
the data we have, with the P0 items (retail velocity + nutrition panels) as the
next acquisition targets.*
