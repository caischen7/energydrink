# Bogus Banana — Admin Credentials (private)

> Internal reference for the repo owner. Kept in the repo because it is
> **private**. Not served by the site — `docs/` is excluded from the deploy image
> (`.dockerignore` / `.gcloudignore`).

## Market Intel dashboard login

| Field | Value |
| --- | --- |
| Page | `/dashboard.html` — reachable via the **MARKET INTEL ↗** link in the top bar |
| Username | `energydrink` |
| Password | `energydrink` |

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

1. **Server-side (real): nginx HTTP Basic Auth.** The dashboard's data file
   `/data/dashboard.json` is guarded in [`nginx.conf`](../nginx.conf) by
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
  anywhere that matters. The dashboard login is now `energydrink`/`energydrink` —
  username and password identical, which is the most guessable form there is.
  That is a deliberate trade for ease of sharing with reviewers; it is only
  defensible because the audience is small and the repo is private. **If the
  licensed Mintel / Euromonitor / PDI figures behind this gate ever need real
  protection, this is the first thing to change**, and the fix is to generate a
  passphrase and inject it at deploy time from an env var instead of committing it.
- The server gate protects the **data**, which is the licensed/sensitive part.
  The dashboard's HTML/JS shell is public (it contains no figures).
- This repo is private today. **If you ever make it public** (e.g. the GitHub
  Pages deploy option), rotate both passwords and scrub `.htpasswd`,
  `.htpasswd-admin` and this file from git history first — committed secrets
  persist in history even after deletion. The retired admin credential is still
  reachable in history, so treat it as burned.
