# Design: audit-cycle-verb

## Executive Summary

`hmad-dispatch audit-cycle` is a shell verb that assembles and dispatches N independent `exec agy`
passes, then hands their per-pass paths to a new stdlib-only `h_mad_audit_cycle.py`, which collects,
gates, and emits the single `AUDITCYCLE:` verdict line.

## Overview

The design is a composition, not a rewrite: no existing script is modified. Two processes split the
work along a boundary drawn once — the shell owns assembly, dispatch and reaping; Python owns
collection, gating, the premise checklist and every verdict line. Every decision below that could
have been assumed was instead executed during the Phase-3 audit cycles, and the three that mattered
are recorded with their observed output in the plan's Architecture Considerations.

## Architecture Overview

```
hmad-dispatch audit-cycle --feature F --phase P --cycle N --project-root R [--passes K=2]
  │
  ├─ SHELL ────────────────────────────────────────────────────────────────────
  │   for i in 1..K:                         # assembly completes for EVERY pass
  │     clear <report_i>, <report_i>.done, <out_i>   ; assert [ ! -e ] on each
  │     h_mad_assemble_audit.py --feature F --phase P --cycle N --project-root R \
  │                              --report-file <report_i> --out <prompt_i>
  │     parse that pass's own `ASSEMBLE:` token (sed -n 's/^ASSEMBLE: //p', last match)
  │   combine tokens:  any HALT | any missing token | any rc≠0  →  no dispatch
  │   size_status := worst over passes (unverified if ANY pass said unverified)
  │   assert prompts differ ONLY at the report-path line
  │   for i in 1..K:  exec agy <prompt_i> --out <out_i> --log <log_i> \
  │                     --cd <project-root> --timeout <timeout> &          # concurrent
  │   wait each PID, record rc_i                                            # reap FIRST
  │
  └─ PYTHON  h_mad_audit_cycle.py --pass <i>:<report_i>:<out_i>:<rc_i> ... ──
        per pass:  report present? → report-file
                   else report_wait(grace) → report-file
                   else extract_report(--after-marker) → out
                   else → none
        per pass:  h_mad_audit_gate.py <collected_i> [--ack-file] → GATE token
        combine:   any delivered=none / GATE INVALID → UNVERIFIED (no counts)
                   any GATE FAIL                     → FAIL
                   else                              → PASS
        emit:      AUDITCYCLE: … + reports:/note: + premise checklist + [H-MAD] marker

  Full helper invocation (every context arg explicit; nothing inferred):
    h_mad_audit_cycle.py --feature F --phase P --cycle N --project-root R
                         --grace 5 --size-status verified|unverified --passes K
                         [--ack-file A]
                         --pass 1:<report_1>:<out_1>:<rc_1>
                         --pass 2:<report_2>:<out_2>:<rc_2>
    no-pass form:  h_mad_audit_cycle.py --feature F --phase P --cycle N --project-root R
                                        --passes K --halt-reason <r> --size-status <v>
                                        (no --pass at all)
      Every context arg is forwarded unconditionally, including in no-pass mode: --passes because
      render() prints `passes=K` and cannot count what was never dispatched, and --project-root
      because argparse requires it and the shell must not learn a second set of rules for when a
      flag applies.

  The collected path is NOT in the --pass payload: the helper derives it from
  --project-root/--phase/--feature/--cycle/<i>, mapping phase→audit-dir
  (plan,impl-plan → docs/01-plan/features ; design → docs/02-design/features).
  Passing it in would force the shell to duplicate that mapping, giving the rule two
  homes that can disagree. --feature is required by the no-pass form too, because the
  [H-MAD] <feature> audit-cycle <verdict> marker (AC-8.3) is emitted on every path.
```

The shell never formats a verdict line. The two conditions it decides alone — an assembly halt and a
prompt divergence — are routed back through the helper's no-pass mode so the format has exactly one
definition.

## Detailed Design

### Shell verb (`hmad-dispatch.sh`, new `audit-cycle)` case)

**Path templating.** All per-pass paths derive from one stem
`/tmp/audit_<feature>_<phase>_cycle<N>` plus `_p<i>`:

| Role | Path |
|---|---|
| assembled prompt | `<stem>_p<i>.txt` |
| report-file slot | `<stem>_p<i>.report.md` (+ `.done`) |
| `exec --out` | `<stem>_p<i>.out.txt` |
| `exec --log` | `<stem>_p<i>.log` |

**Pre-dispatch clearing.** For each pass, `rm -f` the report, its `.done`, and the `--out`, then
assert `[ ! -e "$p" ]` on each of the three. A survivor is an operational error (exit 3, no
`AUDITCYCLE:` line). `--log` is deliberately untouched: it appends by design, is never scored, and
its cross-run history is the diagnostic for the crash case this clearing guards against.

**Assembly, then a barrier.** Every pass assembles before any pass dispatches. A partial cycle —
dispatching the passes that assembled while one halted — would gate a `--passes 2` run on a single
pass while reporting `passes=2`, which is the exact misreport the union exists to prevent.

**Identity assertion.** `diff <prompt_1> <prompt_i>` must report exactly one changed line, and that
line must be the report path. Failure is `reason=prompt_divergence` — a cannot-judge verdict at exit
0, not an operational error, because every script ran correctly and detected a real condition.

**Dispatch and reap.** All passes launch concurrently and are reaped with `wait`; each `rc_i` is
captured and forwarded but never by itself fails the cycle (AC-3.5).

### Python helper (`h_mad_audit_cycle.py`)

Stdlib only. Public surface:

```python
PassSpec   = namedtuple("PassSpec",   "index report_path out_path rc")  # collected_path derived
PassResult = namedtuple("PassResult", "index delivered collected_path verdict must should findings")
#   delivered ∈ {"report-file", "out", "none"}
#   verdict   ∈ {"PASS", "FAIL", "INVALID", None}   # None = no GATE token at all

def collect(spec: PassSpec, *, grace: float, project_root, feature, phase, cycle) -> tuple[str, Path | None]
def gate(collected: Path, *, ack_file: Path | None) -> tuple[str | None, int, int, list[str]]
#   → (verdict, must, should, must_fix_bullets)  — the bullets populate PassResult.findings
def premise_items(results: list[PassResult]) -> list[str]   # findings arrive already filtered
def combine(results: list[PassResult]) -> tuple[str, str | None]   # (verdict, reason)
def render(results, verdict, reason, *, feature, size_status, passes) -> str
def main(argv) -> int
```

**`collect` — the four-outcome ladder**, in order, short-circuiting:

1. `report_path` is non-empty **and `report_path.done` exists** → copy to `spec.collected_path`,
   `("report-file", collected_path)`. **No wait at all.**

   The `.done` half is load-bearing and was nearly omitted. The agent writes the report and *then*
   marks `.done`, so a non-empty report without its marker is a **torn write** — a partial report
   caught mid-flush. Accepting it on size alone would gate the cycle on a truncated report, most
   likely as `GATE: INVALID` (its `## Should-fix` section never written), sending the operator to
   inspect a report the agent was in the middle of delivering correctly. Requiring the marker sends
   that case to step 2, where `report_wait` blocks for the marker the whole grace window —
   confirmed by probe to be exactly what it waits on (a present file with no `.done` times out at
   exit 1, identically to a file that never arrived).
