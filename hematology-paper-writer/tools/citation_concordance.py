"""
Citation-Reference Concordance Checker
======================================

Enhanced module for checking citation-reference concordance in manuscripts.
Identifies citations in text, extracts references, and reports discrepancies.

Based on:
- analyze_citations.py reference implementation

Features:
- Extract citations from text ([1], [1-3], [1, 2, 3])
- Parse reference lists (Vancouver format)
- Report missing citations and uncited references
- Support for DOCX and Markdown files
"""

import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any
from pathlib import Path


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ConcordanceResult:
    """Result of citation-reference concordance check."""
    
    cited_in_text: Set[int] = field(default_factory=set)
    found_in_references: Set[int] = field(default_factory=set)
    missing_in_references: List[int] = field(default_factory=list)
    uncited_references: List[int] = field(default_factory=list)
    
    total_citations: int = 0
    total_references: int = 0
    
    is_concordant: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cited_in_text': sorted(list(self.cited_in_text)),
            'found_in_references': sorted(list(self.found_in_references)),
            'missing_in_references': sorted(self.missing_in_references),
            'uncited_references': sorted(self.uncited_references),
            'total_citations': self.total_citations,
            'total_references': self.total_references,
            'is_concordant': self.is_concordant
        }
    
    def summary(self) -> str:
        """Generate summary report."""
        lines = []
        lines.append("=" * 50)
        lines.append("CONCORDANCE REPORT")
        lines.append("=" * 50)
        lines.append(f"Total citations in text: {self.total_citations}")
        lines.append(f"Total references found: {self.total_references}")
        lines.append("")
        
        if self.is_concordant:
            lines.append("SUCCESS: Concordance confirmed on all counts.")
        else:
            if self.missing_in_references:
                lines.append(f"[ERROR] Cited in text but missing in references ({len(self.missing_in_references)}):")
                for num in self.missing_in_references:
                    lines.append(f"  - [{num}]")
            
            if self.uncited_references:
                lines.append(f"[WARNING] In reference list but never cited ({len(self.uncited_references)}):")
                for num in self.uncited_references:
                    lines.append(f"  - [{num}]")
        
        return "\n".join(lines)


@dataclass
class CitationLocation:
    """Location of a citation in the manuscript."""
    reference_number: int
    context: str = ""
    paragraph_index: int = 0
    sentence_index: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reference_number': self.reference_number,
            'context': self.context,
            'paragraph_index': self.paragraph_index,
            'sentence_index': self.sentence_index
        }


# ============================================================================
# Text Extraction from DOCX
# ============================================================================

def get_text_from_docx(file_path: str) -> List[str]:
    """
    Extracts text from a .docx file.
    Returns a list of paragraph texts.
    
    Args:
        file_path: Path to .docx file
        
    Returns:
        List of paragraph texts
    """
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            xml_content = z.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            paragraphs = []
            for p in tree.findall('.//w:p', ns):
                texts = [node.text for node in p.findall('.//w:t', ns) if node.text]
                if texts:
                    paragraphs.append(''.join(texts))
                else:
                    paragraphs.append('')
            return paragraphs
    except Exception as e:
        print(f"Error reading docx file: {e}")
        return []


def get_text_from_markdown(file_path: str) -> List[str]:
    """
    Extracts text from a markdown file.
    Returns a list of paragraph texts.
    
    Args:
        file_path: Path to .md file
        
    Returns:
        List of paragraph texts
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by double newlines (paragraphs)
        paragraphs = content.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    except Exception as e:
        print(f"Error reading markdown file: {e}")
        return []


def get_text_from_file(file_path: str) -> List[str]:
    """
    Extracts text from a file based on extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        List of paragraph texts
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext == '.docx':
        return get_text_from_docx(file_path)
    elif ext == '.md':
        return get_text_from_markdown(file_path)
    else:
        # Try as plain text
        return get_text_from_markdown(file_path)


# ============================================================================
# Citation Extraction
# ============================================================================

def extract_citations(text: str) -> Set[int]:
    """
    Extract citation numbers from text.
    
    Handles formats:
    - [1] - single citation
    - [1, 2, 3] - multiple citations
    - [1-3] - range of citations
    - [1, 3-5, 7] - mixed format
    
    Args:
        text: Text containing citations
        
    Returns:
        Set of unique citation numbers
    """
    citations = set()
    
    # Find all citation patterns: [numbers]
    matches = re.findall(r'\[([\d\s,\-]+)\]', text)
    
    for group in matches:
        parts = [p.strip() for p in group.split(',')]
        for part in parts:
            if '-' in part:
                # Range: 1-5
                try:
                    start, end = map(int, part.split('-'))
                    if start < end:
                        citations.update(range(start, end + 1))
                except ValueError:
                    pass
            else:
                # Single number
                try:
                    citations.add(int(part))
                except ValueError:
                    pass
    
    return citations


