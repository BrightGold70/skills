## Summary
This is a GATING round-2 audit (codex-leg stand-in) of the remediation in spec v1.20 (`d9f25dc2..d78cca8d`) and design v1.14 (`8a27d264..8fd0f637`). Neither file changes between those commits and HEAD `be702c08`: `git diff 8fd0f637 HEAD --stat` touches only the impl-plan. Every round-1 must-fix and should-fix in the spec and design audits is closed in the text, and so are the four design-level impl-plan items.

The fixes introduced two blocking defects:
- **Design v1.14's new per-cycle `$here` record is written after the `ASSEMBLE: HALT` exit.** An `assemble_halt` cycle is legitimately re-dispatched under AC-3.4/D8. It now leaves a cycle directory with no `*.here.txt`, so `assembler-check` reports `UNPINNED here_unrecorded` and the whole run cannot be scored. That contradicts D21's own text at two places.
- **Spec v1.20's AC-6.1/AC-6.2 additions never reached the design.** D14's exact SKILL.md strings and the D15/doc-pin tests carry neither the AC-3.9 phrase nor the AC-3.9 transfer residual. Design v1.14 takes spec v1.19.

What I read:
- all three round-1 reports in full;
- the whole spec diff;
- the whole design diff, plus design D21 (lines 553–602), D8 (208–296), D14 (422–437), D15 (438–462), the Test Plan doc and path-scope pins (787–801) and the PS rows (849–862);
- spec lines 484–495;
- from the tree: `_cmd_audit_cycle` lines 3720–3815 of `h-mad/scripts/hmad-dispatch.sh`, `record-cycle`'s stem regex in the probe (lines 670–700), `h_mad_audit_cycle.py` imports (lines 15–22), the `_script_dir_with_stub_assemble_and_real_cycle` helper, and the impl-plan's wrapper edit 5 (lines 1985–2012).

What I ran:
- The guard, capture and argv idiom, under `/bin/bash` 3.2.57.
- The `.here.txt` name against `record-cycle`'s regex.
- The pin and blob ids at HEAD, and the `invariants.base.md` commit counts.

Evidence: 12 files opened, 27 greps run.

## Round-1 closure
Spec audit (v1.17–v1.19):
- **Must: Delivery by outcome is a closed set** — CLOSED.
  - New table row: "Assembler not pinned, or no clause (AC-3.6, AC-3.9 fail closed; v1.20)".
  - The precedence paragraph adds "Two more refusals come before both on the same footing (v1.20)", naming `ASSEMBLER:` / `require --verb assembler` and `REQUIRE: STOP reason=path_scope_missing:p<i>`.
  - "So does AC-3.9 (v1.17): … It ships before the AC-1.9 re-smoke".
  - Fix (d) is answered by the AC-3.6 sub-bullet "Where each form appears (v1.20)". A wording residue remains (Nit 1).
- **Should: inserted bytes = clause + separator** — CLOSED. Test (5) and "Calibration prompt = production prompt + the clause" now say "the clause text plus the separator the design names (design D21: `PATH_SCOPE_CLAUSE + "\n\n"`)". This agrees with D21 line 563 and design test (5) (line 586).
- **Should: test (4) inputs omit `invariants.base.md`** — CLOSED. "and the base invariants `h-mad/invariants.base.md` … Both assemblies read the same current copy". Re-run: `git rev-list --count a489031f..7e1c48e3 -- h-mad/invariants.base.md` gives 0, and the count is still 0 to HEAD.
- **Should: AC-6.2 / AC-6.1 carry the AC-3.9 delta** — CLOSED in the spec, but not propagated to the design (Must-fix 2).
- **Should: AC-3.6 "Enforcement is owed"** — CLOSED. "Enforcement (v1.20, discharged by design D21) … No probe check and no AC-5.4 reason is added". NO_CLAUSE is named. AC-5.4 is untouched by the diff; the hunks are at 189, 198, 282, 475 and 532 only. The "sixteen reason forms" text stands at spec lines 195 and 255.
- **Should: AC-3.9 *Why* over-claims the `find`** — CLOSED ("It had also run a `find` over their ancestor `/Users/kimhawk/orca` and over `~/.local/state/h-mad`, which no prompt source names"). Residual (1) is extended to match.
- **Nits (4)** — all CLOSED:
  - the template option is qualified ("only if switch-off bytes stay identical");
  - "set and non-empty";
  - "before the first re-smoke cycle starts, after the tracer pair and the canary", plus the end reading on a smoke failure;
  - the test (6) RED lead-in.

