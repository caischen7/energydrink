/*
 * Whitespace Engine — ten analyses, one tab each.
 *
 * Reads public/data/whitespace.json (built by data/scripts/build_whitespace.py,
 * guarded by the same nginx Basic Auth realm as the rest of public/data/).
 *
 * THE PANELS ARE NOT ALL THE SAME KIND OF THING, AND THE UI SAYS SO
 * -----------------------------------------------------------------
 * Every panel carries a status and renders differently by it:
 *
 *   ok       computed from committed data; numbers shown
 *   partial  computed, but one side of the comparison is known to be weak;
 *            renders the caveat ABOVE the numbers, not in a footnote
 *   blocked  cannot be computed here (no bq client in the container). Renders
 *            the method, the SQL and the cost — and NO numbers at all. An
 *            empty state is the honest output; a plausible-looking chart
 *            would not be.
 *   sample   the underlying file is generated sample data. Same treatment.
 *
 * That distinction is the point of the page. A reader has to be able to tell
 * a measured result from a scaffold at a glance, which is what the pill in the
 * tab strip and the banner at the top of each panel are for.
 */
import '@fontsource-variable/inter';
import './whitespace.css';
import { scatter, hBars, fmtCompact, fmtInt, revealCards } from './charts.js';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

let DATA = null;

/* ---------------------------------------------------------------- helpers -- */
const money = (v) => '$' + fmtCompact(v);
const pct = (v, d = 1) => (v === null || v === undefined ? '—' : v.toFixed(d) + '%');

function statCard(k, v, cls = '') {
  return `<div class="ws-stat"><div class="v ${cls}">${v}</div><div class="k">${esc(k)}</div></div>`;
}
function stats(list) {
  return `<div class="ws-stats">${list.map((s) => statCard(s[0], s[1], s[2] || '')).join('')}</div>`;
}
function table(cols, rows, caption) {
  const head = cols.map((c) => `<th>${esc(c.h)}</th>`).join('');
  const body = rows
    .map(
      (r) =>
        `<tr>${cols
          .map((c) => {
            const v = c.get(r);
            const cls = [c.num ? 'num' : '', c.cls ? c.cls(r) : ''].filter(Boolean).join(' ');
            return `<td${cls ? ` class="${cls}"` : ''}>${v}</td>`;
          })
          .join('')}</tr>`
    )
    .join('');
  return (
    `<div class="ws-tablewrap"><table class="ws-table"><thead><tr>${head}</tr></thead>` +
    `<tbody>${body}</tbody></table></div>` +
    (caption ? `<p class="ws-cap">${esc(caption)}</p>` : '')
  );
}
function method(html) {
  return `<p class="ws-method">${html}</p>`;
}
function needsList(needs) {
  if (!needs || !needs.length) return '';
  return `<p class="ws-method"><b>Needs</b></p><ul class="ws-needs">${needs
    .map((n) => `<li>${esc(n)}</li>`)
    .join('')}</ul>`;
}

/* A blocked or sample panel renders its method and refuses to draw numbers. */
function scaffold(p) {
  const isSample = p.status === 'sample';
  return (
    `<div class="${isSample ? 'ws-warn' : 'ws-stop'}">` +
    `<b>${isSample ? 'Sample data — no findings drawn.' : 'Blocked — not computed here.'}</b> ` +
    esc(p.warning || 'This analysis needs data that is not available in this container. ' +
      'The method and query are below so it can be run where the data is.') +
    `</div>` +
    (p.question ? `<p class="ws-q">${esc(p.question)}</p>` : '') +
    (p.model ? method(`<b>Model</b> — ${esc(p.model)}`) : '') +
    (p.cost ? method(`<b>Cost</b> — ${esc(p.cost)}`) : '') +
    (p.rows_in_sample ? method(`<b>Sample file</b> — ${p.rows_in_sample} rows, not used.`) : '') +
    needsList(p.needs) +
    (p.sql ? `<pre class="ws-sql">${esc(p.sql)}</pre>` : '')
  );
}

