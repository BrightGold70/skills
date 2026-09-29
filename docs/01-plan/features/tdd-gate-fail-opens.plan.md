# Plan: tdd-gate-fail-opens

## Executive Summary

Close the five reproduced TDD-gate fail-opens (D1–D5) by building the spec's single
target-normalisation rule **once**, in one stdlib-only Python function that both gates call. On
top of that function sit the `.py` fold, the governed refusal of unresolvable targets, the Codex
patch-header grammar, and the bounded judge reap with its new `judge-timeout` kind. The expected
outcome: every spelling of a governed production file gets the same decision from both gates, and
a committed probe re-derives each premise this plan depends on.

## Overview

The spec (`docs/01-plan/features/tdd-gate-fail-opens.spec.md` v1.2 at commit `e26466a8`; v1.0
and OD-1…OD-5 operator-approved at commit `662b1ce1`) fixes WHAT the gates must decide. This plan fixes the order of
work, the five decisions the spec left to the plan, the surfaces each change reaches, and the
measurements that must be re-taken as work proceeds. D1, D3 and D4 are one class: the gate decides
on the target's **spelling** rather than its **identity**. The plan therefore does not patch the
three instances. It adds one canonicaliser, and both gates must go through it. Two
implementations of "resolve first" (one in bash, one in Python) would reproduce D4's
cross-gate disagreement, so the plan does not allow them.

## Scope

In scope, and the only files this feature's code changes may touch:

- `h-mad/hooks/h-mad-tdd-gate.sh` (Claude Code gate): root and target canonicalisation, fold,
  unresolvable refusal, `judge-timeout` in `JUDGE_DENY_RE`.
- `h-mad/hooks/h-mad-codex-tdd-gate.py` (Codex gate): root, payload `cwd` and target
  canonicalisation, fold in `_is_production_python`, unresolvable refusal, header grammar in
  `_targets` (replacing `PATCH_TARGET`), `--self-check` additions.
- `h-mad/scripts/h_mad_tdd_judge.py`: `_run_bounded` reap bound, `KINDS`, the kind-priority tuple
  in `judge`, the `timed_out` handling in `resolve`. It also hosts, or imports, the shared
  canonicaliser (PD-1).
- One new stdlib-only module under `h-mad/scripts/` if the design places the canonicaliser outside
  the judge (PD-1 leaves the placement to the design).
- Tests under `h-mad/tests/`, mutation specs under `h-mad/tests/mutation-specs/`.
- Documentation surfaces that state the gate's rules (Deliverable D-8).
- The committed probe directory `docs/03-analysis/probes/tdd-gate-fail-opens/`.

User-visible behaviour: during `step5`, case-variant, symlinked, `..`-after-symlink and
padded-header spellings of a governed production `.py` are refused exactly like the canonical
spelling. Unresolvable targets under governing state are refused `judge-error`. A judge whose test
process cannot be reaped returns within `JUDGE_BUDGET_S + REAP_GRACE_S` and reports
`judge-timeout`.

## Goals

- G-1 (FR-1): both gates decide inside-root, directory exemptions, basename exemptions and the
  suffix test on the canonical root and target produced by one shared function.
- G-2 (FR-2): the `.py` suffix is ASCII-folded before production classification and before all
  three basename exemptions, in both gates.
- G-3 (FR-3): an unresolvable target is refused `judge-error` when governed, and allowed as today
  when not governed. Unresolvable has two arms: a dangling symlink, a loop, or a failed resolution
  at any prefix (arm 1); an existing root or target component the on-disk-spelling primitive cannot
  open or list (arm 2), which never falls back to its spelling.
- G-4 (FR-4): the Codex gate recognises `apply_patch` headers with Codex's own grammar: `\n` split,
  both-end `White_Space` trim, exact marker. It refuses a header path that still holds a control
  byte.
- G-5 (FR-5): `_run_bounded` waits for the reap for at most `REAP_GRACE_S`. A reap failure is DENY
  `judge-timeout` on both judge paths and in both gates.
- G-6 (FR-6): every gap-report repro is a pinned test, and a shared cross-gate differential proves
  equal decisions over the spec's domain.
- G-7 (FR-7): every new guard, and each branch of every new alternation, is mutation-tested and
  caught.
- G-8 (spec §"Measured premises"): the spec's scratch-measured table is re-derived by a committed
  probe, and one stamped reading of that probe replaces the table.

## Requirements

