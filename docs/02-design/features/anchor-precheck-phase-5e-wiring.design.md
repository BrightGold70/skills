# Design: anchor-precheck-phase-5e-wiring

## Executive Summary

Add one shared root resolver, a sibling-only precheck in `run_spec()` returning a new count-free
verdict, a structural spec classifier, and a suite assertion over the repository's own committed
specs — re-rooting all 17 specs onto spec-relative paths so the assertion is portable.

## Overview

The design intent is to add enforcement without changing any verdict that exists today. The single
decision that shapes everything else is that the precheck sweeps **siblings only, excluding the spec
being run**: the running spec's own drift keeps its existing `REFUSED` verdict, and only a
neighbour's drift produces the new one.

That choice is not cosmetic. Sweeping the whole directory including self would make `REFUSED`
unreachable for drift — the precheck would fire first on every drifted spec — orphaning its
`failure-recovery.md` row and breaking eleven existing tests that assert it. Sibling-only also makes
AC-3.4's "distinguish your spec from a sibling" fall out of the structure rather than being a
message-formatting rule that could regress silently.

## Architecture Overview

```
                    _resolve_root(spec, spec_path)        ← ONE resolver, FR-1
                     ·  absolute      → as-is
                     ·  relative      → spec_path.parent / value
                     ·  absent        → spec_path.parent
                          │
        ┌─────────────────┼──────────────────┬─────────────────────┐
        │                 │                  │                     │
  precheck_spec()    run_spec()      _sibling_specs()      test_committed_
   (unchanged          │              (new, FR-3)          specs_are_clean
    semantics)         │                  │                 (new, FR-5)
                       │                  │                     │
                       ▼                  ▼                     ▼
              1. sweep SIBLINGS ──── classify_spec_file()   globs its OWN
                 (excluding self)      (new, FR-6)          project's specs,
                 any drift?            spec / not-a-spec /  calls precheck_spec
                    │  yes             unclassifiable       asserts count > 0
                    ▼
              PRECHECK_DRIFTED  ← new verdict, no mutation counts, exit 2
                    │  no
                    ▼
              2. existing baseline → per-mutation apply/restore
                 own drift here still yields REFUSED  ← UNCHANGED
```

Every path reaches `precheck_spec()` for the one-match rule and `_resolve_root()` for path
resolution. Neither is re-implemented anywhere, satisfying the single-source contract.

## Detailed Design

### `_resolve_root(spec: dict, spec_path: Path) -> Path` (new, FR-1)

Replaces the inline `Path(spec.get("root") or spec_path.parent).resolve()` currently duplicated in
`precheck_spec()` and `run_spec()`.

| declared `root` | resolves to | change |
|---|---|---|
| absent / empty | `spec_path.parent` | none |
| absolute | that path | none |
| relative | `spec_path.parent / value` | **was cwd-relative** |

Only the third row changes, and no committed or test-constructed spec exercises it today (verified:
all 17 committed roots and all 8 test-built roots are absolute), so no current caller observes the
difference.

### `_sibling_specs(spec_path: Path) -> list[Path]` (new, FR-3)

`sorted(spec_path.parent.glob("*.json"))` minus `spec_path` itself, filtered through
`classify_spec_file()`. Directory-scoped, so `h-mad/` and `handoff/` never sweep each other.

### Precheck inside `run_spec()` (FR-3, FR-4)

Runs before the baseline command, before any mutation is applied. For each sibling classified as a
spec, call `precheck_spec()`; collect drift. If any sibling drifted, return immediately:

```python
{"verdict": "PRECHECK_DRIFTED",
 "specs": <siblings swept>,
 "drifted": [{"spec": name, "root": str(resolved_root),
              "mutations": [{"name": ..., "hits": n, "hints": [...]}]}],
 "skipped": [{"path": name, "reason": "not-a-spec" | "unclassifiable"}]}
```

The dict deliberately carries **no** `mutations`/`caught`/`survived`/`refused` keys. Their absence is
the enforcement of AC-4.1: a formatter cannot print a count that is not there, so the no-counts rule
cannot regress into printing zeros.

`run_spec()`'s docstring contract — "raises `SpecError` only when the spec itself is unusable; every
other outcome is a verdict" — is preserved: this is a verdict, not an exception.

### `classify_spec_file(path: Path) -> tuple[str, str | None]` (new, FR-6)

| condition | classification | counted as drift? | reported? |
|---|---|---|---|
| not valid JSON | `unclassifiable` | no | **yes, by name** |
| valid JSON, no non-empty `mutations` list | `not-a-spec` | no | yes, by name |
| valid JSON with non-empty `mutations` | `spec` | its drift counts | n/a |

