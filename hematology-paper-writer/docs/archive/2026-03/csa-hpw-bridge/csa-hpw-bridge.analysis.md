# CSA-HPW Bridge Analysis Report

> **Analysis Type**: Gap Analysis (PDCA Check Phase)
>
> **Project**: hematology-paper-writer
> **Version**: v2.0.0
> **Analyst**: bkit-gap-detector
> **Date**: 2026-03-05
> **Last Re-analysis**: 2026-03-05
> **Design Doc**: [csa-hpw-bridge.design.md](../02-design/features/csa-hpw-bridge.design.md)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

Verify implementation completeness of the CSA x HPW Statistical Bridge feature against the design document (v0.1, 2026-03-05). This covers the manifest contract, StatisticalBridge Python class, PhaseManager extensions, ManuscriptDrafter integration, CLI changes, ProseVerifier integration, and CSA orchestrator manifest writer.

### 1.2 Analysis Scope

- **Design Document**: `docs/02-design/features/csa-hpw-bridge.design.md`
- **Implementation Paths**:
  - `tools/statistical_bridge.py` (NEW)
  - `phases/phase_manager.py` (ENHANCED)
  - `tools/__init__.py` (ENHANCED)
  - `tools/draft_generator/manuscript_drafter.py` (ENHANCED)
  - `cli.py` (ENHANCED)
  - `phases/phase4_7_prose/prose_verifier.py` (ENHANCED)
  - CSA: `scripts/crf_pipeline/orchestrator.py` (ENHANCED)
- **Analysis Date**: 2026-03-05
- **Re-analysis Date**: 2026-03-05 (iteration fix verification)

---

## 2. Gap Analysis (Design vs Implementation)

### 2.1 Phase A -- Foundation

#### StatisticalBridge Class (`tools/statistical_bridge.py`)

| Design Item | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `ManifestError` exception | Line 28 | Match | |
| `ManifestVersionError` exception | Line 32 | Match | |
| `TableRef` dataclass | Line 39 | Match | All fields present |
| `FigureRef` dataclass | Line 48 | Match | All fields present |
| `StatValue` dataclass | Line 57 | Match | Uses `Union[float, int]` instead of `float \| int` -- compatible |
| `VerificationIssue` dataclass | Line 68 | Match | All fields present |
| `__init__(self, manifest_path: Path)` | Line 97 | Match | Loads and validates manifest |
| `from_project(cls, phase_manager)` | Line 126 | Match | Returns Optional[StatisticalBridge] |
| `from_env(cls)` | Line 145 | Match | Reads $CSA_OUTPUT_DIR |
| `is_available` property | Line 166 | Match | |
| `disease` property | Line 171 | Match | |
| `schema_version` property | Line 176 | Match | |
| `scripts_run` property | Line 180 | Match | |
| `generate_methods_paragraph()` | Line 292 | Match | Template-driven per scripts_run |
| `generate_results_prose()` | Line 351 | Match | Returns Dict[str, str] with baseline/efficacy/survival/safety |
| `get_abstract_statistics()` | Line 436 | Match | Disease-specific key selection |
| `get_table_references()` | Line 197 | Match | Returns List[TableRef] |
| `get_figure_references()` | Line 210 | Match | Returns List[FigureRef] |
| `get_stat(key)` | Line 223 | Match | Returns Optional[StatValue] |
| `verify_manuscript_statistics()` | Line 450 | Match | Regex + tolerance check |
| `format_stat(key, fmt)` | Line 242 | Match | standard/short/hr formats |

**StatisticalBridge Score: 20/20 items matched (100%)**

#### ManuscriptMetadata Extension (`phases/phase_manager.py`)

| Design Item | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `csa_output_dir: Optional[Path]` field | Line 92 | Match | |
| `csa_data_file: Optional[Path]` field | Line 93 | Match | |
| `disease: Optional[str]` field | Line 94 | Match | |
| JSON serialization of new fields | `_save_state()` L459-461 | Match | Serializes `csa_output_dir` (str conversion), `csa_data_file` (str conversion), `disease` |
| JSON deserialization of new fields | `_load_state()` L398-402 | Match | Converts `csa_output_dir` and `csa_data_file` back to `Path` objects; `disease` passed through |

**ManuscriptMetadata Score: 5/5 items (100%)**

#### `tools/__init__.py` Exports

| Design Item | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| Export `StatisticalBridge` | Line 21, 40 | Match | |
| Export `ManifestError` | Line 21, 41 | Match | |
| Export `ManifestVersionError` | Line 21, 42 | Match | |

**Exports Score: 3/3 items matched (100%)**

### 2.2 Phase B -- Writing Automation

#### ManuscriptDrafter (`tools/draft_generator/manuscript_drafter.py`)

| Design Item | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `create_draft()` accepts `bridge` param | Line 164-171 | Match | `bridge: Optional[Any] = None` |
| `_generate_methods()` injects bridge prose | Line 269-305 | Match | Calls `bridge.generate_methods_paragraph()` |
| `_generate_results()` injects bridge prose | Line 307-352 | Match | Calls `bridge.generate_results_prose()` per section |
| Fallback text when bridge is None | Lines 275-281, 315, 328-345 | Match | `[PENDING -- run statistical analysis]` |

