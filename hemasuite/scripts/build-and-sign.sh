#!/bin/bash
# build-and-sign.sh
# Unified build, sign, and notarize workflow for HemaSuite macOS app.
#
# Usage:
#   ./scripts/build-and-sign.sh                    # Full build + sign + notarize
#   ./scripts/build-and-sign.sh --dry-run           # Build only, skip signing
#
# Required environment variables (unless --dry-run):
#   APPLE_SIGNING_IDENTITY  - Developer ID Application certificate name
#   APPLE_ID                - Apple ID email for notarization
#   APPLE_TEAM_ID           - Apple Developer Team ID
#   APPLE_APP_PASSWORD      - App-specific password for notarization

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
  esac
done

# ─── Step 1: Validate environment ───────────────────────────────────────────
if [ "$DRY_RUN" = false ]; then
  if [ -z "${APPLE_SIGNING_IDENTITY:-}" ]; then
    echo "Error: APPLE_SIGNING_IDENTITY is not set"
    echo "Example: export APPLE_SIGNING_IDENTITY='Developer ID Application: Your Name (TEAMID)'"
    exit 1
  fi

  if [ -z "${APPLE_ID:-}" ] || [ -z "${APPLE_TEAM_ID:-}" ] || [ -z "${APPLE_APP_PASSWORD:-}" ]; then
    echo "Error: APPLE_ID, APPLE_TEAM_ID, and APPLE_APP_PASSWORD must be set for notarization"
    exit 1
  fi
fi

# ─── Step 2: Build the app with Tauri ───────────────────────────────────────
echo "==> Building HemaSuite..."
cd "$PROJECT_DIR"
TAURI_BUILD_TARGET="${TAURI_BUILD_TARGET:-universal-apple-darwin}"
pnpm tauri build --target "$TAURI_BUILD_TARGET"

APP_PATH="src-tauri/target/release/bundle/macos/HemaSuite.app"
DMG_PATH="src-tauri/target/release/bundle/dmg/HemaSuite_0.1.0_$(uname -m).dmg"

if [ ! -d "$APP_PATH" ]; then
  echo "Error: Build failed — $APP_PATH not found"
  exit 1
fi

echo "==> Build complete: $APP_PATH"

if [ "$DRY_RUN" = true ]; then
  echo "==> DRY_RUN: Skipping signing and notarization"
  echo "==> DMG available at: $DMG_PATH"
  exit 0
fi

# ─── Step 3: Sign R dylibs ─────────────────────────────────────────────────
echo "==> Signing R/Python dylibs..."
bash "$SCRIPT_DIR/sign-r-dylibs.sh" "$APP_PATH" "$APPLE_SIGNING_IDENTITY"

# ─── Step 4: Sign the full app bundle ──────────────────────────────────────
echo "==> Signing app bundle..."
codesign --deep --force --verify --verbose \
  --sign "$APPLE_SIGNING_IDENTITY" \
  --entitlements "src-tauri/Entitlements.plist" \
  --timestamp \
  "$APP_PATH"

echo "==> Verifying signature..."
codesign --verify --verbose=2 "$APP_PATH"
spctl --assess --type execute --verbose "$APP_PATH"

# ─── Step 5: Create signed DMG ─────────────────────────────────────────────
echo "==> Signing DMG..."
codesign --force --sign "$APPLE_SIGNING_IDENTITY" --timestamp "$DMG_PATH"

# ─── Step 6: Notarize ──────────────────────────────────────────────────────
echo "==> Submitting for notarization..."
xcrun notarytool submit "$DMG_PATH" \
  --apple-id "$APPLE_ID" \
  --team-id "$APPLE_TEAM_ID" \
  --password "$APPLE_APP_PASSWORD" \
  --wait

echo "==> Stapling notarization ticket..."
xcrun stapler staple "$DMG_PATH"

echo ""
echo "==> Build complete!"
echo "    DMG: $DMG_PATH"
echo "    Signed: Yes"
echo "    Notarized: Yes"
