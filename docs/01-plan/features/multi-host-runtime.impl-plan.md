# Implementation Plan: multi-host-runtime

> Source: docs/02-design/features/multi-host-runtime.design.md (v1.3, binding, including its
> §"Supersedes the plan on", §"Spec restatements this design depends on" and the v1.3 erratum),
> docs/01-plan/features/multi-host-runtime.spec.md (v1.4, 51 ACs, binding),
> docs/01-plan/features/multi-host-runtime.plan.md (v1.3: §"Connection enforcement" W1–W3, the
> 5c "Rebase, then baseline" step and the Phase-7 smoke stay binding)
> Branch target: `feature/multi-host-runtime` (a git worktree; plan §"Convention Prerequisites")
> 5c baseline: branch `feature/217-multi-host-runtime`, worktree `/Users/kimhawk/orca/skills-multi-host-runtime`, forked from main `3b5c4388` (impl-plan v1.2 + delta review v1.2)

## Executive Summary

Nineteen tasks, each counted once. Two 5c tasks come first: Task 0 authors and runs the first
three probe-sidecar files (design v1.3 Implementation Order step 1: the first commit after the 5c
impl-plan commit, by orchestrator decision), and Task 1 takes the remaining 5c readings. No
production task starts before Task 0's calibration reading is committed. Strand 1 is the parity checker (Task 2)
and the registry (Task 3). Strand 2 is the host classifier (Task 4) and the three `wiring` tasks
W1–W3 (Tasks 5, 6, 7). Strand 3 is the six adapters, one per task (Tasks 8–13). Strand 4 is the
two `SKILL.md` edits (Task 14). Task 15 authors and scores the 117 mutation rows in four specs.
Tasks 16 and 17 author the rest of the probe sidecar (`byte_identity.py`, then `smoke_assert.py`
with `rehearsal/`). Task 18 is the full coupled-suite gate.
2 + 2 + 1 + 3 + 6 + 1 + 1 + 2 + 1 = 19.

## Deviations from design v1.3

The design is binding. Each item below is an addition or a precision the design leaves open, stated
with its evidence. None changes a design decision: Deviation 7 was the one real conflict, and
design v1.3 resolved it by orchestrator decision (item 7 below). An auditor reading both documents
follows this section where they differ.

1. **One helper fixture, `hermetic_env`, is appended to `h-mad/tests/conftest.py` in Task 4**, in
   addition to design §D7's `_hermetic_host_skill_roots` (Task 7). Orchestrator decision: every
   subprocess test strips every `^CLAUDE` name and `HPW_AGENT_BACKEND` from the child's
   environment and must hold under an extra ambient `CLAUDE_ZZZ_PROBE=1`, because the
   orchestrator runs inside Claude Code with about fifteen `CLAUDE*` exports. It is load-bearing
   here: `h_mad_context_budget.resolve_transcript` reads `CLAUDE_TRANSCRIPT_PATH` and
   `CLAUDE_CODE_SESSION_ID`, and the `--window` default reads `HMAD_CONTEXT_WINDOW` (read in
   `h-mad/scripts/h_mad_context_budget.py` at `7e155451`). One fixture serves every test file,
   instead of one private copy per file. Both conftest additions are appends; no existing line
   changes.
2. **Named killing tests the design's mutation table implies but its Test Plan does not list.**
   Each is the named test of a design mutation row, or the per-branch rule of `invariants.base.md`
   §"Test discrimination":
   - `test_default_axes_report_each_fixture[A1|A2|A3|A4-tilde|A4-home|A4-home-braced]` kills "each
     axis dropped from `CATCH_ALL_AXES`" and "each `A4_BRANCHES` entry dropped" by assertion. The
     design's per-axis tests pass their own `axes=`, so they never read the dropped constant
     entry;
   - `test_fenced_pipe_table_is_not_the_table` is the design's "a fixture holding a pipe table
     inside a fence before the real one";
   - `test_split_prefix_does_not_capture_a_longer_name` is the design's "a fixture with skills
     `h-mad` and `h-mad-x`";
   - `test_hermetic_env_drops_claude_names_and_backend` is the control of item 1;
   - `test_host_runtime_locator_fails_loudly[renamed|doubled]` executes AC-7.3;
   - parametrize ids added to three design tests, so each alternative is its own node:
     `test_branch_expander_refuses_unsupported_shapes[group-plus|atom-brace|unbalanced]`,
     `test_host_cli_stub_control_fires[codex|agy|grok]` and
     `test_env_override_is_read[agents|agy]`.
3. **Mutation rows: 117, from the design's 88 members, plus 1 per-branch split row, plus 8 wire
   rows, plus 20 guard rows (item 9).** The design's table heading reads "each one mutant per member". Its members are:
   `host_parity.json` 65 (42 + 5 + 4 + 3 + 6 + 1 + 1 + 1 + 1 + 1, Task 15),
   `host_declaration.json` 13, and `install_check_roots.json` 10. The install table's 7 classes
   expand to 10 members because three classes name one member per root: "the env override read
   dropped", "an empty override read as unset" and "the override preferred over an explicit
   option", each for `agents` and `agy`. The 1 split row: plan v1.3's suppression rule (d) has two
   trigger branches (`TABLE_MISSING`, and `TABLE_MALFORMED reason=header`), so it lands as two
   tagged statements with one row each (Sd-missing, Sd-header) instead of the design's one "rule
   (d) removed" member (`invariants.base.md` §"Test discrimination": each branch its own fixture).
   The 8 wire rows are the plan's wire-scoped reverts and force-fires scored through the harness:
   W1 revert, W1 force-fire, W2 revert, W2 force-fire, and for each of W3's two wires a revert and
   a force-fire (FF3a, FF3b; audit cycle 1). The design members I1 ("the agy name split inverted")
   and I2 ("the split applied to the Claude root") are behaviour mutants of the split, not
   force-fires of a `main` → `check` connection. 88 + 1 + 8 + 20 = 117.
4. **The AC-9.3 executable doc test seeds `docs/.bkit-memory.json` with `{}`** before it runs the
   `--create --claim` line. Measured at `7e155451` in a `tempfile.TemporaryDirectory` git
   repository, which was removed on exit:
   `h_mad_state_write.py docs/.bkit-memory.json --feature fx --create --claim abc` exits 2 with
   `ERROR: no such state file` when the file is absent, even when `docs/` exists. With the file
   holding `{}`, it prints `STATE-WRITE: OK feature=fx keys=0`, and `owner_session_id` reads
   `abc`. The design's D12 row does not state the seed.
5. **Adapter row text carries every D12 token.** Design §D9.3 cells are gists, and design §D12
   pins tokens some gists lack. Both sections are binding, so each row is written to carry both
   (Tasks 8–13 list the tokens per row). The known gaps are `Ctrl+T` in grok's `task-tools` row,
   `h_mad_check_memory_index.py` in grok's `claude-projects-store` row, and `uuid.uuid4()` plus
   `owned_elsewhere` in every `session-id-env` row.
6. **Two fixture shapes are chosen so that a disabled check fails its killing test by assertion,
   not by a crash or an equivalent mutant.** The non-list `skills` split uses a JSON object
   (`{"h-mad": true}`). A string value would re-trigger `bad_skill` through member validation, so
   the "detection disabled" mutant would be equivalent. `split_agy_root` attributes a line to the
   **first** matching `(name, kind)` pair, in `checkout_skill_names` order. A last-match loop lets
   the trailing-space mutant survive the `h-mad`/`h-mad-x` fixture. `PosixPath` sorting puts
   `h-mad` before `h-mad-x`, measured with `sorted([Path('r/h-mad-x/SKILL.md'),
   Path('r/h-mad/SKILL.md')])` at `7e155451`.
7. **Resolved by design v1.3: Task 0 runs at 5c.** Design Implementation Order step 1 now reads
   "**At 5c, before any production task** (orchestrator decision, design v1.3)": Task 0's commit
   is the first commit after the 5c impl-plan commit, and "No production task starts until Task
   0's calibration reading is committed" (design §"Implementation Order", step 1 and its erratum
   note). This plan follows it: Task 0's acceptance criteria require the probes and the reading to
   be committed, Task 1 depends on Task 0, and every production task (Tasks 2–14) depends on Task
   1 directly or transitively. The v1.1 conflict is closed; nothing here is open (audit cycle 1
   codex must 1; cycle 2 codex must 1, teammate should 4).
