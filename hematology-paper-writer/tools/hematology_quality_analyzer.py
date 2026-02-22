from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class HematologyCheckType(Enum):
    CLASSIFICATION_ACCURACY = "classification_accuracy"
    GVHD_COMPLIANCE = "gvhd_compliance"
    THERAPEUTIC_ALIGNMENT = "therapeutic_alignment"
    NOMENCLATURE = "nomenclature"
    GENE_FUSION_NOTATION = "gene_fusion"
    CYTOGENETIC_NOTATION = "cytogenetic"
    RESPONSE_CRITERIA = "response_criteria"


@dataclass
class HematologyIssue:
    check_type: HematologyCheckType
    severity: str
    location: str
    issue: str
    correction: str
    explanation: str


@dataclass
class ClassificationReport:
    entity_mentioned: str
    classification_system: Optional[str]
    issues: List[HematologyIssue] = field(default_factory=list)
    compliant: bool = True


@dataclass
class GVHDComplianceReport:
    criteria_system: Optional[str]
    organs_assessed: List[str] = field(default_factory=list)
    staging_details: List[str] = field(default_factory=list)
    issues: List[HematologyIssue] = field(default_factory=list)
    compliant: bool = True


@dataclass
class TherapeuticReport:
    disease: str
    response_criteria_version: Optional[str] = None
    treatment_mentioned: List[str] = field(default_factory=list)
    issues: List[HematologyIssue] = field(default_factory=list)
    compliant: bool = True


