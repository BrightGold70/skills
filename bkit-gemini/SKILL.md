---
name: bkit-gemini
description: |
  bkit (Vibecoding Kit) - Comprehensive AI development methodology combining PDCA (Plan-Do-Check-Act) with Context Engineering for systematic AI-native development. 
  Includes 16 specialized agents, 21 domain skills, 9-phase development pipeline, and intelligent context management.
  
  Use for: Feature planning, design documents, code architecture, security analysis, quality assurance, and full development workflow management.
  Activate: Any development task, planning, design, review, or when systematic methodology is needed.
---

# bkit - Vibecoding Kit (OpenCode Edition)

> **PDCA methodology + Context Engineering for AI-native development**

*Adapted from bkit-gemini v1.5.1 by POPUP STUDIO*

---

## Overview

**bkit** is a comprehensive development methodology that transforms how you build software with AI. It provides structured development workflows through:

- **PDCA Cycle**: Plan → Design → Do → Check → Act
- **16 Specialized Agents**: Role-based AI agents for different tasks
- **21 Domain Skills**: Progressive disclosure of expert knowledge
- **9-Phase Pipeline**: Systematic development from schema to deployment
- **Context Engineering**: Intelligent context management and persistence

---

## What is Context Engineering?

**Context Engineering** is the systematic curation of context tokens for optimal LLM inference:

```
Traditional Prompt Engineering:
  "The art of writing good prompts"

Context Engineering:
  "The art of designing systems that integrate prompts, tools, and state
   to provide LLMs with optimal context for inference"
```

---

## Core Philosophy

### Always Apply These Rules

1. **New feature request** → Check/create Plan document first
2. **Plan complete** → Create Design document before implementation
3. **After implementation** → Run Gap analysis
4. **Gap Analysis < 90%** → Auto-improvement iteration
5. **Gap Analysis >= 90%** → Generate completion report
6. **Always** verify important decisions with the user

---

## PDCA Workflow

### Plan Phase
Create feature plan document including:
- Feature overview and goals
- User stories and requirements  
- Success criteria
- Implementation approach
- Risk assessment

### Design Phase
Create technical design document with:
- Architecture overview
- Component breakdown
- Data models
- API specifications
- Security considerations

### Do Phase
Implementation guidance:
- Code structure recommendations
- Step-by-step implementation steps
- Best practices and patterns

### Check Phase
Gap analysis comparing:
- Design document vs implementation
- Missing features
- Quality issues
- Security concerns

### Act Phase
Auto-improvement iteration:
- Reviews gap analysis results
- Generates specific fixes
- Prioritizes issues by severity
- Creates action items

---

## 16 Specialized Agents

### Activation Triggers

| Agent | Triggers |
|-------|----------|
| **cto-lead** | team, project lead, architecture decision, CTO, orchestrate, strategic direction, team management |
| **frontend-architect** | UI design, component structure, design system, frontend, UX, responsive |
| **security-architect** | security, vulnerability, OWASP, penetration, audit, encryption, authentication |
| **product-manager** | requirements, user stories, prioritization, roadmap, features, product |
| **qa-strategist** | testing strategy, test plan, quality metrics, coverage, automation |
| **gap-detector** | gap analysis, compare design vs implementation, missing features, consistency check |
| **pdca-iterator** | iterate, improve, fix issues, auto-fix, refinement |
| **code-analyzer** | code review, quality scan, static analysis, lint, complexity |
| **report-generator** | report, summary, documentation, completion, status |
| **design-validator** | design review, design validation, architecture review |
| **qa-monitor** | QA testing, log monitoring, integration testing, E2E |
| **starter-guide** | beginner, starter, getting started, learning, help |
| **pipeline-guide** | pipeline, workflow, development order, phases |
| **bkend-expert** | backend, bkend, BaaS, server, database, API |
| **enterprise-expert** | enterprise, microservices, large scale, architecture |
| **infra-architect** | infrastructure, AWS, Kubernetes, Terraform, DevOps, deployment |

### Agent Usage Examples

**cto-lead** - Team orchestration:
- "Orchestrate a team to build the authentication system"
- "What's the best architecture for this microservices project?"

**frontend-architect** - UI/UX:
- "Design the component structure for the dashboard"
- "Create a design system for our UI"

**security-architect** - Security:
- "Review this code for vulnerabilities"
- "What are the OWASP Top 10 risks in this app?"

**gap-detector** - Analysis:
- "Compare the design document with implementation"
- "What's missing from the current implementation?"

**code-analyzer** - Quality:
- "Review the codebase for quality issues"
- "Analyze code complexity and maintainability"

---

## 21 Domain Skills

### Progressive Disclosure

Skills use progressive disclosure - only metadata loads initially, full instructions inject when activated.

