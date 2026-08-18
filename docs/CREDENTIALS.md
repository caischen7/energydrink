# Bogus Banana — Admin Credentials (private)

> Internal reference for the repo owner. Kept in the repo because it is
> **private**. Not served by the site — `docs/` is excluded from the deploy image
> (`.dockerignore` / `.gcloudignore`).

## Market Intel dashboard login

| Field | Value |
| --- | --- |
| Page | `/dashboard.html` — reachable via the **MARKET INTEL ↗** link in the top bar |
| Username | `energydrink` |
| Password | `JGLLqdMZBrUAN2MmV8iG` |

Rotated 2026-08-18. The previous password was `energydrink` — identical to the
username, and therefore guessable in one attempt by anyone who loaded the site.

## Admin — Site Scout login

| Field | Value |
| --- | --- |
| Page | `/admin.html` — **not linked from public navigation** (bookmark it) |
| Username | `bogusbanana` |
| Password | `bogusbanana1234` |

Same two-layer pattern as the dashboard, with **separate credentials**: the
client-side check lives in `src/admin.js` (`ADMIN_AUTH.passHash`, SHA-256), and
the server side is nginx Basic Auth on everything under `/admin/`
([`.htpasswd-admin`](../.htpasswd-admin)), which guards the tool's config feed
`/admin/config.json`. To change: same recipe as below, but write
`.htpasswd-admin` and update `ADMIN_AUTH.passHash` in `src/admin.js`.

## How it's enforced (two layers, one login)

1. **Server-side (real): nginx HTTP Basic Auth.** Everything under `/data/`
   **and the analysis pages themselves** (`dashboard`, `insights`, `segments`,
   `audience`, `compare`, `opportunity`, `explorer` `.html`) are guarded in
   [`nginx.conf`](../nginx.conf) by
   `auth_basic` against [`.htpasswd`](../.htpasswd) (apr1-hashed, copied into the
   image by the [`Dockerfile`](../Dockerfile)). The login form fetches the data
   with the entered credentials, so the licensed Mintel/Statista figures are never
   sent without them — the JS gate can't be bypassed for the data.
2. **Client-side (UX + local dev): SHA-256 check** in [`src/auth.js`](../src/auth.js)
   (`PASS_HASH`), so the plaintext password isn't in the JS bundle. This is what
   gates `npm run dev` locally, where there's no nginx.

## Changing the password — update BOTH

```bash
# 1) server gate (.htpasswd):
htpasswd -bc .htpasswd energydrink 'NEW_PASSWORD'
#   (no htpasswd? use:  printf 'energydrink:%s\n' "$(openssl passwd -apr1 'NEW_PASSWORD')" > .htpasswd )

# 2) client check (PASS_HASH in src/auth.js):
printf '%s' 'NEW_PASSWORD' | sha256sum     # paste the hex into PASS_HASH

# then rebuild / redeploy, and update the table above
```

## Cautions

- `.htpasswd` / `.htpasswd-admin` (hashed) ship inside the deployed image —
  that's how Basic Auth works. The hashes are apr1/MD5-based and the passwords
  are short, so treat both credentials as **low-strength**; don't reuse them
  anywhere that matters. The dashboard password is now a 20-character random
  string rather than a copy of the username, so it is no longer guessable — but
  it is still **committed to this repo**, which is the remaining weakness. The
  proper fix, if these figures ever need real protection, is to inject it at
  deploy time from an env var (or Secret Manager) instead of committing it.
- The server gate protects the **data** *and* the analysis pages. It did not
  always: until 2026-08-18 only `/data/` was guarded, and this file claimed "the
  dashboard's HTML/JS shell is public (it contains no figures)". That was true of
  `dashboard.html` but **false** of `audience.html`, `compare.html` and
  `opportunity.html`, which were added later and carry licensed figures in their
  own prose — Passport-derived brand shares, the Mintel sizing, the channel-share
  history. Verified with real nginx: those pages returned 200 to anonymous
  requests while the JSON beside them returned 401. `index.html` stays public by
  design; it carries no figures.
- This repo is private today. **If you ever make it public** (e.g. the GitHub
  Pages deploy option), rotate both passwords and scrub `.htpasswd`,
  `.htpasswd-admin` and this file from git history first — committed secrets
  persist in history even after deletion. The retired admin credential is still
  reachable in history, so treat it as burned.
