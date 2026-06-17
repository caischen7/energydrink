// Tiny dependency-free SVG chart helpers. Each returns an SVG string; data
// points carry a `data-tip` attribute that wireTooltips() turns into hover
// tooltips. Styling comes from dashboard.css (.chart, .dot, .tooltip).

const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const nice = (n) => {
  if (n >= 1e9) return (n / 1e9).toFixed(1).replace(/\.0$/, '') + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, '') + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, '') + 'K';
  return String(Math.round(n));
};

// ---------------------------------------------------------------------------
// Demand-vs-supply quadrant: x = catalog supply %, y = consumer demand.
// Top-left = high demand / low supply = white space.
// ---------------------------------------------------------------------------
export function quadrantChart(items, { w = 640, h = 440 } = {}) {
  const m = { t: 24, r: 24, b: 46, l: 56 };
  const iw = w - m.l - m.r;
  const ih = h - m.t - m.b;
  const maxDemand = Math.max(...items.map((d) => d.demand)) * 1.08;
  const x = (v) => m.l + (v / 100) * iw;            // supply_pct 0..100
  const y = (v) => m.t + ih - (v / maxDemand) * ih; // demand
  const maxGap = Math.max(...items.map((d) => d.gap_score), 1);
  const r = (g) => 5 + (g / maxGap) * 16;

  let s = `<svg viewBox="0 0 ${w} ${h}" class="chart" role="img" aria-label="Demand versus supply quadrant">`;

  // white-space shading (left third)
  s += `<rect x="${m.l}" y="${m.t}" width="${iw / 3}" height="${ih}" fill="#c6ff00" opacity="0.04"/>`;
  s += `<text class="quad-label" x="${m.l + 8}" y="${m.t + 16}">◤ WHITE SPACE — high demand, low supply</text>`;
  s += `<text class="quad-label" x="${w - m.r - 8}" y="${h - m.b - 8}" text-anchor="end">crowded ▸</text>`;

  // gridlines + y ticks
  for (let i = 0; i <= 4; i++) {
    const gy = m.t + (ih / 4) * i;
    const val = maxDemand - (maxDemand / 4) * i;
    s += `<line class="gridline" x1="${m.l}" y1="${gy}" x2="${w - m.r}" y2="${gy}"/>`;
    s += `<text x="${m.l - 8}" y="${gy + 3}" text-anchor="end">${nice(val)}</text>`;
  }
  // x ticks
  for (let i = 0; i <= 5; i++) {
    const gx = m.l + (iw / 5) * i;
    s += `<text x="${gx}" y="${h - m.b + 18}" text-anchor="middle">${i * 20}%</text>`;
  }
  s += `<text x="${m.l + iw / 2}" y="${h - 6}" text-anchor="middle">CATALOG SUPPLY (% of products positioning on it)</text>`;
  s += `<text transform="translate(14 ${m.t + ih / 2}) rotate(-90)" text-anchor="middle">CONSUMER DEMAND (mentions)</text>`;

  for (const d of items) {
    const cx = x(d.supply_pct);
    const cy = y(d.demand);
    const tip = `${d.name} — demand ${nice(d.demand)} · supply ${d.supply_pct}% · gap ${d.gap_score}`;
    s += `<circle class="dot" cx="${cx}" cy="${cy}" r="${r(d.gap_score)}" fill="#c6ff00" fill-opacity="0.22" stroke="#c6ff00" stroke-opacity="0.9" data-tip="${esc(tip)}"/>`;
    if (d.gap_score >= maxGap * 0.45)
      s += `<text x="${cx}" y="${cy - r(d.gap_score) - 4}" text-anchor="middle" fill="#eaeaea">${esc(d.name.split(' / ')[0])}</text>`;
  }
  s += `</svg>`;
  return s;
}

