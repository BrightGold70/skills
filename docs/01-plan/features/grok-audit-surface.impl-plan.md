# Implementation Plan: grok-audit-surface

> Source: `docs/02-design/features/grok-audit-surface.design.md` v1.4 (`a6a1571a`), spec v1.7 and
> plan v1.5 (both `28ec5bfc`), the Phase 5 carry list
> `docs/03-analysis/grok-audit-surface.phase5-carry.md` (15 items) and operator decision D4
> (`docs/03-analysis/grok-audit-surface.decision-2026-10-19-d4.md`).
> Branch target: `feature/grok-audit-surface` (Phase 5c names the branch).

Every `path:symbol`, existing test name, mutation `find` and count below was read from the tree at
`30917a1a`. `git diff --quiet a6a1571a 30917a1a -- docs/02-design/features/grok-audit-surface.design.md h-mad`
exits 0, so the design's readings describe the code this plan builds on.

## Executive Summary

Eighteen Tasks. Tasks 0–14 run in the Phase-5 worktree and are the S0 instrument that merges to
`main`. Task 15 is the operator's S0b, S1 and S2 (not CI). Task 16 is S3 on every outcome that
publishes; Task 17 is S4 and runs only on `SEEDSCORE: PASS`.

| Task | Shape | What lands | Design |
|---|---|---|---|
| 0 | operational | the `exec agy` `workspaceDirs=` tracer into a `mktemp -d` root, recorded before S1 | D8 (agy provenance); carry 9 |
| 1 | new-behaviour | `exclusions.txt` and its doc pin | D5 |
| 2 | new-behaviour | the probe's entry point: imports, the nine D2 subparsers, the last resort, usage-error tokens, the mutation spec file | D1, D2; carry 12 |
| 3 | new-behaviour | `check-ledger` (D4) and the synthetic archive and temp-repo builder | D4 |
| 4 | new-behaviour | `build-root` without `--reset`: export, exclusion list, placements, content scan, reach check | D5, D6, D7 |
| 5 | new-behaviour | `build-root --reset`: the target precondition, the no-follow reset, re-walk, step 6 | D5; carry 1, 2, 3, 13 |
| 6 | new-behaviour | `record-cycle` and `commit-data` | D8, D9; carry 14 |
| 7 | new-behaviour | `smoke` and the `AUDITCYCLE:` and `Effort:` parsers | D10, D11; carry 4, 5, 10, 14, 15 |
| 8 | wiring | `extract`: the gate walk, the three `classify`/`_collapses` wires, `cycle_token`, the stands rule | D10, D12; carry 11 |
| 9 | new-behaviour | `score`: `key_mismatch`, `label`, D3, the verdict, the observational lines | D13 |
| 10 | new-behaviour | `main-leak`, `rescore`, the calibration-data set, the grammar sweeps over all nine modes | D3, D9, D2 |
| 11 | new-behaviour | the `HMAD_ASSEMBLE_SAME_REPORT_P<i>` stub knob and the identical-prompts test | Components, Wrapper pins |
| 12 | new-behaviour | FR-8, FR-9, FR-10 and AC-7.2-stamp pins over unchanged code, and the M1/M2 authority test | Gate pins, Wrapper pins |
| 13 | new-behaviour | SKILL.md AC-6.2a and AC-9.5 text and the S0 doc pins | D14 |
| 14 | gate | the Phase 5e verdict over the whole spec, the anchors, the fixture-name check, the two counts | Mutation spec; carry 11 |
| 15 | operational | S0b, S1, S2 (operator) | D8, D9; carry 6, 9, 10 |
| 16 | new-behaviour | S3: `main-leak`, `rescore`, the measurement doc, `grok-runtime.md`, AC-6.2/6.3 text and pins, K2 re-anchor | D9, D14, D15 |
| 17 | new-behaviour | S4 on PASS only: AC-7.1–7.3 and AC-8.3 text and pins | D14 |

Shapes: `operational` 2 (Tasks 0, 15); `new-behaviour` 14 (Tasks 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12,
13, 16, 17); `wiring` 1 (Task 8); `gate` 1 (Task 14). 2 + 14 + 1 + 1 = 18.

Mutation rows at S0 (after Task 13): 171 in `h-mad/tests/mutation-specs/grok_audit_surface.json`.
Per Task: 6 (T2) + 14 (T3) + 14 (T4) + 13 (T5) + 11 (T6) + 25 (T7) + 20 (T8) + 25 (T9) + 21 (T10) +
2 (T11) + 17 (T12) + 3 (T13) = 171. Of these, 28 are the design's named rows (W1–W10, G1–G5, C1–C4,
K1–K3, X1–X6) and 143 are P-rows (one per refusal or non-default-verdict fixture, design §"Mutation
spec", "P-rows"). Task 16 adds the named row K6 on every outcome, and K4 and K5 only on MISS or
INCONCLUSIVE, which makes 172 on PASS or a smoke failure and 174 on MISS or INCONCLUSIVE.
Marker sites in the probe: 117 (per Task: 6 + 13 + 11 + 13 + 10 + 15 + 12 + 20 + 17). The design
carries neither total; Task 14 re-derives both with the design's two commands (carry 11).

## Rules every Task follows

- **Interpreter.** Every pytest run and every mutation spec uses `/opt/anaconda3/bin/python3.11`.
  `python3` (3.15 here) has no pytest, and the RTK hook rewrites `python3 -m pytest`, so a
  precondition is probed as `rtk proxy /opt/anaconda3/bin/python3.11 -m pytest --version`.
- **Full suite per Task**, never a scoped selection as the gate:
  `rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider`, from the
  repository root, in the foreground, gated on the summary line and never on `$?`. The scoped
  `--test-path` given to the 5d/5e assembler is the Task's own test file, repo-root-relative
  (`h-mad/tests/<file>.py`).
- **RED counts are pytest node IDs.** A parametrised test counts once per id. `F` fails at RED, `P`
  passes at RED. A `P` is a regression guard and is labelled as one.
- **Node-id spelling.** In WIRE-PIN lines and assembler arguments a test is written repo-root-relative
  (`h-mad/tests/test_x.py::test_y`). In mutation rows the `test` key is relative to the spec's root
  `../..`, which resolves to `h-mad/` (`tests/test_x.py::test_y`). The function name is identical
  in both.
- **Driving the probe.** Each probe test module defines
  `PROBE = REPO / "docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py"` as one literal
  (what `h_mad_archive_feature.probe_readers` matches) and runs it as
  `subprocess.run([sys.executable, str(PROBE), ...])`, asserting the exit code and the **exact**
  last stdout line together. A test that replaces a function calls `main(argv)` in process with
  `monkeypatch` and `capsys`, and reads `capsys.readouterr()` before asserting.
- **Tracebacks are surfaced, so a mutant's crash is visible (axis: a traceback a mutant causes in
  the probe).** The mutation harness counts a crash kill only from tracebacks visible in the scoring
  run's output (`crash_kill` returns `None` when the traceback is not printed). So: (1) the probe
  prints a traceback on stderr only for an exception outside its declared refusal classes (one base,
  `ProbeRefusal`, which `Refusal`, `UsageError`, `ResetArgsConflict`, `ResetPurposeNotS1`, the four
  `ResetTarget…` classes and `RootResetMismatch` subclass). A declared refusal prints its token and
  no traceback (`# M:GAS-TRACEBACK-SCOPE`). (2) Every assertion on a probe run passes that run's
  stderr as its message: a subprocess assertion passes the child's (`assert lines[-1] == expected, r.stderr`),
  and an in-process `main(argv)` assertion passes the captured one
  (`out, err = capsys.readouterr()`, then `assert out.splitlines()[-1] == expected, err`). So a
  mutant-caused `KeyError`, `TypeError` or `NameError` reaches the harness and is counted, whichever
  way the test drives the probe. (3) The only exceptions are the
  tests that inject an exception on purpose or assert on stderr's content
  (`test_internal_failure_prints_the_mode_token`, and the traceback-absence assertions of
  `test_usage_error_prints_the_mode_token` and of Task 5's refusal tests): these compute their figures into locals first
  (`n = r.stderr.count("Traceback")`) and assert on the locals with a fixed message, never echoing
  stderr. Residual: a mutant whose only effect is that one declared refusal class falls through to
  another declared class prints no traceback by design. That kill is an assertion kill, which is
  the correct reading. The design's D1 sentence ("prints the traceback on stderr") is read as
  covering only exceptions that escape the declared checks; that reading is owed to the design.
- **In-process loads never use bytecode (axis: a mutation that lands but does not execute).** The
  harness purges `__pycache__` only under its root (`h-mad/`), and the probe lives under `docs/`.
  A same-size mutation written within one mtime second is then read from a stale `.pyc`. Every
  in-process test therefore loads the probe with `grokauditfixtures.load_probe(PROBE)`, which
  compiles the source text (`compile(path.read_bytes(), str(path), "exec")`) into a fresh
  `types.ModuleType`, so no `.pyc` is read or written. A subprocess run is unaffected, because
  `subprocess.run([sys.executable, str(PROBE), ...])` runs the probe as `__main__`, which Python
  never caches. The probe's own imports are `h-mad/scripts` modules,
  which sit under the purged root. This also keeps the probe directory free of `__pycache__`,
  which matters because the plan restricts that directory to the probe and the exclusion list.
- **Synthetic only.** Every fixture is invented text built under `tmp_path` (or, for the reset
  fixtures, under `tempfile.gettempdir()` and removed by the fixture's finalizer). No test reads the
  real calibration ref, dispatches an agent, or touches the network. A test whose clean case needs
  its root outside a work tree first asserts `git -C <that parent> rev-parse --git-dir` fails; it
  never skips. No `skip`, `xfail` or `.only` anywhere.
- **Mutation spec.** One file, `h-mad/tests/mutation-specs/grok_audit_surface.json`, created by
  Task 2 with `"root": "../.."`, `"target_command": ["/opt/anaconda3/bin/python3.11", "-m", "pytest", "-q"]`
  and a `command` that names the feature's test files that exist at that Task. Each later Task that
  creates a test file inserts it into `command` at its design position, so after Task 13 `command`
  equals the design's seven-file list. Rows carry `name`, `file`, `find`, `replace`, `test` and
  `symbol` (the enclosing function or class). Probe rows name `file`
  `../docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (one committed precedent names a
  file outside `h-mad/`: `host_runtime_docs.json`, `../handoff/SKILL.md`). Each Task's rows are
  added at its GREEN, against the committed bytes; their intent and `test` are fixed here.
- **P-rows.** Each probe guard line carries a marker comment `# M:GAS-<NAME>`, and nothing else in
  the probe contains the text `M:GAS-`. A P-row's `find` is that marker's line. Its `replace` keeps
  the code running (never introduces an exception, an undefined name or a type change), because
  Phase 5e accepts only `crash_kills=0`; so a row changes a condition, a constant or a printed
  reason, never deletes a statement that later code needs. Where two guards print the same token, a
  `replace` that only disables one of them falls through to the other and survives as an
  equivalent mutant; those rows (named in Task 7) turn the refusal into acceptance instead.
- **Verdicts.** Each Task that adds rows runs, from the repository root,
  `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/grok_audit_surface.json`
  and requires `MUTATION: ALL_CAUGHT` with `untargeted=0/` followed by the row count so far and
  `crash_kills=0`, then the same with `--check-anchors` and `ANCHORS: ANCHORS_OK`, read from the
  token lines.
- **Markers.** Every probe run writes `[H-MAD] grok-audit-surface` followed by the mode and the
  token's verdict word to stderr, after the token line is printed (base §"Marker discipline").

## Task 0: agy workspace tracer

**Production files**: none
**Test files**: none
**Task shape**: `operational` — runs an existing wrapper verb once and records what it wrote; it
builds and mutates nothing in the repository.

**Description**: Before S1, one `exec agy` dispatch into a fresh `mktemp -d` directory records which
spelling agy's own cli log gives that directory on its `workspaceDirs=` line: the `mktemp` spelling
(`/var/folders/…`) or its physical one (`/private/var/folders/…`). D8's agy-provenance selection
matches either spelling; until this reading exists, whether the `exec agy` leg logs the root at
all is unmeasured (D8 residual). The tracer runs first because nothing in Tasks 1–14 depends on it
and Task 15 cannot start S1 without it. The tracer's prompt and reading live under the kept
directory, never in the repository; Task 16 copies the reading into the measurement doc's Readings.

```bash
KEEP="$HOME/.local/state/h-mad/grok-audit-surface"; TR="$KEEP/agy-tracer"; mkdir -p "$TR"
AGYLOG="$HOME/.gemini/antigravity-cli/log"; /bin/ls "$AGYLOG" > "$TR/before.txt"
printf 'Reply with the single word OK.\n' > "$TR/prompt.txt"
T=$(mktemp -d)
h-mad/bin/hmad-dispatch exec agy "$TR/prompt.txt" --cd "$T" --timeout 300 --out "$TR/out.txt"
{ echo "T=$T"; echo "TP=$(cd "$T" && pwd -P)"
  for f in "$AGYLOG"/cli-*.log; do
    grep -qxF -- "${f##*/}" "$TR/before.txt" && continue
    echo "new=${f##*/} $(grep -o -m1 'workspaceDirs=\[[^]]*\]' "$f")"
  done; } > "$TR/reading.txt"
rm -rf "$T"
```

**Acceptance Criteria**:
- [ ] AC-T0.1: `$TR/reading.txt` exists and holds its `T=` and `TP=` lines and every `new=` line
  the loop printed.
- [ ] AC-T0.2: The result is classified from the file, as exactly one of: one `new=` line whose
  `workspaceDirs=[…]` value equals the `T=` value (`mktemp` spelling), or equals the `TP=` value
  (physical spelling); or anything else (zero `new=` lines, several, or neither spelling). The
  classification is written as the file's last line, `CLASS=mktemp`, `CLASS=physical` or
  `CLASS=unmatched`.
- [ ] AC-T0.3: On `CLASS=unmatched`, Task 15 re-derives D8's selection from this reading before
  any S1 dispatch (D8: "If it names neither spelling, the selection above is re-derived from that
  reading before S1 dispatches"); the re-derived selection is recorded in the runbook Task 16
  publishes.
- [ ] AC-T0.4: The `mktemp -d` directory is gone after the run (`test -e "$T"` fails).

**Dependencies on other tasks**: None. Must complete before Task 15's S1 step.

---

## Task 1: the declared exclusion list

**Production file**: `docs/03-analysis/probes/grok-audit-surface/exclusions.txt`
**Test file**: `h-mad/tests/test_grok_audit_surface_docs.py`
**Task shape**: `new-behaviour`

**Description**: The exclusion list D5 specifies, committed on `main`, and the doc pin that it holds
the required entries. Its grammar is two line kinds (`dir`, `name-contains`) plus `#` comments; it
holds exactly D5's six entries.

```
dir docs/archive/2026-09/audit-report-docs-copy
dir docs/archive/2026-09/tdd-gate-fail-opens
dir docs/archive/2026-10/agy-coder-fallback
dir docs/03-analysis/probes/grok-audit-surface
dir docs/03-analysis/agy-coder-fallback.authoring
name-contains grok-audit-surface
```

**Code structure**:
```python
# h-mad/tests/test_grok_audit_surface_docs.py
REPO = Path(__file__).resolve().parents[2]
EXCLUSIONS = REPO / "docs/03-analysis/probes/grok-audit-surface/exclusions.txt"
def test_exclusion_list_holds_the_required_entries() -> None: ...
```

**Acceptance Criteria**:
- [ ] AC-T1.1: `test_exclusion_list_holds_the_required_entries` asserts the non-comment,
  non-blank lines of the file are exactly the six above, in that order.

**RED split**: 1 node; 1 F (the file is absent), 0 P.

**Mutation rows**: none (the doc pin's discrimination is its RED; the list is data).

**Dependencies on other tasks**: None.

---

## Task 2: the probe's entry point

**Production files**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (create),
`h-mad/tests/mutation-specs/grok_audit_surface.json` (create)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (create),
`h-mad/tests/grokauditfixtures.py` (create, holding `load_probe` only; Task 3 extends it)
**Task shape**: `new-behaviour`

**Description**: The probe file with D1's imports and D2's nine subparsers, every command line exactly
as the D2 table writes it, and D1's token discipline: one `try` around the mode, and an escaping
exception printed as the traceback on stderr followed by the mode's refusal token with
`reason=internal:` and the class name, exit 2 (`smoke`: `input_unparseable:` and the path D1 names).
`MODES` maps a mode name to its handler; each later Task adds its own handler, so at this Task a
mode whose handler has not landed reaches the last resort as `internal:KeyError`. That is the
transitional state of a feature branch, not a shipped one: Task 10's `test_success_token_shape_per_mode`
fails until all nine handlers exist.

**Every argparse exit path ends on the mode's token (carry 12; axis: argparse's exits).** Measured on
`/opt/anaconda3/bin/python3.11` (3.11.8) and `python3` (3.15.0): argparse's only `sys.exit` is in
`ArgumentParser.exit`, which has three callers: `error()`, the help action and the version action
(4 `.exit(` sites in the module source on each interpreter). Reproduce:

```bash
for py in /opt/anaconda3/bin/python3.11 python3; do $py -c 'import argparse,inspect,re,sys;print(sys.version.split()[0], len(re.findall(r"\.exit\(", inspect.getsource(argparse))))'; done
# 3.11.8 4
# 3.15.0 4
for py in /opt/anaconda3/bin/python3.11 python3; do $py -c '
import argparse,sys,io,contextlib
p=argparse.ArgumentParser(prog="p"); s=p.add_subparsers(dest="m"); s.add_parser("smoke").add_argument("--data")
o=io.StringIO()
try:
    with contextlib.redirect_stdout(o): p.parse_args(["smoke","--help"])
except SystemExit as e: print(sys.version.split()[0], "SystemExit", e.code, "stdout_bytes", len(o.getvalue()))'; done
# 3.11.8 SystemExit 0 stdout_bytes 105
# 3.15.0 SystemExit 0 stdout_bytes 105
```

The rule:
- Every parser, the top-level one included, is a `_TokenArgumentParser`
  (`build_parser()` returns one, and `add_subparsers(parser_class=_TokenArgumentParser)`). This
  matters because an unrecognised flag after a subcommand is reported by the **top-level**
  parser's `error()`: with a plain top-level parser, `smoke --data x --no-such-flag` exits 2 with
  no token.
- `_TokenArgumentParser.error()` prints the message on stderr and raises `UsageError`
  (`# M:GAS-USAGE`).
- Every parser is built with `add_help=False` (`# M:GAS-NO-HELP`) and `allow_abbrev=False`
  (`# M:GAS-NO-ABBREV`), and no parser defines a `version` action. With `add_help` left at its
  default, `<mode> --help` prints help on stdout and exits through `SystemExit(0)` with no token.
  With `allow_abbrev` left on, `check-ledger --tre t` is silently read as `--tree t` rather than
  refused.

So `ArgumentParser.exit` is unreachable. `--help`, `-h`, an abbreviation, an unknown flag, a
missing value and a bad `type=` conversion all reach `error()`, and the last resort prints that
mode's refusal token with `reason=internal:UsageError`. The `smoke` refusal reads its path from the
**raw argv**, never from a `Namespace`: a `UsageError` raised inside `parse_args` returns no
`Namespace`, and a subparser's error fires before its values are copied up. So
`refusal_token(mode, exc, argv)` gives `SMOKE: UNREADABLE reason=input_unparseable:` followed by
the first of: the module-level `_OPEN_INPUT` (a `str` or `None`, set to `None` at the start of
every `main` call and assigned by Task 7's `smoke` to each input's path immediately before it
opens that input), when it is not `None`; else the word after the first exact `--data` in argv (or
the `--data=` value); else the empty string. That is D1's order: the input the derivation had
open, then the `--data` directory. `refusal_token` reads `_OPEN_INPUT` directly; no other channel
carries it. Residual, stated exactly: a future Python whose argparse
gains another `exit` caller is not covered. Task 2's tests run under the interpreter the suite
uses, and the measured site count above is what would change.

**An argv with no mode prints a cannot-judge token first (operator ruling, 2026-10-19).** When the
first argv word is not one of the nine `GRAMMAR` keys, or argv is empty, `main` checks this before
any parsing: it prints exactly one stdout line, `PROBE: UNREADABLE reason=unknown_mode`, carrying no
counts (`# M:GAS-UNKNOWN-MODE`), then the top-level usage on stderr and the `[H-MAD]` marker, and
returns 2. So AC-5.1 holds as written: there is no exit without a token. `PROBE:` is a tenth token
prefix that belongs to no mode, and no mode's published line or token starts with it. It is an
addition to D2's grammar, owed to the design and the spec.

**Code structure**:
```python
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "h-mad" / "scripts"))
import h_mad_audit_gate as _gate
import h_mad_audit_cycle as _cycle
from h_mad_audit_origins import ORIGINS
from h_mad_review_evidence import _GROK_TYPES

SOURCES: dict[str, str] = {
    "audit-report-docs-copy": "docs/archive/2026-09",
    "tdd-gate-fail-opens": "docs/archive/2026-09",
    "agy-coder-fallback": "docs/archive/2026-10",
}
GRAMMAR: dict[str, tuple[str, str]] = {  # mode -> (token prefix, refusal word), D2
    "check-ledger": ("LEDGER:", "UNREADABLE"), "build-root": ("ROOT:", "UNREADABLE"),
    "record-cycle": ("RECORD:", "REFUSED"), "commit-data": ("COMMIT:", "REFUSED"),
    "smoke": ("SMOKE:", "UNREADABLE"), "extract": ("FINDINGS:", "UNREADABLE"),
    "score": ("SEEDSCORE:", "UNREADABLE"), "rescore": ("SEEDSCORE:", "UNREADABLE"),
    "main-leak": ("MAINLEAK:", "UNREADABLE"),
}
MODES: dict[str, Callable[[argparse.Namespace], int]] = {}
_OPEN_INPUT: str | None = None  # the input smoke has open; reset by main, read by refusal_token

class ProbeRefusal(Exception): ...          # base of every declared refusal; no traceback
class UsageError(ProbeRefusal): ...
class _TokenArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs) -> None: ...  # forces add_help=False, allow_abbrev=False
    def error(self, message: str) -> NoReturn: ...
def parse_sources(value: str) -> dict[str, str]: ...
def build_parser() -> _TokenArgumentParser: ...
def refusal_token(mode: str, exc: BaseException, argv: list[str]) -> str: ...
def main(argv: list[str] | None = None) -> int: ...
# h-mad/tests/grokauditfixtures.py
def load_probe(path: Path) -> types.ModuleType: ...  # compile from source; no .pyc read or written
```

**Tests** (in `h-mad/tests/test_grok_audit_surface_probe.py`):
1. `test_internal_failure_prints_the_mode_token`, parametrised over the nine D2 modes (9 ids). In
   process: `monkeypatch.setitem(probe.MODES, mode, raiser)` with a handler raising `RuntimeError`;
   the argv is the mode plus the minimal D2 arguments with `tmp_path` values. The last stdout line is
   that mode's refusal token with `reason=internal:RuntimeError` (`smoke`:
   `SMOKE: UNREADABLE reason=input_unparseable:` plus the `--data` value), `main` returns 2, and
   stderr carries `Traceback`.
2. `test_usage_error_prints_the_mode_token` (plan-added, carry 12), parametrised over the nine modes
   (9 ids), as a subprocess: argv `[mode, "--no-such-flag"]` for the eight non-smoke modes and
   `["smoke", "--data", str(tmp_path / "s1"), "--no-such-flag"]` for `smoke`. Exit 2 and the last
   stdout line is the mode's refusal token with `reason=internal:UsageError` (`smoke`: with
   `input_unparseable:` and the `--data` value), and `n = r.stderr.count("Traceback")` is 0 (a
   declared refusal prints no traceback).
3. `test_unknown_mode_prints_the_probe_token` (operator ruling), parametrised over two argvs (2 ids):
   `[]` and `["no-such-mode"]`, as a subprocess. Exit 2; stdout is exactly the one line
   `PROBE: UNREADABLE reason=unknown_mode`; stderr contains `usage:`.
4. `test_help_flag_prints_the_mode_token` (plan-added, audit cycle 1), parametrised over the nine
   modes (9 ids), as a subprocess: argv `[mode, "--help"]` (`smoke`: with `--data` before it).
   Exit 2, stdout has no line other than the token, and the token is the mode's refusal token with
   `reason=internal:UsageError` (`smoke`: `SMOKE: UNREADABLE reason=input_unparseable:` followed by
   the `--data` value, as in Tests 1 and 2).
5. `test_abbreviated_flag_is_a_usage_error` (plan-added, audit cycle 1), 1 id, as a subprocess:
   argv `["check-ledger", "--tre", str(tmp_path)]`. Exit 2 and
   `LEDGER: UNREADABLE reason=internal:UsageError`. With abbreviations allowed, the same argv runs
   the ledger check on `tmp_path` and prints a different reason.

**Acceptance Criteria**:
- [ ] AC-T2.1: The five tests pass for all 30 ids (9 + 9 + 2 + 9 + 1).
- [ ] AC-T2.2: The probe imports only the stdlib and the four D1 modules; `grep -nE '^(import|from) ' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py`
  shows nothing else.
- [ ] AC-T2.3: `MODES` is the only dispatch table; `main` never calls a handler by name.
- [ ] AC-T2.4: The spec file exists with the header above and `command`
  `["/opt/anaconda3/bin/python3.11", "-m", "pytest", "tests/test_grok_audit_surface_probe.py", "tests/test_grok_audit_surface_docs.py", "-q"]`.

**RED split**: 30 nodes; 30 F (the probe is absent), 0 P.

**Mutation rows** (6):

| name | find (marker line) | intent of `replace` | test |
|---|---|---|---|
| `p-last-resort-reason` | `# M:GAS-LAST-RESORT` | print `internal:Exception` in place of the class name | `tests/test_grok_audit_surface_probe.py::test_internal_failure_prints_the_mode_token` |
| `p-usage-token` | `# M:GAS-USAGE` | `error()` calls `argparse.ArgumentParser.error` (no token) | `tests/test_grok_audit_surface_probe.py::test_usage_error_prints_the_mode_token` |
| `p-unknown-mode-token` | `# M:GAS-UNKNOWN-MODE` | the token line removed (its `print` call replaced by `pass`); usage and exit 2 unchanged | `tests/test_grok_audit_surface_probe.py::test_unknown_mode_prints_the_probe_token` |
| `p-no-help` | `# M:GAS-NO-HELP` | `add_help=True` | `tests/test_grok_audit_surface_probe.py::test_help_flag_prints_the_mode_token` |
| `p-no-abbrev` | `# M:GAS-NO-ABBREV` | `allow_abbrev=True` | `tests/test_grok_audit_surface_probe.py::test_abbreviated_flag_is_a_usage_error` |
| `p-traceback-scope` | `# M:GAS-TRACEBACK-SCOPE` | print the traceback for every exception, declared refusals included | `tests/test_grok_audit_surface_probe.py::test_usage_error_prints_the_mode_token` |

**Dependencies on other tasks**: Task 1 (the docs test module exists for `command`).

---

## Task 3: ledger checks

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend),
`h-mad/tests/grokauditfixtures.py` (extend; Task 2 created it with `load_probe`)
**Task shape**: `new-behaviour`

