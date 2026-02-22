"""
HPW Skill - Medical Nomenclature Checker
======================================
Validates gene, chromosome, and clinical terminology nomenclature.
"""

import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class NomenclatureIssue:
    """Issue found during nomenclature checking."""

    category: str
    severity: str  # "error", "warning", "info"
    original_text: str
    corrected_text: str
    explanation: str
    line_number: Optional[int] = None


class NomenclatureChecker:
    """Check medical nomenclature compliance."""

    # Gene patterns that should be italicized
    GENE_PATTERNS = {
        # Hematopoietic genes (should be italicized)
        r"\bBCR::ABL1\b": ("*BCR::ABL1*", "Fusion gene symbols should be italicized (HGVS 2024: use :: notation)"),
        r"\bNPM1\b": ("*NPM1*", "Gene symbols should be italicized"),
        r"\bFLT3\b": ("*FLT3*", "Gene symbols should be italicized"),
        r"\bTP53\b": ("*TP53*", "Gene symbols should be italicized"),
        r"\bCEBPA\b": ("*CEBPA*", "Gene symbols should be italicized"),
        r"\bRUNX1\b": ("*RUNX1*", "Gene symbols should be italicized"),
        r"\bIDH1\b": ("*IDH1*", "Gene symbols should be italicized"),
        r"\bIDH2\b": ("*IDH2*", "Gene symbols should be italicized"),
        r"\bASXL1\b": ("*ASXL1*", "Gene symbols should be italicized"),
        r"\bDNMT3A\b": ("*DNMT3A*", "Gene symbols should be italicized"),
        r"\bTET2\b": ("*TET2*", "Gene symbols should be italicized"),
        r"\bSRSF2\b": ("*SRSF2*", "Gene symbols should be italicized"),
        r"\bU2AF1\b": ("*U2AF1*", "Gene symbols should be italicized"),
        r"\bSF3B1\b": ("*SF3B1*", "Gene symbols should be italicized"),
        r"\bJAK2\b": ("*JAK2*", "Gene symbols should be italicized"),
        r"\bCALR\b": ("*CALR*", "Gene symbols should be italicized"),
        r"\bMPL\b": ("*MPL*", "Gene symbols should be italicized"),
        r"\bKMT2A\b": ("*KMT2A*", "Gene symbols should be italicized"),
        r"\bMLLT3\b": ("*MLLT3*", "Gene symbols should be italicized"),
        r"\bPML\b": ("*PML*", "Gene symbols should be italicized"),
        r"\bRARA\b": ("*RARA*", "Gene symbols should be italicized"),
        r"\bCBFB\b": ("*CBFB*", "Gene symbols should be italicized"),
        r"\bMYH11\b": ("*MYH11*", "Gene symbols should be italicized"),
        r"\bGATA1\b": ("*GATA1*", "Gene symbols should be italicized"),
        r"\bWT1\b": ("*WT1*", "Gene symbols should be italicized"),
    }

    # Cytogenetic notation patterns
    CYTOGENETIC_PATTERNS = {
        # ISCN-correct cytogenetic notation
        r"t\(\s*(\d+)\s*;\s*(\d+)\s*\)\s*\(([^)]+)\)": (
            r"t(\1;\2)(\3)",
            "Use ISCN notation: t(9;22)(q34;q11)",
        ),
        r"del\(\s*(\d+)\s*[q]*\s*\)": (
            r"del(\1q)",
            "Use complete ISCN notation: del(5q), not del(5)",
        ),
        r"-(\d+)": (r"-\1", "Numerical abnormalities: -7 not -7q"),
        r"iso\(17q\)": (r"i(17q)", "Use ISCN notation for isochromosome"),
        r"complex karyotype": (
            r"complex karyotype (≥3 abnormalities)",
            "Define complex karyotype as ≥3 abnormalities",
        ),
    }

    # Fusion gene patterns - ISCN 2024 uses double colon (::) notation
    FUSION_PATTERNS = {
        # INCORRECT patterns (BCR-ABL, BCR/ABL) should be corrected to BCR::ABL1
        r"BCR[-/]ABL1?\b": (
            "*BCR::ABL1*",
            "ISCN 2024: Use double colon notation (BCR::ABL1), not BCR-ABL or BCR/ABL",
        ),
        r"PML[-/]RARA?\b": (
            "*PML::RARA*",
            "ISCN 2024: Use double colon notation (PML::RARA)",
        ),
        r"RUNX1[-/]RUNX1T1\b": (
            "*RUNX1::RUNX1T1*",
            "ISCN 2024: Use double colon notation (RUNX1::RUNX1T1)",
        ),
        r"CBFB[-/]MYH11\b": (
            "*CBFB::MYH11*",
            "ISCN 2024: Use double colon notation (CBFB::MYH11)",
        ),
        r"DEK[-/]NUP214\b": (
            "*DEK::NUP214*",
            "ISCN 2024: Use double colon notation (DEK::NUP214)",
        ),
        r"MLLT3[-/]KMT2A\b": (
            "*MLLT3::KMT2A*",
            "ISCN 2024: Use double colon notation (MLLT3::KMT2A)",
        ),
        # Generic pattern for any gene fusion using hyphen or slash
        r"\b([A-Z][A-Z0-9]+)[-/]([A-Z][A-Z0-9]+)\b": (
            r"*\1::\2*",
            "ISCN 2024: Gene fusions use double colon notation (e.g., BCR::ABL1, RUNX1::RUNX1T1)",
        ),
    }

    # HGVS variant patterns (should trigger HGVS notation)
    HGVS_PATTERNS = {
        # c. notation patterns
        r"\bc\.\s*\d+\s*[ACGT]\s*[>]\s*[ACGT]": (None, "Valid HGVS c. notation"),
        r"\bc\.\s*\d+_\s*\d+\s*del": (None, "Valid HGVS deletion notation"),
        r"\bc\.\s*\d+_\s*\d+\s*ins": (None, "Valid HGVS insertion notation"),
        # p. notation patterns
        r"\bp\.[A-Z][a-z]{2}\s*\d+\s*[>]\s*[A-Z][a-z]{2}": (
            None,
            "Valid HGVS p. notation",
        ),
        r"\bp\.\*": (None, "Valid HGVS protein notation"),
    }

    def check_gene_nomenclature(self, text: str) -> List[NomenclatureIssue]:
        """Check gene symbol nomenclature."""
        issues = []

        for pattern, (correct, explanation) in self.GENE_PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.group() != correct:
                    issues.append(
                        NomenclatureIssue(
                            category="gene_nomenclature",
                            severity="error",
                            original_text=match.group(),
                            corrected_text=correct,
                            explanation=explanation,
                        )
                    )

        return issues

    def check_cytogenetic_nomenclature(self, text: str) -> List[NomenclatureIssue]:
        """Check cytogenetic (ISCN) nomenclature."""
        issues = []

        for pattern, (correct, explanation) in self.CYTOGENETIC_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                matched = match.group()
                if isinstance(correct, str) and matched != correct:
                    issues.append(
                        NomenclatureIssue(
                            category="cytogenetic_nomenclature",
                            severity="warning",
                            original_text=matched,
                            corrected_text=correct,
                            explanation=explanation,
                        )
                    )

        return issues

    def check_fusion_genes(self, text: str) -> List[NomenclatureIssue]:
        """Check fusion gene nomenclature."""
        issues = []

        for pattern, (correct, explanation) in self.FUSION_PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                issues.append(
                    NomenclatureIssue(
                        category="fusion_gene_nomenclature",
                        severity="error",
                        original_text=match.group(),
                        corrected_text=correct,
                        explanation=explanation,
                    )
                )

        return issues

    def check_all(self, text: str) -> Dict[str, List[NomenclatureIssue]]:
        """Run all nomenclature checks."""
        return {
            "gene_nomenclature": self.check_gene_nomenclature(text),
            "cytogenetic_nomenclature": self.check_cytogenetic_nomenclature(text),
            "fusion_genes": self.check_fusion_genes(text),
        }

    def generate_report(self, text: str) -> str:
        """Generate nomenclature compliance report."""
        issues = self.check_all(text)

        report_lines = ["=" * 60, "NOMENCLATURE COMPLIANCE REPORT", "=" * 60, ""]

        total_issues = 0
        for category, issue_list in issues.items():
            if issue_list:
                total_issues += len(issue_list)
                report_lines.append(f"\n{category.upper().replace('_', ' ')}:")
                report_lines.append("-" * 40)
                for issue in issue_list:
                    report_lines.append(
                        f'  [{issue.severity.upper()}] "{issue.original_text}" → "{issue.corrected_text}"'
                    )
                    report_lines.append(f"    → {issue.explanation}")

        if total_issues == 0:
            report_lines.append("\n✅ No nomenclature issues detected!")
        else:
            report_lines.append(f"\n{'=' * 60}")
            report_lines.append(f"Total issues: {total_issues}")
            report_lines.append("=" * 60)

        return "\n".join(report_lines)


