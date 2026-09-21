/*
 * Flavor by Year — which flavors sell, once the panel ramp is taken out.
 *
 * Reads `public/data/flavor_year.json`, built by
 * capstone/scripts/analyze_flavor_year.py from the PDI-derived price panel.
 *
 * FOUR CHART DECISIONS, AND WHY
 * -----------------------------
 * 1. THE RAMP CHART IS INDEXED TO 2019 = 100. Units and active-store counts
 *    share no unit. The alternative is a second y-axis, which lets whoever
 *    picks the two scales manufacture any gap they like. Indexing puts all
 *    three series on one axis, which is the only honest comparison available.
 *
 * 2. UNIT SHARE LEADS, not raw units. The panel grows 2.24x across the window;
 *    raw units grow 3.01x. Share is immune to that by construction - if the
 *    panel doubles, every family's units roughly double and the shares do not
 *    move - so it is the default ranking and the default trajectory metric.
 *
 * 3. FOURTEEN FAMILIES GET SMALL MULTIPLES, not fourteen lines. Past about
 *    eight series a shared axis is a hairball and colour stops identifying
 *    anything. Each family gets its own panel on its own scale: shapes
 *    comparable, levels deliberately not. The ranked bars carry the levels.
 *
 * 4. REACH x DEPTH IS A SCATTER, because it is a relationship and not a
 *    ranking. units-per-active-store = reach x depth exactly, so the two axes
 *    decompose one number rather than showing two unrelated ones.
 *
 * Series colours are the three already shipping on the explorer page; the
 * palette was checked for CVD separation and lightness band rather than
 * eyeballed. All three fall under 3:1 against the surface, which obliges
 * visible labels - hence direct labels on the ramp chart and the full table.
 */
import '@fontsource-variable/inter';
import './dashboard.css';
import './audience.css';
import './explorer.css';
import './flavors.css';
import { hBars, multiLine, scatter, slope, sparkGrid, fmtCompact } from './charts.js';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const num = (v) => Math.round(v).toLocaleString('en-US');
const pct = (v) => v.toFixed(2) + '%';

const ACCENT = '#0071e3';   // units / primary
const WARM = '#f77f00';     // store count
const VIOLET = '#c77dff';   // per-store velocity
/* Status pair, not categorical: these mean gained/lost, and they are the same
   two the POS momentum panel already uses. Reusing WARM here would have made
   one hue mean 'active stores' in the ramp chart and 'declining' in the slope
   chart, on the same page. Both ends carry a printed value, so direction is
   never conveyed by colour alone. */
const GAIN = '#34c759';
const LOSS = '#ff3b30';

const METRIC = {
  unit_share_pct: {
    label: 'Unit share', fmt: (v) => v.toFixed(2) + '%',
    note: 'Share of all energy-drink units sold in the panel that year. This is the ' +
          'headline popularity metric because it is unaffected by the panel growing: ' +
          'if PDI doubles its store count, every family’s raw units roughly double ' +
          'and the shares stay put.',
  },
  units_per_active_store: {
    label: 'Per active store', fmt: (v) => num(v),
    note: 'Annual units divided by the average number of stores active in the panel ' +
          'that year. A velocity measure — it answers how hard the family works in ' +
          'a typical store, rather than how many stores PDI happened to have.',
  },
  units_per_sku: {
    label: 'Per SKU', fmt: (v) => fmtCompact(v),
    note: 'Annual units divided by the family’s average lineup size. The control for ' +
          'shelf dominance: a family can lead on total units simply by having more ' +
          'facings, and this asks how hard the average SKU works instead.',
  },
};

let DATA, YEAR, MET = 'unit_share_pct';
let SORT = { key: 'unit_share_pct', dir: -1 };

const forYear = (y) => DATA.families.filter((r) => r.year === y);
const families = () => [...new Set(DATA.families.map((r) => r.cluster))].sort();