/* ================================================== 1. VELOCITY x REACH == */
function renderVelocity(p) {
  const QC = {
    'proven, under-distributed': '#0071e3',
    'scaled winners': '#2c6b34',
    'wide but weak': '#9a9aa2',
    'niche / fading': '#c9c9d0',
  };
  /* Both axes are log: store counts run 25 -> 35,203 and velocity 1 -> 33,679,
     so a linear axis would stack every point against one wall. Labels go only
     to the ten fastest under-distributed SKUs — the scatter's collision engine
     drops overlaps anyway, and 600 labels would be dropped arbitrarily. */
  const pts = p.points.slice(0, 320);
  const top = new Set(
    pts.filter((q) => q.quad === 'proven, under-distributed')
      .sort((a, b) => b.y - a.y).slice(0, 10).map((q) => q.label)
  );
  const points = pts.map((q) => ({
    x: Math.log10(Math.max(q.x, 1)),
    y: Math.log10(Math.max(q.y, 0.5)),
    r: 1,
    label: top.has(q.label) ? q.label.slice(0, 22) : '',
    color: QC[q.quad] || '#9a9aa2',
    _raw: q,
  }));
  return (
    `<p class="ws-q">A SKU that sells fast <em>where it is stocked</em> but is stocked
      almost nowhere is the cleanest whitespace signal in retail: demand is proven and
      the shelf has not caught up.</p>` +
    method(`<b>Method</b> — velocity is lifetime $ per store, so a SKU earns nothing here
      for merely being everywhere; reach is the store count itself. Median split on both
      axes. <b>${fmtInt(p.n)}</b> live SKUs with ${p.min_stores || 25}+ stores.`) +
    `<div class="ws-warn"><b>Tenure confound.</b> The committed extract carries no
      first-sale date, so lifetime $/store rewards a SKU for having existed longer. The
      alive-only cut removes the worst of it; one cheap column (<code>MIN(DATE)</code>
      per GTIN) would remove the rest. Read these as candidates, not forecasts.</div>` +
    stats([
      ['median velocity', money(p.median_velocity) + '/store'],
      ['median reach', fmtInt(p.median_stores) + ' stores'],
      ...p.quadrants.slice(0, 2).map((q) => [q.label, fmtInt(q.n)]),
    ]) +
    `<div class="panel-card"><h3 class="p-title">Velocity × reach — each dot one SKU</h3>` +
    scatter(points, {
      xLabel: 'stores (log scale)',
      yLabel: '$ per store (log scale)',
      xFmt: (v) => fmtCompact(Math.pow(10, v)),
      tip: (q) =>
        `${q._raw.label} — ${q._raw.brand} · ${fmtInt(q._raw.x)} stores · $${q._raw.y}/store · ${q._raw.quad}`,
    }) +
    `</div>` +
    `<h3 class="p-title">Fastest-selling SKUs that almost nobody stocks</h3>` +
    table(
      [
        { h: 'Product', get: (r) => esc(r.desc) },
        { h: 'Brand', get: (r) => esc(r.brand) },
        { h: 'Family', get: (r) => esc(r.family) },
        { h: 'Stores', get: (r) => fmtInt(r.stores), num: true },
        { h: '$/store', get: (r) => money(r.vel), num: true },
        { h: 'Revenue', get: (r) => money(r.rev), num: true },
      ],
      p.under.slice(0, 18),
      'High velocity, below-median distribution. The list is a shortlist to investigate, not a ranking to act on.'
    ) +
    `<h3 class="p-title">Family × size cells, by median velocity</h3>` +
    table(
      [
        { h: 'Flavor family', get: (r) => esc(r.family) },
        { h: 'Size', get: (r) => esc(r.size) },
        { h: 'SKUs', get: (r) => fmtInt(r.n), num: true },
        { h: 'Median $/store', get: (r) => money(r.med_vel), num: true },
        { h: 'Median stores', get: (r) => fmtInt(r.med_stores), num: true },
      ],
      p.cells,
      'Cells with at least 5 SKUs and a parseable size.'
    ) +
    needsList(p.needs)
  );
}

