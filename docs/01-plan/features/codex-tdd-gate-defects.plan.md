# Plan: codex-tdd-gate-defects

## Executive Summary

Replace the two Phase-5 TDD gates' private state readers, resolvers, interpreters and rc-scorers
with one shared judge. A production write is then allowed only when a failing test has been
measured for it, on the Codex host and on the Claude host alike. The work starts by committing the
reproductions, measuring which refusal forms Claude Code honours (V-0), and replaying the HemaSuite
Task 7 incident offline against real artifacts (V-1r). The Claude gate's blocking form cannot be
chosen until V-0 has a conclusive reading, and the feature does not merge without one.

## Overview

Spec v1.0 (`cf7e194f`) is operator-approved, and every open decision OD-1 through OD-7 was accepted
as the spec recommends. The defects are live. At skills `2f262f8a`:
- the Codex gate allows a write with a **passing** test whenever its interpreter lacks pytest;
- it allows a sub-project write with no test run when a nearer state file has no step5 record;
- the Claude gate never reads Claude Code's `tool_input.file_path`;
- the Claude gate decides "is this write governed?" from the root state file first, so a
  sub-project step5 record is never seen while a root state file exists.

P3 below reproduces each case with a control. This feature merges first of the three in-flight
`h-mad/` features because it closes a live safety gap.

Revision v1.2 answered plan audit cycle 2 (codex, 4 musts) and the v1.1 delta review (4
musts, 7 shoulds), under orchestrator decisions D-A…D-D (operator-approved 2026-09-28). Spec v1.1
(`96bf1cd1`) settled S-1…S-6. S-7, S-8, S-9, S-11 and S-12 are cited as "spec v1.2 (S-n)"; spec v1.2
was being written in parallel with this revision, and the sentences this plan depends on are listed
in the author report. S-10 is withdrawn (D-A): the wire registry keeps its own grammar.

Revision v1.3 is a propagation revision, not an audit round. It carries into this plan what spec
v1.3 and design v1.1 (both committed at `b20ef027`) say the plan owes, and nothing else:
- the Claude gate's order, with exemptions before governance (DD-1, OD-A);
- the removal of the no-`jq` allow (DD-2);
- the one `run_suite` predicate that replaces "two explicit branches" (DD-3);
- the SGR strip and the open category axis in the summary-line rule (DD-4, OD-D);
- the process-group time bound (DD-10);
- the shell-policy differential's control-allowlist row and builder-derived versioned spelling
  (OD-C; DD-6 withdrawn);
- R2's citation of design D13;
- where the ACs spec v1.3 added or extended are tested (§"Spec v1.3 ACs: where each is tested").

## Scope

In scope, by file. Every path was verified present at `2f262f8a` with `ls`, except the new judge.

| File | Change | Spec |
|---|---|---|
| `h-mad/scripts/<judge>.py` (new; the design names it) | shared judge: chain reader, resolver, interpreter selection, scorer; CLI with a `judge` verb and a `state` verb | FR-1–FR-5; the `state` verb is spec v1.2 (S-8) |
| `h-mad/hooks/h-mad-codex-tdd-gate.py` | imports the judge; `_relative_target` gains the payload-`cwd` base; `_derived_test`, `_test_exit` and `_target_phase5_status` are removed; shell policy admits a contained `.venv` interpreter | FR-3, FR-5 |
| `h-mad/hooks/h-mad-tdd-gate.sh` | payload read; governance and the Codex-authorship key from the judge's `state` verb; judge CLI call; one refusal function at every refusal site and on every implicit exit | FR-6 |
| `h-mad/scripts/h_mad_wire_pin_gate.py` | `_parse_tasks` extended in place with `production` and `tests` | FR-2, OD-7 |
| `h-mad/scripts/h_mad_wire_registry.py` | **not edited** (D-A). `_production_claims` keeps its own grammar; see "Second Production grammar (residual)" | spec v1.2 FR-2 residual and AC-2.9 |
| `h-mad/scripts/h_mad_audit_gate.py` | `_suite_summary` extended in place; `run_suite`'s three verdict changes (spec v1.3 FR-4 "Audit-gate changes") and its one predicate (DD-3) | FR-4, OD-7 |
| `h-mad/references/codex-runtime.md` | §"Trust boundary" | FR-7 |
| `h-mad/SKILL.md`, `h-mad/references/agy-runtime.md`, `h-mad/references/codex-implementer-prompt.md` | registry entry for the judge; the gate prose the change makes false (see "Stale-prose census") | invariant §"Skill manifest integrity"; spec v1.2 (S-11) |
| `h-mad/tests/` | new test modules; the named updates only, including the module-level `HOOK` constant of the two Claude-gate modules (layer 6, "worktree artifacts reached through `$HOME/.claude`") | FR-8 and the ACs |
| `h-mad/tests/mutation-specs/` | new specs for every FR-8 guard; the audit-gate spec re-anchored if `run_suite` moves | FR-8 |
| `docs/03-analysis/probes/codex-tdd-gate-defects/` | four probes and their readings (step P0) | spec §"Measured premises", AC-0.1 |

## Goals

- G0: Commit the reproductions. Settle which refusal forms Claude Code honours, one live arm per
  form (V-0). Replay the Task 7 incident offline (V-1r). All three happen before FR-6's form is
  built (FR-0, AC-0.1, AC-0.2).
- G1: One judge decides for both gates. Neither gate keeps a state reader, resolver, interpreter
  or scorer of its own (FR-1).
- G2: The impl-plan Task names the test, the name map is the fallback, and otherwise the write is
  denied with both sources named (FR-2). The judge reads `Production` values through
  `_parse_tasks` only; the wire registry keeps its own grammar, a stated residual (D-A).
- G3: pytest runs under the nearest contained `.venv`, never under a venv that escapes the root
  (FR-3). The shell-policy relaxation is proven exact by a differential corpus.
- G4: The verdict comes from pytest's summary line, and rc selects nothing (FR-4).
- G5: Each gate resolves a relative target against its own base, and the two bases differ.
  - **Codex gate** (FR-5, design D8). `_relative_target(root, raw, cwd)` resolves a relative `raw`
    against `_payload_cwd_base(root, cwd)`. That base is the payload `cwd`, `.resolve()`d, when it
    is a directory equal to or under the root; otherwise it is the root. An absolute `raw`
    resolves as today. Either way, today's `.resolve()` in `_relative_target` folds `..` before
    `_is_production_python` tests the root-relative parts.
  - **Claude gate** (FR-6 "Relative target", design DD-7 and D9 step 3). A relative target is made
    absolute against the project root, never against the payload `cwd`. This happens before any
    check, the exemptions included.
    The `*/tests/*` and `*/fixtures/*` exemptions match the root-relative remainder only, so a root
    beneath `tests/` or `fixtures/` exempts nothing (design v1.3 §D9 step 3).
  - **Canonicalization is owed by design v1.2 and is not in the tree.** The target is to be
    canonicalized (`..` resolved) before any exemption pattern matches, so `tests/../x.py` is
    production (design audit cycle 2). Design v1.1 at `b20ef027` does not do this. Its D9 step 3
    is "string work only", so `$ROOT_ABS/tests/../x.py` still matches `*/tests/*`. Layer 6 follows
    design v1.2's rule once it is committed.
  - Both gates read state along the whole chain, for "is this governed?" as well as "which test?"
    (FR-5, FR-6).
- G6: The Claude gate reads Claude Code's real payload and is judged by the same unit. It refuses
  in a form V-0 proved Claude Code honours, on every refusal site and on every implicit exit
  (FR-6).
- G7: The trust boundary is documented (FR-7), and every new guard is mutation-tested (FR-8).

## Requirements

FR-0 through FR-8 of `docs/01-plan/features/codex-tdd-gate-defects.spec.md` v1.1 (`96bf1cd1`)
apply, with OD-1…OD-7 resolved as the spec recommends. Where this plan relies on S-7, S-8, S-9,
S-11 or S-12, it cites spec v1.2 (S-n). Spec v1.3 (`b20ef027`) adds OD-A…OD-D and the ACs listed
under §"Spec v1.3 ACs: where each is tested". Design v1.1 (`b20ef027`) owns every mechanism this
plan names by DD-n or D-n.

**Merge conditions:**
- V-0 must read conclusively (not `INCONCLUSIVE`) with a chosen form (spec v1.1 AC-6.7, S-4).
- V-1r (the offline Task 7 replay) must meet its post-merge criterion against the worktree's gate
  (spec v1.1 §"Live verification", S-5).

The live V-1 stays blocked on `multi-host-runtime`, and it is not a merge condition. Evidence:
`ls ~/.agents/skills/h-mad` → "No such file or directory", run at `2f262f8a`.

## Implementation Strategy

**Seven layers, bottom-up; each is testable offline.**

1. **P0: probes.** Commit `reproduce.py`, `v0-blocking-contract.sh`, `v1-offline-replay.sh` and
   `wire-registry-grammar.py` (Convention Prerequisites, step P0), with their pre-merge readings.
   Run V-0 and commit its reading. Nothing in layer 6's blocking form starts before V-0 reads
   conclusively.
