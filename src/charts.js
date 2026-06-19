/*
 * Dependency-free SVG chart builders for the Bogus Banana market-intel dashboard.
 * Each function returns an <svg> string injected via innerHTML. Charts use a
 * fixed viewBox and scale to their container; entrance animation is CSS-driven
 * (see dashboard.css) and gated by an IntersectionObserver in dashboard.js.
 */

const VOLT = '#0071e3';
const ICE = '#5e9ed6';
const DIM = '#86868b';
const LINE = '#d2d2d7';

/* ---------- number formatting ---------- */
export function fmtCompact(n) {
  if (n == null || isNaN(n)) return '—';
  const a = Math.abs(n);
  if (a >= 1e9) return (n / 1e9).toFixed(a >= 1e10 ? 0 : 1) + 'B';
  if (a >= 1e6) return (n / 1e6).toFixed(a >= 1e7 ? 0 : 1) + 'M';
  if (a >= 1e3) return (n / 1e3).toFixed(a >= 1e4 ? 0 : 1) + 'K';
  return String(Math.round(n));
}
export function fmtInt(n) {
  return n == null || isNaN(n) ? '—' : Math.round(n).toLocaleString('en-US');
}
const esc = (s) =>
  String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/*
 * Horizontal bars with a label column. rows: [{label, value, color?}]
 * opts: { fmt, unit, accent }
 */
export function hBars(rows, opts = {}) {
  const fmt = opts.fmt || fmtCompact;
  const W = 800;
  const rowH = 30;
  const gap = 8;
  const labelW = opts.labelW || 150;
  const valW = 86;
  const barX = labelW + 8;
  const barMax = W - barX - valW;
  const H = rows.length * (rowH + gap);
  const max = Math.max(...rows.map((r) => r.value), 1);

  const bars = rows
    .map((r, i) => {
      const y = i * (rowH + gap);
      const w = Math.max(2, (r.value / max) * barMax);
      const color = r.color || opts.accent || VOLT;
      return `
      <g class="hbar-row" transform="translate(0 ${y})">
        <text x="${labelW}" y="${rowH / 2}" class="c-lbl" text-anchor="end" dominant-baseline="middle">${esc(r.label)}</text>
        <rect x="${barX}" y="2" width="${barMax}" height="${rowH - 4}" class="c-track"/>
        <rect x="${barX}" y="2" width="${w}" height="${rowH - 4}" fill="${color}" class="c-bar c-bar-h">
          <title>${esc(r.label)}: ${fmt(r.value)}${opts.unit ? ' ' + opts.unit : ''}</title>
        </rect>
        <text x="${W}" y="${rowH / 2}" class="c-val" text-anchor="end" dominant-baseline="middle">${fmt(r.value)}</text>
      </g>`;
    })
    .join('');

  return `<svg viewBox="0 0 ${W} ${H}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">${bars}</svg>`;
}

/* Vertical bars, e.g. 1–5 rating distribution. rows: [{label, value}] */
export function vBars(rows, opts = {}) {
  const fmt = opts.fmt || fmtInt;
  const W = 800;
  const H = 300;
  const padB = 46;
  const padT = 30;
  const innerH = H - padB - padT;
  const slot = W / rows.length;
  const bw = Math.min(110, slot * 0.6);
  const max = Math.max(...rows.map((r) => r.value), 1);

  const bars = rows
    .map((r, i) => {
      const x = i * slot + (slot - bw) / 2;
      const h = Math.max(2, (r.value / max) * innerH);
      const y = padT + innerH - h;
      const color = r.color || opts.accent || VOLT;
      return `
      <g>
        <rect x="${x}" y="${y}" width="${bw}" height="${h}" fill="${color}" class="c-bar c-bar-v" style="transform-origin:center ${padT + innerH}px">
          <title>${esc(r.label)}: ${fmt(r.value)}</title>
        </rect>
        <text x="${x + bw / 2}" y="${y - 8}" class="c-val" text-anchor="middle">${fmt(r.value)}</text>
        <text x="${x + bw / 2}" y="${H - padB + 24}" class="c-lbl" text-anchor="middle">${esc(r.label)}</text>
      </g>`;
    })
    .join('');

  return `<svg viewBox="0 0 ${W} ${H}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">${bars}</svg>`;
}

