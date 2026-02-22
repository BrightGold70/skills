
"""
HPW Skill Upgrade - Core Infrastructure
===================================
Comprehensive data classes for PRISMA 2020, CONSORT 2010, and CARE 2013 compliance.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# Enums
# ============================================================================

class DocumentType(Enum):
    """Types of academic documents with guideline compliance."""
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    CLINICAL_TRIAL = "clinical_trial"
    CASE_REPORT = "case_report"
    RESEARCH_PAPER = "research_paper"
    LITERATURE_REVIEW = "literature_review"


class ReportingGuideline(Enum):
    """International reporting guidelines."""
    PRISMA_2020 = "prisma_2020"
    CONSORT_2010 = "consort_2010"
    CARE_2013 = "care_2013"
    ICMJE = "icmje"


class RiskOfBiasTool(Enum):
    """Tools for assessing risk of bias."""
    ROB_2_0 = "rob_2_0"
    ROBINS_I = "robins_i"
    NEWCASTLE_OTTAWA = "newcastle_ottawa"


class EvidenceQuality(Enum):
    """GRADE evidence quality levels."""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


# ============================================================================
# PRISMA 2020 Data Classes
# ============================================================================

@dataclass
class PrismaPhaseData:
    """Data for a single phase in the PRISMA flow diagram."""
    records_count: int = 0
    records_screened: int = 0
    records_excluded: int = 0
    full_text_assessed: int = 0
    full_text_excluded: int = 0
    studies_included: int = 0
    exclusion_reasons: Dict[str, int] = field(default_factory=dict)


@dataclass
class PrismaFlowData:
    """Complete data for PRISMA 2020 flow diagram."""
    title: str = ""
    identification_phase: PrismaPhaseData = field(default_factory=PrismaPhaseData)
    screening_phase: PrismaPhaseData = field(default_factory=PrismaPhaseData)
    eligibility_phase: PrismaPhaseData = field(default_factory=PrismaPhaseData)
    registration_number: str = ""
    protocol_link: str = ""
    prospero_date: str = ""
    
    def to_markdown(self) -> str:
        """Generate PRISMA flow diagram in markdown format."""
        ip = self.identification_phase
        sp = self.screening_phase
        ep = self.eligibility_phase
        
        diagram = f"""### PRISMA Flow Diagram: {self.title}

```
Identification Phase
   Records identified through database searching (n={ip.records_count}):
      • Database search results: {ip.records_count}
      • Additional records identified through other sources: TBD

Screening Phase  
   Records screened (n={ip.records_count}):
      • Records after duplicates removed: {ip.records_count - ip.records_excluded}
      • Records excluded (n={ip.records_excluded}): [reasons]

Eligibility Phase
   Full-text articles assessed for eligibility (n={sp.full_text_assessed}):
      • Full-text articles excluded with reasons (n={sp.full_text_excluded}):
"""
        
        for reason, count in sp.exclusion_reasons.items():
            diagram += f"         • {reason}: {count}\n"
        
        diagram += f"""
Included Studies
   Studies included in qualitative synthesis (n={ep.studies_included}):
      • Quantitative synthesis (meta-analysis): {ep.studies_included}
```