class WHOICCComparator:
    """Compare WHO 2022 and ICC 2022 classifications."""

    AML_ENTITIES = {
        "AML with t(8;21)(q22;q22); RUNX1::RUNX1T1": {
            "WHO": "Same entity, *RUNX1::RUNX1T1* required",
            "ICC": "Same entity",
            "Difference": "Minimal",
        },
        "AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22); CBFB::MYH11": {
            "WHO": "Same entity",
            "ICC": "Same entity",
            "Difference": "Minimal",
        },
        "APL with t(15;17)(q22;q12); PML::RARA": {
            "WHO": "Requires *PML::RARA*",
            "ICC": "Requires *PML::RARA*",
            "Difference": "None",
        },
        "AML with NPM1 mutation": {
            "WHO": "Separate entity if *NPM1*+ without adverse genetics",
            "ICC": "Separate entity",
            "Difference": "Minor criteria differences",
        },
        "AML with TP53 mutation": {
            "WHO": "Separate entity",
            "ICC": "Includes TP53-mutated MDS/AML",
            "Difference": "ICC broader definition",
        },
        "AML with myelodysplasia-related changes": {
            "WHO": "Defined by morphology/genetics",
            "ICC": "More restrictive criteria",
            "Difference": "ICC requires more strict criteria",
        },
    }

    def compare_entity(self, entity_name: str) -> Dict[str, str]:
        """Get comparison for a specific entity."""
        return self.AML_ENTITIES.get(
            entity_name,
            {
                "WHO": "Not specifically defined",
                "ICC": "Not specifically defined",
                "Difference": "Unknown",
            },
        )

    def generate_comparison_table(self) -> str:
        """Generate WHO vs ICC comparison table."""
        lines = [
            "| Entity | WHO 2022 | ICC 2022 | Key Difference |",
            "|--------|----------|----------|---------------|",
        ]

        for entity, comparison in self.AML_ENTITIES.items():
            # Shorten entity name for table
            short_name = entity.split(";")[0][:30] if ";" in entity else entity[:30]
            lines.append(
                f"| {short_name} | {comparison['WHO'][:20]}... | {comparison['ICC'][:20]}... | {comparison['Difference']} |"
            )

        return "\n".join(lines)


