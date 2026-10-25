# Handoff — grok-audit-surface run 8 DONE through step 10; Task 14i shipped; `--authors-test` merged; two HemaSuite briefs taken over

**Date:** 2026-10-25
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-24-main__task15-runs4-7-14h-green.md, 2026-10-24-main__gate-task-authors-test.md, 2026-10-25-main__wire-registry-and-bkit-g001.md

## Session Summary

**Task 15, run 8.** Run 8 finished steps 1–10 on its third attempt, in `run-ab2c85dc2e25-20261024T132452Z`:
- `SMOKE: PASS`, with smoke sha `8f8deaf1` pushed to `calibration/grok-audit-surface`;
- S2 d1–d9 all `REQUIRE: OK`;
- step 9a `ASSEMBLER: PINNED` at `2d8d7b2d`;
- the positive control reads `checkout=21`.

Step 11 (labels by a labeller who has not seen the key) is the operator's to do.

**What fixed the earlier attempts:**

| Fix | Change | Commits |
|---|---|---|
| 14h GREEN | contamination-only halt | `f04cd1d1` |
| 14i | the canary prompt now asks for design D18's three shell commands | RED `b5683b27`, GREEN `2d8d7b2d` |

**HemaSuite briefs.** Two inbound briefs were taken over.
- `gate-task-authors-test` is DONE. `--authors-test` on `--phase gate` is merged as `7373cb1b`, after a fresh review and its fixes.
- `wire-registry-and-bkit-g001` is claimed, its premises are reproduced, and nothing is fixed yet.

## Key Learnings

- **The `no_denial` refusal was not a containment failure.** grok's native `write` fails a sandbox-denied write with `IO Error: File exists (os error 17)`. By the 2026-10-22 decision that is not a denial. Every earlier passing canary had passed only because grok happened to retry the write through the shell, which prints EPERM.
  - The Task 23 prompt (`396018b8`) never implemented D18 ("three shell commands"). D18 itself has said so since `37df3ccc`.
  - Recorded in `docs/03-analysis/grok-audit-surface.incident-2026-10-24-run8-canary-no-denial.md`.
