# Design: HPW + CSA Standalone macOS App

**Feature**: `hpw-csa-macos-app`
**Phase**: Design
**Created**: 2026-03-06
**Depends on**: `hpw-csa-unified-ui-v2` (completed, 100%)

---

## 1. File Inventory

### Files to Create

| File | Phase | Purpose |
|------|-------|---------|
| `macos-app/app_launcher.py` | 1 | PyInstaller entry point — starts Streamlit, opens pywebview window |
| `macos-app/splash.html` | 1 | Startup splash screen shown during Streamlit boot |
| `macos-app/app_launcher.spec` | 1 | PyInstaller build spec (datas, hiddenimports, bundle_identifier) |
| `macos-app/build.sh` | 1 | One-command build automation |
| `macos-app/bundle_r.sh` | 2 | Downloads R.framework and embeds into app bundle |
| `macos-app/install_r_packages.R` | 2 | Installs CRAN packages to Resources/r_packages/ |
| `macos-app/sign_and_notarize.sh` | 3 | codesign + notarytool automation |
| `macos-app/create_dmg.sh` | 3 | create-dmg invocation with branding |
| `macos-app/Entitlements.plist` | 3 | Hardened runtime entitlements |
| `macos-app/dmg_background.png` | 3 | DMG window background (1200×800) |
| `macos-app/README.md` | 1 | Build instructions |

### Files to Modify

| File | Changes |
|------|---------|
| `hematology-paper-writer/ui/app.py` | Add `is_bundled()` guard; use relative paths for bundled assets |
| `hematology-paper-writer/cli.py` | Add `--port` CLI flag (PyInstaller picks a free port) |

### Files Unchanged

All HPW + CSA source files remain unmodified. The `.app` is a wrapper, not a rewrite.

---

## 2. Architecture Overview

```
HPW-CSA.app/
├── Contents/
│   ├── Info.plist                     ← App name, bundle ID, minimum OS
│   ├── MacOS/
│   │   └── HPW-CSA                    ← PyInstaller binary (Python runtime embedded)
│   ├── Frameworks/
│   │   └── R.framework/               ← Phase 2: Full R runtime
│   │       ├── R                      ← R executable
│   │       └── Versions/4.4/lib/      ← libR.dylib + dependencies
│   └── Resources/
│       ├── hematology-paper-writer/   ← HPW source (copied by PyInstaller datas)
│       ├── clinical-statistics-analyzer/ ← CSA source
│       ├── r_packages/                ← Phase 2: CRAN packages (.libPaths target)
│       └── splash.html                ← Startup splash
```

---

## 3. Detailed Component Design

### 3.1 `macos-app/app_launcher.py` — Entry Point

```python
"""
HPW + CSA macOS App Launcher
Starts Streamlit server, waits for readiness, opens pywebview window.
"""
import os
import sys
import socket
import subprocess
import threading
import time
import webview  # pywebview

APP_TITLE = "HPW + CSA — Clinical Research Suite"
WINDOW_W, WINDOW_H = 1400, 900

def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def _resource_path(rel: str) -> str:
    """Resolve path relative to app bundle Resources/ or dev working dir."""
    if getattr(sys, "frozen", False):
        base = os.path.join(os.path.dirname(sys.executable),
                            "..", "Resources")
    else:
        base = os.path.join(os.path.dirname(__file__), "..")
    return os.path.normpath(os.path.join(base, rel))

def _setup_r_env():
    """Phase 2: Override R_HOME and R_LIBS to bundled R.framework."""
    if getattr(sys, "frozen", False):
        framework = os.path.join(os.path.dirname(sys.executable),
                                 "..", "Frameworks", "R.framework")
        r_home = os.path.join(framework, "Versions", "Current", "Resources")
        r_libs = _resource_path("r_packages")
        if os.path.isdir(r_home):
            os.environ["R_HOME"] = r_home
            os.environ["R_LIBS"] = r_libs
            os.environ["R_LIBS_USER"] = r_libs
            # Prepend R bin to PATH so subprocess("Rscript") finds bundled R
            r_bin = os.path.join(r_home, "bin")
            os.environ["PATH"] = r_bin + os.pathsep + os.environ.get("PATH", "")

def _start_streamlit(port: int):
    """Launch Streamlit as a subprocess."""
    app_py = _resource_path("hematology-paper-writer/ui/app.py")
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_py,
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.fileWatcherType", "none",
    ]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _wait_for_streamlit(port: int, timeout: int = 30):
    """Poll until Streamlit is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False

def main():
    _setup_r_env()
    port = _find_free_port()

    # Show splash while Streamlit boots
    splash_path = _resource_path("splash.html")
    window = webview.create_window(
        APP_TITLE,
        f"file://{splash_path}",
        width=WINDOW_W, height=WINDOW_H,
        resizable=True,
    )

    def _load_app():
        _start_streamlit(port)
        if _wait_for_streamlit(port):
            window.load_url(f"http://127.0.0.1:{port}")
        else:
            window.load_html("<h2>Failed to start server. Please relaunch.</h2>")

    t = threading.Thread(target=_load_app, daemon=True)
    t.start()
    webview.start()

if __name__ == "__main__":
    main()
```