2. `h_mad_report_wait.py <report_path> --timeout <grace>` → non-empty body → copy to
   `collected_path`, `("report-file", collected_path)`.
3. `h_mad_extract_report.py <out_path> --feature --phase --cycle --after-marker` → non-empty stdout
   → write to `collected_path`, `("out", collected_path)`.
4. otherwise `("none", None)`.

**Every write is verified by re-reading — and the destination is unlinked FIRST, or the re-read is
blind.** `collected_path` is NOT covered by the shell's pre-dispatch clearing, which touches only the
`/tmp` stem. So on a re-run of the same cycle (`v3` re-run after a failure) the previous run's report
already sits at exactly that path, and a write that silently lands nothing leaves `exists()` and
`st_size > 0` both **True on the OLD file's metadata** — the stale report is then scored as this
run's. Measured:

```
stale file at destination + write lands nothing
  guard says the write landed: True
  content actually scored   : 'STALE REPORT from the previous run'
```

The helper therefore calls `collected_path.unlink(missing_ok=True)` immediately before the write.
Only then does it assert `collected_path.exists() and collected_path.stat().st_size > 0` before the
pass is recorded as delivered. A write that raised no exception is not evidence the bytes landed — the same rule the
shell applies to its `rm`, in the other direction. A silently-empty collected report would gate as
`GATE: INVALID` and be reported as `no_gate_sections`, sending the operator to inspect a report the
agent actually delivered correctly.

**Every delivering branch lands the report at `collected_path`** — under
`<audit-dir>/<feature>.<phase>.audit.v<N>.p<i>.md`, never left in `/tmp`. AC-4.4 requires the
collected reports to live in the audit directory and the `reports:` line to name them; returning the
`/tmp` report path directly would satisfy neither, and would point the operator at a file the next
cycle's clearing step deletes.

Step 1 is why AC-10.2b exists: on the ordinary success fixture the wait in step 2 is never reached,
so its call site is off the executed path and a mutation there survives silently. The delayed
fixture (file created ~1s into the grace) is the only shape that exercises it.

**`gate` — token, never exit code.** Runs `h_mad_audit_gate.py <collected> [--ack-file <p>]` and
reads the last `GATE:` line. Three verdicts across two exit codes:

| gate output | exit | result |
|---|---|---|
| `GATE: PASS must=0 should=0` | 0 | `("PASS", 0, 0)` |
| `GATE: FAIL must=N should=M` | 0 | `("FAIL", N, M)` |
| `GATE: INVALID must=0 should=0` | 2 | `("INVALID", 0, 0)` — **counts discarded**, they were never measured |
| no `GATE:` line | any | `(None, 0, 0)` → operational error |

`INVALID`'s counts are dropped at the boundary rather than carried and ignored downstream, so no
later code can read them by accident.

**`INVALID` short-circuits before the in-process findings read — the `len(findings) == must`
assertion must not run on it.** Measured 2026-08-20: `has_gate_sections` is
`all(section in seen ...)`, so `INVALID` fires when **either** blocking section is absent, not only
when both are. A report carrying a populated `## Must-fix` and no `## Should-fix` therefore yields
subprocess `GATE: INVALID must=0` against an in-process `classify` of `must_count=2`, and an
unconditional assertion raises `2 == 0` — crashing the cycle at exit 4 on exactly the input AC-10.4
requires to yield `UNVERIFIED reason=no_gate_sections:p<i>` at exit 0. `gate()` therefore returns
`("INVALID", 0, 0, [])` immediately, performing no in-process read at all. The assertion binds the
two pathways only where both pathways ran; a verdict that discarded its counts has nothing to bind.
(Spec AC-5.6 says a report "lacking **both**" headers is refused, where the code refuses on either;
the code's behaviour is what is designed against here.)

**`combine` — operational error first, then cannot-judge, then FAIL.**

```
# A pass that delivered NOTHING never reaches the gate, so verdict is None for a benign
# reason. Only a pass that DID deliver and then produced no GATE: token is an operational
# error (AC-2.5 / AC-5.5) — raise before any verdict forms, exit 4, no AUDITCYCLE: line.
for r in results:
    if r.delivered != "none" and r.verdict is None:
        raise OperationalError(f"no GATE: token from pass {r.index} (delivered={r.delivered})")

# only now can a verdict be formed
for r in results:                       # first match wins, so the reason names one pass
    if r.delivered == "none":  return "UNVERIFIED", f"no_report:p{r.index}"
    if r.verdict == "INVALID": return "UNVERIFIED", f"no_gate_sections:p{r.index}"
if any(r.verdict == "FAIL" for r in results): return "FAIL", None
return "PASS", None
```

**The `delivered != "none"` qualifier is load-bearing, not defensive.** A pass that delivered on
neither channel never reaches `gate()`, so its `verdict` is `None` for an entirely benign reason.
Checking `verdict is None` unqualified — as this design did at v1.1 — would turn **every**
missing-report cycle into a crash at exit 4 with no token, instead of the `UNVERIFIED
reason=no_report:p<i>` at exit 0 that AC-6.2 and AC-6.3 require. The two states share a value and
differ only in how they were reached.

Three orderings, each load-bearing. **An absent `GATE:` token is not a cannot-judge** — it means the
gate did not run or did not speak, which is the operational-error path, and collapsing it into
`UNVERIFIED` would exit 0 on a broken toolchain. **Cannot-judge outranks FAIL**, because a cycle
where one pass measured nothing is not a cycle that found problems and reporting FAIL would let a
re-run "fix" it by chance. **`no_report` and `no_gate_sections` are distinct reasons** (AC-6.3):
nothing arrived versus something arrived that could not be scored, which demand different operator
responses — re-dispatch versus inspect the report.

**`render` — the verdict line.**

```
AUDITCYCLE: PASS  must=0 should=0 passes=2 p1=0/0 p2=0/0 delivered=report-file,report-file size_status=verified
AUDITCYCLE: FAIL  must=4 should=1 passes=2 p1=2/0 p2=2/1 delivered=report-file,out size_status=verified
AUDITCYCLE: UNVERIFIED reason=no_report:p2 passes=2 delivered=report-file,none size_status=verified
```

Exactly one `AUDITCYCLE:`-prefixed line is printed per invocation. Two further lines always follow
it, because both are requirements rather than presentation:

```
reports: docs/01-plan/features/F.plan.audit.v3.p1.md docs/01-plan/features/F.plan.audit.v3.p2.md
note: must=/should= are sums across passes and may double-count a finding both passes reported
```

The `reports:` line satisfies AC-4.4 — the collected paths must be **named on the output**, or the
operator cannot open what was scored. The `note:` line satisfies AC-5.4 literally: the spec requires
the output to *state* the double-counting, and relying on the reader to infer it from the per-pass
`p<i>=` fields is not stating it. Both are omitted on `UNVERIFIED`, which has no counts and may have
no collected reports — **and so is the premise checklist**. A cannot-judge cycle must not print a
partial list of must-fix citations harvested from whichever pass did deliver: that reads as "here is
what the cycle found", when the cycle's whole claim is that it found nothing it can stand behind.
`UNVERIFIED` output is the token line and the `[H-MAD]` marker, nothing else.

**A pre-dispatch `UNVERIFIED` prints no `delivered=` fields either.** The no-pass form has no
passes by construction, so there is no channel to report; emitting `delivered=none,none` would state
a measurement the cycle never took. Spec AC-6.4 is scoped to post-dispatch cannot-judges and AC-6.4b
covers this case.

`must=`/`should=` are sums across passes; per-pass `p<i>=` fields make the inflation visible.
`UNVERIFIED` carries **no** count fields at all — an absence, not a zero, so no consumer can read a
cannot-judge as clean.

**`premise_items` — single-sourced against the gate, and acknowledgement-aware.** For every
`## Must-fix` bullet across all collected reports it emits one unchecked line naming the pass and any
`path:line` citation, or `(no citation)`. Two constraints that are not optional:

- **Two read pathways, one extractor.** These are different things and the design must not blur
  them. The **token** comes from a subprocess: `h_mad_audit_gate.py <collected>` opens the markdown
  itself and prints `GATE: …` on stdout, and `gate()` reads only that stdout — it never sees the
  file's text through that channel. The **findings** therefore require a *second, independent read*
  of the same file, performed by `gate()` in the helper process using `h_mad_audit_gate`'s imported
  primitives (`_BULLET_MARKERS`, `_payload`, `_acknowledged_from_text`) and its prose fall-back.

  What "one extractor" means is that this second read happens in exactly **one** place — inside
  `gate()`, which returns the findings as the fourth element of its tuple, becoming
  `PassResult.findings`. `premise_items` **does no parsing at all**: it consumes those findings and
  only formats each entry and attaches its citation. Importing the gate's primitives is safe (a
  sibling module inside the same skill, not the cross-skill coupling the self-containment invariant
  forbids); a *second* call site using them would not be, because the drift being avoided is between
  two extractors in this helper, not between this helper and the gate.

  The `len(findings) == must` assertion is what binds the two pathways: the subprocess counted, the
  in-process read enumerated, and if they disagree the file was read differently by the two, which
  is an operational error rather than a result.
