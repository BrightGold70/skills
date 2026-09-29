# Design: tdd-gate-fail-opens

## Executive Summary

Both TDD gates decide a write from one stdlib canonicaliser, `canonicalise`, in a new module
`h-mad/scripts/h_mad_target_identity.py`. The Codex gate calls it in-process. The Claude gate
receives one percent-encoded record from the single `python3` invocation that today computes
`TARGET_PATH` (`# M:H11`), and that same invocation also replaces the `pwd -P` that computes
`ROOT_ABS`. The record carries every hard-link name of the leaf, one unresolvable flag for both
FR-3 arms, and the spelled component. Each gate then applies its own exemptions to every name.
A governed unresolvable target, a governed bad `apply_patch` header, and a judge reap that
outlives `REAP_GRACE_S` all refuse `judge-error` or `judge-timeout`. The resume oracle is admitted
by a new safe-list key and by `--session-id-from-git-dir`, which reads the minted id before
`decide`.

## Overview

Spec v1.4 (644f8bf6) states what the gates decide. Plan v1.4 (1254595a) states the order, PD-1
through PD-5, and the items this design owes: where the canonicaliser lives, which components it
opens or lists, how the Claude gate hears arm 2, how the hard-link name list is encoded and where
each gate loops, where the git-dir read sits relative to `decide` and what the 10 s constant is
called, and the `REPRO:` grammar `compare_readings.py` parses. This document decides those and
names the functions each task rewrites. Behavioural re-derivation of the M-cells stays in the
probe T0 commits. This document states the structural census it re-ran, once, in §"Verified
premises".

The class is path identity. A gate that still decides from a spelling, on any component the
canonicaliser has already resolved, is the same defect as D1, D3, and D4. The residual is a
second identity function: any later `pwd -P`, `os.path.realpath`, or `Path.resolve` on a root,
payload cwd, or write target that this design routes through `canonical_directory` or
`canonicalise`. The `# M:H8` walk is the one `pwd -P` that stays, and it stays because it runs
on an already-canonical path.

## Architecture

```
h_mad_target_identity.canonicalise(root, target, cwd=None) -> Identity
  canonical_directory  on the root, on the Codex payload cwd, and on the
                        deepest existing directory of the target
                        (fcntl F_GETPATH of an O_RDONLY fd; OSError propagates)
  os.lstat / os.stat    component walk (arm 1: lstat succeeds, stat raises)
  scandir               only the leaf's canonical parent, and only when the leaf exists
  fold_py_suffix        four ASCII suffixes, shared tuple PY_SUFFIXES

Claude hook  h-mad-tdd-gate.sh
  one python3 -c  (# M:H11 stays on this call) -> emit_canon record
  _read_canon     the only reader
  _fold_py        the same four literals, applied once per name
  per-name loops  basename case (# M:H6), suffix-allow case, non-.py test
  exemptions and judge then see the canonical root and the chosen target

Codex hook  h-mad-codex-tdd-gate.py
  _load_identity  in-process, same layout as _load_judge
  _project_root   selected path through canonical_directory (four returns)
  payload cwd     canonical_directory before _payload_cwd_base
  _relative_target  Identity, or None only when resolvable and outside the root
  _patch_header_paths  header grammar; bad header does not raise into # M:G2
  per-name any()  inside the existing `for raw in targets` (# M:G5)

Judge  h_mad_tdd_judge.py
  realpath sites stay (FR-1 step 8 makes them identities)
  _run_bounded -> BoundedRun, sixth field reap_failed
  REAP_GRACE_S = 1.0; judge-timeout first in the priority tuple

Resume  h_mad_resume_decision.py
  build_parser(); git-dir read under GIT_DIR_BOUND_S before decide()
```

Rejected placements, each for a reason already visible in the tree:

- Inside `h_mad_tdd_judge.py`. The judge's `os.path.realpath` calls must stay identities
  (FR-1 step 8). Importing the judge into the Claude hook's one-shot process would also pull
  the judge into a call whose only job is identity.
- `chdir` plus `getcwd`. `_project_root` reads `os.getcwd()` as the third candidate in its
  selection loop and returns `Path.cwd().resolve()` when that loop finds no directory.
  `_payload_cwd_base` joins a relative target to that base. A process-global cwd change moves
  all three.
- `os.path.ALLOW_MISSING` and `os.O_SEARCH` as the open. PD-1's R-1 reading is the authority
  for their absence on the suite interpreter; T0's probe re-derives that row. This design does
  not use either.
- A second arm flag on the Claude record. The gate would then have two channels for one
  predicate. Arm number travels in the reason text.
- Base64 for the name list. The hook already decodes percent-escapes with `_pct_decode`. A
  base64 decoder would be a second grammar, and a `base64` CLI would be a second process or a
  macOS/GNU flag split. Percent-encoding carries every directory-entry byte except NUL.

## Detailed Design

### Canonicaliser

New module `h-mad/scripts/h_mad_target_identity.py`. Stdlib only (`os`, `fcntl`, `stat`).

`canonical_directory(path: str) -> str` opens `path` with `os.open(path, os.O_RDONLY)`, calls
`fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024))`, decodes, and `rstrip`s trailing NULs. The fd
is closed on every path. `OSError` propagates, including an absent `F_GETPATH` attribute only
after the fallback below. When `fcntl.F_GETPATH` is absent, the function returns
`os.path.realpath(path)` and keeps the spelling realpath produced. That fallback has no test
in this feature (PD-3: no Linux runner). The residual is a Linux host whose realpath spelling
disagrees with a future F_GETPATH reading; adding a Linux runner is a spec amendment, and a
skip is not the stand-in.

`canonicalise(root: str, target: str, cwd: str | None = None) -> Identity` is the walk. It
calls `canonical_directory` for the root, for `cwd` when `cwd` is a non-empty string, and for
the deepest existing directory of the target. It lists only the leaf's canonical parent.

`Identity` is a `NamedTuple` with fields `root`, `target`, `prefix`, `names`, `unresolvable`,
`arm`, `component`. `names` is a `tuple` of `str`. `unresolvable` is `bool`. `arm` is `0`, `1`,
or `2`. `component` is the spelled component that failed, or empty.

`PY_SUFFIXES = (".py", ".pY", ".Py", ".PY")`. `fold_py_suffix(name: str) -> str` replaces a
trailing member of that tuple with `.py` and leaves the stem byte-for-byte. It does not call
`str.casefold`. The residual is a fifth spelling that case-folds to `.py`; the spec's fold is
these four, and AC-2.2 runs both gates. The Claude gate cannot call this function (its one
Python process is the canonicaliser call), so the bash function `_fold_py` contains the same
four literals. The equivalence test imports `PY_SUFFIXES` and reads the body of `_fold_py`, and
fails when the two lists differ. A fold written inline at a call site, outside `_fold_py`, is
the residual that test must also reject: the test fails if the basename case, the suffix-allow
case, or the non-`.py` test runs on a name `_fold_py` has not already folded.

`emit_canon(identity: Identity) -> None` prints the record below. It is the only emitter.

### Which component is opened, listed, or neither

Arm 1 is the walk predicate: `os.lstat` succeeds and `os.stat` raises (dangling symlink, loop,
or any other `OSError` from `stat`). An `OSError` from `lstat` means the component is absent;
the walk splits the remainder there and does not treat it as arm 2. That is the spec's
`os.path.lexists` true and `os.path.exists` false, implemented with `lstat` and `stat` so the
same `stat` result supplies `st_dev` and `st_ino`.

Arm 2 is an `OSError` from an operation this function actually performs: `canonical_directory`
on the root, on the payload cwd, or on the deepest existing directory of the target, or the
listing of the leaf's canonical parent. There is no spelling fallback (OQ-P1 closed).

