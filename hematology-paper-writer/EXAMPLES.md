# 📖 Hematology Paper Writer - Examples

**Detailed examples and workflows for the Hematology Paper Writer skill.**

---

## Table of Contents

1. [Quick Examples](#quick-examples)
2. [Complete Workflows](#complete-workflows)
3. [Before/After Comparisons](#beforeafter-comparisons)
4. [Reference Verification Examples](#reference-verification-examples)
5. [Quality Analysis Examples](#quality-analysis-examples)
6. [Common Use Cases](#common-use-cases)
7. [Troubleshooting](#troubleshooting)

---

## Quick Examples

### Example 1: Verify a Single Reference

```python
from tools.pubmed_verifier import verify_reference

reference = "Smith AB, Jones CD. Novel mutations in myeloproliferative neoplasms. Blood. 2023;142(5):456-463."

result = verify_reference(reference)

print(f"Valid: {result.is_valid}")
print(f"PMID: {result.pmid}")
print(f"Confidence: {result.confidence_score:.1%}")
print(f"Title: {result.matched_record.title if result.matched_record else 'N/A'}")
```

**Output:**
```
Valid: True
PMID: 37123456
Confidence: 95.0%
Title: Novel mutations in myeloproliferative neoplasms
```

---

### Example 2: Analyze Manuscript Quality

```python
from tools.quality_analyzer import QualityAnalyzer

manuscript = """
# Novel Mutations in Myeloproliferative Neoplasms

## Abstract
Background: Myeloproliferative neoplasms (MPN) are clonal hematopoietic stem cell disorders...

## Introduction
Myeloproliferative neoplasms represent a spectrum of clonal disorders...

## Methods
This was a retrospective study of 250 patients...

## Results
We identified novel mutations in 45% of patients...

## Discussion
These findings suggest that novel mutations play a role in MPN pathogenesis...
"""

analyzer = QualityAnalyzer()
quality = analyzer.analyze(manuscript)

print(f"Overall Score: {quality.overall_score:.1%}")
print(f"Structure: {quality.structure_score:.1%}")
print(f"Clarity: {quality.clarity_score:.1%}")
print(f"Completeness: {quality.completeness_score:.1%}")
```

**Output:**
```
Overall Score: 85.0%
Structure: 100.0%
Clarity: 80.0%
Completeness: 75.0%
```

---

### Example 3: Get Enhancement Suggestions

```python
from tools.content_enhancer import ContentEnhancer = """


manuscriptThe samples were collected and then analyzed using statistical methods.
The patients was divided into two groups. The data was analyzed by us.
"""

enhancer = ContentEnhancer()
suggestions = enhancer.analyze_and_enhance(manuscript)

for suggestion in suggestions:
    print(f"[{suggestion.section}] {suggestion.reason}")
    if suggestion.original_text:
        print(f"  Found: \"{suggestion.original_text}\"")
```

**Output:**
```
[General] Consider using active voice for clarity
  Found: "were collected and then analyzed"
  Found: "was divided"
  Found: "were analyzed by us"
```

---

## Complete Workflows

### Workflow 1: New Manuscript from Scratch

```bash
# Step 1: Use a template
cp templates/manuscript.md my_paper.md

# Step 2: Write your manuscript

# Step 3: Check quality
hpw check-quality my_paper.md --journal blood

# Step 4: Verify references
hpw verify-references my_paper.md --journal blood

# Step 5: Apply enhancements
hpw edit-manuscript my_paper.md --apply --output my_paper_enhanced.md

# Step 6: Generate final report
hpw generate-report my_paper_enhanced.md --verify-references --output final_report.txt
```

**Python Equivalent:**

```python
from pathlib import Path
from tools import QualityAnalyzer, ReferenceManager, ContentEnhancer
from tools.pubmed_verifier import verify_references

# Step 1: Load manuscript
manuscript = Path("my_paper.md").read_text()

# Step 2: Check quality
analyzer = QualityAnalyzer(journal_specs={"journal": "blood"})
quality = analyzer.analyze(manuscript)

# Step 3: Verify references
ref_manager = ReferenceManager(journal="blood")
references = ref_manager.parse_references(manuscript)
ref_results = verify_references(references)

# Step 4: Apply enhancements
enhancer = ContentEnhancer(target_journal="blood")
suggestions = enhancer.analyze_and_enhance(manuscript)

# Step 5: Generate enhanced version
enhanced = manuscript
for suggestion in suggestions[:20]:  # Apply top 20 suggestions
    if suggestion.suggested_text:
        enhanced = enhanced.replace(suggestion.original_text, suggestion.suggested_text)

# Step 6: Save enhanced manuscript
Path("my_paper_enhanced.md").write_text(enhanced)
```

---

### Workflow 2: Revise and Resubmit

```bash
# Start with previous submission
cp response_to_reviewers.docx reviews_handled.md

# Check what improvements are needed
hpw generate-report reviews_handled.md --verify-references

# Apply specific enhancements
hpw edit-manuscript reviews_handled.md --apply --output revised_manuscript.md

# Verify all references are still valid
hpw verify-references revised_manuscript.md

# Generate submission package
hpw generate-report revised_manuscript.md --verify-references --json final_metrics.json
```

---

### Workflow 3: Quick Reference Check Only

```bash
# Quick check of references without full analysis
hpw verify-references manuscript.md --json verification_results.json

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ All references verified successfully!"
else
    echo "⚠️ Some references need attention"
    cat verification_results.json
fi
```

**Python Version:**

```python
from tools.pubmed_verifier import verify_references

references = [
    "1. Smith AB, et al. Novel mutations in AML. Blood. 2023;142:456-463.",
    "2. Williams EF, et al. Treatment outcomes. JCO. 2022;40:1234-1245.",
    # ... more references
]

results = verify_references(references)

if results.valid_count == results.total_references:
    print("✅ All references verified successfully!")
else:
    print(f"⚠️ {results.invalid_count} references need attention")
    
# Show invalid references
for result in results.results:
    if not result.is_valid:
        print(f"❌ {result.raw_reference}")
        for diff in result.differences:
            print(f"   - {diff}")
```

---

## Before/After Comparisons

### Example 1: Clarity Improvement

**Before:**
```markdown
The samples were collected and then analyzed using statistical methods.
The patients was divided into two groups by the investigators.
The data was analyzed by us to determine significance.
```

**After (with enhancement):**
```markdown
We collected the samples and analyzed them using statistical methods.
We divided the patients into two groups.
We analyzed the data to determine significance.
```

**Improvement:**
- ✅ Passive voice → Active voice
- ✅ "The patients was" → "We divided" (grammar fix)
- ✅ "by us" → Removed (unnecessary)

---

### Example 2: Statistical Reporting

**Before:**
```markdown
The treatment group showed significant improvement (p < 0.05).
```

**After:**
```markdown
The treatment group showed significant improvement compared to control 
(p = 0.03; 95% CI, 1.5-3.2). The effect size was large (Cohen's d = 0.8).
```

**Improvement:**
- ✅ Added specific p-value
- ✅ Added confidence interval
- ✅ Added effect size

---

### Example 3: Reference Formatting

**Before:**
```markdown
[1] Smith AB, Jones CD. Novel mutations in AML. Blood. 2023;142:456-463
```

**After (verified):**
```markdown
[1] Smith AB, Jones CD. Novel mutations in myeloproliferative neoplasms. 
Blood. 2023 May 18;142(5):456-463. doi:10.1182/blood.2023000123. 
PMID: 37123456.
```

**Improvement:**
- ✅ Verified against PubMed
- ✅ Corrected journal abbreviation
- ✅ Added full publication date
- ✅ Added DOI
- ✅ Added PMID

---

## Reference Verification Examples

### Example 1: Valid Reference

**Input:**
```markdown
[1] Smith AB, Jones CD, Williams EF. Novel mutations in myeloproliferative neoplasms. 
Blood. 2023;142(5):456-463.
```

**Verification Result:**
```
✅ VALID
PMID: 37123456
DOI: 10.1182/blood.2023000123
Confidence: 95%
Differences: None
```

---

### Example 2: Reference with Minor Issues

**Input:**
```markdown
[2] Williams EF. Treatment outcomes in AML patients. Blood. 2022;141:123-130.
```

**Verification Result:**
```
⚠️ WARNING
PMID: 37123455
Confidence: 78%
Differences:
  - Title mismatch: "Treatment outcomes in AML patients" vs "Treatment outcomes in acute myeloid leukemia"
  - Author missing: Expected 3 authors, found 1
```

**Recommendation:**
```markdown
[2] Williams EF, Brown GH, Davis JD. Treatment outcomes in acute myeloid leukemia patients. 
Blood. 2022;141(2):123-130. PMID: 37123455.
```

---

### Example 3: Invalid Reference

**Input:**
```markdown
[3] Unknown Author. Fake study. Journal of Made-Up Research. 2020;1:1-10.
```

**Verification Result:**
```
❌ INVALID
PMID: None
Confidence: 0%
Differences:
  - No matching PubMed record found
  - Reference may be fabricated or incorrectly cited
```

**Action Required:**
- ❓ Verify the reference exists
- 🔍 Search PubMed for the correct citation
- ✏️ Correct or remove the reference

---

## Quality Analysis Examples

### Example 1: Good Quality Manuscript

**Manuscript:** Complete IMRAD structure, well-written, all sections present

**Result:**
```
==========================================
QUALITY ANALYSIS RESULTS
==========================================

Overall Score: 92/100

Category Scores:
  Structure:     100% ✅
  Clarity:       90% ✅
  Completeness:  85% ✅

Issues Found:
  - Minor passive voice usage (3 instances)
  - One section could use more detail (Methods)

Recommendations:
  - Reduce passive voice in Results section
  - Add power calculation to Methods
```

---

### Example 2: Manuscript Needing Work

**Manuscript:** Missing sections, poor clarity

**Result:**
```
==========================================
QUALITY ANALYSIS RESULTS
==========================================

Overall Score: 58/100

Category Scores:
  Structure:     60% ⚠️
  Clarity:       55% ⚠️
  Completeness:  60% ⚠️

Critical Issues:
  - Missing Discussion section
  - No References section
  - Abstract too brief (<100 words)

Major Issues:
  - Passive voice overuse (>40%)
  - Technical jargon not defined
  - Statistical methods not described

Recommendations:
  1. Add Discussion section
  2. Add References (50-100 expected)
  3. Expand Abstract to 200-250 words
  4. Rewrite using active voice
  5. Define technical terms on first use
```

---

## Common Use Cases

### Use Case 1: Preparing for Blood Submission

```bash
# 1. Set journal context
export JOURNAL= blood

# 2. Check compliance
hpw check-quality manuscript.md --journal blood

# 3. Verify all references
hpw verify-references manuscript.md --journal blood

# 4. Apply enhancements
hpw edit-manuscript manuscript.md --apply --output ready_for_submission.md

# 5. Generate submission checklist
hpw generate-report ready_for_submission.md --verify-references
```

**Key Checks for Blood:**
- ✅ Abstract ≤250 words
- ✅ Key Points (3-5 bullets)
- ✅ Adverse events section
- ✅ Trial registration number
- ✅ Author contributions statement
- ✅ Conflict of interest statement
- ✅ All references have PMID

---

### Use Case 2: Revising for JCO

```bash
# 1. Check specific requirements
hpw check-quality manuscript.md --journal jco

# 2. Focus on statistical reporting
hpw edit-manuscript manuscript.md --max-suggestions 10

# 3. Add CONSORT diagram if clinical trial
# (Manual step - ensure CONSORT diagram is included)

# 4. Final verification
hpw generate-report manuscript.md --verify-references
```

**Key Checks for JCO:**
- ✅ CONSORT diagram (if clinical trial)
- ✅ Statistical methods detailed
- ✅ Confidence intervals reported
- ✅ Effect sizes reported
- ✅ Author contributions specified

---

### Use Case 3: Quick Reference Audit

```python
from tools.reference_manager import ReferenceManager
from tools.pubmed_verifier import verify_references

# Load manuscript
with open("manuscript.md", "r") as f:
    text = f.read()

# Parse references
ref_manager = ReferenceManager(journal="blood")
references = ref_manager.parse_references(text)

# Quick audit
audit_results = []
for ref in references:
    ref_text = ref_manager.format_reference(ref)
    audit_results.append({
        "number": ref.citation_number,
        "has_all_fields": all([ref.authors, ref.title, ref.journal, ref.year]),
        "has_doi": ref.doi is not None,
        "has_pubmed_id": ref.pubmed_id is not None
    })

# Summary
valid_refs = sum(1 for r in audit_results if r["has_all_fields"])
has_dois = sum(1 for r in audit_results if r["has_doi"])
has_pmids = sum(1 for r in audit_results if r["has_pubmed_id"])

print(f"References with all fields: {valid_refs}/{len(audit_results)}")
print(f"References with DOI: {has_dois}/{len(audit_results)}")
print(f"References with PMID: {has_pmids}/{len(audit_results)}")
```

---

### Use Case 4: Before Submission Checklist

```python
from tools import QualityAnalyzer, ReferenceManager
from tools.pubmed_verifier import BatchReferenceVerifier

class SubmissionChecklist:
    def __init__(self, manuscript_path, journal="blood"):
        self.manuscript = Path(manuscript_path).read_text()
        self.journal = journal
        self.checks = []
    
    def run_all_checks(self):
        # 1. Quality check
        analyzer = QualityAnalyzer(journal_specs={"journal": self.journal})
        quality = analyzer.analyze(self.manuscript)
        self.checks.append({
            "name": "Quality Score",
            "passed": quality.overall_score >= 0.8,
            "score": f"{quality.overall_score:.0%}"
        })
        
        # 2. Reference count
        ref_manager = ReferenceManager(journal=self.journal)
        refs = ref_manager.parse_references(self.manuscript)
        self.checks.append({
            "name": "Reference Count",
            "passed": len(refs) >= 30,
            "count": len(refs)
        })
        
        # 3. Reference verification
        verifier = BatchReferenceVerifier()
        ref_texts = [ref_manager.format_reference(r) for r in refs]
        results = verifier.verify_all(ref_texts)
        self.checks.append({
            "name": "Reference Verification",
            "passed": results.valid_percentage >= 95,
            "accuracy": f"{results.valid_percentage:.0f}%"
        })
        
        return self
    
    def print_checklist(self):
        print("=" * 60)
        print("SUBMISSION CHECKLIST")
        print("=" * 60)
        
        all_passed = True
        for check in self.checks:
            status = "✅ PASS" if check["passed"] else "❌ FAIL"
            if not check["passed"]:
                all_passed = False
            
            print(f"\n{status} - {check['name']}")
            for key, value in check.items():
                if key not in ["name", "passed"]:
                    print(f"    {key}: {value}")
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 READY FOR SUBMISSION!")
        else:
            print("⚠️  ISSUES NEED ATTENTION")
        print("=" * 60)

# Usage
checklist = SubmissionChecklist("manuscript.md", journal="blood")
checklist.run_all_checks().print_checklist()
```

**Output:**
```
============================================================
SUBMISSION CHECKLIST
============================================================

✅ PASS - Quality Score
    score: 85%

✅ PASS - Reference Count
    count: 45

✅ PASS - Reference Verification
    accuracy: 98%

============================================================
🎉 READY FOR SUBMISSION!
============================================================
```

---

## Troubleshooting

### Problem: No References Found

**Symptoms:**
```
WARNING: No references found in manuscript
```

**Solutions:**
1. Ensure references are numbered (e.g., "[1]", "1.")
2. Use Vancouver format (authors. Title. Journal. Year;Vol:Pages.)
3. Check file encoding (use UTF-8)

**Example of correct format:**
```markdown
[1] Smith AB, Jones CD. Novel mutations in AML. Blood. 2023;142:456-463.
[2] Williams EF, Brown GH. Treatment outcomes. JCO. 2022;40:1234-1245.
```

---

### Problem: PubMed Verification Timeout

**Symptoms:**
```
ERROR: PubMed verification timed out
```

**Solutions:**
1. Add NCBI API key for higher rate limits
2. Reduce batch size
3. Check internet connection

**With API key:**
```python
verifier = PubMedVerifier(api_key="your_ncbi_api_key")
```

---

### Problem: Low Quality Score

**Symptoms:**
```
Quality Score: 45% (below 70% threshold)
```

**Solutions:**
1. Check "Issues Found" section
2. Run `hpw edit-manuscript --apply` to auto-fix
3. Review recommendations manually
4. Ensure complete IMRAD structure

**Common fixes:**
- Add missing sections (Discussion, Methods)
- Reduce passive voice
- Add statistical details (p-values, CIs)
- Include all required elements (Conflict of Interest, Funding)

---

### Problem: Reference Format Errors

**Symptoms:**
```
WARNING: Could not parse reference [3]
```

**Solutions:**
1. Use standard Vancouver format
2. Include all required fields (authors, year, journal, volume, pages)
3. Check for typos in author names or journal names

**Correct format:**
```
[Number] Authors. Title. Journal. Year;Vol(Issue):Pages. DOI.
```

---

## Quick Reference

### CLI Command Summary

| Command | Purpose | Quick Example |
|---------|---------|--------------|
| `check-quality` | Analyze manuscript | `hpw check-quality paper.md` |
| `verify-references` | PubMed check | `hpw verify-references paper.md` |
| `edit-manuscript` | Auto-enhance | `hpw edit-manuscript paper.md --apply` |
| `generate-report` | Full report | `hpw generate-report paper.md --verify` |

### Python API Quick Reference

```python
# Verify references
verify_reference(text) → ValidationResult
verify_references(list) → BatchVerificationResult

# Quality analysis  
analyzer.analyze(text) → QualityScore

# Content enhancement
enhancer.analyze_and_enhance(text) → List[EnhancementSuggestion]

# Revision tracking
revisor.create_revision(author, changes, summary) → Revision
```

---

**Need more examples?** Check the main README.md or run:
```bash
hpw --help
hpw <command> --help
```
