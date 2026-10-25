# Handoff — Task 15 step 11: `extract` done; blind-agent labelling planned, not yet dispatched

**Date:** 2026-10-25
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-25-main__run8-done-authors-test-merged.md

## Session Summary

I resumed from the run-8 handoff and began Task 15 step 11. **`extract` is DONE.** It used seed `773509911` against smoke commit `8f8deaf1`, and printed `FINDINGS: WRITTEN findings=130 must=86 should=44 reports=27`.

The operator ruled that the labeller is **an agent that sees only the extract output**, not the operator. I built a sandbox package for it, but **no labeller is dispatched yet**: the session stopped for a machine change.

**Step 11 can only resume on THIS Mac** (or after copying the state dir). The run dir and `key.jsonl` live in `~/.local/state`, which is not in git.

No commits were made this session, apart from this handoff.

## Key Learnings

- **A copy is not containment.** A labeller subagent runs as the same uid, so it can still open `$READING/key.jsonl`, `$RUN/work/extract-stdout.txt` (its `HINT: … candidate-hit:` lines) and `$RUN/stem/*.command.txt` (which prints `--surfaces codex,agy,grok`). Before dispatch, `chmod 000 "$RUN"` and `chmod 000 run-current.env`. Restore both before `commit-data`.
- **The export roots leak which pass wrote what.** Every per-doc root holds the run's own outputs:
  - `docs/01-plan/features/<feat>.<phase>.audit.v1.p{1,2,3}.md(.effort.json)`;
  - `.hmad-report/*_pN.report.md`;
  - `.h-mad/pass-logs/`;
  - `graft/.cache/session/*.json`.

  All four must be excluded from the labeller's copy. Do NOT exclude the older historical `*.audit.vN.md` files: they are source.
- **The per-pass prompts are identical apart from the report path.** `diff` of `_p1.txt` against `_p3.txt` shows only lines 74 and 1153, the `.hmad-report/…_pN.report.md` path. So one `p1` prompt per doc, with that path redacted, is a complete assembled prompt that does not name the surface.
- **The raw `ledger.jsonl` has no `doc` field.** `score` adds it (`grok_audit_probe.py:1582`: `{**seed, "doc": doc_ids[seed["source"]]}`), and `check_labels` (`:1510`) needs it for `HIT` validation. Seed ids carry the doc as a prefix (`d1-s1`).
- **`commit-data` is add-only.** It refuses `would_replace:`. A bad `labels.jsonl` committed at the score sha cannot be fixed by a child commit, and the run burns. So validate it with `check_labels` BEFORE committing.
- **bkit G-001 also fires on `rm -rf` of a scratchpad path inside a compound command.** Use a fresh `mkdir` instead of clean-and-recreate.

## Next Steps

1. **Rebuild the label package** (the scratchpad copy is ephemeral; it was `…/575e7340-…/scratchpad/label-pkg`, 492M).
   - Source the env first: `source ~/.local/state/h-mad/grok-audit-surface/run-current.env`.
   - Layout: `P=<new scratch dir>`, then `mkdir "$P" "$P/roots" "$P/prompts" "$P/out"`.
   - Copy the findings: `cp "$READING/findings.jsonl" "$P/"`.
   - Write the ledger: `git show $CAL_SHA:docs/03-analysis/probes/grok-audit-surface/calibration/ledger.jsonl > "$P/ledger.jsonl"`.
   - For each d in 1..9:
     - Get the root: `R=$(sed -n 's/.*path=\([^ ]*\).*/\1/p' $RUN/stem/s2-d$d-v1.p1.root.txt)`.
     - Copy it: `rsync -a --exclude='.hmad-report/' --exclude='.h-mad/pass-logs/' --exclude='graft/.cache/' --exclude='*.audit.v1.p[123].md*' --exclude='.tmp/' "$R/" "$P/roots/d$d/"`.
     - Write the redacted prompt: `sed -E 's#/[^ ]*/\.hmad-report/[^ ]*\.report\.md#<REPORT_PATH>#g; s#'"$RUN"'/roots/[^/ ]*#<ROOT>#g' $RUN/stem/s2-d$d-v1/*_p1.txt > "$P/prompts/d$d.prompt.txt"`.
