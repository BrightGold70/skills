"""HemaSuite Python sidecar — FastAPI server wrapping HPW and CSA."""

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.hpw import router as hpw_router
from routers.csa import router as csa_router
from routers.projects import router as projects_router
from routers.settings import router as settings_router

app = FastAPI(title="HemaSuite Sidecar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:1420"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(hpw_router)
app.include_router(csa_router)
app.include_router(projects_router)
app.include_router(settings_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "python": sys.version,
        "hpw": Path(os.environ.get("HPW_PATH", "")).exists(),
        "csa": Path(os.environ.get("CSA_PATH", "")).exists(),
    }