/* ------------------------------------------------------------------- KPIs */
function kpis() {
  const r = DATA.ramp;
  const last = forYear(YEAR).slice().sort((a, b) => b.unit_share_pct - a.unit_share_pct)[0];
  const top = DATA.movers[0];
  const rows = [
    ['Panel growth', r.active_stores_growth.toFixed(2) + '×', 'active stores, 2019–2025'],
    ['Real per-store growth', r.per_store_growth.toFixed(2) + '×', 'after removing coverage'],
    ['Biggest family', last ? last.cluster : '—', last ? pct(last.unit_share_pct) + ' of units' : ''],
    ['Biggest gainer', top ? top.cluster : '—', top ? '+' + top.share_delta_pp.toFixed(2) + 'pp share' : ''],
  ];
  $('#fy-kpis').innerHTML = rows.map(([l, n, u]) => `
    <div class="kpi">
      <div class="kpi-l mono">${esc(l)}</div>
      <div class="kpi-n">${esc(n)}</div>
      <div class="kpi-u mono">${esc(u)}</div>
    </div>`).join('');
}

/* -------------------------------------------------------------- 1. ramp -- */
function ramp() {
  const c = DATA.category;
  const base = c[0];
  const idx = (get) => c.map((r) => (get(r) / get(base)) * 100);
  const years = c.map((r) => String(r.year));
  $('#fy-ramp').innerHTML = multiLine(years, [
    { name: 'Raw units', color: ACCENT, values: idx((r) => r.units) },
    { name: 'Active stores in panel', color: WARM, values: idx((r) => r.active_stores) },
    { name: 'Units per active store', color: VIOLET, values: idx((r) => r.units_per_active_store) },
  ], { labelEvery: 1, yUnit: '', yFmt: (v) => v.toFixed(0) });

  const r = DATA.ramp;
  $('#fy-ramp-note').innerHTML =
    `Raw category units grew <b>${r.raw_unit_growth.toFixed(2)}×</b> between 2019 and 2025. ` +
    `But the panel itself grew <b>${r.active_stores_growth.toFixed(2)}×</b> over the same span, ` +
    `so volume per store grew only <b>${r.per_store_growth.toFixed(2)}×</b> — ` +
    `<b>${r.coverage_share_of_growth_pct.toFixed(0)}% of the apparent growth is PDI signing chains</b>, ` +
    `not anyone drinking more. Every chart below is reported on a basis that removes it.`;
}

/* ------------------------------------------------------------ 2. ranked -- */
function ranked() {
  const m = METRIC[MET];
  const rows = forYear(YEAR)
    .filter((r) => r[MET] != null)
    .sort((a, b) => b[MET] - a[MET])
    .map((r) => ({ label: r.cluster, value: r[MET], color: ACCENT }));
  $('#fy-ranked').innerHTML = hBars(rows, { fmt: m.fmt });
  $('#fy-metric-note').innerHTML = esc(m.note);
}

/* --------------------------------------------------- 3. small multiples -- */
function grid() {
  const rows = families().map((c) => {
    const series = DATA.years.map((y) => {
      const r = DATA.families.find((x) => x.cluster === c && x.year === y);
      return r ? r.unit_share_pct : null;
    });
    const mv = DATA.movers.find((x) => x.cluster === c);
    const d = mv ? mv.share_delta_pp : null;
    return {
      label: c,
      values: series,
      badge: d == null ? '' : `${d >= 0 ? '+' : ''}${d.toFixed(1)}pp`,
      badgeUp: d != null && d >= 0,
      note: `${series[series.length - 1] != null ? series[series.length - 1].toFixed(2) + '% in ' + DATA.years[DATA.years.length - 1] : ''}`,
    };
  }).sort((a, b) => parseFloat(b.badge) - parseFloat(a.badge));
  $('#fy-grid').innerHTML = sparkGrid(rows);
}

