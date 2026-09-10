# Handoff — h-mad gates shipped, and 6a-prime finally gets a report-file channel

**Date:** 2026-09-10
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-07-main__hmad-fold-and-takeover-mode.md, 2026-09-08-main__author-done-line-protocol.md, 2026-09-09-main__hmad-version-history-and-pindrift.md, 2026-09-09-feature-archreview-verdict-exemplar__6a-prime-report-file-channel.md

## Session Summary

Nine items shipped to `main` and pushed (`cf39879..e30e54f`), suite **3178 passed / 2 skipped**:
orchestrator rules 7+8 (#25), the `--gated`/`--legs` defaults and the `STAMP:` token (#18, #26),
codex transcript measurement (#27), the coupling-set re-derivation (#28), and two inbound handovers
taken over and completed — version-history series-break + PINDRIFT `--allow-historical` (#29, #30),
then the 6a-prime report-file channel (#31, #32, #33). Every guard is mutation-covered with
per-mutation `test` keys. **The one item still owed is #34**, deferred by its sender and not started.

## Key Learnings

- **An ordinary edit silently invalidates COMMITTED mutation specs — five times in one session.**
  One variable rename (`args.gated` -> `gated`), one comment rewrite, one re-indent. They live in
  **two** directories that both exist — `h-mad/tests/mutation-specs/` and `h-mad/tests/specs/` — and
  every one was caught by a SWEEP, never by the targeted run immediately before it. The harness
  refusing to measure when a sibling precheck fails (`PRECHECK_FAILED … nothing was measured`) is
  what stopped a hollow `ALL_CAUGHT` shipping each time.
- **A prompt instruction at 99.6% of a 690 KB prompt is not an instruction.** The 6a-prime template's
  own text is ~7 KB; the substituted design and 62-path file list are the other 680 KB, so every
  instruction it carries — the verdict line included — sat in the last 0.4%. Two live dispatches
  wrote no report file. What refuted my first hypothesis was a NEGATIVE: the transcript never
  mentioned the report path at all. An agent that reads an instruction and declines leaves a trace;
  one that never reaches it leaves none.
- **`_PLACEHOLDER` matches `<INLINE_[A-Z_0-9]+>` only.** A slot named outside that grammar (the brief
  proposed `<REPORT_FILE_PATH>`) inherits NEITHER the `UNSUBSTITUTED` nor the `MISSING_SLOTS` guard,
  so a substitution miss ships a live placeholder that reads as real prose to the reviewer.
- **A guard killed by the WRONG assertion is not killed.** My rule-8 mutation survived twice: first
  because `"re-read" in section.lower()` matched the *cited evidence* rather than the prescription,
  then because a PREFIX section anchor left a dangling `**` that shifted every bold-span pairing by
  one and swallowed the quote into span 1.
- **`cp <src> <dst> 2>/dev/null` turned a failed copy into what looked like a state-write defect** —
  `NOT_RECORDED … read back None`. The repo-root `HemaSuite/docs/.bkit-memory.json` does not exist;
  the gateway record is in `hematology-paper-writer/docs/`. Never suppress cp/find stderr.
- **A self-matching grep count is not evidence.** `ps -eo command | grep -cF lanes_watch.sh` said 3
  while the filtered listing said none; the count was matching its own command line. `pgrep` settled it.

## Next Steps

1. **#34 — codex templates: get EVIDENCE first, do not edit.** `references/codex-implementer-prompt.md`
   and `references/codex-verifier-prompt.md` carry the same fenced-schema exemplar shape that broke
   agy's archreview. The sender deferred deliberately: codex emits `STATUS:` reliably in this repo's
   record, and rewriting a working prompt on a shape argument is the documented failure mode.
   **The question has changed since that deferral** — my #31 root cause was POSITION, not form. So the
   probe to run is whether the codex path already head-prepends its contract:
   `grep -n 'prepend_output_contract' h-mad/scripts/h_mad_assemble_audit.py` and check whether the
   codex templates are staged through it. If they are, codex's reliability has a MECHANISM and #34
   closes as correctly-deferred-with-a-reason rather than as a pending edit.
2. **#2 — use Phase 7f on the next feature closure owned HERE.** `h_mad_phase7_integrate.py` exists,
   is documented, and has still never run on a real closure. HemaSuite closed `#18` on 2026-09-10 but
   that is their lane, not ours, so it did not discharge this.
3. **Run this repo's automation scout** — `docs/skill-candidates.md` has not been reconciled here.
   HemaSuite ran theirs (31 open rows, `0662a480`); ours is a different store and is still owed.

## Open / Blocked Items

- **#34 codex fenced-schema templates — status: DEFERRED by the sender, not started.**
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`. Inherited via
  **Handover-From:** HemaSuite · feature/18-gateway-consolidation · session `3954e098`.
  Files: `h-mad/references/codex-{implementer,verifier}-prompt.md`. Do not touch without evidence of
  a codex failure to emit its token — agy's behaviour is not evidence about codex's.
- **#2 Phase 7f on the next feature closure — status: OPEN, unchanged since 2026-09-07.**
  Conditional, not blocked: it fires when a closure this repo owns happens.
- **This repo's automation scout — status: OWED, never run this session.**
- **No fresh-context review lane ran on ANY of today's nine commits — status: OPEN.** CLAUDE.md asks
  for a separate approval pass (`code-reviewer`/`verifier`); agent dispatch was not requested, so I
  self-gated with mutation batteries plus the full suite throughout. That gap is real and unclosed.
- **88 untracked `.done` audit markers + `lanestate/` — status: unchanged, deliberate.** `bdf43ed`
  untracked 33 of them; `.gitignore` still has no `done` rule, so they re-accumulate every audit cycle.
- Carried from `2026-09-07-main__hmad-fold-and-takeover-mode.md` and CLOSED in that chain before this
  session: H7 origin tagging, the two-round cap terms, the second surface-disagreement mechanism, the
  two H8 extensions + probe hygiene, the code-phase ledger, #112's reviewer half, the #30/#32/#49w
  opaque labels, and the skill-candidates census. Each is `completed` in this session's task list;
  none was re-opened here.

## Context for Next Session

**Files touched this session:**
- `h-mad/SKILL.md` · `h-mad/references/measurement-discipline.md`
- `h-mad/references/agy-architectural-reviewer-prompt.md`
- `h-mad/scripts/h_mad_audit_cycle.py` · `h_mad_audit_gate.py` (via cycle) · `hmad-dispatch.sh`
- `h-mad/scripts/h_mad_review_evidence.py` · `h_mad_version_history.py` · `h_mad_precheck_doc.py`
- `h-mad/scripts/h_mad_archreview_cycle.py`
- `h-mad/tests/` — 6 test files, 7 new/updated mutation specs, 2 real codex fixtures

**Uncommitted changes:** none tracked. 88 untracked `.done` markers + `lanestate/` (not mine).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                      # expect e30e54f or later, in sync
cd h-mad && python3.11 -m pytest tests/ -q   # expect 3178 passed, 2 skipped
# python3 here is 3.14 with NO pytest — use python3.11
```

**Related docs:**
- `h-mad/SKILL.md` §"Author dispatch rules the ORCHESTRATOR owns" — rules 7 and 8 landed here
- `h-mad/tests/mutation-specs/` and `h-mad/tests/specs/` — BOTH are live spec stores
- HemaSuite `docs/03-analysis/gateway-consolidation.archreview.gate-surface-override.md` — their
  one-off codex surface override, decided before the verdict was known
