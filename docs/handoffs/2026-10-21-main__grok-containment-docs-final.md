# Handoff — grok-audit-surface: containment decided, all four documents final, ready for 5c/5d

**Date:** 2026-10-21
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-20-main__grok-audit-surface-s2-root-escape.md

## Session Summary

This session settled how grok is contained and how S2 will run. All four phase documents for that work are now final:

| Document | Final version |
|---|---|
| spec | v1.16 |
| plan | v1.11 |
| design | v1.12 |
| impl-plan | v1.7 (31 tasks, 3 wiring, 376 mutation rows) |

Every document audit ran its full two gating rounds and then one corrective revision that was not re-audited. All commits are on `main`, ending at `48a79863`. They are pushed by this closeout.

The h-mad state now has `phase=step5`, `halt_reason=null`, and the oracle returns `enter_autonomous`. **No code has been written.** Next is 5c: create branch `feature/218b-grok-containment`, then run TDD on Tasks 18–31.

## Key Learnings

- **The `/tmp`-located export roots were never the only problem: grok read the unseeded ORIGINALS in 11 of 12 recorded S2 cycles.**
  - It did so with `read_file`/`grep`/`find` on `docs/archive/...` in the live checkout. The seeds are the diff between those originals and the export root, so grok had the answer key.
  - Measured with `jq -R 'fromjson?'` over the `tool_call` `rawInput` of each `p3.log`.
  - A first parse without `-R` gave d5 v1 = 0. That is false; d5 v1 is the known escape. The parse aborts on one non-JSON line. A positive control is mandatory for this scan.
  - codex touched the repo in 2 of 12 cycles (metadata only). agy touched it in 0 of 12.
- **`grok --sandbox strict` (1.0.62, macOS Seatbelt) bounds reads as well as writes.** Reads are limited to cwd plus system paths. But strict grants ALL of system temp (`$TMPDIR`, `/private/tmp`), read and write, so parallel lanes rooted under `$TMPDIR` can read and write each other. That is why the roots move to `~/.local/state/...`.
  - strict refuses a `--prompt-file` outside cwd with rc=1, so it fails closed.
  - An unknown profile also gives rc=1.
  - grok documents that it warns and continues when a sandbox cannot be applied. No `sandbox-events.jsonl` was ever written, so a per-run canary is required.
- **`~/.grok/sessions/` holds the full prompts of past sessions.** Design and impl-plan audit prompts inline the unseeded paired originals, which were present for 6 of the 9 calibration sources. My first ruling ("seeded copies at worst") was false; the spec author refuted it by measurement. Only the pass's own session directory and `~/.grok/skills/` are now exempt, and old `gas-root-*` sessions are quarantined.
- **Verdict tokens exit 0 (base invariant).** The canary and quarantine exit 0 on every determined `REFUSED`, and exit 2 only on usage or internal errors. A codex auditor caught the spec saying "any other outcome exits non-zero".
- **Most audit must-fixes were propagation gaps.** A spec revision landed after its siblings were written, for example the sixth quarantine form. Pre-round sibling syncs, from each author's OWED list, cut later rounds: impl-plan musts went 8 → 7 → 3.
- **Shell slip:** backgrounding with `&` inside a `run_in_background` Bash call returns immediately and hides failures. A wrong `HMAD_AUDIT_STEM_DIR`, missing the `/scratchpad` segment, made `audit-cycle` exit 2 unseen.

## Next Steps