**Description**: `check-ledger` per D4, in both front doors (`--tree` and
`--repo . --calibration-sha`), and the fixture builder every later Task uses.
`grokauditfixtures.py` builds (a) a synthetic archive of three invented features, each with spec,
plan, design and impl-plan, giving nine seeded documents `d1`…`d9` in feature order and then plan,
design, impl-plan; (b) a 27-record ledger obeying the AC-2.2 class rule, with seeded copies made by
replacing each `original` once; (c) a temporary repository at `tmp_path/work` whose `origin` is a
bare `tmp_path/origin.git`, with a `main` commit and the calibration branch created by plumbing.
Every probe call in a fixture passes `--sources` with the synthetic archive's mapping. Each check is
one guard with its own marker; the per-document class rule refuses before the totals comparison, so
the totals comparison has no fixture that reaches it and carries no marker.

**Code structure**:
```python
def read_ledger(tree: Path) -> list[dict]: ...
def check_ledger(tree: Path, sources: dict[str, str]) -> dict[str, int]: ...  # raises Refusal("ledger_counts" | "ledger_origin" | "seed_rebuild")
class Refusal(ProbeRefusal):
    def __init__(self, reason: str) -> None: ...
def _mode_check_ledger(args: argparse.Namespace) -> int: ...
# grokauditfixtures.py
def build_archive(root: Path) -> dict[str, str]: ...        # returns the --sources mapping
def build_ledger(tree: Path, sources: dict[str, str]) -> list[dict]: ...
def build_repo(tmp_path: Path) -> tuple[Path, Path]: ...   # (work, origin.git)
```

**Tests** (16, in the probe test module, each with its one trigger alone):
`test_ledger_counts_refuses_a_repeated_class_with_totals_kept` (d1 C2, C2, C4 and d4 C1, C3, C3),
`test_ledger_counts_refuses_a_moved_class`, `test_ledger_counts_refuses_an_unparseable_line`,
`test_ledger_counts_refuses_a_missing_field`, `test_ledger_counts_refuses_a_source_outside_the_nine`,
`test_ledger_counts_refuses_an_empty_original`, `test_ledger_counts_refuses_an_empty_expected`,
`test_ledger_origin_refuses_an_unknown_origin`, `test_seed_rebuild_refuses_one_byte`,
`test_seed_rebuild_refuses_a_twice_occurring_original`,
`test_seed_rebuild_refuses_two_seeds_in_one_section`,
`test_seed_rebuild_refuses_a_seed_under_version_history`,
`test_seed_rebuild_refuses_a_wrong_section_name`, `test_seed_rebuild_refuses_a_seeded_span_not_once`,
`test_ledger_ok_reports_derived_counts`, `test_check_ledger_tree_and_repo_forms_agree`.

**Acceptance Criteria**:
- [ ] AC-T3.1: Each refusal test's last stdout line is exactly `LEDGER: UNREADABLE reason=ledger_counts`,
  `reason=ledger_origin` or `reason=seed_rebuild` as its name says, with exit 2.
- [ ] AC-T3.2: `test_ledger_ok_reports_derived_counts` reads exactly
  `LEDGER: OK seeds=27 docs=9 C1=6 C2=7 C3=7 C4=7` on the clean fixture, exit 0, and the probe source
  holds none of `6`, `7` or `27` as a count literal in `check_ledger` (the totals are derived from the
  rule).
- [ ] AC-T3.3: The two front doors give the same last line on the same content.

**RED split**: 16 nodes; 16 F (no `check-ledger` handler: `internal:KeyError`), 0 P.

**Mutation rows** (14; markers 13):

| name | marker | test |
|---|---|---|
| `p-ledger-class-repeated` | `# M:GAS-LEDGER-CLASS` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_a_repeated_class_with_totals_kept` |
| `p-ledger-class-moved` | `# M:GAS-LEDGER-CLASS` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_a_moved_class` |
| `p-ledger-json` | `# M:GAS-LEDGER-JSON` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_an_unparseable_line` |
| `p-ledger-field` | `# M:GAS-LEDGER-FIELD` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_a_missing_field` |
| `p-ledger-source` | `# M:GAS-LEDGER-SOURCE` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_a_source_outside_the_nine` |
| `p-ledger-empty-original` | `# M:GAS-LEDGER-EMPTY-ORIGINAL` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_an_empty_original` |
| `p-ledger-empty-expected` | `# M:GAS-LEDGER-EMPTY-EXPECTED` | `tests/test_grok_audit_surface_probe.py::test_ledger_counts_refuses_an_empty_expected` |
| `p-origin` | `# M:GAS-ORIGIN` | `tests/test_grok_audit_surface_probe.py::test_ledger_origin_refuses_an_unknown_origin` |
| `p-rebuild-bytes` | `# M:GAS-REBUILD-BYTES` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_one_byte` |
| `p-rebuild-original-once` | `# M:GAS-REBUILD-ORIGINAL-ONCE` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_a_twice_occurring_original` |
| `p-rebuild-section-twice` | `# M:GAS-REBUILD-SECTION-TWICE` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_two_seeds_in_one_section` |
| `p-rebuild-version-history` | `# M:GAS-REBUILD-VERSION-HISTORY` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_a_seed_under_version_history` |
| `p-rebuild-section-name` | `# M:GAS-REBUILD-SECTION-NAME` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_a_wrong_section_name` |
| `p-rebuild-seeded-once` | `# M:GAS-REBUILD-SEEDED-ONCE` | `tests/test_grok_audit_surface_probe.py::test_seed_rebuild_refuses_a_seeded_span_not_once` |

Each `replace` makes its condition never fire.

**Dependencies on other tasks**: Task 2.

---

## Task 4: build-root, content scan, reach check

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `build-root` steps 1–6 of D5 for a fresh root (`--dest-parent` or the default
`tempfile.mkdtemp(prefix=f"gas-root-d{k}-{purpose}-")`): the list read at the `--list-commit` commit with
`git cat-file blob`, D4 on the calibration sha, `git archive` read by `tarfile` with
`extractall(filter="data")`, list removal with a re-walk, `placements(doc, sources)`, then D6 and
D7, then `ROOT: READY`. The D6 normaliser is the one function for needle and haystack. The
`ROOT: READY` parser `parse_root_line` lands here, since its authority is this mode. `--reset` is
parsed (Task 2) and not handled until Task 5. The design writes `placements(doc)`; the plan passes
the parsed `sources` mapping as a second argument because D1 requires every in-process check to
receive the one parsed mapping.

**Code structure**:
```python
def normalise(data: bytes) -> str: ...
def read_exclusions(repo: Path, list_commit: str) -> tuple[list[tuple[str, str]], str, str]: ...  # (entries, list_commit sha40, list_blob)
def placements(doc: str, sources: dict[str, str]) -> dict[str, str]: ...  # live path -> tree path
def scan_root(root: Path, ledger: list[dict], sources: dict[str, str], doc: str) -> None: ...  # raises Refusal("leak:" + path)
def reach_check(root: Path) -> None: ...  # raises Refusal("root_git:" + path)
def build_root(args: argparse.Namespace) -> str: ...  # the ROOT: READY line
def parse_root_line(line: str) -> dict[str, str] | None: ...  # None unless every D2 field is present
def _mode_build_root(args: argparse.Namespace) -> int: ...
```

**Tests** (21):
- Leak (11): `test_leak_original_hit`, `test_leak_expected_hit`, `test_leak_hit_only_after_rewrap`,
  `test_leak_symlink_to_file`, `test_leak_symlink_to_dir`,
  `test_leak_original_in_paired_copy_with_other_sha`,
  `test_leak_expected_in_byte_identical_paired_copy`, `test_leak_on_the_seeded_target`,
  `test_leak_tar_member_leaving_the_root`, `test_leak_exclusion_line_outside_the_grammar`, and the
  must-not-refuse `test_original_in_byte_identical_own_source_copy_does_not_refuse`.
