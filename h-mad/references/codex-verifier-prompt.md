# Codex/agy Verifier Prompt Template — /h-mad Phase 5e (anti-gaming verification)

> Used by `~/.claude/skills/h-mad/SKILL.md` Phase 5e, AFTER a GREEN dispatch and its
> spec-review, as the independent anti-gaming pass. Codex GREEN + agy spec-review say
> "the code was written and matches the spec"; this pass answers the different question
> **"are the tests real and does the source actually hold the properties the plan pins?"**
> — the axis a green suite and a `STATUS: DONE` cannot self-certify.
>
> The orchestrator stages this template at `/tmp/h_mad_<feature>_5e-verify_<N>.txt` with
> `<INLINE_*>` placeholders substituted, then dispatches it — **default `hmad-dispatch exec`**
> (headless, hard exit code, no scrape; monitor with `--log`), or the pane path via
> `hmad-dispatch send` for the iterative loop. Substrate-agnostic file-indirection; see
> `references/agent-substrate.md` (F-12 discipline preserved).

ROLE: /h-mad Phase 5e verification. The implementation for module `<INLINE_MODULE_NAME>`
of feature `<INLINE_FEATURE>` is **ALREADY COMPLETE in the working tree**. Do NOT rewrite
it. Verify it, run the suites, and report. Do not modify production code unless a stated
property below is actually false — if so, STOP and report rather than fixing.

## Context

Working directory: `<INLINE_REPO_ROOT>`.
Interpreter / run command: `<INLINE_TEST_COMMAND>` (e.g. `MPLBACKEND=Agg PYTHONPATH=. <interp> -m pytest`).
Module test file: `<INLINE_TEST_PATH>`.
Production file(s) under test: `<INLINE_PROD_PATHS>`.
Stated properties the plan pins (verify each against source): `<INLINE_PROPERTIES>`.
Full-suite reference number (pre-change baseline): `<INLINE_SUITE_REFERENCE>`.

## Do this, in order

1. **Run the module tests and report the count.** Run `<INLINE_TEST_COMMAND> <INLINE_TEST_PATH> -q`
   and quote the exact passed/failed number. Any failure here is a blocker — report it, do not fix.

2. **Anti-gaming audit of the module tests.** Report any test that CANNOT FAIL: an assertion true
   by construction, a mock asserted against itself, a test that never reaches the code path it
   names, or a sentinel / hollow assertion. Name the test and say why. If all N are discriminating,
   say so explicitly — that is the expected outcome, not a filler line.

3. **Confirm each stated property by reading the source, and quote the line for each.** For every
   property in `<INLINE_PROPERTIES>`, read the production file and quote the exact line (with number)
   that makes it true. A property you cannot ground in a quoted line is a FAILED property → STOP and
   report; do not paper over it.

4. **Confirm the full-suite result against the reference `<INLINE_SUITE_REFERENCE>`.** The orchestrator runs the full suite itself (`/h-mad` step 5f) and passes you the number — confirm it,
   do NOT re-run a multi-thousand-test suite inside this dispatch. (Dogfood finding 2026-07-29: a
   headless codex re-runs the full suite because the PTY shows only progress dots and no summary
   line, doubling wall-time until the watchdog kills it; and running it from an isolated worktree
   fails path-coupled tests. Neither is a real regression.) If — and only if — no orchestrator number
   was provided, run the full suite once with a summary-guaranteed invocation (`-q` redirected to a
   file you then read, never inferred from live PTY dots) and quote passed / skipped / failed. A
   number *higher* than the reference is fine (tests added); any FAILURE is a blocker — report it in
   full, do not repair and re-run silently.

## Cross-check — do not trust your own headline numbers

**Cross-check every count you report against a second, independent measurement** before you emit a
verdict. Exit code 0 and a `STATUS: DONE` line never mean the work is correct — the extractor
carries your token, it cannot judge truth, so a fabricated or miscounted number sails straight
through under a DONE. Re-derive each count a different way (e.g. `grep -c 'def test_'` vs the pytest
collected count; re-read the quoted source line) and reconcile any disagreement in the report rather
than picking one silently.

## Report format (REQUIRED — orchestrator parses the STATUS line)

Keep the report under ~30 lines: the module count; anti-gaming findings (or "all N discriminating");
one quoted source line per stated property; full-suite numbers vs the reference; any cross-check
discrepancy. Do NOT weaken, delete, or loosen any assertion; no skip/xfail. If a suite fails, report
it — do not repair and re-run silently.

End with exactly one line, nothing after it:

```
STATUS: DONE
```
or `STATUS: DONE_WITH_CONCERNS` (name at least one specific concern — a contentless one is rejected)
or `STATUS: BLOCKED` (a property was false, or a suite failed — give the specific blocker)
or `STATUS: NEEDS_CONTEXT` (a reference or path was missing).

## Report file (preferred delivery under Orca)

<REPORT_FILE_PATH>

If a path appears above, your **final two actions** are: (1) write your full report there — the same
`STATUS: <value>` line and summary; then (2) create the marker `<that-path>.done`. The coordinator
reads the file, not your terminal. If the path is empty, print your `STATUS:` line to the terminal.
