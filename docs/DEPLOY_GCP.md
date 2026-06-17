# Hosting on Google Cloud (Cloud Run)

The ION_INTEL site — the marketing landing page **and** the founder
market-intelligence dashboard — deploys to **Google Cloud Run** as a single
public service. This mirrors the Cloud Run pattern used by the
`msbai-dwd-csc9720` dashboard: a container is built server-side by Cloud Build
and served on `$PORT`. The difference is this app is a **static Vite build**, so
the container is just nginx serving `dist/`.

```
Dockerfile                  two-stage build: node (vite build) -> nginx (serve dist/)
deploy/nginx.conf.template  nginx server block; ${PORT} filled in at container start
deploy/deploy.sh            one-command Cloud Run deploy (uses your gcloud auth)
.dockerignore               keeps the build context small (excludes data/, node_modules…)
```

> **Auth note:** unlike the reference repo, this setup does **not** bundle any
> stored service-account key or `.claude` auth hook. It deploys with *your* own
> `gcloud` login, so credentials stay under your control. Nothing secret is
> committed to the repo.

---

## Option A — deploy from your machine

Prereqs: the [gcloud CLI](https://cloud.google.com/sdk/docs/install) and a
billing-enabled GCP project.

```bash
gcloud auth login
GCP_PROJECT=your-project-id ./deploy/deploy.sh
```

That's it. The script enables the needed APIs, runs `gcloud run deploy
--source .` (Cloud Build builds the image, no local Docker required), and prints
the public URLs:

```
landing page  : https://energydrink-site-XXXX-uc.a.run.app/
intel terminal: https://energydrink-site-XXXX-uc.a.run.app/dashboard.html
```

## Option B — deploy from Google Cloud Shell (nothing to install)

[Cloud Shell](https://shell.cloud.google.com) already has `gcloud` installed and
authenticated:

```bash
git clone -b claude/pensive-bell-9idinw https://github.com/caischen7/energydrink.git
cd energydrink
GCP_PROJECT=your-project-id ./deploy/deploy.sh
```

You can reuse the existing `msbai-dwd-csc9720` project or create a new one
(`gcloud projects create ...`, then link billing).

---

## Knobs

All overridable via environment variables when calling `deploy.sh`:

| Var | Default | Meaning |
|-----|---------|---------|
| `GCP_PROJECT` | *(required)* | Target project id |
| `GCP_REGION` | `us-central1` | Cloud Run region |
| `SERVICE` | `energydrink-site` | Cloud Run service name |

## Updating the dashboard data

The dashboard reads `public/market_intel.json`, which is baked into the image at
build time. To refresh it after the datasets change:

```bash
python data/scripts/build_dashboard_data.py   # regenerate public/market_intel.json
git commit -am "refresh market intel" && git push
./deploy/deploy.sh                            # redeploy
```

## Continuous deploy (optional)

To redeploy automatically on every push, either:

- **Cloud Build trigger** — `gcloud builds triggers create github --repo-name
  energydrink --branch-pattern '^main$' --build-config` (or use the inferred
  Dockerfile), or
- a **GitHub Actions** workflow using
  [`google-github-actions/deploy-cloudrun`](https://github.com/google-github-actions/deploy-cloudrun)
  with Workload Identity Federation.

Ask and I can wire either one up.

## Cost

Cloud Run scales to zero — you pay only while serving requests. A low-traffic
static site like this typically stays within the
[free tier](https://cloud.google.com/run/pricing) (2M requests/month).

## Local container smoke test

If you have Docker locally (this CI sandbox can't reach Docker Hub, so it's
built on Cloud Build instead):

```bash
docker build -t energydrink-site .
docker run --rm -e PORT=8080 -p 8080:8080 energydrink-site
# open http://localhost:8080  and  http://localhost:8080/dashboard.html
```
