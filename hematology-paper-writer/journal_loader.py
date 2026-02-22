"""
Journal Loader Module for Hematology Paper Writer
Provides utilities for loading journal specifications and formatting manuscripts.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Manuscript:
    """Represents a manuscript with all its components."""
    title: str = ""
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    sections: Dict[str, str] = field(default_factory=dict)
    tables: List[str] = field(default_factory=list)
    figures: List[str] = field(default_factory=list)
    references: List[Dict] = field(default_factory=list)
    author_contributions: str = ""
    conflict_of_interest: str = ""
    acknowledgments: str = ""
    word_count: int = 0


def load_specs(journal_name: str) -> Dict[str, Any]:
    """
    Load journal specifications from the YAML configuration file.
    
    Args:
        journal_name: Name of the journal (case-insensitive)
                      Options: "Blood", "Blood Advances", "JCO", 
                               "British Journal of Haematology"
    
    Returns:
        Dictionary containing journal specifications
    
    Raises:
        ValueError: If journal not found or name is invalid
    """
    # Map common journal name variations
    name_mapping = {
        "blood": "Blood",
        "blood advances": "Blood_Advances",
        "blood_advances": "Blood_Advances",
        "blood advances": "Blood_Advances",
        "jco": "JCO",
        "journal of clinical oncology": "JCO",
        "british journal of haematology": "British_Journal_of_Haematology",
        "bjh": "British_Journal_of_Haematology",
        "british journal of hematology": "British_Journal_of_Haematology",
    }
    
    # Normalize input
    normalized_input = journal_name.lower().strip()
    yaml_key = name_mapping.get(normalized_input, journal_name.replace(" ", "_"))
    
    # Load YAML file
    config_path = Path(__file__).parent / "journal-specs.yaml"
    
    try:
        with open(config_path, 'r') as f:
            specs = yaml.safe_load(f)
    except FileNotFoundError:
        raise ValueError(f"Journal specifications file not found at {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing journal specifications: {e}")
    
    # Find the journal in specs
    journals = specs.get('journals', {})
    
    # Try exact match first, then case-insensitive search
    for key, journal_specs in journals.items():
        if key.lower() == yaml_key.lower():
            return journal_specs
        if journal_specs.get('full_name', '').lower() == normalized_input:
            return journal_specs
    
    # Try partial match
    for key, journal_specs in journals.items():
        if normalized_input in key.lower() or normalized_input in journal_specs.get('full_name', '').lower():
            return journal_specs
    
    available_journals = [specs.get('full_name', key) for key, specs in journals.items()]
    raise ValueError(
        f"Journal '{journal_name}' not found. "
        f"Available journals: {', '.join(available_journals)}"
    )


def get_required_sections(journal_name: str) -> List[str]:
    """
    Get the list of required sections for a given journal.
    
    Args:
        journal_name: Name of the journal
    
    Returns:
        List of required section names
    """
    specs = load_specs(journal_name)
    return specs.get('required_sections', [])


def format_reference(journal_name: str, pubmed_record: Dict) -> str:
    """
    Format a reference in the style of the specified journal.
    
    Args:
        journal_name: Name of the target journal
        pubmed_record: Dictionary containing PubMed record fields
                       Expected keys: authors, title, journal, year, 
                                     volume, pages, doi
    
    Returns:
        Formatted reference string
    """
    specs = load_specs(journal_name)
    ref_style = specs.get('reference_style', 'Vancouver')
    
    templates = {
        'Vancouver': _format_vancouver_reference
    }
    
    formatter = templates.get(ref_style, _format_vancouver_reference)
    return formatter(pubmed_record)


def _format_vancouver_reference(pubmed_record: Dict) -> str:
    """Format a reference in Vancouver style."""
    authors = _format_authors(pubmed_record.get('authors', []))
    title = pubmed_record.get('title', '').rstrip('.')
    journal = pubmed_record.get('journal', '')
    year = pubmed_record.get('year', '')
    volume = pubmed_record.get('volume', '')
    pages = pubmed_record.get('pages', '')
    doi = pubmed_record.get('doi', '')
    
    # Vancouver format: Authors. Title. Journal Year;Vol:Pages. DOI
    parts = [authors, f"{title}. {journal}"]
    
    if year:
        parts.append(str(year))
    
    if volume:
        parts[-1] += f";{volume}"
    
    if pages:
        parts[-1] += f":{pages}"
    
    if doi:
        parts.append(f"DOI:{doi}")
    
    return '. '.join(parts) + '.'


def _format_authors(authors: List[Dict]) -> str:
    """
    Format list of authors in Vancouver style.
    
    Args:
        authors: List of author dictionaries with 'last_name' and 'initials'
    
    Returns:
        Formatted author string (e.g., "Smith AB, Jones CD, White EF")
    """
    if not authors:
        return "Unknown"
    
    formatted = []
    for author in authors:
        last_name = author.get('last_name', '')
        initials = author.get('initials', '')
        if last_name and initials:
            formatted.append(f"{last_name} {initials}")
        elif last_name:
            formatted.append(last_name)
    
    # Use "et al." if more than 6 authors (Vancouver style)
    if len(formatted) > 6:
        return f"{', '.join(formatted[:6])} et al."
    
    return ', '.join(formatted)


def check_compliance(manuscript: Manuscript, journal_name: str) -> List[str]:
    """
    Check manuscript compliance against journal requirements.
    
    Args:
        manuscript: Manuscript object to check
        journal_name: Name of the target journal
    
    Returns:
        List of compliance issues found (empty list = compliant)
    """
    issues = []
    specs = load_specs(journal_name)
    
    # Word count check
    word_limit = specs.get('word_limit', 5000)
    if manuscript.word_count > word_limit:
        issues.append(
            f"Word count ({manuscript.word_count}) exceeds limit ({word_limit})"
        )
    
    # Abstract check
    abstract_limit = specs.get('abstract', {}).get('limit', 250)
    if manuscript.abstract:
        abstract_words = len(manuscript.abstract.split())
        if abstract_words > abstract_limit:
            issues.append(
                f"Abstract word count ({abstract_words}) exceeds limit ({abstract_limit})"
            )
    else:
        issues.append("Abstract is missing")
    
    # Keywords check
    keywords_limit = specs.get('abstract', {}).get('keywords_limit', 5)
    if manuscript.keywords:
        if len(manuscript.keywords) > keywords_limit:
            issues.append(
                f"Number of keywords ({len(manuscript.keywords)}) exceeds limit ({keywords_limit})"
            )
    else:
        issues.append("Keywords are missing")
    
    # Required sections check
    required_sections = specs.get('required_sections', [])
    manuscript_sections = set(manuscript.sections.keys())
    
    for section in required_sections:
        # Handle section name variations
        section_key = section.lower().replace(' ', '_')
        if section_key == 'consort_diagram':
            # Only required for clinical trials
            continue
        
        found = False
        for ms_key in manuscript_sections:
            if section_key in ms_key.lower() or ms_key.lower() in section.lower():
                found = True
                break
        
        if not found:
            issues.append(f"Required section '{section}' is missing")
    
    # Author contributions check
    if specs.get('specific_requirements', {}).get('author_contributions'):
        if not manuscript.author_contributions:
            issues.append("Author contributions statement is required")
    
    # Conflict of interest check
    if specs.get('specific_requirements', {}).get('conflict_of_interest'):
        if not manuscript.conflict_of_interest:
            issues.append("Conflict of interest statement is required")
    
    # Tables and figures labeling
    for i, table in enumerate(manuscript.tables):
        if not table:
            issues.append(f"Table {i+1} is not properly labeled")
    
    for i, figure in enumerate(manuscript.figures):
        if not figure:
            issues.append(f"Figure {i+1} is not properly labeled")
    
    # References check
    if not manuscript.references:
        issues.append("References section is missing")
    
    # Journal-specific checks
    journal_lower = journal_name.lower()
    
    if 'blood' in journal_lower and 'blood advances' not in journal_lower:
        # Blood journal specific
        if not manuscript.acknowledgments:
            issues.append("Acknowledgments section is recommended for Blood journal")
    
    if 'key_points' in required_sections:
        if 'key_points' not in manuscript_sections:
            issues.append(
                "Key points section (3-5 bullets) is required. "
                "Include 3-5 concise points summarizing the manuscript."
            )
    
    return issues


def get_journal_list() -> List[str]:
    """Get list of all available journals."""
    config_path = Path(__file__).parent / "journal-specs.yaml"
    
    try:
        with open(config_path, 'r') as f:
            specs = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        return []
    
    journals = specs.get('journals', {})
    return [specs.get('full_name', key) for key, specs in journals.items()]


def compare_journals(journal_names: List[str]) -> Dict[str, Any]:
    """
    Compare specifications between multiple journals.
    
    Args:
        journal_names: List of journal names to compare
    
    Returns:
        Dictionary comparing journal specifications
    """
    comparison = {}
    
    for name in journal_names:
        try:
            specs = load_specs(name)
            comparison[name] = {
                'word_limit': specs.get('word_limit'),
                'abstract_limit': specs.get('abstract', {}).get('limit'),
                'font_size': specs.get('manuscript_formatting', {}).get('font_size'),
                'reference_style': specs.get('reference_style'),
                'required_sections_count': len(specs.get('required_sections', [])),
            }
        except ValueError:
            comparison[name] = {'error': 'Journal not found'}
    
    return comparison