| Component | Opened with F_GETPATH | Listed with scandir |
|---|---|---|
| Root directory | yes | no |
| Intermediate ancestor of the target | no; the deepest existing directory's F_GETPATH returns the on-disk path of the whole prefix | no |
| Deepest existing directory | yes | only when that directory is the leaf's parent |
| Leaf's parent, leaf exists | yes (it is the deepest existing directory) | yes, inode match |
| Leaf file | no | no |
| Absent remainder after the walk stops | no | no |
| Codex payload cwd | yes, before `_payload_cwd_base` | no |

An unreadable ancestor that still has an openable descendant is not an arm-2 site: the open
is the descendant, and F_GETPATH on that descendant returns the ancestor's on-disk spelling.
The leaf file is never the fd passed to F_GETPATH. One path from the leaf misses sibling
hard-link names, and PD-1's R-1 row shows F_GETPATH succeeding on a readable child of a
mode-`0311` directory, which would miss AC-3.6 (b).

AC-3.6 (a): absent `tests/newmod.py` under on-disk `Tests/` at mode `0311`. The deepest
existing directory is `Tests/`, the open fails, arm 2. AC-3.6 (b): `src/` at mode `0311` with
existing `src/prod.py`. The parent is both opened and listed; either `OSError` is arm 2.

A leaf symlink is followed (every symlink on the walk is followed). The names returned are the
referent's names in the referent's canonical parent. FR-1's referent rule stands (PD-5).

For an existing leaf, `names` is every directory entry of the canonical parent whose
`(st_dev, st_ino)` equals the leaf's, sorted lexicographically, at least one. The canonicaliser
does not evaluate an exemption. For an absent leaf, `names` is the one spelled leaf name
(FR-1 step 5). `target` on a resolvable result is the canonical parent joined with the
lexicographically first returned name. The gate later chooses the judge path itself.

### Claude record and the one call

The call runs unconditionally, including when the spelled target is empty, because `# M:H13`
still needs a root: `_read_state` refuses when `ROOT_ABS` is empty. `RAW_TARGET=$TARGET_PATH`
stays where it is, immediately before today's `ROOT_ABS` assignment, so the raw spelling is
saved before the call.

The invocation replaces both the `ROOT_ABS=$(cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null && pwd -P)` assignment and the `# M:H11` `os.path.normpath`
call. The marker `# M:H11` stays on the replacement, and the mutation object named `H11` is
re-derived onto that new text at the same guard. The `-c` program resolves its own script path
the way `# M:W6` resolves `BASH_SOURCE` (`os.path.realpath` of the hook path, then `scripts/`
on `sys.path`), imports the new module, calls `canonicalise`, and calls `emit_canon`. The JSON
reader `python3 -c "$READER"` (`# M:H1`, `# M:H12`, `# M:H2`) stays. The feature adds no Python
process: this call replaces the existing `# M:H11` process and absorbs the root computation.

`test_trap_member_refuses_in_form` installs a `python3` shim whose argument match is
`*os.path.realpath*` and then `exit 3`. The `# M:W6` locator already contains that string, and
the test already expects deny `judge-error` (the EXIT trap `# M:T2`). The new call does not
swallow a non-zero status with `||`.

The record is one physical line per field, in this order:

```
CANON 1
root <pct>
target <pct>
prefix <pct>
unresolvable yes|no
arm 0|1|2
component <pct>
names <decimal>
name <pct>
```

`name` repeats exactly `names` times. Percent-encoding uses the existing `_pct_decode`:
`[ "$1" = % ] && return 0; printf '%b' "${1//%/\\x}"`. Every byte outside ASCII alphanumeric
plus `/`, `-`, `.`, and `_` is encoded as `%HH`, so each field is one physical line. Newline
is `%0A`, space is `%20`, `%` is `%25`. NUL is not a directory-entry byte and is not emitted
(`\0` would truncate `printf %b`). The decoder is this one function. A second decoder is a
second grammar for the same list.

`_read_canon` is the only reader. Unparseable is `judge-error` with no spelled-leaf fallback:
unknown key, missing key, a second `CANON` header, a version other than `1`, `arm` outside
`0|1|2`, `unresolvable` outside `yes|no`, `names` not a non-negative integer, a name-line count
that disagrees with `names`, or a `%` not followed by two hex digits. The residual is a second
parser, which would be a second channel for the same flag.

Resolvable record: `unresolvable=no`, `arm=0`, `component` empty, `names` at least 1, `prefix`
equal to the canonical root. Unresolvable record: `unresolvable=yes`, `arm` `1` or `2`,
`names=0`, no `name` lines, `target` empty, `component` the spelled component's bytes,
`prefix` the resolved prefix (the longest prefix step 2 walked before the predicate). Empty
spelled target: `unresolvable=no`, `names=0`, `target` empty, `root` set. That record parses,
and the existing `# M:H13` refusal then fires on the empty spelled target. A call that prints
no parseable record is `judge-error` on that path too, which is stricter than today's
`ROOT_ABS=""` continuation and matches the trap.

Bash order after a parsed record:

1. Parse failure: `_refuse judge-error`, unconditional.
2. Empty spelled target: existing `# M:H13`.
3. `unresolvable=yes`: `_chain_may_hold_state` and `_read_state` run on `prefix`. Governed
   (chain `active` or unreadable) refuses `judge-error` with reason
   `unresolvable arm=<N> component=<decoded component>`. Not governed: `_allow`. The gate
   branches only on `unresolvable`. `arm` is inside the reason, which is what AC-3.6 reads.
   The flag is not a verdict; governed versus not stays the bash decision. `TDD-STATE: none`
   is unchanged.
4. Resolvable: per-name loops, then the rest of the hook unchanged. `_chain_may_hold_state`
   runs on the canonical target.

A protocol or crash failure is always `judge-error`. FR-3's unresolvable predicate is
governed-only. Those are different properties of the gate.

After T3, `grep 'pwd -P' h-mad/hooks/h-mad-tdd-gate.sh` may match only the `# M:H8` walk:
`d=$(dirname "$target"); while [ ! -e "$d" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; d=$(cd "$d" 2>/dev/null && pwd -P) || return 0  # M:H8`.
That walk runs on the canonical target, or on the resolved prefix when unresolvable, where
`pwd -P` is the identity. The `# M:H8` line stays byte-identical, so its mutation find stays.
The residual: the locator is the `# M:H8` comment. A second `pwd -P` means the one-canonicaliser
rule is broken.

### Claude per-name loops

Allow only when every returned name allows. The loops, each over every name after `_fold_py`:

- The basename case whose marker is `# M:H6`, today `case "${TARGET_PATH##*/}" in` with
  patterns `test_*.py|*_test.py|conftest*.py`. The line changes to open the per-name test; the
  marker stays on that `case`. The one mutation object named `H6` is re-derived onto the new
  text at the same guard. A name matches when its folded basename matches. The write is exempt
  here only when every name matches.
- The suffix-allow `case` that has no marker, patterns
  `*.md|*.yaml|*.yml|*.json|*.toml|*.txt|*.rst|*.cfg|*.ini` and
  `*.sh|*.bash|Makefile|Dockerfile|*.dockerignore|*.gitignore`. The locator is that `case`, the
  one that is not the basename case. Every name must match, or one production alias slips
  through an exempt alias.
- `[[ "$TARGET_PATH" != *.py ]] && _allow`, after the fold. Every folded name must be non-`.py`.

