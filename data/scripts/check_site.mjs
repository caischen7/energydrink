#!/usr/bin/env node
/*
 * Site verification harness — structure, charts, facts, responsive.
 *
 * Why this is in the repo rather than a scratch directory: three rounds of chart
 * work each fixed a defect the previous round introduced (overflow -> truncation
 * -> an off-by-one between the sizing and clipping constants). Every one of those
 * would have been caught by a check that ran on demand instead of from memory.
 *
 * `npm run build` will not catch any of this. It compiles a page that throws
 * "D is not defined" at runtime just as happily as a working one.
 *
 * Usage:
 *   npm run build && cp -r public/data dist/
 *   npx vite preview --port 4173 &
 *   node data/scripts/check_site.mjs                 # all suites
 *   node data/scripts/check_site.mjs dom             # HTML visuals only
 *   node data/scripts/check_site.mjs charts facts    # named suites
 *
 * Playwright is deliberately NOT in package.json — it would triple the Docker
 * build for a tool only used here. Install it when you need to check:
 *   npm i -D playwright
 * Chromium is already present in the dev container at the path probed below.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const BASE = process.env.SITE_URL || 'http://localhost:4173';
/* Only needed if the target actually enforces auth. Against `vite preview` there
   is no nginx, so requireAuth's credential-less fetch succeeds and no form ever
   appears — which is why there is no password baked in here. Point this at a
   real deployment with SITE_USER/SITE_PASS from docs/CREDENTIALS.md. */
const USER = process.env.SITE_USER || 'energydrink';
const PASS = process.env.SITE_PASS || '';
const PAGES = ['index.html', 'dashboard.html', 'insights.html', 'segments.html',
               'audience.html', 'compare.html', 'opportunity.html', 'explorer.html'];

const CHROMIUM = [
  '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  '/opt/pw-browsers/chromium/chrome-linux/chrome',
].find((p) => fs.existsSync(p));

const want = process.argv.slice(2);
const run = (name) => !want.length || want.includes(name);

const fails = [];
const oks = [];
const chk = (label, cond) => (cond ? oks : fails).push(label);

/* ------------------------------------------------------------------ setup */
let chromium;
try {
  ({ chromium } = await import(path.join(ROOT, 'node_modules/playwright/index.mjs')));
} catch {
  console.error('playwright not installed — run:  npm i -D playwright');
  process.exit(2);
}

const browser = await chromium.launch(CHROMIUM ? { executablePath: CHROMIUM } : {});

async function open(page, file) {
  await page.goto(`${BASE}/${file}`, { waitUntil: 'networkidle' });
  const pw = await page.$('input[type="password"]');
  if (pw) {
    const u = await page.$('input[type="text"], input[autocomplete="username"]');
    if (u) await u.fill(USER);
    await pw.fill(PASS);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1800);
  }
  await page.waitForTimeout(600);
}

/* Reveal drill-downs and paginated panels so their charts get measured too. */
const revealAll = async (page) => {
  await page.evaluate(() => document.querySelectorAll('[hidden]').forEach((e) => { e.hidden = false; }));
  await page.waitForTimeout(400);
};

/* ------------------------------------------------------- 1. structure ---- */
if (run('structure')) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  for (const f of PAGES) {
    const errs = [];
    page.removeAllListeners('pageerror');
    page.on('pageerror', (e) => errs.push(e.message.slice(0, 120)));
    await open(page, f);
    const info = await page.evaluate(() => ({
      h1: document.querySelectorAll('h1').length,
      empty: [...document.querySelectorAll('[id]')]
        .filter((e) => /^(charts|er|map|pie|pie-now|pie-future|pie-flavor|headlines|sources|matrix|slope|bars|contrib)$/.test(e.id))
        .filter((e) => !e.innerHTML.trim()).map((e) => '#' + e.id),
      noAlt: [...document.querySelectorAll('img')].filter((i) => !i.hasAttribute('alt')).length,
    }));
    chk(`${f}: exactly one h1`, info.h1 === 1);
    chk(`${f}: no empty chart containers${info.empty.length ? ' (' + info.empty.join(',') + ')' : ''}`, !info.empty.length);
    chk(`${f}: images have alt text`, info.noAlt === 0);
    chk(`${f}: no runtime errors${errs.length ? ' — ' + errs[0] : ''}`, errs.length === 0);
  }
  await ctx.close();
}

