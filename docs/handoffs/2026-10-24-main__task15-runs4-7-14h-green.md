# Handoff — grok-audit-surface: Task 15 runs 4–7, fixes 14e–14h; 14h GREEN verified but uncommitted

**Date:** 2026-10-24
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-23-main__grok-run3-agy-gate-halt.md, 2026-10-23-main__hemasuite-hmad-skill-defects.md

## Session Summary

Task 15 ran four more times. Each run fixed the measurement instrument that halted the run before it.

| Run | Outcome |
|---|---|
| 4 | `SMOKE: PASS` (`b1562dd4`); halted at S2 d2 on grep `pattern` |
| 5 | `SMOKE: FAIL`: the grok re-smoke hit the 900 s default |
| 6 | `SMOKE: PASS` (`533ed0c5`); halted at S2 d3 on `write.content` |
| 7 | `SMOKE: PASS` (`0b1dbb8d`); halted at S2 d1 on the shell `HOME=/tmp`, with `checkout=0` |

| Fix | Change | Commits |
|---|---|---|
| 14e | agy `read_file` → class (a) | `15110fbf`/`84d069ed` |
| 14f | grep `pattern` is not a path | `638fb51a`/`dbf92b17` |
| — | re-smoke `--timeout 1800` | `a805f07b` |
| 14g | grok payload-argument table | `b76e67af`/`896b9cf1` |
| 14h | contamination-only halt | RED `bae6f97b`; **GREEN in the working tree, uncommitted** |

14h GREEN is verified except for one re-specified mutant, whose re-score was killed by memory pressure. Run 8 is ready to launch.

## Key Learnings

- **The run-3 premise was false.** The agy gate denies in every phase when its root is not a git repo. agy runs the hook from `$ROOT/.agents`; `git -C <cwd>.parent rev-parse` raises, and `finally` denies with `kind=judge-error`. Only class (a) returns before that call. agy executes `read_file` (1,233 DONE steps) although its init inventory does not advertise the tool.
- **The scanner read data payloads as paths.** That happened twice: grep `pattern` (run 4) and `write.content` (run 6). A per-tool payload table fixed it. A census by argument key, plus a re-scan of every recorded log, is what turned "another false positive" into a class.
- **The real question was the halt policy, not exclusions.** All four S2 halts had `checkout=0`. The ruling: scan the truth, but halt only on contamination. Contamination now also covers `~/.local/state/h-mad` and other grok sessions. `/tmp` cannot be exempted as a blanket rule, because Claude scratchpads live under `/private/tmp/claude-501/`.
- **A mutant can go equivalent when a policy changes.** `p-contain-scan-forced` forced `checkout=0`, which no longer refuses under 14h. It was re-specified to force `checkout=1`, the faithful form. The re-score is still owed.
- **The Phase-5 judge needs the impl-plan mapping even for h-mad's own gate files** (`kind=no-test-resolved`). Every fix here needed its own Task 14x before Codex could write it.
- **Subagents' final reports were repeatedly swallowed by the bkit stop hook** ("Ignored."/"Skipped."). Verify subagent work on disk, never from the final message.
- **`test_hmad_dispatch_progress.py::test_agy_transcript_is_written_DURING_the_run_not_after` now fails at `HEAD` too** (`TimeoutExpired`). agy auto-updated 1.4.5 → 1.4.6 today. Environmental, not caused by 14h.

## Next Steps

