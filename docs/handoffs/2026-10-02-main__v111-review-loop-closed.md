# Handoff — V-11.1 review rounds 18–22 → canonical declaration, loop closed

**Date:** 2026-10-02
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-01-main__v111-file-tool-only.md

## Session Summary

Five fresh-context review rounds (18–22) ran against the V-11.1 checker
(`docs/03-analysis/probes/multi-host-runtime/smoke_assert.py` `v111`), each with a different
reviewer type. The checker now credits an `HMAD_HOST` declaration only from one completed
**canonical** event: `HMAD_HOST=<host> python3 <bound h-mad/scripts/h_mad_*.py> <plain args>`.
That event must itself be a declaring run. Other shell events are no longer judged, and their
environment effects are an accepted residual. The operator made each decision.

Round 22 found no HIGH, so the loop is **closed** under the operator's stop rule. Everything is
pushed (HEAD `7c2a1f27`) and the tree is clean. Rehearsal n=298 passes under Python 3.14 and
3.11. The live verdicts are now pinned from committed logs: grok PASS, agy FAIL, and codex
UNVERIFIED for any log.

## Key Learnings

- **"Redundant" guard removal caused 3 of the 5 rounds' worst defects.**
  - Round 19 dropped the template's script-name check "because `classify()` already requires
    `h_mad_*.py`". Round 20 then found that the template and the declaration came from
    *different* events.
  - Round 20's fix leaned on the same premise again, and round 21 found that `classify()` honoured
    `-m h_mad_x` *after* the script operand.
  - Round 21's count fix put the outer `bash -c` prefix on the wrong inner command (round 22).

  A mutation sweep cannot see redundancy that rests on a wrong premise, because no fixture
  combines the right events. The overlapping layers are now kept deliberately.
- **A verdict claim needs the actual log re-scored.** Round 18's commit said the live verdicts
  were unchanged. Nobody had re-scored the live grok log, and the new rule had made it
  UNVERIFIED. The log was found in an old scratchpad (`c7b2354c…/scratchpad/v11/grok/log`) and is
  now committed as `rehearsal/live-grok-2026-10-01.log`.
- **Real hosts declare in non-canonical forms too.** The live grok run used the adapter-style
  `$SKILL_ROOT` multi-command call. So "every declaration must be canonical" and "every shell
  event must be plain" both turn every realistic log UNVERIFIED. Require *one* canonical
  declaring event and nothing more.
- **pytest runs under `/opt/anaconda3/bin/python` (3.11), not `python3` (3.14).** 3.11's JSON
  decoder recurses, so a deep row crashed only under pytest. Run rehearse and mutation sweeps
  under both interpreters.
- **The mutation-harness control matters.** The first sweep showed every mutant "killed" because
  the harness crashed on load: a dataclass needs a `sys.modules` entry. Always run the unmutated
  source first, and require it to pass.
- **Subagent report delivery.** Reviewers were refused report-file writes, and replies truncate
  at about 4 KB. A SendMessage to "main" in chunks of 3 KB or less worked every time. Persist each
  chunk to `review-rNN/REPORT.md` as it arrives.
- **Under rtk, avoid `ls | head` and `tail | od` pipelines in Bash.** Two such commands hung to
  the 120 s timeout. Use `command ls`.

## Next Steps