class ELNRiskStratification:
    """ELN 2022 AML Risk Stratification."""

    RISK_GROUPS = {
        "Favorable": [
            "t(8;21)(q22;q22); *RUNX1::RUNX1T1*",
            "inv(16)(p13.1q22) or t(16;16)(p13.1;q22); *CBFB::MYH11*",
            "*NPM1* mutation without *FLT3*-ITD or with *FLT3*-ITD low allelic ratio",
            "*CEBPA* bZIP mutation (double allele)",
        ],
        "Intermediate": [
            "*NPM1* mutation with *FLT3*-ITD high allelic ratio",
            "Wild-type *NPM1* without *FLT3*-ITD or with low allelic ratio",
            "t(9;11)(p21.3;q23.3); *MLLT3::KMT2A*",
            "Other cytogenetic abnormalities not classified",
        ],
        "Adverse": [
            "t(6;9)(p23;q34.1); *DEK::NUP214*",
            "t(v;11q23.3); *KMT2A* rearranged",
            "t(9;22)(q34;q11); *BCR::ABL1*",
            "Complex karyotype (≥3 abnormalities including -5/del(5q) or -7/del(7q))",
            "*TP53* mutation or abnormality",
            "inv(3)(q21.3;q26.2) or t(3;3)(q21.3;q26.2); *GATA2, MECOM*",
            "t(8;16)(p11;p13); *KAT6A::CREBBP*",
            "t(7;12)(q36;p13); *ETV6::MNX1*",
        ],
    }

    def format_risk_stratification(self) -> str:
        """Format risk stratification for manuscript."""
        lines = ["### ELN 2022 Risk Stratification", ""]

        for risk, entities in self.RISK_GROUPS.items():
            lines.append(f"**{risk} Risk:**")
            lines.append("")
            for entity in entities:
                lines.append(f"- {entity}")
            lines.append("")

        return "\n".join(lines)


