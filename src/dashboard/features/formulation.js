// FORMULATION ANALYZER — self-contained feature module for ION_INTEL.
// Plots every brand's flagship by sugar vs caffeine to expose product-spec
// white space: the high-caffeine / zero-sugar quadrant is crowded, so the
// open spec keeps that base and layers an unmet FUNCTION on top.
// Vanilla JS + inline SVG only. No imports.

export const meta = {
  id: 'formulation',
  navLabel: 'FORMULATION',
  title: 'Formulation map',
  blurb: 'Every flagship by caffeine vs sugar. The modern sweet spot — high caffeine, zero sugar — is crowded; the open spec adds an unmet function on top.',
};

// --- tiny local helpers (kept internal to avoid cross-module coupling) ------
const esc = (s) => String(s == null ? '' : s)
  .replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const num = (v, d = 0) => (typeof v === 'number' && isFinite(v) ? v : d);
const one = (n) => (Math.round(n * 10) / 10).toString();

export function mount(container, data) {
  const all = Array.isArray(data && data.nutrition) ? data.nutrition : [];
  // normalize + guard null fields
  const items = all.map((it) => ({
    brand: it.brand || '—',
    product: it.product || it.brand || '—',
    serving_oz: num(it.serving_oz, 0),
    caffeine_mg: num(it.caffeine_mg, 0),
    caffeine_per_oz: num(it.caffeine_per_oz, 0),
    sugar_g: num(it.sugar_g, 0),
    calories: num(it.calories, 0),
    category: it.category || '—',
  }));
  const attrs = Array.isArray(data && data.attributes) ? data.attributes : [];

  injectStyle(container);

  if (!items.length) {
    const note = document.createElement('div');
    note.className = 'fa-note';
    note.textContent = 'no nutrition data';
    container.appendChild(note);
    return;
  }

  const body = document.createElement('div');
  body.className = 'fa-root';
  body.innerHTML = `
    <div class="fa-grid">
      <div class="fa-panel fa-chartwrap">
        ${scatterSVG(items)}
        <div class="fa-legend">
          <span><i class="fa-sw" style="background:var(--volt)"></i> zero-sugar (≤1g)</span>
          <span><i class="fa-sw" style="background:var(--ice);opacity:.8"></i> some sugar</span>
          <span><i class="fa-sw" style="background:var(--warn);opacity:.85"></i> high sugar (≥25g)</span>
          <span><i class="fa-band"></i> crowded sweet spot</span>
        </div>
      </div>
      ${calloutPanel(items, attrs)}
    </div>
    ${potencyTable(items)}
  `;
  container.appendChild(body);
  wireTips(container);
}

