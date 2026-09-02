# Design: audit-report-docs-copy

## Executive Summary
One collector (`h_mad_audit_cycle.collect()`) learns a `surface` token, an `overwrite` policy
and a readback; a thin CLI (`h_mad_collect_report.py`) and a delegating verb
(`hmad-dispatch collect-report`) expose it to the codex leg; the gate refuses the transport
grammar `^audit_[^.]+\.report\.md$`; SKILL.md gains the codex-leg recipe with a halt on any
non-`OK` `COLLECT:` token.

## Overview
The plan (v1.5, gated at audit cycles 7+8) fixes the recipe half of the lost-report incident:
the codex audit leg lands only in `/tmp` and its docs copy is a remembered `cp`. This design
puts the copy at the collect seam that already owns the fallback ladder and the docs-path
derivation, keeps `audit-cycle`'s behaviour byte-identical when no surface is given, and makes
the gate refuse a transport path so an uncollected report cannot score. Every verdict follows
the h-mad token contract (exit 0 on a verdict, 2 on an operational error, `[H-MAD]` marker on
every outcome) and every new connection is mutation-pinned in both directions.

## Architecture Overview
```
  codex leg (operator / recipe)                    agy leg (audit-cycle verb)
  ─────────────────────────────                    ─────────────────────────
  h_mad_assemble_audit.py --report-file $RP        _cmd_audit_cycle
  hmad-dispatch exec codex … --out --log                 │  _cmd_exec agy … (per pass)
        │  writes $RP + $RP.done                         ▼
        ▼                                          h_mad_audit_cycle.py main()
  hmad-dispatch collect-report ──► h_mad_collect_report.py      │
        (delegates, $here override)        │                     │
                                           ▼                     ▼
                              h_mad_audit_cycle.collect(spec, …, surface=…, overwrite=…)
                                           │
                     ┌─────────────────────┼──────────────────────┐
                     ▼                     ▼                      ▼
          _collected_path(…, surface)  _copy_collected_report   _write_collected_report
          .p<i>.md | .<surface>.md     (report-file rung)       (--out extract rung)
                                       overwrite? readback       overwrite? readback
                                           │
                                           ▼
                              docs/<dir>/<f>.<phase>.audit.v<N>.<tok>.md
                                           │
                                           ▼
                              h_mad_audit_gate.py  (refuses TRANSPORT_RE names)
```
Neither the CLI nor `_collected_path` imports `TRANSPORT_RE`; only the gate defines it and
only the tests import it (plan §Architecture, AC-1.6 is a property test).

## Detailed Design

### D1. `h_mad_audit_cycle.py` — collector changes (FR-1, FR-2 internal contract)

Observed today (2026-09-02): `_collected_path(*, project_root, feature, phase, cycle, index)`
returns `…/{feature}.{phase}.audit.v{cycle}.p{index}.md`; `collect()` returns
`(delivered, collected_path)` with `delivered ∈ {"report-file","out","none"}`;
`_copy_collected_report` and `_write_collected_report` both `unlink(missing_ok=True)` then
write (lines 92 and 169); `PassSpec.out_path` is a required positional.

Changes:

