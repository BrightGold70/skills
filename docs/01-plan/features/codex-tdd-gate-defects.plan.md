# Plan: codex-tdd-gate-defects

## Executive Summary

Replace the two Phase-5 TDD gates' private resolvers, interpreters and rc-scorers with one shared
judge, so that a production write is allowed only when a failing test has been measured for it, on
the Codex host and on the Claude host alike. The work starts by committing the reproductions and
measuring Claude Code's blocking contract (V-0), because the Claude gate's blocking form cannot be
chosen until that reading exists.

## Overview

Spec v1.0 (`cf7e194f`) is operator-approved, and every open decision OD-1 through OD-7 was accepted
as the spec recommends. The defects are live: at `01121ca7` the Codex gate allows a write with a
**passing** test whenever its interpreter lacks pytest, allows a sub-project write with no test run
when a nearer state file has no step5 record, and the Claude gate never reads Claude Code's
`tool_input.file_path` (P3 below reproduces each, with a control). This feature merges first of
the three in-flight `h-mad/` features because it closes a live safety gap.

## Scope

In scope, by file (every path verified present at `01121ca7` with `ls`, except the new judge):

| File | Change | Spec |
|---|---|---|
| `h-mad/scripts/<judge>.py` (new; the design names it) | shared judge: chain reader, resolver, interpreter selection, scorer, CLI | FR-1–FR-5 |
| `h-mad/hooks/h-mad-codex-tdd-gate.py` | imports the judge; `_relative_target` gains the payload-`cwd` base; `_derived_test`, `_test_exit` and `_target_phase5_status` are removed; shell policy admits a contained `.venv` interpreter | FR-3, FR-5 |
| `h-mad/hooks/h-mad-tdd-gate.sh` | payload read; calls the judge CLI; one blocking form at every refusal site | FR-6 |
| `h-mad/scripts/h_mad_wire_pin_gate.py` | `_parse_tasks` extended in place with `production` and `tests` | FR-2, OD-7 |
| `h-mad/scripts/h_mad_audit_gate.py` | `_suite_summary` extended in place; `run_suite`'s one scoring change | FR-4, OD-7 |
| `h-mad/references/codex-runtime.md` | §"Trust boundary" | FR-7 |
| `h-mad/SKILL.md`, `h-mad/references/agy-runtime.md` | registry entry for the judge; the gate prose the change makes false (see "Stale-prose census") | invariant §"Skill manifest integrity" — **not named by the spec**, see Open Questions OQ-2 |
| `h-mad/tests/` | new test modules; the named updates only | FR-8 and the ACs |
| `h-mad/tests/mutation-specs/` | new specs for every FR-8 guard; the audit-gate spec re-anchored if `run_suite` moves | FR-8 |
| `docs/03-analysis/probes/codex-tdd-gate-defects/` | the reproduction probe and V-0 (step P0) | spec §"Measured premises", AC-0.1 |

## Goals

- G0 — Commit the reproductions and settle the Claude blocking contract before FR-6's form is built (FR-0, AC-0.1, AC-0.2).
- G1 — One judge decides for both gates; neither gate keeps a resolver, interpreter or scorer (FR-1).
- G2 — The impl-plan Task names the test; the name map is the fallback; otherwise deny with both sources named (FR-2).
- G3 — pytest runs under the nearest contained `.venv`, never under a venv that escapes the root (FR-3).
- G4 — The verdict comes from pytest's summary line; rc selects nothing (FR-4).
- G5 — The Codex gate resolves a relative target against the payload `cwd` and reads state along the whole chain (FR-5).
- G6 — The Claude gate reads Claude Code's real payload, is judged by the same unit, and refuses in a form Claude Code honours (FR-6).
- G7 — The trust boundary is documented (FR-7), and every new guard is mutation-tested (FR-8).

## Requirements

FR-0 through FR-8 of `docs/01-plan/features/codex-tdd-gate-defects.spec.md` v1.0, with OD-1…OD-7
resolved as the spec recommends. V-0 is a Phase-5 prerequisite of FR-6's blocking form. V-1 is
blocked on `multi-host-runtime` (`ls ~/.agents/skills/h-mad` → "No such file or directory", run at
`01121ca7`) and is not a merge condition of this feature.

## Implementation Strategy

**Seven layers, bottom-up; each is testable offline.**

1. **P0 — probes.** Commit `reproduce.py` and `v0-blocking-contract.sh` (Convention Prerequisites,
   step P0). Run V-0 and commit its reading. Nothing in layer 6's blocking form starts before this.
2. **Parsers, extended in place (OD-7).** `_parse_tasks` gains `production` and `tests` list fields
   under the spec's label and value axes. `_suite_summary` gains independent `failed`, `passed`,
   `errors` counts and a `no tests ran` reading. Every existing caller keeps its current result,
   except for the single `run_suite` change the spec names; the table under "Regression census"
   is the contract and is pinned cell by cell.
3. **The judge.** A pure core that takes (root, absolute target, ACTIVE features with their state
   files) and returns a verdict and `kind`, plus a CLI that prints exactly one `TDD-JUDGE:` line.
   The chain reader lives here too, so both gates call one state reader (OD-3).
4. **Codex gate.** Import the judge. `_relative_target` resolves against a payload `cwd` inside the
   root (OD-2). Any exception on the main path becomes `_deny(...)` with `judge-error` (AC-5.4).
5. **Shell policy.** `_trusted_executable` admits `<D>/.venv/bin/python*` under FR-3's containment
   rule; the argv rules are unchanged.
6. **Claude gate.** Read `tool_input.file_path`, then top-level `file_path`, then `$1` (OD-4). After
   the exemptions and the Codex-authorship check, call the judge CLI for every governed `.py` write,
   whether or not the target exists (OD-5). The blocking form follows V-0's reading (AC-6.5 /
   AC-6.6 / AC-6.7).
7. **Docs and mutation specs.** FR-7, the stale-prose census below, and the FR-8 specs.

