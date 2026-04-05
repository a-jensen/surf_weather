# Wake Surf Weather

A website for comparing weather and lake conditions across Utah wake surfing lakes. View air temperature, water temperature, wind, water level, rain chance, and lightning risk for the next 7 days — then drill into a lake for 90-day historical charts.

---

## Features

- **7-day forecast strip** per lake with Good / Fair / Poor surfing score per day
- **Lightning risk** indicator derived from WMO thunderstorm codes and CAPE (Convective Available Potential Energy)
- **Real-time water level and temperature** from USGS stream gauges
- **90-day historical charts** for water level and water temperature
- **Modular architecture** — lakes and data providers are independently configurable; adding a new state requires no structural changes

---

## Architecture

```
surf_weather/
├── backend/          # Python FastAPI REST API
├── frontend/         # React + Vite SPA
└── docker-compose.yml
```

### Backend

**Language / framework:** Python 3.11, FastAPI, uvicorn

**External APIs (no keys required):**

| API | Purpose |
|-----|---------|
| [Open-Meteo](https://open-meteo.com) | 7-day weather forecast — single source for all lakes |
| [USGS NWIS](https://waterservices.usgs.gov) | Water level (gage height) and water temperature |

**Internal structure:**

```
backend/
├── config/
│   └── lakes.yaml              # Lake definitions — add lakes here
└── surf_weather/
    ├── main.py                 # FastAPI app factory
    ├── config.py               # YAML loader → list[LakeConfig]
    ├── models/
    │   ├── lake.py             # LakeConfig, LakeConditions, HistoricalPoint
    │   ├── weather.py          # WeatherForecast, DailyForecast, HourlyForecast
    │   └── combined.py         # LakeSummary, LakeDetail (API response shapes)
    ├── providers/
    │   ├── base.py             # WeatherProvider + LakeDataProvider abstract base classes
    │   ├── weather/
    │   │   └── open_meteo.py   # Open-Meteo implementation
    │   └── lake_data/
    │       ├── usgs.py         # USGS NWIS implementation
    │       └── registry.py     # Routes each lake to the right provider (first-match)
    ├── routers/
    │   ├── health.py           # GET /health
    │   └── lakes.py            # GET /lakes, GET /lakes/{id}
    ├── services/
    │   └── aggregator.py       # Combines weather + lake data into response shapes
    └── scripts/
        └── lake_data.py        # CLI: display current conditions or plot multi-year history
```

**API endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `GET` | `/lakes` | All lakes with current conditions and 7-day forecast strips |
| `GET` | `/lakes/{lake_id}` | Full detail: conditions, 90-day history, complete forecast |

### Frontend

**Language / framework:** React 18, TypeScript, Vite, Tailwind CSS, Recharts

**Structure:**

```
frontend/src/
├── api/
│   ├── client.ts               # fetch wrapper (proxies /api → backend)
│   └── types.ts                # TypeScript interfaces mirroring backend models
├── components/
│   ├── layout/Header.tsx
│   ├── lake-list/
│   │   ├── LakeListPage.tsx    # Route /  — fetches GET /lakes
│   │   ├── LakeCard.tsx        # One lake with 7-day strip
│   │   └── DayBadge.tsx        # Single day: icon, temps, wind, rain %, lightning
│   ├── lake-detail/
│   │   ├── LakeDetailPage.tsx  # Route /lakes/:id — fetches GET /lakes/{id}
│   │   ├── ConditionsBanner.tsx
│   │   ├── WeatherTable.tsx    # 7-day table with all stats
│   │   ├── WaterLevelChart.tsx # Recharts 90-day gage height line chart
│   │   └── WaterTempChart.tsx  # Recharts 90-day water temperature line chart
│   └── shared/
│       ├── WeatherIcon.tsx     # WMO code → emoji icon
│       ├── WindIndicator.tsx   # Speed + compass direction
│       └── LoadingSpinner.tsx
├── hooks/
│   ├── useLakes.ts             # Fetches lake list
│   └── useLakeDetail.ts        # Fetches single lake detail
└── utils/
    ├── weatherCodes.ts         # WMO code → label + icon map
    ├── formatters.ts           # Temperature, wind, date, unit conversions
    └── lakeConditionScore.ts   # Good / Fair / Poor scoring logic
```

**Routing:** React Router v6 — `/` for the lake list, `/lakes/:id` for detail.

**API proxying:** In local Docker, nginx proxies `/api/*` → backend container. On Cloud Run, `BACKEND_URL` env var controls the target.

---

## Lakes

Configured in `backend/config/lakes.yaml`. Current lakes:

| Lake | USGS Gauge | Water Data |
|------|-----------|------------|
| Deer Creek Reservoir | 10159000 | Level + Temp |
| Pineview Reservoir | 10139000 | Level + Temp |
| East Canyon Reservoir | 10134000 | Level + Temp |
| Rockport Reservoir | 10129400 | Level + Temp |
| Echo Reservoir | 10131500 | Level + Temp |
| Bear Lake | 10055000 | Level + Temp |
| Jordanelle Reservoir | — | N/A (no gauge) |
| Utah Lake | — | N/A (no gauge) |

Lakes without a USGS gauge still show the full weather forecast; water level and temperature display as N/A.

---

## Surfing Condition Score

Each day is rated based on wind and rain. Lightning always overrides to Poor.

| Factor | Fair | Poor |
|--------|------|------|
| Wind speed | ≥ 15 mph | ≥ 22 mph |
| Rain chance | ≥ 30% | ≥ 60% |
| Thunderstorm | — | any risk |

---

## Lake Data CLI

`backend/scripts/lake_data.py` lets you query lake conditions and plot multi-year historical data directly from the command line without running the full server.

**Prerequisites:** the backend Python environment must be active (or use the Docker container — see below). Plotting additionally requires `matplotlib`.

### Usage

```bash
# Show current water temperature and level for Deer Creek
python backend/scripts/lake_data.py deer_creek

# List all available lake IDs
python backend/scripts/lake_data.py --list-lakes deer_creek

# Plot the last 10 years of temperature + water level (one line per year, Jan–Dec x-axis)
python backend/scripts/lake_data.py deer_creek -p

# Plot only the last 5 years
python backend/scripts/lake_data.py deer_creek -p --years 5

# Choose a provider explicitly (currently only usgs is available)
python backend/scripts/lake_data.py deer_creek --provider usgs
```

### Running via Docker

```bash
docker compose run --rm backend python scripts/lake_data.py deer_creek
docker compose run --rm backend python scripts/lake_data.py deer_creek -p --years 5
```

---

## Running Locally

**Requires:** Docker and Docker Compose.

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Website | http://localhost:8080 |
| API | http://localhost:8000 |

To stop:

```bash
docker compose down
```

To reload lake config changes without rebuilding (the config directory is mounted as a volume):

```bash
docker compose restart backend
```

---

## Testing

All tests run inside Docker — no local language runtimes required.

### Backend

```bash
docker compose run --rm backend pytest
```

To include coverage:

```bash
docker compose run --rm backend pytest --cov --cov-report=term-missing
```

Test layout:

```
backend/tests/
├── conftest.py              # Shared fixtures (fake lake, forecast, conditions)
├── fixtures/                # Recorded API responses for mocking
│   ├── open_meteo_response.json
│   ├── usgs_iv_response.json
│   └── usgs_dv_response.json
├── unit/
│   ├── test_models.py
│   ├── test_open_meteo_provider.py   # httpx mocked via respx
│   ├── test_usgs_provider.py         # httpx mocked via respx
│   ├── test_lake_data_script.py      # CLI script tested via Click's CliRunner
│   ├── test_registry.py
│   ├── test_config.py
│   └── test_aggregator.py
└── integration/
    └── test_api_routes.py            # FastAPI TestClient, providers mocked
```

No external network calls are made during tests — all HTTP is mocked.

### Frontend

```bash
docker compose run --rm frontend npm test
```

Test layout:

```
frontend/tests/
├── setup.ts
├── components/
│   ├── DayBadge.test.tsx
│   ├── LakeCard.test.tsx
│   └── WindIndicator.test.tsx
└── utils/
    ├── weatherCodes.test.ts
    ├── lakeConditionScore.test.ts
    └── formatters.test.ts
```

---

## Adding a New Lake

Edit `backend/config/lakes.yaml` and add an entry:

```yaml
- id: sand_hollow
  name: Sand Hollow Reservoir
  state: UT
  latitude: 37.1067
  longitude: -113.3950
  usgs_site_id: "09415000"   # or null if no gauge
  data_provider: usgs
```

Restart the backend container — no code changes required.

---

## Adding a New State / Data Provider

1. Create `backend/surf_weather/providers/lake_data/<state>.py` implementing the `LakeDataProvider` ABC:

```python
from ..base import LakeDataProvider
from ...models.lake import LakeConfig, LakeConditions

class MyStateProvider(LakeDataProvider):
    @property
    def provider_name(self) -> str:
        return "my_state_provider"

    def supports_lake(self, lake: LakeConfig) -> bool:
        return lake.data_provider == "my_state"

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        # fetch from state API and return LakeConditions
        ...
```

2. Register it in `backend/surf_weather/main.py` inside `_build_aggregator()`:

```python
from .providers.lake_data.my_state import MyStateProvider

registry.register(MyStateProvider())
```

3. Add lakes to `lakes.yaml` with `data_provider: my_state`.

---

## Deployment — Google Cloud Run

Both containers are deployed as separate Cloud Run services. The frontend proxies API calls to the backend using the `BACKEND_URL` environment variable.

### Prerequisites

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
```

### Build and push images

```bash
# Set your project and region
PROJECT=your-gcp-project
REGION=us-central1
REPO=surf-weather

# Create Artifact Registry repo (once)
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION

# Authenticate Docker
gcloud auth configure-docker $REGION-docker.pkg.dev

# Build and push backend
docker build -t $REGION-docker.pkg.dev/$PROJECT/$REPO/backend:latest ./backend
docker push $REGION-docker.pkg.dev/$PROJECT/$REPO/backend:latest

# Build and push frontend
docker build -t $REGION-docker.pkg.dev/$PROJECT/$REPO/frontend:latest ./frontend
docker push $REGION-docker.pkg.dev/$PROJECT/$REPO/frontend:latest
```

### Deploy backend

```bash
gcloud run deploy surf-weather-backend \
  --image $REGION-docker.pkg.dev/$PROJECT/$REPO/backend:latest \
  --region $REGION \
  --platform managed \
  --no-allow-unauthenticated \
  --port 8000
```

Note the service URL from the output (e.g. `https://surf-weather-backend-xxxx-uc.a.run.app`).

### Deploy frontend

```bash
BACKEND_URL=https://surf-weather-backend-xxxx-uc.a.run.app

gcloud run deploy surf-weather-frontend \
  --image $REGION-docker.pkg.dev/$PROJECT/$REPO/frontend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 80 \
  --set-env-vars BACKEND_URL=$BACKEND_URL
```

The frontend URL from the output is the public website address.

### Allow frontend to call backend

The backend is deployed without public access. Grant the frontend's service account permission to invoke it:

```bash
# Get the frontend's service account
FRONTEND_SA=$(gcloud run services describe surf-weather-frontend \
  --region $REGION --format='value(spec.template.spec.serviceAccountName)')

gcloud run services add-iam-policy-binding surf-weather-backend \
  --region $REGION \
  --member "serviceAccount:$FRONTEND_SA" \
  --role roles/run.invoker
```

> **Note:** The nginx proxy in the frontend container passes requests through as-is. For Cloud Run service-to-service auth you may need to configure the backend to accept the OIDC token that Cloud Run attaches — or deploy the backend as publicly accessible if internal-only access is not required for your use case.

### Updating a deployment

```bash
# Rebuild, push, and redeploy (backend example)
docker build -t $REGION-docker.pkg.dev/$PROJECT/$REPO/backend:latest ./backend
docker push $REGION-docker.pkg.dev/$PROJECT/$REPO/backend:latest
gcloud run deploy surf-weather-backend \
  --image $REGION-docker.pkg.dev/$PROJECT/$REPO/backend:latest \
  --region $REGION
```
