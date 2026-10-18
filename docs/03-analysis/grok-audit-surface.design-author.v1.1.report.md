DESIGN-AUTHOR: DONE version=v1.1 path=/Users/kimhawk/orca/skills/docs/02-design/features/grok-audit-surface.design.md lines=595 sha256=8af507a652cdefaa1dab362c83c6646b6f716ec5e44cbd825c2758b25e41f1fc

Not committed. The only file I changed is the design. I wrote and then deleted one scratch pytest probe, under the session scratchpad, not the repo. `git status --short` shows only the design as modified.

## Findings → where answered → singleton or class

| # | Finding (lane) | Design section | Kind; for a class, the rule and the exact residual |
|---|---|---|---|
| 1 | AC-1.3 D11 narrowed delivery to report-file (codex) | D11 "Delivery and acceptance" (quotes AC-1.3 verbatim) | Singleton. Reverted: `out` with a gate-scored collected report counts as delivery. |
| 2 | AC-1.6 acceptance inherits the narrowing (codex) | D11 `accepts()` | Singleton. Same predicate as #1. |
| 3 | AC-2.2 per-document multiset (codex) | D4 | Class: `ledger_counts` triggers. Rule: each AC-5.4 trigger is its own guard and its own fixture (Test Plan header rule). Residual: none; the list follows AC-5.4. |
| 4 | AC-2.7 no main-leak path without a score sha (codex) | D2 `main-leak` mode, D9 | Singleton (new mode). |
| 5 | AC-3.6 versions and RESOLVED-MODEL (codex) | D8 Versions and Resolved model; D3; D15 | Singleton. |
| 6 | AC-4.3 duplicate labels (codex) | D13 `label:<id>` (quotes AC-5.4) | Class: `label` triggers, same per-trigger rule. Residual: none. |
| 7 | AC-4.5 should-fix publication (codex, agy) | D12 Should-fix, D13 `SHOULD:` | Singleton. Residual stated: a report whose should walk disagrees with the gate's count is skipped, not published. |
| 8 | AC-5.1 no-token branch (codex) | D1 last resort; D2; Error Handling | Class: exits of every mode. Rule: one `try` in `main()` that prints the mode's own refusal token; the test is parametrized over all nine modes. Residual: none. |
| 9 | AC-5.3 precedence owed (codex) | D13 Verdict (quotes AC-5.3) | Singleton. The owed note is removed and a MISS-direction fixture is added. |
| 10 | AC-5.4 cycle_token / seed_rebuild expansions (codex) | D4, D12 (the seven triggers) | Class, same per-trigger rule. Trigger (7) is split into its report-file and out branches. |
| 11 | AC-6.1 transfer residual (codex) | D15, plus doc pin `test_measurement_doc_states_the_transfer_residual` | Singleton. |
| 12 | AC-6.3 INCONCLUSIVE text (codex) | D14 branch per outcome; `test_unmeasured_sites_match_the_outcome` | Class: outcome branches. Rule: one branch per outcome, and the test reads the shipped outcome from the measurement doc. Residual: none. |
| 13 | AC-7.2 fallback (codex) | D14 AC-7.2 text; S4 doc pins; wrapper `test_codex_agy_cycle_stamps_carry_the_legs_that_ran` | Singleton. |
| 14 | Refusal-token grammar D1 vs D9 (codex, agy) | D2 table (one row per mode) | Orchestrator decision (see Decisions). |
| 15 | Smoke ordering fixture unsatisfiable (codex) | D11 Coupled reasons; Smoke tests | Singleton. The coupled list is asserted, and a separable two-reason test (`truncated,vocab_split`) is added. |
| 16 | M4 validated by the wrong authority (codex) | D10 | Class: opposed-fixture authority checks. Rule: check each fixture against the authority that DECIDES the opposed field; when a decision reads two fields, check each against its own authority. Residual: a member whose authority needs a live agent (none). Adds e2b (`out`). |
| 17 | Key reassigns surface (codex) | D13 key_mismatch | Class: key triggers, per-trigger rule. Residual: none. |
| 18 | Root provenance has no input (codex) | D5 "Which list version", D8 `--root-record`, D3 `root.txt` | Singleton. |
| 19 | Classify connection not discriminated (codex) | D1 module seam, D12, tests, rows X1/X2 | Singleton. |
| 20 | FR-6 per-phase / per-class producer (codex, agy) | D13 `SPLIT:` lines | Singleton. |
| 21 | auditcycle.txt is calibration data (agy) | D3 (six named exclusions, each with its reason) | Class: the calibration-data set. Rule: the whole directory minus six named files, computed by one function that both trigger (i) and its test call. Residual: the six, which triggers (ii)/(iii) still scan. |
| 22 | extract has no S2 tree; quote paths (agy) | D12 Inputs and Hints | Singleton (`--s2`, plus the placement map that build-root also uses). Residual stated: a quote whose path none of the three resolution rules match. |
| S1 | P-row census unit (codex) | Test Plan P-rows "Two units" | Class. Marker sites come from `grep -c`, rows from `len(mutations)`. |
| S2 | ledger and seeded identity across shas (codex) | D9 Drift step 3 | Singleton. |
| S3 | stamps test helper (agy) | Wrapper pins | Singleton. Measured: see Premises. |
| S4 | smoke input_unparseable over-refuses (agy) | D11 input order | Class: smoke inputs. Rule: an input is required only where a reason reads it. Residual: none. |
| S5 | check-ledger --repo vs --tree (agy) | D2 (two front doors, one function) | Singleton. |
| nit | Overview "one cycle per root" (codex) | Overview | Singleton. |
| nit | shuffle_seed record (agy) | D12 Blinding | Singleton. The record moves to `extract.txt`. |

