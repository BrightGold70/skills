#!/bin/bash
# bundle-python.sh — Download and package standalone Python for HemaSuite macOS app bundle.
#
# Uses python-build-standalone (astral-sh) for a fully relocatable Python.
# Output: hemasuite/src-tauri/resources/python/ (~50MB with pip packages)
#
# Usage:
#   ./hemasuite/scripts/bundle-python.sh [--arch arm64|x86_64]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$PROJECT_ROOT/src-tauri/resources/python"
SIDECAR_DIR="$PROJECT_ROOT/src-tauri/sidecar"

PYTHON_VERSION="3.14.3"
PBS_TAG="20260303"
ARCH="${1:-$(uname -m)}"

# Normalize architecture name
case "$ARCH" in
  --arch) ARCH="${2:-$(uname -m)}" ;;
  arm64|aarch64) ARCH="aarch64" ;;
  x86_64) ARCH="x86_64" ;;
  *) echo "Error: unsupported architecture: $ARCH"; exit 1 ;;
esac

TARBALL="cpython-${PYTHON_VERSION}+${PBS_TAG}-${ARCH}-apple-darwin-install_only_stripped.tar.gz"
URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PBS_TAG}/${TARBALL}"
DOWNLOAD_DIR="${TMPDIR:-/tmp}/hemasuite-bundle"

echo "=== HemaSuite Python Bundler ==="
echo "Python:  ${PYTHON_VERSION}"
echo "Arch:    ${ARCH}"
echo "Dest:    ${DEST}"
echo ""

# Clean previous bundle
if [ -d "$DEST" ]; then
  echo "Removing previous Python bundle..."
  rm -rf "$DEST"
fi
mkdir -p "$DEST"
mkdir -p "$DOWNLOAD_DIR"

# Download if not cached
CACHED_TARBALL="$DOWNLOAD_DIR/$TARBALL"
if [ -f "$CACHED_TARBALL" ]; then
  echo "Using cached download: $CACHED_TARBALL"
else
  echo "Downloading $TARBALL..."
  curl -fSL --progress-bar -o "$CACHED_TARBALL" "$URL"
fi

# Extract — python-build-standalone extracts to python/
echo "Extracting..."
tar xzf "$CACHED_TARBALL" -C "$DEST" --strip-components=1

# Verify extraction
PYTHON_BIN="$DEST/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
  echo "Error: Python binary not found at $PYTHON_BIN"
  exit 1
fi

echo "Bundled Python version:"
"$PYTHON_BIN" --version

# Install sidecar dependencies
echo ""
echo "Installing sidecar pip packages..."
"$PYTHON_BIN" -m pip install --quiet --no-cache-dir \
  -r "$SIDECAR_DIR/requirements.txt"

# Remove test-only packages from bundle (keep runtime deps like anyio, httpx)
echo "Removing test-only packages from bundle..."
"$PYTHON_BIN" -m pip uninstall --yes pytest pytest-anyio 2>/dev/null || true

# Strip __pycache__ and test dirs to reduce size
echo "Cleaning up..."
find "$DEST" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -name "*.pyc" -delete 2>/dev/null || true

# Report size
BUNDLE_SIZE=$(du -sh "$DEST" | cut -f1)
echo ""
echo "=== Python bundle complete ==="
echo "Location: $DEST"
echo "Size:     $BUNDLE_SIZE"
echo ""

# Smoke test
echo "Smoke test..."
"$PYTHON_BIN" -c "import fastapi; import uvicorn; print('fastapi OK')"
echo "All checks passed."
