# Implementation Plan: phase5-gate-feature-scope

> Source: docs/02-design/features/phase5-gate-feature-scope.design.md (v1.10, post-audit; Phase 4 ended on the two-round cap)
> Plan: docs/01-plan/features/phase5-gate-feature-scope.plan.md (v1.16); spec: docs/01-plan/features/phase5-gate-feature-scope.spec.md (v1.17, 88 ACs)
> Branch target: feature/phase5-gate-feature-scope (created at 5c in the feature's linked worktree, as plan §"Convention Prerequisites" item 5 orders)

## Executive Summary
Fifty-six tasks, in the plan's steps S0 to S11, build the shared scope functions in `h_mad_target_identity.py`, connect each consumer the plan's wire table names through one `wiring` task per row and step, and finish with the contract text and the whole-feature evidence.

## How to read this plan

- Every symbol, signature and file named here was checked against the worktree at `bb88b6cc` before it was written. Where the design gives a mechanism, this plan does not restate it; it cites the design section (`design §N`) and the plan's wire row (`row N`).
- Acceptance criteria inside a task are numbered `AC-<task>.<m>`. A criterion of the spec is always written `spec AC-x.y`.
- A test is named in two forms, by where the name is read. In prose, in test lists, in acceptance criteria and in every mutation row's `test` key it is the node id relative to `h-mad/`, which is the `root` of every mutation spec in `h-mad/tests/mutation-specs/` (`"root": "../.."`): `tests/test_h_mad_phase5_scope.py::test_x[id]` is the file `h-mad/tests/test_h_mad_phase5_scope.py`. On a `**WIRE-PIN**` line it is the repository-relative node id, `h-mad/tests/test_h_mad_phase5_scope.py::test_x[id]`, because `h_mad_wire_pin_gate.py` registers the pin verbatim and phase5-substeps 5f verifies it against a collection rooted at the repository root (`--rootdir <repository-root> --testpath h-mad/tests`), whose node ids carry `h-mad/`; the resolver matches a bracketed pin only exactly or after `::`, so a pin without the prefix would read as missing. The two forms name the same test; no other line of this plan uses the repository-relative form.
- The tree checks of this revision were made at `bb88b6cc` (whose `h-mad/` is unchanged at `992b7166`).
- A parametrised test lists its ids in brackets, separated by `|`. An id list written as a name in capitals (`FR4_CASES`) is defined once in §"Shared case lists", with its length. Written in angle brackets inside an id, a list stands for one id per member: `<FR4_CASES>-claude` is the 16 ids `absent-claude` to `git-cannot-judge-claude`, and `<ARMING_TARGETS>-<CODEX_WRITE_OPS>` is the 24 ids of the product, in that order.

## Conventions every task follows

1. **Where and with what.** All work is in the feature's linked worktree. Tests run under Python 3.11 through the worktree's thin venv: `.venv/bin/python -m pytest` on the task's test files, with `-q`, from the repository root. The full suite runs once per task, as the plan requires, from the repository root: `rtk proxy .venv/bin/python -m pytest`, read on pytest's own summary line. Its collected count is taken at 5c; after each task the expected count is the previous one plus the ids the task adds and minus the ids it removes, both as its test list states them (Tasks 30, 35, 38, 42, 44 and 47 remove ids; Task 38 adds 5 and removes 17, so its expected count falls by 12). A collected count that differs from the expected one is stopped on, so a planned removal does not read as lost coverage and a lost test does not hide behind an addition. Every Python module of `h-mad/scripts` and `h-mad/hooks` this plan edits is imported by the Python 3.9 interpreter of `INTERPRETERS`, and each carries `from __future__ import annotations`, which defers annotations only: a type expression evaluated when the module loads (an alias assignment such as Task 11's `Step`, a default value, a `cast`) is written with `Optional` and `Union`, never with `X | Y`.
2. **No live state, no installed file.** Every store is under `tmp_path`. Every test that runs a hook as a process sets `HOME` to a directory under `tmp_path` and uses `tdd_gate_support.hermetic_env`. The old side of every comparison is the tree of `7a3cca48`, extracted with `git archive 7a3cca48 h-mad/hooks h-mad/scripts h-mad/bin` into a temporary directory; a clone without that commit fails the test and does not skip it. Each side runs with its own `h-mad/bin` first on `PATH`, and the harness asserts that `hmad-dispatch` resolves inside that side's tree.
3. **Hooks are driven as processes.** Hook behaviour is asserted through the three real hooks (`h-mad/hooks/h-mad-codex-tdd-gate.py`, `h-mad/hooks/h-mad-agy-tdd-gate.py`, `h-mad/hooks/h-mad-tdd-gate.sh`), read with `tdd_gate_support.host_decision(host, result)`, the one decoder per host that Task 1 adds to `h-mad/tests/tdd_gate_support.py` beside the unedited `decision`. The three output protocols differ and each is decoded by its own branch: the Claude hook by `decision`'s forms (a silent allow, or exit 2 with a reason on stderr that holds `[H-MAD-TDD-GATE] BLOCK kind=`, the kind and a colon, as in `[H-MAD-TDD-GATE] BLOCK kind=judge-error:`, or the JSON denial); codex by a silent allow or a well-formed `hookSpecificOutput` denial JSON, which is `deny` whatever its reason says, its kind the last match of `kind=([a-z0-9-]+)` in the reason (as in `refusing fail-closed. kind=judge-error`, and the production refusal `requires a failing test before …: kind={verdict.kind}; {verdict.reason}`, where the match stops before the `;`), or `""` when the reason has no `kind=` (as the unreadable-state shell refusal, the allowance refusals, the unidentified-target refusal of `_main_guarded`, `write target is outside or unreadable` and `forbids codex writing` at `7a3cca48`, and FR-5's codex refusal, carry none; codex reasons carry no `BLOCK` prefix), so a test that asserts a codex refusal's kind asserts `""` and a fixed part of the reason for those; agy by exactly one JSON object on stdout with exit 0, `{"decision": "allow"}` for an allow and `{"decision": "deny", "reason": …}` whose reason ends with `kind=` and the kind (as in ` kind=arming-input`) for a refusal. `invalid` is reserved for an answer that is no well-formed envelope of its host (on codex: stdout that is neither empty nor one `hookSpecificOutput` denial object, or a non-zero exit), so a crash or a malformed answer is never read as either decision, and a missing kind is never read as a malformed answer. Git is never mocked, except by a PATH shim that records, fails or delays calls (design §Test Strategy). A shim that fails or delays only calls carrying `--no-optional-locks` lets the two root lookups through.
4. **Fixtures in no work tree** stand on the system volume, or set `GIT_DISCOVERY_ACROSS_FILESYSTEM=1` there (design §Test Strategy).
5. **Mutation specs.** One new spec per new test file, in `h-mad/tests/mutation-specs/`: `phase5_scope.json`, `phase5_scope_wires.json`, `phase5_arming_inputs.json`, `phase5_scope_differential.json`, `phase5_scope_topologies.json`, `phase5_scope_docs.json`, `state_write_scope.json`, `assemble_tdd_scope.json`, `tdd_judge_scope.json`, `landing_lanes.json`. Each row has the keys `name`, `_mechanism`, `file`, `find`, `replace` and `test`; `test` is a full node id as written in this plan. A row whose `file` has a type for which the harness derives an enclosing symbol (`enclosing_symbol` in `h-mad/scripts/h_mad_mutation_harness.py`: `.py`, `.sh`, an extensionless file, `.md`) also carries `symbol`, with the value the harness derives for its anchor; a row on any other type carries no `symbol`, because the harness's `anchor_check` reports a pinned symbol it cannot derive as a migration and refuses the spec. In this plan the one such row is Task 11's `schema-fields-required`, on `h-mad/scripts/h_mad_state_schema.json`. Each new spec's header, written with its first row, is that of the existing specs (as `claude_gate_listing.json`): `"root": "../.."`; `"command": ["python3.11", "-m", "pytest", "tests/<the spec's own test file>", "-q"]`, the own test files being, in the order of the spec list above, `test_h_mad_phase5_scope.py`, `test_h_mad_phase5_scope_wires.py`, `test_h_mad_phase5_arming_inputs.py`, `test_h_mad_phase5_scope_differential.py`, `test_h_mad_phase5_scope_topologies.py`, `test_h_mad_phase5_scope_docs.py`, `test_h_mad_state_write_scope.py`, `test_h_mad_assemble_tdd_scope.py`, `test_h_mad_tdd_judge_scope.py` and `test_h_mad_landing_lanes.py`; and `"target_command": ["python3.11", "-m", "pytest", "-q"]`, to which the harness appends each row's `test`, so a row whose `test` lies in another file is still scored on that test. The interpreter is `python3.11`, which carries pytest, and every path is relative to the spec's `root`, `h-mad/`. Only a spec's first row is written by hand; every other row is added with the harness's `--append-row` mode (`python3.11 h-mad/scripts/h_mad_mutation_harness.py --append-row ROW.json SPEC.json`, `ROW.json` holding the one row). Who runs which harness command is fixed, because the codex Phase-5 gate admits the harness only with `--check-anchors` and at least one in-project spec argument (`h_mad_target_identity.py`, the `M:CX-MUT-ANCHORS` line): the gated GREEN dispatch runs `python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors` only on those of the task's specs that exist at the task's RED base (a spec of this plan that an earlier task created, or an existing spec the task re-anchors under convention 6), named one by one, as literal paths and never by a glob (a gated shell refuses `*`). That check reads earlier tasks' rows only: it shows whether the task's production edit moved one of their anchors, and it is no evidence about the task's own rows. A spec the task itself creates does not exist during GREEN (the harness answers a missing spec with `UNCLASSIFIABLE — cannot read JSON` and exit 2), so it is never named there: on Tasks 1, 3, 5, 8, 9, 15, 28, 53 and 55, the 9 tasks with a GREEN dispatch that create a spec, the gated check names only the task's other specs that exist, and it is not run when none does. GREEN proposes its rows in its final message; the orchestrator, outside the gate, writes each new spec's first row, adds every other row with `--append-row`, then runs the per-spec check on every spec of the task, the new ones included, and runs the argument-free `python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors`, which sweeps every committed spec in the repository. Those two checks of the orchestrator report no drift after each task, and they are the evidence about the task's own rows. Mutations are scored on the pytest summary. A killing test asserts the decision, and for a refusal its kind and the record it names, so that no mutant is counted as killed by a crash (plan §"Success Criteria").
6. **Existing specs.** A spec with an anchor inside a function a task edits is re-anchored in that task's commit, keeps its mutation's meaning, and is re-run in full (plan §"Existing tests and mutation specs affected"). Each task names those specs.
7. **The two removals of a scope call** (plan rule 3) and their two expressions are design §13's **A** (every live record) and **F** (every file). The status form of **A** carries Task 33's OPEN-DECISION (OD-2); every row that uses it follows the resolution 5d records there.
8. **Reverse values.** `INACTIVE` is `Status("inactive", ())` and `ACTIVE` is `Status("active", ())`. A *fixed active chain* is `Chain("active", (record,), None, "")` with the fixture's own record (design §13).
9. **RED first** (plan §"Convention Prerequisites", RED first). Each new test is observed failing before its change is committed, for its stated reason. A test whose whole required decision the tree already gives is a **guard**: it is listed as passing at RED, and it is observed failing under the mutant named beside it, which is a row of a spec of this plan (or of the existing spec the task names). The harness runs only a row's own `test` under its mutant (`h_mad_mutation_harness.py`, `scoring_command = list(target_command) + [mutation["test"]]`), so a guard is credited in one of two ways and no other: it is the `test` of the row it names, and the harness scores it; or it is covered by the **observation procedure**, the shape of convention 10's pin-only RED: after the task's GREEN, the orchestrator copies the row's `file`, applies the row's `find` and `replace` (the `find` matching exactly once), runs `.venv/bin/python -m pytest -q` on the guard ids named under that row, records each id's failure from pytest's summary in the 5e report, restores the file and reads the restore back by sha256 against the copy. A row may be named for a guard only when its change reaches the input the guard varies (the guard's fixture takes the code path the row changes, with the value the row's changed condition reads); a guard id that does not fail under its named row is a defect of this plan, stopped on and reported, never credited. The residual of the procedure: its observations are recorded in the 5e reports and are not re-scored at S11 by a `MUTATION:` token. A test that passes at RED and that no change to this feature's production files can make fail (it reads a fixed artefact such as the extracted writer of `7a3cca48`, or a property the operating system gives) is an **observation**, never a guard: it names its *detector control*, a deliberate violation of the property that the test must report, run once at RED and recorded in the RED report, or, where the violating artefact is the task's own GREEN code (Task 11), run once after GREEN and recorded in the 5e report; it is never counted as a mutation kill. Every test this plan lists as passing at RED is one of the two, and says which. Each `WIRE-PIN` is also observed failing under its removal mutant, at the orchestrator's wire-scoped revert in 5e.
10. **A `WIRE-PIN` fails at RED by an assertion about the caller.** Where a task creates a function and its call together, the pin observes the caller's output (a hook decision, a verb's line, a CLI's token), so it fails because the caller has not consulted the callee, never by an `ImportError`. Where a pin needs a callee that does not exist at RED, the task states its scaffold. Where a pin's call stands on the tree at RED (Task 14's pin 1, Task 27's pin 1, and every pin of Tasks 26, 31, 32, 49 and 51), the pin passes at RED and is a guard by convention 9. For Tasks 26, 31, 32, 49 and 51, every pin of which passes on the tree, the 5d RED is the removal-mutant observation and nothing else: no test of the task is expected to fail at RED, and the RED report records, for each pin, the orchestrator applying that pin's removal row (the rows named in the task's table) and the pin failing under it, with the row restored afterwards.
11. **Commit unit.** One commit per step, at 5g, after every task of that step is green: the plan's order of work is per step, and each surface's commit carries the whole rule for that surface (plan §"Order of work"; design §Implementation Order). Within a step the tasks are dispatched in the order written, and one at a time: a task's 5d RED, its 5e GREEN, spec review and verification, and its whole-module revert all finish before the next task's 5d is dispatched, so every task's RED base holds the GREEN of each earlier task (Task 5's RED holds Task 3's `git_environment` and Task 4's `checkout_of`). This departs, for this feature, from the batch order the implementer prompt assumes ("every 5d runs before any 5e", `h-mad/references/codex-implementer-prompt.md`), and each RED dispatch says so in its text, naming the earlier tasks whose GREEN its base holds; a listed guard that fails at RED is then never `guard-not-yet-built` and is stopped on. Because the tasks of one step edit the same production files before the step's commit, a task's RED base is its **task checkpoint**, never a stash of the whole file: at 5c the orchestrator makes one scratch directory, `CHECKPOINTS=$(mktemp -d)`; before a task's RED dispatch it copies every production file the task names into `"$CHECKPOINTS/task-N/pre/"` (N the task number), recording a file that does not yet exist as absent; and the whole-module revert of 5e for that task first copies the same files into `"$CHECKPOINTS/task-N/post/"`, then restores the `pre/` copies in place (deleting a file recorded absent), runs the task's tests, and restores the `post/` copies. Each restore is read back by comparing sha256 values with the copies. So the revert removes this task's change and keeps the earlier tasks of the step, Task 5's callee from Task 3 included; `git stash` is not used for a revert inside a step, since a stash of a whole file carries every earlier task of the step with it. The step's one commit at 5g is unchanged.
12. **The differential tracks the steps, by decision branch.** `differential.py` (Task 1) holds `CHANGES_IN_FORCE`, a map from a key `(surface, branch)` to the classes of spec FR-10 (D1 to D7) that the tree has landed on that branch of that surface. `branch` is `"arming"` for a call FR-5 or FR-6 judges (a shell command that names the writer and an arming field, a write whose target is a state file's name) and `"other"` for every other call; the builder gives each call its branch from the call's own facts, never from an outcome. A surface's two branches move in different tasks (codex's ordinary command in Task 39 and its FR-5 command in Task 42; agy's in Tasks 43 and 44; the write surfaces' arming files in Tasks 30, 35 and 38, after their production writes in Task 25), so a full-suite run between them needs a different twin for each. Every value is empty at S0. Each task that puts a class in force on a branch adds it in the same commit and names its keys under **Differential**; a re-routing task that moves an `"arming"` branch onto the scope functions (Tasks 30, 35, 38, 42, 44) adds to that key every class the same surface's `"other"` key then holds. Beside it, `LEGACY_RAISE_LIFTED`, a set of surfaces, is empty until Task 47: while a codex or agy surface is absent from it, the twin of a call on that surface keeps every state file whose top level is not an object wherever `rglob("docs/.bkit-memory.json")` finds it, whatever the classes in force, because until Task 47 both Python hooks call `_any_phase5_status` before they branch, and its walk raises on that file in an excluded tree too (Task 1's corpus holds that case, `excluded-not-object`, and its readable control, `excluded-object-not-live`, an object without a live record in the same place: before Task 47 the first is refused through the hook's exception path on the codex and agy surfaces and the second gets its twin's verdict; from Task 47 both get the decision the session's discovery gives, the file not being read). The one flag `build_twin` and `expected_verdict` take is derived per call as `legacy_raise_lifted = spec.surface == "claude" or spec.surface in LEGACY_RAISE_LIFTED`, so the `claude` surface is lifted at every task: its hook at `7a3cca48` makes no `rglob` walk (`git show 7a3cca48:h-mad/hooks/h-mad-tdd-gate.sh | grep -c 'rglob\|_any_phase5_status'` gives 0, and its judge reads the chain, `git show 7a3cca48:h-mad/scripts/h_mad_tdd_judge.py | grep -c rglob` giving 0), so no twin of a Claude call keeps a file for a raise that hook never made. The Claude arming branch from Task 24 to Task 29, where `emit_arming` judges by `unscoped_judge(root)`, which reads a raise of the walk as `unknown` (Task 20), needs no flag: `CHANGES_IN_FORCE[("claude", "arming")]` holds D6 and not D1 there, so the twin keeps a not-object file in an excluded tree, and the plan's step 4 (a call FR-6 names, beside an unreadable file that counts for it) requires the refusal the tree gives; from Task 30 that key holds D1, the twin drops the file, and the scan does not read it. The oracle builds twins with those changes only, so every step, and every task inside it, ends with a differential run in which every verdict is the expected one (plan §"Order of work").
13. **Single source.** Each shared function a task adds to `h_mad_target_identity.py` is entered, in the same commit, in a second tuple `SCOPE_FUNCTIONS` of `h-mad/tests/test_h_mad_shared_gate_policy.py`, run through `test_each_scope_function_has_one_definition_in_the_identity_module`; each shared constant in `SCOPE_CONSTANTS`, run through `test_each_scope_constant_is_assigned_in_the_identity_module`. Both are additions; `MOVED_FUNCTIONS` and `test_codex_gate_binds_every_moved_name_to_the_identity_module` are not edited (plan §"Single source").
14. **Public text.** Tests, fixtures, mutation `_mechanism` texts and probe output state required decisions only, with neutral keys and paths; nothing names a live lane. Where a fixture depends on a private ruling the task says "see the private record" and nothing more.
15. **Stated counts are whole-file totals.** A task's RED and GREEN dispatch is staged with one `--test-path` per file on its **Test file** line, and `h_mad_assemble_tdd.py` counts `--expect-fail` and `--expect-pass` as totals across every test path of the dispatch, not per file. So each **Stated counts** line gives the totals over those whole files: the task's new failing ids; plus, passing, its guards and observations and every node the files already hold at the task's RED base (the ids earlier tasks of this plan added, less those they removed, and, for a file that exists at `bb88b6cc`, the nodes collected there: `test_h_mad_shared_gate_policy.py` 29, `test_h_mad_agy_tdd_gate.py` 112, `test_h_mad_tdd_gate_judge.py` 141, collected from an export of `bb88b6cc` with `.venv/bin/python -m pytest --collect-only -q`). An id parametrised over `INTERPRETERS` counts as passing on the machine of record, where every interpreter resolves; an absent interpreter's ids are skips and come off the passing count. If 5c collects a different number for an existing file, every stated total that includes it moves by the same difference. For a `wiring` task the split of its new ids at RED is the RED report's (phase5-substeps 5d) unless the task gives it; its line gives the new ids, the guards among them and the prior nodes, which is what the assembler's informational counts need.
16. **Step-end readings.** S6 ends, before S7 is dispatched, with the Claude hook's timing reading the plan orders (plan §"Tradeoffs to preserve", the owed readings: `timing.py` takes the Claude hook in S6, the first commit whose Claude hook makes the discovery that lands): `python3.11 docs/03-analysis/probes/phase5-gate-feature-scope/timing.py --old "$OLD" --runs 20 --hook claude` in scratch (the 20,000-file fixture) and the same with `--repo "$PWD"` from the repository root, `$OLD` filled as in Task 2. A median over the bound (`TIMING: max_added_ms` above 300) in either is put to the operator before S7 begins; the readings are recorded with their commands in the S6 report and are not committed.

## Shared case lists

| Name | Ids | Length |
|---|---|---|
| `SURFACES` | `codex-shell`, `codex-write`, `agy-shell`, `agy-write`, `claude` | 5 |
| `INTERPRETERS` | `py3.9`, `py3.11`, `py3.12`, `py3.13`, `py3.14`, `py3.15` | 6 |
| `VARIABLES` | `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_CEILING_DIRECTORIES` | 4 |
| `PHASES` | `red`, `green`, `gate`, `review`, derived at run time from the assembler's `--phase` choices and never typed (row 21) | 4 |
| `FR4_CASES` | `absent`, `null`, `number`, `boolean`, `list`, `object`, `empty`, `relative-dot`, `relative-tilde`, `relative-plain`, `missing-path`, `names-file`, `not-top-level`, `sub-project-directory`, `checkout-unreadable`, `git-cannot-judge` (spec AC-4.1 to AC-4.8) | 16 |
| `FR4_MORE` | `symlinked-state-valid`, `symlinked-state-no-checkout`, `symlinked-state-dangling`, `symlinked-state-looping`, `symlinked-checkout-record`, `symlinked-checkout-session`, `case-variant`, `linked-worktree-main-named`, `linked-worktree-reverse`, `nested-outer-named`, `nested-reverse`, `moved-checkout` (spec AC-4.10 to AC-4.15) | 12 |
| `DISCOVERY_CASES` | `root-ignored`, `root-tracked`, `sub-project-tracked`, `sub-project-state-ignored`, `sub-project-new`, `excluded-live`, `excluded-unparsable`, `tests-component`, `fixtures-component`, `nested-clone`, `nested-worktree`, `submodule`, `ignore-rule-added`, `git-cannot-answer`, `docs-symlink`, `directory-symlink` (spec AC-2.1 to AC-2.7, AC-2.10) | 16 |
| `PRESENCE_CASES` | `regular`, `file-link`, `dangling-link`, `looping-link`, `directory-in-place`, `docs-symlink`, `case-variant-docs`, `case-variant-file` (spec AC-2.11) | 8 |
| `SESSION_UNKNOWN_CASES` | `bare-root`, `damaged-root`, `no-work-tree`, `git-missing`, `git-failing`, `git-timeout` (spec AC-4.16; plan §"Convention Prerequisites") | 6 |
| `ARMING_TARGETS` | `root-state`, `sub-project-state`, `dot-git-component`, `alternative-spelling` (spec AC-6.1 to AC-6.3) | 4 |
| `CODEX_WRITE_OPS` | `codex-patch-add`, `codex-patch-update`, `codex-patch-delete`, `codex-patch-move`, `codex-write`, `codex-edit` | 6 |
| `AGY_WRITE_OPS` | `agy-write_to_file`, `agy-replace_file_content`, `agy-write_file`, `agy-edit_file` | 4 |
| `CLAUDE_WRITE_OPS` | `claude-write`, `claude-edit` | 2 |
| `SHARED_FILE_REFUSED` | `a7-own-file`, `a7-through-b-link`, `a7-dot-git-in-a`, `a8-link`, `a8-real-file`, `a8-m-session-a-link` (the refusals of spec AC-6.7, AC-6.8; each is refused whether every live record counts or only an applying one) | 6 |
| `SHARED_FILE_KEEPS` | `a7-dot-git-in-b-keeps`, `a8-m-own-file-keeps` (the present decisions of spec AC-6.7, AC-6.8; each holds only once a record that does not apply stops counting, so each lands with its host's re-routing task) | 2 |
| `ARMING_VARIANTS` | `arm`, `disarm`, `repeat`, `other-record`, `first-of-several`, `middle-of-several`, `last-of-several` (spec AC-5.1, AC-5.2) | 7 |
| `NON_ARMING_OPS` | `create`, `claim`, `release`, `beat`, `drop-undeclared`, `other-field` (spec AC-5.4) | 6 |
| `OWNER_FIELDS` | `owner_session_id`, `owner_heartbeat_ts`, `feature-key` (spec AC-3.7) | 3 |
| `ARMING_FILE_IDS` | `session-root-as-named`, `session-root-as-resolved`, `target-checkout-as-named`, `target-checkout-as-resolved`, `linked-referent`, `linked-referent-absent`, `unfiltered-discovery` (row 6, S5) | 7 |
| `MENTION_HITS` | `unknown-program`, `known-program`, `one-word`, `several-words`, `field-first`, `name-case`, `field-case`, `name-quotes`, `field-quotes`, `longer-word`, `link`, `relative-link`, `word-part`, `link-quotes`, `field-phase`, `field-implementation_checkout`, `field-phase5_stage`, `space`, `split` (the clauses of FR-5) | 19 |
| `NO_MENTION_CASES` | `name-alone`, `field-alone`, `no-equals`, `letter`, `digit`, `underscore` | 6 |
| `ARMING_WRITE_IDS` | `safe`, `run-wrapped-plain`, `run-wrapped-leading-zero`, `run-wrapped-nested`, `allowed`, `mention-<MENTION_HITS>`, `mention-no-line`, `unfiltered-discovery`, `no-mention-<NO_MENTION_CASES>`, `inert-operand`, `inert-value` (row 7, S5) | 34 |
| `PER_TARGET_IDS` | `target-in-named-checkout`, `other-checkout`, `target-checkout-unknown`, `excluded-tree` (row 5) | 4 |
| `CHAIN_IDS` | `production-other-checkout`, `production-excluded-tree`, `production-target-in-named-checkout`, `production-target-checkout-unknown`, `production-unreadable`, `listed-other-checkout`, `listed-excluded-tree`, `listed-target-in-named-checkout`, `listed-target-checkout-unknown`, `listed-unreadable` (row 32) | 10 |
| `WORKDIR_UNKNOWN_CASES` | `null`, `empty`, `not-string`, `nonexistent`, `file`, `timeout`, `bare`, `git-dir-without-head`, `git-file-missing-gitdir`, `moved-main-worktree`, `separate-volume`, `refused-top-level` (row 2) | 12 |
| `OUTSIDE_ROOT_REASONS` | `target-match`, `checkout-match`, `session-unknown`, `target-unknown`, `other-checkout`, `field-absent` (row 17) | 6 |
| `UNUSABLE_CASES` | `not-string`, `empty`, `relative`, `missing-path`, `names-file`, `not-top-level`, `checkout-unreadable` (row 17; spec AC-4.2 to AC-4.8) | 7 |
| `LARGE_TREE_LAYOUTS` | `wide`, `trees`, `subs`, `nested`, `small`, `nogit` (spec AC-2.9) | 6 |
| `RECORD_STATES` | `none`, `live` | 2 |
| `STAGE_VALUES` | `absent`, `null`, `implementing`, `unknown-string`, `non-string` (spec AC-9.3) | 5 |
| `INCIDENT_SHAPES` | `linked-worktree` (the live shape of the brainstorm's §"Evidence": one feature live in the main checkout, a worktree armed through a symlinked state file), `evidence-a-not-live`, `evidence-b-live`, `evidence-linked-second-checkout`, `evidence-excluded-live`, `evidence-excluded-unparsable`, `evidence-tests-fixtures` (the six rows of that section's table) | 7 |

`INTERPRETERS` is resolved by executable identity from the launchers `/usr/bin/python3`, `python3` and each `python3.N` on `PATH` from 3.11 up (spec Compatibility: "the distinct interpreters among" them; plan §"Convention Prerequisites", Interpreters). Each launcher is run once to report its `sys.executable` and version; launchers whose reported executables have the same realpath are one interpreter, resolved once; each distinct executable is one id, `py` followed by its major and minor version (`py3.11`), and a second distinct executable of the same version takes the suffix `-2` (`py3.11-2`, in launcher order), so two installations of one version are both exercised and neither hides the other. An absent interpreter is a named skip. `tests/test_h_mad_phase5_scope_differential.py::test_supported_interpreters_are_the_parametrised_set` (Task 1) fails when the resolved set differs from the parametrised one, and `test_interpreter_resolution` (Task 1) holds the alias, the collision and the missing launcher on scratch launchers. On the machine of record the six ids above resolve, `python3` giving the same executable as `python3.15`.

The tests of the hooks, the writer and the `scope` verb that this plan says run "under each supported Python" keep pytest in the thin venv and vary the invoked process, with the launch method of `h-mad/tests/test_h_mad_hook_live_interpreter.py`: a `python3` shim first on `PATH` that appends its own path to a log and execs the interpreter (codex and Claude hooks, the writer and the judge), and the agy hook through that shim's directory as well. Each interpreter has its own shim directory, so the logged shim path names the interpreter it execs. Each such test asserts, from the log, which interpreter ran each process, so the evidence of which interpreter ran is the test's own. This applies to the topologies of Task 52 and to the `FR4_MORE` ids that hold spec AC-4.10 to AC-4.12 (`symlinked-state-*`, `symlinked-checkout-*`, `case-variant`), whose checkout fields the field-free differential cannot cover: each of those ids loops over the resolved interpreters inside the test and gives one decision for all of them.

Every case of `FR4_CASES` and `FR4_MORE` is one test with both halves, and which session takes which half follows the case (spec FR-4, AC-4.1 to AC-4.15):
- **A record whose checkout cannot be used** applies to every session that finds it. These ids are every `FR4_CASES` id and the `FR4_MORE` ids `symlinked-state-no-checkout`, `symlinked-state-dangling`, `symlinked-state-looping` (unreadable, refused) and `moved-checkout`: the refused half is from a session in a checkout the record does not name (spec FR-4's "tested from a session in a checkout the record does not name"), and the not-gated control is a valid record naming another checkout.
- **A record whose checkout can be used** applies where it matches and nowhere else, so its admitted half is the session the spec says it does not apply to, and its gated half is the matching session: `symlinked-state-valid` (admitted from another checkout, gated from the named one); `symlinked-checkout-record` and `symlinked-checkout-session` (gated in the real checkout, through the link; admitted in another checkout); `case-variant` (on the case-insensitive system volume, gated in its checkout and admitted in another; on the mounted case-sensitive image, where it is spec AC-4.5, refused from any checkout); `linked-worktree-main-named` (admitted in the linked worktree, gated in the main checkout); `linked-worktree-reverse` (admitted in the main checkout, gated in the linked worktree); `nested-outer-named` (admitted in the nested checkout, gated in the outer); `nested-reverse` (admitted in the outer checkout, gated in the nested).

## Task index

| Task | Step | Name | Shape | Wire rows |
|---|---|---|---|---|
| 1 | S0 | Differential harness and oracle | new-behaviour | |
| 2 | S0 | Measurement probes and the pin census | new-behaviour | |
| 3 | S1 | Git environment and pure readers | new-behaviour | |
| 4 | S1 | Checkout identity | new-behaviour | |
| 5 | S1 | State-file discovery | wiring | 29 |
| 6 | S1 | Applicability and the scan | new-behaviour | |
| 7 | S1 | `_safe_argv` delegation | wiring | OD-4 |
| 8 | S1 | Writer parser delegation | wiring | OD-4 |
| 9 | S1 | Arming fields test (FR-5) | new-behaviour | |
| 10 | S1 | Arming files test (FR-6) | new-behaviour | |
| 11 | S2 | Writer: one result, resolved store, schema, transitions | new-behaviour | |
| 12 | S2 | Writer checkout validation and spelling | wiring | 23 |
| 13 | S2 | Writer store membership | wiring | 22 |
| 14 | S2 | Writer seeds both paths | wiring | 31 |
| 15 | S3 | Assembler checkout halt | wiring | 20 |
| 16 | S3 | Assembler stage halt | wiring | 21 |
| 17 | S3 | Assembler lookup root | wiring | 30 |
| 18 | S4 | codex root lookup environment | wiring | 27 |
| 19 | S4 | agy root lookup environment | wiring | 28 |
| 20 | S5 | Today's walk as a value, and `unscoped_judge` | new-behaviour | |
| 21 | S5 | codex arming files | wiring | 6 (S5) |
| 22 | S5 | codex arming fields | wiring | 7 (S5) |
| 23 | S5 | agy arming files and fields | wiring | 12 (S5) |
| 24 | S5 | Claude arming files | wiring | 19 (S5) |
| 25 | S6 | `read_chain` on the scoped chain | wiring | 14 |
| 26 | S6 | `state` and `judge` verbs | wiring | 15 |
| 27 | S6 | `listing` verb and the outside-root filter | wiring | 17 |
| 28 | S6 | `scope` verb | wiring | 24 |
| 29 | S6 | Claude hook through the verbs | wiring | 18 |
| 30 | S6 | Claude arming files re-routed | wiring | 19 (S6) |
| 31 | S6 | codex production and listed targets | wiring | 32 |
| 32 | S6 | agy production and listed targets | wiring | 33 |
| 33 | S7 | codex refusals without a resolvable target | wiring | 4 |
| 34 | S7 | codex per-target branches | wiring | 5 |
| 35 | S7 | codex arming files re-routed | wiring | 6 (S7) |
| 36 | S7 | agy refusals without a resolvable target | wiring | 10 |
| 37 | S7 | agy per-target branches | wiring | 11 |
| 38 | S7 | agy arming files re-routed | wiring | 12 (S7) |
| 39 | S8 | codex shell | wiring | 1 |
| 40 | S8 | codex command directory (rule 5) | wiring | 2 |
| 41 | S8 | codex unreadable-root branch | wiring | 8 |
| 42 | S8 | codex arming fields under the shell's applicability | wiring | 7 (S8) |
| 43 | S8 | agy `run_command` | wiring | 9 (S8) |
| 44 | S8 | agy arming fields under the shell's applicability | wiring | 12 (S8) |
| 45 | S8 | agy tools outside the admitted classes | wiring | 13 |
| 46 | S8 | Shell refusal text | wiring | 26 |
| 47 | S8 | One scan per hook call | new-behaviour | |
| 48 | S9 | codex shell stage | wiring | 3 |
| 49 | S9 | codex arming fields stage | wiring | 7 (S9) |
| 50 | S9 | agy stage, three places | wiring | 9 (S9) |
| 51 | S9 | agy arming fields stage | wiring | 12 (S9) |
| 52 | S9 | Writer routes and topologies | gate | |
| 53 | S10 | Landing probe | wiring | 25 |
| 54 | S10 | Store reading | new-behaviour | |
| 55 | S10 | Contract text | new-behaviour | |
| 56 | S11 | Whole-feature evidence | operational | |

Counts over this table: 56 tasks; 42 `wiring` (Tasks 5, 7, 8, 12 to 19, 21 to 46, 48 to 51 and 53); 12 `new-behaviour` (Tasks 1, 2, 3, 4, 6, 9, 10, 11, 20, 47, 54, 55; Task 47 was `refactor` until v1.3, and one decision moves in it); 1 `gate` (Task 52); 1 `operational` (Task 56). The 42 wiring tasks are the plan's 40 pairs of row and step (rows 1 to 15 and 17 to 33, a row with ids in more than one step counted once per step) and Tasks 7 and 8, which carry OD-4. Row 29 is one task (Task 5); Task 4, before it, builds `checkout_of` without the environment, which Task 5 adds with the four discovery calls.

## Open decisions carried

These are the build-class findings left open when the plan and design audits reached their two-round cap (design audit sidecar `phase5-gate-feature-scope.design.audit.v3.md`; findings of `phase5-gate-feature-scope.design.audit.v2.p1.md`; later reviews). Each still open stands on the task it lands in as an `OPEN-DECISION`, with one implementation named that meets its criterion; 5d settles it. Three were ruled by the operator on 2026-11-26 and stand on their tasks as rulings, not decisions: OD-1 (a), OD-12 (a) and OD-13 (a). The same rulings fix the branch created at 5c, `feature/phase5-gate-feature-scope`, and the RED of the pin-only wiring tasks (convention 10).

| OD | Subject | Task |
|---|---|---|
| OD-1 | case-folding discriminator for spec AC-6.6 (ruled: the stricter reading where the capability lookup is unavailable is a stated residual) | 10 |
| OD-2 | status form of removal A | 33 |
| OD-3 | one shell status read in three places on agy | 43, 50 |
| OD-4 | connection mutants for the S1 delegations | 7, 8 |
| OD-5 | landing probe passes the stored record | 53 |
| OD-6 | assembler tests need a real agy wiring configuration | 15 |
| OD-7 | what the S5 walk count counts | 21 |
| OD-9 | state of three fixtures, from the private record | 28 (named also on 1 and 6) |
| OD-10 | `unscoped_judge` beside the residual of spec FR-10 | 20 |
| OD-11 | an unbounded `wait` after `kill` | 5 |
| OD-12 | an oracle left open in an in-process test (ruled: `TreeOracle.close()` called by tests only, with a `ResourceWarning` test) | 5 |
| OD-13 | what a killed wrapper started (ruled: the direct child alone is killed and reaped; a grandchild is a stated residual) | 5 |
| OD-14 | readings of design §2 and §7 not re-taken | 56 |
| OD-15 | public text on ruled limits | 56 |

OD-8 is measurement-class and is not a task decision: the design's prototype readings become re-runnable when Task 2 commits `discovery_probe.py`, and the sidecar's command is the one Task 2 records.

## Acceptance-criteria map

Every spec criterion, the task or tasks whose tests hold it, and the test.

| Spec AC | Task | Test |
|---|---|---|
| AC-1.1 | 12 | `tests/test_h_mad_state_write_scope.py::test_arm_with_checkout_stores_canonical` |
| AC-1.2 | 12 | `tests/test_h_mad_state_write_scope.py::test_arm_refuses_unusable_checkout` |
| AC-1.3 | 13 | `tests/test_h_mad_state_write_scope.py::test_store_must_be_discoverable`, `::test_undiscoverable_store_wire` |
| AC-1.4 | 11 | `tests/test_h_mad_state_write_scope.py::test_arm_without_checkout_clears` |
| AC-1.5 | 11 | `tests/test_h_mad_state_write_scope.py::test_live_checkout_rules` |
| AC-1.6 | 11 | `tests/test_h_mad_state_write_scope.py::test_disarm_clears_both_fields` |
| AC-1.7 | 11, 14 | `tests/test_h_mad_state_write_scope.py::test_symlinked_store_write`, `::test_seed_both_paths_wire` |
| AC-1.8 | 11 | `tests/test_h_mad_state_write_scope.py::test_validator_reads_new_fields_as_strict` |
| AC-1.9 | 11 | `tests/test_h_mad_state_write_scope.py::test_null_field_rules` |
| AC-2.1 to AC-2.7, AC-2.10 | 5, 25, 39, 43 | `tests/test_h_mad_phase5_scope.py::test_discovery_unit`, `::test_discovery_rule` |
| AC-2.8 | 5, 18, 19, 21, 25 | rows 27 to 29 (`test_git_environment_wire`, `test_codex_root_wire`, `test_agy_root_wire`); `tests/test_h_mad_phase5_scope.py::test_git_variables` |
| AC-2.9 | 47 | `tests/test_h_mad_phase5_scope.py::test_large_tree`; timing in Task 56 |
| AC-2.11 | 1, 5 | `tests/test_h_mad_phase5_scope.py::test_presence_case`; the differential per interpreter |
| (Compatibility, simulated Linux) | 6, 10 | `tests/test_h_mad_phase5_scope.py::test_checkout_match_without_f_getpath`; `::test_fold_discriminator[case-sensitive-volume-absent-document]` |
| AC-3.1 | 25, 39, 43 | `tests/test_h_mad_phase5_scope.py::test_two_checkouts` |
| AC-3.2 | 25, 39, 43 | `tests/test_h_mad_phase5_scope.py::test_other_feature_other_checkout` |
| AC-3.3 | 25, 39, 43 | `tests/test_h_mad_phase5_scope.py::test_same_checkout_feature` |
| AC-3.4 | 27, 29, 34, 37 | rows 17, 18; `tests/test_h_mad_phase5_scope.py::test_production_into_second_checkout` |
| AC-3.5 | 40, 43 | rows 2, 9 |
| AC-3.6 | 31, 32, 43 | rows 32, 33; `tests/test_h_mad_phase5_scope.py::test_surfaces_agree_on_applying_records` |
| AC-3.7 | 6, 43 | `tests/test_h_mad_phase5_scope.py::test_applicable_ignores_owner_fields`, `::test_owner_fields_change_nothing` |
| AC-4.1 to AC-4.8 | 25, 39, 43 | `tests/test_h_mad_phase5_scope.py::test_fr4_case` |
| AC-4.9 | 1, 25, 31, 32, 39, 43, 47, 48, 50 | the differential corpus; rows 32, 33 `unreadable`; `tests/test_h_mad_phase5_scope.py::test_unreadable_beside`, `::test_unreadable_beside_planning` |
| AC-4.10 to AC-4.15 | 25, 39, 43 | `tests/test_h_mad_phase5_scope.py::test_fr4_more` |
| AC-4.16 | 25, 39 | `tests/test_h_mad_phase5_scope.py::test_session_unknown`; the `[refused-top-level]` and unreadable-root ids of rows 1, 3, 4, 8, 14, 15, 17, 18, 24 |
| AC-5.1, AC-5.2 | 22, 23 | `tests/test_h_mad_phase5_scope.py::test_arming_write_variants` |
| AC-5.3 | 9, 22, 23 | rows 7, 12; `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule` |
| AC-5.4 | 22, 23 | rows 7, 12 `[inert-operand]`, `[inert-value]`; `tests/test_h_mad_phase5_scope.py::test_non_arming_writes_keep_decision` |
| AC-5.5 | 42, 44 | `tests/test_h_mad_phase5_scope.py::test_ungated_session_write_unaffected` |
| AC-5.6 | 9, 11 | `tests/test_h_mad_phase5_arming_inputs.py::test_arming_corpus_superset` (`[phase]` in Task 9; the two new fields in Task 11, once the writer can store them) |
| AC-6.1 to AC-6.3 | 21, 23, 24 | `tests/test_h_mad_phase5_scope.py::test_arming_file_refused` |
| AC-6.4 | 21, 23, 24, 30, 35, 38 | `tests/test_h_mad_phase5_scope.py::test_arming_file_no_record`; `[other-checkout]` of rows 6, 12, 19 |
| AC-6.5 | 21, 23, 24 | `tests/test_h_mad_phase5_scope.py::test_arming_file_unreadable_state`; `test_exempt_write_on_unreadable_chain_is_allowed[state-file]` |
| AC-6.6 | 10, 21, 23, 24 | `tests/test_h_mad_phase5_scope.py::test_fold_discriminator`; neighbouring documents of rows 6, 12, 19 |
| AC-6.7, AC-6.8 | 21, 23, 24, 30, 35, 38 | `tests/test_h_mad_phase5_scope.py::test_shared_state_file` (`SHARED_FILE_REFUSED` in S5; `SHARED_FILE_KEEPS` with each host's re-routing) |
| AC-7.1 to AC-7.4 | 52 | `tests/test_h_mad_phase5_scope_topologies.py` |
| AC-7.5 | 22, 23, 42, 44 | the refusal text asserted by the ids of rows 7, 12 |
| AC-7.6 | 55 | `tests/test_h_mad_phase5_scope_docs.py::test_no_documented_step6_or_step7` |
| AC-8.1 | 28, 35, 38, 39, 43, 48, 50 | `tests/test_h_mad_tdd_judge_scope.py::test_scope_agrees_with_hooks`, `::test_unreadable_agrees_with_hooks` |
| AC-8.2 | 28 | `tests/test_h_mad_tdd_judge_scope.py::test_scope_encoding` |
| AC-8.3 | 28, 39, 43 | `tests/test_h_mad_tdd_judge_scope.py::test_scope_allow_is_silent` |
| AC-8.4 | 26 | row 15 `[state]` |
| AC-9.1 | 48, 50 | `tests/test_h_mad_phase5_scope.py::test_planning_window` |
| AC-9.2 | 48, 50 | `tests/test_h_mad_phase5_scope.py::test_after_mark` |
| AC-9.3 | 48, 50 | `tests/test_h_mad_phase5_scope.py::test_stage_values_gate_shell` |
| AC-9.4 | 11 | `tests/test_h_mad_state_write_scope.py::test_stage_transitions` |
| AC-9.5 | 16 | `tests/test_h_mad_assemble_tdd_scope.py::test_planning_stage_wire`, `::test_planning_stage_halt` |
| AC-9.6 | 48, 50 | `tests/test_h_mad_phase5_scope.py::test_second_record_not_planning_gates` |
| AC-9.7 | 45 | row 13 |
| AC-9.8 | 43, 50 | row 9 workspace-mismatch ids |
| AC-10.1 | 1, every task that names a **Differential** line, 56 | `tests/test_h_mad_phase5_scope_differential.py::test_crossed_corpus` |
| AC-10.2 | 43 | `tests/test_h_mad_phase5_scope_differential.py::test_incident_replay` |
| AC-10.3 | 11 | `tests/test_h_mad_state_write_scope.py::test_older_writer_refuses_new_field` |
| AC-10.4 | 2, 23, 24 | the census; `_tree_b`; `GATE_KINDS` |
| AC-10.5 | 11 | `tests/test_h_mad_state_write_scope.py::test_older_arm_newer_write` |
| AC-10.6 | 11, 48 | `tests/test_h_mad_state_write_scope.py::test_newer_arm_older_write`, `::test_newer_exit_older_arm`; `tests/test_h_mad_phase5_scope.py::test_after_drop_undeclared` |
| AC-10.7 | 53 | `tests/test_h_mad_landing_lanes.py` |
| AC-11.1, AC-11.3 to AC-11.6 | 55 | `tests/test_h_mad_phase5_scope_docs.py` |
| AC-11.2 | 15 | `tests/test_h_mad_assemble_tdd_scope.py::test_checkout_mismatch_wire`, `::test_checkout_mismatch_halt` |

The map has 88 spec criteria: 9 of FR-1, 11 of FR-2, 7 of FR-3, 16 of FR-4, 6 of FR-5, 8 of FR-6, 6 of FR-7, 4 of FR-8, 8 of FR-9, 7 of FR-10 and 6 of FR-11.

---

## Task 1: Differential harness and oracle (S0)

**Production file**: `docs/03-analysis/probes/phase5-gate-feature-scope/differential.py`, `h-mad/tests/tdd_gate_support.py` (the test helper gains `host_decision`; `decision` is not edited)
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_differential.py`
**Task shape**: `new-behaviour`

**Description**: The harness that runs the three hooks and the judge of `7a3cca48` beside the tree's (convention 2), the corpus builder, and the oracle of the expected verdict (plan §"Convention Prerequisites", Expected verdict, steps 1 to 4). For every crossed case the oracle computes the verdict required of the tree before it reads the tree's answer: the old hook's verdict, under the same interpreter and to the same call, on a twin built a second time by the same builder (never copied), in which the classes of `CHANGES_IN_FORCE` for that surface have been made in the files and the environment. The builder gives each file and call a kind and checks each kind with git or `lstat` directly; class labels are computed from the fixture's facts, never from an outcome. The oracle and the builder import no module of either tree and run no hook or judge of the tree under test. The corpus is spec AC-10.1's crossing, with every malformed shape of spec AC-4.9 alone and beside a record without the new fields, the presence cases, and each variable of `VARIABLES` at the value plan §"AC-2.8 and the four variables" establishes for its host; it holds no record with the new fields and does not hold the case of spec FR-10's residual (OD-9 applies to its fixtures: see Task 28). Among its calls is one command under an allow line that FR-5 refuses on mention (`[mention-unknown-program]` of row 7), labelled D6. It holds `excluded-not-object` and `excluded-object-not-live`, the legacy-exception case of convention 12 and its readable control, on every surface. At S0 `CHANGES_IN_FORCE` is empty, so every twin is its fixture and every verdict equals the old tree's.

Verdicts are read per host (convention 3). `run_hook` decodes each answer with `tdd_gate_support.host_decision(host, result)`, which `differential.py` loads by path from `h-mad/tests/`; it is a test helper, not a module of `h-mad/scripts` or `h-mad/hooks`, so AC-1.2 holds, and the old and the new tree are decoded by the same function because the three output protocols are not changed by this feature. Before any twin is compared, each host's decoder is checked on that host's own baseline answers: an allow, a refusal and a malformed output, each produced by the real hook of `7a3cca48` or, for the malformed case, by a PATH shim standing in for the hook's interpreter that prints a broken answer. An ordinary agy allow (`{"decision": "allow"}` on stdout) must decode as `allow`, which `decision` alone reads as `invalid`; a codex refusal must decode as `deny` with its kind from the last `kind=([a-z0-9-]+)` of the reason, which `decision`'s `BLOCK kind=` pattern does not match, and a codex refusal with no `kind=` as `deny` with kind `""` (convention 3).

**Code structure**:
```python
SURFACES = ("codex-shell", "codex-write", "agy-shell", "agy-write", "claude")
CLASSES = ("D1", "D2", "D3", "D4", "D5", "D6", "D7")
BRANCHES = ("arming", "other")
CHANGES_IN_FORCE: dict[tuple[str, str], frozenset[str]]  # (surface, branch) -> classes landed; every value empty at S0
LEGACY_RAISE_LIFTED: frozenset[str]  # surfaces whose hook no longer raises on a not-object file outside its discovery; empty until Task 47
# each call's flag: spec.surface == "claude" or spec.surface in LEGACY_RAISE_LIFTED (convention 12)

class CaseSpec(NamedTuple):
    name: str
    surface: str
    kinds: tuple[str, ...]     # builder kinds, each checked with git or lstat
    branch: str                # "arming" or "other", from the call's facts (convention 12)
    call: dict                 # payload or command; paths relative to the fixture
    env: dict[str, str]

class Case(NamedTuple):
    spec: CaseSpec
    root: Path
    labels: frozenset[str]     # D1..D7 from the fixture's facts

class Verdict(NamedTuple):
    decision: str              # "allow" or "deny"
    kind: str
    git_processes: int

def resolve_interpreters(launchers: Sequence[str] | None = None) -> dict[str, str | None]: ...  # id -> executable, None for a named skip; by executable identity
def extract_old_tree(dest: Path, commit: str = "7a3cca48") -> Path: ...
def build_case(spec: CaseSpec, where: Path) -> Case: ...
def build_twin(spec: CaseSpec, where: Path, changes: frozenset[str], legacy_raise_lifted: bool) -> Case: ...
def run_hook(tree: Path, case: Case, interpreter: str) -> Verdict: ...
def expected_verdict(spec: CaseSpec, interpreter: str, changes: frozenset[str], scratch: Path, legacy_raise_lifted: bool = False) -> Verdict: ...  # changes: CHANGES_IN_FORCE[(spec.surface, spec.branch)]
def crossed_corpus() -> tuple[CaseSpec, ...]: ...
def main(argv: list[str] | None = None) -> int: ...  # DIFFERENTIAL: PASS cases=<n> | FAIL case=<name>; exit 0, or 2 on usage

# h-mad/tests/tdd_gate_support.py
def host_decision(host: str, result: subprocess.CompletedProcess) -> Outcome: ...  # host in ("claude", "codex", "agy")
```

**Tests and RED split** (all fail at RED: the module and `host_decision` do not exist):
- `tests/test_h_mad_phase5_scope_differential.py::test_supported_interpreters_are_the_parametrised_set` (1)
- `tests/test_h_mad_phase5_scope_differential.py::test_interpreter_resolution[alias-collapses|same-version-two-executables|missing-launcher]` (3), on scratch launchers: two launcher names for one executable give one id; two executables reporting version 3.11 give `py3.11` and `py3.11-2`; a launcher that is not on `PATH` gives a named skip.
- `tests/test_h_mad_phase5_scope_differential.py::test_host_decoder_controls[claude-allow|claude-deny|claude-malformed|codex-allow|codex-deny|codex-malformed|agy-allow|agy-deny|agy-malformed]` (9): each host's baseline allow decodes as `allow`, its refusal as `deny` with the hook's kind, and its malformed output as `invalid`. `[codex-deny]` decodes three baseline refusals of the hook of `7a3cca48`: one ending `kind=judge-error`, one production refusal whose kind is followed by `;` and its reason (decoded without the `;`), and the unreadable-state shell refusal, which carries no `kind=` (decoded `deny` with kind `""`, never `invalid`).
- `tests/test_h_mad_phase5_scope_differential.py::test_oracle_imports_no_tree_module` (1)
- `tests/test_h_mad_phase5_scope_differential.py::test_baseline_extraction_resolves_own_wrapper[old|new]` (2)
- `tests/test_h_mad_phase5_scope_differential.py::test_admission_control[<INTERPRETERS>-codex|<INTERPRETERS>-agy]` (12): under a live record a declared command alone and the same command after `hmad-dispatch run --timeout 60 --` are admitted by both sides; with the line taken out of the allowance file both refuse it.
- `tests/test_h_mad_phase5_scope_differential.py::test_builder_checks_each_kind` (1)
- `tests/test_h_mad_phase5_scope_differential.py::test_twin_is_built_not_copied` (1)
- `tests/test_h_mad_phase5_scope_differential.py::test_oracle_typed_verdicts[D1-control|D2-control|D3-control|D4-control|presence-<PRESENCE_CASES>|excluded-alone|excluded-beside-live-root|nested-beside-live-root|nested-target-inside|nested-in-excluded-tree|nested-below-fixtures|variable-beside-live-root]` (19): 4 isolated controls, each with its neighbour inside the id; 8 presence controls, one required verdict for every supported Python; 7 crossed cases with the verdicts plan §"Expected verdict" types. Each calls `expected_verdict` with every class in force, not with `CHANGES_IN_FORCE`.
- `tests/test_h_mad_phase5_scope_differential.py::test_crossed_corpus[<INTERPRETERS>-<SURFACES>]` (30): every case of the corpus for that interpreter and surface gives its expected verdict; the test names each failing case.

**Stated counts**: RED 79 failing, 0 passing; GREEN 79 passing (the file is new).

**Mutation rows** (`phase5_scope_differential.json`, 10):

| Name | Change | Killed by |
|---|---|---|
| `oracle-keeps-excluded-copy` | step 2 keeps a file in a git-excluded tree | `tests/test_h_mad_phase5_scope_differential.py::test_oracle_typed_verdicts[excluded-alone]` |
| `oracle-drops-every-file` | step 2 removes every state file | `tests/test_h_mad_phase5_scope_differential.py::test_oracle_typed_verdicts[excluded-beside-live-root]` |
| `oracle-loses-nested-keep-rule` | step 2 applies the outer root's D1 and D3 inside a nested checkout | `tests/test_h_mad_phase5_scope_differential.py::test_oracle_typed_verdicts[nested-target-inside]` |
| `oracle-skips-canonical-spelling` | step 3 leaves a symlinked `docs` in the twin | `tests/test_h_mad_phase5_scope_differential.py::test_oracle_typed_verdicts[presence-docs-symlink]` |
| `oracle-keeps-variables` | step 1 keeps the four variables | `tests/test_h_mad_phase5_scope_differential.py::test_oracle_typed_verdicts[variable-beside-live-root]` |
| `harness-wrapper-unchecked` | the `hmad-dispatch` resolution assertion is dropped | `tests/test_h_mad_phase5_scope_differential.py::test_baseline_extraction_resolves_own_wrapper[old]` |
| `oracle-imports-a-tree` | `differential.py` imports `h_mad_target_identity` | `tests/test_h_mad_phase5_scope_differential.py::test_oracle_imports_no_tree_module` |
| `agy-allow-read-by-claude-form` | `host_decision` reads agy with `decision`'s silent-allow test | `tests/test_h_mad_phase5_scope_differential.py::test_host_decoder_controls[agy-allow]` |
| `interpreters-first-by-version` | `resolve_interpreters` keeps the first launcher of each version | `tests/test_h_mad_phase5_scope_differential.py::test_interpreter_resolution[same-version-two-executables]` |
| `codex-kindless-deny-invalid` | `host_decision` reads a codex denial without `kind=` as `invalid` | `tests/test_h_mad_phase5_scope_differential.py::test_host_decoder_controls[codex-deny]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-1.1: `test_crossed_corpus` passes for every id with `CHANGES_IN_FORCE` empty, and fails, naming the case, when the twin of one case is given a change that is not in force.
- [ ] AC-1.2: `expected_verdict` reads no answer of the tree under test before it returns; `test_oracle_imports_no_tree_module` fails when `differential.py` imports any module of `h-mad/scripts` or `h-mad/hooks`.
- [ ] AC-1.3: A clone without `7a3cca48` makes `extract_old_tree` raise and the tests fail, with no skip.
- [ ] AC-1.4: `python3.11 docs/03-analysis/probes/phase5-gate-feature-scope/differential.py --bad-option` exits 2 with nothing on stdout; a run with no option prints one `DIFFERENTIAL:` line and exits 0.
- [ ] AC-1.5: All 10 mutation rows are caught, by their named tests.
- [ ] AC-1.6: On each host the decoder gives `allow`, `deny` with the hook's kind, and `invalid`, on that host's baseline allow, refusal and malformed output, before any twin is compared.

**Dependencies on other tasks**: None.

---

## Task 2: Measurement probes and the pin census (S0)

**Production file**: `docs/03-analysis/probes/phase5-gate-feature-scope/discovery_probe.py`, `docs/03-analysis/probes/phase5-gate-feature-scope/walk_probe.py`, `docs/03-analysis/probes/phase5-gate-feature-scope/timing.py`, `docs/03-analysis/probes/phase5-gate-feature-scope/pin_census.py`, `docs/03-analysis/probes/phase5-gate-feature-scope/mixtures.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_differential.py`
**Task shape**: `new-behaviour`

**Description**: The four probes of S0 (design §12; plan §"Order of work" S0), and the mixture harness S11 runs (plan §"Risks", the fast-forward row; §"Mixture corpora"). `discovery_probe.py` has the parts design §2, §6, §7 and §12 name as subcommands: `fx`, `fx2`, `disc`, `ev2`, `proto2`, `failclosed`, `chain`, `names`, `arming`. `walk_probe.py` is the text of the walk probe in plan §"Tradeoffs to preserve", committed as it stands there. `timing.py` takes `--old TREE [--repo DIR] [--runs 20] [--hook codex|agy|claude]... [--samples FILE]` (every hook when `--hook` is not given; `--old` is required in every mode, and is not read when `--samples` is given) and prints `TIMING: max_added_ms=<n> bound=300` over the cases the bound covers, the medians of a whole hook call, old side and new, on a document, a production and a state-file target in the root checkout, and, on the `codex-shell` and `agy-shell` surfaces, one real command each (a read-only `git status --short`), once with no live record and once with a live root record, and one line per case (design §12). Both record states are made only on the scratch fixture, where the probe writes its own store inside its scratch directory. Under `--repo DIR`, where the probe only reads (design §12), it writes no record and runs each shell command once, in the record state the root state file of DIR holds at that moment, which the case line names as `record=none` or `record=live`; so the pair of record states is measured in scratch, and a `--repo` run measures the repository as it stands; `--samples FILE` reads each case's old and new medians from a JSON file in place of running the hooks, so the aggregation can be tested on fixed numbers; and, apart from the bound, one `TIMING-SECOND-CHECKOUT: added_ms=<n>` line per hook for an explicit target in a second checkout of the same repository, whose own discovery is a second one (plan §"Tradeoffs to preserve", the owed readings). `mixtures.py --old TREE --new TREE --set gates|writes|staging` assembles, in scratch, every mixture of the set's files (each file from the old or the new tree; the sets and their corpora are plan §"Risks" and §"Mixture corpora"), runs the set's corpus through the set's entry points on each, and prints `MIXTURES: PASS set=<s> mixtures=<n> cases=<m>` or `MIXTURES: FAIL set=<s> mixture=<the files taken from the new tree> case=<name>`, a failure being a case that both whole trees refuse and the mixture allows; `--set-file FILE` reads a set (its files, entry command and corpus) from a JSON file, which is how the tests drive it on a toy tree. `pin_census.py` is the census of plan §"Existing tests and mutation specs affected", with `--control`, which drives each class by hand and must make every detector log, including the detector of FR-6 referents that plan's table says S0 adds. Every probe but `walk_probe.py` exits 0 for a reading and 2, with nothing on stdout, for a usage or internal error; each imports the scripts by a path relative to its own file. Once the tests are green the task records three readings, each a probe run, and commits none of their output: `pin_census.py --control` and then `pin_census.py`, compared row by row with the plan's table, any difference being stopped on and shown to the operator before an expectation is edited; `timing.py --old "$OLD" --runs 20`, the old side's reading, `$OLD` being a temporary directory filled by `git archive 7a3cca48 h-mad/hooks h-mad/scripts h-mad/bin | tar -x -C "$OLD"`; and one hook call timed per interpreter of `INTERPRETERS`, which sizes the differential corpus (plan §"Risks", the differential row).

OD-8 is answered here, as measurement: from this commit the design's prototype readings are re-runnable, with `python3.11 docs/03-analysis/probes/phase5-gate-feature-scope/discovery_probe.py disc "$PWD" 5`, run from the repository root, for the discovery readings and the other parts for the rest (the design audit sidecar's command). The readings marked there as not re-runnable from this repository stay so.

**Code structure**:
```python
# discovery_probe.py
PARTS = ("fx", "fx2", "disc", "ev2", "proto2", "failclosed", "chain", "names", "arming")
def main(argv: list[str] | None = None) -> int: ...
# timing.py
def main(argv: list[str] | None = None) -> int: ...  # TIMING: max_added_ms=<n> bound=300; --samples FILE for fixed medians
# pin_census.py
def main(argv: list[str] | None = None) -> int: ...  # --control first
# mixtures.py
def mixtures(files: Sequence[str]) -> Iterator[frozenset[str]]: ...  # each subset taken from the new tree, the empty and the whole set included
def main(argv: list[str] | None = None) -> int: ...  # MIXTURES: PASS ... | FAIL ...
```

**Tests and RED split** (all fail at RED: the probes do not exist):
- `tests/test_h_mad_phase5_scope_differential.py::test_probe_usage_error_exits_2_with_empty_stdout[discovery_probe|timing|pin_census|mixtures]` (4)
- `tests/test_h_mad_phase5_scope_differential.py::test_discovery_probe_part_reads[fx|fx2|disc|ev2|proto2|failclosed|chain|names|arming]` (9): each part, on a scratch layout, exits 0 with one reading line.
- `tests/test_h_mad_phase5_scope_differential.py::test_pin_census_control_logs_every_class` (1)
- `tests/test_h_mad_phase5_scope_differential.py::test_timing_probe_prints_its_token[every-hook|one-hook|second-checkout-apart]` (3): `[every-hook]` and `[one-hook]` are real-hook smoke runs: with `--runs 1` and `--repo` naming a scratch repository the test builds (with a second checkout), `[every-hook]` prints a `TIMING:` line over the three hooks and one case line for each of the three targets on each hook and for each shell command in each of two runs on that repository, once before and once after the test itself writes a live root record into it, the shell lines naming `record=none` in the first run and `record=live` in the second, with a sha256 listing of the repository's files equal before and after each run (the probe writes nothing under `--repo`), and `[one-hook]`, with `--hook claude`, over the Claude hook alone; `[second-checkout-apart]` runs with `--samples` holding fixed medians in which the second checkout's added time is larger than every bounded case's, and asserts that `max_added_ms` equals the largest bounded case's added time and that the second checkout's value is printed only on its `TIMING-SECOND-CHECKOUT:` line.
- `tests/test_h_mad_phase5_scope_differential.py::test_mixtures_probe[identical-trees-pass|failing-mixture-named|every-mixture-run]` (3), on a toy set of two files given by `--set-file`: two identical trees pass; a new tree whose two files each refuse a case but whose mixture of one old and one new file allows it fails, naming that mixture and case; the count of mixtures run is 4.

**Stated counts**: RED 20 failing, 79 passing (Task 1's nodes in the same file); GREEN 99 passing.

**Mutation rows** (`phase5_scope_differential.json`, 4):

| Name | Change | Killed by |
|---|---|---|
| `census-control-skips-d7` | the control does not drive D7 | `tests/test_h_mad_phase5_scope_differential.py::test_pin_census_control_logs_every_class` |
| `probe-usage-exit-0` | `discovery_probe.py` exits 0 on a usage error | `tests/test_h_mad_phase5_scope_differential.py::test_probe_usage_error_exits_2_with_empty_stdout[discovery_probe]` |
| `timing-second-checkout-bounded` | the second checkout's case is counted in `max_added_ms` | `tests/test_h_mad_phase5_scope_differential.py::test_timing_probe_prints_its_token[second-checkout-apart]` |
| `mixtures-whole-trees-only` | only the empty and the whole subset are run | `tests/test_h_mad_phase5_scope_differential.py::test_mixtures_probe[failing-mixture-named]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-2.1: `walk_probe.py` is byte-identical to the python block of plan §"Tradeoffs to preserve", "The mechanism is Phase 4's".
- [ ] AC-2.2: The census reading is compared with each row of the plan's table, and the comparison is in the task's report; no expectation of an existing test is edited in this task.
- [ ] AC-2.3: The 4 mutation rows are caught.

**Dependencies on other tasks**: Task 1 (the extracted old tree and the interpreter resolution).

---

## Task 3: Git environment and pure readers (S1)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `new-behaviour`

**Description**: The shared functions that call no git and judge no applicability (design §1, §3, §5): the environment every git call of this feature is given, the one reader of a state file and the one comparison with `step5`, the one reading of a stored stage, the always-true stage predicate S8 uses, and the decoder of rule 5. Nothing calls them yet. `git_environment()` returns a copy of `os.environ` without `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR` and `GIT_CEILING_DIRECTORIES`, with `LC_ALL=C`. `read_state` returns one of `read`, `absent`, `unreadable`, `not-object`, reading by `_read_regular_text`, with the judge's tokens of today (`_state_at`, `h_mad_tdd_judge.py`): `absent` only when `lstat` finds no entry (a dangling link is `unreadable` with `FileNotFoundError`, as `_state_at` gives it); a FIFO, a directory or another non-regular file is `unreadable` with `error` `not-a-regular-file`; any other read or parse failure is `unreadable` with the exception's type name; a top level that is not an object, and an `orchestrator_state` that is not an object, are both `not-object` with `error` `not-an-object`. `exception` keeps what today's `_state_status` would raise, and is `None` for everything it does not: for a top level that is not an object, the `AttributeError` that `state.get` raises on it (`read_state` evaluates `data.get` inside a `try` and keeps the error); for a malformed `orchestrator_state` map, which `_state_status` reads as `unknown` without raising, `None`; for a read or parse failure, `None` when the exception is an instance of `(OSError, UnicodeDecodeError, json.JSONDecodeError)`, the tuple `_state_status` catches (`h-mad/scripts/h_mad_target_identity.py:327`), and otherwise the exception itself, beside the `unreadable` status and its type name. One input reaches that last branch under every interpreter of `INTERPRETERS`: a file of 1,000,000 nested JSON arrays (`"[" * 1000000 + "]" * 1000000`), on which `json.loads` raises `RecursionError` (measured on the machine of record under 3.9.6, 3.11.8, 3.12.16, 3.13.18, 3.14.10 and 3.15.2; at a depth of 100,000, 3.14 and 3.15 parse it, so the depth is load-bearing). `command_directory` never raises (design §5).

One boundary for filesystem path values, which every later task keeps. It covers exactly the functions a Claude-hook process reaches with a `str` root or target from `sys.argv`: `read_state` (this task), `checkout_of` and `session_checkout` (Task 4), `walk_state_files`, `session_state_files`, `chain_state_files` and `TreeOracle` (Task 5), `phase5_scan` and `Scan.write` (Task 6), `arming_target` (Task 10), `_any_phase5_status` and `unscoped_judge` (Task 20), and `emit_arming` (Tasks 24 and 30). Each takes its root, target or base as a `PathArg` (`str` or an `os.PathLike[str]`) and applies `os.fspath` once at its entry, so the values inside the module are `str`; the private helpers they call (`_target_names`, `_same_component`) take `str`. `_any_phase5_status` and `unscoped_judge` apply `Path(...)` once at their entry instead while their walk calls `Path.rglob`, which for `_any_phase5_status` lasts until Task 47 replaces that walk with the scan. `emit_arming` converts nothing itself: it passes its root unconverted to the function it calls, `unscoped_judge` until Task 30 and the scan from Task 30, which applies the conversion at its own entry (Task 24). `test_path_parameters_accept_str_and_path` gets one id per function of that list, in the task that adds it, each asserting that a `str` and a `Path` spelling of one fixture give equal answers. Two kinds of parameter are outside the rule. The FR-5 functions (`_safe_executable`, Task 7; `writer_arguments`, `leads_to_writer`, `arming_mention`, `arming_write`, Task 9) are reached only from the codex and agy hooks, which hold `Path` roots, and keep `root: Path | None` as `_safe_argv` does today, with no id. Raw policy inputs are not paths at the boundary and are never converted: a stored field value (`recorded_checkout`'s `value`) is valid only as a non-empty string (a `Path` object is `field-invalid`), and a payload's command directory (`Scan.shell`'s `directory`, `command_directory`'s value) is known only as a string (anything else is the malformed directory). `test_raw_inputs_are_not_paths` holds that, one id per such parameter (Tasks 4 and 6), on a usable checkout where the two classifications differ: the `str` spelling is usable or matches, the `Path` spelling of the same text is refused or unknown. The hooks hold `Path` roots (codex, agy, the judge) or `str` arguments from `sys.argv` (the Claude hook's processes), and each passes what it holds without converting.

**Code structure**:
```python
PathArg = Union[str, "os.PathLike[str]"]

class StateRead(NamedTuple):
    path: str
    status: str                 # "read" | "absent" | "unreadable" | "not-object"
    data: object
    error: str
    exception: BaseException | None

class LiveRecord(NamedTuple):
    feature: str
    state_file: str
    data: dict                  # the record as stored

class Status(NamedTuple):
    value: str                  # "active" | "unknown" | "inactive"; compared by value, never tested for truth
    applied: tuple              # the entries that apply (and, for Scan.shell, gate), in discovery order (Task 6)

INACTIVE = Status("inactive", ())

def git_environment() -> dict[str, str]: ...
def read_state(path: PathArg) -> StateRead: ...
def live_records(read: StateRead) -> tuple[LiveRecord, ...]: ...
def stage_gates_shell(record: LiveRecord) -> bool: ...
def every_stage(record: LiveRecord) -> bool: ...
def command_directory(args: object, key: str, decode: Callable[[], object], absent: object) -> object: ...
```

**Tests and RED split** (all fail at RED: the names do not exist):
- `tests/test_h_mad_phase5_scope.py::test_git_environment_drops_the_four_variables[<VARIABLES>]` (4)
- `tests/test_h_mad_phase5_scope.py::test_git_environment_sets_lc_all_c` (1)
- `tests/test_h_mad_phase5_scope.py::test_git_environment_leaves_os_environ_alone` (1)
- `tests/test_h_mad_phase5_scope.py::test_read_state_status[read|absent|unreadable-fifo|unreadable-unparsable|not-object]` (5): `[unreadable-fifo]` asserts `error` `not-a-regular-file`; `[unreadable-unparsable]` reads two files, an unparsable one (`error` `JSONDecodeError`, `exception` `None`) and the file of 1,000,000 nested arrays (`error` `RecursionError`, `exception` a `RecursionError`); `[not-object]` reads two files, a JSON list (`error` `not-an-object`, `exception` an `AttributeError`) and an object whose `orchestrator_state` is a list (`error` `not-an-object`, `exception` `None`).
- `tests/test_h_mad_phase5_scope.py::test_live_records[step5|other-phase|record-not-object|orchestrator-state-not-object]` (4)
- `tests/test_h_mad_phase5_scope.py::test_stage_gates_shell[absent|null|planning|implementing|unknown-string|non-string]` (6)
- `tests/test_h_mad_phase5_scope.py::test_every_stage_is_true` (1)
- `tests/test_h_mad_phase5_scope.py::test_command_directory[absent|null|empty|number|list|object|string|decode-raises]` (8)
- `tests/test_h_mad_phase5_scope.py::test_status_is_compared_by_value` (1)
- `tests/test_h_mad_phase5_scope.py::test_path_parameters_accept_str_and_path[read_state]` (1)
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_function_has_one_definition_in_the_identity_module[git_environment|read_state|live_records|stage_gates_shell|every_stage|command_directory]` (6)
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_constant_is_assigned_in_the_identity_module[INACTIVE]` (1)

**Stated counts**: RED 39 failing, 29 passing (the nodes `test_h_mad_shared_gate_policy.py` holds at `bb88b6cc`); GREEN 68 passing.

**Mutation rows** (`phase5_scope.json`, 7):

| Name | Change | Killed by |
|---|---|---|
| `git-env-keeps-git-dir` | `GIT_DIR` is not removed | `tests/test_h_mad_phase5_scope.py::test_git_environment_drops_the_four_variables[GIT_DIR]` |
| `git-env-no-lc-all` | `LC_ALL` is not set | `tests/test_h_mad_phase5_scope.py::test_git_environment_sets_lc_all_c` |
| `stage-planning-gates` | `"planning"` gates the shell | `tests/test_h_mad_phase5_scope.py::test_stage_gates_shell[planning]` |
| `stage-absent-exempt` | an absent stage is exempt | `tests/test_h_mad_phase5_scope.py::test_stage_gates_shell[absent]` |
| `command-directory-null-is-absent` | a null key gives `absent` | `tests/test_h_mad_phase5_scope.py::test_command_directory[null]` |
| `command-directory-decode-propagates` | an exception of `decode` escapes | `tests/test_h_mad_phase5_scope.py::test_command_directory[decode-raises]` |
| `live-records-any-phase` | every record is live | `tests/test_h_mad_phase5_scope.py::test_live_records[other-phase]` |

**Existing specs to re-anchor**: none (no existing function is edited).

**Acceptance Criteria**:
- [ ] AC-3.1: `command_directory(args, key, decode, absent)` returns `MALFORMED_WORKDIR` for a present key holding anything but a non-empty string, null and `""` included, and when `decode` raises; `decode()` for a non-empty string; `absent` when the key is not in `args`.
- [ ] AC-3.2: `stage_gates_shell` is false exactly for a stored `"planning"`.
- [ ] AC-3.3: The full suite and `--check-anchors` pass; the 7 rows are caught.

**Dependencies on other tasks**: None.

---

## Task 4: Checkout identity (S1)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `new-behaviour`

**Description**: `checkout_of` with its three answers, the rule for a path with a `.git` component, `session_checkout`, and `recorded_checkout` with the reasons in design §4's order. The `[checkout]` call is `rev-parse --show-toplevel` in the deepest existing directory, run with `--no-optional-locks`, reading bytes, bounded at 2 s, one trailing newline removed and the answer passed through `canonical_directory` (design §1). This task gives that call no environment argument; Task 5 adds `env=git_environment()` to it, which is row 29's `[checkout]` connection. Until then the call inherits the test's environment, so every `test_checkout_of` id sets `LC_ALL=C` in its own environment (`monkeypatch.setenv`) before it runs, which makes the exact English diagnostic this task tests a precondition of the fixture and not of the inherited locale; Task 5's `test_checkout_of_sets_its_locale` then holds the call under an inherited locale that is not `C`. A missing git, an exit not listed, or an exhausted budget is "cannot answer". `recorded_checkout` tests for a directory with `os.stat` before it opens or asks, so a FIFO cannot block and a file of mode 000 is `not-a-checkout`.

**Code structure**:
```python
class Checkout(NamedTuple):
    top: str | None
    answered: bool

def checkout_of(path: PathArg) -> Checkout: ...
def session_checkout(root: PathArg) -> Checkout: ...
def recorded_checkout(value: object, session: Checkout | None = None) -> tuple[str | None, str]: ...
```

**Tests and RED split** (all fail at RED: the names do not exist):
- `tests/test_h_mad_phase5_scope.py::test_checkout_of[checkout|no-work-tree|message-alone|no-entry-alone|inside-valid-dot-git|inside-damaged-dot-git|bare-repository|empty-dot-git-directory|git-missing|git-timeout]` (10): answer 2 by its whole message and by each of its two conditions alone (`message-alone`, `no-entry-alone` give "cannot answer").
- `tests/test_h_mad_phase5_scope.py::test_session_checkout[canonicalisable|refused-top-level-root]` (2)
- `tests/test_h_mad_phase5_scope.py::test_recorded_checkout_reason[absent|null|not-string|empty|relative|not-encodable|missing|through-a-file|stat-error|regular-file|mode-000-file|fifo|canonical-refuses|git-cannot-answer|bare-repository|no-work-tree|sub-directory|inside-dot-git|usable|equals-session-no-git]` (20): `fifo` returns within 1 s and the FIFO is not opened; `equals-session-no-git` starts no git process, counted by a PATH shim.
- `tests/test_h_mad_phase5_scope.py::test_path_parameters_accept_str_and_path[checkout_of|session_checkout]` (2)
- `tests/test_h_mad_phase5_scope.py::test_raw_inputs_are_not_paths[recorded_checkout]` (1): on a usable checkout, the `str` value gives its canonical path and a `Path` object of the same text gives `field-invalid` (Task 3's boundary).
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_function_has_one_definition_in_the_identity_module[checkout_of|session_checkout|recorded_checkout]` (3)

**Stated counts**: RED 38 failing, 68 passing (Task 3's 32 and 7 nodes and the 29 of `bb88b6cc`); GREEN 106 passing.

**Mutation rows** (`phase5_scope.json`, 6):

| Name | Change | Killed by |
|---|---|---|
| `checkout-message-alone` | answer 2 without the `.git` entry test | `tests/test_h_mad_phase5_scope.py::test_checkout_of[message-alone]` |
| `checkout-entry-alone` | answer 2 without the whole-message test | `tests/test_h_mad_phase5_scope.py::test_checkout_of[no-entry-alone]` |
| `recorded-asks-before-stat` | the directory test moves after the git call | `tests/test_h_mad_phase5_scope.py::test_recorded_checkout_reason[fifo]` |
| `recorded-no-session-shortcut` | a value equal to the session checkout is asked of git | `tests/test_h_mad_phase5_scope.py::test_recorded_checkout_reason[equals-session-no-git]` |
| `recorded-missing-is-invalid` | `FileNotFoundError` gives `field-invalid` | `tests/test_h_mad_phase5_scope.py::test_recorded_checkout_reason[missing]` |
| `session-checkout-asks-git` | a root `canonical_directory` refuses is asked of git | `tests/test_h_mad_phase5_scope.py::test_session_checkout[refused-top-level-root]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-4.1: `checkout_of` gives `top=None, answered=True` only when git exits 128 with exactly `fatal: not a git repository (or any of the parent directories): .git` under `LC_ALL=C` and no `.git` entry of any type is found by `lstat` at or above the directory; an `lstat` error other than absence counts as an entry.
- [ ] AC-4.2: `recorded_checkout` returns the reasons of design §4 in its order; a usable value returns its canonical path.
- [ ] AC-4.3: The 6 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 3.

---

## Task 5: State-file discovery (S1)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_target_identity.py:checkout_of` → `git_environment`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[checkout]`
**WIRE 2**: `h-mad/scripts/h_mad_target_identity.py:TreeOracle` → `git_environment`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[ignored]`
**WIRE 3**: `h-mad/scripts/h_mad_target_identity.py:TreeOracle` → `git_environment`
**WIRE-PIN 3**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[index]`
**WIRE 4**: `h-mad/scripts/h_mad_target_identity.py:TreeOracle` → `git_environment`
**WIRE-PIN 4**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[head]`
**WIRE 5**: `h-mad/scripts/h_mad_target_identity.py:TreeOracle` → `git_environment`
**WIRE-PIN 5**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[unborn]`

**Description**: Row 29 (S1, environment): every git call of the shared functions is given `git_environment()`. The task builds the discovery of design §2 (`TreeOracle` with its one streaming `[ignored]` process and its content set from `[index]`, `[head]` and `[unborn]`; the breadth-first walk; the chain) and passes the environment at the four calls it makes and at Task 4's `[checkout]` call. Wires 2 to 5 are the four call sites inside `TreeOracle`: `[ignored]` where the streaming process is started, `[index]`, `[head]` and `[unborn]` where the content set is read. Each pin sets one variable of `VARIABLES` to a value that changes git's answer for that call, asks git directly with it set and unset and fails if the two answers agree, and asserts that the function's answer equals the one with no variable set (plan §"AC-2.8 and the four variables"). At RED `[checkout]` fails by that assertion, `checkout_of` existing without the environment; the other four fail because `TreeOracle`, the caller this task creates, is absent while the callee `git_environment` resolves (Task 3), the one missing-symbol RED phase5-substeps 5d admits for a pin. The structural test `test_every_git_call_passes_the_git_environment[identity]` lands here; its hook ids land in Tasks 18 and 19, and `_outside_every_work_tree` of the Claude hook is its one exclusion by name (plan §"What is reused").

OPEN-DECISION: OD-11, `wait` after `kill` has no timeout, and the bounded calls run by `subprocess.run` have the same shape — resolve in 5d. Named implementation: one private helper, `_bounded_git(argv, cwd, budget, env=None)`, runs every bounded git call of this module with `Popen` and `communicate`, passing `env` through to `Popen` (`None` inheriting, as `Popen` does), and each bounded call site passes its own `env=git_environment()` (the `[checkout]`, `[index]`, `[head]` and `[unborn]` calls), so removing that argument at one site changes that call alone and each `env-*-dropped` row reaches its own pin; its timeout what is left of the 2 s budget, then on expiry `kill()` and `wait(timeout=1.0)`, and on a second expiry abandons the child and answers "cannot answer"; the streaming process's failed exchange uses the same `kill()` and `wait(timeout=1.0)`. A real child killed by `SIGKILL` is reaped at once, so no real child can reach the second expiry; `test_wait_after_kill_is_bounded` therefore drives it in process, with `subprocess.Popen` in the identity module replaced (by `monkeypatch.setattr` on the module's own `subprocess` reference) by a fake process whose `communicate` and first exchange time out and whose `wait` raises `subprocess.TimeoutExpired` when it is given a timeout and, when it is given none, blocks on `release`, a `threading.Event` of the test. The test runs the call in a thread started with `daemon=True` and asserts, for `[bounded-call]` (`checkout_of`) and `[streaming-exchange]` (a scan's first exchange), that the call returns within 5 s with "cannot answer" (or, for the scan, every candidate counted), that `kill` was called once, and that `wait` was given `timeout=1.0`; in a `finally` block it then sets `release` and joins the thread (`join(timeout=5)`), so under a mutant that waits with no timeout the 5 s assertion fails and the blocked worker is released and ends before pytest does. `test_streaming_child_reaped` keeps the real child: after a failed exchange the direct child has exited and been reaped.

Ruled (OD-12, the operator, 2026-11-26, answer (a)): `TreeOracle.close()` closes the process's input and reaps it, and only tests call it; production never does, so the operator's ruling "Take the ending out" (design v1.9) stands. Every new in-process test that starts an oracle passes its own `oracles` mapping and closes each in teardown, and `test_oracle_no_resource_warning` runs a discovery under `warnings.simplefilter("always", ResourceWarning)` with that teardown and `gc.collect()` and finds no warning. Existing in-process callers are left as they are.

Ruled (OD-13, the operator, 2026-11-26, answer (a), "Take the ending out"): a failed exchange kills and reaps the streaming process's direct child only (design §2: "the direct child is killed and reaped (`kill`, `wait`)"); the process is started without `start_new_session` and no process group is signalled. When the direct child is a wrapper, what the wrapper started, if it is not git and ignores the closing of its input, is the stated residual of design §2 ("a launch that is not git and ignores that closing"), and no test builds that case.

**Code structure**:
```python
class Walk(NamedTuple):
    files: tuple[str, ...]
    errors: tuple[tuple[str, str], ...]   # (directory or candidate, error name)

class TreeOracle:
    def __init__(self, root: PathArg) -> None: ...
    def excluded(self, relative: str) -> bool: ...
    def close(self) -> None: ...          # tests only (OD-12)

def walk_state_files(root: PathArg, oracles: dict[str, TreeOracle] | None = None) -> Walk: ...
def session_state_files(root: PathArg, oracles: dict[str, TreeOracle] | None = None) -> tuple[str, ...]: ...
def chain_state_files(root: PathArg, target: PathArg | None, oracles: dict[str, TreeOracle] | None = None) -> tuple[str, ...]: ...
```

**Tests and RED split** (informational for a wiring task; every new test fails at RED, `[checkout]` and `test_checkout_of_sets_its_locale` by assertion and the rest because the discovery functions do not exist):
- `tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[checkout|ignored|index|head|unborn]` (5)
- `tests/test_h_mad_phase5_scope.py::test_oracle_behaviour[started-before-first-listing|started-with-live-record|no-second-process-after-failed-first|ancestor-sent-once|nothing-below-excluded-sent|re-included-directory|content-index-only|content-head-only|content-other-case|no-commit|damaged-ref|more-than-a-pipe|traversal-delayed-over-many-listings|traversal-delayed-in-one-listing|exchanges-sum-past-budget]` (15), the oracle cases of design §Test Strategy.
- `tests/test_h_mad_phase5_scope.py::test_git_ends_partway[between-batches|during-content-call|inside-second-batch|inside-first-batch|later-listing|index-fails|head-fails-with-commit]` (7), on the layouts of design §Test Strategy, each asserting the exact files returned beside the run in which git answers everything.
- `tests/test_h_mad_phase5_scope.py::test_streaming_child_reaped` (1)
- `tests/test_h_mad_phase5_scope.py::test_wait_after_kill_is_bounded[bounded-call|streaming-exchange]` (2), OD-11's named implementation.
- `tests/test_h_mad_phase5_scope.py::test_checkout_of_sets_its_locale` (1): with the inherited environment holding `LC_ALL=de_DE.UTF-8` and a PATH git shim that prints the exact English diagnostic of answer 2 only when its own environment holds `LC_ALL=C` (and a translated one otherwise), `checkout_of` of a directory in no work tree gives `top=None, answered=True`; at RED it gives "cannot answer", the call inheriting the locale.
- `tests/test_h_mad_phase5_scope.py::test_path_parameters_accept_str_and_path[walk_state_files|session_state_files|chain_state_files|TreeOracle]` (4)
- `tests/test_h_mad_phase5_scope.py::test_walk_rules[root-file-first|listing-error|symlink-child-dropped|tests-dropped|fixtures-dropped|dot-git-holder-dropped|docs-symlink-followed|p-symlink-not-followed|lstat-error-counts|excluded-not-listed|root-not-a-directory]` (11)
- `tests/test_h_mad_phase5_scope.py::test_chain_state_files[outside-root|nested-cut|sub-project-no-extra-process|nested-own-oracle]` (4)
- `tests/test_h_mad_phase5_scope.py::test_presence_case[<PRESENCE_CASES>-scan|<PRESENCE_CASES>-chain]` (16)
- `tests/test_h_mad_phase5_scope.py::test_discovery_unit[<DISCOVERY_CASES>]` (16)
- `tests/test_h_mad_phase5_scope.py::test_oracle_no_resource_warning` (1)
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_function_has_one_definition_in_the_identity_module[walk_state_files|session_state_files|chain_state_files]` (3)
- `tests/test_h_mad_shared_gate_policy.py::test_every_git_call_passes_the_git_environment[identity]` (1)

**Stated counts** (whole files, informational): RED 87 failing, 106 passing (the 67 and 39 nodes Tasks 3 and 4 and `bb88b6cc` leave in `test_h_mad_phase5_scope.py` and `test_h_mad_shared_gate_policy.py`; the wires file is new); GREEN 193 passing.

**Mutation rows** (28): `phase5_scope_wires.json` (10) and `phase5_scope.json` (18).

| Name | Change | Killed by |
|---|---|---|
| `env-checkout-dropped` | `[checkout]` runs with the inherited environment | `tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[checkout]` |
| `env-checkout-elsewhere` | `[checkout]` is given an environment naming another checkout | `tests/test_h_mad_phase5_scope.py::test_checkout_of[checkout]` |
| `env-ignored-dropped` | as above, `[ignored]` | `tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[ignored]` |
| `env-ignored-elsewhere` | as above, `[ignored]` | `tests/test_h_mad_phase5_scope.py::test_discovery_unit[excluded-live]` |
| `env-index-dropped` | as above, `[index]` | `tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[index]` |
| `env-index-elsewhere` | as above, `[index]` | `tests/test_h_mad_phase5_scope.py::test_oracle_behaviour[content-index-only]` |
| `env-head-dropped` | as above, `[head]` | `tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[head]` |
| `env-head-elsewhere` | as above, `[head]` | `tests/test_h_mad_phase5_scope.py::test_oracle_behaviour[content-head-only]` |
| `env-unborn-dropped` | as above, `[unborn]` | `tests/test_h_mad_phase5_scope_wires.py::test_git_environment_wire[unborn]` |
| `env-unborn-elsewhere` | as above, `[unborn]` | `tests/test_h_mad_phase5_scope.py::test_oracle_behaviour[no-commit]` |
| `oracle-excluded-is-ignored` | `excluded = ignored` | `tests/test_h_mad_phase5_scope.py::test_oracle_behaviour[content-index-only]` |
| `oracle-never-excluded` | `excluded` always false | `tests/test_h_mad_phase5_scope.py::test_oracle_behaviour[nothing-below-excluded-sent]` |
| `oracle-batch-unbounded` | one batch for a whole listing | `tests/test_h_mad_phase5_scope.py::test_oracle_behaviour[more-than-a-pipe]` |
| `oracle-budget-per-wait` | each wait gets the whole 2 s | `tests/test_h_mad_phase5_scope.py::test_oracle_behaviour[exchanges-sum-past-budget]` |
| `oracle-answered-recounted` | a path answered before git ended counts | `tests/test_h_mad_phase5_scope.py::test_git_ends_partway[inside-second-batch]` |
| `oracle-first-batch-stands` | a partly answered first batch keeps its arrived records | `tests/test_h_mad_phase5_scope.py::test_git_ends_partway[inside-first-batch]` |
| `oracle-kill-dropped` | the failed exchange does not `kill` | `tests/test_h_mad_phase5_scope.py::test_streaming_child_reaped` |
| `oracle-wait-dropped` | the failed exchange does not `wait` | `tests/test_h_mad_phase5_scope.py::test_streaming_child_reaped` |
| `bounded-call-wait-unbounded` | the bounded call's `wait` after `kill` is given no timeout | `tests/test_h_mad_phase5_scope.py::test_wait_after_kill_is_bounded[bounded-call]` |
| `streaming-wait-unbounded` | the failed exchange's `wait` after `kill` is given no timeout | `tests/test_h_mad_phase5_scope.py::test_wait_after_kill_is_bounded[streaming-exchange]` |
| `walk-lists-before-answer` | a directory is listed before `excluded` answers | `tests/test_h_mad_phase5_scope.py::test_oracle_behaviour[started-before-first-listing]` |
| `walk-symlink-child-kept` | a symlinked child is walked | `tests/test_h_mad_phase5_scope.py::test_walk_rules[symlink-child-dropped]` |
| `walk-tests-kept` | `tests` is walked | `tests/test_h_mad_phase5_scope.py::test_walk_rules[tests-dropped]` |
| `walk-fixtures-kept` | `fixtures` is walked | `tests/test_h_mad_phase5_scope.py::test_walk_rules[fixtures-dropped]` |
| `walk-dot-git-holder-kept` | a child holding `.git` is walked | `tests/test_h_mad_phase5_scope.py::test_walk_rules[dot-git-holder-dropped]` |
| `walk-p-symlink-followed` | a symlinked `P` is a candidate | `tests/test_h_mad_phase5_scope.py::test_walk_rules[p-symlink-not-followed]` |
| `walk-lstat-error-dropped` | an `lstat` error other than absence drops the candidate | `tests/test_h_mad_phase5_scope.py::test_walk_rules[lstat-error-counts]` |
| `chain-not-cut-at-nested` | the chain is not cut at a nested checkout | `tests/test_h_mad_phase5_scope.py::test_chain_state_files[nested-cut]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-5.1: Each of the five git calls of design §1 passes `env=git_environment()`, and each pin fails when only that argument is removed.
- [ ] AC-5.2: A whole scan starts at most four git processes, and at a root in no work tree one, counted by a PATH shim in `test_oracle_behaviour`.
- [ ] AC-5.3: When git ends partway, an answered path keeps its answer and every other candidate counts; a partly answered first batch counts whole (design §2).
- [ ] AC-5.4: All 28 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 3, 4.

---

## Task 6: Applicability and the scan (S1)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `new-behaviour`

**Description**: `applicable` with its one order of reasons (design §5), the `Scan` that holds a root's files, reads, live records, oracles and memoised checkout calls, and its three answers `session()`, `write(target)` and `shell(directory, gates)`; `phase5_scan(root)`; `describe`; and the `SessionStatus` class, which Task 20 begins to return. A `Status`'s `applied` is filtered and ordered: the entries of `applicable` whose `applies` is true and, for `shell`, for whose record `gates(record)` is true, in discovery order (the order of the scan's files, then of the records in each file); so `applied[0]`, which Tasks 42 and 44 pass to `arming_refusal`, is the first record that applies and gates, never an entry that does not. `Scan.write` takes the target's checkout from the part of its spelling before its first link. A path on the chain whose presence `lstat` cannot decide keeps its present decision there; the fixture of that case is built in the state the private record names (OD-9, carried on Task 28). Precedence is tested by overlap where conditions can co-occur and by separate fixtures where they cannot. The five unusable-field reasons are one value of one field and exclude each other; `target-unknown` and `target-match` are two answers of one checkout lookup and exclude each other, as do `directory-unknown` and `directory-match`; and a call is given a target or a directory, never both (design §5). Every other pair can co-occur, so each id of `test_applicable_reason_order` holds, beside its own reason, every later reason that can co-occur with it: each unusable-field id (`field-absent` to `checkout-unreadable`) with the session unknown and a target whose checkout git cannot identify (`target-unknown`); `[session-unknown]` with a usable field and the target in the named checkout (`target-match`); `[checkout-match]` with the target in the named checkout (`target-match`), and, in the same id, two further calls from the same session given a command directory instead of a target, one directory in the named checkout (`directory-match`) and one whose checkout git cannot identify (`directory-unknown`), each asserting `checkout-match`; `[session-unknown]`, likewise, also with a directory in the named checkout and with an unknown directory, each asserting `session-unknown`; `[directory-unknown]` and `[directory-match]` with the session in another checkout, given a directory; `[target-unknown]`, `[target-match]` and `[other-checkout]` with the session in another checkout, each alone. So a mutant that tests a later reason first gives that later reason on an id that holds it.

**Code structure**:
```python
class Applied(NamedTuple):
    record: object              # a LiveRecord in every result of this module; the judge's Record in judged_records (Task 25)
    applies: bool
    reason: str

def applicable(records: Sequence[LiveRecord], session: Checkout,
               target: str | None = None, directory: object = None) -> tuple[Applied, ...]: ...

class Scan:
    def __init__(self, root: PathArg, files: tuple[str, ...], oracles: dict[str, TreeOracle]) -> None: ...
    def session_checkout(self) -> Checkout: ...
    def session(self) -> Status: ...
    def write(self, target: PathArg) -> Status: ...
    def shell(self, directory: object, gates: Callable[[LiveRecord], bool]) -> Status: ...

def phase5_scan(root: PathArg) -> Scan: ...

class SessionStatus(str):
    scan: "Scan | None"
    records: tuple

def describe(applied: Sequence[Applied]) -> str: ...
```

**Tests and RED split** (all fail at RED: the names do not exist):
- `tests/test_h_mad_phase5_scope.py::test_applicable_reason_order[field-absent|field-invalid|path-missing|not-a-checkout|checkout-unreadable|session-unknown|checkout-match|target-unknown|target-match|directory-unknown|directory-match|other-checkout]` (12)
- `tests/test_h_mad_phase5_scope.py::test_applicable_ignores_owner_fields[owner_session_id|owner_heartbeat_ts|feature-key]` (3), spec AC-3.7 at the function.
- `tests/test_h_mad_phase5_scope.py::test_scan_session[applies|other-checkout|unreadable|no-live-record|planning-still-applies]` (5)
- `tests/test_h_mad_phase5_scope.py::test_scan_write[target-in-named|target-other|target-unknown|chain-unreadable|nested-chain-file|link-ahead-keeps-checkout|undecided-path-present-decision]` (7)
- `tests/test_h_mad_phase5_scope.py::test_scan_shell[directory-in-named|directory-unknown|directory-no-work-tree|directory-none-not-asked|gates-false-skips|active-before-unknown]` (6): `[active-before-unknown]` holds, first in discovery order, a live record naming another checkout, then an unreadable file and a record that applies, and asserts `applied` is exactly the applying entry.
- `tests/test_h_mad_phase5_scope.py::test_scan_memoises_checkout_calls` (1): git runs once for the session, once per distinct target or command directory and once per distinct other checkout a live record names, and not at all with no live record.
- `tests/test_h_mad_phase5_scope.py::test_describe[empty|first-applying|hostile-values]` (3)
- `tests/test_h_mad_phase5_scope.py::test_session_status_is_a_str[equality|carries-scan-and-records]` (2)
- `tests/test_h_mad_phase5_scope.py::test_path_parameters_accept_str_and_path[phase5_scan|Scan.write]` (2)
- `tests/test_h_mad_phase5_scope.py::test_raw_inputs_are_not_paths[Scan.shell]` (1): with one live record naming checkout C, a `str` directory inside C gives `active` (`directory-match`) and a `Path` object of the same text gives the malformed directory's answer (Task 3's boundary).
- `tests/test_h_mad_phase5_scope.py::test_checkout_match_without_f_getpath[plain|symlinked-checkout-record|symlinked-checkout-session|case-variant-case-sensitive-volume]` (4): the Linux path the spec's Compatibility clause asks to be simulated. With `fcntl.F_GETPATH` removed for the test (`monkeypatch.delattr(fcntl, "F_GETPATH", raising=False)`, so the fallback runs on a host that has the attribute and on one that has not), so `canonical_directory` takes its `os.path.realpath` fallback, `applicable` gives each id the reason it gives with `F_GETPATH` present: `checkout-match` for the plain and the two symlinked spellings on the system volume; on the mounted case-sensitive image (a named skip where `hdiutil` is unavailable), `path-missing` for a case-variant spelling, which is spec AC-4.12's case-sensitive branch.
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_function_has_one_definition_in_the_identity_module[applicable|phase5_scan|describe]` (3)

**Stated counts**: RED 49 failing, 188 passing (the 145 and 43 nodes earlier tasks and `bb88b6cc` leave in the two files); GREEN 237 passing.

**Mutation rows** (`phase5_scope.json`, 13):

| Name | Change | Killed by |
|---|---|---|
| `applicable-session-before-field` | `session-unknown` is tested before the unusable-field reasons | `tests/test_h_mad_phase5_scope.py::test_applicable_reason_order[field-invalid]` |
| `applicable-target-before-checkout` | `target-match` is tested before `checkout-match` | `tests/test_h_mad_phase5_scope.py::test_applicable_reason_order[checkout-match]` |
| `applicable-directory-unknown-skipped` | an unknown directory is not a reason | `tests/test_h_mad_phase5_scope.py::test_applicable_reason_order[directory-unknown]` |
| `shell-unknown-before-active` | `unknown` is returned before `active` | `tests/test_h_mad_phase5_scope.py::test_scan_shell[active-before-unknown]` |
| `shell-gates-ignored` | `gates` is not consulted | `tests/test_h_mad_phase5_scope.py::test_scan_shell[gates-false-skips]` |
| `write-chain-ignored` | `write` reads the session's records only | `tests/test_h_mad_phase5_scope.py::test_scan_write[nested-chain-file]` |
| `write-link-moves-checkout` | the target's checkout is taken from its resolved path | `tests/test_h_mad_phase5_scope.py::test_scan_write[link-ahead-keeps-checkout]` |
| `describe-unencoded` | `describe` omits `_encode_field` | `tests/test_h_mad_phase5_scope.py::test_describe[hostile-values]` |
| `applicable-owner-decides` | a record whose `owner_session_id` is null gives `other-checkout` | `tests/test_h_mad_phase5_scope.py::test_applicable_ignores_owner_fields[owner_session_id]` |
| `applicable-heartbeat-decides` | a record whose `owner_heartbeat_ts` is null gives `other-checkout` | `tests/test_h_mad_phase5_scope.py::test_applicable_ignores_owner_fields[owner_heartbeat_ts]` |
| `applicable-feature-key-decides` | a record whose key differs from its `feature` gives `other-checkout` | `tests/test_h_mad_phase5_scope.py::test_applicable_ignores_owner_fields[feature-key]` |
| `applicable-directory-before-checkout` | the two directory reasons are tested before `session-unknown` and `checkout-match` | `tests/test_h_mad_phase5_scope.py::test_applicable_reason_order[checkout-match]` |
| `shell-applied-unfiltered` | `Scan.shell` puts every entry of `applicable` in `applied` | `tests/test_h_mad_phase5_scope.py::test_scan_shell[active-before-unknown]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-6.1: `applicable` gives the first reason that holds, in design §5's order.
- [ ] AC-6.2: `Scan.shell` returns `active` before `unknown`, and only a record for which `gates(record)` is true gates.
- [ ] AC-6.3: `test_status_is_compared_by_value` (Task 3) and every caller this task adds compare a `Status` by `value`, never by truth.
- [ ] AC-6.4: The 13 rows are caught; the full suite passes; each `test_applicable_ignores_owner_fields` id holds a record that applies, carrying the value its row reads (a null `owner_session_id`, a null `owner_heartbeat_ts`, a key differing from `feature`).

**Dependencies on other tasks**: Tasks 3, 4, 5.

---

## Task 7: `_safe_argv` delegation (S1)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_arming_inputs.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_target_identity.py:_safe_argv` → `_safe_executable`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_safe_argv_delegates[executable]`
**WIRE 2**: `h-mad/scripts/h_mad_target_identity.py:_safe_argv` → `_is_bounded_run`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_safe_argv_delegates[bounded-run]`

**Description**: Design §6: the line of `_safe_argv` marked `M:G9` moves, as it is and with its marker, into `_safe_executable(argv, root, cwd)`, and the shape test of `run` (at least six words, `run`, `--timeout`, digits whose value is not zero, `--`) into `_is_bounded_run(argv)`; `_safe_argv` calls both, `_is_bounded_run` where `argv[1]` is already `run`, and no decision moves. `_argv_operator_allowed` is not edited. Scaffold for the pins: each installs a recorder in place of its callee with `monkeypatch.setattr(identity, "_safe_executable", recorder, raising=False)` or `monkeypatch.setattr(identity, "_is_bounded_run", recorder, raising=False)`, so the attribute need not exist at RED. `[executable]`: the recorder resolves a name no trusted directory holds to `/bin/cat`, and `_safe_argv` must admit that name; its second half, with no recorder, admits `pytest`. `[bounded-run]`: the recorder returns true for `hmad-dispatch run --timeout 0 -- pytest`, which the inline test refuses, and `_safe_argv` must admit it; its second half, with no recorder, admits `hmad-dispatch run --timeout 60 -- pytest` and refuses the malformed wrapper `hmad-dispatch run --timeout 0 -- pytest`, whose inner command is admissible, so a caller that treats every wrapper shape as valid fails it. At RED both first halves fail because `_safe_argv` still uses its inline expressions: an assertion about the caller.

OPEN-DECISION: OD-4, the S1 delegation points have no proof: restoring the old inline expression at the caller leaves every baseline-equivalence test green, and a helper can keep its one definition while its caller ignores it — resolve in 5d. Named implementation: this task's two pins and its rows `safe-argv-inlines-executable` and `safe-argv-inlines-bounded-run`, whose mutants restore the inline expression and are caught by the recorders; the helpers stay importable during the caller's test. The plan's wire table has no row for these two connections; registering them in `.h-mad/wires.jsonl` at 5b is this plan's addition.

**Code structure**:
```python
def _safe_executable(argv: list[str], root: Path | None, cwd: object) -> Path | None: ...
def _is_bounded_run(argv: list[str]) -> bool: ...
def _safe_argv(argv: list[str], root: Path | None, cwd: object) -> bool: ...   # unchanged signature
```

**Tests and RED split** (informational): the two pins fail by assertion; the other four fail because the names do not exist.
- `tests/test_h_mad_phase5_scope_wires.py::test_safe_argv_delegates[executable|bounded-run]` (2)
- `tests/test_h_mad_phase5_arming_inputs.py::test_bounded_run_matches_the_shape_of_7a3cca48` (1): over generated argvs `_is_bounded_run` equals the shape test of `_safe_argv` at `7a3cca48` and is implied by `_argv_operator_allowed`'s shape; a search with those words as its operands is not unwrapped.
- `tests/test_h_mad_phase5_arming_inputs.py::test_safe_executable_is_the_g9_line` (1)
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_function_has_one_definition_in_the_identity_module[_safe_executable|_is_bounded_run]` (2)

**Stated counts** (whole files, informational): RED 6 failing, 51 passing (5 nodes of the wires file and 46 of the shared-policy file; the arming-inputs file is new); GREEN 57 passing.

**Mutation rows** (`phase5_scope_wires.json`, 5):

| Name | Change | Killed by |
|---|---|---|
| `safe-argv-inlines-executable` | `_safe_argv` computes the executable inline again | `tests/test_h_mad_phase5_scope_wires.py::test_safe_argv_delegates[executable]` |
| `safe-argv-executable-none` | the call's result is replaced by `None` | `tests/test_h_mad_phase5_scope_wires.py::test_safe_argv_delegates[executable]` |
| `safe-argv-inlines-bounded-run` | `_safe_argv` tests the shape inline again | `tests/test_h_mad_phase5_scope_wires.py::test_safe_argv_delegates[bounded-run]` |
| `safe-argv-bounded-run-false` | the call's result is replaced by `False` | `tests/test_h_mad_phase5_scope_wires.py::test_safe_argv_delegates[bounded-run]` |
| `safe-argv-bounded-run-true` | the call's result is replaced by `True` | `tests/test_h_mad_phase5_scope_wires.py::test_safe_argv_delegates[bounded-run]` |

The `-none` and `-false` rows are caught by the admitting second half of their pin, `safe-argv-bounded-run-true` by the refusal of the malformed wrapper in that half, and the two `-inlines-` rows by the first: opposite required decisions in one test, each half a case.

**Existing specs to re-anchor**: none re-anchored, every quoted text being unchanged and still occurring once (design §6); re-run in full because the texts of `G9` and `CX-RUN-TIMEOUT` move: `codex_gate_judge_wiring`, `gate_git_verbs`, `gate_authoring_scope`, `gate_option_judging`.

**Acceptance Criteria**:
- [ ] AC-7.1: Every existing gate test passes unedited, and the four specs above report all caught.
- [ ] AC-7.2: The 5 rows are caught; the full suite passes.

**Dependencies on other tasks**: None.

---

## Task 8: Writer parser delegation (S1)

**Production file**: `h-mad/scripts/h_mad_state_write.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_state_write_scope.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_state_write.py:main` → `build_parser`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_writer_main_delegates[parser]`
**WIRE 2**: `h-mad/scripts/h_mad_state_write.py:main` → `assigned_keys`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_writer_main_delegates[keys]`

**Description**: Design §6: the writer exposes `build_parser()` (the parser `main` builds today, moved as it is), `assigned_keys(namespace)` (the stripped text before the first `=` of every `--set` and `--append`, today the expression that names the keys in the `STATE-WRITE: OK` line) and `parse_invocation(argv)` (parses with `build_parser()`, discards what argparse prints, returns `None` when argparse exits). `main` calls `build_parser().parse_args(argv)` and `assigned_keys`, never `parse_invocation`, so its help, diagnostics and exit codes stay argparse's. Scaffold: each pin installs a recorder with `monkeypatch.setattr(writer, "build_parser", recorder, raising=False)` or `monkeypatch.setattr(writer, "assigned_keys", recorder, raising=False)`. `[parser]`: the recorder raises a sentinel exception, and `main` must raise it. `[keys]`: the recorder returns `("sentinel-key",)`, and `main`, on a valid `--set` to a scratch store, must print it in the `OK` line. At RED both fail because `main` still builds its parser and its keys inline.

OPEN-DECISION: OD-4 (its writer half), as on Task 7 — resolve in 5d. Named implementation: this task's two pins and the rows `writer-main-inline-parser` and `writer-main-inline-keys`.

**Code structure**:
```python
def build_parser() -> argparse.ArgumentParser: ...
def assigned_keys(namespace: argparse.Namespace) -> tuple[str, ...]: ...
def parse_invocation(argv: list[str]) -> argparse.Namespace | None: ...
def main(argv: list[str] | None = None) -> int: ...   # unchanged signature
```

**Tests and RED split** (informational): 2 pins fail by assertion; 7 fail because the functions do not exist; 3 are guards.
- `tests/test_h_mad_phase5_scope_wires.py::test_writer_main_delegates[parser|keys]` (2)
- `tests/test_h_mad_state_write_scope.py::test_parse_invocation[valid|argparse-exit-returns-none|output-discarded]` (3)
- `tests/test_h_mad_state_write_scope.py::test_assigned_keys[set|append|stripped|first-equals]` (4)
- `tests/test_h_mad_state_write_scope.py::test_writer_cli_matches_baseline[help|unknown-option]` (2), guards: stdout, stderr and exit code of this writer and of the writer of `7a3cca48`, one interpreter and environment; observed failing under `writer-main-parser-without-append`.
- `tests/test_h_mad_state_write_scope.py::test_ok_line_names_the_keys` (1), guard; observed failing under `writer-main-keys-empty`.

**Stated counts** (whole files, informational): RED 9 failing, 10 passing (the 3 guards and the 7 nodes of the wires file; the writer-scope file is new); GREEN 19 passing.

**Mutation rows** (5): `phase5_scope_wires.json` (2), `state_write_scope.json` (3).

| Name | Change | Killed by |
|---|---|---|
| `writer-main-inline-parser` | `main` builds its parser inline again | `tests/test_h_mad_phase5_scope_wires.py::test_writer_main_delegates[parser]` |
| `writer-main-parser-without-append` | `main` parses with a parser that lacks `--append` | `tests/test_h_mad_state_write_scope.py::test_writer_cli_matches_baseline[help]` |
| `writer-main-inline-keys` | `main` computes its keys inline again | `tests/test_h_mad_phase5_scope_wires.py::test_writer_main_delegates[keys]` |
| `writer-main-keys-empty` | the keys `main` prints are `()` | `tests/test_h_mad_state_write_scope.py::test_ok_line_names_the_keys` |
| `parse-invocation-lets-exit-escape` | `parse_invocation` re-raises `SystemExit` | `tests/test_h_mad_state_write_scope.py::test_parse_invocation[argparse-exit-returns-none]` |

**Existing specs to re-anchor**: `state_undeclared_keys`, `heartbeat_beat`, `state_write_append`, where an anchor lies in `main` (plan §"Existing tests and mutation specs affected", writer row).

**Acceptance Criteria**:
- [ ] AC-8.1: The writer's existing tests pass unedited; `--help` and an unknown option give the bytes and code of the writer of `7a3cca48`.
- [ ] AC-8.2: The 5 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 1 (the extracted writer of `7a3cca48`).

---

## Task 9: Arming fields test (FR-5) (S1)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_arming_inputs.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `new-behaviour`

**Description**: The FR-5 test of design §6, called by no hook yet. `arming_write(command, root, cwd)` returns `None` for a command the lexical rule does not carry or that `shlex.split` refuses. Otherwise one question decides the rule: does `_safe_argv(argv, root, cwd)` admit it? Yes: by position, `writer_arguments` gives the words the writer is run with (an executable by `_safe_executable`; `hmad-dispatch` with `_is_bounded_run`, from the sixth word, by the same rule; a Python whose script is one file with `h_mad_state_write.py` beside the identity module), and `parse_invocation` of them gives the namespace, whose keys in `ARMING_FIELDS` are the hit, `feature` and `state_file` its own. No: on mention, `arming_mention` over the text (the argv joined with single spaces, without `'` and `"`, case-folded) finds each field by `(?<![a-z0-9_])(phase|implementation_checkout|phase5_stage)\s*=` and requires the name, by `h_mad_state_write` in the text or by `leads_to_writer` for a word. The writer is imported inside `writer_arguments`, so the identity module still loads beside a stub judge. `arming_refusal(hit, record, *, applied=None)` names each field, then the feature and state file, then the exit route, each value through `_encode_field`; when `applied` (an `Applied`) is given, its `describe((applied,))` text, which carries the applying reason, stands in place of the record's feature and state file. The S5 callers (Tasks 22 and 23) pass a `LiveRecord` and no `applied`; the S8 callers (Tasks 42 and 44) pass the applying entry, so the signature does not change between the steps.

**Code structure**:
```python
ARMING_FIELDS = ("phase", "implementation_checkout", "phase5_stage")

class ArmingWrite(NamedTuple):
    fields: tuple[str, ...]
    feature: str | None         # None for a mention
    state_file: str | None      # None for a mention

def writer_arguments(argv: list[str], root: Path | None, cwd: object) -> list[str] | None: ...
def leads_to_writer(word: str, root: Path | None, cwd: object) -> bool: ...
def arming_mention(argv: list[str], root: Path | None, cwd: object) -> tuple[str, ...]: ...
def arming_write(command: str, root: Path | None, cwd: object) -> ArmingWrite | None: ...
def arming_refusal(hit: ArmingWrite, record: LiveRecord | None, *, applied: Applied | None = None) -> str: ...
```

**Tests and RED split** (all fail at RED: the names do not exist):
- `tests/test_h_mad_phase5_arming_inputs.py::test_by_position[safe|run-wrapped-plain|run-wrapped-leading-zero|run-wrapped-nested|inert-operand|inert-value|unparsable-words|lexical-refused]` (8): `run-wrapped-leading-zero` is a shape the safe list admits and an allow line does not unwrap; the last two give `None`.
- `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[unknown-program|known-program|one-word|several-words|field-first|name-case|field-case|name-quotes|field-quotes|longer-word|link|relative-link|word-part|link-quotes|field-phase|field-implementation_checkout|field-phase5_stage|space|split|name-alone|field-alone|no-equals|letter|digit|underscore]` (25): the first 19 are hits and the last 6 are not; each id holds the command plain and under `hmad-dispatch run`.
- `tests/test_h_mad_phase5_arming_inputs.py::test_mention_without_a_directory_does_not_lead` (1)
- `tests/test_h_mad_phase5_arming_inputs.py::test_arming_corpus_superset[phase]` (1): spec AC-5.6's corpus, run by the real writer on a scratch store, for the field the writer of S1 can store; the test first asserts that at least one invocation of the corpus changed `phase` in the store (re-read after each run), so it cannot pass with nothing compared, and then that every invocation that changed an arming field is a hit. The ids of the two new fields land in Task 11, when the writer first stores them.
- `tests/test_h_mad_phase5_arming_inputs.py::test_arming_refusal[position|mention|hostile-values|applied-reason]` (4): `[applied-reason]` gives the text of `describe` for the `applied` entry in place of the record's part.
- `tests/test_h_mad_phase5_arming_inputs.py::test_arming_fields_reported_in_order` (1)
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_function_has_one_definition_in_the_identity_module[writer_arguments|leads_to_writer|arming_mention|arming_write|arming_refusal]` (5)
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_constant_is_assigned_in_the_identity_module[ARMING_FIELDS]` (1)

**Stated counts**: RED 46 failing, 50 passing (2 nodes of the arming-inputs file and 48 of the shared-policy file); GREEN 96 passing.

**Mutation rows** (`phase5_arming_inputs.json`, 32): the two groups of design §13 row 7 (22 and 9) and one more.

| Name | Change | Killed by |
|---|---|---|
| `run-allow-line-shape-only` | `run` is unwrapped only in the shape `_argv_operator_allowed` unwraps | `tests/test_h_mad_phase5_arming_inputs.py::test_by_position[run-wrapped-leading-zero]` |
| `writer-arguments-none` | `writer_arguments` returns `None` | `tests/test_h_mad_phase5_arming_inputs.py::test_by_position[safe]` |
| `mention-unknown-programs-only` | the mention is asked only when `argv[0]` is no program the safe list knows | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[known-program]` |
| `mention-known-programs-only` | the mention is asked only when it is one | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[unknown-program]` |
| `mention-not-asked-when-wrapped` | the mention is not asked when `_is_bounded_run(argv)` | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[one-word]` |
| `words-judged-one-by-one` | each word is judged alone | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[several-words]` |
| `words-joined-without-space` | the words are joined with nothing between them | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[several-words]` |
| `parts-in-different-words` | a word holding both parts is not counted | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[one-word]` |
| `name-before-field-only` | the name is sought only before the field | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[field-first]` |
| `name-no-casefold` | the name is not case-folded | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[name-case]` |
| `field-no-casefold` | the field is not case-folded | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[field-case]` |
| `name-quotes-kept` | quote characters are kept for the name | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[name-quotes]` |
| `field-quotes-kept` | quote characters are kept for the field | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[field-quotes]` |
| `link-quotes-kept` | quote characters are kept in `leads_to_writer` | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[link-quotes]` |
| `name-whole-word-only` | the name counts only as a whole word | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[longer-word]` |
| `leads-to-writer-false` | `leads_to_writer` returns `False` | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[link]` |
| `leads-to-writer-from-root` | a relative word is resolved from `root` | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[relative-link]` |
| `leads-to-writer-whole-words` | only whole words are resolved | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[word-part]` |
| `field-set-without-phase` | `phase` is left out of the field set | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[field-phase]` |
| `field-set-without-implementation_checkout` | `implementation_checkout` is left out | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[field-implementation_checkout]` |
| `field-set-without-phase5_stage` | `phase5_stage` is left out | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[field-phase5_stage]` |
| `no-space-before-equals` | `\s*` is dropped | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[space]` |
| `position-question-always-no` | the first question is answered "no" for every command | `tests/test_h_mad_phase5_arming_inputs.py::test_by_position[inert-value]` |
| `every-operand-is-the-writer` | by position every operand is examined as the writer's | `tests/test_h_mad_phase5_arming_inputs.py::test_by_position[inert-operand]` |
| `name-not-required` | the name is not required | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[field-alone]` |
| `field-not-required` | the field is not required | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[name-alone]` |
| `equals-not-required` | `=` is not required | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[no-equals]` |
| `no-left-boundary` | the left boundary is dropped | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[letter]` |
| `boundary-without-letters` | the boundary omits letters | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[letter]` |
| `boundary-without-digits` | the boundary omits digits | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[digit]` |
| `boundary-without-underscore` | the boundary omits the underscore | `tests/test_h_mad_phase5_arming_inputs.py::test_mention_rule[underscore]` |
| `refusal-unencoded` | `arming_refusal` omits `_encode_field` | `tests/test_h_mad_phase5_arming_inputs.py::test_arming_refusal[hostile-values]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-9.1: A command the safe list admits is judged by position only, and an operand nothing runs is data (`[inert-operand]`, `[inert-value]` give no hit).
- [ ] AC-9.2: A command the safe list does not admit is a hit exactly when the text holds a field followed by `=` and the name, by the clauses of design §6.
- [ ] AC-9.3: The 32 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 3, 6 (`Applied`), 7, 8.

---

## Task 10: Arming files test (FR-6) (S1)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `new-behaviour`

**Description**: The FR-6 test of design §7, called by no hook yet. `_target_names` gives the names of one target by step 1 (every spelling its path takes while its links are followed, at most 40, `..` taken physically, the canonical part before the first remaining link, plus `identity.target` and `identity.names`). A name is considered when `judged(name).value` is not `inactive`. It is protected from a place by step 3, with component equality by step 4 (`_same_component`). Inside `arming_target`, one nested `protected(place, names)` is called at four sites, for the two groups (*as named*, *as resolved*) from the session root and from each name's own checkout, so a name is judged from its own second place only (spec AC-6.7, AC-6.8). With no live record and nothing unreadable it returns at step 2, with no checkout call. `emit_arming`, the Claude hook's caller, lands with that hook's call in Task 24, because its S5 `judged` is Task 20's `unscoped_judge`; design §Implementation Order puts it in S1, and this plan moves it to S5.

Ruled (OD-1, the operator, 2026-11-26, answer (a)): the case-folding test of step 4 does not read two separately listed hard links that share an inode as "folds", and where the filesystem's own answer cannot be had it takes the stricter reading, which is a stated residual. The implementation: an entry is evidence of folding only when its case-swapped spelling is not itself among the directory's `os.scandir` names (two listed entries are two links and say nothing about folding). When no entry is evidence, the filesystem is asked only where the selector's meaning is known: `_CASE_SENSITIVE_SELECTOR = {"darwin": 11}` maps `sys.platform` to the numeric `pathconf` selector of `_PC_CASE_SENSITIVE` in the macOS SDK, and `os.pathconf(directory, selector)` is called only when `sys.platform` is a key of that mapping. No interpreter of the machine of record lists that name in `os.pathconf_names` (`python3.11`, `/usr/bin/python3` and `python3.15` were each asked), so the selector is fixed by platform, not looked up by name; a numeric selector's meaning is the platform's own, so it is never asked on a platform outside the mapping. An answer of 0 folds and 1 does not (one reading, at `bb88b6cc`, macOS 27.2.1, `darwin`: `python3.11 -c 'import os,sys; print(sys.platform, sorted(n for n in os.pathconf_names if "CASE" in n), os.pathconf("/", 11))'`, and the same with `/usr/bin/python3` and `python3.15`, each printed `darwin [] 0`, so no interpreter lists the name and the system volume answers 0; the selector's value is the SDK's, `grep -n _PC_CASE_SENSITIVE "$(xcrun --show-sdk-path)/usr/include/sys/unistd.h"` printing `#define _PC_CASE_SENSITIVE 11`); any other answer, an `OSError`, or a platform outside the mapping is *indeterminate*, and indeterminate takes the stricter reading of design §7 (equal). The residual, as ruled: where no directory entry is evidence (design §7 step 4 reads entry evidence from the directory and the directories above it on the same device first), and the platform is outside the mapping (Linux) or the answer is indeterminate, an ordinary absent document whose name differs only in case from a protected one is refused. In that case alone this departs from spec AC-6.6's "Other documents and data files keep their present decision while a record applies"; the residual's text is owed to design §7 and to the spec (see this revision's report). The test ids hold each branch, the unmapped platform and the indeterminate answer separately.

**Code structure**:
```python
class ArmingHit(NamedTuple):
    file: str
    feature: str
    reason: str

def _target_names(root: str, raw: str, base: str, identity: Identity) -> tuple[tuple[str, ...], tuple[str, ...]]: ...  # (as named, as resolved)
def _same_component(directory: str, one: str, other: str) -> bool: ...
def arming_target(scan: Scan, raw: str, base: PathArg, judged: Callable[[str], Status]) -> ArmingHit | None: ...
_CASE_SENSITIVE_SELECTOR: dict[str, int]   # {"darwin": 11}
```

**Tests and RED split** (all fail at RED: the names do not exist):
- `tests/test_h_mad_phase5_scope.py::test_target_names[path-as-given|symlinked-docs-absent-file|chain-of-links|dangling-referent|directory-behind-link|hard-links|absent-parents|unresolvable|dot-dot-after-link|loop|case-variants|alias-of-dot-git]` (12), the layouts of design §7's readings.
- `tests/test_h_mad_phase5_scope.py::test_arming_target_equals_unfiltered_reference` (1): property over generated layouts, both referent cases, names with different own checkouts.
- `tests/test_h_mad_phase5_scope.py::test_arming_target_places[session-root-as-named|session-root-as-resolved|target-checkout-as-named|target-checkout-as-resolved]` (4)
- `tests/test_h_mad_phase5_scope.py::test_arming_target_considered_only_when_judged_active` (1)
- `tests/test_h_mad_phase5_scope.py::test_arming_target_own_place_only` (1)
- `tests/test_h_mad_phase5_scope.py::test_fold_discriminator[two-listed-hard-links|single-entry-two-spellings|no-cased-entry-pathconf|no-cased-entry-no-pathconf|no-cased-entry-unmapped-platform|no-cased-entry-indeterminate|case-sensitive-volume-absent-document|system-volume-absent-document]` (8): `[no-cased-entry-no-pathconf]` has `os.pathconf` raise `OSError`; `[no-cased-entry-unmapped-platform]` sets `sys.platform` to `linux` for the test and asserts, by a recorder in place of `os.pathconf`, that it is not called and the answer is equal; `[no-cased-entry-indeterminate]` has `os.pathconf` answer 2 and expects equal. The case-sensitive volume is an APFS image mounted by the test with `hdiutil`, a named skip where that is unavailable; the last two are spec AC-6.6's absent document beside an absent protected name, its present decision on the case-sensitive volume and refused on the system volume.
- `tests/test_h_mad_phase5_scope.py::test_path_parameters_accept_str_and_path[arming_target]` (1)
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_function_has_one_definition_in_the_identity_module[_target_names|_same_component|arming_target]` (3)

**Stated counts**: RED 31 failing, 245 passing (the 191 and 54 nodes earlier tasks and `bb88b6cc` leave in the two files); GREEN 276 passing.

**Mutation rows** (`phase5_scope.json`, 10):

| Name | Change | Killed by |
|---|---|---|
| `names-stop-at-first-link` | step 1 stops at the first link | `tests/test_h_mad_phase5_scope.py::test_target_names[chain-of-links]` |
| `names-drop-hard-links` | `identity.names` are not added | `tests/test_h_mad_phase5_scope.py::test_target_names[hard-links]` |
| `names-unresolvable-empty` | an unresolvable target has no names | `tests/test_h_mad_phase5_scope.py::test_target_names[unresolvable]` |
| `equality-inode-only` | a found case-swap with one inode folds, whether or not it is listed | `tests/test_h_mad_phase5_scope.py::test_fold_discriminator[two-listed-hard-links]` |
| `equality-undecided-not-equal` | no evidence gives "not equal" | `tests/test_h_mad_phase5_scope.py::test_fold_discriminator[no-cased-entry-no-pathconf]` |
| `equality-pathconf-ignored` | `pathconf` is not asked | `tests/test_h_mad_phase5_scope.py::test_fold_discriminator[no-cased-entry-pathconf]` |
| `equality-selector-on-any-platform` | the selector is asked whatever `sys.platform` is | `tests/test_h_mad_phase5_scope.py::test_fold_discriminator[no-cased-entry-unmapped-platform]` |
| `equality-indeterminate-is-sensitive` | an answer other than 0 or 1 reads as "not equal" | `tests/test_h_mad_phase5_scope.py::test_fold_discriminator[no-cased-entry-indeterminate]` |
| `considered-ignores-judged` | every name is considered | `tests/test_h_mad_phase5_scope.py::test_arming_target_considered_only_when_judged_active` |
| `second-place-shared` | each name is judged from every name's checkout | `tests/test_h_mad_phase5_scope.py::test_arming_target_own_place_only` |

The four `protected` call sites are mutated at the hooks, as rows 6, 12 and 19 (Tasks 21, 23, 24).

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-10.1: `arming_target` equals the unfiltered reference on every generated layout.
- [ ] AC-10.2: A name that is considered and protected gives a hit; with no live record and nothing unreadable no checkout call is made.
- [ ] AC-10.3: The 10 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 5, 6.

---

## Task 11: Writer: one result, resolved store, schema, transitions (S2)

**Production file**: `h-mad/scripts/h_mad_state_write.py`, `h-mad/scripts/h_mad_state_schema.json`
**Test file**: `h-mad/tests/test_h_mad_state_write_scope.py`, `h-mad/tests/test_h_mad_phase5_scope_differential.py`, `h-mad/tests/test_h_mad_phase5_arming_inputs.py`
**Task shape**: `new-behaviour`

**Description**: Design §9, in its order. (1) One invocation, one persisted result, with one step contract. A step is `Step = Callable[[Optional[dict], Path], StepResult]` (`Optional`, because the alias is evaluated when the module loads, under Python 3.9 too; convention 1): it is given the record as it stands after the steps before it (`None` when the feature has no record) and the resolved store path `_mutate` locked, and it returns `StepResult(record, output, removed)`, where `record` is the record after the step, or `None` for a step that changes nothing (`--drop-undeclared` with nothing to remove, a repeated value), and `output` is the lines it would print, each `(stream, text)` with `stream` `"stdout"` or `"stderr"`, held back, and `removed` is the tuple of keys the step removed (`_step_drop` alone fills it; every other step returns `()`), carried out of the locked step as data, never parsed back from the `DROPPED` text, in which a key holding a comma cannot be told from two keys. A step raises `StateWriteError` to refuse. The create step is bound to the requested feature key (`_step_create(record, store, *, feature, started_ts)`), because for a missing record its inputs are `None`, a store several features share, and a timestamp, and none of them names the feature it must write in the record's `feature` property, as `create_feature` writes it today. The steps keep every keyword the present functions take, `now` included: `_step_claim`, `_step_beat` and `_step_merge` take `now: str | None`, and a library call (`beat(path, feature, session_id, now=...)`, `merge_fields(..., now=...)`, `claim(..., now=...)`) binds its own `now` into its step, so the caller-supplied clock reaches the stored timestamp as it does today. `apply_invocation` runs the steps in the present order inside one `_mutate` (lock, load, all steps on a copy, arming rules, `classify`, one `_atomic_write`, seed) and returns `InvocationResult(record, changed, output, removed)`: `changed` is true when any step returned a record, `removed` is the steps' `removed` in order, and when it is false nothing is written and the store stays byte-identical; `output` is every step's held lines in order, which `main` prints after the write, so `DROPPED`, `BEAT` and the takeover line are printed after the write and nothing is persisted or printed before the last check. The library functions keep their signatures and wrap a one-step invocation; `drop_undeclared(path, feature)` returns `(result.record, list(result.removed))`, the `(record, removed)` its callers unpack today (`test_h_mad_state_write.py`, `_, removed = sw.drop_undeclared(p, "demo")`). (2) Resolved store: `_mutate` takes the realpath once, and lock, read, temporary file and replace use it. (3) The two schema properties, placed before `fallback_agent` and not in `required` (design §Data Model). (4) The arming rules in `_step_merge`, per design §9's table, and the refusal of an `--append` that names an arming field. This task stores a checkout value of the not-live-to-live row as given, compares a repeated value by string and by `canonical_directory`, and seeds only the given path; Tasks 12, 13 and 14 add the validation and spelling, the store membership and the second seed. Every refusal of this task's tests asserts exit 2, the store byte-identical, no `STATE-WRITE:` line, and an `ERROR:` line that names the field and the rule.

**Code structure**:
```python
class StepResult(NamedTuple):
    record: dict | None                   # None: this step changes nothing
    output: tuple[tuple[str, str], ...]   # (stream, text), printed only after the write
    removed: tuple[str, ...] = ()         # the keys _step_drop removed; () for every other step

class InvocationResult(NamedTuple):
    record: dict                          # the feature's record after the invocation
    changed: bool
    output: tuple[tuple[str, str], ...]
    removed: tuple[str, ...]              # every step's removed keys, in order

Step = Callable[[Optional[dict], Path], StepResult]   # (record so far, resolved store) -> result; Optional: evaluated at import, 3.9 included

def _step_create(record: dict | None, store: Path, *, feature: str, started_ts: str | None) -> StepResult: ...  # writes record["feature"] = feature
def _step_drop(record: dict | None, store: Path) -> StepResult: ...   # output: the DROPPED line; removed: the keys
def _step_claim(record: dict | None, store: Path, session_id: str, *, force: bool, evidence: object, now: str | None) -> StepResult: ...  # output: the takeover line
def _step_release(record: dict | None, store: Path, session_id: str | None, *, force: bool, evidence: object) -> StepResult: ...
def _step_beat(record: dict | None, store: Path, session_id: str | None, *, now: str | None) -> StepResult: ...  # output: the BEAT line
def _step_merge(record: dict | None, store: Path, fields: dict, *, session_id: str | None, appends: list, now: str | None) -> StepResult: ...
def apply_invocation(state_file: Path, feature: str, steps: Sequence[Step]) -> InvocationResult: ...
```

**Tests and RED split**: 11 guards and 2 observations pass at RED, named below; every other test fails at RED because the fields are undeclared and each step persists alone.
- `tests/test_h_mad_state_write_scope.py::test_compound_write_is_whole` (1), as plan §"Single source" specifies it.
- `tests/test_h_mad_state_write_scope.py::test_one_result_per_invocation[create-then-refused-set|claim-then-refused-set|drop-then-refused-set|nothing-printed-before-last-check|no-change-writes-nothing|create-two-features-one-store|drop-returns-removed-keys]` (7); `[no-change-writes-nothing]` is a guard, observed failing under `invocation-writes-unchanged`; `[create-two-features-one-store]`, a guard, creates `a` and then `b` in one store, through the CLI and through `create_feature`, and asserts each record's `feature` property is its own key and `a`'s record is unchanged by `b`'s create, observed failing under `create-step-feature-unbound`; `[drop-returns-removed-keys]`, a guard, drops the undeclared keys `x,y` and `z` from one record and asserts `drop_undeclared` returns exactly `["x,y", "z"]`, observed failing under `drop-removed-from-text`.
- `tests/test_h_mad_state_write_scope.py::test_symlinked_store_write[link-kept|shared-after-either-writes|same-lock]` (3), spec AC-1.7.
- `tests/test_h_mad_state_write_scope.py::test_arm_without_checkout_clears` (1), spec AC-1.4.
- `tests/test_h_mad_state_write_scope.py::test_live_checkout_rules[change-refused|repeat-as-stored|repeat-canonical|repeat-missing-checkout|null-when-stored-refused|null-when-none-accepted|not-live-without-step5-refused]` (7), spec AC-1.5.
- `tests/test_h_mad_state_write_scope.py::test_disarm_clears_both_fields[checkout|stage|non-null-refused]` (3), spec AC-1.6.
- `tests/test_h_mad_state_write_scope.py::test_null_field_rules[checkout-not-live|checkout-arming|checkout-live-absent|checkout-live-present-refused|stage-not-live|stage-arming|stage-live-absent|stage-live-present-refused]` (8), spec AC-1.9.
- `tests/test_h_mad_state_write_scope.py::test_stage_transitions[arm-planning|arm-implementing|arm-other-refused|repeat-planning-whole-5a-command|planning-on-implementing-refused|planning-on-no-stage-refused|implementing-on-live|implementing-in-arming-write]` (8), spec AC-9.4; the shell half of its last case is Task 48's.
- `tests/test_h_mad_state_write_scope.py::test_append_naming_arming_field_refused[phase|implementation_checkout|phase5_stage]` (3)
- `tests/test_h_mad_state_write_scope.py::test_validator_reads_new_fields_as_strict[with-fields|without-fields|required-unchanged]` (3), spec AC-1.8; `[without-fields]` and `[required-unchanged]` are guards, observed failing under `schema-fields-required`.
- `tests/test_h_mad_state_write_scope.py::test_older_writer_refuses_new_field[checkout|stage]` (2), spec AC-10.3; observations (convention 9): they read the extracted writer of `7a3cca48`, which no change of this feature can move. Detector control, run once after GREEN (convention 9; at RED this tree's writer refuses the field too, so it cannot violate the property) and recorded in the 5e report: the same test with this tree's writer after Task 11's GREEN in place of the extracted one, which stores the field, and the test must fail.
- `tests/test_h_mad_state_write_scope.py::test_older_arm_newer_write[non-arming-field|repeat-step5|implementing|exit|checkout-refused|checkout-with-step5-refused|planning-refused|exit-then-newer-arm-scopes]` (8), spec AC-10.5; `[non-arming-field]`, `[repeat-step5]` and `[exit]` are guards (the accepted writes on an older record do not change), each observed failing under `older-record-refused`.
- `tests/test_h_mad_state_write_scope.py::test_newer_arm_older_write[set|append|claim|beat|release|exit-refused|repeat-create|other-record|drop-undeclared]` (9), spec AC-10.6's writes.
- `tests/test_h_mad_state_write_scope.py::test_newer_exit_older_arm` (1)
- `tests/test_h_mad_state_write_scope.py::test_writer_transitions_per_interpreter[<INTERPRETERS>]` (6): the transition cases of this file under each supported Python (plan §"Convention Prerequisites", Interpreters); each id first runs `import h_mad_state_write` under its interpreter as a process and requires exit 0, so an import-time type expression that Python 3.9 cannot evaluate fails `[py3.9]` by name.
- `tests/test_h_mad_phase5_scope_differential.py::test_class_has_difference[D5]` (1): the old and the new writer make the same write through a symlinked scratch store; `lstat` then finds a regular file with the old writer and a link with the new one, under at least one supported Python.
- `tests/test_h_mad_state_write_scope.py::test_invocation_threads_now[beat|merge|claim]` (3): guards; each library call given `now=` stores that timestamp in `owner_heartbeat_ts` (`[merge]` calls `sw.merge_fields(p, "demo", {"halt_reason": "x"}, session_id="me", now="2026-07-22T01:30:00Z")` on a record whose `owner_session_id` is `"me"`, because `merge_fields` stamps only when `session_id` names the current owner, `h-mad/scripts/h_mad_state_write.py:252-253`, so a call without the owner's id would pass on both sides and leave `invocation-drops-now-merge` alive; `beat` and `claim` stamp unconditionally, lines 307 and 433), as the existing `sw.beat(p, "demo", "me", now="2026-07-22T01:30:00Z")` test does for `beat`; each id is the `test` of its own row, one per stamping site (`invocation-drops-now-beat`, `invocation-drops-now-merge`, `invocation-drops-now-claim`), because the tree stamps `now or _utc_now()` at three separate sites (`merge_fields`, `beat`, `claim`) and a row's `find` matches one of them.
- `tests/test_h_mad_phase5_arming_inputs.py::test_arming_corpus_superset[implementation_checkout|phase5_stage]` (2): Task 9's test for the two new fields, on a fixture whose checkout is a usable top level from which the store is discoverable (so the writer rules of Tasks 12 and 13 accept the corpus's writes too); each id first asserts that at least one invocation changed its field in the store, then that every invocation that changed an arming field is a hit. At RED the writer refuses the undeclared field, so the first assertion fails.

**Stated counts**: RED 63 failing, 164 passing (the 13 guards and observations: `test_one_result_per_invocation[no-change-writes-nothing]`, `test_one_result_per_invocation[create-two-features-one-store]`, `test_one_result_per_invocation[drop-returns-removed-keys]`, `test_validator_reads_new_fields_as_strict[without-fields]`, `test_validator_reads_new_fields_as_strict[required-unchanged]`, `test_older_writer_refuses_new_field[checkout]`, `test_older_writer_refuses_new_field[stage]`, `test_older_arm_newer_write[non-arming-field]`, `test_older_arm_newer_write[repeat-step5]`, `test_older_arm_newer_write[exit]`, `test_invocation_threads_now[beat]`, `test_invocation_threads_now[merge]`, `test_invocation_threads_now[claim]`; and the 151 nodes earlier tasks leave in the three files, 10 of the writer-scope file, 99 of the differential file and 42 of the arming-inputs file); GREEN 227 passing.

**Differential**: `CHANGES_IN_FORCE` gains D5 on no key; D5 is the writer observation above.

**Mutation rows** (`state_write_scope.json`, 23):

| Name | Change | Killed by |
|---|---|---|
| `invocation-persists-each-step` | each step is written as it runs | `tests/test_h_mad_state_write_scope.py::test_compound_write_is_whole` |
| `invocation-prints-before-check` | `DROPPED` is printed before the last check | `tests/test_h_mad_state_write_scope.py::test_one_result_per_invocation[nothing-printed-before-last-check]` |
| `store-not-resolved` | replace uses the given path | `tests/test_h_mad_state_write_scope.py::test_symlinked_store_write[link-kept]` |
| `lock-on-given-path` | the lock uses the given path | `tests/test_h_mad_state_write_scope.py::test_symlinked_store_write[same-lock]` |
| `arm-keeps-stored-checkout` | arming without a checkout keeps a stored one | `tests/test_h_mad_state_write_scope.py::test_arm_without_checkout_clears` |
| `live-checkout-change-accepted` | a live record's checkout can change | `tests/test_h_mad_state_write_scope.py::test_live_checkout_rules[change-refused]` |
| `live-repeat-validated` | a repeated stored value is validated | `tests/test_h_mad_state_write_scope.py::test_live_checkout_rules[repeat-missing-checkout]` |
| `disarm-keeps-checkout` | leaving `step5` keeps the checkout | `tests/test_h_mad_state_write_scope.py::test_disarm_clears_both_fields[checkout]` |
| `disarm-keeps-stage` | leaving `step5` keeps the stage | `tests/test_h_mad_state_write_scope.py::test_disarm_clears_both_fields[stage]` |
| `null-stored` | a null is stored, not a removed key | `tests/test_h_mad_state_write_scope.py::test_null_field_rules[checkout-not-live]` |
| `null-clears-live-value` | a null clears a live record's stored checkout | `tests/test_h_mad_state_write_scope.py::test_null_field_rules[checkout-live-present-refused]` |
| `planning-on-implementing-accepted` | `"planning"` is accepted on a record at `"implementing"` | `tests/test_h_mad_state_write_scope.py::test_stage_transitions[planning-on-implementing-refused]` |
| `planning-repeat-refused` | a repeated `"planning"` is refused | `tests/test_h_mad_state_write_scope.py::test_stage_transitions[repeat-planning-whole-5a-command]` |
| `implementing-in-arming-refused` | `"implementing"` is refused in the arming write | `tests/test_h_mad_state_write_scope.py::test_stage_transitions[implementing-in-arming-write]` |
| `append-arming-field-accepted` | an `--append` naming an arming field is accepted | `tests/test_h_mad_state_write_scope.py::test_append_naming_arming_field_refused[phase]` |
| `schema-fields-required` | both new properties are added to `required` | `tests/test_h_mad_state_write_scope.py::test_validator_reads_new_fields_as_strict[without-fields]` |
| `invocation-writes-unchanged` | an invocation whose steps change nothing still writes the store | `tests/test_h_mad_state_write_scope.py::test_one_result_per_invocation[no-change-writes-nothing]` |
| `older-record-refused` | the arming rules refuse every write to a live record without the new fields | `tests/test_h_mad_state_write_scope.py::test_older_arm_newer_write[non-arming-field]` |
| `invocation-drops-now-beat` | the beat step stamps `_utc_now()` in place of the caller's `now` | `tests/test_h_mad_state_write_scope.py::test_invocation_threads_now[beat]` |
| `invocation-drops-now-merge` | the merge step stamps `_utc_now()` in place of the caller's `now` | `tests/test_h_mad_state_write_scope.py::test_invocation_threads_now[merge]` |
| `invocation-drops-now-claim` | the claim step stamps `_utc_now()` in place of the caller's `now` | `tests/test_h_mad_state_write_scope.py::test_invocation_threads_now[claim]` |
| `create-step-feature-unbound` | the create step writes no `feature` property | `tests/test_h_mad_state_write_scope.py::test_one_result_per_invocation[create-two-features-one-store]` |
| `drop-removed-from-text` | `drop_undeclared` returns the keys split on `,` from the `DROPPED` text in place of the step's `removed` | `tests/test_h_mad_state_write_scope.py::test_one_result_per_invocation[drop-returns-removed-keys]` |

**Existing specs to re-anchor**: `state_undeclared_keys`, `heartbeat_beat`, `state_write_append`, `lane_liveness`, `null_heartbeat_unknown_age`, `release_ownership_guard`, each where an anchor lies in a function this task edits (plan §"Existing tests and mutation specs affected", writer row).

**Acceptance Criteria**:
- [ ] AC-11.1: A refused invocation leaves the store byte-identical and prints no `STATE-WRITE:` line, for every case of `test_compound_write_is_whole`.
- [ ] AC-11.2: `test_new_properties_follow_fallback_agent_in_order` in `h-mad/tests/test_h_mad_state_schema_fr1_docs.py` passes unedited.
- [ ] AC-11.3: The writer's existing tests pass unedited; the 23 rows are caught; the full suite passes.
- [ ] AC-11.4: A library call given `now=` stores that `now`; every step returns a `StepResult`, and a step that changes nothing returns `record=None`.

**Dependencies on other tasks**: Tasks 1, 3, 8, 9 (its `arming_write` and `test_arming_corpus_superset`, which this task extends).

---

## Task 12: Writer checkout validation and spelling (S2)

**Production file**: `h-mad/scripts/h_mad_state_write.py`
**Test file**: `h-mad/tests/test_h_mad_state_write_scope.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_state_write.py:_step_merge` → `recorded_checkout`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_state_write_scope.py::test_checkout_validation_wire[validation]`
**WIRE 2**: `h-mad/scripts/h_mad_state_write.py:_step_merge` → `recorded_checkout`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_state_write_scope.py::test_checkout_validation_wire[spelling]`

**Description**: Row 23 (S2, protection; spelling value): on the not-live-to-live row, `_step_merge` stores a checkout only when `recorded_checkout(value)` gives a usable one, and stores its canonical path. The writer imports the identity module inside its arming rules (design §Architecture). Both wires are the one call: wire 1 is its refusal, wire 2 its spelling. Each pin runs through the CLI and through `merge_fields`. At RED both fail because Task 11 stores the value as given.

**Code structure**:
```python
def _step_merge(record: dict | None, store: Path, fields: dict, *, session_id: str | None, appends: list, now: str | None) -> StepResult: ...  # gains the call
```

**Tests and RED split** (informational): 11 fail, 1 guard passes.
- `tests/test_h_mad_state_write_scope.py::test_checkout_validation_wire[validation|spelling]` (2)
- `tests/test_h_mad_state_write_scope.py::test_arm_with_checkout_stores_canonical[symlink|case-variant|plain]` (3), spec AC-1.1; `[plain]` is a guard, observed failing under `checkout-validation-unconditional`.
- `tests/test_h_mad_state_write_scope.py::test_arm_refuses_unusable_checkout[not-string|empty|relative|missing|file|not-top-level|git-cannot-judge]` (7), spec AC-1.2.

**Stated counts** (whole files, informational): RED 11 failing, 84 passing (the guard and the 83 nodes of the writer-scope file); GREEN 95 passing.

**Mutation rows** (`state_write_scope.json`, 4):

| Name | Change | Killed by |
|---|---|---|
| `checkout-validation-dropped` | the refusal is dropped | `tests/test_h_mad_state_write_scope.py::test_checkout_validation_wire[validation]` |
| `checkout-validation-unconditional` | every checkout is refused | `tests/test_h_mad_state_write_scope.py::test_arm_with_checkout_stores_canonical[plain]` |
| `checkout-spelling-as-given` | the value is stored as given | `tests/test_h_mad_state_write_scope.py::test_checkout_validation_wire[spelling]` |
| `checkout-spelling-fixed` | one fixed path is stored | `tests/test_h_mad_state_write_scope.py::test_arm_with_checkout_stores_canonical[plain]` |

**Existing specs to re-anchor**: none beyond Task 11's.

**Acceptance Criteria**:
- [ ] AC-12.1: Each case of spec AC-1.2 is refused with the store byte-identical; a usable checkout is stored in canonical spelling, through a symlink and in another case.
- [ ] AC-12.2: The 4 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 4, 11.

---

## Task 13: Writer store membership (S2)

**Production file**: `h-mad/scripts/h_mad_state_write.py`
**Test file**: `h-mad/tests/test_h_mad_state_write_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_state_write.py:_step_merge` → `session_state_files`
**WIRE-PIN**: `h-mad/tests/test_h_mad_state_write_scope.py::test_undiscoverable_store_wire`

**Description**: Row 22 (S2, protection): a checkout is stored only when the store's realpath is among the realpaths of `session_state_files(top)` for the named checkout (spec AC-1.3). The store compared is the one `_mutate` locked: `_step_merge` receives it as its `store` argument (Task 11's step contract passes every step the resolved path `_mutate` locked), so the membership check and the write name one file, and a second store cannot be checked in the written one's place. At RED the pin fails because the write is accepted.

**Code structure**:
```python
def _step_merge(record: dict | None, store: Path, fields: dict, *, session_id: str | None, appends: list, now: str | None) -> StepResult: ...  # gains the call
```

**Tests and RED split** (informational): 5 fail, 1 guard passes.
- `tests/test_h_mad_state_write_scope.py::test_undiscoverable_store_wire` (1)
- `tests/test_h_mad_state_write_scope.py::test_store_must_be_discoverable[linked-store-passes|no-state-file|own-copy|two-stores-cli|two-stores-library]` (5); `[linked-store-passes]` writes through the worktree's link, so the path given and the path `_mutate` locks differ; it is a guard, observed failing under `membership-refusal-unconditional` and `membership-checks-given-path`. The two `two-stores` ids hold two stores, B discoverable from the named checkout and A not: arming with that checkout through A is refused and through B accepted, once through the CLI (the store given as the writer's positional `state_file` argument, as `main` declares it) and once through `merge_fields`; each refusal asserts exit 2 (or `StateWriteError`) with the `ERROR:` text naming the store-membership rule, and after each invocation both stores are re-read: A byte-identical after its refusal, B holding the checkout after its acceptance.

**Stated counts** (whole files, informational): RED 5 failing, 96 passing (the guard and the 95 nodes of the writer-scope file); GREEN 101 passing.

**Mutation rows** (`state_write_scope.json`, 3):

| Name | Change | Killed by |
|---|---|---|
| `membership-refusal-dropped` | the refusal is dropped | `tests/test_h_mad_state_write_scope.py::test_undiscoverable_store_wire` |
| `membership-refusal-unconditional` | every checkout is refused | `tests/test_h_mad_state_write_scope.py::test_store_must_be_discoverable[linked-store-passes]` |
| `membership-checks-given-path` | the check compares the store path as given, not the one `_mutate` locked | `tests/test_h_mad_state_write_scope.py::test_store_must_be_discoverable[linked-store-passes]` |

**Existing specs to re-anchor**: none beyond Task 11's.

**Acceptance Criteria**:
- [ ] AC-13.1: A worktree whose state file links to the written file passes; one with no state file, or its own copy, is refused.
- [ ] AC-13.2: The 3 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 5, 12.

---

## Task 14: Writer seeds both paths (S2)

**Production file**: `h-mad/scripts/h_mad_state_write.py`
**Test file**: `h-mad/tests/test_h_mad_state_write_scope.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_state_write.py:_mutate` → `seed_bkit_target`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_state_write_scope.py::test_seed_both_paths_wire[given]`
**WIRE 2**: `h-mad/scripts/h_mad_state_write.py:_mutate` → `seed_bkit_target`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_state_write_scope.py::test_seed_both_paths_wire[resolved]`

**Description**: Row 31 (S2, value): `_mutate` calls `seed_bkit_target` for the path as given (the call marked `M:SW-BKIT-SEED`, which stands today) and, when it differs, for the resolved path (spec AC-1.7). `h_mad_bkit_guard.py` keeps its code; this task's two-path case is the test design §Components gives it. Pin 1 passes at RED (its call stands) and is a guard by convention 10, observed failing under `seed-given-dropped`; pin 2 fails at RED. The pins run on a symlinked store, with a recorder in place of `seed_bkit_target`, and their assertions are independent, so each can pass or fail without the other: `[given]` asserts that the given path occurs exactly once among the destinations seeded, which the call standing today satisfies at RED; `[resolved]` asserts the complete list of destinations seeded, the given path and the resolved path, each once, which fails at RED. A mutant of the resolved call can only be seen where that call is made, so its killer is `[resolved]` on the symlinked store; `test_seed_once_when_paths_agree`, on a regular store where the call is skipped, kills the mutant that makes the call anyway.

**Code structure**:
```python
def _mutate(state_file: Path, feature: str, apply) -> dict: ...  # one seed call per distinct path
```

**Tests and RED split** (informational): 1 fails, 2 guards pass.
- `tests/test_h_mad_state_write_scope.py::test_seed_both_paths_wire[given|resolved]` (2); `[given]` is a guard.
- `tests/test_h_mad_state_write_scope.py::test_seed_once_when_paths_agree` (1), guard, observed failing under `seed-resolved-unconditional`.

**Stated counts** (whole files, informational): RED 1 failing, 103 passing (the 2 guards and the 101 nodes of the writer-scope file); GREEN 104 passing.

**Mutation rows** (`state_write_scope.json`, 5):

| Name | Change | Killed by |
|---|---|---|
| `seed-given-dropped` | the given path is not seeded | `tests/test_h_mad_state_write_scope.py::test_seed_both_paths_wire[given]` |
| `seed-resolved-dropped` | the resolved path is not seeded | `tests/test_h_mad_state_write_scope.py::test_seed_both_paths_wire[resolved]` |
| `seed-given-fixed` | the given call seeds one fixed path | `tests/test_h_mad_state_write_scope.py::test_seed_both_paths_wire[given]` |
| `seed-resolved-fixed` | the resolved call seeds one fixed path | `tests/test_h_mad_state_write_scope.py::test_seed_both_paths_wire[resolved]` |
| `seed-resolved-unconditional` | the resolved call is made when the two paths agree | `tests/test_h_mad_state_write_scope.py::test_seed_once_when_paths_agree` |

**Existing specs to re-anchor**: none (no spec quotes the seed call).

**Acceptance Criteria**:
- [ ] AC-14.1: A write through a symlinked store seeds both paths, and a regular store once.
- [ ] AC-14.2: The 5 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 11.

---

## Task 15: Assembler checkout halt (S3)

**Production file**: `h-mad/scripts/h_mad_assemble_tdd.py`
**Test file**: `h-mad/tests/test_h_mad_assemble_tdd_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_assemble_tdd.py:phase5_staging_halt` → `recorded_checkout`
**WIRE-PIN**: `h-mad/tests/test_h_mad_assemble_tdd_scope.py::test_checkout_mismatch_wire[red]`

**Description**: Row 20 (S3, protection), with design §10's function and its call: `main` calls `phase5_staging_halt(feature, project_root)` after the agy wiring check and before any path is composed. Over the live records with the feature's key, any usable checkout (by `recorded_checkout`) that is not `checkout_of(project_root).top` gives `ASSEMBLE-TDD: HALT checkout_mismatch`, its detail line naming the feature, the state file and the record's checkout, the `[H-MAD]` halt marker, and exit 2 (the exception spec FR-11 records). This task looks the records up from `project_root` itself; Task 17 makes the lookup root the checkout of `project_root`. The pin family is one id per phase of `PHASES`; each id holds the refused half (staged from another checkout) and the opposite half (staged from the named checkout). `[red]` is the pin the registry records; `[green]`, `[gate]` and `[review]` run beside it. At RED the refused half fails because `main` stages.

OPEN-DECISION: OD-6, the assembler launches its sibling wiring checker (`AGY_WIRING_CHECK`) with its own interpreter, and a PATH stub alone does not supply the scratch project's `.agents/hooks.json`, so a `review` can halt before either new condition — resolve in 5d. Named implementation: every test of `test_h_mad_assemble_tdd_scope.py` builds its scratch project with a valid `.agents/hooks.json`, written by the helpers `agy_hooks()` and `write_agy_hooks(root, config)` of `h-mad/tests/test_h_mad_assemble_tdd_agent.py`, runs under that file's `agy_env` fixture, lets the real checker run, and requires the exact staging reason, no staging stamp, no prompt file where there was none, and an existing prompt file byte-identical, for each phase.

**Code structure**:
```python
def phase5_staging_halt(feature: str, project_root: Path) -> tuple[str, str] | None: ...
def main(argv: list[str] | None = None) -> int: ...  # calls it after the agy wiring check
```

**Tests and RED split** (informational; all fail at RED, `main` staging in every case):
- `tests/test_h_mad_assemble_tdd_scope.py::test_checkout_mismatch_wire[<PHASES>]` (4)
- `tests/test_h_mad_assemble_tdd_scope.py::test_checkout_mismatch_halt[<PHASES>]` (4), spec AC-11.2: token, exit 2, no stamp, prompt files as above; a record without the field stages as now, and so does unreadable state when no mismatching record was read.

**Stated counts** (whole files, informational): RED 8 failing, 0 passing (the file is new); GREEN 8 passing.

**Mutation rows** (`assemble_tdd_scope.json`, 2):

| Name | Change | Killed by |
|---|---|---|
| `staging-checkout-condition-false` | the checkout condition is false | `tests/test_h_mad_assemble_tdd_scope.py::test_checkout_mismatch_wire[red]` |
| `staging-checkout-condition-true` | the checkout condition is true | `tests/test_h_mad_assemble_tdd_scope.py::test_checkout_mismatch_wire[green]` |

**Existing specs to re-anchor**: those of plan §"Existing tests and mutation specs affected", assembler row, with an anchor in `main`: `assemble_tdd`, `assemble_tdd_agent`, `assemble_tdd_agy`, `assemble_tdd_authors_test`, `assemble_tdd_effort`, `assemble_tdd_env_known`, `assemble_tdd_mutation_rows`, `assemble_tdd_prompt_rows`, `assemble_tdd_review`, `fill_slots`, `grok_wire_reverts`; each anchor must still match once.

**Acceptance Criteria**:
- [ ] AC-15.1: Staging from a checkout other than a live record's usable one halts `checkout_mismatch` with exit 2 for every phase, and staging from the named checkout passes.
- [ ] AC-15.2: Both rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 4, 5, 6.

---

## Task 16: Assembler stage halt (S3)

**Production file**: `h-mad/scripts/h_mad_assemble_tdd.py`
**Test file**: `h-mad/tests/test_h_mad_assemble_tdd_scope.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_assemble_tdd.py:phase5_staging_halt` → `stage_gates_shell`
**WIRE-PIN**: `h-mad/tests/test_h_mad_assemble_tdd_scope.py::test_planning_stage_wire[red]`

**Description**: Row 21 (S3, protection): only when no live record meets the checkout condition does a record for which `stage_gates_shell(record)` is false give `ASSEMBLE-TDD: HALT phase5_stage_planning`, exit 2 (plan §"The two staging refusals", both conditions at once). One HALT is printed, whatever the order of discovery. The pin family is one id per phase; each id holds the refused half (a record at `"planning"`) and the opposite half (a record with no stage, which stages).

**Code structure**:
```python
def phase5_staging_halt(feature: str, project_root: Path) -> tuple[str, str] | None: ...  # gains the stage half
```

**Tests and RED split** (informational; all fail at RED, no stage halt existing):
- `tests/test_h_mad_assemble_tdd_scope.py::test_planning_stage_wire[<PHASES>]` (4)
- `tests/test_h_mad_assemble_tdd_scope.py::test_planning_stage_halt[<PHASES>]` (4), spec AC-9.5.
- `tests/test_h_mad_assemble_tdd_scope.py::test_both_staging_conditions[one-record-<PHASES>|two-records-<PHASES>|two-records-swapped-<PHASES>]` (12), as plan §"The two staging refusals", Test, carried through the corrective sequence with every token asserted.
- `tests/test_h_mad_phase5_scope.py::test_stage_callers_agree[assembler]` (1): its other ids land in Tasks 28, 48 and 50.

**Stated counts** (whole files, informational): RED 21 failing, 227 passing (8 nodes of the assembler-scope file and 219 of `test_h_mad_phase5_scope.py`); GREEN 248 passing.

**Mutation rows** (`assemble_tdd_scope.json`, 3):

| Name | Change | Killed by |
|---|---|---|
| `staging-stage-false` | the stage condition is `False` | `tests/test_h_mad_assemble_tdd_scope.py::test_planning_stage_wire[red]` |
| `staging-stage-true` | the stage condition is `True` | `tests/test_h_mad_assemble_tdd_scope.py::test_planning_stage_wire[gate]` |
| `staging-stage-before-checkout` | the stage half is tested first | `tests/test_h_mad_assemble_tdd_scope.py::test_both_staging_conditions[two-records-red]` |

**Existing specs to re-anchor**: none beyond Task 15's.

**Acceptance Criteria**:
- [ ] AC-16.1: Each id of `test_both_staging_conditions` gives `checkout_mismatch` first and then the tokens of the corrective sequence.
- [ ] AC-16.2: The 3 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 15.

---

## Task 17: Assembler lookup root (S3)

**Production file**: `h-mad/scripts/h_mad_assemble_tdd.py`
**Test file**: `h-mad/tests/test_h_mad_assemble_tdd_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_assemble_tdd.py:phase5_staging_halt` → `checkout_of`
**WIRE-PIN**: `h-mad/tests/test_h_mad_assemble_tdd_scope.py::test_record_lookup_wire[checkout]`

**Description**: Row 30 (S3, value): the lookup root is `checkout_of(project_root).top`, or `project_root` when that is unknown (design §10). `[checkout]` stages from a directory below the top level and finds the root file's record; at RED it fails because the lookup starts at `project_root`.

**Code structure**:
```python
def phase5_staging_halt(feature: str, project_root: Path) -> tuple[str, str] | None: ...  # lookup root changes
```

**Tests and RED split** (informational): 1 fails, 1 guard passes.
- `tests/test_h_mad_assemble_tdd_scope.py::test_record_lookup_wire[checkout|unknown-checkout]` (2); `[unknown-checkout]` is a guard, observed failing under `lookup-root-fixed-other`.

**Stated counts** (whole files, informational): RED 1 failing, 29 passing (the guard and the 28 nodes of the assembler-scope file); GREEN 30 passing.

**Mutation rows** (`assemble_tdd_scope.json`, 2):

| Name | Change | Killed by |
|---|---|---|
| `lookup-root-project-root` | the lookup root is `project_root` | `tests/test_h_mad_assemble_tdd_scope.py::test_record_lookup_wire[checkout]` |
| `lookup-root-fixed-other` | the lookup root is one fixed other checkout | `tests/test_h_mad_assemble_tdd_scope.py::test_record_lookup_wire[unknown-checkout]` |

**Existing specs to re-anchor**: none beyond Task 15's.

**Acceptance Criteria**:
- [ ] AC-17.1: Both rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 16.

---

## Task 18: codex root lookup environment (S4)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`, `h-mad/tests/test_h_mad_phase5_scope_differential.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_project_root` → `git_environment`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_root_wire[GIT_DIR]`

**Description**: Row 27 (S4, environment), D7: the `rev-parse --show-toplevel` call of `_project_root` passes `env=git_environment()`; nothing else of the lookup changes (no option, no bound). `git_environment` is added to the codex hook's guarded import. Each id of `test_codex_root_wire` sets one variable of `VARIABLES`, without `CODEX_PROJECT_DIR`, to a value that moves git's answer (checked by asking git directly both ways), and asserts the decision equals the one with the four unset; this is spec AC-2.8 for the codex root. `[GIT_DIR]` is the registered pin and the other three run beside it.

**Code structure**:
```python
def _project_root(payload: dict[str, Any]) -> Path | Identity: ...  # its git call gains env=git_environment()
```

**Tests and RED split** (informational): 6 fail, 1 guard passes.
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_root_wire[<VARIABLES>]` (4)
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_root_wire_unset_control` (1), guard, observed failing under `codex-root-env-elsewhere`.
- `tests/test_h_mad_shared_gate_policy.py::test_every_git_call_passes_the_git_environment[codex-hook]` (1)
- `tests/test_h_mad_phase5_scope_differential.py::test_class_has_difference[D7]` (1)

**Stated counts** (whole files, informational): RED 6 failing, 167 passing (the guard, and 9, 57 and 100 nodes of the wires, shared-policy and differential files); GREEN 173 passing.

**Differential**: `CHANGES_IN_FORCE` gains D7 at `("codex-shell", "arming")`, `("codex-shell", "other")`, `("codex-write", "arming")` and `("codex-write", "other")`, the root lookup deciding every branch.

**Mutation rows** (`phase5_scope_wires.json`, 2):

| Name | Change | Killed by |
|---|---|---|
| `codex-root-env-dropped` | the call inherits the environment | `tests/test_h_mad_phase5_scope_wires.py::test_codex_root_wire[GIT_DIR]` |
| `codex-root-env-elsewhere` | the call is given an environment naming another checkout | `tests/test_h_mad_phase5_scope_wires.py::test_codex_root_wire_unset_control` |

**Existing specs to re-anchor**: `shared_gate_policy` (`fr6-import-guard-dropped` quotes the import list, which gains a name).

**Acceptance Criteria**:
- [ ] AC-18.1: With each variable set, the codex decision equals the one with the four unset; `CODEX_PROJECT_DIR` is used as given, with no git lookup.
- [ ] AC-18.2: Both rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 3.

---

## Task 19: agy root lookup environment (S4)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `git_environment`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_root_wire[GIT_DIR]`

**Description**: Row 28 (S4, environment), D7: the root lookup in `main` (`rev-parse --show-toplevel` run with `-C` on the parent of the hook's working directory, its 2 s timeout unchanged) passes `env=git_environment()`, imported inside the guarded `main`. Spec AC-2.8 for the agy root, as Task 18.

**Code structure**:
```python
def main() -> int: ...  # its root lookup gains env=git_environment()
```

**Tests and RED split** (informational): 5 fail, 1 guard passes.
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_root_wire[<VARIABLES>]` (4)
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_root_wire_unset_control` (1), guard, observed failing under `agy-root-env-elsewhere`.
- `tests/test_h_mad_shared_gate_policy.py::test_every_git_call_passes_the_git_environment[agy-hook]` (1)

**Stated counts** (whole files, informational): RED 5 failing, 73 passing (the guard, and 14 and 58 nodes of the wires and shared-policy files); GREEN 78 passing.

**Differential**: `CHANGES_IN_FORCE` gains D7 at `("agy-shell", "arming")`, `("agy-shell", "other")`, `("agy-write", "arming")` and `("agy-write", "other")`.

**Mutation rows** (`phase5_scope_wires.json`, 2):

| Name | Change | Killed by |
|---|---|---|
| `agy-root-env-dropped` | the call inherits the environment | `tests/test_h_mad_phase5_scope_wires.py::test_agy_root_wire[GIT_DIR]` |
| `agy-root-env-elsewhere` | the call is given an environment naming another checkout | `tests/test_h_mad_phase5_scope_wires.py::test_agy_root_wire_unset_control` |

**Existing specs to re-anchor**: none quotes the lookup; every spec with an anchor in agy `main` is re-run in full: `agy_tdd_gate`, `agy_gate_listing`, `listing_connections`, `hook_live_interpreter`.

**Acceptance Criteria**:
- [ ] AC-19.1: With each variable set, the agy decision equals the one with the four unset.
- [ ] AC-19.2: Both rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 3.

---

## Task 20: Today's walk as a value, and `unscoped_judge` (S5)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `new-behaviour`

**Description**: Design §5, for S5 to S7. `_any_phase5_status(root)` returns a `SessionStatus` whose value is exactly today's (the `rglob` walk and its `active` before `unknown`), whose `.records` are the live records of the files that walk found, and whose `.scan` is `None` until Task 47; its name, arity and exceptions stay, and the agy test that replaces it with a one-argument function still reaches it. `unscoped_judge(root, walked=None)` returns a function of one spelling that gives a `Status`: `active` when that walk, or the unfiltered directory chain of the spelling, holds a live record; `unknown` when either holds a file that cannot be read or the walk raises; else `inactive`. It reads the chain itself and does not call `read_chain`. `walked` is the `SessionStatus` the Python hooks already hold, so they walk once; on the Claude hook it is absent and the function walks. The `applied` entries of its `Status` are `Applied(record, True, "unscoped")`: design §5 and §7 leave the reason of an S5 hit unstated, and `unscoped` leaves with the function, in Task 38.

OPEN-DECISION: OD-10, two clauses of design §5 give opposite values for `unscoped_judge` in the case of spec FR-10's residual, and no test holds it — resolve in 5d. Named implementation: the session half of `unscoped_judge` is `walked` itself, or `_any_phase5_status(root)` when `walked` is absent, and never a second classification, so for any path its value is that walk's; `test_unscoped_judge_session_half_is_the_walk` asserts, under each interpreter of `INTERPRETERS`, that for a spelling outside every chain the function's value equals `_any_phase5_status(root)` on each fixture of this task. No test builds the residual's case.

**Code structure**:
```python
def _any_phase5_status(root: PathArg) -> SessionStatus: ...   # value unchanged; carries .records, .scan None
def unscoped_judge(root: PathArg, walked: SessionStatus | None = None) -> Callable[[str], Status]: ...
```

**Tests and RED split** (all fail at RED: `unscoped_judge` does not exist and `_any_phase5_status` returns a plain `str`):
- `tests/test_h_mad_phase5_scope.py::test_session_status_value_unchanged[active|unknown|inactive]` (3)
- `tests/test_h_mad_phase5_scope.py::test_unscoped_judge[walk-live|chain-live|walk-unreadable|chain-unreadable|walk-raises|nothing-live|undecided-path-as-walk]` (7)
- `tests/test_h_mad_phase5_scope.py::test_unscoped_judge_uses_walked` (1)
- `tests/test_h_mad_phase5_scope.py::test_unscoped_judge_session_half_is_the_walk[<INTERPRETERS>]` (6)
- `tests/test_h_mad_phase5_scope.py::test_path_parameters_accept_str_and_path[_any_phase5_status|unscoped_judge]` (2): `[_any_phase5_status]` fails at RED, the walk calling `rglob` on a `str`; this is the boundary the Claude hook's `emit_arming` (Task 24) crosses with its `sys.argv` root.
- `tests/test_h_mad_shared_gate_policy.py::test_each_scope_function_has_one_definition_in_the_identity_module[unscoped_judge]` (1)

**Stated counts**: RED 20 failing, 279 passing (the 220 and 59 nodes earlier tasks and `bb88b6cc` leave in the two files); GREEN 299 passing.

**Mutation rows** (`phase5_scope.json`, 6):

| Name | Change | Killed by |
|---|---|---|
| `unscoped-walk-ignored` | the walk's records are not read | `tests/test_h_mad_phase5_scope.py::test_unscoped_judge[walk-live]` |
| `unscoped-chain-ignored` | the chain is not read | `tests/test_h_mad_phase5_scope.py::test_unscoped_judge[chain-live]` |
| `unscoped-unknown-ignored` | an unreadable file gives `inactive` | `tests/test_h_mad_phase5_scope.py::test_unscoped_judge[walk-unreadable]` |
| `unscoped-walks-twice` | `walked` is ignored | `tests/test_h_mad_phase5_scope.py::test_unscoped_judge_uses_walked` |
| `session-status-records-empty` | `.records` is empty | `tests/test_h_mad_phase5_scope.py::test_session_status_value_unchanged[active]` |
| `walk-root-not-normalised` | `_any_phase5_status` walks its argument without `Path(...)` | `tests/test_h_mad_phase5_scope.py::test_path_parameters_accept_str_and_path[_any_phase5_status]` |

**Existing specs to re-anchor**: none quotes `_any_phase5_status` (plan: it has no mutation today).

**Acceptance Criteria**:
- [ ] AC-20.1: Every existing test that reaches `_any_phase5_status` passes unedited.
- [ ] AC-20.2: The 6 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 3, 6.

---

## Task 21: codex arming files (S5)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_phase5_scope_differential.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `arming_target`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[session-root-as-named]`

**Description**: Row 6 (S5, protection). At the head of the codex target loop, for every target and before the out-of-root, allowance-file and document branches, the hook calls `arming_target(scan, raw, str(base), judged)` with `scan = phase5_scan(root)` (computed beside the status, S5 to S7) and `judged = unscoped_judge(root, phase5_status)`, so every live record of today's discovery counts (plan rule 2). `base` is the directory the loop resolves a relative target against, defined once: the first part of `_relative_target` (from `_payload_cwd_base(root, cwd)` to the end of its canonicalisation of the payload's `cwd`, unchanged in effect) becomes `_payload_base(root, cwd) -> Path`, which binds its own `identity = _load_identity()` (the moved canonicalisation and `CX-FORCE-CWD`'s `replace`, which calls `identity.canonical_directory(cwd)`, both need it; `_relative_target` keeps its own binding for the rest), `_relative_target` calls it, and the loop computes `base = _payload_base(root, payload.get("cwd"))` once before its first target, so FR-6's names and the write's own target are spelled from the same directory. As today, a payload `cwd` outside the root gives the root as `base`, for the check and for the write alike; a relative target written from a `cwd` in another checkout is resolved against the root, which is the present behaviour and not changed here. On agy and Claude `base` is the root, which is what each hook's own `canonicalise` call resolves against (agy passes `str(root)` as its `cwd`; Claude passes none). A hit is refused with a text that names the file, the feature and the reason, each through `_encode_field`, and the exit route. The names the hook uses are added to its guarded import. The pin family is plan row 6's S5 ids: `[session-root-as-named]`, `[session-root-as-resolved]`, `[target-checkout-as-named]`, `[target-checkout-as-resolved]` (the four `protected` call sites), `[linked-referent]` and `[linked-referent-absent]` (each from the session root and from the target's own checkout, each with a neighbouring document at its present decision), and `[unfiltered-discovery]` (the only live record lies in a git-excluded tree with no checkout field; refused). With these ids land this host's FR-6 acceptance cases.

OPEN-DECISION: OD-7, the S5 walk-count assertion does not say which traversal "one walk" counts, while the Python hooks reuse one unfiltered walk and also make a filtered discovery — resolve in 5d. Named implementation: `test_s5_walks_once_each` counts, by an audit hook on `os.scandir`, the listings of the session root in one hook call, which is one per traversal: exactly 2 on codex here and on agy in Task 23 (the unfiltered walk, shared with `unscoped_judge` through `walked`, and the filtered discovery); a third means `walked` was not passed and one means an input is missing. Task 47 asserts 1 from S8.

**Code structure**:
```python
def _payload_base(root: Path, cwd: Any = None) -> Path: ...                       # extracted from _relative_target
def _relative_target(root: Path, raw: str, cwd: Any = None) -> Identity | None: ...  # calls _payload_base
def _main_guarded() -> int: ...  # the target loop's head gains the arming_target call
```

**Tests** (informational counts; the per-test failure mode is the RED report's, phase5-substeps 5d; ids named "no-record" are guards):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[<ARMING_FILE_IDS>]` (7)
- `tests/test_h_mad_phase5_scope.py::test_arming_file_refused[<ARMING_TARGETS>-<CODEX_WRITE_OPS>]` (24), spec AC-6.1 to AC-6.3.
- `tests/test_h_mad_phase5_scope.py::test_arming_file_no_record[root-state-codex|sub-project-state-codex|dot-git-component-codex|alternative-spelling-codex]` (4), spec AC-6.4; guards, observed failing under `codex-arming-always-hit`.
- `tests/test_h_mad_phase5_scope.py::test_arming_file_unreadable_state[root-state-codex|sub-project-state-codex|dot-git-component-codex|alternative-spelling-codex]` (4), spec AC-6.5.
- `tests/test_h_mad_phase5_scope.py::test_shared_state_file[<SHARED_FILE_REFUSED>-codex]` (6), the refusals of spec AC-6.7, AC-6.8; the two `SHARED_FILE_KEEPS` ids land in Task 35, because while every live record counts the session's own file and a `.git` target in B are protected too.
- `tests/test_h_mad_phase5_scope.py::test_git_variables[<VARIABLES>-codex-explicit]` (4), spec AC-2.8 with `CODEX_PROJECT_DIR`, the hook now asking git through the scan.
- `tests/test_h_mad_phase5_scope.py::test_s5_walks_once_each[codex]` (1)
- `tests/test_h_mad_phase5_scope.py::test_codex_relative_arming_target_from_subdirectory` (1): a payload `cwd` of `sub/docs` inside the root and the relative target `.bkit-memory.json`, which is `sub/docs/.bkit-memory.json`, a sub-project state file: refused; spelled from the root it would be `.bkit-memory.json` at the root, which is no arming file.
- `tests/test_h_mad_phase5_scope_differential.py::test_class_has_difference[D6]` (1)

Total 52 test ids. **Stated counts** (whole files, informational): 52 new ids (guards: the 4 `test_arming_file_no_record` ids), and 359 prior nodes passing (19 of the wires file, 239 of `test_h_mad_phase5_scope.py`, 101 of the differential file); GREEN 411 passing.

**Differential**: `CHANGES_IN_FORCE[("codex-write", "arming")]` gains D6.

**Mutation rows** (`phase5_scope_wires.json`, 8):

| Name | Change | Killed by |
|---|---|---|
| `codex-arming-target-none` | the call's result is `None` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[session-root-as-named]` |
| `codex-protected-session-named-false` | the session-root *as named* call answers `False` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[session-root-as-named]` |
| `codex-protected-session-resolved-false` | the session-root *as resolved* call answers `False` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[session-root-as-resolved]` |
| `codex-protected-target-named-false` | the own-checkout *as named* call answers `False` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[target-checkout-as-named]` |
| `codex-protected-target-resolved-false` | the own-checkout *as resolved* call answers `False` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[target-checkout-as-resolved]` |
| `codex-arming-judged-filtered` | `judged` is `phase5_scan(root).write` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[unfiltered-discovery]` |
| `codex-arming-always-hit` | every target is a hit | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[linked-referent]` |
| `codex-arming-base-root` | `arming_target` is given `str(root)` as `base` | `tests/test_h_mad_phase5_scope.py::test_codex_relative_arming_target_from_subdirectory` |

The four `protected` rows change a call site inside `arming_target` in `h-mad/scripts/h_mad_target_identity.py` (design §13); the others change the hook.

**Existing specs to re-anchor**: `codex_gate_judge_wiring`, `codex_gate_shell_allowance`, `codex_gate_listing`, `hook_live_interpreter` (anchors in `_main_guarded`); `codex_gate_judge_wiring` again for `CX-FORCE-CWD` and `CX-CWD-RECHECK`, whose anchors lie in the part of `_relative_target` that moves into `_payload_base`, and `CX-RESOLVE-M9`, whose `canonicalise` line stays in `_relative_target` beside the new call (each keeps its text, its meaning and one match; none carries a `symbol` today); `shared_gate_policy`, `codex_gate_listing`, `listing_connections` (the import block).

**Acceptance Criteria**:
- [ ] AC-21.1: While any live record of today's discovery exists, each codex write operation on an arming file, by each spelling of design §7 step 1, is refused; a neighbouring document keeps its present decision.
- [ ] AC-21.2: The 8 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 10, 18, 20.

---

## Task 22: codex arming fields (S5)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `arming_write`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[safe]`

**Description**: Row 7 (S5, protection), design §6 "Where it stands": a guard of its own, `phase5_status == "active"` (today's walk, through `_any_phase5_status(root)`), after the present refusal on `unknown` and before the command branch, calls `arming_write(command, root, _command_cwd(payload))`, ahead of all three ways a command is admitted. A hit is refused with `arming_refusal(hit, record)`, whose record for a mention is the first of `phase5_status.records`, and whose exit route names the operator at a terminal, a Claude session and a grok session (spec AC-7.5). The pin family is plan row 7's S5 ids, `ARMING_WRITE_IDS`: refused, `safe`, the three `run-wrapped-` ids, `allowed`, the 19 `mention-` ids of `MENTION_HITS`, `mention-no-line` and `unfiltered-discovery`; admitted, the 6 `no-mention-` ids of `NO_MENTION_CASES`, `inert-operand` and `inert-value`. Each `allowed`, `mention-` and `no-mention-` id is run plain and under `hmad-dispatch run`, under its line, and first asserts that the safe list does not admit the command and that it matches its line.

**Code structure**:
```python
def _main_guarded() -> int: ...  # gains the FR-5 guard before the command branch
```

**Tests** (informational; the 6 ids of `test_non_arming_writes_keep_decision` and the 8 admitted pin ids are guards, each observed failing under `codex-arming-write-always-hit`):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[<ARMING_WRITE_IDS>]` (34)
- `tests/test_h_mad_phase5_scope.py::test_arming_write_variants[<ARMING_VARIANTS>-codex-shell]` (7), spec AC-5.1, AC-5.2.
- `tests/test_h_mad_phase5_scope.py::test_non_arming_writes_keep_decision[<NON_ARMING_OPS>-codex-shell]` (6), spec AC-5.4; guards, observed failing under `codex-arming-write-always-hit`.

Total 47 test ids. **Stated counts** (whole files, informational): 47 new ids (14 guards, as above), and 309 prior nodes passing (26 of the wires file, 283 of `test_h_mad_phase5_scope.py`); GREEN 356 passing.

**Differential**: `CHANGES_IN_FORCE[("codex-shell", "arming")]` gains D6.

**Mutation rows** (`phase5_scope_wires.json`, 3):

| Name | Change | Killed by |
|---|---|---|
| `codex-arming-write-none` | the call's result is `None` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[safe]` |
| `codex-arming-guard-filtered` | the guard reads `phase5_scan(root).session().value` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[unfiltered-discovery]` |
| `codex-arming-write-always-hit` | every command is a hit | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[inert-operand]` |

The mutants inside `arming_write` are Task 9's 32 rows.

**Existing specs to re-anchor**: as Task 21 (anchors in `_main_guarded`).

**Acceptance Criteria**:
- [ ] AC-22.1: From a gated codex shell an arming write is refused by position and on mention, plain and wrapped, with and without a matching line; a non-arming write keeps its present decision.
- [ ] AC-22.2: The 3 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 9, 21.

---

## Task 23: agy arming files and fields (S5)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_agy_tdd_gate.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `arming_target`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[session-root-as-named]`
**WIRE 2**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `arming_write`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[safe]`

**Description**: Row 12 (S5, protection): rows 6 and 7 on agy. `arming_target` heads the class-b target loop, before the directory, out-of-root and allowance-file branches; `arming_write` stands in class c, in its own guard on today's `active`, after the refusal on `unknown`, with the directory decoded and entered as now, once, before the check (design §6). Every refusal it gives ends with ` kind=arming-input`, the one `kind=` of the text, values encoded by `_encode_field`. `GATE_KINDS` gains `arming-input` and nothing else; so does the copy of that constant in `h-mad/tests/test_h_mad_agy_tdd_gate.py`, compared by `test_classification_table_is_the_recorded_inventory` (the census's expected edit, spec AC-10.4). `_one_decision` is not edited. The pin families are those of Tasks 21 and 22, on agy.

**Code structure**:
```python
GATE_KINDS: frozenset[str]  # gains "arming-input"
def main() -> int: ...       # class b loop head and class c guard gain the two calls
```

**Tests** (informational; the 4 no-record ids are guards observed failing under `agy-arming-always-hit`, and the 8 admitted pin ids and the 6 non-arming ids guards observed failing under `agy-arming-write-always-hit`):
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[<ARMING_FILE_IDS>]` (7)
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[<ARMING_WRITE_IDS>]` (34)
- `tests/test_h_mad_phase5_scope.py::test_arming_file_refused[<ARMING_TARGETS>-<AGY_WRITE_OPS>]` (16)
- `tests/test_h_mad_phase5_scope.py::test_arming_file_no_record[root-state-agy|sub-project-state-agy|dot-git-component-agy|alternative-spelling-agy]` (4)
- `tests/test_h_mad_phase5_scope.py::test_arming_file_unreadable_state[root-state-agy|sub-project-state-agy|dot-git-component-agy|alternative-spelling-agy]` (4)
- `tests/test_h_mad_phase5_scope.py::test_shared_state_file[<SHARED_FILE_REFUSED>-agy]` (6); the `SHARED_FILE_KEEPS` ids land in Task 38.
- `tests/test_h_mad_phase5_scope.py::test_arming_write_variants[<ARMING_VARIANTS>-agy-shell]` (7)
- `tests/test_h_mad_phase5_scope.py::test_non_arming_writes_keep_decision[<NON_ARMING_OPS>-agy-shell]` (6)
- `tests/test_h_mad_phase5_scope.py::test_s5_walks_once_each[agy]` (1)
- `tests/test_h_mad_phase5_scope.py::test_agy_one_decision_on_arming_refusals` (1): `_one_decision` over every FR-5 and FR-6 refusal, with a feature key and paths that hold `kind=` and a newline.

Total 86 test ids, besides the edited constant. **Stated counts** (whole files, informational): 86 new ids (18 guards, as above), and 468 prior nodes (60 of the wires file, 296 of `test_h_mad_phase5_scope.py`, 112 of `test_h_mad_agy_tdd_gate.py`), of which `test_classification_table_is_the_recorded_inventory`, whose constant this task edits, fails at RED and the other 467 pass; GREEN 554 passing.

**Differential**: `CHANGES_IN_FORCE[("agy-shell", "arming")]` and `[("agy-write", "arming")]` gain D6.

**Mutation rows** (`phase5_scope_wires.json`, 10):

| Name | Change | Killed by |
|---|---|---|
| `agy-arming-target-none` | the call's result is `None` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[session-root-as-named]` |
| `agy-protected-session-named-false` | as Task 21, agy's killer | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[session-root-as-named]` |
| `agy-protected-session-resolved-false` | as Task 21 | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[session-root-as-resolved]` |
| `agy-protected-target-named-false` | as Task 21 | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[target-checkout-as-named]` |
| `agy-protected-target-resolved-false` | as Task 21 | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[target-checkout-as-resolved]` |
| `agy-arming-judged-filtered` | `judged` is `phase5_scan(root).write` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[unfiltered-discovery]` |
| `agy-arming-always-hit` | every target is a hit | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[linked-referent]` |
| `agy-arming-write-none` | the call's result is `None` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[safe]` |
| `agy-arming-guard-filtered` | the guard reads `phase5_scan(root).session().value` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[unfiltered-discovery]` |
| `agy-arming-write-always-hit` | every command is a hit | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[inert-operand]` |

**Existing specs to re-anchor**: `agy_tdd_gate`, `agy_gate_listing`, `listing_connections`, `hook_live_interpreter` (anchors in agy `main`).

**Acceptance Criteria**:
- [ ] AC-23.1: Every agy refusal this task adds carries exactly one `kind=` token, `kind=arming-input`, and ends with it.
- [ ] AC-23.2: The 10 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 9, 10, 19, 20.

---

## Task 24: Claude arming files (S5)

**Production file**: `h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_tdd_gate_judge.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-tdd-gate.sh:M:H11` → `emit_arming`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[session-root-as-named]`
**WIRE 2**: `h-mad/hooks/h-mad-tdd-gate.sh:_allow` → `ARMING`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[function-absent]`

**Description**: Row 19 (S5, protection), design §7 "Claude hook". `emit_arming(root, raw, identity)` lands here, with `judged = unscoped_judge(root)` (no `walked` on this hook) and `base` the root. Its `root` is the `str` the canonicalisation process reads from `sys.argv`, so it crosses Task 3's path boundary as a `str`: `emit_arming` passes it on unconverted, and `unscoped_judge` and `_any_phase5_status` apply `Path(...)` at their entry (Task 20), so an ordinary permitted write does not reach `rglob` on a `str` and raise. `test_path_parameters_accept_str_and_path[emit_arming]` holds the function, and the admitted halves of the pin family hold the real emitter through the hook's own string input. The canonicalisation process of the line marked `M:H11` reads it with `getattr`, prints `arming missing` when the module has none, and otherwise prints, before the canonical record, `arming none`, or for a hit the line design §7 gives, `arming` followed by the fields `file=`, `feature=` and `reason=`, the file and feature encoded by `_encode_field` and the reason the applying record's (`state-unreadable`, with an empty feature, when state cannot be read). The shell cuts that first line off and reads the record and the `docdata` line as now; a well-formed hit refuses `kind=arming-input` at once, before `_chain_may_hold_state` and every early allow; exactly `arming none` sets `ARMING=none`; anything else leaves `ARMING` empty, and `_allow` refuses `kind=arming-input` unless `ARMING` is `none`. In the same commit the stub identity text of `_tree_b` in `h-mad/tests/test_h_mad_tdd_gate_judge.py` gains the two lines `def emit_arming(root, raw, record):` and ` print('arming none')`, with no expectation changed (spec AC-10.4), and `test_exempt_write_on_unreadable_chain_is_allowed[state-file]` moves to refused, its other ids unchanged (spec AC-6.5; the census's expected edit). The pin family: one id per early allow the refusal precedes, `[before-unresolvable-fast-path]`, `[before-chain-fast-path]`, `[before-test-names]`, `[before-tests-directory]`, `[before-docs]`, `[before-out-of-root-directory]`, `[before-scratch]`, `[before-doc-data]`, `[before-listing-outside-root]`; the 7 ids of `ARMING_FILE_IDS`; and `[function-absent]`, whose opposite half is the same write with the function present, admitted.

**Code structure**:
```python
def emit_arming(root: PathArg, raw: str, identity: Identity) -> None: ...  # prints one "arming ..." line
```

**Tests** (informational; the 4 no-record ids are guards):
- `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[before-unresolvable-fast-path|before-chain-fast-path|before-test-names|before-tests-directory|before-docs|before-out-of-root-directory|before-scratch|before-doc-data|before-listing-outside-root|<ARMING_FILE_IDS>|function-absent]` (17)
- `tests/test_h_mad_phase5_scope.py::test_arming_file_refused[<ARMING_TARGETS>-<CLAUDE_WRITE_OPS>]` (8)
- `tests/test_h_mad_phase5_scope.py::test_arming_file_no_record[root-state-claude|sub-project-state-claude|dot-git-component-claude|alternative-spelling-claude]` (4)
- `tests/test_h_mad_phase5_scope.py::test_arming_file_unreadable_state[root-state-claude|sub-project-state-claude|dot-git-component-claude|alternative-spelling-claude]` (4)
- `tests/test_h_mad_phase5_scope.py::test_shared_state_file[<SHARED_FILE_REFUSED>-claude]` (6); the `SHARED_FILE_KEEPS` ids land in Task 30.
- `tests/test_h_mad_phase5_scope.py::test_claude_arming_line[malformed|raising-function|missing-function]` (3): each refused, the raising function with the present `judge-error`.
- `tests/test_h_mad_phase5_scope.py::test_path_parameters_accept_str_and_path[emit_arming]` (1)

Total 43 test ids, besides the edited helper and id. **Stated counts** (whole files, informational): 43 new ids (guards: the 4 no-record ids, observed failing under `claude-arming-always-hit`), and 583 prior nodes (101 of the wires file, 341 of `test_h_mad_phase5_scope.py`, 141 of `test_h_mad_tdd_gate_judge.py`), of which `test_exempt_write_on_unreadable_chain_is_allowed[state-file]`, moved to refused here, fails at RED and the other 582 pass; GREEN 626 passing.

**Differential**: `CHANGES_IN_FORCE[("claude", "arming")]` gains D6.

**Mutation rows** (`phase5_scope_wires.json`, 9):

| Name | Change | Killed by |
|---|---|---|
| `claude-emit-arming-none` | the process always prints `arming none` | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[session-root-as-named]` |
| `claude-protected-session-named-false` | as Task 21, Claude's killer | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[session-root-as-named]` |
| `claude-protected-session-resolved-false` | as Task 21 | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[session-root-as-resolved]` |
| `claude-protected-target-named-false` | as Task 21 | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[target-checkout-as-named]` |
| `claude-protected-target-resolved-false` | as Task 21 | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[target-checkout-as-resolved]` |
| `claude-arming-judged-filtered` | `emit_arming`'s `judged` is `phase5_scan(root).write` | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[unfiltered-discovery]` |
| `claude-arming-always-hit` | every target is a hit | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[linked-referent]` |
| `claude-allow-arming-test-dropped` | `_allow` no longer tests `ARMING` | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[function-absent]` |
| `claude-allow-always-refuses` | `_allow` always refuses `kind=arming-input` | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[function-absent]` |

**Existing specs to re-anchor**: every spec with an anchor in the Claude hook (plan §"Existing tests and mutation specs affected"): `claude_gate_judge_wiring` (`H11` and `CG-CANON` quote the whole `M:H11` line and are re-anchored with the arming part kept in both `find` and `replace`, so each still changes the canonicalisation alone), `claude_gate_listing`, `listing_connections`, `tdd_gate_scratchpad`, `tdd_gate_differential`, `tdd_gate_fallback_agent`, `tdd_gate_peers`, `grok_wire_reverts`; each anchor must still match once.

**Acceptance Criteria**:
- [ ] AC-24.1: The two tests design §7 names, `test_symlinked_hook_runs_its_own_trees_judge` and `test_hook_reads_authorship_from_the_state_line_not_the_environment`, pass with the `_tree_b` stub and no expectation changed; `test_claude_canon_protocol_error_is_judge_error` is not edited.
- [ ] AC-24.2: With an identity module that has no `emit_arming`, a write the hook would otherwise allow is refused `kind=arming-input`.
- [ ] AC-24.3: The 9 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 10, 20.

---

## Task 25: `read_chain` on the scoped chain (S6)

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_phase5_scope_differential.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_tdd_judge.py:read_chain` → `chain_state_files`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[discovery]`
**WIRE 2**: `h-mad/scripts/h_mad_tdd_judge.py:judged_records` → `applicable`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[applicability]`

**Description**: Row 14 (S6, scope; its unreadable-root and refused-top-level ids protection), design §5: `read_chain(root, target)` is `chain_from(root, target, chain_state_files(root, target))`; `chain_from` reads and judges through `judged_records(root, target, files)`, which gives the first unreadable file with its error, or `None`, and one `Applied` for each live record, those that do not apply included, its `record` a `Record` carrying the reason; `chain_from` keeps those that apply. The conversion is one function: `judged_records` reads each file with `read_state`, takes its `live_records`, calls `applicable(live, session, target)` on those `LiveRecord`s, and maps each result `a` to `Applied(_record_from_live(a.record, a.reason), a.applies, a.reason)`. `_record_from_live(live, reason)` builds the judge's `Record` from the stored data exactly as `_active_records` builds it today (`key` the feature, `codex_status`, `state_file` as a `Path`, `fallback`, `implementer`, `agy_status`), with `reason` and `checkout` (the stored `implementation_checkout`, null and absent alike `None`) last. So the identity module's `Applied` holds a `LiveRecord` and the judge's holds a `Record`; `Applied.record` is annotated `object` for that reason, and no caller reads one where the other is held. Every entry is kept, applying or not, because Task 27's outside-root filter reads the entries that do not apply and their reasons. The session is `session_checkout(root)`, so at a root that cannot be opened every live record applies. `Record` gains two last fields, `reason: str = ""` and `checkout: object = None`, and `_active_records` fills `checkout` as the state file has it (null and absent alike `None`). The `TDD-STATE`, `TDD-JUDGE` and `TDD-LISTING` grammars are unchanged. The legacy readers keep their outcomes over the shared reader, by one adapter: `_state_at(path)` returns `("absent", None)` for an `absent` read, `("unreadable", read.error)` for an `unreadable` one (so a FIFO keeps `not-a-regular-file` and a parse failure its exception's type name), `("unreadable", "not-an-object")` for a `not-object` one, whether the top level or the `orchestrator_state` map is the malformed part, and `("read", data)` otherwise; `judged_records` reports the first file whose read is `unreadable` or `not-object` with that same token; and `_state_status`, which Task 47 moves onto `read_state`, keeps raising for a top level that is not an object (the read's `exception`) and returning `unknown` for a malformed map (`exception` `None`). The existing tests that pin those tokens through `read_chain`, `tests/test_h_mad_tdd_judge.py::test_non_regular_state_is_unreadable[fifo|directory|dangling-symlink]` and `tests/test_h_mad_tdd_judge.py::test_state_that_is_not_an_object_is_unreadable[list-top|state-not-object]`, pass unedited. Because the codex and agy production and listed branches, and the Claude hook's verbs, all reach `read_chain`, this task scopes the Claude surface and the codex and agy write surfaces for those targets, and their acceptance cases land here. The pin ids: `[discovery]` and `[applicability]`, each with an admitted half (the only live record names another checkout, or lies in a git-excluded tree) and a refused half (a record that applies); `[unreadable-root-with-target]`, `[unreadable-root-without-target]`, `[refused-top-level-with-target]`, `[refused-top-level-without-target]`, each run with the root a top level and below one, with the three parts of plan rule 4 (or rule 5's control).

**Code structure**:
```python
class Record(NamedTuple):
    key: str
    codex_status: str
    state_file: Path
    fallback: str
    implementer: str = "absent"
    agy_status: str = "available"
    reason: str = ""
    checkout: object = None

def _record_from_live(live: LiveRecord, reason: str) -> Record: ...
def judged_records(root: Path, target: Optional[Path], files: Sequence[str]) -> Tuple[Optional[Tuple[Path, str]], Tuple["Applied", ...]]: ...  # each Applied's record a Record
def chain_from(root: Path, target: Optional[Path], files: Sequence[str]) -> Chain: ...
def read_chain(root: Path, target: Optional[Path]) -> Chain: ...   # name and arity unchanged
```

**Tests** (informational; `test_same_checkout_feature` ids are guards, observed failing under `chain-applicability-none`):
- `tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[discovery|applicability|unreadable-root-with-target|unreadable-root-without-target|refused-top-level-with-target|refused-top-level-without-target]` (6)
- `tests/test_h_mad_phase5_scope.py::test_fr4_case[<FR4_CASES>-claude|<FR4_CASES>-codex-write|<FR4_CASES>-agy-write]` (48)
- `tests/test_h_mad_phase5_scope.py::test_fr4_more[<FR4_MORE>-claude|<FR4_MORE>-codex-write|<FR4_MORE>-agy-write]` (36)
- `tests/test_h_mad_phase5_scope.py::test_discovery_rule[<DISCOVERY_CASES>-claude|<DISCOVERY_CASES>-codex-write|<DISCOVERY_CASES>-agy-write]` (48)
- `tests/test_h_mad_phase5_scope.py::test_two_checkouts[claude|codex-write|agy-write]` (3), spec AC-3.1.
- `tests/test_h_mad_phase5_scope.py::test_other_feature_other_checkout[claude|codex-write|agy-write]` (3), spec AC-3.2.
- `tests/test_h_mad_phase5_scope.py::test_same_checkout_feature[claude|codex-write|agy-write]` (3), spec AC-3.3.
- `tests/test_h_mad_phase5_scope.py::test_session_unknown[<SESSION_UNKNOWN_CASES>-claude|<SESSION_UNKNOWN_CASES>-judge-verbs]` (12), spec AC-4.16, each with its control.
- `tests/test_h_mad_phase5_scope.py::test_unreadable_beside[applies-claude|applies-codex-write|applies-agy-write|other-checkout-claude|other-checkout-codex-write|other-checkout-agy-write]` (6), spec AC-4.9, every malformed shape inside each id.
- `tests/test_h_mad_phase5_scope.py::test_git_variables[<VARIABLES>-claude]` (4), spec AC-2.8.
- `tests/test_h_mad_phase5_scope_differential.py::test_class_has_difference[D1|D3]` (2)
- `tests/test_h_mad_phase5_scope.py::test_judged_record_shape[chain]` (1): one stored record (a usable checkout, a fallback agent and an implementer) reaches `chain_from`, and the kept entry's `Record` has the key, state file, authoring fields and checkout the store holds and the reason `applicable` gave; Task 27 adds `[listing]`, the same record through the outside-root filter.

On the write surfaces each case is a production write (codex `apply_patch`, agy `write_to_file`, Claude `Write`). Total 172 test ids. **Stated counts** (whole files, informational): 172 new ids (guards: the 3 `test_same_checkout_feature` ids), and 587 prior nodes passing (118 of the wires file, 367 of `test_h_mad_phase5_scope.py`, 102 of the differential file); GREEN 759 passing.

**Differential**: `CHANGES_IN_FORCE[("claude", "other")]`, `[("codex-write", "other")]` and `[("agy-write", "other")]` gain D1 and D3; the `"arming"` keys of those surfaces do not, their arming files still being judged by `unscoped_judge` until Tasks 30, 35 and 38.

**Mutation rows** (`phase5_scope_wires.json`, 8):

| Name | Change | Killed by |
|---|---|---|
| `chain-discovery-unfiltered` | the chain of `7a3cca48` in place of `chain_state_files` | `tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[discovery]` |
| `chain-discovery-empty` | `()` in place of the chain | `tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[discovery]` |
| `chain-applicability-every-record` | every live record applies | `tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[applicability]` |
| `chain-applicability-none` | `()` in place of the applying records | `tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[applicability]` |
| `chain-unreadable-root-empty` | `()` in place of the applying records at an unreadable root | `tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[unreadable-root-with-target]` |
| `chain-session-checkout-of-root` | `checkout_of(root)` in place of `session_checkout(root)` | `tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[unreadable-root-without-target]` |
| `chain-session-fixed-record` | one fixed record applies | `tests/test_h_mad_phase5_scope_wires.py::test_read_chain_wire[refused-top-level-with-target]` |
| `judged-map-shape-dropped` | `judged_records` skips a `not-object` read whose `exception` is `None` (the malformed map) as a file with no live record | `tests/test_h_mad_tdd_judge.py::test_state_that_is_not_an_object_is_unreadable[state-not-object]` |

**Existing specs to re-anchor**: `tdd_judge_chain` (`C1`, `C2`, `C4`, `C6`), `claude_gate_judge_wiring` (`H14`, `C2G`), `tdd_gate_fallback_agent` (its `_active_records` anchor), `listing_matcher` (`LV-*`).

**Acceptance Criteria**:
- [ ] AC-25.1: `read_chain` keeps its name and two positional parameters; the stub judge of `test_codex_gate_judge_timeout_reason` still loads.
- [ ] AC-25.2: On the three write surfaces, with the verdicts of spec FR-4 stated per case as §"Shared case lists" splits them: a record whose checkout cannot be used (every `FR4_CASES` id, and `symlinked-state-no-checkout`, `symlinked-state-dangling`, `symlinked-state-looping` and `moved-checkout`) still gates a production write from a checkout it does not name; a record whose checkout can be used gates a production write from the checkout it names and does not gate one from any other (the linked-worktree and nested ids admitted in the checkout the record does not name, gated in the one it names); and an unreadable file on the chain decides.
- [ ] AC-25.3: The 8 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 5, 6, 24.

---

## Task 26: `state` and `judge` verbs (S6)

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_tdd_judge.py:main` → `read_chain`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[state]`

**Description**: Row 15 (S6, scope; its unreadable-root and refused-top-level ids protection). The one `read_chain(root, target)` call of `main` that serves both the `state` and the `judge` verb stands unedited; Task 25 scoped its callee, so every pin passes at RED and is a guard by convention 10, its RED being its removal mutant's. The ids, as plan row 15: `[state]` (`TDD-STATE: none` when the only live record names another checkout, spec AC-8.4; `TDD-STATE: active` when it names this one); `[judge]` (`TDD-JUDGE: DENY kind=judge-error` on the inactive chain; a measured `TDD-JUDGE: ALLOW` on the applying record, with a production target whose own test fails when it is run); `[state-unreadable-root]`, `[judge-unreadable-root]`, `[state-refused-top-level]`, `[judge-refused-top-level]`, `[state-excluded-tree]`, `[judge-excluded-tree]`. Each mutant of the call runs against the ids of both verbs.

**Code structure**:
```python
def main(argv: Optional[list] = None) -> int: ...  # unedited in this task
```

**Tests** (informational; every id is a guard at RED, and the RED is the removal-mutant observation of convention 10):
- `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[state|judge|state-unreadable-root|judge-unreadable-root|state-refused-top-level|judge-refused-top-level|state-excluded-tree|judge-excluded-tree]` (8)

**Stated counts** (whole files, informational): RED 0 failing, 132 passing (the 8 guards and the 124 prior nodes of the wires file); GREEN 132 passing.

**Mutation rows** (`phase5_scope_wires.json`, 10):

| Name | Change | Killed by |
|---|---|---|
| `verb-chain-every-record-state` | A in place of the call | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[state]` |
| `verb-chain-every-record-judge` | A | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[judge]` |
| `verb-chain-every-file-state` | F | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[state-excluded-tree]` |
| `verb-chain-every-file-judge` | F | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[judge-excluded-tree]` |
| `verb-chain-none-state` | `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[state]` |
| `verb-chain-none-judge` | `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[judge]` |
| `verb-chain-unreadable-root-none-state` | `none` for the unreadable-root ids | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[state-unreadable-root]` |
| `verb-chain-unreadable-root-none-judge` | `none` for the unreadable-root ids | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[judge-unreadable-root]` |
| `verb-chain-fixed-active-state` | a fixed active chain | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[state-refused-top-level]` |
| `verb-chain-fixed-active-judge` | a fixed active chain | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[judge-refused-top-level]` |

**Existing specs to re-anchor**: none (the call is not edited).

**Acceptance Criteria**:
- [ ] AC-26.1: Each of the 10 rows is caught, each verb's ids catching every mutant of the call.

**Dependencies on other tasks**: Task 25.

---

## Task 27: `listing` verb and the outside-root filter (S6)

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_tdd_judge.py:main` → `read_chain`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing]`
**WIRE 2**: `h-mad/scripts/h_mad_tdd_judge.py:main` → `judged_records`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing-outside-root-target-match]`

**Description**: Row 17 (S6), design §5 "A listed non-Python target outside the Claude root". For a name inside the root the `listing` verb keeps its unedited `read_chain(root, names[0])` call (wire 1, a guard at RED). For a name outside the root (the test `chain_state_files` makes of `names[0]`) the verb does not ask `read_chain`: it takes the `judged` of `judged_records(root, names[0], chain_state_files(root, names[0]))`, the root file alone, and gives all of it to the filter, which keeps every record that applies except those with reason `field-absent`. The listing root and the impl-plan looked for follow design §5's table, from `Record.checkout` through `recorded_checkout`. No record kept, or unreadable state, gives `not-listed`, so `test_claude_out_of_root_code_like_allows_beside_unreadable_state` stays unedited; the line that turns unreadable root state into `not-listed` for a name outside the root carries the marker `# M:H-LIST-INROOT` (Task 29 re-anchors that row onto it); an unreadable impl-plan of a kept record is `unreadable`. The name of the `other-checkout` id and of the unusable ids' control lies in a checkout nested in the named one; the `target-unknown` name lies below a directory whose `.git` file names a missing git directory. Ids: `[listing]`, `[listing-excluded-tree]`, `[listing-unreadable-root]`, `[listing-refused-top-level]`; `[listing-outside-root-<OUTSIDE_ROOT_REASONS>]`; and `[listing-outside-root-unusable-<UNUSABLE_CASES>]`, one for each of spec AC-4.2 to AC-4.8, each asserting which unusable reason occurs.

**Code structure**:
```python
def main(argv: Optional[list] = None) -> int: ...  # the listing verb gains the outside-root branch and its filter
```

**Tests** (informational; the four in-root ids are guards at RED):
- `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing|listing-excluded-tree|listing-unreadable-root|listing-refused-top-level|listing-outside-root-target-match|listing-outside-root-checkout-match|listing-outside-root-session-unknown|listing-outside-root-target-unknown|listing-outside-root-other-checkout|listing-outside-root-field-absent|listing-outside-root-unusable-not-string|listing-outside-root-unusable-empty|listing-outside-root-unusable-relative|listing-outside-root-unusable-missing-path|listing-outside-root-unusable-names-file|listing-outside-root-unusable-not-top-level|listing-outside-root-unusable-checkout-unreadable]` (17)
- `tests/test_h_mad_phase5_scope.py::test_judged_record_shape[listing]` (1): Task 25's stored record through the outside-root filter; the kept entry's `Record` equals the one `[chain]` reads.

Total 18 test ids. **Stated counts** (whole files, informational): 18 new ids (guards: the 4 in-root ids), and 663 prior nodes passing (132 of the wires file, 531 of `test_h_mad_phase5_scope.py`); GREEN 681 passing.

**Mutation rows** (`phase5_scope_wires.json`, 9):

| Name | Change | Killed by |
|---|---|---|
| `listing-chain-every-record` | A in place of the in-root call | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing]` |
| `listing-chain-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing-excluded-tree]` |
| `listing-chain-none` | `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing]` |
| `listing-chain-unreadable-root-none` | `none` for the unreadable-root id | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing-unreadable-root]` |
| `listing-chain-fixed-active` | a fixed active chain | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing-refused-top-level]` |
| `filter-keeps-every-record` | the filter keeps every live record | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing-outside-root-other-checkout]` |
| `filter-keeps-none` | the filter keeps no record | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing-outside-root-target-match]` |
| `filter-drops-unusable` | the four unusable reasons are dropped | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing-outside-root-unusable-not-string]` |
| `filter-unusable-keeps-every-record` | every live record is kept, read on the unusable ids' control | `tests/test_h_mad_phase5_scope_wires.py::test_judge_verb_wire[listing-outside-root-unusable-empty]` |

`field-absent` is counted on for neither filter mutant (design §5).

**Existing specs to re-anchor**: `listing_matcher` (`LV-*`), `listing_connections`.

**Acceptance Criteria**:
- [ ] AC-27.1: For a name outside the root, a record that applies with a checkout field is kept and its listed name is `listed`; `field-absent` and `other-checkout` give `not-listed`.
- [ ] AC-27.2: The 9 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 25.

---

## Task 28: `scope` verb (S6)

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py`
**Test file**: `h-mad/tests/test_h_mad_tdd_judge_scope.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_tdd_judge.py:scope` → `session_state_files`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[discovery]`
**WIRE 2**: `h-mad/scripts/h_mad_tdd_judge.py:scope` → `session_checkout`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[session]`
**WIRE 3**: `h-mad/scripts/h_mad_tdd_judge.py:scope` → `Scan.shell`
**WIRE-PIN 3**: `h-mad/tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[target]`
**WIRE 4**: `h-mad/scripts/h_mad_tdd_judge.py:scope` → `applicable`
**WIRE-PIN 4**: `h-mad/tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[directory]`
**WIRE 5**: `h-mad/scripts/h_mad_tdd_judge.py:scope` → `stage_gates_shell`
**WIRE-PIN 5**: `h-mad/tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[stage]`

**Description**: Row 24 (S6, value), design §11 and spec FR-8: `h_mad_tdd_judge.py scope --root R [--target T | --directory D]`, relative `T` and `D` joined to the root, `--directory ''` being `directory-unknown`. Records: the target's chain with a target, else the session's files. Output as FR-8 gives it, values through `_enc`; `unreadable` names the first unreadable file in discovery order; `session` is `unknown` or the encoded top; `shell` is the record's part of `Scan.shell` over the session's files, with `directory=D` for `--directory` and `None` otherwise, `gates` being `stage_gates_shell` and `every_stage` at a root that cannot be opened. The text is built whole before it is printed, so an internal error exits 2 with nothing on stdout. The five pins are plan row 24's ids, with the content that row gives each (`[session]` with the unreadable root, its readable twin, the inactive part and `[refused-top-level]`; `[target]` with `applies=yes shell=no` for a `target-match` record and for a nested checkout's file only the chain reaches, beside one with `applies=yes shell=yes`; `[stage]` with its `"planning"` cases).

OPEN-DECISION: OD-9, three fixtures (the `scope` fixture where `lstat` cannot decide the root's own state file, spec AC-8.1; the `Scan.write` fixtures of Task 6; the AC-10.1 corpus of Task 1) are outside the case of spec FR-10's residual, and the public text no longer says which state they are in — resolve in 5d. Named implementation: each such fixture is built in the state the private record names (see the private record), and its builder asserts, under every interpreter of `INTERPRETERS`, that `os.lstat` of the path raises an `OSError` other than `FileNotFoundError` and `NotADirectoryError`, so the fixture is in the class the design means; the builder's assertion text names no more than that.

**Code structure**:
```python
def scope(root: Path, target: Optional[Path], directory: Optional[str]) -> str: ...  # the whole TDD-SCOPE text
def main(argv: Optional[list] = None) -> int: ...  # gains the "scope" verb
```

**Tests** (informational; the 3 `test_scope_allow_is_silent` ids are guards, the grammars being unchanged, each observed failing under its own `-allow-not-silent` row below):
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[discovery|session|target|directory|stage]` (5)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_reason_tokens[checkout-match|target-match|directory-match|session-unknown|target-unknown|directory-unknown|field-absent|field-invalid|path-missing|not-a-checkout|checkout-unreadable|other-checkout]` (12), spec AC-8.1's first sentence.
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_summary_tokens[none|unreadable|records]` (3)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_agrees_with_hooks[claude]` (1), spec AC-8.1 on the Claude hook.
- `tests/test_h_mad_tdd_judge_scope.py::test_unreadable_agrees_with_hooks[target]` (1): asked about a target inside the root, a production write to it is refused on the three hooks, for each record combination.
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_encoding[space|newline|equals|non-ascii]` (4), spec AC-8.2.
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_allow_is_silent[claude|codex-write|agy-write]` (3), spec AC-8.3.
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_usage[empty-directory-is-unknown|relative-joined|internal-error-exit-2]` (3)
- `tests/test_h_mad_phase5_scope.py::test_stage_callers_agree[scope-verb]` (1)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_lstat_undecided[target-<INTERPRETERS>]` (6): `--target` inside the root prints `unreadable`, and a production write to it is refused on the three hooks.
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_root_unopenable` (1): every form prints `unreadable`, and codex refuses the command.

Total 40 test ids. **Stated counts** (whole files, informational): 40 new ids (3 guards, as above), and 532 prior nodes passing (`test_h_mad_phase5_scope.py`; the judge-scope file is new); GREEN 572 passing.

**Mutation rows** (`tdd_judge_scope.json`, 13):

| Name | Change | Killed by |
|---|---|---|
| `scope-discovery-unscoped` | the session's files are the walk of `7a3cca48` | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[discovery]` |
| `scope-discovery-fixed` | one fixed list of files | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[discovery]` |
| `scope-session-unscoped` | the session checkout is always `unknown` | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[session]` |
| `scope-session-fixed` | one fixed checkout | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[session]` |
| `scope-target-shell-from-applies` | `shell` is taken from `applies` | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[target]` |
| `scope-target-shell-fixed-no` | `shell` is fixed at `no` | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[target]` |
| `scope-directory-unscoped` | the directory is not passed | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[directory]` |
| `scope-directory-fixed` | one fixed directory | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[directory]` |
| `scope-stage-true` | `gates` is `lambda record: True` | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[stage]` |
| `scope-stage-false` | `gates` is `lambda record: False` | `tests/test_h_mad_tdd_judge_scope.py::test_scope_verb_wire[stage]` |
| `claude-allow-not-silent` | the Claude hook's `_allow` prints the `TDD-STATE` line before it exits | `tests/test_h_mad_tdd_judge_scope.py::test_scope_allow_is_silent[claude]` |
| `codex-write-allow-not-silent` | the codex hook prints `{}` on its allow path | `tests/test_h_mad_tdd_judge_scope.py::test_scope_allow_is_silent[codex-write]` |
| `agy-write-allow-not-silent` | agy's allow object gains a `reason` key | `tests/test_h_mad_tdd_judge_scope.py::test_scope_allow_is_silent[agy-write]` |

The three `-allow-not-silent` rows change the hooks, as this spec's `root` (`../..`) allows.

**Existing specs to re-anchor**: `tdd_judge_chain`, `claude_gate_judge_wiring`, `listing_matcher` re-run in full (anchors in `main`).

**Acceptance Criteria**:
- [ ] AC-28.1: The verb exits 0 for every judged result and 2 with nothing on stdout for a usage or internal error.
- [ ] AC-28.2: The 13 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 6, 25.

---

## Task 29: Claude hook through the verbs (S6)

**Production file**: `h-mad/hooks/h-mad-tdd-gate.sh`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-tdd-gate.sh:_read_state` → `state`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[state]`
**WIRE 2**: `h-mad/hooks/h-mad-tdd-gate.sh:_read_listing` → `listing`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[listing]`
**WIRE 3**: `h-mad/hooks/h-mad-tdd-gate.sh:JOUT` → `judge`
**WIRE-PIN 3**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[judge]`

**Description**: Row 18 (S6, scope; its unreadable-root, refused-top-level and unusable-checkout ids protection). Scope reaches the Claude hook through the judge verbs (design §8); the one shell change here is the out-of-root listing call: a non-Python target outside the root that no earlier allow admits is judged by the `listing` verb (Task 27) in place of the allow marked `M:H-LIST-INROOT`, and a listed name continues to the `state` and `judge` verbs. A write with no target, or an unresolvable one, is judged by `state --root` without a target, the root file alone (design §5). Each pin is driven through the real hook with that one verb call bypassed by a mutant; each admitted case reaches the bypassed call and no later verb admits by itself (plan row 18). Ids: `[state]`, `[judge]`, `[listing]`; `[listing-outside-root-<OUTSIDE_ROOT_REASONS>]` and `[listing-outside-root-unusable-<UNUSABLE_CASES>]`; `[no-target]`, `[unresolvable]`, `[refused-top-level]`, `[unreadable-root]`.

**Code structure**:
```bash
# h-mad-tdd-gate.sh: the out-of-root early allow of a non-Python target gives way to _read_listing
```

**Tests** (informational):
- `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[state|judge|listing|listing-outside-root-<OUTSIDE_ROOT_REASONS>|listing-outside-root-unusable-<UNUSABLE_CASES>|no-target|unresolvable|refused-top-level|unreadable-root]` (20). RED split: `[state]` and `[judge]` are in-root connections whose callees Task 25 already scoped and whose calls stand on the tree, so they pass at RED and are guards, observed failing under their removal rows (`[state]`, the `test` of `claude-state-fixed-active` and `claude-state-fixed-none`; `[judge]`, the `test` of `claude-judge-fixed-deny` and `claude-judge-fixed-allow`), which the orchestrator applies at RED as convention 10 describes and records in the RED report; the `listing` ids fail at RED, the out-of-root listing call being this task's one shell change; for `[no-target]`, `[unresolvable]`, `[refused-top-level]` and `[unreadable-root]` the split is the RED report's (convention 15), and any that passes is a guard credited under one named row: `[unreadable-root]` is the `test` of `claude-state-fixed-none-protection` and `[refused-top-level]` the `test` of `claude-state-fixed-active-protection`, each scored by the harness; `[no-target]` and `[unresolvable]` are observed, by convention 9's observation procedure, under `claude-state-fixed-active`, whose change is at the one `state` call of `_read_state` (the line marked `M:W5B`, `state --root "$ROOT_ABS" "$@"`), the call both paths make with no target argument (the `-z "$TARGET_PATH"` branch and the `CANON_UNRESOLVABLE=yes` branch of `h-mad/hooks/h-mad-tdd-gate.sh`). The row reaches each id through its admitted half, which reads `TDD-STATE: none` from the real verb and is allowed by `_read_state`: the only live record names another checkout, and for `[unresolvable]` its state file lies on the chain, so `_chain_may_hold_state` does not allow before `_read_state` is called; under the row that half reads a fixed active line and is refused.
- `tests/test_h_mad_phase5_scope.py::test_production_into_second_checkout[claude]` (1), spec AC-3.4.

Total 21 test ids. **Stated counts** (whole files, informational): 21 new ids, and 682 prior nodes passing (149 of the wires file, 533 of `test_h_mad_phase5_scope.py`); GREEN 703 passing.

**Mutation rows** (`phase5_scope_wires.json`, 10):

| Name | Change | Killed by |
|---|---|---|
| `claude-state-fixed-active` | the `state` answer is a fixed active line | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[state]` |
| `claude-state-fixed-none` | a fixed `TDD-STATE: none` | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[state]` |
| `claude-state-fixed-none-protection` | a fixed `TDD-STATE: none`, read at the unreadable root | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[unreadable-root]` |
| `claude-state-fixed-active-protection` | a fixed active line, read on the refused top level's control | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[refused-top-level]` |
| `claude-listing-fixed-listed` | a fixed `listed` answer | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[listing]` |
| `claude-listing-fixed-not-listed` | a fixed `not-listed` answer | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[listing-outside-root-target-match]` |
| `claude-listing-fixed-not-listed-protection` | a fixed `not-listed`, read on an unusable id | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[listing-outside-root-unusable-not-string]` |
| `claude-listing-fixed-listed-protection` | a fixed `listed`, read on the unlisted name of an unusable id | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[listing-outside-root-unusable-empty]` |
| `claude-judge-fixed-deny` | a fixed refusing `TDD-JUDGE` line | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[judge]` |
| `claude-judge-fixed-allow` | a fixed measured `ALLOW` line | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[judge]` |

**Existing specs to re-anchor**: `claude_gate_listing`'s `H-LIST-INROOT`, whose anchor, the out-of-root early allow `[ "$IN_ROOT" = yes ] || _allow  # M:H-LIST-INROOT` of `h-mad/hooks/h-mad-tdd-gate.sh`, this task removes. Its mechanism ("Read the governing root's unreadable state for an outside-root code-like target") and its killer (`tests/test_h_mad_tdd_gate_non_py.py::test_claude_out_of_root_code_like_allows_beside_unreadable_state`, whose root state file holds the bytes `\xff\xfe`, so no record is read at all) stay: the row moves to `scripts/h_mad_tdd_judge.py`, onto the line Task 27 marks `# M:H-LIST-INROOT`, the outside-root branch's suppression of unreadable root state, and its `replace` makes that branch return the unreadable answer, so the hook refuses `judge-error` and the killer, which requires an allow, fails. It is not moved onto the AC-3.4 filter: with unreadable state there is no live record for the filter to keep or drop, so a mutant of the filter cannot change that test's decision. The filter's mutations are Task 27's `filter-*` rows. The other Claude-hook specs Task 24 names are re-anchored as there, each anchor still matching once.

**Acceptance Criteria**:
- [ ] AC-29.1: A listed non-Python target outside the Claude root is refused for each kept reason and each unusable case, and `test_claude_out_of_root_code_like_allows_beside_unreadable_state` passes unedited.
- [ ] AC-29.2: The 10 rows are caught, and the re-anchored `H-LIST-INROOT` of `claude_gate_listing` by its unedited killer; the full suite passes.

**Dependencies on other tasks**: Tasks 25, 26, 27.

---

## Task 30: Claude arming files re-routed (S6)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_target_identity.py:emit_arming` → `Scan.write`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[other-checkout]`

**Description**: Row 19 (S6, scope): `emit_arming`'s `judged` becomes the scan's `write`, so the FR-6 check on Claude considers a name only when a record applies to the session or to the target, and the hit's reason is the applying record's. `[other-checkout]`: a state file and a `.git` target in the session's checkout keep their present decision when the only live record names another checkout; its opposite half runs `[target-checkout-as-named]` from a session the record does not name, so the target's part alone refuses. Task 24's `[unfiltered-discovery]` id is replaced by `[excluded-tree]`, the same fixture with the opposite decision (admitted), and Task 24's row `claude-arming-judged-filtered`, whose mutant this task makes the code, is removed from the spec (plan rule 2). Task 24's other refused ids run again with a record that applies.

**Code structure**:
```python
def emit_arming(root: PathArg, raw: str, identity: Identity) -> None: ...  # judged = the scan's write
```

**Tests** (informational): 4 ids added, 1 removed.
- `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[other-checkout|excluded-tree]` (2)
- `tests/test_h_mad_phase5_scope.py::test_shared_state_file[<SHARED_FILE_KEEPS>-claude]` (2), the present decisions of spec AC-6.7 and AC-6.8 on Claude, which hold now that a record that does not apply no longer counts.
- Removed: `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[unfiltered-discovery]` (Task 24).

**Stated counts** (whole files, informational): 4 new ids, and 702 prior nodes passing (169 of the wires file less the removed id, so 168, and 534 of `test_h_mad_phase5_scope.py`); GREEN 706 passing.

**Differential**: `CHANGES_IN_FORCE[("claude", "arming")]` gains every class `("claude", "other")` holds (convention 12's re-routing rule).

**Mutation rows** (`phase5_scope_wires.json`, 3 added, 1 removed):

| Name | Change | Killed by |
|---|---|---|
| `claude-arming-judged-every-record` | `judged` gives the status of A | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[other-checkout]` |
| `claude-arming-judged-every-file` | `judged` gives the status of F | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[excluded-tree]` |
| `claude-arming-judged-inactive` | `judged` is `lambda name: INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_claude_arming_file_wire[session-root-as-named]` |

Removed: `claude-arming-judged-filtered` (Task 24).

**Existing specs to re-anchor**: none beyond Task 24's.

**Acceptance Criteria**:
- [ ] AC-30.1: With the only live record naming another checkout, a Claude write to the session's own state file keeps its present decision; with a record that applies, every Task 24 refusal stands.
- [ ] AC-30.2: The 3 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 24, 25.

---

## Task 31: codex production and listed targets (S6)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `read_chain`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[production-other-checkout]`
**WIRE 2**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_judge_listed` → `read_chain`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[listed-other-checkout]`

**Description**: Row 32 (S6, scope; the `target-checkout-unknown` ids protection). The two `judge.read_chain` calls of the codex hook (the production branch marked `M:W5A` and `_judge_listed`) stand unedited and read no session status; Task 25 scoped their callee, so every id passes at RED and is a guard by convention 10. Each id runs once as `production-` and once as `listed-` (a listed name that is neither Python nor document data): `other-checkout` (admitted), `excluded-tree` (admitted), `target-in-named-checkout` (refused), `target-checkout-unknown` (refused: the target's directory holds a `.git` file naming a missing git directory), and `unreadable` (an unparsable state file in a sub-project off the target's chain leaves the target admitted, as at `7a3cca48`; the same file moved onto the chain refuses it; spec AC-3.6, AC-4.9). `test_codex_hook_scopes_nested_state_to_the_target_project` and the mutations `W5AR`, `W5AF`, `CX-CHAIN-TARGET` are unedited.

**Code structure**:
```python
# h-mad-codex-tdd-gate.py: no edit; the two calls are pinned and mutated
```

**Tests** (informational; every id is a guard at RED, and the RED is the removal-mutant observation of convention 10):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[production-other-checkout|production-excluded-tree|production-target-in-named-checkout|production-target-checkout-unknown|production-unreadable|listed-other-checkout|listed-excluded-tree|listed-target-in-named-checkout|listed-target-checkout-unknown|listed-unreadable]` (10)

**Stated counts** (whole files, informational): RED 0 failing, 180 passing (the 10 guards and the 170 prior nodes of the wires file); GREEN 180 passing.

**Mutation rows** (`phase5_scope_wires.json`, 14; seven per call):

| Name | Change | Killed by |
|---|---|---|
| `codex-production-chain-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[production-other-checkout]` |
| `codex-production-chain-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[production-excluded-tree]` |
| `codex-production-chain-none` | `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[production-target-in-named-checkout]` |
| `codex-production-chain-none-protection` | `Chain("none", (), None, "")`, read on the protection id | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[production-target-checkout-unknown]` |
| `codex-production-chain-fixed-active` | a fixed active chain | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[production-other-checkout]` |
| `codex-production-chain-session-unreadable` | `Chain("unreadable", (), path, error)` when any file of `phase5_scan(root)` cannot be read, else the real answer | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[production-unreadable]` |
| `codex-production-chain-unreadable-as-none` | the real answer, with `unreadable` read as `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[production-unreadable]` |
| `codex-listed-chain-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[listed-other-checkout]` |
| `codex-listed-chain-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[listed-excluded-tree]` |
| `codex-listed-chain-none` | `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[listed-target-in-named-checkout]` |
| `codex-listed-chain-none-protection` | `Chain("none", (), None, "")`, read on the protection id | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[listed-target-checkout-unknown]` |
| `codex-listed-chain-fixed-active` | a fixed active chain | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[listed-other-checkout]` |
| `codex-listed-chain-session-unreadable` | `Chain("unreadable", (), path, error)` when any file of `phase5_scan(root)` cannot be read, else the real answer | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[listed-unreadable]` |
| `codex-listed-chain-unreadable-as-none` | the real answer, with `unreadable` read as `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_chain_wire[listed-unreadable]` |

The two `unreadable` rows of a call are caught by the two halves of its `unreadable` id.

**Existing specs to re-anchor**: none (the calls are not edited).

**Acceptance Criteria**:
- [ ] AC-31.1: The 14 rows are caught.

**Dependencies on other tasks**: Task 25.

---

## Task 32: agy production and listed targets (S6)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `read_chain`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[production-other-checkout]`
**WIRE 2**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `read_chain`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[listed-other-checkout]`

**Description**: Row 33 (S6, as row 32): agy's production `read_chain(root, absolute)` call (wire 1) and its listed `read_chain(root, names[0])` call (wire 2), both unedited. The ids are `CHAIN_IDS`, with Task 31's meanings, on agy. `AG-CHAIN-TARGET` and `fr4-t6-t7-skipped-when-inactive` are unedited; the production call, which no mutation changes today, gets this task's.

**Code structure**:
```python
# h-mad-agy-tdd-gate.py: no edit; the two calls are pinned and mutated
```

**Tests** (informational; every id is a guard at RED, and the RED is the removal-mutant observation of convention 10):
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[<CHAIN_IDS>]` (10)

**Stated counts** (whole files, informational): RED 0 failing, 190 passing (the 10 guards and the 180 prior nodes of the wires file); GREEN 190 passing.

**Mutation rows** (`phase5_scope_wires.json`, 14; seven per call):

| Name | Change | Killed by |
|---|---|---|
| `agy-production-chain-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[production-other-checkout]` |
| `agy-production-chain-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[production-excluded-tree]` |
| `agy-production-chain-none` | `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[production-target-in-named-checkout]` |
| `agy-production-chain-none-protection` | `Chain("none", (), None, "")`, read on the protection id | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[production-target-checkout-unknown]` |
| `agy-production-chain-fixed-active` | a fixed active chain | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[production-other-checkout]` |
| `agy-production-chain-session-unreadable` | `Chain("unreadable", (), path, error)` when any file of `phase5_scan(root)` cannot be read, else the real answer | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[production-unreadable]` |
| `agy-production-chain-unreadable-as-none` | the real answer, with `unreadable` read as `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[production-unreadable]` |
| `agy-listed-chain-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[listed-other-checkout]` |
| `agy-listed-chain-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[listed-excluded-tree]` |
| `agy-listed-chain-none` | `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[listed-target-in-named-checkout]` |
| `agy-listed-chain-none-protection` | `Chain("none", (), None, "")`, read on the protection id | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[listed-target-checkout-unknown]` |
| `agy-listed-chain-fixed-active` | a fixed active chain | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[listed-other-checkout]` |
| `agy-listed-chain-session-unreadable` | `Chain("unreadable", (), path, error)` when any file of `phase5_scan(root)` cannot be read, else the real answer | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[listed-unreadable]` |
| `agy-listed-chain-unreadable-as-none` | the real answer, with `unreadable` read as `Chain("none", (), None, "")` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_chain_wire[listed-unreadable]` |

The two `unreadable` rows of a call are caught by the two halves of its `unreadable` id.

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-32.1: The 14 rows are caught.

**Dependencies on other tasks**: Task 25.

---

## Task 33: codex refusals without a resolvable target (S7)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `Scan.session`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[session-level-bad-header]`

**Description**: Row 4 (S7, scope): the three codex write refusals that have no resolvable target (a bad patch header, no target, an unresolvable target) read `scan.session()` (rules 1 to 3, stage not consulted) in place of today's status, `scan` being the `phase5_scan(root)` computed beside it. Ids, one per refusal: `[session-level-bad-header]`, `[session-level-no-target]`, `[session-level-unresolvable]`, each admitted when the only live record names another checkout and refused when it applies to the session, without a stage and at `"planning"` (that refused half is also S9's control); `[refused-top-level-bad-header]`, `[refused-top-level-no-target]` and `[refused-top-level-unresolvable]`, refused in both, each with its control admitted; and the rule 3 siblings `[excluded-tree-bad-header]`, `[excluded-tree-no-target]` and `[excluded-tree-unresolvable]`.

OPEN-DECISION: OD-2, removal A's status form puts `LiveRecord` values where `Applied` values are read, so a hook can fail with its exception refusal under the mutant and appear to kill it — resolve in 5d. Named implementation: A's status form is `Status("active", tuple(Applied(r, True, applicable((r,), Checkout(None, False))[0].reason) for r in scan.records if gates(r))) if any(gates(r) for r in scan.records) else original`, `original` being the expression it replaces, where `gates` is the call's own predicate on a shell and `every_stage` elsewhere, so each entry is a well-formed `Applied` whose reason `applicable` itself gives and the stage predicate is kept; and every test that kills an A row asserts the refusal's kind and the feature it names, not only that a refusal happened. Because a test's discriminating half usually expects an allow, which a catch-all denial also fails, a kill of an A row is credited only on the mutated outcome: each test named for an A row prints, before it asserts, one line `OUTCOME: <decision> kind=<kind> reason=<the reason's first 120 characters>` for each hook call it makes; after the harness scores the row, the orchestrator applies the row by convention 9's observation procedure, runs the killing test, and reads that line in pytest's captured output for the failing half; the kill is credited when the refusal is the mutated branch's own (its kind and its branch's reason text, such as the session-level bad-header refusal's `patch has a bad header`), and is recorded as a crash kill, not credited, when it is the catch-all: on codex, the reason beginning `H-MAD Phase 5 gate raised` (it names the exception's type); on agy, the reason equal to `Gate could not reach a judgement. kind=judge-error`, the fixed text the `finally` of `h-mad/hooks/h-mad-agy-tdd-gate.py` gives when no decision was reached (line 282, after the `except Exception:` of line 274), compared whole, because on agy the kind `judge-error` is shared with the branch refusals of lines 124 to 256 and only the text tells them apart. That agy text is also the decision of an `unknown` status on a tool outside the admitted classes (the comment at line 273, `Unknown activity leaves the finally's fail-closed decision in force`), so an agy kill whose mutated branch's own refusal is that text cannot be told from a crash by this line, and is recorded as a crash kill, not credited. Convention 7 makes this the form of A in every task.

**Code structure**:
```python
def _main_guarded() -> int: ...  # the three refusals read scan.session()
```

**Tests** (informational):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[session-level-bad-header|session-level-no-target|session-level-unresolvable|refused-top-level-bad-header|refused-top-level-no-target|refused-top-level-unresolvable|excluded-tree-bad-header|excluded-tree-no-target|excluded-tree-unresolvable]` (9)

**Stated counts** (whole files, informational): 9 new ids, and 190 prior nodes passing (the wires file); GREEN 199 passing.

**Differential**: `CHANGES_IN_FORCE[("codex-write", "other")]` gains D2 and D4, the session-level refusals now reading the session's discovery (a nested checkout's file no longer counts among its files, and every presence case counts).

**Mutation rows** (`phase5_scope_wires.json`, 9; three per refusal):

| Name | Change | Killed by |
|---|---|---|
| `codex-session-bad-header-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[session-level-bad-header]` |
| `codex-session-bad-header-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[excluded-tree-bad-header]` |
| `codex-session-bad-header-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[refused-top-level-bad-header]` |
| `codex-session-no-target-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[session-level-no-target]` |
| `codex-session-no-target-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[excluded-tree-no-target]` |
| `codex-session-no-target-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[refused-top-level-no-target]` |
| `codex-session-unresolvable-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[session-level-unresolvable]` |
| `codex-session-unresolvable-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[excluded-tree-unresolvable]` |
| `codex-session-unresolvable-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[refused-top-level-unresolvable]` |

**Existing specs to re-anchor**: `codex_gate_judge_wiring` (`CX-GOV` and the anchors on these refusals), each still matching once.

**Acceptance Criteria**:
- [ ] AC-33.1: Each refusal is admitted from a session whose only live record names another checkout and refused when a record applies, at `"planning"` included.
- [ ] AC-33.2: The 9 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 6, 21.

---

## Task 34: codex per-target branches (S7)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `Scan.write`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[target-in-named-checkout-outside-root]`
**WIRE 2**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `Scan.write`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[target-in-named-checkout-allowance-file]`

**Description**: Row 5 (S7, protection or scope by id): the codex branches that ask the session's status for a resolvable target read `scan.write(target)`: the outside-the-root branch (wire 1) and the allowance-file branch marked `M:SA-GUARD` (wire 2). `_target_identity` is the part of `_relative_target` before its containment filter, so the outside-the-root branch has an identity for `write` (design §8). Ids, `<PER_TARGET_IDS>-outside-root` and `<PER_TARGET_IDS>-allowance-file`: `target-in-named-checkout` (protection, refused), `other-checkout` (scope, admitted), `target-checkout-unknown` (protection, refused: a resolvable target whose checkout git cannot identify), `excluded-tree` (rule 3). For the allowance file the `.h-mad` directory is, in the first and the third, itself the named checkout or the one git cannot identify.

**Code structure**:
```python
def _target_identity(root: Path, raw: str, cwd: Any = None) -> Identity | None: ...
def _relative_target(root: Path, raw: str, cwd: Any = None) -> Identity | None: ...  # its containment filter over _target_identity
def _main_guarded() -> int: ...
```

**Tests** (informational):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[<PER_TARGET_IDS>-outside-root|<PER_TARGET_IDS>-allowance-file]` (8)
- `tests/test_h_mad_phase5_scope.py::test_production_into_second_checkout[codex]` (1), spec AC-3.4; a guard, observed failing under `codex-write-outside-root-session-only`.

Total 9 test ids. **Stated counts** (whole files, informational): 9 new ids (the guard as named), and 735 prior nodes passing (199 of the wires file, 536 of `test_h_mad_phase5_scope.py`); GREEN 744 passing.

**Mutation rows** (`phase5_scope_wires.json`, 10; five per branch):

| Name | Change | Killed by |
|---|---|---|
| `codex-write-outside-root-session-only` | `scan.session()` in place of `scan.write(target)` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[target-in-named-checkout-outside-root]` |
| `codex-write-outside-root-active` | `ACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[other-checkout-outside-root]` |
| `codex-write-outside-root-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[other-checkout-outside-root]` |
| `codex-write-outside-root-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[excluded-tree-outside-root]` |
| `codex-write-outside-root-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[target-in-named-checkout-outside-root]` |
| `codex-write-allowance-file-session-only` | `scan.session()` in place of `scan.write(target)` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[target-in-named-checkout-allowance-file]` |
| `codex-write-allowance-file-active` | `ACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[other-checkout-allowance-file]` |
| `codex-write-allowance-file-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[other-checkout-allowance-file]` |
| `codex-write-allowance-file-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[excluded-tree-allowance-file]` |
| `codex-write-allowance-file-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[target-in-named-checkout-allowance-file]` |

**Existing specs to re-anchor**: `codex_gate_shell_allowance` (`codex-may-write-the-allowance`, `guard-outlives-phase5`), `codex_gate_judge_wiring`.

**Acceptance Criteria**:
- [ ] AC-34.1: A production write from the first checkout into the second, when the record names the second, is refused on codex.
- [ ] AC-34.2: The 10 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 33.

---

## Task 35: codex arming files re-routed (S7)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_tdd_judge_scope.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `Scan.write`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[other-checkout]`

**Description**: Row 6 (S7, scope): the `judged` given to `arming_target` on codex becomes `scan.write`, the answer the branches of row 5 take. As Task 30 on Claude: `[other-checkout]` and its opposite; Task 21's `[unfiltered-discovery]` is replaced by `[excluded-tree]` (same fixture, admitted); Task 21's row `codex-arming-judged-filtered` is removed.

**Code structure**:
```python
def _main_guarded() -> int: ...  # arming_target's judged = scan.write
```

**Tests** (informational): 5 ids added, 1 removed.
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[other-checkout|excluded-tree]` (2)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_agrees_with_hooks[codex-write]` (1), spec AC-8.1 on the codex write surfaces, its corpus holding an FR-6 target.
- `tests/test_h_mad_phase5_scope.py::test_shared_state_file[<SHARED_FILE_KEEPS>-codex]` (2), as Task 30 on codex.
- Removed: `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[unfiltered-discovery]` (Task 21).

**Stated counts** (whole files, informational): 5 new ids, and 782 prior nodes passing (207 of the wires file less the removed id, so 206; 39 of the judge-scope file; 537 of `test_h_mad_phase5_scope.py`); GREEN 787 passing.

**Differential**: `CHANGES_IN_FORCE[("codex-write", "arming")]` gains every class `("codex-write", "other")` holds (convention 12's re-routing rule).

**Mutation rows** (`phase5_scope_wires.json`, 3 added, 1 removed):

| Name | Change | Killed by |
|---|---|---|
| `codex-arming-judged-every-record` | `judged` gives the status of A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[other-checkout]` |
| `codex-arming-judged-every-file` | `judged` gives the status of F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[excluded-tree]` |
| `codex-arming-judged-inactive` | `judged` is `lambda name: INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_file_wire[session-root-as-named]` |

Removed: `codex-arming-judged-filtered` (Task 21).

**Existing specs to re-anchor**: as Task 21.

**Acceptance Criteria**:
- [ ] AC-35.1: The 3 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 34.

---

## Task 36: agy refusals without a resolvable target (S7)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `Scan.session`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[session-level-no-path-key]`

**Description**: Row 10 (S7, scope): the agy write refusals that have no resolvable target (no recognised path key, an unresolvable target, and the workspace mismatch on a write tool) read `scan.session()`. The workspace-mismatch check is split by class: a write tool reads the session status here; `run_command` reads the shell status in Task 43, and tools outside the admitted classes the session status in Task 45. Ids: `[session-level-no-path-key]`, `[session-level-unresolvable]`, `[session-level-workspace-mismatch]`, each with both halves of row 4, and the rule 3 siblings `[excluded-tree-no-path-key]`, `[excluded-tree-unresolvable]` and `[excluded-tree-workspace-mismatch]`. agy does not meet a refused top level.

**Code structure**:
```python
def main() -> int: ...  # the three refusals read scan.session()
```

**Tests** (informational):
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[session-level-no-path-key|session-level-unresolvable|session-level-workspace-mismatch|excluded-tree-no-path-key|excluded-tree-unresolvable|excluded-tree-workspace-mismatch]` (6)

**Stated counts** (whole files, informational): 6 new ids, and 208 prior nodes passing (the wires file); GREEN 214 passing.

**Differential**: `CHANGES_IN_FORCE[("agy-write", "other")]` gains D2 and D4, as Task 33 on codex.

**Mutation rows** (`phase5_scope_wires.json`, 9; three per refusal):

| Name | Change | Killed by |
|---|---|---|
| `agy-session-no-path-key-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[session-level-no-path-key]` |
| `agy-session-no-path-key-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[excluded-tree-no-path-key]` |
| `agy-session-no-path-key-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[session-level-no-path-key]` |
| `agy-session-unresolvable-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[session-level-unresolvable]` |
| `agy-session-unresolvable-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[excluded-tree-unresolvable]` |
| `agy-session-unresolvable-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[session-level-unresolvable]` |
| `agy-session-workspace-mismatch-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[session-level-workspace-mismatch]` |
| `agy-session-workspace-mismatch-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[excluded-tree-workspace-mismatch]` |
| `agy-session-workspace-mismatch-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[session-level-workspace-mismatch]` |

**Existing specs to re-anchor**: `agy_tdd_gate` (`fr4-no-path-key-deny-dropped` and the anchors on these refusals), each still matching once.

**Acceptance Criteria**:
- [ ] AC-36.1: The 9 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 6, 23.

---

## Task 37: agy per-target branches (S7)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `Scan.write`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[target-in-named-checkout-directory]`
**WIRE 2**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `Scan.write`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[target-in-named-checkout-outside-root]`
**WIRE 3**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `Scan.write`
**WIRE-PIN 3**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[target-in-named-checkout-allowance-file]`

**Description**: Row 11 (S7, as row 5): the agy branches that ask the session's status for a resolvable target read `scan.write(target)`: an existing directory (`T2a`, wire 1), outside the root (`T3`/`T4`, wire 2) and the allowance file (`T5`, wire 3). Ids: `<PER_TARGET_IDS>-directory`, `<PER_TARGET_IDS>-outside-root` and `<PER_TARGET_IDS>-allowance-file`, with Task 34's meanings.

**Code structure**:
```python
def main() -> int: ...
```

**Tests** (informational):
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[<PER_TARGET_IDS>-directory|<PER_TARGET_IDS>-outside-root|<PER_TARGET_IDS>-allowance-file]` (12)
- `tests/test_h_mad_phase5_scope.py::test_production_into_second_checkout[agy]` (1), spec AC-3.4; a guard, observed failing under `agy-write-outside-root-session-only`.

Total 13 test ids. **Stated counts** (whole files, informational): 13 new ids (the guard as named), and 753 prior nodes passing (214 of the wires file, 539 of `test_h_mad_phase5_scope.py`); GREEN 766 passing.

**Mutation rows** (`phase5_scope_wires.json`, 15; five per branch):

| Name | Change | Killed by |
|---|---|---|
| `agy-write-directory-session-only` | `scan.session()` in place of `scan.write(target)` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[target-in-named-checkout-directory]` |
| `agy-write-directory-active` | `ACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[other-checkout-directory]` |
| `agy-write-directory-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[other-checkout-directory]` |
| `agy-write-directory-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[excluded-tree-directory]` |
| `agy-write-directory-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[target-in-named-checkout-directory]` |
| `agy-write-outside-root-session-only` | `scan.session()` in place of `scan.write(target)` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[target-in-named-checkout-outside-root]` |
| `agy-write-outside-root-active` | `ACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[other-checkout-outside-root]` |
| `agy-write-outside-root-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[other-checkout-outside-root]` |
| `agy-write-outside-root-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[excluded-tree-outside-root]` |
| `agy-write-outside-root-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[target-in-named-checkout-outside-root]` |
| `agy-write-allowance-file-session-only` | `scan.session()` in place of `scan.write(target)` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[target-in-named-checkout-allowance-file]` |
| `agy-write-allowance-file-active` | `ACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[other-checkout-allowance-file]` |
| `agy-write-allowance-file-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[other-checkout-allowance-file]` |
| `agy-write-allowance-file-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[excluded-tree-allowance-file]` |
| `agy-write-allowance-file-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[target-in-named-checkout-allowance-file]` |

**Existing specs to re-anchor**: `agy_tdd_gate` (anchors on `T2a` to `T5`).

**Acceptance Criteria**:
- [ ] AC-37.1: A production write from the first checkout into the second, when the record names the second, is refused on agy.
- [ ] AC-37.2: The 15 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 36.

---

## Task 38: agy arming files re-routed (S7)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`, `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_tdd_judge_scope.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `Scan.write`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[other-checkout]`

**Description**: Row 12 (S7, scope, files): as Task 35 on agy, with Task 23's `[unfiltered-discovery]` file id replaced by `[excluded-tree]` and Task 23's row `agy-arming-judged-filtered` removed. This is `unscoped_judge`'s last caller, so it goes in this commit (design §5): the function, its `SCOPE_FUNCTIONS` id, and Task 20's tests and rows of it (`test_unscoped_judge`, 7 ids; `test_unscoped_judge_uses_walked`, 1; `test_unscoped_judge_session_half_is_the_walk`, 6; `test_path_parameters_accept_str_and_path[unscoped_judge]`, 1; rows `unscoped-walk-ignored`, `unscoped-chain-ignored`, `unscoped-unknown-ignored`, `unscoped-walks-twice`). Task 20's `walk-root-not-normalised` stays here, its function staying; Task 47 removes it with the walk. The reason `unscoped` goes with it.

**Code structure**:
```python
def main() -> int: ...  # arming_target's judged = scan.write
# h_mad_target_identity.py: unscoped_judge removed
```

**Tests** (informational): 5 ids added; 1 id of Task 23 and 16 ids of Task 20 removed.
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[other-checkout|excluded-tree]` (2)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_agrees_with_hooks[agy-write]` (1)
- `tests/test_h_mad_phase5_scope.py::test_shared_state_file[<SHARED_FILE_KEEPS>-agy]` (2), as Task 30 on agy.
- Removed: `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[unfiltered-discovery]`; `tests/test_h_mad_phase5_scope.py::test_unscoped_judge` (7 ids), `::test_unscoped_judge_uses_walked` (1), `::test_unscoped_judge_session_half_is_the_walk` (6), `::test_path_parameters_accept_str_and_path[unscoped_judge]` (1); `tests/test_h_mad_shared_gate_policy.py::test_each_scope_function_has_one_definition_in_the_identity_module[unscoped_judge]` (1).

**Stated counts** (whole files, informational): 5 new ids, and 849 prior nodes passing (226 of the wires file, 40 of the judge-scope file, 540 of `test_h_mad_phase5_scope.py` and 60 of the shared-policy file, less the 17 removed ids); GREEN 854 passing.

**Differential**: `CHANGES_IN_FORCE[("agy-write", "arming")]` gains every class `("agy-write", "other")` holds (convention 12's re-routing rule).

**Mutation rows** (3 added to `phase5_scope_wires.json`; 1 removed from it and 4 from `phase5_scope.json`):

| Name | Change | Killed by |
|---|---|---|
| `agy-arming-judged-every-record` | `judged` gives the status of A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[other-checkout]` |
| `agy-arming-judged-every-file` | `judged` gives the status of F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[excluded-tree]` |
| `agy-arming-judged-inactive` | `judged` is `lambda name: INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_file_wire[session-root-as-named]` |

Removed: `agy-arming-judged-filtered` (Task 23); `unscoped-walk-ignored`, `unscoped-chain-ignored`, `unscoped-unknown-ignored`, `unscoped-walks-twice` (Task 20).

**Existing specs to re-anchor**: as Task 23.

**Acceptance Criteria**:
- [ ] AC-38.1: `unscoped_judge` has no definition and no caller in `h-mad/scripts` or `h-mad/hooks`.
- [ ] AC-38.2: The 3 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 30, 35, 37.

---

## Task 39: codex shell (S8)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_tdd_judge_scope.py`, `h-mad/tests/test_h_mad_phase5_scope_differential.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `Scan.shell`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[other-checkout]`

**Description**: Row 1 (S8, scope): the codex command branch reads `shell = scan.shell(None, every_stage)`; Task 40 passes the command directory and Task 48 the stage predicate. The present refusal on `unknown` stays first, and on `active` the command is judged as now. Ids: `[other-checkout]` (a refused-list command admitted when the only live record names another checkout), `[excluded-tree]` (rule 3), `[refused-top-level]` (refused when the record names another checkout, without a stage and at `"implementing"`; its control admitted; `CODEX_PROJECT_DIR` set). The codex shell's acceptance cases land here.

**Code structure**:
```python
def _main_guarded() -> int: ...  # the command branch reads scan.shell(...)
```

**Tests** (informational; `test_same_checkout_feature[codex-shell]` is a guard observed failing under `codex-shell-inactive`, and `test_scope_allow_is_silent[codex-shell]` a guard observed failing under `codex-shell-allow-not-silent`; until S9 the shell gates at every stage, so the corpus of `test_scope_agrees_with_hooks[codex-shell]` holds no record at `"planning"`, the `scope` verb's `shell` part reading the stage since Task 28; Task 48's `[codex-shell-stage]` holds those records):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[other-checkout|excluded-tree|refused-top-level]` (3)
- `tests/test_h_mad_phase5_scope.py::test_fr4_case[<FR4_CASES>-codex-shell]` (16)
- `tests/test_h_mad_phase5_scope.py::test_fr4_more[<FR4_MORE>-codex-shell]` (12)
- `tests/test_h_mad_phase5_scope.py::test_discovery_rule[<DISCOVERY_CASES>-codex-shell]` (16)
- `tests/test_h_mad_phase5_scope.py::test_two_checkouts[codex-shell]`, `::test_other_feature_other_checkout[codex-shell]`, `::test_same_checkout_feature[codex-shell]` (3)
- `tests/test_h_mad_phase5_scope.py::test_session_unknown[<SESSION_UNKNOWN_CASES>-codex-explicit]` (6)
- `tests/test_h_mad_phase5_scope.py::test_unreadable_beside[applies-codex-shell|other-checkout-codex-shell]` (2)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_agrees_with_hooks[codex-shell]` (1)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_allow_is_silent[codex-shell]` (1)
- `tests/test_h_mad_phase5_scope_differential.py::test_class_has_difference[D2|D4]` (2)

Total 62 test ids. **Stated counts** (whole files, informational): 62 new ids (2 guards, as above), and 899 prior nodes passing (227 of the wires file, 527 of `test_h_mad_phase5_scope.py`, 41 of the judge-scope file, 104 of the differential file); GREEN 961 passing.

**Differential**: `CHANGES_IN_FORCE[("codex-shell", "other")]` gains D1, D2, D3 and D4; `("codex-shell", "arming")` does not until Task 42, the FR-5 guard still reading the old walk.

**Mutation rows** (`phase5_scope_wires.json`, 4):

| Name | Change | Killed by |
|---|---|---|
| `codex-shell-every-record` | A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[other-checkout]` |
| `codex-shell-every-file` | F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[excluded-tree]` |
| `codex-shell-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[refused-top-level]` |
| `codex-shell-allow-not-silent` | the codex command branch prints `{}` on an allow | `tests/test_h_mad_tdd_judge_scope.py::test_scope_allow_is_silent[codex-shell]` |

**Existing specs to re-anchor**: `codex_gate_judge_wiring` (`F2-WIRE`, `F2-UNION` and the shell branch's anchors), `codex_gate_shell_allowance` (`allowance-never-consulted`).

**Acceptance Criteria**:
- [ ] AC-39.1: A codex session whose only live record names another checkout runs a command the Phase-5 list refuses; each case of spec FR-4 still gates it.
- [ ] AC-39.2: The 4 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 22, 33.

---

## Task 40: codex command directory (rule 5) (S8)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `command_directory`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[workdir-inside-named]`

**Description**: Row 2 (S8, protection), design §5: the shell status's directory is `command_directory(payload.get("tool_input"), "workdir", lambda: _command_cwd(payload), absent)`, with `absent` the string of the root when the payload's `cwd` is missing, null or `""`, and that `cwd` as it is otherwise. `_safe_shell_command` keeps `_command_cwd(payload)`; `_command_cwd` is not edited, so `F2-WORKDIR` and `F2-MALFORMED` need no re-anchoring. The ids are plan row 2's: `[workdir-inside-named]`; `[workdir-unknown-<WORKDIR_UNKNOWN_CASES>]` (its `timeout` case the one with a git shim, delaying the call whose `-C` names the directory; its `separate-volume` case a mounted image, a named skip where unavailable); `[workdir-no-work-tree]`; `[workdir-git-directory]`; `[workdir-absent-session-checkout-cwd]`, `[workdir-absent-no-payload-cwd]`, `[workdir-absent-null-payload-cwd]`, `[workdir-absent-empty-payload-cwd]`; `[workdir-absent-cwd-in-named]`; `[workdir-absent-cwd-unusable-number]`, `[workdir-absent-cwd-unusable-list]`, `[workdir-absent-cwd-unusable-relative]`, `[workdir-absent-cwd-unusable-nonexistent]`, `[workdir-absent-cwd-unusable-file]`, `[workdir-absent-cwd-unusable-bare]`; `[safe-list-directory]`.

**Code structure**:
```python
def _main_guarded() -> int: ...  # scan.shell(command_directory(...), every_stage)
```

**Tests** (informational; `[safe-list-directory]` is a guard, observed failing under `codex-safe-list-gets-rule5-directory`):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[workdir-inside-named|workdir-unknown-<WORKDIR_UNKNOWN_CASES>|workdir-no-work-tree|workdir-git-directory|workdir-absent-session-checkout-cwd|workdir-absent-no-payload-cwd|workdir-absent-null-payload-cwd|workdir-absent-empty-payload-cwd|workdir-absent-cwd-in-named|workdir-absent-cwd-unusable-number|workdir-absent-cwd-unusable-list|workdir-absent-cwd-unusable-relative|workdir-absent-cwd-unusable-nonexistent|workdir-absent-cwd-unusable-file|workdir-absent-cwd-unusable-bare|safe-list-directory]` (27)

**Stated counts** (whole files, informational): 27 new ids (the guard as named), and 230 prior nodes passing (the wires file); GREEN 257 passing.

**Mutation rows** (`phase5_scope_wires.json`, 6):

| Name | Change | Killed by |
|---|---|---|
| `codex-workdir-not-passed` | the directory is `None` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[workdir-inside-named]` |
| `codex-rule5-gets-command-cwd` | rule 5 is given `_command_cwd(payload)` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[workdir-unknown-null]` |
| `codex-safe-list-gets-rule5-directory` | `_safe_shell_command` is given rule 5's value | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[safe-list-directory]` |
| `codex-absent-root-for-unusable-cwd` | `absent` is the root also for an unusable payload `cwd` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[workdir-absent-cwd-unusable-number]` |
| `codex-workdir-always-unknown` | the directory is `MALFORMED_WORKDIR` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[workdir-absent-session-checkout-cwd]` |
| `codex-absent-unknown-for-null-cwd` | `absent` is `MALFORMED_WORKDIR` for a null or empty payload `cwd` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[workdir-absent-null-payload-cwd]` |

**Existing specs to re-anchor**: as Task 39.

**Acceptance Criteria**:
- [ ] AC-40.1: A `workdir` inside the named checkout, from a session elsewhere, is refused; one in a checkout no record names, and an absent key that selects the session's root, are admitted.
- [ ] AC-40.2: The 6 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 39.

---

## Task 41: codex unreadable-root branch (S8)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `phase5_scan`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_unreadable_root_wire[governed]`

**Description**: Row 8 (S8, protection), design §8: the unreadable-root branch reads `phase5_scan(root.component).session()` and refuses on `active` or `unknown`; the session checkout is unknown there, so every live record applies, and the branch makes no stage call in any step. The `M:CX-ROOT-ENTER` refusal before it is unchanged. Ids: `[governed]` (the root a top level), `[below-top-level]`, `[planning]` (at a top level and below one, the record at `"planning"`), `[inactive]`; each with its readable twin (plan rule 4).

**Code structure**:
```python
def _main_guarded() -> int: ...  # the unreadable-root branch reads phase5_scan(root.component).session()
```

**Tests** (informational):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_unreadable_root_wire[governed|below-top-level|planning|inactive]` (4)

**Stated counts** (whole files, informational): 4 new ids, and 257 prior nodes passing (the wires file); GREEN 261 passing.

**Mutation rows** (`phase5_scope_wires.json`, 2):

| Name | Change | Killed by |
|---|---|---|
| `codex-unreadable-root-inactive` | `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_unreadable_root_wire[governed]` |
| `codex-unreadable-root-active` | `ACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_unreadable_root_wire[inactive]` |

**Existing specs to re-anchor**: `codex_gate_judge_wiring` (`CX-ROOT-ENTER` and the branch's anchors).

**Acceptance Criteria**:
- [ ] AC-41.1: The 2 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 39.

---

## Task 42: codex arming fields under the shell's applicability (S8)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`, `h-mad/scripts/h_mad_target_identity.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `Scan.shell`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[other-checkout-safe]`

**Description**: Row 7 (S8, scope): the FR-5 guard reads the `shell` status Task 39 computes (with Task 40's directory), in place of today's walk, and `arming_refusal` names, for a mention, the record FR-8 (a) names (the first applying one of the status) with its reason by `describe`: the guard passes that entry, `applied=shell.applied[0]`, to the `arming_refusal` of Task 9, whose signature does not change, so the reason is the one `applicable` gave for this call's command directory, which can differ for the same record from one directory to another; the exit route gains its fourth actor, a codex or agy session whose checkout the record does not name. The guard and the command branch read one computed status, so this row's mutants change the guard's read of it, and row 1's change the call (the shape OD-3 names for agy). Ids: `[other-checkout-safe]`, `[other-checkout-allowed]`, `[other-checkout-run-wrapped]`, `[other-checkout-mention]`, one per way, an arming write not refused when the only live record names another checkout; `[excluded-tree]` replaces Task 22's `[unfiltered-discovery]`, and Task 22's row `codex-arming-guard-filtered` is removed. The opposite: Task 22's ids, whose record names this checkout.

**Code structure**:
```python
def _main_guarded() -> int: ...       # the FR-5 guard reads shell
def arming_refusal(hit: ArmingWrite, record: LiveRecord | None, *, applied: Applied | None = None) -> str: ...  # signature of Task 9, unchanged; gains the fourth exit actor
```

**Tests** (informational): 7 ids added, 1 removed.
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[other-checkout-safe|other-checkout-allowed|other-checkout-run-wrapped|other-checkout-mention|excluded-tree]` (5)
- `tests/test_h_mad_phase5_scope.py::test_ungated_session_write_unaffected[codex]` (1), spec AC-5.5.
- `tests/test_h_mad_phase5_scope.py::test_arming_refusal_reason_follows_directory[codex]` (1): one live record naming checkout C, after an earlier one in discovery order that names checkout D and does not apply; a mention refused once from a session in C (reason `checkout-match`) and once from a session elsewhere with `workdir` inside C (reason `directory-match`); each refusal names C's record and its own reason, never D's record (Task 6's filtered, ordered `applied`).
- Removed: `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[unfiltered-discovery]`.

**Stated counts** (whole files, informational): 7 new ids, and 842 prior nodes passing (261 of the wires file less the removed id, so 260, and 582 of `test_h_mad_phase5_scope.py`); GREEN 849 passing.

**Differential**: `CHANGES_IN_FORCE[("codex-shell", "arming")]` gains every class `("codex-shell", "other")` holds (convention 12's re-routing rule).

**Mutation rows** (`phase5_scope_wires.json`, 4 added, 1 removed):

| Name | Change | Killed by |
|---|---|---|
| `codex-arming-guard-every-record` | the guard reads A | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[other-checkout-safe]` |
| `codex-arming-guard-every-file` | the guard reads F | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[excluded-tree]` |
| `codex-arming-guard-inactive` | the guard reads `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[safe]` |
| `codex-arming-refusal-reason-dropped` | the guard passes no `applied` to `arming_refusal` | `tests/test_h_mad_phase5_scope.py::test_arming_refusal_reason_follows_directory[codex]` |

Removed: `codex-arming-guard-filtered` (Task 22).

**Existing specs to re-anchor**: as Task 39.

**Acceptance Criteria**:
- [ ] AC-42.1: Every codex refusal caused by FR-5 names the exit route with its four actors.
- [ ] AC-42.2: The 4 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 40.

---

## Task 43: agy `run_command` (S8)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_tdd_judge_scope.py`, `h-mad/tests/test_h_mad_phase5_scope_differential.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `Scan.shell`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[other-checkout]`
**WIRE 2**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `command_directory`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[workdir-inside-named]`

**Description**: Row 9 (S8, kinds of rows 1 and 2), design §8: agy computes `shell = scan.shell(command_directory(args, "Cwd", decode, str(root)), every_stage)` once, before the workspace check, `decode` being a function of no argument that is agy's present decoding of that call's `Cwd`. `run_command` with a command, `run_command` with no string command (which makes no FR-5 check), and the workspace mismatch on `run_command` all read it; the directory given to `_safe_shell_command` stays agy's own variable. Ids: those of rows 1 and 2 with `Cwd`, without `[refused-top-level]`, `[workdir-absent-cwd-in-named]`, the six `workdir-absent-cwd-unusable-` ids and the payload-`cwd` cases of the `workdir-absent-` ids, an absent `Cwd` being the root: `[other-checkout]`, `[excluded-tree]`, `[workdir-inside-named]`, `[workdir-unknown-<WORKDIR_UNKNOWN_CASES>]`, `[workdir-no-work-tree]`, `[workdir-git-directory]`, `[workdir-absent]`, `[safe-list-directory]`; and `[no-command]`, `[workspace-mismatch-other-checkout]`, `[workspace-mismatch-marked]`, `[workspace-mismatch-cwd-inside-named]`. The timeout case uses Task 40's shim, for the git calls after the root lookup. The agy shell's acceptance cases land here.

OPEN-DECISION: OD-3, row 9 asks for three independently mutable connections, while design §8 computes one shell status before the branch — resolve in 5d. Named implementation: the one computation is pinned once, by this task's call rows (`agy-shell-every-record`, `-every-file`, `-inactive` and the four directory rows), and each branch's read of it is mutated alone, by replacing the branch's `shell` with A or with `INACTIVE` at that read only (the six `agy-shell-read-*` rows), each caught by that branch's ids. Task 50 does the same for the stage.

**Code structure**:
```python
def main() -> int: ...  # one shell status, read by the command, no-command and mismatch branches
```

**Tests** (informational; guards: the 15 `test_owner_fields_change_nothing` ids, each holding a record that applies to the session and gates it, with its own field at the value its row reads, and each observed by convention 9's observation procedure under the Task 6 row of its own field, `applicable-owner-decides` for the 5 `owner_session_id` ids (a null `owner_session_id`), `applicable-heartbeat-decides` for the 5 `owner_heartbeat_ts` ids (a null `owner_heartbeat_ts`) and `applicable-feature-key-decides` for the 5 `feature-key` ids (a key differing from `feature`), `test_same_checkout_feature[agy-shell]`, under `agy-shell-inactive`, and `test_scope_allow_is_silent[agy-shell]`, under `agy-shell-allow-not-silent`; until S9 both shells gate at every stage, so no corpus of this task's agreement tests holds a record at `"planning"`):
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[other-checkout|excluded-tree|workdir-inside-named|workdir-unknown-<WORKDIR_UNKNOWN_CASES>|workdir-no-work-tree|workdir-git-directory|workdir-absent|safe-list-directory|no-command|workspace-mismatch-other-checkout|workspace-mismatch-marked|workspace-mismatch-cwd-inside-named]` (23)
- `tests/test_h_mad_phase5_scope.py::test_fr4_case[<FR4_CASES>-agy-shell]` (16)
- `tests/test_h_mad_phase5_scope.py::test_fr4_more[<FR4_MORE>-agy-shell]` (12)
- `tests/test_h_mad_phase5_scope.py::test_discovery_rule[<DISCOVERY_CASES>-agy-shell]` (16)
- `tests/test_h_mad_phase5_scope.py::test_two_checkouts[agy-shell]`, `::test_other_feature_other_checkout[agy-shell]`, `::test_same_checkout_feature[agy-shell]` (3)
- `tests/test_h_mad_phase5_scope.py::test_unreadable_beside[applies-agy-shell|other-checkout-agy-shell]` (2)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_agrees_with_hooks[agy-shell]` (1)
- `tests/test_h_mad_tdd_judge_scope.py::test_unreadable_agrees_with_hooks[session|directory]` (2): on the real codex and agy shells, for each of no line, `applies=no` only, `shell=yes` and a file whose top level is not an object, three commands (one the safe list admits, one an allow line admits, one neither admits), as plan §"Convention Prerequisites" AC-8.1 says. The fourth case of spec AC-8.1, `applies=yes shell=no` only, is made by a record at `"planning"`, which the shells exempt only from S9, so it lands in Task 50 as `[session-planning]` and `[directory-planning]`; in S8 the same record gates both shells ahead of the unreadable file.
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_allow_is_silent[agy-shell]` (1)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_lstat_undecided[session-<INTERPRETERS>|directory-<INTERPRETERS>]` (12): the session and `--directory` forms agree with both shells (OD-9's fixture, Task 28).
- `tests/test_h_mad_phase5_scope.py::test_surfaces_agree_on_applying_records` (1), spec AC-3.6.
- `tests/test_h_mad_phase5_scope.py::test_owner_fields_change_nothing[<OWNER_FIELDS>-<SURFACES>]` (15), spec AC-3.7.
- `tests/test_h_mad_phase5_scope_differential.py::test_incident_replay[<INCIDENT_SHAPES>]` (7), spec AC-10.2: `linked-worktree` is replayed twice in the same two checkouts on the five surfaces (as captured, the decisions of `7a3cca48` in both; with the main checkout added, the second not gated and the first still gated); each `evidence-` id gives the decision the spec states for its row; all from sanitised copies with neutral keys and paths.

Total 111 test ids. **Stated counts** (whole files, informational): 111 new ids (17 guards, as above), and 998 prior nodes passing (265 of the wires file, 584 of `test_h_mad_phase5_scope.py`, 43 of the judge-scope file, 106 of the differential file); GREEN 1109 passing.

**Differential**: `CHANGES_IN_FORCE[("agy-shell", "other")]` gains D1, D2, D3 and D4; `("agy-shell", "arming")` does not until Task 44.

**Mutation rows** (`phase5_scope_wires.json`, 14):

| Name | Change | Killed by |
|---|---|---|
| `agy-shell-every-record` | A at the call | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[other-checkout]` |
| `agy-shell-every-file` | F at the call | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[excluded-tree]` |
| `agy-shell-inactive` | `INACTIVE` at the call | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[no-command]` |
| `agy-workdir-not-passed` | the directory is `None` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[workdir-inside-named]` |
| `agy-rule5-gets-safe-list-directory` | rule 5 is given the safe list's directory | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[workdir-unknown-null]` |
| `agy-safe-list-gets-rule5-directory` | `_safe_shell_command` is given rule 5's value | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[safe-list-directory]` |
| `agy-workdir-always-unknown` | the directory is `MALFORMED_WORKDIR` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[workdir-absent]` |
| `agy-shell-read-command-every-record` | the command branch reads A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[other-checkout]` |
| `agy-shell-read-command-inactive` | the command branch reads `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[workdir-inside-named]` |
| `agy-shell-read-no-command-every-record` | the no-command branch reads A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[no-command]` |
| `agy-shell-read-no-command-inactive` | the no-command branch reads `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[no-command]` |
| `agy-shell-read-mismatch-every-record` | the mismatch reads A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[workspace-mismatch-other-checkout]` |
| `agy-shell-read-mismatch-inactive` | the mismatch reads `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[workspace-mismatch-marked]` |
| `agy-shell-allow-not-silent` | agy's allow object on `run_command` gains a `reason` key | `tests/test_h_mad_tdd_judge_scope.py::test_scope_allow_is_silent[agy-shell]` |

**Existing specs to re-anchor**: `agy_tdd_gate` (`fr4-step5-s-dropped`, `fr4-t3-after-t5`, `fr4-class-c-command-s-dropped`, `fr4-class-c-bad-cwd-judge-error`, `fr4-kind-shell-not-admitted`), `agy_gate_listing`, `listing_connections`, `hook_live_interpreter`.

**Acceptance Criteria**:
- [ ] AC-43.1: An agy `Cwd` inside the named checkout, from a session elsewhere, is refused; every case rule 5 lists makes every live record apply; a `Cwd` in no work tree is judged on rules 1 to 3.
- [ ] AC-43.2: The codex gate, the agy gate, the judge verbs and the Claude hook agree on which records apply over one corpus.
- [ ] AC-43.3: The 14 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 23, 36, 39.

---

## Task 44: agy arming fields under the shell's applicability (S8)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `Scan.shell`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[other-checkout-safe]`

**Description**: Row 12 (S8, scope, fields): as Task 42 on agy. The FR-5 guard reads Task 43's `shell` and passes `applied=shell.applied[0]` to `arming_refusal`, so a refusal names the reason `applicable` gave for this call's `Cwd`; Task 23's `[unfiltered-discovery]` field id is replaced by `[excluded-tree]` and its row `agy-arming-guard-filtered` removed.

**Code structure**:
```python
def main() -> int: ...  # the FR-5 guard reads shell
```

**Tests** (informational): 7 ids added, 1 removed.
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[other-checkout-safe|other-checkout-allowed|other-checkout-run-wrapped|other-checkout-mention|excluded-tree]` (5)
- `tests/test_h_mad_phase5_scope.py::test_ungated_session_write_unaffected[agy]` (1)
- `tests/test_h_mad_phase5_scope.py::test_arming_refusal_reason_follows_directory[agy]` (1), Task 42's test on agy, the directory being `Cwd`.
- Removed: `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[unfiltered-discovery]`.

**Stated counts** (whole files, informational): 7 new ids, and 936 prior nodes passing (288 of the wires file less the removed id, so 287, and 649 of `test_h_mad_phase5_scope.py`); GREEN 943 passing.

**Differential**: `CHANGES_IN_FORCE[("agy-shell", "arming")]` gains every class `("agy-shell", "other")` holds (convention 12's re-routing rule).

**Mutation rows** (`phase5_scope_wires.json`, 4 added, 1 removed):

| Name | Change | Killed by |
|---|---|---|
| `agy-arming-guard-every-record` | the guard reads A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[other-checkout-safe]` |
| `agy-arming-guard-every-file` | the guard reads F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[excluded-tree]` |
| `agy-arming-guard-inactive` | the guard reads `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[safe]` |
| `agy-arming-refusal-reason-dropped` | the guard passes no `applied` to `arming_refusal` | `tests/test_h_mad_phase5_scope.py::test_arming_refusal_reason_follows_directory[agy]` |

Removed: `agy-arming-guard-filtered` (Task 23).

**Existing specs to re-anchor**: as Task 43.

**Acceptance Criteria**:
- [ ] AC-44.1: Every agy refusal caused by FR-5 names the exit route with its four actors and ends with ` kind=arming-input`.
- [ ] AC-44.2: The 4 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 42, 43.

---

## Task 45: agy tools outside the admitted classes (S8)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `Scan.session`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_class_d_wire[other-checkout]`

**Description**: Row 13 (S8, scope): class d, and the workspace mismatch on a class-d tool, read `scan.session()` (stage not consulted). Ids: `[other-checkout]` and `[workspace-mismatch-other-checkout]`, each admitted when the only live record names another checkout and refused when it names this one, without a stage and at `"planning"` (spec AC-9.7, both windows); `[excluded-tree]` (rule 3). The two reads are of one status; as on Task 43, each is mutated alone.

**Code structure**:
```python
def main() -> int: ...  # class d and its mismatch read scan.session()
```

**Tests** (informational):
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_class_d_wire[other-checkout|workspace-mismatch-other-checkout|excluded-tree]` (3)

**Stated counts** (whole files, informational): 3 new ids, and 292 prior nodes passing (the wires file); GREEN 295 passing.

**Mutation rows** (`phase5_scope_wires.json`, 5):

| Name | Change | Killed by |
|---|---|---|
| `agy-class-d-every-record` | class d reads A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_class_d_wire[other-checkout]` |
| `agy-class-d-every-file` | class d reads F | `tests/test_h_mad_phase5_scope_wires.py::test_agy_class_d_wire[excluded-tree]` |
| `agy-class-d-inactive` | class d reads `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_class_d_wire[other-checkout]` |
| `agy-class-d-mismatch-every-record` | the class-d mismatch reads A | `tests/test_h_mad_phase5_scope_wires.py::test_agy_class_d_wire[workspace-mismatch-other-checkout]` |
| `agy-class-d-mismatch-inactive` | the class-d mismatch reads `INACTIVE` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_class_d_wire[workspace-mismatch-other-checkout]` |

Each `-inactive` row is caught by the refused half of its id, each `-every-record` row by the admitted half.

**Existing specs to re-anchor**: `agy_tdd_gate` (`fr4-class-d-default-allows`).

**Acceptance Criteria**:
- [ ] AC-45.1: agy tools outside the admitted classes are refused while a record applies, at `"planning"` included.
- [ ] AC-45.2: The 5 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 43.

---

## Task 46: Shell refusal text (S8)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`, `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `describe`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_shell_refusal_names_the_record[codex]`
**WIRE 2**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `describe`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_shell_refusal_names_the_record[agy]`

**Description**: Row 26 (S8, value), spec FR-8 (a), design §8 "Refusal text": a shell refusal names the feature, the state file and the reason of the first applying record, by `describe(shell.applied)`; codex appends it, and agy puts it before its ` kind=` token, so every agy refusal still carries exactly one `kind=` and ends with it. `_one_decision` in `test_h_mad_agy_tdd_gate.py` is not edited. Each pin holds two records whose texts differ.

**Code structure**:
```python
def _main_guarded() -> int: ...  # codex shell refusals append describe(shell.applied)
def main() -> int: ...           # agy shell refusals carry it before their kind= token
```

**Tests** (informational):
- `tests/test_h_mad_phase5_scope_wires.py::test_shell_refusal_names_the_record[codex|agy]` (2)
- `tests/test_h_mad_phase5_scope.py::test_agy_one_decision_on_shell_refusals` (1): `_one_decision` over every agy shell refusal with a feature key and paths that hold `kind=` and a newline.

**Stated counts** (whole files, informational): 3 new ids, and 946 prior nodes passing (295 of the wires file, 651 of `test_h_mad_phase5_scope.py`); GREEN 949 passing.

**Mutation rows** (`phase5_scope_wires.json`, 4):

| Name | Change | Killed by |
|---|---|---|
| `codex-refusal-describe-empty` | an empty text | `tests/test_h_mad_phase5_scope_wires.py::test_shell_refusal_names_the_record[codex]` |
| `codex-refusal-describe-fixed` | one fixed record's text | `tests/test_h_mad_phase5_scope_wires.py::test_shell_refusal_names_the_record[codex]` |
| `agy-refusal-describe-empty` | an empty text | `tests/test_h_mad_phase5_scope_wires.py::test_shell_refusal_names_the_record[agy]` |
| `agy-refusal-describe-fixed` | one fixed record's text | `tests/test_h_mad_phase5_scope_wires.py::test_shell_refusal_names_the_record[agy]` |

**Existing specs to re-anchor**: none quotes the refusal texts (plan: the grep for them in `h-mad/tests` finds no line); the shell-branch specs of Tasks 39 and 43 still match once.

**Acceptance Criteria**:
- [ ] AC-46.1: The 4 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 39, 43.

---

## Task 47: One scan per hook call (S8)

**Production file**: `h-mad/scripts/h_mad_target_identity.py`, `h-mad/scripts/h_mad_tdd_judge.py`, `h-mad/hooks/h-mad-codex-tdd-gate.py`, `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_shared_gate_policy.py`
**Task shape**: `new-behaviour`

**Description**: Design §5 and §Implementation Order, S8: `_any_phase5_status(root)` moves to the new scan; its value is `scan.session().value`, `.scan` is that scan and `.records` its live records. It keeps the exceptions it raises today (design §3: "`_any_phase5_status` re-raises what it raises today: a `not-object` top level, or an exception `_state_status` does not catch"): before it reads `scan.session()`, it looks through the scan's reads in discovery order and, at the first read that carries an `exception`, re-raises that `exception`, so the type the codex message names is today's. Task 3's `read_state` sets `exception` in exactly the two cases today's `_state_status` raises in: a top level that is not an object (`not-object`, the `AttributeError`), and a read or parse failure outside the tuple `_state_status` catches (`unreadable`, as the `RecursionError` of 1,000,000 nested arrays); a malformed `orchestrator_state` map, and every failure inside that tuple, carry `None` and read `unknown`, as today. Today the `rglob` walk evaluates every file and raises on such a file wherever it lies, so the hook refuses through its exception path even beside an active record in another file; with the check first, an applying live record cannot win ahead of it, and a file that is merely unreadable still reads `unknown`. The two Python hooks take `scan` from it in place of the `phase5_scan(root)` computed beside it since S5, so one hook call makes one discovery. `_state_status` and the judge's `_active_records` read through `read_state` and `live_records`, so one comparison with `step5` remains, and the `rglob` walk goes, so one walk remains. One decision moves, and only on the codex and agy surfaces: a state file whose top level is not an object, lying where the session's discovery does not read (a git-excluded tree, a `tests` or `fixtures` component, a nested checkout), was raised on by the `rglob` walk before the hook branched, and from this task it is not read, so the call gets the decision the scoped branch gives (convention 12's `excluded-not-object` case). This rests on a reading of the spec and the design, stated here and owed to both texts (see the report of v1.3): spec AC-4.9 opens on "an unreadable, unparsable, non-regular or wrongly shaped discovered file", and its last sentence, "A file whose top level is not an object keeps its present refusal in every case", is read over the files the session's discovery reads, every case of which keeps the refusal; design §3's "`_any_phase5_status` re-raises what it raises today" is read over the scan's reads, which hold no file outside the discovery, so what it re-raises is today's exception for each file it reads. The other reading, that a not-object file anywhere the `rglob` walk would find it keeps the refusal, would keep the walk (or a second, unscoped listing) beside the scan, against AC-47.1 and the pruning tests below; this plan does not take it. Every other decision already goes through the scan (Tasks 25 to 46). Task 3's `Path(...)` entry of `_any_phase5_status` goes with the walk, and with it Task 20's row `walk-root-not-normalised`, whose anchor line this task deletes (`test_path_parameters_accept_str_and_path[_any_phase5_status]` stays, the scan applying `os.fspath`). Task 21's and Task 23's `test_s5_walks_once_each` ids give way to `test_one_scan_per_hook_call`.

**Code structure**:
```python
def _any_phase5_status(root: PathArg) -> SessionStatus: ...  # re-raises the first read carrying an exception; else value = scan.session().value; .scan; .records
def _state_status(state_file: Path) -> str: ...            # over read_state and live_records
```

**Tests and RED split**: 56 fail at RED, and 25 guards and 3 observations pass, named below; 2 ids are removed.
- `tests/test_h_mad_phase5_scope.py::test_one_scan_per_hook_call[codex|agy|claude]` (3): `[codex]` and `[agy]` fail (two traversals per call); `[claude]` is a guard, its one session discovery being the FR-6 call's since Task 30, observed failing under `claude-emit-arming-scans-twice`.
- `tests/test_h_mad_shared_gate_policy.py::test_one_step5_comparison_and_one_walk` (1): fails (two comparisons and the `rglob` walk remain).
- `tests/test_h_mad_shared_gate_policy.py::test_stage_read_once` (1): guard; no comparison of a stored stage outside `stage_gates_shell` in the identity module, the judge, the hooks, the assembler and the writer, the writer's transition rules excepted by name; observed failing under `stage-compared-in-hook`.
- `tests/test_h_mad_phase5_scope.py::test_pruning[every-child-codex|every-child-agy|deep-codex|deep-agy|nothing-found-codex|nothing-found-agy|every-child-live-codex|every-child-live-agy|deep-live-codex|deep-live-agy|nothing-found-live-codex|nothing-found-live-agy|no-work-tree-codex|no-work-tree-claude|no-work-tree-git-missing-codex|no-work-tree-git-missing-claude]` (16), plan §"Tradeoffs to preserve", with one ordered audit log of `os.scandir`, `os.listdir` and `subprocess.Popen`: the 12 `every-child`, `deep` and `nothing-found` ids fail (the `rglob` walk lists below the highest excluded directory); the 4 `no-work-tree` ids are guards (the listing is unrestricted and at most one git process starts), observed failing under `no-work-tree-oracle-restarted`. The audit log counts attempted starts (each `subprocess.Popen` event) apart from launched children (each start that returned a process): at a root in no work tree the oracle's first process is started and ends early (design §2), so the `no-work-tree` ids require at most one attempted start, and the `git-missing` ids also require zero launched children, git being absent from `PATH`.
- `tests/test_h_mad_phase5_scope.py::test_pruning_control[tracked-file-in-sub-project|separate-trees]` (2): `[tracked-file-in-sub-project]` fails; `[separate-trees]` is a guard (the process count does not move), observed failing under `oracle-started-per-listing`.
- `tests/test_h_mad_phase5_scope.py::test_large_tree[<LARGE_TREE_LAYOUTS>-<RECORD_STATES>-<SURFACES>]` (56), spec AC-2.9, without the 4 ids `nogit-none-agy-shell`, `nogit-none-agy-write`, `nogit-live-agy-shell`, `nogit-live-agy-write` (agy's root lookup requires a work tree). The 40 ids on the codex and agy surfaces outside `nogit` fail (the walk opens the excluded copies); the 12 `claude` ids are guards, the Claude hook's one session discovery being the FR-6 scan's since Task 30, observed failing under `pruning-lists-excluded`; the 4 `nogit` ids on `codex-shell` and `codex-write` are guards observed failing, by convention 9's observation procedure, under `no-work-tree-oracle-restarted`.
- `tests/test_h_mad_phase5_scope.py::test_git_leaves_with_hook[codex|agy|claude]` (3): observations (convention 9): git leaves when the hook's process exits and its input closes, which the operating system gives and no change of this feature's files can take away (design §Test Strategy; design §2's residual is a launch that is not git). Detector control, run once at RED: the same test with git replaced by a PATH shim that ignores its closed input and sleeps, which the test must report as a process left behind.
- `tests/test_h_mad_phase5_scope.py::test_legacy_exception_beside_active[codex|agy]` (2): a state file whose top level is not an object beside a live record that applies, in another file, refused through each shell's exception path, as on the hooks of `7a3cca48` (spec AC-4.9's last sentence), each host's refusal asserted by its own text: on `[codex]` the reason beginning `H-MAD Phase 5 gate raised AttributeError:` and ending `kind=judge-error`, which names the type as today's does; on `[agy]`, whose exception path (`except Exception:`, `h-mad/hooks/h-mad-agy-tdd-gate.py:274`) names no type, the reason equal to `Gate could not reach a judgement. kind=judge-error` (line 282), and not the applying record's refusal; in the same id, a state file of 1,000,000 nested JSON arrays beside the same applying record (Task 3's `RecursionError` input, outside the tuple `_state_status` catches), refused through the same exception path, `[codex]` naming `RecursionError` and `[agy]` giving the same fixed reason; and, in the same id, an object whose `orchestrator_state` is a list beside the same applying record, which is not raised on and gets the applying record's refusal; guards (today's walk raises on the first two files and reads the third as `unknown`, `active` winning over `unknown`), observed failing under `session-status-drops-legacy-raise`.
- Removed: `tests/test_h_mad_phase5_scope.py::test_s5_walks_once_each[codex]` (Task 21) and `[agy]` (Task 23).

**Differential**: `LEGACY_RAISE_LIFTED` gains `codex-shell`, `codex-write`, `agy-shell` and `agy-write` (convention 12).

**Stated counts**: RED 56 failing, 737 passing (the 28 guards and observations: `test_one_scan_per_hook_call[claude]`; `test_stage_read_once`; `test_pruning[no-work-tree-codex|no-work-tree-claude|no-work-tree-git-missing-codex|no-work-tree-git-missing-claude]`; `test_pruning_control[separate-trees]`; the 12 `claude` ids and the 4 `nogit` codex ids of `test_large_tree`; `test_git_leaves_with_hook[codex|agy|claude]`; `test_legacy_exception_beside_active[codex|agy]`; and the 709 nodes earlier tasks and `bb88b6cc` leave in the two files, 652 of `test_h_mad_phase5_scope.py` less the 2 removed ids and 59 of the shared-policy file); GREEN 793 passing.

**Mutation rows** (`phase5_scope.json`, 10):

| Name | Change | Killed by |
|---|---|---|
| `session-status-old-walk` | the value comes from the `rglob` walk | `tests/test_h_mad_phase5_scope.py::test_one_scan_per_hook_call[codex]` |
| `codex-scan-computed-twice` | codex computes `phase5_scan(root)` beside the status | `tests/test_h_mad_phase5_scope.py::test_one_scan_per_hook_call[codex]` |
| `agy-scan-computed-twice` | agy computes `phase5_scan(root)` beside the status | `tests/test_h_mad_phase5_scope.py::test_one_scan_per_hook_call[agy]` |
| `second-step5-comparison` | `_active_records` compares `phase` itself | `tests/test_h_mad_shared_gate_policy.py::test_one_step5_comparison_and_one_walk` |
| `stage-compared-in-hook` | the codex hook compares a stored stage | `tests/test_h_mad_shared_gate_policy.py::test_stage_read_once` |
| `pruning-lists-excluded` | the walk lists an excluded directory | `tests/test_h_mad_phase5_scope.py::test_pruning[deep-codex]` |
| `claude-emit-arming-scans-twice` | `emit_arming` computes `phase5_scan(root)` a second time | `tests/test_h_mad_phase5_scope.py::test_one_scan_per_hook_call[claude]` |
| `no-work-tree-oracle-restarted` | at a root in no work tree, after the oracle's first process ends early, a second one is started | `tests/test_h_mad_phase5_scope.py::test_pruning[no-work-tree-codex]` |
| `oracle-started-per-listing` | a new oracle is started for each listed directory | `tests/test_h_mad_phase5_scope.py::test_pruning_control[separate-trees]` |
| `session-status-drops-legacy-raise` | `_any_phase5_status` returns `scan.session().value` without re-raising a read's `exception` | `tests/test_h_mad_phase5_scope.py::test_legacy_exception_beside_active[codex]` |

Removed: `walk-root-not-normalised` (Task 20, from `phase5_scope.json`), its anchor, the walk's `Path(...)` entry, being deleted here.

**Existing specs to re-anchor**: `tdd_judge_chain`, `tdd_gate_fallback_agent` (the `_active_records` anchor), and the codex and agy specs of Tasks 39 and 43.

**Acceptance Criteria**:
- [ ] AC-47.1: `git grep -nE "[\"']step5[\"']" -- h-mad/scripts h-mad/hooks h-mad/bin` gives one comparison beside the schema line, and no `rglob` of the state file's name remains under `h-mad/scripts` and `h-mad/hooks`.
- [ ] AC-47.2: The pruning layouts and spec AC-2.9's counts hold on every surface.
- [ ] AC-47.3: The 10 rows are caught; the full suite passes.
- [ ] AC-47.4: A state file the session's discovery reads whose top level is not an object, or whose read fails outside the tuple `_state_status` catches, is refused through each shell's exception path, beside an applying live record included (`test_legacy_exception_beside_active[codex|agy]`). A not-object file the session's discovery does not read gets, on the codex and agy surfaces from this task, the decision the session's discovery gives (convention 12's `excluded-not-object`, held by `test_crossed_corpus` with `LEGACY_RAISE_LIFTED` as this task's **Differential** sets it).

**Dependencies on other tasks**: Tasks 39 to 46.

---

## Task 48: codex shell stage (S9)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_tdd_judge_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `stage_gates_shell`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[planning]`

**Description**: Row 3 (S9, scope): the `gates` argument of codex's `scan.shell(...)` changes from `every_stage` to `stage_gates_shell` and nothing else (design §Implementation Order); the unreadable-root branch makes no stage call. Ids: `[planning]` (admitted), `[implementing]` and `[planning-beside-implementing]` (refused), every record naming this checkout; `[refused-top-level-planning]` (admitted when the only live record names another checkout and is at `"planning"`). This task also carries S9's control over the branches that must not consult the stage (plan, after row 33): five rows force the stage exemption onto them, each caught by the refused half at `"planning"` of that branch's id.

**Code structure**:
```python
def _main_guarded() -> int: ...  # scan.shell(directory, stage_gates_shell)
```

**Tests** (informational; guards are named):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[planning|implementing|planning-beside-implementing|refused-top-level-planning]` (4); `[implementing]` and `[planning-beside-implementing]` are refused at every stage today, so they are guards, observed failing under `codex-stage-every-exempt`.
- `tests/test_h_mad_phase5_scope.py::test_planning_window[codex-shell|writes]` (2), spec AC-9.1: at `"planning"` in the named checkout the audit dispatch verb is not refused on the codex shell; `[writes]`, a guard, holds a production write without a failing test refused through `apply_patch`, codex `Write` and `Edit`, each admitted agy write tool and the Claude hook; observed failing under `stage-exempt-chain`.
- `tests/test_h_mad_phase5_scope.py::test_after_mark[codex-shell]` (1), spec AC-9.2; guard, observed failing under `codex-stage-every-exempt`.
- `tests/test_h_mad_phase5_scope.py::test_stage_values_gate_shell[absent-codex-shell|null-codex-shell|implementing-codex-shell|unknown-string-codex-shell|non-string-codex-shell]` (5), spec AC-9.3; guards, observed failing under `codex-stage-every-exempt`.
- `tests/test_h_mad_phase5_scope.py::test_second_record_not_planning_gates[codex-shell]` (1), spec AC-9.6; guard, observed failing under `codex-stage-every-exempt`.
- `tests/test_h_mad_phase5_scope.py::test_stage_callers_agree[codex-shell]` (1)
- `tests/test_h_mad_phase5_scope.py::test_unreadable_beside_planning[codex-shell|codex-write|agy-write|claude]` (4), spec AC-4.9 ("a live record ... at stage `planning` never hides an unreadable file"); guards, `[codex-shell]` observed failing under `shell-planning-hides-unreadable` and the write ids under `chain-planning-short-circuits`. Its `[agy-shell]` id lands in Task 50: until then agy passes `every_stage`, so the planning record gates the agy shell and the condition of that mutant (every applying record exempt) is false there, and the mutant cannot reach it.
- `tests/test_h_mad_phase5_scope.py::test_after_drop_undeclared` (1), spec AC-10.6, as plan §"Convention Prerequisites" states it.
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_agrees_with_hooks[codex-shell-stage]` (1)

Total 20 test ids. **Stated counts** (whole files, informational): 20 new ids (14 guards: the 2 shell-wire ids, `[writes]`, the 7 ids of AC-9.2, AC-9.3 and AC-9.6, and the 4 `test_unreadable_beside_planning` ids), and 1088 prior nodes passing (297 of the wires file, 732 of `test_h_mad_phase5_scope.py`, 59 of the judge-scope file); GREEN 1108 passing.

**Mutation rows** (10): `phase5_scope_wires.json` (8), `phase5_scope.json` (2).

| Name | Change | Killed by |
|---|---|---|
| `codex-stage-not-consulted` | `gates` is `lambda record: True` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[planning]` |
| `codex-stage-every-exempt` | `gates` is `lambda record: False` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_shell_wire[implementing]` |
| `stage-exempt-codex-session-level` | row 4's `scan.session()` drops records at `"planning"` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_write_wire[session-level-bad-header]` |
| `stage-exempt-codex-unreadable-root` | row 8's status drops records at `"planning"` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_unreadable_root_wire[planning]` |
| `stage-exempt-agy-session-level` | row 10's `scan.session()` drops records at `"planning"` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_write_wire[session-level-no-path-key]` |
| `stage-exempt-agy-class-d` | row 13's `scan.session()` drops records at `"planning"` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_class_d_wire[other-checkout]` |
| `stage-exempt-claude-state` | the `state` verb's chain drops records at `"planning"` | `tests/test_h_mad_phase5_scope_wires.py::test_claude_hook_wire[no-target]` |
| `stage-exempt-chain` | `chain_from` drops applying records at `"planning"` | `tests/test_h_mad_phase5_scope.py::test_planning_window[writes]` |
| `shell-planning-hides-unreadable` | `Scan.shell` returns `inactive` when every applying record is exempt, before it reads an unreadable file (in `phase5_scope.json`) | `tests/test_h_mad_phase5_scope.py::test_unreadable_beside_planning[codex-shell]` |
| `chain-planning-short-circuits` | a chain whose applying records are all at `"planning"` reads `none` before its unreadable file (in `phase5_scope.json`) | `tests/test_h_mad_phase5_scope.py::test_unreadable_beside_planning[claude]` |

**Existing specs to re-anchor**: as Task 39.

**Acceptance Criteria**:
- [ ] AC-48.1: At `"planning"` in the named checkout the codex shell is not gated by that record; at any other stage, or none, it is; at an unreadable root it is in either window.
- [ ] AC-48.2: The 10 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 16, 28, 47.

---

## Task 49: codex arming fields stage (S9)

**Production file**: `h-mad/hooks/h-mad-codex-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-codex-tdd-gate.py:_main_guarded` → `stage_gates_shell`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[planning-safe]`

**Description**: Row 7 (S9, scope): the FR-5 guard reads the one `shell` status, whose `gates` Task 48 made `stage_gates_shell`, so this task writes no production line; its pins pass at RED and are guards by convention 10, each observed failing under its row. Ids, one per way: `[planning-safe]`, `[planning-allowed]`, `[planning-run-wrapped]`, `[planning-mention]` (an arming write not refused, on mention included, when the only applying record is at `"planning"`); the opposite `[implementing-beside-planning]` (refused), whose planning record comes first in discovery order and whose refusal must name the implementing record, the first entry that applies and gates (Task 6's `applied`). The rows change the guard's read of the status alone, as Task 42's do.

**Code structure**:
```python
# h-mad-codex-tdd-gate.py: no edit; the guard's read of the shell status is pinned and mutated
```

**Tests** (informational; every id is a guard at RED, and the RED is the removal-mutant observation of convention 10):
- `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[planning-safe|planning-allowed|planning-run-wrapped|planning-mention|implementing-beside-planning]` (5)

**Stated counts** (whole files, informational): RED 0 failing, 306 passing (the 5 guards and the 301 prior nodes of the wires file); GREEN 306 passing.

**Mutation rows** (`phase5_scope_wires.json`, 2):

| Name | Change | Killed by |
|---|---|---|
| `codex-arming-guard-stage-not-consulted` | the guard reads `scan.shell(directory, lambda record: True)` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[planning-safe]` |
| `codex-arming-guard-every-stage-exempt` | the guard reads `scan.shell(directory, lambda record: False)` | `tests/test_h_mad_phase5_scope_wires.py::test_codex_arming_write_wire[implementing-beside-planning]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-49.1: Both rows are caught.

**Dependencies on other tasks**: Task 48.

---

## Task 50: agy stage, three places (S9)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`, `h-mad/tests/test_h_mad_phase5_scope.py`, `h-mad/tests/test_h_mad_tdd_judge_scope.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `stage_gates_shell`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[planning]`

**Description**: Row 9 (S9, scope): the `gates` argument of agy's one `scan.shell(...)` becomes `stage_gates_shell`. Ids: `[planning]`, `[implementing]`, `[planning-beside-implementing]` (row 3's, with row 9's exception); `[no-command-planning]` and `[workspace-mismatch-planning]` (not refused), with `[implementing]`, the refused half of `[no-command]` and `[workspace-mismatch-marked]` as their opposites (spec AC-9.8).

OPEN-DECISION: OD-3 (its stage half), as on Task 43 — resolve in 5d. Named implementation: the call's `gates` is mutated once (the first two rows), and each of the three branches' reads is mutated alone, by replacing its `shell` with `scan.shell(directory, lambda record: True)` or `scan.shell(directory, lambda record: False)` at that read only (the six `agy-stage-read-*` rows), each caught by that branch's planning id or its opposite.

**Code structure**:
```python
def main() -> int: ...  # scan.shell(directory, stage_gates_shell)
```

**Tests** (informational; the 7 ids of AC-9.2, AC-9.3 and AC-9.6 and the shell-wire ids `[implementing]` and `[planning-beside-implementing]`, refused at every stage today, are guards, observed failing under `agy-stage-every-exempt`):
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[planning|implementing|planning-beside-implementing|no-command-planning|workspace-mismatch-planning]` (5)
- `tests/test_h_mad_phase5_scope.py::test_planning_window[agy-shell]` (1)
- `tests/test_h_mad_phase5_scope.py::test_after_mark[agy-shell]` (1)
- `tests/test_h_mad_phase5_scope.py::test_stage_values_gate_shell[absent-agy-shell|null-agy-shell|implementing-agy-shell|unknown-string-agy-shell|non-string-agy-shell]` (5)
- `tests/test_h_mad_phase5_scope.py::test_second_record_not_planning_gates[agy-shell]` (1)
- `tests/test_h_mad_phase5_scope.py::test_stage_callers_agree[agy-shell]` (1)
- `tests/test_h_mad_tdd_judge_scope.py::test_scope_agrees_with_hooks[agy-shell-stage]` (1)
- `tests/test_h_mad_tdd_judge_scope.py::test_unreadable_agrees_with_hooks[session-planning|directory-planning]` (2): spec AC-8.1's case `applies=yes shell=no` only, a record at `"planning"` beside an unreadable file, on the real codex and agy shells with Task 43's three commands (one the safe list admits, one an allow line admits, one neither admits). No line says `shell=yes`, so AC-8.1 requires both shells to refuse every one of the three commands, each refusal being the unreadable-state refusal (spec AC-4.9: a planning record never hides an unreadable file); and, asserted separately in the same id, the clean twin, the same fixture with the unreadable file removed, gives each command the decision of a session the planning record does not gate. Both ids fail at RED: agy still passes `every_stage`, so the planning record gates its shell, `Scan.shell` returns `active` before `unknown`, and the safe-list and allow-line commands are admitted; codex, exempt since Task 48, already refuses all three.
- `tests/test_h_mad_phase5_scope.py::test_unreadable_beside_planning[agy-shell]` (1), moved here from Task 48: with the three commands of Task 43, every one is refused beside the planning record and the unreadable file. It fails at RED for the reason above, and after GREEN it is observed failing under `shell-planning-hides-unreadable` by convention 9's observation procedure.

Total 18 test ids. **Stated counts** (whole files, informational): 18 new ids (the 9 guards named above), and 1113 prior nodes passing (306 of the wires file, 747 of `test_h_mad_phase5_scope.py`, 60 of the judge-scope file); GREEN 1131 passing.

**Mutation rows** (`phase5_scope_wires.json`, 8):

| Name | Change | Killed by |
|---|---|---|
| `agy-stage-not-consulted` | `gates` is `lambda record: True` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[planning]` |
| `agy-stage-every-exempt` | `gates` is `lambda record: False` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[implementing]` |
| `agy-stage-read-command-not-consulted` | the command branch reads the stage-blind status | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[planning]` |
| `agy-stage-read-command-every-exempt` | the command branch reads the all-exempt status | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[implementing]` |
| `agy-stage-read-no-command-not-consulted` | the no-command branch reads the stage-blind status | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[no-command-planning]` |
| `agy-stage-read-no-command-every-exempt` | the no-command branch reads the all-exempt status | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[no-command]` |
| `agy-stage-read-mismatch-not-consulted` | the mismatch reads the stage-blind status | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[workspace-mismatch-planning]` |
| `agy-stage-read-mismatch-every-exempt` | the mismatch reads the all-exempt status | `tests/test_h_mad_phase5_scope_wires.py::test_agy_shell_wire[workspace-mismatch-marked]` |

**Existing specs to re-anchor**: as Task 43.

**Acceptance Criteria**:
- [ ] AC-50.1: With an agy workspace mismatch and only a record at `"planning"` applying, `run_command` is not refused, and a write tool and a tool outside the admitted classes are; after the mark `run_command` is refused too.
- [ ] AC-50.2: The 8 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 45, 48.

---

## Task 51: agy arming fields stage (S9)

**Production file**: `h-mad/hooks/h-mad-agy-tdd-gate.py`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_wires.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-agy-tdd-gate.py:main` → `stage_gates_shell`
**WIRE-PIN**: `h-mad/tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[planning-safe]`

**Description**: Row 12 (S9, scope, fields): as Task 49 on agy, `[implementing-beside-planning]` with the same order of records and the same assertion; the FR-5 guard reads Task 50's `shell`, no production line is written, and every pin is a guard at RED.

**Code structure**:
```python
# h-mad-agy-tdd-gate.py: no edit; the guard's read of the shell status is pinned and mutated
```

**Tests** (informational; every id is a guard at RED, and the RED is the removal-mutant observation of convention 10):
- `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[planning-safe|planning-allowed|planning-run-wrapped|planning-mention|implementing-beside-planning]` (5)

**Stated counts** (whole files, informational): RED 0 failing, 316 passing (the 5 guards and the 311 prior nodes of the wires file); GREEN 316 passing.

**Mutation rows** (`phase5_scope_wires.json`, 2):

| Name | Change | Killed by |
|---|---|---|
| `agy-arming-guard-stage-not-consulted` | the guard reads `scan.shell(directory, lambda record: True)` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[planning-safe]` |
| `agy-arming-guard-every-stage-exempt` | the guard reads `scan.shell(directory, lambda record: False)` | `tests/test_h_mad_phase5_scope_wires.py::test_agy_arming_write_wire[implementing-beside-planning]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-51.1: Both rows are caught.

**Dependencies on other tasks**: Task 50.

---

## Task 52: Writer routes and topologies (S9)

**Production file**: none
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_topologies.py`
**Task shape**: `gate`

**Description**: The proofs of spec FR-7's routes and its acceptance criteria (plan §"How the writer routes are proved"), authored once every surface they cross is in place. Every test drives real state-writer commands through the real hooks on scratch checkouts and re-reads the store; none edits production code. Each passes at RED, because the behaviour it holds landed in Tasks 11 to 51, and is observed failing under the mutant named beside it (convention 9), except `test_writer_row[bkit-migration]`, an observation with its detector control. A test that does not pass is a defect of an earlier task and is reported, not fixed here. The older writer with the newer schema (plan §"Risks", two-writer row) is exercised here, beside the routes, because its records are judged by the new hooks under FR-4. Every test drives the hooks and the writer under each supported Python inside the test, with the launch method of §"Shared case lists", and asserts from the launcher's log which interpreter ran each process; pytest stays in the thin venv.

The harness scores each of the 12 rows of `phase5_scope_topologies.json` on its own `test`; the row a topology id is named under has the `find` and `replace` of the row of the same name without the `topology-` prefix where one exists. Every other id is observed, by convention 9's observation procedure, under the row named for it below, after the orchestrator has written the spec, and the orchestrator's report after the `gate` dispatch records each id's failure; those observations are not re-scored at S11. Each id is named under one row, drawn from the route that decides it, and the route is one of six: the FR-5 classifier in a gated session (an admitted id under `topology-codex-arming-write-always-hit` on codex and under `agy-arming-write-always-hit`, Task 23, on agy; a refusal by FR-5 of a command the safe list or an allow line admits under `topology-codex-arming-write-none` or `topology-agy-arming-write-none`); the stage predicate (an id of a session in the named checkout at `"planning"`, under `topology-codex-stage-not-consulted` or `topology-agy-stage-not-consulted`, whose change reaches the FR-5 guard too, the guard reading the one shell status, Task 49); applicability (an admitted id of a session whose record does not apply, under `topology-other-checkout-applies`; a record without the new fields, under `topology-field-absent-exempt`); the allowance (a refusal of a command with no allow line that the safe list does not admit, which stands with FR-5's classifier removed, under `topology-allowance-admits-all`); the writer's rules, for a session no shell gate sees (a row of `state_write_scope.json`); and no gate and no writer, an observation with its detector control. An id is credited when it fails under its one named row, and any half of it failing is enough. A half that FR-5 and the allowance both refuse (the `phase=null` half of the `linked-no-line-*` ids) is shown by neither row alone; its id is credited by another half, and FR-5's refusal of a `phase=null` write is shown on the `own-no-line-*` and `linked-with-line-*` ids, never on that half itself (the residual). An id that its named row does not make fail is reported as a defect of this plan, not credited. The `gate` dispatch creates the test file and nothing else (`h_mad_assemble_tdd.py --phase gate --authors-test` makes no other edit and carries no mutation spec); after it, the orchestrator writes `h-mad/tests/mutation-specs/phase5_scope_topologies.json` (its first row by hand, the others with `--append-row`) and scores it with `python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/phase5_scope_topologies.json`, reading the `MUTATION:` token. There is no 5e GREEN dispatch for this task.

**Tests and RED split** (all pass at RED: 42 guards and 1 observation):
- `tests/test_h_mad_phase5_scope_topologies.py::test_by_route[safe-list|allow-line-linked-store|no-line-linked-store|allow-line-sub-project-store|no-line-sub-project-store|allow-line-path-not-first|no-line-path-not-first|allow-line-implementer-record|no-line-implementer-record|allow-line-archreview-cycle|no-line-archreview-cycle|mention-in-value|ungated]` (13); by the assignment above: the admitted ids of a gated session under `topology-codex-arming-write-always-hit`; the refused `no-line-*` ids, whose commands are refused for want of an allow line even with FR-5's classifier removed, under `topology-allowance-admits-all`; a refusal of an `allow-line-*` id, under `topology-codex-arming-write-none`. `[ungated]` is the exception: in an ungated session the FR-5 guard is not reached, so no mutant of the classifier behind it can change its decision; it is observed failing under `codex-arming-guard-every-record` (Task 42), the guard reading every live record, so the only live record, which names another checkout, gates the session and its arming write is refused.
- `tests/test_h_mad_phase5_scope_topologies.py::test_writer_row[phase0-create-claim|arm-5a|re-arm|mark-5d|halt-5a-to-5c|halt-5d-to-5g-named|success-5g-named|halt-or-success-other-checkout|halt-or-success-claude-grok|halt-other-phases|reset|implementer-verb|non-arming-fields|bkit-migration]` (14), one per row of spec FR-7's table (AC-7.1). Each id's gated session, where it has one, is a codex session, and its row, by the route that decides it (the six routes above), is fixed here; the orchestrator's report after the `gate` dispatch records each id's failure under it:
  - `[success-5g-named]`: the `test` of `topology-exit-route-missing`, scored by the harness.
  - `[non-arming-fields]`: the `test` of `topology-codex-arming-write-always-hit`, scored by the harness.
  - `[phase0-create-claim]`, `[halt-5d-to-5g-named]`, `[halt-other-phases]`, `[implementer-verb]`: the FR-5 classifier; each has an admitted half from a codex session that a live record gates (for `[phase0-create-claim]`, another record; for the others, the record in its named checkout), its write naming no arming field (halt fields without `phase`, a claim, the implementer verb under its allow line), observed under `topology-codex-arming-write-always-hit`, which makes that write an FR-5 hit and refuses it.
  - `[arm-5a]`, `[re-arm]`: the FR-5 classifier; each has a refused half, the arming write from a codex session that another live record gates, by route 1 (the session's own state file, its path the first argument, `--set` as the safe list names it), observed under `topology-codex-arming-write-none`, under which the safe list admits that write.
  - `[mark-5d]`, `[halt-5a-to-5c]`: the stage predicate; each is made from a codex session in the named checkout while the record is at `"planning"`, so the shell is not gated and the write (`phase5_stage`, or `phase` null with the halt fields) is accepted; observed under `topology-codex-stage-not-consulted`, which gates the shell, so FR-5 refuses the write, its arming field being one FR-5 names.
  - `[halt-or-success-other-checkout]`, `[reset]`: applicability; each has an admitted half from a codex session in a checkout the record does not name (for `[reset]`, the ungated session the row requires), observed under `topology-other-checkout-applies`, which gates that session and so refuses the write.
  - `[halt-or-success-claude-grok]`: the writer's rules. No shell gate sees it: the Claude hook's matcher is `("Write", "Edit")` (`h-mad/scripts/h_mad_hook_wiring.py:61`), so the state writer run from that session's shell meets no hook, and grok has no shell gate. The id arms a record with a usable checkout, writes `phase` null with the halt fields from the session's shell, re-reads the store and asserts the record left `step5` with its checkout field null (spec AC-1.6); observed under `disarm-keeps-checkout` (`state_write_scope.json`, Task 11), under which the checkout is kept.
  - `[bkit-migration]`: no gate and no writer, so an observation (convention 9), never a guard: it moves the store away and copies it back as plain file operations, as bkit's SessionStart and the operator do, asserts the restored file byte-identical to the original, and asserts that no hook of this feature is registered on `SessionStart` (`HOOK_EVENTS` of `h-mad/scripts/h_mad_hook_wiring.py` maps only `h-mad-advisor-warn.sh`, to `PostToolUse`, and `DEFAULT_EVENT` is `PreToolUse`; no task of this plan edits that file). Detector control, run once after the `gate` dispatch and recorded in the orchestrator's report: the same test reading a scratch copy of that module whose `HOOK_EVENTS` maps `h-mad-tdd-gate.sh` to `SessionStart`, which the test must report.
- `tests/test_h_mad_phase5_scope_topologies.py::test_halt_only_write[own-no-line-codex|linked-no-line-codex|linked-with-line-codex|own-no-line-agy|linked-no-line-agy|linked-with-line-agy]` (6), spec AC-7.4; each id's `phase=null` half, refused under FR-5, under `topology-codex-arming-write-none` or `topology-agy-arming-write-none`; the `linked-no-line-*` ids, by their halt-only refusal, made for want of an allow line, under `topology-allowance-admits-all`; their `phase=null` half, refused by both, is the residual stated above.
- `tests/test_h_mad_phase5_scope_topologies.py::test_full_run[claude-codex|codex-other-checkout|codex-named-own|codex-named-linked|agy-other-checkout|agy-named-own|agy-named-linked]` (7), spec AC-7.2, with exactly the allow lines it states for state writes and the lines for other commands listed by the fixture; the `named-*` ids observed failing under `topology-codex-stage-not-consulted` or `topology-agy-stage-not-consulted`, by their host, through the 5d mark their gated orchestrator makes at `"planning"`; `[claude-codex]`, in which the codex implementer runs only from 5d at `"implementing"`, where the stage predicate already gates it, under `topology-codex-arming-write-always-hit`, the fixture's codex implementer running at least one shell command in the named checkout while the record gates it, which that row makes an FR-5 hit and refuses; the `codex-other-checkout` and `agy-other-checkout` ids, whose record does not apply, so that no stage predicate can gate them, under `topology-other-checkout-applies`.
- `tests/test_h_mad_phase5_scope_topologies.py::test_exit_ungates_next_command[codex|agy]` (2), spec AC-7.3. The fixture keeps a second live record, naming another checkout, beside the one the exit ends; after the exit by an ungated session, the next command in the formerly gated session is judged as not gated. Removal A falls back to the original expression only when no live record remains, so with the second record still live it gates that next command; each id is therefore observed failing under `codex-shell-every-record` and `agy-shell-every-record`. Without the second record both runs would read `inactive`, and the mutant would be unobservable there.
- `tests/test_h_mad_phase5_scope_topologies.py::test_older_writer_newer_schema` (1): the writer of `7a3cca48` beside this tree's schema file; what it accepts and stores is asserted, and every record it can leave is judged by the five surfaces under FR-4. That writer merges the fields it is given and validates against the schema file beside it, so with this tree's schema it can store a string checkout; the test drives two records: one created without the new fields, which has no checkout field and must apply from every checkout (spec AC-4.1), and one with a usable checkout supplied explicitly (`--set implementation_checkout=<a usable top level>` through that writer), which must gate the session in the checkout it names and admit a session in another checkout; each is judged from a matching and from a nonmatching session. A guard: the field-free half observed failing under `topology-field-absent-exempt`, the checkout-bearing half's nonmatching session under `topology-other-checkout-applies`.

**Stated counts**: RED 0 failing, 43 passing (42 guards and 1 observation, `test_writer_row[bkit-migration]`, as listed; the file is new); GREEN 43 passing. The assembler stages this task with `--authors-test h-mad/tests/test_h_mad_phase5_scope_topologies.py --expect-fail 0 --expect-pass 43`.

**Mutation rows** (`phase5_scope_topologies.json`, 12, authored and scored by the orchestrator after the `gate` dispatch):

| Name | Change | Killed by |
|---|---|---|
| `topology-codex-arming-write-none` | the codex FR-5 call's result is `None` | `tests/test_h_mad_phase5_scope_topologies.py::test_halt_only_write[own-no-line-codex]` |
| `topology-agy-arming-write-none` | the agy FR-5 call's result is `None` | `tests/test_h_mad_phase5_scope_topologies.py::test_halt_only_write[own-no-line-agy]` |
| `topology-codex-stage-not-consulted` | codex's `gates` is `lambda record: True` | `tests/test_h_mad_phase5_scope_topologies.py::test_full_run[codex-named-own]` |
| `topology-exit-route-missing` | `arming_refusal` omits the exit route | `tests/test_h_mad_phase5_scope_topologies.py::test_writer_row[success-5g-named]` |
| `topology-codex-arming-write-always-hit` | every codex command is an FR-5 hit | `tests/test_h_mad_phase5_scope_topologies.py::test_writer_row[non-arming-fields]` |
| `topology-agy-stage-not-consulted` | agy's `gates` is `lambda record: True` | `tests/test_h_mad_phase5_scope_topologies.py::test_full_run[agy-named-own]` |
| `topology-codex-shell-every-record` | removal A at codex's shell call | `tests/test_h_mad_phase5_scope_topologies.py::test_exit_ungates_next_command[codex]` |
| `topology-agy-shell-every-record` | removal A at agy's shell call | `tests/test_h_mad_phase5_scope_topologies.py::test_exit_ungates_next_command[agy]` |
| `topology-codex-arming-guard-every-record` | codex's FR-5 guard reads A | `tests/test_h_mad_phase5_scope_topologies.py::test_by_route[ungated]` |
| `topology-field-absent-exempt` | `applicable` gives `applies=False` for `field-absent` | `tests/test_h_mad_phase5_scope_topologies.py::test_older_writer_newer_schema` |
| `topology-allowance-admits-all` | `_operator_allowed` returns `True` before its lexical test (the line marked `M:SA-LEXICAL`) | `tests/test_h_mad_phase5_scope_topologies.py::test_halt_only_write[linked-no-line-codex]` |
| `topology-other-checkout-applies` | `applicable` gives `applies=True` for `other-checkout` | `tests/test_h_mad_phase5_scope_topologies.py::test_full_run[codex-other-checkout]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-52.1: Each route of spec FR-7 has its test, each AC-7.2 topology completes with exactly the stated allow lines for state writes, and AC-7.4 holds in its three cases on both shell hooks.
- [ ] AC-52.2: The 12 rows are caught; every other guard id fails under the one row it is named under, by convention 9's observation procedure, and `test_writer_row[bkit-migration]`'s detector control is reported, as the orchestrator's report records; the full suite passes.

**Dependencies on other tasks**: Tasks 11, 42, 44, 48 to 51.

---

## Task 53: Landing probe (S10)

**Production file**: `docs/03-analysis/probes/phase5-gate-feature-scope/landing_lanes.py`
**Test file**: `h-mad/tests/test_h_mad_landing_lanes.py`
**Task shape**: `wiring`
**WIRE 1**: `docs/03-analysis/probes/phase5-gate-feature-scope/landing_lanes.py:main` → `walk_state_files`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_landing_lanes.py::test_probe_wire[discovery]`
**WIRE 2**: `docs/03-analysis/probes/phase5-gate-feature-scope/landing_lanes.py:main` → `walk_state_files`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_landing_lanes.py::test_probe_wire[traversal]`
**WIRE 3**: `docs/03-analysis/probes/phase5-gate-feature-scope/landing_lanes.py:main` → `read_minted_owner`
**WIRE-PIN 3**: `h-mad/tests/test_h_mad_landing_lanes.py::test_probe_wire[owner]`
**WIRE 4**: `docs/03-analysis/probes/phase5-gate-feature-scope/landing_lanes.py:main` → `liveness_evidence`
**WIRE-PIN 4**: `h-mad/tests/test_h_mad_landing_lanes.py::test_probe_wire[liveness]`
**WIRE 5**: `docs/03-analysis/probes/phase5-gate-feature-scope/landing_lanes.py:main` → `lane_listing`
**WIRE-PIN 5**: `h-mad/tests/test_h_mad_landing_lanes.py::test_probe_wire[listing]`

**Description**: Row 25 (S10, value), design §12 and spec FR-10's landing precondition: `landing_lanes.py [--path DIR]...`. `lane_listing()` runs `hmad-dispatch worktree-ps --limit 200` (30 s) and returns the paths and an error word by plan §"The lane listing the landing probe reads"; every listed lane is read whatever the word. Per lane: `walk_state_files(lane)` (wire 1 its `files`, wire 2 its `errors`), `read_state`, the live records; records merged by (realpath of file, feature), the first lane kept; owner `none`, `minted` by `read_minted_owner`, else `other`; the liveness column by `liveness_evidence`. The first error found gives `UNKNOWN`, with the lines read; a lane listed whole that holds nothing reads `NONE`. It opens no file for writing and its output is never committed. In tests the lane listing is a PATH stub. The owner and the liveness readings have separate fixtures, because `read_minted_owner` returns `False` before it looks at the lane when `H_MAD_LIVENESS_CLOCKS_OFF` is set: `[owner]` and every `test_owner_values` id run with that variable unset, on a real scratch git directory whose `h-mad-session-id.*` file names (or does not name) the record's owner, and assert the owner column alone; `[liveness]` alone runs with the variable set, so the heartbeat is the only clock, and asserts the liveness column. The `[undecided-presence]` fixture is built as OD-9 says (Task 28).

Scaffold at RED. The CLI and `lane_listing`, the callee of wire 5, both first appear in this file, so neither can be the missing caller of phase5-substeps 5d's exception. RED's first step therefore writes the test file and then the prescribed stub `landing_lanes.py`, in which `lane_listing()` and `main()` are defined and each raises `NotImplementedError`. At RED every pin fails by its assertion on the CLI's output (no `LANDING-LANES:` line), never by an import error; the 5e wire-scoped revert of each connection, made on the GREEN tree where `lane_listing` works, is what shows that the absence of that one connection fails its pin.

OPEN-DECISION: OD-5, the probe passed the record wrapper to `liveness_evidence`, which replaces a non-dictionary with an empty one, so a live record would lose its owner and heartbeat evidence while the line stays well-formed — resolve in 5d. Named implementation: the probe calls `liveness_evidence(record.data, lane)`, and `[liveness]` asserts, in the real CLI output with the other clocks off, a `LIVENESS: LIVE evidence=` reading that carries the record's fresh heartbeat age; the row `liveness-gets-the-wrapper` passes the `LiveRecord` itself and is caught there.

**Code structure**:
```python
def lane_listing() -> tuple[tuple[str, ...], str | None]: ...  # paths, error word
def main(argv: list[str] | None = None) -> int: ...           # LANDING-LANES: NONE | <K> | UNKNOWN ...
```

**Tests** (informational):
- `tests/test_h_mad_landing_lanes.py::test_probe_wire[discovery|traversal|owner|liveness|listing]` (5)
- `tests/test_h_mad_landing_lanes.py::test_listing_completeness[complete|command-failed|not-object|worktrees-not-list|entry-without-path|truncated|total-count-mismatch|omitted-hosts|missing-key]` (9), each condition with its own captured envelope beside the complete one, which reads `NONE`.
- `tests/test_h_mad_landing_lanes.py::test_incomplete_lane[missing-lane|unlistable-lane|unlistable-subdirectory|undecided-presence|unreadable-state|readable-empty]` (6), as plan §"The lane listing the landing probe reads".
- `tests/test_h_mad_landing_lanes.py::test_probe_tokens[none|records|unknown]` (3)
- `tests/test_h_mad_landing_lanes.py::test_owner_values[minted|other|none]` (3): `[minted]` lists two lanes, puts the shared record in the first lane displayed and the only `h-mad-session-id.*` file that mints its owner in the second, a later checked lane, and asserts exactly one output row for the record, with owner `minted` (spec: `other` is an id no checked lane minted, so the probe asks `read_minted_owner(lane, owner)` of every checked lane, never of the displayed lane alone).
- `tests/test_h_mad_landing_lanes.py::test_shared_by_symlink_one_line` (1)
- `tests/test_h_mad_landing_lanes.py::test_probe_encoding` (1)
- `tests/test_h_mad_landing_lanes.py::test_probe_opens_no_file_for_writing` (1): runs `main(argv)` in process under `sys.addaudithook`, recording every `open` event whose mode or flags can write (`w`, `a`, `x` or `+` in the mode; `O_WRONLY`, `O_RDWR`, `O_CREAT`, `O_TRUNC` or `O_APPEND` in the flags) and every `os.remove`, `os.rename`, `os.replace` and `os.mkdir` event, and requires none; the sha256 of every store and file of the fixture is also compared before and after, for a persistent effect. A file opened for writing and closed unchanged, or a temporary file created and removed, is seen by the first and not the second. Residual: the child processes (the PATH stub of the listing and git's read-only calls, which carry `--no-optional-locks`) are outside the audit hook.
- `tests/test_h_mad_landing_lanes.py::test_probe_usage_exit_2` (1)

Total 30 test ids, every one failing at RED (the stub raises). **Stated counts** (whole files, informational): RED 30 failing, 0 passing (the file is new); GREEN 30 passing.

**Mutation rows** (`landing_lanes.json`, 13):

| Name | Change | Killed by |
|---|---|---|
| `probe-files-root-only` | the root file alone in place of the walk's `files` | `tests/test_h_mad_landing_lanes.py::test_probe_wire[discovery]` |
| `probe-files-fixed` | one fixed set of files | `tests/test_h_mad_landing_lanes.py::test_probe_wire[discovery]` |
| `probe-errors-dropped` | `()` in place of the walk's `errors` | `tests/test_h_mad_landing_lanes.py::test_probe_wire[traversal]` |
| `probe-errors-fixed` | one fixed error | `tests/test_h_mad_landing_lanes.py::test_incomplete_lane[readable-empty]` |
| `probe-owner-false` | `read_minted_owner` gives `False` | `tests/test_h_mad_landing_lanes.py::test_probe_wire[owner]` |
| `probe-owner-true` | `read_minted_owner` gives `True` | `tests/test_h_mad_landing_lanes.py::test_owner_values[other]` |
| `probe-liveness-empty` | the liveness column is empty | `tests/test_h_mad_landing_lanes.py::test_probe_wire[liveness]` |
| `probe-liveness-fixed` | one fixed liveness line | `tests/test_h_mad_landing_lanes.py::test_probe_wire[liveness]` |
| `probe-listing-complete` | `lane_listing` always reports complete | `tests/test_h_mad_landing_lanes.py::test_probe_wire[listing]` |
| `probe-listing-failed` | `lane_listing` always reports `listing-failed` | `tests/test_h_mad_landing_lanes.py::test_listing_completeness[complete]` |
| `liveness-gets-the-wrapper` | `liveness_evidence` is given the `LiveRecord` | `tests/test_h_mad_landing_lanes.py::test_probe_wire[liveness]` |
| `probe-writes-scratch-file` | the probe writes a temporary file beside its first lane and removes it | `tests/test_h_mad_landing_lanes.py::test_probe_opens_no_file_for_writing` |
| `probe-owner-displayed-lane-only` | `read_minted_owner` is asked of the record's displayed lane alone | `tests/test_h_mad_landing_lanes.py::test_owner_values[minted]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-53.1: The probe never prints `NONE` when the listing was incomplete or a lane, a directory its discovery lists, or a file could not be read, or a presence could not be decided.
- [ ] AC-53.2: The 13 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 5, 47.

---

## Task 54: Store reading (S10)

**Production file**: `docs/03-analysis/probes/phase5-gate-feature-scope/store_reading.py`
**Test file**: `h-mad/tests/test_h_mad_landing_lanes.py`
**Task shape**: `new-behaviour`

**Description**: The store reading of landing steps 3 and 7 (design §12; plan §"Landing sequence"). `store_reading.py --record FILE STORE...` prints `STORES: RECORDED <n>` or `STORES: UNREADABLE <store>`; `--compare FILE` reads again and prints `STORES: SAME`, `STORES: CHANGED` with the store and the fields that differ, or `STORES: UNREADABLE`, which never counts as same. Fields per store: the named path, its type and link text, the resolved path, device, inode, size, `mtime_ns`, and the sha256 of the resolved file. Exit 0 for every reading, 2 with nothing on stdout for a usage or internal error. Exercised on scratch stores with the writer of `7a3cca48` and this tree's.

**Code structure**:
```python
def read_store(path: str) -> dict[str, object]: ...
def main(argv: list[str] | None = None) -> int: ...
```

**Tests and RED split** (all fail at RED: the probe does not exist):
- `tests/test_h_mad_landing_lanes.py::test_store_reading[quiet|same-bytes|overlap|in-flight|unreadable]` (5), as plan §"Landing sequence" step 7 names them.
- `tests/test_h_mad_landing_lanes.py::test_store_reading_fields` (1)
- `tests/test_h_mad_landing_lanes.py::test_store_reading_usage_exit_2` (1)

**Stated counts**: RED 7 failing, 30 passing (Task 53's nodes in the same file); GREEN 37 passing.

**Mutation rows** (`landing_lanes.json`, 3):

| Name | Change | Killed by |
|---|---|---|
| `compare-ignores-inode` | inode and `mtime_ns` are not compared | `tests/test_h_mad_landing_lanes.py::test_store_reading[same-bytes]` |
| `compare-ignores-link` | the type and link text are not compared | `tests/test_h_mad_landing_lanes.py::test_store_reading[overlap]` |
| `unreadable-counts-as-same` | an unreadable store reads `SAME` | `tests/test_h_mad_landing_lanes.py::test_store_reading[unreadable]` |

**Existing specs to re-anchor**: none.

**Acceptance Criteria**:
- [ ] AC-54.1: The 3 rows are caught; the full suite passes.

**Dependencies on other tasks**: Task 11.

---

## Task 55: Contract text (S10)

**Production file**: `h-mad/SKILL.md`, `h-mad/references/phase5-substeps.md`, `h-mad/references/failure-recovery.md`, `h-mad/references/codex-runtime.md`, `h-mad/references/agy-runtime.md`, `h-mad/references/grok-runtime.md`, `h-mad/references/state-schema.md`, `h-mad/references/helper-scripts.md`
**Test file**: `h-mad/tests/test_h_mad_phase5_scope_docs.py`
**Task shape**: `new-behaviour`

**Description**: Plan §"Documentation, both halves": every sentence removed has its replacement in the same commit. The statements this feature makes false, as that section lists them, are replaced; `failure-recovery.md` gains a row for each new assembler halt and for `exit-pending`; the documented commands print the `[H-MAD]` markers for the 5d mark and `exit-pending`; the exit and its two conditions for a codex or agy session are written beside the command; `codex-runtime.md` and `agy-runtime.md` gain the recommended layout, the exit, the three routes of FR-7 with the allow lines each layout needs, that the owner id plays no part in gating, and, below the oracle line, the literal commands of a gated session (a `<HMAD_SKILL_ROOT>` placeholder for the absolute path and an id read by `git rev-parse --absolute-git-dir` and then `cat` of that literal path, each a command of its own), with one sentence that the form holds for every state command; `grok-runtime.md` gains spec AC-11.4's statement and does not say that grok is ungated or has no gate; `helper-scripts.md` gains the `scope` verb with its `TDD-SCOPE:` token and the two halts. `SKILL.md` stays under `BUDGET_BYTES` of `h-mad/tests/test_h_mad_skill_budget.py`, long text going to the references. `test_claims_section_fenced_lines` (`h-mad/tests/test_host_runtime_docs.py`), `h-mad/tests/test_h_mad_tdd_gate_docs.py`, `h-mad/tests/test_h_mad_agy_authorship_docs.py`, `h-mad/tests/test_h_mad_codex_runtime.py` and `test_helper_scripts_registers_the_judge` stay green unedited.

**Code structure**:
```python
# documentation only; the tests read each file and section
```

**Tests and RED split** (32 fail at RED, the text not being there; 1 guard passes, named below):
- `tests/test_h_mad_phase5_scope_docs.py::test_ac_11_1[5a-command|5a-worktree-first|5a-without-checkout|5c-branch|5d-mark|5g-exit|codex-authors-exit]` (7)
- `tests/test_h_mad_phase5_scope_docs.py::test_ac_11_3[skill-halt-protocol|failure-recovery|machine-wide-dropped]` (3)
- `tests/test_h_mad_phase5_scope_docs.py::test_ac_11_4[codex-layout|codex-exit|codex-routes|codex-owner-id|agy-layout|agy-exit|agy-routes|agy-owner-id|grok-no-shell-gate|grok-not-called-ungated]` (10)
- `tests/test_h_mad_phase5_scope_docs.py::test_ac_11_5[new-fields|only-step5-arms|one-feature-per-checkout]` (3)
- `tests/test_h_mad_phase5_scope_docs.py::test_ac_11_6[keeps-rule|checkout-change-leaves-step5]` (2)
- `tests/test_h_mad_phase5_scope_docs.py::test_no_documented_step6_or_step7` (1), spec AC-7.6: over the tracked contract text.
- `tests/test_h_mad_phase5_scope_docs.py::test_literal_gated_commands[codex|agy]` (2)
- `tests/test_h_mad_phase5_scope_docs.py::test_failure_recovery_halt_rows[checkout_mismatch|phase5_stage_planning|exit-pending]` (3)
- `tests/test_h_mad_phase5_scope_docs.py::test_helper_scripts_scope_verb_and_halts` (1)
- `tests/test_h_mad_phase5_scope_docs.py::test_exit_markers_printed` (1): the documented mark and exit commands, run on a scratch store, print their `[H-MAD]` markers, and after each command the test reopens the store and asserts its fields, since a command can print a marker and change nothing: after the mark, the record is still live (`phase` `"step5"`) with `phase5_stage` `"implementing"`; after the exit, `phase` is no longer `"step5"` and `implementation_checkout` and `phase5_stage` are cleared; and where the documented route is `exit-pending` (the halt row of `failure-recovery.md` that Task 55 adds), the re-read record is still live, with its checkout and stage unchanged.

**Stated counts**: RED 32 failing, 1 passing; GREEN 33 passing (the file is new).

`test_no_documented_step6_or_step7` holds a property that is true today, so once the RED dispatch has written it, it passes: it is a guard (convention 9), listed as passing at RED and observed failing under `docs-step6-documented`. The other 32 fail at RED because the text is not there.

**Mutation rows** (`phase5_scope_docs.json`, 5):

| Name | Change | Killed by |
|---|---|---|
| `docs-5a-checkout-dropped` | the 5a command loses its checkout | `tests/test_h_mad_phase5_scope_docs.py::test_ac_11_1[5a-command]` |
| `docs-machine-wide-restored` | the machine-wide statement returns | `tests/test_h_mad_phase5_scope_docs.py::test_ac_11_3[machine-wide-dropped]` |
| `docs-grok-sentence-dropped` | the grok statement is dropped | `tests/test_h_mad_phase5_scope_docs.py::test_ac_11_4[grok-no-shell-gate]` |
| `docs-halt-row-dropped` | the `checkout_mismatch` row is dropped | `tests/test_h_mad_phase5_scope_docs.py::test_failure_recovery_halt_rows[checkout_mismatch]` |
| `docs-step6-documented` | a documented command sets `phase` to `step6` | `tests/test_h_mad_phase5_scope_docs.py::test_no_documented_step6_or_step7` |

**Existing specs to re-anchor**: those of plan §"Existing tests and mutation specs affected" for these files: `agy_authorship_docs`, `assemble_tdd_review`, `baseline_sha`, `batch_doc_rules`, `grok_audit_surface`, `new_caller_carveout_copies`, `reanchor_diff`, `review_attribution_docs`, `wire_registry_key`, `archreview_done_marker_recovery`, `host_runtime_docs`, `context_budget_docs` and the other `SKILL.md` specs; for `helper-scripts.md`, `batch_doc_rules`, `context_budget_docs`, `doc_block_exec`, `mutation_harness`.

**Acceptance Criteria**:
- [ ] AC-55.1: The documented exit names its performers and, for a codex or agy session, both conditions, beside the command.
- [ ] AC-55.2: The 5 rows are caught; the full suite passes.

**Dependencies on other tasks**: Tasks 15, 16, 28, 47, 52.

---

## Task 56: Whole-feature evidence (S11)

**Production file**: none
**Test file**: none
**Task shape**: `operational`

**Description**: S11 runs what Tasks 1 to 55 built and mutated, on the branch head, and records each reading with its command; it writes no code. The landing report is landing step 2 and not part of this task. Steps, each read on its own token or summary:
1. Full suite: `rtk proxy .venv/bin/python -m pytest` from the repository root, all passing.
2. The differential under every supported Python: `.venv/bin/python -m pytest h-mad/tests/test_h_mad_phase5_scope_differential.py -q`, every id of `test_crossed_corpus` passing with `CHANGES_IN_FORCE` holding every class the tasks named, and each `test_class_has_difference` id passing; the list of interpreters that ran is recorded. The Linux evidence is called simulated, and it is these tests, run in this step and named in the record: `tests/test_h_mad_phase5_scope.py::test_checkout_match_without_f_getpath` (checkout matching through `canonical_directory`'s fallback with `F_GETPATH` removed) and `tests/test_h_mad_phase5_scope.py::test_fold_discriminator[case-sensitive-volume-absent-document]` with `::test_checkout_match_without_f_getpath[case-variant-case-sensitive-volume]` (the mounted case-sensitive volume); a named skip of the volume is recorded as such.
3. The topologies: `.venv/bin/python -m pytest h-mad/tests/test_h_mad_phase5_scope_topologies.py -q`, each test driving the hooks and the writer under every supported Python inside it; the interpreters each launcher log names are recorded.
4. Mutation: the harness on each of the ten new specs of convention 5 (`python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/phase5_scope.json`, and the same for the other nine, each named literally), every row caught, none by a crash alone, read on the `MUTATION:` token; every existing spec a task named re-run in full; `python3.11 h-mad/scripts/h_mad_mutation_harness.py --check-anchors`, with no spec argument, which sweeps every committed spec in the repository, no drift.
5. Timing, both sides: `python3.11 docs/03-analysis/probes/phase5-gate-feature-scope/timing.py --old "$OLD" --runs 20` in scratch (the 20,000-file fixture), `$OLD` filled as in Task 2, and the same with `--repo "$PWD"` from the repository root, read-only, `TIMING: max_added_ms` at most 300 in both, the codex, agy and Claude hooks on the three targets of the root checkout, and the codex and agy shells on one real command each, with and without a live root record in the scratch run, and in the `--repo` run once, in the record state the repository holds then, which its case lines name, no record being written there (Task 2's cases; plan §"Tradeoffs to preserve", the owed readings; the spec states the bound on all five surfaces). The same runs print the `TIMING-SECOND-CHECKOUT:` lines, an explicit target in a second checkout for each hook, whose own discovery is a second one (design §7's owed reading); they are recorded apart and are not held to the 300 ms bound, which covers the two repositories' three targets and the two shell commands. The S6 reading of convention 16 is recorded beside these.
6. The census, re-run as Task 2 runs it, compared with the expectations edited by this feature: only those of plan §"Existing tests and mutation specs affected" (the `[state-file]` id, the two `GATE_KINDS` assertions) and the `_tree_b` helper.
7. The mixtures of plan §"Mixture corpora": `python3.11 docs/03-analysis/probes/phase5-gate-feature-scope/mixtures.py --old "$OLD" --new "$PWD" --set gates`, then the same with `--set writes` and `--set staging` (Task 2's probe), each `MIXTURES: PASS`, no mixture allowing what both trees refuse; a `MIXTURES: FAIL` names the mixture and the case and is stopped on.

OPEN-DECISION: OD-14, design §2's timings were made by a prototype that closes git's input and waits for it, and design §7's reading of a private repository is not marked as not re-runnable — resolve in 5d. Named implementation: step 5's readings, taken by `timing.py` on the committed hooks with the committed discovery, are the readings the success criterion uses, and they replace design §2's prototype timings for every bound; the marking of design §7's reading is design text and is owed to the design.

OPEN-DECISION: OD-15, the spec's Security sentence on reproductions of a gate weakness while ruled limits stand is the operator's word, and design text has the same property (the residuals it states as the spec's, and the mutants of §13) — resolve in 5d. Named implementation: before each push the diff is reviewed for public text (plan §"Risks", the public-repository row): tests, fixtures, mutation `_mechanism` texts and probe output state required decisions only; no test builds the case of a stated residual; the ruling on the sentence itself is the operator's (see the private record).

**Acceptance Criteria**:
- [ ] AC-56.1: Every success criterion of the plan that does not begin with a landing mark has its reading recorded on the tested head, with the command that produced it.
- [ ] AC-56.2: The full suite, the differential, the topologies and every new mutation spec pass on that head.

**Dependencies on other tasks**: Tasks 1 to 55.

## Mutation-row totals

Rows added per spec, by task, with the rows later tasks remove:

| Spec | Added (tasks) | Removed (tasks) | Net |
|---|---|---|---|
| `phase5_scope_differential.json` | 14 (1, 2) | 0 | 14 |
| `phase5_scope.json` | 72 (3, 4, 5, 6, 10, 20, 47, 48) | 5 (38, 47) | 67 |
| `phase5_scope_wires.json` | 231 (5, 7, 8, 18, 19, 21 to 27, 29 to 46, 48 to 51) | 5 (30, 35, 38, 42, 44) | 226 |
| `phase5_arming_inputs.json` | 32 (9) | 0 | 32 |
| `state_write_scope.json` | 38 (8, 11, 12, 13, 14) | 0 | 38 |
| `assemble_tdd_scope.json` | 7 (15, 16, 17) | 0 | 7 |
| `tdd_judge_scope.json` | 13 (28) | 0 | 13 |
| `landing_lanes.json` | 16 (53, 54) | 0 | 16 |
| `phase5_scope_topologies.json` | 12 (52) | 0 | 12 |
| `phase5_scope_docs.json` | 5 (55) | 0 | 5 |
| All | 440 | 10 | 430 |

The design states no total for the mutation rows; these are this plan's, derived from the per-task tables above: 55 tasks carry a table, whose rows sum to 440, and the 10 removals are the rows named on the `Removed:` lines of Tasks 30, 35, 38 (5), 42, 44 and 47.

## Version History
- v1.0: 2026-11-26. Initial implementation plan draft, from design v1.10, plan v1.16 and spec v1.17, at bb88b6cc: 56 tasks in steps S0 to S11, 42 of them wiring. OD-1 to OD-7 and OD-9 to OD-15 stand as OPEN-DECISION lines on their tasks; OD-8 is measurement and is answered by Task 2. Answers no audit cycle.
- v1.1: 2026-11-27. Answers impl-plan audit cycle 1, non-PASS: phase5-gate-feature-scope.impl-plan.audit.v1.p1.md (31 must, 3 should) and phase5-gate-feature-scope.impl-plan.audit.v1.p2.md (6 must, 2 should, 1 nit), each finding fixed once where the two overlap. Applies the operator's rulings of 2026-11-26: OD-1 (a), OD-12 (a) and OD-13 (a) stand as rulings, the killpg implementation removed; the 5c branch; the RED of the pin-only wiring Tasks 26, 31, 32, 49 and 51 is the removal-mutant observation; OD-15 unchanged. WIRE-PIN lines repository-relative; stated counts whole-file totals; per-task checkpoints as the RED base inside a step; one decoder per host; interpreters by executable identity; FR-4 halves per case; precedence by overlap; the writer's step contract with the locked store and the caller's clock; one path boundary; FR-6 keeps-cases with each host's re-routing; H-LIST-INROOT moved onto the outside-root unreadable-state line; applying reason in arming_refusal; the legacy exception kept; guards and observations each with a mutant or a detector control; mixture, second-checkout and S6 timing readings given commands. 56 tasks, 42 wiring; 426 mutation rows added, 9 removed.
- v1.2: 2026-11-27. Corrective revision after the final gating round (round cap reached; not re-audited). Answers impl-plan audit cycle 2, non-PASS: phase5-gate-feature-scope.impl-plan.audit.v2.p1.md (31 must, 2 should), and an advisory delta review of v1.0 to v1.1 (3 must, 6 should, 3 nit; see the private record), each finding fixed once where the two overlap. Per-task dispatch order inside a step; harness commands assigned to the gated dispatch and the orchestrator; spec headers fixed; codex denials decoded without a kind; the differential keyed by surface and decision branch, with the legacy exception lifted at Task 47; a guard credited only as its row's test or by a stated observation procedure, under a row that reaches it; Python 3.9 import-time types; the writer's step contract with the feature key and the removed keys; the path boundary limited to filesystem paths; deterministic timing aggregation and shell timing cases; the legacy reader tokens; filtered applied entries; Task 50's planning expectation reversed and Task 48's agy guard moved to it; Task 52's controls by route; Task 47's equivalent mutant replaced and walk-root-not-normalised removed; the OD-1 residual narrowed. 56 tasks, 42 wiring; 440 mutation rows added, 10 removed.
- v1.3: 2026-11-27. Final corrective revision before 5c (not re-audited). Answers an advisory delta review of v1.1 to v1.2 (4 must, 8 should, 5 nit; see the private record); answers no further audit cycle. The gated GREEN's per-spec anchor check limited to specs that exist at the task's base, the orchestrator's checks being the evidence for a task's own rows; Task 47's legacy-exception guard asserted per host (the codex type, the agy fixed catch-all), AC-47.4 qualified to discovered files, the reading of spec AC-4.9 and design §3 stated, the re-raise set to the first read carrying an exception, and its shape new-behaviour; Task 3's read_state keeps an exception outside the tuple _state_status catches; Task 52's per-id rows by deciding route, the claude-codex topology re-assigned, bkit-migration an observation, the two-rows case removed; Task 11's merge owner precondition; Task 29's no-target and unresolvable ids named under claude-state-fixed-active; OD-2's agy catch-all text; the claude surface's legacy flag; emit_arming on the path boundary; timing's --repo run read-only; convention 3's kindless refusals; timing's --old with --samples. 56 tasks, 42 wiring; no mutation row added or removed.

