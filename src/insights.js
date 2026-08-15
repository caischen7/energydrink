/*
 * Insights page — cross-source findings plus the data-model (ER) map.
 *
 * Reads the same nginx-guarded aggregate as the dashboard (public/data/dashboard.json),
 * so the licensed figures are never shipped in the bundle. The `insights` key is written
 * by data/scripts/add_insights.py.
 */
import '@fontsource-variable/inter';
import './dashboard.css';
import './insights.css';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/* colour per source so a finding and its table read as the same family */
/* Each hue is used BOTH as text on white and as a tag background under white
   text, so it has to clear 4.5:1 in both directions. The pastel iOS greens,
   ambers and teals cleared neither - #34c759 measured 2.2:1. */
const HUE = {
  pdi: '#0071e3', mintel_survey: '#178037', gnpd: '#a35c00', passport: '#5e5ce6',
  simmons: '#c9184a', usda: '#00807f', mulo: '#7a4bc4', combined: '#1d1d1f',
};
const hue = (s) => HUE[s] || '#6e6e73';

function card(i, srcName) {
  return `
  <article class="ins-card${i.tier === 'headline' ? ' hl' : ''}" style="--h:${hue(i.src)}">
    <header>
      <span class="ins-src mono">${esc(srcName)}</span>
      ${i.tier === 'headline' ? '<span class="ins-tag mono">HEADLINE</span>' : ''}
    </header>
    <h3>${esc(i.title)}</h3>
    <p class="ins-find">${esc(i.finding)}</p>
    <p class="ins-why"><b>So what:</b> ${esc(i.why)}</p>
    <div class="ins-metric mono">${esc(i.metric)}</div>
  </article>`;
}

/* ---------- ER diagram: hand-placed columns so the join paths stay legible ---------- */
const POS = {
  pdi_daily_agg:              [430, 250],
  pdi_master_gtin:            [430, 105],
  pdi_stores:                 [430, 395],
  pdi_energy_drinks_monthly:  [125, 250],
  brand_crosswalk:            [125, 105],
  usda_branded_foods:         [745, 105],
  gnpd_products:              [745, 250],
  simmons_brand_profiles:     [745, 395],
  passport_brand_shares:      [125, 395],
  mintel_mulo_brand_sales:    [125, 480],
  mintel_survey_data:         [745, 480],
};
const BOX = { w: 200, h: 46 };

function erDiagram(er) {
  const W = 960, H = 560;
  const anchor = (id) => {
    const [x, y] = POS[id] || [W / 2, H / 2];
    return { x, y, cx: x + BOX.w / 2, cy: y + BOX.h / 2 };
  };
  /*
   * Edge labels sat at the exact midpoint, so edges whose midpoints coincide
   * stacked their labels — and some landed on a table box. Try a few positions
   * along each edge and take the first that is clear of everything placed so far.
   */
  const placedLabels = er.tables.map((t) => {
    const p2 = anchor(t.label === undefined ? t.id : t.id);
    return { x: p2.cx, y: p2.cy, w: BOX.w, h: BOX.h };
  });
  const freeSpot = (a, b) => {
    for (const f of [0.5, 0.36, 0.64, 0.28, 0.72]) {
      const x = a.cx + (b.cx - a.cx) * f;
      const y = a.cy + (b.cy - a.cy) * f;
      const hit = placedLabels.some((q) =>
        Math.abs(q.x - x) < (q.w + 104) / 2 - 6 && Math.abs(q.y - y) < (q.h + 18) / 2 - 4);
      if (!hit) { placedLabels.push({ x, y, w: 104, h: 18 }); return [x, y]; }
    }
    const x = a.cx + (b.cx - a.cx) * 0.5;
    const y = a.cy + (b.cy - a.cy) * 0.5;
    placedLabels.push({ x, y, w: 104, h: 18 });
    return [x, y];
  };

  const edges = er.edges.map((e) => {
    const a = anchor(e.a), b = anchor(e.b);
    const dash = e.kind === 'strong' ? '' : e.kind === 'fuzzy' ? 'stroke-dasharray="6 5"' : 'stroke-dasharray="2 6"';
    const col = e.kind === 'strong' ? '#2a78d6' : e.kind === 'fuzzy' ? '#eb6834' : '#c3c2b7';
    const [mx, my] = freeSpot(a, b);
    return `<g class="er-edge">
      <line x1="${a.cx}" y1="${a.cy}" x2="${b.cx}" y2="${b.cy}" stroke="${col}" stroke-width="1.6" ${dash}/>
      <rect x="${mx - 52}" y="${my - 9}" width="104" height="18" rx="9" fill="var(--bg)" opacity=".92"/>
      <text x="${mx}" y="${my + 4}" text-anchor="middle" class="er-lbl">${esc(e.label)}</text>
      <title>${esc(e.a)} ↔ ${esc(e.b)} on ${esc(e.on)}</title>
    </g>`;
  }).join('');

  const boxes = er.tables.map((t) => {
    const p = anchor(t.id);
    return `<g class="er-node">
      <rect x="${p.x}" y="${p.y}" width="${BOX.w}" height="${BOX.h}" rx="9"
            fill="var(--bg)" stroke="${hue(t.src)}" stroke-width="1.8"/>
      <rect x="${p.x}" y="${p.y}" width="5" height="${BOX.h}" rx="2.5" fill="${hue(t.src)}"/>
      <text x="${p.x + 15}" y="${p.y + 20}" class="er-t">${esc(t.label)}</text>
      <text x="${p.x + 15}" y="${p.y + 36}" class="er-r">${esc(t.rows)} rows</text>
      <title>${esc(t.note)}</title>
    </g>`;
  }).join('');

  return `<div class="er-wrap">
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Entity relationship diagram of the data sources">
      ${edges}${boxes}
    </svg>
    <div class="er-key mono">
      <span><i class="k solid"></i>key join</span>
      <span><i class="k dash"></i>fuzzy join — normalise first</span>
      <span><i class="k dot"></i>no shared key</span>
    </div>
  </div>`;
}

