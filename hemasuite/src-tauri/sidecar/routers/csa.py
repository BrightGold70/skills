"""CSA API router — wraps CSA R scripts and CRF pipeline as REST endpoints."""

import asyncio
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/csa", tags=["csa"])

CSA_PATH = Path(os.environ.get("CSA_PATH", ""))
RSCRIPT = os.environ.get("RSCRIPT_PATH", "Rscript")


@router.get("/scripts")
async def list_scripts():
    scripts_dir = CSA_PATH / "scripts"
    if not scripts_dir.exists():
        raise HTTPException(503, "CSA_PATH not configured")
    scripts = []
    for f in sorted(scripts_dir.glob("*.R")):
        scripts.append({"name": f.name, "path": str(f)})
    for f in sorted(scripts_dir.glob("*.py")):
        if f.name.startswith(("0", "1")):
            scripts.append({"name": f.name, "path": str(f)})
    return scripts


class RunScriptRequest(BaseModel):
    script: str
    data_path: str = ""
    output_dir: str = ""
    args: dict = {}


@router.post("/run")
async def run_script(req: RunScriptRequest):
    script_path = CSA_PATH / "scripts" / req.script
    if not script_path.exists():
        raise HTTPException(404, f"Script not found: {req.script}")

    env = {**os.environ}
    if req.output_dir:
        env["CSA_OUTPUT_DIR"] = req.output_dir
        env["CRF_OUTPUT_DIR"] = req.output_dir

    if req.script.endswith(".R"):
        cmd = [RSCRIPT, str(script_path)]
        if req.data_path:
            cmd.append(req.data_path)
    else:
        cmd = ["python3", str(script_path)]

    # Using create_subprocess_exec (not shell) — safe from injection
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await proc.communicate()

    return {
        "exit_code": proc.returncode,
        "stdout": stdout.decode(errors="replace"),
        "stderr": stderr.decode(errors="replace"),
    }
