# Handoff — Waves 3 and 4a shipped: dogfood run + fanout integrity

**Date:** 2026-07-23
**Branch:** main
**Project:** BrightGold70/skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Two full `/h-mad` runs shipped back to back. **Wave 3** (`4111297`, `preflight-read-enforcement`)
mechanized the Wave-2 carry — `env` now writes a fingerprinted receipt and `send` refuses without a
fresh matching one — and its dogfood run closed G-b, G-d **and** G-a, since the Phase-5 worktree
fanout ran live for the first time. **Wave 4a** (`ab3657e`, `fanout-integrity-and-defects`) then
fixed the four instrument defects that run exposed or carried: J15, J14, J8, J10. Suite went
530 → 592 across both, zero regressions, both `READY_TO_MERGE`, both on `main` and pushed. Wave 4b
(the candidates batch) is the remaining work and can now be fanned out safely.

## Key Learnings

- **Guarding the irreversible step beats instructing the actor.** J15's filed fix direction was
  "tell the fanout worker to commit". Both Wave-3 workers had already been told to self-review and
  neither committed. Putting the guard on `worktree-rm` means the work survives whether or not
  anything is read — the same reasoning that made Wave 3's send-refusal work where Wave 2's mandated
  read did not.
- **A green suite hid two unenforced guards, and only mutation found them.** Replacing the
  `--prompt-file` gate with `true` broke *nothing*: `run()` strips `HMAD_ORCA_*`, so `_coordinator()`
  failed and `task-create` bailed before calling `orca`, leaving the capture clean for the wrong
  reason. My own `--base` doc test passed with the guidance deleted, because both files already
  carried `--base <ref>` and "feature branch" in unrelated prose. Assert the *literal* instruction,
  and disable every guard once to see if anything notices.
- **Replaying against history caught a bug 14 synthetic cases missed.** A prefix-based concern label
  rejected the real form `Working-tree concern:` — discarding a report that *had* stated its concern.
  The same replay measured the true rate: **7 of 13** historical `DONE_WITH_CONCERNS` reports name no
  concern, so J10 is the majority case, not the one-off it was filed as.
- **Agent identity is not missing, it is in a different call (J16).** `orca worktree ps` returns
  `agents[].agentType` keyed by `paneKey` = `<tabId>:<leafId>`, and `terminal list` returns
  `.tabId`/`.leafId`. Joining them resolved two panes that both reported `title: "Codex - skills
  repo"` with empty previews and reset buffers — the exact ambiguity H5 documents, unsolvable by
  every existing heuristic. This may make orca#9870 moot.
- **The documented ~49 KB reviewer cliff did not reproduce, three times.** Prompts of 52,997 B,
  53,058 B and **58,536 B** were all answered normally via file indirection. A design audit was
  trimmed on the strength of a number that is now costing work (J13).
- **`h_mad_telemetry.py` cannot do what `SKILL.md` orders it to (J11).** The prose says twice to
  "record the substrate + agent mapping" via it; the script takes no such argument and the row schema
  has no such field. No run has ever recorded its substrate.
- **`ASSEMBLE: PASS` is returned for prompts the assembler predicts will fail (J12)** — a correct
  warning beside a passing token that the mandated read consumes. Same defect class Wave 2 fixed, one
  signal over.
- **Suppressing stderr on an Orca call turns a loud error into a wrong conclusion.** `orca terminal
  read` takes `--limit`, not `--lines`; with `2>/dev/null` the `invalid_argument` envelope rendered as
  an empty pane and briefly read as "the agent is gone".
- **Fanout teardown must pass `--base <feature-branch>`.** The default base resolves to `main`, so a
  module worktree branched from a feature branch reports every feature commit as unmerged — measured
  at 7 ahead of `main` vs 1 ahead of its real base. A guard that always refuses trains the operator to
  reach for `--force`, the exact reflex J15 exists to prevent.

## Next Steps

1. **Try the J16 identity join before Wave 5 waits any longer.** Add a `worktree ps`-based step to
   `_orca_find` ahead of the title/preview heuristics, joining `agents[].paneKey` to
   `terminals[].tabId + ":" + leafId`, matching on `agentType` (note: `antigravity`, not `agy`).
   See `docs/skill-monitoring.md` §J16. If it holds, report upstream on orca#9870.
2. **Run Wave 4b — the candidates batch, via fanout.** Two `invariants.base.md` discipline rules,
   `file-issue-then-fix-under-TDD` (recurrence 14), the staged-prompt repair sweep, the stub-harness
   probe, and two `SKILL.md` prose notes. See `docs/01-plan/h-mad-remediation-sequence.md` §Wave 4.
   **Pass `--base <feature-branch>` on every `worktree-rm`.**
3. **Fix J12 — fold prompt size into the `ASSEMBLE:` verdict** rather than a warning beside it:
   either `ASSEMBLE: HALT <phase>:oversize` or a distinct `PASS_OVERSIZE` the mandated read must
   branch on. `~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py`.
