# Handoff — backlog drain, then pin-agents-tail-banner through Phase 4

**Date:** 2026-09-01
**Branch:** `main`
**Project:** `/Users/kimhawk/orca/skills`

## Session Summary

Resumed from `wire-pin-gate-and-skill-upgrades`, then shipped six commits of backlog work
and took feature #6 (`pin-agents-tail-banner`) through H-MAD Phases 1–4. **Phase 4 is gated
(`AUDITCYCLE: PASS must=0 should=0`, cycle 9) and Phase 5 has not started — that is the
resume point.** No code has been written for the feature; the design is complete and audited.
Everything else this session is shipped and pushed; `main` is clean at `490dab6`.

The session stopped at the Phase 4/5 boundary deliberately, on the operator's call, because
the run-context projection put Phase 5 or 6 past the 80% ceiling — and "audited design, no
code" is the cleanest resumable state this feature can be left in.

## Key Learnings

- **Three idioms in the tail-evidence pass silently defeat their own guard, and the broken
  form is the one that looks better.** `if _orca_tail_sig "$h"` reads as a condition check and
  streams the pane's scrollback into `_orca_find`'s stdout, corrupting the handle;
  `jq -r '.result.terminal.tail'` prints literal `null` and exits **0** for an absent key, so
  an unreadable pane scores as a non-match; `if local out="$(…)"` returns `local`'s status
  (always 0) and discards the helper's rc. All three are pinned by measurement in the design
  rather than by description, because none is visible as wrong in review.
- **Orca tail retention is hard-capped at 2000 lines** regardless of `--limit`. Measured: a
  200-line pane kept its first line, a 2000-line pane lost it, a 20000-line pane began at
  18001. Agent panes survive this only because they are full-screen TUIs on the alternate
  screen — their output never enters normal-buffer scrollback, which is why a codex pane
  dispatched to for two days still holds 18 lines.
- **`.result.terminal` carries `truncated`, `limited`, `oldestCursor`, `returnedLineCount`.**
  `truncated` would distinguish "no signature" from "signature scrolled past the cap" — the
  load-bearing unknown in the design's Risks table. Out of scope for this feature, worth
  knowing.
- **Twelve of the fourteen audit passes were `low-evidence` (tools ≤ 2).** They found real
  defects, but every one was doc-internal: contradictions, stale counts, invariant
  violations. Each finding that required knowing what the *code* does came from reading it
  directly or from one targeted source-verification dispatch. Agreement between passes was a
  poor stopping signal throughout — they alternated which one bit.