The `mutations` test is the loader's own necessary condition — `_load_spec` raises
`SpecError("spec needs a non-empty `mutations` list")` — not a second guess at spec shape. A file
carrying `mutations` but missing `command` or a per-mutation `find` classifies as `spec` and then
fails to load, which is a reported finding rather than a silent skip (AC-6.3).

### CLI output (FR-4)

`main()` gains a branch beside the existing count-free one, which already exists for
`BASELINE_NOT_GREEN` and `RESTORE_FAILED`:

```python
if verdict == "PRECHECK_DRIFTED":
    print(f"MUTATION: {verdict} specs={result['specs']} drifted={len(result['drifted'])}")
elif verdict in {"BASELINE_NOT_GREEN", "RESTORE_FAILED"}:
    print(f"MUTATION: {verdict}")
else:
    print(f"MUTATION: {verdict} mutations=... caught=... survived=... refused=...")
```

Detail lines name the sibling spec, its **resolved** root, each drifted mutation with its hit count
and near-miss hints, and every skipped or unclassifiable file. The message states plainly that the
drift is in a *sibling*, not in the spec the operator asked to run — the two prescribe different
actions. Then `[H-MAD] <label> mutation PRECHECK_DRIFTED`, and exit **2**, joining the family of
outcomes that measured nothing.

### Re-rooting the committed specs (FR-2)

- **h-mad, 16 specs**: `root` `/Users/kimhawk/orca/skills/h-mad` → `"../.."`. Nothing else changes.
- **handoff, 1 spec**: `root` `/Users/kimhawk/orca/skills` → `"../.."` (the handoff skill directory,
  not the repository), the `handoff/` prefix stripped from all 18 `mutations[].file` values, and
  `command` `pytest handoff/tests/test_skill_candidates_census.py` → `pytest
  tests/test_skill_candidates_census.py`. This is the self-containment case AC-2.6 requires; its
  anchor text is still byte-identical.

Applied by a script that rewrites only the named keys and then asserts, per AC-2.5, that every
`find`/`replace` is byte-identical and that per-spec anchor counts match before and after.

### The suite assertion (FR-5)

