#!/usr/bin/env bash
set -euo pipefail

REGISTRY="us-central1-docker.pkg.dev"
PROJECT="surf-weather-492803"
REGION="us-central1"
BACKEND_URL="https://surf-backend-476326886107.us-central1.run.app"

echo "==> Authenticating Docker with Artifact Registry..."
gcloud auth print-access-token \
  | docker login -u oauth2accesstoken --password-stdin "https://${REGISTRY}"

echo "==> Building images..."
docker compose build

echo "==> Pushing images..."
docker compose push

echo "==> Deploying backend to Cloud Run..."
gcloud run deploy surf-backend \
  --image "${REGISTRY}/${PROJECT}/web/backend" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated

echo "==> Deploying frontend to Cloud Run..."
gcloud run deploy surf-frontend \
  --image "${REGISTRY}/${PROJECT}/web/frontend" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "BACKEND_URL=${BACKEND_URL}"

echo ""
echo "Deploy complete."
echo "  Backend:  ${BACKEND_URL}"
echo "  Frontend: https://surf-fronted-476326886107.us-central1.run.app"
