# Plan: csa-scientific-skills-integration

## Overview

Integrate scientific skills (from `K-Dense-AI/claude-scientific-skills`) into the
Clinical Statistics Analyzer (CSA) skill, mirroring the pattern established by
`hpw-scientific-skills-integration` in the Hematology Paper Writer.

## Problem Statement

1. `key_statistics` in `hpw_manifest.json` is always empty — R scripts never write
   `data/*_stats.json` sidecars, so `StatisticalBridge.get_stat()` returns `None` for
   every key, silencing all NLM enrichment in HPW prose.
2. CSA has no pre-analysis intelligence layer — no hypothesis formulation, no statistical
   assumption validation before R scripts run.
3. CSA produces no Methods prose — the link between "what R scripts ran" and "how to
   write the Methods section" is manual.

## Goals

1. **Fix `key_statistics` gap**: `ROutputInterpreter` reads R-generated CSV outputs
   post-run → writes `data/*_stats.json` → existing `_write_hpw_manifest()` logic
   picks them up automatically (zero orchestrator modification).
2. **Pre-analysis intelligence**: `HypothesisGenerator` + `StatisticalAnalyst` +
   `CriticalThinker` run before R scripts to formulate hypotheses, validate methods,
   and flag assumption risks.
3. **Post-analysis enrichment**: `ScientificWriter` generates Methods prose;
   `ELNGuidelineMapper` maps results to ELN 2022/2020/NIH 2014 categories;
   `ProtocolConsistencyChecker` validates outputs against protocol endpoints.
4. **CLI commands**: `csa hypothesis`, `csa analyze-plan`, `csa interpret-results`,
   `csa draft-methods`, `csa review-assumptions`.

## Decisions (Resolved)

| Question | Decision |
|----------|----------|
| Shared `_base.py` with HPW? | **No** — separate CSA `_base.py` with `CSASkillContext` |
| Context storage location | `scripts/crf_pipeline/skills/` (inside crf_pipeline package) |
| Scope | **Full** — all Tier 1 + Tier 2 skills (8 classes) |
| HPW bridge awareness | **Yes** — `key_statistics` dict keys must match `StatValue` schema |

## Architecture

```
scripts/crf_pipeline/
  skills/
    _base.py                     # CSASkillBase + CSASkillContext (separate from HPW)
    statistical_analyst.py       # Method validation + R-specific mappings (Tier 1)
    hypothesis_generator.py      # Disease-specific null/alternative hypotheses (Tier 1)
    critical_thinker.py          # PH assumption checks, missing data flagging (Tier 1)
    scientific_writer.py         # Methods prose from analysis plan (Tier 1)
    content_researcher.py        # Links R outputs to guideline citations (Tier 1)
    r_output_interpreter.py      # Reads R CSVs → writes *_stats.json (Tier 2, KEY)
    eln_guideline_mapper.py      # Maps results to ELN 2022/2020/NIH 2014 (Tier 2)
    protocol_consistency.py      # Validates outputs vs protocol endpoints (Tier 2)
    __init__.py
  skills_integration.py          # integrate_skills_pre_analysis() / post_analysis()
```

## CSASkillContext Schema

```python
@dataclass
class CSASkillContext:
    study_name: str
    disease: str            # aml | cml | mds | hct

    # Pre-analysis (written before R scripts run)
    hypotheses: list        # list[str]
    statistical_plan: dict  # {methods, assumptions, software, reporting_guideline}
    assumption_warnings: list  # list[str]

    # Post-analysis (written by ROutputInterpreter — fixes key_statistics gap)
    key_statistics: dict    # {stat_key: {"value": float, "ci_lower", "ci_upper", "p_value"}}
    interpretation_notes: list  # list[str]
    methods_prose: str

    # Tracking
    scripts_run: list
```

Persisted to: `{output_dir}/data/{study_name}.csa_skills_context.json`

## key_statistics Schema (HPW-compatible)

All entries must match `StatValue` shape consumed by `StatisticalBridge.get_stat()`:

```json
{
  "n_total":        {"value": 120},
  "AML_cr_rate":    {"value": 0.68, "ci_lower": 0.58, "ci_upper": 0.77},
  "AML_os_median":  {"value": 18.4, "ci_lower": 14.2, "ci_upper": 22.1, "p_value": 0.003},
  "CML_mmr_rate":   {"value": 0.72, "ci_lower": 0.61, "ci_upper": 0.81},
  "HCT_grfs_1yr":   {"value": 0.54, "ci_lower": 0.44, "ci_upper": 0.63}
}
```

