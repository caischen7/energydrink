/*
 * Target Audience — who the category actually sells to.
 *
 * A donut of category revenue split across the nine audiences, with a hover
 * card carrying the numbers that don't fit on a slice (age, gender, SKUs,
 * revenue, share), and a drill-down into the brands and products behind each.
 *
 * Reads the nginx-guarded aggregate; the `audiences` key is written by
 * data/scripts/add_audiences.py.
 */
import '@fontsource-variable/inter';
import './dashboard.css';
import './audience.css';
import { donut } from './charts.js';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const money = (n) =>
  n >= 1e9 ? '$' + (n / 1e9).toFixed(2) + 'B' :
  n >= 1e6 ? '$' + (n / 1e6).toFixed(1) + 'M' :
  n >= 1e3 ? '$' + (n / 1e3).toFixed(0) + 'K' : '$' + Math.round(n);
const int = (n) => (n == null ? '—' : Math.round(n).toLocaleString('en-US'));

/* Distinct hues, ordered so the two biggest slices don't sit adjacent in tone. */
const COLOR = [
  '#0071e3', '#34c759', '#ff9f0a', '#5e5ce6',
  '#ff375f', '#00a5a5', '#8e5cd9', '#c76b1e', '#86868b',
];

let DATA;
const colorOf = (name) => COLOR[DATA.auds.findIndex((a) => a.name === name) % COLOR.length];

/* ---------------------------------------------------------------- hover card */
/* Whole-market rows, appended to the card so hovering either demand donut shows
   the figure that donut is actually drawn from — not just the c-store numbers. */
function demandRows(name) {
  const D = DATA.demand;
  if (!D) return '';
  const now = D.now.auds.find((a) => a.name === name);
  const fut = D.future.auds.find((a) => a.name === name);
  if (!now || !fut) return '';
  const cagr = D.cagr[name];
  return `<dl class="tip-grid tip-grid--demand">
      <div><dt>US demand 2025</dt><dd>${money(now.usd * 1e6)} · ${now.share}%</dd></div>
      <div><dt>Projected 2030</dt><dd>${money(fut.usd * 1e6)} · ${fut.share}%</dd></div>
      <div><dt>$ growth /yr</dt><dd class="${cagr >= 0 ? 'up' : 'down'}">${
        cagr == null ? '—' : (cagr >= 0 ? '+' : '') + cagr + '%'}</dd></div>
      <div><dt>Share shift</dt><dd class="${fut.share >= now.share ? 'up' : 'down'}">${
        (fut.share - now.share >= 0 ? '+' : '') + (fut.share - now.share).toFixed(1)}pp</dd></div>
    </dl>`;
}

function showTip(name, ev) {
  const a = DATA.auds.find((x) => x.name === name);
  if (!a) return;
  const tip = $('#tip');
  tip.innerHTML = `
    <div class="tip-head" style="--c:${colorOf(name)}">
      <span class="tip-dot"></span><b>${esc(a.name)}</b>
    </div>
    <dl class="tip-grid">
      <div><dt>Age</dt><dd>${esc(a.age)}</dd></div>
      <div><dt>Gender</dt><dd>${esc(a.gender)}</dd></div>
      <div><dt>Share</dt><dd>${a.share}%</dd></div>
      <div><dt>Revenue</dt><dd>${money(a.rev)}</dd></div>
      <div><dt>SKUs</dt><dd>${int(a.skus)}</dd></div>
      <div><dt>Brands</dt><dd>${int(a.brandN)}</dd></div>
    </dl>
    ${demandRows(name)}
    <p class="tip-note">${esc(a.note)}</p>
    <p class="tip-cta mono">Click for brands &amp; products →</p>`;
  tip.hidden = false;
  moveTip(ev);
}