- FR-1: one target-normalisation rule in both gates (D3, D4; B2, OD-1). ACs 1.1–1.10.
- FR-2: `.py` suffix case-folded before every name test (D1; B3, OD-3). ACs 2.1–2.5.
- FR-3: unresolvable target refused `judge-error` when governed (B4, OD-4). ACs 3.1–3.6.
- FR-4: Codex gate reads patch headers as Codex does (D2; B6, OD-2). ACs 4.1–4.7.
- FR-5: judge bounds its post-kill reap and reports `judge-timeout` (D5; B5). ACs 5.1–5.5.
- FR-6: pinned repros and a cross-gate differential (B7, OD-5). ACs 6.1–6.3.
- FR-7: every guard bites. AC-7.1.
- The spec's NFRs: at most one added Python process in the Claude gate (FR-1 replaces the
  existing `# M:H11` call rather than adding one); no new knob or environment variable; every
  existing test green except the named deltas.

## Plan decisions (the five items the spec owed to the plan)

Each decision states what the tree showed and the command that showed it. Readings were taken at
`5e3a8238`. The gate, judge and mutation-spec files there are byte-identical to the spec's reading
sha `1a77e1c4`: `git diff --stat 1a77e1c4 5e3a8238 -- h-mad/hooks h-mad/scripts
h-mad/tests/mutation-specs` prints nothing.

### PD-1 — the on-disk-spelling primitive (spec owed item 2)

**Decision.** Canonicalisation is one Python function in one module under `h-mad/scripts/`. The
Codex gate calls it in-process: it already imports the judge through `_load_judge`. The Claude gate
calls it through the single `python3` invocation that today computes `TARGET_PATH` at `# M:H11`.
That invocation also replaces the bash builtin `pwd -P` that computes `ROOT_ABS`, so the bash side
performs **no** canonicalisation of its own. The primitive for an existing directory is
`fcntl(fd, F_GETPATH)` on a descriptor opened on that directory. The existing leaf's on-disk name is
taken per spec FR-1 step 4 (an inode match in the canonical parent's listing). The design owns the
choice between putting this function in `h_mad_tdd_judge.py` and putting it in a new module.

**Why F_GETPATH, not `chdir` + `getcwd`.** The Codex gate runs the canonicaliser in its own
process. `_project_root` reads `os.getcwd()` as its last fallback, and relative targets are joined
to a base. A `chdir` changes process-global state under both, and a failed restore leaves the gate
deciding from the wrong directory. `/bin/pwd -P` as a subprocess costs a process per call, and it
would give the bash side a second primitive, which is D4's class again.

**What the tree showed** (scratch probe, run and deleted; readings at `5e3a8238`, macOS 27.0 APFS):

| Reading | `/opt/anaconda3/bin/python` 3.11.8 | `/opt/homebrew/bin/python3` 3.14.7 | `/usr/bin/python3` 3.9.6 |
|---|---|---|---|
| `hasattr(fcntl, "F_GETPATH")` | True | True | True |
| `hasattr(os.path, "ALLOW_MISSING")` | **False** | True | **False** |
| F_GETPATH on dir `Case/sub` spelled `case/SUB` | `/Case/sub` | `/Case/sub` | not run |
| F_GETPATH on dir stored NFD `é`, spelled NFC | NFD (`0x65 0x301`) | NFD | not run |
| F_GETPATH on file `Case/sub/Prod.py` spelled `case/sub/prod.py` | `/Case/sub/Prod.py` | same | not run |
| `os.open` a mode-`0311` directory, `O_RDONLY` / `O_EVTONLY` | EACCES / EACCES | EACCES / EACCES | not run |
| `os.O_SEARCH` | absent | present, opens the `0311` directory | not run |
| F_GETPATH on a readable child of that `0311` directory | on-disk | on-disk | not run |

The first two rows came from `python -c 'import os,fcntl;print(hasattr(fcntl,"F_GETPATH"),
hasattr(os.path,"ALLOW_MISSING"))'` under each interpreter. The rest came from a scratch script
that built the fixture in a `tempfile.TemporaryDirectory` and was deleted after the run. T0's
committed probe re-derives every row.

**Consequences the design must carry.**

- The suite runs under `/opt/anaconda3/bin/python` 3.11.8. It is the interpreter named in the
  `command` of `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json` and
  `codex_gate_judge_wiring.json`, and `python3` on PATH (3.14.7) has no pytest:
  `python3 -m pytest --version` → "No module named pytest". The tests put a `python3` symlink to
  `sys.executable` on the gate's PATH, so the canonicaliser **must not** use
  `os.path.ALLOW_MISSING`. It implements the spec's component walk with `os.lstat`, `os.stat`,
  `os.path.lexists` and `os.path.exists`, all present on 3.9.6. `O_SEARCH` is not available as a
  fallback on 3.11.8.
- **Closed (OQ-P1, operator decision 2026-09-29: refuse; spec v1.1 FR-3 arm 2, AC-3.6).** An
  existing, resolvable root or target component on which the primitive's open (FR-1 step 3) or the
  listing of the leaf's canonical parent (FR-1 step 4) raises `OSError` is **unresolvable**: refused
  `judge-error` when governed, allowed when not. The canonicaliser never falls back to the spelling
  for that component, because the fallback would exempt on-disk `Tests/` at mode `0311` spelled
  `tests/…` (M-9's class). The canonicaliser's unresolvable result therefore has two causes: arm 1
  (does not resolve) and arm 2 (cannot be read in its on-disk spelling). Which operations the
  canonicaliser performs, and so which components arm 2 can fire on, and how the Claude gate
  receives the arm-2 condition, are the design's (§"Next Steps"). The spec's
  permission residual is now split three ways (cannot `lstat`: inert; can `lstat` but cannot open
  or list: FR-3 arm 2; a writer under another uid or with privileges the gate lacks: residual).
  Scratch reading of AC-3.6's **unfixed** observables, taken at `e26466a8` (the gate and judge
  files are unchanged since `5e3a8238`: `git diff --stat 5e3a8238 e26466a8 -- h-mad/hooks
  h-mad/scripts h-mad/tests/mutation-specs` prints nothing), under `/opt/anaconda3/bin/python`
  3.11.8 and `/opt/homebrew/bin/python3` 3.14.7 with identical results, spec fixture (`src/prod.py`,
  `codex_status: exhausted`), Claude `Write` payload and Codex `apply_patch` payload, script deleted
  after running: (a) on-disk `Tests/` at `0311`, `tests/newmod.py` — `step5`: both gates allow;
  (b) `src/` at `0311`, `src/prod.py` — `step5`: both deny `no-test-resolved`; (c) both cells under
  `step3`: both gates allow. `os.listdir` raised `PermissionError` in every cell (the precondition
  held). These equal the spec's expected unfixed column; T0's committed probe re-derives them and
  its reading supersedes this one.

### PD-2 — `REAP_GRACE_S` and `_run_bounded`'s return arity (spec owed item 3)

**Decision.** `REAP_GRACE_S = 1.0` (seconds), one named module constant in `h_mad_tdd_judge.py`.
`_run_bounded` returns a six-field `NamedTuple`: today's five fields in today's order plus
`reap_failed: bool`. Every unpacking site becomes a named delta.

**Why 1.0.** The spec's cap is ≤ 2.0 s. After `os.killpg(…, SIGKILL)`, every member of the child's
process group loses its pipe ends at once, so the grace only has to cover kernel teardown. The only
writer the grace cannot outwait is a process outside the group, and that is D5 itself. With 1.0 s,
AC-5.1's bound is `2.0 + 1.0 + 1.0 = 4.0 s` (the value spec v1.1 adopted into AC-5.1, with
`reap_failed=True` asserted), and a governed write's worst
case is `JUDGE_BUDGET_S` (40.0, read from the module: `python3 -c 'import sys;
sys.path.insert(0,"h-mad/scripts"); import h_mad_tdd_judge as j; print(j.JUDGE_BUDGET_S)'` →
`40.0`) + 1.0 s = 41.0 s + process start-up (spec FR-5 "Worst case"). The repository already has one bounded drain after `killpg`, in
`h-mad/scripts/h_mad_doc_block_exec.py` (the `proc.communicate(timeout=DRAIN_SECONDS)` block, which
closes `proc.stdout`/`proc.stderr` on `TimeoutExpired`). The design follows that shape. Its
`DRAIN_SECONDS = 5.0` exceeds the spec cap, so it is not reused.

