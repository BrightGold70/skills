"""
Hematology Clinical Guidelines Module
====================================

Comprehensive clinical guidelines for hematology research and manuscript preparation.
Includes AML/CML diagnosis, classification, risk grouping, response evaluation, 
and GvHD evaluation/grading.

Based on:
- ELN 2022 AML Recommendations
- ELN 2025 CML Recommendations  
- WHO 2022 International Consensus Classification
- WHO 5th Edition Classification (2022)
- NIH Consensus Development Project on Chronic GVHD (2005-2021)

"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime


# ============================================================================
# ENUMS
# ============================================================================

class AMLClassification(Enum):
    """AML classification systems."""
    WHO_2022 = "who_2022"
    ICC_2022 = "icc_2022"
    ELN_2022 = "eln_2022"


class CMLPhase(Enum):
    """CML disease phases."""
    CHRONIC_PHASE = "chronic_phase"
    ACCELERATED_PHASE = "accelerated_phase"
    BLAST_PHASE = "blast_phase"


class CMLRiskScore(Enum):
    """CML risk stratification scores."""
    SOKAL = "sokal"
    HASFORD = "hasford"
    ELTS = "elts"


class GvHDSeverity(Enum):
    """GvHD severity grading."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class GvHDOrgan(Enum):
    """GvHD affected organs."""
    SKIN = "skin"
    LIVER = "liver"
    GASTROINTESTINAL = "gi"
    LUNG = "lung"
    EYE = "eye"
    MOUTH = "mouth"
    GENITAL = "genital"
    MUSCULOSKELETAL = "musculoskeletal"
    HEMATOPOIETIC = "hematopoietic"
    NEUROLOGIC = "neurologic"


class ResponseCategory(Enum):
    """Treatment response categories."""
    COMPLETE_REMISSION = "CR"
    PARTIAL_REMISSION = "PR"
    MINIMAL_RESIDUAL_DISEASE_NEGATIVE = "MRD_negative"
    MOLECULAR_RESPONSE = "molecular"
    CYTOGENETIC_RESPONSE = "cytogenetic"
    HEMATOLOGIC_RESPONSE = "hematologic"


# ============================================================================
# AML GUIDELINES (ELN 2022)
# ============================================================================

@dataclass
class AMLDiagnosticCriteria:
    """ELN 2022 AML diagnostic criteria."""
    
    # Required for AML diagnosis
    BLASTS_BM_PERCENT: int = 20  # >=20% blasts required for most AML
    BLASTS_PB_PERCENT: int = 20  # Peripheral blood blast threshold
    
    # AML-defining genetic abnormalities (any % blasts)
    AML_DEFINING_ABNORMALITIES: List[str] = field(default_factory=lambda: [
        "t(8;21)(q22;q22); RUNX1::RUNX1T1",
        "inv(16)(p13.1q22) or t(16;16)(p13.1;q22); CBFB::MYH11",
        "t(15;17)(q22;q12); PML::RARA",
        "t(9;11)(p21.3;q23.3); MLLT3::KMT2A",
        "t(6;9)(p23;q34.1); DEK::NUP214",
        "inv(3)(q21.3q26.2) or t(3;3)(q21.3;q26.2); GATA2::MECOM",
        "t(8;16)(p11;p13); KAT6A::CREBBP",
        "t(9;22)(q34.1;q11.2); BCR::ABL1",
        "t(4;11)(q21.3;q23.3); MLLT3::KMT2A",
        "t(11;19)(q23.3;p13.3); KMT2A::MLLT1",
        "t(6;11)(q27;q23.3); MLLT4::KMT2A",
        "t(7;12)(q36.3;p13.2); ETV6::MNX1",
        "t(17;19)(q23;p13.3); TCF3::HLF",
        "BCR::ABL1",
        "DEK::NUP214",
        "GATA2::MECOM",
        "KAT6A::CREBBP",
        "MNX1::ETV6",
        "NUP98::KDM5A",
        "RARA::PML",
    ])
    
    # AML with defining mutations (any % blasts)
    AML_DEFINING_MUTATIONS: List[str] = field(default_factory=lambda: [
        "TP53 mutated, AML",
        "NPHP1::CHD2",
        "NUP98::KDM5A",
        "NUP98::NSD1",
    ])


