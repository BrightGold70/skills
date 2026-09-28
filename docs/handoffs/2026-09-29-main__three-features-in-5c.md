# Handoff — three H-MAD features in Phase 5c: mhr Tasks 0–18 done, tdd-gate Tasks 0–9 done, grok Task 13 done

**Date:** 2026-09-29
**Branch:** main
**Project:** skills
**Supersedes:** 2026-09-28-main__three-features-past-design.md

## Session Summary

A `/loop` session ran all three features in parallel, following the merge order tdd-gate → grok → mhr.

| Feature | State at close | Next |
|---|---|---|
| `multi-host-runtime` (mhr) | 5b exited (design v1.3, impl-plan v1.2, delta review 0 must). Tasks 0–18 are committed on `feature/multi-host-runtime`, HEAD `4f8c9328`, and the Task 18 coupled-suite gate passed all 7 steps. | 5f (wire registry), then 5g, then Phase 6 |
| `codex-tdd-gate-defects` (tdd-gate) | 5b exited (design v1.3, impl-plan v1.2, delta review 0 must). P0 and V-0 are committed. Tasks 0–9 are committed on `feature/codex-tdd-gate-defects`, HEAD `d11848e9`. **Task 10 (mutation specs) was still running at close.** | Verify Task 10, then Task 11 (phase-5 merge gate), then 5f/5g |
| `grok-codex-fallback` (grok) | Task 13 is committed (`d48ecee7`). Tasks 12 and 14–17 are **deferred until tdd-gate merges** (operator reading of "sequenced merge"). | Rebase onto tdd-gate after it merges, then re-plan Task 12/14 onto tdd-gate design §D13 |

main is 18 commits ahead of origin and nothing was pushed. The operator pre-step is done: the four `~/.agents/skills/{h-mad,handoff}` and `~/.gemini/config/skills/{h-mad,handoff}` symlinks now point into `/Users/kimhawk/orca/skills`.

## Key Learnings

- **Codex's sandbox cannot write inside `.git`, and cannot run `git worktree add`.** Every task that writes a git-dir file (node-id lists, base-suite captures) or runs `byte_identity.py` came back BLOCKED. The fix that worked: the orchestrator runs that one step outside the sandbox and codex reads the result. Say so in the dispatch prompt up front.
- **About 1 in 3 GREEN BLOCKs was a defect in the RED test, not in production code.** Examples: `_baseline` never created `handoff/`; a `home-braced` vs `home_braced` key mismatch in three places; rc 0 asserted where the design says rc 2; `test_w.py` vs the planned `test_x.py`. Codex's "do not edit tests → BLOCKED with diagnosis" rule worked every time. Fix it as a separate test-only amendment commit, then re-dispatch GREEN. Sweep **every** lookup of the defect: my second amendment missed a third occurrence.
- **The scoped gate misses anchor drift; only the full suite catches it.** tdd-gate Task 1 GREEN duplicated a `return` line that a committed mutation row anchors on. The scoped tests were green; the full suite failed three mutation-harness tests. Every GREEN prompt now asks for `--check-anchors`.
- **`comm` between two sorted files is only valid under one collation.** The mhr node-id floor reported 1631 "missing" tests. Re-sorted under `LC_ALL=C` it was 0: codex and I had sorted under different locales.
- **zsh does not word-split an unquoted `$VAR`.** A verification that ran `pytest $TS` printed `no tests ran` for all three runs, and I nearly read that as a result. Write paths out, or use arrays.
- **V-0 reading, conclusive (claude 2.1.283):** `READING=E1_DOES_NOT_BLOCK FORM_A=BLOCKS FORM_B=BLOCKS CHOSEN=b`. An `exit 1` hook does not block a Write; form b (rc 0 + JSON deny) does.
- **Subagent final replies arrive truncated** (for example "Nothing new." or "(no action — awaiting real input)"). Always read the file they wrote, never the reply. Prompts now demand a reply under 1–2 KB, with the detail in a file.

## Next Steps

1. **tdd-gate Task 10: verify the codex output.**
   - Output: `/private/tmp/claude-501/-Users-kimhawk-orca-skills/8ac6172b-1a5c-434c-a8d0-15650c59b49d/scratchpad/tdd_t10.out.txt`, in worktree `/Users/kimhawk/orca/skills-codex-tdd-gate-defects`.
   - Need 8 specs, 98 rows, each `ANCHORS_OK` and `ALL_CAUGHT crash_kills=0`.
   - The W-rows must cover Task 8's three shell-hook wires. They were **not** reverted by hand; only a whole-hook revert was done.
   - Re-run `--check-anchors` yourself before committing.
