# grok-audit-surface: items carried from Phase 4 into Phase 5

Phase 4 exited on design v1.4 (`a6a1571a`) after two gating rounds (cycles 1–2) and two corrective revisions (v1.3, v1.4; operator decision 2026-10-19), neither re-audited. The items below were filed by the advisory delta reviews and the design author after the last revision. The implplan-author must place each on the Task it lands in. Items marked OPEN-DECISION are written `OPEN-DECISION: <finding> — resolve in 5d` and each names an implementation that satisfies it.

## From the v1.4 delta review (`grok-audit-surface.design.delta-review.a6a1571-20261019T011757Z.md`)
1. **OPEN-DECISION (must, build):** `test_build_root_reset_runs_the_reach_check` and `test_build_root_reset_rescans_after_removal` cannot produce their tokens: D5's post-reset re-walk raises `RootResetMismatch` before step 6 (scan, reach) runs. Satisfying implementations: (a) reorder D5 so step 6 runs before the re-walk assertion; or (b) the fixtures patch the re-walk to pass. Pick in 5d; the RED will show which fixture is unsatisfiable.
2. **⚠ Destructive (should, build):** the reset body follows symlinks inside the live root, so a symlinked placed document or by-product directory can make the reset write or delete OUTSIDE the root before step 6's `leak:` fires. The impl must not follow symlinks during removal and rewrite (`lstat`, `os.unlink` on links, no `rmtree` through links), with a fixture for each direction.
3. Reset fixtures must state they build with the default parent and `--purpose s1 --doc d1`; otherwise guards 3/4 refuse first.
4. Add `test_smoke_unrecognised_effort_item_refuses` (the class-closing default branch of step 3) with its P-row.
5. Define the grok log's "distinct `type` set" (line split, depth bound) as ONE reader shared with `scan_grok`, or state the open class of line-acceptance differences exactly; D11's "guaranteed" contradicts residual (2).
6. Pin the agy provenance block's `$STEM` placement (after the agy cycle block's `STEM=…; mkdir -p` line).
7. (measurement) Rows preamble: X3/X4 find `# M:GAS-COLLAPSE-WIRE`, not the D12 block. Re-run: `grep -n 'M:GAS-' docs/02-design/features/grok-audit-surface.design.md`.
8. (measurement) The v1.4 change log says "seven new reset tests"; there are eight (seven refusals + one must-not-refuse). Re-run: `git diff de149bc6 a6a1571a -- docs/02-design/features/grok-audit-surface.design.md | grep -o 'test_build_root_reset_[a-z_]*' | sort -u`.

## From design-author v1.3 / v1.4 reports §"New, for Phase 5"
9. Before S1, run one `exec agy` tracer into a `mktemp -d` root and record its `workspaceDirs=` line (`/var` vs `/private/var`), or agy's model line stays UNKNOWN.
10. A non-grok Effort item gives `SMOKE: UNREADABLE`; AC-1.7's remedy cannot clear it, only a new smoke can (spec gap; note it in the measurement doc runbook).
11. Marker `# M:GAS-COLLAPSE-WIRE` (rows X3/X4), per-alternative P-rows for step-3 refusals and the reset tests; re-derive marker and row counts at 5e.
12. Argparse usage errors exit 2 with no token, against AC-5.1 "every path out": wrap the parser so they print the mode's `UNREADABLE`/`REFUSED` token.
13. `--reset` with `--purpose` other than `s1` is not refused (guard-4 prefix is the literal `s1`).
14. Step-3 wrong-file guard needs a synthetic pairing because step 2 shadows it on real inputs; its reachability depends on how record-cycle copies files.
15. Residual-(2) fixture depth must derive from `GROK_MAX_DEPTH`, not a literal 65.

## Interpreter
Mutation specs and every pytest run: `/opt/anaconda3/bin/python3.11`. `python3` (3.15) has no pytest; the RTK hook rewrites `python3 -m pytest`, so probe with `rtk proxy`.
