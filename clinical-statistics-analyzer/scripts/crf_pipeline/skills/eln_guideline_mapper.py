"""
ELNGuidelineMapper — Tier 2 CSA Scientific Skill (Post-analysis)

Maps key_statistics values to ELN 2022 (AML), ELN 2020 (CML),
and NIH 2014 (HCT) guideline categories and annotations.
Writes a companion JSON sidecar for hpw_manifest enrichment.

Maps to: clinical-decision-support OpenCode skill
CSA Hook: integrate_skills_post_analysis()
"""

from __future__ import annotations

import json
from pathlib import Path

from ._base import CSASkillBase, CSASkillContext

# {stat_key: (guideline_label, annotation_text)}
_ELN_ANNOTATIONS: dict[str, tuple[str, str]] = {
    # AML — ELN 2022
    "eln_favorable_pct":         ("ELN 2022 AML",
                                  "Favorable risk: expected CR rate >90%, 5-yr OS >65%. "
                                  "Includes NPM1mut without FLT3-ITD, biCEBPA, core-binding factor."),
    "eln_intermediate_pct":      ("ELN 2022 AML",
                                  "Intermediate risk: neither Favorable nor Adverse per ELN 2022. "
                                  "Includes wild-type NPM1 without FLT3-ITD (normal karyotype)."),
    "eln_adverse_pct":           ("ELN 2022 AML",
                                  "Adverse risk: expected 5-yr OS <15%. "
                                  "Includes complex karyotype, TP53mut, RUNX1mut, ASXL1mut, "
                                  "FLT3-ITD (high allelic ratio), monosomal karyotype."),
    "ccr_rate":                  ("ELN 2022 AML",
                                  "Composite CR (cCR) = CR + CRi + CRh + MLFS per ELN 2022. "
                                  "Used when CR alone underestimates depth of response."),
    "cr_rate":                   ("ELN 2022 AML",
                                  "Complete remission (CR) per ELN 2022: BM blasts <5%, "
                                  "no Auer rods, ANC ≥1.0×10⁹/L, platelets ≥100×10⁹/L."),
    "cri_rate":                  ("ELN 2022 AML",
                                  "CRi (CR with incomplete count recovery): BM blasts <5% "
                                  "but ANC <1.0×10⁹/L or platelets <100×10⁹/L."),
    "target_dlt_rate":           ("BOIN Design",
                                  "Target DLT rate for BOIN dose-finding (Liu & Yuan 2015). "
                                  "Typical range 0.20–0.33. MTD defined as highest safe dose."),
    "orr":                       ("ELN 2022 AML",
                                  "ORR = CR + CRi per ELN 2022 (some centres include CRh)."),
    # CML — ELN 2020
    "mmr_12mo":                  ("ELN 2020 CML",
                                  "MMR at 12 months: BCR-ABL IS ≤0.1% (MR3). "
                                  "ELN 2020 milestone: optimal response if achieved."),
    "tfr_12mo":                  ("ELN 2020 CML",
                                  "TFR at 12 months: sustained MR4 (BCR-ABL IS ≤0.01%) "
                                  "after TKI discontinuation for ≥2 yr. ELN 2020 criterion."),
    "tfr_24mo":                  ("ELN 2020 CML",
                                  "TFR at 24 months: sustained deep MR off TKI. "
                                  "ELN 2020: major TFR landmark for phase 3 trial endpoints."),
    "sokal_high_pct":            ("Sokal Score",
                                  "Sokal high-risk: score >1.2. Associated with inferior "
                                  "cytogenetic and molecular response rates."),
    "mmr_rate":                  ("ELN 2020 CML",
                                  "MMR (MR3): BCR-ABL IS ≤0.1%. Core response milestone per ELN 2020."),
    # HCT — NIH 2014
    "agvhd_grade2_4_rate":       ("NIH 2014 GVHD",
                                  "aGVHD grade 2–4 cumulative incidence. NIH 2014 consensus: "
                                  "graded by organ (skin, liver, GI) using modified Glucksberg."),
    "agvhd_grade3_4_rate":       ("NIH 2014 GVHD",
                                  "aGVHD grade 3–4 (severe). NIH 2014: associated with "
                                  "high NRM; requires systemic immunosuppression."),
    "cgvhd_moderate_severe_rate":("NIH 2014 GVHD",
                                  "Moderate-severe chronic GVHD per NIH 2014 global severity. "
                                  "Impacts quality of life and long-term OS."),
    "grfs_12mo":                 ("GRFS",
                                  "GRFS at 12 months: freedom from grade 3–4 aGVHD, "
                                  "moderate-severe cGVHD, relapse, or death "
                                  "(Holtan et al. Blood 2015)."),
    # Cross-disease
    "ae_grade3plus_rate":        ("CTCAE v5",
                                  "Grade ≥3 adverse events per CTCAE v5.0. "
                                  "Key safety endpoint for regulatory submissions."),
    "os_median_months":          ("Survival Analysis",
                                  "Median OS with 95% CI. Primary efficacy endpoint "
                                  "in most hematology registration trials."),
    "os_hr":                     ("Cox PH Regression",
                                  "Hazard ratio for OS from Cox proportional hazards model. "
                                  "HR <1.0 favours the treatment arm."),
    "n_total":                   ("Study Size",
                                  "Total enrolled patients. Informs power and generalisability."),
}


class ELNGuidelineMapper(CSASkillBase):
    """
    Annotates key_statistics with ELN/NIH guideline context.
    Writes context.eln_annotations and a companion sidecar JSON.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ELNGuidelineMapper] {prompt[:200]}"
        except Exception:
            return ""

    def map(self, output_dir: Path | None = None) -> "CSASkillContext":
        """
        Annotate each key in context.key_statistics with ELN/NIH guideline text.
        Writes context.eln_annotations.
        Optionally writes a companion sidecar JSON if output_dir provided.

        Returns:
            Updated self.context.
        """
        try:
            annotations: dict[str, str] = {}
            for stat_key in self.context.key_statistics:
                if stat_key in _ELN_ANNOTATIONS:
                    label, text = _ELN_ANNOTATIONS[stat_key]
                    annotations[stat_key] = f"[{label}] {text}"

            self.context.eln_annotations = annotations

            if output_dir is not None:
                self._write_annotation_sidecar(Path(output_dir), annotations)

            self._log.info(
                "ELNGuidelineMapper: annotated %d/%d statistics",
                len(annotations), len(self.context.key_statistics)
            )
            return self.context

        except Exception as exc:
            self._log.warning("ELNGuidelineMapper.map failed: %s", exc)
            return self.context

    def _write_annotation_sidecar(self, output_dir: Path, annotations: dict) -> None:
        """Write data/{disease}_eln_annotations.json for downstream consumers."""
        try:
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            path = data_dir / f"{self.context.disease}_eln_annotations.json"
            path.write_text(json.dumps(annotations, indent=2, ensure_ascii=False))
            self._log.debug("ELNGuidelineMapper: wrote %s", path.name)
        except Exception as exc:
            self._log.warning("ELNGuidelineMapper sidecar write failed: %s", exc)

    def get_annotation(self, stat_key: str) -> str:
        """Return annotation text for a single stat key, or empty string."""
        try:
            if stat_key in _ELN_ANNOTATIONS:
                label, text = _ELN_ANNOTATIONS[stat_key]
                return f"[{label}] {text}"
            return ""
        except Exception:
            return ""
