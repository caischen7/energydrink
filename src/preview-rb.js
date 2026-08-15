/*
 * Entry for preview-redbull.html — the dark, Red-Bull-inspired treatment of
 * the landing page. Deliberately thin: it reuses the real 3D can (scene.js)
 * so the preview is judged against the actual product, not a placeholder,
 * but skips fx.js because that module is wired to the *current* page's
 * markup (edition rows, HUD readouts, mint form).
 *
 * Section ids below must stay in sync with SECTIONS in scene.js — the can's
 * scroll choreography measures them by id.
 */
import '@fontsource-variable/inter';
import '@fontsource-variable/archivo/wdth.css';
import './preview-rb.css';

const $ = (s) => document.querySelector(s);

/* Wrapped rather than top-level await: the build target is es2020. */
async function main() {
  let scene = null;
  try {
    const { initScene } = await import('./scene.js');
    scene = initScene($('#webgl'));
  } catch (err) {
    console.warn('[preview] WebGL unavailable — flat fallback.', err);
    document.body.classList.add('no-webgl');
  }

  if (!scene) return;
  /* Canvas labels are painted before webfonts land; repaint once they do. */
  document.fonts?.ready.then(() => {
    scene.redrawLabels();
    scene.refresh();
  });
  window.addEventListener('load', () => scene.refresh());

  /* Hovering an edition card swaps the can's colourway, same contract fx.js uses. */
  document.querySelectorAll('[data-colorway]').forEach((el) => {
    el.addEventListener('mouseenter', () => scene.setColorway(el.dataset.colorway));
    el.addEventListener('click', () => scene.pulse());
  });
}

/* The ticker scrolls a duplicated track, so the halfway point is seamless. */
const track = $('#rb-ticker-track');
if (track) track.innerHTML += track.innerHTML;

main();
