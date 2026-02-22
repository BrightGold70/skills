---
name: bkit-pdca
description: PDCA (Plan-Do-Check-Act) methodology for systematic AI-native development. Supports Plan → Design → Do → Check → Act workflow with automatic phase tracking. Use for feature planning, design documents, gap analysis, iteration, and completion reports.
---

# bkit PDCA - Plan-Do-Check-Act Methodology

Structured development workflow implementing the PDCA cycle for AI-native development.

## Overview

PDCA is a systematic methodology for development:
- **Plan**: Create feature plan document
- **Design**: Create technical design document
- **Do**: Implement with guidance
- **Check**: Run gap analysis
- **Act**: Iterate or complete

## Core Rules (Always Apply)

1. **New feature request** → Check/create Plan document first
2. **Plan complete** → Create Design document
3. **After implementation** → Run Gap analysis
4. **Gap Analysis < 90%** → Auto-improvement iteration
5. **Gap Analysis >= 90%** → Generate completion report
6. **Always** verify important decisions with the user

## Workflow Commands

### /pdca plan <feature>
Creates a comprehensive plan document including:
- Feature overview and goals
- User stories and requirements
- Success criteria
- Implementation approach
- Risk assessment

### /pdca design <feature>
Creates technical design document with:
- Architecture overview
- Component breakdown
- Data models
- API specifications
- Security considerations

### /pdca do <feature>
Provides implementation guidance:
- Code structure recommendations
- Step-by-step implementation steps
- Best practices
- Common pitfalls to avoid

### /pdca analyze <feature>
Runs gap analysis comparing:
- Design document vs implementation
- Missing features
- Quality issues
- Security concerns

Outputs gap percentage and specific issues.

### /pdca iterate <feature>
Auto-improvement iteration:
- Reviews gap analysis results
- Generates specific fixes
- Prioritizes issues by severity
- Creates action items

### /pdca report <feature>
Generates completion report:
- PDCA cycle summary
- What was accomplished
- Known limitations
- Future improvements
- Lessons learned

### /pdca status
Shows current PDCA status for project:
- Active features
- Current phases
- Blockers
- Recent updates

### /pdca next
Recommends next PDCA step based on current state.

## Document Structure

```
docs/
├── 01-plan/
│   └── features/
│       └── [feature-name].md       # Plan documents
├── 02-design/
│   └── features/
│       └── [feature-name].md       # Design documents
├── 03-analysis/
│   └── [feature-name]-gap.md       # Gap analysis reports
└── 04-report/
    └── [feature-name]-report.md    # Completion reports
```

## Plan Document Template

```markdown
# Plan: [Feature Name]

## Overview
Brief description of the feature.

## Goals
- Goal 1
- Goal 2

## User Stories
- As a [user], I want [action] so that [benefit]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Implementation Approach
High-level approach to implementation.

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Risk 1 | High | Strategy |

## Timeline
Estimated effort and milestones.
```

## Design Document Template

```markdown
# Design: [Feature Name]

## Architecture Overview
System architecture description.

## Components
- Component 1: Description
- Component 2: Description

## Data Models
[Data model definitions]

## API Specifications
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/... | GET | Description |

## Security Considerations
- Security point 1
- Security point 2

## Testing Strategy
- Unit tests
- Integration tests
- E2E tests
```

## Gap Analysis Criteria

Gap analysis checks for:
1. **Completeness**: Are all planned features implemented?
2. **Quality**: Code quality, test coverage, documentation
3. **Security**: Security best practices followed
4. **Performance**: Performance requirements met
5. **Accessibility**: Accessibility standards followed

**Scoring:**
- 100%: Perfect implementation
- 90-99%: Minor issues
- 70-89%: Significant gaps
- <70%: Major rework needed

## Multi-Language Support

PDCA supports triggers in 8 languages:
- **English**: plan, design, analyze, verify, report
- **Korean**: 계획, 설계, 분석, 검증, 보고서
- **Japanese**: 計画, 設計, 分析, 検証, 報告
- **Chinese**: 计划, 设计, 分析, 验证, 报告
- **Spanish**: planificar, diseño, analizar, informe
- **French**: planifier, conception, analyser, rapport
- **German**: planen, Entwurf, analysieren, Bericht
- **Italian**: pianificare, progettazione, analizzare, rapporto

## Integration with Other bkit Skills

- **development-pipeline**: Use for 9-phase development workflow
- **frontend-architect**: Use for UI/UX design phase
- **security-architect**: Use for security review phase
- **code-analyzer**: Use for code quality checks

## Best Practices

1. **Always create Plan first** - Don't jump to implementation
2. **Design before coding** - Technical design reduces rework
3. **Check after doing** - Gap analysis catches issues early
4. **Iterate when needed** - Don't accept <90% quality
5. **Document everything** - Reports help future development

## Example Usage

**Full PDCA Cycle:**

1. User asks for user authentication feature
2. Create plan: /pdca plan "User Authentication"
3. Create design: /pdca design "User Authentication"
4. Implement: /pdca do "User Authentication"
5. Analyze: /pdca analyze "User Authentication"
6. Iterate if needed: /pdca iterate "User Authentication"
7. Report: /pdca report "User Authentication"

## Notes

- **AI is not perfect**: Always verify critical decisions
- **Context matters**: PDCA phase information persists across sessions
- **Progressive disclosure**: Full skill activates when PDCA commands are used
- **Project-level**: Documents stored in project directory

---

*bkit PDCA v1.5.1 - OpenCode Edition*
*Adapted from bkit-gemini by POPUP STUDIO*
