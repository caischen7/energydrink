// Momentum Explorer — multi-line chart of monthly brand-mention volume with the
// fastest riser flagged. Self-contained: vanilla JS + inline SVG, no imports.
// Host renders meta.title/meta.blurb above `container`; we build only the body.

export const meta = {
  id: 'momentum',
  navLabel: 'MOMENTUM',
  title: 'Momentum explorer',
  blurb: 'Monthly mention volume per brand from our own YouTube, Amazon and Instagram timestamps. Toggle brands; the fastest riser is flagged.'
};

// ---- helpers --------------------------------------------------------------
const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// '2024-03' -> "MAR '24"
function fmtMonth(ym) {
  const [y, m] = String(ym).split('-');
  const mi = Math.max(0, Math.min(11, (parseInt(m, 10) || 1) - 1));
  return `${MONTHS[mi].toUpperCase()} '${String(y).slice(2)}`;
}

const mean = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0);

// Dimmer palette for non-emphasized lines (cycled).
const GREYS = ['#5a5a5a', '#666', '#727272', '#7e7e7e', '#8a8a8a', '#969696', '#a2a2a2', '#aeaeae'];

// ---- entry point ----------------------------------------------------------
export function mount(container, data) {
  const trends = (data && data.trends) || {};
  const months = Array.isArray(trends.months) ? trends.months : [];
  const rawSeries = Array.isArray(trends.series) ? trends.series : [];
  // Keep only well-formed series with at least one positive value.
  const series = rawSeries
    .filter((s) => s && Array.isArray(s.counts) && s.counts.length)
    .map((s) => ({ brand: String(s.brand || '—'), counts: s.counts.map((n) => Number(n) || 0) }));

  injectStyle(container);

  if (!months.length || !series.length) {
    const empty = document.createElement('div');
    empty.className = 'mo-empty mono';
    empty.textContent = '// NO TREND DATA — run build_dashboard_data.py to populate data.trends';
    container.appendChild(empty);
    return;
  }

  // ---- fastest riser / biggest faller: last 6 vs prior 6 months -----------
  const ranked = series.map((s) => {
    const c = s.counts;
    const last6 = c.slice(-6);
    const prior6 = c.slice(-12, -6);
    const a = mean(last6);
    const b = mean(prior6);
    // Ratio is only a trustworthy "acceleration" signal off a real baseline:
    // require enough history AND a prior base of ~1+ mention/mo, so a single
    // stray mention (e.g. 0.33 -> 4) can't manufacture a +1000% headline.
    const hasBase = prior6.length >= 3 && b >= 1 && a - b >= 1;
    const pct = hasBase ? ((a - b) / b) * 100 : null;
    return { brand: s.brand, last: a, prior: b, pct, delta: a - b, hasBase };
  });

  // Prefer brands with a credible baseline; fall back to raw delta only if none qualify.
  const rising = ranked.filter((r) => r.pct !== null && r.pct > 0).sort((x, y) => y.pct - x.pct);
  const falling = ranked.filter((r) => r.pct !== null && r.pct < 0).sort((x, y) => x.pct - y.pct);
  const riser = rising[0] || null;
  const faller = falling[0] || null;
  const riserBrand = riser ? riser.brand : null;

  // ---- visibility state (all on by default) -------------------------------
  const visible = new Map(series.map((s) => [s.brand, true]));

  // ---- assign each brand a stable colour ----------------------------------
  const colorOf = (brand) => {
    if (brand === riserBrand) return 'var(--volt)';
    const i = series.findIndex((s) => s.brand === brand);
    return GREYS[i % GREYS.length];
  };

  // ---- root layout --------------------------------------------------------
  const root = document.createElement('div');
  root.className = 'mo-root';
  root.innerHTML = `
    <div class="mo-callout" id="mo-callout"></div>
    <div class="mo-chartwrap">
      <div class="mo-chart" id="mo-chart"></div>
      <div class="mo-tip" id="mo-tip" aria-hidden="true"></div>
    </div>
    <div class="mo-legend" id="mo-legend"></div>
    <div class="mo-note">${esc(trends.note || '')}</div>`;
  container.appendChild(root);

  const chartHost = root.querySelector('#mo-chart');
  const legendHost = root.querySelector('#mo-legend');
  const tip = root.querySelector('#mo-tip');
  const calloutHost = root.querySelector('#mo-callout');

  // ---- callout ------------------------------------------------------------
  let calloutHtml = '';
  if (riser) {
    const sign = riser.pct >= 0 ? '+' : '';
    calloutHtml += `<span class="mo-flag mo-up">&#9650; FASTEST RISER</span>
      <b class="mo-volt">${esc(riser.brand)}</b>
      <span class="mo-pct">${sign}${Math.round(riser.pct)}%</span>
      <span class="mo-sub mono">last 6 mo vs prior 6 mo</span>`;
  } else {
    calloutHtml += `<span class="mo-flag mo-up">&#9650; MOMENTUM</span>
      <span class="mo-sub mono">not enough history to flag a riser</span>`;
  }
  if (faller) {
    calloutHtml += `<span class="mo-faller mono">&#9660; cooling: <b>${esc(faller.brand)}</b> ${Math.round(faller.pct)}%</span>`;
  }
  calloutHost.innerHTML = calloutHtml;

  // ---- legend chips -------------------------------------------------------
  legendHost.innerHTML = series.map((s) => {
    const isRiser = s.brand === riserBrand;
    return `<button type="button" class="mo-chip${isRiser ? ' mo-chip-riser' : ''}" data-brand="${esc(s.brand)}" aria-pressed="true">
      <span class="mo-swatch" style="background:${colorOf(s.brand)}"></span>
      <span class="mo-chip-label">${esc(s.brand)}</span>
    </button>`;
  }).join('');

  legendHost.addEventListener('click', (e) => {
    const chip = e.target.closest('.mo-chip');
    if (!chip) return;
    const brand = chip.getAttribute('data-brand');
    const now = !visible.get(brand);
    visible.set(brand, now);
    chip.classList.toggle('mo-off', !now);
    chip.setAttribute('aria-pressed', String(now));
    renderChart();
  });

  // ---- chart geometry -----------------------------------------------------
  const W = 760;
  const H = 360;
  const M = { t: 18, r: 18, b: 38, l: 40 };
  const iw = W - M.l - M.r;
  const ih = H - M.t - M.b;
  const n = months.length;
  const xAt = (i) => M.l + (n <= 1 ? iw / 2 : (i / (n - 1)) * iw);

  function yMax() {
    let mx = 1;
    for (const s of series) {
      if (!visible.get(s.brand)) continue;
      for (const v of s.counts) if (v > mx) mx = v;
    }
    return mx;
  }

  // nearest-month index for a given client X over the plot rect
  let lastRect = null;
  function renderChart() {
    const maxY = yMax();
    const yAt = (v) => M.t + ih - (v / maxY) * ih;

    let svg = `<svg viewBox="0 0 ${W} ${H}" class="mo-svg" role="img" aria-label="Monthly brand-mention volume per brand" preserveAspectRatio="xMidYMid meet">`;

    // horizontal gridlines + y ticks (5 bands)
    for (let i = 0; i <= 4; i++) {
      const gy = M.t + (ih / 4) * i;
      const val = Math.round(maxY - (maxY / 4) * i);
      svg += `<line class="mo-grid" x1="${M.l}" y1="${gy.toFixed(1)}" x2="${W - M.r}" y2="${gy.toFixed(1)}"/>`;
      svg += `<text class="mo-axt" x="${M.l - 6}" y="${(gy + 3).toFixed(1)}" text-anchor="end">${val}</text>`;
    }
    // x labels every ~6th month (always include the last)
    const step = Math.max(1, Math.round(n / 6));
    for (let i = 0; i < n; i += step) {
      svg += `<text class="mo-axt" x="${xAt(i).toFixed(1)}" y="${H - M.b + 16}" text-anchor="middle">${esc(fmtMonth(months[i]))}</text>`;
    }
    if ((n - 1) % step !== 0) {
      svg += `<text class="mo-axt" x="${xAt(n - 1).toFixed(1)}" y="${H - M.b + 16}" text-anchor="middle">${esc(fmtMonth(months[n - 1]))}</text>`;
    }

    // one polyline per visible series; draw riser last so it sits on top
    const order = [...series].sort((a, b) => (a.brand === riserBrand ? 1 : 0) - (b.brand === riserBrand ? 1 : 0));
    for (const s of order) {
      if (!visible.get(s.brand)) continue;
      const isRiser = s.brand === riserBrand;
      const pts = s.counts.map((v, i) => `${xAt(i).toFixed(1)},${yAt(v).toFixed(1)}`).join(' ');
      svg += `<polyline class="mo-line${isRiser ? ' mo-line-riser' : ''}" points="${pts}" fill="none" `
        + `stroke="${colorOf(s.brand)}" stroke-width="${isRiser ? 2.4 : 1.3}" `
        + `stroke-opacity="${isRiser ? 1 : 0.7}" stroke-linejoin="round" stroke-linecap="round"/>`;
      // end dot for emphasis on the riser
      if (isRiser) {
        const li = s.counts.length - 1;
        svg += `<circle class="mo-end" cx="${xAt(li).toFixed(1)}" cy="${yAt(s.counts[li]).toFixed(1)}" r="3" fill="var(--volt)"/>`;
      }
    }

    // hover guide line + focus dots (hidden until hover)
    svg += `<line id="mo-guide" class="mo-guide" x1="0" y1="${M.t}" x2="0" y2="${M.t + ih}" style="opacity:0"/>`;
    svg += `<g id="mo-focus"></g>`;
    svg += `</svg>`;
    chartHost.innerHTML = svg;
    lastRect = null; // force recompute after re-render
  }

  // ---- hover tooltip ------------------------------------------------------
  function nearestIndex(clientX) {
    const svgEl = chartHost.querySelector('.mo-svg');
    if (!svgEl) return -1;
    const rect = svgEl.getBoundingClientRect();
    const scaleX = rect.width / W; // viewBox unit -> px
    const xView = (clientX - rect.left) / scaleX;
    if (n <= 1) return 0;
    let i = Math.round(((xView - M.l) / iw) * (n - 1));
    return Math.max(0, Math.min(n - 1, i));
  }

  function showTip(clientX, clientY) {
    const svgEl = chartHost.querySelector('.mo-svg');
    if (!svgEl) return;
    const i = nearestIndex(clientX);
    if (i < 0) return;
    const maxY = yMax();
    const yAt = (v) => M.t + ih - (v / maxY) * ih;

    // move guide + focus dots inside the svg coordinate space
    const guide = svgEl.querySelector('#mo-guide');
    const focus = svgEl.querySelector('#mo-focus');
    if (guide) { guide.setAttribute('x1', xAt(i)); guide.setAttribute('x2', xAt(i)); guide.style.opacity = '1'; }

    const rows = [];
    let dots = '';
    for (const s of series) {
      if (!visible.get(s.brand)) continue;
      const v = s.counts[i] ?? 0;
      rows.push({ brand: s.brand, v, riser: s.brand === riserBrand });
      dots += `<circle cx="${xAt(i).toFixed(1)}" cy="${yAt(v).toFixed(1)}" r="${s.brand === riserBrand ? 3 : 2.4}" fill="${colorOf(s.brand)}"/>`;
    }
    if (focus) focus.innerHTML = dots;

    rows.sort((a, b) => b.v - a.v);
    tip.innerHTML = `<div class="mo-tip-h">${esc(fmtMonth(months[i]))}</div>`
      + rows.map((r) => `<div class="mo-tip-r${r.riser ? ' mo-tip-riser' : ''}">`
        + `<span class="mo-tip-sw" style="background:${colorOf(r.brand)}"></span>`
        + `<span class="mo-tip-b">${esc(r.brand)}</span>`
        + `<span class="mo-tip-v">${r.v}</span></div>`).join('');

    // position tooltip relative to the chart wrapper
    const wrap = root.querySelector('.mo-chartwrap');
    const wrapRect = wrap.getBoundingClientRect();
    let left = clientX - wrapRect.left + 14;
    const top = clientY - wrapRect.top + 12;
    if (left + 180 > wrapRect.width) left = clientX - wrapRect.left - 180;
    tip.style.left = `${Math.max(0, left)}px`;
    tip.style.top = `${top}px`;
    tip.style.opacity = '1';
  }

  function hideTip() {
    tip.style.opacity = '0';
    const svgEl = chartHost.querySelector('.mo-svg');
    if (!svgEl) return;
    const guide = svgEl.querySelector('#mo-guide');
    const focus = svgEl.querySelector('#mo-focus');
    if (guide) guide.style.opacity = '0';
    if (focus) focus.innerHTML = '';
  }

  chartHost.addEventListener('mousemove', (e) => showTip(e.clientX, e.clientY));
  chartHost.addEventListener('mouseleave', hideTip);

  // initial paint
  renderChart();
}

