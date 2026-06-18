# CLAUDE.md

Guidance for Claude Code (and other agents) working in this repository.

## What this repo is

Two loosely-related things live here:

1. **`ION® — Liquid Hardware`** — a single-page marketing site for a fictional
   futuristic hydration brand, built around one persistent, procedurally-generated
   interactive 3D can (Vite + three.js, no framework). This is what `npm run dev`
   builds and what `index.html` / `src/` contain.
2. **Energy-drink market data** (`data/`) — cleaned CSV datasets scraped from
   Amazon, Instagram, and YouTube, plus a Python script that regenerates them.
   This is a separate data-analysis artifact and is **not** wired into the website.

When a task mentions "the site", "the can", "the landing page" → work in `src/` +
`index.html`. When it mentions "the data", "datasets", "brands", "scraping" → work
in `data/`.

## Commands

### Website (root)
```bash
npm install
npm run dev      # Vite dev server → http://localhost:5173
npm run build    # static build → dist/
npm run preview  # serve the built dist/
```
There is **no test runner, linter, or formatter configured**. Don't assume
`npm test`/`npm run lint` exist — they don't. Verify changes by running the dev
server and exercising the page.

### Data pipeline (`data/`)
```bash
pip install pandas openpyxl
RAW_DATA_DIR=/path/to/unzipped/raw/data python data/scripts/build_clean_datasets.py
```
Raw scraper exports are **not committed** (large/messy); only the cleaned CSVs are.
`RAW_DATA_DIR` must contain `Amazon data/`, `Instagram data/`, `Youtube data/`.
See `data/README.md` for the full schema and cleaning notes.

## Website architecture

Entry point is `src/main.js`, loaded as a module from `index.html`. It runs the
boot sequence, then wires up two independent layers:

| File | Responsibility |
| --- | --- |
| `src/main.js` | Entry: imports fonts + CSS, runs the `ION_OS` boot overlay, dynamically imports `scene.js` (so a WebGL failure degrades gracefully), calls `initFx`. |
| `src/scene.js` | The **WebGL layer**. One persistent three.js scene. Choreographs the can against scroll using per-section `POSES`, plus pointer parallax, drag-spin momentum, float bob, click pulse, FPS reporting. Exposes `setColorway / pulse / refresh / redrawLabels / onColorway / onFps`. |
| `src/can.js` | The **procedural can**. Geometry is a primitive stack (cylinders/tori/circles + pull tab). Labels are drawn at runtime onto `CanvasTexture`s — one per colorway (`volt` / `void` / `glacier`) defined in `COLORWAYS`. No model files, no image assets. |
| `src/fx.js` | The **DOM layer**. Split-word headline reveals, IntersectionObserver fade-ups, count-up stats, marquee ticker, custom cursor, `body[data-section]` scroll tracking, the edition-row ↔ 3D colorway sync, the header FPS/clock readout, and the fake "mint" form. No animation libraries. |
| `src/style.css` | The futuristic-OS design system (CSS custom properties, grid overlays, telemetry styling, reduced-motion + no-WebGL fallbacks). |
| `index.html` | Static page skeleton — sections in order: `hero`, `manifesto`, `specs`, `drop`, `protocol`, `join`. |

### How the two layers talk
`scene.js` and `fx.js` don't import each other. `main.js` passes the `scene`
handle into `initFx(scene)`, and `fx.js` calls `scene.setColorway(...)` /
`scene.onColorway(...)` / `scene.onFps(...)`. If WebGL is unavailable, `scene`
is `null` and `fx.js` no-ops the 3D hooks while the DOM layer still works.

### Things that will bite you
- **Section order is duplicated** in `src/scene.js` (`SECTIONS`) and `src/fx.js`
  (`SECTION_IDS`) and must match the `id`s in `index.html`. Change one → change all.
- **Colorways** are the source of truth in `can.js` (`COLORWAYS`: `volt`, `void`,
  `glacier`). The editions in `index.html` reference them via
  `.edition[data-colorway="..."]`, and `fx.js` has a parallel `EDITION_HUD` map.
- **Fonts load late.** Canvas labels are first drawn before webfonts arrive, then
  repainted via `scene.redrawLabels()` on `document.fonts.ready`. Section offsets
  are re-measured (`scene.refresh()`) for the same reason — don't remove these.
- **Accessibility / perf are intentional:** honors `prefers-reduced-motion`, clamps
  DPR at 2, pauses the rAF loop in hidden tabs (`visibilitychange`), and degrades to
  a flat layout when WebGL is missing. Preserve these when editing the render loop.
- The boot overlay only plays in full once per session (`sessionStorage`
  `ion-booted`); it short-circuits on repeat visits and under reduced motion.

### Conventions
- Vanilla ES modules, no framework, no build step beyond Vite. No TypeScript.
- 2-space indentation; `const $ = (s) => document.querySelector(s)` style helpers.
- `vite.config.js` sets `base: './'` so the static build works from any subpath
  (e.g. GitHub Pages) — keep asset references relative.
- Brand voice in copy is crypto/OS-native ("MINT_CAN", "the ledger", `© 2086`).
  Match it when editing visible text.

## Git / workflow

- Commit and push only when the work is complete and the user has asked for it.
- Don't commit `node_modules/`, `dist/`, or `.vite/` (already in `.gitignore`).
- Raw scraper data stays out of the repo — only regenerated CSVs under `data/`
  are tracked.
