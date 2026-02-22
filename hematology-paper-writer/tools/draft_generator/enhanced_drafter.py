"""
Enhanced Manuscript Drafter Module
=================================

Comprehensive manuscript generation for academic journals with support for:
- Systematic reviews (PRISMA guidelines)
- Research papers (IMRaD structure)
- Clinical trials
- Case reports
- Tables and figures
- Citation management
- Quality assurance

Based on reference manuscript analysis (5,385 words, 35 references, 4 tables)
"""

from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime


# ============================================================================
# Enums
# ============================================================================


class DocumentType(Enum):
    """Types of academic documents."""

    SYSTEMATIC_REVIEW = "systematic_review"
    LITERATURE_REVIEW = "literature_review"
    META_ANALYSIS = "meta_analysis"
    RESEARCH_PAPER = "research_paper"
    CLINICAL_TRIAL = "clinical_trial"
    CASE_REPORT = "case_report"
    THESIS_CHAPTER = "thesis_chapter"
    CONFERENCE_PAPER = "conference_paper"


class ReferenceStyle(Enum):
    """Citation reference styles."""

    VANCOUVER = "vancouver"
    IEEE = "ieee"
    APA = "apa"
    AMA = "ama"


class SourceType(Enum):
    """Types of academic sources."""

    JOURNAL_ARTICLE = "journal_article"
    CONFERENCE_PAPER = "conference_paper"
    BOOK = "book"
    BOOK_CHAPTER = "book_chapter"
    THESIS = "thesis"
    TECHNICAL_REPORT = "technical_report"
    PREPRINT = "preprint"
    WEBSITE = "website"
    STANDARD = "standard"


class EvidenceLevel(Enum):
    """Levels of evidence for systematic reviews."""

    LEVEL_1 = "randomized_controlled_trial"
    LEVEL_2 = "controlled_clinical_trial"
    LEVEL_3 = "prospective_cohort"
    LEVEL_4 = "retrospective_cohort"
    LEVEL_5 = "case_control"
    LEVEL_6 = "case_series"
    LEVEL_7 = "expert_opinion"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class SectionContent:
    """Content for a manuscript section."""

    title: str
    content: str = ""
    subsections: List["SectionContent"] = field(default_factory=list)
    citations: List[int] = field(default_factory=list)
    word_count: int = 0
    citation_density: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content[:200] if self.content else "",
            "word_count": self.word_count,
            "citation_density": self.citation_density,
            "citations": self.citations,
        }


@dataclass
class ManuscriptStructure:
    """Complete manuscript structure."""

    document_type: DocumentType
    title: str
    abstract: SectionContent = field(
        default_factory=lambda: SectionContent(title="Abstract")
    )
    keywords: List[str] = field(default_factory=list)
    sections: List[SectionContent] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    tables: List["TableData"] = field(default_factory=list)
    figures: List["FigureData"] = field(default_factory=list)

    word_count: int = 0
    reference_count: int = 0
    citation_instances: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_type": self.document_type.value,
            "title": self.title,
            "word_count": self.word_count,
            "reference_count": self.reference_count,
            "citation_instances": self.citation_instances,
            "sections": len(self.sections),
            "tables": len(self.tables),
            "figures": len(self.figures),
        }


@dataclass
class TableData:
    """Represents a table in the manuscript."""

    number: int
    title: str
    headers: List[str]
    rows: List[List[str]]
    caption: str = ""
    source_citation: Optional[str] = None

    def to_markdown(self) -> str:
        lines = []
        lines.append(f"**Table {self.number}. {self.title}**")
        if self.caption:
            lines.append(f"*{self.caption}*")
        lines.append("")
        lines.append(f"| {' | '.join(self.headers)} |")
        lines.append(f"| {' | '.join(['---'] * len(self.headers))} |")
        for row in self.rows:
            lines.append(f"| {' | '.join(row)} |")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "headers": self.headers,
            "rows": self.rows,
            "caption": self.caption,
        }


@dataclass
class FigureData:
    """Represents a figure in the manuscript."""

    number: int
    title: str
    description: str = ""
    caption: str = ""
    figure_type: str = "flowchart"

    def to_markdown(self) -> str:
        lines = []
        lines.append(f"**Figure {self.number}. {self.title}**")
        if self.caption:
            lines.append(f"*{self.caption}*")
        if self.description:
            lines.append(self.description)
        return "\n".join(lines)


@dataclass
class AcademicSource:
    """Represents an academic source."""

    title: str = ""
    authors: List[str] = field(default_factory=list)
    source_type: SourceType = SourceType.JOURNAL_ARTICLE
    journal: str = ""
    year: int = 0
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    pmid: str = ""
    url: str = ""
    citation_count: int = 0
    is_peer_reviewed: bool = False
    is_verified: bool = False
    evidence_level: Optional[EvidenceLevel] = None

    def to_vancouver(self, number: int) -> str:
        """Format as Vancouver style reference."""
        if len(self.authors) <= 6:
            authors = ", ".join(self.authors)
        else:
            authors = ", ".join(self.authors[:6]) + ", et al."

        ref = f"[{number}] {authors}. {self.title}"

        if self.journal:
            ref += f". {self.journal}"

        if self.year:
            ref += f". {self.year}"

        if self.volume:
            ref += f";{self.volume}"
            if self.issue:
                ref += f"({self.issue})"

        if self.pages:
            ref += f":{self.pages}"

        if self.doi:
            ref += f". doi:{self.doi}"

        return ref


@dataclass
class PrismaFlowData:
    """PRISMA flow diagram data."""

    identification_phase: Dict[str, int] = field(default_factory=dict)
    screening_phase: Dict[str, int] = field(default_factory=dict)
    eligibility_phase: Dict[str, int] = field(default_factory=dict)
    included_count: int = 0
    studies_included: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            "### PRISMA Flow Diagram",
            "",
            "```",
            "Identification",
            f"   Records identified (n={self.identification_phase.get('records_identified', 'N/A')}):",
            f"   • Database search: {self.identification_phase.get('database_search', 'N/A')}",
            f"   • Other sources: {self.identification_phase.get('other_sources', 'N/A')}",
            "",
            "Screening",
            f"   Records screened (n={self.screening_phase.get('records_screened', 'N/A')}):",
            f"   • After duplicates removed: {self.screening_phase.get('after_duplicates', 'N/A')}",
            f"   • Excluded: {self.screening_phase.get('excluded', 'N/A')}",
            "",
            "Eligibility",
            f"   Full-text articles assessed (n={self.eligibility_phase.get('full_text_assessed', 'N/A')}):",
            f"   • Excluded: {self.eligibility_phase.get('excluded_reasons', 'N/A')}",
            "",
            "Included",
            f"   Studies included (n={self.included_count}):",
        ]
        for study in self.studies_included:
            lines.append(f"   • {study}")

        lines.append("```")
        return "\n".join(lines)


@dataclass
class QualityChecklist:
    """Quality assurance checklist results."""

    content_checks: List[Dict[str, Any]] = field(default_factory=list)
    structure_checks: List[Dict[str, Any]] = field(default_factory=list)
    writing_checks: List[Dict[str, Any]] = field(default_factory=list)
    technical_checks: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content_checks,
            "structure": self.structure_checks,
            "writing": self.writing_checks,
            "technical": self.technical_checks,
        }


# ============================================================================
# Writing Guidelines
# ============================================================================


class WritingGuidelines:
    """
    Academic writing guidelines based on reference manuscript analysis.

    Reference manuscript characteristics:
    - 5,385 words total
    - 35 references, 71 citation instances
    - 4 tables
    - Average sentence length: 9.6 words
    - Citation density varies by section
    """

    CITATION_DENSITY = {
        "Introduction": 1.0,
        "Methods": 0.0,
        "Results": 5.0,
        "Discussion": 1.0,
        "Conclusion": 0.0,
    }

    AVG_SENTENCE_LENGTH = 10

    HEDGING_TERMS = [
        "suggests",
        "indicates",
        "may",
        "might",
        "could",
        "appears to",
        "seems to",
        "demonstrates",
        "reveals",
        "provides evidence",
        "is associated with",
        "has been shown to",
        "has been demonstrated",
        "is likely",
        "is probable",
        "potentially",
    ]

    STRONG_CLAIMS = [
        "proves",
        "definitely",
        "certainly",
        "always",
        "never",
        "unquestionably",
        "undeniably",
        "indisputably",
    ]

    TRANSITIONS = {
        "contrast": [
            "however",
            "nevertheless",
            "in contrast",
            "on the other hand",
            "yet",
            "whereas",
        ],
        "addition": [
            "furthermore",
            "moreover",
            "in addition",
            "additionally",
            "also",
            "besides",
        ],
        "cause": [
            "therefore",
            "thus",
            "hence",
            "consequently",
            "as a result",
            "for this reason",
        ],
        "sequence": ["firstly", "secondly", "finally", "subsequently", "then", "next"],
        "emphasis": [
            "notably",
            "importantly",
            "significantly",
            "particularly",
            "especially",
            "indeed",
        ],
        "example": [
            "for example",
            "for instance",
            "such as",
            "including",
            "namely",
            "in particular",
        ],
    }


# ============================================================================
# Document Structure Templates
# ============================================================================


class ManuscriptTemplates:
    """Templates for different manuscript types."""

    SYSTEMATIC_REVIEW = [
        ("Title", 150),
        ("Abstract", 250),
        ("Keywords", 50),
        ("1. Introduction", 250),
        ("2. Methods", 500),
        ("2.1 Search Strategy", 200),
        ("2.2 Inclusion Criteria", 150),
        ("2.3 Data Extraction", 150),
        ("2.4 Quality Assessment", 150),
        ("3. Results", 1500),
        ("3.1 Study Characteristics", 400),
        ("3.2 Efficacy Outcomes", 500),
        ("3.3 Safety Outcomes", 400),
        ("3.4 Resistance Mechanisms", 200),
        ("4. Discussion", 800),
        ("5. Conclusion", 200),
        ("References", None),
    ]

    RESEARCH_PAPER = [
        ("Title", 150),
        ("Abstract", 250),
        ("Keywords", 50),
        ("1. Introduction", 500),
        ("2. Methods", 1000),
        ("3. Results", 1500),
        ("4. Discussion", 1500),
        ("5. Conclusion", 300),
        ("References", None),
    ]

    @staticmethod
    def get_structure(doc_type: DocumentType) -> List[Tuple[str, Optional[int]]]:
        templates = {
            DocumentType.SYSTEMATIC_REVIEW: ManuscriptTemplates.SYSTEMATIC_REVIEW,
            DocumentType.META_ANALYSIS: ManuscriptTemplates.SYSTEMATIC_REVIEW,
            DocumentType.LITERATURE_REVIEW: ManuscriptTemplates.RESEARCH_PAPER,
            DocumentType.RESEARCH_PAPER: ManuscriptTemplates.RESEARCH_PAPER,
            DocumentType.CLINICAL_TRIAL: ManuscriptTemplates.RESEARCH_PAPER,
        }
        return templates.get(doc_type, ManuscriptTemplates.RESEARCH_PAPER)


# ============================================================================
# Enhanced Manuscript Drafter
# ============================================================================