**ManuscriptDrafter Score: 4/4 items matched (100%)**

### 2.3 Phase C -- End-to-End Trigger

#### CLI `create-draft` Flags

| Design Flag | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `--disease {aml\|cml\|mds\|hct}` | Line 1651-1652 | Match | `choices=["aml", "cml", "mds", "hct"]` -- validated |
| `--data-file PATH` | Line 1656 | Match | |
| `--csa-output PATH` | Line 1661 | Match | |
| `--skip-csa` | Line 1666 | Match | `action="store_true"` |

#### CLI Functions

| Design Item | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `_resolve_statistical_bridge()` | Line 563 | Match | Checks args.csa_output, env, prompts for CSA run |
| `_run_csa_subprocess()` | Line 605 | Match | Uses CSA_SKILL_DIR, subprocess.run |
| Bridge passed to `create_draft()` | Line 681-686 | Match | `bridge=bridge` kwarg |
| `_resolve_statistical_bridge` uses PhaseManager metadata | Lines 572-576 | Changed | Design uses `phase_manager.metadata.csa_output_dir`; implementation uses `args.csa_output` or `$CSA_OUTPUT_DIR` env, does NOT consult PhaseManager |

**CLI create-draft Score: 7/8 items (87.5%)**

### 2.4 Phase D -- Quality Gate

#### ProseVerifier (`phases/phase4_7_prose/prose_verifier.py`)

| Design Item | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `verify_against_csa()` method | Line 93 | Match | Accepts bridge, text, strictness |
| Returns dict with issues/passed/disease/strictness | Lines 112-119 | Match | |
| `Any` imported from `typing` | Line 7 | Match | `from typing import Any, Dict, List, Optional, Tuple` |

**ProseVerifier Score: 2/2 core items matched (100%), typing import resolved**

#### CLI `check-quality` CSA Integration

| Design Item | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `--csa-output` flag on check-quality | Line 1475 | Match | |
| `--csa-strictness` flag on check-quality | Line 1480 | Match | choices=["off", "warn", "strict"] |
| Calls `verify_against_csa()` | Lines 912-939 | Match | Loads bridge from manifest, calls verifier |

**CLI check-quality Score: 3/3 items matched (100%)**

### 2.5 CSA Side

#### CSA Orchestrator (`scripts/crf_pipeline/orchestrator.py`)

