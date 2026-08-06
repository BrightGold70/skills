# Brainstorm: gate-blindness-hardening

## Executive Summary

Two gates in `/h-mad` cannot see defects they are positioned to catch: the architectural
review is optional in practice (an unrecorded `archreview` passes Phase 7 silently, and the
6a-prime protocol actively pushes runs toward skipping it), and every test fixture feeds tidy
ASCII, so a whole class of real-payload defects is unreachable in-suite.

## Problem Statement

Both were demonstrated in one feature (`exec-path-hardening`, shipped 2026-08-06). A hardcoded
heartbeat and a comment-corrupting quoting bug each passed the entire gate stack; one was
caught only by 6a-prime, the other only by a live run. The gate that caught it is the one the
protocol tells you to skip, and the reason the other was invisible is that no fixture carries
a character an agent actually emits.

## Findings — grounded, not inferred

**F1 — an unrecorded `archreview` blocks nothing.** Probed against the real gate with a record
that never wrote the field, everything else satisfied:

```
$ h_mad_phase7_preconditions.py <state> --feature probe-feat
PHASE7: READY blockers=0
```

`h_mad_phase7_preconditions.py:88-99` branches on `WITH_FIXES`/`NO` (blocker) and
`SKIPPED_NO_PANE` (warning) — and has **no `else`**. So the architectural review is not merely
skippable via a recorded escape hatch; it is optional by omission, with no signal of any kind.
The comment above it says "a deliberate skip is reported", which is true only when the skip is
deliberate enough to be written down.

**F2 — the 6a-prime protocol pushes runs toward that hole.** `SKILL.md` §6a-prime mandates a
**pane** preflight (`hmad-dispatch alive agy`) and halts `step6a-prime:no_reviewer_pane`
otherwise, offering `archreview: "SKIPPED_NO_PANE"` as the way forward. But `exec` is the
documented default transport for every other audit dispatch, and `exec agy` is
pane-independent. Stale pins are the ordinary state — this session ran from first command to
last on `PREFLIGHT: FAIL stale=codex,agy`. So the protocol's own preconditions fail in the
normal case, and the offered remedy is the unchecked one from F1.

Followed literally this session, 6a-prime would have been skipped — and it is the pass that
caught `beat) state="running · 0m"`, a heartbeat that would have reported `0m` for the entire
duration of any dispatch.

**F3 — every fixture is tidy ASCII, and that is exactly why the worst bug survived.**
`prefix="${current%$rest}"` left `$rest` unquoted, so bash glob-matched it. Production
verdicts embed the agent's markdown — `[green_mod3.report.md](…)`, `**Full suite:**` — and
those metacharacters made the strip fail, doubling the comment on every stamp. Measured on the
live worktree card: **513 spans / 38,329 bytes**, reproduced deterministically by feeding the
real card back through the composer (513 → 1026).

It passed 1063 tests, `MUTATION: ALL_CAUGHT 5/5`, five wire-scoped reverts and a clean
architectural review, because every fixture used short glob-free strings — the shared stub
returns `"comment":"c"`. The bug was not under-tested; it was **unreachable** by the fixtures.

## Proposed Approach

**Close the review hole at the gate, then remove the reason to use it.**

1. `h_mad_phase7_preconditions.py` gains the missing `else`: an absent `archreview` is a
   **blocker**, not silence. This is the load-bearing change — it converts "optional by
   omission" into "must be recorded".
2. `SKIPPED_NO_PANE` is promoted from warning to blocker. Once headless review is accepted
   (below) there is no ordinary reason to skip, so the escape must stop being the path of
   least resistance.
3. `SKILL.md` §6a-prime accepts `exec agy` as satisfying the gate — check `command -v agy`,
   not pane resolution — matching what §"Reviewing a skill with agy" already prescribes for
   every other agy dispatch.

**Make fixtures carry what agents actually emit.**

4. The shared stubs gain a hostile-payload mode: markdown links, `**bold**`, `*` and `[`,
   embedded newlines, unicode, and the span markers themselves. Opt-in via an
   `HMAD_STUB_*`-style knob, consulted only when set — the existing precedent used by
   `HMAD_STUB_ORCA_WT_PS_STDOUT`, `HMAD_STUB_ORCA_TASKLIST_STDOUT` and `HMAD_STUB_ORCA_STATE`,
   so all 1143 existing tests keep passing unchanged.
5. `references/codex-implementer-prompt.md` gains the requirement, so future RED dispatches are
   told to drive hostile payloads rather than tidy ones. Without this the convention decays to
   whatever the next author happens to type.

## Alternatives Considered

- **Accept headless review only, leave the gate as-is** — rejected: it fixes the *pressure* to
  skip while leaving the *hole* (F1) untouched, so the next unrecorded review still closes a
  feature silently.
- **Make hostile payloads the default** — rejected for this cycle: strongest guarantee, but it
  would break an unknown number of the 1143 existing tests and force unrelated triage inside a
  feature about gate correctness. The opt-in knob plus a prompt-template mandate gets the
  forward-looking benefit without the blast radius.
- **Repo-wide fixture sweep** — rejected as scope: touches suites unrelated to the observed
  defect. The stubs the exec path shares are where the evidence is.
- **Require a live e2e before Phase 7 closure** — tempting (a live run is what found F3), but
  it is a different feature: it changes what "done" means for every feature, and many have no
  meaningful live surface. Noted as a follow-up, not folded in.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Promoting skip to a blocker strands a run with no reviewer available | M | Accept `exec agy` first (item 3), so the blocker only fires when *neither* transport exists; provide an explicit, recorded operator override rather than a silent warning |
| Hostile stub payloads break existing tests | M | Opt-in knob, unset = today's behaviour; assert the full 1143 pass with the knob unset |
| A hostile payload that contains the span markers breaks the fixture itself | M | That is the point — but the stub must emit them as data; pin with a test that the marker-bearing payload round-trips |
| The prompt-template mandate is ignored by future dispatches | M | It is advisory by nature; pair it with at least one shared hostile fixture helper so the cheap path is also the correct one |
| Changing a shipped gate breaks other features' recorded state | L | Existing records carry `archreview` values already; the new blocker only fires on absence, which no completed feature has |

## Dependencies

None external. Touches `h_mad_phase7_preconditions.py`, `SKILL.md`, `tests/stubs/*`, and
`references/codex-implementer-prompt.md` — all inside `h-mad/`. Note the symlink: this repo is
the live `~/.claude/skills/h-mad`, so both coupled suites must pass before merge.

## Open Questions

- Should the operator override for a genuine skip mirror the existing `[audit-override]` commit
  convention, or be a state field? The commit convention is auditable in history; a state field
  is easier for the gate to read.
- Does promoting `SKIPPED_NO_PANE` to a blocker need a grace path for cmux-only sessions, where
  neither a pane nor `agy` may exist?
- Should the hostile-payload knob be one flag or a named corpus (`markdown`, `unicode`,
  `markers`) so a test can request the hazard it cares about?
- F1's fix makes `archreview` effectively mandatory. Should Phase 6 write it automatically on a
  clean 6a-prime, so the field cannot be forgotten rather than merely enforced?

## Version History

- v1.0: Initial brainstorm draft.