**The judge is found relative to the hook's own resolved path, never through `$HOME/.claude/skills`.**
The Claude gate today hard-wires `DERIVE_SCRIPT="$HOME/.claude/skills/h-mad/scripts/h_mad_derive_test_path.sh"`,
and `~/.claude/skills/h-mad` is a symlink to this checkout's `h-mad/` (`ls -la ~/.claude/skills/h-mad`
→ `/Users/kimhawk/orca/skills/h-mad`, run at `01121ca7`). A worktree's hook would therefore call the
**main tree's** judge, which does not exist until merge: every worktree test of the Claude gate would
read `judge-error`, green for the wrong reason. The installed hook is itself a symlink
(`readlink -f ~/.claude/hooks/h-mad-tdd-gate.sh` → `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh`),
so the hook resolves its own path through the symlink (`python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "${BASH_SOURCE[0]}"`,
since the hook already requires `python3`) and takes `../scripts/` from there. The Codex gate
already does this (`Path(__file__).resolve().parents[1]` in `_derived_test`). A test runs the
worktree hook through a symlink placed outside the tree and asserts that the worktree judge ran.
**Residual:** a copied (not symlinked) hook finds no judge and denies `judge-error`; that is
fail-closed and stated in the SKILL.md install line.

**Refusal sites are an axis, not a list.** Every refusal the Claude gate can emit — the
Codex-authorship BLOCK, every judge DENY and `judge-error` — goes through one function that emits
the chosen form, and no other exit path refuses. Census at `01121ca7`:

```bash
grep -c '^\s*exit 1\s*$' h-mad/hooks/h-mad-tdd-gate.sh      # 5 (unit: matching lines)
grep -c 'BLOCK:' h-mad/hooks/h-mad-tdd-gate.sh              # 5 (unit: matching lines)
grep -c 'exit 2\|permissionDecision' h-mad/hooks/h-mad-tdd-gate.sh   # 0 (unit: matching lines)
```

These counts **move by construction**: after FR-6, four of today's five sites (derivation script
missing, cannot derive, no test file, test already passing) are replaced by the judge call, and the
Codex-authorship site remains. Re-measure at the 5g diff review. The pass condition is AC-6.5's
(`grep -c '^\s*exit 1\s*$'` → 0) or AC-6.6's (every site asserted rc 1 and the prefix), never a
carried count. **Residual:** a refusal written as `exit 1` inside a compound line (`… || exit 1`)
escapes the anchored grep; the per-site tests are the backstop.

**The run_suite change is stated as a table, not a sentence.** Today's behaviour is measured
(P6); the after-column is the spec's one change plus what extending the parser necessarily moves.

**What we deliberately do not touch:** `h_mad_derive_test_path.sh`'s three prefixes;
`_any_phase5_status` (shell policy); the Claude gate's no-state, no-`jq` and exemption fail-opens;
the `codex_status` / `HMAD_CODEX_UNAVAILABLE` escapes; the audit gate's exit-check logic.

## Verified premises (commands run at `01121ca7`)

Each was executed against the tree in this revision. A reading is one reading at one sha. The spec
read the tree at `ae7593a1`; `git diff --name-only ae7593a1 01121ca7 -- h-mad/hooks
h-mad/scripts/h_mad_wire_pin_gate.py h-mad/scripts/h_mad_audit_gate.py
h-mad/scripts/h_mad_derive_test_path.sh | wc -l` → 0 files (run at `01121ca7`), so the gate code
did not move in between; the premises below were re-run anyway rather than inferred from it.

- **P1 — Codex gate symbols.** `grep -n '^def \(_deny\|_project_root\|_target_phase5_status\|_any_phase5_status\|_relative_target\|_trusted_executable\|_safe_shell_command\|_derived_test\|_test_exit\)' h-mad/hooks/h-mad-codex-tdd-gate.py`
  lists all nine. `_test_exit` sends stdout and stderr to DEVNULL and runs `sys.executable`;
  `main` refuses when `test_exit != 1` (`grep -n 'test_exit != 1' h-mad/hooks/h-mad-codex-tdd-gate.py`
  → 1 matching line). `_target_phase5_status` returns the status of the **nearest** state file.
- **P2 — Claude gate.** The stdin branch reads `d.get('file_path', d.get('path', ''))`
  (`grep -n "d.get('file_path'" h-mad/hooks/h-mad-tdd-gate.sh` → 1 matching line). The pytest run
  is bare `pytest`, guarded by `[ -f "$TARGET_PATH" ]` (`grep -n 'if \[ -f "\$TARGET_PATH" \]' h-mad/hooks/h-mad-tdd-gate.sh`
  → 1). `ACTIVE` is the **first** step5 key (`grep -c 'head -1' h-mad/hooks/h-mad-tdd-gate.sh` →
  1 matching line) — the judge's chain reader replaces this for resolution; the Codex-authorship
  check keeps reading `codex_status` for that one key, unchanged.
- **P3 — reproductions, each with a control.** `python3 docs/03-analysis/probes/codex-tdd-gate-defects/reproduce.py . /opt/homebrew/bin/python3 /opt/anaconda3/bin/python`
  (the probe is committed at step P0; its bytes were run from scratch at `01121ca7`). Reading
  (unit: one `REPRO:` line per case; timings and temp paths vary and are not part of the reading):

  | Case | Reading | Control | Control reading |
  |---|---|---|---|
  | D3 — Codex gate under a python with no pytest, passing test | rc 0, **allow** | same, python with pytest | deny, "returned pytest exit 0" |
  | OD-2 — `cwd` = sub-project, target `tools/w.py` | deny, "requires a failing test before tools/w.py; no derived test file exists" | — | — |
  | OD-3 — root state step5, sub-project state without step5, passing test | **allow** | no sub-project state | deny, "returned pytest exit 0" |
  | OD-4 — Claude gate, `{"tool_input":{"file_path":…}}` | rc 0, no stderr | top-level `file_path` | rc 1, Codex-authorship BLOCK |
  | D1 — Claude gate, absolute path, codex exhausted | rc 1, "cannot derive test path" | — | — |
  | OD-5 — Claude gate, codex exhausted, no `pytest` on PATH, passing test | rc 0, **allow** | `pytest` on PATH | rc 1, "already passing" |
  | pytest 9.1.1 final lines | RED rc 1 `1 failed`; GREEN rc 0 `1 passed`; import error rc 2 `1 error`; empty rc 5 `no tests ran`; no pytest rc 1 `No module named pytest` | — | — |

