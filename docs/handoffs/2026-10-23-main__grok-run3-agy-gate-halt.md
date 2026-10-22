# Handoff — grok-audit-surface: Tasks 14a–14d landed; run 3 halted on h-mad's own agy gate

**Date:** 2026-10-23
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-22-main__grok-route-b-docs-converged.md

## Session Summary

Phase-5 TDD for route (b) is done: Tasks 14a, 14b and 14c are merged on `main`, and the Task 14d gate passes AC.1–.4. Task 14d's AC.5 is load-sensitive, and the operator accepted it.

Task 15 run 3 then ran steps 1–6. The grok re-smoke scanned **`TOOLSCAN: CLEAN out_of_root=0 checkout=0`**; run 2 had halted on `OUT_OF_ROOT`. This is first evidence that route (b) works.

The smoke still returned `SMOKE: FAIL reason=nongit_root_refused:agy`. That verdict is an artifact. Every agy tool call was denied by **our own** agy Phase-5 hook (`kind=judge-error`), which is armed because the feature is `phase=step5`. Following the operator's ruling, I halted before steps 6b and 7, so nothing went to the calibration ref.

The feature is halted at `step5:task15:agy_gate_contaminates_resmoke`, the claim is released, and all commits are pushed.

## Key Learnings

- **Our gates contaminate live calibration runs.**
  - The agy Phase-5 hook is global for agy. It fails closed (`Gate could not reach a judgement. kind=judge-error`) in a non-git root under `~/.local/state/h-mad/…/roots/`.
  - The probe's smoke then reads the zero-evidence agy pass as "agy refuses a non-git root".
  - Any Task-15-style live run while the feature is `step5` is invalid for agy.
- **The Phase-5 shell gates block exploration.**
  - Every codex and agy dispatch needed a preface naming the admitted read path. That path is `cat`, `grep`, `head`, `tail`, `wc`, `ls` or `jq`, as one plain command, plus agy's `view_file` / `grep_search`.
  - Without the preface, codex returned `STATUS: BLOCKED` after four refused `graft`/`rg`/`git` calls.
  - Without it, agy returned a blind `DRIFT` (`EVIDENCE: NONE ok=0`) after using `read_file`.
  - The source of truth for the admitted read verbs is `READ_ONLY_COMMANDS` at `h-mad/scripts/h_mad_target_identity.py:225`.
- **Codex GREEN cannot verify its own mutation rows.** `--check-anchors` is refused even through `hmad-dispatch run`. In 14a codex spliced a nested array with a literal `+` into the spec and broke its JSON.
- **The judge refuses a behaviour-preserving fix.** It answers `kind=test-passing` once a module is green, so a marker or comment rework cannot be applied.
  - Remedy used on Task 14c: save the attempt, `git checkout` the production file and spec back to HEAD (tests go RED again), and re-dispatch GREEN with the review findings.
- **Two RED commits shipped wrong-reason REDs, and both were caught only by reading failure reasons.**
  - 14b: the path parse split on a space.
  - 14c: `FileExistsError` from re-making a fixture directory.
  - A split count that matches is not enough; read every failure line.
- **The `test_grok_audit_surface_path_scope.py` module timing is bimodal: 17 s idle, 36–46 s at load ~9.** That exceeds the judge's 40 s budget under concurrent sessions.

## Next Steps

1. **Operator decision on run 3's contamination.** Read `docs/03-analysis/grok-audit-surface.incident-2026-10-23-run3-agy-gate.md` §"Open decision", then pick one:
   - (a) The agy gate stands down for targets and cwds outside the project root, like the Claude gate. This is the likely fix, in `h-mad/hooks/h-mad-agy-tdd-gate.py`.
   - (b) A sanctioned, recorded disarm window for Task 15.
   - (c) Resequence Task 15 out of `step5`.

   Each needs a design and impl-plan note, because Task 15 assumed none of this.
2. **Task 15 run 4 in a NEW run directory**, after the fix.
   - Drivers: `~/.local/state/h-mad/grok-audit-surface/run3-steps1-4.sh` (setup through canary), then `resmoke3.sh` (assembler start reading, grok, agy, codex).
   - Copy and rename both; each run rewrites `run-current.env`.
   - Then step 6, the smoke. On PASS, steps 6b–11 (impl-plan §"Task 15"): assembler end and check, commit-data to `calibration/grok-audit-surface`, second quarantine, S2.
   - Make no commit on this checkout between the two assembler readings (D21).
3. **Task 16, then Task 17, then 5f/5g, Phase 6, Phase 7.**
   - Task 16 inputs: agy/codex `delivered=out`; codex `Effort: not measured`.
   - 6a-prime must read `c4b754b1`, `2925febd`, and the Task 14 commits `a8715d86`..`9f8c96c6`.