**Why six fields and not an overloaded fifth.** Today the `error` field means "Popen raised", and
`judge` maps it to `no-summary` (the line tagged `# M:K3`). Encoding a reap failure there would give
one field two meanings. `timed_out` stays a plain `bool`, true for a reap failure as well, so
existing `timeout` reasoning is unchanged. `reap_failed` is the new discriminator.

**Unpacking sites, measured.** `git grep -n '_run_bounded' -- h-mad` at `5e3a8238` returns
5 matching lines in 2 files. Three are in `h_mad_tdd_judge.py`: the `def` and two production
unpackings (the name-map run in `resolve` and the pytest run in `judge`). Two are in
`h-mad/tests/test_h_mad_tdd_judge.py`: the `def` line of `test_run_bounded_kills_the_process_group`,
whose name contains the substring, and that test's **one** unpacking. So there are three unpacking
sites in all, one of them in a test. Re-run at `e26466a8`: the same 5 matching lines in 2 files.
Spec v1.1's AC-5.2 now says the same: only `test_run_bounded_kills_the_process_group` unpacks
(five names today; its move to the six-field result is the named, reviewed delta), and
`test_name_map_runs_under_the_budget` calls `judge.judge`, does not unpack, and keeps its
assertions (`timeout`, `< 6.0 s`) unchanged. A plain timeout with no detached descendant reports
`timed_out=True`, `reap_failed=False` (AC-5.2). No mutation spec anchors on a
`_run_bounded` line. The only judge anchor on an affected line is `# M:K3`
(`tdd_judge_scoring.json`, 2 mutations), whose `find` text contains `timed_out`. See the anchor
rule in §"Implementation Strategy".

