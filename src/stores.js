/*
 * Store Map — where the convenience panel sells energy drinks.
 *
 * Reads `public/data/stores_map.json`, built by
 * data/scripts/build_stores_map.py from `pdi_stores` joined to trailing-12-month
 * sales in `pdi_daily_agg`, plus the OSM bottling-plant extract in
 * data/osm/bottling_candidates.csv.
 *
 * THREE DECISIONS ARE BAKED IN HERE
 * ---------------------------------
 * 1. Symbols scale by SQRT of the value, so the circle's AREA carries the
 *    number. Scaling the radius linearly triples the apparent size of a value
 *    that merely tripled, and readers judge circles by area - it is the single
 *    most common way a bubble map lies.
 *
 * 2. There is no choropleth. Filling state polygons by revenue would draw
 *    Montana louder than New Jersey because it is bigger, and the metric that
 *    matters most here - revenue PER STORE - is a rate, which a choropleth
 *    encodes especially badly. Proportional symbols at state centroids keep
 *    area tied to the quantity instead of to land.
 *
 * 3. The cluster layer draws the GRID CELLS the builder emitted, never stores.
 *    Cells under the builder's floor were dropped before the JSON was written,
 *    so the map is missing stores by design and the legend says how many. See
 *    build_stores_map.py for why PDI store points cannot reach a browser.
 *
 * The ranked list and the table are not decoration: Leaflet vector markers are
 * not keyboard focusable, so they are how this page is usable without a mouse.
 */
import '@fontsource-variable/inter';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './dashboard.css';
import './audience.css';
import './stores.css';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) =>
  String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const money = (v) =>
  v >= 1e9 ? '$' + (v / 1e9).toFixed(2) + 'B' :
  v >= 1e6 ? '$' + (v / 1e6).toFixed(1) + 'M' :
  v >= 1e3 ? '$' + (v / 1e3).toFixed(0) + 'K' : '$' + Math.round(v);
const num = (v) => Math.round(v).toLocaleString('en-US');

const ACCENT = '#0071e3';
const PLANT = '#f77f00';
const TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const ATTRIB = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
const US = [[18.0, -170.0], [66.0, -66.0]];

const METRICS = {
  rev: { label: 'Revenue', short: 'BY REVENUE', fmt: money,
         blurb: 'Category revenue through panel stores, trailing twelve months.' },
  stores: { label: 'Stores', short: 'BY STORE COUNT', fmt: num,
            blurb: 'Panel stores that recorded any energy-drink sale in the window. This is PDI’s coverage, not the state’s store universe.' },
  rev_per_store: { label: 'Revenue per store', short: 'BY REVENUE PER STORE', fmt: money,
                   blurb: 'Revenue divided by stores — a rate, so it is the one metric here that is not just a proxy for population.' },
};

let DATA, map, layers = {}, VIEW = 'states', METRIC = 'rev';
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ------------------------------------------------------------------ scale --
   Area-proportional radii. `hi` is the largest value in the series, so the
   scale is relative to what is on screen rather than to an absolute dollar
   amount - which is right for comparison within a view and wrong for comparing
   across views, hence the legend restating the metric each time. */
const radius = (v, hi, min, max) =>
  hi <= 0 ? min : min + (max - min) * Math.sqrt(Math.max(v, 0) / hi);

/* ------------------------------------------------------------------ notice */
function notice() {
  const el = $('#sm-notice');
  if (DATA.source !== 'sample') {
    el.innerHTML = '';
    return;
  }
  /* The whole reason this banner is not dismissible: a placeholder that looks
     like a measurement is worse than no map at all. */
  el.innerHTML = `
    <div class="sm-warn" role="status">
      <b>Placeholder data.</b> The real store geography lives in <code>pdi_stores</code>
      in BigQuery, which is licensed and not in this repository. Every store
      count, dollar and dot in the two panel layers below is
      <b>generated</b> so the page renders &mdash; none of it is a measurement.
      Run <code>python data/scripts/build_stores_map.py</code> with a BigQuery
      token to replace it. The <b>bottling-plant layer is real</b> OpenStreetMap
      data either way.
    </div>`;
}

