"""Section Parser for IMRAD manuscripts."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ManuscriptSection:
    name: str
    content: str
    start_pos: int
    end_pos: int


class SectionParser:
    """Parses manuscript into IMRAD sections."""

    SECTION_PATTERNS = {
        "abstract": r"(?i)^#?\s*abstract\s*$",
        "introduction": r"(?i)^#?\s*introduction\s*$",
        "methods": r"(?i)^#?\s*methods?\s*$",
        "results": r"(?i)^#?\s*results?\s*$",
        "discussion": r"(?i)^#?\s*discussion\s*$",
        "acknowledgments": r"(?i)^#?\s*acknowledgments?\s*$",
        "references": r"(?i)^#?\s*references?\s*$",
    }

    def __init__(self):
        self.sections = []

    def parse(self, manuscript: str) -> List[ManuscriptSection]:
        """Parse manuscript into sections."""
        self.sections = []
        lines = manuscript.split("\n")
        current_section = None
        current_content = []
        current_start = 0

        for i, line in enumerate(lines):
            section_match = self._detect_section_start(line)
            if section_match:
                if current_section:
                    self.sections.append(ManuscriptSection(
                        name=current_section,
                        content="\n".join(current_content),
                        start_pos=current_start,
                        end_pos=i,
                    ))
                current_section = section_match
                current_content = []
                current_start = i

        # Don't forget last section
        if current_section:
            self.sections.append(ManuscriptSection(
                name=current_section,
                content="\n".join(current_content),
                start_pos=current_start,
                end_pos=len(lines),
            ))

        return self.sections

    def _detect_section_start(self, line: str) -> Optional[str]:
        """Detect if a line is a section header."""
        for section_name, pattern in self.SECTION_PATTERNS.items():
            if re.search(pattern, line):
                return section_name
        return None

    def extract_abstract(self, manuscript: str) -> str:
        """Extract abstract from manuscript."""
        sections = self.parse(manuscript)
        for section in sections:
            if section.name == "abstract":
                return section.content
        return ""

    def validate_structure(self, manuscript: str) -> Dict:
        """Validate manuscript has proper IMRAD structure."""
        sections = self.parse(manuscript)
        section_names = {s.name for s in sections}

        required = {"introduction", "methods", "results", "discussion"}
        missing = required - section_names

        return {
            "valid": len(missing) == 0,
            "found": list(section_names),
            "missing": list(missing),
            "has_abstract": "abstract" in section_names,
            "has_references": "references" in section_names,
        }
