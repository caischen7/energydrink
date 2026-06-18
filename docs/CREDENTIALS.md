# ION_OS — Admin Credentials (private)

> Internal reference for the repo owner. Kept in the repo because it is
> **private**. Not served by the site — `docs/` is excluded from the deploy image
> (`.dockerignore` / `.gcloudignore`).

## Market Intel dashboard login

| Field | Value |
| --- | --- |
| Page | `/dashboard.html` — reachable via the **MARKET INTEL ↗** link in the top bar |
| Username | `energydrinks` |
| Password | `energydrinks12345` |

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
htpasswd -bc .htpasswd energydrinks 'NEW_PASSWORD'
#   (no htpasswd? use:  printf 'energydrinks:%s\n' "$(openssl passwd -apr1 'NEW_PASSWORD')" > .htpasswd )

# 2) client check (PASS_HASH in src/auth.js):
printf '%s' 'NEW_PASSWORD' | sha256sum     # paste the hex into PASS_HASH

# then rebuild / redeploy, and update the table above
```

## Cautions

- `.htpasswd` (hashed) ships inside the deployed image — that's how Basic Auth
  works. The hash is apr1/MD5-based and this password is short, so treat the
  credential as **low-strength**; don't reuse it anywhere that matters.
- The server gate protects the **data**, which is the licensed/sensitive part.
  The dashboard's HTML/JS shell is public (it contains no figures).
- This repo is private today. **If you ever make it public** (e.g. the GitHub
  Pages deploy option), rotate the password and scrub `.htpasswd` + this file from
  git history first — committed secrets persist in history even after deletion.
