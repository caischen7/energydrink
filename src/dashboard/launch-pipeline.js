/*
 * LAUNCH PIPELINE — what the industry is actually betting on.
 *
 * Mintel GNPD records real product launches. Comparing how often each
 * positioning claim appears on 2018-20 launches vs 2024-26 launches shows
 * where the category is moving *before* it shows up in sales — the closest
 * thing to a leading indicator in this dataset.
 *
 * The uncomfortable finding for our own product thesis: "sugar free" is on
 * 72% of recent launches. It is not white space; it is the price of entry.
 */
import { hBars, VOLT } from '../charts.js';
import { panel } from './_panel.js';

const GREEN = '#34c759';
const DIMGREY = '#c7c7cc';

/* Claim labels are Mintel taxonomy strings — trim the prefix for display. */
/* GNPD claim strings are taxonomy paths — keep the part that distinguishes them. */
const short = (c) =>
  c.replace(/^Functional - /, '')
    .replace(/^Free from /, 'No ')
    .replace(/^Ethical - Environmentally Friendly Package.*/i, 'Eco packaging')
    .replace(/^Ethical - /, '')
    .replace(/^No Added\/Artificial (\w+)/i, (m, w) => 'No artificial ' + w.toLowerCase())
    .replace(/^Vegan\/No Animal Ingredients.*/i, 'Vegan')
    .replace(/ Ingredients$/, '');

export function launchPipeline(data) {
  const rows = data.launch_claims;
  if (!rows?.length) return '';

  // Only claims with enough launches behind them to be meaningful, then the
  // biggest movers in each direction.
  const solid = rows.filter((d) => d.n >= 25);
  const rising = [...solid].sort((a, b) => b.delta - a.delta).slice(0, 8);
  const fading = [...solid].sort((a, b) => a.delta - b.delta).slice(0, 4);

  const bars = [...rising, ...fading].map((d) => ({
    label: `${d.delta >= 0 ? '▲' : '▼'} ${short(d.claim)}`,
    value: Math.abs(d.delta),
    color: d.delta >= 0 ? GREEN : DIMGREY,
  }));

  const brain = solid.find((d) => /Brain/.test(d.claim));
  const sugar = solid.find((d) => /^Sugar Free/.test(d.claim));
  const beauty = solid.find((d) => /Nails|Skin/.test(d.claim));

  const insight =
    `<b class="volt">Cognitive is the category's new center of gravity</b> — ` +
    `"${short(brain.claim)}" appears on ${brain.late}% of 2024-26 launches, up from ${brain.early}% ` +
    `(${brain.delta > 0 ? '+' : ''}${brain.delta}pp). ` +
    `Meanwhile <b class="volt">sugar-free is now table stakes, not white space</b>: ${sugar.late}% of new ` +
    `launches claim it, up from ${sugar.early}%. ` +
    (beauty
      ? `The genuinely new space is beauty-function — "${short(beauty.claim)}" went ${beauty.early}% → ${beauty.late}%, ` +
        `from nothing to a real segment. Notably that is Alani Nu's positioning, and Alani Nu is the fastest-growing ` +
        `brand in the sell-through panel above — two independent sources telling the same story.`
      : '');

  return panel(
    'launch-pipeline',
    17,
    'LAUNCH PIPELINE — WHERE THE BETS ARE',
    'MINTEL GNPD · 766 REAL LAUNCHES · CLAIM PREVALENCE 2024-26 vs 2018-20 · Δ PERCENTAGE POINTS',
    hBars(bars, { fmt: (v) => v.toFixed(1) + 'pp', labelW: 210, accent: VOLT }),
    insight
  );
}
