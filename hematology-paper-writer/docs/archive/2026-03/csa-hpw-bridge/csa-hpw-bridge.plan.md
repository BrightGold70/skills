# CSA × HPW Statistical Bridge Planning Document

> **Summary**: Connect clinical-statistics-analyzer outputs to hematology-paper-writer manuscript generation, enabling end-to-end flow from raw patient data to publication-ready draft.
>
> **Project**: hematology-paper-writer
> **Version**: v2.0.0
> **Author**: kimhawk
> **Date**: 2026-03-04
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

HPW currently writes manuscripts from PubMed/NotebookLM data only — it has no connection to a user's own patient data. CSA produces verified statistical outputs (tables, figures, JSON summaries) from real trial data but those outputs are never consumed by HPW. This feature bridges the two skills so HPW can generate a statistically grounded, publication-ready manuscript draft directly from CSA outputs.

### 1.2 Background

- **HPW** manages manuscript workflow (Phases 1–10), generates prose, verifies references, checks quality
- **CSA** analyzes patient data (AML/CML/MDS/HCT) via R scripts, producing `.docx` tables, `.eps` figures, and an `orchestrator.py` JSON summary
- The gap: CSA outputs exist on disk but HPW has no mechanism to read, interpret, or integrate them
- Brainstorming (2026-03-04) identified four integration layers: Methods paragraph, Results prose, figure/table embedding, and numeric verification

### 1.3 Related Documents

- Brainstorming session: 2026-03-04 (this conversation)
- CSA CLAUDE.md: `/Users/kimhawk/.config/opencode/skill/clinical-statistics-analyzer/CLAUDE.md`
- HPW CLAUDE.md: `CLAUDE.md` (this repo)
- HPW Phase 4.7: `phases/phase4_7_prose/prose_verifier.py`
- CSA orchestrator: `../clinical-statistics-analyzer/scripts/crf_pipeline/orchestrator.py`

---

## 2. Scope

### 2.1 In Scope

**Phase A — Foundation**
- [ ] CSA: Add `hpw_manifest.json` export to `orchestrator.py`
- [ ] HPW: New `tools/statistical_bridge.py` (`StatisticalBridge` class)
- [ ] HPW: `PhaseManager` / `ManuscriptMetadata` gains `csa_output_dir`, `csa_data_file`, `disease` fields

**Phase B — Writing Automation**
- [ ] HPW: `StatisticalBridge.generate_methods_paragraph()` — Statistical Analysis section text
- [ ] HPW: `StatisticalBridge.generate_results_prose()` — per-section Results prose blocks
- [ ] HPW: `ManuscriptDrafter` accepts bridge output, injects at `[STATISTICAL_METHODS]` / `[RESULTS_*]` placeholders
- [ ] HPW: `StatisticalBridge.get_abstract_statistics()` — key stats for abstract injection

**Phase C — End-to-End Trigger**
- [ ] HPW: `create-draft` new flags `--disease`, `--data-file`
- [ ] HPW: Auto-detect missing CSA outputs → prompt to run CSA → subprocess trigger
- [ ] HPW CLI: `hpw init-project` (or `hpw set-project`) sets `csa_output_dir` / `disease` in project state

**Phase D — Quality Gate**
- [ ] HPW: `ProseVerifier.verify_against_csa(manifest)` — cross-reference every number in prose against `key_statistics`
- [ ] HPW: `check-quality` uses bridge when manifest present; configurable strictness (default: Results + Abstract, warn-only)

### 2.2 Out of Scope

