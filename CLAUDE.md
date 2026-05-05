# Surf Weather — Claude Instructions

## Stack

- **Backend:** Python 3.11, FastAPI, uvicorn (`backend/`)
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS (`frontend/`)
- **Infrastructure:** Docker Compose locally; Google Cloud Run in production
- **GCP project:** `surf-weather-492803`
- **Artifact Registry:** `us-central1-docker.pkg.dev/surf-weather-492803/web/`

## Development

All tooling runs inside Docker — never install Node or Python on the host.

```bash
# Start full stack locally
docker compose up --build

# Run frontend tests
docker compose --profile test run --rm frontend-test

# Run backend tests
docker compose run --rm backend pytest
```

## Deployment

### Production

```bash
./deploy.sh
```

Builds both images, pushes to Artifact Registry, deploys `surf-backend` and `surf-frontend` Cloud Run services.

### Test (staging)

Deploy to separate `*-test` Cloud Run services using `:test`-tagged images. Production services are untouched.

```bash
./deploy.sh -t
```

### Service URLs

| Service | URL |
|---------|-----|
| Frontend | `https://surf-frontend-476326886107.us-central1.run.app` |
| Backend | `https://surf-backend-476326886107.us-central1.run.app` |
| Frontend (test) | `https://surf-frontend-test-476326886107.us-central1.run.app` |
| Backend (test) | `https://surf-backend-test-476326886107.us-central1.run.app` |

## Adding a Lake

Edit `backend/config/lakes.yaml` — no code changes needed. Restart the backend container to pick up changes:

```bash
docker compose restart backend
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/config/lakes.yaml` | Lake definitions — coordinates, providers, pool elevations |
| `backend/surf_weather/providers/weather/open_meteo.py` | Weather forecast (Open-Meteo, currently 10-day) |
| `backend/surf_weather/providers/lake_data/` | One file per data provider |
| `frontend/src/components/lake-detail/WeatherTable.tsx` | Daily forecast table with expandable hourly rows |
| `deploy.sh` | Deploy script — production by default, `./deploy.sh -t` for test/staging |
