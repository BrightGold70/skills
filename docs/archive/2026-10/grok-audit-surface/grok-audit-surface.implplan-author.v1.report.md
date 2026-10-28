IMPLPLAN-AUTHOR: DONE version=v1.0 tasks=18 wiring=1 mutation_rows=165 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.impl-plan.md lines=1479 sha256=57966d7b645e14c2ccbcce22c19b3bc737fcf93db8792525666d931a0db56776

Gates run on the final file: `PRECHECK: PASS issues=0` (h_mad_precheck_doc.py --phase impl-plan --root .); `WIREPIN: PASS tasks=18 wiring=1 unpinned=0 mislabeled=0` (I ran it with a scratch --registry, deleted afterwards, so nothing was registered).

## Counts (derived by parsing the document, not by hand)
- Tasks 18: operational 2 (T0, T15), new-behaviour 14, wiring 1 (T8), gate 1 (T14).
- Mutation rows 165 = 2+14+13+13+11+24+20+25+21+2+17+3 (T2..T13). Named 28 (W1-W10, G1-G5, C1-C4, K1-K3, X1-X6) + P-rows 137. Probe rows 143 (137 P + X1-X6).
- Marker sites 111 distinct `M:GAS-` names across the row tables, no name shared between Tasks (2+13+10+13+10+14+12+20+17).
- Every row's `test` is in that Task's own test list, except W8 (`test_verb_prompt_divergence`) and K1-K3 (`test_grok_fallback_docs.py`), which are existing tests.
- RED splits (node ids): T1 1F; T2 18F; T3 16F; T4 20F; T5 15F; T6 15F; T7 45F (42 smoke + 3 parser); T8 33F; T9 31F; T10 43 ids = 32F/11P; T11 1F; T12 14P; T13 3F; T16 3F (+1P on MISS/INCONCLUSIVE); T17 4F.
- The design gives no row total ("neither carried"). 165/111 are this plan's figures; T14 AC-T14.4 re-derives both.

## Premises verified (tree at 30917a1a; `git diff --quiet a6a1571a 30917a1a -- <design> h-mad` exit 0)
- h_mad_audit_gate.py: classify:458, classify_detail:411, _section_detail:309, BLOCKING_SECTIONS:32, _bullet_groups:226, _collapses:264, _flat_findings:204, _bullet_remainder:48, _payload:76, _is_none_sentinel:65, _leg_key:684, exit_check:694, round_check:785, `--round-cap` "N STAMP" (cap first). GATE prints: INVALID x2 and UNSTAMPABLE, all with must=0 should=0, so GATE_RE matches them.
- G1, G2, G3, G5 finds: grep -cF = 1 each.
- h_mad_audit_cycle.py: PassSpec namedtuple:25 "index report_path out_path rc log_path"; collect:426 (grace kw); _gate_token:746 (stdout, collected), raises OperationalError:93 when there is no GATE line; render:1018; _effort_items:703; measure_effort:520 with seven shapes; combine:875. C1, C2 finds = 1 each.
- h_mad_review_evidence.py: _GROK_TYPES:45, GROK_MAX_DEPTH=64:47, _CODEX_HEADER_RE:59, _json_deeper_than:320 (depth>bound, top level is 0), scan_grok:333 (split "\n", ValueError/RecursionError, dict, depth skip, type filter), format_targets:281.
- h_mad_audit_origins.ORIGINS: 8 members.
- hmad-dispatch.sh: `_GROK_TYPES_RE=` at :2078; W1/W4/W6/W7 finds = 1 each; `# M:STEM-DIR` = 4 matching lines; _cmd_audit_cycle:3496; stem `audit_${feature}_${phase}_cycle${cycle}_run…`; log[$i]="${stem}_p${i}.log"; exec has --cd/--out/--log/--timeout.
- tests helpers (all present): audit_cycle:29, pass_result:34 (test_h_mad_audit_cycle); f0_text:31, f_trunc:35, f0_with_completed:128, agy_transcript:146 (grokfixtures); run_with_cmd_exec_stub:552, _dispatch_artifacts_by_pass:523, dispatch_args:261, project_with_docs:134, read_jsonl:68, install_audit_cycle_stubs:148 (the stub writes the report path twice), run_audit_cycle:289 (_BINDIR), _audit_response:1349, _script_dir_with_stub_assemble_and_real_cycle:1375, test_verb_prompt_divergence:1066 (HMAD_ASSEMBLE_DIVERGE_P2) (test_hmad_dispatch_audit_cycle); STUBS:14 (test_hmad_dispatch); titled_section:35 (docsections); test_teammate_section_documents_the_grok_leg:46, test_never_gate_section_cross_references_the_grok_leg:51 (test_grok_fallback_docs); _stamp methods at :126/:241/:334 (test_h_mad_audit_leg_set_gate).
- SKILL.md: the teammate heading at :3030 holds `h_mad_audit_cycle.py --surfaces agy,grok` once; the section has "unmeasured" once and `--surfaces agy,grok` once (so K1 and K2 discriminate). K2 and K3 finds = 1 each; K1 find = 0 (S0 writes it). The legs bullet is at :2476. The headings at :1194 and :1256 exist.
- grok-runtime.md: §"Version and compatibility":6, the 1.0.41 sentence:8.
- h_mad_resolved_model.py: agy_from_cli_logs:123, --log, --agy-log-dir. h_mad_archive_feature.probe_readers:42 (path-boundary needle, markdown excluded).
- Mutation harness: the spec root resolves against the spec's own directory, so it does not depend on cwd. A row needs name, file and find; symbol is optional. A visible traceback framed in the mutated file counts as a crash kill (Tier 2). 1 of the 175 committed specs names a `../` file (host_runtime_docs.json, ../handoff/SKILL.md).
- New files are all absent (probe dir, the 5 test modules, grokauditfixtures.py, the spec). `.h-mad/` is untracked. Fixture-name check: 0 files.