- **P4 — `_parse_tasks` has three consumers, not two.**
  `git grep -n "_parse_tasks" -- h-mad handoff ':!h-mad/tests/fixtures' | grep -v '^h-mad/scripts/h_mad_wire_pin_gate.py'`
  → `h-mad/scripts/h_mad_assemble_tdd.py` (2 matching lines), `h-mad/scripts/h_mad_wire_registry.py`
  (2 matching lines), `h-mad/SKILL.md` (1 prose line). The spec's AC-2.9 names only the wire-pin
  gate's and the assembler's tests. **The tree adds `h_mad_wire_registry`**; this plan holds its
  tests to the same "pass unmodified" rule (Success Criteria) and reports the gap to the spec.
- **P5 — `_suite_summary` has one caller.** `git grep -n "_suite_summary" -- h-mad handoff ':!h-mad/tests/fixtures'`
  → matches in `h-mad/scripts/h_mad_audit_gate.py` only (its definition and `run_suite`). Its return
  shape can change without a second call site. `run_suite` has two callers:
  `git grep -n "run_suite(" -- h-mad/scripts` → `h_mad_audit_gate.py` (its definition and `main`)
  and `h_mad_audit_cycle.py` (1 call).
- **P6 — `run_suite` today.** Measured by `reproduce.py`'s `run_suite` stanza (stub suites printing
  one line and exiting 1). See the table under "Regression census".
- **P7 — the named existing tests exist.** `grep -n 'def test_codex_hook_rejects_untrusted_executable_paths\|def test_codex_hook_scopes_nested_state_to_the_target_project\|def test_codex_hook_rejects_pytest_no_tests_collected_as_red\|def test_codex_hook_resolves_git_root_from_nested_cwd\|def test_codex_adapter_states_pytest_trust_boundary' h-mad/tests/test_h_mad_codex_runtime.py`
  → 5 matching lines.
- **P8 — interpreters.** `/opt/homebrew/bin/python3 -c 'import pytest'` → `ModuleNotFoundError`;
  `/opt/anaconda3/bin/python -m pytest --version` → `pytest 9.1.1`; bare `python3` resolves to
  `/opt/homebrew/bin/python3` (`which python3`). This repository has no `.venv`
  (`ls .venv/bin/python` → no such file). Consequence in Risks (R4) and OQ-1.
- **P9 — HemaSuite layout, re-read at HemaSuite `69ac6210`** (the spec read `ffa87323`).
  `python3 -c "import os;print(os.path.realpath('/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/.venv/bin/python'))"`
  → `/opt/homebrew/Cellar/python@3.14/3.14.7/…/python3.14` (outside the root; OD-1 stands). The
  step5 record is in the root `docs/.bkit-memory.json` (feature `review-manifest-guideline-evidence`);
  the sub-project state file has no step5 record (read with `json.load`; OD-3 stands).
- **P10 — install.** `grep -n 'tdd-gate' ~/.claude/settings.json` → one registration,
  `"$HOME/.claude/hooks/h-mad-tdd-gate.sh"`, no argument. The hook link resolves into this
  checkout (layer 6 above).

## Regression census for OD-7 (`run_suite` scoring)

**Question:** which existing tests, mutation specs, stamps or documents depend on a summary with
failures and no passes reading `UNREADABLE no_summary`? Every command below ran at `01121ca7`.

**Behaviour today and after** (today = P6 reading; after = spec FR-4 plus what the parser
extension necessarily moves). Each row becomes one parametrized test case in the audit-gate
suite, with its own stub:

| Final line | `_suite_summary` today | `run_suite` today | `run_suite` after | Why |
|---|---|---|---|---|
| `3 failed in 0.10s` | `None` | UNREADABLE `no_summary` | **FAIL** | the spec's one change |
| `3 failed, 1 skipped in 0.1s` | `None` | UNREADABLE `no_summary` | **FAIL** | same class: failures, no passes |
| `1 failed, 1 error in 0.1s` | `None` | UNREADABLE `no_summary` | **FAIL** | same class; see OQ-3 |
| `1 error in 0.06s` | `None` | UNREADABLE `no_summary` | UNREADABLE `no_summary` | not in the spec's change; kept |
| `no tests ran in 0.01s` | `None` | UNREADABLE `no_summary` | UNREADABLE **`no_tests_ran`** | the parser now reads it; reason string moves, verdict does not |
| `2 passed, 1 error in 0.1s` | `(2, 0)` | **PASS** | PASS | kept by the spec's "existing callers keep their results"; see OQ-3 |
| `1 failed, 11 passed in 0.2s` | `(11, 1)` | FAIL | FAIL | unchanged |
| `collected 0 items` (no summary) | `None` | UNREADABLE `no_summary` | UNREADABLE `no_summary` | unchanged |

The `1 error` row needs an explicit branch: once the parser returns counts for it, `run_suite`'s
`passed == 0 and failed == 0` test would otherwise catch it and re-label it `no_tests_ran`, which is
false (tests were collected and errored). The design names that branch and its mutation.
The `no tests ran` row is a change the spec does not name: once the parser reads that line,
`run_suite`'s existing `no_tests_ran` branch catches it instead of the `no_summary` branch. It is
the same verdict and a more accurate reason; this plan adopts it and names it here so it is not
discovered at 5g.

**Tests that pin today's behaviour.**

```bash
git grep -n "no_summary\|no_tests_ran\|SUITE: UNREADABLE\|SUITE: FAIL" -- h-mad/tests handoff ':!h-mad/tests/fixtures'
# reading at 01121ca7: 10 matching lines — test_h_mad_audit_suite_gate.py 7,
#   mutation-specs/audit_suite_gate.json 2, and test_h_mad_archreview_cycle.py 1
#   (an unrelated `no_summary_slot.md` fixture name).
git grep -n -E '"[0-9]+ (failed|error|errors)( in|,)|no tests ran' -- h-mad/tests handoff ':!h-mad/tests/fixtures'
# reading at 01121ca7: every stub summary that carries "failed" also carries "passed"
#   ("1 failed, 11 passed", "2 failed, 5 passed", "1 failed, 8 passed"); the one
#   "no tests ran" stub is test_a_run_that_says_only_no_tests_ran_is_also_refused.
```