/* ---------------------------------------------------------- 2. charts ---- */
/*
 * Geometry in SCREEN space. getBBox() reports coordinates local to a transformed
 * <g>, and hBars wraps every row in one — measuring that way once reported 132
 * collisions on a 12-row chart, all of them phantom.
 */
if (run('charts')) {
  for (const width of [1440, 390]) {
    const ctx = await browser.newContext({ viewport: { width, height: 1000 } });
    const page = await ctx.newPage();
    for (const f of PAGES) {
      await open(page, f);
      await revealAll(page);
      const rs = await page.evaluate(() => {
        const out = [];
        document.querySelectorAll('svg[viewBox]').forEach((s, i) => {
          const vb = s.getAttribute('viewBox').split(/[\s,]+/).map(Number);
          const R = s.getBoundingClientRect();
          if (R.width < 5 || R.height < 5) return;
          const texts = [...s.querySelectorAll('text')]
            .filter((t) => t.textContent.trim())
            .map((t) => { const b = t.getBoundingClientRect();
              return { t: t.textContent.trim(), x: b.x, y: b.y, w: b.width, h: b.height }; })
            .filter((t) => t.w > 0 && t.h > 0);
          let esc = 0, worst = 0;
          for (const t of texts) {
            const over = Math.max(0, t.x + t.w - (R.x + R.width), R.x - t.x,
                                     t.y + t.h - (R.y + R.height), R.y - t.y);
            if (over > 2) { esc++; worst = Math.max(worst, over); }
          }
          let coll = 0; const ex = [];
          for (let a = 0; a < texts.length; a++) {
            for (let b2 = a + 1; b2 < texts.length; b2++) {
              const A = texts[a], C = texts[b2];
              const ox = Math.min(A.x + A.w, C.x + C.w) - Math.max(A.x, C.x);
              const oy = Math.min(A.y + A.h, C.y + C.h) - Math.max(A.y, C.y);
              if (ox > 1 && oy > Math.min(A.h, C.h) * 0.4) {
                coll++; if (ex.length < 2) ex.push(`"${A.t.slice(0,18)}"/"${C.t.slice(0,18)}"`);
              }
            }
          }
          const trunc = texts.filter((t) => t.t.includes('…')).map((t) => t.t);
          out.push({ id: (s.closest('[id]') || {}).id || ('svg' + i),
            /* A sparkline is SUPPOSED to stretch: it is a fixed-height strip
               whose width follows the grid column, and preserveAspectRatio is
               "none" on purpose so the shape fills it. The distortion test is
               meaningless there and would only ever be silenced by padding the
               viewBox with a lie. Every other chart still has to hold its
               ratio, which is what the test is for. */
            spark: s.classList.contains('sg-spark'),
            distort: +((R.width / R.height) / (vb[2] / vb[3])).toFixed(2),
            esc, worst: Math.round(worst), coll, ex, trunc });
        });
        return out;
      });
      for (const r of rs) {
        const tag = `[${width}] ${f} #${r.id}`;
        if (!r.spark) {
          chk(`${tag}: box matches content${r.distort !== 1 ? ` (${r.distort}x)` : ''}`,
              r.distort >= 0.9 && r.distort <= 1.12);
        }
        chk(`${tag}: labels inside the frame${r.esc ? ` (${r.esc}, max ${r.worst}px)` : ''}`, r.esc === 0);
        chk(`${tag}: no overlapping labels${r.coll ? ' ' + r.ex.join(' ') : ''}`, r.coll === 0);
        /* Truncation is a real defect: an ellipsised label loses the finding.
           Treemap boxes are the one place a name genuinely cannot fit. */
        const allowed = f === 'segments.html';
        chk(`${tag}: labels not truncated${r.trunc.length ? ' — ' + r.trunc[0] : ''}`,
            allowed || r.trunc.length === 0);
      }
    }
    await ctx.close();
  }
}

