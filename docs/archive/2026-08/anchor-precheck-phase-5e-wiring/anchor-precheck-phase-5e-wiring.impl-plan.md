# Implementation Plan: anchor-precheck-phase-5e-wiring

> Source: docs/02-design/features/anchor-precheck-phase-5e-wiring.design.md (post-audit, v1.5, gate PASS)
> Branch target: feature/197-anchor-precheck-phase-5e-wiring

## Executive Summary

Seven tasks: one shared root resolver, a spec re-rooting with two structural guards, a file
classifier, the precheck wire into `run_spec`, the new CLI verdict, the suite assertions in both
projects, and the documentation — ordered so the resolver lands before anything depends on it and
the re-rooting lands before the suite assertion that needs portability.

## Task 1: root-resolver

**Production file**: `h-mad/scripts/h_mad_mutation_harness.py`
**Test file**: `h-mad/tests/test_h_mad_mutation_harness.py`
**Task shape**: `new-behaviour`

**Description**: Replace the root-resolution expression inlined in both `precheck_spec()` and
`run_spec()` with one shared helper. Absolute and absent `root` values keep their current meaning;
a **relative** value changes from cwd-relative to spec-relative. No committed or test-constructed
spec uses a relative root today, so no existing caller observes the change.

**Code structure**:
```python
def _resolve_root(spec: dict, spec_path: Path) -> Path:
    """The directory a spec's `file` paths are relative to.

    Absolute -> itself. Relative -> resolved against the SPEC's directory, not
    the caller's cwd. Absent -> the spec's directory.
    """
    ...
```

**Acceptance Criteria**:
- [ ] AC-1.1: A spec at `<dir>/s.json` with `"root": ".."` yields the same resolved target paths when the harness runs from `<dir>`, from `/tmp`, and from the repository root.
- [ ] AC-1.2: A spec with an absolute `root` resolves to exactly that path from any cwd.
- [ ] AC-1.3: A spec with no `root` key resolves to the spec file's own directory.
- [ ] AC-1.4: `precheck_spec()` and `run_spec()` both call `_resolve_root`; a test asserts both resolve the same spec to the same root, and no other root-resolution expression remains in the module.
- [ ] AC-1.5: The pre-existing `h-mad/tests/test_h_mad_mutation_harness.py` passes unchanged.

**Dependencies on other tasks**: None

---

## Task 2: portable-spec-roots

**Production file**: `h-mad/tests/mutation-specs/audit_gate_stamp.json` (and the 15 sibling `.json` specs in that directory, each edited identically: `root` only)
**Secondary production file**: `handoff/tests/mutation-specs/census_registry.json` (edited differently: `root`, all 18 `mutations[].file` values, and `command`)
**Test file**: `h-mad/tests/test_h_mad_mutation_harness.py`
**Task shape**: `refactor`

**Description**: Re-root every committed spec onto the spec-relative form Task 1 enables. h-mad's 16
change `root` only. handoff's one additionally drops the `handoff/` prefix from all 18
`mutations[].file` values and from its `command` pytest path, because its root sits one level above
its own skill and the domain layer requires a skill to be runnable from a bare clone with no
hardcoded path outside its own directory. Two structural guards ship with it so the property cannot
regress.

**Code structure**:
```python
# tests only — no new production symbols
def test_no_committed_spec_has_an_absolute_root() -> None: ...
def test_every_committed_spec_resolves_within_its_own_skill() -> None: ...
```

**Acceptance Criteria**:
- [ ] AC-2.1: No committed spec under any `tests/mutation-specs/` directory has an absolute `root`; asserted by a test that walks the repository.
- [ ] AC-2.2: `--check-anchors` over the h-mad specs returns `ANCHORS_OK` with `drifted=0 unreadable=0` from the repository root, from `/tmp`, and from a directory outside the repository, and all three invocations agree exactly on every count. Counts are read from the tree, not hardcoded.
- [ ] AC-2.3: The same sweep gives the same verdict with the repository copied to a different absolute path.
- [ ] AC-2.4: A mutation run executed inside a `git worktree` resolves targets inside that worktree and leaves the main checkout's files byte-identical.
- [ ] AC-2.5: Every mutation's `find` and `replace` are byte-identical before and after the re-rooting, and per-spec anchor counts match before and after.
- [ ] AC-2.6: Every committed spec resolves within its own skill directory; asserted repository-wide so a future spec cannot reintroduce a root above its skill.

**Dependencies on other tasks**: Task 1 (must complete first)

---

## Task 3: spec-classifier

**Production file**: `h-mad/scripts/h_mad_mutation_harness.py`
**Test file**: `h-mad/tests/test_h_mad_mutation_harness.py`
**Task shape**: `new-behaviour`

