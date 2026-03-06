#!/usr/bin/env bash
# build-dmg.sh
# Build, ad-hoc sign, and package HemaSuite into a .dmg for personal distribution.
#
# Usage:
#   ./scripts/build-dmg.sh
#
# Prerequisites:
#   brew install create-dmg

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

VERSION=$(grep '"version"' src-tauri/tauri.conf.json | head -1 | sed 's/.*: *"\(.*\)".*/\1/')
APP_NAME="HemaSuite"
APP_PATH="src-tauri/target/release/bundle/macos/${APP_NAME}.app"
DMG_DIR="dist"
DMG_PATH="${DMG_DIR}/${APP_NAME}-${VERSION}.dmg"

echo "==> Building ${APP_NAME} v${VERSION}..."
pnpm tauri build --release

if [ ! -d "$APP_PATH" ]; then
  echo "Error: Build failed — $APP_PATH not found"
  exit 1
fi

echo "==> Ad-hoc signing..."
codesign -s - --deep --force "$APP_PATH"

echo "==> Creating DMG..."
mkdir -p "$DMG_DIR"

# Remove existing DMG if present (create-dmg fails otherwise)
[ -f "$DMG_PATH" ] && rm "$DMG_PATH"

create-dmg \
  --volname "${APP_NAME} ${VERSION}" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 150 190 \
  --app-drop-link 450 190 \
  "$DMG_PATH" \
  "$APP_PATH"

echo ""
echo "==> Done!"
echo "    DMG: ${DMG_PATH}"
echo "    Size: $(du -h "$DMG_PATH" | cut -f1)"
echo "    Signing: ad-hoc (right-click > Open on recipient Mac)"
