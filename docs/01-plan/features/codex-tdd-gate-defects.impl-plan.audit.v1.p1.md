## Summary
The implementation plan has three hard gaps in guard coverage and the judge interfaces. I checked the planned behavior against the binding design and spec, the current hooks and parser, and direct Bash controls for the path and output handling.
Evidence: 15 files opened, 11 greps run.
🌱 graft saved ~71,387 tokens (~$0.04) this turn, 1 call.

## Must-fix
- The DD-7 differential excludes roots beneath `tests/` or `fixtures/`, hiding another softened verdict: with an active root `/tmp/tests/repo`, positional `x.py` is gated by today's hook but the planned absolute `/tmp/tests/repo/x.py` matches `*/tests/*` and is allowed. This is a Phase-5 production-write bypass beyond the two published softenings; apply directory exemptions to the path below the project root and add both root shapes to the old/new corpus.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md › `The fixture root's own path holds no `tests` or `fixtures` segment (asserted).`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `DD-7 extends it to relative ones.`
- The Claude gate cannot enforce “exactly one line” with the planned command substitutions: Bash strips trailing newlines, so a valid ALLOW or `TDD-STATE: none` followed by a blank second line is accepted as one line. Preserve the raw output until after line-count validation and add a trailing-blank-line stub for both verbs; the current `two-lines` fixtures do not exercise this case.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md › `JOUT=$(python3 "$JUDGE" judge --root "$ROOT_ABS" --target "$TARGET_PATH" 2>/dev/null) || JRC=$?  # M:W2`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `the CLI has two verbs, and each prints exactly one line to stdout.`
- `_run_bounded` returns only `stdout + stderr`, but the binding resolver contract interprets only a non-empty **stdout** value as the name-map path. A stderr-only diagnostic would become a false candidate and `test-missing` instead of the required no-path outcome; return the streams separately and test a stderr-only name map through `NAME_MAP`.
  class: build
  quote: docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md › `(returncode, stdout + stderr, timed_out, start error)`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `A non-empty stdout resolves against `root`.`

## Should-fix
None

## Nit
None
