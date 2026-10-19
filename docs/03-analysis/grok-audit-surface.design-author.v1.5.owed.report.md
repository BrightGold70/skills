DESIGN-AUTHOR: DONE version=v1.5 path=docs/02-design/features/grok-audit-surface.design.md lines=769 sha256=805974b01afd69e726d28493e3a25e6cf1d7be520b799435fa7318ca188ad6ed

# Design author report: grok-audit-surface v1.5 (implementation-time owed items)

Tree: HEAD e39f15c5, branch feature/218-grok-audit-surface. Ownership check before the first write: the design's mtime and its newest Version History line (v1.4) matched what I first read. I did not commit. The spec shows as modified in `git status`; that is spec-author's concurrent work, and I did not touch it.
Precheck: `PRECHECK: PASS issues=0` (run before and after the bump). Every advisory is pre-existing:
- relative paths under the calibration or h-mad directories, plus the S3 measurement doc, which does not exist yet;
- L119 "4 fields beside 3" (D4 ledger line, untouched);
- L353 (D14);
- STALESHA `94a4fd2c` (Readings, untouched).
Version history: `VERSION-HISTORY: OK ... version=v1.5 line=769 placement=append`.

## Changes, each checked against `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` at e39f15c5

1. **D1, last resort.** It is now three channels in `refusal_token`:
   - a `Refusal` prints `exc.reason` (M:GAS-REFUSAL-REASON);
   - under `smoke`, any other exception prints `input_unparseable:<_OPEN_INPUT | --data value | "">` (M:GAS-OPEN-INPUT);
   - anything else prints `internal:<E>` (M:GAS-LAST-RESORT).

   The `_OPEN_INPUT` setters are stated: `_smoke_read`, `vocab_sets` and `delivered`; `main` resets it to None.
   Two residuals are stated: an exception raised after every input was read names the last input, and a smoke usage error with no `--data` prints an empty path.
   Traceback scope: a traceback prints only for an exception that is not a `ProbeRefusal` (M:GAS-TRACEBACK-SCOPE). There are 9 ProbeRefusal subclasses, counted with `grep -n '(ProbeRefusal)'`: Refusal, UsageError and the seven reset classes.
   Also in D1:
   - the sources-taking signatures are named: `placements(doc, sources)`, `extract_all(tree, s2_dir, sources)`, `hints(findings, tree, sources)` and `check_ledger(tree, sources)`;
   - the `_GROK_TYPES_RE` regex is corrected to the implemented either-quote form. The tree contradicted the design here: the design gave `'([^']*)'`, while `vocab_sets` uses `['"]([^'"\n]*)['"]`.
2. **D2.**
   - New paragraph on the `PROBE: UNREADABLE reason=unknown_mode` tenth prefix (M:GAS-UNKNOWN-MODE): stdout is the line only, usage and the `[H-MAD] ... unknown_mode UNREADABLE` marker go to stderr, exit 2.
   - New paragraph on usage errors: NO-HELP, NO-ABBREV and USAGE raise `UsageError`, which reaches the mode token. The paired-flag checks in `main()` go through `parser.error`.
3. **D4.** The totals comparison is unreachable behind the per-document rule, and it is unmarked. Checked with `sed -n 140,212p | grep M:GAS`: the `actual_totals != expected_totals` line has no marker.
4. **D5.**
   - `ResetPurposeNotS1` (M:GAS-RESET-PURPOSE) runs after EXCLUSIVE and before the five target guards (`reset_root` body).
   - The order of operations is unchanged: the re-walk still comes before step 6. Task 5 option (b) is recorded, and `monkeypatch.setattr(... "rewalk_matches" ...)` appears in exactly the two fixtures named in the design (test file, grep).
   - The no-follow guards are stated: NOFOLLOW-REMOVE, NOFOLLOW-PARENT and NOFOLLOW-WRITE with the ELOOP fallback.
   - The reset reason list now includes `internal:ResetPurposeNotS1`.
   - `placements(doc, sources)`.
   - `root_record:no_line` also covers a line that `parse_root_line` returns None for (M:GAS-RECORD-ROOT-MALFORMED). The parse_root_line rules are stated from the code.