function moveTip(ev) {
  const tip = $('#tip');
  if (tip.hidden) return;
  /* Position against the viewport, then pull back inside it — near the right or
     bottom edge an unclamped card would hang off-screen. */
  const pad = 14;
  const r = tip.getBoundingClientRect();
  let x = ev.clientX + pad;
  let y = ev.clientY + pad;
  if (x + r.width > window.innerWidth - 8) x = ev.clientX - r.width - pad;
  if (y + r.height > window.innerHeight - 8) y = ev.clientY - r.height - pad;
  tip.style.transform = `translate(${Math.max(8, x)}px, ${Math.max(8, y)}px)`;
}

const hideTip = () => { $('#tip').hidden = true; };

/* ------------------------------------------------------------------- render */
function renderChart() {
  const rows = DATA.auds.map((a) => ({ label: a.name, value: a.rev, color: colorOf(a.name) }));
  $('#pie').innerHTML = donut(rows, {
    fmt: money,
    centerValue: money(DATA.total),
    centerLabel: 'C-STORE SALES 2016–2026',
  });

  $('#legend').innerHTML = DATA.auds.map((a) => `
    <button class="lg-item" data-aud="${esc(a.name)}">
      <i style="background:${colorOf(a.name)}"></i>
      <span class="lg-n">${esc(a.name)}</span>
      <span class="lg-meta mono">${esc(a.age)} · ${esc(a.gender)}</span>
      <span class="lg-v mono">${a.share}%</span>
    </button>`).join('');
}

/* ------------------------------------------------- demand: today vs 2030 ---- */
/*
 * The same nine audiences at whole-market scale. `auds` above is convenience
 * sell-through only; these two are all channels, so the shares differ — that
 * gap is the point, and the comparison table below makes it explicit.
 */
function renderDemand() {
  const D = DATA.demand;
  if (!D) return;

  const draw = (host, block) => {
    const rows = block.auds.map((a) => ({
      label: a.name, value: a.usd, color: colorOf(a.name),
    }));
    $(host).innerHTML = `
      <h3 class="dm-h">${esc(block.label)}</h3>
      <p class="dm-sub">${esc(block.sub)}</p>
      ${donut(rows, {
        size: 420,
        thickness: 96,
        fmt: (v) => money(v * 1e6),
        centerValue: money(block.market * 1e6),
        centerLabel: 'US MARKET',
      })}
      <ul class="dm-legend">
        ${block.auds.filter((a) => a.share >= 0.15).map((a) => `
          <li data-aud="${esc(a.name)}">
            <i style="background:${colorOf(a.name)}"></i>
            <span>${esc(a.name)}</span>
            <b class="mono">${a.share}%</b>
          </li>`).join('')}
      </ul>`;
  };

  draw('#pie-now', D.now);
  draw('#pie-future', D.future);

  /* Why the three rings differ — two distinct causes, kept separate on purpose. */
  const deltaList = (items, withWhy) => items.map((r) => `
    <li class="dl-row" data-aud="${esc(r.name)}">
      <i style="background:${colorOf(r.name)}"></i>
      <span class="dl-n">${esc(r.name)}</span>
      <span class="dl-m mono">${r.from}% → <b>${r.to}%</b></span>
      <span class="dl-d mono ${r.d >= 0 ? 'up' : 'down'}">${r.d >= 0 ? '+' : ''}${r.d}pp</span>
      ${withWhy && r.why ? `<p class="dl-why">${esc(r.why)}</p>` : ''}
    </li>`).join('');

  $('#delta-channel').innerHTML = deltaList(D.deltas.channel, true);
  $('#delta-time').innerHTML = deltaList(D.deltas.time, false);

  /* Where the two channels disagree — the evidence behind the whole-market split. */
  $('#channel-table').innerHTML = `<table class="intel-table mono">
    <thead><tr><th class="tl">AUDIENCE</th><th>CONVENIENCE<br /><span class="th-s">PDI measured</span></th>
      <th>MULTI-OUTLET<br /><span class="th-s">Mintel MULO</span></th>
      <th>ALL CHANNELS<br /><span class="th-s">2025 blended</span></th>
      <th>2030<br /><span class="th-s">projected</span></th>
      <th>$ CAGR<br /><span class="th-s">25→30</span></th></tr></thead>
    <tbody>${D.pdi_vs_mulo.map((r) => {
      const now = D.now.auds.find((a) => a.name === r.name);
      const fut = D.future.auds.find((a) => a.name === r.name);
      const cagr = DATA.demand.cagr[r.name];
      return `<tr data-aud="${esc(r.name)}">
        <td class="tl"><span class="dot" style="background:${colorOf(r.name)}"></span>${esc(r.name)}</td>
        <td>${r.pdi}%</td><td>${r.mulo}%</td><td><b>${now.share}%</b></td>
        <td>${fut.share}%</td>
        <td class="${cagr >= 0 ? 'up' : 'down'}">${cagr == null ? '—' : (cagr >= 0 ? '+' : '') + cagr + '%'}</td>
      </tr>`;
    }).join('')}</tbody></table>`;

  $('#why').innerHTML = D.future.auds.map((a) => `
    <article class="why-card" style="--c:${colorOf(a.name)}">
      <header>
        <h4>${esc(a.name)}</h4>
        <span class="why-move mono">${D.now.auds.find((x) => x.name === a.name).share}%
          → <b>${a.share}%</b></span>
      </header>
      <p>${esc(D.why[a.name] || '')}</p>
    </article>`).join('');
}

