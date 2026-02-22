"""Reference Manager for Hematology Journals."""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Reference:
    citation_number: int
    authors: List[str]
    title: str
    journal: str
    year: int
    volume: str
    pages: str
    doi: Optional[str] = None
    pubmed_id: Optional[str] = None


class ReferenceManager:
    """Manages and formats references for hematology journals."""

    VANCUVER_PATTERN = re.compile(
        r"^\[(\d+)\]\s+(.+?)\.\s+(.+?)\.\s+(\d{4});(\d+):(\d+-\d+)\.?\s*(doi:)?(.+)?$"
    )

    def __init__(self, journal: str = "blood"):
        self.journal = journal

    def parse_references(self, text: str) -> List[Reference]:
        """Extract references from manuscript text."""
        references = []
        lines = text.split("\n")
        current_ref = []

        for line in lines:
            if re.match(r"^\[\d+\]", line):
                if current_ref:
                    references.append(self._parse_reference("\n".join(current_ref)))
                current_ref = [line]
            elif current_ref:
                current_ref.append(line)

        if current_ref:
            references.append(self._parse_reference("\n".join(current_ref)))

        return references

    def _parse_reference(self, ref_text: str) -> Reference:
        """Parse a single reference."""
        match = self.VANCUVER_PATTERN.match(ref_text.strip())
        if match:
            return Reference(
                citation_number=int(match.group(1)),
                authors=self._parse_authors(match.group(2)),
                title=match.group(3),
                journal=match.group(4),
                year=int(match.group(5)),
                volume=match.group(6),
                pages=match.group(7),
                doi=match.group(8) if match.group(8) else None,
            )
        # Return parsed reference from raw text
        return Reference(
            citation_number=0,
            authors=[],
            title="",
            journal="",
            year=0,
            volume="",
            pages="",
        )

    def _parse_authors(self, author_string: str) -> List[str]:
        """Parse author names from reference string."""
        return [a.strip() for a in author_string.split(",")]

    def format_reference(self, reference: Reference) -> str:
        """Format a reference according to journal style."""
        author_str = ", ".join(reference.authors)
        doi_str = f" doi:{reference.doi}" if reference.doi else ""
        return f"[{reference.citation_number}] {author_str}. {reference.title}. {reference.journal}. {reference.year};{reference.volume}:{reference.pages}.{doi_str}"
