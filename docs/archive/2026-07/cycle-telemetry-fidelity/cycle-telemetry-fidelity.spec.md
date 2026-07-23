# Spec: cycle-telemetry-fidelity

## Executive Summary

H-MAD's two cycle counters are derived from the versioned artifacts each cycle already leaves on
disk instead of from state fields nothing increments, and Phase 6b is changed to emit one
analysis artifact per iterate cycle so both counters are derivable by a single rule.

## Goal

Make `h_mad_telemetry.py` report the number of audit and iterate cycles a feature actually
consumed — for new runs and for every historical run — so the two drift warnings it already
implements can fire.

## Functional Requirements

### FR-1: Audit cycle counts are derived from audit artifacts

- **Description**: A new single-source function computes `audit_cycles` for a feature by finding
  `<feature>.<phase>.audit.v<N>.md` files and taking the highest `N` per phase. Phases are
  `plan`, `design`, `impl_plan` (file segment `impl-plan`). No state field is read for this
  value.
- **Acceptance Criteria**:
  - AC-1.1: Given `f.plan.audit.v1.md` and `f.plan.audit.v2.md`, the derived `plan` count is `2`.
  - AC-1.2: Given no audit files for a phase, that phase's derived count is `0`.
  - AC-1.3: Given a gap in numbering (`v1`, `v3`), the derived count is `3` — the highest cycle
    reached, not the number of surviving files.
  - AC-1.4: `plan` and `impl_plan` are counted separately: given `f.plan.audit.v2.md` and
    `f.impl-plan.audit.v1.md`, the result is `{plan: 2, design: 0, impl_plan: 1}`.
  - AC-1.5: The function is the only place cycle numbers are parsed from filenames; no caller
    re-implements the glob or the regex.

### FR-2: Phase 6b emits one analysis artifact per iterate cycle

- **Description**: `references/inline-protocols.md` §Phase 6 and §Phase 6b are changed so each
  gap-analysis pass writes `docs/03-analysis/<feature>.analysis.v<N>.md` (N starting at 1 for
  the initial Phase 6 analysis, incrementing once per Phase 6b iterate cycle) **in addition to**
  writing the same content to the unversioned `docs/03-analysis/<feature>.analysis.md`.
- **Acceptance Criteria**:
  - AC-2.1: §Phase 6 step 6 instructs writing both the versioned path (`v1`) and the
    unversioned path.
  - AC-2.2: §Phase 6b instructs writing the next `v<N>` on each re-analysis and refreshing the
    unversioned path to the same content.
  - AC-2.3: The protocol states explicitly that the unversioned path always holds the **latest**
    cycle's content, because `h_mad_phase7_preconditions.py` reads it for the match rate.
  - AC-2.4: The protocol text names the artifact as the source of the `iterate_cycles` count, so
    a future editor cannot remove it without seeing what depends on it.

### FR-3: Iterate cycle counts are derived from analysis artifacts

- **Description**: The same single-source module computes `iterate_cycles` as
  `max(N) - 1` over `<feature>.analysis.v<N>.md`, floored at `0` — the first analysis is the
  Phase 6 measurement, not an iterate cycle.
- **Acceptance Criteria**:
  - AC-3.1: Given only `f.analysis.v1.md`, `iterate_cycles` is `0`.
  - AC-3.2: Given `f.analysis.v1.md` through `f.analysis.v4.md`, `iterate_cycles` is `3`.
  - AC-3.3: Given no versioned analysis files at all (every feature shipped before this
    change), the derived value is `0` and the caller falls back per FR-5.
  - AC-3.4: An unversioned `f.analysis.md` alone does not count as a cycle.

### FR-4: `telemetry record` writes derived counts

- **Description**: `cmd_record` populates `audit_cycles` and `iterate_cycles` from FR-1/FR-3
  rather than from `feat_state`, so the appended row is correct at write time.
- **Acceptance Criteria**:
  - AC-4.1: With audit artifacts on disk and a state record whose `audit_cycles` is
    `{plan:0, design:0, impl_plan:0}`, the appended row carries the derived non-zero counts.
  - AC-4.2: The docs root used for derivation is configurable (`--docs-root`) and defaults to
    the `docs/` directory containing the `--state` file, so the existing invocation in
    SKILL.md §Telemetry keeps working unchanged.
  - AC-4.3: `record` still exits 2 when the feature is absent from state and 3 when the state
    file is missing or malformed — derivation does not change the existing exit contract.
  - AC-4.4: A feature with no artifacts on disk records zeros without raising.

### FR-5: `telemetry summary` backfills historical rows on read

