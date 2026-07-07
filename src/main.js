/* Bogus Banana — self-hosted type: chunky Archivo display (width axis),
   Space Grotesk body, Space Mono telemetry */
import '@fontsource-variable/archivo/wdth.css';
import '@fontsource-variable/space-grotesk';
import '@fontsource/space-mono/400.css';
import '@fontsource/space-mono/700.css';

import './style.css';
import { initFx } from './fx.js';

const $ = (s) => document.querySelector(s);

/* ---------- minimal splash ---------- */
function boot() {
  return new Promise((resolve) => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const seen = sessionStorage.getItem('ion-booted');
    const total = reduceMotion || seen ? 250 : 800;

    const bar = $('#boot-bar');
    const t0 = performance.now();
    let done = false;

    const finish = () => {
      if (done) return;
      done = true;
      try { sessionStorage.setItem('ion-booted', '1'); } catch (e) { /* private mode */ }
      if (bar) bar.style.width = '100%';
      document.body.classList.add('booted');
      resolve();
    };

    const step = (now) => {
      if (done) return;
      const t = Math.min(1, (now - t0) / total);
      if (bar) bar.style.width = `${(t * 100).toFixed(0)}%`;
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
