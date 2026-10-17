# agy-coder-fallback — 5d Task 15 record

## D5d-6 · `census_doc_pins.py` FAIL is the Task-13 equivalence test, not a moved pin (2026-10-17)
- Codex GREEN returned `STATUS: BLOCKED` solely on `census_doc_pins.py` → `prompt distinct
  literals: actual=27 expected=23`, `test files: actual=9 expected=8`.
- The delta is exactly one file, `h-mad/tests/test_h_mad_new_caller_carveout_copies.py` (Task 13),
  contributing 4 literals: the FR-9 canonical block's sentences, now in the prompt by design.
  Codex's control (the probe over `git show HEAD:` prompt, i.e. before this Task's GREEN) gives
  the same 27/9, so this Task moved no pin. The probe's EXPECT is its 4e4b5ded reading; compare
  later re-runs (Task 18) against 27 literals / 9 files.
- Gates (outside sandbox): 541 passed across the new tests and every prompt doc-pin file
  (`test_h_mad_tdd_gate_docs.py`, label spelling, portable timeout, census pin files);
  `implementer_neutral_prompt.json` ALL_CAUGHT 4/4 (symbols = enclosing headings); revert probe
  (HEAD prompt) → 4 failed.
