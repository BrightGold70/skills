"""
HPW Skill - Medical Nomenclature Checker
Validates gene, chromosome, and clinical terminology nomenclature.
HGVS 2024 / ISCN 2024 compliant.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class NomenclatureIssue:
    category: str
    severity: str
    original_text: str
    corrected_text: str
    explanation: str
    line_number: Optional[int] = None


class NomenclatureChecker:
    
    # Deprecated fusion patterns (flag these as errors)
    DEPRECATED_FUSIONS = [
        ("BCR-ABL1", "*BCR::ABL1*", "Use double colon for fusion genes (HGVS 2024): BCR::ABL1"),
        ("BCR/ABL", "*BCR::ABL1*", "Use double colon for fusion genes (HGVS 2024): BCR::ABL1"),
        ("PML-RARA", "*PML::RARA*", "Use double colon for fusion genes (HGVS 2024): PML::RARA"),
        ("PML/RARA", "*PML::RARA*", "Use double colon for fusion genes (HGVS 2024): PML::RARA"),
        ("RUNX1-RUNX1T1", "*RUNX1::RUNX1T1*", "Use double colon for fusion genes (HGVS 2024): RUNX1::RUNX1T1"),
        ("CBFB-MYH11", "*CBFB::MYH11*", "Use double colon for fusion genes (HGVS 2024): CBFB::MYH11"),
        ("DEK-NUP214", "*DEK::NUP214*", "Use double colon for fusion genes (HGVS 2024): DEK::NUP214"),
        ("MLLT3-KMT2A", "*MLLT3::KMT2A*", "Use double colon for fusion genes (HGVS 2024): MLLT3::KMT2A"),
        ("ETV6-RUNX1", "*ETV6::RUNX1*", "Use double colon for fusion genes (HGVS 2024): ETV6::RUNX1"),
    ]
    
    # Genes that should be italicized
    GENE_PATTERNS = [
        (r"\*BCR::ABL1\*", True, "Correct fusion gene notation"),
        (r"BCR-ABL1", False, "Use double colon: BCR::ABL1"),
        (r"\*PML::RARA\*", True, "Correct fusion gene notation"),
        (r"PML-RARA", False, "Use double colon: PML::RARA"),
        (r"\*RUNX1::RUNX1T1\*", True, "Correct fusion gene notation"),
        (r"RUNX1-RUNX1T1", False, "Use double colon: RUNX1::RUNX1T1"),
        (r"\*NPM1\*", True, "Correct gene symbol"),
        (r"\bNPM1\b(?!::)", False, "Gene symbols should be italicized: *NPM1*"),
        (r"\*FLT3\*", True, "Correct gene symbol"),
        (r"\bFLT3\b(?!-)", False, "Gene symbols should be italicized: *FLT3*"),
        (r"\*TP53\*", True, "Correct gene symbol"),
        (r"\bTP53\b", False, "Gene symbols should be italicized: *TP53*"),
    ]
    
    def check_gene_nomenclature(self, text: str) -> List[NomenclatureIssue]:
        issues = []
        
        # Check deprecated fusion formats
        for pattern, correct, explanation in self.DEPRECATED_FUSIONS:
            if pattern in text:
                issues.append(NomenclatureIssue(
                    category="fusion_gene_nomenclature",
                    severity="error",
                    original_text=pattern,
                    corrected_text=correct,
                    explanation=explanation
                ))
        
        # Check for non-italicized genes
        non_italicized = [
            ("NPM1", "*NPM1*", "Gene symbols should be italicized"),
            ("FLT3", "*FLT3*", "Gene symbols should be italicized"),
            ("TP53", "*TP53*", "Gene symbols should be italicized"),
            ("CEBPA", "*CEBPA*", "Gene symbols should be italicized"),
            ("IDH1", "*IDH1*", "Gene symbols should be italicized"),
            ("IDH2", "*IDH2*", "Gene symbols should be italicized"),
            ("ASXL1", "*ASXL1*", "Gene symbols should be italicized"),
            ("DNMT3A", "*DNMT3A*", "Gene symbols should be italicized"),
            ("TET2", "*TET2*", "Gene symbols should be italicized"),
        ]
        
        for gene, correct, explanation in non_italicized:
            # Check if gene appears without italics and is not part of a correct fusion
            if re.search(r'(?<!\*)' + gene + r'(?!\*)', text):
                issues.append(NomenclatureIssue(
                    category="gene_nomenclature",
                    severity="warning",
                    original_text=gene,
                    corrected_text=correct,
                    explanation=explanation
                ))
        
        return issues
    
    def check_cytogenetic_nomenclature(self, text: str) -> List[NomenclatureIssue]:
        issues = []
        
        # Check for incomplete cytogenetic notation
        if re.search(r'del\(\d+\)(?!q)', text):
            issues.append(NomenclatureIssue(
                category="cytogenetic_nomenclature",
                severity="warning",
                original_text="del(5)",
                corrected_text="del(5q)",
                explanation="Use complete ISCN notation: del(5q)"
            ))
        
        if re.search(r'complex karyotype(?! \()', text, re.IGNORECASE):
            issues.append(NomenclatureIssue(
                category="cytogenetic_nomenclature",
                severity="info",
                original_text="complex karyotype",
                corrected_text="complex karyotype (>=3 abnormalities)",
                explanation="Define complex karyotype as >=3 abnormalities"
            ))
        
        return issues
    
    def check_all(self, text: str) -> Dict[str, List[NomenclatureIssue]]:
        return {
            "fusion_gene_nomenclature": self.check_gene_nomenclature(text),
            "gene_nomenclature": self.check_gene_nomenclature(text),
            "cytogenetic_nomenclature": self.check_cytogenetic_nomenclature(text),
        }
    
    def generate_report(self, text: str) -> str:
        issues = self.check_all(text)
        
        lines = [
            "=" * 60,
            "NOMENCLATURE COMPLIANCE REPORT",
            "=" * 60,
            "",
            "HGVS 2024 / ISCN 2024 STANDARD",
            "Fusion genes: Use double colon (::) - *BCR::ABL1*",
            "Gene symbols: Italicize - *NPM1*, *FLT3*",
            "-" * 60,
        ]
        
        total = 0
        
        # Fusion gene issues
        for issue in issues["fusion_gene_nomenclature"]:
            total += 1
            lines.append("")
            lines.append(f"[{issue.severity.upper()}] Fusion Gene")
            lines.append(f"  Found: {issue.original_text}")
            lines.append(f"  Use: {issue.corrected_text}")
            lines.append(f"  Reason: {issue.explanation}")
        
        # Gene symbol issues
        for issue in issues["gene_nomenclature"]:
            if issue.category == "gene_nomenclature":
                total += 1
                lines.append("")
                lines.append(f"[{issue.severity.upper()}] Gene Symbol")
                lines.append(f"  Found: {issue.original_text}")
                lines.append(f"  Use: {issue.corrected_text}")
                lines.append(f"  Reason: {issue.explanation}")
        
        # Cytogenetic issues
        for issue in issues["cytogenetic_nomenclature"]:
            total += 1
            lines.append("")
            lines.append(f"[{issue.severity.upper()}] Cytogenetic")
            lines.append(f"  Found: {issue.original_text}")
            lines.append(f"  Use: {issue.corrected_text}")
            lines.append(f"  Reason: {issue.explanation}")
        
        if total == 0:
            lines.append("")
            lines.append("No nomenclature issues detected!")
            lines.append("All fusion genes use HGVS 2024 notation (*BCR::ABL1*)")
        else:
            lines.append("")
            lines.append("=" * 60)
            lines.append(f"Total issues: {total}")
            lines.append("=" * 60)
        
        return "\n".join(lines)


if __name__ == "__main__":
    checker = NomenclatureChecker()
    
    test = """
    The patient had AML with NPM1 mutation and FLT3-ITD.
    Cytogenetics showed BCR-ABL1 fusion and PML-RARA was negative.
    The RUNX1-RUNX1T1 fusion was confirmed.
    Complex karyotype was present with del(5).
    """
    
    print(checker.generate_report(test))
