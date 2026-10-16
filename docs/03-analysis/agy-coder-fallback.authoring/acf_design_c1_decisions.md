# agy-coder-fallback — design audit cycle 1 decision sheet (orchestrator)
Reports: docs/02-design/features/agy-coder-fallback.design.audit.v1.p1.md (codex), .v1.agy.md (agy; the original p2 timed out, re-dispatched). Audited design v1.0 @df46f72a with spec v1.6 @c853b207, plan v1.4 @29ae3e7b.
Classification rule (set before reading verdicts): build = changes code/tests an implementer writes; measurement = a published number/stamp/probe command only. Orchestrator agrees with the reviewers' tags.
Premises spot-checked by orchestrator: design states leap-second refusal as residual; _is_shell_allowance calls candidate.relative_to(root) unguarded (codex gate); test_prompt_file_is_agent_independent loops ("codex","grok") with hashes[0]==hashes[1]; h_mad_target_identity carries a `names` tuple (hard-link names). All others: the AUTHOR verifies each premise against the tree before applying; decline with evidence if one fails.
Operator decisions in force: OQ-A = shared policy in h_mad_target_identity.py; OQ-B = post-merge FR-8 stage, COMPLETE only after it.

DESIGN (design-author) — all of these:
C1 (codex) leap second: ORCHESTRATOR DECISION — keep refusing a seconds=60 value (state timestamps are machine-written by h-mad's own writer via datetime, which cannot produce :60); the SPEC is amended to authorize this restriction (spec-author). Design: cite the spec's restriction, drop "residual" framing.
C2 (codex) hard links: classify EVERY same-parent name the identity module returns, as the Codex gate does; production if any name is production.
C3 (codex+agy) _is_shell_allowance on outside-root targets raises ValueError → containment check BEFORE the allowance call (or guard), and the agy-reported omitted in-root rules (see agy finding 2) — match the Codex gate's full in-root evaluation.
C4 (codex+agy) AC-9.1 three-agent prompt-equivalence: specify a WIRED agy fixture (.agents/hooks.json present in the test's tmp root) and assert all three hashes equal (not hashes[0]==hashes[1]).
C5 (codex) AC-X append control cannot bite → replace with a loss/corruption mutant the persisted-bytes observation can see.
C6 (codex) FR-7 attribution: record the author of the reviewed implementation from the successful implementation dispatch (not implementer_switch.to, which is historical). Spec FR-7 may need the same wording (spec-author).
C7 (codex) --append repeated on one key in one call: accumulate from the updated record; define interaction with --set on the same key; two-appends-in-one-call fixture.
C8 (agy) FR-6 guarded import vs test_codex_gate_kind[judge-error] hand-built tree (no identity module) — reconcile with OQ-A so the existing test passes unmodified.
C9 (agy) FR-4 class (c) run_command: no os.chdir before judging (or guard); handle Cwd=="" / malformed / nonexistent like the Codex gate does (match its existing tests e.g. test_a_workdir_outside_the_root_stays_refused).
C10 (agy) FR-1 _semantic_ok must guard isinstance(record, dict) (CORPUS passes ["nope"]); and the four-pinned-substring test on fallback_agent description.
C11 (agy) FR-5 --agent agy halts UNWIRED in a bare tmp root → covered by C4's WIRED fixture; make the design's statement consistent.
M1 (codex, measurement) FR-3 and FR-6 scratch probes: preserve as committed probes under docs/03-analysis/probes/agy-coder-fallback/ with exact invocation (do it — it's cheap and Phase 5 needs them).
Also from your own v1.0 report: nothing new; keep owed items listed.

SPEC (spec-author): S1 = C1 (FR-1/AC-1.1 authorize refusing a leap second, with the reason above); S2 = C6 wording in FR-7 if the spec says the reviewed implementation's author comes from implementer_switch; S3 = design-owed items: codex_status schema description + state-schema.md row added to FR-1/FR-10 surfaces; agy version 1.4.0 (FR-8 and the SessionStart re-check stamp the version they ran against); FR-6/AC-6.1 "shared module" = h_mad_target_identity.py (OQ-A); OQ-B post-merge stage recorded as operator decision.
PLAN (plan-author): P1 = M-4 is 31 rows (design re-derived), not 19; P2 = DO-2's agy-version condition cannot be met from the inventory log (it carries no version) — restate; P3 = OQ-A/OQ-B operator decisions mirrored; P4 = agy 1.4.0.
