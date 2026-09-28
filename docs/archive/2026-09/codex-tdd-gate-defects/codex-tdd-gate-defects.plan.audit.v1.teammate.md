AUDIT-codex-tdd-gate-defects-plan-v1-BEGIN
## Summary
I checked the plan's premises against the tree rather than taking the inlined text on trust. I extracted both embedded probes, and their sha256 values match the pinned digests. I ran `reproduce.py` and got all 22 `REPRO:` readings the plan claims. That includes the `run_suite` census row `'2 passed, 1 error in 0.1s' summary=(2, 0) verdict=PASS`, so the orchestrator's specific question is answered: PASS today is confirmed. P1, P2, P4, P5, P7–P10, the census greps, the stamp count, the stale-prose counts and the collection counts (3552/201/140) all reproduce. However, the plan has six blocking gaps:
- the Claude gate still decides whether a write is governed with its own root-first state reader, and I reproduced the resulting fail-open;
- `set -euo pipefail` makes the judge's rc decide the outcome;
- a second `Production file` parser already exists in `h_mad_wire_registry`;
- FR-4 has an unrouted widening;
- the probe's own success criterion cannot tell anything apart under form (b);
- three existing negative tests go vacuous under form (b).

Axis C (plan audit, FR granularity):

| FR | Classification | Note |
|---|---|---|
| FR-0 | implemented-as-written | P0 + V-0 |
| FR-1 | implemented-as-written | layer 3 |
| FR-2 | implemented-as-written | AC-2.9 widening routed as OQ-4 |
| FR-3 | implemented-as-written | layer 5, G3 |
| FR-4 | **restated** | `no tests ran` reason change adopted beyond the spec's "one change", not routed (Must-fix 4) |
| FR-5 | implemented-as-written | layer 4 |
| FR-6 | implemented-as-written | inherits the spec's "not step5 unchanged", which defeats the chain reader on the Claude side (Must-fix 1, owed to both documents) |
| FR-7 | implemented-as-written | extra docs routed as OQ-2 |
| FR-8 | implemented-as-written | W1–W6 add to it |

Not verified: the 605 s full-suite reading `1 failed, 3892 passed` (not run). Whether a real Claude Code session honours the V-0 flags is also unverified: the flags exist in `claude --help` 2.1.283, but I ran no session. Note: HEAD moved to `5a9cd8ed` (grok impl-plan v1.2) during this audit.
Evidence: 22 files opened, 41 greps run.

## Must-fix
- **The Claude gate still decides "governed?" with its own reader, so a mirror of OD-3 stays open.** The judge's chain reader only picks the test. Whether the write is governed at all is still decided by `_resolve_state_file` (root file first, `h-mad/hooks/h-mad-tdd-gate.sh:31-34`) plus `head -1` over that one file (`:96-103`). The spec's "not step5" path is listed as unchanged and runs before the judge call.
  - Reproduced at the current tree with a git-root fixture: the root `docs/.bkit-memory.json` has only a `step3` record, and `hpw/docs/.bkit-memory.json` has `feat` at `step5` with `codex_status=exhausted`. `bash h-mad-tdd-gate.sh <root>/hpw/tools/w.py` → rc 0, no output.
  - Control (root state file moved aside): rc 1, `BLOCK: cannot derive test path`. The control pair isolates the root-first reader as the cause.
  - Nothing in FR-1…FR-6 changes this path. The plan's G5/W5 and "both gates call one state reader" are therefore false on the Claude side, and there are two state readers for one decision (base §"Single-source contract"). The spec is the root: FR-1's closed `kind` set has no not-governed outcome, so the gate has to keep its own reader.
  - Repairs, any one of:
    - (a) Amend spec FR-1/FR-6 to give the judge CLI a not-governed result (a new ALLOW kind or a separate verb). The Claude gate then calls it whenever any state file exists on the chain, and takes the Codex-authorship check's `ACTIVE` key from the same chain reader.
    - (b) Keep the shell reader, but state this fail-open as a named residual in both spec and plan, with a test pinning it.

  Route this to both documents.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `The chain reader lives here too, so both gates call one state reader (OD-3).`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `itself, with FR-5's chain reader.`
