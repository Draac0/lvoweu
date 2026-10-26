"""Write the API's OpenAPI spec to backend/openapi.json.

The frontend generates its TypeScript types from this file, so rerun this after any
change to routes or schemas: `uv run python -m app.export_openapi`.
"""

import json
from pathlib import Path

from app.main import app

SPEC_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def render_spec() -> str:
    return json.dumps(app.openapi(), indent=2) + "\n"


if __name__ == "__main__":
    SPEC_PATH.write_text(render_spec())
    print(f"Wrote {SPEC_PATH}")
