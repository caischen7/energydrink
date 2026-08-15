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
const USER = process.env.SITE_USER || 'energydrink';
const PASS = process.env.SITE_PASS || 'energydrink';
const PAGES = ['index.html', 'dashboard.html', 'insights.html', 'segments.html',
               'audience.html', 'compare.html', 'opportunity.html'];

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
            distort: +((R.width / R.height) / (vb[2] / vb[3])).toFixed(2),
            esc, worst: Math.round(worst), coll, ex, trunc });
        });
        return out;
      });
      for (const r of rs) {
        const tag = `[${width}] ${f} #${r.id}`;
        chk(`${tag}: box matches content${r.distort !== 1 ? ` (${r.distort}x)` : ''}`,
            r.distort >= 0.9 && r.distort <= 1.12);
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

/* ------------------------------------------------------ 3. responsive ---- */
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

/* ----------------------------------------------------------- 4. facts ---- */
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
