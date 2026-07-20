# Plan Audit v1 — worktree-parallel-multi-module-tdd

Reviewer: agy (Gemini 3.1 Pro High), Reviewer.adversarial_consistency. Cycle 1.

## Summary
The plan provides a well-scoped additive approach for introducing Orca worktree support for Phase-5 parallel execution while safely preserving the serial cmux fallback. Strong Axis B adherence: `[H-MAD]` marker discipline, Tier-2 JSON-extraction reuse (single-source), no new external dependency. Critical gaps in error-path detection and default configuration need addressing.

## Must-fix
- Axis A (Gap): Missing mechanism for detecting merge conflicts — the risk mitigation states "conflict → halt module → serial re-dispatch" but fails to define how a conflict is detected during per-module merge (git merge exit code, unmerged paths). Hard gap making the mitigation un-implementable as stated.
- Axis A (Gap): Undefined default for concurrency cap — plan introduces `HMAD_ORCA_MAX_WORKTREES` for FR-6 but leaves the default value unstated in the plan body; unstated assumption for the unset-env execution path (spec FR-6 says 4; plan must state it).

## Should-fix
- Axis A (Gap): Ambiguous cleanup scope — the halt-path `worktree-rm` cleanup does not clarify whether a module halt/conflict tears down all parallel worktrees in the current fanout group or only the failed worktree.

## Nit
- Plan references reconciling against `orca agent-context --json` schema v1 but also extracts from `orca worktree ... --json`; clarify whether the worktree command shares the same schema versioning or needs a separate schema pin.