- Reach (4): `test_root_git_dot_git_directory`, `test_root_git_dot_git_file`,
  `test_root_git_root_nested_in_work_tree`, `test_root_git_ignores_ambient_git_dir_env`.
- Root build (4): `test_build_root_places_only_the_phase_pairs`,
  `test_build_root_removes_every_exclusion_entry`,
  `test_build_root_reads_the_list_from_the_commit_not_the_work_tree`,
  `test_build_root_prints_list_commit_and_blob`.
- Parser (2): `test_root_line_parser_reads_build_root_output`, and its must-not-parse fixture
  `test_root_line_parser_rejects_a_malformed_root_line` (D10: every token parser has one). It
  calls `parse_root_line` in process on (a) a `ROOT: READY` line rendered by `build-root` with its
  `list_blob=` field removed, and (b) a `ROOT: UNREADABLE reason=leak:x` line, and asserts `None`
  for each. Callers map `None` to their own reasons (`root_record:no_line` in `record-cycle`,
  `list_changed:unrecorded` in `rescore`).

**Acceptance Criteria**:
- [ ] AC-T4.1: Each leak test's last line is `ROOT: UNREADABLE reason=leak:` followed by the
  fixture's root-relative path (the list's tree path for the grammar test), exit 2; each reach test
  `reason=root_git:` followed by the path D7 names.
- [ ] AC-T4.2: The two must-not-refuse tests read `ROOT: READY`, exit 0.
- [ ] AC-T4.3: `test_build_root_prints_list_commit_and_blob` checks `list_commit=` and `list_blob=`
  against `git rev-parse HEAD` and `git rev-parse HEAD:docs/03-analysis/probes/grok-audit-surface/exclusions.txt`
  in the fixture repo.
- [ ] AC-T4.4: `placements` is the only function that maps a document to live paths (grep shows one
  definition and no second mapping).

**RED split**: 21 nodes; 21 F (no handler; `parse_root_line` absent), 0 P.

**Mutation rows** (14; markers 11):

| name | marker | test |
|---|---|---|
| `p-leak-original` | `# M:GAS-LEAK-ORIGINAL` | `tests/test_grok_audit_surface_probe.py::test_leak_original_hit` |
| `p-leak-expected` | `# M:GAS-LEAK-EXPECTED` | `tests/test_grok_audit_surface_probe.py::test_leak_expected_hit` |
| `p-leak-normalise` | `# M:GAS-LEAK-NORMALISE` | `tests/test_grok_audit_surface_probe.py::test_leak_hit_only_after_rewrap` |
| `p-leak-symlink-file` | `# M:GAS-LEAK-SYMLINK` | `tests/test_grok_audit_surface_probe.py::test_leak_symlink_to_file` |
| `p-leak-symlink-dir` | `# M:GAS-LEAK-SYMLINK` | `tests/test_grok_audit_surface_probe.py::test_leak_symlink_to_dir` |
| `p-leak-exempt-sha-paired` | `# M:GAS-LEAK-EXEMPT-SHA` | `tests/test_grok_audit_surface_probe.py::test_leak_original_in_paired_copy_with_other_sha` |
| `p-leak-exempt-sha-target` | `# M:GAS-LEAK-EXEMPT-SHA` | `tests/test_grok_audit_surface_probe.py::test_leak_on_the_seeded_target` |
| `p-leak-exempt-original-only` | `# M:GAS-LEAK-EXEMPT-ORIGINAL-ONLY` | `tests/test_grok_audit_surface_probe.py::test_leak_expected_in_byte_identical_paired_copy` |
| `p-leak-tar` | `# M:GAS-LEAK-TAR` | `tests/test_grok_audit_surface_probe.py::test_leak_tar_member_leaving_the_root` |
| `p-leak-list-grammar` | `# M:GAS-LEAK-LIST-GRAMMAR` | `tests/test_grok_audit_surface_probe.py::test_leak_exclusion_line_outside_the_grammar` |
| `p-reach-dotgit-dir` | `# M:GAS-REACH-DOTGIT` | `tests/test_grok_audit_surface_probe.py::test_root_git_dot_git_directory` |
| `p-reach-dotgit-file` | `# M:GAS-REACH-DOTGIT` | `tests/test_grok_audit_surface_probe.py::test_root_git_dot_git_file` |
| `p-reach-revparse` | `# M:GAS-REACH-REVPARSE` | `tests/test_grok_audit_surface_probe.py::test_root_git_root_nested_in_work_tree` |
| `p-parse-root` | `# M:GAS-PARSE-ROOT` | `tests/test_grok_audit_surface_probe.py::test_root_line_parser_rejects_a_malformed_root_line` |

**Dependencies on other tasks**: Task 3.

---

## Task 5: the S1 root reset

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test file**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `build-root --reset` per D5, "Resetting the S1 root between its cycles": the mode
checks `--reset` against `--dest-parent` first (`ResetArgsConflict`, `# M:GAS-RESET-EXCLUSIVE`), then
the purpose (below), then the five target guards in D5's order (`# M:GAS-RESET-ABS`,
`# M:GAS-RESET-ISDIR`, `# M:GAS-RESET-TMPDIR`, `# M:GAS-RESET-PREFIX`, `# M:GAS-RESET-REACH`), and only
then builds the expected tree (steps 1–5 into a fresh `mkdtemp`), makes the live root equal to it,
re-walks it (`RootResetMismatch`, `# M:GAS-RESET-REWALK`), runs step 6 on the live root
(`# M:GAS-RESET-SCAN`, `# M:GAS-RESET-STEP6-REACH`), removes the expected tree, and prints
the published `RESET:` line (D5) and then the `ROOT: READY` token with `path=` the live root.

**The reset never follows a link (carry 2, destructive class).** A symlinked placed document, a
symlinked by-product directory, or a symlinked directory on the path to a placed document would let
the reset write or delete outside the root before step 6 sees the link. The reset therefore walks the
live root with `os.walk(followlinks=False)` and judges every entry by `os.lstat`: an entry that is a
link is removed with `os.unlink` (never `shutil.rmtree`, never by its target), whether or not its
path is in the expected tree (`# M:GAS-RESET-NOFOLLOW-REMOVE`). Every ancestor directory between
the root and a path `restore_expected` writes is `lstat`-ed, and an ancestor that is a link is
unlinked and recreated as a real directory before the write (`# M:GAS-RESET-NOFOLLOW-PARENT`).
The file itself is opened with `os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW`
(`# M:GAS-RESET-NOFOLLOW-WRITE`). Measured on this Mac: that open of a link fails with `ELOOP`,
and `restore_expected` then unlinks the link and creates the file with
`O_CREAT | O_EXCL | O_NOFOLLOW`. `O_NOFOLLOW` guards only the last path component (measured: an
`O_NOFOLLOW` open through a linked parent directory wrote the outside file), which is why the
ancestor check is a separate guard. Reproduce (the temporary directory removes itself):

```bash
/opt/anaconda3/bin/python3.11 -c '
import os,errno,tempfile
with tempfile.TemporaryDirectory() as d:
    v=os.path.join(d,"victim"); open(v,"w").write("S"); l=os.path.join(d,"link"); os.symlink(v,l)
    try: os.open(l, os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW); print("opened")
    except OSError as e: print("link:", errno.errorcode[e.errno])
    o=os.path.join(d,"out"); os.mkdir(o); open(os.path.join(o,"doc"),"w").write("S"); os.symlink(o, os.path.join(d,"feat"))
    fd=os.open(os.path.join(d,"feat","doc"), os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW); os.write(fd,b"X"); os.close(fd)
    print("parent link, outside file now:", open(os.path.join(o,"doc")).read())'
# link: ELOOP
# parent link, outside file now: X
```

A real directory absent from the expected tree is removed with `shutil.rmtree`, which does not
follow the links it meets inside it.

**Which test can see which guard (audit cycle 1; axis: a link present when a write happens).**
`remove_absent` runs first and unlinks every link in the live root, so by the time
`restore_expected` runs, an end-to-end reset fixture has no link left. A write-through or
parent-through mutant of `restore_expected` is therefore invisible to any end-to-end fixture: it
survives, and the end-to-end fixture shows nothing about it. The two restore guards are tested
at `restore_expected`'s own boundary instead. Their tests call
`probe.restore_expected(live, expected)` in process (loaded with `load_probe`) on a live tree that
holds the link at that moment. `remove_absent`'s guard keeps its end-to-end fixture. Residual,
stated exactly: a link created inside the root *between* `restore_expected`'s check of a path and
its write of that path (a concurrent writer) is outside every guard. The reset assumes no writer
runs in the root, and the post-reset `lstat` re-walk (`RootResetMismatch`) reports a link that
is present afterwards, but not a write that has already happened outside.

