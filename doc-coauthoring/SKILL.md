---
name: doc-coauthoring
description: Guide users through structured workflow for co-authoring documentation. Use when user wants to write docs, proposals, technical specs, or decision docs.
---

# Doc Co-Authoring Workflow

Structured workflow for collaborative document creation.

## When to Use

**Trigger conditions:**
- User mentions: "write a doc", "draft a proposal", "create a spec"
- User mentions: "PRD", "design doc", "decision doc", "RFC"
- User is starting a substantial writing task

**Offer the workflow:**
1. **Context Gathering**: User provides context, Claude asks questions
2. **Refinement & Structure**: Iteratively build each section
3. **Reader Testing**: Test with fresh context to catch blind spots

## Stage 1: Context Gathering

### Initial Questions
1. What type of document is this?
2. Who's the primary audience?
3. What's the desired impact?
4. Is there a template or format to follow?
5. Any constraints?

### Info Dumping
Encourage user to dump all context:
- Background on project/problem
- Related discussions or documents
- Why alternatives aren't being used
- Organizational context
- Technical architecture
- Stakeholder concerns

**Format**: Stream-of-consciousness, links to documents, or paste content

## Stage 2: Refinement & Structure

1. **Outline**: Create structure based on context
2. **Draft sections**: Iterate through each section
3. **Refine**: Improve clarity, flow, and impact
4. **Add examples**: Concrete illustrations where helpful

## Stage 3: Reader Testing

1. Start new session with NO document context
2. Ask "reader" to review and identify gaps
3. Incorporate feedback
4. Final polish

## Best Practices

- Don't wait for perfect - iterate
- Ask clarifying questions throughout
- Test with fresh eyes before sharing
- Keep audience in mind always
- Use structure to organize complex ideas
