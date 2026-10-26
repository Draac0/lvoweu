# Wind Forecast Monitor

Shows UK national wind generation forecasts as they stood at day-ahead decision time, and measures how accurate they were, for deliveries in January 2026. Data source: Elexon BMRS (`FUELHH` actuals, `WINDFOR` forecasts).

## Repository layout

| Path | Contents |
|---|---|
| `backend/` | Python (FastAPI) service: data fetching, analysis, API |
| `backend/app/` | Application package |
| `backend/tests/` | Unit tests (pytest) |
| `backend/openapi.json` | API contract, generated from the FastAPI app |
| `frontend/` | React + TypeScript app (Vite) |
| `frontend/src/api/` | Typed API client; `schema.d.ts` is generated from `openapi.json` |
| `frontend/src/pages/` | Login and dashboard screens |
| `frontend/src/components/` | UI pieces (summary tiles, charts) |
| `frontend/src/lib/` | Formatting and URL-state helpers |

## Data source: Elexon BMRS

Both datasets are public (no API key) and return a JSON array. Base URL: `https://data.elexon.co.uk/bmrs/api/v1`. All times are UTC, all power values are MW.

### Actual generation: `FUELHH`

```
GET /datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31&fuelType=WIND
```

```json
[
  {
    "dataset": "FUELHH",
    "publishTime": "2026-01-15T18:30:00Z",
    "startTime": "2026-01-15T18:00:00Z",
    "settlementDate": "2026-01-15",
    "settlementPeriod": 37,
    "fuelType": "WIND",
    "generation": 7672
  }
]
```

One row per half-hour: what all metered wind farms in Great Britain actually generated.

| Field | Meaning | Used? |
|---|---|---|
| `startTime` | Start of the 30-minute period the value describes | Yes: the time key |
| `generation` | Average wind output over that period (MW) | Yes |
| `fuelType` | Generation type; we request `WIND` only | Filter |
| `publishTime` | When Elexon published the value. If a period is republished, we keep the latest | Dedup only |
| `settlementDate`, `settlementPeriod` | The market's own clock: 48 half-hour periods per UK day (period 37 on 15 Jan = 18:00) | No |

January 2026: 1,488 rows (31 days × 48).

### Forecasts: `WINDFOR`

```
GET /datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-28T00:00:00Z&publishDateTimeTo=2026-02-01T00:00:00Z
```

```json
[
  {
    "dataset": "WINDFOR",
    "publishTime": "2026-01-14T07:30:00Z",
    "startTime": "2026-01-15T18:00:00Z",
    "generation": 8962
  }
]
```

Read as: *"At 07:30 on 14 Jan, the forecast for 18:00 on 15 Jan was 8,962 MW."*

| Field | Meaning |
|---|---|
| `publishTime` | When the forecast was made |
| `startTime` | The hour being forecast |
| `generation` | Forecast wind output for that hour (MW) |

How the data is shaped:

- **Batches.** Elexon publishes a new forecast 8 times a day (02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30 UTC). Each publish is a batch of 73 hourly rows sharing one `publishTime`.
- **Hourly, not half-hourly.** Forecasts only exist on the hour, so they are compared with the on-the-hour actuals.
- **Overlapping.** Each batch covers roughly 25 hours in the past to 66 hours ahead, so every target hour is forecast about 20 times as it approaches. The rows describing the past (`startTime` ≤ `publishTime`) are not forecasts and are dropped.
- **Filtered by publish time.** The API selects by `publishTime`, so forecasts for early-January deliveries are fetched from late December.

January 2026 analysis window: 280 publishes, 20,440 rows fetched, 16,239 kept after dropping past rows.

## Running locally

Backend (requires [uv](https://docs.astral.sh/uv/)):

```bash
cd backend
uv sync                    # creates .venv and installs dependencies
uv run python -m app.data  # fetch January data from Elexon into data/cache/
uv run pytest              # run tests
uv run ruff check .
uv run uvicorn app.main:app --reload   # API on http://localhost:8000
```

Interactive API docs: http://localhost:8000/docs

The API contract is committed as [`backend/openapi.json`](backend/openapi.json) and the frontend's TypeScript types are generated from it, so client and server can't drift apart. After changing routes or schemas, run `uv run python -m app.export_openapi`; a test fails if you forget.

Frontend (requires Node 22+), in a second terminal while the API runs:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api to the API on :8000)
npm run gen:api    # regenerate src/api/schema.d.ts after the API changes
npm run typecheck
npm run lint
```

### Demo login

All data endpoints require a login. There is one demo user, hard-coded to showcase the login flow:

- Email: `trader@example.com`
- Password: `windpower2026`

`POST /api/v1/auth/login` returns a signed token (JWT, valid 8 hours); send it as `Authorization: Bearer <token>`. In `/docs`, use the **Authorize** button. Override `DEMO_EMAIL`, `DEMO_PASSWORD` and `JWT_SECRET` via environment variables in any real deployment.

| Endpoint | Returns |
|---|---|
| `POST /api/v1/auth/login` | Token for the demo user |
| `GET /api/v1/health` | Status and loaded row counts (public) |
| `GET /api/v1/actuals?start=&end=` | Half-hourly actual wind generation |
| `GET /api/v1/decision-forecasts?cutoff=09:00` | Per hour: the forecast available at the cutoff (UK time, day before delivery), the actual, the error; plus summary stats |
| `GET /api/v1/forecasts?start_time=` | Every forecast published for one target hour |
| `GET /api/v1/accuracy/by-horizon` | Mean absolute error grouped by forecast lead time |

_More sections (frontend, Docker, deployment, assumptions, AI usage) are added as the project is built._
