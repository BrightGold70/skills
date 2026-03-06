"""
HypothesisGenerator — Scientific Skills Integration
Maps to: hypothesis-generation OpenCode skill
HPW Phases: 1 (Topic Selection), 2 (Research Design)
"""

from __future__ import annotations

from typing import Optional
from ._base import SkillBase, SkillContext

# Disease-specific outcome templates for hematology
_DISEASE_OUTCOMES: dict[str, list[str]] = {
    "aml": ["overall survival (OS)", "event-free survival (EFS)", "complete remission (CR) rate",
            "minimal residual disease (MRD) negativity", "relapse-free survival (RFS)"],
    "cml": ["major molecular response (MMR)", "deep molecular response (DMR)",
            "treatment-free remission (TFR)", "progression-free survival (PFS)"],
    "mds": ["overall survival (OS)", "leukemia-free survival (LFS)",
            "transfusion independence", "hematologic improvement (HI)"],
    "hct": ["non-relapse mortality (NRM)", "graft-versus-host disease (GVHD)-free survival",
            "engraftment rate", "overall survival (OS)"],
}

_STUDY_DESIGN_TEMPLATES: list[str] = [
    "{intervention} improves {outcome} compared to {comparator} in patients with {disease}",
    "{biomarker} predicts {outcome} in {disease} patients treated with {intervention}",
    "Addition of {intervention} to standard therapy reduces {adverse_outcome} in {disease}",
    "{disease} patients achieving {milestone} have superior long-term {outcome}",
]


class HypothesisGenerator(SkillBase):
    """
    Generates structured research hypotheses for hematology manuscripts.
    Writes results to context.hypotheses.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        """Format hypothesis generation prompt. Returns structured hypothesis text."""
        try:
            return f"[HypothesisGenerator] {prompt[:200]}"
        except Exception:
            return ""

    def generate(
        self,
        topic: str,
        disease: str = "",
        intervention: str = "",
        comparator: str = "",
        n: int = 3,
    ) -> list[str]:
        """
        Generate research hypotheses from topic and disease context.

        Args:
            topic: Research topic string
            disease: Disease type — "aml", "cml", "mds", "hct", or empty
            intervention: Primary intervention (optional)
            comparator: Comparator/control (optional, defaults to "standard of care")
            n: Number of hypotheses to generate (default 3)

        Returns:
            list[str]: Generated hypotheses. Updates context.hypotheses.
        """
        try:
            disease_key = disease.lower().strip()
            outcomes = _DISEASE_OUTCOMES.get(disease_key, ["overall survival (OS)", "response rate"])
            comparator = comparator or "standard of care"

            hypotheses: list[str] = []

            # Primary efficacy hypothesis
            if intervention and outcomes:
                hypotheses.append(
                    f"{intervention} improves {outcomes[0]} compared to {comparator} "
                    f"in patients with {disease.upper() if disease else topic}."
                )

            # Secondary outcome hypothesis
            if len(outcomes) > 1:
                hypotheses.append(
                    f"Patients achieving {outcomes[1]} after {intervention or 'treatment'} "
                    f"demonstrate superior long-term outcomes in {disease.upper() if disease else topic}."
                )

            # Biomarker/predictive hypothesis
            hypotheses.append(
                f"Baseline molecular and clinical characteristics predict {outcomes[0]} "
                f"in {disease.upper() if disease else topic} patients, enabling risk stratification."
            )

            # Topic-driven fallback hypotheses
            while len(hypotheses) < n:
                idx = len(hypotheses) % len(_STUDY_DESIGN_TEMPLATES)
                tpl = _STUDY_DESIGN_TEMPLATES[idx]
                hypotheses.append(
                    tpl.format(
                        intervention=intervention or "novel therapy",
                        outcome=outcomes[0],
                        comparator=comparator,
                        disease=disease.upper() if disease else topic,
                        biomarker="genomic profile",
                        adverse_outcome="treatment-related mortality",
                        milestone=outcomes[1] if len(outcomes) > 1 else "complete remission",
                    )
                )

            result = hypotheses[:n]
            self.context.hypotheses = result
            self._log.info("Generated %d hypotheses for topic: %s", len(result), topic)
            return result

        except Exception as exc:
            self._log.warning("HypothesisGenerator.generate failed: %s", exc)
            return []

    def generate_null_hypotheses(self, hypotheses: Optional[list[str]] = None) -> list[str]:
        """Convert research hypotheses to null hypothesis form."""
        try:
            source = hypotheses or self.context.hypotheses
            return [f"H₀: There is no significant difference in {h.split('improves')[-1].strip()}"
                    if "improves" in h else f"H₀: No association — {h}"
                    for h in source]
        except Exception as exc:
            self._log.warning("generate_null_hypotheses failed: %s", exc)
            return []
