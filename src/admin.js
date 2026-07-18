/*
 * Bogus Banana // Site Scout — restaurant-location scouting tool (admin).
 *
 * Interactive Leaflet map over OpenStreetMap data (all free, no API keys):
 *   - Scan an area via the Overpass API: existing restaurants/fast food/cafés
 *     (competitors), traffic signals (access), vacant/disused storefronts
 *     (lease leads), parking, transit stops, demand anchors (schools/offices).
 *   - Drop candidate pins (e.g. from a broker's sheet) and score them 0–100
 *     with a weighted scorecard shaped by a restaurant-operator panel:
 *     per-mode weights (QSR / coffee / full-service), non-linear competitor
 *     curve (zero nearby restaurants is ALSO penalized — no proven demand),
 *     and a mandatory "verify offline" checklist so the map is never mistaken
 *     for diligence.
 *
 * Gated like the dashboard: styled client-side login for UX + nginx Basic Auth
 * on /admin/config.json as the real server-side check (see src/auth.js).
 */
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './admin.css';
import { requireAuth } from './auth.js';

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const ADMIN_AUTH = {
  storageKey: 'ion_admin_auth',
  user: 'yamazato1234',
  passHash: '99a64a77a81e1b1860c02f09413a67aeb74ac3a3a8cc039ef9593a5a331ed526',
  dataUrl: 'admin/config.json', // relative → /admin/config.json (nginx-guarded)
  title: 'RESTRICTED — SITE SCOUT',
};

const STORE_KEY = 'bb_scout_v1';

/* ---------- state ---------- */
let cfg;            // gated config.json
let map;            // Leaflet map
let pois = [];      // scanned OSM features: {cat, lat, lng, name, cuisine, kind}
let scannedAt = null;
let candidates = []; // [{id, name, lat, lng, notes, own}]
let selectedId = null;
let arming = false; // "drop a pin" mode
let markers = {};   // candidate id -> L.marker
let groups = {};    // layer name -> L.layerGroup
let ringsGroup;     // radius rings for the selected candidate

const LAYERS = [
  ['competitors', 'Competitors (restaurants · fast food · cafés)', true],
  ['signals', 'Traffic signals', true],
  ['vacancy', 'Possible vacancies (unverified)', true],
  ['parking', 'Parking', false],
  ['transit', 'Transit stops', false],
  ['anchors', 'Anchors (schools · offices)', false],
];

/* ---------- persistence ---------- */
function saveState() {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify({
      candidates,
      view: { c: map.getCenter(), z: map.getZoom() },
      mode: $('#mode-sel').value,
      cuisine: $('#cuisine-q').value,
    }));
  } catch (e) { /* private mode */ }
}
function loadState() {
  try { return JSON.parse(localStorage.getItem(STORE_KEY)) || {}; } catch (e) { return {}; }
}

/* ---------- geometry ---------- */
const R_EARTH = 6371000;
function distM(aLat, aLng, bLat, bLng) {
  const toR = Math.PI / 180;
  const dLat = (bLat - aLat) * toR;
  const dLng = (bLng - aLng) * toR;
  const s = Math.sin(dLat / 2) ** 2 +
    Math.cos(aLat * toR) * Math.cos(bLat * toR) * Math.sin(dLng / 2) ** 2;
  return 2 * R_EARTH * Math.asin(Math.sqrt(s));
}
function bboxKm2(b) {
  const w = distM(b.getSouth(), b.getWest(), b.getSouth(), b.getEast()) / 1000;
  const h = distM(b.getSouth(), b.getWest(), b.getNorth(), b.getWest()) / 1000;
  return w * h;
}

/* ---------- Overpass scan ---------- */
function overpassQuery(b) {
  const bb = `${b.getSouth()},${b.getWest()},${b.getNorth()},${b.getEast()}`;
  return `[out:json][timeout:${cfg.scan.timeout_s}];
(
  nwr["amenity"~"^(restaurant|fast_food|cafe)$"](${bb});
  node["highway"="traffic_signals"](${bb});
  nwr["shop"="vacant"](${bb});
  nwr[~"^disused:(shop|amenity)$"~"."](${bb});
  nwr["amenity"="parking"]["access"!="private"](${bb});
  node["highway"="bus_stop"](${bb});
  node["railway"~"^(station|tram_stop|subway_entrance)$"](${bb});
  nwr["amenity"~"^(school|university|college)$"](${bb});
  nwr["office"](${bb});
);
out center ${cfg.scan.max_results};`;
}