When any name is a production `.py`, `TARGET_PATH` becomes the canonical parent joined with
the lexicographically first name for which the production test holds, and the hook continues.
The judge invocation `# M:W2`, `_read_state --target "$TARGET_PATH"  # M:H3`, and the rc split
`# M:H16` keep their text because they read `TARGET_PATH`. If an implementer rewrites those
lines, the mutation finds are re-derived at the same guard. Today two objects (`W2R`, `W2F`)
share the `# M:W2` find.

Directory exemptions stay single-parent. `# M:H19` uses the canonical path and stays
byte-identical, as does `_dir_match` (`# M:H15`). Two objects (`H15`, `H15B`) share that find.
`# M:H18` and `R=${ROOT_ABS%/}` stay once `ROOT_ABS` and `TARGET_PATH` are the canonical
values. Two objects (`H18`, `H18B`) share the `# M:H18` find.

`# M:H20` keeps both conjuncts:
`elif _dir_match "$TARGET_PATH" && _dir_match "$RAW_TARGET"; then  # M:H20`.
`H20A` and `H20B` share that find. `H20B`'s replace drops the `RAW_TARGET` conjunct. Keeping
the line byte-identical leaves both finds valid. `TARGET_PATH` is already canonical and
`RAW_TARGET` is still the raw spelling, so the conjuncts mean what FR-1 step 7 requires.
Score `H20B` only after T3. On the unfixed tree `TARGET_PATH` is only `normpath`'d, so `H20B`
does not move the cell (spec AC-1.11). AC-7.1 has no H20 row; the floor does not gain one.
The existing nodes are
`test_outside_root_exemption_needs_both_spellings[dotdot-relative]` (`H20B`) and
`[traversal-absolute]` (`H20A`).

### Codex call sites

`_load_identity` mirrors `_load_judge`: `Path(__file__).resolve().parents[1] / "scripts"`,
insert on `sys.path` if absent, `import_module("h_mad_target_identity")`.

`_project_root` keeps today's selection: `CODEX_PROJECT_DIR` when that path is a directory;
otherwise each of payload `project_dir`, payload `cwd`, and `os.getcwd()`, and for a directory
candidate `git -C <path> rev-parse --show-toplevel` or that candidate; otherwise
`Path.cwd().resolve()`. Each of the four `return` sites passes the selected path through
`canonical_directory` instead of `Path.resolve()` or `Path.cwd().resolve()`. Those four returns carry no `# M:` marker. An
`OSError` leaves the root unresolvable. `_main_guarded` catches that `OSError` inside the
function so it does not reach `# M:G2` (which judge-errors even when not governed). It then
runs `_any_phase5_status` on the spelled path; if that scan raises `OSError`, the status is
`unknown`. `active` and `unknown` refuse `judge-error` naming the spelled root. `inactive`
allows.

The payload cwd is passed through `canonical_directory` before `_payload_cwd_base` tests
containment. An `OSError` is the same unresolvable result, reason naming the cwd, and
`_payload_cwd_base` is not called. On success the caller passes the already-canonical cwd, so
the function body stays byte-identical: `if isinstance(cwd, str) and cwd:  # M:G1` and the
containment line `# M:G7`. The remaining `.resolve()` is a spelling-preserving identity. The
object named `G1` keeps that find. The object named `G10` is a different marker, on
`_contained_venv_executable`'s `os.path.normpath` line, and that line stays. The plan's forecast
counted `"M:G1" in find`, which also matches `# M:G10`; this design names the two objects
instead of that substring count. If a later edit removes `.resolve()` from `_payload_cwd_base`,
re-derive `G7` and check `G1`.

`_relative_target` today returns `tuple[Path, str] | None`, and `None` means outside. It
changes to `Identity | None`. `None` only when the result is resolvable and the canonical
target is outside the root. An unresolvable `Identity` is returned so the caller can refuse
`judge-error` when `phase5_status` is `active` or `unknown`, and skip the target when not
governed. Collapsing unresolvable into `None` would deny with the existing outside-root
message and drop the component name AC-3.6 requires. The resolvable inside-root caller runs
`_is_production_python` on every name.

The only production unpack of `_targets` is `_main_guarded`'s
`tool, targets, command = _targets(payload)`. Other `_targets` hits in the tree are different
symbols (`ast_targets`, and the test name `test_relative_targets`). T4 extends the return.

Inside `_main_guarded`, `for raw in targets:  # M:G5` stays byte-identical, so the object
named `G5` is not re-derived. The unmarked `if` under it becomes: the target is production
when any leaf name returns true from `_is_production_python` on `parent_rel + "/" + name`.
Directory parts are shared (`"tests"` and `"fixtures"` not in `path.parts`), so a `tests/`
parent exempts every name. `fold_py_suffix` runs inside `_is_production_python` before the
suffix test and the basename tests; the stem stays case-sensitive. That is the fold on every
name.

`verdict = judge.judge(root, absolute, chain.records)  # M:W1` stays when `absolute` is the
chosen path: canonical parent joined with the lexicographically first name for which the
production test holds. `W1R` and `W1F` share that find. `chain = judge.read_chain(root, absolute)  # M:W5A`
stays on the resolvable path (`W5AR`, `W5AF`). Codex governance for FR-3 uses
`_any_phase5_status(root)`, already computed before the loop, not `read_chain` of the target.
Claude governance stays the chain verdict of the `state` verb.

`Path.resolve` that stays, because its inputs are not the write-target identity this feature
moves: `_trusted_executable`, `_path_within`, `_contained_venv_executable` and the judge's
`venv_contained` (`# M:G6`, `# M:V1`, `# M:V2`), the `hmad-dispatch` identity compare, and
`script.resolve()` inside `_safe_shell_command`. `Path.resolve` / `canonical_directory` that
moves: the four returns of `_project_root`, the payload cwd before `_payload_cwd_base`, and
`_relative_target`'s resolve of the joined target.

Judge `os.path.realpath` that stays, by function: `read_chain` (root and `target.parent`),
`_display`, `resolve` (root, target, and the name-map mapped path), `venv_contained`,
`select_interpreter`, and `main`'s `args.root`. FR-1 step 8 makes them identities once the
gates pass canonical paths.

### Header grammar

`_patch_header_paths(patch: str)` replaces `PATCH_TARGET.findall`. `_targets` calls it for
`apply_patch`. The current constant is
`re.compile(r"^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+)$", re.MULTILINE)`.
After T4 the constant is gone and both `_targets` and `--self-check` call the function, so
there is one grammar.

Split on `\n` only (`str.split`, not `str.splitlines`). Trim both ends with characters for
which `str.isspace()` is true and the code point is outside U+001C–U+001F. Exact markers, one
space after `***` and one space after the colon: `*** Add File: `, `*** Update File: `,
`*** Delete File: `, `*** Move to: `. A path that is empty after trim, or that still contains
a byte in U+0000–U+001F or DEL U+007F, is a bad header.

The return is a `NamedTuple` `TargetParse` with `tool`, `paths`, `command`, `bad_header`.
Only `_main_guarded` unpacks it. A bad header does not raise. `# M:G2` (`except Exception` in
`main`) judge-errors even when not governed, so a raise would refuse a patch the spec says is
decided as today when no state governs it. When `phase5_status` is `active` or `unknown`, one
bad header refuses the whole patch with `judge-error` before resolution, and the reason names
the header. When the status is `inactive`, the bad header contributes no target and the other
headers are decided as today.

`--self-check` gains a trailing-space case and an indented-header case, each yielding
`src/prod.py`, and still prints `CODEX-TDD-GATE: PASS`. AC-4.7: with the trailing trim removed,
the same self-check prints `CODEX-TDD-GATE: FAIL parser`. The code points are the ones R-4
recorded on codex-cli 0.158.0. Tests drive the gate. No committed artifact invokes `codex`.