Result: **no existing test feeds a failures-without-passes summary**, so none pins the
`3 failed` → UNREADABLE behaviour AC-4.7 anticipated; AC-4.7's "that test is updated" has no
member, and the impl-plan says so rather than inventing one. Two tests sit next to the change and
must pass **unmodified**: `test_no_summary_is_UNREADABLE_not_PASS_and_not_FAIL` (stub prints
`collected 0 items`, still no summary) and `test_a_run_that_says_only_no_tests_ran_is_also_refused`
(asserts only "not PASS", still true). The docstring of `test_an_empty_selection_is_not_a_pass`
states that a `no tests ran` stub "never reaches the verdict logic at all"; after the change it
does, so that sentence becomes false. It is prose in a test, not an assertion — the impl-plan
names it as a docstring correction under §"Regression provenance", citing what it asserted.

**Mutation specs anchored inside `run_suite`.** `h-mad/tests/mutation-specs/audit_suite_gate.json`
anchors three mutations on `run_suite` source lines (the `verdict = "PASS" if failed == 0 and passed > 0 else "FAIL"`
line, the `if passed == 0 and failed == 0:` line, and the `no_summary` return). Anchor state before:

```bash
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json | tail -1
# reading at 01121ca7: ANCHORS: ANCHORS_OK specs=99 mutations=907 ok=907 drifted=0 unreadable=0 skipped=0 unclassifiable=0
```

Rule: the `run_suite` edit keeps those three lines byte-identical where it can; any that must move
is re-anchored **in the same commit**, and the re-anchored mutation is re-run and must still be
CAUGHT by the same test. `ANCHORS_OK` with `drifted=0` is a 5g gate; the `specs=`/`mutations=`
figures grow by construction when FR-8's specs land and are re-read then, never carried.