function classify(el) {
  const t = el.tags || {};
  const lat = el.lat ?? el.center?.lat;
  const lng = el.lon ?? el.center?.lon;
  if (lat == null || lng == null) return null;
  const base = { lat, lng, name: t.name || '', cuisine: (t.cuisine || '').toLowerCase() };
  if (/^(restaurant|fast_food|cafe)$/.test(t.amenity || '')) {
    return { ...base, cat: 'competitors', kind: t.amenity };
  }
  if (t.highway === 'traffic_signals') return { ...base, cat: 'signals', kind: 'signal' };
  if (t.shop === 'vacant' || Object.keys(t).some((k) => k.startsWith('disused:'))) {
    return { ...base, cat: 'vacancy', kind: t.shop === 'vacant' ? 'vacant' : 'disused' };
  }
  if (t.amenity === 'parking') return { ...base, cat: 'parking', kind: 'parking' };
  if (t.highway === 'bus_stop' || /^(station|tram_stop|subway_entrance)$/.test(t.railway || '')) {
    return { ...base, cat: 'transit', kind: t.highway === 'bus_stop' ? 'bus' : t.railway };
  }
  if (/^(school|university|college)$/.test(t.amenity || '')) return { ...base, cat: 'anchors', kind: t.amenity };
  if (t.office) return { ...base, cat: 'anchors', kind: 'office' };
  return null;
}

async function scan() {
  const b = map.getBounds();
  const km2 = bboxKm2(b);
  const status = $('#scan-status');
  if (km2 > cfg.scan.max_bbox_km2) {
    status.textContent = `Area is ${km2.toFixed(0)} km² — zoom in to ≤ ${cfg.scan.max_bbox_km2} km² (a district, not a city).`;
    status.classList.add('warn');
    return;
  }
  status.classList.remove('warn');
  status.textContent = 'Scanning OpenStreetMap…';
  $('#scan-btn').disabled = true;

  let json = null;
  let lastErr = null;
  for (const ep of cfg.endpoints.overpass) {
    try {
      const res = await fetch(ep, { method: 'POST', body: 'data=' + encodeURIComponent(overpassQuery(b)) });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      json = await res.json();
      break;
    } catch (e) { lastErr = e; }
  }
  $('#scan-btn').disabled = false;
  if (!json) {
    status.textContent = `Scan failed (${lastErr}). Overpass may be busy — try again in a minute.`;
    status.classList.add('warn');
    return;
  }

  pois = (json.elements || []).map(classify).filter(Boolean);
  scannedAt = Date.now();
  renderPois();
  refreshScores();

  const n = (cat) => pois.filter((p) => p.cat === cat).length;
  const truncated = (json.elements || []).length >= cfg.scan.max_results ? ' (truncated — zoom in for full coverage)' : '';
  status.textContent =
    `Loaded ${n('competitors')} food · ${n('signals')} signals · ${n('vacancy')} vacancies · ` +
    `${n('parking')} parking · ${n('transit')} transit · ${n('anchors')} anchors${truncated}`;
  if (pois.length < cfg.scan.sparse_warn_pois) {
    status.textContent += ' — sparse OSM coverage here: low confidence, not necessarily a sparse market.';
    status.classList.add('warn');
  }
}

/* ---------- POI rendering ---------- */
const POI_STYLE = {
  restaurant: { color: '#d62d20', r: 6 },
  fast_food: { color: '#ff7a00', r: 5 },
  cafe: { color: '#b8860b', r: 5 },
};
function divIcon(emoji, cls) {
  return L.divIcon({ className: `poi-emoji ${cls}`, html: emoji, iconSize: [22, 22], iconAnchor: [11, 11] });
}