### Judge reap

`REAP_GRACE_S = 1.0` in `h_mad_tdd_judge.py`. Do not reuse `DRAIN_SECONDS`. The shape to follow
is the block in `h_mad_doc_block_exec.py`. The shape is `proc.communicate(timeout=REAP_GRACE_S)` after `killpg`, and on
`subprocess.TimeoutExpired` close `stdout` and `stderr`. `reap_failed` becomes true.
`timed_out` stays true for a reap failure as well. The `error` field stays "Popen raised"
(`f"{type(exc).__name__}: {exc}"` on the `OSError` return). Encoding the reap in `error` would
give that field two meanings and would move the `# M:K3` line.

`_run_bounded` returns `BoundedRun`, a `NamedTuple` whose fields are today's five in today's
order plus `reap_failed: bool`: `returncode`, `out`, `err`, `timed_out`, `error`,
`reap_failed`. Today's signature is
`_run_bounded(argv: Sequence[str], cwd: Path, deadline: float) -> Tuple[Optional[int], str, str, bool, str]`.
On `TimeoutExpired` it `killpg`s `SIGKILL` (ignoring `ProcessLookupError`) and then calls the
bounded `communicate`. A process-group kill with no detached descendant reports
`timed_out=True`, `reap_failed=False`.

The two production unpacks, in `resolve` (the name-map run) and in `judge` (the pytest run),
read `reap_failed` before the `# M:K3` assignment
`kind = "no-summary" if error else score(out + "\n" + err, timed_out)  # M:K3`.
A true `reap_failed` sets the outcome kind to `judge-timeout` and does not change that line,
so the finds of `K3` and `K3B` stay. The third unpack is
`test_run_bounded_kills_the_process_group` in `h-mad/tests/test_h_mad_tdd_judge.py`, which
moves to the six-field result. `test_name_map_runs_under_the_budget` calls `judge.judge` and
does not unpack. The existing `< 6.0 s` assertions in those two tests and in `test_timeout_kind`
keep their bound. No mutation spec's find contains `_run_bounded`.

`judge-timeout` is inserted first in the priority tuple that today is
`("timeout", "pytest-missing", "pytest-error", "no-summary", "no-tests-ran", "test-passing")`,
and a `judge-timeout` outcome stops further runs (the same `break` set that today holds
`venv-escapes-root`, `timeout`, and `pytest-missing`). `KINDS` gains the token. `JUDGE_DENY_RE`
in the Claude hook gains `judge-timeout` as one more alternative in the `kind=(…)` group.
`test_claude_gate_kind` and `test_codex_gate_kind` each gain a `judge-timeout` row. AC-5.1's
bound is 4.0 s. Worst case for a governed write is `JUDGE_BUDGET_S` (40.0) plus
`REAP_GRACE_S` plus process start.

### FR-8 git-dir read

`h_mad_resume_decision.py` has no `build_parser`. `ArgumentParser` is constructed inside
`main`, with five `add_argument` calls: `--state`, `--feature`, `--host`, `--session-id`,
`--now`. `decide` calls `_host_verdict` first. A missing id passed as `None` on `--host claude`
returns `None` from `_host_verdict` and can print `enter_autonomous` once
`last_completed_phase >= 4`. That is why the flag's failure modes must not call `decide`.

T10 adds a module-level `build_parser()` that `main` calls. `--session-id-from-git-dir` sits in
one argparse mutually exclusive group with `--session-id`. With the flag, `main` calls
`session_id_from_git_dir(feature)` and passes the stripped id as `session_id`. The read happens
before `decide`. Any failure prints `cannot_judge` and does not call `decide`.

`GIT_DIR_BOUND_S = 10.0` is the module-level constant. It is not `REAP_GRACE_S` and not
`DRAIN_SECONDS`. The bound is `subprocess.run(["git", "rev-parse", "--absolute-git-dir"], timeout=GIT_DIR_BOUND_S, capture_output=True, text=True)`.
`subprocess.TimeoutExpired` is the bound-expired branch. The `timeout` and `gtimeout` CLIs are
not used (§"Portable time bounds"). The script is already Python, so the bounder it can enforce
without a second CLI is the stdlib `timeout` argument. A linked worktree's
`git rev-parse --absolute-git-dir` returns that worktree's git dir (AC-8.3).

The six failure branches, each its own arm: `git` absent from `PATH`; non-zero git exit,
including a cwd outside any repository; the bound expiring; the id file absent; the id file
raising `OSError`; the id empty after stripping. Usage with both flags is argparse exit 2,
empty stdout, and stderr containing the substring `not allowed with argument` (AC-8.5). This
design does not freeze a longer argparse phrase.

`_safe_shell_command("git rev-parse --absolute-git-dir", ".", ".")` is false.
`READ_ONLY_COMMANDS` is `{cat, grep, head, jq, ls, pwd, shasum, tail, wc}` and does not contain
`git`. `SAFE_DISPATCH_VERBS` has no git verb. The oracle is admitted as a script key, not as a
shell pipeline.

`SAFE_HMAD_SCRIPT_OPTIONS` today has these keys: `h_mad_assemble_tdd.py`,
`h_mad_baseline_sha.py`, `h_mad_context_budget.py`, `h_mad_do_preconditions.py`,
`h_mad_extract_verdict.py`, `h_mad_identifier_sweep.py`, `h_mad_state_validate.py`,
`h_mad_state_write.py`, `h_mad_wire_pin_gate.py`, `h_mad_wire_registry.py`. T11 adds
`h_mad_resume_decision.py` whose value is exactly the parser's long options minus `--help`:
`--state`, `--feature`, `--host`, `--session-id`, `--now`, `--session-id-from-git-dir`.
`_safe_hmad_script` gains no per-script value check. An unknown script returns false before the
per-script branches. The resume key falls through to the closing `return True`. Per-script
branches stay only for `h_mad_state_write.py`, `h_mad_wire_pin_gate.py`,
`h_mad_wire_registry.py`, and `h_mad_assemble_tdd.py`. AC-8.2's test derives the set from
`build_parser()`, reading each action's `option_strings`, and never types the set. The vehicle
for AC-8.1 is `test_codex_hook_allows_exact_safe_hmad_control_script` in
`h-mad/tests/test_h_mad_codex_runtime.py`.

### REPRO line grammar

`compare_readings.py` keys a line only when it matches the gate grammar. One physical line:

`REPRO: cell=<cell> gate=<claude|codex> state=<step5|step3> decision=<allow|deny> kind=<kind>`

Field order is fixed. A value runs until the next field name and may contain spaces, which is
how `FR-8 literal-uuid` stays one cell token. `kind` is the rest of the line: a judge kind, or
a single `-` when the decision is allow and the gate printed no kind. The state token is
`step5` or `step3`. The plan's phrase "step3-only" is the prose name of `step3`, not the key.
A key is the triple `(cell, gate, state)`.

Gate cell tokens include `M-1` through `M-23`, `leaf-symlink`, and the three FR-8 forms
`FR-8 cat-subst`, `FR-8 literal-uuid`, and `FR-8 flag`. `FR-8 cat-subst` is printed and stays
deny; a reading that drops it fails the missing-key rule.

The approved softening set, deny to allow only, is this table. A kind change on a deny is
printed and is not a softening.

| cell | gate | state |
|---|---|---|
| `M-10` | claude | step5 |
| `M-10` | codex | step5 |
| `M-11` | claude | step5 |
| `leaf-symlink` | claude | step5 |
| `FR-8 literal-uuid` | codex | step5 |
| `FR-8 flag` | codex | step5 |