**`--reset` requires `--purpose s1` (carry 13).** Guard 4's prefix is the literal `s1`, so
`--purpose s2v1 --reset` on an S1 root passes all five guards and would reset the S1 root under a
`purpose=s2v1` token: the S1 root reused for S2, which D5 forbids ("The S1 root is never reused for
S2"). Right after the exclusivity check, `--reset` with any `--purpose` other than `s1` raises
`ResetPurposeNotS1` (`# M:GAS-RESET-PURPOSE`), printed by the last resort as
`ROOT: UNREADABLE reason=internal:ResetPurposeNotS1`, before anything is removed. This is a guard the
design does not name; it is reported to the design as owed.

**Fixtures (carry 3).** Every reset fixture builds its S1 root with the default parent (no
`--dest-parent`, so the root is directly under `tempfile.gettempdir()`) and with `--purpose s1 --doc d1`,
and resets it with the same `--doc d1 --purpose s1` and the root's own `--list-commit`, so guards 3
and 4 pass; the only exceptions are the fixtures whose trigger is that value
(`…_outside_the_tempdir` uses a `tmp_path` directory, `…_another_documents_root` a
`gas-root-d2-s1-` directory with `--doc d1`, `…_non_s1_purpose` `--purpose s2v1`). Each built root is
removed by the fixture's finalizer. The carry-2 fixtures put every link target under `tmp_path`, so a
mutant that follows a link can only damage the test's own directory.

**OPEN-DECISION: D5's post-reset re-walk raises `RootResetMismatch` before step 6 runs, so
`test_build_root_reset_runs_the_reach_check` and `test_build_root_reset_rescans_after_removal`, whose
in-process replaced removal step leaves an extra path in the live root, cannot reach the `leak:` or
`root_git:` token they assert (carry 1, must) — resolve in 5d.** Two implementations satisfy both
tests: (a) reorder D5 so step 6 (scan, then reach) runs on the live root before the re-walk
assertion; or (b) keep D5's order and have those two fixtures also replace `rewalk_matches` with a
function that returns without raising, so step 6 is reached. (b) changes only the two fixtures; (a)
changes D5's order of operations and is owed to the design if chosen. Either way
`test_build_root_reset_mismatch_is_internal` keeps its token. The RED at 5d cannot show the choice
(the reset is absent then); the first GREEN attempt shows which fixture is unsatisfiable under D5 as
written, and the choice is recorded in the Task's GREEN report.

**Code structure**:
```python
class ResetArgsConflict(ProbeRefusal): ...
class ResetPurposeNotS1(ProbeRefusal): ...
class ResetTargetNotAbsolute(ProbeRefusal): ...
class ResetTargetNotDirectory(ProbeRefusal): ...
class ResetTargetOutsideTempdir(ProbeRefusal): ...
class ResetTargetPrefix(ProbeRefusal): ...
class RootResetMismatch(ProbeRefusal): ...
def check_reset_target(target: str, doc: str) -> Path: ...
def remove_absent(live: Path, expected: Path) -> int: ...
def restore_expected(live: Path, expected: Path) -> int: ...
def rewalk_matches(live: Path, expected: Path) -> None: ...
def reset_root(args: argparse.Namespace) -> str: ...  # the ROOT: READY line
```

**Tests** (15):
- From D5 (11): `test_build_root_reset_removes_by_products_and_restores_placed_files`,
  `test_build_root_reset_rescans_after_removal`, `test_build_root_reset_runs_the_reach_check`,
  `test_build_root_reset_mismatch_is_internal`, `test_build_root_reset_and_dest_parent_are_exclusive`,
  `test_build_root_reset_refuses_an_empty_target`, `test_build_root_reset_refuses_a_missing_target`,
  `test_build_root_reset_refuses_a_target_outside_the_tempdir`,
  `test_build_root_reset_refuses_another_documents_root`, `test_build_root_reset_refuses_a_git_target`,
  and the must-not-refuse `test_build_root_reset_accepts_the_physical_spelling_of_its_root`.
- Carry 2 (3, plan-added), each asserting both directions of one link kind — the link is not
  followed (the outside target is unchanged) and the link is acted on (it is gone or replaced):
  `test_build_root_reset_does_not_delete_through_a_symlinked_by_product_dir` (end to end:
  `.h-mad/pass-logs` in the live root is a link to `tmp_path/outside/logs/` holding a sentinel file;
  afterwards that directory and its sentinel exist with unchanged bytes, the live root has no
  `.h-mad/pass-logs` entry, and the token is `ROOT: READY`);
  `test_restore_expected_does_not_write_through_a_symlinked_placed_document` (in process, at
  `restore_expected`'s boundary: a live tree equal to `expected` except that the seeded target's path
  is a link to `tmp_path/outside/victim.md` holding sentinel bytes; after
  `restore_expected(live, expected)` the victim's bytes are unchanged and the live path is a regular
  file whose sha256 equals the expected file's);
  `test_restore_expected_does_not_write_through_a_symlinked_parent_directory` (in process: the seeded
  target's parent directory in the live tree is a link to `tmp_path/outside/features/`, which holds a
  sentinel file of the target's name; afterwards the sentinel's bytes are unchanged, the live parent
  is a real directory, and the file in it equals the expected file).
- Carry 13 (1, plan-added): `test_build_root_reset_refuses_a_non_s1_purpose` (an S1 root of `d1`,
  reset with `--purpose s2v1`: `ROOT: UNREADABLE reason=internal:ResetPurposeNotS1`, and a sentinel
  planted in the root is unchanged).

**Acceptance Criteria**:
- [ ] AC-T5.1: Each refusal test asserts its exact token as D5's Test Plan entry states it, that
  its sentinel is still there with its bytes unchanged (the missing-target test: the path is still
  absent), and that `n = stderr.count("Traceback")` is 0. Each of these refusals is a declared
  `ProbeRefusal` class other than `UsageError`, so this is the traceback-absence check for the
  non-usage refusals.
- [ ] AC-T5.2: `test_build_root_reset_removes_by_products_and_restores_placed_files` asserts the path
  set and every sha256 equal a fresh build's, the published line `RESET: removed=` with the planted
  count and `restored=1`, and the original `ROOT: READY` line as the token.
- [ ] AC-T5.3: The three carry-2 tests pass, and `grep -n 'rmtree' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` shows `rmtree` called
  only on paths whose `os.lstat` is a directory and not a link.
- [ ] AC-T5.4: The OPEN-DECISION above is resolved and the choice is stated in the GREEN report.

**RED split**: 15 nodes; 15 F (at RED `--reset` is parsed and ignored, so every end-to-end test sees
a fresh root's token or no refusal, and the two `restore_expected` tests find no such attribute), 0 P.

**Mutation rows** (13; markers 13). Each `replace` makes its condition never fire, except the three
no-follow rows, whose `replace` follows the link: the unlink becomes removal of the resolved target
(its target is under `tmp_path`); `O_NOFOLLOW` is dropped from the first open; the ancestor check is
skipped. Each of those three mutants then writes or deletes through the link that its own fixture
holds at that moment, so the kill is by assertion on the outside sentinel, never a crash:

| name | marker | test |
|---|---|---|
| `p-reset-exclusive` | `# M:GAS-RESET-EXCLUSIVE` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_and_dest_parent_are_exclusive` |
| `p-reset-purpose` | `# M:GAS-RESET-PURPOSE` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_a_non_s1_purpose` |
| `p-reset-abs` | `# M:GAS-RESET-ABS` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_an_empty_target` |
| `p-reset-isdir` | `# M:GAS-RESET-ISDIR` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_a_missing_target` |
| `p-reset-tmpdir` | `# M:GAS-RESET-TMPDIR` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_a_target_outside_the_tempdir` |
| `p-reset-prefix` | `# M:GAS-RESET-PREFIX` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_another_documents_root` |
| `p-reset-reach` | `# M:GAS-RESET-REACH` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_refuses_a_git_target` |
| `p-reset-rewalk` | `# M:GAS-RESET-REWALK` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_mismatch_is_internal` |
| `p-reset-scan` | `# M:GAS-RESET-SCAN` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_rescans_after_removal` |
| `p-reset-step6-reach` | `# M:GAS-RESET-STEP6-REACH` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_runs_the_reach_check` |
| `p-reset-nofollow-write` | `# M:GAS-RESET-NOFOLLOW-WRITE` | `tests/test_grok_audit_surface_probe.py::test_restore_expected_does_not_write_through_a_symlinked_placed_document` |
| `p-reset-nofollow-remove` | `# M:GAS-RESET-NOFOLLOW-REMOVE` | `tests/test_grok_audit_surface_probe.py::test_build_root_reset_does_not_delete_through_a_symlinked_by_product_dir` |
| `p-reset-nofollow-parent` | `# M:GAS-RESET-NOFOLLOW-PARENT` | `tests/test_grok_audit_surface_probe.py::test_restore_expected_does_not_write_through_a_symlinked_parent_directory` |

**Dependencies on other tasks**: Task 4.

---

## Task 6: record-cycle and commit-data

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `record-cycle` per D8 (`--feature`, `--phase`, `--cycle` read from the command
file; the stem's single prefix of the form `audit_${feature}_${phase}_cycle${cycle}_run`, matching the wrapper's
`stem="${stem_dir}/audit_${feature}_${phase}_cycle${cycle}_run…"` in `_cmd_audit_cycle`; the D3 file
map; only this cycle's `v<N>` reports, sidecars and pass logs; `root.txt` from `--root-record`;
`mkdir(parents=True, exist_ok=True)`; the re-list and `files=`). `commit-data` per D9 (temporary
index, `hash-object`, `update-index --cacheinfo`, `write-tree`, `commit-tree`, `update-ref` with the
expected old value, the re-read). The stem files are copied byte for byte, so `p1.log` is exactly
the file the wrapper passed as `--log` (`log[$i]="${stem}_p${i}.log"`); that is what keeps D11 step
3's wrong-file guard unreachable on real inputs (carry 14), and a plan-added test pins it. D2 names
three `record-cycle` reasons the design's Test Plan gives no fixture (`input_missing:`,
`stem_prefix:`, `command_unparseable:`); each gets one here, plan-added and reported to the design.

**Code structure**:
```python
def record_cycle(args: argparse.Namespace) -> str: ...  # the RECORD: OK line
def commit_data(args: argparse.Namespace) -> str: ...   # the COMMIT: OK line
def _git(repo: Path, *argv: str, env: dict[str, str] | None = None, stdin: bytes | None = None) -> subprocess.CompletedProcess: ...
def _mode_record_cycle(args: argparse.Namespace) -> int: ...
def _mode_commit_data(args: argparse.Namespace) -> int: ...
```

**Tests** (15):
- From D5/D8/D9 (10): `test_record_cycle_writes_root_txt`,
  `test_record_cycle_refuses_a_root_record_without_a_line`,
  `test_record_cycle_refuses_a_root_record_for_another_root`,
  `test_record_cycle_refuses_stdout_without_auditcycle`,
  `test_record_cycle_copies_only_its_own_cycle_reports`,
  `test_commit_data_never_touches_work_tree_or_index`, `test_commit_data_refuses_an_unknown_parent`,
  `test_commit_data_refuses_a_moved_ref`, `test_commit_data_refuses_outside_calibration_dir`,
  `test_commit_data_rereads_the_ref` (in process: the probe's ref read after `update-ref` replaced to
  return another oid; `COMMIT: REFUSED reason=ref_unconfirmed`).
- Plan-added (5): `test_record_cycle_copies_stem_files_byte_for_byte` (carry 14: every copied file's
  sha256 equals its stem source's), `test_record_cycle_refuses_a_missing_input` (`--stdout` absent:
  `RECORD: REFUSED reason=input_missing:` and that path), `test_record_cycle_refuses_zero_stem_prefixes`
  (`reason=stem_prefix:0`), `test_record_cycle_refuses_two_stem_prefixes` (`reason=stem_prefix:2`),
  `test_record_cycle_refuses_a_command_without_cycle_flags` (a command file lacking `--cycle`:
  `reason=command_unparseable:` and that file).

**Acceptance Criteria**:
- [ ] AC-T6.1: Each refusal test asserts its exact `RECORD: REFUSED` or `COMMIT: REFUSED` token and
  exit 2, then the state that refusal leaves (axis: when the refusal fires relative to `update-ref`).
  - Pre-write refusals (`parent_unknown`, `ref_moved`, `outside_calibration_dir`) fire before
    `update-ref` runs. Their tests assert that
    `git rev-parse --verify refs/heads/calibration/grok-audit-surface` reads the pre-test value (or
    fails, when the ref did not exist).
  - The post-write refusal (`ref_unconfirmed`, `test_commit_data_rereads_the_ref`) fires after a
    successful `update-ref`. D9 specifies no rollback, and the probe performs none, so the test
    asserts the ref's actual value: the commit `commit-tree` made, read through a real
    `git rev-parse` outside the replaced function. Residual, stated exactly: a `ref_unconfirmed`
    refusal can leave the ref moved. The operator reads the ref with `git rev-parse` before
    re-running, and the next `commit-data` takes that value as `--parent` or refuses `ref_moved`.
  - `record-cycle` refusals assert that no dest file was written.
- [ ] AC-T6.2: `test_commit_data_never_touches_work_tree_or_index` asserts `git status --porcelain`
  and the sha256 of `.git/index` are unchanged across the call.

**RED split**: 15 nodes; 15 F (no handlers), 0 P.

**Mutation rows** (11; markers 10):

| name | marker | test |
|---|---|---|
| `p-record-root-line` | `# M:GAS-RECORD-ROOT-LINE` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_a_root_record_without_a_line` |
| `p-record-root-path` | `# M:GAS-RECORD-ROOT-PATH` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_a_root_record_for_another_root` |
| `p-record-auditcycle` | `# M:GAS-RECORD-AUDITCYCLE` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_stdout_without_auditcycle` |
| `p-record-input` | `# M:GAS-RECORD-INPUT` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_a_missing_input` |
| `p-record-stem-zero` | `# M:GAS-RECORD-STEM-PREFIX` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_zero_stem_prefixes` |
| `p-record-stem-two` | `# M:GAS-RECORD-STEM-PREFIX` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_two_stem_prefixes` |
| `p-record-command` | `# M:GAS-RECORD-COMMAND` | `tests/test_grok_audit_surface_probe.py::test_record_cycle_refuses_a_command_without_cycle_flags` |
| `p-commit-parent` | `# M:GAS-COMMIT-PARENT` | `tests/test_grok_audit_surface_probe.py::test_commit_data_refuses_an_unknown_parent` |
| `p-commit-ref-moved` | `# M:GAS-COMMIT-REF-MOVED` | `tests/test_grok_audit_surface_probe.py::test_commit_data_refuses_a_moved_ref` |
| `p-commit-outside` | `# M:GAS-COMMIT-OUTSIDE` | `tests/test_grok_audit_surface_probe.py::test_commit_data_refuses_outside_calibration_dir` |
| `p-commit-reread` | `# M:GAS-COMMIT-REREAD` | `tests/test_grok_audit_surface_probe.py::test_commit_data_rereads_the_ref` |

**Dependencies on other tasks**: Task 4 (`parse_root_line` reads `--root-record`).

---

## Task 7: smoke

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_smoke.py` (create),
`h-mad/tests/test_grok_audit_surface_probe.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `smoke` per D11, with D10's `parse_auditcycle` and `parse_effort_items` (each with a
must-parse fixture rendered by `h_mad_audit_cycle.render` / `_effort_items` and a must-not-parse
fixture), the UNREADABLE checks in D11's fixed order, the five step-3 forms, the reasons in AC-1.7
order, the published `VOCAB:`, `ROOT-ACCEPT:`, `TIMEOUT:` and `GROK-BINARY:` lines, and exit 0 on
PASS/FAIL, 2 on UNREADABLE. `_gate_token` raises `h_mad_audit_cycle.OperationalError` when the gate
prints no `GATE:` line; the smoke maps that to `input_unparseable:` and the collected report's path.
The smoke assigns each input's path to the module-level `_OPEN_INPUT` immediately before it opens
that input (Task 2's `refusal_token` reads it), so the last resort's `input_unparseable:` path is
that input (D1). Fixture grok logs come from `grokfixtures` (`f0_text`, `f_trunc`, `f0_with_completed`).

**One reader for the grok log's type set (carry 5).** `grok_log_types(text)` is the one function
step 2, `vocab_missing` and the `VOCAB:` lines read. Its line acceptance is `scan_grok`'s in every
step but one: it splits on `"\n"`, skips a line whose `json.loads` raises `ValueError` or
`RecursionError`, skips a non-dict, and takes a string `type`; the one difference is that it does not
apply `scan_grok`'s `_json_deeper_than(event, GROK_MAX_DEPTH)` skip and does not filter to
`_GROK_TYPES`. So the open class of lines that this reader counts and `scan_grok` skips is exactly:
lines that parse to a dict with a string `type` and hold a value nested deeper than `GROK_MAX_DEPTH`.
That is D11 residual (2) stated exactly. A line whose `json.loads` raises `RecursionError` is skipped
by both readers, so it is not in residual (2); D11's sentence naming it there, and its "guaranteed"
for `unparseable` (which holds only for logs outside this class), are reported to the design.

**Residual-(2) fixture depth (carry 15).** `test_smoke_deep_grok_types_with_unparseable_item_is_the_stated_residual`
builds its nested value from the imported constant, never a literal: `v = 0`, then `GROK_MAX_DEPTH`
times `v = [v]`, and each line is `{"type": t, "x": v}`. It first asserts
`_json_deeper_than(event, GROK_MAX_DEPTH)` is true for each line and that `measure_effort` gives shape
`unparseable`.

**Unrecognised Effort item (carry 4).** D11 step 3's default branch (an item in none of the five
forms) gets its own fixture, `test_smoke_unrecognised_effort_item_refuses`: a `grok/auditcycle.txt`
whose `p1` Effort item is `p1 measured by a renderer this design does not name` beside a `p1.log`
holding `f0_text()`; `SMOKE: UNREADABLE reason=input_unparseable:` followed by the
`grok/auditcycle.txt` path, exit 2.

**Wrong-file fixtures are synthetic pairings (carry 14).** Step 2 refuses a recorded wrong file first,
so the three wrong-file fixtures put `f0_text()` in `grok/p1.log` beside the wrong-file item; the
wrapper does not produce that pairing, and Task 6's byte-for-byte copy pin is what keeps it from
arising on real records.

**A wrong-file UNREADABLE cannot be cleared by AC-1.7's remedy (carry 10).** A `missing`, `empty` or
`codex-text` item is rendered by the wrapper into `auditcycle.txt`, so restoring inputs and deriving
again from the same passes gives the same token; only a new smoke (a new reading) clears it. The spec
gap is reported; Task 16's runbook states it beside the UNREADABLE remedy.

**Code structure**:
```python
AUDITCYCLE_RE = re.compile(r"^AUDITCYCLE: (PASS|FAIL|UNVERIFIED)( \S+)*$")
GROK_ITEM_RE = re.compile(r"^p1 tools=\d+ ok=\d+ unresolved=\d+ thinking=\d+ format=grok( |$)")
COUNTS_ITEM_RE = re.compile(r"^p1 tools=\d+ ok=\d+ failed=\d+ thinking=\d+( |$)")
def parse_auditcycle(text: str) -> dict: ...
def parse_effort_items(text: str) -> list[str] | None: ...  # None for a malformed Effort block
def grok_log_types(text: str) -> dict[str, list[dict]]: ...  # type -> its events
def effort_form(item: str) -> str: ...  # "grok" | "truncated" | "counts" | "wrong-file" | "unknown"
def vocab_sets(vocab_py: Path, vocab_sh: Path) -> tuple[frozenset[str], frozenset[str]]: ...
def delivered(cycle_dir: Path, parsed: dict) -> bool: ...
def smoke(data: Path, vocab_py: Path, vocab_sh: Path) -> tuple[list[str], str]: ...  # (published lines, token)
def _mode_smoke(args: argparse.Namespace) -> int: ...
```

**Tests** — smoke module (42), each asserting its exit code beside its exact token:
- PASS and FAIL (11): `test_smoke_pass`, `test_smoke_pass_on_out_delivery`, `test_smoke_truncated`,
  `test_smoke_vocab_split`, `test_smoke_vocab_missing_end`, `test_smoke_vocab_missing_tool_call`,
  `test_smoke_vocab_missing_tool_call_update`, `test_smoke_no_delivery`,
  `test_smoke_no_delivery_on_unscorable`, `test_smoke_nongit_root_refused_grok`,
  `test_smoke_nongit_root_refused_agy`.
- UNREADABLE (3): `test_smoke_input_missing`, `test_smoke_input_missing_delivered_collected_report`,
  `test_smoke_input_unparseable`.
- Step 3 (11): `test_smoke_drifted_log_with_unparseable_item_fails`,
  `test_smoke_drifted_log_with_parsed_item_fails`,
  `test_smoke_effort_codex_text_item_refuses_as_wrong_file`,
  `test_smoke_effort_missing_item_refuses_as_wrong_file`,
  `test_smoke_effort_empty_item_refuses_as_wrong_file`, `test_smoke_unrecognised_effort_item_refuses`
  (plan-added, carry 4), `test_smoke_parsed_item_with_all_three_types_is_the_stated_residual`,
  `test_smoke_deep_grok_types_with_unparseable_item_is_the_stated_residual`,
  `test_smoke_effort_grok_item_with_targets_is_grok`, `test_grok_item_predicate_matches_the_renderer`
  (derives the seven `measure_effort` shapes with the D11 regex and maps each to its one form),
  `test_truncated_predicate_matches_the_renderer`.
- Must not fail or refuse (4): `test_smoke_codex_refusal_is_not_a_reason`,
  `test_smoke_out_of_vocabulary_type_is_not_a_reason`,
  `test_smoke_halted_agy_cycle_is_a_refusal_not_unreadable`, `test_smoke_codex_text_log_is_not_an_input`.
- Grok binary (2): `test_smoke_publishes_grok_binary_line`,
  `test_smoke_grok_binary_unrecorded_is_not_unreadable`.
- Ordering and contracts (4): `test_smoke_two_reasons_in_order`, `test_smoke_coupled_reasons_in_order`,
  `test_smoke_unreadable_outranks_fail`, `test_smoke_prints_timeout_derivation`.
- Opposed pairs (7): `test_m3_d1_end_event_beside_truncated_item_is_truncated`,
  `test_m3_d2_no_end_beside_grok_item_is_not_truncated`,
  `test_m4_e1_report_file_inputs_beside_delivered_none_is_no_delivery`,
  `test_m4_e2a_none_inputs_beside_report_file_is_delivered`,
  `test_m4_e2b_none_inputs_beside_out_is_delivered`,
  `test_m5_f1_unverified_token_beside_busy_log_refuses_root`,
  `test_m5_f2_pass_token_beside_hollow_log_accepts_root`. Each first runs its field's authority on the
  raw inputs (D10: `scan_grok`; `collect` with `PassSpec(index, report_path, out_path, rc, log_path)`
  and `grace=0`; `measure_effort` and `combine`) and asserts the verdict opposite to the recorded
  token.

11 + 3 + 11 + 4 + 2 + 4 + 7 = 42.

**Tests** — probe module (4): `test_auditcycle_parser_reads_render_output`,
`test_auditcycle_parser_rejects_two_lines`, `test_effort_parser_reads_effort_items_output`, and the
Effort parser's must-not-parse fixture `test_effort_parser_rejects_a_malformed_effort_block`. It
calls `parse_effort_items` in process on (a) an `Effort:` line followed by an item line without the
`- ` bullet `render` writes (`lines.extend(f"- {item}" for item in effort)` in
`h_mad_audit_cycle.render`), and (b) an `Effort:` line followed directly by the `[H-MAD]` line, and
asserts `None` for each.

**Acceptance Criteria**:
- [ ] AC-T7.1: Every coupled-reason test asserts the full list, e.g. `test_smoke_no_delivery` reads
  exactly `SMOKE: FAIL reason=no_delivery,nongit_root_refused:grok`.
- [ ] AC-T7.2: The two drifted-log tests read exactly
  `SMOKE: FAIL reason=vocab_missing:end,vocab_missing:tool_call,vocab_missing:tool_call_update`, exit 0.
- [ ] AC-T7.3: `grok_log_types` is the only function in the probe that iterates a grok log's lines
  (one definition; step 2, `vocab_missing` and `VOCAB:` call it).
- [ ] AC-T7.4: The smoke test module imports `GROK_MAX_DEPTH` and `_json_deeper_than` from
  `h_mad_review_evidence` and holds no literal `65`.
- [ ] AC-T7.5: The smoke module adds `tests/test_grok_audit_surface_smoke.py` to the spec's `command`
  after the probe module.

**RED split**: 46 nodes; 46 F (no `smoke` handler, no parsers), 0 P.

**Mutation rows** (25; markers 15). Each `replace` makes its condition never fire, except the four
step-3 refusal rows (`p-smoke-effort-codex-text`, `p-smoke-effort-missing`, `p-smoke-effort-empty`,
`p-smoke-effort-unknown`): a wrong-file branch that merely stops firing falls to the
unrecognised-item refusal, which prints the same token, so that mutant is equivalent; these rows
instead turn the refusal into acceptance (the item reaches the reasons, where the `f0_text()` log
fires none, so the token becomes `SMOKE: PASS`). The three-alternative sites (`VOCAB-MISSING` over
`end`, `tool_call`, `tool_call_update`; `ACCEPTS` over grok and agy; `DELIVERED` over `report-file`
and `out`) get one row per alternative, each removing that alternative alone.

| name | marker | test |
|---|---|---|
| `p-smoke-delivered-report-file` | `# M:GAS-SMOKE-DELIVERED` | `tests/test_grok_audit_surface_smoke.py::test_smoke_pass` |
| `p-smoke-delivered-out` | `# M:GAS-SMOKE-DELIVERED` | `tests/test_grok_audit_surface_smoke.py::test_smoke_pass_on_out_delivery` |
| `p-smoke-truncated` | `# M:GAS-SMOKE-TRUNCATED` | `tests/test_grok_audit_surface_smoke.py::test_smoke_truncated` |
| `p-smoke-truncated-m3` | `# M:GAS-SMOKE-TRUNCATED` | `tests/test_grok_audit_surface_smoke.py::test_m3_d1_end_event_beside_truncated_item_is_truncated` |
| `p-smoke-vocab-split` | `# M:GAS-SMOKE-VOCAB-SPLIT` | `tests/test_grok_audit_surface_smoke.py::test_smoke_vocab_split` |
| `p-smoke-vocab-missing-end` | `# M:GAS-SMOKE-VOCAB-MISSING` | `tests/test_grok_audit_surface_smoke.py::test_smoke_vocab_missing_end` |
| `p-smoke-vocab-missing-tool-call` | `# M:GAS-SMOKE-VOCAB-MISSING` | `tests/test_grok_audit_surface_smoke.py::test_smoke_vocab_missing_tool_call` |
| `p-smoke-vocab-missing-tool-call-update` | `# M:GAS-SMOKE-VOCAB-MISSING` | `tests/test_grok_audit_surface_smoke.py::test_smoke_vocab_missing_tool_call_update` |
| `p-smoke-no-delivery` | `# M:GAS-SMOKE-NO-DELIVERY` | `tests/test_grok_audit_surface_smoke.py::test_smoke_no_delivery` |
| `p-smoke-no-delivery-unscorable` | `# M:GAS-SMOKE-NO-DELIVERY` | `tests/test_grok_audit_surface_smoke.py::test_smoke_no_delivery_on_unscorable` |
| `p-smoke-no-delivery-m4` | `# M:GAS-SMOKE-NO-DELIVERY` | `tests/test_grok_audit_surface_smoke.py::test_m4_e1_report_file_inputs_beside_delivered_none_is_no_delivery` |
| `p-smoke-accepts-grok` | `# M:GAS-SMOKE-ACCEPTS` | `tests/test_grok_audit_surface_smoke.py::test_smoke_nongit_root_refused_grok` |
| `p-smoke-accepts-agy` | `# M:GAS-SMOKE-ACCEPTS` | `tests/test_grok_audit_surface_smoke.py::test_smoke_nongit_root_refused_agy` |
| `p-smoke-accepts-m5` | `# M:GAS-SMOKE-ACCEPTS` | `tests/test_grok_audit_surface_smoke.py::test_m5_f1_unverified_token_beside_busy_log_refuses_root` |
| `p-smoke-missing-auditcycle` | `# M:GAS-SMOKE-MISSING-AUDITCYCLE` | `tests/test_grok_audit_surface_smoke.py::test_smoke_input_missing` |
| `p-smoke-missing-collected` | `# M:GAS-SMOKE-MISSING-COLLECTED` | `tests/test_grok_audit_surface_smoke.py::test_smoke_input_missing_delivered_collected_report` |
| `p-smoke-unparseable-auditcycle` | `# M:GAS-SMOKE-UNPARSEABLE-AUDITCYCLE` | `tests/test_grok_audit_surface_smoke.py::test_smoke_input_unparseable` |
| `p-smoke-effort-counts-unparseable` | `# M:GAS-SMOKE-EFFORT-COUNTS` | `tests/test_grok_audit_surface_smoke.py::test_smoke_drifted_log_with_unparseable_item_fails` |
| `p-smoke-effort-counts-parsed` | `# M:GAS-SMOKE-EFFORT-COUNTS` | `tests/test_grok_audit_surface_smoke.py::test_smoke_drifted_log_with_parsed_item_fails` |
| `p-smoke-effort-codex-text` | `# M:GAS-SMOKE-EFFORT-CODEX-TEXT` | `tests/test_grok_audit_surface_smoke.py::test_smoke_effort_codex_text_item_refuses_as_wrong_file` |
| `p-smoke-effort-missing` | `# M:GAS-SMOKE-EFFORT-UNREADABLE` | `tests/test_grok_audit_surface_smoke.py::test_smoke_effort_missing_item_refuses_as_wrong_file` |
| `p-smoke-effort-empty` | `# M:GAS-SMOKE-EFFORT-UNREADABLE` | `tests/test_grok_audit_surface_smoke.py::test_smoke_effort_empty_item_refuses_as_wrong_file` |
| `p-smoke-effort-unknown` | `# M:GAS-SMOKE-EFFORT-UNKNOWN` | `tests/test_grok_audit_surface_smoke.py::test_smoke_unrecognised_effort_item_refuses` |
| `p-parse-auditcycle-one` | `# M:GAS-PARSE-AUDITCYCLE-ONE` | `tests/test_grok_audit_surface_probe.py::test_auditcycle_parser_rejects_two_lines` |
| `p-parse-effort` | `# M:GAS-PARSE-EFFORT` | `tests/test_grok_audit_surface_probe.py::test_effort_parser_rejects_a_malformed_effort_block` |

**Dependencies on other tasks**: Task 2.

---

## Task 8: extract

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `wiring` — the extractor's counts must come from the gate (`_gate.classify`) and its
grouping decision from `_gate._collapses`; the walk, the blinding, the hints, the stands rule and
`cycle_token` are new behaviour carried in the same Task, and their RED split is stated below.
**WIRE 1**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py:extract_report` → `h_mad_audit_gate.classify` (the `must_count` field)
**WIRE-PIN 1**: `h-mad/tests/test_grok_audit_surface_probe.py::test_must_count_mismatch_through_production_path`
**WIRE 2**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py:report_findings` → `h_mad_audit_gate._collapses`
**WIRE-PIN 2**: `h-mad/tests/test_grok_audit_surface_probe.py::test_extract_parity_collapsing_group`
**WIRE 3**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py:extract_report` → `h_mad_audit_gate.classify` (the `should_count` field)
**WIRE-PIN 3**: `h-mad/tests/test_grok_audit_surface_probe.py::test_should_findings_are_written_on_a_count_difference`

**Description**: `extract` per D12: `extract_all(tree, s2_dir, sources)` (the one function `score`
calls for re-extraction; the design writes `extract_all(tree, s2_dir)`, and the plan adds the parsed
`sources` mapping as a third, required argument for the same D1 reason it adds it to `placements`,
since quote resolution calls `placements`; Task 9's `score` passes its own parsed `sources`), `report_findings(text)` making `_gate`'s own calls in `_section_detail`'s order
(`_payload`, `_is_none_sentinel`, `_bullet_groups`, `_collapses(group, set())` on the line marked
`# M:GAS-COLLAPSE-WIRE`, `_flat_findings`, `_bullet_remainder`, the fail-safe), the section split as
`classify_detail` does it over `_gate.BLOCKING_SECTIONS`, and `extract_report` written as D12's five
lines in that order, with the two marked wire lines. The stands rule, the seven `cycle_token`
triggers (trigger 7 per delivery value), pass → surface from `command.txt`, blinding with
`random.Random(shuffle_seed)`, and `HINT:` lines on stdout only. Quote paths resolve through
`placements` (Task 4).

**Scaffold that makes each WIRE-PIN's RED an assertion about the caller.** At RED the probe from
Task 2 exists and imports `h_mad_audit_gate as _gate` (so every callee resolves), and `MODES` has no
`extract` entry. All three pins drive `main(["extract", …])` in process — WIRE-PIN 1 and 3 after
`monkeypatch.setattr(probe._gate, "classify", fake)` with a `fake` returning the real counts plus one
on the field under test — and assert the last stdout line: WIRE-PIN 1
`FINDINGS: UNREADABLE reason=must_count_mismatch:` plus the report's tree path; WIRE-PIN 2 the
`FINDINGS: WRITTEN` token with `must=1` and `should=1`, equal to `_gate.classify`'s counts on the
same text; WIRE-PIN 3 the exact line `SHOULD-COUNT:` with `walk=` the walk's count and `gate=` one
more, then `FINDINGS: WRITTEN`. At RED each reads `FINDINGS: UNREADABLE reason=internal:KeyError`,
so each fails on its token assertion, never on an import. The parity tests therefore run through
`main(["extract", …])` on a one-report tree, not by importing `extract_report`.

**Wire cuts at GREEN** (the mutation rows): X1 cuts WIRE 1, X4 cuts WIRE 2, X5 cuts WIRE 3; X2, X3,
X6 force them. Each cut must fail its WIRE-PIN with the callee and the tests intact.

**Code structure**:
```python
def report_findings(text: str) -> dict[str, list[str]]: ...  # {"must": [...], "should": [...]}
def extract_report(text: str, report: str) -> tuple[list[str], list[str], int, int]: ...
def stands(doc_dir: Path) -> Path: ...  # the v<N> directory that stands; raises Refusal("cycle_token:...")
def extract_all(tree: Path, s2_dir: Path, sources: dict[str, str]) -> list[dict]: ...
def blind(findings: list[dict], shuffle_seed: int) -> tuple[list[dict], list[dict]]: ...  # (findings rows, key rows)
def hints(findings: list[dict], tree: Path, sources: dict[str, str]) -> list[str]: ...
def _mode_extract(args: argparse.Namespace) -> int: ...
```

**Tests** (33):
- Extraction (12): `test_must_count_mismatch_through_production_path`,
  `test_extract_writes_findings_for_clean_reports`, `test_extract_reads_s2_beside_the_base_tree`,
  `test_should_findings_are_extracted_with_their_section`,
  `test_should_findings_are_written_on_a_count_difference`, `test_extract_parity_nested_label_group`
  (3 and 3), `test_extract_parity_real_parent_none_child_real_child` (2 and 2),
  `test_extract_parity_collapsing_group` (1 and 1), `test_extract_parity_prose_only` (1 and 1),
  `test_findings_carry_no_surface`, `test_hint_resolves_a_live_target_path_to_the_seeded_copy`,
  `test_hint_resolves_a_live_paired_path_to_the_archive`. Each parity fixture places the same shape in
  `## Must-fix` and in `## Should-fix`.
- `cycle_token` (8): `test_cycle_token_no_recorded_line`, `test_cycle_token_unparseable_line`,
  `test_cycle_token_v2_missing_after_unverified_v1`, `test_cycle_token_v2_present_when_v1_not_unverified`,
  `test_cycle_token_v3_present`, `test_cycle_token_unparseable_surfaces`,
  `test_cycle_token_report_file_delivery_without_collected`, `test_cycle_token_out_delivery_without_collected`.
- Stands rule (3): `test_whole_v2_stands_for_every_surface`, `test_undelivered_pass_counts_zero_findings`,
  `test_low_evidence_delivered_report_is_scored`.
- Opposed pairs (10): `test_m1_a1_foreign_line_beside_dispatched_token_does_not_fail`,
  `test_m1_a2_identical_prompts_beside_dispatched_token_does_not_fail`,
  `test_m1_b_report_path_only_beside_divergence_token_fails`,
  `test_m2_c1_pass_asm_beside_halt_token_is_halted`, `test_m2_c2_halt_asm_beside_pass_token_is_not_halted`,
  `test_m4_e1_score_ignores_report_beside_delivered_none`,
  `test_m4_e2a_score_reads_collected_beside_report_file`,
  `test_m4_e2b_score_reads_collected_beside_out`, `test_m5_f1_unverified_token_requires_v2`,
  `test_m5_f2_pass_token_beside_hollow_log_stands`.

12 + 8 + 3 + 10 = 33.

**Acceptance Criteria**:
- [ ] AC-T8.1: The three WIRE-PINs pass, and each fails when only its wire is cut (X1, X4, X5).
- [ ] AC-T8.2: `extract_report` contains D12's five lines verbatim and in order; each marker occurs
  once in the probe (`grep -c` of each of `M:GAS-MUST-COUNT-WIRE`, `M:GAS-SHOULD-COUNT-WIRE`,
  `M:GAS-COLLAPSE-WIRE` prints 1).
- [ ] AC-T8.3: `findings.jsonl` rows carry exactly `id doc cycle section text quotes`; `key.jsonl`
  rows exactly `id doc cycle pass surface report`; `extract.txt` holds the argv with the shuffle seed.
- [ ] AC-T8.4: No file the probe writes contains a `HINT:` line.

**RED split** (stated for the record; the WIRE-PINs, not the split, gate this Task): 33 nodes; 33 F
(no `extract` handler, so every test reads `internal:KeyError` or finds no output files), 0 P.

**Mutation rows** (20; markers 12). The design's X1–X6, verbatim:

| name | find | replace | test |
|---|---|---|---|
| `must-count-severed` (X1) | `must_count = _counts["must_count"]  # M:GAS-MUST-COUNT-WIRE` | `must_count = len(must)  # M:GAS-MUST-COUNT-WIRE` | `tests/test_grok_audit_surface_probe.py::test_must_count_mismatch_through_production_path` |
| `must-count-forced` (X2) | the same | `must_count = _counts["must_count"] + 1  # M:GAS-MUST-COUNT-WIRE` | `tests/test_grok_audit_surface_probe.py::test_extract_writes_findings_for_clean_reports` |
| `collapse-forced` (X3) | the probe line marked `# M:GAS-COLLAPSE-WIRE` | its `_gate._collapses(group, set())` call replaced by `True` | `tests/test_grok_audit_surface_probe.py::test_extract_parity_nested_label_group` |
| `collapse-severed` (X4) | the same | the call replaced by `False` | `tests/test_grok_audit_surface_probe.py::test_extract_parity_collapsing_group` |
| `should-count-severed` (X5) | `should_count = _counts["should_count"]  # M:GAS-SHOULD-COUNT-WIRE` | `should_count = len(should)  # M:GAS-SHOULD-COUNT-WIRE` | `tests/test_grok_audit_surface_probe.py::test_should_findings_are_written_on_a_count_difference` |
| `should-count-forced` (X6) | the same | `should_count = _counts["should_count"] + 1  # M:GAS-SHOULD-COUNT-WIRE` | `tests/test_grok_audit_surface_probe.py::test_should_findings_are_written_on_a_count_difference` |

P-rows (14), each `replace` making its condition never fire except the `DELIVERED` rows, which
remove one delivery value each (`report-file`, `out`) or, for `p-extract-undelivered-m4`, count
`none` as delivered:

| name | marker | test |
|---|---|---|
| `p-cycle-no-line` | `# M:GAS-CYCLE-NO-LINE` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_no_recorded_line` |
| `p-cycle-unparseable` | `# M:GAS-CYCLE-UNPARSEABLE` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_unparseable_line` |
| `p-cycle-v2-missing` | `# M:GAS-CYCLE-V2-MISSING` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_v2_missing_after_unverified_v1` |
| `p-cycle-v2-extra` | `# M:GAS-CYCLE-V2-EXTRA` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_v2_present_when_v1_not_unverified` |
| `p-cycle-v3` | `# M:GAS-CYCLE-V3` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_v3_present` |
| `p-cycle-surfaces` | `# M:GAS-CYCLE-SURFACES` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_unparseable_surfaces` |
| `p-cycle-collected-report-file` | `# M:GAS-CYCLE-COLLECTED` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_report_file_delivery_without_collected` |
| `p-cycle-collected-out` | `# M:GAS-CYCLE-COLLECTED` | `tests/test_grok_audit_surface_probe.py::test_cycle_token_out_delivery_without_collected` |
| `p-stands-m1` | `# M:GAS-STANDS-V1-UNVERIFIED` | `tests/test_grok_audit_surface_probe.py::test_m1_b_report_path_only_beside_divergence_token_fails` |
| `p-stands-m2` | `# M:GAS-STANDS-V1-UNVERIFIED` | `tests/test_grok_audit_surface_probe.py::test_m2_c1_pass_asm_beside_halt_token_is_halted` |
| `p-stands-m5` | `# M:GAS-STANDS-V1-UNVERIFIED` | `tests/test_grok_audit_surface_probe.py::test_m5_f1_unverified_token_requires_v2` |
| `p-extract-undelivered-m4` | `# M:GAS-EXTRACT-DELIVERED` | `tests/test_grok_audit_surface_probe.py::test_m4_e1_score_ignores_report_beside_delivered_none` |
| `p-extract-delivered-report-file` | `# M:GAS-EXTRACT-DELIVERED` | `tests/test_grok_audit_surface_probe.py::test_m4_e2a_score_reads_collected_beside_report_file` |
| `p-extract-delivered-out` | `# M:GAS-EXTRACT-DELIVERED` | `tests/test_grok_audit_surface_probe.py::test_m4_e2b_score_reads_collected_beside_out` |

6 + 14 = 20.

**Dependencies on other tasks**: Tasks 4 (placements) and 7 (`parse_auditcycle`, `parse_effort_items`, `delivered`).

---

## Task 9: score

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `score` per D13: refusals in D13's order (`ledger_counts`, `ledger_origin`,
`seed_rebuild`, `cycle_token`, re-extracted `must_count_mismatch`, `key_mismatch`, `label:`), the
`key_mismatch` and `label:` triggers each its own guard, per-surface totals over must findings only,
`fab_rate` as `Fraction` with `0/0` read as `Fraction(0)`, `d3` and `verdict(totals)` taking the
per-surface `(hits, n, f, u)` only, the `SURFACE:` lines, the observational `SHOULD:` and `SPLIT:`
lines from a function the verdict never calls, and the `SEEDSCORE:` token. Re-extraction calls
Task 8's `extract_all(tree, tree / "docs/03-analysis/probes/grok-audit-surface/calibration/s2", sources)`, with
`sources` the mapping `score` parsed (D1).

