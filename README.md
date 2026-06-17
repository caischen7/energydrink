# ION® — LIQUID HARDWARE

A futuristic hydration brand where the product **is** the experience. The landing
page is built around one persistent, interactive 3D can instead of product
photography — every section is staged as a product reveal, styled like the
launch page of a consumer technology company.

![Hero — floating 3D can over oversized ION type](docs/hero.png)

## Concept

**ION** is structured hydration presented through crypto-native design language:

- **Boot sequence** — the site cold-boots like an operating system (`ION_OS v4.2.0`)
- **Genesis drop** — 10,000 serialized cans across three colorways (VOLT / VOID / GLACIER)
- **Hydronomics** — the formula presented as token distribution bars
- **Roadmap** — phases instead of features, `MINT_CAN` instead of "buy now"
- **OS chrome** — hairline grid overlays, mono telemetry, live FPS + protocol clock, film grain

One volt-green accent (`#c6ff00`) on near-black, ultra-expanded Archivo for the
oversized display type, Space Mono for telemetry.

## The 3D can

The can is **fully procedural** — no model files, no image assets:

- Geometry: a primitive stack (cylinders, tori, lathe-style tapers, pull tab)
- Labels: drawn at runtime onto `CanvasTexture`s (wordmark, specs, barcode,
  QR data block, serial) — one per colorway, repainted when webfonts arrive
- Lighting: PMREM-filtered `RoomEnvironment` IBL + volt rim light

### Interaction model

| Input | Reaction |
| --- | --- |
| Scroll | The can travels between per-section poses (position / tilt / scale / spin rate), eased in the render loop |
| Pointer move | Parallax tilt on the rig + camera |
| Drag (empty space) | Spin momentum with friction |
| Click the can | Squash-and-stretch pulse + emissive flash |
| Hover / scroll edition rows | Live colorway + label swap (VOLT-001, VOID-002, GLCR-003) |

Honors `prefers-reduced-motion`, clamps DPR at 2, pauses rendering in hidden
tabs, and degrades to a flat layout when WebGL is unavailable.

| The drop — live colorway swap | Join — final reveal |
| --- | --- |
| ![Genesis series editions](docs/drop.png) | ![Join the protocol](docs/join.png) |

## Stack

- [Vite](https://vitejs.dev) — dev server / build
- [three.js](https://threejs.org) — the vessel
- Self-hosted variable fonts via Fontsource (Archivo `wdth`, Space Grotesk, Space Mono)
- Zero animation libraries — reveals are IntersectionObserver + CSS, choreography is rAF

## Run

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # static build in dist/
npm run preview
```

## Deploy

Hosted on **Google Cloud Run** (landing page + dashboard in one service):

```bash
gcloud auth login
GCP_PROJECT=your-project-id ./deploy/deploy.sh
```

See [`docs/DEPLOY_GCP.md`](docs/DEPLOY_GCP.md) for the full guide (Cloud Shell
option, CI, costs). The `Dockerfile` builds the Vite site and serves it with
nginx; `gcloud run deploy --source .` builds the image on Cloud Build.

## Structure

```
index.html        page skeleton — hero, ticker, manifesto, specs, drop, protocol, join
src/main.js       entry: fonts, boot sequence, wiring
src/style.css     futuristic-OS design system
src/can.js        procedural can + canvas label textures (3 colorways)
src/scene.js      renderer, scroll choreography, pointer physics
src/fx.js         split-text reveals, counters, ticker, cursor, edition sync

dashboard.html    ION_INTEL — founder market-intelligence terminal
src/dashboard/    white-space finder, pricing/pain/brand views, concept builder
data/             cleaned Amazon + Instagram + YouTube datasets + build scripts
docs/advisory-board.md, docs/board-discussion.md   the 12-founder board + data roadmap
```

## Market Intelligence terminal

A second page, **`/dashboard.html`** (linked as `[05] INTEL` in the nav), turns
the cleaned datasets in `data/` into a founder tool for finding white space for a
new beverage:

- **White-space finder** — functional benefits ranked by consumer demand vs.
  catalog supply (e.g. *protein* and *gut health* show high pull, near-zero shelf)
- **Concept builder** — pick a functional angle, flavor, incumbent pain point and
  price band; it scores the combination and writes the one-line brief
- **Pricing arbitrage**, **pain → positioning**, and **share-of-voice** views
- Scoped by a simulated **12-founder advisory board** (`docs/`) that also voted a
  prioritized roadmap of data sources to acquire next

It reads one pre-aggregated file, `public/market_intel.json`, built by
`python data/scripts/build_dashboard_data.py`.

---

*ION BEVERAGE SYSTEMS © 2086 — not financial advice. Just water, evolved.*