// --- 1+2+3: scatter with shaded sweet-spot region + labels + tooltips -------
function scatterSVG(items) {
  const w = 660; const h = 470;
  const m = { t: 26, r: 22, b: 48, l: 56 };
  const iw = w - m.l - m.r; const ih = h - m.t - m.b;
  const SUGMAX = 65; const CAFMAX = 320;
  const x = (v) => m.l + (Math.min(v, SUGMAX) / SUGMAX) * iw;          // sugar_g
  const y = (v) => m.t + ih - (Math.min(v, CAFMAX) / CAFMAX) * ih;     // caffeine_mg
  const maxOz = Math.max(...items.map((d) => d.serving_oz), 1);
  const r = (oz) => 4 + Math.sqrt(Math.min(oz, maxOz) / maxOz) * 7;    // size by serving

  // notable brands to label: highest caffeine, highest sugar, top zero-sugar
  const byCaf = [...items].sort((a, b) => b.caffeine_mg - a.caffeine_mg);
  const bySug = [...items].sort((a, b) => b.sugar_g - a.sugar_g);
  const label = new Set();
  if (byCaf[0]) label.add(byCaf[0].brand);                 // highest caffeine
  if (bySug[0]) label.add(bySug[0].brand);                 // highest sugar
  ['Celsius', 'Alani Nu', 'Bang', 'Reign', 'Monster', 'Red Bull']
    .filter((b) => items.some((it) => it.brand === b)).slice(0, 4)
    .forEach((b) => label.add(b));

  let s = `<svg viewBox="0 0 ${w} ${h}" class="fa-chart" role="img" aria-label="Caffeine versus sugar formulation map">`;

  // crowded sweet-spot region: caffeine >= 180, sugar <= 1
  const sx = x(0); const sx2 = x(2.5); const sy = m.t; const sy2 = y(180);
  s += `<rect x="${sx}" y="${sy}" width="${Math.max(sx2 - sx, 24)}" height="${sy2 - sy}" fill="var(--volt)" opacity="0.07"/>`;
  s += `<text class="fa-quad" x="${sx + 6}" y="${sy + 15}">◤ crowded sweet spot</text>`;
  s += `<text class="fa-quad" x="${sx + 6}" y="${sy + 28}">≥180mg · ≤1g sugar</text>`;

  // gridlines + y ticks (caffeine)
  for (let i = 0; i <= 4; i++) {
    const gy = m.t + (ih / 4) * i;
    const val = CAFMAX - (CAFMAX / 4) * i;
    s += `<line class="fa-grid" x1="${m.l}" y1="${gy}" x2="${w - m.r}" y2="${gy}"/>`;
    s += `<text class="fa-tick" x="${m.l - 8}" y="${gy + 3}" text-anchor="end">${val}</text>`;
  }
  // x ticks (sugar)
  for (let i = 0; i <= 5; i++) {
    const gx = m.l + (iw / 5) * i;
    s += `<text class="fa-tick" x="${gx}" y="${h - m.b + 18}" text-anchor="middle">${Math.round((SUGMAX / 5) * i)}</text>`;
  }
  // axis labels
  s += `<text class="fa-axis" x="${m.l + iw / 2}" y="${h - 6}" text-anchor="middle">SUGAR (g)</text>`;
  s += `<text class="fa-axis" transform="translate(14 ${m.t + ih / 2}) rotate(-90)" text-anchor="middle">CAFFEINE (mg)</text>`;

  // dots
  for (const d of items) {
    const cx = x(d.sugar_g); const cy = y(d.caffeine_mg);
    const zero = d.sugar_g <= 1;
    const fill = zero ? 'var(--volt)' : (d.sugar_g >= 25 ? 'var(--warn)' : 'var(--ice)');
    const op = zero ? 0.85 : 0.6;
    const tip = `${d.brand}\n${d.product}\nCaffeine ${d.caffeine_mg}mg · Sugar ${one(d.sugar_g)}g\n${d.calories} cal · ${one(d.serving_oz)} oz`;
    s += `<circle class="fa-dot" cx="${cx}" cy="${cy}" r="${one(r(d.serving_oz))}" fill="${fill}" fill-opacity="${op}" stroke="${fill}" stroke-opacity="0.95" data-tip="${esc(tip)}"/>`;
    if (label.has(d.brand)) {
      s += `<text class="fa-pt" x="${cx}" y="${cy - r(d.serving_oz) - 4}" text-anchor="middle">${esc(d.brand)}</text>`;
    }
  }
  s += `</svg>`;
  return s;
}

// --- 4: data-referenced callout — keep the base, add an unmet function ------
function calloutPanel(items, attrs) {
  const inSpot = items.filter((d) => d.caffeine_mg >= 180 && d.sugar_g <= 1).length;
  const top = attrs.slice(0, 3);
  const shortName = (n) => String(n).split(' / ')[0].split('/')[0].trim().toLowerCase();
  const chips = top.map((a) => `<span class="fa-chip">+ ${esc(shortName(a.name))}</span>`).join('');
  const lines = top.map((a) => `<li><b class="fa-volt">${esc(a.name)}</b> — only <b>${one(num(a.supply_pct))}%</b> of shelf supplies it · gap score <b>${one(num(a.gap_score))}</b></li>`).join('');

  return `<div class="fa-panel fa-callout">
    <div class="fa-kpi"><div class="fa-kn">${inSpot}/${items.length}</div><div class="fa-kl">flagships in the high-caffeine · zero-sugar quadrant</div></div>
    <div class="fa-lede">The <b class="fa-volt">high-caffeine / zero-sugar</b> spec is <b>saturated</b>. Matching it wins nothing. The open product spec <b>keeps that base</b> — ~200mg caffeine, 0g sugar — and <b class="fa-volt">layers on an unmet function</b> the shelf doesn't serve:</div>
    ${chips ? `<div class="fa-chips">${chips}</div>` : ''}
    ${lines ? `<ul class="fa-list">${lines}</ul>` : ''}
    <div class="fa-fine">Gap score = consumer demand × (1 − catalog supply). Source: data.attributes (top by gap_score).</div>
  </div>`;
}

