/* ION® — LIQUID HARDWARE */

/* self-hosted fonts (variable Archivo incl. width axis for the expanded display cut) */
import '@fontsource-variable/archivo/wdth.css';
import '@fontsource-variable/space-grotesk';
import '@fontsource/space-mono';
import '@fontsource/space-mono/700.css';

import './style.css';
import { initFx } from './fx.js';

const $ = (s) => document.querySelector(s);

/* ---------- boot sequence ---------- */
const BOOT_LINES = [
  ['> ION_OS v4.2.0 — COLD BOOT', 90],
  ['> MOUNTING /dev/hydration ............ <i class="ok">OK</i>', 240],
  ['> VERIFYING ELECTROLYTE LEDGER ....... <i class="ok">OK</i>', 230],
  ['> CALIBRATING FLUID DYNAMICS ......... <i class="ok">OK</i>', 220],
  ['> RENDERING VESSEL [473ML / AL-99] ... <i class="ok">OK</i>', 260],
];

function boot() {
  return new Promise((resolve) => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const seen = sessionStorage.getItem('ion-booted');
    const total = reduceMotion || seen ? 350 : 1900;

    const log = $('#boot-log');
    const bar = $('#boot-bar');
    const pct = $('#boot-pct');
    const t0 = performance.now();
    let lineIdx = 0;
    let lineAt = 0;
    let done = false;

    const finish = () => {
      if (done) return;
      done = true;
      try { sessionStorage.setItem('ion-booted', '1'); } catch (e) { /* private mode */ }
      bar.style.width = '100%';
      pct.textContent = '100%';
      document.body.classList.add('booted');
      resolve();
    };

    $('#boot').addEventListener('click', finish);

    const step = (now) => {
      if (done) return;
      const t = Math.min(1, (now - t0) / total);
      bar.style.width = `${(t * 100).toFixed(0)}%`;
      pct.textContent = `${(t * 100).toFixed(0)}%`;

      if (lineIdx < BOOT_LINES.length && now - t0 > lineAt) {
        const div = document.createElement('div');
        div.innerHTML = BOOT_LINES[lineIdx][0];
        log.appendChild(div);
        lineAt += BOOT_LINES[lineIdx][1];
        lineIdx++;
      }

      if (t >= 1) finish();
      else requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });
}

/* ---------- init ---------- */
async function main() {
  let scene = null;
  try {
    const { initScene } = await import('./scene.js');
    scene = initScene($('#webgl'));
  } catch (err) {
    console.warn('[ION] WebGL unavailable — running flat fallback.', err);
    document.body.classList.add('no-webgl');
  }

  initFx(scene);
  await boot();

  if (scene) {
    /* re-measure & repaint once webfonts land (label canvases + section offsets) */
    document.fonts?.ready.then(() => {
      scene.redrawLabels();
      scene.refresh();
    });
    /* layout can shift as content settles */
    if (document.readyState === 'complete') scene.refresh();
    else window.addEventListener('load', scene.refresh);
  }
}

main();
