"""
StatisticalAnalyst — Tier 1 CSA Scientific Skill (Pre-analysis)

Validates statistical methods appropriate for each disease type and
generates analysis plans before R scripts run.

Maps to: statistical-analysis OpenCode skill
CSA Hook: integrate_skills_pre_analysis()
"""

from __future__ import annotations

from ._base import CSASkillBase, CSASkillContext

_DISEASE_METHODS: dict[str, dict] = {
    "aml": {
        "primary": [
            "Kaplan-Meier estimator (OS, EFS, RFS)",
            "Log-rank test for group comparison",
            "Cox proportional hazards regression (multivariable)",
            "Fine-Gray competing risks (CIR, NRM)",
        ],
        "response": [
            "Wilson score 95% CI for binary response rates (CR, CRi, CRh, cCR)",
            "ELN 2022 risk stratification (cytogenetic + molecular criteria)",
        ],
        "phase1": [
            "BOIN design (Liu & Yuan 2015) for dose-finding",
            "3+3 escalation (if BOIN not applicable)",
            "DLT analysis with CTCAE v5",
        ],
        "safety": ["CTCAE v5.0 adverse event grading", "Fisher's exact test for AE comparison"],
        "assumptions": [
            "Proportional hazards (verified by cox.zph())",
            "Independent observations",
            "Complete case analysis or multiple imputation for missing data",
        ],
        "software": ["R (survival, cmprsk, BOIN, flextable)"],
        "reporting": "CONSORT 2010 (RCT) / STROBE (observational)",
    },
    "cml": {
        "primary": [
            "Kaplan-Meier estimator (OS, PFS, TFR)",
            "Cox PH regression for TFR determinants",
            "ELN 2020 milestone assessment (3/6/12/18 months)",
        ],
        "response": [
            "BCR-ABL IS kinetics (log10 scale)",
            "CCyR, MMR, DMR rate calculation with Wilson CI",
            "Sokal / Hasford / ELTS score calculation",
        ],
        "safety": ["CTCAE v5.0 AE grading", "Chi-squared or Fisher's exact for AE rates"],
        "assumptions": [
            "Proportional hazards for TFR Cox model",
            "Molecular response measured at standardised IS labs",
        ],
        "software": ["R (survival, cmprsk, flextable)"],
        "reporting": "STROBE",
    },
    "mds": {
        "primary": [
            "Kaplan-Meier estimator (OS, transfusion-free survival)",
            "Cox PH regression",
        ],
        "response": [
            "IWG 2006 response criteria (HI, CR, PR, mCR)",
            "Wilson score CI for HI rate",
        ],
        "safety": ["CTCAE v5.0 AE grading"],
        "assumptions": [
            "Proportional hazards (cox.zph())",
            "Competing risk of death without HI",
        ],
        "software": ["R (survival, flextable)"],
        "reporting": "STROBE",
    },
    "hct": {
        "primary": [
            "Fine-Gray subdistribution hazard model (aGVHD, cGVHD, relapse — death competing)",
            "Kaplan-Meier for OS and GRFS",
            "Cox PH for GRFS determinants",
        ],
        "gvhd": [
            "NIH 2014 consensus criteria for aGVHD grading (grades 1–4)",
            "NIH 2014 consensus criteria for cGVHD severity (mild/moderate/severe)",
            "GRFS = freedom from grade 3–4 aGVHD, moderate-severe cGVHD, relapse, or death",
        ],
        "engraftment": ["Cumulative incidence of neutrophil and platelet engraftment"],
        "safety": ["CTCAE v5.0 AE grading"],
        "assumptions": [
            "Non-informative censoring",
            "Fine-Gray preferred over cause-specific Cox for GVHD endpoints",
        ],
        "software": ["R (survival, cmprsk, flextable)"],
        "reporting": "STROBE",
    },
}

_ALPHA = 0.05
_POWER = 0.80


class StatisticalAnalyst(CSASkillBase):
    """
    Recommends statistical methods and generates analysis plans for CSA studies.
    Writes results to context.statistical_plan.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[StatisticalAnalyst] {prompt[:200]}"
        except Exception:
            return ""

    def analyze(
        self,
        disease: str,
        primary_endpoint: str = "",
        study_type: str = "retrospective",
        n: int = 0,
    ) -> dict:
        """
        Generate a statistical analysis plan.

        Args:
            disease: "aml" | "cml" | "mds" | "hct"
            primary_endpoint: e.g. "OS", "CR rate", "TFR"
            study_type: "retrospective" | "rct" | "phase1" | "cohort"
            n: estimated sample size (0 if unknown)

        Returns:
            dict: Statistical plan. Writes to context.statistical_plan.
        """
        try:
            key = disease.lower()
            methods = _DISEASE_METHODS.get(key, _DISEASE_METHODS["aml"])

            # Phase 1 — always use phase1 methods if study_type is phase1
            primary_methods = methods.get("primary", [])
            if study_type == "phase1" and "phase1" in methods:
                primary_methods = methods["phase1"] + primary_methods

            plan = {
                "study_type": study_type,
                "disease": disease,
                "primary_endpoint": primary_endpoint or "to be defined",
                "alpha": _ALPHA,
                "power": _POWER,
                "sample_size": n,
                "methods": primary_methods,
                "response_methods": methods.get("response", []),
                "safety_methods": methods.get("safety", []),
                "assumptions": methods.get("assumptions", []),
                "software": methods.get("software", ["R"]),
                "reporting_guideline": methods.get("reporting", "STROBE"),
                "disease_specific_methods": {
                    k: v for k, v in methods.items()
                    if k not in ("primary", "response", "safety", "assumptions",
                                 "software", "reporting", "phase1")
                },
            }

            self.context.statistical_plan = plan
            self._log.info("StatisticalAnalyst: plan generated for %s/%s", disease, study_type)
            return plan

        except Exception as exc:
            self._log.warning("StatisticalAnalyst.analyze failed: %s", exc)
            return {}

    def get_reporting_checklist(self, disease: str, study_type: str) -> list:
        """Return reporting guideline checklist items."""
        try:
            methods = _DISEASE_METHODS.get(disease.lower(), {})
            guideline = methods.get("reporting", "STROBE")
            return [
                f"Reporting guideline: {guideline}",
                "Sample size justification with formula and assumptions",
                "Missing data handling strategy documented",
                "All statistical software and versions cited",
                "cox.zph() proportional hazards test reported for Cox models",
                f"Disease-specific: {disease.upper()} endpoints per current guidelines",
            ]
        except Exception as exc:
            self._log.warning("get_reporting_checklist failed: %s", exc)
            return []