**Description**: Classify a `.json` file in a specs directory as `spec`, `not-a-spec`, or
`unclassifiable`, so a directory glob cannot mistake an unrelated file for drift and cannot silently
drop a corrupt one. The `spec` test keys on the loader's own necessary condition — `_load_spec`
requires a non-empty `mutations` list — rather than a second guess at spec shape.

**Code structure**:
```python
def classify_spec_file(path: Path) -> tuple[str, str | None]:
    """('spec'|'not-a-spec'|'unclassifiable', detail).

    Keys on `_load_spec`'s own necessary condition, never a second definition.
    """
    ...
```

**Acceptance Criteria**:
- [ ] AC-6.1: A file with a non-empty `mutations` list classifies `spec`; one without classifies `not-a-spec`. A test asserts the classifier and `_load_spec` agree — every file classified `not-a-spec` is one the loader rejects, and every file classified `spec` passes the loader's `mutations` check.
- [ ] AC-6.2: A file that does not parse as JSON classifies `unclassifiable`, is reported by name, and contributes nothing to the drift count.
- [ ] AC-6.3: A file classified `spec` that then raises `SpecError` is a finding, not a skip.
- [ ] AC-6.4: Skipped and unclassifiable files are named in the output on **every** verdict, including a successful run.
- [ ] AC-6.5: A test asserts every `.json` currently committed under `h-mad/tests/mutation-specs/` classifies `spec`.
- [ ] AC-6.6: A differential corpus — valid spec, drifted spec, `mutations` without `command`, mutation missing `find`, valid non-spec JSON, malformed JSON, empty file, non-`.json` file — is run through pre-change and post-change classification, verdicts diffed, and every softened verdict accounted for individually against an intended list enumerated in advance. A passing suite is not accepted as evidence for this AC.

**Dependencies on other tasks**: Task 1 (must complete first)

---

## Task 4: sibling-precheck-wire

**Production file**: `h-mad/scripts/h_mad_mutation_harness.py`
**Test file**: `h-mad/tests/test_h_mad_mutation_harness.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_mutation_harness.py:run_spec` → `precheck_spec`
**WIRE-PIN**: `h-mad/tests/test_h_mad_mutation_harness.py::test_clean_spec_beside_a_drifted_sibling_refuses_before_mutating`

**Description**: Before `run_spec()` executes its baseline command, sweep every **sibling** spec in
the same directory — excluding the spec being run — and refuse the whole run if any has drifted or
declared itself a spec and failed to load. Sibling-only scoping is load-bearing: sweeping the
directory including self would make the existing `REFUSED` verdict unreachable for drift and break
the eleven tests that assert it.

**Code structure**:
```python
def _sibling_specs(spec_path: Path) -> dict:
    """{'spec_paths': [Path, ...], 'skipped': [{'path': str, 'reason': str}, ...]}

    Siblings only: `spec_path` itself is excluded. `spec_paths` is always a
    list; the integer count lives in the result as `precheck['swept']`.
    """
    ...
```

**Acceptance Criteria**:
- [ ] AC-3.1: Given a directory holding a clean spec and a drifted spec, running the **clean** one refuses and applies **zero** mutations — target files byte-identical before and after. **This is the WIRE-PIN**: it fails when the `precheck_spec` call is removed from `run_spec` and `precheck_spec` is left intact.
- [ ] AC-3.2: In an all-clean directory the run proceeds and returns its ordinary verdict. This is the fall-through test: it fails if the precheck is mutated to refuse unconditionally.
- [ ] AC-3.3: The refusal names each drifted spec by filename, each drifted mutation by name, and the **resolved** root for that spec.
- [ ] AC-3.4: The refusal distinguishes "the spec you ran drifted" from "a sibling drifted".
- [ ] AC-3.5: A drifted spec in a different directory does not affect the verdict.
- [ ] AC-6.4-wire: The `precheck` census — `{'swept': int, 'skipped': [...]}` — is attached to **every** result shape, including `ALL_CAUGHT`, not only to a refusal.

**Dependencies on other tasks**: Task 1, Task 3 (must complete first)

---

## Task 5: precheck-failed-verdict

**Production file**: `h-mad/scripts/h_mad_mutation_harness.py`
**Test file**: `h-mad/tests/test_h_mad_mutation_harness.py`
**Task shape**: `new-behaviour`

**Description**: Render the pre-refusal as its own verdict carrying sweep-level counts and no
mutation counts. The word is `PRECHECK_FAILED`, not `PRECHECK_DRIFTED`, because a refusal caused
solely by an unreadable sibling reports `drifted=0` and naming that outcome "DRIFTED" would rebuild
the collapse this project files against `--check-anchors`. This task also re-anchors
`mutation_harness.json`, whose `change-the-summary-line-callers-parse` mutation anchors the exact
summary-line f-string being modified.