```python
SURFACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")   # the _VERSION_RE discriminator
PASS_INDEX_RE = re.compile(r"^p\d+$")

class CollectConflict(OperationalError):
    """Target exists with different bytes and overwrite is False. Carries .delivered."""
    def __init__(self, collected: Path, delivered: str): ...

def validate_surface(surface: str) -> str:
    # ValueError naming the token when it fails SURFACE_RE or matches PASS_INDEX_RE
    # (AC-1.3, AC-2.7). Returns the token unchanged.

def _collected_path(*, project_root, feature, phase, cycle, index, surface=None) -> Path:
    token = f"p{index}" if surface is None else validate_surface(surface)
    return project_root / audit_dirs[phase] / f"{feature}.{phase}.audit.v{cycle}.{token}.md"

def _readback_equal(path: Path, data: bytes) -> bool:
    return path.is_file() and path.read_bytes() == data

# Every filesystem call in the writers and in collect() runs under this guard: an
# OSError (PermissionError on an unwritable docs file, EACCES on unlink, a vanished
# report) becomes OperationalError so the CLI exits 2 with a marker instead of a
# traceback (exit 1) — the audit-gate signal discipline. `collect()` itself also
# wraps its read_bytes() comparisons the same way.
@contextlib.contextmanager
def _fs_errors(what: str):
    try:
        yield
    except OSError as exc:
        raise OperationalError(f"{what}: {exc}") from exc

def _copy_collected_report(report_path, collected_path, *, overwrite=True) -> Path:
  with _fs_errors(f"collect {collected_path}"):        # body indented under this guard
    data = report_path.read_bytes()
    if not data: raise OperationalError(f"report is empty: {report_path}")
    if report_path.resolve() == collected_path.resolve():          # AC-2.8: RP IS the docs path
        marker = Path(str(report_path) + ".done")
        marker.unlink(missing_ok=True)
        if marker.exists(): raise OperationalError(f"readback: marker still present: {marker}")
        return collected_path
    if collected_path.exists():
        if collected_path.read_bytes() == data: return collected_path   # AC-2.4: no write
        if not overwrite: raise CollectConflict(collected_path, "report-file")   # AC-2.5
    collected_path.parent.mkdir(parents=True, exist_ok=True)
    collected_path.unlink(missing_ok=True)
    collected_path.write_bytes(data)
    if not _readback_equal(collected_path, data):                    # AC-2.12
        raise OperationalError(f"readback mismatch after copy: {collected_path}")
    return collected_path

def _write_collected_report(report_text, collected_path, *, overwrite=True) -> Path:
    # identical shape over report_text.encode("utf-8"), delivered="out" (AC-2.6a/2.6b),
    # under the same _fs_errors guard

def collect(spec, *, grace, project_root, feature, phase, cycle,
            surface=None, overwrite=True) -> tuple[str, Path | None]:
    # The WHOLE body runs under the guard, so `_has_complete_report` (stat/size),
    # `_run_report_wait` (subprocess + stat) and every read below convert an OSError
    # into OperationalError; the CLI's outer try is the backstop, not the only line.
    with _fs_errors(f"collect {feature} {phase} v{cycle}"):
        return _collect_unguarded(spec, grace=grace, project_root=project_root,
                                  feature=feature, phase=phase, cycle=cycle,
                                  surface=surface, overwrite=overwrite)

def _collect_unguarded(spec, *, grace, project_root, feature, phase, cycle, surface, overwrite):
    collected_path = _collected_path(..., index=spec.index, surface=surface)
    # AC-2.8 FIRST: $RP IS the docs path. The marker is the completion signal and is
    # removed; a byte-identity short-circuit here would trivially match (same file)
    # and skip the marker path, so it is ordered after this block.
    # Existence-blind on purpose (Path.resolve() is strict=False): a docs-path --report
    # that does not exist yet must still take THIS branch and end MISSING, never fall
    # through to the --out rung and be written by it (AC-2.8 "no copy is attempted").
    same = spec.report_path.resolve() == collected_path.resolve()
    if same:
        if _has_complete_report(spec.report_path) or _run_report_wait(spec.report_path, grace):
            return "report-file", _copy_collected_report(spec.report_path, collected_path, overwrite=overwrite)
        return "none", None                       # no marker → MISSING (AC-2.8 "otherwise")
    # AC-2.11: already collected — a DISTINCT report file, marker or not, bytes identical
    # (under the enclosing guard like everything else in this function).
    data = spec.report_path.read_bytes() if spec.report_path.is_file() else b""
    already = (bool(data) and collected_path.is_file()            # empty is never "collected"
               and collected_path.read_bytes() == data)
    if already:
        return "report-file", collected_path
    if _has_complete_report(spec.report_path):
        return "report-file", _copy_collected_report(spec.report_path, collected_path, overwrite=overwrite)
    if _run_report_wait(spec.report_path, grace):
        return "report-file", _copy_collected_report(spec.report_path, collected_path, overwrite=overwrite)
    if spec.out_path is not None:                                    # optional out rung
        report_text = _run_extract_report(spec.out_path, feature=feature, phase=phase, cycle=cycle)
        if report_text:
            return "out", _write_collected_report(report_text, collected_path, overwrite=overwrite)
    return "none", None
```

`PassSpec` gains a default `out_path=None` is NOT possible without reordering positional
fields (it sits second); instead `main()`'s existing callers keep passing it and the CLI
constructs `PassSpec(index=1, report_path=RP, out_path=out_or_None, rc=0)` by keyword.
`collect()` guards `spec.out_path is not None`. All existing `audit-cycle` calls pass no
`surface` and no `overwrite`, so the verb's output is byte-identical (plan §Compatibility;
the existing `test_h_mad_audit_cycle.py` collect tests are the pin).

Edge cases:
- `report_path` present but empty with `.done` → `_has_complete_report` is False (size > 0
  required) → `report_wait` times out → MISSING (never copies an empty file; mutation (a)).
  An empty `report_path` beside an empty docs file is NOT "already collected" — the AC-2.11
  short-circuit requires non-empty bytes — so it also ends MISSING (pinned by a test).
