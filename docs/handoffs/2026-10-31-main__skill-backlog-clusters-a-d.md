# Handoff — skill-candidates backlog 26 → 5 (clusters A–D), bkit 2.1.41 on Hawui-Macmini

**Date:** 2026-10-31
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-29-main__hmad-test-boundaries-complete.md
**Next-Session Focus:** decide the five design-gated backlog rows, or run the Mac Studio bkit/codex chores when on that machine.
**Suggested-Skills:** h-mad (row 2847 or 2846 as a feature, if chosen)

## Session Summary

On Hawui-Macmini, the session resumed the 2026-10-29 handoff and took the `docs/skill-candidates.md` backlog from 26 open rows to 5. It closed 21 rows: 2 declined, 2 superseded, and the rest fixed test-first in four clusters, all pushed to `origin/main`:
- B (claim protocol): `8c0823d6`.
- A (Phase-5 interpreter trust): `82f6a5a4`.
- C (TDD judge gaps): `d70ee861`.
- D (seven small fixes, built by parallel agents in worktrees, then merged): `d6a55c40`.

Every cluster passed a fresh-context `change-reviewer`, and each review's findings were fixed before merging. Every touched mutation spec is ALL_CAUGHT, and each regression run was compared failure ID by failure ID against a clean `main` worktree. This Mac was also upgraded to bkit 2.1.41, with the patch-verify hook installed and the two still-needed patches re-applied. The g001 and subagentstop patches were retired in the repo (`bb21715f`), because 2.1.41 fixes both upstream (#161, #162).

## Key Learnings

- **This Mac has a fixed set of environment-only test failures.** It lacks `python3.11` and `/opt/anaconda3`. Across 157 related test files, the same 38 fail on clean `main`:
  - 23 in `test_hmad_dispatch_audit_cycle.py`
  - 7 in `test_h_mad_mutation_harness.py`
  - 4 in `test_grok_audit_surface_wrapper.py`
  - 2 in `test_hmad_dispatch_audit_cycle_grok.py`
  - 1 in `test_h_mad_new_gate.py`
  - 1 in `test_h_mad_codex_runtime.py`

  Compare failure IDs against a clean `git worktree add --detach … main` run, never counts. `test_hmad_dispatch_exec_stamp.py::test_heartbeat_without_timeout_keeps_the_same_cadence` is a wall-clock test that flakes under load and passes in isolation.
- **Editing a tree while a background pytest/regression run uses it contaminates the run.** It also hits the suite lock (`SUITE: BUSY`). Stop the run, edit, then re-run.
- **A re-dump with `json.dumps` reformats mutation specs.** Compact arrays expand, and `\u` vs raw-UTF-8 escaping flips. Append rows as text, or check that `git diff` shows only additions.
- **Inserting a new parametrize case shifts the auto-generated `targetN` IDs that mutation rows name.** Re-map them from `--collect-only`.
- **The fresh-context reviews caught real false-ALLOWs that the tests did not.** The cluster C import-RED rule first matched on module name only, which let a same-named stdlib `json` or a sibling `utils.py`, and a shadowing `; 'pkg' is not a package`, count as RED. The fix requires file evidence: the printed source path, or "target file does not exist yet".
- **The final regression run caught something the review missed.** The committed-spec anchor sweep failed after a review fix moved two mutant anchors. Always re-run the anchor sweep after the review-fix commit.
- **`git merge` does not accept `-F -` (stdin).** Use a message file.

## Next Steps

1. Decide each open backlog row (`docs/skill-candidates.md`; census: `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`):
   - **2847** `implementation_authors` correction route. Needs a schema change plus the SKILL.md attribution prose (~line 353). Choose: `/h-mad` feature or planned batch.
   - **2846** `.sh` production files are never gated by wire-pin or TDD. Feature-scale.
   - **2809** mutation-row re-anchor semantic diff. Needs a design ruling on "same tokens".
   - **2726** read-only `git` verbs in the Phase-5 gate. Deferred; needs a flag denylist (`--output`, `--output-directory`, `-o`, `--ext-diff`, `--textconv`).
   - **2852** null heartbeat counts as live (`owner_is_live(None)`). A design call, pinned on purpose by `test_a_claim_with_no_heartbeat_is_treated_as_live`. The F2 half has landed.
2. On the **Mac Studio**:
   - Upgrade bkit: `claude plugin marketplace update bkit-marketplace` then `claude plugin update bkit@bkit-marketplace`.
   - Re-apply only `docs/patches/bkit-g004-protected-branch-precision` and `bkit-sprint-stop-hook-active` (`patch -p1` in `~/.claude/plugins/cache/bkit-marketplace/bkit/2.1.41`, after a `--dry-run`).
   - `rm ~/.claude/state/patch-verify.state` and run `~/.claude/hooks/patch-verify-on-update.sh`. Expect OK.
3. On the **Mac Studio**: re-pin codex. Start a codex pane in `~/orca/skills`, run `h-mad/bin/hmad-dispatch pin-agents`, and confirm `hmad-dispatch env` → `PREFLIGHT: PASS`. The stale pin `term_134b0865…` lives in the Studio's `.h-mad/orca-pins.env`.

## Open / Blocked Items

Carried from `2026-10-29-main__hmad-test-boundaries-complete.md`. Every item is accounted for:
- **Next Step 1, row 28 split**: closed, `234f9be0`.
- **Next Step 2, row 18**: closed, `8597bce9`.
- **Next Step 3, triage rows 33/35/38/39/44/46**: closed. Outcomes recorded in `830b3943`.
- **Next Step 4 / Hawui-Macmini bkit patches + patch-verify hook**: closed this session.
  - bkit 2.1.40 → 2.1.41.
  - Hook copied to `~/.claude/hooks/` and registered in the `~/.claude/settings.json` SessionStart hooks (backup `settings.json.bak-*`).
  - g004 and sprint-stop-hook-active re-applied.
  - Hook reports OK for all 6 patches.
  - These are machine-local changes; there is no commit.
