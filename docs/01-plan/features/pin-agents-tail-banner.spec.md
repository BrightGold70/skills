# Spec: pin-agents-tail-banner

## Executive Summary

Add a standalone tail-evidence pass to `_orca_find`, between Pass 2 and Pass 3, reading a candidate pane's
`.result.terminal.tail` and resolves an agent when — and only when — exactly one candidate
carries that agent's `_agent_pv_re` **banner** signature. The launch command line is not a
signature (§Measured basis 3).

## Goal

Recover a correct agent handle in the case every existing pass fails: a live pane whose
title is inherited and whose preview banner has decayed, which today reports `UNRESOLVED`
and forces a manual `pin`.

## Measured basis

Three measurements taken 2026-09-01; all are load-bearing, one falsified the brainstorm's
stronger claim, and the third falsified this spec's own AC-1.1 (see below).

1. **Identity survives on real agent panes.** Three panes alive since 2026-08-31 — one
   codex (the pinned dispatch target) and two agy — each retain 12–18 tail lines carrying
   both the launch command (`codex '--dangerously-bypass-approvals-and-sandbox'`,
   `agy '--dangerously-skip-permissions'`) and the vendor banner (`OpenAI Codex` / `gpt-5`,
   `Antigravity`).
2. **Tail retention is hard-capped at 2000 lines**, regardless of `--limit`. A disposable
   pane emitting 200 lines retained 203 and kept its first line; one emitting 2000 retained
   exactly 2000 and lost it; one emitting 20000 retained 2000 beginning at line 18001.

3. **Only the banner half of that retained text is a matcher.** The pass reuses
   `_agent_pv_re` unchanged, and that helper deliberately matches *program banners* rather
   than command lines — the bare tokens `codex`/`agy` were removed from it precisely because
   a pane merely discussing an agent matched. Measured 2026-09-01 by extracting both patterns
   from the wrapper and running them against fixed strings, with controls that must match:

   | line | `codex` re | `agy` re |
   |---|---|---|
   | `OpenAI Codex (v0.145.0)  model: gpt-5.6-terra` | MATCH | — |
   | `gpt-5.6-terra high · ~/repo` | MATCH | — |
   | `Antigravity CLI` | — | MATCH |
   | `Gemini 3.1 Pro` | — | MATCH |
   | `codex '--dangerously-bypass-approvals-and-sandbox'` | **NO MATCH** | — |
   | `agy '--dangerously-skip-permissions'` | — | **NO MATCH** |

   An earlier revision of this spec (v1.0–v1.4) guaranteed launch-command-only resolution in
   AC-1.1 while the design reused `_agent_pv_re` unchanged; the two could not both hold, and a
   faithful implementation would have been permanently red on AC-1.1 — or, worse, made green by
   adding a banner to the fixture, which tests the path that already worked. Widening the shared
   helper was considered and rejected: it also widens Pass 1's rival rejection and Pass 2's
   preview match, re-admitting the false-positive class those patterns were narrowed to exclude.
   The guarantee was narrowed instead. In practice nothing is lost — §Measured basis 1 found
   every real agent pane carrying the banner *alongside* the launch line.

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
  - AC-1.1: Given a candidate pool of one pane whose tail carries the agent's `_agent_pv_re`
    signature — its **vendor/model banner** — and no other pane's, `_orca_find <agent>` prints
    that handle and returns 0.
  - AC-1.2: **The launch command line is not itself a signature.** A pane whose tail carries
    only the launch command (`codex '--dangerously-bypass-approvals-and-sandbox'`,
    `agy '--dangerously-skip-permissions'`) and no banner does NOT resolve. Measured
    2026-09-01, with controls: both launch lines are NO MATCH against the unchanged
    `_agent_pv_re`, while all four banner/status-line controls MATCH. See §Measured basis 3.
  - AC-1.3: `hmad-dispatch env` reports the resolved handle rather than `UNRESOLVED` for a
    pane that only the tail pass can identify.

### FR-2: The pass resolves only on exactly one match
- **Description**: Zero or more than one matching candidate declines, leaving the agent
  unresolved.