**Code structure**:
```python
# in main(), beside the existing count-free branch:
if verdict == "PRECHECK_FAILED":
    print(f"MUTATION: {verdict} specs={result['precheck']['swept']} "
          f"drifted={len(result['drifted'])} unreadable={len(result['unreadable'])}")
```

**Acceptance Criteria**:
- [ ] AC-4.1: The line reads `MUTATION: PRECHECK_FAILED specs=<N> drifted=<K> unreadable=<J>` and prints none of `mutations=`, `caught=`, `survived=`, `refused=`.
- [ ] AC-4.2: `PRECHECK_FAILED` exits **2**.
- [ ] AC-4.3: No existing consumer matching on `MUTATION: REFUSED` matches the new word; verified by a repository grep asserted in a test.
- [ ] AC-4.4: An `[H-MAD]` marker line is emitted for the new verdict.
- [ ] AC-4.5: `mutation_harness.json`'s summary-line anchor is re-anchored in the **same commit** as this change, and `--check-anchors` returns `ANCHORS_OK` afterwards.
- [ ] AC-4.6: A sibling that declares itself a spec and raises `SpecError` lands in `unreadable`, refuses the run, and is named with the loader's error text; a run refused solely for that reason prints `drifted=0` with non-zero `unreadable=`.

**Dependencies on other tasks**: Task 4 (must complete first)

---

## Task 6: committed-spec-suite-assertion

**Production file**: `h-mad/tests/test_h_mad_mutation_harness.py`
**Secondary production file**: `handoff/tests/test_mutation_specs_clean.py` (new; the same assertion for the sibling project, which needs its own copy because the assertion is per-project by construction)
**Test file**: `h-mad/tests/test_h_mad_mutation_harness.py`
**Task shape**: `new-behaviour`

> Note on the fields: this task's deliverable **is** a test, so production and test file coincide.
> That is deliberate and not a copy error — the feature's always-on half is an assertion, and there
> is no separate production symbol for it beyond `precheck_spec`, which Task 1 already covers.

**Description**: Assert, from each project's own suite, that that project's committed specs are
un-drifted. This is the always-on half of the feature: it rides the full-suite run Phase 5f already
performs and fires whether or not a cycle runs any mutation. No test currently sweeps the committed
specs, which is how seven drifted anchors sat in the tree with the suite green.

**Code structure**:
```python
def test_committed_mutation_specs_are_not_drifted() -> None:
    """Sweeps this project's own tests/mutation-specs/.

    Locates the directory from __file__, filters through classify_spec_file,
    asserts a non-zero spec count, then calls precheck_spec per spec.
    """
    ...
```

**Acceptance Criteria**:
- [ ] AC-5.1: The test sweeps every spec in its own project's `tests/mutation-specs/` and fails naming each drifted spec, mutation, and resolved root.
- [ ] AC-5.2: The test asserts a non-zero spec count before evaluating drift; pointed at an empty directory it fails rather than passing vacuously.
- [ ] AC-5.3: The specs directory is located from `Path(__file__).resolve().parents[1]`, so the test passes under `pytest` from the repository root, from the project directory, and via the skills symlink.
- [ ] AC-5.4: The test calls `precheck_spec()` and does not re-implement the one-match rule.
- [ ] AC-5.5: Deliberately drifting one committed anchor fails the test and restoring it passes; the drift is applied and reverted under `try`/`finally` and the restore verified by re-reading the file, so a failure or interrupt cannot leave the checkout dirty.

**Dependencies on other tasks**: Task 2, Task 3 (must complete first)

---

## Task 7: documentation

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_h_mad_mutation_harness.py`
**Task shape**: `refactor`

**Description**: Bring the documentation into line with an obligation that is now mechanical.
§Phase-5e currently tells the operator to run `--check-anchors` beforehand; the run does it. The
registry entry and the recovery table are the contract surfaces for the new verdict, and a verdict
absent from the recovery table has no documented route.

**Code structure**:
```python
# tests only
def test_skill_documents_the_precheck_is_automatic() -> None: ...
def test_recovery_table_carries_the_new_verdict() -> None: ...
```

**Acceptance Criteria**:
- [ ] AC-7.1: SKILL.md §Phase-5e states that the mutation run performs the sibling sweep itself and refuses on sibling drift, rather than instructing the operator to sweep beforehand.
- [ ] AC-7.2: The `h_mad_mutation_harness.py` registry entry documents `MUTATION: PRECHECK_FAILED`, its counts, and its exit code.
- [ ] AC-7.3: SKILL.md documents that a relative spec `root` is spec-relative.
- [ ] AC-7.4: A doc test asserts the new verdict word appears in SKILL.md.
- [ ] AC-7.5: `references/failure-recovery.md` gains a row for `MUTATION: PRECHECK_FAILED` naming its halt reason and remedy.

**Dependencies on other tasks**: Task 5 (must complete first)

## Version History

- v1.0: Initial implementation plan draft, derived from design v1.5.