/* -------------------------------------------------------------------- KPIs */
function kpis() {
  const m = DATA.meta;
  const st = DATA.states;
  const top = st[0];
  const perStore = [...st].sort((a, b) => b.rev_per_store - a.rev_per_store)[0];
  /* Exactly four. .kpi-strip is a fixed 4-track grid whose --line background
     shows through 1px gaps, so a fifth tile leaves three cells of bare line
     colour sitting next to it. The plant count lives in the legend and the
     methodology block instead. */
  const rows = [
    ['Stores mapped', num(m.stores_mapped), 'in the panel'],
    ['Revenue, T12M', money(m.rev_total), 'through those stores'],
    ['Biggest state', top ? top.code : '—', top ? money(top.rev) : ''],
    ['Richest per store', perStore ? perStore.code : '—',
     perStore ? money(perStore.rev_per_store) + ' / store' : ''],
  ];
  $('#sm-kpis').innerHTML = rows.map(([l, n, u]) => `
    <div class="kpi">
      <div class="kpi-l mono">${esc(l)}</div>
      <div class="kpi-n">${esc(n)}</div>
      <div class="kpi-u mono">${esc(u)}</div>
    </div>`).join('');
}

/* ------------------------------------------------------------------ layers */

function statePopup(s) {
  const share = DATA.meta.rev_total ? (s.rev / DATA.meta.rev_total) * 100 : 0;
  const brands = s.brands.length
    ? `<table class="sm-pop-t">${s.brands.map((b) => `
        <tr><td>${esc(b.b)}</td><td class="num">${money(b.r)}</td></tr>`).join('')}</table>`
    : '<p class="sm-pop-none">No brand breakdown for this state.</p>';
  return `
    <div class="sm-pop">
      <h3>${esc(s.name)}</h3>
      <dl class="sm-pop-kv">
        <dt>Stores</dt><dd>${num(s.stores)}</dd>
        <dt>Revenue</dt><dd>${money(s.rev)}</dd>
        <dt>Per store</dt><dd>${money(s.rev_per_store)}</dd>
        <dt>Share</dt><dd>${share.toFixed(1)}%</dd>
      </dl>
      <h4>Leading brands</h4>
      ${brands}
    </div>`;
}

function buildStates() {
  const g = L.layerGroup();
  const hi = Math.max(...DATA.states.map((s) => s[METRIC] || 0));
  for (const s of DATA.states) {
    const v = s[METRIC] || 0;
    L.circleMarker([s.lat, s.lon], {
      radius: radius(v, hi, 5, 34),
      color: ACCENT, weight: 1.25, opacity: 0.85,
      fillColor: ACCENT, fillOpacity: 0.28,
    })
      .bindPopup(statePopup(s), { maxWidth: 300 })
      .bindTooltip(`${s.name} — ${METRICS[METRIC].fmt(v)}`, { direction: 'top' })
      .addTo(g);
  }
  return g;
}

/* Cells are [lat, lon, stores, rev]. Small and numerous, so they get flat
   circles with no tooltip binding per marker - 2,000 tooltips is a measurable
   amount of DOM. The popup is built on click instead. */
function buildCells() {
  const g = L.layerGroup();
  const val = (c) => (METRIC === 'stores' ? c[2] : METRIC === 'rev' ? c[3] : c[3] / c[2]);
  const hi = Math.max(...DATA.cells.map(val));
  for (const c of DATA.cells) {
    L.circleMarker([c[0], c[1]], {
      radius: radius(val(c), hi, 2.5, 16),
      color: ACCENT, weight: 0.6, opacity: 0.5,
      fillColor: ACCENT, fillOpacity: 0.32,
    })
      .bindPopup(`
        <div class="sm-pop">
          <h3>${num(c[2])} stores</h3>
          <dl class="sm-pop-kv">
            <dt>Revenue</dt><dd>${money(c[3])}</dd>
            <dt>Per store</dt><dd>${money(c[3] / c[2])}</dd>
            <dt>Cell</dt><dd>${c[0].toFixed(2)}, ${c[1].toFixed(2)}</dd>
          </dl>
          <p class="sm-pop-note">A ${DATA.meta.grid_deg}&deg; grid cell, not a store.
          Position is the cell centre.</p>
        </div>`, { maxWidth: 260 })
      .addTo(g);
  }
  return g;
}

function buildPlants() {
  const g = L.layerGroup();
  for (const [lat, lon, name, op, tagged] of DATA.plants) {
    L.circleMarker([lat, lon], {
      radius: 5,
      color: PLANT, weight: 1.4, opacity: 0.9,
      fillColor: PLANT, fillOpacity: tagged ? 0.75 : 0.2,
    })
      .bindPopup(`
        <div class="sm-pop">
          <h3>${esc(name)}</h3>
          ${op ? `<p class="sm-pop-sub">${esc(op)}</p>` : ''}
          <p class="sm-pop-note">${tagged
            ? 'Carries an explicit industrial tag in OpenStreetMap.'
            : 'Matched on the word &ldquo;bottling&rdquo; in its name only — weaker evidence, and some of these are museums and bars.'}</p>
        </div>`, { maxWidth: 260 })
      .bindTooltip(esc(name), { direction: 'top' })
      .addTo(g);
  }
  return g;
}