/* ================================================ 2. ATTRIBUTE DEMAND == */
function renderAttributes(p) {
  const bars = p.coefs.map((c) => ({ label: c.name, value: c.beta }));
  return (
    `<p class="ws-q">Which <em>attributes</em> carry velocity, once brand scale is held
      constant? Without that control the flavor coefficients would mostly be reading
      “Red&nbsp;Bull is big”.</p>` +
    method(`<b>Model</b> — ridge on log($/store) ~ flavor family + size bucket + audience +
      log(brand revenue). One level of each block is dropped as the reference cell, or the
      one-hots would be collinear with the intercept. Scored on a random 30% holdout:
      <b>${p.n_train}</b> train, <b>${p.n_test}</b> test.`) +
    stats([
      ['out-of-sample R²', p.r2_oos.toFixed(3)],
      ['model MAE', p.mae_model.toFixed(3), p.beats_baseline ? 'pos' : 'neg'],
      ['baseline MAE', p.mae_baseline.toFixed(3)],
      ['beats baseline', p.beats_baseline ? 'yes' : 'no', p.beats_baseline ? 'pos' : 'neg'],
    ]) +
    `<div class="panel-card"><h3 class="p-title">Standardised coefficients — effect on log $/store</h3>` +
    hBars(bars, { fmt: (v) => v.toFixed(3) }) +
    `</div>` +
    `<p class="ws-cap">Positive = higher velocity than the reference cell. Brand revenue
      dominating is the expected and correct result; it is in the model so the other rows
      mean something.</p>` +
    `<h3 class="p-title">Under-supplied cells — model says they should sell, few SKUs try</h3>` +
    table(
      [
        { h: 'Flavor family', get: (r) => esc(r.family) },
        { h: 'Size', get: (r) => esc(r.size) },
        { h: 'SKUs', get: (r) => fmtInt(r.n), num: true },
        {
          h: 'Mean residual',
          get: (r) => (r.mean_resid > 0 ? '+' : '') + r.mean_resid.toFixed(3),
          num: true,
          cls: (r) => (r.mean_resid > 0 ? 'pos' : 'neg'),
        },
      ],
      p.gaps,
      'Mean residual = how much the cell out-performs what its attributes predict. Positive with few SKUs is the whitespace read; cells need 6+ SKUs to appear.'
    ) +
    needsList(p.needs)
  );
}

/* ======================================================= 3. CLAIM SPACE == */
function renderClaims(p) {
  const c = p.coverage;
  const growing = p.rows.filter((r) => r.gnpd_delta_pp !== null);
  return (
    `<p class="ws-q">Which claims are spreading fastest across <em>new launches</em>, and
      are they earning anything?</p>` +
    `<div class="ws-warn"><b>Detection coverage is the headline here.</b> ${esc(p.caveat)}</div>` +
    stats([
      ['SKUs with a detectable claim', `${fmtInt(c.skus_detectable)} / ${fmtInt(c.skus_total)}`],
      ['of live SKUs', pct(c.sku_pct)],
      ['of revenue', pct(c.rev_pct, 2)],
    ]) +
    (growing.length
      ? `<div class="panel-card"><h3 class="p-title">Claim growth in new launches (GNPD, pp change)</h3>` +
        hBars(
          growing.map((r) => ({ label: r.claim, value: r.gnpd_delta_pp })),
          { fmt: (v) => (v > 0 ? '+' : '') + v.toFixed(1) + 'pp' }
        ) +
        `</div>`
      : '') +
    table(
      [
        { h: 'Claim', get: (r) => esc(r.claim) },
        {
          h: 'GNPD Δ (launches)',
          get: (r) => (r.gnpd_delta_pp === null ? '—' : (r.gnpd_delta_pp > 0 ? '+' : '') + r.gnpd_delta_pp + 'pp'),
          num: true,
          cls: (r) => (r.gnpd_delta_pp > 0 ? 'pos' : r.gnpd_delta_pp < 0 ? 'neg' : ''),
        },
        { h: 'SKUs detected', get: (r) => fmtInt(r.skus), num: true },
        { h: '% of detected rev', get: (r) => pct(r.rev_share_of_detected), num: true },
        { h: 'Velocity index', get: (r) => (r.vel_index === null ? '—' : r.vel_index.toFixed(2)), num: true },
      ],
      p.rows,
      'Velocity index: median $/store for the claim ÷ median across claims. Shares are WITHIN the detectable subset and understate every claim.'
    ) +
    method(`<b>Read it as</b> — ${esc(p.note)}`) +
    needsList(p.needs)
  );
}

