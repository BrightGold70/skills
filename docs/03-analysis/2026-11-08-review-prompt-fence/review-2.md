# Change review — working tree against 6f3e48e8 (fence-r2.diff, round-1 remediation) — GATING

## Evidence
- read: 9 files · ran: 14 commands · tests run: 17 test files that read the touched files, 1166 passed (scratch tree from `git archive HEAD` + `git apply fence-r2.diff`, with `main` fetched so BASE_SHA resolves); the 6 rows hand-applied, each against its named node; 5 extra mutations against the whole of test_h_mad_assemble_tdd_agent.py; an in-process probe of the hand-staging recipe
  - The 17 files: test_h_mad_agy_review_fixes, archreview_cycle, assemble_tdd_agent, agy_authorship_docs, assemble_tdd, audit_read_only, codex_gate_tmp_reports, backlog_cycle, codex_runtime, guard_census, new_caller_carveout_copies, skill_reviewer_prompt, skill_budget, tdd_gate_peers, verifier_prompt, test_hmad_dispatch_exec, test_hmad_dispatch.
- Files read:
  - the r2 diff (265 lines, same as `git diff`)
  - `h-mad/scripts/h_mad_assemble_tdd.py`: 899-913 (`review_fence`), 955-977, and `task_body`'s return at line 215
  - `h-mad/references/agy-spec-reviewer-prompt.md` 1-30
  - `h-mad/references/helper-scripts.md:34`
  - `h-mad/tests/test_h_mad_assemble_tdd_agent.py` (new and changed tests)
  - `h-mad/tests/test_h_mad_assemble_tdd.py` 1280-1312 (the `REAL_101_PLAN` fixture)
  - `h-mad/tests/mutation-specs/assemble_tdd_review.json` (the 6 rows)
  - a grep of `h-mad/references/*.md` for templates that carry `<INLINE_CODEX_REPORT>`
  - a grep of `h-mad` for `--phase review` callers that pass `--template`
- I deleted the scratch trees and the probe. I edited no repo file.
- In the mutation copy (no git history), `test_no_agent_output_is_byte_identical_to_base` fails under every mutation because `git archive 8ef6009f` exits 128. That failure comes from my setup, and I left it out of every verdict below.

### Round-1 findings, closed or not
- **Should-fix 1 (overstated "cannot"): closed.** The template now says "does not contain". `review_fence` documents a forging cost of about 2**128 / k and returns 32 hex. Truncating the id to 16 hex is killed by 3 real tests.
- **Should-fix 2 (no hand-staging recipe): partly closed.** The recipe now exists, but it gives the wrong id whenever the task cites a section. See Should-fix 1 below.
- **Should-fix 3 (closing rule unpinned): closed.** `rv-closing-rule-drops-the-id` fails with "the closing rule names this run's id…". My round-1 mutation of the same sentence is now killed (1 failed, 89 passed).
- **Nit (custom template stages unfenced): closed.**
  - `rv-unfenced-custom-template-staged` is killed: the test sees `ASSEMBLE-TDD: PASS` where it expects `template_unfenced`.
  - Only one shipped template carries `<INLINE_CODEX_REPORT>` (`agy-spec-reviewer-prompt.md`), and it is fenced.
  - No `--phase review` caller in `h-mad` passes `--template`.
  - All 17 reading files pass, so the new halt refuses nothing that already runs.
- **Nit (`\0` ambiguity): fixed in the code, but its mutation row survives.** See Must-fix 1.
- **Round-1 survivor "hash the report only": now killed.** `for part in (report,)` fails `test_the_review_fence_follows_both_quoted_blocks_and_their_boundary`.
- **Other rows:** `rv-fence-id-is-a-constant`, `rv-fence-slot-unfilled` and `rv-template-report-unfenced` are killed for the right reasons (constant `000…` != `000…`, `HALT residual_slots`, `('REPORT', [])`). Each `find` matched exactly once.

## Must-fix
- **Mutation row `rv-fence-parts-not-length-prefixed` is not killed.**
  - Scenario: apply its `replace` (`digest.update(data)`) and run its test node, `test_the_review_fence_follows_both_quoted_blocks_and_their_boundary`. The result is `1 passed`.
  - Across the whole of test_h_mad_assemble_tdd_agent.py the same mutation fails only the history-dependent test from my setup, so no real test kills it.
  - Cause: the discriminating assertion was written for the old `\0` separator. Without a length prefix, `fence("a\0b","c")` hashes `a\0bc` and `fence("a","b\0c")` hashes `ab\0c`. Those are different bytes, so the two ids differ either way. The assertion that tells the two versions apart is a boundary shift with no separator, such as `fence("ab","c") != fence("a","bc")`.
  - Effect: the harness run that the background job holds the lock for will report this row SURVIVED. The property the row claims to pin, that no split of the same bytes shares an id, is not pinned.
  quote: h-mad/tests/test_h_mad_assemble_tdd_agent.py:220 › `assert fence("a\0b", "c") != fence("a", "b\0c")`

## Should-fix
- **The hand-staging recipe gives a different id from the script when the task cites a section.**
  - The recipe says to pass "the inlined task body … without trailing newlines". The script hashes `body` without stripping it, and when sections are inlined, `body` ends with `"\n"` (each section is appended as `f"\n{section}\n"`).
  - Executed with `REAL_101_PLAN`, `Task 3`, which inlines `Hash re-pin (…)`:
    - The TASK block ends with a newline (`block ends NL True`).
    - `review_fence(block.rstrip("\n"), report.rstrip("\n")) == script id` is **False**.
    - Hashing the unstripped block reproduces the script's id (`raw block==script True`).
  - With the agent test `PLAN` (no sections) the recipe matches (`recipe==script True`).
  - Security is unaffected, since a mismatched id is still unpredictable. But the recipe promises equivalence it does not give, and a hand-stager has no way to tell. "The inlined task body" also never says that the `**Referenced impl-plan sections …**` wrapper text is part of the task.
  - Fix either side: say "the TASK block's text exactly as the script builds it; strip only the report's trailing newlines", or rstrip `body` before both hashing and filling.
  quote: h-mad/references/agy-spec-reviewer-prompt.md:8-9 › `` `<INLINE_FENCE>` with `h_mad_assemble_tdd.review_fence(task, report)` (the inlined task body and the report`` / `without trailing newlines), never a constant.``
  quote: h-mad/scripts/h_mad_assemble_tdd.py:959 › `+ "".join(f"\n{section}\n" for _, section in sections))`

## Nit
- **`template_unfenced` checks only that `<INLINE_FENCE>` appears somewhere in the template**, not that it wraps the report. A template that names `<INLINE_FENCE>` only in prose and quotes `<INLINE_CODEX_REPORT>` bare still stages. Copied templates fail the simple way, so this rarely matters.
