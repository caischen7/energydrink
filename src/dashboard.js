/*
 * Bogus Banana // Market Intel — dashboard logic.
 * Fetches the precomputed aggregate (public/data/dashboard.json, nginx-guarded), renders every
 * panel with the SVG chart builders, wires the sortable cross-platform table,
 * counts up the KPI readouts, and reveals charts on scroll.
 */
import '@fontsource-variable/inter';
import './dashboard.css';
import { hBars, vBars, scatter, area, multiLine, stackedBars, fmtCompact, fmtInt, VOLT, ICE } from './charts.js';
import { posMomentum } from './dashboard/pos-momentum.js';
import { launchPipeline } from './dashboard/launch-pipeline.js';
import { requireAuth } from './auth.js';

/* populated by requireAuth() once the visitor authenticates (data is fetched
   from the nginx-guarded /data/dashboard.json, not bundled into this file) */
let data;

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
function marketSize() {
  const m = data.market;
  const f = m.facts;
  const series = m.size.map((d) => ({ label: String(d.year), value: d.revenue }));
  return panel(
    'market',
    1,
    'MARKET SIZE — THE PRIZE',
    `GLOBAL ENERGY-DRINK REVENUE ($B) · ACTUALS 2018–2024 + FORECAST TO ${f.forecast_year} · STATISTA`,
    area(series, { labelEvery: 2, fmt: (v) => '$' + Math.round(v) + 'B' }),
    `A <b class="volt">$${f.total_2024_busd}B</b> global market in 2024 (incl. $${f.ooh_2024_busd}B out-of-home), forecast to $${f.forecast_busd}B by ${f.forecast_year}. Historical CAGR <b class="volt">${f.cagr_hist_pct}%</b> (2018–24) — a large, steadily compounding prize, not a fad.`
  );
}

const CONCEPT_SHORT = (c) =>
  c
    .split(' (')[0]
    .replace(/^Offers additional /, '')
    .replace(/^Made with /, '')
    .replace(/^Available in /, '')
    .replace(/^Products with /, '')
    .replace(/^Infused with /, '')
    .replace(/^Customizable energy.*/, 'Customizable caffeine')
    .replace(/^Limited-edition /, 'LTO ')
    .replace(/^(\w)/, (m) => m.toUpperCase());

/* Mintel: which energy-drink concepts consumers want to try (the "what to launch" signal) */
function conceptInterest() {
  const ci = data.concept_interest;
  const rows = ci.map((d, i) => ({ label: CONCEPT_SHORT(d.concept), value: d.pct, color: i === 0 ? VOLT : undefined }));
  const t = ci.slice(0, 3).map((d) => `${CONCEPT_SHORT(d.concept).toLowerCase()} (${d.pct}%)`);
  return panel(
    'concept',
    2,
    'CONCEPT INTEREST — WHAT TO LAUNCH',
    'MINTEL 2026 · % OF US ENERGY-DRINK CONSUMERS INTERESTED IN TRYING (n=766)',
    hBars(rows, { fmt: (v) => v + '%', labelW: 210, accent: '#c7c7cc' }),
    `Consumers most want ${t[0]}, ${t[1]} and ${t[2]} — all squarely in Bogus Banana's lane (functional electrolytes, clean, natural). "Branded flavors" and "adaptogens" (~34%) are the rising white-space bets.`
  );
}

const MOTIV_SHORT = (f) =>
  f
    .replace(/^To /, '')
    .replace(/^Because I /, '')
    .replace(/^As an? /, '')
    .replace(/^For the sense of /, '')
    .replace(/^For /, '')
    .replace(/^Out of /, '')
    .replace(/"/g, '')
    .replace(/^(\w)/, (m) => m.toUpperCase());

/* Mintel: why people drink energy drinks (top-2-box motivation) — the messaging angle */
function motivations() {
  const mv = data.motivations;
  const rows = mv.map((d, i) => ({ label: MOTIV_SHORT(d.factor), value: d.pct, color: i === 0 ? VOLT : undefined }));
  return panel(
    'motivations',
    3,
    'WHY THEY DRINK',
    'MINTEL 2026 · % FINDING EACH FACTOR MOTIVATING (TOP-2-BOX, n=766)',
    hBars(rows, { fmt: (v) => v + '%', labelW: 200, accent: '#c7c7cc' }),
    `Energy (${mv[0].pct}%), taste (${mv[1].pct}%) and focus (${mv[2].pct}%) lead — function and flavor matter almost equally. Bogus Banana's pitch (sustained no-crash energy <em>plus</em> a designed flavor system) hits the top two motivations at once, rather than trading one for the other.`
  );
}

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
    4,
    'SHARE OF VOICE',
    'YOUTUBE REACH · FRACTIONAL ATTRIBUTION · MUSIC/NOISE REMOVED',
    hBars(rows, { unit: 'views', accent: '#c7c7cc' }),
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
    5,
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
    6,
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
    8,
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
    7,
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
    'High-traction brands cluster at 4.5–4.7★ and $19–$31. Few combine premium price with top ratings — the upper-right quadrant is open for a premium Bogus Banana position.'
  );
}

