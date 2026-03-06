"""
StatisticalAnalyst — Scientific Skills Integration
Maps to: statistical-analysis OpenCode skill
HPW Phases: 2 (Research Design), 4 (Manuscript Prep), 5 (Quality)
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

# Statistical method recommendations by study design
_DESIGN_METHODS: dict[str, dict] = {
    "rct": {
        "primary": ["Intention-to-treat analysis", "ANCOVA for continuous endpoints"],
        "survival": ["Kaplan-Meier estimator", "log-rank test", "Cox proportional hazards"],
        "safety": ["Fisher's exact test", "Chi-squared test for adverse events"],
        "assumptions": ["Proportional hazards", "Normal distribution for continuous endpoints",
                        "Independent observations"],
        "software": ["R (survival, lme4)", "SAS PROC LIFETEST"],
        "reporting": "CONSORT 2010",
    },
    "cohort": {
        "primary": ["Kaplan-Meier estimator", "Cox proportional hazards regression"],
        "adjustment": ["Multivariable logistic regression", "Propensity score matching"],
        "safety": ["Incidence rate calculation", "Competing risks analysis (Fine-Gray)"],
        "assumptions": ["No unmeasured confounders", "Proportional hazards"],
        "software": ["R (survival, cmprsk)", "Stata"],
        "reporting": "STROBE",
    },
    "systematic_review": {
        "primary": ["Fixed-effects meta-analysis (I²<25%)", "Random-effects (DerSimonian-Laird)"],
        "heterogeneity": ["Cochran Q test", "I² statistic", "τ²"],
        "bias": ["Funnel plot", "Egger's test", "Begg's test"],
        "subgroup": ["Subgroup meta-regression", "Sensitivity analysis"],
        "assumptions": ["Exchangeability of studies", "Publication bias assessed"],
        "software": ["R (meta, metafor)", "RevMan"],
        "reporting": "PRISMA 2020",
    },
    "case_control": {
        "primary": ["Odds ratio with 95% CI", "Conditional logistic regression"],
        "matching": ["McNemar's test for matched pairs"],
        "adjustment": ["Multivariable logistic regression"],
        "assumptions": ["Representative controls", "No recall bias"],
        "software": ["R (epiR)", "SPSS"],
        "reporting": "STROBE",
    },
    "retrospective": {
        "primary": ["Descriptive statistics", "Kaplan-Meier for time-to-event"],
        "comparison": ["Mann-Whitney U", "Fisher's exact test"],
        "adjustment": ["Multivariable Cox regression", "Propensity score analysis"],
        "assumptions": ["Complete case analysis or multiple imputation for missing data"],
        "software": ["R (survival)", "SPSS", "SAS"],
        "reporting": "STROBE",
    },
    "phase1": {
        "primary": ["3+3 dose escalation", "BOIN design", "mTPI design"],
        "endpoints": ["MTD estimation", "DLT rate", "PK parameters"],
        "safety": ["CTCAE v5 grading", "DLT analysis"],
        "assumptions": ["Monotone dose-toxicity relationship"],
        "software": ["R (BOIN package)", "escalation"],
        "reporting": "CONSORT 2010 extension for dose-finding",
    },
}

_ALPHA = 0.05
_POWER = 0.80


class StatisticalAnalyst(SkillBase):
    """
    Recommends statistical methods and analysis plans for hematology studies.
    Writes results to context.statistical_plan.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[StatisticalAnalyst] {prompt[:200]}"
        except Exception:
            return ""

    def analyze(
        self,
        data_description: str,
        study_type: str,
        primary_endpoint: str = "",
        sample_size: int = 0,
    ) -> dict:
        """
        Generate a statistical analysis plan based on study design.

        Args:
            data_description: Brief description of the data/population
            study_type: One of: rct, cohort, systematic_review, case_control,
                        retrospective, phase1
            primary_endpoint: Primary endpoint (e.g., "OS", "CR rate")
            sample_size: Estimated sample size (0 if unknown)

        Returns:
            dict: Statistical plan. Writes to context.statistical_plan.
        """
        try:
            key = study_type.lower().replace("-", "_").replace(" ", "_")
            methods = _DESIGN_METHODS.get(key, _DESIGN_METHODS["retrospective"])

            plan = {
                "study_type": study_type,
                "primary_endpoint": primary_endpoint or "to be defined",
                "alpha": _ALPHA,
                "power": _POWER,
                "sample_size": sample_size,
                "methods": methods.get("primary", []),
                "assumptions": methods.get("assumptions", []),
                "software": methods.get("software", ["R"]),
                "reporting_guideline": methods.get("reporting", "STROBE"),
                "description": data_description,
                "secondary_methods": {
                    k: v for k, v in methods.items()
                    if k not in ("primary", "assumptions", "software", "reporting")
                },
            }

            self.context.statistical_plan = plan
            self._log.info("StatisticalAnalyst: plan generated for %s", study_type)
            return plan

        except Exception as exc:
            self._log.warning("StatisticalAnalyst.analyze failed: %s", exc)
            return {}

    def recommend_sample_size_approach(self, study_type: str, primary_endpoint: str) -> str:
        """Return plain-text sample size calculation guidance."""
        try:
            endpoint_lower = primary_endpoint.lower()
            if any(t in endpoint_lower for t in ("survival", "os", "pfs", "efs")):
                return (
                    f"For time-to-event endpoint ({primary_endpoint}): Use log-rank test formula. "
                    f"Specify expected median OS in each arm, accrual period, and follow-up. "
                    f"Calculate required events (not patients) at α={_ALPHA}, power={_POWER}."
                )
            elif any(t in endpoint_lower for t in ("rate", "cr", "orr", "response")):
                return (
                    f"For binary endpoint ({primary_endpoint}): Use two-proportion z-test or "
                    f"exact binomial. Specify expected rates in each arm at α={_ALPHA}, power={_POWER}."
                )
            else:
                return (
                    f"For {primary_endpoint}: Specify effect size, SD, and minimal clinically "
                    f"important difference. Use t-test formula at α={_ALPHA}, power={_POWER}."
                )
        except Exception as exc:
            self._log.warning("recommend_sample_size_approach failed: %s", exc)
            return ""

    def get_reporting_checklist(self, study_type: str) -> list[str]:
        """Return reporting guideline checklist items for study type."""
        try:
            key = study_type.lower().replace("-", "_").replace(" ", "_")
            methods = _DESIGN_METHODS.get(key, {})
            guideline = methods.get("reporting", "STROBE")
            base = [
                f"Reporting guideline: {guideline}",
                "Sample size justification with formula and assumptions",
                "Missing data handling strategy documented",
                "Multiplicity correction for secondary endpoints",
                "All statistical software and versions cited",
            ]
            return base
        except Exception as exc:
            self._log.warning("get_reporting_checklist failed: %s", exc)
            return []
