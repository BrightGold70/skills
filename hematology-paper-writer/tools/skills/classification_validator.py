"""
ClassificationValidator — Scientific Skills Integration
Maps to: hpw-classification-validator feature
HPW Phases: 1 (disease detection), 4 (methods prose + results table), 4.7 (nomenclature check)

Ports classification logic from HemaCalc iOS app:
  - MyeloidClassifier.classifyAMLWHO / ICCClassifier.classifyAMLICC
  - ELN2022Calculator (AML risk)
  - CMLResponseCalculator (ELN 2025 milestones)
  - Acute/Chronic GVHD grading (NIH 2014)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ._base import SkillBase, SkillContext

_log = logging.getLogger(__name__)

# ── Citation Registry ──────────────────────────────────────────────────────────

_CITATIONS: Dict[str, str] = {
    "who_ref":       "Khoury JD, et al. Leukemia. 2022;36(7):1703-19",
    "icc_ref":       "Arber DA, et al. Blood. 2022;140(11):1200-28",
    "eln_ref":       "Döhner H, et al. Blood. 2022;140(12):1345-77",
    "eln_cml_ref":   "Apperley JF, et al. Leukemia. 2025;39(8):1797-813",
    "glucksberg_ref":"Przepiorka D, et al. Bone Marrow Transplant. 1995;15(6):825-8",
    "nih_gvhd_ref":  "Jagasia MH, et al. Biol Blood Marrow Transplant. 2015;21(3):389-401",
}

# ── Methods Prose Templates ────────────────────────────────────────────────────

_METHODS_TEMPLATES: Dict[str, str] = {
    "AML": (
        "Patients were classified according to the 2022 World Health Organization "
        "(WHO) Classification of Haematolymphoid Tumours [{who_ref}] and the "
        "International Consensus Classification (ICC) 2022 [{icc_ref}]. "
        "Risk stratification followed the European LeukemiaNet (ELN) 2022 "
        "recommendations [{eln_ref}]. Discordant cases between the two classification "
        "systems were identified and adjudicated based on the predominant genetic "
        "and morphologic features."
    ),
    "CML": (
        "Treatment response was assessed at 3, 6, and 12 months according to the "
        "2025 European LeukemiaNet (ELN) recommendations for the management of "
        "chronic myeloid leukemia [{eln_cml_ref}]. Optimal response, warning, and "
        "failure criteria were applied per ELN 2025 definitions. "
        "BCR::ABL1 transcript levels are reported on the International Scale (IS)."
    ),
    "HCT": (
        "Acute graft-versus-host disease (GVHD) was graded according to the modified "
        "Glucksberg criteria [{glucksberg_ref}]. Chronic GVHD was classified per "
        "NIH 2014 consensus criteria [{nih_gvhd_ref}] as mild, moderate, or severe "
        "based on the global severity score."
    ),
}

# ── CML ELN 2025 Milestone Thresholds ─────────────────────────────────────────
# BCR::ABL1 IS %: (optimal_max, warning_max)
# Values above warning_max = Failure

_CML_THRESHOLDS: Dict[int, Dict[str, float]] = {
    3:  {"optimal": 10.0, "warning": 10.0},   # ≤10% optimal; >10% = warning → failure by CHR
    6:  {"optimal": 1.0,  "warning": 10.0},
    12: {"optimal": 0.1,  "warning": 1.0},
    18: {"optimal": 0.1,  "warning": 1.0},
    24: {"optimal": 0.1,  "warning": 1.0},
}

_CML_RECOMMENDATIONS: Dict[str, str] = {
    "Optimal": "Continue current TKI; reassess at next milestone.",
    "Warning": "Increase monitoring frequency; consider mutation analysis. "
               "TKI switch may be warranted if warning persists.",
    "Failure": "Change TKI; perform BCR::ABL1 kinase domain mutation testing. "
               "Consider allogeneic HCT evaluation.",
}

# ── ELN 2022 AML Risk Constants ────────────────────────────────────────────────

_FAVORABLE_CYTOGENETICS = {"t(8;21)", "inv(16)", "t(16;16)", "t(15;17)"}
_ADVERSE_CYTOGENETICS   = {"complex", "monosomal", "adverse",
                           "inv(3)", "t(3;3)", "t(6;9)", "t(9;22)"}


# ── Output Data Classes ────────────────────────────────────────────────────────

@dataclass
class AMLClassificationResult:
    who_2022: str
    icc_2022: str
    eln_2022_risk: str
    eln_factors: List[str] = field(default_factory=list)
    is_concordant: bool = True
    discordance_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CMLMilestoneResult:
    months: int
    bcr_abl_is: float
    status: str           # "Optimal" | "Warning" | "Failure"
    threshold_optimal: float
    threshold_warning: float
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GVHDResult:
    gvhd_type: str        # "acute" | "chronic"
    grade: str            # acute: "0"/"I"/"II"/"III"/"IV"; chronic: "None"/"Mild"/"Moderate"/"Severe"
    organ_scores: Dict[str, int] = field(default_factory=dict)
    overall_score: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DiscordanceReport:
    concordant_n: int
    discordant_n: int
    discordant_pairs: List[Dict[str, Any]]
    total_n: int
    concordance_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Main Skill Class ───────────────────────────────────────────────────────────

class ClassificationValidator(SkillBase):
    """
    Runtime WHO 2022 / ICC 2022 AML classifier, ELN 2025 CML milestone assessor,
    and NIH GVHD grader. Generates manuscript methods prose and results tables.
    Writes classification_summary to CSA hpw_manifest.json.

    All methods fail silently — returns empty/default on any exception.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ClassificationValidator] {prompt[:200]}"
        except Exception:
            return ""

    # ── AML Classification ─────────────────────────────────────────────────────

    def classify_aml(self, data: Dict[str, Any]) -> AMLClassificationResult:
        """
        Classify a single AML patient per WHO 2022 and ICC 2022.

        Args:
            data: AMLPatientData dict (all fields optional; absent = False/0.0).
                  Keys: blasts_pct, cytogenetics, npm1, flt3_itd,
                        flt3_itd_allelic_ratio, cebpa_bzip, runx1, asxl1, tp53,
                        mds_related_changes, therapy_related, down_syndrome

        Returns:
            AMLClassificationResult with WHO/ICC entity, ELN risk, concordance.
        """
        try:
            blasts      = float(data.get("blasts_pct", 0.0))
            cyto        = str(data.get("cytogenetics", "intermediate")).lower()
            npm1        = bool(data.get("npm1", False))
            flt3_itd    = bool(data.get("flt3_itd", False))
            ar           = float(data.get("flt3_itd_allelic_ratio", 0.0))
            cebpa       = bool(data.get("cebpa_bzip", False))
            runx1       = bool(data.get("runx1", False))
            asxl1       = bool(data.get("asxl1", False))
            tp53        = bool(data.get("tp53", False))
            mds_related = bool(data.get("mds_related_changes", False))
            therapy_rel = bool(data.get("therapy_related", False))
            down_syn    = bool(data.get("down_syndrome", False))

            # ── WHO 2022 (priority order) ──────────────────────────────────────
            who = self._classify_aml_who(
                blasts, cyto, npm1, flt3_itd, ar, cebpa, runx1, asxl1,
                tp53, mds_related, therapy_rel, down_syn,
            )

            # ── ICC 2022 ───────────────────────────────────────────────────────
            icc = self._classify_aml_icc(
                blasts, cyto, npm1, flt3_itd, ar, cebpa, runx1, asxl1,
                tp53, mds_related, therapy_rel, down_syn,
            )

            # ── ELN 2022 risk ──────────────────────────────────────────────────
            risk, factors = self._eln2022_risk(
                cyto, npm1, flt3_itd, ar, cebpa, runx1, asxl1, tp53,
            )

            # ── Concordance ────────────────────────────────────────────────────
            concordant = (who == icc)
            reason = ""
            if not concordant:
                reason = self._discordance_reason(who, icc, blasts, tp53, npm1)

            result = AMLClassificationResult(
                who_2022=who,
                icc_2022=icc,
                eln_2022_risk=risk,
                eln_factors=factors,
                is_concordant=concordant,
                discordance_reason=reason,
            )

            # Persist latest single classification to context
            self.context.classification_result["last_aml"] = result.to_dict()
            self._log.info("classify_aml: who=%s icc=%s eln=%s", who, icc, risk)
            return result

        except Exception as exc:
            self._log.warning("classify_aml failed: %s", exc)
            return AMLClassificationResult(
                who_2022="Unknown", icc_2022="Unknown", eln_2022_risk="Unknown"
            )

    def _classify_aml_who(
        self, blasts, cyto, npm1, flt3_itd, ar, cebpa,
        runx1, asxl1, tp53, mds_related, therapy_rel, down_syn,
    ) -> str:
        """WHO 2022 AML classification — priority-ordered rules."""
        if therapy_rel:
            return "AML, therapy-related"
        if down_syn:
            return "ML-DS"
        if "t(8;21)" in cyto or "runx1::runx1t1" in cyto:
            return "AML with RUNX1::RUNX1T1"
        if "inv(16)" in cyto or "t(16;16)" in cyto or "cbfb::myh11" in cyto:
            return "AML with CBFB::MYH11"
        if "t(15;17)" in cyto or "pml::rara" in cyto:
            return "APL with PML::RARA"
        if npm1:
            return "AML with NPM1 mutation"
        if cebpa:
            return "AML with CEBPA mutation"
        if tp53 and blasts >= 20:
            return "AML with TP53 mutation"
        if mds_related or runx1 or asxl1:
            return "AML, myelodysplasia-related"
        if blasts >= 20:
            return "AML NOS"
        # blasts 10–19% without defining abnormality
        return "MDS with excess blasts (WHO 2022)"

    def _classify_aml_icc(
        self, blasts, cyto, npm1, flt3_itd, ar, cebpa,
        runx1, asxl1, tp53, mds_related, therapy_rel, down_syn,
    ) -> str:
        """ICC 2022 AML classification — divergence rules vs WHO."""
        if therapy_rel:
            return "AML, therapy-related"
        if down_syn:
            return "ML-DS"
        if "t(8;21)" in cyto or "runx1::runx1t1" in cyto:
            return "AML with RUNX1::RUNX1T1"
        if "inv(16)" in cyto or "t(16;16)" in cyto or "cbfb::myh11" in cyto:
            return "AML with CBFB::MYH11"
        if "t(15;17)" in cyto or "pml::rara" in cyto:
            return "APL with PML::RARA"
        # ICC: NPM1 requires blasts ≥10%
        if npm1 and blasts >= 10:
            return "AML with NPM1 mutation"
        if cebpa:
            return "AML with CEBPA mutation"
        # ICC: TP53 with blasts 10–19% → MDS/AML category
        if tp53 and 10 <= blasts < 20:
            return "MDS/AML"
        if tp53 and blasts >= 20:
            return "AML with TP53 mutation"
        # ICC: MDS-related mutations with blasts 10–19% → MDS/AML
        if (mds_related or runx1 or asxl1) and 10 <= blasts < 20:
            return "MDS/AML"
        if mds_related or runx1 or asxl1:
            return "AML, myelodysplasia-related"
        if blasts >= 20:
            return "AML NOS"
        return "MDS/AML"

    def _eln2022_risk(
        self, cyto, npm1, flt3_itd, ar, cebpa, runx1, asxl1, tp53,
    ) -> tuple[str, List[str]]:
        """ELN 2022 AML risk stratification. Returns (risk_category, factors)."""
        factors: List[str] = []

        # Adverse trumps all
        is_adverse_cyto = any(a in cyto for a in _ADVERSE_CYTOGENETICS)
        if is_adverse_cyto:
            factors.append(f"Adverse cytogenetics ({cyto})")
        if tp53:
            factors.append("TP53 mutated")
        if runx1:
            factors.append("RUNX1 mutated")
        if asxl1:
            factors.append("ASXL1 mutated")

        if is_adverse_cyto or tp53 or runx1 or asxl1:
            return "Adverse", factors

        # Favorable
        is_favorable_cyto = any(f in cyto for f in _FAVORABLE_CYTOGENETICS)
        npm1_favorable = npm1 and (not flt3_itd or ar < 0.5)

        if is_favorable_cyto:
            factors.append(f"Favorable cytogenetics ({cyto})")
        if npm1_favorable:
            ratio_note = f", AR={ar:.2f}" if flt3_itd else ""
            factors.append(f"NPM1 mutated (favorable profile{ratio_note})")
        if cebpa:
            factors.append("CEBPA bZIP mutated")

        if is_favorable_cyto or npm1_favorable or cebpa:
            return "Favorable", factors

        factors.append("Intermediate risk profile")
        return "Intermediate", factors

    def _discordance_reason(
        self, who: str, icc: str, blasts: float, tp53: bool, npm1: bool,
    ) -> str:
        """Human-readable explanation for WHO/ICC discordance."""
        if "MDS/AML" in icc and tp53 and blasts < 20:
            return f"TP53 mutation with blasts {blasts:.0f}% (10–19%): ICC classifies as MDS/AML"
        if "MDS/AML" in icc and blasts < 20:
            return f"MDS-related features with blasts {blasts:.0f}% (10–19%): ICC classifies as MDS/AML"
        if npm1 and blasts < 10:
            return f"NPM1 mutation with blasts {blasts:.0f}% (<10%): ICC requires ≥10% blasts"
        return f"WHO: {who} / ICC: {icc}"

    # ── Cohort-level comparison ────────────────────────────────────────────────

    def compare_who_icc(
        self, results: List[AMLClassificationResult],
    ) -> DiscordanceReport:
        """
        Build a cohort-level discordance summary from a list of classified patients.

        Args:
            results: List of AMLClassificationResult from classify_aml()

        Returns:
            DiscordanceReport with counts and discordant pair breakdown.
        """
        try:
            total = len(results)
            if total == 0:
                return DiscordanceReport(0, 0, [], 0, 1.0)

            concordant = sum(1 for r in results if r.is_concordant)
            discordant_list = [r for r in results if not r.is_concordant]

            # Group discordant pairs
            pair_counts: Dict[str, Dict[str, Any]] = {}
            for r in discordant_list:
                key = f"{r.who_2022}||{r.icc_2022}"
                if key not in pair_counts:
                    pair_counts[key] = {
                        "who": r.who_2022, "icc": r.icc_2022,
                        "n": 0, "reason": r.discordance_reason,
                    }
                pair_counts[key]["n"] += 1

            report = DiscordanceReport(
                concordant_n=concordant,
                discordant_n=len(discordant_list),
                discordant_pairs=list(pair_counts.values()),
                total_n=total,
                concordance_rate=concordant / total,
            )

            self.context.classification_result["concordance_report"] = report.to_dict()
            return report

        except Exception as exc:
            self._log.warning("compare_who_icc failed: %s", exc)
            return DiscordanceReport(0, 0, [], 0, 1.0)

    # ── CML Milestone Assessment ───────────────────────────────────────────────

    def classify_cml_milestone(self, data: Dict[str, Any]) -> CMLMilestoneResult:
        """
        Assess CML treatment response at a given timepoint per ELN 2025.

        Args:
            data: CMLMilestoneData dict.
                  Keys: months (int), bcr_abl_is (float 0–100),
                        achieved_chr (bool), ph_positive_pct (float)

        Returns:
            CMLMilestoneResult with Optimal/Warning/Failure status.
        """
        try:
            months     = int(data.get("months", 12))
            bcr_abl    = float(data.get("bcr_abl_is", 100.0))
            achieved_chr = bool(data.get("achieved_chr", True))
            ph_pct     = float(data.get("ph_positive_pct", 100.0))

            # Snap to nearest defined timepoint
            defined = sorted(_CML_THRESHOLDS.keys())
            nearest = min(defined, key=lambda m: abs(m - months))
            thresh  = _CML_THRESHOLDS[nearest]

            opt = thresh["optimal"]
            warn = thresh["warning"]

            # Determine status
            if not achieved_chr:
                status = "Failure"
            elif bcr_abl <= opt:
                status = "Optimal"
            elif bcr_abl <= warn:
                status = "Warning"
            else:
                status = "Failure"

            result = CMLMilestoneResult(
                months=months,
                bcr_abl_is=bcr_abl,
                status=status,
                threshold_optimal=opt,
                threshold_warning=warn,
                recommendation=_CML_RECOMMENDATIONS.get(status, ""),
            )

            # Persist to context
            milestones = self.context.classification_result.setdefault("cml_milestones", {})
            milestones[f"{months}m"] = result.to_dict()

            self._log.info("classify_cml_milestone: %dm BCR::ABL1=%.3f%% → %s",
                           months, bcr_abl, status)
            return result

        except Exception as exc:
            self._log.warning("classify_cml_milestone failed: %s", exc)
            return CMLMilestoneResult(
                months=0, bcr_abl_is=0.0, status="Unknown",
                threshold_optimal=0.0, threshold_warning=0.0,
            )

    # ── GVHD Grading ──────────────────────────────────────────────────────────

    def classify_gvhd(self, data: Dict[str, Any]) -> GVHDResult:
        """
        Grade GVHD per NIH 2014 (chronic) or Glucksberg (acute).

        Args:
            data: GVHDData dict.
                  type: "acute"|"chronic"
                  Acute: skin_stage, liver_stage, gut_stage (0–4)
                  Chronic: skin_score, mouth_score, eye_score, gi_score,
                           liver_score_chronic, lung_score, joint_score,
                           genital_score, ps_score (0–3)

        Returns:
            GVHDResult with grade string and organ breakdown.
        """
        try:
            gvhd_type = str(data.get("type", "acute")).lower()

            if gvhd_type == "acute":
                return self._grade_acute_gvhd(data)
            else:
                return self._grade_chronic_gvhd(data)

        except Exception as exc:
            self._log.warning("classify_gvhd failed: %s", exc)
            return GVHDResult(gvhd_type="unknown", grade="Unknown")

    def _grade_acute_gvhd(self, data: Dict[str, Any]) -> GVHDResult:
        """Glucksberg / modified criteria for acute GVHD."""
        skin  = int(data.get("skin_stage", 0))
        liver = int(data.get("liver_stage", 0))
        gut   = int(data.get("gut_stage", 0))

        organ_scores = {"skin": skin, "liver": liver, "gut": gut}

        # Overall grade per Glucksberg / modified Seattle criteria.
        # Grade III requires multi-organ: skin ≥2 WITH liver or gut ≥2.
        # Skin stage 2 alone (no internal organ involvement) = Grade I.
        if skin == 4 or liver == 4 or gut == 4:
            grade_str, grade_int = "IV", 4
        elif skin >= 2 and (liver >= 2 or gut >= 2):
            grade_str, grade_int = "III", 3
        elif liver >= 1 or gut >= 1:
            grade_str, grade_int = "II", 2
        elif skin >= 1:
            grade_str, grade_int = "I", 1
        else:
            grade_str, grade_int = "0", 0

        result = GVHDResult(
            gvhd_type="acute",
            grade=grade_str,
            organ_scores=organ_scores,
            overall_score=grade_int,
        )

        gvhd_ctx = self.context.classification_result.setdefault("gvhd_grades", {})
        gvhd_ctx.setdefault("acute", {})[grade_str] = (
            gvhd_ctx.get("acute", {}).get(grade_str, 0) + 1
        )
        return result

    def _grade_chronic_gvhd(self, data: Dict[str, Any]) -> GVHDResult:
        """NIH 2014 global severity score for chronic GVHD."""
        organ_keys = [
            "skin_score", "mouth_score", "eye_score", "gi_score",
            "liver_score_chronic", "lung_score", "joint_score",
            "genital_score",
        ]
        scores = {k: int(data.get(k, 0)) for k in organ_keys}
        lung_score = scores.get("lung_score", 0)

        organs_affected = sum(1 for v in scores.values() if v >= 1)
        max_score = max(scores.values(), default=0)

        # NIH 2014 severity
        if max_score >= 3 or lung_score >= 2:
            grade_str, grade_int = "Severe", 3
        elif organs_affected >= 3 or max_score >= 2 or lung_score == 1:
            grade_str, grade_int = "Moderate", 2
        elif organs_affected >= 1:
            grade_str, grade_int = "Mild", 1
        else:
            grade_str, grade_int = "None", 0

        result = GVHDResult(
            gvhd_type="chronic",
            grade=grade_str,
            organ_scores=scores,
            overall_score=grade_int,
        )

        gvhd_ctx = self.context.classification_result.setdefault("gvhd_grades", {})
        gvhd_ctx.setdefault("chronic", {})[grade_str] = (
            gvhd_ctx.get("chronic", {}).get(grade_str, 0) + 1
        )
        return result

    # ── Prose Generation ───────────────────────────────────────────────────────

    def generate_methods_paragraph(
        self,
        disease: str,
        n_patients: int = 0,
    ) -> str:
        """
        Generate a methods paragraph for the classification system used.

        Args:
            disease: "AML" | "CML" | "HCT" (case-insensitive)
            n_patients: Cohort size (included if > 0)

        Returns:
            Prose paragraph string with embedded citations.
        """
        try:
            key = disease.upper().strip()
            if key not in _METHODS_TEMPLATES:
                return ""

            template = _METHODS_TEMPLATES[key]
            paragraph = template.format(**_CITATIONS)

            if n_patients > 0:
                paragraph = f"A total of {n_patients} patients were included. " + paragraph

            # Persist to draft_sections
            section_key = f"methods_classification_{key.lower()}"
            self.context.draft_sections[section_key] = paragraph
            return paragraph

        except Exception as exc:
            self._log.warning("generate_methods_paragraph failed: %s", exc)
            return ""

    def generate_results_table(
        self,
        results: List[AMLClassificationResult],
    ) -> str:
        """
        Generate a markdown table of WHO/ICC classification results.

        Args:
            results: List of AMLClassificationResult objects.

        Returns:
            Markdown-formatted table string.
        """
        try:
            if not results:
                return ""

            lines = [
                "| WHO 2022 | ICC 2022 | ELN 2022 Risk | Concordant |",
                "|----------|----------|---------------|------------|",
            ]
            for r in results:
                concordant_str = "Yes" if r.is_concordant else "No"
                lines.append(
                    f"| {r.who_2022} | {r.icc_2022} | "
                    f"{r.eln_2022_risk} | {concordant_str} |"
                )
            return "\n".join(lines)

        except Exception as exc:
            self._log.warning("generate_results_table failed: %s", exc)
            return ""

    # ── CSA Manifest Output ────────────────────────────────────────────────────

    def write_to_manifest(
        self,
        manifest_path,
        summary: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append classification_summary block to CSA hpw_manifest.json.

        Args:
            manifest_path: Path to hpw_manifest.json (str or Path).
                           Created with minimal wrapper if it does not exist.
            summary: Optional pre-built summary dict. If None, builds from
                     self.context.classification_result.
        """
        try:
            path = Path(manifest_path)

            # Load existing manifest or start fresh
            if path.exists():
                existing = json.loads(path.read_text(encoding="utf-8"))
            else:
                existing = {}

            if summary is None:
                summary = self._build_manifest_summary()

            existing["classification_summary"] = summary
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(existing, indent=2, default=str),
                encoding="utf-8",
            )
            self._log.info("write_to_manifest: wrote classification_summary to %s", path)

        except Exception as exc:
            self._log.warning("write_to_manifest failed: %s", exc)

    def _build_manifest_summary(self) -> Dict[str, Any]:
        """Build classification_summary dict from current SkillContext."""
        ctx = self.context.classification_result
        return {
            "schema_version": "1.0",
            "disease": ctx.get("disease", "Unknown"),
            "n_patients": ctx.get("n_patients", 0),
            "who_2022": ctx.get("who_2022_counts", {}),
            "icc_2022": ctx.get("icc_2022_counts", {}),
            "discordant_n": ctx.get("concordance_report", {}).get("discordant_n", 0),
            "concordance_rate": ctx.get("concordance_report", {}).get("concordance_rate", None),
            "discordant_pairs": ctx.get("concordance_report", {}).get("discordant_pairs", []),
            "eln2022_risk": ctx.get("eln2022_risk_counts", {}),
            "cml_milestones": ctx.get("cml_milestones", {}),
            "gvhd_grades": ctx.get("gvhd_grades", {}),
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ── Nomenclature Check (for Phase 4.7) ────────────────────────────────────

    def check_classification_nomenclature(self, text: str) -> List[str]:
        """
        Scan manuscript text for classification nomenclature issues.

        Checks performed:
        - WHO 2022 citation present when AML classification mentioned
        - ICC 2022 citation present when ICC comparison mentioned
        - BCR::ABL1 double-colon notation (not BCR-ABL1 or BCR/ABL)
        - ELN year is 2022 (AML) or 2025 (CML) not older references

        Args:
            text: Full manuscript text.

        Returns:
            List of issue strings (empty = no issues found).
        """
        try:
            issues: List[str] = []
            text_lower = text.lower()

            # AML classification nomenclature
            if re.search(r"\baml\b|\bacute myeloid\b", text_lower):
                if "who" in text_lower and "2022" not in text:
                    issues.append(
                        "WHO classification referenced without '2022' year qualifier"
                    )
                if re.search(r"\bicc\b|\binternational consensus\b", text_lower):
                    if "arber" not in text_lower and "2022" not in text:
                        issues.append(
                            "ICC classification referenced but 2022 citation not found"
                        )

            # CML: BCR::ABL1 notation (HGVS 2024 / ISCN 2024)
            if re.search(r"bcr[\-/]abl", text_lower):
                issues.append(
                    "Found 'BCR-ABL' or 'BCR/ABL' — use 'BCR::ABL1' (HGVS 2024 double-colon notation)"
                )

            # ELN year checks
            if re.search(r"\beln\b|\beuropean leukemianet\b", text_lower):
                if re.search(r"eln\s+20(17|19|20)\b", text_lower):
                    issues.append(
                        "ELN reference appears to cite an outdated year; verify 2022 (AML) or 2025 (CML)"
                    )

            # GVHD: NIH 2014 required for chronic
            if re.search(r"chronic\s+gvhd|cgvhd", text_lower):
                if "nih" not in text_lower and "jagasia" not in text_lower:
                    issues.append(
                        "Chronic GVHD graded without NIH 2014 citation (Jagasia et al.)"
                    )

            # Persist issues to context
            existing = list(self.context.prose_issues)
            for issue in issues:
                if issue not in existing:
                    existing.append(issue)
            self.context.prose_issues = existing

            return issues

        except Exception as exc:
            self._log.warning("check_classification_nomenclature failed: %s", exc)
            return []
