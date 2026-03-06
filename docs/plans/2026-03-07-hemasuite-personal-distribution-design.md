# HemaSuite Personal Distribution - Design

## Context

HemaSuite (Tauri 2 + React + FastAPI + bundled R) will be distributed personally to < 10 hematologists, all on macOS. This changes the original design assumption of "broad distribution to hospitals and universities."

## Goals

1. Simplify the build-to-distribute pipeline to a single script
2. Remove unnecessary infrastructure (notarization, auto-updater, telemetry)
3. Provide clear install instructions for non-technical recipients
4. Support two delivery methods: .dmg file share and USB stick

## Distribution Model

- **Primary**: .dmg via direct file share (AirDrop, messaging, email)
- **Fallback**: .app copied directly via USB stick (zero Gatekeeper friction)
- **No** Apple Developer Program enrollment ($99/year not needed)
- **No** App Store, no public download page

## Build Pipeline

```
cargo tauri build --release
  -> HemaSuite.app (ad-hoc signed)
  -> create-dmg -> HemaSuite-{version}.dmg
  -> Ready for distribution
```

### `scripts/build-dmg.sh`

Single script that:
1. Runs `cargo tauri build --release`
2. Ad-hoc signs: `codesign -s - --deep --force` the .app bundle
3. Creates .dmg with drag-to-Applications layout via `create-dmg`
4. Outputs `dist/HemaSuite-{version}.dmg`

### Code Signing

- Ad-hoc signing (`codesign -s -`) — no Developer ID required
- Gives a valid code signature so macOS frameworks load correctly
- Recipients bypass Gatekeeper once via right-click > Open

## Removals from Current Design

| Current Feature | Action | Reason |
|---|---|---|
| `sign-and-notarize.sh` | Delete | No Developer ID |
| Tauri updater config (`tauri.conf.json` updater section) | Remove | Manual updates only |
| Sparkle/auto-update endpoints | Delete | Not needed for < 10 users |
| App Store entitlements/sandbox | Simplify to minimum | No App Store submission |
| Crash reporting / telemetry | Remove | Direct feedback from users |

## New Deliverables

| Deliverable | Description |
|---|---|
| `scripts/build-dmg.sh` | One-command build + sign + package pipeline |
| `docs/install-guide.md` | 1-page install instructions for recipients |
| First-launch dialog (in-app) | "If blocked, right-click > Open" guidance |
| `DISTRIBUTION.md` | Internal notes: how to build, version, share |

## Install Guide (for recipients)

### From .dmg (primary)
1. Open the .dmg file
2. Drag HemaSuite to Applications folder
3. Right-click HemaSuite.app > Open > click "Open" on the security dialog
4. Subsequent launches: double-click as normal

### From USB (fallback)
1. Drag HemaSuite.app from USB to Applications
2. Double-click to open (no security dialog — USB files aren't quarantined)

### Troubleshooting
- If still blocked: open Terminal, run `xattr -cr /Applications/HemaSuite.app`
- Delete and re-drag if app seems corrupted

### Updates
- Delete old HemaSuite.app from Applications
- Install new version following the same steps above

## Version Management

- Semantic versioning in `Cargo.toml` and `tauri.conf.json`
- Build date displayed in Settings > About
- No auto-updater — manual .dmg distribution for updates
- Version changelog maintained in `DISTRIBUTION.md`

## Architecture Changes

None. The Tauri 2 + React + FastAPI + bundled R stack remains unchanged. Only the distribution/packaging layer is simplified.

## Risks

| Risk | Mitigation |
|---|---|
| Gatekeeper blocks app | Install guide + first-launch dialog + Terminal fallback |
| macOS version incompatibility | Test on oldest macOS version in the group (ask recipients) |
| Large bundle size (~623MB) | Acceptable for direct/USB distribution; not a download concern |
| User can't follow instructions | You provide personal support to < 10 people |
