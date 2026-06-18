/*
 * ION_OS // MARKET INTEL — dashboard logic.
 * Loads the precomputed aggregate (src/data/dashboard.json), renders every
 * panel with the SVG chart builders, wires the sortable cross-platform table,
 * counts up the KPI readouts, and reveals charts on scroll.
 */
import './dashboard.css';
import data from './data/dashboard.json';
import { hBars, vBars, scatter, area, multiLine, fmtCompact, fmtInt, VOLT, ICE } from './charts.js';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

/* ---------- KPI strip ---------- */
function renderKpis() {
  const k = data.kpis;
  const cells = [
    ['BRANDS TRACKED', k.brands, ''],
    ['AMAZON SKUS', k.amazon_products, ''],
    ['REVIEWS PARSED', k.amazon_reviews, ''],
    ['IG POSTS', k.instagram_posts, ''],
    ['YT VIDEOS', k.youtube_videos, ''],
    ['YT COMMENTS MINED', k.youtube_comments, ''],
    ['ENERGY-CTX REACH', k.youtube_views, 'VIEWS'],
    ['DATA POINTS', k.data_points, ''],
  ];
  $('#kpis').innerHTML = cells
    .map(
      ([label, val, unit]) => `
      <div class="kpi">
        <span class="kpi-n" data-count="${val}">0</span>${unit ? `<span class="kpi-u">${unit}</span>` : ''}
        <span class="kpi-l mono">${label}</span>
      </div>`
    )
    .join('');
}

/* ---------- panel scaffold ---------- */
function panel(id, idx, title, meta, bodyHTML, insight) {
  return `
  <section class="panel-card reveal" id="${id}">
    <header class="pc-head mono">
      <span class="pc-id">${String(idx).padStart(2, '0')}</span>
      <h2 class="pc-title">${title}</h2>
      <span class="pc-meta">${meta}</span>
    </header>
    <div class="pc-body">${bodyHTML}</div>
    ${insight ? `<footer class="pc-insight mono"><b class="volt">&gt;</b> ${insight}</footer>` : ''}
  </section>`;
}

/* ---------- charts ---------- */
function shareOfVoice() {
  const rows = data.share_of_voice.slice(0, 12).map((d, i) => ({
    label: d.brand,
    value: d.views,
    color: i === 0 ? VOLT : undefined,
  }));
  const top = data.share_of_voice[0];
  const two = data.share_of_voice[1];
  const exclB = (data.sov_excluded.views / 1e9).toFixed(1);
  return panel(
    'sov',
    1,
    'SHARE OF VOICE',
    'YOUTUBE REACH · FRACTIONAL ATTRIBUTION · MUSIC/NOISE REMOVED',
    hBars(rows, { unit: 'views', accent: '#8fa600' }),
    `${top.brand} (${fmtCompact(top.views)}) and ${two.brand} (${fmtCompact(two.views)}) run neck-and-neck once ${exclB}B views of false-matched music clips are stripped out — attention is split between two legacy leaders, not monopolized.`
  );
}

/* per-brand trailing-12-month mention share over time */
function mentionMomentum() {
  const mm = data.mention_momentum;
  const series = mm.brands.map((b) => ({ brand: b.brand, values: b.share }));
  const r = mm.risers[0];
  return panel(
    'momentum',
    2,
    'BRAND MOMENTUM',
    `TRAILING-12-MO SHARE OF YT MENTIONS · ${mm.months[0]} → ${mm.complete_through}`,
    multiLine(mm.months, series, { labelEvery: 12 }),
    `Who's winning attention over time, normalized for the growing corpus. ${r.brand} has the steepest climb (${r.delta > 0 ? '+' : ''}${r.delta}pp YoY) — a rising challenger here is an earlier signal than raw size.`
  );
}

