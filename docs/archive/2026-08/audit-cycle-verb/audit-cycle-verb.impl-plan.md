# Implementation Plan: audit-cycle-verb

> Source: docs/02-design/features/audit-cycle-verb.design.md (post-audit, v1.14)
> Paired plan: docs/01-plan/features/audit-cycle-verb.plan.md (post-audit, v1.11)
> Branch target: feature/audit-cycle-verb

## Executive Summary

Nine tasks build `hmad-dispatch audit-cycle` bottom-up: Tasks 1–4 ship the stdlib-only helper
`h_mad_audit_cycle.py` (verdict core first, then one task per subprocess connection), Tasks 5–7 ship
the shell verb (assembly, dispatch/reap, helper invocation — again one task per connection), and
Tasks 8–9 ship the mutation specs and the SKILL.md/doc-token pin. Six of the nine tasks are `wiring`
shaped because this feature's deliverable is almost entirely connections; each carries a WIRE-PIN
that fails when that call site alone is removed with its callee left intact.

## Task decomposition rationale

The design's §"Implementation Order" lists seven steps. This plan splits its steps 1–2 into four
tasks and its steps 3–4 into three, for one reason: the plan's §"Architecture Considerations"
requires **six** connection mutations, each of which must be pinned by a test that fails when that
connection alone is cut. A task that ships two call sites cannot satisfy that — one WIRE-PIN cannot
discriminate two wires, and the second wire would be verified by nothing. So every call site gets
its own task, its own WIRE, and its own WIRE-PIN.

Each task ships complete behaviour for what it declares. No task leaves a stub, a `NotImplementedError`,
or a branch that raises "not yet wired": a function is introduced in the task that can implement it
fully. That is why `gate()` does not appear until Task 4 rather than being introduced in Task 1 in a
degraded in-process form — an in-process-only `gate()` would make Task 4's WIRE-PIN pass *before*
Task 4's wire existed, which is precisely the connection-enforcement failure this decomposition is
built to prevent.

The design's implementation-order step 7 (live cycle against real `agy`) is not a task here: it
produces no file and is a Phase-5f/6 verification obligation. It is recorded under
§"Post-implementation verification" below.

---

## Architecture constraints carried from the plan

