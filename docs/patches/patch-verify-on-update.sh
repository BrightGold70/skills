#!/usr/bin/env bash
# SessionStart: re-verify every locally carried plugin patch after a plugin update.
#
# The patches in orca/skills docs/patches/ live in version-pinned plugin caches that an
# update replaces wholesale, so an update silently drops them. This re-runs each
# docs/patches/*/verify.{js,py} whenever the installed-plugin fingerprint changes, and
# says nothing while they all pass. Any non-zero verify is reported every session until
# it passes again (exit 1 = patch MISSING, re-apply per its README; exit 2 = could not
# judge, which is not a pass).
#
# Output is SessionStart JSON: systemMessage for the user, additionalContext for Claude.
#
# Install (each Mac; the plugin cache is machine-local):
#   cp /Users/kimhawk/orca/skills/docs/patches/patch-verify-on-update.sh ~/.claude/hooks/
#   then add a SessionStart command hook to ~/.claude/settings.json:
#     "command": "bash $HOME/.claude/hooks/patch-verify-on-update.sh", "timeout": 120
# Installed as a COPY, not a symlink: the shared orca/skills tree can be checked out on a
# branch that lacks this file. After editing it here, copy it again. Force a re-check by
# deleting ~/.claude/state/patch-verify.state.

PATCHES="${PATCH_VERIFY_DIR:-/Users/kimhawk/orca/skills/docs/patches}"
INSTALLED="$HOME/.claude/plugins/installed_plugins.json"
STATE_DIR="$HOME/.claude/state"
STATE="$STATE_DIR/patch-verify.state"

emit() {  # $1 = message (plain text)
  python3 - "$1" <<'PY'
import json, sys
msg = sys.argv[1]
print(json.dumps({
    "systemMessage": msg,
    "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg},
}))
PY
}

if [ ! -d "$PATCHES" ]; then
  emit "[patch-verify] cannot check carried plugin patches: $PATCHES is missing (is orca/skills checked out on a branch that has docs/patches/?)"
  exit 0
fi

shopt -s nullglob
scripts=("$PATCHES"/*/verify.js "$PATCHES"/*/verify.py)
if [ ${#scripts[@]} -eq 0 ]; then
  emit "[patch-verify] cannot check carried plugin patches: no verify.js/verify.py under $PATCHES"
  exit 0
fi

fp="$( { cat "$INSTALLED" 2>/dev/null; ls -1 "$HOME/.claude/plugins/cache/bkit-marketplace/bkit" 2>/dev/null; cat "${scripts[@]}"; } | shasum -a 256 | awk '{print $1}')"

if [ -f "$STATE" ] && [ "$(sed -n 1p "$STATE")" = "$fp" ] && [ "$(sed -n 2p "$STATE")" = "OK" ]; then
  exit 0
fi

failed=()
for s in "${scripts[@]}"; do
  name="$(basename "$(dirname "$s")")"
  case "$s" in
    *.js) out="$(cd /tmp && timeout 30 node "$s" 2>&1)"; rc=$? ;;
    *.py) out="$(cd /tmp && timeout 30 python3 "$s" 2>&1)"; rc=$? ;;
  esac
  if [ "$rc" -ne 0 ]; then
    last="$(printf '%s\n' "$out" | grep -v '^[[:space:]]*$' | tail -1 | cut -c1-160)"
    case "$rc" in
      1) why="patch MISSING or wrong — re-apply per $PATCHES/$name/README.md" ;;
      2) why="could not judge (not a pass) — check by hand" ;;
      124) why="verify timed out after 30s" ;;
      *) why="verify exited $rc" ;;
    esac
    failed+=("$name: $why [$last]")
  fi
done

mkdir -p "$STATE_DIR"
if [ ${#failed[@]} -eq 0 ]; then
  printf '%s\nOK\n%s\n' "$fp" "$(date -u +%FT%TZ)" > "$STATE"
  exit 0
fi

printf '%s\nFAIL\n%s\n' "$fp" "$(date -u +%FT%TZ)" > "$STATE"
msg="[patch-verify] ${#failed[@]} of ${#scripts[@]} carried plugin patches failed verification (plugins changed since the last pass):"
for f in "${failed[@]}"; do msg="$msg
- $f"; done
emit "$msg"
exit 0