/* ------------------------------------------------- category-wide flavor mix -- */
function renderFlavors() {
  const F = DATA.flavors;
  if (!F) return;
  const rows = F.fams.map((f, i) => ({
    label: f.f, value: f.r, color: FLAVOR_COLOR[i % FLAVOR_COLOR.length],
  }));
  $('#pie-flavor').innerHTML = donut(rows, {
    size: 440, thickness: 100, fmt: money, minLabelPct: 6,
    centerValue: money(F.total_known),
    centerLabel: 'SALES WITH KNOWN FLAVOR',
  });
  $('#flavor-legend').innerHTML = F.fams.map((f, i) => `
    <li><i style="background:${FLAVOR_COLOR[i % FLAVOR_COLOR.length]}"></i>
      <span>${esc(f.f)}</span><b class="mono">${f.share}%</b>
      <span class="fl-n mono">${int(f.n)} SKU</span></li>`).join('');

  /* Flavor share by audience — the cross-tab that shows preferences actually differ. */
  const auds = DATA.auds.filter((a) => (a.flav || []).length);
  const fams = F.fams.slice(0, 8).map((f) => f.f);
  $('#flavor-matrix').innerHTML = `<table class="intel-table mono">
    <thead><tr><th class="tl">AUDIENCE</th>
      ${fams.map((f) => `<th>${esc(f.split(' ')[0])}</th>`).join('')}</tr></thead>
    <tbody>${auds.map((a) => `<tr data-aud="${esc(a.name)}">
      <td class="tl"><span class="dot" style="background:${colorOf(a.name)}"></span>${esc(a.name)}</td>
      ${fams.map((f) => {
        const hit = a.flav.find((x) => x.f === f);
        const v = hit ? hit.share : 0;
        /* Shade by intensity so the pattern reads without reading every number. */
        return `<td class="heat" style="--a:${Math.min(1, v / 45).toFixed(2)}">${
          v ? v + '%' : '·'}</td>`;
      }).join('')}</tr>`).join('')}</tbody></table>`;

}

function renderTable() {
  $('#aud-table').innerHTML = `<table class="intel-table mono">
    <thead><tr>
      <th class="tl">AUDIENCE</th><th class="tl">AGE</th><th class="tl">GENDER</th>
      <th>SKUS</th><th>BRANDS</th><th>REVENUE</th><th>SHARE</th>
    </tr></thead>
    <tbody>${DATA.auds.map((a) => `<tr data-aud="${esc(a.name)}">
      <td class="tl"><span class="dot" style="background:${colorOf(a.name)}"></span>${esc(a.name)}</td>
      <td class="tl">${esc(a.age)}</td><td class="tl">${esc(a.gender)}</td>
      <td>${int(a.skus)}</td><td>${int(a.brandN)}</td>
      <td>${money(a.rev)}</td><td>${a.share}%</td></tr>`).join('')}</tbody>
  </table>`;
}