The paired plan's §"Architecture Considerations" records three assumptions that were **executed**
rather than reasoned about, and all three constrain code in this plan. They are restated here with
their observed output so an implementer working from this document alone does not have to open the
plan to know why these shapes are non-negotiable. (The plan's section is present and complete — this
is a carry-forward for the implementer's benefit, not a substitute for it.)

**1. `exec` on a shared `--out` is FIRST-writer-wins, not last** (measured 2026-08-20; two
concurrent dispatches staggered 2s apart onto one `--out`):

```
=== rc: a=0 b=0 ===
=== shared --out content ===
ALPHA
=== b.stdout ===
hmad-dispatch: exec: REFUSING to overwrite --out /tmp/probe_out/shared.out — its content
changed while this dispatch ran (another dispatch wrote there; J29).
BETA
```

Both exit 0. So a shared path leaves pass 2's `--out` holding pass **1's report** — well-formed and
plausible, which a collector cannot distinguish from a correct delivery. This is why Task 6's
per-pass `--out`/`--log`/report paths are a correctness constraint and not tidiness.

**2. Concatenating two reports UNDER-counts** (measured 2026-08-20):

```
=== gate prose.md alone ===       GATE: FAIL must=1 should=0
=== gate bullets.md alone ===     GATE: FAIL must=1 should=0
=== gate CONCATENATION ===        GATE: FAIL must=1 should=0
```

Two findings totalling 2 gate to `must=1`: `_count_section_findings` applies its prose fall-back only
when a section has **no** bullets, so the prose finding is silently dropped. This is why Task 4 gates
each pass on its own file, and why AC-10.3 pins the behaviour against the real gate.

**2b. The `--out` fallback is not defensive — it fired during this plan's own audit.** On impl-plan
cycle 7, pass 1's `exec agy` returned rc=0 having written **no report file and no `.done` marker**
(`ls`: both absent), while its `--out` held the complete 1.6 KB sentinelled report. Recovering it
needed exactly rung 3: `h_mad_extract_report.py <out> --feature --phase --cycle` → rc 0, and the
recovered report gated `GATE: FAIL must=2 should=0`. Pass 2 of the same cycle delivered normally via
the report file. So a single cycle produced `delivered=out,report-file` — the mixed case — on real
agents. This is the measurement behind AC-9.2's "always arm the `--out` fallback", observed rather
than anticipated, and it is why `delivered=` is reported per pass rather than once per cycle.

**3. `GATE: INVALID` carries `must=0 should=0` it never measured.** The counts are an artifact of the
verdict, not a measurement, which is why Task 4 discards them at the boundary rather than carrying
them and ignoring them downstream.

---

## Task 1: audit-cycle helper — verdict core

**Production file**: `h-mad/scripts/h_mad_audit_cycle.py`
**Test file**: `h-mad/tests/test_h_mad_audit_cycle.py`
**Task shape**: `new-behaviour`

**Description**: The helper's pure logic and its no-pass path — everything that forms or formats a
verdict without running another script. Ships `_script()` (the `HMAD_AUDIT_CYCLE_SCRIPT_DIR`-aware
resolver every later task depends on), the two namedtuples, `combine()`, `premise_items()`,
`render()`, and `main()`'s argument parsing plus the complete no-pass mode. The no-pass mode is a
shippable behaviour on its own: it is how the shell reports `assemble_halt` and `prompt_divergence`,
so this task closes AC-2.2, AC-6.4b and AC-8.3 end-to-end before any subprocess exists.

`combine()` raises `OperationalError` for a pass that delivered on some channel and still produced no
`GATE:` token, **before** any verdict forms — the ordering is load-bearing and is asserted directly,
not inferred from an exit code. `render()` is the single verdict formatter reached by both the
no-pass and the full path (base invariant: single-source contract).

**Code structure**:
```python
# Key signatures — not implementations, just contracts
PassSpec   = namedtuple("PassSpec",   "index report_path out_path rc")
PassResult = namedtuple("PassResult", "index delivered collected_path verdict must should findings")

class OperationalError(Exception): ...

def _script(name: str) -> Path:
    """Sibling script path; HMAD_AUDIT_CYCLE_SCRIPT_DIR overrides for tests only."""

def _collected_path(*, project_root: Path, feature: str, phase: str,
                    cycle: int, index: int) -> Path:
    """<audit-dir>/<feature>.<phase>.audit.v<N>.p<i>.md; phase selects the audit dir."""

def combine(results: list[PassResult]) -> tuple[str, str | None]:
    """(verdict, reason). Raises OperationalError before any verdict forms."""

def premise_items(results: list[PassResult]) -> list[str]:
    """Format only — consumes PassResult.findings, parses nothing."""

def render(results, verdict, reason, *, feature, size_status, passes) -> str:
    """The one AUDITCYCLE: formatter, reached by both paths."""

def main(argv) -> int: ...
```

**Acceptance Criteria**:
- [ ] AC-1.4: `--phase` outside `{plan, design, impl-plan}` exits 2 with no `AUDITCYCLE:` line.
- [ ] AC-3.1: `--passes 0` and `--passes -1` exit 2 with no `AUDITCYCLE:` line.
- [ ] AC-5.2: `combine()` returns `UNVERIFIED` when any pass has `delivered == "none"` or
      `verdict == "INVALID"`, in preference to `FAIL` from any other pass
      (`test_combine_unverified_outranks_fail`).
- [ ] AC-6.1: `render()` emits **no** `must=`/`should=`/`p<i>=` fields on `UNVERIFIED` — asserted as
      an absence, by matching the line against a pattern that rejects those field names.
- [ ] AC-6.3: `combine()` returns `no_report:p<i>` for a `delivered=none` pass and
      `no_gate_sections:p<i>` for an `INVALID` pass, and the two are distinct.
- [ ] AC-6.4 / AC-6.4b: a post-dispatch `UNVERIFIED` prints `delivered=` for every pass; the no-pass
      form prints no `delivered=` field at all.
- [ ] AC-2.5 / AC-5.5: a `PassResult` with `delivered != "none"` and `verdict is None` raises
      `OperationalError` from `combine()`; a `delivered == "none"` pass with `verdict is None` does
      **not** (this is the qualifier the design records as load-bearing).
- [ ] AC-7.3: a must-fix finding carrying no `path:line` is rendered `(no citation)`.
- [ ] AC-7.5 / AC-8.4: on PASS the checklist is one line stating it is empty
      (`test_render_pass_has_no_premise_items`), and exactly one `AUDITCYCLE:`-prefixed line is
      printed on every path.
- [ ] AC-8.2 / AC-8.3: every verdict exits 0, and `[H-MAD] <feature> audit-cycle <verdict>` is
      emitted on every path including the no-pass form.
- [ ] AC-2.2: `--halt-reason assemble_halt:p2` with no `--pass` renders
      `AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2 passes=2 size_status=verified` and exits 0.
- [ ] **`--pass` is NOT declared in Task 1's argparse.** Task 4 adds the flag together with the
      collect-and-gate path that gives it meaning. Until then, supplying `--pass` must fail with
      argparse's own "unrecognized arguments", exit 2, and print **no** `AUDITCYCLE:` line
      (`test_main_rejects_pass_flag_until_task4`).
- [ ] **`main()` requires exactly one mode.** With neither `--pass` nor `--halt-reason` it exits 2
      with `ERROR:` on stderr and prints **no** `AUDITCYCLE:` line
      (`test_main_without_mode_is_operational_error`). There is no fall-through to
      `combine([])`/`render([], …)`.

      Both tests assert the **absence** of an `AUDITCYCLE:`-prefixed line, not merely a non-PASS
      verdict, because the defect they pin is a *fabricated* verdict. Measured 2026-08-20: the
      first Task 1 implementation declared `--pass`, never read it, and fell through to
      `combine([])` — so two nonexistent report paths, one carrying `rc=1`, produced
      `AUDITCYCLE: PASS passes=2 size_status=verified must=0 should=0` at exit 0. All 19 tests
      were green over it, because none drove `main()` with `--pass`. A helper whose entire purpose
      is refusing to report an unmeasured verdict shipped one.
- [ ] `test_script_resolution_default`: with `HMAD_AUDIT_CYCLE_SCRIPT_DIR` unset, `_script()` returns
      the real sibling paths, so the test override cannot silently become the production path.
- [ ] Every test sandboxes `--project-root` to `tmp_path`; no test writes under the repository's
      `docs/` tree.

**Dependencies on other tasks**: None

---

## Task 2: helper → `h_mad_report_wait.py` (collection rungs 1–2)

**Production file**: `h-mad/scripts/h_mad_audit_cycle.py`
**Test file**: `h-mad/tests/test_h_mad_audit_cycle.py`
**Task shape**: `wiring`
**WIRE** (`wiring` shape only): `h-mad/scripts/h_mad_audit_cycle.py:collect` → `h_mad_report_wait.py`
**WIRE-PIN** (`wiring` shape only): `test_collect_delayed_report`

**Description**: Introduces `collect()` with the first, second and fourth rungs of the four-outcome
ladder: report present **and** `.done` present → copy, no wait at all; otherwise
`h_mad_report_wait.py <report_path> --timeout <grace>` (the path is positional); otherwise (for now)
`delivered=none`. Rung 3 arrives in
Task 3. The `.done` requirement is the torn-write guard the design calls load-bearing: a non-empty
report without its marker routes to the wait rather than being scored.

`report_wait`'s **exit 1** is the legitimate "nothing here" code and falls through; any other
non-zero is an operational error at exit 4.

Every delivering branch copies to `_collected_path(...)` and then re-reads it, asserting
`exists() and st_size > 0` before the pass is recorded as delivered — a write that raised no
exception is not evidence the bytes landed.

**Why the WIRE-PIN is the delayed fixture and not the happy path**: under reap-first, the wait is
*bypassed* whenever the report is already present, which is how a successful delivery is normally
mocked. On that fixture, deleting the `report_wait` call changes nothing and the mutation survives
while reporting the connection as enforced. `test_collect_delayed_report` creates the report ~1s
into the grace window, which is the only shape that puts the call site on the executed path.

**Code structure**:
```python
def collect(spec: PassSpec, *, grace: float, project_root: Path, feature: str,
            phase: str, cycle: int) -> tuple[str, Path | None]:
    """('report-file'|'none', collected_path|None) at this task; 'out' added in Task 3."""

def _run_report_wait(report_path: Path, grace: float) -> bool:
    """True iff a non-empty body arrived. rc 1 => False; any other non-zero => OperationalError."""
```

**Acceptance Criteria**:
- [ ] AC-4.1: the report path is tested directly first; when it is non-empty **and** `.done` exists,
      `report_wait` is not invoked at all — the stub records **zero** invocations
      (`test_collect_report_file_present`).
- [ ] AC-10.2c: the same test asserts the zero-invocation converse explicitly, so the
      force-direction mutation ("remove the file-present check so it always waits") has a failing
      test.
- [ ] AC-10.2b: `test_collect_delayed_report` — report created ~1s into the grace window — yields
      `delivered=report-file` with the wait stub invoked exactly once.
- [ ] A non-empty report **without** `.done` does not short-circuit: it routes to `report_wait`.
- [ ] `report_wait` exiting 1 yields `delivered=none` at this task; any other non-zero raises
      `OperationalError` (exit 4, no `AUDITCYCLE:` line).
- [ ] AC-4.4: the collected report is written to
      `<audit-dir>/<feature>.<phase>.audit.v<N>.p<i>.md` and re-read non-empty before the pass is
      recorded as delivered; the `/tmp` path is never returned as the collected path.
- [ ] Interception is via `HMAD_AUDIT_CYCLE_SCRIPT_DIR`, never `PATH` — a `PATH` stub would never be
      consulted because `_script()` returns absolute paths.

**Dependencies on other tasks**: Task 1 (must complete first)

---

## Task 3: helper → `h_mad_extract_report.py` (collection rung 3)

**Production file**: `h-mad/scripts/h_mad_audit_cycle.py`
**Test file**: `h-mad/tests/test_h_mad_audit_cycle.py`
**Task shape**: `wiring`
**WIRE** (`wiring` shape only): `h-mad/scripts/h_mad_audit_cycle.py:collect` → `h_mad_extract_report.py`
**WIRE-PIN** (`wiring` shape only): `test_collect_falls_back_to_out`

**Description**: Adds the third rung — when both report rungs come up empty, run
`h_mad_extract_report.py <out_path> --feature --phase --cycle --after-marker` and, on non-empty
stdout, write it to the collected path (`delivered=out`). `--after-marker` is mandatory: the codex/agy
transcript echoes the prompt, and the assembled audit prompt contains a complete sentinel pair, so an
unmarked extraction can re-read the prompt's own echoed report.

`extract_report`'s **exit 2** is the legitimate "nothing here" code and covers a missing file, an
empty file, and a present file with no sentinel pair identically; any other non-zero is an
operational error at exit 4. The missing-file case was measured 2026-08-20 to exit 2 (not 1), which
is what makes an ordinary dispatch failure route to `delivered=none` rather than crashing the cycle.

**Code structure**:
```python
def _run_extract_report(out_path: Path, *, feature: str, phase: str,
                        cycle: int) -> str:
    """Report text, or '' when nothing is there. rc 2 => ''; any other non-zero => OperationalError."""
```

**Acceptance Criteria**:
- [ ] AC-4.2 / AC-10.2: `test_collect_falls_back_to_out` — report slot empty, `--out` holds a
      sentinelled report — yields `delivered=out` with the collected file written and re-read
      non-empty.
- [ ] AC-4.3: the extraction invocation carries `--after-marker`, asserted against the recorded stub
      argv rather than against the helper's source text.
- [ ] AC-4.6 / AC-10.2: `test_collect_none` — both channels empty — yields `delivered=none` and a
      `collected_path` of `None`.
- [ ] The force-direction mutation has a failing test **that reaches rung 3**: removing rung 2's
      success return makes a wait-delivered report fall through into extraction, so
      `test_collect_delayed_report` sees `delivered=out` and fails. It cannot be
      `test_collect_report_file_present` — that fixture returns at rung 1, so rung 3 is never
      executed there and the mutation would survive while being recorded as caught.
- [ ] `extract_report` exiting 2 yields `''`; any other non-zero raises `OperationalError`.

**Dependencies on other tasks**: Task 2 (must complete first)

---

## Task 4: helper → `h_mad_audit_gate.py` (per-pass gating)

**Production file**: `h-mad/scripts/h_mad_audit_cycle.py`
**Test file**: `h-mad/tests/test_h_mad_audit_cycle.py`
**Task shape**: `wiring`
**WIRE** (`wiring` shape only): `h-mad/scripts/h_mad_audit_cycle.py:gate` → `h_mad_audit_gate.py`
**WIRE-PIN** (`wiring` shape only): `test_fail_in_either_pass_fails_cycle`

**Description**: Introduces `gate()`, the `--pass` CLI flag, and `main()`'s full collect-and-gate
path — the three arrive **together**, deliberately. Task 1 does not declare `--pass` at all,
because a flag that is parsed and then ignored is how a fabricated `AUDITCYCLE: PASS` shipped once
already (see Task 1's ACs). This task is where `--pass` first becomes meaningful, so it is where the
flag is first accepted. `gate()` runs
`h_mad_audit_gate.py <collected> [--ack-file <p>]` **once per collected pass report** — never on a
concatenation — and takes the verdict from the last `GATE:` line on stdout, never from the exit code.
`GATE: INVALID` arrives at exit 2 and is a **verdict**, routed by its token; its `must=0 should=0`
are discarded at this boundary so no downstream code can read counts the gate never measured.

The findings that populate `PassResult.findings` come from a **second, independent in-process read**
of the same file using `h_mad_audit_gate`'s imported primitives (`_BULLET_MARKERS`, `_payload`,
`_acknowledged_from_text`, `_read_ack_file`) and its prose fall-back. That read happens in exactly one
place — here — and `premise_items()` does no parsing. `gate()` builds the acknowledged set by calling
the same two functions the CLI calls, in the same order, because they parse differently and the
subprocess's `must` already excludes acknowledged items; an unfiltered enumeration would exceed the
count. `assert len(findings) == must` binds the two pathways and raises `OperationalError` on
mismatch.

**`INVALID` short-circuits before the in-process read — the assertion must not run.** This ordering
is load-bearing and was measured 2026-08-20 rather than reasoned about. `has_gate_sections` is
`all(section in seen ...)`, so `INVALID` fires when **either** section is absent, not only when both
are. A report carrying a populated `## Must-fix` and no `## Should-fix` therefore produces:

```
subprocess:  GATE: INVALID must=0 should=0   (exit 2)
in-process:  classify(text) -> {'verdict': 'FAIL', 'must_count': 2, 'should_count': 0}
```

An unconditional `assert len(findings) == must` is then `2 == 0` and raises, crashing the cycle at
exit 4 on precisely the input AC-10.4 requires to yield `UNVERIFIED reason=no_gate_sections:p<i>` at
exit 0. So on an `INVALID` token `gate()` returns `("INVALID", 0, 0, [])` **immediately** — no
in-process read, no findings, no assertion. The assertion binds the two pathways only where both
pathways ran; a verdict that discarded its counts has nothing to bind.

(Note for the design: §"Detailed Design" states the count-discard and the assertion without ordering
them, and AC-5.6 says a report "lacking **both**" headers is refused where the code refuses on
either. The behaviour above is what the code does; the design wording is an erratum.)

Importing sibling primitives from `h_mad_audit_gate` is within-skill and does not breach
self-containment.

**Code structure**:
```python
def gate(collected: Path, *, ack_file: Path | None
         ) -> tuple[str | None, int, int, list[str]]:
    """(verdict, must, should, must_fix_bullets).

    INVALID returns ("INVALID", 0, 0, []) immediately: counts are discarded and the
    in-process read is SKIPPED, so the assertion below cannot fire on a verdict whose
    counts were never measured.

    On PASS/FAIL only: a second, in-process read with the gate's own primitives and
    prose fall-back, filtered by the same acknowledgement rules, asserted
    len(findings) == must."""
```

**Acceptance Criteria**:
- [ ] AC-5.1: one gate invocation per collected pass report, on that pass's own file — asserted by
      counting stub invocations and their argv paths. No invocation ever receives a concatenation.
- [ ] AC-5.3 / AC-5.4: per-pass `p<i>=<must>/<should>` fields appear; aggregate `must=`/`should=` are
      the sums, and the `note:` line stating the double-counting is printed literally.
- [ ] AC-4.4 / AC-4.4b: the `reports:` line names every collected path on PASS/FAIL and is omitted on
      `UNVERIFIED`, including when some passes did deliver.
- [ ] AC-5.6 / AC-10.4: `test_main_invalid_yields_unverified` covers three fixtures — a report
      missing **both** gate sections, missing **only** `## Must-fix`, and missing **only**
      `## Should-fix` — each yielding end-to-end `AUDITCYCLE: UNVERIFIED reason=no_gate_sections:p<i>`.
- [ ] `test_gate_invalid_discards_counts`: an `INVALID` verdict returns `(INVALID, 0, 0, [])` and the
      gate's printed counts are not carried forward.
- [ ] AC-5.7: `test_ack_file_forwarded` — a sidecar clearing p2's only finding — yields cycle PASS,
      and **both** gate stub invocations are asserted to have received `--ack-file`.
- [ ] AC-10.3: `test_prose_plus_bullet_not_concatenated` runs the **real** `h_mad_audit_gate.py`
      (stub-exempt): p1 prose-only finding, p2 one bullet → cycle `FAIL must=2` end-to-end, **and**
      the same two reports concatenated gate to `must=1`. Both halves are required — the second pins
      the trap, the first proves the helper avoids it.
- [ ] The fixtures are the **incident's own inputs**, committed under `h-mad/tests/fixtures/` rather
      than invented at test-writing time: the prose-only and single-bullet reports whose measured
      outputs (`must=1` alone, `must=1` alone, `must=1` concatenated against a true total of 2) are
      recorded in the plan's Architecture Considerations, with those three recorded values as the
      expected assertions. **No naturally-occurring prose-only report exists to replay instead** —
      measured across all 12 collected reports from this feature's own audit history, every blocking
      section is bulleted — so these inputs are the real artifacts of record for this incident, and
      the fixture is a replay rather than a synthetic stand-in.
- [ ] `test_premise_items_match_gate_count` runs the **real** gate (stub-exempt) over bulleted,
      prose, `• `-rendered and acknowledged-filtered reports. It asserts **content, not just count**:
      `len(items) == must` *and* that the extracted payloads equal the payloads the gate's own
      `_payload`/`_BULLET_MARKERS`/prose fall-back yield over the same text. Count equality alone
      would pass while the two reads selected different findings — equal-sized and divergent is
      exactly the failure a mirror is supposed to be checked for.
- [ ] There is **one** parsing implementation, not two: `gate()`'s in-process read calls
      `h_mad_audit_gate`'s own primitives rather than re-deriving the rules, so a change to the
      gate's parser moves both pathways together. `premise_items` parses nothing at all.
- [ ] AC-5.2: `test_fail_in_either_pass_fails_cycle` — p1 PASS + p2 FAIL, and the reverse — yields
      cycle `FAIL` both ways. It asserts **nothing** about dispatch: this is a helper test, and the
      helper has no `exec` path, so a dispatch-count assertion here could only observe a stub the
      helper never calls. AC-1.2's no-further-dispatch claim belongs to the verb suite and is pinned
      by `test_verb_fail_dispatch_count` (Task 7).
- [ ] The force-direction mutation has a failing test: removing the `delivered != "none"` guard so a
      `delivered=none` pass is gated anyway breaks the `no_report:p<i>` `UNVERIFIED` test. The
      mechanism is a crash, not a wrong count — a `delivered=none` pass has `collected_path is None`,
      so forcing `gate()` raises rather than returning counts. The test fails either way because it
      asserts an `UNVERIFIED` verdict, but the mutation must be recorded as caught-by-crash so a
      future reader does not expect a counted FAIL.
- [ ] `test_main_delivered_none_is_unverified` drives `main()` **end-to-end** with one delivering
      pass and one `delivered=none` pass, asserting `AUDITCYCLE: UNVERIFIED reason=no_report:p<i>`.
      This is the anchor for mutation 10 and it must exercise `main()`: the `delivered != "none"`
      guard lives there, so a `combine()`-level unit test bypasses the mutated line entirely and the
      mutation survives while the suite stays green. `test_combine_unverified_outranks_fail`
      (Task 1) remains the unit-level assertion on precedence and anchors nothing.

**Dependencies on other tasks**: Task 3 (must complete first)

---

## Task 5: verb → `h_mad_assemble_audit.py` (validation, clearing, assembly)

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_audit_cycle.py`
**Task shape**: `wiring`
**WIRE** (`wiring` shape only): `h-mad/scripts/hmad-dispatch.sh:audit-cycle` → `h_mad_assemble_audit.py`
**WIRE-PIN** (`wiring` shape only): `test_verb_assemble_halt_no_dispatch`

**Description**: The `audit-cycle)` case up to the dispatch barrier. Validates `--phase` and
`--passes` as the **first** action — before any clearing, so an invalid phase cannot delete a real
cycle's channels. Templates every per-pass path from the stem
`/tmp/audit_<feature>_<phase>_cycle<N>_p<i>`. Clears the report, its `.done` and the `--out` for each
pass and asserts `[ ! -e ]` on all three, treating a survivor as an operational error (exit 3, no
`AUDITCYCLE:` line); `--log` is deliberately not cleared. Assembles **every** pass before any pass
dispatches, parses each pass's own `ASSEMBLE:` token with `sed -n 's/^ASSEMBLE: //p'` taking the last
match, combines the tokens (any HALT, any missing token, any rc≠0 → no dispatch), computes
`size_status` as the worst over passes, and asserts the prompts differ at exactly one line which must
be the report-path line.

An assembly halt and a prompt divergence are both routed back through the helper's **no-pass** mode
so the verdict format has exactly one definition; the shell never formats a verdict line.

**Error routing is three-way, not two-way.** An `ASSEMBLE: HALT` is a *verdict* (`UNVERIFIED
reason=assemble_halt:p<i>`, exit 0, routed through the helper's no-pass mode), while a non-zero
`h_mad_assemble_audit.py` exit (AC-2.4) and an exit of 0 carrying **no** `ASSEMBLE:` token (AC-2.5)
are *operational errors*: exit 4, no `AUDITCYCLE:` line, no helper invocation at all. All three stop
the dispatch, which is why they are easy to collapse into one branch — and collapsing them would
report a broken assembly toolchain as a clean cannot-judge at exit 0.

**Code structure** (`hmad-dispatch.sh` is `#!/usr/bin/env bash`; `local`, `[[`, `$(( ))` and arrays
are the house style, not additions by this feature):
```sh
# Registered in main()'s dispatch table exactly like every other verb:
#     audit-cycle) _cmd_audit_cycle "$@" ;;
# The body lives in a FUNCTION, not inline in the case. Two reasons, both
# structural: `local` is only legal inside a function, and every other verb in
# this file is `_cmd_<verb>`. Note the file runs under `set -euo pipefail` (line 5),
# which the guards below are written against.
_cmd_audit_cycle() {
  # 0. resolve the sibling script dir ONCE, the way this file already does it at
  #    hmad-dispatch.sh:1295 — BASH_SOURCE, never "$0" (the bin/ shim execs this
  #    script, so "$0" can name the shim rather than this file):
  #      local here
  #      local -a prompt report out log asm tok rc pids
  #      here="${HMAD_AUDIT_CYCLE_SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)}"
  #    Every python3 call below goes through "$here/<script>.py" — never a bare
  #    script name, which would depend on PATH (forbidden by self-containment).
  # 1. validate --phase in {plan,design,impl-plan} and --passes >= 1  -> exit 2, no token.
  #    Parse the rest here too: --feature --cycle --project-root
  #    --ack-file (optional) --report-grace (default 5) --timeout (default 900).
  # 2. Per-pass paths are ARRAYS, assigned in a loop. `report_i` is not a bash
  #    construct: bash does not re-expand a scalar when `i` changes, so a name like
  #    `$report_i` transcribed literally holds pass 1's path for every later pass.
  #      stem="/tmp/audit_${feature}_${phase}_cycle${cycle}"
  #      i=1; while [ "$i" -le "$passes" ]; do
  #        prompt[$i]="${stem}_p${i}.txt"       report[$i]="${stem}_p${i}.report.md"
  #        out[$i]="${stem}_p${i}.out.txt"      log[$i]="${stem}_p${i}.log"
  #        asm[$i]="${stem}_p${i}.asm.txt"      # assemble's own stdout, parsed in step 4
  #        i=$((i + 1))
  #      done
  #    Every loop below uses the `while [ "$i" -le … ]` idiom, never `seq`.
  #    MEASURED on this machine: BSD/macOS `seq 2 1` prints "2\n1" — it counts
  #    BACKWARDS rather than yielding nothing. With `--passes 1` a `seq 2 "$passes"`
  #    divergence loop would therefore run for i=2, diff a prompt that was never
  #    assembled, and emit a false `prompt_divergence` verdict.
  # 3. i=1; while [ "$i" -le "$passes" ]; do
  #      rm -f "${report[$i]}" "${report[$i]}.done" "${out[$i]}" || true
  #      # `|| true` is REQUIRED, not defensive: MEASURED, `rm -f` on a file whose
  #      # parent is read-only exits 1 ("Permission denied"). Under `set -e` that
  #      # aborts the script with rc=1 BEFORE the assertion below runs, so the verb
  #      # would exit 1 instead of the documented 3 and `test_verb_unremovable_path`
  #      # — whose fixture is exactly a read-only parent — would fail.
  #      for p in "${report[$i]}" "${report[$i]}.done" "${out[$i]}"; do
  #        [ ! -e "$p" ] || { printf 'ERROR: channel not cleared: %s\n' "$p" >&2; exit 3; }
  #      done
  #      rm -f "${prompt[$i]}" "${asm[$i]}" || true   # this run rewrites both; a
  #                                           # read-only survivor fails the assembly write
  #      i=$((i + 1))
  #    done                                    # log[$i] deliberately NOT cleared (AC-3.3b)
  # 4. i=1; while [ "$i" -le "$passes" ]; do
  #      # `if/else`, NOT a bare call followed by `arc=$?`: MEASURED, under `set -e`
  #      # a non-zero exit aborts the script immediately and the `arc=$?` line is
  #      # never reached, so AC-2.4's `exit 4` could never fire. A call inside an
  #      # `if` condition is exempt from errexit, which is what makes rc capturable.
  #      if python3 "$here/h_mad_assemble_audit.py" --feature "$feature" --phase "$phase" \
  #           --cycle "$cycle" --project-root "$root" \
  #           --report-file "${report[$i]}" --out "${prompt[$i]}" >"${asm[$i]}"
  #      then arc=0; else arc=$?; fi
  #      tok[$i]="$(sed -n 's/^ASSEMBLE: //p' "${asm[$i]}" | tail -1)"   # ARRAY, not scalar
  #      [ "$arc" -eq 0 ]     || exit 4       # AC-2.4 operational error, no token line
  #      [ -n "${tok[$i]}" ]  || exit 4       # AC-2.5 operational error, no token line
  #      # The prompt-exists guard is scoped to PASS ONLY. A HALT deliberately
  #      # writes NO prompt (measured: the assemble refusal path leaves the --out
  #      # path absent, rc=0), so an unconditional `-s` here would convert every
  #      # legitimate HALT verdict into exit 4 and break AC-2.2.
  #      case "${tok[$i]}" in
  #        PASS*) [ -s "${prompt[$i]}" ] || exit 4 ;;   # token is not the artifact:
  #      esac                                   # a PASS with no prompt on disk would
  #                                             # dispatch agy at a missing file
  #      i=$((i + 1))
  #    done
  #    A scalar `tok_i` here is a silent defect: the loop overwrites it every
  #    iteration, so a HALT on pass 1 followed by a PASS on pass 2 leaves only the
  #    PASS visible and the verb dispatches a cycle it was required to refuse.
  # 5. size_status="verified"; i=1; while [ "$i" -le "$passes" ]; do
  #      case "${tok[$i]}" in *size_status=unverified*) size_status="unverified" ;; esac
  #      # Match the FIELD, not the bare word. Two things are pinned here:
  #      #  (a) lowercase is CORRECT and measured — the line reads
  #      #      `ASSEMBLE: PASS <path> <bytes> sentinel=<s> size_status=unverified`,
  #      #      so `*unverified*` matches and `*UNVERIFIED*` does NOT. Only the
  #      #      verdict word (PASS/HALT) is uppercase; the VALUE is lowercase.
  #      #  (b) the token also carries the PROMPT PATH, which embeds the feature
  #      #      name — so a bare `*unverified*` would match a feature literally
  #      #      called `unverified-logins` and report a verified cycle as
  #      #      unverified. Anchoring on `size_status=` cannot.
  #      i=$((i + 1))
  #    done
  #    Computed HERE, before either routing below consumes it. Placing this after
  #    the halt check leaves `--size-status ""` on the halt path.
  # 6. halt_pass=""; i=1; while [ "$i" -le "$passes" ]; do
  #      case "${tok[$i]}" in HALT*) halt_pass="$i"; break ;; esac
  #      i=$((i + 1))
  #    done
  #    if [ -n "$halt_pass" ]; then                              # AC-2.2 verdict
  #      python3 "$here/h_mad_audit_cycle.py" \
  #        --feature "$feature" --phase "$phase" --cycle "$cycle" \
  #        --project-root "$root" --passes "$passes" \
  #        --size-status "$size_status" \
  #        --halt-reason "assemble_halt:p${halt_pass}"
  #      exit $?
  #    fi
  #    The no-pass signature is exactly the design's: --feature --phase --cycle
  #    --project-root --passes --size-status --halt-reason. The helper renders
  #    `passes=K` and the `[H-MAD] <feature> audit-cycle <verdict>` marker from
  #    these and cannot count or name what it was not told. --grace and --ack-file
  #    are deliberately NOT forwarded here: no pass was dispatched, so nothing is
  #    collected and nothing is gated, and passing a collection/gating knob into a
  #    path that reaches neither would read as a control that does something.
  # 7. i=2; while [ "$i" -le "$passes" ]; do   # never runs when passes=1
  #      # `|| true` on BOTH pipelines: the file runs under `set -euo pipefail`, and
  #      # BOTH stages exit non-zero in the ordinary case — `diff` exits 1 whenever
  #      # the prompts differ (which they always do, by one line), and `grep -c`
  #      # exits 1 when its count is 0. Unguarded, the expected path is the failing
  #      # path.
  #      d="$( { diff "${prompt[1]}" "${prompt[$i]}" || true; } | grep -c '^[<>]' || true)"
  #      if ! { [ "$d" -eq 2 ] \
  #             && { diff "${prompt[1]}" "${prompt[$i]}" || true; } | grep -Fq "${report[1]}"; }; then
  #        python3 "$here/h_mad_audit_cycle.py" \
  #          --feature "$feature" --phase "$phase" --cycle "$cycle" \
  #          --project-root "$root" --passes "$passes" \
  #          --size-status "$size_status" --halt-reason "prompt_divergence"
  #        exit $?                            # AC-3.4 verdict, exit 0 from the helper
  #      fi
  #      i=$((i + 1))
  #    done                                   # -F: the report path contains literal dots
}
```

