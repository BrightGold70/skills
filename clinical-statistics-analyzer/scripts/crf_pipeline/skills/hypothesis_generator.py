"""
HypothesisGenerator — Tier 1 CSA Scientific Skill (Pre-analysis)

Generates disease-specific null and alternative hypotheses based on
hematology endpoints before R scripts run.

Maps to: hypothesis-generation OpenCode skill
CSA Hook: integrate_skills_pre_analysis()
"""

from __future__ import annotations

from ._base import CSASkillBase, CSASkillContext

_DISEASE_ENDPOINTS: dict[str, list[str]] = {
    "aml": ["OS", "EFS", "CR rate", "cCR rate (CR+CRi+CRh+MLFS)", "ELN risk distribution",
            "BOIN MTD (Phase 1)"],
    "cml": ["MMR at 12 months", "CCyR rate", "TFR at 12/24 months", "ELN milestone achievement",
            "Sokal/ELTS risk score distribution"],
    "mds": ["OS", "HI rate", "transfusion independence", "CR rate per IWG 2006"],
    "hct": ["OS", "GRFS", "aGVHD grade 2–4 cumulative incidence",
            "cGVHD moderate-severe cumulative incidence", "engraftment days"],
}

_HYPOTHESIS_TEMPLATES: dict[str, dict[str, str]] = {
    "aml": {
        "null":        "H₀: The {treatment} does not improve {endpoint} compared to {comparator} "
                       "(HR = 1.0 for time-to-event; OR = 1.0 for binary response).",
        "alternative": "H₁: The {treatment} improves {endpoint} compared to {comparator} "
                       "(HR < 1.0 for survival; OR > 1.0 for CR/cCR rate per ELN 2022).",
        "exploratory": "H_exp: ELN 2022 risk stratification (Favorable/Intermediate/Adverse) "
                       "predicts {endpoint} heterogeneity with treatment {treatment}.",
    },
    "cml": {
        "null":        "H₀: The {treatment} does not increase the rate of MMR at 12 months "
                       "or TFR beyond historical benchmarks (MMR₁₂ = {comparator}).",
        "alternative": "H₁: The {treatment} achieves superior MMR at 12 months and/or TFR "
                       "rate compared to {comparator} per ELN 2020 milestones.",
        "exploratory": "H_exp: Sokal/ELTS risk score at baseline predicts depth of molecular "
                       "response and TFR durability with {treatment}.",
    },
    "mds": {
        "null":        "H₀: The {treatment} does not improve {endpoint} (HI rate or OS) "
                       "compared to {comparator} per IWG 2006 criteria.",
        "alternative": "H₁: The {treatment} improves {endpoint} and transfusion independence "
                       "rate compared to {comparator}.",
        "exploratory": "H_exp: IPSS-R risk category predicts {endpoint} heterogeneity "
                       "with {treatment}.",
    },
    "hct": {
        "null":        "H₀: The {treatment} conditioning/prophylaxis does not reduce aGVHD "
                       "grade 2–4 cumulative incidence or improve GRFS compared to {comparator}.",
        "alternative": "H₁: The {treatment} reduces aGVHD grade 2–4 CI and/or improves GRFS "
                       "compared to {comparator} per NIH 2014 grading.",
        "exploratory": "H_exp: Donor type and conditioning intensity predict GRFS and NRM "
                       "independently of {treatment}.",
    },
}


class HypothesisGenerator(CSASkillBase):
    """
    Generates null, alternative, and exploratory hypotheses for hematology studies.
    Writes results to context.hypotheses.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[HypothesisGenerator] {prompt[:200]}"
        except Exception:
            return ""

    def generate(
        self,
        disease: str,
        treatment: str = "the study treatment",
        endpoint: str = "",
        comparator: str = "standard of care",
    ) -> list:
        """
        Generate 3 hypotheses (null, alternative, exploratory).

        Args:
            disease: "aml" | "cml" | "mds" | "hct"
            treatment: treatment name/description
            endpoint: primary endpoint (auto-selected if empty)
            comparator: comparator arm description

        Returns:
            list[str]: Three hypothesis strings.
            Writes to context.hypotheses.
        """
        try:
            key = disease.lower()
            templates = _HYPOTHESIS_TEMPLATES.get(key, _HYPOTHESIS_TEMPLATES["aml"])
            endpoints = _DISEASE_ENDPOINTS.get(key, _DISEASE_ENDPOINTS["aml"])
            ep = endpoint or endpoints[0]

            hyps = [
                templates["null"].format(
                    treatment=treatment, endpoint=ep, comparator=comparator),
                templates["alternative"].format(
                    treatment=treatment, endpoint=ep, comparator=comparator),
                templates["exploratory"].format(
                    treatment=treatment, endpoint=ep, comparator=comparator),
            ]

            self.context.hypotheses = hyps
            self._log.info("HypothesisGenerator: generated 3 hypotheses for %s/%s", disease, ep)
            return hyps

        except Exception as exc:
            self._log.warning("HypothesisGenerator.generate failed: %s", exc)
            return []

    def list_endpoints(self, disease: str) -> list:
        """Return canonical endpoints for the given disease."""
        try:
            return _DISEASE_ENDPOINTS.get(disease.lower(), [])
        except Exception:
            return []
