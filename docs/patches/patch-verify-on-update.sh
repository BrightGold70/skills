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

# Global npm packages that carry a patch too (omc-codex-mcp-no-type patches the `omc` CLI).
# installed_plugins.json does not change on `npm update -g`, so fingerprint each package's
# package.json plus the mtime+size of its patched files: a same-version reinstall rewrites
# the files and drops the patch without changing the version.
NPM_ROOT="${PATCH_VERIFY_NPM_ROOT:-/opt/homebrew/lib/node_modules}"
NPM_FILES=(
  "oh-my-claude-sisyphus/package.json"
  "oh-my-claude-sisyphus/dist/installer/mcp-registry.js"
  "oh-my-claude-sisyphus/bridge/cli.cjs"
)
npm_fp() {
  local rel
  for rel in "${NPM_FILES[@]}"; do
    stat -f '%N %m %z' "$NPM_ROOT/$rel" 2>/dev/null || echo "absent $rel"
  done
}

# Codex plugins, configs and skills (codex-duplicate-handoff). Its STALE check pins a
# version-bearing SKILL.md path in each Codex config: a plugin update adds a version folder and
# removes the old one without touching anything above, so fingerprint each Codex home's plugin
# version folders and its config's skills.config / mattpocock lines -- only those lines, and
# without line numbers, because Codex adds a table on every newly trusted project. Its DUPLICATE
# check looks for a second skill named `handoff`, so fingerprint every SKILL.md under each home's
# skills/ and ~/.agents/skills: path, the directory it resolves to (a link to the repo replaced by
# a real copy keeps path and name), and a hash of its content.
# Homes are deduplicated and sorted by realpath and read through it, so CODEX_HOME set, unset or
# naming any Orca account gives the same fingerprint. -maxdepth 3 matches verify.py's MAX_DEPTH
# (skills/<a>/<b>/SKILL.md) and bounds the walk when a skill folder links to a big tree.
skills_fp() {  # $1 = a skills root (a realpath)
  [ -d "$1" ] || return 0
  find -L "$1" -maxdepth 3 -name SKILL.md -type f 2>/dev/null | LC_ALL=C sort | while IFS= read -r f; do
    # The whole SKILL.md, hashed. Parsing its frontmatter here (a name line, then an awk block
    # reader) twice missed changes verify.py does see: a lost opening `---`, a renamed block
    # scalar, and under a UTF-8 locale a BOM or an indented fence. A content hash cannot diverge
    # from verify's reader; the cost is that editing ANY SKILL.md under these folders re-runs
    # every carried verify once (about a second on this host), then the state is OK again.
    printf '%s %s %s\n' "${f#"$1"/}" "$(realpath "$(dirname "$f")" 2>/dev/null)" \
      "$(shasum -a 256 < "$f" 2>/dev/null | cut -c1-16)"
  done
}
codex_fp() {
  local h r homes=""
  for h in "$HOME/.codex" ${CODEX_HOME:+"$CODEX_HOME"} \
           "$HOME/Library/Application Support/orca/codex-accounts"/*/home; do
    [ -d "$h" ] || continue
    r="$(realpath "$h" 2>/dev/null)" || r="$h"
    homes="$homes$r"$'\n'
  done
  printf '%s' "$homes" | LC_ALL=C sort -u | while IFS= read -r h; do
    [ -n "$h" ] || continue
    echo "$h"
    r="$(realpath "$h/plugins/cache" 2>/dev/null)" && ls -1d "$r"/*/*/*/ 2>/dev/null
    [ -f "$h/config.toml" ] && grep -A2 -F -e '[[skills.config]]' -e 'mattpocock' "$h/config.toml" 2>/dev/null
    skills_fp "$h/skills"
  done
  r="$(realpath "$HOME/.agents/skills" 2>/dev/null)" && skills_fp "$r"
}

fp="$( { cat "$INSTALLED" 2>/dev/null; ls -1 "$HOME/.claude/plugins/cache/bkit-marketplace/bkit" 2>/dev/null; npm_fp; codex_fp; cat "${scripts[@]}"; } | shasum -a 256 | awk '{print $1}')"

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
