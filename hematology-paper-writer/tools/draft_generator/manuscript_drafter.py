"""
Manuscript Drafter Module
Generates manuscript drafts following hematology journal guidelines.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime


class Journal(Enum):
    """Supported hematology journals."""
    BLOOD_RESEARCH = "blood_research"
    BLOOD = "blood"
    BLOOD_ADVANCES = "blood_advances"
    JCO = "jco"
    BJH = "bjh"
    LEUKEMIA = "leukemia"
    HAEMATOLOGICA = "haematologica"


@dataclass
class JournalSpecs:
    """Journal specifications for manuscript formatting."""
    name: str
    word_limit_abstract: int = 250
    word_limit_text: int = 5000
    max_references: int = 50
    reference_style: str = "vancouver"  # vancouver, numbered, author-year
    sections_required: List[str] = field(default_factory=lambda: [
        "Abstract", "Introduction", "Methods", "Results", "Discussion"
    ])
    figure_limit: int = 6
    table_limit: int = 6
    font: str = "Times New Roman"
    font_size: int = 12
    line_spacing: float = 2.0
    margins: str = "2.5 cm"
    doi_prefix: str = "10.1182"
    url: str = ""


# Journal specifications
JOURNAL_GUIDELINES: Dict[Journal, JournalSpecs] = {
    Journal.BLOOD_RESEARCH: JournalSpecs(
        name="Blood Research",
        word_limit_abstract=200,  # Blood Research: 200 words
        word_limit_text=5000,
        max_references=50,
        reference_style="vancouver",
        sections_required=["Abstract", "Introduction", "Methods", "Results", "Discussion", "Authors' Contributions", "Conflict of Interest", "Acknowledgments", "References"],
        figure_limit=6,
        table_limit=6,
        url="https://link.springer.com/journal/44313/submission-guidelines"
    ),
    Journal.BLOOD: JournalSpecs(
        name="Blood",
        word_limit_abstract=250,  # Blood (ASH): 250 words for reviews
        word_limit_text=5000,
        max_references=50,
        reference_style="vancouver",
        sections_required=["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        figure_limit=6,
        table_limit=6,
        doi_prefix="10.1182",
        url="https://ashpublications.org/blood"
    ),
    Journal.BLOOD_ADVANCES: JournalSpecs(
        name="Blood Advances",
        word_limit_abstract=250,
        word_limit_text=6000,
        max_references=60,
        reference_style="vancouver",
        sections_required=["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        figure_limit=8,
        table_limit=8,
        doi_prefix="10.1182",
        url="https://ashpublications.org/bloodadvances"
    ),
    Journal.JCO: JournalSpecs(
        name="Journal of Clinical Oncology",
        word_limit_abstract=250,
        word_limit_text=4000,
        max_references=50,
        reference_style="numbered",
        sections_required=["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        figure_limit=6,
        table_limit=6,
        doi_prefix="10.1200/JCO",
        url="https://ascopubs.org/journal/jco"
    ),
    Journal.BJH: JournalSpecs(
        name="British Journal of Haematology",
        word_limit_abstract=200,
        word_limit_text=5000,
        max_references=40,
        reference_style="vancouver",
        sections_required=["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        figure_limit=6,
        table_limit=6,
        doi_prefix="10.1111/bjh",
        url="https://onlinelibrary.wiley.com/journal/14700505"
    ),
    Journal.LEUKEMIA: JournalSpecs(
        name="Leukemia",
        word_limit_abstract=200,
        word_limit_text=5000,
        max_references=50,
        reference_style="vancouver",
        sections_required=["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        figure_limit=6,
        table_limit=6,
        doi_prefix="10.1038/s41375",
        url="https://www.nature.com/leu"
    ),
    Journal.HAEMATOLOGICA: JournalSpecs(
        name="Haematologica",
        word_limit_abstract=250,
        word_limit_text=5000,
        max_references=50,
        reference_style="vancouver",
        sections_required=["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        figure_limit=6,
        table_limit=6,
        doi_prefix="10.3324/haematol",
        url="https://www.haematologica.org"
    )
}


@dataclass
class ArticleData:
    """Data for generating an article."""
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    introduction: str = ""
    methods: str = ""
    results: str = ""
    discussion: str = ""
    references: List[str] = field(default_factory=list)
    figures: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    doi: str = ""
    correspondence: str = ""


class ManuscriptDrafter:
    """Generates manuscript drafts for hematology journals."""
    
    def __init__(self, journal: Journal = Journal.BLOOD_RESEARCH):
        """
        Initialize the manuscript drafter.
        
        Args:
            journal: Target journal
        """
        self.journal = journal
        self.specs = JOURNAL_GUIDELINES.get(journal, JOURNAL_GUIDELINES[Journal.BLOOD_RESEARCH])
    
    def create_draft(
        self,
        topic: str,
        articles: List[Any],
        study_type: str = "observational",
        custom_sections: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a manuscript draft based on research data.
        
        Args:
            topic: Research topic/title
            articles: List of PubMedArticle objects for context
            study_type: Type of study (observational, clinical_trial, review, etc.)
            custom_sections: Custom section content
            
        Returns:
            Markdown manuscript draft
        """
        data = ArticleData(title=topic)
        
        # Extract common themes from articles
        common_themes = self._extract_common_themes(articles)
        key_findings = self._summarize_findings(articles)
        
        # Generate sections
        data.abstract = self._generate_abstract(topic, study_type)
        data.introduction = self._generate_introduction(topic, common_themes, articles)
        data.methods = self._generate_methods(study_type)
        data.results = self._generate_results(topic, study_type, articles)
        data.discussion = self._generate_discussion(topic, common_themes, key_findings)
        
        # Generate references
        data.references = self._generate_references(articles)
        
        # Format manuscript
        return self._format_manuscript(data)
    
    def _extract_common_themes(self, articles: List[Any]) -> List[str]:
        """Extract common themes from articles."""
        themes = set()
        for art in articles[:10]:  # Use top 10
            for term in art.mesh_terms[:5]:
                if len(term) > 3:
                    themes.add(term.lower())
        return list(themes)[:15]
    
    def _summarize_findings(self, articles: List[Any]) -> Dict[str, str]:
        """Summarize key findings from articles."""
        return {
            "main_topic": "treatment outcomes",
            "key_results": "significant improvement observed",
            "limitations": "small sample size, short follow-up"
        }
    
    def _generate_abstract(self, topic: str, study_type: str) -> str:
        """Generate structured abstract."""
        word_limit = self.specs.word_limit_abstract
        
        # Generate structured abstract based on study type
        if study_type == "clinical_trial":
            return f"""**Background:** 
**Methods:** 
**Results:** 
**Conclusion:** """
        elif study_type == "observational":
            return f"""**Background:** This study investigates {topic.lower()}.
**Methods:** A retrospective/prospective analysis was conducted.
**Results:** Key findings demonstrate significant associations.
**Conclusion:** These results suggest important clinical implications."""
        else:
            return f"""**Abstract**
This manuscript examines {topic.lower()}. Through comprehensive analysis, we identified key findings that contribute to understanding in this field. The study provides evidence supporting clinical applications."""
    
    def _generate_introduction(self, topic: str, themes: List[str], articles: List[Any]) -> str:
        """Generate introduction section."""
        intro_parts = [
            f"## Introduction",
            "",
            f"{topic} represents an important area of investigation in hematology.",
            "",
            "### Background",
            "",
            "The pathogenesis and treatment of hematological malignancies have evolved significantly in recent years.",
            "",
            "### Rationale",
            ""
        ]
        
        # Add context from literature
        if articles:
            intro_parts.append(f"This study builds upon recent advances including:")
            for art in articles[:3]:
                intro_parts.append(f"- {art.title} ({art.year})")
        
        intro_parts.extend([
            "",
            "### Objectives",
            "",
            f"This study aims to investigate {topic.lower()} and provide insights into its clinical relevance."
        ])
        
        return "\n".join(intro_parts)
    
    def _generate_methods(self, study_type: str) -> str:
        """Generate methods section."""
        methods_parts = [
            "## Methods",
            "",
            "### Study Design",
            "",
            f"This was a {study_type} study conducted to investigate the research objectives.",
            "",
            "### Patients",
            "",
            "Patients were enrolled according to predefined inclusion and exclusion criteria:",
            "- Inclusion criteria will be specified",
            "- Exclusion criteria will be specified",
            "",
            "### Data Collection",
            "",
            "Data were collected from medical records following institutional protocols.",
            "",
            "### Statistical Analysis",
            "",
            "Statistical analysis was performed using appropriate software.",
            "Continuous variables were compared using parametric/non-parametric tests.",
            "Categorical variables were analyzed using chi-square or Fisher's exact test.",
            "Survival analysis was conducted using Kaplan-Meier method.",
            f"P-value < 0.05 was considered statistically significant."
        ]
        
        return "\n".join(methods_parts)
    
    def _generate_results(self, topic: str, study_type: str, articles: List[Any]) -> str:
        """Generate results section."""
        results_parts = [
            "## Results",
            "",
            "### Patient Characteristics",
            "",
            f"A total of [N] patients were included in this analysis of {topic.lower()}.",
            "",
            "### Clinical Outcomes",
            "",
            "The primary endpoints were assessed as follows:",
            "- Primary endpoint 1: [result]",
            "- Primary endpoint 2: [result]",
            "",
            "### Survival Analysis",
            "",
            "Overall survival and progression-free survival were evaluated.",
            "",
            "### Subgroup Analysis",
            "",
            "Predefined subgroup analyses were conducted."
        ]
        
        return "\n".join(results_parts)
    
    def _generate_discussion(self, topic: str, themes: List[str], findings: Dict[str, str]) -> str:
        """Generate discussion section."""
        discussion_parts = [
            "## Discussion",
            "",
            "### Principal Findings",
            "",
            f"This study provides insights into {topic.lower()}.",
            "The results demonstrate [key findings].",
            "",
            "### Comparison with Existing Literature",
            "",
            "Our findings are consistent with/extend previous observations.",
            "",
            "### Clinical Implications",
            "",
            "These results have important implications for clinical practice.",
            "",
            "### Strengths and Limitations",
            "",
            "This study has several strengths including [strengths].",
            "However, limitations should be acknowledged:",
            "- Retrospective design",
            "- Single-center experience",
            "- Potential selection bias",
            "",
            "### Future Directions",
            "",
            "Larger prospective studies are needed to validate these findings.",
            ""
        ]
        
        return "\n".join(discussion_parts)
    
    def _generate_references(self, articles: List[Any]) -> List[str]:
        """Generate reference list from articles."""
        refs = []
        for i, art in enumerate(articles[:30], 1):
            # Vancouver format
            authors = ", ".join(art.authors[:5])
            if len(art.authors) > 5:
                authors += ", et al."
            ref = f"[{i}] {authors}. {art.title}. {art.journal}. {art.year}"
            if art.volume:
                ref += f";{art.volume}"
                if art.issue:
                    ref += f"({art.issue})"
            if art.pages:
                ref += f":{art.pages}"
            if art.doi:
                ref += f". doi:{art.doi}"
            refs.append(ref)
        return refs
    
    def _format_manuscript(self, data: ArticleData) -> str:
        """Format the complete manuscript."""
        lines = [
            f"# {data.title}",
            "",
            "## Authors",
            ", ".join(data.authors) if data.authors else "[Author names will be added]",
            "",
            data.abstract,
            "",
            "**Keywords:** " + ", ".join(data.keywords) if data.keywords else "Keywords: [To be added]",
            "",
            data.introduction,
            "",
            data.methods,
            "",
            data.results,
            "",
            data.discussion,
            "",
            "## Authors' Contributions",
            "[To be specified]",
            "",
            "## Conflict of Interest",
            "The authors declare no conflicts of interest.",
            "",
            "## Acknowledgments",
            "[To be added]",
            "",
            "## References",
            ""
        ]
        
        # Add references
        for ref in data.references:
            lines.append(ref)
        
        # Add figures and tables placeholders
        if data.figures:
            lines.extend(["", "## Figures", ""])
            for fig in data.figures:
                lines.append(f"- {fig}")
        
        if data.tables:
            lines.extend(["", "## Tables", ""])
            for table in data.tables:
                lines.append(f"- {table}")
        
        return "\n".join(lines)
    
    def get_journal_specs(self) -> JournalSpecs:
        """Get the journal specifications."""
        return self.specs


