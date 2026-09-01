# Spec: pin-agents-tail-banner

## Executive Summary

Add a standalone tail-evidence pass to `_orca_find`, between Pass 2 and Pass 3, reading a candidate pane's
`.result.terminal.tail` and resolves an agent when — and only when — exactly one candidate
carries that agent's launch signature.

## Goal

Recover a correct agent handle in the case every existing pass fails: a live pane whose
title is inherited and whose preview banner has decayed, which today reports `UNRESOLVED`
and forces a manual `pin`.

## Measured basis

Two measurements taken 2026-09-01 before this spec; both are load-bearing and one falsified
the brainstorm's stronger claim.

1. **Identity survives on real agent panes.** Three panes alive since 2026-08-31 — one
   codex (the pinned dispatch target) and two agy — each retain 12–18 tail lines carrying
   both the launch command (`codex '--dangerously-bypass-approvals-and-sandbox'`,
   `agy '--dangerously-skip-permissions'`) and the vendor banner (`OpenAI Codex` / `gpt-5`,
   `Antigravity`).
2. **Tail retention is hard-capped at 2000 lines**, regardless of `--limit`. A disposable
   pane emitting 200 lines retained 203 and kept its first line; one emitting 2000 retained
   exactly 2000 and lost it; one emitting 20000 retained 2000 beginning at line 18001.

These reconcile because agents are full-screen TUIs on the alternate screen buffer, so
their output never enters normal-buffer scrollback — which is why a pane dispatched to for
two days still holds 18 lines. The retention cap is therefore **real but not normally
reached by an agent pane**. It IS reached by a pane where the agent exited and the operator
used the shell for more than 2000 lines; there the signature is gone and this pass must
decline. That is the accepted limit of the feature, stated rather than discovered later.

## Functional Requirements

### FR-1: Tail evidence resolves an otherwise-unresolvable agent
- **Description**: A pass between Pass 2 and Pass 3 reads each unresolved candidate's tail
  and matches the EXISTING `_agent_pv_re` signature. It is gated on neither Pass 2's
  `n == 0` condition nor Pass 3's `lsof` precondition, so it covers an ambiguous title and a
  machine with no `lsof` — neither of which any current pass reaches.
- **Acceptance Criteria**:
  - AC-1.1: Given a candidate pool of one pane whose tail contains the agent's launch
    command and no other pane's, `_orca_find <agent>` prints that handle and returns 0.
  - AC-1.2: Given a pane whose tail carries the vendor banner but not the launch command,
    resolution still succeeds — both forms are accepted signatures.
  - AC-1.3: `hmad-dispatch env` reports the resolved handle rather than `UNRESOLVED` for a
    pane that only the tail pass can identify.

### FR-2: The pass resolves only on exactly one match
- **Description**: Zero or more than one matching candidate declines, leaving the agent
  unresolved.
- **Acceptance Criteria**:
  - AC-2.1: Two candidates whose tails both match the agent → the pass declines (rc 1) and
    prints no handle.
  - AC-2.2: Zero matching candidates → declines (rc 1), no handle.
  - AC-2.3: A candidate whose tail carries the RIVAL agent's signature is rejected before
    counting, so it can neither be selected nor create a false ambiguity.

### FR-3: The tail read runs only when the earlier passes did not settle it
- **Description**: A clean single resolution from Pass 0/1/2 is never re-examined, and the
  candidate pool is never widened beyond what those passes considered.
- **Acceptance Criteria**:
  - AC-3.1: When Pass 0 resolves exactly one handle, no `terminal read` is issued.
  - AC-3.3: The pass runs when the candidate set is ambiguous (>1), a shape that never
    reaches Pass 2, and when `lsof` is absent, a shape that never reaches Pass 3.
  - AC-3.2: The pass considers only handles surviving the earlier passes' filtering; a pane
    those passes excluded is never selected by this one.

### FR-4: Unreadable evidence declines, never guesses
- **Description**: A tail that cannot be read is not evidence of anything.
- **Acceptance Criteria**:
  - AC-4.1: A `terminal read` that errors, times out, or returns no `.terminal.tail` key
    excludes that candidate from the match set rather than counting it as a non-match.
  - AC-4.3: The read is time-bounded with `hmad-dispatch run --timeout`; `timeout` and
    `gtimeout` appear nowhere in the implementation.
  - AC-4.2: If every candidate is unreadable, the pass declines (rc 1) — indistinguishable
    in effect from no match, and never a resolution.

### FR-5: The retention limit is documented where the pass is
- **Description**: The 2000-line cap and its consequence are recorded in the wrapper.
- **Acceptance Criteria**:
  - AC-5.1: A comment at the pass states the measured cap, that agent TUIs do not normally
    reach it, and that a shell-heavy pane is the case that fails to UNRESOLVED.

## Non-Functional Requirements
- **Performance**: at most one `terminal read` per surviving candidate, and none at all
  when an earlier pass resolved cleanly. Bounded by the candidate count, not the pool.
- **Security**: N/A. Read-only against panes the earlier passes already considered.
- **Compatibility**: cmux is unaffected — the pass is inside the orca branch of
  `_orca_find`. Behaviour is unchanged wherever Passes 0–2 already resolve.

## Out-of-Scope
- An env-overridable signature regex (`HMAD_ORCA_<AGENT>_BANNER_RE`). Considered and
  deferred in the brainstorm; vendor drift fails to UNRESOLVED, which is safe.
- Re-scanning the whole worktree by banner, ignoring the earlier passes' conclusions.
- Any change to `pin`, `pin-agents` or the pin file format. This feature changes
  resolution only; the carry behaviour shipped in `7adfce6` is untouched.
- Raising or working around the 2000-line retention cap.

## Assumptions
- Agent panes run as full-screen TUIs and so do not accumulate normal-buffer scrollback.
  Observed on three real panes over two days; the mechanism is inferred from that
  observation rather than from an Orca guarantee.
- `orca terminal read --cursor 0` returns the oldest retained lines, and `.result.terminal.tail`
  is the field carrying them — both confirmed live.
- A pane's launch command line remains visible above the alternate-screen region.

## Version History
- v1.0: Initial specification draft.
- v1.1: Back-propagated from plan v1.1 — the feature extends Pass 3 rather than adding a
  pass; `_agent_pv_re` is reused unchanged (verified against both real panes); AC-4.3 names
  the portable time bounder.
- v1.2: Placement corrected after source review — a standalone pass between Pass 2 and
  Pass 3 rather than a branch inside Pass 3; AC-3.3 added for the two shapes no current
  pass reaches.