**Code structure**:
```python
def d3(fg: Fraction, rg: int, fa: Fraction, ra: int) -> bool: ...
def verdict(totals: dict[str, tuple[int, int, int, int]]) -> tuple[str, str | None]: ...
def check_key(tree: Path, findings: list[dict], key: list[dict], reextracted: list[dict]) -> None: ...
def check_labels(findings: list[dict], labels: list[dict], ledger: list[dict]) -> dict[str, dict]: ...
def observational_lines(rows: list[dict], ledger: list[dict]) -> list[str]: ...
def score(tree: Path, sources: dict[str, str], calibration: str | None, score_sha: str | None) -> tuple[list[str], str]: ...
def _mode_score(args: argparse.Namespace) -> int: ...
```

**Tests** (31):
- `key_mismatch` (8): `test_key_mismatch_id_sets_differ`, `test_key_mismatch_duplicate_id_in_findings`,
  `test_key_mismatch_duplicate_id_in_key`, `test_key_mismatch_surface_moved_grok_to_agy`,
  `test_key_mismatch_doc_differs`, `test_key_mismatch_cycle_differs`, `test_key_mismatch_report_differs`,
  `test_key_mismatch_reextraction`.
- `label:` (8): `test_label_unlabelled_finding`, `test_label_identical_duplicate`,
  `test_label_conflicting_duplicate`, `test_label_unknown_id`, `test_label_unknown_value`,
  `test_label_undecidable_without_why`, `test_label_hit_unknown_seed`, `test_label_hit_seed_of_other_doc`.
