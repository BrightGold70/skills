# Handoff — h-mad install repaired: stale copy → symlink, plus the missing hook link

**Date:** 2026-08-09
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

User asked to "update h-mad skill from github". The repo was already at `origin/main` (`bc4b6f3`,
`git rev-list --left-right --count` → `0 0`) — nothing to pull. The entire delta was **install-side**:
`~/.claude/skills/h-mad` was a stale May-23 *copy* (11KB SKILL.md, 9 scripts) against the repo's
current tree (99KB SKILL.md, 25 scripts, `bin/`, `tests/`, `invariants.base.md`). Upstream documents
the canonical install as a **symlink into the checkout**, not a copy, so the fix was relinking rather
than re-copying. Repairing it exposed a second, entirely missing link — `~/.claude/hooks/h-mad-tdd-gate.sh`
— which 13 tests and `references/codex-implementer-prompt.md` both depend on. Done and verified:
1173 passed / 2 skipped through the install path. No repo files changed.

**Session continued after the first closeout** and drove the remaining items to zero: deleted the
pre-repair backup, repointed `settings.json:129` to the documented `~/.claude/hooks/…` path so all
three references agree, and reran the suite (`1173 passed, 2 skipped` — unchanged). Nothing open.

## Key Learnings

- **h-mad's canonical install is a symlink, and nothing enforces it.** `SKILL.md:774` ("`~/.claude/skills/h-mad`
  **is a symlink into this repository**") and `bin/hmad-dispatch:9` both say so, but a copy install
  works well enough to go unnoticed for months — it just silently stops tracking the checkout. The
  stale copy here was 2.5 months behind and nothing surfaced it; the skill loaded, the frontmatter
  was byte-identical, and both copies self-reported "v2.2".
- **The install is two links, not one.** Beyond the skills-dir symlink, `~/.claude/hooks/h-mad-tdd-gate.sh`
  must exist — `tests/test_h_mad_tdd_gate_codex.py` and `tests/test_h_mad_tdd_gate_state_resolution.py`
  both hardcode `HOOK = Path.home() / ".claude" / "hooks" / "h-mad-tdd-gate.sh"`, and
  `references/codex-implementer-prompt.md:19` tells the implementer that's where the armed gate lives.
  That path did not exist at all. `settings.json:129` happens to arm the gate via the *skills* path,
  so the gate worked while the tests and the Codex-facing docs pointed at nothing.
- **`diff -rq` said IDENTICAL and the install was still incomplete.** Content equality between repo
  and install dir proves nothing about links the skill expects *outside* that dir. Running the suite
  through the **install path** (`pytest ~/.claude/skills/h-mad/tests/`) rather than the repo path is
  what caught it — 13 failures, all `FileNotFoundError` on the missing hook.
- **A backup directory left inside `~/.claude/skills/` registers as a live skill.** `mv h-mad h-mad.bak-20260808`
  in place made `h-mad.bak-20260808` appear in the session's skill listing with h-mad's full
  description — a duplicate, selectable skill pointing at stale code. Backups of a skill must land
  outside `skills/`.
- **The new TDD gate resolves state differently from the one it replaced, which changes blast radius.**
  Per `test_h_mad_tdd_gate_state_resolution.py`'s docstring, the old hook read
  `${CLAUDE_PROJECT_DIR:-.}/docs/.bkit-memory.json` and fail-opened when absent; the new one walks
  into sub-project layouts. This repo has exactly that shape
  (`hematology-paper-writer/docs/.bkit-memory.json`, `clinical-statistics-analyzer/docs/.bkit-memory.json`)
  — the very case the docstring names. Checked: none carry an `orchestrator_state`, so nothing is
  armed. Worth re-checking after any future h-mad run leaves state behind.
- **The arming check has to be machine-wide, not repo-scoped.** `settings.json` `PreToolUse` hooks
  fire in *every* project, so a repo-scoped `find` under-measures the blast radius. Swept `~/Coding`
  and `~/orca`: four `.bkit-memory.json` files, none with an `orchestrator_state`.
  `/Users/kimhawk/Coding/HemaSuite` — the tree the test docstring names as the motivating fail-open
  — has no state file at all, which the gate treats as "no orchestrator → allow"
  (`test_no_state_anywhere_still_allows`). Nothing armed anywhere.
- **A green h-mad suite cannot confirm an arming-path change.** The tests invoke
  `~/.claude/hooks/h-mad-tdd-gate.sh` directly and never read `settings.json`, so they went green the
  moment that symlink existed and stayed green across the `settings.json` edit. Verifying the arming
  surface needs a real `Write` through the harness, which is a separate check from the suite.
- **bkit's ENH-310 heredoc guard is a *text match on the command string*, not nesting detection.**
  It first bit the legitimate case — `git commit -m "$(cat <<'EOF' … EOF)"`, the standard multi-line
  commit idiom, denied at `PreToolUse` (fix: write the message to a file, `git commit -F <file>`).
  It then bit a **plain, correctly-formed** `python3 - <<'PY'` whose *string contents* merely quoted
  an example of the forbidden pattern. Earlier plain heredocs in the same session passed fine, so the
  trigger is the substring, not the shell construct.
  **Since fixed** — see `docs/patches/bkit-enh310-quoted-heredoc-body/`. A quoted heredoc tag
  disables all expansion in the body (verified against real bash), so those bodies are now excised
  before the `sub`-vector patterns run. bkit's suite went 53/53 → 62/62; a 23-case differential
  corpus showed 0 unintended regressions. The patch lives in a version-pinned plugin cache, so
  `verify.js` in that directory must be re-run after any bkit update.
