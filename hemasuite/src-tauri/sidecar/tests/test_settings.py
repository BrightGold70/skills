"""TDD tests for Settings API (Task 4.3).

Settings stored in ~/HemaSuite/settings.json with defaults.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from server import app


@pytest.fixture(autouse=True)
def mock_settings_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HEMASUITE_CONFIG_DIR", str(tmp_path))


@pytest.mark.anyio
async def test_get_settings_defaults():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "r_path" in data
    assert "python_path" in data
    assert "output_dir" in data
    assert "theme" in data
    assert data["theme"] == "light"


@pytest.mark.anyio
async def test_update_settings():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.patch("/settings", json={
            "theme": "dark",
            "default_journal": "Blood",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["theme"] == "dark"
    assert data["default_journal"] == "Blood"


@pytest.mark.anyio
async def test_settings_persist_across_reads():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.patch("/settings", json={"theme": "dark"})
        resp = await client.get("/settings")
    assert resp.status_code == 200
    assert resp.json()["theme"] == "dark"


@pytest.mark.anyio
async def test_update_settings_partial():
    """PATCH should merge, not replace all settings."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.patch("/settings", json={"theme": "dark"})
        await client.patch("/settings", json={"default_journal": "JCO"})
        resp = await client.get("/settings")
    data = resp.json()
    assert data["theme"] == "dark"
    assert data["default_journal"] == "JCO"