**Registration:** This systematic review was registered with PROSPERO (Registration Number: {self.registration_number}) on {self.prospero_date}. The protocol is available at: {self.protocol_link}
"""
        return diagram


@dataclass
class RiskOfBiasDomain:
    """Individual risk of bias domain assessment."""
    domain_name: str = ""
    judgment: str = ""  # Low, Some concerns, High, Critical
    support_for_judgment: str = ""


@dataclass
class RiskOfBiasAssessment:
    """Risk of bias assessment for a single study."""
    study_id: str = ""
    study_name: str = ""
    tool_used: RiskOfBiasTool = RiskOfBiasTool.ROB_2_0
    overall_judgment: str = ""
    domains: List[RiskOfBiasDomain] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """Generate risk of bias assessment in markdown format."""
        lines = [f"**{self.study_name}** ({self.tool_used.value})"]
        lines.append(f"**Overall Judgment:** {self.overall_judgment}\n")
        lines.append("| Domain | Judgment | Justification |")
        lines.append("|--------|----------|---------------|")
        for domain in self.domains:
            lines.append(f"| {domain.domain_name} | {domain.judgment} | {domain.support_for_judgment} |")
        return "\n".join(lines)


@dataclass
class HeterogeneityStatistics:
    """Statistical measures of heterogeneity for meta-analysis."""
    i_squared: float = 0.0
    tau_squared: float = 0.0
    q_statistic: float = 0.0
    q_p_value: float = 1.0
    interpretation: str = ""
    
    def to_markdown(self) -> str:
        """Generate heterogeneity statistics in markdown format."""
        interpretation_map = {
            (0, 25): "Negligible heterogeneity",
            (25, 50): "Low heterogeneity",
            (50, 75): "Moderate heterogeneity",
            (75, 101): "Substantial heterogeneity"
        }
        
        i_range = next((r for (low, high), interp in interpretation_map.items() 
                      if low <= self.i_squared < high), (75, 101))
        interp = next((v for (low, high), v in interpretation_map.items() 
                      if low <= self.i_squared < high), "Considerable heterogeneity")
        
        return f"""**Heterogeneity Statistics:**
- Cochran's Q: {self.q_statistic:.2f} (p = {self.q_p_value:.4f})
- I²: {self.i_squared:.1f}%
- τ²: {self.tau_squared:.4f}

**Interpretation:** {interp}


@dataclass
class GradeAssessment:
    """GRADE certainty of evidence assessment."""
    outcome: str = ""
    quality: EvidenceQuality = EvidenceQuality.MODERATE
    factors: List[str] = field(default_factory=list)
    justification: str = ""
    
    def to_markdown(self) -> str:
        """Generate GRADE assessment in markdown format."""
        factor_map = {
            "risk_of_bias": "Risk of bias",
            "inconsistency": "Inconsistency",
            "indirectness": "Indirectness",
            "imprecision": "Imprecision",
            "publication_bias": "Publication bias"
        }
        
        lines = [f"**Outcome:** {self.outcome}", ""]
        lines.append(f"**Quality Assessment:** {self.quality.value.upper()}", "")
        lines.append("**Factors Affecting Quality:**")
        for factor in self.factors:
            lines.append(f"- {factor_map.get(factor, factor)}")
        lines.append("")
        lines.append(f"**Justification:** {self.justification}")
        return "\n".join(lines)


# ============================================================================
# CONSORT 2010 Data Classes
# ============================================================================

@dataclass
class ConsortArmData:
    """Data for a single trial arm in CONSORT flow diagram."""
    arm_name: str = ""
    randomized: int = 0
    allocated_intervention: int = 0
    received_intervention: int = 0
    did_not_receive: int = 0
    reasons_for_not_receiving: Dict[str, int] = field(default_factory=dict)
    lost_to_followup: int = 0
    reasons_lost: Dict[str, int] = field(default_factory=dict)
    analyzed: int = 0
    excluded_from_analysis: int = 0


