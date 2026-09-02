# Implementation Plan: audit-report-docs-copy

> Source: docs/02-design/features/audit-report-docs-copy.design.md (post-audit — gated at cycles 9+10 as v1.11; every later design entry is a 5b-audit sweep with no design decision changed; the impl-plan tracks the design's NEWEST Version History entry — no version number is pinned here because every later entry is a sweep)
> Branch target: BrightGold70/audit-report-docs-copy (the Orca-assigned feature branch; already checked out in worktree `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy`)

## Executive Summary
Six ordered tasks: the collector gains `surface`/`overwrite`/readback (1), the gate gains the
transport refusal (2), the CLI wraps the collector (3), the wrapper verb wires to the CLI (4,
`wiring`), SKILL.md + references carry the recipe (5), and the 23-mutation spec proves every
guard bites (6). Tests run with `python3.11 -m pytest` from the repository root; the AC-2.9
hand replay runs after task 3.

## Task 1: collector — surface, overwrite, readback

**Production file**: `h-mad/scripts/h_mad_audit_cycle.py`
**Test file**: `h-mad/tests/test_h_mad_collect_report.py`
**Task shape**: `new-behaviour`

**Description**: Extend the audit-cycle collector so one copier serves both audit legs.
`_collected_path` accepts an optional validated `surface` token (`.<surface>.md` instead of
`.p<i>.md`); both writers take `overwrite` (default `True`, unchanged verb behaviour), refuse
to clobber differing bytes when `False` by raising `CollectConflict`, and read back what they
wrote; `collect()` runs its whole body under an `OSError→OperationalError` guard, handles the
same-file (docs path as `$RP`) case FIRST (marker required, marker removed, existence-blind
`same`), then the non-empty already-collected short-circuit, then the existing rungs; the
`--out` rung is skipped when `spec.out_path is None`. Existing `audit-cycle` callers pass no
new arguments and produce byte-identical output.

**Code structure**:
```python
SURFACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
PASS_INDEX_RE = re.compile(r"^p\d+$")

class CollectConflict(OperationalError):
    def __init__(self, collected: Path, delivered: str) -> None: ...
    collected: Path
    delivered: str

def validate_surface(surface: str) -> str:
    """Return the token; ValueError naming it when it fails SURFACE_RE or matches PASS_INDEX_RE."""

@contextlib.contextmanager
def _fs_errors(what: str):
    """OSError → OperationalError(f"{what}: {exc}")."""

def _collected_path(*, project_root: Path, feature: str, phase: str, cycle: int,
                    index: int, surface: str | None = None) -> Path: ...

def _readback_equal(path: Path, data: bytes) -> bool: ...
def _finalize_write(collected_path: Path, data: bytes) -> Path:
    """unlink → write_bytes → _readback_equal or raise OperationalError('readback mismatch after write: <path>').
    The ONE write+readback used by BOTH writers, so the readback is one separable part."""

def _copy_collected_report(report_path: Path, collected_path: Path, *,
                           overwrite: bool = True) -> Path: ...
def _write_collected_report(report_text: str, collected_path: Path, *,
                            overwrite: bool = True) -> Path: ...

def collect(spec: PassSpec, *, grace: float, project_root: Path, feature: str, phase: str,
            cycle: int, surface: str | None = None, overwrite: bool = True
            ) -> tuple[str, Path | None]: ...
def _collect_unguarded(spec, *, grace, project_root, feature, phase, cycle, surface, overwrite): ...
```

**Acceptance Criteria**:
- [ ] AC-1.1: `_collected_path(project_root=r, feature="f", phase="plan", cycle=8, index=1)` == the same call with `surface=None`, ending `f.plan.audit.v8.p1.md`.
- [ ] AC-1.2: `surface="codex"` → `docs/01-plan/features/f.plan.audit.v8.codex.md`; `phase="design"` → `docs/02-design/features/f.design.audit.v8.codex.md`; `phase="impl-plan"` → `docs/01-plan/features/f.impl-plan.audit.v8.codex.md`.
- [ ] AC-1.3: `surface="p2"`, `"codex.draft"`, `".x"`, `""` each raise `ValueError` whose message contains the token.
- [ ] AC-1.4: `collect(spec, ..., surface="codex")` writes at the AC-1.2 path; `collect(spec, ...)` (no `surface`) writes at the AC-1.1 path; the existing `test_h_mad_audit_cycle.py` collect tests pass unchanged.
- [ ] AC-1.5: exactly one function in `h-mad/scripts/*.py` builds the `.audit.v` docs-path string (`_collected_path`).
- [ ] AC-2.4 (writer): `_copy_collected_report` onto an identical existing file does not write (mtime unchanged) and returns the path.
- [ ] AC-2.5 (writer): onto a differing existing file with `overwrite=False` raises `CollectConflict(delivered="report-file")` and leaves bytes unchanged; with `overwrite=True` replaces them; `_write_collected_report` behaves the same with `delivered="out"` (AC-2.6a/2.6b).
- [ ] AC-2.12 (writers): with `_readback_equal` monkeypatched to return False, `_copy_collected_report` raises `OperationalError` whose message starts with `readback` AND `_write_collected_report` raises the same (both go through `_finalize_write`); with `Path.unlink` monkeypatched to a no-op, the same-file marker removal raises `OperationalError` starting with `readback`.
- [ ] AC-2.8 (collect order): `spec.report_path` == docs path with a `.done` marker → `("report-file", path)` and the marker is gone; without a marker (grace 0) → `("none", None)` even when `--out` holds a valid report; a docs-path `report_path` that does not exist → `("none", None)`.
- [ ] AC-2.11 (collect): distinct `report_path` with NO marker, docs file present and byte-identical → `("report-file", docs)`; both files empty → `("none", None)`.
- [ ] A `PassSpec(index=1, report_path=tmp_path / "missing.report.md", out_path=None, rc=0)` (the report file does not exist): `collect()` skips `_run_extract_report` (a fake `_script` dir with a failing extractor proves it was not called) and returns `("none", None)`.
- [ ] `_fs_errors`: a `PermissionError` raised inside any writer surfaces as `OperationalError`, never a raw `OSError`.

**Dependencies on other tasks**: None

---

## Task 2: gate — transport refusal and grammar tests

**Production file**: `h-mad/scripts/h_mad_audit_gate.py`
**Test file**: `h-mad/tests/test_h_mad_audit_gate.py`
**Task shape**: `new-behaviour`

**Description**: Define the single transport grammar and refuse to score a transport-named
path. `TRANSPORT_RE = ^audit_[^.]+\.report\.md$`; `is_transport_path()`; in `main()` the
feature name is derived first, then — after the `--verify-stamp` branch and BEFORE `read_text`
— a transport name prints exactly `GATE: INVALID must=0 should=0` and
`[H-MAD] <stem> gate INVALID (transport file — collect it into docs first: h_mad_collect_report.py)`
and returns 2. The feature slot carries the dot-free stem verbatim. All other behaviour is
unchanged. Tests also pin the downstream contract in `h-mad/tests/test_h_mad_audit_cycle.py`
(AC-3.3) and the grammar-disjointness property (AC-1.6) and two-direction corpus (AC-3.5a).

**Code structure**:
```python
TRANSPORT_RE = re.compile(r"^audit_[^.]+\.report\.md$")

def is_transport_path(path: Path) -> bool:
    """True iff path.name matches TRANSPORT_RE."""

# in main(), after the --verify-stamp branch:
#   feature = args.audit_file.name.split(".")[0] or "unknown"
#   if is_transport_path(args.audit_file): print(...INVALID...); return 2
```

**Acceptance Criteria**:
- [ ] AC-3.1: the gate on `<tmp>/audit_f_plan_cycle3_codex.report.md` (well-formed) prints first line `GATE: INVALID must=0 should=0`, a `[H-MAD]` line containing `transport file`, exit 2; likewise for `audit_hnag_c28_agy.report.md`, `audit_hnag_implplan_c11.report.md`, `audit_f_plan_cycle8_codex_draft.report.md`, `audit_f_plan_cycle8_agy_p2.report.md`.
- [ ] AC-3.2: the same bytes at `<tmp>/docs/01-plan/features/f.plan.audit.v3.codex.md` → `GATE: PASS|FAIL must=<n> should=<m>`, exit 0.
- [ ] AC-3.3 (in `test_h_mad_audit_cycle.py`): `gate(tmp_path / "audit_f_plan_cycle3_codex.report.md", ack_file=None)` (the file holding a well-formed report) returns `("INVALID", 0, 0, [])`; `combine([PassResult(index=1, delivered="report-file", collected_path=p, verdict="INVALID", must=0, should=0, findings=[], effort=None)])` returns `("UNVERIFIED", "no_gate_sections:p1")`.
- [ ] AC-3.5: `f.report.md`, `gate-blindness-hardening.report.md`, `audit-report-docs-copy.report.md`, `audit_f.plan.audit.v8.report.md`, `<tmp>/x.md` → scored normally (exit 0, `GATE: PASS|FAIL`).
- [ ] AC-3.5a: a fixture list of `(name, kind)` triples with `kind ∈ {transport, audit_doc, other}` covering every shape in AC-3.1/3.5 plus `.audit.v<N>.md`, `.p<i>.md`, `.codex.md`, `.codex_draft.md`, `audit_f.plan.audit.v8.codex.md`; every entry satisfies `(kind == "transport") == bool(TRANSPORT_RE.match(name))`; every `audit_doc` entry matches `h_mad_cycle_counts._VERSION_RE`; `other` entries (`f.report.md`, `gate-blindness-hardening.report.md`, `audit-report-docs-copy.report.md`, `x.md`) are asserted only NOT to match `TRANSPORT_RE`; NO name matches both regexes.
- [ ] AC-3.6: `<tmp>/docs/04-report/features/x.report.md` with gate sections → exit 0.
- [ ] AC-3.7: for every `*.audit.v*.md` under this repository's `docs/` (live + `docs/archive`), `is_transport_path()` is False (the test walks the real tree; ≥ 100 files found or the test fails as vacuous).
- [ ] AC-1.6 (property): for `(feature, surface)` in `[("audit_f","report"),("audit_x","report_md"),("audit_","p"),("f","codex"),("nlm-cli-version-pin","agy")]` × phases, `_collected_path(...).name` matches `_VERSION_RE` and does not match `TRANSPORT_RE`.
- [ ] `--verify-stamp` on a transport-named path still reports `GATESTAMP: UNSTAMPED` (unchanged behaviour).

**Dependencies on other tasks**: Task 1 (AC-1.6 needs `_collected_path(surface=<token>)`)

---

## Task 3: `h_mad_collect_report.py` — the CLI

**Production file**: `h-mad/scripts/h_mad_collect_report.py`
**Test file**: `h-mad/tests/test_h_mad_collect_report.py`
**Task shape**: `new-behaviour`
**Checkpoint artifact**: `docs/01-plan/features/audit-report-docs-copy.plan.md` (Version History entry written by the AC-2.9 hand replay, via the helper)

**Description**: Stdlib-only CLI over `collect()` implementing design D2 (with one
simplification from 5b audit v3: the CLI does NOT pre-validate `--surface`; `_collected_path`
is the single validator and its `ValueError` reaches the outer handler): required flags
`--feature --phase --cycle --surface --report --project-root`, optional `--out --grace
(default 5) --force`. One outer `try`/`except (OperationalError, OSError, ValueError)` encloses
everything after argparse; argparse's `SystemExit` is caught → `[H-MAD] unknown collect
usage_error`, return 2. Verdict line first (`COLLECT: OK|MISSING|CONFLICT path=<docs>
delivered=report-file|out|none[ forced=1]`), detail lines (`marker: removed <RP>.done`), then
exactly one `[H-MAD] <feature> collect <verdict|usage_error|operational_error|readback_failed>`
marker; exit 0 on any verdict, 2 on operational error with no `COLLECT:` line. `--force`
retries `collect(overwrite=True)` inside the outer try after a `CollectConflict`. Imports
`collect`, `PassSpec`, `_collected_path`, `CollectConflict`, `OperationalError` from
`h_mad_audit_cycle` (NOT `validate_surface` — the CLI must not pre-validate; `_collected_path`
does it); imports nothing from the gate.

**Code structure**:
```python
def build_parser() -> argparse.ArgumentParser:
    """Required: --feature --phase{plan,design,impl-plan} --cycle --surface --report --project-root;
    optional: --out, --grace (default 5.0), --force."""
def main(argv: list[str] | None = None) -> int:
    try:                                   # its OWN handler: SystemExit is a BaseException and
        args = build_parser().parse_args(argv)   # would escape the (OperationalError, OSError,
    except SystemExit:                     # ValueError) handler below
        print("[H-MAD] unknown collect usage_error"); return 2
    try:                                   # the ONE outer try around everything else (design D2 steps 1-6)
        return _run(args)                  # semantic checks, spec, collect, --force retry, token+marker
    except (OperationalError, OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        reason = "readback_failed" if str(e).startswith("readback") else "operational_error"
        print(f"[H-MAD] {args.feature} collect {reason}"); return 2

def _run(args: argparse.Namespace) -> int:
    """Design D2 steps 1-6; prints the COLLECT: line, detail lines, and the [H-MAD] marker."""
```
(Function bodies shown as `...` elsewhere in this plan are contracts per the impl-plan
template — "key signatures, not implementations"; every signature, flag, path and token is
exact.)

**Acceptance Criteria**:
- [ ] AC-2.1: RP + `.done`, no docs file → stdout line 1 `COLLECT: OK path=<docs> delivered=report-file`, last line `[H-MAD] f collect OK`, exit 0, `filecmp.cmp(RP, docs, shallow=False)`.
- [ ] AC-2.2: RP absent, no `--out` → `COLLECT: MISSING path=<docs> delivered=none`, exit 0, docs file absent.
- [ ] AC-2.3: RP present, no `.done`, `--grace 0` → `MISSING`.
- [ ] AC-2.4: docs identical → `OK`, docs mtime unchanged.
- [ ] AC-2.5: docs differs → `COLLECT: CONFLICT path=<docs> delivered=report-file`, exit 0, docs unchanged; with `--force` → `COLLECT: OK path=<docs> delivered=report-file forced=1`, docs == RP.
- [ ] AC-2.6: RP absent, `--out` with a sentinel-wrapped report → `COLLECT: OK path=<docs> delivered=out`, docs holds the extracted text.
- [ ] AC-2.6a/2.6b: `--out` rung with differing docs → `COLLECT: CONFLICT path=<docs> delivered=out` (and `--force` → `COLLECT: OK path=<docs> delivered=out forced=1`); identical → `COLLECT: OK path=<docs> delivered=out`, mtime unchanged.
- [ ] AC-2.7: `--surface p2` and `--surface codex.draft` → exit 2, stderr names the token, no `COLLECT:` line, stdout marker `[H-MAD] f collect operational_error`.
- [ ] AC-2.8: `--report <docs path>` with `.done` → `OK`, detail line `marker: removed <docs>.done`, marker gone; without marker → `MISSING`; nonexistent docs path with a valid `--out` → `MISSING`, nothing written.
- [ ] AC-2.9 (incident replay, suite): isolated root, no docs copy: (i) `h_mad_audit_gate.py <RP>` → `GATE: INVALID`, exit 2; (ii) CLI → `COLLECT: OK path=<docs> delivered=report-file`, `filecmp` True; (iii) gate on the printed path → exit 0.
- [ ] AC-2.10: `--project-root` not a directory; a FILE at `docs/01-plan/features`; each missing required flag; `--phase bogus` → exit 2, no `COLLECT:` line, stdout marker `usage_error` (argparse cases) or `operational_error`; a `0o555` docs parent with differing docs + `--force` → exit 2, `operational_error`, no traceback on stderr (skipped as root).
- [ ] AC-2.11: docs identical, RP present, no marker → `COLLECT: OK path=<docs> delivered=report-file`.
- [ ] AC-2.12: the CLI is exercised IN-PROCESS for this case — `h_mad_collect_report.main([...])` with `h_mad_audit_cycle._readback_equal` monkeypatched to return False (no production seam, no env var) — → returns 2, captured stdout is exactly the `[H-MAD] f collect readback_failed` line (no `COLLECT:` line), for the report-file rung, the `--out` rung, and inside a `--force` retry.
- [ ] AC-2.9h (hand replay, executable checkpoint — run once after this task's GREEN, before Task 4; distinct from the suite half AC-2.9 above): 
  ```bash
  S=/tmp/audit_nlmpin_plan_cycle8_codex.report.md   # real survivor; if absent after a reboot, use any /tmp/audit_*_codex.report.md and record which
  R=$(mktemp -d)/replay && mkdir -p "$R/docs/01-plan/features" && cp "$S" "$R/rp.report.md" && : > "$R/rp.report.md.done"
  mv "$R/rp.report.md" "$R/audit_nlmpin_plan_cycle8_codex.report.md"; mv "$R/rp.report.md.done" "$R/audit_nlmpin_plan_cycle8_codex.report.md.done"
  python3 h-mad/scripts/h_mad_audit_gate.py "$R/audit_nlmpin_plan_cycle8_codex.report.md"; echo "rc=$?"          # expect GATE: INVALID, rc=2
  python3 h-mad/scripts/h_mad_collect_report.py --feature nlm-cli-version-pin --phase plan --cycle 8 --surface codex --report "$R/audit_nlmpin_plan_cycle8_codex.report.md" --project-root "$R"   # expect COLLECT: OK path=<R>/docs/01-plan/features/nlm-cli-version-pin.plan.audit.v8.codex.md delivered=report-file
  cmp -s "$S" "$R/docs/01-plan/features/nlm-cli-version-pin.plan.audit.v8.codex.md" && echo identical
  python3 h-mad/scripts/h_mad_audit_gate.py "$R/docs/01-plan/features/nlm-cli-version-pin.plan.audit.v8.codex.md"; echo "rc=$?"   # expect GATE: PASS|FAIL, rc=0
  ```
  The four outputs are recorded in `audit-report-docs-copy.plan.md`'s Version History via `h_mad_version_history.py <plan> --version v1.<next-unused> --text "AC-2.9h hand replay <date> survivor=<S>: gate(RP)=<GATE line> rc=<n> · collect=<COLLECT line> · cmp=<identical|DIFFER> · gate(docs)=<GATE line> rc=<n>"` — ONE line, the four results joined by ` · `, because the helper refuses newline-bearing text (`multiline_text`, verified by dry-run 2026-09-02) and a duplicate version (read the newest entry first and use the next number). That entry is the checkpoint's evidence, and Task 4 does not start until it exists.
- [ ] Every exit path prints exactly one `[H-MAD] <feature|unknown> collect <verdict|usage_error|operational_error|readback_failed>` line — `unknown` on the argparse path (a missing `--feature` cannot supply the name), `<feature>` everywhere else.

**Dependencies on other tasks**: Task 1, Task 2 (AC-2.9 step i needs the refusal)

---

## Task 4: `hmad-dispatch collect-report` verb

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_collect_report.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/hmad-dispatch.sh:_cmd_collect_report` → `python3 "$here/h_mad_collect_report.py" "$@"` (with `here="${HMAD_AUDIT_CYCLE_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)}"`), plus the `collect-report)` arm in `main()` and the name in the `# Verbs:` header line
**WIRE-PIN**: `h-mad/tests/test_hmad_dispatch_collect_report.py::test_collect_report_verb_execs_script_with_argv`

**Description**: The same pure-delegation shape as `report-wait` (not byte-identical: this
verb resolves `here` through the `HMAD_AUDIT_CYCLE_SCRIPT_DIR` override so the stub seam the
audit-cycle tests already use applies). No logic in bash: argv passes through
verbatim, exit code and stdout propagate unchanged. The stub seam is the existing
`HMAD_AUDIT_CYCLE_SCRIPT_DIR` override (audit-cycle's tests already use it).

**Code structure**:
```bash
_cmd_collect_report() {  # <args passed verbatim to h_mad_collect_report.py>
  local here
  here="${HMAD_AUDIT_CYCLE_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)}"
  python3 "$here/h_mad_collect_report.py" "$@"
}
# main(): collect-report) _cmd_collect_report "$@" ;;
```

**Acceptance Criteria**:
- [ ] AC-4.1 (WIRE-PIN): with `HMAD_AUDIT_CYCLE_SCRIPT_DIR` pointing at a stub dir whose `h_mad_collect_report.py` records `sys.argv[1:]` to a file, prints `STUB-OUT`, and exits 7: `hmad-dispatch collect-report --feature f --phase plan --cycle 1 --surface codex --report /x --project-root /y` exits 7, stdout is `STUB-OUT`, and the recorded argv equals the six flag/value pairs in order.
- [ ] AC-4.3: `hmad-dispatch collect-reportx --feature f` prints `unknown verb` on stderr, exits 2, and the stub recorded nothing.
- [ ] AC-4.2 (half): the `# Verbs:` header line of `hmad-dispatch.sh` (located by its `# Verbs:` prefix, not by line number) contains `collect-report`.
- [ ] AC-3.5a (wrapper half): under the existing audit-cycle stub harness (`install_audit_cycle_stubs`), the `--report-file` value the assembler stub receives matches `h_mad_audit_gate.TRANSPORT_RE`.

**Dependencies on other tasks**: Task 3

---

## Task 5: recipe — SKILL.md and references

**Production file**: `h-mad/SKILL.md` (and `h-mad/references/orchestration-mode.md` for the verb-table row)
**Test file**: `h-mad/tests/test_h_mad_collect_report_docs.py`
**Task shape**: `new-behaviour`

**Description**: Add the new top-level section `## Second surface — the codex leg` immediately
after `## Putting \`hmad-dispatch\` on PATH` and before `## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)` (design D5 body:
assemble `--report-file` → `exec codex` → `collect-report --surface codex` → read the
`COLLECT:` token, halt `<phase>:report_not_collected` with `[H-MAD] <feature> <phase> halted
reason=report_not_collected` on anything but `OK` → gate the printed docs path, never `$RP`);
one pointer sentence inside the `audit-cycle` paragraph of `## Audit prompt assembly`; one
sentence in step 9 after the `report-wait` redirect ("The gate refuses a path named like a
transport file (`audit_*.report.md`) — gate the docs path, never `$RP`."); an
`h_mad_collect_report.py` entry in the helper registry naming the token set, the exit
contract, `--force` and readback; a `collect-report` row beside `report-wait` in
`h-mad/references/orchestration-mode.md`'s verb table. `test_h_mad_audit_cycle_docs.py` must
stay green.

**Code structure**:
```python
# tests only — docs task. Helpers in the new test file:
def _section(text: str, start: str, end: str) -> str: ...
def _second_surface() -> str: ...   # "## Second surface — the codex leg" → "## Helper scripts"
```

**Acceptance Criteria**:
- [ ] AC-5.1: `grep -c 'collect-report' h-mad/SKILL.md` ≥ 2.
- [ ] AC-5.2: `python3.11 -m pytest h-mad/tests/test_h_mad_audit_cycle_docs.py -q` passes unchanged.
- [ ] AC-5.3: within the new section, the indices of `exec codex` < `collect-report` < `report_not_collected` < `h_mad_audit_gate.py`; the line containing `h_mad_audit_gate.py` does not contain `$RP`.
- [ ] AC-5.4: the helper-registry entry for `h_mad_collect_report.py` contains `COLLECT: OK|MISSING|CONFLICT`, `exit 0`, `2`, `--force`, `readback`.
- [ ] AC-4.2 (other half): `references/orchestration-mode.md` verb table has a `collect-report` row adjacent (within 2 lines) to the `report-wait` row.
- [ ] AC-3.5a (docs half): the 6.6 literal `RP=/tmp/audit_<feature>_<phase>_cycle<N>.report.md` read from SKILL.md, instantiated with `f`/`plan`/`3` and with the `_codex` suffix form from the new section, satisfies `is_transport_path(Path(instantiated))` (the grammar applies to `Path.name`; the full `/tmp/…` string would not match `^audit_`).
- [ ] Step 9 contains the sentence naming `audit_*.report.md` and "never `$RP`".
- [ ] The `## Audit prompt assembly` section contains the pointer sentence naming `Second surface`.

**Dependencies on other tasks**: Task 4 (the verb name must exist)

---

## Task 6: mutation spec

**Production file**: `h-mad/tests/mutation-specs/collect_report.json`
**Test file**: `h-mad/tests/test_h_mad_collect_report.py` (the primary source of named tests; the spec's `command` runs the FIVE new/changed test files — `test_h_mad_collect_report.py`, `test_h_mad_audit_gate.py`, `test_h_mad_audit_cycle.py`, `test_hmad_dispatch_collect_report.py`, `test_h_mad_collect_report_docs.py`; `test_hmad_dispatch_audit_cycle.py` is NOT edited)
**Task shape**: `new-behaviour`

**Description**: The 23-mutation spec (`root: ../..`, `command: python3.11 -m pytest <the
five new/changed test files> -q`, `target_command: python3.11 -m pytest -q`), each mutation an
exact `find`/`replace` in a production file with a named `test`: (a) copy writes empty; (b)
CONFLICT → overwrite; (b′) overwrite refused even with force; (c) surface validation removed;
(c′) validation rejects every token; (d) `_collected_path` ignores `surface`; (d′) emits
`.<surface>` when `None`; (e) CLI returns hard-coded `OK` without `collect()`; (e′) CLI enters `collect()` on the
bad-`--project-root` fall-through (the `is_dir()` refusal neutralized) — observable: with no
report and no `--out`, `_collected_path` merely joins paths and `collect()` returns
`("none", None)`, so the CLI would print `COLLECT: MISSING` / exit 0 where AC-2.10 requires
exit 2 + `operational_error` (the earlier claim that no fall-through was observable was
wrong for this path — 5b audit v8, codex; the `--surface` fall-through remains
unobservable and is not mutated); (f) verb execs wrong script; (f′) wrapper routes unknown verb
to the script; (g) gate refusal removed; (g′) gate refuses every `.report.md`; (h) copy
readback removed; (h′) out-rung conflict check removed; (i) `TRANSPORT_RE` loosened to
`^audit_.*\.report\.md$`; (i′) docs pattern loses `.audit.v` dots; (j) gate refusal drops
its `[H-MAD]` line; (j′) CLI operational-error path drops its marker; (k) gate refusal
returns 0 instead of 2 (exit-code-only); (k′) gate refusal prints `GATE: PASS must=0 should=0`
instead of `INVALID` (token-only); (l) CLI operational-error path returns 0 (exit-code-only);
(l′) CLI operational-error path also prints a `COLLECT: MISSING path=- delivered=none` line (no-token-only). One
mutant per separable output part of each guard: exit code, token, marker. Kill-verdicts come from the harness (`MUTATION: ALL_CAUGHT`) and anchor validity from
`--check-anchors` (`ANCHORS_OK`); the spec's SHAPE — exactly the 23 names, `_mechanism`
present, `test` present and resolvable — is proven by `test_mutation_spec_shape` (AC-6.3a),
because the harness treats `test` as optional and never reads `_mechanism`; the existing
`test_audit_cycle_mutation_specs_*` tests load only their own two specs and are not
touched (AC-6.4).

**Code structure**:
```json
{"root": "../..",
 "command": ["python3.11","-m","pytest","tests/test_h_mad_collect_report.py","tests/test_h_mad_audit_gate.py","tests/test_h_mad_audit_cycle.py","tests/test_hmad_dispatch_collect_report.py","tests/test_h_mad_collect_report_docs.py","-q"],
 "target_command": ["python3.11","-m","pytest","-q"],
 "mutations": [
  {"name": "gate-refusal-removed",
   "_mechanism": "The transport refusal is the RED direction of the whole feature: with it gone a /tmp report scores again.",
   "file": "scripts/h_mad_audit_gate.py",
   "find": "    if is_transport_path(args.audit_file):",
   "replace": "    if False:",
   "test": "tests/test_h_mad_audit_gate.py::test_gate_refuses_transport_names"}
 ]}
```
(One entry shown in full; the other 22 follow the table above with the exact `find` line
copied from the production file at implementation time.)

**Acceptance Criteria**:
**Mutation table** (the implementer fills `find`/`replace` with the exact production lines; the anchor intent and the named test are fixed here):

| # | name | file | anchor intent | test |
|---|---|---|---|---|
| a | copy-writes-empty | `scripts/h_mad_audit_cycle.py` | `_finalize_write` writes `b""` instead of `data` | `tests/test_h_mad_collect_report.py::test_cli_ok_copies_byte_identical` |
| b | conflict-becomes-overwrite | `scripts/h_mad_audit_cycle.py` | `if not overwrite: raise CollectConflict` → `if False:` | `tests/test_h_mad_collect_report.py::test_cli_conflict_preserves_docs` |
| b′ | force-still-refuses | `scripts/h_mad_collect_report.py` | forced retry passes `overwrite=False` | `tests/test_h_mad_collect_report.py::test_cli_force_overwrites` |
| c | surface-validation-removed | `scripts/h_mad_audit_cycle.py` | `validate_surface` returns token unchecked | `tests/test_h_mad_collect_report.py::test_cli_rejects_pass_index_surface` |
| c′ | surface-validation-rejects-all | `scripts/h_mad_audit_cycle.py` | `validate_surface` always raises | `tests/test_h_mad_collect_report.py::test_cli_ok_copies_byte_identical` |
| d | collected-path-ignores-surface | `scripts/h_mad_audit_cycle.py` | token = `f"p{index}"` regardless of surface | `tests/test_h_mad_collect_report.py::test_collected_path_surface_token` |
| d′ | collected-path-forces-surface | `scripts/h_mad_audit_cycle.py` | token = `str(surface)` even when None | `tests/test_h_mad_collect_report.py::test_collected_path_default_is_pass_index` |
| e | cli-skips-collect | `scripts/h_mad_collect_report.py` | `collect(...)` replaced by `("report-file", docs)` | `tests/test_h_mad_collect_report.py::test_cli_missing_when_no_report` |
| e′ | cli-collects-on-bad-root | `scripts/h_mad_collect_report.py` | `if not project_root.is_dir(): raise OperationalError(...)` → `if False:` | `tests/test_h_mad_collect_report.py::test_cli_operational_errors_exit_2_with_marker` |
| f | verb-execs-wrong-script | `scripts/hmad-dispatch.sh` | `h_mad_collect_report.py` → `h_mad_report_wait.py` in `_cmd_collect_report` | `tests/test_hmad_dispatch_collect_report.py::test_collect_report_verb_execs_script_with_argv` |
| f′ | verb-routes-unknown | `scripts/hmad-dispatch.sh` | `*)` arm calls `_cmd_collect_report "$@"` | `tests/test_hmad_dispatch_collect_report.py::test_unknown_verb_does_not_exec_script` |
| g | gate-refusal-removed | `scripts/h_mad_audit_gate.py` | `if is_transport_path(...)` → `if False` | `tests/test_h_mad_audit_gate.py::test_gate_refuses_transport_names` |
| g′ | gate-refuses-all-reports | `scripts/h_mad_audit_gate.py` | `TRANSPORT_RE` → `\.report\.md$` | `tests/test_h_mad_audit_gate.py::test_gate_scores_phase7_and_hyphen_report_names` |
| h | readback-removed | `scripts/h_mad_audit_cycle.py` | `_finalize_write` skips `_readback_equal` | `tests/test_h_mad_collect_report.py::test_out_rung_readback_failure_exits_2` |
| h′ | out-rung-conflict-removed | `scripts/h_mad_audit_cycle.py` | `_write_collected_report` passes `overwrite=True` | `tests/test_h_mad_collect_report.py::test_cli_out_rung_conflict` |
| i | transport-re-loosened | `scripts/h_mad_audit_gate.py` | `^audit_[^.]+` → `^audit_.*` | `tests/test_h_mad_audit_gate.py::test_grammars_are_disjoint_property` |
| i′ | docs-pattern-dedotted | `scripts/h_mad_audit_cycle.py` | `.audit.v` → `_audit_v` in `_collected_path` | `tests/test_h_mad_collect_report.py::test_collected_path_default_is_pass_index` |
| j | gate-refusal-drops-marker | `scripts/h_mad_audit_gate.py` | the `[H-MAD] <stem> gate INVALID (transport file ...)` print removed | `tests/test_h_mad_audit_gate.py::test_gate_refuses_transport_names` |
| j′ | cli-error-drops-marker | `scripts/h_mad_collect_report.py` | operational-error marker print removed | `tests/test_h_mad_collect_report.py::test_cli_operational_errors_exit_2_with_marker` |
| k | gate-refusal-exit-0 | `scripts/h_mad_audit_gate.py` | transport branch `return 2` → `return 0` | `tests/test_h_mad_audit_gate.py::test_gate_refuses_transport_names` |
| k′ | gate-refusal-wrong-token | `scripts/h_mad_audit_gate.py` | transport branch prints `GATE: PASS must=0 should=0` | `tests/test_h_mad_audit_gate.py::test_gate_refuses_transport_names` |
| l | cli-error-exit-0 | `scripts/h_mad_collect_report.py` | outer handler `return 2` → `return 0` | `tests/test_h_mad_collect_report.py::test_cli_operational_errors_exit_2_with_marker` |
| l′ | cli-error-prints-token | `scripts/h_mad_collect_report.py` | outer handler also prints `COLLECT: MISSING path=- delivered=none` | `tests/test_h_mad_collect_report.py::test_cli_operational_errors_exit_2_with_marker` |

- [ ] AC-6.3: the spec has exactly the 23 mutations above, each with `name`, `_mechanism`, `file`, `find`, `replace`, `test`; `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/collect_report.json` prints `MUTATION: ALL_CAUGHT mutations=23 caught=23 survived=0 refused=0 unreadable=0` (the harness appends `unreadable=` on every measured verdict — verified 2026-09-02).
- [ ] AC-6.3a (executable shape check — the harness treats `test` as optional and never reads `_mechanism`, verified 2026-09-02 in `h_mad_mutation_harness.py`): `tests/test_h_mad_collect_report.py::test_mutation_spec_shape` loads `tests/mutation-specs/collect_report.json` and asserts: exactly the 23 mutation `name`s in the table above, each entry has non-empty `_mechanism`, `file`, `find`, `replace`, `test`, each `file` exists under `root`, and each `test` is `<path>::<func>` where `<path>` exists and `def <func>(` appears in it.
- [ ] The named test for k/k′/l/l′ asserts ALL THREE parts of its guard's output (exit code, first stdout line, `[H-MAD]` line) so each single-part mutant is caught by it alone.
- [ ] `h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/collect_report.json` prints a line starting `ANCHORS: ANCHORS_OK`.
- [ ] AC-6.4: the existing `test_hmad_dispatch_audit_cycle.py::test_audit_cycle_mutation_specs_*` tests load ONLY the two audit-cycle specs under `h-mad/tests/specs/` (verified 2026-09-02: `GATING_MUTATION_SPEC`, `CONNECTIONS_MUTATION_SPEC`) and are NOT extended; they stay green. The new spec's shape and named-test existence are proven by the two harness commands above, which is what those tests prove for their own specs.
- [ ] AC-6.5: `python3.11 -m pytest h-mad/tests -q` is green from this worktree.

**Dependencies on other tasks**: Task 5

---

## Version History
- v1.0: Initial implementation plan draft.
- v1.1: 5b audit v1 fixes (agy p1 + codex): no env seam — the CLI readback case runs `main()` in-process with `_readback_equal` monkeypatched; both writers share `_finalize_write` so the readback is one separable part and the `--out` rung is pinned too; the AC-2.9 hand replay is an executable checkpoint with exact commands and a required Version-History paste; 19-row mutation table with fixed names/files/tests; AC-6.4 states the existing spec tests are not extended; verb wording.
- v1.2: 5b audit v2 fixes (codex; agy v2 clean): exit-code-only and token-only mutants for the gate refusal and the CLI error path (k, k′, l, l′ → 23); Task 6's test surface made explicit (five test files in `command`; `test_hmad_dispatch_audit_cycle.py` not edited).
- v1.3: 5b audit v3 fixes (agy p1 + codex): replay evidence recorded via the version-history helper at the next unused version (no hard-coded `v1.7`); Task 6 prose matches AC-6.4; Task 5 metadata names orchestration-mode.md; design pointer v1.13; mutant e′ dropped as unkillable (the surface is validated in `_collected_path`; the CLI no longer pre-checks it) → 22; Task 6 JSON lists all five test files.
- v1.4: 5b audit v4 fixes (codex): AC-6.3a executable spec-shape test (the harness does not enforce `test`/`_mechanism`); `validate_surface` dropped from the CLI import list.
- v1.5: 5b audit v5 sweep (codex): Task 3 lists its checkpoint artifact (the plan's Version History entry); design pointer tracks the newest entry.
- v1.6: 5b audit v6 sweep (codex; agy v6 clean): AC-3.5a fixture kinds (`transport|audit_doc|other`) match the spec's scoping; Task 6 names `test_mutation_spec_shape` as the shape verifier; duplicate AC label removed.
- v1.7: 5b audit v7 fixes (codex; agy v7 clean): AC-2.9h evidence is one `·`-joined line (the version-history helper refuses multiline text); docs-half grammar test uses `is_transport_path(Path(...))`; hand replay renumbered AC-2.9h; Version History reordered ascending; `# Verbs:` header located by prefix.
- v1.8: 5b audit v8 fixes (codex): e′ restored on the observable bad-project-root fall-through (23 mutations); PassSpec AC worded as a full constructor.
- v1.9: 5b audit v8 fix (agy p1): explicit try/except SystemExit around parse_args in the Task 3 code structure.
- v1.10: 5b audit v9 fixes (codex + agy p1, 22 tools): stale 22/v1.15 strings; no placeholder ellipses in paths, tokens or the JSON skeleton (one full mutation entry shown); render_verdict dropped, _run named; provenance line unpinned.
- v1.11: 5b audit v10 fixes (codex; agy v10 clean): AC-6.3 expects the harness's unreadable=0 field; marker AC allows unknown on the argparse path.