// --- 5: ranked potency table (caffeine_per_oz desc) -------------------------
function potencyTable(items) {
  const rows = [...items]
    .filter((d) => d.caffeine_per_oz > 0)
    .sort((a, b) => b.caffeine_per_oz - a.caffeine_per_oz)
    .map((d, i) => {
      const zero = d.sugar_g <= 1;
      return `<tr${zero ? ' class="fa-z"' : ''}>
        <td class="fa-rk">${String(i + 1).padStart(2, '0')}</td>
        <td class="fa-bn">${esc(d.brand)}</td>
        <td class="fa-r">${one(d.caffeine_per_oz)}</td>
        <td class="fa-r">${d.caffeine_mg}</td>
        <td class="fa-r">${zero ? '<span class="fa-zero">0 ✓</span>' : one(d.sugar_g)}</td>
        <td class="fa-r">${d.calories}</td>
      </tr>`;
    }).join('');

  return `<div class="fa-panel fa-tablewrap">
    <div class="fa-th-label">POTENCY RANK — CAFFEINE PER OZ ↓ · <span class="fa-volt">✓</span> = zero sugar</div>
    <div class="fa-scroll"><table class="fa-table">
      <thead><tr>
        <th>#</th><th>Brand</th><th class="fa-r">mg/oz</th><th class="fa-r">total mg</th><th class="fa-r">sugar g</th><th class="fa-r">cal</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table></div>
  </div>`;
}

// --- hover tooltips (local, scoped to this container) -----------------------
function wireTips(container) {
  let tip = container.querySelector('.fa-tooltip');
  if (!tip) {
    tip = document.createElement('div');
    tip.className = 'fa-tooltip';
    container.appendChild(tip);
  }
  const show = (e) => {
    const t = e.target.closest('[data-tip]');
    if (!t) return;
    tip.innerHTML = t.getAttribute('data-tip').split('\n')
      .map((l, i) => (i === 0 ? `<b>${esc(l)}</b>` : esc(l))).join('<br>');
    tip.style.opacity = '1';
  };
  container.addEventListener('mouseover', show);
  container.addEventListener('mousemove', (e) => {
    if (tip.style.opacity === '1') {
      tip.style.left = e.clientX + 12 + 'px';
      tip.style.top = e.clientY - 10 + 'px';
    }
  });
  container.addEventListener('mouseout', (e) => {
    if (e.target.closest('[data-tip]')) tip.style.opacity = '0';
  });
}

