# Plan: split h-mad/SKILL.md into core + references (row 2910, first slice)

**Status:** LANDED 2026-11-02 on main (`004b33fd` + `b06eba3e` + `de75366b`), after the user approved it
2026-11-01 ("Approve as written"). Deviations from the steps below are listed under §"As built".
Measured on Hawui-Macmini; implement on the Mac Studio. Re-measure first if SKILL.md has
moved: line ranges below are as of `b5f8b7ac`.

## Goal
Cut the body that every `/h-mad` invocation loads (3,482 lines / 394 KB / ~112k tokens)
by moving the three largest sections to `h-mad/references/`, read at the step that needs
them. No behaviour change, and no test may lose what it pins.

## Measured scope (read-only, 2026-11-01, main @ b5f8b7ac)
| Section (SKILL.md lines) | Lines | Test files pinning text | Text ONLY there | Mutation rows anchored |
|---|---|---|---|---|
| Phase 5 (Implementation) sub-steps (368-1032) | 665 | 54 | 31 | spread over 11 specs, 25 rows total across the three |
| Teammate authors (1319-1881) | 563 | 25 | 8 | (incl. agy_authorship_docs 5, author_done_line 3, author_report_path 2) |
| Audit prompt assembly (2699-3004) | 306 | 37 | 16 | (incl. orchestrator_freeze_and_document 6, batch_doc_rules 3) |
| **Total moved** | **1,534 (44%)** | 85 read SKILL.md | **43 would break** | **25 rows / 11 specs** |

The 43 test files whose pinned text exists ONLY in a moved section (a literal of ≥20 chars,
found by an `ast` scan of string constants): test_docsections, test_grok_audit_surface_docs,
test_grok_fallback_docs, test_h_mad_ab_dispatch, test_h_mad_agent_definitions,
test_h_mad_agy_authorship_docs, test_h_mad_agy_review_fixes, test_h_mad_archreview_pane_halt,
test_h_mad_assemble_audit, test_h_mad_assemble_tdd, test_h_mad_audit_conditionals,
test_h_mad_audit_cycle_docs, test_h_mad_audit_gate, test_h_mad_audit_origins,
test_h_mad_audit_spec_axis, test_h_mad_batch_doc_rules, test_h_mad_codex_runtime,
test_h_mad_collect_report_docs, test_h_mad_delta_stage, test_h_mad_done_gate,
test_h_mad_gate_git_verbs, test_h_mad_identifier_sweep, test_h_mad_install_check_roots,
test_h_mad_invariants_layering, test_h_mad_mutation_harness, test_h_mad_new_caller_carveout_copies,
test_h_mad_pane_visible_dispatch_docs, test_h_mad_phase7_preconditions, test_h_mad_precheck_doc,
test_h_mad_preflight_docs, test_h_mad_prescribed_block_guards, test_h_mad_report_path_handed,
test_h_mad_review_attribution_docs, test_h_mad_tdd_dispatch_discipline_prompt,
test_h_mad_tdd_gate_docs, test_h_mad_verifier_prompt, test_h_mad_wire_registry,
test_h_mad_wiring_task_shape_docs, test_hmad_dispatch, test_hmad_dispatch_audit_cycle,
test_hmad_dispatch_exec, test_hmad_dispatch_exec_stamp, test_host_runtime_docs.
The scan misses multi-line literals and computed strings, so the full suite is the real check.

The 11 specs with rows anchored in moved sections (rows): orchestrator_freeze_and_document 6,
agy_authorship_docs 5, author_done_line 3, batch_doc_rules 3, author_report_path 2,
new_caller_carveout_copies 1, review_attribution_docs 1, delta_stage 1, grok_audit_surface 1,
wire_registry_key 1, baseline_sha 1.

Cross-references by name: 10 files cite these sections (`SKILL.md §"Audit prompt assembly"`, etc.).
Production code does not read SKILL.md text (only `h_mad_new_gate.py`'s generated-test template,
which pins the Helper scripts section, and that section stays).

