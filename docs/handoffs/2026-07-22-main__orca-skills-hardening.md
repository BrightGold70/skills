# Handoff — Orca-native hardening of h-mad + handoff skills

**Date:** 2026-07-22
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (BrightGold70/skills)

## Session Summary

Reviewed Orca's repo and upgraded the `h-mad` + `handoff` skills to exploit Orca's git-native functions, then hardened everything through repeated audit→fix→review cycles. **Done and shipped to `main` (all pushed):** the original `orca-git-native-checkpoints-and-merge-gate` feature via a full 7-phase `/h-mad` (feature/185), then five follow-on fix passes — F1–F14 (monitoring bugs), G1–G6 (handoff/merge-gate Orca wiring), report-file transport (188), handoff repo-canonical scoping (189), and a live end-to-end verification sweep. Every batch was independently subagent-reviewed and each review caught exactly one real bug pre-merge. Final state: `docs/skill-monitoring.md` has zero open items, suite 383/0, and the entire Orca surface is live-verified against the real runtime.

## Key Learnings

- **Screen-scraping a TUI is the root fragility** — F1–F6 (gate false-pass on indent/`•`, `tui-idle` fooled by spinner, sentinel fragmentation, no safe nudge) were all one problem. The fix that dissolves the class is **report-file transport**: the agent writes its report to `<path>` + a `<path>.done` marker, coordinator polls the marker and reads the file. Live-proven with both agy and Codex; gate scores the clean file directly (no extract/dedent/normalize).
- **agy (Antigravity/Gemini) TUI quirks**: NEVER nudge with a bare Enter — it submits a blank turn and starts junk generation. `Ctrl-C` (`$'\x03'`) exits the REPL and **freezes scrollback** → the reliable capture. agy can self-upgrade via Homebrew mid-run (1.1.1→1.1.5), resetting trust/auth.
- **The separate-review-lane discipline is load-bearing** — 4 independent subagent reviews caught 4 real bugs that green unit tests missed: F-batch stub-envelope regression (suite was actually 346/9 not 355/0), G-batch `gate-wait` fail-**open**, 189 `find_latest` prefix-sibling false-match (`feat` loaded `feat-ab`). Reviews ran as Claude subagents (not agy) specifically to avoid the fragile substrate.
- **Fail closed on gates**: `gate-wait` must resolve only on `.resolution` present OR `.status=="resolved"` (not `!= "pending"`); audit-gate must treat a header-less/empty extract as INVALID, not PASS. A false FAIL blocks a merge (human looks); a false PASS ships a defect.
- **Orca specifics discovered live**: coordinator auto-detects from `ORCA_PANE_KEY` (`<tabId>:<leafId>`) → match `terminal list` `.leafId`. `worktree-current` payload is `{"worktree":{…}}` with a **full-ref** branch (`refs/heads/main`) — the handoff reconcile must read `.worktree.branch` and strip `refs/heads/`. Real gate shape = `{status:pending→resolved, resolution:null→value}`.
- **Handoff/learnings scoping under Orca multi-worktree**: anchor to the canonical **main worktree** via `git rev-parse --git-common-dir` (not `--show-toplevel`, which fragments per-worktree and loses data on worktree removal). Disambiguate within the store by branch, with `__` as the branch|slug separator (branch slugs drop `_`, so `feat` can't match `feat-ab`). Per-repo store + per-worktree/branch identity — NOT per-session, NOT global.
- **Recurring tracer-bullet lesson (again)**: G1/G2 shipped as real bugs because the handoff Orca reconcile was mock-tested + doc-reviewed but never run against the live payload. Probing the live `orca` CLI first (G4/G5) avoided the same trap.

## Next Steps

Session arc is complete — nothing is pending or blocked. Optional follow-ons if the work resumes:

1. `[suggested]` Drive a full `/h-mad` run whose Phase-3/4/5b audits use the **report-file** path by default (mechanism proven end-to-end, but the one full `/h-mad` this session predated 188 and used scrape) — exercise via `/h-mad "<tiny-feature>"`.
2. `[suggested]` Consider giving the pre-existing raw-JSON verbs (`dispatch`, `gate-resolve`, `await`) the same `_orca_json` `.ok`-guard if a future error-envelope bites — currently only the extract verbs are guarded (F11 scope).
3. `[suggested]` `automation-*` verbs are live-verified but unused in any skill flow — wire a scheduled live-e2e automation if that workflow is wanted (`hmad-dispatch automation-create …`).

## Open / Blocked Items

- None. All monitoring items (F1–F14, G1–G6, A1–A2, V1) are FIXED/verified; registry is clean. No blockers.

## Context for Next Session

**Files touched this session (high-level — see git log b877439..d656c11):**
- `h-mad/scripts/hmad-dispatch.sh` — new verbs: `worktree-comment`, `worktree-current`, `gate-wait`, `report-wait`, `interrupt`; `_orca_json` guard; coordinator auto-detect; substrate default→orca
- `h-mad/scripts/h_mad_audit_gate.py`, `h_mad_state_schema.json`, `h_mad_state_validate.py` — F1/F2/F12/F14 fixes
- `h-mad/SKILL.md`, `h-mad/references/orchestration-mode.md`, `agent-substrate.md`, `audit-prompt.template.md`, `codex-implementer-prompt.md` — merge gate, report-file transport, agy-capture docs
- `handoff/SKILL.md`, `handoff/scripts/handoff_paths.py` (new), `handoff/scripts/learn.py` — Orca checkpoints, canonical/branch-scoped store
- `h-mad/tests/*`, `handoff/scripts/test_handoff_paths.py` — 383 tests
- `docs/skill-monitoring.md` — standing registry (F1–F14, G1–G6, A1–A2, V1, all resolved)

**Worktree:** main worktree (not a linked worktree) — canonical store is this repo's `docs/`.

**Uncommitted changes:** none (clean tree, in sync with origin/main).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
export PATH="/opt/anaconda3/bin:$PATH"    # python3 with jsonschema+pytest (F8: brew python3.14 lacks jsonschema)
python3 -m pytest handoff/scripts/test_handoff_paths.py h-mad/tests/ -q   # expect 383 passed
# For live Orca work: source the pinned env (HMAD_ORCA_*_TERMINAL) or rely on auto-detect
```

**Related docs:**
- `docs/skill-monitoring.md` — the standing bug/improvement registry (all resolved)
- `docs/archive/2026-07/orca-git-native-checkpoints-and-merge-gate/` — the /h-mad closure docs (spec/plan/design/audits/report)
- Memory: `~/.claude/projects/-Users-kimhawk-orca-skills/memory/project_orca_git_native_checkpoints_merge_gate.md`