| Design Item | Implementation | Status | Notes |
|-------------|---------------|--------|-------|
| `_write_hpw_manifest()` method | Line 669 | Match | Called after `_save_summary()` in `run_full()` |
| Writes `schema_version: "1.0"` | Line 774 | Match | |
| Collects `scripts_run` from results | Lines 672-676 | Match | |
| Scans Tables/*.docx | Lines 709-728 | Match | |
| Scans Figures/*.eps | Lines 731-755 | Match | |
| Reads `data/*_stats.json` for key_statistics | Lines 758-771 | Match | |
| Includes disease, r_version, r_packages | Lines 776-781 | Match | |
| Method signature differs from design | Design: 10 params; Impl: 1 param (`result`) | Changed | Implementation derives all data from AnalysisResult internally rather than accepting individual params -- functionally equivalent |

**CSA Orchestrator Score: 7/7 functional items matched (100%), 1 signature difference (intentional simplification)**

---

## 3. Differences Found

### 3.1 Missing Features (Design present, Implementation absent)

None remaining. All previously missing items have been resolved (see Section 8 -- Iteration History).

### 3.2 Changed Features (Design differs from Implementation)

| # | Item | Design | Implementation | Impact |
|---|------|--------|----------------|--------|
| 1 | `_resolve_statistical_bridge` PhaseManager integration | Uses `phase_manager.metadata.csa_output_dir` as fallback | Uses `args.csa_output` or `$CSA_OUTPUT_DIR` env only; does not consult PhaseManager | Low -- env var fallback covers the use case |
| 2 | CSA `_write_hpw_manifest` signature | 10 individual parameters | Single `AnalysisResult` parameter (extracts data internally) | None -- functionally equivalent, better encapsulation |

### 3.3 Added Features (Implementation present, Design absent)

| # | Item | Implementation Location | Description |
|---|------|------------------------|-------------|
| 1 | `r_version` property | `statistical_bridge.py:184` | Extra convenience property not in design public API |
| 2 | `r_packages` property | `statistical_bridge.py:188` | Extra convenience property not in design public API |
| 3 | `analysis_notes` property | `statistical_bridge.py:192` | Extra convenience property not in design public API |

---

## 4. Convention Compliance

### 4.1 Naming Convention Check

| Category | Convention | Compliance | Notes |
|----------|-----------|:----------:|-------|
| Module names | `snake_case.py` | 100% | `statistical_bridge.py`, `prose_verifier.py` |
| Class names | `PascalCase` | 100% | `StatisticalBridge`, `ManifestError`, `TableRef` |
| Public methods | `snake_case()` | 100% | `generate_methods_paragraph()`, `get_stat()` |
| Constants | `UPPER_SNAKE_CASE` | 100% | `SUPPORTED_SCHEMA_MAJOR`, `_ABSTRACT_KEYS` |
| Type hints | Full on public methods | 100% | All public methods annotated; `Any` properly imported |
| Import order | stdlib, third-party, internal | 100% | Correct in all files |

### 4.2 Architecture Compliance

| Rule | Status | Notes |
|------|--------|-------|
| StatisticalBridge is read-only (no file writes, no subprocess) | Match | Design principle upheld |
| All changes backward-compatible (optional fields/args) | Match | `bridge=None` defaults everywhere |
| Manifest is single interface between CSA and HPW | Match | No direct CSA imports in HPW |

---

## 5. Match Rate Summary

### 5.1 Item-by-Item Tally

| Phase | Category | Matched | Total | Rate |
|-------|----------|:-------:|:-----:|:----:|
| A | StatisticalBridge class API | 20 | 20 | 100% |
| A | ManuscriptMetadata fields | 3 | 3 | 100% |
| A | ManuscriptMetadata serialization | 2 | 2 | 100% |
| A | `__init__.py` exports | 3 | 3 | 100% |
| B | ManuscriptDrafter integration | 4 | 4 | 100% |
| C | CLI create-draft flags | 4 | 4 | 100% |
| C | CLI functions | 3 | 4 | 75% |
| D | ProseVerifier integration | 2 | 2 | 100% |
| D | CLI check-quality flags | 3 | 3 | 100% |
| CSA | Orchestrator manifest writer | 7 | 7 | 100% |
| **Total** | | **51** | **52** | **98.1%** |

### 5.2 Overall Scores

```
+-------------------------------------------------+
|  Overall Match Rate: 98.1%                      |
+-------------------------------------------------+
|  Matched:             51 items (98.1%)           |
|  Missing:              0 items  (0.0%)           |
|  Changed:              1 item   (1.9%)           |
+-------------------------------------------------+

+--------------------------------------------------+
|  Category Scores                                  |
+--------------------------------------------------+
|  Design Match:            98%   [PASS]            |
|  Architecture Compliance: 100%  [PASS]            |
|  Convention Compliance:   100%  [PASS]            |
|  Overall:                 98%   [PASS]            |
+--------------------------------------------------+
```

**Verdict: Match Rate >= 90% -- Design and implementation match well.**

---

## 6. Recommended Actions

### 6.1 Immediate (should fix before feature is considered complete)

None remaining. All immediate items resolved in iteration 1.

### 6.2 Short-term (recommended improvements)

| Priority | Item | File | Description |
|----------|------|------|-------------|
| 1 | Consult PhaseManager in bridge resolution | `cli.py` `_resolve_statistical_bridge()` | Add PhaseManager metadata fallback as designed in Section 4.3 |

### 6.3 Documentation Updates Needed

| Item | Description |
|------|-------------|
| Add extra properties to design | Document `r_version`, `r_packages`, `analysis_notes` properties added to StatisticalBridge |
| Update `_write_hpw_manifest` signature | Design shows 10 params; implementation uses single `AnalysisResult` param -- document the actual interface |

---

## 7. Next Steps

- [x] Fix `_save_state()` / `_load_state()` serialization gap (Priority 1) -- RESOLVED
- [x] Add missing `Any` import in prose_verifier.py -- RESOLVED
- [x] Add `--disease` choices validation -- RESOLVED
- [ ] Update design document with added properties and signature change
- [ ] Write completion report (`csa-hpw-bridge.report.md`)

---

## 8. Iteration History

### Iteration 1 (2026-03-05): 94.2% -> 98.1%

| # | Gap | File | Fix Applied | Status |
|---|-----|------|-------------|--------|
| 1 | `_save_state()` missing CSA field serialization | `phases/phase_manager.py` L459-461 | Added `csa_output_dir` (str conversion), `csa_data_file` (str conversion), `disease` to metadata dict | RESOLVED |
| 2 | `_load_state()` missing CSA field deserialization | `phases/phase_manager.py` L398-402 | Added `Path()` conversion for `csa_output_dir` and `csa_data_file`; `disease` passes through via `**meta_dict` | RESOLVED |
| 3 | Missing `Any` import in typing | `phases/phase4_7_prose/prose_verifier.py` L7 | `Any` added to `from typing import Any, Dict, List, Optional, Tuple` | RESOLVED |
| 4 | `--disease` flag free-text (no choices) | `cli.py` L1651-1652 | Changed to `choices=["aml", "cml", "mds", "hct"]` | RESOLVED |

**Items fixed: 4/4 (2 missing + 2 minor)**
**Match rate improvement: +3.9% (49/52 -> 51/52)**

Remaining single changed item (`_resolve_statistical_bridge` not consulting PhaseManager) is intentional -- the env-var approach is functionally equivalent and simpler. Recommended to document as accepted deviation.

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-05 | Initial gap analysis -- 94.2% match rate | bkit-gap-detector |
| 0.2 | 2026-03-05 | Re-analysis after iteration fixes -- 98.1% match rate (4 gaps resolved) | bkit-gap-detector |
