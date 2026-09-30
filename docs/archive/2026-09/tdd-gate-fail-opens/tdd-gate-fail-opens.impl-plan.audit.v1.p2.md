## Summary
The implementation plan accurately maps the design's structural constraints onto specific test assertions and gate wiring. However, it requires a Bash 4.3+ feature (`local -n`) that will crash the hook on macOS's default Bash 3.2, violates the skill self-containment invariant by hardcoding an absolute Python path in its mutation specs and test commands, and contains a contradiction where a test asserting exactly five options is expected to stay green when a sixth option is added.

## Must-fix
- The bash hook uses a nameref (`local -n`) for string capture, which requires Bash 4.3+, but macOS `/bin/bash` is Bash 3.2; this will cause an "invalid option" runtime fatal error when the gate runs. — a false premise about the platform
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `_pct_capture() { local -n _out=$1; local _v; _v=$(_pct_decode "$2"; printf '\001'); printf -v _out '%s' "${_v%$'\001'}"; }`

- The execution rules and mutation JSON files hardcode an absolute path to the Python interpreter (`/opt/anaconda3/bin/python`), violating the domain invariant forbidding hardcoded paths outside the skill's own directory (except for documented host install locations). — breaks invariant B (Skill self-containment)
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `Tests run under `/opt/anaconda3/bin/python`.`
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `["/opt/anaconda3/bin/python", "-m", "pytest", "tests/test_h_mad_target_identity.py", "tests/test_h_mad_tdd_gate_judge.py", "tests/test_h_mad_codex_tdd_gate_judge.py", "-q"]`

- Task 10b modifies the command-line parser to add a sixth option but claims the T10a tests stay green, which contradicts the T10a test that explicitly asserts the parser has exactly five options. — a contradiction inside the document
  class: build
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › ``test_build_parser_is_module_level`: `build_parser()` exists and its long options minus
  `--help` are exactly the five above.`
  quote: docs/01-plan/features/tdd-gate-fail-opens.impl-plan.md › `The T10a tests stay green.`

## Should-fix
None

## Nit
None
