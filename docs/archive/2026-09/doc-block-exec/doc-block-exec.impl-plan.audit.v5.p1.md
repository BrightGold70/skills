## Summary
The implementation plan is exceptionally thorough, robust, and well-reasoned, exhibiting flawless type consistency across tasks and meticulously defining every test and mutation row. The design's complex control flows, such as the stream reservation alias check and timeout precedence, are perfectly translated into the code structure and test specs. There are no missing file paths, TBDs, or vague requirements.

## Must-fix
None

## Should-fix
None

## Nit
- `_verify` function signature — The function `def _verify(path: str, text: str) -> bool:` appears in Task 4's code structure but is not explicitly named in the prose (which instead describes the read-back logic inline).
- `shlex` import in Task 5 — The delta for `test_h_mad_collect_report_docs.py` uses `shlex.quote(str(gate))` but does not explicitly show an `import shlex`, though it may already be present in the file.
