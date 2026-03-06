# Plan: HPW + CSA Standalone macOS App

**Feature**: `hpw-csa-macos-app`
**Phase**: Plan
**Created**: 2026-03-06
**Depends on**: `hpw-csa-unified-ui-v2` (completed, 100%)

---

## Overview

Package the unified HPW + CSA Streamlit application as a fully self-contained macOS `.app`
bundle. Clinical researchers double-click the app — no Python, no R, no terminal required.
The bundle embeds the Python runtime (via PyInstaller), the Streamlit server, and the R runtime
(via R.framework) with all required CRAN packages.

## Problem Statement

The current HPW + CSA tool requires:
- Python 3.x installed and configured
- R 4.x installed with 10+ CRAN packages
- Terminal proficiency to run `streamlit run ui/app.py`
- Manual port management (localhost:8501)

Clinical hematologists and oncologists cannot reasonably be expected to meet these requirements.
Distribution as a macOS `.app` eliminates all setup friction and enables use in clinical
research environments with no IT intervention.

## Goals

### Goal 1 — Native macOS App Window (Phase 1)

Wrap the Streamlit server in a `pywebview` WKWebView window. The app opens like any native
macOS application — no browser, no terminal.

**Acceptance Criteria**:
- `HPW-CSA.app` launches on double-click
- Streamlit UI renders inside a native macOS window (WKWebView)
- Window title: "HPW + CSA — Clinical Research Suite"
- Window size: 1400×900 (resizable)
- Splash screen shown during Streamlit startup (~4s)
- App closes cleanly when window is closed

### Goal 2 — Self-Contained Python Bundle (Phase 1)

PyInstaller bundles the Python runtime, Streamlit, and all pip dependencies. No Python
installation required on the target machine.

**Acceptance Criteria**:
- Bundle created via `pyinstaller app_launcher.spec`
- All HPW phases (1–9) functional inside the bundle
- All CSA Python pipeline (CRF, orchestrator, skills) functional
- Bundle size < 600 MB (compressed DMG < 300 MB)
- Runs on macOS 13 Ventura and later (arm64 + x86_64 universal)

### Goal 3 — Self-Contained R Bundle (Phase 2)

Embed the R runtime (R.framework) and all required CRAN packages inside the `.app` bundle.
CSA R scripts (02–25) run using the bundled R, with no system R required.

**Acceptance Criteria**:
- `R.framework` embedded in `HPW-CSA.app/Contents/Frameworks/`
- `R_HOME` environment variable overridden to point to bundled framework
- CRAN packages installed to `Contents/Resources/r_packages/` (`.libPaths()` override)
- All 16 CSA R analysis scripts execute correctly (02_table1 through 25_aml_phase1_boin)
- R version: 4.4.x (current CRAN macOS release)

### Goal 4 — Signed & Notarized Distribution (Phase 3)

Apple Developer signing and notarization so Gatekeeper allows the app without warnings.
Distribute as a DMG with background art and Applications folder shortcut.

**Acceptance Criteria**:
- App signed with Apple Developer certificate (`codesign --deep --timestamp`)
- Notarized via `xcrun notarytool`
- Gatekeeper allows launch on a fresh macOS machine (no "unidentified developer" warning)
- DMG created via `create-dmg` with HPW+CSA branding
- Stapled notarization ticket embedded in DMG

---

## Implementation Phases

### Phase 1 — Python-only `.app` (1 week)
Files to create/modify:
- `macos-app/app_launcher.py` — pywebview entry point
- `macos-app/app_launcher.spec` — PyInstaller spec
- `macos-app/splash.html` — startup splash screen
- `macos-app/build.sh` — build automation script
- `macos-app/README.md` — build instructions

R dependency: system R required (acceptable fallback for Phase 1).

### Phase 2 — R.framework bundling (1–2 weeks)
Files to create/modify:
- `macos-app/bundle_r.sh` — downloads and embeds R.framework
- `macos-app/install_r_packages.R` — installs CRAN deps to Resources/r_packages/
- `macos-app/app_launcher.py` — add R_HOME env override before subprocess launch
- `macos-app/app_launcher.spec` — add Frameworks/ and Resources/r_packages/ to datas

CRAN packages required (from CSA R scripts):
- survival, survminer, tableone, dplyr, tidyr, ggplot2, forestplot
- broom, scales, gt, gtsummary, BOIN, clinfun, cmprsk

### Phase 3 — Notarization + DMG (3–4 days)
Files to create/modify:
- `macos-app/sign_and_notarize.sh` — codesign + notarytool automation
- `macos-app/dmg_background.png` — DMG branding
- `macos-app/create_dmg.sh` — create-dmg invocation
- `macos-app/Entitlements.plist` — required for hardened runtime

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| R.framework binary signing complexity | High | Sign each dylib individually; use `--deep` flag |
| PyInstaller hidden imports (Streamlit) | Medium | Use `--collect-all streamlit` hook |
| App size exceeds 1 GB | Medium | Strip debug symbols; exclude unused R packages |
| macOS ARM vs Intel compatibility | Medium | Build universal binary or separate arm64/x86_64 |
| Apple notarization rejection | Medium | Pre-validate with `spctl`; fix entitlements early |
| CRAN package compile dependencies | Low | Use binary CRAN packages (macOS .tgz) |

---

## Alternative: Python-Only Path (No R Bundling)

If R bundling proves too complex, the CSA R scripts can be reimplemented in Python:

| R Script | Python Replacement |
|----------|--------------------|
| 02_table1.R | `tableone` pip package |
| 03_efficacy.R | `scipy.stats`, `statsmodels` |
| 04_survival.R | `lifelines` |
| 05_safety.R | `pandas` + custom logic |
| 20–25 (disease-specific) | `lifelines` + `statsmodels` |

This path eliminates R dependency entirely — much simpler bundling (~400 MB), but requires
significant rewrite effort (estimated 3–4 weeks).

---

## Out of Scope

- Windows or Linux packaging (macOS only)
- Mac App Store distribution (sandboxing constraints incompatible with R subprocess)
- Auto-update mechanism (future feature)
- Offline PubMed/NLM access (network required for literature search)

---

## Success Criteria

1. Clinical researcher with no Python/R knowledge can launch app by double-clicking `.app`
2. All HPW phases 1–9 functional within the app
3. All 16 CSA R analysis scripts produce correct output
4. App passes Gatekeeper on a fresh macOS 13+ machine
5. Total install size (DMG) < 500 MB
