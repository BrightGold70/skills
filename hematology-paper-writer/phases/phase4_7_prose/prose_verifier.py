"""
Academic Prose Verifier Module (Phase 4.7)
Detects and helps eliminate outline-style writing in favor of flowing prose.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ProseIssueType(Enum):
    """Types of prose issues that can be detected."""

    BULLET_LIST = "bullet_list"
    NUMBERED_LIST = "numbered_list"
    SEQUENTIAL_CONNECTOR = "sequential_connector"
    SHORT_PARAGRAPH = "short_paragraph"
    FRAGMENTED_SENTENCE = "fragmented_sentence"
    ISOLATED_CITATION = "isolated_citation"


@dataclass
class ProseIssue:
    """Represents a prose issue found in the text."""

    issue_type: ProseIssueType
    line_number: int
    text: str
    suggestion: str
    severity: str = "medium"


class AcademicProseVerifier:
    """
    Verifies that manuscript text follows academic prose standards.
    Detects enumeration, lists, and other non-prose structures.
    """

    BULLET_PATTERN = re.compile(r"^\s*[-•·\*]\s+", re.MULTILINE)
    NUMBERED_PATTERN = re.compile(r"^\s*\d+[.\)]\s+", re.MULTILINE)
    LETTER_PATTERN = re.compile(r"^\s*[a-zA-Z][.\)]\s+", re.MULTILINE)

    SEQUENTIAL_CONNECTORS = [
        r"\b[Ff]irst\b",
        r"\b[Ss]econd\b",
        r"\b[Tt]hird\b",
        r"\b[Ff]ourth\b",
        r"\b[Ff]ifth\b",
        r"\b[Ss]ixth\b",
        r"\b[Ss]eventh\b",
        r"\b[Ee]ighth\b",
        r"\b[Ni]nth\b",
        r"\b[Tt]enth\b",
        r"\b[Nn]ext\b.*,",
        r"\b[Ff]inally\b",
        r"\b[Ll]astly\b",
        r"\b[Ii]n addition\b",
        r"\b[Ff]urthermore\b",
        r"\b[Mm]oreover\b",
        r"\b[Hh]owever\b.*,",
    ]

    def __init__(self):
        self.issues: List[ProseIssue] = []
        self.sequential_pattern = re.compile("|".join(self.SEQUENTIAL_CONNECTORS))

    def verify_manuscript(self, text: str) -> Dict:
        """
        Verify entire manuscript for prose compliance.

        Returns:
            Dict with issues, statistics, and recommendations
        """
        self.issues = []
        lines = text.split("\n")
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        self._check_for_lists(lines)
        self._check_for_sequential_connectors(lines)
        self._check_paragraph_quality(paragraphs)
        self._check_citation_integration(lines)

        return {
            "passed": len(self.issues) == 0,
            "issue_count": len(self.issues),
            "issues_by_type": self._categorize_issues(),
            "issues": self.issues,
            "statistics": self._calculate_statistics(text, paragraphs),
            "recommendations": self._generate_recommendations(),
        }

    def verify_against_csa(
        self,
        bridge: Any,
        text: str,
        strictness: str = "warn",
    ) -> Dict:
        """
        Cross-reference manuscript statistics against CSA key_statistics.
        Uses StatisticalBridge.verify_manuscript_statistics() to detect
        numeric discrepancies between manuscript text and verified statistics.

        Args:
            bridge: StatisticalBridge instance with loaded manifest
            text: Full manuscript text to verify
            strictness: "off" | "warn" | "strict"

        Returns:
            Dict with issues, issue_count, passed, disease, strictness
        """
        issues = bridge.verify_manuscript_statistics(text, strictness=strictness)
        return {
            "passed": len(issues) == 0,
            "issue_count": len(issues),
            "issues": issues,
            "bridge_disease": bridge.disease,
            "strictness": strictness,
        }

    def _check_for_lists(self, lines: List[str]):
        """Detect bullet points and numbered lists."""
        for i, line in enumerate(lines, 1):
            if self.BULLET_PATTERN.match(line):
                self.issues.append(
                    ProseIssue(
                        issue_type=ProseIssueType.BULLET_LIST,
                        line_number=i,
                        text=line[:100],
                        suggestion="Convert bullet point to prose. Integrate this point into a flowing paragraph with context and transitions.",
                        severity="high",
                    )
                )
            elif self.NUMBERED_PATTERN.match(line):
                self.issues.append(
                    ProseIssue(
                        issue_type=ProseIssueType.NUMBERED_LIST,
                        line_number=i,
                        text=line[:100],
                        suggestion="Convert numbered item to prose. Develop relationships between enumerated items into flowing narrative.",
                        severity="high",
                    )
                )

    def _check_for_sequential_connectors(self, lines: List[str]):
        """Detect sequential connectors like 'First', 'Second', etc."""
        for i, line in enumerate(lines, 1):
            matches = self.sequential_pattern.findall(line)
            if matches:
                for match in matches:
                    if match and len(match) > 2:
                        self.issues.append(
                            ProseIssue(
                                issue_type=ProseIssueType.SEQUENTIAL_CONNECTOR,
                                line_number=i,
                                text=line[:100],
                                suggestion=f"Replace '{match}' with transitional phrase that shows relationship to previous content without enumeration.",
                                severity="high",
                            )
                        )

    def _check_paragraph_quality(self, paragraphs: List[str]):
        """Check paragraph structure and length."""
        for i, paragraph in enumerate(paragraphs, 1):
            sentences = self._split_into_sentences(paragraph)

            if len(sentences) < 3:
                self.issues.append(
                    ProseIssue(
                        issue_type=ProseIssueType.SHORT_PARAGRAPH,
                        line_number=i,
                        text=paragraph[:100],
                        suggestion=f"Expand paragraph to at least 3 sentences. Current: {len(sentences)} sentence(s). Develop the idea with evidence or analysis.",
                        severity="medium",
                    )
                )

            # Check for fragmented sentences (incomplete thoughts)
            for sentence in sentences:
                if len(sentence.split()) < 5:
                    self.issues.append(
                        ProseIssue(
                            issue_type=ProseIssueType.FRAGMENTED_SENTENCE,
                            line_number=i,
                            text=sentence[:100],
                            suggestion="Expand or integrate this fragment into a complete sentence with subject and predicate.",
                            severity="low",
                        )
                    )

    def _check_citation_integration(self, lines: List[str]):
        """Check that citations are integrated into prose, not isolated."""
        for i, line in enumerate(lines, 1):
            # Pattern for citations at end of sentences (potential issue)
            end_citation_pattern = re.compile(
                r"\[\d+\]\.$|\(\w+\s+et\s+al\.?\s*,?\s*\d{4}\)\.$"
            )

            if end_citation_pattern.search(line):
                # Check if the sentence before citation provides context
                words_before = line[
                    : line.rfind("[") if "[" in line else line.rfind("(")
                ].split()
                if len(words_before) < 10:
                    self.issues.append(
                        ProseIssue(
                            issue_type=ProseIssueType.ISOLATED_CITATION,
                            line_number=i,
                            text=line[:100],
                            suggestion="Integrate citation into sentence with introductory context. Avoid placing citations at end without integration.",
                            severity="medium",
                        )
                    )

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - can be enhanced
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _categorize_issues(self) -> Dict[str, int]:
        """Categorize issues by type."""
        counts = {}
        for issue in self.issues:
            key = issue.issue_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _calculate_statistics(self, text: str, paragraphs: List[str]) -> Dict:
        """Calculate prose quality statistics."""
        all_sentences = []
        for paragraph in paragraphs:
            all_sentences.extend(self._split_into_sentences(paragraph))

        words = text.split()

        return {
            "total_words": len(words),
            "total_paragraphs": len(paragraphs),
            "total_sentences": len(all_sentences),
            "avg_words_per_paragraph": len(words) / len(paragraphs)
            if paragraphs
            else 0,
            "avg_sentences_per_paragraph": len(all_sentences) / len(paragraphs)
            if paragraphs
            else 0,
            "avg_words_per_sentence": len(words) / len(all_sentences)
            if all_sentences
            else 0,
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on detected issues."""
        recommendations = []

        has_lists = any(
            i.issue_type in [ProseIssueType.BULLET_LIST, ProseIssueType.NUMBERED_LIST]
            for i in self.issues
        )
        has_sequential = any(
            i.issue_type == ProseIssueType.SEQUENTIAL_CONNECTOR for i in self.issues
        )
        has_short_paragraphs = any(
            i.issue_type == ProseIssueType.SHORT_PARAGRAPH for i in self.issues
        )

        if has_lists:
            recommendations.append(
                "Eliminate all bullet points and numbered lists. Convert each item to a complete "
                "sentence and integrate into flowing paragraphs with transitions showing relationships."
            )

        if has_sequential:
            recommendations.append(
                "Remove sequential connectors (First, Second, Third, etc.). Replace with transitional "
                "phrases that demonstrate logical relationships between ideas rather than enumeration."
            )

        if has_short_paragraphs:
            recommendations.append(
                "Expand short paragraphs to at least 3 sentences. Each paragraph should develop "
                "a single idea through topic sentence, supporting evidence, and transitional conclusion."
            )

        if not self.issues:
            recommendations.append(
                "Excellent! Manuscript follows academic prose standards with flowing paragraphs "
                "and no enumeration. Continue to ensure all paragraphs connect logically."
            )

        return recommendations

    def get_transformation_guide(self, issue: ProseIssue) -> str:
        """Get specific guidance for transforming a prose issue."""
        guides = {
            ProseIssueType.BULLET_LIST: """
To transform bullet points into prose:
1. Identify the relationship between bullet points (sequential, causal, comparative, etc.)
2. Write a topic sentence introducing the group of points
3. Develop each point as a complete sentence showing its relationship to others
4. Add transitional phrases between sentences
5. Conclude with a sentence synthesizing the group

Example:
BULLET POINTS:
- Increased platelet activation
- Elevated inflammatory markers
- Endothelial dysfunction

PROSE VERSION:
The study demonstrated coordinated platelet activation alongside elevated inflammatory 
markers, suggesting a mechanistic relationship in which inflammatory cytokines potentiate 
platelet reactivity while simultaneously contributing to the endothelial dysfunction 
observed in peripheral blood samples.
""",
            ProseIssueType.SEQUENTIAL_CONNECTOR: """
To replace sequential connectors with transitions:
- Replace "First" with context about what initiated the sequence
- Replace "Second/Next" with transitional phrases showing relationship
- Replace "Finally/Lastly" with synthesizing or concluding statements

Example:
SEQUENTIAL: "First, we measured platelet count. Second, we assessed activation markers."
PROSE: "We initiated the analysis by measuring platelet count, then assessed activation 
markers to characterize the functional state of the platelet population."
""",
            ProseIssueType.SHORT_PARAGRAPH: """
To expand short paragraphs:
1. Identify the paragraph's central claim (topic sentence)
2. Add specific evidence supporting the claim (data, citations)
3. Explain the significance or implications of the evidence
4. Connect to the next paragraph with a transitional sentence

A well-developed paragraph should have:
- Topic sentence stating the main idea
- 2-4 sentences of supporting evidence/analysis
- Transitional conclusion linking to next idea
""",
        }

        return guides.get(
            issue.issue_type,
            "Review the text and develop it into flowing prose with proper paragraph structure.",
        )

    def generate_prose_report(self, text: str) -> str:
        """Generate a comprehensive prose verification report."""
        result = self.verify_manuscript(text)

        lines = [
            "=" * 70,
            "ACADEMIC PROSE VERIFICATION REPORT",
            "=" * 70,
            "",
            f"Status: {'✓ PASSED' if result['passed'] else '✗ ISSUES DETECTED'}",
            f"Total Issues: {result['issue_count']}",
            "",
            "Statistics:",
            f"  Total Words: {result['statistics']['total_words']}",
            f"  Paragraphs: {result['statistics']['total_paragraphs']}",
            f"  Avg Sentences per Paragraph: {result['statistics']['avg_sentences_per_paragraph']:.1f}",
            f"  Avg Words per Sentence: {result['statistics']['avg_words_per_sentence']:.1f}",
            "",
        ]

        if result["issues_by_type"]:
            lines.extend(
                [
                    "Issues by Type:",
                    "-" * 70,
                ]
            )
            for issue_type, count in result["issues_by_type"].items():
                lines.append(f"  {issue_type.replace('_', ' ').title()}: {count}")
            lines.append("")

        if result["issues"]:
            lines.extend(
                [
                    "Detailed Issues:",
                    "-" * 70,
                ]
            )
            for issue in result["issues"][:20]:  # Show first 20
                lines.extend(
                    [
                        f"Line {issue.line_number} [{issue.severity.upper()}]:",
                        f"  Type: {issue.issue_type.value.replace('_', ' ').title()}",
                        f"  Text: {issue.text[:80]}...",
                        f"  Suggestion: {issue.suggestion}",
                        "",
                    ]
                )

            if len(result["issues"]) > 20:
                lines.append(f"... and {len(result['issues']) - 20} more issues")
                lines.append("")

        lines.extend(
            [
                "Recommendations:",
                "-" * 70,
            ]
        )
        for rec in result["recommendations"]:
            lines.append(f"  • {rec}")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)


