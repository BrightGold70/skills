"""
Manuscript Quality Analyzer for Hematology Papers
Analyzes manuscript quality across multiple categories and provides scores with recommendations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import re
import math


class QualityCategory(Enum):
    """Categories for manuscript quality assessment."""
    STRUCTURE = "structure"
    CLARITY = "clarity"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    REFERENCES = "references"
    FIGURES = "figures"
    COMPLIANCE = "compliance"


class Priority(Enum):
    """Priority levels for issues and recommendations."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class QualityScore:
    """Represents a quality score for a specific category."""
    category: QualityCategory
    score: int  # 0-100
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM


@dataclass
class QualityReport:
    """Complete quality report for a manuscript."""
    overall_score: float
    category_scores: Dict[QualityCategory, QualityScore]
    summary: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    actionable_recommendations: List[str] = field(default_factory=list)



JOURNAL_REQUIREMENTS = {
    'blood': {
        'abstract_word_limit': 250,
        'structured_abstract_required': True,
        'keywords_limit': 5,
        'text_word_limit': 6000,
        'reference_limit': 60,
        'figure_limit': 6,
        'table_limit': 6,
        'reference_style': 'Vancouver',
        'author_limit': None,
    },
    'blood_research': {
        'abstract_word_limit': 200,  # Blood Research: 200 words (Wiley)
        'structured_abstract_required': False,
        'keywords_limit': 5,
        'text_word_limit': 5000,
        'reference_limit': 50,
        'figure_limit': 6,
        'table_limit': 6,
        'reference_style': 'Vancouver',
        'author_limit': None,
    },
    'blood_advances': {
        'abstract_word_limit': 250,
        'structured_abstract_required': False,
        'keywords_limit': 5,
        'text_word_limit': 4000,
        'reference_limit': 50,
        'figure_limit': 6,
        'table_limit': 6,
        'reference_style': 'Vancouver',
        'author_limit': None,
    },
    'jco': {
        'abstract_word_limit': 250,
        'structured_abstract_required': True,
        'keywords_limit': 3,
        'text_word_limit': 3000,
        'reference_limit': 50,
        'figure_limit': 6,
        'table_limit': 4,
        'reference_style': 'Vancouver',
        'author_limit': None,
    },
    'bjh': {
        'abstract_word_limit': 200,
        'structured_abstract_required': False,
        'keywords_limit': 5,
        'text_word_limit': 4000,
        'reference_limit': 50,
        'figure_limit': 6,
        'table_limit': 6,
        'reference_style': 'Vancouver',
        'author_limit': None,
    },
    'default': {
        'abstract_word_limit': 250,
        'structured_abstract_required': False,
        'keywords_limit': 5,
        'text_word_limit': 6000,
        'reference_limit': 50,
        'figure_limit': 6,
        'table_limit': 6,
        'reference_style': 'Vancouver',
        'author_limit': None,
    }
}

