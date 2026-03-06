"""TDD tests for Project Manager API (Task 4.1).

Projects are stored in ~/HemaSuite/projects/<slug>/ with a project.json manifest.
Each project holds manuscript, data, analysis, and exports subdirectories.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from server import app

# Use a temp directory instead of the real ~/HemaSuite
@pytest.fixture(autouse=True)
def mock_projects_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HEMASUITE_PROJECTS_DIR", str(tmp_path))


@pytest.mark.anyio
async def test_list_projects_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/projects")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_create_project():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/projects", json={
            "name": "My CML Study",
            "description": "Phase III asciminib analysis",
        })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My CML Study"
    assert data["slug"] == "my-cml-study"
    assert "created_at" in data


@pytest.mark.anyio
async def test_create_project_creates_subdirectories(tmp_path, monkeypatch):
    monkeypatch.setenv("HEMASUITE_PROJECTS_DIR", str(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/projects", json={"name": "Test Project"})

    project_dir = tmp_path / "test-project"
    assert project_dir.exists()
    assert (project_dir / "manuscript").is_dir()
    assert (project_dir / "data").is_dir()
    assert (project_dir / "analysis").is_dir()
    assert (project_dir / "exports").is_dir()
    assert (project_dir / "project.json").is_file()


@pytest.mark.anyio
async def test_list_projects_after_create():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/projects", json={"name": "Study Alpha"})
        await client.post("/projects", json={"name": "Study Beta"})
        resp = await client.get("/projects")
    assert resp.status_code == 200
    projects = resp.json()
    assert len(projects) == 2
    names = {p["name"] for p in projects}
    assert names == {"Study Alpha", "Study Beta"}


@pytest.mark.anyio
async def test_get_project_by_slug():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/projects", json={"name": "My Study"})
        resp = await client.get("/projects/my-study")
    assert resp.status_code == 200
    assert resp.json()["name"] == "My Study"


@pytest.mark.anyio
async def test_get_project_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/projects/nonexistent")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_project():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/projects", json={"name": "To Delete"})
        resp = await client.delete("/projects/to-delete")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == "to-delete"


@pytest.mark.anyio
async def test_delete_project_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete("/projects/nonexistent")
    assert resp.status_code == 404