### PD-3 — AC-1.10 on a case-sensitive runner (spec owed item 4)

**Decision.** No case-sensitive or Linux runner is known to this repository, and this plan adds
none. Measured at `5e3a8238`:
`git ls-files | grep -c -E '(^|/)\.github/workflows/|(^|/)\.gitlab-ci\.yml$|(^|/)\.circleci/|(^|/)Jenkinsfile$|azure-pipelines'`
→ `0` files. `git grep -n -E 'skipif|pytest\.skip|platform'` over the eight TDD-gate test modules
plus `tdd_gate_support.py` → 0 matching lines. AC-1.10 therefore means the following. Each
case-dependent test checks its precondition on the fixture's own directory (create `a`, assert
`os.path.exists("A")`), not on `/`, because the fixture directory is the only volume the assertion
is about. When the precondition does not hold, the test **fails** with a message naming it. It never
skips. If a case-sensitive runner is ever added, these tests fail by design. Adding that runner then
requires a spec amendment choosing between a case-insensitive disk image for the fixtures and an
explicit deselection. A skip is never an option, because a skip is the silent pass that AC-1.10
forbids. The Linux `F_GETPATH` fallback (spec residual) has no test here for the same reason.

### PD-4 — the committed probe re-deriving M-1…M-23 (spec owed item 1)

**Decision.** Task T0 commits `docs/03-analysis/probes/tdd-gate-fail-opens/reproduce.py`, taking
the skills root as its argument and building every fixture in a `TemporaryDirectory`. It prints one
`REPRO:` line per cell of spec §"Measured premises" (M-1…M-23), per PD-1 primitive row, per Codex
trim-set code point, and for the D5 reading. A cell that needs `codex` prints an explicit
`REPRO: M-n SKIP codex-absent` when `codex` is not on PATH, never nothing. T0 runs it on the
unfixed tree and commits the output as a reading named after the short sha it measured, following
the convention of `docs/03-analysis/probes/codex-tdd-gate-defects/reproduce.reading.ab83ae92.txt`.
T9 runs it again on the fixed tree. The spec's measured table is replaced by a pointer to that one
reading. **That replacement is a spec edit, owed by the spec author, not this plan.** This plan
cites no M-cell value of its own beyond the spot-check under §"Verified premises".

### PD-5 — Claude Code Edit / MultiEdit / NotebookEdit on a leaf symlink (spec owed item 5)

