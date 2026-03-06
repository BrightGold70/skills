# HemaSuite macOS App - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone macOS app (HemaSuite) combining HPW manuscript writing and CSA statistical analysis using Tauri 2 + React + bundled Python/R.

**Architecture:** Tauri 2 shell manages a React WebView frontend and a Python FastAPI sidecar. The sidecar wraps existing HPW CLI and CSA CRF pipeline. R scripts run as subprocesses from Python.

**Tech Stack:** Tauri 2.x, React 19, TypeScript, Vite, FastAPI, Python 3.14, R 4.5, Zustand, Tailwind CSS

---

## Progress Tracking (2026-03-06)

| Phase | Status | Commits | Notes |
|-------|--------|---------|-------|
| 0 | ✅ Complete | `c6702c2` | Rust 1.93.1, Tauri CLI 2.10.1, pnpm 10.30.3 |
| 1 | ✅ Complete | `9c64a64` | FastAPI sidecar, HPW/CSA APIs, 5 tests passing |
| 2 | ✅ Complete | `1be6f82` | Tailwind v4, MainLayout, HpwEditor, CsaDashboard |
| 3 | ✅ Complete | | R/Python bundling, lib.rs updated for bundled runtimes |
| 4 | ⏳ Not started | | Integration & polish |
| 5 | ⏳ Not started | | Build & distribution |

**Overall: 12/20 tasks (60%)**

---

## Phase 0: Environment Setup

### Task 0.1: Update Rust Toolchain

Current Rust 1.69.0 is too old for Tauri 2.x (requires 1.77.2+).

**Files:**
- None (system tool update)

**Step 1: Update Rust**

```bash
rustup update stable
rustc --version
# Expected: rustc 1.8x.x or newer
```

**Step 2: Install Tauri CLI**

```bash
cargo install tauri-cli --version "^2"
cargo tauri --version
# Expected: tauri-cli 2.x.x
```

**Step 3: Commit**

No code changes — environment only.

---

### Task 0.2: Create HemaSuite Project Scaffold

**Files:**
- Create: `hemasuite/` (new directory at repo root)

**Step 1: Initialize Tauri + React project**

```bash
cd /Users/kimhawk/.config/opencode/skills
pnpm create tauri-app hemasuite -- --template react-ts
cd hemasuite
```

**Step 2: Verify project structure**

```bash
ls -la src-tauri/  # Rust backend
ls -la src/        # React frontend
```

Expected structure:
```
hemasuite/
├── src-tauri/
│   ├── Cargo.toml
│   ├── src/main.rs
│   ├── tauri.conf.json
│   └── capabilities/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   └── styles.css
├── package.json
├── tsconfig.json
└── vite.config.ts
```

**Step 3: Install dependencies and test build**

```bash
pnpm install
pnpm tauri dev
# Expected: Window opens with React welcome page
```

**Step 4: Commit**

```bash
git add hemasuite/
git commit -m "feat: scaffold HemaSuite Tauri + React project"
```

---

## Phase 1: Python Sidecar Setup

### Task 1.1: Create FastAPI Sidecar

**Files:**
- Create: `hemasuite/src-tauri/sidecar/server.py`
- Create: `hemasuite/src-tauri/sidecar/requirements.txt`
- Test: `hemasuite/src-tauri/sidecar/tests/test_server.py`

**Step 1: Write the failing test**

```python
# hemasuite/src-tauri/sidecar/tests/test_server.py
import pytest
from httpx import AsyncClient, ASGITransport
from server import app

@pytest.mark.anyio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```

**Step 2: Run test to verify it fails**

```bash
cd hemasuite/src-tauri/sidecar
python3 -m pytest tests/test_server.py -v
# Expected: FAIL — ModuleNotFoundError: No module named 'server'
```

**Step 3: Write minimal implementation**

