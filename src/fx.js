/*
 * DOM choreography: split-word headline reveals, staggered fade-ups,
 * count-up stats, marquee ticker, custom cursor, section tracking and
 * the edition-row <-> 3D colorway sync. No animation libraries.
 */

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

/* ---------- split headlines into per-word reveal spans ---------- */
function splitWords() {
  $$('[data-split]').forEach((el) => {
    let i = 0;
    const walk = (node) => {
      [...node.childNodes].forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          const frag = document.createDocumentFragment();
          child.textContent.split(/(\s+)/).forEach((part) => {
            if (!part) return;
            if (/^\s+$/.test(part)) {
              frag.appendChild(document.createTextNode(' '));
              return;
            }
            const w = document.createElement('span');
            w.className = 'w';
            const wi = document.createElement('span');
            wi.className = 'wi';
            wi.style.setProperty('--i', i++);
            wi.textContent = part;
            w.appendChild(wi);
            frag.appendChild(w);
          });
          node.replaceChild(frag, child);
        }
      });
    };
    walk(el);
  });
}

/* ---------- scroll-triggered reveals ---------- */
function observeReveals() {
  /* stagger siblings: delay indexed within each parent container */
  const groups = new Map();
  $$('.reveal').forEach((el) => {
    const parent = el.parentElement;
    const n = groups.get(parent) || 0;
    el.style.setProperty('--d', `${n * 90}ms`);
    groups.set(parent, n + 1);
  });

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          if (entry.target.matches('.spec-card')) countUp(entry.target);
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.18, rootMargin: '0px 0px -8% 0px' }
  );

  $$('.reveal, [data-split], .hbar').forEach((el) => io.observe(el));
}

/* ---------- count-up numbers ---------- */
function countUp(card) {
  const b = $('[data-count]', card);
  if (!b || b.dataset.done) return;
  b.dataset.done = '1';
  const target = parseFloat(b.dataset.count);
  const decimals = parseInt(b.dataset.decimals || '0', 10);
  const pad = parseInt(b.dataset.pad || '0', 10);
  const group = b.dataset.group === 'true';
  const dur = 1300;
  const t0 = performance.now();

  const fmt = (v) => {
    let s = v.toFixed(decimals);
    if (pad) s = s.padStart(pad, '0');
    if (group) s = Number(s).toLocaleString('en-US');
    return s;
  };

  const step = (now) => {
    const t = Math.min(1, (now - t0) / dur);
    const eased = 1 - Math.pow(1 - t, 4);
    b.textContent = fmt(target * eased);
    if (t < 1) requestAnimationFrame(step);
    else b.textContent = fmt(target);
  };
  requestAnimationFrame(step);
}

/* ---------- ticker: clone runs until the track loops seamlessly ---------- */
function buildTicker() {
  const track = $('#ticker-track');
  if (!track) return;
  const run = $('.ticker-run', track);
  const runW = run.offsetWidth || 600;
  const copies = Math.max(2, 2 * Math.ceil(window.innerWidth / runW));
  for (let i = 1; i < copies; i++) track.appendChild(run.cloneNode(true));
  track.style.animationDuration = `${((runW * copies) / 2 / 90).toFixed(2)}s`;
}

/* ---------- custom cursor ---------- */
function initCursor() {
  if (!window.matchMedia('(pointer: fine)').matches) return;
  const cur = $('#cursor');
  let x = -100, y = -100, cx = -100, cy = -100;

  window.addEventListener('pointermove', (e) => {
    x = e.clientX;
    y = e.clientY;
    document.body.classList.add('cursor-on');
  });

  document.addEventListener('mouseover', (e) => {
    document.body.classList.toggle('cursor-hover', !!e.target.closest('[data-hover]'));
  });

  const loop = () => {
    cx += (x - cx) * 0.22;
    cy += (y - cy) * 0.22;
    cur.style.transform = `translate(${cx.toFixed(1)}px, ${cy.toFixed(1)}px)`;
    requestAnimationFrame(loop);
  };
  loop();
}

/* ---------- body[data-section] tracker ---------- */
const SECTION_IDS = ['hero', 'manifesto', 'specs', 'drop', 'protocol', 'join'];

function trackSections() {
  let offsets = [];
  const measure = () => {
    offsets = SECTION_IDS.map((id) => {
      const el = document.getElementById(id);
      return el ? el.offsetTop + el.offsetHeight / 2 : 0;
    });
  };
  measure();
  window.addEventListener('resize', measure);
  window.addEventListener('load', measure);
  document.fonts?.ready.then(measure);

  const update = () => {
    const mid = window.scrollY + window.innerHeight / 2;
    let best = 0;
    offsets.forEach((o, i) => {
      if (Math.abs(o - mid) < Math.abs(offsets[best] - mid)) best = i;
    });
    const id = SECTION_IDS[best];
    if (document.body.dataset.section !== id) document.body.dataset.section = id;
  };
  window.addEventListener('scroll', update, { passive: true });
  update();
}

/* ---------- editions <-> 3D colorway ---------- */
const EDITION_HUD = {
  volt: 'BB-01 · ORIGINAL',
  void: 'BB-02 · MIDNIGHT BERRY',
  glacier: 'BB-03 · FROZEN BANANA',
};