class ManuscriptQualityAnalyzer:
    """
    Analyzes manuscript quality for hematology papers.
    
    Provides comprehensive analysis across structure, clarity, methods,
    results, discussion, references, figures, and compliance categories.
    """
    
    # Medical/scientific jargon terms specific to hematology
    HEMATOLOGY_JARGON = [
        'anemia', 'leukopenia', 'thrombocytopenia', 'neutropenia',
        'hemoglobin', 'hematocrit', 'leukocyte', 'thrombocyte',
        'erythrocyte', 'coagulation', 'fibrinolysis', 'hemostasis',
        'myeloid', 'lymphoid', 'megakaryocyte', 'erythropoiesis',
        'leukopoiesis', 'thrombopoiesis', 'apoptosis', 'proliferation',
        'differentiation', 'maturation', 'homeostasis', 'pathogenesis',
        'etiology', 'prognosis', 'therapeutic', 'intervention',
        'remission', 'relapse', 'refractory', 'resistant', 'sensitive',
        'transfusion', 'transplant', 'engraftment', 'chimerism',
        'chemotherapy', 'immunotherapy', 'targeted therapy', 'biomarker',
        'prognostic', 'predictive', 'survival', 'progression-free',
        'overall survival', 'response rate', 'complete response',
        'partial response', 'stable disease', 'progressive disease',
        'cytopenia', 'pancytopenia', 'hyperleukocytosis', 'leukostasis',
        'disseminated intravascular coagulation', 'DIC', 'TTP', 'HUS',
        'ITP', 'von Willebrand disease', 'hemophilia', 'coagulopathy',
        'thrombosis', 'embolism', 'anticoagulation', 'antiplatelet',
        'heparin', 'warfarin', 'DOAC', 'direct oral anticoagulant',
        'INR', 'PT', 'aPTT', 'fibrinogen', 'D-dimer', 'platelet count',
        'white blood cell count', 'red blood cell count', 'hemolysis',
        'bilirubin', 'LDH', 'haptoglobin', 'reticulocyte', 'MCV',
        'RDW', 'peripheral blood smear', 'bone marrow', 'aspirate',
        'biopsy', 'flow cytometry', 'immunophenotyping', 'cytogenetics',
        'FISH', 'PCR', 'NGS', 'next-generation sequencing', 'mutation',
        'deletion', 'amplification', 'fusion', 'translocation',
        'chromosome', 'karyotype', 'gene expression', 'transcriptome',
        'proteome', 'metabolome', 'biomarker', 'companion diagnostic',
        'precision medicine', 'personalized medicine', 'stratification',
        'risk stratification', 'staging', 'grading', 'prognostication'
    ]
    
    # Ambiguous phrases to watch for
    AMBIGUOUS_PHRASES = [
        'it is believed', 'it is thought', 'it seems', 'it appears',
        'suggests that', 'might', 'could be', 'possibly', 'perhaps',
        'we believe', 'we think', 'we feel', 'in our opinion',
        'interestingly', 'surprisingly', 'remarkably', 'notably',
        'a lot', 'many', 'several', 'some', 'various', 'numerous',
        'quite', 'rather', 'somewhat', 'fairly', 'relatively',
        'increased', 'decreased', 'elevated', 'reduced', 'altered',
        'normal', 'abnormal', 'significant', 'markedly', 'substantially'
    ]
    
    def __init__(self, target_journal: str):
        """
        Initialize the analyzer for a specific target journal.
        
        Args:
            target_journal: Name of the target journal for specialized checks
        """
        self.target_journal = target_journal
        self.journal_specific_requirements = self._load_journal_requirements()
    
    def _load_journal_requirements(self) -> Dict[str, Any]:
        """Load journal-specific formatting and content requirements."""
        journal_key = self.target_journal.lower().replace(' ', '_')
        return JOURNAL_REQUIREMENTS.get(journal_key, JOURNAL_REQUIREMENTS['default'])
    
    def analyze_manuscript(self, manuscript_path: str) -> QualityReport:
        """
        Analyze a complete manuscript and generate a quality report.
        
        Args:
            manuscript_path: Path to the manuscript file (text format)
            
        Returns:
            QualityReport with comprehensive analysis
        """
        # Read manuscript content
        with open(manuscript_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse manuscript sections (basic parsing)
        sections = self._parse_manuscript(content)
        
        # Perform category-specific checks
        category_results = {}
        
        category_results[QualityCategory.STRUCTURE] = self._check_structure(sections)
        category_results[QualityCategory.CLARITY] = self._check_clarity(content)
        category_results[QualityCategory.METHODS] = self._check_methods(
            sections.get('methods', '')
        )
        category_results[QualityCategory.RESULTS] = self._check_results(
            sections.get('results', '')
        )
        category_results[QualityCategory.DISCUSSION] = self._check_discussion(
            sections.get('discussion', '')
        )
        category_results[QualityCategory.REFERENCES] = self._check_references(
            sections.get('references', '')
        )
        category_results[QualityCategory.FIGURES] = self._check_figures(
            sections.get('figures', content)
        )
        category_results[QualityCategory.COMPLIANCE] = self._check_compliance(content)
        
        # Calculate overall score
        overall_score = self._calculate_overall(category_results)
        
        # Generate summary and recommendations
        summary, strengths, weaknesses, recommendations = self._generate_report_summary(
            category_results, overall_score
        )
        
        return QualityReport(
            overall_score=overall_score,
            category_scores=category_results,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            actionable_recommendations=recommendations
        )
    
    def _parse_manuscript(self, content: str) -> Dict[str, str]:
        """Parse manuscript into sections."""
        sections = {}
        
        # Define section markers (common in medical papers)
        section_patterns = [
            (r'(?i)(?:^|\n)\s*(?:ABSTRACT|摘要)\s*(?:\n|$)', 'abstract'),
            (r'(?i)(?:^|\n)\s*(?:INTRODUCTION|背景|前言)\s*(?:\n|$)', 'introduction'),
            (r'(?i)(?:^|\n)\s*(?:MATERIALS AND METHODS?|METHODS?|资料与方法|方法)\s*(?:\n|$)', 'methods'),
            (r'(?i)(?:^|\n)\s*(?:RESULTS?|结果)\s*(?:\n|$)', 'results'),
            (r'(?i)(?:^|\n)\s*(?:DISCUSSION?|讨论)\s*(?:\n|$)', 'discussion'),
            (r'(?i)(?:^|\n)\s*(?:CONCLUSION[S]?|结论)\s*(?:\n|$)', 'conclusions'),
            (r'(?i)(?:^|\n)\s*(?:REFERENCES?|参考文献)\s*(?:\n|$)', 'references'),
            (r'(?i)(?:^|\n)\s*(?:FIGURES?|图表)\s*(?:\n|$)', 'figures'),
            (r'(?i)(?:^|\n)\s*(?:TABLES?|表格)\s*(?:\n|$)', 'tables'),
        ]
        
        content_lower = content.lower()
        
        for pattern, section_name in section_patterns:
            match = re.search(pattern, content)
            if match:
                sections[section_name] = match.group(0)
        
        # If no sections found, treat entire content
        if not sections:
            sections['full_text'] = content
        
        return sections
    
    def _check_structure(self, sections: Dict[str, str]) -> QualityScore:
        """Check manuscript structure completeness."""
        issues = []
        recommendations = []
        score = 100
        
        required_sections = ['introduction', 'methods', 'results', 'discussion']
        recommended_sections = ['abstract', 'conclusions', 'references']
        
        missing_required = [s for s in required_sections if s not in sections]
        missing_recommended = [s for s in recommended_sections if s not in sections]
        
        for section in missing_required:
            issues.append(f"Missing required section: {section}")
            recommendations.append(f"Add a dedicated {section} section")
            score -= 15
        
        for section in missing_recommended:
            recommendations.append(f"Consider adding a {section} section for completeness")
            score -= 5
        
        # Check section order
        section_order = ['abstract', 'introduction', 'methods', 'results', 
                        'discussion', 'conclusions', 'references']
        present_sections = [s for s in section_order if s in sections]
        
        if any(present_sections[i] > present_sections[i+1] 
               for i in range(len(present_sections)-1)):
            issues.append("Sections may not be in standard order")
            recommendations.append("Follow standard IMRaD order: Introduction, Methods, Results, and Discussion")
            score -= 10
        
        priority = self._determine_priority(score)
        
        return QualityScore(
            category=QualityCategory.STRUCTURE,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            priority=priority
        )
    
    def _check_clarity(self, text: str) -> QualityScore:
        """Check writing clarity and readability."""
        issues = []
        recommendations = []
        score = 100
        
        # Calculate readability metrics
        readability = calculate_readability(text)
        
        # Check Flesch-Kincaid grade level
        fk_grade = readability['flesch_kincaid_grade']
        if fk_grade > 14:
            issues.append(f"Readability is too complex (Grade level: {fk_grade:.1f})")
            recommendations.append("Simplify sentence structure for broader readability")
            score -= 10
        elif fk_grade < 10:
            recommendations.append("Consider adding more technical depth where appropriate")
        
        # Check passive voice usage
        passive_count = count_passive_voice(text)
        passive_ratio = passive_count / max(1, len(text.split()))
        if passive_ratio > 0.25:
            issues.append(f"High passive voice usage ({passive_count} instances)")
            recommendations.append("Use active voice for clearer, more direct writing")
            score -= 10
        
        # Check for jargon
        jargon = identify_jargon(text)
        if len(jargon) > 10:
            issues.append(f"High jargon usage ({len(jargon)} terms identified)")
            recommendations.append("Define technical terms on first use for broader audience")
            score -= 5
        
        # Check for ambiguous language
        ambiguous = find_ambiguous_language(text)
        if len(ambiguous) > 5:
            issues.append(f"Found {len(ambiguous)} instances of ambiguous language")
            recommendations.append("Replace vague terms with specific, measurable descriptions")
            score -= 8
        
        priority = self._determine_priority(score)
        
        return QualityScore(
            category=QualityCategory.CLARITY,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            priority=priority
        )
    
    def _check_methods(self, methods_text: str) -> QualityScore:
        """Check methods section completeness and reproducibility."""
        issues = []
        recommendations = []
        score = 100
        
        if not methods_text:
            issues.append("Methods section is empty or missing")
            recommendations.append("Add detailed methods section for reproducibility")
            return QualityScore(
                category=QualityCategory.METHODS,
                score=0,
                issues=issues,
                recommendations=recommendations,
                priority=Priority.HIGH
            )
        
        # Check for statistical details
        if not has_statistical_details(methods_text):
            issues.append("Statistical methods not clearly described")
            recommendations.append("Describe statistical tests, software, and significance thresholds")
            score -= 15
        
        # Check for confidence intervals
        if not has_confidence_intervals(methods_text):
            recommendations.append("Include confidence intervals in statistical analysis description")
            score -= 5
        
        # Check for key methodological elements
        method_elements = {
            'study design': r'(?:prospective|retrospective|cross.?sectional|cohort|case.?control|randomized|RCT|clinical trial)',
            'sample size': r'(?:sample|cohort|participants|patients|n\s*=\s*\d+|sample size)',
            'inclusion criteria': r'(?:inclusion|eligibility|criteria)',
            'exclusion criteria': r'(?:exclusion)',
            'statistical analysis': r'(?:statistical|analysis|test|tested|regression|ANOVA|t.?test|chi.?square)',
            'software': r'(?:SPSS|SAS|R |GraphPad|SAS|Excel|software|program|version)'
        }
        
        for element, pattern in method_elements.items():
            if not re.search(pattern, methods_text.lower()):
                issues.append(f"Missing {element} description")
                recommendations.append(f"Clearly describe {element} in methods")
                score -= 8
        
        priority = self._determine_priority(score)
        
        return QualityScore(
            category=QualityCategory.METHODS,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            priority=priority
        )
    
    def _check_results(self, results_text: str) -> QualityScore:
        """Check results section for completeness and appropriate presentation."""
        issues = []
        recommendations = []
        score = 100
        
        if not results_text:
            issues.append("Results section is empty or missing")
            recommendations.append("Add results section with key findings")
            return QualityScore(
                category=QualityCategory.RESULTS,
                score=0,
                issues=issues,
                recommendations=recommendations,
                priority=Priority.HIGH
            )
        
        # Check for numerical data presentation
        number_pattern = r'\d+\.?\d*'
        if not re.search(number_pattern, results_text):
            issues.append("Limited numerical data presented")
            recommendations.append("Present specific numerical results with statistics")
            score -= 15
        
        # Check for p-values
        if not re.search(r'p\s*[=<>]\s*[\d.]+', results_text.lower()):
            issues.append("Statistical significance (p-values) not reported")
            recommendations.append("Report p-values for all comparisons")
            score -= 12
        
        # Check for effect sizes
        effect_patterns = r'(?:effect size|Cohen|d|η²|eta|odds ratio|hazard|relative risk|95% CI)'
        if not re.search(effect_patterns, results_text.lower()):
            recommendations.append("Consider reporting effect sizes and confidence intervals")
            score -= 5
        
        # Check for figure/table references
        if not re.search(r'(?:Figure|Fig\.|Table)\s*\d+', results_text):
            recommendations.append("Reference figures and tables in results text")
            score -= 5
        
        priority = self._determine_priority(score)
        
        return QualityScore(
            category=QualityCategory.RESULTS,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            priority=priority
        )
    
    def _check_discussion(self, discussion_text: str) -> QualityScore:
        """Check discussion section quality."""
        issues = []
        recommendations = []
        score = 100
        
        if not discussion_text:
            issues.append("Discussion section is empty or missing")
            recommendations.append("Add discussion section for interpretation")
            return QualityScore(
                category=QualityCategory.DISCUSSION,
                score=0,
                issues=issues,
                recommendations=recommendations,
                priority=Priority.HIGH
            )
        
        # Check for limitations
        limitation_patterns = r'(?:limitation|limitations|caveat|caveats|drawback)'
        if not re.search(limitation_patterns, discussion_text.lower()):
            issues.append("Study limitations not discussed")
            recommendations.append("Discuss limitations of the study")
            score -= 15
        
        # Check for comparison with literature
        comparison_patterns = r'(?:consistent with|contrast|unlike|compared|previous|prior|other studies|similar)'
        if not re.search(comparison_patterns, discussion_text.lower()):
            issues.append("Limited comparison with existing literature")
            recommendations.append("Compare findings with relevant studies")
            score -= 10
        
        # Check for future directions
        future_patterns = r'(?:future|future directions|future research|future studies|speculate|speculation)'
        if not re.search(future_patterns, discussion_text.lower()):
            recommendations.append("Suggest directions for future research")
            score -= 8
        
        # Check for clinical implications
        implication_patterns = r'(?:implication|clinical implication|practical|translation|relevance)'
        if not re.search(implication_patterns, discussion_text.lower()):
            recommendations.append("Discuss clinical and research implications")
            score -= 5
        
        priority = self._determine_priority(score)
        
        return QualityScore(
            category=QualityCategory.DISCUSSION,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            priority=priority
        )
    
    def _check_references(self, references_text: str) -> QualityScore:
        """Check references section."""
        issues = []
        recommendations = []
        score = 100
        
        # Basic reference counting
        ref_count = len(re.findall(r'\[\d+\]|\(\d{4}\)|^\d+\.', references_text))
        
        if ref_count < 20:
            issues.append(f"Few references ({ref_count}) for a research paper")
            recommendations.append("Add more relevant citations to support claims")
            score -= 10
        elif ref_count > 100:
            recommendations.append("Consider if all references are essential")
        
        # Check reference format patterns
        doi_pattern = r'doi:\s*\d+\.\d+'
        if not re.search(doi_pattern, references_text.lower()):
            recommendations.append("Include DOIs for references where available")
        
        # Check for recent references (last 5 years)
        current_year = 2026
        recent_pattern = r'\(20[12]\d\)'
        recent_refs = len(re.findall(recent_pattern, references_text))
        if recent_refs < 5:
            recommendations.append("Consider adding more recent references (last 5 years)")
        
        priority = self._determine_priority(score)
        
        return QualityScore(
            category=QualityCategory.REFERENCES,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            priority=priority
        )
    
    def _check_figures(self, text: str) -> QualityScore:
        """Check figure and table presentation."""
        issues = []
        recommendations = []
        score = 100
        
        # Count figure references
        fig_count = len(re.findall(r'(?:Figure|Fig\.)\s*\d+', text, re.IGNORECASE))
        table_count = len(re.findall(r'(?:Table)\s*\d+', text, re.IGNORECASE))
        
        max_figs = self.journal_specific_requirements.get('figure_limit', 6)
        max_tables = self.journal_specific_requirements.get('table_limit', 6)
        
        if fig_count > max_figs:
            issues.append(f"Too many figures ({fig_count}, limit: {max_figs})")
            recommendations.append("Consolidate figures or move some to supplementary material")
            score -= 10
        
        if table_count > max_tables:
            issues.append(f"Too many tables ({table_count}, limit: {max_tables})")
            recommendations.append("Consolidate tables or move some to supplementary material")
            score -= 10
        
        if fig_count == 0:
            recommendations.append("Include figures to illustrate key findings")
            score -= 10
        
        if table_count == 0:
            recommendations.append("Consider adding tables for detailed data presentation")
            score -= 5
        
        priority = self._determine_priority(score)
        
        return QualityScore(
            category=QualityCategory.FIGURES,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            priority=priority
        )
    
    def _check_compliance(self, text: str) -> QualityScore:
        """Check for ethical compliance and reporting standards."""
        issues = []
        recommendations = []
        score = 100
        
        # Check for ethical statements
        ethics_patterns = {
            'IRB': r'(?:IRB|Institutional Review Board|Ethics Committee|Ethics Board|approval number|approved by)',
            'Informed Consent': r'(?:informed consent|consent|participation consent)',
            'Declaration of Interest': r'(?:conflict of interest|COI|Declaration of Interest|disclosure)',
            'Funding': r'(?:funding|supported by|grant|financial support)',
            'Trial Registration': r'(?:clinicaltrials\.gov|ISRCTN|UMIN|registry|registration number)'
        }
        
        for name, pattern in ethics_patterns.items():
            if not re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Missing {name} statement")
                recommendations.append(f"Include {name} information")
                score -= 12
        
        # Check for adherence to reporting guidelines
        guidelines = r'(?:STROBE|CONSORT|PRISMA|STARD|CARE)'
        if not re.search(guidelines, text, re.IGNORECASE):
            recommendations.append("Consider following relevant reporting guidelines (STROBE, CONSORT, PRISMA)")
        
        priority = self._determine_priority(score)
        
        return QualityScore(
            category=QualityCategory.COMPLIANCE,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            priority=priority
        )
    
    def _calculate_overall(self, results: Dict[QualityCategory, QualityScore]) -> float:
        """Calculate weighted overall quality score."""
        weights = {
            QualityCategory.STRUCTURE: 0.15,
            QualityCategory.CLARITY: 0.15,
            QualityCategory.METHODS: 0.20,
            QualityCategory.RESULTS: 0.20,
            QualityCategory.DISCUSSION: 0.10,
            QualityCategory.REFERENCES: 0.08,
            QualityCategory.FIGURES: 0.07,
            QualityCategory.COMPLIANCE: 0.05
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for category, score in results.items():
            weight = weights.get(category, 0.05)
            weighted_sum += score.score * weight
            total_weight += weight
        
        # Normalize to 0-100 scale
        return (weighted_sum / total_weight) if total_weight > 0 else 0.0
    
    def _determine_priority(self, score: int) -> Priority:
        """Determine priority level based on score."""
        if score < 50:
            return Priority.HIGH
        elif score < 75:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _generate_report_summary(
        self,
        results: Dict[QualityCategory, QualityScore],
        overall_score: float
    ) -> tuple:
        """Generate summary, strengths, weaknesses, and recommendations."""
        strengths = []
        weaknesses = []
        recommendations = []
        
        # Identify strengths and weaknesses
        for category, score in results.items():
            if score.score >= 80:
                strengths.append(f"{category.value.title()}: {score.score:.0f}%")
            elif score.score < 60:
                weaknesses.append(f"{category.value.title()}: {score.score:.0f}%")
        
        # Collect top recommendations
        for category, score in results.items():
            if score.score < 80:
                for rec in score.recommendations[:2]:
                    recommendations.append(f"[{category.value.title()}] {rec}")
        
        # Generate summary text
        if overall_score >= 80:
            summary = "Manuscript demonstrates good overall quality with minor areas for improvement."
        elif overall_score >= 60:
            summary = "Manuscript shows acceptable quality but requires revisions in several areas."
        else:
            summary = "Manuscript needs significant improvements across multiple categories."
        
        return summary, strengths, weaknesses, recommendations


# ============== Helper Functions ==============

def calculate_readability(text: str) -> Dict[str, float]:
    """
    Calculate readability metrics for text.
    
    Returns dict with:
        - flesch_kincaid_grade: Grade level equivalent
        - flesch_reading_ease: Reading ease score (0-100)
        - avg_sentence_length: Average words per sentence
        - avg_syllables_per_word: Average syllables per word
    """
    if not text or not text.strip():
        return {
            'flesch_kincaid_grade': 0.0,
            'flesch_reading_ease': 0.0,
            'avg_sentence_length': 0.0,
            'avg_syllables_per_word': 0.0
        }
    
    # Clean text
    clean_text = re.sub(r'[^\w\s]', ' ', text)
    words = [w for w in clean_text.split() if w]
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not words or not sentences:
        return {
            'flesch_kincaid_grade': 0.0,
            'flesch_reading_ease': 0.0,
            'avg_sentence_length': 0.0,
            'avg_syllables_per_word': 0.0
        }
    
    num_words = len(words)
    num_sentences = len(sentences)
    num_syllables = sum(count_syllables(word) for word in words)
    
    # Flesch Reading Ease
    avg_sentence_len = num_words / num_sentences
    avg_syllables_per_word = num_syllables / num_words
    
    flesch_reading_ease = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables_per_word)
    flesch_reading_ease = max(0, min(100, flesch_reading_ease))
    
    # Flesch-Kincaid Grade Level
    flesch_kincaid_grade = (0.39 * avg_sentence_len) + (11.8 * avg_syllables_per_word) - 15.59
    flesch_kincaid_grade = max(0, flesch_kincaid_grade)
    
    return {
        'flesch_kincaid_grade': round(flesch_kincaid_grade, 2),
        'flesch_reading_ease': round(flesch_reading_ease, 2),
        'avg_sentence_length': round(avg_sentence_len, 2),
        'avg_syllables_per_word': round(avg_syllables_per_word, 2)
    }


def count_syllables(word: str) -> int:
    """Count syllables in a word."""
    word = word.lower()
    if len(word) <= 3:
        return 1
    
    count = 0
    vowels = 'aeiouy'
    prev_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    
    # Adjust for silent e
    if word.endswith('e') and count > 1:
        count -= 1
    
    # Adjust for -le endings
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        count += 1
    
    return max(1, count)


def count_passive_voice(text: str) -> int:
    """
    Count instances of passive voice in text.
    
    Identifies common passive voice patterns:
    - "be" verb forms + past participle
    """
    passive_patterns = [
        r'\b(?:is|are|was|were|be|been|being)\s+\w+ed\b',
        r'\b(?:is|are|was|were|be|been|being)\s+\w+en\b',
        r'\b(?:is|are|was|were|be|been|being)\s+\w+ne\b'
    ]
    
    count = 0
    for pattern in passive_patterns:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    
    return count


def identify_jargon(text: str) -> List[str]:
    """
    Identify potential jargon or technical terms in text.
    
    Returns list of jargon terms found.
    """
    jargon_list = ManuscriptQualityAnalyzer.HEMATOLOGY_JARGON
    text_lower = text.lower()
    
    found_jargon = []
    for term in jargon_list:
        # Match whole words only
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_jargon.append(term)
    
    return found_jargon


def find_ambiguous_language(text: str) -> List[str]:
    """
    Find instances of ambiguous or vague language in text.
    
    Returns list of ambiguous phrases found.
    """
    ambiguous_list = ManuscriptQualityAnalyzer.AMBIGUOUS_PHRASES
    text_lower = text.lower()
    
    found_ambiguous = []
    for phrase in ambiguous_list:
        if phrase.lower() in text_lower:
            found_ambiguous.append(phrase)
    
    return found_ambiguous


def has_statistical_details(text: str) -> bool:
    """
    Check if text contains statistical methodology details.
    
    Returns True if statistical details are present.
    """
    stats_indicators = [
        r'(?:statistical|statistics|statistically)',
        r'(?:test|tested|testing)',
        r'(?:p\s*[=<>]\s*[\d.]+)',
        r'(?:analysis|analyses|analyzed)',
        r'(?:significant|significance)',
        r'(?:regression|ANOVA|t.?test|chi.?square|correlation)',
        r'(?:mean|median|mode|standard deviation|SD|IQR)',
        r'(?:confidence interval|CI)',
        r'(?:multivariate|univariate|bivariate)',
        r'(?:SPSS|SAS|R |GraphPad|STATA)'
    ]
    
    for indicator in stats_indicators:
        if re.search(indicator, text, re.IGNORECASE):
            return True
    
    return False


def has_confidence_intervals(text: str) -> bool:
    """
    Check if text mentions confidence intervals.
    
    Returns True if confidence intervals are mentioned.
    """
    ci_patterns = [
        r'confidence interval',
        r'95%\s*CI',
        r'95%\s*confidence',
        r'CI\s*\d+',
        r'\[\d+\s*,\s*\d+\]',  # Numeric CI notation
        r'\(\d+\s*-\s*\d+\)'   # Range notation
    ]
    
    for pattern in ci_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


if __name__ == "__main__":
    # Example usage
    analyzer = ManuscriptQualityAnalyzer("Blood")
    
    # Test with a sample manuscript path
    import sys
    if len(sys.argv) > 1:
        report = analyzer.analyze_manuscript(sys.argv[1])
        print(f"Overall Score: {report.overall_score:.1f}%")
        print(f"Summary: {report.summary}")
        print("\nCategory Scores:")
        for category, score in report.category_scores.items():
            print(f"  {category.value}: {score.score:.0f}% ({score.priority.value})")
