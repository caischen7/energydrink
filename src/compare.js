/*
 * 2025 vs 2030 — the same nine audiences, two points in time, side by side.
 *
 * The Audience page shows each year as its own ring, which is fine for reading a
 * single year but poor for comparison: you end up holding percentages in your
 * head. This page is built the other way round — every view here is a
 * difference, so the question it answers is "what changed, and how much".
 *
 * Reads the nginx-guarded aggregate; `audiences.demand` is written by
 * data/scripts/add_audiences.py.
 */
import '@fontsource-variable/inter';
import './dashboard.css';
import './audience.css';
import './compare.css';
import { slope, groupedBars, donut } from './charts.js';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
/* Values arrive in $M, so scale once here rather than at every call site. */
const money = (m) =>
  m >= 1000 ? '$' + (m / 1000).toFixed(m >= 10000 ? 1 : 2) + 'B' :
  m >= 1 ? '$' + m.toFixed(0) + 'M' : '$' + (m * 1000).toFixed(0) + 'K';
const pp = (v) => (v == null || !isFinite(v) ? '—' : (v >= 0 ? '+' : '') + v.toFixed(1) + 'pp');
/* Some audiences have a zero 2025 base after the Passport revision, so growth and
   CAGR are undefined rather than infinite — say so instead of throwing. */
const pct = (v) => (v == null || !isFinite(v) ? '—' : (v >= 0 ? '+' : '') + v.toFixed(1) + '%');

const COLOR = [
  '#0071e3', '#34c759', '#ff9f0a', '#5e5ce6',
  '#ff375f', '#00a5a5', '#8e5cd9', '#c76b1e', '#86868b',
];

let A, D, ROWS;
const colorOf = (n) => COLOR[A.auds.findIndex((x) => x.name === n) % COLOR.length];

/* One row per audience carrying both years and every derived difference, so no
   view has to recompute them. */
function buildRows() {
  const now = Object.fromEntries(D.now.auds.map((a) => [a.name, a]));
  const fut = Object.fromEntries(D.future.auds.map((a) => [a.name, a]));
  const added = D.future.market - D.now.market;
  return A.auds
    .map((a) => {
      const n = now[a.name];
      const f = fut[a.name];
      const add = f.usd - n.usd;
      return {
        name: a.name,
        age: a.age,
        gender: a.gender,
        color: colorOf(a.name),
        usd25: n.usd, usd30: f.usd, add,
        sh25: n.share, sh30: f.share, dsh: +(f.share - n.share).toFixed(1),
        growth: n.usd > 0 ? (f.usd / n.usd - 1) * 100 : null,
        cagr: D.cagr[a.name] == null ? null : D.cagr[a.name],
        contrib: (add / added) * 100,   // share of all category growth
        why: D.why[a.name] || '',
      };
    })
    .sort((x, y) => y.add - x.add);
}

/* ------------------------------------------------------------------ views --- */
function kpis() {
  const g = D.future.market - D.now.market;
  const cagr = ((D.future.market / D.now.market) ** (1 / 5) - 1) * 100;
  const top = ROWS[0];
  const cells = [
    ['US MARKET 2025', money(D.now.market), ''],
    ['US MARKET 2030', money(D.future.market), 'central forecast'],
    ['NEW DEMAND ADDED', money(g), pct((g / D.now.market) * 100) + ' over five years'],
    ['MARKET CAGR', pct(cagr), 'per year'],
    ['BIGGEST GAINER', top.name, money(top.add) + ' added'],
    ['ITS SHARE OF GROWTH', top.contrib.toFixed(0) + '%', 'of all new demand'],
  ];
  $('#kpis').innerHTML = cells
    .map(([l, v, s]) => `<div class="cmp-kpi">
      <span class="ck-v">${esc(v)}</span>
      <span class="ck-l mono">${esc(l)}</span>
      ${s ? `<span class="ck-s mono">${esc(s)}</span>` : ''}
    </div>`).join('');
}

function slopeView() {
  $('#slope').innerHTML = slope(
    ROWS.map((r) => ({ label: r.name, from: r.sh25, to: r.sh30, color: r.color })),
    { fmt: (v) => v.toFixed(1) + '%', leftTitle: '2025', rightTitle: '2030' }
  );
}

function barsView() {
  $('#bars').innerHTML = groupedBars(
    ROWS.map((r) => ({ label: r.name, a: r.usd25, b: r.usd30, color: r.color })),
    { fmt: money, aLabel: '2025', bLabel: '2030' }
  );
}

/* Where the $11.7B of new demand actually goes. */
function contribView() {
  const gain = ROWS.filter((r) => r.add > 0);
  $('#contrib').innerHTML = donut(
    gain.map((r) => ({ label: r.name, value: r.add, color: r.color })),
    {
      size: 420, thickness: 96, fmt: money, minLabelPct: 5,
      centerValue: money(D.future.market - D.now.market),
      centerLabel: 'NEW DEMAND 2025–2030',
    }
  );
  $('#contrib-legend').innerHTML = gain.map((r) => `
    <li data-aud="${esc(r.name)}">
      <i style="background:${r.color}"></i>
      <span>${esc(r.name)}</span>
      <b class="mono">${r.contrib.toFixed(1)}%</b>
      <span class="fl-n mono">${money(r.add)}</span>
    </li>`).join('');
}

