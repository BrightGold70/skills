# HPW Skill - Enhanced Editing Capabilities

## Overview

The HPW skill now includes advanced editing capabilities for manuscript enhancement:

### 1. Enhanced Editor (`EnhancedEditor`)

**Features:**
- Load and parse manuscripts into structured sections
- Search for topics and generate insertion suggestions
- Context-aware content insertion
- Edit history tracking

**Usage:**
```python
from tools.draft_generator.HPW_Enhanced_Editor import EnhancedEditor

editor = EnhancedEditor("manuscript.md")
sections = editor.load_manuscript("manuscript.md")

# Search for topic and get suggestions
suggestions = editor.search_and_suggest("NPM1 mutation AML")

# Generate edit report
print(editor.generate_edit_report())
```

### 2. Context Searcher (`ContextSearcher`)

**Features:**
- Search PubMed and local databases
- Format results for manuscript insertion
- Compare and merge new information

**Usage:**
```python
from tools.draft_generator.HPW_Enhanced_Editor import ContextSearcher

searcher = ContextSearcher()
results = searcher.search_topic("FLT3-ITD allelic ratio", max_results=5)

# Format for insertion
formatted = searcher.format_for_insertion(results[0])
```

### 3. Section Enhancer (`SectionEnhancer`)

**Features:**
- Add context to manuscript sections
- Calculate completeness scores
- Suggest enhancements

**Usage:**
```python
from tools.draft_generator.HPW_Enhanced_Editor import SectionEnhancer

enhancer = SectionEnhancer()
enhanced = enhancer.enhance_section(
    section_type="introduction",
    existing_content=current_text,
    topic="epidemiology"
)

# Get suggestions
summary = enhancer.generate_section_summary(section)
print(f"Completeness: {summary['completeness_score']:.0%}")
```

---

## Command Line Integration

### Enhanced Search and Insert

```bash
# Search and suggest edits for topic
hpw enhance --manuscript manuscript.md --topic "NPM1 mutation"

# Insert content from topic search
hpw enhance --manuscript manuscript.md --topic "ELN risk stratification" --insert

# Generate section completeness report
hpw enhance --manuscript manuscript.md --check-completeness
```

### Quality Check with Nomenclature

```bash
# Check nomenclature compliance
hpw nomenclature-check --file manuscript.md

# Generate report
hpw nomenclature-check --file manuscript.md --report
```

---

## Integration with Existing Workflow

### Complete Editing Workflow

1. **Load Manuscript**
   ```python
   editor = EnhancedEditor("draft.md")
   sections = editor.load_manuscript("draft.md")
   ```

2. **Search for Missing Context**
   ```python
   suggestions = editor.search_and_suggest("epidemiology of AML")
   ```

3. **Apply Suggestions**
   ```python
   for suggestion in suggestions:
       if suggestion.confidence > 0.8:
           editor.insert_content(suggestion)
   ```

4. **Enhance Sections**
   ```python
   enhancer = SectionEnhancer()
   for section in sections:
       if enhancer._calculate_completeness(section) < 0.7:
           enhanced = enhancer.enhance_section(section.section_type, section.content)
   ```

5. **Validate Nomenclature**
   ```python
   checker = NomenclatureChecker()
   issues = checker.check_all(manuscript_text)
   print(checker.generate_report(manuscript_text))
   ```

---

## Files

- `tools/draft_generator/HPW_Enhanced_Editor.py` - Main module
- `HPW_Nomenclature_Checker.py` - Nomenclature validation
- `HPW_Nomenclature_Guidelines.md` - Reference guide
- `HPW_HGVS_2024_Update.md` - HGVS 2024 updates
