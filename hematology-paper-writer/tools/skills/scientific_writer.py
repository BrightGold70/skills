"""
ScientificWriter — Scientific Skills Integration
Maps to: scientific-writing OpenCode skill
HPW Phases: 4 (Manuscript Prep), 4.5 (Updating)

Provides section-level writing templates and prose guidance for hematology manuscripts.
"""

from __future__ import annotations

from ._base import SkillBase, SkillContext

# IMRaD section templates (academic style)
# Each template is multi-paragraph (paragraphs separated by \n\n).
# Minimum 5 sentences per paragraph. Missing placeholders render as {placeholder}.
_SECTION_TEMPLATES: dict[str, str] = {
    "introduction": (
        # Para 1: disease burden + pathobiology
        "{disease} is a {disease_type} characterized by {pathobiology}, with an annual incidence of "
        "{incidence_context}. "
        "The molecular hallmark, {molecular_marker}, arises from {cytogenetic_event} and drives "
        "constitutive activation of downstream proliferative signaling pathways. "
        "Prior to the introduction of effective targeted therapy, the median survival for patients with "
        "{disease} was measured in years, and treatment options were largely limited to {pre_tki_treatment}. "
        "The introduction of {first_tki} in {approval_year} fundamentally altered the natural history of "
        "this disease, with current 10-year survival rates exceeding 90% in adherent patients [1]. "
        "Despite this progress, a meaningful subset of patients experience primary resistance, acquired "
        "resistance, or treatment intolerance, underscoring the persistent unmet need for additional "
        "therapeutic options [2].\n\n"
        # Para 2: treatment landscape evolution
        "The therapeutic landscape for {disease} has expanded substantially over the past two decades. "
        "{first_tki}, the first approved {drug_class}, established proof of concept for molecular targeted "
        "therapy and remains a widely used frontline option owing to its favorable long-term tolerability "
        "profile. "
        "Second-generation agents — {second_gen_tkis} — were subsequently developed to overcome "
        "{first_tki} resistance mediated by BCR::ABL1 kinase domain mutations and to achieve deeper "
        "molecular responses in the frontline setting [3]. "
        "Third-generation {drug_class} agents, including {third_gen_tkis}, were introduced to address "
        "resistance conferred by the T315I 'gatekeeper' mutation, which remains recalcitrant to all "
        "earlier-generation agents. "
        "Nevertheless, patients who have exhausted multiple lines of therapy face limited options, and the "
        "cumulative toxicity burden from sequential TKI use represents a growing clinical concern [4]. "
        "The development of agents with novel mechanisms of action is therefore of considerable interest "
        "in the field.\n\n"
        # Para 3: the intervention + prior evidence
        "{intervention} represents a mechanistically distinct approach to {disease} treatment. "
        "Unlike ATP-competitive {drug_class} inhibitors, {intervention} binds to the myristoyl pocket of "
        "BCR::ABL1, inducing an inactive kinase conformation through an allosteric mechanism; this mode "
        "of inhibition confers activity against the majority of resistance-conferring kinase domain "
        "mutations, including T315I at higher doses [5]. "
        "In the pivotal {pivotal_trial} trial, {intervention} demonstrated {pivotal_result} compared with "
        "{comparator} in patients with {trial_population}, establishing its clinical utility in this "
        "difficult-to-treat population [6]. "
        "Subsequent real-world analyses and expanded access data have suggested that these benefits may "
        "generalize beyond the controlled trial setting, though heterogeneity in patient populations and "
        "follow-up duration limits cross-study comparisons [7]. "
        "Despite this growing body of evidence, no comprehensive systematic synthesis has integrated "
        "findings across all available studies to provide robust estimates of efficacy and safety.\n\n"
        # Para 4: rationale for review + study aim (prose, no bullets)
        "This systematic review was conducted to address this evidence gap and to provide clinicians with "
        "an integrated, critically appraised synthesis of the available literature on {intervention} in "
        "{disease}. "
        "We evaluated the efficacy and safety of {intervention} compared with standard {drug_class} "
        "therapy, placebo, or best available care in adults with {disease}, with {primary_endpoint} as "
        "the primary outcome and {secondary_endpoints} as secondary outcomes. "
        "The review was conducted and reported in accordance with the Preferred Reporting Items for "
        "Systematic Reviews and Meta-Analyses (PRISMA) 2020 guidelines [8]. "
        "The aim of this study was to {study_aim}."
    ),

    "objectives": (
        # Prose paragraph — objectives stated as sentences, not a bulleted list
        "This {study_type} aimed to {primary_objective}. "
        "The primary objective was to {primary_objective_detail}, assessed by {primary_endpoint} "
        "at {assessment_timepoint}. "
        "Secondary objectives included characterizing {secondary_objective_1}, evaluating "
        "{secondary_objective_2}, and identifying patient subgroups who may derive differential "
        "benefit from {intervention}. "
        "Safety objectives encompassed a comprehensive assessment of adverse events, treatment "
        "discontinuation rates, and dose modifications across the included study populations. "
        "These objectives were pre-specified in the protocol and registered with {registry} prior "
        "to data collection."
    ),

    "pico": (
        # PICO as a single descriptive prose paragraph — never as labeled bullets
        "This {study_type} evaluated the efficacy and safety of {intervention} at any approved dose "
        "as monotherapy in adults with {disease}, compared with {comparator}, with "
        "{primary_endpoint} at {assessment_timepoint} as the primary outcome. "
        "The population of interest comprised adults aged 18 years or older with "
        "Philadelphia chromosome-positive {disease} confirmed according to {diagnostic_criteria}, "
        "including patients across all lines of therapy unless otherwise specified. "
        "The primary outcome was {primary_endpoint}; secondary outcomes included "
        "{secondary_endpoints}. "
        "This PICO framework was defined a priori in the registered protocol and remained "
        "unchanged throughout the review process."
    ),

    "inclusion_criteria": (
        # Prose paragraph — never a bulleted sub-list
        "We included {study_design_types} enrolling adults aged 18 years or older with "
        "Philadelphia chromosome-positive {disease} confirmed by {diagnostic_method}. "
        "Eligible studies were required to evaluate {intervention} at any approved or "
        "investigational dose as monotherapy, administered in comparison with {comparator}, "
        "and to report at least one pre-specified efficacy or safety endpoint with a minimum "
        "follow-up of {min_followup}. "
        "Studies published in peer-reviewed journals in any language were eligible, and "
        "non-English publications were translated where feasible. "
        "No restrictions were placed on geographic region, institution type, or sample size, "
        "with the exception of the minimum participant threshold described below."
    ),

    "exclusion_criteria": (
        # Prose paragraph continuing from inclusion paragraph
        "We excluded case reports and case series enrolling fewer than {min_n} participants, "
        "given the limited statistical precision of estimates from such studies. "
        "Animal studies, in vitro experiments, and pharmacokinetic studies without clinical "
        "efficacy or safety data were not eligible. "
        "Conference abstracts, letters, and editorials without accompanying peer-reviewed "
        "full-text publication were excluded, as were duplicate publications reporting data "
        "from the same patient cohort; in cases of overlapping cohorts, the publication "
        "with the longest follow-up or largest sample was retained. "
        "Studies that did not report any quantitative outcome data were also excluded."
    ),

    "information_sources": (
        # Prose sentences — never a bullet list of databases
        "We conducted a systematic search of PubMed/MEDLINE, Embase, Cochrane Central "
        "Register of Controlled Trials (CENTRAL), and Web of Science Core Collection "
        "from inception through {search_date}, with no date restrictions applied. "
        "Grey literature was systematically searched through ClinicalTrials.gov and the "
        "WHO International Clinical Trials Registry Platform (ICTRP) to identify "
        "completed and ongoing registered trials. "
        "Conference proceedings from the American Society of Hematology (ASH), European "
        "Hematology Association (EHA), and American Society of Clinical Oncology (ASCO) "
        "annual meetings from the past five years were hand-searched for relevant abstracts "
        "subsequently published as full-text articles. "
        "Reference lists of all included studies and relevant systematic reviews were "
        "manually screened to identify additional eligible publications not captured by "
        "the electronic search."
    ),

    "study_selection": (
        "Two independent reviewers ({reviewer_role_1} and {reviewer_role_2}) screened all "
        "titles and abstracts identified by the search against the pre-specified eligibility "
        "criteria using a standardized screening form. "
        "Full-text articles were retrieved for all potentially eligible records and "
        "independently assessed for inclusion by both reviewers. "
        "Discrepancies at either stage were resolved through discussion and, where consensus "
        "could not be reached, by adjudication from a third independent reviewer. "
        "Inter-rater reliability at the full-text screening stage was calculated using "
        "Cohen's kappa coefficient. "
        "The complete study selection process is documented in a PRISMA 2020 flow diagram "
        "(Figure 1), which details the number of records identified, screened, assessed for "
        "eligibility, and ultimately included."
    ),

    "methods": (
        # Para 1: study design + registration
        "This systematic review was conducted and reported in accordance with the Preferred "
        "Reporting Items for Systematic Reviews and Meta-Analyses (PRISMA) 2020 statement [1] "
        "and was registered prospectively with {registry} (Registration Number: {reg_number}) "
        "prior to data collection. "
        "We included {study_design} of patients with {disease} treated {institution_context} "
        "between {start_year} and {end_year}. "
        "Eligibility criteria, outcomes, and analysis methods were pre-specified in the "
        "registered protocol and no post hoc modifications were made.\n\n"
        # Para 2: eligibility
        "We included {study_design_types} enrolling adults aged 18 years or older with "
        "{disease} confirmed by {diagnostic_method}. "
        "Eligible studies evaluated {intervention} compared with {comparator} and reported "
        "at least one pre-specified efficacy or safety endpoint with a minimum follow-up of "
        "{min_followup}. "
        "Case reports, animal studies, and conference abstracts without peer-reviewed "
        "full-text publication were excluded, as were duplicate publications from the "
        "same cohort.\n\n"
        # Para 3: search + data extraction
        "Two independent reviewers screened all records and extracted data using a "
        "standardized extraction form. "
        "The primary endpoint was {primary_endpoint}. "
        "Secondary endpoints included {secondary_endpoints}. "
        "Discrepancies were resolved by consensus or third-reviewer adjudication. "
        "Risk of bias was assessed using {rob_tool} for randomized trials and "
        "{rob_tool_observational} for observational studies.\n\n"
        # Para 4: statistical analysis
        "Statistical analyses were performed using {software} (version {version}). "
        "{statistical_test} was used to compare {comparison_groups}. "
        "Heterogeneity was quantified using the I² statistic; values greater than 50% "
        "were considered indicative of substantial heterogeneity, prompting sensitivity "
        "analyses and pre-specified subgroup analyses to explore potential sources. "
        "Publication bias was assessed using funnel plot asymmetry and Egger's test "
        "where ten or more studies contributed to a meta-analytic estimate."
    ),

    "results": (
        # Para 1: study selection + characteristics
        "The systematic search identified {total_screened} records, of which "
        "{n_full_text} were assessed for full-text eligibility and {n} studies "
        "{enrollment_context} met the inclusion criteria (Figure 1). "
        "The included studies enrolled a total of {total_patients} patients "
        "(range, {patient_range} per study) with a median follow-up of {median_followup}. "
        "Baseline characteristics across the included studies are summarized in Table 1; "
        "{baseline_balance_comment}. "
        "Inter-rater reliability at the full-text screening stage was good "
        "(Cohen's kappa = {kappa}).\n\n"
        # Para 2: primary outcome
        "{intervention} demonstrated {primary_result_description} with regard to the "
        "primary endpoint of {primary_endpoint}. "
        "Specifically, {primary_result} (95% CI, {ci}; p={p_value}), representing "
        "an absolute difference of {absolute_difference} compared with {comparator}. "
        "This difference was {consistency_statement} across the included studies "
        "(I² = {heterogeneity}%). "
        "The clinical significance of this magnitude of improvement is underscored by "
        "{clinical_significance_context}, as {clinical_relevance_elaboration}.\n\n"
        # Para 3: secondary outcomes
        "Regarding secondary endpoints, {secondary_result_1} and {secondary_result_2}. "
        "Treatment-free remission was evaluable in {tfr_eligible} studies and was "
        "achieved in {tfr_rate}% of patients who met eligibility criteria for "
        "discontinuation, {tfr_context}. "
        "Progression to accelerated or blast phase occurred in {progression_rate}% of "
        "patients across studies, {progression_context}.\n\n"
        # Para 4: safety
        "The safety profile of {intervention} was characterized by {safety_summary}. "
        "Grade ≥3 adverse events occurred in {ae_rate}% of patients, most commonly "
        "{common_ae} ({common_ae_rate}%) and {second_ae} ({second_ae_rate}%). "
        "Treatment discontinuation due to adverse events was observed in {dc_rate}% "
        "of patients receiving {intervention} compared with {comparator_dc_rate}% in "
        "the {comparator} group, {tolerability_interpretation}. "
        "No treatment-related deaths were reported in {safety_death_context}."
    ),

    "discussion": (
        # Para 1: summary of main findings
        "In this {study_design}, we demonstrate that {key_finding}. "
        "The primary outcome, {primary_endpoint}, was {primary_result} (95% CI, {ci}), "
        "representing a clinically meaningful absolute improvement of {absolute_difference} "
        "over {comparator}. "
        "Secondary analyses corroborated this primary finding, with {secondary_result_1} "
        "and {secondary_result_2} both favoring {intervention}. "
        "The safety profile was consistent with the known pharmacological mechanism of "
        "{intervention} and did not reveal any previously uncharacterized toxicity signals. "
        "Taken together, these findings position {intervention} as an important option "
        "for {clinical_position_statement}.\n\n"
        # Para 2: contextualization against prior literature
        "These results are consistent with {supporting_literature}, and extend prior "
        "findings by {novel_contribution}. "
        "The {primary_endpoint} of {primary_result} is broadly comparable to that "
        "reported by {prior_author} et al. ({prior_year}), who documented {prior_result} "
        "in a similar population, though differences in {methodological_difference} "
        "may account for the observed variation between estimates [ref]. "
        "In contrast, {discordant_study} reported {discordant_result}; this discordance "
        "is most plausibly attributable to {discordance_explanation}, which may have "
        "{discordance_directional_impact} response rates in that cohort. "
        "The consistency of our findings across studies with differing designs and patient "
        "populations strengthens the robustness of the pooled estimate.\n\n"
        # Para 3: mechanistic/biological interpretation
        "The observed superiority of {intervention} over {comparator} is mechanistically "
        "plausible given the distinct mode of action of {intervention}. "
        "Unlike ATP-competitive inhibitors, which are subject to displacement by kinase "
        "domain mutations at the ATP-binding site, {intervention} engages the myristoyl "
        "pocket, inducing an allosteric conformational change that abrogates kinase "
        "activity irrespective of most resistance-associated mutations [ref]. "
        "This mechanism is particularly relevant in the {treatment_line} setting, where "
        "the prevalence of BCR::ABL1 kinase domain mutations is {mutation_prevalence}, "
        "and where prior TKI exposure may have selected for resistant clones [ref]. "
        "The safety advantage of {intervention} may similarly reflect reduced off-target "
        "kinase inhibition, as the myristoyl-binding mechanism avoids the promiscuous "
        "kinase inhibition associated with {comparator}-class compounds.\n\n"
        # Para 4: limitations
        "Interpretation of these results should be tempered by several important limitations. "
        "{limitations}. "
        "The {principal_limitation} is the principal methodological concern and may have "
        "{limitation_directional_impact} the estimated treatment effect. "
        "Additionally, {second_limitation}, which limits generalizability to "
        "{generalizability_statement}. "
        "Heterogeneity across included studies (I² = {heterogeneity}%) suggests that "
        "the pooled estimate should be interpreted with caution and may not apply "
        "uniformly to all patient subgroups.\n\n"
        # Para 5: future directions + conclusion
        "Several important questions remain unresolved and warrant dedicated investigation. "
        "{future_question_1}. "
        "Ongoing trials, including {ongoing_trial} (NCT{nct_number}), are expected to "
        "provide more definitive data on {future_endpoint} in {future_population}. "
        "In conclusion, {conclusion_statement}, supporting {clinical_implication}. "
        "Further {future_direction} is warranted to optimize patient selection and "
        "treatment sequencing in this evolving landscape."
    ),

    "abstract": (
        "Background: {background_statement}. "
        "{disease_context}. "
        "{treatment_gap}.\n"
        "Methods: {study_design_brief} was conducted including {n} patients with {disease}. "
        "{search_strategy_brief}. "
        "The primary endpoint was {primary_endpoint}.\n"
        "Results: {n_included} studies enrolling {total_patients} patients were included. "
        "{primary_result} (95% CI, {ci}; p={p_value}). "
        "{secondary_result}. "
        "Grade ≥3 adverse events occurred in {ae_rate}% of patients, most commonly {common_ae}. "
        "{safety_context}.\n"
        "Conclusions: {conclusion_statement}. "
        "{clinical_implication}. "
        "Further {future_direction} is warranted."
    ),

    "conclusion": (
        "{intervention} demonstrates {efficacy_summary} with an acceptable safety profile "
        "in patients with {disease}, as evidenced by {key_evidence}. "
        "The {primary_result_plain} observed in this {study_design} are consistent with "
        "the known pharmacological properties of {intervention} and corroborate findings "
        "from prior studies in this population. "
        "These findings support {clinical_implication} and suggest that {intervention} "
        "should be considered as a treatment option for {eligible_population}. "
        "Prospective randomized data from ongoing trials will be critical to confirm "
        "these estimates and to guide optimal treatment sequencing. "
        "Further {future_direction} is warranted to refine patient selection criteria "
        "and to evaluate long-term outcomes including treatment-free remission."
    ),
}