def create_manuscript(
    topic: str,
    articles: List[Any],
    journal: str = "blood_research",
    study_type: str = "observational"
) -> str:
    """
    Convenience function to create a manuscript draft.
    
    Args:
        topic: Research topic
        articles: PubMed articles for context
        journal: Target journal name
        study_type: Type of study
        
    Returns:
        Markdown manuscript draft
    """
    journal_map = {
        "blood_research": Journal.BLOOD_RESEARCH,
        "blood": Journal.BLOOD,
        "blood_advances": Journal.BLOOD_ADVANCES,
        "jco": Journal.JCO,
        "bjh": Journal.BJH,
        "leukemia": Journal.LEUKEMIA,
        "haematologica": Journal.HAEMATOLOGICA
    }
    
    j = journal_map.get(journal.lower(), Journal.BLOOD_RESEARCH)
    drafter = ManuscriptDrafter(j)
    return drafter.create_draft(topic, articles, study_type)


if __name__ == "__main__":
    # Test
    from pubmed_searcher import PubMedSearcher
    
    print("Testing manuscript drafter...")
    print(f"Journal: {Journal.BLOOD_RESEARCH.value}")
    print(f"Specs: {JOURNAL_GUIDELINES[Journal.BLOOD_RESEARCH]}")


def generate_specific_section(section_name: str, topic: str, study_type: str = "observational") -> str:
    """
    Generate a specific manuscript section using EnhancedManuscriptDrafter.
    """
    from tools.draft_generator.enhanced_drafter import EnhancedManuscriptDrafter, DocumentType
    
    # Map study type to DocumentType
    doc_type_map = {
        "observational": DocumentType.RESEARCH_PAPER,
        "clinical_trial": DocumentType.CLINICAL_TRIAL,
        "review": DocumentType.SYSTEMATIC_REVIEW,
        "case_report": DocumentType.CASE_REPORT
    }
    
    doc_type = doc_type_map.get(study_type, DocumentType.RESEARCH_PAPER)
    drafter = EnhancedManuscriptDrafter(document_type=doc_type)
    
    # Generate content using the protected method (we are wrapping it here)
    content = drafter._generate_section_content(section_name, topic)
    return content