const TABLE_COLS = [
  { k: 'name', l: 'AUDIENCE', tl: true, f: (r) => `<span class="dot" style="background:${r.color}"></span>${esc(r.name)}` },
  { k: 'usd25', l: '2025', f: (r) => money(r.usd25) },
  { k: 'usd30', l: '2030', f: (r) => money(r.usd30) },
  { k: 'add', l: 'Δ $', f: (r) => `<b class="${r.add >= 0 ? 'up' : 'down'}">${r.add >= 0 ? '+' : '−'}${money(Math.abs(r.add))}</b>` },
  { k: 'growth', l: 'GROWTH', f: (r) => `<span class="${r.growth == null ? '' : r.growth >= 0 ? 'up' : 'down'}">${pct(r.growth)}</span>` },
  { k: 'cagr', l: 'CAGR', f: (r) => `<span class="${r.cagr == null ? '' : r.cagr >= 0 ? 'up' : 'down'}">${pct(r.cagr)}</span>` },
  { k: 'sh25', l: 'SHARE 25', f: (r) => r.sh25 + '%' },
  { k: 'sh30', l: 'SHARE 30', f: (r) => r.sh30 + '%' },
  { k: 'dsh', l: 'Δ SHARE', f: (r) => `<span class="${r.dsh >= 0 ? 'up' : 'down'}">${pp(r.dsh)}</span>` },
  { k: 'contrib', l: '% OF GROWTH', f: (r) => r.contrib.toFixed(1) + '%' },
];
const tState = { k: 'add', dir: -1 };

function tableView() {
  const rows = [...ROWS].sort((x, y) => {
    const a = x[tState.k];
    const b = y[tState.k];
    /* nulls sort last regardless of direction */
    if (a == null && b == null) return 0;
    if (a == null) return 1;
    if (b == null) return -1;
    return typeof a === 'number' ? tState.dir * (a - b) : tState.dir * String(a).localeCompare(String(b));
  });
  $('#cmp-table').innerHTML = `<table class="intel-table mono">
    <thead><tr>${TABLE_COLS.map((c) => `
      <th class="${c.tl ? 'tl' : ''} ${c.k === tState.k ? 'sorted' : ''}" data-k="${c.k}"
          role="button" tabindex="0" aria-sort="${
            c.k === tState.k ? (tState.dir < 0 ? 'descending' : 'ascending') : 'none'}">
        ${c.l}<i class="sort-caret">${c.k === tState.k ? (tState.dir < 0 ? '▼' : '▲') : ''}</i></th>`).join('')}</tr></thead>
    <tbody>${rows.map((r) => `<tr data-aud="${esc(r.name)}">
      ${TABLE_COLS.map((c) => `<td class="${c.tl ? 'tl' : ''}">${c.f(r)}</td>`).join('')}</tr>`).join('')}</tbody>`;

  $$('#cmp-table th').forEach((th) => {
    const go = () => {
      const k = th.dataset.k;
      tState.dir = k === tState.k ? -tState.dir : (k === 'name' ? 1 : -1);
      tState.k = k;
      tableView();
    };
    th.addEventListener('click', go);
    th.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
    });
  });
}

function cardsView() {
  $('#cards').innerHTML = ROWS.map((r) => `
    <article class="cmp-card" style="--c:${r.color}">
      <header>
        <h3>${esc(r.name)}</h3>
        <span class="cc-meta mono">${esc(r.age)} · ${esc(r.gender)}</span>
      </header>
      <div class="cc-nums">
        <div><span class="l mono">2025</span><span class="v">${money(r.usd25)}</span></div>
        <div class="cc-arrow">→</div>
        <div><span class="l mono">2030</span><span class="v">${money(r.usd30)}</span></div>
        <div class="cc-delta ${r.add >= 0 ? 'up' : 'down'}">
          <span class="v">${r.add >= 0 ? '+' : '−'}${money(Math.abs(r.add))}</span>
          <span class="l mono">${r.cagr == null ? 'new segment' : pct(r.cagr) + '/yr'}</span>
        </div>
      </div>
      <div class="cc-share mono">
        share ${r.sh25}% → ${r.sh30}%
        <b class="${r.dsh >= 0 ? 'up' : 'down'}">${pp(r.dsh)}</b>
        · ${r.contrib >= 0 ? r.contrib.toFixed(1) + '% of all growth' : 'shrinking'}
      </div>
      <p>${esc(r.why)}</p>
    </article>`).join('');
}

/* ------------------------------------------------------------------- boot --- */
function main(data) {
  A = data.audiences;
  D = A && A.demand;
  if (!D) {
    $('#slope').innerHTML =
      '<p class="sec-note">No demand data in this aggregate — run data/scripts/add_audiences.py.</p>';
    return;
  }
  ROWS = buildRows();

  kpis();
  slopeView();
  barsView();
  contribView();
  tableView();
  cardsView();

  $('#band').textContent =
    `${money(D.band.low90)} – ${money(D.band.high90)}`;
  $('#gen-at').textContent =
    new Date(data.generated_at).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';

  /* Clicking any audience anywhere opens it on the Audience page. */
  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-aud]');
    if (t) window.location.href = `./audience.html#${encodeURIComponent(t.dataset.aud)}`;
  });
}

requireAuth().then(main);
