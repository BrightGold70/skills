---
name: academic-writing
description: 综合论文编写技能，支持 plan-outline（概要规划）、write（章节写作与整合）、review（评审）、switch-venue（渠道切换）和 switch-language（语言切换）模式。集成去 AI 味、防幻觉引用工作流、顶级会议写作哲学及稳定绘图功能。
---

# Academic Writing (学术论文编写)

## 核心工作流模式

### 1. `plan-outline` (概要规划)
用于生成论文的文章概要和内容排布。
- **操作**: 基于 `scientific-writing` 的两阶段规划法，确定 IMRAD 结构。
- **叙事原则 (Narrative Principle)**: 确保论文有一个清晰的核心贡献（One-sentence contribution），并围绕其构建故事。

### 2. `write` (章节写作与整合)
支持指定章节的深入写作或修改，并能整合多章节以确保一致性。
- **主动交付**: 只要背景清晰，应主动交付完整草稿，而非反复询问。
- **自动适配**: 根据当前 `venue`（如 NeurIPS 9页, ICML 8页）自动调整内容详略。
- **去 AI 味**: 写作完成后，**必须**调用 `humanizer` (英文) 或 `humanizer-zh` (中文) 进行语言优化。

### 3. `review` (多审稿人评审)
模拟顶级期刊/会议的多审稿人模式。
- **操作**: 模拟 2-3 名不同视角的审稿人对论文进行严苛审查。
- **输出**: 生成 `review.md` 文件。

### 4. `switch-venue` (渠道切换)
在不同会议或期刊格式之间进行转换。
- **操作**: 调整页数限制、章节结构（如是否需要 Broader Impact 或 Limitations）、参考文献格式。
- **参考**: [references/venue_templates.md](references/venue_templates.md)

### 5. `switch-language` (语言切换)
在中英文写作环境之间切换。
- **中文模式**: 遵循 `chinese-copywriting-guidelines`（中英文空格、全角标点）。
- **英文模式**: 遵循 `ml-paper-writing` 的简洁原则，避免过度修饰。

## ⚠️ 严禁幻觉引用
**严禁凭记忆生成 BibTeX。** 所有引用必须通过 [references/citation_workflow.md](references/citation_workflow.md) 中的 API 验证流程。如果无法验证，必须标记为 `[CITATION NEEDED]`。

## 增强功能

### 绘图与排版
- **Matplotlib**: 绘图标签必须与当前 `language` 一致（默认英文）。
- **排版**: 严格处理中英文混排空格。

## 领域参考
- **CS/ML**: [references/cs_ml_guide.md](references/cs_ml_guide.md) (含 Farquhar 5句摘要法)。
- **综合科学**: [references/general_science_guide.md](references/general_science_guide.md)。
- **引用工作流**: [references/citation_workflow.md](references/citation_workflow.md)。
- **渠道规范**: [references/venue_templates.md](references/venue_templates.md)。
