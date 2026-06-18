# ION_OS — Admin Credentials (private)

> Internal reference for the repo owner. Kept in the repo for convenience because
> it is **private**. Not served by the site — `docs/` is excluded from the deploy
> image (`.dockerignore` / `.gcloudignore`).

## Market Intel dashboard login

| Field | Value |
| --- | --- |
| Page | `/dashboard.html` — reachable via the **MARKET INTEL ↗** link in the top bar |
| Username | `energydrinks` |
| Password | `energydrinks12345` |

Defined in [`src/auth.js`](../src/auth.js): the username is compared in plaintext;
the password is checked against its **SHA-256 hash**
(`51399badaf99cab1e1921de22874aa456d30399d2bf8d9757be42bcaf7a83763`), so the
plaintext password is not what's stored in code.

**To change the password:**

```bash
printf '%s' 'NEW_PASSWORD' | sha256sum   # copy the hex digest
# paste it into PASS_HASH in src/auth.js (and update the table above)
```

## Cautions — read before relying on this

- The dashboard login is a **client-side deterrent, not real security.** The check
  and the underlying data both ship in the static bundle, so it's bypassable via
  browser devtools. It keeps casual visitors out; it does **not** protect the
  licensed Mintel/Statista data on a public URL. For real protection, gate it
  server-side (nginx Basic Auth on `/dashboard.html`, or Cloud Run IAM / IAP).
- Because the SHA-256 hash already lives in `src/auth.js` and this password is
  short/guessable, treat it as **effectively non-secret**. Don't reuse it for
  anything that actually matters.
- This repo is private today. **If you ever make it public** (e.g. the GitHub
  Pages deploy option), remove this file, rotate the password, and scrub it from
  git history first — committed secrets persist in history even after deletion.
