"""
ScientificSchematist — Scientific Skills Integration
Maps to: scientific-schematics OpenCode skill
HPW Phases: 2 (Research Design), 4 (Manuscript Prep)

Generates text-based schematic descriptions for study design diagrams,
flowcharts, and pathway diagrams in hematology manuscripts.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

_DIAGRAM_TEMPLATES: dict[str, str] = {
    "study_flow": (
        "Study Population Schematic\n"
        "  {population} (N={n_total})\n"
        "        |\n"
        "        | Inclusion/exclusion criteria applied\n"
        "        v\n"
        "  Eligible patients (n={n_eligible})\n"
        "        |\n"
        "        | Excluded: {n_excluded} ({exclusion_reason})\n"
        "        v\n"
        "  Final analysis cohort (n={n_analyzed})\n"
    ),
    "rct_schema": (
        "Randomized Controlled Trial Schema\n"
        "  Eligible patients (n={n_eligible})\n"
        "        |\n"
        "        | 1:{ratio} randomization\n"
        "        |\n"
        "   ------+------\n"
        "   |            |\n"
        "   v            v\n"
        " Arm A        Arm B\n"
        " {arm_a}     {arm_b}\n"
        " (n={n_arm_a}) (n={n_arm_b})\n"
        "        |\n"
        " Primary endpoint: {primary_endpoint}\n"
    ),
    "treatment_schema": (
        "Treatment Schema\n"
        "  Cycle length: {cycle_length} days\n"
        "  Day 1:        {drug_a} {dose_a}\n"
        "  Days {days_b}: {drug_b} {dose_b}\n"
        "  Repeat every {cycle_length} days × {n_cycles} cycles\n"
        "  Primary endpoint: {primary_endpoint}\n"
    ),
    "pathway": (
        "Molecular Pathway\n"
        "  {upstream}\n"
        "      |\n"
        "      v\n"
        "  {kinase} <--- [Inhibited by {drug}]\n"
        "      |\n"
        "      v\n"
        "  {downstream}\n"
        "      |\n"
        "      v\n"
        "  Apoptosis / Growth arrest\n"
    ),
    "phase1_dose_escalation": (
        "Phase 1 BOIN Dose-Escalation Schema\n"
        "  Dose Level 1: {dose_1}\n"
        "  Dose Level 2: {dose_2}\n"
        "  Dose Level 3: {dose_3} (target)\n"
        "  Dose Level 4: {dose_4}\n"
        "  Target DLT rate: {target_dlt}%\n"
        "  DLT window: {dlt_window}\n"
        "  RP2D determination: {rp2d_method}\n"
    ),
}


class ScientificSchematist(SkillBase):
    """
    Generates text-based study design schematics and flowcharts.
    Writes to context.figure_descriptions.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ScientificSchematist] {prompt[:200]}"
        except Exception:
            return ""

    def generate_diagram(
        self,
        diagram_type: str,
        **placeholders,
    ) -> str:
        """
        Generate a text-based schematic diagram.

        Args:
            diagram_type: study_flow | rct_schema | treatment_schema | pathway |
                          phase1_dose_escalation
            **placeholders: Values to fill template variables

        Returns:
            str: ASCII schematic diagram.
            Appends to context.figure_descriptions.
        """
        try:
            template = _DIAGRAM_TEMPLATES.get(diagram_type)
            if not template:
                diagram = f"[{diagram_type.replace('_', ' ').title()} schematic]\n"
            else:
                from tools.skills.scientific_writer import _SafeFormatMap
                diagram = template.format_map(_SafeFormatMap(placeholders))

            self.context.figure_descriptions.append(diagram)
            self._log.info(
                "ScientificSchematist.generate_diagram: type='%s'", diagram_type
            )
            return diagram
        except Exception as exc:
            self._log.warning("ScientificSchematist.generate_diagram failed: %s", exc)
            return ""

    def list_diagram_types(self) -> list[str]:
        """Return available diagram types."""
        return list(_DIAGRAM_TEMPLATES.keys())