- `collected_path` exists but unreadable, unwritable, or its parent cannot be created →
  `OSError` inside `_fs_errors` → `OperationalError` → CLI exit 2 with the
  `operational_error` marker (never a traceback). A test makes the docs file's PARENT
  directory unwritable (`chmod 0o555` on `docs/01-plan/features`, restored in `finally`)
  with a differing docs file and `--force`, and asserts exit 2 + marker: a read-only FILE
  would not do — `unlink()` succeeds on a read-only file when its directory is writable, and
  `write_bytes()` then creates a fresh file and exits 0. Skipped when running as root
  (root ignores mode bits).
- Same-file case with a missing marker → `_has_complete_report` False → `report_wait` waits
  `grace` then MISSING (AC-2.8 requires the marker); the same-file branch returns before the
  AC-2.11 short-circuit, so an existing marker is always removed on OK (a same-file with a
  marker never reaches the `--out` rung either — it returned already).

### D2. `h_mad_collect_report.py` — the CLI (FR-2)

```
usage: h_mad_collect_report.py --feature F --phase {plan,design,impl-plan} --cycle N
                               --surface S --report RP [--out OUT] --project-root ROOT
                               [--grace SECONDS=5] [--force]
```

Algorithm (`main(argv) -> int`). **Everything after argparse — steps 1 (semantic checks)
through 6 — runs inside ONE outer `try` whose handler is `except (OperationalError, OSError,
ValueError) as e:` (`ValueError` is what `validate_surface` and `int()` raise) → `ERROR: <e>` on stderr, `[H-MAD] <feature> collect <operational_error|readback_failed>`
on stdout, return 2.** So `Path.resolve()` in step 3, `mkdir` in step 1, `is_dir()` probes,
and any `OSError` the library did not already convert all take the same exit path; no
traceback can escape `main()`. Step 4's nested `CollectConflict` handler sits inside that
outer try.
1. Parse with `argparse`, every flag except `--out`, `--grace`, `--force` declared
   `required=True`. A missing required flag (or an unknown one, or `--phase` outside its
   `choices`) makes argparse print usage to stderr and raise `SystemExit(2)`; `main()`
   catches it, prints `[H-MAD] unknown collect usage_error`, and returns 2 — no `COLLECT:`
   line (AC-2.10 "missing required flag"). Then the semantic operational checks, each →
   `ERROR: …` on stderr, `[H-MAD] <feature> collect operational_error` on stdout, exit 2,
   **no** `COLLECT:` line (AC-2.10): `--project-root` not a directory; `--cycle` < 1;
   `--surface` fails `validate_surface` (AC-2.7; its `ValueError` propagates to the outer
   handler, which echoes the message and exits 2 with the `operational_error` marker); docs dir
   cannot be created (`mkdir` raises) or is not a directory.
2. Build `spec = PassSpec(index=1, report_path=Path(RP), out_path=Path(OUT) if OUT else None, rc=0)`.
3. `same = Path(RP).resolve() == _collected_path(...).resolve()` (for the AC-2.8 detail line).
4. Nested handlers, so a failure inside the forced retry is still caught:
   ```python
   forced = False
   try:                                   # the ONE outer try (opened before step 1)
       ... semantic checks, mkdir, spec, same = ... .resolve() ...
       try:
           delivered, path = collect(spec, grace=grace, ..., surface=S, overwrite=False)
       except CollectConflict as c:
           if not args.force:
               print(f"COLLECT: CONFLICT path={c.collected} delivered={c.delivered}")
               print(f"[H-MAD] {F} collect CONFLICT"); return 0
           delivered, path = collect(spec, ..., surface=S, overwrite=True)   # still inside the outer try
           forced = True
       ... steps 5–6 (token line, detail lines, marker) ...
   except (OperationalError, OSError, ValueError) as e:   # CollectConflict handled above
       print(f"ERROR: {e}", file=sys.stderr)
       reason = "readback_failed" if str(e).startswith("readback") else "operational_error"
       print(f"[H-MAD] {F} collect {reason}"); return 2                      # AC-2.12
   ```
   The library converts every `OSError` it raises to `OperationalError` (D1), so nothing
   escapes as a traceback.
5. `delivered == "none"` → `COLLECT: MISSING path=<derived> delivered=none`, marker, return 0
   (AC-2.2, 2.3).
6. Else `COLLECT: OK path=<path> delivered=<delivered>[ forced=1]`; if `same` and the marker
   is gone print `marker: removed <RP>.done`; marker `[H-MAD] <F> collect OK`; return 0.

