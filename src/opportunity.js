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

let O, WHO, AUD, SKU;

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
  const cell = (c, _i, aud) => {
    if (!c.rev) return `<td class="mx-cell mx-empty" title="No measured sales">·</td>`;
    const head = c.rps / med;
    const a = Math.min(1, head / 4);
    /* 0.5 is measured, not chosen: it is the fill at which the deep green
       still clears 4.5:1. Past it the cell goes near-black. */
    const dk = a >= 0.5 ? ' mx-dark' : '';
    const grow = c.cagr == null ? '' :
      `<i class="mx-g ${c.cagr >= 0 ? 'up' : 'down'}">${pct(c.cagr)}</i>`;
    return `<td class="mx-cell mx-click${dk}" style="--a:${a.toFixed(2)}"
      role="button" tabindex="0" data-aud="${esc(aud)}" data-fam="${esc(c.fam)}"
      title="${esc(c.fam)} — ${money(c.rev)} across ${c.skus} SKUs · ${money(c.rps)} per SKU (${head.toFixed(1)}x median)${
        c.cagr == null ? '' : ` · ${pct(c.cagr)} a year`} — click for the SKUs behind it">
      <b>${money(c.rev)}</b><span class="mx-s">${c.skus} SKU</span>${grow}</td>`;
  };
  const sc = O.scaled;
  if (sc) {
    $('#mx-scope').textContent =
      sc.note + ' Flavor is unknown for 470 SKUs, which are excluded. Growth is the 2-year rate to 2025.';
    $('#mx-caveat').innerHTML = '<b>Not directly comparable:</b> ' + esc(sc.caveat);
  }
  $('#matrix').innerHTML = `<table class="intel-table mono mx-table">
    <thead><tr><th class="tl">AUDIENCE</th>
      ${O.fams.map((f) => `<th class="mx-h"><span>${esc(f)}</span></th>`).join('')}</tr></thead>
    <tbody>${O.matrix.map((r) => `<tr>
      <td class="tl mx-aud">${esc(r.aud)}</td>
      ${r.row.map((c, i) => cell(c, i, r.aud)).join('')}</tr>`).join('')}</tbody></table>`;

  /* Delegated so it survives a re-render, and keyboard-reachable — the cells
     are real controls now, not decoration. */
  const open = (el) => drill(el.dataset.aud, el.dataset.fam);
  $('#matrix').addEventListener('click', (e) => {
    const el = e.target.closest('.mx-click');
    if (el) open(el);
  });
  $('#matrix').addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const el = e.target.closest('.mx-click');
    if (el) { e.preventDefault(); open(el); }
  });
}

/* ------------------------------------------------------ cell drill-down ----- */
/*
 * A coloured cell says "this pocket has headroom". That is a claim you have to
 * act on, so it should be inspectable: which products are actually in there,
 * who owns them, what sizes they ship in, and whether the money is spread or
 * sitting in one incumbent. A cell reading 8x median because one SKU earns
 * everything is not an opening — it is somebody's franchise.
 *
 * Per-SKU price is deliberately absent: the aggregate carries revenue and
 * store counts, not shelf price. What the panel shows instead is the price
 * band that earns most per SKU *at the sizes present in this cell*, taken from
 * the price grid further down the page. That is a real number, correctly
 * labelled as being about the format rather than the individual product.
 */
let drillKey = null;

function priceContextFor(sizes) {
  const G = O.price_grid;
  if (!G) return '';
  const want = sizes.map((z) => String(z).toLowerCase().trim());
  const rows = G.grid.filter((r) => want.includes(r.size.toLowerCase().trim()));
  if (!rows.length) return '';
  return rows.map((r) => {
    const best = r.rows.filter((c) => c.skus >= 5).sort((a, b) => b.rps - a.rps)[0];
    if (!best) return `<li><b>${esc(r.size)}</b><span class="mono dim">too few SKUs priced to rank</span></li>`;
    return `<li><b>${esc(r.size)}</b><span class="mono">best rung ${esc(best.band)}</span>
      <span class="mono dim">${money(best.rps)} per SKU across ${best.skus}</span></li>`;
  }).join('');
}