**Acceptance Criteria**:
- [ ] AC-1.4: an unknown or missing `--phase` exits 2 with no `AUDITCYCLE:` line and **zero**
      dispatches, and is rejected before any `rm`.
- [ ] Skill self-containment: every `python3` invocation the verb makes names an absolute
      `"$here/<script>.py"`, where `$here` is `${BASH_SOURCE[0]}`-derived (the pattern already used
      at `hmad-dispatch.sh:1295`), never `$0` and never a bare script name resolved through `PATH`.
      Pinned by a test that runs the verb with `PATH` emptied of the skill's `scripts/` directory and
      asserts it still resolves both helpers.
- [ ] AC-3.1: `test_verb_invalid_passes` — `--passes 0` and `--passes -1` — exits 2, prints no
      `AUDITCYCLE:` line and performs **zero** dispatches, pinning the guard against a zero-dispatch
      cycle that would otherwise be indistinguishable from the no-pass halt mode.
- [ ] AC-3.2 / AC-3.3: each pass gets a distinct `--out`, `--log` and report path, all carrying the
      pass index.
- [ ] Every CLI argument the verb accepts is parsed in the same first block — `--feature`, `--cycle`,
      `--project-root`, `--ack-file`, `--report-grace` (default 5) and `--timeout` (default 900) —
      and each is asserted to reach its consumer: `--report-grace` as the helper's `--grace`,
      `--timeout` as the per-pass `exec` watchdog. `--report-timeout` is **not** accepted (AC-4.1b);
      passing it exits 2 as an unknown option rather than being silently ignored.