/* rising / cooling leaderboard */
function risingBrands() {
  const mm = data.mention_momentum;
  const row = (m, up) =>
    `<li><span class="rk-b">${m.brand}</span><span class="rk-d ${up ? 'up' : 'down'}">${up ? '▲' : '▼'} ${Math.abs(m.delta)}pp</span><span class="rk-n mono dim">${m.now}% now</span></li>`;
  const risers = mm.risers.filter((m) => m.delta > 0).map((m) => row(m, true)).join('');
  const fallers = mm.fallers.filter((m) => m.delta < 0).map((m) => row(m, false)).join('');
  return panel(
    'rising',
    3,
    'WHO’S MOVING',
    'Δ MENTION SHARE · LATEST 12-MO vs PRIOR 12-MO',
    `<div class="rank-cols">
      <div class="rank-col"><h4 class="mono volt">▲ RISING</h4><ol class="rank">${risers}</ol></div>
      <div class="rank-col"><h4 class="mono dim">▼ COOLING</h4><ol class="rank">${fallers}</ol></div>
    </div>`,
    `${mm.risers[0].brand} is gaining fastest (${mm.risers[0].delta > 0 ? '+' : ''}${mm.risers[0].delta}pp); ${mm.fallers[0].brand} is fading (${mm.fallers[0].delta}pp). Watch the climbers — that's where the next breakout forms.`
  );
}

function categoryMomentum() {
  const cm = data.category_momentum;
  const series = cm.months.map((m, i) => ({ label: m, value: cm.t12m_videos[i] }));
  const first = cm.t12m_videos[0];
  const last = cm.t12m_videos[cm.t12m_videos.length - 1];
  return panel(
    'yt-trend',
    5,
    'CATEGORY MOMENTUM',
    `TRAILING-12-MO ENERGY-DRINK UPLOADS · THRU ${cm.complete_through}`,
    area(series, { labelEvery: 12, fmt: fmtInt }),
    `Creator output ${(last / first).toFixed(1)}×'d (${fmtInt(first)} → ${fmtInt(last)} videos per rolling year) and is still climbing. The incomplete final month is excluded, so this is real growth — not a scrape artifact.`
  );
}

function priceVsRating() {
  const pts = data.price_vs_rating.slice(0, 14).map((d) => ({
    x: d.price,
    y: d.rating,
    r: d.ratings_total,
    label: d.brand,
    color: VOLT,
  }));
  return panel(
    'price-rating',
    4,
    'PRICE × QUALITY MAP',
    'AMAZON · BUBBLE = TOTAL RATINGS (MARKET TRACTION)',
    scatter(pts, {
      xLabel: 'AVG PRICE (USD)',
      yLabel: 'AVG RATING',
      xFmt: (v) => '$' + Math.round(v),
      xMin: 10,
      xMax: 55,
      yMin: 3.8,
      yMax: 5,
    }),
    'High-traction brands cluster at 4.5–4.7★ and $19–$31. Few combine premium price with top ratings — the upper-right quadrant is open for a serialized, premium ION position.'
  );
}

function reviewRatings() {
  const d = data.review_ratings;
  const rows = [1, 2, 3, 4, 5].map((s) => ({
    label: s + '★',
    value: d.dist[String(s)],
    color: s >= 4 ? VOLT : '#5a5a5a',
  }));
  return panel(
    'reviews',
    6,
    'REVIEW RATINGS',
    `${fmtInt(d.total)} REVIEWS · AVG ${d.avg}★ · ${d.verified_pct}% VERIFIED`,
    vBars(rows),
    `${Math.round((d.dist['5'] / d.rated) * 100)}% of reviews are 5★ — buyers love what exists. Winning means differentiation, not fixing dissatisfaction.`
  );
}

function voiceOfCustomer() {
  const max = data.voice_of_customer[0].mentions;
  const rows = data.voice_of_customer.map((d) => ({
    label: d.theme,
    value: d.mentions,
    color: d.theme === 'Crash & Jitters' ? ICE : undefined,
  }));
  const crash = data.voice_of_customer.find((d) => d.theme === 'Crash & Jitters');
  return panel(
    'voc',
    8,
    'VOICE OF THE CUSTOMER',
    `THEME FREQUENCY ACROSS ${fmtInt(data.kpis.youtube_comments)} COMMENTS + ${fmtInt(data.kpis.amazon_reviews)} REVIEWS`,
    hBars(rows, { fmt: fmtInt, unit: 'mentions', labelW: 180, accent: '#8fa600' }),
    `Taste and energy dominate the conversation. "Crash & Jitters" (${fmtInt(crash.mentions)}, in blue) is comparatively under-discussed — ION's no-crash protocol speaks to it. Note: this is mention <em>frequency</em>, not sentiment — a complaint and a compliment both count.`
  );
}