function drill(aud, fam) {
  const host = $('#mx-drill');
  const key = `${aud}|${fam}`;
  if (drillKey === key) {                      /* click the same cell to close */
    drillKey = null;
    host.hidden = true;
    $$('.mx-click.on').forEach((e) => e.classList.remove('on'));
    return;
  }
  drillKey = key;
  $$('.mx-click').forEach((e) =>
    e.classList.toggle('on', e.dataset.aud === aud && e.dataset.fam === fam));

  const row = O.matrix.find((r) => r.aud === aud);
  const c = row && row.row.find((x) => x.fam === fam);
  const rows = (SKU[key] || []).slice().sort((a, b) => b.r - a.r);
  const med = O.medRPS || 1;
  const head = c && c.rps ? c.rps / med : 0;

  /* Concentration: what the single biggest SKU takes of the cell. */
  const tot = rows.reduce((t, p) => t + p.r, 0) || 1;
  const topShare = rows.length ? (rows[0].r / tot) * 100 : 0;

  const byBrand = {};
  const bySize = {};
  for (const p of rows) {
    byBrand[p.b] = (byBrand[p.b] || 0) + p.r;
    bySize[p.sz || '—'] = (bySize[p.sz || '—'] || 0) + p.r;
  }
  const brands = Object.entries(byBrand).sort((a, b) => b[1] - a[1]);
  const sizes = Object.entries(bySize).sort((a, b) => b[1] - a[1]);
  const brandShare = brands.length ? (brands[0][1] / tot) * 100 : 0;

  /* The read. Same rule the matrix colours by, stated in words. */
  const verdictText =
    !rows.length ? 'Nothing has ever shipped here that we can measure. Check the graveyard below before treating that as an opening — some cells are empty because the market rejected them.'
    : brandShare > 70 ? `One brand — ${brands[0][0]} — holds ${brandShare.toFixed(0)}% of this cell. The headroom number is that brand's franchise, not an unclaimed pocket.`
    : topShare > 60 ? `A single SKU carries ${topShare.toFixed(0)}% of the money here. The per-SKU average flatters the rest of the field.`
    : head >= 4 ? `Money is spread across ${brands.length} brands and no SKU dominates, and each product still earns ${head.toFixed(1)}x the category median. This is the shape a real opening has.`
    : `Revenue per SKU is ${head.toFixed(1)}x the median — at or below the point where the shelf is already competitive.`;

  host.hidden = false;
  host.innerHTML = `
    <div class="dr-head">
      <div>
        <p class="dr-eyebrow mono">WHAT IS ACTUALLY IN THIS CELL</p>
        <h3 class="dr-title">${esc(aud)} <span>&times;</span> ${esc(fam)}</h3>
      </div>
      <button class="dr-close mono" type="button" aria-label="Close">CLOSE &times;</button>
    </div>

    <div class="dr-kpis">
      <div><b>${c ? money(c.rev) : '$0'}</b><span class="mono">all-channel (scaled)</span></div>
      <div><b>${money(tot)}</b><span class="mono">measured (PDI)</span></div>
      <div><b>${rows.length || (c ? c.skus : 0)}</b><span class="mono">SKUs</span></div>
      <div><b>${c && c.rps ? money(c.rps) : '—'}</b><span class="mono">per SKU (scaled)</span></div>
      <div><b>${head ? head.toFixed(1) + '\u00d7' : '—'}</b><span class="mono">vs median</span></div>
      <div><b class="${c && c.cagr >= 0 ? 'up' : 'down'}">${c && c.cagr != null ? pct(c.cagr) : '—'}</b><span class="mono">a year</span></div>
    </div>

    <p class="dr-scale mono">TWO SCALES, DELIBERATELY SIDE BY SIDE — the matrix colours by
      <b>all-channel</b> dollars, lifted from the convenience flavour mix using this audience's
      Passport share. Everything below (brands, sizes, the SKU table) is <b>measured PDI</b>
      revenue over the full window. They are different quantities and are not meant to add up;
      shares below are computed within the measured figure.</p>

    <p class="dr-read"><b class="mono">THE READ &rarr;</b> ${esc(verdictText)}</p>

    <div class="dr-cols">
      <section>
        <h4 class="mono">WHO OWNS IT</h4>
        <ul class="dr-list">${brands.slice(0, 8).map(([b, r]) => `
          <li><b>${esc(b)}</b>
            <span class="dr-track"><i style="width:${((r / tot) * 100).toFixed(1)}%"></i></span>
            <span class="mono dim">${money(r)} · ${((r / tot) * 100).toFixed(0)}%</span></li>`).join('')
          || '<li class="dim">No measured sales.</li>'}</ul>
      </section>
      <section>
        <h4 class="mono">SIZES THAT SELL</h4>
        <ul class="dr-list">${sizes.slice(0, 6).map(([z, r]) => `
          <li><b>${esc(z)}</b>
            <span class="dr-track"><i style="width:${((r / tot) * 100).toFixed(1)}%"></i></span>
            <span class="mono dim">${money(r)} · ${((r / tot) * 100).toFixed(0)}%</span></li>`).join('')
          || '<li class="dim">No measured sales.</li>'}</ul>
      </section>
      <section>
        <h4 class="mono">PRICE, BY FORMAT</h4>
        <ul class="dr-list dr-price">${priceContextFor(sizes.map(([z]) => z))
          || '<li class="dim">No priced format overlaps this cell.</li>'}</ul>
        <p class="dr-fine">Shelf price is not carried per SKU in this dataset. These are the
          best-earning price rungs for the formats present here, from the grid below.</p>
      </section>
    </div>

    <h4 class="mono dr-tbl-h">EVERY SKU IN THIS CELL <span class="dim">(${rows.length})</span></h4>
    <div class="tbl-wrap"><table class="intel-table mono dr-tbl">
      <thead><tr>
        <th class="tl">PRODUCT</th><th class="tl">BRAND</th><th class="tl">FLAVOR</th>
        <th class="tl">SIZE</th><th>STORES</th><th>REVENUE</th><th>SHARE</th><th class="tl">LAST SEEN</th>
      </tr></thead>
      <tbody>${rows.map((p) => `<tr>
        <td class="tl dr-p" title="${esc(p.d)}">${esc(p.d)}</td>
        <td class="tl">${esc(p.b)}</td>
        <td class="tl">${esc(p.fl || '—')}</td>
        <td class="tl">${esc(p.sz || '—')}</td>
        <td>${(p.st || 0).toLocaleString()}</td>
        <td>${money(p.r)}</td>
        <td>${((p.r / tot) * 100).toFixed(1)}%</td>
        <td class="tl">${esc(p.last || '—')}</td></tr>`).join('')
        || '<tr><td colspan="8" class="tl dim">No SKUs recorded for this pairing.</td></tr>'}</tbody>
    </table></div>`;

  $('.dr-close', host).addEventListener('click', () => drill(aud, fam));
  host.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
      /* Mintel concept strings are full sentences; keep the distinguishing head. */
      label: c.concept.split(' (')[0]
        .replace(/^Offers additional /, '')
        .replace(/^Made with /, '')
        .replace(/^Infused with /, '')
        .replace(/^Products with /, '')
        .replace(/^Available in /, '')
        .replace(/^Limited-edition /, 'LTO ')
        .replace(/^Customizable energy.*/, 'Customizable caffeine')
        .replace(/^(\w)/, (m) => m.toUpperCase()),
      value: c.pct,
      /* The top concept keeps the full accent; the rest step back a shade.
         They must NOT use the track's own grey, or the bar vanishes into it. */
      color: i === 0 ? '#0071e3' : '#7fb4ee',
    })),
    { fmt: (v) => v + '%', labelW: 230 }
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