- **`gate()` owns acknowledgement filtering, and it has no choice.** The subprocess's `must` count
  already excludes items cleared via `## Acknowledged-not-fixed`, so the `len(findings) == must`
  assertion only holds if the in-process read applies the *same* filter — an unfiltered enumeration
  would exceed the count and raise on every cycle carrying an acknowledgement. `gate()` therefore
  builds the acknowledged set **exactly as the CLI does — by calling the same two functions, in the
  same order**: `_acknowledged_from_text(report_text)` for the `## Acknowledged-not-fixed` section
  inside the report, then `.update(_read_ack_file(ack_file))` when `--ack-file` was passed. Source-
  checked 2026-08-20: there is **no automatic sidecar resolution** — the gate reads only those two
  places, and an operator's `.audit.v<N+1>.md` sidecar reaches it solely by being passed as
  `--ack-file`. The two functions also parse differently (`_acknowledged_from_text` is section-scoped
  and bullet-aware; `_read_ack_file` strips a leading `- ` and accepts any non-empty line), so
  calling both is required — collapsing them into one rule would drop acknowledgements from whichever
  source the surviving rule does not match, and an item the subprocess excluded but the in-process
  read kept fails the `len(findings) == must` assertion, crashing the cycle on a legitimate override.
  It returns findings already filtered. `premise_items` receives no acknowledged argument: giving
  it one would put the filter in two places, and the second would be dead code that reads as live.
  The effect the operator sees is unchanged — a cleared finding is scored away *and* absent from the
  checklist, so the gate and the premise list cannot disagree about the override.

- **`gate()` applies the prose fall-back, and a differential assertion proves it.**
  `_count_section_findings` counts a **prose** block as one finding when a section carries no
  bullets — the exact case that motivated per-pass gating. An extractor that looked only for bullets
  would yield `GATE: FAIL must=1` alongside a checklist of **zero** items: a must-fix the premise
  list silently omits, and precisely the finding shape this feature was designed around. `gate()`
  therefore applies the same fall-back on its in-process read and asserts `len(findings) == must`
  against the count the subprocess reported, raising an operational error on mismatch rather than
  returning a finding list known to disagree with the gate's own count. `test_premise_items_match_gate_count` pins it against the **real**
  gate across bulleted, prose, `• `-rendered and acknowledged-filtered reports.

Cited files are never opened: whether the code means what a finding claims is judgment, not parsing.
On PASS the list is empty and the renderer says so on one line rather than printing nothing.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `audit-cycle` verb | `h-mad/scripts/hmad-dispatch.sh` | modify | Assembly, clearing, dispatch, reaping, no-pass routing |
| Cycle helper | `h-mad/scripts/h_mad_audit_cycle.py` | new | Collection, gating, premise list, verdict rendering |
| Helper tests | `h-mad/tests/test_h_mad_audit_cycle.py` | new | Collection ladder, gating, combine, render |
| Verb tests | `h-mad/tests/test_hmad_dispatch_audit_cycle.py` | new | Stubbed dispatch, assembly gating, clearing, no-pass mode |
| Docs test | `h-mad/tests/test_h_mad_audit_cycle_docs.py` | new | Bidirectional `AUDITCYCLE:` token pin |
| Gating mutations | `h-mad/tests/specs/audit_cycle_gating.mutation.json` | new | Guard discrimination, incl. the two shell guards |
| Connection mutations | `h-mad/tests/specs/audit_cycle_connections.mutation.json` | new | One entry per call site, both directions |
| Skill docs | `h-mad/SKILL.md` | modify | Verb leads §"Audit prompt assembly" and states it runs **one** cycle with the revision loop staying the orchestrator's (AC-9.5); §6.6 amended to record the **measured** report-file delivery rate — **17 of the 18 impl-plan audit passes delivered** via the report file, `cycle7_p1` alone fell back to `--out` — and that the verb therefore always arms the `--out` fallback (AC-9.2); `AUDITCYCLE:` added to the token registry (AC-9.3) |

## Implementation Order

1. `h_mad_audit_cycle.py` — `collect`, `gate`, `combine`, `render`, `premise_items`, `main`.
2. `test_h_mad_audit_cycle.py` — every AC that is helper-scoped, including the delayed-delivery and
   file-present-no-wait fixtures.
3. `audit-cycle` verb in `hmad-dispatch.sh`, including clearing, assertions and no-pass routing.
4. `test_hmad_dispatch_audit_cycle.py` — stubbed `exec agy`; the stub lives here, not in the helper
   suite, because the helper never dispatches.
5. Both mutation specs; run them and confirm every mutation is caught **and landed**.
6. `SKILL.md` updates, then `test_h_mad_audit_cycle_docs.py` to pin the token bidirectionally.
7. Live cycle against real `agy` (Success Criteria), producing a real verdict on a real audit.

Steps 1–2 and 3–4 are each test-after-implementation only in listing order; under Phase 5 both run
RED-first per module.

### Requirements covered here that are otherwise easy to miss