function renderPois() {
  Object.values(groups).forEach((g) => g.clearLayers());
  for (const p of pois) {
    let m;
    if (p.cat === 'competitors') {
      const st = POI_STYLE[p.kind] || POI_STYLE.restaurant;
      m = L.circleMarker([p.lat, p.lng], {
        radius: st.r, color: st.color, weight: 1.5, fillColor: st.color, fillOpacity: 0.35,
      }).bindPopup(
        `<b>${esc(p.name) || '(unnamed)'}</b><br>${esc(p.kind)}${p.cuisine ? ' · ' + esc(p.cuisine) : ''}`
      );
    } else if (p.cat === 'signals') {
      m = L.marker([p.lat, p.lng], { icon: divIcon('🚦', 'poi-signal'), interactive: false, keyboard: false });
    } else if (p.cat === 'vacancy') {
      m = L.marker([p.lat, p.lng], { icon: divIcon('🏚', 'poi-vacancy') })
        .bindPopup(`<b>Possible vacancy</b> (${esc(p.kind)})<br>${esc(p.name) || 'unnamed'}<br><i>OSM tag — unverified & often stale. A lead, not inventory.</i>`);
    } else if (p.cat === 'parking') {
      m = L.marker([p.lat, p.lng], { icon: divIcon('🅿️', 'poi-parking') })
        .bindPopup('Parking (may be reserved for another tenant — verify in the lease)');
    } else if (p.cat === 'transit') {
      m = L.marker([p.lat, p.lng], { icon: divIcon('🚏', 'poi-transit') })
        .bindPopup(`Transit: ${esc(p.kind)} ${esc(p.name)}`);
    } else {
      m = L.marker([p.lat, p.lng], { icon: divIcon('🏢', 'poi-anchor') })
        .bindPopup(`Anchor: ${esc(p.kind)} ${esc(p.name)}`);
    }
    groups[p.cat].addLayer(m);
  }
}

/* ---------- scoring (panel-derived) ---------- */
function near(cat, lat, lng, r, filter) {
  return pois.filter((p) => p.cat === cat && (!filter || filter(p)) && distM(lat, lng, p.lat, p.lng) <= r);
}
function nearestM(cat, lat, lng) {
  let best = Infinity;
  for (const p of pois) {
    if (p.cat !== cat) continue;
    const d = distM(lat, lng, p.lat, p.lng);
    if (d < best) best = d;
  }
  return best;
}

/* Non-linear competitor curve: zero nearby = no proven demand (55), 1–3 = sweet
   spot (100), then declining to 0 at 12+. Shaped by the operator panel. */
function competitorScore(count) {
  if (count === 0) return 55;
  if (count <= 3) return 100;
  if (count >= 12) return 0;
  return Math.round(100 * (12 - count) / 9);
}

function scoreCandidate(c) {
  if (!pois.length) return null;
  const mode = cfg.modes[$('#mode-sel').value] || cfg.modes[cfg.default_mode];
  const rr = cfg.radii_m;
  const cuisine = $('#cuisine-q').value.trim().toLowerCase();

  const allFood = near('competitors', c.lat, c.lng, mode.competitor_ring_m);
  const direct = cuisine ? allFood.filter((p) => p.cuisine.includes(cuisine)) : allFood;
  const cluster = near('competitors', c.lat, c.lng, rr.cluster);
  const anchors = near('anchors', c.lat, c.lng, rr.anchors);
  const transit = near('transit', c.lat, c.lng, rr.transit);
  const dSignal = nearestM('signals', c.lat, c.lng);
  const dParking = nearestM('parking', c.lat, c.lng);
  const ownUnits = candidates.filter((o) => o.own && o.id !== c.id);
  const dOwn = ownUnits.length
    ? Math.min(...ownUnits.map((o) => distM(c.lat, c.lng, o.lat, o.lng)))
    : null;

  /* each criterion: {score 0-100, detail, verify?} — road_class is never
     auto-scored (read it off the base map); cannibal drops out with no own units */
  const parts = {
    competitors: {
      score: competitorScore(direct.length),
      detail: cuisine
        ? `${direct.length} "${cuisine}" · ${allFood.length} all food ≤${mode.competitor_ring_m}m`
        : `${direct.length} food spots ≤${mode.competitor_ring_m}m`,
    },
    cluster: {
      score: Math.min(100, Math.round((cluster.length / 12) * 100)),
      detail: `${cluster.length} restaurants/cafés ≤${rr.cluster}m`,
    },
    anchors: {
      score: Math.min(100, Math.round((anchors.length / 6) * 100)),
      detail: `${anchors.length} schools/offices ≤${rr.anchors}m`,
    },
    transit: {
      score: Math.min(100, Math.round((transit.length / 4) * 100)),
      detail: `${transit.length} stops ≤${rr.transit}m`,
    },
    signal: {
      score: dSignal <= rr.signal_best ? 100
        : dSignal >= rr.signal_max ? 0
        : Math.round(100 * (rr.signal_max - dSignal) / (rr.signal_max - rr.signal_best)),
      detail: isFinite(dSignal) ? `nearest signal ${Math.round(dSignal)}m` : 'no signal in scan',
    },
    parking: {
      score: dParking <= rr.parking_best ? 100 : dParking <= rr.parking_ok ? 60 : 0,
      detail: isFinite(dParking) ? `nearest lot ${Math.round(dParking)}m` : 'no lot in scan',
    },
  };
  if (dOwn != null) {
    parts.cannibal = {
      score: dOwn <= rr.cannibal_min ? 0
        : dOwn >= rr.cannibal_ok ? 100
        : Math.round(100 * (dOwn - rr.cannibal_min) / (rr.cannibal_ok - rr.cannibal_min)),
      detail: `own unit ${Math.round(dOwn)}m away${dOwn <= rr.cannibal_min ? ' — CANNIBALIZATION RISK' : ''}`,
    };
  }

  let wsum = 0;
  let total = 0;
  for (const [k, part] of Object.entries(parts)) {
    const w = mode.weights[k] || 0;
    wsum += w;
    total += w * part.score;
  }
  return { total: wsum ? Math.round(total / wsum) : 0, parts, mode };
}

