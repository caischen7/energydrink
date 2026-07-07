# Bogus Banana — Ridiculously Good Energy

A fictional energy-drink brand built as three connected things in one repo:

1. **The landing page** — a single-page marketing site staged around one
   persistent, interactive, fully procedural 3D can (Vite + three.js, no
   framework, no model files).
2. **The market research pipeline** ([`data/`](data/)) — cleaned datasets and
   free, self-run scrapers covering Amazon, Walmart, 7 grocery/big-box
   retailers, Instagram, TikTok, YouTube, Reddit, and the Meta Ad Library.
3. **The Market Intel dashboard** ([`dashboard.html`](dashboard.html)) — a
   login-gated analytics terminal that turns the research corpus into 14
   chart panels.

![Hero — floating 3D can over oversized type](docs/hero.png)

## Concept

**Bogus Banana** is "ridiculously good energy" — a banana-electrolyte energy
drink presented like the launch page of a consumer-technology company:

- **Boot sequence** — the site cold-boots like an operating system on first visit
- **The drop** — serialized cans across three editions:
  `BB-01 ORIGINAL` / `BB-02 MIDNIGHT BERRY` / `BB-03 FROZEN BANANA`
- **OS chrome** — hairline grids, mono telemetry, live FPS + clock readouts

**Design:** a playful banana identity sampled from the can — banana-cream
field (`#fff6df`), peel-yellow bands (`#ffd23f`), mascot red-orange accent
(`#ef4a23`), and a midnight-berry close (`#421a39`). Chunky expanded Archivo
display type, Space Grotesk body, Space Mono telemetry; the 3D can is the hero.

## The 3D can

The can is **fully procedural** — no model files, no image assets:

- Geometry: a primitive stack (cylinders, tori, lathe-style tapers, pull tab)
- Labels: drawn at runtime onto `CanvasTexture`s (wordmark, specs, barcode,
  QR data block, serial) — one per colorway, repainted when webfonts arrive
- Lighting: PMREM-filtered `RoomEnvironment` IBL + rim light

### Interaction model

| Input | Reaction |
| --- | --- |
| Scroll | The can travels between per-section poses (position / tilt / scale / spin rate), eased in the render loop |
| Pointer move | Parallax tilt on the rig + camera |
| Drag (empty space) | Spin momentum with friction |
| Click the can | Squash-and-stretch pulse + emissive flash |
| Hover / scroll edition rows | Live colorway + label swap (BB-01 / BB-02 / BB-03) |

Honors `prefers-reduced-motion`, clamps DPR at 2, pauses rendering in hidden
tabs, and degrades to a flat layout when WebGL is unavailable.

| The drop — live colorway swap | Join — final reveal |
| --- | --- |
| ![Editions](docs/drop.png) | ![Join](docs/join.png) |

## Stack

