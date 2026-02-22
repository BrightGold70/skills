#!/usr/bin/env python3
"""
Hematology Paper Writer CLI

A command-line interface for writing, analyzing, and improving hematology
manuscripts for publication in journals like Blood, Blood Advances, JCO, and BJH.

Usage:
    hpw <command> [options]

Commands:
    check-quality        Analyze manuscript quality against journal standards
    verify-references   Verify citations against PubMed database
    edit-manuscript     Enhance and improve manuscript content
    generate-report     Generate comprehensive manuscript report
    search-pubmed       Search PubMed for articles on a topic
    create-draft        Create manuscript draft from research topic
    research            Complete workflow: search, draft, quality check, verify
    convert             Convert between DOCX, PDF, PPTX, and Markdown
    check-concordance   Check citation-reference concordance
"""

import argparse
import json
import sys
import textwrap
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import re

# Add skill package to path
sys.path.insert(0, str(Path(__file__).parent))

from tools import (
    ManuscriptQualityAnalyzer,
    ReferenceManager,
    PubMedVerifier,
    ContentEnhancer,
    ManuscriptRevisor,
)
from tools.pubmed_verifier import (
    BatchReferenceVerifier,
    ReferenceParser,
)

# Draft generator imports
from tools.draft_generator import (
    PubMedSearcher,
    ManuscriptDrafter,
    Journal,
    JOURNAL_GUIDELINES,
    ResearchWorkflow,
    run_research_workflow,
    ManuscriptStructure,
    EnhancedManuscriptDrafter,
    DocumentType,
    ReferenceStyle,
    create_enhanced_manuscript,
)

# File converter imports
from tools.file_converter import (
    FileConverter,
    ConvertedDocument,
    convert_document,
    markdown_to_docx,
)

# Citation concordance checker
from tools.draft_generator.manuscript_editor import (
    ManuscriptEditor,
    check_manuscript_quality,
)

# Citation concordance checker
from tools.citation_concordance import (
    check_concordance,
    check_concordance_verbose,
    validate_reference_list,
    ConcordanceResult,
)


DEFAULT_OUTPUT_DIR = "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/Manuscript"


def get_timestamp() -> str:
    """Generate timestamp string in YYYYMMDDHHMM format for version control."""
    return datetime.now().strftime("%Y%m%d%H%M")


def add_version_suffix(filename: str) -> str:
    """Add timestamp version suffix to filename before extension.

    Example: "manuscript.md" -> "manuscript-202602121317.md"
    """
    path = Path(filename)
    stem = path.stem
    suffix = path.suffix
    timestamp = get_timestamp()
    return f"{stem}-{timestamp}{suffix}"


# Source discovery
from tools.source_discovery import (
    SourceDiscovery,
    SourceVerifier,
    AcademicSource,
    SourceType,
    IEEEFormatter,
)


# ============================================================================
# Output Formatting
# ============================================================================


class OutputFormatter:
    """Provides styled output formatting for CLI."""

    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
    }

    @classmethod
    def color(cls, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['reset']}"

    @classmethod
    def header(cls, text: str) -> str:
        """Format as header."""
        return cls.color(f"\n{'=' * 60}\n{text}\n{'=' * 60}\n", "cyan")

    @classmethod
    def section(cls, text: str) -> str:
        """Format as section."""
        return cls.color(f"\n{'-' * 40}\n{text}\n{'-' * 40}\n", "blue")

    @classmethod
    def success(cls, text: str) -> str:
        """Format as success message."""
        return cls.color(f"✓ {text}", "green")

    @classmethod
    def warning(cls, text: str) -> str:
        """Format as warning message."""
        return cls.color(f"⚠ {text}", "yellow")

    @classmethod
    def error(cls, text: str) -> str:
        """Format as error message."""
        return cls.color(f"✗ {text}", "red")

    @classmethod
    def info(cls, text: str) -> str:
        """Format as info message."""
        return cls.color(f"ℹ {text}", "magenta")

    @classmethod
    def table(cls, headers: list, rows: list) -> str:
        """Format as table."""
        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Format header
        header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        separator = "  ".join("-" * w for w in col_widths)

        # Format rows
        row_lines = []
        for row in rows:
            row_line = "  ".join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
            )
            row_lines.append(row_line)

        return f"{header_line}\n{separator}\n" + "\n".join(row_lines)


def format_score(score: float) -> str:
    """Format a score with color based on value."""
    if score >= 0.7:
        return OutputFormatter.color(f"{score:.0%}", "green")
    elif score >= 0.5:
        return OutputFormatter.color(f"{score:.0%}", "yellow")
    else:
        return OutputFormatter.color(f"{score:.0%}", "red")


# ============================================================================
# Utility Functions
# ============================================================================