2. **Lock the run state**: `chmod 000 "$RUN" ~/.local/state/h-mad/grok-audit-surface/run-current.env`. Copy anything you still need from the env BEFORE locking.
3. **Write one labeller prompt** to `$P/labeller-prompt.txt`.
   - The rules are spec AC-4.3 verbatim: `HIT:<seed-id>` / `REAL` / `FABRICATED` / `UNDECIDABLE` with a `why`.
   - A `HIT` seed must share the finding's doc prefix.
   - Each id gets exactly one line. The package path is the whole world.
   - Mention no surface, pass, hint or finding id.
4. **Dispatch 9 fresh labellers, one per doc.** Each gets:
   - only its rows of `findings.jsonl`;
   - `roots/dN/`;
   - `prompts/dN.prompt.txt`;
   - the ledger rows whose ids start `dN-` (3 each).

   Output goes to `$P/out/dN.labels.jsonl`. Counts per doc: d1 11, d2 13, d3 15, d4 13, d5 12, d6 16, d7 26, d8 15, d9 9.
5. **Merge the outputs into `$READING/labels.jsonl`** (but only after step 6 unlocks `$RUN`). Then validate in scratch python:
   - Import `check_labels` from the probe.
   - Call it with `findings`, `labels`, and the ledger built as at `:1582`. Build `doc_ids` the way `score` does; read `_score_table` at `:1564` and its caller first.
   - If it refuses with `label:<id>`, send that id back to the same labeller. Do not relabel it yourself: this session has seen 4 HINT ids and the per-pass counts.
6. **Restore permissions**: `chmod 755 "$RUN"; chmod 644 run-current.env`.
   - Copy `labeller-prompt.txt` and the rsync exclusion list into `$RUN/work/` as provenance.
7. **Score commit** (impl-plan §Task 15 step 11 and the calibration-ref precondition at `docs/01-plan/features/grok-audit-surface.impl-plan.md:2960`):
   - Run the precondition.
   - Fetch: `git fetch --no-tags origin +refs/heads/calibration/grok-audit-surface:refs/heads/calibration/grok-audit-surface`.
   - Set `TIP` and confirm it with `ls-remote` (expect `8f8deaf1`).
   - Commit: `python3 "$PROBE" commit-data --repo . --parent "$TIP" --src "$RUN/data" --message "grok-audit-surface score ${RUN##*/}"`.
   - **Ask the operator before the push.** Push without force, then confirm with `ls-remote`. That commit is the score sha. Then Task 16.

## Open / Blocked Items

**This session:**

- **Task 15 step 11.** Status: in progress.
  - `extract` is done; the labels and the score commit are pending.
  - **Machine-local**: the run dir is `~/.local/state/h-mad/grok-audit-surface/run-ab2c85dc2e25-20261024T132452Z/`. It holds `findings.jsonl`, `key.jsonl` and `extract.txt`, and `run-current.env` records `SEED=773509911; LAST_STEP=11-extract`. To continue on another machine, copy the whole `~/.local/state/h-mad/grok-audit-surface/` dir first.
- **Procedure deviation to record in Task 16's measurement doc.** Design rows 122–123 name the per-pass `p<i>.*` files and `report.md` as labeller inputs. The labeller package here is stricter: it gives finding `text`/`quotes` instead of the report, and redacted `p1` prompts.
- **h-mad claim on `grok-audit-surface`.** Claimed this session (session `575e7340-41d5-451c-b5ff-0d210bee2c0d`); released at this closeout.
- **Task list.** Pruned 14 stale or duplicate tasks. #7 (deferred backlog) and #16–#21 remain.

**Carried from `2026-10-25-main__run8-done-authors-test-merged.md`:**

- Next Step 1 (step 11): in progress, as above.
- Next Step 2: diagnose wire-registry `missing=268` under TDD. Open and unchanged.
  - Origin HemaSuite · BrightGold70/hemasuite-document-workbench · session c1e6df26.
  - Repro: in `/Users/kimhawk/orca/workspaces/HemaSuite/hemasuite-document-workbench`, read-only: `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_registry.py verify --base efcaae522e206826dab9a832dee718504f54c416 --rootdir "$PWD" --testpath hemasuite/tests --python "$PWD/.venv/bin/python"`.
  - Control: `test_api.py::test_quit_stops_new_work_preserves_data_and_marks_interrupted_run` collects 7.
  - Hypotheses: (a) parametrized ids, (b) foreign sub-project pins, (c) a collection failure scored as absence.
  - Claim `wire-registry-and-bkit-g001` first (the oracle answered `resume_manual`).
