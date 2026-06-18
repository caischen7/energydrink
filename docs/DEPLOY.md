# Deploying to Google Cloud Run

The site is containerized and deploys to **Google Cloud Run** as a public
service — the same pattern as [`caischen7/msbai-dwd-csc9720`](https://github.com/caischen7/msbai-dwd-csc9720),
adapted for a static Vite site instead of a Streamlit app.

## What's here

| File | Purpose |
| --- | --- |
| `Dockerfile` | Multi-stage: `node` builds the Vite site → `nginx` serves `dist/` on `$PORT`. |
| `nginx.conf` | nginx server template; `${PORT}` is substituted at container start. |
| `deploy.sh` | One command: `gcloud run deploy --source .` (Cloud Build → Cloud Run, public URL). |
| `.dockerignore` / `.gcloudignore` | Keep the build context / source upload small (exclude `.claude`, `data`, `docs`, deps). |

## Deploy it

```bash
# from the repo root, with gcloud authenticated and a billing-enabled project:
GCP_PROJECT=your-project-id ./deploy.sh
```

That builds the image server-side with Cloud Build (no local Docker needed),
deploys to Cloud Run with `--allow-unauthenticated`, and prints the public URL
(`https://ion-liquid-hardware-<hash>-uc.a.run.app`). Overrides:
`GCP_REGION` (default `us-central1`), `SERVICE_NAME` (default `ion-liquid-hardware`).

## Why it can't be deployed from this Claude session

The reference repo deploys because **its** Claude Code environment was created
with the **Google Cloud integration**, which provisions:

- a GCP project + a `claude-agent@…` service account,
- a managed `.cloud-config.json` and an encrypted `.cloud-credentials.*.enc`,
- the `gcloud` CLI and a cloud-auth hook that authenticates automatically when
  `GCP_CREDENTIALS_KEY` is set.

**This** environment was **not** created with that integration — there is no
`gcloud`, no `.cloud-config.json`, and no `GCP_CREDENTIALS_KEY` — so the live
`gcloud run deploy` cannot run here. The build itself is verified
(`npm run build` is green and reproduced in CI).

To actually deploy, pick one:

1. **Claude Code on the web, with Google Cloud enabled** — start a session for
   this repo in an environment configured with the Google Cloud integration,
   then run `./deploy.sh`. The cloud-auth hook handles auth. See the
   [environment configuration docs](https://code.claude.com/docs/en/claude-code-on-the-web).
2. **From your own machine** — install the
   [gcloud CLI](https://cloud.google.com/sdk/docs/install), run
   `gcloud auth login`, then `GCP_PROJECT=your-project-id ./deploy.sh`.

## Dashboard authentication

The Market Intel dashboard's data (`/data/dashboard.json`, derived from licensed
Mintel/Statista reports) is served behind **nginx HTTP Basic Auth** — see the
guarded `location = /data/dashboard.json` block in `nginx.conf`, backed by
`.htpasswd` (copied into the image by the `Dockerfile`). Credentials live in
`.htpasswd` (hashed); see `docs/CREDENTIALS.md` to view or change them. The
landing page and the dashboard shell stay public; only the data is gated.

## Notes

- The container listens on Cloud Run's `$PORT` (default 8080) via nginx's
  `envsubst` template mechanism.
- Vite's `base: './'` (in `vite.config.js`) keeps asset paths relative, so the
  site also works behind a proxy or sub-path without changes.
- Cloud Run scales to zero — there's no cost when no one is visiting.
