# Handoff — `exec agy` report loss: scoping the exec-missing-report recovery

**Date:** 2026-08-01
**Branch:** main
**Project:** /Users/kimhawk/orca/skills

## Session Summary

Investigated an `exec agy` audit dispatch that returned 358 bytes of narration and no report
(`grounding-shadow-measurement` design cycle 2). Root-caused it, then patched `h-mad/SKILL.md` and
`h-mad/references/failure-recovery.md` to scope the existing exec-missing-report recovery correctly:
it is **implementer-scoped** and does not apply to audit dispatches. Also compacted the auto-memory
index from 21.1 KB to 14.9 KB. Two of my own diagnostic claims turned out wrong mid-session and were
retracted in the shipped text — see Key Learnings. The doc edits are **written but uncommitted**.

## Key Learnings

- **`exec agy`: `--log` and `--out` are byte-identical.** `agy --print` emits one response and the
  wrapper writes it to both (verified by `diff` on both cycles — clean at 2.9 KB and at 358 B). The
  `SKILL.md` claim that `--log` "is the one channel observed to outlive the others" is **codex-only**,
  where the live transcript genuinely differs from `--output-last-message`. For agy, "read `--log`"
  is the same bytes twice — it is not recovery.
- **The exec-missing-report recovery is implementer-scoped.** Its three steps and its
  "do not re-dispatch" rule exist because a codex RED/GREEN leaves working-tree artifacts that a
  blind re-dispatch would clobber. An audit writes nothing to the tree: no delta for step 2 to
  enumerate, no code for step 3 to re-derive a verdict from. A short agy exec is therefore a plain
  `<phase>:no_verdict` halt whose documented route is the **opposite** — re-read, `clear agy`,
  re-dispatch (idempotent, safe).
- **F-10 lives in `~/orca/HemaSuite/AGENTS.md:820`-ish (line 320), not in the h-mad skill.** Grepping
  only `~/orca/skills` for it returns nothing, which reads as "no such ID" and is wrong. Capability-
  catalogue IDs live in the consuming project's `AGENTS.md`. I made exactly this error and asserted
  nonexistence off a single-repo grep.
- **Two mechanisms fit the 358 B evidence and this data cannot separate them:** either the report was
  emitted and a later summarizing turn became the last message, or it was never emitted and the agent
  narrated having done so (= F-10 claim-execution divergence). Cycle 1 succeeded on identical config,
  which is consistent with both. The remedy is the same either way, so discriminating is not worth a
  cycle — the docs now say so rather than picking one.
- **A multi-file `pytest` invocation can report `No tests collected` and exit 0 because ONE file
  errored at collection.** Running the same 9 files one at a time surfaced 58 passing tests plus a
  single `ModuleNotFoundError`. This is the known `-k`-selection hazard generalised: any collection
  error in a batch silently zeroes the whole run. Per-file loops are how you see it.
- **Falsify before acting — twice in one session.** I twice reported work as "owed" that had already
  been done correctly: the cycle-2 failure record already existed (written 3 min after the bad
  output, and it classified F-10, proved the channels identical, confirmed the narrated defects, and
  explicitly refused to claim a gate), and cycle 3 had already re-audited against design v1.2 and
  gated `PASS must=0 should=0`. Checking the artifact first would have caught both.

## Next Steps

1. Commit the two doc edits — `git add h-mad/SKILL.md h-mad/references/failure-recovery.md` then
   commit; they are the session's actual deliverable and are currently uncommitted.
2. Make the tooling do what the docs now say: pass `--report-file` on `exec agy` audit assembles.
   The flag already exists (`h-mad/scripts/h_mad_assemble_audit.py:186`, `default=""`), so today every
   exec audit takes the sentinel-scrape path and inherits the single-fragile-channel failure. Decide
   whether the default flips or the caller always passes it.
3. Fix the HPW venv gap so `test_launcher_project_phase_routing.py` can run — no venv exists under
   `~/orca/HemaSuite`, and `tools/hpw_run_substrate.sh:173` still defaults `HPW_VENV_PYTHON` to the
   stale `~/Coding/HemaSuite/hematology-paper-writer/.venv/bin/python` clone.
4. [suggested] `grounding-shadow-measurement` design gate is clean (v3, `PASS must=0 should=0`) —
   the feature is ready to move to Phase 5. Owned by the HemaSuite run, not this repo.

## Open / Blocked Items

- Two `h-mad` doc edits uncommitted on `main` — status: in progress, see Next Step 1. Suite verified
  green after them (h-mad 760 passed).
- `test_launcher_project_phase_routing.py` cannot run in the orca clone — status: blocked on a missing
  venv (`ModuleNotFoundError: No module named 'frontmatter'` at `tools/document_revisor.py:20`;
  falls back to anaconda 3.11). Pre-existing, not caused by this session's edits. The other 8 coupled
  files pass (58 tests).
- `grounding-shadow-measurement` Phase 5 — status: not blocked, just not started.
  `repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: main · worktree: none` ·
  artifacts: `docs/02-design/features/grounding-shadow-measurement.design.{md,audit.v1,audit.v2,audit.v3}.md`,
  `docs/01-plan/features/grounding-shadow-measurement.{spec,plan}.md`. The `audit.v2.md` file is a
  deliberate NO-REPORT record, not a verdict — do not read it as a gate.

## Context for Next Session

**Files touched this session:**
- `h-mad/SKILL.md` — exec-agy report-file exception; `--log` codex-only caveat; recovery scoped to implementer dispatches
- `h-mad/references/failure-recovery.md` — new row for phases 3/4/5b/6a-prime, `exec agy` no-sentinel
- `~/.claude/projects/-Users-kimhawk-orca-skills/memory/feedback_hmad_dispatch_verdict_echo_and_idle.md` — 2026-08-01 entry (not a git repo)
- `~/.claude/projects/-Users-kimhawk-orca-skills/memory/MEMORY.md` — hooks-only compaction, 21.1 KB → 14.9 KB, 111 entries, all links resolve

**Uncommitted changes:** 2 files — `h-mad/SKILL.md` (+35), `h-mad/references/failure-recovery.md` (+1)

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
git status --short                      # expect the 2 h-mad doc files
python3 -m pytest h-mad/tests/ -q       # expect 760 passed
```

**Related docs:**
- `docs/handoffs/2026-07-30-main__exec-missing-report-recovery-shipped.md` — the recovery rule this session scoped
- `docs/handoffs/2026-08-01-main__hmad-dispatch-timeout-pgroup.md` — earlier today, same wrapper
- `~/orca/HemaSuite/AGENTS.md:320` — F-10 claim-execution divergence, the capability-catalogue definition
- `/tmp/rev_gsm_design_c2.{txt,log}` — the 358 B artifacts (ephemeral; the analysis is preserved in `grounding-shadow-measurement.design.audit.v2.md`)
