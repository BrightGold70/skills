# Plan: tdd-gate-fail-opens

## Executive Summary

Close the five reproduced TDD-gate fail-opens (D1–D5) by building the spec's single
target-normalisation rule **once**, in one stdlib-only Python function that both gates call. On
top of that function sit the `.py` fold, the governed refusal of unresolvable targets, the Codex
patch-header grammar, and the bounded judge reap with its new `judge-timeout` kind. The expected
outcome: every spelling of a governed production file gets the same decision from both gates, and
a committed probe re-derives each premise about the two gates and the judge. The two premises that
are behaviour of an agent's own tools (Codex's `apply_patch` grammar, Claude Code's Edit tool on a
leaf symlink) are manual, dated readings with their exact command (§"Reproduction commands"),
because no committed script may invoke an agent CLI (PD-4).

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
  suffix test on the canonical root and target produced by one shared function. The Claude gate's
  outside-root directory exemption (`# M:H20`) keeps its second conjunct on the **raw** spelling
  (spec FR-1 step 7): an outside-root target is exempt only when the canonical target **and** the
  raw spelling both match. That exemption is the one place a raw spelling still takes part in a
  decision, and it can only narrow an ALLOW.
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
  equal decisions, and equal kinds on every cell where both gates deny, over the spec's domain.
- G-7 (FR-7): every new guard, and each branch of every new alternation, is mutation-tested and
  caught.
- G-8 (spec §"Measured premises"): the spec's scratch-measured table is re-derived by a committed
  probe. T0's **unfixed** reading, one stamped reading of that probe, replaces the table, as the
  spec's own text requires. T9's **fixed** reading is a separate artifact, cited on its own and
  never substituted for T0's (PD-4). The columns the probe cannot derive (Codex's writes, Codex's
  trim set, Claude Code's tools) are manual rows in T0's reading.

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
`5e3a8238` (v1.0, v1.1) and re-run at `983c2f85` (v1.2) wherever a stamp below says so. The gate,
judge and mutation-spec files at both shas are byte-identical to the spec's reading sha
`1a77e1c4`: `git diff --stat 1a77e1c4 983c2f85 -- h-mad/hooks h-mad/scripts
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

**What the tree showed** (command R-1 in §"Reproduction commands", run once under each
interpreter; reading at `983c2f85`, macOS 27.0 APFS, 2026-09-29):

| Reading | `/opt/anaconda3/bin/python` 3.11.8 | `/opt/homebrew/bin/python3` 3.14.7 | `/usr/bin/python3` 3.9.6 |
|---|---|---|---|
| `hasattr(fcntl, "F_GETPATH")` | True | True | True |
| `hasattr(os.path, "ALLOW_MISSING")` | **False** | True | **False** |
| F_GETPATH on dir `Case/sub` spelled `case/SUB` | `/Case/sub` | `/Case/sub` | `/Case/sub` |
| F_GETPATH on dir stored NFD `é`, spelled NFC | NFD (`0x65 0x301`) | NFD | NFD |
| F_GETPATH on file `Case/sub/Prod.py` spelled `case/sub/prod.py` | `/Case/sub/Prod.py` | same | same |
| `os.open` a mode-`0311` directory, `O_RDONLY` / `O_EVTONLY` (`0x8000`) | errno 13 / errno 13 | errno 13 / errno 13 | errno 13 / errno 13 |
| `os.O_SEARCH` | absent | present, opens the `0311` directory (`/Tests`) | present, opens it (`/Tests`) |
| F_GETPATH on a readable child of that `0311` directory | on-disk `/Tests/prod.py` | same | same |
| `os.listdir` on that `0311` directory | errno 13 | errno 13 | errno 13 |

The 3.9.6 column was "not run" at plan v1.1 and was measured for v1.2 by the same command; its
`O_SEARCH` is present, unlike 3.11.8's. That changes nothing below, because the constraint is set
by the suite interpreter (3.11.8). T0's committed probe re-derives every row.

**Consequences the design must carry.**

- The suite runs under `/opt/anaconda3/bin/python` 3.11.8. It is the interpreter named in the
  `command` of `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json` and
  `codex_gate_judge_wiring.json`, and `python3` on PATH (3.14.7) has no pytest:
  `python3 -m pytest --version` → "No module named pytest" (at `983c2f85`; run it outside any
  command-rewriting shell hook — under this session's `rtk` hook the same line printed `pytest
  9.1.1`, because the hook rewrote it, and `rtk proxy python3 -m pytest --version` restored the
  true reading; `/opt/homebrew/bin/python3 -c 'import pytest'` → `ModuleNotFoundError` is the
  hook-proof form). The interpreter named by each spec: `python3 -c 'import json;[print(json.load(open(f"h-mad/tests/mutation-specs/{n}.json"))["command"][0]) for n in
  ("claude_gate_judge_wiring","codex_gate_judge_wiring")]'` → `/opt/anaconda3/bin/python` twice.
  The tests put a `python3` symlink to
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
  Reading of AC-3.6's **unfixed** observables by command R-2 (§"Reproduction commands"), at
  `983c2f85` (the gate, judge and test files are unchanged since `5e3a8238`: `git diff --stat
  5e3a8238 983c2f85 -- h-mad/hooks h-mad/scripts h-mad/tests` prints nothing), under
  `/opt/anaconda3/bin/python` 3.11.8 and `/opt/homebrew/bin/python3` 3.14.7 with byte-identical
  output, spec fixture (`src/prod.py`, `codex_status: exhausted`), a `Write` payload to each gate:
  (a) on-disk `Tests/` at `0311`, `tests/newmod.py` — `step5`: both gates allow; (b) `src/` at
  `0311`, `src/prod.py` — `step5`: both deny `no-test-resolved`; (c) both cells under `step3`: both
  gates allow. R-2 prints `listdir EACCES` for every cell (the precondition held). These equal the
  spec's expected unfixed column; T0's committed probe re-derives them and its reading supersedes
  this one.

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
`DRAIN_SECONDS = 5.0` exceeds the spec cap, so it is not reused (`grep -n -E
'^DRAIN_SECONDS|communicate\(timeout=DRAIN_SECONDS' h-mad/scripts/h_mad_doc_block_exec.py` → 2
matching lines, the constant `5.0` and its one `communicate` use; at `983c2f85`).