/*
 * Scatter. points: [{x, y, r, label}]  domains: {xMin,xMax,yMin,yMax}
 * Renders gridlines + axis ticks. Used for price (x) vs rating (y).
 */
export function scatter(points, opts = {}) {
  const W = 800;
  const H = 460;
  const padL = 64;
  const padR = 24;
  const padB = 54;
  const padT = 24;
  const iw = W - padL - padR;
  const ih = H - padB - padT;

  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const xMin = opts.xMin ?? Math.min(...xs) * 0.9;
  const xMax = opts.xMax ?? Math.max(...xs) * 1.05;
  const yMin = opts.yMin ?? Math.min(...ys) - 0.1;
  const yMax = opts.yMax ?? Math.max(...ys) + 0.1;
  const rMax = Math.max(...points.map((p) => p.r || 1), 1);

  const sx = (v) => padL + ((v - xMin) / (xMax - xMin)) * iw;
  const sy = (v) => padT + ih - ((v - yMin) / (yMax - yMin)) * ih;
  const sr = (v) => 6 + Math.sqrt((v || 1) / rMax) * 30;

  let grid = '';
  const xticks = opts.xTicks || 5;
  for (let i = 0; i <= xticks; i++) {
    const v = xMin + ((xMax - xMin) * i) / xticks;
    const x = sx(v);
    grid += `<line x1="${x}" y1="${padT}" x2="${x}" y2="${padT + ih}" class="c-grid"/>
      <text x="${x}" y="${H - padB + 24}" class="c-lbl" text-anchor="middle">${opts.xFmt ? opts.xFmt(v) : Math.round(v)}</text>`;
  }
  const yticks = opts.yTicks || 5;
  for (let i = 0; i <= yticks; i++) {
    const v = yMin + ((yMax - yMin) * i) / yticks;
    const y = sy(v);
    grid += `<line x1="${padL}" y1="${y}" x2="${padL + iw}" y2="${y}" class="c-grid"/>
      <text x="${padL - 12}" y="${y}" class="c-lbl" text-anchor="end" dominant-baseline="middle">${v.toFixed(1)}</text>`;
  }

  const dots = points
    .map(
      (p) => `<g class="c-dot">
        <circle cx="${sx(p.x)}" cy="${sy(p.y)}" r="${sr(p.r)}" fill="${p.color || VOLT}" fill-opacity="0.16" stroke="${p.color || VOLT}" stroke-width="1.25">
          <title>${esc(p.label)} — $${p.x} avg · ${p.y}★ · ${fmtInt(p.r)} ratings</title>
        </circle>
        <circle cx="${sx(p.x)}" cy="${sy(p.y)}" r="2.5" fill="${p.color || VOLT}"/>
        <text x="${sx(p.x)}" y="${sy(p.y) - sr(p.r) - 6}" class="c-pt-lbl" text-anchor="middle">${esc(p.label)}</text>
      </g>`
    )
    .join('');

  return `<svg viewBox="0 0 ${W} ${H}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">
    ${grid}
    <text class="c-axis" x="${padL + iw / 2}" y="${H - 6}" text-anchor="middle">${esc(opts.xLabel || '')}</text>
    <text class="c-axis" x="16" y="${padT + ih / 2}" text-anchor="middle" transform="rotate(-90 16 ${padT + ih / 2})">${esc(opts.yLabel || '')}</text>
    ${dots}
  </svg>`;
}

