import pytest
from httpx import AsyncClient, ASGITransport
from server import app


@pytest.mark.anyio
async def test_hpw_phases_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/hpw/phases")
    assert resp.status_code == 200
    phases = resp.json()
    assert len(phases) == 10
    assert phases[0]["name"] == "Topic Development"


@pytest.mark.anyio
async def test_hpw_phases_have_required_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/hpw/phases")
    phases = resp.json()
    for phase in phases:
        assert "id" in phase
        assert "name" in phase
        assert "module" in phase
