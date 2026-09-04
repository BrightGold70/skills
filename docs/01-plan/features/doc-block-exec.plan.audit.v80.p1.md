AUDIT-doc-block-exec-plan-v80-BEGIN
## Summary
The Plan document contains multiple adversarial consistency failures where the text asserts the output of a command (such as `grep` counts or `git ls-files`) but the actual command run against the repository or the document itself yields a different result. There is also a flaw in the `awk` regex that contradicts a claim about POSIX boundaries.

## Must-fix
- The command opener census for the spec incorrectly claims `sed` ×1 and 20 total openers, when the command actually returns `sed` ×2 and 21 total openers.
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``**20 openers** over **11 distinct tokens** — `awk` ×1, `curl` ×1, `git` ×7, `pairs` ×1, `printf` ×2, `python3.11` ×1, `RULE` ×1, `S` ×1, `sed` ×1, `split_only` ×3, `while` ×1.``
- The plan claims `grep -c '74e126f'` returns 27, but running it over the document returns 29.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `` `grep -c '74e126f'` over the body returns **27** at `6f0ee85` ``
- The plan claims the narrowed `awk` and `grep` pipeline returns 10, but it actually returns 11.
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``the narrowed form `awk '/^## Version History/{exit}{print}' <doc> | grep '74e126f' | grep -cE 'h-mad|handoff'` returns **10**, and neither integer is the number of covered figures``
- The plan claims `grep -c '35698f9'` and `grep '35698f9' … | grep -c 'h-mad'` both return 5, but they actually return 20 and 4 respectively.
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``Every `35698f9` in the body mentions both (`grep -c '35698f9' …` and `grep '35698f9' … | grep -c 'h-mad'` both return **5**)``
- The plan claims `grep -c '6f0ee85'` returns 3 and `grep '6f0ee85' … | grep -c 'h-mad'` returns 3, but they actually return 36 and 5 respectively.
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``and every `6f0ee85` in the body mentions both (`grep -c '6f0ee85'` returns **3** and `grep '6f0ee85' … | grep -c 'h-mad'` returns **3**).``
- The plan claims `h-mad/tests/test_docsections.py` is the only caller of `docsections` in the repository, but a search reveals it is also imported by `h-mad/tests/test_h_mad_review_evidence.py` and `h-mad/tests/test_h_mad_wire_registry.py`.
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``(the only caller is `h-mad/tests/test_docsections.py` testing it — see §Design for why it isn't an execution-time dependency)``
- The plan claims `git show --stat 6db8e50` lists exactly five new files under `h-mad/agents/`, but the command output also lists modifications to `h-mad/SKILL.md` (6 files total).
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``(`git show --stat 6db8e50` lists exactly those five new files)``
- The carve-out table claims `git ls-files` on the subject `h-mad/bin/hmad-dispatch` returns "two paths", but running it returns exactly one path.
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``| The `run --timeout` wrapper's `124` (the 5f bound under §Success Criteria) | `h-mad/bin/hmad-dispatch` | **two paths** | **not exempt — carries a sha, below** |``
- The third branch of the shape filter (`[Tt]his session`) lacks the both-sides POSIX boundaries applied to the other two branches — contradicting the claim that the same both-sides treatment is applied to every sibling branch.
  quote: docs/01-plan/features/doc-block-exec.plan.md › ``/(^|[^[:alnum:]_])[Mm]easured([^[:alnum:]_]|$)|(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)|[Tt]his session/ && !/[0-9a-f]{7}/{print NR": "$0}' \``

## Should-fix
None

## Nit
None
AUDIT-doc-block-exec-plan-v80-END