A test in each project globs **its own** `tests/mutation-specs/`, asserts the spec count is non-zero
before evaluating anything, and calls `precheck_spec()` per spec — never re-deriving the one-match
rule. Failure names each drifted spec, mutation, hit count and resolved root. The specs directory is
located from `Path(__file__).resolve().parents[1]`, matching the idiom the existing doc test already
uses, so it is cwd-independent and survives the skills symlink.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_resolve_root` | `h-mad/scripts/h_mad_mutation_harness.py` | new | FR-1; one resolver for both entry points |
| `precheck_spec` / `run_spec` root lines | `h-mad/scripts/h_mad_mutation_harness.py` | modify | call the resolver instead of inlining it |
| `classify_spec_file` | `h-mad/scripts/h_mad_mutation_harness.py` | new | FR-6 |
| `_sibling_specs` | `h-mad/scripts/h_mad_mutation_harness.py` | new | FR-3 |
| precheck block in `run_spec` | `h-mad/scripts/h_mad_mutation_harness.py` | modify | FR-3 |
| `PRECHECK_DRIFTED` branch in `main` | `h-mad/scripts/h_mad_mutation_harness.py` | modify | FR-4 |
| 16 h-mad specs | `h-mad/tests/mutation-specs/*.json` | modify | FR-2, `root` only |
| handoff spec | `handoff/tests/mutation-specs/census_registry.json` | modify | FR-2/AC-2.6, root + prefixes + command |
| harness tests | `h-mad/tests/test_h_mad_mutation_harness.py` | modify | new behaviour + FR-5 assertion |
| handoff suite assertion | `handoff/tests/test_mutation_specs_clean.py` | new | FR-5 for handoff |
| own mutation spec | `h-mad/tests/mutation-specs/mutation_harness.json` | modify | re-anchor the summary line, AC-4.5 |
| SKILL.md §Phase-5e + registry | `h-mad/SKILL.md` | modify | FR-7 |
| recovery table | `h-mad/references/failure-recovery.md` | modify | FR-7/AC-7.5 |

## Implementation Order

1. `_resolve_root`, both call sites switched to it, tests for the three cases (FR-1). No behaviour
   change observable to any existing spec.
2. Re-root the 16 h-mad specs; assert anchor-text and anchor-count equality (FR-2, AC-2.5).
3. Re-root and re-prefix the handoff spec; same assertions plus its suite still green (AC-2.6).
4. `classify_spec_file` plus its differential corpus (FR-6, AC-6.6).
5. `_sibling_specs` and the precheck block in `run_spec`, returning the new verdict (FR-3).
6. `main`'s `PRECHECK_DRIFTED` branch, marker, and exit code (FR-4); re-anchor
   `mutation_harness.json` in the **same** commit (AC-4.5).
7. The suite assertions in both projects (FR-5).
8. Documentation: SKILL.md, registry entry, recovery row, doc test (FR-7).

Steps 1–3 must precede 7, because the suite assertion is not portable until the roots are.

## Data Model / Schema Changes

The mutation-spec format gains no keys. One key changes meaning: a **relative** `root` is now
spec-relative rather than cwd-relative. Absolute and absent are unchanged.

`run_spec()`'s return dict gains a third shape, alongside the full-count shape and the bare
`BASELINE_NOT_GREEN`/`RESTORE_FAILED` shape: `{verdict, specs, drifted[], skipped[]}`, carrying no
mutation counts by construction.

## API / Interface Changes

| Interface | Change |
|---|---|
| `_resolve_root(spec: dict, spec_path: Path) -> Path` | new, module-private |
| `classify_spec_file(path: Path) -> tuple[str, str \| None]` | new, module-level so tests reach it without duplicating it |
| `_sibling_specs(spec_path: Path) -> list[Path]` | new, module-private |
| `run_spec(spec_path)` | signature unchanged; may return the new verdict |
| CLI | no new flags. New stdout verdict `MUTATION: PRECHECK_DRIFTED specs=<N> drifted=<K>`, exit 2 |

No new flag is added deliberately: an opt-out would be reachable from ordinary use, which is exactly
what the spec's open question warned against. The harness's own tests avoid the precheck by
construction — a single-spec directory has no siblings — rather than by a suppression switch.

## Error Handling Strategy

Unchanged in kind. `SpecError` remains reserved for the spec being run being unusable, surfacing as
`MUTATION: UNREADABLE` and exit 2. A **sibling** that fails to load is never allowed to raise out of
the precheck: it is caught, classified, and reported as a named skipped file, because a neighbour's
broken JSON must not present as the run spec being unreadable. Drift is a verdict, never an
exception. Every new outcome prints an `[H-MAD]` marker.

## Test Strategy

Unit-level throughout, with the real filesystem under `tmp_path` — the harness's existing idiom.
Nothing is mocked: these are pure path and file-classification behaviours, and a fake would test the
fake. Two departures worth naming:

- **The differential corpus (AC-6.6) is a test, not a script.** It enumerates its intended softenings
  in advance and asserts the count matches exactly, so it fails if the relaxation widens.
- **FR-5's assertion runs against the real committed specs**, not a fixture. That is the entire
  point; a fixture would reproduce the blindness it exists to remove.

Regression provenance: the eleven existing tests asserting `REFUSED` are expected to stay green
**unchanged**, because sibling-only scoping leaves single-spec directories on the existing path. If
any one of them fails, that is a signal the precheck scope is wrong — not a test to update.

## Test Plan

| Scenario | File | Verifies |
|---|---|---|
| relative root from three different cwds resolves identically | `test_h_mad_mutation_harness.py` | AC-1.1 |
| absolute and absent roots unchanged | " | AC-1.2, AC-1.3 |
| the existing suite passes unchanged after the resolver switch | " (existing) | AC-1.5 |
| both entry points resolve one spec identically | " | AC-1.4 |
| no committed spec has an absolute root | " | AC-2.1 |
| sweep clean from repo root, `/tmp`, and a copied checkout | " | AC-2.2, AC-2.3 |
| run inside a worktree leaves the main checkout untouched | " | AC-2.4 |
| clean spec beside a drifted sibling refuses, zero mutations applied | " | AC-3.1 |
| all-clean directory runs normally | " | AC-3.2 |
| refusal names spec, mutation, resolved root, sibling-vs-self | " | AC-3.3, AC-3.4 |
| a drifted spec in another directory does not affect the verdict | " | AC-3.5 |
| verdict line carries `specs=`/`drifted=` and no mutation counts | " | AC-4.1 |
| exit code is 2; `[H-MAD]` marker emitted | " | AC-4.2, AC-4.4 |
| own spec drifted still yields `REFUSED` | " (existing, unchanged) | backward compatibility |
| committed specs sweep clean; empty dir fails loudly | " + `handoff/tests/test_mutation_specs_clean.py` | AC-5.1, AC-5.2 |
| specs dir located from the test file, not cwd; passes from three invocation dirs | " | AC-5.3 |
| the test calls `precheck_spec()` rather than re-deriving the one-match rule | " | AC-5.4 |
| deliberately drifting one committed anchor fails the test | " | AC-5.5 |
| unparseable JSON reported by name, not counted as drift | " | AC-6.2 |
| skipped and unclassifiable files are always named in output | " | AC-6.4 |
| every `.json` currently committed carries a `mutations` key | " | AC-6.5 |
| classification corpus, intended softenings enumerated and counted | " | AC-6.1, AC-6.3, AC-6.6 |
| no existing consumer of the `MUTATION:` token matches the new word | " | AC-4.3 |
| SKILL.md §Phase-5e says the run sweeps, not that the operator should | " | AC-7.1 |
| SKILL.md documents that a relative spec `root` is spec-relative | " | AC-7.3 |
| SKILL.md registry entry and recovery table carry the new verdict | `test_h_mad_mutation_harness.py` | AC-7.2, AC-7.4, AC-7.5 |

Commands: `/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -v --tb=short` and the same for
`handoff/tests/`, both from the repository root. Then
`h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json` expecting
`ANCHORS_OK specs=16 mutations=213`.

## Invariant Compliance

**Base layer.**

- *Audit-gate signal discipline* — complies: the new verdict exits 2 because it measured nothing,
  matching `REFUSED`/`UNREADABLE`; verdicts that did measure keep exit 0.
- *Single-source contract* — complies: `_resolve_root` and `precheck_spec` each exist once and are
  called by every path, including the new test. This is the invariant the design is built around.
- *Standalone / no plugin dependency*, *No new external dependency* — complies: stdlib only, no new
  imports, git untouched (still zero calls).
- *Portable time bounds* — not engaged; no new time-bounded command.
- *Doc-template superset compliance* — complies; verified by `h_mad_doc_shape_check.py`.
- *Operator-override preservation* — complies: nothing overridable is removed. No suppression flag
  is added, deliberately.
- *Backward compatibility* — complies, and is the reason for sibling-only scoping. No verdict that
  exists today becomes unreachable, and the eleven `REFUSED` tests stay green unchanged.
- *Marker discipline* — complies: `[H-MAD]` on the new verdict.
- *Mutation verification* — the new guards get mutation coverage, and `mutation_harness.json` is
  re-anchored in the same commit that changes the summary line it anchors on (AC-4.5).
- *Test discrimination* — each new guard is mutated to its permissive value and a named test must
  fail; AC-5.5 is the discrimination check for the suite assertion.
- *Verifying a review finding* — applied during Phase 3: two audit premises were checked against
  source before acting, and F13/F14 came from checking invariants against the spec.
- *Guard narrowing* — engaged by FR-6 and satisfied by AC-6.6's differential corpus. The relaxation
  rests on the loader's own necessary condition, verified against `_load_spec` rather than its
  documentation.
- *Connection enforcement* — engaged: the precheck is a connection from `run_spec` to
  `precheck_spec`. The wire test is AC-3.1 — remove the call alone, leaving `precheck_spec` intact,
  and the clean-spec-beside-drifted-sibling case stops refusing.
- *Assumption verification* — applied: the loader's requirements, the absoluteness of all existing
  roots, and the resolution behaviour were each read from source or measured, not assumed.
- *Regression provenance* — pre-committed: the eleven `REFUSED` tests are expected green unchanged;
  a failure means the scope is wrong, not that the test needs updating.
- *Both halves of a doc change* — FR-7 pairs the SKILL.md text with the registry entry, the recovery
  row, and a doc test.
- *Reimplementation parity* — not engaged; nothing is reimplemented.
- *Incident replay*, *Wrapper–runtime reconciliation* — not engaged.

**Domain layer.**

- *Skill self-containment* — complies, and this design **repairs** an existing violation. Every
  committed spec currently hardcodes an absolute path naming one machine's checkout, so neither
  skill is runnable from a bare clone; AC-2.6 additionally ensures handoff's spec resolves within
  its own skill rather than at the repository root.
- *Skill manifest integrity* — complies: no skill's entry behaviour or frontmatter changes.

## Version History

- v1.0: Initial design draft. Records the sibling-only scoping decision and why whole-directory
  scoping would have made `REFUSED` unreachable and broken eleven existing tests.