- **Description**: `cmd_summary` recomputes both counters from disk for each row it displays.
  `.h-mad/telemetry.jsonl` is never rewritten.
- **Acceptance Criteria**:
  - AC-5.1: A row stored with `audit_cycles: {plan:0,...}` displays the derived counts when the
    artifacts exist on disk.
  - AC-5.2: When no artifacts are found for a feature, the row's **stored** values are displayed
    — a deleted or never-archived docs tree must not silently zero a real recorded number.
  - AC-5.3: The telemetry file's bytes are unchanged by any number of `summary` invocations.
  - AC-5.4: The two drift warnings are computed from the displayed (derived) values, so a
    feature with 4 plan audit cycles triggers `audit_cycles > 3`.
  - AC-5.5: `summary` accepts `--docs-root` with the same default rule as FR-4.

### FR-6: Archived and live features are both found

- **Description**: Derivation searches the live feature directories and the archive.
- **Acceptance Criteria**:
  - AC-6.1: Audit artifacts are found under `docs/01-plan/features/` and
    `docs/02-design/features/`.
  - AC-6.2: Audit and analysis artifacts are found under
    `docs/archive/<YYYY-MM>/<feature>/`.
  - AC-6.3: When a feature has artifacts in both a live directory and the archive, the highest
    `N` across both wins.
  - AC-6.4: Analysis artifacts are found under `docs/03-analysis/`.

### FR-7: Matching is anchored and excludes non-feature files

- **Description**: Filename matching anchors on the exact feature name and rejects files that
  merely contain it.
- **Acceptance Criteria**:
  - AC-7.1: Deriving counts for feature `feat` does not match `feat-ab.plan.audit.v9.md` — the
    prefix-collision defect fixed in `handoff_paths.py` by its `__` separator.
  - AC-7.2: Files under `docs/templates/` are excluded; specifically
    `docs/templates/audit-example.audit.v1.md` (a real file in the HemaSuite checkout, which
    additionally has no phase segment) contributes nothing to any feature's count.
  - AC-7.3: A filename with no parseable `v<N>` segment is ignored rather than raising.
  - AC-7.4: Matching is case-sensitive on the feature name, so `Feat` and `feat` are distinct.

## Non-Functional Requirements

- **Performance**: Derivation is a bounded directory scan per feature. `summary --limit 20`
  performs at most 20 feature scans; no requirement beyond "no perceptible delay on a repo with
  a few hundred archived docs".
- **Security**: N/A — read-only globbing within the project's own `docs/` tree.
- **Compatibility**:
  - `telemetry record`'s existing CLI contract (flags, exit codes 0/2/3) is preserved; the new
    `--docs-root` is optional with a derived default.
  - Rows already in `telemetry.jsonl` remain readable and are never modified.
  - `h_mad_phase7_preconditions.py` continues to read the unversioned
    `docs/03-analysis/<feature>.analysis.md` and must keep parsing a match rate from it.
  - Python stdlib only, consistent with the other h-mad scripts. **No `jsonschema` import** —
    derivation must run under the bare `python3` on PATH, unlike the state scripts (F8).

## Out-of-Scope

- Changing the `> 3` drift-warning thresholds. They are measured for the first time by this
  feature; retuning needs data this feature produces.
- Adding an `--increment` operation to `h_mad_state_write.py`. Explicitly rejected in the
  brainstorm; the state fields `audit_cycles` / `iterate_cycles` are left in place and simply
  stop being the source of truth for telemetry.
- Backfilling or rewriting `.h-mad/telemetry.jsonl`.
- Any HemaSuite change. HemaSuite benefits as a consumer with no edit to its tree.
- Resolving F8 (`jsonschema` absent from the default `python3`). Noted during Phase 1; a
  separate item.
- Retro-generating versioned analysis artifacts for already-shipped features. Their
  `iterate_cycles` stay 0 and fall back per AC-5.2.

## Assumptions

- Audit filenames continue to be produced by the orchestrator to the documented pattern
  `<feature>.<phase>.audit.v<N>.md`; they are machine-written, not hand-authored.
- A feature's docs live under one `docs/` root — the repo-canonical one, per the handoff
  skill's `git rev-parse --git-common-dir` resolution. Multi-worktree fragmentation of `docs/`
  is out of scope here.
- The archive layout `docs/archive/<YYYY-MM>/<feature>/` is stable; it is the layout every
  archived feature in both repos uses today.
- Phase 6 currently writes the unversioned analysis path, and no consumer other than
  `h_mad_phase7_preconditions.py` and human readers depends on it.

## Version History
- v1.0: Initial specification draft.
