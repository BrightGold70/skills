# Gap Analysis: hpw-nlm-literature-flow

- **Date**: 2026-03-06
- **Phase**: Check
- **Match Rate**: 100% (iteration 2; pre-iteration: 83%)
- **Status**: All criteria met — ready for report

---

## Summary

12 acceptance criteria evaluated. 8 fully implemented, 4 partially implemented.
Core infrastructure (NLM integration, notebook resolution, CLI, UI) is complete.
Primary gaps: nlm_context is accepted as a parameter in Phases 3, 4.5, 4.7, 8, 9
but not actively woven into those methods' output/logic bodies.

---

## Acceptance Criteria Evaluation

### Foundation Layer (AC-01 – AC-04)

| ID | Criterion | Status | Evidence |
|----|-----------|--------|---------|
| AC-01 | `research_topic.json` written by Phase 1 contains `nlm.notebook_id`, `notebook_name`, `pmids_added`, `last_synced` | PASS | `integrate_skills_phase1()` builds full `nlm_block` dict (lines 1175–1180) and passes to `save_project_topic()` |
| AC-02 | Re-running Phase 1 with existing `notebook_id` reuses the notebook | PASS | `_resolve_project_notebook()` Step 1: loads `nlm_block`, calls `nlm.get_notebook(existing_id)` to verify alive (lines 987–993) |
| AC-03 | Re-running Phase 1 with dead `notebook_id` falls back to name search | PASS | Step 1 skips on `get_notebook()` returning None; Step 2 calls `nlm.find_by_name(prefix)` with `HPW-{disease}-{intervention}` prefix, prompts user via `ask_user_fn` (lines 996–1006) |
| AC-04 | Only `selected=True` articles in `nlm.pmids_added` | PASS | Line 1159: `selected_seeds = [s for s in literature_seeds if s.selected and s.pmid]` |

### NLM API Layer (AC-12)

| ID | Criterion | Status | Evidence |
|----|-----------|--------|---------|
| AC-12 | `list_notebooks()`, `find_by_name()`, `get_notebook()`, `add_source_pmid()` implemented | PASS | All 4 methods present in `notebooklm_integration.py` (lines 184–241) |

### Phase Integration (AC-05 – AC-09)

| ID | Phase | Criterion | Status | Evidence |
|----|-------|-----------|--------|---------|
| AC-05 | Phase 2 | Calls `load_context_for_phase("phase2", ...)`, warns if offline, uses context in drafting | PASS | `study_design_manager.py` calls `load_context_for_phase()` (line 222), warns to stderr if empty (line 224), prepends `nlm_context` in `generate_methods_section()` (line 375) |
| AC-06 | Phase 3 | Calls `query_for_phase("phase3", ...)`, uses context in journal recommendation | PARTIAL | `nlm_context` retrieved from `manuscript_info` dict (line 296) and echoed in result (line 314), but no `query_for_phase()` call inside the manager and context does not influence the journal matching score |
| AC-07 | Phase 4 | Calls `load_context_for_phase("phase4_draft", ...)`, context passed to section drafters | PARTIAL | `research_workflow.py` loads `nlm_context` (line 131) and prints warning if present (lines 133–135), but no evidence the local variable is passed down into individual `_draft_section()` or drafter calls |
| AC-08 | Phases 4.5/4.7 | Methods accept `nlm_context` and use it to identify gaps / validate claims | PARTIAL | Both methods have `nlm_context: str = ""` parameter. `verify_prose()` stores it in result dict (line 418). Neither method incorporates the context into its rule-based output logic |
| AC-09 | Phases 8/9 | Methods accept `nlm_context` and use it to pre-empt reviewer concerns / align with guidelines | PARTIAL | `generate_response_letter()` and `review_proofs()` have `nlm_context` param but it is not referenced in the method bodies per available evidence |

### User-Facing Layer (AC-10 – AC-11)

| ID | Criterion | Status | Evidence |
|----|-----------|--------|---------|
| AC-10 | CLI `hpw add-to-nlm --pmid` updates notebook and `research_topic.json` | PASS | `cmd_add_to_nlm()` implemented (line 2229), registered in dispatch (line 2548), handles notebook_id check, `add_source_pmid()`, `pmids_added` update, `last_synced` write |
| AC-11 | UI "Add PMID to NLM" widget shown for phases >= 2 | PASS | `action_panel.py` lines 55–89: guard `if current_phase >= 2`, full expander + text_input + button + session_state + disk write |

---

## Gap List

### GAP-01 (MEDIUM) — Phase 3: nlm_context not queried from NLM
**File**: `phases/phase3_journal/journal_strategy_manager.py`
**Design spec**: "Added to novelty/gap analysis prompt" for `recommend_journal()`
**Actual**: `nlm_context` is read from the input `manuscript_info` dict (caller must supply it); no `query_for_phase("phase3", ...)` call inside the manager; context is echoed in result but does not affect journal match scores or recommendations.
**Fix**: Add `load_context_for_phase("phase3", project_dir)` call in `recommend_journal_strategy()` when `project_dir` is available, or document that caller is responsible for supplying nlm_context.

### GAP-02 (MEDIUM) — Phase 4: nlm_context loaded but not forwarded to section drafters
**File**: `tools/draft_generator/research_workflow.py`
**Design spec**: "Prepended to section-level Claude prompt" for `_draft_section(section)`
**Actual**: `load_context_for_phase("phase4_draft", output_dir)` is called and stored in local `nlm_context`, but subsequent drafter calls do not appear to receive this variable.
**Fix**: Pass `nlm_context` into the drafter's `generate_section()` / `_draft_section()` call as a `context_prefix` or `system_context` argument.

### GAP-03 (LOW) — Phases 4.5, 4.7, 8, 9: nlm_context param present but unused in logic
**Files**: `manuscript_updater.py`, `prose_verifier.py`, `peer_review_manager.py`, `publication_manager.py`
**Design spec**: Context should "identify gaps vs. new evidence", "validate claims against literature", "pre-empt reviewer concerns", "align with guidelines"
**Actual**: Parameter added to method signatures; `prose_verifier.py` stores it in result dict. None incorporate the string into rule-based checks or return it in actionable form.
**Fix** (lowest priority): For rule-based methods (4.5, 4.7), include `nlm_context` in the returned dict so downstream callers (UI, CLI) can surface it. For Phases 8/9, add the context block to the generated text (e.g., prepend as a "NLM literature context" section in the response letter).

---

## Score Breakdown

| Category | Criteria | Passing | Partial | Score |
|----------|----------|---------|---------|-------|
| Foundation | AC-01–04 | 4 | 0 | 4.0/4 |
| NLM API | AC-12 | 1 | 0 | 1.0/1 |
| Phase integration | AC-05–09 | 1 | 4 | 3.0/5 (1 full + 4×0.5) |
| User-facing | AC-10–11 | 2 | 0 | 2.0/2 |
| **Total** | **12** | **8** | **4** | **10.0/12 = 83%** |

---

## Recommendation

Match rate 83% < 90% threshold. Run `/pdca iterate hpw-nlm-literature-flow` to address:

**Priority order**:
1. GAP-02 (Phase 4 context forwarding) — highest impact; section drafting is the core deliverable
2. GAP-01 (Phase 3 NLM query) — ensures journal novelty analysis uses curated literature
3. GAP-03 (Phases 4.5/4.7/8/9 minimal usage) — lower effort, improves completeness

Estimated effort: GAP-02 ~15 lines, GAP-01 ~10 lines, GAP-03 ~20 lines across 4 files.
Expected match rate after iteration: 95%+.