8. **Resolved by design v1.3: the install-check contract is design §D11 items 1–7.** Design v1.3
   §D11 §"The install-check contract" adopts the six `h-mad/SKILL.md` edits Task 14 made under
   this deviation in v1.1, in the same order, and adds item 7 (the remedy table's "all ten have
   one" count, which item 3's eleventh row moves). Task 14 applies items 1–7 and pins item 7 with
   `test_remedy_count_sentence_names_the_eleventh_row` (the node the design says the impl-plan
   owes). What remains a plan-level statement is only the premise: at `212aab9d`,
   `grep -rn 'all ten have one' h-mad handoff` → 1 matching line (`h-mad/SKILL.md:73`), and
   `h-mad/SKILL.md` line 84 still holds the `rm -rf ~/.claude/skills/<name>` remedy. **W2
   residual, left as the design leaves it:** design v1.3 §D11 "Residual, stated exactly" names two
   W2 surfaces that still describe only the old cause, `h-mad/SKILL.md`'s "Pass `--session-id` so
   the collision check runs; omitting it opts out" and `handoff/SKILL.md`'s bullet starting
   "**`cannot_judge`** → the state file exists and could not be READ", and says "Extending D11 to
   them is open for the orchestrator". This plan edits neither and adds no node for them, because
   an edit the design explicitly leaves open is the orchestrator's call, not the plan's (audit
   cycle 2, teammate should 5; reported, not decided).
9. **Guard rows: 20 mutation rows for guards that are green before their task's change or pass
   without a RED of their own** (audit cycle 2, codex must 3; `invariants.base.md` §"Test
   discrimination": a guard is enforced only once it has been seen to fail with its subject
   removed or permissively stubbed). Each row's mutant removes or loosens the guard's subject,
   and Task 15 scores it by the named test failing on its assertion:
   - Task 2 (7, `host_parity.json`): G1–G3 put a direct launcher into `host_parity.py`
     (`import subprocess`; `os.system`; `os.popen`) against
     `test_host_parity_has_no_direct_launcher_import`; G4 and G5 put a fence scanner into it
     (a `startswith("#")` function; a module-level `"~~~"` constant) against
     `test_host_parity_has_no_fence_scanner`; G6 makes `check()` launch `codex` against
     `test_gate_runs_no_host_cli`; G7 drops the non-empty-reason condition from
     `_missing_seed_ids` against `test_seed_check_honours_retirement[retired-empty-reason]`;
   - Task 4 (4, `host_declaration.json`): HE1–HE4 loosen `hermetic_env` (the `CLAUDE` prefix
     filter dropped; each of the three `_AMBIENT_HOST_KEYS` members dropped alone) against
     `test_hermetic_env_drops_claude_names_and_backend`, which passes at Task 4's RED;
   - Task 6 (3, `host_declaration.json`): AG-unset, AG-empty and AG-claude apply FF2's mutant
     against `test_budget_and_decide_agree[unset]`, `[empty]` and `[claude]`, the three ids that
     pass at Task 6's RED;
   - Task 14 (6, new spec `host_runtime_docs.json`): R1–R4 remove the codex or agy adapter link
     from one `## Host runtime` section each, against the four
     `test_host_runtime_names_every_adapter` ids that pass before Task 14's edit; L1 and L2 make
     `_section` return `""` instead of raising, against
     `test_host_runtime_locator_fails_loudly[renamed]` and `[doubled]`.

   Already covered, no new row: Task 7's `test_check_without_root_keywords_reads_no_new_root`
   (passes at RED) is FF3a's and FF3b's named test. Task 6's item 3 (`[grok]`) is V1's named test.
   **Residual, stated rather than rowed:** Task 6's three `…-unreadable-file` ids pass at RED and
   cannot be killed by any single-point mutant, because two independent paths both return
   `cannot_judge` for them after Task 6: the host check (first statement) and the existing
   `except (json.JSONDecodeError, OSError): return "cannot_judge"` branch
   (`h-mad/scripts/h_mad_resume_decision.py`, `decide`, read at `212aab9d`). WR2 and V2 leave the
   legacy branch; `resume_decision_cannot_judge.json`'s committed row on `        return
   "cannot_judge"` leaves the host check. They are matrix completeness, not claimed as a guard of
   either path.

## Preamble — where and how this plan runs

- **Where the readings were taken.** Every "read at `7e155451`" in this plan was run on the main
  checkout at that commit. `main` then advanced to `b8662267`, which adds only
  `codex-tdd-gate-defects` design-audit documents:
  `git diff --name-only 7e155451 b8662267 -- h-mad handoff docs/03-analysis/probes pytest.ini | wc -l`
  → 0 files. So every reading also holds at `b8662267`. All of them move at the 5c rebase, and
  Tasks 0 and 1 re-take the ones the tasks depend on.
- **Worktree, not the main checkout.** `~/.claude/skills/h-mad` is a symlink into
  `/Users/kimhawk/orca/skills/h-mad` (`ls -la ~/.claude/skills/h-mad` → `-> /Users/kimhawk/orca/skills/h-mad`,
  read at `7e155451`), so an edit on the main checkout changes the live skill mid-run. At 5c the
  branch `feature/multi-host-runtime` is created as a git worktree (`hmad-dispatch
  worktree-create` or `git worktree add`), after `codex-tdd-gate-defects` and then
  `grok-codex-fallback` have merged into `main` (plan merge order). At `7e155451` neither has
  merged: `git branch -a` lists `feature/216-grok-codex-fallback` only, checked out in
  `~/orca/skills-grok-codex-fallback`.
- **`BASE_SHA`.** It is the commit the branch forks from, which is the parent of the 5c commit.
  It is first derived in Task 0, as that task's first step and before any probe runs, as the
  parent of the sha that `h_mad_baseline_sha.py` prints. Shell variables do not survive between
  commands, so every task that uses `$BASE_SHA` runs this block first, in the same shell as the
  commands that use it:
  ```bash
  BL=$(/opt/anaconda3/bin/python h-mad/scripts/h_mad_baseline_sha.py --branch feature/multi-host-runtime | grep -m1 '^BASELINE:')
  case "$BL" in
    "BASELINE: OK sha="*) BASE_SHA=$(git rev-parse "$(printf '%s\n' "$BL" | sed -E 's/^BASELINE: OK sha=([0-9a-f]{40}).*/\1/')^") ;;
    *) BASE_SHA=""; echo "HALT: BASELINE not OK: $BL" ;;
  esac
  ```
  Read the `BASELINE:` token; only `OK` carries `sha=`. An empty `BASE_SHA` or a printed
  `HALT: BASELINE not OK` stops the task. Task 0 writes the value into the Phase-6 document's
  §"Baseline at BASE_SHA"; every later derivation must equal that recorded value, or the task
  halts to the operator. Every "at `BASE_SHA`" in this plan means that commit. The 5c commit (the
  impl-plan and its audits) must be the branch's first commit, which is what
  `h_mad_baseline_sha.py` verifies. Task 0's probe commit therefore follows it.
- **Codex authors every non-test `.py`, including the probes.** `h-mad/hooks/h-mad-tdd-gate.sh`
  blocks a Claude write to any non-test `.py` while any feature's phase is `step5`, and 5a sets
  `phase = "step5"` (`h-mad/SKILL.md` §5a). For every `h-mad/scripts/*.py` path,
  `h_mad_derive_test_path.sh` derives no test path (it prints nothing for each of the four
  scripts this plan edits and for the probe paths, read at `7e155451`), so the gate's fallback
  branch would block a Claude-authored write with "cannot derive test path". Codex therefore
  authors 5d/5e, and also the three probe tasks that write a `.py`: Task 0 (`seed_coverage.py`),
  Task 16 (`byte_identity.py`) and Task 17 (`smoke_assert.py`). If codex is out, halt to the
  operator; never bypass the gate.
- **Interpreter.** Every command this plan tells an implementer to run uses
  `/opt/anaconda3/bin/python` (or `python3.11`, which resolves to it). On this host bare `python3`
  is `/opt/homebrew/bin/python3` and has no pytest. The only `python3` spellings left are text
  written into adapters and `SKILL.md` (design §D9 and §D12 pin them) and the argv inside
  rehearsal fixtures.
- **No test in this plan runs `codex`, `agy` or `grok`.** The live smoke is Phase 7 (plan), after
  7f and before 7e. It is described under §"After Phase 5" and is not a task.
- **The operator's four install links** (`~/.agents/skills/{h-mad,handoff}`,
  `~/.gemini/config/skills/{h-mad,handoff}`) do not exist on this machine: `ls -ld` on each →
  "No such file or directory", 4 of 4, read at `7e155451`. This feature creates none. Every step
  that needs them (Task 1's link gate, Phase 6's byte-identity arm B, the Phase-7 smoke) halts to
  the operator while they are absent, and never passes.

### Conventions every task follows

1. **Both coupled suites, per task.** Every task's GREEN verification runs, from the worktree
   root, `env -u HMAD_HOST /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests
   handoff/tests handoff/scripts` in full, and then runs the task's own test file a second time
   with `CLAUDE_ZZZ_PROBE=1` exported. That second run must report the same `passed` count. The
   only failures a task may leave are the nodes in the carried-RED ledger below for that task,
   plus
   `h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`,
   and only if Task 1 recorded it failing at `BASE_SHA` for the same reason. That node is not
   waived at Task 18 (plan Success Criteria).
2. **Carried-RED ledger.** The live parity nodes are written in Task 2 and go GREEN in the tasks
   that satisfy them (plan: "RED/GREEN per adapter is per test node").
   `P = h-mad/tests/test_host_construct_parity.py`.

   | After task | Carried-RED nodes (all in `P`) | Count |
   |---|---|---|
   | 2 | `test_live_registry_and_skill_files_are_clean`; `test_live_adapter_is_clean` × 6; `test_registry_holds_every_seed_id`; `test_registry_branch_samples` × 22 (one per `BRANCH_SAMPLES` key; 22 at the seed) | 30 |
   | 3, 4, 5, 6, 7 | `test_live_adapter_is_clean[h-mad-codex|h-mad-agy|h-mad-grok|handoff-codex|handoff-agy|handoff-grok]` | 6 |
   | 8 | the five ids except `h-mad-codex` | 5 |
   | 9 | `h-mad-grok`, `handoff-codex`, `handoff-agy`, `handoff-grok` | 4 |
   | 10 | `handoff-codex`, `handoff-agy`, `handoff-grok` | 3 |
   | 11 | `handoff-agy`, `handoff-grok` | 2 |
   | 12 | `handoff-grok` | 1 |
   | 13 onward | none | 0 |
3. **Hermetic subprocess environment.** Every test that starts a subprocess passes
   `env=hermetic_env(...)` (Deviation 1), or an explicit minimal dict it builds itself (Task 2's
   stub control, `{"PATH": <stub dir>}`). `hermetic_env` copies `os.environ`, so the Task 7
   autouse root overrides are kept. It drops every key starting `CLAUDE` and the keys
   `HPW_AGENT_BACKEND`, `HMAD_HOST` and `HMAD_CONTEXT_WINDOW`, then applies the keyword extras.
   Every `subprocess.run` in a test carries `timeout=60.0`.
4. **No identity assertion between compiled patterns.** No test asserts `is` between two
   `re.compile` results, because the `re` cache makes separately compiled identical patterns the
   same object. No test pins "compiled once". A test that needs a fresh module constant uses
   `re.purge()` and then `importlib.reload`, or a source check.
5. **Parametrize ids are part of the contract.** Every id is named below and written with
   `pytest.param(..., id="...")` or `ids=[...]`. Mutation `test` keys, WIRE-PINs and ACs use full
   node ids (`tests/test_x.py::test_y[id]` in specs, relative to `h-mad/`).
6. **Committed anchors.** After every task that edits a file some committed mutation spec
   anchors, both of
   `env -u HMAD_HOST /opt/anaconda3/bin/python h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json`
   and `env -u HMAD_HOST /opt/anaconda3/bin/python h-mad/scripts/h_mad_mutation_harness.py --check-anchors handoff/tests/mutation-specs/*.json`
   must print `ANCHORS_OK` with `drifted=0`. Read the `ANCHORS:` token, never `$?`. The anchored
   files this plan edits are the three scripts and both `SKILL.md` files. `h-mad/tests/conftest.py`
   is not anchored by any committed spec at the base (the `"file"` values of both spec directories
   name no conftest: 0 matching lines at `a85abf7f`); from Task 15 on it is anchored by this
   feature's own HE rows, and no later task edits it. It is swept anyway because the sweep is
   directory-wide.
7. **Mutation spec form.** `root` is `"../.."` (the `h-mad/` directory); `file` is
   `scripts/…` or `tests/…`; `test` is `tests/<file>.py::<name>[<id>]`; `command` and
   `target_command` start with `python3.11` (`which python3.11` → `/opt/anaconda3/bin/python3.11`,
   Python 3.11.8, read at `7e155451`). Every row carries `name`, `file`, `find`, `replace` and
   `test`. The score is the `MUTATION:` token, never `$?`.
8. **Probes are deleted.** A scratch probe written to confirm a suspected defect is deleted after it
   answers. The committed sidecar under `docs/03-analysis/probes/multi-host-runtime/` is a
   deliverable, not scratch.
9. **No bare time-limit command** in `h-mad/scripts/*.py`, `h-mad/references/*.md`,
   `h-mad/scripts/*.sh` or `h-mad/hooks/*.sh`. `test_h_mad_portable_timeout.py` scans those four
   globs with `(?:^|[^-\w])timeout\s+\d+`. Adapter prose writes "a 5 s handler limit", never the
   word `timeout` followed by a number.

---

## Task 0: probe-sidecar-calibration

**Production file**: `docs/03-analysis/probes/multi-host-runtime/calibrate.sh` (new, executable),
`docs/03-analysis/probes/multi-host-runtime/seed.json` (new),
`docs/03-analysis/probes/multi-host-runtime/seed_coverage.py` (new). None of these is under
`h-mad/`, and no test reads them.
**Test file**: none. The probes are measurement instruments, and their controls below are run,
not asserted.
**Task shape**: `gate` (authors the committed calibration probes and records their reading; writes no h-mad file)

**Description**: Design §D8 rows 1–3 and Implementation Order step 1, landed in the 5c commit
sequence directly after the 5c impl-plan commit and before any RED (orchestrator decision). The
probe directory is absent at `7e155451` (`ls docs/03-analysis/probes/multi-host-runtime` → "No
such file or directory").

- **`calibrate.sh SHA`** runs the spec FR-4 command verbatim at `SHA`. It resolves the repository
  with `git -C "$(dirname "$0")" rev-parse --show-toplevel`, so it works from any cwd and from a
  worktree. It refuses a sha that `git rev-parse --verify -q "$SHA^{commit}"` does not resolve,
  printing `CALIBRATE: UNREADABLE reason=bad_sha` and exiting 2. For each of `h-mad/SKILL.md` and
  `handoff/SKILL.md` it prints a header line (`== h-mad/SKILL.md`), then the `sort | uniq -c`
  lines, then a total line (`TOTAL h-mad/SKILL.md occurrences=122 distinct=13` is the form). It
  ends with `CALIBRATE: OK sha=` followed by the full
  sha, and exits 0. It writes no file. It uses no `set -e`: every pass condition is an explicit
  `||`.
- **`seed.json`** is `{"$comment": "...", "constructs": [...]}`. It holds the 22 spec-seed entries
  in design §D1's format and seed-table order: `H` expanded, `\|` un-escaped, `both` written as
  `["h-mad", "handoff"]`, and a one-sentence `description`. The `$comment` says it is a frozen copy
  of the spec seed at `6494b3c`, that it measures `BASE_SHA` before the registry exists, and that
  no test reads it.
- **`seed_coverage.py --sha SHA --registry PATH [--branches]`**:
  - Per-entry mode reads both `SKILL.md` files through `git show` at the given sha and counts
    occurrences with `re.finditer`. It prints one line per entry, in the form
    `ENTRY id=claude-md h-mad=2 handoff=1 declared=h-mad,handoff verdict=ok`. A **finding** is
    `stale:` plus a skill name (0 hits in a declared skill) or `undeclared:` plus a skill name
    (≥ 1 hit in an undeclared skill). One entry can carry a finding per skill, so the verdict is
    `ok` when the entry has none, and otherwise every finding of the entry, comma-joined, in skill
    order `h-mad` then `handoff` (for example `verdict=undeclared:h-mad,stale:handoff`). It ends
    with `SEEDCOV: PASS entries=N stale=0 undeclared=0` or
    `SEEDCOV: FAIL entries=N stale=N undeclared=N`, exit 0. `entries` counts entries; `stale` and
    `undeclared` count findings, not entries.
  - `--branches` imports `expand_branches` from `h-mad/tests/host_parity.py`, reached by putting
    the repository's `h-mad/tests` directory on `sys.path`. It prints one line per branch ×
    declared skill, in the form
    `CELL id=claude-settings branch="..." skill=h-mad hits=N` (the branch JSON-encoded), then one
    `ZERO` line per zero cell in the same form, then
    `SEEDCOV-BRANCHES: entries=N branches=N cells=N zero=N dead=N`. `dead` counts the branches
    with 0 hits in every declared skill.
  - When `host_parity` cannot be imported, it prints `SEEDCOV: UNREADABLE reason=no_expander` and
    exits 2. An unreadable registry prints `SEEDCOV: UNREADABLE reason=bad_registry`, and an
    unresolvable sha prints `SEEDCOV: UNREADABLE reason=bad_sha`; both exit 2.
  - It is stdlib only.

**Author**: codex (§Preamble), because `seed_coverage.py` is a non-test `.py`.

**Probe-run step** (the reading is written to `docs/03-analysis/multi-host-runtime.analysis.md`,
§"Baseline at BASE_SHA", which this task creates). All three items run in one shell:
0. **Derive `BASE_SHA`** with the §Preamble block. A `HALT: BASELINE not OK` line or an empty
   `BASE_SHA` stops the task before item 1. Record the value first in §"Baseline at BASE_SHA".
1. `bash docs/03-analysis/probes/multi-host-runtime/calibrate.sh "$BASE_SHA"` → record every
   line. This is AC-4.5's reading.
2. `/opt/anaconda3/bin/python docs/03-analysis/probes/multi-host-runtime/seed_coverage.py --sha "$BASE_SHA" --registry docs/03-analysis/probes/multi-host-runtime/seed.json`
   → record every line.

**Controls, each executed in this task** (expected values were read at `7e155451`, where
`git diff --stat 6494b3c 7e155451 -- h-mad/SKILL.md handoff/SKILL.md` prints nothing):
- C0.1: `calibrate.sh 7e155451` → `TOTAL h-mad/SKILL.md occurrences=122 distinct=13` and
  `TOTAL handoff/SKILL.md occurrences=71 distinct=12`. This reading was reproduced at
  `7e155451` with the spec command piped to `wc -l` and to `sort -u | wc -l`.
- C0.2: `seed_coverage.py --sha 7e155451 --registry …/seed.json` →
  `SEEDCOV: PASS entries=22 stale=0 undeclared=0`. It was reproduced at `7e155451` by an in-memory
  `re.finditer` pass over the 22 patterns: 0 contradictions, 17 entries declaring `h-mad` and 12
  declaring `handoff`.
- C0.3: `seed_coverage.py --sha 7e155451 --registry …/seed.json --branches` →
  `SEEDCOV: UNREADABLE reason=no_expander`, because `host_parity.py` does not exist yet. This
  control shows that branch mode refuses rather than guessing.
- C0.4 (negative): a scratch copy of `seed.json` with `advisor`'s `skills` set to `["handoff"]`,
  written in the session scratchpad and deleted after the run → the line
  `ENTRY id=advisor h-mad=18 handoff=0 declared=handoff verdict=undeclared:h-mad,stale:handoff`
  and `SEEDCOV: FAIL entries=22 stale=1 undeclared=1`. The two hit counts were read at
  `7e155451` with `re.findall(r'\badvisor\(\)', …)` over `git show 7e155451:<skill>/SKILL.md`:
  18 occurrences in `h-mad`, 0 in `handoff`. One entry carries both findings, which is the case
  the per-entry verdict list exists for.
- C0.5: `calibrate.sh deadbeef` → `CALIBRATE: UNREADABLE reason=bad_sha`, exit 2.

The `BASE_SHA` readings move with either `SKILL.md`, because both siblings edit `h-mad/SKILL.md`.
They are recorded, never compared with the `7e155451` controls.

**Acceptance Criteria**:
- [ ] AC-4.5 (reading half): the calibration command and its reading at `BASE_SHA` are in the
  Phase-6 document's §"Baseline at BASE_SHA".
- [ ] C0.1–C0.5 print exactly the tokens above.
- [ ] `BASE_SHA` was derived by item 0 before item 1 ran, and its value is recorded.
- [ ] The three probe files and the Phase-6 document holding this reading are committed in one
  commit, the first after the 5c impl-plan commit, before Task 1 starts (design v1.3
  Implementation Order step 1: "No production task starts until Task 0's calibration reading is
  committed").

**Mutation rows**: none. **Dependencies on other tasks**: None. It runs right after the 5c
impl-plan commit.

---

## Task 1: baseline-at-base

**Production file**: none. The readings go into `docs/03-analysis/multi-host-runtime.analysis.md`.
**Test file**: none
**Task shape**: `gate`

**Description**: The rest of design Implementation Order step 2 and plan §"Rebase, then
baseline". Each item records its command and reading, stamped with `BASE_SHA`; every item that
uses `$BASE_SHA` runs in the same shell as item 1's derivation, or repeats it:
1. **Re-derive `BASE_SHA`** with the §Preamble block and compare it with the value Task 0
   recorded. A difference halts to the operator.
2. **Four-link gate.** Run the plan's loop verbatim. Its first `HALT` line stops 5c and goes to
   the operator. The loop is `for p in ~/.agents/skills ~/.gemini/config/skills; do for k in h-mad
   handoff; do test -L …; test "$(readlink -f …)" = "/Users/kimhawk/orca/skills/$k"; done; done`.
   At `7e155451` all four links are absent, so this step halts until the operator creates them.
   This feature never creates a link, and never records the gate as passed without the four
   `test -L` successes.
3. **P4, P5, P6, P9, P15**: re-run with the plan's commands (plan §"Verified premises") at
   `BASE_SHA`.
4. **`REFUSAL_FORM_AT_BASE`**, from P5 and the sibling's recorded FR-0 branch. Read every refusal
   site of `h-mad/hooks/h-mad-tdd-gate.sh` at `BASE_SHA` and record exactly one of:
   - `exit1`: every refusal ends `exit 1`;
   - `a`: every refusal is rc 2 (`exit 2`) with the reason on stderr;
   - `b`: every refusal is rc 0 with stdout
     `hookSpecificOutput.permissionDecision == "deny"`.

   A mix of forms, or anything else, halts to the operator before Task 10 (design §D9.2). At
   `7e155451`, `grep -c 'exit 1' h-mad/hooks/h-mad-tdd-gate.sh` → 5 matching lines, and the
   sibling feature has not merged, so the reading at `BASE_SHA` is expected to differ.
5. **Suite baseline**: keep the whole output, never a tail of it, in the untracked git directory:
   `GD="$(git rev-parse --absolute-git-dir)"; env -u HMAD_HOST /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts > "$GD/hmad-mhr-base-suite.txt" 2>&1; tail -1 "$GD/hmad-mhr-base-suite.txt"; grep -E '^(FAILED|ERROR) ' "$GD/hmad-mhr-base-suite.txt"`.
   Record the summary line and every `FAILED`/`ERROR` line of pytest's short test summary (the
   default `-r fE` lists each failing node id with its reason, one per line), and check that the
   number of those lines equals the summary's `failed` plus `error` counts; a mismatch halts to
   the operator (audit cycle 2, codex should 2).
6. **Node-id list for the floor**:
   `/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts 2>&1 | grep '::' | sort > "$(git rev-parse --absolute-git-dir)/hmad-mhr-base-nodeids.txt"`.
   The file sits inside the git directory, so it is untracked and survives until Task 18.
7. **Anchors**: both `--check-anchors` commands (Convention 6) → `ANCHORS_OK drifted=0`. DP3's
   reading at `1ef1a782` was `specs=99 mutations=907` and `specs=7 mutations=69`; this count moves
   with any spec either sibling adds.
8. **AC-6.1 gap table**: for each registry entry × each of the four existing adapters, record
   `addressed` or `absent` by reading `git show "$BASE_SHA":<adapter>`, with the sha stated.
9. **AC-4.6 record**: compare Task 0's calibration at `BASE_SHA` with the spec's 25 distinct
   tokens (13 in `h-mad/SKILL.md`, 12 in `handoff/SKILL.md`). Record:
   - every new distinct token, classified as a Claude construct or a false hit;
   - every entry whose per-entry verdict is not `ok`;
   - the resulting registry changes, each of one of four kinds: **add** a new entry; **retire**
     an entry, with its reason; **amend `skills`** of an existing entry (the fix for a per-skill
     `stale:` or `undeclared:` finding on an entry that stays, for example `claude-settings`
     going stale in `handoff`); **amend `pattern`** of an existing entry. A false hit is never
     registered, and an existing id is never re-added as a new entry.

   Task 3 builds the registry from `seed.json` plus exactly this record. **A false hit halts.**
   Spec AC-4.6 fixes a false hit by "narrowing an axis or its exclusion, which is recorded with a
   new control". Design §D2 gives no narrowing mechanism: `CATCH_ALL_AXES`, `A4_BRANCHES` and
   `EXCLUSION_SUFFIXES` are fixed constants, and each dict entry of the first two and each suffix
   of the third is its own Task 15 mutation row (S5; `EXCLUSION_SUFFIXES` is one tagged line
   carrying six X rows). A new suffix or a narrowed axis changes the design's member count and
   needs its own killing fixture. So when this record classifies any token as a false hit, Task 1
   ends with `HALT: AC-4.6 false hit — design delta owed`, naming the token, and **no later task
   starts: Task 2 onward waits**, because Task 2 writes the three constants the revision would
   change. The orchestrator routes the narrowing to a design revision, which names the changed
   constant, its discriminating control and its mutation row. This plan does not invent that
   mechanism (audit cycle 2, teammate should 1).

**Acceptance Criteria**:
- [ ] AC-4.6: the record (item 9) is in the Phase-6 document before Task 3 starts.
- [ ] AC-6.1: the gap table (item 8) with its sha is in the Phase-6 document.
- [ ] `REFUSAL_FORM_AT_BASE` is recorded as one of `exit1`, `a` or `b`.
- [ ] The four-link gate printed no `HALT`.
- [ ] The AC-4.6 record classifies no token as a false hit.
- [ ] The suite-baseline `FAILED`/`ERROR` line count equals the summary's `failed` + `error`.

A halt on any of these is not a met criterion: it stops 5c, and no later task starts until the
operator or the orchestrator clears it and the item is re-run.

**Mutation rows**: none. **Dependencies on other tasks**: Task 0

---

## Task 2: host-parity-checker

**Production file**: `h-mad/tests/host_parity.py` (new; not collected, because `pytest.ini` holds
only `testpaths = h-mad/tests handoff/tests handoff/scripts`, read at `7e155451`)
**Test file**: `h-mad/tests/test_host_construct_parity.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §D2 in full: the registry, `SKILL.md` and adapter stages, catch-all,
suppression rules (a)–(e), the adapter-table reader and the branch expander. The module imports
`json`, `re`, `sys`, `dataclasses`, `pathlib`, `typing` and `h_mad_doc_block_exec`, the last through
`sys.path.insert(0, <h-mad>/scripts)` as `h-mad/tests/docsections.py` does. It imports no
`subprocess` and calls no `os.system` or `os.popen`. The fence helpers were verified at
`7e155451`:
- `find_heading(text: str, heading: str) -> tuple[int, int] | None`, which raises
  `AmbiguousHeading`;
- `fence_aware_end(text: str, start: int, level: int) -> int`;
- `_fence_events(text: str) -> Iterator[_FenceEvent]`, where `_FenceEvent` carries `lineno`,
  `kind`, `start`, `end`, `level` and `text`. `text` is filled only for `heading` events, where it
  holds the title; every `body` and `prose` event keeps the default `text=""`
  (`h-mad/scripts/h_mad_doc_block_exec.py`, `_fence_events`, read at `a85abf7f`). A line's text is
  therefore always `text[event.start:event.end].rstrip("\r\n")`, never `event.text`, both in
  `adapter_table`'s "begins with `|`" test and in Task 8's `_fenced_lines`.

**Code structure** (design §D2.1, verbatim contracts):
```python
@dataclass(frozen=True)
class ParityPaths:
    root: Path
    registry: Path
    skills: Mapping[str, Path]
    adapters: Mapping[Path, str]

@dataclass(frozen=True)
class Failure:
    kind: str; file: str; id: str = "-"; reason: str | None = None; token: str | None = None
    def line(self) -> str: ...

class UnsupportedPattern(ValueError): ...
REQUIRED_KEYS = ("id", "pattern", "skills", "description")
def live_paths(root: Path) -> ParityPaths: ...
CATCH_ALL_AXES: Mapping[str, str]
A4_BRANCHES: Mapping[str, str]
EXCLUSION_SUFFIXES: tuple[str, ...]
def a4_pattern(branches: Iterable[str]) -> str: ...
def expand_branches(pattern: str) -> list[str]: ...

@dataclass(frozen=True)
class Row:
    id: str; status: str; mapping: str; source: str

@dataclass(frozen=True)
class Table:
    rows: list[Row]
    problems: list[tuple[str, str, str]]

def adapter_table(text: str) -> Table: ...

@dataclass(frozen=True)
class ParityResult:
    failures: list[Failure]
    stages: tuple[str, ...]

def check(paths: ParityPaths, *, axes: Mapping[str, str] = CATCH_ALL_AXES,
          exclusion_suffixes: Sequence[str] = EXCLUSION_SUFFIXES) -> ParityResult: ...
```

**Landed structure** (Task 15's rows anchor on it; each rule is checkable with `grep -c` on the
landed file):
- **S1.** Every emission of a `(kind, reason)` pair is one statement on its own line:
  `failures.append(...)`, or, inside `adapter_table` (which returns `Table.problems` for `check()`
  to convert), `problems.append(...)`. The table-kind emissions D21–D25 and D42 are the
  `problems.append(...)` ones. The control-flow statement after an emission (`return`, `continue`
  or a skip flag) is on a separate line. Each emission line ends with a tag comment naming the design
  disjunct it emits: `# M:D01` … `# M:D42` in the order of the fixture table below. Two families
  share one line: `# M:D07-D10` (the `missing_key` emission inside `for key in REQUIRED_KEYS:`,
  whose reason is `f"missing_key:{key}"`) and `# M:D31-D36` (the `CELL_EMPTY` emission, whose
  reason is `f"{cell_name}:{kind}"`, with the loop variables named `cell_name` and `kind`). Every other
  disjunct has its own emission line, including the non-`str` splits, which are checked before
  the value checks they guard.
- **S2.** Field reads in the registry stage use `element.get(key)`.
- **S3.** The ids of `BAD_PATTERN` entries go into a set by a statement separate from the emission.
  Later stages skip entries through that set, so disabling an emission never lets
  `re.compile` see a non-`str` pattern.
- **S4.** Suppression rules (a), (b), (c) and (e) are each one statement, tagged `# M:Sa`,
  `# M:Sb`, `# M:Sc` and `# M:Se`. Rule (d) has two trigger branches in plan v1.3 ("An adapter
  with `TABLE_MISSING`, or with `TABLE_MALFORMED reason=header`, yields no `ROW_*`,
  `STATUS_INVALID` or `CELL_EMPTY` line"; design §D2.4 names only the header branch), so it is two
  statements, `# M:Sd-missing` (the adapter has a `TABLE_MISSING` problem) and `# M:Sd-header`
  (it has `TABLE_MALFORMED reason=header`). A `TABLE_MISSING` adapter has no rows, so what
  Sd-missing suppresses is one `ROW_MISSING` per registry id declared for the adapter's skill.
  Each tagged statement is either an `if` whose condition switches the rule on, or a single
  side-effect statement (for (e), recording the cell-count row's id as present). Rule (b) has two
  halves: Sb is the `UNREGISTERED` skip; the `STALE_ENTRY`/`UNDECLARED_SKILL` skip is S3's
  set-skip, which is not tagged. Residual, stated rather than rowed: disabling that set-skip makes
  `re.compile` see `"("` in fixture (b), which is a crash kill and never an assertion kill, so it
  gets no row (Task 15's pass condition requires `crash_kills=0`).
- **S5.** `CATCH_ALL_AXES` and `A4_BRANCHES` are dict literals with one entry per line, tagged
  `# M:A1` … `# M:A4` and `# M:B1` (`tilde`), `# M:B2` (`home`), `# M:B3` (`home_braced`).
  `CATCH_ALL_AXES["A4"]` is `a4_pattern(A4_BRANCHES.values())`. `EXCLUSION_SUFFIXES` is a
  one-line tuple tagged `# M:X`.
- **S6.** The empty alternative for an optional group is appended by one line tagged `# M:E1`. The
  table-line selection uses the comparison `event.kind == "prose"` on one line tagged `# M:F1`.
  The `tbd`/`todo` test is one line tagged `# M:C1` holding `.lower()`. The `BAD_PATTERN` step
  iterates only elements whose field checks ran, on one line tagged `# M:P1`. The cell-count
  branch reads its id through `_cell_id(cells[0])` on one line tagged `# M:K1`.
- **S7.** Each tag occurs exactly once in the file. (`# M:X` is simply the tag of the one tuple
  line; it is not an exception.)
- **S8** (guard rows G1–G6 anchor here). Imports are one module per line, and the line
  `import json` occurs exactly once in `host_parity.py`. `check()`'s signature is the two lines of
  the code structure above, so its second line,
  `          exclusion_suffixes: Sequence[str] = EXCLUSION_SUFFIXES) -> ParityResult:`, occurs
  exactly once.
- **S9** (guard row G7 anchors in the test module). `_missing_seed_ids`' body is the one line
  `    return [i for i in seed_ids if i not in registry_ids and not retired.get(i)]`, which occurs
  exactly once in `test_host_construct_parity.py`.

**Clean baseline** (one builder, `_baseline(tmp_path) -> ParityPaths`, shared by every fixture):
- registry: `advisor` (pattern `\badvisor\(\)`, skills `["h-mad"]`) and `claude-md` (pattern
  `\bCLAUDE\.md\b`, skills `["h-mad", "handoff"]`), each with a one-sentence description;
- `h-mad/SKILL.md`: `# h`, a blank line, then `Call advisor() before CLAUDE.md is read.`;
- `handoff/SKILL.md`: `# f`, a blank line, then `Read CLAUDE.md first.`;
- six adapters under `tmp_path/{h-mad,handoff}/references/{codex,agy,grok}-runtime.md`, each
  holding `# A`, then `## Construct mapping`, then a table with the header
  `| construct | status | mapping | source |` and the delimiter `|---|---|---|---|`. The h-mad
  adapters carry the rows `` | `advisor` | not-applicable | no advisor tool on this host | observed: fixture | ``
  and `` | `claude-md` | mapped | the host project rules file | observed: fixture | ``. The handoff
  adapters carry the `claude-md` row only.

The baseline's only catch-all hits are A3's `CLAUDE` in `CLAUDE.md`, which the `claude-md`
pattern covers. It yields `[]`.

**The 42 kind fixtures.** Each is one edit to the baseline and yields exactly its pair. "h-mad
codex" means that adapter's table.

| Row | id | edit | pair |
|---|---|---|---|
| D01 | `ru-missing-file` | registry file deleted | `REGISTRY_UNREADABLE`, `missing_file` |
| D02 | `ru-invalid-json` | registry text `{"constructs": [` | `REGISTRY_UNREADABLE`, `invalid_json` |
| D03 | `ru-not-object` | registry text `[]` | `REGISTRY_UNREADABLE`, `not_object` |
| D04 | `ru-no-constructs` | registry `{"entries": []}` | `REGISTRY_UNREADABLE`, `no_constructs` |
| D05 | `ru-constructs-not-array` | registry `{"constructs": {}}` | `REGISTRY_UNREADABLE`, `constructs_not_array` |
| D06 | `ru-element-not-object` | the `claude-md` element replaced by the string `"claude-md"` | `REGISTRY_UNREADABLE`, `element_not_object` |
| D07 | `ru-missing-key-id` | `id` deleted from `advisor` | `REGISTRY_UNREADABLE`, `missing_key:id` |
| D08 | `ru-missing-key-pattern` | `pattern` deleted from `advisor` | `REGISTRY_UNREADABLE`, `missing_key:pattern` |
| D09 | `ru-missing-key-skills` | `skills` deleted from `advisor` | `REGISTRY_UNREADABLE`, `missing_key:skills` |
| D10 | `ru-missing-key-description` | `description` deleted from `advisor` | `REGISTRY_UNREADABLE`, `missing_key:description` |
| D11 | `ru-extra-key` | `"notes": "x"` added to `advisor` | `REGISTRY_UNREADABLE`, `extra_key:notes` |
| D12 | `ru-bad-id` | `advisor`'s id → `"Advisor"` | `REGISTRY_UNREADABLE`, `bad_id` |
| D13 | `ru-empty-description` | `advisor`'s description → `""` | `REGISTRY_UNREADABLE`, `empty_description` |
| D14 | `ru-empty-skills` | `advisor`'s skills → `[]` | `REGISTRY_UNREADABLE`, `empty_skills` |
| D15 | `ru-bad-skill` | `advisor`'s skills → `["h-mad", "grok"]` | `REGISTRY_UNREADABLE`, `bad_skill` |
| D16 | `duplicate-id` | a third element, an exact copy of `claude-md` | `DUPLICATE_ID`, none |
| D17 | `bad-pattern` | `advisor`'s pattern → `"("` | `BAD_PATTERN`, none |
| D18 | `stale-entry` | `advisor()` removed from h-mad `SKILL.md` | `STALE_ENTRY`, none |
| D19 | `undeclared-skill` | `Call advisor().` appended to handoff `SKILL.md` | `UNDECLARED_SKILL`, none |
| D20 | `unregistered` | ``Use `FooBar`.`` appended to h-mad `SKILL.md` | `UNREGISTERED`, none (token `` `FooBar` ``) |
| D21 | `tm-no-heading` | h-mad codex heading → `## Constructs` | `TABLE_MISSING`, `no_heading` |
| D22 | `tm-no-table` | h-mad codex table lines removed; heading kept, one prose line under it | `TABLE_MISSING`, `no_table` |
| D23 | `tm-heading-twice` | a second `## Construct mapping` heading and a prose line appended to h-mad codex | `TABLE_MISSING`, `heading_twice` |
| D24 | `tmal-header` | h-mad codex header cell `status` → `state` | `TABLE_MALFORMED`, `header` |
| D25 | `tmal-cell-count` | h-mad codex `advisor` row → `` | `advisor` | not-applicable | no advisor tool | `` (3 cells, id backticked) | `TABLE_MALFORMED`, `cell_count` |
| D26 | `row-missing` | h-mad codex `advisor` row deleted; the prose line `advisor here, advisor again, advisor a third time.` added (AC-3.2) | `ROW_MISSING`, none |
| D27 | `row-unknown-id` | row `` | `zeta-thing` | mapped | a map | observed: fixture | `` added to h-mad codex | `ROW_UNKNOWN_ID`, none |
| D28 | `row-wrong-skill` | the h-mad `advisor` row added to handoff codex | `ROW_WRONG_SKILL`, none |
| D29 | `row-duplicate` | h-mad codex `claude-md` row duplicated | `ROW_DUPLICATE`, none |
| D30 | `status-invalid` | h-mad codex `advisor` status → `maybe` | `STATUS_INVALID`, none |
| D31 | `ce-mapping-no-alnum` | h-mad codex `advisor` mapping → `—` | `CELL_EMPTY`, `mapping:no_alnum` |
| D32 | `ce-mapping-tbd` | same mapping → `TbD` | `CELL_EMPTY`, `mapping:tbd` |
| D33 | `ce-mapping-todo` | same mapping → `ToDo` | `CELL_EMPTY`, `mapping:todo` |
| D34 | `ce-source-no-alnum` | h-mad codex `advisor` source → `—` | `CELL_EMPTY`, `source:no_alnum` |
| D35 | `ce-source-tbd` | same source → `TbD` | `CELL_EMPTY`, `source:tbd` |
| D36 | `ce-source-todo` | same source → `ToDo` | `CELL_EMPTY`, `source:todo` |
| D37 | `split-bad-pattern-non-str` | `advisor`'s pattern → `5` | `BAD_PATTERN`, none |
| D38 | `split-bad-id-non-str` | `advisor`'s id → `7` | `REGISTRY_UNREADABLE`, `bad_id` |
| D39 | `split-bad-skill-non-list` | `advisor`'s skills → `{"h-mad": true}` | `REGISTRY_UNREADABLE`, `bad_skill` |
| D40 | `split-bad-skill-duplicate-name` | `advisor`'s skills → `["h-mad", "h-mad"]` | `REGISTRY_UNREADABLE`, `bad_skill` |
| D41 | `split-empty-description-non-str` | `advisor`'s description → `7` | `REGISTRY_UNREADABLE`, `empty_description` |
| D42 | `split-header-bad-delimiter` | h-mad codex delimiter row → `|---|---|x|---|` | `TABLE_MALFORMED`, `header` |

Counts, by kind: `REGISTRY_UNREADABLE` D01–D15 = 15; `TABLE_MISSING` D21–D23 = 3;
`TABLE_MALFORMED` D24–D25 = 2; `CELL_EMPTY` D31–D36 = 6; one each for `DUPLICATE_ID`,
`BAD_PATTERN`, `STALE_ENTRY`, `UNDECLARED_SKILL`, `UNREGISTERED`, `ROW_MISSING`,
`ROW_UNKNOWN_ID`, `ROW_WRONG_SKILL`, `ROW_DUPLICATE` and `STATUS_INVALID` = 10. That is 36
disjunct fixtures. The splits are D37–D42 = 6. 36 + 6 = 42.

**Suppression fixtures.** Each yields two pairs without its rule and exactly one with it:
- (a): D11's edit plus D21's edit → `{(REGISTRY_UNREADABLE, extra_key:notes)}`;
- (b): D17's edit plus D20's edit → `{(BAD_PATTERN, None)}`;
- (c): D16's edit, plus the `claude-md` row deleted from handoff codex →
  `{(DUPLICATE_ID, None)}`;
- (d): D24's edit, plus h-mad codex `advisor` status `maybe` → `{(TABLE_MALFORMED, header)}`.
  This is the header branch (Sd-header). The `TABLE_MISSING` branch (Sd-missing) has its own
  fixture, D21 (`tm-no-heading`): without the rule it yields `TABLE_MISSING` plus a
  `ROW_MISSING` for each of `advisor` and `claude-md`, so its exactly-one-pair assertion fails;
- (e): h-mad codex `advisor` row with five cells → `{(TABLE_MALFORMED, cell_count)}`.

**Catch-all fixtures** (spec AC-4.2 and AC-4.3). The fixture tokens are A1 `Foobar(`, A2
`` `FooBar` ``, A3 `CLAUDE_FOO`, A4-tilde `~/.claude/foo`, A4-home `$HOME/.claude/foo`,
A4-home-braced `${HOME}/.claude/foo`, and the six suffixes `` `FooError` ``,
`` `FooException` ``, `` `FooWarning` ``, `` `FooExpired` ``, `` `FooExit` `` and
`` `FooInterrupt` ``. Each is run against an empty registry (`{"constructs": []}`), with the token
as the h-mad `SKILL.md` text, and asserts only on `UNREGISTERED` lines naming that file. Removing
a suffix is `[s for s in EXCLUSION_SUFFIXES if s != suffix]`. Removing a branch is
`a4_pattern` over the other two `A4_BRANCHES` values.

**Branch samples.** `BRANCH_SAMPLES` holds 54 literals, written independently of the patterns. The
per-entry branch counts below were measured at `7e155451` by an in-memory expansion of design
§D2.7's grammar over the spec seed (no file written):
- `subagent-call` 2, `hook-event` 6, `task-tools` 5, `claude-skills-dir` 3, `claude-agents-dir` 3,
  `claude-hooks-dir` 3, `claude-settings` 6, `claude-handoffs-dir` 3, `claude-projects-store` 4,
  `claude-homunculus` 3, `claude-home-bare` 3, `session-reset-command` 2 and
  `skill-slash-invocation` 2 (13 branching entries, 45 branches);
- 1 each for the other 9 entries.

That is 45 + 9 = 54 branches. `SEED_IDS` lists the 22 spec-seed ids, and `RETIRED_IDS` is `{}`.
`BRANCH_SAMPLES` is keyed by construct id (22 keys at the seed), and the sample test is
parametrized over its keys, so a retired id (removed from `BRANCH_SAMPLES`) has no sample node
and an added id (a new key) has one. `test_registry_holds_every_seed_id` and item 20 share one
module helper, `_missing_seed_ids(registry_ids, seed_ids, retired) -> list[str]`: the seed ids
that are neither in `registry_ids` nor a `retired` key with a non-empty reason.

**Tests** (125 collected items):
1. `test_live_registry_and_skill_files_are_clean` (1). It asserts
   `"registry" in result.stages`, no failure line naming the registry or either `SKILL.md`, and no
   failure line whose `file=` names none of the nine files.
2. `test_live_adapter_is_clean[h-mad-codex|h-mad-agy|h-mad-grok|handoff-codex|handoff-agy|handoff-grok]`
   (6). Each first asserts `"adapter" in result.stages`, else it fails with "registry unreadable;
   adapter not checked". It then asserts that no failure line names its adapter, and prints every
   line on failure.
3. `test_clean_baseline_yields_nothing` (1).
4. `test_kind_fixture_reports_exactly_its_pair[…]` (42): one id per row D01–D42, spelled as in the
   table.
5. `test_suppression_rule_leaves_one_pair[a|b|c|d|e]` (5).
6. `test_absent_adapter_file_reads_as_no_heading` (1): a control, not a 43rd kind fixture.
7. `test_catch_all_axis_alone_reports_its_fixture[A1|A2|A3|A4-tilde|A4-home|A4-home-braced]` (6).
8. `test_removing_an_axis_or_branch_clears_its_fixture[A1|A2|A3|A4|A4-tilde|A4-home|A4-home-braced]`
   (7). For a branch id, the other two A4 fixtures are still reported.
9. `test_default_axes_report_each_fixture[A1|A2|A3|A4-tilde|A4-home|A4-home-braced]` (6). It calls
   `check(paths)` with no `axes=` argument.
10. `test_exclusion_suffix_hides_its_fixture[Error|Exception|Warning|Expired|Exit|Interrupt]` (6).
11. `test_removed_exclusion_suffix_reports_its_fixture[Error|Exception|Warning|Expired|Exit|Interrupt]`
    (6).
12. `test_unregistered_teamcreate_then_registered_passes` (1). This is AC-4.4: the fixture reports
    `` `TeamCreate` ``. After a `team-create` entry (pattern `\bTeamCreate\b`, skills `["h-mad"]`)
    and its row in the three h-mad adapters are added, it yields `[]`.
13. `test_fenced_pipe_table_is_not_the_table` (1). The baseline gets, inside h-mad codex's
    `## Construct mapping` and before the real table, a fenced block holding a pipe table with a
    `zeta-thing` row. It yields `[]`.
14. `test_registry_holds_every_seed_id` (1). It first asserts that the live registry file exists,
    then AC-1.2: `_missing_seed_ids(<live registry ids>, SEED_IDS, RETIRED_IDS) == []`.
15. `test_registry_branch_samples[…]` (22 at the seed): one id per `BRANCH_SAMPLES` key, spelled
    as the construct id (for example `claude-settings`). Each case reads that id's pattern from
    the live registry.
16. `test_branch_expander_refuses_unsupported_shapes[group-plus|atom-brace|unbalanced]` (3), over
    `(?:a|b)+`, `a{2}` and `(a` respectively.
17. `test_gate_runs_no_host_cli` (1). Stubs named `codex`, `agy` and `grok` are written to
    `tmp_path/bin`; each writes a marker and exits 99. `PATH` is monkeypatched to put that
    directory first. `check(live_paths(REPO_ROOT))` runs, and the test asserts that no marker
    exists.
18. `test_host_cli_stub_control_fires[codex|agy|grok]` (3). It runs
    `subprocess.run([name], env={"PATH": str(stub_dir)}, timeout=60.0)` and asserts `returncode == 99`
    and that the marker exists.
19. `test_host_parity_has_no_direct_launcher_import` (1). This is a source scan: no
    `import subprocess`, `os.system` or `os.popen` in `host_parity.py` (direct-only, plan AC-3.5
    note).
20. `test_seed_check_honours_retirement[retired-with-reason|retired-empty-reason|absent-not-retired]`
    (3), the positive control for the retirement reason. It calls `_missing_seed_ids` in memory,
    with `seed_ids=["advisor", "claude-md"]` and `registry_ids=["claude-md"]`, and
    `retired` set to `{"advisor": "fixture reason"}`, `{"advisor": ""}` and `{}` respectively. The
    expected results are `[]`, `["advisor"]` and `["advisor"]`. It reads no registry file.
21. `test_host_parity_has_no_fence_scanner` (1). It imports the module-level
    `recognition_sites` from `test_h_mad_doc_block_exec` (defined at line 327 of
    `h-mad/tests/test_h_mad_doc_block_exec.py`, read at `a85abf7f`). It first asserts the positive
    control `recognition_sites("def f(t):\n    return t.startswith('#')\n") == {"f"}`, then
    `recognition_sites(<host_parity.py source>) == set()`. This is the guard that host_parity
    adds no fence scanner: the existing `test_extract_has_no_fence_state_of_its_own` parses only
    `h_mad_doc_block_exec.py`, so it cannot fail on anything in `host_parity.py`.
22. `test_expand_branches_optional_group_adds_empty_alternative` (1). It asserts
    `sorted(expand_branches("x(?:y)?z")) == ["xyz", "xz"]`, over a literal pattern, reading no
    registry. It is E1's killing test ("one expander alternative dropped", design §"Mutation
    specs"), so E1 no longer depends on which registry entries keep an optional group (audit cycle
    2, teammate should 3: at the seed `claude-settings` is the only one of the 22 patterns with an
    optional group, spec seed table lines 68–89).

1+6+1+42+5+1+6+7+6+6+6+1+1+1+22+3+1+3+1+3+1+1 = 125.

**Expected RED split**: the test module imports `host_parity` at module level (design
Implementation Order step 3), so RED is one collection error,
`ModuleNotFoundError: No module named 'host_parity'`, with 0 items. **After GREEN**: 95 passed and
30 failed. The 30 are exactly the carried-RED set for Task 2: the registry node fails on
`REGISTRY_UNREADABLE reason=missing_file`, each adapter node fails on its stage guard, and the 23
registry-file tests fail on "registry file absent". Items 20, 21 and 22 read no registry file
and pass. **Regression guards**: the full suite, including item 21 (host_parity reuses
`_fence_events`; it adds no fence scanner). Items 17, 19, 20 and 21 are guards whose only RED is
the collection error, so each gets a loss-of-behavior run as a Task 15 guard row (Deviation 9):
G1–G3 (item 19), G4–G5 (item 21), G6 (item 17) and G7 (item 20).

**Acceptance Criteria**:
- [ ] AC-1.1: D02, D07–D10, D12, D14, D15, D16 and D17 each yield exactly their pair.
- [ ] AC-3.2: `test_kind_fixture_reports_exactly_its_pair[row-missing]`.
- [ ] AC-3.3: the 42 fixture nodes, `test_clean_baseline_yields_nothing` and the five suppression
  nodes.
- [ ] AC-3.4: `[stale-entry]` and `[undeclared-skill]`.
- [ ] AC-3.5: `test_gate_runs_no_host_cli` with `test_host_cli_stub_control_fires[codex|agy|grok]`
  as its positive control. Each stub is a `#!/bin/sh` script that writes its marker with a shell
  redirection (`: > marker`), a builtin, because the control's child `PATH` holds only the stub
  directory and `touch` is not on it.
- [ ] AC-4.2: items 7, 8 and 9. AC-4.3: items 10 and 11. AC-4.4: item 12.

**Mutation rows** (authored and run in Task 15): 73 rows of `host_parity.json` (66 design and
split rows, and guard rows G1–G7).

**Dependencies on other tasks**: Task 1

---

## Task 3: host-constructs-registry

**Production file**: `h-mad/references/host-constructs.json` (new)
**Test file**: `h-mad/tests/test_host_construct_parity.py` (written in Task 2; this task adds
tests only if Item 9 of Task 1 adds an entry, as described below)
**Task shape**: `new-behaviour`

**Description**: Design §D1. The registry is `seed.json`'s `constructs` array with exactly the
Task 1 AC-4.6 record applied, and an optional `$comment` naming that record. If the record adds an
entry, this task adds a `BRANCH_SAMPLES` key for it holding one sample per branch, which adds its
sample node. If it retires one, it removes that id's `BRANCH_SAMPLES` key (so the retired id has
no sample node) and adds a `RETIRED_IDS` key with the reason, and the Phase-6 record names the
same key. `SEED_IDS` stays the 22 spec ids. A false hit never reaches this task: Task 1 halted on
it (§Task 1 item 9). Then, in one shell with the §Preamble `BASE_SHA` block, take the per-branch
reading:
`/opt/anaconda3/bin/python docs/03-analysis/probes/multi-host-runtime/seed_coverage.py --sha "$BASE_SHA" --registry h-mad/references/host-constructs.json --branches`.
Record it in the Phase-6 document, with every `ZERO` cell listed for the Phase-6 classification.
At `7e155451`, an in-memory run of the same computation over the seed read
`branches=54 cells=72 zero=25 dead=14`, which is DP2's figure. The figure moves with either
`SKILL.md`.

**Expected RED split**, stated as formulas over `S = len(BRANCH_SAMPLES)` after this task's
edits (S = 22 when the AC-4.6 record changes nothing; S = 22 + added − retired otherwise). At the
start of the task the 30 carried nodes fail (registry absent). After GREEN, 2 + S pass:
`test_live_registry_and_skill_files_are_clean`, `test_registry_holds_every_seed_id` and the S
samples (24 when S = 22). The 6 adapter nodes stay RED, and their failure changes from the stage
guard to `TABLE_MISSING reason=no_heading`. Check that change in the output: it is the executed
evidence that the vacuity guard and the adapter stage both work. The carried-RED ledger's Task-3
row (6) is unchanged by S. Whenever S ≠ 22, the Phase-6 document records the re-derived counts.
**The four record kinds** (Task 1 item 9), and what each moves: **add** a `BRANCH_SAMPLES` key
(S + 1) and a `## Construct mapping` row in each adapter of every declared skill; **retire** the
key (S − 1), a `RETIRED_IDS` key with the reason, and the id's adapter rows; **amend `skills`**
leaves S unchanged and adds or removes that id's row in the adapters of the skill gained or lost,
so the per-adapter row count Tasks 8–13 state ("17 at the seed") follows the registry; **amend
`pattern`** leaves S unchanged and rewrites that key's samples to one per branch of the new
pattern, so the Phase-6 per-branch figure is re-derived. E1's killing test is item 22 of Task 2,
which reads no registry, so no record kind can remove it.
**Regression guards**: the 95 Task-2 nodes that already passed.

**Acceptance Criteria**:
- [ ] AC-1.1 (live half): the committed registry passes the registry stage (item 1 node).
- [ ] AC-1.2: `test_registry_holds_every_seed_id`.
- [ ] AC-4.1 at this tree: the item 1 node shows no `UNREGISTERED`.

**Mutation rows**: none. **Dependencies on other tasks**: Task 2

---

## Task 4: host-classifier

**Production file**: `h-mad/scripts/h_mad_host.py` (new)
**Test file**: `h-mad/tests/test_h_mad_host_declaration.py` (new). Test support is appended to
`h-mad/tests/conftest.py` in this task's RED commit (Deviation 1).
**Task shape**: `new-behaviour`

**Description**: Design §D3. The module is stdlib only and imports nothing from `scripts/`.

**Landed literals** (Task 15 rows H1–H3 anchor here):
```python
HOST_ENV = "HMAD_HOST"
NON_CLAUDE_HOSTS = ("codex", "agy", "grok")


def classify_host(environ: Mapping[str, str] | None = None) -> tuple[str, str | None]:
    """('claude', value) | ('declared', value) | ('unknown', value); value None when unset."""
    env = os.environ if environ is None else environ
    value = env.get(HOST_ENV)
    if value is None or value in ("", "claude"):
        return ("claude", value)
    if value in NON_CLAUDE_HOSTS:
        return ("declared", value)
    return ("unknown", value)
```

**Conftest append** (after the file's last line; `h-mad/tests/conftest.py` is 101 lines at
`7e155451`, and no existing line changes):
```python
import os

_AMBIENT_HOST_KEYS = ("HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CONTEXT_WINDOW")


@pytest.fixture
def hermetic_env():
    """Build a subprocess environment carrying no ambient Claude or host markers."""
    def make(**extra: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items()
               if not k.startswith("CLAUDE") and k not in _AMBIENT_HOST_KEYS}
        env.update(extra)
        return env
    return make
```

**Tests** (10 collected items). The module puts `h-mad/scripts` on `sys.path` and imports
`h_mad_host` inside a fixture, `host`, so RED is one failure per test:
1. `test_classify_host[unset|empty|claude|codex|agy|grok|zzz|Grok|space-grok]` (9). The expected
   results are `unset` → `("claude", None)` (from `{}`); `empty` → `("claude", "")`; `claude` →
   `("claude", "claude")`; `codex`, `agy` and `grok` → `("declared", v)`; `zzz`, `Grok` and
   `space-grok` (value `" grok"`) → `("unknown", v)`.
2. `test_hermetic_env_drops_claude_names_and_backend` (1). With `CLAUDE_ZZZ_PROBE=1`,
   `CLAUDECODE=1`, `HPW_AGENT_BACKEND=claude`, `HMAD_HOST=grok` and `HMAD_CONTEXT_WINDOW=5`
   monkeypatched in, `hermetic_env(X="1")` holds none of them and holds `X`. A child started with
   that env through
   `subprocess.run([sys.executable, "-c", <print sorted CLAUDE* names as JSON>], env=hermetic_env(X="1"), capture_output=True, text=True, timeout=60.0)`
   prints `[]`. This is the positive control that the dict reaches a real child.

**Expected RED split**: 9 failing (`ModuleNotFoundError` in the `host` fixture) and 1 passing (the
conftest control lands with the tests). **Regression guards**:
`test_hermetic_env_drops_claude_names_and_backend`, and
`test_h_mad_portable_timeout.py::test_no_document_or_script_emits_a_bare_timeout_command`, whose
parametrization picks up the new script.

**Acceptance Criteria**:
- [ ] The exact value rule of design §D3: no strip, no case fold, `""` is Claude.

The hermetic control passes at RED, so it is a guard with no RED of its own; its loss-of-behavior
runs are guard rows HE1–HE4 (Deviation 9), anchored on the conftest append's two lines
`_AMBIENT_HOST_KEYS = ("HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CONTEXT_WINDOW")` and
`               if not k.startswith("CLAUDE") and k not in _AMBIENT_HOST_KEYS}`, each of which
occurs exactly once in `h-mad/tests/conftest.py` after the append.

**Mutation rows** (Task 15): H1, H2, H3 and guard rows HE1–HE4 in `host_declaration.json` — 7
rows.

**Dependencies on other tasks**: Task 1

---

## Task 5: budget-host-check

**Production file**: `h-mad/scripts/h_mad_context_budget.py`
**Test file**: `h-mad/tests/test_h_mad_host_declaration.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_context_budget.py:main` → `classify_host`
**WIRE-PIN**: `h-mad/tests/test_h_mad_host_declaration.py::test_budget_host_unsupported_valid_transcript[grok]`

**Description**: Design §D4 (W1). The import `from h_mad_host import classify_host` lands after
`from pathlib import Path`. The script already imports `json` and `re` (`grep -n '^import'` at
`7e155451`: `argparse`, `glob`, `json`, `os`, `re`, `sys`). The host block below lands between
`    args = ap.parse_args(argv)` and `    ceiling = args.ceiling`, byte-for-byte as written. None of
its lines contains any of the nine `context_budget.json` anchors.

**Landed literals**:
```python
    host_class, host_value = classify_host()
    if host_class == "declared":
        print(f"ERROR: HMAD_HOST={host_value} has no Claude transcript to measure", file=sys.stderr)
        print(f"CTXBUDGET: UNKNOWN reason=host_unsupported host={host_value}")
        return 2
    if host_class == "unknown":
        print("ERROR: HMAD_HOST is not a known host value", file=sys.stderr)
        shown = host_value if re.fullmatch(r"[A-Za-z0-9._-]+", host_value) else json.dumps(host_value)
        print(f"CTXBUDGET: UNKNOWN reason=unknown_host host={shown}")
        return 2
```

**Tests** (17 new collected items; 27 in the file). Each runs
`[sys.executable, str(BUDGET), …]` with `cwd=tmp_path`,
`env=hermetic_env(HOME=str(tmp_path / "home"), HMAD_HOST=value)` and `timeout=60.0`. For
`unset`, `HMAD_HOST` is left out of the extras. Transcripts are written with the record shape of
`test_h_mad_context_budget.py`'s `_turn` helper.
1. `test_budget_host_unsupported_valid_transcript[codex|agy|grok]` (3), fixture (a) and AC-8.1: a
   valid JSONL under `home/.claude/projects/<cwd slug>/`, also passed with `--transcript`. Stdout
   is exactly `CTXBUDGET: UNKNOWN reason=host_unsupported host=<value>` plus a newline, rc 2, and
   no `used=` substring.
2. `test_budget_host_check_precedes_transcript_lookup[codex|agy|grok]` (3), fixture (b):
   `--transcript` names an absent file and `HOME` is empty → `host_unsupported`.
3. `test_budget_host_check_precedes_usage_read[codex|agy|grok]` (3), fixture (c): a transcript with
   no usage record → `host_unsupported`.
4. `test_budget_host_check_precedes_window_check[codex|agy|grok]` (3), fixture (d): `--window 0` →
   `host_unsupported`.
5. `test_budget_unknown_host_encoding[zzz|Grok|space-grok|zzz-newline]` (4), AC-8.2, with a valid
   transcript. Stdout is exactly one line: `host=zzz`, `host=Grok`, `host=" grok"` and
   `host="zzz\n"` (the JSON text, backslash-n), each after
   `CTXBUDGET: UNKNOWN reason=unknown_host `, with rc 2.
6. `test_budget_unknown_host_precedes_window_check[zzz]` (1), AC-8.5: `--window 0` →
   `reason=unknown_host host=zzz`, and no `bad_window`.

3+3+3+3+4+1 = 17.

**Expected RED split**: 17 failing, 10 passing (Task 4's). Without the host check, (a) and item 5
print a `CTXBUDGET: OK` line carrying `used=`, (b) prints `no_transcript`, (c) `no_usage`, and (d)
and item 6 `bad_window`. **WIRE-PIN RED reason**: the pin's stdout is a Claude reading (a
`CTXBUDGET: OK` line carrying `used=`), so the equality assertion on the caller's output fails. The test drives the CLI in a
subprocess, and `h_mad_host` already exists (Task 4), so no import error is involved.
**Regression guards**: the whole existing `h-mad/tests/test_h_mad_context_budget.py` module, run
twice by AC-8.3 at GREEN:
`env -u HMAD_HOST /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests/test_h_mad_context_budget.py`
and
`env HMAD_HOST=claude /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests/test_h_mad_context_budget.py`.
Each summary must show no `failed` and no `error`, and both must show the same `passed` count. The
reading at `1ef1a782` (DP13) was 31 and 31. (Bare `python3` has no pytest on this host: the v1.0
spelling printed `No module named pytest`, audit cycle 1.)
**Wire-scoped revert**: `    host_class, host_value = classify_host()` →
`    host_class, host_value = "claude", None`. The pin fails, because stdout is a Claude reading.
Scored as row WR1 (Task 15).
**Force-fire**: `    if host_class == "declared":` → `    if True:`. Then
`tests/test_h_mad_context_budget.py::TestVerdict::test_ok_below_the_ceiling` fails: it prints
`host=None`, rc 2. Scored as row FF1.

**Acceptance Criteria**:
- [ ] AC-8.1: item 1 for each of `codex`, `agy` and `grok`.
- [ ] AC-8.2: item 5.
- [ ] AC-8.3: the double run above; the byte-identity half is Task 16 and Phase 6.
- [ ] AC-8.5: item 4 and item 6. The unset `--window 0` → `bad_window` clause is held by the
  existing module.

**Mutation rows** (Task 15): W1a, W1b, W1c, E1, E2, E3, WR1 and FF1 in `host_declaration.json` —
8 rows.

**Dependencies on other tasks**: Task 4

---

## Task 6: decide-host-check

**Production file**: `h-mad/scripts/h_mad_resume_decision.py`
**Test file**: `h-mad/tests/test_h_mad_host_declaration.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_resume_decision.py:decide` → `_host_verdict`
**WIRE-PIN**: `h-mad/tests/test_h_mad_host_declaration.py::test_decide_cannot_judge_without_session_id[grok-no-owner]`

**Description**: Design §D5 (W2). `from h_mad_host import classify_host  # noqa: E402` lands
directly after the existing `from h_mad_state_ownership import (…)` block. The module already puts
its own directory on `sys.path` (`SCRIPT_DIR`, read at `7e155451`). The constant and the function
land between `_owned_elsewhere` and `decide`. The three-line check is `decide()`'s first statement,
before `    if not state_file.is_file():`. No new line contains the anchor
`        return "cannot_judge"`, and the anchored pair
`    if not state_file.is_file():` / `        return "start_fresh"` stays byte-identical.

**Landed literals**:
```python
CANNOT_JUDGE_WITHOUT_SESSION = "cannot_judge"


def _host_verdict(session_id: str | None) -> str | None:
    host_class, _host_value = classify_host()
    if host_class == "claude" or session_id:
        return None
    return CANNOT_JUDGE_WITHOUT_SESSION
```
```python
    host_verdict = _host_verdict(session_id)
    if host_verdict is not None:
        return host_verdict
```

**State fixtures** (feature `fx`, `now="2026-09-28T00:00:00Z"`):
- `live-foreign-owner`: `owner_session_id` `sess-other`, `owner_heartbeat_ts` equal to `now`, and
  `last_completed_phase` 4;
- `no-owner`: `last_completed_phase` 4;
- `absent-file`: the path is not created;
- `unreadable-file`: the text `{`;
- `absent-feature`: a record for `other` only.

`parse_ts` accepts the `Z` form (`h-mad/scripts/h_mad_state_ownership.py`, `parse_ts`, read at
`7e155451`). Host env is set with `monkeypatch.setenv` or `monkeypatch.delenv` for the in-process
calls.

**Tests** (32 new collected items; 59 in the file):
1. `test_budget_and_decide_agree[unset|empty|claude|codex|agy|grok|zzz|Grok|space-grok]` (9). For
   each value, the budget CLI on a valid transcript prints `host_unsupported` or `unknown_host`
   exactly when `decide()` on `no-owner` without a session id returns `cannot_judge`.
2. `test_decide_cannot_judge_without_session_id[…]` (15). Each id is the host, a hyphen, then the
   state, for host in `codex`, `agy`, `grok` and state in `live-foreign-owner`, `no-owner`,
   `absent-file`, `unreadable-file`, `absent-feature` (for example `grok-no-owner`). Each expects
   `cannot_judge`.
3. `test_decide_routes_normally_with_session_id[codex|agy|grok]` (3): `no-owner` with
   `session_id="sess-mine"` → `enter_autonomous`.
4. `test_decide_unknown_host_without_session_id[zzz-live-foreign-owner|zzz-no-owner]` (2) →
   `cannot_judge`.
5. `test_decide_empty_session_id_is_no_id[grok-live-foreign-owner|grok-no-owner]` (2), with
   `session_id=""` → `cannot_judge`.
6. `test_resume_decision_cli_under_grok` (1): the CLI with
   `env=hermetic_env(HMAD_HOST="grok")`, `--state` naming the `no-owner` state fixture's file,
   `--feature fx`, no `--session-id`, and `timeout=60.0` → stdout `cannot_judge`.

9+15+3+2+2+1 = 32.

**Expected RED split**: 23 failing and 9 passing among the new items.
- Item 1: 6 fail (the six non-Claude values, where the budget is already wired by Task 5 and
  `decide()` still routes); 3 pass (`unset`, `empty`, `claude`).
- Item 2: 12 fail and 3 pass. The three `unreadable-file` ids (`codex-unreadable-file`,
  `agy-unreadable-file`, `grok-unreadable-file`) already return `cannot_judge` at `7e155451`, so
  those 3 are not RED. After GREEN two independent paths return `cannot_judge` for them, so no
  single-point mutant kills them; they are matrix completeness, not a guard (Deviation 9
  residual).
- Item 3: 3 pass (controls).
- Items 4, 5 and 6: 5 fail.

`_owned_elsewhere` returns `False` for a falsy session id (`if not session_id: return False`,
read at `7e155451`), which is why the live-foreign-owner and empty-id cases route today.
**WIRE-PIN RED reason**: `decide()` exists and returns `enter_autonomous` for `grok-no-owner`, so
the assertion on the caller's return value fails. The test imports `h_mad_resume_decision`, which
exists, and `h_mad_host` exists since Task 4, so no import error is involved.
**Regression guards**: every existing `test_h_mad_resume_decision.py` and
`test_h_mad_feature_lock.py` test (AC-9.2), including
`tests/test_h_mad_feature_lock.py::TestResumeDecisionSurfacesOwnership::test_no_session_id_preserves_legacy_behaviour`.
**Wire-scoped revert**: delete the three-line check from `decide()`. The pin fails
(`enter_autonomous`). Row WR2.
**Force-fire**: `    if host_class == "claude" or session_id:` → `    if session_id:`. With
`HMAD_HOST` unset, the legacy test gets `cannot_judge`. Row FF2.

**Acceptance Criteria**:
- [ ] AC-9.1: item 2's `live-foreign-owner` and `no-owner` ids for each host, plus items 4 and 5.
- [ ] AC-9.2: the regression guards above, unchanged.

Item 1's three Claude ids pass at RED, so each gets a loss-of-behavior run: guard rows AG-unset,
AG-empty and AG-claude apply FF2's mutant (`    if session_id:`), under which `decide()` without a
session id returns `cannot_judge` while the budget CLI still prints a Claude reading, so the
agreement assertion fails. Item 3 is V1's named test and needs no new row.

**Mutation rows** (Task 15): W2a, W2b, V1, V2, WR2, FF2 and guard rows AG-unset, AG-empty and
AG-claude in `host_declaration.json` — 9 rows.

**Dependencies on other tasks**: Task 5 (item 1 needs W1)

---

## Task 7: install-check-roots

**Production file**: `h-mad/scripts/h_mad_install_check.py`, `h-mad/tests/conftest.py` (append
design §D7's `_hermetic_host_skill_roots`)
**Test file**: `h-mad/tests/test_h_mad_install_check_roots.py` (new)
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_install_check.py:main` → `check(agents_skills_dir=agents_dir)`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_install_check_roots.py::test_agents_root[copy]`
**WIRE 2**: `h-mad/scripts/h_mad_install_check.py:main` → `check(agy_skills_dir=agy_dir)`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_install_check_roots.py::test_agy_root_cell[h-mad-copy]`

**Description**: Design §D6 (W3) and §D7. The body of `check_siblings` stays byte-identical, as do
its four anchors and `check()`'s `        checkout.parent if checkout is not None else None`
(`install_check_siblings.json`, read at `7e155451`). `import os` lands after `import argparse`,
and `from collections.abc import Iterable, Mapping` after `import sys`. The existing `main()`
reads `parse_args()` with no argv and has one UNREADABLE branch for an empty `--skills-link` or
`--hook-link` (read at `7e155451`). That branch stays unchanged.

**Landed literals**:
```python
AGENTS_SKILLS_ENV = "HMAD_AGENTS_SKILLS_DIR"
AGY_SKILLS_ENV = "HMAD_AGY_SKILLS_DIR"
AGY_INSTALLED_NAMES = ("h-mad", "handoff")
SIBLING_KINDS = ("NOT_SYMLINK", "DANGLING", "WRONG_CHECKOUT")


def default_host_roots(environ: Mapping[str, str] | None = None) -> tuple[str, str]:
    env = os.environ if environ is None else environ
    home = Path.home()
    agents = env[AGENTS_SKILLS_ENV] if AGENTS_SKILLS_ENV in env else str(home / ".agents" / "skills")
    agy = env[AGY_SKILLS_ENV] if AGY_SKILLS_ENV in env else str(home / ".gemini" / "config" / "skills")
    return agents, agy


def checkout_skill_names(repo: Path) -> list[str]:
    return [p.parent.name for p in sorted(Path(repo).glob("*/" + CHECKOUT_MARKER))]