/* ------------------------------------------------------- SKU table (sortable) */
/*
 * The whole SKU list ships in the aggregate, so sorting and filtering are local —
 * no refetch. Default view is the top 12 by revenue; "Show all" lifts the cap.
 */
const SKU_COLS = [
  { key: 'd', label: 'PRODUCT', tl: true, fmt: (p) => esc(p.d) },
  { key: 'b', label: 'BRAND', tl: true, fmt: (p) => esc(p.b) },
  { key: 'fl', label: 'FLAVOR', tl: true, fmt: (p) => esc(p.fl) || '—' },
  { key: 'ff', label: 'FAMILY', tl: true, fmt: (p) => esc(p.ff) },
  { key: 'sz', label: 'SIZE', tl: true, fmt: (p) => esc(p.sz) || '—' },
  { key: 'st', label: 'STORES', fmt: (p) => int(p.st) },
  { key: 'r', label: 'REVENUE', fmt: (p) => money(p.r) },
  { key: 'last', label: 'LAST SOLD', tl: true, fmt: (p) => esc(p.last) },
];
const skuState = { key: 'r', dir: -1, all: false, q: '' };

function renderSkus(a) {
  const q = skuState.q.trim().toLowerCase();
  let rows = a.prod;
  if (q) {
    rows = rows.filter((p) =>
      `${p.d} ${p.b} ${p.fl} ${p.ff} ${p.sz}`.toLowerCase().includes(q));
  }
  const total = rows.length;

  const { key, dir } = skuState;
  rows = [...rows].sort((x, y) => {
    const xv = x[key];
    const yv = y[key];
    /* Size sorts as a number ("8.4 OZ" < "16 OZ"); everything else by type. */
    if (key === 'sz') return dir * ((parseFloat(xv) || 0) - (parseFloat(yv) || 0));
    if (typeof xv === 'number') return dir * (xv - yv);
    return dir * String(xv).localeCompare(String(yv));
  });

  const shown = skuState.all ? rows : rows.slice(0, 12);

  $('#sku-table').innerHTML = `
    <thead><tr>${SKU_COLS.map((c) => `
      <th class="${c.tl ? 'tl' : ''} ${c.key === key ? 'sorted' : ''}" data-sk="${c.key}"
          role="button" tabindex="0" aria-sort="${
            c.key === key ? (dir < 0 ? 'descending' : 'ascending') : 'none'}">
        ${c.label}<i class="sort-caret">${c.key === key ? (dir < 0 ? '▼' : '▲') : ''}</i>
      </th>`).join('')}</tr></thead>
    <tbody>${shown.map((p) => `<tr>${SKU_COLS.map((c) => `
      <td class="${c.tl ? 'tl' : ''} ${c.key === 'd' ? 'pd' : ''}">${c.fmt(p)}</td>`).join('')}</tr>`).join('')}</tbody>`;

  $('#sku-note').textContent = skuState.all
    ? `Showing all ${int(total)} SKUs${q ? ' matching your filter' : ''}.`
    : `Showing ${int(shown.length)} of ${int(total)}${q ? ' matching' : ''} SKUs.`;
  $('#sku-all').textContent = skuState.all
    ? 'Show top 12 only'
    : `Show all ${int(total)} SKUs`;

  $$('#sku-table th').forEach((th) => {
    const go = () => {
      const k = th.dataset.sk;
      /* First click on a new column: numbers descend, text ascends. */
      skuState.dir = k === skuState.key ? -skuState.dir : (k === 'r' || k === 'st' ? -1 : 1);
      skuState.key = k;
      renderSkus(a);
    };
    th.addEventListener('click', go);
    th.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
    });
  });
  $('#sku-all').onclick = () => { skuState.all = !skuState.all; renderSkus(a); };
  const box = $('#sku-q');
  box.oninput = () => {
    skuState.q = box.value;
    renderSkus(a);
    $('#sku-q').focus();
  };
  box.value = skuState.q;
}