function initEditions(setColorway) {
  const rows = $$('.edition');
  const drop = $('#drop');
  let hovered = null;

  const fromScroll = () => {
    if (hovered) return;
    const rect = drop.getBoundingClientRect();
    if (rect.bottom < 0) return; // below: keep last colorway (stateful)
    if (rect.top > window.innerHeight * 0.7) {
      setColorway('volt'); // back above the drop: reset to genesis
      return;
    }
    const mid = window.innerHeight / 2;
    let best = null;
    let bestD = Infinity;
    rows.forEach((row) => {
      const r = row.getBoundingClientRect();
      const d = Math.abs(r.top + r.height / 2 - mid);
      if (d < bestD) { bestD = d; best = row; }
    });
    if (best) setColorway(best.dataset.colorway);
  };

  rows.forEach((row) => {
    const pick = () => {
      hovered = row;
      setColorway(row.dataset.colorway);
    };
    row.addEventListener('pointerenter', pick);
    row.addEventListener('focus', pick);
    row.addEventListener('click', pick);
    row.addEventListener('pointerleave', () => { hovered = null; });
    row.addEventListener('blur', () => { hovered = null; });
  });

  window.addEventListener('scroll', fromScroll, { passive: true });

  /* reflect active colorway in the rows + hero HUD */
  return (name) => {
    rows.forEach((r) => r.classList.toggle('active', r.dataset.colorway === name));
    const hud = $('#hud-edition');
    if (hud && EDITION_HUD[name]) hud.textContent = EDITION_HUD[name];
  };
}

/* ---------- header readout: fps + protocol clock (+60y) ---------- */
function initReadout() {
  const el = $('#sys-readout');
  if (!el) return { setFps: () => {} };
  let fps = '··';
  const render = () => {
    const d = new Date();
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    const ss = String(d.getSeconds()).padStart(2, '0');
    el.textContent = `SYS ${fps}FPS · ${d.getFullYear() + 60}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')} ${hh}:${mm}:${ss}`;
  };
  setInterval(render, 1000);
  render();
  return { setFps: (v) => { fps = v; } };
}

/* ---------- terminal form: real capture ----------
 * Persists signups to localStorage (deduped) with UTM + referrer, and — if a
 * backend is configured at build time via VITE_WAITLIST_ENDPOINT — POSTs the
 * record there too. No address is discarded; wiring a real ESP is one env var. */
const WAITLIST_KEY = 'ion_waitlist';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function readWaitlist() {
  try {
    return JSON.parse(localStorage.getItem(WAITLIST_KEY)) || [];
  } catch (e) {
    return [];
  }
}

/* deterministic per-email "node id" — stable across submits, not a fresh fake each time */
function nodeId(email) {
  let h = 2166136261;
  for (let i = 0; i < email.length; i++) {
    h ^= email.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return String(((h >>> 0) % 9000) + 1000).padStart(5, '0');
}

function captureUtm() {
  const p = new URLSearchParams(location.search);
  const utm = {};
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach((k) => {
    if (p.get(k)) utm[k] = p.get(k);
  });
  return utm;
}

function initForm() {
  const form = $('#join-form');
  const out = $('#term-out');
  if (!form) return;
  const input = $('#join-email');
  const btn = $('button', form);

  const lock = () => {
    input.disabled = true;
    btn.textContent = 'MINTED ✓';
    btn.disabled = true;
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = input.value.trim().toLowerCase();
    if (!EMAIL_RE.test(email)) {
      out.textContent = '> ERR :: INVALID ADDRESS FORMAT — RETRY';
      input.focus();
      return;
    }
    const list = readWaitlist();
    const slot = nodeId(email);
    if (list.some((r) => r.email === email)) {
      out.textContent = `> ALREADY ON THE LIST :: #${slot} ✓`;
      lock();
      return;
    }

    const record = {
      email,
      slot,
      ts: new Date().toISOString(),
      utm: captureUtm(),
      ref: document.referrer || null,
    };
    list.push(record);
    try {
      localStorage.setItem(WAITLIST_KEY, JSON.stringify(list));
    } catch (e) {
      /* private mode — still forward below if configured */
    }

    const endpoint = import.meta.env.VITE_WAITLIST_ENDPOINT;
    if (endpoint) {
      out.textContent = '> TRANSMITTING…';
      try {
        await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(record),
        });
      } catch (err) {
        console.warn('[ION] waitlist POST failed; address stored locally.', err);
      }
    }
    out.textContent = `> YOU'RE ON THE LIST :: #${slot} :: WELCOME TO THE BUNCH ✓`;
    lock();
  });
}

export function initFx(scene) {
  splitWords();
  observeReveals();
  buildTicker();
  initCursor();
  trackSections();
  initForm();

  const readout = initReadout();
  const setColorway = scene ? scene.setColorway : () => {};
  const reflect = initEditions(setColorway);

  if (scene) {
    scene.onColorway(reflect);
    scene.onFps(readout.setFps);
  }
  reflect('volt');
}
