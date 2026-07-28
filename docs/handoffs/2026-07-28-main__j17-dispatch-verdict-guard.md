# Handoff — J17 dispatch verdict guard + exec-default one-shot transport

**Date:** 2026-07-28
**Branch:** main
**Project:** orca/skills (h-mad skill)

## Session Summary

Two shipped changes to the h-mad dispatch layer, both merged to main:
1. **J17 (PR #16, `076d13a`)** — a live 5d/5e Codex dispatch produced a **false `STATUS: DONE`** on a silent pane (submit-Enter swallowed mid-boot). Two stacked root causes (prompt-echo verdict + `wait` false-idle); fixed both.
2. **exec-default (PR #17, `4bf506b`)** — flipped the documented default for a **one-shot** 5d/5e dispatch to headless `hmad-dispatch exec` (hard exit code, sidesteps the whole pane failure class), and added `exec --log <file>` for live tailing so headless is not blind. Pane path reserved for the iterative revision loop.

Verified: h-mad suite 733/0, HemaSuite symlink-coupled 39/0, all guards mutation-verified.

## Key Learnings

- **Prompt-echo defeats a bare-token extractor.** Any pane dispatch whose prompt states its output contract (`STATUS: DONE` on its own line) plants that exact token in the echoed buffer. On silence, the extractor's last-match reads the prompt's own contract line as the agent's verdict. Fails closed on an *empty* buffer, not an *echoed* one. The `key-must-start-the-line` guard misses it because the echoed contract line does start the line.
- **The audit path was NOT immune by nature.** `assemble_audit.py` substitutes the concrete sentinel into the prompt exemplar, so a silent reviewer's echo forms a complete `<sentinel>-BEGIN…-END` pair. The per-cycle sentinel only defeats a *stale prior cycle*, not *same-run echo*. Audit escaped in practice only via Orca report-file transport (no scrape).
- **`wait` idle ≠ completion.** A pane parked on `Waiting for background terminal` (Codex delegated to a background terminal) is a static frame: native tui-idle satisfied, two snapshots match, generation still live. `_wait_stable` stability is not authoritative for the background-terminal state.
- **Fix = boundary slice + evidence gate.** `send` appends a fixed `===HMAD-DISPATCH-BOUNDARY===` as the last prompt line; extractors slice past its last occurrence (also fences stale scrollback). `wait` gains `--until-regex`/`--not-while-regex`. `--after-marker` fails **closed** if the boundary is absent (safe direction).
- **Test artifact:** rapid mutate/restore of a `.py` under anaconda pytest left a stale `.pyc` with a colliding mtime — `getsource` showed correct source while runtime used mutated bytecode. `find … -delete` between mutations, and run pytest with `-B`.
- **exec vs pane is not one-or-the-other — it's one-shot vs iterative.** Headless `exec` wins per-single-dispatch (exit code = hard completion, no scrape → no J17 class); warm pane wins the iterative revision loop (cycles 2..N reuse context, cheaper + observable). SKILL.md now makes exec the one-shot default.
- **`--out` is not tailable; the transcript is.** `--output-last-message`/captured response only lands at completion. `exec --log <file>` streams the live transcript (codex) / response (agy) to a tailable file. Direct redirect not a pipe → agent exit code survives; codex folds transcript+stderr, agy stays stdout-only so the verdict read-back stays clean. codex streams truly live; agy `--print` buffers so there's less mid-run chatter.

## Next Steps

1. On the **next real one-shot 5d/5e dispatch**, use `hmad-dispatch exec codex <pf> --out … --log … --timeout 900 &` + `tail -f <log>` (SKILL.md §"Exit-code dispatch for 5d/5e"). For the pane path (iterative loop), still pass `--after-marker` + evidence-gated `wait` (§"Reading a dispatch verdict").
2. **Resume the parked Task 3** work (separate H-MAD feature, its own worktree): Codex anti-gaming audit of the 22 module tests, capture the full-suite number, then 5e review cycle 2 on the corrected code. Nothing committed there yet.
3. Watch live on first real use: (a) confirm Codex/agy echo the boundary line into the scrape on the pane path (else `--after-marker` halts — safe but flag if spurious); (b) confirm `exec --log` actually streams live from the real codex CLI (verified against stubs only, not the live CLI).

## Open / Blocked Items

- Task 3 (the feature the false-DONE surfaced under) — status: in progress, parked in its own worktree; owed Codex audit + full suite + 5e cycle 2. Not part of this skill fix.

## Context for Next Session

**Files touched this session (all merged; J17 → `076d13a`, exec-default → `4bf506b`):**
- `h-mad/scripts/h_mad_extract_verdict.py` — `slice_after_boundary` + `after=`/`--after-marker` (J17)
- `h-mad/scripts/h_mad_extract_report.py` — same slice (J17)
- `h-mad/scripts/hmad-dispatch.sh` — `send` appends boundary; `wait` gains `_frame_satisfies` + `--until-regex`/`--not-while-regex` (J17); `exec` gains `--log` live-stream (exec-default)
- `h-mad/SKILL.md` — §"Reading a dispatch verdict" (J17) + §"Exit-code dispatch for 5d/5e" flipped to exec-default + 5d/5e phase bullets (exec-default)
- `h-mad/tests/test_h_mad_extract_verdict.py`, `test_h_mad_extract_report.py`, `test_hmad_dispatch.py` (J17); `test_hmad_dispatch_exec.py` (exec-default, 4 `--log` tests)

**Uncommitted changes:** none (PRs #16 + #17 merged, local main = origin/main `4bf506b`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
# one-shot 5d/5e: see h-mad/SKILL.md §"Exit-code dispatch for 5d/5e" (exec + --log)
# pane path:      see h-mad/SKILL.md §"Reading a dispatch verdict" (--after-marker + wait gates)
```

**Related docs:**
- `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e" (exec-default + `--log`) and §"Reading a dispatch verdict" (J17)
- PRs: https://github.com/BrightGold70/skills/pull/16 (J17), https://github.com/BrightGold70/skills/pull/17 (exec-default)
- Scratchpad plan (session-local): `hmad-verdict-echo-fix-plan.md`
