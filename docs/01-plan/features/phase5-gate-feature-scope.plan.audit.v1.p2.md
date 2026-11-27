## Summary
Plan v1.2 establishes a strong single-source architecture, a 31-row two-way wire-pin plan, and verified baseline counts at `7a3cca48`, but has five blocking build defects across spec reconciliation (`FR-6`), gated state-writer reachability (`FR-7`), unprobed `worktree-ps` envelope extraction (`FR-10`), [redacted: private, operator record], and an internal/pinned-test contradiction in `grok-runtime.md` (`FR-11`). Three non-blocking gaps in the Claude-hook mutation census, `helper-scripts.md` contract updates, and [redacted: private, operator record] should also be resolved before Phase 4.

| Requirement | Classification | Notes |
|---|---|---|
| `FR-1` | `implemented-as-written` | Covered by S2, wire rows 22, 23 and 31, schema/writer deliverables, and Next Steps items 5, 6 and 9. |
| `FR-2` | `implemented-as-written` | Covered by S1, S4 and S6, wire rows 8, 14, 22, 24, 25 and 27–30, batched git classification, and `lstat` presence rules. |
| `FR-3` | `implemented-as-written` | Covered by S1 and S6–S8, wire rows 1–2, 4–5, 9–11, 13–18, 20 and 24, and cross-surface agreement corpus. |
| `FR-4` | `implemented-as-written` | Covered by S1, merged-reader differential matrix, `test_h_mad_phase5_scope.py`, and Next Steps item 4. |
| `FR-5` | `implemented-as-written` | Covered by S5, shared writer-parser reuse, and wire rows 7 and 12. |
| `FR-6` | `restated` | Plan narrows the Claude hook's target-only pre-filter for off-chain symlinked sub-project state files and allows returning the gap as a Phase-4 spec residual. |
| `FR-7` | `implemented-as-written` | Addressed in S10/S11, though keeping `_safe_shell_command` and `_operator_allowed` unchanged breaks `AC-7.1`/`AC-7.2`/`AC-7.4` in code (see Must-fix). |
| `FR-8` | `implemented-as-written` | Covered by S6 and S8, wire rows 15, 24 and 26, and `h_mad_tdd_judge.py scope` deliverable. |
| `FR-9` | `implemented-as-written` | Covered by S1–S3 and S9, wire rows 3, 9, 10, 13 and 21, and `phase5_stage_planning` staging halt. |
| `FR-10` | `implemented-as-written` | Covered by S0, S2, S4 and S11, though reusing `h_mad_live_runs.py` and [redacted: private, operator record] fail in code (see Must-fix). |
| `FR-11` | `implemented-as-written` | Covered by S3 and S10, wire rows 20 and 30, and seven-file documentation update list. |

Evidence: 74 files opened, 24 greps run.

## Must-fix
- [fr6-claude-maybe-not-superset] Axis C (`FR-6` restated) and Axis A contradiction: the Plan's target-only `"May be"` filter for the Claude hook is narrower than Spec `FR-6` and licenses deferring a covered `AC-6.2`/`AC-6.3` case to a Phase-4 spec residual — Spec `FR-6` unconditionally requires all three write hooks, including Claude `Write|Edit`, to refuse any state file `FR-2` counts from the session root or the target's own checkout (whether or not it exists yet) by resolved identity, with no residual for off-chain sub-project links; the Plan claims all 88 ACs remain in force unweakened and calls `"May be"` a superset of `FR-6`, yet immediately admits `"May be"` misses the real file under another name of an off-chain sub-project's linked state file (in fact it misses both existing referents, because a symlink leaves `st_nlink == 1`, and not-yet-existing referents on creation) and permits Phase 4 Design to return that case for a spec residual instead of satisfying `FR-6` as written.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `Targets are judged by resolved identity, so symlink, hard-link-in-directory and case-variant spellings are the same target; a target named through a symlink is also judged under the path as named, and either is enough.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `One member cannot be seen from the target: the real file, under another name, of an off-chain sub-project's linked state file. The design either pays for discovery there inside the 300 ms bound or returns the case for a spec residual; it may not drop it silently.`
- [fr7-gated-state-write-blocked] Keeping `_safe_shell_command` and `_operator_allowed` unchanged in what they admit makes `FR-7` (`AC-7.1`, `AC-7.2`, `AC-7.4`) impossible for a gated codex or agy session in three verified code paths — (1) in the shared-store worktree topology required by `AC-1.3` and `AC-3.1` (`<worktree>/docs/.bkit-memory.json` symlinked to `<main>/docs/.bkit-memory.json`), `_safe_hmad_script` calls `_argument_within(args[0], root / "docs", root, cwd)` -> `_path_within`, which checks `candidate.resolve().relative_to(parent.resolve())`, resolving the symlink to `<main>/docs/.bkit-memory.json` outside `<worktree>/docs` and refusing every safe-list state write including `halt_reason`/`halt_ts` (`FR-7` row 6, `AC-7.4`), `--beat` and `--release`; (2) in `AC-7.2`'s `codex orchestrator in the named checkout` and `agy` topologies, 5e runs after the 5d mark (shell gated) and requires `--append implementation_authors='{...}'` and `--append review_independence='{...}'`, but `"--append"` is absent from `SAFE_HMAD_SCRIPT_OPTIONS["h_mad_state_write.py"]` (`h_mad_target_identity.py:278-281`) and `{`/`}` fail `SIMPLE_SHELL_COMMAND` (`line 245`), which `_operator_allowed` (`line 599`) also enforces so even `.h-mad/phase5-shell-allow` cannot admit it; and (3) hook refusal hints (`FR-7` row 12, `h-mad-tdd-gate.sh:357,369,375,395`) pass `"$FILE"` last whereas `_safe_hmad_script` (`line 533`) requires `args[0]` to be `.bkit-memory.json`.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `, unchanged in what they admit; FR-5 is a check in front of both, not a change to the list.`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `AC-7.1: Each table row is driven by real state-writer commands, through the real hook when the row names a gated host, and gives the stated outcome.`
  quote: h-mad/scripts/h_mad_target_identity.py › `and _argument_within(args[0], root / "docs", root, cwd)`
- [fr10-worktree-ps-envelope-unverified] Reusing `h_mad_live_runs.py`'s lane listing for the landing probe drops both `truncated` and `omitted hosts` (`FR-10`, `AC-10.7`) and breaches Axis B (`Assumption verification` and `Wrapper–runtime reconciliation`) — `h_mad_live_runs.py:orca_lanes()` discards the `hmad-dispatch worktree-ps` JSON envelope around `worktrees` and returns only `list[Path] | None`, checking neither truncation nor omitted hosts, and the Plan never executes `hmad-dispatch worktree-ps` live or cites its observed output shape (`h-mad/bin/hmad-dispatch worktree-ps --limit 5` on this machine emits top-level `"truncated":true` and nested `"hostScope":{"hostIds":["local"],"omittedHostIds":[]}`, a key path referenced nowhere in `h-mad/` today).
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `for the landing probe, and the lane listing that`
  quote: docs/01-plan/features/phase5-gate-feature-scope.spec.md › `the lanes could not be listed, the listing was truncated or named omitted hosts, or a state file could not be read.`
  quote: h-mad/scripts/h_mad_live_runs.py › `return [Path(w["path"]) for w in data["worktrees"] if w.get("path")]`
  quote: h-mad/invariants.base.md › `The evidence belongs in the document, not only in the author's terminal.`