- **Next Step 5 / bkit #162 and #161**: closed. Both issues are CLOSED upstream and fixed in v2.1.41. The local g001 and subagentstop patches are retired in `bb21715f`; their `verify.js` files stay as upstream regression checks.
- **Mac Studio carried bkit patches + hook copy**: open, blocked on access to the Mac Studio. Next Step 2.
- **`skill-candidates` census OPEN 31 → 5 → 9**: open. Next Step 1 covers the 5 carried rows. This closeout's scout then appended 4 new candidates, all tool or check improvements seen 2–4 times this session: a census `--stamp` verb, a clean-main regression-diff script, a text-preserving `--append-row` for the harness, and a per-run suite-command override.
- **HemaSuite `document-intake-source-review::Task 6` WIRE-RUNNER**: owed by HemaSuite, unchanged since 2026-10-27.
  - repo: `/Users/kimhawk/orca/HemaSuite` · branch: main · worktree: none.
- **Wire-registry `missing=268`**: possibly addressed by `d05c85da` (Triage Row 5, which resolves parametrized pins and subproject rootdir paths). That commit was made before this session; not re-verified here.
- **Codex pin `term_134b0865…` stale**: open, on the Mac Studio. Next Step 3. `hmad-dispatch exec codex` is unaffected meanwhile.
- **Run 8 attempts 1–2**: evidence only, never scored. Unchanged since 2026-10-27.
- **Rows 23 and 34**: closed in the 2026-10-29 triage outcome table (`830b3943`). 23 verified; 34 has 0 leaked temp files.
- **Rows 41, 49, 50, 52 (blocked on HemaSuite)**: handed over or closed in `4972c653` and the triage outcome table. 50 and 52 are recorded closed.
- **Watch-only rows**: unchanged.
- **Residuals recorded in this session's stamps, not filed as rows**:
  - **Name map:** the generic `*test_*` skip still hides `h_mad_test_boundaries_check.py`.
  - **Missing receipt:** `h_mad_archreview_cycle.py` prompts write no `.assembled` receipt.
  - **Install check scope:** no user-level agy `hooks.json` is read.
  - **Codex hook timeout:** Codex's default hook timeout is unmeasured. `.codex/hooks.json` sets none, so it may cut short a `**Judge budget**` above it; a cut-short hook refuses.

## Context for Next Session

**Files touched this session** (all committed and pushed; `main` = `origin/main` at `d6a55c40` before this handoff commit):
- **Cluster B**:
  - `h-mad/scripts/h_mad_state_write.py`
  - `h-mad/tests/test_h_mad_state_write.py`
  - `h-mad/tests/mutation-specs/heartbeat_beat.json`
  - `h-mad/scripts/h_mad_archreview_cycle.py`
- **Cluster A**:
  - `h-mad/scripts/h_mad_target_identity.py`
  - `h-mad/scripts/h_mad_assemble_tdd.py`
  - `h-mad/scripts/h_mad_tdd_judge.py`
  - `h-mad/references/codex-runtime.md`
  - Tests and specs: `codex_gate_shell_allowance`, `assemble_tdd`, `tdd_judge_venv`
- **Cluster C**:
  - `h_mad_tdd_judge.py`
  - `h_mad_wire_pin_gate.py`
  - `h_mad_derive_test_path.sh`
  - `references/inline-protocols.md`
  - Tests and specs: `tdd_judge_scoring`, `tdd_judge_resolution`
- **Cluster D**:
  - `h_mad_install_check.py`
  - `hmad-dispatch.sh`
  - `h_mad_assemble_audit.py`
  - `h_mad_audit_gate.py`
  - `codex-verifier-prompt.md`
  - `audit-prompt.template.md`
  - `h_mad_wire_pin_gate.py`
  - `h_mad_tool_calls.py`
  - Tests and specs, including the new `wire_pin_path_labels.json`
- **bkit retirement**: `docs/patches/bkit-g001-bare-heredoc-substitution/{README.md,verify.js}`, `docs/patches/bkit-subagentstop-additionalcontext/{README.md,verify.js}`
- **Shared docs**: `h-mad/SKILL.md` (several sections), `docs/skill-candidates.md` (stamps)
- **Trail learnings**: `.trail/learnings/2026-10-31-resume-from-2026-10-29-handoff-hawk.md`, `.trail/learnings/2026-10-31-hawui-macmini-on-bkit-2-1-hawk.md`
- **Machine-local, not in the repo**: `~/.claude/settings.json` (SessionStart hook entry), `~/.claude/hooks/patch-verify-on-update.sh`, the bkit 2.1.41 plugin cache (patched), and the memory file `python-interpreters-this-mac.md` (32/38-failure baseline, harness `--python`)

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md
# tests on this Mac: /opt/homebrew/opt/python@3.14/bin/python3.14 -m pytest <files>
# mutation: h-mad/scripts/h_mad_mutation_harness.py --python /opt/homebrew/opt/python@3.14/bin/python3.14 <spec>
```

**Related docs:**
- `docs/skill-candidates.md` — every landed row carries its stamp, decision and residuals.
- `docs/03-analysis/2026-10-25-backlog-triage.md`
- `docs/patches/` — bkit patch READMEs; RETIRED status on g001 and subagentstop.