1. **[task #28]** Fix `h-mad/tests/test_h_mad_check_memory_index.py::TestAgainstTheLiveBinary::test_the_warn_and_target_fractions_still_match`.
   It fails with "the 0.8/0.7 declaration pair is no longer in the binary" since Claude Code
   auto-updated to 2.1.287 mid-session. Re-probe the binary for the memory-index warn/target
   fractions. This is the only red test in the full suite (5263 pass).
2. **[optional]** Re-run the agy live smoke with an agy that reads through `view_file` first *and*
   declares canonically, `HMAD_HOST=agy python3 <root>/h-mad/scripts/h_mad_*.py …`. Plan:
   `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.plan.md` §"The smoke script"
   (part 2, with `--home "$HOME"` and all three `--link`s). Unchanged since 2026-10-01, apart from
   the new canonical requirement.
3. **[suggested]** Exercise `h_mad_assemble_tdd.py --phase green --mutation-spec <spec>` live on
   the next h-mad feature's 5e. It has only been tested offline. File:
   `h-mad/scripts/h_mad_assemble_tdd.py`. Unchanged since 2026-10-01.

## Open / Blocked Items

- **V-11.1 accepted residuals.** Status: deferred by design. They are documented in the spec's
  round-19 amendment block and the live-smoke addenda:
  - other shell events' effects on the environment, `python3` resolution and the cwd;
  - a quoted or escaped `HMAD_"HOST"=` name balancing a stray mention (round-22 F1, pinned at
    PASS);
  - the earlier read-side residuals (partial read, trusted start env, workspace-relative paths,
    codex injection, shell-before-reads voids them).

  The round-22 F2 fix (outer prefix counts on the first *script* in a wrapper) has had no fresh
  review.
- **tdd-gate-fail-opens evidence bookkeeping.** Unchanged since 2026-10-01: `reading-fixed.txt`
  MANUAL R-4/R-5, the T0 control, the T7 record and the census counts. See
  `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.report.md` §"Residual
  disposition". Status: deferred.
- **Skill-candidates reconcile not run this WRITE.** The census shows 33 open `yes` rows. The scout
  appended 2 rows but did not reconcile the open ones because the context budget was tight. Run
  `python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md` next session.
- **Foreign `stash@{0}` ("resolved-model", `7541628`).** Unchanged since 2026-09-29. Do not touch
  it.
- **HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`.** Unchanged since
  2026-09-14. Ownership stays here.
- **Closed this session:**
  - **Fresh-reviewer round on `v111`** (predecessor Next Step 1): done as rounds 18–22, in commits
    `99679c5f`, `0ce01a20`, `95ccfd12`, `7e542e85` and `7c2a1f27`. Reports are in
    `docs/03-analysis/probes/multi-host-runtime/review-r{18..22}/REPORT.md`.
  - **"Live verdicts unchanged" claim** in `99679c5f`: false when written. Corrected in the
    live-smoke addendum (round 19), and both live logs are now pinned in the rehearsal.

## Context for Next Session

**Files touched this session:**
- `docs/03-analysis/probes/multi-host-runtime/smoke_assert.py`
- `docs/03-analysis/probes/multi-host-runtime/rehearsal/`: `cases.json` (now 298 cases), about
  120 `R18-*`–`R22-*` fixtures, and `live-grok-2026-10-01.log`
- `docs/03-analysis/probes/multi-host-runtime/review-r18`–`review-r22/REPORT.md`
- `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.{spec,live-smoke}.md`

**Uncommitted changes:** none, apart from this handoff.

**Mutation harness** (not committed): scratchpad
`/private/tmp/claude-501/-Users-kimhawk-orca-skills/e649d0b2-3026-4ac7-b2ed-505eceb4f931/scratchpad/mut/sweep.py`.
It has an unmutated control, one module per mutant, and `sys.modules` registration; run it under
both `python3` and `/opt/anaconda3/bin/python`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills && git checkout main && git pull --ff-only
python3 docs/03-analysis/probes/multi-host-runtime/smoke_assert.py rehearse            # PASS n=298
/opt/anaconda3/bin/python docs/03-analysis/probes/multi-host-runtime/smoke_assert.py rehearse  # PASS n=298
pytest -q h-mad/tests/test_h_mad_check_memory_index.py   # task #28, currently red
```

**Related docs:**
- `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.spec.md`: the "Amended 2026-10-01
  (operator decision, review round 19)" block and its round-20, 21 and 22 bullets.
- `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.live-smoke.md`: the round 18–22
  addenda.
- Memory: `feedback_shell_text_classifier_never_converges.md`.