## Integration Hook (zero-modification to existing code)

```python
# skills_integration.py — appended, never modifies existing orchestrator

def integrate_skills_post_analysis(result: AnalysisResult, output_dir: Path, disease: str) -> None:
    """Writes *_stats.json sidecars; _write_hpw_manifest() picks them up automatically."""
    try:
        from .skills import ROutputInterpreter, ELNGuidelineMapper, ScientificWriter
        ctx = CSASkillContext.load(disease, output_dir)
        ctx = ROutputInterpreter(ctx).interpret(output_dir)   # → data/*_stats.json
        ctx = ELNGuidelineMapper(ctx).map(output_dir)
        ctx = ScientificWriter(ctx).draft_methods()
        ctx.save(output_dir)
    except Exception:
        pass  # fail-silent — skills never break the pipeline
```

Called from `AnalysisOrchestrator.run()` as optional post-hook (appended to end of run()).

## CLI Commands

```bash
python -m scripts.crf_pipeline hypothesis --disease aml --endpoint "CR_rate"
python -m scripts.crf_pipeline analyze-plan --data data.csv --disease cml
python -m scripts.crf_pipeline interpret-results --output-dir /path --disease aml
python -m scripts.crf_pipeline draft-methods --study-name STUDY --disease hct
python -m scripts.crf_pipeline review-assumptions --data data.csv --disease mds
```

## R CSV Sources for ROutputInterpreter

| R Script | CSV Output | Key Statistics to Extract |
|----------|-----------|--------------------------|
| `04_survival.R` | `Cox_*_Analysis.csv` | HR, CI, p-value for OS/PFS/EFS |
| `04_survival.R` | `FineGray_*.csv` | SHR, CI, p-value for competing risks |
| `21_aml_composite_response.R` | (embedded in docx) | CR rate, CRi rate, cCR |
| `22_cml_tfr_analysis.R` | `CML_TFR_Cox_Model.docx` | TFR rate, HR |
| `24_hct_gvhd_analysis.R` | `HCT_Outcomes_Summary.docx` | aGVHD/cGVHD CI, GRFS |
| `10_sample_size.R` | `SampleSize_*.csv` | n_total, power, alpha |

## Skills from claude-scientific-skills Catalog

| CSA Skill Class | Maps to OpenCode skill | Phase |
|----------------|----------------------|-------|
| `StatisticalAnalyst` | `statistical-analysis` | Pre |
| `HypothesisGenerator` | `hypothesis-generation` | Pre |
| `CriticalThinker` | `scientific-critical-thinking` | Pre |
| `ScientificWriter` | `scientific-writing` | Post |
| `ContentResearcher` | `literature-review` | Post |
| `ROutputInterpreter` | `exploratory-data-analysis` | Post (KEY) |
| `ELNGuidelineMapper` | `clinical-decision-support` | Post |
| `ProtocolConsistencyChecker` | `scientific-critical-thinking` | Post |

## Implementation Order

1. `scripts/crf_pipeline/skills/_base.py` — CSASkillBase + CSASkillContext
2. `r_output_interpreter.py` — highest priority (fixes key_statistics gap)
3. `statistical_analyst.py` + `hypothesis_generator.py` + `critical_thinker.py` — pre-analysis
4. `scientific_writer.py` + `content_researcher.py` — post-analysis prose
5. `eln_guideline_mapper.py` + `protocol_consistency.py` — CSA-specific
6. `skills/__init__.py` — re-exports
7. `skills_integration.py` — hook functions
8. `cli.py` additions — 5 new subcommands
9. Tests: `tests/test_skills_integration.py`

## Success Criteria

- [ ] `key_statistics` in `hpw_manifest.json` non-empty after analysis run with R CSV outputs
- [ ] `StatisticalBridge.get_stat("AML_os_median")` returns `StatValue` (not None)
- [ ] Pre-analysis skills produce `hypotheses` + `statistical_plan` in CSASkillContext
- [ ] `methods_prose` non-empty string in CSASkillContext after post-analysis
- [ ] All 5 CLI subcommands functional
- [ ] Existing CSA tests still pass (skills fail-silent, no regressions)
- [ ] `tests/test_skills_integration.py` ≥ 40 tests pass

## Out of Scope

- Modifying R scripts to write JSON sidecars themselves
- Shared `SkillBase`/`SkillContext` with HPW
- UI/Streamlit integration
- Automatic R script re-running based on skill recommendations
