from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class StudyDesignType(Enum):
    RANDOMIZED_CONTROLLED_TRIAL = "rct"
    COHORT_STUDY = "cohort"
    CASE_CONTROL = "case_control"
    CROSS_SECTIONAL = "cross_sectional"
    CASE_SERIES = "case_series"
    SINGLE_ARM = "single_arm"
    RETROSPECTIVE_CHART_REVIEW = "retrospective"
    REGISTRY_BASED = "registry"


class ClassificationSystem(Enum):
    WHO_2022 = "WHO 2022 (5th edition)"
    ICC_2022 = "ICC 2022"
    BOTH = "Both WHO 2022 and ICC 2022"


class GVHDCriteria(Enum):
    MAGIC_ACUTE = "MAGIC criteria (acute GVHD)"
    NIH_CHRONIC = "NIH consensus criteria (chronic GVHD)"
    BOTH_ACUTE_CHRONIC = "Both MAGIC and NIH criteria"


@dataclass
class SampleSizeCalculation:
    alpha: float = 0.05
    power: float = 0.80
    effect_size: Optional[float] = None
    estimated_sample_size: int = 0
    dropout_rate: float = 0.10
    final_sample_size: int = 0

    def calculate_with_dropout(self) -> int:
        if self.estimated_sample_size > 0:
            self.final_sample_size = int(
                self.estimated_sample_size / (1 - self.dropout_rate)
            )
        return self.final_sample_size


@dataclass
class StudyDesign:
    design_type: StudyDesignType = StudyDesignType.COHORT_STUDY
    title: str = ""
    primary_objective: str = ""
    secondary_objectives: List[str] = field(default_factory=list)
    primary_endpoint: str = ""
    secondary_endpoints: List[str] = field(default_factory=list)
    inclusion_criteria: List[str] = field(default_factory=list)
    exclusion_criteria: List[str] = field(default_factory=list)
    sample_size: SampleSizeCalculation = field(default_factory=SampleSizeCalculation)
    classification_system: Optional[ClassificationSystem] = None
    gvhd_criteria: Optional[GVHDCriteria] = None
    statistical_methods: List[str] = field(default_factory=list)
    data_collection_methods: List[str] = field(default_factory=list)
    quality_control_measures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_type": self.design_type.value,
            "title": self.title,
            "primary_objective": self.primary_objective,
            "secondary_objectives": self.secondary_objectives,
            "primary_endpoint": self.primary_endpoint,
            "secondary_endpoints": self.secondary_endpoints,
            "inclusion_criteria": self.inclusion_criteria,
            "exclusion_criteria": self.exclusion_criteria,
            "sample_size": {
                "alpha": self.sample_size.alpha,
                "power": self.sample_size.power,
                "estimated": self.sample_size.estimated_sample_size,
                "with_dropout": self.sample_size.final_sample_size,
            },
            "classification_system": self.classification_system.value
            if self.classification_system
            else None,
            "gvhd_criteria": self.gvhd_criteria.value if self.gvhd_criteria else None,
            "statistical_methods": self.statistical_methods,
        }


