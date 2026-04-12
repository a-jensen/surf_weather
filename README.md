# Wake Surf Weather

A website for comparing weather and lake conditions across Utah wake surfing lakes. View air temperature, water temperature, wind, water level, rain chance, and lightning risk for the next 7 days — then drill into a lake for 90-day historical charts.

---

## Features

- **7-day forecast strip** per lake with Good / Fair / Poor surfing score per day
- **Lightning risk** indicator derived from WMO thunderstorm codes and CAPE (Convective Available Potential Energy)
- **Real-time water level and temperature** from USGS stream gauges
- **90-day historical charts** for water level and water temperature
- **Legend dropdown** in the header explaining the Good / Fair / Poor color thresholds
- **Pin lakes** to the top of the list; pinned and unpinned groups are each sorted independently
- **Sort options** — default, name, warmest water, best conditions, nearest first (uses browser geolocation)
- **User preferences persisted** — pins and sort choice survive page refreshes via `localStorage`
- **Backend response cache** — provider data cached in-process for 15 minutes so page loads are near-instant after the first request
- **Modular architecture** — lakes and data providers are independently configurable; adding a new state requires no structural changes

---

## Architecture

```
surf_weather/
├── backend/          # Python FastAPI REST API
├── frontend/         # React + Vite SPA
├── docker-compose.yml
└── deploy.sh         # One-command build, push, and Cloud Run deploy
```

### Backend

**Language / framework:** Python 3.11, FastAPI, uvicorn

**External APIs (no keys required):**

