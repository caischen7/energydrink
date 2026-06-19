/*
 * OPPORTUNITY FINDER — the dashboard's one prescriptive panel: where descriptive
 * panels stop at "what exists," this one ranks "where's the gap." Combines two
 * already-collected-but-unused signals:
 *   - flavor_demand: mentions (demand, from 125k YT comments + Amazon reviews)
 *     vs products (Amazon SKU count, i.e. supply) → a white-space score.
 *   - voice_of_customer: per-theme sentiment → unmet-need rate (neg / mentions).
 */
import { scatter, panel, fmtInt } from '../charts.js';

export function opportunityFinder(data) {
  const fd = data.flavor_demand;

  // White-space score: demand per unit of supply. +1 on products avoids
  // divide-by-zero and keeps a zero-SKU flavor finite rather than infinite.
  const ranked = fd
    .map((d) => ({ ...d, score: d.mentions / (d.products + 1) }))
    .sort((a, b) => b.score - a.score);

  const top3 = ranked.slice(0, 3);

  const pts = fd.map((d) => ({
    x: d.products,
    y: d.mentions,
    r: d.avg_rating ?? 4.2,
    label: d.flavor,
  }));

  const chart = scatter(pts, {
    xLabel: 'PRODUCTS ON AMAZON (SUPPLY)',
    yLabel: 'MENTIONS (DEMAND)',
    xMin: 0,
    xFmt: (v) => Math.round(v),
  });

  // Unmet-need theme ranked by negative-sentiment RATE, not raw complaint count.
  const voc = data.voice_of_customer
    .map((d) => ({ ...d, negRate: d.neg / d.mentions }))
    .sort((a, b) => b.negRate - a.negRate);
  const worst = voc[0];
  const worstPct = Math.round(worst.negRate * 100);

  const [g1, g2, g3] = top3;
  const insight = `Highest white-space score: <b class="volt">${g1.flavor}</b> (${fmtInt(g1.mentions)} mentions on just ${g1.products} SKU${g1.products === 1 ? '' : 's'}), followed by ${g2.flavor} (${fmtInt(g2.mentions)} mentions, ${g2.products} SKUs) and ${g3.flavor} (${fmtInt(g3.mentions)} mentions, ${g3.products} SKUs) — demand the shelf hasn't caught up to. On the needs side, <b class="volt">${worst.theme}</b> carries the highest complaint rate (${worstPct}% negative) of any theme tracked — the clearest unmet need to design against.`;

  return panel(
    'opportunity',
    14,
    'OPPORTUNITY FINDER',
    'WHITE-SPACE SCORE · DEMAND (MENTIONS) vs SUPPLY (SKUS) · FLAVOR DEMAND BOARD + VOICE OF CUSTOMER',
    chart,
    insight
  );
}