class StudyDesignManager:
    CLASSIFICATION_DATA_ELEMENTS = {
        "morphology": [
            "Bone marrow blast percentage",
            "Lineage dysplasia assessment",
            "Auer rod presence",
            "Multilineage dysplasia status",
        ],
        "immunophenotype": [
            "Flow cytometry panel (≥8 colors recommended)",
            "Blast gating strategy",
            "Aberrant antigen expression",
            "Lineage assignment markers",
        ],
        "cytogenetics": [
            "Karyotype analysis (≥20 metaphases)",
            "FISH for common abnormalities",
            "Complex karyotype definition (≥3 abnormalities)",
            "ISCN 2024 nomenclature compliance",
        ],
        "molecular": [
            "NGS panel coverage (myeloid genes)",
            "Mutation allele frequency threshold",
            "FLT3-ITD vs TKD distinction",
            "NPM1 mutation status",
        ],
    }

    GVHD_DATA_ELEMENTS = {
        "acute": {
            "skin": ["Stage 0-4", "BSA involvement %", "Maculopapular rash presence"],
            "liver": ["Stage 0-4", "Bilirubin mg/dL", "Jaundice presence"],
            "gi_upper": ["Stage 0-1", "Anorexia severity", "Nausea/vomiting grade"],
            "gi_lower": ["Stage 0-4", "Daily stool volume", "Diarrhea grade"],
            "overall": ["Grade I-IV", "Performance status"],
        },
        "chronic": {
            "skin": ["Score 0-3", "Mobility assessment", "Sclerotic features"],
            "mouth": ["Score 0-3", "Lichen planus features", "Mouth opening"],
            "eyes": ["Score 0-3", "Schirmer test", "KCS assessment"],
            "gi": ["Score 0-3", "Weight loss %", "Esophageal involvement"],
            "liver": ["Score 0-3", "Bilirubin", "Cholestatic pattern"],
            "lungs": ["Score 0-3", "FEV1", "Pleural involvement"],
        },
    }

    ELN_RESPONSE_CRITERIA = {
        "AML": {
            "CR": [
                "Bone marrow blasts <5%",
                "Absence of blasts with Auer rods",
                "ANC ≥1.0 × 10⁹/L",
                "Platelets ≥100 × 10⁹/L",
                "Transfusion independence",
            ],
            "CRi": [
                "All CR criteria except ANC <1.0 × 10⁹/L or Platelets <100 × 10⁹/L",
            ],
            "CRh": [
                "All CR criteria with ANC ≥0.5 × 10⁹/L and Platelets ≥50 × 10⁹/L",
            ],
            "MLFS": [
                "Bone marrow blasts 5-25%",
                "ANC ≥0.5 × 10⁹/L",
                "Platelets ≥50 × 10⁹/L",
            ],
        },
        "CML": {
            "CCyR": ["BCR::ABL1 IS 0% by FISH"],
            "MMR": ["BCR::ABL1 IS ≤0.1% by qPCR"],
            "MR4": ["BCR::ABL1 IS ≤0.01% by qPCR"],
            "MR4.5": ["BCR::ABL1 IS ≤0.0032% by qPCR"],
            "MR5": ["BCR::ABL1 IS ≤0.001% by qPCR"],
        },
    }

    def __init__(self):
        self.current_design: Optional[StudyDesign] = None
        self.design_history: List[StudyDesign] = []

    def create_classification_study_design(
        self,
        classification_system: ClassificationSystem,
        disease_entity: str,
        design_type: StudyDesignType = StudyDesignType.COHORT_STUDY,
    ) -> StudyDesign:
        design = StudyDesign(
            design_type=design_type,
            title=f"{disease_entity}: Classification and Outcomes",
            primary_objective=f"To characterize {disease_entity} using {classification_system.value} criteria",
            classification_system=classification_system,
        )

        design.data_collection_methods = [
            "Central pathology review",
            "Standardized morphology assessment",
            "Multi-parameter flow cytometry",
            "Conventional karyotyping",
            "Targeted NGS panel",
        ]

        design.quality_control_measures = [
            "Inter-observer reproducibility testing",
            "Reference laboratory validation",
            "Standardized reporting forms",
        ]

        self.current_design = design
        return design

    def create_gvhd_study_design(
        self,
        acute_criteria: GVHDCriteria,
        chronic_criteria: Optional[GVHDCriteria] = None,
        design_type: StudyDesignType = StudyDesignType.COHORT_STUDY,
    ) -> StudyDesign:
        design = StudyDesign(
            design_type=design_type,
            title="GVHD Assessment and Outcomes",
            primary_objective="To evaluate GVHD incidence, severity, and response",
            gvhd_criteria=acute_criteria,
        )

        design.data_collection_methods = [
            "Standardized organ assessment forms",
            "Serial photography (skin)",
            "Biomarker sample collection",
            "Quality of life assessments",
        ]

        design.quality_control_measures = [
            "Central adjudication of GVHD grades",
            "Training for site investigators",
            "Standardized timepoint assessments",
        ]

        self.current_design = design
        return design

    def create_therapeutic_study_design(
        self,
        disease: str,
        response_criteria: str,
        design_type: StudyDesignType = StudyDesignType.RANDOMIZED_CONTROLLED_TRIAL,
    ) -> StudyDesign:
        design = StudyDesign(
            design_type=design_type,
            title=f"{disease} Treatment Outcomes",
            primary_objective=f"To evaluate treatment efficacy using ELN {response_criteria} criteria",
        )

        design.data_collection_methods = [
            "Bone marrow assessments at specified intervals",
            "Molecular monitoring (qPCR for MRD)",
            "Adverse event collection (CTCAE v5.0)",
            "Concomitant medication tracking",
        ]

        design.quality_control_measures = [
            "Independent response adjudication",
            "Central laboratory for molecular testing",
            "Data safety monitoring board",
        ]

        self.current_design = design
        return design

    def get_classification_data_elements(self) -> Dict[str, List[str]]:
        return self.CLASSIFICATION_DATA_ELEMENTS

    def get_gvhd_data_elements(self, gvhd_type: str = "acute") -> Dict[str, List[str]]:
        return self.GVHD_DATA_ELEMENTS.get(gvhd_type, {})

    def get_response_criteria(self, disease: str) -> Dict[str, List[str]]:
        return self.ELN_RESPONSE_CRITERIA.get(disease.upper(), {})

    def generate_methods_section(self) -> str:
        if not self.current_design:
            return "No study design defined."

        design = self.current_design
        lines = [
            "## Methods",
            "",
            "### Study Design",
            f"This {design.design_type.value.replace('_', ' ')} study was conducted...",
            "",
            "### Classification",
        ]

        if design.classification_system:
            lines.append(
                f"Disease classification followed {design.classification_system.value}."
            )
            lines.append(
                "Diagnoses were confirmed using integrated morphologic, immunophenotypic,"
            )
            lines.append(
                "and molecular diagnostic assessment. Cytogenetic analysis followed ISCN 2024 nomenclature."
            )

        if design.gvhd_criteria:
            lines.append(f"GVHD was assessed using {design.gvhd_criteria.value}.")

        lines.extend(
            [
                "",
                "### Endpoints",
                f"The primary endpoint was {design.primary_endpoint or '[to be defined]'}.",
            ]
        )

        return "\n".join(lines)


if __name__ == "__main__":
    manager = StudyDesignManager()

    design = manager.create_classification_study_design(
        ClassificationSystem.WHO_2022,
        "AML with NPM1 mutation",
    )

    print("Classification Study Design Created")
    print(f"Design Type: {design.design_type.value}")
    print(f"Classification: {design.classification_system.value}")
    print()
    print("Data Elements Required:")
    for category, elements in manager.get_classification_data_elements().items():
        print(f"  {category}: {len(elements)} elements")
