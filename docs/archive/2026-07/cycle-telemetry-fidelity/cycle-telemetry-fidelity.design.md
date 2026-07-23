# Design: cycle-telemetry-fidelity

## Executive Summary

A new stdlib-only `h_mad_cycle_counts.py` owns all parsing of `v<N>` artifact filenames and
exposes both cycle counts plus the latest-audit lookup that `h_mad_do_preconditions.py` currently
re-implements; `h_mad_telemetry.py` calls it at record and summary time, and Phase 6/6b are
changed to version the analysis artifact.

## Overview

The design intent is to make the counters read from evidence rather than from bookkeeping. The
binding constraint is the base invariant on single-source contracts: the "highest `v<N>` for this
feature and phase" rule is about to have two implementations, and one of them
(`h_mad_do_preconditions._latest_audit`) already exists. The key decision is therefore that the
new module owns discovery and version parsing for *both* consumers, with an explicit scope
parameter, because the two consumers legitimately need different scopes.

## Architecture Overview

```
                       h_mad_cycle_counts.py          <-- new; owns v<N> parsing
                       ┌──────────────────────────┐
                       │ audit_artifacts()        │
                       │ latest_audit_path()      │
                       │ audit_cycles()           │
                       │ iterate_cycles()         │
                       └──────────┬───────────────┘
             ┌────────────────────┼─────────────────────┐
             │                    │                     │
   h_mad_telemetry.py    h_mad_telemetry.py     h_mad_do_preconditions.py
     cmd_record()          cmd_summary()            _latest_audit()
   scope=live+archive    scope=live+archive        scope=live ONLY
```

`h_mad_phase7_preconditions.py` is untouched and keeps reading the unversioned
`docs/03-analysis/<feature>.analysis.md`.

## Detailed Design

### Artifact discovery

Two artifact families, one shape (`<stem>.v<N>.md`):

| Family | Stem | Searched in |
|---|---|---|
| audit | `<feature>.<phase-seg>.audit` | `docs/01-plan/features/`, `docs/02-design/features/`, `docs/archive/*/<feature>/` |
| analysis | `<feature>.analysis` | `docs/03-analysis/`, `docs/archive/*/<feature>/` |

`phase-seg` maps `plan → plan`, `design → design`, `impl_plan → impl-plan`. The returned dict
keys use the underscore form, matching the existing telemetry row shape.

Discovery uses `Path.glob` with the literal stem, so separator anchoring is by construction — the
pattern `feat.plan.audit.v*.md` cannot match `feat-ab.plan.audit.v1.md` because the character
after `feat` must be `.` (AC-7.1). This is the existing `_latest_audit` behaviour, preserved
deliberately rather than re-derived.

**Case sensitivity is enforced in code, not delegated to the glob.** The default macOS filesystem
(APFS, and HFS+ before it) is case-**insensitive**, so `Path.glob("feat.plan.audit.v*.md")`
matches `Feat.plan.audit.v1.md` on the very machine this runs on; Linux ext4 would not. Relying on
glob semantics would therefore make AC-7.4 pass or fail by platform. Every candidate returned by
the glob is re-checked with an exact, case-sensitive string comparison on `Path.name`:

```python
prefix = f"{feature}."
candidates = [p for p in root.glob(pattern) if p.name.startswith(prefix)]
```

`str.startswith` is case-sensitive in Python regardless of filesystem, so `Feat` and `feat` are
distinct (AC-7.4) and the behaviour is identical across platforms.

`docs/templates/` is excluded by never being one of the searched roots (AC-7.2) — an exclusion by
construction rather than a filter that a later reader could delete as redundant.

### Version parsing and the count rule

One regex, `_VERSION_RE = re.compile(r"\.v(\d+)\.md$")`, applied to `Path.name`. A file whose
name does not match contributes nothing and does not raise (AC-7.3).

- `audit_cycles(docs_root, feature) -> {"plan": int, "design": int, "impl_plan": int}` —
  `max(N)` per phase, `0` when the phase has no artifacts (AC-1.1, AC-1.2, AC-1.4).
  `max` rather than `len` so a numbering gap reports the cycle actually reached (AC-1.3) — the
  archived `orca-git-native-checkpoints-and-merge-gate` has `design.audit.v2.md` with no `v1`
  and must report `2`.
