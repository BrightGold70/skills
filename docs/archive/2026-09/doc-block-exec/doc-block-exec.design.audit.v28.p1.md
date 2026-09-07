## Summary
The impl-plan audit reveals a missing function in the implementation order that breaks type consistency across tasks, as `select` is needed to bridge the candidate list from `extract` to the single block required by `substitute`. Additionally, the tasks violate the exact file paths requirement by omitting directories for several mutated files and referencing line numbers without the accompanying file path.

## Must-fix
- Missing `select` function in Implementation Order — `extract` returns a `list[Block]` but `substitute` and `run_block` require a single `Block`; omitting `select` from the tasks breaks type consistency and leaves `main` with no specified way to validate ordinals or resolve the list.
- Inexact file paths in Implementation Order — Task 1 refers to `docsections.json` instead of `h-mad/tests/mutation-specs/docsections.json` (and omits paths for the new helper/test files); Task 4 refers to `SKILL.md` instead of `h-mad/SKILL.md`; Task 5 migrates line `:270` without naming `h-mad/tests/test_h_mad_collect_report_docs.py` or the gate fence's document, violating the exact file paths rule.

## Should-fix
- Missing `RunResult` dataclass in Implementation Order — Task 3 covers `run_block` but omits the `RunResult` dataclass it returns, whereas Task 1 explicitly names the `Block` dataclass.

## Nit
None