def load_manuscript(path: str) -> str:
    """Load manuscript from file."""
    path = Path(path)
    if path.suffix == ".docx":
        try:
            from docx import Document

            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])
        except ImportError:
            print(
                "Error: python-docx not installed. Please install with: pip install python-docx"
            )
            sys.exit(1)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def save_manuscript(path: str, content: str) -> None:
    """Save manuscript to file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class ProgressBar:
    """Simple progress bar for CLI."""

    def __init__(self, total: int, description: str = ""):
        """Initialize progress bar."""
        self.total = total
        self.description = description
        self.current = 0

    def __enter__(self):
        """Enter context manager."""
        print(f"{self.description}: ", end="", flush=True)
        self.update(0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.update(self.total)
        print()
        return False

    def update(self, value: int):
        """Update progress."""
        self.current = value
        filled = int(30 * self.current // self.total)
        bar = "█" * filled + "░" * (30 - filled)
        print(
            f"\r{self.description}: [{bar}] {self.current}/{self.total}",
            end="",
            flush=True,
        )


# ============================================================================
# NEW COMMANDS: search-pubmed, create-draft, research
# ============================================================================


def cmd_check_concordance(args):
    """Check citation-reference concordance in manuscript."""
    OutputFormatter.header("Citation-Reference Concordance Check")

    print(f"Input: {args.input}")
    print()

    try:
        result = check_concordance(args.input)

        # Display summary
        print(f"Total citations in text: {result.total_citations}")
        print(f"Total references found: {result.total_references}")
        print()

        if result.is_concordant:
            print(f"✅ SUCCESS: Concordance confirmed on all counts.")
        else:
            if result.missing_in_references:
                print(
                    f"[ERROR] Cited in text but missing in references ({len(result.missing_in_references)}):"
                )
                for num in result.missing_in_references:
                    print(f"  - [{num}]")
                print()

            if result.uncited_references:
                print(
                    f"[WARNING] In reference list but never cited ({len(result.uncited_references)}):"
                )
                for num in result.uncited_references:
                    print(f"  - [{num}]")
                print()

        # Format validation
        if args.validate_format:
            print(f"{OutputFormatter.section('Reference Format Validation')}")
            format_results = validate_reference_list(args.input)
            print(f"Total references: {format_results.get('total_references', 0)}")
            print(f"Valid format: {format_results.get('valid_format', 0)}")
            print(f"Format rate: {format_results.get('format_rate', 0):.1%}")

            # Show issues
            ref_results = format_results.get("reference_results", {})
            issues = {k: v for k, v in ref_results.items() if not v["is_valid"]}
            if issues:
                print("References with format issues:")
                for num, validation in list(issues.items())[:5]:
                    print(f"  [{num}]: {', '.join(validation['issues'])}")

        # Save JSON if requested
        if args.json:
            json_data = result.to_dict()
            if args.validate_format:
                json_data["format_validation"] = validate_reference_list(args.input)

            import json

            with open(args.json, "w") as f:
                json.dump(json_data, f, indent=2)
            print(f"{OutputFormatter.success(f'Results saved to: {args.json}')}")

        return 0 if result.is_concordant else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_create_enhanced(args):
    """Create enhanced manuscript with academic writing guidelines."""
    from tools.draft_generator import (
        EnhancedManuscriptDrafter,
        ManuscriptStructure,
        DocumentType,
        ReferenceStyle,
    )

    OutputFormatter.header(f"Enhanced Manuscript Creation")

    # Map document type
    doc_types = {
        "research_paper": DocumentType.RESEARCH_PAPER,
        "literature_review": DocumentType.LITERATURE_REVIEW,
        "systematic_review": DocumentType.SYSTEMATIC_REVIEW,
        "clinical_trial": DocumentType.CLINICAL_TRIAL,
        "case_report": DocumentType.CASE_REPORT,
    }

    # Map reference style
    ref_styles = {
        "vancouver": ReferenceStyle.VANCOUVER,
        "ieee": ReferenceStyle.IEEE,
        "apa": ReferenceStyle.APA,
    }

    doc_type = doc_types.get(args.document_type, DocumentType.RESEARCH_PAPER)
    ref_style = ref_styles.get(args.reference_style, ReferenceStyle.VANCOUVER)

    print(f"Topic: {args.topic}")
    print(f"Document Type: {doc_type.value}")
    print(f"Reference Style: {ref_style.value}")
    print()

    # Create manuscript structure
    drafter = EnhancedManuscriptDrafter(
        document_type=doc_type, reference_style=ref_style
    )

    structure = drafter.create_manuscript(
        title=args.topic, keywords=args.keywords.split(",") if args.keywords else None
    )

    # Display structure
    print(f"Manuscript Structure:")
    print(f"  Title: {structure.title}")
    print(f"  Word Count: {structure.word_count}")
    print(f"  References: {structure.reference_count}")
    print(f"  Keywords: {', '.join(structure.keywords)}")
    print(f"  Sections: {len(structure.sections)}")
    for section in structure.sections:
        print(f"    - {section.title}: {section.word_count} words")
    print()

    # Generate manuscript
    manuscript = drafter.format_manuscript(structure)

    # Save output
    if args.output:
        output_path = add_version_suffix(args.output)
        if not os.path.isabs(output_path):
            output_path = os.path.join(DEFAULT_OUTPUT_DIR, output_path)
    else:
        safe_name = f"{args.topic[:30].replace(' ', '_')}_enhanced"
        output_path = os.path.join(
            DEFAULT_OUTPUT_DIR, f"{safe_name}-{get_timestamp()}.md"
        )
    with open(output_path, "w") as f:
        f.write(manuscript)
    print(f"{OutputFormatter.success(f'Manuscript saved to: {output_path}')}")

    # Run academic style check
    try:
        from tools.draft_generator.manuscript_editor import ManuscriptEditor

        editor = ManuscriptEditor(target_journal="blood_research")
        print(f"\n{OutputFormatter.section('Academic Style Analysis')}")
        style_issues = editor.check_style(manuscript)
        total_issues = sum(len(issues) for issues in style_issues.values())
        if total_issues == 0:
            print("✅ No style issues detected!")
        else:
            print(f"Found {total_issues} style issues")

        # Blood Research compliance check
        print(f"\n{OutputFormatter.section('Blood Research Compliance')}")
        compliance = editor.check_blood_research_compliance(manuscript)
        for check, (passed, msg) in compliance.items():
            icon = "✅" if passed else "❌"
            print(f"  {icon} {check.title()}: {msg}")

        # Pre-output validation
        is_valid, msg = editor.validate_before_output(manuscript)
        print(f"\n{OutputFormatter.section('Pre-Output Validation')}")
        print(f"  {'✅' if is_valid else '❌'} {msg}")
    except Exception as e:
        print(f"⚠️ Style check skipped: {e}")

    # Generate QA checklist
    checklist = drafter.generate_qa_checklist(structure)
    print(f"\n{OutputFormatter.section('Quality Assurance Checklist')}")
    for category, items in checklist.items():
        print(f"\n{category.upper()}:")
        for item in items:
            status_icon = (
                "✅"
                if item["status"] == "PASS"
                else "❌"
                if item["status"] == "FAIL"
                else "⚠️"
            )
            print(f"  {status_icon} {item['check']}: {item['status']}")

    return 0


def cmd_convert(args):
    """Convert between document formats (DOCX, PDF, PPTX, Markdown)."""
    from tools.file_converter import FileConverter

    OutputFormatter.header(f"File Conversion")

    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    print(f"Format: {args.format}")
    print()

    try:
        converter = FileConverter()

        if args.format == "docx":
            # Convert to DOCX
            with open(args.input, "r") as f:
                markdown_text = f.read()
            converter.to_docx(
                markdown_text, args.output, title=args.title or "Manuscript"
            )
            print(f"✅ Converted to DOCX: {args.output}")
        else:
            # Convert from DOCX/PDF/PPTX
            doc = converter.convert(args.input, args.format)
            with open(args.output, "w") as f:
                f.write(doc.text)
            print(f"✅ Converted to Markdown: {args.output}")
            print(f"   Text length: {len(doc.text)} characters")
            print(f"   Metadata: {doc.metadata}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_search_pubmed(args):
    """Search PubMed for articles on a topic."""
    from tools.draft_generator import PubMedSearcher

    OutputFormatter.header("PubMed Literature Search")

    print(f"Searching PubMed for: {args.topic}")
    print(f"Max results: {args.max_results}")
    print(f"Time period: {args.time_period}")
    print(f"Repeat search: {'Yes' if not args.no_repeat else 'No'}")
    print()

    searcher = PubMedSearcher(api_key=args.api_key)
    try:
        articles = searcher.search_by_topic(
            args.topic,
            max_results=args.max_results,
            time_period=getattr(args, "time_period", "all"),
            use_repeat=not getattr(args, "no_repeat", False),
        )

        print(f"Found {len(articles)} articles:")
        print()

        for i, art in enumerate(articles, 1):
            print(f"{i}. {art.title}")
            print(f"   PMID: {art.pmid} | {art.journal} ({art.year})")
            authors_str = ", ".join(art.authors[:3])
            if len(art.authors) > 3:
                authors_str += " et al."
            print(f"   Authors: {authors_str}")
            if art.doi:
                print(f"   DOI: {art.doi}")
            print()

        # Save to file if requested
        if args.output:
            import json

            data = [
                {
                    "pmid": art.pmid,
                    "title": art.title,
                    "authors": art.authors,
                    "journal": art.journal,
                    "year": art.year,
                    "doi": art.doi,
                    "abstract": art.abstract[:500] + "..."
                    if len(art.abstract) > 500
                    else art.abstract,
                    "mesh_terms": art.mesh_terms,
                }
                for art in articles
            ]

            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Results saved to: {args.output}")

        return 0 if articles else 1

    finally:
        searcher.close()


def cmd_create_draft(args):
    """Create a manuscript draft from research topic."""
    from tools.draft_generator import ManuscriptDrafter, Journal, JOURNAL_GUIDELINES

    OutputFormatter.header("Manuscript Draft Creation")

    journal = args.journal if args.journal else "blood_research"
    journal_enum = Journal.BLOOD_RESEARCH
    for j in Journal:
        if j.value == journal:
            journal_enum = j
            break

    journal_specs = JOURNAL_GUIDELINES[journal_enum]

    print(f"Topic: {args.topic}")
    print(f"Target Journal: {journal_specs.name}")
    print(f"Journal URL: {journal_specs.url}")
    print(f"Max articles: {args.max_articles}")
    print(f"Time period: {args.time_period}")
    print()

    # Search for articles
    articles = []
    if not args.no_search:
        print("Searching for relevant literature...")
        from tools.draft_generator import PubMedSearcher

        searcher = PubMedSearcher(api_key=args.api_key)
        try:
            articles = searcher.search_by_topic(
                args.topic,
                max_results=args.max_articles,
                time_period=getattr(args, "time_period", "all"),
                use_repeat=not getattr(args, "no_repeat", False),
            )
            print(f"Found {len(articles)} relevant articles")
        finally:
            searcher.close()

    # Create draft
    print()
    print("Creating manuscript draft...")
    drafter = ManuscriptDrafter(journal_enum)

    manuscript = drafter.create_draft(
        topic=args.topic, articles=articles, study_type=args.study_type
    )

    # Save manuscript
    if args.output:
        output_path = Path(add_version_suffix(args.output))
        if not os.path.isabs(str(output_path)):
            output_path = Path(DEFAULT_OUTPUT_DIR) / output_path
    else:
        safe_name = re.sub(r"[^\w\s-]", "", args.topic)[:30].replace(" ", "_")
        output_path = Path(DEFAULT_OUTPUT_DIR) / f"{safe_name}-{get_timestamp()}.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(manuscript)

    print(f"Manuscript saved to: {output_path}")
    print(f"Word count: {len(manuscript.split())}")
    print(f"References: {len(articles)}")

    # Optionally create DOCX
    if getattr(args, "docx", False):
        from tools.file_converter import FileConverter

        converter = FileConverter()
        docx_path = str(output_path).replace(".md", ".docx")
        converter.to_docx(manuscript, docx_path, title=args.topic)
        print(f"DOCX version: {docx_path}")

    print()

    # Optionally run quality check
    if args.check_quality:
        print("Running quality check...")
        from tools.quality_analyzer import ManuscriptQualityAnalyzer

        analyzer = ManuscriptQualityAnalyzer(journal)
        quality = analyzer.analyze_manuscript(str(output_path))
        print(f"Quality Score: {quality.overall_score:.1%}")

    return 0


def cmd_systematic_review(args):
    """Create a systematic review manuscript with PRISMA guidelines."""
    from tools.systematic_review_workflow import SystematicReviewWorkflow

    OutputFormatter.header("SYSTEMATIC REVIEW (PRISMA)")

    journal = args.journal if args.journal else "blood_research"

    print(f"Topic: {args.topic}")
    print(f"Target Journal: {journal}")
    print(f"Max articles: {args.max_articles}")
    print(f"Time period: {args.time_period}")

    if args.notebook_path:
        print(f"Using existing notebook: {args.notebook_path}")
        print("Flow: EXISTING NOTEBOOK (PDF/PPT/MP3 sources)")
    elif args.source_files:
        print(f"Using source files: {args.source_files}")
        print("Flow: LOCAL SOURCE FILES (NotebookLM exports)")
    else:
        print("Flow: NEW NOTEBOOK (PubMed research)")

    pico = None
    if args.pico:
        pico = {
            "population": args.pico[0],
            "intervention": args.pico[1],
            "comparison": args.pico[2],
            "outcome": args.pico[3],
        }
        print(f"\nPICO Elements:")
        print(f"  Population: {pico['population']}")
        print(f"  Intervention: {pico['intervention']}")
        print(f"  Comparison: {pico['comparison']}")
        print(f"  Outcome: {pico['outcome']}")

    print()

    output_dir = args.output or DEFAULT_OUTPUT_DIR

    workflow = SystematicReviewWorkflow(journal=journal, pubmed_api_key=args.api_key)

    result = workflow.run(
        topic=args.topic,
        max_articles=args.max_articles,
        time_period=args.time_period,
        output_dir=output_dir,
        create_notebook=not args.no_notebook and not args.notebook_path,
        pico=pico,
        existing_notebook_path=args.notebook_path,
        source_files=args.source_files,
    )

    print(f"\nQuality Score: {result.overall_score:.1%}")
    print(f"Articles Found: {result.articles_found}")
    print(f"Articles Used: {result.articles_used}")

    if result.errors:
        print(f"\nErrors: {', '.join(result.errors)}")
    if result.warnings:
        print(f"Warnings: {', '.join(result.warnings)}")

    return 0


def cmd_research(args):
    """Run complete research workflow: search, draft, quality check, verify."""
    from tools.draft_generator import ResearchWorkflow

    OutputFormatter.header("COMPLETE RESEARCH WORKFLOW")

    journal = args.journal if args.journal else "blood_research"

    workflow = ResearchWorkflow(journal=journal, pubmed_api_key=args.api_key)

    result = workflow.run(
        topic=args.topic,
        max_articles=args.max_articles,
        time_period=getattr(args, "time_period", "all"),
        use_repeat=not getattr(args, "no_repeat", False),
        include_web_search=args.web_search,
        output_dir=args.output_dir or ".",
    )

    # Save JSON report
    if args.json:
        workflow.save_report(result, args.json)

    return 0 if not result.errors else 1


# ============================================================================
# ORIGINAL COMMANDS
# ============================================================================


def cmd_check_quality(args):
    """Check manuscript quality."""
    OutputFormatter.header("Manuscript Quality Analysis")

    # Load manuscript
    manuscript = load_manuscript(args.input)

    # Initialize analyzer
    analyzer = ManuscriptQualityAnalyzer(args.journal if args.journal else "blood")

    # Analyze
    with ProgressBar(3, "Analyzing") as progress:
        progress.update(1)
        quality_score = analyzer.analyze_manuscript(args.input)
        progress.update(1)
        progress.update(1)

    # Display results
    print(f"\nOverall Score: {format_score(quality_score.overall_score)}")

    # Extract individual scores for display
    structure_score = next(
        (
            v.score
            for k, v in quality_score.category_scores.items()
            if "structure" in k.value.lower()
        ),
        0,
    )
    clarity_score = next(
        (
            v.score
            for k, v in quality_score.category_scores.items()
            if "clarity" in k.value.lower()
        ),
        0,
    )
    completeness_score = next(
        (
            v.score
            for k, v in quality_score.category_scores.items()
            if "method" in k.value.lower()
        ),
        0,
    )

    print(f"\nDetailed Scores:")
    print(f"  Structure:   {format_score(structure_score / 100)}")
    print(f"  Clarity:     {format_score(clarity_score / 100)}")
    print(f"  Completeness:{format_score(completeness_score / 100)}")

    # Display issues by category
    print(f"\n{OutputFormatter.section('Issues Found')}")
    for cat_score in quality_score.category_scores.values():
        if cat_score.score < 100:
            print(
                f"  {OutputFormatter.warning(f'{cat_score.category.value}: {cat_score.score}%')}"
            )
            for issue in cat_score.issues[:3]:
                print(f"    • {issue}")

    # Display recommendations
    print(f"\n{OutputFormatter.section('Recommendations')}")
    for cat_score in quality_score.category_scores.values():
        for rec in cat_score.recommendations[:2]:
            print(f"  {OutputFormatter.info(f'[{cat_score.category.value}] {rec}')}")

    # Save JSON report if requested
    if args.json:
        all_issues = []
        all_recommendations = []
        for cat_score in quality_score.category_scores.values():
            all_issues.extend(cat_score.issues)
            all_recommendations.extend(cat_score.recommendations)

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": quality_score.overall_score,
            "structure_score": structure_score,
            "clarity_score": clarity_score,
            "completeness_score": completeness_score,
            "issues": all_issues,
            "recommendations": all_recommendations,
        }
        with open(args.json, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n{OutputFormatter.success(f'JSON report saved to: {args.json}')}")

    return 0 if quality_score.overall_score >= 0.7 else 1


def cmd_verify_references(args):
    """Verify references in manuscript."""
    OutputFormatter.header("Reference Verification")

    # Load manuscript
    manuscript = load_manuscript(args.input)

    # Initialize
    ref_manager = ReferenceManager(args.journal if args.journal else "blood")

    with ProgressBar(5, "Verifying references") as progress:
        # Parse references
        progress.update(1)
        references = ref_manager.parse_references(manuscript)
        print(f"\nFound {len(references)} references")

        # Initialize verifier
        progress.update(1)
        verifier = PubMedVerifier(api_key=args.api_key)

        # Verify each reference
        progress.update(1)
        results = []
        for ref in references:
            parsed = ref_manager._parse_reference(ref)
            if parsed.title:
                record = verifier.search_by_title(parsed.title)
                if record:
                    results.append(
                        {
                            "reference": ref[:60] + "..." if len(ref) > 60 else ref,
                            "status": "VALID",
                            "pmid": record.get("uid", "N/A"),
                            "title": record.get("title", "N/A"),
                        }
                    )
                else:
                    results.append(
                        {
                            "reference": ref[:60] + "..." if len(ref) > 60 else ref,
                            "status": "INVALID",
                            "pmid": "-",
                            "title": parsed.title[:50] + "..."
                            if len(parsed.title) > 50
                            else parsed.title,
                        }
                    )
            else:
                results.append(
                    {
                        "reference": ref[:60] + "..." if len(ref) > 60 else ref,
                        "status": "INVALID",
                        "pmid": "-",
                        "title": "Could not parse reference",
                    }
                )

        progress.update(1)
        progress.update(1)

    # Display summary
    valid_count = sum(1 for r in results if r["status"] == "VALID")
    invalid_count = len(results) - valid_count

    print(f"\n{OutputFormatter.section('Verification Summary')}")
    print(f"  Total:   {len(results)}")
    print(f"  Valid:   {format_score(valid_count / len(results) if results else 0)}")
    print(f"  Invalid: {invalid_count}")
    print(f"  Accuracy: {format_score(valid_count / len(results) if results else 0)}")

    # Display detailed results
    if results:
        print(f"\n{OutputFormatter.section('Detailed Results')}")
        headers = ["#", "Status", "PMID", "Title"]
        rows = []
        for i, r in enumerate(results[:20], 1):
            status_icon = "✓" if r["status"] == "VALID" else "✗"
            rows.append([i, status_icon, r["pmid"], r["title"][:50]])
        print(OutputFormatter.table(headers, rows))

    return 0 if invalid_count == 0 else 1


def cmd_edit_manuscript(args):
    """Edit and enhance manuscript."""
    OutputFormatter.header("Manuscript Enhancement")

    # Load manuscript
    manuscript = load_manuscript(args.input)

    # Enhance content
    from tools.content_enhancer import analyze_and_enhance

    with ProgressBar(4, "Analyzing manuscript") as progress:
        progress.update(1)
        analysis_result = analyze_and_enhance(
            args.input, args.journal if args.journal else "blood"
        )
        suggestions = analysis_result.get("suggestions", [])
        progress.update(1)
        progress.update(1)
        progress.update(1)

    # Display suggestions
    print(f"\nFound {len(suggestions)} enhancement suggestions")

    if suggestions:
        print(f"\n{OutputFormatter.section('Suggestions')}")
        for i, suggestion in enumerate(suggestions[: args.max_suggestions], 1):
            topic = (
                getattr(suggestion, "topic", "General")
                if hasattr(suggestion, "topic")
                else (
                    suggestion.get("topic")
                    if isinstance(suggestion, dict)
                    else "General"
                )
            )
            reason = (
                getattr(suggestion, "reason", "")
                if hasattr(suggestion, "reason")
                else (suggestion.get("reason") if isinstance(suggestion, dict) else "")
            )
            suggested = (
                getattr(suggestion, "suggested_text", "")
                if hasattr(suggestion, "suggested_text")
                else (
                    suggestion.get("suggested_text")
                    if isinstance(suggestion, dict)
                    else ""
                )
            )
            print(f"\n{i}. [{topic}] {OutputFormatter.info(reason)}")
            print(f"   Topic: {topic}")
            if suggested:
                print(
                    f'   Suggested: "{suggested[:200]}..."'
                    if len(suggested) > 200
                    else f'   Suggested: "{suggested}"'
                )

    # Save JSON if requested
    if args.json:
        json_data = []
        for s in suggestions:
            json_data.append(
                {
                    "type": s.type.value if hasattr(s.type, "value") else str(s.type),
                    "topic": getattr(s, "topic", "General"),
                    "reason": getattr(s, "reason", ""),
                }
            )
        with open(args.json, "w") as f:
            json.dump(json_data, f, indent=2)
        print(f"\n{OutputFormatter.success(f'Suggestions saved to: {args.json}')}")

    return 0


def cmd_generate_report(args):
    """Generate comprehensive manuscript report."""
    OutputFormatter.header(f"Manuscript Report: {Path(args.input).name}")

    # Load manuscript
    manuscript = load_manuscript(args.input)

    # Run all analyses
    with ProgressBar(5, "Generating comprehensive report") as progress:
        # Quality analysis
        progress.update(1)
        quality_analyzer = ManuscriptQualityAnalyzer(
            args.journal if args.journal else "blood"
        )
        quality_score = quality_analyzer.analyze_manuscript(args.input)

        # Reference parsing
        progress.update(1)
        ref_manager = ReferenceManager(args.journal if args.journal else "blood")
        references = ref_manager.parse_references(manuscript)

        # Content enhancement suggestions
        progress.update(1)
        from tools.content_enhancer import analyze_and_enhance as enhancer_analysis

        suggestions = enhancer_analysis(
            args.input, args.journal if args.journal else "blood"
        ).get("suggestions", [])

        # Manuscript state
        progress.update(1)
        # revision_history = revisor.get_revision_history()  # TODO: Fix this

        # Verify references if requested
        if args.verify_references:
            progress.update(1)
            verifier = PubMedVerifier(api_key=args.api_key)
            valid_count = 0
            for ref in references:
                parsed = ref_manager._parse_reference(ref_manager.format_reference(ref))
                if parsed.title:
                    record = verifier.search_by_title(parsed.title)
                    if record:
                        valid_count += 1
        else:
            valid_count = None
            progress.update(1)

    # Build report
    report_lines = []

    # Manuscript info
    report_lines.append(f"\n{OutputFormatter.section('Manuscript Information')}")
    report_lines.append(f"  File: {args.input}")
    report_lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"  Word Count: {len(manuscript.split())}")
    report_lines.append(f"  Character Count: {len(manuscript)}")

    # Quality Metrics
    report_lines.append(f"\n{OutputFormatter.section('Quality Metrics')}")
    report_lines.append(f"  Overall Score: {format_score(quality_score.overall_score)}")

    structure_score = next(
        (
            v.score
            for k, v in quality_score.category_scores.items()
            if "structure" in k.value.lower()
        ),
        0,
    )
    clarity_score = next(
        (
            v.score
            for k, v in quality_score.category_scores.items()
            if "clarity" in k.value.lower()
        ),
        0,
    )
    completeness_score = next(
        (
            v.score
            for k, v in quality_score.category_scores.items()
            if "method" in k.value.lower()
        ),
        0,
    )

    report_lines.append(f"  Structure Score:   {format_score(structure_score / 100)}")
    report_lines.append(f"  Clarity Score:     {format_score(clarity_score / 100)}")
    report_lines.append(
        f"  Completeness:      {format_score(completeness_score / 100)}"
    )

    # Issues
    report_lines.append(f"\n{OutputFormatter.section('Issues')}")
    for cat_score in quality_score.category_scores.values():
        if cat_score.score < 100:
            report_lines.append(f"  - {cat_score.category.value}: {cat_score.score}%")

    # Recommendations
    report_lines.append(f"\n{OutputFormatter.section('Recommendations')}")
    for cat_score in quality_score.category_scores.values():
        for rec in cat_score.recommendations[:2]:
            report_lines.append(f"  - [{cat_score.category.value}] {rec}")

    # References
    report_lines.append(f"\n{OutputFormatter.section('References')}")
    report_lines.append(f"  Total References: {len(references)}")
    if valid_count is not None:
        report_lines.append(f"  Validated: {valid_count}")

    # Enhancement Suggestions
    report_lines.append(f"\n{OutputFormatter.section('Enhancement Suggestions')}")
    report_lines.append(f"  Total Suggestions: {len(suggestions)}")
    for i, s in enumerate(suggestions[:10], 1):
        topic = getattr(s, "topic", "General")
        reason = getattr(s, "reason", "")
        report_lines.append(f"  {i}. [{topic}] {reason}")

    # Revision history (disabled)
    # if revision_history:
    #     report_lines.append(f"\n{OutputFormatter.section('Revision History')}")
    #     for rev in revision_history:
    #         report_lines.append(f"  - v{rev.version}: {rev.summary}")

    # Print report
    print("\n".join(report_lines))

    # Save report
    if args.output:
        report_text = "\n".join(report_lines)
        save_manuscript(args.output, report_text)
        print(f"\n{OutputFormatter.success(f'Report saved to: {args.output}')} ")

    # Save JSON if requested
    if args.json:
        json_report = {
            "timestamp": datetime.now().isoformat(),
            "file": args.input,
            "word_count": len(manuscript.split()),
            "overall_score": quality_score.overall_score,
            "structure_score": structure_score,
            "clarity_score": clarity_score,
            "completeness_score": completeness_score,
            "total_references": len(references),
            "validated_references": valid_count,
            "total_suggestions": len(suggestions),
        }
        with open(args.json, "w") as f:
            json.dump(json_report, f, indent=2)
        print(f"\n{OutputFormatter.success(f'JSON report saved to: {args.json}')}")

    return 0


def cmd_notebooklm(args):
    from tools.notebooklm_integration import (
        NotebookLMIntegration,
        initialize_all_notebooks,
    )

    OutputFormatter.header("NotebookLM Research Intelligence")

    if args.notebooklm_command == "status":
        integration = NotebookLMIntegration()
        print(integration.generate_setup_report())

    elif args.notebooklm_command == "query-classification":
        integration = NotebookLMIntegration()
        OutputFormatter.info(f"Querying classification for: {args.entity}")
        response = integration.query_classification(args.entity, args.type)
        print(f"\nEntity: {args.entity}")
        print(f"Type: {args.type}")
        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence}")

    elif args.notebooklm_command == "query-gvhd":
        integration = NotebookLMIntegration()
        OutputFormatter.info(f"Querying GVHD: {args.aspect}")
        response = integration.query_gvhd(args.aspect, args.organ)
        print(f"\nAspect: {args.aspect}")
        if args.organ:
            print(f"Organ: {args.organ}")
        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence}")

    elif args.notebooklm_command == "query-eln":
        integration = NotebookLMIntegration()
        version = args.version or ("2022" if args.disease == "AML" else "2025")
        OutputFormatter.info(f"Querying ELN {version} for {args.disease}: {args.topic}")
        response = integration.query_therapeutic(args.disease, args.topic, version)
        print(f"\nDisease: {args.disease}")
        print(f"Topic: {args.topic}")
        print(f"Version: ELN {version}")
        print(f"Answer: {response.answer}")
        print(f"Confidence: {response.confidence}")

    elif args.notebooklm_command == "validate-nomenclature":
        integration = NotebookLMIntegration()
        OutputFormatter.info(f"Validating nomenclature: {args.term}")
        response = integration.query_nomenclature(args.term, args.type)
        print(f"\nTerm: {args.term}")
        print(f"Correct notation: {response.answer}")
        print(f"Confidence: {response.confidence}")

    elif args.notebooklm_command == "initialize":
        OutputFormatter.info("Initializing NotebookLM notebooks...")
        integration = initialize_all_notebooks(args.reference_path)
        print("\nAll notebooks initialized successfully!")
        print(integration.generate_setup_report())

    return 0


def cmd_project_notebook(args):
    """Manage project notebooks for research topics."""
    from tools.project_notebook_manager import ProjectNotebookManager
    from tools.notebook_integrated_workflow import NotebookIntegratedWorkflow

    OutputFormatter.header("Project Notebook Management")

    manager = ProjectNotebookManager()

    if args.project_command == "create":
        OutputFormatter.info(f"Creating notebook for: {args.topic}")
        notebook = manager.create_notebook(
            topic=args.topic, project_id=args.id, metadata={"journal": args.journal}
        )
        print(f"\n✅ Created project notebook: {notebook.project_id}")
        print(f"   Topic: {notebook.topic}")
        print(f"   Storage: {manager._get_project_file(notebook.project_id)}")

    elif args.project_command == "list":
        projects = manager.list_projects()
        if projects:
            print(f"Found {len(projects)} project notebooks:\n")
            for p in projects:
                print(f"  {p.project_id}")
                print(f"    Topic: {p.topic}")
                print(
                    f"    Articles: {len(p.articles)}, Versions: {len(p.manuscript_versions)}"
                )
                print(f"    Updated: {p.updated_at.strftime('%Y-%m-%d %H:%M')}")
                print()
        else:
            print("No project notebooks found.")

    elif args.project_command == "status":
        notebook = manager.get_notebook(args.project_id)
        if not notebook:
            print(f"❌ Project not found: {args.project_id}")
            return 1
        print(manager.get_project_summary(notebook))

    elif args.project_command == "add-sources":
        workflow = NotebookIntegratedWorkflow()
        print(f"Searching PubMed: {args.query}")

        try:
            from tools.draft_generator.pubmed_searcher import PubMedSearcher

            searcher = PubMedSearcher()
            articles = searcher.search_by_topic(
                args.query, max_results=args.max_articles
            )
            print(f"Found {len(articles)} articles")
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return 1

        notebook = manager.get_notebook(args.project_id)
        if not notebook:
            print(f"❌ Project not found: {args.project_id}")
            return 1

        summary = manager.update_with_new_research(
            notebook=notebook,
            new_articles=articles,
            query_text=args.query,
        )
        print(f"\n✅ Updated notebook: {args.project_id}")
        print(f"   New articles: {summary.get('new_articles', 0)}")
        print(f"   Total articles: {summary.get('total_articles', 0)}")

    elif args.project_command == "add-manuscript":
        notebook = manager.get_notebook(args.project_id)
        if not notebook:
            print(f"❌ Project not found: {args.project_id}")
            return 1

        with open(args.manuscript_path, "r") as f:
            content = f.read()

        import re

        pmids = re.findall(r"\[(\d+)\]", content)

        manager.add_manuscript_version(
            notebook=notebook,
            title=args.manuscript_path.split("/")[-1],
            content=content,
            sources=pmids,
            notes=args.notes or "",
        )

        print(f"✅ Added manuscript to notebook: {args.project_id}")
        print(f"   Version: {len(notebook.manuscript_versions)}")
        print(f"   Sources cited: {len(pmids)}")

    return 0


# ============================================================================
# Argument Parser
# ============================================================================


def build_parser():
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="hpw",
        description=textwrap.dedent("""
            Hematology Paper Writer CLI
            Tools for writing, analyzing, and improving hematology manuscripts.
            
            NEW COMMANDS:
              research         Complete workflow: search literature, create draft, check quality
              search-pubmed    Search PubMed for articles on a topic
              create-draft     Generate manuscript draft from research topic
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              # Research workflow (all-in-one)
              hpw research "Asciminib first-line therapy CML" --journal blood_research
              
              # Search PubMed
              hpw search-pubmed "CAR-T cell therapy leukemia" --max-results 20
              
              # Create draft
              hpw create-draft "Novel mutations in myeloproliferative neoplasms" --journal blood
              
              # Analyze existing manuscript
              hpw check-quality manuscript.md --journal blood
              hpw verify-references manuscript.md
              hpw edit-manuscript manuscript.md --journal blood
              hpw generate-report manuscript.md --journal blood
        """),
    )

    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    subparsers = parser.add_subparsers(
        title="commands", dest="command", required=True, help="Available commands"
    )

    # check-quality command
    quality_parser = subparsers.add_parser(
        "check-quality", help="Analyze manuscript quality against journal standards"
    )
    quality_parser.add_argument(
        "input", help="Path to manuscript file (Markdown or text)"
    )
    quality_parser.add_argument(
        "--journal",
        choices=["blood", "blood-advances", "jco", "bjh"],
        help="Target journal for quality standards",
    )
    quality_parser.add_argument(
        "--json", metavar="FILE", help="Save results as JSON to FILE"
    )

    # verify-references command
    verify_parser = subparsers.add_parser(
        "verify-references", help="Verify citations against PubMed database"
    )
    verify_parser.add_argument("input", help="Path to manuscript file")
    verify_parser.add_argument(
        "--journal",
        choices=["blood", "blood-advances", "jco", "bjh"],
        help="Target journal style",
    )
    verify_parser.add_argument("--api-key", help="NCBI API key for higher rate limits")

    # edit-manuscript command
    edit_parser = subparsers.add_parser(
        "edit-manuscript", help="Enhance and improve manuscript content"
    )
    edit_parser.add_argument("input", help="Path to manuscript file")
    edit_parser.add_argument(
        "--journal",
        choices=["blood", "blood-advances", "jco", "bjh"],
        help="Target journal style",
    )
    edit_parser.add_argument(
        "--apply", action="store_true", help="Apply enhancement suggestions"
    )
    edit_parser.add_argument(
        "--output", metavar="FILE", help="Output file for enhanced manuscript"
    )
    edit_parser.add_argument(
        "--author", metavar="NAME", help="Author name for revision tracking"
    )
    edit_parser.add_argument(
        "--max-suggestions",
        type=int,
        default=20,
        help="Maximum number of suggestions to process (default: 20)",
    )
    edit_parser.add_argument(
        "--json", metavar="FILE", help="Save suggestions as JSON to FILE"
    )

    # generate-report command
    report_parser = subparsers.add_parser(
        "generate-report", help="Generate comprehensive manuscript report"
    )
    report_parser.add_argument("input", help="Path to manuscript file")
    report_parser.add_argument(
        "--journal",
        choices=["blood", "blood-advances", "jco", "bjh"],
        help="Target journal style",
    )
    report_parser.add_argument(
        "--output", metavar="FILE", help="Save report to FILE (text format)"
    )
    report_parser.add_argument(
        "--json", metavar="FILE", help="Save detailed results as JSON to FILE"
    )
    report_parser.add_argument(
        "--verify-references",
        action="store_true",
        help="Include reference verification in report",
    )
    report_parser.add_argument(
        "--api-key", help="NCBI API key for reference verification"
    )

    # convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Convert between document formats"
    )
    convert_parser.add_argument("input", help="Input file path")
    convert_parser.add_argument("output", help="Output file path")
    convert_parser.add_argument(
        "--format",
        choices=["md", "docx"],
        default="md",
        help="Target format: md (from docx/pdf/pptx) or docx (from md)",
    )
    convert_parser.add_argument("--title", help="Document title (for DOCX output)")

    # search-pubmed command
    search_parser = subparsers.add_parser(
        "search-pubmed", help="Search PubMed for articles on a topic"
    )
    search_parser.add_argument("topic", help="Search topic/keywords")
    search_parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of results per search (default: 50)",
    )
    search_parser.add_argument(
        "--time-period",
        choices=["all", "1y", "2y", "5y", "10y"],
        default="all",
        help="Filter by publication year: all, 1y (last year), 2y, 5y, 10y (default: all)",
    )
    search_parser.add_argument(
        "--no-repeat",
        action="store_true",
        help="Disable repeat search with multiple strategies",
    )
    search_parser.add_argument("--api-key", help="NCBI API key for higher rate limits")
    search_parser.add_argument(
        "--output", "-o", metavar="FILE", help="Save results to JSON file"
    )

    # create-draft command
    draft_parser = subparsers.add_parser(
        "create-draft", help="Create a manuscript draft from research topic"
    )
    draft_parser.add_argument("topic", help="Research topic for manuscript")
    draft_parser.add_argument(
        "--journal",
        choices=["blood_research", "blood", "blood-advances", "jco", "bjh"],
        default="blood_research",
        help="Target journal (default: blood_research)",
    )
    draft_parser.add_argument(
        "--study-type",
        choices=[
            "observational",
            "clinical_trial",
            "review",
            "meta_analysis",
            "case_series",
        ],
        default="observational",
        help="Type of study (default: observational)",
    )
    draft_parser.add_argument(
        "--max-articles",
        type=int,
        default=50,
        help="Maximum articles to include (default: 20)",
    )
    draft_parser.add_argument(
        "--time-period",
        choices=["all", "1y", "2y", "5y", "10y"],
        default="all",
        help="Filter PubMed search by year: all, 1y, 2y, 5y, 10y (default: all)",
    )
    draft_parser.add_argument(
        "--no-repeat",
        action="store_true",
        help="Disable repeat search with multiple strategies",
    )
    draft_parser.add_argument(
        "--no-search",
        action="store_true",
        help="Skip literature search, create empty draft",
    )
    draft_parser.add_argument(
        "--output", "-o", metavar="FILE", help="Output file for manuscript"
    )
    draft_parser.add_argument(
        "--docx", action="store_true", help="Also create DOCX version of manuscript"
    )
    draft_parser.add_argument(
        "--check-quality",
        action="store_true",
        help="Run quality check after creating draft",
    )
    draft_parser.add_argument("--api-key", help="NCBI API key for literature search")

    # systematic-review command
    sr_parser = subparsers.add_parser(
        "systematic-review",
        help="Create systematic review manuscript with PRISMA guidelines",
    )
    sr_parser.add_argument("topic", help="Research topic for systematic review")
    sr_parser.add_argument(
        "--journal",
        choices=["blood_research", "blood", "blood-advances", "jco", "bjh"],
        default="blood_research",
        help="Target journal (default: blood_research)",
    )
    sr_parser.add_argument(
        "--max-articles",
        type=int,
        default=30,
        help="Maximum articles to include (default: 30)",
    )
    sr_parser.add_argument(
        "--time-period",
        choices=["all", "1y", "2y", "5y", "10y"],
        default="5y",
        help="Filter PubMed search by year (default: 5y)",
    )
    sr_parser.add_argument(
        "--output", "-o", metavar="DIR", help="Output directory for manuscripts"
    )
    sr_parser.add_argument(
        "--pico",
        nargs=4,
        metavar=("POPULATION", "INTERVENTION", "COMPARISON", "OUTCOME"),
        help="PICO elements: population intervention comparison outcome",
    )
    sr_parser.add_argument(
        "--no-notebook",
        action="store_true",
        help="Skip creating project notebook",
    )
    sr_parser.add_argument(
        "--notebook-path",
        help="Path to existing notebook (for Flow 2: use existing notebook with PDF/PPT/MP3 sources)",
    )
    sr_parser.add_argument(
        "--source-files",
        nargs="+",
        metavar="FILE",
        help="Local source files exported from NotebookLM (PDF/PPT/MP3) for manuscript content",
    )
    sr_parser.add_argument("--api-key", help="NCBI API key for literature search")

    # check-concordance command
    concordance_parser = subparsers.add_parser(
        "check-concordance", help="Check citation-reference concordance in manuscript"
    )
    concordance_parser.add_argument(
        "input", help="Path to manuscript file (DOCX, Markdown, or text)"
    )
    concordance_parser.add_argument(
        "--validate-format", action="store_true", help="Also validate reference format"
    )
    concordance_parser.add_argument(
        "--json", metavar="FILE", help="Save results as JSON to FILE"
    )

    # create-enhanced command (academic writing)
    enhanced_parser = subparsers.add_parser(
        "create-enhanced", help="Create manuscript with academic writing guidelines"
    )
    enhanced_parser.add_argument("topic", help="Research topic or title")
    enhanced_parser.add_argument(
        "--document-type",
        choices=[
            "research_paper",
            "literature_review",
            "systematic_review",
            "clinical_trial",
            "case_report",
        ],
        default="research_paper",
        help="Type of document",
    )
    enhanced_parser.add_argument(
        "--reference-style",
        choices=["vancouver", "ieee", "apa"],
        default="vancouver",
        help="Citation style",
    )
    enhanced_parser.add_argument("--keywords", help="Comma-separated keywords")
    enhanced_parser.add_argument(
        "-o, --output", dest="output", metavar="FILE", help="Output file path"
    )

    # research command (complete workflow)
    research_parser = subparsers.add_parser(
        "research",
        help="Complete workflow: search literature, create draft, quality check, verify",
    )
    research_parser.add_argument("topic", help="Research topic for manuscript")
    research_parser.add_argument(
        "--journal",
        choices=["blood_research", "blood", "blood-advances", "jco", "bjh"],
        default="blood_research",
        help="Target journal (default: blood_research)",
    )
    research_parser.add_argument(
        "--max-articles",
        type=int,
        default=50,
        help="Maximum articles to retrieve (default: 50)",
    )
    research_parser.add_argument(
        "--time-period",
        choices=["all", "1y", "2y", "5y", "10y"],
        default="all",
        help="Filter PubMed search by year: all, 1y, 2y, 5y, 10y",
    )
    research_parser.add_argument(
        "--no-repeat",
        action="store_true",
        help="Disable repeat search with multiple strategies",
    )
    research_parser.add_argument(
        "--no-web-search",
        dest="web_search",
        action="store_false",
        help="Skip web search",
    )
    research_parser.add_argument(
        "--output-dir", "-o", metavar="DIR", help="Output directory for files"
    )
    research_parser.add_argument(
        "--json", metavar="FILE", help="Save workflow report as JSON"
    )
    research_parser.add_argument("--api-key", help="NCBI API key for PubMed searches")

    # notebooklm command
    notebooklm_parser = subparsers.add_parser(
        "notebooklm", help="NotebookLM research intelligence queries"
    )
    notebooklm_subparsers = notebooklm_parser.add_subparsers(
        title="notebooklm commands",
        dest="notebooklm_command",
        required=True,
        help="NotebookLM query types",
    )

    # notebooklm status
    notebooklm_status_parser = notebooklm_subparsers.add_parser(
        "status", help="Check NotebookLM notebook status"
    )

    # notebooklm query-classification
    nb_classification_parser = notebooklm_subparsers.add_parser(
        "query-classification", help="Query WHO/ICC classification notebook"
    )
    nb_classification_parser.add_argument(
        "entity", help="Disease entity (e.g., 'AML with NPM1 mutation')"
    )
    nb_classification_parser.add_argument(
        "--type",
        choices=["comparison", "definition", "criteria"],
        default="comparison",
        help="Type of information to query",
    )

    # notebooklm query-gvhd
    nb_gvhd_parser = notebooklm_subparsers.add_parser(
        "query-gvhd", help="Query GVHD guidelines notebook"
    )
    nb_gvhd_parser.add_argument(
        "aspect", help="Aspect of GVHD to query (diagnosis, staging, scoring, response)"
    )
    nb_gvhd_parser.add_argument(
        "--organ", help="Specific organ system (skin, liver, GI, oral, etc.)"
    )

    # notebooklm query-eln
    nb_eln_parser = notebooklm_subparsers.add_parser(
        "query-eln", help="Query ELN therapeutic guidelines notebook"
    )
    nb_eln_parser.add_argument("disease", choices=["AML", "CML"], help="Disease type")
    nb_eln_parser.add_argument(
        "topic",
        help="Topic to query (e.g., 'first-line treatment', 'risk stratification')",
    )
    nb_eln_parser.add_argument(
        "--version", help="ELN version (2022 for AML, 2025 for CML)"
    )

    # notebooklm validate-nomenclature
    nb_nom_parser = notebooklm_subparsers.add_parser(
        "validate-nomenclature",
        help="Validate nomenclature against ISCN/HGVS standards",
    )
    nb_nom_parser.add_argument(
        "term", help="Term to validate (e.g., 'BCR-ABL', 't(9;22)')"
    )
    nb_nom_parser.add_argument(
        "--type",
        choices=["fusion", "cytogenetic", "mutation"],
        default="fusion",
        help="Type of nomenclature",
    )

    # notebooklm initialize
    nb_init_parser = notebooklm_subparsers.add_parser(
        "initialize", help="Initialize all NotebookLM notebooks with references"
    )
    nb_init_parser.add_argument(
        "--reference-path", help="Path to reference PDFs (default: LaCie drive)"
    )

    # project-notebook command
    project_parser = subparsers.add_parser(
        "project-notebook", help="Manage project notebooks for research topics"
    )
    project_subparsers = project_parser.add_subparsers(
        title="project commands", dest="project_command", required=True
    )

    # project-notebook create
    project_create = project_subparsers.add_parser(
        "create", help="Create a new project notebook for a research topic"
    )
    project_create.add_argument("topic", help="Research topic")
    project_create.add_argument("--id", help="Custom project ID (optional)")
    project_create.add_argument(
        "--journal",
        default="blood_research",
        help="Target journal (default: blood_research)",
    )

    # project-notebook list
    project_list = project_subparsers.add_parser(
        "list", help="List all project notebooks"
    )

    # project-notebook status
    project_status = project_subparsers.add_parser(
        "status", help="Show status of a project notebook"
    )
    project_status.add_argument("project_id", help="Project ID")

    # project-notebook add-sources
    project_add = project_subparsers.add_parser(
        "add-sources", help="Add new PubMed sources to a project notebook"
    )
    project_add.add_argument("project_id", help="Project ID")
    project_add.add_argument("query", help="PubMed search query")
    project_add.add_argument(
        "--max-articles",
        type=int,
        default=10,
        help="Maximum articles to fetch (default: 10)",
    )

    # project-notebook add-manuscript
    project_add_ms = project_subparsers.add_parser(
        "add-manuscript", help="Add manuscript version to project notebook"
    )
    project_add_ms.add_argument("project_id", help="Project ID")
    project_add_ms.add_argument("manuscript_path", help="Path to manuscript file")
    project_add_ms.add_argument("--notes", help="Notes about this version")

    # search-web command (Tavily)
    web_parser = subparsers.add_parser(
        "search-web",
        help="Search the web using Tavily for supplementary literature beyond PubMed",
    )
    web_parser.add_argument("query", help="Search query")
    web_parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)",
    )
    web_parser.add_argument(
        "--type",
        dest="search_type",
        choices=[
            "general",
            "trials",
            "guidelines",
            "preprints",
            "conferences",
            "news",
            "comprehensive",
        ],
        default="general",
        help="Type of search to perform",
    )
    web_parser.add_argument(
        "-o",
        "--output",
        help="Save results to JSON file",
    )
    web_parser.add_argument(
        "--require-permission",
        action="store_true",
        help="Enable reference permission workflow for non-PubMed sources",
    )

    return parser


def cmd_search_web(args):
    """Search the web using Tavily for supplementary literature."""
    from tools.draft_generator.tavily_searcher import TavilySearcher

    OutputFormatter.header("Web Search (Tavily)")

    print(f"Query: {args.query}")
    print(f"Max results: {args.max_results}")
    print(f"Search type: {args.search_type}")
    print()

    try:
        searcher = TavilySearcher()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set TAVILY_API_KEY environment variable.")
        return 1

    if args.search_type == "general":
        results = searcher.search(args.query, max_results=args.max_results)
    elif args.search_type == "trials":
        results = searcher.search_clinical_trials(args.query)
    elif args.search_type == "guidelines":
        results = searcher.search_guidelines(args.query)
    elif args.search_type == "preprints":
        results = searcher.search_preprints(args.query)
    elif args.search_type == "conferences":
        results = searcher.search_conferences(args.query)
    elif args.search_type == "news":
        results = searcher.search_news(args.query)
    elif args.search_type == "comprehensive":
        results_dict = searcher.comprehensive_search(args.query)
        print(f"Found results across {len(results_dict)} categories:\n")
        for category, items in results_dict.items():
            print(f"  {category}: {len(items)} results")
        results = results_dict.get("general", [])
    else:
        results = searcher.search(args.query, max_results=args.max_results)

    if not results:
        print("No results found.")
        return 0

    if args.require_permission:
        from tools.draft_generator.reference_permission_workflow import (
            ReferencePermissionWorkflow,
        )

        workflow = ReferencePermissionWorkflow()
        state = workflow.create_permission_review(args.query, results)

        if not state.requests:
            print("All results are PubMed-indexed. No permission needed.")
        else:
            print("\n" + "=" * 60)
            print(workflow.format_permission_prompt(state))
            print("=" * 60)

            user_input = input(
                "\nEnter your decision (e.g., '1,3,5' or 'all' or 'none'): "
            )
            state = workflow.process_user_decision(state, user_input)

            saved_path = workflow.save_state(state)
            print(f"\nPermission decision saved to: {saved_path}")
            print(f"  - Permitted: {len(state.permitted_indices)}")
            print(f"  - Rejected: {len(state.rejected_indices)}")

            permitted_results = [results[i] for i in state.permitted_indices]
            results = permitted_results

            if not results:
                print("\nNo references were permitted. Exiting.")
                return 0

            print(f"\nProceeding with {len(results)} permitted references.")

    print(f"Found {len(results)} results:\n")

    for i, r in enumerate(results, 1):
        print(f"{i}. {r.title}")
        print(f"   URL: {r.url}")
        if r.published_date:
            print(f"   Date: {r.published_date}")
        print(f"   {r.content[:150]}...")
        print()

    if args.output:
        import json

        data = {
            "query": args.query,
            "search_type": args.search_type,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content,
                    "published_date": r.published_date,
                    "source": r.source,
                }
                for r in results
            ],
        }
        with open(args.output, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Results saved to: {args.output}")

    return 0


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Route to appropriate command
    commands = {
        "check-quality": cmd_check_quality,
        "verify-references": cmd_verify_references,
        "edit-manuscript": cmd_edit_manuscript,
        "generate-report": cmd_generate_report,
        "search-pubmed": cmd_search_pubmed,
        "search-web": cmd_search_web,
        "create-draft": cmd_create_draft,
        "systematic-review": cmd_systematic_review,
        "create-enhanced": cmd_create_enhanced,
        "research": cmd_research,
        "convert": cmd_convert,
        "check-concordance": cmd_check_concordance,
        "notebooklm": cmd_notebooklm,
        "project-notebook": cmd_project_notebook,
    }

    command_func = commands.get(args.command)
    if command_func:
        try:
            return command_func(args)
        except FileNotFoundError as e:
            print(f"{OutputFormatter.error(str(e))}")
            return 1
        except Exception as e:
            print(f"{OutputFormatter.error(f'Unexpected error: {e}')}")
            if getattr(args, "debug", False):
                import traceback

                traceback.print_exc()
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
