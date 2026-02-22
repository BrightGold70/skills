# HPW NotebookLM Integration Plan for Source Control

**Created:** 2026-02-12  
**Skill Location:** `/Users/kimhawk/.openclaw/skills/hematology-paper-writer/`  
**Output Location:** `/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/`  
**References:** `/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/References/`

---

## Executive Summary

This plan outlines the integration of NotebookLM to ensure robust source control for the Hematology Paper Writer (HPW) skill. NotebookLM will serve as a centralized knowledge management system for tracking manuscripts, references, literature searches, and research materials.

**Key Benefits:**
- Automated manuscript version tracking
- Centralized reference library management
- Source attribution for claims
- Audio overview generation for manuscript review
- Collaborative research documentation

---

## 1. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Create NotebookLM project for HPW
- [ ] Upload existing reference library
- [ ] Document manuscript version naming conventions
- [ ] Set up folder structure in NotebookLM

### Phase 2: Integration (Week 3-4)
- [ ] Develop CLI commands for NotebookLM sync
- [ ] Create automated upload workflows
- [ ] Implement citation tracking
- [ ] Set up source attribution system

### Phase 3: Automation (Week 5-6)
- [ ] Auto-upload manuscripts on save
- [ ] Generate Audio Overview for each manuscript
- [ ] Implement reference verification workflow
- [ ] Create progress tracking dashboards

### Phase 4: Optimization (Week 7-8)
- [ ] Fine-tune source attribution accuracy
- [ ] Optimize Audio Overview generation
- [ ] Document best practices
- [ ] User training and handover

---

## 2. Technical Architecture

### NotebookLM Source Structure
```
HPW Source (NotebookLM)
├── References/
│   ├── ELN_2022_AML.pdf
│   ├── ELN_2025_CML.pdf
│   ├── WHO_2022_Myeloid.pdf
│   ├── ISCN_2024.pdf
│   └── HGVS_2024.pdf
├── Manuscripts/
│   ├── Asciminib_CML_Review-202602121528.md
│   └── [Manuscript Name]-[Timestamp].md
├── Literature_Searches/
│   ├── PubMed_2026-02-12_CML.txt
│   └── Google_Scholar_2026-02-12_AML.txt
└── Project_Notes/
    ├── Nomenclature_Guidelines.md
    └── Style_Checklist.md
```

### Local File Structure
```
hematology-paper-writer/
├── tools/
│   ├── draft_generator/
│   │   ├── enhanced_drafter.py
│   │   ├── HPW_Nomenclature_Checker.py
│   │   ├── HPW_Enhanced_Editor.py
│   │   └── manuscript_editor.py
│   └── notebooklm/
│       └── notebooklm_manager.py  (NEW)
├── notebooks/
│   └── [archived notebooks]
├── HPW_NotebookLM_Integration_Plan.md
└── SKILL.md
```

---

## 3. Code Modules Required

### A. NotebookLM Manager (`tools/notebooklm/notebooklm_manager.py`)

**Functions:**
```python
class NotebookLMManager:
    def upload_manuscript(self, path: str) -> bool
    def upload_reference(self, path: str) -> bool
    def generate_audio_overview(self, notebook_id: str) -> str
    def get_source_list(self) -> List[dict]
    def sync_references(self, local_dir: str) -> bool
    def track_version(self, manuscript_path: str, version: str) -> bool
```

### B. CLI Commands

**New commands for `hpw` CLI:**
```bash
hpw notebooklm upload-manuscript --path <manuscript.md>
hpw notebooklm upload-reference --path <reference.pdf>
hpw notebooklm sync-references --local-dir <path>
hpw notebooklm audio-overview --notebook <id>
hpw notebooklm status
```

### C. Automated Workflows

**Git Integration:**
- Auto-commit on manuscript save
- Tag versions with timestamps
- Generate diff reports

**NotebookLM Sync:**
- Upload new manuscripts automatically
- Update references library
- Generate Audio Overview on save

---

## 4. Migration Steps

### Step 1: Export Current References
```bash
# Export existing references to NotebookLM-compatible format
hpw references export --format pdf --output /tmp/references/
```

### Step 2: Create NotebookLM Project
1. Go to notebooklm.google.com
2. Create new source "HPW-Research-Library"
3. Upload exported references

### Step 3: Configure Local Environment
```bash
# Set up NotebookLM API credentials (if available)
export NOTEBOOKLM_API_KEY="your-api-key"

# Configure sync directory
hpw config set notebooklm.sync_dir "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/"
```

### Step 4: Test Integration
```bash
# Test upload
hpw notebooklm upload-manuscript "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/Asciminib_CML_Review-Revised.md"

# Test audio overview
hpw notebooklm audio-overview --notebook <notebook-id>
```

---

## 5. User Guide

### Quick Start

1. **Upload a manuscript:**
   ```bash
   hpw notebooklm upload-manuscript --path Asciminib_CML_Review.md
   ```

2. **Sync references:**
   ```bash
   hpw notebooklm sync-references --local-dir References/
   ```

3. **Generate Audio Overview:**
   ```bash
   hpw notebooklm audio-overview --notebook <notebook-id>
   ```

### Workflow Integration

**Research Phase:**
1. Conduct literature search using `hpw search-pubmed`
2. Save results to `Literature_Searches/`
3. Upload references to NotebookLM
4. Create Audio Overview for initial review

**Writing Phase:**
1. Draft manuscript using `hpw create-draft`
2. Save to output directory (auto-timestamped)
3. Auto-upload to NotebookLM
4. Generate Audio Overview for proofreading

**Review Phase:**
1. Listen to Audio Overview
2. Make revisions
3. Save new version (new timestamp)
4. Re-upload and generate new Audio Overview

---

## 6. Timeline Estimates

| Phase | Duration | Effort | Deliverables |
|-------|----------|---------|--------------|
| Phase 1 | 2 weeks | 20 hours | NotebookLM project, folder structure |
| Phase 2 | 2 weeks | 30 hours | CLI commands, integration scripts |
| Phase 3 | 2 weeks | 25 hours | Automated workflows, sync scripts |
| Phase 4 | 2 weeks | 15 hours | Documentation, training |

**Total Estimated Time:** 8 weeks (90 hours)

---

## 7. Dependencies

- Python 3.10+
- NotebookLM account
- Google Cloud credentials (for API access)
- Git for version control
- Sufficient storage for reference library

---

## 8. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API access limitations | Manual upload fallback |
| Large reference files | Compress before upload |
| Sync conflicts | Version control integration |
| Data loss | Regular git commits + cloud backup |

---

## 9. Success Metrics

- [ ] 100% of manuscripts uploaded to NotebookLM
- [ ] All references tracked in source library
- [ ] Audio Overview generated for each manuscript
- [ ] Zero manual upload errors
- [ ] Source attribution coverage >95%

---

## 10. Next Steps

1. **Immediate:** Create NotebookLM account and upload existing references
2. **This week:** Test manual upload workflow
3. **Next week:** Develop CLI integration scripts
4. **Ongoing:** Iterate based on feedback

---

**Plan Version:** 1.0  
**Last Updated:** 2026-02-12  
**Status:** Ready for Implementation
