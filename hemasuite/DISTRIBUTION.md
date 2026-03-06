# HemaSuite - Distribution Guide (Internal)

## Prerequisites

- Rust toolchain (`rustup`)
- Node.js + pnpm
- Xcode Command Line Tools (`xcode-select --install`)
- `create-dmg` (`brew install create-dmg`)

## Build

```bash
./scripts/build-dmg.sh
```

Output: `dist/HemaSuite-{version}.dmg`

## Versioning

Bump version in both files:
- `src-tauri/tauri.conf.json` → `"version": "X.Y.Z"`
- `src-tauri/Cargo.toml` → `version = "X.Y.Z"`

## Distribution Checklist

- [ ] Bump version number
- [ ] Run `./scripts/build-dmg.sh`
- [ ] Test: mount .dmg, drag to Applications, right-click > Open
- [ ] Verify splash shows "Developed by Hawk Kim, M.D., Ph.D."
- [ ] Share via AirDrop, messaging, or USB
- [ ] Confirm recipient can launch successfully

## Delivery Methods

### AirDrop (primary)
Share the `.dmg` file directly. Recipient will need to right-click > Open once.

### USB stick (zero-friction)
Copy `HemaSuite.app` directly to USB. Files from USB aren't quarantined by macOS, so no Gatekeeper dialog.

## Signing

Ad-hoc signing (`codesign -s -`). No Apple Developer ID needed.

## Changelog

### v0.1.0
- Initial release
- HPW (Hematology Paper Writer) + CSA (Clinical Statistics Analyzer)
- Bundled R and Python runtimes
- Personal distribution via .dmg / USB
