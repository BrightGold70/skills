AUDIT-grok-codex-fallback-design-v1-BEGIN
## Summary
The design covers the feature's main paths, but one acceptance criterion is restated and several parser and test claims do not hold under the specified inputs. Axis C classifies 54 of 55 ACs as implemented-as-written, AC-5.2 as restated, and none as absent; the table records every identifier.
Evidence: 12 files opened, 11 greps run. I read the saved spec and design, the paired plan audit, and the relevant dispatch, evidence, audit-cycle, resolver, assembler, and test-harness code; I also ran read-only shell/Python controls for key order, malformed types, and jq discovery.

| FR | implemented-as-written ACs | restated | absent |
|---|---|---|---|
| 1 | AC-1.1, AC-1.2, AC-1.3, AC-1.4 | — | — |
| 2 | AC-2.1, AC-2.1b, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.6, AC-2.7 | — | — |
| 3 | AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6, AC-3.7 | — | — |
| 4 | AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5, AC-4.6, AC-4.7, AC-4.8, AC-4.9 | — | — |
| 5 | AC-5.1, AC-5.3 | AC-5.2 | — |
| 6 | AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 | — | — |
| 7 | AC-7.1, AC-7.2, AC-7.3, AC-7.4, AC-7.5 | — | — |
| 8 | AC-8.1, AC-8.2, AC-8.3, AC-8.4, AC-8.5 | — | — |
| 9 | AC-9.1, AC-9.2, AC-9.3, AC-9.4 | — | — |
| 10 | AC-10.1, AC-10.2 | — | — |
| 11 | AC-11.1, AC-11.2 | — | — |

## Must-fix
- AC-5.2 is restated: the spec requires the F0 progress output to print exactly the listed event lines, while the design tests only counts per named class and permits extra thought/text run lines. The design narrows the assertion and must either match the spec's output contract or have that contract explicitly revised before implementation.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.spec.md › `progress --lines 400` on F0 prints exactly these lines
  quote: docs/02-design/features/grok-codex-fallback.design.md › `"Prints exactly these lines" is read as exact counts per named class`
- The shell detector and Python reader disagree when `type` is not the first key: `{"meta":1,"type":"text"}` makes the proposed grep return 1 while JSON parsing recognizes `text`. The design expressly leaves this untested, so a valid grok log can render as codex text while the audit-cycle scorer calls it grok; equality of the seven type names does not meet the base single-source contract. Make the classifiers behaviorally equivalent and add a reordered-key agreement case, or reconcile the narrower format rule in the spec.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.spec.md › `grok-ndjson` is chosen when any line matches, whitespace-tolerantly, a JSON object whose
  quote: docs/02-design/features/grok-codex-fallback.design.md › `A grok build that emits `type` later in the object classifies as `codex-text` here, while `scan_grok` (D6) still parses it.`
- The proposed `scan_grok` membership test crashes on a JSON object with `"type":[]` or `"type":{}`: Python raises `TypeError` when an unhashable value is tested against a frozenset. The parser promises to skip objects without one of the seven string types, and an unrecognized line must not abort evidence reading or audit scoring. Type-check the field and test malformed objects before and among valid events.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `An event counts only when `event.get("type") in _GROK_TYPES`. When no line qualifies, the function returns `None`.`
- The planned no-jq test cannot remove jq by omitting it from `bindir`: the documented test PATH retains `/usr/bin:/bin`, and `/usr/bin/jq` exists on this host (`h-mad/tests/test_hmad_dispatch.py:162`; `command -v jq` under that PATH returned `/usr/bin/jq`). The test would exercise the parsed path, leaving the required missing-jq EMPTY behavior unverified. Give that test a PATH containing the required utilities but no jq and verify `command -v jq` fails inside the subprocess.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `**no-jq** EMPTY path (a `bindir` without `jq`, where stderr has `not parsed` and no `TRUNCATED`)`
- The FR-4 performance contract is unresolved: the spec requires the parser to be tail-bounded, but the design slurps the entire dispatch region into `jq -Rs` for final-message extraction and provides no bound for completion detection. The cited agy response reader is also unbounded (`h-mad/scripts/hmad-dispatch.sh:1982-2017`), so “as the agy readers are” is a false premise. Specify and test a bound that preserves a complete final segment, or revise the spec's performance requirement deliberately.
  class: build
  quote: docs/01-plan/features/grok-codex-fallback.spec.md › `The FR-4 and FR-5 parsers read only the dispatch's region, tail-bounded as the agy readers`
  quote: docs/02-design/features/grok-codex-fallback.design.md › `It is run as `jq -Rs -r`, slurped raw, so a multi-line segment stays one value.`

## Should-fix
- `_grok_last_tool` would print a dispatch-wide “N tool calls completed” count computed only from the last 2,000 lines; a longer dispatch can silently undercount. Either compute distinct completed IDs over the full region with a bounded-memory stream or label the number as a recent-window count and pin that behavior in the spec and a test.
  class: build
  quote: docs/02-design/features/grok-codex-fallback.design.md › `**Residual:** a region longer than 2000 lines counts `N` within that window only.`
- The design's closed-world shape census says six reachable shapes, but its own routing table and shape-enumeration test name seven (`codex-text`, `missing`, `unparseable`, `empty`, `grok-truncated`, `parsed`, `grok`). Correct the published count so the future shape sweep has an unambiguous population; no production change is implied.
  class: measurement
  quote: docs/02-design/features/grok-codex-fallback.design.md › `Today the only reachable shapes are the six named.`

## Nit
None
AUDIT-grok-codex-fallback-design-v1-END
