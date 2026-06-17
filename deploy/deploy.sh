#!/usr/bin/env bash
# Deploy the ION_INTEL site (landing page + market-intelligence dashboard) to
# Google Cloud Run as a public service.
#
# Modeled on the Cloud Run deploy used by the msbai-dwd-csc9720 dashboard, but
# it authenticates with YOUR own gcloud session — run `gcloud auth login` first
# (no stored service-account keys are bundled in this repo).
#
# Prereqs:
#   1. Install the gcloud CLI:  https://cloud.google.com/sdk/docs/install
#   2. gcloud auth login
#   3. A billing-enabled GCP project (set GCP_PROJECT below or via env)
#
# Usage:
#   GCP_PROJECT=my-project ./deploy/deploy.sh
#
set -euo pipefail

PROJECT="${GCP_PROJECT:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE="${SERVICE:-energydrink-site}"

if [[ -z "$PROJECT" ]]; then
  echo "ERROR: set GCP_PROJECT to your Google Cloud project id, e.g.:" >&2
  echo "  GCP_PROJECT=my-project ./deploy/deploy.sh" >&2
  exit 1
fi

# Run from the repo root so the build context contains the Dockerfile + source.
cd "$(dirname "$0")/.."

echo "▸ project=$PROJECT  region=$REGION  service=$SERVICE"
gcloud config set project "$PROJECT"

# APIs needed to build (Cloud Build) and serve (Run). Harmless if already on.
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

# --source . builds the image from the repo Dockerfile with Cloud Build
# (server-side; no local Docker needed) and deploys it. The site is static and
# needs no GCP data access, so it runs as the default service account.
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 4

URL=$(gcloud run services describe "$SERVICE" --region "$REGION" \
  --format 'value(status.url)')
echo
echo "✓ Deployed."
echo "  landing page : $URL/"
echo "  intel terminal: $URL/dashboard.html"