Anything else that moves deny to allow is a failure. The comparator exits non-zero when a key
is present in one reading and absent from the other, or when a deny-to-allow key is outside
that table. It prints `COMPARE: PASS softened=N approved=N` or `COMPARE: FAIL`. T0's
self-comparison is `PASS softened=0`. T0's injected unapproved key is `FAIL`. T9 is
`COMPARE: PASS softened=6 approved=6`.

Lines that are not gate keys use a different first field, so a missing primitive row cannot
hide inside a gate-key check and a primitive row cannot be required to carry `gate=`:

- `REPRO: family=primitive` for each PD-1 primitive row.
- `REPRO: family=oq-p1` for each OQ-P1 cell.
- `REPRO: family=d5` for the D5 reading.
- `REPRO: agent-cli-reachable=yes|no` as its own line. The comparator does not treat it as a
  gate key. A reading is valid only when the value is `no`.

Manual R-4 and R-5 rows are lines beginning `MANUAL:`, entered by hand, and they do not match
the gate grammar. The residual is a hand row written as a `REPRO:` gate line: it would become
a key, and a one-sided key fails the comparison. The `MANUAL:` prefix is what keeps the hand
rows out of the key space.

The probe and every new test spawn subprocesses with a constructed `PATH`: a private `bin/`
(`python3` → `sys.executable`, `dirname`, `basename`, `jq`) then `/usr/bin:/bin`. Where a gate's
`codex` lookup must succeed, the existing stub `_bin(…, codex=True)` stands in. No committed
artifact invokes `codex`, `agy`, or `grok`.

### Copied-hook fixtures