/* ==================================================== 4. PRICE RESPONSE == */
function renderElasticity(p) {
  const po = p.pooled || {};
  const ref = p.reference || {};
  const ci = (o) => (o ? `${o.beta.toFixed(2)} [${o.lo.toFixed(2)}, ${o.hi.toFixed(2)}]` : '—');
  return (
    `<p class="ws-q">Does volume actually fall when price rises — and can this data even
      answer that?</p>` +
    method(`<b>The trap</b> — there is no price column in PDI; price is revenue ÷ units.
      The same measurement therefore sits on both sides of the regression with opposite
      signs, which drives the naive slope negative <em>even at a true elasticity of
      zero</em>. The panel ships two disjoint halves of stores, so pairing A-price with
      B-quantity makes the two errors independent and the mechanical term cancels.`) +
    `<div class="ws-stop"><b>Not identified at this grain.</b> ${esc(p.verdict)}</div>` +
    stats([
      ['A-price → B-units', ci(po.a_to_b), 'neg'],
      ['B-price → A-units', ci(po.b_to_a)],
      ['naive (biased)', ci(po.naive)],
      ['halves agree?', p.halves_agree ? 'yes' : 'no', p.halves_agree ? 'pos' : 'neg'],
    ]) +
    method(`<b>Reference specification</b> — <code>${esc(ref.source || 'price_models.py')}</code>
      carries cluster controls this pooling omits, and its two halves <em>do</em> agree:
      ${ref.a_to_b} and ${ref.b_to_a}, mean <b>${ref.mean}</b> on n=${ref.n}.
      ${esc(ref.note || '')} Prefer those numbers over the ones above.`) +
    `<h3 class="p-title">Per-family estimates — shown as evidence of instability</h3>` +
    `<div class="ws-warn">These are <b>not</b> estimates to use. Each rests on 72
      twelve-month changes against a fixed-weight index that barely moves within one
      family, and they range over ${p.per_family_spread} elasticity units — including
      positive values, which would mean raising price sells more. That spread is the
      argument for pooling, and it is why no per-family number is reported anywhere
      else on this site.</div>` +
    table(
      [
        { h: 'Flavor family', get: (r) => esc(r.family) },
        {
          h: 'Cross-half slope',
          get: (r) => r.cross.toFixed(2),
          num: true,
          cls: (r) => (r.cross > 0 ? 'neg' : ''),
        },
        { h: 'n', get: (r) => r.n, num: true },
      ],
      p.per_family,
      'A positive slope here is a symptom of the identification problem, not a finding about that flavor.'
    ) +
    needsList(p.needs)
  );
}

