---
name: bkit-development-pipeline
description: 9-phase development pipeline for structured software development. Guides through Schema Design → Conventions → Mockup → API Design → Design System → UI Integration → SEO/Security → Review → Deployment. Use for complex projects requiring systematic development workflow.
---

# bkit Development Pipeline

9-phase development pipeline for systematic software development.

## Overview

The development pipeline provides a structured approach to building software, breaking down complex projects into 9 manageable phases.

## The 9 Phases

### Phase 1: Schema Design
**Focus**: Data architecture and database design

**Tasks**:
- Define data entities and relationships
- Create database schema
- Design data models
- Plan data migrations

**Deliverables**:
- Entity Relationship Diagram (ERD)
- Database schema documentation
- Data model definitions
- Migration strategy

**Command**: /pipeline phase-1

### Phase 2: Conventions & Standards
**Focus**: Coding standards and project conventions

**Tasks**:
- Define naming conventions
- Set up linting rules
- Establish code style guide
- Configure CI/CD pipelines

**Deliverables**:
- Coding standards document
- Linting configuration
- Git workflow documentation
- Project structure guidelines

**Command**: /pipeline phase-2

### Phase 3: UI/UX Mockup
**Focus**: User interface design and prototyping

**Tasks**:
- Create wireframes
- Design user flows
- Build interactive prototypes
- Define design system basics

**Deliverables**:
- Wireframes
- Interactive prototypes
- User flow diagrams
- Design specifications

**Command**: /pipeline phase-3

### Phase 4: API Design
**Focus**: Backend API architecture and specifications

**Tasks**:
- Define API endpoints
- Design request/response schemas
- Plan authentication/authorization
- Document API specifications

**Deliverables**:
- API specification (OpenAPI/Swagger)
- Authentication flow diagrams
- API endpoint documentation
- Error handling strategy

**Command**: /pipeline phase-4

### Phase 5: Design System
**Focus**: Component library and design tokens

**Tasks**:
- Create design tokens (colors, typography, spacing)
- Build reusable components
- Document component usage
- Set up Storybook/component library

**Deliverables**:
- Design tokens documentation
- Component library
- Usage guidelines
- Design system documentation

**Command**: /pipeline phase-5

### Phase 6: UI Integration
**Focus**: Frontend development and API integration

**Tasks**:
- Implement UI components
- Connect to APIs
- Handle state management
- Implement error handling

**Deliverables**:
- Frontend implementation
- API integration layer
- State management setup
- Error handling implementation

**Command**: /pipeline phase-6

### Phase 7: SEO & Security
**Focus**: Search optimization and security hardening

**Tasks**:
- Implement SEO meta tags
- Set up analytics
- Security audit
- Performance optimization
- Accessibility improvements

**Deliverables**:
- SEO implementation
- Security audit report
- Performance metrics
- Accessibility audit

**Command**: /pipeline phase-7

### Phase 8: Architecture Review
**Focus**: Code review and gap analysis

**Tasks**:
- Code quality review
- Architecture compliance check
- Design implementation review
- Gap analysis

**Deliverables**:
- Code review report
- Gap analysis document
- Refactoring recommendations
- Quality metrics

**Command**: /pipeline phase-8

### Phase 9: Deployment
**Focus**: Production deployment and monitoring

**Tasks**:
- Set up deployment pipeline
- Configure monitoring
- Deploy to production
- Post-deployment verification

**Deliverables**:
- Deployment configuration
- Monitoring setup
- Production deployment
- Post-deployment report

**Command**: /pipeline phase-9

## Pipeline Commands

### /pipeline start
Initializes the pipeline for a new project.
- Detects project type (Starter/Dynamic/Enterprise)
- Sets up pipeline tracking
- Creates initial documentation

### /pipeline status
Shows current pipeline status:
- Current phase
- Completed phases
- Phase progress
- Next steps

### /pipeline next
Advances to the next phase.
- Verifies current phase completion
- Sets up next phase requirements
- Provides phase-specific guidance

