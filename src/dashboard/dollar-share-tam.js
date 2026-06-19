/*
 * COMPETITIVE $ SHARE + TAM — adds brand-level dollar share to the dashboard's
 * existing category-level market size (market.size / market.facts). Lets you
 * read a flavor/spec gap found elsewhere against whether the market it sits in
 * is realistically contestable, or already locked up by Monster/Red Bull
 * distribution and shelf space.
 */
import { hBars, panel, VOLT } from '../charts.js';

export function dollarShareTam(data) {
  const m = data.market;
  const share = [...m.dollar_share].sort((a, b) => b.pct - a.pct);
  const meta = m.dollar_share_meta;
  const totalB = parseFloat(m.facts.total_2024_busd);

  const rows = share.map((d, i) => ({
    label: d.brand,
    value: d.pct,
    color: i === 0 ? VOLT : '#c7c7cc',
  }));

  const chart = hBars(rows, { fmt: (v) => v + '%', labelW: 150, accent: '#c7c7cc' });

  const top = share[0];
  const second = share[1];
  const others = share.find((d) => d.brand === 'All others') || share[share.length - 1];
  const topTamB = (top.pct / 100) * totalB;
  const incumbentPct = top.pct + second.pct;

  const insight = `${top.brand} holds the largest slice of US retail dollar share at <b class="volt">${top.pct}%</b> — illustratively, that share applied to the $${totalB.toFixed(1)}B <em>global</em> 2024 category implies a <b class="volt">$${topTamB.toFixed(1)}B</b> ceiling if it held worldwide (US share against global TAM, an order-of-magnitude estimate, not a real global figure). ${meta.note.split('.')[0]}. ${top.brand}/${second.brand} alone own ${incumbentPct}% of US retail dollars — a flavor or spec gap found elsewhere is more contestable in the ${others.pct}% "${others.brand}" remainder than in shelf space the two incumbents already control. Sources: ${meta.sources}.`;

  return panel(
    'dollar-share',
    16,
    'COMPETITIVE $ SHARE + TAM',
    `US RETAIL DOLLAR SHARE · AS OF ${meta.as_of} · BEVERAGE-DIGEST / C-STORE DIVE / INVESTOR DISCLOSURES`,
    chart,
    insight
  );
}
