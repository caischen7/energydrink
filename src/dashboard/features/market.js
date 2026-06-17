// Market Sizing / TAM feature for ION_INTEL.
// Self-contained: builds its DOM into a host-provided empty <div>, injects its
// own scoped (.mk-*) <style>, and wires a live TAM->SAM->SOM calculator.
// No libraries, no imports. The host renders meta.title / meta.blurb above us.

export const meta = {
  id: 'market',
  navLabel: 'TAM',
  title: 'Market sizing',
  blurb: 'Real US category size and dollar-share, plus an interactive TAM→SAM→SOM calculator anchored to a white-space you pick.',
};

// ---- helpers --------------------------------------------------------------
const esc = (s) => String(s == null ? '' : s)
  .replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// Format a USD figure given in *billions*. $21.0B / $3.2B / $63M / $450K.
function money(billions) {
  const v = Number(billions) * 1e9;
  if (!isFinite(v)) return '$—';
  const a = Math.abs(v);
  if (a >= 1e9) return '$' + (v / 1e9).toFixed(1).replace(/\.0$/, '') + 'B';
  if (a >= 1e6) return '$' + Math.round(v / 1e6) + 'M';
  if (a >= 1e3) return '$' + Math.round(v / 1e3) + 'K';
  return '$' + Math.round(v);
}

const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));
const $ = (sel, root) => root.querySelector(sel);