def extract_citations_with_context(paragraphs: List[str]) -> Tuple[Set[int], List[CitationLocation]]:
    """
    Extract citations with their context/location.
    
    Args:
        paragraphs: List of paragraph texts
        
    Returns:
        Tuple of (set of citation numbers, list of CitationLocation objects)
    """
    citations = set()
    locations = []
    
    for para_idx, para in enumerate(paragraphs):
        # Split into sentences
        sentences = re.split(r'[.!?]+', para)
        
        for sent_idx, sentence in enumerate(sentences):
            # Extract citations from sentence
            matches = re.findall(r'\[([\d\s,\-]+)\]', sentence)
            
            for group in matches:
                parts = [p.strip() for p in group.split(',')]
                for part in parts:
                    # Handle ranges
                    if '-' in part:
                        try:
                            start, end = map(int, part.split('-'))
                            if start < end:
                                for num in range(start, end + 1):
                                    citations.add(num)
                                    locations.append(CitationLocation(
                                        reference_number=num,
                                        context=sentence.strip()[:200],
                                        paragraph_index=para_idx,
                                        sentence_index=sent_idx
                                    ))
                        except ValueError:
                            pass
                    else:
                        try:
                            num = int(part)
                            citations.add(num)
                            locations.append(CitationLocation(
                                reference_number=num,
                                context=sentence.strip()[:200],
                                paragraph_index=para_idx,
                                sentence_index=sent_idx
                            ))
                        except ValueError:
                            pass
    
    return citations, locations


# ============================================================================
# Reference Extraction
# ============================================================================

def extract_references(paragraphs: List[str]) -> Tuple[Set[int], Dict[int, str]]:
    """
    Extract reference numbers and their full text from reference section.
    
    Args:
        paragraphs: List of paragraph texts (reference section)
        
    Returns:
        Tuple of (set of reference numbers, dict mapping number to full reference text)
    """
    references = {}
    
    for text in paragraphs:
        text = text.strip()
        if not text:
            continue
        
        # First, try to split by newlines if it looks like inline references
        lines = text.split('\n')
        if len(lines) > 1:
            # Each line is a separate reference
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                match = re.match(r'^\[?(\d+)\]?[\.\s]+(.{10,})', line)
                if match:
                    ref_num = int(match.group(1))
                    references[ref_num] = line
        else:
            # Single paragraph reference
            match = re.match(r'^\[?(\d+)\]?[\.\s]+(.{10,})', text)
            if match:
                ref_num = int(match.group(1))
                references[ref_num] = text
    
    return set(references.keys()), references


def find_reference_section_start(paragraphs: List[str]) -> int:
    """
    Find the starting index of the reference section.
    
    Args:
        paragraphs: List of paragraph texts
        
    Returns:
        Index of reference section start, or -1 if not found
    """
    for i, text in enumerate(paragraphs):
        normalized = text.strip().lower()
        
        # Look for reference section headers
        if normalized in ['references', 'reference', 'bibliography', 'references cited']:
            return i
        
        # Heuristic: look for first [1] or 1. pattern
        if re.match(r'^\[?1\]?[\.\s]', text.strip()):
            # Verify it looks like a reference
            if len(text) > 50:  # References are usually longer
                return i - 1 if i > 0 else 0
    
    return -1


# ============================================================================
# Concordance Checking
# ============================================================================

def check_concordance(file_path: str) -> ConcordanceResult:
    """
    Check citation-reference concordance for a manuscript.
    
    Args:
        file_path: Path to manuscript file (.docx, .md, or .txt)
        
    Returns:
        ConcordanceResult with all findings
    """
    # Extract text
    paragraphs = get_text_from_file(file_path)
    
    if not paragraphs:
        return ConcordanceResult()
    
    # Find reference section
    ref_start = find_reference_section_start(paragraphs)
    
    if ref_start == -1:
        # Fallback: use last 1/3 of document as reference section
        ref_start = int(len(paragraphs) * 2 / 3)
    
    # Split into main text and references
    main_text_paragraphs = paragraphs[:ref_start]
    reference_paragraphs = paragraphs[ref_start:]
    
    # Extract citations from main text
    cited_numbers, _ = extract_citations_with_context(main_text_paragraphs)
    
    # Extract references
    reference_numbers, reference_texts = extract_references(reference_paragraphs)
    
    # Calculate discrepancies
    missing_in_refs = sorted(list(cited_numbers - reference_numbers))
    uncited_refs = sorted(list(reference_numbers - cited_numbers))
    
    # Create result
    result = ConcordanceResult(
        cited_in_text=cited_numbers,
        found_in_references=reference_numbers,
        missing_in_references=missing_in_refs,
        uncited_references=uncited_refs,
        total_citations=len(cited_numbers),
        total_references=len(reference_numbers),
        is_concordant=(len(missing_in_refs) == 0 and len(uncited_refs) == 0)
    )
    
    return result


