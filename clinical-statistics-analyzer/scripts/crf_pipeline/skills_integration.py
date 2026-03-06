"""
CSA Scientific Skills Integration Hooks

Provides two standalone functions called from AnalysisOrchestrator.run():
  - integrate_skills_pre_analysis(): before R scripts run
  - integrate_skills_post_analysis(): after R scripts complete

Both functions are fail-silent — they never raise, ensuring skills
cannot break the core analysis pipeline.

Pattern mirrors HPW's integrate_skills_phaseN() approach:
  - Additive only — no modification of existing orchestrator logic
  - Context persisted to {output_dir}/data/{study_name}.csa_skills_context.json
  - Sidecar JSON written to {output_dir}/data/*_stats.json for hpw_manifest
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .orchestrator import AnalysisResult

logger = logging.getLogger(__name__)


def integrate_skills_pre_analysis(
    study_name: str,
    disease: str,
    output_dir: Path,
    study_type: str = "retrospective",
    primary_endpoint: str = "",
    n_estimated: int = 0,
    endpoints: list | None = None,
    treatment: str = "the study treatment",
    comparator: str = "standard of care",
) -> "object":
    """
    Run pre-analysis skills before R scripts execute.

    Skills called (in order, all fail-silent):
      1. HypothesisGenerator  → context.hypotheses
      2. StatisticalAnalyst   → context.statistical_plan
      3. CriticalThinker      → context.assumption_warnings

    Args:
        study_name: Identifier for this analysis run (used for context file naming)
        disease: "aml" | "cml" | "mds" | "hct"
        output_dir: CSA output directory (context persisted here)
        study_type: "retrospective" | "rct" | "phase1" | "cohort"
        primary_endpoint: e.g. "OS", "CR rate", "TFR"
        n_estimated: estimated sample size (0 if unknown)
        endpoints: list of all endpoints (for multiplicity warning)
        treatment: treatment name for hypothesis templates
        comparator: comparator arm for hypothesis templates

    Returns:
        CSASkillContext (populated). Returns empty context on any failure.
    """
    try:
        from .skills import (
            CSASkillContext,
            HypothesisGenerator,
            StatisticalAnalyst,
            CriticalThinker,
        )

        output_dir = Path(output_dir)
        ctx = CSASkillContext.load(study_name, output_dir)
        ctx.disease = disease

        # 1. Hypothesis generation
        try:
            HypothesisGenerator(context=ctx).generate(
                disease=disease,
                treatment=treatment,
                endpoint=primary_endpoint,
                comparator=comparator,
            )
        except Exception as exc:
            logger.debug("HypothesisGenerator skipped: %s", exc)

        # 2. Statistical plan
        try:
            StatisticalAnalyst(context=ctx).analyze(
                disease=disease,
                primary_endpoint=primary_endpoint,
                study_type=study_type,
                n=n_estimated,
            )
        except Exception as exc:
            logger.debug("StatisticalAnalyst skipped: %s", exc)

        # 3. Assumption checks
        try:
            CriticalThinker(context=ctx).check_assumptions(
                disease=disease,
                study_type=study_type,
                n=n_estimated,
                endpoints=endpoints or ([primary_endpoint] if primary_endpoint else []),
            )
        except Exception as exc:
            logger.debug("CriticalThinker skipped: %s", exc)

        ctx.save(output_dir)
        logger.info(
            "skills_integration: pre-analysis complete — %d hypotheses, %d warnings",
            len(ctx.hypotheses), len(ctx.assumption_warnings),
        )
        return ctx

    except Exception as exc:
        logger.debug("integrate_skills_pre_analysis failed silently: %s", exc)
        try:
            from .skills import CSASkillContext
            return CSASkillContext(study_name=study_name, disease=disease)
        except Exception:
            return None  # type: ignore[return-value]


def integrate_skills_post_analysis(
    result: "AnalysisResult",
    output_dir: Path,
    study_name: str,
) -> None:
    """
    Run post-analysis skills after R scripts complete.

    Skills called (in order, all fail-silent):
      1. ROutputInterpreter       → reads R CSVs/DOCX → writes data/*_stats.json
      2. ELNGuidelineMapper       → annotates key_statistics with ELN/NIH labels
      3. ScientificWriter         → drafts Methods prose
      4. ProtocolConsistencyChecker → validates vs protocol endpoints
      5. ContentResearcher        → links stats to guideline citations

    The *_stats.json sidecars written by ROutputInterpreter are consumed
    automatically by _write_hpw_manifest() — zero orchestrator modification.

    Args:
        result: AnalysisResult from AnalysisOrchestrator.run()
        output_dir: CSA output directory
        study_name: Identifier for context file
    """
    try:
        from .skills import (
            CSASkillContext,
            ROutputInterpreter,
            ELNGuidelineMapper,
            ScientificWriter,
            ProtocolConsistencyChecker,
            ContentResearcher,
        )

        output_dir = Path(output_dir)
        disease = getattr(result, "disease", "unknown") or "unknown"
        ctx = CSASkillContext.load(study_name, output_dir)
        ctx.disease = disease
        ctx.scripts_run = [
            sr.script for sr in getattr(result, "script_results", [])
            if getattr(sr, "success", False)
        ]

        # 1. Extract key_statistics from R outputs → writes *_stats.json sidecars
        try:
            ROutputInterpreter(context=ctx).interpret(output_dir)
        except Exception as exc:
            logger.debug("ROutputInterpreter skipped: %s", exc)

        # 2. Annotate with ELN/NIH guideline labels
        try:
            ELNGuidelineMapper(context=ctx).map(output_dir)
        except Exception as exc:
            logger.debug("ELNGuidelineMapper skipped: %s", exc)

        # 3. Draft Methods prose (requires statistical_plan from pre-analysis)
        try:
            if not ctx.statistical_plan:
                # Fallback: generate minimal plan for writer
                from .skills import StatisticalAnalyst
                StatisticalAnalyst(context=ctx).analyze(disease=disease)
            ScientificWriter(context=ctx).draft_methods()
        except Exception as exc:
            logger.debug("ScientificWriter skipped: %s", exc)

        # 4. Protocol consistency check
        try:
            ProtocolConsistencyChecker(context=ctx).check(output_dir=output_dir)
        except Exception as exc:
            logger.debug("ProtocolConsistencyChecker skipped: %s", exc)

        # 5. Guideline citations
        try:
            ContentResearcher(context=ctx).find_citations()
        except Exception as exc:
            logger.debug("ContentResearcher skipped: %s", exc)

        ctx.save(output_dir)
        logger.info(
            "skills_integration: post-analysis complete — %d key_statistics, "
            "%d protocol_gaps, methods_prose=%d chars",
            len(ctx.key_statistics),
            len(ctx.protocol_gaps),
            len(ctx.methods_prose),
        )

    except Exception as exc:
        logger.debug("integrate_skills_post_analysis failed silently: %s", exc)
