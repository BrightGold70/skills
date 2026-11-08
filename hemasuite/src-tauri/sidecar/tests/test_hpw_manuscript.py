import pytest
from httpx import AsyncClient, ASGITransport
from server import app


@pytest.mark.anyio
async def test_get_manuscript_new_phase(tmp_path, monkeypatch):
    """GET returns empty string for a new phase."""
    monkeypatch.setenv("HEMASUITE_PROJECTS_DIR", str(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/hpw/manuscript/test-project/1")
    assert resp.status_code == 200
    assert resp.json()["content"] == ""


@pytest.mark.anyio
async def test_save_and_get_manuscript(tmp_path, monkeypatch):
    """PUT saves content, GET retrieves it."""
    monkeypatch.setenv("HEMASUITE_PROJECTS_DIR", str(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        put_resp = await client.put(
            "/hpw/manuscript/test-project/1",
            json={"content": "<p>Introduction text</p>"},
        )
        assert put_resp.status_code == 200

        get_resp = await client.get("/hpw/manuscript/test-project/1")
        assert get_resp.status_code == 200
        assert get_resp.json()["content"] == "<p>Introduction text</p>"


@pytest.mark.anyio
async def test_pipeline_endpoint_exists():
    """POST /csa/pipeline endpoint should exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/csa/pipeline", json={
            "data_path": "/tmp/test.csv",
            "output_dir": "/tmp/out",
        })
    # Should not be 404 (endpoint exists), may be 503 if CSA not configured
    assert resp.status_code != 404


@pytest.mark.anyio
async def test_save_lands_in_the_projects_dir_set_at_request_time(tmp_path, monkeypatch):
    """HEMASUITE_PROJECTS_DIR is read per request, not frozen at import (it used to default to the cwd)."""
    monkeypatch.setenv("HEMASUITE_PROJECTS_DIR", str(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put("/hpw/manuscript/p1/2", json={"content": "<p>x</p>"})
    assert resp.status_code == 200
    assert (tmp_path / "p1" / "phase-2.html").read_text(encoding="utf-8") == "<p>x</p>"