@dataclass
class ConsortFlowData:
    """Complete data for CONSORT 2010 flow diagram."""
    title: str = ""
    total_randomized: int = 0
    intervention_arm: ConsortArmData = field(default_factory=ConsortArmData)
    comparison_arm: ConsortArmData = field(default_factory=ConsortArmData)
    recruitment_dates: str = ""
    followup_period: str = ""
    analysis_dates: str = ""
    
    def to_markdown(self) -> str:
        """Generate CONSORT flow diagram in markdown format."""
        ia = self.intervention_arm
        ca = self.comparison_arm
        
        diagram = f"""### CONSORT Flow Diagram: {self.title}

```
Enrollment
   Randomized (n={self.total_randomized})
      |
      +-- Allocated to {ia.arm_name} (n={ia.randomized})
      |     +-- Received allocated intervention (n={ia.received_intervention})
      |     +-- Did not receive allocated intervention (n={ia.did_not_receive}):
"""
        
        for reason, count in ia.reasons_for_not_receiving.items():
            diagram += f"     |           • {reason}: {count}\n"
        
        diagram += f"""      |
      +-- Allocated to {ca.arm_name} (n={ca.randomized})
            +-- Received allocated intervention (n={ca.received_intervention})
            +-- Did not receive allocated intervention (n={ca.did_not_receive}):
"""
        
        for reason, count in ca.reasons_for_not_receiving.items():
            diagram += f"           • {reason}: {count}\n"
        
        diagram += f"""
Follow-Up
   {ia.arm_name}:
      +-- Lost to follow-up (n={ia.lost_to_followup}):
"""
        
        for reason, count in ia.reasons_lost.items():
            diagram += f"           • {reason}: {count}\n"
        
        diagram += f"""
   {ca.arm_name}:
      +-- Lost to follow-up (n={ca.lost_to_followup}):
"""
        
        for reason, count in ca.reasons_lost.items():
            diagram += f"           • {reason}: {count}\n"
        
        diagram += f"""
Analysis
   {ia.arm_name}:
      +-- Analysed (n={ia.analyzed})
      +-- Excluded from analysis (n={ia.excluded_from_analysis})
   
   {ca.arm_name}:
      +-- Analysed (n={ca.analyzed})
      +-- Excluded from analysis (n={ca.excluded_from_analysis})

**Recruitment Period:** {self.recruitment_dates}
**Follow-up Period:** {self.followup_period}
**Analysis Period:** {self.analysis_dates}
```
"""
        return diagram


@dataclass
class SampleSizeCalculation:
    """Sample size calculation for clinical trial."""
    alpha: float = 0.05
    power: float = 0.80
    effect_size: float = 0.0
    effect_measure: str = ""  # "mean difference", "proportion", "hazard ratio"
    expected_dropout: float = 0.10
    calculated_n_per_group: int = 0
    total_n: int = 0
    calculation_software: str = ""
    formula_reference: str = ""
    
    def to_markdown(self) -> str:
        """Generate sample size justification in markdown format."""
        dropout_pct = int(self.expected_dropout * 100)
        return f"""**Sample Size Determination:**

The sample size was calculated based on the following parameters:
- **Primary Outcome:** {self.effect_measure}
- **Expected Effect Size:** {self.effect_size}
- **Alpha (Two-sided):** {self.alpha}
- **Statistical Power:** {self.power}
- **Anticipated Dropout Rate:** {dropout_pct}%

**Calculation:**
Based on these parameters, {self.calculated_n_per_group} patients per group were required, for a total sample size of {self.total_n} patients.

**Software Used:** {self.calculation_software}
**Formula Reference:** {self.formula_reference}"""


@dataclass
class RandomizationDetails:
    """Randomization procedure documentation."""
    method: str = ""  # "Block randomization", "Permuted block", "Minimization"
    block_sizes: List[int] = field(default_factory=list)
    allocation_ratio: str = "1:1"
    stratification_factors: List[str] = field(default_factory=list)
    concealment_method: str = ""  # "Central randomization", "Web-based system", "Sealed envelopes"
    
    def to_markdown(self) -> str:
        """Generate randomization documentation in markdown format."""
        lines = [f"**Randomization Method:** {self.method}"]
        if self.block_sizes:
            lines.append(f"**Block Sizes:** {', '.join(map(str, self.block_sizes))}")
        lines.append(f"**Allocation Ratio:** {self.allocation_ratio}")
        if self.stratification_factors:
            lines.append(f"**Stratification Factors:** {', '.join(self.stratification_factors)}")
        lines.append(f"**Allocation Concealment:** {self.concealment_method}")
        return "\n".join(lines)


