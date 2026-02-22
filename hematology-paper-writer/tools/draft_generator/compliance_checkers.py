"""
HPW Skill Upgrade - Compliance Checkers
==================================
PRISMA 2020, CONSORT 2010, and CARE 2013 compliance validation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class ComplianceResult:
    """Result of compliance check."""
    is_compliant: bool
    score: float
    items_passed: int
    items_total: int
    missing_items: List[str]
    warnings: List[str]
    recommendations: List[str]


class PrismaComplianceChecker:
    """Check PRISMA 2020 compliance."""
    
    PRISMA_ITEMS = [
        ("title", "Title identifies as systematic review"),
        ("abstract", "Structured abstract provided"),
        ("rationale", "Rationale described"),
        ("objectives", "Objectives clearly stated"),
        ("eligibility_pico", "Eligibility criteria (PICO) documented"),
        ("information_sources", "Information sources listed"),
        ("search_strategy", "Complete search strategy provided"),
        ("selection_process", "Selection process described"),
        ("data_extraction", "Data extraction process documented"),
        ("data_items", "Data items listed"),
        ("risk_of_bias_study", "Study risk of bias assessed"),
        ("effect_measures", "Effect measures specified"),
        ("synthesis_methods", "Synthesis methods described"),
        ("reporting_bias", "Reporting bias assessed"),
        ("certainty", "Certainty assessment conducted"),
        ("flow_diagram", "PRISMA flow diagram included"),
        ("study_characteristics", "Study characteristics documented"),
        ("risk_of_bias_results", "Risk of bias results presented"),
        ("individual_results", "Results of individual studies"),
        ("synthesis_results", "Results of syntheses"),
        ("reporting_bias_discussion", "Reporting biases discussed"),
        ("certainty_discussion", "Certainty of evidence discussed"),
        ("limitations", "Limitations discussed"),
        ("interpretation", "Interpretation provided"),
        ("registration", "Protocol registered"),
        ("protocol_access", "Protocol access provided"),
        ("support", "Sources of support acknowledged"),
    ]
    
    def check(self, manuscript: str, sections: Dict[str, str]) -> ComplianceResult:
        """Check PRISMA 2020 compliance."""
        text_lower = manuscript.lower()
        
        items_passed = []
        missing_items = []
        warnings = []
        recommendations = []
        
        # Check for each item
        checks = {
            "title": any(kw in text_lower for kw in ["systematic review", "meta-analysis"]),
            "abstract": "abstract" in text_lower and len(sections.get("abstract", "")) > 100,
            "rationale": any(kw in text_lower for kw in ["rationale", "background", "introduction"]),
            "objectives": any(kw in text_lower for kw in ["objective", "aim", "purpose"]),
            "eligibility_pico": "pico" in text_lower or any(kw in text_lower for kw in ["eligibility", "inclusion", "exclusion criteria"]),
            "information_sources": any(kw in text_lower for kw in ["database", "pubmed", "embase", "cochrane"]),
            "search_strategy": "search" in text_lower and any(kw in text_lower for kw in ["strategy", "terms", "string"]),
            "selection_process": any(kw in text_lower for kw in ["selection", "screening", "prisma flow"]),
            "data_extraction": "data extraction" in text_lower,
            "data_items": any(kw in text_lower for kw in ["data items", "variables", "outcomes"]),
            "risk_of_bias_study": any(kw in text_lower for kw in ["risk of bias", "rob", "bias assessment"]),
            "effect_measures": any(kw in text_lower for kw in ["effect measure", "risk ratio", "hazard ratio"]),
            "synthesis_methods": any(kw in text_lower for kw in ["synthesis", "meta-analysis", "pooled"]),
            "reporting_bias": any(kw in text_lower for kw in ["publication bias", "funnel plot", "egger"]),
            "certainty": any(kw in text_lower for kw in ["certainty", "grade", "quality of evidence"]),
            "flow_diagram": "flow diagram" in text_lower or "prisma" in text_lower,
            "study_characteristics": any(kw in text_lower for kw in ["study characteristics", "table 1"]),
            "risk_of_bias_results": any(kw in text_lower for kw in ["risk of bias", "rob results"]),
            "individual_results": any(kw in text_lower for kw in ["results of individual", "study results"]),
            "synthesis_results": any(kw in text_lower for kw in ["synthesis results", "meta-analysis results"]),
            "reporting_bias_discussion": "publication bias" in text_lower,
            "certainty_discussion": "certainty" in text_lower,
            "limitations": "limitation" in text_lower,
            "interpretation": any(kw in text_lower for kw in ["interpretation", "implication"]),
            "registration": any(kw in text_lower for kw in ["registration", "prospero"]),
            "protocol_access": any(kw in text_lower for kw in ["protocol", "available at"]),
            "support": any(kw in text_lower for kw in ["funding", "support", "acknowledg"]),
        }
        
        for item, description in self.PRISMA_ITEMS:
            if checks.get(item, False):
                items_passed.append(description)
            else:
                missing_items.append(description)
        
        # Calculate score
        score = len(items_passed) / len(self.PRISMA_ITEMS) if self.PRISMA_ITEMS else 0
        is_compliant = score >= 0.85
        
        # Add recommendations
        if "flow_diagram" not in checks or not checks["flow_diagram"]:
            recommendations.append("Include a PRISMA flow diagram documenting study selection")
        if "certainty" not in checks or not checks["certainty"]:
            recommendations.append("Conduct GRADE certainty of evidence assessment")
        if "search_strategy" not in checks or not checks["search_strategy"]:
            recommendations.append("Provide complete search strategy for each database")
        
        return ComplianceResult(
            is_compliant=is_compliant,
            score=score,
            items_passed=len(items_passed),
            items_total=len(self.PRISMA_ITEMS),
            missing_items=missing_items,
            warnings=warnings,
            recommendations=recommendations
        )


class ConsortComplianceChecker:
    """Check CONSORT 2010 compliance."""
    
    CONSORT_ITEMS = [
        ("title", "Title identifies as randomized trial"),
        ("abstract", "Structured abstract provided"),
        ("scientific_background", "Scientific background and rationale"),
        ("objectives", "Specific objectives and hypotheses"),
        ("trial_design", "Trial design described with changes documented"),
        ("participants", "Eligibility criteria documented"),
        ("settings", "Settings and locations described"),
        ("interventions", "Interventions fully described"),
        ("outcomes", "Outcomes pre-specified and defined"),
        ("sample_size", "Sample size determination documented"),
        ("randomization_sequence", "Randomization sequence generation described"),
        ("allocation_concealment", "Allocation concealment mechanism described"),
        ("implementation", "Randomization implementation documented"),
        ("blinding", "Blinding procedures documented"),
        ("statistical_methods", "Statistical methods described"),
        ("participant_flow", "CONSORT flow diagram included"),
        ("recruitment", "Recruitment dates documented"),
        ("baseline_data", "Baseline demographic data provided"),
        ("numbers_analyzed", "Numbers analyzed per group"),
        ("outcomes_estimation", "Outcomes with estimates provided"),
        ("ancillary_analyses", "Ancillary analyses conducted"),
        ("adverse_events", "Adverse events reported"),
        ("limitations", "Limitations discussed"),
        ("generalizability", "Generalizability addressed"),
        ("interpretation", "Interpretation provided"),
        ("registration", "Trial registration documented"),
        ("protocol", "Protocol access provided"),
        ("funding", "Sources of funding documented"),
    ]
    
    def check(self, manuscript: str, sections: Dict[str, str]) -> ComplianceResult:
        """Check CONSORT 2010 compliance."""
        text_lower = manuscript.lower()
        
        items_passed = []
        missing_items = []
        recommendations = []
        
        # Check for each item
        checks = {
            "title": any(kw in text_lower for kw in ["randomized", "randomised", "rct", "clinical trial"]),
            "abstract": "abstract" in text_lower,
            "scientific_background": any(kw in text_lower for kw in ["background", "rationale"]),
            "objectives": any(kw in text_lower for kw in ["objective", "hypothesis"]),
            "trial_design": any(kw in text_lower for kw in ["trial design", "parallel", "crossover"]),
            "participants": any(kw in text_lower for kw in ["eligibility", "inclusion", "exclusion criteria"]),
            "settings": any(kw in text_lower for kw in ["setting", "location", "site"]),
            "interventions": any(kw in text_lower for kw in ["intervention", "treatment", "dose"]),
            "outcomes": any(kw in text_lower for kw in ["outcome", "endpoint"]),
            "sample_size": any(kw in text_lower for kw in ["sample size", "power calculation", "sample size determination"]),
            "randomization_sequence": any(kw in text_lower for kw in ["randomization", "randomisation", "block"]),
            "allocation_concealment": any(kw in text_lower for kw in ["allocation concealment", "concealment"]),
            "implementation": "randomization" in text_lower or "implementation" in text_lower,
            "blinding": any(kw in text_lower for kw in ["blinding", "masking", "double-blind", "single-blind"]),
            "statistical_methods": any(kw in text_lower for kw in ["statistical analysis", "statistical methods"]),
            "participant_flow": "flow diagram" in text_lower or "consort" in text_lower,
            "recruitment": any(kw in text_lower for kw in ["recruitment", "enrollment", "dates"]),
            "baseline_data": any(kw in text_lower for kw in ["baseline", "demographic"]),
            "numbers_analyzed": any(kw in text_lower for kw in ["analyzed", "analysis population", "itt"]),
            "outcomes_estimation": any(kw in text_lower for kw in ["hazard ratio", "risk ratio", "effect estimate"]),
            "ancillary_analyses": any(kw in text_lower for kw in ["subgroup", "sensitivity analysis"]),
            "adverse_events": any(kw in text_lower for kw in ["adverse event", "safety", "toxicity"]),
            "limitations": "limitation" in text_lower,
            "generalizability": any(kw in text_lower for kw in ["generalizability", "generalisation", "external validity"]),
            "interpretation": any(kw in text_lower for kw in ["interpretation", "implication"]),
            "registration": any(kw in text_lower for kw in ["registration", "clinicaltrials.gov", "nct"]),
            "protocol": any(kw in text_lower for kw in ["protocol", "analysis plan"]),
            "funding": any(kw in text_lower for kw in ["funding", "supported by", "grant"]),
        }
        
        for item, description in self.CONSORT_ITEMS:
            if checks.get(item, False):
                items_passed.append(description)
            else:
                missing_items.append(description)
        
        score = len(items_passed) / len(self.CONSORT_ITEMS) if self.CONSORT_ITEMS else 0
        is_compliant = score >= 0.90
        
        if "flow_diagram" not in checks or not checks["flow_diagram"]:
            recommendations.append("Include a CONSORT flow diagram showing participant flow")
        if "adverse_events" not in checks or not checks["adverse_events"]:
            recommendations.append("Report all adverse events by treatment arm with severity grades")
        
        return ComplianceResult(
            is_compliant=is_compliant,
            score=score,
            items_passed=len(items_passed),
            items_total=len(self.CONSORT_ITEMS),
            missing_items=missing_items,
            warnings=[],
            recommendations=recommendations
        )


class CareComplianceChecker:
    """Check CARE 2013 compliance."""
    
    CARE_ITEMS = [
        ("title", "Title identifies as case report"),
        ("abstract", "Abstract provided"),
        ("keywords", "Keywords provided"),
        ("introduction", "Introduction with context"),
        ("patient_info", "Patient information anonymized"),
        ("case_presentation", "Case presentation with timeline"),
        ("clinical_findings", "Clinical findings documented"),
        ("diagnostic_assessment", "Diagnostic assessment described"),
        ("therapeutic_intervention", "Therapeutic intervention documented"),
        ("follow_up", "Follow-up and outcomes described"),
        ("discussion", "Discussion with strengths and limitations"),
        ("patient_perspective", "Patient perspective if available"),
        ("informed_consent", "Informed consent statement included"),
    ]
    
    def check(self, manuscript: str, sections: Dict[str, str]) -> ComplianceResult:
        """Check CARE 2013 compliance."""
        text_lower = manuscript.lower()
        
        items_passed = []
        missing_items = []
        recommendations = []
        
        checks = {
            "title": "case report" in text_lower,
            "abstract": "abstract" in text_lower,
            "keywords": "keyword" in text_lower,
            "introduction": "introduction" in text_lower,
            "patient_info": any(kw in text_lower for kw in ["patient", "age", "male", "female"]),
            "case_presentation": any(kw in text_lower for kw in ["case presentation", "presentation", "history"]),
            "clinical_findings": any(kw in text_lower for kw in ["physical examination", "clinical finding", "vital"]),
            "diagnostic_assessment": any(kw in text_lower for kw in ["diagnosis", "diagnostic", "laboratory", "imaging"]),
            "therapeutic_intervention": any(kw in text_lower for kw in ["treatment", "intervention", "therapy"]),
            "follow_up": any(kw in text_lower for kw in ["follow-up", "outcome", "response"]),
            "discussion": "discussion" in text_lower,
            "patient_perspective": "patient perspective" in text_lower or "patient's perspective" in text_lower,
            "informed_consent": any(kw in text_lower for kw in ["informed consent", "consent obtained"]),
        }
        
        for item, description in self.CARE_ITEMS:
            if checks.get(item, False):
                items_passed.append(description)
            else:
                missing_items.append(description)
        
        score = len(items_passed) / len(self.CARE_ITEMS) if self.CARE_ITEMS else 0
        is_compliant = score >= 0.90
        
        if "informed_consent" not in checks or not checks["informed_consent"]:
            recommendations.append("Include statement confirming informed consent obtained")
        if "timeline" not in text_lower:
            recommendations.append("Include timeline of clinical course")
        
        return ComplianceResult(
            is_compliant=is_compliant,
            score=score,
            items_passed=len(items_passed),
            items_total=len(self.CARE_ITEMS),
            missing_items=missing_items,
            warnings=[],
            recommendations=recommendations
        )


def check_manuscript_compliance(
    manuscript: str,
    sections: Dict[str, str],
    document_type: str
) -> Dict[str, ComplianceResult]:
    """Check manuscript compliance with appropriate guidelines."""
    results = {}
    
    if document_type in ["systematic_review", "meta_analysis"]:
        checker = PrismaComplianceChecker()
        results["PRISMA 2020"] = checker.check(manuscript, sections)
    
    if document_type == "clinical_trial":
        checker = ConsortComplianceChecker()
        results["CONSORT 2010"] = checker.check(manuscript, sections)
    
    if document_type == "case_report":
        checker = CareComplianceChecker()
        results["CARE 2013"] = checker.check(manuscript, sections)
    
    return results


if __name__ == "__main__":
    print("HPW Compliance Checkers Module Loaded")
    print("Checkers available:")
    print("  - PrismaComplianceChecker")
    print("  - ConsortComplianceChecker")
    print("  - CareComplianceChecker")
    print("  - check_manuscript_compliance()")