5. **D8 record-cycle.** The check order is input_missing → root record → AUDITCYCLE → command → stem prefix, and every source is read before anything is written. The `command_unparseable` rule now matches the code: a flag absent or repeated, `=` form allowed, an empty or `--`-prefixed feature, a phase outside the three, or a cycle that is not a positive integer.
6. **D9 step 5.** `list_changed:unrecorded` now also covers a root.txt with zero or more than one READY line, or a malformed one (M:GAS-LIST-MALFORMED).
7. **D10.** The `[]` vs `None` semantics are stated, and the must-not-parse fixtures are named.
8. **D11.**
   - Effort block grammar: one `Effort:` line; then the `- ` items; each item must match `^p\d+ `; an empty block is malformed; two blocks are malformed; no block gives `[]`. Checked against `parse_effort_items` and `render` (h_mad_audit_cycle.py, `lines.append("Effort:")`).
   - A malformed block refuses at step 1, whether or not the cycle dispatched (M:GAS-SMOKE-EFFORT-MALFORMED). This is the order in the code: the block is checked before p1.log is read.
   - Step 2 states that `grok_log_types` skips ValueError and RecursionError and has no depth bound.
   - Residual (2) is rewritten to cover only events deeper than 64, and the "guaranteed" claim is qualified to hold outside that class. Checked: `scan_grok` catches `(ValueError, RecursionError)` and then applies `_json_deeper_than(event, GROK_MAX_DEPTH)` (h_mad_review_evidence.py).
9. **D12.**
   - `extract_all(tree, s2_dir, sources)`.
   - `placements(doc, sources)` in the hint resolver.
10. **D13 (Task 9 option (b)).** `delivered=<n>` and `low_evidence=<n|unreadable>` are defined from `score()`: pass index from `--surfaces`; ` low-evidence (` items starting `p<index> `; a None result sets `unreadable` for every surface the cycle lists, which stays set and never refuses. The output order is codex, agy, grok. `verdict` reads only `(hits, n, f, u)`.
11. **Error Handling.** The traceback scope, `PROBE:`, and the `internal:` sources.
12. **Test Plan.**
    - All 21 plan-added tests are named, each with what it asserts. The count is 18 probe + 3 smoke, derived by a script that diffs `^def test_` names against the design text; after the edit, 0 test names in the 5 modules are missing from the design.
    - S3 `test_grok_runtime_states_the_outcome_sentence` and rows K4–K7 come from impl-plan Task 16. They are marked not yet implemented.
    - K3, K5 and K6 finds: each gave 1 matching line on `grep -cF` at e39f15c5.
    - Rows preamble: X3/X4 find `# M:GAS-COLLAPSE-WIRE`, not the code block. That line is in the mutation spec and has 1 matching line in the probe.
    - P-row rule: "disarm = accept, never fall to a same-token sibling", with the stated exception for `root_record:no_line`. That fixture has two ends, and the two-line end kills it. Checked from the mutation-spec rows and the fixture body.
    - Written-out reset rows: added `p-reset-purpose`.
13. **Version History v1.5.** Corrects v1.4's "seven new reset tests" to eight (7 refusals + 1 must-not-refuse). Measured with `comm -13` of the sorted unique `test_build_root_reset_*` names at de149bc6 and a6a1571a: 8.

Value sweeps, run with `grep -cF` on the design: `placements(doc)` 0; `extract_all(tree, s2_dir)` 0; old regex `'([^']*)'` 0; `low_evidence=<count>` / `delivered=<counts>` 0. `RecursionError` gives 2: both are in the new D11 text, and both say both readers skip it. `seven reset` gives 2: D1 and Error Handling, both with the class count 7 (`ResetArgsConflict`, `ResetPurposeNotS1`, 4×`ResetTarget*`, `RootResetMismatch`).

## Not applied, or the tree disagreed
- The dispatch said "rows K4–K7": these are not in the mutation spec at HEAD (180 rows, none named K4–K7). They are Task 16 (S3) rows. I stated them as planned, not as implemented.
- Exclusion-list observation from implplan v1.0: `name-contains grok-audit-surface` does not remove the underscore-named `h-mad/tests/test_grok_audit_surface_*.py`, `grokauditfixtures.py` or `grok_audit_surface.json`. This is undecided, so I left D5 residual (4) unchanged. It needs an orchestrator or operator ruling: either widen the list (for example `name-contains grok_audit_surface` plus `grokauditfixtures`) or state these files as a residual.
- `list_check` has dead code (`if True: raise ... continue`, and a second `if fields is None: continue`). This is a structure for mutation, not a design matter. Noted only.

## Owed elsewhere (not edited)
- **Spec AC-5.1 / AC-5.4:**
  - the `PROBE: UNREADABLE reason=unknown_mode` tenth prefix;
  - `root_record:no_line` and `list_changed:unrecorded` extended to malformed records;
  - `low_evidence=` source and `unreadable` value (AC-5.4 is unchanged: not a reason);
  - the `ResetPurposeNotS1` guard.
- **Spec:** the new D11 residual (2) wording, if the spec quotes the RecursionError clause.
- **Spec AC-1.7 (carry 10):** an UNREADABLE caused by a wrong-file Effort item cannot be cleared by "restore input, derive again".
- **Impl-plan Task 16:** re-count the K-row finds at its own sha (the design cites e39f15c5).