**Why six fields and not an overloaded fifth.** Today the `error` field means "Popen raised", and
`judge` maps it to `no-summary` (the line tagged `# M:K3`; `grep -n -F '# M:K3'
h-mad/scripts/h_mad_tdd_judge.py` → 1 matching line, `kind = "no-summary" if error else score(out
+ "\n" + err, timed_out)`, at `983c2f85`). Encoding a reap failure there would give
one field two meanings. `timed_out` stays a plain `bool`, true for a reap failure as well, so
existing `timeout` reasoning is unchanged. `reap_failed` is the new discriminator.

**Unpacking sites, measured.** `git grep -n '_run_bounded' -- h-mad` at `5e3a8238` returns
5 matching lines in 2 files. Three are in `h_mad_tdd_judge.py`: the `def` and two production
unpackings (the name-map run in `resolve` and the pytest run in `judge`). Two are in
`h-mad/tests/test_h_mad_tdd_judge.py`: the `def` line of `test_run_bounded_kills_the_process_group`,
whose name contains the substring, and that test's **one** unpacking. So there are three unpacking
sites in all, one of them in a test. Re-run at `983c2f85`: the same 5 matching lines in 2 files
(`git grep -n '_run_bounded' -- h-mad | awk -F: '{print $1}' | sort | uniq -c` → 3 in the judge,
2 in `test_h_mad_tdd_judge.py`).
Spec v1.1's AC-5.2 now says the same: only `test_run_bounded_kills_the_process_group` unpacks
(five names today; its move to the six-field result is the named, reviewed delta), and
`test_name_map_runs_under_the_budget` calls `judge.judge`, does not unpack, and keeps its
assertions (`timeout`, `< 6.0 s`) unchanged. A plain timeout with no detached descendant reports
`timed_out=True`, `reap_failed=False` (AC-5.2). No mutation spec anchors on a
`_run_bounded` line (`git grep -l -F '_run_bounded' -- h-mad/tests/mutation-specs | wc -l` → 0
files at `983c2f85`). The only judge anchor on an affected line is `# M:K3`
(`tdd_judge_scoring.json`, 2 mutations), whose `find` text contains `timed_out`. See the anchor
rule in §"Implementation Strategy".

### PD-3 — AC-1.10 on a case-sensitive runner (spec owed item 4)

**Decision.** No case-sensitive or Linux runner is known to this repository, and this plan adds
none. Measured at `5e3a8238`:
`git ls-files | grep -c -E '(^|/)\.github/workflows/|(^|/)\.gitlab-ci\.yml$|(^|/)\.circleci/|(^|/)Jenkinsfile$|azure-pipelines'`
→ `0` files. The eight TDD-gate test modules plus `tdd_gate_support.py` are the pathspec
`'h-mad/tests/test_h_mad_tdd_gate*.py' 'h-mad/tests/test_h_mad_tdd_judge.py'
'h-mad/tests/test_h_mad_codex_tdd_gate*.py' 'h-mad/tests/tdd_gate_support.py'` (`git ls-files`
over it → 9 files); `git grep -n -E 'skipif|pytest\.skip|platform' --` that pathspec → 0 matching
lines. Both re-run at `983c2f85` with the same results. AC-1.10 therefore means the following. Each
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
`REPRO:` line per gate cell of spec §"Measured premises" (M-1…M-23: each cell's **gate** columns),
per PD-1 primitive row, per OQ-P1 cell, and for the D5 reading. It exercises only the two gates and
the judge.

**No agent CLI, in any committed artifact of this feature (the class, not the instance).**
`h-mad/invariants.base.md` §"Dispatched agent CLIs are not script dependencies" forbids a script
or test invoking `codex`, `agy` or `grok` for its own work. The rule over the axis: `reproduce.py`,
every test this feature adds, and every mutation spec's `command` reach **no** agent CLI, directly
or through a gate they spawn. Mechanism, not intent: every subprocess the probe and the new tests
spawn gets a constructed `PATH` of a private `bin/` (symlinks to `sys.executable` as `python3`,
`dirname`, `basename`, `jq`) followed by `/usr/bin:/bin`, the shape `_bin` in
`h-mad/tests/test_h_mad_tdd_gate_judge.py` already uses; where a gate's `codex` lookup must
succeed, the tests' existing stub (`_bin(…, codex=True)`, `exit 0`) stands in. The probe prints
`REPRO: agent-cli-reachable=<yes|no>` from `command -v codex agy grok` under that `PATH`, and its
reading is valid only with `no` (at `983c2f85`, `PATH=/usr/bin:/bin command -v codex` exits 1).
The spec's columns that are behaviour of an agent's **own** tools are therefore **manual, dated
readings**, entered in T0's reading by hand with their exact command, the same way PD-5's Claude
Edit reading is:

- the "Codex writes" column of M-15…M-23, Codex's trim set (spec AC-4.6's code points), and Codex
  `apply_patch` following a leaf symlink: command R-4 (§"Reproduction commands") on the codex-cli
  whose `codex --version` is recorded beside the row (0.158.0 at this plan);
- Claude Code Write and Edit on a leaf symlink: command R-5 (PD-5), build and date recorded.

The residual, exactly: the gate side of AC-4.6 is pinned by tests against the grammar **as
measured on codex-cli 0.158.0**. A later codex-cli that trims differently is detected only when
someone re-takes R-4 by hand on the new binary; nothing committed re-runs it. `hmad-dispatch.sh`
has no verb that runs `apply_patch` as a bare tool (`grep -c apply_patch
h-mad/scripts/hmad-dispatch.sh` → 0 matching lines at `983c2f85`; its generic `run` verb is a
time bound, not an agent dispatch, and this plan does not use it as one), so no dispatch route
exists today either; if one is added, R-4 may move behind it. The Claude gate's own pre-existing `command -v codex` in its
authorship rule is product behaviour at run time, not a script's dependency, and is outside this
class; under the constructed `PATH` it finds nothing.

T0 runs `reproduce.py` on the unfixed tree and commits the output, plus the manual rows, as a
reading named after the short sha it measured, following the convention of
`docs/03-analysis/probes/codex-tdd-gate-defects/reproduce.reading.ab83ae92.txt`. T9 runs it again
on the fixed tree and commits a **second, separate** reading.

