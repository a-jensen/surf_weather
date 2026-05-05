#!/usr/bin/env bash
set -euo pipefail

REGISTRY="us-central1-docker.pkg.dev"
PROJECT="surf-weather-492803"
REGION="us-central1"

TEST=false
while getopts "t" opt; do
  case $opt in
    t) TEST=true ;;
    *) echo "Usage: $0 [-t]" >&2; exit 1 ;;
  esac
done

if $TEST; then
  TAG="test"
  BACKEND_SERVICE="surf-backend-test"
  FRONTEND_SERVICE="surf-frontend-test"
  BACKEND_URL="https://surf-backend-test-476326886107.us-central1.run.app"
  FRONTEND_URL="https://surf-frontend-test-476326886107.us-central1.run.app"
else
  TAG="latest"
  BACKEND_SERVICE="surf-backend"
  FRONTEND_SERVICE="surf-frontend"
  BACKEND_URL="https://surf-backend-476326886107.us-central1.run.app"
  FRONTEND_URL="https://surf-frontend-476326886107.us-central1.run.app"
fi

IMAGE_BASE="${REGISTRY}/${PROJECT}/web"

echo "==> Authenticating Docker with Artifact Registry..."
gcloud auth print-access-token \
  | docker login -u oauth2accesstoken --password-stdin "https://${REGISTRY}"

echo "==> Building images..."
docker compose build

if $TEST; then
  echo "==> Tagging images as :test..."
  docker tag "${IMAGE_BASE}/backend" "${IMAGE_BASE}/backend:test"
  docker tag "${IMAGE_BASE}/frontend" "${IMAGE_BASE}/frontend:test"

  echo "==> Pushing images..."
  docker push "${IMAGE_BASE}/backend:test"
  docker push "${IMAGE_BASE}/frontend:test"
else
  echo "==> Pushing images..."
  docker compose push
fi

echo "==> Deploying backend to Cloud Run..."
gcloud run deploy "${BACKEND_SERVICE}" \
  --project "${PROJECT}" \
  --image "${IMAGE_BASE}/backend:${TAG}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated

echo "==> Deploying frontend to Cloud Run..."
gcloud run deploy "${FRONTEND_SERVICE}" \
  --project "${PROJECT}" \
  --image "${IMAGE_BASE}/frontend:${TAG}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "BACKEND_URL=${BACKEND_URL}"

echo ""
echo "Deploy complete."
echo "  Backend:  ${BACKEND_URL}"
echo "  Frontend: ${FRONTEND_URL}"
