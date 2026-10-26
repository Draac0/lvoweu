# Wind Forecast Monitor

Shows UK national wind generation forecasts as they stood at day-ahead decision time, and measures how accurate they were, for deliveries in January 2026. Data source: Elexon BMRS (`FUELHH` actuals, `WINDFOR` forecasts).

## Repository layout

| Path | Contents |
|---|---|
| `backend/` | Python (FastAPI) service: data fetching, analysis, API |
| `backend/app/` | Application package |
| `backend/tests/` | Unit tests (pytest) |

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