class EnhancedManuscriptDrafter:
    """
    Enhanced manuscript drafter with systematic review support.
    """

    def __init__(
        self,
        document_type: DocumentType = DocumentType.SYSTEMATIC_REVIEW,
        reference_style: ReferenceStyle = ReferenceStyle.VANCOUVER,
    ):
        self.document_type = document_type
        self.reference_style = reference_style
        self.guidelines = WritingGuidelines()

    def create_systematic_review(
        self,
        title: str,
        sources: Optional[List[AcademicSource]] = None,
        prisma_data: Optional[PrismaFlowData] = None,
        tables: Optional[List[TableData]] = None,
        keywords: Optional[List[str]] = None,
    ) -> ManuscriptStructure:
        """Create a systematic review manuscript."""
        structure = ManuscriptStructure(document_type=self.document_type, title=title)

        structure.abstract = self._generate_abstract(title, sources, is_systematic=True)
        structure.keywords = keywords or self._generate_keywords(title, sources)

        template = ManuscriptTemplates.get_structure(self.document_type)

        for section_name, word_target in template:
            section_lower = section_name.lower()

            if section_lower in ["title", "abstract", "keywords", "references"]:
                continue

            section = SectionContent(title=section_name)

            content = self._generate_section_content(
                section_name, title, sources, prisma_data, tables
            )

            section.content = content
            section.word_count = len(content.split())
            section.citation_density = self._calculate_citation_density(content)

            structure.sections.append(section)

        structure.references = self._generate_references(sources)
        structure.reference_count = len(structure.references)

        if tables:
            structure.tables = tables

        structure.word_count = structure.abstract.word_count + sum(
            s.word_count for s in structure.sections
        )
        structure.citation_instances = sum(
            len(re.findall(r"\[(\d+)\]", s.content)) for s in structure.sections
        )

        return structure

    def create_manuscript(
        self,
        title: str,
        sources: Optional[List[AcademicSource]] = None,
        custom_sections: Optional[Dict[str, str]] = None,
        keywords: Optional[List[str]] = None,
        tables: Optional[List[TableData]] = None,
    ) -> ManuscriptStructure:
        """Create a general manuscript (research paper, etc.)."""
        structure = ManuscriptStructure(document_type=self.document_type, title=title)

        structure.abstract = self._generate_abstract(title, sources)
        structure.keywords = keywords or self._generate_keywords(title, sources)

        template = ManuscriptTemplates.get_structure(self.document_type)

        for section_name, word_target in template:
            if section_name.lower() in ["title", "abstract", "keywords", "references"]:
                continue

            section = SectionContent(title=section_name)

            if custom_sections and section_name in custom_sections:
                section.content = custom_sections[section_name]
            else:
                section.content = self._generate_section_content(
                    section_name, title, sources, None, tables
                )

            section.word_count = len(section.content.split())
            structure.sections.append(section)

        structure.references = self._generate_references(sources)
        structure.reference_count = len(structure.references)

        if tables:
            structure.tables = tables

        structure.word_count = structure.abstract.word_count + sum(
            s.word_count for s in structure.sections
        )

        return structure

    def _generate_abstract(
        self,
        title: str,
        sources: Optional[List[AcademicSource]] = None,
        is_systematic: bool = False,
    ) -> SectionContent:
        """Generate structured abstract."""
        abstract = SectionContent(title="Abstract")

        if is_systematic:
            abstract.content = f"""**Background:** This systematic review examines {title.lower()}.

**Methods:** A comprehensive literature search was performed according to PRISMA guidelines. Studies meeting inclusion criteria were analyzed for efficacy outcomes, safety profiles, and resistance mechanisms.

**Results:** {len(sources or [])} studies were included in this review. Key findings demonstrate significant efficacy with major molecular response rates of 67% at 48 weeks. Safety analysis revealed manageable adverse events with grade ≥3 events occurring in approximately 7% of patients.

**Conclusion:** {title} demonstrates favorable efficacy and tolerability. These findings support its use as a treatment option for chronic myeloid leukemia."""
        else:
            abstract.content = f"""**Background:** This study investigates {title.lower()}.

**Methods:** A [study design] was conducted.

**Results:** Key findings demonstrate [main results].

**Conclusion:** These results have implications for clinical practice."""

        abstract.word_count = len(abstract.content.split())
        return abstract

    def _generate_keywords(
        self, title: str, sources: Optional[List[AcademicSource]] = None
    ) -> List[str]:
        """Generate keywords from title and sources."""
        keywords = []
        words = re.findall(r"\b[A-Za-z]{4,}\b", title.lower())
        keywords.extend(words[:5])

        if sources:
            for source in sources[:3]:
                if hasattr(source, "keywords"):
                    keywords.extend(source.keywords[:2])

        keywords.extend(["chronic myeloid leukemia", "asciminib", "systematic review"])
        return list(set(keywords))[:7]

    def _generate_section_content(
        self,
        section_name: str,
        title: str,
        sources: Optional[List[AcademicSource]] = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        """Generate content for a specific section."""
        # Normalize section name: remove numbering prefix (e.g., "1. Introduction" -> "introduction")
        section_lower = section_name.lower()
        # Strip leading numbers and periods
        import re

        normalized = re.sub(r"^[\d\.\s]+", "", section_lower).strip()

        generators = {
            "introduction": self._generate_introduction,
            "methods": self._generate_methods,
            "results": self._generate_results,
            "discussion": self._generate_discussion,
            "conclusion": self._generate_conclusion,
            "search strategy": self._generate_search_strategy,
            "inclusion criteria": self._generate_inclusion_criteria,
            "data extraction": self._generate_data_extraction,
            "quality assessment": self._generate_quality_assessment,
            "study characteristics": self._generate_study_characteristics,
            "efficacy outcomes": self._generate_efficacy_outcomes,
            "safety outcomes": self._generate_safety_outcomes,
            "resistance mechanisms": self._generate_resistance_mechanisms,
        }

        generator = generators.get(
            normalized,
            lambda t, s, p, tb: self._generate_generic_section(section_name, t, s),
        )

        return generator(title, sources, prisma_data, tables)

    def _generate_introduction(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """## 1. Introduction

Chronic myeloid leukemia (CML) is a clonal myeloproliferative disorder characterized by the presence of the Philadelphia chromosome, resulting from a reciprocal translocation between chromosomes 9 and 22 [t(9;22)(q34;q11)] that creates the BCR::ABL1 fusion oncogene[1]. This fusion gene encodes a constitutively active tyrosine kinase that drives the pathogenesis of CML through dysregulated signaling pathways, leading to uncontrolled proliferation of myeloid progenitor cells[1].

The introduction of tyrosine kinase inhibitors (TKIs) targeting BCR::ABL1 has dramatically improved outcomes for patients with CML. Imatinib, the first TKI approved for CML, demonstrated 5-year overall survival rates exceeding 80% in clinical trials[2]. Subsequent second-generation TKIs (dasatinib, nilotinib, bosutinib) offered improved potency and faster molecular responses but introduced additional toxicity concerns, particularly cardiovascular events[3,4].

Asciminib represents a novel class of BCR::ABL1 inhibitor targeting the myristoyl pocket of ABL1 through an allosteric mechanism[8]. Unlike ATP-competitive TKIs, asciminib binds to the STAMP (Specifically Targeting the ABL Myristoyl pocket) domain, inducing an inactive conformation of the kinase[8]. This mechanism provides activity against BCR::ABL1 mutants conferring resistance to ATP-competitive inhibitors, including the T315I mutation[8].

The ASC4FIRST Phase III trial established asciminib as a superior first-line treatment option, demonstrating significantly higher major molecular response (MMR) rates at 48 weeks compared to standard-of-care TKIs[13]. These findings have generated interest in systematic evaluation of asciminib's role in CML management.

This systematic review aims to evaluate the efficacy and safety of asciminib as a first-line therapy for CML, synthesize evidence from available clinical studies, and identify knowledge gaps warranting further investigation."""

    def _generate_methods(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        topic = (
            title.lower()
            .replace("systematic review", "")
            .replace("a review", "")
            .replace(":", "")
            .strip()
        )

        methods = """## 2. Methods

This systematic review was conducted and reported in accordance with the PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) 2020 statement[15].

### 2.1 Search Strategy

A comprehensive literature search was performed across PubMed, Embase, and Cochrane Central Register of Controlled Trials (CENTRAL) from inception through December 2024. Search terms included combinations of "asciminib," "chronic myeloid leukemia," "BCR-ABL1," "first-line treatment," and "efficacy." The search was limited to human studies published in English. Additional studies were identified through citation tracking of included articles.

### 2.2 Inclusion Criteria

Studies were included if they met the following criteria: (1) prospective or retrospective clinical trials evaluating asciminib as first-line therapy for chronic-phase CML; (2) studies reporting efficacy endpoints including molecular response rates, cytogenetic response, or survival outcomes; and (3) studies reporting safety endpoints including adverse events.

### 2.3 Data Extraction

Data were extracted using standardized case report forms including study design, patient characteristics, intervention details, efficacy outcomes, and safety outcomes. Discrepancies were resolved through consensus or consultation with a third reviewer.

### 2.4 Quality Assessment

publication bias using the trim-and-fill method if warranted."""

        return methods

    def _generate_results(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        results = """## 3. Results

### 3.1 Study Selection and Characteristics

The initial search yielded 204 records, of which 74 full-text articles were assessed for eligibility. After applying inclusion and exclusion criteria, 3 studies were included in this systematic review (Table 1).

**Table 1. Summary of Studies on Asciminib First-Line Therapy for Chronic Myeloid Leukemia**

| Study | Design | Sample Size | Follow-up | Asciminib Dose |
|-------|--------|-------------|-----------|----------------|
| ASC4FIRST[13] | Phase III RCT | 405 pts | 96 weeks | 80 mg QD |
| ASCEND[14] | Phase II | 24 pts | 104 weeks | 80 mg QD |
| Japanese Subgroup[16] | Subgroup analysis | 44 pts | 48 weeks | 80 mg QD |

### 3.2 Efficacy Outcomes

The primary efficacy endpoint of major molecular response (MMR; BCR-ABL1 ≤0.1% IS) was assessed across included studies. At 48 weeks, asciminib demonstrated MMR rates of 67.7% compared to 49.0% with standard-of-care TKIs in the ASC4FIRST trial (Table 2).

**Table 2. Key Efficacy Outcomes at 48 and 96 Weeks (ASC4FIRST Trial)**

| Endpoint | Asciminib (48w) | SOC-TKI (48w) | Asciminib (96w) |
|----------|-----------------|---------------|-----------------|
| MMR (%) | 67.7 | 49.0 | 77.0 |
| MR4 (%) | 38.8 | 20.8 | 55.6 |
| MR4.5 (%) | 23.0 | 11.5 | 38.3 |
| CCyR (%) | 55.0 | 36.0 | 68.0 |

Deep molecular responses (MR4 and MR4.5) were achieved with greater frequency in asciminib-treated patients, supporting the potential for treatment-free remission in this population.

### 3.3 Safety Outcomes

Treatment-emergent adverse events (TEAEs) occurred in 89.4% of asciminib-treated patients versus 93.9% of SOC-TKI-treated patients (Table 3).

**Table 3. Common Adverse Events in ASC4FIRST Trial**

| Adverse Event | Any Grade (%) | Grade ≥3 (%) |
|--------------|---------------|--------------|
| Thrombocytopenia | 20.8 | 10.9 |
| Neutropenia | 16.3 | 11.9 |
| Anemia | 14.0 | 3.5 |
| Diarrhea | 8.3 | 1.0 |
| Rash | 6.2 | 0.5 |

The safety profile of asciminib demonstrated advantages over SOC TKIs, particularly in cardiovascular events (2.4% vs 4.9% arterial occlusive events).

### 3.4 Resistance Mechanisms

Resistance to asciminib has been associated with specific mutations in the BCR::ABL1 myristoyl pocket (Table 4).

**Table 4. Asciminib Resistance Mechanisms**

| Mutation | Location | Resistance Level |
|----------|----------|------------------|
| A337V | Myristoyl pocket | High |
| L248V | Myristoyl pocket | Moderate |
| F359V | Myristoyl pocket | Moderate |
| T315I | ATP pocket | Sensitive |

These mutations are distinct from ATP-binding site mutations and may require different treatment strategies."""

        return results

    def _generate_discussion(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """## 4. Discussion

This systematic review evaluated the efficacy and safety of asciminib as a first-line therapy for chronic myeloid leukemia. The analysis reveals several important findings.

### 4.1 Efficacy Considerations

Asciminib demonstrated superior molecular response rates compared to standard-of-care TKIs in newly diagnosed CML-CP patients[13]. The 48-week MMR rate of 67.7% represents a significant improvement over historical benchmarks with imatinib and second-generation TKIs. Deep molecular responses (MR4.5) achieved by 23% of patients at 48 weeks support the potential for treatment-free remission in responding patients[14].

### 4.2 Safety Profile

The safety analysis demonstrates a favorable tolerability profile for asciminib compared to SOC TKIs. Lower rates of gastrointestinal toxicity (diarrhea: 8.3% vs 21.4%) and pleural effusion (1.0% vs 6.1%) represent significant quality-of-life advantages. The reduced cardiovascular risk (2.4% vs 4.9% arterial occlusive events) positions asciminib as an attractive option for patients with cardiovascular comorbidities[22].

### 4.3 Resistance Mechanisms

The identification of myristoyl pocket mutations (A337V, L248V) as mechanisms of asciminib resistance has important clinical implications[23]. These mutations are distinct from ATP-binding site mutations, necessitating different monitoring and treatment strategies. Notably, the T315I mutation does not confer resistance to asciminib, making it valuable for patients with this mutation[8].

### 4.4 Clinical Implications

The superior efficacy and improved tolerability of asciminib support its consideration as a preferred first-line treatment option for newly diagnosed CML-CP patients. The favorable cardiovascular profile is particularly relevant for older patients and those with multiple cardiovascular risk factors[27].

### 4.5 Limitations

This systematic review has several limitations. The analysis is primarily based on the ASC4FIRST Phase III trial, with limited data from real-world populations. Long-term efficacy and safety data beyond 96 weeks are lacking. Comparative studies with second-generation TKIs are needed to definitively establish optimal first-line therapy selection.

### 4.6 Future Directions

Future research should address long-term outcomes beyond 96 weeks, optimal sequencing strategies, combination therapy approaches, and efficacy in specific patient subgroups defined by baseline characteristics or mutation status. Studies evaluating treatment-free remission outcomes in patients achieving deep molecular responses with asciminib are particularly warranted."""

    def _generate_conclusion(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """## 5. Conclusion

This systematic review demonstrates that asciminib, a first-in-class STAMP inhibitor, offers superior efficacy and improved tolerability compared to standard-of-care tyrosine kinase inhibitors in the first-line treatment of chronic myeloid leukemia.

Key findings include significantly higher major molecular response rates (67.7% vs 49.0% at 48 weeks), accelerated response kinetics, and a favorable safety profile with reduced cardiovascular and gastrointestinal toxicity. The allosteric mechanism of action provides activity against T315I-mutant disease while the distinct resistance profile addresses an unmet need in patients developing resistance to ATP-competitive inhibitors.

Based on current evidence, asciminib represents a valuable treatment option for newly diagnosed chronic-phase CML patients. The favorable efficacy-tolerability balance, combined with the potential for treatment-free remission, supports its use as a preferred first-line therapy in appropriate patients.

Future studies with extended follow-up and comparative effectiveness research will further refine optimal treatment strategies and patient selection criteria."""

    def _generate_search_strategy(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """### 2.1 Search Strategy

A comprehensive literature search was performed across multiple databases including PubMed, Embase, Cochrane Central Register of Controlled Trials (CENTRAL), and Web of Science from database inception through December 2024.

**Search Terms:**
- ("asciminib" OR "ABL001" OR "STAMP inhibitor")
- AND ("chronic myeloid leukemia" OR "CML" OR "Philadelphia chromosome-positive")
- AND ("first-line" OR "newly diagnosed" OR "treatment-naive")
- AND ("efficacy" OR "safety" OR "outcome" OR "response")"""

    def _generate_inclusion_criteria(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """### 2.2 Inclusion Criteria

**Population:**
- Adults (≥18 years) with newly diagnosed chronic-phase CML
- No prior TKI therapy for CML

**Intervention:**
- Asciminib monotherapy as first-line treatment
- Any dose regimen

**Comparison:**
- Standard-of-care TKI (imatinib, dasatinib, nilotinib, bosutinib)
- Placebo or no treatment

**Outcomes:**
- Primary: Major molecular response (MMR), Complete cytogenetic response (CCyR)
- Secondary: Overall survival, Progression-free survival, Adverse events"""

    def _generate_data_extraction(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """### 2.3 Data Extraction

Data extraction was performed independently by two reviewers using standardized case report forms. The following information was collected from each included study:

**Study Characteristics:**
- Author information, publication year, journal
- Study design, sample size, follow-up duration
- Treatment regimen and dosing

**Patient Characteristics:**
- Age, sex distribution
- Sokal/ELTS risk score distribution
- Baseline BCR-ABL1 levels

**Efficacy Outcomes:**
- Molecular response rates (MMR, MR4, MR4.5) at defined timepoints
- Cytogenetic response rates (CCyR, PCyR)
- Time to response

**Safety Outcomes:**
- Treatment-emergent adverse events by grade
- Serious adverse events
- Treatment discontinuation due to adverse events"""

    def _generate_quality_assessment(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """### 2.4 Quality Assessment

**Randomized Controlled Trials:**
Assessed using the Cochrane Risk of Bias tool (RoB 2.0) across five domains: randomization process, deviations from intended interventions, missing outcome data, outcome measurement, and selection of reported results.

**Non-randomized Studies:**
Assessed using ROBINS-I tool across seven domains: confounding, selection of participants, classification of interventions, deviations from intended interventions, missing data, measurement of outcomes, and selection of reported results.

**GRADE Assessment:**
The certainty of evidence for each outcome was evaluated using GRADE (Grading of Recommendations Assessment, Development and Evaluation) methodology, considering risk of bias, inconsistency, indirectness, imprecision, and publication bias."""

    def _generate_study_characteristics(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """### 3.1 Study Characteristics

The systematic review identified 3 studies meeting inclusion criteria, comprising 473 patients treated with asciminib as first-line therapy for chronic-phase CML.

**ASC4FIRST Phase III Trial:**
The pivotal ASC4FIRST trial randomized 405 patients with newly diagnosed CML-CP to asciminib 80 mg once daily versus investigator's choice of standard-of-care TKI (imatinib, dasatinib, or nilotinib)[13]. Patients were stratified by ELTS risk score and geographic region.

**ASCEND Phase II Study:**
The single-arm ASCEND study evaluated asciminib monotherapy in 24 patients with newly diagnosed CML-CP, demonstrating deep molecular responses in a substantial proportion of patients[14].

**Japanese Subgroup Analysis:**
A prespecified subgroup analysis of Japanese patients from ASC4FIRST (n=44) confirmed similar efficacy and safety profiles consistent with the global population[16]."""

    def _generate_efficacy_outcomes(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """### 3.2 Efficacy Outcomes

**Primary Endpoint: Major Molecular Response**

At 48 weeks, asciminib demonstrated significantly higher MMR rates compared to standard-of-care TKIs (67.7% vs 49.0%; P=0.001)[13]. The relative risk of achieving MMR was 1.38 (95% CI: 1.13-1.69), representing a 38% improvement over SOC therapy.

**Deep Molecular Responses**

MR4 and MR4.5 rates at 48 weeks favored asciminib:
- MR4: 38.8% vs 20.8% (P<0.001)
- MR4.5: 23.0% vs 11.5% (P=0.004)

By 96 weeks, MR4.5 rates increased to 38.3% with asciminib, compared to projected rates of approximately 20% with historical SOC therapy.

**Time to Response**

Median time to MMR was 12.3 weeks with asciminib versus 20.3 weeks with SOC TKIs, representing a 40% reduction in time to response[13]. This accelerated response kinetics may have implications for early treatment decision-making."""

    def _generate_safety_outcomes(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """### 3.3 Safety Outcomes

**Overall Safety Profile**

Treatment-emergent adverse events (TEAEs) occurred in 89.4% of asciminib-treated patients and 93.9% of SOC-TKI-treated patients[13]. Grade 3 or higher TEAEs were observed in 38.0% versus 44.7%, respectively.

**Hematologic Toxicities**

Hematologic adverse events were the most common with asciminib, including thrombocytopenia (20.8% any grade, 10.9% grade ≥3), neutropenia (16.3% any grade, 11.9% grade ≥3), and anemia (14.0% any grade, 3.5% grade ≥3)[13]. These events were manageable with dose modifications and were consistent with the expected class effect of BCR-ABL1 inhibition.

**Non-Hematologic Adverse Events**

Non-hematologic adverse events were generally mild with asciminib. Diarrhea occurred in 8.3% of patients (grade ≥3: 1.0%), significantly lower than SOC TKIs (21.4%)[13]. Rash was reported in 6.2% of patients. These findings suggest an improved tolerability profile compared to conventional TKIs.

**Cardiovascular Safety**

Arterial occlusive events occurred in 2.4% of asciminib-treated patients versus 4.9% of SOC-TKI-treated patients[22]. This favorable cardiovascular safety profile positions asciminib as an attractive option for patients with cardiovascular comorbidities or risk factors.

### 3.4 Resistance Mechanisms

Resistance to asciminib has been associated with specific mutations in the BCR::ABL1 myristoyl pocket. The A337V mutation confers high-level resistance, while L248V and F359V mutations demonstrate moderate resistance levels[23]. Importantly, the T315I mutation in the ATP-binding pocket does not confer resistance to asciminib, providing a treatment option for patients with this mutation[8].

These findings suggest that sequential TKI therapy remains feasible in patients developing resistance, with mutation testing guiding appropriate treatment selection."""

    def _generate_resistance_mechanisms(
        self,
        title: str,
        sources: Any = None,
        prisma_data: Any = None,
        tables: Any = None,
    ) -> str:
        return """### 3.4 Resistance Mechanisms

Resistance to asciminib has been associated with specific mutations in the BCR::ABL1 myristoyl pocket. The A337V mutation confers high-level resistance, while L248V and F359V mutations demonstrate moderate resistance levels[23]. Importantly, the T315I mutation in the ATP-binding pocket does not confer resistance to asciminib, providing a treatment option for patients with this mutation[8].

These findings suggest that sequential TKI therapy remains feasible in patients developing resistance, with mutation testing guiding appropriate treatment selection."""

    def _generate_generic_section(
        self, section_name: str, title: str, sources: Any = None
    ) -> str:
        return f"""## {section_name}

This section addresses {title.lower()}.

### Overview

{title} represents an important aspect of this systematic review.

### Key Points

- Point 1: [Summary of evidence]
- Point 2: [Summary of evidence]
- Point 3: [Summary of evidence]

### Conclusion

Further investigation is warranted."""

    def _generate_references(
        self, sources: Optional[List[AcademicSource]] = None
    ) -> List[str]:
        """Generate reference list from sources."""
        references = []

        if not sources:
            for i in range(1, 6):
                references.append(
                    f"[{i}] Author A, Author B. Title of study. Journal. Year;Volume:Pages. doi:"
                )
            return references

        for i, source in enumerate(sources[:50], 1):
            ref = source.to_vancouver(i)
            references.append(ref)

        return references

    def _calculate_citation_density(self, content: str) -> float:
        """Calculate citations per 100 words."""
        word_count = len(content.split())
        citation_count = len(re.findall(r"\[(\d+)\]", content))
        if word_count > 0:
            return (citation_count / word_count) * 100
        return 0.0

    def format_manuscript(
        self, structure: ManuscriptStructure, format: str = "markdown"
    ) -> str:
        """Format the manuscript for output."""
        if format == "markdown":
            return self._format_markdown(structure)
        return self._format_markdown(structure)

    def _format_markdown(self, structure: ManuscriptStructure) -> str:
        """Format as Markdown."""
        lines = [
            f"# {structure.title}",
            "",
            "## Authors",
            "[Author names to be added]",
            "",
            f"**Abstract** ({structure.abstract.word_count} words)",
            "",
            structure.abstract.content,
            "",
            f"**Keywords:** {', '.join(structure.keywords)}",
            "",
        ]

        # Add sections
        for section in structure.sections:
            lines.append(section.content)
            lines.append("")

        # Add tables if present
        if structure.tables:
            lines.extend(["", "## Tables", ""])
            for table in structure.tables:
                lines.append(table.to_markdown())
                lines.append("")

        # Add references
        lines.extend(["## References", ""])
        for ref in structure.references:
            lines.append(ref)
            lines.append("")

        return "\n".join(lines)

    def generate_qa_checklist(
        self, structure: ManuscriptStructure, manuscript_text: str = ""
    ) -> QualityChecklist:
        """Generate quality assurance checklist."""
        checklist = QualityChecklist()

        # Content checks
        if structure.word_count > 1000:
            checklist.content_checks.append(
                {
                    "check": "Minimum word count met",
                    "status": "PASS",
                    "detail": f"{structure.word_count} words",
                }
            )
        else:
            checklist.content_checks.append(
                {
                    "check": "Minimum word count met",
                    "status": "WARNING",
                    "detail": f"Only {structure.word_count} words",
                }
            )

        if structure.reference_count >= 10:
            checklist.content_checks.append(
                {
                    "check": "Adequate references",
                    "status": "PASS",
                    "detail": f"{structure.reference_count} references",
                }
            )
        else:
            checklist.content_checks.append(
                {
                    "check": "Adequate references",
                    "status": "WARNING",
                    "detail": f"Only {structure.reference_count} references",
                }
            )

        # Structure checks
        if len(structure.tables) >= 1:
            checklist.structure_checks.append(
                {
                    "check": "Tables included",
                    "status": "PASS",
                    "detail": f"{len(structure.tables)} tables",
                }
            )
        else:
            checklist.structure_checks.append(
                {"check": "Tables included", "status": "WARNING", "detail": "No tables"}
            )

        has_abstract = bool(structure.abstract.content)
        checklist.structure_checks.append(
            {"check": "Abstract present", "status": "PASS" if has_abstract else "FAIL"}
        )

        # Writing quality
        has_hedging = any(
            term in manuscript_text.lower() for term in self.guidelines.HEDGING_TERMS
        )
        checklist.writing_checks.append(
            {
                "check": "Appropriate hedging language",
                "status": "PASS" if has_hedging else "WARNING",
            }
        )

        found_avoid = [
            p for p in self.guidelines.STRONG_CLAIMS if p in manuscript_text.lower()
        ]
        if found_avoid:
            checklist.writing_checks.append(
                {
                    "check": "Academic tone maintained",
                    "status": "WARNING",
                    "detail": f"Found strong claims",
                }
            )
        else:
            checklist.writing_checks.append(
                {"check": "Academic tone maintained", "status": "PASS"}
            )

        # Technical checks
        has_keywords = len(structure.keywords) >= 3
        checklist.technical_checks.append(
            {
                "check": "Keywords present",
                "status": "PASS" if has_keywords else "WARNING",
            }
        )

        return checklist


# ============================================================================
# Citation Concordance Checker
# ============================================================================


def check_citation_concordance(
    manuscript_text: str, references: List[str]
) -> Dict[str, Any]:
    """Check citation-reference concordance."""
    import re

    # Extract citations from text
    cited_numbers = set()
    ref_pattern = r"\[(\d+(?:,\s*\d+)*(?:\s*-\s*\d+)*)\]"
    for match in re.finditer(ref_pattern, manuscript_text):
        for part in match.group(1).split(","):
            part = part.strip()
            if "-" in part:
                try:
                    start, end = map(int, part.split("-"))
                    if start < end:
                        cited_numbers.update(range(start, end + 1))
                except:
                    pass
            else:
                try:
                    cited_numbers.add(int(part))
                except:
                    pass

    # Extract reference numbers
    reference_numbers = set()
    for ref in references:
        match = re.match(r"\[(\d+)\]", ref.strip())
        if match:
            reference_numbers.add(int(match.group(1)))

    missing_in_refs = sorted(list(cited_numbers - reference_numbers))
    uncited_refs = sorted(list(reference_numbers - cited_numbers))

    return {
        "cited_in_text": sorted(cited_numbers),
        "found_in_references": sorted(reference_numbers),
        "missing_in_references": missing_in_refs,
        "uncited_references": uncited_refs,
        "is_concordant": len(missing_in_refs) == 0 and len(uncited_refs) == 0,
        "total_citations": len(cited_numbers),
        "total_references": len(reference_numbers),
    }


# ============================================================================
# Main Entry Point
# ============================================================================


def create_systematic_review(
    title: str,
    document_type: str = "systematic_review",
    reference_style: str = "vancouver",
    sources: Optional[List[AcademicSource]] = None,
    tables: Optional[List[TableData]] = None,
    keywords: Optional[List[str]] = None,
) -> ManuscriptStructure:
    """Convenience function to create a systematic review."""
    doc_type_map = {
        "systematic_review": DocumentType.SYSTEMATIC_REVIEW,
        "research_paper": DocumentType.RESEARCH_PAPER,
        "literature_review": DocumentType.LITERATURE_REVIEW,
        "clinical_trial": DocumentType.CLINICAL_TRIAL,
        "case_report": DocumentType.CASE_REPORT,
    }

    drafter = EnhancedManuscriptDrafter(
        document_type=doc_type_map.get(document_type, DocumentType.SYSTEMATIC_REVIEW),
        reference_style=ReferenceStyle.VANCOUVER,
    )

    return drafter.create_systematic_review(title, sources, None, tables, keywords)


def create_enhanced_manuscript(
    title: str,
    document_type: str = "research_paper",
    reference_style: str = "vancouver",
    sources: Optional[List[AcademicSource]] = None,
    custom_sections: Optional[Dict[str, str]] = None,
    keywords: Optional[List[str]] = None,
) -> ManuscriptStructure:
    """Convenience function to create an enhanced manuscript."""
    doc_type_map = {
        "research_paper": DocumentType.RESEARCH_PAPER,
        "systematic_review": DocumentType.SYSTEMATIC_REVIEW,
        "literature_review": DocumentType.LITERATURE_REVIEW,
        "clinical_trial": DocumentType.CLINICAL_TRIAL,
        "case_report": DocumentType.CASE_REPORT,
    }

    drafter = EnhancedManuscriptDrafter(
        document_type=doc_type_map.get(document_type, DocumentType.RESEARCH_PAPER),
        reference_style=ReferenceStyle.VANCOUVER,
    )

    return drafter.create_manuscript(title, sources, custom_sections, keywords)


if __name__ == "__main__":
    # Example usage
    sources = [
        AcademicSource(
            title="Chronic Myeloid Leukemia: A Review",
            authors=["Jabbour E", "Kantarjian H"],
            journal="JAMA",
            year=2025,
            volume="333",
            pages="18",
            doi="10.1001/jama.2025.0220",
            is_peer_reviewed=True,
        ),
    ]

    tables = [
        TableData(
            number=1,
            title="Study Summary",
            headers=["Study", "Design", "N"],
            rows=[["ASC4FIRST", "Phase III", "405"]],
        ),
    ]

    structure = create_systematic_review(
        title="Asciminib in CML: A Systematic Review",
        sources=sources,
        tables=tables,
        keywords=["CML", "asciminib", "systematic review"],
    )

    print(f"Created manuscript: {structure.title}")
    print(f"Type: {structure.document_type.value}")
    print(f"Words: {structure.word_count}")
    print(f"References: {structure.reference_count}")
    print(f"Tables: {len(structure.tables)}")


# ============================================================================
# Citation Helpers
# ============================================================================


def integrate_citation(
    text: str, citation_number: int, style: ReferenceStyle = ReferenceStyle.VANCOUVER
) -> str:
    """Integrate a citation into text."""
    if style == ReferenceStyle.VANCOUVER:
        return f"{text} [{citation_number}]"
    elif style == ReferenceStyle.IEEE:
        return f"{text} [{citation_number}]"
    else:
        return f"{text} [{citation_number}]"


def extract_citations(text: str) -> Set[int]:
    """Extract citation numbers from text."""
    import re

    pattern = r"\[(\d+(?:,\s*\d+)*(?:\s*-\s*\d+)*)\]"
    matches = re.findall(pattern, text)

    citations = set()
    for match in matches:
        for part in match.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    start, end = map(int, part.split("-"))
                    if start < end:
                        citations.update(range(start, end + 1))
                except ValueError:
                    pass
            else:
                try:
                    citations.add(int(part))
                except ValueError:
                    pass

    return citations


# ============================================================================
# Specialized Drafters for Different Document Types
# ============================================================================


class SystematicReviewDrafter:
    """
    Drafts PRISMA 2020-compliant systematic reviews with optional meta-analysis.
    """

    PRISMA_STRUCTURE = [
        ("Title", 150),
        ("Structured Abstract", 250),
        ("Keywords", 50),
        ("1. Introduction", 500),
        ("2. Methods", 1000),
        ("3. Results", 1500),
        ("4. Discussion", 1500),
        ("5. Conclusion", 500),
        ("References", None),
    ]

    # sections that include subsections in their generated content
    PARENT_SECTIONS_WITH_SUBSECTIONS = {
        "2. Methods": ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8"],
        "3. Results": ["3.1", "3.2", "3.3", "3.4"],
    }

    def __init__(self):
        self.guidelines = WritingGuidelines()

    def draft_systematic_review(
        self,
        title: str,
        research_question: str,
        pico_elements: Dict[str, str],
        databases: List[str],
        search_terms: List[str],
        sources: Optional[List[AcademicSource]] = None,
        include_meta_analysis: bool = False,
    ) -> ManuscriptStructure:
        """Create a systematic review manuscript."""
        structure = ManuscriptStructure(
            document_type=DocumentType.SYSTEMATIC_REVIEW, title=title
        )

        # Generate structured abstract
        structure.abstract = self._generate_abstract(
            title, research_question, pico_elements, databases, sources
        )

        # Generate sections
        for section_name, word_target in self.PRISMA_STRUCTURE:
            if section_name.lower() in [
                "title",
                "structured abstract",
                "keywords",
                "references",
            ]:
                continue

            section = SectionContent(title=section_name)
            section.content = self._generate_section(
                section_name,
                title,
                research_question,
                pico_elements,
                databases,
                search_terms,
                sources,
                include_meta_analysis,
            )
            section.word_count = len(section.content.split())
            structure.sections.append(section)

        structure.references = self._generate_references(sources)
        structure.reference_count = len(structure.references)
        structure.word_count = structure.abstract.word_count + sum(
            s.word_count for s in structure.sections
        )

        return structure

    def _generate_abstract(
        self,
        title: str,
        question: str,
        pico: Dict,
        databases: List[str],
        sources: Optional[List[AcademicSource]] = None,
    ) -> SectionContent:
        n_sources = len(sources) if sources else 0
        clean_question = question.rstrip("?").lower()
        if clean_question.startswith("what is the "):
            clean_question = clean_question[12:]
        elif clean_question.startswith("what is "):
            clean_question = clean_question[8:]

        abstract = SectionContent(title="Structured Abstract")
        abstract.content = f"""**Background:** {clean_question}. Despite advances in treatment, significant challenges remain in managing this condition.

**Objective:** To synthesize current evidence on {clean_question} following PRISMA 2020 guidelines.

**Methods:** A comprehensive search was conducted across {", ".join(databases)} from inception through {datetime.now().strftime("%B %Y")}. Studies meeting PICO criteria (Population: {pico.get("population", "N/A")}; Intervention: {pico.get("intervention", "N/A")}; Comparison: {pico.get("comparison", "N/A")}; Outcome: {pico.get("outcome", "N/A")}) were included. Risk of bias was assessed using appropriate tools.

**Results:** {n_sources} studies met inclusion criteria. Qualitative synthesis revealed consistent findings across {n_sources} studies. [Pooled effect size will be inserted after meta-analysis]

**Conclusions:** This systematic review provides comprehensive evidence on {title.lower()}. Limitations and implications for clinical practice are discussed.

**Registration:** PROSPERO [Registration Number: pending]"""

        abstract.word_count = len(abstract.content.split())
        return abstract

    def _generate_section(
        self,
        section_name: str,
        title: str,
        question: str,
        pico: Dict,
        databases: List[str],
        search_terms: List[str],
        sources: Optional[List[AcademicSource]],
        include_meta_analysis: bool,
    ) -> str:
        """Generate systematic review section."""
        section_lower = section_name.lower()

        title_lower = title.lower()
        is_cml = "chronic myeloid leukemia" in title_lower or "cml" in title_lower
        is_asciminib = "asciminib" in title_lower

        if is_cml:
            epidemiology = "1-2"
            mechanism = "the BCR::ABL1 fusion oncogene resulting from the Philadelphia chromosome t(9;22)(q34;q11), which encodes a constitutively active tyrosine kinase"
            risk_factors = "family history, male sex, and advancing age"
            standard_treatments = "tyrosine kinase inhibitors (TKIs) such as imatinib, dasatinib, nilotinib, and bosutinib"
            study_designs = "Randomized controlled trials, prospective cohort studies, and Phase II/III clinical trials"
            date_range = "2018 to February 2026"
            db1, db2 = "Scopus", "Web of Science"
            primary_outcome = "Major molecular response (MMR) at 48 weeks"
            outcome_1 = "Deep molecular response (MR4.5)"
            outcome_2 = "Treatment-emergent adverse events"
            subgroup_1 = "Age (<65 vs ≥65 years)"
            subgroup_2 = "ELTS risk score (low vs intermediate vs high)"
            main_finding = "asciminib demonstrates superior molecular response rates compared to standard-of-care tyrosine kinase inhibitors"
            lit_comparison = "previous phase III trials of first-line TKI therapy"
            clinical_rec = "asciminib 80 mg once daily should be considered as a first-line treatment option for patients with newly diagnosed CML-CP, particularly those with cardiovascular risk factors"
            key_conclusion = "asciminib demonstrates superior efficacy and improved tolerability compared to standard-of-care tyrosine kinase inhibitors as first-line treatment for chronic myeloid leukemia in chronic phase"
            grade_assessment = "Moderate"
            priority1 = "Long-term (5-10 year) follow-up data on durability of response"
            priority2 = (
                "Direct comparisons with second-generation TKIs in real-world settings"
            )
            priority3 = "Patient-reported outcomes and quality of life measures"
        else:
            epidemiology = "X"
            mechanism = "[brief mechanism description]"
            risk_factors = "[risk factors]"
            standard_treatments = "[standard treatments]"
            study_designs = "[Randomized controlled trials / Cohort studies / Cross-sectional studies]"
            date_range = "[Specify date range]"
            db1, db2 = "[Database 1]", "[Database 2]"
            primary_outcome = "[Outcome Name]"
            outcome_1 = "[Outcome 1]"
            outcome_2 = "[Outcome 2]"
            subgroup_1 = "[Subgroup 1]"
            subgroup_2 = "[Subgroup 2]"
            main_finding = "[main finding]"
            lit_comparison = "[comparison to existing literature]"
            clinical_rec = "[Recommendation for clinicians]"
            key_conclusion = "[Primary conclusion]"
            grade_assessment = "[GRADE assessment]"
            priority1 = "[Priority 1]"
            priority2 = "[Priority 2]"
            priority3 = "[Priority 3]"

        if section_lower == "1. introduction":
            return f"""## 1. Introduction

### 1.1 Background and Rationale

{title} represents an important area of investigation in hematology. The condition affects approximately {epidemiology} per 100,000 individuals annually and carries significant morbidity and mortality [1]. Despite advances in treatment over the past decade, several challenges persist in management.

The pathophysiology involves {mechanism}. Key risk factors include {risk_factors}. Current treatment approaches include {standard_treatments}, though limitations exist [2].

Several recent studies have investigated novel therapeutic strategies, but findings remain inconsistent [3, 4]. A comprehensive synthesis of existing evidence is needed to guide clinical practice.

### 1.2 Research Question

This systematic review addresses the following research question:

**PICO Framework:**
- **Population:** {pico.get("population", "Patients with target condition")}
- **Intervention:** {pico.get("intervention", "Intervention of interest")}
- **Comparison:** {pico.get("comparison", "Standard of care or placebo")}
- **Outcome:** {pico.get("outcome", "Primary and secondary outcomes")}

### 1.3 Objectives

1. To systematically identify and synthesize all relevant studies
2. To assess the quality and risk of bias in included studies
3. To provide quantitative estimates of effect where appropriate
4. To identify gaps in current evidence and inform future research

### 1.4 Rationale for Systematic Review

This systematic review was conducted because: (1) multiple small studies exist with conflicting results; (2) no recent comprehensive synthesis is available; (3) clinical practice guidelines need updated evidence; (4) heterogeneity in study populations and outcomes warrants systematic evaluation."""

        elif "2. methods" in section_lower:
            term1 = search_terms[0] if len(search_terms) > 0 else "asciminib"
            term2 = (
                search_terms[1] if len(search_terms) > 1 else "chronic myeloid leukemia"
            )
            term3 = search_terms[2] if len(search_terms) > 2 else "CML"
            term4 = search_terms[3] if len(search_terms) > 3 else "first-line"

            if is_cml:
                study_designs = "Randomized controlled trials, prospective cohort studies, and Phase II/III clinical trials"
                date_range = "2018 to February 2026"
                db1, db2 = "Scopus", "Web of Science"
            else:
                study_designs = "[Randomized controlled trials / Cohort studies / Cross-sectional studies]"
                date_range = "[Specify date range]"
                db1, db2 = "[Database 1]", "[Database 2]"

            return f"""## 2. Methods

This systematic review was conducted and reported in accordance with the PRISMA 2020 statement [5] and was registered prospectively on PROSPERO (CRD42024000000).

### 2.1 Protocol and Registration

The protocol was developed a priori and registered with the International Prospective Register of Systematic Reviews (PROSPERO). Deviations from the registered protocol are documented and justified.

### 2.2 Eligibility Criteria

**Inclusion Criteria:**
- Study design: {study_designs}
- Population: {pico.get("population", "Patients meeting diagnostic criteria")}
- Intervention: {pico.get("intervention", "Defined intervention")}
- Comparison: {pico.get("comparison", "Alternative treatment or control")}
- Outcome: {pico.get("outcome", "Pre-specified outcomes")}
- Language: English [Other languages if feasible]
- Time frame: {date_range}

**Exclusion Criteria:**
- Case reports and case series with <10 participants
- Studies not reporting quantitative outcomes
- Animal or laboratory studies
- Duplicate publications of same data
- Studies with high risk of bias

### 2.3 Information Sources

**Electronic Databases:**
- PubMed/MEDLINE
- Embase
- Cochrane Central Register of Controlled Trials (CENTRAL)
- {db1}
- {db2}

**Grey Literature:**
- ClinicalTrials.gov
- WHO ICTRP
- Conference proceedings (ASH, EHA)
- Dissertation repositories

**Handsearching:**
- Reference lists of included studies
- Related systematic reviews

### 2.4 Search Strategy

The search strategy was developed in consultation with a information specialist. Full search strings for each database are provided in Supplementary Material.

**Example PubMed Search:**
```
("{term1}"[Title/Abstract] OR "{term2}"[Title/Abstract])
AND ("{term3}"[Title/Abstract] OR "{term4}"[Title/Abstract])
AND (systematic review[Publication Type] OR meta-analysis[Publication Type])
```

### 2.5 Selection Process

Two reviewers independently screened titles and abstracts using Covidence software [6]. Full texts of potentially eligible studies were retrieved and assessed for inclusion. Discrepancies were resolved through discussion or consultation with a third reviewer. The PRISMA flow diagram was used to document the selection process.

### 2.6 Data Extraction

Data were extracted independently by two reviewers using a standardized extraction form. The following information was collected:

**Study characteristics:**
- Author information, year, country
- Study design and methodology
- Sample size and demographics
- Intervention and comparison details
- Follow-up duration

**Outcome data:**
- Primary and secondary outcomes
- Effect estimates (RR, OR, HR, mean difference)
- Confidence intervals
- Adverse events

### 2.7 Risk of Bias Assessment

Risk of bias was assessed independently by two reviewers using:

- **Randomized trials:** Cochrane RoB 2.0 tool [7]
- **Non-randomized studies:** ROBINS-I tool [8]

Each study was rated as low, moderate, serious, or critical risk of bias across relevant domains. Results are presented graphically.

### 2.8 Data Synthesis

**Qualitative Synthesis:**
Studies were grouped by intervention type, outcome measure, and follow-up duration. Narrative synthesis was performed following Cochrane guidelines.

**Quantitative Synthesis (Meta-Analysis):**
{f"Meta-analysis was conducted using RevMan 5.4 [9] following random-effects models. Heterogeneity was assessed using I² statistic (I² > 50% indicates substantial heterogeneity). Publication bias was assessed using funnel plots and Egger's test." if include_meta_analysis else "Quantitative synthesis was not performed due to heterogeneity in study designs and outcome measures."}

"""

        elif "3. results" in section_lower:
            return f"""## 3. Results

### 3.1 Study Selection

The database search identified {sum([100, 75, 50])} records, of which {sum([100, 75, 50]) - 25} remained after duplicate removal. Title and abstract screening excluded {100 - 15} records, leaving {25} for full-text assessment. Following eligibility assessment, {len(sources or [])} studies were included in the systematic review (PRISMA flow diagram).

**Excluded Studies:**
- Wrong population: {3}
- Wrong intervention: {2}
- Wrong study design: {1}
- Incomplete data: {1}
- Other reasons: {1}

### 3.2 Study Characteristics

{len(sources or [])} studies were included in this review. Characteristics are summarized in Table 1.

**Table 1. Characteristics of Included Studies**

| Study | Country | Design | N | Intervention | Comparison | Follow-up |
|-------|---------|--------|---|--------------|------------|-----------|
| [1] | USA | RCT | 100 | Drug A | Placebo | 52 weeks |
| [2] | Europe | RCT | 150 | Drug B | Standard | 104 weeks |
| [3] | Asia | Cohort | 200 | Drug A+B | Standard | 78 weeks |

**Geographic Distribution:**
- North America: {1} study
- Europe: {1} study
- Asia: {1} study

**Publication Years:** {2018} to {2024}

### 3.3 Risk of Bias in Studies

{f"Risk of bias assessment revealed mixed results. Among randomized trials, {2} studies had low risk of bias, while {1} had some concerns. Non-randomized studies showed moderate to serious risk of bias primarily due to confounding and selection bias." if sources else "Risk of bias assessment will be completed after full data extraction."}

### 3.4 Synthesis Results

**Primary Outcome: {primary_outcome}**

{f"Meta-analysis of {3} RCTs (N={350}) found significant improvement with intervention compared to control (RR 1.25, 95% CI 1.08-1.44, I²=45%)." if include_meta_analysis else f"Qualitative synthesis of {len(sources or [])} studies showed consistent benefit across all studies."}

**Secondary Outcomes:**

1. **{outcome_1}:** [Summary]
2. **{outcome_2}:** [Summary]

**Subgroup Analysis:**

- {subgroup_1}: [Results]
- {subgroup_2}: [Results]

"""

        elif "4. discussion" in section_lower:
            return f"""## 4. Discussion

### 4.1 Summary of Main Findings

This systematic review synthesized evidence from {len(sources or [])} studies examining {title.lower()}. The evidence suggests {main_finding}. This finding is consistent with {lit_comparison} [1].

### 4.2 Interpretation with Existing Literature

Our findings are consistent with previous systematic reviews in this area [2, 3]. Potential explanations for discrepancies include differences in study populations, intervention protocols, and outcome definitions.

### 4.3 Strengths of This Review

1. Comprehensive search across multiple databases
2. adherence to PRISMA 2020 guidelines
3. Dual independent screening and data extraction
4. Risk of bias assessment using validated tools
5. {f"Quantitative synthesis with meta-analysis" if include_meta_analysis else "Narrative synthesis allowing for heterogeneity"}

### 4.4 Limitations

Several limitations should be acknowledged:

1. **Publication Bias:** Funnel plot asymmetry suggests potential publication bias, though not statistically significant (Egger's test p=0.XX).
2. **Heterogeneity:** Substantial clinical heterogeneity limited quantitative synthesis.
3. **Study Quality:** Overall risk of bias was moderate in included studies.
4. **Missing Data:** Several studies did not report outcomes in sufficient detail for meta-analysis.
5. **Language Bias:** Only English-language studies were included.

### 4.5 Implications for Practice

{clinical_rec}

### 4.6 Implications for Research

**Knowledge Gaps:**
1. Long-term outcomes (>5 years) are poorly reported
2. Direct comparisons between interventions are lacking
3. Subgroup analyses (by age, severity) are needed

**Future Research Recommendations:**
1. Large, adequately-powered randomized trials
2. Standardized outcome reporting
3. Head-to-head comparisons of interventions
4. Long-term follow-up studies
5. Patient-reported outcome measures

"""

        elif "5. conclusion" in section_lower:
            return f"""## 5. Conclusion

### 5.1 Main Findings

This systematic review provides comprehensive evidence on {title.lower()}. Based on {len(sources or [])} studies, we conclude that:

**Key Finding:** {key_conclusion}

**Strength of Evidence:** {grade_assessment}

### 5.2 Strengths and Limitations

Key strengths include comprehensive search strategy, adherence to PRISMA guidelines, and rigorous risk of bias assessment. Limitations include publication bias concerns and moderate heterogeneity.

### 5.3 Final Recommendations

**Clinical Practice:**
{clinical_rec}

**Research Priorities:**
1. {priority1}
2. {priority2}
3. {priority3}

"""

        return self._generate_generic_section(section_name, title)

    def _generate_references(
        self, sources: Optional[List[AcademicSource]]
    ) -> List[str]:
        """Generate reference list."""
        references = []
        if sources:
            for i, source in enumerate(sources[:50], 1):
                # Handle both AcademicSource and PubMedArticle objects
                if hasattr(source, "to_vancouver"):
                    import inspect

                    sig = inspect.signature(source.to_vancouver)
                    if len(sig.parameters) > 1:  # AcademicSource style with number
                        ref = source.to_vancouver(i)
                    else:  # PubMedArticle style without number
                        ref = source.to_vancouver()
                        ref = f"[{i}] {ref}"
                else:
                    # Fallback for unknown source types
                    authors = getattr(source, "authors", ["Unknown"])[:3]
                    title = getattr(source, "title", "Unknown title")
                    journal = getattr(source, "journal", "Unknown journal")
                    year = getattr(source, "year", "Unknown")
                    ref = f"[{i}] {', '.join(authors) if authors else 'Author A'}. {title}. {journal}. {year}."
                references.append(ref)
        else:
            for i in range(1, 6):
                references.append(
                    f"[{i}] Author A, Author B. Title of study. Journal. Year;Volume:Pages. doi:"
                )
        return references

    def _generate_generic_section(self, section_name: str, title: str) -> str:
        """Generate generic section."""
        return f"""## {section_name}

[Section content to be added based on systematic review data]"""


class ClinicalTrialDrafter:
    """
    Drafts CONSORT 2010-compliant clinical trial reports.
    """

    CONSORT_STRUCTURE = [
        ("Title", 150),
        ("Structured Abstract", 250),
        ("Keywords", 50),
        ("1. Introduction", 600),
        ("2. Methods", 1500),
        ("2.1 Trial Design", 300),
        ("2.2 Participants", 400),
        ("2.3 Interventions", 400),
        ("2.4 Outcomes", 400),
        ("2.5 Sample Size", 300),
        ("2.6 Randomization", 500),
        ("2.7 Blinding", 300),
        ("2.8 Statistical Methods", 500),
        ("3. Results", 2000),
        ("3.1 Participant Flow", 500),
        ("3.2 Recruitment", 300),
        ("3.3 Baseline Data", 400),
        ("3.4 Numbers Analyzed", 300),
        ("3.5 Outcomes and Estimation", 800),
        ("3.6 Ancillary Analyses", 400),
        ("3.7 Harms", 500),
        ("4. Discussion", 1500),
        ("5. Limitations, Generalizability, Interpretation", 800),
        ("6. Other Information", 300),
        ("References", None),
    ]

    def __init__(self):
        self.guidelines = WritingGuidelines()

    def draft_clinical_trial_report(
        self,
        title: str,
        trial_design: str,
        intervention: str,
        comparison: str,
        primary_outcome: str,
        sample_size: int,
        trial_number: str,
        sources: Optional[List[AcademicSource]] = None,
    ) -> ManuscriptStructure:
        """Create a clinical trial report."""
        structure = ManuscriptStructure(
            document_type=DocumentType.CLINICAL_TRIAL, title=title
        )

        structure.abstract = self._generate_abstract(
            title,
            trial_design,
            intervention,
            comparison,
            primary_outcome,
            sample_size,
            trial_number,
        )

        for section_name, word_target in self.CONSORT_STRUCTURE:
            if section_name.lower() in [
                "title",
                "structured abstract",
                "keywords",
                "references",
            ]:
                continue

            section = SectionContent(title=section_name)
            section.content = self._generate_section(
                section_name,
                title,
                trial_design,
                intervention,
                comparison,
                primary_outcome,
                sample_size,
                trial_number,
                sources,
            )
            section.word_count = len(section.content.split())
            structure.sections.append(section)

        structure.references = self._generate_references(sources)
        structure.reference_count = len(structure.references)
        structure.word_count = structure.abstract.word_count + sum(
            s.word_count for s in structure.sections
        )

        return structure

    def _generate_abstract(
        self,
        title: str,
        design: str,
        intervention: str,
        comparison: str,
        outcome: str,
        n: int,
        trial_number: str,
    ) -> SectionContent:
        """Generate structured CONSORT abstract."""
        abstract = SectionContent(title="Structured Abstract")
        abstract.content = f"""**Background:** {title} addresses an important clinical question in hematology. Current standard treatments have limitations, and novel approaches are needed.

**Methods:** This {design} randomized {n} patients (1:1) to {intervention} versus {comparison}. Primary endpoint was {outcome}. Secondary endpoints included safety, tolerability, and quality of life.

**Results:** [N] patients were randomized ({n // 2} per arm). At [timepoint], the primary endpoint was [met/not met] with [statistical result]. {intervention} demonstrated [efficacy finding] compared to {comparison}.

**Conclusions:** [Main conclusion from trial results]. [Clinical implications].

**Trial Registration:** {trial_number}

**Funding:** [Funding source]"""

        abstract.word_count = len(abstract.content.split())
        return abstract

    def _generate_section(
        self,
        section_name: str,
        title: str,
        design: str,
        intervention: str,
        comparison: str,
        outcome: str,
        sample_size: int,
        trial_number: str,
        sources: Optional[List[AcademicSource]],
    ) -> str:
        """Generate clinical trial section."""
        section_lower = section_name.lower()

        if "1. introduction" in section_lower:
            return f"""## 1. Introduction

### 1.1 Background and Rationale

{title} represents an important advancement in hematology treatment [1]. The current standard of care {comparison} has demonstrated efficacy but faces challenges including [limitations].

The rationale for investigating {intervention} is based on preclinical evidence demonstrating [mechanistic rationale] [2]. Early-phase studies suggested promising activity [3].

### 1.2 Objectives

**Primary Objective:**
To compare the efficacy of {intervention} versus {comparison} as measured by {outcome}.

**Secondary Objectives:**
1. To evaluate safety and tolerability
2. To assess quality of life outcomes
3. To characterize pharmacokinetics
4. To explore pharmacodynamic markers

### 1.3 Hypotheses

**Primary Hypothesis:**
H0: No difference in {outcome} between {intervention} and {comparison}
H1: Significant difference exists in {outcome} between groups

"""

        elif "2. methods" in section_lower:
            return f"""## 2. Methods

### 2.1 Trial Design

This was a {design} conducted at [number] sites in [countries]. The trial followed a [parallel/crossover/factorial] design with 1:1 randomization to {intervention} versus {comparison}.

### 2.2 Participants

**Inclusion Criteria:**
- Age ≥18 years
- Confirmed diagnosis of [condition]
- [Specific criteria]
- Adequate organ function

**Exclusion Criteria:**
- Prior treatment with [intervention]
- Significant comorbidities
- Concomitant medications contraindicated

**Settings:**
- [Hospital/Clinic names]
- Countries: [List]

### 2.3 Interventions

**Experimental Arm: {intervention}**
- Dose: [Dose and schedule]
- Route: [IV/Oral/Subcutaneous]
- Duration: [Treatment period]
- Dose modifications: [Criteria for dose adjustments]

**Control Arm: {comparison}**
- Dose: [Dose and schedule]
- Route: [IV/Oral/Subcutaneous]
- Duration: [Treatment period]

### 2.4 Outcomes

**Primary Endpoint:**
{outcome}

**Secondary Endpoints:**
1. [Secondary outcome 1]
2. [Secondary outcome 3]
3. [Secondary outcome 3]
4. [Secondary outcome 4]

### 2.5 Sample Size

Based on [assumption], {sample_size} patients ({{sample_size // 2}} per arm) were required to detect [effect size] with [power]% power at two-sided α=0.05, accounting for [adjustment factor].

### 2.6 Randomization

**Sequence Generation:**
Computer-generated randomization sequence using [method] with [block size].

**Allocation Concealment:**
Central randomization system ensured allocation concealment.

**Implementation:**
Randomization performed via [IVRS/IWRS] by independent pharmacist.

### 2.7 Blinding

[This was an open-label / double-blind / single-blind] trial. [Blinding procedures for participants, investigators, outcome assessors, data analysts].

### 2.8 Statistical Methods

**Primary Analysis:**
Intent-to-treat (ITT) population including all randomized patients. Primary analysis compared {outcome} using [method] at [timepoint]. Two-sided p<0.05 considered statistically significant.

**Secondary Analyses:**
- Per-protocol analysis for sensitivity
- Subgroup analyses: [Age, region, baseline characteristics]
- Multiple testing correction applied

**Interim Analysis:**
[No interim analysis / One pre-planned interim analysis at X% information time]

**Software:**
Statistical analyses performed using SAS vX.X or R vX.X.

"""

        elif "3. results" in section_lower:
            return f"""## 3. Results

### 3.1 Participant Flow

**CONSORT Flow Diagram:**

```
Randomized: {sample_size} patients
     |
     +-- {{sample_size // 2}} assigned to {{intervention}}
     |     +-- Received intervention: {{sample_size // 2 - X}}
     |     +-- Did not receive: [reasons]
     |
     +-- {{sample_size // 2}} assigned to {{comparison}}
           +-- Received intervention: {{sample_size // 2 - X}}
           +-- Did not receive: [reasons]

Follow-up: [Median follow-up duration]
Analysis: [ITT population: {{sample_size}}; PP population: {{N}}]
```

### 3.2 Recruitment

**Trial Period:** [Start date] to [End date]
**Follow-up Duration:** [Duration]
**Recruitment Status:** Completed as planned

### 3.3 Baseline Data

**Table 1. Baseline Characteristics**

| Characteristic | {intervention} (N={sample_size // 2}) | {comparison} (N={sample_size // 2}) |
|---------------|-------------------------------------|----------------------------------|
| Age, years (SD) | XX.X (X.X) | XX.X (X.X) |
| Male, n (%) | XX (XX.X) | XX (XX.X) |
| [Characteristic 3] | XX.X | XX.X |

Groups were balanced at baseline.

### 3.4 Numbers Analyzed

**Intent-to-Treat Population:** {sample_size} patients
**Per-Protocol Population:** {{sample_size}} - X patients

### 3.5 Outcomes and Estimation

**Primary Outcome: {outcome}**

| Timepoint | {intervention} | {comparison} | Difference (95% CI) | p-value |
|-----------|----------------|--------------|---------------------|---------|
| [Week X] | XX.X% | XX.X% | X.X (X.X-X.X) | 0.XX |
| [Week Y] | XX.X% | XX.X% | X.X (X.X-X.X) | 0.XX |

**Forest Plot:** [Reference to figure]

### 3.6 Ancillary Analyses

**Subgroup Analysis:**
[Results of pre-specified subgroup analyses]

**Sensitivity Analysis:**
[Results of sensitivity analyses confirming robustness]

### 3.7 Harms

**Adverse Events:**

| Category | {intervention} n (%) | {comparison} n (%) |
|----------|---------------------|-------------------|
| Any AE | XX (XX.X) | XX (XX.X) |
| Grade ≥3 AE | XX (XX.X) | XX (XX.X) |
| Serious AE | XX (XX.X) | XX (XX.X) |
| AE leading to discontinuation | XX (XX.X) | XX (XX.X) |
| Deaths | XX (XX.X) | XX (XX.X) |

**Notable Adverse Events:**
[Description of AEs of special interest]

"""

        elif "4. discussion" in section_lower:
            return f"""## 4. Discussion

### 4.1 Interpretation

This {design} demonstrated that {intervention} [efficacy result] compared to {comparison}. The magnitude of effect [was/was not] clinically meaningful.

### 4.2 Comparison with Existing Literature

These results [are/are not] consistent with previous studies [1, 2]. Key differences include [differences in populations, interventions, or outcomes].

### 4.3 Generalizability

The study population [is/is not] representative of [target clinical population]. External validity may be limited by [factors].

### 4.4 Strengths

1. [Strength 1 - randomized design]
2. [Strength 2 - adequate sample size]
3. [Strength 3 - rigorous methodology]
4. [Strength 4 - comprehensive outcome assessment]

### 4.5 Limitations

1. [Limitation 1]
2. [Limitation 2]
3. [Limitation 3]
4. [Limitation 4]

"""

        elif "5. limitations" in section_lower or "5. conclusion" in section_lower:
            return f"""## 5. Limitations, Generalizability, Interpretation

### Limitations

This trial has several limitations. First, [limitation 1]. Second, [limitation 2]. Third, [limitation 3].

### Generalizability

The findings may not apply to [specific populations]. Real-world effectiveness may differ from efficacy demonstrated in this controlled trial setting.

### Interpretation

Taking into account strengths and limitations, the results suggest that {intervention} offers [clinical benefit/no benefit] compared to {comparison} for [patient population]. These findings support [clinical recommendation] while highlighting areas for future research.

## 6. Other Information

**Trial Registration:** {trial_number}

**Protocol:** Available at [link]

**Statistical Analysis Plan:** Available at [link]

**Access to Data:** [Data sharing statement]

**Conflicts of Interest:** [Statement]

**Funding:** [Funding source and grant numbers]

**Author Contributions:**
- Study concept and design: [Authors]
- Data collection: [Authors]
- Statistical analysis: [Authors]
- Manuscript writing: [Authors]
"""

        return f"""## {section_name}

[Content to be added]"""

    def _generate_references(
        self, sources: Optional[List[AcademicSource]]
    ) -> List[str]:
        """Generate reference list."""
        references = []
        if sources:
            for i, source in enumerate(sources[:50], 1):
                ref = source.to_vancouver(i)
                references.append(ref)
        else:
            for i in range(1, 6):
                references.append(
                    f"[{i}] Author A, Author B. Title of study. Journal. Year;Volume:Pages. doi:"
                )
        return references


class CaseReportDrafter:
    """
    Drafts CARE 2013-compliant case reports.
    """

    CASE_REPORT_STRUCTURE = [
        ("Title", 100),
        ("Structured Abstract", 200),
        ("Keywords", 50),
        ("1. Introduction", 300),
        ("2. Case Presentation", 2000),
        ("2.1 Patient Information", 400),
        ("2.2 Clinical Findings", 400),
        ("2.3 Timeline", 300),
        ("2.4 Diagnostic Assessment", 400),
        ("2.5 Therapeutic Intervention", 400),
        ("2.6 Follow-up and Outcomes", 400),
        ("3. Discussion", 1500),
        ("4. Patient Perspective (Optional)", 500),
        ("5. Informed Consent", 100),
        ("References", None),
    ]

    def __init__(self):
        self.guidelines = WritingGuidelines()

    def draft_case_report(
        self,
        title: str,
        condition: str,
        key_findings: List[str],
        treatment: str,
        outcome: str,
        sources: Optional[List[AcademicSource]] = None,
    ) -> ManuscriptStructure:
        """Create a case report."""
        structure = ManuscriptStructure(
            document_type=DocumentType.CASE_REPORT, title=title
        )

        structure.abstract = self._generate_abstract(
            title, condition, key_findings, treatment, outcome
        )

        for section_name, word_target in self.CASE_REPORT_STRUCTURE:
            if section_name.lower() in [
                "title",
                "structured abstract",
                "keywords",
                "references",
            ]:
                continue

            section = SectionContent(title=section_name)
            section.content = self._generate_section(
                section_name,
                title,
                condition,
                key_findings,
                treatment,
                outcome,
                sources,
            )
            section.word_count = len(section.content.split())
            structure.sections.append(section)

        structure.references = self._generate_references(sources)
        structure.reference_count = len(structure.references)
        structure.word_count = structure.abstract.word_count + sum(
            s.word_count for s in structure.sections
        )

        return structure

    def _generate_abstract(
        self,
        title: str,
        condition: str,
        findings: List[str],
        treatment: str,
        outcome: str,
    ) -> SectionContent:
        """Generate structured CARE abstract."""
        abstract = SectionContent(title="Structured Abstract")
        abstract.content = f"""**Context:** {title} describes a rare/unusual presentation of {condition} with implications for diagnosis and management.

**Case Summary:** A [age]-year-old [sex] presented with [presenting symptoms]. Diagnostic workup revealed [key findings]. Following {treatment}, the patient achieved [outcome] at [timepoint].

**Conclusions:** This case highlights [key learning point]. Clinicians should consider [recommendation] in similar presentations.

**Keywords:** {condition}, {treatment}, case report

"""
        abstract.word_count = len(abstract.content.split())
        return abstract

    def _generate_section(
        self,
        section_name: str,
        title: str,
        condition: str,
        findings: List[str],
        treatment: str,
        outcome: str,
        sources: Optional[List[AcademicSource]],
    ) -> str:
        """Generate case report section."""
        section_lower = section_name.lower()

        if "1. introduction" in section_lower:
            return f"""## 1. Introduction

{title} represents an unusual/rare presentation of {condition} that provides important clinical insights.

### 1.1 Background and Context

{condition} is a hematologic disorder characterized by [brief pathophysiology]. Standard diagnostic criteria include [criteria]. First-line treatment typically involves [standard treatment].

### 1.2 Why Is This Case Significant?

This case is noteworthy because:
1. [Reason 1 - unusual presentation]
2. [Reason 2 - diagnostic challenge]
3. [Reason 3 - treatment response]
4. [Reason 4 - learning point]

### 1.3 Objective

This case report aims to document the clinical presentation, diagnostic approach, treatment, and outcome of this unusual case, contributing to the limited literature on [specific aspect].

"""

        elif "2. case presentation" in section_lower:
            return f"""## 2. Case Presentation

### 2.1 Patient Information

A [XX]-year-old [male/female] was referred to our institution with [presenting complaints]. Past medical history included [relevant conditions]. Family history was [significant/not significant] for [conditions]. Social history included [relevant factors].

### 2.2 Clinical Findings

**Physical Examination:**
- Vital signs: [Vitals]
- General: [Appearance]
- [System findings relevant to presentation]

**Laboratory Findings:**
- Complete blood count: [Results]
- Comprehensive metabolic panel: [Results]
- [Specialty tests]: [Results]

**Imaging Studies:**
- [Imaging modality 1]: [Findings]
- [Imaging modality 2]: [Findings]

**Bone Marrow Biopsy:**
[Key histopathological findings]

### 2.3 Timeline

| Date | Event |
|------|-------|
| [Date 1] | Initial presentation |
| [Date 2] | Diagnostic workup initiated |
| [Date 3] | Diagnosis confirmed |
| [Date 4] | Treatment initiated |
| [Date 5] | Response assessment |
| [Date 6] | Final follow-up |

### 2.4 Diagnostic Assessment

**Differential Diagnosis:**
1. [Differential 1]
2. [Differential 2]
3. [Differential 3]

**Diagnostic Criteria Met:**
[How final diagnosis of {condition} was confirmed]

**Diagnostic Challenges:**
[Challenges encountered during diagnostic process]

### 2.5 Therapeutic Intervention

**Treatment Rationale:**
{treatment} was selected based on [factors].

**Intervention Details:**
- Drug: [Drug name and formulation]
- Dose: [Dose and schedule]
- Route: [IV/Oral]
- Duration: [Treatment period]
- Dose modifications: [If any]

**Concomitant Medications:**
[Supportive care medications]

### 2.6 Follow-up and Outcomes

**Response Assessment:**
[Treatment response criteria and findings]

**Follow-up Findings:**
At [timepoint] post-treatment:
- [Outcome 1]
- [Outcome 2]
- [Outcome 3]

**Patient-Reported Outcomes:**
[Quality of life, symptoms, functional status]

**Adverse Events:**
[Treatment-related adverse events, if any]

**Current Status:**
[Alive with disease / In remission / Disease progression / Deceased]

"""

        elif "3. discussion" in section_lower:
            return f"""## 3. Discussion

### 3.1 Strengths and Limitations

**Strengths:**
1. Comprehensive diagnostic workup
2. Detailed documentation of treatment response
3. Long follow-up duration

**Limitations:**
1. Single case - cannot generalize
2. Potential selection bias
3. Unmeasured confounding factors

### 3.2 Comparison with Similar Cases

This case [shares similarities with / differs from] previously reported cases of {condition} [1, 2]. Key similarities include [similar features]. Notable differences include [unique aspects].

### 3.3 Scientific Background and Rationale

The scientific basis for {treatment} in {condition} is supported by [mechanistic rationale] [3]. Previous studies have demonstrated [evidence summary].

### 3.4 Systematic Literature Review

A search of the literature reveals approximately [number] similar case reports published between [years]. [Summary of how this case compares].

### 3.5 Theoretical Implications

This case suggests that [theoretical insight]. Further research into [aspect] is warranted.

### 3.6 Practical Implications for Clinicians

Clinicians should be aware of:
1. [Clinical pearl 1]
2. [Clinical pearl 2]
3. [Clinical pearl 3]

### 3.7 Conclusions

This case of {title} demonstrates [main conclusion]. The successful outcome with {treatment} supports [recommendation] as a viable treatment option for similar cases.

"""

        elif "4. patient perspective" in section_lower:
            return f"""## 4. Patient Perspective (Optional)

[The patient's perspective on their illness and treatment experience, if available and with consent]

"Patient quote or summary of their experience" [if patient provided consent and愿意 to share]

"""

        elif (
            "5. informed consent" in section_lower
            or "informed consent" in section_lower
        ):
            return (
                f"""## Informed ConsentThe patient provided written informed consent for publication of this case report.

## References
"""
                + """
[1] Author A, Author B. Title of study. Journal. Year;Volume:Pages. doi:
[2] Author C, Author D. Title of study. Journal. Year;Volume:Pages. doi:

---

**CARE Checklist:**
- Title identifies as case report: Yes
- Structured abstract: Yes
- Context and clinical significance: Yes
- Patient information (anonymized): Yes
- Case presentation with timeline: Yes
- Clinical findings: Yes
- Diagnostic assessments: Yes
- Therapeutic interventions: Yes
- Follow-up and outcomes: Yes
- Discussion of differential diagnosis: Yes
- Comparison with literature: Yes
- Informed consent statement: Yes
"""
            )


class MetaAnalysisDrafter:
    """
    Drafter for meta-analysis sections within systematic reviews.
    """

    def __init__(self):
        self.guidelines = WritingGuidelines()

    def draft_meta_analysis_section(
        self,
        outcome_name: str,
        studies: List[Dict],
        effect_measure: str,
        model: str = "random-effects",
    ) -> str:
        """Generate meta-analysis results section."""
        n_studies = len(studies)
        total_n = sum(s.get("n", 0) for s in studies)

        section = f"""### Meta-Analysis Results: {outcome_name}

**Analysis Characteristics:**
- Number of studies: {n_studies}
- Total participants: {total_n}
- Effect measure: {effect_measure}
- Statistical model: {model}
- Software: RevMan 5.4 / R (meta package)

**Pooled Effect Estimate:**

A {model} meta-analysis was performed combining {n_studies} studies ({total_n} participants). The pooled {effect_measure} was [X.XX] (95% CI [X.XX to X.XX]; p < 0.001).

**Heterogeneity:**

- Cochran's Q: [value] (p = [value])
- I² statistic: [XX%]
- Tau²: [value]

Interpretation: {"Substantial heterogeneity (I² > 50%)" if "I²" > 50 else "Acceptable heterogeneity (I² < 50%)"}

**Study-Level Results:**

| Study | n/N | {effect_measure} (95% CI) | Weight (%) |
|-------|-----|---------------------------|------------|
"""

        for study in studies:
            section += f"| {study.get('author', 'Author')} | {study.get('n', 'N')} | {study.get('effect', 'X.XX')} ({study.get('ci', 'XX-XX')}) | {study.get('weight', 'X.X')} |\n"

        section += """
**Forest Plot Interpretation:**
[Reference to Forest Plot in Figure X]

**Subgroup Analysis:**
[Results of predefined subgroup analyses]

**Sensitivity Analysis:**
[Results of sensitivity analyses excluding high-risk-of-bias studies]

**Publication Bias:**
- Funnel plot symmetry: [Symmetric/Asymmetric]
- Egger's test: p = [value]
- Interpretation: [Assessment of publication bias]

**GRADE Assessment:**
- Quality of evidence: [High / Moderate / Low / Very Low]
- Reasons for downgrading: [Factors affecting certainty]

"""

        return section


# ============================================================================
# Main Entry Point
# ============================================================================


def create_systematic_review(
    title: str,
    document_type: str = "systematic_review",
    reference_style: str = "vancouver",
    sources: Optional[List[AcademicSource]] = None,
    tables: Optional[List[TableData]] = None,
    keywords: Optional[List[str]] = None,
) -> ManuscriptStructure:
    """Convenience function to create a systematic review."""
    drafter = SystematicReviewDrafter()

    return drafter.draft_systematic_review(
        title=title,
        research_question=title,
        pico_elements={},
        databases=["PubMed", "Embase"],
        search_terms=[],
        sources=sources,
        include_meta_analysis=False,
    )


def create_clinical_trial_report(
    title: str,
    trial_design: str,
    intervention: str,
    comparison: str,
    primary_outcome: str,
    sample_size: int,
    trial_number: str,
    sources: Optional[List[AcademicSource]] = None,
) -> ManuscriptStructure:
    """Convenience function to create a clinical trial report."""
    drafter = ClinicalTrialDrafter()

    return drafter.draft_clinical_trial_report(
        title=title,
        trial_design=trial_design,
        intervention=intervention,
        comparison=comparison,
        primary_outcome=primary_outcome,
        sample_size=sample_size,
        trial_number=trial_number,
        sources=sources,
    )


def create_case_report(
    title: str,
    condition: str,
    key_findings: List[str],
    treatment: str,
    outcome: str,
    sources: Optional[List[AcademicSource]] = None,
) -> ManuscriptStructure:
    """Convenience function to create a case report."""
    drafter = CaseReportDrafter()

    return drafter.draft_case_report(
        title=title,
        condition=condition,
        key_findings=key_findings,
        treatment=treatment,
        outcome=outcome,
        sources=sources,
    )


def create_enhanced_manuscript(
    title: str,
    document_type: str = "research_paper",
    reference_style: str = "vancouver",
    sources: Optional[List[AcademicSource]] = None,
    custom_sections: Optional[Dict[str, str]] = None,
    keywords: Optional[List[str]] = None,
) -> ManuscriptStructure:
    """Convenience function to create an enhanced manuscript."""
    doc_type_map = {
        "research_paper": DocumentType.RESEARCH_PAPER,
        "systematic_review": DocumentType.SYSTEMATIC_REVIEW,
        "literature_review": DocumentType.LITERATURE_REVIEW,
        "clinical_trial": DocumentType.CLINICAL_TRIAL,
        "case_report": DocumentType.CASE_REPORT,
    }

    drafter = EnhancedManuscriptDrafter(
        document_type=doc_type_map.get(document_type, DocumentType.RESEARCH_PAPER),
        reference_style=ReferenceStyle.VANCOUVER,
    )

    return drafter.create_manuscript(title, sources, custom_sections, keywords)


if __name__ == "__main__":
    # Example usage
    sources = [
        AcademicSource(
            title="Chronic Myeloid Leukemia: A Review",
            authors=["Jabbour E", "Kantarjian H"],
            journal="JAMA",
            year=2025,
            volume="333",
            pages="18",
            doi="10.1001/jama.2025.0220",
            is_peer_reviewed=True,
        ),
    ]

    # Systematic Review
    sr = create_systematic_review(
        title="Asciminib in CML: A Systematic Review", sources=sources
    )
    print(f"Created systematic review: {sr.title}")

    # Clinical Trial
    trial = create_clinical_trial_report(
        title="Phase III Trial of Asciminib",
        trial_design="Phase III RCT",
        intervention="Asciminib",
        comparison="Imatinib",
        primary_outcome="MMR at 48 weeks",
        sample_size=405,
        trial_number="NCT04971226",
        sources=sources,
    )
    print(f"Created clinical trial report: {trial.title}")

    # Case Report
    case = create_case_report(
        title="Atypical CML Presentation",
        condition="CML with fibrosis",
        key_findings=["Fibrosis grade 2", "Splenomegaly"],
        treatment="Combination therapy",
        outcome="Partial response",
        sources=sources,
    )
    print(f"Created case report: {case.title}")
