# Brainstorm: exec-path-hardening

## Executive Summary

`hmad-dispatch exec` is now the documented default for one-shot 5d/5e and every audit
dispatch, but it is the only transport with **no observability surface at all** — no pane,
no Orca task row, no checkpoint, no liveness signal for up to 900 s. Stamp visibility
inside `_cmd_exec` (worktree-comment + notify + heartbeat) and close the one code/comment
contradiction the transport still carries (`--log` truncation asymmetry between backends).

## Problem Statement

When `/h-mad` Phase 5 runs on `exec`, the operator away from the desk has no way to tell a
900-second Codex GREEN that is working from one that died at second 3. Under the pane path
the Orca pane is on the phone; under orchestration the worktree card and `worker_done` are.
Under `exec` there is a blocking subprocess and silence until it exits, and nothing durable
is left behind afterwards.

## Findings: what is actually still open on the exec path

The evaluation that prompted this feature said full hardening would mostly re-audit shipped
work. That held up under checking, and it narrows the real surface rather than removing it.

**Already shipped — not in scope, listed so the audit does not re-open them:**

| Defect | Status |
|---|---|
| Empty final message read as success | `rc 3` + explicit `EMPTY final message` diagnostic |
| Prompt echo laundered into a verdict (`STATUS: NEEDS_CONTEXT` from the contract block) | `===HMAD-DISPATCH-BOUNDARY===` appended; recovery slices after its **last** occurrence |
| No-boundary transcript re-opening the laundering hole | per-backend: codex **fails closed**, agy reads whole log (its prompt is an arg, never echoed) |
| `tree delta` counting unrelated repo dirt as "the work landed" | `git status --porcelain -- .` scoped to `--cd` |
| Timeout orphaning grandchildren | `_run_with_timeout` runs the child in its own pgroup via `set -m`, TERM→grace→KILL on the group, absolute deadline off `SECONDS` |
| agy report lost to a later summarizing turn (F-10) | report-file + `report-wait`, transport-agnostic, works behind `exec … &` |

**Open — the actual scope:**

1. **No visibility surface (primary).** `_cmd_exec` writes to stderr and nowhere else.
   Nothing reaches the phone; nothing survives the run. `_cmd_worktree_comment` and
   `notify` both already exist as verbs and neither is wired into `exec`.
2. **No liveness during the run.** `exec` blocks. `--log` is tailable, but tailing requires
   an operator already at a terminal — which is the situation this feature is not about.
   "Process gone, output empty" is a measured transport symptom here, so silence is
   genuinely ambiguous today.
3. **`--log` truncation is asymmetric between backends, and a load-bearing comment assumes
   otherwise.** codex redirects `> "$log"` (truncates a caller-supplied log); agy appends
   `>> "$log"`. The comment justifying the boundary on both backends
   (`hmad-dispatch.sh:1898`) reasons from "a caller can point `--log` at a file that
   already holds echoed content" — for codex that content is destroyed before the run
   starts. Verified by reading the redirects, not assumed. Small, but it is a doc-vs-code
   contradiction on the recovery path, and the recovery protocol names `--log` as *the one
   channel observed to outlive the others*.

**Adjacent, deliberately out of scope:** `docs/skill-monitoring.md` stops at J18
(2026-07-23). Every exec defect since — J19 through J23 — shipped through handoffs and was
never filed. The registry that is supposed to make exec defects findable no longer tracks
them. Naming it here so it is a decision, not an omission.

## Proposed Approach

Wire the three surfaces **inside `_cmd_exec`**, so they cannot be forgotten at a call site.
This skill's own recorded failure mode is a correct signal that nothing was obliged to
consume — `PREFLIGHT:` had to be re-engineered specifically because detection existed and
no step read it, and `size_status=` was moved onto the verdict line for the same reason.
An orchestrator-level instruction in `SKILL.md` would reproduce that defect one signal over.

- **worktree-comment** — durable, mobile-visible, survives the run. Stamp at start
  (`exec <agent> <feature>/<module> started`) and at exit (rc + extracted verdict).
- **notify** — push at exit carrying rc + verdict, so completion reaches the phone actively.
- **heartbeat** — periodic stamp while the subprocess is alive, so "still working" is
  distinguishable from "died". `_run_with_timeout` already owns a `kill -0` poll loop at
  0.25 s; the heartbeat can ride that existing liveness check rather than adding a second
  poller.

All three are **best-effort and never gate the dispatch**: a failed comment must not change
`rc`, must not consume stdout (the verdict carrier), and must not fail the run. Orca-only
verbs degrade to a no-op on cmux.

Plus: make the codex `--log` redirect append-consistent with agy, or state truncation as the
contract in both places. One of the two, not both.

## Alternatives Considered

- **Orca orchestration instead of `exec`** — rejected on measured evidence. Completion
  becomes a self-reported `worker_done` with no process to reap; `worker-start` returning
  `stage: "input_accepted"` was measured delivering a prompt into a booting pane that never
  ran it; a lifecycle-rejected `worker_done` still lands in the mailbox; one Delivery holds
  every message and `--ack` destroys all of it. That trades a hard exit code for a weaker
  signal, on the one axis `exec` exists to provide.
- **Retrofit Orca provenance onto exec runs** — rejected as structurally impossible, not
  merely hard. `worker_done` must be sent from the dispatched terminal (`sender_not_assignee`
  measured), and the Orca guide explicitly forbids relabeling externally-run work as
  orchestrated.
- **`SKILL.md` instruction to the orchestrator** — rejected per the PREFLIGHT precedent above.
- **A separate opt-in `checkpoint` verb** — composable, but still advisory at the call site,
  so it inherits the same failure.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| A visibility call writes to stdout and corrupts the verdict channel | M | Every surface call redirected to stderr; pin it with a test asserting stdout is byte-identical with and without the surfaces |
| A failing/slow `worktree-comment` changes `rc` or stalls the dispatch | M | Best-effort wrapper: ignore failure, bound the call, never let it touch `rc`; test that a stubbed-failing comment leaves `rc` unchanged |
| Heartbeat noise floods the worktree card | M | Stamp a single rolling comment (overwrite), not an append stream; interval configurable, default sparse |
| A guard ships whose message is the load-bearing part and a returncode-only test passes it | M | Mutation-verify each guard via `h_mad_mutation_harness.py`, asserting message content — the exact J22/J23 lesson |
| Changing the codex `--log` redirect breaks the recovery path that depends on it | L | The recovery tests already drive realistic echo shapes (`HMAD_STUB_CODEX_ECHO_STDIN=1`); RED against them first |
| Scope drifts back into already-shipped work | M | The shipped table above is the explicit non-scope; audit against it |

## Dependencies

None external. Uses `_cmd_worktree_comment`, `_cmd_notify`, `_run_with_timeout` — all
already in `scripts/hmad-dispatch.sh`. Orca-only surfaces no-op on cmux by existing
`_require_orca` behaviour.

## Open Questions

- Heartbeat interval and whether it is on by default or opt-in via flag/env.
- Rolling single comment vs. a short append trail — which is actually more readable on the
  phone card.
- Does the comment target the **active** worktree (default) or the `--cd` worktree? They
  differ whenever `exec --cd` points at a sibling checkout.
- Is the stale registry (J19+ unfiled) taken as a follow-up feature, or closed inside this
  one?
- `notify` on every exec, or only on failure/non-clean verdict? Every-exec risks becoming
  notification noise across a multi-module Phase 5.

## Version History

- v1.0: Initial brainstorm draft.