/* --------------------------------------------------------- 2b. visible --- */
/*
 * A mark can have perfect geometry and still never appear. The entrance
 * animation starts bars at scaleX(0) and lines at a full stroke-dashoffset,
 * released by an .in class on the panel; the opportunity page had no observer
 * adding it, so its bars sat at zero width permanently. Correct in the DOM,
 * invisible on screen, no console error, and every other suite green.
 *
 * Each mark is scrolled to individually and measured after the transition
 * would have landed. Measuring after a single sweep instead produced false
 * positives: revealAll() un-hides paginated panels outside the flow their
 * observer expects, so they report as unpainted when a real reader would
 * never see them that way.
 */
if (run('visible')) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await ctx.newPage();
  for (const f of PAGES) {
    await open(page, f);
    await revealAll(page);
    const n = await page.evaluate(() =>
      document.querySelectorAll('.c-bar-h, .c-bar-v, .c-mline, .c-line').length);
    const dead = [];
    for (let i = 0; i < Math.min(n, 60); i++) {
      const r = await page.evaluate(async (idx) => {
        const el = document.querySelectorAll('.c-bar-h, .c-bar-v, .c-mline, .c-line')[idx];
        if (!el) return null;
        const w = parseFloat(el.getAttribute('width') || '1');
        const h = parseFloat(el.getAttribute('height') || '1');
        if (w <= 0.5 || h <= 0.5) return null;         /* legitimately zero */
        el.scrollIntoView({ block: 'center' });
        await new Promise((res) => setTimeout(res, 700));
        const cs = getComputedStyle(el);
        if (el.tagName.toLowerCase() === 'path') {
          /* stroke-dashoffset only hides anything while a dasharray is set.
             Once the panel is revealed the dasharray drops to none and the
             offset merely transitions to 0 - the line is fully drawn the
             whole time. Checking the offset alone flags every line caught
             mid-transition. */
          if (cs.strokeDasharray === 'none') return null;
          const off = parseFloat(cs.strokeDashoffset) || 0;
          const len = parseFloat(cs.strokeDasharray) || 0;
          return len > 0 && off > len * 0.9 ? el.getAttribute('class') : null;
        }
        const box = el.getBoundingClientRect();
        return (box.width < 0.5 || box.height < 0.5) ? el.getAttribute('class') : null;
      }, i);
      if (r) dead.push(r);
    }
    chk(`${f}: every chart mark actually paints${dead.length ? ` (${dead.length}) — ` + dead[0] : ''}`,
        dead.length === 0);
  }
  await ctx.close();
}

/* ------------------------------------------------------------- 3. dom ---- */
/*
 * Charts on this site are not all SVG. The white-space matrix, the price grid,
 * the brand/size bar lists and the e-commerce claim rails are HTML, and the
 * chart suite above cannot see any of them — it passed 359/359 while the
 * opportunity page shipped grey-on-grey bars, grey labels on solid-blue cells
 * and column headers clipped to "Peach & stone f".
 *
 * Two things get checked here, on rendered geometry rather than on source:
 *   clipping  — text wider than the box that is set to hide the overflow
 *   contrast  — WCAG AA on every visible text run, against the real painted
 *               background, walking up ancestors until something is opaque
 */
