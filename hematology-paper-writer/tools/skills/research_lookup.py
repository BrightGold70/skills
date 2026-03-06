"""
ResearchLookup — Scientific Skills Integration
Maps to: research-lookup OpenCode skill
HPW Phases: 1 (Topic Selection), 4 (Manuscript Prep)

Wraps existing PubMedSearcher for skill-layer access with SkillContext integration.
"""

from __future__ import annotations

from typing import Optional
from ._base import SkillBase, SkillContext


class ResearchLookup(SkillBase):
    """
    Performs literature lookups via PubMed and appends results to context.research_gaps.
    Wraps tools.draft_generator.pubmed_searcher.PubMedSearcher.
    """

    def invoke(self, prompt: str, **kwargs) -> str:
        try:
            return f"[ResearchLookup] {prompt[:200]}"
        except Exception:
            return ""

    def lookup(
        self,
        query: str,
        max_results: int = 10,
        time_period: Optional[str] = None,
    ) -> list[dict]:
        """
        Search PubMed for articles matching query.

        Args:
            query: PubMed search string (MeSH or free text)
            max_results: Maximum results to return (default 10)
            time_period: Optional time filter e.g. "5y", "2y"

        Returns:
            list[dict]: Articles as {title, pmid, authors, journal, year, abstract}.
                        Appends article summaries to context.research_gaps.
        """
        try:
            from tools.draft_generator.pubmed_searcher import PubMedSearcher

            searcher = PubMedSearcher()
            articles = searcher.search(
                query=query,
                max_results=max_results,
                time_period=time_period or "5y",
            )

            results = []
            for article in articles:
                entry = {
                    "title": getattr(article, "title", ""),
                    "pmid": getattr(article, "pmid", ""),
                    "authors": getattr(article, "authors", []),
                    "journal": getattr(article, "journal", ""),
                    "year": getattr(article, "year", ""),
                    "abstract": getattr(article, "abstract", ""),
                }
                results.append(entry)
                # Append short summary to research gaps
                summary = f"[PMID {entry['pmid']}] {entry['title']}"
                if summary not in self.context.research_gaps:
                    self.context.research_gaps.append(summary)

            self._log.info("ResearchLookup: found %d articles for: %s", len(results), query)
            return results

        except ImportError:
            self._log.warning("PubMedSearcher not available — using fallback")
            return self._fallback_lookup(query, max_results)
        except Exception as exc:
            self._log.warning("ResearchLookup.lookup failed: %s", exc)
            return []

    def _fallback_lookup(self, query: str, max_results: int) -> list[dict]:
        """Fallback when PubMedSearcher is unavailable."""
        placeholder = {
            "title": f"[Search pending] {query}",
            "pmid": "",
            "authors": [],
            "journal": "",
            "year": "",
            "abstract": "",
        }
        summary = f"[PubMed search queued] {query}"
        if summary not in self.context.research_gaps:
            self.context.research_gaps.append(summary)
        return [placeholder]

    def lookup_by_pmid(self, pmid: str) -> Optional[dict]:
        """Fetch a single article by PMID."""
        try:
            from tools.draft_generator.pubmed_searcher import PubMedSearcher
            searcher = PubMedSearcher()
            results = searcher.search(query=f"{pmid}[PMID]", max_results=1)
            if results:
                a = results[0]
                return {
                    "title": getattr(a, "title", ""),
                    "pmid": pmid,
                    "authors": getattr(a, "authors", []),
                    "journal": getattr(a, "journal", ""),
                    "year": getattr(a, "year", ""),
                    "abstract": getattr(a, "abstract", ""),
                }
            return None
        except Exception as exc:
            self._log.warning("lookup_by_pmid(%s) failed: %s", pmid, exc)
            return None