`_tree_b` in `h-mad/tests/test_h_mad_tdd_gate_judge.py` copies the hook with
`shutil.copyfile(HOOK, hook)` and writes a stub judge at `h_mad_tdd_judge.py`. It does not
copy a second scripts module. Callers: `test_claude_gate_kind` (the `judge-error` arm),
`test_judge_stub_is_judge_error`, `test_state_stub_is_judge_error`,
`test_refusal_sites_use_the_chosen_form`, `test_trap_member_refuses_in_form`, and
`test_symlinked_hook_runs_its_own_trees_judge` (which copies, then `link.symlink_to(hook)`,
and expects ALLOW from tree B's stub judge).

If T3's gate imports `h_mad_target_identity` from the hook's own tree and the copy lacks the
module, the import failure is `judge-error` and the symlink test's ALLOW breaks. The reviewed
delta: `_tree_b` also writes `h_mad_target_identity.py` beside the stub judge, a stub that
emits a resolvable `CANON 1` record for the spelled path (one name, `unresolvable no`), so the
gate proceeds to the stub judge. A hook whose realpath is not next to `scripts/` still refuses
`judge-error`; that is the existing `# M:W6` contract. The symlink test proves the symlinked
hook uses tree B's module.

The Codex `judge-error` arm of `test_codex_gate_kind` copies the gate with
`shutil.copyfile(CODEX_GATE, gate)` and writes `scripts/h_mad_tdd_judge.py` that raises
`ImportError`. The assertion is `kind={kind}` in the reason. The fixture leaves
`h_mad_target_identity.py` absent, so `_load_identity` fails first and `# M:G2` still maps the
exception to `kind=judge-error`. Adding a real module there would let the gate proceed to a
different verdict. The phrase `broken judge` is not what the assertion reads.

### Documentation surfaces (T7 and T12)

`codex-implementer-prompt.md`: the paragraph under the `## Context` heading that begins
`Hook:`. There is one such line. `test_h_mad_tdd_gate_docs.py` asserts
`assert len(starts) == 1, f"expected one 'Hook: ' line, found {len(starts)}"  # M:D1`,
and the mutation object named `D1` in `claude_gate_judge_wiring.json` carries that find.
T7 rewrites the resolved-identity and any-case `.py` sentences inside that same paragraph.
A second line beginning `Hook:` moves the mutation and fails the test.

`h-mad/SKILL.md`: the helper-scripts bullet is the line beginning `- \`h_mad_tdd_judge.py\` —`.
T7 adds `judge-timeout` to that bullet. Frontmatter `name: h-mad` and the description that
begins "Orchestrate the seven-phase H-MAD development workflow" stay byte-identical
(§"Skill manifest integrity").

`codex-runtime.md` §"Trust boundary" (`### Trust boundary`) gains two sentences: a reap that
fails is DENY `judge-timeout`, and a governed target the canonicaliser cannot resolve is DENY
`judge-error` naming the component. It does not gain a closed kind list. The pytest paragraph
in that section stays.

`agy-runtime.md` and `grok-runtime.md` §"The TDD gate" (`## The TDD gate`) name no judge kind.
The zero is load-bearing: those sections describe hosts that have no TDD gate of their own
(`step5:agy_tdd_hook_unverified`, `step5:grok_tdd_hook_unverified`). T7 adds no kind tokens
there. The command and the zero are in §"Verified premises". T12 still edits each adapter's
oracle line and empty-id prose under `## Context budget and claims`.

The oracle line in each of the three adapters is the one fenced `h_mad_resume_decision.py`
invocation whose `--session-id` value is the `$(cat "$(git rev-parse --absolute-git-dir)/…")`
substitution. T12 replaces that invocation with
`python3 "<HMAD_SKILL_ROOT>/scripts/h_mad_resume_decision.py" --host <host> --state docs/.bkit-memory.json --feature "<feature>" --session-id-from-git-dir`,
host spelled `codex`, `grok`, or `agy`. The five `h_mad_state_write.py` lines in the same fence
keep the `$(cat …)` substitution. FR-8 closes the oracle line only. The Claude-host line in
`h-mad/SKILL.md` (`--session-id "<this session's id>"`) stays.

Empty-id prose becomes one sentence in all three: "the oracle cannot read the id and returns
`cannot_judge`". Today the Codex and agy paragraphs begin "If the id file becomes unreadable"
and the grok paragraph begins "An unreadable id file gives the oracle an empty id".

### Verdicts that move toward ALLOW

Only these, and `compare_readings.py` is the mechanical check over the probe corpus:

- M-10, both gates, `step5`.
- M-11, Claude gate, `step5`.
- `leaf-symlink`, Claude gate, `step5`.
- `FR-8 literal-uuid` and `FR-8 flag`, Codex gate, `step5`.

`FR-8 cat-subst` stays deny. Any other existing test that changes verdict is stop-and-report.
`# M:H20`'s raw conjunct is an added condition on an ALLOW, read beside the canonical value.

### Mutation anchors

A task that rewrites a marked line re-derives every mutation object whose `find` is that line,
at the same guard, and does not delete the object. `--check-anchors` after each task is the
census. Objects and the disposition this design assigns:

| Objects | Find locator | Disposition |
|---|---|---|
| `H11` | the `# M:H11` normpath `python3 -c` | re-derive onto the replacement call |
| `H6` | `case "${TARGET_PATH##*/}" in  # M:H6` | re-derive onto the per-name case |
| `H8` | the `# M:H8` walk | byte-identical |
| `H15`, `H15B` | `_dir_match` `# M:H15` | byte-identical |
| `H18`, `H18B` | `# M:H18` | byte-identical |
| `H19` | `# M:H19` | byte-identical |
| `H20A`, `H20B` | both conjuncts `# M:H20` | byte-identical; score `H20B` after T3 |
| `W2R`, `W2F` | `# M:W2` | byte-identical while they read `TARGET_PATH` |
| `G1` | `if isinstance(cwd, str) and cwd:  # M:G1` | byte-identical |
| `G10` | `# M:G10` normpath in `_contained_venv_executable` | byte-identical; not a G1 object |
| `G5` | `for raw in targets:  # M:G5` | byte-identical |
| `G7` | the `# M:G7` containment line | byte-identical |
| `W1R`, `W1F` | `# M:W1` | byte-identical when `absolute` is the chosen path |
| `W5AR`, `W5AF` | `# M:W5A` | byte-identical on the resolvable path |
| `K3`, `K3B` | the `# M:K3` assignment | byte-identical; `reap_failed` handled above it |
| `D1` | the one-`Hook:` assertion | byte-identical; T7 edits the paragraph in place |

New guards AC-7.1 names get their own mutation objects in T8. The plan's floor command is the
acceptance check's floor; this design does not publish a second floor. The per-guard census
over the committed specs is the acceptance check.

## Components Changed / Added

| Component | File | Change |
|---|---|---|
| `canonicalise`, `canonical_directory`, `fold_py_suffix`, `emit_canon`, `Identity`, `PY_SUFFIXES` | `h-mad/scripts/h_mad_target_identity.py` | new |
| Claude gate: one call, `_read_canon`, `_fold_py`, per-name loops, `judge-timeout` in `JUDGE_DENY_RE` | `h-mad/hooks/h-mad-tdd-gate.sh` | modify |
| Codex gate: identity load, root, cwd, targets, fold, header grammar, safe-list key | `h-mad/hooks/h-mad-codex-tdd-gate.py` | modify |
| `BoundedRun`, `REAP_GRACE_S`, `judge-timeout` | `h-mad/scripts/h_mad_tdd_judge.py` | modify |
| `build_parser`, `session_id_from_git_dir`, `GIT_DIR_BOUND_S` | `h-mad/scripts/h_mad_resume_decision.py` | modify |
| Trust-boundary sentences; oracle line and empty-id prose | `h-mad/references/codex-runtime.md` | modify |
| Oracle line and empty-id prose | `h-mad/references/grok-runtime.md`, `h-mad/references/agy-runtime.md` | modify |
| `Hook:` paragraph in place; judge bullet gains `judge-timeout` | `h-mad/references/codex-implementer-prompt.md`, `h-mad/SKILL.md` | modify |
| `_tree_b` identity stub; `judge-timeout` rows; header and FR-8 tests; differential; SID control | `h-mad/tests/` | modify and new |
| Probe and comparator | `docs/03-analysis/probes/tdd-gate-fail-opens/reproduce.py`, `docs/03-analysis/probes/tdd-gate-fail-opens/compare_readings.py` | new, committed by T0 |

## Data Model / Schema Changes

No state-file schema change. The new on-wire record is the `CANON 1` text protocol between the
Claude hook and the canonicaliser. `Identity`, `BoundedRun`, and `TargetParse` are in-process
tuples. `KINDS` gains the token `judge-timeout`. The resume CLI gains one flag in a mutually
exclusive group. No new environment variable.

## API / Interface Changes

- `canonicalise(root, target, cwd=None) -> Identity` and `canonical_directory(path) -> str`.
- `emit_canon` writes the field list in §"Claude record and the one call".
- `_run_bounded` returns `BoundedRun`, with `reap_failed` added after the five values it returns today.
- `_targets` returns `TargetParse` (`bad_header` last). `_relative_target` returns
  `Identity | None`.
- `build_parser()` and `--session-id-from-git-dir`. Failures print `cannot_judge` and do not
  call `decide`.
- `SAFE_HMAD_SCRIPT_OPTIONS` gains the resume-script key.
- Judge stdout gains DENY `kind=judge-timeout`, which `JUDGE_DENY_RE` accepts.

## Error Handling Strategy

Every refusal this feature adds is fail-closed, and the exception path is specific so it does
not collapse into a broader one:

- Canonicaliser `OSError` on an operation the table marks as opened or listed becomes
  `unresolvable` arm 2. It is not caught and replaced with the spelling.
- Claude: no parseable record, or a non-zero `python3`, is `judge-error` via the existing
  trap or via `_read_canon`. The call is not wrapped in `||`.
- Codex: root, cwd, and target `OSError` are caught inside `_main_guarded` and mapped to
  `judge-error` only when governed. They do not propagate to `# M:G2`.
- A bad header is a `TargetParse.bad_header` value, not a raise, for the same reason.
- Reap failure is `judge-timeout`, distinct from `timeout` (`reap_failed=False`) and from
  `no-summary` (the `# M:K3` `error` field).
- Git-dir failures print `cannot_judge` on every host, including `--host claude`, and do not
  call `decide`. Argparse mutual exclusion stays argparse (exit 2, the AC-8.5 substring).

Governed means, for Claude, the chain verdict `active` or unreadable, and for Codex,
`_any_phase5_status` in `{active, unknown}`. FR-3 and FR-4 inherit those existing notions.

## Implementation Order

The plan's order stands. This column is the anchor set: the functions the task rewrites.

| Task | Rewrites |
|---|---|
| T0 | new `reproduce.py` and `compare_readings.py`; prints the grammar in §"REPRO line grammar"; commits the two comparator controls |
| T1 | new module: `canonical_directory`, `canonicalise`, `fold_py_suffix`, `emit_canon` |
| T2 | `_load_identity`, `_project_root` (four returns), cwd before `_payload_cwd_base`, `_relative_target`, `_is_production_python`, the body under `# M:G5`. Leaves `G1`, `G5`, `G7`, `G10`, `W1`, `W5A` finds matching |
| T3 | the one `# M:H11` call, `_read_canon`, `_fold_py`, the three per-name loops. Re-derives `H11` and `H6`. Leaves `H8`, `H15`, `H18`, `H19`, `H20`, `W2`, `H3`, `H16` finds matching. Updates `_tree_b` |
| T4 | `_patch_header_paths`, `TargetParse`, `_targets`, `--self-check`. Removes `PATCH_TARGET` |
| T5 | `REAP_GRACE_S`, `BoundedRun`, `_run_bounded`, the priority tuple, `KINDS`, `JUDGE_DENY_RE`. Leaves the `# M:K3` line matching. Unpack delta: `test_run_bounded_kills_the_process_group` |
| T6 | new differential test importing `decision` and `hermetic_env` from `h-mad/tests/tdd_gate_support.py`. The `conftest.py` fixture of the same name is a different function. Existing `test_dd7_differential_matches_the_published_cells` assertion text stays |
| T7 | the `Hook:` paragraph in place, the `h_mad_tdd_judge.py` bullet, two sentences under `### Trust boundary`. No kind tokens added under either adapter's `## The TDD gate` |
| T8 | new mutation objects for AC-7.1's guards; re-derive only the finds this table marks as rewritten |
| T9 | re-run the probe; `COMPARE: PASS softened=6 approved=6` |
| T10 | `build_parser`, the mutually exclusive flag, `session_id_from_git_dir`, `GIT_DIR_BOUND_S`, the six failure branches before `decide` |
| T11 | one new key in `SAFE_HMAD_SCRIPT_OPTIONS`; no new branch in `_safe_hmad_script` |
| T12 | three oracle lines, three empty-id sentences, and the two `test_host_runtime_docs.py` deltas plus the `SID_READ` control delta below |

T5 is independent of T1–T4. T10 is independent of T1–T9. T11 depends on T10. T12 depends on
T10 and T11. T7's adapter oracle edit is T12's; T7 re-checks the other gate sentences after
T12.

## Test Strategy

Tests are RED before the production change, under `/opt/anaconda3/bin/python`. Case-dependent
tests create `a` in the fixture directory and assert `os.path.exists("A")`. When that
precondition fails, the test fails with a message naming it. It does not skip (PD-3).

The cross-gate differential reuses `tdd_gate_support.decision` and
`tdd_gate_support.hermetic_env`. Domain is the spec's two clauses: a resolvable spelling is
in-root when its canonical target is inside the canonical root; an unresolvable spelling is
in-root when its resolved prefix is inside the canonical root. Cells are M-1 through M-14 and
M-18, plus `notes.md`, `tests/test_x.py`, and `sub/test_x.PY`, each its own row. Unresolvable
cells keep their resolved prefixes (M-12 `R/docs`, M-13 leaf `R/src`, M-13 intermediate `R`,
M-14 `R/src`, and each again under M-18). Both gates deny `judge-error` under the governing
state and allow under `step3`. The deny count is derived by the test from its expectation
table. Codex kind is parsed with `kind=([a-z-]+)`. Each assertion has its own failure message.

`test_dd7_differential_matches_the_published_cells` keeps the assertion
`assert len(observed) == 126 and observed.count("deny") == 18`. That text was one matching
line in this draft's census. The implementer re-derives it with grep before editing and does
not change it. AC-6.3 re-runs `dd7_differential.py`.

A connection test fails when the call is removed and the callee remains: Claude's one `python3`
must import the new module (the `_tree_b` stub is the fixture that makes the import observable),
and `_is_production_python` must call `fold_py_suffix` (a mutation that inlines `.py` only, and
a mutation that skips the per-name loop, each red on AC-1.9). AC-1.9's fixture is `src/prod.py`
and `src/test_prod.py` on one inode, spelled `src/test_prod.py`. Its AC-7.1 mutation makes T1
return only the spelled name.

No new test and no mutation `command` invokes an agent CLI. The constructed `PATH` is the one
in §"REPRO line grammar".

## Test Plan

| Scenario | What fails red | AC |
|---|---|---|
| Case-variant and `..`-after-symlink spellings of a governed production file | both gates allow on the unfixed tree where the spec's today-column says allow | 1.1–1.6, 1.8 |
| Canonicaliser unit: walk, F_GETPATH, inode match, lexical remainder | direct call | 1.7, 1.10 |
| `src/prod.py` and `src/test_prod.py` on one inode, spelled `src/test_prod.py` | both gates allow | 1.9 |
| Outside-root `out/lnk/x.py` with `lnk -> tests` | stays deny `no-test-resolved`; positive `out/tests/x.py` allows; `out/src/x.py` denies | 1.11 |
| `.py` / `.pY` / `.Py` / `.PY` before basename and suffix tests, both gates | AC-2.2 | 2.1–2.5 |
| Dangling, loop, and mode-`0311` open or list failure, governed | allow on the unfixed tree for AC-3.6 (a); deny `no-test-resolved` for (b) | 3.1–3.6 |
| Header trim, exact marker, control byte, empty path, `--self-check` | trailing-space header is invisible to `PATCH_TARGET` today | 4.1–4.7 |
| Reap past `REAP_GRACE_S` | `judge-timeout` within 4.0 s; plain timeout stays `timeout` | 5.1–5.5 |
| `test_claude_gate_kind` and `test_codex_gate_kind` gain `judge-timeout` | the parametrize tuples today list the eleven tokens in §"Verified premises" | 5.5 |
| Differential over the FR-6 domain | new test | 6.1–6.3 |
| `test_dd7_differential_matches_the_published_cells` | assertion text unchanged | 6.3 |
| Each AC-7.1 guard mutated alone | T8 | 7.1 |
| Safe-list key equals `build_parser()` options minus `--help` | key absent today | 8.1, 8.2 |
| Worktree git dir, hermetic `PATH` without `git`, six failure branches, `--host claude` | missing id on claude reaches `decide` | 8.3, 8.4 |
| Both flags | exit 2, stderr contains `not allowed with argument` | 8.5 |
| Oracle condition and oracle-line selection in `test_host_runtime_docs.py` | the `oracle` lambdas require `SID_READ` | 8.6 |

Reviewed deltas the spec's compatibility sentence does not list. They are decided here so
existing tests stay discriminating:

- `_tree_b` writes the resolvable identity stub. The Codex `judge-error` fixture does not.
  Without the Claude stub, `test_symlinked_hook_runs_its_own_trees_judge` flips from ALLOW to
  `judge-error` for an import failure, which is a fixture lie, not a product change.
- `test_claims_lines_execute_across_invocations` does
  `control = run(oracle.replace(SID_READ, '""'))` and asserts `cannot_judge`. After T12 the
  oracle line contains no `SID_READ`, so the replace leaves the line untouched and the control
  stops forcing an empty id. The control must still force an empty id by a means the new line
  can express: run after removing the minted file, or invoke with a feature whose id file is
  absent, and still assert `cannot_judge`. The `no-dollar-sid` case keeps `any(SID_READ in line)`
  because the five state-write lines keep the substitution. Only the oracle condition drops
  `SID_READ`.

`test_run_bounded_kills_the_process_group`, `test_name_map_runs_under_the_budget`, and
`test_timeout_kind` keep their `< 6.0 s` bounds. `--self-check` still prints
`CODEX-TDD-GATE: PASS` except inside the AC-4.7 trim-removed mutant, which prints
`CODEX-TDD-GATE: FAIL parser`.

## Invariant Compliance

**Single-source contract.** One `canonicalise` for both gates. The bash fold is a checked copy
of `PY_SUFFIXES` because the Claude gate's one Python process is already the canonicaliser
call; the equivalence test is the byte-equivalence the contract allows. One header grammar
(`_patch_header_paths`). One name-list decoder (`_pct_decode`). One arm flag.

**No new external dependency**, including **Dispatched agent CLIs are not script dependencies.**
The module is stdlib. The probe, the new tests, and every mutation `command` reach no agent
CLI. The constructed `PATH` and `REPRO: agent-cli-reachable=no` are the mechanism.

**Portable time bounds.** The git-dir bound is the stdlib `timeout` argument of
`subprocess.run`. The design does not write `timeout` or `gtimeout` as a CLI.

**Skill self-containment** and **Skill manifest integrity.** Edits stay under `h-mad/` plus the
probe directory and this document. `SKILL.md` frontmatter `name` and `description` stay
byte-identical. The helper bullet's behaviour sentence gains `judge-timeout` in the same change
that adds the kind.

**Doc-template superset compliance.** This file carries the seven required design headings and
the house sections the predecessor design carries (components, data model, API, error
handling, test strategy, invariant compliance).

**Marker discipline.** Existing `# M:` markers stay on the guards named above. New behaviour
is located by those markers and by function names. This design writes no line number.

**Mutation verification** and **Test discrimination.** Reap failure is a separate field so
`# M:K3` still discriminates `no-summary`. The empty-id control is rewritten so it still fails
when the id file is present and the flag can read it. `H20B` is scored only after T3, because
before T3 the mutant does not move the cell. Each new alternation branch gets its own mutation
(T8), run alone.

**Guard narrowing.** The ALLOW relaxations are the six rows of the approved table, checked by
`compare_readings.py` over the probe corpus. A softening outside that table fails the compare.

**Connection enforcement.** The Claude import and the per-name fold call each have a test that
fails when the connection is removed and the callee remains (AC-1.9's mutation returns only the
spelled name; the `_tree_b` stub is what makes the import the thing the symlink test consumes).

**Test discrimination** on the copied Codex fixture: leaving the identity module absent keeps
`kind=judge-error` as the observation. A stub module that emitted a resolvable record would
make that arm pass for a different reason.

**Backward compatibility** and **Regression provenance.** Existing tests stay green except the
deltas named in the spec (AC-5.2's unpack, AC-5.5's new rows, AC-8.6's two oracle edits) and
the two reviewed deltas in §"Test Plan". Each of those pins a contract the change replaces:
five-field unpack, eleven-kind parametrize, `$(cat)` oracle line, copied tree without an
identity module, and a replace that assumed `SID_READ` was on the oracle line.

**Assumption verification** and **Behavioural premises carry their command.** §"Verified
premises" records the commands re-run for this draft. F_GETPATH, `ALLOW_MISSING`, and
`O_SEARCH` are not re-probed here; PD-1's R-1 is the authority, and T0 re-derives it. The
argparse mutual-exclusion phrase is the spec's substring, not a longer phrase this draft
executed.

**Counts a dispatch reports.** The mutation-object table was counted in this session by walking
each spec's `find` fields. The plan's `"M:G1" in find` substring also matches `G10`; the table
names both objects. The suite collection floor and the anchor baseline are the plan's to
re-measure at the feature-branch base. This design does not freeze them.

**Both halves of a doc change.** T12 removes the oracle `$(cat)` and lands
`--session-id-from-git-dir` in the same tasks (T10 writes the flag, T12 writes the line, T11
admits it). The state-write lines stay, which is the spec's residual, stated, not dropped.

**Reimplementation parity.** The header grammar is new relative to `PATCH_TARGET`, and the
differential is the self-check cases plus AC-4.1–AC-4.7 against the R-4 code points. It is not
a reimplementation of Codex. A later codex-cli that trims differently is caught when R-4 is
re-taken by hand.

**Operator-override preservation**, **Audit-gate signal discipline**, **Standalone / no plugin
dependency**, **Incident replay**, **Wrapper–runtime reconciliation.** This feature does not
change the audit gate, the override sidecar, or a wrapper over an external runtime's CLI. The
probe replays gate behaviour through `tdd_gate_support`, which is the in-repo harness, and the
agent-tool rows stay manual because no committed artifact may invoke the agent.

**How agy uses this file.** agy reads `h-mad/invariants.base.md` as the base rubric. The agy
adapter's `## The TDD gate` stays free of judge-kind tokens because no agy gate exists. T12
still changes the agy oracle line under `## Context budget and claims`.

## Verified premises

Structural census re-run from the skills root in the session that wrote this draft. `git
rev-parse --short=8 HEAD` printed `1254595a`. Units are matching lines unless a cell says
otherwise. Behavioural M-cell readings are T0's probe, not this table.

| Premise | Command | Result |
|---|---|---|
| `KINDS` members | `/opt/anaconda3/bin/python -c 'import sys;sys.path.insert(0,"h-mad/scripts");import h_mad_tdd_judge as j;print(len(j.KINDS), sorted(j.KINDS))'` | 11 distinct values: `judge-error`, `no-summary`, `no-test-resolved`, `no-tests-ran`, `pytest-error`, `pytest-missing`, `red-measured`, `test-missing`, `test-passing`, `timeout`, `venv-escapes-root` |
| `JUDGE_DENY_RE` alternatives | `grep '^JUDGE_DENY_RE=' h-mad/hooks/h-mad-tdd-gate.sh` piped to a count of the `kind=(…)` split | 10 alternatives in that one assignment |
| `pwd -P` | `grep -c 'pwd -P' h-mad/hooks/h-mad-tdd-gate.sh` | 2 matching lines (the `ROOT_ABS` assignment and the `# M:H8` walk) |
| `build_parser` | `grep -c 'def build_parser' h-mad/scripts/h_mad_resume_decision.py` | 0 matching lines. The zero is load-bearing: the parser is built inside `main`, which is why T10 adds `build_parser`. An unrelated later `def build_parser` would make this zero incidental |
| `ArgumentParser` / `add_argument` | `grep -c ArgumentParser` and `grep -c 'parser.add_argument('` on that file | 1 matching line, and 5 matching lines |
| Safe-list length and resume key | import the Codex gate via `importlib.util.spec_from_file_location` and print `len(SAFE_HMAD_SCRIPT_OPTIONS)` and whether `h_mad_resume_decision.py` is a key | `10 False` |
| git rev-parse refused | the same import, `_safe_shell_command("git rev-parse --absolute-git-dir", ".", ".")` | `False` |
| `_run_bounded` | `git grep -n '_run_bounded' -- h-mad` | 5 matching lines: 3 in `h_mad_tdd_judge.py` (the `def` and two unpacks), 2 in `test_h_mad_tdd_judge.py` (the test name and one unpack) |
| `# M:K3` | `grep -c -F '# M:K3' h-mad/scripts/h_mad_tdd_judge.py` | 1 matching line |
| `apply_patch` in the dispatcher | `grep -c apply_patch h-mad/scripts/hmad-dispatch.sh` | 0 matching lines. The zero is load-bearing: the file has no `apply_patch` verb, so no dispatch route runs it as a bare tool. A later verb of that name would move the zero |
| copied-hook sites | `grep -c -F` of `link.symlink_to(hook)`, `shutil.copyfile(HOOK, hook)`, `shutil.copyfile(CODEX_GATE, gate)` | 1 matching line each |
| dd7 assertion | `grep -c -F 'assert len(observed) == 126 and observed.count("deny") == 18' h-mad/tests/test_h_mad_tdd_gate_judge.py` | 1 matching line |
| oracle cat-subst | `grep -c 'h_mad_resume_decision.py.*session-id "$(cat'` on each of `codex-runtime.md`, `grok-runtime.md`, `agy-runtime.md` | 1 matching line in each file |
| `DRAIN_SECONDS` shape | `grep -c -E '^DRAIN_SECONDS\|communicate\(timeout=DRAIN_SECONDS' h-mad/scripts/h_mad_doc_block_exec.py` | 2 matching lines. The constant's value was not printed in this census; the plan records why it is not reused |
| `_project_root` returns | `ast` walk of `Return` nodes inside the function | 4 return sites |
| `Hook:` lines | `grep -c '^Hook:' h-mad/references/codex-implementer-prompt.md` | 1 matching line |
| D1 assertion | `grep -c "expected one 'Hook: ' line" h-mad/tests/test_h_mad_tdd_gate_docs.py` | 1 matching line |
| Judge-kind tokens in `## The TDD gate` | extract that section until the next `## ` heading in `grok-runtime.md` and in `agy-runtime.md`, count lines matching any current `KINDS` token | 0 matching lines in each section. The zero is load-bearing: the sections do not list judge kinds, which is why T7 adds none. A later sentence that names a kind moves the zero and T7's "add nothing" has to be re-read |
| Mutation finds | walk `mutations[].find` in `claude_gate_judge_wiring.json`, `codex_gate_judge_wiring.json`, `tdd_judge_scoring.json` | the object names in §"Mutation anchors". `"M:G1" in find` matches two finds, objects `G1` and `G10`, because `# M:G10` contains the substring `M:G1`. The G1 line itself is one object |

`_pct_decode` is the function whose body is `[ "$1" = % ] && return 0; printf '%b' "${1//%/\\x}";`.
`_relative_target`'s annotation today is `tuple[Path, str] | None`. `SAFE_HMAD_SCRIPT_OPTIONS`
keys are the ten listed in §"FR-8 git-dir read". Frontmatter of `h-mad/SKILL.md` is `name: h-mad`
and the description quoted in §"Documentation surfaces".

## Open questions

None. The two fixture deltas in §"Test Plan" are decided. They are owed to the spec author as
awareness: the spec's compatibility sentence names AC-5.2, AC-5.5, AC-8.6, and FR-1's verdict
changes, and does not name the `_tree_b` stub or the `SID_READ` control. This design does not
edit the spec.

## Version History
- v1.0: First draft. One canonicaliser module for both gates, one unresolvable flag, percent-encoded name list, bounded reap, and the resume git-dir read before decide.