export function mount(container, data) {
  const m = (data && data.market) || null;
  const attrs = (data && Array.isArray(data.attributes)) ? data.attributes : [];

  // Inject scoped styles once per container.
  const style = document.createElement('style');
  style.textContent = CSS;
  container.appendChild(style);

  if (!m || m.market_size_usd_b == null) {
    const note = document.createElement('div');
    note.className = 'mk-empty';
    note.textContent = 'Market sizing data unavailable — data.market is empty.';
    container.appendChild(note);
    return;
  }

  const size = Number(m.market_size_usd_b);
  const cagr = Number(m.cagr_pct) || 0;
  const projected = size * Math.pow(1 + cagr / 100, 5);
  const shares = Array.isArray(m.share_by_dollar_sales) ? m.share_by_dollar_sales : [];
  const sources = Array.isArray(m.sources) ? m.sources : [];

  // ---- 1. headline tiles --------------------------------------------------
  const tiles = `
    <div class="mk-tiles">
      <div class="mk-tile">
        <div class="mk-big">${money(size)}</div>
        <div class="mk-cap">US category · TAM</div>
        ${m.market_size_note ? `<div class="mk-fine">${esc(m.market_size_note)}</div>` : ''}
      </div>
      <div class="mk-tile">
        <div class="mk-big">~${cagr.toFixed(0)}%</div>
        <div class="mk-cap">CAGR</div>
        ${m.cagr_note ? `<div class="mk-fine">${esc(m.cagr_note)}</div>` : ''}
      </div>
      <div class="mk-tile">
        <div class="mk-big">${money(projected)}</div>
        <div class="mk-cap">projected 2029 @ ~${cagr.toFixed(0)}%</div>
        <div class="mk-fine">${money(size)} × (1 + ${cagr.toFixed(0)}%)^5 — compounding today's category forward five years.</div>
      </div>
    </div>`;

  // ---- 2. dollar-share stacked bar ---------------------------------------
  const palette = { 'Red Bull': 'var(--ice)', 'Monster': 'var(--good)', 'Celsius': 'var(--dim)' };
  const isBattleground = (b) => /all\s*others?/i.test(b || '');
  let shareViz = '';
  if (shares.length) {
    const segs = shares.map((s) => {
      const pct = clamp(Number(s.share_pct) || 0, 0, 100);
      const volt = isBattleground(s.brand);
      const color = volt ? 'var(--volt)' : (palette[s.brand] || 'var(--line-2)');
      return `<span class="mk-seg${volt ? ' mk-seg-bg' : ''}" style="width:${pct}%;background:${color}" title="${esc(s.brand)} · ${pct}%"></span>`;
    }).join('');
    const legend = shares.map((s) => {
      const pct = Number(s.share_pct) || 0;
      const volt = isBattleground(s.brand);
      const color = volt ? 'var(--volt)' : (palette[s.brand] || 'var(--line-2)');
      return `<span class="mk-leg${volt ? ' mk-leg-bg' : ''}">
        <i style="background:${color}"></i>${esc(s.brand)} <b>${pct}%</b></span>`;
    }).join('');
    shareViz = `
      <div class="mk-share">
        <div class="mk-cap">US dollar-sales share</div>
        <div class="mk-bar">${segs}</div>
        <div class="mk-legend">${legend}</div>
        ${m.share_note ? `<div class="mk-fine mk-note">${esc(m.share_note)}</div>` : ''}
      </div>`;
  }

  // ---- 3. TAM -> SAM -> SOM calculator ------------------------------------
  // Build the white-space <select>. Attributes arrive sorted by gap_score desc.
  const opts = attrs.map((a, i) => {
    const lbl = `${a.name} · gap ${a.gap_score} · ${a.supply_pct}% of shelf`;
    return `<option value="${i}">${esc(lbl)}</option>`;
  }).join('');

  const hasAttrs = attrs.length > 0;
  const calc = `
    <div class="mk-calc">
      <div class="mk-cap mk-calc-h">TAM → SAM → SOM · live</div>
      <div class="mk-controls">
        <label class="mk-ctrl">
          <span class="mk-clabel">White-space attribute (the niche)</span>
          ${hasAttrs
            ? `<select class="mk-select" id="mk-attr">${opts}</select>`
            : `<div class="mk-fine">no attribute data</div>`}
        </label>
        <label class="mk-ctrl">
          <span class="mk-clabel">Share of obtainable segment you capture
            <b class="mk-val" id="mk-capv">2.0%</b></span>
          <input class="mk-range" id="mk-cap" type="range" min="0.1" max="10" step="0.1" value="2">
        </label>
        <label class="mk-ctrl">
          <span class="mk-clabel">% of category that wants this attribute
            <b class="mk-val" id="mk-wantv">—</b>
            <em class="mk-assume">assumption</em></span>
          <input class="mk-range" id="mk-want" type="range" min="1" max="60" step="0.5" value="15">
        </label>
      </div>

      <div class="mk-funnel">
        <div class="mk-step">
          <div class="mk-slabel">TAM</div>
          <div class="mk-snum" id="mk-tam">${money(size)}</div>
          <div class="mk-sdesc">whole US category</div>
        </div>
        <div class="mk-arrow">›</div>
        <div class="mk-step">
          <div class="mk-slabel">SAM</div>
          <div class="mk-snum" id="mk-sam">—</div>
          <div class="mk-sdesc">serviceable · the niche</div>
        </div>
        <div class="mk-arrow">›</div>
        <div class="mk-step mk-step-som">
          <div class="mk-slabel">SOM</div>
          <div class="mk-snum" id="mk-som">—</div>
          <div class="mk-sdesc">obtainable · yr-1-ish</div>
        </div>
      </div>

      <div class="mk-formula" id="mk-formula"></div>
      <div class="mk-take" id="mk-take"></div>
    </div>`;

  // ---- 4. sources + disclaimer -------------------------------------------
  const srcLinks = sources.map((s) =>
    `<a class="mk-src" href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.label)}</a>`
  ).join('');
  const disclaimer = m.note ? esc(m.note)
    : 'Directional estimate — industry figures vary widely by research firm and category scope.';
  const foot = `
    <div class="mk-foot">
      <div class="mk-disc">⚠ ${disclaimer}${m.as_of ? ` · as of ${esc(m.as_of)}` : ''}</div>
      ${srcLinks ? `<div class="mk-sources"><span class="mk-cap">Sources</span>${srcLinks}</div>` : ''}
    </div>`;

  container.insertAdjacentHTML('beforeend', tiles + shareViz + calc + foot);

  // ---- wire interactivity -------------------------------------------------
  if (!hasAttrs) return;

  const attrSel = $('#mk-attr', container);
  const capR = $('#mk-cap', container);
  const wantR = $('#mk-want', container);
  const capV = $('#mk-capv', container);
  const wantV = $('#mk-wantv', container);
  const tamEl = $('#mk-tam', container);
  const samEl = $('#mk-sam', container);
  const somEl = $('#mk-som', container);
  const formulaEl = $('#mk-formula', container);
  const takeEl = $('#mk-take', container);

  // Heuristic for the default "% who want this" given an attribute.
  // demand_pct is share of *all consumer mentions* (e.g. Protein 1.296%). It is
  // a thin proxy, so we scale it up into a plausible interest band and clamp to
  // [5, 40]. Labeled in the UI as an assumption the investor can override.
  function defaultWant(a) {
    const base = (Number(a && a.demand_pct) || 0) * 12;
    return clamp(Math.round(base), 5, 40);
  }

  function shortName(name) {
    return String(name || '').split(' / ')[0].toLowerCase();
  }

  function recompute() {
    const a = attrs[Number(attrSel.value)] || attrs[0];
    const capPct = Number(capR.value);   // share of segment captured
    const wantPct = Number(wantR.value); // % of category wanting attribute

    const sam = size * (wantPct / 100);
    const som = sam * (capPct / 100);

    capV.textContent = capPct.toFixed(1) + '%';
    wantV.textContent = wantPct.toFixed(0) + '%';
    samEl.textContent = money(sam);
    somEl.textContent = money(som);

    formulaEl.innerHTML =
      `<span class="mk-frow">TAM = <b>${money(size)}</b> &nbsp;·&nbsp; whole US category</span>` +
      `<span class="mk-frow">SAM = TAM × ${wantPct.toFixed(0)}% want <b>${esc(a.name)}</b> = <b>${money(sam)}</b></span>` +
      `<span class="mk-frow">SOM = SAM × ${capPct.toFixed(1)}% you capture = <b>${money(som)}</b></span>`;

    takeEl.innerHTML =
      `A <b>${esc(shortName(a.name))}</b> energy drink capturing <b>${capPct.toFixed(1)}%</b> ` +
      `of the segment that wants it ≈ <b>${money(som)}</b> — vs a ${money(size)} category growing ~${cagr.toFixed(0)}%/yr.`;
  }

  // When attribute changes, reset the "% want" slider to its derived default.
  function onAttrChange() {
    const a = attrs[Number(attrSel.value)] || attrs[0];
    wantR.value = String(defaultWant(a));
    recompute();
  }

  attrSel.addEventListener('change', onAttrChange);
  capR.addEventListener('input', recompute);
  wantR.addEventListener('input', recompute);

  // Initial state: first attribute (highest gap), derived want, ~2% capture.
  onAttrChange();
}

