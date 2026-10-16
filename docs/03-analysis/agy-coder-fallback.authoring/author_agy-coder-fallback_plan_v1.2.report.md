PLAN-AUTHOR: DONE version=v1.2 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.plan.md lines=710 sha256=c5dbae34191f6393cff0c10893e53c2c1359220e3ea9e0000eb039b5a55f8844

## Pre-write assertion
- Before the first write: sha256 8827b5f4…, newest VH line v1.1, mtime 1792127466. All matched the brief.
- HEAD had moved to d90decc6, which commits only the audit reports. h-mad/ is unchanged since 17d73037 (`git diff --stat 17d73037 d90decc6 -- h-mad` → empty).
- Spec v1.4 (e6610381, sha256 2f9991b2…) landed mid-task. I read its ACs, FR-1 mechanism, FR-5 exit table and FR-8 step 2a, and folded them in (coordinator message).
- The plan is uncommitted. I did not commit it.

## Findings answered (plan owner)
- **F1:** stage 5 mirrors spec v1.4 FR-5's exit table.
  - Verdicts exit 0. UNREADABLE exits 2, and no-token gives `check=no-token` with exit 2.
  - AC-5.2 pins the token and the exit code separately.
  - The `h_mad_assemble_tdd.py` docstring ("2 on any HALT") is rewritten in the same commit.
  - The two conventions and the `h_mad_hook_wiring.py` precedent and divergence are stated.
  - New deliverable row.
- **F2:** DO-4's premise is corrected. `format` is enforced on neither path; probe re-run at d90decc6.
  - The mechanism is a design obligation, with the three options.
  - Carries the rfc3339-validator hazard, the AC-1.2 fixtures, and the package-absent fixture.
  - For a schema-wide mechanism: `classify_store` (h_mad_state_validate.py) over the live state files, plus a blast-radius note on the 3 existing date-time fields.
  - R-6 rewritten.
- **F3:** stage 6 adds the differential corpus (AC-9.2) with the 4 spec cases plus a plan-added `other-symbol` case. Changed set must equal {new-caller}. Callee resolution is decided by executed import, never traceback parsing.
  - New DO-7: no code applies the rule today (`git ls-files h-mad/scripts h-mad/hooks | xargs grep -ln red_wrong_reason` → 0 files). The design says prose or code, and states the corpus residual.
  - New R-14.
- **F4:** stage 6 adds the incident replay (AC-9.3).
  - Covers T4/T5/T6 at their task commits 531a6296b/7aa0d9dec/c2d671f6b, each verified with `git log -1`.
  - The RED is reproduced at the parent, in a scratch worktree or archive export, never in the live clone.
  - Wire-cut re-run, M4.1/M5.1/WIRE 2 citations, both shas.
  - An unreproduced case is counted, not dropped.
- **F5:** stage 8 adds step 2a.
  - Delay hook: timeout T, sleep ≥2T, in the project `.agents/hooks.json`, never the global one. Same transport.
  - Three independent readings, four outcomes, and `session-error` is re-run.
  - Deletion is recorded, plus a byte-identity check of hooks.json by shasum before and after.
  - `timeout-allows` → agy-runtime.md residual plus an operator question. New R-13.
