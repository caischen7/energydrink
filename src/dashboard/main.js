import './dashboard.css';
import '@fontsource-variable/archivo';
import '@fontsource-variable/space-grotesk';
import '@fontsource/space-mono';
import {
  quadrantChart, priceScatter, barList, demandSupplyRow, wireTooltips, nice,
} from './charts.js';

// 12-seat board (condensed; full bios in docs/advisory-board.md)
const BOARD = [
  ['Maya Okafor', 'Voltcore', 'Better-for-you energy'],
  ['Dev Ramaswamy', 'Cultret', 'Gut-health functional soda'],
  ['Sofia Marchetti', 'Lumen Labs', 'Nootropic focus drinks'],
  ['Tariq Bennett', 'Replenish', 'Electrolyte hydration'],
  ['Grace Liu', 'Frostbyte', 'Esports / gaming energy'],
  ['Marcus Webb', 'HALO', 'Protein + energy RTD'],
  ['Priya Anand', 'Wildwater', 'Brand-first natural energy'],
  ['Jordan Reyes', 'Kindle', "Women's wellness energy"],
  ['Helena Vance', 'Rooted', 'Adaptogen calm-energy'],
  ['Sam Calloway', 'Reefer Bev', 'Distribution / retail'],
  ['Nina Patel', 'Northstar CPG', 'Operator-investor'],
  ['Andre Kowalski', 'Quantbev', 'Category data science'],
];

const ROADMAP = [
  ['P0', 'Retail sales & velocity (SPINS / NielsenIQ / Amazon BSR over time)', 'Converts demand signal into "does it actually sell." Biggest gap.'],
  ['P0', 'Nutrition / ingredient panels per SKU (caffeine, sugar, protein, actives)', 'Reason about real formulation gaps & feasibility, not just words.'],
  ['P1', 'TikTok posts, sounds & hashtag velocity', 'Where the category breaks out now; YouTube/IG miss it.'],
  ['P1', 'Time-series mentions & ratings by week', 'Separate nascent trends from dying ones; show momentum.'],
  ['P1', 'Audience/segment tags (gamer, gym, wellness, student, parent)', 'Make every white space filterable by who wants it.'],
  ['P2', 'Reddit + long-form 1–3★ reviews', 'Highest-signal complaints and "I wish it had…" requests.'],
  ['P2', 'Google / Amazon search-volume trends', 'Leading indicator of demand before social catches up.'],
  ['P3', 'Distribution footprint by retailer', 'White space by channel, not just by attribute.'],
];

const $ = (sel, el = document) => el.querySelector(sel);
const el = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };

async function boot() {
  let d;
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}market_intel.json`);
    d = await res.json();
  } catch (e) {
    $('#app').innerHTML = `<div class="wrap"><p class="warn" style="padding:4rem 0">Could not load market_intel.json — run <code>python data/scripts/build_dashboard_data.py</code> first.</p></div>`;
    return;
  }
  render(d);
  wireTooltips();
}

function render(d) {
  const m = d.meta;
  const kpis = [
    [nice(m.n_brands), 'brands tracked'],
    [nice(m.n_products), 'Amazon products'],
    [nice(m.n_reviews), 'product reviews'],
    [nice(m.n_ig_posts), 'Instagram posts'],
    [nice(m.n_videos), 'YouTube videos'],
    [nice(m.n_comments), 'video comments'],
  ];

  const demandMax = Math.max(...d.attributes.map((a) => a.demand));

  $('#app').innerHTML = `
  <div class="topbar">
    <div class="brand"><span class="dot"></span><b>ION_INTEL</b><span class="mono dim">MARKET&nbsp;TERMINAL</span></div>
    <div class="mono live"><span>BUILD ${m.generated}</span></div>
    <nav class="mono"><a href="#opportunity">WHITE_SPACE</a><a href="#builder">BUILDER</a><a href="#pricing">PRICING</a><a href="#pain">PAIN→POS</a><a href="#brands">BRANDS</a><a href="#board">BOARD</a><a href="${import.meta.env.BASE_URL}index.html">↩ SITE</a></nav>
  </div>

  <div class="wrap">
    <header class="hero">
      <div class="eyebrow mono">// FOUNDER OPPORTUNITY TERMINAL · ${m.sources.join(' + ')}</div>
      <h1>Find the <em>white space</em><br>before you build the can.</h1>
      <p>A demand-signal engine over <b class="volt">${nice(m.n_comments + m.n_reviews)}</b> consumer voices and <b class="volt">${m.n_products}</b> shelf products. It surfaces what people ask for that the category doesn't yet sell — then lets you assemble a concept and score its white space. Built for the founder board; every number drills to its evidence.</p>
      <div class="kpis">
        ${kpis.map(([n, l]) => `<div class="kpi"><div class="n">${n}</div><div class="l mono">${l}</div></div>`).join('')}
      </div>
    </header>

    <!-- WHITE SPACE -->
    <section class="block" id="opportunity">
      <div class="shead">
        <div><div class="tag mono">01 / WHITE-SPACE FINDER</div><h2>Demand the shelf isn't serving</h2></div>
        <p>Bubble = a functional benefit. Up = consumers want it. Left = few products offer it. Top-left bubbles are open territory. Size = white-space score.</p>
      </div>
      <div class="grid grid-2" style="align-items:stretch">
        <div class="panel" style="padding:1.2rem">${quadrantChart(d.attributes)}
          <div class="legend"><span><i style="background:#c6ff00;opacity:.5;border-radius:50%"></i> functional benefit · size = gap score</span><span><i style="background:#c6ff00;opacity:.1"></i> white-space band</span></div>
        </div>
        <div class="grid" style="grid-template-columns:1fr">${d.opportunities.map((o, i) => oppCard(o, i, demandMax)).join('')}</div>
      </div>
      <p class="note">SCORE = normalized consumer demand × (1 − catalog supply). Demand counted across reviews + YouTube comments; supply across product titles, descriptions & feature bullets.</p>
    </section>

    <!-- CONCEPT BUILDER -->
    <section class="block" id="builder">
      <div class="shead">
        <div><div class="tag mono">02 / CONCEPT BUILDER</div><h2>Assemble a new beverage</h2></div>
        <p>Pick a functional angle, a flavor, a pain point to beat and a price band. The terminal scores the combination's white space and writes the one-line brief.</p>
      </div>
      <div class="builder">
        <div class="builder-grid">
          <div class="builder-controls">
            ${field('b-attr', 'Functional white space', d.attributes.map((a) => [a.name, `${a.name} · gap ${a.gap_score} · ${a.supply_pct}% of shelf`]))}
            ${field('b-flavor', 'Flavor', d.flavors.map((f) => [f.name, `${f.name} · ${nice(f.demand)} mentions · ${f.supply_pct}% of shelf`]))}
            ${field('b-pain', 'Incumbent pain to beat', d.painpoints.map((p) => [p.name, `${p.name} · ${nice(p.mentions)} mentions`]))}
            ${field('b-price', 'Target price band', d.pricing.bands.map((b) => [b.label, `${b.label} · ${b.count} products here`]))}
          </div>
          <div class="builder-out" id="b-out"></div>
        </div>
      </div>
    </section>

    <!-- PRICING -->
    <section class="block" id="pricing">
      <div class="shead">
        <div><div class="tag mono">03 / PRICING ARBITRAGE</div><h2>Where quality and price diverge</h2></div>
        <p>Each dot is a product — price vs rating, sized by # ratings. Hunt the premium zone for thin, high-rated air, or crowded value bands full of complaints.</p>
      </div>
      <div class="grid grid-2" style="align-items:stretch">
        <div class="panel" style="padding:1.2rem">${priceScatter(d.pricing.scatter)}
          <div class="legend"><span><i style="background:#c6ff00;opacity:.4;border-radius:50%"></i> product · size = # ratings</span><span><i style="background:#9fd8ff;opacity:.2"></i> premium zone ($35+)</span></div>
        </div>
        <div class="panel" style="padding:1.4rem">
          <div class="mono dim" style="margin-bottom:1rem">PRODUCTS PER PRICE BAND</div>
          ${barList(d.pricing.bands.map((b) => ({ label: b.label, value: b.count })), { fmt: (n) => n })}
          <div class="callout" style="margin-top:1.5rem">Value bands <b>$15–35</b> hold ${d.pricing.bands.filter(b=>['$15–25','$25–35'].includes(b.label)).reduce((a,b)=>a+b.count,0)} of ${m.n_products} products. The <b>$35+ premium</b> is comparatively thin — room for a justified premium SKU if the formula earns it.</div>
        </div>
      </div>
    </section>

    <!-- PAIN -> POSITIONING -->
    <section class="block" id="pain">
      <div class="shead">
        <div><div class="tag mono">04 / PAIN → POSITIONING</div><h2>Complaints you can put on the can</h2></div>
        <p>What consumers dislike about today's energy drinks — ranked by how often they say it. Each is a positioning angle in the consumer's own words.</p>
      </div>
      <div class="grid grid-3">
        ${d.painpoints.slice(0, 9).map((p) => painCard(p, d.painpoints[0].mentions)).join('')}
      </div>
    </section>

    <!-- BRANDS -->
    <section class="block" id="brands">
      <div class="shead">
        <div><div class="tag mono">05 / SHARE OF VOICE</div><h2>Who owns the conversation</h2></div>
        <p>Blended social reach (YouTube views + Instagram likes) with Amazon presence and rating. Loud ≠ loved — watch for high reach with soft ratings.</p>
      </div>
      <div class="panel" style="padding:0.4rem 1.2rem 1.2rem;overflow-x:auto">
        ${brandTable(d.brands)}
      </div>
      <p class="note">Share of voice is attention, not sales — Amazon over-indexes subscribe-and-save brands, YouTube over-indexes review channels. Treat as a hypothesis, not a verdict (per the board's data-bias caveat).</p>
    </section>

    <!-- FLAVORS -->
    <section class="block" id="flavors">
      <div class="shead">
        <div><div class="tag mono">06 / FLAVOR PULL</div><h2>Most-wanted flavors</h2></div>
        <p>Flavor words by consumer mention volume. Cross-reference with the builder to pair an under-served flavor with an open functional angle.</p>
      </div>
      <div class="panel" style="padding:1.4rem">
        ${barList(d.flavors.slice(0, 14).map((f) => ({ label: f.name, value: f.demand, sub: `${f.supply_pct}% of shelf` })))}
      </div>
    </section>

    <!-- BOARD -->
    <section class="block" id="board">
      <div class="shead">
        <div><div class="tag mono">07 / FOUNDER ADVISORY BOARD</div><h2>12 operators steering the tool</h2></div>
        <p>The board that defined these views and voted the data roadmap below. Full session in <a class="volt" href="https://github.com/caischen7/energydrink/blob/HEAD/docs/board-discussion.md">board-discussion.md</a>.</p>
      </div>
      <div class="board-grid">
        ${BOARD.map(([n, c, l]) => `<div class="seat"><div class="nm">${n}</div><div class="co">${c}</div><div class="ln">${l}</div></div>`).join('')}
      </div>

      <div class="shead" style="margin-top:3rem">
        <div><div class="tag mono">08 / DATA ROADMAP</div><h2>What the board wants next</h2></div>
        <p>Sources the board prioritized to turn this hypothesis engine into a go/no-go tool. P0 = highest impact.</p>
      </div>
      <div class="roadmap panel" style="padding:0 1.4rem">
        ${ROADMAP.map(([pri, src, why]) => `<div class="road"><div class="pri ${pri.toLowerCase()}">${pri}</div><div class="src"><b>${src}</b><span>${why}</span></div></div>`).join('')}
      </div>
      <div class="callout"><b>Board consensus:</b> ship v1 as a white-space <b>hypothesis generator</b> on the data we have; acquire retail-velocity + nutrition-panel data (P0) next to earn a real go/no-go call.</div>
    </section>

    <footer>
      <span>ION_INTEL · MARKET TERMINAL · v1</span>
      <span>SOURCES: ${m.sources.join(' / ')} · BUILD ${m.generated} · HYPOTHESIS ENGINE — NOT SALES DATA</span>
    </footer>
  </div>`;

  initBuilder(d, demandMax);
}

// ---- component builders ---------------------------------------------------
function oppCard(o, i, demandMax) {
  return `<div class="opp">
    <span class="rank">#${String(i + 1).padStart(2, '0')}</span>
    <h3>${o.title}</h3>
    <div class="score"><b>${o.gap_score}</b><span class="mono dim">WHITE-SPACE SCORE</span></div>
    ${demandSupplyRow(o.title, o.demand, demandMax, o.supply_pct)}
    <div class="thesis">${o.thesis}</div>
    ${o.quotes && o.quotes.length ? `<div class="quotes">${o.quotes.map((q) => `<div class="quote">“${escapeHtml(q)}”</div>`).join('')}</div>` : ''}
  </div>`;
}

function painCard(p, max) {
  return `<div class="opp">
    <h3 style="font-size:1.05rem">${p.name}</h3>
    <div class="score"><b style="font-size:1.6rem">${nice(p.mentions)}</b><span class="mono dim">MENTIONS · ${p.share_pct}% of voices</span></div>
    <span class="track" style="margin:2px 0"><i class="d" style="width:${((p.mentions / max) * 100).toFixed(0)}%"></i></span>
    ${p.quotes && p.quotes.length ? `<div class="quote">“${escapeHtml(p.quotes[0])}”</div>` : ''}
  </div>`;
}

function brandTable(brands) {
  const maxSov = Math.max(...brands.map((b) => b.sov_pct));
  const rows = brands
    .filter((b) => b.sov_pct > 0 || b.amazon_products > 0)
    .slice(0, 18)
    .map((b) => `<tr>
      <td class="bn">${b.brand}</td>
      <td><span class="miniwrap"><span class="minibar" style="width:${Math.max(2, (b.sov_pct / maxSov) * 100).toFixed(0)}%"></span></span> ${b.sov_pct}%</td>
      <td>${b.yt_views ? nice(b.yt_views) : '—'}</td>
      <td>${b.ig_likes ? nice(b.ig_likes) : '—'}</td>
      <td>${b.amazon_products || '—'}</td>
      <td>${b.avg_rating ? b.avg_rating + '★' : '—'}</td>
      <td>${b.avg_price ? '$' + b.avg_price.toFixed(0) : '—'}</td>
    </tr>`)
    .join('');
  return `<table class="t"><thead><tr>
    <th>Brand</th><th>Share of voice</th><th>YT views</th><th>IG likes</th><th>Products</th><th>Avg ★</th><th>Avg $</th>
    </tr></thead><tbody>${rows}</tbody></table>`;
}

function field(id, label, options) {
  return `<div class="field">
    <label for="${id}">${label}</label>
    <select id="${id}">${options.map(([v, t]) => `<option value="${escapeHtml(v)}">${escapeHtml(t)}</option>`).join('')}</select>
  </div>`;
}

// ---- interactive concept builder -----------------------------------------
function initBuilder(d, demandMax) {
  const attrBy = Object.fromEntries(d.attributes.map((a) => [a.name, a]));
  const flavBy = Object.fromEntries(d.flavors.map((f) => [f.name, f]));
  const painBy = Object.fromEntries(d.painpoints.map((p) => [p.name, p]));
  const bandBy = Object.fromEntries(d.pricing.bands.map((b) => [b.label, b]));
  const totalProducts = d.meta.n_products;

  function update() {
    const a = attrBy[$('#b-attr').value];
    const f = flavBy[$('#b-flavor').value];
    const p = painBy[$('#b-pain').value];
    const b = bandBy[$('#b-price').value];

    // combined white-space score: attribute gap, flavor under-supply, pain size, band thinness
    const flavorGap = f.demand / demandMax * (1 - Math.min(f.supply_pct, 100) / 100);
    const painNorm = p.mentions / d.painpoints[0].mentions;
    const bandThin = 1 - b.count / totalProducts;
    const score = Math.round(
      0.45 * a.gap_score +
      0.25 * (flavorGap * 100) +
      0.20 * (painNorm * 100) +
      0.10 * (bandThin * 100)
    );

    const attrShort = a.name.split(' / ')[0].toLowerCase();
    const out = $('#b-out');
    out.innerHTML = `
      <div class="label mono">// GENERATED CONCEPT</div>
      <div class="concept">A <em>${escapeHtml(f.name)}</em> ${escapeHtml(attrShort)} energy drink,<br>priced <em>${b.label}</em>, built to beat <em>${escapeHtml(p.name.toLowerCase())}</em>.</div>
      <div class="scoreline"><b>${score}</b><span class="gauge"><i style="width:${Math.min(score, 100)}%"></i></span></div>
      <div class="label mono">// WHITE-SPACE SCORE (0–100) · weighted blend</div>
      <div class="evidence">
        <div><b>${nice(a.demand)}</b> mentions want <b>${escapeHtml(a.name)}</b> — only <b>${a.supply_pct}%</b> of the shelf offers it.</div>
        <div><b>${nice(f.demand)}</b> mentions name <b>${escapeHtml(f.name)}</b> — on <b>${f.supply_pct}%</b> of products.</div>
        <div><b>${nice(p.mentions)}</b> voices complain of <b>${escapeHtml(p.name.toLowerCase())}</b> — your wedge.</div>
        <div>Only <b>${b.count}</b> of ${totalProducts} products sit in <b>${b.label}</b>.</div>
      </div>
      ${p.quotes && p.quotes.length ? `<div class="quote">“${escapeHtml(p.quotes[0])}”</div>` : ''}`;
  }

  ['#b-attr', '#b-flavor', '#b-pain', '#b-price'].forEach((s) => $(s).addEventListener('change', update));
  // sensible defaults: the #1 white space + an under-served flavor
  $('#b-flavor').value = (d.flavors.find((f) => f.supply_pct < 20) || d.flavors[0]).name;
  update();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

boot();