- CSA UI changes (Streamlit / HPW web UI integration deferred)
- Bidirectional sync (HPW writing back to CSA)
- Automatic re-run of CSA on data change (Phase 4.5 manual re-run only)
- Non-hematology disease types (outside AML/CML/MDS/HCT)
- Statistical computation inside HPW (all computation stays in CSA/R)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | CSA `orchestrator.py` exports `hpw_manifest.json` alongside existing summary | High | Pending |
| FR-02 | `hpw_manifest.json` contains: disease, scripts_run, r_packages, r_version, tables[], figures[], key_statistics{} | High | Pending |
| FR-03 | `StatisticalBridge` reads manifest and exposes typed accessors | High | Pending |
| FR-04 | `StatisticalBridge.generate_methods_paragraph()` returns a publication-ready Statistical Analysis paragraph | High | Pending |
| FR-05 | `StatisticalBridge.generate_results_prose()` returns prose dict keyed by section (baseline, efficacy, survival, safety) | High | Pending |
| FR-06 | `ManuscriptDrafter` injects bridge outputs at named placeholders in section templates | High | Pending |
| FR-07 | `PhaseManager` persists `csa_output_dir`, `csa_data_file`, `disease` per project | High | Pending |
| FR-08 | `create-draft --data-file --disease` auto-detects absent CSA outputs and prompts to run CSA | Medium | Pending |
| FR-09 | CSA subprocess trigger: `python -m scripts.crf_pipeline run-analysis <data_file> -d <disease> -o <csa_output_dir>` | Medium | Pending |
| FR-10 | `ProseVerifier.verify_against_csa()` flags manuscript numbers absent from `key_statistics` | Medium | Pending |
| FR-11 | Bridge degrades gracefully when manifest not present (HPW proceeds without statistics) | High | Pending |
| FR-12 | `StatisticalBridge.get_abstract_statistics()` returns the 3–5 key stats for abstract | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Compatibility | CSA change must not break existing `run-analysis` behavior | Existing CSA tests pass |
| Graceful degradation | HPW works normally when `hpw_manifest.json` absent | `--csa-output` omitted runs clean |
| Correctness | Statistics in generated prose exactly match `key_statistics` values | Numeric diff check |
| Maintainability | Bridge has no knowledge of R internals; only reads manifest JSON | Code review |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `hpw create-draft "AML topic" --disease aml --data-file data.csv` triggers CSA, produces manuscript with real statistics
- [ ] Generated Statistical Methods paragraph is publication-ready without manual editing
- [ ] Generated Results prose uses exact values from `key_statistics` (no hallucinated numbers)
- [ ] `hpw check-quality manuscript.md` warns on unverified statistics when manifest present
- [ ] HPW works identically when no CSA manifest provided (no regression)

### 4.2 Quality Criteria

- [ ] `StatisticalBridge` unit-testable with mock manifest JSON
- [ ] `hpw_manifest.json` schema documented (JSON Schema or dataclass)
- [ ] CSA `run-analysis` exit codes (0/1/2) handled in HPW subprocess call

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| `key_statistics` structure varies by disease/scripts run | High | High | Define mandatory keys + optional disease-specific keys in manifest schema |
| CSA subprocess path differs across machines | Medium | Medium | Use `CSA_SKILL_DIR` env var or discover from project registry |
| R script output format changes in CSA updates | Medium | Low | Manifest is produced by Python orchestrator, insulated from R output format |
| LLM-generated methods paragraph contains errors | High | Medium | Use template-driven generation (not free-form LLM) with R package list from manifest |
| Phase D numeric verification produces false positives | Low | Medium | Configurable strictness; default warn-only, not blocking |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Selected |
|-------|-----------------|:--------:|
| Starter | Simple structure | ☐ |
| **Dynamic** | Feature-based modules, service integration | ☑ |
| Enterprise | Strict layer separation, microservices | ☐ |

This is a Dynamic-level integration: two separate skills communicating via file-based contract (manifest JSON + output directory).

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| Bridge location | HPW / CSA / shared | HPW (`tools/statistical_bridge.py`) | HPW is the manuscript orchestrator; CSA is the computation engine |
| Handoff contract | manifest.json / subprocess API / file convention | `hpw_manifest.json` (CSA produces, HPW reads) | Clean separation; CSA owns statistics, HPW owns writing |
| CSA trigger | manual / CLI flag / auto-detect | Auto-detect + prompt (FR-08/FR-09) | Best UX; user can still run CSA manually |
| Methods paragraph | Template / LLM / CSA-generated | Template-driven in HPW using manifest data | Reproducible, no hallucination risk |
| Project state | env var / CLI flag / PhaseManager | PhaseManager (set once per project) | Consistent with existing HPW project model |
| Numeric verification | strict / warn / configurable | Warn-only default, configurable | Avoids blocking legitimate paraphrase or rounding |