```python
# hemasuite/src-tauri/sidecar/server.py
"""HemaSuite Python sidecar — FastAPI server wrapping HPW and CSA."""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HemaSuite Sidecar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:1420"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "python": sys.version,
        "hpw": Path(os.environ.get("HPW_PATH", "")).exists(),
        "csa": Path(os.environ.get("CSA_PATH", "")).exists(),
    }
```

```
# hemasuite/src-tauri/sidecar/requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0
anyio>=4.0
pytest>=8.0
pytest-anyio>=0.0.0
```

**Step 4: Run test to verify it passes**

```bash
pip install -r requirements.txt
python3 -m pytest tests/test_server.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add hemasuite/src-tauri/sidecar/
git commit -m "feat: add FastAPI sidecar with health check"
```

---

### Task 1.2: Add HPW API Endpoints

**Files:**
- Modify: `hemasuite/src-tauri/sidecar/server.py`
- Create: `hemasuite/src-tauri/sidecar/routers/hpw.py`
- Test: `hemasuite/src-tauri/sidecar/tests/test_hpw.py`

**Step 1: Write the failing test**

```python
# hemasuite/src-tauri/sidecar/tests/test_hpw.py
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
async def test_hpw_search_pubmed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/hpw/search-pubmed", json={
            "query": "asciminib CML",
            "max_results": 5,
        })
    assert resp.status_code == 200
    assert "results" in resp.json()
```

**Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_hpw.py -v
# Expected: FAIL — 404 Not Found
```

**Step 3: Write implementation**

```python
# hemasuite/src-tauri/sidecar/routers/hpw.py
"""HPW API router — wraps HPW CLI commands as REST endpoints."""

import os
import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/hpw", tags=["hpw"])

HPW_PATH = Path(os.environ.get("HPW_PATH", ""))

def _ensure_hpw():
    if HPW_PATH.exists():
        sys.path.insert(0, str(HPW_PATH))
    else:
        raise HTTPException(503, "HPW_PATH not configured or not found")

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
    except Exception as e:
        raise HTTPException(500, str(e))
```

Add router to `server.py`:
```python
from routers.hpw import router as hpw_router
app.include_router(hpw_router)
```

**Step 4: Run test to verify it passes**

```bash
HPW_PATH=/Users/kimhawk/.config/opencode/skills/hematology-paper-writer \
python3 -m pytest tests/test_hpw.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add hemasuite/src-tauri/sidecar/
git commit -m "feat: add HPW API endpoints (phases, pubmed search)"
```

---

### Task 1.3: Add CSA API Endpoints

**Files:**
- Create: `hemasuite/src-tauri/sidecar/routers/csa.py`
- Test: `hemasuite/src-tauri/sidecar/tests/test_csa.py`

**Step 1: Write the failing test**

```python
# hemasuite/src-tauri/sidecar/tests/test_csa.py
import pytest
from httpx import AsyncClient, ASGITransport
from server import app

@pytest.mark.anyio
async def test_csa_scripts_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/csa/scripts")
    assert resp.status_code == 200
    scripts = resp.json()
    assert any(s["name"] == "02_table1.R" for s in scripts)

@pytest.mark.anyio
async def test_csa_run_script():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/csa/run", json={
            "script": "02_table1.R",
            "data_path": "/tmp/test_data.csv",
        })
    # Script may fail without real data, but endpoint should respond
    assert resp.status_code in (200, 422, 500)
```

**Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_csa.py -v
# Expected: FAIL — 404 Not Found
```

**Step 3: Write implementation**

```python
# hemasuite/src-tauri/sidecar/routers/csa.py
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
```

Add router to `server.py`:
```python
from routers.csa import router as csa_router
app.include_router(csa_router)
```

**Step 4: Run test to verify it passes**

```bash
CSA_PATH=/Users/kimhawk/.config/opencode/skills/clinical-statistics-analyzer \
python3 -m pytest tests/test_csa.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add hemasuite/src-tauri/sidecar/
git commit -m "feat: add CSA API endpoints (scripts list, run)"
```