**Stamps.** A stamp records `run_suite`'s verdict string as `"suite"`, and `--exit-check` maps any
non-PASS value to `BLOCKED` (`suite_fail:` for FAIL, `suite_unreadable:` for UNREADABLE). The
change therefore moves a new stamp from `UNREADABLE` to `FAIL` and an `EXIT:` reason from
`suite_unreadable` to `suite_fail`; both block, and no PASS flips (invariant §"Backward
compatibility"). Committed stamps carrying `UNREADABLE`:

```bash
git ls-files -z '*.gated.json' | xargs -0 grep -l 'UNREADABLE' | wc -l
# reading at 01121ca7 (skills): 0 files, of 25 tracked stamps (git ls-files '*.gated.json' | wc -l)
# same command at HemaSuite 69ac6210: 0 files, of 124 tracked stamps
```

No committed stamp is re-scored by this change (stamps are read, never re-derived).

**Documents.** `h-mad/SKILL.md`'s #91 bullet says `SUITE: UNREADABLE reason=no_summary` is a
cannot-judge; that stays true. `git grep -n "suite_unreadable" -- h-mad handoff` → 0 matching
lines at `01121ca7` (the reason is built by f-string), so no prose names the reason that moves.

## Stale-prose census (FR-6 blocking form, FR-1 judge)

```bash
git grep -c "h-mad-tdd-gate\|h-mad-codex-tdd-gate\|h_mad_derive_test_path\|exit-code protocol" -- h-mad handoff ':!h-mad/tests' ':!*/archive/*'
# reading at 01121ca7 (unit: matching lines per file): h-mad/SKILL.md 6, h-mad/hooks/h-mad-codex-tdd-gate.py 1,
#   h-mad/hooks/h-mad-tdd-gate.sh 4, h-mad/references/agy-runtime.md 2, h-mad/references/codex-implementer-prompt.md 1,
#   h-mad/references/codex-runtime.md 2, h-mad/scripts/h_mad_derive_test_path.sh 2,
#   h-mad/scripts/h_mad_hook_wiring.py 1, h-mad/scripts/h_mad_install_check.py 3
```

Each non-code match is a **candidate**, re-read at 5g against the shipped gate. Known to go false:
`h-mad/references/agy-runtime.md` §"The TDD gate" says the Claude gate "is written to Claude Code's
exit-code protocol" — false under AC-6.5 form (b). `h-mad/SKILL.md`'s script registry lists
`h_mad_derive_test_path.sh` as the mapper, and the judge must be registered beside it.
**Residual:** prose that describes the gate without naming a file is outside this grep; the
design's doc-test pins the new wording by heading, not by the old text's absence (invariant §"Both
halves of a doc change").

## Architecture Considerations

- **Single-source contract.** One chain reader, one resolver, one scorer, called by both gates.
  The Codex gate imports the judge; the Claude gate runs its CLI and parses one line. No gate keeps
  a private fallback (AC-1.1: `git grep -n "h_mad_derive_test_path.sh" -- h-mad/hooks` → no match).
- **The CLI boundary fails closed in both directions.** Zero lines, two lines, an unknown verb or
  an unknown `kind` are `judge-error` DENY (AC-1.3). The Claude gate reads the token, never `$?`.
- **Import failure in the Codex gate** must still print a JSON deny with rc 0 (AC-5.4): the
  judge import sits inside the guarded main path, not at module top level.
- **Self-containment.** The judge is stdlib-only and lives under `h-mad/scripts/`; the hooks reach
  it by their own resolved path (Implementation Strategy). pytest is the only non-stdlib tool, and
  it is already a declared dependency.
- **No knob.** No environment variable or config key is added (spec NFR Security).
- **Time bound.** The judge bounds pytest with `subprocess.run(timeout=…)`, never `timeout`/`gtimeout`
  (invariant §"Portable time bounds"). The design owns the value and the latency measurement.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| `reproduce.py` + reading, `v0-blocking-contract.sh` + reading, captured payload, replay rcs, `claude --version` | probe | AC-0.1, AC-0.2 |
| Shared judge module + CLI (`TDD-JUDGE:` token) | module / CLI | FR-1–FR-4 |
| `_parse_tasks` `production` / `tests` fields | module | FR-2 |
| `_suite_summary` counts incl. errors and `no tests ran`; `run_suite` table above | module | FR-4 |
| Codex gate rewiring, `cwd` base, chain reader, venv shell policy | hook | FR-3, FR-5 |
| Claude gate payload read, judge call, blocking form | hook | FR-6 |
| §"Trust boundary" text; SKILL.md registry + gate bullets; agy-runtime.md sentence | docs | FR-7, OQ-2 |
| One mutation spec per FR-8 guard, plus wire mutations (below) | mutation specs | FR-8 |

## Connection enforcement (the feature is partly wiring-shaped)

Each wire ships a test that fails when the connection alone is removed with the callee intact, and
is mutated in both directions (invariant §"Connection enforcement").

| Wire | Remove → must fail | Force → must fail |
|---|---|---|
| W1 Codex gate → judge | a RED-measured fixture is no longer ALLOWED (AC-4.2) | a GREEN fixture is ALLOWED (AC-4.2 `test-passing`) |
| W2 Claude gate → judge CLI | AC-6.3/AC-6.4 allow again | a governed RED write is refused |
| W3 judge → `_parse_tasks` fields | AC-2.1 resolves by name map or not at all | AC-2.5 (Task authority) inverts |
| W4 judge → `_suite_summary` | AC-4.4 (rc-blindness) fails | AC-4.2 GREEN reads RED |
| W5 both gates → chain reader | AC-5.2 allows again (the OD-3 fail-open) | the sibling-project case of `test_codex_hook_scopes_nested_state_to_the_target_project` denies |
| W6 Claude gate → hook-relative judge path | the symlinked-hook test runs no judge / the main tree's | — (a path has no "force" direction; stated) |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| R1 — V-0 reads `INCONCLUSIVE` | FR-6's blocking form cannot ship (AC-6.7) | AC-6.1–AC-6.4 still ship; the halt reason from the probe is fixed and V-0 re-run; merge does not wait on it, the FR-6 form task does |
| R2 — grok-codex-fallback's impl-plan asserts the Claude gate's `exit 1` | After this merges with form (b), its BLOCK-GROK / BLOCK-INVALID tests and mutation anchors assert a form the gate no longer uses | `grep -n 'exit 1' docs/01-plan/features/grok-codex-fallback.impl-plan.md \| grep -c 'BLOCK\|;;\|gate_matrix\|rc'` → 10 matching lines at `01121ca7`; owed to that impl-plan (report). Its new refusals must use this feature's refusal function |
| R3 — `_parse_tasks`' dict gains keys | A consumer that iterates or serialises the dict changes output | P4's three consumers' suites run unmodified; the new keys are additive |
| R4 — no `.venv` in a governed project and the hook's `python3` has no pytest | Every Claude-fallback write in this repository is DENY `pytest-missing` (P8) — fail-closed but blocking | Deny reason names the remedy (create a contained `.venv`); OQ-1 to the operator. No knob (spec) |
| R5 — the worktree hook calls the main tree's scripts | Tests green for the wrong reason | Hook-relative judge path + W6 test |
| R6 — a pre-existing test is deleted or weakened while counts stay green | Compatibility NFR silently false | Node-id floor (Success Criteria), not a count |
| R7 — the run_suite edit drifts `audit_suite_gate.json` anchors | A guard stops being mutation-tested | `--check-anchors` at 5g, re-anchor in the same commit |
| R8 — the V-0 session writes the sentinel through a tool other than Write | A false `E1_DOES_NOT_BLOCK` | `--tools Write`; the hook logs each invocation and an arm with no invocation halts `UNMEASURED` |

## Convention Prerequisites

- **Worktree.** `~/.claude/skills/h-mad` is a live symlink into this checkout (P10), so the
  implementation runs in `git worktree add ../skills-codex-tdd-gate-defects -b feature/codex-tdd-gate-defects`
  from the base recorded in the state record at 5c. No edit of `h-mad/` happens in the main
  checkout. At `01121ca7`, `git branch -a | grep -E 'grok|codex-tdd|multi-host'` → no output and
  `git worktree list` → the main checkout only.
- **Interpreter and suites.** Every pytest command is `/opt/anaconda3/bin/python -m pytest … -p no:cacheprovider`
  (P8), with the coupled suites named explicitly: `h-mad/tests handoff/tests handoff/scripts`.
  Collection at `01121ca7`, `… --collect-only -q <dir> | tail -1`: `h-mad/tests` 3552,
  `handoff/tests` 201, `handoff/scripts` 140, all three together 3893 (unit: tests collected).
  Full run at `01121ca7` (`/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts | tail -1`):
  `1 failed, 3892 passed, 1 warning in 605.79s`. The one failure is
  `h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`,
  which reads the installed `claude` binary and is outside this feature's files; it is the only
  failure a task may leave, and only for that reason (the grok-codex-fallback impl-plan carries the
  same carve-out). These figures move with every merge ahead of this branch and are re-measured at
  the worktree's base.
- **Merge order: this feature → `grok-codex-fallback` → `multi-host-runtime`.** Shared files,
  derived from the sibling documents at `01121ca7` (grok: `git show HEAD:docs/01-plan/features/grok-codex-fallback.impl-plan.md | grep -oE '\*\*(Production|Test) file\*\*:.*' | grep -oE '`[^`]+`' | tr -d '`' | sort -u | grep -v /tests`;
  multi-host: its plan's §"Convention Prerequisites" table):

  | File | This feature | `grok-codex-fallback` | `multi-host-runtime` |
  |---|---|---|---|
  | `h-mad/hooks/h-mad-tdd-gate.sh` | edits (payload, judge, form) | edits (`fallback_agent`, BLOCK-GROK/INVALID) | reads (grok adapter AC-5.2) |
  | `h-mad/hooks/h-mad-codex-tdd-gate.py` | edits | not touched (its plan) | reads |
  | `h-mad/references/codex-runtime.md` | edits §"Trust boundary" | not a production file | edits |
  | `h-mad/SKILL.md` | edits (registry, gate bullets) | edits | edits |
  | `h-mad/references/agy-runtime.md` | edits one sentence (if form (b)) | not a production file | edits (construct mapping) |
  | `h-mad/scripts/h_mad_audit_gate.py` | edits | not a production file | not named |
  | `h-mad/scripts/h_mad_wire_pin_gate.py` | edits | not a production file | not named |
  | `h-mad/scripts/h_mad_assemble_tdd.py` | reads (`_parse_tasks` consumer) | edits | not named |
  | `h-mad/scripts/h_mad_audit_cycle.py` | reads (`run_suite` consumer) | edits | not named |

  Textual overlaps: the Claude hook, `SKILL.md`, `codex-runtime.md`, `agy-runtime.md`. Semantic
  overlaps: grok's edits to the two consumers of the functions this feature extends. The later
  features rebase onto this one and re-run their own premises; multi-host-runtime's table still
  says this feature does not name `h-mad/SKILL.md`, which this plan changes (owed, report).
- **Step P0 — commit the probes** (owed by the orchestrator since the spec; spec §"Measured
  premises" and AC-0.1 cite the directory). From the repository root, in the main checkout (docs
  only), before the worktree is cut:

  ```bash
  D=docs/03-analysis/probes/codex-tdd-gate-defects
  cat > "$D/reproduce.py" <<'PY'
#!/usr/bin/env python3
"""Re-derive the codex-tdd-gate-defects spec premises against a skills tree.

Usage: reproduce.py <skills-root> <python-without-pytest> <python-with-pytest>
Prints one `REPRO:` line per reading. Scratch fixtures live in a TemporaryDirectory.
"""
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

SK, NOPY, WITHPY = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
CODEX_GATE = SK / "h-mad/hooks/h-mad-codex-tdd-gate.py"
CLAUDE_GATE = SK / "h-mad/hooks/h-mad-tdd-gate.sh"
PASSING = "def test_ok():\n    assert True\n"


def fixture(base: Path, sub_state: bool, codex_status: str | None = None) -> Path:
    root = base / "repo"
    (root / "docs").mkdir(parents=True)
    rec = {"phase": "step5"}
    if codex_status:
        rec["codex_status"] = codex_status
    (root / "docs/.bkit-memory.json").write_text(json.dumps({"orchestrator_state": {"feat": rec}}))
    hpw = root / "hematology-paper-writer"
    (hpw / "tools").mkdir(parents=True)
    (hpw / "tests").mkdir()
    (hpw / "tools/w.py").write_text("X = 1\n")
    (hpw / "tests/test_w.py").write_text(PASSING)
    if sub_state:
        (hpw / "docs").mkdir()
        (hpw / "docs/.bkit-memory.json").write_text(json.dumps({"orchestrator_state": {}}))
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root.resolve()


def codex(py: str, root: Path, payload: dict, env_root: bool = True, cwd: Path | None = None):
    env = {k: v for k, v in os.environ.items() if k != "CODEX_PROJECT_DIR"}
    if env_root:
        env["CODEX_PROJECT_DIR"] = str(root)
    r = subprocess.run([py, str(CODEX_GATE)], input=json.dumps(payload), text=True,
                       capture_output=True, cwd=cwd or root, env=env)
    out = r.stdout.strip()
    verdict = "deny" if '"deny"' in out else ("allow" if out in ("", "{}") else "other")
    reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"] if verdict == "deny" else ""
    return r.returncode, verdict, reason


def patch(target: str) -> dict:
    return {"tool_name": "apply_patch", "tool_input": {"patch": f"*** Update File: {target}\n"}}


def bindir(base: Path, with_pytest: bool) -> Path:
    b = base / ("bin_py" if with_pytest else "bin_nopy")
    b.mkdir()
    (b / "codex").write_text("#!/bin/sh\nexit 0\n")
    (b / "codex").chmod(0o755)
    for tool in ("jq", "python3", "git", "dirname", "cat", "basename"):
        found = shutil.which(tool)
        if found:
            (b / tool).symlink_to(found)
    if with_pytest:
        (b / "pytest").write_text(f'#!/bin/sh\nexec "{WITHPY}" -m pytest "$@"\n')
        (b / "pytest").chmod(0o755)
    return b


def claude(root: Path, b: Path, arg: str | None = None, stdin: str = ""):
    env = {"HOME": os.environ["HOME"], "PATH": f"{b}:/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(root)}
    argv = ["bash", str(CLAUDE_GATE)] + ([arg] if arg else [])
    r = subprocess.run(argv, input=stdin, text=True, capture_output=True, cwd=root, env=env)
    return r.returncode, (r.stderr.strip().splitlines() or [""])[0][:90]


def run(label, fn):
    with tempfile.TemporaryDirectory() as t:
        print(f"REPRO: {label} {fn(Path(t))}")


t_rel = "hematology-paper-writer/tools/w.py"
# D3: passing test, gate interpreter without pytest -> allowed (fail-open). Control: with pytest.
run("D3 nopytest", lambda t: codex(NOPY, fixture(t, False), patch(t_rel)))
run("D3 control-withpytest", lambda t: codex(WITHPY, fixture(t, False), patch(t_rel)))
# OD-2: cwd-relative target from the sub-project cwd, root found by git from payload cwd.
run("OD-2 cwd-relative", lambda t: (lambda r: codex(WITHPY, r, {**patch("tools/w.py"), "cwd": str(r / "hematology-paper-writer")},
                                                   env_root=False, cwd=r / "hematology-paper-writer"))(fixture(t, False)))
# OD-3: root state step5, sub-project state without step5, passing test -> allowed. Control: no sub state.
run("OD-3 nearest-state", lambda t: (lambda r: codex(WITHPY, r, patch(str(r / t_rel))))(fixture(t, True)))
run("OD-3 control-nosubstate", lambda t: (lambda r: codex(WITHPY, r, patch(str(r / t_rel))))(fixture(t, False)))
# OD-4: Claude-Code-shaped payload vs top-level file_path, codex on PATH.
run("OD-4 tool_input", lambda t: (lambda r: claude(r, bindir(t, True), stdin=json.dumps(
    {"tool_name": "Write", "tool_input": {"file_path": str(r / t_rel)}})))(fixture(t, False)))
run("OD-4 control-toplevel", lambda t: (lambda r: claude(r, bindir(t, True), stdin=json.dumps(
    {"file_path": str(r / t_rel)})))(fixture(t, False)))
# D1: absolute path into the Claude gate's name map (codex declared exhausted).
run("D1 claude-absolute", lambda t: (lambda r: claude(r, bindir(t, True), arg=str(r / t_rel)))(fixture(t, False, "exhausted")))
# OD-5: codex exhausted, relative derivable target, passing test, no pytest on PATH -> allowed.
run("OD-5 nopytest", lambda t: (lambda r: claude(r, bindir(t, False), arg=t_rel))(fixture(t, False, "exhausted")))
run("OD-5 control-withpytest", lambda t: (lambda r: claude(r, bindir(t, True), arg=t_rel))(fixture(t, False, "exhausted")))
# pytest final lines.
with tempfile.TemporaryDirectory() as t:
    for name, body in (("red", "def test_x():\n    assert False\n"), ("green", PASSING),
                       ("importerr", "import not_a_module_xyz\ndef test_x():\n    pass\n"), ("empty", "")):
        f = Path(t) / f"test_{name}.py"
        f.write_text(body)
        r = subprocess.run([WITHPY, "-m", "pytest", str(f), "-x", "-q", "--no-header", "-p", "no:cacheprovider"],
                           capture_output=True, text=True, cwd=t)
        last = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.strip()][-1]
        print(f"REPRO: summary {name} rc={r.returncode} last={last.strip()!r}")
    r = subprocess.run([NOPY, "-m", "pytest", "-q"], capture_output=True, text=True, cwd=t)
    print(f"REPRO: summary nopytest rc={r.returncode} last={(r.stderr.strip().splitlines() or [''])[-1]!r}")
# OD-7: how the audit gate's run_suite scores each summary shape today.
sys.path.insert(0, str(SK / "h-mad/scripts"))
import h_mad_audit_gate as gate  # noqa: E402
with tempfile.TemporaryDirectory() as t:
    for i, line in enumerate(("3 failed in 0.10s", "1 error in 0.06s", "2 passed, 1 error in 0.1s",
                              "1 failed, 1 error in 0.1s", "3 failed, 1 skipped in 0.1s",
                              "no tests ran in 0.01s", "1 failed, 11 passed in 0.2s")):
        sh = Path(t) / f"s{i}.sh"
        sh.write_text(f'#!/bin/sh\necho "{line}"; exit 1\n')
        sh.chmod(0o755)
        out = gate.run_suite(Path(t), [str(sh)])
        print(f"REPRO: run_suite {line!r} summary={gate._suite_summary(line)} "
              f"verdict={out['verdict']} reason={out.get('reason', '-')}")
PY
  shasum -a 256 "$D/reproduce.py" | grep -q '^4b8b36a31e20bf2b9ae03a8e6e35c6edf79ee11aebc8db59269449d4db4f3c08 ' || exit 1
  cat > "$D/v0-blocking-contract.sh" <<'SH'
#!/bin/bash
# V-0 (spec FR-0): does Claude Code refuse a Write when a PreToolUse hook exits 1?
# Run from a shell whose cwd is OUTSIDE every repository. Every halt is `exit 1`,
# and a halt means the reading is INCONCLUSIVE — never a pass.
S="$(mktemp -d "${TMPDIR:-/tmp}/hmad-v0.XXXXXX")" || exit 1
git -C "$S" rev-parse --show-toplevel >/dev/null 2>&1 && { echo "V-0: HALT scratch is inside a git repo"; exit 1; }
command -v jq >/dev/null || { echo "V-0: HALT no jq"; exit 1; }
claude --version > "$S/claude.version" || { echo "V-0: HALT claude --version"; exit 1; }

mkhook() {  # $1 = arm, $2 = rc on the sentinel ("" = capture arm)
  {
    printf '#!/bin/bash\np=$(cat)\nprintf "%%s\\n" "$p" >> %q\n' "$S/$1.invoked"
    if [ -z "$2" ]; then
      printf 'printf "%%s" "$p" > %q\nexit 0\n' "$S/payload.json"
    else
      printf 'f=$(printf "%%s" "$p" | jq -r ".tool_input.file_path // empty")\n'
      printf 'case "$f" in *SENTINEL_E1.py) echo "V-0 arm %s refuses" >&2; exit %s;; esac\nexit 0\n' "$1" "$2"
    fi
  } > "$S/hook.$1.sh" || exit 1
  chmod +x "$S/hook.$1.sh" || exit 1
  jq -n --arg c "$S/hook.$1.sh" \
    '{hooks:{PreToolUse:[{matcher:"Write",hooks:[{type:"command",command:$c}]}]}}' \
    > "$S/settings.$1.json" || exit 1
}

attempt() {  # $1 = arm; asks a real session to Write the sentinel, returns nothing
  mkdir "$S/$1" || exit 1
  (cd "$S/$1" && claude -p "Use the Write tool to create SENTINEL_E1.py in the current directory containing exactly: X = 1" \
      --settings "$S/settings.$1.json" --tools Write --permission-mode acceptEdits \
      --no-session-persistence --output-format json > "$S/$1.out.json" 2> "$S/$1.err")
  [ -s "$S/$1.invoked" ] || { echo "V-0: $1 UNMEASURED hook_never_invoked"; exit 1; }
}

mkhook cap ""; attempt cap
F=$(jq -r '.tool_input.file_path // empty' "$S/payload.json") || exit 1
case "$F" in *SENTINEL_E1.py) ;; *) echo "V-0: HALT captured payload has no sentinel file_path"; exit 1;; esac

for arm in E1:1 E2:2 E0:0; do
  a=${arm%%:*} want=${arm##*:}
  mkhook "$a" "$want"
  : > "$S/$a.invoked"   # the replay must not count as a real invocation
  "$S/hook.$a.sh" < "$S/payload.json" 2>/dev/null; rc=$?
  : > "$S/$a.invoked"
  echo "V-0: replay $a rc=$rc" | tee -a "$S/replay.txt"
  [ "$rc" = "$want" ] || { echo "V-0: $a UNMEASURED replay_rc=$rc want=$want"; exit 1; }
  attempt "$a"
done

p() { [ -e "$S/$1/SENTINEL_E1.py" ] && echo present || echo absent; }
E1=$(p E1) E2=$(p E2) E0=$(p E0)
case "$E1/$E2/$E0" in
  absent/absent/present)  R=E1_BLOCKS ;;
  present/absent/present) R=E1_DOES_NOT_BLOCK ;;
  *)                      R=INCONCLUSIVE ;;
esac
echo "V-0: READING=$R E1=$E1 E2=$E2 E0=$E0 claude=$(head -1 "$S/claude.version") scratch=$S"
SH
  shasum -a 256 "$D/v0-blocking-contract.sh" | grep -q '^90772a333cf4ca7e588e9c52e79692fc6cd60dc4ba579adcec8e6f899975af1a ' || exit 1
  SHA=$(git rev-parse --short HEAD) || exit 1
  python3 "$D/reproduce.py" . /opt/homebrew/bin/python3 /opt/anaconda3/bin/python > "$D/reproduce.reading.$SHA.txt" || exit 1
  test "$(grep -c '^REPRO:' "$D/reproduce.reading.$SHA.txt")" = 22 || exit 1
  grep -q "^REPRO: D3 nopytest (0, 'allow'" "$D/reproduce.reading.$SHA.txt" || exit 1
  grep -q "^REPRO: OD-3 nearest-state (0, 'allow'" "$D/reproduce.reading.$SHA.txt" || exit 1
  grep -q "^REPRO: OD-4 tool_input (0, '')" "$D/reproduce.reading.$SHA.txt" || exit 1
  grep -q "^REPRO: OD-5 nopytest (0, '')" "$D/reproduce.reading.$SHA.txt" || exit 1
  ```

  The 22 is the probe's own line count at `01121ca7` (15 gate and summary lines + 7 `run_suite`
  lines) — a property of the probe, not of the tree. After this feature merges, the four `allow` /
  silent readings are **expected to invert**; the probe is then the regression witness, and its
  post-merge reading is committed beside the first.
- **V-0 — the blocking-contract probe** (verification, not pytest). It needs a real Claude Code
  session and is run by the operator or orchestrator from a cwd outside every repository, after
  P0 and before the FR-6 blocking-form task:

  ```bash
  cd "${TMPDIR:-/tmp}" || exit 1
  bash /Users/kimhawk/orca/skills/docs/03-analysis/probes/codex-tdd-gate-defects/v0-blocking-contract.sh | tee v0.out || exit 1
  grep -q '^V-0: READING=\(E1_BLOCKS\|E1_DOES_NOT_BLOCK\) ' v0.out || exit 1
  ```

  Every precondition in the script is an explicit `|| exit 1` (scratch not in a git repo; `jq`;
  `claude --version`; the captured payload names `SENTINEL_E1.py`; each arm's hand replay returns
  1, 2, 0; each arm's hook was actually invoked). A halt, or `READING=INCONCLUSIVE`, fails the last
  `grep` and AC-6.7 applies. The script's logic was exercised offline at `01121ca7` against a fake
  `claude` that honours only rc≠0 (→ `E1_BLOCKS`), only rc 2 (→ `E1_DOES_NOT_BLOCK`), never writes
  (→ `INCONCLUSIVE`) and never invokes the hook (→ halt `cap UNMEASURED hook_never_invoked`); the
  real session was **not** run. Commit into the probe directory: `v0.out`, the scratch's
  `payload.json`, `replay.txt` and `claude.version`, stamped with the skills sha.
- **5c state.** The feature record carries the base sha, the V-0 reading and its sha.

## Success Criteria

- Every AC of spec FR-1…FR-8 passes through each hook's real entry point (stdin JSON, and for the
  Claude gate also the positional argument), with the AC-6.5 / AC-6.6 branch chosen by V-0.
- The `run_suite` table above passes cell by cell, one stub per row.
- The tests of `h_mad_wire_pin_gate`, `h_mad_assemble_tdd` **and `h_mad_wire_registry`** pass
  unmodified (P4).
- **Node-id floor, not a count.** At the worktree's base, `…/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts | grep '::' | sort > base.ids`;
  at 5g the same into `head.ids`; `comm -23 base.ids head.ids` must be empty, except for node ids
  the impl-plan names as changed under §"Regression provenance" (today: one —
  `test_codex_hook_rejects_pytest_no_tests_collected_as_red`'s assertion, AC-5.3; its node id is
  unchanged, so the list of *removed* ids is expected to be empty).
- `ANCHORS_OK` with `drifted=0` over every committed mutation spec; every FR-8 guard and every
  wire above CAUGHT, scored on the pytest summary, each alternation branch mutated alone.
- `python3 h-mad/hooks/h-mad-codex-tdd-gate.py --self-check` → `CODEX-TDD-GATE: PASS`.
- `reproduce.py`'s post-merge reading shows the four fail-open cases denied.

## Out-of-Scope (confirmed from spec)

- Installing `~/.agents/skills/h-mad` (owned by `multi-host-runtime`; V-1 depends on it).
- Changing the name map's three prefixes.
- How the grok host treats `exit 1` (owned by `multi-host-runtime`).
- The Claude gate's no-state, no-`jq` and file-type-exemption fail-opens.
- Venvs not named `.venv`, and `.venv/bin/pytest` as a shell entry point.

## Open Questions

- **OQ-1 (operator).** In a governed project with no `.venv` whose hook `python3` lacks pytest —
  this repository today (P8) — every Claude-fallback production write will be DENY
  `pytest-missing`. The spec's "no venv → the judge's own interpreter" makes that so. Accept it
  (fail-closed; remedy in the deny reason), or amend the spec?
- **OQ-2 (spec).** The spec names no `SKILL.md` or `agy-runtime.md` change, but the invariant
  §"Skill manifest integrity" requires the gate's documented contract to follow its behaviour, and
  the stale-prose census finds at least one sentence that goes false. This plan includes them;
  FR-7 should say so.
- **OQ-3 (operator).** `run_suite` scores `2 passed, 1 error` as PASS today (P6) — a collection
  error hidden by a green count. The spec keeps existing results, so this plan keeps it; and it
  scores `1 failed, 1 error` FAIL under the new rule. Is the PASS row a defect to file separately?
- **OQ-4 (spec).** AC-2.9 omits `h_mad_wire_registry`, a third `_parse_tasks` consumer (P4).

## Next Steps

1. Operator approves plan v1.0 and answers OQ-1 and OQ-3; the orchestrator routes OQ-2 and OQ-4 to
   the spec.
2. Orchestrator runs step P0 and commits the probes; V-0 is run before the FR-6 form task.
3. Plan audit cycle (SKILL.md §"Audit prompt assembly").
4. Phase 4 design names the judge file, the timeout value and the blocking form.

## Version History
- v1.0: Initial plan draft (2026-09-28) from spec v1.0 at cf7e194f with OD-1..OD-7 accepted as recommended. Premises, the reproductions with controls, the OD-7 run_suite regression census, the stale-prose census and the coupled-suite baseline measured at 01121ca7. Step P0 embeds reproduce.py and v0-blocking-contract.sh with their sha256; OQ-1..OQ-4 raised.