@dataclass  
class ELN2022RiskGroup:
    """ELN 2022 AML risk groups based on genetics."""
    
    FAVORABLE: List[str] = field(default_factory=lambda: [
        "NPM1 mut (no FLT3-ITD or FLT3-ITD low AR)",
        "CEBPA bZIP mutations (biallelic)",
        "t(8;21)(q22;q22); RUNX1::RUNX1T1",
        "inv(16)(p13.1q22) or t(16;16); CBFB::MYH11",
    ])
    
    INTERMEDIATE: List[str] = field(default_factory=lambda: [
        "NPM1 mut with FLT3-ITD high AR",
        "FLT3-ITD (no NPM1 mutation)",
        "NPM1 wild-type (no FLT3-ITD)",
        "t(9;11)(p21.3;q23.3); MLLT3::KMT2A",
        "Cytogenetic abnormalities not classified",
    ])
    
    ADVERSE: List[str] = field(default_factory=lambda: [
        "Complex karyotype (>=3 abnormalities)",
        "Monosomal karyotype",
        "t(6;9)(p23;q34.1); DEK::NUP214",
        "inv(3)(q21.3q26.2)/t(3;3)(q21.3;q26.2); GATA2::MECOM",
        "t(9;22)(q34.1;q11.2); BCR::ABL1",
        "t(4;11)(q21.3;q23.3); MLLT3::KMT2A",
        "t(8;16)(p11;p13); KAT6A::CREBBP",
        "t(7;12)(q36.3;p13.2); ETV6::MNX1",
        "t(17;19)(q23;p13.3); TCF3::HLF",
        "TP53 mutated (any karyotype)",
        "ASXL1 mutation",
        "BCOR mutation",
        "EZH2 mutation",
        "SF3B1 mutation",
        "SRSF2 mutation",
        "STAG2 mutation",
        "U2AF1 mutation",
        "ZRSR2 mutation",
        "KDM6A mutation",
    ])


# ============================================================================
# CML GUIDELINES (ELN 2025)
# ============================================================================

@dataclass
class CMLDiagnosticCriteria:
    """ELN 2025 CML diagnostic criteria."""
    
    REQUIRED_FOR_CML_DIAGNOSIS: Dict[str, Any] = field(default_factory=lambda: {
        "Philadelphia chromosome": True,
        "BCR::ABL1 fusion gene": True,
        "WHO criteria": "Presence of Ph+ and/or BCR::ABL1+",
        "chronic_phase": {
            "blasts_PB": "<2%",
            "blasts_BM": "<5%", 
            "basophils": "<20%",
            "promyelocytes_PB": "Variable",
            "WBC": "Typically elevated"
        }
    })
    
    ACCELERATED_PHASE_CRITERIA: List[str] = field(default_factory=lambda: [
        "Blasts 10-19% in PB or BM",
        "Basophils >=20% in PB",
        "Platelets <100 x 10^9/L unrelated to therapy",
        "Platelets >1000 x 10^9/L unresponsive to therapy",
        "Additional cytogenetic abnormalities in Ph+ cells",
        "Major route abnormalities (second Ph, i(17q), +8)",
        "Minor route abnormalities (-7, +21, +19, -Y)",
        "New clonal evolution"
    ])
    
    BLAST_PHASE_CRITERIA: List[str] = field(default_factory=lambda: [
        "Blasts >=20% in PB or BM",
        "Extramedullary blast proliferation",
        "Large foci or clusters of blasts in BM biopsy"
    ])