- **The spec was the trailing document all feature long.** Three back-propagations (rc-1
  semantics, the portable time bounder, AC-3.2's pool), all the same shape: the audit compared
  design against spec, the design was right, the spec's wording predated it.
- **Two plan→design drops, same direction.** `--cursor 0` and the three verification
  requirements were both fixed in the plan and never carried across. The paired design is the
  surface the five-surface value sweep misses on.
- **A finding's premise can fail while the finding stands.** "Every ambiguous case resolves
  toward the first" meant the first *failure direction*; an audit read it as the first
  *candidate*. The intent was misread and the sentence still had to change — it admitted a
  reading that licensed the exact defect the feature prevents.
- **`git worktree list` is not the only thing that moves.** 110 tests in `handoff/scripts/`
  were never collected by the habitual `pytest h-mad/tests handoff/tests`, and one had been
  RED since 2026-08-31 while four commits reported a green suite.

## Next Steps

1. **Start Phase 5a** for `pin-agents-tail-banner` — generate the impl-plan per
   `h-mad/references/inline-protocols.md §Phase 5`, output to
   `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md`. The design's Implementation
   Order (7 steps) is the input; step 1 is `_orca_tail_sig` + unit tests alone.
2. **Phase 5b** — audit the impl-plan, then run the wire-pin gate:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/pin-agents-tail-banner.impl-plan.md --feature pin-agents-tail-banner`
3. **Phase 5c** — `git checkout -b feature/pin-agents-tail-banner`, commit impl-plan + audits.
4. **Phase 5d/5e** — codex TDD. Stage with `h_mad_assemble_tdd.py --phase red|green`; the
   task shape is `wiring`-adjacent but is NOT a wiring task (no call-site to pin), so state
   expected failing/passing counts. **The test-harness change comes first**: the existing stub
   answers one `HMAD_STUB_ORCA_STDOUT` payload and this pass needs `terminal list` AND
   `terminal read` to differ — see design §Test Strategy.
5. **Re-check AC-1.1 against current behaviour before counting it as coverage** — `cn == 1`
   with `lsof` present already resolves today via the OS-evidence pass, so a careless test
   passes with the whole feature reverted. Design §Test Plan flags test 7 as the vacuous risk.
6. [suggested] Task #8 (`warn before merging a shared skill change while a lane is mid-cycle`)
   and #11 (`frozen-tree guard`) remain in the triaged backlog, both assessed as needing full
   h-mad rather than a direct fix.

## Open / Blocked Items

- **`pin-agents-tail-banner` Phase 5 — status: not started, feature CLAIMED by this session.**
  The claim is released at closeout (see below), so the next session claims it fresh via the
  normal `start_fresh`/`resume_manual` route. State says `last_completed_phase=4`,
  `current_phase=5`.
  - `repo: /Users/kimhawk/orca/skills · branch: main (no feature branch yet — 5c creates it) · worktree: none`
  - Artifacts: `docs/01-plan/features/pin-agents-tail-banner{-brainstorm,.spec,.plan}.md`,
    `docs/02-design/features/pin-agents-tail-banner.design.md`, audit reports
    `*.plan.audit.v1–v6.p{1,2}.md` and `*.design.audit.v1–v9.p{1,2}.md`
  - Scratchpad: `<scratchpad>/pin_plan_selffindings.md` — the four corrections found by
    reading `_orca_find`, kept because two were not reproduced in any audit report.
- **An untracked handoff doc from a different session is sitting in the store** —
  `docs/handoffs/2026-09-01-main__handoff-restore-chain-and-audit-version-discovery.md`.
  Status: deliberately NOT staged by this closeout. It is not this session's work and I have
  not read it, so committing it would be distributing a document I have not seen. It is
  nonetheless exactly the orphan case the skill documents (`git log --all -- <path>` shows
  zero commits), so whoever wrote it should commit it or delete it.
- **Retention risk on the tail pass — status: accepted and documented, not resolved.** A pane
  where the agent exited and the operator ran >2000 lines of shell loses its signature and the
  pass declines to UNRESOLVED. Design Risks table, row 1.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` (pin-agents carry fix), `h-mad/scripts/h_mad_resolved_model.py`,
  `h-mad/scripts/h_mad_response_probe.py`
- `handoff/scripts/handover_landed.py`, `handoff/SKILL.md` (Step 3.6 refusal record, Step 7)
- `h-mad/tests/docsections.py`, `h-mad/tests/test_suite_collection.py`, `pytest.ini`
- `docs/skill-candidates.md` (20-row triage), `docs/01-plan/features/pin-agents-tail-banner*`,
  `docs/02-design/features/pin-agents-tail-banner*`

**Uncommitted changes:** none of this session's work. One foreign untracked handoff doc (above).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/h-mad "pin-agents-tail-banner"          # routes on state: last_completed_phase=4 -> Phase 5
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py --mode run   # check the ceiling FIRST
pytest -q                                 # 2538 expected; testpaths now covers handoff/scripts
```

**Related docs:**
- `docs/02-design/features/pin-agents-tail-banner.design.md` — v1.7, the implementation contract
- `docs/01-plan/features/pin-agents-tail-banner.plan.md` — v1.5
- `docs/01-plan/features/pin-agents-tail-banner.spec.md` — v1.4, 13 ACs
- `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps" · §"Run-context ceiling"
