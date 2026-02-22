"""
Academic Prose Verifier Module (Phase 4.7)
Detects and helps eliminate outline-style writing in favor of flowing prose.
"""

import re
from typing import List, Dict, Tuple, Optional
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


def verify_prose(text: str) -> Dict:
    """Convenience function to verify prose in text."""
    verifier = AcademicProseVerifier()
    return verifier.verify_manuscript(text)


def check_paragraph_prose_quality(paragraph: str) -> Dict:
    """Check quality of a single paragraph."""
    verifier = AcademicProseVerifier()

    sentences = verifier._split_into_sentences(paragraph)

    checks = {
        "has_topic_sentence": len(sentences) > 0,
        "has_sufficient_length": len(sentences) >= 3,
        "has_development": len(sentences) >= 2,
        "has_conclusion": len(sentences) >= 3,
        "no_bullets": not bool(verifier.BULLET_PATTERN.match(paragraph)),
        "no_numbering": not bool(verifier.NUMBERED_PATTERN.match(paragraph)),
    }

    checks["passed"] = all(checks.values())
    checks["sentence_count"] = len(sentences)
    checks["word_count"] = len(paragraph.split())

    return checks
