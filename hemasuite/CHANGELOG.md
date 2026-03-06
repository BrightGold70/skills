# Changelog

## v0.1.0 (2026-03-07)

### Features
- HPW (Hematology Paper Writer) with TipTap rich text editor and PubMed integration
- CSA (Clinical Statistics Analyzer) with Recharts visual pipeline dashboard
- Project manager with Zustand state management
- Splash screen with developer credit
- First-launch dialog with Gatekeeper bypass instructions

### Architecture
- Tauri 2 desktop shell with React 19 frontend
- FastAPI Python sidecar on port 9720
- Bundled R 4.5 runtime (~549MB) for statistical analysis
- Bundled Python 3.14 runtime (~74MB) for sidecar

### Distribution
- Personal distribution via .dmg (AirDrop) and USB
- Ad-hoc code signing (no Apple Developer ID)
- `build-dmg.sh` build script with `create-dmg` packaging

### Build
- Vite code splitting: react, recharts, tiptap as separate chunks
- Main JS chunk reduced from ~992KB to ~197KB

### Testing
- 48 Vitest unit tests (React components, hooks, stores)
- 44 pytest tests (FastAPI sidecar endpoints)
- 15 Playwright E2E specs (navigation, HPW editor, CSA dashboard, project manager)
