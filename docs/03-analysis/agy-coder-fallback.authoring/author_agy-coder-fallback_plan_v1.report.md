PLAN-AUTHOR: DONE version=v1.0 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.plan.md lines=377 sha256=a212da32f834fac266d133e2027d8adaf669385ae374925930be315a0ba96b5e

# plan-author report — agy-coder-fallback plan v1.0

The plan is new and untracked, and I did not commit it. I wrote no probe files. The one scratch
script, `mrows.py`, is in the session scratchpad, outside the repository.

## What I wrote
I followed the inline Phase-3 template: Executive Summary through Version History. I added two
sections of my own: "Design obligations" (DO-1..DO-6, under Architecture Considerations) and
"Owed by other documents".

I carried all five orchestrator items:
1. **D-9 and D-11** are in Requirements and G6, for every implementer (`codex|agy|grok|claude`).
   One Success Criterion forbids restating the trigger as agy-only on any surface this feature
   edits.
2. **The D-10 per-clone prerequisite** is in Convention Prerequisites, with the check-ignore
   evidence re-run.
3. **The TDD-STATE line shape and the read-only allowlist** are design obligations (DO-1, DO-2).
   They are not settled in the plan. Re-anchoring the mutation rows is R-1, backed by census M-3,
   and the stage-3 work requires it.
4. **SKILL.md** text saying the `review_independence` entry is appended for every implementer is in
   stage 7 and G6.
5. **SessionStart**: I re-checked it against agy 1.3.6 and filed it as R-9 (details below).

## Measurements re-run (all at 17d73037)
- `rtk proxy /opt/anaconda3/bin/python3 -m pytest h-mad/tests --collect-only -q -p no:cacheprovider | tail -1`
  → **6042 tests collected**. The bare `python3` (Homebrew 3.15) has no pytest. An rtk-rewritten
  run printed "No tests collected". This number drifts by construction, so the plan does not use it
  as the floor; re-measure at 5c.
- Mutation rows per file (M-2; the one-liner is in the plan). Rows / specs:
  - `tdd-gate.sh` 56 / 5
  - `tdd_judge.py` 36 / 8
  - `codex-tdd-gate.py` 62 / 5
  - `assemble_tdd.py` 60 / 6
  - `phase7_preconditions.py` 12 / 2
  - `hook_wiring.py` 10 / 1
- Rows over the state-line contract (M-3; the regex is over `find` and `replace`) → **8 rows,
  3 specs**. On a `find`-only pass the matching set was different (7 rows, some from other
  patterns). The `replace` side matters: the grok-codex-fallback probe shows rows that embed the
  state line in `replace`.
- Codex-gate rows in the `_safe_shell_command` AST call closure (M-4) → **10 functions, 19 rows**
  (17 in `codex_gate_judge_wiring`, 2 in `assemble_tdd_mutation_rows`), and 0 `find`-not-found.
  `_shell_allowance` lies outside the closure.
- `git ls-files -z h-mad | xargs -0 grep -l 'TDD-STATE: active'` → **6 files**. `grep -o` counted
  8 occurrences.
- Test-side files naming the prompt → **15 files**. My first count read 14 by hand; I chased the
  gap and it was a miscount. The spec's figure of 20 h-mad files reproduced.
- `red_wrong_reason` (excluding docs/archive) → **4 files**.
- `JUDGE_BUDGET_S` = 40.0. The agy hook default timeout is 30.
- `SessionStart`: **3 matching lines** in hooks.md, and **2 lines** in agy-runtime.md.
- `grep -rn 'no .SessionStart' h-mad/tests` → no hits.
- `.git/info/exclude` → `/.agents/skills/`. `git check-ignore -v .agents/hooks.json` → no output
  (rc 1).
- `~/.gemini/config/hooks.json`: `orca-status` registers `PreToolUse` with matcher `*`, and the
  script prints `{"decision":"ask"}` for `PreToolUse`.
- Precheck: `PRECHECK: PASS issues=0`. `DOC-SHAPE: PASS`. `VERSION-HISTORY: OK version=v1.0`.

## Where the tree contradicted the spec
- **AC-3.2 "unmodified" vs FR-3 (DO-1a, R-4).** `test_h_mad_tdd_gate_judge.py` `_tree_b` and
  `test_h_mad_tdd_gate_fallback_agent.py` `PREFIX` stub old-shape `TDD-STATE` lines.
  `test_h_mad_tdd_judge.py` `ACTIVE_RE` is `$`-anchored, so any appended field breaks it.
- **FR-7 "appends ... with h_mad_state_write.py".** The writer has no append. `--set` replaces the
  whole value (DO-3).
- **FR-6 "mutation rows stay green".** That holds only if the 19+ rows are re-pointed to the shared
  module (R-3).
- **FR-9 / AC-9.1** miss the `failure-recovery.md` recovery row for `step5d:red_wrong_reason`. That
  row is pinned by `test_h_mad_wiring_task_shape_docs.py`.
- **FR-1 / FR-10** miss the `fallback_agent` descriptions in `h_mad_state_schema.json` and in
  `state-schema.md`. Both say "when Codex is out", which is false after FR-3.
- **The SessionStart claim** is on two `agy-runtime.md` surfaces: §Hooks and the
  Construct-mapping `hook-event` row. The spec names one.

## New risks the spec did not name
- **R-2.** `~/.gemini/config/skills/h-mad` is a symlink to the main checkout. In a Phase-5 worktree,
  FR-5's check therefore reads UNWIRED, and FR-8 cannot run before merge (DO-6).
- **R-6 / DO-4.** The bundled state validator ignores unknown keywords (`format`, `oneOf`, …).
  AC-1.1 must run on both validator paths.
- **R-7.** `exec agy` runs with `--dangerously-skip-permissions`. hooks.md does not say whether a
  deny still binds under it, and a sibling hook's `overwrite` can rewrite args after this gate has
  judged them.

## Owed by other documents (verbatim targets)
- **Spec:**
  - AC-3.2: add an exception for stub-line fixtures, or the design keeps old stubs passing.
  - FR-7: say how an entry is appended.
  - FR-6: change "rows stay green" to "rows re-pointed".
  - FR-9 / AC-9.1: add the `failure-recovery.md` row.
  - FR-1 / FR-10: add the `fallback_agent` description surfaces.
  - §Owed: name the second SessionStart surface.
- **Design:** DO-1..DO-6.

## Advisories kept deliberately
- PATH advisories for `h-mad/hooks/h-mad-agy-tdd-gate.py` and `.agents/hooks.json`: both are new
  files.
- `COUNT: L328 states 3 files beside a list of 1`: a false positive. "FR-3 files" was parsed as a
  count.

## Open questions (no advisor)
- Should FR-8 run after the merge, or through a worktree override? That is a design choice (DO-6),
  and it may need the operator.