def verify_prose(text: str, nlm_context: str = "") -> Dict:
    """Convenience function to verify prose in text."""
    verifier = AcademicProseVerifier()
    result = verifier.verify_manuscript(text)
    result["nlm_context"] = nlm_context
    result["literature_context"] = nlm_context  # alias for UI rendering
    if nlm_context:
        result.setdefault("notes", []).append(
            "NLM literature context loaded — verify claims against curated sources above."
        )
    return result


# ── Scientific Skills Integration (additive, opt-in) ──────────────────────────

def integrate_skills_phase4_7(
    project_name: str,
    project_dir,
    text: str = "",
) -> None:
    """
    Invoke scientific skills for Phase 4.7 (Prose Verification).

    Runs CriticalThinker (quality scoring) on the manuscript text and persists
    results to SkillContext. Fails silently on any error.

    Args:
        project_name: Manuscript project name
        project_dir: Project directory (Path or str)
        text: Manuscript text to evaluate
    """
    try:
        from pathlib import Path
        from tools.skills import SkillContext, CriticalThinker

        ctx = SkillContext.load(project_name, Path(project_dir))

        if text:
            CriticalThinker(context=ctx).evaluate(text=text, focus="fallacies")

        ctx.save(Path(project_dir))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Phase 4.7 skill integration failed: %s", exc)