def split_agy_root(lines, skills_dir, names, installed):
    installed_set = set(installed)
    issues: list[str] = []
    details: list[str] = []
    for line in lines:
        owner = next(((name, kind) for name in names for kind in SIBLING_KINDS
                      if line.startswith(f"SIBLING_{kind}:{skills_dir / name} ")), None)
        if owner is None or owner[0] in installed_set:
            issues.append(line)
        else:
            details.append(f"AGY_SIBLING_COLLISION:{skills_dir / owner[0]} kind={owner[1]}")
    return issues, details
```
In `check()`: the signature becomes
`check(skills_link, hook_link, repo=None, *, agents_skills_dir=None, agy_skills_dir=None, details=None)`.
Directly after the existing `        issues += check_siblings(sibling_repo, skills_link.parent)` line,
inside the existing `if sibling_repo is not None:`, these lines land:
```python
        if agents_skills_dir is not None:
            issues += check_siblings(sibling_repo, Path(agents_skills_dir))
        if agy_skills_dir is not None:
            agy_root = Path(agy_skills_dir)
            agy_issues, agy_details = split_agy_root(
                check_siblings(sibling_repo, agy_root), agy_root,
                checkout_skill_names(sibling_repo), AGY_INSTALLED_NAMES)
            issues += agy_issues
            if details is not None:
                details.extend(sorted(agy_details))