// ---- scoped styles (all .mk-*) -------------------------------------------
const CSS = `
.mk-empty { color: var(--dim); font-family: var(--f-mono); font-size: 12px; padding: 1rem 0; }

.mk-tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: var(--line); border: 1px solid var(--line); }
.mk-tile { background: var(--panel); padding: 1.3rem 1.4rem; }
.mk-big { font-family: var(--f-display); font-weight: 800; font-stretch: 115%; font-size: 2.6rem; line-height: 1; color: var(--volt); }
.mk-cap { font-family: var(--f-mono); font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--dim); margin-top: 0.6rem; }
.mk-fine { font-family: var(--f-mono); font-size: 10px; line-height: 1.5; color: var(--dim); margin-top: 0.55rem; }

.mk-share { margin-top: 1.4rem; background: var(--panel); border: 1px solid var(--line); padding: 1.3rem 1.4rem; }
.mk-bar { display: flex; width: 100%; height: 30px; margin-top: 0.6rem; border: 1px solid var(--line-2); overflow: hidden; }
.mk-seg { display: block; height: 100%; transition: filter 0.2s; }
.mk-seg:hover { filter: brightness(1.3); }
.mk-seg-bg { box-shadow: inset 0 0 0 1px #000; }
.mk-legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1.1rem; margin-top: 0.8rem; }
.mk-leg { display: inline-flex; align-items: center; gap: 0.4rem; font-family: var(--f-mono); font-size: 11px; color: var(--dim); }
.mk-leg i { width: 10px; height: 10px; display: inline-block; }
.mk-leg b { color: var(--ink); }
.mk-leg-bg { color: var(--volt); }
.mk-leg-bg b { color: var(--volt); }
.mk-note { margin-top: 0.9rem; max-width: 70ch; }

.mk-calc { margin-top: 1.4rem; background: linear-gradient(180deg, #0d0d0d, var(--bg)); border: 1px solid var(--line-2); padding: 1.3rem 1.4rem 1.5rem; }
.mk-calc-h { margin-top: 0; margin-bottom: 1rem; color: var(--volt); }
.mk-controls { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; }
.mk-ctrl { display: block; }
.mk-clabel { display: block; font-family: var(--f-mono); font-size: 10px; letter-spacing: 0.05em; text-transform: uppercase; color: var(--dim); margin-bottom: 0.55rem; }
.mk-val { color: var(--volt); font-size: 11px; }
.mk-assume { font-style: normal; color: var(--warn); font-size: 9px; border: 1px solid var(--warn); padding: 0 4px; margin-left: 4px; border-radius: 2px; opacity: 0.85; }

.mk-select { width: 100%; background: var(--bg-2); border: 1px solid var(--line-2); padding: 0.65rem 0.7rem; color: var(--ink); font-family: var(--f-body); font-size: 0.86rem; appearance: none;
  background-image: linear-gradient(45deg, transparent 50%, var(--volt) 50%), linear-gradient(135deg, var(--volt) 50%, transparent 50%);
  background-position: calc(100% - 16px) 1.05rem, calc(100% - 11px) 1.05rem; background-size: 5px 5px; background-repeat: no-repeat; }
.mk-select:focus { outline: none; border-color: var(--volt); }

.mk-range { width: 100%; margin-top: 0.5rem; accent-color: var(--volt); background: transparent; cursor: pointer; }
.mk-range:focus { outline: none; }

.mk-funnel { display: flex; align-items: stretch; gap: 0.4rem; margin-top: 1.5rem; }
.mk-step { flex: 1; background: var(--panel); border: 1px solid var(--line); padding: 1rem 1.1rem; }
.mk-step-som { border-color: var(--volt); box-shadow: inset 0 0 18px rgba(198,255,0,0.06); }
.mk-slabel { font-family: var(--f-mono); font-size: 10px; letter-spacing: 0.12em; color: var(--dim); }
.mk-snum { font-family: var(--f-display); font-weight: 800; font-stretch: 110%; font-size: 1.9rem; line-height: 1.1; color: var(--volt); margin-top: 0.35rem; }
.mk-sdesc { font-family: var(--f-mono); font-size: 9.5px; color: var(--dim); margin-top: 0.35rem; text-transform: uppercase; letter-spacing: 0.04em; }
.mk-arrow { display: flex; align-items: center; color: var(--dimmer); font-size: 1.6rem; font-family: var(--f-display); }

.mk-formula { margin-top: 1.3rem; display: flex; flex-direction: column; gap: 0.3rem; }
.mk-frow { font-family: var(--f-mono); font-size: 11px; color: var(--dim); }
.mk-frow b { color: var(--ice); }
.mk-take { margin-top: 1rem; border-left: 2px solid var(--volt); padding: 0.5rem 0 0.5rem 0.8rem; font-size: 0.95rem; line-height: 1.5; color: var(--ink); }
.mk-take b { color: var(--volt); }

.mk-foot { margin-top: 1.5rem; }
.mk-disc { font-family: var(--f-mono); font-size: 10px; line-height: 1.5; color: var(--warn); max-width: 80ch; }
.mk-sources { margin-top: 0.8rem; display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.4rem 1rem; }
.mk-src { font-family: var(--f-mono); font-size: 10px; color: var(--dim); text-decoration: underline; text-underline-offset: 2px; }
.mk-src:hover { color: var(--volt); }

@media (max-width: 760px) {
  .mk-tiles { grid-template-columns: 1fr; }
  .mk-controls { grid-template-columns: 1fr; }
  .mk-funnel { flex-direction: column; }
  .mk-arrow { transform: rotate(90deg); justify-content: center; padding: 0.2rem 0; }
}
`;
