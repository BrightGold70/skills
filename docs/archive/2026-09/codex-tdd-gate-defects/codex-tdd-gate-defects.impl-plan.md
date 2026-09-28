# Implementation Plan: codex-tdd-gate-defects

> Source: docs/02-design/features/codex-tdd-gate-defects.design.md (v1.3, binding, including its
> §"Supersedes the plan or the spec on" rows DD-1…DD-13 and the D13 rebase contract),
> docs/01-plan/features/codex-tdd-gate-defects.spec.md (v1.4, 49 ACs, binding),
> docs/01-plan/features/codex-tdd-gate-defects.plan.md (v1.4: step P0, V-0, V-1r, §"Connection
> enforcement" W1–W6, §"Regression census", §"Success Criteria" stay binding)
> Branch target: `feature/codex-tdd-gate-defects` (a git worktree; plan §"Convention Prerequisites")
> 5c baseline: branch `feature/codex-tdd-gate-defects`, worktree `/Users/kimhawk/orca/skills-codex-tdd-gate-defects`, forked from main `a35707b8` (impl-plan v1.2 + delta review v1.2)

## Executive Summary

Twelve tasks, each counted once. Task 0 is the 5c gate: it checks that the orchestrator's step P0
landed, derives `BASE_SHA`, takes the baseline readings and ships the top-level-statement diff
probe. Tasks 1 and 2 extend the two shared parsers in place (`_suite_summary`, `_parse_tasks`).
Tasks 3, 4 and 5 build the judge: Task 3 lands the whole module with its two callee connections in
their pre-wire form, Task 4 wires W4 (`score` → `_suite_summary`) and Task 5 wires W3
(`resolve` → `_parse_tasks`). Task 6 rewires the Codex gate (W1, W5a) and Task 7 adds its venv
shell-policy branch. Task 8 rewrites the Claude gate (W2, W5b, W6) in the form V-0 chose. Task 9
lands the documentation, Task 10 authors and scores the 98 mutation rows in eight specs, and Task
11 is the 5g gate. 1 + 2 + 3 + 2 + 1 + 1 + 1 + 1 = 12. Four tasks are `wiring` (4, 5, 6, 8) and
carry seven wires between them. Task 8 follows design v1.3 §D9 (the root-relative
directory-exemption subject, `RAW_TARGET`, the 126-cell DD-7 differential) and waits only on its
FR-0 precondition, a conclusive V-0; no task waits on a design delta.

## Deviations from design v1.3

The design is binding. Each item is an addition or a precision the design leaves open, with its
evidence. An auditor reading both documents follows this section where they differ.

1. **One shared test-support module, `h-mad/tests/tdd_gate_support.py` (new, not collected:
   `pytest.ini` holds only `testpaths = h-mad/tests handoff/tests handoff/scripts` and the default
   `test_*.py` file pattern, read at `f6b258f0`).** It holds `hermetic_env` (Convention 3), the
   fixture builders every judge and gate test shares, the shell-policy corpus builder and the
   form reader `decision`. It is not appended to `h-mad/tests/conftest.py`, because
   `multi-host-runtime`'s impl-plan appends its own `hermetic_env` there (its Deviation 1) and the
   two features would then collide textually in one file. Tests import it the way
   `test_docsections.py` imports `docsections` (`from docsections import …`, read at `f6b258f0`;
   `h-mad/tests/` has no `__init__.py`). **It is test code, and every addition to it lands in the
   RED commit of the task that adds it** (Tasks 1, 3, 7 and 8 list it on their Test file line), so
   each RED split below counts the support code as present and no test module fails collection
   on a missing helper. Both gates exempt the file: the Claude gate's `*/tests/*` and the Codex
   gate's `_is_production_python` (`"tests"` among the path parts, read at `a1478ad3`). Residual:
   each later addition must be re-checked against its own task's RED split.
2. **W3 and W4 are staged.** The judge is the caller of both wires and does not exist before this
   feature, so a W3/W4 pin written against a missing judge would go RED on `ModuleNotFoundError`,
   which 5d refuses (`step5d:red_wrong_reason`). Task 3 therefore lands the two call-site lines in
   their pre-wire form, which is byte for byte the design's own remove mutants
   (`_parse_tasks(text)` → `[]`, `_suite_summary(…)` → `None`, design §"Test Strategy", W3/W4
   table). Tasks 4 and 5 each change exactly that line (plus the import), so each wiring task's RED
   state is its wire-scoped revert and its pin fails on the caller's verdict.
3. **`resolve` gains a keyword `deadline: float`.** Design §"API / Interface Changes" gives
   `resolve(root, target, records) -> Resolution`, while D3 step 6 runs the name map through
   `_run_bounded(…, deadline)`. The deadline must reach `resolve`, so it is a keyword argument.
   `Resolution`'s fields, which the design leaves unstated, are fixed in Task 3.
4. **The `_suite_summary` grammar rows are tested in `h-mad/tests/test_h_mad_audit_suite_gate.py`
   (Task 1), not in the judge module.** Design §"Test Plan" lists "the D7 grammar rows" under the
   judge module, but the function is the audit gate's, AC-4.7 is the audit gate's, and Task 1
   precedes the judge. The judge's classifier rows stay in the judge module (Task 4).
5. **Parser-level `_parse_tasks` rows live in a new module, `h-mad/tests/test_h_mad_parse_tasks_paths.py`
   (Task 2).** Resolution-level AC-2.2 and AC-2.3 rows stay in the judge module (Task 5), as the
   design places them. Design Implementation Order step 3 tests AC-2.2 and AC-2.3 with the parser,
   so both levels exist.
6. **Mutation rows beyond the design's table**, each named by the guard it proves:
   - S6 (the `failed` exact-category branch), S7A and S7B (`error` and `errors`, each alone): the
     design mutates the exact-category rule as one row, but the rule is three branches;
   - V1's killing fixture `venv-out-bin-back-in`: design §D12's rows cannot isolate conjunct 1,
     because a `.venv` symlinked out of the root also puts `.venv/bin` out, so conjunct 2 still
     denies and a V1 mutant survives every D12 row. The new fixture points `.venv` at an outside
     directory that holds a regular `pyvenv.cfg` and whose `bin` is a symlink back inside the
     root. The regular `pyvenv.cfg` is load-bearing (v1.2, teammate impl-plan audit c2 should 2):
     conjunct 3 reads `os.lstat(<root>/…/.venv/pyvenv.cfg)`, which follows the `.venv` symlink,
     so without it the V1 mutant still returns `False` and survives. Executed on a scratch copy of
     the three-conjunct literal (deleted) at `c93da638`: outside directory holding only the `bin`
     symlink → unmutated `False`, V1 mutant `False`; the same plus a regular `pyvenv.cfg` →
     unmutated `False`, V1 mutant `True`;
   - G6 (the Codex shell branch's containment call) and H3 (DD-2's revert, re-adding the no-`jq`
     allow): plan §"Spec v1.3 ACs: where each is tested" leaves AC-3.6 and AC-6.12 mutation specs
     to the impl-plan;
   - H1B and H1C (the top-level `file_path` and `path` branches of the stdin reader): spec AC-8.1
     names only the `tool_input` branch, and invariant §"Test discrimination" asks for each
     alternation branch alone;
   - v1.1, one row per new test that passes at RED (invariant §"Test discrimination": a guard
     never seen failing is not trusted), listed in Task 10 §"Initially-green guards": S8, S9, S10,
     S11, S12, E1, P1, P1B, P2, K3B, K5, G6B, G7, G8, H15, W5BF2, W5BF3 and D1;
   - v1.1, rows for guards the revision adds: R5 (the name map reads stdout only), H16 and H17
     (the one-line check keeps trailing newlines), C2G and C3G (spec AC-8.1 scores the
     unreadable-chain refusal and the every-record escape on a named AC test, so C2's and C3's
     mutants are re-scored on the Claude gate's AC-6.9 and AC-6.10 tests, as H14 already is);
   - v1.2, one row per initially-green guard that v1.1 left without one (codex impl-plan audit c2
     must 3): S8B (`quoted-assert`), G6C (`[escaping-venv]`, until then "reasoned"), G9
     (`[usr-bin-python3-control]`), G10 (`[doubled-path]`) and G11 (`[script-outside-scripts]`),
     each killed on a scratch copy (Task 10 §"Initially-green guards");
   - v1.2, rows for the design v1.3 directory-exemption subject (Deviation 16): H15B (the
     `*/fixtures/*` alternative alone), H18 and H18B (root membership, and its quoting), H19 (the
     root-relative subject) and H20A and H20B (each spelling of the outside-root conjunction
     alone).
7. **One design mutant is not authored: `_absent_at`'s `[ -x "$D" ]` → true.** It is equivalent on
   every reachable input, so it would SURVIVE by construction. Every `D` the fast path tests was
   entered by `cd` (`d=$(cd "$d" && pwd -P)`, and `ROOT_ABS` likewise), which needs search
   permission on `D` and on each of its ancestors, so `[ -x "$D" ]` is true for every `D` the walk
   reaches. The line stays in the gate as the design states it; only the mutation row is dropped.
   Reported as a contradiction, not silently narrowed. `[ -x "$D/docs" ]` is falsifiable
   (`docs` under a searchable `D`) and keeps its row, H10.
8. **The two old-versus-new differentials are split into a stable test and a probe.** A committed
   test cannot name `BASE_SHA` after the merge (at `main` the "old" gate is the new one), so each
   test pins the new gate's verdict table, and a committed probe computes the softened and
   tightened sets against `BASE_SHA` and publishes them (Tasks 7 and 8). Both read one corpus
   builder in `tdd_gate_support.py`.
9. **Each judge-started child reads stdin from `/dev/null`.** `_run_bounded` passes
   `stdin=subprocess.DEVNULL`, so a pytest child cannot consume the gate's own stdin. The design
   does not state the child's stdin.
10. **The name-map script path is a module attribute, `NAME_MAP`.** Design §"Test Plan" points
    "the module's name-map script path" at a sleeper script; the attribute is that seam.
11. **The Claude gate captures each verb's output with an `rc=` sentinel** (v1.1, codex impl-plan
    audit c1). Design D9 steps 8 and 10 give `SOUT=$(…) || SRC=$?` and `JOUT=$(…) || JRC=$?`, and
    the same steps refuse "zero lines, more than one line". Command substitution strips every
    trailing newline, so a valid line followed by a blank one reads as one line and that rule
    cannot fire. Task 8 appends `; printf 'rc=%s' "$?"` inside the substitution, splits the rc off,
    strips exactly one trailing newline, and refuses an empty value or one that still holds a
    newline. Executed under `/bin/bash` 3.2.57 with `set -euo pipefail` (a scratch script, deleted):
    `ALLOW\n` → one line, rc 0; `ALLOW\n\n` → refused; `ALLOW` (no newline) → one line; `` (empty)
    and `\n` → refused; `A\nB\n` → refused; `ALLOW\n` then exit 1 → one line, rc 1 (the ALLOW-rc-1
    rule still refuses it); `x rc=5\n` then exit 3 → line `x rc=5`, rc 3; a failing command → rc 1,
    empty, refused; the script ran past every case (errexit does not fire inside the
    substitution). The design's rule is kept; only its capture literal changes. Rows H16 and H17.
12. **`_run_bounded` returns stdout and stderr separately** (v1.1, codex impl-plan audit c1).
    Design D3 step 6 reads the name map's **stdout** alone ("A non-empty stdout resolves against
    `root`"); a combined stream would turn a stderr-only diagnostic into a candidate and a
    `test-missing` verdict. A candidate run is scored on `out + "\n" + err`, because a missing
    pytest reports on stderr. Row R5.
13. **Each candidate's DENY-reason entry** (v1.1, teammate impl-plan audit c1): design D7 says
    "its summary line" and its Error Handling table says the reason names a start error. Task 3
    fixes the entry: the start error, `f"{type(exc).__name__}: {exc}"`, when the interpreter
    could not start, else the candidate's
    summary line, else its last non-empty output line (a `no-summary` run has no summary line).
14. **The refusal form is read from the hook lazily; the V-0 line is quoted in the test module's
    docstring** (v1.1, teammate impl-plan audit c1). A module-level read of
    `readonly REFUSAL_FORM=` fails collection at RED, because today's hook has no such line
    (`grep -c REFUSAL_FORM h-mad/hooks/h-mad-tdd-gate.sh` → 0 matching lines at `a1478ad3`). The
    tests do not read `v0.out` from `docs/`, because `v0.out` is a run artifact in this feature's
    probe directory (Task 0 item 2), whose presence and content at test time depend on which checkout
    the suite runs in; a quote held by the test file itself does not. (v1.1 argued "Skill
    self-containment" instead; that overstated it: Task 2 item 8 reads the repository's
    `docs/**/*.impl-plan.md`, and existing modules set `REPO_ROOT = Path(__file__).resolve().parents[2]`,
    `h-mad/tests/conftest.py:24`.) AC-6.6 already requires the docstring quote, so the test compares
    the hook's literal with it.
15. **W4F's force literal is `_suite_summary("1 failed in 0.01s")`**, where the design's W3/W4
    table writes `SuiteSummary(0, 1, 0, False, frozenset({"failed"}))`. The effect is the same
    value, and the plan's form needs no `SuiteSummary` import in the judge.
16. **Design v1.3's directory-exemption subject is landed as a membership flag and one matcher**
    (v1.2). Design §D9 step 3 decides "inside the root" by the `case` pattern `"$R"/*` and matches
    `*/tests/*|*/fixtures/*` against `DIR_SUBJECT="/${TARGET_PATH#"$R"/}"` inside the root, and
    against both the canonical `TARGET_PATH` and `RAW_TARGET` outside it. Task 8 lands the
    membership decision as `IN_ROOT=yes|no` (step 3, after the normalization) and the two
    alternatives once, in a function `_dir_match`, which both branches call; the second `case`
    block keeps only the extension alternatives. The design's variable names `RAW_TARGET`, `R` and
    `DIR_SUBJECT` are kept. Executed under `/bin/bash` 3.2.57 with `set -euo pipefail` in a scratch
    script of Task 8 steps 4 and 7 only (deleted), at `c93da638`: the 126-cell corpus reads 18
    refusals (6 per root shape), softened exactly the 6 and tightened exactly the 8 cells design
    v1.3 names, against `git show HEAD:h-mad/hooks/h-mad-tdd-gate.sh` (Task 8 §"Executed
    readings").

## Preamble — where and how this plan runs

- **Where the readings were taken.** Every "read at `f6b258f0`" ran on the main checkout at that
  commit. `main` then advanced to `a85abf7f`, which adds only three `multi-host-runtime` audit
  documents: `git diff --name-only f6b258f0 a85abf7f -- h-mad handoff docs/03-analysis/probes pytest.ini`
  → 0 files. So every reading also holds at `a85abf7f`. All of them move at the 5c base, and Task 0
  re-takes the ones the tasks depend on.
- **Worktree, not the main checkout.** `readlink ~/.claude/skills/h-mad` →
  `/Users/kimhawk/orca/skills/h-mad` and `readlink ~/.claude/hooks/h-mad-tdd-gate.sh` →
  `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh` (read at `f6b258f0`), so an edit on
  the main checkout changes the live gate mid-run. The branch is cut as
  `git worktree add ../skills-codex-tdd-gate-defects -b feature/codex-tdd-gate-defects` (plan
  §"Convention Prerequisites"). At `f6b258f0`, `git worktree list` shows the main checkout and
  `~/orca/skills-grok-codex-fallback` (`feature/216-grok-codex-fallback` at `0cdbf8e0`); no branch
  or worktree for this feature exists.
- **Merge order.** This feature merges first, then `grok-codex-fallback`, then
  `multi-host-runtime` (plan §"Convention Prerequisites"). `grok-codex-fallback` rebases onto this
  feature after it merges and re-plans its Task 12 and Task 14 onto design §D13's contract (the
  `fallback` subfield of the `state` line, the fold in the judge, `_refuse fallback-grok` /
  `_refuse fallback-invalid` in the chosen form). None of grok's tasks is planned here.
- **`BASE_SHA`** is the parent of the 5c commit, derived once in Task 0 from
  `python3 h-mad/scripts/h_mad_baseline_sha.py --branch feature/codex-tdd-gate-defects`. Only the
  `OK` token carries `sha=`; any other token halts Task 0 with `HALT: BASELINE not OK`.
- **Codex authors 5d/5e.** The installed Claude gate is the main checkout's pre-feature
  `h-mad/hooks/h-mad-tdd-gate.sh`. For every `h-mad/scripts/*.py` and `h-mad/hooks/*.py` path it
  derives no test (`h_mad_derive_test_path.sh` maps only `hematology-paper-writer/`,
  `clinical-statistics-analyzer/` and `shared/`, read at `f6b258f0`), so a Claude write there is
  refused. If codex is out, halt to the operator; never bypass the gate.
- **Expected baseline failure.** Measured at `f6b258f0`:
  `/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts`
  → `1 failed, 3892 passed, 1 warning in 572.72s (0:09:32)`, and the failing node is
  `h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`
  (it reads the installed `claude` binary; outside this feature's files). Collection:
  `… --collect-only -q … | tail -1` → `3893 tests collected`. That node is the only failure any
  task may leave, and only if Task 0 recorded it failing at `BASE_SHA` for the same reason.

### Conventions every task follows

1. **Full coupled suite, per task.** Every task's GREEN verification runs, from the worktree root,
   `/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts`
   in full (a scoped green is not a suite green), and then runs the task's own test files a second
   time with `CLAUDE_ZZZ_PROBE=1` exported. The second run must report the same `passed` count.
   The only failure allowed is the baseline node above.
2. **Expected RED splits are per test, and checked by count.** Each task states its new collected
   items, which fail and which pass at RED, and why each passing one passes. 5d reads the pytest
   summary (`N failed, M passed`) and requires those exact numbers, and for a `wiring` task also
   the failure reason of the `WIRE-PIN`. A new module that does not import yet is RED as one
   collection error with 0 items, as the sibling impl-plan states it.
3. **Hermetic subprocess environment.** Claude Code exports about fifteen `CLAUDE*` names. Every
   test that starts a subprocess passes either `env=hermetic_env(...)` or an explicit minimal
   dict it builds itself. `hermetic_env(**extra)` copies `os.environ`, drops every key that starts
   with `CLAUDE` and the keys `HPW_AGENT_BACKEND`, `HMAD_CODEX_UNAVAILABLE` and
   `CODEX_PROJECT_DIR`, then applies `extra`. In-process judge tests run under an autouse fixture
   that `monkeypatch.delenv`s the same names, because the judge's pytest child inherits the
   process environment. The ambient probe of Convention 1 proves the split.
4. **Every test that invokes a hook passes stdin explicitly** (design D9 step 2, orchestrator
   OD-L): `input=<payload JSON>` for a payload test, `stdin=subprocess.DEVNULL` for a
   positional-argument test. A held-open inherited pipe costs the reader's 2.0 s bound per call and
   bytes on it would be decided as a payload.
5. **Every `subprocess.run` in a test carries a `timeout=`:** `timeout=60.0` by default,
   `timeout=120.0` for the two 40 s-budget `timeout` rows (Tasks 6 and 8), and `timeout=5.0`
   around every non-blocking FIFO assertion. A FIFO test catches `subprocess.TimeoutExpired` and
   fails on an assertion (`assert elapsed < 1.0`), never on the exception, so a blocking mutant is
   an assertion kill, not a crash kill.
6. **No identity assertion between compiled patterns.** `re.compile` caches, so two separately
   compiled identical patterns are the same object. No test asserts `is` between patterns. A test
   that needs a fresh module constant calls `re.purge()` and then `importlib.reload`, or compares
   `.pattern` and `.flags`.
7. **Parametrize ids are part of the contract.** Every id below is written with
   `pytest.param(..., id="…")` or `ids=[…]`. Mutation `test` keys and WIRE-PINs use full node ids
   (`tests/<file>.py::<name>[<id>]` in specs, relative to `h-mad/`; `h-mad/tests/…` elsewhere).
8. **Committed anchors.** After every task that edits a file a committed mutation spec anchors,
   `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json`
   must print `ANCHORS: ANCHORS_OK` with `drifted=0` (read the token, never `$?`). At `f6b258f0`
   it reads `specs=99 mutations=907 ok=907 drifted=0`. The anchored files this plan edits are
   `h-mad/scripts/h_mad_audit_gate.py` (`audit_gate_stamp.json`, `audit_leg_set_gate.json`,
   `audit_round_cap.json`, `audit_suite_gate.json`, `collect_report.json`) and
   `h-mad/scripts/h_mad_wire_pin_gate.py` (`wire_pin_numbered_labels.json`,
   `wire_pin_one_wire_many_pins.json`, `wire_pin_shape_vocabulary.json`), and `h-mad/SKILL.md`
   (Task 9): a JSON walk of `h-mad/tests/mutation-specs/*.json` over each row's `file` at
   `a1478ad3` gives `SKILL.md` 53 rows in 14 specs, `scripts/h_mad_audit_gate.py` 44 rows in 5,
   `scripts/h_mad_wire_pin_gate.py` 11 rows in 3, and 0 rows for every other file this plan edits
   (both hooks, `references/codex-runtime.md`, `references/agy-runtime.md`,
   `references/codex-implementer-prompt.md`, `scripts/h_mad_derive_test_path.sh`, and the test
   modules `test_h_mad_audit_suite_gate.py`, `test_h_mad_codex_runtime.py`,
   `test_h_mad_tdd_gate_codex.py`, `test_h_mad_tdd_gate_state_resolution.py`). The sweep
   therefore runs after Tasks 1, 2 and 9, and after Task 10 adds its own specs. No new line may be byte-identical to an existing
   anchor.
9. **Mutation tags.** Every line a Task 10 row anchors ends with a tag comment, `# M:` followed by the row id (`# M:S1`, `# M:W4`),
   written verbatim as the task shows it, and each tag occurs once in its file, counted with a
   line-end boundary (`grep -c '# M:H1$'`, because `# M:H1` is a prefix of `# M:H10`…`# M:H20`,
   `# M:S1` of `# M:S10`… and `# M:G1` of `# M:G10`). A spec row's `find` is the whole tagged
   line, indentation included. Rows S8B, S11, S12, K3B, K5, G6B, G6C, H15B, H18B, H20A, H20B,
   W5BF2, W5BF3, C2G and C3G reuse another row's tag (H20A and H20B the tag `M:H20`); P1, P1B, P2,
   G8 and G11 quote an untagged line, as R2 and W3C do.
10. **No bare time-limit command.** `h-mad/tests/test_h_mad_portable_timeout.py` scans
    `h-mad/scripts/*.py`, `h-mad/scripts/*.sh`, `h-mad/hooks/*.sh`, `h-mad/references/*.md` and
    `h-mad/SKILL.md` with `(?:^|[^-\w])timeout\s+\d+` (read at `f6b258f0`). Prose says "a 40 s
    budget" or "the 2.0 s bound", never the word followed by a number; code passes
    `communicate(timeout=remaining)`, which the pattern does not match.
11. **Probes are deleted.** A scratch probe written to confirm a suspected defect is deleted once
    it answers. The files under `docs/03-analysis/probes/codex-tdd-gate-defects/` are deliverables.
12. **Python floor.** The judge and every module it imports must parse and import under Python 3.9
    (`/usr/bin/python3 --version` → `Python 3.9.6` at `f6b258f0`): no `match`, no parenthesised
    context managers, no `X | Y` outside annotations under `from __future__ import annotations`.

---

## Task 0: baseline-and-probe-prerequisites

**Production file**: `docs/03-analysis/probes/codex-tdd-gate-defects/toplevel_diff.py` (new). The
readings go into `docs/03-analysis/codex-tdd-gate-defects.analysis.md` §"Baseline at BASE_SHA",
which this task creates.
**Test file**: none. The probe's controls below are run, not asserted.
**Task shape**: `gate`

**Description**: The 5c readings (plan §"Convention Prerequisites", design Implementation Order
steps 1 and 9). Each item records its command and its reading, stamped with `BASE_SHA`.
1. **Step P0 landed.** Plan step P0 is the orchestrator's, run on the main checkout before the
   worktree is cut. At `f6b258f0` it has not run:
   `ls docs/03-analysis/probes/codex-tdd-gate-defects/` → `hemasuite-t7_green.blocked1.report.md`
   only (1 file). This item requires, at `BASE_SHA`, the four probes with the plan's sha256 pins
   (`shasum -a 256`): `reproduce.py` `45f763ee14162b4747fe1c3dee3afa1478f9cc86d2599717f3993bd34939d974`,
   `v0-blocking-contract.sh` `04700d9ffc254a603387f4baf1a62a1b115956fd410d88c3484db3fc50ddaff4`,
   `v1-offline-replay.sh` `8dd639240265d338ee24aa6a52e80929302c52c14ee8c41b8bb9360cd2e4ee10`,
   `wire-registry-grammar.py` `9d20448039ca662b646981fbb57ddc1879fa852faaaa4dbef2b0654150b82650`,
   and their three pre-merge readings (`reproduce.reading.*.txt` with 24 `REPRO:` lines,
   `wire-registry-grammar.reading.*.txt`, `v1-offline-replay.reading.*.txt` ending
   `V-1r: DONE VERDICT=FAIL fails=4/6 `). Anything missing prints `HALT: P0 not committed` and
   returns to the orchestrator.
2. **V-0 status.** Record whether `v0.out` is committed in the probe directory and, if it is, its
   line matching `^V-0: READING=\(E1_BLOCKS\|E1_DOES_NOT_BLOCK\) FORM_A=[A-Z_]* FORM_B=[A-Z_]* CHOSEN=\(a\|b\) `.
   V-0 is a precondition of Task 8 only; Tasks 1–7 do not wait for it.
3. **`BASE_SHA`** (§Preamble).
4. **Suite baseline**: Convention 1's command, `| tail -3`. Record the summary and each failing
   node with its reason.
5. **Node ids for the floor**:
   `/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts 2>&1 | grep '::' | sort > "$(git rev-parse --absolute-git-dir)/hmad-ctg-base-nodeids.txt"`.
   The file sits inside the git directory, untracked, until Task 11.
6. **Anchors**: Convention 8's command → `ANCHORS_OK drifted=0`, with its `specs=`/`mutations=`
   figures recorded (they grow by construction in Task 10 and are never carried).
7. **Author `toplevel_diff.py`**, the checker plan §"Success Criteria" asks the impl-plan to ship
   as a probe. Stdlib only.
   - Usage: `toplevel_diff.py --base SHA [--head REF] [--repo PATH]` (`--head` defaults to
     `HEAD`, `--repo` to the repository holding the probe, found with
     `git -C "$(dirname "$0")" rev-parse --show-toplevel`).
   - File set: every `*.py` that
     `git diff --diff-filter=M --name-only BASE HEAD -- h-mad/tests handoff/tests handoff/scripts`
     names; every `conftest.py` that exists at `BASE` in a directory on the path of one of those
     files; and every module of the same directory, existing at `BASE`, that one of those files
     imports (`import X` or `from X import …` with a sibling `X.py`).
   - Per file, both versions are parsed with `ast`. Each top-level `def`, `async def` and `class`
     is keyed by its name, each top-level `Assign`/`AnnAssign` by its target names joined with
     `,`. A key whose `ast.get_source_segment` differs prints
     `TOPDIFF: changed <file>::<key>`; a key present at `BASE` and absent at `HEAD` prints
     `TOPDIFF: removed <file>::<key>`. The run ends
     `TOPDIFF: DONE files=N changed=N removed=N`, exit 0. An unresolvable sha prints
     `TOPDIFF: UNREADABLE reason=bad_sha`, exit 2.
   - Controls, each executed in this task: C0.1 `--base "$BASE_SHA" --head "$BASE_SHA"` →
     `TOPDIFF: DONE files=0 changed=0 removed=0`. C0.2: in a `tempfile.TemporaryDirectory` git
     repository (removed on exit) holding `h-mad/tests/test_a.py` with `def test_x()` and
     `def test_y()`, a second commit that edits `test_x`'s body and deletes `test_y` →
     `TOPDIFF: changed h-mad/tests/test_a.py::test_x`, `TOPDIFF: removed h-mad/tests/test_a.py::test_y`,
     `TOPDIFF: DONE files=1 changed=1 removed=1`. C0.3: `--base deadbeef` →
     `TOPDIFF: UNREADABLE reason=bad_sha`, exit 2.

**Acceptance Criteria**:
- [ ] AC-0.1 (orchestrator-owned, recorded here): the V-0 recipe, its reading, the captured
  payload, the four replay results and the per-arm `HIT` logs are committed, or item 2 records
  "V-0 not yet run" and Task 8 does not start.
- [ ] Items 1–6 recorded with `BASE_SHA`; C0.1–C0.3 print exactly the tokens above.

**Mutation rows**: none. **Dependencies on other tasks**: None. It runs right after the 5c
impl-plan commit.

---

## Task 1: suite-summary-line

**Production file**: `h-mad/scripts/h_mad_audit_gate.py`
**Test file**: `h-mad/tests/test_h_mad_audit_suite_gate.py`, `h-mad/tests/test_h_mad_tdd_gate_support.py` (new), `h-mad/tests/tdd_gate_support.py` (new, lands in the RED commit)
**Task shape**: `new-behaviour`

**Description**: Design §D7, the parser half and `run_suite`; spec FR-4 "Audit-gate changes" and
"Audit-gate non-change"; plan §"Regression census" table. Also creates
`h-mad/tests/tdd_gate_support.py` with `hermetic_env` (Deviation 1, Convention 3).

- `from typing import FrozenSet, NamedTuple, Optional` lands after `from pathlib import Path`
  (the import block is `argparse`, `subprocess`, `hashlib`, `json`, `os`, `re`, `sys`,
  `from pathlib import Path`, read at `f6b258f0`).
- `_SUITE_RE` (today at `h-mad/scripts/h_mad_audit_gate.py:440`) is deleted: `git grep -nw _SUITE_RE f6b258f0 -- h-mad handoff`
  → 2 matching lines, both in that file (the definition, line 440, and `_suite_summary`'s loop,
  line 450; the same count at `c93da638`). Without `-w` the scoped command gives 4 matching lines,
  the other two being `<INLINE_SUITE_REFERENCE>` substrings in
  `h-mad/references/codex-verifier-prompt.md`, and unscoped it gives 11 (v1.1 published the
  unscoped command with the word-bounded figure).
- `_suite_summary` is replaced in place. Its callers stay `run_suite` alone
  (`git grep -n "_suite_summary" -- h-mad handoff ':!h-mad/tests/fixtures'` → 2 matching lines at
  `f6b258f0`: the definition and `run_suite`'s call).

**Landed literals** (replacing `_SUITE_RE` and today's `_suite_summary`):
```python
class SuiteSummary(NamedTuple):
    passed: int
    failed: int
    errors: int
    no_tests_ran: bool
    phrases: FrozenSet[str]


_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")
_CATEGORY = r"[a-z][a-z-]*(?: [a-z][a-z-]*)*"  # M:S9
_PHRASE = r"\d+ " + _CATEGORY
_SUMMARY_LINE_RE = re.compile(
    r"^(?:(?P<ph>" + _PHRASE + r"(?:, " + _PHRASE + r")*)|no tests ran)"
    r"(?P<timed> in \d+(?:\.\d+)?s(?: \(\d+:\d{2}:\d{2}\))?)?$"
)
_PHRASE_RE = re.compile(r"(\d+) (" + _CATEGORY + r")")


def _suite_summary(text: str) -> Optional[SuiteSummary]:
    """pytest's own summary line, whole-line only, SGR stripped; a timed line beats an untimed one."""
    timed: Optional[SuiteSummary] = None
    untimed: Optional[SuiteSummary] = None
    for raw in text.splitlines():
        line = _SGR_RE.sub("", raw).strip().strip("=").strip()  # M:S4
        match = _SUMMARY_LINE_RE.match(line)  # M:S8
        if match is None:
            continue
        if match.group("ph") is None:
            summary = SuiteSummary(0, 0, 0, True, frozenset())
        else:
            passed = failed = errors = 0
            phrases = set()
            for part in match.group("ph").split(", "):
                number, category = _PHRASE_RE.fullmatch(part).groups()
                phrases.add(category)
                if category == "passed":  # M:S5
                    passed += int(number)
                elif category == "failed":  # M:S6
                    failed += int(number)  # M:W4C
                elif category in ("error", "errors"):  # M:S7
                    errors += int(number)  # M:S10
            summary = SuiteSummary(passed, failed, errors, False, frozenset(phrases))
        if match.group("timed"):
            timed = summary
        else:
            untimed = summary
    return timed if timed is not None else untimed  # M:S3
```
The regex is built by concatenation, never as an `rf`-string, because `\d{2}` inside an f-string is
a format field. `run_suite`'s `passed, failed = summary` line becomes these three lines, and every
anchored `run_suite` line keeps its bytes:
```python
    if not ({"passed", "failed"} & summary.phrases):  # M:S1
        return {"reason": "no_summary", "verdict": "UNREADABLE", "rc": run.returncode}
    passed, failed = summary.passed, summary.failed
```
The new return orders its keys `reason, verdict, rc`, so it is not byte-identical to the anchored
`        return {"verdict": "UNREADABLE", "reason": "no_summary", "rc": run.returncode}`.

**Executed readings** (a scratch copy of the literals above under `/usr/bin/python3` 3.9.6 at
`f6b258f0`, deleted): every row of the table below read exactly its expected value, including
`2 rows inserted` → phrases `{"rows inserted"}` and `3 records written in 0.2s` → phrases
`{"records written"}` (design D7's stated open-axis residual, not pinned). Today's
`_suite_summary`, called on the same 22 inputs, returned `(2, 0)`, `(8, 1)`, `(1, 0)`, `(9, 0)`,
`(2, 1)`, `(2, 0)`, `(1, 0)` for rows 4, 5, 6, 7, 8, 10, 13 and `None` for the other 15.

**`tdd_gate_support.py` (new), first contents**:
```python
"""Shared test support for codex-tdd-gate-defects (not collected: no test_ prefix)."""
from __future__ import annotations

import os

DROPPED_ENV = ("HPW_AGENT_BACKEND", "HMAD_CODEX_UNAVAILABLE", "CODEX_PROJECT_DIR")


def hermetic_env(**extra: str) -> dict[str, str]:
    """os.environ minus every CLAUDE* name and DROPPED_ENV, then `extra`."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE") and k not in DROPPED_ENV}  # M:E1
    env.update(extra)
    return env
```
This block is the whole file as Task 1 lands it; later tasks append below it and add their own
imports to the import block. **Executed** (v1.2, codex impl-plan audit c2 must 2): the block
written verbatim to a scratch directory (deleted) at `c93da638` imports and runs under
`/usr/bin/python3` 3.9.6 and `/opt/anaconda3/bin/python` 3.11.8: with `CLAUDE_ZZZ_PROBE=1` and
`HPW_AGENT_BACKEND=claude` exported, `hermetic_env(X="1")` holds neither, holds `X == "1"` and
keeps `PATH`. The same block without `import os` (v1.1's literal) raises
`NameError: name 'os' is not defined` on the first `hermetic_env()` call.
The file lands in this task's RED commit (Deviation 1), so the test below passes at RED; row E1
is its observed failure.

**Tests** (38 new collected items).
In `test_h_mad_audit_suite_gate.py`, as new top-level functions (no existing class or function is
touched except the docstring below). A module helper `_run_hermetic(*args)` runs
`[sys.executable, str(SCRIPT), *args]` with `capture_output=True, text=True, env=hermetic_env(),
stdin=subprocess.DEVNULL, timeout=60.0`.
1. `test_run_suite_table_row[…]` (15). Each row writes a `fake_suite` stub, runs the audit CLI with
   `--project-tests <tmp_path> --suite-cmd <stub>` over the module's `CLEAN` audit, and asserts
   `token(out, "SUITE:")` equals exactly:

   | id | stub prints (then exits) | expected `SUITE:` line |
   |---|---|---|
   | `three-failed` | `3 failed in 0.10s` (1) | `SUITE: FAIL passed=0 failed=3` |
   | `three-failed-one-skipped` | `3 failed, 1 skipped in 0.1s` (1) | `SUITE: FAIL passed=0 failed=3` |
   | `failed-and-error` | `1 failed, 1 error in 0.1s` (1) | `SUITE: FAIL passed=0 failed=1` |
   | `one-error` | `1 error in 0.06s` (2) | `SUITE: UNREADABLE reason=no_summary` |
   | `no-tests-ran` | `no tests ran in 0.01s` (5) | `SUITE: UNREADABLE reason=no_summary` |
   | `passed-and-error` | `2 passed, 1 error in 0.1s` (1) | `SUITE: PASS passed=2 failed=0` |
   | `failed-and-passed` | `1 failed, 11 passed in 0.2s` (1) | `SUITE: FAIL passed=11 failed=1` |
   | `collected-zero` | `collected 0 items` (0) | `SUITE: UNREADABLE reason=no_summary` |
   | `stray-failed-on-stderr` | stdout `2 passed in 0.1s`, then stderr `1 failed` (0) | `SUITE: PASS passed=2 failed=0` |
   | `coloured` | `printf '\033[31m\033[31m\033[1m1 failed\033[0m, \033[32m1 passed\033[0m\033[31m in 0.04s\033[0m\033[0m\n'` (1) | `SUITE: FAIL passed=1 failed=1` |
   | `three-skipped` | `3 skipped in 0.1s` (0) | `SUITE: UNREADABLE reason=no_summary` |
   | `five-deselected` | `5 deselected in 0.1s` (5) | `SUITE: UNREADABLE reason=no_summary` |
   | `one-xfailed` | `1 xfailed in 0.1s` (0) | `SUITE: UNREADABLE reason=no_summary` |
   | `subtests-passed` | `2 passed, 2 subtests passed in 0.00s` (0) | `SUITE: PASS passed=2 failed=0` |
   | `subtests-failed-run` | `2 failed, 1 subtests passed in 0.02s` (1) | `SUITE: FAIL passed=0 failed=2` |

2. `test_suite_summary_reads_the_line[…]` (22). In-process
   `assert _suite_summary(text) == expected`, where `expected` is `None` or a plain 5-tuple
   `(passed, failed, errors, no_tests_ran, frozenset(phrases))`; a `NamedTuple` equals the plain
   tuple of its values, and today's 2-tuple equals no 5-tuple, so every mismatch is an assertion.

   | # | id | text | expected |
   |---|---|---|---|
   | 1 | `one-failed` | `1 failed in 0.01s` | `(0, 1, 0, False, {"failed"})` |
   | 2 | `one-error` | `1 error in 0.06s` | `(0, 0, 1, False, {"error"})` |
   | 3 | `no-tests-ran` | `no tests ran in 0.00s` | `(0, 0, 0, True, set())` |
   | 4 | `stray-untimed-failed` | `2 passed in 0.1s` + newline + `1 failed` | `(2, 0, 0, False, {"passed"})` |
   | 5 | `untimed-failed-passed` | `1 failed, 8 passed` | `(8, 1, 0, False, {"failed", "passed"})` |
   | 6 | `coloured` | the `coloured` bytes of item 1 | `(1, 1, 0, False, {"failed", "passed"})` |
   | 7 | `passed-warning` | `9 passed, 1 warning in 1.09s` | `(9, 0, 0, False, {"passed", "warning"})` |
   | 8 | `padded-wallclock` | `==== 1 failed, 2 passed in 65.20s (0:01:05) ====` | `(2, 1, 0, False, {"failed", "passed"})` |
   | 9 | `one-xfailed` | `1 xfailed in 0.1s` | `(0, 0, 0, False, {"xfailed"})` |
   | 10 | `subtests-passed` | `2 passed, 2 subtests passed in 0.00s` | `(2, 0, 0, False, {"passed", "subtests passed"})` |
   | 11 | `subtests-failed-run` | `2 failed, 1 subtests passed in 0.02s` | `(0, 2, 0, False, {"failed", "subtests passed"})` |
   | 12 | `coloured-subtests` | `\x1b[31m3 failed\x1b[0m, \x1b[32m1 subtests passed\x1b[0m\x1b[31m in 0.02s\x1b[0m` (synthetic; design D7's `od -c` capture is not quoted) | `(0, 3, 0, False, {"failed", "subtests passed"})` |
   | 13 | `passed-skipped` | `1 passed, 1 skipped in 0.00s` | `(1, 0, 0, False, {"passed", "skipped"})` |
   | 14 | `three-skipped` | `3 skipped in 0.1s` | `(0, 0, 0, False, {"skipped"})` |
   | 15 | `five-deselected` | `5 deselected in 0.1s` | `(0, 0, 0, False, {"deselected"})` |
   | 16 | `subtests-failed` | `2 subtests failed in 0.1s` | `(0, 0, 0, False, {"subtests failed"})` |
   | 17 | `three-apples` | `3 apples in 0.1s` | `(0, 0, 0, False, {"apples"})` |
   | 18 | `collected-zero` | `collected 0 items` | `None` |
   | 19 | `quoted-assert` | `E   assert '1 failed' in x` | `None` |
   | 20 | `failed-node-line` | `FAILED t.py::a - 1 failed` | `None` |
   | 21 | `capitalised-category` | `3 Apples in 0.1s` | `None` |
   | 22 | `one-errors` | `1 errors in 0.1s` | `(0, 0, 1, False, {"errors"})` |

In `test_h_mad_tdd_gate_support.py` (new):
3. `test_hermetic_env_drops_claude_names_and_backend` (1). With `CLAUDE_ZZZ_PROBE=1`,
   `CLAUDE_PROJECT_DIR=/nowhere`, `HPW_AGENT_BACKEND=claude`, `HMAD_CODEX_UNAVAILABLE=1` and
   `CODEX_PROJECT_DIR=/nowhere` monkeypatched in, `hermetic_env(X="1")` holds none of them, holds
   `X`, and keeps `PATH`; `hermetic_env(CLAUDE_PROJECT_DIR="/r")["CLAUDE_PROJECT_DIR"] == "/r"`; a
   child started with `env=hermetic_env()` through
   `subprocess.run([sys.executable, "-c", <print the sorted matching names as JSON>], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60.0)`
   prints `[]`.

15 + 22 + 1 = 38.

**Docstring correction** (not an assertion change): `test_an_empty_selection_is_not_a_pass` says a
`no tests ran` stub "never reaches the verdict logic at all". After this task it does; the sentence
becomes "reaches the one predicate and still reads `no_summary`". It lives inside class
`TestTheSuiteVerdictIsScoredOnTheSummary`, so §"Regression provenance" lists that class.

**Expected RED split**: in `test_h_mad_audit_suite_gate.py`, 23 failing and 14 passing among the
37 new items, and the 21 existing items pass (collected 21 at `f6b258f0`).
- Item 1: 5 fail (`three-failed`, `three-failed-one-skipped`, `failed-and-error`, `coloured`,
  `subtests-failed-run`: today each reads `no_summary`, or `PASS passed=1 failed=0` for
  `coloured`); 10 pass as regression guards, because today's reading already equals the
  expected line (the five `no_summary` rows, `passed-and-error`, `failed-and-passed`,
  `stray-failed-on-stderr`, `subtests-passed` and `collected-zero`).
- Item 2: 18 fail on the tuple assertion; 4 pass (rows 18–21: today `None`, expected `None`).
- `test_h_mad_tdd_gate_support.py`: 1 passing (`tdd_gate_support.py` lands in the RED commit,
  Deviation 1, so `hermetic_env` exists and the module imports).
Over the task's 38 new items: 23 failing and 15 passing.
**After GREEN**: 58 passed in the audit module (21 + 37), 1 in the support module.
**Passing at RED, and the row that shows each one failing** (Task 10 §"Initially-green guards"):
item 1 `subtests-passed` S1, `stray-failed-on-stderr` S3, the five `no_summary` rows S12,
`passed-and-error` S10, `failed-and-passed` S11, `collected-zero` the existing
`a-missing-summary-becomes-a-verdict` row of `audit_suite_gate.json` (its subject, the
`summary is None` return, is unchanged); item 2 rows 18 and 20 S8, row 21 S9, row 19 S8B; item 3
E1.
**Regression guards**: the 21 existing audit-suite tests, unmodified in assertions, including
`test_no_summary_is_UNREADABLE_not_PASS_and_not_FAIL` and
`test_a_run_that_says_only_no_tests_ran_is_also_refused` (plan §"Regression census");
`h-mad/tests/test_h_mad_audit_cycle.py` (a `run_suite` consumer through `h_mad_audit_cycle`);
`audit_suite_gate.json`'s 9 anchors.

**Acceptance Criteria**:
- [ ] AC-4.7: items 1 and 2; the existing audit-suite tests pass. Spec AC-4.7's "a test that pinned
  one of the three audit-gate change rows is updated" has no member (plan §"Regression census":
  no existing stub prints a failures-without-passes summary), so no assertion changes.

**Mutation rows** (Task 10): S1, S2, S3, S4, S5, S6, S7A, S7B, S8, S8B, S9, S10, S11, S12 and E1
in `audit_suite_summary_line.json` — 15 rows.

**Dependencies on other tasks**: Task 0

---

## Task 2: parse-tasks-paths

**Production file**: `h-mad/scripts/h_mad_wire_pin_gate.py`
**Test file**: `h-mad/tests/test_h_mad_parse_tasks_paths.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §D5; spec FR-2 rule 2 and AC-2.9. `_FIELD_RE`
(`h-mad/scripts/h_mad_wire_pin_gate.py:74`) stays byte-identical. The three regexes land directly
after `_FIELD_RE`'s definition and before `_FILLER`. The task dict gains `"production": []` and
`"tests": []` after `"pins": []`. Only the `if not field:` branch of `_parse_tasks`'s loop changes.

**Landed literals**:
```python
_PATHS_FIELD_RE = re.compile(
    r"^\s*(?:[-*•]\s+)?\*{0,2}\s*(?P<label>Production(?:\s+files?)?|Test(?:\s+files?)?)"
    r"\s*(?::\s*\*{0,2}|\*{0,2}\s*:)\s*(?P<value>.*)$",
    re.IGNORECASE,
)
_PY_TOKEN_RE = re.compile(r"`([^`]+\.py)`")
_NONE_VALUE_RE = re.compile(r"^[\s*_`]*none(?![\w/-]|\.\w)", re.IGNORECASE)
```
```python
        field = _FIELD_RE.match(line)
        if not field:
            paths = _PATHS_FIELD_RE.match(line)
            if paths is not None and _NONE_VALUE_RE.match(paths.group("value")) is None:
                key = "production" if paths.group("label").lower().startswith("production") else "tests"
                current[key].extend(_PY_TOKEN_RE.findall(paths.group("value")))
            continue
```
**Executed readings** (a scratch copy of the three regexes under `/usr/bin/python3` 3.9.6 at
`f6b258f0`, deleted): each label spelling of item 1 read its `.py` tokens; ``**Tests** (5 functions, `x.py`)``,
``**Production files** (x): `a.py` `` and ``**Task shape**: `wiring` `` read nothing; the four `none`
values of item 3 read `[]`; the four values of item 4 read `["none.py"]`, `["tools/a.py"]`,
`["a.py"]` and `["a.py"]`.

**Tests** (23 new collected items; the module imports `_parse_tasks` and `_FIELD_RE` from
`h_mad_wire_pin_gate`, which exists, and reads the new keys with `.get`, so a missing key fails an
assertion):
1. `test_paths_label_spelling[production-file|production-files|production|production-colon-inside|production-unbolded-lowercase|test-file|test-files|test|test-colon-inside|test-bulleted]`
   (10). One `## Task 1: t` section per id, one label line each (`**Production file**:`,
   `**Production files**:` with two tokens, `**Production**:`, `**Production file:**`,
   `production file:`, `**Test file**:`, `**Test files**:`, `**Test**:`, `**Test:**`,
   `- **Test file**:`); the matching list equals the tokens, the other list equals `[]`.
2. `test_tests_plural_prose_label_contributes_nothing` (1): ``**Tests** (5 functions, `x.py`)`` →
   `tests == []`.
3. `test_none_value_contributes_nothing[none-with-quoted-path|bold-none-dash|none-period|bare-none]`
   (4): `` none (writes `docs/x/derive_readings.py`) ``, `**none** — x`, `None.`, `none` → `[]`.
4. `test_none_rule_keeps_a_real_path[none-py-token|tools-path|nonexistent-word|none-slash]` (4):
   `` `none.py` ``, `` `tools/a.py` ``, ``nonexistent `a.py` ``, ``none/`a.py` `` → one entry each.
5. `test_label_lines_accumulate` (1): two `**Production file**:` lines in one task → both entries,
   in order.
6. `test_existing_fields_unchanged` (1): a task carrying `**Task shape**:`, `**WIRE**:`,
   `**WIRE-PIN**:`, a Production and a Test line yields the same `shape`, `wire`, `pin`, `wires`
   and `pins` as the same text with the two path lines deleted.
7. `test_field_re_is_unchanged` (1): `_FIELD_RE.pattern` and `_FIELD_RE.flags` equal the literal
   read at `f6b258f0` (Convention 6: no `is`).
8. `test_corpus_old_fields_unperturbed` (1): the corpus is this repository's
   `git -C <REPO_ROOT> ls-files '*.impl-plan.md'` minus every path holding an `/archive/` segment,
   with `REPO_ROOT = Path(__file__).resolve().parents[2]` (the precedent at
   `h-mad/tests/conftest.py:24`), each listed path read as `REPO_ROOT / path`. The directory is
   named explicitly because the mutation harness runs every spec's `command` with `cwd=root`
   (`h_mad_mutation_harness.py:380`), and every Task 10 spec's root is `h-mad/`, where the
   cwd-relative `git ls-files '*.impl-plan.md'` lists 0 files (executed at `c93da638`; from the
   repository top, 11 non-archive files). `_parse_tasks` of each file and of the same text with
   every path-label line removed give the same list of `id` values in the same order, and the same
   `shape`, `wire`, `pin`, `wires`, `pins` per task. A path-label line is one that the module's own
   constant `_PATHS_LABEL_LINE` matches: a copy of the Task 2 `_PATHS_FIELD_RE` literal above, held
   in the test file, because the module imports nothing that does not exist at RED. **Non-vacuity,
   asserted before the comparison**: the corpus holds at least one file, and the removed lines
   include at least one whose value holds a `.py` token (the P1 mutant's input). At `c93da638`
   the corpus reads 11 files and 105 such lines across all 11 (a scratch reading, deleted; the
   figures are re-read by the test, never frozen). `git` runs under `hermetic_env()` with
   `timeout=60.0`.

10 + 1 + 4 + 4 + 1 + 1 + 1 + 1 = 23.

**Expected RED split**: 20 failing (items 1–5: `.get("production")`/`.get("tests")` is `None`)
and 3 passing (items 6, 7, 8: the unchanged fields and the unchanged regex hold before the edit).
**Regression guards**: `h-mad/tests/test_h_mad_wire_pin_gate.py` (124 collected at `f6b258f0`),
`h-mad/tests/test_h_mad_assemble_tdd.py` (81) and `h-mad/tests/test_h_mad_wire_registry.py`
(114), unmodified; the three `wire_pin_*.json` specs' anchors.
`h_mad_wire_registry.py` is not edited (D-A).

**Acceptance Criteria**:
- [ ] AC-2.9 (in-repo half): the three regression modules pass unmodified; item 8. The
  cross-repository base comparison is Task 11's `parse_corpus.py`.
- [ ] Parser half of AC-2.2 and AC-2.3: items 1–4.

**Passing at RED, and the row that shows each one failing**: item 6 P1, item 8 P1B, item 7 P2
(Task 10 §"Initially-green guards").

**Mutation rows** (Task 10): P1, P1B and P2 in `tdd_judge_resolution.json` — 3 rows. R2 and W3C
also anchor in this file and are owned by Task 5, whose tests kill them.

**Dependencies on other tasks**: Task 0

---

## Task 3: judge-core

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py` (new)
**Test file**: `h-mad/tests/test_h_mad_tdd_judge.py` (new), `h-mad/tests/tdd_gate_support.py` (additions land in the RED commit)
**Task shape**: `new-behaviour`

**Description**: Design §D1, D2, D3 (the whole resolver, matching and candidates included; only
its Task list is the pre-wire `[]`), D4, D6, D7's classifier, D10 and D13's `fallback` field. The two callee connections land in their pre-wire form (Deviation 2): the plan
loop's Task list is `[]` and the classifier's summary is `None`, so every candidate run that
reaches rule 3 reads `no-summary` until Task 4. `tdd_gate_support.py` gains the fixture builders
below.

**Code structure** (design §"API / Interface Changes", with Deviation 3):
```python
from __future__ import annotations
# stdlib only: argparse, json, os, re, signal, stat, subprocess, sys, time, urllib.parse,
# pathlib.Path, typing.{NamedTuple, Optional, Sequence, Tuple, Union}
_HERE = str(Path(__file__).resolve().parent)       # inserted at sys.path[0] when absent
from h_mad_audit_gate import _SGR_RE, _SUMMARY_LINE_RE  # noqa: E402

KINDS = frozenset({"red-measured", "no-test-resolved", "test-missing", "venv-escapes-root",
                   "pytest-missing", "pytest-error", "no-tests-ran", "no-summary",
                   "test-passing", "timeout", "judge-error"})
STATE_VALUES = ("none", "active", "unreadable")
JUDGE_BUDGET_S = 40.0
ESCAPE_STATUSES = frozenset({"unavailable", "exhausted"})
NAME_MAP = Path(_HERE) / "h_mad_derive_test_path.sh"

class Record(NamedTuple):
    key: str; codex_status: str; state_file: Path; fallback: str
class Chain(NamedTuple):
    value: str; records: tuple; error_file: Optional[Path]; error: str
class Verdict(NamedTuple):
    decision: str; kind: str; reason: str; source: str; test: Optional[Path]
class Resolution(NamedTuple):
    source: str                      # "impl-plan" | "name-map" | ""
    present: Tuple[Tuple[Path, Path], ...]   # (test, cwd) in plan order, then task order
    missing: Tuple[Path, ...]
    notes: Tuple[str, ...]           # plan outcomes, drops, the literal name-map result
    verdict: Optional[Verdict]       # set when resolution alone decides

def read_chain(root: Path, target: Optional[Path]) -> Chain: ...
def resolve(root: Path, target: Path, records: Sequence[Record], *, deadline: float) -> Resolution: ...
def venv_contained(venv_parent: Path, root: Path) -> bool: ...
def select_interpreter(test: Path, root: Path, fallback: str) -> Union[str, Verdict]: ...
def score(proc_output: str, timed_out: bool) -> str: ...
def judge(root: Path, target: Path, records: Sequence[Record], *, budget_s: float = JUDGE_BUDGET_S,
          fallback_interpreter: str = sys.executable) -> Verdict: ...
def format_state_line(chain: Chain, root: Path) -> str: ...
def format_verdict_line(verdict: Verdict, root: Path) -> str: ...
def main(argv: Optional[list] = None) -> int: ...
```

**Landed structure** (each tagged line verbatim, once; Convention 9):
- **Chain** (D2). `read_chain` builds `dirs` nearest first: the realpath of the target's parent up
  to and including the realpath of `root`; `[real_root]` when `target` is `None`; and, for a target
  outside the root, the line `            dirs = [real_root]  # M:H14`. Each directory's
  `docs/.bkit-memory.json` goes through `_state_at(path) -> Tuple[str, object]`, which returns
  `("absent", None)`, `("unreadable", <error>)` or `("read", <dict>)`:
  ```python
      try:
          os.lstat(path)
      except (FileNotFoundError, NotADirectoryError):  # M:C6
          return "absent", None
      except OSError as exc:
          return "unreadable", type(exc).__name__
  ```
  then `fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)` (an `OSError` → its class name), and
  ```python
          if not stat.S_ISREG(os.fstat(fd).st_mode):  # M:C4
              return "unreadable", "not-a-regular-file"
  ```
  then read from that `fd`, decode UTF-8, `json.loads` (`OSError` or `ValueError` → class name),
  `os.close(fd)` in a `finally`; a top level that is not a dict, or an `orchestrator_state` key
  present with a non-dict value, → `"not-an-object"`. The loop:
  ```python
          status, data = _state_at(path)
          if status == "absent":
              continue
          if status == "unreadable":
              return Chain("unreadable", (), path, data)  # M:C2
          records.extend(_active_records(data, path))  # M:C1
  ```
  `_active_records` yields a `Record` per dict value with `phase == "step5"`, in JSON key order,
  `codex_status` defaulting to `"available"` for absent or `null` and `str()`-ed otherwise, and
  `fallback` by design §D13's table (`isinstance(value, str)` tested first; `invalid:` plus
  `json.dumps(value, separators=(",", ":"))`, unencoded).
- **State line** (D10). `_enc(s) = urllib.parse.quote(s, safe="/._-") or "%"`. In
  `format_state_line`:
  ```python
      escape = bool(chain.records) and all(r.codex_status in ESCAPE_STATUSES for r in chain.records)  # M:C3
      blocker = next((i for i, r in enumerate(chain.records, 1) if r.codex_status not in ESCAPE_STATUSES), 0)  # M:C5
  ```
  The fallback subfield is the literal tag, or `invalid:` + `_enc(<json text>)`, never `_enc` of
  the whole tag. State-file fields are absolute.
- **Resolution** (D3). The plan loop, per unique plan path in chain order:
  ```python
      for plan in plan_paths:
          try:
              text = plan.read_text(encoding="utf-8")
          except FileNotFoundError:
              notes.append(f"{plan}: absent")
              continue
          except (OSError, UnicodeDecodeError) as exc:
              notes.append(f"{plan}: impl-plan unreadable: {type(exc).__name__}")
              continue
          tasks = []  # M:W3
  ```
  Task 5 replaces the last line with `        tasks = _parse_tasks(text)  # M:W3`. Matching,
  candidate collection (realpath, dedup, outside-root drop noted as
  `candidate outside root dropped: <entry>`) and the per-plan note `matched` / `matched none`
  follow D3 steps 3–4 and 8. Then, at 4 spaces:
  ```python
      present = [c for c in candidates if _is_present(c[0])]  # M:R4
      missing = tuple(c[0] for c in candidates if not _is_present(c[0]))
      if matched:  # M:R1
          if not present:
              return Resolution("impl-plan", (), missing, tuple(notes), _test_missing(missing, notes, root))
          return Resolution("impl-plan", tuple(present), missing, tuple(notes), None)
  ```
  `_is_present(p)` is `os.stat` succeeding with `S_ISREG`. The name map runs
  `["bash", str(NAME_MAP), rel]` through `_run_bounded(…, cwd=real_root, deadline)` and reads its
  **stdout alone** (design D3 step 6; Deviation 12):
  ```python
      returncode, out, err, timed_out, error = _run_bounded(["bash", str(NAME_MAP), rel], real_root, deadline)
      mapped = out.strip()  # M:R5
  ```
  It notes `name map: ` plus the resolved path, `name map: empty for ` plus the root-relative
  target (an empty `mapped`, whatever stderr holds), or `name map: target outside root`, and ends in
  `timeout`, `test-missing`, `no-test-resolved` or a one-candidate `Resolution("name-map", …)`.
  The one `test-missing` constructor is the module-level helper
  `_test_missing(candidates: Sequence[Path], notes: Sequence[str], root: Path) -> Verdict`, whose
  whole body is the line below. The Task-match branch above calls it with `missing` as
  `candidates`; the name-map branch wraps it as
  `Resolution("name-map", (), (mapped_path,), tuple(notes), _test_missing((mapped_path,), notes, root))`
  (`mapped_path` the name map's resolved candidate) and never returns `_deny(…)` from `resolve`
  directly (`resolve` is typed `-> Resolution`):
  ```python
      return _deny("test-missing", f"no resolved test file exists ({_listing(candidates, root)}); author the failing test first{_notes(notes)}")  # M:R3
  ```
  `_notes(notes)` is `"; " + "; ".join(notes)` or `""`, and it ends every DENY reason of the call.
- **Venv** (D4):
  ```python
      if not _inside(os.path.realpath(venv), real_root):  # M:V1
          return False
      if not _inside(os.path.realpath(venv / "bin"), real_root):  # M:V2
          return False
      try:
          return stat.S_ISREG(os.lstat(venv / "pyvenv.cfg").st_mode)  # M:V3
      except OSError:
          return False
  ```
  `select_interpreter` takes the first `D` from `test.parent` up to the root for which
  `os.path.lexists(D/.venv/bin/python)`, returns the **unresolved** `str(D/.venv/bin/python)` when
  contained, a `venv-escapes-root` DENY naming `D/.venv` and its realpath when not, and `fallback`
  when no `D` exists.
- **Bounded run** (D6). `_run_bounded(argv, cwd, deadline) -> Tuple[Optional[int], str, str, bool, str]`
  (returncode, stdout, stderr, timed_out, start error; the two streams are never joined here,
  Deviation 12): `remaining <= 0` → `(None, "", "", True, "")`
  without starting; `subprocess.Popen(argv, cwd=…, stdin=subprocess.DEVNULL, stdout=PIPE,
  stderr=PIPE, start_new_session=True)`, an `OSError` → `(None, "", "", False, "<Class>: <msg>")`;
  `communicate(timeout=remaining)`; on `TimeoutExpired`, `os.killpg(proc.pid, signal.SIGKILL)`
  (a `ProcessLookupError` ignored) then `communicate()`. The file holds no `subprocess.run`.
- **Classifier** (D7):
  ```python
  def score(proc_output: str, timed_out: bool) -> str:
      if timed_out:
          return "timeout"
      if _pytest_missing(proc_output):  # M:K1
          return "pytest-missing"
      summary = None  # M:W4
      if summary is None:
          return "no-summary"
      if summary.no_tests_ran:
          return "no-tests-ran"
      if summary.errors >= 1:  # M:K2
          return "pytest-error"
      if summary.failed >= 1:
          return "red-measured"
      if summary.passed >= 1:
          return "test-passing"
      return "no-tests-ran"  # M:K4
  ```
  `_pytest_missing` is true when some line, after `_SGR_RE.sub("", line).strip()` (no `=`
  stripping), ends with `: No module named pytest`. Task 4 replaces the `# M:W4` line with
  `    summary = _suite_summary(proc_output)  # M:W4`.
- **Judge** (D3 step 5, D6, D7 "Several candidates"): `deadline = time.monotonic() + budget_s`;
  `resolve(…, deadline=deadline)`; for each present `(test, cwd)`: `select_interpreter`, then
  ```python
          returncode, out, err, timed_out, error = _run_bounded(argv, cwd, deadline)
          kind = "no-summary" if error else score(out + "\n" + err, timed_out)  # M:K3
  ```
  with `argv = [interpreter, "-m", "pytest", str(test), "-x", "-q", "--no-header"]`. The first
  `red-measured` returns `ALLOW`; `venv-escapes-root`, `timeout` and `pytest-missing` return DENY
  at once; otherwise the DENY kind is the first of `pytest-error`, `no-summary`, `no-tests-ran`,
  `test-passing` any candidate produced, and the reason names every candidate with its kind and
  one entry (Deviation 13): `error` itself (built as `f"{type(exc).__name__}: {exc}"`, so it
  begins `PermissionError: ` for a mode-`0o644` interpreter) when the interpreter could not
  start; else its summary line, the last line of `out + "\n" + err` that, after
  `_SGR_RE.sub("", line).strip().strip("=").strip()`, `_SUMMARY_LINE_RE.match`es (imported beside
  `_SGR_RE`, so the entry does not go through the W4 call); else its last non-empty output line.
  Each missing candidate is named `missing`, then the notes follow. A
  `pytest-error` reason contains `import` and `inside the test body` (AC-4.6). The rc appears in
  reasons only.
- **CLI** (D10): `argparse` with `state` and `judge` sub-commands, each `--root DIR [--target PATH]`
  (a relative target resolves against `--root`). An empty or non-directory `--root` → rc 2,
  nothing on stdout. `state` prints one line, rc 0; an exception prints nothing on stdout, a
  message on stderr, rc 2. `judge` reads the chain; a chain that is not `active` →
  `TDD-JUDGE: DENY kind=judge-error reason=chain is none at judge time` (or `unreadable`); any
  exception → the same DENY line whose reason is the exception class, a colon and its message
  (`reason=RuntimeError: boom`), rc 0. `format_verdict_line` maps `[\x00-\x1f\x7f]` in the reason to
  spaces; the ALLOW `test=` is root-relative POSIX inside the root, absolute outside, through `_enc`.

**`tdd_gate_support.py` additions**: `write_state(dir, records) -> Path` (writes
`dir/docs/.bkit-memory.json` as `{"orchestrator_state": records}`), `write_plan(state_dir, key, text)`,
`build_venv(dest, *, with_pytest)` (`[sys.executable, "-m", "venv", "--without-pip", …]`, adding
`--system-site-packages` when `with_pytest`, then asserting — failing, never skipping — the design
D12 precondition with the reason "builder's base interpreter has no pytest; run the suite under a
base interpreter (sys.prefix == sys.base_prefix)"; `/opt/anaconda3/bin/python` prints `9.1.1 3.11.8 True`
for pytest version, Python version and `sys.prefix == sys.base_prefix` at `f6b258f0`),
`fake_venv(dir, sh_body)` (a `.venv` with a regular `pyvenv.cfg` and a `/bin/sh` `bin/python`
script), `marker_shim(python, marker)` (design D12's marker shim) and
`sleeper(path, pidfile, seconds)` (a `/bin/sh` script that starts `sleep` for `seconds` seconds,
the value written into the script body, as its child,
writes that child's pid to `pidfile`, and waits on it). "A `fake_venv` whose `bin/python` is
`sleeper(…, seconds=N)`" means, in this order: `fake_venv(dir, "exit 0")`, then
`sleeper(dir / ".venv" / "bin" / "python", pidfile, N)`, which overwrites the script `fake_venv` wrote and
keeps it executable; `pyvenv.cfg` stays the regular file `fake_venv` made. The in-process `timeout` rows below run
at `budget_s=1.0` with `seconds=30`. The two gate-level `timeout` rows (Task 6 item 1, Task 8
item 1) run at the default 40 s budget and pass `seconds=90`, so the sleeper is still alive when
the budget runs out: the verdict is `timeout`, not a `no-summary` from a sleeper that exited on its
own, and the pid-gone check after it is meaningful. 40 s plus hook start-up stays under those rows'
`timeout=120.0`, and 90 s does too, so a missing kill fails on the pid assertion, never on the
subprocess timeout.

**Tests** (80 new collected items). An autouse fixture strips the ambient names (Convention 3).
In-process calls use `judge.judge(…, fallback_interpreter=sys.executable)` unless stated.
- Chain (17):
  1. `test_chain_reads_every_state_file_up_to_root` — root state step5 `feat`,
     `sub/docs/.bkit-memory.json` = `{"orchestrator_state": {}}`, target `sub/tools/x.py` →
     `active`, keys `["feat"]`, `state_file` the root file (AC-5.2's core; the OD-3 case).
  2. `test_chain_orders_records_nearest_first` — sub step5 `a`, root step5 `b` → `["a", "b"]`.
  3. `test_chain_without_step5_is_none`.
  4. `test_first_unreadable_file_decides[root-unreadable-sub-step5|sub-unreadable-root-step5]` →
     `unreadable` each (a readable step5 record elsewhere does not rescue it).
  5. `test_non_regular_state_is_unreadable[fifo|directory|dangling-symlink]` → errors
     `not-a-regular-file`, `not-a-regular-file`, `FileNotFoundError`; the `fifo` call returns
     within 1.0 s.
  6. `test_unsearchable_directory_is_unreadable[chmod-dir|chmod-docs]` — a step5 state under a
     `chmod 000` `sub`, and under a `chmod 000` `sub/docs` → `unreadable`, error
     `PermissionError`; modes restored in a `finally`.
  7. `test_docs_regular_file_is_absent` — `sub/docs` a regular file, root step5 → `active`
     (the `sub` step skipped).
  8. `test_state_that_is_not_an_object_is_unreadable[list-top|state-not-object]` → error
     `not-an-object`.
  9. `test_outside_target_reads_the_root_alone[root-step5|root-none]` → `active`, `none` (DD-9).
  10. `test_no_target_reads_the_root_alone` — `read_chain(root, None)`, sub step5 only → `none`.
  11. `test_missing_parent_directories_are_skipped` — sub step5, target
      `sub/newdir/deeper/x.py` (neither directory exists) → `active`.
- Fallback tags (14): `test_fallback_tag[absent|null|grok|claude|false|true|zero|empty-string|capital-grok|string-null|codex|empty-object|empty-list|nested-object]`.
  One step5 record per id; `Record.fallback` and the fourth `record=` subfield of
  `format_state_line` are asserted literally: `absent`, `null`, `grok`, `claude`,
  `invalid:false`, `invalid:true`, `invalid:0`, `invalid:%22%22`, `invalid:%22Grok%22`,
  `invalid:%22null%22`, `invalid:%22codex%22`, `invalid:%7B%7D`, `invalid:%5B%5D`,
  `invalid:%7B%22a%22%3A%5B1%2C2%5D%7D`; the line matches design D10's active ERE (held as a test
  constant, compiled with `re.fullmatch`); stripping `invalid:` and `urllib.parse.unquote` gives
  `json.dumps(value, separators=(",", ":"))` byte for byte.
- State line (11):
  1. `test_state_line_none` → `TDD-STATE: none`.
  2. `test_state_line_unreadable` → matches `^TDD-STATE: unreadable file=[^ ]+ error=[A-Za-z_-][A-Za-z0-9_-]*$`;
     the decoded file is absolute.
  3. `test_state_line_escape_and_blocker[single-available|single-exhausted|exhausted-then-available|available-then-exhausted|both-escaping|unavailable-and-exhausted]`
     → `codex-escape=` and `blocker=` pairs `no 1`, `yes 0`, `no 2`, `no 1`, `yes 0`, `yes 0`.
  4. `test_state_line_empty_values_encode_as_percent[empty-key|empty-status]` → the field reads
     `%`, the ERE matches, and the field decodes to `""`.
  5. `test_state_line_path_with_space_decodes` — a root named `a b "q"` → the state-file subfield
     decodes to the absolute path.
- CLI (9), each through `[sys.executable, str(JUDGE_PATH), …]` with `env=hermetic_env()`,
  `stdin=subprocess.DEVNULL`, `timeout=60.0`, unless in-process:
  1. `test_cli_state_verb[none|active|unreadable]` → exactly one stdout line, rc 0, matching its
     D10 form.
  2. `test_cli_usage_error[empty-root|missing-root|unknown-verb]` → rc 2, empty stdout.
  3. `test_cli_judge_exception_is_a_judge_error_line` — in-process `judge.main([...])` with
     `judge.judge` monkeypatched to raise `RuntimeError("boom")` → captured stdout
     `TDD-JUDGE: DENY kind=judge-error reason=RuntimeError: boom`, return 0.
  4. `test_cli_state_exception_prints_nothing` — in-process, `read_chain` raising → return 2,
     empty stdout.
  5. `test_cli_judge_on_a_chain_that_is_not_active` — no state → `DENY kind=judge-error`.
- Verdict line (3): `test_verdict_line_format[allow-inside|allow-outside|deny-control-chars]` —
  ALLOW `test=` root-relative, absolute outside the root; a reason holding `\n` and `\t` prints as
  one line with spaces.
- Venv (9):
  1. `test_venv_contained_rows[contained|venv-symlink-out|bin-symlink-out|cfg-missing|cfg-symlink|venv-out-bin-back-in]`
     → `True`, then `False` five times. Each row first asserts its own oracle (design D12 "the
     oracle is per row"): the two directory-symlink rows, `os.path.realpath(<mutated path>)`
     outside the root; `cfg-missing`, `os.path.lexists(cfg)` false; `cfg-symlink`,
     `os.path.islink(cfg)` and `not S_ISREG(os.lstat(cfg).st_mode)`; `venv-out-bin-back-in`,
     `realpath(.venv)` outside and `realpath(.venv/bin)` inside the root, and
     `S_ISREG(os.lstat(<venv>/pyvenv.cfg).st_mode)` true, so that conjunct 3 cannot be what
     denies (Deviation 6).
  2. `test_select_interpreter_takes_the_nearest_venv` — venvs at `hpw/.venv` and `.venv`, test in
     `hpw/tests` → `str(hpw/.venv/bin/python)`, unresolved.
  3. `test_select_interpreter_without_a_venv_uses_the_fallback`.
  4. `test_select_interpreter_never_skips_an_escaping_venv` — `hpw/.venv` escapes, root `.venv`
     contained → `venv-escapes-root` naming `hpw/.venv` and its realpath.
- Bounded run (4):
  1. `test_run_bounded_kills_the_process_group` — `/bin/sh` script `sleep 30 & echo $! > pid; wait`
     with a 1.0 s deadline → `timed_out`, returns within 6.0 s, and `os.kill(pid, 0)` raises
     `ProcessLookupError` after a 0.5 s grace.
  2. `test_name_map_runs_under_the_budget` — `monkeypatch.setattr(judge, "NAME_MAP", <that script>)`,
     no plan, `judge(…, budget_s=1.0)` → `timeout` within 6.0 s, no surviving `sleep` (D3 step 6,
     OD-K).
  3. `test_spent_budget_is_timeout_without_a_run` — `budget_s=0.0` with a marker shim venv →
     `timeout`, marker absent.
  4. `test_judge_source_has_no_subprocess_run` — the source text holds no `subprocess.run`.
- Resolution before W3 (4):
  1. `test_unmapped_path_is_no_test_resolved` (AC-2.7) — a plan whose one Task names another file;
     target `tools/x.py` → `no-test-resolved`; the reason contains the plan path, `matched none`
     and `name map: empty for tools/x.py`.
  2. `test_name_map_missing_test_is_test_missing` — target `hematology-paper-writer/tools/w.py`,
     no test file → `test-missing`, reason contains `author the failing test first`.
  3. `test_unreadable_plan_is_named_in_test_missing` (AC-2.8, route 1) — the plan holds
     `b"\xff\xfe"`; same target → `test-missing`, reason contains
     `impl-plan unreadable: UnicodeDecodeError`.
  4. `test_name_map_stderr_is_not_a_path` (design D3 step 6; Deviation 12) —
     `monkeypatch.setattr(judge, "NAME_MAP", <script>)` where the `/bin/sh` script prints
     `hematology-paper-writer/tests/test_w.py` to **stderr** only and exits 0; no plan; that file
     does not exist; target `hematology-paper-writer/tools/w.py` → `no-test-resolved`, reason
     contains `name map: empty for hematology-paper-writer/tools/w.py`. A reader of both streams
     would take the stderr line as a candidate and return `test-missing` (row R5).
- Scoring before W4 (5):
  1. `test_pytest_missing_denies[project-venv|gate-interpreter]` (AC-4.1) — a passing test;
     `build_venv(hpw, with_pytest=False)` as the project `.venv`, and, second id, no project venv
     with `fallback_interpreter=<that venv>/bin/python`, where the venv is built at
     `tmp_path / "gate-venv"` and the fixture root is `tmp_path / "root"`, so it is never the
     first id's project venv and never on the test's parent chain → `pytest-missing` each.
  2. `test_timeout_kind` (AC-4.5) — `fake_venv` whose `bin/python` is `sleeper(…, seconds=30)`,
     `budget_s=1.0` → `timeout` within 1.0 s + a 5.0 s margin, sleeper pid gone.
  3. `test_interpreter_that_cannot_start_is_no_summary` — `fake_venv` whose `bin/python` has mode
     `0o644` → `no-summary`, reason names `PermissionError` (the start error is the candidate's
     reason entry, Deviation 13).
  4. `test_escaping_venv_denies_before_any_run` (AC-3.2) — design D12 tree, `hpw/.venv` a symlink
     to `outside-venv` whose `bin/python` is a marker shim → `venv-escapes-root`; the marker file
     does not exist.
- Floor (4): `test_three_nine_floor[h_mad_tdd_judge|h_mad_wire_pin_gate|h_mad_wire_registry|h_mad_audit_gate]`
  — two assertions per module (v1.2, codex impl-plan audit c2 should): `ast.parse(source,
  feature_version=(3, 9))` over its file, and an actual import under the floor interpreter,
  `subprocess.run(["/usr/bin/python3", "-c", f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import {name}"], stdin=subprocess.DEVNULL, capture_output=True, text=True, env=hermetic_env(), timeout=60.0)`
  with `SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"`, asserting `returncode == 0`
  (the stderr is the failure message). `ast.parse` proves syntax only; the import proves every
  name the module evaluates at import time exists on 3.9. The test first asserts
  `Path("/usr/bin/python3").is_file()` (a missing floor interpreter fails, never skips). The three
  existing modules import this way today (executed at `c93da638`: `h_mad_wire_pin_gate ok`,
  `h_mad_wire_registry ok`, `h_mad_audit_gate ok`).

17 + 14 + 11 + 9 + 3 + 9 + 4 + 4 + 5 + 4 = 80.

**Expected RED split**: the module imports `h_mad_tdd_judge` at module level, so RED is one
collection error (`ModuleNotFoundError: No module named 'h_mad_tdd_judge'`), 0 items; the
`tdd_gate_support.py` additions are in the same RED commit and import cleanly. **After
GREEN**: 80 passed. `h-mad/tests/test_h_mad_portable_timeout.py` gains 2 collected nodes
(`…[h_mad_tdd_judge.py]` of its two `_SCANNED` parametrizations), which pass.
**Regression guards**: the full suite; `test_h_mad_portable_timeout.py`.

**Acceptance Criteria**:
- [ ] AC-2.7, AC-2.8 (route 1), AC-3.2, AC-4.1, AC-4.5: the tests named above.
- [ ] Design D1 floor, D2 chain rules, D4 containment, D6 bound, D10 line grammar, D13 tag table.

**Mutation rows** (Task 10): R3, R5 in `tdd_judge_resolution.json`; V1, V2, V3 in
`tdd_judge_venv.json`; K1 in `tdd_judge_scoring.json`; C1–C6 in `tdd_judge_chain.json` — 12 rows.

**Dependencies on other tasks**: Task 1

---

## Task 4: judge-summary-wire

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py`
**Test file**: `h-mad/tests/test_h_mad_tdd_judge.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_tdd_judge.py:score` → `h_mad_audit_gate._suite_summary`
**WIRE-PIN**: `h-mad/tests/test_h_mad_tdd_judge.py::test_scoring_kinds[red]`

**Description**: W4 (plan §"Connection enforcement"; design D7). Two edits: the import line becomes
`from h_mad_audit_gate import _SGR_RE, _SUMMARY_LINE_RE, _suite_summary  # noqa: E402`, and
`score`'s tagged line becomes `    summary = _suite_summary(proc_output)  # M:W4`. Nothing else
changes.

**Tests** (17 new collected items; 97 in the file). Fixtures use the hematology-paper-writer
layout: root state step5 `feat`, no plan, target `hematology-paper-writer/tools/w.py`, name-map
test `hematology-paper-writer/tests/test_w.py`.
1. `test_scoring_kinds[red|green|empty|skipped-only|import-error|red-with-subtest|green-with-subtest]`
   (7; AC-4.2, AC-4.3, AC-4.6). Test bodies: `assert False`; `assert True`; empty; one
   `@pytest.mark.skip` test; `import not_a_module_xyz` at top level; a `subtests.test("a")` block
   holding `assert True` then `assert False`; the same block then `assert True`. Expected
   `ALLOW red-measured`, `test-passing`, `no-tests-ran`, `no-tests-ran`, `pytest-error` (reason
   contains `import` and `inside the test body`), `ALLOW red-measured`, `test-passing`.
2. `test_rc_selects_nothing[failed-line-rc0|silent-rc1]` (2; AC-4.4) — `fake_venv` shims printing
   `1 failed in 0.01s` then `exit 0` → ALLOW; printing nothing then `exit 1` → `no-summary`.
3. `test_stray_failed_line_after_a_passing_summary_is_test_passing` (1; plan §"Regression census",
   beside AC-4.4) — shim prints `2 passed in 0.1s`, then `1 failed`, exit 0 → `test-passing`.
4. `test_quoted_no_module_phrase_is_not_pytest_missing` (1; DD-11) — shim prints
   `E   assert "No module named pytest" in out`, then `1 failed in 0.01s`, exit 1 → ALLOW.
5. `test_whole_line_no_module_is_pytest_missing_even_after_red` (1; DD-11's stated residual) —
   shim prints `x: No module named pytest`, then `1 failed in 0.01s` → `pytest-missing`.
6. `test_name_map_source_allows_via_the_cli[absolute|relative]` (2; AC-2.6) — the `judge` verb with
   `--target` absolute and root-relative → exactly
   `TDD-JUDGE: ALLOW kind=red-measured source=name-map test=hematology-paper-writer/tests/test_w.py`.
7. `test_contained_venv_shim_runs_pytest` (1; AC-3.1) — design D12 tree with the contained marker
   shim → ALLOW; the marker file holds the shim's path.
8. `test_real_venv_interpreter_symlink_is_accepted` (1; AC-3.3) — `build_venv(hpw, with_pytest=True)`,
   whose `bin/python` symlinks to the builder outside the root → ALLOW.
9. `test_unreadable_plan_with_a_passing_name_map_test_is_test_passing` (1; AC-2.8, route 2) →
   `test-passing`, reason contains `impl-plan unreadable`.

7 + 2 + 1 + 1 + 1 + 2 + 1 + 1 + 1 = 17.

**Expected RED split**: 15 failing and 2 passing among the new items; the 80 Task-3 items pass.
Before the wire every run past rule 2 reads `no-summary`, so items 1, 3, 4, 6, 7, 8, 9 and
`failed-line-rc0` fail on their verdict assertions (7 + 1 + 1 + 2 + 1 + 1 + 1 + 1 = 15).
`silent-rc1` passes (it expects `no-summary`) and item 5 passes (rule 2 precedes the summary).
The rows that show those two failing: K3B (`silent-rc1` under rc scoring reads `red-measured`) and
K5 (rule 2 made to yield to a parsed summary: item 5 reads `red-measured`).
**WIRE-PIN RED reason**: `judge()` exists and returns `Verdict("DENY", "no-summary", …)` for the
RED fixture, so the assertion `verdict.decision == "ALLOW" and verdict.kind == "red-measured"`
fails on the caller's return value; the module imports, so no import error is involved.
**Regression guards**: the 80 Task-3 items; `test_h_mad_audit_suite_gate.py`.
**Wire-scoped revert**: the `# M:W4` line back to `    summary = None  # M:W4` → the pin fails.
Row W4R. **Force-fire**: `    summary = _suite_summary("1 failed in 0.01s")  # M:W4` →
`test_scoring_kinds[green]` reads RED and fails. Row W4F. **Callee-side**: `failed += 0` at
`# M:W4C` in `h_mad_audit_gate.py`, scored on the judge's `[red]` only. Row W4C.

**Acceptance Criteria**:
- [ ] AC-2.6: item 6. AC-2.8 (route 2): item 9. AC-3.1: item 7. AC-3.3: item 8.
- [ ] AC-4.2: item 1's seven ids. AC-4.3 and AC-4.6: `[import-error]`. AC-4.4: item 2.

**Mutation rows** (Task 10): K2, K3, K3B, K4, K5 in `tdd_judge_scoring.json`; W4R, W4F, W4C in
`tdd_judge_wiring.json` — 8 rows.

**Dependencies on other tasks**: Task 3

---

## Task 5: judge-plan-wire

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py`
**Test file**: `h-mad/tests/test_h_mad_tdd_judge.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_tdd_judge.py:resolve` → `h_mad_wire_pin_gate._parse_tasks`
**WIRE-PIN**: `h-mad/tests/test_h_mad_tdd_judge.py::test_hemasuite_layout_resolves_from_the_task`

**Description**: W3 (plan §"Connection enforcement"; design D3). Two edits:
`from h_mad_wire_pin_gate import _parse_tasks  # noqa: E402` lands after the audit-gate import, and
the plan loop's tagged line becomes `        tasks = _parse_tasks(text)  # M:W3`. Matching,
authority, candidates and notes already exist (Task 3); they now see Tasks.

**Tests** (16 new collected items; 113 in the file). The plan lives at
`docs/01-plan/features/feat.impl-plan.md` beside the root state; paths in it are relative to
`hematology-paper-writer/` unless stated. No fixture below creates `hematology-paper-writer/tests/test_w.py`
unless it says so, so the name map never resolves in the pre-wire state.
1. `test_hemasuite_layout_resolves_from_the_task` (1; AC-2.1) — Task Production
   `` `tools/review_round/guideline_excerpts.py`, `cli/_parser.py` ``, Test
   `` `tests/test_certificate_lock_removed.py` `` (RED); write to `hematology-paper-writer/cli/_parser.py`
   → `ALLOW`, `source == "impl-plan"`, test `hematology-paper-writer/tests/test_certificate_lock_removed.py`.
2. `test_label_spelling_resolves_the_same[production-file|production-files|production|test-file|test-files|test|test-colon-inside]`
   (7; AC-2.2) — one spelling varied per id, the other label standard; test `tests/test_from_plan.py`
   (RED) → `ALLOW source=impl-plan`.
3. `test_tests_prose_line_contributes_no_candidate` (1; AC-2.2) — the Task also carries
   ``**Tests** (5 functions, `tests/test_absent.py`)`` → `ALLOW`, the absent file never named.
4. `test_none_valued_production_does_not_match` (1; AC-2.3) — Production
   `` none (writes `docs/x/derive_readings.py`) ``, Test `tests/test_t.py` (absent); write to
   `docs/x/derive_readings.py` (root-relative) → `no-test-resolved`, never `test-missing`.
5. `test_several_candidates_first_red_allows` (1; AC-2.4) — Tasks 1 and 2 name `tools/w.py`, tests
   `tests/test_one.py` (GREEN) and `tests/test_two.py` (RED) → ALLOW naming `test_two.py`.
6. `test_several_candidates_all_green_names_both` (1; AC-2.4) → `test-passing`, reason names both
   files and `matched`.
7. `test_task_match_is_authoritative_over_the_name_map` (1; AC-2.5) — Task test absent,
   `hematology-paper-writer/tests/test_w.py` exists and is RED → `test-missing`.
8. `test_mixed_candidates_missing_then_red_allows_the_red` (1; D3 step 5) → ALLOW naming Task 2's.
9. `test_mixed_candidates_missing_then_green_denies_test_passing` (1) → `test-passing`, reason
   names Task 1's test as `missing`.
10. `test_candidate_outside_root_is_dropped_and_noted` (1) — the only Test entry is
    `../../outside/test_x.py` → `test-missing`, reason contains `candidate outside root dropped`.

1 + 7 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 = 16.

**Expected RED split**: 15 failing and 1 passing among the new items; the 97 earlier items pass.
Before the wire no Task matches, so each fixture falls to the name map, which finds no file:
items 1, 2, 3, 5, 6, 8, 9, 10 read `test-missing` or `no-test-resolved` where they expect ALLOW,
`test-passing` or the dropped-candidate note, and item 7 reads ALLOW through the name map where it
expects `test-missing`. Item 4 passes (it expects `no-test-resolved`, which the unwired judge also
returns); it is a guard that turns discriminating once Tasks match, and row R2 shows it failing.
**WIRE-PIN RED reason**: `judge()` returns `Verdict("DENY", "test-missing", …)` naming
`hematology-paper-writer/tests/test__parser.py`, so the assertion on `decision`, `source` and
`test` fails on the caller's return value; no import error is involved.
**Regression guards**: the 97 earlier items; `test_h_mad_parse_tasks_paths.py`.
**Wire-scoped revert**: `        tasks = []  # M:W3` → the pin fails. Row W3R. **Force-fire**:
`        tasks = [dict(t, production=[]) for t in _parse_tasks(text)]  # M:W3` → item 7 inverts
(the name-map RED test ALLOWS). Row W3F. **Callee-side**: `_PATHS_FIELD_RE`'s `Production` label
alternative → `Productionx` in `h_mad_wire_pin_gate.py`, scored on the pin only. Row W3C.

**Acceptance Criteria**:
- [ ] AC-2.1: item 1. AC-2.2: items 2 and 3. AC-2.3: item 4. AC-2.4: items 5 and 6. AC-2.5: item 7.

**Mutation rows** (Task 10): R1, R2, R4 in `tdd_judge_resolution.json`; W3R, W3F, W3C in
`tdd_judge_wiring.json` — 6 rows.

**Dependencies on other tasks**: Task 2, Task 4

---

## Task 6: codex-gate-judge

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py` (new), `h-mad/tests/test_h_mad_codex_runtime.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `h_mad_tdd_judge.judge`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_gate_kind[test-passing]`
**WIRE 2**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `h_mad_tdd_judge.read_chain`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py::test_root_step5_governs_a_subproject_with_its_own_state`

**Description**: Design §D8 except the shell branch (Task 7); W1 and W5a. The task is `wiring`
because it carries the two wires; the payload-`cwd` base, the crash guard and the non-blocking
state read are new behaviour landed in the same edit, and their RED split is stated per test below.
- **Removed**: `_target_phase5_status`, `_derived_test`, `_test_exit` (each defined once in the
  hook at `f6b258f0`).
- **`_read_regular_text(path) -> str`**: `os.open(path, os.O_RDONLY | os.O_NONBLOCK)`, `os.fstat`,
  a non-`S_ISREG` mode raises `OSError("not a regular file")`, else read that descriptor and decode
  UTF-8; close in a `finally`.
- **`_state_status`**:
  ```python
      try:
          text = _read_regular_text(state_file)  # M:G4
          state = json.loads(text)
      except (OSError, UnicodeDecodeError, json.JSONDecodeError):
          return "unknown"
  ```
- **`_load_judge()`** inserts `str(Path(__file__).resolve().parents[1] / "scripts")` at
  `sys.path[0]` when absent, imports `h_mad_tdd_judge` once and caches the module.
- **`_payload_cwd_base(root, cwd) -> Path`**:
  ```python
      if isinstance(cwd, str) and cwd:  # M:G1
          c = Path(cwd).expanduser().resolve()
          if c.is_dir() and (c == root or root in c.parents):  # M:G7
              return c
      return root
  ```
- **`_relative_target(root, raw, cwd=None)`**: an absolute `raw` resolves as today; a relative one
  as `(_payload_cwd_base(root, cwd) / candidate).resolve()`.
- **`main`** keeps `--self-check` unchanged, then:
  ```python
      try:
          return _main_guarded()
      except Exception as exc:  # M:G2
          return _deny(f"H-MAD Phase 5 gate raised {type(exc).__name__}: {exc}; refusing fail-closed. kind=judge-error")
  ```
  `_main_guarded` is today's body from `payload = _payload()` on, with the write loop:
  ```python
      for raw in targets:  # M:G5
          resolved = _relative_target(root, raw, payload.get("cwd"))
          if resolved is None:
              if phase5_status in {"active", "unknown"}:
                  return _deny("H-MAD Phase 5 write target is outside or unreadable; refusing fail-closed.")
              continue
          absolute, relative = resolved
          judge = _load_judge()
          chain = judge.read_chain(root, absolute)  # M:W5A
          if chain.value == "unreadable":
              return _deny(f"H-MAD state governing this write is unreadable ({chain.error_file}: {chain.error}); refusing fail-closed. kind=judge-error")
          if chain.value != "active" or not _is_production_python(relative):
              continue
          verdict = judge.judge(root, absolute, chain.records)  # M:W1
          if verdict.decision != "ALLOW":
              return _deny(f"H-MAD Phase 5 requires a failing test before {relative}: kind={verdict.kind}; {verdict.reason}")
      return 0
  ```
  The chain read runs for every write target whatever `_any_phase5_status` returned (DD-12).

**Tests** (19 new collected items in the new module; 1 changed assertion in
`test_h_mad_codex_runtime.py`). Each gate run is
`subprocess.run([sys.executable, str(CODEX_GATE)], input=json.dumps(payload), capture_output=True,
text=True, cwd=<root>, env=hermetic_env(CODEX_PROJECT_DIR=str(root)), timeout=60.0)` with
`CODEX_GATE = Path(__file__).resolve().parents[1] / "hooks" / "h-mad-codex-tdd-gate.py"`, and a
helper returns `("allow", "")` for rc 0 with stdout empty or `{}`, `("deny", reason)` for rc 0 with
one JSON deny, `("invalid", stdout)` otherwise.
1. `test_codex_gate_kind[red-measured|no-test-resolved|test-missing|venv-escapes-root|pytest-missing|pytest-error|no-tests-ran|no-summary|test-passing|timeout|judge-error]`
   (11; AC-1.2 Codex half, AC-5.4). `apply_patch` of `hematology-paper-writer/tools/w.py` under a
   root step5 record. Per id: RED name-map test → allow; `tools/x.py` (unmapped) →
   `kind=no-test-resolved`; no test file; `hpw/.venv` symlinked outside; `build_venv(…, with_pytest=False)`
   as `hpw/.venv`; top-level import error; empty test file; `fake_venv` printing nothing, exit 1;
   GREEN test; `fake_venv` whose `bin/python` is `sleeper(…, seconds=90)` (`timeout=120.0`,
   about 40 s at the default budget, and the sleeper pid is gone afterwards, which it would not
   be on its own for another 50 s); a tree-B copy (`B/hooks/h-mad-codex-tdd-gate.py` copied from the worktree,
   `B/scripts/h_mad_tdd_judge.py` = `raise ImportError("broken judge for AC-5.4")`) → rc 0,
   stdout parses as one JSON deny whose reason contains `kind=judge-error`. Each deny reason
   contains `kind=` followed by its own id.
2. `test_root_step5_governs_a_subproject_with_its_own_state` (1; AC-5.2) — root step5,
   `hematology-paper-writer/docs/.bkit-memory.json` = `{"orchestrator_state": {}}`, GREEN name-map
   test → deny, `kind=test-passing`.
3. `test_payload_cwd_base_resolves_a_subproject_relative_target` (1; AC-5.1) — a root plan whose
   Task names `tools/review_round/guideline_excerpts.py` with a RED test; payload
   `"cwd": <tmp>/alias/hematology-paper-writer`, where `<tmp>/alias` is a symlink to the root (an
   unresolved spelling of a directory inside the resolved root; the test asserts
   `os.path.realpath(cwd) != cwd`); patch target `tools/review_round/guideline_excerpts.py` → allow.
4. `test_payload_cwd_deny_names_the_prefixed_path` (1; AC-5.1) — the same with a GREEN test → the
   reason contains `hematology-paper-writer/tools/review_round/guideline_excerpts.py`.
5. `test_payload_cwd_outside_the_root_falls_back_to_the_root` (1) — `cwd` a directory outside the
   root, target `hematology-paper-writer/tools/w.py` with a RED name-map test → allow.
6. `test_fifo_state_on_the_chain_denies_a_write_without_blocking` (1; DD-12) — `os.mkfifo` at
   `hematology-paper-writer/docs/.bkit-memory.json`, write payload → deny containing
   `unreadable`, within 1.0 s (`timeout=5.0`, Convention 5).
7. `test_fifo_state_off_the_chain_denies_shell_without_blocking` (1; DD-12) — FIFO at
   `other/docs/.bkit-memory.json`, `shell_command` `ls` → deny containing
   `state is unreadable`, within 1.0 s.
8. `test_unsearchable_docs_on_the_chain_denies_although_the_scan_is_inactive` (1; OD-I) — a step5
   state under a `chmod 000` `hematology-paper-writer/docs`, no root state, write to
   `hematology-paper-writer/tools/w.py` → deny, `kind=judge-error`; mode restored in a `finally`.
9. `test_codex_gate_keeps_no_private_resolver` (1) — the hook source holds none of
   `_target_phase5_status`, `_derived_test`, `_test_exit`, `h_mad_derive_test_path.sh`.

11 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 = 19.

**Changed existing assertion** (AC-5.3): in
`test_codex_hook_rejects_pytest_no_tests_collected_as_red`, `assert "exit 1" in …` becomes
`assert "no-tests-ran" in …`. It pinned the rc-scoring FR-4 removes.

**Expected RED split**: 17 failing and 2 passing among the new items; in
`test_h_mad_codex_runtime.py`, 1 failing (the changed assertion) and 23 passing (24 collected at
`f6b258f0`).
- Item 1: 10 fail (no deny reason from today's gate carries `kind=`; the `venv-escapes-root`,
  `pytest-missing`, `no-summary` and `timeout` fixtures are allowed or denied without it, since
  today's gate runs `sys.executable` and ignores the venv; the tree-B copy of today's gate never
  imports the judge and denies "no derived test file exists"). `[red-measured]` passes: today's
  gate already allows a RED name-map test.
- Items 2, 3, 4: fail (today: nearest-state allow; root-relative deny; unprefixed reason).
- Item 5: passes (today ignores `cwd` and resolves against the root, as the new rule does here);
  row G7 shows it failing.
- Items 6 and 7: fail on the elapsed-time assertion (today's `read_text` blocks on the FIFO until
  the 5.0 s `timeout=` kills it).
- Item 8: fails, because today's gate crashes. `_target_phase5_status` calls
  `state_file.is_file()`, and on a `chmod 000` parent `Path.is_file()` raises `PermissionError`
  rather than returning `False`, so the hook exits rc 1 with a traceback and empty stdout; the
  helper reads `("invalid", "")` and the deny assertion fails. Executed at `a1478ad3` under
  `/opt/anaconda3/bin/python`: a `tempfile.TemporaryDirectory` root holding a step5 state in
  `hematology-paper-writer/docs` at mode `000`, payload
  `{"tool_name": "apply_patch", "tool_input": {"patch": "*** Update File: hematology-paper-writer/tools/w.py\n"}}`,
  env `PATH=/usr/bin:/bin`, `HOME`, `CODEX_PROJECT_DIR=<root>` → `rc 1`, stdout `''`, last
  stderr line `PermissionError: [Errno 13] Permission denied: '…/hematology-paper-writer/docs/.bkit-memory.json'`
  (mode restored, directory removed).
- Item 9: fails (the three functions exist).
**WIRE-PIN 1 RED reason**: today's gate denies the GREEN fixture with "returned pytest exit 0, not
test-failure exit 1", so the assertion that the stdout deny reason contains `kind=test-passing`
fails on the gate's output. The gate runs as a subprocess, so no import error is involved.
**WIRE-PIN 2 RED reason**: today's gate reads the nearer, step5-free state and allows (rc 0, empty
stdout), so the deny assertion fails on the gate's output.
**Regression guards**: the other 23 tests of `test_h_mad_codex_runtime.py` unmodified, including
`test_codex_hook_scopes_nested_state_to_the_target_project`,
`test_codex_hook_resolves_git_root_from_nested_cwd` (AC-5.3),
`test_codex_hook_fails_closed_on_malformed_state` (reason contains `state`),
`test_codex_hook_rejects_untrusted_executable_paths` and
`test_codex_hook_self_check_reports_machine_readable_pass`; `--self-check` →
`CODEX-TDD-GATE: PASS`.
**Wire-scoped reverts**: `        verdict = judge.Verdict("DENY", "judge-error", "wire removed", "", None)  # M:W1`
→ `[red-measured]` is denied; row W1R. `        chain = judge.Chain("none", (), None, "")  # M:W5A`
→ WIRE-PIN 2 allows again; row W5AR. **Force-fires**:
`        verdict = judge.Verdict("ALLOW", "red-measured", "", "impl-plan", None)  # M:W1` → WIRE-PIN 1
allows; row W1F. `        chain = judge.Chain("active", (judge.Record("forced", "available", root / "docs" / ".bkit-memory.json", "absent"),), None, "")  # M:W5A`
→ the sibling write of `tests/test_h_mad_codex_runtime.py::test_codex_hook_scopes_nested_state_to_the_target_project`
is denied; row W5AF.

**Acceptance Criteria**:
- [ ] AC-1.2 (Codex half): item 1. AC-5.1: items 3 and 4. AC-5.2: item 2. AC-5.3: the changed
  assertion and the two unmodified tests. AC-5.4: `[judge-error]`.

**Mutation rows** (Task 10): G1, G2, G4, G5, G7, W1R, W1F, W5AR, W5AF in
`codex_gate_judge_wiring.json` — 9 rows.

**Dependencies on other tasks**: Task 5

---

## Task 7: codex-shell-venv

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`, `docs/03-analysis/probes/codex-tdd-gate-defects/shell_differential.py` (new)
**Test file**: `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`, `h-mad/tests/tdd_gate_support.py` (`shell_corpus` lands in the RED commit)
**Task shape**: `new-behaviour`

**Description**: Design §D8 "Shell policy" and "Differential"; spec FR-3 shell policy, AC-3.4,
AC-3.5, AC-3.6; plan §"Guard narrowing: shell policy".
- New helper:
  ```python
  def _contained_venv_executable(token: str, root: Path, cwd: object) -> Path | None:
      if "/" not in token:
          return None
      p = Path(os.path.normpath(os.path.join(str(_payload_cwd_base(root, cwd)), os.path.expanduser(token))))  # M:G10
      if not (p.name.startswith("python") and p.parent.name == "bin" and p.parent.parent.name == ".venv"):
          return None
      if not p.is_file():
          return None
      if not _load_judge().venv_contained(p.parent.parent.parent, root):  # M:G6
          return None
      return p  # M:G3
  ```
- `_safe_shell_command(command, root=None, cwd=None)` changes its signature and one line:
  `    resolved_executable = (_contained_venv_executable(argv[0], root, cwd) if root is not None else None) or _trusted_executable(argv[0])  # M:G9`.
  Every argv rule after it is unchanged; `--self-check` passes `root=None`, so the lookup is inert
  there.
- `_main_guarded` passes `payload.get("cwd")`:
  `if command and phase5_status == "active" and not _safe_shell_command(command, root, payload.get("cwd")):`.
- **`tdd_gate_support.shell_corpus(tmp, scripts_dir) -> list[CorpusRow]`** builds design D12's
  tree (git-initialised root, one step5 record, `hematology-paper-writer/.venv` from
  `build_venv(…, with_pytest=True)`, `python-evil` in its `bin/`, RED
  `hematology-paper-writer/tests/test_x.py`, `outside-venv`, a `sibling/` directory) and returns
  one row per cell: 5 venv states (contained, `venv-symlink-out`, `bin-symlink-out`,
  `cfg-missing`, `cfg-symlink`, each on its own tree copy) × 8 spellings (absolute into the
  venv; root-prefixed from the root `cwd`; `.venv/bin/python` from the sub-project `cwd`;
  `./.venv/bin/python`; `../hematology-paper-writer/.venv/bin/python` from `sibling/`; the doubled
  root-prefixed spelling from the sub-project `cwd`; `.venv/bin/python<X.Y>` with `<X.Y>` from
  `sys.version_info`; `.venv/bin/python-evil`) × 6 argv (`-m pytest tests/test_x.py`;
  `-c "open('x','w')"`; `-m pip install x`; `script.py`; `-m pytest tests/test_x.py; touch y`;
  `<scripts_dir>/h_mad_state_write.py <root>/docs/.bkit-memory.json --set x=y`) = 240 rows; plus
  the outside venv named by its absolute token × the 6 argv = 6 rows; plus the 5 control rows
  (`/usr/bin/python3 -m pytest …`, `/usr/bin/python3 <scripts_dir>/h_mad_state_write.py …`,
  `venv/bin/python -m pytest …`, `.venv/bin/pytest …`, `python3 -m pytest …`) = 251 rows. Each
  row carries its `expected_new` verdict: allow exactly for the 14 cells {contained} × {the 7
  spellings that resolve into it} × {`-m pytest`, `h_mad_state_write.py`} and the 3 control rows
  `/usr/bin/python3 -m pytest`, `/usr/bin/python3 … h_mad_state_write.py` and
  `python3 -m pytest`; deny for the other 234. Every run uses `PATH=/usr/bin:/bin` so the bare
  `python3` control resolves to `/usr/bin/python3` (in `TRUSTED_BIN_DIRS`).
- **`shell_differential.py --old HOOK --new HOOK`** (probe, stdlib plus `tdd_gate_support`) runs
  both hooks over the corpus and prints one `SHELLDIFF: softened <row>` or
  `SHELLDIFF: tightened <row>` line per changed row and
  `SHELLDIFF: DONE rows=251 softened=N tightened=N unexpected=N`. The old hook is
  `git show "$BASE_SHA":h-mad/hooks/h-mad-codex-tdd-gate.py`, written to a scratch tree whose
  `scripts` is a symlink to the worktree's `h-mad/scripts`, so both hooks' `_safe_hmad_script`
  resolve the same scripts root. **Probe-run step**: expected `softened=14 tightened=0
  unexpected=0`; the reading goes to the analysis document §"Shell-policy differential".

**Tests** (18 new collected items; 37 in the module):
1. `test_shell_venv_token[sub-cwd-contained|root-cwd-contained|sub-cwd-escaping|root-cwd-escaping|doubled-path|c-sub-cwd-contained|c-root-cwd-contained|c-doubled-contained|c-sub-cwd-escaping|c-root-cwd-escaping|c-doubled-escaping]`
   (11; AC-3.4): the two contained `-m pytest` pairs allow; the two escaping ones deny; the doubled
   path denies; the six `-c "open('x','w')"` cells deny.
2. `test_shell_control_allowlist_under_a_venv[contained-venv|usr-bin-python3-control|escaping-venv|script-outside-scripts]`
   (4; AC-3.6): allow, allow, deny, deny. `[usr-bin-python3-control]` is
   `/usr/bin/python3 -m pytest tests/test_x.py` from the sub-project `cwd`. `[escaping-venv]` is
   `.venv/bin/python -m pytest tests/test_x.py` from the sub-project `cwd` with the sub-project's
   `.venv` a symlink to `outside-venv`. `[script-outside-scripts]` is
   `.venv/bin/python <root>/hematology-paper-writer/h_mad_wire_registry.py verify` from the
   sub-project `cwd`, a contained venv, and the script path absolute (v1.2: v1.1 ran a `tools.py`,
   which `_safe_hmad_script` also rejects because `SAFE_HMAD_SCRIPT_OPTIONS` has no `tools.py` key,
   so no single mutant could make that cell fail; a script named like an allowed H-MAD script but
   outside `scripts/` leaves the scripts-root rule as the one guard, row G11).
3. `test_venv_token_keys_on_the_lexical_name` (1): a contained venv whose `bin/python` symlinks to
   `/bin/cat`, command `.venv/bin/python notes.txt` from the sub-project `cwd` → deny (the lexical
   `python*` rules reject a non-script argument; a realpath name `cat` would reach
   `READ_ONLY_COMMANDS` and allow).
4. `test_shell_policy_corpus_allows_exactly_the_expected_rows` (1): every corpus row through the
   worktree hook; the set of allowed rows equals the set whose `expected_new` is allow.
5. `test_venv_token_still_obeys_the_argv_rules` (1): a contained venv, `shell_command`
   `.venv/bin/python -c pass` from the sub-project `cwd` → deny. The test first asserts its own
   oracle, `SIMPLE_SHELL_COMMAND.fullmatch(command)` is truthy (read from the loaded hook), so the
   deny comes from the argv rules after the venv lookup, not from the lexical subset. This is the
   discriminating twin of item 1's six `-c "open('x','w')"` cells, which the lexical subset
   rejects before any executable is resolved (`(` and `)` are outside
   `[A-Za-z0-9_./:@%+=,'" \t-]+`; executed at `a1478ad3`: `fullmatch` → `False` for that command,
   `True` for `.venv/bin/python -c pass` and for `.venv/bin/python -m pytest tests/test_x.py`).

11 + 4 + 1 + 1 + 1 = 18.

**Expected RED split**: 4 failing and 14 passing. Today `_trusted_executable` refuses every
`.venv/bin/…` token (its parent is not in `TRUSTED_BIN_DIRS`), so the two contained allow rows of
item 1, `[contained-venv]` of item 2 and item 4 fail; the 9 other item-1 rows, the 3 other item-2
rows, item 3 and item 5 already deny (or allow, for the control) and pass as guards.
**Passing at RED, and the row that shows each one failing** (Task 10 §"Initially-green guards"):
`[sub-cwd-escaping]` G6, `[root-cwd-escaping]` G6B, item 2 `[escaping-venv]` G6C, item 2
`[usr-bin-python3-control]` G9 (the `or _trusted_executable(argv[0])` fallback removed), item 2
`[script-outside-scripts]` G11 (the pre-existing scripts-root rule, an untagged line), item 1
`[doubled-path]` G10 (the token joined to the root instead of the payload `cwd` base), item 3 G3,
item 5 G8. G6C, G9, G10 and G11 were each killed on a scratch copy (Task 10 §"Initially-green
guards").
**No coverage claimed (v1.2, codex impl-plan audit c2 must 3): the six `c-*` cells of item 1.**
They stay because spec AC-3.4 names them, and they claim conformance to AC-3.4's table only, not
discrimination of any guard: two independent rules deny each of them (the lexical subset rejects
`(` and `)` before any executable is resolved, and behind it the containment and trusted-directory
rules deny the escaping cells while the argv rules deny a contained `python -c`), so no
single-site mutant can make one of them fail, and no row is authored for them. The discrimination
claim for the venv branch's argv rules is item 5's, row G8 (OQ-I4).
**Regression guards**: `test_codex_hook_rejects_untrusted_executable_paths` passes unmodified
(AC-3.5); the Task-6 items; `--self-check`.

**Acceptance Criteria**:
- [ ] AC-3.4: item 1. AC-3.5: the guard above. AC-3.6: item 2 and the corpus rows.
- [ ] The probe reads `softened=14 tightened=0 unexpected=0`, published with its sha.

**Mutation rows** (Task 10): G3, G6, G6B, G6C, G8, G9, G10, G11 in `codex_gate_judge_wiring.json`
— 8 rows.

**Dependencies on other tasks**: Task 6

---

## Task 8: claude-gate-rewrite

**Production file**: `h-mad/hooks/h-mad-tdd-gate.sh`, `docs/03-analysis/probes/codex-tdd-gate-defects/dd7_differential.py` (new)
**Test file**: `h-mad/tests/test_h_mad_tdd_gate_judge.py` (new), `h-mad/tests/test_h_mad_tdd_gate_codex.py`, `h-mad/tests/test_h_mad_tdd_gate_state_resolution.py`, `h-mad/tests/tdd_gate_support.py` (`hook_form`, `decision` and `dd7_cells` land in the RED commit)
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-tdd-gate.sh:JOUT` → `h_mad_tdd_judge.main` (`judge` verb)
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_tdd_gate_judge.py::test_new_production_file_with_passing_test_is_refused`
**WIRE 2**: `h-mad/hooks/h-mad-tdd-gate.sh:_read_state` → `h_mad_tdd_judge.main` (`state` verb)
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_tdd_gate_judge.py::test_subproject_step5_under_root_step3_is_governed`
**WIRE 3**: `h-mad/hooks/h-mad-tdd-gate.sh:_find_judge` → `h-mad/scripts/h_mad_tdd_judge.py` (hook-relative path)
**WIRE-PIN 3**: `h-mad/tests/test_h_mad_tdd_gate_judge.py::test_symlinked_hook_runs_its_own_trees_judge`

**Description**: Design §D9 top to bottom; W2, W5b, W6; spec FR-6 and AC-6.1–AC-6.15. The task is
`wiring` because it carries the three wires; the payload read, the canonical target, the fast
path, the refusal function and the trap are new behaviour in the same rewrite, and each test's RED
reason is stated below.

**Precondition (FR-0, AC-6.7).** Task 0 item 2 recorded a `v0.out` line with
`READING=E1_BLOCKS` or `READING=E1_DOES_NOT_BLOCK` and `CHOSEN=a` or `CHOSEN=b`. Otherwise this
task does not start and the feature halts to the operator (plan R1): every refusal test below
asserts the chosen form, so none of them can be written before the form is known. The literal is
`readonly REFUSAL_FORM=a` when `CHOSEN=a` and `readonly REFUSAL_FORM=b` when `CHOSEN=b`. The test
module's docstring quotes the `v0.out` line (AC-6.6).

**Design v1.3 (v1.2 of this plan; answers v1.1's precondition 2 and OQ-I3, now lifted).** Design
v1.3 §D9 adopted remedy (i): step 3 keeps `RAW_TARGET`, decides root membership lexically, and
matches the directory exemptions against the root-relative `DIR_SUBJECT` inside the root and
against both spellings outside it (Deviation 16). The DD-7 differential gains the root shapes
`<tmp>/tests/repo` and `<tmp>/fixtures/repo` (126 cells). v1.1's executed reading still holds
for today's gate and is now a RED reading of item 34: root `<tmp>/tests/repo`, positional `x.py`
→ rc 1 (gated today); positional `<tmp>/tests/repo/x.py` → rc 0 (exempt today). Items 21–23, the
probe's expected sets and row H15 are re-derived below; items 21 and 22 keep their outcomes.

**Script order and landed lines** (shebang `#!/bin/bash`; must run under `/bin/bash` 3.2.57; each
tagged line verbatim and once):
1. `set -euo pipefail`; the `readonly REFUSAL_FORM=a` or `readonly REFUSAL_FORM=b` literal; `DECIDED=""`; `TRC=0 SRC=0 JRC=0`;
   `JUDGE=""`; the functions below; then `trap _on_exit EXIT  # M:T1`, before the first fallible
   command.
2. Functions:
   ```bash
   _allow() { DECIDED=allow; exit 0; }
   _refuse() {
     MSG="[H-MAD-TDD-GATE] BLOCK kind=$1: $2"
     printf '%s\n' "$MSG" >&2
     if [ "$REFUSAL_FORM" = b ]; then
       printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$(_json_str "$MSG")" || exit 2  # M:H5B
       DECIDED=refused
       exit 0
     fi
     DECIDED=refused
     exit 2  # M:H5A
   }
   _on_exit() {
     local rc=$?
     trap - EXIT
     set +euo pipefail
     case "$DECIDED" in
       allow) exit 0 ;;
       refused) exit "$rc" ;;
     esac
     _refuse judge-error "gate exited rc=$rc before deciding"  # M:T2
     exit 2
   }
   _lexists() { [ -e "$1" ] || [ -L "$1" ]; }  # M:H7
   ```
   `_json_str` escapes `\`, then `"`, then maps `[[:cntrl:]]` to a space. `_pct_decode` is
   `[ "$1" = % ] && return 0; printf '%b' "${1//%/\\x}"`. `_absent_at D` returns 1 when
   `_lexists "$D/docs/.bkit-memory.json"`; returns 1 unless `[ -x "$D" ]` (no mutation row,
   Deviation 7); returns 0 when `! _lexists "$D/docs"`; then
   `  [ -x "$1/docs" ] && return 0  # M:H10`; then returns 0 when `[ -e "$1/docs" ] && [ ! -d "$1/docs" ]`;
   else 1.
3. **Target** (step 2, DD-13). `READER` is an inline Python program: a tty on fd 0 reads nothing;
   otherwise `select.select` plus `os.read` until EOF or 2.0 s in total; 0 bytes read → exit 0
   printing nothing; UTF-8 JSON object → the first non-empty string of
   ```python
       for value in (tool_input.get("file_path"), payload.get("file_path"), payload.get("path")):  # M:H1
   ```
   (with `tool_input` the payload's `tool_input` when it is a dict, else `{}`); no target from ≥ 1
   byte → the single line `    sys.exit(4)  # M:H12`; a control character (`ord < 32` or 127) →
   exit 3. Then `TP=$(python3 -c "$READER") || TRC=$?` and
   ```bash
   if [ "$TRC" = 0 ] && [ -n "$TP" ]; then
     TARGET_PATH=$TP  # M:H2
   elif [ "$TRC" = 0 ]; then
     TARGET_PATH=${1:-}
   else
     TARGET_PATH=""
   fi
   ```
4. **Canonical target and root membership** (DD-7; design v1.3 §D9 step 3):
   ```bash
   RAW_TARGET=$TARGET_PATH
   ROOT_ABS=$(cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null && pwd -P) || ROOT_ABS=""
   if [ -n "$TARGET_PATH" ]; then
     TARGET_PATH=$(python3 -c 'import os,sys;print(os.path.normpath(os.path.join(sys.argv[1],sys.argv[2])))' "$ROOT_ABS" "$TARGET_PATH")  # M:H11
   fi
   R=${ROOT_ABS%/}
   IN_ROOT=no
   if [ -n "$ROOT_ABS" ]; then case "$TARGET_PATH" in "$R"/*) IN_ROOT=yes ;; esac; fi  # M:H18
   ```
   `"$R"` is quoted so that glob characters in the root's name are literal; for root `/`, `R` is
   empty and `/*` admits every absolute target (design v1.3).
5. **Fast path** (step 4): `_chain_may_hold_state "$ROOT_ABS" "$TARGET_PATH" || _allow`, per design
   D9 step 4, with the parent computation as one line:
   `  d=$(dirname "$2"); while [ ! -e "$d" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; d=$(cd "$d" 2>/dev/null && pwd -P) || return 0  # M:H8`.
6. **Empty target** (DD-8):
   ```bash
   if [ -z "$TARGET_PATH" ]; then
     _find_judge
     _read_state
     _refuse judge-error "could not identify the write target"  # M:H13
   fi
   ```
7. **Exemptions and `.py` filter** (DD-1; design v1.3 §D9 steps 3 and 6; Deviation 16). The
   functions of item 2 gain the one directory matcher, today's two alternatives verbatim:
   ```bash
   _dir_match() { case "$1" in */tests/*|*/fixtures/*) return 0 ;; esac; return 1; }  # M:H15
   ```
   Then, in this order:
   ```bash
   case "${TARGET_PATH##*/}" in  # M:H6
     test_*.py|*_test.py|conftest*.py) _allow ;;
   esac
   if [ "$IN_ROOT" = yes ]; then
     DIR_SUBJECT="/${TARGET_PATH#"$R"/}"; if _dir_match "$DIR_SUBJECT"; then _allow; fi  # M:H19
   elif _dir_match "$TARGET_PATH" && _dir_match "$RAW_TARGET"; then  # M:H20
     _allow
   fi
   case "$TARGET_PATH" in
     *.md|*.yaml|*.yml|*.json|*.toml|*.txt|*.rst|*.cfg|*.ini) _allow ;;
     *.sh|*.bash|Makefile|Dockerfile|*.dockerignore|*.gitignore) _allow ;;
   esac
   [[ "$TARGET_PATH" != *.py ]] && _allow
   ```
   The basename block and the extension alternatives keep today's pattern bytes and the
   canonical `TARGET_PATH` as subject; only the directory alternatives move into `_dir_match`.
   Every matcher call sits in an `if` or `elif` condition, never as a bare failing command, so
   `set -e` never fires on a non-match.
   **Executed readings** (v1.2), under `/bin/bash` 3.2.57 with `set -euo pipefail`, in a scratch
   script holding the lines of steps 4 and 7 above, with each `_allow` replaced by a printed `allow`,
   a non-exempt `.py` printed as `gated`, and an environment switch selecting one mutant of Task
   10's H15, H15B, H18, H18B, H19, H20A or H20B at a time (deleted), at `c93da638`; the old gate is
   `git show HEAD:h-mad/hooks/h-mad-tdd-gate.sh` (last changed at `dde1c7ad`), run with a
   `codex` stub, `jq` and `python3` on `PATH`, stdin `/dev/null`, `cwd` and `CLAUDE_PROJECT_DIR`
   at the root, one ACTIVE step5 record; a gated active cell counts as a refusal, and every
   no-state cell allows under both (the fast path):
   - the 126 cells of item 23: old refusals 6 / 5 / 5 and new 6 / 6 / 6 (roots `repo`,
     `tests/repo`, `fixtures/repo`); softened exactly the 6 active relative `tests/x.py` and
     `fixtures/x.py` cells of the three shapes; tightened exactly the 8 active `./tests/../x.py`
     and `<root>/tests/../x.py` cells of the three shapes and `<root>/x.py` of the `tests/repo`
     and `fixtures/repo` shapes: design v1.3's sets;
   - root `<tmp>/tests/repo`: `x.py` and `<root>/x.py` gated; `../x.py` gated (canonical
     `<tmp>/tests/x.py` outside the root, `RAW_TARGET` `../x.py` matches neither alternative);
     `<tmp>/tests/../x.py` gated (canonical `<tmp>/x.py` matches neither);
   - root `<tmp>/repo`: `tests/x.py`, `./tests/x.py` and `fixtures/x.py` allow; root
     `<tmp>/re[p]o`: `tests/x.py` allows.
   The old gate on those cells (same fixture): `tests/repo` `x.py` rc 1, `<root>/x.py` rc 0,
   `../x.py` rc 1, `<tmp>/tests/../x.py` rc 0; `repo` `tests/x.py` rc 1 and `fixtures/x.py` rc 1;
   `re[p]o` `tests/x.py` rc 1.
   **Residual, stated (design v1.3 §D9 step 3).** The patterns key on the lexically normalized
   path, not the file the host opens: (a) a symlinked directory named `tests` or `fixtures`, or
   under one, pointing at production code is exempt; (b) a `..` after a symlinked component
   normalizes to a different file, and can exempt only a target whose raw spelling already holds a
   `tests` or `fixtures` segment; (c) outside the root only, a root reached through a symlinked
   spelling whose own path carries a `tests` or `fixtures` segment exempts an absolute target
   spelled through it, because that target is outside `ROOT_ABS` lexically and both its spellings
   match. The old gate exempted (a) and (c) identically; design v1.3 records (c) as old rc 0,
   v1.3 allow. No test pins a residual.
8. **Judge path**: `_find_judge` sets
   `  JUDGE=$(python3 -c 'import os,sys;print(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[1]))),"scripts","h_mad_tdd_judge.py"))' "${BASH_SOURCE[0]}")  # M:W6`
   unless `JUDGE` is already set.
9. **Governance**: `_find_judge`, then `_read_state --target "$TARGET_PATH"  # M:H3`. `_read_state`
   refuses `judge-error` naming `CLAUDE_PROJECT_DIR` on an empty `ROOT_ABS`, then (Deviation 11)
   ```bash
     SOUT=$(python3 "$JUDGE" state --root "$ROOT_ABS" "$@" 2>/dev/null; printf 'rc=%s' "$?")  # M:W5B
     SRC=${SOUT##*rc=}; SOUT=${SOUT%rc=*}; SOUT=${SOUT%$'\n'}  # M:H17
     case "$SOUT" in *$'\n'*|"") _refuse judge-error "state verb printed zero or several lines" ;; esac
   ```
   then refuses `judge-error` on a non-zero `SRC`, or a line matching none of
   design D10's three state EREs; `none` → `_allow`; `unreadable` → `_refuse judge-error` with the
   decoded file and error; `active` → the three cross-checks (under `set -f`, the `record=` word
   count equals `records=`; `blocker=0` exactly when `codex-escape=yes`; `blocker` ≤ `records`),
   then return with the blocker's record field kept.
10. **Codex authorship** (OD-9): when `HMAD_CODEX_UNAVAILABLE` is empty, `codex-escape=no` and
    `command -v codex` succeeds → `_refuse codex-authorship` with today's five-line message, the
    blocker record's decoded key in `--feature` and its decoded absolute state file as the
    `h_mad_state_write.py` argument.
11. **Judge**:
    ```bash
    JOUT=$(python3 "$JUDGE" judge --root "$ROOT_ABS" --target "$TARGET_PATH" 2>/dev/null; printf 'rc=%s' "$?")  # M:W2
    JRC=${JOUT##*rc=}; JOUT=${JOUT%rc=*}; JOUT=${JOUT%$'\n'}  # M:H16
    case "$JOUT" in *$'\n'*|"") _refuse judge-error "judge verb printed zero or several lines" ;; esac
    if [ "$JRC" = 0 ] && [[ $JOUT =~ $JUDGE_ALLOW_RE ]]; then _allow; fi  # M:H4
    if [[ $JOUT =~ $JUDGE_DENY_RE ]]; then _refuse "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"; fi
    _refuse judge-error "judge verb rc=$JRC printed no well-formed verdict line"
    ```
    with `JUDGE_ALLOW_RE` and `JUDGE_DENY_RE` design D10's two `TDD-JUDGE:` EREs.
12. The last line: `_refuse judge-error "gate fell through without a decision"`.

What leaves (design D9): `_resolve_state_file`, every `jq` use and the no-`jq` allow, the
`ACTIVE`/`head -1` read, `CODEX_STATUS`, `DERIVE_SCRIPT` and the bare `pytest` run, and every
`exit 1` (today 5 matching lines for `^\s*exit 1\s*$`, read at `f6b258f0`).

**Test harness** (in the new module): `HOOK = Path(__file__).resolve().parents[1] / "hooks" / "h-mad-tdd-gate.sh"`.
The form is never read at import (Deviation 14). `tdd_gate_support.hook_form(hook) -> Optional[str]`
returns the `[ab]` of the one line matching `^readonly REFUSAL_FORM=([ab])$` (`re.M`) in the hook's
text, and `None` when no line matches; each test calls it at run time. `CHOSEN = re.search(r"CHOSEN=([ab]) ", __doc__).group(1)`
reads the `v0.out` line the module docstring quotes (AC-6.6), a literal the test file itself holds.
`_gate(root, *, payload=None, arg=None, bin_dir, extra_env=None, cwd=None, hook=HOOK, timeout=60.0)`
runs `[str(hook)] + ([arg] if arg else [])` with `input=json.dumps(payload)` when a payload is
given and `stdin=subprocess.DEVNULL` otherwise, `cwd=cwd or root`, and the explicit minimal env
`{"PATH": f"{bin_dir}:/usr/bin:/bin", "HOME": str(Path.home()), "CLAUDE_PROJECT_DIR": str(root)}`
plus `extra_env`. `tdd_gate_support.decision(result, form)` returns
`Outcome(decision, kind, reason, rc)`: under `a`, rc 2 → deny with the stderr reason, rc 0 with
empty stdout → allow; under `b`, rc 0 with exactly one JSON object whose `hookSpecificOutput` has
`hookEventName == "PreToolUse"`, `permissionDecision == "deny"` and a non-empty reason → deny, rc
0 with empty stdout → allow; under `None` (today's hook, at RED), rc 0 with empty stdout → allow;
in every form, any other result → `invalid`. Every call passes
`hook_form(<the hook the test ran>)`. `kind` is parsed from
`[H-MAD-TDD-GATE] BLOCK kind=…:`. Bin dirs hold `python3` → `sys.executable` (plan rule (ii)),
`dirname` and `basename` → `/usr/bin/…`, and a `codex` stub only where stated. Fixtures default to
a root step5 record with `codex_status` `exhausted` and the hematology-paper-writer name-map
layout, and a Claude-Code-shaped payload `{"tool_name": "Write", "tool_input": {"file_path": <abs>}}`.
Tree-B stubs: `B/h-mad/hooks/h-mad-tdd-gate.sh` copied from the worktree hook, and
`B/h-mad/scripts/h_mad_tdd_judge.py` a stub whose `state` verb prints
`TDD-STATE: active codex-escape=yes blocker=0 records=1 record=feat,exhausted,/x/docs/.bkit-memory.json,absent`
unless the fixture replaces it, and whose `judge` verb prints the fixture's output and exits with
its rc.

**Tests** (80 new collected items):
1. `test_claude_gate_kind[red-measured|no-test-resolved|test-missing|venv-escapes-root|pytest-missing|pytest-error|no-tests-ran|no-summary|test-passing|timeout|judge-error]`
   (11; AC-1.2 Claude half): the Codex-gate fixtures of Task 6 item 1 in Claude's payload shape;
   `red-measured` → allow, every other id → deny with that kind; `timeout` uses `timeout=120.0`;
   `judge-error` is a tree-B judge printing `TDD-JUDGE: MAYBE`.
2. `test_judge_stub_is_judge_error[empty-line|two-lines|trailing-blank-line|maybe|unknown-kind|traceback-rc1|allow-rc1]`
   (7; AC-1.3): tree-B judge printing an empty line; two ALLOW lines; a valid ALLOW line followed
   by an empty line (`printf '%s\n\n'`, exit 0; Deviation 11); `TDD-JUDGE: MAYBE`;
   `TDD-JUDGE: DENY kind=bogus reason=x`; a traceback, exit 1; a valid ALLOW line, exit 1 → deny
   `judge-error` in the chosen form, `rc != 1`.
3. `test_state_stub_is_judge_error[zero-lines|two-lines|trailing-blank-line|bad-value|none-rc1]`
   (5; AC-1.3): tree-B `state` printing nothing; two lines; `TDD-STATE: none` followed by an
   empty line, exit 0; `TDD-STATE: maybe`; `TDD-STATE: none` with exit 1 → deny `judge-error`.
4. `test_claude_code_payload_reaches_codex_authorship` (1; AC-6.1) — `codex` stub on PATH,
   `codex_status` absent → deny `codex-authorship`.
5. `test_stdin_target_beats_positional` (1; AC-6.1, OD-B) — the same payload plus the exempt
   `<root>/tests/x.py` as `$1` → deny `codex-authorship`.
6. `test_positional_alone_reaches_codex_authorship` (1; AC-6.1) — `stdin=DEVNULL`, the production
   path as `$1` → deny `codex-authorship`.
7. `test_stdin_target_fields[top-level-file-path|top-level-path]` (2) — `{"file_path": …}` and
   `{"path": …}` → deny `codex-authorship`.
8. `test_no_pytest_on_path_passing_test_is_refused` (1; AC-6.3) → deny, kind `pytest-missing` or
   `test-passing`.
9. `test_new_production_file_with_passing_test_is_refused` (1; AC-6.4) — the target does not exist,
   GREEN name-map test → deny `test-passing`.
10. `test_refusal_sites_use_the_chosen_form[codex-authorship|judge-deny|unreadable-state|empty-target|malformed-judge]`
    (5; AC-6.5/AC-6.6): each site's exact form, `rc != 1`, and under `b` exactly one JSON object.
11. `test_hook_has_no_exit_1` (1; AC-6.5) — `re.findall(r"^\s*exit 1\s*$", text, re.M) == []`.
12. `test_subproject_step5_under_root_step3_is_governed` (1; AC-6.8) — root holds only
    `{"other": {"phase": "step3"}}`, `hematology-paper-writer/docs/.bkit-memory.json` holds step5
    `exhausted`, GREEN name-map test → deny `test-passing`.
13. `test_unreadable_chain_refuses_production` (1; AC-6.9) — root state `{not json`, production
    target → deny `judge-error`.
14. `test_exempt_write_on_unreadable_chain_is_allowed[state-file|test-file|doc]` (3; AC-6.9) —
    `<root>/docs/.bkit-memory.json`, `<root>/tests/test_x.py`, `<root>/notes.md` → allow each.
15. `test_codex_escape_needs_every_record[exhausted-then-none|none-then-exhausted]` (2; AC-6.10) —
    two step5 records, `codex` stub on PATH → deny `codex-authorship`.
16. `test_codex_escape_all_declared_proceeds_to_judge[both-exhausted|unavailable-and-exhausted]`
    (2; AC-6.10) — GREEN name-map test → deny `test-passing`.
17. `test_fast_path_defers[dangling-state-symlink|missing-parent|unsearchable-docs]` (3; AC-6.11):
    the only state name is a dangling symlink → deny `judge-error`; no root state,
    `hematology-paper-writer/docs/.bkit-memory.json` step5, target
    `<root>/hematology-paper-writer/newdir/x.py` with `newdir` absent and GREEN
    `hematology-paper-writer/tests/test_x.py` → deny `test-passing`; step5 state under a
    `chmod 000` `hematology-paper-writer/docs` → deny `judge-error` (mode restored in a `finally`).
18. `test_no_jq_on_path_still_judges` (1; AC-6.12) — `PATH=<bin>:/bin` with a bin holding only
    `python3`, `dirname` and `basename` (`/usr/bin/jq` exists at `f6b258f0`, so `/usr/bin` is left
    out), GREEN test → deny `test-passing`.
19. `test_empty_target_rule[active-root|unreadable-root|no-step5-root]` (3; AC-6.13) — payload
    `{"tool_name": "Write", "tool_input": {}}`, no `$1` → deny `judge-error`, deny `judge-error`,
    allow.
20. `test_outside_root_target_is_governed_by_root[active|no-step5]` (2; AC-6.14) — a target in a
    sibling temp directory, `codex` stub on PATH, `codex_status` absent → deny
    `codex-authorship`; with a root holding only a step3 record → allow.
21. `test_relative_targets[tests-relative|dot-tests-relative|fixtures-relative|sub-relative]` (4;
    AC-6.15) — root `<tmp>/repo`: `$1` `tests/x.py`, `./tests/x.py` and `fixtures/x.py` → allow;
    `sub/x.py` → the same outcome as `<root>/sub/x.py`, both deny `codex-authorship` (codex stub on
    PATH). Re-derived under design v1.3: each directory cell's subject is `/tests/x.py` or
    `/fixtures/x.py`, and `sub/x.py`'s is `/sub/x.py`, so the outcomes are v1.1's; `fixtures-relative`
    is new in v1.2 (the `*/fixtures/*` alternative alone, row H15B).
22. `test_traversal_target_is_gated[relative|dot-relative|absolute]` (3; DD-7, OD-G) —
    `tests/../x.py`, `./tests/../x.py`, `<root>/tests/../x.py` → deny `codex-authorship`.
    Re-derived under design v1.3: all three normalize to `<root>/x.py`, subject `/x.py`; unchanged.
23. `test_dd7_differential_matches_the_published_cells` (1; D9 differential, design v1.3) — the
    126 cells of `tdd_gate_support.dd7_cells` (3 spellings × 7 paths × 2 states × 3 root shapes
    `<tmp>/repo`, `<tmp>/tests/repo`, `<tmp>/fixtures/repo`; positional entry point,
    `stdin=DEVNULL`, `cwd` and `CLAUDE_PROJECT_DIR` at the shape's root, bin with a `codex` stub,
    `jq` and `python3`; the active state one step5 record with `codex_status` absent) through the
    worktree hook: exactly 18 cells refuse, `codex-authorship` in the chosen form (per shape the 6
    active cells relative `x.py`, `./x.py`, `<root>/x.py`, `tests/../x.py`, `./tests/../x.py` and
    `<root>/tests/../x.py`), and the other 108 allow. The three roots are made under pytest's
    `tmp_path`, whose resolved path holds no `tests` or `fixtures` segment (asserted), so the root
    shape alone decides the root's ancestry.
24. `test_control_character_stdin_target_never_falls_back` (1) — `tool_input.file_path` holding
    `"a\nb.py"`, exempt `$1` → deny `judge-error`.
25. `test_non_json_stdin_never_falls_back_to_positional` (1; DD-13) — stdin `not json`, exempt
    `$1`, root step5 → deny `judge-error`.
26. `test_unenterable_project_dir_refuses` (1) — `CLAUDE_PROJECT_DIR` a missing directory, a step5
    state on the target's chain → deny `judge-error`, reason contains `CLAUDE_PROJECT_DIR`.
27. `test_codex_authorship_hint_names_blocker_key_and_state_file` (1) — root named `my proj`,
    records `a` (`exhausted`) then `b` (absent), `codex` stub → the reason contains `--feature b`
    and the absolute state file path with its space.
28. `test_trap_member_refuses_in_form[traceback-rc1|allow-rc1|realpath-stub|unset-variable]` (4;
    plan layer 6): the two tree-B judge stubs of item 2; a bin `python3` stub that exits 3 when
    its argv contains `os.path.realpath` and otherwise `exec`s `sys.executable`; a tree-B hook copy
    in which the test replaces the single `_refuse() {` line (asserted to occur once) with
    `_refuse() {` + newline + `  : "$HMAD_UNSET_PROBE_VAR"`, and a `codex` stub so the first
    refusal is reached. Each → deny `judge-error` in the chosen form and `rc != 1`. No id asserts
    the rc the reason names: under `/bin/bash` 3.2.57, `local rc=$?` inside the EXIT trap reads 0
    after a `set -u` abort (executed at `c93da638` on a scratch copy of the trap with that line,
    deleted: `trap rc=0`, final rc 2), so `[unset-variable]`'s reason reads
    `gate exited rc=0 before deciding`. Under T2's mutant (`exit "$rc"`) that id exits 0 with empty
    stdout, an allow, so T2 is killed on the deny assertion.
29. `test_symlinked_hook_runs_its_own_trees_judge` (1; W6) — tree B's judge writes `B/marker` and
    prints `TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=tree-b.py`; the hook is run
    through a symlink `L/h-mad-tdd-gate.sh` placed outside both trees → allow, and `B/marker`
    exists.
30. `test_hooks_reach_the_name_map_only_through_the_judge` (1; AC-1.1) — neither hook file contains
    `h_mad_derive_test_path.sh`.
31. `test_claude_gate_keeps_no_private_state_reader` (1) — the hook holds no `orchestrator_state`,
    no `_resolve_state_file` and no `jq`.
32. `test_refusal_form_is_a_readonly_literal` (1) — exactly one line matches
    `^readonly REFUSAL_FORM=[ab]$`, `hook_form(HOOK) == CHOSEN`, and no line reads
    `REFUSAL_FORM` from the environment.
33. `test_state_without_step5_is_allowed` (1) — root holds only a step3 record, `codex` stub on
    PATH, production target → allow.
34. `test_root_under_a_test_directory_is_governed[tests-root-relative|tests-root-absolute]` (2;
    AC-6.15, design v1.3) — root `<tmp>/tests/repo`, one step5 record with `codex_status` absent,
    `codex` stub on PATH, `stdin=DEVNULL`: `$1` `x.py` and `$1` `<root>/x.py` → deny
    `codex-authorship` each (the root's own `tests` segment never exempts; row H19).
35. `test_outside_root_exemption_needs_both_spellings[dotdot-relative|traversal-absolute]` (2;
    design v1.3) — the same fixture: `$1` `../x.py` (canonical `<tmp>/tests/x.py` matches, raw
    `../x.py` does not; row H20B) and `$1` `<tmp>/tests/../x.py` (raw matches, canonical
    `<tmp>/x.py` does not; row H20A) → deny `codex-authorship` each (AC-6.14: an outside-root
    target is governed by the root's state).
36. `test_root_name_glob_characters_are_literal` (1; design v1.3) — root `<tmp>/re[p]o`, one step5
    record, `$1` `tests/x.py` → allow (the quoted `"$R"/*` membership; row H18B).

11 + 7 + 5 + 1 + 1 + 1 + 2 + 1 + 1 + 5 + 1 + 1 + 1 + 3 + 2 + 2 + 3 + 1 + 3 + 2 + 4 + 3 + 1 + 1 + 1 + 1 + 1 + 4 + 1 + 1 + 1 + 1 + 1 + 2 + 2 + 1 = 80.

**Existing modules, the named changes only** (spec AC-6.2; §"Regression provenance"):
- Both modules' `HOOK` constant becomes
  `Path(__file__).resolve().parents[1] / "hooks" / "h-mad-tdd-gate.sh"`.
- The 3 call sites that run the gate gain `stdin=subprocess.DEVNULL`: the `_run` helper of each
  module and `test_non_step5_ignores_codex_gate` (`grep -n 'subprocess.run(\[str(HOOK)'` over the
  two files → 3 matching lines at `f6b258f0`; `grep -n 'stdin=\|input='` → 0).
- **Under `REFUSAL_FORM=a`**: only the 4 `returncode == 1` assertions change, to `== 2`, in
  `test_blocks_claude_prod_write_when_codex_available`, `test_gate_finds_state_one_directory_down`,
  `test_repo_root_layout_still_works` and
  `test_a_production_file_under_a_test_named_directory_is_still_gated`. The stderr and
  `returncode == 0` assertions stand.
- **Under `REFUSAL_FORM=b`**: every assertion moves to `tdd_gate_support.decision(result,
  hook_form(HOOK))`, the form read at run time as in the new module (Deviation 14), exactly as spec
  AC-6.2 lists: the 4 rc-1 tests read a deny (with `codex`/`dispatch`, and `H-MAD-TDD-GATE`, in its
  reason); the 3 "must be authored by codex" absences read the helper's reason; the 6
  `returncode == 0` tests read an allow.
- After the rewrite these tests run the new gate under `/usr/bin/python3` (their bin dirs hold no
  `python3`), which the Python floor covers. Their refusals are `codex-authorship`,
  `no-test-resolved` or `test-missing`, none of which runs pytest.

**Probe deliverable**: `dd7_differential.py --old HOOK --new HOOK` runs both hooks over
`dd7_cells` and prints `DD7: softened <cell>` / `DD7: tightened <cell>` lines and
`DD7: DONE cells=126 softened=N tightened=N`, each cell named by its root shape, spelling, path
and state. **Probe-run step**, old = `git show "$BASE_SHA":h-mad/hooks/h-mad-tdd-gate.sh`:
expected `softened=6` (the active relative `tests/x.py` and relative `fixtures/x.py` cells in each
of the three root shapes) and `tightened=8` (the active `./tests/../x.py` and absolute
`<root>/tests/../x.py` cells in each shape, and the active absolute `<root>/x.py` cells of the
`tests/repo` and `fixtures/repo` shapes), exactly the sets of design v1.3 §D9 "DD-7
guard-narrowing differential" and of this task's executed readings (step 7); any other changed
cell is a defect and halts. Published in the analysis document §"DD-7 differential".

**Expected RED split** (against today's gate; the migrated modules already point `HOOK` at the
worktree): 75 failing and 5 passing among the 80 new items; in the two migrated modules, 4
failing and 9 passing under either form. The module collects at RED: nothing reads the form at
import (Deviation 14), and `hook_form`, `decision` and `dd7_cells` are in the RED commit
(Deviation 1). With today's hook `hook_form` returns `None` (`grep -c REFUSAL_FORM
h-mad/hooks/h-mad-tdd-gate.sh` → 0 at `a1478ad3`), so a refusal reads `invalid` and an allow reads
allow.
- The 5 passing new items are guards today's gate already satisfies: `test_claude_gate_kind[red-measured]`
  (today reads no `tool_input`, so the target is empty and it allows),
  `test_empty_target_rule[no-step5-root]`, `test_outside_root_target_is_governed_by_root[no-step5]`,
  `test_relative_targets[dot-tests-relative]` (today's `*/tests/*` matches `./tests/x.py`) and
  `test_state_without_step5_is_allowed`. The rows that show each failing: W2F, W5BF2, W5BF3, H15
  and W5BF (Task 10 §"Initially-green guards").
- Every other new item fails on its outcome assertion: today's gate reads no `tool_input` (payload
  tests allow), refuses with `exit 1` (no chosen form), exits rc 5 on `{not json`, allows on a
  dangling or unsearchable state and on a missing parent, stands down without `jq`, never calls a
  judge (tree-B markers and stubs unused), and still contains `exit 1`, `jq` and
  `h_mad_derive_test_path.sh`. The six v1.2 items fail on today's verdicts, read in step 7's
  executed readings: `test_relative_targets[fixtures-relative]` (rc 1, `invalid` where allow is
  expected), `test_root_under_a_test_directory_is_governed[tests-root-relative]` (rc 1, `invalid`
  where deny is expected) and `[tests-root-absolute]` (rc 0, allow),
  `test_outside_root_exemption_needs_both_spellings[dotdot-relative]` (rc 1, `invalid`) and
  `[traversal-absolute]` (rc 0, allow), and `test_root_name_glob_characters_are_literal` (rc 1,
  `invalid`).
- Migrated modules: the 4 rc-1 tests fail (today exits 1); the other 9 pass under `a` and under `b`.
**WIRE-PIN 1 RED reason**: today's gate skips pytest when the target does not exist and exits 0,
so `decision(...).decision == "deny"` fails on the gate's outcome. **WIRE-PIN 2 RED reason**:
today's root-first reader sees only the step3 record and exits 0; the deny assertion fails on the
gate's outcome. **WIRE-PIN 3 RED reason**: tree B's copy of today's gate never calls a judge, so
`B/marker` does not exist and the marker assertion fails. All three run the gate as a subprocess,
so no import error is involved.
**Regression guards**: the 9 unchanged-assertion tests of the two migrated modules;
`test_h_mad_hook_wiring.py`, `test_h_mad_install_check.py` and `test_h_mad_install_check_docs.py`
(they name the gate but do not run it, plan §"Success Criteria").
**Wire-scoped reverts** (each keeps the `rc=` sentinel the next line splits off):
`JOUT=$'TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=removed\nrc=0'  # M:W2`
→ WIRE-PIN 1 allows (row W2R); `  SOUT=$'TDD-STATE: none\nrc=0'  # M:W5B` → WIRE-PIN 2 allows
(row W5BR); `  JUDGE="$HOME/.claude/skills/h-mad/scripts/h_mad_tdd_judge.py"  # M:W6` → `B/marker`
absent (row W6R). **Force-fires**:
`JOUT=$'TDD-JUDGE: DENY kind=judge-error reason=forced\nrc=0'  # M:W2` →
`test_claude_gate_kind[red-measured]` is refused (row W2F);
`  SOUT=$'TDD-STATE: active codex-escape=no blocker=1 records=1 record=forced,available,/nowhere/docs/.bkit-memory.json,absent\nrc=0'  # M:W5B`
→ `test_state_without_step5_is_allowed` is refused (row W5BF), and so are
`test_empty_target_rule[no-step5-root]` (row W5BF2: the empty-target branch reads the forced
`active` and refuses) and `test_outside_root_target_is_governed_by_root[no-step5]` (row W5BF3:
`codex-escape=no` with the `codex` stub on `PATH` refuses `codex-authorship`);
`  JUDGE="/Users/kimhawk/orca/skills/h-mad/scripts/h_mad_tdd_judge.py"  # M:W6` (tree A, the main
checkout; any fixed path fails the tree-B test the same way) → `B/marker` absent (row W6F).

**Acceptance Criteria**:
- [ ] AC-1.1: item 30. AC-1.2 (Claude half): item 1. AC-1.3: items 2 and 3.
- [ ] AC-6.1: items 4, 5, 6. AC-6.2: the migration above. AC-6.3: item 8. AC-6.4: item 9.
- [ ] AC-6.5 (branch `E1_DOES_NOT_BLOCK`) or AC-6.6 (branch `E1_BLOCKS`), per `v0.out`: items 10,
  11, 32. AC-6.7: the precondition.
- [ ] AC-6.8: item 12. AC-6.9: items 13 and 14. AC-6.10: items 15 and 16. AC-6.11: item 17.
  AC-6.12: item 18. AC-6.13: item 19. AC-6.14: items 20 and 35. AC-6.15: items 21, 22, 23, 34,
  35, 36 and the probe.

**Mutation rows** (Task 10): H1A, H1B, H1C, H2, H3, H4, H5, H6, H7, H8, H10, H11, H12, H13, H14,
H15, H15B, H16, H17, H18, H18B, H19, H20A, H20B, C2G, C3G, W2R, W2F, W5BR, W5BF, W5BF2, W5BF3,
W6R, W6F, T1, T2 in `claude_gate_judge_wiring.json` — 36 rows.

**Dependencies on other tasks**: Task 7 (and the FR-0 V-0 precondition)

---

## Task 9: gate-docs

**Production file**: `h-mad/references/codex-runtime.md`, `h-mad/SKILL.md`, `h-mad/references/agy-runtime.md`, `h-mad/references/codex-implementer-prompt.md`, `h-mad/scripts/h_mad_derive_test_path.sh` (header comment only)
**Test file**: `h-mad/tests/test_h_mad_tdd_gate_docs.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §D11; spec FR-7. Each span is located by heading or line prefix:
- `codex-runtime.md` `### Trust boundary` (a level-3 heading, read at `f6b258f0`) gains a paragraph:
  the nearest `.venv` from the test file up to the root; `realpath` containment of `.venv` and
  `.venv/bin` plus a regular `pyvenv.cfg`; DENY `venv-escapes-root`; the residuals; the verdict
  scored on pytest's summary line, never rc. The existing sentences that
  `test_codex_adapter_states_pytest_trust_boundary` pins stay.
- `SKILL.md` `## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)`: a bullet for
  `h_mad_tdd_judge.py` beside `h_mad_derive_test_path.sh`, naming the `state` and `judge` verbs,
  the `TDD-STATE:` and `TDD-JUDGE:` tokens, and that a copied (not symlinked) Claude hook finds no
  judge and refuses `judge-error`.
- `SKILL.md` gate bullets: the 4 lines naming `hooks/h-mad-tdd-gate.sh` (`grep -c` → 4 at
  `f6b258f0`) are re-read; the "reads the **same** `codex_status`" bullet gains: with several
  ACTIVE records on the chain, every one must declare `unavailable` or `exhausted`.
- `agy-runtime.md` `## The TDD gate`: "is written to Claude Code's exit-code protocol" is replaced
  by the chosen form: `rc 2` with the reason on stderr for `a`, or a `permissionDecision` JSON deny
  on rc 0 for `b`.
- `codex-implementer-prompt.md`: the line beginning `Hook: ` names `h-mad-codex-tdd-gate.py` for
  Codex's `apply_patch` and shell writes and `h-mad-tdd-gate.sh` for Claude's `Write`/`Edit`; the
  production bullet says the test comes from the impl-plan Task, else the name map, and "failing"
  means the summary shows `N failed`; the test bullet names `test_*.py`, `*_test.py` and
  `conftest*.py`. The line and bullets carry no angle-bracket slot, because
  `h_mad_assemble_tdd.py` halts `residual_slots` on one.
- `h_mad_derive_test_path.sh`: "Used by ~/.claude/hooks/h-mad-tdd-gate.sh" → "Used by
  h_mad_tdd_judge.py".

**Tests** (11 new collected items). Sections come from `docsections.titled_section`, which fails
loudly on a missing heading; the `Hook: ` block from a module helper that asserts exactly one line
starts with `Hook: ` and returns it with the `- ` lines under it:
```python
def _hook_block(text: str) -> str:
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("Hook: ")]
    assert len(starts) == 1, f"expected one 'Hook: ' line, found {len(starts)}"  # M:D1
```
followed by the lines from `starts[0]` up to the first line after it that does not begin with `- `.

1. `test_trust_boundary_states_the_venv_rule` (AC-7.1): `.venv`, `realpath`, `venv-escapes-root`,
   `summary line`.
2. `test_helper_scripts_registers_the_judge` (AC-7.2): `h_mad_tdd_judge.py`, `TDD-STATE:`,
   `TDD-JUDGE:`, `judge-error`.
3. `test_tdd_gate_section_names_the_chosen_form` (AC-7.2): `rc 2` under `a`; `permissionDecision`
   under `b`, and no `exit-code protocol` under `b`. The form is `tdd_gate_support.hook_form(HOOK)`,
   called at run time as in Task 8 (Task 8 has landed, so it is `a` or `b`).
4. `test_hook_line_names_both_gates` (AC-7.2).
5. `test_hook_bullets_state_the_shipped_rule` (AC-7.2): `impl-plan` and `failed`.
6. `test_skill_gate_bullet_states_the_every_record_rule`.
7. `test_derive_script_header_names_the_judge`.
8. `test_locators_fail_loudly[trust-boundary|helper-scripts|tdd-gate|hook-line]` (4): each locator
   on a copy of its document with the heading or `Hook: ` prefix renamed raises
   `AssertionError`.

1 + 1 + 1 + 1 + 1 + 1 + 1 + 4 = 11.

**Expected RED split**: 7 failing (items 1–7: the wording is not there yet) and 4 passing (item 8
exercises the test's own locators on doctored copies, which fail loudly before any doc edit).
**Passing at RED, and the row that shows each one failing**: `[hook-line]` D1 (the helper made to
fall back to the first line, `    starts = starts or [0]  # M:D1`, no longer raises, so
`pytest.raises(AssertionError)` fails with `DID NOT RAISE`, a `Failed`, not a crash); the other
three ids exercise `docsections.titled_section`, whose loud failure the committed
`docsections.json` spec already mutates (8 rows at `a1478ad3`, one of them scored on
`tests/test_docsections.py::test_a_missing_heading_fails_loudly`).
**Regression guards**: the full suite, in particular every module that reads these documents:
`test_h_mad_codex_runtime.py::test_codex_adapter_states_pytest_trust_boundary` (AC-7.1),
`test_h_mad_assemble_tdd.py`, `test_h_mad_prompt_tails.py`, `test_h_mad_install_check_docs.py`,
`test_h_mad_hook_wiring.py`, `test_h_mad_wire_registry.py::test_skill_inventory_lists_wire_registry_helper`
and `test_h_mad_portable_timeout.py` (Convention 10).

**Acceptance Criteria**:
- [ ] AC-7.1: item 1 and the existing test. AC-7.2: items 2–5 and item 8.

**Mutation rows** (Task 10): D1 in `claude_gate_judge_wiring.json` — 1 row. **Dependencies on
other tasks**: Task 8

---

## Task 10: mutation-specs

**Production file**: none. Eight new JSON specs in `h-mad/tests/mutation-specs/`:
`audit_suite_summary_line.json`, `tdd_judge_resolution.json`, `tdd_judge_venv.json`,
`tdd_judge_scoring.json`, `tdd_judge_chain.json`, `tdd_judge_wiring.json`,
`codex_gate_judge_wiring.json`, `claude_gate_judge_wiring.json` (none exists at `f6b258f0`).
**Test file**: none. The killing tests belong to Tasks 1–9.
**Task shape**: `operational`

**Description**: Author the eight specs with exactly the 98 rows below (spec FR-8, AC-8.1; design
§"Test Strategy"). Every spec has `root` `"../.."` (the `h-mad/` directory), `command` the named
test module(s) as `["/opt/anaconda3/bin/python", "-m", "pytest", <module>…, "-q"]`, and
`target_command` `["/opt/anaconda3/bin/python", "-m", "pytest", "-q"]`, so each row runs only its
`test` under the pinned interpreter (`ls -l /opt/anaconda3/bin/python` → a symlink to
`python3.11`, `--version` → `Python 3.11.8`, at `a1478ad3`). Of the 99 committed specs, 98 name
`python3.11` and 1 names `/opt/anaconda3/bin/python3.11` as `command[0]` (a JSON walk at
`a1478ad3`), so an absolute interpreter has a precedent and nothing here rests on `PATH` at
harness time. Every row carries `name`, `file`, `find`, `replace` and `test`; `find` is the whole
tagged line of Convention 9 (or, for R2, W3C, P1, P1B, P2, G8 and G11, the untagged line quoted). Rows
sharing a `find` are applied one at a time.
- **Pass condition, per spec**: `--check-anchors <spec>` → `ANCHORS_OK`; the run →
  `MUTATION: ALL_CAUGHT` with `crash_kills=0`. A crash kill is re-authored so that its test fails
  on an assertion. `SURVIVED`, `REFUSED` or any other token halts and is reported against the
  owning task.
- Afterwards Convention 8's sweep → `ANCHORS_OK drifted=0` (the existing `audit_suite_gate.json`
  keeps its 9 rows and anchors), and
  `h-mad/tests/test_h_mad_mutation_harness.py::test_committed_mutation_harness_anchor_sweep_is_ok`
  passes in the full suite.
- The claude spec's H5 row uses the tag of the chosen form only (`# M:H5A` under `a`, `# M:H5B`
  under `b`); the other branch is dead code and a row on it would be equivalent.

**`audit_suite_summary_line.json`** — `command` `tests/test_h_mad_audit_suite_gate.py`
`tests/test_h_mad_tdd_gate_support.py`; `file` `scripts/h_mad_audit_gate.py` except E1
(`tests/tdd_gate_support.py`):

| Row | find tag | replace (the tagged line becomes) | test |
|---|---|---|---|
| S1 | `M:S1` | `    if not ({"failed"} & summary.phrases):  # M:S1` | `tests/test_h_mad_audit_suite_gate.py::test_run_suite_table_row[subtests-passed]` |
| S2 | `M:S1` | `    if not ({"passed"} & summary.phrases):  # M:S1` | `tests/test_h_mad_audit_suite_gate.py::test_run_suite_table_row[three-failed]` |
| S3 | `M:S3` | `    return untimed if untimed is not None else timed  # M:S3` | `tests/test_h_mad_audit_suite_gate.py::test_run_suite_table_row[stray-failed-on-stderr]` |
| S4 | `M:S4` | `        line = raw.strip().strip("=").strip()  # M:S4` | `tests/test_h_mad_audit_suite_gate.py::test_run_suite_table_row[coloured]` |
| S5 | `M:S5` | `                if category.endswith("passed"):  # M:S5` | `tests/test_h_mad_audit_suite_gate.py::test_run_suite_table_row[subtests-failed-run]` |
| S6 | `M:S6` | `                elif category.endswith("failed"):  # M:S6` | `tests/test_h_mad_audit_suite_gate.py::test_suite_summary_reads_the_line[subtests-failed]` |
| S7A | `M:S7` | `                elif category == "errors":  # M:S7` | `tests/test_h_mad_audit_suite_gate.py::test_suite_summary_reads_the_line[one-error]` |
| S7B | `M:S7` | `                elif category == "error":  # M:S7` | `tests/test_h_mad_audit_suite_gate.py::test_suite_summary_reads_the_line[one-errors]` |
| S8 | `M:S8` | `        match = re.search(_SUMMARY_LINE_RE.pattern.lstrip("^"), line)  # M:S8` | `tests/test_h_mad_audit_suite_gate.py::test_suite_summary_reads_the_line[failed-node-line]` |
| S8B | `M:S8` | `        match = re.search(_SUMMARY_LINE_RE.pattern.lstrip("^").rstrip("$"), line)  # M:S8` | `tests/test_h_mad_audit_suite_gate.py::test_suite_summary_reads_the_line[quoted-assert]` |
| S9 | `M:S9` | `_CATEGORY = r"[A-Za-z][a-z-]*(?: [a-z][a-z-]*)*"  # M:S9` | `tests/test_h_mad_audit_suite_gate.py::test_suite_summary_reads_the_line[capitalised-category]` |
| S10 | `M:S10` | `                    failed += int(number)  # M:S10` | `tests/test_h_mad_audit_suite_gate.py::test_run_suite_table_row[passed-and-error]` |
| S11 | `M:W4C` | `                    failed += 0  # M:W4C` | `tests/test_h_mad_audit_suite_gate.py::test_run_suite_table_row[failed-and-passed]` |
| S12 | `M:S1` | `    if False:  # M:S1` | `tests/test_h_mad_audit_suite_gate.py::test_run_suite_table_row[three-skipped]` |
| E1 | `M:E1` | `    env = dict(os.environ)  # M:E1` | `tests/test_h_mad_tdd_gate_support.py::test_hermetic_env_drops_claude_names_and_backend` |

Executed readings for S8–S12 (a scratch copy of Task 1's literals, with a `run_suite`-shaped
wrapper reproducing its `summary is None`, S1 and `passed == 0 and failed == 0` branches, under
`/usr/bin/python3` 3.9.6 at `a1478ad3`, run in memory and never written): S8 turns
`FAILED t.py::a - 1 failed` into `failed=1` and `collected 0 items` into phrases `{"items"}`
(each `None` unmutated) and leaves `E   assert '1 failed' in x` at `None`; S9 turns
`3 Apples in 0.1s` into phrases `{"Apples"}`; S10 turns `2 passed, 1 error in 0.1s` into
`SUITE: FAIL passed=2 failed=1`; S11 turns `1 failed, 11 passed in 0.2s` into
`SUITE: PASS passed=11 failed=0`; S12 turns `3 skipped in 0.1s` and `1 error in 0.06s` into
`SUITE: UNREADABLE reason=no_tests_ran`. The first S8 candidate, `.match` → `.search`, killed
nothing, because the pattern's own `^` anchors a search too; the row therefore strips that `^`
in the same line. S8B (v1.2; a scratch copy of Task 1's `_suite_summary` literal written to the
session scratch directory and deleted, `/usr/bin/python3` 3.9.6 at `c93da638`): stripping both
the `^` and the `$` turns `E   assert '1 failed' in x` into `(0, 1, 0, False, {"failed"})`
(`None` unmutated, and `None` under S8), so the `quoted-assert` row fails on its tuple assertion.

**`tdd_judge_resolution.json`** — `command` `tests/test_h_mad_tdd_judge.py`
`tests/test_h_mad_parse_tasks_paths.py`:

| Row | file | find | replace | test |
|---|---|---|---|---|
| R1 | `scripts/h_mad_tdd_judge.py` | `M:R1` | `    if matched and present:  # M:R1` | `tests/test_h_mad_tdd_judge.py::test_task_match_is_authoritative_over_the_name_map` |
| R2 | `scripts/h_mad_wire_pin_gate.py` | the `_NONE_VALUE_RE = re.compile(…)` line of Task 2 | `_NONE_VALUE_RE = re.compile(r"(?!)")` | `tests/test_h_mad_tdd_judge.py::test_none_valued_production_does_not_match` |
| R3 | `scripts/h_mad_tdd_judge.py` | `M:R3` | the same line without `{_notes(notes)}` | `tests/test_h_mad_tdd_judge.py::test_unreadable_plan_is_named_in_test_missing` |
| R4 | `scripts/h_mad_tdd_judge.py` | `M:R4` | `    present = list(candidates)  # M:R4` | `tests/test_h_mad_tdd_judge.py::test_mixed_candidates_missing_then_green_denies_test_passing` |
| R5 | `scripts/h_mad_tdd_judge.py` | `M:R5` | `    mapped = (out + err).strip()  # M:R5` | `tests/test_h_mad_tdd_judge.py::test_name_map_stderr_is_not_a_path` |
| P1 | `scripts/h_mad_wire_pin_gate.py` | the `current[key].extend(…)` line of Task 2 | `                current["pins"].extend(_PY_TOKEN_RE.findall(paths.group("value")))` | `tests/test_h_mad_parse_tasks_paths.py::test_existing_fields_unchanged` |
| P1B | `scripts/h_mad_wire_pin_gate.py` | the same line | the same replacement | `tests/test_h_mad_parse_tasks_paths.py::test_corpus_old_fields_unperturbed` |
| P2 | `scripts/h_mad_wire_pin_gate.py` | `    r"^\s*(?:[-*•]\s+)?\*{0,2}\s*(?P<label>Task\s+shape\|WIRE-PIN\|WIRE)"` (`_FIELD_RE`'s first pattern line, read at `a1478ad3`) | the same line with `\|WIRE)` → `\|WIRE\|Production)` | `tests/test_h_mad_parse_tasks_paths.py::test_field_re_is_unchanged` |

P1 and P1B put path tokens into `pins`, a list of `(suffix, value)` tuples (`current["pins"].append((suffix, value))`,
read at `a1478ad3`), so both comparisons fail on an assertion. P2 changes `_FIELD_RE.pattern`,
which item 7 compares with its literal.

**`tdd_judge_venv.json`** — `command` `tests/test_h_mad_tdd_judge.py`; `file` `scripts/h_mad_tdd_judge.py`:

| Row | find | replace | test |
|---|---|---|---|
| V1 | `M:V1` | `    if False:  # M:V1` | `tests/test_h_mad_tdd_judge.py::test_venv_contained_rows[venv-out-bin-back-in]` |
| V2 | `M:V2` | `    if False:  # M:V2` | `tests/test_h_mad_tdd_judge.py::test_venv_contained_rows[bin-symlink-out]` |
| V3 | `M:V3` | `        return True  # M:V3` | `tests/test_h_mad_tdd_judge.py::test_venv_contained_rows[cfg-missing]` |

**`tdd_judge_scoring.json`** — `command` `tests/test_h_mad_tdd_judge.py`; `file` `scripts/h_mad_tdd_judge.py`:

| Row | find | replace | test |
|---|---|---|---|
| K1 | `M:K1` | `    if False:  # M:K1` | `tests/test_h_mad_tdd_judge.py::test_pytest_missing_denies[project-venv]` |
| K2 | `M:K2` | `    if False:  # M:K2` | `tests/test_h_mad_tdd_judge.py::test_scoring_kinds[import-error]` |
| K3 | `M:K3` | `        kind = "red-measured" if returncode == 1 else "test-passing"  # M:K3` | `tests/test_h_mad_tdd_judge.py::test_rc_selects_nothing[failed-line-rc0]` |
| K3B | `M:K3` | the K3 replacement | `tests/test_h_mad_tdd_judge.py::test_rc_selects_nothing[silent-rc1]` |
| K4 | `M:K4` | `    return "no-summary"  # M:K4` | `tests/test_h_mad_tdd_judge.py::test_scoring_kinds[skipped-only]` |
| K5 | `M:K1` | `    if _pytest_missing(proc_output) and _suite_summary(proc_output) is None:  # M:K1` | `tests/test_h_mad_tdd_judge.py::test_whole_line_no_module_is_pytest_missing_even_after_red` |

**`tdd_judge_chain.json`** — `command` `tests/test_h_mad_tdd_judge.py`; `file` `scripts/h_mad_tdd_judge.py`:

| Row | find | replace | test |
|---|---|---|---|
| C1 | `M:C1` | `        records.extend(_active_records(data, path)); break  # M:C1` | `tests/test_h_mad_tdd_judge.py::test_chain_reads_every_state_file_up_to_root` |
| C2 | `M:C2` | `            continue  # M:C2` | `tests/test_h_mad_tdd_judge.py::test_first_unreadable_file_decides[root-unreadable-sub-step5]` |
| C3 | `M:C3` | the same line with `all(` → `any(` | `tests/test_h_mad_tdd_judge.py::test_state_line_escape_and_blocker[exhausted-then-available]` |
| C4 | `M:C4` | `        if False:  # M:C4` | `tests/test_h_mad_tdd_judge.py::test_non_regular_state_is_unreadable[fifo]` |
| C5 | `M:C5` | `    blocker = 1  # M:C5` | `tests/test_h_mad_tdd_judge.py::test_state_line_escape_and_blocker[exhausted-then-available]` |
| C6 | `M:C6` | `    except OSError:  # M:C6` | `tests/test_h_mad_tdd_judge.py::test_unsearchable_directory_is_unreadable[chmod-dir]` |

**`tdd_judge_wiring.json`** — `command` `tests/test_h_mad_tdd_judge.py`; every row scored on the
judge's tests only (design W3/W4 table):

| Row | file | find | replace | test |
|---|---|---|---|---|
| W3R | `scripts/h_mad_tdd_judge.py` | `M:W3` | `        tasks = []  # M:W3` | `tests/test_h_mad_tdd_judge.py::test_hemasuite_layout_resolves_from_the_task` |
| W3F | `scripts/h_mad_tdd_judge.py` | `M:W3` | `        tasks = [dict(t, production=[]) for t in _parse_tasks(text)]  # M:W3` | `tests/test_h_mad_tdd_judge.py::test_task_match_is_authoritative_over_the_name_map` |
| W3C | `scripts/h_mad_wire_pin_gate.py` | the `_PATHS_FIELD_RE` label line of Task 2 | the same with `Production(?:` → `Productionx(?:` | `tests/test_h_mad_tdd_judge.py::test_hemasuite_layout_resolves_from_the_task` |
| W4R | `scripts/h_mad_tdd_judge.py` | `M:W4` | `    summary = None  # M:W4` | `tests/test_h_mad_tdd_judge.py::test_scoring_kinds[red]` |
| W4F | `scripts/h_mad_tdd_judge.py` | `M:W4` | `    summary = _suite_summary("1 failed in 0.01s")  # M:W4` | `tests/test_h_mad_tdd_judge.py::test_scoring_kinds[green]` |
| W4C | `scripts/h_mad_audit_gate.py` | `M:W4C` | `                    failed += 0  # M:W4C` | `tests/test_h_mad_tdd_judge.py::test_scoring_kinds[red]` |

**`codex_gate_judge_wiring.json`** — `command`
`["/opt/anaconda3/bin/python", "-m", "pytest", "tests/test_h_mad_codex_tdd_gate_judge.py", "tests/test_h_mad_codex_runtime.py", "-q"]`;
`file` `hooks/h-mad-codex-tdd-gate.py`:

| Row | find | replace | test |
|---|---|---|---|
| G1 | `M:G1` | `    if False:  # M:G1` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_payload_cwd_base_resolves_a_subproject_relative_target` |
| G2 | `M:G2` | `    except ZeroDivisionError as exc:  # M:G2` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_gate_kind[judge-error]` |
| G3 | `M:G3` | `    return Path(os.path.realpath(p))  # M:G3` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_venv_token_keys_on_the_lexical_name` |
| G4 | `M:G4` | `        text = state_file.read_text(encoding="utf-8")  # M:G4` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_fifo_state_off_the_chain_denies_shell_without_blocking` |
| G5 | `M:G5` | `    for raw in (targets if phase5_status != "inactive" else []):  # M:G5` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_unsearchable_docs_on_the_chain_denies_although_the_scan_is_inactive` |
| G6 | `M:G6` | `    if False:  # M:G6` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_shell_venv_token[sub-cwd-escaping]` |
| G6B | `M:G6` | `    if False:  # M:G6` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_shell_venv_token[root-cwd-escaping]` |
| G7 | `M:G7` | `        if c.is_dir():  # M:G7` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_payload_cwd_outside_the_root_falls_back_to_the_root` |
| G8 | `    if executable.startswith("python") and len(argv) >= 3 and argv[1:3] == ["-m", "pytest"]:` (untagged, unchanged by this feature; 1 matching line at `a1478ad3`) | `    if executable.startswith("python"):` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_venv_token_still_obeys_the_argv_rules` |
| G6C | `M:G6` | `    if False:  # M:G6` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_shell_control_allowlist_under_a_venv[escaping-venv]` |
| G9 | `M:G9` | `    resolved_executable = _contained_venv_executable(argv[0], root, cwd) if root is not None else _trusted_executable(argv[0])  # M:G9` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_shell_control_allowlist_under_a_venv[usr-bin-python3-control]` |
| G10 | `M:G10` | `    p = Path(os.path.normpath(os.path.join(str(root), os.path.expanduser(token))))  # M:G10` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_shell_venv_token[doubled-path]` |
| G11 | `            script.relative_to(scripts_root)` (untagged, unchanged by this feature; 1 matching line at `c93da638`) | `            script.relative_to(script.anchor)` | `tests/test_h_mad_codex_tdd_gate_judge.py::test_shell_control_allowlist_under_a_venv[script-outside-scripts]` |
| W1R | `M:W1` | the Task 6 remove line | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_gate_kind[red-measured]` |
| W1F | `M:W1` | the Task 6 force line | `tests/test_h_mad_codex_tdd_gate_judge.py::test_codex_gate_kind[test-passing]` |
| W5AR | `M:W5A` | the Task 6 remove line | `tests/test_h_mad_codex_tdd_gate_judge.py::test_root_step5_governs_a_subproject_with_its_own_state` |
| W5AF | `M:W5A` | the Task 6 force line | `tests/test_h_mad_codex_runtime.py::test_codex_hook_scopes_nested_state_to_the_target_project` |

**`claude_gate_judge_wiring.json`** — `command` `tests/test_h_mad_tdd_gate_judge.py`
`tests/test_h_mad_tdd_gate_docs.py`; `file` `hooks/h-mad-tdd-gate.sh` unless stated; `T` =
`tests/test_h_mad_tdd_gate_judge.py`:

| Row | find | replace | test |
|---|---|---|---|
| H1A | `M:H1` | the tuple without `tool_input.get("file_path"), ` | `T::test_claude_code_payload_reaches_codex_authorship` |
| H1B | `M:H1` | the tuple without `payload.get("file_path"), ` | `T::test_stdin_target_fields[top-level-file-path]` |
| H1C | `M:H1` | the tuple without `, payload.get("path")` | `T::test_stdin_target_fields[top-level-path]` |
| H2 | `M:H2` | `  TARGET_PATH=${1:-$TP}  # M:H2` | `T::test_stdin_target_beats_positional` |
| H3 | `M:H3` | `command -v jq >/dev/null 2>&1 \|\| _allow; _read_state --target "$TARGET_PATH"  # M:H3` (DD-2's revert) | `T::test_no_jq_on_path_still_judges` |
| H4 | `M:H4` | `if [[ $JOUT =~ $JUDGE_ALLOW_RE ]]; then _allow; fi  # M:H4` | `T::test_judge_stub_is_judge_error[allow-rc1]` |
| H5 | `M:H5A` (form `a`) or `M:H5B` (form `b`) | `  exit 1  # M:H5A`, or `    :  # M:H5B` | `T::test_refusal_sites_use_the_chosen_form[codex-authorship]` |
| H6 | `M:H6` | `_find_judge; _read_state --target "$TARGET_PATH"; case "${TARGET_PATH##*/}" in  # M:H6` | `T::test_exempt_write_on_unreadable_chain_is_allowed[state-file]` |
| H7 | `M:H7` | `_lexists() { [ -e "$1" ]; }  # M:H7` | `T::test_fast_path_defers[dangling-state-symlink]` |
| H8 | `M:H8` | `  d=$(dirname "$2"); d=$(cd "$d" 2>/dev/null && pwd -P) \|\| return 1  # M:H8` | `T::test_fast_path_defers[missing-parent]` |
| H10 | `M:H10` | `  true && return 0  # M:H10` | `T::test_fast_path_defers[unsearchable-docs]` |
| H11 | `M:H11` | the same line with `os.path.normpath(os.path.join(sys.argv[1],sys.argv[2]))` → `os.path.join(sys.argv[1],sys.argv[2])` | `T::test_traversal_target_is_gated[absolute]` |
| H12 | `M:H12` | `    sys.exit(0)  # M:H12` | `T::test_non_json_stdin_never_falls_back_to_positional` |
| H13 | `M:H13` | `  _allow  # M:H13` | `T::test_empty_target_rule[active-root]` |
| H14 | `M:H14`, in `scripts/h_mad_tdd_judge.py` | `            dirs = []  # M:H14` | `T::test_outside_root_target_is_governed_by_root[active]` |
| H15 | `M:H15` | `_dir_match() { case "$1" in */fixtures/*) return 0 ;; esac; return 1; }  # M:H15` | `T::test_relative_targets[dot-tests-relative]` |
| H15B | `M:H15` | `_dir_match() { case "$1" in */tests/*) return 0 ;; esac; return 1; }  # M:H15` | `T::test_relative_targets[fixtures-relative]` |
| H18 | `M:H18` | `:  # M:H18` | `T::test_relative_targets[tests-relative]` |
| H18B | `M:H18` | the same line with `"$R"/*)` → `$R/*)` | `T::test_root_name_glob_characters_are_literal` |
| H19 | `M:H19` | `  DIR_SUBJECT=$TARGET_PATH; if _dir_match "$DIR_SUBJECT"; then _allow; fi  # M:H19` | `T::test_root_under_a_test_directory_is_governed[tests-root-relative]` |
| H20A | `M:H20` | `elif _dir_match "$RAW_TARGET"; then  # M:H20` | `T::test_outside_root_exemption_needs_both_spellings[traversal-absolute]` |
| H20B | `M:H20` | `elif _dir_match "$TARGET_PATH"; then  # M:H20` | `T::test_outside_root_exemption_needs_both_spellings[dotdot-relative]` |
| H16 | `M:H16` | `JRC=${JOUT##*rc=}; JOUT=$(printf '%s' "${JOUT%rc=*}")  # M:H16` | `T::test_judge_stub_is_judge_error[trailing-blank-line]` |
| H17 | `M:H17` | `  SRC=${SOUT##*rc=}; SOUT=$(printf '%s' "${SOUT%rc=*}")  # M:H17` | `T::test_state_stub_is_judge_error[trailing-blank-line]` |
| C2G | `M:C2`, in `scripts/h_mad_tdd_judge.py` | `            continue  # M:C2` | `T::test_unreadable_chain_refuses_production` |
| C3G | `M:C3`, in `scripts/h_mad_tdd_judge.py` | the same line with `all(` → `any(` | `T::test_codex_escape_needs_every_record[exhausted-then-none]` |
| W2R | `M:W2` | the Task 8 remove line | `T::test_new_production_file_with_passing_test_is_refused` |
| W2F | `M:W2` | the Task 8 force line | `T::test_claude_gate_kind[red-measured]` |
| W5BR | `M:W5B` | the Task 8 remove line | `T::test_subproject_step5_under_root_step3_is_governed` |
| W5BF | `M:W5B` | the Task 8 force line | `T::test_state_without_step5_is_allowed` |
| W5BF2 | `M:W5B` | the Task 8 force line | `T::test_empty_target_rule[no-step5-root]` |
| W5BF3 | `M:W5B` | the Task 8 force line | `T::test_outside_root_target_is_governed_by_root[no-step5]` |
| W6R | `M:W6` | the Task 8 remove line | `T::test_symlinked_hook_runs_its_own_trees_judge` |
| W6F | `M:W6` | the Task 8 force line | `T::test_symlinked_hook_runs_its_own_trees_judge` |
| T1 | `M:T1` | `:  # M:T1` | `T::test_trap_member_refuses_in_form[realpath-stub]` |
| T2 | `M:T2` | `  exit "$rc"  # M:T2` | `T::test_trap_member_refuses_in_form[unset-variable]` |
| D1 | `M:D1`, in `tests/test_h_mad_tdd_gate_docs.py` | `    starts = starts or [0]  # M:D1` | `tests/test_h_mad_tdd_gate_docs.py::test_locators_fail_loudly[hook-line]` |

(`T::` abbreviates the table only; each JSON `test` key is written in full,
`tests/test_h_mad_tdd_gate_judge.py::` followed by the test name.) A `\|` in the table is a literal `|` in the spec.
H16 and H17 restore command substitution's stripping of every trailing newline, the pre-v1.1
capture (Deviation 11), so a line followed by a blank one reads as one valid line. C2G reads the
root's `{not json` state as skippable, so the chain is `none` and the gate allows the production
write that AC-6.9 refuses. C3G (reasoned, not executed: the code does not exist yet) sets
`codex-escape=yes` while `blocker=2`, and the gate's `blocker=0`-iff-`codex-escape=yes`
cross-check then refuses `judge-error`, not the `codex-authorship` AC-6.10 asserts.

15 + 8 + 3 + 6 + 6 + 6 + 17 + 37 = 98 rows. Per owning task: Task 1 15, Task 2 3, Task 3 12,
Task 4 8, Task 5 6, Task 6 9, Task 7 8, Task 8 36, Task 9 1;
15 + 3 + 12 + 8 + 6 + 9 + 8 + 36 + 1 = 98.

Executed readings for the v1.2 codex-gate rows (a scratch copy of today's
`h-mad/hooks/h-mad-codex-tdd-gate.py` with Task 6's `_payload_cwd_base` and Task 7's helper and
one-line change applied verbatim, and `_load_judge()` returning a stub whose `venv_contained` is
Task 3's three-conjunct literal; `_safe_shell_command(command, root, cwd)` called in process under
`/usr/bin/python3` 3.9.6 at `c93da638`; deleted). Unmutated, the cells read: `[doubled-path]`
`False`, `[escaping-venv]` `False`, `[usr-bin-python3-control]` `True`,
`[script-outside-scripts]` `False`, the contained `-m pytest` cell `True`. Each mutant flips its
own cell: G10 `[doubled-path]` → `True`; G6C (G6's replacement) `[escaping-venv]` → `True`; G9
`[usr-bin-python3-control]` → `False`; G11 `[script-outside-scripts]` → `True`. The same copy
also executed the v1.1 rows G6 and G6B (`[sub-cwd-escaping]` and `[root-cwd-escaping]` → `True`),
G3 (the `/bin/cat` venv, `.venv/bin/python notes.txt` → `True`) and G8 (`.venv/bin/python -c
pass` → `True`). The v1.2 claude-gate rows (H15, H15B, H18, H18B, H19, H20A, H20B) were executed
in Task 8 step 7's scratch script: each flips the verdict of the cell its row's test runs, and
of the 126 differential cells H15 changes 18, H15B 9, H18 12, H19 12, and H18B, H20A and H20B
none (their cells lie outside that corpus). E1's mutant, on the scratch copy
of Task 1's support block, keeps `CLAUDE_ZZZ_PROBE` in `hermetic_env()`.

**Initially-green guards** (invariant §"Test discrimination": a check never seen failing is not
trusted). Every new item that passes at RED, with the row whose mutant makes it fail; the six
`c-…` cells are the only items with no row, and they claim no coverage (v1.2). Rows marked
executed were killed on a scratch copy before this revision; E1 and S8–S12 likewise. P1, P1B,
P2, K3B, K5, R2, W1R, G7, W2F, W5BF, W5BF2, W5BF3 and D1 mutate code that does not exist yet
(or, for P1B, a test whose corpus v1.2 re-rooted), so their first killing run is this task's
harness run, which halts on `SURVIVED`:

| Task | Item passing at RED | Row |
|---|---|---|
| 1 | `test_run_suite_table_row[subtests-passed]` | S1 |
| 1 | `test_run_suite_table_row[stray-failed-on-stderr]` | S3 |
| 1 | `test_run_suite_table_row[one-error\|no-tests-ran\|three-skipped\|five-deselected\|one-xfailed]` | S12 (scored on `three-skipped`; executed on it and on `one-error`; one predicate decides all five) |
| 1 | `test_run_suite_table_row[passed-and-error]` | S10 |
| 1 | `test_run_suite_table_row[failed-and-passed]` | S11 |
| 1 | `test_run_suite_table_row[collected-zero]` | the committed `audit_suite_gate.json` row `a-missing-summary-becomes-a-verdict` (its subject, the `summary is None` return, is unchanged) |
| 1 | `test_suite_summary_reads_the_line[collected-zero\|failed-node-line]` | S8 (scored on `failed-node-line`; executed on both) |
| 1 | `test_suite_summary_reads_the_line[capitalised-category]` | S9 |
| 1 | `test_suite_summary_reads_the_line[quoted-assert]` | S8B (executed; S8 alone leaves it `None`) |
| 1 | `test_hermetic_env_drops_claude_names_and_backend` | E1 |
| 2 | `test_existing_fields_unchanged`, `test_corpus_old_fields_unperturbed`, `test_field_re_is_unchanged` | P1, P1B, P2 |
| 4 | `test_rc_selects_nothing[silent-rc1]`, `test_whole_line_no_module_is_pytest_missing_even_after_red` | K3B, K5 |
| 5 | `test_none_valued_production_does_not_match` | R2 |
| 6 | `test_codex_gate_kind[red-measured]`, `test_payload_cwd_outside_the_root_falls_back_to_the_root` | W1R, G7 |
| 7 | `test_shell_venv_token[sub-cwd-escaping\|root-cwd-escaping]`, `test_venv_token_keys_on_the_lexical_name`, `test_venv_token_still_obeys_the_argv_rules` | G6, G6B, G3, G8 (each executed, v1.2) |
| 7 | `test_shell_control_allowlist_under_a_venv[escaping-venv]` | G6C (executed) |
| 7 | `test_shell_venv_token[doubled-path]` | G10 (executed) |
| 7 | `test_shell_control_allowlist_under_a_venv[usr-bin-python3-control]` | G9 (executed) |
| 7 | `test_shell_control_allowlist_under_a_venv[script-outside-scripts]` | G11 (executed; v1.2 fixture, Task 7 item 2) |
| 7 | the six `test_shell_venv_token[c-…]` cells | no coverage claimed (Task 7 §"No coverage claimed"): spec AC-3.4 conformance only; the discrimination claim is item 5's, G8 (OQ-I4) |
| 8 | `test_claude_gate_kind[red-measured]`, `test_state_without_step5_is_allowed`, `test_empty_target_rule[no-step5-root]`, `test_outside_root_target_is_governed_by_root[no-step5]`, `test_relative_targets[dot-tests-relative]` | W2F, W5BF, W5BF2, W5BF3, H15 (H15 executed, v1.2) |
| 9 | `test_locators_fail_loudly[hook-line]` | D1 |
| 9 | `test_locators_fail_loudly[trust-boundary\|helper-scripts\|tdd-gate]` | the committed `docsections.json` (Task 9 §"Expected RED split") |

Items that fail at RED are observed failing by their RED run. Task 3's 80 items are observed
failing only as one collection error; their guards are the Task 3 rows.

**Acceptance Criteria**:
- [ ] AC-8.1: each guard spec AC-8.1 names has its row: Task-match authority R1; `none` rule R2;
  containment V1–V3; `pytest-missing` K1; `errors ≥ 1` K2; rc-blindness K3; payload `cwd` G1; chain
  reader C1 (and W5AR); `tool_input` read H1A; blocking form H5; non-zero-rc refusal H4;
  `state`-verb governance W5BR; unreadable-chain refusal C2G (C2's mutant scored on the named AC-6.9
  test `test_unreadable_chain_refuses_production`); every-record escape C3G (C3's mutant scored on
  the named AC-6.10 test `test_codex_escape_needs_every_record[exhausted-then-none]`); C2 and C3
  stay as the judge-level rows; exemptions-before-governance H6; stdin-before-`$1` H2; fast-path
  non-regular state H7 and missing parent H8, each alone; empty-target refusal H13; outside-root
  chain H14; SGR strip S4; `subtests` category rule S5; rule 8 K4. Each alternation branch is its
  own row (S1/S2, S7A/S7B, H1A/H1B/H1C).
- [ ] All eight specs `ALL_CAUGHT` with `crash_kills=0`.

**Mutation rows**: the 98 above. **Dependencies on other tasks**: Task 9

---

## Task 11: phase5-merge-gate

**Production file**: `docs/03-analysis/probes/codex-tdd-gate-defects/parse_corpus.py` (new),
`docs/03-analysis/probes/codex-tdd-gate-defects/judge_latency.py` (new)
**Test file**: none
**Task shape**: `gate`

**Description**: design Implementation Order step 9 and plan §"Success Criteria". Read every token;
never read `$?`.
1. **Suite**: Convention 1's command → only the baseline node may fail, and only if Task 0
   recorded it failing at `BASE_SHA` for the same reason; the same command with
   `CLAUDE_ZZZ_PROBE=1` exported → the same summary. Collected count at 5g = the Task-0 count +
   302 new items + 2 portable-timeout nodes (3893 + 304 = 4197 at a `f6b258f0` base; re-derived at
   the real base, never carried).
2. **Node-id floor**: collect at `HEAD` as in Task 0 item 5, then
   `comm -23 "$(git rev-parse --absolute-git-dir)/hmad-ctg-base-nodeids.txt" <head file>` prints
   nothing.
3. **Top-level diff**: `toplevel_diff.py --base "$BASE_SHA"` → its `changed`/`removed` lines equal
   §"Regression provenance" for the chosen form exactly.
4. **Anchors**: Convention 8's sweep → `ANCHORS_OK drifted=0`.
5. **Self-check**: `python3 h-mad/hooks/h-mad-codex-tdd-gate.py --self-check` →
   `CODEX-TDD-GATE: PASS`.
6. **V-1r** (merge condition):
   `bash docs/03-analysis/probes/codex-tdd-gate-defects/v1-offline-replay.sh <worktree> /Users/kimhawk/orca/HemaSuite > v1r.out`
   → a line `V-1r: DONE VERDICT=PASS fails=0/6 `.
7. **`reproduce.py` post-merge reading**: the five fail-open readings (`D3 nopytest`,
   `OD-3 nearest-state`, `OD-4 tool_input`, `OD-3c claude-root-first`, `OD-5 nopytest`) read
   `(0, 'deny', …)` on the Codex side and `(2, '', …)` under `a` or `(0, 'deny', '')` under `b` on
   the Claude side; committed beside the pre-merge reading.
8. **5g greps** (unit: matching lines): `grep -c '^\s*exit 1\s*$' h-mad/hooks/h-mad-tdd-gate.sh`
   → 0; `grep -c 'orchestrator_state' h-mad/hooks/h-mad-tdd-gate.sh` → 0;
   `grep -c '_resolve_state_file' h-mad/hooks/h-mad-tdd-gate.sh` → 0;
   `git grep -n "h_mad_derive_test_path.sh" -- h-mad/hooks` → no match;
   `grep -c 'subprocess.run' h-mad/scripts/h_mad_tdd_judge.py` → 0;
   `git diff --stat "$BASE_SHA" -- h-mad/scripts/h_mad_wire_registry.py` → empty (AC-2.9).
9. **Stale-prose re-read**: plan §"Stale-prose census"'s `git grep -c` re-run; every hit read
   against the shipped gate, and the path-constant census `grep -n 'Path.home() / ".claude"' h-mad/tests/*.py`
   re-read by hand for this feature's files.
10. **`parse_corpus.py BASE_SHA HEMASUITE_ROOT`** (probe): `h_mad_wire_pin_gate.py` does
    `import h_mad_wire_registry` at module top, and that module does
    `from h_mad_audit_gate import _acknowledged_from_text` (both read at `a1478ad3`), so the base
    parser is not importable alone. The probe writes
    `git show "$BASE_SHA":h-mad/scripts/<name>.py` for `h_mad_wire_pin_gate`, `h_mad_wire_registry`
    and `h_mad_audit_gate` into one `tempfile.TemporaryDirectory`, then runs two child processes
    (`[sys.executable, "-c", <reader>, <scripts dir>, <file>…]`, `stdin=subprocess.DEVNULL`,
    `timeout=60.0`), one with the temporary directory and one with the worktree's `h-mad/scripts`
    at `sys.path[0]`, so the two versions never share a `sys.modules`. Each child prints, per
    file, the JSON of its `_parse_tasks` ids and old fields. The parent compares them over the
    tracked non-`archive/` `*.impl-plan.md` files of both repositories, and prints `PARSECORPUS: files=N id_mismatch_files=N py_symbol_label_lines=N parenthesised_label_lines=N`
    (units: files, files, matching lines, matching lines). Pass: `id_mismatch_files=0` (AC-2.9).
    The two residual counts are design D5's owed reading (2 and 1 at skills `1ef1a782` /
    HemaSuite `3f0c9f3a`), recorded with their shas, never compared.
11. **`judge_latency.py HEMASUITE_ROOT`** (probe): times `h_mad_tdd_judge.judge` over the four Task 7
    candidates of HemaSuite `31bfcfe4` in a scratch snapshot (V-1r's snapshot method), and prints
    `LATENCY: runs=3 worst_s=N budget_s=40.0`. Pass: `worst_s` below the budget (design D6 re-measure;
    12.93 s through pytest alone, design reading).
12. **OQ-D1 host-deadline probe** (merge condition, run by the operator or the orchestrator in the
    live Claude Code session V-0 used): a governed production write whose resolved test sleeps
    35 s and then fails; pass when the gate's own ALLOW lands. If the host cancels first, the
    registration gains an explicit `timeout` in the unit the probe shows, and the probe re-runs.
13. **Wire-pin gate**:
    `python3 h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md`
    → `WIREPIN: PASS tasks=12 wiring=4`.

**Acceptance Criteria**:
- [ ] NFR Compatibility: items 1, 2, 3, 5. V-1r: item 6. AC-2.9: items 8 and 10. OQ-D1 (Claude
  half): item 12.

**Mutation rows**: none. **Dependencies on other tasks**: Task 10

---

## Regression provenance

Every pre-existing top-level statement this plan changes, by file and key (Task 11 item 3 compares
this list with `toplevel_diff.py`'s output). Nothing is removed.

**On either form** (7 keys):
- `h-mad/tests/test_h_mad_audit_suite_gate.py::run` — Task 1, `stdin=subprocess.DEVNULL` added
  (Convention 4; not an assertion change). Omitted through v1.2 and found by Task 11 item 3's
  first reading (`changed=20` against 19); added in v1.3.
- `h-mad/tests/test_h_mad_audit_suite_gate.py::TestTheSuiteVerdictIsScoredOnTheSummary` — Task 1,
  the docstring of `test_an_empty_selection_is_not_a_pass` (prose only; it asserted nothing about
  that sentence).
- `h-mad/tests/test_h_mad_codex_runtime.py::test_codex_hook_rejects_pytest_no_tests_collected_as_red`
  — Task 6, `"exit 1"` → `"no-tests-ran"` (it pinned the rc scoring FR-4 removes).
- `h-mad/tests/test_h_mad_tdd_gate_codex.py::HOOK` and
  `h-mad/tests/test_h_mad_tdd_gate_state_resolution.py::HOOK` — Task 8, the worktree path (layer 6);
  on `main` the value resolves to the same file.
- `h-mad/tests/test_h_mad_tdd_gate_codex.py::_run` and
  `h-mad/tests/test_h_mad_tdd_gate_state_resolution.py::_run` — Task 8, `stdin=subprocess.DEVNULL`
  added (not an assertion change).

**Under `REFUSAL_FORM=a`** (5 more keys; 12 in all): `test_h_mad_tdd_gate_codex.py::test_non_step5_ignores_codex_gate`
(`stdin=` only), `::test_blocks_claude_prod_write_when_codex_available` (rc 1 → 2);
`test_h_mad_tdd_gate_state_resolution.py::test_gate_finds_state_one_directory_down`,
`::test_repo_root_layout_still_works`,
`::test_a_production_file_under_a_test_named_directory_is_still_gated` (rc 1 → 2).

**Under `REFUSAL_FORM=b`** (13 more keys; 20 in all): every test function of both modules — the 6
of `test_h_mad_tdd_gate_codex.py` and the 7 of `test_h_mad_tdd_gate_state_resolution.py`
(collected 6 and 7 at `f6b258f0`) — with the assertion moves spec AC-6.2 lists; both modules gain
`from tdd_gate_support import decision, hook_form` (a new import, not a changed key).

## After Phase 5 (not tasks)

- **grok-codex-fallback rebases onto this feature after it merges** (design §D13). Its Task 12 and
  Task 14 are re-planned onto the `state` line's fourth `record=` subfield, a fold in the judge,
  `_refuse fallback-grok` / `_refuse fallback-invalid` and the D10 ERE, and its Expected RED split
  and mutation rows are re-derived there. Nothing here plans or edits grok's documents.
- **multi-host-runtime** rebases after grok; its §"Convention Prerequisites" table still says this
  feature does not name `h-mad/SKILL.md` (plan: owed to that document).
- **Live V-1** stays blocked on `~/.agents/skills/h-mad` (owned by `multi-host-runtime`); it is not
  a merge condition.
- **OQ-D1, Codex half** stays open: the Codex gate is not registered on this machine (design D6).

## AC coverage

| AC | Task · test or step |
|---|---|
| AC-0.1 | orchestrator (V-0); Task 0 item 2 records it |
| AC-0.2 | orchestrator (V-0); Task 8 precondition reads `CHOSEN=` |
| AC-1.1 | Task 8, `test_hooks_reach_the_name_map_only_through_the_judge`; Task 11 item 8 |
| AC-1.2 | Task 6, `test_codex_gate_kind[…]`; Task 8, `test_claude_gate_kind[…]` |
| AC-1.3 | Task 8, `test_judge_stub_is_judge_error[…]`, `test_state_stub_is_judge_error[…]` |
| AC-2.1 | Task 5, `test_hemasuite_layout_resolves_from_the_task` |
| AC-2.2 | Task 2, `test_paths_label_spelling[…]`; Task 5, `test_label_spelling_resolves_the_same[…]`, `test_tests_prose_line_contributes_no_candidate` |
| AC-2.3 | Task 2, `test_none_value_contributes_nothing[…]`; Task 5, `test_none_valued_production_does_not_match` |
| AC-2.4 | Task 5, `test_several_candidates_first_red_allows`, `test_several_candidates_all_green_names_both` |
| AC-2.5 | Task 5, `test_task_match_is_authoritative_over_the_name_map` |
| AC-2.6 | Task 4, `test_name_map_source_allows_via_the_cli[…]` (both ids) |
| AC-2.7 | Task 3, `test_unmapped_path_is_no_test_resolved` |
| AC-2.8 | Task 3, `test_unreadable_plan_is_named_in_test_missing`; Task 4, `test_unreadable_plan_with_a_passing_name_map_test_is_test_passing` |
| AC-2.9 | Task 2 regression guards and `test_corpus_old_fields_unperturbed`; Task 11 items 8 and 10 |
| AC-3.1 | Task 4, `test_contained_venv_shim_runs_pytest` |
| AC-3.2 | Task 3, `test_escaping_venv_denies_before_any_run`, `test_venv_contained_rows[…]` |
| AC-3.3 | Task 4, `test_real_venv_interpreter_symlink_is_accepted` |
| AC-3.4 | Task 7, `test_shell_venv_token[…]` |
| AC-3.5 | Task 7 guard, `test_codex_hook_rejects_untrusted_executable_paths` |
| AC-3.6 | Task 7, `test_shell_control_allowlist_under_a_venv[…]`, the corpus test and the probe |
| AC-4.1 | Task 3, `test_pytest_missing_denies[…]` (both ids) |
| AC-4.2 | Task 4, `test_scoring_kinds[…]`, every id except `import-error` |
| AC-4.3 | Task 4, `test_scoring_kinds[import-error]` |
| AC-4.4 | Task 4, `test_rc_selects_nothing[…]` |
| AC-4.5 | Task 3, `test_timeout_kind` |
| AC-4.6 | Task 4, `test_scoring_kinds[import-error]` (reason words) |
| AC-4.7 | Task 1, `test_run_suite_table_row[…]`, `test_suite_summary_reads_the_line[…]` |
| AC-5.1 | Task 6, `test_payload_cwd_base_resolves_a_subproject_relative_target`, `test_payload_cwd_deny_names_the_prefixed_path` |
| AC-5.2 | Task 6, `test_root_step5_governs_a_subproject_with_its_own_state`; Task 3, `test_chain_reads_every_state_file_up_to_root` |
| AC-5.3 | Task 6, the changed assertion and the two unmodified tests |
| AC-5.4 | Task 6, `test_codex_gate_kind[judge-error]` |
| AC-6.1 | Task 8, items 4, 5, 6 |
| AC-6.2 | Task 8, the migration; §"Regression provenance" |
| AC-6.3 | Task 8, `test_no_pytest_on_path_passing_test_is_refused` |
| AC-6.4 | Task 8, `test_new_production_file_with_passing_test_is_refused` |
| AC-6.5 | Task 8, items 10, 11, 32 (branch `E1_DOES_NOT_BLOCK`) |
| AC-6.6 | Task 8, items 10, 11, 32 and the docstring (branch `E1_BLOCKS`) |
| AC-6.7 | Task 8 precondition; plan R1 |
| AC-6.8 | Task 8, `test_subproject_step5_under_root_step3_is_governed` |
| AC-6.9 | Task 8, `test_unreadable_chain_refuses_production`, `test_exempt_write_on_unreadable_chain_is_allowed[…]` |
| AC-6.10 | Task 8, `test_codex_escape_needs_every_record[…]`, `test_codex_escape_all_declared_proceeds_to_judge[…]` |
| AC-6.11 | Task 8, `test_fast_path_defers[dangling-state-symlink]`, `test_fast_path_defers[missing-parent]` |
| AC-6.12 | Task 8, `test_no_jq_on_path_still_judges` |
| AC-6.13 | Task 8, `test_empty_target_rule[…]` |
| AC-6.14 | Task 8, `test_outside_root_target_is_governed_by_root[…]`, `test_outside_root_exemption_needs_both_spellings[…]` |
| AC-6.15 | Task 8, `test_relative_targets[…]`, `test_traversal_target_is_gated[…]`, `test_dd7_differential_matches_the_published_cells`, `test_root_under_a_test_directory_is_governed[…]`, `test_outside_root_exemption_needs_both_spellings[…]`, `test_root_name_glob_characters_are_literal`, `dd7_differential.py` |
| AC-7.1 | Task 9, `test_trust_boundary_states_the_venv_rule` and the existing test |
| AC-7.2 | Task 9, items 2–5 and 8 |
| AC-8.1 | Task 10 |

49 rows, one per spec AC id (`grep -oE '^ *- AC-[0-9]+\.[0-9]+'` over the spec, `sort -u` → 49
distinct ids at `f6b258f0`).

## Open Questions

- **OQ-I1 (orchestrator).** Step P0 and V-0 have not run at `f6b258f0` (Task 0 item 1). Task 0 halts
  until P0 is committed; Task 8 waits for a conclusive V-0.
- **OQ-I2 (design owner).** Deviation 7: the design's `[ -x "$D" ]` mutant is equivalent on the
  walk. This plan keeps the line and drops the row; the design's §"Test Strategy" still lists it.
- **OQ-I3 (closed in v1.2).** Answered by design v1.3 §D9 (`85b81698`): the root-relative
  directory-exemption subject, `RAW_TARGET` outside the root, and the 126-cell differential. Task
  8 implements it (Deviation 16, items 21–23 and 34–36, rows H15B, H18, H18B, H19, H20A, H20B);
  nothing waits on it.
- **OQ-I4 (spec owner).** Spec AC-3.4's six `-c "open('x','w')"` cells cannot observe the venv
  branch: the Codex gate's lexical subset rejects `(` and `)` before any executable is resolved
  (executed at `a1478ad3`). They are kept as the spec requires and claim no coverage (v1.2);
  Task 7 item 5 (`.venv/bin/python -c pass`, row G8) is the discriminating case. A spec revision
  may replace the argv. Not a halt: no task waits on it.
- **Carried** from plan and design: OQ-1 (no `.venv` and no pytest → `pytest-missing`), OQ-3
  (`2 passed, 1 error` scores PASS; pinned unchanged by Task 1's `passed-and-error` row), OQ-D2
  (`` `path.py::symbol` `` entries).

## Version History
- v1.0: Initial implementation plan (2026-09-28), first 5a draft; answers no audit cycle. From design v1.2, spec v1.4 and plan v1.4; premises read at f6b258f0 (h-mad, handoff, probes and pytest.ini unchanged at a85abf7f). 12 tasks: Task 0 5c gate with the top-level-diff probe, parsers (Tasks 1-2), judge core plus staged W4/W3 wiring (Tasks 3-5), Codex gate W1/W5a and shell venv branch (Tasks 6-7), Claude gate rewrite W2/W5b/W6 behind the V-0 precondition (Task 8), docs (Task 9), 64 mutation rows in eight specs (Task 10), 5g gate (Task 11); 4 wiring tasks carrying 7 wires. Ten deviations recorded, one design mutant dropped as equivalent.
- v1.1: Answers impl-plan audit cycle 1 (round 1 of 2; codex `audit.v1.p1`: 3 must; teammate `audit.v1.teammate`: 4 must, 6 should, 5 nit), 2026-09-28; premises re-read at `a1478ad3` (h-mad unchanged at `212aab9d`). Each premise was re-run before acting; no premise was refuted. **Codex must 1 (DD-7 root under `tests/`)**: premise holds (today's gate, root `<tmp>/tests/repo`: positional `x.py` rc 1, absolute rc 0; the canonical path matches `*/tests/*`); the remedy changes design §D9, so DEFERRED as a design delta: Task 8 precondition 2 halts, OQ-I3. **Codex must 2 (trailing blank line)**: FIXED, `rc=` sentinel capture executed under bash 3.2.57 (Deviation 11), `trailing-blank-line` ids in Task 8 items 2 and 3, rows H16/H17. **Codex must 3 (stderr as name-map path)**: FIXED, `_run_bounded` returns the streams apart, name map reads stdout (Deviation 12), `test_name_map_stderr_is_not_a_path`, row R5. **Teammate must 1 (FORM read at import)**: FIXED, lazy `hook_form`, `CHOSEN` from the module docstring's V-0 quote, not from `docs/` (Deviation 14). **Teammate must 2 (support code RED or GREEN)**: FIXED, lands in each task's RED commit, listed on the Test file line of Tasks 1, 3, 7, 8 (Deviation 1); Task 1 reads 23 failing / 15 passing of 38. **Teammate must 3 (30 s sleeper vs 40 s budget)**: FIXED, `sleeper(…, seconds)`, 90 s in the two gate rows. **Teammate must 4 (false RED premise)**: FIXED, Task 6 item 8 now carries the executed traceback reading (rc 1, `PermissionError`). **Teammate should 1**: FIXED (`_PATHS_LABEL_LINE` test constant). **Should 2**: FIXED (Deviation 13: start error, else summary line, else last line). **Should 3**: FIXED (rows C2G, C3G on the named AC-6.9 / AC-6.10 tests). **Should 4**: FIXED (`parse_corpus.py` copies three base files and runs two child processes). **Should 5**: FIXED (`/opt/anaconda3/bin/python` in every spec). **Should 6**: FIXED (Convention 8 names `SKILL.md`, 53 rows in 14 specs, and every other edited file at 0). **Nits**: N1 fixed (tag boundary in Convention 9), N2 fixed (Deviation 15), N3 fixed (Task 3 description), N4 fixed (gate-interpreter venv outside the root), N5 no change needed. **Proactive (dispatch rule: every initially-green guard needs a row)**: Task 10 §"Initially-green guards" added; new rows S8–S12, E1, P1, P1B, P2, K3B, K5, G6B, G7, G8, H15, W5BF2, W5BF3, D1; S8–S12 executed on scratch copies (the first S8 candidate killed nothing and was replaced); Task 7 item 5 added as the discriminating twin of spec AC-3.4's six `-c` cells, which the lexical subset decides first (OQ-I4). Counts: 296 new items (38 + 23 + 80 + 17 + 16 + 19 + 18 + 74 + 11); 87 mutation rows in eight specs; 12 tasks, 4 wiring, 7 wires, WIRE and WIRE-PIN lines unchanged.
- v1.2: Corrective revision after the 5b round cap, answering impl-plan audit cycle 2 (codex `audit.v2.p1`: 3 must, 1 should; teammate `audit.v2.teammate`: 1 must, 3 should, 4 nit) and propagating design v1.3 (`85b81698`; spec v1.4 and plan v1.4 sentences at `8322fa04`), 2026-09-28; premises re-read at `c93da638`. Every premise was re-run before acting; none was refuted. **Design v1.3 propagation / codex must 1 / teammate should 1**: FIXED. Task 8 precondition 2 and OQ-I3 lifted (OQ-I3 closed); Source header and Deviations heading read v1.3; step 4 keeps `RAW_TARGET` and sets `R` and `IN_ROOT`; step 7 matches `_dir_match` on `DIR_SUBJECT` inside the root and on both spellings outside it (Deviation 16); the symlinked-root residual (c) stated; item 21 gains `fixtures-relative`, items 21–22 re-derived (unchanged outcomes); item 23 and the probe move to 126 cells, 18 refusals, softened 6, tightened 8; new items 34–36; rows H15 (re-anchored on `_dir_match`), H15B, H18, H18B, H19, H20A, H20B, each executed with the 126-cell corpus under `/bin/bash` 3.2.57 in a scratch script (deleted). **Codex must 2**: FIXED, the support module's first contents carry the docstring, `from __future__ import annotations` and `import os`; executed under 3.9.6 and 3.11.8, and v1.1's literal reproduced `NameError`. **Codex must 3**: FIXED. `quoted-assert` → S8B; `[doubled-path]` → G10; `[escaping-venv]` → G6C (until then reasoned); `[usr-bin-python3-control]` → G9; `[script-outside-scripts]` → G11, with the fixture changed to a script named `h_mad_wire_registry.py` outside `scripts/` (v1.1's `tools.py` was held by two rules, so no single mutant could make it fail); each killed on a scratch copy. The six `c-…` cells now claim no coverage (two independent rules deny each, so no single-site row can make one fail); G8 on Task 7 item 5 is AC-3.4's discrimination claim. G3, G6, G6B, G8, H15 and E1 were also executed. **Codex should (floor import)**: FIXED, each Task 3 floor id also imports its module under `/usr/bin/python3`; the three existing modules import today. **Teammate must (P1B cwd)**: FIXED, Task 2 item 8 runs `git -C <REPO_ROOT>` and reads paths from `REPO_ROOT`, with non-vacuity asserted (≥ 1 file, ≥ 1 removed `.py`-token line; 11 files and 105 lines at `c93da638`; 0 files from `h-mad/` without `-C`). **Teammate should 2 (V1 fixture)**: FIXED, the outside directory holds a regular `pyvenv.cfg`, and the row's oracle asserts it (executed: mutant `False` without it, `True` with it). **Teammate should 3 (`_SUITE_RE` census)**: FIXED, `git grep -nw … -- h-mad handoff` → 2 lines, with the 4-line and 11-line readings of the other spellings. **Nits**: N1 fixed (`_test_missing(candidates, notes, root)` signature, name-map wrapping); N2 fixed (item 28 states the `rc=0` reason after a `set -u` abort; T2 still killed on deny; executed); N3 fixed (Deviation 14 rationale); N4 fixed (`fake_venv` then `sleeper` over its `bin/python`). **Remaining halts**: none on a design delta; Task 0's P0 gate and Task 8's FR-0 V-0 precondition are unchanged operator preconditions. Counts: 302 new items (38 + 23 + 80 + 17 + 16 + 19 + 18 + 80 + 11); 98 mutation rows in eight specs (15 + 8 + 3 + 6 + 6 + 6 + 17 + 37); 12 tasks, 4 wiring, 7 wires, WIRE and WIRE-PIN lines unchanged.
- v1.3: Task 11 item 3 amendment (2026-09-29). §"Regression provenance" gains `h-mad/tests/test_h_mad_audit_suite_gate.py::run` (Task 1, `stdin=subprocess.DEVNULL`), omitted through v1.2 and found by item 3's first reading (`changed=20` against 19); totals now 7 / 12 / 20. No task, row or count elsewhere changes.