- [ ] AC-3.3 / AC-10.5b: `test_verb_clears_all_three_channels` — a stale report, its stale `.done`
      marker and a stale `--out` are all three removed and asserted before dispatch.
- [ ] AC-3.3b: `--log` is not cleared; a pre-existing log survives the run.
- [ ] `test_verb_unremovable_path` — read-only parent directory — exits 3 with no `AUDITCYCLE:` line.
      The fixture **creates the condition**; a permissive mutation is invisible against a happy path.
- [ ] AC-2.1 / AC-3.4: assembly runs once per pass and completes for every pass before any dispatch.
- [ ] AC-2.2: `test_verb_assemble_halt_no_dispatch` — pass 2 halts — performs **zero** dispatches and
      emits `AUDITCYCLE: UNVERIFIED reason=assemble_halt:p2`, exit 0.
- [ ] AC-2.4 / AC-2.5: a non-zero `h_mad_assemble_audit.py` exit, and an exit of 0 with no
      `ASSEMBLE:` token, are both operational errors — never a PASS and never a dispatch. The
      no-token case is pinned by `test_verb_assemble_no_token_is_operational_error` (exit 4, no
      `AUDITCYCLE:` line, zero dispatches); that exact name is the anchor for Task 8's mutation 2.
- [ ] `test_verb_passes_one` additionally asserts the divergence loop does not execute at
      `--passes 1` — the guard against the measured BSD `seq 2 1` backwards-count, which would
      otherwise emit a false `prompt_divergence` on a single-pass cycle.