**Decision: closed as measured; FR-1's leaf rule stands.** The orchestrator measured it live on
Claude Code 2.1.284 (2026-09-29), with a leaf symlink `src/link.py -> ../tests/t.py` in a scratch
fixture: **Edit** on `src/link.py` is refused by the tool itself ("Refusing to write …: it is a
symbolic link. Write to the link's target path instead"), and the link and `tests/t.py` are
unchanged. Write was already measured refusing (spec §"Measured premises"). **MultiEdit** and
**NotebookEdit** are absent from that build's tool set, so they are **unmeasurable** there, not
measured. No observed tool replaces the link, so spec v1.1 leaves FR-1's "decide a leaf symlink by
its referent" unamended. These are harness-tool actions: `reproduce.py` cannot re-derive them, so
they enter T0's reading **only as manual rows** carrying the build (2.1.284) and the date. The
residual is the spec's: a later build's MultiEdit or NotebookEdit, or any writer that replaces a
leaf symlink, is measured before it is trusted.

## Verified premises (commands run at `5e3a8238`)

Each premise below was re-run for this plan. Premises the spec measured and this plan did not
re-run are T0's to re-derive.

| Premise | Command | Result |
|---|---|---|
| Six spec cells still reproduce on the unfixed tree | scratch script driving both gates with the spec's fixture (step5, `codex_status: exhausted`); run under 3.14.7, then deleted | M-1 both deny `no-test-resolved`; M-2 both ALLOW; M-4 Claude ALLOW, Codex deny `no-test-resolved`; M-9 both ALLOW; M-17 Codex ALLOW; M-15 (trailing space) Codex ALLOW — each equal to the spec's table |
| `KINDS` has 11 members today (12 after FR-5) | `python3 -c 'import sys;sys.path.insert(0,"h-mad/scripts");import h_mad_tdd_judge as j;print(len(j.KINDS))'` | `11` |
| `JUDGE_DENY_RE` alternates 10 kinds (every `KINDS` member but `red-measured`) | `grep '^JUDGE_DENY_RE=' h-mad/hooks/h-mad-tdd-gate.sh \| python3 -c 'import sys,re;print(len(re.search(r"kind=\(([^)]*)\)",sys.stdin.read()).group(1).split("\|")))'` | `10` |
| Named test and helper symbols exist | `git grep -n -F` of each name over `h-mad/tests` | `test_run_bounded_kills_the_process_group`, `test_name_map_runs_under_the_budget`, `test_timeout_kind` (`test_h_mad_tdd_judge.py`); `test_claude_gate_kind`, `test_dd7_differential_matches_the_published_cells` (`test_h_mad_tdd_gate_judge.py`); `test_codex_gate_kind` (`test_h_mad_codex_tdd_gate_judge.py`); `def decision` and `def hermetic_env` (`tdd_gate_support.py`) — each found once as a `def` |
| `test_dd7_differential_matches_the_published_cells` asserts 126 cells and 18 denies | read its final assertion | `assert len(observed) == 126 and observed.count("deny") == 18` |
| Suite collection floor | `/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests \| tail -1` on a clean tree | `4618 tests collected` |
| Mutation anchors baseline | `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json` | `ANCHORS_OK specs=118 mutations=1195 ok=1195 drifted=0` |

**The suite floor drifts by construction.** It moved from 4611 (a `git archive 662b1ce1 h-mad`
export) to 4618 at `5e3a8238`, one commit later, through an unrelated documentation test. Phase 5
re-measures it with the same command at the feature branch's base commit, immediately before the
first task, and the post-feature gate is "collected ≥ that floor + the tests this feature adds, and
0 failed". The anchor baseline drifts the same way with every committed spec and is re-measured at
the same moment.

## Implementation Strategy

Test-first per task (Phase 5d RED, 5e GREEN), in this order. Each task's ACs are the spec's. The
task list is the impl-plan's to refine; the order and the dependencies are this plan's.

| Task | Content | ACs | Depends on |
|---|---|---|---|
| T0 | Probe `reproduce.py` + unfixed reading (PD-4). Includes the OQ-P1 cells, each under the `step5` and the `step3`-only state: a mode-`0311` directory spelled in another case with an absent leaf (on-disk `Tests/`, `tests/newmod.py`), and an existing leaf whose parent lacks `r` (`src/` at `0311`, `src/prod.py`); each cell prints its `os.listdir` precondition. These cells are the measurement of AC-3.6's unfixed observables (a), (b) and (c). Plus the PD-5 manual rows (Write and Edit refused on Claude Code 2.1.284; MultiEdit and NotebookEdit absent from that build), entered by hand, not printed by the script | — (measurement) | — |
| T1 | Shared canonicaliser: component walk, F_GETPATH on existing directories, leaf inode match with the all-entries rule for hard links in one directory, remainder append + lexical collapse, unresolvable predicate over both FR-3 arms. **Arm-2 guard:** an `OSError` from the primitive's open of an existing component (FR-1 step 3) or from the listing of the leaf's canonical parent (FR-1 step 4) makes the result unresolvable, with no fallback to the spelling. Unit tests drive it directly, including the arm-2 guard on the `0311` fixture. | 1.7, 1.8 (unit half), 1.9 (unit half), 1.10, 3.4 | T0 |
| T2 | Codex gate: root, payload `cwd` (before `_payload_cwd_base` tests containment) and every target through T1; fold in `_is_production_python`; FR-3 refusal (both arms) gated on `_any_phase5_status` ∈ {`active`, `unknown`} | 1.1–1.6, 1.8, 1.9, 2.1–2.4, 3.1–3.6 (Codex halves) | T1 |
| T3 | Claude gate: one Python call returns canonical root, canonical target and the unresolvable condition (both FR-3 arms; the call contract is the design's), replacing `ROOT_ABS`'s `pwd -P` and the `# M:H11` call; every exemption, `IN_ROOT` and the suffix test read the canonical values; fold in the basename `case` and the `*.py` test; FR-3 refusal after `_read_state` reports `active`/`unreadable`, with `_chain_may_hold_state` and `TDD-STATE: none` unchanged | 1.1–1.9, 2.1–2.4, 3.1–3.6 (Claude halves) | T1 |
| T4 | Codex header grammar: `\n` split, both-end trim with `str.isspace()` minus U+001C–U+001F, exact markers, control-byte and empty-path refusal when governed; `--self-check` gains the trailing-space and indented cases | 2.5, 4.1–4.7 | T2 |
| T5 | Judge: `REAP_GRACE_S = 1.0`, six-field `NamedTuple` return adding `reap_failed: bool` (AC-5.1 bound 4.0 s; AC-5.2's only unpacking delta is `test_run_bounded_kills_the_process_group`), reap failure → `judge-timeout` on the name-map path and the pytest path, `judge-timeout` first in the priority tuple and stopping further runs, `KINDS` + `JUDGE_DENY_RE`, new rows in `test_claude_gate_kind` and `test_codex_gate_kind` | 5.1–5.5 | — (independent of T1–T4) |
| T6 | Cross-gate differential over the OD-5 domain, reusing `tdd_gate_support.decision` and `hermetic_env`, with an expectation table whose deny count the test derives; re-run `dd7_differential.py` (AC-6.3) | 6.1–6.3 | T2, T3 |
| T7 | Documentation surfaces (D-8) | — (doc-derived tests stay green) | T2–T5 |
| T8 | Mutation specs for every guard AC-7.1 names, one mutation per alternation branch, each alone. Spec v1.2's AC-7.1 names **19 guard rows** (18 at spec v1.0; the added row is FR-3's cannot-be-read arm, AC-3.6, whose mutation lives on T1's arm-2 guard). Counted as the AC-7.1 paragraph's `(AC-` parentheticals plus its `separate mutations` phrases: `git show e26466a8:docs/01-plan/features/tdd-gate-fail-opens.spec.md \| awk '/AC-7\.1:/{f=1} f&&/^$/{exit} f' \| tr '\n' ' ' \| tr -s ' '`, then `grep -o '(AC-' \| wc -l` → 16 and `grep -o 'separate mutations' \| wc -l` → 3; the same at `662b1ce1` → 15 and 3. 19 is a **floor** on mutations, not their count: a row naming a guard in each gate ("the fold in each gate") needs one mutation per gate, and the committed specs are the census | 7.1 | T1–T6 |
| T9 | Re-run `reproduce.py` on the fixed tree; commit the reading | — (measurement) | T1–T8 |

**Rules over the whole feature** (each closes a class, not an instance):

- **One canonicaliser.** No gate computes a path identity any other way. After T3, a
  `grep -n 'pwd -P'` over `h-mad/hooks/h-mad-tdd-gate.sh` may match only the `# M:H8` walk inside
  `_chain_may_hold_state`. That walk runs on the already-canonical target, where a builtin `pwd -P`
  is the identity. The design must either confirm this or route that walk through T1 too.
  `os.path.realpath` and `Path.resolve` stay in the judge only where FR-1 step 8 makes them
  identities.
- **Mutation anchors follow the edit.** A task that rewrites a line carrying an `# M:` marker
  re-derives the affected mutation spec entries at the **same guard**, never deletes them.
  `--check-anchors` over `h-mad/tests/mutation-specs/*.json` must report `ANCHORS_OK drifted=0`
  after every task. **Candidate** markers (on lines that T2, T3 and T5 may rewrite), with the number of
  **mutations** whose `find` text carries each marker (counted at `5e3a8238` by loading each spec's
  `mutations` list and testing `"M:" + marker in m["find"]`): `claude_gate_judge_wiring.json` —
  H6 1, H8 1, H11 1, H15 2, H18 2, H19 1, H20 2, W2 2; `codex_gate_judge_wiring.json` — G1 2, G5 1,
  G7 1, W1 2; `tdd_judge_scoring.json` — K3 2. (A `git grep -c -F 'M:H15'` over the directory
  reports twice these numbers because each of these mutations also carries its marker in
  `replace`; lines are not mutations.) The candidate set is a forecast, not a census: the design
  names the exact lines, and `--check-anchors` after each task is the census.
- **Verdict changes are named, never discovered.** The only verdict changes toward ALLOW are the
  spec's three: M-10 (both gates), M-11 (Claude gate), and a leaf symlink into `tests/` (Claude
  gate). Any other existing test that changes verdict is a stop-and-report, not a test edit.
- **Every refusal the feature adds is fail-closed on exception.** The Codex gate's
  `except Exception` (`# M:G2`) already maps a raise to `kind=judge-error`. On the Claude side the
  new Python call must print a line the gate parses, or the gate refuses `judge-error`. It never
  falls back to the raw spelling.

## Architecture Considerations

- **Single source, two callers.** Both gates reach the canonicaliser through code paths they
  already have: the Codex gate's `_load_judge` import and the Claude gate's `# M:H11` Python call.
  A hook installed as a symlink finds the scripts directory through `os.path.realpath` of its own
  path (`# M:W6` in `_find_judge`). A copied hook uses the same mechanism, and the placement must
  keep both working. `test_h_mad_tdd_gate_judge.py` already links the hook at one site, and the
  design must name the test covering the copied case.
- **The judge becomes a pass-through for identity.** FR-1 step 8 hands the judge canonical
  `--root` and `--target`. Its own `os.path.realpath` calls in `resolve` and `main` then change
  nothing. They stay, because the Codex gate calls `judge.judge` in-process and must see the same
  values.
- **Governance scope differs by gate and stays that way.** The Claude gate's "governed" is the
  chain verdict of the `state` verb; the Codex gate's is `_any_phase5_status` over
  `root.rglob("docs/.bkit-memory.json")`. FR-3 and FR-4 inherit each gate's existing notion. The
  differential's domain (OD-5) is chosen so this difference does not show there.
- **Header over-recognition is fail-closed by design** (spec FR-4). A trimmed hunk line that reads
  as a header adds a governed target. It never removes one.
- **Timing.** T5's RED run of AC-5.1 waits about 12 s on the unfixed runner (spec D5 reading), and
  the fixed run is bounded at 4.0 s (PD-2). The existing `< 6.0 s` assertions in
  `test_run_bounded_kills_the_process_group`, `test_name_map_runs_under_the_budget` and
  `test_timeout_kind` keep their bound. A process-group kill with no detached descendant must still
  report plain `timeout` (AC-5.2).

## Deliverables

| Id | Deliverable | Type | Satisfies |
|---|---|---|---|
| D-1 | Shared canonicaliser function (module placement: design) | module | FR-1, FR-3 |
| D-2 | Codex gate: canonical root, `cwd` and targets; fold; unresolvable refusal | hook | FR-1, FR-2, FR-3 |
| D-3 | Claude gate: canonical root and target via one Python call; fold; unresolvable refusal; `judge-timeout` branch | hook | FR-1, FR-2, FR-3, FR-5 |
| D-4 | Codex header grammar + `--self-check` cases | hook | FR-4 |
| D-5 | Judge: `REAP_GRACE_S`, six-field runner result, `judge-timeout` kind and priority | module | FR-5 |
| D-6 | Pinned repro tests + cross-gate differential test module | tests | FR-6, all ACs |
| D-7 | Mutation specs for AC-7.1's guard list, plus re-derived anchors for touched markers | mutation specs | FR-7 |
| D-8 | Documentation: `h-mad/references/codex-implementer-prompt.md` "Hook:" bullets (resolved identity, any-case `.py`), `h-mad/SKILL.md` helper-scripts bullet for `h_mad_tdd_judge.py` (`judge-timeout`), `h-mad/references/codex-runtime.md` §"Trust boundary" (`judge-timeout`, unresolvable refusal). The design confirms whether `h-mad/references/agy-runtime.md` §"The TDD gate" needs a change: it states no kind list at `5e3a8238`. | docs | FR-2, FR-3, FR-5 |
| D-9 | `docs/03-analysis/probes/tdd-gate-fail-opens/reproduce.py` + unfixed reading (T0) + fixed reading (T9) | probe | G-8, PD-4, PD-5 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| An existing directory the primitive cannot open or list (OQ-P1) falls back to its spelling | A fail-open of M-9's class under a mode-`0311` directory | Closed by the operator (refuse): spec FR-3 arm 2 and AC-3.6; T1's arm-2 guard has no spelling fallback and its own AC-7.1 mutation; T0's probe carries the OQ-P1 cells |
| A Claude Code tool replaces a leaf symlink (PD-5) | FR-1's referent rule allows a production write through a link into `tests/` | Measured on 2.1.284: Write and Edit refuse, MultiEdit and NotebookEdit absent; a tool in a later build is measured before it is trusted (spec residual) |
| The canonicaliser uses an API absent on the suite's 3.11.8 (`ALLOW_MISSING`, `O_SEARCH`) | Green under PATH `python3` 3.14.7, red or wrong under the suite | PD-1 names the constraint; T1's unit tests run under the suite interpreter |
| Rewriting marked lines drifts mutation anchors silently | A guard's mutation no longer applies, or relocates and reports SURVIVED | `--check-anchors` `ANCHORS_OK drifted=0` after every task; re-derive at the same guard |
| Canonicalisation flips an existing pinned verdict beyond the spec's three | Silent softening of a pinned cell | Stop-and-report rule; T6 re-runs `dd7_differential.py` and `test_dd7_differential_matches_the_published_cells` stays at 126/18 |
| The Codex trim set is re-measured against a later codex-cli | AC-4.6's code-point cases pin a stale grammar | T0 records the codex-cli version in its reading; a version change re-runs the trim-set section (spec Assumptions) |
| The reap grace is too short on a loaded machine | A plain timeout is misreported as `judge-timeout` | Both kinds DENY, so the write is refused either way; AC-5.2's no-descendant case pins `timeout` |
| AC-5.1 and AC-5.3 leave a detached `sleep` running | Leaked processes across the suite | Teardown kills the sleeper via its pidfile (spec AC-5.1), with the pattern `_pid_gone` already used in `test_h_mad_tdd_judge.py` |

## Convention Prerequisites

- Phase 3 audit exit and Phase 4 design approval per `h-mad/SKILL.md`. OQ-P1 and PD-5 are
  settled (operator 2026-09-29; folded into spec v1.1 and v1.2, committed together at `e26466a8`), so
  the design may freeze FR-1 and FR-3.
- Feature branch cut from `main` after this plan's approval. The suite floor and anchor baseline
  (§"Verified premises") are re-measured at that branch base with the same commands.
- Phase 5 authorship by Codex (the gate under repair is the gate that governs its own Phase 5).
  The judge and both gates are live while they are edited. Each GREEN step must leave both gates
  deciding, and `python3 h-mad/hooks/h-mad-codex-tdd-gate.py --self-check` must print
  `CODEX-TDD-GATE: PASS` at every commit.
- The suite interpreter is `/opt/anaconda3/bin/python` (pytest 9.1.1). The full `h-mad/tests`
  suite runs per task, not only the scoped modules.
- The scratch probes behind this plan were deleted after running. T0's probe is the committed
  instrument.

## Success Criteria

- Every AC in spec FR-1…FR-7 passes as an automated test on the fixed tree. The "unfixed" halves
  (AC-1.7's `realpath` substitution, AC-3.4, AC-4.7, AC-5.4, AC-6.1, AC-6.2) are **run** on the
  unfixed code or with the named substitution, not asserted.
- Full suite: collected ≥ the floor re-measured at the branch base + the tests this feature adds,
  and `0 failed`, under `/opt/anaconda3/bin/python`.
- `--check-anchors` over all committed mutation specs: `ANCHORS_OK drifted=0`. Every new spec from
  D-7 runs to `MUTATION: ALL_CAUGHT` with `survived=0`, scored on the pytest summary.
- `CODEX-TDD-GATE: PASS` from `--self-check`. `test_dd7_differential_matches_the_published_cells`
  keeps 126 cells and 18 denies. `dd7_differential.py` either reproduces its published cells or
  each changed cell is a stated delta (AC-6.3).
- T9's fixed reading shows the spec's "fixed" column for every M-cell. The spec's measured table is
  replaced by a pointer to that reading (spec author).

## Out-of-Scope (confirmed from spec)

- The shell-command policy and the Codex `workdir` question (gap report §"Unverified").
- The empty-target rule under a governed sub-project (gap report §"Unverified").
- The name map (`h_mad_derive_test_path.sh`) and impl-plan test resolution.
- Hard links across directories, and a legitimate `*.PY` data file (spec residuals, stated, not
  fixed).
- Host hook timeouts (predecessor OQ-D1). FR-5 bounds the judge, not the host.
- A Linux or case-sensitive runner (PD-3).

## Next Steps

1. Operator review of v1.1 (OQ-P1 decided refuse, PD-5 measured, OD-1…OD-5 approved).
2. Phase 3 audit cycle on two surfaces per `h-mad/SKILL.md`.
3. Phase 4 design: canonicaliser placement (PD-1), the exact lines each task rewrites (which fixes
   the anchor set), and the Claude gate's call contract for the canonical root, target and
   unresolvable flag. Owed to the design by spec v1.1's FR-3 arm 2:
   - **Which operations the canonicaliser performs**, named exactly. Arm 2 fires only on an
     operation the canonicaliser actually performs, so a component the design's primitive never
     opens is never tested (for example, F_GETPATH on the deepest existing directory covers its
     ancestors without opening them). The design states, per component kind (root, intermediate
     directory, leaf's parent, leaf), whether it is opened, listed, or neither.
   - **How the Claude gate receives the arm-2 condition**, alongside the existing unresolvable
     flag from the same single Python call: one flag carrying both arms or a separate arm-2 value,
     and the reason text naming the component either way (AC-3.6 requires the reason to name it).

## Version History
- v1.0: Initial plan draft (2026-09-29) from spec v1.0 (662b1ce1). PD-1 F_GETPATH primitive in one shared canonicaliser, bash side does no canonicalisation; PD-2 REAP_GRACE_S=1.0 and a six-field runner result; PD-3 no case-sensitive runner exists, AC-1.10 fails never skips; PD-4 committed probe T0/T9; PD-5 leaf-symlink tools need a live measurement. Opens OQ-P1 (an existing directory the primitive cannot open). Readings at 5e3a8238.
- v1.1: Revision (2026-09-29) against spec v1.2 (e26466a8). OQ-P1 closed (operator: refuse; spec FR-3 arm 2, AC-3.6): G-3 and FR-3 carry both arms, T1 gains the arm-2 guard with no spelling fallback, AC-3.6 owned by T2/T3 (gate halves), scratch reading of AC-3.6's unfixed observables at e26466a8 equals the spec's expected column. PD-5 closed as measured (Edit refused on Claude Code 2.1.284; MultiEdit/NotebookEdit absent, unmeasurable); T0 enters it as manual rows only. T0 gains the OQ-P1 cells under both states. T8 states AC-7.1's 19 guard rows (18 at spec v1.0) with the counting command, as a floor on mutations. FR-5 aligned to spec: REAP_GRACE_S = 1.0, six-field NamedTuple with reap_failed, AC-5.1 < 4.0 s, AC-5.2 unpacking only in test_run_bounded_kills_the_process_group. Next Steps owe the design the canonicaliser's operations and the Claude gate's arm-2 transport.
