import pytest
from httpx import AsyncClient, ASGITransport
from server import app


@pytest.mark.anyio
async def test_csa_scripts_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/csa/scripts")
    # Without CSA_PATH configured, should return 503
    assert resp.status_code in (200, 503)


@pytest.mark.anyio
async def test_csa_run_script_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/csa/run", json={
            "script": "nonexistent.R",
            "data_path": "/tmp/test.csv",
        })
    assert resp.status_code in (404, 503)
