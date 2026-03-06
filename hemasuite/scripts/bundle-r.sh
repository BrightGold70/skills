#!/bin/bash
# bundle-r.sh — Package R runtime with pre-installed packages for HemaSuite macOS app bundle.
#
# Copies the system R framework into a relocatable bundle and installs
# all R packages required by CSA analysis scripts.
# Output: hemasuite/src-tauri/resources/r-runtime/ (~400MB)
#
# Usage:
#   ./hemasuite/scripts/bundle-r.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="$PROJECT_ROOT/src-tauri/resources/r-runtime"

# Required R packages (derived from CSA scripts library() calls)
# CRAN packages (installed via install.packages with binary)
R_PACKAGES=(
  broom
  cmprsk
  dplyr
  flextable
  forestplot
  ggplot2
  haven
  lubridate
  officer
  pwr
  readxl
  survival
  survminer
  table1
  tidyr
)

# GitHub-only packages (installed via remotes::install_github)
R_GITHUB_PACKAGES=(
  "davidsjoberg/ggsankey"
)

echo "=== HemaSuite R Runtime Bundler ==="

# Verify system R exists
R_HOME=$(R RHOME 2>/dev/null) || { echo "Error: R not found. Install R 4.5+ first."; exit 1; }
R_VERSION=$(R --version 2>/dev/null | head -1)
echo "System R: $R_VERSION"
echo "R_HOME:   $R_HOME"
echo "Dest:     $DEST"
echo ""

# Clean previous bundle
if [ -d "$DEST" ]; then
  echo "Removing previous R bundle..."
  rm -rf "$DEST"
fi
mkdir -p "$DEST"

# Copy R framework to bundle
echo "Copying R runtime from $R_HOME..."
cp -R "$R_HOME/" "$DEST/"

# Fix the R and Rscript shell scripts to use relocatable R_HOME
# The key trick: use the script's own location to determine R_HOME
echo "Patching R/Rscript for relocatability..."

cat > "$DEST/bin/R" << 'RSCRIPT'
#!/bin/bash
# Relocatable R wrapper for HemaSuite app bundle
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
export R_HOME="$(cd "$SELF_DIR/.." && pwd)"
exec "$R_HOME/bin/R.original" "$@"
RSCRIPT

# Preserve original R binary
if [ -f "$DEST/bin/R" ] && [ ! -f "$DEST/bin/R.original" ]; then
  # The R in bin/ is typically a shell script itself
  cp "$R_HOME/bin/R" "$DEST/bin/R.original"
fi

cat > "$DEST/bin/Rscript" << 'RSCRIPT'
#!/bin/bash
# Relocatable Rscript wrapper for HemaSuite app bundle
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
export R_HOME="$(cd "$SELF_DIR/.." && pwd)"
exec "$R_HOME/bin/Rscript.original" "$@"
RSCRIPT

if [ -f "$DEST/bin/Rscript" ] && [ ! -f "$DEST/bin/Rscript.original" ]; then
  cp "$R_HOME/bin/Rscript" "$DEST/bin/Rscript.original"
fi

chmod +x "$DEST/bin/R" "$DEST/bin/Rscript"

# Install required packages into bundle's library
BUNDLE_LIB="$DEST/library"
echo ""
echo "Installing R packages into bundle library..."
echo "Packages: ${R_PACKAGES[*]}"
echo ""

# Build the install.packages() call
PKG_LIST=$(printf '"%s",' "${R_PACKAGES[@]}")
PKG_LIST="${PKG_LIST%,}"  # Remove trailing comma

"$R_HOME/bin/Rscript" --no-save --no-restore -e "
  pkgs <- c(${PKG_LIST})
  # Only install packages not already in the bundle library
  installed <- rownames(installed.packages(lib.loc='${BUNDLE_LIB}'))
  missing <- setdiff(pkgs, installed)
  if (length(missing) > 0) {
    cat('Installing:', paste(missing, collapse=', '), '\n')
    install.packages(missing, lib='${BUNDLE_LIB}',
                     repos='https://cloud.r-project.org',
                     type='binary', quiet=TRUE)
  } else {
    cat('All packages already installed.\n')
  }
  cat('CRAN packages done.\n')
"

# Install GitHub-only packages
if [ ${#R_GITHUB_PACKAGES[@]} -gt 0 ]; then
  echo ""
  echo "Installing GitHub-only packages..."
  for gh_pkg in "${R_GITHUB_PACKAGES[@]}"; do
    pkg_name=$(basename "$gh_pkg")
    echo "  Installing $gh_pkg..."
    "$R_HOME/bin/Rscript" --no-save --no-restore -e "
      .libPaths(c('${BUNDLE_LIB}', .libPaths()))
      if (!requireNamespace('remotes', quietly=TRUE)) {
        install.packages('remotes', lib='${BUNDLE_LIB}', repos='https://cloud.r-project.org', quiet=TRUE)
      }
      remotes::install_github('${gh_pkg}', lib='${BUNDLE_LIB}', quiet=TRUE, upgrade='never')
    "
  done
fi

# Verify ALL packages load (CRAN + GitHub)
ALL_PKGS=("${R_PACKAGES[@]}")
for gh_pkg in "${R_GITHUB_PACKAGES[@]}"; do
  ALL_PKGS+=("$(basename "$gh_pkg")")
done
ALL_PKG_LIST=$(printf '"%s",' "${ALL_PKGS[@]}")
ALL_PKG_LIST="${ALL_PKG_LIST%,}"

echo ""
echo "Verifying all packages..."
"$R_HOME/bin/Rscript" --no-save --no-restore -e "
  pkgs <- c(${ALL_PKG_LIST})
  for (p in pkgs) {
    if (!require(p, lib.loc='${BUNDLE_LIB}', character.only=TRUE, quietly=TRUE)) {
      stop(paste('Failed to load package:', p))
    }
  }
  cat('All', length(pkgs), 'packages verified.\n')
"

# Clean up unnecessary files to reduce size
echo ""
echo "Cleaning up bundle..."
# Remove documentation (saves ~50MB)
find "$DEST/library" -type d -name "doc" -exec rm -rf {} + 2>/dev/null || true
find "$DEST/library" -type d -name "help" -exec rm -rf {} + 2>/dev/null || true
find "$DEST/library" -type d -name "html" -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -name "*.pdf" -delete 2>/dev/null || true
# Remove example data (saves ~20MB)
find "$DEST/library" -type d -name "demo" -exec rm -rf {} + 2>/dev/null || true

# Report size
BUNDLE_SIZE=$(du -sh "$DEST" | cut -f1)
PKG_COUNT=$(ls -d "$BUNDLE_LIB"/*/ 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "=== R runtime bundle complete ==="
echo "Location: $DEST"
echo "Size:     $BUNDLE_SIZE"
echo "Packages: $PKG_COUNT installed"
echo ""

# Smoke test with relocatable wrapper
echo "Smoke test..."
"$DEST/bin/Rscript" -e "library(survival); library(ggplot2); cat('R bundle OK\n')"
echo "All checks passed."
