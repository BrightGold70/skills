"""
Project Notebook Manager
=======================
Manages topic-specific NotebookLM notebooks for research projects.
Each research topic gets its own notebook that stores:
- PubMed articles and abstracts
- Search queries and results
- Draft versions and revisions
- Related sources and references

This enables:
- Long-term research memory for each topic
- Easy revision with updated sources
- Version control of research resources
"""

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import re


@dataclass
class PubMedArticle:
    """Represents a PubMed article for notebook storage."""

    pmid: str
    title: str
    authors: List[str]
    journal: str
    year: int
    abstract: str = ""
    doi: str = ""
    mesh_terms: List[str] = field(default_factory=list)

    def to_notebook_source(self) -> Dict[str, str]:
        """Convert to NotebookLM source format."""
        return {
            "title": self.title,
            "content": f"""PMID: {self.pmid}
Title: {self.title}
Authors: {", ".join(self.authors)}
Journal: {self.journal} ({self.year})
DOI: {self.doi}

Abstract:
{self.abstract}

MeSH Terms: {", ".join(self.mesh_terms) if self.mesh_terms else "N/A"}
""",
            "source_type": "pubmed",
            "pmid": self.pmid,
        }


@dataclass
class ResearchQuery:
    """Represents a research query stored in notebook."""

    query_text: str
    databases: List[str]
    max_results: int
    timestamp: datetime = field(default_factory=datetime.now)
    articles_found: List[str] = field(default_factory=list)  # PMIDs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query_text,
            "databases": self.databases,
            "max_results": self.max_results,
            "timestamp": self.timestamp.isoformat(),
            "articles_found": self.articles_found,
        }


@dataclass
class ManuscriptVersion:
    """Represents a manuscript version in the notebook."""

    version_number: int
    title: str
    content_preview: str
    word_count: int
    sources: List[str]  # PMIDs used
    timestamp: datetime = field(default_factory=datetime.now)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version_number,
            "title": self.title,
            "word_count": self.word_count,
            "sources": self.sources,
            "timestamp": self.timestamp.isoformat(),
            "notes": self.notes,
        }


@dataclass
class ProjectNotebook:
    """Represents a research project notebook."""

    project_id: str
    topic: str
    notebook_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    queries: List[ResearchQuery] = field(default_factory=list)
    articles: Dict[str, PubMedArticle] = field(default_factory=dict)
    manuscript_versions: List[ManuscriptVersion] = field(default_factory=list)
    related_notebooks: List[str] = field(default_factory=list)  # Other notebook IDs
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_article(self, article: PubMedArticle) -> None:
        """Add article to notebook."""
        self.articles[article.pmid] = article
        self.updated_at = datetime.now()

    def add_query(self, query: ResearchQuery) -> None:
        """Add search query to notebook."""
        self.queries.append(query)
        self.updated_at = datetime.now()

    def add_manuscript_version(
        self, title: str, content: str, sources: List[str], notes: str = ""
    ) -> ManuscriptVersion:
        """Add manuscript version to notebook."""
        version = ManuscriptVersion(
            version_number=len(self.manuscript_versions) + 1,
            title=title,
            content_preview=content[:500] if content else "",
            word_count=len(content.split()) if content else 0,
            sources=sources,
            notes=notes,
        )
        self.manuscript_versions.append(version)
        self.updated_at = datetime.now()
        return version

    def get_latest_sources(self) -> List[PubMedArticle]:
        """Get all articles sorted by recency (from queries)."""
        all_pmids = []
        for query in self.queries:
            all_pmids.extend(query.articles_found)
        unique_pmids = list(dict.fromkeys(reversed(all_pmids)))
        return [self.articles[pmid] for pmid in unique_pmids if pmid in self.articles]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "topic": self.topic,
            "notebook_id": self.notebook_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "queries": [q.to_dict() for q in self.queries],
            "articles": {
                pmid: {
                    "pmid": a.pmid,
                    "title": a.title,
                    "authors": a.authors,
                    "journal": a.journal,
                    "year": a.year,
                    "abstract": a.abstract[:500] if a.abstract else "",
                    "doi": a.doi,
                }
                for pmid, a in self.articles.items()
            },
            "manuscript_versions": [v.to_dict() for v in self.manuscript_versions],
            "related_notebooks": self.related_notebooks,
            "metadata": self.metadata,
        }


