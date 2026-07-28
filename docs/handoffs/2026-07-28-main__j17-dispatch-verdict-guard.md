# Handoff — J17 dispatch verdict prompt-echo + false-idle fix

**Date:** 2026-07-28
**Branch:** main
**Project:** orca/skills (h-mad skill)

## Session Summary

During a live H-MAD run a 5d/5e Codex dispatch produced a **false `STATUS: DONE`** on a silent pane (submit-Enter swallowed mid-boot). Investigated, found two stacked root causes, fixed both, shipped via PR #16 (squash-merged to main `076d13a`). Done and verified: h-mad suite 729/0, HemaSuite symlink-coupled tests 39/0, all three guards mutation-verified.

## Key Learnings

- **Prompt-echo defeats a bare-token extractor.** Any pane dispatch whose prompt states its output contract (`STATUS: DONE` on its own line) plants that exact token in the echoed buffer. On silence, the extractor's last-match reads the prompt's own contract line as the agent's verdict. Fails closed on an *empty* buffer, not an *echoed* one. The `key-must-start-the-line` guard misses it because the echoed contract line does start the line.
- **The audit path was NOT immune by nature.** `assemble_audit.py` substitutes the concrete sentinel into the prompt exemplar, so a silent reviewer's echo forms a complete `<sentinel>-BEGIN…-END` pair. The per-cycle sentinel only defeats a *stale prior cycle*, not *same-run echo*. Audit escaped in practice only via Orca report-file transport (no scrape).
- **`wait` idle ≠ completion.** A pane parked on `Waiting for background terminal` (Codex delegated to a background terminal) is a static frame: native tui-idle satisfied, two snapshots match, generation still live. `_wait_stable` stability is not authoritative for the background-terminal state.
- **Fix = boundary slice + evidence gate.** `send` appends a fixed `===HMAD-DISPATCH-BOUNDARY===` as the last prompt line; extractors slice past its last occurrence (also fences stale scrollback). `wait` gains `--until-regex`/`--not-while-regex`. `--after-marker` fails **closed** if the boundary is absent (safe direction).
- **Test artifact:** rapid mutate/restore of a `.py` under anaconda pytest left a stale `.pyc` with a colliding mtime — `getsource` showed correct source while runtime used mutated bytecode. `find … -delete` between mutations, and run pytest with `-B`.

## Next Steps

1. On the **next real 5d/5e dispatch**, add `--after-marker` to the extractor call and gate `wait` with the evidence regexes — both documented in `h-mad/SKILL.md` §"Reading a dispatch verdict".
2. **Resume the parked Task 3** work (separate H-MAD feature, its own worktree): Codex anti-gaming audit of the 22 module tests, capture the full-suite number, then 5e review cycle 2 on the corrected code. Nothing committed there yet.
3. Watch live: confirm Codex/agy actually echo the appended boundary line into the scrape. If a TUI drops it, `--after-marker` will halt (not false-pass) — safe, but flag it if spurious.

## Open / Blocked Items

- Task 3 (the feature the false-DONE surfaced under) — status: in progress, parked in its own worktree; owed Codex audit + full suite + 5e cycle 2. Not part of this skill fix.

## Context for Next Session

**Files touched this session (all merged to main `076d13a`):**
- `h-mad/scripts/h_mad_extract_verdict.py` — `slice_after_boundary` + `after=`/`--after-marker`
- `h-mad/scripts/h_mad_extract_report.py` — same slice
- `h-mad/scripts/hmad-dispatch.sh` — `send` appends boundary; `wait` gains `_frame_satisfies` + `--until-regex`/`--not-while-regex`
- `h-mad/SKILL.md` — §"Reading a dispatch verdict" documents the contract
- `h-mad/tests/test_h_mad_extract_verdict.py`, `test_h_mad_extract_report.py`, `test_hmad_dispatch.py`

**Uncommitted changes:** none (PR #16 merged, local main = origin/main).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
# next dispatch: see h-mad/SKILL.md §"Reading a dispatch verdict"
```

**Related docs:**
- `h-mad/SKILL.md` §"Reading a dispatch verdict"
- PR: https://github.com/BrightGold70/skills/pull/16
- Scratchpad plan (session-local): `hmad-verdict-echo-fix-plan.md`
