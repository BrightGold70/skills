# Change review — working tree vs cdd36a6f (census-r1.diff: guard_census foreign-shebang + doc-named unreadable head) — GATING

## Evidence
- read: 4 files. I read the full diff (155 lines) and these spans of `h_mad_guard_census.py`: 125-160, 394-412, 483-495, 525-720. I also read the `make`/`census`/`spec` helpers in `test_h_mad_guard_census.py`.
- ran: 14 commands. The scratch tree is `git archive HEAD` plus `git apply` of the diff, and its census script is byte-identical to the working tree's.
- tests run: `h-mad/tests/test_h_mad_guard_census.py` (whole file, python3.11.8), with the result `132 passed, 4 skipped`. I did not run the mutation harness or the full suite.
- Probes run:
  - `_language` on 23 shebang variants, new code vs HEAD code.
  - CLI scenarios r1/r2/r3 on throwaway git repos.
  - The new census over its own diff.
  - Real-history census, new vs HEAD code, `--base` HEAD~10 / HEAD~50 / HEAD~200 / HEAD~600 / the root commit (3d9af666) with `--head HEAD`. The outputs were identical in all 5 ranges (`diff` empty; e.g. root: `decision=28991 … unmeasured=73`, the same on both sides).

## Must-fix
- **A `RecursionError` escapes the new pre-check, so the census crashes with a traceback and prints no token.** HEAD code printed `UNREADABLE` for the same input. The pre-check catches `(Unreadable, SyntaxError, ValueError)`, but `_python_decisions` (line 407) also catches `RecursionError` for the same `ast.parse`. Python 3.11 raises it for a long flat expression.
  - Scenario r1: `run.conf` = `#!/usr/bin/env python3\nx = 1+1+…` (200000 terms), plus a normal `b.py` change.
    - New code: `RecursionError: maximum recursion depth exceeded during ast construction`, rc=1, no `GUARD-CENSUS:` line.
    - HEAD code: `GUARD-CENSUS: UNREADABLE reason=unreadable-file`, rc=2.
    - The intended result is `UNMEASURED: run.conf` plus DONE.
  - So the change turns a fail-closed token into an unparseable crash, which is worse than both the old and the intended behaviour.
  - Fix: add `RecursionError` to the tuple, matching line 407. A second effect follows from Python 3.11's ast recursion limit, which I traced but did not probe. The limit depends on the current stack depth, so a source right at the limit can pass the shallow pre-check and then fail inside `_python_decisions`, a few frames deeper. That raise at line 408 is outside the try, so the census goes UNREADABLE. Line 408 is therefore still reachable for a doc-named head in that narrow case.
  quote: h-mad/scripts/h_mad_guard_census.py:629 › `except (Unreadable, SyntaxError, ValueError):`
  quote: h-mad/scripts/h_mad_guard_census.py:407 › `except (SyntaxError, ValueError, RecursionError) as exc:`

## Should-fix
- **The `continue` also drops a measurable BASE side, so guards it removed go uncounted.** Scenario r3: base `run.conf` = `#!/usr/bin/env python3\nif x:\n    raise SystemExit(1)\nassert y\n`, head = `#!/usr/bin/env python3\nif x\n`.
  - New code: `UNMEASURED: run.conf`, `GUARD-CENSUS: DONE … removed=0 unparsed_base=0`.
  - HEAD code: `UNREADABLE reason=unreadable-file`.
  - The file is still listed on `UNMEASURED:`, so it is not silent. But three base decisions (`if`, `raise`, `assert`) that the head no longer has as parseable code are not listed on `REMOVED:`. The neighbouring path does list them: when the head stops being code, all base decisions are counted (`if not e.h_kind: old_lines = set(range(…))`).
  - The more fail-closed option: keep the entry with `h_kind=None` and the base side, so `REMOVED:` lists every base decision and the file is also counted unmeasured. The docstring would then say "the head side is unmeasured" instead of "the whole entry".
  quote: h-mad/scripts/h_mad_guard_census.py:636 › `continue`
- **The new census leaves its own new guard lines unanchored.** Run over this diff, it reports `decision=14 anchored=2 unanchored=12`. Among the unanchored lines:
  - `:627` `if h_kind == "py" and _doc_named(ch.path):`, the pre-check gate.
  - `:629`, the except tuple.
  - `:634`/`:636` (`continue`).
  - `:553` `if _doc_named(path):`.

  For example, narrowing `:629` to `(Unreadable, SyntaxError)` would kill no row. My r1 scenario shows that this tuple's contents are exactly where the defect lives. Suggested rows:
  - `:627` → `if False:`: should be killed by `[py-unparsable]`, since `_python_decisions` then raises the UNREADABLE token.
  - `:636` `continue` deleted: should be killed by `[py-unparsable]` or `[sh-not-utf8]`.
  - A RecursionError fixture once the Must-fix lands.

  I did not run the harness (lock held), so whether these mutants are killed is my inference.
  quote: h-mad/scripts/h_mad_guard_census.py:627 › `if h_kind == "py" and _doc_named(ch.path):`
- **No test covers the `ValueError` arm or a null byte.** In Python 3.11.8, `ast.parse("x = 1\0\n")` raises `SyntaxError: source code string cannot contain null bytes`, not `ValueError`, so `ValueError` is dead on this interpreter. That is harmless, but it is untested. A NUL inside git's first 8000 bytes makes the diff binary, so only a late NUL reaches this code. I found nothing else that `ast.parse` raises: `MemoryError` from `-`×200000 is uncaught here AND at line 407. That is pre-existing, not introduced by this change, and not a gate for it.

## Nit
- **The `startswith(b"#!")` breadth, executed against both regexes on 23 variants.** No real sh/python shebang changed class:
  - These stay `py`/`sh` exactly as at HEAD: `#! /bin/sh`, `#!/usr/bin/env -S python3 -u`, `#!/usr/bin/python3.11`, `#!/usr/local/bin/python3.11 -I`, `#!python`, `#!/bin/dash`, and CRLF endings.
  - Only doc-named files that were `other` changed: `#!/usr/bin/perl`, `#!/usr/bin/pypy3`, `#!/usr/bin/env PYTHONPATH=. python3`, `#!/usr/bin/env -S uv run --script`, `#!/bin/mksh`, a bare `#!`, and `#!markdown note`. These now read `unmeasured`, which is the intended fail-closed result.
  - Over this repo's whole history no file changed classification (identical outputs, 5 ranges), so the false-unmeasured noise from a document that really begins with `#!` is zero here.
  - Residual: `\xef\xbb\xbf#!/bin/sh` and `  #!/bin/sh` under a doc name still read `other`. This is unchanged from HEAD, and a kernel will not exec either of them. It is worth one line in the docstring, or a `lstrip(b"\xef\xbb\xbf")` before the shebang tests.
- **The `ch.path not in unmeasured` check works, but its premise is misleading.** When the head is py/sh, `h_kind` is never `"unmeasured"`, so the path is already in the list only if the base side was unmeasured. A comment saying so would stop a reader assuming a double count is common.
