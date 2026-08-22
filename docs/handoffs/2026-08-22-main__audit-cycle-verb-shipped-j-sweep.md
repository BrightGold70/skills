# Handoff — audit-cycle-verb shipped end-to-end; J registry swept

**Date:** 2026-08-22
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Took `audit-cycle-verb` from mid-Phase-6 to **merged on main** (`02da79f`, `--no-ff`, 36 commits):
6a-prime `READY_TO_MERGE`, gap analysis 100% (10/10 FRs, 57/57 ACs), Phase 7 report + archive,
claim released. Then shipped three follow-ups — an 80% run-context cap for the h-mad skill, the J40
evidence gate, and coverage for the J18 pin-file guard — and classified all 40 entries in
`docs/skill-monitoring.md`, which now has **exactly one open item (J30)**. Suite 1601/0, main 0/0,
tree clean, nothing in flight.

**The through-line: six defects this session were found by steps that RUN something, and none by a
step that reads.** Phase 7 alone produced two that no earlier gate could see.

## Key Learnings

- **Phase 7 is a detector, not a formality.** It runs the reporter against real filenames (J42: the
  verb's per-pass `.p<i>` artifacts broke `h_mad_cycle_counts.py`, reporting `audit_cycles=0` for a
  feature with plan v14 / design v24 / impl-plan v10) and it moves the files (J43: archiving took a
  real-artifact corpus 8 → 0, and pytest answers an empty `parametrize` with `SKIPPED`, one `s`
  among 1580 dots). Both live outside any diff, so 6a-prime was structurally blind to them.
- **A silent zero is a claim about the WORK; an error is a claim about the TOOL.** J42's `0` read as
  "no audits were run". That is why it survived — nothing looked broken.
- **`extract_verdict` closes silence; nothing closed fluency.** J40: a 6a-prime review made one tool
  call, it errored, `result.status=ERROR`, and it returned `ASSESSMENT: READY_TO_MERGE` in 1510
  confident bytes about files it never opened. rc, the extractor and the Phase-7 gate all took it.
- **A correct `--cd` is not sufficient for agy.** `init.cwd` was the repo root while repo-relative
  citations resolved against `~/.gemini/antigravity-cli/scratch/`. Cite absolute paths.
- **Do not gate on `result.status`.** `hmad-dispatch` ignores it deliberately — one denied tool call
  yields `ERROR` beside a complete answer. The J40 gate counts successful tool calls instead, and
  **knows no tool names**: my first probe hardcoded `view_file|grep_search` and returned a false zero
  when agy switched to `run_command`.
- **A carried claim decays into a fact.** "Real concurrency untested by every lane" (J41) survived
  three handoffs, restated each time, and dissolved in ten minutes of probing — the suite *does*
  fork, and two of its four shapes already had direct tests. J18's "verified by re-introducing the
  leak" was likewise a manual one-off that nothing carried forward.
- **Falsify the claim the finding makes, not the story it tells.** The `--passes` finding arrived
  with a fabricated symptom (a bash error that does not occur). The symptom falsified cleanly and I
  let it discharge the whole finding — but spec AC-3.1 genuinely was unimplemented (J38).
- **A fixture's default can masquerade as the program's.** `dispatch_args(..., passes="2")` emitted
  `--passes` into all 44 call sites, so 1560 tests could not see that the verb had no default.
- **A guard's younger sibling got tested and the original did not** (J18). A session-scoped autouse
  fixture that nothing tests is one deletion from gone, and its absence is silent by construction.
- **`grep -c` exits 1 on no match**, which reads as a clean zero if the exit code is ignored — that,
  plus 9-of-40 entries carrying a `Status:` line, is how a census reported J18 open when its own
  body said "Fixed".
- **zsh does not word-split unquoted expansions** — bit me three times in one session (`set -- $spec`
  in a loop, `$PROD` as a git pathspec, and a `|` in a grep pattern read as alternation).