- `iterate_cycles(docs_root, feature) -> int` — `max(0, max(N) - 1)` over analysis artifacts, `0`
  when none exist (AC-3.1, AC-3.2, AC-3.3). The unversioned `<feature>.analysis.md` has no `v<N>`
  segment, so it is skipped by the same regex that ignores any other non-matching name (AC-3.4).

`max(N) - 1` encodes that the first analysis is the Phase 6 measurement, not an iterate cycle.
Floored at 0 so a future `analysis.v0.md`, or any unexpected numbering, cannot produce a negative
count.

**The count functions are not sufficient for the fallback rule, so discovery is public too.**
`iterate_cycles` returns `0` both when a feature has no analysis artifacts at all and when it has
exactly `analysis.v1.md` (a real Phase 6 measurement with zero iterate cycles). AC-5.2 must
distinguish those: the first falls back to the stored row value, the second must display a
derived `0`. A caller cannot tell them apart from an `int`, and re-globbing in the caller to find
out would violate the single-source rule (AC-1.5).

`audit_artifacts()` and `analysis_artifacts()` are therefore part of the public surface, each
returning `dict[int, Path]`. Emptiness of that mapping — not the value of the count — is the
fallback trigger. The count functions are thin wrappers over them, so there is still exactly one
discovery implementation.

### Scope, and why it is a parameter

`audit_artifacts(..., include_archive: bool)` exists because the two callers need opposite
answers, and defaulting either way silently breaks the other:

- **Telemetry** must include the archive. Every shipped feature lives there, and excluding it
  under-counts precisely the features worth measuring (AC-6.2, AC-6.3).
- **`h_mad_do_preconditions`** must NOT. It gates `/h-mad do` on a *live* audited plan and design;
  if it began accepting archived audits, a previously-shipped feature's artifacts could satisfy
  the precondition for new work on the same name. That is a behaviour change disguised as a
  refactor, and the invariant asks for one implementation — not one behaviour.

So `_latest_audit` delegates to `latest_audit_path(..., include_archive=False)` and keeps its
current semantics exactly. Its existing tests are the regression gate for that claim.

### Telemetry integration

`cmd_record` replaces its two `feat_state.get(...)` reads with calls to the module. The state
record is still required for `started_ts`, `last_completed_phase`, and `halt_reason`, so the
existing exit codes 2 (feature absent) and 3 (state missing/malformed) are reached by the same
paths and in the same order as today (AC-4.3).

`cmd_summary` computes counts per displayed row, then applies the fallback rule: **if
`audit_artifacts()` / `analysis_artifacts()` returns an empty mapping for that family, the stored
row value for that family is used** (AC-5.2). Emptiness of the mapping is the trigger, not a
count of zero — a real feature with genuinely zero iterate cycles derives 0 from an existing
`analysis.v1.md` and must display 0, not fall back. The two families are tested for emptiness and
fall back independently.

The drift warnings are computed from the displayed values (AC-5.4), which requires deriving
before the warning loop rather than inside the print loop.

### Docs-root resolution

`--docs-root` defaults to the parent of the `--state` file's directory when that directory is
named `docs`, else to `Path("docs")` relative to cwd. The documented invocation in SKILL.md
§Telemetry passes `--state docs/.bkit-memory.json`, which resolves to `docs/` — so the existing
command keeps working with no edit (AC-4.2, AC-5.5).

### Phase 6 / 6b protocol change (FR-2)

Two edits to `h-mad/references/inline-protocols.md`, both in prose steps outside the fenced
template blocks. The fenced `# Analysis: <feature>` template and its headings are untouched, which
is what keeps `test_h_mad_doc_templates.py` green.

**§Phase 6, step 6** — currently `6. Save to docs/03-analysis/<feature>.analysis.md.` Replaced by
(AC-2.1, AC-2.3):

> 6. Save the analysis to **both** paths:
>    - `docs/03-analysis/<feature>.analysis.v1.md` — the per-cycle artifact. This is the first
>      measurement; Phase 6b adds `v2`, `v3`, … one per iterate cycle.
>    - `docs/03-analysis/<feature>.analysis.md` — the same content, unversioned. This path must
>      always hold the **latest** cycle's content, because `h_mad_phase7_preconditions.py` reads
>      it to parse the match rate and takes the *first* rate it finds in the file. A stale copy
>      here gates Phase 7 on an old measurement.