// --- scoped styles (all classes fa- prefixed; reuse global :root vars) ------
function injectStyle(container) {
  const style = document.createElement('style');
  style.textContent = `
.fa-root{display:flex;flex-direction:column;gap:1.2rem}
.fa-grid{display:grid;grid-template-columns:1.55fr 1fr;gap:1.2rem;align-items:stretch}
@media(max-width:880px){.fa-grid{grid-template-columns:1fr}}
.fa-panel{background:var(--panel);border:1px solid var(--line);padding:1.2rem}
.fa-chartwrap{display:flex;flex-direction:column}
.fa-chart{width:100%;height:auto;display:block}
.fa-grid line.fa-grid,.fa-chart .fa-grid{stroke:var(--line);stroke-width:1}
.fa-tick,.fa-axis,.fa-quad,.fa-pt{font-family:var(--f-mono);fill:var(--dim)}
.fa-tick{font-size:10px}
.fa-axis{font-size:10px;letter-spacing:.08em;fill:var(--dim)}
.fa-quad{font-size:9px;letter-spacing:.06em;fill:var(--volt);opacity:.85}
.fa-pt{font-size:9.5px;fill:var(--ink);letter-spacing:.03em}
.fa-dot{cursor:crosshair;transition:fill-opacity .12s,r .12s}
.fa-dot:hover{fill-opacity:1}
.fa-legend{display:flex;flex-wrap:wrap;gap:.4rem 1.1rem;margin-top:.7rem;font-family:var(--f-mono);font-size:10px;color:var(--dim);text-transform:uppercase}
.fa-legend span{display:inline-flex;align-items:center;gap:.4rem}
.fa-sw{width:9px;height:9px;border-radius:50%;display:inline-block}
.fa-band{width:11px;height:9px;display:inline-block;background:var(--volt);opacity:.18;border:1px solid var(--volt)}
.fa-callout{display:flex;flex-direction:column;gap:.85rem}
.fa-kpi{border-bottom:1px solid var(--line);padding-bottom:.7rem}
.fa-kn{font-family:var(--f-display);font-size:2.2rem;line-height:1;color:var(--volt);font-weight:800}
.fa-kl{font-family:var(--f-mono);font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:.05em;margin-top:.35rem}
.fa-lede{font-family:var(--f-body);font-size:.92rem;line-height:1.5;color:var(--ink)}
.fa-volt{color:var(--volt)}
.fa-chips{display:flex;flex-wrap:wrap;gap:.45rem}
.fa-chip{font-family:var(--f-mono);font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--volt);border:1px solid var(--line-2);background:var(--bg-2);padding:.3rem .55rem}
.fa-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:.5rem}
.fa-list li{font-family:var(--f-body);font-size:.84rem;line-height:1.4;color:var(--dim);border-left:2px solid var(--line-2);padding-left:.6rem}
.fa-list li b{color:var(--ink)}
.fa-fine{font-family:var(--f-mono);font-size:9px;color:var(--dim);opacity:.7;letter-spacing:.03em;border-top:1px solid var(--line);padding-top:.6rem}
.fa-tablewrap{padding:.4rem 1.2rem 1rem}
.fa-th-label{font-family:var(--f-mono);font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em;padding:.9rem 0 .5rem}
.fa-scroll{overflow-x:auto}
.fa-table{width:100%;border-collapse:collapse;font-family:var(--f-body);font-size:.84rem}
.fa-table th{font-family:var(--f-mono);font-size:9.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--dim);text-align:left;font-weight:400;padding:.5rem .7rem;border-bottom:1px solid var(--line-2)}
.fa-table td{padding:.42rem .7rem;border-bottom:1px solid var(--line);color:var(--ink)}
.fa-table tr:last-child td{border-bottom:none}
.fa-table .fa-r{text-align:right;font-family:var(--f-mono)}
.fa-table th.fa-r{text-align:right}
.fa-rk{font-family:var(--f-mono);color:var(--dim);font-size:11px}
.fa-bn{font-weight:600}
.fa-z .fa-bn{color:var(--volt)}
.fa-zero{color:var(--volt);font-family:var(--f-mono);font-size:11px}
.fa-note{font-family:var(--f-mono);font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em;padding:2rem;border:1px solid var(--line);background:var(--panel)}
.fa-tooltip{position:fixed;z-index:50;pointer-events:none;opacity:0;transition:opacity .1s;background:var(--bg-2);border:1px solid var(--line-2);padding:.5rem .65rem;font-family:var(--f-mono);font-size:11px;color:var(--ink);line-height:1.45;max-width:260px;box-shadow:0 6px 24px rgba(0,0,0,.6)}
.fa-tooltip b{color:var(--volt)}
`;
  container.appendChild(style);
}
