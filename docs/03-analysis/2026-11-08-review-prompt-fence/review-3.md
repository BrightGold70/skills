# Change review — working tree against 6f3e48e8 (fence-r3.diff, round-2 remediation) — GATING

## Evidence
- read: 4 files · ran: 8 commands · tests run: 17 test files that read the touched files, 1167 passed (scratch tree from `git archive HEAD` + `git apply fence-r3.diff`, with `main` fetched); all 9 fence and template rows applied by hand; one in-process probe
- Files read:
  - the r3 diff, same as `git diff`
  - `h-mad/scripts/h_mad_assemble_tdd.py`: 955-978, and every use of `body` between lines 950 and 1000
  - `h-mad/references/agy-spec-reviewer-prompt.md` 7-11
  - `h-mad/tests/mutation-specs/assemble_tdd_review.json`
- I deleted the scratch trees and the probe. I edited no repo file.

### Checks
- **Round-2 Must-fix (length-prefix row survived): closed.**
  - `rv-fence-parts-not-length-prefixed` now fails its node (`1 failed`).
  - All 9 rows, including `rv-template-implementer`, are killed against their named nodes.
  - The two new rows fail for the right reason:
    - `rv-fence-body-keeps-trailing-newline` fails `test_the_review_inlines_the_sections_the_task_cites` with "the documented recipe … `'38a58da2c44a…' == 'acf0a3491f88…'`".
    - `rv-fence-named-only-in-prose-passes` fails `[fence-only-in-prose]` with `ASSEMBLE-TDD: PASS` where a halt was expected.
- **Round-2 Should-fix (recipe gave a different id with inlined sections): closed.** I re-ran the probe with `REAL_101_PLAN`, `Task 3`, which inlines `Hash re-pin (…)`.
  - It applied the recipe literally: `review_fence(TASK block.rstrip("\n"), REPORT block.rstrip("\n"))`.
  - The result was `recipe==script True`, and also `True` for the agent `PLAN`, which inlines no section.
  - A CRLF report reaches the block with no trailing `\r` (`ends CR False`), because `read_text` translates newlines. The "without trailing newlines" wording therefore covers it.
- **Round-2 Nit (fence named only in prose): closed** by the literal block check at `h_mad_assemble_tdd.py:974`.
- **The strict template check, against templates I built:**
  - The shipped template is accepted (PASS).
  - A copy with CRLF line endings is accepted (PASS). `read_text` turns CRLF into `\n` before the literal compare.
  - A copy with no trailing newline at end of file is accepted (PASS).
  - A copy with a trailing space on the BEGIN REPORT line is refused (`HALT template_unfenced`).
  - A copy with a blank line inside the block is refused (`HALT template_unfenced`).
  - I think refusing those last two is right. The halt names the shipped template to start from. A loose match would have to re-implement the BEGIN/END grammar that agy is told to apply exactly, and a refusal only costs the person who edited the copy one re-copy.
- **The body strip changes nothing else that is depended on.**
  - Its only byte effect is that when sections are inlined, the TASK block loses its final `\n`, so there is one fewer blank line before `=== END TASK`.
  - After line 961, `body` is used only for the fence and the `<INLINE_IMPL_PLAN_TASK>` fill. `meta` takes `sections`, not `body`.
  - The RED, GREEN and gate assemblers do not call this code.
  - All 17 reading files pass, including the byte-identity test against BASE_SHA, which now runs in a tree with history.

## Must-fix
None

## Should-fix
None

## Nit
None
