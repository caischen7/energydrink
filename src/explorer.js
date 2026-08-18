/*
 * Flavor Explorer — type a flavor, see its sales against its search interest.
 *
 * Reads `public/data/flavor_explorer.json`, built by
 * data/scripts/build_flavor_explorer.py (PDI monthly revenue per flavor term)
 * and filled in by data/scripts/add_trends_to_explorer.py (Google Trends).
 *
 * FOUR STATISTICAL DECISIONS ARE BAKED IN HERE, ON PURPOSE
 * --------------------------------------------------------
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
 *
 * 4. Across terms, a Benjamini-Hochberg FDR correction. Testing forty terms at
 *    alpha 0.05 yields two "findings" from noise before anyone looks at the
 *    data, so the summary reports the corrected count alongside the number that
 *    would have passed uncorrected. The category series is the other half of
 *    that defence: if total category revenue already tracks generic "energy
 *    drink" search, then a per-flavor correlation has to beat the category, not
 *    beat zero, and the page says so.
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
let MODE = 'terms';                 // terms | brands | concepts

const GROUP = () => DATA[MODE] || {};
const LABEL = { terms: 'flavor', brands: 'brand', concepts: 'concept' };

/* One analysis, used by the single-term view, the category control and every
   row of the summary table — so the number in the table is provably the same
   number the chart shows. */
function analyze(rev, trendTerms) {
  const bareT = trendTerms[0];
  const qualT = trendTerms[1] || null;
  const bare = DATA.trends[bareT] || null;
  const qual = qualT ? DATA.trends[qualT] || null : null;
  const which = qual || bare;
  if (!which) return { have: false, bare, qual, bareT, qualT };
  const scan = lagScan(logDiff(rev), logDiff(which));
  const usable = scan.filter((s) => s.r != null);
  if (!usable.length) return { have: true, scan, best: null, bare, qual, bareT, qualT };
  const best = usable.reduce((a, b) => (Math.abs(b.r) > Math.abs(a.r) ? b : a));
  return {
    have: true, scan, best, bare, qual, bareT, qualT,
    whichName: qual ? qualT : bareT,
    // Bonferroni within the entity: the reported lag is the best of thirteen.
    pAdjLags: best.p == null ? null : Math.min(1, best.p * scan.length),
  };
}

/* Benjamini-Hochberg. Controls the expected PROPORTION of false discoveries
   rather than the chance of any single one, which is the right trade when the
   question is "how many of these are real" across a whole family of terms. */
function bhAdjust(ps) {
  const idx = ps.map((p, i) => [p, i]).filter(([p]) => p != null).sort((a, b) => a[0] - b[0]);
  const m = idx.length;
  const out = new Array(ps.length).fill(null);
  let prev = 1;
  for (let k = m - 1; k >= 0; k--) {
    const [p, i] = idx[k];
    prev = Math.min(prev, (p * m) / (k + 1));
    out[i] = prev;
  }
  return out;
}

function resolveTerm(qRaw) {
  const q = qRaw.trim().toLowerCase();
  if (!q) return null;
  const g = GROUP();
  const keys = Object.keys(g);
  if (g[q]) return q;
  const byTotal = (a, b) => g[b].total - g[a].total;
  const starts = keys.filter((k) => k.toLowerCase().startsWith(q));
  if (starts.length) return starts.sort(byTotal)[0];
  const has = keys.filter((k) => k.toLowerCase().includes(q) || q.includes(k.toLowerCase()));
  return has.length ? has.sort(byTotal)[0] : null;
}

function suggest(qRaw) {
  const q = qRaw.trim().toLowerCase();
  const box = $('#fx-suggest');
  const close = () => { box.hidden = true; $('#fx-input').setAttribute('aria-expanded', 'false'); };
  if (!q) return close();
  const g = GROUP();
  const hits = Object.keys(g).filter((k) => k.toLowerCase().includes(q))
    .sort((a, b) => g[b].total - g[a].total).slice(0, 8);
  if (!hits.length) return close();
  box.innerHTML = hits.map((k) =>
    `<li role="option" tabindex="-1" data-term="${esc(k)}">
       <span>${esc(k)}</span><span class="fx-sug-v mono">${esc(money(g[k].total))}</span></li>`).join('');
  box.hidden = false;
  $('#fx-input').setAttribute('aria-expanded', 'true');
}