/* --------------------------------------------------- 4. reach x depth ---- */
function reachDepth() {
  const rows = forYear(YEAR);
  const pts = rows.map((r) => ({
    x: r.reach_pct, y: r.depth_units_per_selling_store,
    r: Math.max(4, Math.sqrt(r.unit_share_pct) * 4),
    label: r.cluster, color: ACCENT,
  }));
  $('#fy-scatter').innerHTML = scatter(pts, {
    xLabel: 'REACH — % OF PANEL STORES CARRYING IT',
    yLabel: 'DEPTH — UNITS PER SELLING STORE',
    xFmt: (v) => Math.round(v) + '%',
    fmt: (v) => num(v),
  });
  $('#fy-scatter-note').innerHTML =
    `Units per active store factors exactly into <b>reach × depth</b>: how much of the ` +
    `panel carries a family, times how hard it sells where it is carried. Bubble area is ` +
    `unit share. <b>Top-left is the signal worth acting on</b> — low distribution, high ` +
    `rate of sale, meaning demand that stocking has not caught up with. Bottom-right is ` +
    `the opposite: everywhere, and slow. Year follows the selector above.`;
}

/* ---------------------------------------------------------- 5. movers ---- */
function movers() {
  const last = DATA.years[DATA.years.length - 1];
  const rows = DATA.movers.map((r) => ({
    label: r.cluster, from: r.share_first, to: r.share_last,
    color: r.share_delta_pp >= 0 ? GAIN : LOSS,
  }));
  $('#fy-slope').innerHTML = slope(rows, {
    fmt: (v) => v.toFixed(1) + '%',
    leftTitle: String(DATA.years[0]), rightTitle: String(last),
  });

  /* The slope chart above is a first-vs-last comparison, and on this data that
     is capable of lying outright. Every family it paints as a winner has
     already turned over. Saying so next to the chart is the difference between
     a finding and a mistake. */
  const risen = DATA.movers.filter((r) => r.share_delta_pp > 0);
  const stale = risen.filter((r) => r.past_peak);
  const live = DATA.movers.filter((r) => !r.past_peak && r.share_delta_pp > 0);
  if (!stale.length) return;
  $('#fy-slope').insertAdjacentHTML('afterend', `
    <div class="fy-warn" role="status">
      <b>Read this before reading the chart.</b> A first-versus-last comparison
      hides the shape in between, and here it hides almost everything:
      <b>${stale.length} of the ${risen.length} families that gained share since
      ${DATA.years[0]} have already peaked</b> and are falling.
      <ul class="fy-peaks">
        ${stale.map((r) => `<li><b>${esc(r.cluster)}</b> reads as
          +${r.share_delta_pp.toFixed(2)}pp, but peaked in <b>${r.peak_year}</b> at
          ${r.peak_share.toFixed(2)}% and now sits
          <b>${Math.abs(r.off_peak_pct).toFixed(0)}% below</b> that.</li>`).join('')}
      </ul>
      ${live.length
        ? `Only <b>${live.map((r) => esc(r.cluster)).join('</b> and <b>')}</b>
           ${live.length === 1 ? 'is' : 'are'} still at ${last} peak. The
           small-multiples grid above is where this is visible; the slope chart
           cannot show it.`
        : `<b>No family is still at its peak in ${last}.</b>`}
    </div>`);
}

/* --------------------------------------------------------- 6. ratings ---- */
/* Kept in its own section, on its own chart, with a standing warning. The
   temptation is to put rating and sales on one scatter and call the gap white
   space - but one axis would be seven years of measured convenience sell-through
   and the other a single day of Amazon reviews. That chart would look like an
   analysis and would not be one. */
