"""
CriticalThinker — Tier 1 CSA Scientific Skill (Pre-analysis)

Flags statistical assumption risks and methodological concerns
before R scripts run. Checks PH assumption, small-n risks,
competing risks requirements, and Phase 1 design prerequisites.

Maps to: scientific-critical-thinking OpenCode skill
CSA Hook: integrate_skills_pre_analysis()
"""

from __future__ import annotations

from ._base import CSASkillBase, CSASkillContext


class CriticalThinker(CSASkillBase):
    """
    Generates assumption warnings for a CSA analysis.
    Writes results to context.assumption_warnings.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[CriticalThinker] {prompt[:200]}"
        except Exception:
            return ""

    def check_assumptions(
        self,
        disease: str,
        study_type: str = "retrospective",
        n: int = 0,
        endpoints: list | None = None,
    ) -> list:
        """
        Generate assumption warnings for the study design.

        Args:
            disease: "aml" | "cml" | "mds" | "hct"
            study_type: "retrospective" | "rct" | "phase1" | "cohort"
            n: estimated sample size
            endpoints: list of primary/secondary endpoints

        Returns:
            list[str]: Warning strings. Writes to context.assumption_warnings.
        """
        try:
            warnings: list[str] = []
            endpoints = endpoints or []
            disease = disease.lower()

            # ── Sample size warnings ──────────────────────────────────────────
            if n > 0 and n < 30:
                warnings.append(
                    f"Small sample (n={n}): use exact tests (Fisher's, Wilcoxon) "
                    "instead of asymptotic chi-squared. Power may be insufficient "
                    "for multivariable Cox regression."
                )
            if n > 0 and n < 50:
                warnings.append(
                    f"Moderate sample (n={n}): limit Cox model to ≤1 covariate "
                    "per 10 events (EPV rule). Consider penalised regression."
                )

            # ── Proportional hazards warning (all survival analyses) ──────────
            survival_eps = {"os", "efs", "pfs", "rfs", "grfs", "tfr", "dfs"}
            if any(ep.lower() in survival_eps for ep in endpoints) or disease in ("aml", "cml", "mds", "hct"):
                warnings.append(
                    "Proportional hazards assumption must be verified via cox.zph() "
                    "Schoenfeld residuals test. If violated (p<0.05), consider "
                    "time-varying coefficients or restricted mean survival time (RMST)."
                )

            # ── HCT-specific: competing risks ─────────────────────────────────
            if disease == "hct":
                warnings.append(
                    "HCT analysis: use Fine-Gray subdistribution hazard model for "
                    "GVHD and relapse endpoints — death is a competing risk. "
                    "Cause-specific Cox underestimates cumulative incidence when "
                    "competing events are frequent (NRM ~20–30%)."
                )
                warnings.append(
                    "GRFS definition: verify all four components (grade 3–4 aGVHD, "
                    "moderate-severe cGVHD, relapse, death) are captured in CRF "
                    "before running 24_hct_gvhd_analysis.R."
                )

            # ── AML-specific warnings ─────────────────────────────────────────
            if disease == "aml":
                warnings.append(
                    "AML composite response (cCR): confirm CRF captures CR, CRi, "
                    "CRh, and MLFS separately per ELN 2022 — required by "
                    "21_aml_composite_response.R."
                )
                if study_type == "phase1":
                    warnings.append(
                        "Phase 1 BOIN design: verify monotone dose-toxicity assumption "
                        "before applying BOIN (25_aml_phase1_boin.R). If assumption "
                        "is questionable, consider BLRM or EWOC as alternatives."
                    )

            # ── CML-specific warnings ─────────────────────────────────────────
            if disease == "cml":
                warnings.append(
                    "CML BCR-ABL kinetics: ensure IS (International Scale) conversion "
                    "factor is applied per lab. Mixed IS/non-IS values invalidate "
                    "milestone assessment in 22_cml_tfr_analysis.R."
                )
                warnings.append(
                    "TFR eligibility: confirm TFR patients had sustained deep MR "
                    "(MR4 or better for ≥2 years) before TKI discontinuation. "
                    "Otherwise TFR rates are not interpretable per ELN 2020."
                )

            # ── Missing data warning (all studies) ───────────────────────────
            warnings.append(
                "Missing data: document missingness rate per variable. "
                "If >10% missing on outcome, consider multiple imputation (MICE). "
                "Complete-case analysis is acceptable only if MCAR can be justified."
            )

            # ── Multiplicity warning (multiple endpoints) ─────────────────────
            if len(endpoints) > 1:
                warnings.append(
                    f"Multiple endpoints ({len(endpoints)}): pre-specify primary vs "
                    "secondary endpoints and apply multiplicity correction (Bonferroni "
                    "or Holm) for secondary analyses to control family-wise error rate."
                )

            self.context.assumption_warnings = warnings
            self._log.info(
                "CriticalThinker: generated %d warnings for %s/%s",
                len(warnings), disease, study_type
            )
            return warnings

        except Exception as exc:
            self._log.warning("CriticalThinker.check_assumptions failed: %s", exc)
            return []