## Findings applied (carry list, all 15)
1 OPEN-DECISION in Task 5, naming two satisfying implementations: (a) reorder D5 so step 6 runs before the re-walk; (b) the two fixtures also patch `rewalk_matches`.
2 Task 5: a no-follow reset (lstat; unlink links; O_NOFOLLOW; ancestor check; rmtree only on real dirs). Three fixtures (write-through file, delete-through dir, write-through parent). Each asserts both directions: the outside target is unchanged, and the link itself is removed or replaced. Three rows whose replace follows the link.
3 Task 5 "Fixtures": default parent with `--purpose s1 --doc d1`, and the stated exceptions.
4 Task 7: `test_smoke_unrecognised_effort_item_refuses` + `p-smoke-effort-unknown`.
5 Task 7: one reader, `grok_log_types`. Its open class differs from scan_grok's in exactly one way: dict lines with a string type nested deeper than GROK_MAX_DEPTH. I chose "state the class exactly" over "share the reader" because sharing would flip the design-pinned residual-(2) test from PASS to FAIL (rule 7). See contradictions.
6 Task 15 step 5: the before-listing goes right after the agy block's `STEM=…; mkdir -p` line.
7, 8 "Measurement acknowledgements", with re-run commands and readings.
9 Task 0 (operational, first), consumed by Task 15 step 2.
10 Task 7 (stated), Task 15 step 7, Task 16 runbook.
11 Rows in T5/T7/T8; counts in T14.
12 Task 2: `_TokenArgumentParser` + `test_usage_error_prints_the_mode_token`.
13 Task 5: `ResetPurposeNotS1`, `# M:GAS-RESET-PURPOSE`, a test.
14 Task 7 (synthetic pairing) and Task 6 (`test_record_cycle_copies_stem_files_byte_for_byte`).
15 Task 7: depth built from GROK_MAX_DEPTH; no literal 65.

## Contradictions found / OWED-ELSEWHERE
- DESIGN D11 residual (2) + "guaranteed": scan_grok catches RecursionError and skips the line, and so does the plan's reader. So "lines raising RecursionError … while this step-2 type reading counts them" cannot happen with a json.loads reader. Residual (2) is only the depth class. "Guaranteed" for `unparseable` holds only outside that class.
- DESIGN D11 step 3: the wrong-file branch and the unrecognised-item default print the same token. A "disarm" P-row on a wrong-file branch is therefore an equivalent mutant. The plan's four step-3 rows turn the refusal into acceptance instead. The design's P-row rule ("replace disarms that alternative") needs that exception.
- DESIGN D5: the `--reset` purpose guard (carry 13) is plan-added. If 5d picks OPEN-DECISION (a), D5's order of operations changes.
- DESIGN D2/D1: (i) an argv whose first word is not one of the nine modes has no D2 grammar, yet AC-5.1 says every invocation ends on a token. The plan prints usage and exits 2 with no token; this is undecided and needs a spec/design ruling. (ii) A smoke usage error with no `--data` gives `input_unparseable:` with an empty path under D1's rule as written.
- DESIGN Test Plan: it has no fixtures for the record-cycle reasons `input_missing:`, `stem_prefix:<n>` and `command_unparseable:`. The plan adds 4 tests and 4 rows. Also plan-added: test_usage_error_prints_the_mode_token, test_record_cycle_copies_stem_files_byte_for_byte, test_build_root_reset_refuses_a_non_s1_purpose and the 3 carry-2 tests.
- DESIGN: `placements(doc)` takes `sources` as a second argument in the plan (D1 requires the one parsed mapping in process).
- DESIGN rows preamble (carry 7): X3/X4's find is not in the D12 code block.
- DESIGN v1.4 change log (carry 8): it says "seven" new reset tests; the measured count is 8 distinct names. The carried re-run command prints 11 because it reads diff context lines too; the plan gives a corrected command.
- DESIGN D4 (observation): the per-document class rule dominates the totals comparison, so the totals check has no reachable fixture and no row.
- SPEC AC-1.7 (carry 10): an UNREADABLE caused by a wrong-file Effort item cannot be cleared by the "restore input, derive again" remedy.
- Observation, not decided: the exclusion list's `name-contains grok-audit-surface` does not remove `h-mad/tests/test_grok_audit_surface_*.py`, `grokauditfixtures.py` or `grok_audit_surface.json` (underscores). Their synthetic text is therefore in every export root, where it shows a reviewer that seeded-defect machinery exists. The design's D5 residual (4) "name mentions" may or may not be meant to cover this.
- Decisions I made that the orchestrator may overrule: the marker names for every guard the design does not name; the AC numbering `AC-T<n>.<m>`; the tracer reading location `$KEEP/agy-tracer/`; and making Task 12 `new-behaviour` with 0F/14P, since `gate` would stop the assembler from staging the RED.

## Placeholder scan
Clean: PRECHECK PASS issues=0. Advisories kept on purpose:
- PATH: new files, plus spec-root-relative `scripts/…` and `tests/…` keys and `tmp_path/origin.git`, all deliberate.
- COUNT L1211 "17 rows" and L1317 "0 files": the 17 refers to the table below it, and the 0 is the fixture-name zero.

No probe or scratch file remains: the registry scratch was deleted, and `git status` shows only the impl-plan as untracked.