/* ================================================= 5. STATED vs REVEALED == */
function renderStated(p) {
  return (
    `<p class="ws-q">Consumers say they want functional benefits, natural caffeine and
      tea-inspired flavors. Do those preferences show up in what actually sells?</p>` +
    `<div class="ws-warn"><b>Only half of this comparison is sound.</b> ${esc(p.note)}</div>` +
    stats([
      ['concepts matched', fmtInt(p.n)],
      ['SKUs matched', fmtInt(p.skus_matched)],
      ['rank correlation', p.spearman === null ? 'not reported' : p.spearman.toFixed(3)],
    ]) +
    (p.spearman === null
      ? `<p class="ws-cap">No rank correlation is reported: ${p.n} concepts matched, and the
         threshold is six. An earlier build returned −0.949 on four points, which meant
         nothing at all.</p>`
      : '') +
    `<h3 class="p-title">Stated interest vs. what the POS data can detect</h3>` +
    table(
      [
        { h: 'Concept (Mintel)', get: (r) => esc(r.concept) },
        { h: 'Interest', get: (r) => pct(r.interest_pct), num: true },
        { h: 'SKUs found', get: (r) => fmtInt(r.skus), num: true },
        { h: 'Detected rev share', get: (r) => pct(r.rev_share, 2), num: true },
      ],
      p.rows,
      'The interest column is measured. The revenue column is a floor set by keyword detection on terse product descriptions — it is not the concept’s real footprint.'
    ) +
    `<h3 class="p-title">Why people say they drink it (Mintel, top-2-box)</h3>` +
    `<div class="panel-card">` +
    hBars(
      p.motivations.map((m) => ({ label: m.factor, value: m.top2box_pct })),
      { fmt: (v) => v.toFixed(1) + '%' }
    ) +
    `</div>` +
    `<p class="ws-cap">This chart is survey data reported as measured, and is the part of
      this tab you can rely on.</p>` +
    needsList(p.needs)
  );
}

/* ========================================================== 6. SURVIVAL == */
function renderSurvival(p) {
  const m = p.models;
  return (
    `<p class="ws-q">Which SKUs are still selling at the end of the window — and what
      predicts it?</p>` +
    method(`<b>Target</b> — survival to date: a last sale within the alive window. This is
      <em>not</em> the year-3 $100K bar in <code>predict_launch.py</code>; that needs the
      untracked per-year extract. Five-fold cross-validated AUC on
      <b>${fmtInt(p.n)}</b> SKUs, base rate <b>${(p.base_rate * 100).toFixed(1)}%</b>.`) +
    `<div class="ws-warn"><b>Read the model comparison, not the headline AUC.</b> Lifetime
      revenue is a legitimate predictor — bigger SKUs survive — but a SKU that died early
      necessarily accumulated less, so revenue is partly the outcome. The distribution-only
      row is the honest floor.</div>` +
    stats(
      m.map((x) => [x.label, x.auc.toFixed(3), x.auc > 0.7 ? 'pos' : ''])
    ) +
    `<div class="panel-card"><h3 class="p-title">Cross-validated AUC by feature set</h3>` +
    hBars(
      m.map((x) => ({ label: x.label, value: x.auc })),
      { fmt: (v) => v.toFixed(3) }
    ) +
    `</div>` +
    `<p class="ws-cap">Distribution alone reaches ${m[1].auc.toFixed(3)} against the full
      model's ${m[0].auc.toFixed(3)}. Most of what looks like a survival model is “how many
      stores stock it”.</p>` +
    `<h3 class="p-title">Survival rate by flavor family</h3>` +
    table(
      [
        { h: 'Flavor family', get: (r) => esc(r.family) },
        { h: 'SKUs', get: (r) => fmtInt(r.n), num: true },
        { h: 'Still selling', get: (r) => pct(r.survival_pct), num: true },
      ],
      p.by_family,
      'Families with at least 20 SKUs.'
    ) +
    needsList(p.needs)
  );
}

