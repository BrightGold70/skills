"""TDD tests for HPW-CSA Integration API (Task 4.2).

The integration endpoint reads hpw_manifest.json from a project's analysis/
directory and returns linkable artifacts (tables, figures) for the manuscript.
"""

import json
import pytest
from httpx import AsyncClient, ASGITransport
from server import app


@pytest.fixture
def project_with_analysis(tmp_path, monkeypatch):
    """Create a project with CSA analysis outputs."""
    monkeypatch.setenv("HEMASUITE_PROJECTS_DIR", str(tmp_path))

    project_dir = tmp_path / "my-study"
    project_dir.mkdir()
    (project_dir / "project.json").write_text(json.dumps({
        "name": "My Study", "slug": "my-study",
    }))
    (project_dir / "manuscript").mkdir()
    (project_dir / "data").mkdir()
    (project_dir / "analysis").mkdir()
    (project_dir / "exports").mkdir()

    # Simulate CSA outputs
    (project_dir / "analysis" / "Tables").mkdir()
    (project_dir / "analysis" / "Figures").mkdir()
    (project_dir / "analysis" / "Tables" / "table1.docx").write_bytes(b"fake")
    (project_dir / "analysis" / "Tables" / "table2.docx").write_bytes(b"fake")
    (project_dir / "analysis" / "Figures" / "km_plot.png").write_bytes(b"fake")
    (project_dir / "analysis" / "Figures" / "forest_plot.png").write_bytes(b"fake")

    # Simulate hpw_manifest.json
    manifest = {
        "tables": [
            {"name": "table1.docx", "caption": "Baseline characteristics"},
            {"name": "table2.docx", "caption": "Efficacy outcomes"},
        ],
        "figures": [
            {"name": "km_plot.png", "caption": "Kaplan-Meier survival"},
            {"name": "forest_plot.png", "caption": "Subgroup analysis"},
        ],
    }
    (project_dir / "analysis" / "hpw_manifest.json").write_text(
        json.dumps(manifest, indent=2)
    )
    return project_dir


@pytest.fixture
def empty_project(tmp_path, monkeypatch):
    """Create a project without analysis outputs."""
    monkeypatch.setenv("HEMASUITE_PROJECTS_DIR", str(tmp_path))
    project_dir = tmp_path / "empty-study"
    project_dir.mkdir()
    (project_dir / "project.json").write_text(json.dumps({
        "name": "Empty Study", "slug": "empty-study",
    }))
    for d in ("manuscript", "data", "analysis", "exports"):
        (project_dir / d).mkdir()
    return project_dir


@pytest.mark.anyio
async def test_get_artifacts_with_manifest(project_with_analysis):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/projects/my-study/artifacts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tables"]) == 2
    assert len(data["figures"]) == 2
    assert data["tables"][0]["caption"] == "Baseline characteristics"


@pytest.mark.anyio
async def test_get_artifacts_no_manifest(empty_project):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/projects/empty-study/artifacts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tables"] == []
    assert data["figures"] == []


@pytest.mark.anyio
async def test_get_artifacts_project_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("HEMASUITE_PROJECTS_DIR", str(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/projects/nonexistent/artifacts")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_link_artifact_to_manuscript(project_with_analysis):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/projects/my-study/artifacts/link", json={
            "type": "figure",
            "name": "km_plot.png",
            "insert_after": "Results",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["linked"] is True
    assert data["artifact"] == "km_plot.png"
