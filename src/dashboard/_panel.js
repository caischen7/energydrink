/*
 * Shared panel scaffold for the dashboard panel modules in this directory.
 *
 * Lives here rather than in charts.js so panel modules don't import from the
 * chart library just to get the wrapper (and so charts.js stays purely about
 * drawing). dashboard.js imports it from here too.
 */
export function panel(id, idx, title, meta, bodyHTML, insight) {
  return `
  <section class="panel-card reveal" id="${id}">
    <header class="pc-head mono">
      <span class="pc-id">${String(idx).padStart(2, '0')}</span>
      <h2 class="pc-title">${title}</h2>
      <span class="pc-meta">${meta}</span>
    </header>
    <div class="pc-body">${bodyHTML}</div>
    ${insight ? `<footer class="pc-insight mono"><b class="volt">&gt;</b> ${insight}</footer>` : ''}
  </section>`;
}