- **The plan's "reads the token, never `$?`" cannot hold under the hook's `set -euo pipefail`** (`h-mad/hooks/h-mad-tdd-gate.sh:14`).
  - Executed: a `set -euo pipefail` script doing `OUT=$(printf "TDD-JUDGE: ALLOW kind=red-measured\n"; exit 3)` exits rc 3 before the token is read.
  - So a judge that crashes with a traceback (rc 1), or prints a valid line and then exits non-zero, ends the hook with the judge's rc. That bypasses the "one refusal function" and the chosen blocking form.
  - Under `E1_DOES_NOT_BLOCK`, an rc-1 crash is a fail-open. AC-1.3's four malformed-output stubs do not say which rc they exit with, so all four can pass while this hole stays open.
  - instance of: implicit exit paths under `set -euo pipefail`. The members are errexit on a command substitution (the judge call; the hook-relative `python3 -c 'import os,sys;print(os.path.realpath(...))'` resolution), `pipefail` on a pipeline, and `nounset`. The plan's stated residual (`… || exit 1` escaping the anchored grep) is a different member of the same class.
  - Rule: every command substitution or pipeline on the refusal path captures its rc explicitly (`OUT=$(…) || JRC=$?`), or the hook drops `-e` from that region. Then add AC-1.3 stubs that exit non-zero: one printing a valid ALLOW line with rc 1, and one printing a traceback with rc 1, each expecting DENY `judge-error` in the chosen form.
  - Residual: signals and timeouts that kill `bash` itself.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `The Claude gate reads the token, never`