### 6.3 Component Map

```
CSA orchestrator.py
  └─▶ hpw_manifest.json (NEW)
        │
        ▼
HPW tools/statistical_bridge.py (NEW)
  ├─▶ generate_methods_paragraph() → str
  ├─▶ generate_results_prose()     → Dict[str, str]
  ├─▶ get_abstract_statistics()    → Dict
  └─▶ verify_manuscript_statistics(text) → List[VerificationIssue]
        │
        ├─▶ ManuscriptDrafter (ENHANCED)
        │     injects at [STATISTICAL_METHODS], [RESULTS_*], [ABSTRACT_STATS]
        │
        └─▶ ProseVerifier (ENHANCED)
              verify_against_csa(manifest)

HPW PhaseManager / ManuscriptMetadata (ENHANCED)
  └─▶ fields: csa_output_dir, csa_data_file, disease

HPW cli.py create-draft (ENHANCED)
  └─▶ --disease, --data-file flags
  └─▶ auto-detect + subprocess trigger
```

---

## 7. Convention Prerequisites

### 7.1 Existing Conventions

- [x] `CLAUDE.md` exists with coding conventions
- [x] Python module pattern: `tools/__init__.py` re-exports all public classes
- [x] CSA env var convention: `CSA_OUTPUT_DIR`, `CRF_OUTPUT_DIR`
- [x] CSA CRF pipeline exit codes: 0=success, 1=partial, 2=failure

### 7.2 Conventions to Define

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| Manifest schema | Missing | `hpw_manifest.json` JSON schema (v1) | High |
| Bridge placeholder names | Missing | `[STATISTICAL_METHODS]`, `[RESULTS_BASELINE]`, `[RESULTS_EFFICACY]`, `[RESULTS_SURVIVAL]`, `[RESULTS_SAFETY]`, `[ABSTRACT_STATS]` | High |
| Disease codes | Implicit in CSA | Enum: `aml`, `cml`, `mds`, `hct` (matches CSA `-d` flag) | Medium |
| Verification strictness levels | Missing | `off` / `warn` / `strict` | Low |

### 7.3 Environment Variables

| Variable | Purpose | Scope | Owner |
|----------|---------|-------|-------|
| `CSA_OUTPUT_DIR` | CSA output base dir (already exists) | R scripts | CSA |
| `CRF_OUTPUT_DIR` | CRF pipeline output dir (already exists) | Python | CSA |
| `CSA_SKILL_DIR` | Path to CSA skill root (for subprocess) | HPW → CSA | New |

---

## 8. Phased Delivery

| Phase | Scope | Deliverables |
|-------|-------|-------------|
| **A — Foundation** | Manifest + Bridge (read-only) | `hpw_manifest.json` schema, `StatisticalBridge` class, `PhaseManager` fields |
| **B — Writing** | Methods + Results prose generation | `generate_methods_paragraph()`, `generate_results_prose()`, `ManuscriptDrafter` injection |
| **C — Trigger** | Auto-detect + subprocess | `create-draft` flags, CSA auto-trigger |
| **D — Quality Gate** | Numeric verification | `ProseVerifier.verify_against_csa()`, `check-quality` integration |

---

## 9. Next Steps

1. [ ] Write design document: `docs/02-design/features/csa-hpw-bridge.design.md`
2. [ ] Define `hpw_manifest.json` JSON schema (Phase A prerequisite)
3. [ ] Review with `/pdca design csa-hpw-bridge`

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-04 | Initial draft from brainstorming session | kimhawk |