@dataclass
class CMLRiskScores:
    """CML risk stratification scores."""
    
    SOKAL: Dict[str, Any] = field(default_factory=lambda: {
        "formula": "Exp(0.0116 x (age - 43.4)) + 0.0345 x (spleen - 7.51) + 0.188 x ((platelets/700)^2 - 0.563) + 0.0887 x (blasts - 2.10)",
        "low": "<0.8",
        "intermediate": "0.8-1.2", 
        "high": ">1.2"
    })
    
    HASFORD: Dict[str, Any] = field(default_factory=lambda: {
        "formula": "0.666 when age >=50 + (0.042 x spleen) + 1.0956 x (platelets/700) + 0.0584 x (blasts) + 0.0413 x (eosinophils) + 0.2039 x (basophils) x 100",
        "low": "<=780",
        "intermediate": "781-1480",
        "high": ">1480"
    })
    
    ELTS: Dict[str, Any] = field(default_factory=lambda: {
        "formula": "0.0025 x (age/10)^3 + 0.0615 x (spleen/10) + 0.1052 x (platelets/1000) + 0.4104 x (blasts/10) x 1000",
        "low": "<=1.5680",
        "intermediate": "1.5681-2.2165",
        "high": ">2.2165"
    })


@dataclass
class CMLResponseCriteria:
    """ELN 2025 CML treatment response criteria."""
    
    HEMATOLOGIC_RESPONSE: Dict[str, str] = field(default_factory=lambda: {
        "complete": "CHR",
        "WBC": "<10 x 10^9/L",
        "neutrophils": ">=1.5 x 10^9/L", 
        "platelets": "<450 x 10^9/L",
        "blasts": "<1% in PB",
        "basophils": "<5%",
        "no_immature_cells": "No premature granulocytes",
        "spleen": "Not palpable"
    })
    
    CYTOGENETIC_RESPONSE: Dict[str, str] = field(default_factory=lambda: {
        "complete_ccy": "0% Ph+ metaphases (CCyR)",
        "partial_pcy": "1-35% Ph+ metaphases (PCyR)",
        "minor_mcy": "36-65% Ph+ metaphases",
        "minimal_mincy": "66-95% Ph+ metaphases",
        "none_nocy": ">95% Ph+ metaphases"
    })
    
    MOLECULAR_RESPONSE: Dict[str, str] = field(default_factory=lambda: {
        "MR4": "BCR::ABL1 <=0.01% (IS)",
        "MR4.5": "BCR::ABL1 <=0.0032% (IS)",
        "MR5": "BCR::ABL1 <=0.001% (IS)",
        "complete_CMR": "Undetectable BCR::ABL1 transcript",
        "major_MMR": "BCR::ABL1 <=0.1% (IS)"
    })
    
    RESPONSE_MILESTONES_MONTHS: Dict[str, Dict] = field(default_factory=lambda: {
        "3_months": {
            "CHR": "Required",
            "BCR::ABL1_IS": "Preferably <=10%",
            "Ph+_metaphases": "<65%",
            "notes": "Failure if no CHR or BCR::ABL1 >100%"
        },
        "6_months": {
            "BCR::ABL1_IS": "<1% (PCyR)",
            "Ph+_metaphases": "<35%",
            "notes": "Warning if BCR::ABL1 1-10%"
        },
        "12_months": {
            "BCR::ABL1_IS": "<0.1% (MMR/CCyR)",
            "notes": "Warning if BCR::ABL1 0.1-1%"
        },
        "18_months": {
            "BCR::ABL1_IS": "MR4.0 desirable",
            "notes": "Warning if BCR::ABL1 >0.01%"
        }
    })


# ============================================================================
# WHO 2022 / ICC 2022 CLASSIFICATION
# ============================================================================

