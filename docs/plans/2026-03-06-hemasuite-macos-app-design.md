# HemaSuite - macOS Standalone App Design

## Overview

HemaSuite is a standalone macOS application that combines Hematology Paper Writer (HPW) and Clinical Statistics Analyzer (CSA) into a single native desktop app. It targets broad distribution to hospitals and universities, including non-developer users.

## Goals

1. **Offline-first security** — All patient/trial data stays local. No external server required.
2. **Unified workflow** — HPW manuscript writing + CSA statistical analysis in one window.
3. **Easy deployment** — Single .app file, no Python/R installation required.

## Architecture

```
HemaSuite.app
├── Tauri Shell (Rust)
│   ├── Window management, macOS integration
│   ├── IPC bridge (frontend <-> backend)
│   ├── Sidecar lifecycle (Python/R process management)
│   └── File system access, auto-updater
│
├── React Frontend (WebView)
│   ├── Phase Navigator (HPW 10 phases)
│   ├── Statistical Dashboard (CSA)
│   ├── Document Editor
│   ├── CRF Pipeline Monitor
│   └── Project Manager
│
├── Python Sidecar (FastAPI)
│   ├── HPW CLI commands (phases 1-10)
│   ├── CSA CRF pipeline (v3.0)
│   ├── R script executor (subprocess)
│   └── PubMed/web search (online mode)
│
└── Bundled R Runtime
    ├── 28 analysis scripts
    └── Pre-installed packages
```

### Layer Responsibilities

| Layer | Technology | Role |
|-------|-----------|------|
| Shell | Tauri 2.x (Rust) | Window, IPC, sidecar, file system, macOS menus/notifications |
| Frontend | React + TypeScript | All UI rendering, user interaction |
| Backend | FastAPI (Python) | HPW/CSA business logic, R script execution |
| Runtime | Bundled R | Statistical computation (survival, plots, tables) |

## UI Design

### Main Layout

```
+----------+-----------------------------------------------+
| Sidebar  |  [HPW] [CSA] [Pipeline]          [Settings]   |
|          |                                               |
| Phases   |  Active Tab Content                           |
|  1-10    |  - Phase editor (HPW)                         |
|          |  - Analysis dashboard (CSA)                   |
| Stats    |  - Pipeline monitor (CRF)                     |
|          |                                               |
| Files    +-----------------------------------------------+
|          |  Output / Log Panel                            |
|          |  Real-time R/Python output                     |
+----------+-----------------------------------------------+
```

### Screens (5)

| Screen | Features |
|--------|----------|
| HPW Editor | Phase-specific manuscript editing, PubMed search, reference management, DOCX conversion |
| CSA Dashboard | R analysis execution, result visualization (KM curves, Forest plots), Table 1 generation |
| CRF Pipeline | CRF extraction -> validation -> analysis pipeline monitoring |
| Project Manager | Project CRUD, file browser, manifest status |
| Settings | R/Python paths, journal defaults, output directory, theme |

### Core Integrated Workflow

```
CRF data -> CSA analysis -> Tables/Figures -> HPW manuscript auto-insert -> Journal format -> DOCX output
```

## R/Python Bundling Strategy

### Bundle Structure

```
HemaSuite.app/Contents/Resources/
├── python/              # python-build-standalone (~50MB)
│   ├── bin/python3
│   ├── lib/
│   └── site-packages/   # fastapi, httpx, python-docx, xmltodict, ...
├── r-runtime/           # Relocatable R (~400MB with packages)
│   ├── bin/Rscript
│   ├── lib/
│   └── library/         # survival, ggplot2, flextable, officer, ...
├── hpw/                 # HPW source
├── csa/                 # CSA source
└── frontend/            # React build output
```

### Component Sizes

| Component | Method | Size |
|-----------|--------|------|
| Python | python-build-standalone (indygreg) | ~50MB |
| R runtime | rig install + relocatable packaging | ~400MB |
| R packages | Pre-compiled binary bundle | included |
| **Total .app** | | **~500-600MB** |

### Pre-installed R Packages

survival, survminer, ggplot2, flextable, officer, cmprsk, BOIN, forestplot, ggalluvial, dplyr, tidyr, readxl