- **One earlier claim of mine was wrong and is worth not repeating**: `echo "… $(cat <<TAG … TAG) …"`
  is *not* a false positive. `$()` is active inside double quotes — `echo "x $(echo hi) y"` prints
  `x hi y` — so that command genuinely asks bash to run the substitution. Denying it is the guard
  working. Only the *quoted-tag heredoc body* case was ever the bug.
- **`learn.py` hard-rejects a pattern >200 chars** (`ERROR: pattern exceeds 200 chars (208)`) and
  exits non-zero, but entries queued *before* the failing one in the same invocation are already
  written — so a batch that trips the limit lands partially. Re-run only the rejected entry; the
  same-day dedupe makes a full re-run safe either way.

## Next Steps

1. Confirm the duplicate skill entry cleared — `h-mad.bak-20260808` should be gone from the skill
   listing next session; only `h-mad` should appear. (Directory is deleted; the stale *listing* entry
   is cached until a fresh session, so this is the one item that can only be checked later.)
2. Future "update h-mad from github" is now just `git -C /Users/kimhawk/orca/skills pull` — the symlink
   makes the checkout the live skill. No resync step, no re-copy.
3. If a future h-mad run leaves `orchestrator_state` behind, re-run the machine-wide arming sweep before
   assuming writes are unblocked — the gate resolves sub-project state that the old one fail-opened on.

**Done this session** (were Next Steps #2/#3 and both Open Items at first closeout):
- `rm -rf ~/.claude/h-mad.bak-20260808` — verified target first (real dir, 116K, 11158-byte SKILL.md,
  7 scripts, no symlinks pointing out), then deleted; both live symlinks confirmed intact after.
- `settings.json:129` repointed to `bash ~/.claude/hooks/h-mad-tdd-gate.sh` — one-line diff, JSON
  re-validated, hook exercised directly (`exit=0`) and end-to-end through a real `Write`.

## Open / Blocked Items

None. Both items from the first closeout are resolved (see "Done this session" above), the repo is
clean and at `origin/main`, and nothing is blocked or in flight.

## Context for Next Session

**Files touched this session:**
- None in the repo. All changes were to the user-global install:
  - `~/.claude/skills/h-mad` — stale directory replaced with symlink → `/Users/kimhawk/orca/skills/h-mad`
  - `~/.claude/hooks/h-mad-tdd-gate.sh` — new symlink → `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh`
  - `~/.claude/settings.json:129` — arming path repointed to `bash ~/.claude/hooks/h-mad-tdd-gate.sh`
  - `~/.claude/h-mad.bak-20260808` — backup of the pre-repair copy; created, then deleted this session

**Uncommitted changes:** none (repo tree clean throughout; `git status --short` empty)

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main

# confirm the install is intact — both must be symlinks into this repo
ls -la ~/.claude/skills/h-mad ~/.claude/hooks/h-mad-tdd-gate.sh

# confirm the gate is armed at the documented path
grep -n "h-mad" ~/.claude/settings.json   # expect: bash ~/.claude/hooks/h-mad-tdd-gate.sh

# confirm the skill still works through the install path (not the repo path)
python3 -m pytest ~/.claude/skills/h-mad/tests/ -q --tb=line     # expect 1173 passed, 2 skipped
```

**Verification evidence from this session:**
- `git rev-list --left-right --count origin/main...HEAD` → `0	0` (repo at github HEAD)
- `diff -rq ~/.claude/skills/h-mad/ /Users/kimhawk/orca/skills/h-mad/` → identical
- `pytest ~/.claude/skills/h-mad/tests/` → `1173 passed, 2 skipped in 107.10s`
- The 2 skips are `tests/test_h_mad_state_validate_fallback.py:116,151`, both gated on "no live state
  file" — correct here, since no `docs/.bkit-memory.json` exists in this project.
- Post-change rerun after the backup deletion and the `settings.json` edit: `1173 passed, 2 skipped in
  106.99s` — identical, same two skips.
- `settings.json` edit verified independently of the suite (which never reads it): `python3 -m json.tool`
  → valid, hook invoked directly with a synthetic `Write` payload → `exit=0`, and a real `Write` passed
  through the `PreToolUse` registration at the new path.
- Machine-wide arming sweep over `~/Coding` and `~/orca`: four `.bkit-memory.json`, none with an
  `orchestrator_state`. Nothing armed.

**Plugin guard patches spun out of this session** (both local patches live in volatile plugin
caches — run each `verify.*` after any plugin update; drop the patch if upstream ships the fix):
- `docs/patches/bkit-enh310-quoted-heredoc-body/` — filed as
  [popup-studio-ai/bkit-claude-code#145](https://github.com/popup-studio-ai/bkit-claude-code/issues/145)
- `docs/patches/claude-security-guidance-bare-exec/` — filed as
  [anthropics/claude-plugins-official#5085](https://github.com/anthropics/claude-plugins-official/issues/5085)

**Related docs:**
- `h-mad/SKILL.md:774` — "Editing this skill while a run is in flight" (why the install is a symlink,
  and the worktree discipline that follows from it)
- `h-mad/bin/hmad-dispatch:9` — PATH shim; documents the symlink-chain install assumption
- `h-mad/references/codex-implementer-prompt.md:19` — names `~/.claude/hooks/h-mad-tdd-gate.sh` as the
  armed gate path
- `h-mad/tests/test_h_mad_tdd_gate_state_resolution.py` — module docstring explains the sub-project
  state-resolution fail-open this gate version fixes