def check_concordance_verbose(file_path: str) -> Tuple[ConcordanceResult, List[CitationLocation], Dict[int, str]]:
    """
    Check concordance with detailed citation locations.
    
    Args:
        file_path: Path to manuscript file
        
    Returns:
        Tuple of (ConcordanceResult, citation locations, reference texts)
    """
    paragraphs = get_text_from_file(file_path)
    
    if not paragraphs:
        return ConcordanceResult(), [], {}
    
    ref_start = find_reference_section_start(paragraphs)
    if ref_start == -1:
        ref_start = int(len(paragraphs) * 2 / 3)
    
    main_paragraphs = paragraphs[:ref_start]
    ref_paragraphs = paragraphs[ref_start:]
    
    cited_numbers, citation_locations = extract_citations_with_context(main_paragraphs)
    reference_numbers, reference_texts = extract_references(ref_paragraphs)
    
    missing_in_refs = sorted(list(cited_numbers - reference_numbers))
    uncited_refs = sorted(list(reference_numbers - cited_numbers))
    
    result = ConcordanceResult(
        cited_in_text=cited_numbers,
        found_in_references=reference_numbers,
        missing_in_references=missing_in_refs,
        uncited_references=uncited_refs,
        total_citations=len(cited_numbers),
        total_references=len(reference_numbers),
        is_concordant=(len(missing_in_refs) == 0 and len(uncited_refs) == 0)
    )
    
    return result, citation_locations, reference_texts


# ============================================================================
# Reference Style Validation
# ============================================================================

def validate_reference_format(text: str) -> Dict[str, Any]:
    """
    Validate the format of a single reference.
    
    Args:
        text: Reference text
        
    Returns:
        Dict with validation results
    """
    issues = []
    
    # Check for common Vancouver format elements
    has_author = bool(re.search(r'[A-Z][a-z]+[\s,]+[A-Z][a-z]+', text))
    has_year = bool(re.search(r'\b(19|20)\d{2}\b', text))
    has_journal = bool(re.search(r'[A-Z][a-z]+(\s+[A-Z][a-z]+)*(\s+Journals?|\s+Blood|\s+Leukemia|\s+NEJM)?', text))
    
    if not has_author:
        issues.append("Missing or unclear author names")
    if not has_year:
        issues.append("Missing publication year")
    if not has_journal:
        issues.append("Missing or unclear journal name")
    
    # Check for DOI
    has_doi = bool(re.search(r'doi:\s*10\.\d{4,}', text.lower()) or 
                   re.search(r'DOI:\s*10\.\d{4,}', text))
    
    return {
        'is_valid': len(issues) == 0,
        'has_author': has_author,
        'has_year': has_year,
        'has_journal': has_journal,
        'has_doi': has_doi,
        'issues': issues
    }


def validate_reference_list(file_path: str) -> Dict[str, Any]:
    """
    Validate format of all references in a manuscript.
    
    Args:
        file_path: Path to manuscript file
        
    Returns:
        Dict with validation results
    """
    paragraphs = get_text_from_file(file_path)
    
    if not paragraphs:
        return {'error': 'No text extracted'}
    
    ref_start = find_reference_section_start(paragraphs)
    if ref_start == -1:
        ref_start = int(len(paragraphs) * 2 / 3)
    
    ref_paragraphs = paragraphs[ref_start:]
    _, reference_texts = extract_references(ref_paragraphs)
    
    results = {}
    for num, text in reference_texts.items():
        results[num] = validate_reference_format(text)
    
    # Summary
    valid_count = sum(1 for r in results.values() if r['is_valid'])
    
    return {
        'total_references': len(results),
        'valid_format': valid_count,
        'invalid_format': len(results) - valid_count,
        'format_rate': valid_count / len(results) if results else 0,
        'reference_results': results
    }


# ============================================================================
# Main Entry Point
# ============================================================================

def main(file_path: str) -> ConcordanceResult:
    """
    Main function to analyze citations in a manuscript.
    
    Args:
        file_path: Path to manuscript file
        
    Returns:
        ConcordanceResult
    """
    print(f"Analyzing: {file_path}")
    
    if not Path(file_path).exists():
        print(f"Error: File not found at {file_path}")
        return ConcordanceResult()
    
    result = check_concordance(file_path)
    print(result.summary())
    
    return result


if __name__ == "__main__":
    import sys
    
    target = sys.argv[1] if len(sys.argv) > 1 else "manuscript.docx"
    main(target)