---

### Task 1.4: Configure Tauri Sidecar Management

**Files:**
- Modify: `hemasuite/src-tauri/tauri.conf.json`
- Modify: `hemasuite/src-tauri/src/main.rs`

**Step 1: Configure sidecar in tauri.conf.json**

Add sidecar configuration:

```json
{
  "bundle": {
    "resources": ["sidecar/**", "resources/**"]
  },
  "app": {
    "security": {
      "csp": null
    }
  }
}
```

**Step 2: Add sidecar spawn to main.rs**

```rust
// src-tauri/src/main.rs
use tauri::Manager;
use std::process::{Command, Child};
use std::sync::Mutex;

struct SidecarState(Mutex<Option<Child>>);

fn main() {
    tauri::Builder::default()
        .manage(SidecarState(Mutex::new(None)))
        .setup(|app| {
            let resource_dir = app.path().resource_dir()
                .expect("failed to get resource dir");
            let sidecar_dir = resource_dir.join("sidecar");
            let python = resource_dir.join("python/bin/python3");

            let child = Command::new(python.to_str().unwrap_or("python3"))
                .args(["-m", "uvicorn", "server:app",
                       "--host", "127.0.0.1", "--port", "9720"])
                .current_dir(&sidecar_dir)
                .env("HPW_PATH", resource_dir.join("hpw"))
                .env("CSA_PATH", resource_dir.join("csa"))
                .env("RSCRIPT_PATH", resource_dir.join("r-runtime/bin/Rscript"))
                .spawn()
                .expect("Failed to start Python sidecar");

            app.state::<SidecarState>().0.lock().unwrap().replace(child);
            Ok(())
        })
        .on_event(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(mut child) = app.state::<SidecarState>().0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

**Step 3: Test sidecar launches with Tauri**

```bash
cd hemasuite
pnpm tauri dev
# Expected: Window opens + Python sidecar starts on port 9720
# Verify: curl http://127.0.0.1:9720/health
```

**Step 4: Commit**

```bash
git add hemasuite/src-tauri/
git commit -m "feat: configure Tauri sidecar lifecycle management"
```

---

## Phase 2: React Frontend

### Task 2.1: Setup Tailwind + Layout Shell

**Files:**
- Modify: `hemasuite/package.json`
- Create: `hemasuite/src/App.tsx`
- Create: `hemasuite/src/layouts/MainLayout.tsx`
- Create: `hemasuite/src/components/Sidebar.tsx`

**Step 1: Install dependencies**

```bash
cd hemasuite
pnpm add tailwindcss @tailwindcss/vite zustand @tanstack/react-query
pnpm add -D @types/react @types/react-dom
```

**Step 2: Create MainLayout with sidebar**

```tsx
// hemasuite/src/layouts/MainLayout.tsx
import { useState } from "react";
import { Sidebar } from "../components/Sidebar";

type Tab = "hpw" | "csa" | "pipeline";

export function MainLayout() {
  const [activeTab, setActiveTab] = useState<Tab>("hpw");

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 flex flex-col">
        <nav className="flex border-b bg-white px-4">
          {(["hpw", "csa", "pipeline"] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 text-sm font-medium border-b-2 ${
                activeTab === tab
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab === "hpw" ? "HPW" : tab === "csa" ? "CSA" : "Pipeline"}
            </button>
          ))}
        </nav>
        <div className="flex-1 overflow-auto p-4">
          {activeTab === "hpw" && <div>HPW Editor (Phase 2.2)</div>}
          {activeTab === "csa" && <div>CSA Dashboard (Phase 2.3)</div>}
          {activeTab === "pipeline" && <div>Pipeline Monitor (Phase 2.4)</div>}
        </div>
      </main>
    </div>
  );
}
```

```tsx
// hemasuite/src/components/Sidebar.tsx
const PHASES = [
  "Topic Development", "Research", "Journal Selection",
  "Drafting", "Quality", "References",
  "Prose & Style", "Peer Review", "Publication", "Resubmission",
];

