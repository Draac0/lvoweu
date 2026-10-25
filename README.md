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
uv sync          # creates .venv and installs dependencies
uv run pytest    # run tests
uv run ruff check .
```

_More sections (frontend, Docker, deployment, assumptions, AI usage) are added as the project is built._
