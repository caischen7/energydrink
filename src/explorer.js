/*
 * Flavor Explorer — type a flavor, see its sales against its search interest.
 *
 * Reads `public/data/flavor_explorer.json`, built by
 * data/scripts/build_flavor_explorer.py (PDI monthly revenue per flavor term)
 * and filled in by data/scripts/add_trends_to_explorer.py (Google Trends).
 *
 * THREE STATISTICAL DECISIONS ARE BAKED IN HERE, ON PURPOSE
 * ---------------------------------------------------------
 * 1. The chart plots levels INDEXED TO EACH SERIES' OWN PEAK. Dollars and a
 *    0-100 search index share no unit, and a dual y-axis lets whoever picks the
 *    two scales manufacture any apparent relationship they like. Indexing shows
 *    shape, which is the only comparison the data supports.
 *
 * 2. The correlation is computed on MONTH-OVER-MONTH LOG CHANGE, never on the
 *    plotted levels. Any two series that trend upward correlate near 0.9 in
 *    levels regardless of whether they have anything to do with each other.
 *    Differencing removes the shared trend. It is also what makes each Trends
 *    series usable at all: Trends rescales to its own window maximum, and a
 *    common scale factor cancels out of a log difference.
 *
 * 3. The lag scan reports the BEST lag out of thirteen, so its p-value is
 *    optimistic by construction - scanning thirteen lags at alpha 0.05 gives
 *    roughly a one-in-two chance of a "significant" result from noise alone.
 *    The verdict text says so rather than burying it, and applies a Bonferroni
 *    threshold before calling anything real.
 */
import '@fontsource-variable/inter';
import './dashboard.css';
import './audience.css';
import './explorer.css';
import { multiLine } from './charts.js';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const money = (v) =>
  v >= 1e9 ? '$' + (v / 1e9).toFixed(2) + 'B' :
  v >= 1e6 ? '$' + (v / 1e6).toFixed(1) + 'M' :
  v >= 1e3 ? '$' + (v / 1e3).toFixed(0) + 'K' : '$' + v.toFixed(0);

const MAX_LAG = 6;          // months, each direction
const SALES = '#0071e3';
const BARE = '#c77dff';
const QUALIFIED = '#f77f00';

/* ------------------------------------------------------------------ math -- */

/* Index a series to its own peak so two different units can share an axis. */
function indexToPeak(vals) {
  const peak = Math.max(...vals.filter((v) => v != null && isFinite(v)), 0);
  if (!peak) return vals.map(() => null);
  return vals.map((v) => (v == null ? null : (v / peak) * 100));
}

/* Log change month over month. Zero months are dropped rather than clamped:
   log(0) is undefined, and substituting a small constant invents a huge change
   at exactly the months where a flavor enters or leaves distribution. */
function logDiff(vals) {
  const out = [];
  for (let i = 1; i < vals.length; i++) {
    const a = vals[i - 1];
    const b = vals[i];
    out.push(a > 0 && b > 0 ? Math.log(b / a) : null);
  }
  return out;
}

function pearson(xs, ys) {
  const pairs = xs.map((x, i) => [x, ys[i]]).filter(([a, b]) => a != null && b != null && isFinite(a) && isFinite(b));
  const n = pairs.length;
  if (n < 8) return { r: null, n };
  const mx = pairs.reduce((s, p) => s + p[0], 0) / n;
  const my = pairs.reduce((s, p) => s + p[1], 0) / n;
  let sxy = 0, sxx = 0, syy = 0;
  for (const [a, b] of pairs) {
    sxy += (a - mx) * (b - my);
    sxx += (a - mx) ** 2;
    syy += (b - my) ** 2;
  }
  const den = Math.sqrt(sxx * syy);
  return { r: den ? sxy / den : null, n };
}

/* Normal-approximation two-sided p via Fisher's z. Exact enough at n > 20, and
   the verdict never leans on the third decimal. */
function pValue(r, n) {
  if (r == null || n < 8) return null;
  const z = Math.atanh(Math.max(-0.999999, Math.min(0.999999, r))) * Math.sqrt(n - 3);
  // Abramowitz & Stegun 7.1.26 error-function approximation.
  const x = Math.abs(z) / Math.SQRT2;
  const t = 1 / (1 + 0.3275911 * x);
  const erf = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return Math.max(0, Math.min(1, 1 - erf));
}

/* Positive lag = search moves FIRST and sales follow k months later. */
function lagScan(salesD, searchD, maxLag = MAX_LAG) {
  const out = [];
  for (let k = -maxLag; k <= maxLag; k++) {
    const a = [], b = [];
    for (let i = 0; i < salesD.length; i++) {
      const j = i - k;                       // search index for sales month i
      if (j < 0 || j >= searchD.length) continue;
      a.push(searchD[j]);
      b.push(salesD[i]);
    }
    const { r, n } = pearson(a, b);
    out.push({ lag: k, r, n, p: pValue(r, n) });
  }
  return out;
}