class HematologyQualityAnalyzer:
    WHO_2022_ENTITIES = [
        "AML with NPM1 mutation",
        "AML with CEBPA mutation",
        "AML with RUNX1::RUNX1T1",
        "AML with CBFB::MYH11",
        "AML with PML::RARA",
        "AML with KMT2A rearrangement",
        "AML with MECOM rearrangement",
        "AML with BCR::ABL1",
        "AML with NUP98 rearrangement",
        "AML with DEK::NUP214",
        "AML with RBM15::MRTFA",
        "AML with FLT3-ITD",
    ]

    GENE_FUSION_PATTERNS = {
        r"BCR-ABL1?": "BCR::ABL1",
        r"BCR/ABL": "BCR::ABL1",
        r"PML-RARA?": "PML::RARA",
        r"PML/RARA": "PML::RARA",
        r"RUNX1-RUNX1T1": "RUNX1::RUNX1T1",
        r"CBFB-MYH11": "CBFB::MYH11",
        r"DEK-NUP214": "DEK::NUP214",
        r"MLLT3-KMT2A": "MLLT3::KMT2A",
        r"ETV6-RUNX1": "ETV6::RUNX1",
    }

    ISCN_PATTERNS = {
        r"t\((\d+);(\d+)\)(?!\()": "Incomplete translocation notation - add band details",
        r"del\((\d+)\)(?!q|p)": "Incomplete deletion notation - specify arm (q or p)",
        r"inv\((\d+)\)(?!\()": "Incomplete inversion notation - add band details",
        r"complex karyotype(?! \()": "Define complex karyotype as ≥3 abnormalities",
    }

    ELN_VERSIONS = {
        "AML": ["2022"],
        "CML": ["2025", "2020"],
    }

    def __init__(self):
        self.issues_found: List[HematologyIssue] = []

    def analyze_classification_accuracy(self, text: str) -> ClassificationReport:
        report = ClassificationReport(entity_mentioned="", classification_system=None)

        who_mentioned = "WHO 2022" in text or "WHO 5th" in text
        icc_mentioned = "ICC 2022" in text or "ICC" in text

        if who_mentioned:
            report.classification_system = "WHO 2022"
        elif icc_mentioned:
            report.classification_system = "ICC 2022"

        if not who_mentioned and not icc_mentioned:
            if "AML" in text or "MDS" in text or "CML" in text:
                report.issues.append(
                    HematologyIssue(
                        check_type=HematologyCheckType.CLASSIFICATION_ACCURACY,
                        severity="warning",
                        location="Methods",
                        issue="Classification system not specified",
                        correction="Specify WHO 2022 or ICC 2022 classification system",
                        explanation="Current manuscripts should reference 2022 classification systems",
                    )
                )
                report.compliant = False

        for entity in self.WHO_2022_ENTITIES:
            if entity.lower() in text.lower():
                report.entity_mentioned = entity

        if "AML" in text and "defining genetic abnormalities" not in text.lower():
            if "recurrent genetic abnormalities" in text.lower():
                report.issues.append(
                    HematologyIssue(
                        check_type=HematologyCheckType.CLASSIFICATION_ACCURACY,
                        severity="warning",
                        location="Terminology",
                        issue="Outdated terminology: 'recurrent genetic abnormalities'",
                        correction="Use 'defining genetic abnormalities' (WHO 2022)",
                        explanation="WHO 2022 changed terminology from 'recurrent' to 'defining'",
                    )
                )

        return report

    def analyze_gvhd_compliance(self, text: str) -> GVHDComplianceReport:
        report = GVHDComplianceReport(criteria_system=None)

        if "GVHD" not in text:
            return report

        magic_mentioned = "MAGIC" in text or "Mount Sinai" in text
        nih_mentioned = "NIH" in text and "consensus" in text.lower()

        if magic_mentioned and nih_mentioned:
            report.criteria_system = "Both MAGIC and NIH"
        elif magic_mentioned:
            report.criteria_system = "MAGIC"
        elif nih_mentioned:
            report.criteria_system = "NIH"
        else:
            report.issues.append(
                HematologyIssue(
                    check_type=HematologyCheckType.GVHD_COMPLIANCE,
                    severity="error",
                    location="Methods",
                    issue="GVHD criteria system not specified",
                    correction="Specify MAGIC criteria for acute GVHD or NIH criteria for chronic GVHD",
                    explanation="Standardized criteria required for reproducibility",
                )
            )
            report.compliant = False

        organs = ["skin", "liver", "GI", "gut", "mouth", "eyes", "lung"]
        for organ in organs:
            if organ.lower() in text.lower():
                report.organs_assessed.append(organ)

        if len(report.organs_assessed) < 2 and report.criteria_system:
            report.issues.append(
                HematologyIssue(
                    check_type=HematologyCheckType.GVHD_COMPLIANCE,
                    severity="info",
                    location="Methods",
                    issue="Limited organ assessment described",
                    correction="Consider assessing all potentially involved organs",
                    explanation="Comprehensive GVHD assessment typically includes multiple organs",
                )
            )

        return report

    def analyze_therapeutic_alignment(
        self, text: str, disease: Optional[str] = None
    ) -> TherapeuticReport:
        report = TherapeuticReport(disease=disease or "Unknown")

        if not disease:
            if "AML" in text:
                report.disease = "AML"
            elif "CML" in text:
                report.disease = "CML"

        if report.disease == "AML":
            if "ELN 2022" in text:
                report.response_criteria_version = "ELN 2022"
            elif "ELN 2017" in text:
                report.issues.append(
                    HematologyIssue(
                        check_type=HematologyCheckType.THERAPEUTIC_ALIGNMENT,
                        severity="warning",
                        location="Methods",
                        issue="Using outdated ELN 2017 criteria",
                        correction="Update to ELN 2022 response criteria",
                        explanation="ELN 2022 updated response criteria for AML",
                    )
                )
                report.compliant = False

        elif report.disease == "CML":
            if "ELN 2025" in text or "ELN 2020" in text:
                report.response_criteria_version = "ELN 2025"
            elif "ELN 2013" in text or "ELN 2006" in text:
                report.issues.append(
                    HematologyIssue(
                        check_type=HematologyCheckType.THERAPEUTIC_ALIGNMENT,
                        severity="warning",
                        location="Methods",
                        issue="Using outdated ELN criteria",
                        correction="Update to ELN 2025 response criteria",
                        explanation="ELN 2025 updated treatment milestones for CML",
                    )
                )
                report.compliant = False

        response_terms = [
            "complete remission",
            "CR",
            "partial remission",
            "PR",
            "overall response",
        ]
        if any(term in text for term in response_terms):
            if not report.response_criteria_version:
                report.issues.append(
                    HematologyIssue(
                        check_type=HematologyCheckType.THERAPEUTIC_ALIGNMENT,
                        severity="warning",
                        location="Methods",
                        issue="Response criteria specified but version not mentioned",
                        correction=f"Specify ELN {self.ELN_VERSIONS.get(report.disease, ['current'])[0]} response criteria",
                        explanation="Response criteria version required for reproducibility",
                    )
                )

        return report

    def analyze_nomenclature(self, text: str) -> List[HematologyIssue]:
        issues = []

        for pattern, correction in self.GENE_FUSION_PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                issues.append(
                    HematologyIssue(
                        check_type=HematologyCheckType.GENE_FUSION_NOTATION,
                        severity="error",
                        location=f"Position {match.start()}",
                        issue=f"Old fusion notation: '{match.group()}'",
                        correction=f"Use ISCN 2024 double colon: {correction}",
                        explanation="ISCN 2024 requires double colon notation for gene fusions",
                    )
                )

        for pattern, explanation in self.ISCN_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issues.append(
                    HematologyIssue(
                        check_type=HematologyCheckType.CYTOGENETIC_NOTATION,
                        severity="warning",
                        location=f"Position {match.start()}",
                        issue=f"Incomplete cytogenetic notation: '{match.group()}'",
                        correction="Add complete band details using ISCN 2024 format",
                        explanation=explanation,
                    )
                )

        gene_symbols = [
            "NPM1",
            "FLT3",
            "TP53",
            "CEBPA",
            "IDH1",
            "IDH2",
            "ASXL1",
            "DNMT3A",
            "TET2",
        ]
        for gene in gene_symbols:
            if re.search(rf"\b{gene}\b(?![*])", text):
                if f"*{gene}*" not in text:
                    issues.append(
                        HematologyIssue(
                            check_type=HematologyCheckType.NOMENCLATURE,
                            severity="info",
                            location="Throughout",
                            issue=f"Gene symbol {gene} not italicized",
                            correction=f"Italicize gene symbols: *{gene}*",
                            explanation="Gene symbols should be italicized per HGVS recommendations",
                        )
                    )

        return issues

    def generate_full_hematology_report(self, text: str) -> Dict[str, Any]:
        classification = self.analyze_classification_accuracy(text)
        gvhd = self.analyze_gvhd_compliance(text)
        therapeutic = self.analyze_therapeutic_alignment(text)
        nomenclature = self.analyze_nomenclature(text)

        all_issues = (
            classification.issues + gvhd.issues + therapeutic.issues + nomenclature
        )

        errors = [i for i in all_issues if i.severity == "error"]
        warnings = [i for i in all_issues if i.severity == "warning"]
        infos = [i for i in all_issues if i.severity == "info"]

        return {
            "classification": {
                "entity": classification.entity_mentioned,
                "system": classification.classification_system,
                "compliant": classification.compliant,
            },
            "gvhd": {
                "criteria_system": gvhd.criteria_system,
                "organs_assessed": gvhd.organs_assessed,
                "compliant": gvhd.compliant,
            },
            "therapeutic": {
                "disease": therapeutic.disease,
                "response_criteria": therapeutic.response_criteria_version,
                "compliant": therapeutic.compliant,
            },
            "nomenclature": {
                "issues_count": len(nomenclature),
                "gene_fusion_errors": len(
                    [
                        i
                        for i in nomenclature
                        if i.check_type == HematologyCheckType.GENE_FUSION_NOTATION
                    ]
                ),
            },
            "summary": {
                "total_issues": len(all_issues),
                "errors": len(errors),
                "warnings": len(warnings),
                "infos": len(infos),
                "compliant": len(errors) == 0,
            },
            "all_issues": all_issues,
        }


if __name__ == "__main__":
    analyzer = HematologyQualityAnalyzer()

    sample_text = """
    Patients with AML were classified according to WHO 2022 criteria.
    BCR-ABL fusion was detected by FISH. The t(9;22) translocation was present.
    Response was assessed using ELN 2022 criteria.
    """

    print("=" * 60)
    print("Hematology Quality Analysis")
    print("=" * 60)

    report = analyzer.generate_full_hematology_report(sample_text)

    print(f"\nClassification System: {report['classification']['system']}")
    print(f"Disease: {report['therapeutic']['disease']}")
    print(f"Response Criteria: {report['therapeutic']['response_criteria']}")

    print(f"\nSummary:")
    print(f"  Total Issues: {report['summary']['total_issues']}")
    print(f"  Errors: {report['summary']['errors']}")
    print(f"  Warnings: {report['summary']['warnings']}")
    print(f"  Compliant: {report['summary']['compliant']}")

    if report["all_issues"]:
        print(f"\nIssues Found:")
        for issue in report["all_issues"]:
            print(f"  [{issue.severity.upper()}] {issue.check_type.value}")
            print(f"    Issue: {issue.issue}")
            print(f"    Correction: {issue.correction}")
            print()
