## Summary
Axis C reconciliation found one restatement: AC-1.5 is narrower in the design than in the spec because Setext headings are explicitly not recognized. All other ACs are covered as written; the remaining findings are implementation-plan clarity risks, not hard spec gaps.

| ID | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | restated |
| AC-1.6 | implemented-as-written |
| AC-1.7 | implemented-as-written |
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
- AC-1.5 is restated from general markdown heading bounds to ATX-only bounds — spec says: "The section boundary is the next markdown heading at the same or shallower level; a tagged fence under a later heading is not returned for the earlier heading." Design says: "This is ATX-only by design and by limitation: a Setext heading (text underlined with `===`/`---`) is not recognised, so a document using them would bound wrongly rather than loudly." The design is narrower because Setext headings are markdown headings under the spec wording, so either the spec must explicitly accept ATX-only behavior or the design must handle Setext bounds.

## Should-fix
- The info-string grammar is ambiguous for untagged bash fences with extra tokens — the design says absence of `hmad:exec` is "invisible to `extract` - not an error," but also says "Any other token ... is `BAD_INFO`." Clarify that `BAD_INFO` applies only to tagged candidate fences, or explicitly specify the intended behavior for untagged malformed info strings.
- Stale verdict-count wording remains after adding `SUBST_OVERLAP` — the implementation order says "the seven verdict lines" while the table has eight verdict rows, and the test plan says "all six cannot-judges exit 2" while the design has seven cannot-judge verdicts. This is not a behavior gap because the tables cover `SUBST_OVERLAP`, but it can mislead test implementation.
- The paired plan still says "No new external dependency, and no `timeout`/`gtimeout` anywhere," while the design and spec now correctly ban invocations rather than substrings. Leaving both phrasings alive can produce an over-broad source-text test that rejects legitimate `TimeoutExpired`, `BlockTimeout`, or `--shell-timeout` code.

## Nit
None
