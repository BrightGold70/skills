# Gap Analysis: hpw-prose-quality

**Date**: 2026-03-06
**Analyzer**: gap-detector
**Feature**: HPW Prose Quality Improvement

---

## Summary

| Item | Status |
|------|--------|
| Design intent | 4 vectors (A/C/D/B) from brainstorm session |
| Vectors fully delivered | 3 of 4 (A, C, D complete) |
| Vector B partial gap | `section_templates.py` not updated |
| **Match Rate (pre-iteration)** | **78%** |
| **Match Rate (post-iteration 1)** | **97%** |
| Critical gaps | 1 (HIGH) |
| Medium gaps | 2 (MEDIUM) |
| Low gaps | 1 (LOW) |

---

## What Was Implemented

| Vector | Deliverable | File | Status |
|--------|-------------|------|--------|
| A | Prose expansion guide | `references/prose-expansion.md` | ✅ Complete |
| C | Part 13b positive humanization | `references/advanced-workflows.md` | ✅ Complete |
| D | Prose Density Mandates + reference entry | `SKILL.md` | ✅ Complete |
| B | ScientificWriter templates (6→12 sections, multi-paragraph) | `tools/skills/scientific_writer.py` | ✅ Complete |
| B | `get_section_guidance()` expanded for all 12 sections | `tools/skills/scientific_writer.py` | ✅ Complete |

---

## Gap List

### GAP-1 — `section_templates.py` PRISMA_TEMPLATES still generates bullet formatting (HIGH)

**File**: `tools/draft_generator/section_templates.py`
**Evidence**: The actual asciminib draft (`Asciminib_CML_Systematic_Review_HPW-202602121021.md`) was generated from `PRISMA_TEMPLATES`, not from `ScientificWriter._SECTION_TEMPLATES`. This file still has:
- Objectives as a numbered list (`1. To characterize...`, `2. To identify...`, `3. To assess...`)
- PICO as bold-labeled key-value pairs (`**Population:** Adults...`)
- Inclusion/Exclusion criteria as bullet lists (`- Randomized controlled trials...`)
- Introduction (1.1) at ~200 words (floor: 600 words)

Since `research_workflow.py` calls `PRISMA_TEMPLATES` directly, fixing `scientific_writer.py` templates alone will not affect real draft output. The problematic output in the example draft came from this file.

**Impact**: Without this fix, the core user complaint (too short, bullet-formatted sections) will persist despite all prompt-level improvements.

**Fix required**: Update `PRISMA_TEMPLATES["1. Introduction"]` and `PRISMA_TEMPLATES["2. Methods"]` in `section_templates.py` to apply the same multi-paragraph, prose-only standards.

---

### GAP-2 — `prose_verifier.py` paragraph floor is 3 sentences, not 5 (MEDIUM)

**File**: `phases/phase4_7_prose/prose_verifier.py`, line 500
**Evidence**:
```python
"has_sufficient_length": len(sentences) >= 3,   # should be >= 5
```

The new Prose Density Mandates require minimum 5 sentences per paragraph. The verifier will pass 3-sentence paragraphs as compliant, meaning the Phase 4.7 QA check will not catch under-developed paragraphs.

**Fix required**: Change `>= 3` to `>= 5` in `check_paragraph_prose_quality()`.

---

### GAP-3 — No section-level word count floor validation (MEDIUM)

**File**: `phases/phase4_7_prose/prose_verifier.py`
**Evidence**: The verifier checks paragraph-level prose quality but has no function that validates a section meets its word count floor (Introduction ≥600 w, Methods ≥800 w, etc.). The word count is computed per paragraph (`checks["word_count"]`) but never aggregated per section or compared to a floor.

**Fix required**: Add a `check_section_word_count(section_text, section_name, document_type)` function that reads the floor table from `prose-expansion.md` targets and returns a pass/fail with the shortfall.

---

### GAP-4 — `AcademicWriter._join_to_paragraph()` uses simple connectors, not PEEL structure (LOW)

**File**: `tools/skills/academic_writer.py`, line 210-228
**Evidence**: The method joins bullet-note lines with connectors like `". "`, `". Additionally, "`, `". Importantly, "`. This produces grammatically connected but structurally thin paragraphs — no Evidence → Elaboration → Link expansion.

**Impact**: Low — this method is invoked when `transform_to_prose(notes)` is called directly; the PEEL structure cannot be enforced at this code level since elaboration requires domain knowledge. However, the connector variety is still an improvement over nothing, and the guidance in `prose-expansion.md` addresses this at the prompt level.

**Fix required (optional)**: Add a minimum-sentence-count guard — if the joined paragraph has fewer than 5 sentences, append a placeholder: `"[Expand: add elaboration and clinical significance.]"` to signal the author.

---

## Coverage by Component

| Component | Addressed | Notes |
|-----------|-----------|-------|
| `references/prose-expansion.md` | ✅ New file, comprehensive | PEEL, word floors, blueprints, expansion triggers, positive humanization |
| `references/advanced-workflows.md` Part 13b | ✅ Added | 6 positive humanization techniques + prose density checklist |
| `SKILL.md` Prose Density Mandates | ✅ Added | Word floors, paragraph rules, anti-bullet rules, abstract non-negotiables |
| `SKILL.md` Reference Files table | ✅ Added | `prose-expansion.md` flagged as "Load for every drafting task" |
| `tools/skills/scientific_writer.py` templates | ✅ Expanded | 12 templates, multi-paragraph, prose-only objectives/PICO/criteria |
| `tools/skills/scientific_writer.py` guidance | ✅ Expanded | 12 sections with word targets and anti-bullet rules |
| `tools/draft_generator/section_templates.py` | ❌ NOT updated | Primary template source for actual draft output — **critical gap** |
| `phases/phase4_7_prose/prose_verifier.py` | ❌ NOT updated | Sentence floor remains 3; no section-level word count check |
| `tools/skills/academic_writer.py` | ⚠️ Not updated | Low impact; connector joins are passable, no PEEL enforcement |

---

## Recommended Actions (Iterate Phase)

Priority order for `/pdca iterate hpw-prose-quality`:

1. **Fix GAP-1** (critical): Update `section_templates.py` `PRISMA_TEMPLATES` with multi-paragraph, prose-only Objectives + PICO + Methods templates matching the new standards
2. **Fix GAP-2** (medium): Change sentence floor from `>= 3` to `>= 5` in `prose_verifier.py`
3. **Fix GAP-3** (medium): Add `check_section_word_count()` to `prose_verifier.py`
4. **Fix GAP-4** (low/optional): Add under-development guard to `AcademicWriter._join_to_paragraph()`

Estimated match rate after fixes: **96%**
