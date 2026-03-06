"""
ScientificVisualizer — Scientific Skills Integration
Maps to: scientific-visualization OpenCode skill
HPW Phases: 4 (Manuscript Prep), 9 (Publication)

Generates figure descriptions and visualization specifications
for hematology manuscripts.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

_FIGURE_TYPES: dict[str, dict] = {
    "kaplan_meier": {
        "description": "Kaplan–Meier survival curve",
        "axes": "Time (months) on x-axis; Probability on y-axis (0–1)",
        "required": [
            "n at risk table",
            "median with 95% CI",
            "log-rank p-value",
            "censoring marks",
        ],
    },
    "bar_chart": {
        "description": "Grouped bar chart",
        "axes": "Category on x-axis; Value (%) on y-axis",
        "required": ["error bars (SD or 95% CI)", "sample sizes", "p-values for comparisons"],
    },
    "forest_plot": {
        "description": "Forest plot for meta-analysis or subgroup analysis",
        "axes": "Hazard ratio / OR on x-axis (log scale); Study/subgroup on y-axis",
        "required": [
            "individual estimates with 95% CI",
            "pooled estimate diamond",
            "heterogeneity I²",
            "weights",
        ],
    },
    "waterfall": {
        "description": "Waterfall plot of best tumor/disease response",
        "axes": "Patient ID on x-axis; % change from baseline on y-axis",
        "required": [
            "response threshold lines (e.g., -30% for PR)",
            "color coding by response category",
        ],
    },
    "swimmer": {
        "description": "Swimmer plot of treatment duration and response",
        "axes": "Patient ID on y-axis; Time (months) on x-axis",
        "required": [
            "response markers",
            "censoring indicators",
            "treatment interruptions",
        ],
    },
    "consort": {
        "description": "CONSORT flow diagram",
        "axes": "None (flowchart)",
        "required": [
            "enrollment numbers",
            "randomization",
            "allocation",
            "follow-up losses",
            "analysis numbers",
        ],
    },
}

_FIGURE_LEGENDS: dict[str, str] = {
    "kaplan_meier": (
        "Figure {n}. {title}. Kaplan–Meier estimates of {endpoint} in {n_patients} patients "
        "with {disease} treated with {treatment}. The number of patients at risk is shown "
        "below the x-axis. Vertical tick marks indicate censored observations. "
        "Median {endpoint} was {median} months (95% CI, {ci_lower}–{ci_upper} months). "
        "{group_comparison}"
    ),
    "bar_chart": (
        "Figure {n}. {title}. {description}. Error bars represent {error_type}. "
        "Comparisons were performed using {test}. *p<0.05; **p<0.01; ***p<0.001."
    ),
    "forest_plot": (
        "Figure {n}. {title}. Forest plot of {outcome} across {context}. "
        "Diamonds represent pooled estimates. Squares are proportional to study weights. "
        "Heterogeneity: I²={i2}%, p={p_het}."
    ),
    "waterfall": (
        "Figure {n}. {title}. Maximum percent change from baseline in {endpoint} "
        "for each patient (n={n_patients}). Dashed lines indicate response thresholds. "
        "Colors represent best overall response category."
    ),
}


class ScientificVisualizer(SkillBase):
    """
    Generates figure specifications and legend templates for hematology manuscripts.
    Writes to context.figure_descriptions.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ScientificVisualizer] {prompt[:200]}"
        except Exception:
            return ""

    def describe_figure(
        self,
        figure_type: str,
        title: str = "",
        **placeholders,
    ) -> str:
        """
        Generate a figure description and legend template.

        Args:
            figure_type: kaplan_meier | bar_chart | forest_plot | waterfall | swimmer | consort
            title: Figure title
            **placeholders: Template values (n, endpoint, disease, treatment, etc.)

        Returns:
            str: Figure legend template.
            Appends to context.figure_descriptions.
        """
        try:
            spec = _FIGURE_TYPES.get(figure_type)
            if not spec:
                description = f"[{figure_type.replace('_', ' ').title()} figure] {title}"
            else:
                template = _FIGURE_LEGENDS.get(figure_type, "")
                if template:
                    from tools.skills.scientific_writer import _SafeFormatMap
                    all_placeholders = {"title": title, **placeholders}
                    description = template.format_map(_SafeFormatMap(all_placeholders))
                else:
                    req = ", ".join(spec.get("required", []))
                    description = (
                        f"{spec['description']}: {title}. "
                        f"Required elements: {req}."
                    )

            self.context.figure_descriptions.append(description)
            self._log.info(
                "ScientificVisualizer.describe_figure: type='%s', %d chars",
                figure_type, len(description),
            )
            return description
        except Exception as exc:
            self._log.warning("ScientificVisualizer.describe_figure failed: %s", exc)
            return ""

    def get_figure_requirements(self, figure_type: str) -> dict:
        """Return technical requirements for a figure type."""
        try:
            return dict(_FIGURE_TYPES.get(figure_type, {}))
        except Exception:
            return {}

    def list_figure_types(self) -> list[str]:
        """Return available figure types."""
        return list(_FIGURE_TYPES.keys())

    def generate_figure_list(self) -> str:
        """Generate a figure list from all accumulated descriptions."""
        try:
            if not self.context.figure_descriptions:
                return ""
            lines = ["Figure List", ""]
            for i, desc in enumerate(self.context.figure_descriptions, 1):
                first_sentence = desc.split(".")[0] + "."
                lines.append(f"Figure {i}. {first_sentence}")
            return "\n".join(lines)
        except Exception as exc:
            self._log.warning("generate_figure_list failed: %s", exc)
            return ""