/* ------------------------------------------------------------ flavor donut --- */
function flavorBlock(a, col) {
  const fams = (a.flav || []).filter((f) => f.share >= 0.1);
  if (!fams.length) return '<p class="dt-note">No flavor data for this audience.</p>';
  const rows = fams.map((f, i) => ({
    label: f.f, value: f.r, color: FLAVOR_COLOR[i % FLAVOR_COLOR.length],
  }));
  const unk = a.flav_unknown || { r: 0, n: 0 };
  const top = fams[0];
  return `<div class="fl-wrap">
    <div class="fl-chart">${donut(rows, {
      size: 360, thickness: 84, fmt: money, minLabelPct: 7,
      centerValue: top.share + '%', centerLabel: top.f.toUpperCase(),
    })}</div>
    <ul class="fl-legend">
      ${fams.map((f, i) => `<li>
        <i style="background:${FLAVOR_COLOR[i % FLAVOR_COLOR.length]}"></i>
        <span>${esc(f.f)}</span>
        <b class="mono">${f.share}%</b>
        <span class="fl-n mono">${int(f.n)} SKU</span>
      </li>`).join('')}
    </ul>
  </div>
  <p class="dt-note">
    Share of this audience's revenue where the flavor is known.
    ${unk.n ? `${int(unk.n)} SKUs (${money(unk.r)}) carry no flavor in the product
    record — mostly bare "MONSTER" / "RED BULL" entries — and are excluded rather
    than guessed at.` : ''}
  </p>`;
}

const FLAVOR_COLOR = [
  '#0071e3', '#ff9f0a', '#34c759', '#ff375f', '#5e5ce6', '#00a5a5',
  '#8e5cd9', '#c76b1e', '#e0245e', '#1a8a3a', '#7d7d82', '#b38600',
  '#4a7ec7', '#9b5de5', '#86868b',
];

/* ------------------------------------------------------- audience switcher -- */
/*
 * Stays pinned at the top of the drill-down so you can move between audiences
 * without bouncing back to the full page. The ring is the same split as the
 * main chart; the active audience is opaque and the rest are dimmed, so it
 * doubles as a "you are here" marker.
 *
 * No handlers needed — the slices and chips carry data-aud, which the delegated
 * click listener in main() already routes to openAud().
 */
function switcher(active) {
  const rows = DATA.auds.map((a) => ({
    label: a.name,
    value: a.rev,
    color: colorOf(a.name),
  }));
  const cur = DATA.auds.find((a) => a.name === active);
  return `<div class="dt-switch">
    <div class="sw-chart">${donut(rows, {
      size: 200, thickness: 46, fmt: money, labels: false, active,
      centerValue: cur ? cur.share + '%' : '',
      centerLabel: 'OF SALES',
    })}</div>
    <div class="sw-side">
      <p class="sw-h mono">JUMP TO ANOTHER AUDIENCE</p>
      <div class="sw-chips">
        ${DATA.auds.map((a) => `
          <button class="sw-chip${a.name === active ? ' on' : ''}" data-aud="${esc(a.name)}">
            <i style="background:${colorOf(a.name)}"></i>${esc(a.name)}
            <b class="mono">${a.share}%</b>
          </button>`).join('')}
      </div>
    </div>
  </div>`;
}

