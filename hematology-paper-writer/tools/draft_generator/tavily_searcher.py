import os
import json
import re
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class SourceCategory(Enum):
    """Category of web search result for permission workflow."""

    PEER_REVIEWED = "peer_reviewed"  # PubMed-indexed articles (no permission needed)
    CONFERENCE_ABSTRACT = "conference_abstract"  # ASH, EHA abstracts
    CONFERENCE_PROCEEDINGS = "conference_proceedings"  # Conference proceedings
    WEBSITE = "website"  # Website/online resource
    CLINICAL_TRIAL = "clinical_trial"  # Clinical trial registry
    GUIDELINE = "guideline"  # Clinical guidelines
    PREPRINT = "preprint"  # Preprint (arXiv, medRxiv, bioRxiv)
    NEWS = "news"  # News article
    UNKNOWN = "unknown"


@dataclass
class WebSearchResult:
    title: str
    url: str
    content: str
    published_date: Optional[str] = None
    source: Optional[str] = None
    score: float = 0.0
    # Enhanced metadata for permission workflow
    category: SourceCategory = SourceCategory.UNKNOWN
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    journal: str = ""
    conference: str = ""
    year: int = 0
    doi: str = ""
    isbn: str = ""
    organization: str = ""
    access_date: str = ""
    # For permission workflow
    permission_status: str = "pending"  # pending, permitted, rejected
    permission_notes: str = ""


