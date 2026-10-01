# Handoff — V-11.1 agy adapter decision → file-tool-only read credit

**Date:** 2026-10-01
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-01-main__backlog-cleared.md

## Session Summary

This session started by deciding the agy V-11.1 question as **lazy**: a read-only status call
need not read its adapter. Making that safe exposed a long run of fail-opens in the V-11.1
checker (`docs/03-analysis/probes/multi-host-runtime/smoke_assert.py` `v111`), and 17
adversarial review rounds followed.

The operator then made two decisions:
- **Only file-tool reads earn credit.** These are agy `view_file` and grok `read_file`. Codex is
  always `UNVERIFIED V-11.1 codex has no file-read tool`.
- **Every shell command counts as a possible write.** A read counts only if it completes before
  any shell command, unmapped tool or unknown row.

The session also verified that HemaSuite picked up the run-verb fix. All work is pushed: HEAD is
`5aec6cc0`, the full suite passed 5264, the tree is clean, and the live verdicts are unchanged
(grok PASS, codex UNVERIFIED, agy FAIL).

## Key Learnings

- **Judging shell-command text never converged.** Each review round found 2–4 new zsh tricks:
  - subscript math `$PWD[HOME=7]`;
  - `printf %d HOME=7`;
  - `[ -v 'x[N=5]' ]`;
  - `${NAME::=v}`;
  - `cat < <(cp …)`;
  - `HMAD_HOST=grok"agy"`.

  Denylists and allowlists both leaked. What held was removing the class: credit only structured
  tool events, and fail closed on every shell event.
- **Fresh-context reviewers found classes that an 11-round reviewer had stopped seeing.** Its
  first "clean" round was followed by 3 new HIGH findings from a fresh reviewer. Rotate
  reviewers rather than reusing one.
- **Order reads by completion, not by issue.** Hosts run tools in parallel, so a write issued
  after a read can still finish first and change what the read returns.
- **Ad-hoc mutation sweeps can reuse stale bytecode.** When every mutant is written to the same
  `_mut.py`, Python can reuse a cached `.pyc` (it checks mtime to the second, plus size), which
  gives false kills. Fix: one module per mutant, `sys.dont_write_bytecode`, assert the mutant
  differs from the original, and count a crashing mutant as killed. The repo harness
  `h_mad_mutation_harness.py` already clears `__pycache__`.
- **Running only the delta tests missed a break on `main`.** Committing the captured live agy log
  (`87472fd0`) broke a repo-wide grep test, `test_nothing_sources_the_wrapper…`. It was fixed in
  `a3133b34` with `--exclude=*.log`. The full suite is what catches this.
- **The live agy log had survived in an old session scratchpad.** A record that says "log not
  retained" can be wrong: search the scratchpads before concluding it.

## Next Steps

1. **[optional]** Run another fresh-reviewer round on `smoke_assert.py` `v111` at `5aec6cc0`. The
   last round (17) found fixable issues, and none has been run since. Spec block:
   `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.spec.md`, "Amended 2026-10-01
   (operator decision)". Use rehearsal `python3 docs/03-analysis/probes/multi-host-runtime/smoke_assert.py rehearse`
   (n=176) and the mutation sweep recipe described in Key Learnings.
2. **[suggested]** Exercise `h_mad_assemble_tdd.py --phase green --mutation-spec <spec>` live on
   the next h-mad feature's 5e. It has only been tested offline. File:
   `h-mad/scripts/h_mad_assemble_tdd.py`.
3. **[optional]** Re-run the agy live smoke with an agy that reads through `view_file` first,
   using the plan's part 2 with `--home "$HOME"` and all three `--link`s. Plan:
   `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.plan.md` §"The smoke script".

## Open / Blocked Items

- **V-11.1 checker residuals.** Accepted and documented in the spec and in the `live-smoke.md`
  addenda:
  - a partial read counts;
  - the trusted starting environment;
  - workspace-relative tool paths;
  - codex output injection;
  - any shell command before the reads voids them. The design cases `R7-sed`/`R7-grep` now FAIL.

  Status: deferred by design.
- **tdd-gate-fail-opens evidence bookkeeping.** Unchanged since 2026-10-01. It covers
  `reading-fixed.txt` MANUAL R-4/R-5, the T0 control, the T7 record and the census counts; see
  `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.report.md` §"Residual
  disposition". Status: deferred.
- **Foreign `stash@{0}` ("resolved-model", `7541628`).** Unchanged since 2026-09-29. Do not touch
  it.
- **HemaSuite pointer `2026-09-14-main__wsg-backlog-two-items-owed-here.md`.** Unchanged since
  2026-09-14. Ownership stays here.
- **Closed this session:**
  - **agy adapter question (V-11.1):** decided lazy, then superseded by the file-tool-only rule.
    Commits: `8f219cb4`, `87472fd0`, `a3133b34`, `21ef5839`, `98e68f87`, `a6bd786c`,
    `5aec6cc0`. Live agy was re-scored from the retained log as a genuine FAIL.
  - **HemaSuite run-verb notification:** verified picked up. The note appears in
    `t9_green.prompt` (05:20) and is absent from every prompt from 05:49 onward. Lane: repo
    `/Users/kimhawk/orca/workspaces/HemaSuite/citation-fidelity-judge`, branch
    `BrightGold70/citation-fidelity-judge`.
  - **`main` broken by the committed live log:** fixed in `a3133b34`.

## Context for Next Session

**Files touched this session:**
- `docs/03-analysis/probes/multi-host-runtime/smoke_assert.py` and `rehearsal/` (`cases.json` and
  about 60 fixtures)
- `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.{spec,plan,design,live-smoke}.md`
- `h-mad/SKILL.md` §Host runtime
- `h-mad/tests/test_host_runtime_docs.py`, `h-mad/tests/test_hmad_dispatch_torn_read.py`

**Uncommitted changes:** none, apart from this handoff.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills && git checkout main && git pull --ff-only
python3 docs/03-analysis/probes/multi-host-runtime/smoke_assert.py rehearse   # expect PASS n=176
```

**Related docs:**
- `docs/archive/2026-09/multi-host-runtime/multi-host-runtime.live-smoke.md`: the addenda record
  every round.
- Memory: `feedback_shell_text_classifier_never_converges.md`.