```
In `main()`, the argument `parser.add_argument("--agents-skills-dir", default=None)` and the
argument `parser.add_argument("--agy-skills-dir", default=None)` land before
`    args = parser.parse_args()`. After the existing UNREADABLE branch:
```python
    default_agents, default_agy = default_host_roots()
    agents_dir = args.agents_skills_dir if args.agents_skills_dir is not None else default_agents
    agy_dir = args.agy_skills_dir if args.agy_skills_dir is not None else default_agy
    if not agents_dir.strip() or not agy_dir.strip():
        print("ERROR: --agents-skills-dir and --agy-skills-dir must name a path", file=sys.stderr)
        print("INSTALL: UNREADABLE")
        print("  nothing was checked, so this is not a verdict about the install — pass a path for each skill root.")
        return 2
    details: list[str] = []
```
The existing `check(` call gains three lines after `        Path(args.repo) if args.repo else None,`:
`        agents_skills_dir=agents_dir,`, `        agy_skills_dir=agy_dir,` and
`        details=details,`. After the unchanged verdict block, the loop `    for line in details:` /
`        print(line)` lands. Every new line is checked against the five anchors before GREEN
(Convention 6).

**Conftest append** (design §D7, verbatim):
```python
@pytest.fixture(autouse=True)
def _hermetic_host_skill_roots(monkeypatch, tmp_path):
    monkeypatch.setenv("HMAD_AGENTS_SKILLS_DIR", str(tmp_path / "absent-agents-skills"))
    monkeypatch.setenv("HMAD_AGY_SKILLS_DIR", str(tmp_path / "absent-agy-skills"))
```

**Fixture install.** It is the healthy install that `test_h_mad_install_check.py` builds: a
checkout holding `h-mad/SKILL.md`, `h-mad/hooks/h-mad-tdd-gate.sh`, `handoff/SKILL.md` and
`debugger/SKILL.md`, a Claude skills directory holding `h-mad` → the checkout's `h-mad`, and a
hook link to the checkout's hook. The CLI is run with `--skills-link`, `--hook-link` and `--repo`,
with `env=hermetic_env(...)` and `timeout=60.0`. Except in the two env-driven tests, both new
options are passed explicitly, and an unused root is an absent `tmp_path` path.

**Tests** (33 collected items):
1. `test_agents_root[correct|copy|dangling|other-checkout|absent]` (5), AC-10.1: `handoff` is a
   correct link in the agents root, and `h-mad` takes the named state.
2. `test_empty_root_option_is_unreadable[agents|agy]` (2): the option value `""` → stdout line 1
   `INSTALL: UNREADABLE`, rc 2.
3. `test_empty_env_override_is_unreadable[agents|agy]` (2): no option, and the variable `""` given
   through `hermetic_env` → `INSTALL: UNREADABLE`, rc 2.
4. `test_explicit_option_beats_env_override[agents|agy]` (2): the option names a root holding a
   copy of `h-mad`, and the variable names a root holding a correct link → the option root's
   `SIBLING_NOT_SYMLINK` is reported.
5. `test_agy_root_cell[…]` (12), AC-10.5, with the ids:
   - `h-mad-correct` → `INSTALL: PASS`, no detail line;
   - `h-mad-copy`, `h-mad-dangling` and `h-mad-other-checkout` → `SIBLING_NOT_SYMLINK`,
     `SIBLING_DANGLING` and `SIBLING_WRONG_CHECKOUT` respectively, with `INSTALL: FAIL`;
   - `handoff-copy`, `handoff-dangling` and `handoff-other-checkout` → the same three tokens;
   - `both-absent` → `INSTALL: PASS`;
   - `debugger-copy`, `debugger-dangling` and `debugger-other-checkout` → `INSTALL: PASS` with
     exactly one `AGY_SIBLING_COLLISION:` line whose `kind=` is `NOT_SYMLINK`, `DANGLING` and
     `WRONG_CHECKOUT` respectively, and no `SIBLING_` line;
   - `h-mad-copy-plus-debugger-copy` → `INSTALL: FAIL issues=1`, one `SIBLING_` line and one
     `AGY_SIBLING_COLLISION:` line.
6. `test_claude_root_debugger_copy_still_fails` (1), AC-10.6: `debugger` is a plain directory in
   the `--skills-link` parent → `SIBLING_NOT_SYMLINK`, `INSTALL: FAIL`, and no
   `AGY_SIBLING_COLLISION:` line.
7. `test_absent_roots_add_no_line` (1): both roots absent → stdout exactly `INSTALL: PASS` then
   `OK`, and no line naming either root.
8. `test_env_override_is_read[agents|agy]` (2): no option; the variable names a root holding a copy
   of `h-mad` → that root's `SIBLING_NOT_SYMLINK`.
9. `test_default_roots_resolve_to_documented_paths` (1):
   `default_host_roots({}) == (str(Path.home() / ".agents" / "skills"), str(Path.home() / ".gemini" / "config" / "skills"))`.
   The CLI is never run.
10. `test_detail_lines_sorted_and_after_verdict` (1): the checkout adds `zeta/SKILL.md`, and the
    agy root holds plain directories `zeta` and `debugger` → stdout is `INSTALL: PASS`, `OK`, then
    the `debugger` detail line, then the `zeta` one.
11. `test_check_without_root_keywords_reads_no_new_root` (1): in process, with both variables
    pointing at roots that hold an `h-mad` copy, `check(skills_link, hook_link, repo)` returns
    `[]`.
12. `test_unattributable_sibling_line_stays_an_issue` (1):
    `split_agy_root(["SIBLING_NOT_SYMLINK:/elsewhere/x (expected -> /y)"], Path("/agy"), ["h-mad"], ("h-mad", "handoff"))`
    → that line is in `issues` and `details` is `[]`.
13. `test_checkout_names_agree_with_check_siblings` (1): design §D6. A checkout of three skills,
    each installed as a copy under a temp root; the set of names in `check_siblings`' lines equals
    `set(checkout_skill_names(repo))`.
14. `test_split_prefix_does_not_capture_a_longer_name` (1): the checkout's skills are `h-mad`,
    `handoff` and `h-mad-x`; the agy root holds `h-mad-x` as a plain directory → `INSTALL: PASS`
    and exactly one `AGY_SIBLING_COLLISION:<agy>/h-mad-x kind=NOT_SYMLINK`.

5+2+2+2+12+1+1+2+1+1+1+1+1+1 = 33. The module imports `h_mad_install_check as ic` and reads each
new symbol as an attribute of `ic` inside the test body (`ic.split_agy_root`), so a missing symbol
is one failure, never a collection error.

**Expected RED split**: 32 failing and 1 passing. Every CLI test that passes a new option gets
argparse's rc 2 and empty stdout. Items 3 and 8 (no option) get today's `INSTALL: PASS`, because
the variables are ignored. Items 9, 12 and 13 hit a missing attribute. Item 11 passes, because
today's `check()` reads no new root. **WIRE-PIN RED reason**: for both pins, argparse refuses the
new option (rc 2), so the assertion that stdout names `SIBLING_NOT_SYMLINK:` under the new root
fails. It is a CLI subprocess, and no import of a missing symbol is involved.
**Regression guards**: all 23 `def test_` lines of `h-mad/tests/test_h_mad_install_check.py`
(`grep -c 'def test_'` → 23 at `7e155451`, 7 of them in `class TestSiblingSkills`) under the new
autouse override (AC-10.2, first clause), and item 11.
**Wire-scoped reverts**: remove `        agents_skills_dir=agents_dir,` from `main()`'s call, and pin 1
fails (row WR3a). Remove `        agy_skills_dir=agy_dir,`, and pin 2 fails (row WR3b).
**Force-fires**, one per root wire, each making `check()` read its root even when the caller
passed no root keyword. FF3a inserts, directly before `        if agents_skills_dir is not None:`,
the line
`        agents_skills_dir = agents_skills_dir if agents_skills_dir is not None else os.environ.get(AGENTS_SKILLS_ENV)`;
FF3b inserts, directly before `        if agy_skills_dir is not None:`, the line
`        agy_skills_dir = agy_skills_dir if agy_skills_dir is not None else os.environ.get(AGY_SKILLS_ENV)`.
The fallback is inside the body on purpose: a mutated signature default would be evaluated once,
at import, before the test's `monkeypatch.setenv`, and would survive. Each is killed by assertion by
`test_check_without_root_keywords_reads_no_new_root`: both variables name roots holding an
`h-mad` copy, so under FF3a the agents root yields `SIBLING_NOT_SYMLINK`, and under FF3b the agy
root yields it too (`h-mad` is an installed agy name, so `split_agy_root` keeps it as an issue).
Either way `check()` no longer returns `[]`. `os` is imported by this task, so neither mutant is
an import crash. I1 (the name split inverted, killed by `test_agy_root_cell[debugger-copy]`) and
I2 (the split applied to the Claude root, killed by `test_claude_root_debugger_copy_still_fails`)
are design members that mutate the split's behaviour. They are not force-fires of a `main` →
`check` connection.

**Acceptance Criteria**:
- [ ] AC-10.1: item 1. AC-10.3: items 2, 3 and 4. AC-10.5: item 5. AC-10.6: item 6 and the existing
  `TestSiblingSkills`.
- [ ] AC-10.2: the existing module unchanged, plus item 7 as its permanent pin. The byte-identity
  half is Task 16 and Phase 6.

**Mutation rows** (Task 15): I1, I2, I3a, I3b, I4a, I4b, I5a, I5b, I6, I7, WR3a, WR3b, FF3a and
FF3b in `install_check_roots.json` — 14 rows.

**Dependencies on other tasks**: Task 4 (the `hermetic_env` fixture)

---

## Task 8: adapter-h-mad-codex

**Production file**: `h-mad/references/codex-runtime.md`
**Test file**: `h-mad/tests/test_host_runtime_docs.py` (new)
**Task shape**: `new-behaviour`

**Description**: Design §D9. At `7e155451` the file's headings are `# Codex runtime adapter`,
`## Package and project roots`, `### Trust boundary`, `## Collaboration mapping`,
`## Seven phases` and `## State and halt discipline`. `### Trust boundary` belongs to
`codex-tdd-gate-defects` and is not touched. Append, after `## State and halt discipline` and in
this order, `## Install`, `## Context budget and claims` and `## Construct mapping`.
- **`## Install`**: the two commands `ln -s /path/to/checkout/h-mad ~/.agents/skills/h-mad` and
  `ln -s /path/to/checkout/handoff ~/.agents/skills/handoff`, in a fenced block. It also states:
  "an existing non-symlink at either path is an operator decision and is never overwritten";
  "creating the link does not re-arm HemaSuite's codex TDD gate: its tracked `.codex/hooks.json`
  reads `{"hooks": {}}`"; and the check
  `python3 "$HMAD_SKILL_ROOT/scripts/h_mad_install_check.py" --agents-skills-dir ~/.agents/skills`.
- **`## Context budget and claims`**: design §D9.2's four points. Every fence opens at indent 0,
  outside any list item, because `_fence_events` recognises only an opener matching
  `^(?P<indent> {0,3})`. One fence holds exactly the budget line
  `HMAD_HOST=codex python3 "$HMAD_SKILL_ROOT/scripts/h_mad_context_budget.py"`. A second fence
  holds the seven lines of design §D9.2, with the design's host slot written `codex` and its
  sid-read slot written out in full. That full text, called SID_READ in this plan, is exactly
  `"$(cat "$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>")"`. The oracle line
  comes first. The feature slot stays literal in the adapter; the orchestrator fills it. The prose carries `CTXBUDGET: UNKNOWN reason=host_unsupported`, `80%`,
  `substitute: none`, `once at bootstrap`, and `never deleted or reused without the operator`. No
  fenced line holds `$SID`.
- **`## Construct mapping`**: one row per registry entry declaring `h-mad` (17 at the seed; the
  count follows the Task 3 registry). Each row is the codex column of design §D9.3, with the id
  backticked in the `construct` cell and a literal pipe written `\|`. Tokens every row must also
  carry (Deviation 5):
  - `advisor`: `not-applicable`, `hmad-dispatch exec`, `collaboration.spawn_agent` and
    `fork_turns` in `mapping`;
  - `session-id-env`: `uuid.uuid4()` and `owned_elsewhere` in `mapping`;
  - every `not-applicable` row's `mapping` states its reason in at least three words (AC-2.2).
- **Text constraints**: no `Agent(subagent_type:`, `AskUserQuestion` or `TodoWrite` anywhere in
  the file, because `h-mad/tests/test_h_mad_codex_runtime.py` asserts that. Name constructs by
  kebab id.

**Test file skeleton** (this task creates it; later tasks add params):
- `REPO_ROOT = Path(__file__).resolve().parents[2]`, and a dict `ADAPTERS` mapping each of the
  six ids `h-mad-codex`, `h-mad-agy`, `h-mad-grok`, `handoff-codex`, `handoff-agy` and
  `handoff-grok` to its path, for example `REPO_ROOT / "h-mad/references/codex-runtime.md"`;
- `_section(text, heading) -> str` uses `find_heading` and `fence_aware_end`, and raises
  `LookupError` naming the heading on `None` or `AmbiguousHeading`. Its landed body (Task 15's
  guard rows L1 and L2 anchor on the two tagged lines, each of which occurs exactly once in the
  file):
  ```python
  def _section(text: str, heading: str) -> str:
      try:
          found = find_heading(text, heading)
      except AmbiguousHeading:
          raise LookupError(f"heading doubled: {heading}")  # M:L2
      if found is None:
          raise LookupError(f"heading absent: {heading}")  # M:L1
      start, level = found
      return text[start:fence_aware_end(text, start, level)]
  ```
- `_fenced_lines(section) -> list[str]` returns, for each `body` event `e` of
  `_fence_events(section)`, the line `section[e.start:e.end].rstrip("\r\n")`. It never reads
  `e.text`, which is `""` for every `body` event (Task 2 description);
- `_row(adapter_id, construct_id) -> Row` calls `host_parity.adapter_table`, asserts
  `problems == []` and exactly one row with that id, and returns it.

No test splits a table line itself.

**Tests** (29 new collected items):
1. `test_advisor_row[h-mad-codex-status|h-mad-codex-hmad-dispatch-exec|h-mad-codex-spawn-agent|h-mad-codex-fork-turns]`
   (4). `status` asserts `not-applicable`; the rest assert `hmad-dispatch exec`,
   `collaboration.spawn_agent` and `fork_turns` in `mapping`.
2. `test_session_id_env_row[h-mad-codex-uuid4|h-mad-codex-owned-elsewhere]` (2).
3. `test_claims_section_fenced_lines[…]` (11), with the ids `h-mad-codex-` followed by
   `create-claim`, `claim`, `beat`, `set`, `release`, `oracle`, `mint`, `oracle-first`,
   `no-dollar-sid`, `prose-once-at-bootstrap` and `prose-never-deleted`. These are design §D12's
   AC-9.3 row, one case each, with SID_READ as the literal text.
4. `test_claims_lines_execute_across_invocations[h-mad-codex]` (1): design §D12 OD-5. Inside a
   `tmp_path` repository made by `git init`, with `docs/.bkit-memory.json` seeded `{}`
   (Deviation 4) and the feature slot replaced by `fixture-feature`, each line runs in its own
   `subprocess.run(["bash", "-c", line], cwd=repo, env=hermetic_env(HMAD_SKILL_ROOT=<checkout h-mad>, HOME=<empty tmp>), timeout=60.0)`.
   The assertions are:
   - the mint line prints `SID: MINTED`;
   - a second mint prints `SID: NOT_MINTED` and leaves the file's bytes unchanged;
   - the `--create --claim` line sets `owner_session_id` to the file's id, read from the JSON
     directly;
   - the oracle line prints neither `cannot_judge` nor `owned_elsewhere`;
   - control: the oracle line with SID_READ replaced by `""` prints `cannot_judge`.
5. `test_not_applicable_rows_state_a_reason[h-mad-codex]` (1): design §D12's AC-2.2 row. It first
   asserts that at least one `not-applicable` row exists.
6. `test_context_budget_section[h-mad-codex-unknown|h-mad-codex-80pct|h-mad-codex-substitute-none]`
   (3).
7. `test_budget_line_runs_and_reports_host[h-mad-codex]` (1). Exactly one fenced line matches
   `^HMAD_HOST=codex python3 "\$HMAD_SKILL_ROOT/scripts/h_mad_context_budget\.py"$`. That line,
   run with `bash -c` and the `hermetic_env` of item 4, prints exactly
   `CTXBUDGET: UNKNOWN reason=host_unsupported host=codex`.
8. `test_install_section[h-mad-codex-agents-h-mad|h-mad-codex-agents-handoff|h-mad-codex-ln-s|h-mad-codex-never-overwritten|h-mad-codex-codex-hooks-json|h-mad-codex-does-not-re-arm]`
   (6).

4+2+11+1+1+3+1+6 = 29.

**Expected RED split**: 29 failing, because the three sections are absent and each locator raises
`LookupError`. The carried node `test_live_adapter_is_clean[h-mad-codex]` also fails
(`TABLE_MISSING reason=no_heading`). **After GREEN**: the 29 new items and that node pass, and the
ledger drops to 5. **Regression guards**: `h-mad/tests/test_h_mad_codex_runtime.py` (AC-6.6,
unchanged), the `test_h_mad_portable_timeout.py` scans over `references/*.md`, and the
unfilled-inline-slot scan (the `INLINE_` placeholder check) in `test_h_mad_skill_reviewer_prompt.py`.

**Acceptance Criteria**:
- [ ] AC-2.1 and AC-6.2 (codex h-mad): `test_live_adapter_is_clean[h-mad-codex]` passes.
- [ ] AC-2.2: the live node's `CELL_EMPTY` check plus item 5. AC-2.3 and AC-6.3: item 1. AC-2.5 and
  AC-6.5: item 2.
- [ ] AC-8.1 (documented path): item 7. AC-8.4: item 6. AC-9.3: items 3 and 4. AC-10.4: item 8.

**Mutation rows**: none. **Dependencies on other tasks**: Task 3, Task 5, Task 6, Task 7

---

## Task 9: adapter-h-mad-agy

**Production file**: `h-mad/references/agy-runtime.md`
**Test file**: `h-mad/tests/test_host_runtime_docs.py`
**Task shape**: `new-behaviour`

**Description**: Design §D9. At `7e155451` the headings are `## Package and project roots`,
`## Hooks`, `## The TDD gate`, `## Author and reviewer roles`, `## Memory index` and
`## What does not change`. Insert `## Install`, `## Context budget and claims` and
`## Construct mapping`, in that order, before `## What does not change`. In
`## Package and project roots`:
- replace the one "typically" sentence (`grep -c typically` → 1 at `7e155451`) with "the
  operator-installed link `~/.gemini/config/skills/h-mad` (§Install below), when it exists";
- extend the install-check paragraph with `--agy-skills-dir` checking this host's own root, keeping
  the `SKILL_NOT_INSTALLED` explanation for the Claude link, and keeping the sentence "Do not run
  it as a gate here" byte-identical (it occurs once at `7e155451`).

`## Install` carries `ln -s /path/to/checkout/h-mad ~/.gemini/config/skills/h-mad` and the
`handoff` line, "never overwritten", and
`python3 "$HMAD_SKILL_ROOT/scripts/h_mad_install_check.py" --agy-skills-dir ~/.gemini/config/skills`.
`## Context budget and claims` is Task 8's section with `agy` for `codex`. Table rows come from the
agy column of design §D9.3. The `advisor` row carries `not-applicable`, `hmad-dispatch exec` and
`invoke_subagent`. The `session-id-env` row carries `uuid.uuid4()` and `owned_elsewhere`.

**Tests** (26 new collected items):
- `test_advisor_row[h-mad-agy-status|h-mad-agy-hmad-dispatch-exec|h-mad-agy-invoke-subagent]` (3);
- `test_session_id_env_row[h-mad-agy-uuid4|h-mad-agy-owned-elsewhere]` (2);
- `test_claims_section_fenced_lines` with the eleven Task-8 case suffixes after `h-mad-agy-` (11);
- `test_claims_lines_execute_across_invocations[h-mad-agy]` (1);
- `test_not_applicable_rows_state_a_reason[h-mad-agy]` (1);
- `test_context_budget_section[h-mad-agy-unknown|h-mad-agy-80pct|h-mad-agy-substitute-none]` (3);
- `test_budget_line_runs_and_reports_host[h-mad-agy]` (1);
- `test_install_section[h-mad-agy-gemini-h-mad|h-mad-agy-gemini-handoff|h-mad-agy-ln-s|h-mad-agy-never-overwritten]`
  (4).

3+2+11+1+1+3+1+4 = 26.

**Expected RED split**: 26 failing (sections absent). The carried node
`test_live_adapter_is_clean[h-mad-agy]` also fails, then passes at GREEN, and the ledger drops to
4. **Regression guards**: after the edit, `grep -c 'Do not run it as a gate here'
h-mad/references/agy-runtime.md` → 1 and `grep -c typically h-mad/references/agy-runtime.md` → 0.
The Task 8 nodes also guard.

**Acceptance Criteria**:
- [ ] AC-2.1 and AC-6.2 (agy h-mad): the live node. AC-2.3, AC-6.3, AC-2.5, AC-6.5, AC-8.4, AC-9.3
  and AC-10.4: the items above.

**Mutation rows**: none. **Dependencies on other tasks**: Task 8

---

## Task 10: adapter-h-mad-grok

**Production file**: `h-mad/references/grok-runtime.md` (new; absent at `7e155451`)
**Test file**: `h-mad/tests/test_host_runtime_docs.py`
**Task shape**: `new-behaviour`

**Description**: Design §D9. The sections, in order: `# grok runtime adapter`,
`## Version and compatibility`, `## Package and project roots`, `## Install`, `## Project trust`,
`## Hooks`, `## The TDD gate`, `## Author and reviewer roles`, `## Context budget and claims`,
`## Memory index`, `## Construct mapping` and `## What does not change`. Content is design
§D9.2, section by section. The pinned tokens are:
- **`## Version and compatibility`**: `1.0.41`, `compat.claude.skills` and `compat.claude.hooks`.
- **`## Hooks`**: `h-mad-advisor-warn.sh`, `CTXBUDGET` and `ignore`. The handler limit is written
  as "a 5 s handler limit, after which the handler fails open" (Convention 9).
- **`## The TDD gate`**: `step5:grok_tdd_hook_unverified`, `toolInput`, `fails open`, `pytest`,
  and reason (i) written from Task 1's `REFUSAL_FORM_AT_BASE` row of design §D9.2's table. Its
  pinned token is `exit 1` for `exit1`, `exit 2` for `a`, or `permissionDecision` for `b`.
- **`## Install`**: Task 8's `## Install` with `~/.agents/skills`.
- **`## Context budget and claims`**: Task 8's section with `grok`. It adds `/context`,
  `not an orchestrator gate`, `GROK_SESSION_ID`, and the phrase
  `only after the live smoke records it present in the orchestrator's shell`.
- **Table rows** come from the grok column of design §D9.3. Every `source` cell is a chapter file
  matching `\b\d\d-[a-z-]+\.md\b`, the literal `grok inspect`, or text beginning `observed:`
  (AC-5.7). Row tokens:
  - `advisor`: `not-applicable`, `hmad-dispatch exec` and `spawn_subagent`;
  - `session-id-env`: `uuid.uuid4()`, `owned_elsewhere`, `GROK_SESSION_ID` and `hook processes`;
  - `claude-projects-store`: `not-applicable`, `~/.grok/memory` and `h_mad_check_memory_index.py`.

The test file gains the module constant `REFUSAL_FORM_AT_BASE`, written literally from Task 1's
record, and the lookup `REFUSAL_TOKEN = {"exit1": "exit 1", "a": "exit 2", "b": "permissionDecision"}[REFUSAL_FORM_AT_BASE]`
at module level. The constant has no default, so a missing or unknown reading is a collection
error.

**Tests** (49 new collected items):
- `test_advisor_row[h-mad-grok-status|h-mad-grok-hmad-dispatch-exec|h-mad-grok-spawn-subagent]` (3);
- `test_session_id_env_row[h-mad-grok-uuid4|h-mad-grok-owned-elsewhere|h-mad-grok-grok-session-id|h-mad-grok-hook-processes]`
  (4);
- `test_claims_section_fenced_lines` with the eleven Task-8 case suffixes after `h-mad-grok-` (11);
- `test_claims_lines_execute_across_invocations[h-mad-grok]` (1);
- `test_not_applicable_rows_state_a_reason[h-mad-grok]` (1);
- `test_grok_session_id_condition[grok-session-id|smoke-condition]` (2);
- `test_version_and_compatibility[h-mad-grok-version|h-mad-grok-compat-skills|h-mad-grok-compat-hooks]`
  (3);
- `test_tdd_gate_section[halt-token|tool-input|fails-open|pytest|reason-i]` (5);
- `test_claude_projects_store_row[status|grok-memory|memory-index-script]` (3);
- `test_grok_source_cells_format[h-mad-grok]` (1). It first asserts at least one row;
- `test_context_budget_section[h-mad-grok-unknown|h-mad-grok-80pct|h-mad-grok-substitute-none|h-mad-grok-slash-context|h-mad-grok-not-a-gate]`
  (5);
- `test_budget_line_runs_and_reports_host[h-mad-grok]` (1);
- `test_install_section[h-mad-grok-agents-h-mad|h-mad-grok-agents-handoff|h-mad-grok-ln-s|h-mad-grok-never-overwritten|h-mad-grok-codex-hooks-json|h-mad-grok-does-not-re-arm]`
  (6);
- `test_hooks_section_advisor_warn_note[hook-name|ctxbudget|ignore]` (3).

3+4+11+1+1+2+3+5+3+1+5+1+6+3 = 49.

**Expected RED split**: 49 failing, because the file does not exist and each locator raises
`LookupError`. The carried node `test_live_adapter_is_clean[h-mad-grok]` passes at GREEN, and the
ledger drops to 3. **Regression guards**: the portable-time-limit scan, which now includes this
file, and the Tasks 8–9 nodes.

**Acceptance Criteria**:
- [ ] AC-2.1 (grok h-mad): the live node. AC-5.1 to AC-5.3 and AC-5.5 to AC-5.7: the items above.
  AC-8.4, AC-9.3 and AC-10.4 for grok.

**Mutation rows**: none. **Dependencies on other tasks**: Task 9

---

## Task 11: adapter-handoff-codex

**Production file**: `handoff/references/codex-runtime.md`
**Test file**: `h-mad/tests/test_host_runtime_docs.py`
**Task shape**: `new-behaviour`

**Description**: Insert `## Construct mapping` before `## Safety invariants`. At `7e155451` the
headings are `## Resolve the skill package`, `## Codex tool mapping`, `## Mode routing` and
`## Safety invariants`. Add one row per registry entry declaring `handoff` (12 at the seed), from
the codex column of design §D9.3. The `task-tools` row is `not-applicable` and names
`.omc/notepad.md` and `update_plan` (as a lead). No `Skill(skill:`, `AskUserQuestion` or
`TodoWrite` appears anywhere in the file (`handoff/tests/test_handoff_codex_runtime.py` forbids
exactly those three, line 37, AC-6.6). `Agent(subagent_type:` is kept out too, as a stricter
self-imposed rule borrowed from `h-mad/tests/test_h_mad_codex_runtime.py`. No text points into an
`h-mad` file.

**Tests** (4 new collected items):
- `test_task_tools_row[handoff-codex-status|handoff-codex-notepad|handoff-codex-update-plan]` (3);
- `test_not_applicable_rows_state_a_reason[handoff-codex]` (1).

**Expected RED split**: 4 failing (no table). The carried node
`test_live_adapter_is_clean[handoff-codex]` passes at GREEN, and the ledger drops to 2.
**Regression guards**: `handoff/tests/test_handoff_codex_runtime.py`.

**Acceptance Criteria**:
- [ ] AC-2.1 and AC-6.2 (codex handoff): the live node. AC-2.4 and AC-6.4 (codex): the
  `task-tools` items. AC-6.6: the regression guard.

**Mutation rows**: none. **Dependencies on other tasks**: Task 10

---

## Task 12: adapter-handoff-agy

**Production file**: `handoff/references/agy-runtime.md`
**Test file**: `h-mad/tests/test_host_runtime_docs.py`
**Task shape**: `new-behaviour`

**Description**: Insert `## Construct mapping` before `## Safety invariants`. Replace the one
"typically" sentence in `## Resolve the skill package` (`grep -c typically` → 1 at `7e155451`)
with "the operator-installed link `~/.gemini/config/skills/handoff`, when it exists", with no
section reference. Rows come from the agy column of design §D9.3. The `task-tools` row is
`not-applicable` and names `manage_task` and `.omc/notepad.md`.

**Tests** (4 new collected items):
- `test_task_tools_row[handoff-agy-status|handoff-agy-manage-task|handoff-agy-notepad]` (3);
- `test_not_applicable_rows_state_a_reason[handoff-agy]` (1).

**Expected RED split**: 4 failing. The carried node `test_live_adapter_is_clean[handoff-agy]`
passes at GREEN, and the ledger drops to 1. **Regression guards**: after the edit,
`grep -c typically handoff/references/agy-runtime.md` → 0.

**Acceptance Criteria**:
- [ ] AC-2.1 and AC-6.2 (agy handoff): the live node. AC-2.4 and AC-6.4 (agy): the `task-tools`
  items.

**Mutation rows**: none. **Dependencies on other tasks**: Task 11

---

## Task 13: adapter-handoff-grok

**Production file**: `handoff/references/grok-runtime.md` (new)
**Test file**: `h-mad/tests/test_host_runtime_docs.py`
**Task shape**: `new-behaviour`

**Description**: The sections, in order: `# grok runtime adapter`, `## Version and compatibility`
(`1.0.41` and `compat.claude.skills`), `## Resolve the skill package`, `## grok tool mapping`
(`todo_write` with its user-visible `Ctrl+T` pane, `spawn_subagent`, and `HANDOFF_SKILL_ROOT`
from the loaded skill path), `## Mode routing`, `## Construct mapping` and `## Safety invariants`.
Rows come from the grok column of design §D9.3. The `task-tools` row is `mapped` and names
`todo_write` and `Ctrl+T`. The `claude-settings` row is `not-applicable` for handoff. `source`
cells follow AC-5.7.

**Tests** (7 new collected items):
- `test_task_tools_row[handoff-grok-status|handoff-grok-todo-write|handoff-grok-ctrl-t]` (3);
- `test_not_applicable_rows_state_a_reason[handoff-grok]` (1);
- `test_version_and_compatibility[handoff-grok-version|handoff-grok-compat-skills]` (2);
- `test_grok_source_cells_format[handoff-grok]` (1).

**Expected RED split**: 7 failing (the file is absent). The carried node
`test_live_adapter_is_clean[handoff-grok]` passes at GREEN, and the ledger is empty: AC-3.1's seven
live nodes all pass from here on.

**Acceptance Criteria**:
- [ ] AC-2.1 (grok handoff) and AC-3.1: all seven live nodes pass. AC-2.4 and AC-5.4: the
  `task-tools` items. AC-5.1 and AC-5.7 (handoff).

**Mutation rows**: none. **Dependencies on other tasks**: Task 12

---

## Task 14: skill-md-routing

**Production file**: `h-mad/SKILL.md`, `handoff/SKILL.md`
**Test file**: `h-mad/tests/test_host_runtime_docs.py`
**Task shape**: `new-behaviour`

**Description**: Design §D11. In each file, the section located by
`find_heading(text, "## Host runtime")` has its first two sentences replaced by design §D11's
text. h-mad ends the grok clause "before bootstrap"; handoff says "before acting". Everything else
in both sections stays byte-identical. In `h-mad/SKILL.md`'s decision-routing section, located by
its full heading ``## Decision routing (for `/h-mad "<feature>"`)`` (the short form
`## Decision routing` makes `find_heading` return `None`; the full form returns `(14377, 2)`,
both executed at `a85abf7f`), the one row whose first cell is `` `cannot_judge` ``
(`grep -c '^| `cannot_judge`'` → 1 at `7e155451`) gains design §D11's "**Second cause:**"
sentence at the end of its second cell, before the closing ` |`. The row's opening text,
`` | `cannot_judge` | The state file EXISTS and could not be read ``, stays byte-identical: it is
`resume_decision_cannot_judge.json`'s anchor.