**Which reading the spec points at.** Spec §"Measured premises" says its table "stays until T0
commits its unfixed reading, and is then replaced by a pointer to that one reading". The pointer
therefore names **T0's unfixed reading**, which is the table's own re-derivation (the "today"
columns). T9's fixed reading is cited separately (this plan's §"Success Criteria", the Phase 6
analysis) as the evidence for each "fixed" observable; it never replaces the table. **The
replacement is a spec edit, owed by the spec author, not this plan.** This plan cites no M-cell
value of its own beyond the spot-check under §"Verified premises".

### PD-5 — Claude Code Edit / MultiEdit / NotebookEdit on a leaf symlink (spec owed item 5)

**Decision: closed as measured; FR-1's leaf rule stands.** The orchestrator measured it live on
Claude Code 2.1.284 (2026-09-29) by command R-5 (§"Reproduction commands"), with the fixture
`mkdir -p pd5/src pd5/tests; printf 'X = 1\n' > pd5/tests/t.py; ln -sf ../tests/t.py
pd5/src/link.py`, then the Claude Code Edit tool on `pd5/src/link.py` replacing `X = 1` with
`X = 2`: it is refused with "Refusing to write …: it is a symbolic link. Write to the link's
target path instead"; afterwards `ls -l pd5/src/link.py` still shows the link and `cat
pd5/tests/t.py` still reads `X = 1`. Write was already measured refusing (spec §"Measured premises"). **MultiEdit** and
**NotebookEdit** are absent from that build's tool set, so they are **unmeasurable** there, not
measured. No observed tool replaces the link, so spec v1.1 leaves FR-1's "decide a leaf symlink by
its referent" unamended. These are harness-tool actions: `reproduce.py` cannot re-derive them, so
they enter T0's reading **only as manual rows** carrying the build (2.1.284) and the date. The
residual is the spec's: a later build's MultiEdit or NotebookEdit, or any writer that replaces a
leaf symlink, is measured before it is trusted.

## Verified premises (commands run at `983c2f85`)

Each premise below was re-run for this plan, from the skills root, at `983c2f85`; the h-mad code
and tests are unchanged since v1.1's reading sha `5e3a8238` (`git diff --stat 5e3a8238 983c2f85 --
h-mad/hooks h-mad/scripts h-mad/tests` prints nothing), and every result below equals v1.1's.
Premises the spec measured and this plan did not re-run are T0's to re-derive.

| Premise | Command | Result |
|---|---|---|
| Six spec cells still reproduce on the unfixed tree | R-2 (§"Reproduction commands"), under `/opt/anaconda3/bin/python` 3.11.8 and `/opt/homebrew/bin/python3` 3.14.7, byte-identical output | M-1 both deny `no-test-resolved`; M-2 both allow; M-4 Claude allow, Codex deny `no-test-resolved`; M-9 both allow; M-17 Codex allow; M-15 (trailing space) Codex allow, and its control (no space) Codex deny `no-test-resolved` — each equal to the spec's table |
| Outside-root `# M:H20` cells on the unfixed Claude gate (M1) | R-3, under `/opt/anaconda3/bin/python` 3.11.8 | `out/lnk/x.py` with `lnk -> tests` (canonical enters `tests/`, raw does not): deny `no-test-resolved`; `out/tests/x.py` (both match): allow; `out/src/x.py` (control): deny `no-test-resolved` |
| `KINDS` has 11 members today (12 after FR-5) | `python3 -c 'import sys;sys.path.insert(0,"h-mad/scripts");import h_mad_tdd_judge as j;print(len(j.KINDS))'` | `11` |
| `JUDGE_DENY_RE` alternates 10 kinds (every `KINDS` member but `red-measured`) | `grep '^JUDGE_DENY_RE=' h-mad/hooks/h-mad-tdd-gate.sh \| python3 -c 'import sys,re;print(len(re.search(r"kind=\(([^)]*)\)",sys.stdin.read()).group(1).split("\|")))'` | `10` |
| Named test and helper symbols exist | `for s in 'def test_run_bounded_kills_the_process_group' 'def test_name_map_runs_under_the_budget' 'def test_timeout_kind' 'def test_claude_gate_kind' 'def test_dd7_differential_matches_the_published_cells' 'def test_codex_gate_kind' 'def decision' 'def hermetic_env'; do printf '%s: ' "$s"; git grep -l -F "$s" -- h-mad/tests \| tr '\n' ' '; echo; done` | the first three in `test_h_mad_tdd_judge.py`; `test_claude_gate_kind` and `test_dd7_…` in `test_h_mad_tdd_gate_judge.py`; `test_codex_gate_kind` in `test_h_mad_codex_tdd_gate_judge.py`; `def decision` in `tdd_gate_support.py` only; `def hermetic_env` in **two** files, `tdd_gate_support.py` (the `**extra` helper T6 reuses) and `conftest.py` (a fixture of the same name, not the one reused). v1.1 said "each found once"; that was false for `hermetic_env` |
| `test_dd7_differential_matches_the_published_cells` asserts 126 cells and 18 denies | `grep -n -F 'assert len(observed) == 126 and observed.count("deny") == 18' h-mad/tests/test_h_mad_tdd_gate_judge.py` | 1 matching line |
| Suite collection floor | `/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests \| tail -1` on a clean tree | `4618 tests collected` |
| Mutation anchors baseline | `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json` | `ANCHORS: ANCHORS_OK specs=118 mutations=1195 ok=1195 drifted=0 unreadable=0 skipped=0 unclassifiable=0` |