function ratings() {
  const R = DATA.ratings;
  if (!R) {
    $('#fy-rating-warn').innerHTML =
      '<div class="fy-warn"><b>No rating data.</b> PDI carries none, and no retailer ' +
      'snapshot is present in this repository.</div>';
    return;
  }
  $('#fy-rating-warn').innerHTML = `
    <div class="fy-warn" role="status">
      <b>Not comparable to anything above, and not splittable by year.</b>
      PDI is point-of-sale &mdash; units, revenue, transactions, stores &mdash; and
      carries <b>no rating field at all</b>. These bars are a single Amazon snapshot
      captured on <b>${esc(R.capture_date)}</b>: ${R.n_products} products, one day, one
      retailer. There is no time dimension to split. Treat it as provisional
      &mdash; the defensible version is a manual multi-retailer capture with a
      recorded protocol.
    </div>`;

  const rows = R.families.map((f) => ({
    label: `${f.family} (${f.products} prod, ${fmtCompact(f.reviews)} rev)`,
    value: f.adjusted, color: ACCENT,
  }));
  /* Full scale, baseline at zero. An earlier version started the axis at 4.3,
     which made a 0.22-point spread look like a threefold difference - the exact
     distortion a truncated bar baseline produces. On an honest scale the bars
     are nearly identical, and that IS the finding: every family lands between
     4.45 and 4.67, a band far narrower than the sampling error on groups this
     small. The chart is flat because the differences are not real. */
  $('#fy-ratings').innerHTML = hBars(rows, {
    fmt: (v) => v.toFixed(2), xMin: 0, xMax: 5,
  });

  /* The sensitivity table is not decoration: with groups this small the prior
     weight m does real work, and a reader is entitled to see how much. */
  const span = R.families[0].adjusted - R.families[R.families.length - 1].adjusted;
  $('#fy-ratings').insertAdjacentHTML('afterend', `
    <p class="sec-note fy-caption">
      Plotted on the full 1&ndash;5 scale rather than zoomed to the data, so the
      bars carry their true relative length. They look identical because they
      nearly are: top to bottom the spread is <b>${span.toFixed(2)} of a star</b>.
      Zooming the axis would manufacture a ranking out of that.
    </p>`);

  const ms = Object.keys(R.families[0].sensitivity);
  $('#fy-sens').innerHTML = `
    <p class="sec-note">
      Bayesian-adjusted: <code>(n&middot;R + m&middot;C) / (n + m)</code> with
      <b>C = ${R.prior_mean_C}</b> (mean rating across products) and
      <b>m = ${R.prior_weight_m}</b> (median review count). The columns below vary
      m to show how much the ranking depends on that choice. Watch
      <b>Peach &amp; stone fruit</b>: one product, two reviews, a raw 3.5 that the
      prior drags most of the way back to the mean. That is the adjustment doing
      its job, and also a sign the sample is too thin to rank.
    </p>
    <div class="fy-tablewrap">
      <table class="intel-table fy-table">
        <caption class="sr-only">Sensitivity of adjusted rating to the prior weight m</caption>
        <thead><tr><th scope="col">Family</th><th scope="col" class="num">Products</th>
          <th scope="col" class="num">Reviews</th><th scope="col" class="num">Raw</th>
          ${ms.map((k) => `<th scope="col" class="num">${esc(k)}</th>`).join('')}</tr></thead>
        <tbody>${R.families.map((f) => `
          <tr><th scope="row">${esc(f.family)}</th>
            <td class="num">${f.products}</td>
            <td class="num">${num(f.reviews)}</td>
            <td class="num">${f.raw_rating == null ? '—' : f.raw_rating.toFixed(2)}</td>
            ${ms.map((k) => `<td class="num">${f.sensitivity[k].toFixed(3)}</td>`).join('')}
          </tr>`).join('')}</tbody>
      </table>
    </div>`;
}

