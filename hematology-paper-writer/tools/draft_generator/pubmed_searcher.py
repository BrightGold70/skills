"""
PubMed Searcher Module
Searches PubMed for medical/scientific articles using NCBI E-utilities.
"""

import httpx
from typing import List, Dict, Optional
from dataclasses import dataclass
import xmltodict
import time


@dataclass
class PubMedArticle:
    """Represents a PubMed article."""
    pmid: str
    title: str
    authors: List[str]
    journal: str
    year: str
    volume: str
    issue: str
    pages: str
    doi: str
    abstract: str
    mesh_terms: List[str]

    def to_vancouver(self) -> str:
        """Convert to Vancouver citation format."""
        authors = ", ".join(self.authors[:3]) + " et al." if len(self.authors) > 3 else ", ".join(self.authors)
        return f"{authors}. {self.title}. {self.journal}. {self.year};{self.volume}:{self.pages}. doi:{self.doi}"


class PubMedSearcher:
    """Search PubMed for relevant articles."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the PubMed searcher.
        
        Args:
            api_key: NCBI API key for higher rate limits
        """
        self.api_key = api_key
        self.client = httpx.Client(timeout=60.0)
    
    def search(self, query: str, max_results: int = 20) -> List[PubMedArticle]:
        """
        Search PubMed for articles matching the query.
        
        Args:
            query: Search query (MeSH terms, keywords, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            List of PubMedArticle objects
        """
        # Search for IDs
        search_url = f"{self.BASE_URL}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": min(max_results, 100),
            "sort": "relevance",
            "usehistory": "y"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        try:
            response = self.client.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            ids = data.get("esearchresult", {}).get("idlist", [])
            
            if not ids:
                return []
            
            # Fetch article details in batches
            articles = []
            batch_size = 10
            
            for i in range(0, len(ids), batch_size):
                batch = ids[i:i + batch_size]
                articles.extend(self._fetch_details(batch))
                time.sleep(0.34)  # NCBI rate limit (3 requests/second)
            
            return articles[:max_results]
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    def _fetch_details(self, pmids: List[str]) -> List[PubMedArticle]:
        """Fetch details for a batch of PMIDs."""
        fetch_url = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract"
        }
        
        try:
            response = self.client.get(fetch_url, params=params)
            response.raise_for_status()
            
            # Parse XML
            data = xmltodict.parse(response.text)
            articles = []
            
            pubmed_articles = data.get("PubmedArticleSet", {}).get("PubmedArticle", [])
            if isinstance(pubmed_articles, dict):
                pubmed_articles = [pubmed_articles]
            
            for article in pubmed_articles:
                try:
                    med = article.get("MedlineCitation", {})
                    art = med.get("Article", {})
                    ab = art.get("Abstract", {}).get("AbstractText", "")
                    if isinstance(ab, list):
                        ab = " ".join([a.get("#text", "") for a in ab])
                    else:
                        ab = ab.get("#text", "") if isinstance(ab, dict) else str(ab)
                    
                    # Authors
                    authors = []
                    auth_list = art.get("AuthorList", {}).get("Author", [])
                    if isinstance(auth_list, dict):
                        auth_list = [auth_list]
                    for auth in auth_list:
                        last = auth.get("LastName", "")
                        initials = auth.get("Initials", "")
                        if last and initials:
                            authors.append(f"{last} {initials}")
                        elif last:
                            authors.append(last)
                    
                    # Journal info
                    journal = art.get("Journal", {})
                    j_title = journal.get("Title", "")
                    
                    j_issue = journal.get("JournalIssue", {})
                    volume = j_issue.get("Volume", "")
                    issue = j_issue.get("Issue", "")
                    year = j_issue.get("PubDate", {}).get("Year", "")
                    pages = j_issue.get("MedlineDate", "")
                    if not pages:
                        pages = j_issue.get("Pages", "")
                    
                    # DOI
                    article_ids = article.get("PubmedData", {}).get("ArticleIdList", {}).get("ArticleId", [])
                    doi = ""
                    for aid in article_ids:
                        if aid.get("@IdType") == "doi":
                            doi = aid.get("#text", "")
                            break
                    
                    # Mesh terms
                    mesh_list = med.get("MeshHeadingList", {}).get("MeshHeading", [])
                    if isinstance(mesh_list, dict):
                        mesh_list = [mesh_list]
                    mesh_terms = [m.get("DescriptorName", {}).get("#text", "") for m in mesh_list if m]
                    
                    # PMID extraction (PMID is inside MedlineCitation)
                    pmid_elem = med.get("PMID")
                    if isinstance(pmid_elem, str):
                        pmid = pmid_elem
                    elif isinstance(pmid_elem, dict):
                        pmid = pmid_elem.get("#text", "")
                    else:
                        pmid = ""
                    
                    articles.append(PubMedArticle(
                        pmid=pmid,
                        title=art.get("ArticleTitle", ""),
                        authors=authors,
                        journal=j_title,
                        year=year,
                        volume=volume,
                        issue=issue,
                        pages=pages,
                        doi=doi,
                        abstract=ab,
                        mesh_terms=mesh_terms
                    ))
                except Exception as e:
                    continue
            
            return articles
            
        except Exception as e:
            print(f"Error fetching article details: {e}")
            return []
    
    def search_by_topic(
        self, 
        topic: str, 
        max_results: int = 50,
        time_period: str = "all",  # "all", "1y", "2y", "5y", "10y"
        use_repeat: bool = True,
        sort_by: str = "relevance"  # "relevance", "pub_date"
    ) -> List[PubMedArticle]:
        """
        Search PubMed with optimized query for a hematology topic.
        
        Args:
            topic: The research topic (e.g., "asciminib first-line therapy")
            max_results: Maximum results per search
            time_period: Time filter - "all", "1y", "2y", "5y", "10y"
            use_repeat: If True, repeat search with different strategies
            sort_by: Sort results by "relevance" or "pub_date"
            
        Returns:
            List of relevant articles
        """
        import time as time_module
        
        # Build a specific search query with the main topic terms
        query_parts = topic.split()
        
        # Skip common words to build specific query
        specific_terms = []
        for p in query_parts:
            if p.lower() in ['as', 'a', 'for', 'the', 'in', 'of', 'and', 'or', 'with', 'therapy', 'treatment', 'use']:
                continue
            specific_terms.append(p)
        
        if len(specific_terms) >= 2:
            query = f'"{topic}"'
        else:
            query = f'"{topic}"'
        
        # Add hematology filter
        if any(term.lower() in topic.lower() for term in ['leukemia', 'leukemia', 'myeloid', 'cml', 'aml', 'mpn', 'blood', 'hemato']):
            full_query = f'({query}) AND (leukemia OR myeloid OR hematology)'
        else:
            full_query = f'({query}) AND (hematology OR oncology)'
        
        # Add time filter
        time_filter = ""
        if time_period == "1y":
            time_filter = ' AND ("2024/01/01"[PDAT] : "2025/12/31"[PDAT])'
        elif time_period == "2y":
            time_filter = ' AND ("2023/01/01"[PDAT] : "2025/12/31"[PDAT])'
        elif time_period == "5y":
            time_filter = ' AND ("2020/01/01"[PDAT] : "2025/12/31"[PDAT])'
        elif time_period == "10y":
            time_filter = ' AND ("2015/01/01"[PDAT] : "2025/12/31"[PDAT])'
        
        # Build multiple search strategies
        strategies = []
        if use_repeat:
            # Strategy 1: Original query
            strategies.append((full_query + time_filter, sort_by))
            
            # Strategy 2: Broader search without hematology filter
            strategies.append((query + time_filter, "pub_date"))
            
            # Strategy 3: Search by specific terms
            if len(specific_terms) >= 2:
                term_query = " AND ".join([f'"{t}"' for t in specific_terms[:4]])
                strategies.append((f'({term_query})' + time_filter, "pub_date"))
            
            # Strategy 4: Search by first 2 specific terms
            if len(specific_terms) >= 2:
                simple_query = f'"{specific_terms[0]}" AND "{specific_terms[1]}"'
                strategies.append((simple_query + time_filter, "pub_date"))
        else:
            strategies.append((full_query + time_filter, sort_by))
        
        # Execute searches
        all_articles = []
        seen_pmids = set()
        
        for query_str, sort in strategies:
            if len(all_articles) >= max_results * 2:  # Cap to avoid too many
                break
                
            try:
                search_url = f"{self.BASE_URL}/esearch.fcgi"
                params = {
                    "db": "pubmed",
                    "term": query_str,
                    "retmode": "json",
                    "retmax": min(max_results, 100),
                    "sort": sort
                }
                
                if self.api_key:
                    params["api_key"] = self.api_key
                
                response = self.client.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                ids = data.get("esearchresult", {}).get("idlist", [])
                
                if ids:
                    batch_size = 10
                    for i in range(0, min(len(ids), max_results * 2), batch_size):
                        batch = ids[i:i + batch_size]
                        articles = self._fetch_details(batch)
                        
                        for art in articles:
                            if art.pmid not in seen_pmids:
                                seen_pmids.add(art.pmid)
                                all_articles.append(art)
                        
                        time_module.sleep(0.34)  # Rate limit
                        
            except Exception as e:
                continue
        
        # Remove duplicates and sort
        unique = []
        seen = set()
        for art in all_articles:
            if art.pmid and art.pmid not in seen:
                seen.add(art.pmid)
                unique.append(art)
        
        return unique
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


def search_pubmed(topic: str, max_results: int = 15, api_key: Optional[str] = None) -> List[PubMedArticle]:
    """
    Convenience function to search PubMed.
    
    Args:
        topic: Research topic
        max_results: Maximum results
        api_key: Optional NCBI API key
        
    Returns:
        List of PubMedArticle objects
    """
    searcher = PubMedSearcher(api_key)
    try:
        return searcher.search_by_topic(topic, max_results)
    finally:
        searcher.close()


if __name__ == "__main__":
    # Test
    articles = search_pubmed("asciminib chronic myeloid leukemia", max_results=5)
    for art in articles:
        print(f"\n{art.title}")
        print(f"  PMID: {art.pmid}")
        print(f"  Journal: {art.journal} ({art.year})")
        print(f"  Authors: {', '.join(art.authors[:3])}")
