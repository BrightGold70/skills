"""
PubMed Reference Verification System
Verifies academic references against PubMed database.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote_plus
import requests
import xmltodict
import json
from difflib import SequenceMatcher


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PubMedRecord:
    """Represents a PubMed article record."""
    pmid: str
    doi: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    mesh_terms: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pmid': self.pmid,
            'doi': self.doi,
            'title': self.title,
            'authors': self.authors,
            'journal': self.journal,
            'year': self.year,
            'volume': self.volume,
            'issue': self.issue,
            'pages': self.pages,
            'mesh_terms': self.mesh_terms
        }


@dataclass
class ParsedReference:
    """Represents a parsed reference string."""
    raw_text: str
    authors: List[str] = field(default_factory=list)
    title: str = ""
    journal: str = ""
    year: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'raw_text': self.raw_text,
            'authors': self.authors,
            'title': self.title,
            'journal': self.journal,
            'year': self.year,
            'volume': self.volume,
            'issue': self.issue,
            'pages': self.pages,
            'doi': self.doi
        }


@dataclass
class ValidationResult:
    """Represents the result of reference validation."""
    is_valid: bool
    pmid: Optional[str] = None
    matched_record: Optional[PubMedRecord] = None
    confidence_score: float = 0.0
    differences: List[str] = field(default_factory=list)
    raw_reference: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'pmid': self.pmid,
            'matched_record': self.matched_record.to_dict() if self.matched_record else None,
            'confidence_score': self.confidence_score,
            'differences': self.differences,
            'raw_reference': self.raw_reference
        }


@dataclass
class BatchVerificationResult:
    """Represents the result of batch reference verification."""
    total_references: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    results: List[ValidationResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_references': self.total_references,
            'valid_count': self.valid_count,
            'invalid_count': self.invalid_count,
            'results': [r.to_dict() for r in self.results]
        }
    
    @property
    def valid_percentage(self) -> float:
        if self.total_references == 0:
            return 0.0
        return (self.valid_count / self.total_references) * 100


# ============================================================================
# PubMed Verifier
# ============================================================================

class PubMedVerifier:
    """Interface with PubMed E-utilities API to search and fetch records."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # second
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the PubMed verifier.
        
        Args:
            api_key: Optional NCBI API key for higher rate limits
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/xml',
            'User-Agent': 'PubMedReferenceVerifier/1.0'
        })
    
    def _make_request(self, url: str, params: Dict[str, Any] = None) -> Optional[str]:
        """Make a request to the PubMed API with retry logic."""
        if params is None:
            params = {}
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    import time
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    return None
        return None
    
    def search_by_doi(self, doi: str) -> Optional[PubMedRecord]:
        """
        Search for a PubMed record by DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            PubMedRecord if found, None otherwise
        """
        clean_doi = doi.strip().replace('https://doi.org/', '').replace('doi:', '')
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': f'"{clean_doi}"[DOI]',
            'retmode': 'xml',
            'retmax': 1
        }
        
        xml_text = self._make_request(search_url, params)
        if not xml_text:
            return None
        
        try:
            root = ET.fromstring(xml_text)
            id_list = root.findall('.//Id')
            if id_list:
                pmid = id_list[0].text
                return self.fetch_record(pmid)
        except ET.ParseError:
            pass
        
        return None
    
    def search_by_title(self, title: str, year: Optional[str] = None) -> Optional[PubMedRecord]:
        """
        Search for a PubMed record by article title.
        
        Args:
            title: Article title
            year: Optional publication year for disambiguation
            
        Returns:
            PubMedRecord if found, None otherwise
        """
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        term = f'"{title}"[Title]'
        if year:
            term += f' AND {year}[PDAT]'
        
        params = {
            'db': 'pubmed',
            'term': term,
            'retmode': 'xml',
            'retmax': 5  # Get a few to find best match
        }
        
        xml_text = self._make_request(search_url, params)
        if not xml_text:
            return None
        
        try:
            root = ET.fromstring(xml_text)
            id_list = root.findall('.//Id')
            if id_list:
                # Return the first match
                pmid = id_list[0].text
                return self.fetch_record(pmid)
        except ET.ParseError:
            pass
        
        return None
    
    def search_by_author_journal(self, authors: List[str], journal: str, 
                                  year: Optional[str] = None) -> Optional[PubMedRecord]:
        """
        Search for a PubMed record by authors, journal, and year.
        
        Args:
            authors: List of author last names
            journal: Journal name
            year: Optional publication year
            
        Returns:
            PubMedRecord if found, None otherwise
        """
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        
        # Build search query
        author_query = ' AND '.join(f'{author}[Author]' for author in authors[:3])
        journal_query = f'"{journal}"[Journal]'
        query = f'{author_query} AND {journal_query}'
        
        if year:
            query += f' AND {year}[PDAT]'
        
        params = {
            'db': 'pubmed',
            'term': query,
            'retmode': 'xml',
            'retmax': 5
        }
        
        xml_text = self._make_request(search_url, params)
        if not xml_text:
            return None
        
        try:
            root = ET.fromstring(xml_text)
            id_list = root.findall('.//Id')
            if id_list:
                pmid = id_list[0].text
                return self.fetch_record(pmid)
        except ET.ParseError:
            pass
        
        return None
    
    def fetch_record(self, pmid: str) -> Optional[PubMedRecord]:
        """
        Fetch a PubMed record by PMID.
        
        Args:
            pmid: PubMed ID
            
        Returns:
            PubMedRecord if found, None otherwise
        """
        fetch_url = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            'db': 'pubmed',
            'id': pmid,
            'rettype': 'xml',
            'retmode': 'xml'
        }
        
        xml_text = self._make_request(fetch_url, params)
        if not xml_text:
            return None
        
        return self._parse_xml(xml_text, pmid)
    
    def _parse_xml(self, xml_text: str, pmid: str) -> Optional[PubMedRecord]:
        """
        Parse PubMed XML response into a PubMedRecord.
        
        Args:
            xml_text: XML response from PubMed
            pmid: PubMed ID
            
        Returns:
            PubMedRecord parsed from XML
        """
        try:
            # Use xmltodict for easier parsing
            data = xmltodict.parse(xml_text)
            
            pubmed_article = data.get('PubmedArticleSet', {}).get('PubmedArticle', {})
            if isinstance(pubmed_article, list):
                pubmed_article = pubmed_article[0]
            
            medline_citation = pubmed_article.get('MedlineCitation', {})
            article = medline_citation.get('Article', {})
            medline_data = medline_citation.get('MedlineCitation', {}).get('PMID', {})
            
            # Extract PMID
            record_pmid = medline_data.get('#text', pmid) if isinstance(medline_data, dict) else medline_data
            
            # Extract DOI
            article_id_list = article.get('ELocationID', [])
            if isinstance(article_id_list, dict):
                article_id_list = [article_id_list]
            
            doi = ""
            for aid in article_id_list:
                if isinstance(aid, dict) and aid.get('@EIdType') == 'doi':
                    doi = aid.get('#text', '')
                    break
            
            # Extract title
            title = article.get('ArticleTitle', '')
            
            # Extract authors
            author_list = article.get('AuthorList', {}).get('Author', [])
            if not isinstance(author_list, list):
                author_list = [author_list] if author_list else []
            
            authors = []
            for author in author_list:
                if isinstance(author, dict):
                    last_name = author.get('LastName', '')
                    initials = author.get('Initials', '')
                    if last_name:
                        authors.append(f"{last_name} {initials}".strip())
            
            # Extract journal info
            journal = article.get('Journal', {}).get('Title', '')
            
            # Extract publication date
            pub_date = article.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {})
            year = pub_date.get('Year', '')
            if not year:
                medline_date = medline_citation.get('DateCompleted', {})
                year = medline_date.get('Year', '') if isinstance(medline_date, dict) else ''
            
            volume = article.get('Journal', {}).get('JournalIssue', {}).get('Volume', '')
            issue = article.get('Journal', {}).get('JournalIssue', {}).get('Issue', '')
            
            # Extract pagination
            pagination = article.get('Pagination', {})
            pages = pagination.get('MedlinePgn', '')
            
            # Extract MeSH terms
            mesh_terms = []
            mesh_list = medline_citation.get('MeshHeadingList', {})
            if isinstance(mesh_list, dict):
                mesh_terms = [m.get('DescriptorName', {}).get('#text', '') 
                             for m in mesh_list.get('MeshHeading', []) 
                             if isinstance(m, dict)]
            elif isinstance(mesh_list, list):
                for m in mesh_list:
                    if isinstance(m, dict):
                        name = m.get('DescriptorName', {}).get('#text', '') if isinstance(m.get('DescriptorName'), dict) else m.get('DescriptorName', '')
                        if name:
                            mesh_terms.append(name)
            
            return PubMedRecord(
                pmid=str(record_pmid),
                doi=doi,
                title=title,
                authors=authors,
                journal=journal,
                year=year,
                volume=volume,
                issue=issue,
                pages=pages,
                mesh_terms=mesh_terms
            )
            
        except Exception as e:
            return None