/* -------------------------------------------------------------- rank + table */

function renderRank() {
  const sorted = [...DATA.states].sort((a, b) => (b[METRIC] || 0) - (a[METRIC] || 0));
  const hi = sorted.length ? sorted[0][METRIC] || 0 : 0;
  $('#sm-side-metric').textContent = METRICS[METRIC].short;
  $('#sm-rank').innerHTML = sorted.slice(0, 15).map((s, i) => {
    const v = s[METRIC] || 0;
    const pct = hi ? (v / hi) * 100 : 0;
    return `
      <li class="sm-rank-row">
        <button type="button" class="sm-rank-btn" data-code="${esc(s.code)}">
          <span class="sm-rank-i mono">${i + 1}</span>
          <span class="sm-rank-n">${esc(s.name)}</span>
          <span class="sm-rank-bar"><i style="width:${pct.toFixed(1)}%"></i></span>
          <span class="sm-rank-v mono">${METRICS[METRIC].fmt(v)}</span>
        </button>
      </li>`;
  }).join('');
}

let SORT = { key: 'rev', dir: -1 };

function renderTable() {
  const total = DATA.meta.rev_total || 1;
  const rows = DATA.states.map((s) => ({
    ...s, share: (s.rev / total) * 100, top: s.brands[0] ? s.brands[0].b : '—',
  }));
  const k = SORT.key;
  rows.sort((a, b) => {
    const x = a[k], y = b[k];
    const c = typeof x === 'string' ? x.localeCompare(y) : (x || 0) - (y || 0);
    return c * SORT.dir;
  });
  $('#sm-table tbody').innerHTML = rows.map((s) => `
    <tr>
      <th scope="row">${esc(s.name)}</th>
      <td class="num">${num(s.stores)}</td>
      <td class="num">${money(s.rev)}</td>
      <td class="num">${money(s.rev_per_store)}</td>
      <td class="num">${s.share.toFixed(1)}%</td>
      <td>${esc(s.top)}</td>
    </tr>`).join('');
  for (const th of document.querySelectorAll('#sm-table th[data-sort]')) {
    const on = th.dataset.sort === k;
    th.setAttribute('aria-sort', on ? (SORT.dir < 0 ? 'descending' : 'ascending') : 'none');
    th.classList.toggle('sorted', on);
  }
}

/* ----------------------------------------------------------------- legend */

function renderLegend() {
  const m = DATA.meta;
  const el = $('#sm-legend');
  if (VIEW === 'plants') {
    el.innerHTML = `Solid dots carry an explicit industrial tag in OpenStreetMap
      (${DATA.plants.filter((p) => p[4]).length} of ${DATA.plants.length}); hollow ones
      were matched on the word &ldquo;bottling&rdquo; in a name and include some
      false positives. Not a census &mdash; see <code>data/osm/README.md</code>.`;
    return;
  }
  const scope = VIEW === 'states'
    ? `One circle per state, drawn at the state centroid.`
    : `One circle per ${m.grid_deg}&deg; grid cell (about 11&nbsp;km), holding
       ${m.min_cell} or more stores.`;
  const dropped = VIEW === 'cells'
    ? ` <b>${num(m.stores_suppressed)} stores in ${num(m.cells_suppressed)} thinner cells
        are not drawn</b> &mdash; mostly rural &mdash; because a cell of one store is
        that store's exact location and revenue.`
    : '';
  el.innerHTML = `${scope} Area is proportional to
    <b>${esc(METRICS[METRIC].label.toLowerCase())}</b>, not radius, so a circle
    with four times the area carries four times the value.
    ${esc(METRICS[METRIC].blurb)}${dropped}`;
}

/* ----------------------------------------------------------------- method */

function renderMethod() {
  const m = DATA.meta;
  const cards = [
    ['Window', `${esc(m.window)}. One window only: a map of change over time would be mostly the panel growing, drawn as demand, and nothing inside this data separates the two.`],
    ['Coverage', esc(m.coverage)],
    ['What leaves the warehouse', esc(m.privacy)],
    ['Bottling plants', `Real OpenStreetMap data, independent of PDI and of the sample switch. ${DATA.plants.length} candidates, of which ${DATA.plants.filter((p) => p[4]).length} carry an explicit industrial tag; the rest matched on a name. Most energy brands co-pack rather than own plants, so this answers &ldquo;where is capacity&rdquo; and not &ldquo;who makes what&rdquo;.`],
  ];
  $('#sm-method').innerHTML = cards.map(([h, b]) => `
    <div class="method-card">
      <h3 class="mono">${esc(h)}</h3>
      <p>${b}</p>
    </div>`).join('');
}