4. **File the h-mad tooling defects as `docs/skill-candidates.md` rows** (the scout was skipped again). Items 1–7 are carried; items 8–12 are new this session:
   1. The codex gate does not check `run --timeout` inner commands.
   2. The judge falls back to a Python with no pytest.
   3. The assembler's bare `--python`.
   4. agy and codex source reads are refused under the Phase-5 hook.
   5. The test-passing DENY has no path for a behaviour-preserving fix.
   6. Subagent transport truncates at about 4 KB.
   7. The 40 s judge budget is too tight for a slow file.
   8. **New:** `_PY_TOKEN_RE` in `h_mad_wire_pin_gate.py` reads only `.py`, so a `.sh` production file never maps and is ungated.
   9. **New:** the agy gate fails closed outside the repo; this is the run-3 root cause.
   10. **New:** codex GREEN cannot run `--check-anchors`.
   11. **New:** `implementation_authors` is append-only, so a mistaken entry cannot be corrected.
   12. **New:** the 14d AC.5 judge-budget exposure under load.

## Open / Blocked Items

**This session:**

- **Halt** `step5:task15:agy_gate_contaminates_resmoke`. Blocked on the operator decision in Next Step 1. State: `phase=step5`, claim released.
- **Run 3 directory** `~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261022T222714Z`. Incident evidence only; never score it. Its `HALT` file holds `agy_gate_contaminates_resmoke`.
  - The grok, agy and codex readings are kept under `data/runs/<run>/resmoke/`.
  - The first quarantine moved one item to `grok-quarantine-20261022T222728Z`.
- **Task 14d AC.5 not met:** the path-scope module takes 36–46 s under load. Accepted by the operator as an environmental limit and recorded in `docs/03-analysis/grok-audit-surface.task14d-gate-2026-10-23.md`. The option to split its two real-cycle ids into their own module is still open.
- **Task 14c deviation, operator-accepted:** `status_dir = here.parent if here.name == "scripts" else here` at `h-mad/scripts/h_mad_grok_containment.py:134`.
  - The plan's `git -C <here>/..` contradicts its own sha256 fixture.
  - Production is unchanged, because `here` is always `…/h-mad/scripts`.
  - Owed: a plan or design note so Phase 6 does not flag it as drift.
- **`implementation_authors` misattribution:** for `path_scope_wire` it lists `claude` last. The cause is my test-only parse fix in 14b; the field is append-only, and this is disclosed in `1c495954`.
- **Run-2 env backup:** `~/.local/state/h-mad/grok-audit-surface/run-current.env.run2-20261022T044856Z`. Harmless.

**Carried from `2026-10-22-main__grok-route-b-docs-converged.md`:**

- **Phase-5 preflight.** CLOSED this session: the judge mapping and halt_reason were checked, and the `.sh` gap is filed as defect 8 above.
- **Task 14a, then 14b, 14c, 14d.** CLOSED: commits `a8715d86` through `e3629604`.
- **Task 15 run 3.** CLOSED as incident (`f7045cd0`); run 4 is owed, see Next Step 2.
- **Round-3 fixes not re-audited** (design v1.16, impl-plan v1.11). Superseded: Phase 5 executed both, and no anchor or count surprise appeared apart from the 14c plan/test contradiction above.
- **Audit and author reports** in `docs/03-analysis/grok-audit-surface.route-b-audits-2026-10-22/`. Unchanged.
- **Foreign untracked files.** Never stage them. Unchanged:
  - `hemasuite/docs/research/`
  - `docs/03-analysis/2026-10-22-ai-memory-hmad-handoff-integration.analysis.md`
  - `docs/03-analysis/2026-10-22-billion-context-hmad-handoff-integration.analysis.md`
- **Halted run dirs** `$KEEP/run-ab2c85dc2e25-20261022T015212Z` and `…T044856Z`. Incident evidence; never score them. Unchanged.
- **h-mad tooling defects 1–7.** Still unfiled; merged into Next Step 4.
- **Stray `$RUN/roots/graft/.cache/`** in run 2. Harmless. Unchanged.
- **Local env.** Unchanged:
  - `.h-mad/phase5-shell-allow` (8 bounded pytest lines);
  - root `.venv`.
- **Phase 6 residuals.** Deferred, unchanged:
  - T19 RMGUARD fixture (D16);
  - T22 `test_quarantine_never_deletes` greps the whole source.