Design audit (v1.13):
- **S1, the `set -e` capture** — CLOSED, line 565: `n="$(grep -cxF -e "$_HMAD_PATH_SCOPE_CLAUSE" -- "${prompt[$i]}" || true)"`, a string compare, and the class rule stated. Executed under `/bin/bash` 3.2.57 with `set -euo pipefail` over 1/0/2 matching lines and a missing file: `ok n=1`, `HALT n=[0]`, `HALT n=[2]`, `HALT n=[]`, rc 0.
- **S2, `$here` inferred and not measured** — CLOSED in principle (line 566, `${stem}.here.txt`; `here_unrecorded` / `here_mismatch`; the D8 diagram now uses `h-mad/bin/hmad-dispatch`). But the placement introduces Must-fix 1.
- **S3, "No test imports the clause"** — CLOSED, line 581: "The presence tests, (1), (3) and (5), never import the clause … The copy test … `ast`-parses the source".
- **S4, residual (2) vs the D15 NO_CLAUSE stamp** — CLOSED. D15 line 442 says the "stamp line is `assembler=<sha40>`, copied from the `ASSEMBLER: PINNED` token", and residual (2) is reworded at line 596.
- **S5, usage-error tokens** — CLOSED (lines 569 and 576, and the usage-error pair of tests at line 592).
- **Nits:**
  - header now names v1.19 — CLOSED;
  - test (4) wording — CLOSED (line 580);
  - `split("\n")` — CLOSED (line 573);
  - assembly-halt ordering — the sentence was added at line 579, but it is now false (Must-fix 1);
  - residual (6) and the measurement doc — CLOSED (line 600).

Impl-plan audit, design-level items:
- **Wrapper guard `${#scope_arg[@]}`** — CLOSED (line 565). Executed under bash 3.2: empty array → `unarmed`, and `${scope_arg[@]+"${scope_arg[@]}"}` expands to nothing; set → armed.
- **Production GUARD observes output** — CLOSED (line 588; PS14 at line 861).
- **Assembler-pin module** — CLOSED (line 592, the Components row, the mutation `command` list, and the path-scope pins at line 788).
- **Test (4) without `path_scope`** — CLOSED (line 580, "The current call passes no `path_scope` keyword (v1.14)").
- Count check: D21 names 14 tests in the path-scope module (2+2+1+1+1+2+2+1+1+1). There are 15 rows, PS1–PS15, and line 853 confirms that PS5 and PS14 share a target. That gives 13 distinct targets, which is 14 minus the negative control, as stated.

Question (3), spec↔design spot checks (both hold):
- `record-cycle`'s stem regex (probe line 680) does not match `audit_gas-d1_plan_cycle1_run20261022T010203Z-4242.here.txt` (executed: False; the `_p1.txt` control gives True), so the stem-prefix claim holds.
- `7e10f543` is still the last commit touching the assembler and template at HEAD, and both blob ids match.