- **A second parser of `Production file` already exists, and the plan does not name it.** `h_mad_wire_registry._production_claims` (`h-mad/scripts/h_mad_wire_registry.py:370-380`) re-parses the plan with its own regex `^\s*(?:[-*•]\s+)?\*{0,2}Production file\*{0,2}\s*:\s*(.*)$`. It also uses its own task counter (`## Task ` or `#{2,3} [MT]\d+`, not `_TASK_RE`).
  - It reads the singular label only, and it takes the whole value as one key with only its outer backticks stripped. So a two-path value such as the one in AC-2.1 becomes a single malformed key.
  - P4 found `h_mad_wire_registry` as a consumer of `_parse_tasks` (lines 271-272) and stopped there. Line 273 hands the parsed tasks to `_production_claims`.
  - After this feature, the judge and the wire registry would read "which Task owns this production file" with two grammars that can silently diverge (base §"Single-source contract"). OD-7's own rationale, "still exactly one parser each", would then be false.
  - Repairs:
    - (a) Bring `_production_claims` into scope and rewrite it over `task["production"]`. This changes wire-registry output for plural labels and multi-path values, which contradicts the Success Criteria line saying its tests pass unmodified. That would need a before/after differential over the 83-file corpus (base §"Guard narrowing").
    - (b) Leave it, but name it as a residual in plan and spec, route it to the spec with OQ-4, and add a test asserting the two agree on the corpus.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `Extend both functions in place, so there is still exactly one parser each.`
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `Parsers, extended in place (OD-7).`
- **Axis C, FR-4 is `restated`.** The spec allows exactly one audit-gate change. The plan adopts a second one and does not route it to the spec: the `no tests ran in …` row moves from `UNREADABLE no_summary` to `UNREADABLE no_tests_ran`.
  - That is a different `SUITE:` token (`SUITE: UNREADABLE reason=no_tests_ran`, printed by `main` and `h_mad_audit_cycle`). The spec says existing callers keep their current results.
  - OQ-2 and OQ-4 go to the spec, but this change has no OQ.
  - Repairs:
    - (a) Raise it as an OQ and amend FR-4/AC-4.7 to name two changes.
    - (b) Add an explicit branch that keeps `no_summary` for a parsed `no tests ran`, so the spec's single change holds.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `The one change to the audit gate:`
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `the same verdict and a more accurate reason; this plan adopts it and names it here so it is not`
- **The success criterion "post-merge reading shows the four fail-open cases denied" cannot discriminate for the Claude-gate cases under form (b), the recommended form.**
  - `reproduce.py`'s `claude()` discards stdout. It returns only rc and the first stderr line.
  - Form (b) refuses with rc 0, the reason in stdout JSON, and an empty stderr. So a post-merge DENY for OD-4 or OD-5 reads `(0, '')`, byte-identical to today's fail-open readings `REPRO: OD-4 tool_input (0, '')` and `REPRO: OD-5 nopytest (0, '')` (both reproduced by my run). D1 would also move from `(1, …)` to `(0, '')`, which looks like an allow.
  - That breaks base §"Test discrimination": no observation differs between the fixed and unfixed states.
  - Repairs:
    - (a) Change `claude()` now to report stdout's `permissionDecision`, and re-pin the sha256 and the 22-line count.
    - (b) Commit a v2 probe for the post-merge reading and say so.
    - (c) Narrow the criterion to D3 and OD-3 (Codex gate, which already parses stdout), and rely on AC-6.1 and AC-6.3 for the Claude cases.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `post-merge reading shows the four fail-open cases denied.`
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `return r.returncode, (r.stderr.strip().splitlines() or [""])[0][:90]`
- **Under form (b), three existing negative tests go vacuous, and more existing assertions change than the plan names.**
  - `h-mad/tests/test_h_mad_tdd_gate_codex.py` lines 87, 93 and 99 assert `"must be authored by codex" not in r.stderr.lower()`. Once the Codex-authorship BLOCK moves to stdout JSON, these pass even when that block fires.
  - Lines 78-79 (`"codex"`/`"dispatch"` in `r.stderr`) and `test_h_mad_tdd_gate_state_resolution.py:85` (`"H-MAD-TDD-GATE" in r.stderr`) fail outright.
  - AC-6.2 says only "rc assertions change". The plan's §"Regression provenance" floor names one changed test ("today: one").
  - Several of these rc-1 assertions are satisfied today by the D1 defect itself. They fixture absolute targets under `codex_status=exhausted`, which read `cannot derive test path` (my D1 reproduction). base §"Regression provenance" requires the plan to say what each asserted before any of them is edited.
  - Repair: list every stderr- and rc-reading assertion in the two Claude-gate test modules under §"Regression provenance" for the form-(b) branch. Name the channel each must read afterwards (stdout `permissionDecisionReason`), or make them assert on both streams. Record that the three negative tests would otherwise stop discriminating.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `the impl-plan names as changed under §"Regression provenance" (today: one —`

## Should-fix
- **The interpreter that runs the judge CLI is unspecified, and P8's premise does not hold in the existing hook-test harness.**
  - Both Claude-gate test modules run the hook with `PATH={bin}:/usr/bin:/bin` (`test_h_mad_tdd_gate_state_resolution.py:63`, `test_h_mad_tdd_gate_codex.py:62`). There, `python3` is Apple's `/usr/bin/python3`: `Python 3.9.6`, with `No module named 'pytest'` (both executed).
  - "No venv → `sys.executable`" therefore means every Claude-side fixture without a contained `.venv` reads `pytest-missing`. AC-6.4 requires `test-passing`, and AC-1.2's Claude half requires `red-measured`.
  - The judge, and the `h_mad_audit_gate`/`h_mad_wire_pin_gate` it imports, would also have to import under 3.9. Both have `from __future__ import annotations`. I did not check whether the future judge would be 3.9-safe (unverified).
  - State which interpreter launches the judge, and require Claude-side fixtures to supply a contained `.venv` (or a pytest-capable `python3` on PATH).
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `bare `python3` resolves to`
- **V-0's "hook was invoked" check accepts any invocation, not one on the sentinel Write.** `attempt` only tests `[ -s "$S/$1.invoked" ]`.
  - Scenario: the session writes some other file in arms E1 and E2 and the sentinel in E0. The reading is then `absent/absent/present`, a false `E1_BLOCKS`.
  - Repair: have the check `grep -q SENTINEL_E1.py "$S/$1.invoked"` (the log already holds each payload).
  - Separately, `claude --help` (2.1.283) describes `--settings` as loading *additional* settings. The user's own PreToolUse hooks (including the installed `h-mad-tdd-gate.sh`) therefore run in every arm. Consider `--setting-sources` to isolate the arm hook. I did not check the effect on the reading (unverified); most interference would land in `INCONCLUSIVE`.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `[ -s "$S/$1.invoked" ] || { echo "V-0: $1 UNMEASURED hook_never_invoked"; exit 1; }`