1. **Re-score the re-specified mutant `p-contain-scan-forced`.** Build a one-row spec in the scratchpad, as I did; its `root` is the absolute path `/Users/kimhawk/orca/skills/h-mad`. Then run `python3 h-mad/scripts/h_mad_mutation_harness.py <one_row.json>`, reading the `MUTATION:` line. Run it in the foreground or with spare memory: it does a full baseline of the spec's `command` modules.
2. **If caught, commit 14h GREEN.** Files:
   - `h-mad/scripts/h_mad_tool_calls.py`
   - `h-mad/scripts/h_mad_grok_containment.py`
   - `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
   - `h-mad/tests/mutation-specs/grok_audit_surface.json` (431 rows)
   - `h-mad/tests/test_grok_audit_surface_containment.py` (post-RED update: the codex own-looking-session test now has `checkout=1`; disclose it)
   - `docs/03-analysis/grok-audit-surface.incident-2026-10-24-run7-shell-home-tmp.md` (calibration table)

   The message cites the anchors (`ANCHORS_OK` 431/431), mutation 430/431 plus the re-score, and the full suite at `7325 passed, 1 failed` (the unrelated agy-1.4.6 test). Push.
3. **Run 8.** Stamp the freeze with `hmad-dispatch worktree-comment active "… run 8 RUNNING — DO NOT COMMIT …"`, then run `bash ~/.local/state/h-mad/grok-audit-surface/run8-all.sh > …/run8-all.out.txt` in the background. The drivers are already built and syntax-checked. Keep every session off this checkout's `main` until step 9a.
4. On `RUN8: DONE through step 10`, do step 11 (impl-plan §Task 15): extract, then **hand labels by a labeller without the key**, then commit-data (the score sha). Then Task 16.
5. **Look at the agy 1.4.6 progress-test failure** in `h-mad/tests/test_hmad_dispatch_progress.py`. Re-run it when idle. If it fails again, file it as an h-mad defect (agy-version sensitivity).

## Open / Blocked Items

**This session:**

- **14h GREEN uncommitted.** Blocked on the mutant re-score (Next Step 1).
- **The h-mad claim on `grok-audit-surface` is released at this closeout.** `halt_reason` is `step5:task15:run7_toolscan_shell_home_tmp`; it says the operator ruling is owed, but that ruling is now given and implemented as 14h. The next session runs `h_mad_resume_decision.py`, then `--claim`.
- **Calibration branch tip:** `0b1dbb8d` (chain `f7520e72` → `b1562dd4` → `533ed0c5` → `0b1dbb8d`). These are smoke commits of halted runs 4, 6 and 7, so they are evidence and none is a reading. Run 8 pushes on top of them.
- **Run dirs 4–7** are kept as incident evidence; never score them. Their incident docs, under `docs/03-analysis/`:
  - `…incident-2026-10-23-run4-toolscan-false-positive.md`
  - `…-run5-grok-timeout.md`
  - `…-run6-toolscan-write-content.md`
  - `…incident-2026-10-24-run7-shell-home-tmp.md`
- **Residuals recorded in the impl-plan:**
  - shell text in `run_terminal_command` is still scanned; it halts only if it is contaminating;
  - the 14h `home + "/…"` concatenation has no `rstrip("/")`; harmless for the `--home "$HOME"` callers.
- **Policy B** (the agy gate denies `run_command` and writes when there is no git toplevel) is still open. Not needed for runs: agy reads and delivers via `out`.
- **Todos #5–#7 (next features)**, from the analysis doc review. These come after Task 15, or go in their own worktree:
  - H-MAD test-boundary + oracle fields with a deterministic check;
  - handoff redaction + next-session focus + scout remedy classes;
  - progressive disclosure, deferred: 82/192 h-mad and 7/12 handoff test modules read `SKILL.md`.
- **Analysis doc** `docs/03-analysis/2026-10-23-mattpocock-skills-hmad-handoff-review.analysis.md` is untracked and written by another session. Its owner should commit it; I did not.
- **Foreign `.codex/config.toml`**, untracked, appeared mid-session. Not ours; never stage it.
- **Local-only skills:** `.claude/skills/verify-hmad-gates/` and `.claude/skills/verify-hmad-claims/`. `.claude/` is gitignored, so they exist only on this machine.
- **TLA+ claim-model findings F1–F4**, recorded in `verify-hmad-claims/SKILL.md` §Findings. F2 was replayed on the real code: `--set owner_session_id=<me>` takes a LIVE owner's feature with rc 0. To be filed with todo #4.
- **pstack rule** `~/.claude/rules/pstack-models.md`: budget small, hardest tasks on `opus high`.

**Carried from `2026-10-23-main__grok-run3-agy-gate-halt.md`:**

- **Next Step 1 (operator decision on run 3):** CLOSED. Option A shipped as 14e; the cause was corrected (incident addendum).
- **Next Step 2 (run 4):** CLOSED, but superseded through runs 4–7 above. Run 8 is owed.
- **Next Step 3 (Task 16, Task 17, 5f/5g, Phase 6, Phase 7):** unchanged, blocked on Task 15. The 6a-prime range now also includes `15110fbf`..14h.
- **Next Step 4 (skill-candidates rows):** still open (todo #4).
  - Skills defects 1–12 are unfiled. HemaSuite's 9+2 were filed by HemaSuite itself in `f2a37a71`.
  - Dedupe: #1 = HS2, #2 = HS7, #4 ≈ HS1/HS5 (the agy part is fixed by 14e), #5 ≈ HS6.
  - Add the judge-mapping defect, F1–F4, and the agy-1.4.6 progress test.
- **Task 14d AC.5 load-sensitivity** and the 14c `status_dir` plan note: unchanged since 2026-10-23.
- **`implementation_authors` misattribution** (`path_scope_wire`): unchanged.
- **Foreign untracked files:** never stage `hemasuite/docs/research/` or the two 2026-10-22 analysis docs. Unchanged.
- **Halted run dirs `…T015212Z`, `…T044856Z`, `…T222714Z`:** evidence only. Unchanged.
- **h-mad tooling defects 1–7 (now 1–12):** merged into todo #4.
- **Local env:** `.h-mad/phase5-shell-allow` and root `.venv`. Unchanged.
- **Phase 6 residuals:**
  - T19 RMGUARD (D16);
  - T22 grep-whole-source.

  Unchanged.
- **About 179 leaked `hmad_exec_prompt.*`:** unchanged; probably more by now.
- **Owed measurement-class notes** (T19, T20, T25, T26, marker count, D18): unchanged.
- **Old S2 data `run-ab2c85dc2e25/`:** still the step-10 positive control. Unchanged.
- **HemaSuite PID 70888** and the escape diff backup: historical. Unchanged.
- **7 older `candidate: yes` rows** and the agy install-check gap (`:2673`): unchanged.
- **Other deferred items:**
  - the mutation-harness interpreter row;
  - the `backlog_cycle` LOW residuals;
  - census `--help`;
  - the `h_mad_mutation_harness.py:2300` SyntaxWarning, still printed on every run.

  Unchanged.
- **HemaSuite feature/204** and the foreign `stash@{0}` (`resolved-model`): untouched, intact. Unchanged.
- **Watch-only items** and the "advisor ceiling exceeded" note: unchanged. Context reached about 63% this session.
- **The two meta notes** ("WRITE does not verify claimed state", "plan audit exit stamp"): unchanged.
- **From `2026-10-02-main__v111-review-loop-closed.md`:** unchanged.
  - task #28 (`test_the_warn_and_target_fractions_still_match`);
  - the optional agy live smoke;
  - V-11.1 residuals;
  - the skill-candidates reconcile;
  - HemaSuite WSG pointer.

**Carried from `2026-10-23-main__hemasuite-hmad-skill-defects.md`:** CLOSED. Its items were filed by HemaSuite in `f2a37a71`; its claim was released (`d8598290`). Its sender-side pointer stays owed by HemaSuite's next WRITE on `BrightGold70/hemasuite-document-workbench`.

## Context for Next Session

**Commits this session (all on `main`, pushed through `bae6f97b`):** `15110fbf`, `65e0b34d`, `84d069ed`, `d8598290`, `cb2cfddf`, `638fb51a`, `dbf92b17`, `a805f07b`, `b76e67af`, `896b9cf1`, `bae6f97b`. Foreign: `f2a37a71`, by HemaSuite's session.

**Files touched:**
- Production:
  - `h-mad/hooks/h-mad-agy-tdd-gate.py`
  - `h-mad/scripts/h_mad_tool_calls.py`
  - `h-mad/scripts/h_mad_grok_containment.py`
  - `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
- Tests:
  - `h-mad/tests/test_h_mad_agy_tdd_gate.py`
  - `h-mad/tests/test_grok_audit_surface_toolscan_pattern.py` (new)
  - `…containment.py`
  - `…probe.py`
- Mutation specs: `grok_audit_surface.json` (now 431 rows) and `agy_tdd_gate.json`.
- Docs: the design, spec and impl-plan (now v1.18 / v1.23 / v1.16) and five incident docs.
- Drivers, in `~/.local/state/h-mad/grok-audit-surface/`: `run{4..8}-*`, `resmoke{4..8}.sh`, `s2-run{4..8}.sh`.

**Uncommitted changes:** 14h GREEN (6 files, listed in Next Step 2), plus the foreign untracked files.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature grok-audit-surface --session-id <id>
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature grok-audit-surface --claim <id>
git status --short   # expect the 6 14h GREEN files modified
```

**Related docs:**
- Impl-plan: §Task 14e–14h, §Task 15, §Task 16
- Design D8, D19–D21
- The incident docs listed above
- `docs/03-analysis/2026-10-23-mattpocock-skills-hmad-handoff-review.analysis.md`
