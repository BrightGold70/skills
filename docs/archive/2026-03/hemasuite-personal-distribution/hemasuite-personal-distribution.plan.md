# Plan: HemaSuite Personal Distribution

## Feature Overview

| Item | Detail |
|------|--------|
| Feature Name | hemasuite-personal-distribution |
| Priority | High |
| Complexity | Low-Medium |
| Estimated Scope | 4 files (1 script, 2 docs, 1 config change) |

## Problem Statement

HemaSuite's current build pipeline assumes public distribution (Developer ID signing, notarization, auto-updater). The actual audience is < 10 hematologists on macOS who will receive the app directly. The current pipeline has unnecessary complexity and a $99/year cost dependency.

## Goals

1. Create a single-command build-to-DMG pipeline with ad-hoc signing
2. Remove notarization, auto-updater, and telemetry infrastructure
3. Provide a 1-page install guide for non-technical recipients
4. Document the distribution workflow for the developer

## Non-Goals

- App Store submission
- Windows/Linux support
- Auto-update mechanism
- Crash reporting or analytics
- Developer ID enrollment

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| Build script produces valid .dmg | `scripts/build-dmg.sh` exits 0, .dmg mounts correctly |
| Ad-hoc signed .app launches | App opens after right-click > Open on a clean Mac |
| Install guide is clear | A non-developer can follow it (test with 1 person) |
| Unnecessary code removed | No notarization scripts, no updater config, no telemetry |

## Scope

### In Scope

| Task | Description | Files |
|------|-------------|-------|
| T1: Build script | `scripts/build-dmg.sh` — build, ad-hoc sign, create .dmg | 1 new file |
| T2: Remove notarization | Delete `sign-and-notarize.sh`, remove updater from `tauri.conf.json` | 2 files modified/deleted |
| T3: Install guide | `docs/install-guide.md` — .dmg and USB instructions | 1 new file |
| T4: Distribution doc | `DISTRIBUTION.md` — internal build/version/share workflow | 1 new file |
| T5: First-launch dialog | In-app Gatekeeper bypass guidance on first open | 1 component |
| T6: Simplify entitlements | Remove App Store sandbox entitlements, keep minimum needed | 1 file modified |

### Out of Scope

- Changing the app's core architecture (Tauri + React + FastAPI + R)
- Adding new features to HPW or CSA
- Cross-platform builds

## Dependencies

| Dependency | Status |
|-----------|--------|
| HemaSuite codebase (Phase 0-5 complete) | Done (archived at 100%) |
| `create-dmg` CLI tool | Install via `brew install create-dmg` |
| Xcode Command Line Tools (for `codesign`) | Standard macOS dev setup |

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gatekeeper blocks app on recipient Mac | Medium | Install guide + first-launch dialog + Terminal fallback |
| macOS version incompatibility | Low | Ask recipients for their macOS version, test on oldest |
| Large .dmg size (~623MB) | Low | Acceptable for direct/USB transfer |

## Implementation Order

1. T2: Remove notarization/updater (clean the slate)
2. T6: Simplify entitlements
3. T1: Create build-dmg.sh script
4. T5: First-launch dialog component
5. T3: Install guide
6. T4: Distribution doc

## Design Reference

See: `docs/plans/2026-03-07-hemasuite-personal-distribution-design.md`
