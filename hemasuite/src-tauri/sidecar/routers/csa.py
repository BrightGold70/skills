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


class RunPipelineRequest(BaseModel):
    data_path: str
    output_dir: str
    scripts: list[str] = []


class PipelineStepResult(BaseModel):
    step: str
    status: str
    exit_code: int | None = None
    output: str = ""
    duration_ms: int = 0


@router.post("/pipeline")
async def run_pipeline(req: RunPipelineRequest):
    """Run CRF pipeline: extract -> validate -> analyze -> report."""
    import time

    scripts_dir = CSA_PATH / "scripts"
    if not scripts_dir.exists():
        raise HTTPException(503, "CSA_PATH not configured")

    all_scripts = sorted(scripts_dir.glob("*.R")) + sorted(scripts_dir.glob("*.py"))
    if req.scripts:
        all_scripts = [s for s in all_scripts if s.name in req.scripts]

    step_names = ["extract", "validate", "analyze", "report"]
    results: list[dict] = []

    for i, script in enumerate(all_scripts[:4]):
        step_name = step_names[i] if i < len(step_names) else f"step-{i+1}"
        start = time.monotonic()

        env = {**os.environ}
        if req.output_dir:
            env["CSA_OUTPUT_DIR"] = req.output_dir
            env["CRF_OUTPUT_DIR"] = req.output_dir

        if script.suffix == ".R":
            cmd = [RSCRIPT, str(script)]
            if req.data_path:
                cmd.append(req.data_path)
        else:
            cmd = ["python3", str(script)]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, stderr = await proc.communicate()
            elapsed = int((time.monotonic() - start) * 1000)

            results.append({
                "step": step_name,
                "status": "done" if proc.returncode == 0 else "error",
                "exit_code": proc.returncode,
                "output": stdout.decode(errors="replace") or stderr.decode(errors="replace"),
                "duration_ms": elapsed,
            })

            if proc.returncode != 0:
                for j in range(i + 1, min(len(all_scripts), 4)):
                    sn = step_names[j] if j < len(step_names) else f"step-{j+1}"
                    results.append({"step": sn, "status": "pending", "output": "", "duration_ms": 0})
                break
        except Exception as e:
            elapsed = int((time.monotonic() - start) * 1000)
            results.append({
                "step": step_name,
                "status": "error",
                "exit_code": None,
                "output": str(e),
                "duration_ms": elapsed,
            })
            break

    return {"steps": results}


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
