# Brainstorm: pin-agents-tail-banner

## Executive Summary

`_orca_find`'s three identity passes all fail for a codex pane whose launch banner has
decayed, so `hmad-dispatch env` reports `codex -> UNRESOLVED` on a machine where the pane
is sitting right there. Add a final pass that reads `.result.terminal.tail` and matches a
per-agent banner, resolving only when **exactly one** candidate matches.

## Problem Statement

Codex has no title identity by construction (it emits no OSC title, so any matching
`.title` was inherited from the tab), and Pass 2's preview signature scrolls away once the
pane does work. Measured on this machine today: `pin-agents` reports `codex UNRESOLVED`
while the pinned pane is live, and **two panes share the title `agy`**, so Pass 1 is
ambiguous across the pool as well. The pin only survives at all because of the carry fix
shipped in `7adfce6` — auto-detect itself is still blind.

## Proposed Approach

A new **Pass 3** inside `_orca_find`, after the existing passes:

- Runs only when Passes 0–2 left **0 or >1** candidates — a clean single resolution is
  never second-guessed, and the pool is never widened beyond what those passes considered.
- For each surviving candidate, read `orca terminal read --terminal <h> --cursor 0 --json`
  → `.result.terminal.tail` and match a hardcoded per-agent regex.
- Resolve **only on exactly one match**; on zero or many, decline (rc 1) exactly as the
  other passes do.

Chosen over the alternatives because it fixes the gap for every caller (`env`, `resolve`,
`send`, `verify`, `pin-agents`) rather than only at pin time.

**Evidence it can work** (measured 2026-09-01, panes alive since 08-31):

| pane | tail signal | first line |
|---|---|---|
| codex `term_f483657a` | `OpenAI Codex`, `gpt-5` | `codex '--dangerously-bypass-approvals-and-sandbox'` |
| agy `term_a3b4c1dd` | `Antigravity` | prompt + `agy '--dangerously-skip-permissions'` |
| agy `term_e3f34fcf` | `Antigravity` | prompt + feature/41 worktree |

The **launch command line** is present in every tail and is a stronger signal than the
vendor splash: it is the operator's own invocation, so it does not move when a vendor
changes its banner text. Worth pinning both.

## Alternatives Considered

- **Pass only inside `pin-agents`**: cheapest and most contained — one tail read at the
  moment identity is frozen. Rejected: `env`/`resolve` keep reporting UNRESOLVED for a
  pane the banner would have identified, so the gap stays open everywhere but the pin path.
- **Env-overridable banner regex** (`HMAD_ORCA_<AGENT>_BANNER_RE`): survives vendor drift
  with no skill edit. Rejected for v1 as a second config surface; vendor drift surfaces as
  UNRESOLVED, which is the safe direction, and Pass 2's preview matcher already carries the
  same exposure. Revisit if a banner actually moves.
- **Re-scan every pane in the worktree by banner**: catches a pane Pass 1's title filter
  wrongly excluded. Rejected: more reads, and it can select a pane the earlier passes
  deliberately rejected — the rival-banner rule in Pass 1 exists for that reason.
- **Do nothing / rely on explicit `pin`**: status quo. Rejected: it is the documented
  remedy today and it is a manual step at exactly the moment identity is least knowable.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| **A busy pane scrolls its banner out of retention** — the exact failure that kills Pass 2, one buffer larger | **H** | The load-bearing unknown; measure before designing (see Open Questions). If retention is bounded, the launch-command line dies with the banner and this pass degrades to "works on idle panes" — still useful, but the claim must shrink to match |
| A wrong-but-live pin leaks dispatches into a stranger's shell | M | Resolve only on **exactly one** match; decline on 0 or >1. This is the guard that made the 2026-08-31 hand-resolution safe, and it is non-negotiable |
| Tail reads cost one orca call per candidate on every resolution | M | Pass 3 runs only when 0 or >1 candidates survive; a clean Pass 0/1 never reaches it |
| A rival agent's banner appears in a pane's scrollback (an operator ran `codex --help` in an agy pane) | L | Reuse Pass 1's rival-rejection rule: a candidate carrying the OTHER agent's banner is rejected rather than counted |
| Vendor changes its banner text | L | Fails to UNRESOLVED, never to a wrong pane. Pin the launch-command form as well as the splash |

## Dependencies

None. `orca terminal read` is already called three times inside `hmad-dispatch`, so no new
capability is required — the "no wrapper verb reads an arbitrary handle" note filed against
this row constrains the **handoff** skill, which may not call `orca` directly. It does not
constrain h-mad's own wrapper, which is the orca layer.

## Open Questions

- **Does `--cursor 0` reach the true start of a busy pane's scrollback, or is retention
  bounded?** All three probed panes were idle with 12–18 total lines, so the measurement so
  far says nothing about a pane that has worked. This decides whether Pass 3 is a general
  fix or an idle-pane fix, and it must be measured on a pane with real scrollback before
  the spec commits to a claim.
- Should the launch-command line and the vendor banner be two patterns with different
  confidence, or one alternation? (Two lets a vendor-drift failure be distinguished from a
  pane that was never an agent.)
- Does Pass 3 belong before or after the existing Pass 2 preview fallback? Running it last
  is cheapest; running it before Pass 2 would prefer strong evidence over weak.

## Version History
- v1.0: Initial brainstorm draft.
