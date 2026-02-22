"""
Draft Generator Module
=====================

Tools for generating manuscript drafts from research topics.

Available Classes:
- PubMedSearcher: Search PubMed for relevant articles
- ManuscriptDrafter: Generate manuscript drafts
- EnhancedManuscriptDrafter: Enhanced drafting with academic guidelines
- SystematicReviewDrafter: PRISMA-compliant systematic reviews
- ClinicalTrialDrafter: CONSORT-compliant clinical trial reports
- CaseReportDrafter: CARE-compliant case reports
- MetaAnalysisDrafter: Meta-analysis support
- ResearchWorkflow: Complete research workflow orchestration
- Journal: Supported journals enum

Functions:
- run_research_workflow: Execute complete research workflow
- create_manuscript: Create manuscript draft from topic
- create_enhanced_manuscript: Create enhanced manuscript with academic guidelines
- create_systematic_review: Create PRISMA-compliant systematic review
- create_clinical_trial_report: Create CONSORT-compliant clinical trial report
- create_case_report: Create CARE-compliant case report
"""

from .pubmed_searcher import PubMedSearcher, PubMedArticle, search_pubmed
from .manuscript_drafter import (
    ManuscriptDrafter,
    Journal,
    JournalSpecs,
    ArticleData,
    create_manuscript,
    JOURNAL_GUIDELINES,
)
from .enhanced_drafter import (
    EnhancedManuscriptDrafter,
    ManuscriptStructure,
    DocumentType,
    ReferenceStyle,
    SectionContent,
    TableData,
    FigureData,
    AcademicSource,
    PrismaFlowData,
    QualityChecklist,
    WritingGuidelines,
    ManuscriptTemplates,
    create_systematic_review,
    create_enhanced_manuscript,
    check_citation_concordance,
    integrate_citation,
    extract_citations,
    SystematicReviewDrafter,
    ClinicalTrialDrafter,
    CaseReportDrafter,
    MetaAnalysisDrafter,
)
from .research_workflow import ResearchWorkflow, run_research_workflow
from .enhanced_methods_drafter import (
    EnhancedManuscriptDrafter as HematologyMethodsDrafter,
    ClassificationSystem,
    GVHDCriteria,
    ManuscriptType,
    MethodsTemplate,
)

__all__ = [
    # PubMed Searcher
    "PubMedSearcher",
    "PubMedArticle",
    "search_pubmed",
    # Manuscript Drafter
    "ManuscriptDrafter",
    "Journal",
    "JournalSpecs",
    "ArticleData",
    "create_manuscript",
    "JOURNAL_GUIDELINES",
    # Enhanced Drafter
    "EnhancedManuscriptDrafter",
    "ManuscriptStructure",
    "DocumentType",
    "ReferenceStyle",
    "SectionContent",
    "TableData",
    "FigureData",
    "AcademicSource",
    "PrismaFlowData",
    "QualityChecklist",
    "WritingGuidelines",
    "ManuscriptTemplates",
    "create_systematic_review",
    "create_enhanced_manuscript",
    "check_citation_concordance",
    "integrate_citation",
    "extract_citations",
    # Specialized Drafters
    "SystematicReviewDrafter",
    "ClinicalTrialDrafter",
    "CaseReportDrafter",
    "MetaAnalysisDrafter",
    # Research Workflow
    "ResearchWorkflow",
    "run_research_workflow",
    "HematologyMethodsDrafter",
    "ClassificationSystem",
    "GVHDCriteria",
    "ManuscriptType",
    "MethodsTemplate",
]
