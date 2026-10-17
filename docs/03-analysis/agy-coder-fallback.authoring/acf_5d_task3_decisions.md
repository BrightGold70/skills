# agy-coder-fallback — 5d Task 3 record

## Post-Task census reading (plan: "record the post-Task M-3 reading; it moves by construction")
`census_mutation_rows.py` at a9102c1d prints `PROBE: FAIL` against the 4e4b5ded EXPECT — every
moved figure is a row this feature added, nothing else moved:
- M-2 `h-mad-tdd-gate.sh` 56→62 rows, 5→6 specs (+6 rows of `tdd_gate_peers.json`).
- M-2 `h_mad_tdd_judge.py` 36→41 rows, 8→10 specs (+4 `tdd_judge_implementer.json`, +1 `wire1-author-not-from-resolver`).
- M-3 8→10 rows, 3→5 specs (+1 `tdd_gate_peers.json`, +1 `tdd_judge_implementer.json`).
- FR-3 `_read_state` 7→10 (+`fr3-invalid-scan-first-record-only`, `wire2-hook-rederives-from-env`,
  `wire2-every-author-is-a-peer`); `format_state_line` 4→5 (+`wire1-author-not-from-resolver`).
- FR-3 authorship-block boundary absent → 0 rows: the `command -v codex` block it measured was
  replaced by FR-3's precedence (design intent). Row `H3` still anchors (`ANCHORS_OK`).
Tasks 4 and 18 re-run this probe; compare against THIS reading, not the 4e4b5ded EXPECT.

## Gates (outside sandbox)
- 574 passed (peers + judge + implementer + every `test_h_mad_tdd_gate_*.py`).
- Three fixture literals vs a8d9ba99: exactly one changed line each (`RECORD`, `_tree_b`
  default, `ACTIVE_RE`).
- `ANCHORS_OK` 12 specs 128/128; all 12 specs `MUTATION: ALL_CAUGHT` (incl. `wire1-*`, `wire2-*` cut, `wire2-every-author-is-a-peer` converse).
- Grammar probe, both bashes: `mode=shipped`, `shipped literal == grammar derived from a8d9ba99`,
  `PROBE: PASS`; `--control` → `PROBE: FAIL`.
- Revert probe (HEAD hook + judge): `8 failed, 6 passed` = RED split; restored `14 passed`.
- Rows without `symbol`: 3, all at top-level shell sites (Codex-documented).