- [redacted: private, operator record]
  class: build
- [grok-runtime-doc-contradiction-and-pin] Adding "grok is ungated" (`AC-11.4`) to `h-mad/references/grok-runtime.md` without reconciling its existing `## The TDD gate` section or `test_host_runtime_docs.py` creates either an internal contract contradiction or an unaccounted pinned-test break (Axis B `Regression provenance`) — `grok-runtime.md:74-84` currently states that grok runs the Claude `PreToolUse` gate under `compat.claude.hooks`, halts Phase 5 with `step5:grok_tdd_hook_unverified`, and refuses `toolInput`-only writes in step 5, and `test_host_runtime_docs.py:400-407,422-438` pins `## The TDD gate` and those tokens; leaving `## The TDD gate` intact contradicts "grok is ungated", while revising it breaks `test_host_runtime_docs.py` outside the Plan's closed test-edit census.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `The only existing expectations edited are those the census names.`
  quote: h-mad/references/grok-runtime.md › `target and is refused ("could not identify the write target"), so that gap fails closed. A handler reaching the 5 s limit fails open.`
  quote: h-mad/tests/test_host_runtime_docs.py › `section = _required_section("h-mad-grok", "## The TDD gate", f"TDD gate {case}")`
  quote: h-mad/invariants.base.md › `When a change makes an existing test fail, the plan or design MUST establish whether that test`

## Should-fix
- [mutation-census-claude-hook-omissions] The `Mutation specs` census row for `Claude hook, early allows and verb reads` omits three committed specs that carry anchors in `h-mad/hooks/h-mad-tdd-gate.sh`'s verb-read and refusal blocks — `grep -l h-mad-tdd-gate.sh h-mad/tests/mutation-specs/*.json` also hits `tdd_gate_fallback_agent.json` (7 mutations across `_read_state` and `FALLBACK`), `tdd_gate_peers.json` (6 mutations across `_read_state` and `PEER_RECORD`), and `grok_wire_reverts.json` (`wr12-2-gate-never-reads-the-fold` in `_read_state`), all of whose single-match invariants sit in the same top-level script region edited in S5 and S6.
  class: measurement
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `The specs below have anchors inside functions this feature edits`
- [helper-scripts-doc-omission] S10 and `## Deliverables` omit `h-mad/references/helper-scripts.md` from the contract-text update list — `helper-scripts.md` is spliced into `doc_text(SKILL)` by `h_mad_skill_corpus.py` (`test_h_mad_tdd_gate_docs.py:47-55`) and enumerates both `h_mad_assemble_tdd.py`'s halt tokens (line 34) and `h_mad_tdd_judge.py`'s verbs and `TDD-*:` verdict tokens (line 36), so adding `checkout_mismatch`, `phase5_stage_planning`, and the `scope` verb (`TDD-SCOPE:`) without updating `helper-scripts.md` leaves the restored `SKILL.md` helper registry incomplete.
  class: build
  quote: docs/01-plan/features/phase5-gate-feature-scope.plan.md › `| S10 | Contract text, halt rows and runtime references | none on gates | FR-7, FR-11 |`
  quote: h-mad/references/helper-scripts.md › `SKILL.md with every split section's body restored in place of its pointer stub, byte for byte;`
- [redacted: private, operator record]
  class: build

## Nit
- Step `S5` in `## Implementation Strategy` §"Order of work" notes that `The exit route its refusals name already exists: the operator, a Claude or a grok session`, whereas `FR-7` / `AC-7.5` includes a fourth exit actor (`a codex or agy session whose checkout the record does not name`) that only becomes ungated at `S8`; note in `S5` that either the refusal text gains that fourth actor at `S8` or mentions that another-checkout codex/agy exit applies once checkout scoping is active.