| Skill | Triggers |
|-------|----------|
| **pdca** | /pdca, plan, design, analyze, iterate, report |
| **starter** | static site, portfolio, beginner, starter level |
| **dynamic** | login, fullstack, authentication, dynamic level |
| **enterprise** | microservices, k8s, terraform, enterprise level |
| **development-pipeline** | where to start, development order, pipeline |
| **code-review** | review code, code review, check quality |
| **zero-script-qa** | test logs, QA without scripts, log monitoring |
| **mobile-app** | React Native, Flutter, iOS app, Android app |
| **desktop-app** | Electron, Tauri, desktop app |
| **bkit-templates** | plan template, design template, document templates |
| **bkit-rules** | rules, guidelines, conventions |
| **gemini-cli-learning** | learn, setup, configuration |
| **phase-1-schema** | schema, data model, database design |
| **phase-2-convention** | coding rules, conventions, style guide |
| **phase-3-mockup** | mockup, wireframe, prototype, UI design |
| **phase-4-api** | API design, REST endpoints, backend |
| **phase-5-design-system** | design system, component library |
| **phase-6-ui-integration** | frontend integration, API client |
| **phase-7-seo-security** | SEO, security hardening, performance |
| **phase-8-review** | architecture review, gap analysis |
| **phase-9-deployment** | CI/CD, production deployment |

---

## 9-Phase Development Pipeline

### Phase 1: Schema Design
- Data modeling
- Database schema
- Entity relationships

### Phase 2: Conventions
- Coding standards
- Naming conventions
- File structure

### Phase 3: Mockup
- UI/UX design
- Wireframes
- Prototypes

### Phase 4: API Design
- REST endpoints
- Data contracts
- Authentication

### Phase 5: Design System
- Component library
- Theming
- UI tokens

### Phase 6: UI Integration
- Frontend implementation
- API integration
- State management

### Phase 7: SEO & Security
- Performance optimization
- Security hardening
- SEO setup

### Phase 8: Review
- Architecture review
- Gap analysis
- Quality checks

### Phase 9: Deployment
- CI/CD pipelines
- Production deployment
- Monitoring setup

---

## Project Levels

| Level | Description | Stack | Detection |
|-------|-------------|-------|-----------|
| **Starter** | Static websites, portfolios | HTML, CSS, JS | Default (no special files) |
| **Dynamic** | Fullstack applications | Next.js, BaaS | `docker-compose.yml`, `.mcp.json` |
| **Enterprise** | Microservices | K8s, Terraform, MSA | `kubernetes/`, `terraform/` |

### Level-Based Agent Assignment

- **Starter** → starter-guide agent
- **Dynamic** → bkend-expert agent  
- **Enterprise** → enterprise-expert + infra-architect agents

---

## Multi-Language Support

bkit automatically detects triggers in 8 languages:

| Language | Keywords |
|----------|----------|
| **English** | static website, verify, analyze, plan, design |
| **Korean** | 정적 웹, 검증, 분석, 계획, 설계 |
| **Japanese** | 静的サイト, 確認, 分析, 計画, 設計 |
| **Chinese** | 静态网站, 验证, 分析, 计划, 设计 |
| **Spanish** | sitio web estático, verificar, analizar |
| **French** | site web statique, verifier, analyser |
| **German** | statische Webseite, prufen, analysieren |
| **Italian** | sito web statico, verificare, analizzare |

---

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

---

## Document Templates

### Plan Document

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
High-level approach.

## Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
```

### Design Document

```markdown
# Design: [Feature Name]

## Architecture Overview
System architecture.

## Components
- Component 1: Description

## Data Models
[Data model definitions]

## API Specifications
| Endpoint | Method | Description |
|----------|--------|-------------|

## Security Considerations
- Security point 1
```

---

## Gap Analysis Scoring

| Score | Status | Action |
|-------|--------|--------|
| 100% | Perfect | Generate report |
| 90-99% | Minor issues | Generate report with notes |
| 70-89% | Significant gaps | Iterate |
| <70% | Major rework | Iterate + redesign |

---

## Configuration

### Project Level Override

Set environment variable to override auto-detection:
```
BKIT_PROJECT_LEVEL=Starter|Dynamic|Enterprise
```

### Output Styles

| Style | Best For |
|-------|----------|
| bkit-learning | Beginners - step-by-step explanations |
| bkit-pdca-guide | Standard development - PDCA workflow |
| bkit-enterprise | Enterprise - technical architecture |
| bkit-pdca-enterprise | Enterprise PDCA - combined |

---

## Best Practices

1. **Always create Plan first** - Don't jump to implementation
2. **Design before coding** - Technical design reduces rework
3. **Check after doing** - Gap analysis catches issues early
4. **Iterate when needed** - Don't accept <90% quality
5. **Document everything** - Reports help future development
6. **Use appropriate level** - Match methodology to project complexity

---

## Example Usage

### Full Feature Development

1. Plan: "Create user authentication feature"
2. Design: "Design the auth system architecture"
3. Do: "Implement the login/logout flow"
4. Check: "Analyze gaps between design and code"
5. Act: "Fix identified issues or generate report"

### Quick Task

For simple tasks, use appropriate agents directly:
- Code review → Use code-analyzer agent
- Security check → Use security-architect agent
- UI design → Use frontend-architect agent

---

## Integration Notes

- **AI is not perfect**: Always verify critical decisions
- **Context persists**: Phase information stored in project
- **Progressive disclosure**: Full skill activates when needed
- **Flexible**: Use components individually or as full workflow

---

## Credits

- Original: [bkit-gemini](https://github.com/popup-studio-ai/bkit-gemini) by POPUP STUDIO
- Platform: Gemini CLI → OpenCode adaptation
- License: Apache-2.0

---

*bkit-gemini v1.5.1 - OpenCode Edition*
*PDCA methodology + Context Engineering for AI-native development*