2. **Parsers, extended in place (OD-7).**
   - `_parse_tasks` gains `production` and `tests` list fields under the spec's label and value
     axes.
   - `_production_claims` is not touched (D-A; see "Second Production grammar (residual)").
   - `_suite_summary` gains independent `failed`, `passed` and `errors` counts, and a
     `no tests ran` reading, and it scores only a whole pytest summary line (the "summary-line
     rule" under "Regression census"), never a count phrase found elsewhere in the output. SGR
     colour sequences are stripped from each line before it is matched (DD-4).
   - Every existing caller keeps its current result, except the three `run_suite` verdict changes
     spec v1.3 FR-4 lists ("Audit-gate changes"). The table under "Regression census" is the contract and is pinned cell by cell.
3. **The judge.** A pure core takes (root, absolute target, ACTIVE features with their state
   files) and returns a verdict and a `kind`. The chain reader lives here. The CLI has two verbs:
   - `judge` prints exactly one `TDD-JUDGE:` line (FR-1).
   - `state` prints exactly one `TDD-STATE:` line, which is the chain reader's result for a target:
     no step5 record on the chain, the ACTIVE keys with each one's `codex_status`, or unreadable.
     The design owns the format; spec v1.2 (S-8) names the verb in FR-1.

   The Claude gate uses `state` for "is this governed?" and for the Codex-authorship key, so both
   gates reach one state reader for every state decision (OD-3).
4. **Codex gate.** Import the judge. `_relative_target` resolves against a payload `cwd` inside the
   root (OD-2). Any exception on the main path becomes `_deny(...)` with `judge-error` (AC-5.4).
5. **Shell policy.** A contained `<D>/.venv/bin/python*` token is admitted under FR-3's
   containment rule, with relative tokens resolved against the payload `cwd` (design D8 adds
   `_contained_venv_executable` ahead of the unchanged `_trusted_executable`). The argv rules are
   unchanged, so a venv token gets exactly the `python*` rules, the H-MAD control allowlist
   included (spec v1.3 FR-3 and AC-3.6, OD-C; design DD-6 is withdrawn). The relaxation ships with
   the differential corpus under "Guard narrowing: shell policy".
6. **Claude gate.** The decision order is spec v1.3 FR-6 "Order" (OD-A, design DD-1); design D9
   owns the mechanism. The first step that decides ends the run:
   0. **Target** (OD-4, OD-B). The stdin payload is read first: the first non-empty string among
      `tool_input.file_path`, the top-level `file_path` and the top-level `path`. `$1` is consulted
      only when stdin yields no target. A stdin target that holds a control character, or a stdin
      read that fails, is no target, and `$1` is not consulted in its place: the empty-target rule
      decides (design D9 step 2). A relative target is made absolute against the project root,
      never against the payload `cwd`, before any check (DD-7, spec v1.3 AC-6.15). It is then
      canonicalized, with `..` resolved, before the exemptions match. That rule is owed by design
      v1.2 (G5).
   1. **Fast path.** No state file name on the target's chain → allow. It replaces
      `_resolve_state_file` (design D9 step 4, `_chain_may_hold_state`) and may allow only a write
      the `state` verb would read as none: a non-regular or dangling-symlink state path, and a
      target whose parent does not exist yet under an ancestor that holds a state file, both defer
      to the `state` verb (spec v1.3 AC-6.11).
   2. **Empty target** (DD-8). Governance of the root alone: `active` or `unreadable` → refuse
      `judge-error`; `none` → allow (spec v1.3 AC-6.13).
   3. **Exemptions and the `.py` filter** → allow. Their patterns keep their bytes. No state is read
      for an exempt write, so an exempt write is allowed even on an unreadable chain and the broken
      state file can be repaired (spec v1.3 AC-6.9, the three exempt fixtures).
   4. **Governance.** The `state` verb decides. No step5 record → allow. Unreadable, or any `state`
      failure mode → refuse `judge-error`, fail-closed like the Codex gate (spec v1.2 (S-8),
      AC-6.9; today the Claude gate fails open here). A target outside the root is governed by the
      root's state (DD-9, spec v1.3 AC-6.14).
   5. **Codex authorship** over the `state` verb's ACTIVE records. The escape applies only when
      **every** ACTIVE record on the chain declares `unavailable`/`exhausted` or
      `HMAD_CODEX_UNAVAILABLE` is set (spec v1.2 (S-8), AC-6.10).
   6. **Judge.** The `judge` verb for every governed `.py` write, whether or not the target exists
      (OD-5). The blocking form follows V-0's `CHOSEN=` reading (AC-6.5 / AC-6.6): (b) when
      `FORM_B=BLOCKS`, otherwise (a) rc 2, on either conclusive branch. `exit 1` is never a chosen
      form.

   The gate no longer reads `jq`, so its `command -v jq` allow is removed (DD-2, spec v1.3 FR-6
   "Removed", AC-6.12). Today that allow is the gate's
   `if ! command -v jq >/dev/null 2>&1; then` block (`grep -n 'command -v jq'
   h-mad/hooks/h-mad-tdd-gate.sh` → 1 matching line at `34c0e962`).
7. **Docs and mutation specs.** FR-7, the stale-prose census below, and the FR-8 specs.

**The judge is found relative to the hook's own resolved path, never through `$HOME/.claude/skills`.**
- The Claude gate today hard-wires
  `DERIVE_SCRIPT="$HOME/.claude/skills/h-mad/scripts/h_mad_derive_test_path.sh"`.
- `~/.claude/skills/h-mad` is a symlink to this checkout's `h-mad/`: `readlink ~/.claude/skills/h-mad`
  → `/Users/kimhawk/orca/skills/h-mad`, run at `2f262f8a`.
- A worktree's hook would therefore call the **main tree's** judge, which does not exist until
  merge. Every worktree test of the Claude gate would read `judge-error`, green for the wrong
  reason.
- The installed hook is itself a symlink: `readlink ~/.claude/hooks/h-mad-tdd-gate.sh` →
  `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh`.
- So the hook resolves its own path through the symlink and takes `../scripts/` from there:
  `python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "${BASH_SOURCE[0]}"`, since the
  hook already requires `python3`. The Codex gate already does the same
  (`Path(__file__).resolve().parents[1]` in `_derived_test`).
- A test runs the worktree hook through a symlink placed outside the tree, and asserts that the
  worktree judge ran. The W6 test uses **two distinct trees** (see "Connection enforcement"), so a
  judge path fixed to one checkout fails it.
- **Residual:** a copied (not symlinked) hook finds no judge and denies `judge-error`. That is
  fail-closed, and the SKILL.md install line states it.

**Worktree artifacts reached through `$HOME/.claude` are an axis; the tests are on it too.** The
hook→judge edge above is one member. The test→hook edge is another: both existing Claude-gate test
modules hard-wire `HOOK = Path.home() / ".claude" / "hooks" / "h-mad-tdd-gate.sh"`, which resolves
to the **main** checkout's hook, so in the worktree every migrated assertion would run the unmodified
gate. Census at `dfd5f02e` (`bash --noprofile --norc`, unit: matching lines):

```bash
grep -n 'Path.home() / ".claude"' h-mad/tests/*.py
# reading at dfd5f02e: 6 matching lines in 4 files. Members of this feature's axis: the HOOK
#   constant of test_h_mad_tdd_gate_codex.py and of test_h_mad_tdd_gate_state_resolution.py (2).
#   Not members: test_h_mad_install_check.py (3 lines), which asserts the installed defaults on
#   purpose, and test_h_mad_resume_decision.py (1 line), which reads handoff/, not this feature's files.
```

- **Rule:** every test that runs a file this feature edits resolves it from its own tree. Both
  `HOOK` constants become `Path(__file__).resolve().parents[1] / "hooks" / "h-mad-tdd-gate.sh"`.
- The change is module-level, outside any `def test_*`, so the impl-plan lists both constants under
  §"Regression provenance", and the widened function-body diff (Success Criteria) sees them.
- On main the value is unchanged in effect: `readlink ~/.claude/hooks/h-mad-tdd-gate.sh` →
  `/Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh`, the same file `parents[1]` reaches.
- **Residual:** a test that reaches this feature's files through `$HOME/.claude` by a spelling other
  than `Path.home() / ".claude"` (for example `os.path.expanduser`) is outside the grep. The 5g
  diff review reads each new or changed test module's path constants by hand.

**The judge's interpreter on the Claude side is the first `python3` on PATH**, the same one the
hook already uses for the payload read.
- Measured at `2f262f8a`: `/usr/bin/python3 --version` → `Python 3.9.6`, and
  `/usr/bin/python3 -c 'import pytest'` → `ModuleNotFoundError`.
- Both existing Claude-gate test modules run the hook with `PATH=<bin>:/usr/bin:/bin`, and their
  bin dirs hold no `python3`. The `_bin` helper in `test_h_mad_tdd_gate_state_resolution.py`
  symlinks only `jq`. So they get that interpreter.

Two rules follow:
- **(i) Python 3.9 floor.** The judge, and every module it imports, must import under Python 3.9.
  Today `h_mad_audit_gate`, `h_mad_wire_pin_gate` and `h_mad_wire_registry` each import under
  `/usr/bin/python3` (3.9.6), run at `2f262f8a` with `sys.dont_write_bytecode=True`. A test pins
  the floor with `ast.parse(source, feature_version=(3, 9))` over the judge and its imports.
  **Residual:** `feature_version` is best-effort for syntax and blind to runtime APIs.
- **(ii) Fixture interpreter.** Any Claude-gate fixture that expects `red-measured` or
  `test-passing` puts `python3 → sys.executable` in its bin dir (pytest-capable by construction,
  because it runs the suite) or supplies a contained `.venv`. A fixture that exercises
  `pytest-missing` uses a `python -m venv --without-pip` venv (AC-4.1). No fixture relies on
  whatever `python3` the machine has.

**Refusal sites are an axis, not a list. Implicit exits are on the axis too.** Every refusal the
Claude gate can emit goes through one function that emits the chosen form. That covers the
Codex-authorship BLOCK, every judge DENY and `judge-error`. No other exit path refuses.

The hook runs under `set -euo pipefail` (1 matching line for `grep -c '^set -euo pipefail'`). A
failing command substitution therefore ends the hook with **that command's** rc, bypassing the
refusal function. Executed at `2f262f8a`:
`bash -c 'set -euo pipefail; OUT=$(printf "TDD-JUDGE: ALLOW kind=red-measured\n"; exit 3); echo "$OUT"'`
→ rc 3, and nothing is printed. So "the gate reads the token, never `$?`" is false today for any
judge that exits non-zero.

- **Axis:** exit paths not written by the gate. The members are:
  - errexit on a command substitution (the judge call; the hook-relative `realpath` resolution;
    the payload read, which is already `|| true`);
  - `pipefail` on a pipeline;
  - `nounset`.
- **Rule:** the hook installs an `EXIT` trap before its first fallible command. When the hook
  exits non-zero and no allow or refusal decision has been recorded, the trap routes the exit
  through the refusal function with `kind=judge-error`, then exits with the chosen form's status.
  In addition, the judge call captures its rc explicitly (`OUT=$(…) || JRC=$?`), so a
  non-zero-rc judge reaches the token parser.
- **Per-member fixtures** (each run alone), each expecting a refusal in the chosen form and never
  the member's own rc:
  - a judge stub that prints a traceback and exits 1;
  - a judge stub that prints a valid ALLOW line and exits 1. It expects DENY `judge-error`
    (spec v1.2 (S-9): rc never selects ALLOW; AC-1.3).
  - a `python3` stub that fails the `realpath` call;
  - an unset variable reached on the refusal path, injected by a mutation.
- **Residual:** signals that kill `bash` itself, and a parse error before the trap is installed.

Census at `2f262f8a`, run in `bash --noprofile --norc`, unit: matching lines:

```bash
grep -c '^\s*exit 1\s*$' h-mad/hooks/h-mad-tdd-gate.sh      # 5
grep -c 'BLOCK:' h-mad/hooks/h-mad-tdd-gate.sh              # 5
grep -c 'exit 2\|permissionDecision' h-mad/hooks/h-mad-tdd-gate.sh   # 0
grep -c '\$(' h-mad/hooks/h-mad-tdd-gate.sh                 # 9 (command-substitution lines)
```

These counts **move by construction**. After FR-6, four of today's five `exit 1` sites are
replaced by the judge call: derivation script missing, cannot derive, no test file, test already
passing. The Codex-authorship site remains. Re-measure at the 5g diff review. The pass condition
is AC-6.5's `grep -c '^\s*exit 1\s*$'` → 0 on **either** conclusive branch (spec v1.1 AC-6.6 reuses
AC-6.5's check; `exit 1` is not kept under `E1_BLOCKS`), never a carried count. The trap's
per-member fixtures are the backstop for a refusal the greps cannot see, such as `… || exit 1`
inside a compound line.

**The run_suite change is stated as a table, not a sentence.** Today's behaviour is measured
(P6). The after-column is spec v1.3 FR-4's three audit-gate changes plus what extending the parser
necessarily moves.

**What we deliberately do not touch:**
- `h_mad_derive_test_path.sh`'s three prefixes;
- `_any_phase5_status` (shell policy);
- the Claude gate's no-state and exemption fail-opens (the no-state one bounded by the fast-path
  rule in layer 6; the exemptions keep their pattern bytes and move ahead of governance). The
  no-`jq` allow is **not** kept: it is removed (DD-2, spec v1.3 FR-6 "Removed", AC-6.12);
- the `codex_status` / `HMAD_CODEX_UNAVAILABLE` escapes;
- the audit gate's exit-check logic.

## Verified premises (commands run at `2f262f8a`)

Each premise was executed against the tree in this revision, in `bash --noprofile --norc`. The
Bash tool's own shell defines `grep` as a function: in that shell,
`grep -n 'exit 1' F | grep -c 'exit 1 ;;$\|…'` printed 4 where the true count is 7, so no reading
here comes from it.

The gate code has not moved since v1.0's readings. `git diff --name-only 01121ca7 2f262f8a -- h-mad
handoff | wc -l` → 0 files. The spec read the tree at `ae7593a1`, and the gate files did not move
between it and `01121ca7` either (v1.0). The premises were re-run anyway rather than inferred.

- **P1: Codex gate symbols.**
  `grep -c '^def \(_deny\|_project_root\|_target_phase5_status\|_any_phase5_status\|_relative_target\|_trusted_executable\|_safe_shell_command\|_derived_test\|_test_exit\)' h-mad/hooks/h-mad-codex-tdd-gate.py`
  → 9 (matching lines).
  - `_test_exit` sends stdout and stderr to DEVNULL and runs `sys.executable`.
  - `main` refuses when `test_exit != 1` (`grep -c 'test_exit != 1'` → 1 matching line).
  - `_target_phase5_status` returns the status of the **nearest** state file.
  - `_project_root` takes `CODEX_PROJECT_DIR`, then the payload's `project_dir`, then `cwd`, then
    the process cwd, each through `git rev-parse`.
- **P2: Claude gate.**
  - The stdin branch reads `d.get('file_path', d.get('path', ''))` (`grep -c "d.get('file_path'"` →
    1 matching line).
  - The pytest run is bare `pytest`, guarded by `[ -f "$TARGET_PATH" ]` (1 matching line).
  - `ACTIVE` is the **first** step5 key of the file `_resolve_state_file` returns
    (`grep -c 'head -1'` → 1 matching line).
  - `_resolve_state_file` returns the root `docs/.bkit-memory.json` whenever it exists, and walks
    up from the target only when it does not. Read in `_resolve_state_file`: the root branch
    returns before the walk.
  - So a root state file with no step5 record hides a sub-project's step5 record. Reproduced as
    P3 `OD-3c`.
- **P3: reproductions, each with a control.** Command:
  `/opt/homebrew/bin/python3 docs/03-analysis/probes/codex-tdd-gate-defects/reproduce.py . /opt/homebrew/bin/python3 /opt/anaconda3/bin/python`.
  The interpreter is pinned because the probe's `str | None` signatures need Python ≥ 3.10, and
  `/usr/bin/python3` is 3.9.6 (P8). The bytes of the P0 block below were run from scratch at
  `2f262f8a`, and again at `dfd5f02e` under that interpreter (3.14.7): 24 `REPRO:` lines, rc 0,
  and the five fail-open lines P0 greps for all present.
  A Claude-gate reading is `(rc, stdout permissionDecision or '', first stderr line)`, so each
  blocking form reads differently from an allow. Unit: one `REPRO:` line per case. Timings and
  temp paths vary and are not part of the reading.

  | Case | Reading | Control | Control reading |
  |---|---|---|---|
  | D3: Codex gate under a python with no pytest, passing test | `(0, 'allow', '')` | same, python with pytest | `(0, 'deny', '… returned pytest exit 0 …')` |
  | OD-2: `cwd` = sub-project, target `tools/w.py` | `(0, 'deny', '… before tools/w.py; no derived test file exists.')` | the `D3 control-withpytest` row: the same file named root-relative | deny on the test's result, not on derivation |
  | OD-3: Codex gate, root state step5, sub-project state without step5, passing test | `(0, 'allow', '')` | no sub-project state | `(0, 'deny', '… returned pytest exit 0 …')` |
  | OD-4: Claude gate, `{"tool_input":{"file_path":…}}` | `(0, '', '')` | top-level `file_path` | `(1, '', '[H-MAD-TDD-GATE] BLOCK: … must be authored by Codex …')` |
  | OD-3c: Claude gate, root state holds only a step3 record, sub-project state holds step5 (codex exhausted), absolute target | `(0, '', '')` | no root state | `(1, '', '[H-MAD-TDD-GATE] BLOCK: cannot derive test path …')` |
  | D1: Claude gate, absolute path, codex exhausted | `(1, '', '… cannot derive test path …')` | the `OD-5 control-withpytest` row: the same file named relatively | reaches the test run (`already passing`) |
  | OD-5: Claude gate, codex exhausted, no `pytest` on PATH, passing test | `(0, '', '')` | `pytest` on PATH | `(1, '', '… already passing …')` |
  | pytest 9.1.1 summary lines | RED rc 1 `1 failed`; GREEN rc 0 `1 passed`; import error rc 2 `1 error`; empty rc 5 `no tests ran`; no pytest rc 1 `No module named pytest` | — | — |

- **P4: `Production` is read by two grammars today, and `_parse_tasks` has three consumers.**
  - `git grep -n "_parse_tasks" -- h-mad handoff ':!h-mad/tests/fixtures' | grep -v '^h-mad/scripts/h_mad_wire_pin_gate.py'`
    → `h-mad/scripts/h_mad_assemble_tdd.py` (2 matching lines), `h-mad/scripts/h_mad_wire_registry.py`
    (2 matching lines), and `h-mad/SKILL.md` (1 prose line).
  - `h_mad_wire_registry` hands the parsed tasks to `_production_claims`
    (`git grep -n "_production_claims" -- h-mad handoff` → 2 matching lines, both in that file:
    the definition and the one call).
  - `_production_claims` re-reads the plan with its **own** label regex, which accepts the singular
    `Production file` only. It takes the whole value as one key with only the outer backticks
    stripped. It uses its **own** task counter: `## Task ` or `#{2,3} [MT]\d+`, not `_TASK_RE`.
  - This feature does not edit `_production_claims` (D-A). Spec v1.2 AC-2.9 names the registry's
    tests beside the wire-pin gate's and the assembler's, and pins that `_production_claims` has
    no diff against the base.
- **P5: `_suite_summary` has one caller.**
  - `git grep -n "_suite_summary" -- h-mad handoff ':!h-mad/tests/fixtures'` → matches in
    `h-mad/scripts/h_mad_audit_gate.py` only: its definition and `run_suite`.
  - Its scan rule: the **last** `_SUITE_RE` match, anywhere in `stdout + stderr`, that carries a
    `passed` or `failed` count (read in `_suite_summary` and `run_suite`).
  - `run_suite` has two callers: `git grep -n "run_suite(" -- h-mad/scripts` →
    `h_mad_audit_gate.py` (its definition and `main`) and `h_mad_audit_cycle.py` (1 call).
- **P6: `run_suite` today.** Measured by `reproduce.py`'s `run_suite` stanza: stub suites print
  one line and exit 1. See the table under "Regression census".
- **P7: the named existing tests exist.**
  `grep -c 'def test_codex_hook_rejects_untrusted_executable_paths\|def test_codex_hook_scopes_nested_state_to_the_target_project\|def test_codex_hook_rejects_pytest_no_tests_collected_as_red\|def test_codex_hook_resolves_git_root_from_nested_cwd\|def test_codex_adapter_states_pytest_trust_boundary' h-mad/tests/test_h_mad_codex_runtime.py`
  → 5 matching lines.
- **P8: interpreters.**
  - `/opt/homebrew/bin/python3 -c 'import pytest'` → `ModuleNotFoundError`.
  - `/opt/anaconda3/bin/python -m pytest --version` → `pytest 9.1.1`.
  - Bare `python3` resolves to `/opt/homebrew/bin/python3` in an interactive shell (`which python3`).
  - `/usr/bin/python3` is 3.9.6, with no pytest.
  - This repository has no `.venv` (`ls .venv/bin/python` → no such file).
  - Consequences are in R4, OQ-1 and the interpreter rules above.
