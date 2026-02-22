"""
Content Enhancer for Hematology Manuscripts
Identifies content gaps and provides suggestions for manuscript improvement.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import json
import re


class ContentType(Enum):
    """Types of content gaps that can be identified."""
    METHODS_DETAIL = "methods_detail"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    RESULTS_INTERPRETATION = "results_interpretation"
    COMPARISON_LITERATURE = "comparison_literature"
    LIMITATIONS = "limitations"
    FUTURE_DIRECTIONS = "future_directions"
    CLINICAL_IMPLICATIONS = "clinical_implications"
    BACKGROUND_CONTEXT = "background_context"
    DEFINITION_TERMS = "definition_terms"
    ETHICAL_STATEMENT = "ethical_statement"
    FUNDING_DISCLOSURE = "funding_disclosure"


class SuggestionType(Enum):
    """Types of suggestions for content additions."""
    ADD_SECTION = "add_section"
    EXPAND_EXISTING = "expand_existing"
    REVISE_TEXT = "revise_text"
    ADD_REFERENCE = "add_reference"
    DEFINE_TERM = "define_term"
    ADD_STATISTIC = "add_statistic"
    ADD_FIGURE = "add_figure"
    ADD_TABLE = "add_table"


class Priority(Enum):
    """Priority levels for suggestions."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Effort(Enum):
    """Effort levels required to implement suggestions."""
    MINOR = "minor"      # Quick fix
    MODERATE = "moderate"  # Some work needed
    MAJOR = "major"        # Significant revision


@dataclass
class ContentGap:
    """Represents a gap in manuscript content."""
    type: ContentType
    topic: str
    prompt: str
    references_needed: List[str] = field(default_factory=list)


@dataclass
class Suggestion:
    """Represents a suggestion for manuscript improvement."""
    type: SuggestionType
    topic: str
    reason: str
    priority: Priority
    effort: Effort
    suggested_text: Optional[str] = None
    location_hint: Optional[str] = None


@dataclass
class Revision:
    """Represents a single revision made to the manuscript."""
    change_type: str
    location: str
    original_text: str
    new_text: str
    reason: str
    timestamp: str
    tracked: bool = True