@dataclass
class BlindingDetails:
    """Blinding procedure documentation."""
    blinded_participants: bool = False
    blinded_personnel: bool = False
    blinded_assessors: bool = False
    blinded_data_analysis: bool = False
    blinding_procedure: str = ""
    emergency_unblinding_procedure: str = ""
    
    def to_markdown(self) -> str:
        """Generate blinding documentation in markdown format."""
        lines = ["**Blinding Procedures:**", ""]
        lines.append(f"- Participants: {'Yes' if self.blinded_participants else 'No'}")
        lines.append(f"- Personnel: {'Yes' if self.blinded_personnel else 'No'}")
        lines.append(f"- Outcome Assessors: {'Yes' if self.blinded_assessors else 'No'}")
        lines.append(f"- Data Analysts: {'Yes' if self.blinded_data_analysis else 'No'}", "")
        lines.append(f"**Blinding Procedure:** {self.blinding_procedure}", "")
        lines.append(f"**Emergency Unblinding Procedure:** {self.emergency_unblinding_procedure}")
        return "\n".join(lines)


# ============================================================================
# CARE 2013 Data Classes
# ============================================================================

@dataclass
class TimelineEvent:
    """Single event in case report timeline."""
    date: str = ""
    event_description: str = ""
    clinical_significance: str = ""
    
    def to_markdown(self) -> str:
        """Generate timeline event in markdown format."""
        return f"- **{self.date}:** {self.event_description}"


@dataclass
class CaseReportData:
    """Complete data for CARE 2013 case report."""
    title: str = ""
    patient_age: str = ""
    patient_sex: str = ""
    presenting_symptoms: List[str] = field(default_factory=list)
    past_medical_history: List[str] = field(default_factory=list)
    family_history: str = ""
    social_history: str = ""
    physical_exam_findings: Dict[str, str] = field(default_factory=dict)
    laboratory_results: Dict[str, str] = field(default_factory=dict)
    imaging_findings: Dict[str, str] = field(default_factory=dict)
    biopsy_results: Dict[str, str] = field(default_factory=dict)
    diagnostic_reasoning: str = ""
    differential_diagnosis: List[str] = field(default_factory=list)
    treatment_rationale: str = ""
    treatment_details: Dict[str, str] = field(default_factory=dict)
    treatment_response: str = ""
    adverse_events: List[str] = field(default_factory=list)
    follow_up_timeline: List[TimelineEvent] = field(default_factory=list)
    final_outcome: str = ""
    informed_consent: str = "Written informed consent was obtained from the patient for publication."
    patient_perspective: str = ""
    
    def to_markdown(self) -> str:
        """Generate complete case report data in markdown format."""
        lines = ["### Patient Information", ""]
        lines.append(f"- **Age:** {self.patient_age}")
        lines.append(f"- **Sex:** {self.patient_sex}", "")
        lines.append("**Presenting Symptoms:**")
        for symptom in self.presenting_symptoms:
            lines.append(f"- {symptom}")
        lines.append("")
        lines.append("**Past Medical History:**")
        for history in self.past_medical_history:
            lines.append(f"- {history}")
        lines.append("")
        lines.append(f"**Family History:** {self.family_history}")
        lines.append(f"**Social History:** {self.social_history}", "")
        lines.append("### Clinical Findings")
        for system, finding in self.physical_exam_findings.items():
            lines.append(f"- **{system}:** {finding}")
        lines.append("")
        lines.append("### Diagnostic Assessment")
        lines.append("**Laboratory Results:**")
        for test, result in self.laboratory_results.items():
            lines.append(f"- {test}: {result}")
        lines.append("")
        lines.append("**Imaging Findings:**")
        for modality, finding in self.imaging_findings.items():
            lines.append(f"- {modality}: {finding}")
        lines.append("")
        lines.append("**Biopsy Results:**")
        for biopsy_type, result in self.biopsy_results.items():
            lines.append(f"- {biopsy_type}: {result}")
        lines.append("")
        lines.append(f"**Diagnostic Reasoning:** {self.diagnostic_reasoning}")
        lines.append("")
        lines.append("**Differential Diagnosis:**")
        for diagnosis in self.differential_diagnosis:
            lines.append(f"- {diagnosis}")
        lines.append("")
        lines.append("### Treatment")
        lines.append(f"**Rationale:** {self.treatment_rationale}")
        lines.append("")
        lines.append("**Treatment Details:**")
        for detail_type, detail in self.treatment_details.items():
            lines.append(f"- **{detail_type}:** {detail}")
        lines.append("")
        lines.append(f"**Response:** {self.treatment_response}")
        lines.append("")
        lines.append("**Adverse Events:**")
        for event in self.adverse_events:
            lines.append(f"- {event}")
        lines.append("")
        lines.append("### Follow-up Timeline")
        for event in self.follow_up_timeline:
            lines.append(event.to_markdown())
        lines.append("")
        lines.append(f"**Final Outcome:** {self.final_outcome}")
        return "\n".join(lines)


