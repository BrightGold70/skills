"""
HPW Skill - Enhanced Manuscript Editor
===================================
Advanced editing with style validation and Blood Research compliance.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EditSuggestion:
    """Manuscript edit suggestion."""

    section: str
    issue_type: str
    description: str
    suggestion: str
    confidence: float
    source: str


class ManuscriptEditor:
    """
    Enhanced manuscript editor with style checking and compliance validation.
    """

    def __init__(self, target_journal: str = "blood_research"):
        """Initialize the editor."""
        self.target_journal = target_journal
        self._load_style_checker()

    def _load_style_checker(self):
        """Load the academic style checker."""
        try:
            from tools.draft_generator.academic_style_checker import (
                AcademicStyleChecker,
                BloodResearchCompliance,
            )

            self.style_checker = AcademicStyleChecker(target_journal=target_journal)
            self.compliance_checker = BloodResearchCompliance()
        except ImportError:
            self.style_checker = None
            self.compliance_checker = None

    def load_manuscript(self, path: str) -> Dict[str, str]:
        """Load manuscript and parse into sections."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        sections = self._parse_sections(content)
        return {
            "full_text": content,
            "sections": sections,
            "word_count": len(content.split()),
            "reference_count": len(re.findall(r"\[\d+\]", content)),
        }

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse manuscript into sections."""
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = line.replace("## ", "").strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    def check_style(self, text: str) -> Dict[str, List[EditSuggestion]]:
        """Check manuscript style and generate suggestions."""
        if not self.style_checker:
            self._load_style_checker()

        if not self.style_checker:
            return {"general": []}

        issues = self.style_checker.check_full(text)

        # Convert to EditSuggestion format
        suggestions = {"general": []}
        for category, issue_list in issues.items():
            for issue in issue_list:
                suggestion = EditSuggestion(
                    section=issue.location,
                    issue_type=category,
                    description=issue.description,
                    suggestion=issue.suggestion,
                    confidence=1.0 - (0.1 if issue.severity == "info" else 0.3),
                    source="AcademicStyleChecker",
                )
                if category not in suggestions:
                    suggestions[category] = []
                suggestions[category].append(suggestion)

        return suggestions

    def check_blood_research_compliance(self, text: str) -> Dict[str, Tuple[bool, str]]:
        """Check Blood Research journal compliance."""
        if not self.compliance_checker:
            self._load_style_checker()

        if not self.compliance_checker:
            return {"status": (False, "Style checker not available")}

        return self.compliance_checker.check_full_compliance(text)

    def apply_edits(
        self, text: str, suggestions: Dict[str, List[EditSuggestion]]
    ) -> str:
        """Apply edits to manuscript."""
        # This is a simplified implementation
        # A full implementation would need more sophisticated text manipulation
        return text

    def generate_editing_report(self, text: str, manuscript_path: str = None) -> str:
        """Generate comprehensive editing report."""
        ref_pattern = r"\[\d+\]"
        lines = [
            "=" * 60,
            "MANUSCRIPT EDITING REPORT",
            "=" * 60,
            f"Target Journal: {self.target_journal.replace('_', ' ').title()}",
            f"Word Count: {len(text.split())}",
            f"Reference Count: {len(re.findall(ref_pattern, text))}",
            "-" * 60,
        ]

        # Style check
        if self.style_checker:
            lines.append("\nACADEMIC STYLE ANALYSIS")
            lines.append("-" * 40)
            style_report = self.style_checker.generate_report(text)
            lines.append(style_report)

        # Blood Research compliance
        if self.compliance_checker:
            lines.append("\n" + "=" * 60)
            lines.append("BLOOD RESEARCH COMPLIANCE")
            lines.append("-" * 40)

            compliance = self.check_blood_research_compliance(text)
            for check_name, (passed, message) in compliance.items():
                icon = "PASS" if passed else "FAIL"
                lines.append(f"  [{icon}] {check_name.title()}: {message}")

        return "\n".join(lines)

    def validate_before_output(self, text: str) -> Tuple[bool, str]:
        """
        Validate manuscript before outputting.
        Returns (is_valid, message).
        """
        # Check abstract length
        abstract_match = re.search(r"## Abstract\n(.*?)(\n##|\n#|$)", text, re.DOTALL)
        if abstract_match:
            abstract_words = len(abstract_match.group(1).split())
            abstract_limit = 200 if self.target_journal == "blood_research" else 250
            if abstract_words > abstract_limit:
                return (
                    False,
                    f"Abstract too long ({abstract_words} words, limit: {abstract_limit})",
                )

        # Check for excessive bullet points
        bullet_count = len(re.findall(r"^[•\-\*]\s", text, re.MULTILINE))
        if bullet_count > 10:
            return (
                False,
                f"Too many bullet points ({bullet_count}). Convert to prose paragraphs.",
            )

        # Check for informal language
        informal_phrases = re.findall(
            r"\b(very|really|I think|I believe)\b", text, re.IGNORECASE
        )
        if len(informal_phrases) > 5:
            return (
                False,
                f"Informal language detected ({len(informal_phrases)} instances). Use formal academic tone.",
            )

        return True, "Manuscript passes all validation checks"


def check_manuscript_quality(manuscript_path: str) -> Dict:
    """
    Check manuscript quality and return detailed report.

    Returns:
        Dict with: word_count, reference_count, section_count,
                   style_issues, compliance_status, overall_score
    """
    editor = ManuscriptEditor()
    manuscript = editor.load_manuscript(manuscript_path)

    text = manuscript["full_text"]
    style_issues = editor.check_style(text)
    compliance = editor.check_blood_research_compliance(text)

    # Calculate overall score
    issue_count = sum(len(issues) for issues in style_issues.values())
    compliance_score = (
        sum(1 for v in compliance.values() if v[0]) / len(compliance)
        if compliance
        else 0
    )

    # Style score based on issues
    if issue_count == 0:
        style_score = 100
    elif issue_count < 5:
        style_score = 85
    elif issue_count < 10:
        style_score = 70
    else:
        style_score = 50

    # Overall score
    overall_score = style_score * 0.6 + compliance_score * 100 * 0.4

    return {
        "word_count": manuscript["word_count"],
        "reference_count": manuscript["reference_count"],
        "section_count": len(manuscript["sections"]),
        "style_issues": issue_count,
        "compliance_score": f"{compliance_score:.0%}",
        "overall_score": f"{overall_score:.0f}%",
        "is_compliant": compliance_score >= 0.8 and style_score >= 70,
        "compliance_details": compliance,
        "style_issues_details": style_issues,
    }


if __name__ == "__main__":
    # Example usage
    editor = ManuscriptEditor()
    print("Manuscript Editor Module Loaded")
    print("\nFeatures:")
    print("  - Load and parse manuscripts")
    print("  - Academic style checking")
    print("  - Blood Research compliance validation")
    print("  - Quality scoring")
    print("  - Pre-output validation")