/* Area + line trend. series: [{label, value}] (value drives the area). */
export function area(series, opts = {}) {
  const fmt = opts.fmt || fmtCompact;
  const W = 800;
  const H = 320;
  const padL = 56;
  const padR = 20;
  const padB = 44;
  const padT = 24;
  const iw = W - padL - padR;
  const ih = H - padB - padT;
  const max = Math.max(...series.map((s) => s.value), 1);
  const n = series.length;
  const sx = (i) => padL + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
  const sy = (v) => padT + ih - (v / max) * ih;

  const pts = series.map((s, i) => [sx(i), sy(s.value)]);
  const linePath = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  const areaPath = `${linePath} L ${sx(n - 1)} ${padT + ih} L ${sx(0)} ${padT + ih} Z`;

  let grid = '';
  for (let i = 0; i <= 4; i++) {
    const v = (max * i) / 4;
    const y = sy(v);
    grid += `<line x1="${padL}" y1="${y}" x2="${padL + iw}" y2="${y}" class="c-grid"/>
      <text x="${padL - 10}" y="${y}" class="c-lbl" text-anchor="end" dominant-baseline="middle">${fmt(v)}</text>`;
  }
  const every = opts.labelEvery || 1;
  const xlabels = series
    .map((s, i) =>
      i % every === 0 || i === n - 1
        ? `<text x="${sx(i)}" y="${H - padB + 24}" class="c-lbl" text-anchor="middle">${esc(s.label)}</text>`
        : ''
    )
    .join('');
  const dots = pts
    .map(
      (p, i) =>
        `<circle cx="${p[0]}" cy="${p[1]}" r="3.5" fill="${VOLT}"><title>${esc(series[i].label)}: ${fmt(series[i].value)}</title></circle>`
    )
    .join('');
  const len = pts.reduce((a, p, i) => (i ? a + Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) : 0), 0);

  return `<svg viewBox="0 0 ${W} ${H}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">
    ${grid}
    <path d="${areaPath}" class="c-area"/>
    <path d="${linePath}" class="c-line" style="--len:${len.toFixed(0)}" fill="none" stroke="${VOLT}" stroke-width="2.5"/>
    ${dots}${xlabels}
  </svg>`;
}

/*
 * 100%-style stacked horizontal bars: length ∝ total (so volume still ranks),
 * split into sentiment segments. rows: [{label, pos, neu, neg, total}]
 */
export function stackedBars(rows, opts = {}) {
  const fmt = opts.fmt || fmtInt;
  const W = 800;
  const rowH = 28;
  const gap = 12;
  const labelW = opts.labelW || 150;
  const valW = 70;
  const barX = labelW + 8;
  const barMax = W - barX - valW;
  const legendH = opts.legend ? 36 : 0;
  const H = rows.length * (rowH + gap);
  const max = Math.max(...rows.map((r) => r.total), 1);
  const SEG = [
    ['pos', '#0071e3', 'LOVES'],
    ['neu', '#d2d2d7', 'NEUTRAL'],
    ['neg', '#ff3b30', 'COMPLAINTS'],
  ];

  const bars = rows
    .map((r, i) => {
      const y = i * (rowH + gap);
      const w = Math.max(2, (r.total / max) * barMax);
      let x = barX;
      let parts = '';
      SEG.forEach(([k, c]) => {
        const sw = r.total ? (r[k] / r.total) * w : 0;
        if (sw > 0.2) {
          parts += `<rect x="${x.toFixed(1)}" y="2" width="${sw.toFixed(1)}" height="${rowH - 4}" fill="${c}">
            <title>${esc(r.label)} — ${k}: ${fmt(r[k])} (${Math.round((100 * r[k]) / r.total)}%)</title></rect>`;
        }
        x += sw;
      });
      return `<g transform="translate(0 ${y})">
        <text x="${labelW}" y="${rowH / 2}" class="c-lbl" text-anchor="end" dominant-baseline="middle">${esc(r.label)}</text>
        ${parts}
        <text x="${W}" y="${rowH / 2}" class="c-val" text-anchor="end" dominant-baseline="middle">${fmt(r.total)}</text>
      </g>`;
    })
    .join('');

  let legend = '';
  if (opts.legend) {
    legend =
      `<g transform="translate(${barX} ${H + 20})">` +
      SEG.map(
        ([, c, lbl], i) =>
          `<g transform="translate(${i * 150} 0)"><rect width="14" height="10" y="-9" fill="${c}"/><text x="20" y="0" class="c-lbl" dominant-baseline="middle">${lbl}</text></g>`
      ).join('') +
      `</g>`;
  }

  return `<svg viewBox="0 0 ${W} ${H + legendH}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">${bars}${legend}</svg>`;
}