- **P9: HemaSuite layout, re-read at HemaSuite `69ac6210`.**
  - `realpath` of `hematology-paper-writer/.venv/bin/python` is outside the root, so OD-1 stands.
  - The step5 record for `review-manifest-guideline-evidence` sits in the root
    `docs/.bkit-memory.json`, with `codex_status=available`. The sub-project state file has no
    step5 record (read with `json.load`), so OD-3 stands.
  - The sub-project `.venv` has pytest 9.1.1, and its `site-packages` holds one `.pth` file,
    `distutils-precedence.pth`, so there is no editable install pointing back into the tree.
  - The sub-project conftest puts the git root on `sys.path`, so tests import `shared/`.
- **P10: install.** `grep -n 'tdd-gate' ~/.claude/settings.json` → one registration,
  `"$HOME/.claude/hooks/h-mad-tdd-gate.sh"`, with no argument. The hook link resolves into this
  checkout (layer 6).
- **P11: the Task 7 incident is recoverable from git objects.**
  - HemaSuite `31bfcfe4` ("Task 7 delete the certificate lock") adds
    `tests/test_certificate_lock_removed.py` in the same commit as the production change.
  - Its parent `1fbf8022`, plus that one test file, is therefore the incident state: the RED test
    existed and the production change did not.
  - At both commits the impl-plan's only Task naming `tools/review_round/guideline_excerpts.py`
    is Task 7. Its Test entries, in plan order, are `tests/test_certificate_lock_removed.py`,
    `tests/test_review_guideline_pdf_excerpts.py`, `tests/test_review_qualitative_assets.py` and
    `tests/test_review_intake_wiring.py`.
  - The blocked GREEN report
    (`docs/03-analysis/probes/codex-tdd-gate-defects/hemasuite-t7_green.blocked1.report.md`)
    records both denials: the patch ("no derived test file exists") and
    `.venv/bin/python -m pytest` (shell policy).

## Second Production grammar (residual, D-A)

**Decision D-A (operator-approved 2026-09-28):** `h_mad_wire_registry._production_claims` is not
edited. v1.1's rewrite over `_parse_tasks`, its three-population differential and wire W7 are
withdrawn, and spec S-10 with them. The judge reads `Production` values only through
`_parse_tasks`' new `production` field; no third parser is written.

**Residual, stated exactly.** After FR-2, "which Task owns this production file" is answered by two
grammars: the judge's (`_parse_tasks`, spec FR-2's label and value axes) and the wire registry's
(`_production_claims`: its own Task counter, `## Task ` or `#{2,3} [MT]\d+`; the singular
`Production file` label only; the whole value as one key with the outer backticks stripped, of any
extension). A plan line can be a production claim to one and not to the other, in both directions
(spec v1.2 FR-2 "Residual: two `Production` parsers remain"). The registry's claims do not move,
because its code does not move; spec v1.2 AC-2.9 pins `_production_claims` with no diff against
the base, and pins that the extended `_parse_tasks` returns the same task ids in the same order as
the base, because the registry pairs its own counter with that list by index.

**Where the two disagree today, as a witness, not a complete census.** Probe
`wire-registry-grammar.py` (step P0), run as
`python3 …/wire-registry-grammar.py . /Users/kimhawk/orca/HemaSuite` at skills `2f262f8a` /
HemaSuite `69ac6210`, over the corpus of 83 tracked, non-`archive/` `*.impl-plan.md` files. It
counts three divergence populations; it does not enumerate every divergence (the v1.1 delta review
found further populations, such as singular-label values with no `.py` token). Reading:

| Divergence today | Unit | Count |
|---|---|---|
| task counter differs from `_parse_tasks`: `desk-check-autofix` 11/12, `guideline-ingest-doc-id-uniqueness` 36/0, `presentation-voice-guidance` 8/0, `review-pipeline-correctness` 0/1 | files | 4 |
| singular `Production file` value carrying ≥2 backticked `.py` tokens, read by the registry as one malformed key | matching lines | 16 |
| `Production files` / `Production` label lines the registry does not read | matching lines | 64 |

The 64 agree with the spec's label census (46 + 18). The corpus moves with every impl-plan
commit, so this reading is re-derived at 5g, never carried. No row is a pass condition: under D-A
the pass condition is AC-2.9.

The registry's existing tests pass unmodified (R3), and its mutation specs
(`wire_registry_*.json`, 3 files) are untouched by this feature.

## Guard narrowing: shell policy

FR-3 deliberately makes `_trusted_executable` / `_safe_shell_command` accept tokens they reject
today. Invariant §"Guard narrowing" requires the relaxation to be shown exact.

