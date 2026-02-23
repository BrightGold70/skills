# PDCA Plan: Hematology Clinical Analysis Skill Upgrade

## 1. Goal Description

Upgrade the `clinical-study-analysis` skill to provide specialized support for Hematology clinical research, involving statistical analysis of prospective, retrospective, and epidemiological studies in the field.

## 2. Background

Hematology research often involves complex survival analysis (e.g., bone marrow transplant outcomes, AML/CML progression) and specialized response criteria (IWG, ELN). The current skill is general and can be significantly enhanced by integrating specific R-based workflows via the `rmcp` MCP and synergizing with other biostatistics and reporting skills.

## 3. Features

- **Hematology Specialization**: Dedicated support for AML, CML, MDS, MM, and Lymphoma.
- **Advanced Survival Metrics**: Relapse vs. Non-Relapse Mortality (Competing Risks), Multi-state modeling.
- **Cross-Skill Synergy**: Automated assumption checking via `statistical-analysis` and trial benchmarking via `clinicaltrials-database`.
- **Publication Graphics**: Generation of Swimmer and Waterfall plots via `scientific-visualization`.

## 4. Success Criteria

- [ ] `SKILL.md` updated with Hematology-specific sections and tool integrations.
- [ ] New reference document for Hematology Response Criteria created.
- [ ] Example Hematology R scripts provided in the skill's script directory.
- [ ] Synergy patterns with `statistical-analysis` documented and verified.