## Steps
1. **Corpus helper (tests only).** Add `h-mad/tests/skill_corpus.py`:
   `skill_text()` returns SKILL.md plus every `references/*.md` that SKILL.md links by name,
   concatenated in link order. It fails loudly if a linked reference is missing. Switch the
   43 breaking files from `SKILL_MD.read_text()` to `skill_text()`. This is mechanical, one
   import per file. Files that pin ORDER or "this text is in SKILL.md specifically" are listed
   and handled one by one, never silently corpus-ified. Commit 1 changes no doc, so the suite
   must be byte-for-byte SAME.
2. **Move the sections.** Create `references/phase5-substeps.md`, `references/teammate-authors.md`
   and `references/audit-prompt-assembly.md`, each the verbatim section body. In SKILL.md each
   section becomes a 3–6 line stub: its heading (kept, so the 10 `§"…"` cross-refs still
   resolve), one sentence on when it applies, and `Read references/<x>.md before <step>.`
3. **Re-anchor the 25 mutation rows.** Change `"file"` from SKILL.md to the new reference;
   the `find` text is unchanged. Gate: `--check-anchors` ANCHORS_OK over every spec, and each of
   the 11 specs ALL_CAUGHT at its previous count.
4. **Budget pin.** `test_h_mad_skill_budget.py`: SKILL.md ≤ 260 KB (was 394), and the three
   stubs each name an existing reference. Red if a moved section is pasted back.
5. **Verify.** Full suite via `h_mad_failure_diff.py run --base main` → `SAME` (38 env failures,
   or fewer once `fix/audit-cycle-test-interpreter` lands). Then a fresh-context review
   (change-reviewer) of the diff, with the question "did any instruction the orchestrator needs
   *before* the pointer get moved behind it?"

## Risks
- **An instruction the model needs early lands behind a pointer it never follows.** Mitigation:
  each stub states its trigger step explicitly, and the reviewer checks this.
- **A corpus helper hides a real pin regression** (text deleted, still "found" in a reference).
  Mitigation: the helper only concatenates; deletion still fails. Order-sensitive pins stay
  file-specific.
- **Concurrency:** a sibling session editing SKILL.md (the hemasuite-94 peer touched grok docs).
  Do it on a branch; rebase before merge.

## Out of scope (later slices)
handoff/SKILL.md (~34k); the other 37 sections; any rewording.

## Order with in-flight work
Both prerequisite branches merged 2026-11-01 (`67b653eb`, `841a7671`), so step 5's baseline is
main at or after `841a7671`. On Hawui-Macmini that baseline is 9 environment-only failures;
the Studio's will differ, so compare failure IDs with `h_mad_failure_diff.py`, never counts.

## As built (2026-11-02, Hawk-MacStudio)
- **Step 1, the corpus helper, RECONSTRUCTS rather than concatenates.** Each reference keeps the original
  `## ` heading and, below a split-body marker line, the section body verbatim. `skill_text()` puts each
  body back in place of its stub and returns the pre-split SKILL.md byte for byte, so slice, order,
  count and `not in` pins all measure what they did before. `doc_text(path)` routes a SKILL.md path
  through it. The breaking set came from a trial split's failure-diff (128 tests in 36 files), not the
  ast scan: 3 files were outside the scan's 43, and 10 of the 43 did not break.
- **Step 2, the stubs, list every moved `###`/`####` heading and five cited bold-lead paragraphs as
  `§"…"`.** The plan assumed cross-references cited `##` headings only; many cite `###` subsections.
- **Step 3: 25 rows / 11 specs, as measured.** The reference keeps the `## ` heading so `symbol` pins
  (the nearest heading) hold. ANCHORS_OK 2740/2740. 10 specs ALL_CAUGHT. `grok_audit_surface` is
  464/465, with survivor `grok-tmp-env-ambient` identical on main (row 2936).
- **Added:** `h_mad_doc_consumers.py` gives a marker-bearing reference its SKILL.md's consumers. It had 0,
  and now has 89.
- **Review fixes:** the audit stub triggers per session, not per run. The Phase 5 opening block and its
  dispatch-channels section are read before a session's first audit dispatch. `skill_text()` fails
  closed on an unlinked or unlisted split reference. Trigger wording is pinned by phrase.
- **Verify:** `FAILDIFF: SAME`, 8,092 vs 8,073 passed, 0 failed on both sides. Next slices: row 2930.