# ============================================================================
# Reference Parser
# ============================================================================

# ============================================================================
# Reference Parser
# ============================================================================


import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from urllib.parse import quote_plus

@dataclass
class ParsedReference:
    """Parsed reference data extracted from string."""
    authors: List[str] = field(default_factory=list)
    title: str = ""
    journal: str = ""
    year: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: Optional[str] = None
    pmid: Optional[str] = None

class ReferenceParser:
    """Parses reference strings into structured format using Vancouver style."""
    
    def __init__(self):
        pass
    
    def parse(self, reference_text: str) -> ParsedReference:
        """
        Parse a reference string into a ParsedReference object.
        
        Args:
            reference_text: Raw reference string
            
        Returns:
            ParsedReference with extracted fields
        """
        ref = reference_text.strip()
        
        # Remove numbering: [1], 1., [12], etc.
        ref = re.sub(r'^\[\d+\]\s*|^\d+\.\s*', '', ref)
        
        # Extract DOI
        doi_match = re.search(r'(?:doi[:\s]*|DOI:?\s*)(10\.\d{4,}/[^\s]+)', ref, re.IGNORECASE)
        doi = doi_match.group(1) if doi_match else None
        
        # Extract PMID
        pmid_match = re.search(r'(?:pmid[:\s]*)?(\d{7,})', ref, re.IGNORECASE)
        pmid = pmid_match.group(1) if pmid_match else None
        
        # Split by periods
        parts = [p.strip() for p in ref.split('.') if p.strip()]
        
        # Parse authors
        authors = []
        if parts:
            author_str = parts[0]
            author_str = re.sub(r'\s*et\s+al\.?\s*$', '', author_str, flags=re.IGNORECASE)
            if ',' in author_str:
                authors = [a.strip() for a in author_str.split(',') if a.strip()]
            else:
                authors = [a for a in author_str.split() if a]
        
        # Title
        title = parts[1] if len(parts) > 1 else ""
        
        # Journal is in parts[2], Year;Volume:Pages is in parts[3]
        journal = ""
        year = ""
        volume = ""
        issue = ""
        pages = ""
        
        if len(parts) > 2:
            journal = parts[2]
        
        if len(parts) > 3:
            year_vol_pages = parts[3]
            semi_parts = year_vol_pages.split(';')
            
            # First part: YEAR
            if semi_parts[0]:
                year_match = re.search(r'(\d{4})', semi_parts[0])
                if year_match:
                    year = year_match.group(1)
            
            # Second part: VOLUME(ISSUE):PAGES or VOLUME:PAGES
            if len(semi_parts) > 1:
                vol_pages_part = semi_parts[1]
                
                # Volume (first number)
                vol_match = re.search(r'^(\d+)', vol_pages_part)
                if vol_match:
                    volume = vol_match.group(1)
                    
                    # After volume
                    after_vol = vol_pages_part[len(volume):]
                    
                    # Issue in parentheses
                    issue_match = re.search(r'\((\d+)\)', after_vol)
                    if issue_match:
                        issue = issue_match.group(1)
                        # Remove issue from after_vol
                        after_vol = after_vol[after_vol.find(')')+1:]
                    
                    # Pages after colon
                    pages_match = re.search(r':\s*(\d+[-–]\d+)', after_vol)
                    if pages_match:
                        pages = pages_match.group(1)
        
        return ParsedReference(
            authors=authors,
            title=title,
            journal=journal,
            year=year,
            volume=volume,
            issue=issue,
            pages=pages,
            doi=doi,
            pmid=pmid
        )