The token line is the FIRST stdout line on a verdict; detail lines follow; the `[H-MAD]`
marker is last (same layout as `h_mad_audit_gate.py`). On an operational error there is no
token line and the marker is the only stdout line — `usage_error`, `operational_error` or
`readback_failed` — so every exit path carries exactly one `[H-MAD]` marker. The CLI imports `collect`, `PassSpec`,
`_collected_path`, `validate_surface`, `CollectConflict`, `OperationalError` from
`h_mad_audit_cycle` and nothing from the gate. Stdlib only.

### D3. `h_mad_audit_gate.py` — transport refusal (FR-3)

```python
TRANSPORT_RE = re.compile(r"^audit_[^.]+\.report\.md$")

def is_transport_path(path: Path) -> bool:
    return bool(TRANSPORT_RE.match(path.name))
```
In `main()`, immediately after the `--verify-stamp` branch and BEFORE `read_text` (a
transport path is refused by name whether or not it exists):
```python
    feature = args.audit_file.name.split(".")[0] or "unknown"     # moved up
    # For a transport name this yields the whole dot-free stem (`audit_f_plan_cycle3_codex`,
    # or a hand-staged `audit_hnag_c28_agy`) — deliberately: a transport stem has NO
    # reliable feature grammar (hand-staged names differ), so the marker's feature slot
    # carries the stem verbatim rather than a guessed feature. AC-3.1 asserts the marker
    # contains `transport file`, not a feature name.
    if is_transport_path(args.audit_file):
        print("GATE: INVALID must=0 should=0")
        print(f"[H-MAD] {feature} gate INVALID (transport file — collect it into docs first: "
              "h_mad_collect_report.py)")
        return 2
```
**Downstream contract (AC-3.3), pinned in `h_mad_audit_cycle.py`, not inferred from the
regex:** `h_mad_audit_cycle.gate(collected)` runs the gate CLI as a subprocess; on a transport
name the CLI prints `GATE: INVALID must=0 should=0` and exits 2; `gate()` accepts rc ∈ {0, 2},
`_gate_token` parses `("INVALID", 0, 0)`, and `gate()` returns `("INVALID", 0, 0, [])`
before the in-process read (existing early return). `combine()` then renders `UNVERIFIED`
with `reason=no_gate_sections:p<i>` — the existing word, no new one. A test in
`test_h_mad_audit_cycle.py` calls `gate(Path("…/audit_f_plan_cycle3_codex.report.md"))` on a
well-formed report and asserts exactly that tuple, and a `combine()` test asserts the reason,
so the consumer path cannot drift while the CLI tests stay green.
`h_mad_do_preconditions.py` never passes a transport name (AC-3.4). `--verify-stamp` on a transport path is unaffected (it reads a stamp
sidecar, never scores).

### D4. `hmad-dispatch.sh` — `collect-report` verb (FR-4)

```bash
_cmd_collect_report() {  # <args passed verbatim to h_mad_collect_report.py>
  local here
  here="${HMAD_AUDIT_CYCLE_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)}"
  python3 "$here/h_mad_collect_report.py" "$@"
}
```
plus `collect-report) _cmd_collect_report "$@" ;;` in `main()`'s case (beside `report-wait`)
and the name in the line-3 verb list. `HMAD_AUDIT_CYCLE_SCRIPT_DIR` is reused deliberately —
it is the stub seam the audit-cycle tests already use, so the wiring test needs no new knob.
An unknown verb keeps hitting the existing `*)` arm (`unknown verb`, return 2) — AC-4.3.

### D5. Docs (FR-5)

SKILL.md gains a NEW top-level section `## Second surface — the codex leg`, placed
immediately after `## Putting \`hmad-dispatch\` on PATH` (SKILL.md:1791) and before
`## Helper scripts …` — i.e. OUTSIDE the `## Audit prompt assembly` → `## Putting …` slice
that `test_h_mad_audit_cycle_docs.py` pins, as the spec (FR-5) and plan require. Inside the
slice, the `audit-cycle` paragraph gains ONE pointer sentence: "`audit-cycle` dispatches agy
only; the codex pass is dispatched and collected by hand — see §"Second surface — the codex
leg"." The new section's body:

```markdown
**Second surface — the codex leg, collected by the same copier.** `audit-cycle` dispatches agy;
the codex pass is dispatched by hand and MUST be collected before it is gated:
```bash
RP=/tmp/audit_<feature>_<phase>_cycle<N>_codex.report.md; rm -f "$RP" "$RP.done"
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py --feature <feature> --phase <phase> \
  --cycle <N> --project-root <PROJECT_ROOT> --report-file "$RP" --out /tmp/audit_<feature>_<phase>_cycle<N>_codex.txt