@dataclass
class ManuscriptRevisor:
    """Manages revisions to a manuscript with tracking capabilities."""
    manuscript_path: str
    revisions: List[Revision] = field(default_factory=list)
    versions: Dict[str, str] = field(default_factory=dict)
    
    def __init__(self, manuscript_path: str):
        """
        Initialize the revisor with a manuscript path.
        
        Args:
            manuscript_path: Path to the manuscript file
        """
        self.manuscript_path = manuscript_path
        self.revisions = []
        self.versions = {}
        
        # Save initial version
        try:
            with open(manuscript_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.versions['initial'] = content
        except FileNotFoundError:
            self.versions['initial'] = ""
    
    def make_change(
        self,
        change_type: str,
        location: str,
        original_text: str,
        new_text: str,
        reason: str,
        track_changes: bool = True
    ) -> Revision:
        """
        Create a tracked revision to the manuscript.
        
        Args:
            change_type: Type of change (add, delete, replace, etc.)
            location: Where in the manuscript this change applies
            original_text: Text being replaced (empty for additions)
            new_text: New text to insert (empty for deletions)
            reason: Reason for this change
            track_changes: Whether to track this revision
            
        Returns:
            Revision object with change details
        """
        revision = Revision(
            change_type=change_type,
            location=location,
            original_text=original_text,
            new_text=new_text,
            reason=reason,
            timestamp=datetime.now().isoformat(),
            tracked=track_changes
        )
        
        self.revisions.append(revision)
        return revision
    
    def apply_revisions(
        self,
        revisions: List[Revision],
        output_path: str,
        track_changes: bool = True
    ) -> str:
        """
        Apply a list of revisions to the manuscript.
        
        Args:
            revisions: List of Revision objects to apply
            output_path: Path for the revised manuscript
            track_changes: Whether to track changes in output
            
        Returns:
            Path to the revised manuscript
        """
        # Load current content
        try:
            with open(self.manuscript_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            content = ""
        
        # Apply revisions in order (simple text replacement for now)
        for rev in revisions:
            if rev.change_type == 'replace':
                content = content.replace(rev.original_text, rev.new_text)
            elif rev.change_type == 'add':
                content = content + "\n" + rev.new_text
            elif rev.change_type == 'delete':
                content = content.replace(rev.original_text, "")
            elif rev.change_type == 'insert_after':
                content = content.replace(
                    rev.original_text,
                    rev.original_text + "\n\n" + rev.new_text
                )
            
            # Track applied revision
            if track_changes:
                self.revisions.append(rev)
        
        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save version
        version_key = f"revised_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.versions[version_key] = content
        
        return output_path
    
    def generate_revision_summary(self) -> str:
        """
        Generate a summary of all revisions made.
        
        Returns:
            Summary string of revisions
        """
        if not self.revisions:
            return "No revisions have been made."
        
        summary_lines = [
            f"Revision Summary ({len(self.revisions)} revisions)",
            "=" * 50
        ]
        
        # Group by change type
        by_type: Dict[str, List[Revision]] = {}
        for rev in self.revisions:
            by_type.setdefault(rev.change_type, []).append(rev)
        
        for change_type, revs in by_type.items():
            summary_lines.append(f"\n{change_type.upper()} ({len(revs)} changes):")
            for rev in revs:
                summary_lines.append(f"  - {rev.reason}")
                if rev.location:
                    summary_lines.append(f"    Location: {rev.location}")
        
        # Priority breakdown
        priority_counts: Dict[str, int] = {}
        for rev in self.revisions:
            priority_counts[rev.change_type] = priority_counts.get(rev.change_type, 0) + 1
        
        summary_lines.append("\n" + "=" * 50)
        summary_lines.append("By Priority:")
        for ptype, count in priority_counts.items():
            summary_lines.append(f"  {ptype}: {count}")
        
        return "\n".join(summary_lines)
    
    def revert_to_version(self, version: str) -> str:
        """
        Revert manuscript to a previous version.
        
        Args:
            version: Version key to revert to
            
        Returns:
            Reverted content
        """
        if version not in self.versions:
            raise ValueError(f"Version '{version}' not found. Available: {list(self.versions.keys())}")
        
        content = self.versions[version]
        
        # Create a new file with reverted content
        output_path = self.manuscript_path.replace(
            '.txt', 
            f'_reverted_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Track the revert as a revision
        self.revisions.append(Revision(
            change_type='revert',
            location='entire document',
            original_text='current version',
            new_text=version,
            reason=f"Reverted to version: {version}",
            timestamp=datetime.now().isoformat(),
            tracked=True
        ))
        
        return output_path


class ContentEnhancer:
    """
    Identifies content gaps in hematology manuscripts and suggests improvements.
    """
    
    # Reference templates for common hematology topics
    REFERENCE_TEMPLATES = {
        'anemia': [
            "Hoffbrand AV, et al. Essential Haematology. 7th ed. Wiley; 2019.",
            "Cappellini MD, et al. Iron deficiency anemia. N Engl J Med. 2020;382(19):1838-1848."
        ],
        'coagulation': [
            "Hoffman M, Monroe DM. Coagulation 2006: a view from the bedside. J Thromb Haemost. 2006;4(5):1021-1026.",
            "Tripodi A, Mannucci PM. The coagulopathy of chronic liver disease. N Engl J Med. 2011;365(2):147-156."
        ],
        'leukemia': [
            "Döhner H, et al. Acute myeloid leukemia. N Engl J Med. 2020;383(3):234-249.",
            "Arber DA, et al. The 2016 revision to the WHO classification of myeloid neoplasms and acute leukemia. Blood. 2016;127(20):2391-2405."
        ],
        'lymphoma': [
            "Swerdlow SH, et al. WHO Classification of Tumours of Haematopoietic and Lymphoid Tissues. 4th ed. IARC; 2017.",
            "Cheson BD, et al. Recommendations for initial evaluation, staging, and response assessment of Hodgkin and non-Hodgkin lymphoma. J Clin Oncol. 2014;32(27):3059-3068."
        ],
        'stem_cell_transplant': [
            "Copelan EA. Hematopoietic stem-cell transplantation. N Engl J Med. 2006;354(17):1813-1826.",
            "Majhail NS, et al. Indications for hematopoietic stem cell transplantation. Biol Blood Marrow Transplant. 2015;21(3):402-409."
        ],
        'statistics': [
            "Vandenbroucke JP, et al. Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement. BMJ. 2007;335(7624):806-808.",
            "Schulz KF, et al. CONSORT 2010 explanation and elaboration. BMJ. 2010;340:c869."
        ]
    }
    
    # Templates for common content additions
    CONTENT_TEMPLATES = {
        ContentType.STATISTICAL_ANALYSIS: {
            'template': (
                "Statistical Analysis\n"
                "Statistical analysis was performed using {software} "
                "({version}, {manufacturer}). Data distribution was assessed "
                "using the Shapiro-Wilk test. Continuous variables were compared "
                "using {tests}. Categorical variables were compared using "
                "{tests_cat}. A p-value <0.05 was considered statistically significant. "
                "Confidence intervals were calculated at the 95% level."
            ),
            'fillers': {
                'software': ['R version 4.0+', 'SPSS Statistics', 'SAS 9.4', 'GraphPad Prism 9'],
                'tests': ["Student's t-test", 'Mann-Whitney U test', 'ANOVA', 'Kruskal-Wallis test'],
                'tests_cat': ["chi-square test", "Fisher's exact test"]
            }
        },
        ContentType.LIMITATIONS: {
            'template': (
                "This study has several limitations that should be considered when "
                "interpreting the results. First, {limitation_1}. Second, {limitation_2}. "
                "Third, {limitation_3}. These limitations may affect the generalizability "
                "of our findings and should be addressed in future studies."
            ),
            'fillers': {
                'limitation_1': ['the sample size was relatively small',
                                 'this was a single-center study',
                                 'data collection was retrospective'],
                'limitation_2': ['selection bias cannot be excluded',
                                 'unmeasured confounders may exist',
                                 'follow-up duration was limited'],
                'limitation_3': ['some clinical data were incomplete',
                                 'the control group was not matched',
                                 'we did not perform validation cohorts']
            }
        },
        ContentType.FUTURE_DIRECTIONS: {
            'template': (
                "Future studies should address the limitations identified in this work. "
                "Prospective, multi-center studies with larger sample sizes are needed "
                "to validate our findings. {specific_direction}. Additionally, "
                "{another_direction} would provide valuable insights into "
                "{clinical_relevance}."
            ),
            'fillers': {
                'specific_direction': ['mechanistic studies exploring the underlying pathways',
                                       'longitudinal studies examining long-term outcomes',
                                       'randomized controlled trials'],
                'another_direction': ['biomarker validation studies',
                                      'cost-effectiveness analyses',
                                      'comparative effectiveness research'],
                'clinical_relevance': ['patient outcomes',
                                       'treatment decision-making',
                                       'clinical practice guidelines']
            }
        },
        ContentType.CLINICAL_IMPLICATIONS: {
            'template': (
                "The findings of this study have important implications for clinical practice. "
                "{implication_1}. Clinicians should {clinical_recommendation}. "
                "Furthermore, {implication_2}. These considerations should be weighed "
                "when making treatment decisions for {patient_population}."
            ),
            'fillers': {
                'implication_1': ['Our data suggest that {intervention} may be beneficial',
                                 'The identified risk factors could inform risk stratification',
                                 'Early detection of {finding} may improve outcomes'],
                'clinical_recommendation': ['consider {intervention} in eligible patients',
                                             'implement screening protocols',
                                             'discuss prognostic implications with patients'],
                'implication_2': ['healthcare systems should allocate resources accordingly',
                                  'policy makers should consider these findings',
                                  'further research is warranted'],
                'patient_population': ['patients with similar characteristics',
                                       'high-risk individuals',
                                       'the broader hematology patient population']
            }
        },
        ContentType.BACKGROUND_CONTEXT: {
            'template': (
                "{condition} is a significant hematologic disorder characterized by "
                "{characteristics}. It affects approximately {prevalence} and is associated "
                "with {morbidity}. The pathophysiology involves {pathophysiology}, "
                "leading to {clinical_consequences}. Despite advances in treatment, "
                "{unmet_need}, highlighting the importance of this study."
            ),
            'fillers': {
                'condition': ['Anemia of chronic disease', 'Myelodysplastic syndrome',
                              'Immune thrombocytopenia', 'Chronic lymphocytic leukemia'],
                'characteristics': ['abnormal blood cell production',
                                     'impaired hematopoietic function',
                                     'immune dysregulation'],
                'prevalence': ['1-2% of the general population',
                               'an estimated 60,000 new cases annually in the US',
                               'increasing incidence with age'],
                'morbidity': ['significant morbidity and mortality',
                              'reduced quality of life',
                              'substantial healthcare burden'],
                'pathophysiology': ['dysregulated iron metabolism',
                                    'clonal hematopoietic stem cell disorders',
                                    'autoimmune-mediated platelet destruction'],
                'clinical_consequences': ['fatigue, weakness, and exercise intolerance',
                                           'increased bleeding risk',
                                           'susceptibility to infections'],
                'unmet_need': ['treatment options remain limited',
                              'many patients develop refractory disease',
                              'prognosis has not substantially improved']
            }
        }
    }
    
    def __init__(self):
        """Initialize the content enhancer."""
        pass
    
    def identify_content_gaps(
        self,
        manuscript: str,
        quality_report: Any
    ) -> List[ContentGap]:
        """
        Identify content gaps in the manuscript based on quality analysis.
        
        Args:
            manuscript: The manuscript text
            quality_report: QualityReport from ManuscriptQualityAnalyzer
            
        Returns:
            List of identified content gaps
        """
        gaps = []
        
        # Analyze quality report for gaps
        for category, score in quality_report.category_scores.items():
            for issue in score.issues:
                gap = self._map_issue_to_gap(issue, category, manuscript)
                if gap:
                    gaps.append(gap)
        
        return gaps
    
    def _map_issue_to_gap(
        self,
        issue: str,
        category: Any,
        manuscript: str
    ) -> Optional[ContentGap]:
        """
        Map a quality issue to a content gap.
        
        Args:
            issue: The quality issue text
            category: The quality category
            manuscript: The manuscript text
            
        Returns:
            ContentGap if identified, None otherwise
        """
        issue_lower = issue.lower()
        
        # Map issues to content types
        if 'statistic' in issue_lower or 'p-value' in issue_lower:
            return ContentGap(
                type=ContentType.STATISTICAL_ANALYSIS,
                topic="Statistical Analysis",
                prompt="Add detailed statistical methodology including tests used, "
                        "software versions, and significance thresholds.",
                references_needed=['statistics']
            )
        
        if 'limitation' in issue_lower:
            return ContentGap(
                type=ContentType.LIMITATIONS,
                topic="Study Limitations",
                prompt="Discuss the limitations of your study, including sample size, "
                        "study design constraints, and potential biases.",
                references_needed=[]
            )
        
        if 'literature' in issue_lower or 'compare' in issue_lower:
            return ContentGap(
                type=ContentType.COMPARISON_LITERATURE,
                topic="Literature Comparison",
                prompt="Compare your findings with existing literature and discuss "
                        "similarities, differences, and potential explanations.",
                references_needed=[]
            )
        
        if 'future' in issue_lower or 'research' in issue_lower:
            return ContentGap(
                type=ContentType.FUTURE_DIRECTIONS,
                topic="Future Research Directions",
                prompt="Suggest directions for future research based on your findings "
                        "and limitations.",
                references_needed=[]
            )
        
        if 'implication' in issue_lower or 'clinical' in issue_lower:
            return ContentGap(
                type=ContentType.CLINICAL_IMPLICATIONS,
                topic="Clinical Implications",
                prompt="Discuss the clinical and practical implications of your findings.",
                references_needed=[]
            )
        
        if 'method' in issue_lower or 'sample' in issue_lower:
            return ContentGap(
                type=ContentType.METHODS_DETAIL,
                topic="Methods Detail",
                prompt="Provide more detailed methodology for reproducibility.",
                references_needed=[]
            )
        
        if 'introduction' in issue_lower or 'background' in issue_lower:
            return ContentGap(
                topic="Background Context",
                prompt="Expand the background section with more context about the condition.",
                type=ContentType.BACKGROUND_CONTEXT,
                references_needed=[]
            )
        
        if 'ethical' in issue_lower or 'irb' in issue_lower:
            return ContentGap(
                type=ContentType.ETHICAL_STATEMENT,
                topic="Ethical Statement",
                prompt="Add IRB approval statement and ethical compliance information.",
                references_needed=[]
            )
        
        if 'funding' in issue_lower:
            return ContentGap(
                type=ContentType.FUNDING_DISCLOSURE,
                topic="Funding Disclosure",
                prompt="Add funding source declarations and grant information.",
                references_needed=[]
            )
        
        return None
    
    def generate_content(self, gap: ContentGap, context: str = "") -> str:
        """
        Generate content to fill a specific gap.
        
        Args:
            gap: The content gap to fill
            context: Optional context from surrounding text
            
        Returns:
            Generated content string
        """
        if gap.type in self.CONTENT_TEMPLATES:
            template_info = self.CONTENT_TEMPLATES[gap.type]
            template = template_info['template']
            fillers = template_info['fillers']
            
            # Select random filler options for variety
            import random
            filled_template = template
            
            for key, options in fillers.items():
                if key in filled_template:
                    choice = random.choice(options) if options else ""
                    filled_template = filled_template.replace(
                        "{" + key + "}",
                        choice
                    )
            
            return filled_template
        
        # Generic templates for types without specific templates
        generic_templates = {
            ContentType.RESULTS_INTERPRETATION: (
                "The observed {finding} suggests that {interpretation}. "
                "This finding has {significance} and may impact {impact_area}."
            ),
            ContentType.DEFINITION_TERMS: (
                "{term} is defined as {definition}. This is relevant because {relevance}."
            ),
            ContentType.ETHICAL_STATEMENT: (
                "This study was approved by the Institutional Review Board "
                "(IRB) [Approval Number: XXXXX]. All patients provided "
                "written informed consent. The study was conducted in accordance "
                "with the Declaration of Helsinki."
            ),
            ContentType.FUNDING_DISCLOSURE: (
                "This work was supported by [Grant Number] from [Funding Agency]. "
                "The funder had no role in study design, data collection, analysis, "
                "interpretation, or manuscript preparation."
            )
        }
        
        if gap.type in generic_templates:
            return generic_templates[gap.type]
        
        return ""
    
    def suggest_content_additions(self, manuscript_path: str) -> List[Suggestion]:
        """
        Analyze manuscript and suggest content additions.
        
        Args:
            manuscript_path: Path to the manuscript file
            
        Returns:
            List of suggestions for content additions
        """
        suggestions = []
        
        # Read manuscript
        try:
            with open(manuscript_path, 'r', encoding='utf-8') as f:
                manuscript = f.read()
        except FileNotFoundError:
            return suggestions
        
        # Analyze manuscript structure
        sections = self._parse_sections(manuscript)
        
        # Check each section for gaps
        if 'introduction' in sections:
            intro_suggestions = self._check_intro_gaps(sections['introduction'])
            suggestions.extend(intro_suggestions)
        
        if 'methods' in sections:
            methods_suggestions = self._check_methods_gaps(sections['methods'])
            suggestions.extend(methods_suggestions)
        
        if 'results' in sections:
            results_suggestions = self._check_results_gaps(sections['results'])
            suggestions.extend(results_suggestions)
        
        if 'discussion' in sections:
            discussion_suggestions = self._check_discussion_gaps(sections['discussion'])
            suggestions.extend(discussion_suggestions)
        
        return suggestions
    
    def _parse_sections(self, manuscript: str) -> Dict[str, str]:
        """Parse manuscript into sections."""
        sections = {}
        
        section_patterns = [
            # Support both plain text and markdown headers (## Title or just TITLE)
            (r'(?i)(?:^|\n)(?:#+\s*)?(?:ABSTRACT)(?:\s*:?\s*\n|$)', 'abstract'),
            (r'(?i)(?:^|\n)(?:#+\s*)?(?:INTRODUCTION)(?:\s*:?\s*\n|$)', 'introduction'),
            (r'(?i)(?:^|\n)(?:#+\s*)?(?:MATERIALS AND METHODS?|METHODS?)(?:\s*:?\s*\n|$)', 'methods'),
            (r'(?i)(?:^|\n)(?:#+\s*)?(?:RESULTS?)(?:\s*:?\s*\n|$)', 'results'),
            (r'(?i)(?:^|\n)(?:#+\s*)?(?:DISCUSSION)(?:\s*:?\s*\n|$)', 'discussion'),
            (r'(?i)(?:^|\n)(?:#+\s*)?(?:CONCLUSION[S]?)(?:\s*:?\s*\n|$)', 'conclusions'),
            (r'(?i)(?:^|\n)(?:#+\s*)?(?:REFERENCES|Citations)(?:\s*:?\s*\n|$)', 'references'),
        ]
        
        for pattern, name in section_patterns:
            match = re.search(pattern, manuscript)
            if match:
                sections[name] = match.group(0)
        
        return sections
    
    def _check_intro_gaps(self, intro: str) -> List[Suggestion]:
        """Check introduction for content gaps."""
        suggestions = []
        
        # Check for disease prevalence
        if not re.search(r'\d+\s*%|\d+\s*per\s*\d+|million|thousand', intro.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.EXPAND_EXISTING,
                topic="Prevalence Data",
                reason="Introduction lacks specific prevalence/incidence data",
                priority=Priority.MEDIUM,
                effort=Effort.MINOR,
                location_hint="Introduction"
            ))
        
        # Check for gap statement
        if not re.search(r'however|nevertheless|nonetheless|remains|unclear', intro.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.EXPAND_EXISTING,
                topic="Research Gap Statement",
                reason="Introduction should clearly state the gap in current knowledge",
                priority=Priority.HIGH,
                effort=Effort.MINOR,
                location_hint="End of Introduction"
            ))
        
        # Check for study objective
        if not re.search(r'(?:aim|purpose|objective|goal)\s*(?:of|was|is|were)', intro.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.ADD_SECTION,
                topic="Study Objective",
                reason="Clear study objective/aim should be stated",
                priority=Priority.HIGH,
                effort=Effort.MINOR,
                location_hint="End of Introduction"
            ))
        
        return suggestions
    
    def _check_methods_gaps(self, methods: str) -> List[Suggestion]:
        """Check methods for content gaps."""
        suggestions = []
        
        # Check for statistics
        if not re.search(r'(?:statistical|analysis|test|SPSS|R\s*version|SAS|GraphPad)', methods.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.ADD_SECTION,
                topic="Statistical Analysis",
                reason="Methods should describe statistical tests and software used",
                priority=Priority.HIGH,
                effort=Effort.MODERATE,
                location_hint="Methods"
            ))
        
        # Check for inclusion criteria
        if not re.search(r'(?:inclusion|criteria|eligible)', methods.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.ADD_SECTION,
                topic="Inclusion Criteria",
                reason="Methods should specify inclusion criteria",
                priority=Priority.HIGH,
                effort=Effort.MODERATE,
                location_hint="Methods"
            ))
        
        # Check for exclusion criteria
        if not re.search(r'(?:exclusion)', methods.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.ADD_SECTION,
                topic="Exclusion Criteria",
                reason="Methods should specify exclusion criteria",
                priority=Priority.HIGH,
                effort=Effort.MODERATE,
                location_hint="Methods"
            ))
        
        return suggestions
    
    def _check_results_gaps(self, results: str) -> List[Suggestion]:
        """Check results for content gaps."""
        suggestions = []
        
        # Check for sample size description
        if not re.search(r'(?:n\s*=|sample|cohort|patients)', results.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.ADD_SECTION,
                topic="Sample Size in Results",
                reason="Results should clearly report sample sizes",
                priority=Priority.HIGH,
                effort=Effort.MINOR,
                location_hint="Results"
            ))
        
        # Check for figure/table references
        if not re.search(r'(?:Figure|Fig\.|Table)\s*\d+', results):
            suggestions.append(Suggestion(
                type=SuggestionType.ADD_FIGURE,
                topic="Visual Representation",
                reason="Results should reference figures or tables",
                priority=Priority.MEDIUM,
                effort=Effort.MAJOR,
                location_hint="Results"
            ))
        
        return suggestions
    
    def _check_discussion_gaps(self, discussion: str) -> List[Suggestion]:
        """Check discussion for content gaps."""
        suggestions = []
        
        # Check for limitations
        if not re.search(r'(?:limitation|limitation|caveat|drawback)', discussion.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.ADD_SECTION,
                topic="Study Limitations",
                reason="Discussion should address study limitations",
                priority=Priority.HIGH,
                effort=Effort.MODERATE,
                location_hint="Discussion"
            ))
        
        # Check for comparison with literature
        if not re.search(r'(?:consistent with|unlike|compared|previous|similar)', discussion.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.EXPAND_EXISTING,
                topic="Literature Comparison",
                reason="Discussion should compare findings with existing literature",
                priority=Priority.HIGH,
                effort=Effort.MODERATE,
                location_hint="Discussion"
            ))
        
        # Check for conclusions
        if not re.search(r'(?:conclusion|conclude|in summary|overall)', discussion.lower()):
            suggestions.append(Suggestion(
                type=SuggestionType.ADD_SECTION,
                topic="Conclusions",
                reason="Discussion should end with clear conclusions",
                priority=Priority.HIGH,
                effort=Effort.MODERATE,
                location_hint="End of Discussion"
            ))
        
        return suggestions