# ============================================================================
# Source and Reference Classes
# ============================================================================

@dataclass
class AcademicSource:
    """Enhanced academic source with verification status."""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: int = 0
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""
    pmid: str = ""
    url: str = ""
    citation_count: int = 0
    is_peer_reviewed: bool = True
    is_verified: bool = False
    verification_source: str = ""
    risk_of_bias_assessment: Optional[RiskOfBiasAssessment] = None
    
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
class TableData:
    """Manuscript table representation."""
    number: int = 0
    title: str = ""
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    caption: str = ""
    note: str = ""
    
    def to_markdown(self) -> str:
        """Generate markdown table."""
        lines = [f"**Table {self.number}. {self.title}**"]
        if self.caption:
            lines.append(f"*{self.caption}*")
        lines.append("")
        lines.append(f"| {' | '.join(self.headers)} |")
        lines.append(f"| {' | '.join(['---'] * len(self.headers))} |")
        for row in self.rows:
            lines.append(f"| {' | '.join(row)} |")
        if self.note:
            lines.append(f"\n*{self.note}*")
        return "\n".join(lines)


@dataclass
class FigureData:
    """Manuscript figure representation."""
    number: int = 0
    title: str = ""
    description: str = ""
    caption: str = ""
    figure_type: str = "graph"  # "flowchart", "forest", "survival", "scatter", etc.
    
    def to_markdown(self) -> str:
        """Generate figure reference in markdown."""
        lines = [f"**Figure {self.number}. {self.title}**"]
        if self.caption:
            lines.append(f"*{self.caption}*")
        if self.description:
            lines.append(self.description)
        return "\n".join(lines)


# ============================================================================
# Manuscript Structure Class
# ============================================================================

