/*
 * Need-state segments — a treemap of the category by who each product is for.
 *
 * Box area is trailing-12-month revenue, so the map is a market-share picture you can
 * read at a glance. Clicking a box drills into the brands and products inside it.
 *
 * Reads the nginx-guarded aggregate, same as the other intel pages. The `segments` key
 * is written by data/scripts/add_segments.py.
 */
import '@fontsource-variable/inter';
import './dashboard.css';
import './segments.css';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const money = (n) =>
  n >= 1e9 ? '$' + (n / 1e9).toFixed(2) + 'B' :
  n >= 1e6 ? '$' + (n / 1e6).toFixed(1) + 'M' :
  n >= 1e3 ? '$' + (n / 1e3).toFixed(0) + 'K' : '$' + Math.round(n);
const int = (n) => (n == null ? '—' : Math.round(n).toLocaleString('en-US'));

const COLOR = [
  '#2a78d6', '#eb6834', '#1baf7a', '#eda100',
  '#e87ba4', '#008300', '#4a3aa7', '#e34948',
];

/*
 * Squarified treemap (Bruls, Huizing & van Wijk). Plain proportional slices produce
 * slivers once one category holds two thirds of the market, which is exactly our case —
 * squarified keeps every box close to square so the small ones stay clickable.
 */
function squarify(items, x, y, w, h) {
  const out = [];
  const total = items.reduce((s, i) => s + i.value, 0) || 1;
  let nodes = items.map((i) => ({ ...i, area: (i.value / total) * w * h }));

  const worst = (row, len) => {
    const s = row.reduce((a, r) => a + r.area, 0);
    const mx = Math.max(...row.map((r) => r.area));
    const mn = Math.min(...row.map((r) => r.area));
    return Math.max((len * len * mx) / (s * s), (s * s) / (len * len * mn));
  };

  const layoutRow = (row, len, horizontal) => {
    const s = row.reduce((a, r) => a + r.area, 0);
    const thick = s / len;
    let off = 0;
    row.forEach((r) => {
      const side = r.area / thick;
      out.push(horizontal
        ? { ...r, x, y: y + off, w: thick, h: side }
        : { ...r, x: x + off, y, w: side, h: thick });
      off += side;
    });
    if (horizontal) { x += thick; w -= thick; } else { y += thick; h -= thick; }
  };

  while (nodes.length) {
    const horizontal = w >= h;          // lay the next strip along the shorter side
    const len = horizontal ? h : w;
    const row = [nodes[0]];
    let rest = nodes.slice(1);
    while (rest.length && worst(row, len) >= worst([...row, rest[0]], len)) {
      row.push(rest[0]);
      rest = rest.slice(1);
    }
    layoutRow(row, len, horizontal);
    nodes = rest;
  }
  return out;
}

let DATA;

function renderMap() {
  const W = 1000, H = 560;
  const boxes = squarify(
    DATA.cats.map((c, i) => ({ ...c, value: c.t12, color: COLOR[i % COLOR.length] })),
    0, 0, W, H
  );

  $('#map').innerHTML = `<svg viewBox="0 0 ${W} ${H}" role="img"
      aria-label="Treemap of energy drink need-state segments sized by revenue">
    ${boxes.map((b) => {
      const pad = 2;
      const bw = Math.max(0, b.w - pad * 2), bh = Math.max(0, b.h - pad * 2);
      const big = bw > 120 && bh > 62;
      const mid = bw > 74 && bh > 34;
      return `<g class="tm-box" data-cat="${esc(b.name)}" tabindex="0" role="button"
                 aria-label="${esc(b.name)}, ${b.share}% of sales">
        <rect x="${b.x + pad}" y="${b.y + pad}" width="${bw}" height="${bh}" rx="8"
              fill="${b.color}" fill-opacity="0.16" stroke="${b.color}" stroke-width="1.6"/>
        ${big ? `<text x="${b.x + 16}" y="${b.y + 30}" class="tm-t" fill="${b.color}">${esc(b.name)}</text>
                 <text x="${b.x + 16}" y="${b.y + 52}" class="tm-v">${b.share}% · ${money(b.t12)}</text>
                 <text x="${b.x + 16}" y="${b.y + 72}" class="tm-s">${esc(b.who)}</text>`
          : mid ? `<text x="${b.x + 10}" y="${b.y + 22}" class="tm-t sm" fill="${b.color}">${esc(b.name)}</text>
                   <text x="${b.x + 10}" y="${b.y + 38}" class="tm-v sm">${b.share}%</text>`
              : `<text x="${b.x + 6}" y="${b.y + 16}" class="tm-v sm">${b.share}%</text>`}
        <title>${esc(b.name)} — ${b.share}% of sales · ${money(b.t12)} · ${b.skus} SKUs · ${b.brands} brands</title>
      </g>`;
    }).join('')}
  </svg>`;

  $('#legend').innerHTML = DATA.cats.map((c, i) => `
    <button class="lg-item" data-cat="${esc(c.name)}">
      <i style="background:${COLOR[i % COLOR.length]}"></i>
      <span class="lg-n">${esc(c.name)}</span>
      <span class="lg-v mono">${c.share}%</span>
    </button>`).join('');
}