# ============================================================================
# Reference Validator


# ============================================================================
# Reference Validator
# ============================================================================

class ReferenceValidator:
    """Validates parsed references against PubMed records."""
    
    TITLE_THRESHOLD = 0.85
    AUTHOR_THRESHOLD = 0.70
    JOURNAL_THRESHOLD = 0.80
    
    def __init__(self):
        """Initialize the validator."""
        self.parser = ReferenceParser()
        self.verifier = PubMedVerifier()
    
    def validate_reference(self, reference_text: str) -> ValidationResult:
        """
        Validate a reference against PubMed database.
        
        Args:
            reference_text: Raw reference string
            
        Returns:
            ValidationResult with validation details
        """
        # Parse the reference
        parsed = self.parser.parse(reference_text)
        
        # Try different search strategies
        record = None
        
        # 1. Try DOI search first (most reliable)
        if parsed.doi:
            record = self.verifier.search_by_doi(parsed.doi)
        
        # 2. Try title search
        if record is None and parsed.title:
            record = self.verifier.search_by_title(parsed.title, parsed.year)
        
        # 3. Try author/journal/year search
        if record is None and parsed.authors and parsed.journal:
            record = self.verifier.search_by_author_journal(
                parsed.authors, parsed.journal, parsed.year
            )
        
        if record is None:
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                differences=["No matching record found in PubMed"],
                raw_reference=reference_text
            )
        
        # Compare parsed reference with found record
        return self._compare(parsed, record)
    
    def _compare(self, parsed: ParsedReference, record: PubMedRecord) -> ValidationResult:
        """
        Compare parsed reference with PubMed record.
        
        Args:
            parsed: Parsed reference
            record: PubMed record
            
        Returns:
            ValidationResult with comparison details
        """
        differences = []
        scores = []
        
        # Compare title
        title_sim = self._similarity(parsed.title.lower(), record.title.lower())
        scores.append(title_sim)
        if title_sim < self.TITLE_THRESHOLD:
            differences.append(f"Title similarity: {title_sim:.2%} (parsed: '{parsed.title}', found: '{record.title[:50]}...')")
        
        # Compare authors
        if parsed.authors and record.authors:
            author_sims = []
            for p_author in parsed.authors[:3]:  # Compare first 3 authors
                best_sim = max(self._similarity(p_author.lower(), r_author.lower()) 
                              for r_author in record.authors[:3])
                author_sims.append(best_sim)
            avg_author_sim = sum(author_sims) / len(author_sims)
            scores.append(avg_author_sim)
            if avg_author_sim < self.AUTHOR_THRESHOLD:
                differences.append(f"Author similarity: {avg_author_sim:.2%}")
        
        # Compare journal
        if parsed.journal and record.journal:
            journal_sim = self._similarity(parsed.journal.lower(), record.journal.lower())
            scores.append(journal_sim)
            if journal_sim < self.JOURNAL_THRESHOLD:
                differences.append(f"Journal similarity: {journal_sim:.2%} (parsed: '{parsed.journal}', found: '{record.journal}')")
        
        # Compare year
        if parsed.year and record.year:
            if parsed.year != record.year:
                differences.append(f"Year mismatch: parsed '{parsed.year}', found '{record.year}'")
        
        # Calculate overall confidence
        if scores:
            confidence_score = sum(scores) / len(scores)
        else:
            confidence_score = 0.0
        
        is_valid = confidence_score >= 0.7 and len(differences) <= 2
        
        return ValidationResult(
            is_valid=is_valid,
            pmid=record.pmid,
            matched_record=record,
            confidence_score=confidence_score,
            differences=differences,
            raw_reference=parsed.raw_text
        )
    
    def _similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein distance.
        
        Args:
            str1: First string
            str2: Second string
            
            Returns:
                Similarity score between 0 and 1
        """
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0
        
        # Use SequenceMatcher for simple cases (faster)
        matcher = SequenceMatcher(None, str1, str2)
        return matcher.ratio()


# ============================================================================
# Batch Reference Verifier
# ============================================================================

class BatchReferenceVerifier:
    """Verifies multiple references with progress tracking."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize batch verifier.
        
        Args:
            api_key: Optional NCBI API key
        """
        self.validator = ReferenceValidator()
        self.validator.verifier.api_key = api_key
    
    def verify_all(self, references: List[str], 
                   progress_callback=None) -> BatchVerificationResult:
        """
        Verify a list of references.
        
        Args:
            references: List of reference strings
            progress_callback: Optional callback function(progress, total)
            
        Returns:
            BatchVerificationResult with all results
        """
        results = []
        total = len(references)
        
        for i, ref in enumerate(references):
            result = self.validator.validate_reference(ref)
            results.append(result)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = total - valid_count
        
        return BatchVerificationResult(
            total_references=total,
            valid_count=valid_count,
            invalid_count=invalid_count,
            results=results
        )
    
    def generate_report(self, result: BatchVerificationResult) -> str:
        """
        Generate a human-readable report of verification results.
        
        Args:
            result: BatchVerificationResult
            
        Returns:
            Formatted report string
        """
        lines = [
            "=" * 70,
            "REFERENCE VERIFICATION REPORT",
            "=" * 70,
            f"Total References: {result.total_references}",
            f"Valid: {result.valid_count} ({result.valid_percentage:.1f}%)",
            f"Invalid: {result.invalid_count} ({100 - result.valid_percentage:.1f}%)",
            "-" * 70,
            "",
        ]
        
        # Detailed results
        for i, r in enumerate(result.results, 1):
            status = "✓ VALID" if r.is_valid else "✗ INVALID"
            lines.append(f"[{i}/{result.total_references}] {status}")
            lines.append(f"  Confidence: {r.confidence_score:.1%}")
            
            if r.pmid:
                lines.append(f"  PMID: {r.pmid}")
            
            if r.matched_record:
                lines.append(f"  Title: {r.matched_record.title[:60]}...")
                lines.append(f"  Journal: {r.matched_record.journal}")
                lines.append(f"  Year: {r.matched_record.year}")
            
            if r.differences:
                lines.append("  Issues:")
                for diff in r.differences:
                    lines.append(f"    - {diff}")
            
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ============================================================================
# Convenience Functions
# ============================================================================

def verify_reference(reference_text: str, api_key: Optional[str] = None) -> ValidationResult:
    """
    Convenience function to verify a single reference.
    
    Args:
        reference_text: Raw reference string
        api_key: Optional NCBI API key
        
    Returns:
        ValidationResult
    """
    validator = ReferenceValidator()
    if api_key:
        validator.verifier.api_key = api_key
    return validator.validate_reference(reference_text)


def verify_references(references: List[str], api_key: Optional[str] = None,
                      show_progress: bool = False) -> BatchVerificationResult:
    """
    Convenience function to verify multiple references.
    
    Args:
        references: List of reference strings
        api_key: Optional NCBI API key
        show_progress: Whether to show progress bar
        
    Returns:
        BatchVerificationResult
    """
    from tqdm import tqdm
    
    verifier = BatchReferenceVerifier(api_key)
    
    if show_progress:
        def callback(progress, total):
            tqdm.write(f"Progress: {progress}/{total}", end="\r")
        
        with tqdm(total=len(references), desc="Verifying references") as pbar:
            result = verifier.verify_all(references, progress_callback=lambda p, t: pbar.update(1))
    else:
        result = verifier.verify_all(references)
    
    return result
