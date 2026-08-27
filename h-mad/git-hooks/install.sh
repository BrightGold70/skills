#!/usr/bin/env bash
# install.sh — install the h-mad skill's git hooks into a local clone.
#
# Git hooks live in .git/hooks, which is NOT version-controlled, so a hook that
# ships inside a skill does nothing until each clone links it. This installer
# symlinks (not copies) the skill's hook into the target repo's common hooks
# dir, so later edits to the skill take effect immediately with no re-install
# and no drift between the shipped hook and the running one.
#
# The common hooks dir is shared by all linked worktrees of a clone, so one
# install covers every worktree. A separate clone needs its own run.
#
# Usage:
#   h-mad/git-hooks/install.sh                    # install into the cwd's repo
#   h-mad/git-hooks/install.sh --repo <dir>       # install into another clone
#   h-mad/git-hooks/install.sh --force            # overwrite a foreign hook
#   h-mad/git-hooks/install.sh --uninstall        # remove only symlinks we own
#
# Hooks installed:
#   pre-push — blocks a push when any H-MAD mutation anchor has drifted.

set -euo pipefail

HOOKS=(pre-push)

SRC_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

FORCE=0
UNINSTALL=0
REPO=""
while [ $# -gt 0 ]; do
    case "$1" in
        --force)     FORCE=1 ;;
        --uninstall) UNINSTALL=1 ;;
        --repo)      shift; [ $# -gt 0 ] || { echo "install.sh: --repo needs a directory" >&2; exit 2; }; REPO=$1 ;;
        --repo=*)    REPO=${1#--repo=} ;;
        -h|--help)   sed -n '2,21p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *)           echo "install.sh: unknown option '$1'" >&2; exit 2 ;;
    esac
    shift
done

if [ -n "$REPO" ]; then
    [ -d "$REPO" ] || { echo "install.sh: no such directory: $REPO" >&2; exit 2; }
    cd -- "$REPO"
fi

git rev-parse --show-toplevel >/dev/null 2>&1 || {
    echo "install.sh: $(pwd) is not inside a git repository." >&2
    exit 2
}

# --path-format=absolute is load-bearing: --git-common-dir alone returns a
# RELATIVE '.git', which resolves against the CALLER's cwd and silently answers
# a question about the wrong repository. Requires git >= 2.31.
COMMON_DIR=$(git rev-parse --path-format=absolute --git-common-dir)
DEST_DIR="$COMMON_DIR/hooks"

if [ -n "$(git config --get core.hooksPath || true)" ]; then
    echo "install.sh: core.hooksPath is set to '$(git config --get core.hooksPath)'." >&2
    echo "            Git will read hooks from there, not from $DEST_DIR." >&2
    echo "            Unset it (git config --unset core.hooksPath) or install by hand." >&2
    exit 1
fi

mkdir -p "$DEST_DIR"

for hook in "${HOOKS[@]}"; do
    src="$SRC_DIR/$hook"
    dest="$DEST_DIR/$hook"

    [ -f "$src" ] || { echo "install.sh: missing source hook $src" >&2; exit 1; }

    if [ "$UNINSTALL" -eq 1 ]; then
        if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
            rm "$dest"
            echo "uninstalled: $hook"
        elif [ -e "$dest" ]; then
            echo "skipped: $dest is not our symlink — left in place"
        else
            echo "skipped: $hook not installed"
        fi
        continue
    fi

    chmod +x "$src"

    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
        echo "already installed: $hook -> $src"
        continue
    fi

    if [ -e "$dest" ] || [ -L "$dest" ]; then
        if [ "$FORCE" -eq 1 ]; then
            rm "$dest"
        else
            backup="$dest.bak.$(date +%Y%m%d%H%M%S)"
            mv "$dest" "$backup"
            echo "backed up existing hook -> $backup"
        fi
    fi

    ln -s "$src" "$dest"
    echo "installed: $hook -> $src"
done

if [ "$UNINSTALL" -eq 1 ]; then
    exit 0
fi

# Smoke-test: the hook must exit 0 on the current, presumed-clean tree. A
# non-zero here means it would block every push from this clone.
for hook in "${HOOKS[@]}"; do
    if "$DEST_DIR/$hook" origin "$(git remote get-url origin 2>/dev/null || echo none)" </dev/null; then
        echo "verified: $hook exits 0 on the current tree"
    else
        echo "WARNING: $hook exited non-zero on the current tree — it will block pushes." >&2
        echo "         Fix the reported drift, or run with --uninstall to remove it." >&2
        exit 1
    fi
done
