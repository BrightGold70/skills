---
name: orchestrator
description: Multi-agent coordination specialist. Use when task requires multiple areas of expertise or parallel execution. Triggers: "orchestrate", "coordinate", "multiple", "full stack", "complex task".
allowed-tools: task, Glob, Grep, Read
---

# ORCHESTRATOR MODE - Multi-Agent Coordination

## Purpose

Breaks complex tasks into subtasks, coordinates parallel execution, and synthesizes results from multiple areas of expertise.

## When Triggered

- Task requires multiple expertise areas
- User says "orchestrate", "coordinate"
- "full stack" feature request
- Complex multi-component task

---

## Orchestration Workflow

### Step 1: Analyze Task

Break down the request:
1. What are the components?
2. What expertise is needed?
3. What can run in parallel?
4. What has dependencies?

### Step 2: Identify Subtasks

Create subtask list:
```
Task: [User Request]

Subtasks:
1. [Frontend] - UI components
2. [Backend] - API endpoints  
3. [Database] - Schema changes
4. [DevOps] - Deployment config
```

### Step 3: Determine Execution Strategy

| Strategy | When |
|----------|------|
| **Sequential** | Tasks depend on each other |
| **Parallel** | Independent tasks |
| **Fan-out/Fan-in** | Multiple sub-tasks → single result |

### Step 4: Coordinate Execution

For each subtask:
1. Identify required skill/agent
2. Define input/output contracts
3. Execute (parallel when possible)
4. Collect results

### Step 5: Synthesize Results

Combine all subtask results:
1. Verify compatibility
2. Resolve conflicts
3. Integrate components
4. Test end-to-end

---

## Example: Full Stack Feature

**Request**: "Add user authentication to the app"

**Breakdown**:
```
1. [Frontend] Login form + auth state
2. [Backend] Auth endpoints (login/logout)
3. [Database] Users table + tokens
4. [Security] JWT + hashing
```

**Execution**: 
- Tasks 2, 3, 4 can run in parallel
- Task 1 (Frontend) depends on 2 (API contracts)
- Task 5 (Integration) runs last

---

## Output Format

```markdown
## Orchestrating: [Task Name]

### Task Breakdown
| # | Component | Expertise | Depends On |
|---|-----------|-----------|------------|
| 1 | Frontend | frontend | - |
| 2 | Backend | backend | - |
| 3 | Database | database | - |
| 4 | Integration | orchestrator | 1, 2, 3 |

### Execution Strategy
[Sequential/Parallel/Fan-out]

### Progress
- [ ] Component 1: [Status]
- [ ] Component 2: [Status]
- [ ] Component 3: [Status]

### Results Synthesis
[How components fit together]

### Final Verification
[End-to-end test results]
```

---

## Coordination Patterns

### Parallel Execution
```typescript
// Independent tasks run simultaneously
task(category="frontend", ...)
task(category="backend", ...)
task(category="database", ...)
// Then synthesize results
```

### Sequential with Dependencies
```typescript
// Task B needs A's output
resultA = task(...)
resultB = task(input: resultA.output)
```

### Fan-Out/Fan-In
```typescript
// Multiple workers → single result
results = parallel(task(...), task(...), task(...))
final = synthesize(results)
```

---

## Best Practices

1. **Define clear interfaces** - What does each subtask produce/consume?
2. **Minimize dependencies** - More parallel = faster
3. **Fail fast** - If subtask fails, stop and assess
4. **Verify integration** - Don't assume components work together
5. **Report progress** - Keep user informed

---

## Related Skills

- **parallel-agents**: Parallel execution patterns
- **plan-writing**: Task breakdown
- **frontend-design**: UI components
- **nodejs-best-practices**: Backend patterns
- **database-design**: Schema design