@dataclass
class ManuscriptStructure:
    """Complete manuscript structure with guideline compliance."""
    document_type: DocumentType = DocumentType.RESEARCH_PAPER
    title: str = ""
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    sections: Dict[str, str] = field(default_factory=dict)
    tables: List[TableData] = field(default_factory=list)
    figures: List[FigureData] = field(default_factory=list)
    references: List[AcademicSource] = field(default_factory=list)
    
    # Guideline compliance metadata
    prisma_data: Optional[PrismaFlowData] = None
    consort_data: Optional[ConsortFlowData] = None
    case_data: Optional[CaseReportData] = None
    
    # Calculated fields
    word_count: int = 0
    reference_count: int = 0
    table_count: int = 0
    figure_count: int = 0
    
    def to_markdown(self) -> str:
        """Generate complete manuscript in markdown format."""
        lines = [f"# {self.title}", ""]
        
        # Authors
        if self.authors:
            lines.append(", ".join(self.authors), "")
        else:
            lines.append("[Authors to be added]", "")
        
        # Abstract
        if self.abstract:
            lines.append(f"**Abstract**\n\n{self.abstract}", "")
        
        # Keywords
        if self.keywords:
            lines.append(f"**Keywords:** {', '.join(self.keywords)}", "")
        
        # Sections
        for section_title, section_content in self.sections.items():
            lines.append(f"## {section_title}", "")
            lines.append(section_content, "")
        
        # Tables
        if self.tables:
            lines.append("## Tables", "")
            for table in self.tables:
                lines.append(table.to_markdown(), "")
        
        # Figures
        if self.figures:
            lines.append("## Figures", "")
            for figure in self.figures:
                lines.append(figure.to_markdown(), "")
        
        # References
        lines.append("## References", "")
        for i, ref in enumerate(self.references, 1):
            lines.append(ref.to_vancouver(i), "")
        
        return "\n".join(lines)


# ============================================================================
# Utility Functions
# ============================================================================

def calculate_sample_size(
    alpha: float = 0.05,
    power: float = 0.80,
    effect_size: float = 0.5,
    effect_measure: str = "standardized mean difference",
    dropout_rate: float = 0.10
) -> SampleSizeCalculation:
    """Calculate required sample size for clinical trial."""
    # Simplified calculation (would use proper statistical library in production)
    from scipy import stats
    import numpy as np
    
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power)
    
    if effect_measure in ["standardized mean difference", "cohens d"]:
        n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    else:
        n_per_group = ((z_alpha + z_beta) / effect_size) ** 2
    
    # Adjust for dropout
    n_adjusted = int(np.ceil(n_per_group / (1 - dropout_rate)))
    
    return SampleSizeCalculation(
        alpha=alpha,
        power=power,
        effect_size=effect_size,
        effect_measure=effect_measure,
        expected_dropout=dropout_rate,
        calculated_n_per_group=n_adjusted,
        total_n=n_adjusted * 2,
        calculation_software="Python (scipy.stats)",
        formula_reference=f"Two-sided alpha={alpha}, power={power}, effect={effect_size}"
    )


def calculate_sample_size(
    alpha: float = 0.05,
    power: float = 0.80,
    effect_size: float = 0.5,
    effect_measure: str = "standardized mean difference",
    dropout_rate: float = 0.10
) -> SampleSizeCalculation:
    """Calculate required sample size for clinical trial."""
    # Simplified calculation (would use proper statistical library in production)
    try:
        from scipy import stats
        import numpy as np
        
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(power)
        
        if effect_measure in ["standardized mean difference", "cohens d"]:
            n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        else:
            n_per_group = ((z_alpha + z_beta) / effect_size) ** 2
        
        # Adjust for dropout
        n_adjusted = int(np.ceil(n_per_group / (1 - dropout_rate)))
        total_n = n_adjusted * 2
        
    except ImportError:
        # Fallback if scipy not available
        n_per_group = int(2 * ((1.96 + 0.84) / effect_size) ** 2)
        n_adjusted = int(np.ceil(n_per_group / (1 - dropout_rate)))
        total_n = n_adjusted * 2
    
    return SampleSizeCalculation(
        alpha=alpha,
        power=power,
        effect_size=effect_size,
        effect_measure=effect_measure,
        expected_dropout=dropout_rate,
        calculated_n_per_group=n_adjusted,
        total_n=total_n,
        calculation_software="Python (scipy.stats)",
        formula_reference=f"Two-sided alpha={alpha}, power={power}, effect={effect_size}"
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print("HPW Skill Upgrade - Core Infrastructure Module Loaded")
    print(f"Document Types: {[dt.value for dt in DocumentType]}")
    print(f"Reporting Guidelines: {[rg.value for rg in ReportingGuideline]}")
