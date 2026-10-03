# Handoff — h-mad codex TDD gate rejects the project interpreter and scratchpad report paths

**Date:** 2026-10-03
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · feature/203-guideline-web-evidence-admission · session 4cb9f363-9ba0-40fa-90db-59cce2d5a6df
**Supersedes:** none — first on this branch for this topic

## Session Summary

HemaSuite's `guideline-web-evidence-admission` ran Phase 5 with codex as the implementer. The codex-side
TDD gate (`h-mad/hooks/h-mad-codex-tdd-gate.py`) blocked codex from running the project's pytest
interpreter. As a result every RED/GREEN count in that feature was measured by the orchestrator, not by
codex. The gate also rejected codex report paths under the session scratchpad, so reports landed inside
the repo's `tests/`. This brief hands the defect to the skills lane. Nothing is claimed: skills has no
`docs/.bkit-memory.json`. The HemaSuite feature itself is complete, merged into main as `77cb717d`.

## Key Learnings

- The gate is invoked as `python3 $HOME/.agents/skills/h-mad/hooks/h-mad-codex-tdd-gate.py` (HemaSuite
  `.codex/hooks.json`), so `sys.executable` is the system/anaconda `python3`, never the project venv.
- `TRUSTED_BIN_DIRS` (`h-mad/hooks/h-mad-codex-tdd-gate.py:59-65`) is `/bin`, `/usr/bin`, `/usr/local/bin`,
  `/opt/homebrew/bin` and `Path(sys.executable).resolve().parent`. A project interpreter such as
  `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/.venv/bin/python` is therefore always refused.
  This happens even though h-mad's own `h_mad_assemble_tdd.py` bakes that interpreter into the dispatch
  and the codex prompt mandates it.
- `~/.agents/skills/h-mad` (the codex install path) is a **plain directory copy**, not a symlink into this
  checkout. Measured 2026-10-03: the gate file there is byte-identical to the checkout, but it will drift.
  This is the `SKILL_NOT_SYMLINK` hazard on the codex side, and `h_mad_install_check.py` checks only
  `~/.claude/skills`.
- On a gate refusal, codex returns a well-formed `STATUS: BLOCKED`, so the defect looks like a task-level
  blocker rather than a tooling fault.

## Next Steps

1. **Reproduce.** From a HemaSuite worktree, dispatch `hmad-dispatch exec codex` with a prompt that runs
   `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/.venv/bin/python -m pytest -q <one test file>`.
   Expect the PreToolUse gate to refuse it. HemaSuite evidence: its scratchpad
   `fix_audit_authors.out.txt` reported "The H-MAD PreToolUse hook rejected the pytest command because its
   trusted executable directories exclude …/.venv/bin/python".
2. **Fix the allowlist.** Trust the project's interpreter, by one of: the interpreter
   `h_mad_assemble_tdd.py` probed and baked into the prompt; any `<repo>/**/.venv/bin` under the hook's
   project root; or an explicit `HMAD_TRUSTED_PYTHON`. Close the class rather than one path. State the
   residual: what remains untrusted, and why.
3. **Fix the report-path rule.** Line ~245 (`_path_within(value, Path("/tmp"))`) permits `/tmp` but not the
   session scratchpad (`/private/tmp/claude-501/...`, or whatever `$TMPDIR`/scratchpad resolves to). Codex
   then wrote reports into the repo's `tests/` instead. Check whether `/tmp` vs `/private/tmp` symlink
   resolution is the actual cause before widening anything.
4. **Make the codex install a symlink,** and extend `h_mad_install_check.py` to check
   `~/.agents/skills/h-mad` the same way it checks `~/.claude/skills/h-mad`.
5. **Second gate trip.** The gate also refused a production edit to `tools/references/package.py` with "no
   derived test file exists" (it maps to `tests/test_package.py`). The workaround was a temporary
   re-export file, deleted before commit. Decide whether an existing, already-RED test elsewhere should
   satisfy the gate (e.g. the dispatch's `--test-path`).

## Open / Blocked Items

- Codex-gate interpreter allowlist — status: not started. repo: `/Users/kimhawk/orca/skills` · branch: main ·
  worktree: none (main checkout) · file: `h-mad/hooks/h-mad-codex-tdd-gate.py` (`TRUSTED_BIN_DIRS` :59;
  path rule :245) · codex hook wiring seen at
  `/Users/kimhawk/orca/workspaces/HemaSuite/MacBookPro/.codex/hooks.json`.
- Codex install is a copy — status: not started. path: `~/.agents/skills/h-mad`.
- Related, not handed over: the **codex audit round owed for HemaSuite's Phases 3/4/5b** of
  `guideline-web-evidence-admission` stays in HemaSuite. It audits that repo's feature documents, now
  archived at `docs/archive/2026-10/guideline-web-evidence-admission/`.

## Context for Next Session

**Files touched this session (in skills):** none — this brief only.

**Uncommitted changes:** this brief.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
python3 h-mad/hooks/h-mad-codex-tdd-gate.py --help 2>/dev/null; sed -n 55,70p h-mad/hooks/h-mad-codex-tdd-gate.py
```

**Related docs:**
- HemaSuite report: `docs/archive/2026-10/guideline-web-evidence-admission/guideline-web-evidence-admission.report.md` (What To Improve, Carry Items)