1. **5c: create the S0c branch.** `git checkout -b feature/218b-grok-containment` from `main` at `48a79863` or later. The impl-plan proposes that name (`docs/01-plan/features/grok-audit-surface.impl-plan.md`, header note ~line 9). The impl-plan and its audits are already committed on main.
2. **Stage the implementer.** Run `python3 ~/.claude/skills/h-mad/scripts/h_mad_tdd_judge.py implementer --root . --feature grok-audit-surface --record`, read the `TDD-IMPLEMENTER:` token, then run `hmad-dispatch env` and require `PREFLIGHT: PASS`.
3. **5d/5e: Tasks 18–31 in dependency order.** Stage each with `h_mad_assemble_tdd.py --phase red|green --task <N> ...`. Before the first RED, run `h_mad_prescribed_block_guards.py docs/01-plan/features/grok-audit-surface.impl-plan.md --repo-root .`. Carry the Phase-5 notes below into the relevant tasks.
4. **Task 30: operator-run NON-SEEDED live canary round trip.** `hmad-dispatch grok-canary` → `exec grok` under strict, against a scratch root, with its evidence file. This happens before the S0c merge.
5. **Then Task 15 in the new order:**
   1. codex tracer pair
   2. quarantine (`h_mad_grok_containment.py quarantine`)
   3. canary
   4. S1 re-smoke + TOOLSCAN
   5. smoke
   6. re-smoke commit, whose parent is the confirmed calibration tip
   7. quarantine again
   8. fresh S2 of all 9 docs × 3 surfaces as v1, in a new `run-<cal12>-<UTC>` dir, with per-cycle `require` + HALT
   9. d5 v1 positive control
   10. extract / labels / score sha
6. **Then Task 16** (measurement doc, citing the incident record and the superseded smoke `f7520e72`), **Task 17** (gated on S0c merged plus a scored, unhalted fresh S2), **5f/5g, Phase 6, Phase 7.**

## Open / Blocked Items

**This session — Phase-5 notes the authors left (not edited into the documents):**
- `REQUIRE:` has two printers: `require` itself and the audit-cycle halt branch (`REQUIRE: STOP reason=halt_file`). Consumers must not assume `require` printed it. Status: carry into the Task 22 and Task 27 implementation.
- D18's 32-hex token scan misses a token that is glued to adjacent hex characters. That fails open toward PASS. Status: needs a residual line or a fix in Task 23.
- The D9 runbook needs a fetched local calibration ref. A forced fetch discards a local ref that is ahead of origin. Status: needs a precondition check in the Task 15 runbook.
- The canary `cannot_run:truncated` form is unreachable on the live path, because `_cmd_exec` returns 3 for an end-less stream (hmad-dispatch.sh ~3207–3218, 3366–3370). Status: the design D18 note is owed, and the impl-plan v1.7 report states it.
- Acknowledged-not-fixed: plan `[prompt-divergence-repro]` (docs/01-plan/features/grok-audit-surface.plan.audit.v6.md). Its re-run command is in that sidecar.

**Carried from the 2026-10-20 handoff:**
- grok-audit-surface Tasks 15–17 have been re-planned. They are re-emitted in the new order in Next Steps and are no longer blocked on a decision, only on S0c implementation.
- The old S2 data `~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25/data/s2/` is now **incident evidence only and never scored** (spec v1.10 FR-3, operator ruling 2026-10-20).
- HemaSuite `pytest tests/` (PID 70888) read the reverted h-mad scripts. It has exited and its result is suspect. It belongs to HemaSuite and is unchanged.
- The escape diff backup is at `/private/tmp/claude-501/-Users-kimhawk-orca-skills/d00c4d73-f82c-4f9a-8bfd-7b4fcac2b3b1/scratchpad/grok-escape-1254595a.patch`. It was still present on 2026-10-20, is session-scoped and may vanish. Unchanged.
- S1/S2 artefacts for the measurement doc: agy and codex reported `delivered=out`, not `report-file`, and codex `Effort:` reads "not measured (codex-text log)". Unchanged; they go into Task 16.
- The 7 older `candidate: yes` rows in `docs/skill-candidates.md` (2666, 2667, 2672, 2673, 2677, 2678, 2682) are unchanged and deferred.
- The Codex Phase-5 gate refuses read-only checks (`e39f15c5`). Unchanged. This may bite in 5d.
- The agy install-check gap (`skill-candidates.md:2673`) is unchanged. `INSTALL: PASS` was re-seen this session, with advisory `AGY_SIBLING_COLLISION ~/.gemini/config/skills/debugger`.
- These are deferred and unchanged:
  - the mutation harness interpreter override row (`:2666`)
  - the backlog_cycle LOW residuals
  - the census `--help` FileNotFoundError
  - the `h_mad_mutation_harness.py:2300` SyntaxWarning
