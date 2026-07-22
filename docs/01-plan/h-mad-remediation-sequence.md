# H-MAD remediation sequence — bugs, gaps, candidates

Derived 2026-07-23 from `docs/skill-monitoring.md`, the archived report carry items, the
2026-07-22 handoffs, and a code read of `h-mad/scripts/`. Everything F/G/H/A-numbered is
already FIXED; this sequences what remains.

## Ordering principles

1. **Fix the instrument before you measure.** A live run is the only way to close the
   doc-verified gaps, and each run is expensive. Anything that changes what a run *records*
   must land before the run that would have been its first observation.
2. **Make a signal consumable before the run that depends on it.** An unread token is not a gate.
3. **One dogfood run closes several gaps at once** — the assembler cycle, the merge gate, and
   the handoff WRITE/READ protocol are all "verbs live-verified, prose doc-verified only".
   They share a single vehicle: a real 7-phase `/h-mad` feature.

## Constraint that shapes every fix

`invariants.base.md` §"Audit-gate signal discipline": any gate whose verdict the orchestrator
consumes MUST report PASS/FAIL as a **stdout token with exit 0**. Non-zero exit is reserved for
operational errors, because a non-zero exit registers as a Claude Code `PostToolUseFailure` and
leaks into coexisting plugins. So no remediation below may "fix" a weak signal by making it exit
non-zero. Signals get *canonical tokens* and *mandated reads*.

---

## Wave 1 · Instrumentation — `audit_cycles` counter (B1)

**Blocks:** every later verification that would cite a cycle count. Must be first.

`h_mad_state_write.py:53` seeds `{"plan":0,"design":0,"impl_plan":0}`; nothing anywhere
increments it. `h_mad_telemetry.py:46-58` reports the zeros faithfully. Measured on HemaSuite
`clinical-abbreviation-hygiene`: recorded 0/0/0, actual 1/2/2. Knock-on: the drift warning at
`h_mad_telemetry.py:122` (`audit_cycles > 3` → "possible plan/design quality drift") can never
fire, and `references/state-schema.md:18` documents non-zero values the code cannot produce.

- Wire an increment at the single place an audit cycle completes (the gate-verdict consumption
  point), not at N call sites — one writer, per the single-source base invariant.
- Add a regression test asserting the counter advances across two cycles of one phase.
- Verify the telemetry drift warning can fire by feeding a synthetic 4-cycle state.

**Done when:** a two-cycle plan audit records `plan: 2`, not `0`.

## Wave 2 · Signal consumability — preflight tokens (G-c)

**Depends on:** nothing. **Blocks:** Wave 3 (the run should exercise the mandated reads).

`_cmd_env` prints `STALE` / `CONFLICT:` and returns 0 unconditionally. Correct per the signal
invariant — but no orchestrator step is *required* to read them, so a scripted
`hmad-dispatch env && dispatch …` still walks into a stale handle. That is exactly the failure
that lost a Task-2 RED dispatch on HemaSuite: no error, no report, no tests written.

- Give `env` a canonical terminal token line — `PREFLIGHT: PASS` / `PREFLIGHT: FAIL` — matching
  the `GATE:` / `ASSEMBLE:` shape already in use. Exit stays 0.
- Add the mandated read to `SKILL.md` Phase-5 preflight: the orchestrator asserts
  `PREFLIGHT: PASS` before the first dispatch of a run, and re-asserts after any re-pin.
- `ASSEMBLE: PASS|HALT` already complies; it needs only the same mandated-read step
  (`SKILL.md` §"Audit prompt assembly" 7.2).

**Done when:** a stale pin makes the Phase-5 preflight step fail the checklist, not just print.

## Wave 3 · Dogfood run — closes G-b + G-d

**Depends on:** Waves 1–2 (they are the payload). **Vehicle:** run `/h-mad` on the Wave-1+2
work itself.

Closes two standing gaps in one pass:
- **G-b** — one full audit cycle through `h_mad_assemble_audit.py`. Today all three phases are
  smoke-tested but only the *plan* recheck was ever dispatched to a live reviewer.
- **G-d** — the merge-gate and handoff WRITE/READ *protocol* paths (skill prose driving the
  verbs). The verbs are live-verified; the prose that drives them is not.

Expect `audit_cycles` still 0/0/0 for this run — the counter lands at the end of it. That is
fine and expected; Wave 4 is the first run that should show a real number.