_STYLE_MODIFIERS: dict[str, str] = {
    "academic": "Use passive voice, avoid first-person where possible, cite all factual claims.",
    "clinical": "Use active voice, emphasize patient outcomes, use clinical terminology.",
    "journalistic": "Use clear language accessible to non-specialist clinicians.",
}


class ScientificWriter(SkillBase):
    """
    Provides IMRaD section templates and prose guidance for hematology manuscripts.
    Writes results to context.draft_sections[section].
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ScientificWriter] {prompt[:200]}"
        except Exception:
            return ""

    def write_section(
        self,
        section: str,
        outline: str = "",
        style: str = "academic",
        **placeholders,
    ) -> str:
        """
        Generate a prose template for an IMRaD section.

        Args:
            section: Section name — "introduction", "methods", "results",
                     "discussion", "abstract", "conclusion"
            outline: Optional additional context/outline points to incorporate
            style: "academic" | "clinical" | "journalistic"
            **placeholders: Template variable values (e.g., disease="AML", n="120")

        Returns:
            str: Prose template with filled or bracketed placeholders.
                 Writes to context.draft_sections[section].
        """
        try:
            key = section.lower().strip()
            template = _SECTION_TEMPLATES.get(key, "")

            if not template:
                # Generic template for unlisted sections
                text = (
                    f"[{section.title()} section] {outline}\n"
                    f"Style guide: {_STYLE_MODIFIERS.get(style, '')}"
                )
            else:
                # Fill provided placeholders; leave missing as {placeholder}
                try:
                    text = template.format_map(_SafeFormatMap(placeholders))
                except Exception:
                    text = template

                if outline:
                    text = f"{text}\n\nAdditional points to address: {outline}"

            self.context.draft_sections[key] = text
            self._log.info("ScientificWriter: drafted section '%s' (%d chars)", key, len(text))
            return text

        except Exception as exc:
            self._log.warning("ScientificWriter.write_section failed: %s", exc)
            return ""

    def get_section_guidance(self, section: str, journal: str = "") -> str:
        """Return prose writing guidance for a section."""
        try:
            guidance = {
                "introduction": (
                    "4 paragraphs (min 600 words, target 780): "
                    "(1) disease burden + pathobiology, "
                    "(2) treatment landscape evolution with specific trial data, "
                    "(3) intervention mechanism + prior evidence + evidence gap, "
                    "(4) rationale for review + PICO as prose sentence + study aim. "
                    "No bullet points. Minimum 5 sentences per paragraph."
                ),
                "objectives": (
                    "One prose paragraph (5 sentences). State primary objective, primary endpoint, "
                    "secondary objectives, safety objectives, and registration. "
                    "NEVER format as a numbered or bulleted list."
                ),
                "pico": (
                    "One prose paragraph (4 sentences). Weave Population/Intervention/Comparison/Outcome "
                    "into a single descriptive paragraph ending with outcome statement. "
                    "NEVER use bold labels or bullet formatting."
                ),
                "inclusion_criteria": (
                    "One prose paragraph (4-5 sentences). Cover: study design types, population with "
                    "diagnostic criteria, intervention requirements, comparator, outcome reporting, "
                    "and language/publication requirements. NEVER use bullet sub-lists."
                ),
                "exclusion_criteria": (
                    "One prose paragraph (4 sentences) continuing from inclusion. Cover: minimum N, "
                    "non-clinical study types, publication types excluded, duplicate handling. "
                    "NEVER use bullet formatting."
                ),
                "information_sources": (
                    "2-3 prose sentences. Name all electronic databases searched with date range as a "
                    "sentence. Add grey literature sentence. Add reference list hand-searching sentence. "
                    "NEVER use a bullet list of database names."
                ),
                "study_selection": (
                    "One prose paragraph (5 sentences): two-reviewer process, full-text assessment, "
                    "discrepancy resolution, kappa coefficient, PRISMA flow reference. "
                    "NEVER use a numbered step list."
                ),
                "methods": (
                    "Past tense throughout. 4 paragraphs (min 800 words, target 1050): "
                    "(1) design + PRISMA registration, (2) eligibility as prose, "
                    "(3) search + data extraction, (4) statistical analysis with heterogeneity handling. "
                    "No bullet lists anywhere in methods."
                ),
                "results": (
                    "Past tense. 4 paragraphs (min 900 words, target 1200): "
                    "(1) study selection + PRISMA numbers + baseline characteristics, "
                    "(2) primary outcome with CI + absolute difference + clinical significance, "
                    "(3) secondary outcomes including TFR + progression, "
                    "(4) safety with grade ≥3 rates + discontinuation comparison. "
                    "Every data point must be followed by an interpretation sentence."
                ),
                "discussion": (
                    "5 paragraphs (min 900 words, target 1200): "
                    "(1) summary of main findings — quantified, (2) contextualization with named prior "
                    "studies and specific values, (3) mechanistic interpretation, "
                    "(4) limitations with directional impact stated, "
                    "(5) future directions + conclusion with clinical implication."
                ),
                "abstract": (
                    "Structured 4-part: Background/Methods/Results/Conclusions. "
                    "Target 95-100% of journal word limit (minimum 220 words). "
                    "Results must include specific numbers, CIs, and p-values. "
                    "NEVER use placeholder sentences ('A [study design] was conducted')."
                ),
                "conclusion": (
                    "1-2 paragraphs (min 150 words, target 200). State key finding + quantify it. "
                    "Connect to prior literature. State clinical implication. "
                    "Name future research direction specifically."
                ),
            }
            base = guidance.get(section.lower(), f"Write {section} in flowing academic prose. "
                                "Minimum 5 sentences per paragraph. No bullet points.")
            if journal:
                base += f" Follow {journal} specific formatting requirements."
            return base
        except Exception as exc:
            self._log.warning("get_section_guidance failed: %s", exc)
            return ""

    def list_sections(self) -> list[str]:
        """Return list of available section templates."""
        return list(_SECTION_TEMPLATES.keys())


class _SafeFormatMap(dict):
    """dict subclass that returns '{key}' for missing keys instead of raising KeyError."""
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"
