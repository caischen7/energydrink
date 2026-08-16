/*
 * Monte Carlo launch simulator.
 *
 * Every other panel on this page describes what has already happened. This one
 * asks the forward question a launch decision actually turns on: given where we
 * launch, what range of five-year revenue have comparable products produced?
 *
 * It is a bootstrap, not a model. Each trial draws one real launch's complete
 * observed trajectory from the pool of comparables and replays it. Nothing is
 * fitted, so the skew, the survival pattern and the year-to-year
 * autocorrelation all come from the data rather than from an assumption about
 * its shape — which matters here, because the distribution is close to
 * degenerate: half of these SKUs peak under $22K a year.
 *
 * The donor pool is horizon-matched (see data/scripts/add_montecarlo.py): a
 * five-year run samples only launches with five observed years. That keeps
 * every simulated year backed by a real observation of that year, at the cost
 * of a smaller and older sample, which the panel states.
 *
 * The simulation is seeded, so the same selection always produces the same
 * numbers. An unseeded simulator that shifts its answer on every re-render
 * invites the reader to re-roll until they like the result.
 */
import { multiLine } from './charts.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const TRIALS = 10000;

const money = (n) =>
  n >= 1e9 ? '$' + (n / 1e9).toFixed(2) + 'B' :
  n >= 1e6 ? '$' + (n / 1e6).toFixed(1) + 'M' :
  n >= 1e3 ? '$' + (n / 1e3).toFixed(0) + 'K' : '$' + Math.round(n);

/* mulberry32 — small, fast, and seedable. */
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const pct = (sorted, p) =>
  sorted[Math.max(0, Math.min(sorted.length - 1, Math.round(p * (sorted.length - 1))))];

/*
 * Widen the comparable set until it is big enough to sample, and say which
 * step it stopped at. A pool of six is not a distribution, and silently
 * sampling one would be the most dangerous thing this panel could do.
 */
function pool(all, horizon, aud, fam, min) {
  const deep = all.filter((t) => t.p.length >= horizon);
  const steps = [
    { rows: deep.filter((t) => t.a === aud && t.f === fam), how: `${aud} × ${fam}` },
    { rows: deep.filter((t) => t.a === aud), how: `${aud}, any flavor` },
    { rows: deep.filter((t) => t.f === fam), how: `${fam}, any audience` },
    { rows: deep, how: 'all launches' },
  ];
  const exact = steps[0].rows.length;
  for (const s of steps) if (s.rows.length >= min) return { ...s, exact, widened: s !== steps[0] };
  return { ...steps[3], exact, widened: true };
}

function simulate(rows, horizon, scaleBar, seed = 12345) {
  const rand = rng(seed);
  const cum = Array.from({ length: horizon }, () => []);
  const totals = [];
  let hitScale = 0;
  let aliveEnd = 0;
  /* Same materiality rule as the base-rate panel above: a SKU counts as alive
     in a year only if it does at least 10% of its own peak. Using "any revenue
     at all" here instead put year-5 survival at 83% against that panel's 25%,
     two numbers on one page describing the same thing. The naive definition is
     the one that is wrong - most of these barcodes trickle. */
  const MATERIAL = 0.10;

  for (let i = 0; i < TRIALS; i++) {
    const t = rows[Math.floor(rand() * rows.length)];
    let run = 0;
    let best = 0;
    for (let y = 0; y < horizon; y++) {
      const v = t.p[y] || 0;
      run += v;
      best = Math.max(best, v);
      cum[y].push(run);
    }
    totals.push(run);
    if (best >= scaleBar) hitScale++;
    if (best > 0 && (t.p[horizon - 1] || 0) >= best * MATERIAL) aliveEnd++;
  }

  cum.forEach((c) => c.sort((a, b) => a - b));
  totals.sort((a, b) => a - b);
  return {
    bands: [0.1, 0.25, 0.5, 0.75, 0.9].map((p) => ({ p, path: cum.map((c) => pct(c, p)) })),
    total: {
      p10: pct(totals, 0.1), p25: pct(totals, 0.25), p50: pct(totals, 0.5),
      p75: pct(totals, 0.75), p90: pct(totals, 0.9),
      mean: totals.reduce((s, v) => s + v, 0) / totals.length,
    },
    pScale: (hitScale / TRIALS) * 100,
    pAlive: (aliveEnd / TRIALS) * 100,
    pNothing: (totals.filter((v) => v < 10000).length / TRIALS) * 100,
  };
}