class GVHDGrader:
    """NIH Consensus GVHD Diagnosis and Grading."""

    ACUTE_GVHD_STAGING = {
        "Skin": {
            1: "Maculopapular rash <25% BSA",
            2: "Maculopapular rash 25-50% BSA",
            3: "Maculopapular rash >50% BSA",
            4: "Generalized erythroderma + bullae",
        },
        "Liver (Bilirubin)": {
            1: "2-3 mg/dL",
            2: "3-6 mg/dL",
            3: "6-15 mg/dL",
            4: ">15 mg/dL",
        },
        "Gut": {
            1: "<500 mL diarrhea/day",
            2: "500-1000 mL/day",
            3: ">1000 mL/day",
            4: "Grade 3 + severe abdominal pain, ileus, or melena",
        },
    }

    CHRONIC_GVHD_SEVERITY = {
        "Mild": "1-2 organs involved, no significant functional impairment",
        "Moderate": "1-3 organs involved, mild-moderate functional impact",
        "Severe": "3+ organs involved, significant functional impairment",
    }

    def format_gvhd_section(self) -> str:
        """Format GVHD grading section for manuscript."""
        lines = [
            "## NIH Consensus GVHD Diagnosis and Grading",
            "",
            "### Acute GVHD Staging",
            "",
        ]

        for organ, stages in self.ACUTE_GVHD_STAGING.items():
            lines.append(f"**{organ}:**")
            for stage, description in stages.items():
                lines.append(f"- Stage {stage}: {description}")
            lines.append("")

        lines.append("### Chronic GVHD Severity")
        lines.append("")
        for severity, description in self.CHRONIC_GVHD_SEVERITY.items():
            lines.append(f"- **{severity}:** {description}")

        return "\n".join(lines)


if __name__ == "__main__":
    # Test the nomenclature checker
    checker = NomenclatureChecker()

    test_text = """
    The patient had AML with NPM1 mutation and FLT3 ITD.
    Cytogenetics showed t(9;22) and del(5) and -7.
    The BCR/ABL fusion was detected by PCR.
    Complex karyotype was present.
    """

    report = checker.generate_report(test_text)
    print(report)

    print("\n" + "=" * 60)

    # Test WHO/ICC comparison
    comparator = WHOICCComparator()
    print(comparator.generate_comparison_table())