- Verdicts (11): `test_d3_strictly_lower_fab_equal_recall_pass`, `test_d3_equal_fab_greater_recall_pass`,
  `test_d3_full_tie_miss`, `test_d3_equal_fab_lower_recall_miss`,
  `test_d3_unreduced_equal_fab_equal_recall_miss`, `test_undecidable_flips_inconclusive`,
  `test_seeds_undetected_inconclusive`, `test_seeds_undetected_outranks_a_fabrication_pass`,
  `test_seeds_undetected_outranks_a_fabrication_miss`, `test_zero_decidable_musts_prints_0_over_0`,
  `test_score_exit_codes`.
- Observational (3): `test_split_lines_never_move_the_verdict`, `test_should_hits_never_move_the_verdict`,
  `test_should_and_split_lines_are_printed`.
- Hints (1): `test_hints_never_move_the_score`.

8 + 8 + 11 + 3 + 1 = 31.

**Acceptance Criteria**:
- [ ] AC-T9.1: Each `key_mismatch` and `label:` test reads its exact `SEEDSCORE: UNREADABLE` token, exit 2.
- [ ] AC-T9.2: Each verdict test reads its exact `SEEDSCORE:` token with `calibration=unstated score=unstated`
  when no shas are given; `test_score_exit_codes` reads exit 0 for PASS, MISS and INCONCLUSIVE and 2
  for UNREADABLE.
- [ ] AC-T9.3: `verdict` takes only the per-surface totals (its signature) and `observational_lines`
  is not called from `verdict` or `d3`.

**RED split**: 31 nodes; 31 F (no `score` handler; `d3` and `verdict` absent), 0 P.

**Mutation rows** (25; markers 20). Each `replace` makes its condition never fire, except: the
`GAS-D3-EQUAL` rows for the full tie and lower recall, which force the recall comparison
(`rg > ra` to `rg >= ra`, and to `rg != ra`); `p-fab-fraction`, which keeps every value a
`Fraction` and shifts the worst-case denominator by one (`Fraction(f + u, n)` to
`Fraction(f + u, n + 1)`, the same on the optimistic side), so the fixture's `1/4` against `2/8`
becomes `1/5` against `2/9`, unequal (measured: `Fraction(1, 5) < Fraction(2, 9)` is true), and the
verdict moves off `MISS`; and `p-verdict-flips`, which returns `MISS` in place of the final
`INCONCLUSIVE`. Residual, stated exactly, for `p-fab-fraction`: `Fraction` normalises on
construction (measured: `Fraction(2, 8)` is `1/4`), so no `Fraction`-preserving mutant can make the
two sides differ in representation alone. The row therefore shows the test can fail at this
fixture's tie boundary. That a non-`Fraction` comparison (a string or an unreduced pair) would also
fail it is pinned by the test's construction, not by a row, because the only mutants that reach it
change the value's type, which the P-row rule forbids. `test_zero_decidable_musts_prints_0_over_0` and `test_score_exit_codes` are format and
exit contracts over guards rowed here, and the three observational tests and the hint test are
invariance tests; none of them gets a row.

| name | marker | test |
|---|---|---|
| `p-key-id-sets` | `# M:GAS-KEY-ID-SETS` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_id_sets_differ` |
| `p-key-dup-findings` | `# M:GAS-KEY-DUP-FINDINGS` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_duplicate_id_in_findings` |
| `p-key-dup-key` | `# M:GAS-KEY-DUP-KEY` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_duplicate_id_in_key` |
| `p-key-surface` | `# M:GAS-KEY-SURFACE` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_surface_moved_grok_to_agy` |
| `p-key-doc` | `# M:GAS-KEY-DOC` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_doc_differs` |
| `p-key-cycle` | `# M:GAS-KEY-CYCLE` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_cycle_differs` |
| `p-key-report` | `# M:GAS-KEY-REPORT` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_report_differs` |
| `p-key-reextract` | `# M:GAS-KEY-REEXTRACT` | `tests/test_grok_audit_surface_probe.py::test_key_mismatch_reextraction` |
| `p-label-missing` | `# M:GAS-LABEL-MISSING` | `tests/test_grok_audit_surface_probe.py::test_label_unlabelled_finding` |
| `p-label-dup-identical` | `# M:GAS-LABEL-DUP` | `tests/test_grok_audit_surface_probe.py::test_label_identical_duplicate` |
| `p-label-dup-conflicting` | `# M:GAS-LABEL-DUP` | `tests/test_grok_audit_surface_probe.py::test_label_conflicting_duplicate` |
| `p-label-unknown-id` | `# M:GAS-LABEL-UNKNOWN-ID` | `tests/test_grok_audit_surface_probe.py::test_label_unknown_id` |
| `p-label-value` | `# M:GAS-LABEL-VALUE` | `tests/test_grok_audit_surface_probe.py::test_label_unknown_value` |
| `p-label-why` | `# M:GAS-LABEL-WHY` | `tests/test_grok_audit_surface_probe.py::test_label_undecidable_without_why` |
| `p-label-seed-unknown` | `# M:GAS-LABEL-SEED-UNKNOWN` | `tests/test_grok_audit_surface_probe.py::test_label_hit_unknown_seed` |
| `p-label-seed-doc` | `# M:GAS-LABEL-SEED-DOC` | `tests/test_grok_audit_surface_probe.py::test_label_hit_seed_of_other_doc` |
| `p-d3-lower` | `# M:GAS-D3-LOWER` | `tests/test_grok_audit_surface_probe.py::test_d3_strictly_lower_fab_equal_recall_pass` |
| `p-d3-equal-greater` | `# M:GAS-D3-EQUAL` | `tests/test_grok_audit_surface_probe.py::test_d3_equal_fab_greater_recall_pass` |
| `p-d3-equal-tie` | `# M:GAS-D3-EQUAL` | `tests/test_grok_audit_surface_probe.py::test_d3_full_tie_miss` |
| `p-d3-equal-lower` | `# M:GAS-D3-EQUAL` | `tests/test_grok_audit_surface_probe.py::test_d3_equal_fab_lower_recall_miss` |
| `p-fab-fraction` | `# M:GAS-FAB-FRACTION` | `tests/test_grok_audit_surface_probe.py::test_d3_unreduced_equal_fab_equal_recall_miss` |
| `p-verdict-flips` | `# M:GAS-VERDICT-FLIPS` | `tests/test_grok_audit_surface_probe.py::test_undecidable_flips_inconclusive` |
| `p-verdict-undetected` | `# M:GAS-VERDICT-UNDETECTED` | `tests/test_grok_audit_surface_probe.py::test_seeds_undetected_inconclusive` |
| `p-verdict-undetected-pass` | `# M:GAS-VERDICT-UNDETECTED` | `tests/test_grok_audit_surface_probe.py::test_seeds_undetected_outranks_a_fabrication_pass` |
| `p-verdict-undetected-miss` | `# M:GAS-VERDICT-UNDETECTED` | `tests/test_grok_audit_surface_probe.py::test_seeds_undetected_outranks_a_fabrication_miss` |

8 + 8 + 9 = 25.

**Dependencies on other tasks**: Task 8.

---

## Task 10: main-leak, rescore, the calibration-data set, the grammar sweeps

**Production file**: `docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py` (extend)
**Test files**: `h-mad/tests/test_grok_audit_surface_probe.py` (extend), `h-mad/tests/grokauditfixtures.py` (extend)
**Task shape**: `new-behaviour`

**Description**: `calibration_data_files(tree)` per D3 (the six named candidates excluded only when
they carry none of (a), (b), (c), with (c)'s needles from Task 8's `report_findings` per line). D9's
ref and sha checks, drift check, main leak check (triggers i–iii over `git ls-tree -r -z HEAD` read
through `git cat-file --batch`), `main-leak`, and `rescore`'s eight steps in AC-6.4's order, ending
in a `finally` that removes and re-lists every temporary directory. The three D2 grammar sweeps land
here because they need all nine handlers.

**Code structure**:
```python
def calibration_data_files(tree: Path) -> list[str]: ...
def ref_checks(repo: Path, remote: str, shas: list[str]) -> str: ...  # the fetched tip
def drift_check(repo: Path, calibration: str, later: str) -> None: ...
def main_leak(repo: Path, data_sha: str, sources: dict[str, str]) -> tuple[str, str, int]: ...  # (HEAD sha40, data sha40, blobs)
def list_check(export: Path, repo: Path) -> str: ...  # the LIST: line
def rescore(args: argparse.Namespace) -> tuple[list[str], str]: ...
def _mode_main_leak(args: argparse.Namespace) -> int: ...
def _mode_rescore(args: argparse.Namespace) -> int: ...
```

**Tests** (30 functions, 43 node ids):
- Calibration-data set (4): `test_calibration_data_set_is_the_directory_minus_six_named_files`,
  `test_calibration_data_set_keeps_an_excluded_name_carrying_a_finding_text`,
  `test_calibration_data_set_keeps_an_excluded_name_carrying_a_seeded_span`,
  `test_calibration_data_set_keeps_an_excluded_name_carrying_an_expected_sentence`.
- Drift (6): `test_drift_outside_calibration_dir`, `test_drift_not_descendant`,
  `test_drift_score_not_descendant_of_smoke_commit`, `test_drift_seeded_copy_changed_at_score_sha`,
  `test_drift_ledger_changed_at_smoke_commit`, `test_drift_ledger_absent_at_score_sha`.
- Main leak (9): `test_main_leak_trigger_i_byte_equal_copy`,
  `test_main_leak_trigger_i_on_a_captured_wrapper_stdout`,
  `test_main_leak_trigger_i_smoke_commit_without_score_sha`,
  `test_main_leak_trigger_i_on_an_excluded_name_carrying_a_finding_text`,
  `test_main_leak_trigger_ii_expected`, `test_main_leak_trigger_iii_seeded_span`, the must-not-refuse
  `test_seeded_span_also_in_its_own_archive_source_does_not_refuse` and
  `test_main_leak_ignores_a_main_blob_equal_to_wall_seconds`, and `test_main_leak_prints_the_scanned_commit`.
- Ref (4): `test_ref_fetch_failed_no_remote`, `test_ref_absent`, `test_ref_sha_unknown`, `test_ref_not_on_ref`.
- List (2): `test_list_changed_recorded_blob_differs`, `test_list_changed_unrecorded_root_record`.
- End to end (2): `test_main_leak_mode_clean_on_a_smoke_failure_branch`,
  `test_rescore_reproduces_the_score_and_removes_its_temp_dirs`.
- Grammar sweeps (3 functions, 16 ids): `test_success_token_shape_per_mode` (9 ids, one per D2 mode),
  `test_no_published_line_uses_another_modes_prefix` (1), `test_sources_override_reaches_every_ledger_mode`
  (6 ids: `check-ledger`, `build-root`, `extract`, `score`, `rescore`, `main-leak`).

4 + 6 + 9 + 4 + 2 + 2 = 27 functions with one id each, plus 9 + 1 + 6 = 16: 43 ids.

**Acceptance Criteria**:
- [ ] AC-T10.1: Every refusal test reads its exact `MAINLEAK: UNREADABLE` or `SEEDSCORE: UNREADABLE`
  token, exit 2, built on `tmp_path/work` with `tmp_path/origin.git` as `origin`.
- [ ] AC-T10.2: `test_rescore_reproduces_the_score_and_removes_its_temp_dirs` reads the same
  `SEEDSCORE:` line as `score --tree` on the same export, the published `SCANNED:` and `LIST:` lines,
  and finds none of the probe's `mkdtemp` directories after the run.
- [ ] AC-T10.3: `calibration_data_files` is the only definition of the set; `main_leak` and the four
  calibration-set tests call it.
- [ ] AC-T10.4: The spec's `command` is unchanged by this Task (no new test file).

**RED split**: 43 ids; 32 F, 11 P. F: the 27 single-id functions (the two modes are absent, and
`calibration_data_files` is absent); `test_success_token_shape_per_mode[rescore]` and `[main-leak]`;
`test_no_published_line_uses_another_modes_prefix` (it runs every mode);
`test_sources_override_reaches_every_ledger_mode[rescore]` and `[main-leak]`. P (regression guards on
modes Tasks 3–9 built): `test_success_token_shape_per_mode` for `check-ledger`, `build-root`,
`record-cycle`, `commit-data`, `smoke`, `extract`, `score` (7), and
`test_sources_override_reaches_every_ledger_mode` for `check-ledger`, `build-root`, `extract`,
`score` (4). 27 + 2 + 1 + 2 = 32; 7 + 4 = 11.

**Mutation rows** (21; markers 17), each `replace` making its condition never fire:

| name | marker | test |
|---|---|---|
| `p-calset-finding` | `# M:GAS-CALSET-FINDING` | `tests/test_grok_audit_surface_probe.py::test_calibration_data_set_keeps_an_excluded_name_carrying_a_finding_text` |
| `p-calset-seeded` | `# M:GAS-CALSET-SEEDED` | `tests/test_grok_audit_surface_probe.py::test_calibration_data_set_keeps_an_excluded_name_carrying_a_seeded_span` |
| `p-calset-expected` | `# M:GAS-CALSET-EXPECTED` | `tests/test_grok_audit_surface_probe.py::test_calibration_data_set_keeps_an_excluded_name_carrying_an_expected_sentence` |
| `p-drift-path` | `# M:GAS-DRIFT-PATH` | `tests/test_grok_audit_surface_probe.py::test_drift_outside_calibration_dir` |
| `p-drift-ancestor` | `# M:GAS-DRIFT-ANCESTOR` | `tests/test_grok_audit_surface_probe.py::test_drift_not_descendant` |
| `p-drift-smoke-ancestor` | `# M:GAS-DRIFT-SMOKE-ANCESTOR` | `tests/test_grok_audit_surface_probe.py::test_drift_score_not_descendant_of_smoke_commit` |
| `p-drift-blob-seeded` | `# M:GAS-DRIFT-BLOB` | `tests/test_grok_audit_surface_probe.py::test_drift_seeded_copy_changed_at_score_sha` |
| `p-drift-blob-ledger` | `# M:GAS-DRIFT-BLOB` | `tests/test_grok_audit_surface_probe.py::test_drift_ledger_changed_at_smoke_commit` |
| `p-drift-absent` | `# M:GAS-DRIFT-ABSENT` | `tests/test_grok_audit_surface_probe.py::test_drift_ledger_absent_at_score_sha` |
| `p-mainleak-i-copy` | `# M:GAS-MAINLEAK-I` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_i_byte_equal_copy` |
| `p-mainleak-i-stdout` | `# M:GAS-MAINLEAK-I` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_i_on_a_captured_wrapper_stdout` |
| `p-mainleak-i-smoke` | `# M:GAS-MAINLEAK-I` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_i_smoke_commit_without_score_sha` |
| `p-mainleak-i-finding` | `# M:GAS-MAINLEAK-I` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_i_on_an_excluded_name_carrying_a_finding_text` |
| `p-mainleak-ii` | `# M:GAS-MAINLEAK-II` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_ii_expected` |
| `p-mainleak-iii` | `# M:GAS-MAINLEAK-III` | `tests/test_grok_audit_surface_probe.py::test_main_leak_trigger_iii_seeded_span` |
| `p-ref-fetch` | `# M:GAS-REF-FETCH` | `tests/test_grok_audit_surface_probe.py::test_ref_fetch_failed_no_remote` |
| `p-ref-absent` | `# M:GAS-REF-ABSENT` | `tests/test_grok_audit_surface_probe.py::test_ref_absent` |
| `p-ref-sha-unknown` | `# M:GAS-REF-SHA-UNKNOWN` | `tests/test_grok_audit_surface_probe.py::test_ref_sha_unknown` |
| `p-ref-not-on-ref` | `# M:GAS-REF-NOT-ON-REF` | `tests/test_grok_audit_surface_probe.py::test_ref_not_on_ref` |
| `p-list-changed` | `# M:GAS-LIST-CHANGED` | `tests/test_grok_audit_surface_probe.py::test_list_changed_recorded_blob_differs` |
| `p-list-unrecorded` | `# M:GAS-LIST-UNRECORDED` | `tests/test_grok_audit_surface_probe.py::test_list_changed_unrecorded_root_record` |

