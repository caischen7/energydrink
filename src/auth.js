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
  user: 'energydrink',
  passHash: 'fb4ae640687c24b5d2a8e57d24ce5c5f3a5cd9c3db3cf52edd280241e3b72e37',
  dataUrl: 'data/dashboard.json', // relative → /data/dashboard.json (nginx-guarded)
  title: 'RESTRICTED — MARKET INTEL',
};

async function sha256(s) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

/* token === null sends NO Authorization header, which is the point: for a
   same-origin request the browser attaches any Basic credentials it already
   holds for this realm by itself. */
async function fetchData(cfg, token) {
  const res = await fetch(cfg.dataUrl, {
    headers: token ? { Authorization: 'Basic ' + token } : {},
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
      <label class="gate-label" for="gate-user"><span class="volt">&gt;</span> USERNAME</label>
      <input id="gate-user" type="text" spellcheck="false" autocapitalize="off" placeholder="username" />
      <label class="gate-label" for="gate-pass"><span class="volt">&gt;</span> PASSWORD</label>
      <input id="gate-pass" type="password" placeholder="password" />
      <button type="submit">SIGN IN ↵</button>
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

/* Fetch a SECOND gated file after requireAuth has already resolved, reusing the
   session token rather than prompting again. The explorer page needs both
   dashboard.json and flavor_explorer.json, and nginx guards all of /data/.
   Returns null if the token is missing or the server rejects it, so callers can
   degrade instead of throwing. */
export async function fetchGated(url, storageKey = DASHBOARD.storageKey) {
  const token = sessionStorage.getItem(storageKey);
  if (!token) return null;
  try {
    return await fetchData({ dataUrl: url }, token);
  } catch {
    return null;
  }
}

/* Resolves with the gated page's data once the visitor is authenticated.
   No-args call = the Market Intel dashboard (back-compat); pass a config
   object ({storageKey, user, passHash, dataUrl, title}) for other surfaces. */
export function requireAuth(config) {
  const cfg = { ...DASHBOARD, ...(config || {}) };
  return new Promise((resolve) => {
    const saved = sessionStorage.getItem(cfg.storageKey);
    const prompt = () => showForm(cfg, resolve);
    const withSaved = () =>
      saved
        ? fetchData(cfg, saved)
            .then((d) => (d ? resolve(d) : (sessionStorage.removeItem(cfg.storageKey), prompt())))
            .catch(prompt)
        : prompt();

    /* Try with NO credentials of our own first.
       On the deployed site the analysis pages are themselves behind the same
       Basic Auth realm as their data, so by the time this runs the browser has
       already authenticated and re-sends those credentials automatically — the
       visitor sees one native prompt instead of a native prompt followed by
       this styled form. Locally (vite preview, no nginx) there is no server
       auth and this also succeeds, which is what the old sessionStorage branch
       was really for. Anything else falls through to the form, so the admin
       console — whose page is not HTML-gated — behaves exactly as before. */
    fetchData(cfg, null)
      .then((d) => (d ? resolve(d) : withSaved()))
      .catch(withSaved);
  });
}