function openCat(name) {
  const c = DATA.cats.find((x) => x.name === name);
  if (!c) return;
  const i = DATA.cats.indexOf(c);
  const col = COLOR[i % COLOR.length];
  const maxBrand = Math.max(...c.top.map((b) => b.r), 1);

  $('#detail').innerHTML = `
    <div class="dt-head" style="--c:${col}">
      <button class="dt-back mono" id="back">← All segments</button>
      <h2>${esc(c.name)}</h2>
      <p class="dt-who">${esc(c.who)}</p>
      <p class="dt-desc">${esc(c.desc)}</p>
      <div class="dt-kpis">
        <div><span class="n">${c.share}%</span><span class="l mono">OF CATEGORY SALES</span></div>
        <div><span class="n">${money(c.t12)}</span><span class="l mono">TRAILING 12 MONTHS</span></div>
        <div><span class="n">${int(c.skus)}</span><span class="l mono">SKUS</span></div>
        <div><span class="n">${int(c.brands)}</span><span class="l mono">BRANDS</span></div>
      </div>
    </div>
    <h3 class="dt-h mono">BRANDS IN THIS SEGMENT</h3>
    <div class="dt-brands">
      ${c.top.map((b) => `<div class="br-row">
        <span class="br-n">${esc(b.b)}</span>
        <span class="br-bar" style="width:${Math.max(2, (b.r / maxBrand) * 100)}%;background:${col}"></span>
        <span class="br-v mono">${money(b.r)}</span></div>`).join('')}
    </div>
    <h3 class="dt-h mono">TOP PRODUCTS BY SALES</h3>
    <div class="tbl-wrap"><table class="intel-table mono">
      <thead><tr><th class="tl">PRODUCT</th><th class="tl">BRAND</th><th class="tl">FLAVOR</th>
        <th class="tl">SIZE</th><th>STORES</th><th>T12M SALES</th></tr></thead>
      <tbody>${c.prod.map((p) => `<tr>
        <td class="tl pd">${esc(p.d)}</td><td class="tl">${esc(p.b)}</td>
        <td class="tl">${esc(p.fl) || '—'}</td><td class="tl">${esc(p.sz) || '—'}</td>
        <td>${int(p.st)}</td><td>${money(p.r)}</td></tr>`).join('')}</tbody>
    </table></div>
    <p class="dt-note">Showing the top ${c.prod.length} of ${int(c.skus)} SKUs by trailing-12-month sales.</p>`;

  document.body.classList.add('drilled');
  $('#back').addEventListener('click', closeCat);
  $('#detail').scrollIntoView?.({ behavior: 'smooth', block: 'start' });
}

function closeCat() {
  document.body.classList.remove('drilled');
  $('#detail').innerHTML = '';
  $('#map').scrollIntoView?.({ behavior: 'smooth', block: 'start' });
}

function main(data) {
  DATA = data.segments;
  if (!DATA) {
    $('#map').innerHTML = '<p class="sec-note">No segment data in this aggregate — run data/scripts/add_segments.py.</p>';
    return;
  }
  $('#total').textContent = money(DATA.total);
  $('#window').textContent = DATA.window;
  renderMap();

  const go = (e) => {
    const t = e.target.closest('[data-cat]');
    if (t) openCat(t.dataset.cat);
  };
  $('#map').addEventListener('click', go);
  $('#legend').addEventListener('click', go);
  $('#map').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(e); }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.body.classList.contains('drilled')) closeCat();
  });

  $('#gen-at').textContent = new Date(data.generated_at).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

requireAuth().then(main);