class TavilySearcher:
    """Web search using Tavily API for supplementary literature beyond PubMed."""

    CONFERENCE_PATTERNS = [
        r"ash\s*(abstract|meeting|annual|conference)",
        r"eha\s*(abstract|meeting|conference)",
        r"american\s*society\s*hematology",
        r"european\s*hematology\s*association",
        r"icml",
        r"ebmt",
        r"waldenstrom",
    ]

    WEBSITE_PATTERNS = [
        r"clinicaltrials\.gov",
        r"clinicaltrialsregister\.eu",
        r"nccn\.org",
        r"elns\.org",
        r"who\.int",
        r"fda\.gov",
        r"ema\.europa\.eu",
    ]

    GUIDELINE_PATTERNS = [
        r"guideline",
        r"consensus",
        r"recommendation",
        r"nccn\.org",
        r"elns\.org",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TAVILY_API_KEY not found. Set environment variable or pass api_key."
            )
        self.base_url = "https://api.tavily.com"

    def search(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "basic",
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
    ) -> List[WebSearchResult]:
        """Perform web search."""
        endpoint = f"{self.base_url}/search"

        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
        }

        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                result = WebSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    published_date=item.get("published_date"),
                    source=item.get("source"),
                    score=item.get("score", 0.0),
                )
                result = self._classify_source(result)
                results.append(result)

            return results

        except requests.exceptions.RequestException as e:
            print(f"Search error: {e}")
            return []

    def _classify_source(self, result: WebSearchResult) -> WebSearchResult:
        """Classify the source category based on URL and content."""
        url_lower = result.url.lower()
        content_lower = (result.title + " " + result.content).lower()

        if re.search(r"clinicaltrials\.gov|clinicaltrialsregister\.eu", url_lower):
            result.category = SourceCategory.CLINICAL_TRIAL
        elif re.search(r"arxiv\.org|medrxiv|biorxiv", url_lower):
            result.category = SourceCategory.PREPRINT
        elif any(re.search(p, url_lower) for p in self.CONFERENCE_PATTERNS):
            result.category = SourceCategory.CONFERENCE_ABSTRACT
        elif any(re.search(p, url_lower) for p in self.GUIDELINE_PATTERNS):
            result.category = SourceCategory.GUIDELINE
        elif re.search(r"news|newsroom|press\s*release", content_lower):
            result.category = SourceCategory.NEWS
        else:
            result.category = SourceCategory.WEBSITE

        result.access_date = datetime.now().strftime("%Y-%m-%d")
        self._extract_metadata(result)
        return result

    def _extract_metadata(self, result: WebSearchResult) -> None:
        """Extract structured metadata from search result."""
        content = result.title + " " + result.content

        year_match = re.search(r"(19|20)\d{2}", content)
        if year_match:
            result.year = int(year_match.group())

        doi_match = re.search(r"10\.\d{4,}/[^\s]+", content)
        if doi_match:
            result.doi = doi_match.group()

        if result.source:
            result.organization = result.source

        if result.category == SourceCategory.CONFERENCE_ABSTRACT:
            for pattern in self.CONFERENCE_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    result.conference = match.group().title()
                    break

    def search_clinical_trials(self, condition: str) -> List[WebSearchResult]:
        """Search for clinical trials related to a condition."""
        query = f"clinical trial {condition} site:clinicaltrials.gov OR site:clinicaltrialsregister.eu"
        return self.search(query, max_results=10, search_depth="advanced")

    def search_guidelines(self, topic: str) -> List[WebSearchResult]:
        """Search for medical guidelines."""
        query = f"{topic} clinical guidelines 2024 2025 site:nccn.org OR site:ashpublications.org OR site:elns.org"
        return self.search(query, max_results=10, search_depth="advanced")

    def search_preprints(self, topic: str) -> List[WebSearchResult]:
        """Search for preprints."""
        query = f"{topic} preprint medrxiv biorxiv 2024 2025"
        return self.search(query, max_results=10, search_depth="advanced")

    def search_conferences(self, topic: str) -> List[WebSearchResult]:
        """Search for conference abstracts (ASH, EHA, etc)."""
        query = f"{topic} ASH abstract EHA 2024 2025"
        return self.search(query, max_results=10, search_depth="advanced")

    def search_drug_approvals(self, drug: str) -> List[WebSearchResult]:
        """Search for recent drug approvals."""
        query = f"{drug} FDA approval EMA 2024 2025"
        return self.search(query, max_results=10, search_depth="advanced")

    def search_news(self, topic: str) -> List[WebSearchResult]:
        """Search for recent news about a topic."""
        query = f"{topic} news 2024 2025"
        return self.search(query, max_results=10, search_depth="advanced")

    def comprehensive_search(self, topic: str) -> Dict[str, List[WebSearchResult]]:
        """Perform comprehensive search covering multiple sources."""
        return {
            "general": self.search(topic, max_results=10),
            "guidelines": self.search_guidelines(topic),
            "clinical_trials": self.search_clinical_trials(topic),
            "preprints": self.search_preprints(topic),
            "conferences": self.search_conferences(topic),
            "news": self.search_news(topic),
        }

    def save_results(self, results: List[WebSearchResult], filepath: str) -> None:
        """Save search results to JSON file."""
        data = {
            "query": "",
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(r) for r in results],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def format_results_markdown(self, results: List[WebSearchResult]) -> str:
        """Format search results as markdown."""
        if not results:
            return "No results found."

        md = "## Web Search Results\n\n"
        for i, result in enumerate(results, 1):
            md += f"### {i}. {result.title}\n"
            md += f"- **URL**: {result.url}\n"
            if result.published_date:
                md += f"- **Date**: {result.published_date}\n"
            if result.source:
                md += f"- **Source**: {result.source}\n"
            md += f"- **Content**: {result.content[:300]}...\n\n"

        return md

    def format_for_permission_review(self, results: List[WebSearchResult]) -> str:
        """Format results for user permission review with full metadata."""
        if not results:
            return "No results requiring permission."

        md = "## References Requiring Permission Review\n\n"
        md += "The following sources are not PubMed-indexed. Review each and decide whether to include.\n\n"

        for i, result in enumerate(results, 1):
            category_label = {
                SourceCategory.CONFERENCE_ABSTRACT: "[Conference Abstract]",
                SourceCategory.CONFERENCE_PROCEEDINGS: "[Conference Proceedings]",
                SourceCategory.WEBSITE: "[Website]",
                SourceCategory.CLINICAL_TRIAL: "[Clinical Trial]",
                SourceCategory.GUIDELINE: "[Guideline]",
                SourceCategory.PREPRINT: "[Preprint]",
                SourceCategory.NEWS: "[News]",
            }.get(result.category, "[Unknown]")

            md += f"### {i}. {category_label} {result.title}\n\n"
            md += f"**URL**: {result.url}\n"
            md += f"**Source**: {result.source or 'N/A'}\n"
            md += f"**Published Date**: {result.published_date or 'N/A'}\n"
            md += f"**Year**: {result.year or 'N/A'}\n"
            md += f"**Organization**: {result.organization or 'N/A'}\n"

            if result.conference:
                md += f"**Conference**: {result.conference}\n"
            if result.doi:
                md += f"**DOI**: {result.doi}\n"

            md += f"\n**Content Preview**:\n{result.content[:500]}...\n"
            md += f"\n**Permission Status**: {result.permission_status.upper()}\n"
            md += "\n---\n\n"

        return md

    def filter_needs_permission(
        self, results: List[WebSearchResult]
    ) -> List[WebSearchResult]:
        """Filter results that require user permission."""
        permission_categories = [
            SourceCategory.CONFERENCE_ABSTRACT,
            SourceCategory.CONFERENCE_PROCEEDINGS,
            SourceCategory.WEBSITE,
            SourceCategory.CLINICAL_TRIAL,
            SourceCategory.GUIDELINE,
            SourceCategory.PREPRINT,
            SourceCategory.NEWS,
        ]
        return [r for r in results if r.category in permission_categories]


def search_web(query: str, max_results: int = 10) -> List[WebSearchResult]:
    """Quick search function for CLI usage."""
    searcher = TavilySearcher()
    return searcher.search(query, max_results=max_results)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python tavily_searcher.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    searcher = TavilySearcher()
    results = searcher.search(query)

    for r in results:
        print(f"Title: {r.title}")
        print(f"URL: {r.url}")
        print(f"Content: {r.content[:200]}...")
        print("---")
