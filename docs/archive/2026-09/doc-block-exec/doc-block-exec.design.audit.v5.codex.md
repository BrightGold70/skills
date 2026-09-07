## Summary
Axis C reconciliation finds every one of the 43 specified acceptance criteria semantically implemented as written; no criterion is restated or absent. The design still leaves an unsafe ordinal path, unverified cleanup, timeout-race error handling, and four acceptance criteria without planned automated enforcement.

| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-3.8 | implemented-as-written |
| AC-3.9 | implemented-as-written |
| AC-3.10 | implemented-as-written |
| AC-3.11 | implemented-as-written |
| AC-3.12 | implemented-as-written |
| AC-3.13 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix
- Zero and negative ordinal handling is unspecified — the design calls `index` 1-based but only defines not-found for an index past the end. A conventional `blocks[index - 1]` implementation turns `--index 0` into the final tagged block and negative values into other unintended blocks, violating the unambiguous address/security boundary. Define validation and its mapped refusal, then test 0 and a negative ordinal.
- Cleanup is deliberately unverified — `shutil.rmtree(cwd, ignore_errors=True)` suppresses deletion failures and performs no read-back. This breaches the base mutation-verification invariant and can report a completed run while retaining its supposedly disposable cwd; remove the silent suppression or handle it, re-check that the directory is absent, and surface a genuine cleanup operational error.
- The timeout path has unhandled races — `os.killpg(proc.pid, SIGKILL)` can raise `ProcessLookupError` if the group exits between `TimeoutExpired` and the kill, and the stated second bounded `communicate` has no action if it itself times out. Either case escapes the declared `BlockTimeout` to a traceback instead of the required `DOCBLOCK: TIMEOUT`, despite FR-5 requiring every run be bounded; specify the races, final pipe/cleanup behavior, and tests that exercise them.
- The Test Plan omits planned enforcement for AC-1.7 and AC-3.11 through AC-3.13 — its scanner row names AC-1.1–1.6 and AC-1.8, while its execution row stops at AC-3.9. There is no stated test for duplicate-heading refusal, the preamble failure/unreadable-file contract, or `mkdtemp` mode plus no-`mktemp` invocation, leaving the specs promise that every AC pass an automated test unenforced.

## Should-fix
- The authoritative-bounder import is not executable as designed — `h-mad/tests/docsections.py` currently imports from the tests directory, while the new authoritative module is under `h-mad/scripts/`; a direct import will fail when `test_docsections.py` is collected alone because it does not add `scripts` to `sys.path`. State the exact intra-skill import/loading arrangement and add an isolated collection/import test, rather than relying on another test modules path side effect.

## Nit
None
