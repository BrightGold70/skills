# Plan Audit v1 — orca-native-orchestration

Reviewer: agy (Gemini 3.1 Pro High). Dispatched via hmad-dispatch (cmux surface:5). Cycle 1.

## Summary
The plan cleanly introduces opt-in orchestration-mode verbs for Orca without disrupting the existing scrape transport, adhering to backward compatibility and dependency constraints. One internal naming contradiction must be resolved before implementation.

## Must-fix
- Inconsistent verb naming — the Executive Summary lists the underlying orca command `check` while the Implementation Strategy/Risks use the hmad-dispatch verb `await` (`_cmd_await`). Resolve to consistent naming (the hmad verb is `await`, wrapping `orca orchestration check`).

## Should-fix
None

## Nit
None