function instagramEngagement() {
  const rows = data.instagram_engagement.slice(0, 10).map((d, i) => ({
    label: d.brand,
    value: d.likes,
    color: i === 0 ? VOLT : undefined,
  }));
  const top = data.instagram_engagement[0];
  return panel(
    'ig',
    7,
    'SOCIAL ENGAGEMENT',
    'INSTAGRAM · TOTAL LIKES ON SAMPLED POSTS (15/BRAND)',
    hBars(rows, { unit: 'likes', accent: '#8fa600' }),
    `${top.brand} leads on Instagram (${fmtCompact(top.likes)} likes) — newer challenger brands punch far above legacy players on social, proving the category rewards brand-led launches.`
  );
}

/* ---------- sortable cross-platform table ---------- */
const COLS = [
  { key: 'brand', label: 'BRAND', align: 'left', fmt: (v) => v },
  { key: 'amazon_rating', label: 'AMZ ★', fmt: (v) => (v ? v.toFixed(2) : '—') },
  { key: 'amazon_price', label: 'AVG $', fmt: (v) => (v ? '$' + v.toFixed(2) : '—') },
  { key: 'amazon_reviews', label: 'REVIEWS', fmt: fmtInt },
  { key: 'ig_likes', label: 'IG LIKES', fmt: fmtCompact },
  { key: 'yt_videos', label: 'YT VIDS', fmt: fmtInt },
  { key: 'yt_views', label: 'YT VIEWS', fmt: fmtCompact },
];

function renderTable(sortKey = 'yt_views', dir = -1) {
  const rows = [...data.brands].sort((a, b) => {
    const av = a[sortKey] ?? -1;
    const bv = b[sortKey] ?? -1;
    if (typeof av === 'string') return dir * av.localeCompare(bv);
    return dir * (av - bv);
  });
  const maxViews = Math.max(...data.brands.map((b) => b.yt_views));

  const head = COLS.map(
    (c) =>
      `<th class="${c.align === 'left' ? 'tl' : ''} ${c.key === sortKey ? 'sorted' : ''}" data-key="${c.key}">
        ${c.label}<i class="sort-caret">${c.key === sortKey ? (dir < 0 ? '▼' : '▲') : ''}</i>
      </th>`
  ).join('');

  const body = rows
    .map((r) => {
      const tds = COLS.map((c) => {
        if (c.key === 'brand') {
          const w = (r.yt_views / maxViews) * 100;
          return `<td class="tl brand-cell"><span class="brand-spark" style="--w:${w.toFixed(1)}%"></span>${r.brand}</td>`;
        }
        return `<td class="${c.key === sortKey ? 'sorted' : ''}">${c.fmt(r[c.key])}</td>`;
      }).join('');
      return `<tr>${tds}</tr>`;
    })
    .join('');

  $('#brand-table').innerHTML = `<table class="intel-table mono">
    <thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;

  $$('#brand-table th').forEach((th) =>
    th.addEventListener('click', () => {
      const key = th.dataset.key;
      const nd = key === sortKey ? -dir : key === 'brand' ? 1 : -1;
      renderTable(key, nd);
    })
  );
}

/* ---------- reveal + count-up ---------- */
function animate() {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        e.target.classList.add('in');
        $$('[data-count]', e.target).forEach(countUp);
        io.unobserve(e.target);
      });
    },
    { threshold: 0.15 }
  );
  $$('.reveal').forEach((el) => io.observe(el));
}

function countUp(el) {
  if (el.dataset.done) return;
  el.dataset.done = '1';
  const target = parseFloat(el.dataset.count);
  const t0 = performance.now();
  const dur = 1400;
  const step = (now) => {
    const t = Math.min(1, (now - t0) / dur);
    const eased = 1 - Math.pow(1 - t, 4);
    el.textContent = fmtCompact(target * eased);
    if (t < 1) requestAnimationFrame(step);
    else el.textContent = fmtCompact(target);
  };
  requestAnimationFrame(step);
}

/* ---------- boot ---------- */
function main() {
  renderKpis();
  $('#charts').innerHTML = [
    shareOfVoice(),
    mentionMomentum(),
    risingBrands(),
    priceVsRating(),
    categoryMomentum(),
    reviewRatings(),
    instagramEngagement(),
    voiceOfCustomer(),
  ].join('');
  renderTable();
  $('#gen-at').textContent = new Date(data.generated_at).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
  animate();
  /* KPIs sit above the fold and aren't inside a .reveal panel — count them up on load */
  $$('#kpis [data-count]').forEach(countUp);
}

main();