- [ ] AC-2.3: `size_status=` is echoed on the verb's output and is `unverified` if **any** pass
      reported `unverified`.
- [ ] AC-3.4 / AC-10.5b: `test_verb_prompt_divergence` — the plan edited between the two assemblies —
      yields `UNVERIFIED reason=prompt_divergence` at exit 0, a cannot-judge verdict rather than an
      operational error.

**Dependencies on other tasks**: Task 4 (must complete first)

---

## Task 6: verb → `exec agy` (concurrent dispatch and reap)

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_audit_cycle.py`
**Task shape**: `wiring`
**WIRE** (`wiring` shape only): `h-mad/scripts/hmad-dispatch.sh:audit-cycle` → `exec agy`
**WIRE-PIN** (`wiring` shape only): `test_verb_two_distinct_dispatches`

**Description**: Launches all K passes concurrently as `exec agy <prompt_i> --out <out_i>
--log <log_i> --cd <project-root> --timeout <timeout> &`, then reaps each with `wait` and records
`rc_i`. Reaping happens **before** any collection: `report_wait` polls a path and knows nothing about
a process, so collecting first would burn the whole timeout on a file a dead dispatch will never
write. A pass's non-zero `rc` is forwarded but never by itself fails the cycle.

Per-pass path isolation is a correctness constraint, not tidiness. Measured 2026-08-20: two
concurrent `exec` dispatches sharing one `--out` are **first**-writer-wins with an explicit refusal,
so pass 2's `--out` would hold pass 1's *report* — a well-formed, plausible audit report that a
collector cannot distinguish from a correct delivery, gating the cycle twice on one pass's findings
while reporting `passes=2`.

**Call the in-process entry point, not the CLI.** The verb lives inside `hmad-dispatch.sh`, so it
reaches the exec backend through `_cmd_exec agy …` — the same function the top-level dispatcher
routes to (`exec) _cmd_exec "$@"`). Re-invoking the wrapper as an external `hmad-dispatch exec`
would fork a second copy of the script and make the verb depend on its own presence on `PATH`.
Backgrounding a subshell around it is the existing house pattern in this file.

**Code structure**:
```sh
  # 8. i=1; while [ "$i" -le "$passes" ]; do
  #      ( _cmd_exec agy "${prompt[$i]}" --cd "$root" \
  #                  --out "${out[$i]}" --log "${log[$i]}" --timeout "$timeout" ) &
  #      pids[$i]=$!
  #      i=$((i + 1))
  #    done
  # 9. i=1; while [ "$i" -le "$passes" ]; do          # reap FIRST, always
  #      if wait "${pids[$i]}"; then rc[$i]=0; else rc[$i]=$?; fi
  #      i=$((i + 1))
  #    done
```

**Acceptance Criteria**:
- [ ] AC-3.2 / AC-10.1: `test_verb_two_distinct_dispatches` — `--passes 2` produces exactly two
      `_cmd_exec agy` invocations with pairwise-distinct `--out` and `--log`, asserted from the
      dispatch stub's recorded argv. The whole cycle runs offline; no test requires a live `agy`,
      network or pane.
- [ ] AC-3.3: report-path distinctness is asserted **from the assembly stub's `--report-file` argv**,
      not from the dispatch argv. The `_cmd_exec agy` command line carries `--out` and `--log` but
      **not** the report path — that path is embedded inside `${prompt[$i]}` by assembly — so a test
      asserting it from the dispatch argv would be asserting against a flag that is never there.
- [ ] AC-3.1: `test_verb_passes_one` — `--passes 1` produces exactly one dispatch. This is the
      failing test for the force-direction mutation (removing the `--passes` guard so the verb always
      dispatches 2).
- [ ] AC-4.1: every dispatch is reaped before the **helper is invoked**, asserted by ordering in the
      stub's invocation log. The verb makes no collection call itself — collection happens inside the
      helper — so this is the strongest ordering claim a verb test can make, and stating it as
      "before any collection call" would assert against a call this suite never observes.
- [ ] AC-3.5: a pass whose `exec` exits non-zero does not by itself fail the cycle; the verdict still
      comes from that pass's collected report and gate token.
- [ ] `rc[$i]` is captured per pass and forwarded to the helper unchanged. It is deliberately
      **inert in the verdict**: AC-3.5 makes a non-zero `exec` exit non-fatal, so `rc` reaches
      `PassSpec` for diagnosis only and is intentionally absent from `PassResult` and from
      `render()`'s output. Keeping it in the `--pass` payload is what lets an operator distinguish
      "the agent crashed and delivered nothing" from "the agent ran fine and delivered nothing"
      without re-reading `--log`; dropping it would collapse those two into one indistinguishable
      `delivered=none`.
- [ ] The dispatch reaches the exec backend through the in-process `_cmd_exec agy`, not by
      re-invoking `hmad-dispatch exec` as an external command — asserted by the stub intercepting
      `_cmd_exec`, so a re-forked wrapper would leave the stub unused and fail the test.

**Dependencies on other tasks**: Task 5 (must complete first)

---

## Task 7: verb → `h_mad_audit_cycle.py` (the shell→helper process boundary)

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_audit_cycle.py`
**Task shape**: `wiring`
**WIRE** (`wiring` shape only): `h-mad/scripts/hmad-dispatch.sh:audit-cycle` → `h_mad_audit_cycle.py`
**WIRE-PIN** (`wiring` shape only): `test_completed_cycle_emits_token`

**Description**: The full collect-and-gate invocation after reaping — every context argument
forwarded unconditionally (`--feature --phase --cycle --project-root --grace --size-status --passes`,
plus `--ack-file` when given), then one `--pass <i>:<report_i>:<out_i>:<rc_i>` per pass. The collected
path is deliberately **not** in the payload: the helper derives it from
`--project-root/--phase/--feature/--cycle/<i>`, so the phase→audit-dir mapping has exactly one home.

This is the load-bearing boundary — it carries every verdict line, on both the normal and the no-pass
path — and it is the easiest row to leave out of a connection table because the helper is this
feature's own code. A whole-module test passes while the shell silently fails to invoke it, leaving
the cycle with no verdict formatter at all.

**Code structure**:
```sh
  # 10. args=(--feature "$feature" --phase "$phase" --cycle "$cycle"
  #           --project-root "$root" --grace "$report_grace"   # verb flag is
  #                                           # --report-grace; helper flag is --grace
  #           --size-status "$size_status" --passes "$passes")
  #     [ -n "$ack_file" ] && args+=(--ack-file "$ack_file")
  #     i=1; while [ "$i" -le "$passes" ]; do
  #       args+=(--pass "${i}:${report[$i]}:${out[$i]}:${rc[$i]}")
  #       i=$((i + 1))
  #     done
  #     python3 "$here/h_mad_audit_cycle.py" "${args[@]}"     # $here from step 0
  #     exit $?      # 0 on any verdict; non-zero only operational error
  #     # Under errexit a non-zero helper exit aborts here with that same code, so
  #     # `exit $?` is reached only on success. That is deliberate and equivalent —
  #     # the helper's code propagates either way — and is why this call is NOT
  #     # wrapped in an if/else the way the assemble call is: there is no rc to
  #     # capture and branch on, only one to propagate.
```

**Acceptance Criteria**:
- [ ] `test_completed_cycle_emits_token`: a cycle where both passes deliver and gate emits exactly
      one `AUDITCYCLE:`-prefixed line on stdout. This test fails when the helper invocation alone is
      dropped after reaping.
- [ ] AC-8.1: the verdict line matches
      `AUDITCYCLE: (PASS|FAIL) must=<N> should=<M> passes=<K>` with the per-pass and `delivered=`
      fields following.
- [ ] AC-8.2: the verb exits 0 on PASS, FAIL and UNVERIFIED alike; non-zero only on operational
      error, and then with no `AUDITCYCLE:` line.
- [ ] AC-8.3 / AC-8.4: `[H-MAD] <feature> audit-cycle <verdict>` is emitted, and the verdict line is
      the only `AUDITCYCLE:`-prefixed line on stdout.
- [ ] AC-5.7: `--ack-file` is forwarded when given and absent when not, asserted against the recorded
      argv.
- [ ] AC-1.2: `test_verb_fail_dispatch_count` — a cycle whose verdict is `FAIL` makes **no further**
      `exec agy` dispatch, asserted by counting stub invocations across the whole verb run. This is a
      verb test by necessity: the helper never dispatches, so only this suite can observe it.