hmad-dispatch exec codex /tmp/audit_<feature>_<phase>_cycle<N>_codex.txt --cd <PROJECT_ROOT> \
  --out /tmp/audit_<feature>_<phase>_cycle<N>_codex.out.txt --log /tmp/audit_<feature>_<phase>_cycle<N>_codex.log --timeout 1800
hmad-dispatch collect-report --feature <feature> --phase <phase> --cycle <N> --surface codex \
  --report "$RP" --out /tmp/audit_<feature>_<phase>_cycle<N>_codex.out.txt --project-root <PROJECT_ROOT>
# Read the COLLECT: token. Anything but OK → halt <phase>:report_not_collected, emit
# [H-MAD] <feature> <phase> halted reason=report_not_collected, and do NOT run the gate.
python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py <the path= the COLLECT: OK line printed>
```
Never gate `$RP`: the gate refuses a transport name (`audit_*.report.md`) with `GATE: INVALID`.
```
Step 9 gains one sentence after the `report-wait` redirect: "The gate refuses a path named
like a transport file (`audit_*.report.md`) — gate the docs path, never `$RP`." The helper
registry gains the `h_mad_collect_report.py` entry (token set, exit contract, `--force`,
readback). `references/orchestration-mode.md` verb table gains a `collect-report` row beside
`report-wait`. `test_h_mad_audit_cycle_docs.py`'s anchors (`## Audit prompt assembly`,
`## Putting …`, `6.6.`→`\n7.`, the helper-registry heading) are untouched.

## Components Changed / Added
| Component | File path | Change type | Purpose |
|---|---|---|---|
| collector | `h-mad/scripts/h_mad_audit_cycle.py` | modify | `surface`, `overwrite`, readback, `CollectConflict`, `validate_surface`, optional out rung, already-collected short-circuit |
| CLI | `h-mad/scripts/h_mad_collect_report.py` | new | `COLLECT:` contract over `collect()` |
| gate | `h-mad/scripts/h_mad_audit_gate.py` | modify | `TRANSPORT_RE`, `is_transport_path`, refusal |
| verb | `h-mad/scripts/hmad-dispatch.sh` | modify | `_cmd_collect_report` + case + header |
| recipe | `h-mad/SKILL.md` | modify | new `## Second surface — the codex leg` section (after `## Putting …`), one pointer sentence in the audit-cycle paragraph, step-9 sentence, registry entry |
| verb table | `h-mad/references/orchestration-mode.md` | modify | `collect-report` row |
| tests | `h-mad/tests/test_h_mad_collect_report.py` | new | AC-1.1–1.6, AC-2.1–2.12 |
| tests | `h-mad/tests/test_h_mad_audit_gate.py` | modify | AC-3.1, 3.2, 3.5–3.7 incl. corpus + sweep |
| tests | `h-mad/tests/test_h_mad_audit_cycle.py` | modify | AC-3.3 (`gate()`/`combine()` on a transport name), AC-2.8 branch order, compatibility pins |
| tests | `h-mad/tests/test_hmad_dispatch_collect_report.py` | new | AC-4.1, AC-4.3 |
| tests | `h-mad/tests/test_h_mad_collect_report_docs.py` | new | AC-4.2, AC-5.1–5.4 |
| mutation spec | `h-mad/tests/mutation-specs/collect_report.json` | new | 19 mutations (17 connection/branch + 2 marker-stripping for separable output parts) |

## Implementation Order
1. Task 1 — collector (`h_mad_audit_cycle.py`): `validate_surface`, `_collected_path(surface)`,
   `CollectConflict`, `overwrite` + readback on both writers, same-file marker handling,
   already-collected short-circuit, optional out rung. RED: AC-1.1–1.5 + unit tests for the
   writers. Existing collect tests stay green (compatibility pin).
2. Task 2 — gate: `TRANSPORT_RE`, `is_transport_path`, refusal. RED: AC-3.1–3.7 incl. the
   two-direction corpus (AC-3.5a) and the AC-1.6 property test (it needs both `_collected_path`
   from task 1 and `TRANSPORT_RE` from this task).
3. Task 3 — CLI. RED: AC-2.1–2.12, incident replay AC-2.9 (suite half).
   **Checkpoint — AC-2.9 hand replay** against `/tmp/audit_nlmpin_plan_cycle8_codex.report.md`
   copied into a scratch project root; transcript into the plan's Version History.
