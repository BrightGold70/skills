AUDIT-doc-block-exec-design-v82-BEGIN

## Summary

One Must-fix: the CLI's stated parser configuration (`exit_on_error=False` plus an overridden
`error()`) provably cannot produce the `BAD_ARGS` verdict for a missing option value — the exact
input the design's own named test drives — so `argparse.ArgumentError`, which is not a
`DocBlockError`, escapes `main` as a traceback and a non-`DOCBLOCK` exit, breaching the very
Audit-gate signal-discipline invariant the paragraph invokes. Two Should-fixes: a false
behavioural premise in Task 5 (tagging the gate fence does **not** make `:270`'s `re.findall`
match zero blocks — measured: 3 of 4), and an `__all__` composition sentence whose enumeration
(28) disagrees with its own count (29) and with the impl-plan's Task 1. Everything else I could
falsify held: 81 mutation rows (79 helper + 2 `SKILL.md`), the 8-row `docsections.json` accounting
(4 originals + 4, 6 + 2 by file), 30 `*.md` under `h-mad/`+`handoff/` excluding `archive/`,
`h-mad/SKILL.md` with 0 duplicated bare heading texts and both `titled_section` targets unique,
`invariants.example.md`'s two duplicated headings, `docsections.py`'s 4-row spec and its
`_fence_aware_end`/`titled_section`/`section_from` shapes, `:270`/`run_recipe@:309`/`:412` and
`_gate_bash_block`'s two surviving text-pin callers, the mutation harness's `target_command`+`test`
node-ID contract, `test_skill_candidates_census.py`, markdown-it-py 2.2.0 on python 3.11.8, and
four cited probes reproduced here (reader-less FIFO `ENXIO` errno 6 at 0.0000 s; `mkdtemp` mode
`0o0` under `umask 0o777`; `json.dumps(..., ensure_ascii=False)` leaving U+0085/U+2028/U+2029/DEL
literal so `splitlines()` sees 4 lines; an empty alternation raising `KeyError('')`).

## Must-fix

- The parser configuration the design specifies cannot emit `BAD_ARGS` for a missing option value,
  which is one of the two inputs its own named test is specified to drive. Measured on
  python 3.11.8 (the supported interpreter) with `allow_abbrev=False` and `error()` overridden to
  raise `BadArgs`: under `exit_on_error=False` an unknown option, an abbreviation, a missing
  required option and a missing positional all reach the override, but a missing option value
  (`--index` with no value) raises `argparse.ArgumentError` **inside** `_parse_known_args` and
  never reaches `error()` — `exit_on_error=False` is precisely what suppresses argparse's own
  `except ArgumentError: self.error(str(err))`. `ArgumentError` is not a `DocBlockError`, so
  `main`'s `except DocBlockError` does not catch it: the run prints a traceback and exits non-zero
  with no `DOCBLOCK:` line, the outcome the paragraph itself calls "a breach, not an exception".
  The class is closed: with the argparse default `exit_on_error=True` all five grammar shapes
  reach the override and become `BadArgs`, and `--help` still exits 0 with its help text. The
  `argparse-error-unrouted` mutation row is wrong for the same input under the design's config —
  with the override removed the missing value still raises `ArgumentError`, not `SystemExit(2)`
  with usage. Fix: drop `exit_on_error=False` and keep only the `error()` override (measured
  sufficient, and it makes the mutation row true), or state an explicit `ArgumentError → BadArgs`
  mapping in `main`; the design states neither.
  quote: docs/02-design/features/doc-block-exec.design.md › `` `exit_on_error=False` and its `error()` overridden to raise `BadArgs(message)`, a `DocBlockError` ``
  quote: docs/02-design/features/doc-block-exec.design.md › `` `test_malformed_invocation_is_a_verdict` drives an unknown option and a missing ``

## Should-fix

- Task 5's justification for not splitting the tag from the migration rests on a measurably false
  premise. Measured against the tree at `e8eaf6f` (`_second_surface()` from the real
  `test_h_mad_collect_report_docs.py`, the gate fence tagged in memory): `re.findall(r"```bash\n(.*?)```", section, re.S)`
  matches **4** blocks today and **3** after tagging, not zero — the gating block is index 3, and
  the other three openers are unaffected. What goes to zero is the `h_mad_audit_gate.py` filter on
  the next line, so the loud failure is `_gate_bash_block`'s `assert gating, "…"`, not an empty
  `findall`. The conclusion (tag and migration cannot be split) survives; the mechanism a
  Phase-5d implementer would look for does not. `docs/01-plan/features/doc-block-exec.plan.md:369-370`
  carries the same wording and needs the same correction.
  quote: docs/02-design/features/doc-block-exec.design.md › `` `re.findall` match zero blocks. ``
  quote: docs/01-plan/features/doc-block-exec.plan.md › `— match zero blocks. It fails loudly rather than silently, which is the good case, but`
- The API section's statement of `__all__`'s composition contradicts its own count and the
  impl-plan it cites as the enumerator. Seven functions + `Block` + `RunResult` + **every
  `DocBlockError` subclass** is 7 + 2 + 19 = 28, since the Error Handling Strategy table lists
  exactly 19 subclasses and does not list the base. 29 is reachable only by including
  `DocBlockError` itself — which is what the Executive Summary's wording ("the exception
  hierarchy") means and what `docs/01-plan/features/doc-block-exec.impl-plan.md:139` and its
  `__all__` literal at :402-404 actually do (`DocBlockError` and its 19 subclasses, 20 exception
  classes, `"DocBlockError"` first in the list). This is the same off-by-one that already churned
  the count across v1.85 → v1.86; the API sentence is the one surface still stating it wrongly.
  quote: docs/02-design/features/doc-block-exec.design.md › `` `__all__` names all seven functions, plus `Block`, `RunResult` and every `DocBlockError` subclass — 29 names (`BadArgs` included) ``

## Nit

- §Scanning presents a six-name list as exhaustive ("every fence-grammar mutation row anchors"),
  but `backtick-in-info-accepted`, `prefix-state-truncated-mid-line` and `body-indent-not-stripped`
  are also `_fence_events` rows by their own mechanism columns and are absent from it.
  quote: docs/02-design/features/doc-block-exec.design.md › ``fence-grammar mutation row anchors (`fence-run-length-ignored`, `tilde-fence-not-tracked`,``
- Test Strategy's seam ordinals disagree with the order of its own parenthetical list. Read
  positionally, the list makes `os.unlink` fifth and `_final_write` sixth; the body and every
  cross-reference number `_final_write` fifth, `_close_stream` sixth, the `Popen` instance wrapper
  seventh and `os.unlink` eighth. Same eight seams either way — only the display order conflicts.
  quote: docs/02-design/features/doc-block-exec.design.md › ``The fifth is the module's own `_final_write(handle, text)` seam``
  quote: docs/02-design/features/doc-block-exec.design.md › ``The eighth is `os.unlink` in the helper's namespace``
- The AC-6.1–6.6 Test Plan row still names the executing path as `_gate_bash_block` and
  `run_recipe`, but Task 5 and the wire-mutation table rename the runner to the module-level
  `_run_recipe` (v1.54 claimed this was made consistent in Implementation Order and the wire
  table; the Test Plan row was not swept).
  quote: docs/02-design/features/doc-block-exec.design.md › ``left on the **executing** path (`_gate_bash_block` and `run_recipe`)``

AUDIT-doc-block-exec-design-v82-END
