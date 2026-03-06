"""HPW API router — wraps HPW CLI commands as REST endpoints."""

import os
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/hpw", tags=["hpw"])

HPW_PATH = Path(os.environ.get("HPW_PATH", ""))

PHASES = [
    {"id": 1, "name": "Topic Development", "module": "phase1_topic"},
    {"id": 2, "name": "Research & Literature", "module": "phase2_research"},
    {"id": 3, "name": "Journal Selection", "module": "phase3_journal"},
    {"id": 4, "name": "Manuscript Drafting", "module": "phase4_drafting"},
    {"id": 5, "name": "Quality Analysis", "module": "phase5_quality"},
    {"id": 6, "name": "Reference Management", "module": "phase6_references"},
    {"id": 7, "name": "Prose & Style", "module": "phase7_prose"},
    {"id": 8, "name": "Peer Review", "module": "phase8_peerreview"},
    {"id": 9, "name": "Publication", "module": "phase9_publication"},
    {"id": 10, "name": "Resubmission", "module": "phase10_resubmission"},
]


def _ensure_hpw():
    if HPW_PATH.exists():
        sys.path.insert(0, str(HPW_PATH))
    else:
        raise HTTPException(503, "HPW_PATH not configured or not found")


@router.get("/phases")
async def list_phases():
    return PHASES


PROJECTS_DIR = Path(os.environ.get("HEMASUITE_PROJECTS_DIR", "")).resolve()


class ManuscriptBody(BaseModel):
    content: str


@router.get("/manuscript/{project_id}/{phase_id}")
async def get_manuscript(project_id: str, phase_id: int):
    """Read phase HTML content from project directory."""
    file_path = PROJECTS_DIR / project_id / f"phase-{phase_id}.html"
    if not file_path.exists():
        return {"content": ""}
    return {"content": file_path.read_text(encoding="utf-8")}


@router.put("/manuscript/{project_id}/{phase_id}")
async def save_manuscript(project_id: str, phase_id: int, body: ManuscriptBody):
    """Save phase HTML content to project directory."""
    project_dir = PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    file_path = project_dir / f"phase-{phase_id}.html"
    file_path.write_text(body.content, encoding="utf-8")
    return {"saved": True, "path": str(file_path)}


class InsertResultsRequest(BaseModel):
    project_id: str
    phase_id: int
    csa_output_dir: str
    insert_mode: str = "append"


@router.post("/insert-results")
async def insert_results(req: InsertResultsRequest):
    """Read CSA output files and insert into manuscript HTML."""
    output_dir = Path(req.csa_output_dir)
    snippets: list[str] = []

    if output_dir.exists():
        for f in sorted(output_dir.iterdir()):
            if f.suffix == ".html":
                snippets.append(f.read_text(encoding="utf-8"))
            elif f.suffix == ".json":
                snippets.append(f'<div data-chart=\'{f.read_text(encoding="utf-8")}\'></div>')
            elif f.suffix in (".png", ".jpg", ".jpeg"):
                import base64
                data = base64.b64encode(f.read_bytes()).decode()
                mime = "image/png" if f.suffix == ".png" else "image/jpeg"
                snippets.append(f'<img src="data:{mime};base64,{data}" alt="{f.stem}" />')

    # Read current manuscript
    manuscript_path = PROJECTS_DIR / req.project_id / f"phase-{req.phase_id}.html"
    current = manuscript_path.read_text(encoding="utf-8") if manuscript_path.exists() else ""

    insert_html = "\n".join(snippets)
    if req.insert_mode == "placeholder" and "{{CSA_RESULT}}" in current:
        updated = current.replace("{{CSA_RESULT}}", insert_html, 1)
    else:
        updated = current + "\n" + insert_html if current else insert_html

    # Save updated manuscript
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(updated, encoding="utf-8")

    return {"content": updated, "items_inserted": len(snippets)}


class PubMedSearchRequest(BaseModel):
    query: str
    max_results: int = 20
    time_period: str = "5y"


@router.post("/search-pubmed")
async def search_pubmed(req: PubMedSearchRequest):
    _ensure_hpw()
    try:
        from tools.pubmed_verifier import PubMedVerifier
        verifier = PubMedVerifier()
        results = verifier.search(req.query, max_results=req.max_results)
        return {"results": results, "count": len(results)}
    except ImportError as e:
        raise HTTPException(503, f"HPW module not available: {e}")
    except Exception as e:
        raise HTTPException(500, str(e))