**Done when:** design and impl-plan audits were both dispatched live through the assembler, and
a real merge gate blocked and resolved.

## Wave 4 · Candidates batch, dispatched via worktree fanout — closes G-a + confirms B1

**Depends on:** Wave 3. **Why combined:** the candidates decompose into independent,
non-conflicting files — the natural payload for the parallel fanout that has never run live.

Fanout target (G-a): `worktree-create → dispatch → await → merge → rm` is stub-tested only; no
real Orca-hosted-agent run has exercised it. Needs ≥2 independent modules and 2 live agents —
this batch supplies both.

Payload, triaged by kind:

**Discipline → `invariants.base.md` (Axis B).** These two are the exact failure modes that bit
both repos repeatedly; they belong in the rubric that audits read, not in prose:
- `verify-the-mutation-not-the-command` (recurrence 3) — re-read resulting state after any
  git/shell mutation; caught two silent zsh no-ops that both looked like success.
- `replay-the-incident-against-the-fix` (recurrence 4) — validate against the historical data
  that motivated the fix, not only unit stubs; caught a wrong heuristic that unit tests passed.

**Tooling → scripts:**
- `file-issue-then-fix-under-TDD` (recurrence 14, verdict yes) — the highest-recurrence
  candidate on the list.
- `staged-prompt repair sweep` (2, maybe) — rewrite stale `/tmp/audit_*.txt` to current
  template output, with backups + an in-flight freshness guard.
- `throwaway stub-harness probe` (2, maybe) — scratch pytest importing dispatch-test helpers to
  confirm a suspected resolver hole before fixing it.

**Prose notes → `SKILL.md`:**
- `worktree-for-live-skill-edits` (2) — edit a symlinked live skill in a worktree so an
  in-flight run keeps reading the merged tree.
- `sanitize-before-public-filing` (2) — grep issue bodies against a forbidden-term list
  (project names, slugs, local paths) before filing publicly.

**Done when:** the fanout completed against live agents, and `h_mad_telemetry.py` reports a
non-zero `audit_cycles` for this feature — the end-to-end proof of Wave 1.

## Wave 5 · Blocked upstream — watch only

**[stablyai/orca#9870](https://github.com/stablyai/orca/issues/9870)** — per-terminal identity.
Orca exposes no field naming the running program: Codex's `.title` is its cwd basename, its
preview banner decays once it works, and `terminal rename` returns `{"ok":true}` while `.title`
is unchanged. Mitigations shipped and durable — `hmad-dispatch launch <agent>` captures the
handle at t=0 from the create response; `pin`/`pin-agents` fail loud for an operator-launched
pane. When #9870 lands, delete the heuristics in `_orca_find`
(`h-mad/scripts/hmad-dispatch.sh:131-275`) and resolve on the real field.

Nothing else waits on this. Do not sequence work behind it.

---

## Explicitly dropped

- **Stale cmux surface map** — already fixed. `hmad-dispatch.sh:77-87` does title-token matching
  with n-candidate ambiguity and a fail-loud pin message; the hardcoded `codex→surface:5` /
  `agy→surface:2` no longer exists.
- **`ASSEMBLE: HALT` exits 0** — deliberate, documented at `h_mad_assemble_audit.py:13-17` and
  required by the signal-discipline base invariant. Not a defect.
- **`hmad-dispatch env` stale-pin bug** — FIXED by `912b93a`; the HemaSuite handoff's
  "file upstream" step is obsolete for this half.
- **Plan-doc `status:` frontmatter** — deferred. `docs/01-plan/features/*.plan.md` carries none,
  so the handoff scout surfaces no backlog signal, but those are HemaSuite-facing product plans,
  not this repo's work.

## Sequence at a glance

| Wave | Work | Closes | Gate to next |
|---|---|---|---|
| 1 | `audit_cycles` counter | B1 | counter advances in a test |
| 2 | `PREFLIGHT:` token + mandated reads | G-c | stale pin fails the checklist |
| 3 | dogfood `/h-mad` on Waves 1–2 | G-b, G-d | design + impl-plan audited live; merge gate exercised |
| 4 | candidates via worktree fanout | G-a, candidates, B1 proof | fanout ran live; telemetry non-zero |
| 5 | watch #9870 | H4/H5 residual | upstream |
