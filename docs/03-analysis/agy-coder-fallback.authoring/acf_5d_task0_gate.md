# agy-coder-fallback — 5d Task 0 (gate) report

**Date:** 2026-10-17 · **HEAD measured:** 7919a542 · **Author:** Codex (`hmad-dispatch exec codex`, hand prompt —
the assembler has no path for a `gate` task; operator chose this route) · **Gate:** orchestrator re-run.

## Dispatch
- rc=124 at 2400 s, no final message, no report file. Cause from transcript: after writing and
  self-verifying the four probes, Codex ran the full suite inside its `workspace-write` sandbox
  (~20 min, sandbox-only failures seen) and the watchdog fired before it reported. The probes were
  complete; the timeout cost the report only. Next hand-prompt: forbid the in-sandbox full suite
  (the orchestrator runs it outside).
- Tree delta: exactly the 4 permitted files, all new.

## Probe verdicts (orchestrator re-run, all exit 0)
| probe | real run | Codex control (expectation override) | input-doctored control (orchestrator) |
|---|---|---|---|
| `census_mutation_rows.py` (from `h-mad/`) | PASS — every M-2/M-3/FR-3 (13 = hook 8 + judge 5)/M-4 (31 of 62, 4 specs, 0 absent, 0 non-unique) figure = plan | FAIL | one row dropped from `tdd_gate_scratchpad.json` in a scratch repo → `tdd-gate.sh/rows 55 vs 56 MOVED`, FAIL |
| `census_state_line.py` | PASS — DO-1a 6 files, four-pattern 7 | FAIL | `TDD-STATE: active` doctored in one test file → `5 vs 6 MOVED`, FAIL |
| `census_doc_pins.py` | PASS — prompt 23 distinct literals in 8 files | FAIL | one pinned literal reworded in the prompt copy → `22 vs 23`, FAIL |
| `class_inventory.py` | PASS — 58; (a) 11, (b) 5, (c) 1, (d) 41 | FAIL | `run_command` removed from first `init.tools` → total 57, (c) 0, FAIL |

No figure moved between `4e4b5ded` and the 5c tree → nothing routes back to the design before Task 3.

**Finding (process):** the probes' built-in `--control` flags override an EXPECTED value, not the
input; AC "a doctored input it is given on its command line" is met through `--root PATH` / the log
path argument, which the input-doctored column exercised. Tasks 3/4/18 re-runs should use those.

## Suite floor (5c, outside sandbox)
`rtk proxy /opt/anaconda3/bin/python3 -m pytest h-mad/tests -q -p no:cacheprovider` →
`6042 passed, 1 warning in 1254.06s`; collect-only `6042 tests collected` (= plan M-1 at 17d73037).