- **Acceptance Criteria**:
  - AC-2.1: Two candidates whose tails both match the agent → the pass declines: it prints
    no handle and control falls through to the next pass. It does NOT return non-zero from
    `_orca_find`, which would short-circuit the OS-evidence pass behind it.
  - AC-2.2: Zero matching candidates → declines the same way: no handle, fall through.
  - AC-2.3: A candidate whose tail carries the RIVAL agent's signature is rejected before
    counting, so it can neither be selected nor create a false ambiguity.

### FR-3: The tail read runs only when the earlier passes did not settle it
- **Description**: A clean single resolution from Pass 0/1/2 is never re-examined, and the
  candidate pool is never widened beyond what those passes considered.
- **Acceptance Criteria**:
  - AC-3.1: When Pass 0 resolves exactly one handle, no `terminal read` is issued.
  - AC-3.3: The pass runs when the candidate set is ambiguous (>1), a shape that never
    reaches Pass 2, and when `lsof` is absent, a shape that never reaches Pass 3.
  - AC-3.2: The candidate pool is `$scoped` — the worktree-scoped terminal set that already
    excludes the caller's own pane — and nothing wider. A pane `$scoped` excludes is never
    selected by this pass. Passes 1 and 2 do NOT narrow the pool further: they are matchers
    that select, not filters that remove, so a pane they failed to match is still a legitimate
    candidate here. That is the point of the pass — a codex pane whose title is inherited and
    whose preview has decayed matches neither, and is exactly what the tail identifies.

### FR-4: Unreadable evidence declines, never guesses
- **Description**: A tail that cannot be read is not evidence of anything.
- **Acceptance Criteria**:
  - AC-4.1: A `terminal read` that errors, times out, or returns no `.terminal.tail` key
    excludes that candidate from the match set rather than counting it as a non-match.
  - AC-4.3: The read is time-bounded with `_cmd_run --timeout` — the function the
    `hmad-dispatch run` verb dispatches to, called IN-PROCESS, never the verb re-exec'd as a
    subprocess. No line of the implementation **invokes** `timeout` or `gtimeout` as a
    command; the predicate is command position, not substring presence, so naming either in
    prose or a comment is free.
  - AC-4.2: If every candidate is unreadable, the pass declines by falling through —
    indistinguishable in effect from no match, and never a resolution.

### FR-5: The retention limit is documented where the pass is
- **Description**: The 2000-line cap and its consequence are recorded in the wrapper.
- **Acceptance Criteria**:
  - AC-5.1: A comment at the pass states the measured cap, that agent TUIs do not normally
    reach it, and that a shell-heavy pane is the case that fails to UNRESOLVED.
  - AC-5.2: The same comment states the **stale-pane limit**, which is the OTHER side of the
    cap and is the more likely one: a pane whose agent has EXITED but which has since emitted
    fewer than 2000 lines of shell still carries the banner, is still a unique match, and is
    still resolved — so a dispatch can land in a plain shell. Tail evidence is HISTORICAL; it
    proves what a pane once ran, never what it is running now.

## Non-Functional Requirements
- **Performance**: at most one `terminal read` per surviving candidate, and none at all
  when an earlier pass resolved cleanly. Bounded by the candidate count, not the pool.
- **Security**: N/A. Read-only against panes the earlier passes already considered.
- **Compatibility**: cmux is unaffected — the pass is inside the orca branch of
  `_orca_find`. Behaviour is unchanged wherever Passes 0–2 already resolve.

### FR-5 note — why the stale-pane limit is accepted rather than closed

Two closures were considered and both cost more than the hole. Gating the pass on process
liveness (`_agent_procs_in`) reintroduces the `lsof` dependency on the exact path the feature
exists to cover, contradicting AC-3.3 outright. Downgrading the pass to a diagnostic leaves the
manual pin in place, which is this spec's Goal.

