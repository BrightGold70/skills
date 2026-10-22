# H-MAD Phase 5d/5e per-task runbook — grok-audit-surface S0c

You run ONE impl-plan Task through RED → GREEN → verify → commit, on branch
`feature/218b-grok-containment` in `/Users/kimhawk/orca/skills`. You are the orchestrator's
delegate: Codex writes all test and production code; you stage, dispatch, VERIFY, and commit.
Never write production `.py`/`.sh` yourself. Never `git push`, never `--force`, never
`git stash` on a clean tree, never `reset --hard`/`checkout --`.

Constants (each Bash call is a fresh shell — re-export every time):
```
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
SP=/private/tmp/claude-501/-Users-kimhawk-orca-skills/37d16870-c23d-4356-895d-ec6c913e3b14/scratchpad
P=/opt/anaconda3/bin/python3.11          # the ONLY interpreter with pytest; pass it ABSOLUTE
SID=37d16870-c23d-4356-895d-ec6c913e3b14
PLAN=docs/01-plan/features/grok-audit-surface.impl-plan.md
SPEC=h-mad/tests/mutation-specs/grok_audit_surface.json   # unless the Task names another spec
```
Read the Task section in `$PLAN` (`## Task N:` up to the next `## Task`). Take from it: test
path(s), the **RED split** (F/P counts, which ids are P = regression guards), the mutation spec
and rows. Pre-flight: `git status --short` must be clean (ignore nothing).

## 1. RED
```
python3 ~/.claude/skills/h-mad/scripts/h_mad_tdd_judge.py implementer --root . --feature grok-audit-surface --record
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_tdd.py --feature grok-audit-surface \
  --task "Task N" --phase red --project-root . --module <slug> --test-path <test file> \
  --python $P --expect-fail F --expect-pass P_ [--guard <nodeid> ...] --agent codex \
  --prompt $SP/tdd/tN_red.txt --out $SP/tdd/tN_red.out --log $SP/tdd/tN_red.log --timeout 1800
hmad-dispatch exec codex $SP/tdd/tN_red.txt --cd . --out $SP/tdd/tN_red.out --log $SP/tdd/tN_red.log --timeout 1800
```
Run the exec with Bash `run_in_background: true` and wait for the notification (do not poll).
`--expect-fail/--expect-pass` must both be given (omit both only for `wiring` shape).
Read `python3 h-mad/scripts/h_mad_extract_verdict.py $SP/tdd/tN_red.out --key STATUS`.
**A `STATUS: BLOCKED` whose only blocker is "could not run pytest" is NOT a failure** — the
Codex sandbox gate sometimes refuses its runs. Ignore its self-report; re-derive yourself:
`$P -m pytest <test file> -q -p no:cacheprovider` → the FAILED set must equal the plan's F ids
exactly, guards pass. Check failure MODES (`grep '^E '`): behavioural assertions, or the
plan-stated cause (e.g. "module absent"). An unexpected pass/fail → STOP, report.
If RED wrote **mutation-spec rows** anchored on code that does not exist yet, save
`git diff -- $SPEC > $SP/tdd/tN_red_spec.patch` and `git restore -- $SPEC` (rows belong at GREEN).
Commit ONLY the test files: `git add <test files> && git commit -m "test(grok-audit-surface): Task N RED — <topic>" ` with the
two trailer lines below.

## 2. GREEN
Same assembler with `--phase green`, no counts, `--mutation-spec $SPEC`, `--timeout 2400`,
files `tN_green.*`. Dispatch in background, wait. Extract STATUS. If BLOCKED, read the blocker:
- interpreter/gate refusal → report it to the orchestrator; do NOT edit `.h-mad/phase5-shell-allow`
  or `.venv` yourself.
- otherwise one re-dispatch (`tN_green2.*`); a third failure → STOP, report `green_unreachable`.
On DONE / DONE_WITH_CONCERNS record the author:
`python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature grok-audit-surface --session-id $SID --append implementation_authors='{"module":"<slug>","agent":"codex"}'`