def integrate_skills_phase4_7_classification(
    project_name: str,
    project_dir,
    text: str = "",
) -> None:
    """
    Check manuscript text for classification nomenclature issues using
    ClassificationValidator. Appends any issues to SkillContext.prose_issues.
    Fails silently on any error.

    Checks performed:
    - WHO 2022 / ICC 2022 citation presence when AML mentioned
    - BCR::ABL1 double-colon notation (not BCR-ABL or BCR/ABL)
    - ELN year qualifier (2022 AML, 2025 CML)
    - NIH 2014 citation for chronic GVHD

    Args:
        project_name: Manuscript project name
        project_dir: Project directory (Path or str)
        text: Full manuscript text to scan
    """
    try:
        from pathlib import Path
        from tools.skills import SkillContext, ClassificationValidator

        ctx = SkillContext.load(project_name, Path(project_dir))

        if text:
            ClassificationValidator(context=ctx).check_classification_nomenclature(text)

        ctx.save(Path(project_dir))

    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            "Phase 4.7 classification skill integration failed: %s", exc
        )


def check_paragraph_prose_quality(paragraph: str) -> Dict:
    """Check quality of a single paragraph."""
    verifier = AcademicProseVerifier()

    sentences = verifier._split_into_sentences(paragraph)

    checks = {
        "has_topic_sentence": len(sentences) > 0,
        "has_sufficient_length": len(sentences) >= 5,   # PEEL: min 5 sentences
        "has_development": len(sentences) >= 3,
        "has_conclusion": len(sentences) >= 5,
        "no_bullets": not bool(verifier.BULLET_PATTERN.match(paragraph)),
        "no_numbering": not bool(verifier.NUMBERED_PATTERN.match(paragraph)),
    }

    checks["passed"] = all(checks.values())
    checks["sentence_count"] = len(sentences)
    checks["word_count"] = len(paragraph.split())

    return checks


