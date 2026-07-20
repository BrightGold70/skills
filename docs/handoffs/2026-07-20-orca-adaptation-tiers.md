# Handoff — Orca adaptation into h-mad + HemaSuite (substrate → Tier 1 → Tier 2 → backlog)

**Date:** 2026-07-20
**Branch:** main (both `Coding/skills` and `Coding/HemaSuite`)
**Project:** BrightGold70/skills (h-mad skill) — with one HemaSuite feature

## Session Summary
Adapted Orca (`stablyai/orca`) into the **h-mad skill** and **HemaSuite**, shipping **four features** — each through the full 7-phase H-MAD workflow (later three fully autonomous per operator directive). All merged + pushed; nothing in flight. The h-mad `hmad-dispatch` wrapper became substrate-agnostic (cmux **or** orca) and then drove the correction/extension of its own Orca layer. A Tier-3 + medium backlog was saved for the operator to implement next.

## Key Learnings
- **The original Orca wrapper verbs were guessed, not schema-checked.** Tier 1 reconciled them against `orca agent-context --json` (schema v1, self-describing, 202 cmds): `wait` needed `--for tui-idle --timeout-ms` (was a broken `tui-idle` positional), `read` has native `--limit` (was `| tail`). **Reconcile any Orca-touching change vs `agent-context` at BUILD time.**
- **`orca terminal list --json` nests under `.result.terminals[]` keyed by `.handle`** — NOT a top-level array / `.id`. The wrapper's guessed `.[] | select(.id==…)` never matched live Orca (liveness + `_orca_find` both broken). No field names the running program → the reliable identity is an explicit **handle pin**, not command-substring match.
- **cmux `alive` string-match gives false positives.** `hmad-dispatch alive` grepped the surface id in `cmux tree`; surface:2/:5 existed but weren't the agent panes. Real layout this session: **Codex = surface:4, agy = surface:5** (default surface:5/:2 convention is STALE — pin via `HMAD_CMUX_CODEX_SURFACE`/`HMAD_CMUX_AGY_SURFACE`). Always `read` a pane to confirm the REPL before dispatching.
- **zsh doesn't word-split unquoted vars** → `env $PINS bash …` failed; use prefix-assignment `VAR=v VAR2=v bash …`. Also: shell env exports do NOT persist across Bash tool calls — inline the pins every call.
- **agy verdict-polling is scrape-fragile**: grep matched the prompt-echo AND stale scrollback (warm agy pane keeps prior verdicts). Poll on the idle marker (`? for shortcuts` present AND `esc to cancel` absent) + a schema token, not just a keyword.
- **Tier 2 worker can't read the coordinator handle from its own shell env** — inject it into the task spec (`task-create` prepends a `[H-MAD] worker_done coordinator handle` line and enforces the pin). agy design-audit caught this + the best-effort-vs-enforced edge before code.
- **`test_real_features_synced` (literal `.audit.vN.md` refs) lives only in HemaSuite hpw tests, NOT the skills h-mad tests** — the skills-repo H-MAD cycles didn't hit that gotcha (83/73-pass suites confirm).

## Next Steps
1. Implement **Tier-3 · worktree parallel multi-module TDD** (h-mad) — `orca worktree create/ps/rm` → isolated worktree per impl-plan module → parallel Codex dispatch + Tier-2 `await` merge. Full scope: `Coding/skills/docs/orca-adaptation-candidates.md` §Tier 3.
2. Implement **Medium M1** — `orca file diff`/`open-changed` to surface Phase-5 diffs / manuscript DOCX at review gates — `Coding/skills/docs/orca-adaptation-candidates.md` §M1.
3. Implement **Medium M2** — HemaSuite `orca automations` to schedule long live-e2e/regression runs — same doc §M2.
4. [suggested] Live-Orca e2e once Orca-hosted Codex/agy agents exist — validate Tier-1/2 (`dispatch → worker_done → await → gate`) end-to-end; all Orca features are stub-tested only.

## Open / Blocked Items
- **Live-Orca e2e** — status: blocked on an Orca-hosted-agent environment (this session ran agents on cmux). Every Orca feature (Tier 1/2, orca-launch-profile) is unit-tested against `orca` stubs; not one has been exercised against a real Orca runtime.
- **HemaSuite launch-path carries** (from the session-start `/handoff read`, never acted — session pivoted to Orca) — status: deferred. (a) Re-run anemia-jmj live e2e to confirm A-P0-1/A-P1-3 fix; (b) review-pipeline-correctness feature (A-P1-1/2/4); (c) #37 dose-token topic-hygiene follow-on. See `HemaSuite/hematology-paper-writer/docs/handoffs/2026-07-20-launch-path-canonical-resolution.md`.
- **MEMORY.md ~20KB** (limit 24.4KB) — status: not urgent; compaction pass advised soon (one line per entry; detail already in topic files).
- **HemaSuite skill-design branch** deleted this session; `h_mad_derive_test_path.sh` remains a pre-existing uncommitted dirty file in the skills repo (NOT ours — leave it).

## Context for Next Session

**Files touched this session (all merged+pushed):**
- Skills (BrightGold70/skills main): `h-mad/scripts/hmad-dispatch.sh` (substrate + Tier1 + Tier2 verbs), `h-mad/tests/test_hmad_dispatch.py`, `h-mad/references/{agent-substrate,codex-implementer-prompt,agy-spec-reviewer-prompt,orchestration-mode}.md`, `h-mad/SKILL.md`, `docs/orca-adaptation-candidates.md`, full H-MAD doc trails under `docs/0{1,2,3,4}-*/`.
- HemaSuite (BrightGold70/HemaSuite main): `hematology-paper-writer/{launch_hemasuite.sh,tools/launcher_helpers.py,notify_shim.sh,test_notify.sh}`, `HemaSuite_Project_Document.md §37`, `docs/superpowers/{specs,plans}/2026-07-20-h-mad-orca-substrate-support-*`.

**Shipped commits:**
- skills: substrate `d6af804c`-era → Tier-1 merge `a2cdfe2` → Tier-2 merge `f1bcf97` → backlog `e26199e`.
- HemaSuite: orca-launch-profile `89087615`.

**Uncommitted changes:** skills — only the pre-existing `h_mad_derive_test_path.sh` (not ours). HemaSuite — operational cruft only (telemetry.jsonl, *.bak, orca_vs_cmux_comparison.md).

**To resume:**
```bash
cd /Users/kimhawk/Coding/skills           # h-mad skill lives here (symlinked to ~/.claude/skills/h-mad)
git checkout main && git pull --ff-only
# Tier-3 / medium implementation → read the backlog first:
#   docs/orca-adaptation-candidates.md
# H-MAD dispatch needs cmux panes: Codex=surface:4, agy=surface:5 (pin via HMAD_CMUX_{CODEX,AGY}_SURFACE)
```

**Related docs:**
- `Coding/skills/docs/orca-adaptation-candidates.md` — the Tier-3 + medium + low backlog (primary next-session input).
- Auto-memory: `project_orca_adaptation_backlog.md` (+ MEMORY.md pointer).
- `Coding/HemaSuite/docs/orca_vs_cmux_comparison.md` — the source comparison that seeded the whole arc.
