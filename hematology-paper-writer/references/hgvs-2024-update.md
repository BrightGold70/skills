# HGVS 2024 Nomenclature Updates

## Summary of Key Changes from 2016 to 2024

### Major Revisions

1. **Somatic Variant Nomenclature**
   - Separate recommendations for somatic vs germline variants
   - Clear distinction in notation
   - Recommended databases: ClinVar, COSMIC, LOVD

2. **Copy Number Variations (CNVs)**
   - Updated CNV notation standards
   - Complex rearrangements handling
   - Reference sequence requirements

3. **Fusion Genes**
   - Standardized fusion gene nomenclature
   - Breakpoint notation improvements
   - Transcript designation rules

4. **Splicing Variants**
   - Enhanced splicing variant descriptions
   - Standardized intronic position numbering
   - Splice site notation updates

---

## 2024 HGVS Variant Types and Syntax

### DNA Level

#### Substitutions
```
c.123A>G         # Single nucleotide substitution
c.123_124delinsGG  # Substitution of 2 bases
```

#### Deletions
```
c.123del          # Single base deletion
c.123_456del      # Multi-base deletion (334bp)
c.123_456delinsT  # Deletion-insertion
```

#### Duplications
```
c.123dup          # Single base duplication
c.123_456dup      # Multi-base duplication
```

#### Insertions
```
c.123_124insABC   # Insertion of bases
```

#### Complex
```
c.123_456delinsTUV  # Deletion-insertion
```

### Protein Level

#### Substitutions
```
p.Val617Phe       # Using 3-letter code (RECOMMENDED)
p.V617F           # Using 1-letter code (acceptable)
```

#### Frameshifts
```
p.Gln424Hisfs*4   # Frameshift, new amino acid, stop at position 4
```

#### Truncating Variants
```
p.Tyr421*         # Stop codon, 3-letter
p.Y421*           # Stop codon, 1-letter
```

---

## Somatic Variant Nomenclature (2024 Update)

### Key Principles

1. **Separate Designation**
   - Use "somatic" qualifier when known
   - "c." notation for coding DNA variants
   - Include allelic fraction when available

2. **Variant Allele Frequency (VAF)**
   ```
   c.1794T>G;VAF=0.35  # Variant with allelic fraction
   ```

3. **Clonal Hematopoiesis Notation**
   ```
   c.101C>T;VAF=0.12;clone_size=15%  # With clonal context
   ```

4. **COSMIC Database Reference**
   ```
   COSM12345  # COSMIC database ID
   ```

### Fusion Gene Notation

| Fusion | Old Format | 2024 Format |
|--------|------------|-------------|
| BCR-ABL1 | BCR/ABL | *BCR-ABL1* (gene symbol italicized) |
| PML-RARA | PML/RARA | *PML-RARA* |
| RUNX1-RUNX1T1 | RUNX1/RUNX1T1 | *RUNX1-RUNX1T1* |

### Recommended References

1. **HGVS 2024 Main Recommendations:**
   https://hgvs-nomenclature.org

2. **Somatic Variant Guidelines:**
   https://www.ncbi.nlm.nih.gov/clinvar/

3. **COSMIC Database:**
   https://cancer.sanger.ac.uk/cosmic

---

## ISCN 2024 Cytogenetic Notation

### Structural Variants

| Abbreviation | Meaning | Example |
|--------------|---------|---------|
| del | Deletion | del(5q) |
| dup | Duplication | dup(1q) |
| ins | Insertion | ins(9;22) |
| inv | Inversion | inv(16)(p13.1q22) |
| t | Translocation | t(9;22)(q34;q11) |
| add | Additional material | add(3p) |
| der | Derivative chromosome | der(9)t(9;22) |
| r | Ring chromosome | r(22) |
| i | Isochromosome | i(17q) |

### Numerical Abnormalities

| Abbreviation | Meaning | Example |
|--------------|---------|---------|
| - | Monosomy | -7 |
| + | Trisomy | +8 |
| cp | Complex karyotype | cp |

### Breakpoint Notation

- **Simple translocation:** t(9;22)(q34;q11)
- **Complex rearrangement:** t(9;22;11)(q34;q11;q13)
- **Three-way:** t(9;22)(q34;q11)add(9)(q34)

---

## Quality Assurance Checklist

### Variant Nomenclature

- [ ] Gene symbols italicized (*BCR-ABL1*, *NPM1*)
- [ ] HGVS notation correct (c. or p. prefix)
- [ ] Reference sequence specified (NM_ for RNA, NG_ for genomic)
- [ ] All positions numeric
- [ ] Substitution notation complete

### Cytogenetic Notation

- [ ] Chromosome numbers without "chr" prefix
- [ ] Arms designated (p/q)
- [ ] Bands in parentheses (q34)
- [ ] Breakpoints specified
- [ ] Karyotype complete (ISCN format)

### Fusion Genes

- [ ] Hyphen between gene symbols
- [ ] Numerical designation (BCR-ABL1, not BCR-ABL)
- [ ] Italicized gene symbols
- [ ] Transcript variants specified if needed

---

## Manuscript Integration Examples

### Example 1: AML with NPM1 Mutation

**Correct:**
> Patient harbored an *NPM1* frameshift mutation (c.860_861insTCTG; p.Trp288Cysfs*2) at a variant allele frequency of 32%. Cytogenetic analysis revealed a normal female karyotype (46,XX[20]).

**Incorrect:**
> Patient had NPM1 mutation (860_861insTCTG) with VAF of 32%. Normal chromosomes (46,XX).

### Example 2: CML with Complex Karyotype

**Correct:**
> The patient had a complex karyotype with 3 abnormalities: 46,XX,del(5)(q13q33),-7,i(17)(q10)[12]/46,XX[8].

**Incorrect:**
> Complex karyotype with 5q deletion, monosomy 7, and isochromosome 17q.

### Example 3: APL with PML-RARA Fusion

**Correct:**
> Fluorescence in situ hybridization confirmed the t(15;17)(q22;q12) creating the *PML-RARA* fusion. RT-PCR identified the bcr1 isoform.

**Incorrect:**
> FISH positive for PML/RARA fusion. RT-PCR showed bcr1.

---

## Implementation in HPW Skill

### Automatic Validation

```python
from HPW_Nomenclature_Checker import NomenclatureChecker

checker = NomenclatureChecker()
issues = checker.check_all(manuscript_text)
```

### Check Categories

1. **Gene Symbol Validation**
   - Italicization
   - Correct case (BCR-ABL1, not BCR-ABL)

2. **HGVS Notation**
   - Correct prefix (c. vs p.)
   - Valid format

3. **ISCN Cytogenetics**
   - Chromosome format
   - Band notation
   - Karyotype completeness

4. **Fusion Gene Format**
   - Hyphen usage
   - Italicization

### Nomenclature Report

The checker generates:
- Error count by category
- Corrected examples
- Reference to guidelines
- Severity assessment
