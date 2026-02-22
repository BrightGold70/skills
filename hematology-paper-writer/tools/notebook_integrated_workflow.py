"""
Notebook-Integrated Research Workflow
====================================
Extends the research workflow to automatically create and manage
project-specific NotebookLM notebooks for each research topic.

Workflow:
1. Research topic is selected
2. PubMed search is performed
3. Project notebook is created with search results
4. Manuscript is drafted using notebook sources
5. When revising with new PubMed results, notebook is updated
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.draft_generator.research_workflow import ResearchWorkflow, WorkflowResult
from tools.project_notebook_manager import (
    ProjectNotebookManager,
    ProjectNotebook,
    create_project_notebook,
)


@dataclass
class NotebookIntegratedResult(WorkflowResult):
    """Extended result with notebook information."""

    notebook_id: str = ""
    notebook_path: str = ""
    articles_in_notebook: int = 0
    manuscript_versions: int = 0
    manuscript_docx_path: str = ""


class NotebookIntegratedWorkflow:
    """
    Research workflow with automatic NotebookLM notebook management.

    Each research topic gets its own notebook that tracks:
    - All PubMed searches and results
    - Manuscript versions
    - Related sources

    Usage:
        workflow = NotebookIntegratedWorkflow()

        # Run research with notebook management
        result = workflow.run(
            topic="asciminib chronic myeloid leukemia first-line",
            max_articles=30,
            output_dir="./output"
        )

        # Later, update with new research for revision
        workflow.update_with_new_research(
            project_id=result.notebook_id,
            new_topic="asciminib chronic myeloid leukemia",
            max_articles=10
        )
    """

    def __init__(
        self,
        journal: str = "blood_research",
        notebook_storage_path: Optional[str] = None,
        pubmed_api_key: Optional[str] = None,
    ):
        """Initialize the notebook-integrated workflow."""
        self.journal = journal
        self.notebook_manager = ProjectNotebookManager(notebook_storage_path)
        self.base_workflow = ResearchWorkflow(
            journal=journal, pubmed_api_key=pubmed_api_key
        )

    def run(
        self,
        topic: str,
        max_articles: int = 30,
        time_period: str = "5y",
        use_repeat: bool = True,
        include_web_search: bool = False,
        output_dir: str = ".",
        create_notebook: bool = True,
    ) -> NotebookIntegratedResult:
        """
        Run research workflow with notebook management.

        Args:
            topic: Research topic
            max_articles: Maximum PubMed articles to retrieve
            time_period: Time filter for PubMed (5y, 10y, all)
            use_repeat: Use multiple search strategies
            include_web_search: Include web search
            output_dir: Output directory for manuscript
            create_notebook: Whether to create project notebook

        Returns:
            NotebookIntegratedResult with manuscript and notebook info
        """
        print("=" * 70)
        print("📓 NOTEBOOK-INTEGRATED RESEARCH WORKFLOW")
        print("=" * 70)
        print(f"Topic: {topic}")
        print(f"Journal: {self.journal}")
        print(f"Output: {output_dir}")
        print()

        project_id = self._generate_project_id(topic)

        notebook = None
        if create_notebook:
            print("📓 Creating project notebook...")
            notebook = self.notebook_manager.create_notebook(
                topic=topic,
                project_id=project_id,
                metadata={"journal": self.journal, "time_period": time_period},
            )
            print(f"   Notebook ID: {notebook.project_id}")
            print()

        base_result = self.base_workflow.run(
            topic=topic,
            max_articles=max_articles,
            time_period=time_period,
            use_repeat=use_repeat,
            include_web_search=include_web_search,
            output_dir=output_dir,
        )

        articles = []
        try:
            from tools.draft_generator.pubmed_searcher import PubMedSearcher

            searcher = PubMedSearcher()
            articles = searcher.search_by_topic(topic, max_results=max_articles)
        except Exception as e:
            print(f"Warning: Could not fetch articles for notebook: {e}")

        if notebook and articles:
            print("📓 Saving research to notebook...")
            self.notebook_manager.add_research_results(
                notebook=notebook,
                articles=articles,
                query_text=topic,
                databases=["PubMed"],
                max_results=max_articles,
            )

            if base_result.manuscript_path:
                with open(base_result.manuscript_path, "r") as f:
                    content = f.read()

                pmids = [str(a.pmid) for a in articles if hasattr(a, "pmid")]
                self.notebook_manager.add_manuscript_version(
                    notebook=notebook,
                    title=topic,
                    content=content,
                    sources=pmids,
                    notes=f"Initial draft - {datetime.now().strftime('%Y-%m-%d')}",
                )
            print()

        result = NotebookIntegratedResult(
            topic=base_result.topic,
            journal=base_result.journal,
            manuscript_path=base_result.manuscript_path,
            quality_report=base_result.quality_report,
            reference_report=base_result.reference_report,
            suggestions=base_result.suggestions,
            articles_found=base_result.articles_found,
            references_generated=base_result.references_generated,
            overall_score=base_result.overall_score,
            errors=base_result.errors,
            warnings=base_result.warnings,
            notebook_id=project_id,
            notebook_path=str(self.notebook_manager._get_project_file(project_id))
            if notebook
            else "",
            articles_in_notebook=len(notebook.articles) if notebook else 0,
            manuscript_versions=len(notebook.manuscript_versions) if notebook else 0,
        )

        if base_result.manuscript_path:
            md_path = Path(base_result.manuscript_path)
            docx_path = md_path.with_suffix(".docx")

            try:
                from tools.file_converter import FileConverter

                converter = FileConverter()
                converter.to_docx(
                    md_path.read_text(encoding="utf-8"), str(docx_path), title=topic
                )
                result.manuscript_docx_path = str(docx_path)
                print(f"📄 DOCX Manuscript: {docx_path}")
            except Exception as e:
                print(f"⚠️ DOCX conversion failed: {e}")

        print("=" * 70)
        print("✅ RESEARCH COMPLETE")
        print("=" * 70)
        if notebook:
            print(f"📓 Notebook: {result.notebook_id}")
            print(f"   Articles: {result.articles_in_notebook}")
            print(f"   Versions: {result.manuscript_versions}")
        print(f"📄 Manuscript (MD): {result.manuscript_path}")
        if hasattr(result, "manuscript_docx_path") and result.manuscript_docx_path:
            print(f"📄 Manuscript (DOCX): {result.manuscript_docx_path}")
        print(f"📊 Quality Score: {result.overall_score:.1%}")
        print()

        return result

    def update_with_new_research(
        self,
        project_id: str,
        new_topic: Optional[str] = None,
        max_articles: int = 10,
        time_period: str = "2y",
    ) -> Dict[str, Any]:
        """
        Update project notebook with new research for manuscript revision.

        Called when:
        - User searches PubMed again for the same topic
        - User wants to add more sources to existing manuscript

        Args:
            project_id: ID of the project notebook
            new_topic: Optional new search term (uses original topic if None)
            max_articles: Number of new articles to fetch
            time_period: Time filter for search

        Returns:
            Dict with update summary
        """
        notebook = self.notebook_manager.get_notebook(project_id)
        if not notebook:
            raise ValueError(f"Project notebook not found: {project_id}")

        topic = new_topic or notebook.topic

        print("=" * 70)
        print("📓 UPDATING PROJECT NOTEBOOK")
        print("=" * 70)
        print(f"Project: {project_id}")
        print(f"New search: {topic}")
        print()

        articles = []
        try:
            from tools.draft_generator.pubmed_searcher import PubMedSearcher

            searcher = PubMedSearcher()
            articles = searcher.search_by_topic(topic, max_results=max_articles)
            print(f"Found {len(articles)} new articles")
        except Exception as e:
            print(f"Warning: PubMed search failed: {e}")

        if articles:
            summary = self.notebook_manager.update_with_new_research(
                notebook=notebook,
                new_articles=articles,
                query_text=topic,
                databases=["PubMed"],
            )
            print(f"Added {summary['new_articles']} new articles")
            print(f"Total articles now: {summary['total_articles']}")
            return summary
        else:
            return {"error": "No new articles found"}

    def add_manuscript_revision(
        self,
        project_id: str,
        manuscript_title: str,
        manuscript_content: str,
        source_pmids: List[str],
        notes: str = "",
    ) -> None:
        """
        Add a new manuscript version to the notebook.

        Called after:
        - Drafting a new version of the manuscript
        - Editing/revising the manuscript

        Args:
            project_id: ID of the project notebook
            manuscript_title: Title of the manuscript
            manuscript_content: Full manuscript text
            source_pmids: List of PMIDs used as sources
            notes: Optional notes about this revision
        """
        notebook = self.notebook_manager.get_notebook(project_id)
        if not notebook:
            raise ValueError(f"Project notebook not found: {project_id}")

        self.notebook_manager.add_manuscript_version(
            notebook=notebook,
            title=manuscript_title,
            content=manuscript_content,
            sources=source_pmids,
            notes=notes,
        )

        print(f"Added manuscript v{len(notebook.manuscript_versions)} to notebook")

    def get_manuscript_sources(
        self,
        project_id: str,
        include_all: bool = False,
    ) -> List[Any]:
        """
        Get sources for manuscript from notebook.

        Args:
            project_id: ID of the project notebook
            include_all: If True, include all articles. If False, only latest.

        Returns:
            List of PubMed articles
        """
        notebook = self.notebook_manager.get_notebook(project_id)
        if not notebook:
            raise ValueError(f"Project notebook not found: {project_id}")

        return self.notebook_manager.get_sources_for_manuscript(notebook, include_all)

    def list_project_notebooks(self) -> List[ProjectNotebook]:
        """List all project notebooks."""
        return self.notebook_manager.list_projects()

    def get_notebook_summary(self, project_id: str) -> str:
        """Get summary of a project notebook."""
        notebook = self.notebook_manager.get_notebook(project_id)
        if not notebook:
            return f"Not found: {project_id}"
        return self.notebook_manager.get_project_summary(notebook)

    def _generate_project_id(self, topic: str) -> str:
        """Generate project ID from topic."""
        import re

        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", topic.lower())
        safe = re.sub(r"_+", "_", safe)
        return f"project_{safe[:50]}"


def run_notebook_integrated_research(
    topic: str,
    journal: str = "blood_research",
    max_articles: int = 30,
    output_dir: str = ".",
) -> NotebookIntegratedResult:
    """
    Convenience function to run notebook-integrated research.

    Usage:
        result = run_notebook_integrated_research(
            topic="asciminib chronic myeloid leukemia first-line",
            journal="blood_research",
            max_articles=30,
            output_dir="./output"
        )

        print(f"Notebook: {result.notebook_id}")
        print(f"Manuscript: {result.manuscript_path}")
    """
    workflow = NotebookIntegratedWorkflow(journal=journal)
    return workflow.run(
        topic=topic,
        max_articles=max_articles,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    workflow = NotebookIntegratedWorkflow()

    print("Notebook-Integrated Research Workflow")
    print("=" * 40)
    print()

    projects = workflow.list_project_notebooks()
    if projects:
        print("Existing project notebooks:")
        for p in projects:
            print(f"  - {p.project_id}: {p.topic}")
            print(
                f"    Articles: {len(p.articles)}, Versions: {len(p.manuscript_versions)}"
            )
    else:
        print("No project notebooks yet.")

    print()
    print("Usage:")
    print(
        "  from tools.notebook_integrated_workflow import run_notebook_integrated_research"
    )
    print("  result = run_notebook_integrated_research('your topic')")
