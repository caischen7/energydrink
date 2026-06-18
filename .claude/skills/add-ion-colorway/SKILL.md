---
name: add-ion-colorway
description: >-
  Use when adding, removing, or editing a colorway / edition on the ION 3D can —
  e.g. a new can color, flavor, serial run, or limited "drop" edition. Covers the
  synchronized edits across src/can.js (COLORWAYS), index.html (.edition rows +
  hero HUD), and src/fx.js (EDITION_HUD), plus how to verify the swap in the
  running site.
---

# Add or update an ION can colorway

A "colorway" is one of the can's interchangeable skins (`volt` / `void` /
`glacier`). It is **not** defined in a single place — the same colorway must be
declared in three files that don't import each other. Miss one and the can,
the edition list, and the hero HUD drift out of sync (e.g. the label paints but
the row never highlights, or the HUD shows the wrong serial).

## The source of truth

`src/can.js` → the `COLORWAYS` object is canonical. Each entry drives the
procedurally-drawn `CanvasTexture` label for that can:

```js
volt: {
  bg: '#c6ff00',      // label background
  ink: '#0a0a0a',     // primary text / barcode / QR
  accent: '#0a0a0a',  // accent bar + edition strap
  dim: 'rgba(10,10,10,0.55)', // secondary text
  metal: 0xd8d8d8,    // can body metal tint (THREE hex int)
  flash: 0xc6ff00,    // emissive flash color on swap/tap (THREE hex int)
  label: 'VOLT-001',  // edition id shown on the label + HUD
  flavor: 'CITRUS STATIC',
  serial: 'Nº 000001 / 10000',
}
```

The key (`volt`) is the colorway **name** used everywhere else.

## Steps to add a colorway

Use a new lowercase key, e.g. `ember`. Keep all three edits consistent.

1. **`src/can.js` — add to `COLORWAYS`.** Copy an existing entry and set every
   field. `metal` and `flash` are three.js hex integers (`0xRRGGBB`); the rest
   are CSS color strings. The label is redrawn from these values, so contrast
   matters (`ink`/`dim` must read against `bg`).

2. **`index.html` — add an `.edition` row** inside `<ul class="editions">` in the
   `#drop` section. The `data-colorway` attribute **must equal the new key**:

   ```html
   <li class="edition reveal" data-colorway="ember" data-hover tabindex="0">
     <span class="ed-id mono">EMBR-004</span>
     <span class="ed-name">SOLAR&nbsp;FLARE</span>
     <span class="ed-rarity mono"><i class="tag">RARE</i></span>
     <span class="ed-supply mono">1,000&nbsp;MINTED</span>
     <span class="ed-status mono dim">○ LOCKED</span>
   </li>
   ```

3. **`src/fx.js` — add to the `EDITION_HUD` map.** This is the string shown in the
   hero readout (`#hud-edition`) when the colorway is active:

   ```js
   const EDITION_HUD = {
     volt: 'VOLT-001 / 10000',
     // ...
     ember: 'EMBR-004 / 01000',
   };
   ```

## Things that will bite you

- **The key must match in all three places** (`COLORWAYS` key ⇄
  `.edition[data-colorway]` ⇄ `EDITION_HUD` key). `fx.js` reads the row's
  `data-colorway` and calls `scene.setColorway(name)`, which looks the name up in
  `COLORWAYS`. A typo silently no-ops the swap.
- **`fx.js` resets to `volt`** when you scroll back above the drop section, and
  `reflect('volt')` runs on init — so `volt` must always exist as the genesis
  default. Don't rename or remove it without updating `initEditions`/`initFx`.
- **`metal` / `flash` are integers, not strings.** `0xc6ff00`, not `'#c6ff00'`.
- Labels are drawn before webfonts load, then repainted via
  `scene.redrawLabels()` on `document.fonts.ready` — you don't need to trigger
  this, but don't remove it.

## Removing or editing a colorway

- **Edit:** change the values in `COLORWAYS`; if you change `label`/`serial`,
  update the matching `.edition` row text and `EDITION_HUD` string too.
- **Remove:** delete from all three places. Never remove `volt` (the default).

## Verify

There is no test runner. Verify by eye in the dev server:

```bash
npm run dev   # http://localhost:5173
```

Then in the running page:
1. Scroll to **THE DROP** (`#drop`). Hover/focus the new edition row → the can's
   label should swap to the new colorway, the body metal tint should change, and
   you should see a brief emissive flash.
2. The hovered row should get the `.active` class (highlight), and the hero HUD
   (`#hud-edition`, top of page) should show the new `EDITION_HUD` string.
3. Scroll above the drop and back → confirm it resets to `volt` then re-detects
   on scroll.