- [Vite](https://vitejs.dev) — dev server / build
- [three.js](https://threejs.org) — the vessel
- Self-hosted Archivo + Space Grotesk + Space Mono via Fontsource
- Zero animation libraries — reveals are IntersectionObserver + CSS, choreography is rAF

## Run

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # static build in dist/
npm run preview
```

There is no test runner or linter for the site; the data pipeline has offline
fixture tests (see below).

## Deploy

Containerized for **Google Cloud Run** (`Dockerfile` + `deploy.sh`):

```bash
GCP_PROJECT=your-project-id ./deploy.sh   # Cloud Build → public Cloud Run URL
```

See [`docs/DEPLOY.md`](docs/DEPLOY.md) for prerequisites and the managed
Google-Cloud-integration path. Deploy from the **default branch or `main`**
(they are kept in sync).

## Data & scrapers

[`data/`](data/) holds the cleaned market-research corpus (Amazon products +
reviews, Instagram posts, 3,214 YouTube videos + 125,054 comments, Reddit
brand pulse, Mintel/Statista market facts, cross-platform brand summaries) and
**eight free, self-run scrapers** in [`data/scripts/`](data/scripts/):

| Script | Source | Free path |
| --- | --- | --- |
| `scrape_amazon.py` | Amazon products + reviews | Playwright browser |
| `scrape_walmart.py` | Walmart products + reviews | Playwright browser (SerpAPI optional) |
| `scrape_retailers.py` | Target, Trader Joe's, Publix, H-E-B, Costco, Whole Foods, Kroger | Playwright browser; Kroger via its official free API |
| `scrape_instagram.py` | Brand-account posts | instaloader |
| `scrape_tiktok.py` | Brand accounts + hashtag pages (views/likes/shares) | Playwright browser |
| `scrape_facebook.py` | Meta **Ad Library** — brand ad copy, platforms, campaign dates | Playwright browser (public, no login) |
| `scrape_youtube.py` | Videos + comments | Official YouTube Data API (free key) or yt-dlp |
| `scrape_reddit.py` | r/EnergyDrinks posts + comment trees | Public JSON endpoints (stdlib) |

All scrapers share the same conventions: output schemas match the committed
CSVs, runs are **incremental** (merge + dedupe on natural keys), polite
rate-limiting, clear `BLOCKED:` errors, and offline fixture tests in
[`data/scripts/tests/`](data/scripts/tests/). Scrapers run from your own
machine (residential IP) — retailer/social bot-walls block cloud IPs.

**One command runs them all:** `python data/scripts/run_all.py` drives every
scraper in order (API/no-bot sources first, browser ones last), keeps going if
one fails, and prints a summary. Add `--headless` for hands-off runs once
you've solved each site's challenge a first time, `--light` for a quick test,
`--only`/`--skip` to choose sources, `--build` to rebuild the dashboard after.
Full docs: [`data/README.md`](data/README.md).

## Market Intel dashboard

A second page — [`dashboard.html`](dashboard.html), linked from the nav as
**MARKET INTEL** — turns the cleaned research in [`data/`](data/) into an
analytics terminal across 14 panels: **market size** ($98B → $107B forecast,
Statista), **concept interest** (Mintel — what consumers want to try),
**why-they-drink motivations** (Mintel), share of voice, **brand momentum**
(trailing-12-mo trend lines), a **rising/cooling leaderboard**, category
momentum, an Amazon price × quality map, a **flavor demand board**, review
ratings, Instagram engagement, a **Reddit community pulse**, a
**loves-vs-complaints sentiment** breakdown mined across **125K+ comments**,
and a sortable 23-brand cross-platform matrix. Hand-rolled SVG charts, no
charting library.

**Trend-spotting & credibility (Momentum pass).** The dashboard answers *who's
moving*, not just *who's big*: per-brand monthly **mention-share** is normalized
for the growing corpus, smoothed over trailing-12-month windows, and the partial
final scrape month is excluded so trends don't show a false cliff. Share of voice
uses **fractional attribution** (a video's views split across the brands it names)
and strips music/entertainment false-matches — ~1.2B phantom views (e.g. Eminem's
*"The Monster"*, which had inflated Monster Energy ~10×) are removed, so Red Bull
and Monster correctly land neck-and-neck.

The numbers come from a precomputed aggregate, `public/data/dashboard.json`
(~20 KB) — served as a standalone file (not bundled) so nginx can guard it with
Basic Auth — built from the cleaned CSVs by:

```bash
pip install vaderSentiment            # optional — enables real sentiment (else a lexicon fallback)
python data/scripts/build_dashboard_json.py   # reduces 129K+ records → one small JSON
```

The **external sources** (market size, Mintel survey, Reddit) are cleaned by a
separate step into `data/market/` and `data/reddit/` (the raw corpus — Mintel /
Catalyst `.xlsx`, Reddit dumps — is **not** committed, per repo convention):

```bash
pip install openpyxl vaderSentiment
RAW_DATA_DIR=/path/to/raw python data/scripts/build_external_datasets.py
python data/scripts/build_dashboard_json.py   # folds them into the aggregate
```

Nothing large is shipped to the browser — the 25 MB comment corpus is reduced
to theme/momentum/flavor/sentiment aggregates at build time. Regenerate the
JSON after the data changes.

### Dashboard login

The dashboard is reachable via the **MARKET INTEL ↗** link in the landing-page
top bar or directly at `/dashboard.html`, and opens behind a styled login —
username `energydrinks`, password `energydrinks12345`.

**This is enforced server-side, not just cosmetically.** The dashboard's data
(`/data/dashboard.json`) is served behind **nginx HTTP Basic Auth** (`.htpasswd`),
and the login form fetches it with the entered credentials. So the licensed
Mintel/Statista figures are never sent without valid credentials — bypassing the
JS check in devtools just yields an empty shell. (Locally via `npm run dev` there's
no nginx, so the client-side check alone gates it; the real enforcement is on the
deployed nginx / Cloud Run.)

To change the credentials, update **both** (see [`docs/CREDENTIALS.md`](docs/CREDENTIALS.md)):

```bash
# 1) server (Basic Auth) — the real gate:
htpasswd -bc .htpasswd energydrinks 'NEWPASS'     # or: openssl passwd -apr1
# 2) client check (instant UX / local dev) — PASS_HASH in src/auth.js:
printf '%s' 'NEWPASS' | sha256sum
```

### Waitlist capture

The landing-page join form persists signups (deduped, with UTM + referrer) to
`localStorage`. To forward them to a real backend/ESP, set a build-time env
var — the form then POSTs each record as JSON and still stores it locally as a
fallback:

```bash
VITE_WAITLIST_ENDPOINT=https://your-endpoint.example/subscribe npm run build
```

## Structure

```
index.html                 landing skeleton — hero, ticker, manifesto, specs, drop, protocol, join
dashboard.html             market-intel terminal (charts + brand matrix)
src/main.js                entry: fonts, boot sequence, wiring
src/style.css              playful banana design system — cream/peel/zest/plum (shared by both pages)
src/can.js                 procedural can + canvas label textures (3 colorways)
src/scene.js               renderer, scroll choreography, pointer physics
src/fx.js                  split-text reveals, counters, ticker, cursor, edition sync
src/auth.js                dashboard login (client check + Basic-Auth fetch)
src/dashboard.js           dashboard: panels, sortable table, count-up, scroll reveals
src/dashboard.css          dashboard layout + chart styling (imports style.css)
src/charts.js              dependency-free SVG chart builders (bars, scatter, area)
public/data/dashboard.json precomputed aggregate consumed by the dashboard
data/                      cleaned datasets + scrapers + build scripts (see data/README.md)
```

## Project status

- **Deploy:** containerized for **Google Cloud Run** — `./deploy.sh` →
  service `ion-liquid-hardware`. See [`docs/DEPLOY.md`](docs/DEPLOY.md)
  (deploy from Google Cloud Shell; this repo is private so authenticate first).
- **Delivered:** the data-driven concept work shipped as the **Bogus Banana**
  rebrand (banana-electrolyte positioning, three editions).
- **In progress:** first-party data collection with the free scrapers above —
  run them locally, commit the CSVs, regenerate the dashboard aggregate.

**Working on this with an AI agent?** Current state and exact next steps live
in **[`CLAUDE.md`](CLAUDE.md)** → "Status & handoff". Note: the raw research
corpus is **not committed** (size + PII), so re-upload it in a new session to
reprocess the external sources.

---

*BOGUS BANANA CO © 2026 — ridiculously good energy. Not medical advice.*