# Section-level word count floors by document type and section name.
_SECTION_WORD_FLOORS: dict[str, dict[str, int]] = {
    "systematic_review": {
        "abstract": 220,
        "introduction": 600,
        "methods": 800,
        "results": 900,
        "discussion": 900,
        "conclusion": 150,
    },
    "original_research": {
        "abstract": 180,
        "introduction": 500,
        "methods": 700,
        "results": 800,
        "discussion": 800,
        "conclusion": 100,
    },
    "case_report": {
        "abstract": 150,
        "introduction": 200,
        "case_presentation": 400,
        "discussion": 600,
        "conclusion": 80,
    },
}


def check_section_word_count(
    section_text: str,
    section_name: str,
    document_type: str = "systematic_review",
) -> dict:
    """
    Validate that a manuscript section meets the minimum word count floor.

    Args:
        section_text: Full text of the section (including heading if present)
        section_name: Section identifier — "introduction", "methods", "results",
                      "discussion", "abstract", "conclusion", "case_presentation"
        document_type: "systematic_review" | "original_research" | "case_report"

    Returns:
        dict with keys: section, document_type, word_count, floor, shortfall,
                        passed (bool), message
    """
    try:
        floors = _SECTION_WORD_FLOORS.get(document_type, _SECTION_WORD_FLOORS["systematic_review"])
        floor = floors.get(section_name.lower(), 0)
        word_count = len(section_text.split())
        shortfall = max(0, floor - word_count)
        passed = word_count >= floor

        if passed:
            message = f"Section '{section_name}' meets word floor ({word_count} >= {floor})."
        else:
            message = (
                f"Section '{section_name}' is below the word floor: "
                f"{word_count} words (floor: {floor}; shortfall: {shortfall} words). "
                f"Expand with additional paragraphs following Medical PEEL structure."
            )

        return {
            "section": section_name,
            "document_type": document_type,
            "word_count": word_count,
            "floor": floor,
            "shortfall": shortfall,
            "passed": passed,
            "message": message,
        }
    except Exception:
        return {
            "section": section_name,
            "document_type": document_type,
            "word_count": 0,
            "floor": 0,
            "shortfall": 0,
            "passed": False,
            "message": f"check_section_word_count failed for section '{section_name}'",
        }