| AC | Where this design satisfies it |
|---|---|
| AC-1.1 | The verb is a single linear shell path — assemble, dispatch, reap, call helper, exit. It contains no loop over cycles and no self-invocation; `audit-cycle` never appears in its own body. Pinned by `test_verb_no_self_invocation` (greps the emitted command trace for a nested `audit-cycle`). |
| AC-1.2 | Dispatch happens once, before collection; the helper cannot dispatch (it has no `exec` path). A FAIL is therefore structurally incapable of triggering another dispatch, asserted by `test_verb_fail_dispatch_count` counting stub invocations. |
| AC-1.3 | The only writes under `docs/` are the per-pass collected reports at `<audit-dir>/<feature>.<phase>.audit.v<N>.p<i>.md`. Everything else lives under the `/tmp` stem. `test_verb_writes_only_reports` snapshots the docs tree before and after. |
| AC-1.4 | `--phase` is validated against `{plan, design, impl-plan}` as the **first** action, before any clearing or assembly, exiting 2 with no `AUDITCYCLE:` line. Validating before clearing matters: an invalid phase must not delete a real cycle's channels. |
| AC-3.1 | `--passes` is validated in the same first block: a non-integer or `K < 1` exits 2 with no `AUDITCYCLE:` line. `K=0` is the dangerous value — an unguarded `for i in $(seq 1 0)` runs **zero** dispatches and the helper would then be handed no `--pass` at all, which is indistinguishable from the no-pass halt mode and would print a verdict for an audit that never ran. |
| AC-9.5 | `SKILL.md` §"Audit prompt assembly" gains an explicit sentence that `audit-cycle` runs exactly one cycle and that the revision loop remains the orchestrator's, adjacent to the verb's introduction. |

## Data Model / Schema Changes

None. No `orchestrator_state` field is added or read; `.h-mad/telemetry.jsonl` is untouched. The
only new persistent artifacts are the per-pass audit reports
`<feature>.<phase>.audit.v<N>.p<i>.md`, which are files, not schema.

## API / Interface Changes

New verb only; no existing signature changes.

```
hmad-dispatch audit-cycle --feature <name> --phase plan|design|impl-plan --cycle <N>
                          --project-root <path>
                          [--passes <K>]           # default 2, K>=1
                          [--ack-file <path>]      # forwarded to EVERY per-pass gate
                          [--report-grace <sec>]   # default 5, post-reap
                          [--timeout <sec>]        # per-pass exec watchdog, default 900
```

**`--report-timeout` is deliberately absent**, and the plan (v1.11) and spec (AC-4.1b, v1.10) now
agree. This design has only the reap-first flow, so the flag would reach no logic at all. A CLI
flag that silently does nothing is worse than an absent one: it reads as a supported control and
invites an operator to tune a timeout that cannot apply. Spec AC-4.1b is amended to record the
removal rather than the retention.

Exit codes: `0` on any verdict (PASS / FAIL / UNVERIFIED); non-zero only for operational error —
`2` bad arguments, `3` a channel that would not clear, `4` a composed script exiting non-zero or
emitting no token.

## Error Handling Strategy

**A composed script's non-zero exit is triaged, never blanket-trusted or blanket-raised.** Each of
the three has one non-zero code that is a legitimate "nothing here" and must fall through to the
next rung, while every other non-zero is an operational error that must crash rather than degrade:

Codes measured 2026-08-20, not assumed:

| Script | Non-zero that means "nothing here" | Any other non-zero |
|---|---|---|
| `h_mad_report_wait.py` | **exit 1** — timed out; covers both "file never arrived" and "file present but no `.done`" | operational error, exit 4 |
| `h_mad_extract_report.py` | **exit 2** — covers a missing file, an empty file, and a present file with no sentinel pair, all three identically | operational error, exit 4 |
| `h_mad_audit_gate.py` | **exit 2** with `GATE: INVALID` — a cannot-judge **verdict** | operational error, exit 4 |

The `extract_report` result retires a hazard the audit raised: a dispatch that dies instantly leaves
no `--out` file at all (the shell cleared it pre-dispatch), and the concern was that a
`FileNotFoundError` would surface as exit 1 and crash the cycle on an ordinary dispatch failure. It
does not — the missing-file case exits 2 with `ERROR: [Errno 2] No such file or directory` on
stderr, the same code as a present-but-unsentinelled file, so it routes to `delivered=none` as
intended.

A blanket `check=True` would turn all three legitimate cases into crashes; treating every non-zero
as empty output would let a traceback in the extraction toolchain read as `delivered=none` and
produce a benign-looking `UNVERIFIED` — a broken toolchain reported as a cycle that merely could not
judge. The discriminator is the token or the specific code, never the fact of failure.

Verdicts go to stdout as a token and always exit 0; operational errors go to stderr as `ERROR:` and
exit non-zero with **no** `AUDITCYCLE:` line. The distinction is *did a script run at all* versus
*what did it decide*, and both are read for every composed call — exit code for the first question,
token for the second. A non-zero exit is never a FAIL verdict, and an absent token is never a PASS.

`GATE: INVALID` is the one case where a non-zero exit (2) is a **verdict**, not an operational
error; it is routed by its token like everything else.

## Test Strategy

Helper tests mock at the **subprocess boundary**, but **not via `PATH`** — that would not work and
would fail silently. The helper resolves its sibling scripts `__file__`-relative (Skill
self-containment), producing absolute paths that bypass `PATH` lookup entirely; stubs placed on
`PATH` would never be consulted and every "mocked" test would quietly execute the **real** scripts.
The suite would stay green while the mocked error paths — `GATE: INVALID`, delayed delivery,
`delivered=none` — went untested, which is the test-discrimination failure in its purest form: a
green suite over code no test reached.

Interception is therefore explicit. `h_mad_audit_cycle.py` resolves every sibling through one
function:

```python
def _script(name: str) -> Path:
    base = os.environ.get("HMAD_AUDIT_CYCLE_SCRIPT_DIR")      # test-only override
    return Path(base) / name if base else Path(__file__).resolve().parent / name
```

Tests set `HMAD_AUDIT_CYCLE_SCRIPT_DIR` to a `tmp_path` holding the stubs. Default behaviour is
unchanged and still `__file__`-relative with no `PATH` dependence, so self-containment holds; the
override exists solely so interception is a real mechanism rather than an assumed one.
`test_script_resolution_default` asserts that with the variable unset the resolved paths are the
real siblings, so the override cannot silently become the production path.

The helper's own argument construction and token parsing are exercised for real against the stubs. Verb tests stub `exec agy` the same way. No
test requires a live `agy`, network, or pane.

**Two tests are exempt from the stub and must run the real gate — and the rule generalises: any
test whose subject is the REAL gate's behaviour cannot use a stub, because a stub can only prove it
behaves as configured.** Both exemptions exist because `premise_items` and the per-pass gating
decision are each pinned to what `h_mad_audit_gate.py` actually does:

- `test_premise_items_match_gate_count` — the **in-process read inside `gate()`** applies the gate's
  prose fall-back, and a second read of the same file is only verified by a differential test
  against the original. (The subject is `gate()`'s read, not `premise_items`, which does no parsing
  — the test keeps its name because what it pins is that the findings `premise_items` *receives*
  match what the real gate counted.) Run against a stub it asserts that the mirror matches the
  test author's own fixture, which is the thing least likely to be wrong; the real gate's edge cases
  (`• ` bullets, `**Note:**` exclusion, stripped indentation, the prose fall-back itself) go
  untested. It runs the real gate over bulleted, prose, `• `-rendered and acknowledged-filtered
  reports and asserts `len(items) == must` for each.