@dataclass
class MyeloidNeoplasmClassification:
    """WHO 2022 and ICC 2022 myeloid neoplasm classification."""
    
    AML_CATEGORIES: Dict[str, List[str]] = field(default_factory=lambda: {
        "AML_with_defining_genetic_abnormalities": [
            "AML with t(8;21)(q22;q22); RUNX1::RUNX1T1",
            "AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22); CBFB::MYH11",
            "AML with t(15;17)(q22;q12); PML::RARA",
            "AML with t(9;11)(p21.3;q23.3); MLLT3::KMT2A",
            "AML with t(6;9)(p23;q34.1); DEK::NUP214",
            "AML with inv(3)(q21.3q26.2)/t(3;3)(q21.3;q26.2); GATA2, MECOM",
            "AML with t(8;16)(p11;p13); KAT6A::CREBBP",
            "AML with t(9;22)(q34.1;q11.2); BCR::ABL1",
            "AML with t(4;11)(q21.3;q23.3); MLLT3::KMT2A",
            "AML with t(11;19)(q23.3;p13.3); KMT2A::MLLT1",
            "AML with t(7;12)(q36.3;p13.2); ETV6::MNX1",
            "AML with t(17;19)(q23;p13.3); TCF3::HLF",
        ],
        "AML_with_morphologic_definitions": [
            "AML with mutated NPM1",
            "AML with mutated CEBPA (biallelic)",
            "AML, myelodysplasia-related",
        ],
        "AML_defined_by_differentiation": [
            "AML, not otherwise specified (NOS)",
            "AML with minimal differentiation",
            "AML without maturation", 
            "AML with maturation",
            "Acute myelomonocytic leukemia",
            "Acute monoblastic/monocytic leukemia",
            "Acute erythroid leukemia",
            "Acute megakaryoblastic leukemia",
        ],
        "myeloid_proliferations_associated_down_syndrome": [
            "Transient abnormal myelopoiesis (TAM)",
            "Myeloid leukemia associated with Down syndrome",
        ]
    })
    
    MDS_CATEGORIES: Dict[str, str] = field(default_factory=lambda: {
        "MDS-LB": "MDS with low blasts (blasts <5% BM)",
        "MDS-IB": "MDS with increased blasts (blasts 5-19% BM)",
        "MDS-F": "MDS with ring sideroblasts (>=15%)",
        "MDS-SF3B1": "MDS with SF3B1 mutation",
        "MDS-LD": "MDS with single lineage dysplasia",
        "MDS-MLD": "MDS with multilineage dysplasia",
        "MDS-5q": "MDS with isolated del(5q)",
        "MDS-U": "MDS, unclassifiable"
    })
    
    MPN_CATEGORIES: List[str] = field(default_factory=lambda: [
        "Chronic myeloid leukemia (CML)",
        "Chronic neutrophilic leukemia (CNL)",
        "Polycythemia vera (PV)",
        "Essential thrombocythemia (ET)",
        "Primary myelofibrosis (PMF)",
        "Mastocytosis (including systemic mastocytosis)",
        "Chronic eosinophilic leukemia, NOS (CEL-NOS)",
        "Myeloproliferative neoplasm, unclassifiable (MPN-U)"
    ])


# ============================================================================
# NIH CHRONIC GVHD GUIDELINES
# ============================================================================

@dataclass
class ChronicGVHDDiagnosis:
    """NIH Consensus chronic GvHD diagnosis criteria."""
    
    DIAGNOSTIC_CRITERIA: Dict[str, List[str]] = field(default_factory=lambda: {
        "skin": [
            "Poikiloderma",
            "Lichen planus-like features",
            "Sclerotic features",
            "Morphea-like features",
            "Lichen sclerosus-like features"
        ],
        "mouth": [
            "Lichen planus-like changes",
            "Hyposalivation/Xerostomia",
            "Mucous membrane pseudomembranes/ulcers",
            "Restrictive trismus"
        ],
        "gastrointestinal": [
            "Esophageal web",
            "Strictures or stenosis in upper third",
            "Pancreatic insufficiency"
        ],
        "liver": [
            "Hepatitis by biochemical testing",
            "Sclerosing cholangitis",
            "Cirrhosis"
        ],
        "lung": [
            "Bronchiolitis obliterans syndrome (BOS)",
            "Restrictive lung disease"
        ],
        "eye": [
            "New dry, gritty, or painful eyes",
            "Sicca syndrome",
            "Bulbar conjunctival hyperemia",
            "Corneal erosions"
        ],
        "genital": [
            "Lichen planus-like features",
            "Vaginal scarring/stenosis",
            "Ulcers"
        ],
        "musculoskeletal": [
            "Fascial involvement",
            "Joint stiffness/fibrosis",
            "Contractures"
        ],
        "hematopoietic": [
            "Immune thrombocytopenia",
            "Autoimmune hemolytic anemia"
        ]
    })
    
    DISTINCTIVE_FEATURES: Dict[str, str] = field(default_factory=lambda: {
        "pathognomonic": "Poikiloderma (skin)",
        "diagnostic": [
            "Lichen planus-like features (skin, mouth)",
            "Sclerotic features (skin)",
            "Morphea-like features (skin)",
            "Lichen sclerosus-like features (genital)",
            "Esophageal web (GI)",
            "Strictures/stenosis upper 1/3 esophagus (GI)",
            "Bronchiolitis obliterans syndrome (lung)"
        ],
        "common_features": [
            "Sicca syndrome (eye)",
            "Xerostomia (mouth)",
            "Vaginal stenosis (genital)",
            "Joint contractures (musculoskeletal)"
        ]
    })


