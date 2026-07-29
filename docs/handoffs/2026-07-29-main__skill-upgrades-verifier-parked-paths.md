# Handoff — h-mad 5e verifier + handoff parked-path skill upgrades

**Date:** 2026-07-29
**Branch:** main
**Project:** orca/skills (h-mad + handoff skills)

## Session Summary

Continuation of the same day's dispatch-transport work (prior doc: `2026-07-29-main__dispatch-transport-validation.md`). Finished #7's pane-path validation, then evaluated the drained skill-candidate backlog and shipped the only two actionable upgrades — both TDD'd, mutation-verified, and pushed. **B (`5f9ae60`)**: the handoff skill now requires parked feature-work to record `repo · branch · worktree` + artifact paths, with a READ-mode recovery bullet for older location-less handoffs. **A (`ad04a60`)**: a bundled Phase-5e anti-gaming verifier prompt (`h-mad/references/codex-verifier-prompt.md`) wired into SKILL.md 5e with a `step5e:verify_failed` halt. All green: h-mad 744/0, HemaSuite coupled 54/0. Backlog drained again.

## Key Learnings

- **The 5e anti-gaming verify had no bundled template.** `references/` shipped an implementer prompt and a spec-reviewer prompt, but the independent "are the tests real / does the source hold the pinned properties" pass lived only in an ad-hoc scratchpad prompt (`codex_task3_verify.txt`). SKILL.md L334 asserted the pass was needed without codifying it. That gap is what A closed.
- **`set -e` + a mutation loop is a footgun when `python3` resolves inconsistently.** A mutation test run picked `/opt/homebrew/opt/python@3.14` (no pytest) instead of `/opt/anaconda3/bin/python3` (pytest 8.3.5) — the mutations applied but tests never executed, giving zero RED evidence. Pin the interpreter explicitly (`PY=/opt/anaconda3/bin/python3`) for h-mad doc-tests; do not trust bare `python3` here.
- **h-mad skill edits must clear BOTH suites.** The skill is symlinked as `~/.claude/skills/h-mad`; HemaSuite's `test_h_mad_*` + `test_audit_phase_frontmatter` hit it by path. Ran them (54/0) after the SKILL.md edit — a skill change is not "done" on the skills suite alone.
- **The verifier's own crosscheck codifies this session's live finding.** Its "do not trust your own headline numbers" section exists because a real `codex exec` emitted `STATUS: DONE` over a fabricated count (21 vs 28). Exit 0 + a STATUS line is never proof of correct work.

## Next Steps

1. **Dogfood the new 5e verifier on a live feature run** — the LANDED discipline's last step, not yet done. On the next real 5d/5e, stage `references/codex-verifier-prompt.md` with the `<INLINE_*>` slots filled and dispatch it (`hmad-dispatch exec`), confirm the `step5e:verify_failed` halt path fires on a seeded false property. — `h-mad/SKILL.md` §Phase 5e.
2. **Exercise the `wait --not-while-regex 'Waiting for background terminal'` false-idle guard live** — still only unit-tested (`test_hmad_dispatch.py`); needs a real pane dispatch that delegates to a background terminal. — `h-mad/SKILL.md` §"Reading a dispatch verdict".
3. [suggested] Promote `orca terminal read` JSON shape into the h-mad dispatch docs — the `.result.terminal.tail[]` path (not `.rows[]`) cost a wrong-jq round-trip this session; a one-line note in the pane-read section would prevent it.

## Open / Blocked Items

- 5e verifier template — status: shipped but not yet dogfooded on a live run (deferred to next real feature; see Next Step 1). Not blocking — doc-test-covered and mutation-verified.
- `wait` false-idle guard — status: deferred, not live-validated (see Next Step 2).

## In-Flight Processes

None — no long-running work alive at handoff (the day's pytest runs and read-only `exec` smokes all completed).

## Context for Next Session

**Files touched this session (all committed + pushed):**
- `handoff/SKILL.md` — parked-path requirement + READ recovery bullet (`5f9ae60`)
- `h-mad/references/codex-verifier-prompt.md` — new 5e verifier template (`ad04a60`)
- `h-mad/SKILL.md` — 5e wiring + `step5e:verify_failed` halt (`ad04a60`)
- `h-mad/tests/test_h_mad_verifier_prompt.py` — doc-test (existence + literals + wiring), mutation-verified (`ad04a60`)
- `docs/skill-candidates.md` — 3 rows reconciled to LANDED (`ad04a60`)
- `docs/learnings.md` — +4 entries across the day (`82438ca`, and the handoff-write step below)

**Uncommitted changes:** none (local `main` = `origin/main` `ad04a60`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
# run h-mad doc-tests with the pytest interpreter:
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q
```

**Related docs:**
- `h-mad/references/codex-verifier-prompt.md` (new) + `h-mad/SKILL.md` §Phase 5e
- Prior handoff (same day): `docs/handoffs/2026-07-29-main__dispatch-transport-validation.md`
- `docs/skill-candidates.md` — backlog now fully drained
