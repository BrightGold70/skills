## Summary

The design covers the acceptance criteria broadly, but AC-2.7 has conflicting diagnostic expectations and an incomplete intersection scan. Re-running the document’s checks also exposed stale measurements; filesystem restrictions prevented writing the report artifact and completion marker.

Evidence: 7 files opened, 8 greps run.

| Acceptance criteria | Axis C classification |
|---|---|
| AC-1.1–1.9 | implemented-as-written |
| AC-2.1–2.6 | implemented-as-written |
| AC-2.7 | restated |
| AC-2.8 | implemented-as-written |
| AC-3.1–3.14 | implemented-as-written |
| AC-4.1–4.6 | implemented-as-written |
| AC-5.1–5.6 | implemented-as-written |
| AC-6.1–6.6 | implemented-as-written |

## Must-fix

- **AC-2.7’s test matrix asserts the wrong diagnostic.** For `ab`/`bc` in `abc`, it requires an extra `at` token and offset `0`; the specification requires no connective and shared index `1`. This changes the accepted output rather than merely paraphrasing it: the prescribed test would reject conforming code. Correct the matrix to match the specification and the design’s substitution section.
  quote: docs/02-design/features/doc-block-exec.design.md › `asserting one `intersect: "ab" "bc" at "0"` line and nothing executed`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `intersect: "ab" "bc" "1"`

- **AC-2.7’s demonstrated scanner silently narrows “every match span” to non-overlapping occurrences within each key.** Executed counterexample: keys `aa` and `ab` on `aaab`. The prescribed `finditer` construction produces `[0,2)` and `[2,4)` and finds no intersection; it misses `aa` at `[1,3)`, which intersects `ab` at index `2`. Neither key contains the other, so that guard does not compensate. Enumerate overlapping occurrences and add this discriminating fixture, or explicitly amend the specification before adopting the narrower policy.
  quote: docs/02-design/features/doc-block-exec.design.md › `sp = [(m.start(), m.end(), k) for k in subs for m in re.finditer(re.escape(k), text)]`
  quote: docs/01-plan/features/doc-block-exec.spec.md › `collected, two spans from different keys sharing an index being an intersection`

- **The shipped document contradicts its claimed post-edit measurements.** The published digit-ordinal expression returns **30**, not 29; the compliance marker walk returns **70**, while its subsequent partition accounts for 69. The claimed empty `af19d53`→working candidate-line differential actually contains four replaced lines, despite unchanged totals. These are reproducible failures of the stated verification evidence, violating Assumption verification and Behavioural premises carry their command. Re-run and reconcile every affected reading and partition on the final bytes.
  quote: docs/02-design/features/doc-block-exec.design.md › `head is published beside that stamp rather than withheld — `$P` **29** and `$W` **8**, both`
  quote: docs/02-design/features/doc-block-exec.design.md › `**The second walk's `69` splits mechanically before anything is`
  quote: docs/02-design/features/doc-block-exec.design.md › `nothing, and `af19d53`→working prints nothing.`

## Should-fix

- **Synchronize the paired plan’s mutation inventory.** It still specifies 81 mutations while the design specifies 85. This leaves conflicting implementation scope in the documents being gated together.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `81 mutations with a full-node-ID `test` binding each`
  quote: docs/02-design/features/doc-block-exec.design.md › `85 mutations (85 rows: 84 of the helper's source, 1 of `h-mad/SKILL.md``

## Nit

None
