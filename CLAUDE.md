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

### Looking up a USBR site ID

USBR site IDs can be verified against the official metadata CSV, which lists every site with its name, coordinates, and state:

```bash
curl -s "https://www.usbr.gov/uc/water/hydrodata/reservoir_data/meta.csv" | \
  python3 -c "
import csv, sys
for row in csv.DictReader(sys.stdin):
    if 'RESERVOIR NAME' in row['site_metadata.site_name'].upper():
        print(row['site_id'], row['site_metadata.site_name'], row['site_metadata.lat'], row['site_metadata.longi'])
        break
"
```

Cross-check the returned lat/lon against the lake's known coordinates — elevation alone is not a reliable signal (different reservoirs can operate at similar elevations). The data file for a given site and parameter is at `https://www.usbr.gov/uc/water/hydrodata/reservoir_data/{site_id}/json/49.json` (parameter 49 = pool elevation).

## Performance Testing

`perf_test.py` at the project root measures response times against the live test or production environment. Stdlib only — runs from the host without Docker.

```bash
python3 perf_test.py            # test environment (default)
python3 perf_test.py --env prod # production
python3 perf_test.py --runs 5   # more samples for a stable average
```

**Key performance facts:**
- The `/api/lakes` summary cache and per-lake detail cache are separate — warming one does not warm the other.
- Lake Powell is the slowest provider (~5 s cold) because it scrapes an HTML page; all others call JSON APIs.
- Cloud Run scales to zero when idle, so the first request after a gap hits both a cold start and an empty cache.

## Key Files

| File | Purpose |
|------|---------|
| `backend/config/lakes.yaml` | Lake definitions — coordinates, providers, pool elevations |
| `backend/surf_weather/providers/weather/open_meteo.py` | Weather forecast (Open-Meteo, currently 10-day) |
| `backend/surf_weather/providers/lake_data/` | One file per data provider |
| `backend/surf_weather/services/cache.py` | CachingAggregator — 15-min TTL; summary and detail caches are independent |
| `frontend/src/components/lake-detail/WeatherTable.tsx` | Daily forecast table with expandable hourly rows |
| `deploy.sh` | Deploy script — production by default, `./deploy.sh -t` for test/staging |
| `perf_test.py` | Measures live endpoint response times; stdlib only, no Docker needed |