/* ------------------------------------------------------ price x size grid --- */
/*
 * The one chart on this site that changes a number in the launch spec.
 *
 * Pooled across formats the best-yielding price rung looks like $3.00-3.49, but
 * that is 12oz economics leaking through the pool. Held at 16 oz — the can this
 * brand actually sells — the ranking inverts. Colour is revenue per SKU, so a
 * dense cell means each product there earns more, not that the cell is bigger.
 */
function priceGrid() {
  const G = O.price_grid;
  if (!G) return;
  const cells = G.grid.flatMap((r) => r.rows.filter((c) => c.skus >= 5).map((c) => c.rps));
  const max = Math.max(...cells, 1);
  const ours = G.our_size;

  $('#pg-table').innerHTML = `<table class="intel-table mono mx-table">
    <thead><tr><th class="tl">CAN SIZE</th>
      ${G.bands.map((b) => `<th class="mx-h"><span>${esc(b)}</span></th>`).join('')}
      <th>TOTAL</th></tr></thead>
    <tbody>${G.grid.map((r) => `<tr class="${r.size === ours ? 'pg-ours' : ''}">
      <td class="tl mx-aud">${esc(r.size)}${r.size === ours ? ' <b class="pg-tag">our can</b>' : ''}</td>
      ${r.rows.map((c) => {
        if (!c.skus) return '<td class="mx-cell mx-empty">·</td>';
        const a = c.skus >= 5 ? Math.min(1, c.rps / max) : 0.06;
        const dk = a >= 0.5 ? ' mx-dark' : '';
        return `<td class="mx-cell${dk}" style="--a:${a.toFixed(2)}"
          title="${esc(r.size)} at ${esc(c.band)} — ${money(c.rev)} across ${c.skus} SKUs, ${money(c.rps)} per SKU">
          <b>${money(c.rps)}</b><span class="mx-s">${c.skus} SKU · ${money(c.rev)}</span></td>`;
      }).join('')}
      <td class="mx-cell mx-tot">${money(r.tot)}</td></tr>`).join('')}</tbody></table>`;

  const b = G.best;
  $('#pg-compare').innerHTML = Object.entries(b).map(([size, x]) => `
    <div class="pg-card ${size === ours ? 'on' : ''}">
      <span class="pg-size mono">${esc(size)}${size === ours ? ' — OUR FORMAT' : ''}</span>
      <p class="pg-best">Best rung: <b>${esc(x.band)}</b></p>
      <p class="pg-rps">${money(x.rps)} <span>per SKU</span></p>
      <p class="pg-vs mono">vs ${esc(x.next)} at ${money(x.next_rps)} — ${x.delta_pct >= 0 ? '+' : ''}${x.delta_pct}%</p>
    </div>`).join('');

  $('#pg-headline').textContent = G.headline;
  $('#pg-note').textContent = G.note;
  $('#pg-corridor').textContent = G.corridor_pct + '%';
}