**§Phase 6b, step 3** — currently `3. Re-run full gap analysis (Phase 6 steps 1–7).` Replaced by
(AC-2.2, AC-2.3):

> 3. Re-run the full gap analysis (Phase 6 steps 1–7). Write it to the next unused
>    `docs/03-analysis/<feature>.analysis.v<N>.md` — never overwrite a previous cycle's file —
>    and refresh the unversioned `docs/03-analysis/<feature>.analysis.md` with the same content
>    so it continues to hold the latest cycle.

**§Phase 6b, new closing note** (AC-2.4):

> **Why the per-cycle files matter.** `iterate_cycles` in the Phase 7 telemetry row is derived by
> `h_mad_cycle_counts.py` as `max(N) - 1` over these `analysis.v<N>.md` files — there is no
> counter. Overwriting one file instead of adding the next `v<N>` silently reports a multi-cycle
> Phase 6 as zero iterate cycles, and erases the record of what each cycle measured.

AC-2.4 is satisfied by that note being adjacent to the instruction it protects, so an editor
tempted to simplify the write step sees what depends on it without leaving the page.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| Cycle-count derivation | `h-mad/scripts/h_mad_cycle_counts.py` | new | Single source for `v<N>` discovery, parsing, and both counts |
| Telemetry record | `h-mad/scripts/h_mad_telemetry.py` | modify | Derive counts; add `--docs-root` |
| Telemetry summary | `h-mad/scripts/h_mad_telemetry.py` | modify | Recompute on read with per-family fallback; add `--docs-root` |
| Do-preconditions | `h-mad/scripts/h_mad_do_preconditions.py` | modify | Delegate `_latest_audit`; behaviour unchanged |
| Phase 6 / 6b protocol | `h-mad/references/inline-protocols.md` | modify | Version the analysis artifact |
| SKILL.md §Telemetry | `h-mad/SKILL.md` | modify | State that counts are derived; document `--docs-root` |
| Derivation tests | `h-mad/tests/test_h_mad_cycle_counts.py` | new | FR-1, FR-3, FR-6, FR-7 |
| Telemetry tests | `h-mad/tests/test_h_mad_telemetry.py` | new | FR-4, FR-5 |
| Protocol doc-contract tests | `h-mad/tests/test_h_mad_analysis_versioning_docs.py` | new | FR-2 |

## Implementation Order

1. `h_mad_cycle_counts.py` + `test_h_mad_cycle_counts.py` — no dependants yet, so it lands
   independently.
2. `h_mad_telemetry.py` record + summary + `test_h_mad_telemetry.py` — depends on 1.
3. `h_mad_do_preconditions.py` delegation — depends on 1; verified by the *existing*
   `test_h_mad_do_preconditions` / `test_h_mad_preconditions_shared` tests staying green.
4. `inline-protocols.md` §Phase 6 + §Phase 6b — independent of 1–3; run
   `test_h_mad_doc_templates.py` before and after.
5. `SKILL.md` §Telemetry — documentation, last.

Steps 1–3 and step 4 touch disjoint files and have no ordering dependency between them.

## Data Model / Schema Changes

None to `h_mad_state_schema.json`: `audit_cycles` and `iterate_cycles` remain in the state schema
and are simply no longer telemetry's source of truth.

Telemetry row shape is unchanged — same keys, same types, `schema_version` stays `1`. Only the
provenance of two values changes, so old and new rows remain mutually readable.

New on-disk artifact: `docs/03-analysis/<feature>.analysis.v<N>.md`, same content shape as the
existing unversioned analysis document.

## API / Interface Changes

New module:

```python
audit_artifacts(docs_root: Path, feature: str, phase: str, *, include_archive: bool = True) -> dict[int, Path]
analysis_artifacts(docs_root: Path, feature: str, *, include_archive: bool = True) -> dict[int, Path]
latest_audit_path(docs_root: Path, feature: str, phase: str, *, include_archive: bool = True) -> Path | None
audit_cycles(docs_root: Path, feature: str) -> dict[str, int]
iterate_cycles(docs_root: Path, feature: str) -> int
```