- [ ] AC-1.1: `test_verb_no_self_invocation` — the emitted command trace contains no nested
      `audit-cycle`; the verb is a single linear path with no loop over cycles.
- [ ] AC-1.3: `test_verb_writes_only_reports` snapshots the sandboxed docs tree before and after and
      asserts the only new files are the per-pass collected reports.
- [ ] The force-direction mutation has a failing test: removing the shell's `ASSEMBLE:`-token guard so
      the helper is invoked in full collect-and-gate mode even on a halt breaks
      `test_verb_assemble_halt_no_dispatch`.

**Dependencies on other tasks**: Task 6 (must complete first)

---

## Task 8: mutation specs

**Production file**: `h-mad/tests/specs/audit_cycle_gating.mutation.json`, `h-mad/tests/specs/audit_cycle_connections.mutation.json`
**Test file**: `h-mad/tests/test_hmad_dispatch_audit_cycle.py` (spec-shape assertions)
**Task shape**: `new-behaviour`

**Description**: Two `h_mad_mutation_harness.py` specs. The **gating** spec proves the verdict logic's
own guards bite; the **connections** spec proves the verb actually reaches each callee. They are
distinct: a whole-module revert establishes neither, because it removes both sides at once.

Every mutation is applied to the **caller**, leaving the callee intact. Mutating a callee's output (a
stubbed `ASSEMBLE: PASS`, a forced `GATE: PASS`) tests the caller's branch while modifying the callee,
so it is not a connection mutation and is not evidence the connection is enforced.

The harness refuses any anchor not matching exactly once, which is what makes an unlanded mutation
impossible to report as a caught one. Read the `MUTATION:` token, never `$?`.

**The twelve connection mutations, fully specified.** Each names the file, the **caller-side**
construct the anchor must match, and the test that must fail. The literal `find`/`replace` strings
are transcribed from those constructs when the spec is authored — every one of them is code written
by Tasks 1–7, so the anchor is determined by this table and not chosen at authoring time. The harness
refuses any anchor that does not match exactly once, so a mis-transcribed anchor halts rather than
reporting a caught mutation.

| # | Name | File | Caller-side anchor to mutate | Must then fail |
|---|---|---|---|---|
| 1 | `verb-assemble-drop` | `hmad-dispatch.sh` | the `h_mad_assemble_audit.py` invocation in the per-pass assembly loop → removed, dispatching `${prompt[$i]}` as found | `test_verb_assemble_halt_no_dispatch` |
| 2 | `verb-assemble-result-guard` | `hmad-dispatch.sh` | the **token-emptiness** guard `[ -n "${tok[$i]}" ] \|\| exit 4` → removed, so an assembly that emitted no `ASSEMBLE:` token is treated as usable | `test_verb_assemble_no_token_is_operational_error` |
| 3 | `verb-exec-drop-p2` | `hmad-dispatch.sh` | the dispatch loop bound `[ "$i" -le "$passes" ]` → `-le 1`, keeping pass 2's paths allocated | `test_verb_two_distinct_dispatches` |
| 4 | `verb-exec-force-2` | `hmad-dispatch.sh` | the same bound → hardcoded `-le 2`, ignoring `--passes` | `test_verb_passes_one` |
| 5 | `helper-report-wait-drop` | `h_mad_audit_cycle.py` | the `_run_report_wait(...)` call in `collect()` → replaced by `False` | `test_collect_delayed_report` |
| 6 | `helper-report-wait-force` | `h_mad_audit_cycle.py` | the rung-1 file-present-and-`.done` check → `if False:`, so it always waits | `test_collect_report_file_present` |
| 7 | `helper-extract-drop` | `h_mad_audit_cycle.py` | the `_run_extract_report(...)` call in `collect()` → replaced by `""` | `test_collect_falls_back_to_out` |
| 8 | `helper-extract-force` | `h_mad_audit_cycle.py` | **rung 2's success return** → removed, so a report delivered by the wait still falls through into rung 3 | `test_collect_delayed_report` (its `delivered` flips to `out`) |
| 9 | `helper-gate-drop-p2` | `h_mad_audit_cycle.py` | the per-pass `gate(...)` call in `main()`'s loop → skipped for `index == 2` | `test_fail_in_either_pass_fails_cycle` |
| 10 | `helper-gate-force-none` | `h_mad_audit_cycle.py` | the `delivered != "none"` guard before `gate(...)` **in `main()`** → removed | `test_main_delivered_none_is_unverified` (end-to-end through `main()`) |
| 11 | `verb-helper-drop` | `hmad-dispatch.sh` | the `h_mad_audit_cycle.py` invocation after reaping → removed | `test_completed_cycle_emits_token` |
| 12 | `verb-helper-force` | `hmad-dispatch.sh` | the **HALT branch** `if [ -n "$halt_pass" ]; then … exit $?; fi` (step 6) → removed, so the helper runs in full collect-and-gate mode even on a halt | `test_verb_assemble_halt_no_dispatch` |

**Every force-direction row must name a guard no other row uses.** Mutations 2 and 12 originally both
deleted the `ASSEMBLE:`/HALT branch, which is one guard claimed as the force direction for two
different connections — the inflation the connection-enforcement invariant warns about, since a
single deletion cannot certify two distinct call sites. They now target genuinely different guards:
row 2 removes the **token-emptiness** check (an assembly that spoke no token is treated as usable,
AC-2.5), row 12 removes the **HALT branch** (the helper is invoked in full collect-and-gate mode on a
halt, AC-2.2). Deleting either leaves the other standing, which is what makes them two mutations
rather than one counted twice.

**A force-direction mutation must land on code the failing test actually REACHES, and a
short-circuiting ladder makes that easy to get wrong.** Row 8 originally mutated "the empty-slot
check guarding rung 3" against `test_collect_report_file_present` — but that test delivers at rung 1,
which returns before rung 3 exists as executed code. The mutation would have run, changed nothing,
left the suite green, and been recorded as a **caught** guard. It now mutates rung 2's success return
against the delayed fixture, which is the only shape that reaches that far. Row 10 has the same shape
one level up: its guard lives in `main()`, so a `combine()` unit test bypasses it entirely and the
mutation survives silently; its failing test must drive `main()` end-to-end.

The gating spec (`audit_cycle_gating.mutation.json`) is separate and covers the verdict logic's own
guards, including the two shell guards named in the ACs below.

**Acceptance Criteria**:
- [ ] AC-10.5: the gating spec exists and every mutation is caught; `MUTATION: ALL_CAUGHT` with
      `survived=0 refused=0`.
- [ ] AC-10.5b: the gating spec covers the **two shell guards** as well as the Python ones — deleting
      the `[ ! -e "$path" ]` assertion while keeping the `rm` must fail `test_verb_unremovable_path`,
      and deleting the prompt divergence assertion while keeping both assemblies must fail
      `test_verb_prompt_divergence`.
- [ ] The connections spec carries one entry per call site in **both** directions, six sites, twelve
      mutations, each anchored on the caller.
- [ ] Both specs report `MUTATION: ALL_CAUGHT`; a `REFUSED`, `BASELINE_NOT_GREEN` or `UNREADABLE`
      token is treated as "nothing was measured" and halts, not as a pass.
- [ ] The three anchor tests named in the design's Test Plan
      (`test_verb_two_distinct_dispatches`, `test_fail_in_either_pass_fails_cycle`,
      `test_completed_cycle_emits_token`) each exist and are the failing test for their mutation.

**Dependencies on other tasks**: Task 7 (must complete first)

---

## Task 9: SKILL.md updates and the bidirectional docs token pin

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_h_mad_audit_cycle_docs.py`
**Task shape**: `new-behaviour`

**Description**: Documents the verb where an orchestrator will look for it and pins the token so the
script and the document cannot drift apart. §"Audit prompt assembly" leads with
`hmad-dispatch audit-cycle` as the way to run one audit cycle, keeping the hand-run step list below it
as the debugging path (base invariant: backward compatibility). §6.6 is amended to record the **measured**
report-file delivery rate — **17 of the 18 impl-plan audit passes delivered** via the report file,
with `cycle7_p1` alone writing neither the file nor its `.done` marker and being recovered from
`--out` — which is why the verb always arms the `--out` fallback. The helper registry gains an `h_mad_audit_cycle.py` entry carrying the
`AUDITCYCLE:` token.

**Code structure**:
```python
# test_h_mad_audit_cycle_docs.py — bidirectional, so neither side can drop the token alone
def test_docs_token_pinned():
    """AUDITCYCLE: appears in h_mad_audit_cycle.py  <=>  it appears in SKILL.md."""
