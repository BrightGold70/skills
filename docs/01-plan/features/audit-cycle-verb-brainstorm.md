# Brainstorm: audit-cycle-verb

## Executive Summary

Collapse the five-script audit cycle that h-mad runs at Phases 3, 4 and 5b into one
`hmad-dispatch audit-cycle` verb that dispatches two independent agy passes, gates on the union of
their findings, and emits a premise-check list — closing the five highest-recurrence rows in the
skill-candidate backlog (recurrences 18, 13, 10, 10, 9).

## Problem Statement

Every audit cycle is hand-assembled from five separate calls — `h_mad_assemble_audit.py`,
`hmad-dispatch exec agy`, `report-wait`, `h_mad_extract_report.py`, `h_mad_audit_gate.py` — plus the
fallback and token reads between them. All five parts exist; nothing wires them. The backlog
records this shape being retyped **18 times in one session** (`HemaSuite:268`), **10 more**
(`HemaSuite:346`), and **20+** in terminal mode (`skills:203`), and every hand-run is an opportunity
to drop the step that makes the cycle trustworthy: the fallback when the report file comes back
empty, the second pass, or the premise check.

## Proposed Approach

A single `hmad-dispatch audit-cycle` verb, **one cycle per call**, that performs:

1. `h_mad_assemble_audit.py` — assert `ASSEMBLE: PASS`, relay `size_status=`.
2. Dispatch **two independent `exec agy` passes** on the same assembled prompt, concurrently, each
   to its own `--out` and `--log`.
3. Collect each pass's report: **try the report-file slot, fall back to `--out` +
   `h_mad_extract_report.py`** when it comes back empty or times out. Record which channel
   delivered, per pass.
4. `h_mad_audit_gate.py` on the **union** of the two passes' `## Must-fix` + `## Should-fix`
   bullets.
5. Emit a **premise-check list**: every must-fix bullet carrying a `file:line` citation, printed
   unchecked, for the orchestrator to verify against source before acting.
6. Print one verdict line — `AUDITCYCLE: PASS|FAIL must=N should=M passes=2 delivered=<channels>` —
   and exit 0 on any verdict, per the audit-gate signal discipline.

The loop stays with the orchestrator, because advancing a cycle means *revising the audited
document*, which is authoring judgment the verb cannot hold.

### Four decisions, settled at brainstorm

- **Transport: try report-file, fall back to `--out`.** This is what the rec-18 row describes
  doing. It preserves the preferred-under-Orca path while making the fallback automatic. The verb
  reports the delivering channel per pass, so the measurement that motivated this keeps accruing.
- **Passes: 2 by default, union-gated; `--passes 1` opts out.** `HemaSuite:403` measured the two
  passes disagreeing on **every one of 10 cycles**, and on one cycle each found a real must-fix the
  other missed — either alone would have shipped one. A single-pass default is the unsafe gate the
  measurement names.
- **Premise check: emit a checklist, do not adjudicate.** A script can see that a citation
  resolves; it cannot see whether the code *means* what the finding claims. The rec-13 row is about
  the second thing. Printing an unchecked list is honest about the boundary; a green automated
  premise-check on a wrong premise would be worse than no check.
- **One cycle per call.** A self-looping verb would either author the revision itself or re-dispatch
  an unchanged document — the second re-audits identical input and burns cycles for nothing.

## Alternatives Considered

- **Loop until `GATE: PASS` inside the verb**: rejected — advancing requires authoring the doc
  revision, which is judgment; a loop over unchanged input is a no-op that looks like progress.
- **`--out` scrape only, drop report-file**: rejected — the 8/8-empty measurement is scoped to
  impl-plan cycles, and report-file delivered cleanly on other phases (a 2.9 KB sentinel report on
  the same feature's cycle 1). Discarding a channel on a phase-scoped failure over-corrects.
- **Flag-controlled transport with no default**: rejected — pushing the decision back to the caller
  every cycle is precisely the hand-run cost this verb removes.
- **Single pass by default**: rejected — see the union measurement above. A default nobody changes
  *is* the behaviour.
- **Fully automated premise check (script hard-fails on an unresolvable citation)**: rejected as the
  primary mechanism, but see Open Questions — the existence half may be worth adding later, once the
  checklist half has shipped and its output shape is settled.
- **A Python script rather than a `hmad-dispatch` verb**: rejected — every part it orchestrates is
  already reached through `hmad-dispatch`, and the verb inherits its substrate detection, receipt
  enforcement, and `--log`/`progress` observability for free.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Two concurrent `exec agy` passes share one `--out` and the second clobbers the first (J29) | M | Template `--out`/`--log` per pass (`…_p1`, `…_p2`); `exec`'s existing overwrite refusal is the backstop, not the plan |
| The union double-counts a finding both passes report | H | Union is over bullets, and the gate counts bullets — a duplicated must-fix inflates `must=` but never turns a FAIL into a PASS. Report the per-pass counts alongside the union so the inflation is visible |
| A pass returns no extractable report; the verb scores the cycle on one pass silently | M | A pass that delivers nothing on **both** channels is a cannot-judge, not a zero. Verdict becomes `AUDITCYCLE: UNVERIFIED` carrying **no counts**, matching every other h-mad cannot-judge |
| Premise-check list is emitted and nobody reads it | M | It is part of the verdict output, not a side file; a FAIL with unchecked premises says so on the token line |
| `PREFLIGHT: FAIL unresolved=codex,agy` in this repo blocks live-fire | H | `exec` is pane-independent and both CLIs are on PATH; the verb never uses `send`. Live-fire is unblocked — verified at bootstrap |
| The verb is built and the SKILL.md audit-prompt-assembly section still prescribes the hand-run steps | H | Updating §"Audit prompt assembly" to lead with the verb is part of the feature, not a follow-up |
| Editing `hmad-dispatch.sh` while another h-mad run is in flight | L | The skills symlink makes the working tree the live skill — build on a feature branch per §"Editing this skill while a run is in flight" |

## Dependencies

None external. Every part is already in `h-mad/scripts/`: `h_mad_assemble_audit.py`,
`h_mad_extract_report.py`, `h_mad_audit_gate.py`, `h_mad_report_wait.py`, and the `exec` verb in
`hmad-dispatch.sh`. `agy` and `codex` are both on PATH (verified at bootstrap).

## Open Questions

- **Does the union need dedup, or is bullet-count inflation acceptable?** Inflation is safe in the
  gating direction but makes `must=` a poor progress signal across cycles. Defer to the spec: it may
  be enough to report `must=` per pass *and* as a union.
- **Should the premise-check list hard-fail on a citation that does not resolve** (file absent, line
  past EOF)? Deferred deliberately — ship the checklist, then decide whether the existence half is
  worth a second verdict once the output shape is settled.
- **What does the verb do at Phase 5b, where the wire-pin gate also runs?** 5b's `WIREPIN:` gate is
  a separate check on the same document. Likely out of scope — but the spec should say so rather
  than leave it ambiguous.
- **Correcting `h-mad/SKILL.md:1419`** ("report-file … preferred under Orca") against the 8/8-empty
  measurement: in scope for this feature, or a separate docs fix? Leaning in-scope, since the verb's
  transport default is the operative statement either way.

## Version History

- v1.0: Initial brainstorm draft.
