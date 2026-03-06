"""
ContentResearcher — Tier 1 CSA Scientific Skill (Post-analysis)

Links R output statistics to guideline citations and reference anchors.
Returns citation suggestions keyed to stat categories found in key_statistics.

Maps to: literature-review OpenCode skill
CSA Hook: integrate_skills_post_analysis()
"""

from __future__ import annotations

from ._base import CSASkillBase, CSASkillContext

# Maps stat_key prefix/pattern → (citation_label, reference_text)
_GUIDELINE_CITATIONS: dict[str, tuple[str, str]] = {
    "eln_":      ("ELN 2022 AML",
                  "Döhner H, et al. Diagnosis and management of AML in adults: "
                  "2022 ELN recommendations. Blood. 2022;140(12):1345-1377."),
    "ccr_":      ("ELN 2022 AML",
                  "Döhner H, et al. Diagnosis and management of AML in adults: "
                  "2022 ELN recommendations. Blood. 2022;140(12):1345-1377."),
    "cr_rate":   ("ELN 2022 AML",
                  "Döhner H, et al. Diagnosis and management of AML in adults: "
                  "2022 ELN recommendations. Blood. 2022;140(12):1345-1377."),
    "cri_":      ("ELN 2022 AML",
                  "Döhner H, et al. Diagnosis and management of AML in adults: "
                  "2022 ELN recommendations. Blood. 2022;140(12):1345-1377."),
    "boin_":     ("BOIN Design",
                  "Liu S, Yuan Y. Bayesian optimal interval designs for phase I "
                  "clinical trials. J R Stat Soc C. 2015;64(3):507-523."),
    "target_dlt":("BOIN Design",
                  "Liu S, Yuan Y. Bayesian optimal interval designs for phase I "
                  "clinical trials. J R Stat Soc C. 2015;64(3):507-523."),
    "mmr_":      ("ELN 2020 CML",
                  "Hochhaus A, et al. European LeukemiaNet 2020 recommendations "
                  "for treating chronic myeloid leukemia. Leukemia. 2020;34(4):966-984."),
    "tfr_":      ("ELN 2020 CML",
                  "Hochhaus A, et al. European LeukemiaNet 2020 recommendations "
                  "for treating chronic myeloid leukemia. Leukemia. 2020;34(4):966-984."),
    "sokal_":    ("Sokal Score",
                  "Sokal JE, et al. Prognostic discrimination in 'good-risk' chronic "
                  "granulocytic leukemia. Blood. 1984;63(4):789-799."),
    "agvhd_":    ("NIH 2014 GVHD",
                  "Przepiorka D, et al. NIH Consensus Development Project on Criteria "
                  "for Clinical Trials in Chronic GVHD: I. Diagnosis and Staging. "
                  "Biol Blood Marrow Transplant. 2015;21(3):389-401."),
    "cgvhd_":    ("NIH 2014 GVHD",
                  "Jagasia MH, et al. National Institutes of Health Consensus Development "
                  "Project on Criteria for Clinical Trials in Chronic GVHD: I. "
                  "The 2014 Diagnosis and Staging Working Group Report. "
                  "Biol Blood Marrow Transplant. 2015;21(3):389-401."),
    "grfs_":     ("GRFS Definition",
                  "Holtan SG, et al. Composite end point of graft-versus-host disease-free, "
                  "relapse-free survival after allogeneic hematopoietic cell transplantation. "
                  "Blood. 2015;125(8):1333-1338."),
    "ae_grade3": ("CTCAE v5",
                  "National Cancer Institute. Common Terminology Criteria for Adverse Events "
                  "(CTCAE) version 5.0. 2017. https://ctep.cancer.gov/protocoldevelopment/"
                  "electronic_applications/ctc.htm"),
    "os_":       ("Survival Analysis",
                  "Kaplan EL, Meier P. Nonparametric estimation from incomplete observations. "
                  "J Am Stat Assoc. 1958;53(282):457-481."),
    "n_total":   ("CONSORT/STROBE",
                  "von Elm E, et al. The Strengthening the Reporting of Observational Studies "
                  "in Epidemiology (STROBE) Statement. PLoS Med. 2007;4(10):e296."),
}


class ContentResearcher(CSASkillBase):
    """
    Links key_statistics to guideline citations.
    Returns list of relevant references for the analysis.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ContentResearcher] {prompt[:200]}"
        except Exception:
            return ""

    def find_citations(self) -> list:
        """
        Match key_statistics keys to guideline citations.

        Returns:
            list[str]: Unique reference strings relevant to extracted statistics.
        """
        try:
            seen_labels: set[str] = set()
            refs: list[str] = []

            for stat_key in self.context.key_statistics:
                for pattern, (label, citation) in _GUIDELINE_CITATIONS.items():
                    if stat_key.startswith(pattern) or stat_key == pattern:
                        if label not in seen_labels:
                            seen_labels.add(label)
                            refs.append(citation)
                        break

            # Always include Fine-Gray if competing risks used (HCT)
            if self.context.disease == "hct" and "Fine-Gray" not in str(refs):
                refs.append(
                    "Fine JP, Gray RJ. A proportional hazards model for the subdistribution "
                    "of a competing risk. J Am Stat Assoc. 1999;94(446):496-509."
                )

            self._log.info("ContentResearcher: found %d citations", len(refs))
            return refs

        except Exception as exc:
            self._log.warning("ContentResearcher.find_citations failed: %s", exc)
            return []

    def get_disease_guidelines(self, disease: str) -> list:
        """Return primary guideline references for a disease."""
        try:
            disease_refs = {
                "aml": [
                    "Döhner H, et al. Blood. 2022;140(12):1345-1377. [ELN 2022]",
                    "Arber DA, et al. Blood. 2022;140(11):1200-1228. [WHO 2022]",
                ],
                "cml": [
                    "Hochhaus A, et al. Leukemia. 2020;34(4):966-984. [ELN 2020]",
                ],
                "mds": [
                    "Greenberg PL, et al. Blood. 2012;120(12):2454-2465. [IPSS-R]",
                    "Cheson BD, et al. Blood. 2006;108(2):419-425. [IWG 2006]",
                ],
                "hct": [
                    "Jagasia MH, et al. Biol Blood Marrow Transplant. 2015;21(3):389-401. [NIH 2014]",
                    "Holtan SG, et al. Blood. 2015;125(8):1333-1338. [GRFS]",
                ],
            }
            return disease_refs.get(disease.lower(), [])
        except Exception:
            return []