if (run('dom')) {
 /* Both widths: contrast is width-independent, but the column crush only
    appears on a phone. */
 for (const width of [1440, 390]) {
  const ctx = await browser.newContext({ viewport: { width, height: 1000 } });
  const page = await ctx.newPage();
  for (const f of PAGES) {
    await open(page, f);
    await revealAll(page);
    const r = await page.evaluate(() => {
      const srgb = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
      const lum = ([r, g, b]) => 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b);
      /* Chrome resolves color-mix() to `color(srgb r g b / a)` with 0-1
         channels, not rgba(). The matrix cells are painted that way, so a
         regex that only knows rgba() reads them as transparent - and every
         white-on-blue label then measures against white. */
      const parse = (s) => {
        const t = String(s);
        let m = t.match(/rgba?\(([^)]+)\)/);
        if (m) {
          const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
          return { rgb: p.slice(0, 3), a: p.length > 3 ? p[3] : 1 };
        }
        m = t.match(/color\(srgb\s+([^)]+)\)/);
        if (m) {
          const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
          return { rgb: p.slice(0, 3).map((c) => c * 255), a: p.length > 3 ? p[3] : 1 };
        }
        return null;
      };
      const mix = (fg, bg, a) => fg.map((c, i) => c * a + bg[i] * (1 - a));
      /* Walk up until the accumulated background is opaque. Cells here are
         painted with color-mix over the page, so the parent matters. */
      const bgOf = (el) => {
        let acc = null;                       /* nearest translucent layer, if any */
        for (let n = el; n; n = n.parentElement) {
          const p = parse(getComputedStyle(n).backgroundColor);
          if (!p || p.a === 0) continue;
          if (p.a === 1) return acc ? mix(acc.rgb, p.rgb, acc.a) : p.rgb;
          if (!acc) acc = { rgb: p.rgb, a: p.a };
        }
        return acc ? mix(acc.rgb, [255, 255, 255], acc.a) : [255, 255, 255];
      };
      const ratio = (a, b) => {
        const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m);
        return (x + 0.05) / (y + 0.05);
      };

      const clipped = [], low = [], crushed = [];
      for (const el of document.querySelectorAll('body *')) {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) continue;
        const box = el.getBoundingClientRect();
        if (box.width < 4 || box.height < 4) continue;

        /* Only leaf text nodes — a wrapper's text is its children's. */
        const own = [...el.childNodes]
          .filter((n) => n.nodeType === 3 && n.textContent.trim())
          .map((n) => n.textContent.trim()).join(' ');
        /* Pure separators and icon glyphs carry no information - a dim middot
           between two readable strings is not a contrast defect. */
        if (!own || !/[\p{L}\p{N}]/u.test(own)) continue;

        /* A column squeezed below a few characters wide wraps one letter per
           line. table-layout:fixed splits the width evenly, so a 15-column
           matrix on a phone gives each column ~23px and the grid becomes a
           vertical alphabet. Fixed by a min-width that makes the wrapper
           scroll; checked here so it cannot come back. */
        if (/^(TD|TH)$/.test(el.tagName) && el.clientWidth > 0 && el.clientWidth < 34
            && own.replace(/\s/g, '').length > 5) {
          crushed.push(`${own.slice(0, 20)} @${Math.round(el.clientWidth)}px`);
        }

        const hidesX = cs.overflowX === 'hidden' || cs.textOverflow === 'ellipsis';
        if (hidesX && el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) {
          clipped.push(own.slice(0, 34));
        }

        const fg = parse(cs.color);
        if (fg && fg.a > 0.15) {
          const bg = bgOf(el);
          const eff = fg.a === 1 ? fg.rgb : mix(fg.rgb, bg, fg.a);
          const size = parseFloat(cs.fontSize);
          const bold = +cs.fontWeight >= 600;
          const large = size >= 24 || (size >= 18.66 && bold);
          const need = large ? 3 : 4.5;
          const got = ratio(eff, bg);
          if (got < need) low.push(`${own.slice(0, 26)} (${got.toFixed(1)}:1, needs ${need})`);
        }
      }
      return { clipped: [...new Set(clipped)], low: [...new Set(low)], crushed: [...new Set(crushed)] };
    });
    chk(`[${width}] ${f}: no text clipped by its own box${r.clipped.length ? ` (${r.clipped.length}) — ${r.clipped[0]}` : ''}`,
        r.clipped.length === 0);
    chk(`[${width}] ${f}: text meets WCAG AA on its real background${r.low.length ? ` (${r.low.length}) — ${r.low[0]}` : ''}`,
        r.low.length === 0);
    chk(`[${width}] ${f}: no table column crushed below readable width${r.crushed.length ? ` (${r.crushed.length}) — ${r.crushed[0]}` : ''}`,
        r.crushed.length === 0);
  }
  await ctx.close();
 }
}

