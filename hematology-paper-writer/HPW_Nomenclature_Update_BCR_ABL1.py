"""
HPW Skill - BCR::ABL1 Fusion Gene Nomenclature Update
=====================================================
Update to use double colon (::) notation for fusion genes per HGVS 2024 / ISCN 2024.
"""

FUSION_GENE_NOTATION = {
    "correct_2024": {
        "BCR::ABL1": "Philadelphia chromosome fusion",
        "PML::RARA": "APL fusion",
        "RUNX1::RUNX1T1": "AML with t(8;21)",
        "CBFB::MYH11": "AML with inv(16)",
        "DEK::NUP214": "AML with t(6;9)",
        "MLLT3::KMT2A": "AML with t(9;11)",
        "ETV6::RUNX1": "B-ALL with t(12;21)",
    },
    "deprecated": [
        "BCR-ABL1",
        "PML-RARA", 
        "RUNX1-RUNX1T1",
        "CBFB-MYH11",
        "BCR/ABL",
        "PML/RARA",
    ]
}


def generate_nomenclature_template():
    template = """
## Fusion Gene Nomenclature (HGVS 2024 / ISCN 2024)

Per HGVS 2024 recommendations and ISCN 2024 guidelines, fusion genes should be denoted using **double colons (::)** with italicized gene symbols.

### Correct Format

| Fusion | Correct Notation | Cytogenetic Abnormality |
|--------|-----------------|------------------------|
| Philadelphia | *BCR::ABL1* | t(9;22)(q34;q11) |
| APL | *PML::RARA* | t(15;17)(q22;q12) |
| AML with eosinophilia | *CBFB::MYH11* | inv(16)(p13.1q22) |
| AML with t(8;21) | *RUNX1::RUNX1T1* | t(8;21)(q22;q22) |
| AML with t(6;9) | *DEK::NUP214* | t(6;9)(p23;q34) |
| AML with t(9;11) | *MLLT3::KMT2A* | t(9;11)(p21.3;q23.3) |
| B-ALL with t(12;21) | *ETV6::RUNX1* | t(12;21)(p13;q22) |

### Deprecated Formats (Do Not Use)

| Deprecated | Use Instead |
|------------|-------------|
| BCR-ABL1 | *BCR::ABL1* |
| PML-RARA | *PML::RARA* |
| RUNX1-RUNX1T1 | *RUNX1::RUNX1T1* |
| CBFB-MYH11 | *CBFB::MYH11* |
| BCR/ABL | *BCR::ABL1* |

### Manuscript Examples

**Correct:**
> Cytogenetic analysis revealed the Philadelphia chromosome with the *BCR::ABL1* fusion gene in 95% of metaphases. RT-PCR confirmed the e1a2 transcript.

**Incorrect:**
> The BCR-ABL1 fusion was detected by FISH.

### Key Points

1. **Double Colon (::)** - HGVS 2024 uses :: to denote gene fusions
2. **Italics** - Gene symbols should be italicized: *BCR::ABL1*
3. **Reference Sequences** - Include transcript variants when relevant
4. **Consistency** - Use same format throughout manuscript
"""
    return template


if __name__ == "__main__":
    print("=" * 70)
    print("HPW NOMENCLATURE UPDATE - BCR::ABL1 Format")
    print("=" * 70)
    
    print("\nCorrect Format (HGVS 2024 / ISCN 2024):")
    for fusion, desc in FUSION_GENE_NOTATION["correct_2024"].items():
        print("  *{}* - {}".format(fusion, desc))
    
    print("\nDeprecated Formats (Do Not Use):")
    for dep in FUSION_GENE_NOTATION["deprecated"]:
        print("  {}".format(dep))
