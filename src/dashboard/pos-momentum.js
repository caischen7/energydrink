/*
 * REAL BRAND MOMENTUM (POS) — measured sell-through, not social proxy.
 *
 * Every other momentum signal on this dashboard is inferred from social
 * chatter. This one is dollars actually rung up at the register, from the PDI
 * convenience-store panel (trailing 12 months vs the prior 12, partial final
 * month excluded).
 *
 * Why it earns its own panel: the two signals disagree, and the social one is
 * wrong. "Who's Moving" ranks Bang as a riser on mention share; its actual
 * sales fell 15.6%. See docs/bigquery-findings.md.
 */
import { hBars, panel, fmtCompact, VOLT } from '../charts.js';

const GREEN = '#34c759';
const RED = '#ff3b30';

export function posMomentum(data) {
  const rows = data.pos_momentum;
  if (!rows?.length) return '';

  // Rank by growth, but only among brands big enough to read. Tiny brands post
  // absurd percentages off a near-zero base (one here is +1880% on $2.2M) and
  // would crowd out the real story.
  const material = rows.filter((d) => d.revenue >= 10_000_000);
  const ranked = [...material].sort((a, b) => b.yoy - a.yoy);

  // hBars scales bar length from the value, so a negative would collapse to a
  // 2px stub. Length carries magnitude; direction is the arrow + color.
  const bars = ranked.map((d) => ({
    label: `${d.yoy >= 0 ? '▲' : '▼'} ${d.brand}`,
    value: Math.abs(d.yoy),
    color: d.yoy >= 0 ? GREEN : RED,
  }));

  const top = ranked[0];
  const worst = ranked[ranked.length - 1];
  const leader = [...rows].sort((a, b) => b.share - a.share)[0];

  // Category growth = total this year vs total last year, across every brand
  // (including the small ones filtered out of the chart).
  const now = rows.reduce((s, d) => s + d.revenue, 0);
  const then = rows.reduce((s, d) => s + d.prior_revenue, 0);
  const cat = 100 * (now / then - 1);

  const insight =
    `<b class="volt">${top.brand} is the real breakout: ${top.yoy > 0 ? '+' : ''}${top.yoy}% YoY</b> ` +
    `(${fmtCompact(top.revenue)} in trailing-12-month revenue, ${top.share_delta > 0 ? '+' : ''}${top.share_delta}pp of share). ` +
    `The category grew ${cat.toFixed(1)}%, so anything below that is losing ground in relative terms — ` +
    `including ${leader.brand}, still the largest at ${leader.share}% share but growing only ${leader.yoy}% ` +
    `and shedding ${Math.abs(leader.share_delta)}pp a year. ${worst.brand} is falling fastest at ${worst.yoy}%. ` +
    `This is measured sell-through, so where it contradicts the mention-share panels above, trust this one.`;

  return panel(
    'pos-momentum',
    16,
    'REAL BRAND MOMENTUM — SELL-THROUGH',
    'PDI C-STORE POS · TRAILING 12MO vs PRIOR 12MO · % REVENUE CHANGE · BRANDS >$10M',
    hBars(bars, { fmt: (v) => v.toFixed(1) + '%', labelW: 160, accent: VOLT }),
    insight
  );
}