## Decisions
- **Token grammar (orchestrator's new decision).**
  - Each mode has one prefix, used by both its success token and its refusal token.
  - The checking modes refuse with `UNREADABLE` and AC-5.4 reasons. These are check-ledger, build-root, extract, score, rescore and main-leak.
  - record-cycle and commit-data refuse with `REFUSED` and their own closed sets.
  - Every mode prints `internal:<E>` inside its own grammar.
  - **This is a reading of the spec, announced here.** AC-5.1's literal `SEEDSCORE: UNREADABLE reason=internal:<ExceptionName>` is applied to score and rescore only. Applying it to the other modes would make them print two grammars, which the same AC forbids. Revert option: put every non-smoke refusal under the SEEDSCORE prefix. That needs AC-5.4 reasons for commit-data's `ref_moved`, `parent_unknown` and `ref_unconfirmed`.
- **A ninth mode, `main-leak`.** Required by AC-2.7, "a probe path that needs no score sha". "eight" no longer appears in the document.
- **The score sha must also descend from the smoke commit.** A failure refuses `calibration_drift:not_descendant`. Basis: AC-2.7's definition of the score sha.
- **`rescore` gains `--smoke-sha`.** The byte-identity check at the smoke commit (AC-5.5 fixture) needs it.
- **Six files are outside the calibration data**, to avoid false positives from trigger (i).
- **Every finding is labelled, must and should alike.**

## Premises verified (commands run at 94a4fd2c unless stated)
- **`collect` returns.** `sed -n 426,520p h_mad_audit_cycle.py`: `report-file`, `out` (from `_run_extract_report`), `none` and `unscorable:`.
- **Halted cycles.** `main` renders a halt as `render([], "UNVERIFIED", …)` (`sed -n 1328,1350p`). Its line has no `delivered=` field and no Effort block (`sed -n 1018,1085p`, `_effort_items` at 703-760).
- **Premise checklist.** Printed only on non-UNVERIFIED cycles (same read).
- **Truncated rendering.** The item text is `"p<i> not measured (grok log truncated"` (`_effort_items`).
- **GATE tokens.** `grep -n -o 'print(f\?"GATE: [A-Z_]*' h_mad_audit_gate.py` → INVALID x2, UNSTAMPABLE x1, verdict x1. Stamps are written only under `args.gated`. `GATE_RE` and `_gate_token` exist in h_mad_audit_cycle.
- **Imported symbols exist.** `classify` (returns `must_count` and `should_count`), `_bullet_groups`, `_payload`, `_is_none_sentinel`, `ORIGINS`, `_GROK_TYPES`, `_GROK_TYPES_RE=` (grep -n).
- **Test helpers exist.** Checked by grep -n: `run_with_cmd_exec_stub`, `run_audit_cycle`, `_audit_response`, `_script_dir_with_stub_assemble_and_real_cycle`, `install_audit_cycle_stubs`, `dispatch_args`, `project_with_docs`, `read_jsonl`, `_dispatch_artifacts_by_pass`, `STUBS` and `_bindir` (test_hmad_dispatch), `pass_result`, `audit_cycle`, `f0_text`, `f_trunc`, `f0_with_completed`, `titled_section`, `test_verb_prompt_divergence`, both `test_grok_fallback_docs` tests, `probe_readers`.
- **Stub knobs.** `codex` reads `HMAD_STUB_CODEX_LAST`; `grok` reads `HMAD_STUB_GROK_STREAM`.
- **Scratch probe (run, then deleted).**
  - `run_with_cmd_exec_stub` with codex,agy,grok → `delivered=report-file,report-file,report-file`, 0 stamps. agy's mechanism (`delivered=none`) was wrong; its conclusion (no stamps) was right.
  - `run_audit_cycle` with a three-stub bin dir → `delivered=out,out,none`, 2 stamps with legs `[agy,codex,grok]`, about 20 s.
- **resolved_model.** Refuses `agy --log`; for agy it reads the cli logs.
- **Exclusion-name reading.** `git ls-files | grep grok-audit-surface | awk …` → still 2 files at 94a4fd2c.
- **v1.0 readings still hold.** `git diff --quiet 3660aeeb 94a4fd2c -- h-mad docs/archive` exits 0.
- **SKILL.md sites.** `grep -c 'audit precision' h-mad/SKILL.md` → 1 line (the teammate section). The exec grok bullet wraps "audit / precision" (`sed -n 620,627p`).
- **Spec quotes.** A script checked every `spec AC-…: "…"` quote in the design: all 15 are substrings of spec v1.6.
- **Counts.**
  - D2 has 9 mode rows (awk).
  - Exactly six exclusions are listed in both D3 and its test.
  - Four imported modules; seven cycle_token triggers, giving 8 fixtures.
  - The tests list carries 6 `ledger_counts` triggers and 6 `seed_rebuild` triggers.
- **Value sweeps.** `grep -c -E` was run on the design for each of: `eight`, `roots\.jsonl`, `shuffle_seed`, `refusal vocabulary`, `Owed to the spec`, `leak:exclusions`, `MAINLEAK: scanned`, `step 4`, `no_delivery_on_out`, `format_grok`, `test_key_mismatch_ids`, `1\.0\.62`, `D5 step`, `match=yes`, `smoke-sha`, `should_count`. The retired values all read 0, and every remaining hit was read in context and is consistent. The sweep covered fences and table cells, because the command ran over the whole file.
- **Precheck.** `PRECHECK: PASS issues=0`. Advisories kept:
  - COUNT L110: "nine AC-2.4 fields" lists nine names; false positive.
  - COUNT L282: "both AC-6.2 sites" means two sites; false positive.
  - STALESHA 94a4fd2c: HEAD moved only the plan (8a48e328), not h-mad.
  - PATH advisories: new files.
- `VERSION-HISTORY: OK … version=v1.1`.

## Tree or sibling contradictions
- **grok version.** `grok --version` in this shell reports `grok 1.0.52 (0920c8169e27)`, but the spec FR-1 and D14 strings say 1.0.62. The design records the version and does not fix it. The orchestrator or operator must settle which grok S1 will run.
- **HEAD moved during my run.** The plan-author committed 8a48e328 (plan v1.4). I did not read it; my design input is plan v1.3, as the brief says.

## Owed elsewhere
- **Spec (one sentence, AC-5.1).** State that the `SEEDSCORE: … internal:<ExceptionName>` literal is the form for score and rescore, and that every other mode carries `internal:<ExceptionName>` in its own D2 grammar. Alternatively, accept the revert option above.
- **Spec (optional, AC-2.7).** The descent check from the smoke commit to the score sha is a design reading of "descending from the smoke commit". Naming it under `not_descendant` in AC-5.4 would make it explicit.
- **Plan.**
  - The probe now has nine modes, including `main-leak`.
  - Per-cycle `root.txt` replaces `roots.jsonl`.
  - `extract` takes `--s2` and `--base-sha` (the smoke commit).
  - `rescore` takes `--smoke-sha`.
  - The S3 runbook runs `main-leak` before the measurement-doc commit on every outcome.
  - The labeller also labels should-fix findings (more S2 labelling effort).
- **Impl-plan.** The stamps test path takes about 20 s per run, from the grok report-wait grace. Budget it in the suite.

## Declines
- None. Every must and should in both lanes is answered.
