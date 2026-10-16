# Handoff — three h-mad fixes surfaced by HemaSuite #101 (notebooklm-integration-interface)

**Date:** 2026-10-16
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · main · session 0980df8b-6dd0-4651-a65d-1d72d50fea8b
**Supersedes:** none — first on this branch for this item

## Session Summary

HemaSuite's P06 #101 (`notebooklm-integration-interface`) ran Phases 5–7 and merged as `460c15968`. Three pieces of h-mad tooling forced hand-work during that run. The operator directed that they move to the skills repo, which owns h-mad. No skills code was changed. On 2026-10-16 I re-checked all three against `skills@main` (in sync with origin), and all three are still owed.

## Key Learnings

- The evidence lives in HemaSuite, in the #101 report §Carry Items and the 2026-10-16 handoff's Key Learnings. Those paths are read-only sources; the work is this repo's.
- Fix 3 is a rule-text gap rather than a code bug. The current wording in `codex-implementer-prompt.md:68` is right for a missing **callee**. It is wrong for a NEW **caller** whose callee already exists, and codex obeyed it literally and halted.

## Next Steps

1. **`h_mad_assemble_tdd.py`: carry referenced global impl-plan sections.**
   - Today it inlines only the `§Task N` section.
   - In #101, the impl-plan's global §"Hash re-pin" had to be spliced into each T3–T6 GREEN prompt by hand.
   - Fix: when a Task section references a global section (by heading or `§"…"`), inline that section too, or fail loudly if the reference doesn't resolve.
   - Re-check: `grep -n -i global h-mad/scripts/h_mad_assemble_tdd.py` returns 0 hits today.
2. **`h_mad_phase7_preconditions.py`: add `--docs-root`.**
   - The versioned-analysis and parked-spec checks anchor on the state file's `docs/` (`resolve_docs_root`, `parked_specs(docs_root, …)`, around lines 26, 79 and 99).
   - Before 7f the state file is main's, while the Phase-6 artifacts exist only in the feature worktree, so the CLI reports BLOCKED.
   - The workaround used in #101 was a Python call: `check(record, analysis, docs_root=<worktree>/docs)`.
   - Fix: expose that as `--docs-root`. The CLI args are around lines 318–331 and currently offer only `--analysis` and `--mutation-specs-dir`.
3. **Codex wiring rule: add a new-caller note.**
   - Location: `h-mad/references/codex-implementer-prompt.md:68`, and the RED clause at line 60.
   - Today an `ImportError`/`AttributeError`/`NameError` RED on a WIRE-PIN means "the pin tests the callee → report and stop".
   - That is also what fires when the task adds a NEW CALLER symbol and the callee already exists. In that case the RED is valid.
   - Fix: state that case explicitly. A missing caller is acceptable RED when the callee exists. The wire is then proven by a wire-cut mutation or a revert of the connection alone, as #101 did at M4.1, M5.1 and T6 WIRE 2.
   - The ruling had to go into both the RED and the GREEN prompts by hand.

## Open / Blocked Items

- **All three fixes above:** not started; owned by skills from this handover.
  - Evidence:
    - repo: `/Users/kimhawk/orca/HemaSuite` · branch: `main` · worktree: none
    - `docs/archive/2026-10/notebooklm-integration-interface/notebooklm-integration-interface.report.md` (§Carry Items, line ~30)
    - `docs/archive/2026-10/notebooklm-integration-interface/notebooklm-integration-interface.analysis.v1.md` (§Findings F-3, the new-caller WIRE-PIN RED)
    - `docs/handoffs/2026-10-16-main__notebooklm-feature-complete.md` (Key Learnings 1–3)
- **Nothing was claimed.** This was a todo on the HemaSuite session's list, never an h-mad feature, so no claim was released. On takeover, create a record under this brief's slug.

## Context for Next Session

**Files touched this session:** none in skills. This brief is the only artifact.

**Uncommitted changes:** none from this handover. The brief is committed locally in skills and not pushed.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff takeover    # claims hmad-notebooklm-carry-fixes and stamps this brief
```

**Related docs:**
- `h-mad/scripts/h_mad_assemble_tdd.py`
- `h-mad/scripts/h_mad_phase7_preconditions.py`
- `h-mad/references/codex-implementer-prompt.md`
- Reminder: `~/.claude/skills/h-mad` is a live symlink into this checkout, so edit in a worktree if any h-mad run is in flight.
