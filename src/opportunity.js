/*
 * Market Opportunity — where the unmet need is, and where it only looks unmet.
 *
 * Four views, in the order a founder actually needs them:
 *   1. the board reading the same data from four incompatible angles
 *   2. a White Space Finder: every audience x flavor cell, scored on headroom
 *   3. the graveyard — cells that look empty because the market rejected them
 *   4. a verdict, with the base rates that argue against it stated next to it
 *
 * Headroom is revenue per SKU. A cell with $25M across 33 SKUs is a better place
 * to launch than one with $80M across 86, because the second is already fought
 * over. That single ratio is what the matrix is coloured by.
 *
 * Reads the nginx-guarded aggregate; `audiences.opportunity` comes from
 * data/scripts/add_audiences.py.
 */
import '@fontsource-variable/inter';
import './dashboard.css';
import './audience.css';
import './opportunity.css';
import { hBars } from './charts.js';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const money = (n) =>
  n >= 1e9 ? '$' + (n / 1e9).toFixed(2) + 'B' :
  n >= 1e6 ? '$' + (n / 1e6).toFixed(1) + 'M' :
  n >= 1e3 ? '$' + (n / 1e3).toFixed(0) + 'K' : '$' + Math.round(n);
const pct = (v) => (v >= 0 ? '+' : '') + Math.round(v) + '%';

let O, WHO;

/* ------------------------------------------------------------------ board --- */
function board() {
  $('#board').innerHTML = O.board.map((b) => `
    <article class="bd-card" style="--c:${b.color}">
      <header>
        <span class="bd-av" aria-hidden="true">${b.avatar}</span>
        <div>
          <h3>${esc(b.name)}</h3>
          <p class="bd-role">${esc(b.role)}</p>
        </div>
      </header>
      <ul class="bd-says">${b.says.map((s) => `<li>${esc(s)}</li>`).join('')}</ul>
    </article>`).join('');

  $('#debate').innerHTML = O.debate.map((d, i) => `
    <section class="db-block">
      <h3 class="db-q"><span class="db-n mono">${String(i + 1).padStart(2, '0')}</span>${esc(d.q)}</h3>
      <div class="db-views">
        ${d.views.map((v) => {
          const p = WHO[v.who];
          return `<div class="db-view" style="--c:${p.color}">
            <span class="db-who mono"><i>${p.avatar}</i>${esc(p.name)}</span>
            <p>${esc(v.text)}</p></div>`;
        }).join('')}
      </div>
      <p class="db-resolve"><b class="mono">WHERE THAT LANDS →</b> ${esc(d.resolve)}</p>
    </section>`).join('');
}

/* --------------------------------------------------- white space matrix ----- */
/*
 * Colour = revenue per SKU against the category median (headroom per entrant).
 * Size of the number = revenue. An empty cell is genuinely empty; a pale cell
 * with many SKUs is crowded, which is the opposite of an opportunity.
 */
function matrix() {
  const med = O.medRPS || 1;
  const cell = (c) => {
    if (!c.rev) return `<td class="mx-cell mx-empty" title="No measured sales">·</td>`;
    const head = c.rps / med;
    const a = Math.min(1, head / 4);
    const grow = c.cagr == null ? '' :
      `<i class="mx-g ${c.cagr >= 0 ? 'up' : 'down'}">${pct(c.cagr)}</i>`;
    return `<td class="mx-cell" style="--a:${a.toFixed(2)}"
      title="${esc(c.fam)} — ${money(c.rev)} across ${c.skus} SKUs · ${money(c.rps)} per SKU (${head.toFixed(1)}x median)${
        c.cagr == null ? '' : ` · ${pct(c.cagr)} a year`}">
      <b>${money(c.rev)}</b><span class="mx-s">${c.skus} SKU</span>${grow}</td>`;
  };
  $('#matrix').innerHTML = `<table class="intel-table mono mx-table">
    <thead><tr><th class="tl">AUDIENCE</th>
      ${O.fams.map((f) => `<th class="mx-h"><span>${esc(f)}</span></th>`).join('')}</tr></thead>
    <tbody>${O.matrix.map((r) => `<tr>
      <td class="tl mx-aud">${esc(r.aud)}</td>
      ${r.row.map(cell).join('')}</tr>`).join('')}</tbody></table>`;
}

