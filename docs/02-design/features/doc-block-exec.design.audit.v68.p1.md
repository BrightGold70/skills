## Summary
The `# Design: doc-block-exec` document is highly detailed, internally consistent, and its implementation plan maps cleanly to the current constraints of the `h-mad` repository. The function signatures in the plan are type-consistent with their descriptions, and exact file paths for new and modified components are provided without vague placeholders. The design accurately cites the current repository state (e.g., the text scan at `:412`, the regex vulnerability at `:270` in `test_h_mad_collect_report_docs.py`, and the four-backtick logic gap in `docsections.py`). 

## Must-fix
- The test suite floor assertion in Task 5 (`asserts collected >= 2747...`) uses a stale baseline count of `2747`. A fresh `pytest --collect-only -q` run inside `h-mad` currently collects exactly `2485` tests. The assertion number must be verified and updated to match the exact post-Task-5 baseline to prevent the test from failing when it lands.

## Should-fix
None

## Nit
None
