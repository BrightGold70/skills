---
name: med-ai-writing
description: 专门针对医学与 AI 交叉方向（Med-AI）的论文编写技能。支持临床验证逻辑检查、医学伦理合规性审查、跨学科叙事规划以及顶级医学 AI 刊物格式适配。继承 academic-writing 的所有核心功能，并针对医学场景进行了深度优化。
---

# Med-AI Writing (医学与 AI 交叉论文编写)

本技能旨在帮助研究者编写高质量的医学 AI 交叉学科论文。它在 `academic-writing` 的基础上，增加了医学特有的严谨性要求和临床价值导向。

## 核心工作流模式

### 1. `plan-outline` (Med-AI 增强版)
基于临床痛点构建叙事。
- **叙事结构**: 必须遵循 [references/med_ai_narrative.md](references/med_ai_narrative.md) 中的“临床缺口-AI解决方案”模型。
- **关键要素**: 明确临床背景（Clinical Context）、现有技术的局限（Gap）、AI 如何填补该缺口（Innovation）以及临床获益（Clinical Impact）。

### 2. `clinical-validation` (临床验证逻辑检查)
对论文的实验设计和结果分析进行医学严谨性审查。
- **操作**: 检查数据集划分（是否包含外部验证）、统计学方法（p-value, CI）、评价指标（Sensitivity, Specificity, AUC, F1）是否符合医学标准。
- **参考**: [references/clinical_validation_guide.md](references/clinical_validation_guide.md)。

### 3. `ethics-compliance` (伦理合规性检查)
确保论文符合医学研究的伦理要求。
- **操作**: 检查是否提及 IRB 批准、患者告知同意、数据匿名化处理等关键信息。
- **输出**: 提示缺失的伦理声明或合规性风险。

### 4. `write` & `review` (跨学科适配)
- **写作**: 针对不同受众（临床医生 vs AI 专家）平衡专业术语的使用。
- **评审**: 模拟 1 名临床医生和 2 名 AI 专家的视角进行评审。
- **去 AI 味**: 写作后必须调用 `humanizer` 或 `humanizer-zh`。

## ⚠️ 严禁幻觉引用
所有医学文献引用必须通过 `academic-writing` 的引用验证流程。严禁虚构临床指南或研究结果。

## 领域参考
- **叙事指南**: [references/med_ai_narrative.md](references/med_ai_narrative.md)
- **验证规范**: [references/clinical_validation_guide.md](references/clinical_validation_guide.md)
- **投稿渠道**: [references/med_ai_venues.md](references/med_ai_venues.md) (含 MICCAI, Nature Medicine, Lancet Digital Health 等)
- **基础能力**: 继承 `academic-writing` 技能。