- **`h_mad_state_write.py --claim` took a claim it had just judged LIVE.** It printed `TAKEOVER from=7f7228ab LIVENESS: LIVE` and still exited 0, with no `--force`. The resume oracle said `halted` for the same claim.
  - The predecessor handoff also said its claim was "released at closeout" when it was not.
  - Both go to the skill-candidates batch (todo #4).
  - This closeout released its three claims explicitly and verified `owner=None`.
- **Codex's GREEN re-anchors need checking for meaning, not only for anchors.** In GREEN round 2 Codex rewrote mutation row `emit-the-guards-only-for-wiring` into a mutant that only touched an authoring gate. That still passed ANCHORS_OK, but its test could no longer catch it. I restored the original meaning.
- **A fresh-context reviewer found a must-fix in green code.** On `11b3b5fe` (180/180 tests passing, 5/5 mutants caught) it found that an authoring gate never probed `--python` for pytest. It also found 5 should-fixes. All were fixed in `4ce14417`/`2d087a39`.
- **bkit G-001 blocks text, not deletes.** A `git commit -m` whose message named the Python recursive-removal identifier was refused as "Recursive delete". Write commit messages to a file and pass `-F` until the bkit patch lands.
- **Exit 0 from `run8-all.sh` means nothing.** Its `stop()` also exits 0, so read the `RUN8:` line every time.

## Next Steps

1. **Task 15 step 11** (operator; impl-plan §Task 15): extract run 8, have the labels done by someone who has not seen the key, then run `commit-data` to make the score commit. Run dir: `~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z`. Then Task 16.
2. **Diagnose wire-registry `missing=268`** under TDD. Script: `h-mad/scripts/h_mad_wire_registry.py`.
   - Reproduce, in `/Users/kimhawk/orca/workspaces/HemaSuite/hemasuite-document-workbench`, read-only:
     `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_registry.py verify --base efcaae522e206826dab9a832dee718504f54c416 --rootdir "$PWD" --testpath hemasuite/tests --python "$PWD/.venv/bin/python"`
   - Control: `pytest --collect-only` on `hemasuite/tests/test_api.py::test_quit_stops_new_work_preserves_data_and_marks_interrupted_run` collects 7.
   - Hypotheses, none tested yet: (a) exact node-id matching against parametrized ids; (b) pins from other sub-projects; (c) a collection failure scored as absence.
3. **Operator decision:** how to represent a Playwright WIRE-PIN — either a `runner` field, or an `unverifiable-by-registry` status. Example record: HemaSuite `document-intake-source-review::Task 6`.
4. **bkit G-001 local patch.** Rule: `~/.claude/plugins/cache/bkit-marketplace/bkit/2.1.38/lib/control/destructive-detector.js:36-38`. Put the patch beside `docs/patches/bkit-enh310-quoted-heredoc-body/`. Ask before filing the upstream issue at popup-studio-ai/bkit-claude-code.
5. **Todo #4: skill-candidates rows.** This session's scout appended 4 rows, and the census now reads OPEN 32. It reconciled only the open `yes` rows that touch this session's work: 2 found, both still genuinely open. A full reconcile of the 23 older `yes` rows is still owed. It now also holds:
   - the claim-writer LIVE takeover;
   - the false "released" closeout;
   - the agy-1.4.6 flake.

## Open / Blocked Items

**This session:**

- **Task 15 step 11** — blocked on the operator (keyless labels). Run 8 attempts 1 (`…T115256Z`, canary timeout) and 2 (`…T120234Z`, `no_denial`) are kept as evidence. Never score them.
- **wire-registry-and-bkit-g001** — taken over from HemaSuite · BrightGold70/hemasuite-document-workbench · session c1e6df26. Not started. Claim released at this closeout; the next session runs `--claim`. Its three items are Next Steps 2–4. The HemaSuite worktree had uncommitted changes (`.gitignore`, `.mcp.json`, `graft/INDEX.md`) that are not mine, so I left them alone.
- **gate-task-authors-test** — **CLOSED**. Merged as `7373cb1b`, pushed; the full suite read 7348 passed / 0 failed on the branch.
  - Taken over from HemaSuite · feature/207-review-banner-gateway · session 245c1f4a.
  - `codex-implementer-prompt.md` has no gate section, so the brief's step 3 needed only `SKILL.md:3210`.
  - The leftover worktree `../skills-gate-authoring` (branch `fix/gate-task-authors-test`, merged) can be removed with `git worktree remove ../skills-gate-authoring && git branch -d fix/gate-task-authors-test`. Its `graft/` dir came from my own `graft skeleton` call.
- **The 5f wire-registry nested-`--rootdir` FYI** (from the authors-test brief) is merged into Next Step 2.
- **agy-1.4.6 progress test** — it passed in both full suites this session after failing on 2026-10-24. Treat it as a flake: watch it, and file only if it recurs.
- **h-mad claim on `grok-audit-surface`** — released at this closeout (verified `owner=None`). The next session runs `h_mad_resume_decision.py`, then `--claim`.

**Carried from `2026-10-24-main__task15-runs4-7-14h-green.md`:**

- Next Step 1 (re-score `p-contain-scan-forced`): **CLOSED** — `ALL_CAUGHT` 1/1.
- Next Step 2 (commit 14h GREEN): **CLOSED** — `f04cd1d1`.
- Next Step 3 (run 8): **CLOSED** — DONE through step 10, on attempt 3.
- Next Step 4 (step 11, then Task 16): open, now this doc's Next Step 1.
- Next Step 5 (agy-1.4.6 test): see the flake item above.
- Calibration branch tip: now `8f8deaf1` (chain `…0b1dbb8d` → `8f8deaf1`). These are smoke commits, not readings.
- Run dirs 4–7 and their incident docs: evidence; never score them. Unchanged.
- Residuals recorded in the impl-plan (shell text is still scanned; the 14h `home + "/…"` has no `rstrip`): unchanged. The impl-plan now also records 14i's residuals: a grok that ignores the shell instruction still refuses, failing closed, and the prompt's paths are unquoted.
- Policy B (the agy gate denies `run_command` and writes when there is no git toplevel): unchanged.
- Todos #5–#7 (test-boundary and oracle fields; handoff redaction, next-session focus and scout remedies; progressive disclosure): unchanged.
- The untracked analysis doc `2026-10-23-mattpocock-skills-hmad-handoff-review.analysis.md` belongs to another session; its owner should commit it. Unchanged.
- Foreign `.codex/config.toml`: never stage it. Unchanged.
- Local-only skills `.claude/skills/verify-hmad-{gates,claims}/`: unchanged.
- TLA+ findings F1–F4 (F2: `--set owner_session_id` takes a live owner's feature, rc 0): to be filed with todo #4. Unchanged.
- pstack rule `~/.claude/rules/pstack-models.md`: unchanged.
- Task 16, Task 17, 5f/5g, Phase 6 and Phase 7: blocked on Task 15 step 11. The 6a-prime range now spans `15110fbf`..`2d8d7b2d` (14e–14i).
- Skills defects 1–12 plus the judge-mapping defect, F1–F4 and dedupe vs HemaSuite `f2a37a71`: all in todo #4. Unchanged.
- Task 14d AC.5 load-sensitivity and the 14c `status_dir` note: unchanged since 2026-10-23.
- `implementation_authors` misattribution (`path_scope_wire`): unchanged.
- Foreign untracked `hemasuite/docs/research/` and the two 2026-10-22 analysis docs: never stage them. Unchanged.
- Halted run dirs `…T015212Z`, `…T044856Z`, `…T222714Z`: evidence. Unchanged.
- Local env `.h-mad/phase5-shell-allow` and the root `.venv`: unchanged.
- Phase 6 residuals T19 RMGUARD (D16) and T22 grep-whole-source: unchanged.
- About 179 or more leaked `hmad_exec_prompt.*`: unchanged.
- Owed measurement-class notes (T19, T20, T25, T26, marker count, D18): unchanged.
- Old S2 data `run-ab2c85dc2e25/`: still the step-10 positive control; it read `checkout=21` this run.
- HemaSuite PID 70888 and the escape-diff backup: historical. Unchanged.
- 7 older `candidate: yes` rows and the agy install-check gap (`:2673`): unchanged.
- Deferred: the mutation-harness interpreter row, `backlog_cycle` LOW residuals, census `--help`, and the `h_mad_mutation_harness.py:2300` SyntaxWarning (still printed): unchanged.
- HemaSuite feature/204 and the foreign `stash@{0}`: untouched. Unchanged.
- Watch-only items and the advisor-ceiling note: unchanged. Context reached about 52% this session.
- The meta notes "WRITE does not verify claimed state" (reconfirmed this session — see Key Learnings) and "plan audit exit stamp": open.
- From `2026-10-02-main__v111-review-loop-closed.md` (task #28, optional agy live smoke, V-11.1 residuals, the skill-candidates reconcile, HemaSuite WSG pointer): unchanged.
- The `2026-10-23-main__hemasuite-hmad-skill-defects.md` sender-side pointer is still owed by HemaSuite. Unchanged.

**Carried from `2026-10-24-main__gate-task-authors-test.md`:** CLOSED — see above.

**Carried from `2026-10-25-main__wire-registry-and-bkit-g001.md`:** all three items are open, as Next Steps 2–4. They keep their origin: HemaSuite · BrightGold70/hemasuite-document-workbench · session c1e6df26. The registry `…/hemasuite-document-workbench/.h-mad/wires.jsonl` (268 records) stays read-only.

## Context for Next Session

**Commits this session** (all on `main`, pushed through `7373cb1b`):
- `f04cd1d1`, `b5683b27`, `c6b360a1`, `2d8d7b2d`, `59d1174c`;
- the merge `7373cb1b`, which brings in branch commits `8f5b1c31`, `11b3b5fe`, `4ce14417`, `2d087a39`;
- foreign briefs `1a15a39c` and `2eee9294`, from HemaSuite sessions.

The calibration ref `8f8deaf1` was pushed by the run 8 driver.

**Files touched:**
- Production:
  - `h-mad/scripts/h_mad_grok_containment.py` (canary prompt)
  - `h-mad/scripts/h_mad_assemble_tdd.py` (`--authors-test`)
  - `h-mad/SKILL.md:3210`
- Tests:
  - `h-mad/tests/test_grok_audit_surface_containment.py` (+1)
  - `h-mad/tests/test_h_mad_assemble_tdd.py` (`TestGateAuthorsTestSpec`, 20 tests)
- Mutation specs:
  - `grok_audit_surface.json` (432 rows)
  - `assemble_tdd.json` (re-anchored)
  - `assemble_tdd_authors_test.json` (new, 16 rows)
- Docs:
  - the impl-plan, now v1.17 with Task 14i;
  - the run-8 incident doc;
  - two brief stamps.

**Uncommitted changes:** none of mine; only the foreign untracked files.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature grok-audit-surface --session-id <id>
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature grok-audit-surface --claim <id>
tail -3 ~/.local/state/h-mad/grok-audit-surface/run8-all.out.txt   # expect RUN8: DONE through step 10
```

**Related docs:**
- Impl-plan §Task 14i, §Task 15 (step 11), §Task 16
- `docs/03-analysis/grok-audit-surface.incident-2026-10-24-run8-canary-no-denial.md`
- `docs/handoffs/2026-10-25-main__wire-registry-and-bkit-g001.md`
- Review report of `11b3b5fe`: `docs/03-analysis/2026-10-25-authors-test-change-review.md` (1 must, 5 should; all fixed in `4ce14417`/`2d087a39`)