function render(term) {
  const d = GROUP()[term];
  const months = DATA.months;
  const label = months.map((m) => (m.endsWith('-01') ? m.slice(0, 4) : ''));

  // --- headline numbers ---------------------------------------------------
  const active = d.rev.filter((v) => v > 0).length;
  const peakI = d.rev.indexOf(Math.max(...d.rev));
  const tiles = [kpi('TOTAL REVENUE 2019–2025', money(d.total),
    d.skus != null ? `${d.skus} SKUs` : 'all SKUs for this brand')];
  if (d.total > 0) {
    tiles.push(kpi('PEAK MONTH', money(d.rev[peakI]), months[peakI]));
    tiles.push(kpi('MONTHS WITH SALES', `${active}/${months.length}`,
      active < months.length ? 'partial coverage' : 'continuous'));
  } else {
    tiles.push(kpi('MONTHS WITH SALES', '0', 'never sold in this channel'));
  }
  if (d.units != null) tiles.push(kpi('UNITS SOLD', d.units.toLocaleString(), 'convenience channel'));
  else if (d.why) tiles.push(kpi('WHY IT IS HERE', d.skus ? 'partly present' : 'no product', d.why));
  $('#fx-kpis').innerHTML = tiles.join('');

  // --- chart --------------------------------------------------------------
  const a = analyze(d.rev, d.trend_terms);
  const series = [];
  if (d.total > 0) series.push({ name: `${term} — revenue`, values: indexToPeak(d.rev), color: SALES });
  if (a.bare) series.push({ name: `search: "${a.bareT}"`, values: bridge(indexToPeak(a.bare)), color: BARE });
  if (a.qual) series.push({ name: `search: "${a.qualT}"`, values: bridge(indexToPeak(a.qual)), color: QUALIFIED });

  $('#fx-chart').innerHTML = series.length
    ? multiLine(label, series, { labelEvery: 12, yUnit: '', yFmt: (v) => v.toFixed(0) })
    : `<p class="fx-empty mono">NOTHING TO PLOT FOR THIS TERM YET</p>`;
  $('#fx-scale').innerHTML = a.have
    ? `Each line is indexed to its own peak (100).${d.total > 0
        ? ` Revenue peaked at <b>${money(d.rev[peakI])}</b> in ${months[peakI]}.` : ''}
       The search lines are Google's own 0–100 index, so <b>the vertical distance between two
       lines means nothing</b> — only the shapes are comparable.`
    : `<b>No search series collected for “${esc(term)}” yet.</b> Run the
       <i>Refresh Google Trends</i> action; this container cannot reach trends.google.com.`;

  // --- set composition (before any early return) ---------------------------
  $('#fx-set-note').innerHTML = d.why
    ? `<b>${d.skus} SKU${d.skus === 1 ? '' : 's'}</b> in PDI. ${esc(d.why)}.
       ${d.skus === 0
         ? 'Zero here means <b>not sold in convenience</b>, not that nobody wants it — this channel sees no grocery, specialty or DTC.'
         : 'Small but non-zero: somebody has already tried it in this channel.'}`
    : d.skus != null
      ? `<b>${d.skus} SKUs</b> carry “${esc(term)}” in their flavor or description field. Flavor sets
         overlap — a mango-pineapple SKU counts in both — so these totals do not sum to the category.`
      : `All PDI convenience revenue recorded against <b>${esc(term)}</b>, 2019–2025.`;
  $('#fx-brands').innerHTML = d.brands
    ? `<ul class="fx-brands">${d.brands.map((b) => `<li>${esc(b)}</li>`).join('')}</ul>` : '';

  // --- correlation --------------------------------------------------------
  const box = $('#fx-corr');
  const verdict = $('#fx-verdict');
  if (!a.have) {
    box.innerHTML = `<p class="fx-empty mono">NO SEARCH SERIES FOR THIS TERM</p>`;
    verdict.textContent = `Search data is collected by a scheduled GitHub Action, because this
      environment cannot reach trends.google.com. Until it runs for “${term}”, there is nothing
      to correlate — and a sales line on its own says nothing about search.`;
    return;
  }
  if (!a.best) {
    box.innerHTML = `<p class="fx-empty mono">NOT ENOUGH OVERLAPPING MONTHS</p>`;
    verdict.textContent = `“${term}” has too few months with sales in both series to compute a
      correlation. That is a coverage statement, not a null result.`;
    return;
  }
  box.innerHTML = correlogram(a.scan, a.best);

  const b = a.best;
  const real = a.pAdjLags != null && a.pAdjLags < 0.05;
  const dir = b.lag > 0 ? `search led sales by ${b.lag} month${b.lag > 1 ? 's' : ''}`
    : b.lag < 0 ? `sales led search by ${-b.lag} month${b.lag < -1 ? 's' : ''}`
    : 'search and sales moved in the same month';
  verdict.innerHTML = `
    Strongest relationship for <b>${esc(term)}</b> is at <b>lag ${b.lag > 0 ? '+' : ''}${b.lag}</b> —
    ${dir} — with <b>r = ${b.r.toFixed(3)}</b> over ${b.n} months
    (raw p ${b.p < 0.001 ? '&lt; 0.001' : '= ' + b.p.toFixed(3)},
     ${a.pAdjLags < 0.001 ? '&lt; 0.001' : a.pAdjLags.toFixed(3)} after correcting for the
     ${a.scan.length} lags tested).
    ${real
      ? `That survives the correction, so it is unlikely to be scan noise. It is still not
         causation: a launch drives search and sales together, and nothing here separates that
         from search driving sales. Check it against the category control below.`
      : `That does <b>not</b> survive the correction. Read it as no detectable relationship —
         picking the largest of ${a.scan.length} correlations produces an r near
         ${Math.abs(b.r).toFixed(2)} from pure noise about half the time.`}
    ${b.lag < 0 && real
      ? ` <b>Note the sign.</b> Sales moved first, which inverts the story — people search after
          they meet the product, not before.` : ''}
    <br /><br />Series used: <b>“${esc(a.whichName)}”</b>${a.qual && a.bare
      ? `. The bare word “${esc(a.bareT)}” is plotted but not used for the statistic — it measures
         the fruit, not drink intent.` : '.'}`;
}