/* ---------- candidates ---------- */
const CAND_LABELS = {
  competitors: 'Direct competitors',
  cluster: 'Cluster vitality',
  anchors: 'Demand anchors',
  transit: 'Transit',
  signal: 'Signalized access',
  parking: 'Parking',
  cannibal: 'Cannibalization',
};

function addCandidate(latlng) {
  const c = {
    id: 'c' + Date.now().toString(36),
    name: `Site ${candidates.length + 1}`,
    lat: +latlng.lat.toFixed(6),
    lng: +latlng.lng.toFixed(6),
    notes: '',
    own: false,
  };
  candidates.push(c);
  addCandMarker(c);
  selectCandidate(c.id);
  saveState();
  renderCandList();
}

function addCandMarker(c) {
  const m = L.marker([c.lat, c.lng], {
    draggable: true,
    icon: L.divIcon({ className: 'cand-pin', html: '📍', iconSize: [30, 30], iconAnchor: [15, 28] }),
  }).addTo(map);
  m.on('click', () => selectCandidate(c.id));
  m.on('dragend', () => {
    const ll = m.getLatLng();
    c.lat = +ll.lat.toFixed(6);
    c.lng = +ll.lng.toFixed(6);
    saveState();
    refreshScores();
  });
  markers[c.id] = m;
}

function removeCandidate(id) {
  candidates = candidates.filter((c) => c.id !== id);
  markers[id]?.remove();
  delete markers[id];
  if (selectedId === id) { selectedId = null; $('#scorecard').hidden = true; ringsGroup.clearLayers(); }
  saveState();
  renderCandList();
  refreshScores();
}

function selectCandidate(id) {
  selectedId = id;
  const c = candidates.find((x) => x.id === id);
  if (!c) return;
  drawRings(c);
  renderScorecard(c);
  renderCandList();
}

function drawRings(c) {
  ringsGroup.clearLayers();
  const mode = cfg.modes[$('#mode-sel').value] || cfg.modes[cfg.default_mode];
  for (const r of cfg.rings_m) {
    ringsGroup.addLayer(L.circle([c.lat, c.lng], {
      radius: r, color: '#8e8e93', weight: 1, fill: false, dashArray: '2 5', interactive: false,
    }));
  }
  ringsGroup.addLayer(L.circle([c.lat, c.lng], {
    radius: mode.competitor_ring_m, color: '#0071e3', weight: 1.5, fill: false, dashArray: '6 4', interactive: false,
  }));
}

function scoreBadge(s) {
  if (s == null) return '<span class="sc-badge sc-none">—</span>';
  const cls = s >= 70 ? 'sc-good' : s >= 45 ? 'sc-mid' : 'sc-low';
  return `<span class="sc-badge ${cls}">${s}</span>`;
}

function renderCandList() {
  const list = $('#cand-list');
  if (!candidates.length) {
    list.innerHTML = '<li class="ss-status dim">No pins yet — arm the button above, then click the map (or a vacancy marker location from a broker sheet).</li>';
    return;
  }
  const scored = candidates.map((c) => ({ c, s: scoreCandidate(c) }));
  scored.sort((a, b) => (b.s?.total ?? -1) - (a.s?.total ?? -1));
  list.innerHTML = scored.map(({ c, s }) => `
    <li class="${c.id === selectedId ? 'sel' : ''}" data-id="${c.id}">
      ${scoreBadge(s?.total ?? null)}
      <span class="cand-name">${esc(c.name)}${c.own ? ' <i class="own-tag">OWN UNIT</i>' : ''}</span>
    </li>`).join('');
  list.querySelectorAll('li[data-id]').forEach((li) => {
    li.addEventListener('click', () => {
      const c = candidates.find((x) => x.id === li.dataset.id);
      map.panTo([c.lat, c.lng]);
      selectCandidate(c.id);
    });
  });
}

