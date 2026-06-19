/*
 * Dashboard access gate (Bogus Banana // RESTRICTED).
 *
 * Two layers, one styled login:
 *   1. Client-side check (instant UX + gates local dev where there's no server).
 *   2. REAL protection: the dashboard's data (public/data/dashboard.json) is
 *      served behind nginx HTTP Basic Auth on the deployed site. The form fetches
 *      it with the entered credentials in an Authorization header, so without
 *      valid credentials the licensed market data is never sent — bypassing the
 *      JS check (devtools) gets you an empty shell, not the data.
 *
 * Credentials live in `.htpasswd` (server, hashed). The client-side check uses a
 * SHA-256 of the password so the plaintext isn't in the bundle. To change them,
 * update BOTH: `.htpasswd` (htpasswd/openssl) and PASS_HASH below.
 */
const KEY = 'ion_dash_auth'; // sessionStorage: base64(user:pass) for the session
const USER = 'energydrinks';
const PASS_HASH = '51399badaf99cab1e1921de22874aa456d30399d2bf8d9757be42bcaf7a83763';
const DATA_URL = 'data/dashboard.json'; // relative → /data/dashboard.json (nginx-guarded)

async function sha256(s) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function fetchData(token) {
  const res = await fetch(DATA_URL, {
    headers: { Authorization: 'Basic ' + token },
    cache: 'no-store',
  });
  if (res.status === 401 || res.status === 403) return null; // server rejected
  if (!res.ok) throw new Error('data ' + res.status);
  return res.json();
}

function overlay() {
  const el = document.createElement('div');
  el.className = 'gate';
  el.innerHTML = `
    <form class="gate-card mono" autocomplete="off" novalidate>
      <div class="gate-brand"><img class="gate-mark" src="/mascot.svg" alt="" /><span>Bogus Banana</span></div>
      <div class="gate-head"><span class="volt">·</span> RESTRICTED — MARKET INTEL</div>
      <label class="gate-label" for="gate-user"><span class="volt">&gt;</span> OPERATOR_ID</label>
      <input id="gate-user" type="text" spellcheck="false" autocapitalize="off" placeholder="username" />
      <label class="gate-label" for="gate-pass"><span class="volt">&gt;</span> ACCESS_KEY</label>
      <input id="gate-pass" type="password" placeholder="password" />
      <button type="submit">AUTHENTICATE ↵</button>
      <p class="gate-out" role="status"></p>
    </form>`;
  return el;
}

function showForm(resolve) {
  document.body.classList.add('gated');
  const el = overlay();
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
      okLocal = u === USER && (await sha256(p)) === PASS_HASH;
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
      data = await fetchData(token);
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
      sessionStorage.setItem(KEY, token);
    } catch (e2) {
      /* private mode — just won't persist across reloads */
    }
    unlock(data);
  });
}

/* Resolves with the dashboard data once the visitor is authenticated. */
export function requireAuth() {
  return new Promise((resolve) => {
    const saved = sessionStorage.getItem(KEY);
    if (saved) {
      fetchData(saved)
        .then((d) => (d ? resolve(d) : (sessionStorage.removeItem(KEY), showForm(resolve))))
        .catch(() => showForm(resolve));
      return;
    }
    showForm(resolve);
  });
}