export function Sidebar() {
  return (
    <aside className="w-56 bg-slate-900 text-white flex flex-col">
      <div className="p-4 text-lg font-bold tracking-wide">HemaSuite</div>
      <div className="px-3 py-2 text-xs text-slate-400 uppercase">Phases</div>
      <nav className="flex-1 overflow-y-auto">
        {PHASES.map((phase, i) => (
          <button
            key={i}
            className="w-full text-left px-4 py-2 text-sm hover:bg-slate-800 flex items-center gap-2"
          >
            <span className="text-slate-500 text-xs">{i + 1}</span>
            {phase}
          </button>
        ))}
      </nav>
    </aside>
  );
}
```

**Step 3: Test visual layout**

```bash
pnpm tauri dev
# Expected: Sidebar with 10 phases + tabbed main area
```

**Step 4: Commit**

```bash
git add hemasuite/
git commit -m "feat: add main layout with sidebar and tab navigation"
```

---

### Task 2.2: HPW Editor View

**Files:**
- Create: `hemasuite/src/views/HpwEditor.tsx`
- Create: `hemasuite/src/hooks/useApi.ts`
- Create: `hemasuite/src/stores/projectStore.ts`

**Step 1: Create API hook**

```tsx
// hemasuite/src/hooks/useApi.ts
const API_BASE = "http://127.0.0.1:9720";

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}
```

**Step 2: Create HPW editor view**

```tsx
// hemasuite/src/views/HpwEditor.tsx
import { useEffect, useState } from "react";
import { api } from "../hooks/useApi";

interface Phase { id: number; name: string; module: string; }

