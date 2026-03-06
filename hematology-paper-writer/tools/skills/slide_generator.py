"""
SlideGenerator — Scientific Skills Integration
Maps to: scientific-slides OpenCode skill
HPW Phase: 9 (Publication)

Generates structured slide outlines for conference presentations
of hematology manuscripts.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

_SLIDE_TEMPLATES: dict[str, list[dict]] = {
    "oral_10min": [
        {"title": "Title Slide", "content": "{title} | {authors} | {conference} {year}"},
        {"title": "Background & Rationale", "content": "Disease context • Unmet need • Study rationale"},
        {"title": "Study Design", "content": "Design type • Eligibility criteria • Primary endpoint • Sample size"},
        {"title": "Patient Characteristics", "content": "Table 1: Baseline demographics and disease characteristics"},
        {"title": "Primary Endpoint", "content": "{primary_endpoint}: {primary_result} (95% CI {ci})"},
        {"title": "Key Secondary Endpoints", "content": "{secondary_endpoint_1} • {secondary_endpoint_2}"},
        {"title": "Safety", "content": "Grade ≥3 AEs table • Treatment modifications • Discontinuations"},
        {"title": "Conclusions", "content": "{conclusion_statement}"},
        {"title": "Acknowledgements", "content": "Funding • Contributing sites • Patients"},
    ],
    "oral_20min": [
        {"title": "Title Slide", "content": "{title} | {authors} | {conference} {year}"},
        {"title": "Background", "content": "Disease context and epidemiology"},
        {"title": "Rationale", "content": "Unmet need and mechanistic basis"},
        {"title": "Study Design", "content": "Schema with eligibility and endpoints"},
        {"title": "Patient Disposition", "content": "Enrollment flowchart (CONSORT)"},
        {"title": "Baseline Characteristics", "content": "Table 1"},
        {"title": "Primary Endpoint", "content": "KM curve or bar chart with 95% CI"},
        {"title": "Secondary Endpoints", "content": "Supporting efficacy data"},
        {"title": "Subgroup Analyses", "content": "Forest plot by pre-specified subgroups"},
        {"title": "Safety Overview", "content": "AE table (all grades and grade ≥3)"},
        {"title": "Notable Toxicities", "content": "Drug-specific safety profile"},
        {"title": "Discussion", "content": "Context vs. prior studies • Mechanism"},
        {"title": "Conclusions & Future Directions", "content": "{conclusion_statement}"},
        {"title": "Acknowledgements", "content": "Funding • Sites • Patients"},
    ],
    "poster": [
        {"title": "Introduction", "content": "Background • Hypothesis • Rationale"},
        {"title": "Methods", "content": "Study design • Eligibility • Endpoints • Statistics"},
        {"title": "Results — Efficacy", "content": "Primary and key secondary endpoints"},
        {"title": "Results — Safety", "content": "AE summary table"},
        {"title": "Conclusions", "content": "{conclusion_statement}"},
        {"title": "References & Disclosures", "content": "Key references (Vancouver style)"},
    ],
}


class SlideGenerator(SkillBase):
    """
    Generates conference presentation slide outlines from manuscript content.
    Writes to context.slide_outline.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[SlideGenerator] {prompt[:200]}"
        except Exception:
            return ""

    def generate_outline(
        self,
        format: str = "oral_10min",
        **placeholders,
    ) -> list[dict]:
        """
        Generate a structured slide outline for a presentation.

        Args:
            format: oral_10min | oral_20min | poster
            **placeholders: Template values (title, authors, conference, year,
                            primary_endpoint, primary_result, ci, conclusion_statement, etc.)

        Returns:
            list[dict]: Slide outline with title and content per slide.
            Writes to context.slide_outline.
        """
        try:
            template = _SLIDE_TEMPLATES.get(format, _SLIDE_TEMPLATES["oral_10min"])
            from tools.skills.scientific_writer import _SafeFormatMap
            outline = []
            for slide in template:
                outline.append({
                    "title": slide["title"],
                    "content": slide["content"].format_map(_SafeFormatMap(placeholders)),
                })

            self.context.slide_outline = outline
            self._log.info(
                "SlideGenerator.generate_outline: format='%s', %d slides",
                format, len(outline),
            )
            return outline
        except Exception as exc:
            self._log.warning("SlideGenerator.generate_outline failed: %s", exc)
            return []

    def list_formats(self) -> list[str]:
        """Return available presentation formats."""
        return list(_SLIDE_TEMPLATES.keys())

    def render_outline_text(self) -> str:
        """Render the current slide outline as plain text."""
        try:
            if not self.context.slide_outline:
                return ""
            lines = []
            for i, slide in enumerate(self.context.slide_outline, 1):
                lines.append(f"Slide {i}: {slide['title']}")
                lines.append(f"  {slide['content']}")
                lines.append("")
            return "\n".join(lines)
        except Exception as exc:
            self._log.warning("render_outline_text failed: %s", exc)
            return ""
