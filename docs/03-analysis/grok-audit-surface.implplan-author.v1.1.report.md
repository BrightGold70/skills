IMPLPLAN-AUTHOR: DONE version=v1.1 tasks=18 wiring=1 mutation_rows=166 path=/Users/kimhawk/orca/skills/docs/01-plan/features/grok-audit-surface.impl-plan.md lines=1490 sha256=5490674354dbfab24c79344f7b94c05f769b30ce128e0fa273ffd51ba0383d73

## Ownership check before writing
The document's sha256 was 57966d7b645e14c2ccbcce22c19b3bc737fcf93db8792525666d931a0db56776 (my v1.0) and its newest Version History entry was `- v1.0`, so nobody else had written it. I bumped the version with h_mad_version_history.py, which printed `VERSION-HISTORY: OK … version=v1.1 placement=append`.

## Applied: operator ruling on the unknown-mode argv
- Task 2: before any parsing, an empty argv or a first word outside the nine `GRAMMAR` keys prints exactly one stdout line, `PROBE: UNREADABLE reason=unknown_mode`, with no counts (marker `# M:GAS-UNKNOWN-MODE`). Usage then goes to stderr, followed by the `[H-MAD]` marker, and the probe exits 2. AC-5.1 holds as written.
- New test `test_unknown_mode_prints_the_probe_token`, 2 ids (`[]` and `["no-such-mode"]`), run as a subprocess. It asserts exit 2, stdout exactly that one line, and `usage:` on stderr.
- New row `p-unknown-mode-token`: the token line removed (its `print` replaced by `pass`), with usage and exit 2 unchanged. Its target is `tests/test_grok_audit_surface_probe.py::test_unknown_mode_prints_the_probe_token`.
- Task 2's RED split goes from 18 F to 20 F, and AC-T2.1 now says 20 ids.
- New totals: 166 rows (28 named + 138 P-rows) and 112 marker sites. The Executive Summary, T14 (AC-T14.2 `untargeted=0/166`, AC-T14.4 "112 and 166") and T16 (AC-T16.3) are updated. Carry row 12 is updated.

## Counts (parsed from the document)
166 row-table lines and 112 distinct markers. WIREPIN still reads 18 tasks with 1 wiring.

## OWED-ELSEWHERE
- Design D2 and the spec's AC-5.1/AC-5.4: add a tenth token prefix, `PROBE:`, owned by no mode, with the single form `PROBE: UNREADABLE reason=unknown_mode`, exit 2, printed when argv names no mode. I did not edit the spec or the design.
- All other v1.0 items are unchanged; see /tmp/author_grok-audit-surface_5a_v1.report.md.

## Gates
- `PRECHECK: PASS issues=0`.
- Advisories kept on purpose:
  - L1221 "17 rows" and L1327 "0 files", as in v1.0.
  - L1489 is the dated v1.0 Version History entry ("18 Tasks", "165 rows", "111 sites"). Those figures were true for v1.0 and are kept as the historical record.
- `WIREPIN: PASS tasks=18 wiring=1 unpinned=0 mislabeled=0`. I gave it a scratch registry and deleted it afterwards.

## Placeholder scan
Clean.

## Tree
`git status` shows only the impl-plan as untracked; no scratch files remain.