function renderScorecard(c) {
  const card = $('#scorecard');
  const s = scoreCandidate(c);
  const rows = s ? Object.entries(s.parts).map(([k, p]) => `
      <div class="sc-row">
        <span class="sc-k">${CAND_LABELS[k]}</span>
        <span class="sc-bar"><i style="--w:${p.score}%"></i></span>
        <span class="sc-v">${p.score}</span>
        <span class="sc-d dim">${esc(p.detail)}</span>
      </div>`).join('')
    : '<p class="ss-status warn">No scan data yet — “Scan this area” first, then scores compute automatically.</p>';

  card.hidden = false;
  card.innerHTML = `
    <header class="sc-head">
      <input id="sc-name" class="sc-name" value="${esc(c.name)}" />
      ${scoreBadge(s?.total ?? null)}
      <button id="sc-close" class="sc-x" aria-label="Close">✕</button>
    </header>
    <p class="sc-sub dim">${c.lat}, ${c.lng} · ${s ? esc(s.mode.label) : ''} <em>${s ? esc(s.mode.blurb) : ''}</em></p>
    ${rows}
    <div class="sc-row"><span class="sc-k">Frontage / road class</span><span class="sc-d dim">not auto-scored — read it off the base map</span></div>
    <label class="sc-own"><input type="checkbox" id="sc-own" ${c.own ? 'checked' : ''}/> This is one of MY existing units (enables cannibalization checks)</label>
    <textarea id="sc-notes" class="sc-notes" placeholder="Notes (broker, rent quoted, visit impressions…)">${esc(c.notes)}</textarea>
    <details class="sc-verify"><summary>VERIFY OFFLINE before LOI (${cfg.verify_offline.length})</summary>
      <ul>${cfg.verify_offline.map((v) => `<li>${esc(v)}</li>`).join('')}</ul>
    </details>
    <div class="ss-row">
      <button id="sc-del" class="ss-btn ss-btn--danger">Delete pin</button>
    </div>
    <p class="sc-disc dim">${esc(cfg.disclaimer)}</p>`;

  $('#sc-close').addEventListener('click', () => { card.hidden = true; ringsGroup.clearLayers(); selectedId = null; renderCandList(); });
  $('#sc-name').addEventListener('change', (e) => { c.name = e.target.value.trim() || c.name; saveState(); renderCandList(); });
  $('#sc-notes').addEventListener('change', (e) => { c.notes = e.target.value; saveState(); });
  $('#sc-own').addEventListener('change', (e) => { c.own = e.target.checked; saveState(); refreshScores(); });
  $('#sc-del').addEventListener('click', () => removeCandidate(c.id));
}

function refreshScores() {
  renderCandList();
  if (selectedId) {
    const c = candidates.find((x) => x.id === selectedId);
    if (c) { renderScorecard(c); drawRings(c); }
  }
}

/* ---------- geocoding (Nominatim) ---------- */
async function geocode(q) {
  const url = `${cfg.endpoints.nominatim}?format=json&limit=1&q=${encodeURIComponent(q)}`;
  const res = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!res.ok) throw new Error('geocode ' + res.status);
  const hits = await res.json();
  return hits[0] || null;
}

/* ---------- exports ---------- */
function download(name, mime, text) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type: mime }));
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

function exportCSV() {
  const head = ['name', 'lat', 'lng', 'own_unit', 'score', 'notes', 'detail'];
  const lines = [head.join(',')];
  for (const c of candidates) {
    const s = scoreCandidate(c);
    const detail = s ? Object.entries(s.parts).map(([k, p]) => `${CAND_LABELS[k]}: ${p.score} (${p.detail})`).join(' | ') : 'no scan';
    const cell = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    lines.push([cell(c.name), c.lat, c.lng, c.own ? 'yes' : 'no', s?.total ?? '', cell(c.notes), cell(detail)].join(','));
  }
  lines.push(`# ${cfg.disclaimer}`);
  download('site-scout-candidates.csv', 'text/csv', lines.join('\n'));
}