- Next Step 3: operator decision on the Playwright WIRE-PIN representation (`runner` field vs `unverifiable-by-registry`). Example: HemaSuite `document-intake-source-review::Task 6`. Unchanged.
- Next Step 4: bkit G-001 local patch, at `~/.claude/plugins/cache/bkit-marketplace/bkit/2.1.38/lib/control/destructive-detector.js:36-38`, beside `docs/patches/bkit-enh310-quoted-heredoc-body/`. Ask before filing upstream. Unchanged. This session reconfirmed it: the rule fires on `rm -rf` inside a compound command.
- Next Step 5 (Todo #4, skill-candidates): OPEN 32. A full reconcile of the 23 older `yes` rows is still owed. It includes the claim-writer LIVE takeover, the false "released" closeout and the agy-1.4.6 flake. Unchanged.
- Worktree `../skills-gate-authoring` (branch `fix/gate-task-authors-test`, merged in `7373cb1b`): still present. Remove with `git worktree remove ../skills-gate-authoring && git branch -d fix/gate-task-authors-test` once the operator OKs it.
- The codex pin `term_134b0865…` is STALE (no such terminal). Re-pin before any codex dispatch. New this session.
- Run 8 attempts 1 and 2 (`…T115256Z`, `…T120234Z`): evidence; never score them. Unchanged.
- Everything listed under "Carried from `2026-10-24-main__task15-runs4-7-14h-green.md`" in the predecessor (lines 72–107) is unchanged since 2026-10-25. That covers:
  - the calibration tip `8f8deaf1`;
  - run dirs 4–7 as evidence;
  - the 14h and 14i residuals;
  - Policy B;
  - todos #5–#7;
  - the foreign untracked files: never stage them;
  - `.codex/config.toml`: never stage it;
  - the local-only `verify-hmad-*` skills;
  - TLA+ F1–F4;
  - the pstack rule;
  - Tasks 16–17, 5f/5g and Phases 6–7, blocked on step 11;
  - skills defects 1–12;
  - 14d AC.5 and the 14c `status_dir` note;
  - the `implementation_authors` misattribution;
  - the halted run dirs;
  - `.h-mad/phase5-shell-allow` and the root `.venv`;
  - the T19 and T22 residuals;
  - the leaked `hmad_exec_prompt.*` files;
  - the owed measurement-class notes;
  - the old S2 positive-control data;
  - HemaSuite PID 70888;
  - the 7 older `yes` rows and the `:2673` gap;
  - the deferred mutation-harness items;
  - HemaSuite feature/204 and `stash@{0}`;
  - the watch-only items;
  - the meta notes;
  - the 2026-10-02 carry;
  - the 2026-10-23 sender pointer.

## Context for Next Session

**Files touched this session:**
- `~/.local/state/h-mad/grok-audit-surface/run-current.env` (appended `SEED=773509911; LAST_STEP=11-extract`).
- The run's reading dir: `extract.txt`, `findings.jsonl` and `key.jsonl` were created, plus `$RUN/work/extract-stdout.txt`.
- `docs/.bkit-memory.json` (claim taken, then released).

Nothing on `main` changed apart from this handoff.

**Uncommitted changes:** none of mine; only the foreign untracked files.

**To resume (THIS Mac):**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature grok-audit-surface --session-id <id>
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature grok-audit-surface --claim <id>
source ~/.local/state/h-mad/grok-audit-surface/run-current.env; cd /Users/kimhawk/orca/skills
ls "$READING"    # expect extract.txt findings.jsonl key.jsonl resmoke s2 — NO labels.jsonl yet
```

**Related docs:**
- Impl-plan §Task 15 step 11 (`:2953`) and the calibration-ref precondition (`:2960`).
- Spec FR-4 / AC-4.2–4.5 (`docs/01-plan/features/grok-audit-surface.spec.md:229`).
- Plan blinding paragraph (`docs/01-plan/features/grok-audit-surface.plan.md:253`).
- Probe `check_labels` (`docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py:1510`) and the score ledger build (`:1582`).