---

### 3.2 `macos-app/splash.html` — Startup Screen

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0; background: #1a2744; display: flex;
    flex-direction: column; align-items: center; justify-content: center;
    height: 100vh; font-family: -apple-system, sans-serif; color: #f5f0e8;
  }
  h1 { font-size: 2rem; margin-bottom: 0.5rem; }
  p  { font-size: 1rem; opacity: 0.7; }
  .spinner {
    width: 40px; height: 40px; margin-top: 2rem;
    border: 4px solid rgba(255,255,255,0.2);
    border-top-color: #e63946; border-radius: 50%;
    animation: spin 0.9s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
  <h1>HPW + CSA</h1>
  <p>Clinical Research Suite — Starting up…</p>
  <div class="spinner"></div>
</body>
</html>
```

---

### 3.3 `macos-app/app_launcher.spec` — PyInstaller Spec

```python
# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

ROOT = Path("..").resolve()
HPW  = ROOT / "hematology-paper-writer"
CSA  = ROOT / "clinical-statistics-analyzer"

block_cipher = None

a = Analysis(
    ["app_launcher.py"],
    pathex=[str(HPW), str(CSA / "scripts")],
    binaries=[],
    datas=[
        (str(HPW), "hematology-paper-writer"),
        (str(CSA), "clinical-statistics-analyzer"),
        ("splash.html", "."),
    ],
    hiddenimports=[
        # Streamlit
        "streamlit", "streamlit.web.cli",
        "streamlit.runtime.scriptrunner.magic_funcs",
        # HPW phases
        "phases.phase1_topic", "phases.phase2_research",
        "phases.phase3_journal", "phases.phase4_5_updating",
        "phases.phase4_7_prose", "phases.phase5_quality",
        "phases.phase8_peerreview", "phases.phase9_publication",
        # Scientific
        "pandas", "numpy", "scipy", "statsmodels",
        "lifelines", "tableone",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib.tests"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="HPW-CSA",
    debug=False, bootloader_ignore_signals=False,
    strip=True, upx=False, console=False,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=True, upx=False,
    name="HPW-CSA",
)

app = BUNDLE(
    coll,
    name="HPW-CSA.app",
    icon=None,  # TODO: add .icns
    bundle_identifier="com.brightgold.hpw-csa",
    info_plist={
        "CFBundleName": "HPW + CSA",
        "CFBundleDisplayName": "HPW + CSA Clinical Research Suite",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "13.0",
        "NSRequiresAquaSystemAppearance": False,
    },
)
```

---

### 3.4 `macos-app/bundle_r.sh` — R.framework Embedding (Phase 2)

```bash
#!/usr/bin/env bash
# Downloads macOS R.framework and embeds it in the built .app
set -euo pipefail

APP_PATH="dist/HPW-CSA.app"
FRAMEWORKS="$APP_PATH/Contents/Frameworks"
R_PKG_URL="https://cran.r-project.org/bin/macosx/big-sur-arm64/base/R-4.4.2-arm64.pkg"

mkdir -p "$FRAMEWORKS"

# Download + extract R.framework from .pkg
tmpdir=$(mktemp -d)
curl -L "$R_PKG_URL" -o "$tmpdir/R.pkg"
pkgutil --expand "$tmpdir/R.pkg" "$tmpdir/R_expanded"
# R.framework is inside Payload
cd "$tmpdir/R_expanded/R-fw.pkg"
cat Payload | gunzip | cpio -id
cp -R R.framework "$OLDPWD/$FRAMEWORKS/"
cd "$OLDPWD"
rm -rf "$tmpdir"

echo "R.framework embedded at $FRAMEWORKS/R.framework"

# Install CRAN packages to Resources/r_packages/
R_LIBS="$APP_PATH/Contents/Resources/r_packages"
mkdir -p "$R_LIBS"
R_HOME="$FRAMEWORKS/R.framework/Versions/Current/Resources"
"$R_HOME/bin/Rscript" install_r_packages.R "$R_LIBS"

echo "CRAN packages installed to $R_LIBS"
```

---

### 3.5 `macos-app/install_r_packages.R` — CRAN Package Installer (Phase 2)

```r
#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
lib_path <- args[1]

packages <- c(
  # Core statistics
  "survival", "survminer", "cmprsk",
  # Table generation
  "tableone", "gtsummary", "gt",
  # Data manipulation
  "dplyr", "tidyr", "broom", "scales",
  # Visualization
  "ggplot2", "forestplot",
  # Disease-specific
  "BOIN", "clinfun"
)

installed <- rownames(installed.packages(lib.loc = lib_path))
to_install <- setdiff(packages, installed)

if (length(to_install) > 0) {
  cat("Installing:", paste(to_install, collapse = ", "), "\n")
  install.packages(
    to_install,
    lib = lib_path,
    repos = "https://cloud.r-project.org",
    type = "binary",  # macOS binary packages (no compilation needed)
    quiet = FALSE
  )
} else {
  cat("All packages already installed.\n")
}
```

---

### 3.6 `macos-app/build.sh` — Build Automation

```bash
#!/usr/bin/env bash
# Full build: Phase 1 (Python bundle) + Phase 2 (R embedding)
set -euo pipefail

PHASE=${1:-1}

echo "=== HPW + CSA macOS App Build (Phase $PHASE) ==="

# 1. Install Python deps
pip install pyinstaller pywebview

# 2. Build PyInstaller bundle
cd "$(dirname "$0")"
pyinstaller app_launcher.spec --clean --noconfirm

echo "Python bundle built: dist/HPW-CSA.app"

if [ "$PHASE" -ge 2 ]; then
  echo "--- Phase 2: Embedding R.framework ---"
  bash bundle_r.sh
  echo "R.framework embedded."
fi

if [ "$PHASE" -ge 3 ]; then
  echo "--- Phase 3: Signing & Notarizing ---"
  bash sign_and_notarize.sh
  bash create_dmg.sh
  echo "DMG created: dist/HPW-CSA-installer.dmg"
fi

echo "=== Build complete ==="
open dist/
```

---

### 3.7 `macos-app/Entitlements.plist` (Phase 3)

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

> `allow-unsigned-executable-memory` is required for Python's JIT. `disable-library-validation`
> is required for R.framework dylibs which Apple did not sign.

---

## 4. Data / Control Flow

```
User double-clicks HPW-CSA.app
        │
        ▼
app_launcher.py (PyInstaller binary)
        │
        ├── _setup_r_env()         [Phase 2]
        │     └── sets R_HOME, R_LIBS, PATH → bundled R.framework
        │
        ├── _find_free_port()
        │     └── random port e.g. 54231
        │
        ├── webview.create_window("splash.html")  ← shows instantly
        │
        ├── Thread: _load_app()
        │     ├── _start_streamlit(port=54231)
        │     │     └── subprocess: python -m streamlit run ui/app.py ...
        │     ├── _wait_for_streamlit(port)       ← polls TCP, max 30s
        │     └── window.load_url("http://127.0.0.1:54231")
        │
        └── webview.start()                       ← blocks until window closes
```

---

## 5. Build Pipeline

```
Phase 1 (1 week):
  pip install pyinstaller pywebview
  pyinstaller app_launcher.spec
  → dist/HPW-CSA.app  (~400 MB, R via system)

Phase 2 (+1–2 weeks):
  bash bundle_r.sh
  → dist/HPW-CSA.app  (~800 MB, fully self-contained)

Phase 3 (+3–4 days):
  bash sign_and_notarize.sh
  bash create_dmg.sh
  → dist/HPW-CSA-1.0.dmg  (~400 MB compressed)
```

---

## 6. Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Window wrapper | `pywebview` (WKWebView) | Native macOS WebKit; no Electron overhead; pure Python |
| Bundler | `PyInstaller` | Most mature for Streamlit; proven patterns available |
| R distribution | `R.framework` from CRAN macOS pkg | Official binary; correct dylib layout for `.app` embedding |
| CRAN package install | `type="binary"` | Avoids compilation; binary .tgz from CRAN has all deps |
| Port selection | random free port | Avoids conflicts if user runs multiple instances |
| Startup detection | TCP poll on 127.0.0.1:PORT | More reliable than stdout parsing |
| Entitlements | `disable-library-validation` | Required for R.framework unsigned dylibs |

---

## 7. Acceptance Criteria Mapping

| Plan Goal | Design Component | Status |
|-----------|-----------------|--------|
| Native window (Goal 1) | `app_launcher.py` → `webview.create_window` | Designed |
| Self-contained Python (Goal 2) | `app_launcher.spec` → PyInstaller BUNDLE | Designed |
| Self-contained R (Goal 3) | `bundle_r.sh` + `install_r_packages.R` | Designed |
| Signed DMG (Goal 4) | `sign_and_notarize.sh` + `create_dmg.sh` | Designed |
| Splash screen | `splash.html` | Designed |
| R env override | `_setup_r_env()` in launcher | Designed |