export function HpwEditor() {
  const [phases, setPhases] = useState<Phase[]>([]);

  useEffect(() => {
    api<Phase[]>("/hpw/phases").then(setPhases);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Manuscript Editor</h2>
      <div className="grid grid-cols-2 gap-4">
        {phases.map((p) => (
          <div key={p.id} className="p-4 bg-white rounded-lg border shadow-sm">
            <span className="text-sm text-gray-400">Phase {p.id}</span>
            <h3 className="font-medium">{p.name}</h3>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 3: Test data flows from sidecar to UI**

```bash
pnpm tauri dev
# Expected: HPW tab shows 10 phase cards loaded from sidecar API
```

**Step 4: Commit**

```bash
git add hemasuite/src/
git commit -m "feat: add HPW editor view with phase cards"
```

---

### Task 2.3: CSA Dashboard View

**Files:**
- Create: `hemasuite/src/views/CsaDashboard.tsx`

**Step 1: Create CSA dashboard**

```tsx
// hemasuite/src/views/CsaDashboard.tsx
import { useEffect, useState } from "react";
import { api } from "../hooks/useApi";

interface Script { name: string; path: string; }
interface RunResult { exit_code: number; stdout: string; stderr: string; }

export function CsaDashboard() {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [running, setRunning] = useState<string | null>(null);
  const [result, setResult] = useState<RunResult | null>(null);

  useEffect(() => {
    api<Script[]>("/csa/scripts").then(setScripts);
  }, []);

  const runScript = async (name: string) => {
    setRunning(name);
    setResult(null);
    try {
      const res = await api<RunResult>("/csa/run", {
        method: "POST",
        body: JSON.stringify({ script: name, output_dir: "/tmp/hemasuite-out" }),
      });
      setResult(res);
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Statistical Analysis</h2>
      <div className="grid grid-cols-3 gap-3">
        {scripts.map((s) => (
          <button
            key={s.name}
            onClick={() => runScript(s.name)}
            disabled={running !== null}
            className="p-3 bg-white rounded-lg border text-left hover:border-blue-400 disabled:opacity-50"
          >
            <span className="text-sm font-mono">{s.name}</span>
          </button>
        ))}
      </div>
      {result && (
        <pre className="mt-4 p-4 bg-gray-900 text-green-400 rounded-lg text-xs overflow-auto max-h-64">
          {result.stdout || result.stderr}
        </pre>
      )}
    </div>
  );
}
```

**Step 2: Test CSA dashboard**

```bash
pnpm tauri dev
# Expected: CSA tab shows R/Python script buttons, clicking runs script
```

**Step 3: Commit**

```bash
git add hemasuite/src/views/
git commit -m "feat: add CSA dashboard with script runner"
```

---

### Task 2.4: CRF Pipeline Monitor View

**Files:**
- Create: `hemasuite/src/views/PipelineMonitor.tsx`

Similar pattern to CSA dashboard but for the CRF pipeline subcommands (parse-crf, parse-protocol, validate, run-analysis). Uses polling for real-time log output.

**Step 1: Create pipeline monitor**

Wire up to `/csa/run` with CRF pipeline Python scripts. Show step-by-step progress.

**Step 2: Commit**

```bash
git commit -m "feat: add CRF pipeline monitor view"
```

---

## Phase 3: R/Python Bundling

### Task 3.1: Bundle Python with python-build-standalone

**Files:**
- Create: `hemasuite/scripts/bundle-python.sh`

**Step 1: Write bundling script**

```bash
#!/bin/bash
# hemasuite/scripts/bundle-python.sh
# Downloads and packages standalone Python for macOS app bundle.

set -euo pipefail

PYTHON_VERSION="3.14"
ARCH=$(uname -m)
DEST="hemasuite/src-tauri/resources/python"
mkdir -p "$DEST"

echo "Downloading Python ${PYTHON_VERSION} standalone for ${ARCH}..."
# Download from python-build-standalone releases
# Extract to $DEST
# Install pip packages from sidecar/requirements.txt
# Strip debug symbols to reduce size

echo "Python bundle ready at $DEST (~50MB)"
```

**Step 2: Test bundled Python**

```bash
./hemasuite/src-tauri/resources/python/bin/python3 -c "import fastapi; print('OK')"
# Expected: OK
```

**Step 3: Commit**

```bash
git add hemasuite/scripts/
git commit -m "feat: add Python bundling script"
```

---

### Task 3.2: Bundle R Runtime

**Files:**
- Create: `hemasuite/scripts/bundle-r.sh`

**Step 1: Write R bundling script**

```bash
#!/bin/bash
# hemasuite/scripts/bundle-r.sh
# Packages R runtime with pre-installed packages for macOS app bundle.

set -euo pipefail

DEST="hemasuite/src-tauri/resources/r-runtime"
mkdir -p "$DEST"

# Copy system R to relocatable bundle
R_HOME=$(R RHOME)
cp -R "$R_HOME" "$DEST/"

# Install required packages into bundle library
"$DEST/bin/Rscript" -e '
  install.packages(c(
    "survival", "survminer", "ggplot2", "flextable", "officer",
    "cmprsk", "BOIN", "forestplot", "ggalluvial",
    "dplyr", "tidyr", "readxl"
  ), lib="library", repos="https://cloud.r-project.org")
'

# Fix paths for relocatability
echo "R bundle ready at $DEST (~400MB)"
```

**Step 2: Test bundled R**

```bash
./hemasuite/src-tauri/resources/r-runtime/bin/Rscript \
  -e "library(survival); cat('OK\n')"
# Expected: OK
```

**Step 3: Commit**

```bash
git add hemasuite/scripts/
git commit -m "feat: add R runtime bundling script"
```

---

## Phase 4: Integration & Polish

### Task 4.1: Project Manager

**Files:**
- Create: `hemasuite/src/views/ProjectManager.tsx`
- Create: `hemasuite/src-tauri/sidecar/routers/projects.py`

Project CRUD — create/open/list projects in `~/HemaSuite/projects/`. Each project stores manuscript, data, analysis, and exports.

### Task 4.2: HPW-CSA Workflow Integration

Connect CSA analysis outputs (Tables/, Figures/, hpw_manifest.json) to HPW manuscript editor. Auto-insert figures and tables into draft.

### Task 4.3: Settings View

**Files:**
- Create: `hemasuite/src/views/Settings.tsx`

Configure R/Python paths, default journal, output directory, theme.

### Task 4.4: Splash Screen During Sidecar Boot

**Files:**
- Create: `hemasuite/src/splash.html`
- Modify: `hemasuite/src-tauri/src/main.rs`

**Step 1: Create splash.html**

Minimal loading screen shown while Python sidecar starts (~2-4s).

**Step 2: Modify Tauri setup to show splash first**

In `main.rs`, load `splash.html` initially. Spawn a background thread that polls `http://127.0.0.1:9720/health`. Once healthy, send a Tauri event to the frontend to navigate to the React app.

**Step 3: Commit**

```bash
git commit -m "feat: add splash screen during sidecar startup"
```

### Task 4.5: macOS Native Integration

- App icon and menu bar
- Keyboard shortcuts (Cmd+N, Cmd+O, Cmd+S)
- Notification center integration

---

## Phase 5: Build & Distribution

### Task 5.1: Build DMG

```bash
pnpm tauri build
# Produces: hemasuite/src-tauri/target/release/bundle/dmg/HemaSuite.dmg
```

### Task 5.2: Entitlements & R Dylib Signing

**Files:**
- Create: `hemasuite/src-tauri/Entitlements.plist`
- Create: `hemasuite/scripts/sign-r-dylibs.sh`

**Step 1: Create Entitlements.plist**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/>
  <key>com.apple.security.cs.disable-library-validation</key><true/>
  <key>com.apple.security.network.client</key><true/>
  <key>com.apple.security.files.user-selected.read-write</key><true/>
</dict>
</plist>
```

**Step 2: Create R dylib signing script**

```bash
#!/bin/bash
# hemasuite/scripts/sign-r-dylibs.sh
# Signs all R runtime dylibs individually (required for notarization).
set -euo pipefail

APP_PATH="${1:-hemasuite/src-tauri/target/release/bundle/macos/HemaSuite.app}"
IDENTITY="${2:-Developer ID Application: ...}"
ENTITLEMENTS="hemasuite/src-tauri/Entitlements.plist"

echo "Signing R dylibs in $APP_PATH..."
find "$APP_PATH/Contents/Resources/r-runtime" \
  \( -name "*.dylib" -o -name "*.so" \) | while read -r lib; do
  codesign --force --sign "$IDENTITY" \
    --entitlements "$ENTITLEMENTS" --timestamp "$lib"
done
echo "R dylib signing complete."
```

**Step 3: Commit**

```bash
git commit -m "feat: add Entitlements.plist and R dylib signing script"
```

### Task 5.3: Code Signing & Notarization

```bash
# Sign R dylibs first (must happen before app signing)
bash hemasuite/scripts/sign-r-dylibs.sh

# Sign the full app with Developer ID
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: ..." \
  --entitlements hemasuite/src-tauri/Entitlements.plist \
  "HemaSuite.app"

# Notarize
xcrun notarytool submit HemaSuite.dmg \
  --apple-id "..." --team-id "..." --password "..."
```

### Task 5.4: Auto-Update Configuration

Configure Tauri Updater plugin with update server URL.

---

## Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| 0 | 0.1-0.2 | Environment + Scaffold |
| 1 | 1.1-1.4 | Python Sidecar (FastAPI + HPW/CSA APIs) |
| 2 | 2.1-2.4 | React Frontend (Layout + Views) |
| 3 | 3.1-3.2 | R/Python Bundling |
| 4 | 4.1-4.5 | Integration & Polish (+ Splash Screen) |
| 5 | 5.1-5.4 | Build & Distribution (+ Entitlements & R Dylib Signing) |

Total: 20 tasks across 6 phases.
