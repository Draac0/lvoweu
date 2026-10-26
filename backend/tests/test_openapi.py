from app.export_openapi import SPEC_PATH, render_spec


def test_committed_spec_matches_the_api():
    # Fails when routes or schemas change without regenerating the spec (and frontend types).
    assert SPEC_PATH.read_text() == render_spec(), (
        "openapi.json is out of date: run `uv run python -m app.export_openapi`"
    )