function ranked() {
  $('#under').innerHTML = O.under.map((c, i) => `
    <li class="op-row">
      <span class="op-rank mono">${String(i + 1).padStart(2, '0')}</span>
      <span class="op-cell">
        <b>${esc(c.aud)}</b>
        <span class="op-fam">${esc(c.fam)}</span>
      </span>
      <span class="op-nums mono">
        <i>${money(c.rev25)}</i> · ${c.skus} SKU ·
        <b class="op-head">${c.head}× median $/SKU</b>
        ${c.cagr2y == null ? '' : `· <b class="${c.cagr2y >= 0 ? 'up' : 'down'}">${pct(c.cagr2y)}/yr</b>`}
      </span>
    </li>`).join('');

  $('#untried').innerHTML = O.untried.map((g) => `
    <li>
      <b>${esc(g.aud)}</b> × <span>${esc(g.fam)}</span>
      <span class="mono dim">${g.skus} SKU ever · flavour proven elsewhere ·
        implied ${money(g.exp)} if this audience indexed like the category</span>
    </li>`).join('');

  $('#failed').innerHTML = O.failed.map((g) => `
    <li>
      <b>${esc(g.aud)}</b> × <span>${esc(g.fam)}</span>
      <span class="mono dim">${g.skus} SKUs tried · only ${money(g.cur)} — the market answered</span>
    </li>`).join('');

  /* Stated demand, as a cross-check on anything the sales data suggests. */
  $('#concepts').innerHTML = hBars(
    O.concepts.map((c, i) => ({
      label: c.concept.split(' (')[0].slice(0, 34),
      value: c.pct,
      color: i === 0 ? '#0071e3' : undefined,
    })),
    { fmt: (v) => v + '%', labelW: 230, accent: '#c7c7cc' }
  );
}


/* ------------------------------------------------------- e-commerce signal --- */
/*
 * The Amazon scrape is too narrow to measure share — four search terms — so it is
 * used qualitatively: which *kinds* of brand exist online that never reach a
 * convenience cooler, and which claims appear in the copy. Both bear directly on
 * the white space, and both come from a source independent of PDI and Mintel.
 */
function ecom() {
  const E = O.ecom;
  if (!E) return;
  $('#ecom-brands').innerHTML = E.absent.map((a) => `
    <li><b>${esc(a.b)}</b> <span class="ec-fmt mono">${esc(a.fmt)}</span>
      <span class="mono dim">${esc(a.t)}</span></li>`).join('');

  const max = Math.max(...E.claims.map((c) => c.n), 1);
  $('#ecom-claims').innerHTML = E.claims.map((c) => `
    <li>
      <span class="ec-c">${esc(c.c)}</span>
      <span class="ec-bar" style="width:${Math.max(1.5, (c.n / max) * 100)}%;
        ${c.n === 0 ? 'background:#c0392b;min-width:3px' : ''}"></span>
      <b class="mono ${c.n === 0 ? 'down' : ''}">${c.n}</b>
    </li>`).join('');

  $('#ecom-caveat').textContent = E.caveat;
  $('#ecom-n').textContent = `${E.n_absent} of ${E.n_brands}`;
}

function verdict() {
  const v = O.verdict;
  $('#verdict').innerHTML = `
    <p class="vd-head">${esc(v.headline)}</p>
    <div class="vd-grid">
      ${v.why.map(([k, t]) => `<div class="vd-item">
        <span class="vd-k mono">${esc(k)}</span><p>${esc(t)}</p></div>`).join('')}
    </div>
    <h4 class="vd-risk-h mono">WHAT ARGUES AGAINST IT</h4>
    <ul class="vd-risks">${v.risks.map((r) => `<li>${esc(r)}</li>`).join('')}</ul>`;
}

function main(data) {
  O = data.audiences && data.audiences.opportunity;
  if (!O) {
    $('#board').innerHTML =
      '<p class="sec-note">No opportunity data in this aggregate — run data/scripts/add_audiences.py.</p>';
    return;
  }
  WHO = Object.fromEntries(O.board.map((b) => [b.id, b]));
  board();
  matrix();
  ranked();
  ecom();
  verdict();
  $('#gen-at').textContent =
    new Date(data.generated_at).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

requireAuth().then(main);
