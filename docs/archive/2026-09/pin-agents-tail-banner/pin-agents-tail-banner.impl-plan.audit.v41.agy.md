## Summary
The plan is highly rigorous and thoroughly traces and patches edge cases in bash pipeline handling and regex matching. However, two implementation details introduce self-falsifying assertions and environment-specific hardcodes that break the test suite and validation steps.

## Must-fix
- `test_tail_pass_call_form_is_source_pinned` always fails — The test asserts that `"if local tout=" not in flat`. However, the T3 code block adds an explanatory comment containing exactly `` `if local tout="$(...)"` ``. When the source is split by whitespace and joined by spaces, the literal substring `"if local tout="` is recreated, causing the test to fail against the correct implementation.
- AC-6.10 hardcodes an absolute user path — The bash command `bash -c 'python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py ...'` hardcodes `~/.claude/skills/`, which will fail on systems where the repository is located elsewhere. It must use the relative path `h-mad/scripts/h_mad_mutation_harness.py` like the rest of the verification commands.

## Should-fix
None

## Nit
None