The two `*_artifacts` functions are public because `cmd_summary` needs to distinguish "no
artifacts" from "zero cycles" to apply AC-5.2; see §Version parsing and the count rule.

CLI additions, both optional with a derived default:

```
h_mad_telemetry.py record  [--docs-root PATH]
h_mad_telemetry.py summary [--docs-root PATH]
```

No removals, no changed defaults, no changed exit codes.

## Error Handling Strategy

Derivation is total: it returns counts, never raises for missing directories, unreadable names,
or absent features. A missing docs root yields zeros, which the summary fallback then converts
into the stored values.

This is deliberate. Telemetry is explicitly non-fatal in SKILL.md ("if record fails, emit warning
and continue to report"), so a derivation error must not become the thing that blocks a Phase 7
closure. Exit codes stay exactly as documented: `0` success, `2` feature not in state, `3` state
file missing or malformed — all operational conditions, consistent with the audit-gate signal
discipline invariant.

`OSError` from a glob on an unreadable directory is caught per-root and treated as "no artifacts
here", so one bad path cannot mask counts found under the others.

## Test Strategy

Unit tests against a `tmp_path` docs tree — the module takes a root as a parameter precisely so
no mocking is needed. Boundary: the filesystem, constructed directly.

Telemetry tests drive `main()` with argv and assert on stdout plus the bytes of the telemetry
file, rather than importing internals, so the CLI contract is what is pinned.

Two tests deliberately use **real repository data** rather than fixtures, per the
`replay-the-incident-against-the-fix` discipline: fixtures encode what I expect the tree to look
like, and the defect being fixed is a wrong belief about the tree.

## Test Plan

`h-mad/tests/test_h_mad_cycle_counts.py`:
- `test_audit_cycles_takes_max_per_phase` — v1+v2 → 2 (AC-1.1)
- `test_absent_phase_counts_zero` (AC-1.2)
- `test_numbering_gap_reports_highest` — v1, v3 → 3 (AC-1.3)
- `test_plan_and_impl_plan_counted_separately` (AC-1.4)
- `test_iterate_cycles_is_max_minus_one` (AC-3.1, AC-3.2)
- `test_no_versioned_analysis_yields_zero` (AC-3.3)
- `test_unversioned_analysis_is_not_a_cycle` (AC-3.4)
- `test_archive_artifacts_are_found` (AC-6.2)
- `test_highest_across_live_and_archive_wins` (AC-6.3)
- `test_prefix_sibling_feature_does_not_match` — `feat` vs `feat-ab` (AC-7.1)
- `test_templates_dir_is_not_searched` — literal `audit-example.audit.v1.md` (AC-7.2)
- `test_unparseable_version_is_ignored` (AC-7.3)
- `test_feature_match_is_case_sensitive` (AC-7.4) — writes `Feat.plan.audit.v1.md` and asserts
  feature `feat` derives 0. On macOS this fails against a glob-only implementation, which is the
  point of the test.
- `test_analysis_artifacts_empty_vs_zero_cycles` — `{}` for no files, `{1: path}` for
  `analysis.v1.md`; both yield `iterate_cycles == 0`, and the mapping is what distinguishes them
  (supports AC-5.2)
- `test_module_imports_without_jsonschema` — stdlib-only guard
- `test_real_archive_counts_match_known_values` — **live data**: the three archived features from
  the plan's table, asserted exactly

`h-mad/tests/test_h_mad_analysis_versioning_docs.py` (FR-2, doc-contract — same pattern as the
existing `test_h_mad_substrate_docs.py`):
- `test_phase6_instructs_both_paths` (AC-2.1)
- `test_phase6b_instructs_next_version_and_refresh` (AC-2.2)
- `test_protocol_states_unversioned_is_latest_for_phase7` (AC-2.3)
- `test_protocol_names_iterate_cycles_dependency` (AC-2.4)

`h-mad/tests/test_h_mad_telemetry.py`:
- `test_record_writes_derived_counts_over_zero_state` (AC-4.1)
- `test_record_docs_root_defaults_from_state_path` (AC-4.2)
- `test_record_exit_2_feature_absent` / `test_record_exit_3_state_missing` (AC-4.3)
- `test_record_no_artifacts_writes_zeros` (AC-4.4)
- `test_summary_displays_derived_counts_for_zero_row` (AC-5.1)
- `test_summary_falls_back_to_stored_when_no_artifacts` (AC-5.2)
- `test_summary_does_not_modify_telemetry_file` — byte comparison (AC-5.3)
- `test_summary_drift_warning_fires_on_derived_counts` (AC-5.4) — *the test that would have
  caught the original defect*
- `test_summary_accepts_docs_root` (AC-5.5)

`h-mad/tests/test_h_mad_doc_templates.py` — existing, must stay green (FR-2 regression gate).
Existing `do_preconditions` tests — must stay green (delegation regression gate).

Verification: `/opt/anaconda3/bin/python3 -m pytest h-mad/tests/ -q` → 454 pre-existing + new,
0 failures. Plus `python3 h-mad/scripts/h_mad_telemetry.py summary` under **bare** `python3` on
the real repo, showing non-zero audit cycles for a historical feature.

## Invariant Compliance

**Base — audit-gate signal discipline**: complies. Telemetry is not a gate; its exit codes remain
0 for success and 2/3 for operational errors only. No verdict is communicated by exit status.

**Base — single-source contract**: complies, and improves the status quo. The `v<N>` rule
currently has one implementation in `h_mad_do_preconditions._latest_audit` and was about to gain
a second; instead the new module is the sole implementation and `_latest_audit` delegates to it.
AC-1.5 states this as a testable requirement.

**Base — standalone / no plugin dependency**: complies. No plugin or external skill is imported.

**Base — no new external dependency**: complies, strictly. Stdlib `pathlib` + `re` only;
specifically **not** `jsonschema`, so telemetry keeps running under the default `python3` that
the state scripts cannot (F8).

**Base — doc-template superset compliance**: this is the rule FR-2 puts at risk.
`test_h_mad_doc_templates.py` extracts §Phase 6's fenced template block and validates its
headings. The design change adds a *save-path instruction* in the protocol prose (step 6),
leaving the fenced analysis template block and its headings untouched. Step 4 of the
Implementation Order runs that test before and after the edit to prove it.

**Base — operator-override preservation**: complies; the gate and its `## Acknowledged-not-fixed`
sidecar are untouched.

**Base — backward compatibility**: complies. No audit-gate change. Telemetry keeps its flags,
defaults, exit codes, row shape, and `schema_version`; `--docs-root` is additive with a default
that reproduces today's behaviour; existing rows stay readable and are never rewritten.

**Base — marker discipline**: complies. No new phase transition or halt is introduced, so no new
`[H-MAD]` marker is required; existing markers are unchanged.

**Project — skill self-containment**: complies. The new module sits in `h-mad/scripts/` and is
imported by siblings via the established bare-import convention (`from h_mad_audit_gate import
classify` in `h_mad_do_preconditions.py`). No cross-skill import, no path outside the skill dir.

**Project — skill manifest integrity**: `record`'s observable behaviour changes (counts now
derived), so SKILL.md §Telemetry is updated in the same feature to state it and to document
`--docs-root`. Implementation Order step 5.

## Version History
- v1.0: Initial design draft.
- v1.1: Addressed the three Must-fix items from `.design.audit.v1.md`. (a) AC-2.1–2.4 were absent
  — added §"Phase 6 / 6b protocol change (FR-2)" specifying the verbatim replacement prose for
  §Phase 6 step 6 and §Phase 6b step 3 plus the closing dependency note, and a doc-contract test
  file. (b) AC-7.4 was narrowed to "case sensitivity follows the glob" — macOS APFS is
  case-insensitive, so that delegated the requirement to the platform; case sensitivity is now
  enforced in code via a `str.startswith` re-check, with a test that fails a glob-only
  implementation on this machine. (c) `iterate_cycles() -> int` could not distinguish "no
  artifacts" from "zero cycles", making AC-5.2's fallback unimplementable without re-globbing in
  the caller — `audit_artifacts()` and `analysis_artifacts()` are now public, mapping-emptiness is
  the fallback trigger, and the count functions are thin wrappers so discovery stays single-source.