4. Task 4 — verb (wiring shape). WIRE: `hmad-dispatch collect-report` → `$here/h_mad_collect_report.py`.
   WIRE-PIN: the verb test that runs against a stub script dir and fails when severed. RED:
   AC-4.1, AC-4.3.
5. Task 5 — docs. RED: AC-4.2, AC-5.1–5.4 (docs tests), `test_h_mad_audit_cycle_docs.py`
   still green.
6. Task 6 — mutation spec (19 mutations, every one naming a test from tasks 1–5; the two
   marker-stripping mutants (j) gate refusal without its `[H-MAD]` line, (j′) CLI
   operational error without its marker, pin the separable output parts) →
   `MUTATION: ALL_CAUGHT`; `--check-anchors` clean; full suite green.

## Data Model / Schema Changes
None. No state-schema key is added; the docs filename grammar is unchanged (`.<surface>` was
already in the documented grammar).

## API / Interface Changes
- `h_mad_audit_cycle._collected_path(*, project_root, feature, phase, cycle, index, surface: str | None = None)`
- `h_mad_audit_cycle.collect(spec, *, grace, project_root, feature, phase, cycle, surface: str | None = None, overwrite: bool = True)`
- `h_mad_audit_cycle._copy_collected_report(report_path, collected_path, *, overwrite: bool = True)`;
  `_write_collected_report(report_text, collected_path, *, overwrite: bool = True)`
- new `h_mad_audit_cycle.validate_surface(str) -> str`, `CollectConflict(OperationalError)` with
  `.collected: Path`, `.delivered: str`
- `PassSpec.out_path` may be `None` (constructed by keyword; positional order unchanged)
- new CLI `h_mad_collect_report.py` (flags in D2; `--grace` default 5; `--force` off)
- `h_mad_audit_gate.TRANSPORT_RE`, `h_mad_audit_gate.is_transport_path(Path) -> bool`; gate CLI
  refuses transport names with `GATE: INVALID must=0 should=0`, exit 2
- `hmad-dispatch collect-report <args…>`

## Error Handling Strategy
Verdicts are stdout tokens with exit 0 (`COLLECT: OK|MISSING|CONFLICT`; `GATE: PASS|FAIL`).
Operational errors are exit 2 with `ERROR:` (or argparse usage) on stderr, a
`[H-MAD] <feature|unknown> collect usage_error|operational_error|readback_failed` marker on
stdout and NO token line (missing flag, bad surface, bad root, unwritable docs dir, readback
mismatch, unreadable files); `GATE: INVALID` keeps its
existing exit 2 and exact line shape. Inside the library, `CollectConflict` is an
`OperationalError` subclass so `audit-cycle`'s existing `except OperationalError` still maps
anything unexpected to exit 4 — but `audit-cycle` passes `overwrite=True` and can never raise
it. Every CLI exit path — verdict or operational error — carries exactly one `[H-MAD] … collect
<OK|MISSING|CONFLICT|usage_error|operational_error|readback_failed>` marker (Marker
discipline). The recipe halts on any non-`OK` token before the gate.

## Test Strategy
- Unit (in-process, `tmp_path` project roots): `_collected_path`, `validate_surface`, both
  writers (identical / differing / overwrite / readback via monkeypatched `write_bytes`),
  same-file marker path, `collect()` rungs with a fake `report_wait` (grace 0) and a stub
  `--out` carrying a sentinel pair.
- CLI (subprocess, `sys.executable`): every `COLLECT:` case, exit codes, stderr, marker lines,
  `--force`, operational errors including each missing required flag and an unknown `--phase`
  (exit 2, usage on stderr, `usage_error` marker, no token), a `PermissionError` from an
  unwritable docs DIRECTORY (`0o555`) under `--force` (exit 2, `operational_error` marker,
  no traceback; skipped as root), a readback
  mismatch inside the forced retry (exit 2, `readback_failed`), incident replay (AC-2.9 suite half: gate on RP → INVALID;
  collect → OK identical; gate on docs → scores).
- Gate: transport names refused (all observed shapes), docs names scored, Phase-7 name
  scored, two-direction corpus vs `_VERSION_RE`, repo sweep (`docs/**/*.audit.v*.md` → none
  transport), AC-1.6 property over adversarial `(feature, surface)` pairs.
- Wrapper: the verb under a stub `HMAD_AUDIT_CYCLE_SCRIPT_DIR` whose `h_mad_collect_report.py`
  records argv and exits with a chosen code; severed route → test fails; unknown verb →
  `unknown verb`, stub not invoked. The wrapper's staged `--report-file` under the existing
  audit-cycle stub harness is asserted to match `TRANSPORT_RE`, AND the SKILL.md 6.6 literal
  (`RP=/tmp/audit_<feature>_<phase>_cycle<N>.report.md`, read from the file by regex) is
  instantiated with sample tokens (`f`, `plan`, `3`, and the `_codex` suffix form from the D5
  block) and asserted to match `TRANSPORT_RE` too (AC-3.5a, both halves).