## Data Flow

### Project Structure

```
~/HemaSuite/projects/<project-name>/
├── manuscript/          # HPW manuscript files
│   ├── draft.md
│   ├── draft.docx
│   └── references.bib
├── data/                # CSA input data
│   ├── crf/            # CRF originals (PDF/Excel)
│   └── parsed/         # Parsed data
├── analysis/            # CSA output
│   ├── Tables/
│   ├── Figures/
│   └── hpw_manifest.json
├── exports/             # Final outputs
└── project.json         # Project metadata
```

### Online/Offline Capabilities

| Feature | Offline | Online |
|---------|---------|--------|
| Manuscript editing | Yes | Yes |
| CSA analysis (R) | Yes | Yes |
| PubMed search | No | Yes |
| Reference verification | Cached only | Yes |
| DOCX/PDF conversion | Yes | Yes |
| Quality analysis | Yes | Yes |

All patient data stored **locally only**. No external transmission.

## Startup Experience

### Splash Screen

During sidecar boot (~2-4 seconds), show a lightweight splash screen:

```
+-----------------------------------------------+
|                                               |
|              HemaSuite                        |
|     Clinical Research Suite                   |
|                                               |
|            [spinner]                          |
|       Starting up...                          |
|                                               |
+-----------------------------------------------+
```

Implementation: Tauri `setup()` hook loads a local `splash.html` in the WebView while polling the sidecar `/health` endpoint. Once healthy, navigate to the React app.

## Deployment

| Item | Method |
|------|--------|
| Code signing | Apple Developer ID (per-binary + deep) |
| Notarization | notarytool |
| Distribution | DMG + GitHub Releases (or internal server) |
| Updates | Tauri Updater plugin (auto-update) |
| Minimum macOS | 13 (Ventura) |
| Architecture | Universal binary (arm64 + x86_64) |

### Entitlements (Hardened Runtime)

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

- `allow-unsigned-executable-memory`: Required for Python runtime JIT
- `disable-library-validation`: Required for bundled R dylibs (unsigned by Apple)
- `network.client`: PubMed/web search in online mode

### R Dylib Signing

Bundled R runtime contains unsigned dylibs that must be individually signed before notarization:

```bash
# Sign each dylib in the R bundle
find HemaSuite.app/Contents/Resources/r-runtime -name "*.dylib" -o -name "*.so" | \
  xargs -I {} codesign --force --sign "Developer ID Application: ..." \
    --entitlements Entitlements.plist --timestamp {}
```

This is a known high-complexity step — R.framework dylibs are not Apple-signed and require per-file codesigning for Gatekeeper acceptance.

## Testing Strategy

| Layer | Method |
|-------|--------|
| React UI | Vitest + React Testing Library |
| Tauri IPC | Tauri integration tests |
| Python API | pytest (reuse existing HPW/CSA tests) |
| R scripts | testthat (maintain existing tests) |
| E2E | Playwright (WebView UI testing) |

## Technology Stack Summary

| Category | Choice |
|----------|--------|
| Desktop framework | Tauri 2.x |
| Frontend | React + TypeScript + Vite |
| Backend | Python + FastAPI |
| Statistics | R (bundled) |
| Charts | Plotly.js / Recharts |
| Editor | Monaco Editor or TipTap |
| State management | Zustand |
| Styling | Tailwind CSS |

## Decisions & Rationale

1. **Tauri over Electron** — 10x smaller binary, native performance, stronger security model
2. **React over Svelte** — Richer ecosystem for data visualization and editor components
3. **FastAPI over direct IPC** — Clean separation, existing HPW/CSA code runs unchanged
4. **Bundled R over Python-only** — CSA's 28 R scripts are production-tested; rewriting in Python would introduce regression risk
5. **Project-based data** — Each project is self-contained for portability and backup
6. **Tauri+React over PyInstaller+Streamlit** — Supersedes `hpw-csa-macos-app` plan. PyInstaller+Streamlit bundling is fragile (hidden imports, version lock-in). Tauri's sidecar pattern provides cleaner separation and built-in distribution tooling (signing, notarization, auto-update). See `docs/01-plan/features/hpw-csa-macos-app.plan.md` for the superseded approach.