/* ------------------------------------------------------ 4. responsive ---- */
if (run('responsive')) {
  for (const v of [{ n: 'mobile', w: 390 }, { n: 'tablet', w: 820 }, { n: 'desktop', w: 1440 }]) {
    const ctx = await browser.newContext({ viewport: { width: v.w, height: 900 } });
    const page = await ctx.newPage();
    for (const f of PAGES) {
      await open(page, f);
      const r = await page.evaluate(() => ({
        hScroll: document.documentElement.scrollWidth > window.innerWidth + 2,
        tiny: [...document.querySelectorAll('p,li,td,span')]
          .filter((e) => { const fs = parseFloat(getComputedStyle(e).fontSize); return fs > 0 && fs < 9.5; }).length,
      }));
      chk(`${v.n} ${f}: no horizontal scroll`, !r.hScroll);
      chk(`${v.n} ${f}: no text under 9.5px`, r.tiny === 0);
    }
    await ctx.close();
  }
}

/* ----------------------------------------------------------- 5. facts ---- */
/* Numbers written into page copy must still match the aggregate they came from. */
if (run('facts')) {
  const J = JSON.parse(fs.readFileSync(path.join(ROOT, 'public/data/dashboard.json'), 'utf8'));
  const A = J.audiences, D = A.demand, O = A.opportunity;
  const html = (f) => fs.readFileSync(path.join(ROOT, f), 'utf8').replace(/\s+/g, ' ');
  const H = html('audience.html');
  const now = (n) => D.now.auds.find((a) => a.name === n).share;
  const fut = (n) => D.future.auds.find((a) => a.name === n).share;

  chk('market 2025 $26.9B', Math.abs(D.now.market - 26948) < 5);
  chk('market 2030 $38.6B', Math.abs(D.future.market - 38600) < 5);
  chk('demand shares sum to 100', Math.abs(D.now.auds.reduce((s, a) => s + a.share, 0) - 100) < 1);
  chk('2030 shares sum to 100', Math.abs(D.future.auds.reduce((s, a) => s + a.share, 0) - 100) < 1);
  chk('dollars reconcile to the market total',
      Math.abs(D.now.auds.reduce((s, a) => s + a.usd, 0) - D.now.market) / D.now.market < 0.01);
  chk('young adults 73.0% -> 64.1%', now('Young adults') === 73.0 && fut('Young adults') === 64.1);
  chk('women 13.2% -> 22.4%', now('Women (fitness & wellness)') === 13.2 && fut('Women (fitness & wellness)') === 22.4);
  chk('superseded MULO estimate kept for audit', !!D.alt_mulo);
  chk('"has not yet slowed" claim is gone',
      !/has not yet slowed|without slowing/.test(H) && !/has not yet slowed|without slowing/.test(html('compare.html')));
  chk('back-test MAE 5.1pp', Math.abs(D.backtest.mae - 5.13) < 0.05);
  chk('drinks + shots = market total',
      Math.abs((D.segments_dw.rows.find((r) => r.y === 2025).drinks
              + D.segments_dw.rows.find((r) => r.y === 2025).shots) - D.now.market) < 5);
  chk('channel shares: convenience 59.9%', D.channel_detail.chs.convenience.share25 === 59.9);
  chk('product count is distinct barcodes, not rows', A.skus === 2178 && A.skus_rows === 2309);
  chk('quality audit records the GTIN failure',
      A.data_quality.checks.find((c) => /GTIN is unique/.test(c[0]))[1] === 'fail');
  chk('16oz best rung is $2.50-2.99', O.price_grid.best['16 oz'].band === '$2.50–2.99');
  chk('verdict prices the can, not the ounce', /2\.50/.test(O.verdict.why.find((w) => w[0] === 'Price')[1]));
  chk('insights: 22 findings across 8 sources', J.insights.insights.length === 22 && J.insights.sources.length === 8);
}

await browser.close();

/* ---------------------------------------------------------------- report */
const pad = (n) => String(n).padStart(3);
console.log(`\n${pad(oks.length)} passed`);
if (fails.length) {
  console.log(`${pad(fails.length)} FAILED\n`);
  fails.forEach((f) => console.log('  ✗ ' + f));
  process.exit(1);
}
console.log('    all checks passed');