/* ------------------------------------------------- category + summary ---- */

function renderControl() {
  const c = DATA.category;
  const a = analyze(c.rev, c.trend_terms);
  const months = DATA.months;
  const label = months.map((m) => (m.endsWith('-01') ? m.slice(0, 4) : ''));

  const series = [{ name: 'all energy drinks — revenue', values: indexToPeak(c.rev), color: SALES }];
  if (a.bare) series.push({ name: 'search: "energy drink"', values: bridge(indexToPeak(a.bare)), color: QUALIFIED });

  $('#fx-control').innerHTML =
    multiLine(label, series, { labelEvery: 12, yUnit: '', yFmt: (v) => v.toFixed(0) }) +
    (a.best ? correlogram(a.scan, a.best) : '');

  if (!a.have) {
    $('#fx-control-note').innerHTML = `Category revenue is <b>${money(c.total)}</b> across
      ${c.skus.toLocaleString()} GTINs. The generic <i>"energy drink"</i> search series has not
      been collected yet, so the control cannot be computed — every per-term result below is
      unanchored until it is.`;
    return null;
  }
  if (!a.best) { $('#fx-control-note').textContent = 'Not enough overlap to compute the control.'; return null; }
  const real = a.pAdjLags < 0.05;
  $('#fx-control-note').innerHTML = `Category revenue <b>${money(c.total)}</b> across
    ${c.skus.toLocaleString()} GTINs. Against generic <i>"energy drink"</i> search the best lag is
    <b>${a.best.lag > 0 ? '+' : ''}${a.best.lag}</b> at <b>r = ${a.best.r.toFixed(3)}</b>
    (${real ? 'survives' : 'does not survive'} correction).
    ${real
      ? `<b>Because the category itself moves with generic search, a flavor that correlates with
         its own search term has not shown anything yet</b> — it has to beat this, not beat zero.`
      : `The category does <b>not</b> track generic search, which is good news for the per-term
         tests: a flavor-level correlation cannot be dismissed as category seasonality.`}`;
  return a;
}

