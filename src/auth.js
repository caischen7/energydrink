/*
 * Access gate (Bogus Banana // RESTRICTED) — shared by the Market Intel
 * dashboard and the Admin console.
 *
 * Two layers, one styled login:
 *   1. Client-side check (instant UX + gates local dev where there's no server).
 *   2. REAL protection: the page's data (a JSON under a guarded path) is served
 *      behind nginx HTTP Basic Auth on the deployed site. The form fetches it
 *      with the entered credentials in an Authorization header, so without
 *      valid credentials the data is never sent — bypassing the JS check
 *      (devtools) gets you an empty shell, not the data.
 *
 * Credentials live in `.htpasswd` / `.htpasswd-admin` (server, hashed). The
 * client-side check uses a SHA-256 of the password so the plaintext isn't in
 * the bundle. To change them, update BOTH the htpasswd file and the passHash
 * (see docs/CREDENTIALS.md).
 */

/* per-surface defaults — the dashboard config, kept as requireAuth()'s default */
const DASHBOARD = {
  storageKey: 'ion_dash_auth', // sessionStorage: base64(user:pass) for the session
  user: 'energydrinks',
  passHash: '51399badaf99cab1e1921de22874aa456d30399d2bf8d9757be42bcaf7a83763',
  dataUrl: 'data/dashboard.json', // relative → /data/dashboard.json (nginx-guarded)
  title: 'RESTRICTED — MARKET INTEL',
};

async function sha256(s) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function fetchData(cfg, token) {
  const res = await fetch(cfg.dataUrl, {
    headers: { Authorization: 'Basic ' + token },
    cache: 'no-store',
  });
  if (res.status === 401 || res.status === 403) return null; // server rejected
  if (!res.ok) throw new Error('data ' + res.status);
  return res.json();
}

function overlay(cfg) {
  const el = document.createElement('div');
  el.className = 'gate';
  el.innerHTML = `
    <form class="gate-card mono" autocomplete="off" novalidate>
      <div class="gate-brand"><img class="gate-mark" src="/mascot.svg" alt="" /><span>Bogus Banana</span></div>
      <div class="gate-head"><span class="volt">·</span> ${cfg.title}</div>
      <label class="gate-label" for="gate-user"><span class="volt">&gt;</span> OPERATOR_ID</label>
      <input id="gate-user" type="text" spellcheck="false" autocapitalize="off" placeholder="username" />
      <label class="gate-label" for="gate-pass"><span class="volt">&gt;</span> ACCESS_KEY</label>
      <input id="gate-pass" type="password" placeholder="password" />
      <button type="submit">AUTHENTICATE ↵</button>
      <p class="gate-out" role="status"></p>
    </form>`;
  return el;
}

function showForm(cfg, resolve) {
  document.body.classList.add('gated');
  const el = overlay(cfg);
  document.body.appendChild(el);
  const form = el.querySelector('form');
  const out = el.querySelector('.gate-out');
  const user = el.querySelector('#gate-user');
  const pass = el.querySelector('#gate-pass');
  user.focus();

  const unlock = (data) => {
    el.classList.add('out');
    document.body.classList.remove('gated');
    setTimeout(() => {
      el.remove();
      resolve(data);
    }, 450);
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    out.textContent = '> VERIFYING…';
    const u = user.value.trim();
    const p = pass.value;
    let okLocal = false;
    try {
      okLocal = u === cfg.user && (await sha256(p)) === cfg.passHash;
    } catch (err) {
      out.textContent = '> ERR :: SECURE CONTEXT REQUIRED (USE HTTPS OR LOCALHOST)';
      return;
    }
    if (!okLocal) {
      out.textContent = '> ACCESS DENIED :: INVALID CREDENTIALS';
      pass.value = '';
      pass.focus();
      return;
    }
    const token = btoa(`${u}:${p}`);
    let data;
    try {
      data = await fetchData(cfg, token);
    } catch (err) {
      out.textContent = '> ERR :: DATA FEED UNREACHABLE';
      return;
    }
    if (!data) {
      out.textContent = '> ACCESS DENIED :: SERVER REJECTED CREDENTIALS';
      pass.value = '';
      return;
    }
    try {
      sessionStorage.setItem(cfg.storageKey, token);
    } catch (e2) {
      /* private mode — just won't persist across reloads */
    }
    unlock(data);
  });
}

/* Resolves with the gated page's data once the visitor is authenticated.
   No-args call = the Market Intel dashboard (back-compat); pass a config
   object ({storageKey, user, passHash, dataUrl, title}) for other surfaces. */
export function requireAuth(config) {
  const cfg = { ...DASHBOARD, ...(config || {}) };
  return new Promise((resolve) => {
    const saved = sessionStorage.getItem(cfg.storageKey);
    if (saved) {
      fetchData(cfg, saved)
        .then((d) => (d ? resolve(d) : (sessionStorage.removeItem(cfg.storageKey), showForm(cfg, resolve))))
        .catch(() => showForm(cfg, resolve));
      return;
    }
    showForm(cfg, resolve);
  });
}