export function initSimulator(O) {
  const M = O.montecarlo;
  const host = $('#sim');
  if (!M || !host) {
    if (host) host.innerHTML =
      '<p class="sec-note">No simulation data — run data/scripts/add_montecarlo.py.</p>';
    return;
  }

  const auds = O.matrix.map((r) => r.aud);
  const fams = O.fams;

  $('#sim-controls').innerHTML = `
    <label class="sim-f"><span class="mono">AUDIENCE</span>
      <select id="sim-aud">${auds.map((a) => `<option>${esc(a)}</option>`).join('')}</select></label>
    <label class="sim-f"><span class="mono">FLAVOR FAMILY</span>
      <select id="sim-fam">${fams.map((f) => `<option>${esc(f)}</option>`).join('')}</select></label>
    <label class="sim-f"><span class="mono">HORIZON</span>
      <select id="sim-hz">
        <option value="3">3 years</option>
        <option value="5" selected>5 years</option>
      </select></label>`;

  function run() {
    const aud = $('#sim-aud').value;
    const fam = $('#sim-fam').value;
    const hz = +$('#sim-hz').value;

    const P = pool(M.trajectories, hz, aud, fam, M.min_donors);
    const r = simulate(P.rows, hz, M.scale_bar);
    const lift = M.cell_scale[`${aud}|${fam}`] || M.scale;

    const yrs = Array.from({ length: hz }, (_, i) => 'Yr ' + (i + 1));
    $('#sim-chart').innerHTML = multiLine(yrs, [
      { name: 'Top 10% of outcomes', color: '#0071e3', values: r.bands[4].path },
      { name: 'Upper quartile', color: '#7fb4ee', values: r.bands[3].path },
      { name: 'Median', color: '#1d1d1f', values: r.bands[2].path },
      { name: 'Lower quartile', color: '#e0b0aa', values: r.bands[1].path },
      { name: 'Bottom 10%', color: '#c0392b', values: r.bands[0].path },
    ], {
      labelEvery: 1,
      /* Log: the top decile runs ~30x the median here, and on a linear axis
         the median and both lower bands sit flat on the floor. */
      log: true,
      yFmt: money,
      /* Extra headroom so the padL gutter fits a "$1.5M" label. */
      padL: 62,
    });

    $('#sim-cards').innerHTML = [
      ['Median outcome', money(r.total.p50), `${hz}-year panel revenue`],
      ['Top 10%', money(r.total.p90), `${money(r.total.p75)} at the upper quartile`],
      ['Bottom 10%', money(r.total.p10), `${r.pNothing.toFixed(0)}% of trials never clear $10K`],
      ['Reaches $1M a year', r.pScale.toFixed(1) + '%', 'in any year of the horizon'],
      [`Still selling in year ${hz}`, r.pAlive.toFixed(0) + '%',
        'at 10%+ of its own peak, as above'],
    ].map(([k, v, n]) => `<div class="sim-c">
        <span class="sim-k mono">${esc(k)}</span><b>${esc(v)}</b>
        <span class="sim-n mono">${esc(n)}</span></div>`).join('');

    /* The mean sits above the 75th percentile in a distribution this skewed.
       Saying so is the point: an "expected value" here is not a typical case. */
    const skewNote = r.total.mean > r.total.p75
      ? ` The average trial returns ${money(r.total.mean)} — above the 75th percentile, `
        + `because a handful of very large outcomes carry it. Plan against the median, not the mean.`
      : '';

    $('#sim-note').innerHTML =
      `<b>${P.rows.length} comparable launches</b> sampled ${TRIALS.toLocaleString()} times` +
      (P.widened
        ? ` — only ${P.exact} launch${P.exact === 1 ? '' : 'es'} match ${esc(aud)} × ${esc(fam)} over `
          + `${hz} years, too few to sample, so the pool widened to <b>${esc(P.how)}</b>.`
        : ` from <b>${esc(P.how)}</b>.`) +
      skewNote;

    $('#sim-scale').innerHTML =
      `Figures are <b>PDI panel dollars</b> — convenience only, and a sample of it. At this cell's `
      + `measured panel-to-all-channel ratio of <b>${lift}×</b>, the median lands near `
      + `<b>${money(r.total.p50 * lift)}</b> and the top decile near <b>${money(r.total.p90 * lift)}</b> `
      + `of all-channel revenue. That conversion inherits every assumption behind the ratio, so it is `
      + `shown beside the measured figure rather than instead of it.`;
  }

  ['#sim-aud', '#sim-fam', '#sim-hz'].forEach((s) =>
    $(s).addEventListener('change', run));

  /* Open on the pocket the rest of the page argues for. */
  $('#sim-aud').value = 'Women (fitness & wellness)';
  $('#sim-fam').value = 'Sour & candy';
  run();

  $('#sim-method').innerHTML = '<b>How this is simulated:</b> ' + esc(M.method);
  $('#sim-caveat').innerHTML = '<b>What it cannot tell you:</b> ' + esc(M.caveat);
}