- `test_prose_plus_bullet_not_concatenated` exists to pin `h_mad_audit_gate.classify`'s actual
behaviour — that a prose finding concatenated with a bulleted one is under-counted — which is the
measurement the whole per-pass-gating decision rests on (AC-10.3). A stubbed gate cannot pin the
real gate: it would assert that the stub behaves as configured, and a future change to the real
parser would escape silently, retiring the guard while it still looks green. That test therefore
invokes `h_mad_audit_gate.py` directly. Every other helper test keeps the stub, because they are
exercising the helper's argument construction and token parsing, not the gate's semantics.

**Every test sandboxes `--project-root` to a `tmp_path`.** The collected-report path is derived
from it, so a test run against the real repo root writes audit artifacts into the live
`docs/01-plan/features/` tree — and a test that crashes before cleanup leaves them there, where the
next cycle's clearing step does not look and a future census counts them as real. `test_verb_writes_only_reports`
snapshots that sandbox, not the repository.

Two fixtures must **create the condition** rather than assert on a happy path, because a permissive
mutation is invisible against inputs that never trip the guard: delayed report delivery (for the
`report_wait` call site) and an unremovable path (for the clearing assertion).

## Test Plan

| Test | Scenario | Verification |
|---|---|---|
| `test_collect_report_file_present` | report non-empty at reap | `delivered=report-file`; `report_wait` stub records **zero** invocations |
| `test_collect_delayed_report` | file created ~1s into grace | `delivered=report-file`; wait stub invoked once |
| `test_collect_falls_back_to_out` | report empty, `--out` holds a sentinel report | `delivered=out` |
| `test_collect_none` | both channels empty | `delivered=none` |
| `test_gate_invalid_discards_counts` | header-less report | verdict `INVALID`, counts dropped |
| `test_combine_unverified_outranks_fail` | p1 FAIL, p2 none | `UNVERIFIED`, no count fields |
| `test_prose_plus_bullet_not_concatenated` | p1 prose-only finding, p2 one bullet, **real gate, both passes** | cycle `FAIL must=2` end-to-end through `gate()`+`combine()`, **and** the same two reports concatenated gate to `must=1` — the second half pins the trap, the first proves the helper avoids it |
| `test_render_pass_has_no_premise_items` | both clean | one line stating the checklist is empty |
| `test_ack_file_forwarded` | sidecar clears p2's only finding | cycle `PASS`; both gate stubs saw `--ack-file` |
| `test_verb_assemble_halt_no_dispatch` | pass 2 assembly halts | zero dispatches; `UNVERIFIED reason=assemble_halt:p2` |
| `test_verb_clears_all_three_channels` | stale report, stale `.done` marker AND stale `--out` — all three | **all three** removed and asserted before dispatch |
| `test_verb_unremovable_path` | read-only parent | exit 3, no `AUDITCYCLE:` line |
| `test_verb_prompt_divergence` | plan edited between assemblies | `UNVERIFIED reason=prompt_divergence`, exit 0 |
| `test_verb_passes_one` | `--passes 1` | exactly one dispatch |
| `test_verb_two_distinct_dispatches` | `--passes 2` | exactly two `exec agy` invocations, with distinct `--out`/`--log`/report paths — **anchors the `exec agy` connection mutation** |
| `test_fail_in_either_pass_fails_cycle` | p1 PASS, p2 FAIL (and the reverse) | cycle `FAIL` both ways — **anchors the `h_mad_audit_gate.py` connection mutation** |
| `test_completed_cycle_emits_token` | both passes deliver and gate | exactly one `AUDITCYCLE:` line on stdout — **anchors the shell→helper connection mutation** |
| `test_verb_invalid_passes` | `--passes 0` and `--passes -1` | exit 2, no `AUDITCYCLE:` line, **zero** dispatches — pins the guard against a zero-dispatch cycle |
| `test_main_invalid_yields_unverified` | three fixtures: report missing **both** sections, missing **only `## Must-fix`**, missing **only `## Should-fix`** | each yields end-to-end `AUDITCYCLE: UNVERIFIED reason=no_gate_sections:p<i>` — AC-10.4 says *either* section, and the single-section cases are the ones a future `has_gate_sections` relaxation would silently break |
| `test_verb_assemble_no_token_is_operational_error` | assembly exits 0 emitting no `ASSEMBLE:` token | exit 4, no `AUDITCYCLE:` line, **zero** dispatches — **anchors the token-emptiness guard mutation** (impl-plan Task 8 row 2) |
| `test_main_delivered_none_is_unverified` | one delivering pass, one `delivered=none`, driven through `main()` | `AUDITCYCLE: UNVERIFIED reason=no_report:p<i>` — **anchors the `main()` gate-invocation guard mutation** (impl-plan Task 8 row 10). NOTE there are TWO distinct guards spelled `delivered != "none"`, and this row anchors the second: `combine()` uses it as the qualifier on the operational-error raise (`delivered != "none" AND verdict is None`), while `main()` uses it to decide whether to call `gate()` at all. This row targets `main()`'s, so a `combine()`-level test bypasses the mutated line: the `delivered != "none"` guard lives there, so a `combine()`-level test bypasses the mutated line and the mutation survives green |
| `test_verb_fail_dispatch_count` | cycle verdict is FAIL | no further `exec agy` dispatch (AC-1.2). A **verb** test by necessity — the helper never dispatches, so no helper test can observe it |
| `test_gate_count_mismatch_is_operational_error` | stub gate reports `must=2` for a file carrying 1 finding | `gate()` raises `OperationalError`; cycle exits 4 with NO `AUDITCYCLE:` line — **the negative test for `len(findings) == must`**. Without it, deleting that assertion survives on a green suite |
| `test_collected_write_failure_is_operational_error` | a STALE report from a previous run already at `collected_path`, PLUS `Path.write_bytes`/`write_text` monkeypatched to a SILENT NO-OP | `collect()` raises `OperationalError` — **the negative test for the `exists() and st_size > 0` re-read**. A read-only destination dir does NOT work here: the guard sits *after* the write, so `write_bytes` raises `PermissionError` first and the cycle crashes for a different reason — deleting the guard would still crash and the mutation would survive. The fixture must make the write appear to SUCCEED and leave nothing behind, which is the only shape that reaches the guard. The stale file is required too: without the `unlink`, the guard reads the OLD file and passes, so a fixture with an empty destination would pass for the wrong reason and the mutation would survive |
| `test_verb_assemble_nonzero_exit_is_operational_error` | `h_mad_assemble_audit.py` exits non-zero (unreadable inputs) | exit 4, no `AUDITCYCLE:` line, zero dispatches — AC-2.4. Distinct from the absent-token case (AC-2.5), which is a different guard |
| `test_verb_no_self_invocation` | emitted command trace | contains no nested `audit-cycle` (AC-1.1) |
| `test_verb_writes_only_reports` | sandboxed docs tree snapshotted before/after | the only new files are the per-pass collected reports (AC-1.3) |
| `test_verb_phase_validated_before_clearing` | invalid `--phase` with stale channels present on disk | exit 2, and the stale files are STILL THERE — validation runs before any `rm`, so an invalid phase cannot delete a real cycle's channels (AC-1.4) |
| `test_premise_items_formats_no_citation` / `..._formats_supplied_path_line` | a must-fix bullet with and without a `path:line` | `(no citation)` marker and the cited path respectively (AC-7.2, AC-7.3) |
| `test_premise_items_match_gate_count` | bulleted, prose, `• `-rendered and acknowledged-filtered reports, **real gate**, AND a sample of REAL collected reports from `docs/0{1,2}-*/features/*.audit.v*.p*.md` | `len(items) == must` AND the payloads equal the gate's own — the differential test for `gate()`'s in-process read. The real-artifact half is required by `invariants.base.md` §"Reimplementation parity" — synthetic fixtures only encode the author's own model of the format, and this repo already holds 55+ real agent-produced reports |
| `test_docs_token_pinned` | token in script ⇔ token in SKILL.md | fails if either drops it |

