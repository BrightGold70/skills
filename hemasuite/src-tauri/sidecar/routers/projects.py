"""Projects API router — CRUD for HemaSuite project directories."""

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["projects"])

SUBDIRS = ["manuscript", "data", "analysis", "exports"]


def _projects_dir() -> Path:
    base = os.environ.get(
        "HEMASUITE_PROJECTS_DIR",
        str(Path.home() / "HemaSuite" / "projects"),
    )
    return Path(base)


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _read_manifest(project_dir: Path) -> dict:
    manifest_path = project_dir / "project.json"
    if not manifest_path.exists():
        return {}
    with open(manifest_path) as f:
        return json.load(f)


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""


@router.get("")
async def list_projects():
    base = _projects_dir()
    if not base.exists():
        return []
    projects = []
    for d in sorted(base.iterdir()):
        if d.is_dir():
            manifest = _read_manifest(d)
            if manifest:
                projects.append(manifest)
    return projects


@router.post("", status_code=201)
async def create_project(req: CreateProjectRequest):
    slug = _slugify(req.name)
    base = _projects_dir()
    project_dir = base / slug

    if project_dir.exists():
        raise HTTPException(409, f"Project '{slug}' already exists")

    project_dir.mkdir(parents=True, exist_ok=True)
    for subdir in SUBDIRS:
        (project_dir / subdir).mkdir(exist_ok=True)

    manifest = {
        "name": req.name,
        "slug": slug,
        "description": req.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(project_dir / "project.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return JSONResponse(content=manifest, status_code=201)


@router.get("/{slug}")
async def get_project(slug: str):
    project_dir = _projects_dir() / slug
    if not project_dir.exists():
        raise HTTPException(404, f"Project '{slug}' not found")
    manifest = _read_manifest(project_dir)
    if not manifest:
        raise HTTPException(404, f"Project '{slug}' has no manifest")
    return manifest


@router.delete("/{slug}")
async def delete_project(slug: str):
    project_dir = _projects_dir() / slug
    if not project_dir.exists():
        raise HTTPException(404, f"Project '{slug}' not found")
    shutil.rmtree(project_dir)
    return {"deleted": slug}


# --- HPW-CSA Integration (Task 4.2) ---


def _get_project_dir(slug: str) -> Path:
    project_dir = _projects_dir() / slug
    if not project_dir.exists():
        raise HTTPException(404, f"Project '{slug}' not found")
    return project_dir


@router.get("/{slug}/artifacts")
async def get_artifacts(slug: str):
    project_dir = _get_project_dir(slug)
    manifest_path = project_dir / "analysis" / "hpw_manifest.json"

    if not manifest_path.exists():
        return {"tables": [], "figures": []}

    with open(manifest_path) as f:
        return json.load(f)


class LinkArtifactRequest(BaseModel):
    type: str  # "table" or "figure"
    name: str
    insert_after: str = ""


@router.post("/{slug}/artifacts/link")
async def link_artifact(slug: str, req: LinkArtifactRequest):
    project_dir = _get_project_dir(slug)
    source_dir = "Tables" if req.type == "table" else "Figures"
    source_path = project_dir / "analysis" / source_dir / req.name

    if not source_path.exists():
        raise HTTPException(404, f"Artifact not found: {req.name}")

    # Copy artifact to manuscript directory for linking
    dest = project_dir / "manuscript" / req.name
    shutil.copy2(source_path, dest)

    return {"linked": True, "artifact": req.name, "destination": str(dest)}