## 3. Verify (yourself — never trust the report)
a. `git diff` — read the production diff against the Task description; every `# M:` marker the
   Task names present.
b. Tests: the Task's test file(s) all pass; every suite the Task's ACs name passes; each AC's
   literal check (grep counts, byte-identical lines, `--check-anchors` on named specs) re-run.
c. Revert test — NEVER `git stash` (a failed push followed by `pop` applies the FOREIGN `stash@{0}`
   that lives in this repo; it happened once). Instead: copy each production file to `$SP/tdd/`,
   then `git show HEAD:<path> > <path>` (or `rm` for a new untracked file), run, then copy back and
   `cmp` against the saved copy. Old form for reference only: `git stash push -u -q -- <production paths>`; assert revert landed with an
   EXISTENCE/grep check (not `git diff --quiet`); rerun the Task test file → FAILED set must equal
   the RED F set exactly; `git stash pop -q`; re-run → green (import/execute, not grep).
   If the Task modifies a test fixture module that is production-like, include only production paths.
d. Mutation: build a subset spec of ONLY this Task's new rows (rows appended after the previous
   count; rows rewritten in place too) with `root` absolute `/Users/kimhawk/orca/skills/h-mad`
   and `command` narrowed to this Task's test module(s), save to `$SP/mut/tN.json`, run
   `python3 h-mad/scripts/h_mad_mutation_harness.py $SP/mut/tN.json`. Need `MUTATION: ALL_CAUGHT`.
   SURVIVED/REFUSED → one GREEN fix re-dispatch telling Codex the survivor; still failing → STOP.
   Also `--check-anchors` the full spec(s) → `ANCHORS_OK`.
e. agy spec review — ONLY after (d) finished (the harness mutates files while it runs):
   `python3 $SP/stage_review.py N <slug> $SP/tdd/tN_green.out $SP/tdd/tN_rev.txt <changed paths...>`
   then background `hmad-dispatch exec agy $SP/tdd/tN_rev.txt --cd . --out $SP/tdd/tN_rev.out --log $SP/tdd/tN_rev.log --timeout 900`.
   Read `h_mad_extract_verdict.py ... --key VERDICT` and
   `h_mad_review_evidence.py $SP/tdd/tN_rev.log --project-root .` (need `EVIDENCE: PASS`, code>0).
   `git status --short` must show no agy edits. DRIFT → check each finding's premise against the
   code; real drift → one GREEN fix re-dispatch; false premise → note it and proceed.
   Record: `--append review_independence='{"leg":"5e-review","module":"<slug>","reviewer":"agy","implementer":"codex","independent":true}'`

## 4. Commit
`git add <exact changed paths>` (never `-A`; never `.venv`, never `.done` markers) and
`git commit -m "feat(grok-audit-surface): Task N — <summary>"` ending with:
```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01BrKtQCV6B1MBMVQLoPEbuP
```

### Revert rule when GREEN churned existing tests
If GREEN legitimately edited existing tests (interface churn the Task names), the revert F set
will be a superset of RED's F set. Then require: RED F ⊆ revert F, and classify every extra
failure's reason (e.g. `grep -oE 'unrecognized arguments: [^ ]+'`) — each must be the churned
interface. Any unexplained extra → STOP. Also read GREEN's test-file diff: assertions may be
retargeted to the new contract, never deleted or loosened.

## 5. Report — WRITE IT TO A FILE
Your final chat message is truncated in transit (~4 KB, tail cut). Write the full report to
`$SP/tdd/tN_REPORT.md` FIRST, then make your final message just its first line plus the path.
First line: `TASK N: DONE red=<sha> green=<sha>` or `TASK N: STOPPED reason=<r>`.
Then: RED split observed; GREEN status; tests run + counts; revert result; mutation token;
anchors token; agy verdict + EVIDENCE line; any concern, deviation, or Codex blocker verbatim.