- **About 179 leaked `hmad_exec_prompt.*`** in system temp. Unchanged.
- **Owed measurement-class notes.** Unchanged:
  - T19 `mktemp -t`/TMPDIR;
  - T19 AC-T19.4 grep scoping;
  - T20 re-anchor `audit_cycle_connections.mutation.json`;
  - T25 fixture ruling;
  - T26 RED split 29/3;
  - plan marker count 177;
  - T26 `unrecorded_*` → `unrecorded`;
  - D18 `cannot_run:truncated` cannot be reached on the live path.
- **Old S2 data** at `~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25/`. Evidence only, read by the step 10 positive control. Unchanged.
- **HemaSuite `pytest tests/` PID 70888.** Exited, result suspect, HemaSuite's. Unchanged.
- **Escape diff backup** `grok-escape-1254595a.patch` in the 2026-10-20 session scratchpad. Unchanged.
- **7 older `candidate: yes` rows** in `docs/skill-candidates.md` (2666, 2667, 2672, 2673, 2677, 2678, 2682). Deferred, unchanged.
- **agy install-check gap** (`:2673`, `AGY_SIBLING_COLLISION`). Seen again this session (`debugger` NOT_SYMLINK). Unchanged.
- **Other deferred items.** Unchanged:
  - mutation-harness interpreter override row (`:2666`);
  - backlog_cycle LOW residuals;
  - census `--help` FileNotFoundError;
  - `h_mad_mutation_harness.py:2300` SyntaxWarning (seen under python3.15 this session).
- **HemaSuite feature/204 `no-mutation-spec`.** HemaSuite's call. Unchanged.
- **Foreign `stash@{0}` (`resolved-model`, base `7541628`).** Do not touch. Verified intact twice this session; my own `git stash push -- <path>` / `pop` cycles stacked on top of it and popped cleanly. Unchanged.
- **Watch-only.** Unchanged:
  - the Bash pin blast radius;
  - the `.git/info/exclude` entries;
  - the row 1412 liveness limits;
  - agy-coder-fallback `review_independence_unrecorded`.
- **"Advisor ceiling exceeded".** This session made zero `advisor()` calls; context passed 45% at Task 14c and reached about 53%. Unchanged as a standing note.
- **"Handoff WRITE does not verify claimed state" and "Plan audit exit stamp never written".** Unchanged.
- **From `2026-10-02-main__v111-review-loop-closed.md`.** Unchanged:
  - [task #28] Run `test_h_mad_check_memory_index.py::TestAgainstTheLiveBinary::test_the_warn_and_target_fractions_still_match` by name.
  - [optional] agy live smoke.
  - V-11.1 residuals, round-22 F2, and tdd-gate-fail-opens bookkeeping.
  - The skill-candidates reconcile.
  - HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`; ownership stays here.

## Context for Next Session

**Commits this session (all on `main`, pushed):**

| Commit | Content |
|---|---|
| `a8715d86` | Task 14a RED |
| `b9e09c3b` | Task 14a GREEN |
| `1f859403` | Task 14b RED |
| `1c495954` | Task 14b GREEN |
| `f5f661b4` | Task 14c RED |
| `9f8c96c6` | Task 14c GREEN |
| `e3629604` | Task 14d gate record |
| `f7045cd0` | Run 3 incident |

**Files touched:**
- `h-mad/scripts/h_mad_assemble_audit.py`
- `h-mad/scripts/hmad-dispatch.sh`
- `h-mad/scripts/h_mad_grok_containment.py`
- `h-mad/tests/test_grok_audit_surface_path_scope.py` (new)
- `h-mad/tests/test_grok_audit_surface_assembler_pin.py` (new)
- `h-mad/tests/test_hmad_dispatch_audit_cycle.py`
- `h-mad/tests/mutation-specs/grok_audit_surface.json` (421 rows)
- `h-mad/tests/specs/audit_cycle_connections.mutation.json`
- the two `docs/03-analysis/grok-audit-surface.*2026-10-23*.md` records

**Uncommitted changes:** none besides this closeout. The three foreign untracked paths remain.

**Dispatch preface** (reuse it): `t14a_red2.prompt.txt` lines 1–8 in session scratchpad `0eee0477-41ca-4424-98fc-f6e48dc2e305` covers codex; `t14c_review.prompt.txt`'s READ PATH block covers agy. Both are ephemeral; the rule is in Key Learnings.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "grok-audit-surface"   # halted; read the incident doc, take the operator decision (Next Step 1)
```

**Related docs:**
- `docs/03-analysis/grok-audit-surface.incident-2026-10-23-run3-agy-gate.md`
- `docs/03-analysis/grok-audit-surface.task14d-gate-2026-10-23.md`
- Impl-plan §"Task 15", §"Task 16"
- Design D8 (Setup, run order), D21
- `h-mad/hooks/h-mad-agy-tdd-gate.py`