**Install-check and helper-registry edits** (design v1.3 §D11 §"The install-check contract",
items 1–7, in its order; Deviation 8; `h-mad/SKILL.md` only). Each edit adds text and keeps every
existing token, except that item 2 replaces the `SIBLING_NOT_SYMLINK` remedy cell as the design
prescribes (see item 2); no edited line is a committed mutation anchor except the
context-budget registry line, whose anchor `` - `h_mad_context_budget.py` — orchestrator context
budget `` (`context_budget_docs.json`, `drop-helper-from-list`) is its unchanged prefix. The new
text must add no catch-all hit: it has no PascalCase call, no backticked compound PascalCase, no
`CLAUDE` token, and its only Claude home path is the existing `~/.claude/skills` form, which
`claude-skills-dir` covers. The live registry node is the check.
1. In ``## First-run auto-bootstrap``, the bootstrap step that runs `h_mad_install_check.py` gains
   one sentence at its end: "The check also reads `~/.agents/skills` and
   `~/.gemini/config/skills` (override with `HMAD_AGENTS_SKILLS_DIR` and `HMAD_AGY_SKILLS_DIR`,
   or with `--agents-skills-dir` and `--agy-skills-dir`); a root that does not exist adds no
   line."
2. In the same section's remedy table, the `` `SIBLING_NOT_SYMLINK` `` row's remedy cell becomes:
   remove the copy and link the checkout's skill in its place, in the skills directory the line
   names, which is one of `~/.claude/skills`, `~/.agents/skills` or `~/.gemini/config/skills`
   (for example `rm -rf ~/.agents/skills/handoff` then
   `ln -s <checkout>/handoff ~/.agents/skills/handoff`). This is design §D11 item 2's "new
   remedy cell", so today's Claude-root command pair
   (`rm -rf ~/.claude/skills/<name>` then `ln -s <checkout>/<name> ~/.claude/skills/<name>`,
   `h-mad/SKILL.md:84` at `212aab9d`) is replaced, not kept beside the example: the new cell names
   `~/.claude/skills` as one of the three roots. No test reads the old pair
   (`grep -rn 'rm -rf ~/.claude/skills' h-mad/tests handoff/tests` → 0 matching lines at
   `212aab9d`). The design's "keeps every existing token" sentence and its item 2 disagree on this
   one cell; this plan follows item 2, the specific text (audit cycle 2, teammate nit 1).
