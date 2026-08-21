# Spec: audit-cycle-verb

## Executive Summary

`hmad-dispatch audit-cycle` runs one complete h-mad audit cycle — assemble, two independent `exec
agy` passes, per-pass report collection with an automatic transport fallback, union gating, and a
premise-check checklist — and emits a single `AUDITCYCLE:` verdict token, exiting 0 on every
verdict.

## Goal

Replace the five-call hand-assembled audit cycle at Phases 3, 4 and 5b with one verb, so the steps
that make a cycle trustworthy (the transport fallback, the second pass, the premise check) cannot be
dropped by being forgotten.

## Functional Requirements

### FR-1: One verb, one cycle

- **Description**: `hmad-dispatch audit-cycle` performs exactly one audit cycle per invocation and
  returns. It never re-dispatches after a FAIL and never authors a document revision.
- **Acceptance Criteria**:
  - AC-1.1: `hmad-dispatch audit-cycle --feature <f> --phase plan|design|impl-plan --cycle <N>
    --project-root <p>` runs to a verdict and exits without re-invoking itself.
  - AC-1.2: On a FAIL verdict the verb makes no further `exec agy` dispatch — asserted by counting
    dispatch invocations in a stubbed run.
  - AC-1.3: The verb writes no file under `docs/01-plan/` or `docs/02-design/` other than the
    per-pass audit report files named in FR-4.
  - AC-1.4: An unknown or missing `--phase` value is rejected before any dispatch, with a non-zero
    exit and no `AUDITCYCLE:` line (an operational error, not a verdict).

### FR-2: Assembly is gated, and its size signal is relayed

- **Description**: The verb calls `h_mad_assemble_audit.py` and refuses to dispatch a prompt that
  did not assemble cleanly.
- **Acceptance Criteria**:
  - AC-2.1: The verb takes its **verdict** from the `ASSEMBLE:` token on stdout and dispatches only
    on `ASSEMBLE: PASS`. It never derives a verdict from the script's exit code — a `HALT` and a
    `PASS` both exit 0, so the exit code cannot distinguish them. (Exit code is still read, for the
    orthogonal question in AC-2.4; the two are separate reads and are not in conflict.)
  - AC-2.2: On `ASSEMBLE: HALT` from **any** pass, the verb emits `AUDITCYCLE: UNVERIFIED
    reason=assemble_halt:p<i>` naming the first halting pass, carrying **no** `must=`/`should=`
    fields, and exits 0. **No pass is dispatched** — every pass assembles before any dispatch, so a
    partial cycle cannot occur; dispatching only the passes that assembled would gate a `--passes 2`
    cycle on one pass while reporting `passes=2`.
  - AC-2.3: The `size_status=` field is echoed on the verb's own output so an `unverified` size is
    visible without re-running assemble. With multiple passes the **worst** value across them is
    reported (`unverified` if any pass reported it) — the field exists to surface an unverified
    size, so any aggregation that could hide one defeats it.
  - AC-2.4: A non-zero exit from `h_mad_assemble_audit.py` (unreadable inputs) is an **operational
    error**, not a verdict: the verb exits non-zero and emits no `AUDITCYCLE:` line. Exit code and
    token answer different questions — *did the script run at all* versus *what did it decide* — and
    the verb reads both. What it must never do is treat a non-zero exit as a FAIL verdict, or an
    absent token as a PASS.
  - AC-2.5: An exit of 0 with **no** `ASSEMBLE:` token on stdout is treated as an operational error
    (AC-2.4's path), never as a PASS. A missing token is the one case where silence would otherwise
    read as consent.

### FR-3: Two independent passes, isolated per-pass channels

- **Description**: The verb dispatches `exec agy` twice on prompts assembled per pass and asserted
  byte-identical apart from the report path (AC-3.4), with per-pass output paths so neither pass can
  overwrite the other (J29).
- **Acceptance Criteria**:
  - AC-3.1: Default pass count is 2. `--passes 1` runs one pass; `--passes N` for N<1 is rejected
    as an operational error.
  - AC-3.2: Each pass receives a distinct `--out` and a distinct `--log` path, both carrying the
    pass index (e.g. `…_p1.txt` / `…_p2.txt`). No two passes in one invocation share either path.
  - AC-3.3: Each pass receives a distinct report-file path carrying the pass index, and the verb
    removes any pre-existing `<report-path>`, `<report-path>.done` **and `<out-path>`** before
    dispatching that pass, asserting each removal landed by re-reading. Clearing `--out` is not
    symmetry for its own sake: the paths are deterministic per feature/phase/cycle/pass, so a re-run
    reuses them, and a dispatch that dies before writing leaves `exec`'s overwrite guard unfired —
    the stale file is unchanged since that dispatch began, which is precisely the case the guard
    permits overwriting. The fallback would then extract the previous run's report, correctly
    sentinelled for this same feature/phase/cycle and indistinguishable from a real delivery.
  - AC-3.3b: `--log` is not cleared. It appends by design, is never scored, and its cross-run
    history is the diagnostic for the crash case AC-3.3 guards against.
  - AC-3.4: Assembly runs once **per pass**, and the verb asserts the resulting prompts are
    byte-identical except for the single line carrying that pass's `--report-file` path. (Revised
    in v1.1: the report path is substituted into the prompt *body* at assembly time, so a single
    shared prompt file and per-pass report-file isolation (AC-3.3) are mutually exclusive. The
    guarantee that matters — one preflight, one size check, one sentinel per cycle — is preserved by
    the byte-identical assertion.)
  - AC-3.5: A pass's non-zero `exec` exit code does not by itself fail the cycle; the verdict comes
    from that pass's report collection (FR-4) and gate result (FR-5).

