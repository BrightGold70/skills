#!/bin/bash
# sign-r-dylibs.sh
# Signs all R runtime dylibs individually (required for macOS notarization).
#
# Usage: ./scripts/sign-r-dylibs.sh [APP_PATH] [SIGNING_IDENTITY]

set -euo pipefail

APP_PATH="${1:-src-tauri/target/release/bundle/macos/HemaSuite.app}"
IDENTITY="${2:-Developer ID Application: -}"
ENTITLEMENTS="src-tauri/Entitlements.plist"

if [ ! -f "$ENTITLEMENTS" ]; then
  echo "Error: Entitlements.plist not found at $ENTITLEMENTS"
  exit 1
fi

R_RUNTIME_DIR="$APP_PATH/Contents/Resources/resources/r-runtime"

if [ ! -d "$R_RUNTIME_DIR" ]; then
  echo "Warning: R runtime not found at $R_RUNTIME_DIR"
  echo "Skipping R dylib signing (R may not be bundled yet)"
  exit 0
fi

echo "Signing R dylibs in $R_RUNTIME_DIR..."

count=0
find "$R_RUNTIME_DIR" \( -name "*.dylib" -o -name "*.so" \) | while read -r lib; do
  codesign --force --sign "$IDENTITY" \
    --entitlements "$ENTITLEMENTS" --timestamp "$lib"
  count=$((count + 1))
done

echo "Signing Python binaries..."
PYTHON_DIR="$APP_PATH/Contents/Resources/resources/python"
if [ -d "$PYTHON_DIR" ]; then
  find "$PYTHON_DIR" \( -name "*.dylib" -o -name "*.so" \) | while read -r lib; do
    codesign --force --sign "$IDENTITY" \
      --entitlements "$ENTITLEMENTS" --timestamp "$lib"
  done
fi

echo "R dylib signing complete."
