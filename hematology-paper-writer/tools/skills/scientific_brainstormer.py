"""
ScientificBrainstormer — Scientific Skills Integration
Maps to: scientific-brainstorming OpenCode skill
HPW Phases: 1 (Topic Selection), Part 16 (Manuscript Brainstorming)

Implements SCAMPER, Six Thinking Hats, and free-association brainstorming
for research ideation, as described in the scientific-brainstorming SKILL.md.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

_SCAMPER_PROMPTS = {
    "Substitute":   "What component of current treatment/approach could be substituted?",
    "Combine":      "What two existing therapies or approaches could be combined?",
    "Adapt":        "What method from another disease area could be adapted?",
    "Modify":       "What aspect of dosing, timing, or patient selection could be modified?",
    "Put to use":   "What existing data or biomarker could be repurposed for this question?",
    "Eliminate":    "What step or treatment could be eliminated to reduce toxicity?",
    "Reverse":      "What if the current treatment sequence were reversed?",
}

_SIX_HATS = {
    "White (Facts)":   "What do we know from existing data and literature?",
    "Red (Emotion)":   "What does clinical intuition suggest about this approach?",
    "Black (Caution)": "What could go wrong? What are the risks and limitations?",
    "Yellow (Value)":  "What is the best-case scenario if this hypothesis is correct?",
    "Green (Creative)":"What unconventional approach hasn't been tried yet?",
    "Blue (Process)":  "What is the most rigorous study design to test this?",
}


class ScientificBrainstormer(SkillBase):
    """
    Generates structured brainstorming output for research topic exploration.
    Appends results to context.research_gaps.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ScientificBrainstormer] {prompt[:200]}"
        except Exception:
            return ""

    def brainstorm(
        self,
        topic: str,
        method: str = "free",
        disease: str = "",
    ) -> list[str]:
        """
        Generate brainstorming ideas for a research topic.

        Args:
            topic: Research topic to brainstorm
            method: "scamper" | "six_hats" | "free" (default)
            disease: Optional disease context for targeted prompts

        Returns:
            list[str]: Brainstorming ideas/gaps. Appends to context.research_gaps.
        """
        try:
            method = method.lower().replace("-", "_")
            ideas: list[str] = []

            if method == "scamper":
                ideas = self._scamper(topic, disease)
            elif method in ("six_hats", "six-hats"):
                ideas = self._six_hats(topic, disease)
            else:
                ideas = self._free_association(topic, disease)

            self.context.research_gaps = list(dict.fromkeys(
                self.context.research_gaps + ideas
            ))
            self._log.info("Brainstormed %d ideas (%s) for: %s", len(ideas), method, topic)
            return ideas

        except Exception as exc:
            self._log.warning("ScientificBrainstormer.brainstorm failed: %s", exc)
            return []

    def _scamper(self, topic: str, disease: str) -> list[str]:
        disease_ctx = f" in {disease.upper()}" if disease else ""
        return [
            f"[{key}] {prompt} — applied to {topic}{disease_ctx}"
            for key, prompt in _SCAMPER_PROMPTS.items()
        ]

    def _six_hats(self, topic: str, disease: str) -> list[str]:
        disease_ctx = f" ({disease.upper()})" if disease else ""
        return [
            f"[{hat}] {question} — for {topic}{disease_ctx}"
            for hat, question in _SIX_HATS.items()
        ]

    def _free_association(self, topic: str, disease: str) -> list[str]:
        disease_ctx = disease.upper() if disease else "hematology"
        return [
            f"What are the unmet needs in {topic} for {disease_ctx} patients?",
            f"Which subgroup of {disease_ctx} patients benefits most from current approaches to {topic}?",
            f"What biomarker could stratify patients for {topic}-based interventions?",
            f"How does {topic} compare across different {disease_ctx} risk groups?",
            f"What is the mechanism underlying resistance to {topic} in {disease_ctx}?",
            f"Could {topic} be applied earlier in the disease course of {disease_ctx}?",
        ]

    def generate_research_questions(self, topic: str, disease: str = "") -> list[str]:
        """Convert brainstorming ideas into formal research questions."""
        try:
            ideas = self.brainstorm(topic, method="free", disease=disease)
            return [idea if "?" in idea else f"{idea}?" for idea in ideas]
        except Exception as exc:
            self._log.warning("generate_research_questions failed: %s", exc)
            return []
