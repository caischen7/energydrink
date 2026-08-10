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
    centerLabel: 'TOTAL CATEGORY SALES',
  });

  $('#legend').innerHTML = DATA.auds.map((a) => `
    <button class="lg-item" data-aud="${esc(a.name)}">
      <i style="background:${colorOf(a.name)}"></i>
      <span class="lg-n">${esc(a.name)}</span>
      <span class="lg-meta mono">${esc(a.age)} · ${esc(a.gender)}</span>
      <span class="lg-v mono">${a.share}%</span>
    </button>`).join('');
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

function openAud(name) {
  const a = DATA.auds.find((x) => x.name === name);
  if (!a) return;
  const col = colorOf(name);
  const maxBrand = Math.max(...a.top.map((b) => b.r), 1);

  $('#detail').innerHTML = `
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
    <h3 class="dt-h mono">TOP PRODUCTS</h3>
    <div class="tbl-wrap"><table class="intel-table mono">
      <thead><tr><th class="tl">PRODUCT</th><th class="tl">BRAND</th><th class="tl">FLAVOR</th>
        <th class="tl">SIZE</th><th>STORES</th><th>REVENUE</th><th class="tl">LAST SOLD</th></tr></thead>
      <tbody>${a.prod.map((p) => `<tr>
        <td class="tl pd">${esc(p.d)}</td><td class="tl">${esc(p.b)}</td>
        <td class="tl">${esc(p.fl) || '—'}</td><td class="tl">${esc(p.sz) || '—'}</td>
        <td>${int(p.st)}</td><td>${money(p.r)}</td>
        <td class="tl">${esc(p.last)}</td></tr>`).join('')}</tbody>
    </table></div>
    <p class="dt-note">Top ${a.prod.length} of ${int(a.skus)} SKUs by lifetime revenue.</p>`;

  document.body.classList.add('drilled');
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