3. The same table gains one row after `` `SIBLING_WRONG_CHECKOUT` ``: first cell
   `` `AGY_SIBLING_COLLISION` ``; second cell "a skill from this checkout that agy does not
   install (anything but `h-mad` and `handoff`) sits in `~/.gemini/config/skills` as a copy, a
   dangling link or another checkout's link; printed after the verdict and never changes it";
   third cell "none required: the operator decides whether that directory is theirs".
4. In ``## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)``, the
   `` - `h_mad_install_check.py` — `` line gains, at its end: "Also reads `~/.agents/skills` and
   `~/.gemini/config/skills` (`--agents-skills-dir` / `--agy-skills-dir`, env
   `HMAD_AGENTS_SKILLS_DIR` / `HMAD_AGY_SKILLS_DIR`); an empty value for either prints
   `INSTALL: UNREADABLE`, exit 2; in the agy root, a skill agy does not install prints an
   `AGY_SIBLING_COLLISION:` line after the verdict and never changes it."
5. The `` - `h_mad_context_budget.py` — `` line gains, at its end: "Under a declared non-Claude
   host it refuses before any transcript read: `HMAD_HOST` set to `codex`, `agy` or `grok` prints
   `CTXBUDGET: UNKNOWN reason=host_unsupported`, and any other value except empty or `claude`
   prints `reason=unknown_host` (see `h_mad_host.py`)."
6. A new line directly after the context-budget line: "- `h_mad_host.py` — host classifier:
   `classify_host()` reads `HMAD_HOST` and returns `claude` (unset, empty or `claude`), `declared`
   (`codex`, `agy` or `grok`) or `unknown` (any other value; no strip, no case fold). No CLI. Read
   by `h_mad_context_budget.py` and `h_mad_resume_decision.py`. Stdlib-only."
7. In ``## First-run auto-bootstrap``, the sentence before the remedy table ends "The detail
   lines each name one remedy, and all ten have one:" (`h-mad/SKILL.md:73` holds
   `detail lines each name one remedy, and all ten have one:` at `212aab9d`). Item 3 makes the
   table eleven rows, so the words "(the eleventh row, `AGY_SIBLING_COLLISION`, is a detail that
   needs none)" are inserted after "all ten have one", before the colon (design §D11 item 7).

**Tests** (24 new collected items):
- `test_host_runtime_names_every_adapter[h-mad-codex|h-mad-agy|h-mad-grok|handoff-codex|handoff-agy|handoff-grok]`
  (6). Each id is the skill, a hyphen, then the host, and each asserts that `references/<host>-runtime.md` is in the
  located section.
- `test_host_runtime_locator_fails_loudly[renamed|doubled]` (2). On in-memory copies of
  `h-mad/SKILL.md` with the heading renamed or doubled, `_section` raises `LookupError`.
- `test_cannot_judge_row_names_host_cause[hmad-host|session-id]` (2). The section is located with
  ``_section(text, '## Decision routing (for `/h-mad "<feature>"`)')``, the full heading. Exactly
  one line of it starts with ``| `cannot_judge` |``, and that line holds `HMAD_HOST` or
  `--session-id` respectively.
- `test_bootstrap_install_check_names_host_roots[agents-root|agy-root|agents-env|agy-env]` (4).
  In the section located by `## First-run auto-bootstrap`, the tokens `~/.agents/skills`,
  `~/.gemini/config/skills`, `HMAD_AGENTS_SKILLS_DIR` and `HMAD_AGY_SKILLS_DIR` respectively.
- `test_sibling_remedy_names_every_root[agents|agy]` (2). In the same section, exactly one line
  starts with ``| `SIBLING_NOT_SYMLINK` |``, and it holds `~/.agents/skills` or
  `~/.gemini/config/skills` respectively.
- `test_agy_collision_row_present` (1). In the same section, exactly one line starts with
  ``| `AGY_SIBLING_COLLISION` |``.
- `test_helper_registry_install_check_line[agents-option|agy-option|agy-collision]` (3). In the
  section located by ``## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)``, exactly one
  line starts with ``- `h_mad_install_check.py` —``, and it holds `--agents-skills-dir`,
  `--agy-skills-dir` or `AGY_SIBLING_COLLISION:` respectively.
- `test_helper_registry_budget_line[host-unsupported|unknown-host]` (2). In the same section,
  exactly one line starts with ``- `h_mad_context_budget.py` —``, and it holds
  `host_unsupported` or `unknown_host` respectively.
- `test_helper_registry_lists_h_mad_host` (1). In the same section, exactly one line starts with
  ``- `h_mad_host.py` —``, and it holds `HMAD_HOST`.
- `test_remedy_count_sentence_names_the_eleventh_row` (1). In the section located by
  `## First-run auto-bootstrap`, exactly one line contains `all ten have one`, and that line
  holds ``the eleventh row, `AGY_SIBLING_COLLISION` `` (design §D11 item 7, the node the design
  says the impl-plan owes).

6+2+2+4+2+1+3+2+1+1 = 24.

**Expected RED split**: 18 failing and 6 passing.
- The failures are the two `-grok` ids, both `test_cannot_judge_row_names_host_cause` ids, and
  the 14 install-check and helper-registry items (4+2+1+3+2+1+1). At `7e155451` the h-mad row
  holds neither `HMAD_HOST` nor `session-id`, and at `a85abf7f` `h-mad/SKILL.md` holds none of the
  Deviation-8 tokens (`grep -cF` → 0 lines each), so each of the first 13 fails on its assertion.
  The fourteenth fails on its assertion too: at `212aab9d` the one line holding
  `all ten have one` (`h-mad/SKILL.md:73`) does not hold `the eleventh row`. Both headings
  resolve at `a85abf7f` (`find_heading` → `(2052, 2)` and `(255565, 2)`, executed), so none fails
  on its locator.
- Passing now, and guards: the four codex/agy ids, because both sections already name
  `references/codex-runtime.md` and `references/agy-runtime.md` at `7e155451`, and the two locator
  ids. None of the six has a RED, so each gets a loss-of-behavior run as a Task 15 guard row in
  `host_runtime_docs.json` (Deviation 9): R1–R4 and L1–L2.

**Regression guards**: `test_live_registry_and_skill_files_are_clean` is the FR-4 re-run (AC-7.2):
the new text adds no `UNREGISTERED` hit. Also both `--check-anchors` commands (Convention 6),
because 74 committed rows anchor `SKILL.md` (`grep -rn '"file": "SKILL.md"'` over both spec
directories → 74 matching lines at `7e155451`), and `h-mad/tests/test_h_mad_codex_runtime.py`
and `handoff/tests/test_handoff_codex_runtime.py`, which assert `references/codex-runtime.md` in
each entrypoint.

**Acceptance Criteria**:
- [ ] AC-7.1: the six host-runtime ids. AC-7.2: the live registry node stays GREEN. AC-7.3: the
  locator ids. AC-9.4: the two cannot-judge ids.
- [ ] Axis-B "Skill manifest integrity" (design §D11 items 1–7, Deviation 8): the 14
  install-check and helper-registry nodes pass, and
  `h-mad/tests/test_h_mad_install_check_docs.py` passes unchanged (its fixed token tuples are not
  extended; that would edit an existing test).

**Mutation rows** (Task 15): guard rows R1–R4, L1 and L2 in `host_runtime_docs.json` — 6 rows.
**Dependencies on other tasks**: Task 13

---

## Task 15: mutation-specs-and-wire-reverts

**Production file**: none. Four new JSON specs:
`h-mad/tests/mutation-specs/host_parity.json`, `h-mad/tests/mutation-specs/host_declaration.json`,
`h-mad/tests/mutation-specs/install_check_roots.json` and
`h-mad/tests/mutation-specs/host_runtime_docs.json` (none exists at `212aab9d`).
**Test file**: none. The killing tests belong to Tasks 2–7 and 14.
**Task shape**: `operational`

**Description**: Author the four specs with exactly the 117 rows below. For each spec, read
`ANCHORS:` and then `MUTATION:` from:
```bash
for s in h-mad/tests/mutation-specs/host_parity.json h-mad/tests/mutation-specs/host_declaration.json h-mad/tests/mutation-specs/install_check_roots.json h-mad/tests/mutation-specs/host_runtime_docs.json; do
  env -u HMAD_HOST /opt/anaconda3/bin/python h-mad/scripts/h_mad_mutation_harness.py --check-anchors "$s"
  env -u HMAD_HOST /opt/anaconda3/bin/python h-mad/scripts/h_mad_mutation_harness.py "$s"
done
```
`env -u HMAD_HOST` keeps
an ambient host value out of the harness's pytest children: under a non-Claude `HMAD_HOST`,
FF2's killing test calls `decide()` in process and is red before any mutation.
- **Pass condition, per spec**: `ANCHORS_OK`, and `MUTATION: ALL_CAUGHT` with `crash_kills=0`.
  A crash kill does not count: that row is re-authored so its killing test fails on its assertion.
- `SURVIVED`, `REFUSED` or any other token halts, and is reported against the owning task.
- Afterwards, both directory-wide `--check-anchors` commands (Convention 6) must still print
  `ANCHORS_OK`, and `tests/test_h_mad_mutation_harness.py::test_committed_mutation_harness_anchor_sweep_is_ok`
  must pass in the full suite.

**`host_parity.json`**: file `tests/host_parity.py` (G7: `tests/test_host_construct_parity.py`);
`command` `["python3.11","-m","pytest","tests/test_host_construct_parity.py","-q"]`;
`target_command` `["python3.11","-m","pytest","-q"]`. For every design and split row, each `find`
is the whole line carrying the row's `# M:` tag,
including its indentation. For D07–D10 the find is the `# M:D07-D10` line, and for D31–D36 it is
the `# M:D31-D36` line: those rows share a find, and the harness applies one row at a time.

| Rows | replace | test |
|---|---|---|
| D01–D06, D11–D30, D37–D42 (32 rows) | the same indentation, then `pass` | `tests/test_host_construct_parity.py::test_kind_fixture_reports_exactly_its_pair[<the row's fixture id>]` |
| D07, D08, D09, D10 (4) | the line's own leading indentation, then `if key != "id": `, then the line with its leading indentation stripped; `"id"` is `"pattern"`, `"skills"` or `"description"` for D08, D09 and D10 respectively | the matching `[ru-missing-key-…]` id |
| D31–D36 (6) | the line's own leading indentation, then `if (cell_name, kind) != ("mapping", "no_alnum"): `, then the line with its leading indentation stripped; the pair is set per row to the row's `(cell, reason)` | the matching `[ce-…]` id |
| Sa, Sb, Sc, Sd-header, Se (5) | an `if` rule: its condition → `False`; a side-effect rule: `pass` | `tests/test_host_construct_parity.py::test_suppression_rule_leaves_one_pair[a]`, `[b]`, `[c]`, `[d]`, `[e]` respectively |
| Sd-missing (1) | its condition → `False` | `tests/test_host_construct_parity.py::test_kind_fixture_reports_exactly_its_pair[tm-no-heading]` |
| A1–A4 (4) | the empty string (the dict entry is dropped) | `tests/test_host_construct_parity.py::test_default_axes_report_each_fixture[A1]`, `[A2]`, `[A3]`, `[A4-tilde]` |
| B1–B3 (3) | the empty string | `…::test_default_axes_report_each_fixture[A4-tilde]`, `[A4-home]`, `[A4-home-braced]` |
| X-Error, X-Exception, X-Warning, X-Expired, X-Exit, X-Interrupt (6) | the tuple line with that suffix's string replaced by `".*"` | `tests/test_host_construct_parity.py::test_removed_exclusion_suffix_reports_its_fixture[<suffix>]` |
| E1 (1) | the same indentation, then `pass` | `tests/test_host_construct_parity.py::test_expand_branches_optional_group_adds_empty_alternative` |
| F1 (1) | `event.kind == "prose"` → `event.kind in ("prose", "body")` | `tests/test_host_construct_parity.py::test_fenced_pipe_table_is_not_the_table` |
| C1 (1) | `.lower()` removed | `tests/test_host_construct_parity.py::test_kind_fixture_reports_exactly_its_pair[ce-mapping-tbd]` |
| P1 (1) | the iteration over the checked elements → over every element | `tests/test_host_construct_parity.py::test_kind_fixture_reports_exactly_its_pair[ru-missing-key-pattern]` |
| K1 (1) | `_cell_id(cells[0])` → `cells[0].strip()` | `tests/test_host_construct_parity.py::test_kind_fixture_reports_exactly_its_pair[tmal-cell-count]` |

Guard rows (Deviation 9). Their `find` is the S8 or S9 line named, and `⏎` stands for a newline:

| Row | find | replace | test |
|---|---|---|---|
| G1 | `import json` | `import json⏎import subprocess` | `tests/test_host_construct_parity.py::test_host_parity_has_no_direct_launcher_import` |
| G2 | `import json` | `import json⏎import os⏎_LAUNCH = os.system` | `tests/test_host_construct_parity.py::test_host_parity_has_no_direct_launcher_import` |
| G3 | `import json` | `import json⏎import os⏎_LAUNCH = os.popen` | `tests/test_host_construct_parity.py::test_host_parity_has_no_direct_launcher_import` |
| G4 | `import json` | `import json⏎def _fence_scan(t):⏎    return t.startswith("#")` | `tests/test_host_construct_parity.py::test_host_parity_has_no_fence_scanner` |
| G5 | `import json` | `import json⏎_FENCE = "~~~"` | `tests/test_host_construct_parity.py::test_host_parity_has_no_fence_scanner` |
| G6 | `          exclusion_suffixes: Sequence[str] = EXCLUSION_SUFFIXES) -> ParityResult:` | the same line, then `⏎    __import__("subprocess").run(["codex"], timeout=60.0)` | `tests/test_host_construct_parity.py::test_gate_runs_no_host_cli` |
| G7 | the S9 line | the same line with `and not retired.get(i)` → `and i not in retired` | `tests/test_host_construct_parity.py::test_seed_check_honours_retirement[retired-empty-reason]` |