3 + 6 + 6 + 4 + 2 = 21.

**Dependencies on other tasks**: Tasks 6 (`commit-data` builds the fixture branch commits), 8, 9.

---

## Task 11: the identical-prompts stub knob

**Production file**: `h-mad/tests/test_hmad_dispatch_audit_cycle.py` (modify `install_audit_cycle_stubs` only)
**Test file**: `h-mad/tests/test_grok_audit_surface_wrapper.py` (create)
**Task shape**: `new-behaviour`

**Description**: The test-only knob the design's Components table names. In the stub
`h_mad_assemble_audit.py` that `install_audit_cycle_stubs` writes, `HMAD_ASSEMBLE_SAME_REPORT_P<i>=1`
writes the constant `Report path: SAME` in place of both report-path lines of that pass's prompt (the
stub writes the path twice, `Head contract report path:` and `Report path:`), so two passes can
assemble byte-identical prompts and `_cmd_audit_cycle`'s empty-diff branch
(`if [ -z "$div" ] || [ "$foreign" -ne 0 ]; then`) halts them. Unset, the stub's output is
byte-for-byte what it is at `30917a1a`. No other helper changes.

**Tests** (1): `test_identical_prompts_halt_prompt_divergence` — with `HMAD_ASSEMBLE_SAME_REPORT_P1=1`
and `HMAD_ASSEMBLE_SAME_REPORT_P2=1`, the `AUDITCYCLE:` lines are exactly
`["AUDITCYCLE: UNVERIFIED reason=prompt_divergence passes=2 size_status=verified"]` and zero agents are
dispatched (the capture file's dispatch count is 0), using `project_with_docs`, `dispatch_args`,
`run_audit_cycle` and `install_audit_cycle_stubs` imported from `test_hmad_dispatch_audit_cycle`.

**Acceptance Criteria**:
- [ ] AC-T11.1: The test passes; every existing test in `h-mad/tests/test_hmad_dispatch_audit_cycle.py`
  passes unchanged (regression guard).
- [ ] AC-T11.2: The spec's `command` gains `tests/test_grok_audit_surface_wrapper.py` and
  `tests/test_hmad_dispatch_audit_cycle.py` at their design positions.

**RED split**: 1 node; 1 F (without the knob the two prompts differ on their report-path lines only,
the wrapper's check passes them, and the cycle dispatches). Regression guards: all of
`h-mad/tests/test_hmad_dispatch_audit_cycle.py`.

**Mutation rows** (2), the design's:

| name | file | find | replace | test |
|---|---|---|---|---|
| `divergence-empty-branch-dropped` (W7) | `scripts/hmad-dispatch.sh` | `␣␣␣␣if [ -z "$div" ] \|\| [ "$foreign" -ne 0 ]; then` | `␣␣␣␣if [ "$foreign" -ne 0 ]; then` | `tests/test_grok_audit_surface_wrapper.py::test_identical_prompts_halt_prompt_divergence` |
| `divergence-foreign-branch-dropped` (W8) | `scripts/hmad-dispatch.sh` | the same | `␣␣␣␣if [ -z "$div" ]; then` | `tests/test_hmad_dispatch_audit_cycle.py::test_verb_prompt_divergence` |

`␣` is one space (four leading spaces); the table cell escapes the two `|` of `||`.

**Dependencies on other tasks**: Task 2 (the spec file).

---

## Task 12: pins over unchanged code

**Production files**: none (the gate, the cycle helper and the wrapper are pinned, not edited)
**Test files**: `h-mad/tests/test_grok_audit_surface_gate_pins.py` (create),
`h-mad/tests/test_grok_audit_surface_wrapper.py` (extend)
**Task shape**: `new-behaviour` — tests over existing behaviour; each is expected to pass at RED, and
its ability to fail is shown only by its mutation row (design §"Test Strategy").

**Description**: FR-8 through `combine` over `pass_result` indices 1–3 (`audit_cycle()` and
`pass_result` from `test_h_mad_audit_cycle`; p3 efforts from `grokfixtures.f0_text` and `f_trunc`);
FR-9 through the gate CLI (`--exit-check`, and `--round-cap 2` with the cap first, as `main` parses
it) over stamps named `gas-fx.design.audit.v<N>.p<i>.md.gated.json`, written with `verdict`, `suite`
and `legs` the way `test_h_mad_audit_leg_set_gate.py`'s `_stamp` methods write them; FR-10 and
AC-7.2's stamp claim through `run_with_cmd_exec_stub` / `_dispatch_artifacts_by_pass` and
`run_audit_cycle` with `_BINDIR` (a bin dir holding the `STUBS` `codex`, `agy`, `grok` stubs and `jq`),
`HMAD_AUDIT_CYCLE_SCRIPT_DIR` from `_script_dir_with_stub_assemble_and_real_cycle(tmp_path)`, and
`HMAD_STUB_AGY_RESP` / `HMAD_STUB_CODEX_LAST` from `_audit_response(...)`; and the D10 M1/M2 authority
test, which drives the real `_cmd_audit_cycle` through `install_audit_cycle_stubs` and
`run_audit_cycle` on the three M1 shapes (a foreign line via `HMAD_ASSEMBLE_DIVERGE_P2`; identical
prompts via Task 11's knob; report-path-only differences, the default) and on an `ASSEMBLE: HALT`
shape (`HMAD_ASSEMBLE_HALT_P2`), asserting the wrapper's own verdicts.

**Tests** (14):
- Gate pins (8): `test_union_three_passes_only_grok_must_fails`, `test_union_three_passes_all_clean_pass`,
  `test_floor_low_evidence_at_index_3`, `test_floor_truncated_at_index_3`,
  `test_exit_three_leg_first_gate_then_codex_blocks_legs_changed`, `test_exit_two_codex_revisions_ready`,
  `test_round_cap_first_gate_counts_one_cycle`, `test_exit_mixed_first_gate_legs_disagree`.
- Wrapper pins (6): `test_three_surfaces_map_pass_index_to_agent`,
  `test_three_surfaces_print_no_repeated_warning`, `test_three_surface_stamps_carry_sorted_legs`
  (asserts exactly the two stamps `….p1.md.gated.json` and `….p2.md.gated.json`, each with
  `"legs": ["agy", "codex", "grok"]`), `test_codex_agy_cycle_stamps_carry_the_legs_that_ran` (both
  stamps `"legs": ["agy", "codex"]`), `test_two_surfaces_for_three_passes_exit_2`,
  `test_m1_m2_raw_shapes_are_what_the_wrapper_says`.

**Acceptance Criteria**:
- [ ] AC-T12.1: All 14 pass; no file under `h-mad/scripts/` changes (`git diff --quiet -- h-mad/scripts`).
- [ ] AC-T12.2: Every one of the 13 tests other than `test_m1_m2_raw_shapes_are_what_the_wrapper_says`
  is the `test` of at least one row below, and the 17 rows are all caught.
- [ ] AC-T12.3: The spec's `command` gains `tests/test_grok_audit_surface_gate_pins.py`.

**RED split**: 14 nodes; 0 F, 14 P (all regression guards over unchanged code). An F here falsifies
the design's "unchanged code" premise for that property: the Task stops and reports it, and no
production file is edited to make it pass.

**Mutation rows** (17), the design's, verbatim (`␣` is one space; `\|` in a cell is a literal `|`):

| name | file | find | replace | test |
|---|---|---|---|---|
| `surf-map-rotate` (W1) | `scripts/hmad-dispatch.sh` | `agent[$i]="${_surf[$((i - 1))]}"` | `agent[$i]="${_surf[$((i % passes))]}"` | `tests/test_grok_audit_surface_wrapper.py::test_three_surfaces_map_pass_index_to_agent` |
| `surf-map-fixed` (W2) | `scripts/hmad-dispatch.sh` | the same | `agent[$i]="grok"` | `tests/test_grok_audit_surface_wrapper.py::test_three_surfaces_map_pass_index_to_agent` |
| `surf-map-fixed-warns` (W3) | `scripts/hmad-dispatch.sh` | the same | `agent[$i]="grok"` | `tests/test_grok_audit_surface_wrapper.py::test_three_surfaces_print_no_repeated_warning` |
| `legs-default-dropped` (W4) | `scripts/hmad-dispatch.sh` | `␣␣␣␣legs=("${_surf[@]}")` | `␣␣␣␣legs=()` | `tests/test_grok_audit_surface_wrapper.py::test_three_surface_stamps_carry_sorted_legs` |
| `legs-default-fixed` (W5) | `scripts/hmad-dispatch.sh` | the same | `␣␣␣␣legs=(codex)` | `tests/test_grok_audit_surface_wrapper.py::test_three_surface_stamps_carry_sorted_legs` |
| `surfaces-count-check-dropped` (W6) | `scripts/hmad-dispatch.sh` | `␣␣␣␣[ "${#_surf[@]}" -eq "$passes" ] \|\| {` | `␣␣␣␣true \|\| {` | `tests/test_grok_audit_surface_wrapper.py::test_two_surfaces_for_three_passes_exit_2` |
| `legs-default-dropped-two-surface` (W9) | `scripts/hmad-dispatch.sh` | W4's find | `␣␣␣␣legs=()` | `tests/test_grok_audit_surface_wrapper.py::test_codex_agy_cycle_stamps_carry_the_legs_that_ran` |
| `legs-default-fixed-two-surface` (W10) | `scripts/hmad-dispatch.sh` | W5's find | `␣␣␣␣legs=(codex)` | `tests/test_grok_audit_surface_wrapper.py::test_codex_agy_cycle_stamps_carry_the_legs_that_ran` |
| `leg-key-input-order` (G1) | `scripts/h_mad_audit_gate.py` | `␣␣␣␣return sorted({str(name).strip() for name in legs if str(name).strip()})` | `␣␣␣␣return list(dict.fromkeys(str(name).strip() for name in legs if str(name).strip()))` | `tests/test_grok_audit_surface_wrapper.py::test_three_surface_stamps_carry_sorted_legs` |
| `legs-changed-dropped` (G2) | `scripts/h_mad_audit_gate.py` | `␣␣␣␣␣␣␣␣if first != second:` | `␣␣␣␣␣␣␣␣if False:` | `tests/test_grok_audit_surface_gate_pins.py::test_exit_three_leg_first_gate_then_codex_blocks_legs_changed` |
| `legs-disagree-dropped` (G3) | `scripts/h_mad_audit_gate.py` | `␣␣␣␣␣␣␣␣if len(distinct) > 1:` | `␣␣␣␣␣␣␣␣if False:` | `tests/test_grok_audit_surface_gate_pins.py::test_exit_mixed_first_gate_legs_disagree` |
| `legs-disagree-always` (G4) | `scripts/h_mad_audit_gate.py` | the same | `␣␣␣␣␣␣␣␣if True:` | `tests/test_grok_audit_surface_gate_pins.py::test_exit_two_codex_revisions_ready` |
| `round-counts-stamps` (G5) | `scripts/h_mad_audit_gate.py` | `␣␣␣␣␣␣␣␣grouped.add(key)` | `␣␣␣␣␣␣␣␣grouped.add((key[0], key[1], (key[2], path.name)))` | `tests/test_grok_audit_surface_gate_pins.py::test_round_cap_first_gate_counts_one_cycle` |
| `union-drops-p3` (C1) | `scripts/h_mad_audit_cycle.py` | `␣␣␣␣␣␣␣␣if result.verdict == "FAIL":` | `␣␣␣␣␣␣␣␣if result.verdict == "FAIL" and result.index != 3:` | `tests/test_grok_audit_surface_gate_pins.py::test_union_three_passes_only_grok_must_fails` |
| `floor-skips-last-pass` (C2) | `scripts/h_mad_audit_cycle.py` | `␣␣␣␣␣␣␣␣if result.effort is None:` | `␣␣␣␣␣␣␣␣if result.effort is None or result.index == len(results):` | `tests/test_grok_audit_surface_gate_pins.py::test_floor_low_evidence_at_index_3` |
| `floor-skips-last-pass-truncated` (C3) | `scripts/h_mad_audit_cycle.py` | the same | the same as C2 | `tests/test_grok_audit_surface_gate_pins.py::test_floor_truncated_at_index_3` |
| `union-always-fails` (C4) | `scripts/h_mad_audit_cycle.py` | C1's find | `␣␣␣␣␣␣␣␣if True:` | `tests/test_grok_audit_surface_gate_pins.py::test_union_three_passes_all_clean_pass` |

Each find was re-counted at `30917a1a` with `grep -cF` in its file: 1 matching line each.

**Dependencies on other tasks**: Task 11 (the knob for the M1 identical-prompts shape; the wrapper
module).

---

## Task 13: SKILL.md S0 text

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_grok_audit_surface_docs.py` (extend)
**Task shape**: `new-behaviour`

**Description**: D14's two S0 edits. AC-6.2a: in §"Teammate audit leg — when codex is unavailable",
the code span `h_mad_audit_cycle.py --surfaces agy,grok` becomes
`hmad-dispatch audit-cycle --feature <feature> --phase <phase> --cycle <N> --project-root <root> --passes 2 --surfaces agy,grok`,
and nothing else in that section changes. AC-9.5: this sentence is appended to the §"What you NEVER do"
bullet that starts "**Name the reviewer legs with `--legs`…**": "The first gate and the revisions run
different leg sets by design, so the streak, when it is reached, is among revision cycles." The RED
run of `test_no_h_mad_md_pairs_audit_cycle_py_with_surfaces` against the uncorrected SKILL.md is
recorded first: its pytest summary line is quoted in the RED report and in the RED commit's message.
Doc tests read sections with `titled_section` and collapse each whitespace run to one space.

**Tests** (3): `test_teammate_section_names_hmad_dispatch_audit_cycle`,
`test_no_h_mad_md_pairs_audit_cycle_py_with_surfaces` (scans `git ls-files -z 'h-mad/*.md'` with
`h_mad_audit_cycle\.py[^\n]*\n?[^\n]*--surfaces`; 0 occurrences after the edit),
`test_never_do_legs_bullet_states_the_first_gate_leg_set`.

**Acceptance Criteria**:
- [ ] AC-T13.1: The three tests pass; `tests/test_grok_fallback_docs.py` passes unchanged (its
  teammate test still finds `--surfaces agy,grok` and `unmeasured`, each once in the section at
  `30917a1a`).
- [ ] AC-T13.2: The teammate section's diff is that one code span; the §"What you NEVER do" diff is
  that one appended sentence.
- [ ] AC-T13.3: The spec's `command` gains `tests/test_grok_fallback_docs.py`, completing the design's
  seven-file list.

**RED split**: 3 nodes; 3 F, 0 P. Regression guards: `h-mad/tests/test_grok_fallback_docs.py`.

**Mutation rows** (3), the design's:

| name | file | find | replace | test |
|---|---|---|---|---|
| `teammate-surfaces-pin` (K1) | `SKILL.md` | `--project-root <root> --passes 2 --surfaces agy,grok` | `--project-root <root> --passes 2 --surfaces agy,codex` | `tests/test_grok_fallback_docs.py::test_teammate_section_documents_the_grok_leg` |
| `teammate-unmeasured-pin` (K2) | `SKILL.md` | `audit precision remain **unmeasured** (D4)` | `audit precision remain **measured** (D4)` | `tests/test_grok_fallback_docs.py::test_teammate_section_documents_the_grok_leg` |
| `never-gate-surfaces-pin` (K3) | `SKILL.md` | ``When Codex is unavailable and `fallback_agent=grok`, use `--surfaces agy,grok` `` | the same with `--surfaces agy,codex` | `tests/test_grok_fallback_docs.py::test_never_gate_section_cross_references_the_grok_leg` |

K2 and K3's finds occur once in `h-mad/SKILL.md` at `30917a1a`; K1's find is written by this Task
(0 occurrences before it, 1 after).

**Dependencies on other tasks**: Task 1 (the docs module), Task 2 (the spec).

---

## Task 14: Phase 5e verdict

**Production files**: none
**Test files**: none
**Task shape**: `gate` — reads verdicts over what Tasks 1–13 built; writes no production file.

**Description**: One run over the whole spec and the closing checks the design names.

```bash
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest --version
rtk proxy /opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider
python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/grok_audit_surface.json
python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/grok_audit_surface.json
git ls-files 'h-mad/tests/*' | grep -E '\.(plan|design|impl-plan|spec)\.md$'
grep -c 'M:GAS-' docs/03-analysis/probes/grok-audit-surface/grok_audit_probe.py
/opt/anaconda3/bin/python3.11 -c 'import json; print(len(json.load(open("h-mad/tests/mutation-specs/grok_audit_surface.json"))["mutations"]))'
```

**Acceptance Criteria**:
- [ ] AC-T14.1: The first command prints a pytest version; the full suite's summary line shows no failure.
- [ ] AC-T14.2: `MUTATION: ALL_CAUGHT` with `untargeted=0/171` and `crash_kills=0`, and
  `ANCHORS: ANCHORS_OK`, read from the token lines.
- [ ] AC-T14.3: The `git ls-files` line prints nothing (the zero holds because every synthetic phase
  document is written under `tmp_path`; it was 0 files at `30917a1a`).
- [ ] AC-T14.4 (carry 11): the marker-site count (matching lines) and the row count (rows) are
  re-derived by the last two commands at this Task's sha and reported with their units. This plan
  expects 117 and 171; a different figure is reported against this plan with the Task whose table
  it contradicts, never silently accepted.

**Dependencies on other tasks**: Tasks 1–13.

---

## Task 15: S0b, S1, S2 (operator)

**Production files**: none on `main` (calibration data goes only to `calibration/grok-audit-surface`, by Task 6's `commit-data`)
**Test files**: none
**Task shape**: `operational` — runs the probe Tasks 2–10 built and the existing wrapper, live; not CI.

**Description**: The operator runs D8 and D9 as written, from a `main` clone at the merge of Tasks
0–14, with these variables in place of D8's template slots:
`KEEP="$HOME/.local/state/h-mad/grok-audit-surface"`;
`CAL_SHA=$(git rev-parse refs/heads/calibration/grok-audit-surface)` read right after the calibration
push is confirmed (at that moment the tip is the calibration sha); `CAL12=${CAL_SHA:0:12}`;
`LIST_SHA=$(git rev-parse HEAD)` on `main`. Steps, in order:
1. **S0b.** Branch from the `main` commit holding S0 by `commit-data --parent` that commit; commit the
   ledger and nine seeded copies from `$KEEP/authoring/`; `check-ledger` and one `build-root` per
   document until every one reads `LEDGER: OK` / `ROOT: READY`; push without force; confirm with
   `git ls-remote origin refs/heads/calibration/grok-audit-surface`; delete `$KEEP/authoring/`.
2. **Before S1**: read Task 0's `$KEEP/agy-tracer/reading.txt`. On `CLASS=unmatched`, re-derive the
   agy selection from that reading before any S1 dispatch (Task 0 AC-T0.3).
3. **S1 setup and versions** exactly as D8 ("Setup", "Versions").
4. **S1 grok cycle** (D8 "One cycle", `--cycle 1 --passes 1 --surfaces grok`, no `--reset`), its
   `record-cycle`, `wall_seconds.txt`, and `resolved_model.txt`.
5. **S1 agy cycle** (`--cycle 2`, with `--reset "${ROOT:?}"`). **Carry 6:** the agy provenance block's
   first line, `AGYLOG=…; /bin/ls "$AGYLOG" > "$STEM.agy-before.txt"`, goes immediately after this
   cycle block's `STEM="$KEEP/run-$CAL12/stem/s1-agy"; mkdir -p "$STEM"` line and before its
   `build-root` line, so `$STEM` is the agy cycle's stem when the listing is written; the rest of the
   provenance block runs after this cycle's `record-cycle` and before the codex block begins (D8).
6. **S1 codex cycle** (`--cycle 3`, `--reset`), when `command -v codex` succeeds.
7. `smoke --data "$KEEP/run-$CAL12/data/s1"`. On `SMOKE: PASS` or `SMOKE: FAIL`: `commit-data` the
   smoke commit, push, confirm. On `SMOKE: UNREADABLE`: restore the named input and derive again; a
   wrong-file Effort item is not cleared that way (carry 10) and needs a new smoke.
8. **S2**, only on `SMOKE: PASS`: nine cycles in fresh roots, each re-dispatch (AC-3.4) in a fresh
   `s2v2` root as `--cycle 2`; `extract --repo . --base-sha` the smoke commit; hand labels by a
   labeller without the key; `commit-data` the score sha; push; confirm.

**Acceptance Criteria**:
- [ ] AC-T15.1: Every step's entry condition is read from the previous step's token line, never `$?`.
- [ ] AC-T15.2: The shas Task 16 needs (calibration, smoke commit, score sha or its absence, list commit
  and blob) are each confirmed by `git ls-remote` or the `ROOT: READY` line that printed them.

**Dependencies on other tasks**: Tasks 0–14 merged to `main`.

---

## Task 16: S3 publish

**Production files**: `docs/03-analysis/grok-audit-surface.measurement.md` (create),
`h-mad/references/grok-runtime.md`, `h-mad/SKILL.md`, `h-mad/tests/mutation-specs/grok_audit_surface.json` (K2 re-anchor)
**Test file**: `h-mad/tests/test_grok_audit_surface_docs.py` (extend)
**Task shape**: `new-behaviour`

**Description**: On every outcome that publishes (`SMOKE: FAIL`, or a non-UNREADABLE `SEEDSCORE:`):
`main-leak` runs before the measurement doc is committed (without `--score-sha` on a smoke failure);
on a scored outcome `rescore` runs from a `main` checkout and its `SEEDSCORE:` line is the one
published. The measurement doc holds D15's contents, including the runbook as run (with Task 15's
carry-6 placement and the carry-10 note beside the UNREADABLE remedy), Task 0's tracer reading as a
Reading beside `T` and its `pwd -P` form, and the `GROK-BINARY:` line naming the version that ran
(operator decision D4: no phase document names a target version). `grok-runtime.md` §"Version and
compatibility" gains the AC-1.5 sentence (scored outcome) or the AC-1.8 sentence (smoke failure);
"These mappings were checked against grok 1.0.41." stays unchanged. SKILL.md's two AC-6.2 sites
change per D14's branch for the outcome. K2's `find` is re-pointed to the S3 text's remaining
`**unmeasured**` clause, same intent and test.

**Tests**: every outcome (4): `test_both_unmeasured_sites_point_to_the_measurement_doc`,
`test_measurement_doc_states_the_transfer_residual`, `test_unmeasured_sites_match_the_outcome`,
`test_grok_runtime_states_the_outcome_sentence`. The last reads §"Version and compatibility" of
`h-mad/references/grok-runtime.md` with `titled_section`, whitespace collapsed. On a scored
outcome it asserts the AC-1.5 sentence naming the version read from the measurement doc's
`GROK-BINARY:` line by D14's slot rule and naming `docs/03-analysis/grok-audit-surface.measurement.md`;
on a smoke failure it asserts the AC-1.8 sentence instead. On every outcome it asserts that
"These mappings were checked against grok 1.0.41." is present, unchanged. On MISS or INCONCLUSIVE
only (1 more): `test_never_gate_section_keeps_two_surface_routing_off_pass`.

**Acceptance Criteria**:
- [ ] AC-T16.1: The `MAINLEAK: CLEAN` line in the doc names the commit it scanned.
- [ ] AC-T16.2: `test_unmeasured_sites_match_the_outcome` fails when the doc has no `GROK-BINARY:` line,
  when it reads `GROK-BINARY: unrecorded`, or when D14's slot rule yields no version on a smoke failure.
- [ ] AC-T16.3: `--check-anchors` reads `ANCHORS: ANCHORS_OK` after the K2 re-anchor, and the spec run
  reads `MUTATION: ALL_CAUGHT` with `crash_kills=0` and `untargeted=0/172` on PASS or a smoke
  failure (K6 below), or `untargeted=0/174` on MISS or INCONCLUSIVE (K4, K5 and K6 below).
- [ ] AC-T16.4 (MISS or INCONCLUSIVE only; audit cycle 1): before K4 and K5 are added,
  `test_never_gate_section_keeps_two_surface_routing_off_pass` is observed failing against each of
  the two mutated texts and passing on the restored text. The harness run is that observation: each
  row is required green before it is applied and failing after.

**RED split**: PASS, MISS, INCONCLUSIVE or smoke failure: the 4 every-outcome tests F
(`test_grok_runtime_states_the_outcome_sentence` fails at RED because the AC-1.5 or AC-1.8
sentence is absent; that RED is the negative observation for its outcome-sentence assertion). MISS or
INCONCLUSIVE adds `test_never_gate_section_keeps_two_surface_routing_off_pass`, which is P at RED (the
section is unchanged at S0), so 5 nodes, 4 F, 1 P; on PASS or a smoke failure, 4 nodes, 4 F, 0 P.
Because that one test is P at RED, a RED run never shows that it can fail. K4 and K5 show it (axis:
a test that is P at RED needs a negative run).

**Mutation rows**: on every outcome, 1 new row, K6. Its target's host-mapping assertion passes at
RED (the 1.0.41 sentence is there at S0), so K6 is the negative observation for that assertion.
K2 is re-anchored, not added. On MISS or INCONCLUSIVE, 2 more rows, K4 and K5, one per property
the off-PASS test asserts:

| name | file | find | replace | test |
|---|---|---|---|---|
| `never-gate-three-surface-leak` (K4) | `SKILL.md` | ``When Codex is unavailable and `fallback_agent=grok`, use `--surfaces agy,grok` `` | the same with `--surfaces codex,agy,grok` | `tests/test_grok_audit_surface_docs.py::test_never_gate_section_keeps_two_surface_routing_off_pass` |
| `never-gate-family-sentence-dropped` (K5) | `SKILL.md` | `that is three reports, of which two share a model family` | `that is three reports, of which two share a vendor` | `tests/test_grok_audit_surface_docs.py::test_never_gate_section_keeps_two_surface_routing_off_pass` |
| `grok-runtime-host-sentence-changed` (K6) | `references/grok-runtime.md` | `These mappings were checked against grok 1.0.41.` | `These mappings were checked against grok 1.0.40.` | `tests/test_grok_audit_surface_docs.py::test_grok_runtime_states_the_outcome_sentence` |

K4's find is K3's (1 matching line in `h-mad/SKILL.md` at `30917a1a`). K6's find has 1 matching line in
`h-mad/references/grok-runtime.md` at `30917a1a` (`grep -cF`). K5's find is on one line (line
2024 at `30917a1a`, 1 matching line by `grep -cF`); the test collapses whitespace, so a change to
either half of the sentence fails it.

**Dependencies on other tasks**: Task 15.

---

## Task 17: S4 route (PASS only)

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_grok_audit_surface_docs.py` (extend)
**Task shape**: `new-behaviour`

**Description**: Runs only when Task 16 published `SEEDSCORE: PASS`. D14's AC-7.1 (the
"**Which two surfaces …**" paragraph of §"Never gate on one audit pass" names
`--surfaces codex,agy,grok` and points to the measurement doc; the "three reports, of which two share a
model family" sentence is reworded per AC-7.1), AC-7.2 (D14's availability-fallback words, verbatim),
AC-8.3 (D14's falsification sentence, verbatim, at the AC-7.1 text). Both AC-8.3 targets are heading
lines of `h-mad/SKILL.md` at `30917a1a` (`## Verifying a review finding before acting on it`,
`### Record a rejected finding in the rejections ledger, never in a gated document`).

**Tests** (4): `test_never_gate_section_names_three_surface_first_gate`,
`test_never_gate_section_names_grok_falsification`,
`test_never_gate_section_names_the_grok_unavailable_fallback`,
`test_never_gate_section_names_the_twice_unverified_grok_fallback`.

**Acceptance Criteria**:
- [ ] AC-T17.1: The four tests pass; `tests/test_grok_fallback_docs.py` still passes (K3's pin
  survives the edit, and `--check-anchors` reads `ANCHORS: ANCHORS_OK`).

**RED split**: 4 nodes; 4 F, 0 P.

**Mutation rows**: none.

**Dependencies on other tasks**: Task 16 with `SEEDSCORE: PASS`.

---

## Carry list disposition

| Carry item | Lands in |
|---|---|
| 1 OPEN-DECISION, re-walk before step 6 | Task 5, as `OPEN-DECISION … — resolve in 5d` with implementations (a) and (b) |
| 2 destructive symlink-following reset | Task 5: the no-follow rule; three fixtures, each asserting the link is not followed and is acted on: delete-through directory end to end, and write-through file and write-through parent at `restore_expected`'s own boundary (an end-to-end fixture cannot see those two guards, audit cycle 1); three rows; the concurrent-writer residual stated |
| 3 reset fixtures' default parent and `--purpose s1 --doc d1` | Task 5, "Fixtures" |
| 4 `test_smoke_unrecognised_effort_item_refuses` and its P-row | Task 7 (`p-smoke-effort-unknown`) |
| 5 one grok type-set reader, or the exact open class | Task 7: `grok_log_types`, one difference from `scan_grok` stated exactly; the design's "guaranteed" and its `RecursionError` clause reported |
| 6 agy provenance `$STEM` placement | Task 15 step 5; Task 16 publishes it in the runbook |
| 7 (measurement) X3/X4 find the collapse marker | "Measurement acknowledgements" below; Task 8's X3/X4 rows find the marked line |
| 8 (measurement) "seven" vs "eight" reset tests | "Measurement acknowledgements" below |
| 9 pre-S1 `exec agy` tracer | Task 0; consumed in Task 15 step 2 |
| 10 wrong-file UNREADABLE needs a new smoke | Task 7 (stated), Task 15 step 7, Task 16 runbook; spec gap reported |
| 11 collapse marker, per-alternative P-rows, re-derived counts | Tasks 5, 7, 8 (rows), Task 14 (AC-T14.4) |
| 12 argparse usage errors | Task 2: every argparse exit path (`error()`, help, version, abbreviation) ends on the mode's token (`_TokenArgumentParser` at every level, `add_help=False`, `allow_abbrev=False`, the `--data` path read from raw argv); `test_usage_error_prints_the_mode_token`, `test_help_flag_prints_the_mode_token`, `test_abbreviated_flag_is_a_usage_error`; the no-mode argv per the operator ruling (`PROBE: UNREADABLE reason=unknown_mode`, `test_unknown_mode_prints_the_probe_token`) |
| 13 `--reset` with a non-`s1` purpose | Task 5 (`ResetPurposeNotS1`, `test_build_root_reset_refuses_a_non_s1_purpose`) |
| 14 step-3 wrong-file reachability | Task 7 (synthetic pairing stated), Task 6 (`test_record_cycle_copies_stem_files_byte_for_byte`) |
| 15 residual-(2) depth from `GROK_MAX_DEPTH` | Task 7 |

## Measurement acknowledgements

Both are readings of the design text at `30917a1a` (unchanged since `a6a1571a`); neither is moved by
this plan, and neither has a Task.

- **Carry 7.** Re-run: `grep -n 'M:GAS-' docs/02-design/features/grok-audit-surface.design.md`.
  Reading: `M:GAS-COLLAPSE-WIRE` occurs 2 times in the design (lines 296 and 555), neither inside the
  D12 fenced code block (lines 301–307), which holds only the `MUST-COUNT` and `SHOULD-COUNT` markers.
  So the rows preamble's "their finds are the two marked lines of the D12 code block" covers X1, X2,
  X5, X6 and not X3, X4, whose find is the probe line carrying `# M:GAS-COLLAPSE-WIRE` (Task 8).
- **Carry 8.** The carried re-run command, `git diff de149bc6 a6a1571a -- docs/02-design/features/grok-audit-surface.design.md | grep -o 'test_build_root_reset_[a-z_]*' | sort -u`,
  prints 11 distinct names, because it reads context lines as well as additions. The count of names
  new in v1.4 is
  `comm -13 <(git show de149bc6:docs/02-design/features/grok-audit-surface.design.md | grep -o 'test_build_root_reset_[a-z_]*' | sort -u) <(git show a6a1571a:docs/02-design/features/grok-audit-surface.design.md | grep -o 'test_build_root_reset_[a-z_]*' | sort -u) | wc -l`:
  8 distinct test names (3 at `de149bc6`, 11 at `a6a1571a`): seven refusals plus one must-not-refuse,
  as the carry item says, against the v1.4 change log's "seven".

## Version History
- v1.0: Initial impl-plan draft (Phase 5a, 2026-10-19), from design v1.4 (`a6a1571a`), spec v1.7 and plan v1.5 (`28ec5bfc`); answers no audit cycle (first draft) and places all 15 Phase 5 carry items. 18 Tasks; 165 mutation rows (28 named, 137 P-rows); 111 marker sites. Premises read at `30917a1a`.
- v1.1: 2026-10-19, answers the operator ruling on the AC-5.1 / D2 unknown-mode gap (no audit cycle): an argv whose first word is not one of the nine modes now prints PROBE: UNREADABLE reason=unknown_mode first, then usage, exit 2; Task 2 adds test_unknown_mode_prints_the_probe_token (2 ids) and row p-unknown-mode-token; RED 20 F; totals 166 rows (138 P-rows), 112 marker sites.
- v1.2: 2026-10-19, answers impl-plan audit cycle 1 (agy p1: 1 must, 2 should; codex p2: 6 must, 1 should; on v1.1 5490674): every argparse exit path ends on the mode's token (top-level _TokenArgumentParser, add_help=False, allow_abbrev=False, --data read from raw argv; +2 tests, +2 rows); tracebacks only for undeclared exceptions and surfaced in assertion messages (+1 row); in-process loads compile from source (load_probe); Task 5's write and parent no-follow guards tested at restore_expected's boundary; AC-T6.1 split pre-write vs ref_unconfirmed; extract_all takes sources; p-fab-fraction Fraction-preserving; Task 16 adds K4/K5 on MISS/INCONCLUSIVE. Rejected: agy should-fix on Task 17 counts (quoted text absent). Totals 169 rows at S0 (141 P-rows), 171 on MISS/INCONCLUSIVE, 115 marker sites; Task 2 RED 30 F.
- v1.3: 2026-10-19, corrective revision answering impl-plan audit cycle 2 (agy p1: 0 must, 2 should; codex p2: 3 must, 2 should; on v1.2 4b8400ba): Refusal and the reset classes subclass ProbeRefusal, with a traceback-absence check on Task 5's refusals; in-process main(argv) assertions forward captured stderr; reproduce commands and outputs beside the argparse and O_NOFOLLOW readings; Test 4's smoke token carries input_unparseable plus the --data value; the smoke's open input reaches refusal_token through _OPEN_INPUT; must-not-parse fixtures for the ROOT and Effort parsers (+2 tests, +2 rows); Task 16 pins grok-runtime.md (test_grok_runtime_states_the_outcome_sentence, row K6). Totals 171 rows at S0 (143 P-rows), 172 or 174 after Task 16, 117 marker sites.