/* flavor/descriptor demand ranked by mentions across the corpus */
function flavorBoard() {
  const fd = data.flavor_demand;
  const rows = fd.map((d, i) => ({ label: d.flavor, value: d.mentions, color: i === 0 ? VOLT : undefined }));
  const top = fd[0];
  const two = fd[1];
  const gem = fd.find((f) => f.flavor === 'Sour / Candy');
  const mint = fd.find((f) => f.flavor === 'Mint / Menthol');
  return panel(
    'flavor',
    9,
    'FLAVOR DEMAND BOARD',
    'MENTIONS ACROSS 125K COMMENTS + REVIEWS · BARS = DEMAND',
    hBars(rows, { fmt: fmtInt, unit: 'mentions', labelW: 150, accent: '#c7c7cc' }),
    `${top.flavor} (${fmtInt(top.mentions)} mentions, ${top.avg_rating}★) and ${two.flavor} (${fmtInt(two.mentions)}, ${two.avg_rating}★) lead demand — validating Bogus Banana's Original Blast & Midnight Berry.${gem ? ` "${gem.flavor}" is the sleeper: best-rated at ${gem.avg_rating}★ on only ${gem.products} SKUs — high satisfaction, low supply.` : ''}${mint ? ` Mint/menthol is weakest (${mint.avg_rating}★) — a flag if "Frozen Banana" leans cooling.` : ''}`
  );
}

function reviewRatings() {
  const d = data.review_ratings;
  const rows = [1, 2, 3, 4, 5].map((s) => ({
    label: s + '★',
    value: d.dist[String(s)],
    color: s >= 4 ? VOLT : '#c7c7cc',
  }));
  return panel(
    'reviews',
    10,
    'REVIEW RATINGS',
    `${fmtInt(d.total)} REVIEWS · AVG ${d.avg}★ · ${d.verified_pct}% VERIFIED`,
    vBars(rows),
    `${Math.round((d.dist['5'] / d.rated) * 100)}% of reviews are 5★ — buyers love what exists. Winning means differentiation, not fixing dissatisfaction.`
  );
}

function voiceOfCustomer() {
  const rows = data.voice_of_customer.map((d) => ({
    label: d.theme,
    pos: d.pos,
    neu: d.neu,
    neg: d.neg,
    total: d.mentions,
  }));
  const crash = data.voice_of_customer.find((d) => d.theme === 'Crash & Jitters');
  const crashNeg = Math.round((100 * crash.neg) / crash.mentions);
  return panel(
    'voc',
    13,
    'LOVES vs COMPLAINTS',
    `SENTIMENT (${data.sentiment_method}) BY THEME · ${fmtInt(data.kpis.youtube_comments)} COMMENTS + ${fmtInt(data.kpis.amazon_reviews)} REVIEWS`,
    stackedBars(rows, { fmt: fmtInt, labelW: 150, legend: true }),
    `Most themes run 75–82% positive — buyers love what exists, so winning means differentiation, not damage control. The exception: "Crash & Jitters" is <b class="volt">${crashNeg}% negative</b> — ~2× the category complaint rate, the clearest unmet need, and exactly what Bogus Banana's no-crash promise targets.`
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
    11,
    'SOCIAL ENGAGEMENT',
    'INSTAGRAM · TOTAL LIKES ON SAMPLED POSTS (15/BRAND)',
    hBars(rows, { unit: 'likes', accent: '#c7c7cc' }),
    `${top.brand} leads on Instagram (${fmtCompact(top.likes)} likes) — newer challenger brands punch far above legacy players on social, proving the category rewards brand-led launches.`
  );
}

/* Reddit r/EnergyDrinks: brand chatter + sentiment (recent-window snapshot, not a trend) */
function redditPulse() {
  const rb = data.reddit.brands.slice(0, 10);
  const m = data.reddit.meta;
  const rows = rb.map((d) => ({ label: d.brand, pos: d.pos, neu: d.neu, neg: d.neg, total: d.mentions }));
  const top = rb[0];
  // brand with the highest complaint ratio among the well-discussed ones
  const grumpy = rb
    .filter((d) => d.mentions >= 20)
    .map((d) => ({ brand: d.brand, negPct: Math.round((100 * d.neg) / d.mentions) }))
    .sort((a, b) => b.negPct - a.negPct)[0];
  return panel(
    'reddit',
    12,
    'REDDIT COMMUNITY PULSE',
    `r/ENERGYDRINKS · MENTIONS + SENTIMENT · ${m.date_start}→${m.date_end} SNAPSHOT`,
    stackedBars(rows, { fmt: fmtInt, labelW: 120, legend: true }),
    `${top.brand} drives the most chatter (${top.mentions} mentions). ${grumpy ? `${grumpy.brand} draws the most heat — ${grumpy.negPct}% negative, a quality opening for a challenger.` : ''} Note: a ~3-week sample, so read it as a current snapshot, not a trend.`
  );
}