Each guard mutant is importable, so its kill is the named assertion, never a crash: G2 and G3
import `os` themselves; G6's call runs only inside `check()`, and under
`test_gate_runs_no_host_cli` the `PATH` put first resolves `codex` to the stub, which writes its
marker and exits 99, so the "no marker" assertion fails. The harness scores each row by its named
test alone (`scoring_command = target_command + [test]`, `h_mad_mutation_harness.py`, read at
`212aab9d`), so G6 never starts a real `codex`. G4 and G5 are two of `recognition_sites`'
recognised forms (a `startswith` call on a `#` literal; a string constant holding `~~~`), each
run alone. G1–G3 are the three launcher forms the source scan names, each run alone.

Rows: 32 + 4 + 6 + 5 + 1 + 4 + 3 + 6 + 1 + 1 + 1 + 1 + 1 = 66 design and split rows, plus 7 guard
rows = 73. The D rows are 32 + 4 + 6 = 42; the suppression rows are 5 + 1 = 6 (Deviation 3).

**`host_declaration.json`**: the row's `file` is given per row; `command`
`["python3.11","-m","pytest","tests/test_h_mad_host_declaration.py","tests/test_h_mad_context_budget.py","tests/test_h_mad_resume_decision.py","tests/test_h_mad_feature_lock.py","-q"]`;
`target_command` `["python3.11","-m","pytest","-q"]`. `⏎` stands for a newline.

| Row | file | find | replace | test |
|---|---|---|---|---|
| H1 | `scripts/h_mad_host.py` | `    value = env.get(HOST_ENV)` | `    value = env.get(HOST_ENV)⏎    value = value.strip() if value is not None else None` | `tests/test_h_mad_host_declaration.py::test_classify_host[space-grok]` |
| H2 | `scripts/h_mad_host.py` | `    value = env.get(HOST_ENV)` | `    value = env.get(HOST_ENV)⏎    value = value.lower() if value is not None else None` | `tests/test_h_mad_host_declaration.py::test_classify_host[Grok]` |
| H3 | `scripts/h_mad_host.py` | `    if value is None or value in ("", "claude"):` | `    if value is None or value == "claude":` | `tests/test_h_mad_host_declaration.py::test_classify_host[empty]` |
| W1a | `scripts/h_mad_context_budget.py` | reorder span A (below) | span A with the host block last | `tests/test_h_mad_host_declaration.py::test_budget_host_check_precedes_window_check[grok]` |
| W1b | `scripts/h_mad_context_budget.py` | reorder span B | span B with the host block last | `tests/test_h_mad_host_declaration.py::test_budget_host_check_precedes_transcript_lookup[grok]` |
| W1c | `scripts/h_mad_context_budget.py` | reorder span C | span C with the host block last | `tests/test_h_mad_host_declaration.py::test_budget_host_check_precedes_usage_read[grok]` |
| E1 | `scripts/h_mad_context_budget.py` | `        shown = host_value if re.fullmatch(r"[A-Za-z0-9._-]+", host_value) else json.dumps(host_value)` | `        shown = host_value` | `tests/test_h_mad_host_declaration.py::test_budget_unknown_host_encoding[space-grok]` |
| E2 | same | same | `        shown = json.dumps(host_value)` | `tests/test_h_mad_host_declaration.py::test_budget_unknown_host_encoding[zzz]` |
| E3 | same | `re.fullmatch(r"[A-Za-z0-9._-]+", host_value)` | `re.match(r"^[A-Za-z0-9._-]+$", host_value)` | `tests/test_h_mad_host_declaration.py::test_budget_unknown_host_encoding[zzz-newline]` |
| WR1 | `scripts/h_mad_context_budget.py` | `    host_class, host_value = classify_host()` | `    host_class, host_value = "claude", None` | `tests/test_h_mad_host_declaration.py::test_budget_host_unsupported_valid_transcript[grok]` |
| FF1 | `scripts/h_mad_context_budget.py` | `    if host_class == "declared":` | `    if True:` | `tests/test_h_mad_context_budget.py::TestVerdict::test_ok_below_the_ceiling` |
| W2a | `scripts/h_mad_resume_decision.py` | reorder span D | span D with the host check last | `tests/test_h_mad_host_declaration.py::test_decide_cannot_judge_without_session_id[grok-absent-file]` |
| W2b | `scripts/h_mad_resume_decision.py` | reorder span E | span E with the host check last | `tests/test_h_mad_host_declaration.py::test_decide_cannot_judge_without_session_id[grok-absent-feature]` |
| V1 | `scripts/h_mad_resume_decision.py` | `    if host_class == "claude" or session_id:` | `    if host_class == "claude":` | `tests/test_h_mad_host_declaration.py::test_decide_routes_normally_with_session_id[grok]` |
| V2 | `scripts/h_mad_resume_decision.py` | `    return CANNOT_JUDGE_WITHOUT_SESSION` | `    return None` | `tests/test_h_mad_host_declaration.py::test_decide_cannot_judge_without_session_id[grok-no-owner]` |
| WR2 | `scripts/h_mad_resume_decision.py` | the three-line check of Task 6, with its trailing newline | the empty string | `tests/test_h_mad_host_declaration.py::test_decide_cannot_judge_without_session_id[grok-no-owner]` |
| FF2 | `scripts/h_mad_resume_decision.py` | `    if host_class == "claude" or session_id:` | `    if session_id:` | `tests/test_h_mad_feature_lock.py::TestResumeDecisionSurfacesOwnership::test_no_session_id_preserves_legacy_behaviour` |
| HE1 | `tests/conftest.py` | `               if not k.startswith("CLAUDE") and k not in _AMBIENT_HOST_KEYS}` | `               if k not in _AMBIENT_HOST_KEYS}` | `tests/test_h_mad_host_declaration.py::test_hermetic_env_drops_claude_names_and_backend` |
| HE2 | `tests/conftest.py` | `_AMBIENT_HOST_KEYS = ("HPW_AGENT_BACKEND", "HMAD_HOST", "HMAD_CONTEXT_WINDOW")` | `_AMBIENT_HOST_KEYS = ("HMAD_HOST", "HMAD_CONTEXT_WINDOW")` | `tests/test_h_mad_host_declaration.py::test_hermetic_env_drops_claude_names_and_backend` |
| HE3 | `tests/conftest.py` | same as HE2 | `_AMBIENT_HOST_KEYS = ("HPW_AGENT_BACKEND", "HMAD_CONTEXT_WINDOW")` | `tests/test_h_mad_host_declaration.py::test_hermetic_env_drops_claude_names_and_backend` |
| HE4 | `tests/conftest.py` | same as HE2 | `_AMBIENT_HOST_KEYS = ("HPW_AGENT_BACKEND", "HMAD_HOST")` | `tests/test_h_mad_host_declaration.py::test_hermetic_env_drops_claude_names_and_backend` |
| AG-unset | `scripts/h_mad_resume_decision.py` | as FF2 | as FF2 | `tests/test_h_mad_host_declaration.py::test_budget_and_decide_agree[unset]` |
| AG-empty | `scripts/h_mad_resume_decision.py` | as FF2 | as FF2 | `tests/test_h_mad_host_declaration.py::test_budget_and_decide_agree[empty]` |
| AG-claude | `scripts/h_mad_resume_decision.py` | as FF2 | as FF2 | `tests/test_h_mad_host_declaration.py::test_budget_and_decide_agree[claude]` |

The E rows in this spec (E1–E3) are separate from `host_parity.json`'s E1: each row's `name` key
carries its spec, so they never collide. The reorder spans, each measured on the landed file:
- **Span A** runs from `    host_class, host_value = classify_host()` through the `        return 2`
  that closes the `reason=bad_window` block.
- **Span B** runs from the same first line through the `        return 2` that closes the
  `reason=no_transcript` block.
- **Span C** runs through the `        return 2` that closes the `reason=no_usage` block.
- **Span D** runs from `    host_verdict = _host_verdict(session_id)` through
  `        return "start_fresh"` directly after `    if not state_file.is_file():`.
- **Span E** runs from the same first line through the `        return "start_fresh"` directly after
  `    if not feat_state:`.

Each `replace` holds the same lines with the host block (10 lines, Task 5) or the host check
(3 lines, Task 6) moved to the end. The self-check, run before scoring:
`sorted(find.splitlines()) == sorted(replace.splitlines())`, and `find` occurs exactly once in its
file. HE1 keeps every `CLAUDE*` name, so the test's `CLAUDE_ZZZ_PROBE`/`CLAUDECODE` absence
assertion fails; HE2, HE3 and HE4 each keep one of `HPW_AGENT_BACKEND`, `HMAD_HOST` and
`HMAD_CONTEXT_WINDOW`, which the test monkeypatches in and asserts absent, each member alone.
Rows: 3 + 3 + 3 + 1 + 1 + 2 + 1 + 1 + 1 + 1 + 4 + 3 = 24. That is 13 design members (H1–H3,
W1a–W1c, W2a–W2b, V1, V2, E1–E3), 4 wire rows (WR1, FF1, WR2, FF2) and 7 guard rows (HE1–HE4,
AG-unset, AG-empty, AG-claude).

**`install_check_roots.json`**: file `scripts/h_mad_install_check.py`; `command`
`["python3.11","-m","pytest","tests/test_h_mad_install_check_roots.py","tests/test_h_mad_install_check.py","-q"]`;
`target_command` `["python3.11","-m","pytest","-q"]`.

| Row | find | replace | test |
|---|---|---|---|
| I1 | `        if owner is None or owner[0] in installed_set:` | `        if owner is None or owner[0] not in installed_set:` | `tests/test_h_mad_install_check_roots.py::test_agy_root_cell[debugger-copy]` |
| I2 | `        issues += check_siblings(sibling_repo, skills_link.parent)` | `        issues += split_agy_root(check_siblings(sibling_repo, skills_link.parent), skills_link.parent, checkout_skill_names(sibling_repo), AGY_INSTALLED_NAMES)[0]` | `tests/test_h_mad_install_check_roots.py::test_claude_root_debugger_copy_still_fails` |
| I3a | `    agents = env[AGENTS_SKILLS_ENV] if AGENTS_SKILLS_ENV in env else str(home / ".agents" / "skills")` | `    agents = str(home / ".agents" / "skills")` | `tests/test_h_mad_install_check_roots.py::test_env_override_is_read[agents]` |
| I3b | `    agy = env[AGY_SKILLS_ENV] if AGY_SKILLS_ENV in env else str(home / ".gemini" / "config" / "skills")` | `    agy = str(home / ".gemini" / "config" / "skills")` | `tests/test_h_mad_install_check_roots.py::test_env_override_is_read[agy]` |
| I4a | `env[AGENTS_SKILLS_ENV] if AGENTS_SKILLS_ENV in env else` | `env[AGENTS_SKILLS_ENV] if env.get(AGENTS_SKILLS_ENV) else` | `tests/test_h_mad_install_check_roots.py::test_empty_env_override_is_unreadable[agents]` |
| I4b | `env[AGY_SKILLS_ENV] if AGY_SKILLS_ENV in env else` | `env[AGY_SKILLS_ENV] if env.get(AGY_SKILLS_ENV) else` | `tests/test_h_mad_install_check_roots.py::test_empty_env_override_is_unreadable[agy]` |
| I5a | `    agents_dir = args.agents_skills_dir if args.agents_skills_dir is not None else default_agents` | `    agents_dir = os.environ[AGENTS_SKILLS_ENV] if AGENTS_SKILLS_ENV in os.environ else (args.agents_skills_dir if args.agents_skills_dir is not None else default_agents)` | `tests/test_h_mad_install_check_roots.py::test_explicit_option_beats_env_override[agents]` |
| I5b | `    agy_dir = args.agy_skills_dir if args.agy_skills_dir is not None else default_agy` | `    agy_dir = os.environ[AGY_SKILLS_ENV] if AGY_SKILLS_ENV in os.environ else (args.agy_skills_dir if args.agy_skills_dir is not None else default_agy)` | `tests/test_h_mad_install_check_roots.py::test_explicit_option_beats_env_override[agy]` |
| I6 | `if line.startswith(f"SIBLING_{kind}:{skills_dir / name} "))` | `if line.startswith(f"SIBLING_{kind}:{skills_dir / name}"))` | `tests/test_h_mad_install_check_roots.py::test_split_prefix_does_not_capture_a_longer_name` |
| I7 | `    if issues:⏎        print(f"INSTALL: FAIL issues={len(issues)}")` | `    for line in details:⏎        print(line)⏎    if issues:⏎        print(f"INSTALL: FAIL issues={len(issues)}")` | `tests/test_h_mad_install_check_roots.py::test_detail_lines_sorted_and_after_verdict` |
| WR3a | `        agents_skills_dir=agents_dir,⏎` | the empty string | `tests/test_h_mad_install_check_roots.py::test_agents_root[copy]` |
| WR3b | `        agy_skills_dir=agy_dir,⏎` | the empty string | `tests/test_h_mad_install_check_roots.py::test_agy_root_cell[h-mad-copy]` |
| FF3a | `        if agents_skills_dir is not None:` | `        agents_skills_dir = agents_skills_dir if agents_skills_dir is not None else os.environ.get(AGENTS_SKILLS_ENV)⏎        if agents_skills_dir is not None:` | `tests/test_h_mad_install_check_roots.py::test_check_without_root_keywords_reads_no_new_root` |
| FF3b | `        if agy_skills_dir is not None:` | `        agy_skills_dir = agy_skills_dir if agy_skills_dir is not None else os.environ.get(AGY_SKILLS_ENV)⏎        if agy_skills_dir is not None:` | `tests/test_h_mad_install_check_roots.py::test_check_without_root_keywords_reads_no_new_root` |

Rows: 10 design members (I1, I2, I3a, I3b, I4a, I4b, I5a, I5b, I6, I7) and 4 wire rows (WR3a,
WR3b, FF3a, FF3b) = 14. FF3a and FF3b re-contain their `find`, which the harness reports as a
self-matching advisory, never a refusal (`h_mad_mutation_harness.py`, `SELF_MATCHING_NOTE`); the
killing test asserts a return value, not text containment, so the advisory does not apply.

**`host_runtime_docs.json`** (guard rows of Task 14, Deviation 9): `root` `"../.."`; `command`
`["python3.11","-m","pytest","tests/test_host_runtime_docs.py","-q"]`; `target_command`
`["python3.11","-m","pytest","-q"]`. The `file` is per row. `../handoff/SKILL.md` is the first
`file` in either spec directory to leave the `h-mad/` root (`grep -ln '"file": "\.\./'` over both
directories → 0 files at `212aab9d`). The harness resolves it as `(root / file).resolve()` with no
containment check (`h_mad_mutation_harness.py`, `--check-anchors` and run paths, read at
`212aab9d`), and a scratch spec holding rows R2 and R3 against the tree at `212aab9d` printed
`ANCHORS: ANCHORS_OK specs=1 mutations=2 ok=2 drifted=0`; the scratch spec was deleted.

| Row | file | find | replace | test |
|---|---|---|---|---|
| R1 | `SKILL.md` | `[references/codex-runtime.md](references/codex-runtime.md)` | `the codex adapter` | `tests/test_host_runtime_docs.py::test_host_runtime_names_every_adapter[h-mad-codex]` |
| R2 | `SKILL.md` | `[references/agy-runtime.md](references/agy-runtime.md)` | `the agy adapter` | `tests/test_host_runtime_docs.py::test_host_runtime_names_every_adapter[h-mad-agy]` |
| R3 | `../handoff/SKILL.md` | `[references/codex-runtime.md](references/codex-runtime.md)` | `the codex adapter` | `tests/test_host_runtime_docs.py::test_host_runtime_names_every_adapter[handoff-codex]` |
| R4 | `../handoff/SKILL.md` | `[references/agy-runtime.md](references/agy-runtime.md)` | `the agy adapter` | `tests/test_host_runtime_docs.py::test_host_runtime_names_every_adapter[handoff-agy]` |
| L1 | `tests/test_host_runtime_docs.py` | the `# M:L1` line of Task 8's `_section` | the same indentation, then `return ""` | `tests/test_host_runtime_docs.py::test_host_runtime_locator_fails_loudly[renamed]` |
| L2 | `tests/test_host_runtime_docs.py` | the `# M:L2` line | the same indentation, then `return ""` | `tests/test_host_runtime_docs.py::test_host_runtime_locator_fails_loudly[doubled]` |

