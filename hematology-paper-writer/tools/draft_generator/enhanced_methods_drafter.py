from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ManuscriptType(Enum):
    CLASSIFICATION_STUDY = "classification"
    GVHD_STUDY = "gvhd"
    THERAPEUTIC_TRIAL = "therapeutic"
    PROGNOSTIC_STUDY = "prognostic"
    DIAGNOSTIC_STUDY = "diagnostic"


class ClassificationSystem(Enum):
    WHO_2022 = "WHO 2022 (5th edition)"
    ICC_2022 = "ICC 2022"
    BOTH = "Both WHO 2022 and ICC 2022"


class GVHDCriteria(Enum):
    MAGIC_ACUTE = "MAGIC criteria"
    NIH_CHRONIC = "NIH consensus criteria"
    BOTH = "Both MAGIC and NIH criteria"


@dataclass
class MethodsTemplate:
    section_title: str
    content: str
    required_elements: List[str] = field(default_factory=list)
    optional_elements: List[str] = field(default_factory=list)


class EnhancedManuscriptDrafter:
    CLASSIFICATION_METHODS_TEMPLATE = """### Study Population
Patients with suspected or confirmed {disease_entity} were enrolled between {start_date} and {end_date} at {site_description}. All diagnoses were confirmed using integrated morphologic, immunophenotypic, and molecular diagnostic assessment according to {classification_system}.

### Diagnostic Criteria
Disease classification followed {classification_system} criteria. Specific diagnostic requirements included:

**Morphologic Assessment:**
- Bone marrow aspirate and biopsy with {morphology_details}
- Blast enumeration on ≥500 nucleated cells
- Dysplasia assessment in ≥2 lineages

**Immunophenotyping:**
- Multiparameter flow cytometry (≥8 colors) using {panel_description}
- Blast gating strategy: {gating_strategy}
- Aberrant antigen expression patterns documented

**Cytogenetic Analysis:**
- Conventional karyotyping with ≥20 metaphases
- FISH panel for common abnormalities: {fish_panel}
- All cytogenetic abnormalities reported using ISCN 2024 nomenclature

**Molecular Studies:**
- Targeted NGS panel covering {gene_panel}
- Variant calling at {vaf_threshold} allele frequency
- Germline filtering using matched control samples

### Central Pathology Review
All diagnostic materials underwent central pathology review by {reviewer_description}. Inter-observer reproducibility was assessed using {reproducibility_method}."""

    GVHD_METHODS_TEMPLATE = """### Study Population
{patient_population} undergoing allogeneic hematopoietic cell transplantation at {site_description}.

### GVHD Assessment

**Acute GVHD:**
Assessment followed the Mount Sinai Acute GVHD International Consortium (MAGIC) criteria:

*Skin:*
- Stage 0-4 based on body surface area involvement and rash characteristics
- Maculopapular rash staging: {skin_staging}

*Liver:*
- Stage 0-4 based on total bilirubin levels (mg/dL)
- Staging criteria: {liver_staging}

*GI (Upper):*
- Stage 0-1 based on anorexia, nausea, and vomiting severity

*GI (Lower):*
- Stage 0-4 based on stool volume and diarrhea grade
- Daily stool volume: {stool_volume_criteria}

*Overall Grade:*
- Grade I-IV determined by composite organ involvement

**Chronic GVHD:**
Assessment followed the NIH Consensus Development Project criteria (2014):

*Organ Scoring (0-3 scale):*
- Skin: {skin_chronic_criteria}
- Mouth: {mouth_criteria}
- Eyes: {eyes_criteria}
- GI: {gi_criteria}
- Liver: {liver_chronic_criteria}
- Lungs: {lungs_criteria}

*Global Scoring:*
- Mild, moderate, or severe based on organ involvement

### GVHD Prophylaxis
{prophylaxis_description}

### Response Assessment
GVHD response was assessed at {timepoints} using standardized criteria:
- Complete response: Complete resolution of all signs/symptoms
- Partial response: ≥50% improvement without new organ involvement
- No response: <50% improvement or progression"""

    THERAPEUTIC_METHODS_TEMPLATE = """### Study Population
Patients with {disease} were eligible if they met the following criteria:

**Inclusion Criteria:**
{inclusion_criteria}

**Exclusion Criteria:**
{exclusion_criteria}

### Treatment Protocol
{treatment_description}

### Response Assessment
Response evaluation followed ELN {eln_version} recommendations:

**{disease} Response Criteria:**
{response_criteria}

**Timing of Assessments:**
- Bone marrow examination: {bm_timing}
- Molecular monitoring: {molecular_timing}
- Imaging studies: {imaging_timing}

### Statistical Analysis
{statistical_methods}"""

    NOMENCLATURE_COMPLIANCE_CHECKLIST = [
        "Gene symbols italicized: *NPM1*, *FLT3*, *TP53*, etc.",
        "Fusion genes use double colon: BCR::ABL1, RUNX1::RUNX1T1",
        "Cytogenetics follow ISCN 2024: t(9;22)(q34.1;q11.2)",
        "Molecular variants use HGVS: c.863A>G, p.Tyr288Cys",
        "Disease names follow WHO/ICC: 'AML with NPM1 mutation'",
        "Abbreviations defined at first use",
    ]

    def __init__(self):
        self.classification_data_elements = {
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

    def draft_classification_methods(
        self, disease_entity: str, classification_system: ClassificationSystem, **kwargs
    ) -> MethodsTemplate:
        content = self.CLASSIFICATION_METHODS_TEMPLATE.format(
            disease_entity=disease_entity,
            classification_system=classification_system.value,
            start_date=kwargs.get("start_date", "[start date]"),
            end_date=kwargs.get("end_date", "[end date]"),
            site_description=kwargs.get("site_description", "[participating centers]"),
            morphology_details=kwargs.get(
                "morphology_details", "[specific staining and assessment criteria]"
            ),
            panel_description=kwargs.get("panel_description", "[antibody panel]"),
            gating_strategy=kwargs.get("gating_strategy", "[gating approach]"),
            fish_panel=kwargs.get("fish_panel", "[FISH probes]"),
            gene_panel=kwargs.get("gene_panel", "[genes included]"),
            vaf_threshold=kwargs.get("vaf_threshold", "[VAF threshold]"),
            reviewer_description=kwargs.get(
                "reviewer_description", "[pathologist qualifications]"
            ),
            reproducibility_method=kwargs.get("reproducibility_method", "[method]"),
        )

        return MethodsTemplate(
            section_title="Methods - Classification Study",
            content=content,
            required_elements=list(self.classification_data_elements.keys()),
            optional_elements=[
                "Central pathology review",
                "Inter-observer reproducibility",
            ],
        )

    def draft_gvhd_methods(
        self, patient_population: str, site_description: str, **kwargs
    ) -> MethodsTemplate:
        content = self.GVHD_METHODS_TEMPLATE.format(
            patient_population=patient_population,
            site_description=site_description,
            skin_staging=kwargs.get(
                "skin_staging",
                "BSA <25% (Stage 1), 25-50% (Stage 2), >50% (Stage 3), generalized erythroderma (Stage 4)",
            ),
            liver_staging=kwargs.get(
                "liver_staging",
                "Bilirubin <2 (Stage 0), 2-3 (Stage 1), 3-6 (Stage 2), 6-15 (Stage 3), >15 (Stage 4) mg/dL",
            ),
            stool_volume_criteria=kwargs.get(
                "stool_volume_criteria",
                "<500 mL (Stage 0), 500-1000 mL (Stage 1), 1000-1500 mL (Stage 2), >1500 mL (Stage 3)",
            ),
            skin_chronic_criteria=kwargs.get(
                "skin_chronic_criteria",
                "Score based on lichen planus-like features, sclerotic features, and mobility restriction",
            ),
            mouth_criteria=kwargs.get(
                "mouth_criteria",
                "Score based on lichen planus features, ulcers, and mouth opening limitation",
            ),
            eyes_criteria=kwargs.get(
                "eyes_criteria",
                "Score based on Schirmer test and keratoconjunctivitis sicca",
            ),
            gi_criteria=kwargs.get(
                "gi_criteria",
                "Score based on weight loss, esophageal strictures, and dysphagia",
            ),
            liver_chronic_criteria=kwargs.get(
                "liver_chronic_criteria",
                "Score based on bilirubin elevation and cholestatic pattern",
            ),
            lungs_criteria=kwargs.get(
                "lungs_criteria", "Score based on FEV1 and pleural involvement"
            ),
            prophylaxis_description=kwargs.get(
                "prophylaxis_description", "[GVHD prophylaxis regimen details]"
            ),
            timepoints=kwargs.get(
                "timepoints", "Day 28, Day 56, and Day 100 post-transplant"
            ),
        )

        return MethodsTemplate(
            section_title="Methods - GVHD Study",
            content=content,
            required_elements=[
                "Acute GVHD assessment",
                "Chronic GVHD assessment",
                "Response criteria",
            ],
            optional_elements=["Biomarker collection", "Quality of life assessments"],
        )

    def draft_therapeutic_methods(
        self, disease: str, eln_version: str, **kwargs
    ) -> MethodsTemplate:
        content = self.THERAPEUTIC_METHODS_TEMPLATE.format(
            disease=disease,
            eln_version=eln_version,
            inclusion_criteria=kwargs.get("inclusion_criteria", "[inclusion criteria]"),
            exclusion_criteria=kwargs.get("exclusion_criteria", "[exclusion criteria]"),
            treatment_description=kwargs.get(
                "treatment_description", "[treatment protocol]"
            ),
            response_criteria=kwargs.get("response_criteria", "[response criteria]"),
            bm_timing=kwargs.get("bm_timing", "[timing of bone marrow assessments]"),
            molecular_timing=kwargs.get(
                "molecular_timing", "[timing of molecular monitoring]"
            ),
            imaging_timing=kwargs.get("imaging_timing", "[timing of imaging studies]"),
            statistical_methods=kwargs.get(
                "statistical_methods", "[statistical methods]"
            ),
        )

        return MethodsTemplate(
            section_title="Methods - Therapeutic Study",
            content=content,
            required_elements=[
                "Treatment protocol",
                "Response criteria",
                "Statistical analysis",
            ],
            optional_elements=["Subgroup analyses", "Interim analyses"],
        )

    def get_nomenclature_checklist(self) -> List[str]:
        return self.NOMENCLATURE_COMPLIANCE_CHECKLIST

    def validate_methods_section(
        self, methods_text: str, study_type: ManuscriptType
    ) -> Dict[str, Any]:
        issues = []
        warnings = []

        if study_type == ManuscriptType.CLASSIFICATION_STUDY:
            if "WHO" not in methods_text and "ICC" not in methods_text:
                issues.append(
                    "Classification system not specified (WHO 2022 or ICC 2022)"
                )
            if "ISCN" not in methods_text:
                warnings.append("ISCN nomenclature compliance not mentioned")
            if "central pathology" not in methods_text.lower():
                warnings.append("Central pathology review not mentioned")

        elif study_type == ManuscriptType.GVHD_STUDY:
            if "MAGIC" not in methods_text and "NIH" not in methods_text:
                issues.append("GVHD criteria not specified (MAGIC or NIH)")
            if "organ" not in methods_text.lower():
                warnings.append("Organ-specific assessment details may be missing")

        elif study_type == ManuscriptType.THERAPEUTIC_TRIAL:
            if "ELN" not in methods_text:
                warnings.append("ELN response criteria not mentioned")
            if "adverse event" not in methods_text.lower():
                warnings.append("Adverse event reporting not mentioned")

        nomenclature_issues = self._check_nomenclature_compliance(methods_text)

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "nomenclature_issues": nomenclature_issues,
        }

    def _check_nomenclature_compliance(self, text: str) -> List[str]:
        issues = []

        old_fusion_patterns = ["BCR-ABL1", "BCR/ABL", "PML-RARA", "RUNX1-RUNX1T1"]
        for pattern in old_fusion_patterns:
            if pattern in text:
                issues.append(
                    f"Old fusion notation '{pattern}' found - use double colon notation"
                )

        if re.search(r"\bNPM1\b(?![*])", text):
            issues.append("Gene symbol NPM1 should be italicized: *NPM1*")

        if "del(5)" in text and "del(5q)" not in text:
            issues.append("Incomplete cytogenetic notation - use del(5q)")

        return issues


import re


if __name__ == "__main__":
    drafter = EnhancedManuscriptDrafter()

    print("=" * 60)
    print("Enhanced Manuscript Drafter - Classification Methods")
    print("=" * 60)

    template = drafter.draft_classification_methods(
        disease_entity="AML with NPM1 mutation",
        classification_system=ClassificationSystem.WHO_2022,
        start_date="January 2020",
        end_date="December 2023",
        site_description="15 academic medical centers",
    )

    print(f"\n{template.section_title}")
    print("-" * 60)
    print(template.content[:500] + "...")
    print(f"\nRequired Elements: {len(template.required_elements)}")
    print(f"Optional Elements: {len(template.optional_elements)}")

    print("\n" + "=" * 60)
    print("Nomenclature Compliance Checklist:")
    print("=" * 60)
    for item in drafter.get_nomenclature_checklist():
        print(f"  □ {item}")
