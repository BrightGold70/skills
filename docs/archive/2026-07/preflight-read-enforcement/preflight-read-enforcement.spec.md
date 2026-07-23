# Spec: preflight-read-enforcement

## Executive Summary

`hmad-dispatch env` writes a fingerprinted receipt when its preflight passes, and a dispatch refuses
to deliver a prompt without a fresh, matching one — turning the Wave-2 `PREFLIGHT:` token from a
signal an orchestrator is *asked* to read into one it *cannot* skip, and closing the agent-conflict
case that `send` still cannot see.

## Goal

Make it mechanically impossible to dispatch to an agent without a passing preflight whose resolved
handle set is still current, so a rotated or conflicting handle cannot silently swallow a dispatch.

## Definitions

Used precisely throughout; the audit should hold ACs to these.

- **Dispatch** — the operation that delivers a prompt to an agent for work: `hmad-dispatch send`.
  Which internal function carries the enforcement (`_cmd_send` vs `_send_text`) is a design
  decision, deliberately not fixed here.
- **Receipt** — the on-disk artifact recording a passed preflight.
- **Fingerprint** — a deterministic function of the resolved values for `codex` and `agy`, where an
  unresolvable agent contributes the literal value `UNRESOLVED`.
- **Valid receipt** — one that exists, is within the freshness window, and whose fingerprint equals
  the fingerprint recomputed at dispatch time.

## Requirement on exit codes (read before auditing Axis B)

`invariants.base.md` §"Audit-gate signal discipline" governs *gates whose verdict the orchestrator
consumes* — those MUST use a stdout token and exit 0. It does **not** govern an operation that
declines to act. A refused dispatch is the latter: it emits a diagnostic on stderr and returns
non-zero, exactly as the existing `terminal_handle_stale` refusal does
(`h-mad/scripts/hmad-dispatch.sh:757-759`). `env` itself continues to exit 0 on both verdicts.
No requirement below may be satisfied by making `PREFLIGHT: FAIL` exit non-zero.

## Functional Requirements

### FR-1: `env` emits a receipt on a passing preflight
- **Description**: When `hmad-dispatch env` concludes `PREFLIGHT: PASS`, it writes a receipt
  recording the verdict, the fingerprint of the resolved handle set, and a UTC timestamp.
- **Acceptance Criteria**:
  - AC-1.1: After an `env` run that prints `PREFLIGHT: PASS`, the receipt file exists.
  - AC-1.2: The receipt contains a timestamp parseable as UTC and a non-empty fingerprint field.
  - AC-1.3: Two `env` runs with an identical resolved handle set produce an identical fingerprint.
  - AC-1.4: An `env` run whose resolved handle set differs in any agent produces a different
    fingerprint from AC-1.3's.
  - AC-1.5: `env` still prints the `PREFLIGHT: PASS` line and still exits 0 when writing the receipt.

### FR-2: A failing preflight leaves no usable receipt
- **Description**: `PREFLIGHT: FAIL` must not write a receipt, and must invalidate any receipt
  already present, so an ignored FAIL cannot be dispatched through on a stale token.
- **Acceptance Criteria**:
  - AC-2.1: Starting with no receipt, an `env` run printing `PREFLIGHT: FAIL` leaves no receipt file.
  - AC-2.2: Starting with a valid receipt on disk, an `env` run printing `PREFLIGHT: FAIL` leaves no
    valid receipt (the prior one is removed or rendered invalid).
  - AC-2.3: `env` still prints its `PREFLIGHT: FAIL …` line with its `stale=` / `conflict=` fields
    intact, and still exits 0.
  - AC-2.4: A dispatch attempted immediately after a FAIL preflight is refused (ties FR-2 to FR-3;
    asserts the observable consequence, not just the file state).

### FR-3: Dispatch fails closed without a valid receipt
- **Description**: A dispatch with no valid receipt is refused, non-zero, with nothing sent.
- **Acceptance Criteria**:
  - AC-3.1: With no receipt present, a dispatch returns non-zero.
  - AC-3.2: With no receipt present, a dispatch performs no send — no delivery call is made to the
    substrate. (Asserted against the call, not merely the exit code.)
  - AC-3.3: The refusal names a distinguishable reason on **stderr**: `preflight_not_run` when the
    receipt is absent, `preflight_expired` when it is too old, `preflight_handles_rotated` when the
    fingerprint no longer matches.
  - AC-3.4: With a valid receipt present, a dispatch proceeds and delivers, and its behavior is
    otherwise unchanged from today (same delivery mode selection by prompt size).

### FR-4: Fingerprint mismatch invalidates a receipt (rotation detection)
- **Description**: A receipt whose fingerprint no longer matches resolution at dispatch time is
  invalid regardless of age. This is the requirement that makes the receipt more than a stamp.
