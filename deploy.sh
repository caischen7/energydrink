#!/bin/bash
# Deploy ION — Liquid Hardware (static Vite site) to Google Cloud Run as a
# public service. Mirrors the Cloud Run deploy used in caischen7/msbai-dwd-csc9720.
#
# Prereqs:
#   - gcloud authenticated as a principal allowed to deploy (Cloud Run + Cloud
#     Build). In a Claude Code "Google Cloud" environment the cloud-auth hook
#     does this automatically when GCP_CREDENTIALS_KEY is set (see the managed
#     .cloud-config.json). Otherwise run `gcloud auth login` yourself first.
#   - A GCP project with billing enabled.
#
# Usage (from the repo root):
#   GCP_PROJECT=my-project ./deploy.sh
#   # optional overrides: GCP_REGION=us-central1 SERVICE_NAME=ion-liquid-hardware
set -euo pipefail

REGION="${GCP_REGION:-us-central1}"
SERVICE="${SERVICE_NAME:-ion-liquid-hardware}"

# Resolve the project: explicit env var wins, else the managed .cloud-config.json.
PROJECT="${GCP_PROJECT:-}"
if [ -z "$PROJECT" ] && [ -f .cloud-config.json ]; then
  PROJECT="$(sed -nE 's/.*"project_id"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' .cloud-config.json)"
fi
if [ -z "$PROJECT" ]; then
  echo "ERROR: no project. Set GCP_PROJECT=your-project-id (or provide .cloud-config.json)." >&2
  exit 1
fi

echo "Deploying '$SERVICE' to project '$PROJECT' ($REGION)..."
gcloud config set project "$PROJECT"

# APIs needed to build (Cloud Build) and serve (Run); harmless if already on.
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

# --source . builds the Dockerfile with Cloud Build (server-side; no local
# Docker needed), then deploys. --allow-unauthenticated => public URL, no login.
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --port 8080 \
  --timeout 60

echo
echo "Deployed. Public URL:"
gcloud run services describe "$SERVICE" --region "$REGION" \
  --format 'value(status.url)'
