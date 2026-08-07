/*
 * Paginates the dashboard: one panel per view instead of one endless scroll.
 *
 * Deliberately a post-processor rather than a change to dashboard.js. It reads whatever
 * panels that file happened to render, so new panels are picked up automatically with no
 * wiring — and the rendering logic stays in one place.
 *
 * dashboard.js renders asynchronously (after the login gate resolves), so we watch #charts
 * and initialise the moment panels appear.
 */
import './dashboard-pages.css';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

function init() {
  const charts = $('#charts');
  const panels = $$('.panel-card', charts);
  if (!panels.length) return false;

  /* Every routable view: the chart panels, then the two standalone sections that
     already live in dashboard.html. */
  const pages = panels.map((el) => ({
    el,
    id: el.id,
    num: $('.pc-id', el)?.textContent.trim() || '',
    title: $('.pc-title', el)?.textContent.trim() || el.id,
  }));

  const matrix = $('#matrix');
  if (matrix) {
    pages.push({ el: matrix, id: 'matrix', num: $('.pc-id', matrix)?.textContent.trim() || '',
                 title: $('.pc-title', matrix)?.textContent.trim() || 'Brand Matrix' });
  }
  const method = $('.methodology');
  if (method) {
    method.id = method.id || 'methodology';
    pages.push({ el: method, id: method.id, num: '', title: 'Methodology' });
  }

  /* Sort by the panel's own index so the order matches the numbering shown in each header. */
  pages.sort((a, b) => (parseInt(a.num, 10) || 99) - (parseInt(b.num, 10) || 99));

  /* ---- nav ---- */
  const nav = document.createElement('nav');
  nav.className = 'pg-nav';
  nav.setAttribute('aria-label', 'Dashboard panels');
  nav.innerHTML = pages
    .map((p) => `<button class="pg-chip mono" data-go="${p.id}">
        ${p.num ? `<span class="pg-n">${p.num}</span>` : ''}${p.title}</button>`)
    .join('');
  charts.parentNode.insertBefore(nav, charts);

  /* ---- prev / next ---- */
  const pager = document.createElement('div');
  pager.className = 'pg-pager mono';
  pager.innerHTML = `
    <button class="pg-btn" data-step="-1">← Previous</button>
    <span class="pg-pos" aria-live="polite"></span>
    <button class="pg-btn" data-step="1">Next →</button>`;
  (method || matrix || charts).after(pager);

  let idx = 0;

  function show(i, { push = true } = {}) {
    idx = Math.max(0, Math.min(pages.length - 1, i));
    const cur = pages[idx];

    pages.forEach((p, n) => {
      p.el.hidden = n !== idx;
      /* Panels animate in via an IntersectionObserver in dashboard.js. A hidden element
         never intersects, so reveal the active one directly. */
      if (n === idx) p.el.classList.add('in');
    });

    $$('.pg-chip', nav).forEach((c) =>
      c.classList.toggle('on', c.dataset.go === cur.id));
    $('.pg-pos', pager).textContent = `${idx + 1} / ${pages.length}`;
    $$('.pg-btn', pager).forEach((b) => {
      const step = Number(b.dataset.step);
      b.disabled = (step < 0 && idx === 0) || (step > 0 && idx === pages.length - 1);
    });

    if (push && cur.id) history.replaceState(null, '', `#${cur.id}`);
    /* Optional-call both: neither is implemented everywhere (jsdom, older WebViews), and an
       unguarded call throws mid-way through show(), leaving the view half-updated. */
    const chip = $(`.pg-chip[data-go="${cur.id}"]`, nav);
    chip?.scrollIntoView?.({ block: 'nearest', inline: 'nearest' });
    window.scrollTo?.({ top: 0, behavior: 'smooth' });
  }

  const indexOfId = (id) => pages.findIndex((p) => p.id === id);

  nav.addEventListener('click', (e) => {
    const b = e.target.closest('[data-go]');
    if (b) show(indexOfId(b.dataset.go));
  });
  pager.addEventListener('click', (e) => {
    const b = e.target.closest('[data-step]');
    if (b) show(idx + Number(b.dataset.step));
  });

  /* The existing header links (#market, #flavor, …) point at panel ids, so they keep working. */
  window.addEventListener('hashchange', () => {
    const i = indexOfId(location.hash.slice(1));
    if (i >= 0) show(i, { push: false });
  });

  document.addEventListener('keydown', (e) => {
    if (e.target.matches('input, textarea, select')) return;
    if (e.key === 'ArrowLeft') show(idx - 1);
    if (e.key === 'ArrowRight') show(idx + 1);
  });

  const start = indexOfId(location.hash.slice(1));
  show(start >= 0 ? start : 0, { push: false });
  document.body.classList.add('paginated');
  return true;
}

/* dashboard.js fills #charts only after requireAuth() resolves. */
if (!init()) {
  const target = $('#charts');
  if (target) {
    const mo = new MutationObserver(() => {
      if (init()) mo.disconnect();
    });
    mo.observe(target, { childList: true });
  }
}