The decisive argument is that the pass is **no weaker than the two it sits between**: Pass 1
matches a title and Pass 2 a preview, and neither is liveness-gated either, so a stale pane is
already resolvable today by both. Only Pass 0 (which names the running program) and Pass 4
(which requires a live process) carry liveness. Accepting the limit therefore adds no new class
of failure; leaving it undocumented would.

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
- The agent's **banner/status line** remains visible above the alternate-screen region.
  Stated in terms of the banner, not the launch command: v1.5 made the launch line
  non-evidence (§Measured basis 3), so an assumption about ITS visibility would describe a
  dependency the feature no longer has — and would quietly re-license a launch-only fixture.

## Version History
- v1.0: Initial specification draft.
- v1.1: Back-propagated from plan v1.1 — the feature extends Pass 3 rather than adding a
  pass; `_agent_pv_re` is reused unchanged (verified against both real panes); AC-4.3 names
  the portable time bounder.
- v1.2: Placement corrected after source review — a standalone pass between Pass 2 and
  Pass 3 rather than a branch inside Pass 3; AC-3.3 added for the two shapes no current
  pass reaches.
- v1.3: Back-propagated from design audit v2 — "declines (rc 1)" replaced by fall-through in
  AC-2.1, AC-2.2 and AC-4.2. The design's narrower reading is the correct one: a non-zero
  return from `_orca_find` would stop the OS-evidence pass from running at all. The plan
  states no rc semantics, so no Phase-3 round-trip was required.
- v1.4: Back-propagated from design audit v7 — AC-3.2's "surviving the earlier passes'
  filtering" was the ambiguous phrase behind the cycle-3 pool argument; it now names `$scoped`
  explicitly and states that Passes 1-2 are matchers rather than filters. The plan already
  said `$scoped` for both entry paths, so the spec was the stale surface, not the design.
- v1.5: Back-propagated from impl-plan audit v5 (codex surface, operator-approved 2026-09-01) — AC-1.1's launch-command-only guarantee was UNSATISFIABLE by the design's unchanged _agent_pv_re; measured with controls, both launch lines are NO MATCH and all four banner controls MATCH. AC-1.1 narrowed to the vendor/model banner, AC-1.2 inverted to state the launch line is NOT a signature, and Measured basis 3 added with the table. AC-5.2 adds the stale-pane limit (an exited agent's banner still resolves below the 2000-line cap) with an FR-5 note on why it is accepted: Pass 1 and Pass 2 are not liveness-gated either, so it is no new failure class.
- v1.6: Impl-plan audit v13 (codex) — all three must-fixes were mutation-discrimination gaps in this plan's own scaffolding, and the 37/11/26 counts reproduced. resolve-on-ge-0 was a CRASH mutant: with tn=0 the relaxed branch runs tail_h=$(printf … | grep . | head -n 1), grep returns 1 on empty input and set -euo pipefail aborts before anything resolves (reproduced: rc 1, no output), so a kill would be credited to an abort rather than the property. Replaced by signature-check-not-enforced, which lets a readable non-matching candidate into tail_ids and produces an observably wrong resolution; AC-3.5's fixture is pinned to exactly one readable non-matching candidate to make that kill possible. The two long-tail nodes added in v1.8 had NO mutation reverting the here-string to the pipeline, so the guard they exist for was never mutation-tested - two reverting mutations added, one per branch. tail-sig-fabricates-banner-on-failure has a fixture precondition that was unstated: its hardcoded OpenAI Codex output only changes behaviour for exactly one unreadable candidate resolving codex, so AC-3.11's fixture is now pinned. AC-4.2 was still listed as active in Task 4 while marked withdrawn elsewhere. The spec's assumption about launch-command visibility was restated in terms of the banner, which v1.5 made the only evidence.
- v1.7: Impl-plan audit v16 (codex) — AC-4.3 rewritten. It prescribed `hmad-dispatch run --timeout` (the subprocess form the implementation contract rejects in favour of the in-process `_cmd_run`) and asserted that `timeout`/`gtimeout` "appear nowhere in the implementation" — a SUBSTRING claim that impl-plan AC-2.7 does not make and could not pass, since the predicate is command position and the regex matched 66 lines of the existing file. The AC now names `_cmd_run` and says no line **invokes** either binary, so the comment that tells an implementer why `timeout 2 orca …` is not an option stays legal.