function openAud(name) {
  const a = DATA.auds.find((x) => x.name === name);
  if (!a) return;
  const col = colorOf(name);
  const maxBrand = Math.max(...a.top.map((b) => b.r), 1);

  $('#detail').innerHTML = `
    ${switcher(name)}
    <div class="dt-head" style="--c:${col}">
      <button class="dt-back mono" id="back">← All audiences</button>
      <h2>${esc(a.name)}</h2>
      <p class="dt-who">${esc(a.age)} · ${esc(a.gender)}</p>
      <p class="dt-desc">${esc(a.note)}</p>
      <div class="dt-kpis">
        <div><span class="n">${a.share}%</span><span class="l mono">OF CATEGORY SALES</span></div>
        <div><span class="n">${money(a.rev)}</span><span class="l mono">LIFETIME REVENUE</span></div>
        <div><span class="n">${int(a.skus)}</span><span class="l mono">SKUS</span></div>
        <div><span class="n">${int(a.brandN)}</span><span class="l mono">BRANDS</span></div>
      </div>
    </div>
    <h3 class="dt-h mono">BRANDS SELLING TO THIS AUDIENCE</h3>
    <div class="dt-brands">
      ${a.top.map((b) => `<div class="br-row">
        <span class="br-n">${esc(b.b)}</span>
        <span class="br-bar" style="width:${Math.max(2, (b.r / maxBrand) * 100)}%;background:${col}"></span>
        <span class="br-v mono">${money(b.r)}</span></div>`).join('')}
    </div>
    <h3 class="dt-h mono">FLAVOR MIX</h3>
    ${flavorBlock(a, col)}
    <h3 class="dt-h mono">PRODUCTS</h3>
    <div class="sku-bar">
      <input type="search" id="sku-q" class="sku-q" placeholder="Filter by product, brand, flavor or size…"
             aria-label="Filter products" />
      <button class="sku-toggle mono" id="sku-all">Show all ${int(a.skus)} SKUs</button>
    </div>
    <div class="tbl-wrap"><table class="intel-table mono" id="sku-table"></table></div>
    <p class="dt-note" id="sku-note"></p>`;

  document.body.classList.add('drilled');
  Object.assign(skuState, { key: 'r', dir: -1, all: false, q: '' });
  renderSkus(a);
  $('#back').addEventListener('click', closeAud);
  $('#detail').scrollIntoView?.({ behavior: 'smooth', block: 'start' });
}

function closeAud() {
  document.body.classList.remove('drilled');
  $('#detail').innerHTML = '';
  $('#pie').scrollIntoView?.({ behavior: 'smooth', block: 'center' });
}

/* --------------------------------------------------------------------- boot */
function main(data) {
  DATA = data.audiences;
  if (!DATA) {
    $('#pie').innerHTML =
      '<p class="sec-note">No audience data in this aggregate — run data/scripts/add_audiences.py.</p>';
    return;
  }

  $('#total').textContent = money(DATA.total);
  $('#skus').textContent = int(DATA.skus);
  $('#brands').textContent = int(DATA.brands);
  $('#window').textContent = DATA.window;
  renderChart();
  renderDemand();
  renderFlavors();
  renderTable();

  /* One delegated set of handlers covers the slices, the legend and the table —
     every one of them carries data-aud. */
  const named = (e) => e.target.closest?.('[data-aud]');
  document.addEventListener('mouseover', (e) => {
    const t = named(e);
    if (t) showTip(t.dataset.aud, e); else if (!e.target.closest('#tip')) hideTip();
  });
  document.addEventListener('mousemove', (e) => { if (named(e)) moveTip(e); });
  document.addEventListener('click', (e) => {
    const t = named(e);
    if (t) { hideTip(); openAud(t.dataset.aud); }
  });
  /* Keyboard parity: slices and legend buttons are focusable. */
  document.addEventListener('focusin', (e) => {
    const t = named(e);
    if (!t) return hideTip();
    const r = t.getBoundingClientRect();
    showTip(t.dataset.aud, { clientX: r.left + r.width / 2, clientY: r.bottom });
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      hideTip();
      if (document.body.classList.contains('drilled')) closeAud();
    }
    if ((e.key === 'Enter' || e.key === ' ') && e.target.dataset?.aud) {
      e.preventDefault();
      openAud(e.target.dataset.aud);
    }
  });
  window.addEventListener('scroll', hideTip, { passive: true });

  $('#gen-at').textContent =
    new Date(data.generated_at).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

requireAuth().then(main);