- **F6:** DO-1a's false statements are corrected. Placement invariants P-1..P-5 cover the 6 tests, each located by test name with a grep. They include the ambient-PATH consequence: `fallback=` stays the raw fold, and both-peers-out gating is applied in the hook.
  - Mutation-row dependents: grok_wire_reverts.json has 1 row on P-1's test, and tdd_judge_chain.json has 2 rows on P-4's test.
  - Probed with a scratch script, now deleted. Results:
    - per-record slot: passes all 5;
    - uncaptured header prefix: passes all 5;
    - captured prefix: fails P-2;
    - header after fallback=: fails P-1 (p2's suggested placement, now explicitly forbidden);
    - trailing field: fails P-3.
  - bash ERE `(?:)` → rc 2.
  - Aligned to spec v1.4 AC-3.2: test_h_mad_tdd_judge.py has ACTIVE_RE as its only changed literal. R-4's mitigation is extended to diff that file.
- **F7:** the FR-10 locator is now structure-aware. The Phase-7 step is list item 7, so it uses the `str.index` slice precedent from test_h_mad_archreview_pane_halt.py (`7. **Closure (autonomous)**` → `\n## Phase 5`).
  - R-8 names the `_phase_5e_text` end anchor `Phase 5 implementation is **Codex's job**`.
  - Class closure: a new "doc-pin census" lists every test literal pinned inside each section stages 6/7 rewrite, across SKILL.md (Codex authors Phase 5, Exit-code dispatch, Phase-7 item, 5d bullet), agy-runtime.md, the failure-recovery row and the prompt (23 literals / 8 files). It comes with a rule over the class.
- **S1:** every FR-10 baseline carries an inline command using the docsections locator.
  - Re-run at d90decc6: 0/0, 2 (exec agy lines) and 0 (exec agy + implement), 0 (Phase-7 WARNING), 0 (agy-runtime).
  - Every published command was extracted from the document and executed verbatim. Each matched.

## Measurements re-run (all at d90decc6 unless noted)
- M-1: `rtk proxy /opt/anaconda3/bin/python3 -m pytest h-mad/tests --collect-only -q -p no:cacheprovider | tail -1` → 6042 tests collected (unchanged).
- DO-1a: `git ls-files -z h-mad | xargs -0 grep -l 'TDD-STATE: active' | wc -l` → 6 files.
- Broader line-shape census: `git ls-files -z h-mad | xargs -0 grep -l -e 'codex-escape=' -e ' record=' -e 'STATE_ACTIVE_RE' -e 'format_state_line'` → 7 files (the 6 plus grok_wire_reverts.json, by a test name).
- Halt token: `git ls-files -z h-mad | xargs -0 grep -l red_wrong_reason | wc -l` → 3 files.
- Heading pins: `git ls-files -z h-mad/tests | xargs -0 grep -l 'Codex authors Phase 5'` → 2 files.
- `grep -c -B3 '"format"' h-mad/scripts/h_mad_state_schema.json` → 3 matching lines.
- Spec AC census: `h_mad_ac_census.py <spec>` → `ACS: OK count=18 frs=9` (e6610381).
- Validator probe (from p1) → Draft7Validator True, bundled True.

## Tree contradicted
- p2's F6 remedy ("header fields after fallback=<fold> and before record=") contradicts P-1. It was not adopted.
- p2 quoted the plan as saying "Known in the tree at e7730f78: test_h_mad_tdd_gate_docs.py locates §Codex authors Phase 5 by heading substring". That text is not in v1.1 (`grep -n 'Known in the tree'` → no hit). The finding's substance still held.

## Precheck
- Result: PRECHECK: PASS issues=0. Advisories I kept:
  - PATH (9): new files (h-mad-agy-tdd-gate.py, .agents/hooks.json), HemaSuite-relative paths I verified, and the test literal `src/docs/foo.py`.
  - STALESHA, the R-8 cell `e7730f78`: re-run at d90decc6 with the same result. h-mad is unchanged, and I did not hand re-stamp it.
  - COUNT, at the M-3 sentence and the VH line: false positives of the "N files beside a list" heuristic.

## Owed by other documents
- Spec: nothing. v1.4 answers F1–F6, and step 2 now "settles two unknowns".
- Design: DO-1/DO-1a (P-1..P-5), DO-3, DO-4 mechanism, DO-5, DO-7.
- Impl-plan: each FR-9/FR-10 Task's RED names the census pins it moves. The doc-pin census and the line census become committed probes under docs/03-analysis/probes/agy-coder-fallback/. I wrote neither.
- Later feature: classify the existing ASSEMBLE-TDD HALT reasons (spec FR-5 residual).

## Judgement calls for the orchestrator
- Stage 5 requires a test-pinned sentence in the rewritten assembler docstring, so that a stale "2 on any HALT" fails. The spec does not ask for this. I can revert it if you prefer.
- I added a fifth corpus case, `other-symbol`, beyond AC-9.2's four. It is additive, and I can revert it.
- The doc-pin census is heuristic: string constants ≥16 chars containing a space, plus a second pass at 8 chars. Its residual is stated in the plan.
