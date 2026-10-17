# Report: agy-coder-fallback

## Executive Summary
agy is now a gated Phase-5 peer implementer beside Codex and grok: merged as `dba9e1f9` (Tasks
0–19), and FR-8's post-merge stage (Tasks 20–22) proved the gate live on agy `1.4.0` — a real
forbidden write refused, an overrunning handler blocking, and a real agy RED/GREEN — so the
feature is COMPLETE.

## Summary
The feature added the agy TDD gate (`h-mad-agy-tdd-gate.py`), the `--agy` wiring check, the
`--agent agy` assembler path, the review-independence/implementation-authors state fields and
Phase-7 warnings, and the implementer-neutral prompt with the WIRE-PIN new-caller case (FR-9).
Post-merge, the payload capture showed agy `1.4.0` declares only three of the five class-(b)
inventory tools to the model; by operator decision (D-FR8-1) Task 20 was narrowed to the three
captured tools, which surfaced and fixed a real defect: `replace_file_content` names its target
`TargetFile`, which the gate did not read, so every in-place edit was refused during step5. The
derived agy dispatch timeout is 900 s, and this repository now commits its `.agents/hooks.json`.

## Metrics

| Metric | Value |
|---|---|
| Plan audit cycles | not recorded in state (`audit_cycles` counters 0; see `docs/03-analysis/agy-coder-fallback.authoring/`) |
| Design audit cycles | not recorded in state (as above) |
| Impl-plan audit cycles | not recorded in state (as above) |
| Iterate cycles (Phase 6b) | 0 |
| Final match rate | 100% (9/9 in-scope FRs, 20/20 ACs pre-merge; AC-8.1/AC-8.2 met post-merge) |
| 6a-prime architectural review | `READY_TO_MERGE` (`EVIDENCE: PASS`) |
| Tests | 6521 passing / 0 failing (full h-mad suite at `f3233797`, clean, no TREE_MOVED) |
| Phases with back-propagation | Phase 5 → impl-plan/design: D-FR8-1 (Task 20 scope), D5d-1, D5d-5 wording |

## What Went Well
- The capture gate's "no subset" rule forced the tool-declaration finding into the open instead of
  letting three uncapturable tools be silently dropped; the narrowed scope kept the three
  undeclared tools fail-closed (no `PATH_KEYS` entry → deny under active step5).
- The live tracer settled three unknowns the design left open, each by observation: a gate `deny`
  beats the global `orca-status` `ask`; project `.agents/hooks.json` loads without a trust prompt
  in both the fixture and this repository; an overrunning handler is killed and blocks
  (`timeout-blocks`, 6.1 s at T=5).
- The assembler's built-in wiring check ran inside every `--agent agy` staging, and agy completed a
  real RED (117 s) and GREEN (71 s) with every `.py` write under the root.

## What To Improve Next Time
- Hook order inside `.agents/hooks.json` is load-bearing: with the gate first, its `deny`
  short-circuited the capture handler, costing one capture attempt. A capture hook goes first.
- `init.tools` is not the model's declared tool set; an inventory taken from `init` alone
  over-counted class (b). A capture stage should list callable tools before instructing.
- Running the full suite while committing other work produced `TREE_MOVED`; the suite was re-run
  on a still tree. Queue commits behind a running suite.
- A hand mutation re-run read a stale `__pycache__` (same-size rewrite in the same second); the
  harness already purges bytecode, hand probes do not. Use the harness or `rm -rf __pycache__`.

## Carry Items
- `multi_replace_file_content`, `sed_file`, `notebook_edit`: re-open Task 20's capture when an agy
  version declares them (`agy-runtime.md` §"The TDD gate" names the re-take trigger).
- Post-merge Tasks 20 and 22 had no 5e review leg; Phase 7 carries `WARNING
  review_independence_unrecorded` (the feature predates its own `implementation_authors` field for
  Tasks 0–19).
- Fixture project `/Users/kimhawk/orca/agy-fr8-fixture` and the merged feature worktree
  `/Users/kimhawk/orca/workspaces/skills/agy-coder-fallback` can be removed.
- Tooling gaps from 5d (assembler `gate` shape, single `--test-path`, no `--env-known-failure` for
  the sandbox teardown, `h_mad_wire_registry.py verify` uses PATH python): skill-candidate rows.
- Design FR-4 `FAIL parser` sentence; `failure-recovery.md` rows for the `step5:implementer_*`
  halts; ASSEMBLE-TDD HALT classification (spec FR-5 residual).

## Version History
- v1.0: Initial report draft (2026-10-17, after FR-8 Tasks 20–22).