/* ----------------------------------------------------------- 7. table ---- */
function table() {
  const rows = forYear(YEAR).slice();
  const k = SORT.key;
  rows.sort((a, b) => {
    const x = a[k], y = b[k];
    const c = typeof x === 'string' ? x.localeCompare(y) : (x || 0) - (y || 0);
    return c * SORT.dir;
  });
  $('#fy-table tbody').innerHTML = rows.map((r) => `
    <tr>
      <th scope="row">${esc(r.cluster)}</th>
      <td class="num">${r.unit_share_pct.toFixed(2)}%</td>
      <td class="num">${num(r.units)}</td>
      <td class="num">${num(r.units_per_active_store)}</td>
      <td class="num">${r.reach_pct.toFixed(0)}%</td>
      <td class="num">${num(r.depth_units_per_selling_store)}</td>
      <td class="num">${r.skus.toFixed(0)}</td>
      <td class="num">${r.units_per_sku == null ? '—' : fmtCompact(r.units_per_sku)}</td>
      <td class="num">${r.price_per_unit == null ? '—' : '$' + r.price_per_unit.toFixed(2)}</td>
    </tr>`).join('');
  for (const th of document.querySelectorAll('#fy-table th[data-sort]')) {
    const on = th.dataset.sort === k;
    th.setAttribute('aria-sort', on ? (SORT.dir < 0 ? 'descending' : 'ascending') : 'none');
    th.classList.toggle('sorted', on);
  }
}

function method() {
  const c = DATA.caveats;
  $('#fy-method').innerHTML = [
    ['The panel is not a fixed sample', c.panel_ramp],
    ['There are no ratings in PDI', c.no_ratings_in_pdi],
    ['Convenience only', c.convenience_only],
    ['How a flavor gets its family', c.taxonomy],
    ['Two families are not flavors',
     '"Unspecified" is excluded from every ranking — it is the bucket for a blank ' +
     'FLAVOR field, and letting it win a flavor study would report a data gap as a ' +
     'finding. "Novelty & branded" is kept, because an invented name like Cosmic ' +
     'Stardust is a real positioning choice, but it is a mixed bag and should not be ' +
     'read as a flavor direction.'],
    ['Units, not dollars',
     'Everything here is units. Revenue would fold in price, and a family that skews ' +
     'to 16oz cans would outrank one that skews to 8.4oz on dollars alone. Price per ' +
     'unit is in the table if you want it.'],
  ].map(([h, b]) => `
    <div class="method-card"><h3 class="mono">${esc(h)}</h3><p>${esc(b)}</p></div>`).join('');
}

/* ----------------------------------------------------------- wiring ------ */
function redrawYear() {
  ranked(); reachDepth(); table();
  for (const b of document.querySelectorAll('.fy-btn[data-year]')) {
    b.setAttribute('aria-selected', String(Number(b.dataset.year) === YEAR));
  }
}

function controls() {
  $('#fy-years').innerHTML = DATA.years.map((y) => `
    <button type="button" class="fy-btn" role="tab" data-year="${y}"
      aria-selected="${y === YEAR}">${y}</button>`).join('');
  $('#fy-years').addEventListener('click', (e) => {
    const b = e.target.closest('[data-year]');
    if (b) { YEAR = Number(b.dataset.year); redrawYear(); }
  });
  for (const btn of document.querySelectorAll('.fy-btn[data-metric]')) {
    btn.addEventListener('click', () => {
      MET = btn.dataset.metric;
      for (const b of document.querySelectorAll('.fy-btn[data-metric]')) {
        b.setAttribute('aria-selected', String(b === btn));
      }
      ranked();
    });
  }
  for (const th of document.querySelectorAll('#fy-table th[data-sort]')) {
    th.tabIndex = 0;
    const go = () => {
      const k = th.dataset.sort;
      SORT = { key: k, dir: SORT.key === k ? -SORT.dir : (k === 'cluster' ? 1 : -1) };
      table();
    };
    th.addEventListener('click', go);
    th.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
    });
  }
}

async function main() {
  DATA = await requireAuth({ dataUrl: 'data/flavor_year.json' });
  YEAR = DATA.years[DATA.years.length - 1];
  kpis(); ramp(); grid(); movers(); ratings(); method();
  controls(); redrawYear();
}

main();