/* ------------------------------------------------------------------- map */

function setLayer() {
  for (const k of Object.keys(layers)) {
    if (layers[k] && map.hasLayer(layers[k])) map.removeLayer(layers[k]);
  }
  if (!layers[VIEW]) {
    layers[VIEW] = VIEW === 'states' ? buildStates()
      : VIEW === 'cells' ? buildCells() : buildPlants();
  }
  layers[VIEW].addTo(map);
}

/* The metric changes the geometry of every marker, so the two data layers are
   thrown away and rebuilt rather than walked. Plants carry no metric. */
function invalidateMetricLayers() {
  for (const k of ['states', 'cells']) {
    if (layers[k]) {
      if (map.hasLayer(layers[k])) map.removeLayer(layers[k]);
      layers[k] = null;
    }
  }
}

function flyToState(code) {
  const s = DATA.states.find((x) => x.code === code);
  if (!s) return;
  const to = [s.lat, s.lon];
  if (reduced) map.setView(to, 6);
  else map.flyTo(to, 6, { duration: 0.8 });
  if (VIEW === 'states' && layers.states) {
    layers.states.eachLayer((l) => {
      const ll = l.getLatLng();
      if (Math.abs(ll.lat - s.lat) < 1e-6 && Math.abs(ll.lng - s.lon) < 1e-6) l.openPopup();
    });
  }
}

function hint() {
  $('#sm-hint').textContent = VIEW === 'plants'
    ? '> BOTTLING PLANTS :: REAL OSM DATA :: SIZE IS FIXED'
    : `> ${VIEW === 'states' ? 'STATE CENTROIDS' : 'STORE CLUSTERS'} :: AREA ∝ ${METRICS[METRIC].label.toUpperCase()}`;
}

function redraw() {
  hint();
  setLayer();
  renderLegend();
  renderRank();
}

/* ------------------------------------------------------------------ wiring */

function controls() {
  for (const btn of document.querySelectorAll('.sm-btn[data-view]')) {
    btn.addEventListener('click', () => {
      VIEW = btn.dataset.view;
      for (const b of document.querySelectorAll('.sm-btn[data-view]')) {
        b.setAttribute('aria-selected', String(b === btn));
      }
      /* Plants have no metric; disabling the toggle is clearer than leaving
         three live buttons that do nothing. */
      for (const b of document.querySelectorAll('.sm-btn[data-metric]')) {
        b.disabled = VIEW === 'plants';
      }
      redraw();
    });
  }
  for (const btn of document.querySelectorAll('.sm-btn[data-metric]')) {
    btn.addEventListener('click', () => {
      METRIC = btn.dataset.metric;
      for (const b of document.querySelectorAll('.sm-btn[data-metric]')) {
        b.setAttribute('aria-selected', String(b === btn));
      }
      invalidateMetricLayers();
      redraw();
    });
  }
  $('#sm-rank').addEventListener('click', (e) => {
    const b = e.target.closest('[data-code]');
    if (b) flyToState(b.dataset.code);
  });
  for (const th of document.querySelectorAll('#sm-table th[data-sort]')) {
    th.tabIndex = 0;
    const go = () => {
      const k = th.dataset.sort;
      SORT = { key: k, dir: SORT.key === k ? -SORT.dir : (k === 'name' || k === 'top' ? 1 : -1) };
      renderTable();
    };
    th.addEventListener('click', go);
    th.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
    });
  }
}

/* -------------------------------------------------------------------- boot */

async function main() {
  DATA = await requireAuth({ dataUrl: 'data/stores_map.json' });
  DATA.plants = DATA.plants || [];
  DATA.states = DATA.states || [];
  DATA.cells = DATA.cells || [];

  notice();
  kpis();
  renderMethod();
  renderTable();

  map = L.map('sm-map', { zoomControl: true, scrollWheelZoom: false });
  L.tileLayer(TILES, { maxZoom: 18, attribution: ATTRIB }).addTo(map);
  map.fitBounds(US);
  /* Wheel-zoom is off by default so the page still scrolls past a full-bleed
     map on a laptop; ctrl/cmd-wheel and the +/- control still zoom. */
  map.on('click', () => map.scrollWheelZoom.enable());
  map.on('mouseout', () => map.scrollWheelZoom.disable());

  controls();
  redraw();

  /* The map is laid out inside a grid that settles after fonts arrive; without
     this Leaflet caches a stale size and tiles come up grey on the right edge. */
  const fix = () => map.invalidateSize();
  document.fonts?.ready.then(fix);
  addEventListener('resize', fix);
  setTimeout(fix, 0);
}

main();
