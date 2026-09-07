## Summary

Two surfaces of this plan carry `81` as the `doc_block_exec.json` mutation total while the design's
authoritative matrix, the design's own Components cell and the impl-plan all carry `85`; the design
gained four rows in `cb4fe99`, the same commit that landed plan v1.104, so the plan is the only one
of the four documents that disagrees. Everything else I could reach reproduced exactly: I re-ran the
fence census at seven shas, the three repo-wide `.py` censuses, the `awk` boundary probe's five
legs, the three committed measurement probes, the `json.dumps` per-code-point probe, both collect
counts, the codex/teammate ledger series at eleven shas, the two screens and roughly forty locators
and per-sha greps, and every published value returned what the document states.
Evidence: 13 files opened, 190 greps run.

## Must-fix

- The `doc_block_exec.json` mutation total is `81` on two plan surfaces (§Deliverables and the
  §Measurements carve-out list) against `85` in the design's matrix, the design's Components cell
  and the impl-plan — a 5c author sizing that spec from §Deliverables authors four rows fewer than
  the matrix this document names as authoritative, and the mutation harness refuses a spec whose
  rows do not match their anchors. Measured at the freeze `cb4fe99`: the design's matrix at lines
  3672–3758 is 87 table lines, so 85 data rows, with 85 distinct names in column 1 and exactly one
  row naming `SKILL.md` as the mutation target — the split is `84 + 1`, not `80 + 1`. The same row
  count over `git show 09e9307:<design>` is 81, and the four rows added in between are
  `cleanup-chain-selection-flipped`, `intersect-check-removed`, `rollback-identity-check-removed`
  and `spawn-valueerror-unmapped`. **The class, and it is why this is not a one-digit repair**: the
  §Measurements carve-out exempts design-derived counts of artifacts that do not exist yet from the
  provenance rule, so this is the one figure in the document carrying neither a command nor a sha,
  and §Deliverables re-derives the *split* from the matrix's mechanism column while *carrying* the
  total — the half that moved is the half with no derivation. Prescription: derive the total from
  the same surface and in the same form as the split, with the sha inside the command
  (`git show <sha>:<design> | sed -n '<first>,<last>p' | grep -c '^| \`'` or equivalent), and retire
  the "contract values" carve-out for any figure whose source is a sibling under `docs/` — a value
  this plan must match is still a reading of another document, and the carve-out is what removed
  the only screen that would have caught this.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `81 mutations with a full-node-ID`
  quote: docs/01-plan/features/doc-block-exec.plan.md › `(`29` names, `81` mutations, `8` rows), which are contract`
  quote: docs/02-design/features/doc-block-exec.design.md › `85 mutations (85 rows: 84 of the helper's source, 1 of`
  quote: docs/01-plan/features/doc-block-exec.impl-plan.md › `` `doc_block_exec.json` 85 rows ``

## Should-fix

- The second AC-1.8 collect-alone pin is described here only by mechanism, while the design and the
  impl-plan both name it `test_docsections_imports_when_collected_alone` — 1 occurrence in the
  design body, 4 in the impl-plan body, 0 in this plan's body at `cb4fe99`. Its twin is named by
  node ID in the same sentence (`test_docsections_imports_from_an_unrelated_cwd`), so a 5c author
  reading the plan alone gets one AC-1.8 import pin as a test name and the other as a shell command
  with no node ID to bind, which is the shape this document's own rule against unnamed seams exists
  to prevent ("one name on every surface"). Prescription: name it in the same clause, beside the
  isolated-import pin.
  quote: docs/01-plan/features/doc-block-exec.plan.md › `they are the AC-1.8 collect-alone pins Success Criteria names`
  quote: docs/02-design/features/doc-block-exec.design.md › `test_docsections_imports_when_collected_alone`

## Nit

- §Scope's parenthetical enumerating the values `_field` escapes predates the `intersect:` detail
  line the round-seventeen batch added to the other three documents (8 body occurrences in the
  spec, 21 in the design, 22 in the impl-plan; 0 here). Nothing this plan states is thereby false —
  the enumeration is a gloss on "every dynamic field", and `intersect:` is quoted, which the bare
  seven-field list already implies — but adding it would keep the gloss current with the siblings.
