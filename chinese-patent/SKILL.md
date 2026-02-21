---
name: chinese-patent
description: |
  Comprehensive skill for Chinese patent specifications. Handles drafting, revising, and auditing/reviewing patent drafts. Supports HTML format with figures and outputs docx for filing. Use for writing new patents, rewriting existing ones, or reviewing drafts for compliance and quality.
---

# Chinese Patent (中国专利)

> **Note**: This skill provides comprehensive support for Chinese patent specification lifecycle. The detailed guidelines are presented in both English and Chinese below.

This skill provides complete lifecycle support for Chinese patent specifications, including drafting, rewriting, reviewing, auditing, and format conversion (HTML to docx).

## When to Use (何时使用)

- **Drafting/Rewriting**: When users request to write new patents, rewrite existing patent drafts, or handle invention/utility model patents with figures.
- **Review/Audit**: When users request to check, audit, review, or examine patent drafts (specifications, claims, etc.) for quality and compliance.
- **Keywords**: patent writing, patent rewriting, patent review, patent audit, patent disclosure, figure description, patent docx, specification review.

---

## 1. Drafting & Rewriting Guide (撰写与改写指南)

### Specification Structure (说明书撰写结构)
Organize content in HTML in the following order (consistent with Patent Law/Examination Guidelines):
1. **Technical Field**: Technical field of the invention, briefly describing the scope.
2. **Background Art**: Current state of existing technology and existing problems/deficiencies.
3. **Invention Content**: Technical problems to be solved, technical solutions, beneficial effects.
4. **Figure Description**: Brief description of each figure, corresponding one-to-one with images.
5. **Detailed Implementation**: Specific description of technical solutions combined with figures.

### HTML Specifications (HTML 规范)
- **Tags**: Use semantic tags (`<h1>`~`<h3>`, `<p>`, `<ul>`/`<ol>`).
- **Tables**: Use `<table class="patent-table" border="1">`, content in Song typeface.
- **Images**: Must use local paths (e.g., `images/图1.png`). Supports using Python scripts (matplotlib, graphviz, etc.) to generate figures and save to `images/` directory.
- **Formatting**: Body text recommended as Size 4 Song typeface, 1.5 line spacing.

### Workflow (工作流)
1. **Unify to HTML**: If input is docx, first convert using `pandoc existing.docx -o current.html`.
2. **Edit and Draw**: Modify content in HTML, run scripts to generate new figures if needed.
3. **Export to docx**: Execute `pandoc -s specification.html -o specification.docx` or use `scripts/html_to_docx.py`.

---

## 2. Review & Audit Guide (审阅与复核指南)

### Review Dimensions (审阅维度)
1. **Structural Integrity**: Whether all statutory sections are complete and in correct order.
2. **Consistency**: Whether terminology and technical feature descriptions are unified between specification and claims.
3. **Figure Correspondence**: Whether figure numbers, descriptions correspond one-to-one with body text; whether image paths are correct.
4. **Terminology Standards**: Check for violations of legal terminology standards or common errors (see reference.md).
5. **Substantive Check**: Whether background art is objective, whether detailed implementation sufficiently supports claims.

### Output Format (输出格式)
List issues by dimension, recommended grading:
- **【Must Fix】**: Serious issues affecting authorization or compliance.
- **【Recommended】**: Improvement suggestions to enhance quality or reduce examination opinions.

---

## 3. Additional Resources (附加资源)

- **Detailed Specifications**: [reference.md](./reference.md) (includes terminology standards, common error quick reference).
- **Conversion Scripts**: [scripts/html_to_docx.py](./scripts/html_to_docx.py).
- **Figure Examples**: [scripts/generate_figure_example.py](./scripts/generate_figure_example.py).
- **Blank Template**: [templates/patent_spec_template.html](./templates/patent_spec_template.html).