/* Interpolate interior gaps so a line does not break; leading and trailing
   nulls stay null so the line simply starts and stops where data does. */
function bridge(vals) {
  const out = vals.slice();
  let last = -1;
  for (let i = 0; i < out.length; i++) {
    if (out[i] == null) continue;
    if (last >= 0 && i - last > 1) {
      const step = (out[i] - out[last]) / (i - last);
      for (let j = last + 1; j < i; j++) out[j] = out[last] + step * (j - last);
    }
    last = i;
  }
  return out;
}

/* ----------------------------------------------------------------- views -- */

/* Diverging correlogram. vBars can't do this: it scales bars from a zero floor,
   so a negative correlation renders as a negative height and vanishes. */
function correlogram(scan, best) {
  const W = 800, H = 260, padL = 44, padR = 14, padT = 22, padB = 44;
  const iw = W - padL - padR, ih = H - padT - padB;
  const max = Math.max(0.35, ...scan.map((d) => Math.abs(d.r ?? 0))) * 1.15;
  const slot = iw / scan.length;
  const bw = Math.min(38, slot * 0.62);
  const zero = padT + ih / 2;
  const sy = (v) => zero - (v / max) * (ih / 2);

  let grid = '';
  for (const v of [-max, -max / 2, 0, max / 2, max]) {
    grid += `<line x1="${padL}" y1="${sy(v).toFixed(1)}" x2="${padL + iw}" y2="${sy(v).toFixed(1)}"
      class="${v === 0 ? 'c-axis' : 'c-grid'}"/>
      <text x="${padL - 8}" y="${sy(v).toFixed(1)}" class="c-lbl" text-anchor="end"
        dominant-baseline="middle">${v.toFixed(2)}</text>`;
  }

  const bars = scan.map((d, i) => {
    if (d.r == null) return '';
    const x = padL + i * slot + (slot - bw) / 2;
    const y = d.r >= 0 ? sy(d.r) : zero;
    const h = Math.max(1.5, Math.abs(sy(d.r) - zero));
    const on = best && d.lag === best.lag;
    return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}"
      fill="${on ? SALES : 'var(--hair-strong, #c9c9cf)'}" rx="2">
      <title>lag ${d.lag >= 0 ? '+' : ''}${d.lag} months — r ${d.r.toFixed(3)}, n ${d.n}</title></rect>`;
  }).join('');

  const labels = scan.map((d, i) => {
    if (d.lag % 2 !== 0) return '';
    const x = padL + i * slot + slot / 2;
    return `<text x="${x.toFixed(1)}" y="${H - padB + 20}" class="c-lbl" text-anchor="middle">${
      d.lag > 0 ? '+' + d.lag : d.lag}</text>`;
  }).join('');

  return `<svg viewBox="0 0 ${W} ${H}" class="chart" preserveAspectRatio="xMidYMid meet" role="img"
      aria-label="Correlation between search and sales at each monthly lag">
    ${grid}${bars}${labels}
    <text x="${padL}" y="${H - 8}" class="c-lbl">← sales moved first</text>
    <text x="${padL + iw}" y="${H - 8}" class="c-lbl" text-anchor="end">search moved first →</text>
  </svg>`;
}

function kpi(label, value, sub) {
  return `<div class="fx-kpi"><div class="fx-kpi-v">${esc(value)}</div>
    <div class="fx-kpi-l mono">${esc(label)}</div>
    ${sub ? `<div class="fx-kpi-s">${esc(sub)}</div>` : ''}</div>`;
}

/* ------------------------------------------------------------------ page -- */

let DATA = null;

function resolveTerm(qRaw) {
  const q = qRaw.trim().toLowerCase();
  if (!q) return null;
  const keys = Object.keys(DATA.terms);
  if (DATA.terms[q]) return q;
  const starts = keys.filter((k) => k.startsWith(q));
  if (starts.length) return starts.sort((a, b) => DATA.terms[b].total - DATA.terms[a].total)[0];
  const has = keys.filter((k) => k.includes(q) || q.includes(k));
  if (has.length) return has.sort((a, b) => DATA.terms[b].total - DATA.terms[a].total)[0];
  return null;
}

function suggest(qRaw) {
  const q = qRaw.trim().toLowerCase();
  const box = $('#fx-suggest');
  if (!q) { box.hidden = true; $('#fx-input').setAttribute('aria-expanded', 'false'); return; }
  const hits = Object.keys(DATA.terms)
    .filter((k) => k.includes(q))
    .sort((a, b) => DATA.terms[b].total - DATA.terms[a].total)
    .slice(0, 8);
  if (!hits.length) { box.hidden = true; $('#fx-input').setAttribute('aria-expanded', 'false'); return; }
  box.innerHTML = hits.map((k) =>
    `<li role="option" tabindex="-1" data-term="${esc(k)}">
       <span>${esc(k)}</span><span class="fx-sug-v mono">${esc(money(DATA.terms[k].total))}</span></li>`).join('');
  box.hidden = false;
  $('#fx-input').setAttribute('aria-expanded', 'true');
}

function render(term) {
  const d = DATA.terms[term];
  const months = DATA.months;
  const label = months.map((m) => (m.endsWith('-01') ? m.slice(0, 4) : ''));

  // --- headline numbers ---------------------------------------------------
  const active = d.rev.filter((v) => v > 0).length;
  const peakI = d.rev.indexOf(Math.max(...d.rev));
  $('#fx-kpis').innerHTML =
    kpi('TOTAL REVENUE 2019–2025', money(d.total), `${d.skus} SKUs`) +
    kpi('PEAK MONTH', money(d.rev[peakI]), months[peakI]) +
    kpi('MONTHS WITH SALES', `${active}/${months.length}`, active < months.length ? 'partial coverage' : 'continuous') +
    kpi('UNITS SOLD', d.units.toLocaleString(), 'convenience channel');

  // --- the two search series, if collected --------------------------------
  const [bareT, qualT] = d.trend_terms;
  const bare = DATA.trends[bareT] || null;
  const qual = DATA.trends[qualT] || null;
  const haveSearch = !!(bare || qual);

  const series = [{ name: `${term} — revenue`, values: indexToPeak(d.rev), color: SALES }];
  if (bare) series.push({ name: `search: "${bareT}"`, values: bridge(indexToPeak(bare)), color: BARE });
  if (qual) series.push({ name: `search: "${qualT}"`, values: bridge(indexToPeak(qual)), color: QUALIFIED });

  $('#fx-chart').innerHTML = multiLine(label, series, { labelEvery: 12, yUnit: '', yFmt: (v) => v.toFixed(0) });
  $('#fx-scale').innerHTML = haveSearch
    ? `Each line is indexed to its own peak (100). Revenue peaked at <b>${money(d.rev[peakI])}</b> in
       ${months[peakI]}; the search lines are Google's own 0–100 index, so <b>the vertical distance
       between two lines means nothing</b> — only the shapes are comparable.`
    : `<b>Search data has not been collected for “${esc(term)}” yet.</b> Only the top
       ${'' + (DATA.meta.trends_top_n || 20)} flavors by revenue get a search series. Run the
       <i>Refresh Google Trends</i> action to collect more.`;

  // --- set composition ----------------------------------------------------
  // Rendered BEFORE the correlation block, which returns early when a term has
  // no search series. Left below it, "what's in the set" stayed blank for every
  // term outside the collected top 20 - the majority of the vocabulary.
  $('#fx-set-note').innerHTML = `<b>${d.skus} SKUs</b> carry “${esc(term)}” in their flavor or
    description field. Flavor sets overlap — a mango-pineapple SKU counts in both — so these
    totals do not sum to the category.`;
  $('#fx-brands').innerHTML = `<ul class="fx-brands">${d.brands.map((b) =>
    `<li>${esc(b)}</li>`).join('')}</ul>`;

  // --- correlation --------------------------------------------------------
  const salesD = logDiff(d.rev);
  const box = $('#fx-corr');
  const verdict = $('#fx-verdict');

  if (!haveSearch) {
    box.innerHTML = `<p class="fx-empty mono">NO SEARCH SERIES FOR THIS TERM</p>`;
    verdict.innerHTML = `This container cannot reach trends.google.com, so search data is
      collected by a scheduled GitHub Action. Until it runs for “${esc(term)}”, the sales line
      above stands alone — and a sales line on its own says nothing about search.`;
    return;
  }

  const which = qual || bare;
  const whichName = qual ? qualT : bareT;
  const scan = lagScan(salesD, logDiff(which));
  const usable = scan.filter((s) => s.r != null);
  const best = usable.length ? usable.reduce((a, b) => (Math.abs(b.r) > Math.abs(a.r) ? b : a)) : null;
  box.innerHTML = correlogram(scan, best);

  if (!best) {
    verdict.innerHTML = `Too few overlapping months with sales in both series to compute a
      correlation for “${esc(term)}”. That is a coverage statement, not a null result.`;
    return;
  }

  // Thirteen lags were scanned, so the naive threshold is wrong. Bonferroni is
  // conservative and easy to defend, which is what this needs to be.
  const alpha = 0.05 / scan.length;
  const real = best.p != null && best.p < alpha;
  const dir = best.lag > 0 ? `search led sales by ${best.lag} month${best.lag > 1 ? 's' : ''}`
    : best.lag < 0 ? `sales led search by ${-best.lag} month${best.lag < -1 ? 's' : ''}`
    : 'search and sales moved in the same month';

  verdict.innerHTML = `
    Strongest relationship for <b>${esc(term)}</b> is at <b>lag ${best.lag > 0 ? '+' : ''}${best.lag}</b> —
    ${dir} — with <b>r = ${best.r.toFixed(3)}</b> over ${best.n} months
    (raw p ${best.p < 0.001 ? '&lt; 0.001' : '= ' + best.p.toFixed(3)}).
    ${real
      ? `That survives a Bonferroni threshold of ${alpha.toFixed(4)} for the ${scan.length} lags tested,
         so it is unlikely to be scan noise. It still is not causation: a flavor launch drives
         search and sales together, and this cannot separate that from search driving sales.`
      : `That does <b>not</b> survive the Bonferroni threshold of ${alpha.toFixed(4)} needed once you
         account for testing ${scan.length} lags. Read it as no detectable relationship.
         Picking the largest of thirteen correlations will produce an r near ${Math.abs(best.r).toFixed(2)}
         from pure noise about half the time.`}
    ${best.lag < 0 && real
      ? ` <b>Note the sign of the lag.</b> Sales moved first, which inverts the story — people
          search after they see the product, not before.`
      : ''}
    <br /><br />Series used: <b>“${esc(whichName)}”</b>${qual && bare
      ? `. The bare word “${esc(bareT)}” is plotted too but not used for the statistic — it measures
         the fruit, not drink intent.` : '.'}`;
}

function select(term, push = true) {
  if (!DATA.terms[term]) return;
  $('#fx-input').value = term;
  $('#fx-suggest').hidden = true;
  $('#fx-hint').textContent = `${DATA.terms[term].skus} SKUs · ${money(DATA.terms[term].total)} 2019–2025`;
  if (push) history.replaceState(null, '', `#${encodeURIComponent(term)}`);
  render(term);
}

async function main() {
  // requireAuth's default target is dashboard.json; point it at this page's own
  // aggregate instead. Same credentials, same nginx realm.
  DATA = await requireAuth({ dataUrl: 'data/flavor_explorer.json' });

  const withSearch = Object.keys(DATA.trends || {}).length;
  $('#fx-foot').textContent =
    `${Object.keys(DATA.terms).length} flavors · ${withSearch} search series · PDI 2019–2025`;

  $('#fx-limits').innerHTML = [
    `<b>Convenience channel only</b>, and roughly 8.6% of it. A flavor that sells in
     grocery, club or DTC is under-represented here — this is not total market.`,
    `<b>Flavor sets overlap.</b> "Mango Peach" counts under both mango and peach, so
     term revenues cannot be added together.`,
    `<b>Search values are relative.</b> Google indexes each term to its own peak, so
     levels compare within a term over time and never between terms.`,
    `<b>Correlation is not causation</b>, and a lag is not a mechanism. A launch moves
     search and sales at once; nothing here separates that from search driving sales.`,
    `<b>The lag scan tests 13 hypotheses.</b> The verdict applies a Bonferroni
     correction; the raw p-value alone would call roughly half of pure-noise pairs
     significant.`,
  ].map((t) => `<li>${t}</li>`).join('');

  // Highest-revenue flavors as one-click chips, so the page is useful before
  // the visitor knows what the vocabulary contains.
  const top = Object.keys(DATA.terms).slice(0, 12);
  $('#fx-chips').innerHTML = top.map((t) =>
    `<button type="button" class="fx-chip" data-term="${esc(t)}">${esc(t)}</button>`).join('');
  $('#fx-chips').addEventListener('click', (e) => {
    const b = e.target.closest('[data-term]');
    if (b) select(b.dataset.term);
  });

  const input = $('#fx-input');
  input.addEventListener('input', () => suggest(input.value));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const t = resolveTerm(input.value);
      if (t) select(t);
      else $('#fx-hint').textContent = `No flavor matching "${input.value.trim()}" in the PDI set.`;
    } else if (e.key === 'Escape') {
      $('#fx-suggest').hidden = true;
    }
  });
  $('#fx-suggest').addEventListener('click', (e) => {
    const li = e.target.closest('[data-term]');
    if (li) select(li.dataset.term);
  });
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.fx-search')) $('#fx-suggest').hidden = true;
  });

  const initial = decodeURIComponent(location.hash.slice(1)) || 'mango';
  select(DATA.terms[initial] ? initial : Object.keys(DATA.terms)[0], false);
}

main();