- **Corpus**, driven through the gate's real entry point: a stdin `shell_command` payload with a
  `cwd`, on a step5 fixture. The entry point is used so the old and new signatures do not matter.
  The axes are crossed in full, and the design fixes the fixture tree.
  - **Token spelling:**
    - absolute, into the contained venv;
    - root-prefixed `hematology-paper-writer/.venv/bin/python` from the root `cwd`;
    - `.venv/bin/python` from the sub-project `cwd` (the incident's shape);
    - `./.venv/bin/python`;
    - `../hematology-paper-writer/.venv/bin/python` from a sibling `cwd`;
    - root-prefixed from the sub-project `cwd`, which resolves to a doubled path that does not
      exist (spec v1.1 AC-3.4, S-6);
    - the versioned name `.venv/bin/python<X.Y>`, where `<X.Y>` is derived from the fixture's
      builder interpreter (`f"python{sys.version_info[0]}.{sys.version_info[1]}"`, design D12),
      never a literal: a literal version exists only under one builder, so the row would silently
      stop testing a versioned name under any other;
    - a `python-evil` file placed in the contained venv's `bin/`, which matches `python*`.
  - **Venv state:**
    - contained;
    - `.venv` is a symlink that leaves the root;
    - `.venv/bin` is a symlink that leaves the root;
    - `pyvenv.cfg` is missing;
    - `pyvenv.cfg` is a symlink;
    - a venv outside the root, named by an absolute token.
  - **argv:**
    - `-m pytest tests/test_x.py`;
    - `-c "open('x','w')"`;
    - `-m pip install x`;
    - `script.py`;
    - `-m pytest tests/test_x.py; touch y`;
    - `<the hook's h-mad/scripts>/h_mad_state_write.py <root>/docs/.bkit-memory.json`, an argv
      that `_safe_hmad_script` accepts under `/usr/bin/python3` (spec v1.3 AC-3.6, OD-C; design D8
      "Differential").
  - **Control rows**, which must not change: `/usr/bin/python3 -m pytest …`,
    `/usr/bin/python3 <the hook's h-mad/scripts>/h_mad_state_write.py …` (AC-3.6's control),
    `venv/bin/python -m pytest …`, `.venv/bin/pytest …` and `python3 -m pytest …`.
- **Old versus new.** The old verdicts come from `git show <base>:h-mad/hooks/h-mad-codex-tdd-gate.py`,
  run against the same fixtures. The new verdicts come from the worktree head.
- **Accounting.** Publish rows, softened (deny→allow) and tightened (allow→deny). The expected
  softened set is exactly {contained venv} × {spellings that resolve into it, `python-evil`
  included} × {`-m pytest tests/test_x.py`, the `h_mad_state_write.py` row} (design D8
  "Differential"). The control-allowlist row is softened because FR-3 has always let a contained
  venv interpreter pass the existing argv rules, H-MAD control allowlist included (spec v1.3
  AC-3.6; OD-C withdrew design DD-6's narrowing to `-m pytest …`). The `python-evil` spelling is
  the spec's stated residual ("a `.venv/bin/python` inside a contained venv that symlinks to an
  arbitrary binary … is accepted") applied to the `python*` glob, and it is listed by name. Any
  other softened row is a defect, and any tightened row is justified by name.
- **AC-3.6's refusals are rows of the same corpus:** the `h_mad_state_write.py` argv under the
  escaping venv states (denied), and a script path outside the hook's `h-mad/scripts/` under the
  contained-venv token (denied).
- **Guarantee checked against the real system, not a heuristic.** Containment rests on
  `os.path.realpath`. A fixture asserts that `realpath` follows each symlink in the venv-state axis
  as the rule assumes.

## Regression census for OD-7 (`run_suite` scoring)

**Question:** which existing tests, mutation specs, stamps or documents depend on a summary with
failures and no passes reading `UNREADABLE no_summary`? Every command below ran at `2f262f8a`
unless its reading names another sha.

**Behaviour today and after.** Today is the P6 reading. After is spec v1.3 FR-4 plus what the parser
extension necessarily moves. Each row becomes one parametrized test case in the audit-gate suite,
with its own stub. The first column is what the stub prints.

**Summary-line rule (FR-4 "pytest's summary line").** Today `_suite_summary` takes the last
`_SUITE_RE` match found **anywhere** in `stdout + stderr` (P5). Once the parser reads `failed`
alone, that rule would score a stray `1 failed` printed after a passing summary as a failure: a
passing test would read `red-measured` and allow a production write. So the extended parser scores
only a **summary line**:
- SGR colour sequences (`ESC [ … m`) are removed from each line **first**, before any stripping
  or matching (spec v1.3 FR-4 "Colour", DD-4). Without the strip, pytest's `--color=yes` summary
  is not a whole-line match and would read `UNREADABLE`; today it is a fail-open the other way
  (the coloured-row reading below);
- a whole line, after stripping surrounding whitespace and pytest's `=` padding, that consists only
  of comma-separated `<N> <category>` count phrases (or `no tests ran`), optionally followed by
  ` in <duration>` and a parenthesised wall-clock. A category is one or more lowercase words
  (design D7), so pytest 9.1.1's two-word `subtests passed` / `subtests failed` /
  `subtests skipped` are summary phrases. Only a phrase whose category is exactly `passed`,
  `failed`, or `error`/`errors` adds to a count, so `2 subtests passed` adds nothing to `passed`
  (spec v1.3 FR-4 "Category axis"). A line with a category holding a digit, an uppercase letter
  or other punctuation is not a summary line, and fails closed (`no-summary` / `no_summary`);
  that residual is the design's (D7);
- a line that carries ` in <duration>` beats any line that does not, wherever each sits; among lines
  of the same kind, the last wins;
- a count phrase inside a longer line (a traceback, a `FAILED …` line, a diagnostic) is never read.

The untimed fallback exists because an existing caller depends on it: of the stub lines that reach
`run_suite`, one prints an untimed summary. Census at `dfd5f02e` (`bash --noprofile --norc`, unit:
matching lines):

```bash
git grep -n -E '[0-9]+ (passed|failed|error|errors)( in|,|"|\\n)' -- h-mad/tests handoff ':!h-mad/tests/fixtures' | grep -v mutation-specs
# reading at dfd5f02e: 13 matching lines. 8 reach run_suite (test_h_mad_audit_suite_gate.py 7,
#   test_h_mad_audit_cycle.py 1), each echoing its summary as a whole line; 7 of the 8 are timed,
#   and test_h_mad_audit_suite_gate.py's `echo "1 failed, 8 passed"; exit 1` is the untimed one
#   (asserted FAIL). The other 5 are in modules that do not call _suite_summary (P5).
```

**Residual:** output with no timed summary line and a stray whole-line count (for example pytest
killed before its summary, after a plugin printed `1 failed` on a line of its own) is scored on the
stray line. The judge's timeout and `pytest-missing` branches run first (FR-4 classification).

| Stub prints | `_suite_summary` today | `run_suite` today | `run_suite` after | Why |
|---|---|---|---|---|
| `3 failed in 0.10s` | `None` | UNREADABLE `no_summary` | **FAIL** | spec v1.3 FR-4 audit-gate change 1 |
| `3 failed, 1 skipped in 0.1s` | `None` | UNREADABLE `no_summary` | **FAIL** | same class: failures, no passes |
| `1 failed, 1 error in 0.1s` | `None` | UNREADABLE `no_summary` | **FAIL** | same class; see OQ-3 |
| `1 error in 0.06s` | `None` | UNREADABLE `no_summary` | UNREADABLE `no_summary` | spec v1.3 FR-4 non-change; kept by the one predicate |
| `no tests ran in 0.01s` | `None` | UNREADABLE `no_summary` | UNREADABLE `no_summary` | spec v1.3 FR-4 non-change; kept by the one predicate |
| `2 passed, 1 error in 0.1s` | `(2, 0)` | **PASS** | PASS | kept by the spec's "existing callers keep their results"; see OQ-3 |
| `1 failed, 11 passed in 0.2s` | `(11, 1)` | FAIL | FAIL | unchanged |
| `collected 0 items` (no summary) | `None` | UNREADABLE `no_summary` | UNREADABLE `no_summary` | unchanged |
| stdout `2 passed in 0.1s`, then stderr `1 failed` | `(2, 0)` | PASS | PASS | the summary-line rule; the discriminating case |
| coloured `1 failed, 1 passed in 0.04s` (the `--color=yes` bytes, design D7) | `(1, 0)` | **PASS** | **FAIL** | spec v1.3 FR-4 audit-gate change 2 (DD-4): a fail-open closed |
| `3 skipped in 0.1s` | `None` | UNREADABLE `no_summary` | UNREADABLE `no_summary` | the one predicate; `5 deselected in 0.1s` and `1 xfailed in 0.1s` read the same (spec v1.3 AC-4.7) |
| `2 passed, 2 subtests passed in 0.00s` | `(2, 0)` | PASS | PASS | spec v1.3 FR-4: 2 passed, the subtests phrase counts toward nothing |
| `2 failed, 1 subtests passed in 0.02s` | `None` | UNREADABLE `no_summary` | **FAIL** | spec v1.3 FR-4 audit-gate change 3; 0 passed |

The four rows after the discriminating case come from design D7's table (spec v1.3 FR-4). Their
"`_suite_summary` today" cells were re-read at `34c0e962` (h-mad/ unchanged since `1ef1a782`:
`git diff --stat 1ef1a782 34c0e962 -- h-mad handoff` is empty) by calling today's parser under
`/usr/bin/python3` from `h-mad/scripts` with `sys.dont_write_bytecode=True`, nothing written:
the coloured bytes
`\x1b[31m\x1b[31m\x1b[1m1 failed\x1b[0m, \x1b[32m1 passed\x1b[0m\x1b[31m in 0.04s\x1b[0m\x1b[0m`
→ `(1, 0)`; `3 skipped in 0.1s` → `None`; `2 failed, 1 subtests passed in 0.02s` → `None`;
`2 passed, 2 subtests passed in 0.00s` → `(2, 0)`. No row moves toward PASS.

The last row's "today" was measured at `dfd5f02e` by calling `_suite_summary('2 passed in 0.1s\n1 failed\n')`
and `run_suite` on a stub printing that pair, under `/opt/homebrew/bin/python3`: `(2, 0)` and
`PASS`. Today's parser gets it right only because `_SUITE_RE` requires `passed`; a parser extended
to read `failed` alone without the summary-line rule scores it FAIL, and that is the mutation the
row catches. The same pair fed to the judge (AC-4.4-style shim, rc 0) reads DENY `test-passing`,
never ALLOW `red-measured`; the impl-plan pins it beside AC-4.4.

**One predicate, not one branch per instance** (spec v1.3 FR-4 "Audit-gate non-change", DD-3).
Once the parser returns counts for `1 error`, for `no tests ran` and for any summary whose
phrases carry no `passed` and no `failed`, `run_suite`'s `passed == 0 and failed == 0` test would
otherwise catch every one of them and re-label it `no_tests_ran`.
- For `1 error` that is false, because tests were collected and errored.
- For `no tests ran`, `3 skipped in …`, `5 deselected in …` and `1 xfailed in …` it changes the
  `SUITE:` reason that `main` and `h_mad_audit_cycle` print.

The axis is "a parsed summary with no `passed` phrase and no `failed` phrase", not the two members
plan v1.2 named: a branch per member left the other three moving to `no_tests_ran` (design D7).
So `run_suite` gains one predicate, between the `summary is None` return and
`if passed == 0 and failed == 0:`, over exact category strings: a summary whose phrase set holds
neither `passed` nor `failed` scores `UNREADABLE no_summary`, as today. `subtests passed` alone
does not satisfy it. `no_tests_ran` stays reserved for a parsed summary with a `passed` or
`failed` phrase and 0 passed, 0 failed, such as `0 passed in …`. The judge's rule 8
(`no-tests-ran`) does not reach `run_suite`. AC-4.7 pins five members with exact-reason fixtures
(`no tests ran`, `1 error`, `3 skipped`, `5 deselected`, `1 xfailed`), each run alone. The
design names the predicate and its mutation (`audit_suite_summary_line.json`: each word of the
`{"passed","failed"}` set mutated alone).

**Tests that pin today's behaviour.**

```bash
git grep -n "no_summary\|no_tests_ran\|SUITE: UNREADABLE\|SUITE: FAIL" -- h-mad/tests handoff ':!h-mad/tests/fixtures' | wc -l
# reading at 2f262f8a: 10 matching lines: test_h_mad_audit_suite_gate.py 7,
#   mutation-specs/audit_suite_gate.json 2, and test_h_mad_archreview_cycle.py 1
#   (an unrelated `no_summary_slot.md` fixture name).
git grep -n -E '"[0-9]+ (failed|error|errors)( in|,)|no tests ran' -- h-mad/tests handoff ':!h-mad/tests/fixtures'
# reading at 01121ca7 (h-mad/ and handoff/ are unchanged since, see Verified premises): every stub
#   summary that carries "failed" also carries "passed" ("1 failed, 11 passed", "2 failed, 5 passed",
#   "1 failed, 8 passed"); the one "no tests ran" stub is
#   test_a_run_that_says_only_no_tests_ran_is_also_refused.
```

**Result: no existing test feeds a failures-without-passes summary.** So none pins the
`3 failed` → UNREADABLE behaviour that AC-4.7 anticipated. AC-4.7's "that test is updated" has no
member, and the impl-plan says so rather than inventing one.

Two tests sit next to the change and must pass **unmodified**:
- `test_no_summary_is_UNREADABLE_not_PASS_and_not_FAIL`: its stub prints `collected 0 items`, and
  there is still no summary.
- `test_a_run_that_says_only_no_tests_ran_is_also_refused`: it asserts only "not PASS", which is
  still true under spec v1.2 (S-7), which keeps `UNREADABLE no_summary` for it.

The docstring of `test_an_empty_selection_is_not_a_pass` says a `no tests ran` stub "never reaches
the verdict logic at all". After the change it does, so that sentence becomes false. It is prose
in a test, not an assertion. The impl-plan names it as a docstring correction under
§"Regression provenance", citing what it asserted.

**Mutation specs anchored inside `run_suite`.** `h-mad/tests/mutation-specs/audit_suite_gate.json`
anchors three mutations on `run_suite` source lines:
- the `verdict = "PASS" if failed == 0 and passed > 0 else "FAIL"` line;
- the `if passed == 0 and failed == 0:` line;
- the `no_summary` return.

Anchor state before:

```bash
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json | grep '^ANCHORS: ANCHORS_OK'
# reading at 2f262f8a: ANCHORS: ANCHORS_OK specs=99 mutations=907 ok=907 drifted=0 unreadable=0 skipped=0 unclassifiable=0
```

v1.0 piped this through `tail -1`, which prints `[H-MAD] anchors ANCHORS_OK`, not the line shown.
The `grep` above selects the reading line itself.

**Rule, over the axis "any edit that changes how many times an anchored line occurs".** That
covers three cases:
- an anchored line that moves;
- an anchored line that is deleted;
- a **new** line byte-identical to an anchored one. The harness refuses an anchor that matches
  other than exactly once ("anchor matched N times … expected exactly 1").

The one predicate above is the known case: it returns an `UNREADABLE`/`no_summary` dict that
could duplicate the anchored `no_summary` return. It is written so that it is not byte-identical
to the anchor (design D7 orders its dict keys for exactly this), or the anchor is narrowed. Any re-anchor lands **in the same
commit**, and the re-anchored mutation is re-run and must still be CAUGHT by the same test.

`ANCHORS_OK` with `drifted=0` is a 5g gate. The `specs=` and `mutations=` figures grow by
construction when FR-8's specs land, so they are re-read then and never carried.

**Stamps.** A stamp records `run_suite`'s verdict string as `"suite"`, and `--exit-check` maps any
non-PASS value to `BLOCKED`: `suite_fail:` for FAIL, `suite_unreadable:` for UNREADABLE. The change
therefore moves a new stamp from `UNREADABLE` to `FAIL`, and an `EXIT:` reason from
`suite_unreadable` to `suite_fail`. Both block, and no PASS flips (invariant §"Backward
compatibility"). Committed stamps carrying `UNREADABLE`:

```bash
git ls-files -z '*.gated.json' | xargs -0 grep -l 'UNREADABLE' | wc -l
# reading at 2f262f8a (skills): 0 files, of 25 tracked stamps (git ls-files '*.gated.json' | wc -l)
# same command at HemaSuite 69ac6210 (v1.0 reading, not re-run): 0 files, of 124 tracked stamps
```

No committed stamp is re-scored by this change, because stamps are read and never re-derived.

**Documents.** `h-mad/SKILL.md`'s #91 bullet says `SUITE: UNREADABLE reason=no_summary` is a
cannot-judge, and that stays true. `git grep -n "suite_unreadable" -- h-mad handoff` → 0 matching
lines at `01121ca7`, unchanged tree since. The reason is built by an f-string, so no prose names
the reason that moves.

## Stale-prose census (FR-6 blocking form, FR-1 judge)

```bash
git grep -c "h-mad-tdd-gate\|h-mad-codex-tdd-gate\|h_mad_derive_test_path\|exit-code protocol" -- h-mad handoff ':!h-mad/tests' ':!*/archive/*'
# reading at 2f262f8a (unit: matching lines per file): h-mad/SKILL.md 6, h-mad/hooks/h-mad-codex-tdd-gate.py 1,
#   h-mad/hooks/h-mad-tdd-gate.sh 4, h-mad/references/agy-runtime.md 2, h-mad/references/codex-implementer-prompt.md 1,
#   h-mad/references/codex-runtime.md 2, h-mad/scripts/h_mad_derive_test_path.sh 2,
#   h-mad/scripts/h_mad_hook_wiring.py 1, h-mad/scripts/h_mad_install_check.py 3
```

Each non-code match is a **candidate**, re-read at 5g against the shipped gate. Known to go false,
and each is in the Scope table:
- `h-mad/references/agy-runtime.md` §"The TDD gate" says the Claude gate "is written to Claude
  Code's exit-code protocol". That is false under AC-6.5 form (b).
- `h-mad/SKILL.md`'s script registry lists `h_mad_derive_test_path.sh` as the mapper, and the judge
  must be registered beside it.
- `h-mad/references/codex-implementer-prompt.md`, in its list of what the hook allows:
  - The production-code bullet says the hook allows the write when "a derived test file exists AND
    the test file is currently failing". After FR-2 the test comes from the impl-plan Task first,
    and "failing" means the summary shows `N failed` (FR-4).
  - The test-file bullet lists `*test_*.py` as exempt, while the hook exempts on the basename.

**Residual:** prose that describes the gate without naming a file is outside this grep. The
design's doc-test pins the new wording by heading, not by the old text's absence (invariant §"Both
halves of a doc change").

## Architecture Considerations

- **Single-source contract.** One chain reader, one resolver, one scorer, one `Production`
  grammar for the judge, all called by both gates (the wire registry's own grammar is the stated
  residual, D-A). The Codex gate imports the judge. The Claude gate runs its CLI
  and parses one line per verb. No gate keeps a private fallback: AC-1.1 requires
  `git grep -n "h_mad_derive_test_path.sh" -- h-mad/hooks` → no match. No gate keeps a private
  state reader either: after FR-6 the Claude gate contains no `jq` expression over
  `orchestrator_state` (a 5g grep).
- **The CLI boundary fails closed in both directions.**
  - Zero lines, two lines, an unknown verb or an unknown `kind` are DENY `judge-error` (AC-1.3).
  - A judge that exits non-zero reaches the token parser, never errexit (the `EXIT` trap rule).
- **Import failure in the Codex gate** must still print a JSON deny with rc 0 (AC-5.4). The judge
  import sits inside the guarded main path, not at module top level.
- **Self-containment.** The judge is stdlib-only, runs on Python ≥ 3.9, and lives under
  `h-mad/scripts/`. The hooks reach it by their own resolved path. pytest is the only non-stdlib
  tool, and it is already a declared dependency.
- **No knob.** No environment variable or config key is added (spec NFR Security).
- **Time bound.** The judge starts each pytest run with `subprocess.Popen(…,
  start_new_session=True)`, reads it with `communicate(timeout=…)`, and on timeout kills the whole
  process group with `os.killpg` before reading the verdict `timeout` (DD-10, design D6). It
  never uses `timeout`/`gtimeout` (invariant §"Portable time bounds"). `subprocess.run(timeout=…)`
  is not enough: design D6 measured it returning after 1.0 s with the shim's child `sleep` still
  alive, and a surviving pytest child can write into the tree after the gate has decided. The
  design owns the value (one 40 s budget per judge call), the latency measurement, and the 5g
  host-deadline probe for the Claude half of the spec's and design's OQ-D1.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| `reproduce.py`, `v0-blocking-contract.sh`, `v1-offline-replay.sh` and `wire-registry-grammar.py`, each with its reading; V-0's captured payload, replay rcs and `claude --version` | probe | AC-0.1, AC-0.2 |
| Shared judge module and CLI (`judge` → `TDD-JUDGE:`, `state` → `TDD-STATE:`) | module / CLI | FR-1–FR-5 |
| `_parse_tasks` `production` / `tests` fields (`_production_claims` untouched, D-A) | module | FR-2 |
| `_suite_summary` counts including errors and `no tests ran`, under the summary-line rule (SGR strip, open category axis); `run_suite`'s one predicate; the `run_suite` table above | module | FR-4 |
| Codex gate rewiring, `cwd` base, chain reader, venv shell policy with its differential | hook | FR-3, FR-5 |
| Claude gate payload read, `state` and `judge` calls, refusal function with `EXIT` trap | hook | FR-6 |
| §"Trust boundary" text; SKILL.md registry and gate bullets; agy-runtime.md sentence; codex-implementer-prompt.md bullets | docs | FR-7, OQ-2 |
| One mutation spec per FR-8 guard, plus the wire mutations below | mutation specs | FR-8 |

## Spec v1.3 ACs: where each is tested

Spec v1.3 (`b20ef027`) added or extended these ACs. Each is a pytest AC through the hook's or the
audit gate's real entry point, one fixture per case, each case run alone. "FR-8" means the guard is
in spec v1.3 AC-8.1's list, so its mutation spec must turn the named fixture red, scored on the
pytest summary, with each alternation branch mutated alone. The impl-plan assigns them to Tasks;
this table fixes the layer and the fixture, not the Task split.

| AC | Layer | Fixture(s) | Guard |
|---|---|---|---|
| AC-3.6 (OD-C) | 5 | Rows of the shell-policy differential: the `h_mad_state_write.py` argv under the contained-venv token → allow; the same argv under `/usr/bin/python3` → allow (control); the same argv under each escaping venv state → deny; a script outside the hook's `h-mad/scripts/` under the contained-venv token → deny | differential accounting ("Guard narrowing: shell policy") |
| AC-4.2 additions | 2, 3 | A skipped-only test file → DENY `no-tests-ran` (rule 8); a RED test with a passing subtest → ALLOW `red-measured`; a GREEN test with a passing subtest → DENY `test-passing` | FR-8: rule 8 (skipped-only fixture) |
| AC-4.7 additions | 2 | `run_suite` stubs, one per output: `no tests ran in 0.01s`, `1 error in 0.06s`, `3 skipped in 0.1s`, `5 deselected in 0.1s`, `1 xfailed in 0.1s` → exactly `SUITE: UNREADABLE reason=no_summary`; the coloured bytes → `FAIL`; `2 failed, 1 subtests passed in 0.02s` → `FAIL`, 0 passed; `2 passed, 2 subtests passed in 0.00s` → `PASS`, 2 passed | FR-8: the SGR strip (coloured fixture), the `subtests` category rule; the one predicate (design D7) |
| AC-6.1 addition (OD-B) | 6 step 0 | A stdin payload naming a production target, with an exempt `<root>/tests/x.py` as `$1` → still refused | FR-8: stdin-before-`$1` precedence |
| AC-6.9 exempt fixtures (OD-A) | 6 step 3 | On a `{not json` chain: writes to `docs/.bkit-memory.json`, `tests/test_x.py` and `notes.md` → each allowed, beside the production `.py` write → refused `judge-error` | FR-8: exemptions-before-governance order; the unreadable-chain refusal |
| AC-6.11 (a), (b) | 6 step 1 | (a) the only state name on the chain is a dangling symlink → refused `judge-error`; (b) no root state, `sub/docs/.bkit-memory.json` step5, target `<root>/sub/newdir/x.py` with `newdir` absent and a passing resolved test → refused | FR-8: non-regular-state and missing-parent handling, each its own mutation |
| AC-6.12 (DD-2) | 6 | A bin dir with no `jq` (the existing `_bin` helper in `test_h_mad_tdd_gate_state_resolution.py` symlinks `jq`, so this fixture does not use it unchanged), governed write, passing resolved test → refused `test-passing` | the `jq`-free path; the design's remove-DD-2 revert re-adds the allow and must turn it red |
| AC-6.13 (DD-8) | 6 step 2 | Empty target: root ACTIVE step5 → refused `judge-error`; root state unreadable → refused `judge-error`; root with no step5 record → allowed | FR-8: empty-target refusal |
| AC-6.14 (DD-9) | 6 step 4 | A target outside the root: root ACTIVE step5 with `codex` on PATH → Codex-authorship refusal; root with no step5 → allowed | FR-8: outside-root chain |
| AC-6.15 (DD-7, kept by design v1.1) | 6 step 0 | Relative `tests/x.py` and `./tests/x.py` → allowed as exempt; relative `sub/x.py` → the verdict the absolute `<root>/sub/x.py` gets | design D9's DD-7 old-versus-new differential; expected softened set exactly two cells (relative `tests/x.py`, relative `fixtures/x.py`) |

**Residual.** AC-3.6, AC-6.12 and AC-6.15 are not in spec v1.3 AC-8.1's guard list. AC-3.6 and
AC-6.15 are bounded by their differentials instead of a mutation; AC-6.12 is bounded by the
revert its DD row states. Whether they also get FR-8 mutation specs is the impl-plan's call.

## Connection enforcement (the feature is partly wiring-shaped)

Each wire ships a test that fails when the connection alone is removed and the callee is intact.
Each is mutated in both directions (invariant §"Connection enforcement").

| Wire | Remove → must fail | Force → must fail |
|---|---|---|
| W1 Codex gate → judge | a RED-measured fixture is no longer ALLOWED (AC-4.2) | a GREEN fixture is ALLOWED (AC-4.2 `test-passing`) |
| W2 Claude gate → judge CLI (`judge` verb) | AC-6.3/AC-6.4 allow again | a governed RED write is refused |
| W3 judge → `_parse_tasks` fields | AC-2.1 resolves by name map or not at all | AC-2.5 (Task authority) inverts |
| W4 judge → `_suite_summary` | AC-4.4 (rc-blindness) fails | AC-4.2 GREEN reads RED |
| W5a Codex gate → chain reader | AC-5.2 allows again (the OD-3 fail-open) | the sibling-project case of `test_codex_hook_scopes_nested_state_to_the_target_project` denies |
| W5b Claude gate → chain reader (`state` verb) | the `OD-3c` fixture (root step3, sub-project step5) allows again | a no-step5 chain is refused |
| W6 Claude gate → hook-relative judge path | the symlinked-hook test runs no judge, or the main tree's | the path is forced to tree A's `h-mad/scripts/` unconditionally: the test run through tree B's symlinked hook must fail, because tree B's judge marker is absent (fixture below) |

**W6 fixture: two distinct hook/judge trees.** A single symlinked-hook fixture cannot tell a
hook-relative judge path from one fixed to that same checkout, so the W6 test builds two:
- tree A is the worktree's own `h-mad/`;
- tree B is a scratch copy holding `hooks/h-mad-tdd-gate.sh` and a judge at the same relative
  path, whose judge prints a valid verdict line and writes a tree-B marker file;
- the test runs tree B's hook through a symlink placed outside both trees, and asserts that
  tree B's marker was written and the verdict is tree B's judge's.

The force mutation replaces the hook's resolved-path computation with tree A's absolute
`h-mad/scripts/` path; the tree-B test must then fail. The remove mutation restores the
`$HOME/.claude/skills` lookup; the tree-B test must fail too.

Wire W7 (`_production_claims` → `_parse_tasks`) is withdrawn with the rewrite (D-A).

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| R1: V-0 reads `INCONCLUSIVE`, or no form is proven (`CHOSEN=none`) | FR-6's refusal form cannot be chosen | **Halt to the operator. The feature does not merge.** The halt reason from the probe is fixed and V-0 is re-run. AC-6.1–AC-6.4 may be implemented in the worktree meanwhile, but nothing merges (spec v1.1 AC-6.7) |
| R2: `grok-codex-fallback`'s impl-plan asserts the Claude gate's `exit 1` | After this merges with form (a) or (b), its BLOCK-GROK / BLOCK-INVALID tests and mutation anchors assert a form the gate no longer uses. Its worktree is already in Phase 5 (`git worktree list` → `~/orca/skills-grok-codex-fallback` on `feature/216-grok-codex-fallback`, at `2f262f8a`) | The R2 census below the table → 7 gate-assertion lines: 3 `exit 1 ;;` case arms, 2 AC prose lines, 2 mutation rows. Owed to that impl-plan (report). Its new refusals must use this feature's refusal function. The rebase contract is design D13: the `fallback_agent` value arrives as the fourth `record=` field of the `state` line (no `jq`, DD-2), the fold over records lives in the judge, the refusals are `_refuse fallback-grok` / `_refuse fallback-invalid` in the chosen form, and grok's Task 12 re-plans onto it (owed by grok's documents, not done here) |
| R3: `_parse_tasks`' dict gains keys | A consumer that iterates or serialises the dict changes output | P4's three consumers' suites run unmodified, and spec v1.2 AC-2.9's same-ids-same-order check over the corpus. The registry's own grammar is untouched (D-A) |
| R4: no `.venv` in a governed project, and the hook's `python3` has no pytest | Every Claude-fallback write in this repository is DENY `pytest-missing` (P8): fail-closed but blocking | The deny reason names the remedy (create a contained `.venv`). OQ-1 goes to the operator. No knob (spec) |
| R5: the worktree hook calls the main tree's scripts, or a worktree test runs the main tree's hook | Tests green for the wrong reason | Hook-relative judge path and the two-tree W6 test; both test modules' `HOOK` resolved from `Path(__file__)` (layer 6) |
| R6: a pre-existing test is deleted, or weakened under the same node id, while counts stay green | Compatibility NFR silently false | Node-id floor **and** the function-body diff (Success Criteria) |
| R7: the `run_suite` edit drifts or duplicates `audit_suite_gate.json` anchors | A guard stops being mutation-tested | `--check-anchors` at 5g; the anchor-occurrence rule; re-anchor in the same commit |
| R8: a V-0 session writes some other file, or invokes the hook for another path | A false reading | Per-arm nonce in the sentinel name. Only a Write whose path ends in that sentinel's basename logs `HIT <nonce> <path>`, and presence is scored at every logged path. An arm with no such line is `UNMEASURED`: a halt for E1, E2, E0 and the capture arm, `FORM_B=INCONCLUSIVE` for EJ |
| R9: V-0's isolation flags (`--setting-sources project --strict-mcp-config`) change session behaviour in a way not measured here | The sessions fail and every arm halts | A halt is `INCONCLUSIVE` → R1. The flags exist in `claude --help` (2.1.283), and their live effect has not been observed |
| R10: the objects HemaSuite `1fbf8022` / HemaSuite `31bfcfe4` become unreachable (branch rewritten, gc) | V-1r cannot run | The script halts `UNMEASURED` on `git archive`. Re-pin to the rewritten Task 7 commit and its parent, and say so |

**R2 census** (in a fenced block, because a table cell must escape `|` as `\|`, and that escape
copied raw into `grep -E` matches a literal `|`). Run in `bash --noprofile --norc`, unit: matching
lines:

```bash
grep -n 'exit 1' docs/01-plan/features/grok-codex-fallback.impl-plan.md | grep -cE 'exit 1 ;;$|BLOCK-|test_gate_matrix'
# reading at 2f262f8a, again at dfd5f02e, and again at 34c0e962 (file last changed 5a9cd8ed): 7
```

The broader v1.0 command (plan v1.0's R2 cell) matches 16 lines, 9 of them `exit 1` in that
plan's verification scripts (v1.1 reading, reproduced by the v1.1 delta review, not re-run here). BSD `grep` without `-E` reads `$` before `\|` literally and prints 4.

## Convention Prerequisites

- **Worktree.** `~/.claude/skills/h-mad` is a live symlink into this checkout (P10), so the
  implementation runs in
  `git worktree add ../skills-codex-tdd-gate-defects -b feature/codex-tdd-gate-defects`, from the
  base recorded in the state record at 5c. No edit of `h-mad/` happens in the main checkout. At
  `2f262f8a`, `git worktree list` shows the main checkout and `~/orca/skills-grok-codex-fallback`
  (`feature/216-grok-codex-fallback`). No branch or worktree for this feature exists.
- **Interpreter and suites.** Every pytest command is
  `/opt/anaconda3/bin/python -m pytest … -p no:cacheprovider` (P8), with the coupled suites named
  explicitly: `h-mad/tests handoff/tests handoff/scripts`.
  - Collection at `01121ca7`, `… --collect-only -q <dir> | tail -1` (unit: tests collected):
    `h-mad/tests` 3552, `handoff/tests` 201, `handoff/scripts` 140, all three together 3893. These
    paths are unchanged at `2f262f8a` (Verified premises).
  - Full run at `01121ca7`:
    `/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts | tail -1`
    → `1 failed, 3892 passed, 1 warning in 605.79s`.
  - The one failure is
    `h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`.
    It reads the installed `claude` binary and is outside this feature's files. It is the only
    failure a task may leave, and only for that reason; the grok-codex-fallback impl-plan carries
    the same carve-out.
  - These figures move with every merge ahead of this branch, and are re-measured at the
    worktree's base.
- **Merge order: this feature → `grok-codex-fallback` → `multi-host-runtime`.** Shared files are
  derived from the sibling documents at `01121ca7`:
  - grok: `git show HEAD:docs/01-plan/features/grok-codex-fallback.impl-plan.md | grep -oE '\*\*(Production|Test) file\*\*:.*' | grep -oE '`[^`]+`' | tr -d '`' | sort -u | grep -v /tests`;
  - multi-host: its plan's §"Convention Prerequisites" table.

  `git grep -c h_mad_wire_registry` over both sibling documents → 0 matching lines each, at
  `2f262f8a`.

  | File | This feature | `grok-codex-fallback` | `multi-host-runtime` |
  |---|---|---|---|
  | `h-mad/hooks/h-mad-tdd-gate.sh` | edits (payload, `state`/`judge`, form, trap) | edits (`fallback_agent`, BLOCK-GROK/INVALID) | reads (grok adapter AC-5.2) |
  | `h-mad/hooks/h-mad-codex-tdd-gate.py` | edits | not touched (its plan) | reads |
  | `h-mad/references/codex-runtime.md` | edits §"Trust boundary" | not a production file | edits |
  | `h-mad/SKILL.md` | edits (registry, gate bullets) | edits | edits |
  | `h-mad/references/agy-runtime.md` | edits one sentence (if form (b)) | not a production file | edits (construct mapping) |
  | `h-mad/references/codex-implementer-prompt.md` | edits two bullets | not named | not named |
  | `h-mad/scripts/h_mad_audit_gate.py` | edits | not a production file | not named |
  | `h-mad/scripts/h_mad_wire_pin_gate.py` | edits | not a production file | not named |
  | `h-mad/scripts/h_mad_wire_registry.py` | not edited (D-A); its tests run unmodified | not named | not named |
  | `h-mad/scripts/h_mad_assemble_tdd.py` | reads (`_parse_tasks` consumer) | edits | not named |
  | `h-mad/scripts/h_mad_audit_cycle.py` | reads (`run_suite` consumer) | edits | not named |

  - **Textual overlaps:** the Claude hook, `SKILL.md`, `codex-runtime.md` and `agy-runtime.md`.
  - **Semantic overlaps:** grok's edits to the two consumers of the functions this feature extends.
  - The later features rebase onto this one and re-run their own premises. multi-host-runtime's
    table still says this feature does not name `h-mad/SKILL.md`, which this plan changes (owed;
    see report).
- **Step P0: commit the probes.** This has been owed by the orchestrator since the spec; spec
  §"Measured premises" and AC-0.1 cite the directory. Run it from the repository root, in the main
  checkout (docs only), before the worktree is cut:

  ```bash
  D=docs/03-analysis/probes/codex-tdd-gate-defects
  cat > "$D/reproduce.py" <<'PY'
#!/usr/bin/env python3
"""Re-derive the codex-tdd-gate-defects spec premises against a skills tree.

Usage: reproduce.py <skills-root> <python-without-pytest> <python-with-pytest>
Prints one `REPRO:` line per reading. Scratch fixtures live in a TemporaryDirectory.
A Claude-gate reading is (rc, stdout permissionDecision or "", first stderr line), so a
refusal in either blocking form reads differently from an allow.
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
    try:
        decision = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else ""
    except (ValueError, KeyError, TypeError):
        decision = "unparsed"
    return r.returncode, decision, (r.stderr.strip().splitlines() or [""])[0][:90]


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
# OD-3c: Claude gate. Root state holds only a step3 record; the sub-project state holds the step5
# record (codex exhausted). The root-first reader never sees the step5 -> allowed. Control: no root state.
def od3c(t: Path, root_state: bool):
    r = fixture(t, True, "exhausted")
    (r / "hematology-paper-writer/docs/.bkit-memory.json").write_text((r / "docs/.bkit-memory.json").read_text())
    if root_state:
        (r / "docs/.bkit-memory.json").write_text(json.dumps({"orchestrator_state": {"other": {"phase": "step3"}}}))
    else:
        (r / "docs/.bkit-memory.json").unlink()
    return claude(r, bindir(t, True), arg=str(r / t_rel))
run("OD-3c claude-root-first", lambda t: od3c(t, True))
run("OD-3c control-noroot", lambda t: od3c(t, False))
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
  shasum -a 256 "$D/reproduce.py" | grep -q '^45f763ee14162b4747fe1c3dee3afa1478f9cc86d2599717f3993bd34939d974 ' || exit 1
  cat > "$D/v0-blocking-contract.sh" <<'SH'
#!/bin/bash
# V-0 (spec v1.1 FR-0; plan v1.2): which PreToolUse refusal forms does Claude Code honour for Write?
# Arms: E1 = exit 1, E2 = exit 2 (form a), EJ = rc 0 + JSON permissionDecision deny (form b),
# E0 = exit 0 (negative control). Each arm has its own nonce, carried in its sentinel file name.
# Proof that an arm's session reached the hook's refusal branch is a log line carrying THAT
# arm's nonce, written only for tool_name=Write on that arm's sentinel. Any other invocation
# logs nothing. Presence is scored at every path the arm's session HIT lines logged, never at an
# assumed path. Run from a cwd OUTSIDE every repository. Every halt is `exit 1` and means the
# reading is INCONCLUSIVE, never a pass. Arm EJ alone may be UNMEASURED without a halt: it then
# reads FORM_B=INCONCLUSIVE, and READING is still scored over E1/E2/E0 (spec v1.1 FR-0).
S="$(mktemp -d "${TMPDIR:-/tmp}/hmad-v0.XXXXXX")" || exit 1
git -C "$S" rev-parse --show-toplevel >/dev/null 2>&1 && { echo "V-0: HALT scratch is inside a git repo"; exit 1; }
command -v jq >/dev/null || { echo "V-0: HALT no jq"; exit 1; }
claude --version > "$S/claude.version" || { echo "V-0: HALT claude --version"; exit 1; }

nonce() { od -An -N8 -tx1 /dev/urandom | tr -d ' \n'; }

unmeasured() {  # $1 = arm, $2 = why. EJ is recorded and the run goes on; any other arm halts.
  echo "V-0: $1 UNMEASURED $2"
  [ "$1" = EJ ] || exit 1
  EJ_UNMEASURED=1
}

mkhook() {  # $1 = arm, $2 = sentinel basename, $3 = refusal: 1 | 2 | json | 0 | cap
  {
    printf '#!/bin/bash\np=$(cat)\n'
    printf 't=$(printf "%%s" "$p" | jq -r ".tool_name // empty")\n'
    printf 'f=$(printf "%%s" "$p" | jq -r ".tool_input.file_path // empty")\n'
    printf '[ "$t" = Write ] || exit 0\n'
    printf 'case "$f" in */%s|%s) ;; *) exit 0;; esac\n' "$2" "$2"
    printf 'printf "HIT %%s %%s\\n" %q "$f" >> %q\n' "${2#SENTINEL_}" "$S/$1.log"
    case "$3" in
      cap)  printf 'printf "%%s" "$p" > %q\nexit 0\n' "$S/payload.json" ;;
      0)    printf 'exit 0\n' ;;
      json) printf 'printf "%%s\\n" %q\nexit 0\n' \
              '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"V-0 arm EJ refuses"}}' ;;
      *)    printf 'echo "V-0 arm %s refuses" >&2\nexit %s\n' "$1" "$3" ;;
    esac
  } > "$S/hook.$1.sh" || exit 1
  chmod +x "$S/hook.$1.sh" || exit 1
  jq -n --arg c "$S/hook.$1.sh" \
    '{hooks:{PreToolUse:[{matcher:"Write",hooks:[{type:"command",command:$c}]}]}}' \
    > "$S/settings.$1.json" || exit 1
}

attempt() {  # $1 = arm, $2 = sentinel basename; a real session is asked to Write the sentinel
  mkdir "$S/$1" || exit 1
  (cd "$S/$1" && claude -p "Use the Write tool to create $2 in the current directory containing exactly: X = 1" \
      --settings "$S/settings.$1.json" --setting-sources project --strict-mcp-config \
      --tools Write --permission-mode acceptEdits \
      --no-session-persistence --output-format json > "$S/$1.out.json" 2> "$S/$1.err")
  grep -q "^HIT ${2#SENTINEL_} " "$S/$1.log" 2>/dev/null \
    || unmeasured "$1" "no_hit_for_nonce ${2#SENTINEL_}"
}

N_cap="SENTINEL_cap$(nonce).py"
mkhook cap "$N_cap" cap; attempt cap "$N_cap"
F=$(jq -r '.tool_input.file_path // empty' "$S/payload.json") || exit 1
case "$F" in */"$N_cap") ;; *) echo "V-0: HALT captured payload file_path is not the cap sentinel"; exit 1;; esac

for arm in E1:1 E2:2 EJ:json E0:0; do
  a=${arm%%:*} want=${arm##*:}
  n="SENTINEL_${a}$(nonce).py"
  eval "N_$a=\$n"
  mkhook "$a" "$n" "$want"
  # Replay the captured payload, re-pointed at this arm's sentinel (jq, not hand-written JSON).
  jq --arg f "$S/$a/$n" '.tool_input.file_path = $f' "$S/payload.json" > "$S/payload.$a.json" || exit 1
  out=$("$S/hook.$a.sh" < "$S/payload.$a.json" 2>/dev/null); rc=$?
  dec=$(printf '%s' "$out" | jq -r '.hookSpecificOutput.permissionDecision // empty' 2>/dev/null)
  echo "V-0: replay $a rc=$rc decision=${dec:-none}" | tee -a "$S/replay.txt"
  case "$want" in
    json) ok=$([ "$rc" = 0 ] && [ "$dec" = deny ] && echo y) ;;
    *)    ok=$([ "$rc" = "$want" ] && [ -z "$dec" ] && echo y) ;;
  esac
  [ "$ok" = y ] || { unmeasured "$a" "replay rc=$rc want=$want decision=${dec:-none}"; continue; }
  grep -q "^HIT ${n#SENTINEL_} " "$S/$a.log" || { unmeasured "$a" replay_no_hit; continue; }
  mv "$S/$a.log" "$S/$a.replay.log" || exit 1   # the replay must not count as the session's hit
  attempt "$a" "$n"
done

p() {  # present if ANY path this arm's session logged exists; a relative one is the session cwd's
  local n f r=absent
  eval "n=\$N_$1"
  while read -r _ _ f; do
    case "$f" in /*) ;; *) f="$S/$1/$f" ;; esac
    [ -e "$f" ] && r=present
  done < <(grep "^HIT ${n#SENTINEL_} " "$S/$1.log")
  echo "$r"
}
E1=$(p E1) E2=$(p E2) E0=$(p E0)
if [ -n "$EJ_UNMEASURED" ]; then EJ=UNMEASURED; else EJ=$(p EJ); fi
case "$E1/$E2/$E0" in
  absent/absent/present)  R=E1_BLOCKS ;;
  present/absent/present) R=E1_DOES_NOT_BLOCK ;;
  *)                      R=INCONCLUSIVE ;;
esac
form() {
  [ "$E0" = present ] || { echo INCONCLUSIVE; return; }
  case "$1" in absent) echo BLOCKS ;; present) echo DOES_NOT_BLOCK ;; *) echo INCONCLUSIVE ;; esac
}
FA=$(form "$E2") FB=$(form "$EJ")
# Spec v1.1 AC-6.5 / AC-6.6: on either conclusive branch the form is (b) when FORM_B=BLOCKS, else (a)
# when FORM_A=BLOCKS. `exit 1` is never a chosen form.
case "$R/$FA/$FB" in
  E1_DOES_NOT_BLOCK/*/BLOCKS|E1_BLOCKS/*/BLOCKS)   C=b ;;
  E1_DOES_NOT_BLOCK/BLOCKS/*|E1_BLOCKS/BLOCKS/*)   C=a ;;
  *)                                               C=none ;;
esac
echo "V-0: READING=$R FORM_A=$FA FORM_B=$FB CHOSEN=$C E1=$E1 E2=$E2 EJ=$EJ E0=$E0 claude=$(head -1 "$S/claude.version") scratch=$S"
SH
  shasum -a 256 "$D/v0-blocking-contract.sh" | grep -q '^04700d9ffc254a603387f4baf1a62a1b115956fd410d88c3484db3fc50ddaff4 ' || exit 1
  cat > "$D/v1-offline-replay.sh" <<'V1R'
#!/bin/bash
# V-1 offline (plan v1.2): replay the HemaSuite #28 Task 7 incident against a skills tree's Codex
# gate, read-only on HemaSuite. Usage: v1-offline-replay.sh <skills-tree> <hemasuite-checkout>
# HemaSuite is only READ: `git archive` / `git show` of two pinned commits, and an APFS clone
# (`cp -c`) of its hematology-paper-writer/.venv. Every pytest run happens in the scratch copies.
# RED  = the tree before Task 7's commit plus that commit's test file (the incident's state:
#        the RED test existed, the production change did not).
# GREEN = Task 7's commit (the same test now passes): the denying control.
# Every halt is `exit 1` and means the reading is UNMEASURED, never a pass. A completed run scores
# each of the six gate lines against its post-merge pass condition (one `V-1r: CHECK` line each)
# and exits 0 only on `VERDICT=PASS`; any failed check gives `VERDICT=FAIL` and exit 2.
SK=$(cd "$1" && pwd -P) || exit 1
H=$(cd "$2" && pwd -P) || exit 1
GREEN_SHA=31bfcfe4 SUB=hematology-paper-writer  # `shared/` rides along: the sub-project conftest puts the git root on sys.path
PLAN=docs/01-plan/features/review-manifest-guideline-evidence.impl-plan.md
TEST=tests/test_certificate_lock_removed.py PROD=tools/review_round/guideline_excerpts.py
# Task 7's Test entries, in plan order: the judge's candidate set for PROD (FR-2 rule 4).
TESTS="$TEST tests/test_review_guideline_pdf_excerpts.py tests/test_review_qualitative_assets.py tests/test_review_intake_wiring.py"
RED_SHA=$(git -C "$H" rev-parse --short "$GREEN_SHA^") || exit 1
S="$(mktemp -d "${TMPDIR:-/tmp}/hmad-v1r.XXXXXX")" || exit 1

snapshot() {  # $1 = name, $2 = sha whose tree is used, $3 = sha the test file comes from
  local R="$S/$1"
  mkdir -p "$R/docs/01-plan/features" || exit 1
  git -C "$H" archive "$2" "$SUB" shared | tar -x -C "$R" || { echo "V-1r: HALT archive $2"; exit 1; }
  git -C "$H" show "$3:$SUB/$TEST" > "$R/$SUB/$TEST" || { echo "V-1r: HALT test blob $3"; exit 1; }
  git -C "$H" show "$2:$PLAN" > "$R/$PLAN" || { echo "V-1r: HALT impl-plan $2"; exit 1; }
  # State is synthesized, not copied: the root holds the step5 record, the sub-project a state
  # file with none (the OD-3 layout measured in HemaSuite, plan P9).
  printf '%s\n' '{"orchestrator_state":{"review-manifest-guideline-evidence":{"phase":"step5"}}}' > "$R/docs/.bkit-memory.json"
  mkdir -p "$R/$SUB/docs" && printf '%s\n' '{"orchestrator_state":{}}' > "$R/$SUB/docs/.bkit-memory.json" || exit 1
  cp -cR "$H/$SUB/.venv" "$R/$SUB/.venv" || { echo "V-1r: HALT venv clone (needs APFS clonefile)"; exit 1; }
  git init -q "$R" || exit 1
  # Independent control: each candidate test, run directly by the cloned venv, no gate involved.
  for t in $TESTS; do
    last=$(cd "$R/$SUB" && PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest "$t" -q --no-header -p no:cacheprovider 2>&1 | tail -1)
    echo "V-1r: direct $1 tree=$2 $t last=$last" | tee -a "$S/reading.txt"
  done
}

gate() {  # $1 = snapshot, $2 = label, $3 = payload json (cwd is the sub-project)
  local R="$S/$1" out rc
  out=$(cd "$R/$SUB" && env -u CODEX_PROJECT_DIR python3 "$SK/h-mad/hooks/h-mad-codex-tdd-gate.py" <<<"$3"); rc=$?
  echo "V-1r: gate $1 $2 rc=$rc out=${out:-<empty>}" | tee -a "$S/reading.txt"
  k="$1_$(printf '%s' "$2" | tr - _)"
  eval "RC_$k=\$rc"; eval "OUT_$k=\$out"
}
is_allow() {  # $1 = key: rc 0 and an empty or `{}` stdout
  eval "rc=\$RC_$1"; eval "out=\$OUT_$1"
  [ "$rc" = 0 ] && { [ -z "$out" ] || [ "$out" = "{}" ]; }
}
is_deny() {  # $1 = key, $2 = a word the deny must also carry (optional)
  eval "out=\$OUT_$1"
  case "$out" in *'"deny"'*) ;; *) return 1 ;; esac
  [ -z "$2" ] || case "$out" in *"$2"*) ;; *) return 1 ;; esac
}
FAILS=0
check() {  # $1 = check name, rest = the predicate
  local name=$1 v=PASS; shift
  "$@" || { v=FAIL; FAILS=$((FAILS + 1)); }
  echo "V-1r: CHECK $name $v" | tee -a "$S/reading.txt"
}

snapshot red "$RED_SHA" "$GREEN_SHA"
snapshot green "$GREEN_SHA" "$GREEN_SHA"
case "$(grep "^V-1r: direct red .* $TEST " "$S/reading.txt")" in *" failed"*) ;; *) echo "V-1r: HALT red snapshot's first candidate is not RED"; exit 1;; esac
while read -r line; do
  case "$line" in *" failed"*|*" error"*) echo "V-1r: HALT green snapshot is not GREEN: $line"; exit 1;; *" passed"*) ;; *) echo "V-1r: HALT no summary: $line"; exit 1;; esac
done < <(grep '^V-1r: direct green ' "$S/reading.txt")

for snap in red green; do
  cwd="$S/$snap/$SUB"
  gate "$snap" patch "$(jq -cn --arg c "$cwd" --arg p "*** Update File: $PROD
" '{tool_name:"apply_patch",cwd:$c,tool_input:{patch:$p}}')"
  gate "$snap" shell-pytest "$(jq -cn --arg c "$cwd" --arg x ".venv/bin/python -m pytest $TEST" '{tool_name:"shell_command",cwd:$c,tool_input:{command:$x}}')"
  gate "$snap" shell-write "$(jq -cn --arg c "$cwd" --arg x ".venv/bin/python -c \"open('x','w')\"" '{tool_name:"shell_command",cwd:$c,tool_input:{command:$x}}')"
done
check red-patch-allows is_allow red_patch
check green-patch-denies-test-passing is_deny green_patch test-passing
check red-shell-pytest-allows is_allow red_shell_pytest
check green-shell-pytest-allows is_allow green_shell_pytest
check red-shell-write-denies is_deny red_shell_write
check green-shell-write-denies is_deny green_shell_write
V=PASS; [ "$FAILS" = 0 ] || V=FAIL
echo "V-1r: DONE VERDICT=$V fails=$FAILS/6 skills=$(git -C "$SK" rev-parse --short HEAD) hemasuite_red=$RED_SHA hemasuite_green=$GREEN_SHA scratch=$S"
[ "$V" = PASS ] || exit 2
V1R
  shasum -a 256 "$D/v1-offline-replay.sh" | grep -q '^8dd639240265d338ee24aa6a52e80929302c52c14ee8c41b8bb9360cd2e4ee10 ' || exit 1
  cat > "$D/wire-registry-grammar.py" <<'WRG'
#!/usr/bin/env python3
"""Where h_mad_wire_registry._production_claims and _parse_tasks disagree today.

Usage: wire-registry-grammar.py <skills-root> <hemasuite-root>
Corpus: tracked, non-archive/ `*.impl-plan.md` files of both repositories (git ls-files).
Prints one `WRGRAMMAR:` line. Units: files, and matching lines.
"""
import re, subprocess, sys
from pathlib import Path

SK, HS = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(SK / "h-mad/scripts"))
sys.dont_write_bytecode = True
from h_mad_wire_pin_gate import _parse_tasks  # noqa: E402

files = []
for root in (SK, HS):
    out = subprocess.run(["git", "-C", str(root), "ls-files", "*.impl-plan.md"],
                         capture_output=True, text=True, check=True).stdout.split()
    files += [root / f for f in out if "archive/" not in f]
TOKEN = re.compile(r"`([^`]+\.py)`")
# The registry's own grammar, copied from _production_claims (task counter and label).
REG_TASK = re.compile(r"^\s*#{2,3}\s+[MT]\d+")
REG_LABEL = re.compile(r"^\s*(?:[-*•]\s+)?\*{0,2}Production file\*{0,2}\s*:\s*(.*)$", re.I)
# The spec FR-2 label axis: Production file | Production files | Production, colon in or out of bold.
AXIS_LABEL = re.compile(r"^\s*(?:[-*•]\s+)?\*{0,2}\s*Production(?: files?)?\s*\*{0,2}\s*:\s*\*{0,2}\s*(.*)$", re.I)
div, multi, unread = [], 0, 0
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    reg_tasks = sum(1 for ln in text.splitlines() if ln.lstrip().startswith("## Task ") or REG_TASK.match(ln))
    if reg_tasks != len(_parse_tasks(text)):
        div.append(f"{f.name}:{len(_parse_tasks(text))}/{reg_tasks}")
    for ln in text.splitlines():
        m = REG_LABEL.match(ln)
        if m and len(TOKEN.findall(m.group(1))) >= 2:
            multi += 1
        if AXIS_LABEL.match(ln) and not m:
            unread += 1
print(f"WRGRAMMAR: files={len(files)} task_counter_divergent_files={len(div)} "
      f"singular_label_multi_path_lines={multi} axis_label_lines_unread_by_registry={unread} "
      f"divergent=[{' '.join(div)}]")
WRG
  shasum -a 256 "$D/wire-registry-grammar.py" | grep -q '^9d20448039ca662b646981fbb57ddc1879fa852faaaa4dbef2b0654150b82650 ' || exit 1
  SHA=$(git rev-parse --short HEAD) || exit 1
  /opt/homebrew/bin/python3 "$D/reproduce.py" . /opt/homebrew/bin/python3 /opt/anaconda3/bin/python > "$D/reproduce.reading.$SHA.txt" || exit 1
  test "$(grep -c '^REPRO:' "$D/reproduce.reading.$SHA.txt")" = 24 || exit 1
  grep -q "^REPRO: D3 nopytest (0, 'allow'" "$D/reproduce.reading.$SHA.txt" || exit 1
  grep -q "^REPRO: OD-3 nearest-state (0, 'allow'" "$D/reproduce.reading.$SHA.txt" || exit 1
  grep -q "^REPRO: OD-4 tool_input (0, '', '')" "$D/reproduce.reading.$SHA.txt" || exit 1
  grep -q "^REPRO: OD-3c claude-root-first (0, '', '')" "$D/reproduce.reading.$SHA.txt" || exit 1
  grep -q "^REPRO: OD-5 nopytest (0, '', '')" "$D/reproduce.reading.$SHA.txt" || exit 1
  python3 "$D/wire-registry-grammar.py" . /Users/kimhawk/orca/HemaSuite > "$D/wire-registry-grammar.reading.$SHA.txt" || exit 1
  grep -q '^WRGRAMMAR: files=' "$D/wire-registry-grammar.reading.$SHA.txt" || exit 1
  bash "$D/v1-offline-replay.sh" . /Users/kimhawk/orca/HemaSuite > "$D/v1-offline-replay.reading.$SHA.txt"; V1RC=$?
  # Pre-merge the gate is unfixed: the replay must complete and FAIL its post-merge checks (exit 2),
  # never halt (exit 1) and never pass (exit 0).
  test "$V1RC" = 2 || exit 1
  grep -q '^V-1r: DONE VERDICT=FAIL fails=4/6 ' "$D/v1-offline-replay.reading.$SHA.txt" || exit 1
  grep -q '^V-1r: CHECK red-patch-allows FAIL$' "$D/v1-offline-replay.reading.$SHA.txt" || exit 1
  ```

  - **The 24** is the probe's own line count: 17 gate and summary lines plus 7 `run_suite` lines. It
    is a property of the probe, not of the tree. v1.0's probe printed 22; the two `OD-3c` lines are
    new.
  - **Post-merge.** The five fail-open readings (`D3 nopytest`, `OD-3 nearest-state`,
    `OD-4 tool_input`, `OD-3c claude-root-first`, `OD-5 nopytest`) are **expected to become
    refusals**. The probe is then the regression witness, and its post-merge reading is committed
    beside the first.
  - **The wire-registry reading** is published in "Second Production grammar (residual)". It
    moves with every impl-plan commit, in either repository.
  - **This P0 block was executed as written** in this revision, with `D` pointed at a scratch
    directory, from the repository root at skills `b327e8bf` (it differs from `dfd5f02e` only in
    `docs/02-design/`), HemaSuite `3f0c9f3a`: rc 0. Every sha256 pin matched; `reproduce.py` printed
    24 `REPRO:` lines; `wire-registry-grammar.py` printed `files=83 task_counter_divergent_files=4
    singular_label_multi_path_lines=16 axis_label_lines_unread_by_registry=64`; the V-1r replay
    exited 2 with the reading below.
  - **The pre-merge V-1r reading** at skills `dfd5f02e`, HemaSuite red `1fbf8022` / green
    `31bfcfe4` (the same six gate lines at `b327e8bf` in the P0 run above):
    - Direct control, RED snapshot: `tests/test_certificate_lock_removed.py` → `7 failed, 2 passed`.
    - Direct control, GREEN snapshot: all four candidates pass (`9 passed`, `10 passed`,
      `30 passed`, `17 passed`).
    - Today's gate denies all six payloads (unit: `V-1r: gate` lines carrying `"deny"`: 6). Both
      `patch` lines deny "requires a failing test before tools/review_round/guideline_excerpts.py;
      no derived test file exists". All four `shell-*` lines deny "permits only explicit test,
      read-only, and H-MAD control commands". That is the incident, reproduced from its own
      artifacts.
    - The checks read `red-patch-allows FAIL`, `green-patch-denies-test-passing FAIL`,
      `red-shell-pytest-allows FAIL`, `green-shell-pytest-allows FAIL`, and both
      `*-shell-write-denies PASS`: `VERDICT=FAIL fails=4/6`, exit 2. So the post-merge check has
      been observed failing against the unfixed gate.
    - **Positive and single-branch controls**, run against a stub gate in a scratch skills tree
      (then deleted): a stub that allows the RED patch, denies the GREEN patch with `test-passing`,
      admits both `shell-pytest` payloads and denies both `shell-write` payloads reads
      `VERDICT=PASS fails=0/6`, exit 0; the same stub allowing the GREEN patch reads
      `green-patch-denies-test-passing FAIL`, `VERDICT=FAIL fails=1/6`, exit 2.
    - HemaSuite was not written: `git -C <HemaSuite> --no-optional-locks status --porcelain`
      hashed the same before and after the `dfd5f02e` run.
- **V-0: the blocking-contract probe** (verification, not pytest). It needs real Claude Code
  sessions, and it is run by the operator or the orchestrator from a cwd outside every repository,
  after P0 and before the FR-6 blocking-form task:

  ```bash
  cd "${TMPDIR:-/tmp}" || exit 1
  bash /Users/kimhawk/orca/skills/docs/03-analysis/probes/codex-tdd-gate-defects/v0-blocking-contract.sh | tee v0.out || exit 1
  grep -q '^V-0: READING=\(E1_BLOCKS\|E1_DOES_NOT_BLOCK\) FORM_A=[A-Z_]* FORM_B=[A-Z_]* CHOSEN=\(a\|b\) ' v0.out || exit 1
  ```

  - **Arms and proof.**
    - There are five sessions: a capture arm, then E1 (`exit 1`), E2 (`exit 2`, form (a)), EJ
      (rc 0 plus JSON `permissionDecision: deny`, form (b)) and E0 (`exit 0`).
    - Each arm's sentinel file name carries a fresh nonce. The arm's hook writes `HIT <nonce> <path>`
      only when `tool_name` is `Write` and `file_path` ends in that sentinel's basename, and only on
      its refusal (or, for E0, match) branch.
    - An arm whose session leaves no `HIT` line with its own nonce is `UNMEASURED`. For E1, E2 and
      E0 (and the capture arm) that halts the run; for EJ it is recorded and the run goes on, and
      EJ reads `UNMEASURED`, so `FORM_B=INCONCLUSIVE` (spec v1.1 FR-0: the three-valued reading
      depends on E1, E2 and E0 only). The same holds for a failed hand replay.
    - **Presence is scored at the path the session actually wrote**, not at an assumed one: `p()`
      reads every `HIT` line of the arm's session log and reports `present` when any logged path
      exists (a relative path is taken against the arm's session directory). A session that Writes
      the sentinel's basename into another directory is therefore scored there.
    - Each arm's hand replay of the captured payload, re-pointed at the arm's sentinel with `jq`,
      must return its rc: 1, 2, 0 with `decision=deny`, or 0. It must log its own `HIT`, which is
      then moved aside so that it cannot stand in for the session's.
  - **Readings** (spec v1.1 FR-0, AC-0.2).
    - `READING` is the spec's three-valued reading over E1/E2/E0.
    - `FORM_A` and `FORM_B` are per-form: `BLOCKS` when that arm's sentinel is absent while E0's is
      present, `DOES_NOT_BLOCK` when both are present, and `INCONCLUSIVE` when E0's sentinel is
      absent or the arm is `UNMEASURED`.
  - **Choice** (spec v1.1 AC-6.5 / AC-6.6, orchestrator decision D-C). On either conclusive reading
    the form is (b) when `FORM_B=BLOCKS`, otherwise (a) rc 2 (`FORM_A=BLOCKS` holds on both
    conclusive readings, because both require E2 absent and E0 present). `exit 1` is never chosen,
    so `rc1` is not a value of `CHOSEN=`. `CHOSEN=none` or `READING=INCONCLUSIVE` fails the last
    `grep`, halts to the operator, and blocks the merge (R1).
  - **Isolation.** `--setting-sources project --strict-mcp-config` keeps the user's own
    PreToolUse hooks, including the installed gate, and MCP servers out of the sessions. The
    arm's hook arrives through `--settings`, which still applies. The effect of these flags on a
    live session is unverified (R9).
  - **Exercised offline, not live.** In this revision the embedded script (the bytes pinned above)
    ran against a throwaway fake `claude` on PATH that invokes the settings hook with a
    Claude-Code-shaped payload, from a scratch `TMPDIR`, under `bash` 5 and again under
    `/bin/bash` 3.2.57 for four modes. Mode → reading, each run alone:
    - honours rc 2 and JSON deny → `E1_DOES_NOT_BLOCK FORM_A=BLOCKS FORM_B=BLOCKS CHOSEN=b`;
    - honours any rc≠0 and JSON deny → `E1_BLOCKS FORM_A=BLOCKS FORM_B=BLOCKS CHOSEN=b`;
    - honours any rc≠0 only → `E1_BLOCKS FORM_A=BLOCKS FORM_B=DOES_NOT_BLOCK CHOSEN=a`;
    - honours rc 2 only → `E1_DOES_NOT_BLOCK FORM_A=BLOCKS FORM_B=DOES_NOT_BLOCK CHOSEN=a`;
    - never writes → `INCONCLUSIVE FORM_A=INCONCLUSIVE FORM_B=INCONCLUSIVE CHOSEN=none`;
    - never invokes the hook → halt `cap UNMEASURED no_hit_for_nonce`;
    - writes a different file in every arm → halt at `cap`;
    - writes a different file in E1 and E2 only → halt `E1 UNMEASURED no_hit_for_nonce`;
    - honours rc 2 and JSON deny, but E1's session writes the same basename into another directory
      → `E1_DOES_NOT_BLOCK … CHOSEN=b` (the v1.1 script read this as a false `E1_BLOCKS`,
      measured on the v1.1 bytes in the same run);
    - honours rc 2 only, and EJ's session never invokes the hook → `EJ UNMEASURED`, then
      `E1_DOES_NOT_BLOCK FORM_A=BLOCKS FORM_B=INCONCLUSIVE CHOSEN=a` (the v1.1 script halted);
    - a bare-basename `file_path` in the payload → halt `captured payload file_path is not the cap
      sentinel` (the capture check requires a `/` before the basename; a halt, never a reading).

    The two `E1_BLOCKS` modes read `CHOSEN=rc1` on the v1.1 bytes. The last `grep` above was run
    over five sample reading lines: it accepts `CHOSEN=a` and `CHOSEN=b` on either conclusive
    reading, and rejects `CHOSEN=rc1` and `READING=INCONCLUSIVE … CHOSEN=none`. The fake and its
    scratch directories were deleted after the run. The real sessions were **not** run.
  - **Commit** into the probe directory, stamped with the skills sha: `v0.out`, and the scratch's
    `payload.json`, `replay.txt`, `claude.version` and per-arm `*.replay.log` / `*.log`.
- **V-1r: the offline incident replay** (verification, not pytest; spec v1.1 §"Live
  verification", S-5). Run at 5g, against the worktree's gate:

  ```bash
  bash docs/03-analysis/probes/codex-tdd-gate-defects/v1-offline-replay.sh <worktree> /Users/kimhawk/orca/HemaSuite > v1r.out; test $? = 0 || exit 1
  grep -q '^V-1r: DONE VERDICT=PASS fails=0/6 ' v1r.out || exit 1
  ```

  It needs no `~/.agents` install, and it writes nothing to HemaSuite. The script itself scores
  every gate line; exit 0 and `VERDICT=PASS` require all of:
  - both direct controls as in the pre-merge reading (otherwise the script halts, exit 1);
  - `CHECK red-patch-allows`: rc 0 and an empty or `{}` stdout, an ALLOW for the incident's own
    payload;
  - `CHECK green-patch-denies-test-passing`: stdout carries `"deny"` and `test-passing`, the
    denying control;
  - `CHECK red-shell-pytest-allows` and `CHECK green-shell-pytest-allows`: the incident's
    `.venv/bin/python -m pytest` from the sub-project `cwd`, now admitted;
  - `CHECK red-shell-write-denies` and `CHECK green-shell-write-denies`: stdout carries `"deny"`.

  Any failed check gives `VERDICT=FAIL` and exit 2. An allow with no denying control is not a pass
  (spec §"Live verification").
- **5c state.** The feature record carries the base sha, the V-0 reading with its `CHOSEN=`, and
  its sha.

## Success Criteria

- Every AC of spec FR-1…FR-8 passes through each hook's real entry point: stdin JSON, and for the
  Claude gate also the positional argument. The AC-6.5 / AC-6.6 branch and the form are chosen by
  V-0's `CHOSEN=`.
  - Every test that runs the Claude gate, new or migrated, passes stdin explicitly. A payload test
    uses `input=<payload>`. A positional-argument test uses `stdin=subprocess.DEVNULL`.
  - Why: the gate now reads its target from stdin first and consults `$1` only when stdin yields
    no target (design D9). An inherited stdin makes the verdict depend on the runner's fd 0. A pipe
    held open with no data costs D9's 2.0 s bound. A payload on it would be decided instead of
    `$1`.
- **V-0 is conclusive** and **V-1r meets its pass condition**. Both are merge conditions (R1;
  spec v1.1 AC-6.7 and §"Live verification").
- The `run_suite` table above passes cell by cell, with one stub per row, including the
  summary-line row.
- The tests of `h_mad_wire_pin_gate`, `h_mad_assemble_tdd` **and `h_mad_wire_registry`** pass
  unmodified (P4), and `h_mad_wire_registry.py` has no diff against the base (spec v1.2 AC-2.9;
  D-A).
- The shell-policy differential is published and fully accounted ("Guard narrowing: shell
  policy").
- **Existing Claude-gate assertions migrate by form, exactly as spec v1.2 AC-6.2's list says**
  (D-B; spec v1.1 AC-6.6 names the same list). Located by function name
  (`bash --noprofile --norc`, `grep '^\s*assert' <module> | grep -c 'stderr\|stdout\|returncode'`
  → 8 of 8 assert lines in `test_h_mad_tdd_gate_codex.py`, and 8 of 9 in
  `test_h_mad_tdd_gate_state_resolution.py`, at `2f262f8a` and again at `dfd5f02e`;
  `grep -n 'returncode == 1'` over the two modules → 4 matching lines at `dfd5f02e`). The impl-plan
  lists each changed assertion under §"Regression provenance", with what it asserted before and
  what it reads after, for the form V-0 chose:
  - **Under (a)** (rc 2 on stderr): only the four `returncode == 1` assertions change, to rc 2 —
    in `test_blocks_claude_prod_write_when_codex_available`,
    `test_gate_finds_state_one_directory_down`, `test_repo_root_layout_still_works` and
    `test_a_production_file_under_a_test_named_directory_is_still_gated`. The stderr assertions
    and the `returncode == 0` assertions stand unchanged. No shared helper is added.
  - **Under (b)** (rc 0 with a stdout JSON deny): a refusal exits 0 with its reason on stdout, so
    every assertion that reads one channel alone stops discriminating or fails. The assertions
    move to one helper that returns (allow|deny, reason) from rc, stdout JSON and stderr together;
    the helper is a single definition shared by both modules.
    - `test_h_mad_tdd_gate_codex.py`: `test_blocks_claude_prod_write_when_codex_available` (rc 1
      plus `codex` and `dispatch` in stderr → deny, both words in the reason);
      `test_state_codex_status_exhausted_allows_fallback`, `test_env_override_allows_fallback` and
      `test_codex_absent_does_not_trigger_codex_gate` ("must be authored by codex" absent from
      stderr, vacuous under (b) → absent from the helper's reason);
      `test_test_file_allowed_even_with_codex_available` and `test_non_step5_ignores_codex_gate`
      (rc 0 → allow).
    - `test_h_mad_tdd_gate_state_resolution.py`: `test_gate_finds_state_one_directory_down`,
      `test_repo_root_layout_still_works` and
      `test_a_production_file_under_a_test_named_directory_is_still_gated` (rc 1, and the first
      also `H-MAD-TDD-GATE` in stderr → deny, with the prefix in the reason);
      `test_no_state_anywhere_still_allows`, `test_state_outside_the_project_is_not_adopted`,
      `test_real_test_files_are_still_exempt` and `test_test_directories_are_still_exempt`
      (rc 0 → allow).
  - **On either form**, both modules' `HOOK` constant moves to
    `Path(__file__).resolve().parents[1] / "hooks" / "h-mad-tdd-gate.sh"` (layer 6) and is listed
    under §"Regression provenance".
  - **On either form**, every existing call site that runs the Claude gate gains
    `stdin=subprocess.DEVNULL` (design D9; rule under the first bullet above). This is a
    non-assertion change: the argv, env and every assertion stand as they are. It is listed
    under §"Regression provenance" as a non-assertion change.
    - Census, at `b8662267`, of 3 call sites (unit: matching lines): the `_run` helper of
      `test_h_mad_tdd_gate_codex.py`, `test_non_step5_ignores_codex_gate` in the same module, and
      the `_run` helper of `test_h_mad_tdd_gate_state_resolution.py`. None passes `stdin=` or
      `input=` today. Command, in `bash --noprofile --norc`:

      ```bash
      grep -n 'subprocess.run(\[str(HOOK)' h-mad/tests/test_h_mad_tdd_gate_codex.py h-mad/tests/test_h_mad_tdd_gate_state_resolution.py
      # reading at b8662267: 3 matching lines in 2 files (2 in the codex module, 1 in state_resolution)
      grep -n 'stdin=\|input=' h-mad/tests/test_h_mad_tdd_gate_codex.py h-mad/tests/test_h_mad_tdd_gate_state_resolution.py
      # reading at b8662267: 0 matching lines
      ```

    - The two `_run` helpers are top-level statements, so the 5g top-level-statement diff lists
      them. The `test_*` function is listed too.
    - Residual: a call spelled other than `subprocess.run([str(HOOK)` is outside the grep. The
      other modules that name `h-mad-tdd-gate.sh` do not run the real gate. They are
      `test_h_mad_hook_wiring.py`, `test_h_mad_install_check.py` and
      `test_h_mad_install_check_docs.py`. The first names the gate only in settings fixtures for
      `h_mad_hook_wiring.py`. The second runs a `#!/bin/bash\nexit 0` stand-in. The third reads
      docs. The census re-runs at 5g, because a new test adds call sites.
  - Fact recorded, not a change: the three `test_h_mad_tdd_gate_state_resolution.py` rc-1 tests
    feed an **absolute** target under `codex_status=exhausted`, so today each is satisfied by the
    D1 "cannot derive test path" branch (P3 `D1`); after FR-6 each reaches the judge.
- **Node-id floor, and a module-level diff.**
  - At the worktree's base,
    `…/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts | grep '::' | sort > base.ids`.
    At 5g, the same into `head.ids`. `comm -23 base.ids head.ids` must be empty. The expected
    removed set is empty: every changed test above keeps its node id.
  - A node id cannot see an assertion weakened in place, and a `def test_*`-only diff cannot see
    one weakened through a helper, a fixture or a module constant. So at 5g the checker compares,
    by `ast.get_source_segment`, **every top-level statement** — each `def`, `class` and assignment,
    keyed by its name — of each pre-existing file among: the test files that
    `git diff --diff-filter=M --name-only <base> HEAD -- h-mad/tests handoff/tests handoff/scripts`
    names; every `conftest.py` on the path of a changed test file; and every module under those
    trees that a changed test file imports. A statement whose source differs, or that was
    removed, is listed. That set must equal the impl-plan's §"Regression provenance" list exactly
    (the `HOOK` constants included). The impl-plan ships the checker as a probe.
  - Measured at `dfd5f02e`: the two Claude-gate modules import only the standard library and
    `pathlib` (`grep -n '^from\|^import'` over both, then excluding `json`, `shutil`, `stat`,
    `subprocess`, `pathlib` and `__future__` → 0 matching lines), so for them the set is the two
    modules plus `h-mad/tests/conftest.py`. Re-derived at 5g, because a new import moves it.
- `ANCHORS_OK` with `drifted=0` over every committed mutation spec. Every FR-8 guard and every wire
  above is CAUGHT, scored on the pytest summary, with each alternation branch mutated alone. The
  `EXIT`-trap members are each mutated alone.
- `python3 h-mad/hooks/h-mad-codex-tdd-gate.py --self-check` → `CODEX-TDD-GATE: PASS`.
- **`reproduce.py`'s post-merge reading shows each of the five fail-open cases refused, in a form
  that differs from today's reading:**
  - Codex gate cases read `(0, 'deny', …)`.
  - Claude gate cases read `(0, 'deny', '')` under (b), or `(2, '', …)` under (a).
  - Today's `(0, '', '')` matches none of these.

## Out-of-Scope (confirmed from spec)

- Installing `~/.agents/skills/h-mad` (owned by `multi-host-runtime`; the live V-1 depends on it).
- Changing the name map's three prefixes.
- How the grok host treats `exit 1` (owned by `multi-host-runtime`).
- The Claude gate's no-state and file-type-exemption fail-opens. The no-`jq` fail-open is in
  scope and removed (spec v1.3 FR-6 "Removed", AC-6.12; DD-2).
- Venvs not named `.venv`, and `.venv/bin/pytest` as a shell entry point.

## Spec items (S-1…S-12)

The plan cites each where it is used. None is adopted beyond what the named spec revision says.

- **Settled in spec v1.1 (`96bf1cd1`):** S-1 (FR-0 arm EJ, nonce proof, per-form readings), S-2
  (AC-6.5 form), S-3 (AC-6.6: the single-form rule, no `exit 1`), S-4 (AC-6.7), S-5 (V-1r in
  §"Live verification"), S-6 (AC-3.4 doubled path).
- **Applied in spec v1.2:** S-7 (FR-4 audit-gate non-change), S-8 (the `state` verb, OD-8/OD-9,
  AC-6.8–AC-6.10), S-9 (rc never selects ALLOW; AC-1.3 stubs), S-11 (FR-7 names the three docs;
  AC-7.2), S-12 (AC-6.2 carries the form-conditional list).
- **Withdrawn:** S-10, by orchestrator decision D-A. Spec v1.2 states the two-parser residual in
  FR-2 and pins the registry in AC-2.9.
- **Spec v1.3 (`b20ef027`)** answered design audit cycle 1 with OD-A…OD-D and adopted DD-1…DD-5
  and DD-7…DD-9; this plan carries them (v1.3). Spec v1.4 was being written in parallel with plan
  v1.3, to take six design v1.1 sentences (FR-4 rule 2's whole-line `pytest-missing` match, the
  FR-4 category residual, FR-5's Codex-side unreadable refusal, FR-6's control-character target,
  FR-7's `Hook:` line, and the OQ-D1 split). Where this plan states one of those facts it uses the
  design's wording; the author report lists each.

## Open Questions

- **OQ-1 (operator).** Consider a governed project with no `.venv` whose hook `python3` lacks
  pytest; this repository is one today (P8). Every Claude-fallback production write there will be
  DENY `pytest-missing`, because the spec's "no venv → the judge's own interpreter" makes it so.
  Accept this (fail-closed, with the remedy in the deny reason), or amend the spec?
- **OQ-2 (spec).** The spec names no `SKILL.md`, `agy-runtime.md` or `codex-implementer-prompt.md`
  change. The invariant §"Skill manifest integrity" requires the gate's documented contract to
  follow its behaviour, and the stale-prose census finds sentences that go false. Answered by
  spec v1.2 (S-11).
- **OQ-3 (operator).** `run_suite` scores `2 passed, 1 error` as PASS today (P6): a collection
  error hidden by a green count. The spec keeps existing results, so this plan keeps it. Under the
  new rule `1 failed, 1 error` scores FAIL. Is the PASS row a defect to file separately?
- **OQ-4 (spec).** Closed by D-A: the registry is not edited, and spec v1.2 AC-2.9 names its
  tests.

## Next Steps

1. The operator answers OQ-1 and OQ-3.
2. The orchestrator runs step P0 and commits the probes and their readings. V-0 is run before the
   FR-6 form task, and an inconclusive V-0 halts to the operator.
3. Plan v1.2 is the final corrective revision after audit cycle 2 (the document-audit round cap).
   Plan v1.3 is a propagation revision from spec v1.3 and design v1.1, not an audit round.
4. The Phase 4 design names the judge file, the `state` verb's line format, the timeout value, the
   `EXIT`-trap shape and the blocking form.

## Version History
- v1.0: Initial plan draft (2026-09-28) from spec v1.0 at cf7e194f with OD-1..OD-7 accepted as recommended. Premises, the reproductions with controls, the OD-7 run_suite regression census, the stale-prose census and the coupled-suite baseline measured at 01121ca7. Step P0 embeds reproduce.py and v0-blocking-contract.sh with their sha256; OQ-1..OQ-4 raised.
- v1.1: Plan audit cycle 1 answered (2026-09-28; reports at be1ac452, codex p1 6 musts + 1 should, teammate 6 musts + 6 shoulds + 2 nits); premises re-run at 2f262f8a in bash --noprofile --norc. V-0 rewritten: arm EJ tests the JSON-deny form beside exit 2, per-arm nonce HIT lines replace the any-nonempty-log proof, CHOSEN= reading; exercised offline against a fake claude in 7 modes. INCONCLUSIVE V-0 now halts to the operator and blocks merge (R1). New V-1r probe replays the HemaSuite Task 7 incident offline from git objects 1fbf8022/31bfcfe4 (pre-merge: 6/6 gate lines deny, controls RED/GREEN) and is a merge condition. Claude gate governance and Codex-authorship key move to the judge's chain reader (state verb; OD-3c reproduced). EXIT-trap rule closes the set -euo pipefail implicit-exit class. _production_claims rewritten over _parse_tasks (wire-registry-grammar probe: 4 files, 16 lines, 64 lines). reproduce.py reports stdout permissionDecision (24 lines). Shell-policy guard-narrowing differential, Claude-gate assertion census by function name, function-body diff beside the node-id floor, anchor-occurrence rule, ANCHORS and R2 commands fixed. Spec-owed items S-1..S-12 cited as pending spec v1.1, not adopted.
- v1.2: Final corrective revision after plan audit cycle 2 (2026-09-28; codex p1 4 musts, v1.1 delta review 4 musts + 7 shoulds + 2 nits, both at dfd5f02e) under orchestrator decisions D-A..D-D. D-C: V-0 never chooses exit 1; CHOSEN is b when FORM_B=BLOCKS else a on either conclusive reading; rc1 removed from the script, run-gate grep, Choice, offline modes, reproduce post-merge row and census pass condition. V-0 also scores presence at the session's logged HIT paths and records EJ UNMEASURED as FORM_B=INCONCLUSIVE; exercised offline against a fake claude in 11 modes (v1.1 bytes read a false E1_BLOCKS in the other-directory mode). V-1r now scores all six gate lines (CHECK lines, VERDICT, exit 0/2/1); pre-merge reading VERDICT=FAIL fails=4/6 exit 2 at dfd5f02e, positive control PASS 0/6 and single-branch control FAIL 1/6 against a stub gate. v0 and v1r sha256 re-pinned; the P0 block executed as written into a scratch dir (rc 0). FR-4 summary-line rule with the stdout-2-passed/stderr-1-failed row. W6 uses two distinct hook/judge trees. Test HOOK constants resolve from Path(__file__) (worktree-via-HOME axis census, 6 lines / 4 files). D-A: _production_claims not edited, two-parser residual stated, W7 and S-10 withdrawn. D-B: existing assertions migrate form-conditionally. Function-body diff widened to every top-level statement plus conftest and imported helpers. S-1..S-6 cited as spec v1.1, S-7/8/9/11/12 as spec v1.2. R2 command moved to a fenced block; reproduce.py interpreter pinned.
- v1.3: Propagation revision (2026-09-28), not an audit round: carries what spec v1.3 and design v1.1 (both at b20ef027) say the plan owes. Layer 6 reordered to spec v1.3 FR-6 Order (fast path, empty target, exemptions, governance, Codex authorship, judge; DD-1/OD-A), with stdin-first target read and DD-7/DD-8/DD-9. No-jq allow removed from "What we deliberately do not touch" and Out-of-Scope (DD-2, AC-6.12). "Two explicit branches" replaced by the one run_suite predicate (DD-3); summary-line rule gains the SGR strip and open category axis (DD-4, OD-D); run_suite table gains four rows, today cells re-read at 34c0e962. Time bound is Popen+killpg (DD-10). Shell-policy differential gains the h_mad_state_write.py row and control, builder-derived python<X.Y>, widened softened set (OD-C/AC-3.6). R2 cites design D13; R2 census re-run at 34c0e962 -> 7. New section "Spec v1.3 ACs: where each is tested" (AC-3.6, AC-4.2, AC-4.7, AC-6.1, AC-6.9, AC-6.11..AC-6.15).
- v1.4: Propagation revision (2026-09-28), not an audit round, from design audit cycle 2's plan-G5 must (codex p1 at b8662267). G5 no longer sends both gates to the payload cwd. The Codex gate resolves against _payload_cwd_base (design D8), and the Claude gate against the project root (DD-7). Canonicalizing ('..' resolved before the exemptions) is stated as owed by design v1.2: design v1.1's D9 step 3 is string work only. Layer 6 step 0 swept. Success Criteria: every test that runs the Claude gate passes stdin explicitly (design D9's stdin-first read). The 3 existing call sites (census at b8662267) gain stdin=subprocess.DEVNULL and are listed under Regression provenance as a non-assertion change.
