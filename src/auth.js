/*
 * Dashboard access gate (ION_OS // RESTRICTED).
 *
 * IMPORTANT — this is a client-side deterrent, NOT real security. The page is a
 * static bundle, so a determined visitor can bypass the check via devtools and
 * the underlying data ships in the JS regardless. To actually restrict the
 * dashboard (e.g. the licensed market data), gate it server-side — nginx Basic
 * Auth on the /dashboard.html location, or Cloud Run IAM / IAP. See docs/DEPLOY.md.
 *
 * Credentials: username compared in the clear (not secret); the password is
 * checked against a SHA-256 hash so the plaintext isn't committed. To change the
 * password, recompute:  printf '%s' 'NEWPASS' | sha256sum
 */
const KEY = 'ion_dash_auth';
const USER = 'energydrinks';
const PASS_HASH = '51399badaf99cab1e1921de22874aa456d30399d2bf8d9757be42bcaf7a83763';

async function sha256(s) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function overlay() {
  const el = document.createElement('div');
  el.className = 'gate';
  el.innerHTML = `
    <form class="gate-card mono" autocomplete="off" novalidate>
      <div class="gate-brand">ION<sup>®</sup></div>
      <div class="gate-head"><span class="volt">//</span> RESTRICTED — MARKET INTEL TERMINAL</div>
      <label class="gate-label" for="gate-user"><span class="volt">&gt;</span> OPERATOR_ID</label>
      <input id="gate-user" type="text" spellcheck="false" autocapitalize="off" placeholder="username" />
      <label class="gate-label" for="gate-pass"><span class="volt">&gt;</span> ACCESS_KEY</label>
      <input id="gate-pass" type="password" placeholder="password" />
      <button type="submit">AUTHENTICATE ↵</button>
      <p class="gate-out" role="status"></p>
    </form>`;
  return el;
}

export function requireAuth() {
  return new Promise((resolve) => {
    if (sessionStorage.getItem(KEY) === '1') {
      resolve();
      return;
    }
    document.body.classList.add('gated');
    const el = overlay();
    document.body.appendChild(el);
    const form = el.querySelector('form');
    const out = el.querySelector('.gate-out');
    const user = el.querySelector('#gate-user');
    const pass = el.querySelector('#gate-pass');
    user.focus();

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      out.textContent = '> VERIFYING…';
      let ok = false;
      try {
        ok = user.value.trim() === USER && (await sha256(pass.value)) === PASS_HASH;
      } catch (err) {
        out.textContent = '> ERR :: SECURE CONTEXT REQUIRED (USE HTTPS OR LOCALHOST)';
        return;
      }
      if (ok) {
        try {
          sessionStorage.setItem(KEY, '1');
        } catch (e2) {
          /* private mode — gate just won't persist across reloads */
        }
        el.classList.add('out');
        document.body.classList.remove('gated');
        setTimeout(() => {
          el.remove();
          resolve();
        }, 450);
      } else {
        out.textContent = '> ACCESS DENIED :: INVALID CREDENTIALS';
        pass.value = '';
        pass.focus();
      }
    });
  });
}
