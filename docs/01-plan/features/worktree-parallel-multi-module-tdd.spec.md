# Spec: worktree-parallel-multi-module-tdd

## Executive Summary
Add three Orca-only `hmad-dispatch` worktree verbs plus a Phase-5 parallel-fanout protocol so independent impl-plan modules implement concurrently in isolated Orca worktrees, with the existing serial path as the unconditional fallback.

## Goal
Collapse H-MAD Phase-5 wall-clock for multi-module features from ~sum(modules) toward ~max(module) by running independent modules in parallel, without weakening per-module RED/GREEN TDD or the agy spec-compliance review, and without changing behavior on the cmux / linear-DAG / no-coordinator paths.

## Functional Requirements

### FR-1: `worktree-create` verb
- **Description**: New Orca-only `hmad-dispatch` subcommand `worktree-create <name> [--agent <id>] [--base <ref>] [--prompt-file <path>]` wrapping `orca worktree create --name <name> [--agent <id>] [--base-branch <ref>] [--prompt <text>] --json`. Prints the created worktree selector/handle to stdout (parsed from `.result` JSON). Mirrors the Tier-2 guard pattern: refuse with non-zero + `[H-MAD]` marker when substrate ≠ orca.
- **Acceptance Criteria**:
  - AC-1.1: Given substrate=orca, `worktree-create mymod --agent a1 --base main` invokes `orca worktree create --name mymod --agent a1 --base-branch main --json` (argv asserted against an `orca` stub).
  - AC-1.2: The verb parses the worktree selector from the stub's `--json` output (`.result.worktree.handle` or documented key) and prints exactly that selector on stdout, nothing else.
  - AC-1.3: Given substrate=cmux (or no orca), the verb exits non-zero, prints no `orca` invocation, and emits a `[H-MAD] ... worktree-create refused substrate=<s>` marker.
  - AC-1.4: `--prompt-file <path>` reads the file and passes its contents as `--prompt <text>` (file-indirection per CLAUDE.md §F-12; never a bare inline blob on argv).

### FR-2: `worktree-ps` verb
- **Description**: `hmad-dispatch worktree-ps [--limit <n>]` wrapping `orca worktree ps [--limit <n>] --json`; passes the parsed JSON summary through to stdout for the orchestrator to consume.
- **Acceptance Criteria**:
  - AC-2.1: `worktree-ps` invokes `orca worktree ps --json`; `worktree-ps --limit 3` appends `--limit 3` (argv asserted).
  - AC-2.2: stdout is the JSON `.result` payload (valid JSON, parseable by the caller), not raw scrape text.
  - AC-2.3: substrate ≠ orca → non-zero + refusal marker (same contract as AC-1.3).

### FR-3: `worktree-rm` verb
- **Description**: `hmad-dispatch worktree-rm <selector> [--force]` wrapping `orca worktree rm --worktree <selector> [--force] --json`. Used for cleanup on success and in the halt path.
- **Acceptance Criteria**:
  - AC-3.1: `worktree-rm wt-7` invokes `orca worktree rm --worktree wt-7 --json`; `--force` appends `--force` (argv asserted).
  - AC-3.2: A non-zero from `orca` (e.g. unknown selector) surfaces as a non-zero exit + `[H-MAD]` marker; the verb does not swallow the failure.
  - AC-3.3: substrate ≠ orca → non-zero + refusal marker.

### FR-4: Phase-5 parallel-fanout protocol (SKILL.md)
- **Description**: A documented Phase-5 sub-protocol: partition impl-plan tasks into independent (`Dependencies on other tasks: None`) vs dependent; for each independent task create one worktree + dispatch one Codex agent (RED then GREEN), `await` each `worker_done` via Tier-2 verbs, merge per module in dependency order; dependent tasks run serially in topological order. Guarded so it engages ONLY when substrate=orca AND a coordinator pin is present AND ≥2 independent tasks exist.
- **Acceptance Criteria**:
  - AC-4.1: SKILL.md Phase-5 section documents the partition rule, the fanout loop, the per-module merge, and the explicit engage-conditions.
  - AC-4.2: The engage-condition is stated as a conjunction (orca ∧ coordinator-pin ∧ ≥2 independent tasks); any unmet condition → serial fallback.
  - AC-4.3: The halt path documents `worktree-rm` cleanup of any worktree created during a fanout that then halted.

### FR-5: Serial-path fallback preserved
- **Description**: When fanout does not engage, Phase 5 executes exactly the pre-existing serial dispatch (no behavioral change on cmux, linear DAGs, or unpinned-coordinator Orca).
- **Acceptance Criteria**:
  - AC-5.1: With substrate=cmux, no worktree verb is invoked and the documented Phase-5 flow is byte-identical to the current serial protocol (SKILL.md diff touches only additive fanout content).
  - AC-5.2: With substrate=orca but a fully linear impl-plan (every task has a dependency), fanout does not engage (0 worktrees created) and the serial path runs.

### FR-6: Concurrency bound
- **Description**: A configurable cap on concurrent worktrees via `HMAD_ORCA_MAX_WORKTREES` (default 4); the fanout creates at most that many worktrees at once, queuing the rest.
- **Acceptance Criteria**:
  - AC-6.1: `HMAD_ORCA_MAX_WORKTREES` unset → default 4 documented and applied.
  - AC-6.2: The fanout protocol documents that independent tasks beyond the cap queue until a worktree frees (no silent drop — over-cap tasks are logged).

## Non-Functional Requirements
- Performance: fanout must not add per-module overhead beyond one `worktree create` + one `worktree rm` per module; the win is wall-clock, not CPU.
- Security: all agent prompts dispatched via file-indirection (CLAUDE.md §F-12); no bare prompt blobs on argv (FR-1 AC-1.4).
- Compatibility: additive only — no change to existing `hmad-dispatch` verbs, the cmux path, or the state schema beyond optional fanout telemetry. Existing tests (`test_hmad_dispatch.py`) must stay green.

## Out-of-Scope
- Live-Orca e2e validation against real Orca-hosted agents (standing gap across Tier 1/2/3; deferred carry, not a completion blocker).
- Automatic merge-conflict resolution between worktrees — on conflict, halt the module and fall back to serial re-dispatch (documented, not automated).
- Parallelizing dependent tasks or re-ordering the impl-plan DAG.
- Changes to Tier-2 orchestration verbs themselves (fanout consumes them as-is).

## Assumptions
- `orca worktree create --agent <id> --prompt <text>` both creates the worktree and attaches/seeds the agent (to be reconciled against `agent-context --json` at design; if attach is separate, design adds an `orchestration dispatch` targeting the worktree handle).
- The impl-plan's `Dependencies on other tasks` field is the authoritative independence signal (Phase 5a already produces it).
- Coordinator pin (`HMAD_ORCA_COORDINATOR_TERMINAL`) presence is the Tier-2 signal that structured orchestration/`await` is available.

## Version History
- v1.0: Initial specification draft.
