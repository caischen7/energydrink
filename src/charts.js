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

/* SVG text does not wrap or ellipsise, so a long label silently runs out of the
   chart. Trim to what the column can hold. 7px/char is measured from the rendered
   label font — 6.2 under-estimated it and still let labels overrun by ~14px. */
/* One constant for both sizing and clipping — two different values left the
   column a character short of what it had just been sized to hold. */
const CH = 7.8;
const clip = (s, px) => {
  const max = Math.floor(px / CH);
  const t = String(s);
  return t.length <= max ? t : t.slice(0, Math.max(1, max - 1)) + '…';
};

/*
 * Horizontal bars with a label column. rows: [{label, value, color?}]
 * opts: { fmt, unit, accent }
 */
export function hBars(rows, opts = {}) {
  const fmt = opts.fmt || fmtCompact;
  const W = 800;
  const rowH = 30;
  const gap = 8;
  /*
   * Grow the label column to fit the longest label rather than truncating it.
   * A fixed width was cutting "Support physical performance" and seven other
   * survey answers down to an ellipsis, which loses the very thing the row says.
   * Capped at 46% of the frame so the bars stay readable; anything past that
   * still clips, and the hover title keeps the full string either way.
   */
  const longest = Math.max(...rows.map((r) => String(r.label).length), 1);
  const labelW = Math.min(Math.max(opts.labelW || 150, longest * CH + 8), W * 0.52);
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
        <text x="${labelW}" y="${rowH / 2}" class="c-lbl" text-anchor="end" dominant-baseline="middle">${esc(clip(r.label, labelW))}</text>
        <rect x="${barX}" y="2" width="${barMax}" height="${rowH - 4}" class="c-track"/>
        <rect x="${barX}" y="2" width="${w}" height="${rowH - 4}" fill="${color}" class="c-bar c-bar-h">
          <title>${esc(r.label)}: ${fmt(r.value)}${opts.unit ? ' ' + opts.unit : ''}</title>
        </rect>
        <text x="${W - 2}" y="${rowH / 2}" class="c-val" text-anchor="end" dominant-baseline="middle">${fmt(r.value)}</text>
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

  /* SVG has no label-collision engine. Place labels largest-bubble-first and skip
     any that would land on one already drawn — a missing label beats two on top
     of each other, and the hover title still carries the name. */
  const placed = [];
  const labelFits = (p) => {
    const x = sx(p.x);
    const y = sy(p.y) - sr(p.r) - 6;
    const halfW = Math.max(18, String(p.label).length * 3.4);
    const hit = placed.some((q) => Math.abs(q.y - y) < 14 && Math.abs(q.x - x) < q.halfW + halfW);
    if (!hit) placed.push({ x, y, halfW });
    return !hit;
  };

  const dots = [...points]
    .sort((a, b) => (b.r || 0) - (a.r || 0))
    .map(
      (p) => `<g class="c-dot">
        <circle cx="${sx(p.x)}" cy="${sy(p.y)}" r="${sr(p.r)}" fill="${p.color || VOLT}" fill-opacity="0.16" stroke="${p.color || VOLT}" stroke-width="1.25">
          <title>${esc(opts.tip ? opts.tip(p) : `${p.label} — $${p.x} avg · ${p.y}★ · ${fmtInt(p.r)} ratings`)}</title>
        </circle>
        <circle cx="${sx(p.x)}" cy="${sy(p.y)}" r="2.5" fill="${p.color || VOLT}"/>
        ${labelFits(p) ? `<text x="${sx(p.x)}" y="${sy(p.y) - sr(p.r) - 6}" class="c-pt-lbl" text-anchor="middle">${esc(p.label)}</text>` : ''}
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
        ? `<text x="${sx(i)}" y="${H - padB + 24}" class="c-lbl" text-anchor="${
            i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle'}">${esc(s.label)}</text>`
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
        <text x="${labelW}" y="${rowH / 2}" class="c-lbl" text-anchor="end" dominant-baseline="middle">${esc(clip(r.label, labelW))}</text>
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
  const max = opts.max || Math.max(...series.flatMap((s) => s.values), 1) * 1.12;
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
      xl += `<text x="${sx(i)}" y="${H - padB + 22}" class="c-lbl" text-anchor="${
        i === 0 ? 'start' : i >= months.length - 1 ? 'end' : 'middle'}">${esc(m)}</text>`;
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
          <title>${esc(s.name || s.brand)}</title></path>
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
        <text x="22" y="0" class="c-lbl" dominant-baseline="middle">${esc(s.name || s.brand)}</text></g>`;
    })
    .join('');

  return `<svg viewBox="0 0 ${W} ${H}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">${grid}${xl}${lines}${legend}</svg>`;
}

/*
 * Donut chart. rows: [{label, value, color}]
 *
 * A donut rather than a full pie: the hole carries the total, and with one slice
 * at 71% the remaining eight are thin wedges that read better as a ring than as
 * slivers meeting at a point. Slices under `minLabelPct` get a leader line
 * instead of an inline label, because their arc is too short to sit text on.
 *
 * opts: { size, thickness, fmt, centerLabel, centerValue, minLabelPct, labels, active }
 *   labels:false suppresses all slice labels (for small "you are here" rings)
 *   active:<label> dims every other slice, marking the current selection
 */
export function donut(rows, opts = {}) {
  const {
    size = 460,
    thickness = 108,
    fmt = (v) => String(v),
    centerLabel = '',
    centerValue = '',
    minLabelPct = 4,
    labels = true,
    active = null,
  } = opts;

  const cx = size / 2;
  const cy = size / 2;
  const rOuter = size / 2 - 58;          // room for the leader-line labels
  const rInner = rOuter - thickness;
  const total = rows.reduce((s, r) => s + r.value, 0) || 1;

  const pt = (r, a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];

  let angle = -Math.PI / 2;              // start at 12 o'clock
  const slices = [];
  rows.forEach((row, i) => {
    const frac = row.value / total;
    const sweep = frac * Math.PI * 2;
    const a0 = angle;
    const a1 = angle + sweep;
    const mid = a0 + sweep / 2;
    angle = a1;

    const [x0, y0] = pt(rOuter, a0);
    const [x1, y1] = pt(rOuter, a1);
    const [x2, y2] = pt(rInner, a1);
    const [x3, y3] = pt(rInner, a0);
    const large = sweep > Math.PI ? 1 : 0;
    const d = `M${x0} ${y0} A${rOuter} ${rOuter} 0 ${large} 1 ${x1} ${y1}
               L${x2} ${y2} A${rInner} ${rInner} 0 ${large} 0 ${x3} ${y3} Z`;

    const pct = frac * 100;
    slices.push({ row, i, d, mid, pct });
  });

  const arcs = slices
    .map(
      ({ row, i, d, pct }) => `<path d="${d}" fill="${row.color}" class="c-slice${
        active && row.label !== active ? ' c-slice--off' : ''}"
        style="--i:${i}" data-aud="${esc(row.label)}" tabindex="0" role="button"
        aria-label="${esc(row.label)}, ${pct.toFixed(1)} percent">
        <title>${esc(row.label)} — ${pct.toFixed(1)}% · ${fmt(row.value)}</title></path>`
    )
    .join('');

  /* Inline labels for the fat slices; leader lines for everything else. */
  const labelSvg = !labels ? '' : slices
    .map(({ row, mid, pct }) => {
      if (pct >= minLabelPct) {
        const [lx, ly] = pt((rOuter + rInner) / 2, mid);
        return `<text x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" class="c-slice-pct"
          text-anchor="middle" dominant-baseline="middle">${pct.toFixed(1)}%</text>`;
      }
      /* Below ~1.5% the leader lines converge and the numbers land on top of each
         other. The legend already names those slices, so drop the label. */
      if (pct < 3) return '';
      const [ax, ay] = pt(rOuter + 2, mid);
      const [bx, by] = pt(rOuter + 18, mid);
      const right = Math.cos(mid) >= 0;
      const tx = bx + (right ? 8 : -8);
      return `<polyline points="${ax.toFixed(1)},${ay.toFixed(1)} ${bx.toFixed(1)},${by.toFixed(1)}"
          fill="none" stroke="${row.color}" stroke-width="1.2"/>
        <text x="${tx.toFixed(1)}" y="${by.toFixed(1)}" class="c-slice-out"
          text-anchor="${right ? 'start' : 'end'}" dominant-baseline="middle"
          fill="${row.color}">${pct.toFixed(1)}%</text>`;
    })
    .join('');

  const center = centerValue
    ? `<text x="${cx}" y="${cy - 6}" class="c-hole-v" text-anchor="middle">${esc(centerValue)}</text>
       <text x="${cx}" y="${cy + 16}" class="c-hole-l" text-anchor="middle">${esc(centerLabel)}</text>`
    : '';

  return `<svg viewBox="0 0 ${size} ${size}" class="chart chart--donut"
    preserveAspectRatio="xMidYMid meet" role="img"
    aria-label="Share of energy-drink sales by target audience">${arcs}${labelSvg}${center}</svg>`;
}

/*
 * Slope chart — two points per series, one line between them. rows:
 * [{label, from, to, color}]
 *
 * The right tool for "these nine things all changed between two dates": a
 * reader compares slopes at a glance, where two pie charts force them to hold
 * percentages in their head. Labels collide when values are close, so tightly
 * packed rows get nudged apart vertically.
 *
 * opts: { fmt, leftTitle, rightTitle, minGap }
 */
export function slope(rows, opts = {}) {
  const { fmt = (v) => v + '%', leftTitle = '', rightTitle = '' } = opts;
  const W = 900;
  const ROW = 26;                       // vertical room a label needs, in viewBox units
  const padT = 58;
  const padB = 28;
  /* Height follows the series count. A fixed height forced nine labels into space
     for four, which is what pushed them outside the box. */
  const ih = Math.max(240, (rows.length - 1) * ROW + 40);
  const H = padT + ih + padB;
  const xL = 330;                        // room for "Women (fitness & wellness)"
  const xR = W - 120;
  const max = Math.max(...rows.flatMap((r) => [r.from, r.to]), 1);
  const sy = (v) => padT + ih - (v / max) * ih;

  /*
   * Spread labels that would sit on top of each other, without letting the spread
   * run past either edge. A single downward pass is not enough: seven of nine
   * audiences cluster under 4%, so pushing them all down overflowed the bottom,
   * and correcting by shifting the block up then overflowed the top. Two passes
   * — down from the top, then up from the bottom — settle against both bounds.
   */
  const top = padT;
  const bot = padT + ih;
  const place = (key) => {
    const order = rows.map((r, i) => ({ i, y: sy(r[key]) })).sort((a, b) => a.y - b.y);
    for (let k = 1; k < order.length; k++) {
      order[k].y = Math.max(order[k].y, order[k - 1].y + ROW);
    }
    order[order.length - 1].y = Math.min(order[order.length - 1].y, bot);
    for (let k = order.length - 2; k >= 0; k--) {
      order[k].y = Math.min(order[k].y, order[k + 1].y - ROW);
    }
    order[0].y = Math.max(order[0].y, top);
    for (let k = 1; k < order.length; k++) {
      order[k].y = Math.max(order[k].y, order[k - 1].y + ROW);
    }
    const out = [];
    order.forEach((o) => { out[o.i] = o.y; });
    return out;
  };
  const ly = place('from');
  const ry = place('to');

  const body = rows
    .map((r, i) => {
      const y0 = sy(r.from);
      const y1 = sy(r.to);
      return `<g class="c-slope" data-aud="${esc(r.label)}" tabindex="0" role="button"
                 aria-label="${esc(r.label)}: ${fmt(r.from)} to ${fmt(r.to)}">
        <title>${esc(r.label)} — ${fmt(r.from)} → ${fmt(r.to)}</title>
        <line x1="${xL}" y1="${y0}" x2="${xR}" y2="${y1}" stroke="${r.color}"
              stroke-width="2.4" class="c-slope-line"/>
        <circle cx="${xL}" cy="${y0}" r="4.5" fill="${r.color}"/>
        <circle cx="${xR}" cy="${y1}" r="4.5" fill="${r.color}"/>
        <text x="${xL - 14}" y="${ly[i]}" class="c-slope-l" text-anchor="end"
              dominant-baseline="middle">${esc(clip(r.label, xL - 34 - fmt(r.from).length * 7))}
          <tspan class="c-slope-v" fill="${r.color}"> ${fmt(r.from)}</tspan></text>
        <text x="${xR + 14}" y="${ry[i]}" class="c-slope-v" text-anchor="start"
              dominant-baseline="middle" fill="${r.color}">${fmt(r.to)}</text>
      </g>`;
    })
    .join('');

  return `<svg viewBox="0 0 ${W} ${H}" class="chart chart--slope"
    preserveAspectRatio="xMidYMid meet" role="img"
    aria-label="Share by audience, ${esc(leftTitle)} versus ${esc(rightTitle)}">
    <text x="${xL}" y="26" class="c-slope-h" text-anchor="middle">${esc(leftTitle)}</text>
    <text x="${xR}" y="26" class="c-slope-h" text-anchor="middle">${esc(rightTitle)}</text>
    <line x1="${xL}" y1="${padT - 16}" x2="${xL}" y2="${padT + ih}" class="c-grid"/>
    <line x1="${xR}" y1="${padT - 16}" x2="${xR}" y2="${padT + ih}" class="c-grid"/>
    ${body}</svg>`;
}

/*
 * Paired bars — two values per row, side by side. rows:
 * [{label, a, b, color}]  opts: { fmt, aLabel, bLabel, labelW }
 */
export function groupedBars(rows, opts = {}) {
  const { fmt = fmtCompact, aLabel = 'A', bLabel = 'B', labelW = 190 } = opts;
  const W = 800;
  const rowH = 44;
  const gap = 12;
  const barX = labelW + 8;
  const valW = 92;
  const barMax = W - barX - valW;
  const H = rows.length * (rowH + gap) + 26;
  /* Space the second legend key past the first label instead of at a fixed 92px,
     which "model predicted" overran. */
  const legendGap = Math.max(92, 26 + aLabel.length * 6.2);
  const max = Math.max(...rows.flatMap((r) => [r.a, r.b]), 1);

  const body = rows
    .map((r, i) => {
      const y = 26 + i * (rowH + gap);
      const wa = Math.max(1.5, (r.a / max) * barMax);
      const wb = Math.max(1.5, (r.b / max) * barMax);
      return `<g data-aud="${esc(r.label)}" class="c-grp" tabindex="0" role="button"
                 aria-label="${esc(r.label)}: ${fmt(r.a)} then ${fmt(r.b)}">
        <text x="${labelW}" y="${y + rowH / 2}" class="c-lbl" text-anchor="end"
              dominant-baseline="middle">${esc(r.label)}</text>
        <rect x="${barX}" y="${y + 2}" width="${wa}" height="${rowH / 2 - 3}" rx="3"
              fill="${r.color}" fill-opacity="0.42"><title>${esc(r.label)} ${esc(aLabel)}: ${fmt(r.a)}</title></rect>
        <rect x="${barX}" y="${y + rowH / 2 + 1}" width="${wb}" height="${rowH / 2 - 3}" rx="3"
              fill="${r.color}"><title>${esc(r.label)} ${esc(bLabel)}: ${fmt(r.b)}</title></rect>
        <text x="${barX + wa + 7}" y="${y + rowH / 4 + 1}" class="c-val"
              dominant-baseline="middle">${fmt(r.a)}</text>
        <text x="${barX + wb + 7}" y="${y + (rowH * 3) / 4}" class="c-val"
              dominant-baseline="middle">${fmt(r.b)}</text>
      </g>`;
    })
    .join('');

  return `<svg viewBox="0 0 ${W} ${H}" class="chart" preserveAspectRatio="xMidYMid meet" role="img">
    <g transform="translate(${barX} 12)">
      <rect width="13" height="7" rx="2" fill="${DIM}" fill-opacity="0.42"/>
      <text x="19" y="6" class="c-lbl">${esc(aLabel)}</text>
      <rect x="${legendGap}" width="13" height="7" rx="2" fill="${DIM}"/>
      <text x="${legendGap + 19}" y="6" class="c-lbl">${esc(bLabel)}</text>
    </g>${body}</svg>`;
}

export { VOLT, ICE, DIM, LINE, SERIES_COLORS };


/* Reveal panels as they scroll in. Lives here so every page that renders these
   marks can opt in with one call instead of each re-implementing the observer -
   the opportunity page had no observer at all, which is how its bars ended up
   permanently at scaleX(0). Panels already on screen are revealed immediately,
   and with no IntersectionObserver everything is simply shown. */
export function revealCards(root = document) {
  const cards = [...root.querySelectorAll('.panel-card')];
  if (!('IntersectionObserver' in window)) {
    cards.forEach((c) => c.classList.add('in'));
    return;
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add('in');
      io.unobserve(e.target);
    });
  }, { threshold: 0.12 });
  cards.forEach((c) => io.observe(c));
}
