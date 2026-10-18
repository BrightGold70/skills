# Plan: backlog-row-cycle

**Status:** Draft, awaiting user approval. No code has been written.
**Written:** 2026-10-18. Source row: `docs/skill-candidates.md:2661` ("backlog-row TDD cycle driver", recurrence 10, verdict `yes`).

## Executive Summary

The 2026-10-18 session drove ten backlog rows through one hand-scripted chain (`redfull.sh`,
`cycle.sh`, `land.sh` in that session's scratchpad). Those scripts no longer exist anywhere.
This plan replaces them with a single committed driver, `h-mad/scripts/h_mad_backlog_cycle.py`.
The driver composes the tools that already exist and does not reimplement them. It closes the
two gaps the row names that are still open. The third gap (census `--apply` silently skipping
a row with an unescaped `|`) is already fixed: `apply_table` now refuses with
`APPLY: REFUSED reason=malformed-row`.

## The chain being replaced (from the row text)

spec file → Codex RED dispatch → orchestrator re-run of the RED split → commit RED → Codex GREEN
dispatch with mutation-row instructions → scoped re-run → `h_mad_doc_consumers.py --run` on changed
files → `h_mad_mutation_harness.py --isolate --sweep` on changed specs →
`skill_candidates_census.py --apply` LANDED line (pipes escaped) → commit + push.

## Existing components (reused as-is)

| Step | Tool | Already does |
|---|---|---|
| RED / GREEN dispatch + independent re-run | `h_mad_assemble_tdd.py --phase red\|green` | staging, agent dispatch, `--expect-fail/--expect-pass`, `--guard`, `--mutation-spec` |
| Doc consumers | `h_mad_doc_consumers.py --run` | `CONSUMERS-RUN` verdict; rc 2 + `UNREADABLE reason=unknown-docs no-documents` when given no docs |
| Mutation sweep | `h_mad_mutation_harness.py --sweep --isolate <spec>` | detached-worktree run, corpus summary |
| Census | `skill_candidates_census.py --apply <table.md> <store>` | inserts the status line, refuses malformed rows |

## Design

One script with three subcommands. Each one is re-runnable and prints one verdict token as its last line.

```
h_mad_backlog_cycle.py red   --row <name> --paths <test files...> [assemble_tdd passthrough]
h_mad_backlog_cycle.py green --row <name> --paths <impl/spec/doc files...> --mutation-spec <spec> [passthrough]
h_mad_backlog_cycle.py land  --row <name> --status "<LANDED text>" [--no-push]
```

The `--row` name is checked against `open_candidates()` before anything runs. A row name that
does not match exactly one open row is refused, using the same rule `apply_table` already applies.

### Gap 1 — GREEN not committed separately when cycles overlap

- Every commit the driver makes is **pathspec-scoped**: `git commit -m … -- <declared paths>`.
  It never runs `git add -A` and never commits the whole index.
- `red` commits only its declared test paths. `green` commits only its declared paths.
- **Refuse on overlap.** The driver writes the declared paths to
  `.h-mad/backlog-cycles/<row-slug>.json`, which is gitignored. Before committing, `green` refuses
  (`CYCLE: REFUSED reason=path-claimed-by=<other-row>`) if any declared path is also claimed by
  another cycle that is still active. `land` deletes the record.
- **Refuse on undeclared drift.** If a declared path is unchanged, the driver refuses
  (`reason=nothing-to-commit path=…`); it does not create an empty commit.

### Gap 3 — `CONSUMERS-RUN: UNREADABLE no-documents` read as a result

- `land` computes the changed documents itself: `git diff --name-only <red-commit>^..HEAD`,
  filtered with `h_mad_doc_consumers._is_document`.
- **No documents changed** → it prints `CONSUMERS: SKIPPED reason=no-documents` and does **not**
  call `--run`. That is a legitimate outcome for a code-only row, and it is named as a skip.
- **Documents changed** → it calls `--run`. Any `UNREADABLE` or a non-zero rc **halts** `land`
  before the census line or the push. It is never folded into success.

### `land` order (fail-closed; any non-zero rc stops)

1. doc consumers (or explicit SKIP)
2. mutation sweep `--isolate` on the specs this cycle changed (or explicit `SKIPPED reason=no-specs`)
3. write a one-row temp table, escaping `|` → `\|` in the status; run census `--apply`
4. scoped commit of `docs/skill-candidates.md`
5. `git push` unless `--no-push`. The push is plain: it never uses `--force`, and a rejected push is reported, not retried with a rebase.

## Files

| File | Change |
|---|---|
| `h-mad/scripts/h_mad_backlog_cycle.py` | new (~250 lines) |
| `h-mad/tests/test_h_mad_backlog_cycle.py` | new. Uses a temp git repo fixture and stubs `assemble_tdd`/the harness at the subprocess boundary |
| `h-mad/tests/mutation-specs/backlog_cycle.json` | new mutation spec |
| `h-mad/SKILL.md` | one row in the scripts table |
| `.gitignore` | `.h-mad/backlog-cycles/` (if `.h-mad/` is not already ignored) |
| `docs/skill-candidates.md:2661` | LANDED line, written by the new tool itself (dogfood) |

## Tests (RED first)

1. `red` commits only the declared test paths, while an unrelated dirty file stays dirty.
2. `green` refuses when a declared path is claimed by another active cycle.
3. `green` refuses `nothing-to-commit` on an unchanged declared path.
4. `land` with zero changed documents prints `CONSUMERS: SKIPPED reason=no-documents` and never invokes `--run`.
5. `land` halts before the census step when consumers return rc 2.
6. A `|` in `--status` reaches the store escaped, and census accepts it.
7. `--row` matching zero or two open rows is refused.
8. `--no-push` makes no push; the default path pushes without `--force`.

## Out of scope — found while planning, filed separately if wanted

- `skill_candidates_census.py --help` crashes with `FileNotFoundError: '--help'`. The argv parser
  treats it as a store path.
- `h_mad_mutation_harness.py:2300` emits `SyntaxWarning: 'return' in a 'finally' block`. A
  `return` inside `finally` swallows any in-flight exception, which is a possible silent-failure path.

## Risks

- **Overlap detection only sees cycles this driver started.** Hand edits are not tracked.
  Pathspec-scoped commits still keep them out of the commit.
- **Codex dispatch time stays the same.** The driver removes the glue work, not the wait.