function renderSummary(control) {
  const rows = [];
  for (const [mode, group] of [['brands', DATA.brands], ['terms', DATA.terms], ['concepts', DATA.concepts]]) {
    for (const [name, d] of Object.entries(group || {})) {
      const a = analyze(d.rev, d.trend_terms);
      if (!a.have || !a.best) continue;
      rows.push({ mode, name, total: d.total, r: a.best.r, lag: a.best.lag, n: a.best.n,
                  p: a.pAdjLags, pRaw: a.best.p });
    }
  }
  const table = $('#fx-table');
  if (!rows.length) {
    table.innerHTML = `<tbody><tr><td class="fx-empty">No search series collected yet — the
      summary appears once the Refresh Google Trends action has run.</td></tr></tbody>`;
    $('#fx-overall').innerHTML = `Nothing to summarise yet. The pipeline is in place: the
      collector, the merge step and this table all run without further edits once
      <i>Refresh Google Trends</i> has completed one pass.`;
    return;
  }
  const adj = bhAdjust(rows.map((r) => r.p));
  rows.forEach((r, i) => { r.q = adj[i]; });
  rows.sort((a, b) => Math.abs(b.r) - Math.abs(a.r));

  table.innerHTML = `
    <thead><tr>
      <th>Term</th><th>Type</th><th class="num">Revenue</th><th class="num">Best lag</th>
      <th class="num">r</th><th class="num">n</th><th class="num">q (FDR)</th><th>Verdict</th>
    </tr></thead>
    <tbody>${rows.map((r) => `
      <tr>
        <td class="pd">${esc(r.name)}</td>
        <td>${LABEL[r.mode]}</td>
        <td class="num">${esc(money(r.total))}</td>
        <td class="num">${r.lag > 0 ? '+' : ''}${r.lag}</td>
        <td class="num">${r.r.toFixed(3)}</td>
        <td class="num">${r.n}</td>
        <td class="num">${r.q < 0.001 ? '&lt;0.001' : r.q.toFixed(3)}</td>
        <td>${r.q < 0.05
          ? (r.lag > 0 ? '<b>search leads</b>' : r.lag < 0 ? '<b>sales lead</b>' : '<b>same month</b>')
          : '<span class="fx-null">no signal</span>'}</td>
      </tr>`).join('')}</tbody>`;

  const hits = rows.filter((r) => r.q < 0.05);
  const leads = hits.filter((r) => r.lag > 0).length;
  const lagsBehind = hits.filter((r) => r.lag < 0).length;
  // Count of terms that would have looked significant with NO correction at all.
  // This is the "how much of this is scan noise" number, and it belongs next to
  // the corrected count rather than replacing it.
  const naive = rows.filter((r) => r.pRaw != null && r.pRaw < 0.05).length;
  $('#fx-overall').innerHTML = `
    <b>${hits.length} of ${rows.length}</b> terms show a relationship surviving both corrections —
    Bonferroni across the ${2 * MAX_LAG + 1} lags within each term, then Benjamini–Hochberg across
    all ${rows.length} terms. Without any correction, <b>${naive}</b> would have looked
    significant.
    ${hits.length === 0
      ? `<br /><br />That is a clean null: <b>at this granularity, search interest does not predict
         convenience-channel revenue.</b> It is a real answer rather than a failure — 83 monthly
         points per term can detect a strong relationship and not a weak one, so this rules out a
         large effect, not every effect.`
      : `<br /><br />${hits.length === 1 ? 'That one is a genuine discovery' : `Those ${hits.length} are genuine discoveries`}
         at a 5% false-discovery rate: BH controls the expected <i>proportion</i> of false
         positives among them, so about 1 in 20 of what survives is expected to be spurious.
         <b>${leads} ${leads === 1 ? 'has' : 'have'} search leading sales</b> and
         <b>${lagsBehind} ${lagsBehind === 1 ? 'has' : 'have'} sales leading search</b>.
         ${lagsBehind >= leads && hits.length > 1
           ? `That balance is the thing to watch: with as many terms showing sales moving first,
              the pattern looks more like a shared seasonal cycle than like search driving demand.`
           : `Search leading is the direction a predictive story needs — though a launch moves
              search and sales at once, so this is still not causal evidence.`}`}
    ${control && control.pAdjLags != null && control.pAdjLags < 0.05
      ? `<br /><br /><b>Read all of this against the control.</b> Total category revenue already
         tracks generic search (r = ${control.best.r.toFixed(3)}), so some of the per-term
         correlation above is the category's own seasonality appearing in every term at once.`
      : ''}`;
}

/* ------------------------------------------------------------------ wire -- */

function select(term, push = true) {
  const g = GROUP();
  if (!g[term]) return;
  $('#fx-input').value = term;
  $('#fx-suggest').hidden = true;
  const d = g[term];
  $('#fx-hint').textContent = d.skus != null
    ? `${d.skus} SKUs · ${money(d.total)} 2019–2025`
    : `${money(d.total)} 2019–2025`;
  if (push) history.replaceState(null, '', `#${MODE}:${encodeURIComponent(term)}`);
  render(term);
}