4. **Re-measure or delete the reviewer cliff numbers** in
   `~/.claude/skills/h-mad/references/agent-substrate.md` — 53,066 B is recorded as silent and three
   larger prompts answered fine. Distinguish TUI paste from agent-side file reads while doing it (J13).
5. **Fix J11** — either give `h_mad_telemetry.py` a substrate/agents field and the arguments to write
   it, or delete the instruction from both places in `SKILL.md`.
6. **Delete the 10 merged feature branches** — `git branch -d` for `feature/185`…`feature/193` plus
   `BrightGold70/auto-hmad-e2e-auto-run-1-20260722T0258`. All merged into `main`.

## Open / Blocked Items

- **Wave 4b candidates batch** — status: not started. The only remaining Wave-4 work.
- **J11 (unexecutable telemetry instruction)** — status: filed, unfixed.
- **J12 (`ASSEMBLE: PASS` on a doomed prompt)** — status: filed, unfixed. 🟡
- **J13 (oversize remedy does not reduce size when the design dominates)** — status: filed, unfixed.
- **J16 (identity via `worktree ps` paneKey join)** — status: filed as an **opportunity**, unattempted.
  Blocks nothing, but Wave 5 is idling on the problem it may solve.
- **J1 (`launch` mis-captures the handle)** — status: filed, unfixed. Worked around by content- and
  paneKey-identification.
- **J9 (flaky `test_alive_cmux_true`)** — status: filed, unfixed. Probes the real `cmux` binary.
- **`*) shift ;;` drops unrecognised flags at 11 sites in `hmad-dispatch.sh`** — status: deliberately
  declined in Wave 4a as pre-existing and out of scope. If it changes, change all 11 as its own feature.
- **FR-2 under-protects where no `origin/HEAD`/`main`/`master` resolves** — the unmerged check is
  skipped rather than failed, by design (AC-2.4). Stated, not hidden.
- **Pre-existing Pyright warning** on `_remove_stray_pin_file` (`atexit`-registered, false positive).
  Present on `main` before both waves.
- **[stablyai/orca#9870](https://github.com/stablyai/orca/issues/9870)** — status: blocked upstream,
  **but see J16 first.**

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` — receipt lifecycle, preflight enforcement, conflict guard,
  `worktree-rm` guards, `worktree-create` task-id
- `h-mad/scripts/h_mad_state_write.py` — `started_ts` default (J8)
- `h-mad/scripts/h_mad_extract_verdict.py` — `concern_stated` + `main()` check (J10)
- `h-mad/tests/test_hmad_dispatch.py`, `test_h_mad_state_write.py`,
  `test_h_mad_extract_verdict.py`, `test_h_mad_preflight_docs.py`
- `h-mad/SKILL.md`, `h-mad/references/agent-substrate.md`,
  `h-mad/references/orchestration-mode.md`, `h-mad/references/codex-implementer-prompt.md`
- `docs/skill-monitoring.md` — J11–J16
- `docs/01-plan/h-mad-remediation-sequence.md` — Waves 3 and 4a marked shipped
- `docs/archive/2026-07/preflight-read-enforcement/` and
  `docs/archive/2026-07/fanout-integrity-and-defects/` — 26 archived artifacts

**Commits (all pushed to `origin/main`):**
- Wave 3: `1aaf3c4` baseline · `e2df2a6`/`94e2e05` fanout modules · `f4c98e8`/`98bde9d` merges ·
  `42af09d` enforcement · `20cac8b` docs · `bd20c5e` AC gaps · `953a055` report · `4111297` merge
- Wave 4a: `8c99e9e` baseline · `c73c268` J15 · `77e8c86` J14 · `a9d682b` J8 · `b7f6bc4` J10 ·
  `b4e5aa6` docs · `dfc1339` report · `ab3657e` merge
- Monitoring/sequence: `81e4c1d`, `2a6c9f0`, `57f7d46`, `b71cc39`, `8605249`

**Uncommitted changes:** none — clean, in sync with `origin/main` at `8605249`.

**Agent panes** — handles rotated **twice** during this session and both rotations were caught by the
Wave-3 receipt (`PREFLIGHT: FAIL stale=agy`, then `stale=codex,agy`). Do not reuse these; re-identify
via the J16 paneKey join or by content:
- codex `term_294ce89e…` · agy `term_0a2de455…` (as of session end)

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git pull --ff-only
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
hmad-dispatch env                       # assert PREFLIGHT: PASS — send now REFUSES without it
/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q    # expect 592 passed
```

**Related docs:**
- `docs/01-plan/h-mad-remediation-sequence.md` — Waves 1–3 + 4a shipped; 4b and 5 remain
- `docs/skill-monitoring.md` — J1–J16; J6 **disproven**, J7/J8/J10/J14/J15 **resolved**
- `docs/archive/2026-07/preflight-read-enforcement/preflight-read-enforcement.report.md`
- `docs/archive/2026-07/fanout-integrity-and-defects/fanout-integrity-and-defects.report.md`

## Version History
- v1.0: Waves 3 + 4a closeout.
