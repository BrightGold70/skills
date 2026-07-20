# Orca Adaptation Candidates — h-mad + HemaSuite

Backlog of Orca (`stablyai/orca`) capabilities worth adapting into the **h-mad skill** and/or **HemaSuite**, derived from `orca agent-context --json` (schema v1, 202 commands). Operator (Hawk) will implement **Tier-3** + the **Medium** candidates in a future session.

## Already shipped (this arc — for context)
- **Substrate support** (`hmad-dispatch.sh`, cmux **or** orca, auto-detected) — BrightGold70/skills.
- **Tier 1 · `orca-native-transport`** — corrected the guessed Orca verbs to schema v1: `wait --for tui-idle --timeout-ms`, `read --limit`, real `.result.terminals[].handle` liveness/identity. Shipped `a2cdfe2`.
- **Tier 2 · `orca-native-orchestration`** — 5 Orca-only verbs (`task-create`/`dispatch`/`await`/`gate-create`/`gate-resolve`) wrapping `orca orchestration *`; structured `worker_done`+`await` verdict collection + native decision gates; coordinator pin injected into the task spec. Shipped `f1bcf97`.
- **HemaSuite · `orca-launch-profile`** — auto-detected `orca` headless monitoring profile in `launch_hemasuite.sh` (`orca terminal create` monitor surfaces). Shipped BrightGold70/HemaSuite `89087615`.

---

## Tier 3 (RECOMMENDED — build next) · h-mad: worktree-based parallel multi-module TDD

**Problem**: H-MAD Phase 5 dispatches Codex **serially** — one module at a time in the shared working tree. The impl-plan already decomposes into a per-module task DAG with explicit dependencies; independent tasks could run in parallel but don't.

**Orca capability**:
- `orca worktree create --name <module> [--agent <id>] [--prompt <task>] [--base-branch <ref>] [--json]` — isolated Orca-managed git worktree per module (no cross-module file conflict).
- `orca worktree ps [--json]` — compact orchestration summary across worktrees.
- `orca worktree list --json` / `orca worktree rm --worktree <sel> [--force] [--json]` — enumerate / clean up.

**Adaptation**: new `hmad-dispatch` verbs (Orca-only, mirroring Tier 2's guard/JSON pattern): `worktree-create <name> [--agent <a>] [--base <ref>]` → worktree id; `worktree-ps` → JSON summary; `worktree-rm <sel>`. Then Phase 5 fans out **independent** impl-plan tasks: one worktree + one dispatched agent each, `await` each `worker_done` (Tier 2), merge per module. Dependent tasks stay serial. This turns Tier 2's coordination into true parallelism — the missing piece.

**Value**: high — attacks the serial-Codex bottleneck; wall-clock of a multi-module feature drops toward slowest-single-module.
**Caveat**: needs Orca-hosted agents to live-validate (can't in a cmux session) — same live-Orca-e2e gap as Tier 1/2. Unit-test the verb argv/JSON against `orca` stubs.
**Scope**: `hmad-dispatch.sh` worktree verbs + SKILL.md Phase-5 parallel-fanout section + tests. Additive; serial path stays the fallback.

---

## Medium (operator will also implement)

### M1 · h-mad + HemaSuite: `file diff` / `file open-changed` — surface diffs to the operator
**Orca**: `orca file diff <path> [--staged] [--worktree <sel>]`; `orca file open-changed [--mode edit|diff|both] [--worktree <sel>]` — open workspace diffs / changed files in the Orca editor.
**Adaptation**: during the human-in-loop gates — plan/design approval, Phase-6 verification — the orchestrator opens the Phase-5 diff (`file open-changed --mode diff`) so the operator reviews in Orca's editor instead of scrollback. For **HemaSuite**: surface generated manuscript DOCX / desk-check diffs.
**Value**: medium (ergonomic, human-review quality). Small `hmad-dispatch` verb or a SKILL note.

### M2 · HemaSuite: `automations` — schedule long live-e2e / regression runs
**Orca**: `orca automations create --name <n> --trigger <preset|cron|rrule> --prompt <text> --provider agent [--precheck <command>] [--repo|--workspace|--project ...]`; `automations run/runs/list/edit/remove`.
**Adaptation**: schedule HemaSuite's long **operator-triggered** live-e2e (the standing carry items — anemia-jmj narrative e2e, review-pipeline-correctness, full regression suites) as cron/preset Orca automations with a `--precheck` (e.g. `hpw doctor`) and `--provider agent`. Nightly/scheduled instead of manual.
**Value**: medium (real, IF HemaSuite runs under Orca). Requires HemaSuite executing in an Orca workspace.

---

## Low / speculative (recorded, not prioritized)
- **`orca linear`** — reads Linear ticket context for agents. **N/A**: HemaSuite uses GitHub issues + a markdown backlog, not Linear. Revisit only if the backlog migrates to Linear.
- **`orca computer` / `orca tab` (browser)** — GUI/accessibility + browser automation. Could drive the **NotebookLM web UI** as a fallback when the `nlm` CLI fails (HemaSuite's NLM hard dependency). Speculative; the CLI path is primary.
- **`orca status [--json]`** — app/runtime/graph readiness probe. Minor; HemaSuite already has `hpw doctor`, h-mad has `hmad-dispatch env`.

---

## Cross-cutting notes
- Every Orca-touching change should reconcile against `orca agent-context --json` (schema-versioned, self-describing) at build time — the original wrapper's guessed syntax is what Tier 1 had to fix.
- The reliable Orca identity path is an explicit **handle pin** (`HMAD_ORCA_*_TERMINAL`, `HMAD_ORCA_COORDINATOR_TERMINAL`) — no `terminal list` field names the running program.
- All Orca features here are unit-tested against `orca` stubs; a **live-Orca session with Orca-hosted agents** is the standing validation gap across Tier 1/2/3.