@dataclass
class ChronicGVHDGrading:
    """NIH chronic GvHD severity grading."""
    
    ORGAN_SEVERITY_SCORE: Dict[str, str] = field(default_factory=lambda: {
        "skin_0": "0",
        "skin_1": "1-18% BSA involved without sclerotic features",
        "skin_2": "19-50% BSA involved OR superficial sclerotic features",
        "skin_3": ">50% BSA involved OR deep sclerotic features",
        "mouth_1": "Mild symptoms with signs",
        "mouth_2": "Moderate symptoms with signs",
        "mouth_3": "Severe symptoms with signs",
        "liver_1": "Bilirubin 2-3x ULN, AST/ALT 2-5x ULN",
        "liver_2": "Bilirubin 3-6x ULN, AST/ALT 5-10x ULN",
        "liver_3": "Bilirubin >6x ULN",
        "gi_1": "Mild symptoms (weight loss <15%)",
        "gi_2": "Moderate symptoms (weight loss 15-25%)",
        "gi_3": "Severe symptoms (weight loss >25%)",
        "lung_1": "FEV1 60-79% predicted",
        "lung_2": "FEV1 40-59% predicted",
        "lung_3": "FEV1 <40% predicted"
    })
    
    OVERALL_SEVERITY: Dict[str, Dict] = field(default_factory=lambda: {
        "mild": {
            "description": "1-2 organs involved, no organ with score >1",
            "1-year_NRM": "<5%",
            "treatment": "Topical/systemic corticosteroids"
        },
        "moderate": {
            "description": "3+ organs involved OR any organ with score >=2",
            "1-year_NRM": "5-15%",
            "treatment": "Systemic immunosuppression"
        },
        "severe": {
            "description": "Any organ score = 3 OR lung involvement with FEV1 <40%",
            "1-year_NRM": ">15%",
            "treatment": "Aggressive combination therapy"
        }
    })


@dataclass
class ChronicGVHDResponseAssessment:
    """NIH chronic GvHD response assessment."""
    
    RESPONSE_CATEGORIES: Dict[str, str] = field(default_factory=lambda: {
        "complete_response": "CR",
        "partial_response": "PR", 
        "stable_disease": "SD",
        "progressive_disease": "PD",
        "not_evaluable": "NE"
    })
    
    ORGAN_RESPONSE: Dict[str, str] = field(default_factory=lambda: {
        "complete": "Return to baseline organ function",
        "improved": "At least one organ score improved by >=1 without others worsening",
        "stable": "No change in organ scores",
        "worsened": "Any organ score increased by >=1"
    })