/* ================================================= 9. AUDIENCE x FLAVOR == */
function renderMatrix(p) {
  /* Colour by revenue per SKU — the headroom measure. A cell with $25M across
     33 SKUs beats one with $80M across 86, because the second is already fought
     over. Scale is a log ramp: the raw values span three orders of magnitude and
     a linear ramp would paint everything but the top cell white. */
  const byKey = new Map(p.rows.map((r) => [r.aud + '|' + r.family, r]));
  const vals = p.rows.map((r) => r.rev_per_sku).filter((v) => v > 0);
  const lo = Math.log10(Math.min(...vals));
  const hi = Math.log10(Math.max(...vals));
  const shade = (v) => {
    if (!v) return 'transparent';
    const t = (Math.log10(v) - lo) / (hi - lo || 1);
    return `rgba(0, 113, 227, ${(0.06 + t * 0.62).toFixed(3)})`;
  };
  const head =
    `<tr><th></th>${p.families.map((f) => `<th>${esc(f)}</th>`).join('')}</tr>`;
  const body = p.auds
    .map((a) => {
      const cells = p.families
        .map((f) => {
          const r = byKey.get(a + '|' + f);
          if (!r) return `<td class="cell" style="color:var(--dim)">·</td>`;
          return `<td class="cell" style="background:${shade(r.rev_per_sku)}" title="${esc(
            `${a} × ${f} — ${r.skus} SKUs · ${money(r.rev)} · ${money(r.rev_per_sku)}/SKU · ${r.survival_pct}% alive`
          )}">${fmtCompact(r.rev_per_sku)}</td>`;
        })
        .join('');
      return `<tr><td class="rowh">${esc(a)}</td>${cells}</tr>`;
    })
    .join('');
  return (
    `<p class="ws-q">Every audience × flavor cell, scored on revenue per SKU — the
      headroom measure. Adding survival rate and distribution separates “nobody tried it”
      from “people tried it and it died”.</p>` +
    method(`<b>Method</b> — ${esc(p.note)} Cells need 3+ SKUs to appear.
      <b>${fmtInt(p.n)}</b> SKUs across ${p.auds.length} audiences and
      ${p.families.length} families.`) +
    `<h3 class="p-title">Revenue per SKU — darker is more headroom</h3>` +
    `<div class="ws-matrix"><table><thead>${head}</thead><tbody>${body}</tbody></table></div>` +
    `<p class="ws-cap">A dot means fewer than 3 SKUs — too thin to read, and itself a
      kind of whitespace. Hover any cell for SKU count, revenue and survival.</p>` +
    `<h3 class="p-title">Thin but surviving — few SKUs, most still selling</h3>` +
    table(
      [
        { h: 'Audience', get: (r) => esc(r.aud) },
        { h: 'Flavor family', get: (r) => esc(r.family) },
        { h: 'SKUs', get: (r) => fmtInt(r.skus), num: true },
        { h: '$/SKU', get: (r) => money(r.rev_per_sku), num: true },
        { h: 'Still selling', get: (r) => pct(r.survival_pct), num: true },
        { h: 'Median stores', get: (r) => fmtInt(r.med_stores), num: true },
      ],
      p.thin,
      'At most 8 SKUs and at least 60% still selling: the market has not rejected these, there just are not many of them.'
    )
  );
}

/* ------------------------------------------------------------ tab registry -- */
const TABS = [
  { key: 'velocity', n: 1, title: 'Velocity × reach', render: renderVelocity },
  { key: 'attributes', n: 2, title: 'Attribute demand', render: renderAttributes },
  { key: 'claims', n: 3, title: 'Claim space', render: renderClaims },
  { key: 'elasticity', n: 4, title: 'Price response', render: renderElasticity },
  { key: 'stated', n: 5, title: 'Stated vs revealed', render: renderStated },
  { key: 'survival', n: 6, title: 'Survival', render: renderSurvival },
  { key: 'cannibalization', n: 7, title: 'Cannibalization', render: scaffold },
  { key: 'geographic', n: 8, title: 'Geographic', render: scaffold },
  { key: 'matrix', n: 9, title: 'Audience × flavor', render: renderMatrix },
  { key: 'nutrition', n: 10, title: 'Nutrition space', render: scaffold },
];

const TITLES = {
  velocity: 'Sells fast, stocked nowhere',
  attributes: 'What actually drives velocity',
  claims: 'Claims growing vs claims earning',
  elasticity: 'Price response, and whether it is identified',
  stated: 'What people say vs what they buy',
  survival: 'What predicts a SKU staying on shelf',
  cannibalization: 'Does a launch steal from your own shelf?',
  geographic: 'Which markets want which flavors',
  matrix: 'Audience × flavor headroom',
  nutrition: 'Sugar × caffeine positioning',
};