// ---------------------------------------------------------------------------
// Price vs rating scatter. x = price, y = rating, dot size = # ratings.
// ---------------------------------------------------------------------------
export function priceScatter(points, { w = 640, h = 420 } = {}) {
  const m = { t: 22, r: 22, b: 46, l: 46 };
  const iw = w - m.l - m.r;
  const ih = h - m.t - m.b;
  const maxP = Math.max(...points.map((p) => p.price)) * 1.05;
  const minR = Math.min(...points.map((p) => p.rating)) - 0.15;
  const maxR = 5.02;
  const maxRev = Math.max(...points.map((p) => p.reviews), 1);
  const x = (v) => m.l + (v / maxP) * iw;
  const y = (v) => m.t + ih - ((v - minR) / (maxR - minR)) * ih;
  const r = (v) => 3 + Math.sqrt(v / maxRev) * 11;

  let s = `<svg viewBox="0 0 ${w} ${h}" class="chart" role="img" aria-label="Price versus rating scatter">`;
  // premium / thin zone shading (high price)
  s += `<rect x="${x(35)}" y="${m.t}" width="${w - m.r - x(35)}" height="${ih}" fill="#9fd8ff" opacity="0.04"/>`;
  s += `<text class="quad-label" x="${x(35) + 6}" y="${m.t + 14}">premium zone ▸</text>`;

  for (let i = 0; i <= 4; i++) {
    const gy = m.t + (ih / 4) * i;
    const val = maxR - ((maxR - minR) / 4) * i;
    s += `<line class="gridline" x1="${m.l}" y1="${gy}" x2="${w - m.r}" y2="${gy}"/>`;
    s += `<text x="${m.l - 8}" y="${gy + 3}" text-anchor="end">${val.toFixed(1)}★</text>`;
  }
  for (let i = 0; i <= 5; i++) {
    const gx = m.l + (iw / 5) * i;
    s += `<text x="${gx}" y="${h - m.b + 18}" text-anchor="middle">$${Math.round((maxP / 5) * i)}</text>`;
  }
  s += `<text x="${m.l + iw / 2}" y="${h - 6}" text-anchor="middle">PRICE (USD, listed pack price)</text>`;

  for (const p of points) {
    const tip = `${p.brand} — $${p.price} · ${p.rating}★ · ${nice(p.reviews)} ratings\n${p.title}`;
    s += `<circle class="dot" cx="${x(p.price)}" cy="${y(p.rating)}" r="${r(p.reviews)}" fill="#c6ff00" fill-opacity="0.18" stroke="#c6ff00" stroke-opacity="0.7" data-tip="${esc(tip)}"/>`;
  }
  s += `</svg>`;
  return s;
}

// ---------------------------------------------------------------------------
// Horizontal bars (generic). rows: [{label, value, sub?}]
// ---------------------------------------------------------------------------
export function barList(rows, { max, fmt = nice, accent = '#c6ff00' } = {}) {
  const mx = max || Math.max(...rows.map((r) => r.value), 1);
  return rows
    .map((r) => {
      const pct = (r.value / mx) * 100;
      return `<div class="dsbar"><span class="k" title="${esc(r.label)}">${esc(r.label)}</span>
        <span class="track"><i class="d" style="width:${pct.toFixed(1)}%;background:${accent}"></i></span>
        <span class="v">${fmt(r.value)}${r.sub ? `<br><span class="dim" style="font-size:9px">${esc(r.sub)}</span>` : ''}</span></div>`;
    })
    .join('');
}

// demand (volt) vs supply (ice) paired bar for one item
export function demandSupplyRow(name, demand, demandMax, supplyPct) {
  return `<div style="display:flex;flex-direction:column;gap:4px">
    <div class="dsbar"><span class="k">DEMAND</span>
      <span class="track"><i class="d" style="width:${((demand / demandMax) * 100).toFixed(1)}%"></i></span>
      <span class="v">${nice(demand)}</span></div>
    <div class="dsbar"><span class="k">SUPPLY</span>
      <span class="track"><i class="s" style="width:${Math.min(supplyPct, 100).toFixed(1)}%"></i></span>
      <span class="v">${supplyPct}%</span></div>
  </div>`;
}

// ---------------------------------------------------------------------------
// Tooltip wiring — call once after charts are in the DOM.
// ---------------------------------------------------------------------------
export function wireTooltips() {
  let tip = document.querySelector('.tooltip');
  if (!tip) {
    tip = document.createElement('div');
    tip.className = 'tooltip';
    document.body.appendChild(tip);
  }
  document.addEventListener('mouseover', (e) => {
    const el = e.target.closest('[data-tip]');
    if (!el) return;
    tip.innerHTML = el.getAttribute('data-tip').split('\n').map((l, i) => (i === 0 ? `<b>${esc(l)}</b>` : esc(l))).join('<br>');
    tip.style.opacity = '1';
  });
  document.addEventListener('mousemove', (e) => {
    if (tip.style.opacity === '1') {
      tip.style.left = e.clientX + 'px';
      tip.style.top = e.clientY - 12 + 'px';
    }
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest('[data-tip]')) tip.style.opacity = '0';
  });
}

export { nice };