- Docs: SKILL.md block order (`exec codex` < `collect-report` < `report_not_collected` <
  `h_mad_audit_gate.py`), gate line has no `$RP`, registry entry names the token set and exit
  contract, orchestration-mode verb row, step-9 sentence.
- Mutation: 19 mutations, each with `test`, `root: ../..`, `python3.11 -m pytest` — the
  spec's 17 plus (j)/(j′) marker-stripping mutants so the marker assertions are load-bearing.

## Test Plan
| Test file | Scenarios | Command |
|---|---|---|
| `tests/test_h_mad_collect_report.py` | AC-1.1–1.6, AC-2.1–2.12 | `python3.11 -m pytest h-mad/tests/test_h_mad_collect_report.py -q` |
| `tests/test_h_mad_audit_gate.py` (+) | AC-3.1, 3.2, 3.5, 3.5a, 3.6, 3.7 | `python3.11 -m pytest h-mad/tests/test_h_mad_audit_gate.py -q` |
| `tests/test_h_mad_audit_cycle.py` (+) | AC-3.3: `gate()` on a transport name → `("INVALID",0,0,[])`; `combine()` → `UNVERIFIED reason=no_gate_sections:p1`; AC-2.8 ordering (same-file with marker → OK + marker removed; without marker → none) | `python3.11 -m pytest h-mad/tests/test_h_mad_audit_cycle.py -q` |
| `tests/test_hmad_dispatch_collect_report.py` | AC-4.1, AC-4.3, staged-name grammar | `python3.11 -m pytest h-mad/tests/test_hmad_dispatch_collect_report.py -q` |
| `tests/test_h_mad_collect_report_docs.py` | AC-4.2, AC-5.1–5.4 | `python3.11 -m pytest h-mad/tests/test_h_mad_collect_report_docs.py -q` |
| existing `test_h_mad_audit_cycle*.py`, `test_hmad_dispatch_audit_cycle.py` | compatibility, spec-registry tests | `python3.11 -m pytest h-mad/tests -q` |
| `tests/mutation-specs/collect_report.json` | 19 mutations | `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/collect_report.json` → `MUTATION: ALL_CAUGHT` |

## Invariant Compliance
- **Audit-gate signal discipline** — complies: `COLLECT:` verdicts exit 0; exit 2 reserved for
  operational errors; `GATE: INVALID` keeps its existing exit 2 and exact token shape.
- **Single-source contract** — complies: one docs-path derivation (`_collected_path`), one
  transport grammar (`TRANSPORT_RE` in the gate; tests import it), one copier used by both legs.
- **Standalone / no plugin dependency; No new external dependency** — complies: stdlib only;
  the verb delegates to a script inside the skill.
- **Portable time bounds** — complies: no `timeout`; `--grace` reuses `report_wait`'s poll.
- **Doc-template superset compliance** — complies: design follows the template; SKILL.md edit
  is additive inside an existing section.
- **Operator-override preservation** — complies: `--ack-file`, `[audit-override]` untouched.
- **Backward compatibility** — complies: `audit-cycle` output byte-identical; every existing
  audit doc keeps its verdict (AC-3.7 sweep); only transport-named paths change verdict, which
  no recipe/test gated (grep 0).
- **Marker discipline** — complies: `[H-MAD]` on every `COLLECT:` outcome, on readback
  failure, on the gate refusal, and the recipe's halt line.
- **Mutation verification** — complies: both writers read back; the marker removal re-checks;
  19 mutations each with a named test, including one per separable output part (exit code,
  token, marker) of the gate refusal and the CLI error path.
- **Test discrimination** — complies: each mutation names the one test that must bite.
- **Guard narrowing** — complies: the transport regex was widened from a stem to prefix+suffix
  and then narrowed by the dot rule, each step with executed evidence in the plan.
- **Connection enforcement** — complies: CLI→`collect()` (e/e′), verb→script (f/f′),
  gate refusal (g/g′), grammar disjointness (i/i′) all dropped AND forced.
- **Incident replay** — complies: AC-2.9 replays absent-docs → collected → gateable, in the
  suite and once by hand on a real survivor.
- **Assumption verification** — complies: every load-bearing shape was executed (plan table);
  D1's "observed today" lines cite line numbers read this session.
