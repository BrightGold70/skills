## Summary
The implementation plan accurately translates the design's detailed requirements and tests, but it introduces a structural flaw by splitting the scanner implementation and `docsections` delegation into two separate tasks. This violates the Single-source contract at the intermediate commit. Additionally, Task 6 contains explicit TBD placeholders in its code and description that must be resolved.

## Must-fix
- The plan splits the scanner (Task 1) and `docsections` delegation (Task 2) into separate tasks — This directly contradicts the design's Implementation Order ("In the same task") and violates the Single-source contract invariant by creating an intermediate commit where two separate bounder implementations exist. They must be merged into a single Task 1.
- TBD placeholders in Task 6 — The description uses `<the fixture preamble...>` and the code block contains `timeout=...` in the `run_block` call. These are vague requirements and syntactically invalid placeholders; the plan must specify `preamble=preamble` and define an exact timeout value (or omit the kwarg to use the default).

## Should-fix
- `__all__` is missing the exception classes — Task 1's code structure defines `__all__` but omits `DocBlockError` and its subclasses. Because these exceptions are part of the public API contract that callers must catch, they should be exported in `__all__`.

## Nit
- Missing `subprocess.` prefix for `PIPE` — In Task 4's description of the `Popen` call, `stdout=PIPE, stderr=PIPE` is used, but only `subprocess` is imported. It should read `stdout=subprocess.PIPE, stderr=subprocess.PIPE`.
- Missing type annotation for `handle` — In Task 5's code structure, `_final_write(handle, text: str)` and `_close_stream(handle)` omit the type annotation for `handle` (e.g., `io.TextIOWrapper`).
