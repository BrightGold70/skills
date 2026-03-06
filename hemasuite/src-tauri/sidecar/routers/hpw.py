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