@dataclass
class AcuteGVHDGrading:
    """Acute GvHD grading (IBMTR/NIH)."""
    
    STAGE_CRITERIA: Dict[str, Dict] = field(default_factory=lambda: {
        "skin": {
            "stage_1": "Rash <25% BSA",
            "stage_2": "Rash 25-50% BSA",
            "stage_3": "Rash >50% BSA",
            "stage_4": "Generalized erythroderma + bullae"
        },
        "liver": {
            "stage_0": "Bilirubin <2 mg/dL",
            "stage_1": "Bilirubin 2-3 mg/dL",
            "stage_2": "Bilirubin 3-6 mg/dL",
            "stage_3": "Bilirubin >6 mg/dL",
            "stage_4": "Bilirubin >15 mg/dL"
        },
        "gut": {
            "stage_0": "No symptoms",
            "stage_1": "Diarrhea 500-1000 mL/day",
            "stage_2": "Diarrhea 1000-1500 mL/day", 
            "stage_3": "Diarrhea >1500 mL/day",
            "stage_4": "Severe abdominal pain with ileus"
        }
    })
    
    OVERALL_GRADE: Dict[str, str] = field(default_factory=lambda: {
        "grade_I": "Skin stage 1-2 only",
        "grade_II": "Skin stage 1-2 + GI stage 1 OR liver stage 1",
        "grade_III": "GI stage 2-3 OR liver stage 2-3",
        "grade_IV": "GI stage 4 OR liver stage 4 OR skin stage 4"
    })


# ============================================================================
# RESPONSE EVALUATION CRITERIA
# ============================================================================

@dataclass
class ResponseEvaluation:
    """Standard response evaluation criteria."""
    
    AML_RESPONSE: Dict[str, Dict] = field(default_factory=lambda: {
        "complete_remission_CR": {
            "BM_blasts": "<5%",
            "PB_blasts": "<1% (no blasts with Auer rods)",
            "ANC": ">=1.0 x 10^9/L",
            "Platelets": ">=100 x 10^9/L",
            "No_extramedullary": "No extramedullary disease"
        },
        "CRi_CRi": {
            "BM_blasts": "<5%",
            "PB_blasts": "<1%",
            "ANC": "<1.0 x 10^9/L OR platelets <100 x 10^9/L"
        },
        "partial_remission_PR": {
            "BM_blasts": ">=50% decrease to 5-25%",
            "PB_blasts": ">=50% decrease"
        },
        "stable_disease_SD": {
            "Not_CR": "Does not meet CR/CRi/PR criteria",
            "Not_PD": "No increase in blast percentage"
        },
        "progressive_disease_PD": {
            "Blasts_increase": ">=50% increase in BM/PB blasts",
            "New_lesions": "New extramedullary disease"
        }
    })
    
    MRD_RESPONSE: Dict[str, Dict] = field(default_factory=lambda: {
        "MRD_negative": {
            "flow_cytometry": "<1 x 10^-4 cells (0.01%)",
            "molecular": "BCR::ABL1 <0.01% IS",
            "NPM1": "NPM1 mutation negative by PCR"
        },
        "MRD_positive": {
            "flow": ">=0.1% by flow cytometry",
            "molecular": "Detectable mutations above threshold"
        }
    })


# ============================================================================
# MAIN GUIDELINES CLASS
# ============================================================================