- **A stale-prose census candidate that will go false is outside the scope table.** `h-mad/references/codex-implementer-prompt.md:22` says the hook allows a production write only when "a derived test file exists AND the test file is currently failing". After FR-2 the test comes from the impl-plan Task first. Line 20's exemption list (`*test_*.py`) also no longer matches the hook's basename rule.
  - The census found the file (1 matching line). The plan's "Known to go false" names only `agy-runtime.md` and `SKILL.md`, and the scope table has no row for this file.
  - Add it to the scope table, or record it as re-read at 5g with the expected verdict.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `Each non-code match is a **candidate**, re-read at 5g against the shipped gate.`
- **The `1 error` explicit branch can break a mutation anchor without moving it.** The plan says `1 error` keeps `UNREADABLE no_summary`. If that branch reuses the literal `return {"verdict": "UNREADABLE", "reason": "no_summary", "rc": run.returncode}` at the same indent, then `audit_suite_gate.json`'s `a-missing-summary-becomes-a-verdict` anchor occurs twice.
  - The harness demands exactly one occurrence (`h_mad_mutation_harness.py:753` `hits = source.count(find)`; `hits != 1` → "narrow the anchor until it is unique").
  - The plan's rule covers lines that *move*, not a new duplicate of an unchanged one. Name it in the re-anchor rule.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `Rule: the `run_suite` edit keeps those three lines byte-identical where it can;`
- **The published ANCHORS command does not print the published reading.** `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json | tail -1` prints `[H-MAD] anchors ANCHORS_OK` (executed twice, on stdout). The `ANCHORS: ANCHORS_OK specs=99 mutations=907 …` line the plan shows is the second-to-last line of the tool's output, not the last. Its figures do reproduce (99/907/0 drifted).
  - Fix the command (`| grep '^ANCHORS: ANCHORS_OK'`), or fix the reading.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `# reading at 01121ca7: ANCHORS: ANCHORS_OK specs=99 mutations=907 ok=907 drifted=0 unreadable=0 skipped=0 unclassifiable=0`
- **R2's count over-counts by grammar and is now stale.**
  - At `01121ca7` the command gives 10 matching lines, as claimed. Only 7 of them are Claude-gate refusals or assertions: the three `exit 1 ;;` case arms, the two AC prose lines and the two mutation rows G1/G2. The other 3 (lines 1781, 1858, 1864) are `exit 1` in the verification scripts, matched through the `rc`/`;;` alternation.
  - The grok impl-plan changed after that sha (`git rev-list 01121ca7..HEAD` → `5a9cd8ed`, v1.2, which is now HEAD). There the same command gives 16 matching lines, still 7 of them gate-related.
  - Publish the classified figure (unit: gate-assertion lines) with its sha.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `→ 10 matching lines at `01121ca7`; owed to that impl-plan (report).`

## Nit
- P3's heading says "each with a control", but the OD-2 and D1 rows show `—`. Controls for both do exist in the same run (`D3 control-withpytest` is the root-relative form of OD-2's target, and `OD-5 control-withpytest` is D1's relative form). Cite those rows instead of leaving a dash.
- The census table's first column is headed "Final line", but `_suite_summary` takes the last regex match anywhere in `stdout + stderr` (`h_mad_audit_gate.py:422,450-453`). Once the parser gains a failed-only alternative, a stray `N failed` in stderr after the summary would be read as the summary. The design should state the scan rule, not "final line".
AUDIT-codex-tdd-gate-defects-plan-v1-END