- **Documentation can pollute the thing it documents.** My status legend used `` `WORD` `` as a
  placeholder (matched the status regex) and wrote `**J31–J33**` in bold (manufactured a phantom
  J-id: `40 of 41`). Both caught by re-running my own census.

## Next Steps

1. **J30 — the only open registry item.** `exec agy` at ~260 KB honours neither transport and writes
   a real report at a path of its own choosing, so the artifact is unfindable rather than absent.
   Reproduced 5/5. See `docs/skill-monitoring.md` (search `**J30`).
2. **Live-fire the advisor gate**, still owed from a prior session:
   `HMAD_CONTEXT_WINDOW=1000 claude` then one `advisor()` call — it MUST be denied. A gate that
   stands down silently is indistinguishable from one that approves.
3. **Live-fire the new run-context cap the same way** — `h_mad_context_budget.py --mode run` is
   documented as a phase-boundary obligation but has never fired in anger. Shrink the window so
   `CTXBUDGET: HALT mode=run` trips and confirm the halt route is actually taken.
4. **Delete merged local branches** — `feature/audit-cycle-verb`, `fix/j40-review-evidence-gate`,
   `fix/j18-pin-guard-coverage`, `chore/j-status-sweep` are all merged to main; three older
   `feature/21x-*` branches predate this session and want checking before removal.

## Open / Blocked Items

- **J30 — `exec agy` drops its output contract at ~260 KB** — status: open, `MONITORING`. The only
  unclosed entry of 40. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`.
- **Advisor-gate and run-cap live-fire** — status: deferred, both need a fresh session with a shrunk
  `HMAD_CONTEXT_WINDOW`; neither can be verified from the session that wired them, because hooks are
  snapshotted at session start.
- **`test_verb_no_self_invocation` has no mutation coverage** — status: accepted, not fixed. The
  natural mutation recurses without bound and the assertion may be structurally immune. Recorded
  rather than implied clean.
- **`PREFLIGHT: FAIL unresolved=codex,agy`** — status: known, cosmetic. Zero candidate panes in this
  worktree; `exec` is pane-independent and was proven live all session. Do NOT launch panes to green
  it.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_audit_cycle.py` (gate exit-code guard), `h-mad/scripts/hmad-dispatch.sh`
  (`--passes` default), `h-mad/scripts/h_mad_cycle_counts.py` (per-pass regex)
- `h-mad/scripts/h_mad_context_budget.py` (`--mode run`), `h-mad/scripts/h_mad_review_evidence.py` (new)
- `h-mad/tests/conftest.py` (pin-file mutation anchor), `h-mad/tests/test_h_mad_pin_file_guard.py` (new),
  `h-mad/tests/test_h_mad_review_evidence.py` (new), plus audit-cycle/context-budget/cycle-count tests
- `h-mad/SKILL.md`, `h-mad/references/failure-recovery.md`,
  `h-mad/references/agy-architectural-reviewer-prompt.md`
- `docs/skill-monitoring.md` (J36–J43 + the 40-entry status sweep and lifecycle legend)
- `docs/archive/2026-08/audit-cycle-verb/` (105 archived artifacts, incl. report + analysis)

**Uncommitted changes:** none. `main` level with `origin/main` (0/0).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q     # expect 1601 passed
python3 h-mad/scripts/h_mad_context_budget.py --mode run   # the new phase-boundary check
```

**Interpreter:** bare `python3` is 3.14 with **no pytest** — always `/opt/anaconda3/bin/python3.11`.
Bare `pytest` from the repo root collects the sibling `hematology-paper-writer/` and dies with
pre-existing collection errors; always scope to `h-mad/tests`.

**Related docs:**
- `docs/archive/2026-08/audit-cycle-verb/audit-cycle-verb.report.md` — the Phase 7 report
- `docs/skill-monitoring.md` — 40 entries, all classified; header documents the lifecycle vocabulary
  and why the old census lied