### /pipeline phase-<number>
Jumps to specific phase with detailed guidance.

## Project Levels

### Starter Level
- Static websites
- Simple portfolios
- Basic web apps
- **Stack**: HTML, CSS, JavaScript

### Dynamic Level
- Fullstack applications
- Database-driven apps
- User authentication
- **Stack**: Next.js, React, BaaS (Firebase/Supabase)

### Enterprise Level
- Microservices architecture
- High-scale applications
- Complex infrastructure
- **Stack**: Kubernetes, Terraform, Microservices

## Pipeline Workflow

**Starting a New Project:**
```
1. /pipeline start
   → Detects project level
   → Creates pipeline tracking

2. Work through each phase:
   /pipeline phase-1  (Schema Design)
   /pipeline phase-2  (Conventions)
   /pipeline phase-3  (Mockup)
   ...continue through all 9 phases

3. /pipeline status
   → Check overall progress

4. /pipeline next
   → Advance to next phase
```

## Phase Integration with PDCA

Each pipeline phase follows PDCA internally:
- **Plan**: Phase requirements and goals
- **Do**: Execute phase tasks
- **Check**: Verify phase completion
- **Act**: Move to next phase or iterate

## Best Practices

1. **Don't skip phases** - Each phase builds on previous
2. **Complete before advancing** - Ensure quality at each phase
3. **Document everything** - Maintains project knowledge
4. **Review regularly** - Use /pipeline status frequently
5. **Iterate within phases** - Don't be afraid to revisit

## Integration with Other Skills

- **bkit-pdca**: Each phase uses PDCA methodology
- **bkit-frontend-architect**: Used in phases 3, 5, 6
- **bkit-security-architect**: Used in phase 7
- **bkit-code-analyzer**: Used in phase 8

## Example: Full Pipeline Execution

```
# Initialize
/pipeline start

# Phase 1: Schema
/pipeline phase-1
[Design database schema for user management]

# Phase 2: Conventions
/pipeline phase-2
[Set up ESLint, Prettier, Git workflow]

# Phase 3: Mockup
/pipeline phase-3
[Create Figma mockups for auth screens]

# Phase 4: API Design
/pipeline phase-4
[Design REST API endpoints]

# Phase 5: Design System
/pipeline phase-5
[Create component library with Storybook]

# Phase 6: UI Integration
/pipeline phase-6
[Implement frontend and connect APIs]

# Phase 7: SEO & Security
/pipeline phase-7
[Add meta tags, run security audit]

# Phase 8: Review
/pipeline phase-8
[Code review, gap analysis]

# Phase 9: Deployment
/pipeline phase-9
[Deploy to production]
```

## Multi-Language Support

Pipeline recognizes triggers in multiple languages:
- **English**: pipeline, phase, development
- **Korean**: 파이프라인, 개발 단계
- **Japanese**: パイプライン, 開発フェーズ
- **Chinese**: 流水线, 开发阶段

## Document Structure

```
pipeline-docs/
├── status.json              # Current phase tracking
├── phase-1-schema/
│   └── schema.md
├── phase-2-conventions/
│   └── conventions.md
├── phase-3-mockup/
│   └── mockup.md
├── phase-4-api/
│   └── api-spec.md
├── phase-5-design-system/
│   └── design-system.md
├── phase-6-ui-integration/
│   └── integration.md
├── phase-7-seo-security/
│   └── seo-security.md
├── phase-8-review/
│   └── review-report.md
└── phase-9-deployment/
    └── deployment.md
```

## Notes

- **Progressive disclosure**: Full skill activates when pipeline commands are used
- **Project-level tracking**: Pipeline state stored in project directory
- **Adaptive**: Adjusts guidance based on project level
- **Compatible with PDCA**: Works seamlessly with bkit-pdca skill

---

*bkit Development Pipeline v1.5.1 - OpenCode Edition*
*Adapted from bkit-gemini by POPUP STUDIO*