function exportGeoJSON() {
  const fc = {
    type: 'FeatureCollection',
    note: cfg.disclaimer,
    features: candidates.map((c) => {
      const s = scoreCandidate(c);
      return {
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [c.lng, c.lat] },
        properties: {
          name: c.name, own_unit: c.own, notes: c.notes, score: s?.total ?? null,
          breakdown: s ? Object.fromEntries(Object.entries(s.parts).map(([k, p]) => [k, { score: p.score, detail: p.detail }])) : null,
        },
      };
    }),
  };
  download('site-scout-candidates.geojson', 'application/geo+json', JSON.stringify(fc, null, 2));
}

/* ---------- boot ---------- */
function initUI(saved) {
  /* mode selector */
  const sel = $('#mode-sel');
  sel.innerHTML = Object.entries(cfg.modes)
    .map(([k, m]) => `<option value="${k}">${esc(m.label)}</option>`).join('');
  sel.value = saved.mode && cfg.modes[saved.mode] ? saved.mode : cfg.default_mode;
  const blurb = () => { $('#mode-blurb').textContent = cfg.modes[sel.value].blurb; };
  sel.addEventListener('change', () => { blurb(); saveState(); refreshScores(); });
  blurb();

  /* layer toggles */
  $('#layer-list').innerHTML = LAYERS.map(([k, label, on]) => `
    <li><label><input type="checkbox" data-layer="${k}" ${on ? 'checked' : ''}/> ${label}</label></li>`).join('');
  document.querySelectorAll('[data-layer]').forEach((cb) => {
    cb.addEventListener('change', () => {
      const g = groups[cb.dataset.layer];
      cb.checked ? g.addTo(map) : g.remove();
    });
  });

  /* cuisine filter */
  if (saved.cuisine) $('#cuisine-q').value = saved.cuisine;
  let cuisineT;
  $('#cuisine-q').addEventListener('input', () => {
    clearTimeout(cuisineT);
    cuisineT = setTimeout(() => { saveState(); refreshScores(); }, 350);
  });

  /* scan + geocode */
  $('#scan-btn').addEventListener('click', scan);
  $('#geo-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const q = $('#geo-q').value.trim();
    if (!q) return;
    const status = $('#scan-status');
    status.textContent = 'Searching…';
    try {
      const hit = await geocode(q);
      if (!hit) { status.textContent = 'No match — try a more specific place.'; return; }
      map.setView([+hit.lat, +hit.lon], 15);
      status.textContent = `→ ${hit.display_name.split(',').slice(0, 3).join(',')} — now scan.`;
    } catch (err) {
      status.textContent = 'Geocoding unreachable — pan manually.';
      status.classList.add('warn');
    }
  });

  /* pin-drop arming */
  const pinBtn = $('#pin-btn');
  pinBtn.addEventListener('click', () => {
    arming = !arming;
    pinBtn.setAttribute('aria-pressed', String(arming));
    pinBtn.textContent = arming ? '⌖ Click the map to place…' : '＋ Drop a candidate pin';
    map.getContainer().classList.toggle('crosshair', arming);
  });
  map.on('click', (e) => {
    if (!arming) return;
    arming = false;
    pinBtn.setAttribute('aria-pressed', 'false');
    pinBtn.textContent = '＋ Drop a candidate pin';
    map.getContainer().classList.remove('crosshair');
    addCandidate(e.latlng);
  });

  /* exports */
  $('#exp-csv').addEventListener('click', exportCSV);
  $('#exp-geo').addEventListener('click', exportGeoJSON);

  map.on('moveend', saveState);
}

requireAuth(ADMIN_AUTH).then((config) => {
  cfg = config;
  const saved = loadState();
  $('#scout-main').hidden = false;

  map = L.map('map', { zoomControl: true });
  const v = saved.view;
  map.setView(v?.c ? [v.c.lat, v.c.lng] : cfg.map.center, v?.z || cfg.map.zoom);
  L.tileLayer(cfg.map.tiles, { maxZoom: 19, attribution: cfg.map.attribution }).addTo(map);

  for (const [k, , on] of LAYERS) {
    groups[k] = L.layerGroup();
    if (on) groups[k].addTo(map);
  }
  ringsGroup = L.layerGroup().addTo(map);

  candidates = saved.candidates || [];
  candidates.forEach(addCandMarker);

  initUI(saved);
  renderCandList();
  setTimeout(() => map.invalidateSize(), 50);
});