The rows marked *anchors* are the positive tests the plan's connection-mutation table removes
against. A mutation with no failing test to catch it is not a verified connection — the mutation
runs, the suite stays green, and the harness reports the connection enforced. They are listed here
explicitly because a test plan that omits them still looks complete.

Commands: `pytest h-mad/tests/test_h_mad_audit_cycle.py h-mad/tests/test_hmad_dispatch_audit_cycle.py -v`,
then `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/specs/audit_cycle_gating.mutation.json`
and the connections spec, each read by its `MUTATION:` token.

## Invariant Compliance

**Skill self-containment** — complies. `h_mad_audit_cycle.py` imports only the stdlib and resolves
its sibling scripts relative to its own `__file__`, never through `~/.claude/skills/...` or another
skill's internals. It is runnable from a bare clone.

**Skill manifest integrity** — complies. The verb changes `hmad-dispatch`'s surface, so `SKILL.md`
is updated in the same feature (FR-9): §"Audit prompt assembly" leads with it, the helper registry
gains an entry, and `test_h_mad_audit_cycle_docs.py` fails if the token drifts between script and
document. `SKILL.md` frontmatter `name`/`description` are unchanged and remain valid.

**Audit-gate signal discipline** (base) — complies. Every verdict exits 0; non-zero is reserved for
operational error; the `[H-MAD]` marker is emitted on every path. `GATE: INVALID`'s non-zero exit is
explicitly handled as a verdict rather than propagated as failure.

**Single-source contract** (base) — complies. Exactly one verdict formatter (`render`), reached by
both the normal and no-pass paths, so the token has one definition.

**No-plugin-dependency** (base) — complies. Stdlib-only Python and **bash** (`hmad-dispatch.sh`
is `#!/usr/bin/env bash` and already uses `local`, `[[`, `$(( ))` and array expansion at
`hmad-dispatch.sh:1921`), no new external dependency; `agy` was already required by the path this verb replaces.

**Operator-override preservation** (base) — complies. `--ack-file` is forwarded to every per-pass
gate, so the `## Acknowledged-not-fixed` escape works identically through the verb and by hand.

**Backward-compatibility** (base) — complies. Purely additive: no existing verb, script or flag
changes behaviour, and the hand-run step list stays in `SKILL.md` as the debugging path.

**Connection enforcement** (base) — complies. Six call sites, each with a test that fails when the
connection alone is removed with its callee intact, plus a genuine force-direction mutation. The
`report_wait` site additionally requires the delayed fixture to be reachable at all.

**Mutation verification** (base) — complies. Both specs run through `h_mad_mutation_harness.py`,
which refuses an anchor not matching exactly once, so an unlanded mutation cannot report a guard as
enforced. The two shell guards are covered alongside the Python ones.

**Assumption verification** (base) — complies. Three load-bearing assumptions were executed and
their observed output is cited in the plan's Architecture Considerations: `exec` shared-`--out`
behaviour, the concatenation under-count, and `GATE: INVALID`'s counts.

## Version History
- v1.22 (J36 correction, post-implementation). The Components Changed row for `h-mad/SKILL.md`
  carried spec AC-9.2's false measurement — "the report-file slot was measured **empty on 8 of 8
  impl-plan cycles**". The staged artifacts show the opposite: **17 of the 18** impl-plan audit
  passes delivered via the report file; only `cycle7_p1` wrote neither the file nor its `.done`
  marker, and its report was recovered from `--out`. Nine cycles, not eight, and the unit is the
  **pass**, not the cycle. Nothing downstream changes — the always-armed `--out` fallback is what a
  1-in-18 failure rate calls for too — which is exactly why a true conclusion resting on a false
  premise read as correct to every reviewer checking only that the conclusion followed. The v1.11
  entry below still quotes the old figure **deliberately**: it records what that audit cycle found
  at the time and is not rewritten. Spec v1.18, plan v1.12, impl-plan v1.9 carry the same fix.
- v1.21 (Phase-4 re-audit cycle 22 — **both passes gated clean, must=0 should=0**; one nit, raised
  independently by both). The nit was introduced by v1.20 one cycle earlier: the scenario column
  was updated to name all three channels while the verification column still said "both
  removed". Fixing one half of a pair and leaving the other stale, again. Re-gated at cycle 23
  rather than declaring PASS on a gate that never saw this edit.