### FR-4: Report collection tries report-file, falls back to `--out`

- **Description**: For each pass the verb first waits on the report-file slot, then falls back to
  extracting a sentinel-framed report from that pass's `--out`.
- **Acceptance Criteria**:
  - AC-4.1: The verb **reaps each backgrounded dispatch first**, then decides per pass from the
    report path:
    - non-empty **and** `<report-path>.done` exists → `delivered=report-file`, **no wait at all**;
    - anything else — absent, empty, or non-empty with no `.done` — → `h_mad_report_wait.py
      <report-path>` with a **grace** timeout (`--report-grace`, default 5s), never a full wait.

    The `.done` requirement is why the second branch is not simply "empty or absent": the agent
    writes the report and *then* marks `.done`, so a non-empty report without the marker is a torn
    write caught mid-flush, and accepting it on size alone would gate a truncated report (typically
    `GATE: INVALID`, its `## Should-fix` section not yet written). `report_wait` blocks on exactly
    that marker — probed 2026-08-20: a present file with no `.done` times out at exit 1, identically
    to a file that never arrived.

    Reap-first, and a grace rather than a full wait, because `report_wait` polls a path and knows
    nothing about a process: *both* naive orderings can hang for the full timeout — collecting
    before reaping hangs when a dispatch dies without writing, and reaping then waiting fully hangs
    when the agent delivered via `--out`. Once a dispatch has exited, no longer wait can change the
    outcome. (Revised v1.3 to reap-first; narrowed v1.14 to require `.done`; the superseded "only an
    empty or absent file" clause removed v1.15, where it had survived alongside its own replacement.)
  - AC-4.1b: `--report-timeout` is **not offered**. The reap-first flow is the only collection path,
    so the flag would reach no logic; a control that silently does nothing reads as supported and
    invites tuning a timeout that cannot apply. The collection bound is the dispatch's own
    `--timeout` plus `--report-grace`. (Inverted in v1.10: previously retained "for a future
    non-blocking mode", which the design showed was a flag with no reachable logic.)
  - AC-4.2: When `report_wait` times out **or** delivers an empty body, the verb falls back to
    `h_mad_extract_report.py <out-path> --feature <f> --phase <p> --cycle <N> --after-marker`.
  - AC-4.3: The fallback extraction passes `--after-marker`, so an echoed prompt containing the
    template's own sentinel pair cannot be scored as the agent's report.
  - AC-4.4: Each pass's collected report is written to
    `<audit-dir>/<feature>.<phase>.audit.v<N>.p<i>.md`, and on a **PASS or FAIL** verdict the paths
    are named on the verb's output via a `reports:` line. The write is verified by re-reading
    (exists and non-empty) before the pass is recorded as delivered.
  - AC-4.4b: On `UNVERIFIED` the `reports:` line is omitted, including when some passes did deliver.
    Naming a partial set of reports on a cannot-judge cycle presents them as the cycle's result,
    which is the claim `UNVERIFIED` exists to withhold. (Narrowed in v1.13.)
  - AC-4.5: The verb reports the delivering channel per pass as `delivered=report-file|out|none`,
    so the report-file failure rate remains measurable across cycles.
  - AC-4.6: A pass whose report is empty or absent on **both** channels is recorded as
    `delivered=none` and routed to FR-6's cannot-judge path — never scored as zero findings.

### FR-5: Union gating by per-pass gate runs, never by concatenation

- **Description**: Each pass's report is gated separately with `h_mad_audit_gate.py`; the cycle
  verdict is PASS only if every pass gated PASS.
- **Acceptance Criteria**:
  - AC-5.1: `h_mad_audit_gate.py` is invoked once per collected pass report, on that pass's own
    file. The verb never concatenates two pass reports into one file and gates the concatenation.
  - AC-5.2: Verdict precedence is **cannot-judge, then FAIL, then PASS**. If any pass is a
    cannot-judge (`delivered=none` or `GATE: INVALID`) the cycle is `UNVERIFIED` regardless of the
    other passes; otherwise, if any pass returned `GATE: FAIL` the cycle is `FAIL`; otherwise every
    pass returned `GATE: PASS` and the cycle is `PASS`. (Narrowed in v1.17: this previously said
    FAIL follows unconditionally from any `GATE: FAIL`, which contradicted AC-6.1 — a cycle where
    one pass measured nothing is not a cycle that found problems, and reporting FAIL would let a
    re-run "fix" it by chance.)
  - AC-5.3: Per-pass counts appear on the verdict output as `p<i>=<must>/<should>` for each pass.
  - AC-5.4: The aggregate `must=`/`should=` fields are the **sums** of the per-pass counts, and the
    verb's output states that the sum may double-count a finding both passes reported.
  - AC-5.5: The verb takes each pass's **verdict** from that gate run's `GATE:` token on stdout and
    never derives a verdict from the gate's exit code. The gate emits three verdicts across two exit
    codes, so exit code alone cannot route them:

    | gate output | exit | the verb's routing |
    |---|---|---|
    | `GATE: PASS must=0 should=0` | 0 | pass gated clean |
    | `GATE: FAIL must=N should=M` | 0 | cycle FAIL (AC-5.2) |
    | `GATE: INVALID must=0 should=0` | 2 | cannot-judge → `no_gate_sections:p<i>` (AC-5.6) |
    | no `GATE:` token at all | any | operational error (AC-2.5) |

  - AC-5.6: A pass report lacking both `## Must-fix` and `## Should-fix` headers is refused rather
    than scored. The gate already detects this and returns `GATE: INVALID` (verified 2026-08-20 on
    both a narration-only report and an empty file), so the verb composes it unmodified and routes
    on the token. **`GATE: INVALID` carries `must=0 should=0`** — counts it did not measure — so the
    verb MUST key on the verdict word and MUST NOT read those counts. The pass routes to the
    cannot-judge verdict with `reason=no_gate_sections:p<i>`, and its `delivered=` value is left
    **as measured** (`report-file` or `out`). (Revised in v1.11: this previously said the pass
    "becomes `delivered=none`", which would have made `no_gate_sections` unreachable — `combine`
    tests `delivered == "none"` first, so `no_report:p<i>` would always win and AC-6.3's distinction
    would be dead code. Something that arrived but could not be scored is not the same event as
    nothing arriving, and the operator responses differ: inspect the report versus re-dispatch.)
  - AC-5.7: `--ack-file <path>`, when passed, is forwarded to every per-pass gate invocation, so the
    operator escape hatch works identically to a hand-run cycle.

> **Why concatenation is forbidden (AC-5.1).** `h_mad_audit_gate.classify` accumulates content
> across repeated `## Must-fix` headers, so a concatenated file *looks* like a correct union. But
> `_count_section_findings` returns `len(bullets)` whenever any bullet is present and only falls
> back to the prose/numbered/blockquote fail-safe when there are **none**. Concatenating a
> prose-finding report with a bulleted one therefore silently drops the prose finding — an
> **under**-count, the unsafe direction. Per-pass gating has no such interaction.

### FR-6: Cannot-judge is a distinct verdict carrying no counts

- **Description**: A cycle that measured nothing is not a passing cycle.
- **Acceptance Criteria**:
  - AC-6.1: If any pass ends `delivered=none`, the cycle verdict is `AUDITCYCLE: UNVERIFIED` with a
    `reason=` field, and the line carries **no** `must=` or `should=` field.
  - AC-6.2: `UNVERIFIED` exits 0, matching every other h-mad verdict; only operational errors
    (unreadable inputs, bad arguments) exit non-zero.
  - AC-6.3: The `reason=` value distinguishes at minimum `assemble_halt`, `prompt_divergence`
    (the per-pass prompts differed beyond the report-path line, so the passes would audit different
    documents — a cannot-judge verdict at exit 0, never an operational error), `no_report:p<i>`, and
    `no_gate_sections:p<i>`.
  - AC-6.4: On a **post-dispatch** `UNVERIFIED`, the per-pass `delivered=` fields are still printed,
    so the operator can see which pass failed and on which channel.
  - AC-6.4b: A **pre-dispatch** `UNVERIFIED` — `reason=assemble_halt:p<i>` or
    `reason=prompt_divergence` — prints no `delivered=` fields, because no dispatch occurred and no
    collection channel exists to report on. Printing `delivered=none,none` there would be a
    measurement the cycle never took, the same defect as a cannot-judge carrying counts (AC-6.1).
    (Added in v1.12: AC-6.4 was written unconditionally before the no-pass halt path existed.)

### FR-7: Premise-check checklist

- **Description**: Every must-fix bullet carrying a source citation is printed as an unchecked
  item for the orchestrator to verify against source before acting.
- **Acceptance Criteria**:
  - AC-7.1: The verb extracts `path:line` citations from the `## Must-fix` bullets of every
    collected pass report and prints one unchecked checklist item per citing bullet.
  - AC-7.2: Each checklist item names the pass it came from and the cited `path:line`.
  - AC-7.3: A must-fix bullet with **no** citation is listed too, marked `(no citation)`, so an
    uncitable finding is visible rather than silently omitted.
  - AC-7.4: The verb does **not** open, read, or validate the cited files. Whether the code means
    what the finding claims is not adjudicated here.
  - AC-7.5: The checklist is emitted on a FAIL verdict. On PASS there are no must-fix bullets, so
    the checklist is empty and the verb says so on one line rather than printing nothing.

### FR-8: Verdict line and signal discipline

- **Description**: One canonical machine-readable line per invocation.
- **Acceptance Criteria**:
  - AC-8.1: The verdict line matches `AUDITCYCLE: (PASS|FAIL) must=<N> should=<M> passes=<K>` with
    per-pass `p<i>=<must>/<should>` and `delivered=` fields, or
    `AUDITCYCLE: UNVERIFIED reason=<r>` with no counts.
  - AC-8.2: Every verdict exits 0. A non-zero exit means an operational error and is accompanied by
    no `AUDITCYCLE:` line.
  - AC-8.3: The verb emits an `[H-MAD] <feature> audit-cycle <verdict>` marker line.
  - AC-8.4: The verdict line is the only `AUDITCYCLE:`-prefixed line on stdout, so a consumer
    reading the last match and a consumer reading the first read the same thing.

### FR-9: Documentation, including the report-file correction

- **Description**: `h-mad/SKILL.md` leads with the verb, and its report-file claim is reconciled
  with the measurement that contradicts it.
- **Acceptance Criteria**:
  - AC-9.1: §"Audit prompt assembly" presents `hmad-dispatch audit-cycle` as the way to run a
    cycle, with the existing hand-run step list retained as the debugging/fallback path.
  - AC-9.2: The report-file guidance at §6.6 (`h-mad/SKILL.md:1419`, "preferred under Orca") is
    amended to record the measured delivery rate — across the 18 impl-plan audit passes, 17
    delivered via the report file and 1 (cycle 7 pass 1) wrote neither the file nor the `.done`
    marker and was recovered from `--out` — and that the verb therefore always arms the `--out`
    fallback.
  - AC-9.3: The `AUDITCYCLE:` token is listed in SKILL.md's helper/verb registry alongside the other
    verdict tokens.
  - AC-9.4: A bidirectional docs test asserts the `AUDITCYCLE:` token appears in both the
    implementation and SKILL.md, failing if either drops it.
  - AC-9.5: SKILL.md states that `audit-cycle` runs one cycle and that the revision loop remains the
    orchestrator's.

### FR-10: Tests

- **Description**: The verb is covered without requiring a live `agy`.
- **Acceptance Criteria**:
  - AC-10.1: Tests stub the `exec agy` dispatch so the whole cycle runs offline, with no network
    and no live agent.
  - AC-10.2: A test covers each `delivered=` value — `report-file`, `out`, and `none`.
  - AC-10.2b: A **delayed-delivery** test covers `report-file` arriving *after* the grace wait
    begins (fixture creates the file ~1s in). Without it the `report_wait` call site is never on the
    executed path — the reap-first flow bypasses the wait whenever the file is already present, which
    is how a successful delivery is normally mocked — so its connection mutation would survive while
    reporting the connection as enforced.
  - AC-10.2c: A test asserts the converse: when the report file is already present at reap time,
    `h_mad_report_wait.py` is **not** invoked at all.
  - AC-10.3: A test asserts AC-5.1's motivating case directly: a pass report whose only finding is
    prose (no bullet) combined with a bulleted pass report yields `FAIL` with that prose finding
    counted, which a concatenation-based implementation fails.
  - AC-10.4: A test asserts that a report **missing either gate section** yields `UNVERIFIED` at the
    cycle level, not `PASS`. Probed 2026-08-20: `has_gate_sections` requires **both** `## Must-fix`
    and `## Should-fix`, so a report carrying only one of them gates `INVALID` exactly as a report
    carrying neither does — `## Should-fix`-only is *not* a clean pass. The test asserts the cycle's
    `AUDITCYCLE: UNVERIFIED reason=no_gate_sections:p<i>`, not merely the gate's `INVALID` return,
    since the AC is about the cycle's outcome. (Reworded in v1.16 from "a `## Must-fix`-less
    report", which implied the missing section had to be that one.)
  - AC-10.5: A mutation spec exists for the gating logic, and every mutation is caught (guard
    mutated to its permissive value → a test fails).
  - AC-10.5b: The spec covers the **shell-level** guards as well as the Python ones — the
    post-removal `[ ! -e "$path" ]` assertion and the per-pass prompt byte-identity assertion. Each
    has a fixture that creates the condition it guards (an unremovable path; a plan edited between
    the two assemblies), because a permissive mutation is invisible against inputs that never trip
    the guard.

## Non-Functional Requirements

- **Performance**: Two passes dispatch concurrently, so wall-clock for `--passes 2` is
  approximately one pass plus collection overhead, not two passes serially.
- **Security**: N/A — no new network surface; the verb shells out to the same scripts and the same
  `agy` CLI the hand-run path already uses.
- **Compatibility**: Stdlib-only Python and POSIX shell, consistent with the rest of `h-mad`. No new
  external dependency. Existing hand-run cycles keep working unchanged; the verb is additive.

## Out-of-Scope

- **Looping until `GATE: PASS`.** Advancing a cycle requires revising the audited document, which is
  authoring judgment. The orchestrator keeps the loop.
- **Automated premise adjudication.** The verb does not open cited files. Hard-failing on a
  citation that does not resolve (file absent, line past EOF) is deferred until the checklist's
  output shape has settled in use.
- **Phase 5b's `WIREPIN:` gate.** That is a separate check on the same document and is not folded
  into this verb. SKILL.md's 5b step continues to call it separately.
- **Union deduplication.** Aggregate counts may double-count a finding both passes reported. This is
  safe in the gating direction (it can never turn a FAIL into a PASS) and per-pass counts are
  reported alongside, so the inflation is visible.
- **Replacing the hand-run step list in SKILL.md.** It is retained as the debugging path for when
  the verb itself is suspect.
- **Any change to `h_mad_assemble_audit.py`, `h_mad_audit_gate.py`, `h_mad_extract_report.py`, or
  `h_mad_report_wait.py`.** The verb composes them as they are.

## Assumptions

- `agy` is on PATH. The verb uses `exec`, which is pane-independent, so a `PREFLIGHT: FAIL
  unresolved=codex,agy` does not block it.
- `hmad-dispatch exec` appends the `===HMAD-DISPATCH-BOUNDARY===` line, which AC-4.3's
  `--after-marker` relies on.
- `h_mad_audit_gate.classify` continues to accumulate across repeated section headers and to apply
  the prose fail-safe only in the absence of bullets. AC-10.3 pins the behaviour this spec depends
  on, so a future change to the gate breaks a test rather than the verb silently.
- The audit report directory is `docs/01-plan/features/` for `plan` and `impl-plan` phases and
  `docs/02-design/features/` for `design`, matching the existing hand-run redirects.

## Version History

- v1.0: Initial specification draft.
- v1.1: AC-3.4 corrected — assembly runs once per pass, not once per cycle, because the report-file
  path is substituted into the prompt body and therefore cannot be shared across passes that require
  isolated report files. Found by hand-running this feature's own Phase-3 audit cycle.
- v1.2: AC-2.1, AC-2.4 and AC-5.5 reworded to remove a real contradiction found in plan-audit cycle
  2 — "never branches on the exit code" read as forbidding the operational-error read that AC-2.4
  requires. Exit code and token answer different questions and the verb reads both; what it must
  never do is derive a *verdict* from an exit code. New AC-2.5 closes the third case: exit 0 with no
  token is an operational error, never a PASS.
- v1.3: AC-4.1 rewritten and AC-4.1b added, reconciling the spec with the plan's reap-first
  collection order. Both plan-audit cycle-4 passes flagged the divergence independently — the plan
  had narrowed a 600s wait to a 5s post-reap grace without the spec following.
- v1.4: AC-5.5 rewritten as a three-verdict routing table and AC-5.6 grounded in a live probe.
  `GATE: INVALID` (exit 2) is a cannot-judge, not an operational error, and it carries counts it did
  not measure — the previous wording would have routed it to the error path, and a counts-reading
  consumer would have scored it a clean pass.
- v1.5: AC-6.3 gains `prompt_divergence`, classified as a cannot-judge verdict at exit 0.
- v1.6: AC-3.3 extended to clear `<out-path>` as well as the report paths, with AC-3.3b recording
  why `--log` is deliberately exempt.
- v1.18: AC-9.2's measurement corrected (J36). It stated the report-file slot was measured "empty
  on 8 of 8 impl-plan cycles"; the staged artifacts show the opposite — **17 of the 18 impl-plan
  audit passes delivered** via the report file (present, non-empty, `.done` written), and only
  `cycle7_p1` fell back to `--out`. The old count was wrong twice over: there were **9** cycles,
  not 8, and the measurement is per **pass**, not per cycle. The conclusion it justifies — always
  arm the `--out` fallback — is unchanged, and the real 1-in-18 rate supports it just as well; only
  the stated evidence was false, which is why the claim survived three gates. Re-verified from
  `/tmp/audit_audit-cycle-verb_impl-plan_cycle{1..9}_p{1,2}.report.md` before correcting.
- v1.17: AC-5.2 restated as an explicit three-way precedence so it no longer contradicts AC-6.1.
- v1.16: AC-10.4 reworded to "missing either gate section". An audit finding argued a
  `## Should-fix`-only report is a clean pass needing `PASS`; probing the gate disproved that — it
  returns `INVALID` for either section missing. The wording mismatch was real, the stated reason was
  not.
- v1.15: AC-4.1 rewritten as a two-branch rule. The v1.14 edit added the `.done` requirement but
  left the superseded "only an empty or absent file" clause in the same criterion, so AC-4.1
  contradicted itself for one revision.
- v1.14: AC-4.1 requires the `.done` marker, closing a torn-write window found by probe.
- v1.13: AC-4.4 scoped to PASS/FAIL with AC-4.4b covering the UNVERIFIED omission, and the collected
  write is now verified by re-reading.
- v1.12: AC-6.4 scoped to post-dispatch UNVERIFIED; AC-6.4b covers the pre-dispatch halts, which
  have no channels to report and must not print invented ones.
- v1.11: AC-5.6 corrected — an INVALID pass keeps its measured `delivered=` value instead of being
  forced to `none`, which would have made `no_gate_sections:p<i>` unreachable. Found by a design
  audit that argued the spec was wrong and the design right.
- v1.10: AC-4.1b inverted — `--report-timeout` removed, not retained; no logic reaches it.
- v1.9: AC-10.5b added — the two shell-level guards get discrimination coverage with
  condition-creating fixtures.
- v1.8: AC-2.2 and AC-2.3 made multi-pass aware — assembly runs per pass, so there are N tokens and
  N size_status values. Any HALT stops the whole cycle before any dispatch, and the worst
  size_status is the one reported.
- v1.7: AC-10.2b/10.2c added — a delayed-delivery fixture so the `report_wait` call site is on the
  executed path, and its converse (file present ⇒ wait never invoked).
