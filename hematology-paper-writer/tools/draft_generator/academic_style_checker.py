"""
HPW Skill - Academic Writing Style Checker
=====================================
Validates manuscripts follow proper academic writing style and Blood Research guidelines.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class StyleIssue:
    """Academic writing style issue."""
    category: str
    severity: str  # "error", "warning", "info"
    location: str
    description: str
    suggestion: str
    line_number: Optional[int] = None


class AcademicStyleChecker:
    """
    Check academic writing style and Blood Research compliance.
    """
    
    # Blood Research journal guidelines
    BLOOD_RESEARCH_GUIDELINES = {
        "abstract_word_limit": 200,
        "max_references": 50,
        "structured_abstract": False,
        "keywords_limit": 5,
        "figure_limit": 6,
        "table_limit": 6,
        "font": "Times New Roman",
        "font_size": 12,
        "line_spacing": 2.0,
        "margins": "2.5 cm",
        "reference_style": "vancouver"
    }
    
    # Prose indicators (should have many)
    PROSE_MARKERS = [
        "however", "therefore", "furthermore", "moreover", "consequently",
        "additionally", "subsequently", "previously", "additionally",
        "in contrast", "on the other hand", "in conclusion", "it is important",
        "these findings", "this suggests", "it has been", "the present",
        "our findings", "previous studies", "these results", "interestingly"
    ]
    
    # Bullet point patterns to flag
    BULLET_PATTERNS = [
        r"^[•\-\*]\s",  # Bullet characters
        r"^\d+\.\s",  # Numbered lists
        r"^\[\d+\]",  # Reference-style brackets at line start
        r"^\(i\)|\(ii\)|\(iii\)",  # Roman numeral lists
        r"^\([a-z]\)\s",  # Lettered lists
    ]
    
    # Informal writing to avoid
    INFORMAL_PHRASES = [
        (r"\bvery\b", "Avoid 'very' - use more precise language"),
        (r"\breally\b", "Avoid 'really' - use more precise language"),
        (r"\bkind of\b", "Avoid 'kind of' - use precise terminology"),
        (r"\bsort of\b", "Avoid 'sort of' - use precise terminology"),
        (r"\bI think\b", "Avoid first person in academic writing"),
        (r"\bI believe\b", "Avoid first person in academic writing"),
        (r"\bin my opinion\b", "Avoid first person in academic writing"),
        (r"\blots of\b", "Use 'substantial' or 'considerable' instead of 'lots of'"),
        (r"\bmany studies\b", "Specify number or use 'numerous studies'"),
        (r"\bwe found that\b", "Use passive voice: 'it was found that'"),
        (r"\bgiven that\b", "Consider using 'since' or 'because'"),
        (r"\bdue to the fact that\b", "Use 'because' for conciseness"),
    ]
    
    def __init__(self, target_journal: str = "blood_research"):
        """Initialize the style checker."""
        self.target_journal = target_journal
        self.guidelines = self._load_journal_guidelines()
    
    def _load_journal_guidelines(self) -> Dict:
        """Load journal-specific guidelines."""
        journals = {
            "blood_research": self.BLOOD_RESEARCH_GUIDELINES,
            "blood": {
                "abstract_word_limit": 250,
                "max_references": 60,
                "structured_abstract": True,
                "keywords_limit": 5,
                "figure_limit": 6,
                "table_limit": 6,
            },
            "blood_advances": {
                "abstract_word_limit": 250,
                "max_references": 50,
                "structured_abstract": False,
                "keywords_limit": 5,
            },
            "jco": {
                "abstract_word_limit": 250,
                "max_references": 50,
                "structured_abstract": True,
                "keywords_limit": 3,
            },
        }
        return journals.get(self.target_journal, self.BLOOD_RESEARCH_GUIDELINES)
    
    def check_prose_style(self, text: str) -> List[StyleIssue]:
        """Check if text follows prose writing style."""
        issues = []
        lines = text.split('\n')
        
        # Check for bullet points in content sections
        prose_sections = ["## Introduction", "## Methods", "## Results",
                         "## Discussion", "## Conclusion"]
        
        in_prose_section = False
        for i, line in enumerate(lines, 1):
            # Detect section headers
            for section in prose_sections:
                if line.strip() == section:
                    in_prose_section = True
                    break
                elif line.strip().startswith("## "):
                    in_prose_section = False
            
            if in_prose_section:
                # Check for bullet points
                for pattern in self.BULLET_PATTERNS:
                    if re.search(pattern, line):
                        issues.append(StyleIssue(
                            category="prose_style",
                            severity="warning",
                            location=f"Line {i}",
                            description=f"Bullet point detected: {line.strip()[:50]}...",
                            suggestion="Convert to full prose paragraph. Academic writing should flow as narrative text.",
                            line_number=i
                        ))
                
                # Check for single-word or very short lines
                if len(line.strip()) > 0 and len(line.strip().split()) <= 3:
                    if not line.strip().startswith("##") and not line.strip().startswith("*"):
                        issues.append(StyleIssue(
                            category="prose_style",
                            severity="info",
                            location=f"Line {i}",
                            description=f"Very short line: {line.strip()}",
                            suggestion="Consider expanding into a full sentence or paragraph.",
                            line_number=i
                        ))
        
        return issues
    
    def check_formal_academic_voice(self, text: str) -> List[StyleIssue]:
        """Check for informal language that should be avoided."""
        issues = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, suggestion in self.INFORMAL_PHRASES:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(StyleIssue(
                        category="academic_voice",
                        severity="warning",
                        location=f"Line {i}",
                        description=f"Informal phrase: '{line.strip()[:50]}'",
                        suggestion=suggestion,
                        line_number=i
                    ))
        
        return issues
    
    def check_paragraph_structure(self, text: str) -> List[StyleIssue]:
        """Check paragraph structure and flow."""
        issues = []
        paragraphs = text.split('\n\n')
        
        very_short_count = 0
        for para in paragraphs:
            words = para.split()
            if len(words) < 15 and not para.strip().startswith("##"):
                very_short_count += 1
        
        if very_short_count > len(paragraphs) * 0.3:
            issues.append(StyleIssue(
                category="paragraph_structure",
                severity="warning",
                location="General",
                description=f"Many very short paragraphs ({very_short_count} of {len(paragraphs)})",
                suggestion="Academic writing should use substantial paragraphs (typically 3-6 sentences). Consolidate short paragraphs.",
            ))
        
        return issues
    
    def check_citation_density(self, text: str) -> List[StyleIssue]:
        """Check citation density and formatting."""
        issues = []
        
        citations = re.findall(r'\[\d+\]', text)
        citation_count = len(citations)
        word_count = len(text.split())
        
        if word_count > 0:
            citations_per_1000 = (citation_count / word_count) * 1000
            if citations_per_1000 < 5:
                issues.append(StyleIssue(
                    category="citation_density",
                    severity="info",
                    location="General",
                    description=f"Low citation density ({citations_per_1000:.1f} per 1000 words)",
                    suggestion="Consider adding more references to support claims.",
                ))
            elif citations_per_1000 > 30:
                issues.append(StyleIssue(
                    category="citation_density",
                    severity="warning",
                    location="General",
                    description=f"High citation density ({citations_per_1000:.1f} per 1000 words)",
                    suggestion="Review if all citations are necessary. Avoid reference-heavy paragraphs.",
                ))
        
        return issues
    
    def check_journal_compliance(self, text: str) -> List[StyleIssue]:
        """Check Blood Research journal compliance."""
        issues = []
        
        # Check abstract
        abstract_match = re.search(r'## Abstract\n(.*?)(\n##|\n#|$)', text, re.DOTALL)
        if abstract_match:
            abstract = abstract_match.group(1)
            abstract_words = len(abstract.split())
            abstract_limit = self.guidelines["abstract_word_limit"]
            
            if abstract_words > abstract_limit:
                issues.append(StyleIssue(
                    category="journal_compliance",
                    severity="error",
                    location="Abstract",
                    description=f"Abstract word count ({abstract_words}) exceeds limit ({abstract_limit})",
                    suggestion=f"Reduce abstract to {abstract_limit} words or fewer.",
                ))
        
        return issues
    
    def check_full(self, text: str) -> Dict[str, List[StyleIssue]]:
        """Run all style checks."""
        return {
            "prose_style": self.check_prose_style(text),
            "academic_voice": self.check_formal_academic_voice(text),
            "paragraph_structure": self.check_paragraph_structure(text),
            "citation_density": self.check_citation_density(text),
            "journal_compliance": self.check_journal_compliance(text),
        }
    
    def generate_report(self, text: str) -> str:
        """Generate comprehensive style report."""
        issues = self.check_full(text)
        
        lines = [
            "=" * 60,
            "ACADEMIC WRITING STYLE REPORT",
            "=" * 60,
            f"Target Journal: {self.target_journal.replace('_', ' ').title()}",
            f"Word Count: {len(text.split())}",
            "-" * 60,
        ]
        
        total_issues = 0
        
        for category, issue_list in issues.items():
            if issue_list:
                total_issues += len(issue_list)
                lines.append(f"\n{category.replace('_', ' ').upper()}:")
                lines.append("-" * 40)
                for issue in issue_list[:10]:
                    severity_icon = "ERROR" if issue.severity == "error" else "WARNING" if issue.severity == "warning" else "INFO"
                    lines.append(f"  [{severity_icon}] {issue.location}: {issue.description}")
                    lines.append(f"         -> {issue.suggestion}")
                if len(issue_list) > 10:
                    lines.append(f"  ... and {len(issue_list) - 10} more issues")
        
        if total_issues == 0:
            lines.append("\n✅ No style issues detected! Manuscript follows academic writing guidelines.")
        else:
            lines.append(f"\n{'=' * 60}")
            lines.append(f"Total issues: {total_issues}")
            lines.append("=" * 60)
        
        return "\n".join(lines)


class BloodResearchCompliance:
    """Blood Research journal-specific compliance checker."""
    
    ABSTRACT_LIMIT = 200
    KEYWORDS_LIMIT = 5
    MAX_REFERENCES = 50
    
    def check_abstract(self, abstract: str) -> Tuple[bool, str]:
        """Check abstract compliance."""
        words = abstract.split()
        word_count = len(words)
        
        if word_count > self.ABSTRACT_LIMIT:
            return False, f"Abstract exceeds {self.ABSTRACT_LIMIT} words (current: {word_count})"
        
        return True, f"Abstract is {word_count} words (within limit)"
    
    def check_keywords(self, text: str) -> Tuple[bool, str]:
        """Check keywords compliance."""
        kw_match = re.search(r'\*\*Keywords\*\*:(.*?)(?:\n\n|$)', text, re.DOTALL)
        if kw_match:
            keywords = [k.strip() for k in kw_match.group(1).split(',')]
            if len(keywords) > self.KEYWORDS_LIMIT:
                return False, f"Too many keywords ({len(keywords)}, limit is {self.KEYWORDS_LIMIT})"
            return True, f"{len(keywords)} keywords (acceptable)"
        return True, "No keywords section found"
    
    def check_references(self, text: str) -> Tuple[bool, str]:
        """Check reference count compliance."""
        refs_match = re.search(r'## References\n(.*?)$', text, re.DOTALL)
        if refs_match:
            refs = refs_match.group(1)
            ref_count = len(re.findall(r'\[\d+\]', refs))
            if ref_count > self.MAX_REFERENCES:
                return False, f"Too many references ({ref_count}, limit is {self.MAX_REFERENCES})"
            return True, f"{ref_count} references (within limit)"
        return True, "No references section found"
    
    def check_full_compliance(self, text: str) -> Dict[str, Tuple[bool, str]]:
        """Run all Blood Research compliance checks."""
        return {
            "abstract": self.check_abstract(text),
            "keywords": self.check_keywords(text),
            "references": self.check_references(text),
        }


if __name__ == "__main__":
    checker = AcademicStyleChecker()
    
    test_text = """
    ## Introduction
    
    Chronic Myeloid Leukemia (CML) is a myeloproliferative neoplasm.
    
    However, there are many challenges. Very few patients achieve deep molecular response.
    
    ## Methods
    
    - This is a bullet point (should be prose)
    - Another bullet point
    
    ## Results
    
    We found that asciminib is effective.
    
    ## Discussion
    
    This is really interesting. I think these findings are important.
    """
    
    print(checker.generate_report(test_text))
