# Handoff — h-mad audit dispatch must persist the report into docs, not only /tmp

**Date:** 2026-09-02
**Branch:** `main` (work branch `BrightGold70/audit-report-docs-copy` in worktree `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy`, off `main`; the main checkout `/Users/kimhawk/orca/skills` sits on `feature/pin-agents-tail-banner` with a LIVE h-mad run — do not edit that tree)
**Project:** skills (`github.com/BrightGold70/skills`, h-mad skill)
**Handover-From:** HemaSuite · main · session f15c716a-0b1b-43cc-8dc0-d67f5670a59e
**Taken-Over-By:** skills · BrightGold70/audit-report-docs-copy · session session_01K1d48W2pVLpA3yJ8V6LjrB · 2026-09-02
**Supersedes:** none — first on this branch

## Session Summary

Handover of one defect found while closing HemaSuite backlog task #32/#33 on 2026-09-02. Under
Orca's report-file transport, an h-mad audit pass writes its report to
`/tmp/audit_<feature>_<phase>_cycle<N>[_<surface>].report.md` (SKILL.md step 6.6, ~line 1687)
and step 9 reads that file directly. The copy into the feature's docs store —
`docs/<01-plan|02-design>/features/<feature>.<phase>.audit.v<N>.<surface>.md` — is a **separate
manual `cp`** that the recipe never performs. On `nlm-cli-version-pin` the copy was skipped for
plan cycles 8 and 10–15: seven codex reports were cited by the plan's Version History and absent
from docs and from `git log --all`, and the consumer-side sync guard scored cycles 10/12/14 PASS on
the surviving agy leg. All seven were recovered from `/tmp` (HemaSuite `9e855dfa`) — `/tmp` is
wiped on reboot, so the recovery window was luck. The consumer-side guard is fixed (HemaSuite
`d1e73d53`); the **recipe half** is this handover. Outcome: not started here.

## Key Learnings

- The report-file transport is the only step that knows both the `/tmp` path and the `(feature,
  phase, cycle, surface)` tuple, so it is the only place the docs copy can be made without a human
  remembering. Eight consecutive cycles forgot.
- A `.done` marker beside the `/tmp` report proves the *agent* finished; nothing proves the
  *orchestrator* persisted. `h_mad_extract_report.py` exiting 0 on the `/tmp` file is exactly the
  green that hid this.
- `git log --all` empty is evidence of *not committed*, never of *never written* — look in `/tmp`
  before concluding a report is lost (HemaSuite memory
  `feedback_audit_reports_must_be_persisted_before_acting.md`, corrected 2026-09-02).

## Next Steps

1. Reproduce the gap on the live corpus — from `/Users/kimhawk/orca/HemaSuite`:
   `ls /tmp/audit_nlmpin_plan_cycle*_codex.report.md | wc -l` (31 at 2026-09-02) vs the docs
   copies `ls hematology-paper-writer/docs/01-plan/features/nlm-cli-version-pin.plan.audit.v*.codex.md | wc -l`;
   any cycle present in the first and absent from the second is the defect (all restored now — the
   count should match; the point is the mechanism, not the current state).
2. Read the recipe surfaces: `~/.claude/skills/h-mad/SKILL.md` step 6.6 (report-file staging,
   ~:1687) and step 9 (read-and-gate, ~:1734); `scripts/h_mad_report_wait.py`;
   `scripts/h_mad_extract_report.py`; `bin/hmad-dispatch exec … --report-file`.
3. Choose the fix and, if it is more than 1–2 files, run it through `/h-mad` (feature slug
   suggestion: `audit-report-docs-copy`). Candidates, receiver's call: (a) step 9 copies `$RP` to
   the docs path **before** the gate reads it and refuses to gate on a `/tmp`-only report; (b)
   `hmad-dispatch exec --report-file … --persist-to <docs path>` performs the copy on `.done`;
   (c) `h_mad_report_wait.py` returns only after the docs copy exists. Whichever is chosen, the
   docs path must be derived from `(feature, phase, cycle, surface)` — never typed by hand.
4. Pin it both directions: a run whose docs copy is missing must not gate (RED), and the copy must
   be byte-identical to `$RP` (measured: HemaSuite v16 `/tmp` == repo copy, `cmp -s`).
5. Consumer-side reference: HemaSuite `tests/test_audit_phase_inline_summary_sync.py::test_real_features_cite_only_audit_reports_that_exist`
   (`_absent_audit_citations`) — the guard that now goes red on a cited-but-absent report; the
   recipe fix makes that guard a backstop rather than the only line.

## Open / Blocked Items

- **Recipe half of HemaSuite task #33** — status: not started. `repo: /Users/kimhawk/orca/skills ·
  branch: BrightGold70/audit-report-docs-copy · worktree: /Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy`.
  Artifacts: this brief; HemaSuite commits `9e855dfa` (restore), `d1e73d53` (guard);
  `/tmp/audit_nlmpin_plan_cycle{8,10,11,12,13,14,15}_codex.report.md` (survivors, until reboot).
- **Do not touch `/Users/kimhawk/orca/skills` on `feature/pin-agents-tail-banner`** — live run
  (`5b NOT gated after 20 cycles`); edits in the checkout are live via the `~/.claude/skills/h-mad`
  symlink. Work in the new worktree only.

## Context for Next Session

**Files touched this session:** none in this repo (brief only).

**Uncommitted changes:** this brief is untracked in the canonical store — commit it first (READ
Step 3.6 allowlist).

**To resume:**
```bash
cd /Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy
python3 ~/.claude/skills/h-mad/scripts/h_mad_install_check.py   # INSTALL: PASS
grep -n 'report-file' ~/.claude/skills/h-mad/SKILL.md | head
```

**Related docs:**
- `~/.claude/skills/h-mad/references/orchestration-mode.md` §"Report-file transport"
- HemaSuite `docs/handoffs/2026-09-02-main__nlm-pin-phase3-gated-phase4-design-cycle2.md` (the
  session that found the seven absent reports)