```

**Acceptance Criteria**:
- [ ] AC-9.1: §"Audit prompt assembly" presents `hmad-dispatch audit-cycle` as the way to run a cycle,
      with the hand-run steps retained beneath it.
- [ ] AC-9.2: §6.6 records the measured 17-of-18 report-file delivery rate (the one fallback being
      `cycle7_p1`) and the resulting always-armed `--out` fallback.
- [ ] AC-9.3: the `AUDITCYCLE:` token is listed in SKILL.md's helper/verb registry alongside the other
      verdict tokens.
- [ ] AC-9.4: `test_docs_token_pinned` fails if **either** side drops the token — asserted by checking
      both directions, not one.
- [ ] AC-9.5: SKILL.md states adjacent to the verb's introduction that `audit-cycle` runs exactly one
      cycle and that the revision loop remains the orchestrator's.
- [ ] SKILL.md frontmatter `name`/`description` are unchanged and remain valid (skill manifest
      integrity).

**Dependencies on other tasks**: Task 8 (must complete first)

---

## Post-implementation verification (Phase 5f / 6, not a task)

The design's implementation-order step 7 is a **live** cycle against real `agy`, producing a real
verdict on a real audit. It writes no new file and is therefore not a task here; it is the Success
Criteria obligation discharged at 5f/6:

1. Run `hmad-dispatch audit-cycle --feature <a real feature> --phase plan --cycle <N>
   --project-root <repo>` against live `agy` and confirm a real `AUDITCYCLE:` line with per-pass
   counts and named collected reports.
2. Confirm the collected reports exist at `<audit-dir>/<feature>.<phase>.audit.v<N>.p<i>.md` and are
   the reports the passes actually produced.
3. 5f registry: `h_mad_wire_registry.py verify --base <5c sha> --rootdir <repo-root>
   --testpath h-mad/tests`, then `challenge --base <5c sha>` (warning-only, verdict-neutral).
4. Full suite: `pytest h-mad/tests/ -v --tb=short` — 100% pass.

## Invariant compliance

- **Skill self-containment** — `h_mad_audit_cycle.py` is stdlib-only and resolves siblings
  `__file__`-relative; the `HMAD_AUDIT_CYCLE_SCRIPT_DIR` override is test-only and
  `test_script_resolution_default` prevents it becoming the production path.
- **Audit-gate signal discipline** — every verdict exits 0; non-zero is reserved for operational
  error; `[H-MAD]` is emitted on every path; `GATE: INVALID`'s exit 2 is handled as a verdict.
- **Single-source contract** — `render()` is the only verdict formatter, reached by both paths.
- **No-plugin-dependency** — stdlib-only Python and **bash**, with no new external dependency. The
  design's §"Invariant Compliance" phrases this as "POSIX shell"; that wording is an erratum, not a
  constraint this plan is breaking. `h-mad/scripts/hmad-dispatch.sh` is `#!/usr/bin/env bash` and
  already uses 212 bash constructs (`local`, `[[`, `$(( ))`) including an array expansion at
  `hmad-dispatch.sh:1921` (`"${wargs[@]}"`). The invariant's substance is *no new external
  dependency*, which holds: `agy` was already required by the hand-run path this verb replaces.
  Rewriting this feature's code to strict POSIX `sh` would make it the only such region in the file.
- **Operator-override preservation** — `--ack-file` reaches every per-pass gate (Task 4, AC-5.7).
- **Backward compatibility** — purely additive; no existing verb, script or flag changes behaviour.
- **Connection enforcement** — six call sites, six `wiring` tasks, six WIRE-PINs, twelve caller-side
  mutations (Task 8).
- **Mutation verification** — both specs run through `h_mad_mutation_harness.py`, which refuses an
  anchor not matching exactly once.