- **Acceptance Criteria**:
  - AC-4.1: Given a valid receipt, changing any agent's resolved handle causes the next dispatch to
    be refused with `preflight_handles_rotated`.
  - AC-4.2: A receipt written while an agent was `UNRESOLVED` is invalidated once that agent
    resolves to a handle (matching `SKILL.md`'s "re-assert after any re-pin").
  - AC-4.3: Re-running `env` after the change produces a receipt that permits the dispatch again,
    without any manual file edit.
  - AC-4.4: A dispatch is **not** refused when handles are unchanged — the guard discriminates
    rather than refusing unconditionally.

### FR-5: Receipt freshness window
- **Description**: A receipt expires after a bounded, configurable interval, as a backstop to the
  fingerprint check.
- **Acceptance Criteria**:
  - AC-5.1: A receipt older than the window causes a dispatch to be refused with `preflight_expired`.
  - AC-5.2: A receipt within the window, fingerprint matching, permits the dispatch.
  - AC-5.3: The window is configurable via a documented environment variable, and the default is a
    specific documented number of seconds (not unbounded).
  - AC-5.4: An unset override yields the documented default rather than an error or an infinite window.

### FR-6: Documented operator opt-out
- **Description**: `HMAD_SKIP_PREFLIGHT=1` bypasses the receipt requirement, and announces itself.
- **Acceptance Criteria**:
  - AC-6.1: With `HMAD_SKIP_PREFLIGHT=1` and no receipt present, a dispatch proceeds and delivers.
  - AC-6.2: Each bypassed dispatch emits a notice on stderr naming the bypass.
  - AC-6.3: With the variable unset, the requirement is enforced — the default is fail-closed.
    (Guards against the escape hatch becoming the production path via a globally exported var.)
  - AC-6.4: The opt-out does not suppress the FR-7 conflict guard.

### FR-7: Agent-conflict guard at dispatch
- **Description**: A dispatch is refused when the target agent's resolved handle is identical to the
  other agent's resolved handle — the case `_cmd_env` reports at `hmad-dispatch.sh:303-306` but
  `_send_text` cannot see.
- **Acceptance Criteria**:
  - AC-7.1: When `codex` and `agy` resolve to the same non-empty handle, a dispatch to either is
    refused, non-zero, with nothing sent.
  - AC-7.2: The refusal names `preflight_agent_conflict` on stderr.
  - AC-7.3: When the two agents resolve to different handles, a dispatch is not refused for conflict
    — the guard discriminates.
  - AC-7.4: An `UNRESOLVED` value for both agents does **not** count as a conflict (two unresolved
    agents are not "one pane"); the guard requires two equal, non-empty resolved values.

### FR-8: Receipt path override for isolation
- **Description**: The receipt path is overridable, mirroring `HMAD_ORCA_PIN_FILE`
  (`hmad-dispatch.sh:91-92`), so the wrapper's own suite is not coupled to a developer's live
  session state — the J7 failure mode, where pinning agents and running the suite were mutually
  exclusive.
- **Acceptance Criteria**:
  - AC-8.1: A documented environment variable overrides the receipt path; when set, no receipt is
    read from or written to the default location.
  - AC-8.2: With the variable unset, the default path is used.
  - AC-8.3: The full test suite reports **identical pass/fail counts** whether or not a receipt
    exists at the default path. (Verified by measurement, not by a test asserting a property of the
    suite it lives in — see Out-of-Scope.)
  - AC-8.4: The receipt is not tracked by git, consistent with `.h-mad/orca-pins.env`.

### FR-9: Documentation states machinery, not protocol
- **Description**: `h-mad/SKILL.md` and the affected `references/*.md` describe the enforced
  behavior, so the prose no longer claims a mandated-read obligation the code now guarantees.
- **Acceptance Criteria**:
  - AC-9.1: `SKILL.md`'s Phase-5 preflight section states that a dispatch refuses without a valid
    receipt, and names the refusal reasons.
  - AC-9.2: The documented recovery for each refusal reason is present and actionable.
  - AC-9.3: `references/agent-substrate.md` documents the receipt, its override variable, the
    freshness variable, and the opt-out.
  - AC-9.4: `SKILL.md` frontmatter (`name`, `description`) remains valid — project Axis B, "Skill
    manifest integrity".

## Non-Functional Requirements

- **Performance**: A dispatch may add at most one additional terminal-listing call beyond today's.
  Receipt read/write is local file I/O and must not add a network or substrate round trip.
- **Security**: N/A — no credentials or external transport. The receipt holds handle identifiers
  already visible in `env` output.
- **Compatibility**: Backward compatibility is a base Axis B invariant. `env`'s stdout contract
  (`substrate:`, `<agent> -> <handle>`, `stale pins:`, `CONFLICT:`, `orchestration:`, `PREFLIGHT:`)
  is unchanged and additive-only. Operator overrides (`HMAD_ORCA_PIN_FILE`, `HMAD_ORCA_*_TERMINAL`,
  `HMAD_SEND_INLINE_MAX`) keep their current precedence.

## Out-of-Scope

- **FR-5 of Wave 2 — the `ASSEMBLE: PASS` mandated read.** This run dogfoods
  `h_mad_assemble_audit.py`; changing that instrument during the measurement invalidates both.
- **Making any gate exit non-zero.** Forbidden by base Axis B.
- **`stablyai/orca#9870`** — per-terminal identity is blocked upstream. This feature mitigates the
  consequences of misresolution; it does not attempt to fix resolution itself.
- **A test asserting AC-8.3.** A test inside the suite cannot honestly assert a property *of* that
  suite; AC-8.3 is verified by measured A/B pass/fail counts and reported as such. Named here
  explicitly so its absence from the test set is a deliberate decision, not a coverage gap.
- **Enforcement on `clear` / `interrupt` recovery verbs.** Refusing to clear a wedged pane because
  no preflight ran would obstruct the recovery path; these are not dispatches per the Definitions.

## Assumptions

- Wave 1 (`5fa96ba`) and Wave 2 (`787aecf`) are on `main` and unmodified by this feature.
- `_orca_handle_live`'s three-way contract holds: rc=2 (unreadable listing) must never be treated as
  death, so an unreadable listing must not by itself invalidate a receipt.
- Agents are exactly `codex` and `agy`, as enumerated at `hmad-dispatch.sh:281`.
- The substrate under test is orca; cmux applicability is an open design question carried from
  brainstorm, and whichever way it resolves must be stated in the design.

## Version History
- v1.0: Initial specification draft.
