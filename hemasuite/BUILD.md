# HemaSuite Build Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Rust | 1.93.1+ | Tauri backend |
| Node.js | 20+ | Frontend build |
| pnpm | 10.30+ | Package manager |
| Python | 3.14+ | Sidecar runtime |
| R | 4.5+ | Statistical analysis |
| Xcode CLT | 16+ | macOS compilation |

## Development Build

```bash
cd hemasuite
pnpm install
pnpm tauri dev
# Opens app window + starts Python sidecar on port 9720
```

## Production Build

```bash
./scripts/build-dmg.sh
# Output: dist/HemaSuite-0.1.0.dmg
```

This runs `pnpm tauri build --release`, ad-hoc signs with `codesign -s -`, and creates a .dmg via `create-dmg`.

## Build Scripts

| Script | Purpose |
|--------|---------|
| `scripts/build-dmg.sh` | Build, ad-hoc sign, create .dmg |
| `scripts/sign-r-dylibs.sh` | Per-file codesign for R/Python dylibs |
| `scripts/bundle-python.sh` | Bundle standalone Python runtime |
| `scripts/bundle-r.sh` | Bundle R runtime with packages |

## Code Signing Flow

```
pnpm tauri build --release
    |
    v
sign-r-dylibs.sh  (sign each .dylib/.so individually)
    |
    v
codesign -s -      (ad-hoc sign full .app bundle)
    |
    v
create-dmg         (package into .dmg with drag-to-Applications)
```

No Apple Developer ID or notarization needed for personal distribution.
Recipients bypass Gatekeeper via right-click > Open (once), or use USB delivery (no quarantine).

## Troubleshooting

### Build fails with "no signing identity found"
Ad-hoc signing (`codesign -s -`) doesn't need a certificate. If you see this error, ensure `build-dmg.sh` uses `-s -` not `-s "Developer ID..."`.

### R dylibs fail to load at runtime
Ensure `Entitlements.plist` includes `allow-unsigned-executable-memory` and `disable-library-validation`. These are required for bundled R's JIT and unsigned .so files.

### DMG creation fails
Install `create-dmg`: `brew install create-dmg`

### App crashes on first launch
Bundled runtimes load on first launch (10-30 seconds). If it crashes, check Console.app for sidecar errors — the Python venv or R_HOME path may be incorrect.

## Entitlements

`src-tauri/Entitlements.plist` grants these capabilities:

| Entitlement | Why |
|-------------|-----|
| `allow-unsigned-executable-memory` | R JIT compiler needs executable memory |
| `disable-library-validation` | R packages contain unsigned .so files |
| `network.client` | PubMed API calls from sidecar |
| `files.user-selected.read-write` | User picks CSV/Excel data files |

## Bundle Resources

The app bundles (~623MB total):
- **Python runtime** (~74MB): `resources/python/`
- **R runtime** (~549MB): `resources/r-runtime/`
- **Sidecar code**: `sidecar/*.py`, `sidecar/routers/*.py`

## Running Tests

```bash
# Frontend (Vitest)
pnpm test

# Python sidecar (pytest)
cd src-tauri/sidecar && source .venv/bin/activate && python -m pytest tests/ -v
```
