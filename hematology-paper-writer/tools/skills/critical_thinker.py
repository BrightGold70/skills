"""
CriticalThinker — Scientific Skills Integration
Maps to: scientific-critical-thinking OpenCode skill
HPW Phases: 5 (Quality), 8 (Peer Review)

Evaluates scientific claims, identifies logical weaknesses,
and provides critical analysis of hematology manuscript arguments.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

_FALLACY_PATTERNS: dict[str, str] = {
    "overgeneralization": "Conclusion drawn from insufficient sample or data subset.",
    "correlation_causation": "Correlation treated as causation without mechanistic evidence.",
    "cherry_picking": "Selective data presentation omitting contradictory findings.",
    "appeal_to_authority": "Citing authority without independent evidence in context.",
    "hasty_generalization": "Universal claim based on limited evidence.",
    "circular_reasoning": "Conclusion restates the premise without new evidence.",
    "false_dichotomy": "Only two options presented when others exist.",
}

_METHODOLOGICAL_WEAKNESSES: dict[str, list[str]] = {
    "rct": [
        "Lack of blinding",
        "Inadequate randomization",
        "High dropout rate",
        "Short follow-up",
        "Surrogate endpoint only",
    ],
    "cohort": [
        "Selection bias",
        "Loss to follow-up",
        "Unmeasured confounders",
        "Retrospective ascertainment",
        "Single-center limitation",
    ],
    "retrospective": [
        "Ascertainment bias",
        "Missing data",
        "Selection bias",
        "No control group",
        "Heterogeneous treatment",
    ],
    "case_series": [
        "No comparator",
        "Selection bias",
        "Small sample size",
        "Limited generalizability",
        "No statistical testing",
    ],
    "systematic_review": [
        "Publication bias",
        "Heterogeneity in pooled analyses",
        "Quality variability of included studies",
        "Grey literature exclusion",
        "Language bias",
    ],
    "phase1": [
        "No control group",
        "Small sample size per dose level",
        "Efficacy assessment not primary purpose",
        "Highly selected patient population",
    ],
}

_CRITICAL_QUESTIONS: dict[str, list[str]] = {
    "internal_validity": [
        "Were the inclusion/exclusion criteria clearly defined and consistently applied?",
        "Were all outcomes pre-specified before data collection?",
        "Was there adequate control for confounding variables?",
        "Is the follow-up duration appropriate for the endpoint measured?",
    ],
    "external_validity": [
        "Is the study population representative of the target clinical population?",
        "Were centers/sites representative of typical practice?",
        "Can results be generalized to non-academic centers?",
        "Are the treatment regimens consistent with current practice?",
    ],
    "statistical_rigor": [
        "Was the sample size calculation pre-specified and justified?",
        "Were multiple comparisons appropriately adjusted?",
        "Was the statistical analysis plan pre-specified?",
        "Are confidence intervals reported alongside p-values?",
    ],
    "clinical_relevance": [
        "Is the observed effect size clinically meaningful?",
        "Does the primary endpoint reflect patient-important outcomes?",
        "Are the benefits weighed against harms and treatment burden?",
        "How does this compare with existing standard of care?",
    ],
}

_FALLACY_TRIGGERS: dict[str, list[str]] = {
    "overgeneralization": ["all patients", "all cases", "universally true"],
    "correlation_causation": ["therefore causes", "directly leads to", "resulted in the improvement"],
    "cherry_picking": ["selected patients only", "we focused on responders"],
    "hasty_generalization": ["this proves that all", "these data confirm that all"],
    "false_dichotomy": ["either … or", "only two options", "no other choice"],
}


class CriticalThinker(SkillBase):
    """
    Evaluates scientific arguments for logical fallacies and methodological weaknesses.
    Writes findings to context.quality_scores['critical_thinking'].
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[CriticalThinker] {prompt[:200]}"
        except Exception:
            return ""

    def evaluate(
        self,
        text: str,
        study_type: str = "cohort",
        focus: str = "all",
    ) -> dict:
        """
        Evaluate scientific text for critical thinking issues.

        Args:
            text: Manuscript section or full text to evaluate
            study_type: rct | cohort | retrospective | case_series | systematic_review | phase1
            focus: "all" | "fallacies" | "methodology" | "statistics" | "validity"

        Returns:
            dict with fallacies, weaknesses, questions, score, recommendations.
            Writes to context.quality_scores['critical_thinking'].
        """
        try:
            result: dict = {
                "fallacies": [],
                "weaknesses": [],
                "critical_questions": [],
                "score": 0.0,
                "recommendations": [],
            }

            if focus in ("all", "fallacies"):
                result["fallacies"] = self._detect_fallacies(text)

            if focus in ("all", "methodology"):
                result["weaknesses"] = self._get_methodological_weaknesses(study_type)

            if focus in ("all", "validity"):
                result["critical_questions"] = self._get_critical_questions()

            result["score"] = self._compute_score(result)
            result["recommendations"] = self._generate_recommendations(result)

            self.context.quality_scores["critical_thinking"] = result["score"]
            self._log.info(
                "CriticalThinker.evaluate: score=%.2f, fallacies=%d, weaknesses=%d",
                result["score"],
                len(result["fallacies"]),
                len(result["weaknesses"]),
            )
            return result
        except Exception as exc:
            self._log.warning("CriticalThinker.evaluate failed: %s", exc)
            return {}

    def generate_reviewer_questions(self, domain: str = "all") -> list[str]:
        """
        Return critical reviewer questions for the given domain.

        Args:
            domain: "internal_validity" | "external_validity" |
                    "statistical_rigor" | "clinical_relevance" | "all"

        Returns:
            list[str]: Critical questions for peer review.
        """
        try:
            if domain == "all":
                questions: list[str] = []
                for q_list in _CRITICAL_QUESTIONS.values():
                    questions.extend(q_list)
                return questions
            return list(_CRITICAL_QUESTIONS.get(domain, []))
        except Exception as exc:
            self._log.warning("generate_reviewer_questions failed: %s", exc)
            return []

    def identify_limitations(self, study_type: str, text: str = "") -> list[str]:
        """
        Identify study limitations based on design type and optional text.

        Args:
            study_type: rct | cohort | retrospective | case_series | systematic_review
            text: Optional manuscript text for context-specific detection

        Returns:
            list[str]: Applicable limitations for the study type.
        """
        try:
            base = list(_METHODOLOGICAL_WEAKNESSES.get(study_type.lower(), []))
            text_lower = text.lower()
            if "single center" in text_lower or "single-center" in text_lower:
                base.append("Single-center design limits generalizability")
            if "retrospective" in text_lower and study_type not in ("retrospective",):
                base.append("Retrospective data collection introduces ascertainment bias")
            return base
        except Exception as exc:
            self._log.warning("identify_limitations failed: %s", exc)
            return []

    # ── private helpers ──────────────────────────────────────────────────────

    def _detect_fallacies(self, text: str) -> list[dict]:
        found = []
        text_lower = text.lower()
        for fallacy, keywords in _FALLACY_TRIGGERS.items():
            for kw in keywords:
                if kw in text_lower:
                    found.append({
                        "type": fallacy,
                        "description": _FALLACY_PATTERNS[fallacy],
                        "trigger": kw,
                    })
                    break
        return found

    def _get_methodological_weaknesses(self, study_type: str) -> list[str]:
        return list(_METHODOLOGICAL_WEAKNESSES.get(study_type.lower(), []))

    def _get_critical_questions(self) -> list[str]:
        questions: list[str] = []
        for q_list in _CRITICAL_QUESTIONS.values():
            questions.extend(q_list)
        return questions

    def _compute_score(self, result: dict) -> float:
        deductions = len(result["fallacies"]) * 10 + len(result["weaknesses"]) * 5
        return max(0.0, 100.0 - float(deductions))

    def _generate_recommendations(self, result: dict) -> list[str]:
        recs = []
        if result["fallacies"]:
            recs.append(
                f"Address {len(result['fallacies'])} logical issue(s): "
                + ", ".join(f["type"] for f in result["fallacies"])
            )
        if result["weaknesses"]:
            recs.append(
                "Acknowledge study limitations in the Discussion: "
                + "; ".join(result["weaknesses"][:3])
            )
        if not recs:
            recs.append(
                "Critical analysis passed. Ensure limitations section is comprehensive."
            )
        return recs