/* Open Food Facts: sugar vs caffeine per brand — the nutrition white-space map */
function nutritionMap() {
  const n = data.nutrition;
  const pts = n.brands
    .filter((d) => d.sugar != null && d.caffeine != null)
    .slice(0, 16)
    .map((d) => ({
      x: d.sugar,
      y: d.caffeine,
      r: d.products,
      label: d.brand,
      color: d.sugar === 0 ? ICE : VOLT,
      tip: `${d.brand} — ${d.sugar}g sugar / 100ml · ${d.caffeine}mg caffeine / 100ml · ${d.products} SKU`,
    }));
  const sf = Math.round((100 * n.sugarfree) / (n.sugarfree + n.sugared || 1));
  return panel(
    'nutrition',
    14,
    'NUTRITION MAP — SUGAR × CAFFEINE',
    `OPEN FOOD FACTS · ${n.products} SKUS · PER 100ML · ${sf}% ZERO-SUGAR · SAMPLE DATA`,
    scatter(pts, {
      xLabel: 'SUGAR (g / 100ml)',
      yLabel: 'CAFFEINE (mg / 100ml)',
      xFmt: (v) => v.toFixed(0) + 'g',
      xMin: 0,
      xMax: 14,
      yMin: 0,
      yMax: 36,
      tip: (p) => p.tip,
    }),
    `Nutrition is the axis Amazon price/rating can't see. <b class="volt">${sf}%</b> of tracked SKUs are already zero-sugar, so "no sugar" alone is table stakes — the open quadrant is <em>zero-sugar with clean, moderate caffeine</em> (bottom-left), exactly where Bogus Banana's 120mg / no-crash spec sits. (Ships with generated sample data — run <code>data/scrapers/openfoodfacts.py</code> for live values.)`
  );
}

/* Wikipedia pageviews: platform-neutral curiosity per brand over the last 12 months */
function wikiInterest() {
  const rows = data.wiki_interest.slice(0, 12).map((d, i) => ({
    label: d.brand,
    value: d.total,
    color: i === 0 ? VOLT : undefined,
  }));
  const top = data.wiki_interest[0];
  const two = data.wiki_interest[1];
  return panel(
    'wiki',
    15,
    'SEARCH INTEREST — PUBLIC CURIOSITY',
    'WIKIPEDIA PAGEVIEWS · TRAILING 12 MONTHS · SAMPLE DATA',
    hBars(rows, { fmt: fmtCompact, unit: 'views', accent: '#c7c7cc' }),
    `A key-free, platform-neutral demand proxy: ${top.brand} (${fmtCompact(top.total)}) and ${two.brand} (${fmtCompact(two.total)}) top raw curiosity, tracking their retail dominance. Useful as an independent cross-check on the social-reach ranking above. (Generated sample — run <code>data/scrapers/wikipedia.py</code> for live pageviews.)`
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
function main(loaded) {
  data = loaded;
  renderKpis();
  const panels = [
    marketSize(),
    conceptInterest(),
    motivations(),
    shareOfVoice(),
    mentionMomentum(),
    risingBrands(),
    priceVsRating(),
    categoryMomentum(),
    flavorBoard(),
    reviewRatings(),
    instagramEngagement(),
    redditPulse(),
    voiceOfCustomer(),
  ];
  /* new sources — only render if the aggregate carries their data */
  if (data.nutrition?.brands?.length) panels.push(nutritionMap());
  if (data.wiki_interest?.length) panels.push(wikiInterest());
  /* BigQuery-derived: measured sell-through + the launch pipeline */
  if (data.pos_momentum?.length) panels.push(posMomentum(data));
  if (data.launch_claims?.length) panels.push(launchPipeline(data));
  $('#charts').innerHTML = panels.join('');
  renderTable();
  $('#gen-at').textContent = new Date(data.generated_at).toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
  animate();
  /* KPIs sit above the fold and aren't inside a .reveal panel — count them up on load */
  $$('#kpis [data-count]').forEach(countUp);
}

/* gate the dashboard behind the login overlay (client-side deterrent — see auth.js) */
requireAuth().then(main);
