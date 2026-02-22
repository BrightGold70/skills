---
name: chinese-patent
description: |
  Comprehensive skill for Chinese patent specifications. Handles drafting, revising, and auditing/reviewing patent drafts. Supports HTML format with figures and outputs docx for filing. Use for writing new patents, rewriting existing ones, or reviewing drafts for compliance and quality.
---

# 中国专利 (Chinese Patent)

本技能提供中国专利说明书的完整生命周期支持，包括撰写、改写、审阅、复核以及格式转换（HTML 转 docx）。

## 何时使用

- **撰写/改写**：用户要求撰写新专利、改写已有专利稿、或需要处理带附图的发明/实用新型专利。
- **审阅/复核**：用户要求检查、审计、复核或审阅专利稿（说明书、权利要求书等）的质量与合规性。
- **关键词**：专利撰写、专利改写、专利审阅、专利复核、专利交底、附图说明、专利 docx、说明书审查。

---

## 1. 撰写与改写指南

### 说明书撰写结构
按以下顺序用 HTML 组织正文（与专利法/审查指南一致）：
1. **技术领域**：发明所属技术领域，简明说明涉及范围。
2. **背景技术**：现有技术现状及存在的问题、不足。
3. **发明内容**：要解决的技术问题、技术方案、有益效果。
4. **附图说明**：各附图的简要说明，与图片一一对应。
5. **具体实施方式**：结合附图对技术方案的具体描述。

### HTML 规范（便于转 docx）
- **标签**：使用语义化标签（`<h1>`~`<h3>`, `<p>`, `<ul>`/`<ol>`）。
- **表格**：使用 `<table class="patent-table" border="1">`，内容使用宋体。
- **图片**：必须使用本地路径（如 `images/图1.png`）。支持使用 Python 脚本（matplotlib, graphviz 等）生成附图并保存至 `images/` 目录。
- **格式**：正文建议小四宋体，1.5 倍行距。

### 工作流
1. **统一到 HTML**：若输入为 docx，先用 `pandoc 现有.docx -o 当前.html` 转换。
2. **编辑与绘图**：在 HTML 中修改内容，如有需要则运行脚本生成新附图。
3. **导出 docx**：执行 `pandoc -s 说明书.html -o 说明书.docx` 或使用 `scripts/html_to_docx.py`。

---

## 2. 审阅与复核指南

### 审阅维度（检查项）
1. **结构完整性**：各法定章节是否齐全，顺序是否正确。
2. **一致性**：说明书与权利要求书之间的术语、技术特征表述是否统一。
3. **附图对应性**：附图编号、说明与正文引用是否一一对应；图片路径是否正确。
4. **用语规范**：检查是否违反法律用语规范或存在常见错误（参考 `reference.md`）。
5. **实质性检查**：背景技术是否客观，具体实施方式是否充分支持权利要求。

### 输出格式
按维度列出问题，建议分级：
- **【必须改】**：影响授权或合规的严重问题。
- **【建议改】**：提升质量或减少审查意见的改进建议。

---

## 3. 附加资源

- **详细规范**：[reference.md](./reference.md)（含用语规范、常见错误速查）。
- **转换脚本**：[scripts/html_to_docx.py](./scripts/html_to_docx.py)。
- **绘图示例**：[scripts/generate_figure_example.py](./scripts/generate_figure_example.py)。
- **空白模板**：[templates/patent_spec_template.html](./templates/patent_spec_template.html)。
