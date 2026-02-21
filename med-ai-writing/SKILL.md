---
name: med-ai-writing
description: Specialized skill for Medical-AI interdisciplinary paper writing. Supports clinical validation logic checking, medical ethics compliance review, cross-disciplinary narrative planning, and top-tier medical AI journal format adaptation. Inherits all core features from academic-writing with deep optimization for medical scenarios.
---

# Med-AI Writing (Medical & AI Interdisciplinary Paper Writing)

This skill helps researchers write high-quality medical-AI interdisciplinary papers. It builds on academic-writing, adding medical-specific rigor requirements and clinical value orientation.

## Core Workflow Modes

### 1. `plan-outline` (Med-AI Enhanced)
Build narrative based on clinical pain points.
- **Narrative Structure**: Must follow "Clinical Gap - AI Solution" model in references/med_ai_narrative.md.
- **Key Elements**: Clear clinical context, limitations of existing technology, how AI fills the gap, and clinical impact.

### 2. `clinical-validation` (Clinical Validation Logic Check)
Conduct medical rigor review of paper's experimental design and results analysis.
- **Operation**: Check dataset partitioning (whether external validation included), statistical methods (p-value, CI), evaluation metrics (Sensitivity, Specificity, AUC, F1) against medical standards.
- **Reference**: references/clinical_validation_guide.md.

### 3. `ethics-compliance` (Ethics Compliance Check)
Ensure paper meets medical research ethics requirements.
- **Operation**: Check whether IRB approval, patient informed consent, data anonymization are mentioned.
- **Output**: Flag missing ethics statements or compliance risks.

### 4. `write` & `review` (Cross-disciplinary Adaptation)
- **Writing**: Balance technical terminology for different audiences (clinicians vs AI experts).
- **Review**: Simulate review from 1 clinician and 2 AI expert perspectives.
- **AI Pattern Removal**: After writing, must call humanizer or humanizer-zh.

## ⚠️ Strictly Prohibit Hallucination Citations
All medical literature citations must go through academic-writing citation verification workflow. Strictly forbidden to fabricate clinical guidelines or research results.

## Domain References
- **Narrative Guide**: references/med_ai_narrative.md
- **Validation Standards**: references/clinical_validation_guide.md
- **Submission Venues**: references/med_ai_venues.md (includes MICCAI, Nature Medicine, Lancet Digital Health, etc.)
- **Base Capability**: Inherits academic-writing skill.
