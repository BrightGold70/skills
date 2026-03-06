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

### Build only (no signing)

```bash
./scripts/build-and-sign.sh --dry-run
# Output: src-tauri/target/release/bundle/macos/HemaSuite.app
# Output: src-tauri/target/release/bundle/dmg/HemaSuite_0.1.0_*.dmg
```

### Full signed + notarized build

```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAMID)"
export APPLE_ID="your@email.com"
export APPLE_TEAM_ID="TEAMID"
export APPLE_APP_PASSWORD="app-specific-password"

./scripts/build-and-sign.sh
```

## Build Scripts

| Script | Purpose |
|--------|---------|
| `scripts/build-and-sign.sh` | Unified build, sign, notarize pipeline |
| `scripts/sign-r-dylibs.sh` | Per-file codesign for R/Python dylibs |
| `scripts/bundle-python.sh` | Bundle standalone Python runtime |
| `scripts/bundle-r.sh` | Bundle R runtime with packages |

## Code Signing Flow

```
pnpm tauri build
    |
    v
sign-r-dylibs.sh  (sign each .dylib/.so individually)
    |
    v
codesign --deep    (sign full .app bundle)
    |
    v
codesign DMG       (sign disk image)
    |
    v
notarytool submit  (Apple notarization)
    |
    v
stapler staple     (embed notarization ticket)
```

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

## Auto-Update

Configured via `tauri.conf.json` plugins.updater. Before first release:
1. Generate signing keypair: `tauri signer generate`
2. Update `pubkey` in tauri.conf.json
3. Deploy update server at configured endpoint

## Running Tests

```bash
# Frontend (Vitest)
pnpm test

# Python sidecar (pytest)
cd src-tauri/sidecar && source .venv/bin/activate && python -m pytest tests/ -v
```