class HematologyGuidelines:
    """
    Comprehensive hematology guidelines for manuscript preparation.
    
    Access guidelines using:
    - guidelines.aml (ELN 2022 AML criteria)
    - guidelines.cml (ELN 2025 CML criteria) 
    - guidelines.gvhd (NIH chronic GvHD criteria)
    - guidelines.classification (WHO/ICC classification)
    """
    
    def __init__(self):
        """Initialize guidelines module."""
        self.aml_diagnosis = AMLDiagnosticCriteria()
        self.aml_risk = ELN2022RiskGroup()
        self.cml_diagnosis = CMLDiagnosticCriteria()
        self.cml_risk = CMLRiskScores()
        self.cml_response = CMLResponseCriteria()
        self.classification = MyeloidNeoplasmClassification()
        self.gvhd_diagnosis = ChronicGVHDDiagnosis()
        self.gvhd_grading = ChronicGVHDGrading()
        self.gvhd_response = ChronicGVHDResponseAssessment()
        self.agvhd_grading = AcuteGVHDGrading()
        self.response = ResponseEvaluation()
    
    def get_aml_risk_group(self, abnormalities: List[str]) -> str:
        """
        Determine ELN 2022 AML risk group based on abnormalities.
        
        Args:
            abnormalities: List of genetic abnormalities
            
        Returns:
            Risk group: 'favorable', 'intermediate', or 'adverse'
        """
        for abn in abnormalities:
            if abn in self.aml_risk.ADVERSE:
                return "adverse"
        for abn in abnormalities:
            if abn in self.aml_risk.INTERMEDIATE:
                return "intermediate"
        for abn in abnormalities:
            if abn in self.aml_risk.FAVORABLE:
                return "favorable"
        return "intermediate"
    
    def get_cml_phase(self, blasts: float, basophils: float, 
                      platelets: int, cytogenetics: List[str] = None) -> str:
        """
        Determine CML disease phase.
        
        Args:
            blasts: Peripheral blood/bone marrow blast percentage
            basophils: Peripheral blood basophil percentage
            platelets: Platelet count
            cytogenetics: List of cytogenetic abnormalities
            
        Returns:
            CML phase: 'chronic', 'accelerated', or 'blast'
        """
        if blasts >= 20:
            return "blast_phase"
        elif (blasts >= 10 or basophils >= 20 or 
              platelets < 100 or platelets > 1000):
            return "accelerated_phase"
        return "chronic_phase"
    
    def format_risk_score(self, score_type: str, value: float) -> Dict:
        """Format CML risk score with interpretation."""
        if score_type == "sokal":
            return {
                "value": value,
                "interpretation": "low" if value < 0.8 else ("intermediate" if value <= 1.2 else "high"),
                "range": {"low": "<0.8", "intermediate": "0.8-1.2", "high": ">1.2"}
            }
        elif score_type == "hasford":
            return {
                "value": value,
                "interpretation": "low" if value <= 780 else ("intermediate" if value <= 1480 else "high"),
                "range": {"low": "<=780", "intermediate": "781-1480", "high": ">1480"}
            }
        elif score_type == "elts":
            return {
                "value": value,
                "interpretation": "low" if value <= 1.568 else ("intermediate" if value <= 2.2165 else "high"),
                "range": {"low": "<=1.5680", "intermediate": "1.5681-2.2165", "high": ">2.2165"}
            }
        return {"error": "Unknown score type"}
    
    def get_agvhd_grade(self, skin: int, liver: int, gut: int) -> Dict:
        """
        Calculate acute GvHD overall grade.
        
        Args:
            skin: Skin stage (0-4)
            liver: Liver stage (0-4)
            gut: Gut stage (0-4)
            
        Returns:
            Dict with grade and clinical interpretation
        """
        if skin >= 1 and liver == 0 and gut == 0:
            return {"grade": "I", "clinical": "Mild"}
        elif skin >= 1 and (gut <= 2 or liver <= 1):
            return {"grade": "II", "clinical": "Moderate"}
        elif gut >= 2 or liver >= 2:
            return {"grade": "III", "clinical": "Severe"}
        elif gut >= 3 or liver >= 3 or skin >= 4:
            return {"grade": "IV", "clinical": "Life-threatening"}
        return {"grade": "0", "clinical": "No acute GvHD"}
    
    def format_guidelines_for_manuscript(self, section: str) -> str:
        """
        Get formatted guidelines text for manuscript sections.
        
        Args:
            section: 'aml_diagnosis', 'cml_response', 'gvhd_grading', etc.
            
        Returns:
            Formatted text for inclusion in manuscript
        """
        formatters = {
            "aml_diagnosis": self._format_aml_diagnosis,
            "aml_risk": self._format_aml_risk,
            "cml_diagnosis": self._format_cml_diagnosis,
            "cml_response": self._format_cml_response,
            "cml_risk": self._format_cml_risk,
            "gvhd_diagnosis": self._format_gvhd_diagnosis,
            "gvhd_grading": self._format_gvhd_grading,
            "agvhd_grading": self._format_agvhd_grading,
        }
        
        if section in formatters:
            return formatters[section]()
        return f"Unknown section: {section}"
    
    def _format_aml_diagnosis(self) -> str:
        return """
## AML Diagnostic Criteria (ELN 2022)

AML was diagnosed according to the ELN 2022 recommendations.

### Required Criteria
- Bone marrow blasts >=20%, OR
- Presence of AML-defining genetic abnormalities (any blast percentage)

### AML-Defining Genetic Abnormalities
- t(8;21)(q22;q22); RUNX1::RUNX1T1
- inv(16)(p13.1q22) or t(16;16)(p13.1;q22); CBFB::MYH11
- t(15;17)(q22;q12); PML::RARA
- t(9;11)(p21.3;q23.3); MLLT3::KMT2A
- t(6;9)(p23;q34.1); DEK::NUP214
- inv(3)(q21.3q26.2) or t(3;3)(q21.3;q26.2); GATA2::MECOM
- t(8;16)(p11;p13); KAT6A::CREBBP
- t(9;22)(q34.1;q11.2); BCR::ABL1
- TP53-mutated AML
"""
    
    def _format_aml_risk(self) -> str:
        return """
## ELN 2022 Risk Stratification (AML)

### Favorable Risk
- NPM1 mutated without FLT3-ITD or with FLT3-ITD low allele ratio
- Biallelic CEBPA mutations (bZIP in-frame)
- t(8;21)(q22;q22); RUNX1::RUNX1T1
- inv(16)(p13.1q22) or t(16;16); CBFB::MYH11

### Intermediate Risk
- NPM1 mutated with FLT3-ITD high allele ratio
- FLT3-ITD without NPM1 mutation
- Wild-type NPM1 without FLT3-ITD

### Adverse Risk
- Complex karyotype (>=3 abnormalities)
- Monosomal karyotype
- TP53 mutation
- inv(3)(q21.3q26.2)/t(3;3)(q21.3;q26.2); GATA2::MECOM
"""
    
    def _format_cml_diagnosis(self) -> str:
        return """
## CML Diagnostic Criteria (ELN 2025)

CML was diagnosed according to the ELN 2025 recommendations.

### Required for Diagnosis
- Philadelphia chromosome positive (Ph+)
- BCR::ABL1 fusion gene detected

### Chronic Phase Criteria
- Blasts in PB: <2%
- Blasts in BM: <5%
- Basophils in PB: <20%
- Platelets: <1000 x 10^9/L

### Accelerated Phase Criteria
- Blasts 10-19% in PB or BM
- Basophils >=20% in PB
- Platelets <100 x 10^9/L unrelated to therapy
- Additional cytogenetic abnormalities in Ph+ cells

### Blast Phase Criteria
- Blasts >=20% in PB or BM
- Extramedullary blast proliferation
"""
    
def _format_cml_response(self) -> str:
        return """
## ELN 2025 CML Treatment Response Criteria

### Hematologic Response
- Complete hematologic response (CHR): WBC <10 x 10^9/L, Platelets <450 x 10^9/L, No blasts, Spleen not palpable

### Cytogenetic Response
- Complete (CCyR): 0% Ph+ metaphases
- Partial (PCyR): 1-35% Ph+ metaphases
- Minor: 36-65% Ph+ metaphases

### Molecular Response
- MMR (MR3.0): BCR::ABL1 <=0.1% (IS)
- MR4.0: BCR::ABL1 <=0.01% (IS)
- MR4.5: BCR::ABL1 <=0.0032% (IS)
- CMR: Undetectable BCR::ABL1 transcript

### Time-based Milestones
- 3 months: CHR required, BCR::ABL1 <=10% (IS)
- 6 months: BCR::ABL1 <1% (IS) [PCyR]
- 12 months: BCR::ABL1 <0.1% (IS) [MMR/CCyR]
"""