## Must-fix
- **The per-cycle `$here` record is written after the `ASSEMBLE: HALT` branch, so a re-dispatched `assemble_halt` cycle makes the whole run unscorable (`UNPINNED here_unrecorded`).**
  - D21 places the `# M:PATH-SCOPE-HERE` write "Inside the same armed guard, before the clause check". That guard comes after the assembly loop and its `ASSEMBLE: HALT` branch. In the tree, that branch ends in `exit $?` (`hmad-dispatch.sh` lines 3765–3772, after it calls `h_mad_audit_cycle.py --halt-reason "assemble_halt:p${halt_pass}"`). The impl-plan's edit 5 inserts the guard after line 3773, which is the same placement.
  - So an `assemble_halt` cycle (D21 residual (7)'s `oversize`, or the line-579 scenario) prints `AUDITCYCLE: UNVERIFIED reason=assemble_halt:p<i>`, is recorded, and is re-dispatched as `v2` (D8 line 295: "any reason, `prompt_divergence` and `assemble_halt:pN` included"). Its `$RUN/stem/s2-d<k>-v1` directory holds no `*.here.txt`.
  - `assembler-check` walks every directory matching `^(s1-[a-z]+|s2-d[0-9]+-v[0-9]+)$` and reports `here_unrecorded:<cycle-id>`. That is an `UNPINNED` reason, ordered before every `NO_CLAUSE` reason (lines 572–573). The run is therefore not scored even when the re-dispatch succeeds. That contradicts spec AC-3.4 ("The second outcome stands") and two of D21's own sentences:
    - line 579 says the run reads `NO_CLAUSE clause_missing:…`, but it reads `UNPINNED here_unrecorded`;
    - residual (7) says "D8's re-dispatch applies", but the re-dispatch cannot rescue the run.
  - It still fails closed, but it turns a legitimate re-dispatch into a wasted S2 run under the "unpinned blocks scoring" ruling.
  - instance of: the class "an early exit of `_cmd_audit_cycle` that runs before a per-cycle record which a run-level check requires". The members in the tree are:
    - the `ASSEMBLE: HALT` exit (3765–3772): recorded, re-dispatched, and this defect;
    - the `exit 4` paths at 3742–3746 (`arc`, empty token, empty PASS prompt): `record-cycle` refuses `no_auditcycle_line`, so the run already stops, and the missing file is harmless.
    - The D17 refusals exit 2 before assembly, with the same harmless outcome.
  - The rule: the record must be written before the first exit that can still yield a recorded, re-dispatchable cycle.
  - Repairs, any one of these:
    - (a) Move the `printf 'here=%s\n' "$here" > "${stem}.here.txt" || exit 4` write to its own `if [ "${#scope_arg[@]}" -gt 0 ]` block right after `stem=` is computed (line 3720), before the assembly loop. Keep the clause check where it is. I checked that `stem` and `scope_arg` are both set by then: `scope_arg` per impl-plan edit 3 after line 3649, and `stem` at 3720. PS15 and `test_calibration_cycle_records_its_here` are unaffected.
    - (b) Have `assembler-check` read `here.txt` only for cycles whose recorded `AUDITCYCLE:` is not `UNVERIFIED reason=assemble_halt:`. This adds a parse dependency, and I have not checked it.
    - (c) Accept the behaviour, and rewrite line 579 and residual (7) to say an assembly halt unpins the run.
  - Under any repair, add a fixture: an `assemble_halt` cycle directory beside a good `v2` must not read `here_unrecorded`, or must, under (c).
  class: build
  quote: docs/02-design/features/grok-audit-surface.design.md › `Inside the same armed guard, before the clause check, the wrapper writes one line,`
  quote: docs/02-design/features/grok-audit-surface.design.md › `and D8 re-dispatches it. p1's clause-less prompt is recorded with it, so `
  quote: docs/02-design/features/grok-audit-surface.design.md › `That fails closed, and D8's re-dispatch applies.`

- **Spec v1.20's AC-6.1/AC-6.2 additions are not in the design, whose D14 is the "exact strings the tests pin".**
  - What the spec requires:
    - AC-6.2 now requires the SKILL.md replacement at both sites to carry `"measured with the calibration-only path-scope clause (AC-3.9)"`, and "a new assertion pins … the AC-3.9 phrase in both sections".
    - AC-6.1 now requires the measurement doc to name the AC-3.9 prompt delta as a transfer residual.
  - What the design has:
    - D14's PASS/MISS and INCONCLUSIVE strings (lines 427–428) do not contain the phrase.
    - `test_unmeasured_sites_match_the_outcome` (line 798) does not assert it.
    - `test_measurement_doc_states_the_transfer_residual` pins only "the D15 sentence", which is the AC-2.1 one (line 445).
    - D15's delta sentence (line 442) says what AC-6.1 needs, but it is not the residual and no test pins it.
  - Measured: `grep -c 'calibration-only path-scope clause'` gives 2 matching lines in the spec, 0 in the design and 0 in the impl-plan.
  - Cause: design v1.14 "takes spec v1.19 (`d9f25dc2`)". The two documents moved concurrently and the spec's v1.20 additions were routed to one of the pair only.
  - An S3 implementer writing the doc tests from D14 omits the phrase, and the spec gate then fails.
  - Fix:
    - Add the phrase to D14's PASS/MISS and INCONCLUSIVE strings, and to the `test_unmeasured_sites_match_the_outcome` assertions.
    - Either move the D15 delta sentence into the Residuals group under the transfer-residual doc test, or name a second doc test that pins it.
    - Bump the design header to spec v1.20.
    - Route the same change to impl-plan Task 16.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `and the words "measured with the calibration-only path-scope clause (AC-3.9)"`
  quote: docs/02-design/features/grok-audit-surface.design.md › `including the AC-6.1 transfer residual in this sentence, which a doc test pins`

## Should-fix
- **Spec AC-6.2 does not say whether the AC-3.9 phrase is asserted on the smoke-failure branch.**
  - The sentence "a new assertion pins the pointer to the measurement doc and the AC-3.9 phrase in both sections" is followed by "On a smoke failure, AC-1.8 replaces this retirement: … only the pointer and the smoke-failure clause are added". That reads as no phrase on a smoke failure, but the assertion is not scoped to the scored outcomes.
  - The S3 test's branch logic differs depending on the answer.
  - Fix: write "on PASS, MISS and INCONCLUSIVE", or add the phrase to the AC-1.8 clause too. Either is coherent.
  class: build
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `a new assertion pins the pointer to the measurement doc and the AC-3.9 phrase in both sections`

- **Spec AC-3.6 is stale against design v1.14's `$here` measurement.**
  - What is stale:
    - The spec's gloss of the refinements still describes one reading-side here check ("it is not the wrapper's own script directory"). In v1.14 that property is `here_mismatch`, which compares the per-cycle `*.here.txt`. `here_not_self` compares the reading with the checker's own `SELF_DIR`.
    - The spec does not mention `here_unrecorded`, `here_mismatch` or the per-cycle wrapper record at all.
    - "It records three things … Each is read twice" no longer describes how `$here` is measured.
  - "Include" is non-exhaustive and the list is single-sourced in D21, so this is not a contradiction. It is the spec lagging the design it now cites.
  - Fix: name the per-cycle `${stem}.here.txt` record and the two v1.14 reasons. Map "not the wrapper's own script directory" to `here_mismatch`, and gloss `here_not_self` as "the reading's directory is not the checker's".
  class: measurement
  quote: docs/01-plan/features/grok-audit-surface.spec.md › `it is not the wrapper's own script directory, or the tree's dirtiness could not be read.`

- **D8's "Order of a run" omits the smoke-failure end reading and its `--stages resmoke` gate.**
  - D21 line 570 says "On a smoke failure (AC-1.8), the end reading follows the last re-smoke cycle instead". D15 and D21 line 578 make the smoke-failure doc conditional on the `--stages resmoke` gate reading `PINNED`.
  - D8 step 4 ends at the smoke and the re-smoke commit, and only step 6 names the gate. The ordered runbook list is the one place a reader takes the order from.
  - Fix: append to step 4 "on `SMOKE: FAIL`: the end reading, `assembler-check --stages resmoke`, and `require --verb assembler`, before any doc is published".
  class: measurement
  quote: docs/02-design/features/grok-audit-surface.design.md › `and the re-smoke commit (D9) on every outcome that derives to`

## Nit
- Spec Delivery row and "Where each form appears": "`assembler=unpinned` … appears" in the incident record. The design never writes that literal: the incident carries the `ASSEMBLER: UNPINNED reason=…` / `NO_CLAUSE` lines and the readings verbatim, and the only design occurrence of `assembler=unpinned` is line 902, a historical table cell. A `path_scope_missing` halt has no `ASSEMBLER:` token at all, because its incident carries `REQUIRE: STOP reason=path_scope_missing:p<i>`. Suggested wording: "where the `ASSEMBLER:` token or the `path_scope_missing` line appears".
- D21 line 589: "holds … the real `h_mad_audit_cycle.py`". Round-1 impl-plan should-fix 4 (its sibling imports, `h_mad_audit_cycle.py` lines 18–20) is not addressed in the design. The existing `_script_dir_with_stub_assemble_and_real_cycle` symlinks the real scripts, and Python resolves a symlinked script's directory for `sys.path[0]`. Writing "symlinks, as `_script_dir_with_stub_assemble_and_real_cycle` does" closes it, which a plain copy would not. I did not run this.
- Spec AC-3.9 "Fail closed" says that an unrecognised switch "is the same failure". Under D21 line 567 it is the same outcome (not scored) but a different signal: exit 4, no `REQUIRE: STOP`, no halt-file line, and other lanes are not stopped. One clause in the spec saying so would prevent a reader from expecting `path_scope_missing` there.