function statusLabel(s) {
  return { ok: 'computed', partial: 'partial', blocked: 'blocked', sample: 'sample data' }[s] || s;
}

function selectTab(key, push = true) {
  TABS.forEach((t) => {
    const btn = $(`#tab-${t.key}`);
    const panel = $(`#panel-${t.key}`);
    const on = t.key === key;
    if (btn) {
      btn.setAttribute('aria-selected', on ? 'true' : 'false');
      btn.tabIndex = on ? 0 : -1;
    }
    if (panel) panel.hidden = !on;
  });
  if (push && location.hash.slice(1) !== key) history.replaceState(null, '', `#${key}`);
  revealCards(document);
}

function boot() {
  const tabsEl = $('#ws-tabs');
  const panelsEl = $('#ws-panels');
  $('#ws-meta').innerHTML =
    `<b>${fmtInt(DATA.skus)}</b> SKUs · window ${esc(DATA.window || '')} · ` +
    `alive rule: ${esc(DATA.alive_rule)} · ${esc(DATA.coverage)}`;
  $('#ws-foot').textContent = `built ${DATA.generated_at || ''}`;

  tabsEl.innerHTML = TABS.map((t) => {
    const p = DATA.panels[t.key] || { status: 'blocked' };
    return `<button class="ws-tab" role="tab" id="tab-${t.key}" type="button"
      aria-controls="panel-${t.key}" aria-selected="false" tabindex="-1"
      title="${esc(statusLabel(p.status))}">
      <span class="ws-num">${t.n}</span>
      <span class="ws-dot d-${p.status}"></span>${esc(t.title)}</button>`;
  }).join('');

  panelsEl.innerHTML = TABS.map((t) => {
    const p = DATA.panels[t.key];
    let inner;
    try {
      inner = p ? t.render(p) : '<p class="ws-q">No data for this panel.</p>';
    } catch (err) {
      /* One panel throwing must not blank the other nine. */
      console.error(`panel ${t.key} failed`, err);
      inner = `<div class="ws-stop"><b>This panel failed to render.</b> The other tabs are
        unaffected; see the console for the error.</div>`;
    }
    return `<section class="ws-panel" role="tabpanel" id="panel-${t.key}"
      aria-labelledby="tab-${t.key}" hidden>
      <div class="ws-head">
        <h2>${t.n}. ${esc(TITLES[t.key] || t.title)}</h2>
        <span class="ws-pill ws-${p ? p.status : 'blocked'}">${esc(statusLabel(p ? p.status : 'blocked'))}</span>
      </div>${inner}</section>`;
  }).join('');

  tabsEl.addEventListener('click', (e) => {
    const btn = e.target.closest('.ws-tab');
    if (btn) selectTab(btn.id.replace('tab-', ''));
  });
  /* Arrow-key roving focus, which is what makes a tablist usable without a mouse. */
  tabsEl.addEventListener('keydown', (e) => {
    if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(e.key)) return;
    const i = TABS.findIndex((t) => $(`#tab-${t.key}`).getAttribute('aria-selected') === 'true');
    const next =
      e.key === 'Home' ? 0
        : e.key === 'End' ? TABS.length - 1
          : e.key === 'ArrowRight' ? (i + 1) % TABS.length
            : (i - 1 + TABS.length) % TABS.length;
    e.preventDefault();
    selectTab(TABS[next].key);
    $(`#tab-${TABS[next].key}`).focus();
  });

  const initial = TABS.some((t) => t.key === location.hash.slice(1))
    ? location.hash.slice(1)
    : TABS[0].key;
  selectTab(initial, false);
}

(async () => {
  DATA = await requireAuth({ dataUrl: 'data/whitespace.json' });
  boot();
})();