- HemaSuite feature/204 `no-mutation-spec` is HemaSuite's call; unchanged.
- The foreign `stash@{0}` (`resolved-model`) is present. Do not touch it.
- These are unchanged, watch-only or accepted:
  - the Bash pin blast radius
  - the `.git/info/exclude` entries
  - the row 1412 liveness limits
  - agy-coder-fallback `review_independence_unrecorded`
- "Advisor ceiling exceeded": one `advisor()` call this session, early, at about 35%. Unchanged.
- "Handoff WRITE does not verify claimed state" and "Plan audit exit stamp never written": both unchanged.
- From `2026-10-02-main__v111-review-loop-closed.md`:
  - [task #28] Run `test_h_mad_check_memory_index.py::TestAgainstTheLiveBinary::test_the_warn_and_target_fractions_still_match`. The full suite read 7007 passed at every audit cycle this session (2026-10-20), so it is likely green, but that one test was not run by name.
  - [optional] agy live smoke with canonical declaration. Unchanged.
  - [suggested] `h_mad_assemble_tdd.py --mutation-spec` live at a 5e. **Due in this feature's 5e.**
  - V-11.1 residuals and round-22 F2. Unchanged, deferred.
  - tdd-gate-fail-opens evidence bookkeeping. Unchanged, deferred.
  - skill-candidates reconcile. Not run this WRITE either (`automation scout` skipped, see below).
  - HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`. Unchanged; ownership stays here.

## Context for Next Session

**Commits this session (13 on `main`, pushed by this closeout):**

| Commit | Content |
|---|---|
| `e94727ce` | containment decision |
| `a489031f` | spec v1.9 + route reversal |
| `880cf173` | spec v1.10 |
| `b233caa6` | spec v1.11 |
| `e3d84865` | spec v1.12 |
| `37df3ccc` | plan + design v1.6 |
| `37e48a23` | v1.13/v1.7/v1.7 |
| `d49c3020` | round-1 answers |
| `e4a98d45` | pre-round-2 sync |
| `9628c857` | plan/design final correctives `[audit-override]` |
| `121ae4ce` | impl-plan v1.5 |
| `b17e1b36` | impl-plan v1.6 |
| `48a79863` | impl-plan v1.7 `[audit-override]` |

**Files touched:**
- `docs/01-plan/features/grok-audit-surface.{spec,plan,impl-plan}.md`
- `docs/02-design/features/grok-audit-surface.design.md`
- the audit reports `design.audit.v3–v4`, `plan.audit.v4–v6` and `impl-plan.audit.v3–v4`, with their `.effort.json` files
- `docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md`, which gained three decision sections
- `.h-mad/wires.jsonl`, written by the wire-pin gate
- `docs/.bkit-memory.json` (untracked state)

**Uncommitted changes:** none besides this closeout.

**h-mad state:** `phase=step5`, `halt_reason=null`. The claim is released at closeout, so the next session claims it with plain `--claim`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "grok-audit-surface"     # oracle → enter_autonomous; then 5c branch feature/218b-grok-containment
```

**Related docs:**
- The incident record: `docs/03-analysis/grok-audit-surface.incident-2026-10-20-grok-root-escape.md`, sections "Containment decision", "S2 route decision" (superseded) and "S2 route reversed to (a)".
- Design D16–D20: `docs/02-design/features/grok-audit-surface.design.md`.
- Impl-plan Tasks 18–31: `docs/01-plan/features/grok-audit-surface.impl-plan.md`.
- Spec FR-11 (AC-11.1–11.7), AC-1.9, AC-3.8, AC-6.6: `docs/01-plan/features/grok-audit-surface.spec.md`.