function verdict() {
  const v = O.verdict;
  $('#verdict').innerHTML = `
    <p class="vd-head">${esc(v.headline)}</p>
    <div class="vd-grid">
      ${v.why.map(([k, t]) => `<div class="vd-item">
        <span class="vd-k mono">${esc(k)}</span><p>${esc(t)}</p></div>`).join('')}
    </div>
    ${v.price_correction ? `<div class="vd-fix">
      <h4 class="mono">A CORRECTION TO AN EARLIER VERSION OF THIS VERDICT</h4>
      <p class="vd-was">It previously read: &ldquo;${esc(v.price_correction.was)}&rdquo;</p>
      <p>${esc(v.price_correction.why)}</p>
      <div class="tbl-wrap"><table class="intel-table mono vd-tbl">
        <thead><tr><th class="tl">PER OUNCE</th><th class="tl">ON A 16 OZ CAN</th>
          <th>16 OZ REVENUE</th><th>SKUS</th><th>PER SKU</th></tr></thead>
        <tbody>${v.price_correction.oz16.map((r, i) => `<tr class="${i === 0 ? 'up' : i === 2 ? 'down' : ''}">
          <td class="tl">${esc(r.band)}</td><td class="tl">${esc(r.can)}</td>
          <td>$${r.rev}M</td><td>${r.skus}</td><td>$${r.rps.toFixed(2)}M</td></tr>`).join('')}</tbody>
      </table></div>
    </div>` : ''}
    <h4 class="vd-risk-h mono">WHAT ARGUES AGAINST IT</h4>
    <ul class="vd-risks">${v.risks.map((r) => `<li>${esc(r)}</li>`).join('')}</ul>`;
}

function main(data) {
  O = data.audiences && data.audiences.opportunity;
  AUD = (data.audiences && data.audiences.auds) || [];
  /* Every SKU already carries its audience and flavour family, so the cell
     drill-down is an index over data we ship, not another query. */
  SKU = {};
  for (const a of AUD) {
    for (const p of a.prod || []) (SKU[`${a.name}|${p.ff || 'Unknown'}`] ||= []).push(p);
  }
  if (!O) {
    $('#board').innerHTML =
      '<p class="sec-note">No opportunity data in this aggregate — run data/scripts/add_audiences.py.</p>';
    return;
  }
  /* Board hues arrive from the aggregate and are painted as names on white.
     The pastel iOS set measured ~2:1, so they are mapped to AA-safe siblings
     of the same hue rather than being re-picked. */
  const SAFE = {
    '#34c759': '#178037', '#ff9f0a': '#a35c00', '#00a5a5': '#00807f',
    '#ff375f': '#c9184a', '#5e5ce6': '#4b49c4', '#8e5cd9': '#7a4bc4',
    '#ff3b30': '#c0392b',
  };
  for (const b of O.board) b.color = SAFE[String(b.color).toLowerCase()] || b.color;
  WHO = Object.fromEntries(O.board.map((b) => [b.id, b]));
  board();
  matrix();
  ranked();
  ecom();
  priceGrid();
  verdict();
  $('#gen-at').textContent =
    new Date(data.generated_at).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

requireAuth().then(main);