2. **tdd-gate: re-run the one post-Task-9 suite failure alone.** `h-mad/tests/test_h_mad_wire_registry.py::test_wire_registry_guard_mutation_is_caught_by_harness` failed while Task 10 was writing specs in the same tree, so it is probably a concurrency artifact, but that is unverified.
3. **tdd-gate Task 11 (phase-5 merge gate)**, from `docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md` `## Task 11`. Then 5f (`h_mad_baseline_sha.py --branch feature/codex-tdd-gate-defects` gives the 5c sha `d6863515`, then `h_mad_wire_registry.py verify/challenge`), then 5g, then Phase 6 and 7.
4. **mhr 5f → 5g → Phase 6.**
   - `h_mad_wire_registry.py verify --base c0f8af67` reports `WIREREG: FAIL missing=7`. All 7 are **codex-tdd-gate-defects** wires, whose pin tests exist only on the unmerged tdd-gate branch; mhr's own wires verify. Record this as expected until tdd-gate merges, or ask the operator whether registry verify should be feature-scoped.
   - mhr merges **last**.
5. **grok (after tdd-gate merges):** rebase `feature/216-grok-codex-fallback` onto the new main, then dispatch `implplan-author` for grok impl-plan v1.4 (Task 12/14 onto tdd-gate §D13, plus the stale Task 7/9 plan text), then Tasks 12, 14–17.
6. **Push main** once the operator agrees (18 commits ahead; this handoff's commit is not pushed either).

## Open / Blocked Items

- **tdd-gate Task 10: in flight at close.** See In-Flight Processes.
  - Location: `repo: /Users/kimhawk/orca/skills · branch: feature/codex-tdd-gate-defects · worktree: /Users/kimhawk/orca/skills-codex-tdd-gate-defects`.
  - Prompt: `<scratchpad>/tdd_t10.prompt.txt`.
- **tdd-gate: Task 8 per-wire reverts were not done by hand.** Only the whole-hook revert ran (79 failed / 14 passed, the exact RED). Task 10's W-rows must prove each of the three wires.
- **main `.h-mad/wires.jsonl` is modified and uncommitted (+11/−7), and this session did not write it.** It re-registers the codex-tdd-gate-defects wire records. It was probably the impl-plan v1.1/v1.2 author or the delta reviewer re-running `h_mad_wire_pin_gate.py --feature` on main. Inspect with `git diff .h-mad/wires.jsonl`, then commit it or discard it deliberately.
- **mhr Task 17 deviation.** `rehearsal/cases.json` now expects `replay-agy` to be `FAIL V-11.1 no adapter read`, where the plan said "a script ran before the adapter was read". The log has no `view_file` events, so design §D10's R2/R3 rule gives `no adapter read`. The plan text is now stale; fold this into the Phase 6 analysis.
- **mhr Task 18 suite 1 had one collection error** that did not recur in suite 2 on the same tree. It ran concurrently with another full suite and a codex dispatch.
- **grok Tasks 12 and 14–17 are deferred until tdd-gate merges.**
  - Location: `repo: /Users/kimhawk/orca/skills · branch: feature/216-grok-codex-fallback · worktree: /Users/kimhawk/orca/skills-grok-codex-fallback`.
  - HEAD is `d48ecee7`.
- **codex-tdd-gate-defects open questions** (from the impl-plan):
  - OQ-I2: the design's `[ -x "$D" ]` mutant is equivalent.
  - OQ-I4: the lexical subset of the six `-c` cells.
  - OQ-D1: the Codex host hook timeout (the Claude half is a 5g merge condition).
- **Filed this session** (`f6b258f0`): two skill-candidate rows.
  - The audit gate counts nested sub-bullets (re-measured: `must=27` against 3 real). Workaround: auditors tag top-level bullets only.
  - The audit preflight false-HALTs when the gated doc quotes a slot token such as `<INLINE_*>`.
- **Pre-existing suite failure `test_top_level_key_set_still_matches`** (live-binary drift): unchanged since 2026-09-28.
- **grok quality measurement (D4 follow-up):** deferred, unchanged since 2026-09-28.
- **Carried from 2026-09-15:**
  - (a) Skill-candidates census: re-run this session, OPEN=53 (51 + 2 filed). Done.
  - (b) The `exec-pane` wrapper leak is open row `:2186`; still unimplemented.
  - (c) HemaSuite pointer: `2026-09-14-main__wsg-backlog-two-items-owed-here.md` Next Step 1 is answered by `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md`. Unchanged; ownership stays here.
- **HemaSuite #28 still runs with the codex TDD hook disarmed** until codex-tdd-gate-defects ships and is live-verified.
  - Location: `repo: /Users/kimhawk/orca/HemaSuite · branch: feature/28-review-manifest-guideline-evidence`.
  - Unchanged.
- **Closed this session:**
  - Operator symlink pre-step: done, 4 links.
  - Audit-gate over-count: filed.
  - Task 12 decision: deferred by merge order.
  - mhr Deviation 7/8/M4/S7: resolved by mhr design v1.3 (`212aab9d`).
  - tdd-gate OQ-I3 (DD-7 root-under-`tests/` bypass): resolved by tdd-gate design v1.3 (`85b81698`), spec/plan propagation `8322fa04`.
  - tdd-gate OQ-I1 (P0/V-0): P0 committed `aa5c43c7`, V-0 committed `10553592`.

## In-Flight Processes

| PID | Command | Log | Started | Elapsed @ handoff | ETA | What to check on exit |
|---|---|---|---|---|---|---|
| (find with `pgrep -f tdd_t10.prompt`) | `hmad-dispatch exec codex <scratchpad>/tdd_t10.prompt.txt --cd /Users/kimhawk/orca/skills-codex-tdd-gate-defects --timeout 7200` | `<scratchpad>/tdd_t10.log`; final message `<scratchpad>/tdd_t10.out.txt` | ~01:20 KST 2026-09-29 | ~40 min | ≤ 2 h total | `grep '^STATUS:' tdd_t10.out.txt`; per spec `MUTATION: ALL_CAUGHT … crash_kills=0`; worktree `git status` shows 8 new specs |

`<scratchpad>` = `/private/tmp/claude-501/-Users-kimhawk-orca-skills/8ac6172b-1a5c-434c-a8d0-15650c59b49d/scratchpad`

## Context for Next Session

**Claims:** this session (`8ac6172b-1a5c-434c-a8d0-15650c59b49d`) holds all three features in `docs/.bkit-memory.json`, all at `phase=step5`. Released at closeout (see the commit); re-`--claim` before working.

**Worktrees:**
- `/Users/kimhawk/orca/skills-multi-host-runtime`
  - Branch `feature/multi-host-runtime`; 5c sha `c0f8af67`; HEAD `4f8c9328`.
  - `$GD/hmad-mhr-base-{suite,nodeids}.txt` placed.
- `/Users/kimhawk/orca/skills-codex-tdd-gate-defects`
  - Branch `feature/codex-tdd-gate-defects`; 5c sha `d6863515`, rebased on P0 `aa5c43c7`; HEAD `d11848e9`.
  - `$GD/hmad-ctg-base-nodeids.txt` placed.
- `/Users/kimhawk/orca/skills-grok-codex-fallback`
  - Branch `feature/216-grok-codex-fallback`; HEAD `d48ecee7`.
- Parent repo: `/Users/kimhawk/orca/skills`, branch `main`.

**Uncommitted changes (main):**
- Pre-existing: `.gitignore`, `.ignore`, `.mcp.json`, `AGENTS.md`, `docs/03-analysis/jev-system-one-adaptation.md`, `opencode.json`.
- Not this session's: `.h-mad/wires.jsonl` (see Open Items).

**Foreign stash:** `stash@{0}` ("resolved-model") is untouched.

**Per-task recipe that worked**, for each task:
1. `h_mad_assemble_tdd.py --feature F --task "Task N" --phase red|green --project-root <wt> --module … --test-path … --python /opt/anaconda3/bin/python --expect-fail X --expect-pass Y --prompt/--out/--log <scratchpad>`, then append an ORCHESTRATOR NOTE (hermetic env, stdin=, no `.git` writes, `--check-anchors`, STATUS last line).
2. Dispatch with `hmad-dispatch exec codex … --cd <wt>` via `run_in_background`.
3. Verify:
   - both locales with `CLAUDE_ZZZ_PROBE=1`;
   - revert check: named stash for a tracked file, or `mv` for a new file;
   - per-wire revert: replace the call with a constant;
   - full suite after each 2–3 tasks, never concurrent with another suite.
4. Before every commit: `git checkout -- .gitignore && rm -f .ignore`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills-codex-tdd-gate-defects && git status --short
grep '^STATUS:' /private/tmp/claude-501/-Users-kimhawk-orca-skills/8ac6172b-1a5c-434c-a8d0-15650c59b49d/scratchpad/tdd_t10.out.txt
/opt/anaconda3/bin/python h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json
```

**Related docs:**
- tdd-gate:
  - `docs/02-design/features/codex-tdd-gate-defects.design.md` (v1.3)
  - `docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md` (v1.2)
  - `docs/03-analysis/codex-tdd-gate-defects.analysis.md` (worktree)
- mhr:
  - `docs/02-design/features/multi-host-runtime.design.md` (v1.3)
  - `docs/01-plan/features/multi-host-runtime.impl-plan.md` (v1.2)
  - `docs/03-analysis/multi-host-runtime.analysis.md` (worktree; Tasks 0–18 readings)
- mhr T16/T17 diagnosis: `<scratchpad>/mhr_t16_t17_diag.md`
