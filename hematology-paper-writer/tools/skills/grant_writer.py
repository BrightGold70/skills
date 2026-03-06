"""
GrantWriter — Scientific Skills Integration
Maps to: research-grants OpenCode skill
HPW Phase: 9 (Publication), standalone

Generates grant application section templates for hematology research proposals.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

_GRANT_SECTION_TEMPLATES: dict[str, str] = {
    "specific_aims": (
        "SPECIFIC AIMS\n\n"
        "{disease} remains a significant clinical challenge, with {incidence_context}. "
        "{current_treatment_limitations}. "
        "We hypothesize that {hypothesis}. "
        "To test this hypothesis, we propose the following specific aims:\n\n"
        "Aim 1: {aim_1}\n"
        "Aim 2: {aim_2}\n"
        "Aim 3: {aim_3}\n\n"
        "Successful completion of these aims will {expected_impact}."
    ),
    "significance": (
        "SIGNIFICANCE\n\n"
        "{disease} affects approximately {prevalence} patients annually in {region}. "
        "Despite advances with {current_treatments}, {unmet_need}. "
        "The proposed research addresses this gap by {proposed_approach}. "
        "These studies are significant because {significance_statement}."
    ),
    "innovation": (
        "INNOVATION\n\n"
        "This proposal is innovative because it {innovation_statement}. "
        "Prior approaches have {prior_approach_limitations}. "
        "Our {novel_element} represents a departure from conventional thinking in the field. "
        "The proposed {method_or_approach} has not previously been applied to {context}."
    ),
    "approach": (
        "APPROACH\n\n"
        "Aim 1: {aim_1}\n"
        "Rationale: {rationale_1}\n"
        "Design: {design_1}\n"
        "Anticipated Results: {results_1}\n"
        "Potential Pitfalls and Alternatives: {pitfalls_1}\n\n"
        "Aim 2: {aim_2}\n"
        "Rationale: {rationale_2}\n"
        "Design: {design_2}\n"
        "Anticipated Results: {results_2}\n"
        "Potential Pitfalls and Alternatives: {pitfalls_2}\n"
    ),
    "human_subjects": (
        "HUMAN SUBJECTS\n\n"
        "Risk Level: {risk_level}\n"
        "Subject Population: {population_description}\n"
        "Inclusion Criteria: {inclusion_criteria}\n"
        "Exclusion Criteria: {exclusion_criteria}\n"
        "Recruitment Strategy: {recruitment_strategy}\n"
        "Informed Consent: {consent_process}\n"
        "Data Safety: {data_safety_plan}\n"
    ),
}

_BUDGET_CATEGORIES: list[str] = [
    "Personnel (PI, Co-I, postdoctoral fellows, graduate students, research coordinator)",
    "Equipment (major equipment if needed for proposed studies)",
    "Supplies (reagents, sequencing costs, flow cytometry panels)",
    "Patient recruitment and incentives (if applicable)",
    "Travel (dissemination at conferences and collaboration visits)",
    "Indirect costs (at negotiated institutional rate)",
]


class GrantWriter(SkillBase):
    """
    Generates grant application section templates for hematology research.
    Writes to context.grant_sections[section].
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[GrantWriter] {prompt[:200]}"
        except Exception:
            return ""

    def write_section(
        self,
        section: str,
        **placeholders,
    ) -> str:
        """
        Generate a grant section template.

        Args:
            section: specific_aims | significance | innovation | approach |
                     human_subjects
            **placeholders: Template variable values

        Returns:
            str: Filled grant section template.
            Writes to context.grant_sections[section].
        """
        try:
            template = _GRANT_SECTION_TEMPLATES.get(section)
            if not template:
                text = f"[{section.replace('_', ' ').title()} section]\n"
            else:
                from tools.skills.scientific_writer import _SafeFormatMap
                text = template.format_map(_SafeFormatMap(placeholders))

            self.context.grant_sections[section] = text
            self._log.info(
                "GrantWriter.write_section: section='%s', %d chars",
                section, len(text),
            )
            return text
        except Exception as exc:
            self._log.warning("GrantWriter.write_section failed: %s", exc)
            return ""

    def get_budget_template(self) -> list[str]:
        """Return standard NIH/grant budget categories."""
        return list(_BUDGET_CATEGORIES)

    def list_sections(self) -> list[str]:
        """Return available grant sections."""
        return list(_GRANT_SECTION_TEMPLATES.keys())