// ---- scoped styles (all classes prefixed mo-) -----------------------------
function injectStyle(container) {
  if (container.querySelector('style[data-mo]')) return;
  const style = document.createElement('style');
  style.setAttribute('data-mo', '');
  style.textContent = `
.mo-root { display: flex; flex-direction: column; gap: 1rem; }
.mo-callout {
  display: flex; align-items: center; flex-wrap: wrap; gap: 0.55rem;
  border: 1px solid var(--line-2); border-left: 2px solid var(--volt);
  background: var(--bg-2); padding: 0.7rem 1rem;
  font-family: var(--f-mono); font-size: 0.8rem; color: var(--dim);
}
.mo-flag { font-family: var(--f-mono); font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase; }
.mo-up { color: var(--volt); }
.mo-callout .mo-volt { color: var(--volt); font-family: var(--f-display); font-weight: 800; font-size: 1rem; letter-spacing: 0.02em; }
.mo-pct { color: var(--ink); font-weight: 700; }
.mo-sub { color: var(--dimmer); }
.mo-faller { margin-left: auto; color: var(--warn); font-size: 0.72rem; }
.mo-faller b { color: var(--warn); }

.mo-chartwrap { position: relative; border: 1px solid var(--line); background: var(--panel); padding: 1rem 1rem 0.4rem; }
.mo-svg { width: 100%; display: block; }
.mo-svg .mo-axt { font-family: var(--f-mono); fill: var(--dim); font-size: 10px; }
.mo-grid { stroke: var(--line); stroke-dasharray: 2 3; }
.mo-line { transition: stroke-opacity 0.15s; }
.mo-guide { stroke: var(--line-2); stroke-dasharray: 3 3; }
.mo-end { filter: drop-shadow(0 0 4px var(--volt)); }

.mo-tip {
  position: absolute; pointer-events: none; opacity: 0; transition: opacity 0.1s;
  background: #000; border: 1px solid var(--line-2); padding: 0.5rem 0.6rem;
  font-family: var(--f-mono); font-size: 11px; min-width: 130px; z-index: 5;
  box-shadow: 0 6px 20px rgba(0,0,0,0.6);
}
.mo-tip-h { color: var(--volt); font-size: 10px; letter-spacing: 0.06em; margin-bottom: 0.3rem; border-bottom: 1px solid var(--line); padding-bottom: 0.25rem; }
.mo-tip-r { display: flex; align-items: center; gap: 0.4rem; color: var(--dim); line-height: 1.5; }
.mo-tip-riser { color: var(--ink); }
.mo-tip-sw { width: 8px; height: 2px; flex: 0 0 8px; }
.mo-tip-b { flex: 1 1 auto; }
.mo-tip-v { color: var(--ink); font-weight: 700; }

.mo-legend { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.mo-chip {
  display: inline-flex; align-items: center; gap: 0.4rem; cursor: pointer;
  background: var(--bg-2); border: 1px solid var(--line); color: var(--dim);
  padding: 0.3rem 0.6rem; font-family: var(--f-mono); font-size: 10px;
  letter-spacing: 0.04em; text-transform: uppercase; transition: all 0.15s;
}
.mo-chip:hover { border-color: var(--line-2); color: var(--ink); }
.mo-chip-riser { border-color: var(--volt); color: var(--ink); }
.mo-chip-riser .mo-chip-label { color: var(--volt); }
.mo-swatch { width: 12px; height: 3px; flex: 0 0 12px; }
.mo-chip.mo-off { opacity: 0.4; }
.mo-chip.mo-off .mo-swatch { background: var(--dimmer) !important; }
.mo-chip.mo-off .mo-chip-label { text-decoration: line-through; color: var(--dimmer); }

.mo-note { color: var(--dimmer); font-family: var(--f-mono); font-size: 10px; line-height: 1.5; }
.mo-empty { color: var(--dim); font-family: var(--f-mono); font-size: 11px; padding: 2rem 0; }
`;
  container.appendChild(style);
}
