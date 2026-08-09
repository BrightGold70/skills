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

## Next Steps

1. Confirm the duplicate skill entry cleared — the `h-mad.bak-20260808` skill should be gone from the
   listing next session; only `h-mad` should appear.
2. Delete the backup once confident: `rm -rf ~/.claude/h-mad.bak-20260808` (stale May-23 copy, superseded).
3. Future "update h-mad from github" is now just `git -C /Users/kimhawk/orca/skills pull` — the symlink
   makes the checkout the live skill. No resync step.

## Open / Blocked Items

- `~/.claude/h-mad.bak-20260808` — status: deferred (intentional retention). Stale pre-repair copy kept
  as a rollback path; delete when the symlink install has a few sessions of confidence behind it.
- `settings.json:129` still arms the gate via `~/.claude/skills/h-mad/hooks/h-mad-tdd-gate.sh` rather
  than the documented `~/.claude/hooks/…` path — status: deliberately not changed. Both paths now
  resolve to the same physical file through the symlinks, it is the sole arming registration (no
  double-fire), and rewriting it would be churn with zero behavior change.

## Context for Next Session

**Files touched this session:**
- None in the repo. All changes were to the user-global install:
  - `~/.claude/skills/h-mad` — stale directory replaced with symlink → `/Users/kimhawk/orca/skills/h-mad`
  - `~/.claude/hooks/h-mad-tdd-gate.sh` — new symlink → `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh`
  - `~/.claude/h-mad.bak-20260808` — backup of the pre-repair copy (moved out of `skills/`)

**Uncommitted changes:** none (repo tree clean throughout; `git status --short` empty)

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main

# confirm the install is intact
ls -la ~/.claude/skills/h-mad ~/.claude/hooks/h-mad-tdd-gate.sh   # both must be symlinks into this repo

# confirm the skill still works through the install path (not the repo path)
python3 -m pytest ~/.claude/skills/h-mad/tests/ -q --tb=line     # expect 1173 passed, 2 skipped
```

**Verification evidence from this session:**
- `git rev-list --left-right --count origin/main...HEAD` → `0	0` (repo at github HEAD)
- `diff -rq ~/.claude/skills/h-mad/ /Users/kimhawk/orca/skills/h-mad/` → identical
- `pytest ~/.claude/skills/h-mad/tests/` → `1173 passed, 2 skipped in 107.10s`
- The 2 skips are `tests/test_h_mad_state_validate_fallback.py:116,151`, both gated on "no live state
  file" — correct here, since no `docs/.bkit-memory.json` exists in this project.

**Related docs:**
- `h-mad/SKILL.md:774` — "Editing this skill while a run is in flight" (why the install is a symlink,
  and the worktree discipline that follows from it)
- `h-mad/bin/hmad-dispatch:9` — PATH shim; documents the symlink-chain install assumption
- `h-mad/references/codex-implementer-prompt.md:19` — names `~/.claude/hooks/h-mad-tdd-gate.sh` as the
  armed gate path
- `h-mad/tests/test_h_mad_tdd_gate_state_resolution.py` — module docstring explains the sub-project
  state-resolution fail-open this gate version fixes
