"""
Research Workflow Orchestrator
Coordinates the complete manuscript creation workflow:
1. Research (PubMed + Web search)
2. Draft creation
3. Quality check
4. Reference verification
5. Improvement suggestions
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.draft_generator.pubmed_searcher import PubMedSearcher, search_pubmed
from tools.draft_generator.manuscript_drafter import (
    ManuscriptDrafter,
    Journal,
    JOURNAL_GUIDELINES,
    create_manuscript,
)


@dataclass
class WorkflowResult:
    """Result of the research workflow."""

    topic: str
    journal: str
    manuscript_path: str = ""
    quality_report: Dict[str, Any] = field(default_factory=dict)
    reference_report: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[Dict] = field(default_factory=list)
    articles_found: int = 0
    references_generated: int = 0
    overall_score: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ResearchWorkflow:
    """
    Orchestrates the complete manuscript creation workflow.
    """

    def __init__(
        self,
        journal: str = "blood_research",
        pubmed_api_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
    ):
        """
        Initialize the research workflow.

        Args:
            journal: Target journal
            pubmed_api_key: NCBI API key
            tavily_api_key: Tavily API key for web search
        """
        self.journal = journal
        self.pubmed_api_key = pubmed_api_key
        self.tavily_api_key = tavily_api_key

        # Map journal string to enum
        journal_map = {
            "blood_research": Journal.BLOOD_RESEARCH,
            "blood": Journal.BLOOD,
            "blood_advances": Journal.BLOOD_ADVANCES,
            "jco": Journal.JCO,
            "bjh": Journal.BJH,
            "leukemia": Journal.LEUKEMIA,
            "haematologica": Journal.HAEMATOLOGICA,
        }
        self.journal_enum = journal_map.get(journal.lower(), Journal.BLOOD_RESEARCH)
        self.journal_specs = JOURNAL_GUIDELINES[self.journal_enum]

    def run(
        self,
        topic: str,
        max_articles: int = 50,
        time_period: str = "all",
        use_repeat: bool = True,
        include_web_search: bool = True,
        output_dir: str = ".",
    ) -> WorkflowResult:
        """
        Run the complete research workflow.

        Args:
            topic: Research topic
            max_articles: Maximum articles to retrieve
            time_period: Time filter (all, 1y, 2y, 5y, 10y)
            use_repeat: Use multiple search strategies
            include_web_search: Include web search
            output_dir: Directory for output files

        Returns:
            WorkflowResult with all outputs
        """
        print("=" * 70)
        print("🔬 RESEARCH WORKFLOW - STARTED")
        print("=" * 70)
        print(f"Topic: {topic}")
        print(f"Journal: {self.journal_specs.name}")
        print(f"Output: {output_dir}")
        print()

        result = WorkflowResult(topic=topic, journal=self.journal)

        # Step 1: Research Phase
        print("📚 STEP 1: LITERATURE SEARCH")
        print("-" * 50)

        articles = self._search_literature(topic, max_articles, time_period, use_repeat)
        result.articles_found = len(articles)

        if articles:
            print(f"✅ Found {len(articles)} relevant articles from PubMed")
            for art in articles[:5]:
                title = ""
                if hasattr(art, "title"):
                    title = art.title or ""
                elif isinstance(art, dict):
                    title = art.get("title", "") or ""
                print(f"  - {title[:60]}...")
        else:
            print("⚠️ No articles found from PubMed")
            result.warnings.append("No PubMed articles found")

        if include_web_search:
            web_info = self._search_web(topic)
            if web_info:
                print(f"✅ Web search completed: {len(web_info)} sources")
            else:
                print("⚠️ Web search unavailable or no results")

        print()

        # Step 2: Draft Creation
        print("📝 STEP 2: MANUSCRIPT DRAFT CREATION")
        print("-" * 50)

        drafter = ManuscriptDrafter(self.journal_enum)
        manuscript_text = drafter.create_draft(topic, articles)

        # Save manuscript
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        output_path = (
            Path(output_dir) / f"{self._sanitize_filename(topic)}_{timestamp}.md"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(manuscript_text)

        result.manuscript_path = str(output_path)
        result.references_generated = len(articles)

        print(f"✅ Draft created: {output_path}")
        print(f"   Word count: {len(manuscript_text.split())}")
        print(f"   References: {len(articles)}")
        print()

        # Step 3: Quality Check
        print("📊 STEP 3: QUALITY CHECK")
        print("-" * 50)

        from tools.quality_analyzer import ManuscriptQualityAnalyzer

        analyzer = ManuscriptQualityAnalyzer(self.journal)
        quality_score = analyzer.analyze_manuscript(str(output_path))

        result.overall_score = quality_score.overall_score

        print(f"✅ Quality analysis completed")
        print(f"   Overall Score: {quality_score.overall_score:.1%}")
        print()

        # Step 4: Reference Verification
        print("🔗 STEP 4: REFERENCE VERIFICATION")
        print("-" * 50)

        from tools.reference_manager import ReferenceManager

        ref_manager = ReferenceManager(self.journal)
        references = ref_manager.parse_references(manuscript_text)

        from tools.pubmed_verifier import PubMedVerifier

        verifier = PubMedVerifier()

        valid_count = 0
        for ref in references:
            if hasattr(ref, "title") and ref.title:
                title = ref.title
            else:
                continue
            try:
                record = verifier.search_by_title(title)
                if record:
                    valid_count += 1
            except Exception:
                pass

        result.reference_report = {
            "total": len(references),
            "valid": valid_count,
            "accuracy": valid_count / len(references) * 100 if references else 0,
        }

        print(f"✅ Reference verification completed")
        print(f"   Total references: {len(references)}")
        print(f"   Validated: {valid_count}")
        print()

        # Step 5: Improvement Suggestions
        print("💡 STEP 5: IMPROVEMENT SUGGESTIONS")
        print("-" * 50)

        from tools.content_enhancer import analyze_and_enhance

        enhancement = analyze_and_enhance(str(output_path), self.journal)
        suggestions = enhancement.get("suggestions", [])

        result.suggestions = [
            {
                "type": s.type.value if hasattr(s.type, "value") else str(s.type),
                "topic": s.topic,
                "reason": s.reason,
            }
            for s in suggestions[:10]
        ]

        print(f"✅ Generated {len(suggestions)} enhancement suggestions")
        for i, sug in enumerate(result.suggestions[:5], 1):
            print(f"   {i}. [{sug['topic']}] {sug['reason'][:60]}...")
        print()

        # Summary
        print("=" * 70)
        print("📋 WORKFLOW SUMMARY")
        print("=" * 70)
        print(f"Manuscript: {output_path}")
        print(f"Articles Found: {result.articles_found}")
        print(f"References: {result.references_generated}")
        print(f"Quality Score: {result.overall_score:.1%}")
        print(f"Suggestions: {len(result.suggestions)}")
        print()

        if result.warnings:
            print("⚠️ Warnings:")
            for w in result.warnings:
                print(f"   - {w}")
            print()

        print("=" * 70)
        print("✅ RESEARCH WORKFLOW COMPLETED")
        print("=" * 70)

        return result

    def _search_literature(
        self,
        topic: str,
        max_articles: int,
        time_period: str = "all",
        use_repeat: bool = True,
    ) -> List[Any]:
        """Search PubMed for relevant articles."""
        searcher = PubMedSearcher(self.pubmed_api_key)
        try:
            return searcher.search_by_topic(
                topic,
                max_results=max_articles,
                time_period=time_period,
                use_repeat=use_repeat,
            )
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
        finally:
            searcher.close()

    def _search_web(self, topic: str, require_permission: bool = False) -> List[Dict]:
        """Search the web for additional information using Tavily."""
        try:
            from tools.draft_generator.tavily_searcher import TavilySearcher

            api_key = self.tavily_api_key or os.environ.get("TAVILY_API_KEY")
            if not api_key:
                print("⚠️ TAVILY_API_KEY not set, skipping web search")
                return []

            searcher = TavilySearcher(api_key=api_key)
            results = searcher.search(topic, max_results=10)

            if require_permission:
                from tools.draft_generator.reference_permission_workflow import (
                    ReferencePermissionWorkflow,
                    interactive_permission_review,
                )

                permitted_results = interactive_permission_review(topic, results)
                results = permitted_results

            return [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content,
                    "published_date": r.published_date,
                    "category": getattr(r, "category", "unknown").value
                    if hasattr(getattr(r, "category", None), "value")
                    else str(getattr(r, "category", "unknown")),
                    "permission_status": getattr(r, "permission_status", "auto"),
                }
                for r in results
            ]
        except ImportError:
            print("⚠️ Tavily searcher not available")
        except Exception as e:
            print(f"Web search error: {e}")
        return []

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as filename."""
        # Remove special characters, replace spaces with underscores
        import re

        name = re.sub(r"[^\w\s-]", "", name)
        name = name.strip().replace(" ", "_")
        return name[:50]

    def save_report(
        self, result: WorkflowResult, output_path: str = "workflow_report.json"
    ):
        """Save workflow result as JSON report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "topic": result.topic,
            "journal": result.journal,
            "manuscript_path": result.manuscript_path,
            "quality_report": result.quality_report,
            "reference_report": result.reference_report,
            "suggestions": result.suggestions,
            "articles_found": result.articles_found,
            "references_generated": result.references_generated,
            "overall_score": result.overall_score,
            "errors": result.errors,
            "warnings": result.warnings,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"Report saved to: {output_path}")


def run_research_workflow(
    topic: str,
    journal: str = "blood_research",
    max_articles: int = 20,
    include_web_search: bool = True,
) -> WorkflowResult:
    """
    Convenience function to run the complete research workflow.

    Args:
        topic: Research topic
        journal: Target journal
        max_articles: Maximum articles to retrieve
        include_web_search: Include web search

    Returns:
        WorkflowResult
    """
    workflow = ResearchWorkflow(journal)
    return workflow.run(topic, max_articles, include_web_search)


if __name__ == "__main__":
    # Test
    print("Testing research workflow...")

    topic = "Asciminib as first-line therapy for chronic myeloid leukemia"

    result = run_research_workflow(
        topic=topic, journal="blood_research", max_articles=10, include_web_search=False
    )

    print(f"\nResult: {result.manuscript_path}")