**The suite floor drifts by construction.** It moved from 4611 (a `git archive 662b1ce1 h-mad`
export) to 4618 at `5e3a8238`, one commit later, through an unrelated documentation test, and
read 4618 again at `983c2f85` (the commits between touch only this feature's documents). Phase 5
re-measures it with the same command at the feature branch's base commit, immediately before the
first task, and the post-feature gate is "collected ≥ that floor + the tests this feature adds, and
0 failed". The anchor baseline drifts the same way with every committed spec and is re-measured at
the same moment.

## Implementation Strategy

Test-first per task (Phase 5d RED, 5e GREEN), in this order. Each task's ACs are the spec's. The
task list is the impl-plan's to refine; the order and the dependencies are this plan's.

| Task | Content | ACs | Depends on |
|---|---|---|---|
| T0 | Probe `reproduce.py` + unfixed reading (PD-4). Includes the OQ-P1 cells, each under the `step5` and the `step3`-only state: a mode-`0311` directory spelled in another case with an absent leaf (on-disk `Tests/`, `tests/newmod.py`), and an existing leaf whose parent lacks `r` (`src/` at `0311`, `src/prod.py`); each cell prints its `os.listdir` precondition. These cells are the measurement of AC-3.6's unfixed observables (a), (b) and (c). Plus the outside-root `# M:H20` cells of R-3. The probe invokes no agent CLI and prints `REPRO: agent-cli-reachable=no` (PD-4). Manual rows, entered by hand with their command, never printed by the script: the Codex-writes column of M-15…M-23, the Codex trim set and Codex following a leaf symlink (R-4, with `codex --version`), and PD-5 (R-5: Write and Edit refused on Claude Code 2.1.284; MultiEdit and NotebookEdit absent from that build) | — (measurement) | — |
| T1 | Shared canonicaliser: component walk, F_GETPATH on existing directories, leaf inode match with the all-entries rule for hard links in one directory, remainder append + lexical collapse, unresolvable predicate over both FR-3 arms. **Arm-2 guard:** an `OSError` from the primitive's open of an existing component (FR-1 step 3) or from the listing of the leaf's canonical parent (FR-1 step 4) makes the result unresolvable, with no fallback to the spelling. Unit tests drive it directly, including the arm-2 guard on the `0311` fixture. | 1.7, 1.8 (unit half), 1.9 (unit half), 1.10, 3.4 | T0 |
| T2 | Codex gate: root, payload `cwd` (before `_payload_cwd_base` tests containment) and every target through T1; fold in `_is_production_python`; FR-3 refusal (both arms) gated on `_any_phase5_status` ∈ {`active`, `unknown`} | 1.1–1.6, 1.8, 1.9, 2.1–2.4, 3.1–3.6 (Codex halves) | T1 |
| T3 | Claude gate: one Python call returns canonical root, canonical target and the unresolvable condition (both FR-3 arms; the call contract is the design's), replacing `ROOT_ABS`'s `pwd -P` and the `# M:H11` call; `IN_ROOT`, the in-root directory exemption (`# M:H19`), the basename exemptions and the suffix test read the canonical values; the outside-root directory exemption (`# M:H20`) keeps its dual check per spec FR-1 step 7 — `_dir_match` of the canonical target **and** `_dir_match` of the raw spelling `RAW_TARGET` — so the canonical value replaces only its first conjunct. **Pinned outside-root symlink control** (R-3's first cell): a target outside the root, `out/lnk/x.py` with `out/lnk -> tests`, whose canonical form enters `tests/` but whose raw spelling does not, stays deny `no-test-resolved` on the fixed gate; with its positive control `out/tests/x.py` (allow) and negative control `out/src/x.py` (deny). This pin is what the existing mutation `H20B` (canonical conjunct only) must turn red after T3 re-derives it; fold in the basename `case` and the `*.py` test; FR-3 refusal after `_read_state` reports `active`/`unreadable`, with `_chain_may_hold_state` and `TDD-STATE: none` unchanged | 1.1–1.9, 2.1–2.4, 3.1–3.6 (Claude halves) | T1 |
| T4 | Codex header grammar: `\n` split, both-end trim with `str.isspace()` minus U+001C–U+001F, exact markers, control-byte and empty-path refusal when governed; `--self-check` gains the trailing-space and indented cases. AC-4.6's code points are the ones the manual R-4 reading measured on codex-cli 0.158.0; the tests drive only the gate, never `codex` (PD-4) | 2.5, 4.1–4.7 | T2 |
| T5 | Judge: `REAP_GRACE_S = 1.0`, six-field `NamedTuple` return adding `reap_failed: bool` (AC-5.1 bound 4.0 s; AC-5.2's only unpacking delta is `test_run_bounded_kills_the_process_group`), reap failure → `judge-timeout` on the name-map path and the pytest path, `judge-timeout` first in the priority tuple and stopping further runs, `KINDS` + `JUDGE_DENY_RE`, new rows in `test_claude_gate_kind` and `test_codex_gate_kind` | 5.1–5.5 | — (independent of T1–T4) |
| T6 | Cross-gate differential over the OD-5 domain, reusing `tdd_gate_support.decision` and `tdd_gate_support.hermetic_env`. It asserts, per spec FR-6: (1) the two gates' decisions are equal on every cell; (2) on every cell where both deny, their **kinds** are equal (Codex kind parsed with `kind=([a-z-]+)` from the reason); (3) each cell's decision, and its kind when it denies, equals that cell's row in a **published expectation table** in the test, one row per cell and state mode carrying the expected decision and the expected kind; (4) the table's deny count is derived by the test from the table, never typed. Each assertion is its own failure message, so a cross-gate kind disagreement fails on its own and is not masked by an equal decision. Re-run `dd7_differential.py` (AC-6.3) | 6.1–6.3 | T2, T3 |
| T7 | Documentation surfaces (D-8) | — (doc-derived tests stay green) | T2–T5 |
| T8 | Mutation specs for every guard AC-7.1 names, one mutation per alternation branch, each alone. The mutation **floor is 20** at spec v1.2 (19 at spec v1.0): the AC-7.1 paragraph's `(AC-` parentheticals, plus one for each `separate mutations` pair, plus one for each guard named `in each gate` (one mutation per gate, AC-2.2). Command: `P=$(git show e26466a8:docs/01-plan/features/tdd-gate-fail-opens.spec.md \| awk '/AC-7\.1:/{f=1} f&&/^$/{exit} f' \| tr '\n' ' ' \| tr -s ' ')`, then `echo "$P" \| grep -o '(AC-' \| wc -l` → 16 occurrences, `echo "$P" \| grep -o 'separate mutations' \| wc -l` → 3, `echo "$P" \| grep -o 'in each gate' \| wc -l` → 1; 16 + 3 + 1 = 20. The same at `662b1ce1` → 15, 3 and 1 = 19; the added row is FR-3's cannot-be-read arm, AC-3.6, whose mutation lives on T1's arm-2 guard. Re-run at `983c2f85` (spec unchanged since `e26466a8`): 16, 3, 1. 20 is a **floor**, not the count: the acceptance check is the per-guard census over the committed specs — every guard AC-7.1 names, and every gate a guard is named in, has at least one mutation reported caught | 7.1 | T1–T6 |
| T9 | Re-run `reproduce.py` on the fixed tree; commit the reading | — (measurement) | T1–T8 |

**Rules over the whole feature** (each closes a class, not an instance):

- **One canonicaliser.** No gate computes a path identity any other way. Today `grep -n 'pwd -P'
  h-mad/hooks/h-mad-tdd-gate.sh` → 2 matching lines at `983c2f85`: the `ROOT_ABS=` assignment and
  the walk inside `_chain_may_hold_state`. After T3 it may match only the `# M:H8` walk inside
  `_chain_may_hold_state`. That walk runs on the already-canonical target, where a builtin `pwd -P`
  is the identity. The design must either confirm this or route that walk through T1 too.
  `os.path.realpath` and `Path.resolve` stay in the judge only where FR-1 step 8 makes them
  identities.
- **Mutation anchors follow the edit.** A task that rewrites a line carrying an `# M:` marker
  re-derives the affected mutation spec entries at the **same guard**, never deletes them.
  `--check-anchors` over `h-mad/tests/mutation-specs/*.json` must report `ANCHORS_OK drifted=0`
  after every task. **Candidate** markers (on lines that T2, T3 and T5 may rewrite), with the number of
  **mutations** whose `find` text carries each marker, measured at `983c2f85` (unchanged from
  `5e3a8238`) with, per spec and marker, `python3 -c 'import json;print(sum("M:H15" in m["find"]
  for m in json.load(open("h-mad/tests/mutation-specs/claude_gate_judge_wiring.json"))["mutations"]))'`
  (substitute the marker and the spec file): `claude_gate_judge_wiring.json` —
  H6 1, H8 1, H11 1, H15 2, H18 2, H19 1, H20 2, W2 2; `codex_gate_judge_wiring.json` — G1 2, G5 1,
  G7 1, W1 2; `tdd_judge_scoring.json` — K3 2. (A `git grep -c -F 'M:H15'` over the directory
  reports twice these numbers because each of these mutations also carries its marker in
  `replace`; lines are not mutations.) The candidate set is a forecast, not a census: the design
  names the exact lines, and `--check-anchors` after each task is the census.
- **Verdict changes are named, never discovered.** The only verdict changes toward ALLOW are the
  spec's three: M-10 (both gates), M-11 (Claude gate), and a leaf symlink into `tests/` (Claude
  gate). Any other existing test that changes verdict is a stop-and-report, not a test edit. The
  axis along which a fourth ALLOW could slip in unnamed is an exemption whose input changes from
  the spelling to the canonical value; the only such exemption outside the root is `# M:H20`, and
  it keeps its raw-spelling conjunct (T3), pinned by R-3's outside-root symlink control. Inside
  the root, a verdict change beyond the three is the stop-and-report above; the spec, not this
  plan, decides that the in-root exemptions read only canonical values (FR-1 step 6).
- **Every refusal the feature adds is fail-closed on exception.** The Codex gate's
  `except Exception` (`# M:G2`) already maps a raise to `kind=judge-error`. On the Claude side the
  new Python call must print a line the gate parses, or the gate refuses `judge-error`. It never
  falls back to the raw spelling. (`# M:H20`'s raw conjunct is not a fallback: it is an added
  condition on an ALLOW, read alongside the canonical value, never instead of it.)

## Architecture Considerations

- **Single source, two callers.** Both gates reach the canonicaliser through code paths they
  already have: the Codex gate's `_load_judge` import and the Claude gate's `# M:H11` Python call.
  A hook installed as a symlink finds the scripts directory through `os.path.realpath` of its own
  path (`# M:W6` in `_find_judge`). A copied hook uses the same mechanism, and the placement must
  keep both working. `test_h_mad_tdd_gate_judge.py` already links the hook at one site (`grep -c -F
  'link.symlink_to(hook)' h-mad/tests/test_h_mad_tdd_gate_judge.py` → 1 matching line at
  `983c2f85`), and the
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
| D-8 | Documentation: `h-mad/references/codex-implementer-prompt.md` "Hook:" bullets (resolved identity, any-case `.py`), `h-mad/SKILL.md` helper-scripts bullet for `h_mad_tdd_judge.py` (`judge-timeout`), `h-mad/references/codex-runtime.md` §"Trust boundary" (`judge-timeout`, unresolvable refusal). The design confirms whether `h-mad/references/agy-runtime.md` §"The TDD gate" needs a change: it names no judge kind (`grep -c -E "$(python3 -c 'import sys;sys.path.insert(0,"h-mad/scripts");import h_mad_tdd_judge as j;print("\|".join(sorted(j.KINDS)))')" h-mad/references/agy-runtime.md` → 0 matching lines over the whole file, at `983c2f85`). | docs | FR-2, FR-3, FR-5 |
| D-9 | `docs/03-analysis/probes/tdd-gate-fail-opens/reproduce.py` (gates and judge only, no agent CLI) + unfixed reading with the manual R-4 and R-5 rows (T0) + fixed reading (T9), two separate files | probe | G-8, PD-4, PD-5 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| An existing directory the primitive cannot open or list (OQ-P1) falls back to its spelling | A fail-open of M-9's class under a mode-`0311` directory | Closed by the operator (refuse): spec FR-3 arm 2 and AC-3.6; T1's arm-2 guard has no spelling fallback and its own AC-7.1 mutation; T0's probe carries the OQ-P1 cells |
| A Claude Code tool replaces a leaf symlink (PD-5) | FR-1's referent rule allows a production write through a link into `tests/` | Measured on 2.1.284: Write and Edit refuse, MultiEdit and NotebookEdit absent; a tool in a later build is measured before it is trusted (spec residual) |
| The canonicaliser uses an API absent on the suite's 3.11.8 (`ALLOW_MISSING`, `O_SEARCH`) | Green under PATH `python3` 3.14.7, red or wrong under the suite | PD-1 names the constraint; T1's unit tests run under the suite interpreter |
| Rewriting marked lines drifts mutation anchors silently | A guard's mutation no longer applies, or relocates and reports SURVIVED | `--check-anchors` `ANCHORS_OK drifted=0` after every task; re-derive at the same guard |
| Canonicalisation flips an existing pinned verdict beyond the spec's three | Silent softening of a pinned cell | Stop-and-report rule; T6 re-runs `dd7_differential.py` and `test_dd7_differential_matches_the_published_cells` stays at 126/18 |
| The Codex trim set is re-measured against a later codex-cli | AC-4.6's code-point cases pin a stale grammar | T0's manual R-4 rows record `codex --version` beside each row; a version change is caught only when R-4 is re-taken by hand on the new binary, because no committed artifact may invoke `codex` (PD-4 residual; spec Assumptions owes the matching wording) |
| Canonicalising the Claude gate's outside-root exemption drops its raw-spelling conjunct (`# M:H20`) | An outside-root target whose canonical form enters `tests/` becomes a fourth, unnamed ALLOW | T3 keeps the dual check (spec FR-1 step 7); R-3's outside-root symlink control is a pinned test, and the re-derived `H20B` mutation must turn it red |
| The committed probe or a new test reaches an agent CLI | Breaks `invariants.base.md` §"Dispatched agent CLIs are not script dependencies"; a probe reading then depends on an installed agent | Constructed `PATH` for every spawned process; `REPRO: agent-cli-reachable=no` gates the reading's validity (PD-4) |
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
- Every reading this plan cites carries its command inline or as R-1…R-5 in §"Reproduction
  commands", runnable from the skills root. T0's probe is the committed instrument that
  supersedes them for every gate and judge row; R-4 and R-5 stay manual by construction (PD-4).

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
- T0's unfixed reading reproduces the spec's "today" columns for every gate cell, and the spec's
  measured table is replaced by a pointer to **that** unfixed reading, as spec §"Measured
  premises" requires (spec author). T9's fixed reading, a separate file, shows the spec's "fixed"
  observable for every M-cell and is cited on its own; it does not replace the table.
- The pinned outside-root symlink control (R-3's first cell) stays deny `no-test-resolved` on the
  fixed Claude gate.

## Out-of-Scope (confirmed from spec)

- The shell-command policy and the Codex `workdir` question (gap report §"Unverified").
- The empty-target rule under a governed sub-project (gap report §"Unverified").
- The name map (`h_mad_derive_test_path.sh`) and impl-plan test resolution.
- Hard links across directories, and a legitimate `*.PY` data file (spec residuals, stated, not
  fixed).
- Host hook timeouts (predecessor OQ-D1). FR-5 bounds the judge, not the host.
- A Linux or case-sensitive runner (PD-3).

## Next Steps

1. Operator review of v1.2 (plan audit cycle 1 answered; OQ-P1 decided refuse, PD-5 measured,
   OD-1…OD-5 approved).
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
4. Owed by the spec author (this plan does not edit the spec): (a) spec §"Assumptions" says a
   later Codex "is caught by AC-4.6 only if the owed probe re-runs against the new binary", and
   spec §"Measured premises" says the committed probe's reading replaces the whole table; under
   PD-4 the probe never invokes `codex`, so the Codex-writes column and the trim set are
   re-derived only by the manual R-4 reading, and the pointer must name T0's reading **with its
   manual rows**; (b) the outside-root symlink control of R-3 has no AC of its own in spec FR-1;
   T3 pins it, and the spec may name it.

## Reproduction commands

Each command runs from the skills root. R-1…R-3 were run for v1.2 at `983c2f85` on 2026-09-29,
macOS 27.0 APFS, and their outputs are the readings cited above; they build every fixture in a
`TemporaryDirectory`, drive only the two gates (through the existing `tdd_gate_support` helpers),
and give every spawned gate a constructed `PATH` with no agent CLI. R-4 and R-5 are **manual**:
they exercise an agent's own tool, so no committed artifact runs them (PD-4).

**R-1 — the on-disk-spelling primitive (PD-1 table).** Run once per interpreter:
`/opt/anaconda3/bin/python`, `/opt/homebrew/bin/python3`, `/usr/bin/python3`.

```bash
/opt/anaconda3/bin/python - <<'EOF'
import os, fcntl, sys, tempfile, unicodedata as u
def gp(p, fl=os.O_RDONLY):
    fd = os.open(p, fl)
    try: return fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024)).rstrip(b"\0").decode()[len(t):]
    finally: os.close(fd)
def tryopen(p, fl):
    try: return gp(p, fl)
    except OSError as e: return f"errno {e.errno}"
with tempfile.TemporaryDirectory() as t0:
    t = os.path.realpath(t0)
    os.makedirs(t + "/Case/sub"); open(t + "/Case/sub/Prod.py", "w").close()
    os.mkdir(t + "/" + u.normalize("NFD", "é"))
    os.mkdir(t + "/Tests"); open(t + "/Tests/prod.py", "w").close(); os.chmod(t + "/Tests", 0o311)
    print(sys.version.split()[0], "F_GETPATH", hasattr(fcntl, "F_GETPATH"), "ALLOW_MISSING", hasattr(os.path, "ALLOW_MISSING"))
    print("dir case/SUB ->", gp(t + "/case/SUB"))
    print("dir NFC e ->", [hex(ord(c)) for c in gp(t + "/" + u.normalize("NFC", "é"))[1:]])
    print("file case/sub/prod.py ->", gp(t + "/case/sub/prod.py"))
    print("0311 O_RDONLY", tryopen(t + "/tests", os.O_RDONLY), "O_EVTONLY", tryopen(t + "/tests", 0x8000))
    print("O_SEARCH", tryopen(t + "/tests", os.O_SEARCH) if hasattr(os, "O_SEARCH") else "absent")
    print("child of 0311 ->", gp(t + "/tests/prod.py"))
    try: os.listdir(t + "/tests"); print("listdir ok")
    except OSError as e: print("listdir errno", e.errno)
    os.chmod(t + "/Tests", 0o755)
EOF
```

**R-2 — spec gate cells and AC-3.6's unfixed observables (§"Verified premises", PD-1).** Run
under `/opt/anaconda3/bin/python` and `/opt/homebrew/bin/python3`; the two outputs are
byte-identical at `983c2f85`.

```bash
/opt/anaconda3/bin/python - . <<'EOF'
import json, os, re, shutil, subprocess, sys, tempfile
H = os.path.abspath(sys.argv[1]) + "/h-mad"; sys.path.insert(0, H + "/tests")
from tdd_gate_support import decision, hermetic_env, hook_form, write_state
from pathlib import Path
def claude(r, b, target):
    env = {"PATH": f"{b}:/usr/bin:/bin", "HOME": str(Path.home()), "CLAUDE_PROJECT_DIR": r}
    p = subprocess.run([H + "/hooks/h-mad-tdd-gate.sh"], input=json.dumps({"tool_name": "Write", "tool_input": {"file_path": target}}), capture_output=True, text=True, cwd=r, env=env)
    o = decision(p, hook_form(Path(H + "/hooks/h-mad-tdd-gate.sh"))); return o.decision + (" " + o.kind if o.kind else "")
def codex(r, ti):  # both gates get the constructed PATH: no agent CLI is reachable
    p = subprocess.run([sys.executable, H + "/hooks/h-mad-codex-tdd-gate.py"], input=json.dumps(dict(cwd=r, **ti)), capture_output=True, text=True, cwd=r, env=hermetic_env(CODEX_PROJECT_DIR=r, PATH=f"{r}/.bin:/usr/bin:/bin"))
    if p.returncode or p.stdout.strip() in ("", "{}"): return "allow" if not p.returncode else f"invalid rc={p.returncode}"
    why = json.loads(p.stdout)["hookSpecificOutput"]["permissionDecisionReason"]; m = re.search(r"kind=([a-z-]+)", why)
    return "deny " + (m.group(1) if m else why[:40])
def fixture(t, phase):
    r = os.path.realpath(t); os.makedirs(r + "/src"); open(r + "/src/prod.py", "w").write("X = 1\n")
    subprocess.run(["git", "init", "-q", r]); write_state(Path(r), {"feat": {"phase": phase, "codex_status": "exhausted"}})
    b = r + "/.bin"; os.mkdir(b)
    for n, s in (("python3", sys.executable), ("dirname", "/usr/bin/dirname"), ("basename", "/usr/bin/basename"), ("jq", shutil.which("jq"))): os.symlink(s, f"{b}/{n}")
    return r, b
W = lambda p: {"tool_name": "Write", "tool_input": {"file_path": p}}
AP = lambda P: {"tool_name": "apply_patch", "tool_input": {"command": P}}
with tempfile.TemporaryDirectory() as t:
    r, b = fixture(t, "step5")
    for cell, rel in (("M-1", "src/prod.py"), ("M-2", "src/prod.PY")):
        print(cell, "claude:", claude(r, b, f"{r}/{rel}"), "| codex:", codex(r, W(f"{r}/{rel}")))
    os.symlink("src", r + "/tests"); print("M-4 claude:", claude(r, b, f"{r}/tests/prod.py"), "| codex:", codex(r, W(f"{r}/tests/prod.py"))); os.unlink(r + "/tests")
    os.mkdir(r + "/Tests"); open(r + "/Tests/prod.py", "w").close(); print("M-9 claude:", claude(r, b, f"{r}/tests/prod.py"), "| codex:", codex(r, W(f"{r}/tests/prod.py")))
    print("M-17 codex:", codex(r, AP("*** Begin Patch\n*** Add File: docs/x.md\n+x\n  *** Update File: src/prod.py\n@@\n-X = 1\n+X = 2\n*** End Patch\n")))
    print("M-15 control (no space) codex:", codex(r, AP("*** Begin Patch\n*** Update File: src/prod.py\n@@\n-X = 1\n+X = 2\n*** End Patch\n")))
    print("M-15(space) codex:", codex(r, AP("*** Begin Patch\n*** Update File: src/prod.py \n@@\n-X = 1\n+X = 2\n*** End Patch\n")))
for phase in ("step5", "step3"):
    for cell, d, rel in (("a", "Tests", "tests/newmod.py"), ("b", "src", "src/prod.py")):
        with tempfile.TemporaryDirectory() as t:
            r, b = fixture(t, phase); os.makedirs(f"{r}/{d}", exist_ok=True); os.chmod(f"{r}/{d}", 0o311)
            try: os.listdir(f"{r}/{d}"); pre = "listdir ok"
            except PermissionError: pre = "listdir EACCES"
            print(f"AC-3.6({cell}) {phase} [{pre}] claude:", claude(r, b, f"{r}/{rel}"), "| codex:", codex(r, W(f"{r}/{rel}")))
            os.chmod(f"{r}/{d}", 0o755)
EOF
```

Output at `983c2f85` (both interpreters): `M-1 claude: deny no-test-resolved | codex: deny
no-test-resolved`; `M-2 claude: allow | codex: allow`; `M-4 claude: allow | codex: deny
no-test-resolved`; `M-9 claude: allow | codex: allow`; `M-17 codex: allow`; `M-15 control (no
space) codex: deny no-test-resolved`; `M-15(space) codex: allow`; `AC-3.6(a) step5 [listdir
EACCES] claude: allow | codex: allow`; `AC-3.6(b) step5 [listdir EACCES] claude: deny
no-test-resolved | codex: deny no-test-resolved`; `AC-3.6(a) step3 [listdir EACCES] claude: allow
| codex: allow`; `AC-3.6(b) step3 [listdir EACCES] claude: allow | codex: allow`.

**R-3 — the Claude gate's outside-root `# M:H20` cells (M1; T3's pinned control).**

```bash
/opt/anaconda3/bin/python - . <<'EOF'
import json, os, shutil, subprocess, sys, tempfile
H = os.path.abspath(sys.argv[1]) + "/h-mad"; sys.path.insert(0, H + "/tests")
from tdd_gate_support import decision, hook_form, write_state
from pathlib import Path
G = H + "/hooks/h-mad-tdd-gate.sh"
with tempfile.TemporaryDirectory() as t0:
    t = os.path.realpath(t0); r = t + "/root"; os.makedirs(r + "/src"); os.makedirs(t + "/out/tests"); os.makedirs(t + "/out/src")
    subprocess.run(["git", "init", "-q", r]); write_state(Path(r), {"feat": {"phase": "step5", "codex_status": "exhausted"}})
    os.symlink("tests", t + "/out/lnk")
    b = t + "/bin"; os.mkdir(b)
    for n, s in (("python3", sys.executable), ("dirname", "/usr/bin/dirname"), ("basename", "/usr/bin/basename"), ("jq", shutil.which("jq"))): os.symlink(s, f"{b}/{n}")
    for label, target in (("canonical tests/, raw not", t + "/out/lnk/x.py"), ("raw tests/ and canonical tests/", t + "/out/tests/x.py"), ("neither (control)", t + "/out/src/x.py")):
        p = subprocess.run([G], input=json.dumps({"tool_name": "Write", "tool_input": {"file_path": target}}), capture_output=True, text=True, cwd=r, env={"PATH": f"{b}:/usr/bin:/bin", "HOME": str(Path.home()), "CLAUDE_PROJECT_DIR": r})
        o = decision(p, hook_form(Path(G))); print("outside-root", label, "->", o.decision, o.kind)
EOF
```

Output at `983c2f85`: `outside-root canonical tests/, raw not -> deny no-test-resolved`;
`outside-root raw tests/ and canonical tests/ -> allow`; `outside-root neither (control) -> deny
no-test-resolved`. On the fixed gate the first line must be unchanged; dropping the raw conjunct
would turn it into `allow`.

**R-4 — Codex's own `apply_patch` (manual; never in a script or test).** In a scratch copy of the
fixture, never in the repository, record the binary's version, then run `apply_patch` as Codex
dispatches it (`argv[0]=apply_patch`), substituting the header line under test:

```bash
F=$(mktemp -d) && mkdir -p "$F/src" && printf 'X = 1\n' > "$F/src/prod.py" && cd "$F" && codex --version && P=$'*** Begin Patch\n*** Update File: src/prod.py \n@@\n-X = 1\n+X = 2\n*** End Patch\n' && (exec -a apply_patch "$(command -v codex)" "$P"); echo "rc=$?"; cat src/prod.py
```

Reading 2026-09-29 (this author, by hand), trailing-space header (M-15's space variant):
`codex-cli 0.158.0`, `Success. Updated the following files:` / `M src/prod.py`, `rc=0`, `X = 2`,
and `ls src` shows only `prod.py`. The other M-15…M-23 cells and the trim-set code points are the
same command with the header line substituted; T0 enters each as a manual row with its version
and date.

**R-5 — Claude Code Edit on a leaf symlink (PD-5; manual, harness tool).** The orchestrator's
procedure, verbatim: fixture `mkdir -p pd5/src pd5/tests; printf 'X = 1\n' > pd5/tests/t.py; ln
-sf ../tests/t.py pd5/src/link.py`, then the Claude Code Edit tool on `pd5/src/link.py` replacing
`X = 1` with `X = 2`, which is refused with "Refusing to write …: it is a symbolic link. Write to
the link's target path instead"; afterwards `ls -l pd5/src/link.py` still shows the link and `cat
pd5/tests/t.py` still reads `X = 1`. Claude Code 2.1.284, 2026-09-29.

## Version History
- v1.0: Initial plan draft (2026-09-29) from spec v1.0 (662b1ce1). PD-1 F_GETPATH primitive in one shared canonicaliser, bash side does no canonicalisation; PD-2 REAP_GRACE_S=1.0 and a six-field runner result; PD-3 no case-sensitive runner exists, AC-1.10 fails never skips; PD-4 committed probe T0/T9; PD-5 leaf-symlink tools need a live measurement. Opens OQ-P1 (an existing directory the primitive cannot open). Readings at 5e3a8238.
- v1.1: Revision (2026-09-29) against spec v1.2 (e26466a8). OQ-P1 closed (operator: refuse; spec FR-3 arm 2, AC-3.6): G-3 and FR-3 carry both arms, T1 gains the arm-2 guard with no spelling fallback, AC-3.6 owned by T2/T3 (gate halves), scratch reading of AC-3.6's unfixed observables at e26466a8 equals the spec's expected column. PD-5 closed as measured (Edit refused on Claude Code 2.1.284; MultiEdit/NotebookEdit absent, unmeasurable); T0 enters it as manual rows only. T0 gains the OQ-P1 cells under both states. T8 states AC-7.1's 19 guard rows (18 at spec v1.0) with the counting command, as a floor on mutations. FR-5 aligned to spec: REAP_GRACE_S = 1.0, six-field NamedTuple with reap_failed, AC-5.1 < 4.0 s, AC-5.2 unpacking only in test_run_bounded_kills_the_process_group. Next Steps owe the design the canonicaliser's operations and the Claude gate's arm-2 transport.
- v1.2: Revision (2026-09-29) answering plan audit cycle 1 (docs/01-plan/features/tdd-gate-fail-opens.plan.audit.v1.p1.md, codex: 5 must, 1 should; tdd-gate-fail-opens.plan.audit.v1.agy.md, agy: 1 must, a duplicate of codex must 4; both at 983c2f85) against spec v1.2 (e26466a8). M1: G-1 and T3 keep the Claude gate's outside-root M:H20 dual check (canonical target AND raw spelling, spec FR-1 step 7); new pinned outside-root symlink control (R-3), which the re-derived H20B mutation must turn red. M2: T6 asserts equal kinds wherever both gates deny and a published expectation table carrying each cell's decision and kind. M3: no committed artifact invokes an agent CLI (constructed PATH, REPRO agent-cli-reachable=no); the Codex-writes column and trim set become the manual dated reading R-4; residual stated; spec Assumptions wording owed by the spec. M4: every behavioural premise carries its runnable command; new section Reproduction commands with R-1 (F_GETPATH, now also measured on 3.9.6), R-2 (gate cells and AC-3.6), R-3 (M:H20 cells), R-4 (manual apply_patch), R-5 (PD-5 procedure verbatim); premises re-run at 983c2f85; def hermetic_env is defined in two files, not one. M5: the spec table's pointer names T0's unfixed reading; T9's fixed reading is cited separately. S1: mutation floor 20 (16 parentheticals + 3 separate-mutation pairs + 1 in-each-gate), per-guard census remains the acceptance check.