function main(data) {
  const ins = data.insights;
  if (!ins) {
    $('#headlines').innerHTML = '<p class="sec-note">No insight set in this aggregate — run data/scripts/add_insights.py.</p>';
    return;
  }
  const nameOf = Object.fromEntries(ins.sources.map((s) => [s.id, s.name]));
  nameOf.combined = 'Cross-source';

  $('#headlines').innerHTML = ins.insights.filter((i) => i.tier === 'headline')
    .map((i) => card(i, nameOf[i.src])).join('');

  const order = [...ins.sources.map((s) => s.id), 'combined'];
  $('#sources').innerHTML = order.map((sid) => {
    const items = ins.insights.filter((i) => i.src === sid);
    if (!items.length) return '';
    const meta = ins.sources.find((s) => s.id === sid);
    const head = meta
      ? `<h3 class="srcb-t">${esc(meta.name)} <span class="srcb-k mono">${esc(meta.kind)}</span></h3>
         <p class="srcb-s mono dim">${esc(meta.scale)}</p>
         <p class="srcb-w">${esc(meta.what)}</p>
         <p class="srcb-l"><b>Blind spot:</b> ${esc(meta.limit)}</p>`
      : `<h3 class="srcb-t">Cross-source <span class="srcb-k mono">Convergent evidence</span></h3>
         <p class="srcb-w">Findings that only hold because more than one dataset says the same thing.</p>`;
    return `<section class="srcb" style="--h:${hue(sid)}">
      <div class="srcb-head">${head}</div>
      <div class="ins-grid">${items.map((i) => card(i, nameOf[i.src])).join('')}</div>
    </section>`;
  }).join('');

  $('#er').innerHTML = erDiagram(ins.er);
  $('#er-tables').innerHTML = `<div class="tbl-wrap"><table class="intel-table mono">
    <thead><tr><th class="tl">TABLE</th><th class="tl">ROWS</th><th class="tl">KEY COLUMNS</th><th class="tl">NOTE</th></tr></thead>
    <tbody>${ins.er.tables.map((t) => `<tr>
      <td class="tl"><span class="dot" style="background:${hue(t.src)}"></span>${esc(t.label)}</td>
      <td class="tl">${esc(t.rows)}</td>
      <td class="tl cols">${t.cols.map((c) => `<code>${esc(c)}</code>`).join(' ')}</td>
      <td class="tl note">${esc(t.note)}</td></tr>`).join('')}</tbody></table></div>`;

  $('#gen-at').textContent = new Date(data.generated_at).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

requireAuth().then(main);