| API | Purpose |
|-----|---------|
| [Open-Meteo](https://open-meteo.com) | 7-day weather forecast — single source for all lakes |
| [USGS NWIS](https://api.waterdata.usgs.gov) | Water level (elevation) and water temperature — Bear Lake |
| [CUWCD](https://api2.cuwcd.gov) | Reservoir percent-full + 30-day history — Deer Creek, Jordanelle, Utah Lake |
| [Utah State Parks](https://stateparks.utah.gov) | Current water temperature and level % (scraped) — most Utah lakes |
| [lakepowell.water-data.com](https://lakepowell.water-data.com) | Elevation (ft MSL), percent full, 365-day history (scraped) — Lake Powell |
| [USBR HydroData](https://www.usbr.gov/uc/water/hydrodata/reservoir_data/) | Pool elevation (ft MSL) history — Pineview, East Canyon, Rockport, Echo, Willard Bay |

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
    │       ├── cuwcd.py        # Central Utah Water Conservancy District implementation
    │       ├── state_parks.py  # Utah State Parks scraper
    │       ├── lake_powell.py  # lakepowell.water-data.com scraper
    │       ├── usbr.py         # USBR HydroData pool elevation provider
    │       └── registry.py     # Routes each lake to conditions + history providers
    ├── routers/
    │   ├── health.py           # GET /health
    │   └── lakes.py            # GET /lakes, GET /lakes/{id}
    └── services/
        ├── aggregator.py       # Combines weather + lake data into response shapes
        ├── cache.py            # CachingAggregator — 15-min TTL in-process cache
        └── scripts/
            └── lake_data.py    # CLI: display current conditions or plot multi-year history
```

**API endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `GET` | `/lakes` | All lakes with current conditions and 7-day forecast strips |
| `GET` | `/lakes/{lake_id}` | Full detail: conditions, 90-day history, complete forecast |

**Caching:** `CachingAggregator` wraps the `Aggregator` and caches both `/lakes` and `/lakes/{id}` responses for 15 minutes. The first request after server start (or after the TTL expires) fetches live data; all subsequent requests within the window are served from memory. No external cache dependency — stdlib `threading.Lock` only.

### Frontend

**Language / framework:** React 18, TypeScript, Vite, Tailwind CSS, Recharts

**Structure:**

```
frontend/src/
├── api/
│   ├── client.ts               # fetch wrapper (proxies /api → backend)
│   └── types.ts                # TypeScript interfaces mirroring backend models
├── components/
│   ├── layout/Header.tsx       # App header with Legend dropdown
│   ├── lake-list/
│   │   ├── LakeListPage.tsx    # Route / — sort controls, pinned/unpinned sections
│   │   ├── LakeCard.tsx        # One lake with pin button and 7-day strip
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
│   ├── useLakeDetail.ts        # Fetches single lake detail
│   ├── useUserLocation.ts      # Browser Geolocation API wrapper; persists opt-in
│   └── usePreferences.ts       # Pins + sort choice; persists to localStorage
└── utils/
    ├── weatherCodes.ts         # WMO code → label + icon map
    ├── formatters.ts           # Temperature, wind, date, unit conversions
    ├── lakeConditionScore.ts   # Good / Fair / Poor scoring logic
    ├── distance.ts             # Haversine distance in miles
    └── sorting.ts              # sortLakes() — applies sort option to a lake array
```

**Routing:** React Router v6 — `/` for the lake list, `/lakes/:id` for detail.

**API proxying:** In local Docker, nginx proxies `/api/*` → backend container. On Cloud Run, `BACKEND_URL` env var controls the target.

**User preferences** are stored in two `localStorage` keys:

| Key | Contents |
|-----|----------|
| `preferences` | `{ pinnedLakes: string[], sortBy: SortOption }` |
| `sortByDistance` | Set by `useUserLocation` when location access is granted |

---

## Lakes

Configured in `backend/config/lakes.yaml`. Each lake specifies a `conditions_provider` (used for the tile display and detail banner) and an optional `history_provider` (used for the historical chart).

| Lake | Conditions | History | Notes |
|------|-----------|---------|-------|
| Deer Creek Reservoir | state_parks | usbr | Temp + level %; 90-day elevation history |
| Pineview Reservoir | state_parks | usbr | Temp + level %; 90-day elevation history |
| East Canyon Reservoir | state_parks | usbr | Temp + level %; 90-day elevation history |
| Rockport Reservoir | state_parks | usbr | Temp + level %; 90-day elevation history |
| Echo Reservoir | state_parks | usbr | Temp + level %; 90-day elevation history |
| Bear Lake | usgs | — | Level (elevation ft) + temp; 90-day history |
| Jordanelle Reservoir | state_parks | usbr | Temp + level %; 90-day elevation history |
| Utah Lake | cuwcd | — | Level % only; 30-day history |
| Willard Bay | state_parks | usbr | Temp + level %; 90-day elevation history |
| Lake Powell | lake_powell | — | Elevation (ft MSL) + level %; 365-day history |
| Quail Creek Reservoir | state_parks | usbr | Temp + level %; 90-day elevation history |
| Sand Hollow Reservoir | state_parks | usbr | Temp + level %; 90-day elevation history |

---

## Surfing Condition Score

Each day is rated based on wind and rain. Lightning always overrides to Poor. The **Legend** button in the header shows these thresholds at a glance.

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
│   ├── test_cache.py                 # CachingAggregator TTL and thread-safety
│   ├── test_aggregator.py
│   ├── test_open_meteo_provider.py   # httpx mocked via respx
│   ├── test_usgs_provider.py         # httpx mocked via respx
│   ├── test_lake_powell_provider.py  # httpx mocked via respx
│   ├── test_usbr_provider.py         # httpx mocked via respx
│   ├── test_lake_data_script.py      # CLI script tested via Click's CliRunner
│   ├── test_registry.py
│   └── test_config.py
└── integration/
    └── test_api_routes.py            # FastAPI TestClient, providers mocked
```

No external network calls are made during tests — all HTTP is mocked.

### Frontend

```bash
docker compose --profile test run --rm frontend-test
```

Test layout:

```
frontend/tests/
├── setup.ts
├── components/
│   ├── DayBadge.test.tsx
│   ├── LakeCard.test.tsx         # includes pin button tests
│   └── WindIndicator.test.tsx
├── hooks/
│   ├── useUserLocation.test.ts
│   └── usePreferences.test.ts
└── utils/
    ├── weatherCodes.test.ts
    ├── lakeConditionScore.test.ts  # includes threshold boundary tests
    ├── distance.test.ts
    ├── sorting.test.ts
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
  usgs_site_id: null
  conditions_provider: state_parks
  state_park_slug: sand-hollow
```

If the lake has both a scraper source (for current conditions) and an automated source (for history), specify both:

```yaml
- id: my_lake
  conditions_provider: state_parks   # used for tiles and detail banner
  history_provider: cuwcd            # used for historical chart
  state_park_slug: my-lake
  cuwcd_set_name: public_ml
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
        return lake.conditions_provider == "my_state"

    def get_conditions(self, lake: LakeConfig) -> LakeConditions:
        # fetch from state API and return LakeConditions
        ...
```

2. Register it in `backend/surf_weather/main.py` inside `_build_aggregator()`:

```python
from .providers.lake_data.my_state import MyStateProvider

registry.register(MyStateProvider())
```

3. Add lakes to `lakes.yaml` with `conditions_provider: my_state`.

---

## Deployment — Google Cloud Run

Both containers are deployed as separate Cloud Run services. The frontend proxies API calls to the backend using the `BACKEND_URL` environment variable.

### One-command deploy

```bash
./deploy.sh
```

`deploy.sh` authenticates Docker with Artifact Registry, builds and pushes both images, then deploys backend followed by frontend.

### Prerequisites (first time only)

```bash
gcloud auth login
gcloud config set project surf-weather-492803
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
```

### Manual steps

```bash
# Authenticate Docker with Artifact Registry (WSL)
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin https://us-central1-docker.pkg.dev

# Build and push
docker compose build
docker compose push

# Deploy backend
gcloud run deploy surf-backend \
  --image us-central1-docker.pkg.dev/surf-weather-492803/web/backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated

# Deploy frontend
gcloud run deploy surf-frontend \
  --image us-central1-docker.pkg.dev/surf-weather-492803/web/frontend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars BACKEND_URL=https://surf-backend-476326886107.us-central1.run.app
```

### Live URLs

| Service | URL |
|---------|-----|
| Backend | `https://surf-backend-476326886107.us-central1.run.app` |
| Frontend | `https://surf-fronted-476326886107.us-central1.run.app` |