- **Assumption verification** — the three load-bearing assumptions (shared-`--out` first-writer-wins,
  the concatenation under-count, `GATE: INVALID`'s unmeasured counts) were executed and are cited in
  the plan's Architecture Considerations.

## Version History
- v1.0: Initial implementation plan draft.
- v1.1: Impl-plan audit cycle-1 revisions (8 must-fix across two passes; the two passes agreed on 2
  of them). Task 5's code block split assembly error routing three ways — `HALT` is a verdict at
  exit 0, while a non-zero exit or a missing `ASSEMBLE:` token are operational errors at exit 4; the
  v1.0 block collapsed all three into the no-pass path, contradicting this plan's own AC-2.4/AC-2.5.
  Task 5's pseudo-code now uses the real templated variables and parses every accepted flag. Task 8's
  mutation spec placeholders are replaced by a twelve-row table naming file, caller-side anchor and
  failing test for each connection. The three measured assumptions are carried into a new
  §"Architecture constraints carried from the plan".

  **Two findings had correct facts and a wrong prescription, recorded here so the next reviewer does
  not re-derive them from the same premise:**
  - Both passes flagged `hmad_exec agy` as contradicting the design's `exec agy`, and both prescribed
    `exec agy`. Neither is right: the verb runs *inside* `hmad-dispatch.sh`, whose dispatcher routes
    `exec)` to `_cmd_exec` (`hmad-dispatch.sh:3139`). The corrected call is the in-process
    `_cmd_exec agy`, backgrounded in a subshell as at `:1968` and `:2077`. Calling the external CLI
    would fork a second copy of the script and make the verb depend on its own presence on `PATH`.
  - Both passes flagged bash arrays as violating a "POSIX shell only" claim, and one prescribed
    rewriting them as POSIX scalars. The contradiction is real but the wrong half was named: the
    script is `#!/usr/bin/env bash` with 212 bash constructs and an existing array expansion at
    `:1921`. The *claim* was corrected, not the code.
  - Pass 1's "Architecture Considerations is completely missing from the plan" is false as stated —

    `audit-cycle-verb.plan.md:177` carries it with all three probe transcripts. The underlying
    concern was real (an implementer reading only this document lacked them), so they are carried
    forward here rather than the section being invented.
- v1.2: Impl-plan audit cycle-2 revisions (2 must-fix, 1 should-fix, 2 nits; **both passes converged
  on the same must-fix**, unlike cycle 1). The must-fix was a real defect introduced in v1.0: the
  shell code blocks called `_script`, which is a **Python** function defined in Task 1, as though it
  were a shell command — `python3 "$(_script h_mad_audit_cycle.py)"` would have failed with
  `command not found`. Task 5 additionally invoked `h_mad_assemble_audit.py` by bare name, relying on
  `PATH`, which self-containment forbids. Both are fixed by resolving `$here` once in step 0 and
  routing every `python3` call through it, with a new AC pinning it under an emptied `PATH`.

  **The prescription was again not adopted as written.** Both passes prescribed
  `dirname "$0"`. This file already resolves siblings at `hmad-dispatch.sh:1295` with
  `"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"`, and `BASH_SOURCE` is the correct choice
  here specifically because `bin/hmad-dispatch` execs this script — under the shim, `$0` can name
  the shim rather than this file. The house pattern is kept and the reviewers' variant rejected on
  that evidence. Pass 2's `${HMAD_AUDIT_CYCLE_SCRIPT_DIR:-…}` half **was** adopted: it keeps one
  variable with one meaning ("where audit-cycle's sibling scripts live") across both processes and
  is what makes the verb's Python calls interceptable in tests.

  Also applied: `grep -Fq` for the report-path match (the path contains literal dots), `$(seq 2
  "$passes")` in place of `2..passes` (brace expansion does not expand variables), and a correction
  to Task 4's force-mutation rationale — that mutation is caught by a crash on
  `collected_path is None`, not by a wrong count.
- v1.3: Impl-plan audit cycle-3 revisions (6 must-fix, 2 should-fix, 1 nit; the passes overlapped on
  **none** of them — the alternating pattern returned). The finding count rose from cycle 2 because
  v1.2 added surface (the `$here` step, the twelve-row mutation table) and the new surface carried
  new defects.

  **The sharpest was verified by probe before being applied**, and it was real:
  `gate()`'s unconditional `assert len(findings) == must` crashes on an `INVALID` verdict. Measured —
  `has_gate_sections` is `all(...)`, so `INVALID` fires when **either** section is absent; a report
  with a populated `## Must-fix` and no `## Should-fix` gives subprocess `must=0` against an
  in-process `must_count=2`, so `2 == 0` raises. That is exit 4 on exactly the input AC-10.4 requires
  to yield `UNVERIFIED` at exit 0. `INVALID` now short-circuits before the in-process read.

  Also fixed: a scalar `tok_i` inside the assembly loop, which silently kept only the **last** pass's
  token — a HALT on pass 1 followed by a PASS on pass 2 would have dispatched a cycle the verb was
  required to refuse (now an array plus an explicit halt scan); the no-pass and prompt-divergence
  routings now forward every context arg, without which the helper cannot render `passes=K` or the
  `[H-MAD]` marker; `asm_i` was used but never defined; AC-1.2's no-further-dispatch assertion was
  grafted onto a **helper** test that cannot observe the shell's dispatch stub, and moves to
  `test_verb_fail_dispatch_count` in Task 7; mutation 10 named a test covering the wrong reason
  (`no_gate_sections` rather than `no_report`).

  **One finding was accepted in substance and refused in remedy.** Pass 1 called mutations 2 and 12
  "fake" and prescribed deleting them. The observation was right — both deleted the same
  `ASSEMBLE:`/HALT guard, so one deletion was being counted as certifying two connections — but
  dropping them would leave two connections with no force direction, which the base invariant asks
  for wherever a direction exists. They were re-pointed at genuinely distinct guards instead
  (token-emptiness vs the HALT branch), so deleting either leaves the other standing. Row 2 is named
`verb-assemble-result-guard` rather than `-force` because it is precisely an output-validation
mutation: the assembly call is unconditional, so "force it to fire" has no meaning there, and the
certifying direction for that connection is row 1's drop. Row 2 earns its place as guard-
discrimination coverage, not as a second certification of the same call site.
- v1.4: Impl-plan audit cycle-4 revisions (5 must-fix, 1 should-fix; the passes agreed on the
  step-ordering defect and on nothing else). **Two were confirmed by running the construct rather
  than reasoning about it**, and both were real:
  - `seq 2 1` on this machine prints `2\n1` — BSD/macOS `seq` counts **backwards** rather than
    yielding nothing. The divergence loop at `--passes 1` would therefore have run for `i=2`,
    diffed a prompt that was never assembled, and emitted a false `prompt_divergence` on a
    perfectly good single-pass cycle. Every loop now uses the `while [ "$i" -le … ]` idiom the
    file already uses, and `seq` appears nowhere.
  - `report_i="${stem}_p${i}…"; i=2; echo "$report_i"` still prints the **pass-1** path. The
    `<name>_i` shorthand was pseudo-code that a literal transcription turns into stale paths for
    every pass after the first; all per-pass paths are now arrays assigned in a loop.

  Also fixed: `size_status` was computed in step 6 and consumed in step 5, so the halt path would
  have forwarded `--size-status ""` (my own inline comment claimed the opposite ordering — the
  comment was the tell); Task 6's AC asserted distinct **report-file** paths from the dispatch argv,
  which never carries that flag (the report path is embedded inside the assembled prompt), so the
  assertion moves to the assembly stub's `--report-file` argv; and Task 5's ACs now name
  `test_verb_assemble_no_token_is_operational_error` explicitly, since Task 8's mutation 2 anchors
  on that exact name.
- v1.5: Impl-plan audit cycle-5 revisions (6 must-fix; both passes converged on the Task 7 scalars
  and diverged on everything else). Three of the six are the same underlying mistake — **a guard
  mutated in a place the failing test never executes**, which is worse than an uncaught defect
  because the harness records it as a *caught* one:
  - Mutation 8 targeted rung 3's slot check against `test_collect_report_file_present`, but that
    fixture returns at **rung 1** — rung 3 is not executed code there. Re-pointed at rung 2's
    success return against the delayed fixture, the only shape that reaches that far.
  - Mutation 10's guard lives in `main()`, but v1.3 had pointed it at
    `test_combine_unverified_outranks_fail`, a `combine()` unit test that bypasses `main()`
    entirely. A new end-to-end `test_main_delivered_none_is_unverified` is the anchor; the unit
    test stays and anchors nothing. **This defect was introduced by v1.3's own fix** — cycle 3
    corrected the *reason* the test covered and did not check its *level*.
  - Row 12's anchor column called the HALT branch the "`ASSEMBLE:`-token guard", which is the name
    of the **different** guard row 2 targets — the harness would have mutated the wrong line.

  Also fixed: Task 7 still passed `${report_i}`/`${out_i}` scalars into the `--pass` payload, the
  exact class v1.4 converted to arrays everywhere else; `size_status := "verified"` is not bash;
  Task 6's AC-4.1 claimed an ordering against collection calls the verb never makes; and `rc`'s
  deliberate inertness in the verdict is now stated rather than left to look like an oversight.

  **My own class sweep missed the Task 7 scalars.** The grep required a quote character before
  `${report_i}`, so `--pass "${i}:${report_i}:…"` did not match — the detection pattern was wrong,
  not the fix. The sweep is now `\$\{?(report|out|…)_i\}?` with no leading-context requirement.
- v1.6: Impl-plan audit cycle-6 revisions. **Pass 1 gated clean (`must=0 should=0`) while pass 2
  found three must-fixes** — the alternating pattern, and the cycle a single-pass gate would have
  shipped.

  **One finding was REFUTED by measurement, and its prescription would have broken a working
  guard.** Pass 2 reported the step-5 `case "${tok[$i]}" in *unverified*)` as a case-sensitivity bug
  and prescribed `*UNVERIFIED*`. Measured against real assemble output:

  ```
  tok = "PASS /tmp/… 129256B (126.2 KB) sentinel=AUDIT-…-v99 size_status=unverified"
  *unverified*  -> MATCHES
  *UNVERIFIED*  -> does NOT match
  ```

  Only the verdict word (`PASS`/`HALT`) is uppercase; the `size_status` **value** is lowercase. The
  lowercase pattern is correct and now carries a comment saying so, so the next reviewer does not
  re-file it.

  Applied in substance: `test_premise_items_match_gate_count` now asserts **content**, not just
  `len(items) == must` — equal-sized-but-divergent is the exact failure a mirror check exists to
  catch — and the plan states explicitly that `gate()` calls the gate's own primitives rather than
  re-deriving its rules, so there is one parser rather than two that can drift.

  **The incident-replay finding was accepted with a correction of fact.** It asked for replay against
  real artifacts rather than synthetic ones. Measured: across all 12 collected reports from this
  feature's own audit history, **every** blocking section is bulleted — no naturally-occurring
  prose-only report exists to replay. The concatenation probe's own inputs are therefore the real
  artifacts of record; they are committed as fixtures with the three recorded outputs as the expected
  values, which is a replay rather than a stand-in.

  Row 2 renamed `verb-assemble-result-guard`: the assembly call is unconditional, so "force" has no
  meaning there and row 1's drop is the certifying direction.
- v1.7: Impl-plan audit cycle-7 revisions (4 must-fix, 2 should-fix, 1 nit). **The cycle itself
  produced the evidence for §"Architecture constraints" item 2b**: pass 1 returned rc=0 having
  written neither its report file nor its `.done` marker, and had to be recovered from `--out` via
  `h_mad_extract_report.py`. `delivered=out,report-file` in one real cycle.

  Both passes raised `local here` at what they read as global scope. **The facts were right and both
  prescriptions ("drop `local`") diverge from the file**: the dispatcher *is* `main()`, a function
  whose own first line is `local verb`, and every verb routes to a `_cmd_<verb>` function. The body
  therefore moves into `_cmd_audit_cycle()` registered as `audit-cycle) _cmd_audit_cycle "$@" ;;`,
  which keeps `local` legal *and* matches every sibling verb.

  `set -euo pipefail` is confirmed at `hmad-dispatch.sh:5`, so the pipefail finding was real and is
  now guarded on **both** stages of the divergence check — `diff` exits 1 whenever the prompts differ
  (always, by one line) and `grep -c` exits 1 when its count is 0, so unguarded the *expected* path
  was the failing path.

  The `*unverified*` match is narrowed to `*size_status=unverified*`. This does not reverse v1.6's
  refutation — lowercase is still correct and `*UNVERIFIED*` still matches nothing — it closes a
  different hole in the same line: the token embeds the prompt path, which embeds the feature name,
  so a feature called `unverified-logins` would have reported every verified cycle as unverified.

  Also applied: assembly now asserts `[ -s "${prompt[$i]}" ]` before dispatch (a token is not an
  artifact — a clean `ASSEMBLE: PASS` with no prompt on disk would dispatch `agy` at a missing file);
  `${prompt[$i]}`/`${asm[$i]}` are cleared alongside the scored channels; and
  `test_combine_invalid_yields_unverified` is renamed `test_main_invalid_yields_unverified`, since a
  `test_combine_` prefix on a test asserting an end-to-end `AUDITCYCLE:` string is the exact
  unit-vs-`main()` confusion that produced the v1.5 mutation-anchor defect.
- v1.8: Impl-plan audit cycle-8 revisions (3 must-fix, 2 should-fix, 2 nits; p2 returned **zero**
  must-fixes while p1 found three — sides flipped again). All three must-fixes are one class, and it
  is a class **v1.7 created**: learning at cycle 7 that the file runs under `set -euo pipefail`, I
  guarded the `diff` pipeline and nothing else. Each was confirmed by running it:

  ```
  set -euo pipefail; false >/dev/null; arc=$?; echo REACHED   ->  never prints, rc=1
  rm -f <file in chmod 500 dir>                               ->  rc=1 ("Permission denied")
  assemble on a refusal path                                  ->  rc=0, prompt file ABSENT
  ```

  - `arc=$?` after a bare `python3 …` is unreachable under errexit, so AC-2.4's `exit 4` could never
    fire. The call moves inside an `if` condition, which is exempt from errexit.
  - `rm -f` exits 1 on a read-only parent and aborts the script **before** the `[ ! -e "$p" ]`
    assertion, so the verb would exit 1 rather than the documented 3 — failing
    `test_verb_unremovable_path`, whose fixture is exactly a read-only parent. Now `|| true`.
  - **The v1.7 `[ -s "${prompt[$i]}" ]` guard broke the HALT path.** A halt deliberately writes no
    prompt, so an unconditional check converts every legitimate `ASSEMBLE: HALT` into `exit 4` and
    breaks AC-2.2. The guard is now scoped to `PASS*` only. This is the second time in this feature
    that a correct fix for one finding composed into a new defect — the reason findings get
    reconciled against each other before any is applied.

  Also: the no-pass signature now states precisely which args it forwards and why `--grace`/
  `--ack-file` are excluded (that path collects nothing and gates nothing), replacing a blanket
  "every context arg" claim the code did not honour; "prompt byte-identity assertion" renamed
  "prompt divergence assertion" (the prompts differ by one line **by design**, so the old name
  described the opposite of the check); the clearing AC names the `.done` marker explicitly; and the
  per-pass arrays are declared `local -a` alongside `local here`.
- v1.9: J36 correction (post-implementation). Task 9's description and AC-9.2 both carried spec
  AC-9.2's false measurement — the report-file slot "measured **empty on 8 of 8 impl-plan cycles**".
  The staged artifacts show the opposite: **17 of the 18** impl-plan audit passes delivered via the
  report file; only `cycle7_p1` fell back to `--out`. Nine cycles, not eight, and the unit is the
  **pass**. This plan already contradicted itself — architecture constraint 2b records exactly that
  single mixed-delivery pass. Shipped behaviour is unaffected (the always-armed `--out` fallback is
  correct either way) and `h-mad/SKILL.md` §6.6 already carries the measured figure, so this edit
  makes AC-9.2 describe what actually shipped. Paired: spec v1.18, plan v1.12, design v1.22.
