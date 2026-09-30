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

The feature also carries the operator's fold of OD-6 (spec FR-8): the Codex gate admits the
documented resume oracle, `h_mad_resume_decision.py` reads the minted session id itself behind a new
`--session-id-from-git-dir` flag, and the three host adapters' oracle line drops its `$(…)`
(tasks T10–T12).

## Overview

The spec (`docs/01-plan/features/tdd-gate-fail-opens.spec.md` v1.4 at commit `644f8bf6`; v1.3 at
`766860ba`; v1.2 at `e26466a8`; v1.0 and OD-1…OD-5 operator-approved at commit `662b1ce1`; OD-6
folded by the operator 2026-09-29, spec v1.4) fixes WHAT the gates must decide. This plan fixes the order of
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
- `h-mad/scripts/h_mad_resume_decision.py` (FR-8 change 2): the `--session-id-from-git-dir` flag,
  and a module-level `build_parser()` that `main()` calls (T10).
- `h-mad/references/codex-runtime.md`, `grok-runtime.md` and `agy-runtime.md`: the fenced
  resume-oracle line and its "empty id" prose (FR-8 change 3, T12).
- Tests under `h-mad/tests/` (including the two named deltas in `test_host_runtime_docs.py`,
  AC-8.6), mutation specs under `h-mad/tests/mutation-specs/`.
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
  trim set, Claude Code's tools) are manual rows in T0's reading. A committed comparison of the two
  readings fails on any softened verdict the spec does not name (PD-4, "Old-versus-new verdict
  comparison").
- G-9 (FR-8): under `step5` the Codex gate admits the resume oracle in its documented form, and
  that form carries no command substitution.

## Requirements

- FR-1: one target-normalisation rule in both gates (D3, D4; B2, OD-1). ACs 1.1–1.11.
- FR-2: `.py` suffix case-folded before every name test (D1; B3, OD-3). ACs 2.1–2.5.
- FR-3: unresolvable target refused `judge-error` when governed (B4, OD-4). ACs 3.1–3.6.
- FR-4: Codex gate reads patch headers as Codex does (D2; B6, OD-2). ACs 4.1–4.7.
- FR-5: judge bounds its post-kill reap and reports `judge-timeout` (D5; B5). ACs 5.1–5.5.
- FR-6: pinned repros and a cross-gate differential (B7, OD-5). ACs 6.1–6.3.
- FR-7: every guard bites. AC-7.1.
- FR-8: the Codex gate admits the documented resume oracle (OD-6). ACs 8.1–8.6.
- The spec's NFRs: at most one added Python process in the Claude gate (FR-1 replaces the
  existing `# M:H11` call rather than adding one); no new environment variable (FR-8 adds one CLI
  flag, `--session-id-from-git-dir`); every existing test green except the named deltas (spec
  NFR Compatibility, which names AC-8.6's two).

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
the judge. The gate corpus also carries two cell families the M-table does not number, each
printed per gate and per state mode (`step5`, `step3`-only):

- **`leaf-symlink`**, the third approved relaxation (spec FR-1 "Verdict changes toward ALLOW": a
  leaf symlink into `tests/`, Claude gate): `src/link.py -> ../tests/t.py` with `tests/t.py`
  present, a `Write` of `src/link.py`. Unfixed reading by R-6 at `644f8bf6`: `step5` Claude deny
  `no-test-resolved`, Codex allow; `step3` both allow. Fixed: both allow under both states.
- **`FR-8`** (spec owed item (d)): the Codex gate on a `step5` shell payload of the shape
  `test_codex_hook_allows_exact_safe_hmad_control_script` uses, one cell per command form: the
  documented `--session-id "$(cat …)"` line, the literal `--session-id <uuid>` form, and the
  `--session-id-from-git-dir` form. Unfixed: deny for all three (spec §"Measured premises",
  OD-6 reading at `78e35abf`). Fixed: deny, allow, allow.

**Old-versus-new verdict comparison (the class: every softened verdict is named).**
`h-mad/invariants.base.md` requires running a corpus through the old and new logic, diffing the
verdicts, and accounting for **every** input whose verdict softened. T0 commits
`docs/03-analysis/probes/tdd-gate-fail-opens/compare_readings.py`, which takes two readings and
keys each `REPRO:` gate line by (cell, gate, state mode). It exits non-zero, printing each
offending key, when:

1. a key is present in one reading and absent from the other (a dropped cell would hide a
   softening);
2. a key's verdict moved from deny to allow and the key is not in its **approved set**, a literal
   table in the script: (`M-10`, Claude, `step5`), (`M-10`, Codex, `step5`), (`M-11`, Claude,
   `step5`), (`leaf-symlink`, Claude, `step5`) — spec FR-1's three relaxations — and (`FR-8
   literal-uuid`, Codex, `step5`), (`FR-8 flag`, Codex, `step5`) — spec FR-8, operator-approved
   OD-6 — and (`M-18 M-14`, Codex, `step3`) — spec FR-1 (v1.5), operator-approved 2026-09-30:
   the unfixed Codex gate denies this `step3`-only loop `judge-error` where the Claude gate
   allows, and `step3` is ungoverned.

It prints `COMPARE: PASS softened=N approved=N` or `COMPARE: FAIL …`, and a deny that changes kind
is reported but is not a softening. T0 runs its two controls and commits their output beside the
unfixed reading: the unfixed reading against itself gives `PASS softened=0`, and against a copy
with one extra deny-to-allow key outside the approved set gives `FAIL`. T9 runs it on T0's reading
against T9's reading and commits the output; the feature is not done unless that output is
`PASS`, with `softened` equal to `approved` equal to 7. The approved set has seven keys, not three,
because spec FR-8 (v1.4) adds two approved ALLOWs and spec FR-1 (v1.5) adds the operator-approved
`M-18 M-14` Codex `step3` key, all in the same readings: a smaller table would make T9's
comparison fail on the operator's own decisions. The residual: the comparison covers only the corpus the probe prints; a softened
verdict on a spelling outside that corpus is caught only by the per-task stop-and-report rule
(§"Implementation Strategy").

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
Claude Code 2.1.284 (2026-09-29) by the tool call R-5 (§"Reproduction commands": tool `Edit`,
`file_path` `<scratchpad>/pd5/src/link.py`, `old_string` `X = 1`, `new_string` `X = 2`), which the
tool refused; the link and `pd5/tests/t.py` were unchanged afterwards. R-5 carries the exact
input, response and follow-up commands. Write was already measured refusing (spec §"Measured premises"). **MultiEdit** and
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
| Outside-root `# M:H20` cells on the unfixed Claude gate (M1; spec AC-1.11) | R-3, under `/opt/anaconda3/bin/python` 3.11.8 | `out/lnk/x.py` with `lnk -> tests` (canonical enters `tests/`, raw does not): deny `no-test-resolved`; `out/tests/x.py` (both match): allow; `out/src/x.py` (control): deny `no-test-resolved` |
| `KINDS` has 11 members today (12 after FR-5) | `python3 -c 'import sys;sys.path.insert(0,"h-mad/scripts");import h_mad_tdd_judge as j;print(len(j.KINDS))'` | `11` |
| `JUDGE_DENY_RE` alternates 10 kinds (every `KINDS` member but `red-measured`) | `grep '^JUDGE_DENY_RE=' h-mad/hooks/h-mad-tdd-gate.sh \| python3 -c 'import sys,re;print(len(re.search(r"kind=\(([^)]*)\)",sys.stdin.read()).group(1).split("\|")))'` | `10` |
| Named test and helper symbols exist | `for s in 'def test_run_bounded_kills_the_process_group' 'def test_name_map_runs_under_the_budget' 'def test_timeout_kind' 'def test_claude_gate_kind' 'def test_dd7_differential_matches_the_published_cells' 'def test_codex_gate_kind' 'def decision' 'def hermetic_env'; do printf '%s: ' "$s"; git grep -l -F "$s" -- h-mad/tests \| tr '\n' ' '; echo; done` | the first three in `test_h_mad_tdd_judge.py`; `test_claude_gate_kind` and `test_dd7_…` in `test_h_mad_tdd_gate_judge.py`; `test_codex_gate_kind` in `test_h_mad_codex_tdd_gate_judge.py`; `def decision` in `tdd_gate_support.py` only; `def hermetic_env` in **two** files, `tdd_gate_support.py` (the `**extra` helper T6 reuses) and `conftest.py` (a fixture of the same name, not the one reused). v1.1 said "each found once"; that was false for `hermetic_env` |
| `test_dd7_differential_matches_the_published_cells` asserts 126 cells and 18 denies | `grep -n -F 'assert len(observed) == 126 and observed.count("deny") == 18' h-mad/tests/test_h_mad_tdd_gate_judge.py` | 1 matching line |
| Suite collection floor | `/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests \| tail -1` on a clean tree | `4618 tests collected` |
| Mutation anchors baseline | `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json` | `ANCHORS: ANCHORS_OK specs=118 mutations=1195 ok=1195 drifted=0 unreadable=0 skipped=0 unclassifiable=0` |
| FR-8: the safe list has no oracle entry today (spec OD-6 reading at `78e35abf`, re-run for v1.4) | `/opt/anaconda3/bin/python -c 'import importlib.util as u;s=u.spec_from_file_location("g","h-mad/hooks/h-mad-codex-tdd-gate.py");m=u.module_from_spec(s);s.loader.exec_module(m);d=m.SAFE_HMAD_SCRIPT_OPTIONS;print(len(d),"h_mad_resume_decision.py" in d)'` | `10 False`, at `644f8bf6` |
| FR-8: `git` is refused by the gate's shell policy (why the flag, not a path) | the same import, then `print(m._safe_shell_command("git rev-parse --absolute-git-dir", ".", "."))` | `False`, at `644f8bf6` |
| FR-8: the script builds its parser inside `main()`, with no `build_parser()` for AC-8.2 to reach (why T10 adds one) | `grep -n -E 'def build_parser\|ArgumentParser' h-mad/scripts/h_mad_resume_decision.py`; `grep -c 'parser.add_argument(' h-mad/scripts/h_mad_resume_decision.py` | 1 matching line, the `ArgumentParser(` inside `main()`, and no `def build_parser`; 5 matching lines, one per option (`--state`, `--feature`, `--host`, `--session-id`, `--now`), at `644f8bf6` |
| FR-8: each adapter carries one `$(cat …)` oracle line | `for f in codex grok agy; do printf '%s ' $f; grep -c 'h_mad_resume_decision.py.*session-id "\$(cat' h-mad/references/$f-runtime.md; done` | `codex 1`, `grok 1`, `agy 1` (matching lines), at `644f8bf6` |

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
| T0 | Probe `reproduce.py` + unfixed reading (PD-4). Includes the OQ-P1 cells, each under the `step5` and the `step3`-only state: a mode-`0311` directory spelled in another case with an absent leaf (on-disk `Tests/`, `tests/newmod.py`), and an existing leaf whose parent lacks `r` (`src/` at `0311`, `src/prod.py`); each cell prints its `os.listdir` precondition. These cells are the measurement of AC-3.6's unfixed observables (a), (b) and (c). Plus the outside-root `# M:H20` cells of R-3 (spec AC-1.11), the `leaf-symlink` cells (R-6) and the three `FR-8` gate cells (spec owed item (d)), each described in PD-4. The probe invokes no agent CLI and prints `REPRO: agent-cli-reachable=no` (PD-4). Also commits `compare_readings.py` (PD-4, "Old-versus-new verdict comparison") with the output of its two controls (self-comparison `PASS softened=0`; an injected unapproved deny-to-allow key `FAIL`). Manual rows, entered by hand with their command, never printed by the script: one row per R-4 case (the Codex-writes column of M-15…M-23, each trim code point, Codex following a leaf symlink), with `codex --version`, and PD-5 (R-5's exact tool input and response: Write and Edit refused on Claude Code 2.1.284; MultiEdit and NotebookEdit absent from that build) | — (measurement) | — |
| T1 | Shared canonicaliser: component walk, F_GETPATH on existing directories, leaf inode match returning **every** entry of the canonical parent that shares the leaf's `(st_dev, st_ino)` (the hard-link contract, below the table: the canonicaliser returns all names and never evaluates an exemption), remainder append + lexical collapse, unresolvable predicate over both FR-3 arms. **Arm-2 guard:** an `OSError` from the primitive's open of an existing component (FR-1 step 3) or from the listing of the leaf's canonical parent (FR-1 step 4) makes the result unresolvable, with no fallback to the spelling. Unit tests drive it directly, including the arm-2 guard on the `0311` fixture. | 1.7, 1.8 (unit half), 1.9 (unit half), 1.10, 3.4 | T0 |
| T2 | Codex gate: root, payload `cwd` (before `_payload_cwd_base` tests containment) and every target through T1; fold in `_is_production_python`, which runs on every leaf name T1 returns (the target is production unless every name is exempt, the hard-link contract below the table); FR-3 refusal (both arms) gated on `_any_phase5_status` ∈ {`active`, `unknown`} | 1.1–1.6, 1.8, 1.9, 2.1–2.4, 3.1–3.6 (Codex halves) | T1 |
| T3 | Claude gate: one Python call returns canonical root, canonical target, **every leaf name sharing the leaf's inode in its canonical parent**, and the unresolvable condition (both FR-3 arms; the encoding is the design's, the content is the hard-link contract below the table), replacing `ROOT_ABS`'s `pwd -P` and the `# M:H11` call; `IN_ROOT`, the in-root directory exemption (`# M:H19`), the basename exemptions and the suffix test read the canonical values; the outside-root directory exemption (`# M:H20`) keeps its dual check per spec FR-1 step 7 — `_dir_match` of the canonical target **and** `_dir_match` of the raw spelling `RAW_TARGET` — so the canonical value replaces only its first conjunct. **Pinned outside-root symlink control** (R-3's first cell): a target outside the root, `out/lnk/x.py` with `out/lnk -> tests`, whose canonical form enters `tests/` but whose raw spelling does not, stays deny `no-test-resolved` on the fixed gate; with its positive control `out/tests/x.py` (allow) and negative control `out/src/x.py` (deny). This pin is spec AC-1.11. Its discriminating observable is the mutant, not the unfixed tree: the existing mutation `H20B` (keeps only the `$TARGET_PATH` conjunct) kills only on the **fixed** tree, where `TARGET_PATH` is canonical. On the unfixed tree `TARGET_PATH` is only `normpath`'d, so `H20B` does not move the cell, and a mutation run before T3 lands reports `H20B` SURVIVED legitimately (spec AC-1.11, measured at `4192ad8c`). Score `H20B` only after T3, once T3 has re-derived it at the same guard; the basename `case` (`# M:H6`) and the `*.py` test run over every returned name, allowing only when every name allows; fold in the basename `case` and the `*.py` test; FR-3 refusal after `_read_state` reports `active`/`unreadable`, with `_chain_may_hold_state` and `TDD-STATE: none` unchanged | 1.1–1.9, 1.11, 2.1–2.4, 3.1–3.6 (Claude halves) | T1 |
| T4 | Codex header grammar: `\n` split, both-end trim with `str.isspace()` minus U+001C–U+001F, exact markers, control-byte and empty-path refusal when governed; `--self-check` gains the trailing-space and indented cases. AC-4.6's code points are the ones the manual R-4 reading measured on codex-cli 0.158.0; the tests drive only the gate, never `codex` (PD-4) | 2.5, 4.1–4.7 | T2 |
| T5 | Judge: `REAP_GRACE_S = 1.0`, six-field `NamedTuple` return adding `reap_failed: bool` (AC-5.1 bound 4.0 s; AC-5.2's only unpacking delta is `test_run_bounded_kills_the_process_group`), reap failure → `judge-timeout` on the name-map path and the pytest path, `judge-timeout` first in the priority tuple and stopping further runs, `KINDS` + `JUDGE_DENY_RE`, new rows in `test_claude_gate_kind` and `test_codex_gate_kind` | 5.1–5.5 | — (independent of T1–T4) |
| T6 | Cross-gate differential over the OD-5 domain as spec v1.4 FR-6 defines it, reusing `tdd_gate_support.decision` and `tdd_gate_support.hermetic_env`. **Domain rule, two clauses:** a resolvable spelling is in-root when its canonical target (FR-1) is inside the canonical root; an unresolvable spelling (FR-3, either arm) is in-root when its **resolved prefix** is inside the canonical root, the resolved prefix being the longest prefix of the spelled components, after FR-1 step 1, that FR-1 step 2 walks before FR-3's predicate holds ("inside" includes equal). **Cells:** M-1…M-14 and M-18, plus the controls `notes.md`, `tests/test_x.py` and `sub/test_x.PY`, each asserted as its own row. The required unresolvable cells stay in, with their resolved prefixes: M-12 `R/docs`, M-13 leaf case `R/src`, M-13 intermediate case (`lnk -> nowhere`) `R`, M-14 `R/src`, and each of them again under M-18; their expected rows are deny `judge-error` in **both** gates (equal kinds) under the governing state and allow under the `step3`-only state (FR-3 fires at step 2, before step 6's inside-root test). The test asserts each resolved prefix is inside the canonical root, so a cell cannot leave the domain silently. It asserts, per spec FR-6: (1) the two gates' decisions are equal on every cell; (2) on every cell where both deny, their **kinds** are equal (Codex kind parsed with `kind=([a-z-]+)` from the reason); (3) each cell's decision, and its kind when it denies, equals that cell's row in a **published expectation table** in the test, one row per cell and state mode carrying the expected decision and the expected kind; (4) the table's deny count is derived by the test from the table, never typed. Each assertion is its own failure message, so a cross-gate kind disagreement fails on its own and is not masked by an equal decision. Re-run `dd7_differential.py` (AC-6.3) | 6.1–6.3 | T2, T3 |
| T7 | Documentation surfaces (D-8), including the three adapters `codex-runtime.md`, `grok-runtime.md` and `agy-runtime.md` (spec owed item (e)); their oracle line and "empty id" prose are T12's edit, and T7 re-checks each adapter's other gate statements against the fixed gates | — (doc-derived tests stay green) | T2–T5, T12 |
| T8 | Mutation specs for every guard AC-7.1 names, one mutation per alternation branch, each alone. The mutation **floor is 25** at spec v1.4 (20 at spec v1.2 and v1.3, 19 at spec v1.0): the AC-7.1 paragraph's `(AC-` parentheticals, plus one for each `separate mutations` pair, plus one for each guard named `in each gate` (one mutation per gate, AC-2.2). Command: `P=$(git show 644f8bf6:docs/01-plan/features/tdd-gate-fail-opens.spec.md \| awk '/AC-7\.1:/{f=1} f&&/^$/{exit} f' \| tr '\n' ' ' \| tr -s ' ')`, then `echo "$P" \| grep -o '(AC-' \| wc -l` → 21 occurrences, `echo "$P" \| grep -o 'separate mutations' \| wc -l` → 3, `echo "$P" \| grep -o 'in each gate' \| wc -l` → 1; 21 + 3 + 1 = 25 (run 2026-09-29 for plan v1.4). The five rows spec v1.4 added are FR-8's: the safe-list entry (AC-8.1), its equality with the parser (AC-8.2), the id-file read (AC-8.3), the `cannot_judge` answer (AC-8.4) and the mutual exclusion (AC-8.5), whose mutations live in T11 and T10. Earlier readings of the same command: `e26466a8` and `983c2f85` → 16, 3, 1 = 20; `766860ba` (AC-1.11 added, no AC-7.1 row for `H20`) → 16, 3, 1 = 20; `662b1ce1` → 15, 3, 1 = 19. The floor moves with every spec revision that edits AC-7.1 and is re-measured with the same command, at the spec's sha, whenever the spec changes. 25 is a **floor**, not the count: the acceptance check is the per-guard census over the committed specs — every guard AC-7.1 names, and every gate a guard is named in, has at least one mutation reported caught | 7.1 | T1–T6, T10, T11 |
| T9 | Re-run `reproduce.py` on the fixed tree; commit the reading; run `compare_readings.py` on T0's reading against it and commit the output, which must be `COMPARE: PASS softened=7 approved=7` (PD-4) | — (measurement) | T1–T8, T10–T12 |
| T10 | Script (spec FR-8 change 2, owed item (b)): `h_mad_resume_decision.py` gains a module-level `build_parser()` that `main()` calls, and `--session-id-from-git-dir` in one argparse mutually exclusive group with `--session-id`; with the flag it runs `git rev-parse --absolute-git-dir` under a 10 s bound, reads `<git dir>/h-mad-session-id.<feature>`, strips it, and decides as `--session-id <id>` would; each of the six failure modes prints `cannot_judge` on every host. Tests use a git repository and a linked worktree (AC-8.3) and a hermetic `PATH` without `git` (AC-8.4) | 8.3, 8.4, 8.5 | — (independent of T1–T9) |
| T11 | Codex gate (spec FR-8 change 1, owed item (a)): `SAFE_HMAD_SCRIPT_OPTIONS` gains the `h_mad_resume_decision.py` key with exactly the parser's long options minus `--help` (six after T10), no per-script value check. AC-8.2's test derives the set from `build_parser()` (T10), reading each action's `option_strings`, and never types it | 8.1, 8.2 | T10 |
| T12 | Adapters (spec FR-8 change 3, owed item (c)): the fenced oracle line in `codex-runtime.md`, `grok-runtime.md` and `agy-runtime.md` becomes the `--session-id-from-git-dir` form, and each adapter's "empty id" prose becomes "the oracle cannot read the id and returns `cannot_judge`"; the two named deltas in `test_host_runtime_docs.py` (`test_claims_section_fenced_lines`'s `oracle` condition, `test_claims_lines_execute_across_invocations`'s oracle selection) | 8.6 | T10, T11 |

**The hard-link contract (spec FR-1 step 4, AC-1.9; agy must #1 of audit cycle 2).** Chosen:
**the canonicaliser returns all names; it never evaluates an exemption.** For an existing leaf it
returns the tuple of every entry of the leaf's canonical parent whose `(st_dev, st_ino)` equals the
leaf's, sorted, at least one name. For an absent leaf it returns the one spelled leaf name (FR-1
step 5). Each gate then applies its own basename exemptions and its `.py` suffix test (after the
FR-2 fold) to **every** name: the write is exempt by name only if every name is exempt, and it is
non-`.py` only if every name is non-`.py`. The directory exemptions need no loop, because every
name shares the one canonical parent. The Codex gate receives the tuple in-process (T2). The Claude
gate receives it from the single Python call (T3), which also returns the canonical root, the
canonical target and the unresolvable condition. Why not the alternative (the call evaluates the
exemptions): it would move the Claude gate's basename `case` (`# M:H6`) and `*.py` test into Python,
putting the exemption list in a third place beside the Codex gate's `_is_production_python` and
relocating the `# M:H6` anchor; returning names keeps each gate's exemption code where it is. Owed
by the design: the encoding of the name list on the Claude gate's call output. It must carry any
byte a directory entry can hold except NUL (a newline, a space), and a list the gate cannot parse
is `judge-error`, never a fallback to the spelled leaf (the fail-closed rule below). AC-1.9's
fixture (`src/prod.py` and `src/test_prod.py` on one inode, spelled `src/test_prod.py`) is the pin
in both gates; its AC-7.1 mutation makes T1 return only the spelled name, which turns AC-1.9 red
in both gates at once. Each gate's per-name loop is a separate site the design names; whether it
gets its own mutation beyond the floor is the per-guard census's call (T8).

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
  spec's three from FR-1: M-10 (both gates), M-11 (Claude gate), and a leaf symlink into `tests/`
  (Claude gate); plus FR-8's two admitted oracle forms (the literal-uuid and the
  `--session-id-from-git-dir` forms, Codex gate); plus the operator-approved (2026-09-30, spec
  v1.5) Codex gate on `M-18 M-14` under `step3`. Any other existing test that changes verdict is a
  stop-and-report, not a test edit. Over the probe's corpus this is mechanical:
  `compare_readings.py` (PD-4) fails on any softened key outside the approved set of seven. The
  axis along which a fourth ALLOW could slip in unnamed is an exemption whose input changes from
  the spelling to the canonical value; the only such exemption outside the root is `# M:H20`, and
  it keeps its raw-spelling conjunct (T3), pinned by R-3's outside-root symlink control (spec AC-1.11). Inside
  the root, a verdict change beyond the named ones is the stop-and-report above; the spec, not this
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
| D-8 | Documentation: `h-mad/references/codex-implementer-prompt.md` "Hook:" bullets (resolved identity, any-case `.py`), `h-mad/SKILL.md` helper-scripts bullet for `h_mad_tdd_judge.py` (`judge-timeout`), `h-mad/references/codex-runtime.md` §"Trust boundary" (`judge-timeout`, unresolvable refusal). The design confirms whether `h-mad/references/agy-runtime.md` §"The TDD gate" needs a change: it names no judge kind (`grep -c -E "$(python3 -c 'import sys;sys.path.insert(0,"h-mad/scripts");import h_mad_tdd_judge as j;print("\|".join(sorted(j.KINDS)))')" h-mad/references/agy-runtime.md` → 0 matching lines over the whole file, at `983c2f85`). The three adapters `codex-runtime.md`, `grok-runtime.md` and `agy-runtime.md` §"Context budget and claims": the resume-oracle line and its "empty id" prose (FR-8 change 3; edited in T12, listed here per spec owed item (e)). | docs | FR-2, FR-3, FR-5, FR-8 |
| D-10 | FR-8: `h_mad_resume_decision.py` `build_parser()` and `--session-id-from-git-dir` (T10); the `SAFE_HMAD_SCRIPT_OPTIONS` entry (T11); the adapters' oracle line and the two `test_host_runtime_docs.py` deltas (T12) | script, hook, docs, tests | FR-8 |
| D-9 | `docs/03-analysis/probes/tdd-gate-fail-opens/reproduce.py` (gates and judge only, no agent CLI) + `compare_readings.py` and its two controls' output (T0) + unfixed reading with the manual R-4 and R-5 rows (T0) + fixed reading and its comparison output (T9), each a separate file | probe | G-8, PD-4, PD-5 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| An existing directory the primitive cannot open or list (OQ-P1) falls back to its spelling | A fail-open of M-9's class under a mode-`0311` directory | Closed by the operator (refuse): spec FR-3 arm 2 and AC-3.6; T1's arm-2 guard has no spelling fallback and its own AC-7.1 mutation; T0's probe carries the OQ-P1 cells |
| A Claude Code tool replaces a leaf symlink (PD-5) | FR-1's referent rule allows a production write through a link into `tests/` | Measured on 2.1.284: Write and Edit refuse, MultiEdit and NotebookEdit absent; a tool in a later build is measured before it is trusted (spec residual) |
| The canonicaliser uses an API absent on the suite's 3.11.8 (`ALLOW_MISSING`, `O_SEARCH`) | Green under PATH `python3` 3.14.7, red or wrong under the suite | PD-1 names the constraint; T1's unit tests run under the suite interpreter |
| Rewriting marked lines drifts mutation anchors silently | A guard's mutation no longer applies, or relocates and reports SURVIVED | `--check-anchors` `ANCHORS_OK drifted=0` after every task; re-derive at the same guard |
| Canonicalisation flips an existing pinned verdict beyond the spec's named relaxations (FR-1's three, FR-8's two, and the operator-approved Codex `M-18 M-14` `step3` key of spec v1.5) | Silent softening of a pinned cell | `compare_readings.py` fails on any softened key of the probe's corpus outside the approved set of seven (PD-4; T0 runs its controls, T9 commits `PASS softened=7 approved=7`); stop-and-report rule for anything outside the corpus; T6 re-runs `dd7_differential.py` and `test_dd7_differential_matches_the_published_cells` stays at 126/18 |
| The Codex trim set is re-measured against a later codex-cli | AC-4.6's code-point cases pin a stale grammar | T0's manual R-4 rows record `codex --version` beside each row; a version change is caught only when R-4 is re-taken by hand on the new binary, because no committed artifact may invoke `codex` (PD-4 residual; spec Assumptions owes the matching wording) |
| Canonicalising the Claude gate's outside-root exemption drops its raw-spelling conjunct (`# M:H20`) | An outside-root target whose canonical form enters `tests/` becomes a fourth, unnamed ALLOW | T3 keeps the dual check (spec FR-1 step 7); R-3's outside-root symlink control is a pinned test (spec AC-1.11), and the re-derived `H20B` mutation must turn it red on the fixed tree (on the unfixed tree `H20B` SURVIVES legitimately, so it is scored only after T3) |
| The committed probe or a new test reaches an agent CLI | Breaks `invariants.base.md` §"Dispatched agent CLIs are not script dependencies"; a probe reading then depends on an installed agent | Constructed `PATH` for every spawned process; `REPRO: agent-cli-reachable=no` gates the reading's validity (PD-4) |
| The reap grace is too short on a loaded machine | A plain timeout is misreported as `judge-timeout` | Both kinds DENY, so the write is refused either way; AC-5.2's no-descendant case pins `timeout` |
| The hard-link rule is lost at the gate boundary (agy must #1 of audit cycle 2) | A name sharing the leaf's inode is exempt while its sibling is production (AC-1.9's class) | T1 returns every same-inode name and each gate tests every name (the hard-link contract, §"Implementation Strategy"); an unparseable name list is `judge-error`; AC-1.9 pinned in both gates with its AC-7.1 mutation |
| FR-8 closes only the oracle line (spec Residuals, "FR-8 closes the oracle line only") | Each adapter's `h_mad_state_write.py` lines (`--create --claim`, `--claim`, `--beat`, `--set`, `--release`) still use `$HMAD_SKILL_ROOT` and `$(cat …)`, so the Codex gate still refuses them under `step5`, including `--beat` and `--release` during Phase 5 | Not fixed here: the operator's fold names only the oracle. Stated as the spec's residual; an operator decision to fold them is a spec change first |
| `--session-id-from-git-dir` hides a read failure as "no id" | On the Claude host a missing id reaches `decide` as `None` and prints `enter_autonomous` | Every failure mode prints `cannot_judge` on every host (T10); AC-8.4's `--host claude` cases discriminate, and the fail-closed branch has its own AC-7.1 mutation |
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
- Every reading this plan cites carries its command inline or as R-1…R-6 in §"Reproduction
  commands", runnable from the skills root. T0's probe is the committed instrument that
  supersedes them for every gate and judge row; R-4 and R-5 stay manual by construction (PD-4).

## Success Criteria

- Every AC in spec FR-1…FR-8 passes as an automated test on the fixed tree. The "unfixed" halves
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
- The pinned outside-root symlink control (R-3's first cell, spec AC-1.11) stays deny
  `no-test-resolved` on the fixed Claude gate, and `H20B` turns it red on the fixed tree.
- T9's committed `compare_readings.py` output is `COMPARE: PASS softened=7 approved=7`: every
  softened verdict in the corpus is one the spec names, and every named one happened.
- The mutation census covers every guard AC-7.1 names at spec v1.4, a floor of 25 mutations (T8).

## Out-of-Scope (confirmed from spec)

- The shell-command policy and the Codex `workdir` question (gap report §"Unverified").
- The empty-target rule under a governed sub-project (gap report §"Unverified").
- The name map (`h_mad_derive_test_path.sh`) and impl-plan test resolution.
- Hard links across directories, and a legitimate `*.PY` data file (spec residuals, stated, not
  fixed).
- Host hook timeouts (predecessor OQ-D1). FR-5 bounds the judge, not the host.
- A Linux or case-sensitive runner (PD-3).

## Next Steps

1. Operator review of v1.4, the corrective revision after plan audit cycle 2 (the second and last
   gating round; v1.4 is not re-audited). OQ-P1 decided refuse, PD-5 measured, OD-1…OD-5 approved,
   OD-6 folded as FR-8.
2. Phase 4 design.
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

   Owed to the design by this revision:
   - **The hard-link name list's encoding** on the Claude gate's call output (§"Implementation
     Strategy", the hard-link contract): it carries any byte but NUL, and an unparseable list is
     `judge-error`. The contract itself (all names returned, each gate tests every name) is fixed
     here; the design names each gate's per-name loop site.
   - **FR-8's git-dir read** (spec v1.4 owed item): where in `h_mad_resume_decision.py` the
     `git rev-parse --absolute-git-dir` call and the id-file read sit relative to `decide`, and the
     name of the 10 s bound's module constant.
   - **`compare_readings.py`'s key format**: the `REPRO:` line grammar T0 prints, from which the
     (cell, gate, state mode) key is parsed.
4. Owed by the spec author (this plan does not edit the spec): (a) spec §"Assumptions" says a
   later Codex "is caught by AC-4.6 only if the owed probe re-runs against the new binary", and
   spec §"Measured premises" says the committed probe's reading replaces the whole table; under
   PD-4 the probe never invokes `codex`, so the Codex-writes column and the trim set are
   re-derived only by the manual R-4 reading, and the pointer must name T0's reading **with its
   manual rows**; (b) the outside-root symlink control of R-3 had no AC of its own in spec FR-1.
   Both were answered by spec v1.3 (`766860ba`), which added AC-1.11 for (b).

## Reproduction commands

Each command runs from the skills root. R-1…R-3 were run for v1.2 at `983c2f85` on 2026-09-29,
macOS 27.0 APFS, and their outputs are the readings cited above; they build every fixture in a
`TemporaryDirectory`, drive only the two gates (through the existing `tdd_gate_support` helpers),
and give every spawned gate a constructed `PATH` with no agent CLI. R-6 has the same properties and
was run at `644f8bf6` for v1.4. R-4 and R-5 are **manual**: they exercise an agent's own tool, so
no committed artifact runs them (PD-4); R-4 was re-taken case by case for v1.4, R-5 is the
orchestrator's tool call.

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

**R-3 — the Claude gate's outside-root `# M:H20` cells (M1; T3's pinned control, spec AC-1.11).**

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
(`H20B`) turns it into `allow` there. On this unfixed gate `H20B` leaves all three lines unchanged
(spec AC-1.11), so `H20B` SURVIVED before T3 is expected, not a defect.

**R-4 — Codex's own `apply_patch` (manual; never in a script or test).** Run by hand, from a
scratch directory outside the repository, never committed, and deleted after the run; each case
builds its own fixture in a `TemporaryDirectory` (removed on exit). Every case is invoked as
Codex dispatches the tool, `argv[0]=apply_patch` on the `codex` binary (the same as
`exec -a apply_patch codex "$P"`). Each case's fixture is `src/prod.py` = `X = 1`, empty `docs/` and
`tests/`, plus the case's own `setup`; each case's patch is the literal string in its `run` call.
The output line per case is: label, `rc`, the first 90 characters of stdout+stderr with newlines
shown as ` / `, and every file (`repr(name)=repr(content)`) or symlink (`repr(name)->repr(target)`)
in the fixture afterwards. Invocation: `/opt/homebrew/bin/python3 r4.py`, with `r4.py`:

```python
import os, shutil, subprocess, sys, tempfile
CODEX = shutil.which("codex")
B, E = "*** Begin Patch\n", "*** End Patch\n"
UPD = "@@\n-X = 1\n+X = 2\n"
def run(label, patch, setup=()):
    with tempfile.TemporaryDirectory() as t:
        os.makedirs(t + "/src"); os.makedirs(t + "/docs"); os.makedirs(t + "/tests")
        open(t + "/src/prod.py", "w").write("X = 1\n")
        for kind, a, b in setup:
            if kind == "file": open(t + "/" + a, "w").write(b)
            if kind == "link": os.symlink(b, t + "/" + a)
        p = subprocess.run(["apply_patch", patch], executable=CODEX, cwd=t, capture_output=True, text=True)
        msg = (p.stdout + p.stderr).strip().replace("\n", " / ")[:90]
        state = []
        for d, ds, fs in os.walk(t):
            for n in sorted(fs + [x for x in ds if os.path.islink(os.path.join(d, x))]):
                q = os.path.join(d, n); rel = os.path.relpath(q, t)
                if os.path.islink(q): state.append(f"{rel!r}->{os.readlink(q)!r}")
                else: state.append(f"{rel!r}={open(q, errors='replace').read()!r}")
        print(f"{label} | rc={p.returncode} | {msg} | {' '.join(sorted(state))}")
print("codex:", subprocess.run([CODEX, "--version"], capture_output=True, text=True).stdout.strip())
run("M-15 control", B + "*** Update File: src/prod.py\n" + UPD + E)
run("M-15 CRLF patch", (B + "*** Update File: src/prod.py\n" + UPD + E).replace("\n", "\r\n"))
CPS = [0x09, 0x0B, 0x0C, 0x0D, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x85, 0xA0, 0x1680] + list(range(0x2000, 0x200C)) + [0x2028, 0x2029, 0x202F, 0x205F, 0x3000, 0xFEFF]
for c in CPS:
    ch = chr(c)
    run(f"trail U+{c:04X}", B + "*** Update File: src/prod.py" + ch + "\n" + UPD + E)
    run(f"lead  U+{c:04X}", B + ch + "*** Update File: src/prod.py\n" + UPD + E)
run("M-16 lead space", B + " *** Update File: src/prod.py\n" + UPD + E)
run("M-17 Add+indented Update", B + "*** Add File: docs/x.md\n+x\n  *** Update File: src/prod.py\n" + UPD + E)
run("M-19 Move trailing space", B + "*** Update File: docs/a.md\n*** Move to: src/prod2.py \n@@\n-a\n+b\n" + E, [("file", "docs/a.md", "a\n")])
run("M-23 lead space Move", B + "*** Update File: docs/a.md\n *** Move to: src/new.py\n@@\n-a\n+b\n" + E, [("file", "docs/a.md", "a\n")])
run("M-20 Add + U+001F", B + "*** Add File: src/n.py\x1f\n+x\n" + E)
run("AC-4.4 Add interior U+0001", B + "*** Add File: src/pr\x01od.py\n+x\n" + E)
for h in ["*** update file: src/prod.py", "***  Update File: src/prod.py", "*** Update File:src/prod.py", "**** Update File: src/prod.py", "*** Update File:\tsrc/prod.py"]:
    run(f"M-22 {h!r}", B + h + "\n" + UPD + E)
run("leaf symlink", B + "*** Update File: src/link.py\n" + UPD + E, [("file", "tests/t.py", "X = 1\n"), ("link", "src/link.py", "../tests/t.py")])
```

The code-point list is every code point for which Python `str.isspace()` is true except U+000A,
the line separator itself (the list was checked against
`python3 -c 'print([hex(c) for c in range(0x110000) if chr(c).isspace()])'`, 29 code points, at
this reading), plus U+200B and U+FEFF. So T4's rule, `str.isspace()` minus U+001C–U+001F, is
measured at **every** code point it admits and every one it removes; no trim code point T4 relies
on is inferred. What stays inferred is only the claim for code points outside this list (spec
§"Measured premises": "The code points not run are inferred from the property, not measured").

Reading: codex-cli 0.158.0, 2026-09-29T07:58:57Z, this plan's author, run at skills `644f8bf6`,
`/opt/homebrew/bin/python3` 3.14.7; the script and every fixture were deleted after the run. The
output, 75 lines, is below. Rows that group code points stand for lines that are byte-identical
except for their label; `<tmp>` stands for the `TemporaryDirectory` path, cut at 90 characters.

| Case (labels) | Observed output after the label |
|---|---|
| `codex:` | `codex-cli 0.158.0` |
| `M-15 control`, `M-15 CRLF patch` | `rc=0 \| Success. Updated the following files: / M src/prod.py \| 'src/prod.py'='X = 2\n'` |
| `trail` and `lead` for U+0009, U+000B, U+000C, U+000D, U+0020, U+0085, U+00A0, U+1680, U+2000 to U+200A, U+2028, U+2029, U+202F, U+205F, U+3000 (48 lines) | `rc=0 \| Success. Updated the following files: / M src/prod.py \| 'src/prod.py'='X = 2\n'` |
| `trail` for U+001C, U+001D, U+001E, U+001F, U+200B, U+FEFF (6 lines) | `rc=1 \| Failed to read file to update <tmp>… \| 'src/prod.py'='X = 1\n'` |
| `lead` for U+001C, U+001D, U+001E, U+001F, U+200B, U+FEFF (6 lines) | `rc=1 \| Invalid patch hunk on line 2: '<code point>*** Update File: src/prod.py' is not a valid hunk header. … \| 'src/prod.py'='X = 1\n'` |
| `M-16 lead space` | `rc=0 \| Success. Updated the following files: / M src/prod.py \| 'src/prod.py'='X = 2\n'` |
| `M-17 Add+indented Update` | `rc=0 \| Success. Updated the following files: / A docs/x.md / M src/prod.py \| 'docs/x.md'='x\n' 'src/prod.py'='X = 2\n'` |
| `M-19 Move trailing space` | `rc=0 \| Success. Updated the following files: / M src/prod2.py \| 'src/prod.py'='X = 1\n' 'src/prod2.py'='b\n'` (`docs/a.md` is gone) |
| `M-23 lead space Move` | `rc=1 \| Failed to find expected lines in <tmp>… \| 'docs/a.md'='a\n' 'src/prod.py'='X = 1\n'` |
| `M-20 Add + U+001F` | `rc=0 \| Success. Updated the following files: / A src/n.py \| 'src/n.py\x1f'='x\n' 'src/prod.py'='X = 1\n'` |
| `AC-4.4 Add interior U+0001` | `rc=0 \| Success. Updated the following files: / A src/prod.py \| 'src/pr\x01od.py'='x\n' 'src/prod.py'='X = 1\n'` |
| `M-22` × 5 (each header in the list) | `rc=1 \| Invalid patch hunk on line 2: '<the header>' is not a valid hunk header. … \| 'src/prod.py'='X = 1\n'` |
| `leaf symlink` | `rc=0 \| Success. Updated the following files: / M src/link.py \| 'src/link.py'->'../tests/t.py' 'src/prod.py'='X = 1\n' 'tests/t.py'='X = 2\n'` |

Each result equals the spec's "Codex writes" column for M-15…M-23 and its trim-set paragraph.
Two readings go beyond the spec's table and change nothing in it: U+001D (not in the spec's list)
is not trimmed, as `str.isspace()` minus U+001C–U+001F predicts; and the interior-U+0001 Add
writes `src/pr\x01od.py`, which is why AC-4.4 refuses it. T0 enters each case as a manual row
with this version and date.

**R-5 — Claude Code Edit on a leaf symlink (PD-5; manual, harness tool).** Taken by the
orchestrator on Claude Code 2.1.284, 2026-09-29, in the session scratchpad (written `<scratchpad>`
below). This is a **Claude Code tool call, not a shell command**: no script can replay it, and
nothing committed re-runs it (PD-4). It is re-taken by hand, in a Claude Code session, on any
build that is to be trusted.

1. Fixture, shell, run in `<scratchpad>`:
   `mkdir -p pd5/src pd5/tests; printf 'X = 1\n' > pd5/tests/t.py; ln -sf ../tests/t.py pd5/src/link.py`
2. Tool call, the exact input:

   | Field | Value |
   |---|---|
   | tool | `Edit` |
   | `file_path` | `<scratchpad>/pd5/src/link.py` |
   | `old_string` | `X = 1` |
   | `new_string` | `X = 2` |

3. Exact response: "Refusing to write …/pd5/src/link.py: it is a symbolic link. Write to the link's
   target path instead: …/pd5/tests/t.py." (the orchestrator elided the scratchpad prefix as `…`).
4. Afterwards, shell: `ls -l pd5/src/link.py` showed the link to `../tests/t.py`, and
   `cat pd5/tests/t.py` showed `X = 1`.

MultiEdit and NotebookEdit are absent from that build's tool set, so no call could be made.

**R-6 — the `leaf-symlink` corpus cell on the unfixed gates (PD-4, codex must #1 of audit
cycle 2).** It reuses R-2's definitions verbatim: the command below extracts R-2's heredoc body up to
its first `with tempfile.TemporaryDirectory() as t:` line, appends the cell, runs it, and deletes
the scratch file.

```bash
S=<scratchpad>/leafprobe.py; awk '/^\*\*R-2 /{f=1} f&&/^```bash$/{g=1;next} g&&/^EOF$/{exit} g' docs/01-plan/features/tdd-gate-fail-opens.plan.md | sed '1d' | awk '/^with tempfile.TemporaryDirectory\(\) as t:$/{exit} {print}' > $S; cat >> $S <<'EOF'
for phase in ("step5", "step3"):
    with tempfile.TemporaryDirectory() as t:
        r, b = fixture(t, phase); os.makedirs(r + "/tests"); open(r + "/tests/t.py", "w").write("X = 1\n"); os.symlink("../tests/t.py", r + "/src/link.py")
        print("leaf-symlink", phase, "claude:", claude(r, b, f"{r}/src/link.py"), "| codex:", codex(r, W(f"{r}/src/link.py")))
EOF
/opt/anaconda3/bin/python $S . ; rm -f $S
```

Output at `644f8bf6` (2026-09-29, `/opt/anaconda3/bin/python` 3.11.8): `leaf-symlink step5 claude:
deny no-test-resolved | codex: allow`; `leaf-symlink step3 claude: allow | codex: allow`. So the
relaxation is the Claude gate's alone under `step5`, as spec FR-1 says ("Codex already follows
it"), and the approved-set key is (`leaf-symlink`, Claude, `step5`) only. The files R-2 and R-6
exercise are unchanged since `983c2f85`: `git diff --stat 983c2f85 644f8bf6 --
h-mad/hooks/h-mad-tdd-gate.sh h-mad/hooks/h-mad-codex-tdd-gate.py h-mad/scripts/h_mad_tdd_judge.py
h-mad/tests/tdd_gate_support.py` prints nothing. (The wider `h-mad/hooks h-mad/scripts
h-mad/tests` pathspec does move over that range, 11 files from unrelated features, so the
§"Verified premises" suite floor and anchor baseline stamped at `983c2f85` are stale by
construction and are re-measured at the branch base, as that section already requires.)

## Version History
- v1.0: Initial plan draft (2026-09-29) from spec v1.0 (662b1ce1). PD-1 F_GETPATH primitive in one shared canonicaliser, bash side does no canonicalisation; PD-2 REAP_GRACE_S=1.0 and a six-field runner result; PD-3 no case-sensitive runner exists, AC-1.10 fails never skips; PD-4 committed probe T0/T9; PD-5 leaf-symlink tools need a live measurement. Opens OQ-P1 (an existing directory the primitive cannot open). Readings at 5e3a8238.
- v1.1: Revision (2026-09-29) against spec v1.2 (e26466a8). OQ-P1 closed (operator: refuse; spec FR-3 arm 2, AC-3.6): G-3 and FR-3 carry both arms, T1 gains the arm-2 guard with no spelling fallback, AC-3.6 owned by T2/T3 (gate halves), scratch reading of AC-3.6's unfixed observables at e26466a8 equals the spec's expected column. PD-5 closed as measured (Edit refused on Claude Code 2.1.284; MultiEdit/NotebookEdit absent, unmeasurable); T0 enters it as manual rows only. T0 gains the OQ-P1 cells under both states. T8 states AC-7.1's 19 guard rows (18 at spec v1.0) with the counting command, as a floor on mutations. FR-5 aligned to spec: REAP_GRACE_S = 1.0, six-field NamedTuple with reap_failed, AC-5.1 < 4.0 s, AC-5.2 unpacking only in test_run_bounded_kills_the_process_group. Next Steps owe the design the canonicaliser's operations and the Claude gate's arm-2 transport.
- v1.2: Revision (2026-09-29) answering plan audit cycle 1 (docs/01-plan/features/tdd-gate-fail-opens.plan.audit.v1.p1.md, codex: 5 must, 1 should; tdd-gate-fail-opens.plan.audit.v1.agy.md, agy: 1 must, a duplicate of codex must 4; both at 983c2f85) against spec v1.2 (e26466a8). M1: G-1 and T3 keep the Claude gate's outside-root M:H20 dual check (canonical target AND raw spelling, spec FR-1 step 7); new pinned outside-root symlink control (R-3), which the re-derived H20B mutation must turn red. M2: T6 asserts equal kinds wherever both gates deny and a published expectation table carrying each cell's decision and kind. M3: no committed artifact invokes an agent CLI (constructed PATH, REPRO agent-cli-reachable=no); the Codex-writes column and trim set become the manual dated reading R-4; residual stated; spec Assumptions wording owed by the spec. M4: every behavioural premise carries its runnable command; new section Reproduction commands with R-1 (F_GETPATH, now also measured on 3.9.6), R-2 (gate cells and AC-3.6), R-3 (M:H20 cells), R-4 (manual apply_patch), R-5 (PD-5 procedure verbatim); premises re-run at 983c2f85; def hermetic_env is defined in two files, not one. M5: the spec table's pointer names T0's unfixed reading; T9's fixed reading is cited separately. S1: mutation floor 20 (16 parentheticals + 3 separate-mutation pairs + 1 in-each-gate), per-guard census remains the acceptance check.
- v1.3: Propagation (2026-09-29) of spec v1.3 (766860ba), which added AC-1.11 (the outside-root M:H20 symlink control, plan R-3). FR-1 cites ACs 1.1-1.11; T3's AC column adds 1.11; every R-3 and H20B citation names AC-1.11 (T0, T3, the verdict-change rule, the Verified-premises R-3 row, the Risks row, Success Criteria, R-3 itself). H20B kills only on the fixed tree: on the unfixed tree TARGET_PATH is only normpath'd, so a mutation run before T3 reports H20B SURVIVED legitimately (spec AC-1.11, measured at 4192ad8c); it is scored after T3. AC-7.1 has no H20 row and none is added; the T8 floor stays 20. Next Steps item 4 records that spec v1.3 answered both owed items.
- v1.4: Corrective revision, not re-audited (2026-09-29), after plan audit cycle 2, the second and final gating round: docs/01-plan/features/tdd-gate-fail-opens.plan.audit.v2.p1.md (codex: 4 must) and docs/03-analysis/tdd-gate-fail-opens.plan-audit-c2-agy-unscored.md (agy: 2 must), against spec v1.4 (644f8bf6). codex #1: PD-4 adds the leaf-symlink ALLOW cell (R-6 reading at 644f8bf6: step5 Claude deny no-test-resolved, Codex allow) and the FR-8 gate cells to the corpus, and a committed compare_readings.py (T0 with two run controls, T9 must print COMPARE: PASS softened=6 approved=6) that fails on any softened key outside an approved set of six: FR-1's three plus FR-8's two (announced override of the brief's three). codex #2: T6 adopts spec v1.4's two-clause domain rule and resolved-prefix definition; M-12, M-13 (both cases), M-14 and M-18 stay, judge-error in both gates under step5. codex #3: R-4 publishes the driver script, every case's patch, and its observed output on codex-cli 0.158.0 (2026-09-29T07:58:57Z): every str.isspace code point but U+000A plus U+200B and U+FEFF, leading and trailing; M-15 CRLF, M-16, M-17, M-19, M-20, M-22, M-23, interior U+0001, leaf symlink. codex #4: R-5 records the exact Edit tool input and response and says it is a tool call, not replayable. agy #1: hard-link contract, the canonicaliser returns every same-inode name and each gate tests every name; the encoding is owed by the design. agy #2: T6 asserts notes.md, tests/test_x.py, sub/test_x.PY. Spec v1.4 owed items: T10 (script flag and build_parser), T11 (safe-list entry), T12 (adapters), T0 FR-8 cells, T7 lists the adapters; T8 floor 20 -> 25 (21 + 3 + 1 at 644f8bf6); FR-8 verified premises at 644f8bf6; Risks carry the h_mad_state_write residual.
- v1.5: Propagation (2026-09-30) of the operator decision recorded in spec v1.5, design v1.3 and impl-plan v1.3: the Codex-gate key M-18 M-14 under step3 (unfixed decision=deny kind=judge-error, fixed decision=allow kind=-) joins the approved deny-to-allow set, which becomes seven. PD-4's approved-set list and its count sentence, the T9 task row, the 'Verdict changes are named' bullet, the canonicalisation Risks row and the T9 Success Criterion now read seven / COMPARE: PASS softened=7 approved=7, matching the committed docs/03-analysis/probes/tdd-gate-fail-opens/compare-fixed.txt at 196f4d70. Nothing else changes; earlier Version History entries stay historical.