class ProjectNotebookManager:
    """
    Manages project-specific NotebookLM notebooks.

    Each research project (topic) gets its own notebook that stores:
    - PubMed articles and abstracts
    - Search queries and results
    - Manuscript versions
    - Related sources

    Usage:
        manager = ProjectNotebookManager()

        # Create new project notebook
        notebook = manager.create_notebook("asciminib_cml_firstline")

        # Add research results
        manager.add_research_results(notebook, articles, query)

        # Add manuscript version after drafting
        manager.add_manuscript_version(notebook, title, content, pmids)

        # Update with new research for revision
        manager.update_with_new_research(notebook, new_articles, new_query)
    """

    DEFAULT_STORAGE_PATH = (
        "/Users/kimhawk/.openclaw/skills/hematology-paper-writer/project_notebooks"
    )

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the notebook manager."""
        self.storage_path = Path(storage_path or self.DEFAULT_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.projects: Dict[str, ProjectNotebook] = {}
        self._load_projects()

    def _load_projects(self) -> None:
        """Load all existing projects from storage."""
        for project_file in self.storage_path.glob("*.json"):
            try:
                with open(project_file, "r") as f:
                    data = json.load(f)
                    notebook = self._deserialize_notebook(data)
                    self.projects[notebook.project_id] = notebook
            except Exception as e:
                print(f"Warning: Failed to load {project_file}: {e}")

    def _get_project_file(self, project_id: str) -> Path:
        """Get the storage file path for a project."""
        return self.storage_path / f"{project_id}.json"

    def _save_notebook(self, notebook: ProjectNotebook) -> None:
        """Save notebook to storage."""
        with open(self._get_project_file(notebook.project_id), "w") as f:
            json.dump(notebook.to_dict(), f, indent=2)

    def _deserialize_notebook(self, data: Dict[str, Any]) -> ProjectNotebook:
        """Deserialize notebook from storage."""
        notebook = ProjectNotebook(
            project_id=data["project_id"],
            topic=data["topic"],
            notebook_id=data.get("notebook_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

        for q in data.get("queries", []):
            notebook.queries.append(
                ResearchQuery(
                    query_text=q["query"],
                    databases=q["databases"],
                    max_results=q["max_results"],
                    timestamp=datetime.fromisoformat(q["timestamp"]),
                    articles_found=q["articles_found"],
                )
            )

        for pmid, a in data.get("articles", {}).items():
            notebook.articles[pmid] = PubMedArticle(
                pmid=a["pmid"],
                title=a["title"],
                authors=a["authors"],
                journal=a["journal"],
                year=a["year"],
                abstract=a.get("abstract", ""),
                doi=a.get("doi", ""),
            )

        for v in data.get("manuscript_versions", []):
            notebook.manuscript_versions.append(
                ManuscriptVersion(
                    version_number=v["version"],
                    title=v["title"],
                    content_preview="",
                    word_count=v["word_count"],
                    sources=v["sources"],
                    timestamp=datetime.fromisoformat(v["timestamp"]),
                    notes=v.get("notes", ""),
                )
            )

        notebook.related_notebooks = data.get("related_notebooks", [])
        notebook.metadata = data.get("metadata", {})

        return notebook

    def create_notebook(
        self,
        topic: str,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProjectNotebook:
        """
        Create a new project notebook for a research topic.

        Args:
            topic: Research topic (e.g., "asciminib_cml_firstline")
            project_id: Optional custom project ID (generated from topic if not provided)
            metadata: Optional metadata about the project

        Returns:
            Created ProjectNotebook
        """
        if project_id is None:
            project_id = self._generate_project_id(topic)

        if project_id in self.projects:
            print(f"Project '{project_id}' already exists. Loading existing notebook.")
            return self.projects[project_id]

        notebook = ProjectNotebook(
            project_id=project_id,
            topic=topic,
            metadata=metadata or {},
        )

        self.projects[project_id] = notebook
        self._save_notebook(notebook)

        print(f"Created new project notebook: {project_id}")
        print(f"  Topic: {topic}")
        print(f"  Storage: {self._get_project_file(project_id)}")

        return notebook

    def _generate_project_id(self, topic: str) -> str:
        """Generate a project ID from topic."""
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", topic.lower())
        safe = re.sub(r"_+", "_", safe)
        return f"project_{safe[:50]}"

    def get_notebook(self, project_id: str) -> Optional[ProjectNotebook]:
        """Get a project notebook by ID."""
        return self.projects.get(project_id)

    def list_projects(self) -> List[ProjectNotebook]:
        """List all project notebooks."""
        return sorted(self.projects.values(), key=lambda n: n.updated_at, reverse=True)

    def add_research_results(
        self,
        notebook: ProjectNotebook,
        articles: List[Any],
        query_text: str,
        databases: List[str] = None,
        max_results: int = 20,
    ) -> None:
        """
        Add research results to a notebook.

        Args:
            notebook: Project notebook to update
            articles: List of PubMed articles (PubMedArticle or dict)
            query_text: The search query used
            databases: Databases searched
            max_results: Maximum results requested
        """
        databases = databases or ["PubMed"]

        pmids = []
        for article in articles:
            if hasattr(article, "pmid"):
                pmid = str(article.pmid)
                pubmed_article = PubMedArticle(
                    pmid=pmid,
                    title=getattr(article, "title", "Unknown"),
                    authors=getattr(article, "authors", []),
                    journal=getattr(article, "journal", ""),
                    year=getattr(article, "year", 2024),
                    abstract=getattr(article, "abstract", ""),
                    doi=getattr(article, "doi", ""),
                )
            elif isinstance(article, dict):
                pmid = str(article.get("pmid", "unknown"))
                pubmed_article = PubMedArticle(
                    pmid=pmid,
                    title=article.get("title", "Unknown"),
                    authors=article.get("authors", []),
                    journal=article.get("journal", ""),
                    year=article.get("year", 2024),
                    abstract=article.get("abstract", ""),
                    doi=article.get("doi", ""),
                )
            else:
                continue

            notebook.add_article(pubmed_article)
            pmids.append(pmid)

        query = ResearchQuery(
            query_text=query_text,
            databases=databases,
            max_results=max_results,
            articles_found=pmids,
        )
        notebook.add_query(query)

        self._save_notebook(notebook)

        print(f"Added {len(pmids)} articles to notebook '{notebook.project_id}'")
        print(f"  Query: {query_text}")

    def add_manuscript_version(
        self,
        notebook: ProjectNotebook,
        title: str,
        content: str,
        sources: List[str],
        notes: str = "",
    ) -> ManuscriptVersion:
        """
        Add a manuscript version to the notebook.

        Args:
            notebook: Project notebook
            title: Manuscript title
            content: Manuscript content
            sources: List of PMIDs used as sources
            notes: Optional notes about this version

        Returns:
            Created ManuscriptVersion
        """
        version = notebook.add_manuscript_version(title, content, sources, notes)
        self._save_notebook(notebook)

        print(
            f"Added manuscript v{version.version_number} to notebook '{notebook.project_id}'"
        )
        print(f"  Title: {title}")
        print(f"  Word count: {version.word_count}")
        print(f"  Sources: {len(sources)} articles")

        return version

    def update_with_new_research(
        self,
        notebook: ProjectNotebook,
        new_articles: List[Any],
        query_text: str,
        databases: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Update notebook with new research for manuscript revision.

        This is called when:
        - User searches PubMed again for the same topic
        - User wants to add more sources to existing manuscript

        Args:
            notebook: Project notebook to update
            new_articles: New PubMed articles found
            query_text: The new search query
            databases: Databases searched

        Returns:
            Dict with update summary
        """
        existing_pmids = set(notebook.articles.keys())

        self.add_research_results(notebook, new_articles, query_text, databases)

        new_pmids = set(notebook.articles.keys()) - existing_pmids

        summary = {
            "existing_articles": len(existing_pmids),
            "new_articles": len(new_pmids),
            "total_articles": len(notebook.articles),
            "total_queries": len(notebook.queries),
            "new_pmids": list(new_pmids),
        }

        print(f"Notebook updated: {summary['new_articles']} new articles added")
        print(f"  Total articles now: {summary['total_articles']}")

        return summary

    def get_sources_for_manuscript(
        self, notebook: ProjectNotebook, include_all: bool = False
    ) -> List[PubMedArticle]:
        """
        Get sources for manuscript revision.

        Args:
            notebook: Project notebook
            include_all: If True, include all articles. If False, only from latest query.

        Returns:
            List of PubMed articles
        """
        if include_all:
            return list(notebook.articles.values())
        return notebook.get_latest_sources()

    def link_notebooks(
        self, notebook: ProjectNotebook, related_notebook_id: str
    ) -> None:
        """Link this notebook to another related notebook."""
        if related_notebook_id not in notebook.related_notebooks:
            notebook.related_notebooks.append(related_notebook_id)
            self._save_notebook(notebook)
            print(f"Linked notebook '{notebook.project_id}' to '{related_notebook_id}'")

    def get_project_summary(self, notebook: ProjectNotebook) -> str:
        """Get a summary of the project notebook."""
        lines = [
            f"Project: {notebook.project_id}",
            f"Topic: {notebook.topic}",
            f"Created: {notebook.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"Updated: {notebook.updated_at.strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"Research Queries: {len(notebook.queries)}",
            f"Articles: {len(notebook.articles)}",
            f"Manuscript Versions: {len(notebook.manuscript_versions)}",
            f"Related Notebooks: {len(notebook.related_notebooks)}",
        ]

        if notebook.manuscript_versions:
            latest = notebook.manuscript_versions[-1]
            lines.extend(
                [
                    f"",
                    f"Latest Manuscript:",
                    f"  Version: {latest.version_number}",
                    f"  Title: {latest.title}",
                    f"  Word count: {latest.word_count}",
                    f"  Sources: {len(latest.sources)}",
                ]
            )

        return "\n".join(lines)


def create_project_notebook(
    topic: str, storage_path: Optional[str] = None
) -> ProjectNotebook:
    """Helper function to create a new project notebook."""
    manager = ProjectNotebookManager(storage_path)
    return manager.create_notebook(topic)


if __name__ == "__main__":
    manager = ProjectNotebookManager()

    print("Project Notebook Manager")
    print("=" * 40)
    print()

    projects = manager.list_projects()
    if projects:
        print("Existing projects:")
        for p in projects:
            print(f"  - {p.project_id}: {p.topic}")
    else:
        print("No projects yet.")

    print()
    print("Usage:")
    print("  from tools.project_notebook_manager import ProjectNotebookManager")
    print("  manager = ProjectNotebookManager()")
    print("  notebook = manager.create_notebook('your_topic')")
    print("  manager.add_research_results(notebook, articles, query)")
    print("  manager.add_manuscript_version(notebook, title, content, pmids)")
    print("  manager.update_with_new_research(notebook, new_articles, query)")