- **Counts a dispatch reports / Wrapper–runtime reconciliation / Regression provenance /
  Both halves of a doc change / Reimplementation parity** — complies or N/A: no dispatch
  count is trusted; the verb is a pure delegation; SKILL.md prose and the registry are edited
  together; `collect()` is reused, not reimplemented.
- **Project: Skill self-containment / manifest integrity** — complies: all files inside
  `h-mad/`; frontmatter untouched; entry behaviour change (new verb) is documented in SKILL.md.

## Assumption verification (evidence, 2026-09-02)
| Assumption | Evidence |
|---|---|
| `collect()` return shape and both writers unlink-then-write | read `h_mad_audit_cycle.py` this session: `collect()` returns `(str, Path\|None)`; `unlink` at lines 92 and 169 |
| gate `main()` order | read `h_mad_audit_gate.py:231-326`: argparse → `--verify-stamp` branch → `read_text` → `has_gate_sections` → `classify` |
| wrapper delegation shape | `_cmd_report_wait` (`hmad-dispatch.sh:1399-1424`): `here=…; python3 "$here/h_mad_report_wait.py" "$@"`; `HMAD_AUDIT_CYCLE_SCRIPT_DIR` override at `:2695` |
| unknown verb path | `hmad-dispatch.sh:3531`: `*) echo "hmad-dispatch: unknown verb '$verb'" >&2; return 2` |
| mutation spec shape | `tests/mutation-specs/ab_dispatch.json`: `root: ../..`, `command: python3.11 -m pytest …`, per-mutation `file/find/replace/test` |
| test interpreter | `run_with_cmd_exec_stub` uses `/opt/anaconda3/bin/python3.11`; spec commands use `python3.11` |
| grammar disjointness | executed `^audit_[^.]+\.report\.md$` vs `_VERSION_RE` over 10 names incl. `audit_f.plan.audit.v8.report.md` (T=False, V=True) — plan v1.3 table |

## Version History
- v1.0: Initial design draft.
- v1.11: Design-audit v8 fixes (agy p1): the transport-refusal marker's feature slot is the stem verbatim (a transport name has no reliable feature grammar) — stated, not left to inference; marker-stripping mutants (j)/(j′) added → 19, swept into spec/plan counts.
- v1.10: Design-audit v8 fix (codex): the already-collected short-circuit requires non-empty bytes, so an empty-identical docs/RP pair is MISSING, not OK.
- v1.9: Design-audit v7 fix (agy p1): the same-file test is existence-blind so a missing docs-path `--report` ends MISSING instead of reaching the `--out` rung.
- v1.8: Design-audit v7 fix (codex; agy v6 clean): the outer handler also catches `ValueError` so a bad `--surface` cannot leak as a traceback.
- v1.7: Design-audit v5 fixes (codex): `collect()` runs its WHOLE body under `_fs_errors` (the probes `_has_complete_report`/`_run_report_wait` included); the SKILL.md block is a new top-level section after `## Putting …`, outside the pinned slice, per spec/plan — one pointer sentence inside.
- v1.6: Design-audit v5 fix (agy p1): one outer `try … except (OperationalError, OSError)` encloses every step after argparse, so `resolve()`, `mkdir` and the directory probes cannot leak a traceback either.
- v1.5: Design-audit v4 fix (agy p1, 10 tool calls; codex v4 clean): the PermissionError test chmods the parent DIRECTORY, not the file — `unlink` on a read-only file succeeds under a writable parent and the scenario would have exited 0.
- v1.4: Design-audit v3 fix (agy p1; codex v3 clean): the `collect()` same-file and already-collected checks run under `_fs_errors` too — the code block now matches the prose.
- v1.3: Design-audit v2 fixes (agy p1): the `--force` retry runs inside the OUTER try so an `OperationalError` from the retry is still caught; every filesystem call in the writers/`collect()` runs under `_fs_errors` (OSError → OperationalError, exit 2 + marker, never a traceback); AC-3.5a's SKILL.md 6.6 literal assertion restored in Test Strategy.
- v1.2: Design-audit v2 fixes (codex): missing-required-flag path designed explicitly (argparse `required=True`, `SystemExit` caught → `usage_error` marker, exit 2, no token); marker contract made exact — one `[H-MAD]` marker on every exit path including operational errors.
- v1.1: Design-audit v1 fixes (codex + agy p1, same finding on the short-circuit): the AC-2.8 same-file branch is ordered BEFORE the AC-2.11 byte-identity short-circuit (which would trivially match the same file and skip the marker path); AC-3.3's `gate()` tuple and `combine()` reason are pinned by tests in `test_h_mad_audit_cycle.py`, not inferred from `_gate_token`'s regex.