/* palette for multi-series brand lines — restrained, on-brand, still distinguishable */
/* Apple system colors — distinguishable but restrained for the multi-line chart */
const SERIES_COLORS = ['#0071e3', '#34c759', '#5e5ce6', '#ff9f0a', '#ff375f', '#86868b'];

/*
 * Multi-series line chart. months: ['YYYY-MM', ...]; series: [{brand, values:[…]}]
 * opts: { labelEvery, yFmt, yUnit }
 */
export function multiLine(months, series, opts = {}) {
  const W = 800;
  const H = 380;
  const padL = 46;
  const padR = 16;
  const padB = 70;
  const padT = 18;
  const iw = W - padL - padR;
  const ih = H - padB - padT;
  const n = months.length;
  const every = opts.labelEvery || 12;
  const max = Math.max(...series.flatMap((s) => s.values), 1) * 1.12;
  const sx = (i) => padL + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
  const sy = (v) => padT + ih - (v / max) * ih;
  const yUnit = opts.yUnit || '%';

  let grid = '';
  for (let i = 0; i <= 4; i++) {
    const v = (max * i) / 4;
    const y = sy(v);
    grid += `<line x1="${padL}" y1="${y}" x2="${padL + iw}" y2="${y}" class="c-grid"/>
      <text x="${padL - 8}" y="${y}" class="c-lbl" text-anchor="end" dominant-baseline="middle">${v.toFixed(0)}${yUnit}</text>`;
  }
  let xl = '';
  months.forEach((m, i) => {
    if (i % every === 0 || i === n - 1) {
      xl += `<text x="${sx(i)}" y="${H - padB + 22}" class="c-lbl" text-anchor="middle">${esc(m)}</text>`;
    }
  });

  const lines = series
    .map((s, si) => {
      const color = s.color || SERIES_COLORS[si % SERIES_COLORS.length];
      const pts = s.values.map((v, i) => [sx(i), sy(v)]);
      const path = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
      const len = pts.reduce((a, p, i) => (i ? a + Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) : 0), 0);
      const end = pts[pts.length - 1];
      return `<path d="${path}" fill="none" stroke="${color}" stroke-width="2.25" class="c-mline" style="--len:${len.toFixed(0)}">
          <title>${esc(s.brand)}</title></path>
        <circle cx="${end[0]}" cy="${end[1]}" r="3" fill="${color}"/>`;
    })
    .join('');

  const legend = series
    .map((s, si) => {
      const color = s.color || SERIES_COLORS[si % SERIES_COLORS.length];
      const perRow = Math.ceil(series.length / 1);
      const x = padL + si * (iw / perRow);
      return `<g transform="translate(${x.toFixed(0)} ${H - 20})">
        <rect width="16" height="3" y="-4" fill="${color}"/>
        <text x="22" y="0" class="c-lbl" dominant-baseline="middle">${esc(s.brand)}</text></g>`;
    })
    .join('');

  return `<svg viewBox="0 0 ${W} ${H}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">${grid}${xl}${lines}${legend}</svg>`;
}

export { VOLT, ICE, DIM, LINE, SERIES_COLORS };