# ============== Integration Helper ==============

def analyze_and_enhance(manuscript_path: str, target_journal: str = "Blood") -> Dict[str, Any]:
    """
    Complete analysis and enhancement pipeline for a manuscript.
    
    Args:
        manuscript_path: Path to the manuscript
        target_journal: Target journal name
        
    Returns:
        Dictionary with quality report, suggestions, and enhanced content options
    """
    from tools.quality_analyzer import ManuscriptQualityAnalyzer, QualityReport
    
    # Analyze quality
    analyzer = ManuscriptQualityAnalyzer(target_journal)
    quality_report = analyzer.analyze_manuscript(manuscript_path)
    
    # Identify gaps
    enhancer = ContentEnhancer()
    gaps = enhancer.identify_content_gaps(manuscript_path, quality_report)
    suggestions = enhancer.suggest_content_additions(manuscript_path)
    
    return {
        'quality_report': quality_report,
        'content_gaps': gaps,
        'suggestions': suggestions
    }


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        manuscript_path = sys.argv[1]
        
        # Analyze
        result = analyze_and_enhance(manuscript_path)
        
        print("Quality Report:")
        print(f"Overall Score: {result['quality_report'].overall_score:.1f}%")
        print(f"\nSummary: {result['quality_report'].summary}")
        
        print(f"\n\nContent Gaps ({len(result['content_gaps'])} found):")
        for gap in result['content_gaps']:
            print(f"  - [{gap.type.value}] {gap.topic}")
        
        print(f"\nSuggestions ({len(result['suggestions'])} found):")
        for suggestion in result['suggestions']:
            print(f"  - [{suggestion.priority.value}] {suggestion.topic}")