Each R `find` occurs exactly once in its file, and in each file both occurrences of the path are
inside that one link, so the mutant leaves the path nowhere in the file (at `212aab9d`:
`grep -oF` → 1 link occurrence and 2 path occurrences in each of the four file × host pairs;
design §D11's new first sentences keep the same link form). L1 and L2 turn the raise into a
return, so the `pytest.raises(LookupError)` check fails with `DID NOT RAISE`, whose pytest footer
names `Failed`, which the harness's crash classifier (`_PYTEST_FOOTER`, `(?:Error|Exception)$`)
does not count as a crash. Rows: 4 + 2 = 6.

**Total**: 73 + 24 + 14 + 6 = 117, matching the per-task attributions: Task 2 73, Task 4 7,
Task 5 8, Task 6 9, Task 7 14, Task 14 6 (73 + 7 + 8 + 9 + 14 + 6 = 117). By kind: 88 design
members, 1 split row, 8 wire rows and 20 guard rows (Deviation 3).

**Acceptance Criteria**:
- [ ] Every guard is mutation-verified (plan Success Criteria): all four specs print
  `ALL_CAUGHT` with `crash_kills=0`. That includes the 20 guard rows, each the loss-of-behavior
  run of a guard that is green before its task's change or has no RED of its own (Deviation 9).
- [ ] W1–W3 each fail their WIRE-PIN under the wire-scoped revert (WR1, WR2, WR3a, WR3b), and each
  force-fire fails its named test by assertion (FF1, FF2, FF3a, FF3b).

**Dependencies on other tasks**: Task 14 (every killing test file must be GREEN for the harness's
baseline)

---

## Task 16: byte-identity-probe

**Production file**: `docs/03-analysis/probes/multi-host-runtime/byte_identity.py` (new)
**Test file**: none (a committed probe, verified by its own runs below)
**Task shape**: `gate` (authors a committed measurement probe and runs it; writes no h-mad file)

**Description**: Design §D8's `byte_identity.py` row and plan §"Regression is proven against the
base". The CLI is `byte_identity.py --base SHA --arm {budget,decision,install-a,install-b}`. It
checks out `SHA` with `git worktree add --detach` into a `tempfile.mkdtemp()` directory. It runs
each case against both trees with `subprocess.run(..., timeout=60.0)`. It removes the worktree
with `git worktree remove --force`, then re-reads `git worktree list --porcelain`; if the path is
still listed, it prints `BYTE-IDENTITY: UNREADABLE reason=worktree_left`.
- **Child environment**: `os.environ` without every `^CLAUDE` key, `HPW_AGENT_BACKEND`,
  `HMAD_HOST` and `HMAD_CONTEXT_WINDOW` (the Convention 3 rule), plus each case's own settings.
- **Output**: one of three forms, shown here with example values:
  `BYTE-IDENTITY: PASS arm=budget cases=14`;
  `BYTE-IDENTITY: FAIL arm=budget case=run-ok-unset`, followed by a unified diff of stdout and the
  two exit codes; or `BYTE-IDENTITY: UNREADABLE reason=links_absent` (exit 2). The UNREADABLE
  reasons are `links_absent`, `worktree_left`, `bad_base` and `worktree_add_failed`.
- **Case names**:
  - budget: `ok-advisor`, `deny-advisor`, `run-ok`, `run-halt`, `window-zero`,
    `missing-transcript` (`HOME` an empty temp dir) and `no-usage`, each run as `-unset` then
    `-claude`: 7 × 2 = 14 cases. The two advisor cases pass **no** `--mode` (advisor is the
    default at both trees); the two run cases pass `--mode run`. Cases run in exactly the listed
    order, and `FAIL` names the **first** failing case in that order;
  - decision: `absent-file`, `unreadable-file`, `absent-feature`, `foreign-owner-with-id`,
    `foreign-owner-without-id`, `halted`, `complete`, `lcp-4` and `lcp-1`, each `-unset` then
    `-claude`: 9 × 2 = 18;
  - install-a: `healthy`, `stale-copy`, `missing-hook`, `split`, `dangling`, `absent-link`,
    `sibling-copy`, `sibling-other-checkout` and `empty-path`, with both root variables at absent
    paths: 9;
  - install-b: the precondition `test -L` on the four links, resolved under `Path.home()` (so
    under the `HOME` the probe runs with), else
    `BYTE-IDENTITY: UNREADABLE reason=links_absent`. Then B1 (the 9 install-a argvs at the real
    defaults) and B2 (`--skills-link ~/.claude/skills/h-mad --repo /Users/kimhawk/orca/skills`),
    compared by the plan's closed-diff rule. The probe expands the tilde itself: B2's argv holds
    `str(Path.home() / ".claude" / "skills" / "h-mad")`, never the two characters `~/`, because
    `subprocess.run` with an argv list starts no shell and `h_mad_install_check.py` builds
    `Path(args.skills_link)` with no `expanduser` (line 196 at `212aab9d`), so a literal `~` would
    check a relative path under the child's cwd (audit cycle 2, codex should 1). The same rule
    holds for every other path the probe passes. The `AGY_SIBLING_COLLISION:` names are taken from
    the plan P8 `comm -12` reading run inside the probe: 10 cases.

**Author**: codex (§Preamble), because `byte_identity.py` is a non-test `.py`.

**Runs in this task**, which are this probe's verification. Phase 6 re-runs them for its record.
Each is `/opt/anaconda3/bin/python docs/03-analysis/probes/multi-host-runtime/byte_identity.py`
with the arguments shown, run in one shell after the §Preamble `BASE_SHA` block.
1. `--base "$BASE_SHA" --arm budget` → `BYTE-IDENTITY: PASS arm=budget cases=14`.
2. `--base "$BASE_SHA" --arm decision` → `PASS arm=decision cases=18`.
3. `--base "$BASE_SHA" --arm install-a` → `PASS arm=install-a cases=9`.
4. `--base "$BASE_SHA" --arm install-b` → `BYTE-IDENTITY: PASS arm=install-b cases=10`. The four
   links exist by now: Task 1's four-link gate halts 5c until the operator creates them, so no
   run reaches this task without them. If this run prints
   `BYTE-IDENTITY: UNREADABLE reason=links_absent`, the links were removed after Task 1, and the
   task halts to the operator; it never prints `PASS` without them.
5. **Negative control, links**: `env HOME=<an empty scratch directory>` in front of run 4's
   command → `BYTE-IDENTITY: UNREADABLE reason=links_absent`, exit 2. The scratch directory is
   made in the session scratchpad and deleted after the run.
6. **Negative control, budget**: `--base 9df441ca --arm budget` →
   `BYTE-IDENTITY: FAIL arm=budget case=run-ok-unset`. `9df441ca` is `a467ee57^`, the commit
   before `h_mad_context_budget.py` gained `--mode` (`git show 9df441ca:h-mad/scripts/h_mad_context_budget.py | grep -c -- '--mode'`
   → 0 matching lines at `7e155451`), so its `run-ok` case exits 2 with a usage error. The two
   advisor cases before it pass, because they pass no `--mode`: a probe at `a85abf7f` ran the
   `9df441ca` script and the current one with `--transcript` only, on a one-turn transcript of
   1,010 and of 150,010 tokens, and both printed the same line
   (`CTXBUDGET: OK used=1010 window=1000000 pct=0.1 projected=2020 ceiling=45`, and the
   `used=150010` line), rc 0; `--mode run` at `9df441ca` printed
   `error: unrecognized arguments: --mode run`. The probe was deleted.
7. After each run, `git worktree list --porcelain` names no temp path.

**Acceptance Criteria**:
- [ ] AC-8.3 (probe half), AC-10.2 (second clause) and AC-12.2 (arm A): runs 1–3 print `PASS`.
  AC-12.2 arm B: run 4 prints `PASS`; Phase 6 re-runs it for its record.
- [ ] Negative control 5 prints `UNREADABLE reason=links_absent`, and negative control 6 prints
  `FAIL` at the named case.

**Mutation rows**: none. **Dependencies on other tasks**: Task 15

---

## Task 17: smoke-assertions-and-rehearsal

**Production file**: `docs/03-analysis/probes/multi-host-runtime/smoke_assert.py` (new),
`docs/03-analysis/probes/multi-host-runtime/rehearsal/` (new: `cases.json` plus one log file per
case)
**Test file**: none (verified by `smoke_assert.py rehearse`)
**Task shape**: `gate` (authors a committed measurement probe and its rehearsal fixtures; writes no h-mad file)
**Author**: codex (§Preamble), because `smoke_assert.py` is a non-test `.py`.

**Description**: Design §D10, which is binding in full: verdict tokens, the per-host log table,
the tokenizer (`shlex.shlex(text, posix=True, punctuation_chars=";&|<>()\n")`, whitespace
`" \t\r"`, `whitespace_split = True`, `commenters = ""`), the command classes, the mention regex,
the "which files count" rule, the needle rule, and verdict steps 1–6. `v112` is the plan's logic
moved into Python. `rehearse` reads `rehearsal/cases.json`: each case names its host, its log, its
`--root` (the checkout) and its exact expected stdout line. It prints one line per case, then
`REHEARSAL: PASS n=N` or `REHEARSAL: FAIL`.
- **Grok fixtures** copy the first `available_commands` line of
  `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson` verbatim, with
  `grep -m1 '"type": *"available_commands"'`. That file is present at `7e155451`. The `read_file`
  events copy that log's shape with only the path changed.

**Rehearsal cases** (92):
- per host (`codex`, `agy`, `grok`): R1, R2, R3, R4, R6 × 4, R7 × 2, R8, R9, R10, R11, R12 × 2,
  R13 × 3, R14 × 8 and R15, that is 1+1+1+1+4+2+1+1+1+1+2+3+8+1 = 28, so 84 over three hosts;
- grok R5: 1;
- `v112`: 4 (a correct line; a wrong `halt_reason`; a non-null value where the record holds
  `null`; two `HMAD-STATUS` lines);
- replays of the three committed real logs: 3. The sibling grok probe log is predicted
  `FAIL V-11.1 no adapter read`; `plan-audit-v1-p2-agy.log` is predicted
  `FAIL V-11.1 a script ran before the adapter was read`; `h-mad/tests/fixtures/codex-text-8-exec.log`
  (8 lines equal to `exec` at `7e155451`) is predicted `FAIL V-11.1 no adapter read`.

84 + 1 + 4 + 3 = 92.

**Verification in this task**:
- `/opt/anaconda3/bin/python docs/03-analysis/probes/multi-host-runtime/smoke_assert.py rehearse` →
  `REHEARSAL: PASS n=92`. A replay that prints anything but its prediction is investigated
  (design §D10): the finding says whether the classifier or the prediction is wrong.
- **R14(a), in design v1.3's form** (erratum item 2; the v1.1 halt is removed). The case tests
  that a `#` never hides the separator after it or the command after that (`commenters = ""`).
  The separator differs by host, and every host's expected line is
  `FAIL V-11.1 a script ran before the adapter was read`:
  - **codex**: `; ` on one line. The command line after `exec` in the fixture log is exactly
    `/bin/zsh -lc "echo x # c; python3 h-mad/scripts/h_mad_state_write.py" in /Users/kimhawk/orca/skills`,
    one physical line, holding no newline inside the command and no two-character backslash-n.
    Byte check before the run: `grep -c 'echo x # c; python3 h-mad/scripts/h_mad_state_write.py' <the codex R14(a) log>`
    → 1 matching line. The design's shape check on that line
    (`re.match(r'^\S+ -lc .* in \S+$', line)`) is `True`, and the v1.2 two-line form's first line
    is `False` (design v1.3 Version History, executed there at `a1478ad3`). What the codex form
    gives up is stated in design §D10: a real shell would treat `# c; …` as a comment, so the
    codex case tests the tokenizer setting, not shell fidelity;
  - **grok and agy**: a newline. The command is a JSON string, so the fixture writes `\n` inside
    the JSON string and it decodes to a real newline.

  With `commenters = "#"` the codex form yields `echo x` alone and the newline form yields
  `echo x python3 h-mad/scripts/h_mad_state_write.py` (design v1.3's tokenizer control, re-executed
  at `212aab9d` with the §D10 `shlex` settings: token lists `['echo', 'x']` and
  `['echo', 'x', 'python3', 'h-mad/scripts/h_mad_state_write.py']`; with `commenters = ""` both
  forms keep the separator and the run). So under a `#` commenter no script run is classified on
  any host, and each host's case prints a line other than its expected `FAIL`. The reader is
  unchanged and the case count stays 92.
- **Control**: `v111 --host codex --log <R1 log> --root <scratch copy of the checkout whose h-mad/references/codex-runtime.md has no line starting "# ">`
  → `UNREADABLE V-11.1 reason=no_needle`, exit 2. The scratch copy is made in the session
  scratchpad and deleted.

**Acceptance Criteria**:
- [ ] Every case prints its expected line. `REHEARSAL: PASS n=92`.

**Mutation rows**: none. **Dependencies on other tasks**: Task 14 (the rehearsal reads the real
adapters' and `SKILL.md`'s first headings from `--root`)

---

## Task 18: coupled-suite-gate

**Production file**: none
**Test file**: none
**Task shape**: `gate`

**Description**: The pre-merge Phase-5 gate (plan §Success Criteria). Read every token; never read
`$?`.
1. **AC-12.1**: `env -u HMAD_HOST /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts`
   → no `failed` and no `error`. If
   `test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`
   still fails, AC-12.1 is not met, 7f does not run, and the orchestrator halts to the operator
   naming that node (plan: not waived).
2. The same command with `CLAUDE_ZZZ_PROBE=1` exported → the same summary.
3. **AC-8.3**: the two module runs of Task 5, spelled exactly as there (`/opt/anaconda3/bin/python`,
   never bare `python3`), which must show equal `passed` counts.
4. **Node-id floor**: collect at HEAD with Task 1's command into a temp file, then
   `comm -23 "$(git rev-parse --absolute-git-dir)/hmad-mhr-base-nodeids.txt" <head file>` must
   print nothing.
5. **Append-only** (in one shell after the §Preamble `BASE_SHA` block):
   `git diff --numstat "$BASE_SHA" -- h-mad/tests/conftest.py` shows `0` deleted.
   No other pre-existing test file is touched: `git diff --name-only "$BASE_SHA" -- h-mad/tests handoff/tests handoff/scripts`
   lists only this plan's new files and `conftest.py`.
6. **Anchors**: both `--check-anchors` commands → `ANCHORS_OK drifted=0`.
7. **Wire-pin gate**: `/opt/anaconda3/bin/python h-mad/scripts/h_mad_wire_pin_gate.py --feature multi-host-runtime docs/01-plan/features/multi-host-runtime.impl-plan.md`
   → `WIREPIN: PASS`.

**Acceptance Criteria**:
- [ ] AC-12.1: item 1. AC-8.3: item 3. FR-12's node-id floor and append-only rule: items 4 and 5.

**Mutation rows**: none. **Dependencies on other tasks**: Task 15, Task 16, Task 17

---

## After Phase 5 (not tasks)

- **Phase 6** (design Implementation Order step 9) runs `byte_identity.py` over all four arms,
  `smoke_assert.py rehearse`, the calibration re-run at 5g, and writes the analysis document:
  AC-4.5, AC-4.6, AC-6.1, the branch classification, the byte-identity reading and the rehearsal
  record. Arm B and the Phase-7 smoke need the four operator links. While they are absent, each
  halts to the operator and never passes.
- **Phase 7** follows the plan's sequence, with the smoke delta of design §D10 and the archive step
  of design §"When the smoke record is archived".

## AC coverage

| AC | Task · owner |
|---|---|
| AC-1.1 | Task 2, D02, D07–D10, D12, D14–D17; Task 3, live registry node |
| AC-1.2 | Task 3, `test_registry_holds_every_seed_id` |
| AC-2.1 | Tasks 8–13, `test_live_adapter_is_clean[…]` |
| AC-2.2 | Tasks 8–13, live nodes (`CELL_EMPTY`) and `test_not_applicable_rows_state_a_reason[…]` |
| AC-2.3 | Tasks 8–10, `test_advisor_row` |
| AC-2.4 | Tasks 11–13, `test_task_tools_row` |
| AC-2.5 | Tasks 8–10, `test_session_id_env_row` |
| AC-3.1 | Task 13 onward: all seven live nodes pass |
| AC-3.2 | Task 2, `[row-missing]` |
| AC-3.3 | Task 2, the 42 fixtures, the clean baseline and five suppression nodes |
| AC-3.4 | Task 2, `[stale-entry]`, `[undeclared-skill]` |
| AC-3.5 | Task 2, `test_gate_runs_no_host_cli` with its stub control |
| AC-4.1 | Task 3 and Task 14, `test_live_registry_and_skill_files_are_clean` |
| AC-4.2 | Task 2, axis-alone, removal and default-axes nodes |
| AC-4.3 | Task 2, the two suffix tests |
| AC-4.4 | Task 2, `test_unregistered_teamcreate_then_registered_passes` |
| AC-4.5 | Task 0 reading; the Phase-6 document |
| AC-4.6 | Task 1 record; the Phase-6 document |
| AC-5.1 | Tasks 10 and 13, `test_version_and_compatibility` |
| AC-5.2 | Task 10, `test_tdd_gate_section` |
| AC-5.3 | Task 10, `test_advisor_row[h-mad-grok-…]` |
| AC-5.4 | Task 13, `test_task_tools_row[handoff-grok-…]` |
| AC-5.5 | Task 10, `test_session_id_env_row[h-mad-grok-…]`, `test_grok_session_id_condition` |
| AC-5.6 | Task 10, `test_claude_projects_store_row` |
| AC-5.7 | Tasks 10 and 13, `test_grok_source_cells_format` |
| AC-6.1 | Task 1 gap table; the Phase-6 document |
| AC-6.2 | Tasks 8, 9, 11 and 12, live nodes |
| AC-6.3 | Tasks 8 and 9, `test_advisor_row` |
| AC-6.4 | Tasks 11 and 12, `test_task_tools_row` |
| AC-6.5 | Tasks 8 and 9, `test_session_id_env_row` |
| AC-6.6 | the existing `test_h_mad_codex_runtime.py` and `test_handoff_codex_runtime.py`, per task |
| AC-7.1 | Task 14, `test_host_runtime_names_every_adapter` |
| AC-7.2 | Task 14, the live registry node re-run |
| AC-7.3 | Task 14, `test_host_runtime_locator_fails_loudly` |
| AC-8.1 | Task 5, `test_budget_host_unsupported_valid_transcript`; Tasks 8–10, `test_budget_line_runs_and_reports_host` |
| AC-8.2 | Task 5, `test_budget_unknown_host_encoding` |
| AC-8.3 | Task 5 and Task 18 double run; Task 16 budget arm |
| AC-8.4 | Tasks 8–10, `test_context_budget_section` |
| AC-8.5 | Task 5, `test_budget_host_check_precedes_window_check`, `test_budget_unknown_host_precedes_window_check[zzz]` |
| AC-9.1 | Task 6, `test_decide_cannot_judge_without_session_id`, `test_decide_unknown_host_without_session_id`, `test_decide_empty_session_id_is_no_id` |
| AC-9.2 | the existing `test_h_mad_resume_decision.py` and `test_h_mad_feature_lock.py` |
| AC-9.3 | Tasks 8–10, `test_claims_section_fenced_lines`, `test_claims_lines_execute_across_invocations`; Task 10, `test_grok_session_id_condition` |
| AC-9.4 | Task 14, `test_cannot_judge_row_names_host_cause` |
| AC-10.1 | Task 7, `test_agents_root` |
| AC-10.2 | the existing `test_h_mad_install_check.py`; Task 7, `test_absent_roots_add_no_line`; Task 16, install-a |
| AC-10.3 | Task 7, the empty-option, empty-env and option-over-env tests |
| AC-10.4 | Tasks 8–10, `test_install_section` |
| AC-10.5 | Task 7, `test_agy_root_cell` |
| AC-10.6 | Task 7, `test_claude_root_debugger_copy_still_fails`, and the existing `TestSiblingSkills` |
| AC-12.1 | Task 18 |
| AC-12.2 | Task 16 (arm A, runs 1–3; arm B, run 4); Phase 6 re-runs both |

51 rows, one per spec AC id (`grep -oE '^ *- AC-[0-9]+\.[0-9]+'` over the spec, then `sort -u` →
51 distinct ids at `7e155451`). V-11.1 to V-11.5 are owned by the Phase-7 live-smoke record.

## Version History
- v1.2 (2026-09-28): corrective revision after the 5b audit round cap, answering impl-plan audit cycle 2 (codex `audit.v2.p1`: 3 must, 2 should; teammate `audit.v2.teammate`: 1 must, 5 should, 4 nit) and propagating design v1.3; premises re-read at `212aab9d`. Design v1.3 item 1 → Deviation 7 resolved (Task 0 is the first commit after the 5c impl-plan commit; new Task 0 AC that the reading is committed before Task 1). Design v1.3 item 2 → Task 17's R14(a) halt removed; codex fixture `; ` on one line, grok/agy newline, all three expect `FAIL V-11.1 a script ran before the adapter was read`; regex and tokenizer controls re-executed. Design v1.3 item 3 → Deviation 8 resolved against §D11 items 1–7; Task 14 gains edit 7 and `test_remedy_count_sentence_names_the_eleventh_row` (Task 14: 24 items, RED 18/6). codex M1 and teammate S4 → fixed by design v1.3 (Deviation 7). codex M2 and teammate M1 → fixed by design v1.3 (Task 17). codex M3 → fixed: Deviation 9, 20 guard rows (G1–G7, HE1–HE4, AG ×3, R1–R4, L1–L2) and new spec `host_runtime_docs.json`; Task 7's item 11 already killed by FF3a/FF3b; Task 6's three unreadable-file ids stated as an unkillable two-path residual. codex S1 → fixed: Task 16 B2 passes an expanded home path (`Path(args.skills_link)`, no `expanduser`, line 196). codex S2 → fixed: Task 1 keeps the full suite output and checks the FAILED/ERROR line count. teammate S1 → fixed: an AC-4.6 false hit stops Task 2 onward; Task 1 ACs no longer count a halt as met. teammate S2 → fixed: four record kinds (add, retire, amend `skills`, amend `pattern`) with what each moves (Task 3). teammate S3 → fixed: E1 killed by new Task 2 item 22 over a literal pattern (Task 2: 125 items, 95 pass after GREEN). teammate S5 → not applied: design v1.3 §D11 leaves the two W2 surfaces open for the orchestrator; recorded in Deviation 8. Nits: remedy cell replaced per design item 2, stated (1); `env=hermetic_env(X="1")` in Task 4 (2); Task 0 AC list joined (3); S5 wording per suffix (4). Also Task 18's gate command gains `--feature`. Counts: 19 tasks, 3 wiring, 117 mutation rows (73 + 24 + 14 + 6).
- v1.1 (2026-09-28): answers impl-plan audit cycle 1 (codex `audit.v1.p1`: 7 must, 1 should; teammate `audit.v1.teammate`: 3 must, 10 should, 7 nit), premises re-read at `a85abf7f`. codex M1 (probe sidecar after the design gate) — premise HOLDS (design lines 1380–1385 say "Before the design gate clears"; `ls docs/03-analysis/probes/multi-host-runtime` → absent), not refuted; the gate already closed at `34c0e962`, so the plan cannot reorder it: recorded as Deviation 7, open for the orchestrator. codex M2 + teammate M1 (`BASE_SHA` used before derived) — fixed: derivation block in §Preamble, Task 0 item 0, Task 1 re-derives and compares. codex M3 (single verdict vs C0.4) — fixed: verdict is the entry's comma-joined finding list, counts are findings; C0.4 now pins `verdict=undeclared:h-mad,stale:handoff` (advisor() 18/0 at `7e155451`). codex M4 (AC-4.6 false hit has no owner) — fixed as a halt: design §D2 has no narrowing mechanism, so Task 1 halts `design delta owed`; design change reported, not invented. codex M5 (retired id still parametrized) — fixed: sample test keyed on `BRANCH_SAMPLES`, plus `test_seed_check_honours_retirement[…]` (3) as the retirement-reason control. codex M6 (W3 force-fires are not force-fires) — fixed: FF3a/FF3b added (body-level env fallback, killed by `test_check_without_root_keywords_reads_no_new_root`); I1/I2 relabelled as design members. codex M7 (arm B `links_absent` unreachable) — fixed: run 4 expects `PASS cases=10`; `links_absent` is negative control 5 under an empty `HOME`. codex S1 (fixed Task 3 counts) — fixed: formulas over `len(BRANCH_SAMPLES)`. teammate M2 (bare `python3` has no pytest) — fixed: every run command uses `/opt/anaconda3/bin/python`; AC-8.3 commands executed → 31 passed / 31 passed. teammate M3 (SKILL.md install-check contract) — fixed as Deviation 8 plus 13 Task 14 nodes; also owed to design §D11. teammate S1 (`if` prefix before indentation) — fixed. S2 (`_FenceEvent.text` empty for body) — fixed (read at `a85abf7f`). S3 (`## Decision routing` locator returns None) — fixed with the full heading (executed: None vs `(14377, 2)`). S4 (suppression (d) two branches) — fixed: Sd-missing/Sd-header rows, (b) STALE/UNDECLARED half stated as a crash-kill residual. S5 (recognition-site guard cannot see host_parity) — fixed: `test_host_parity_has_no_fence_scanner` with a positive control (executed: `{'f'}`). S6 (byte-identity argv/first-failure) — fixed: advisor cases pass no `--mode`, first failure in listed order; parity probed at `a85abf7f` and deleted. S7 (codex R14(a) unbuildable) — deferred to design: premise holds, all three repairs change design §D10; Task 17 halts on it. S8 (Task 0 has no author) — fixed: codex authors Tasks 0, 16, 17. S9 (`problems.append`) — fixed. S10 (harness without `env -u HMAD_HOST`) — fixed. Nits: conftest not anchored (fixed); handoff forbidden tokens (fixed); `sys` import (fixed); CLI `--state` fixture (fixed); stub builtins (fixed); S7 wording (fixed); design Test Strategy vs Test Plan on resume-decision CLI tests — no change, a design-internal mismatch this plan follows the Test Plan on. Counts: 19 tasks, 3 wiring, 97 mutation rows (66 + 17 + 14).
- v1.0: Initial implementation plan (2026-09-28), first 5a draft; answers no audit cycle. From design v1.2, spec v1.4 and plan v1.3; premises read at 7e155451 (h-mad, handoff, probes and pytest.ini unchanged at b8662267). 19 tasks: Task 0 probe sidecar part 1 and Task 1 baseline at 5c, strands 1-4, 3 wiring tasks (W1-W3, W3 with two wires), mutation specs (94 rows = 88 design members + 6 wire rows), byte-identity and smoke-assertion probes, suite gate. Six deviations recorded (hermetic_env fixture, added killing tests, row census, state-file seed, D12 tokens in matrix rows, fixture shapes).