- v1.20 (Phase-4 re-audit cycle 21 — 1 must-fix, 2 nits; **p1 gated clean**, so the sides flipped
  again). The must-fix was a genuine ambiguity: **two distinct guards are spelled
  `delivered != "none"`** — `combine()`:287 uses it as the qualifier on the operational-error
  raise, `main()`:434 uses it to decide whether to invoke `gate()` at all. The Test Plan row
  asserted the guard "lives in `main()`" while the `combine` code block showed one too, leaving
  the mutation anchor ambiguous. Both are now named explicitly at the row.
  Nit applied: `test_verb_clears_all_three_channels` scenario now names all three channels
  including the `.done` marker, matching its own name and AC-3.3.
  **Nit REFUTED — its prescription would have broken the shipped helper.** p1 read `--grace 5`
  in the Architecture Overview as contradicting `--report-grace` in the API section and asked
  for the full name everywhere. They are two different surfaces: `--report-grace` is the VERB's
  flag (API section, the verb's CLI) and `--grace` is the HELPER's own
  (`h_mad_audit_cycle.py:406`, and the Architecture Overview line is the HELPER invocation).
  The impl-plan already documents the mapping. Renaming the helper's flag would break shipped
  code and contradict the plan; recorded here so the next reviewer does not re-file it.
- v1.19 (Phase-4 re-audit cycle 20 — 1 must-fix, 1 should-fix; p2 gated clean). **A real defect in
  the SHIPPED helper, proven live**: `collected_path` is not covered by the pre-dispatch clearing
  (which touches only the `/tmp` stem), so on a re-run the previous run's report sits at that
  exact path and a silently-failed write leaves `exists()`/`st_size > 0` True on the OLD file —
  the stale report is scored as this run's. The helper now unlinks the destination immediately
  before writing. This also corrected v1.18's fixture, which reached the guard only with an
  empty destination: the write-failure test now requires a STALE file present as well, or it
  passes for the wrong reason and the mutation survives.
  Should-fix: `test_premise_items_match_gate_count` now runs against REAL collected reports as
  well as synthetic shapes, per `invariants.base.md` §"Reimplementation parity" ("AND against
  the real artifacts on disk") — synthetic fixtures only encode the author's own model of the
  format, and this repo holds 55+ real agent-produced reports to draw on.
- v1.18 (Phase-4 re-audit cycle 19 — 1 must-fix; p2 gated clean). **The finding was against a row
  v1.17 itself added**, and it was right: `test_collected_write_failure_is_operational_error`
  prescribed a read-only destination directory, but `_copy_collected_report` writes BEFORE it
  checks — `collected_path.write_bytes(...)` then `if not collected_path.exists() or ...`. A
  read-only parent therefore raises `PermissionError` at the write, never reaching the guard, so
  deleting the guard still crashes and the mutation SURVIVES while looking caught. The fixture
  now monkeypatches the write to a silent no-op, which is the only shape that reaches the guard.
  This is the third consecutive cycle in which a fix introduced the next cycle's finding
  (v1.15 -> the dangling mutation numbers and the stale "three rows"; v1.17 -> this). A guard's
  negative test must fail for the GUARD's reason, not merely fail.
- v1.17 (Phase-4 re-audit cycle 18 — 3 must-fix, 1 should-fix, 1 nit; the passes agreed on the
  two guard gaps and diverged on the rest). **Two of these are real COVERAGE gaps in already
  shipped code, not documentation gaps** — verified against the suite before applying:
  1. Nothing tests that `gate()`'s `len(findings) == must` assertion FIRES. Deleting the
     assertion survives a green 49-test suite, so the guard has no discrimination coverage.
  2. Nothing forces the `collected_path` re-read (`exists() and st_size > 0`) to fail —
     `chmod` appears 0 times in the suite, so no read-only-destination fixture exists. The
     shell's equivalent guard IS covered (`test_verb_unremovable_path`); the Python one is not.
  Both now have Test Plan rows, and both are owed as CODE in Phase 5 against the shipped
  helper — recorded rather than silently carried.
  Also added: the AC-2.4 assemble-non-zero-exit row (distinct guard from AC-2.5's absent
  token), and the rows for tests the design text cites but the table omitted
  (`test_verb_no_self_invocation`, `test_verb_writes_only_reports`, the `--phase`-before-
  clearing ordering test, the two premise-formatting tests, and
  `test_premise_items_match_gate_count`).
  Nit: "The three rows marked *anchors*" was wrong because **v1.15 added two more anchor
  rows and left the count** — the second time the errata edit introduced its own drift.
- v1.16 (Phase-4 RE-AUDIT of the v1.15 errata, cycle 17 — operator ruled the errata must be
  re-gated rather than accepted). Two findings, both real, and **the second was introduced by
  the v1.15 edit itself** — which is the case for re-gating rather than accepting errata:
  1. Must-fix (p1; p2 gated clean): the doc asserted BOTH that `premise_items` "does no parsing
     at all" and that it "deliberately mirrors the gate's prose fall-back, which makes it a
     reimplementation". The second is stale from before v1.9 moved extraction into `gate()`.
     The Test Strategy rationale now names `gate()`'s in-process read as the subject. The
     finding's prescription ("the test should be testing gate()") was ALREADY satisfied by the
     shipped test, which deletes the stub dir and runs the real gate — so this is a doc fix,
     not a code change.
  2. Nit (p2): the Test Plan rows added by v1.15 cited "connection mutation 2" and "mutation
     10" — numbers belonging to the impl-plan's 12-row table. This design carries no numbered
     mutation table and the plan's has 6 unnumbered rows, so both references dangled. They now
     name the guard and cite the impl-plan explicitly.
- v1.15 (errata, applied during Phase 5b — no design DECISION changed): three corrections of
  demonstrated fact, each measured during the impl-plan audit cycles.
  1. `gate()`'s `len(findings) == must` assertion is now explicitly ordered AFTER the `INVALID`
     short-circuit. Unordered, it crashes at exit 4 on a report with a populated `## Must-fix`
     and no `## Should-fix` — the exact input AC-10.4 requires to yield `UNVERIFIED` at exit 0.
  2. "POSIX shell" corrected to bash: `hmad-dispatch.sh` is `#!/usr/bin/env bash` with 212 bash
     constructs and an existing array expansion at `:1921`. The invariant's substance — no new
     external dependency — is unchanged and still holds.
  3. Test Plan: `test_combine_invalid_yields_unverified` renamed `test_main_...` (it asserts an
     end-to-end string, and a `test_combine_` prefix invites the unit-vs-`main()` confusion that
     produced a wrong mutation anchor), and the three anchor tests the impl-plan's connection
     mutations depend on are added — they were required by the mutation table and absent here.

- v1.0: Initial design draft.
- v1.1: Design-audit cycle-1 revisions (13 distinct must-fixes across two passes). The sharpest was
  self-contradiction: `gate` classified an absent `GATE:` token as an operational error while
  `combine` routed it to `UNVERIFIED`, which would exit 0 on a broken toolchain — `combine` now
  raises before any verdict forms, and `no_report:p<i>` / `no_gate_sections:p<i>` are mapped
  distinctly per AC-6.3. `--report-timeout` is **removed** rather than documented: this design has
  only a reap-first flow, so the flag reached no logic and a dead control invites tuning a timeout
  that cannot apply. Adds `size_status` worst-across-passes aggregation, the `reports:` and `note:`
  output lines (AC-4.4 and AC-5.4 are output requirements, not inferences), the complete helper
  invocation signature, and explicit coverage of AC-1.1/1.2/1.3/1.4/9.5.
- v1.2: Design-audit cycle-2 revisions (5 distinct). `collect` now copies to `collected_path` on
  **every** delivering branch — it previously returned the `/tmp` report path, so the `reports:`
  line would have named a file outside the audit directory that the next cycle's clearing deletes.
  `PassSpec` carried `log_path` while the CLI passed `collected`, leaving `collect` no destination.
  `--passes < 1` validation added: `K=0` runs zero dispatches and hands the helper no `--pass`,
  which is indistinguishable from the no-pass halt mode. The premise checklist is now explicitly
  omitted on `UNVERIFIED`. One finding argued the **spec** was wrong rather than the design, and was
  right — see spec v1.11.
- v1.3: Design-audit cycle-4 revisions (4 distinct, disjoint across passes). One was a **real logic
  bug introduced by the cycle-1 fix**: `combine` raised on `verdict is None` unqualified, but a pass
  that delivered nothing never reaches `gate()`, so its verdict is `None` benignly — every
  missing-report cycle would have crashed at exit 4 instead of returning `UNVERIFIED
  reason=no_report:p<i>` at exit 0. The check is now qualified by `delivered != "none"`. Also: the
  collected path leaves the `--pass` payload and is derived inside the helper, so the phase→audit-dir
  mapping has one home rather than two that can disagree; the no-pass form gains `--feature`, without
  which it cannot emit the `[H-MAD]` marker (AC-8.3); and the `h_mad_assemble_audit.py` call in the
  architecture block now carries its context arguments.
- v1.4: Design-audit cycle-5 revisions (2 distinct). `--timeout` was accepted by the verb's CLI and
  never forwarded to `exec agy` — an operator-supplied watchdog silently replaced by the default,
  which is the dead-flag defect that removed `--report-timeout` at v1.1, in the other direction.
  `--cd <project-root>` is forwarded on the same line. `collect()` gained `project_root`, without
  which it could not build the audit-directory path the surrounding text says it derives.
- v1.5: Design-audit cycle-6 revisions (4 findings from one pass; the other gated clean). Two were
  substantive. `premise_items` would have **re-implemented the gate's bullet parsing** — subtle
  rules (trailing space, `• ` from agy, stripped indentation) that a second implementation drifts
  from silently — and would have **ignored `--ack-file`**, re-surfacing findings the operator had
  cleared while the gate scored them away. It now imports the gate's own primitives and filters on
  the same acknowledged set. And `test_prose_plus_bullet_not_concatenated` is **exempted from the
  gate stub**: it exists to pin the real parser's under-count, and a stub can only prove the stub
  behaves as configured, so a future parser change would retire the guard while it still looked
  green. `render()` gained `feature` (needed for the marker) and `gate()` now returns the bullets
  that populate `PassResult.findings`, which previously had no defined origin.
- v1.6: Design-audit cycle-7 revisions (5 distinct, no overlap). The sharpest: `premise_items`
  looked only for bullets while the gate counts a **prose** block as one finding when a section has
  none — so a prose-only must-fix would have produced `GATE: FAIL must=1` beside a checklist of
  **zero** items, silently omitting exactly the finding shape this feature was designed around. It
  now mirrors the fall-back, and the helper asserts `len(items) == must` per pass rather than
  trusting the two extractors to agree. Collected writes are verified by re-reading. The no-pass
  form forwards `--passes` and `--project-root` unconditionally — `render()` prints `passes=K` and
  cannot count what was never dispatched. Spec AC-4.4 narrowed to PASS/FAIL with AC-4.4b for the
  UNVERIFIED omission.
- v1.7: Design-audit cycle-8 revisions (2 distinct). `test_premise_items_match_gate_count` — added
  one cycle earlier to verify the mirror — would itself have run against the **stub**, proving only
  that the mirror matches the fixture author's expectation while every real edge case went untested.
  It is now exempt, and the exemption is stated as a general rule: any test whose subject is the
  real gate's behaviour cannot use a stub. Also triages composed-script exit codes: each of the
  three has exactly one non-zero that means "nothing here", and a blanket policy in either
  direction either crashes on a normal fallback or lets a traceback read as `delivered=none`.
- v1.8: Design-audit cycle-9 revisions (3 distinct). Two were assumption-verification hits on the
  triage table written one cycle earlier — the exit codes were asserted, not measured. Probed:
  `report_wait` exits 1 on timeout, `extract_report` exits 2 for missing/empty/unsentinelled alike,
  which retires the feared crash-on-missing-`--out` path. The probe also surfaced something no
  finding asked for: step 1 accepted a non-empty report **without its `.done` marker**, so a torn
  write would have been gated as a complete report. Step 1 now requires the marker. Tests sandbox
  `--project-root` to a `tmp_path` so a crashed test cannot leave artifacts in the live docs tree.
- v1.9: Design-audit cycle-10 revisions (3 distinct). Applying the cycle-6 and cycle-7 fixes
  independently had re-created the very thing cycle 7 warned about: `gate()` returned the bullets
  *and* `premise_items` re-parsed them, leaving two extractors and an unresolved data model. There
  is now exactly one — `gate()` extracts (it already reads the file for the token), applies the
  prose fall-back, and asserts `len(findings) == must` on the pass it just gated; `premise_items`
  does no parsing at all and only formats. `--passes K` added to the full invocation, which claimed
  "nothing inferred" while omitting it. Spec AC-4.1 narrowed to require the `.done` marker.
- v1.10: Design-audit cycle-11 revision (1 finding; the other pass gated clean). The v1.9 wording
  claimed `gate()` "already reads the collected report to obtain the token, so it extracts in the
  same pass" — an **impossible data model**. The token comes from a *subprocess* that reads the file
  and prints to stdout; `gate()` sees only that stdout. Enumerating findings needs a second,
  independent read in the helper process. Both pathways are now described as such, "one extractor"
  is restated as "the second read happens in exactly one place", and the `len(findings) == must`
  assertion is framed as what binds the subprocess's count to the in-process enumeration.
- v1.11: Design-audit cycle-12 revisions (3 distinct; the other pass gated clean). Acknowledgement
  filtering was assigned to **two** owners: `gate()` must filter, or its `len(findings) == must`
  assertion raises on every cycle carrying an acknowledgement, yet `premise_items` also took an
  `acknowledged` set — which would have been dead code that reads as live. `gate()` owns it alone.
  The Test Plan had also dropped the three **positive** tests the plan's connection mutations remove
  against; a mutation with no failing test to catch it reports the connection enforced while the
  suite stays green. And AC-9.2's substance — the 8-of-8 measurement — was reduced to "§6.6
  correction", leaving the nature of the correction undefined.
- v1.12: Design-audit cycle-13 (1 must + 2 should from one pass; the other gated clean). The
  must-fix was a **self-contradiction inside spec AC-4.1**: the v1.14 edit added the `.done`
  requirement and left the superseded "only an empty or absent file" clause beside it, so the
  criterion described two different rules for one revision. Rewritten as an explicit two-branch
  rule (spec v1.15). Test Plan gains `test_verb_invalid_passes` (the `--passes < 1` guard had no
  anchoring test) and `test_main_invalid_yields_unverified` (AC-10.4 asks for the *cycle's*
  outcome on a header-less report, not just the gate's `INVALID` return).
- v1.13: Design-audit cycle-14 (2 must + 1 should from one pass; the other gated clean). The
  substantive one: the Test Strategy stubbed subprocesses **via `PATH`** while the helper resolves
  siblings `__file__`-relative — an absolute path bypasses `PATH`, so every "mocked" test would have
  silently run the real scripts and the mocked error paths would have been untested behind a green
  suite. Interception is now an explicit `HMAD_AUDIT_CYCLE_SCRIPT_DIR` override with a test pinning
  the default. `test_prose_plus_bullet_not_concatenated` now exercises the helper end-to-end rather
  than only proving the gate's under-count premise. The third finding's *facts* were wrong — it held
  that a `## Should-fix`-only report is a clean pass; probing showed the gate returns `INVALID` when
  **either** section is missing — but the wording mismatch it pointed at was real, fixed in spec
  v1.16 for the measured reason.
- v1.14: Design-audit cycle-15 (3 distinct; the other pass gated clean). A finding held that
  `h_mad_audit_gate.py` "resolves and reads a sidecar automatically" — source-checked false, it
  reads only the report's own `## Acknowledged-not-fixed` section plus an explicitly-passed
  `--ack-file`. The concern behind it was real: `gate()` must build its acknowledged set by calling
  **both** CLI functions, which parse differently, or an override from whichever source it missed
  fails the `len(findings) == must` assertion and crashes the cycle on a legitimate operator action.
  Spec AC-5.2 restated as explicit cannot-judge/FAIL/PASS precedence, and the AC-10.4 test now
  covers a report missing **only one** gate section, not just one missing both.
