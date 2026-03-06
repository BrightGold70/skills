# HemaSuite

Standalone macOS desktop app for hematologists, combining two tools:

- **HPW** (Hematology Paper Writer) — manuscript editor with PubMed integration and R-powered statistical inserts
- **CSA** (Clinical Statistics Analyzer) — visual pipeline builder for clinical data analysis

## Architecture

```
HemaSuite.app (Tauri 2)
├── Frontend: React 19 + TailwindCSS + Zustand + Recharts + TipTap
├── Backend:  FastAPI sidecar (Python, port 9720)
└── Runtime:  Bundled R 4.5 (~549MB) + Python 3.14 (~74MB)
```

## Quick Start

```bash
pnpm install
pnpm tauri dev
```

## Build & Distribute

```bash
./scripts/build-dmg.sh
# Output: dist/HemaSuite-0.1.0.dmg
```

Distribution is personal (< 10 users, all macOS). No Apple Developer ID or notarization needed.
See [DISTRIBUTION.md](DISTRIBUTION.md) for delivery methods and [docs/install-guide.md](docs/install-guide.md) for recipient instructions.

## Testing

```bash
pnpm test              # Vitest (48 tests)
pnpm test:e2e          # Playwright E2E (15 specs)
cd src-tauri/sidecar && python -m pytest tests/ -v  # pytest (44 tests)
```

## Developed by

Hawk Kim, M.D., Ph.D.
