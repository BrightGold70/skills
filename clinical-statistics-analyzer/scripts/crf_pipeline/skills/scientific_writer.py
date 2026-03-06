"""
ScientificWriter — Tier 1 CSA Scientific Skill (Post-analysis)

Generates Methods section prose from the statistical_plan in context.
Disease-specific templates ensure correct R package citations, guideline
references, and endpoint terminology.

Maps to: scientific-writing OpenCode skill
CSA Hook: integrate_skills_post_analysis()
"""

from __future__ import annotations

from ._base import CSASkillBase, CSASkillContext

_METHODS_BASE = (
    "All statistical analyses were performed using R (version ≥4.3.0; R Core Team). "
    "Categorical variables are summarised as counts and percentages; continuous variables "
    "as median and interquartile range (IQR). "
    "All tests were two-sided at a significance level of α=0.05. "
    "Confidence intervals (CI) were 95% unless otherwise stated."
)

_METHODS_TEMPLATES: dict[str, str] = {
    "aml": (
        "{base} "
        "Time-to-event outcomes (overall survival [OS], event-free survival [EFS]) were "
        "estimated by the Kaplan-Meier method and compared between groups using the "
        "log-rank test. Multivariable analysis used Cox proportional hazards regression; "
        "the proportional hazards assumption was verified by Schoenfeld residuals "
        "(cox.zph()). "
        "Cumulative incidence of relapse and non-relapse mortality incorporated death "
        "as a competing risk using the Fine-Gray subdistribution hazard model (cmprsk). "
        "Response rates (CR, CRi, CRh, MLFS, composite cCR) were calculated with "
        "95% Wilson score confidence intervals per ELN 2022 criteria. "
        "ELN 2022 risk stratification was applied using cytogenetic and molecular data. "
        "Adverse events were graded per CTCAE v5.0. "
        "{phase1}"
        "Analyses were performed using the survival, cmprsk, and flextable packages."
    ),
    "cml": (
        "{base} "
        "Time-to-event outcomes (OS, progression-free survival [PFS], "
        "treatment-free remission [TFR]) were estimated by the Kaplan-Meier method "
        "and compared using the log-rank test. "
        "Cox proportional hazards regression was used for multivariable analysis; "
        "the proportional hazards assumption was verified by cox.zph(). "
        "BCR-ABL transcript levels are expressed on the International Scale (IS). "
        "Response rates (CCyR, MMR, MR4, MR4.5) and ELN 2020 milestone achievement "
        "(3, 6, 12, 18 months) were calculated with 95% Wilson score CIs. "
        "Sokal, Hasford, and ELTS scores were calculated from baseline clinical variables. "
        "TFR analysis used Fine-Gray subdistribution hazard regression with relapse "
        "as the primary event and death as a competing risk. "
        "Adverse events were graded per CTCAE v5.0. "
        "Analyses used the survival and cmprsk packages."
    ),
    "mds": (
        "{base} "
        "OS and transfusion-free survival were estimated by the Kaplan-Meier method; "
        "groups were compared using the log-rank test. "
        "Haematological improvement (HI) was assessed per IWG 2006 response criteria. "
        "Response rates were reported with 95% Wilson score CIs. "
        "Cox proportional hazards regression was used for multivariable analysis "
        "(cox.zph() for PH assumption). "
        "IPSS-R risk was calculated at baseline. "
        "Adverse events were graded per CTCAE v5.0. "
        "Analyses used the survival and flextable packages."
    ),
    "hct": (
        "{base} "
        "Cumulative incidences of acute GVHD (grades 2–4 and 3–4), chronic GVHD "
        "(moderate-severe), relapse, and non-relapse mortality were estimated using "
        "the Fine-Gray subdistribution hazard model, with death or relapse as "
        "the competing risk as appropriate (cmprsk). "
        "Overall survival and GVHD-free relapse-free survival (GRFS; defined as "
        "freedom from grade 3–4 acute GVHD, moderate-severe chronic GVHD, relapse, "
        "or death) were estimated by the Kaplan-Meier method. "
        "GVHD grading followed NIH 2014 consensus criteria. "
        "Engraftment was defined as first of 3 consecutive days with ANC ≥0.5×10⁹/L "
        "(neutrophil) and platelets ≥20×10⁹/L unsupported (platelet). "
        "Cox PH regression was used for multivariable GRFS analysis (cox.zph() verified). "
        "Adverse events were graded per CTCAE v5.0. "
        "Analyses used the survival, cmprsk, and flextable packages."
    ),
}

_PHASE1_ADDITION = (
    "Dose-finding followed the Bayesian Optimal Interval (BOIN) design "
    "(Liu & Yuan 2015) with target DLT rate {target_dlt}. "
    "Dose escalation and de-escalation boundaries were calculated using the BOIN package. "
    "Operating characteristics were evaluated by Monte Carlo simulation (10,000 trials). "
)


class ScientificWriter(CSASkillBase):
    """
    Generates Methods prose from context.statistical_plan.
    Writes result to context.methods_prose.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ScientificWriter] {prompt[:200]}"
        except Exception:
            return ""

    def draft_methods(self) -> str:
        """
        Generate Methods section from context.statistical_plan.

        Returns:
            str: Methods prose. Writes to context.methods_prose.
        """
        try:
            plan = self.context.statistical_plan
            disease = plan.get("disease", self.context.disease).lower()
            study_type = plan.get("study_type", "retrospective")

            template = _METHODS_TEMPLATES.get(disease, _METHODS_TEMPLATES["aml"])

            # Phase 1 addition
            phase1_text = ""
            if study_type == "phase1":
                target_dlt = plan.get("disease_specific_methods", {}).get("target_dlt", "0.30")
                phase1_text = _PHASE1_ADDITION.format(target_dlt=target_dlt)

            prose = template.format(base=_METHODS_BASE, phase1=phase1_text).strip()

            # Append reporting guideline sentence
            guideline = plan.get("reporting_guideline", "STROBE")
            prose += f" The study is reported per {guideline} guidelines."

            self.context.methods_prose = prose
            self._log.info(
                "ScientificWriter: drafted Methods (%d chars) for %s", len(prose), disease
            )
            return prose

        except Exception as exc:
            self._log.warning("ScientificWriter.draft_methods failed: %s", exc)
            return ""

    def draft_software_statement(self) -> str:
        """Return a standalone software citation sentence."""
        try:
            plan = self.context.statistical_plan
            software = plan.get("software", ["R (survival, cmprsk, flextable)"])
            sw_str = "; ".join(software)
            return f"Statistical analyses used {sw_str} (R version ≥4.3.0)."
        except Exception as exc:
            self._log.warning("draft_software_statement failed: %s", exc)
            return ""
