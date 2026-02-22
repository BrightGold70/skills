"""
Phase 1: Topic Development Module
PICO framework formulation and research question validation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import re


class StudyType(Enum):
    """Types of hematology studies."""

    CLASSIFICATION = "classification"
    GVHD = "gvhd"
    THERAPEUTIC = "therapeutic"
    PROGNOSTIC = "prognostic"
    DIAGNOSTIC = "diagnostic"


@dataclass
class PICO:
    """PICO framework structure for research questions."""

    population: str = ""
    intervention: str = ""
    comparator: str = ""
    outcome: str = ""
    study_design: str = ""

    def is_complete(self) -> bool:
        """Check if all PICO elements are defined."""
        return all([self.population, self.intervention, self.comparator, self.outcome])

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "Population": self.population,
            "Intervention": self.intervention,
            "Comparator": self.comparator,
            "Outcome": self.outcome,
            "Study Design": self.study_design,
        }

    def format_research_question(self) -> str:
        """Format PICO into research question."""
        if not self.is_complete():
            return "[Incomplete PICO - all elements required]"

        return (
            f"In {self.population}, "
            f"does {self.intervention} "
            f"compared to {self.comparator} "
            f"result in {self.outcome}?"
        )


@dataclass
class ResearchTopic:
    """Complete research topic with PICO and metadata."""

    title: str = ""
    pico: PICO = field(default_factory=PICO)
    study_type: StudyType = StudyType.THERAPEUTIC
    disease_entity: str = ""
    keywords: List[str] = field(default_factory=list)
    clinical_significance: str = ""
    innovation_score: int = 0  # 1-10
    feasibility_score: int = 0  # 1-10

    def validate(self) -> Dict[str, Any]:
        """Validate research topic completeness."""
        issues = []

        if not self.title:
            issues.append("Title is required")

        if not self.pico.is_complete():
            issues.append("Complete PICO framework required")

        if not self.disease_entity:
            issues.append("Disease/entity must be specified")

        if len(self.keywords) < 3:
            issues.append("At least 3 keywords recommended")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "completeness": self._calculate_completeness(),
        }

    def _calculate_completeness(self) -> float:
        """Calculate topic completeness percentage."""
        required_fields = [
            self.title,
            self.pico.population,
            self.pico.intervention,
            self.pico.comparator,
            self.pico.outcome,
            self.disease_entity,
        ]

        filled = sum(1 for field in required_fields if field)
        return (filled / len(required_fields)) * 100


class TopicDevelopmentManager:
    """Manages research topic development and PICO formulation."""

    # Hematology-specific study design recommendations
    STUDY_DESIGNS = {
        StudyType.CLASSIFICATION: [
            "Retrospective cohort analysis",
            "Cross-sectional diagnostic study",
            "Multi-center registry analysis",
            "Validation cohort study",
        ],
        StudyType.GVHD: [
            "Prospective cohort study",
            "Retrospective chart review",
            "Case-control study",
            "Cross-sectional analysis",
        ],
        StudyType.THERAPEUTIC: [
            "Randomized controlled trial",
            "Single-arm phase II trial",
            "Retrospective cohort comparison",
            "Registry-based comparative study",
        ],
        StudyType.PROGNOSTIC: [
            "Retrospective cohort analysis",
            "Prospective validation study",
            "Multi-center registry study",
            "Survival analysis",
        ],
        StudyType.DIAGNOSTIC: [
            "Cross-sectional diagnostic accuracy study",
            "Prospective validation cohort",
            "Case-control diagnostic study",
            "Method comparison study",
        ],
    }

    # Disease entities for validation
    DISEASE_ENTITIES = {
        "AML": [
            "AML with NPM1 mutation",
            "AML with FLT3-ITD",
            "AML with TP53 mutation",
            "AML with RUNX1::RUNX1T1",
            "AML with CBFB::MYH11",
            "AML with PML::RARA",
            "AML with myelodysplasia-related changes",
            "Therapy-related AML",
        ],
        "MDS": [
            "MDS with single vs multilineage dysplasia",
            "MDS with excess blasts",
            "MDS with del(5q)",
            "MDS-EB1",
            "MDS-EB2",
        ],
        "MPN": [
            "Chronic myeloid leukemia (CML)",
            "Polycythemia vera (PV)",
            "Essential thrombocythemia (ET)",
            "Primary myelofibrosis (PMF)",
        ],
        "GVHD": [
            "Acute GVHD Grade I-IV",
            "Chronic GVHD Mild-Severe",
            "Steroid-refractory GVHD",
            "Overlap syndrome",
        ],
        "ALL": ["B-ALL", "T-ALL", "Ph+ ALL (BCR::ABL1+)", "KMT2A-rearranged ALL"],
    }

    def __init__(self):
        """Initialize topic development manager."""
        self.current_topic: Optional[ResearchTopic] = None
        self.topic_history: List[ResearchTopic] = []

    def create_pico(
        self,
        population: str,
        intervention: str,
        comparator: str,
        outcome: str,
        study_design: str = "",
    ) -> PICO:
        """
        Create PICO framework from components.

        Args:
            population: Study population
            intervention: Intervention or exposure
            comparator: Control or comparison group
            outcome: Primary outcome measure
            study_design: Proposed study design

        Returns:
            PICO object
        """
        return PICO(
            population=population,
            intervention=intervention,
            comparator=comparator,
            outcome=outcome,
            study_design=study_design,
        )

    def suggest_population(self, disease_entity: str) -> List[str]:
        """
        Suggest appropriate study populations for disease entity.

        Args:
            disease_entity: Disease or entity being studied

        Returns:
            List of suggested population descriptions
        """
        suggestions = []

        disease_upper = disease_entity.upper()

        if "AML" in disease_upper:
            suggestions = [
                "Adults ≥18 years with newly diagnosed AML",
                "AML patients receiving first-line induction chemotherapy",
                "Older adults (≥60 years) with AML unfit for intensive chemotherapy",
                "Pediatric AML patients (1-18 years)",
                "AML patients with adverse-risk cytogenetics",
            ]
        elif "MDS" in disease_upper:
            suggestions = [
                "Adults with newly diagnosed MDS",
                "MDS patients with IPSS-R intermediate or higher risk",
                "MDS patients with del(5q) cytogenetic abnormality",
            ]
        elif "GVHD" in disease_upper or "GVHD" in disease_upper:
            suggestions = [
                "Allogeneic HSCT recipients with chronic GVHD",
                "Patients with steroid-refractory acute GVHD",
                "Pediatric HSCT recipients with any grade GVHD",
            ]
        elif "CML" in disease_upper:
            suggestions = [
                "CML patients in chronic phase",
                "CML patients with treatment failure on first-line TKI",
                "CML patients with BCR::ABL1 kinase domain mutations",
            ]
        else:
            suggestions = [
                f"Patients with {disease_entity}",
                f"Adults diagnosed with {disease_entity}",
                f"Treatment-naive patients with {disease_entity}",
            ]

        return suggestions

    def suggest_interventions(
        self, disease_entity: str, study_type: StudyType
    ) -> List[str]:
        """Suggest appropriate interventions based on disease and study type."""
        suggestions = []

        if study_type == StudyType.THERAPEUTIC:
            if "AML" in disease_entity.upper():
                suggestions = [
                    "Venetoclax + azacitidine combination",
                    "Intensive 7+3 chemotherapy",
                    "Targeted therapy based on molecular profiling",
                    "Hypomethylating agent monotherapy",
                    "Clinical trial novel agent",
                ]
            elif "CML" in disease_entity.upper():
                suggestions = [
                    "Second-generation TKI (dasatinib, nilotinib)",
                    "Third-generation TKI (ponatinib)",
                    "Switch to alternative TKI after failure",
                    "Asciminib (STAMP inhibitor)",
                ]
            elif "GVHD" in disease_entity.upper():
                suggestions = [
                    "Ruxolitinib (JAK1/2 inhibitor)",
                    "Extracorporeal photopheresis (ECP)",
                    "Mesenchymal stromal cell therapy",
                    "Belumosudil (ROCK2 inhibitor)",
                    "Ibrutinib (BTK inhibitor)",
                ]

        elif study_type == StudyType.DIAGNOSTIC:
            suggestions = [
                "Next-generation sequencing panel",
                "Flow cytometry immunophenotyping",
                "FISH analysis for common translocations",
                "RT-PCR for fusion transcripts",
                "Multiplex ligation-dependent probe amplification (MLPA)",
            ]

        elif study_type == StudyType.PROGNOSTIC:
            suggestions = [
                "Molecular risk stratification",
                "Minimal residual disease (MRD) monitoring",
                "Measurable residual disease by flow cytometry",
                "NGS-based measurable residual disease",
            ]

        return suggestions or ["[Specify intervention based on research question]"]

    def suggest_outcomes(self, study_type: StudyType) -> List[str]:
        """Suggest appropriate outcome measures."""
        outcomes = {
            StudyType.THERAPEUTIC: [
                "Overall survival (OS) at 2 years",
                "Event-free survival (EFS)",
                "Complete remission (CR) rate",
                "Minimal residual disease negativity",
                "Treatment-related mortality",
                "Time to progression",
            ],
            StudyType.GVHD: [
                "GVHD response rate (CR+PR)",
                "Steroid-free response",
                "Failure-free survival",
                "Overall survival",
                "Quality of life scores (LEFS, FACT-BMT)",
                "GVHD-specific survival",
            ],
            StudyType.CLASSIFICATION: [
                "Diagnostic accuracy (sensitivity/specificity)",
                "Inter-observer agreement (kappa)",
                "Reclassification rate",
                "Prognostic discrimination (C-index)",
            ],
            StudyType.DIAGNOSTIC: [
                "Sensitivity and specificity",
                "Positive predictive value",
                "Negative predictive value",
                "Area under ROC curve",
                "Diagnostic odds ratio",
            ],
            StudyType.PROGNOSTIC: [
                "Overall survival",
                "Disease-free survival",
                "Cumulative incidence of relapse",
                "Non-relapse mortality",
                "Risk stratification accuracy",
            ],
        }

        return outcomes.get(study_type, ["[Specify primary outcome measure]"])

    def recommend_study_design(
        self,
        study_type: StudyType,
        feasibility: str = "moderate",  # 'high', 'moderate', 'low'
    ) -> List[str]:
        """
        Recommend study designs based on study type and feasibility.

        Args:
            study_type: Type of study
            feasibility: Resource/feasibility level

        Returns:
            List of recommended study designs
        """
        designs = self.STUDY_DESIGNS.get(study_type, [])

        if feasibility == "high":
            # Prioritize RCTs and prospective studies
            return [
                d for d in designs if "trial" in d.lower() or "prospective" in d.lower()
            ]
        elif feasibility == "low":
            # Prioritize retrospective and registry studies
            return [
                d
                for d in designs
                if "retrospective" in d.lower() or "registry" in d.lower()
            ]
        else:
            return designs

    def validate_disease_entity(self, entity: str) -> Dict[str, Any]:
        """
        Validate disease entity against WHO 2022 and ICC 2022.

        Args:
            entity: Disease entity name

        Returns:
            Validation results with recommendations
        """
        entity_upper = entity.upper()

        # Check against known entities
        found_category = None
        for category, entities in self.DISEASE_ENTITIES.items():
            if category in entity_upper:
                found_category = category
                break

        validation = {
            "is_valid": found_category is not None,
            "category": found_category,
            "suggested_entities": [],
            "recommendations": [],
        }

        if not found_category:
            validation["recommendations"].append(
                "Specify exact WHO 2022 or ICC 2022 entity name"
            )
        else:
            validation["suggested_entities"] = self.DISEASE_ENTITIES[found_category][:5]

        # Check nomenclature
        if "BCR-ABL" in entity or "BCR/ABL" in entity:
            validation["recommendations"].append(
                "Use ISCN 2024 notation: BCR::ABL1 (not BCR-ABL or BCR/ABL)"
            )

        return validation

    def generate_literature_search_strategy(
        self, topic: ResearchTopic
    ) -> Dict[str, Any]:
        """
        Generate PubMed search strategy for topic.

        Args:
            topic: Research topic with PICO

        Returns:
            Search strategy with terms
        """
        pico = topic.pico

        # Population terms
        population_terms = self._extract_search_terms(pico.population)

        # Intervention terms
        intervention_terms = self._extract_search_terms(pico.intervention)

        # Outcome terms
        outcome_terms = self._extract_search_terms(pico.outcome)

        # Build search strings
        population_query = " OR ".join(
            [f'"{term}"[Title/Abstract]' for term in population_terms[:3]]
        )
        intervention_query = " OR ".join(
            [f'"{term}"[Title/Abstract]' for term in intervention_terms[:3]]
        )
        outcome_query = " OR ".join(
            [f'"{term}"[Title/Abstract]' for term in outcome_terms[:2]]
        )

        full_query = f"({population_query}) AND ({intervention_query})"
        if outcome_query:
            full_query += f" AND ({outcome_query})"

        return {
            "population_terms": population_terms,
            "intervention_terms": intervention_terms,
            "outcome_terms": outcome_terms,
            "pubmed_query": full_query,
            "expected_results": "50-500",
        }

    def _extract_search_terms(self, text: str) -> List[str]:
        """Extract search terms from text."""
        # Remove common stop words
        stop_words = {"with", "and", "or", "the", "of", "in", "for", "to", "a", "an"}

        words = re.findall(r"\b[A-Za-z][A-Za-z0-9\-:]+\b", text)
        terms = [w for w in words if w.lower() not in stop_words and len(w) > 2]

        return terms[:5]

    def export_topic_summary(self, topic: ResearchTopic) -> str:
        """Export topic as formatted summary."""
        lines = [
            "# Research Topic Summary",
            "",
            f"**Title:** {topic.title}",
            f"**Study Type:** {topic.study_type.value}",
            f"**Disease Entity:** {topic.disease_entity}",
            "",
            "## PICO Framework",
            "",
        ]

        for element, value in topic.pico.to_dict().items():
            lines.append(f"- **{element}:** {value}")

        lines.extend(
            [
                "",
                "## Research Question",
                f"{topic.pico.format_research_question()}",
                "",
                "## Keywords",
                ", ".join(topic.keywords) if topic.keywords else "[To be defined]",
            ]
        )

        if topic.clinical_significance:
            lines.extend(["", "## Clinical Significance", topic.clinical_significance])

        return "\n".join(lines)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 1: Topic Development Module")
    print("=" * 60)

    # Example usage
    manager = TopicDevelopmentManager()

    # Create PICO for AML study
    pico = manager.create_pico(
        population="Adults ≥60 years with newly diagnosed AML",
        intervention="Venetoclax + azacitidine",
        comparator="Intensive 7+3 chemotherapy",
        outcome="Overall survival at 2 years",
        study_design="Retrospective cohort comparison",
    )

    print("\nPICO Framework:")
    for element, value in pico.to_dict().items():
        print(f"  {element}: {value}")

    print(f"\nResearch Question:")
    print(f"  {pico.format_research_question()}")

    # Suggest populations
    print("\nSuggested Populations for AML:")
    for i, pop in enumerate(manager.suggest_population("AML"), 1):
        print(f"  {i}. {pop}")

    # Validate entity
    validation = manager.validate_disease_entity("AML with NPM1 mutation")
    print(f"\nValidation: {'✅ Valid' if validation['is_valid'] else '❌ Invalid'}")
    if validation["recommendations"]:
        print("Recommendations:")
        for rec in validation["recommendations"]:
            print(f"  - {rec}")