function setMode(mode) {
  MODE = mode;
  for (const b of document.querySelectorAll('.fx-mode')) {
    b.setAttribute('aria-selected', String(b.dataset.mode === mode));
  }
  const g = GROUP();
  const keys = Object.keys(g).slice(0, 14);
  $('#fx-chips').innerHTML = keys.map((t) =>
    `<button type="button" class="fx-chip" data-term="${esc(t)}">${esc(t)}</button>`).join('');
  $('#fx-input').placeholder = { terms: 'mango', brands: 'Red Bull', concepts: 'masala chai' }[mode];
  select(keys[0]);
}

async function main() {
  // requireAuth's default target is dashboard.json; point it at this page's own
  // aggregate instead. Same credentials, same nginx realm.
  DATA = await requireAuth({ dataUrl: 'data/flavor_explorer.json' });

  const n = Object.keys(DATA.trends || {}).length;
  $('#fx-foot').textContent = `${Object.keys(DATA.terms).length} flavors · ` +
    `${Object.keys(DATA.brands || {}).length} brands · ${Object.keys(DATA.concepts || {}).length} concepts · ` +
    `${n} search series · PDI 2019–2025`;

  $('#fx-limits').innerHTML = [
    `<b>Convenience channel only</b>, and roughly 8.6% of it. A flavor that sells in grocery, club
     or DTC is under-represented — this is not total market. It is why a concept can read as
     "no product" here and still exist on a shelf somewhere else.`,
    `<b>Flavor sets overlap.</b> "Mango Peach" counts under both mango and peach, so term revenues
     cannot be added together.`,
    `<b>Search values are relative.</b> Google indexes each term to its own peak, so levels compare
     within a term over time and never between terms.`,
    `<b>Correlation is not causation</b>, and a lag is not a mechanism. A launch moves search and
     sales at once; nothing here separates that from search driving sales.`,
    `<b>Two corrections are applied</b>: Bonferroni across the ${2 * MAX_LAG + 1} lags within each
     term, then Benjamini–Hochberg across all terms. Raw p-values alone would call roughly half of
     pure-noise pairs significant.`,
    `<b>83 monthly points per term</b> is enough to detect a strong relationship and not enough to
     detect a weak one. A null here rules out a large effect, not every effect.`,
  ].map((t) => `<li>${t}</li>`).join('');

  $('#fx-chips').addEventListener('click', (e) => {
    const b = e.target.closest('[data-term]');
    if (b) select(b.dataset.term);
  });
  document.querySelector('.fx-modes').addEventListener('click', (e) => {
    const b = e.target.closest('[data-mode]');
    if (b) setMode(b.dataset.mode);
  });

  const input = $('#fx-input');
  input.addEventListener('input', () => suggest(input.value));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const t = resolveTerm(input.value);
      if (t) select(t);
      else $('#fx-hint').textContent = `No ${LABEL[MODE]} matching "${input.value.trim()}" in the PDI set.`;
    } else if (e.key === 'Escape') $('#fx-suggest').hidden = true;
  });
  $('#fx-suggest').addEventListener('click', (e) => {
    const li = e.target.closest('[data-term]');
    if (li) select(li.dataset.term);
  });
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.fx-search')) $('#fx-suggest').hidden = true;
  });

  const control = renderControl();
  renderSummary(control);

  const [hm, ht] = decodeURIComponent(location.hash.slice(1)).split(':');
  MODE = ['terms', 'brands', 'concepts'].includes(hm) ? hm : 'terms';
  setMode(MODE);
  if (ht && GROUP()[ht]) select(ht, false);
}

main();
