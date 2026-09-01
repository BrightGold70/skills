# Plan: pin-agents-tail-banner

## Executive Summary

Add one final, bounded identity pass to `_orca_find` that resolves an agent from its pane's
tail signature when — and only when — exactly one candidate matches.

## Overview

`_orca_find` has **four** passes and all four can miss the same pane: Pass 0's `paneKey` join
needs Orca to have adopted the pane, Pass 1's title is inherited for codex by construction,
Pass 2's preview banner decays once the pane works, and Pass 3 (J18) can prove the agent
PROCESS is alive but declines whenever more than one candidate pane could hold it. The result is `UNRESOLVED` beside a
live pane, and the documented remedy is a manual `pin`. This matters now because the carry
fix in `7adfce6` stopped the *pin file* losing a live handle, but left auto-detect itself
blind — this is the other half of that defect.

## Scope

Resolution only, inside the orca branch of `_orca_find`. No verb gains or loses a flag, the
pin file format is untouched, and cmux is unaffected. The user-visible change is that
`env`, `resolve`, `verify`, `send` and `pin-agents` report a handle in a case that
previously reported `UNRESOLVED`.

## Goals

- Resolve an agent whose only remaining evidence is its pane tail — FR-1
- Never resolve to the wrong pane — FR-2
- Cost nothing when the existing passes already succeed — FR-3
- Treat unreadable evidence as absence of evidence, not as a non-match — FR-4
- Record the measured retention limit where the pass lives — FR-5

## Requirements

- FR-1: a tail-signature pass resolves an otherwise-unresolvable agent
- FR-2: resolves only on exactly one match
- FR-3: runs only when earlier passes did not settle it
- FR-4: unreadable evidence declines rather than guesses
- FR-5: the retention limit is documented at the pass

## Implementation Strategy

**A standalone tail-evidence pass, after Pass 2 and BEFORE Pass 3.** An external source
review (2026-09-01, `EVIDENCE: PASS tools=4`) confirmed every factual claim below and
returned `DRIFT` on the earlier plan's placement, correctly: putting the check inside Pass
3's `cn > 1` branch **couples a text check to OS evidence**, so the tail would never be read
on a machine without `lsof` (`_agent_procs_in` returns rc 2 there, and Pass 3 is gated on
rc 0). That objection stands.

Its proposed remedy — fold it into Pass 2 — does not, and the difference matters: **Pass 2
is gated on `n == 0`**, so a title that matched TWO panes skips Pass 2 entirely and falls to
Pass 3. That is not hypothetical; this machine currently has two panes titled `agy`. A
finding can be right about the defect and wrong about the cure, and both halves are recorded
here so the next reviewer does not relitigate a settled point.

So the pass is its own step, placed after Pass 2 and before Pass 3, and it runs whenever the
candidate set is unresolved — **0 or >1 survivors** — over `$scoped`, gated on neither
`n == 0` nor `lsof`. Before Pass 3 because tail evidence NAMES THE AGENT for a specific pane,
while OS evidence only proves a process exists somewhere in the worktree and cannot say which
pane holds it; the pane-specific signal should be tried first, and Pass 3 remains the fallback
when no tail matches.

**Tail evidence is historical, not a liveness proof** (spec v1.5 AC-5.2). It says what a pane
ONCE ran; below the 2000-line cap an exited agent's banner survives and still resolves. Accepted
deliberately — Pass 1 (title) and Pass 2 (preview) are not liveness-gated either, so this adds no
new failure class, and a liveness gate would need `lsof` and contradict AC-3.3. Only Pass 0 and
Pass 3 (OS evidence) carry liveness.

**No new signature constants.** `_agent_pv_re` already returns per-agent regexes hardened
against prose, and both were verified against the REAL panes on 2026-09-01:
`openai codex|model: *gpt-|…` matches the codex tail (`OpenAI Codex`), and
`antigravity cli|gemini [0-9]` matches the agy tail (`Antigravity CLI 1.1.22`,
`Gemini 3.1 Pro (High)`). The work is running the EXISTING helper against `.tail` instead
of `.preview`. An earlier check of this against a hand-written reconstruction reported
"agy: NO MATCH" and was wrong — the reconstruction is not the production surface.

**What matches is the BANNER line, not the launch line** (spec v1.5 §Measured basis 3). Both
claims above are about the tail *as a whole*, which on a real pane carries both. Measured
separately with controls: `codex '--dangerously-bypass-approvals-and-sandbox'` and
`agy '--dangerously-skip-permissions'` are NO MATCH for their own agents. Do not read the
paragraph above as licensing a launch-command-only fixture.

**The read command, in full.** Each candidate is read with

    hmad-dispatch run --timeout <s> -- orca terminal read --terminal <handle> --cursor 0 --limit <n> --json

and matched against `.result.terminal.tail`. **`--cursor 0` is load-bearing, not decoration**:
without it the call returns the most recent rows, and the agent's banner sits at the START of
scrollback. On the panes measured today that would still work by accident — their entire
scrollback is 12-18 lines, so tail and head coincide — which is exactly why a naive read would
pass a live check and fail later on a pane with real history. `.result.terminal.tail` is the
field name; `.content`/`.output`/`.preview` are absent and reading them returns nothing in a
way that looks identical to an empty pane.

**The read must be time-bounded with the portable bounder.** `timeout`/`gtimeout` are
forbidden unconditionally by the base invariant — neither is a macOS system component, so
the form fails at 127 where coreutils is absent and silently works where someone installed
it. Use `hmad-dispatch run --timeout <s> -- <cmd…>` (exit 124 at the deadline). If no
time-bounder is reachable, halt rather than issuing an unbounded read.

Rival rejection is reused from Pass 1 rather than reinvented: a candidate carrying the
other agent's signature is dropped before counting, so it cannot be selected and cannot
manufacture the ambiguity that would suppress a correct resolution.

We deliberately do not touch `pin`, `pin-agents`, the pin file, or Passes 0–2.

## Architecture Considerations

- **The exactly-one rule is the safety property, not a nicety.** A wrong-but-live pin
  passes every liveness check the wrapper has and leaks dispatches into a stranger's shell.
  Declining is always available and always cheaper than being wrong.
- **Ordering is a cost decision with a correctness consequence.** Living inside Pass 3
  means a clean Pass 0/1/2 issues no reads at all. It also means strong tail evidence never
  overrides a weak title match that already resolved — accepted, because overriding a
  settled resolution is a larger behaviour change than this feature is buying.
- **`cn == 1` with `lsof` present is already bound by OS evidence today**, so an AC
  asserting that shape may pass unchanged and must be checked against current behaviour
  before being counted as coverage. The new pass earns its keep on three shapes Pass 3
  cannot reach: an ambiguous title (>1, which never reaches Pass 2), any machine without
  `lsof`, and a live process whose pane count is >1.
- **`set -euo pipefail` is on.** A helper returning non-zero as an answer must be called in
  a condition context; the carry fix in `7adfce6` was broken exactly this way for an hour.
- **Two failure directions, one safe.** Unresolved costs a manual pin. Wrongly resolved
  costs a dispatch into someone else's shell. **Every ambiguous case must therefore resolve
  to UNRESOLVED — never to a candidate, and specifically never to "the first" one.** An
  earlier draft of this line said "resolves toward the first", meaning the first of the two
  failure directions above; an audit read it as "the first candidate" and filed it as a
  contradiction of FR-2. The intent was misread, but the sentence genuinely admitted a
  reading that licenses the exact defect this feature exists to prevent, so it is stated
  explicitly rather than defended.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| Standalone tail-evidence pass between Pass 2 and Pass 3 | shell function change | FR-1, FR-2, FR-3, FR-4 |
| Time-bounded read via `hmad-dispatch run --timeout` | shell call form | FR-4 |
| Retention-limit comment at the pass | code comment | FR-5 |
| Tests in `test_hmad_dispatch.py` covering resolve / ambiguous / rival / unreadable / not-reached | tests | all |
| `tests/mutation-specs/tail_signature_pass.json` | mutation spec | all |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| A shell-heavy pane exceeds the measured 2000-line retention cap and loses its signature | Medium — reverts to today's behaviour | Accepted and documented; fails to UNRESOLVED, never to a wrong pane |
| The pass fires on a pane an earlier filter deliberately excluded | High | Operate only on `$scoped`, which already excludes the caller's own pane and is the same set Passes 1-2 filter from; never widen it |
| Running before Pass 3 changes which evidence wins when both are available | Medium | Deliberate: a tail names the agent for a SPECIFIC pane, while OS evidence proves only that a process exists in the worktree and cannot say which pane holds it. Pass 3 still runs when no tail matches, so nothing that resolves today stops resolving |
| A pane whose agent EXITED still carries its banner below the 2000-line cap, so the pass resolves a dead agent's shell | Medium — a dispatch lands in a plain shell | Accepted and documented at the pass (spec AC-5.2): tail evidence is HISTORICAL. Passes 1 and 2 are not liveness-gated either, so this is no new failure class; a liveness gate would require `lsof` and contradict AC-3.3 |
| A `terminal read` hangs and stalls every resolution | Medium | Bound it with `hmad-dispatch run --timeout <s> --` (NEVER `timeout`/`gtimeout`, forbidden unconditionally by the base invariant); an unreadable candidate is excluded, and all-unreadable declines |
| Reading tails on every resolution becomes a per-call cost | Low | Conditional on 0 or >1 survivors; a clean Pass 0/1 reads nothing |
| A rival's banner in scrollback selects the wrong agent | High | Rival rejection before counting (AC-2.3) |
| The TUI/alt-screen assumption is wrong on some agent | Medium | It is an inference from n=3, stated as an assumption in the spec; if false the pass declines more often, which is safe |

## Convention Prerequisites

- Feature branch off `main` at Phase 5c; `main` is currently clean and pushed.
- The suite is `pytest` at the repo root (`pytest.ini` testpaths, 2538 tests as of `7c6499c`).
- Anchor sweep must stay `ANCHORS_OK`; the pre-push hook enforces it.
- Live verification runs against the real Orca runtime — the panes used must be closed.
- RED-before-GREEN per the base invariant on test discrimination: confirm each new test
  fails against the unfixed wrapper before implementing, and state the expected
  failing/passing counts in the 5d dispatch so an unexpected pass halts.

## Success Criteria

- All 14 ACs pass automated tests (AC-1.1, AC-1.2, AC-1.3, AC-2.1, AC-2.2, AC-2.3, AC-3.1, AC-3.2, AC-3.3, AC-4.1, AC-4.2, AC-4.3, AC-5.1, AC-5.2 — counted from the spec by
  `grep -o 'AC-[0-9]\.[0-9]' | sort -u`, never carried; **this line has now been stale three
  times**, the third when spec v1.5 added AC-5.2 and this count was not swept. Re-run the command;
  do not read the number above.)
- **Every new test is either observed RED against the unfixed code, or carries a named
  reject-direction proof.** A test that passes against the code it was written to catch is
  decoration, and this feature is especially exposed to it: `cn == 1` already resolves today by
  OS evidence, so an AC-1.1 style test can pass with the change reverted. But a *blanket* RED
  requirement is unsatisfiable and would halt a correct 5d dispatch: preservation and negative
  nodes ("the legacy stub path is unchanged", "a launch-command-only tail does not resolve",
  "zero matches decline", "no read is issued when Pass 0 resolved", "frontmatter unchanged") are
  legitimately green before any code exists. Measured: **26 of 37 nodes RED, 11 green**, each of
  the 11 tied to a mutation that must be killed by that specific node. RED observation OR a
  discriminating mutation is what distinguishes new coverage from a restatement of current
  behaviour — one or the other, never neither
- Each guard is mutation-tested to its permissive value, and each mutant is confirmed to
  have LANDED — an anchor matching nothing reports the guard as enforced
- The mutation spec is ALL_CAUGHT
- Full suite green, anchors OK
- A live check: `hmad-dispatch env` resolves codex on this machine without a manual pin,
  and any pane created for the check is closed

## Out-of-Scope (confirmed from spec)

- Env-overridable signature regexes
- Re-scanning the worktree by banner, ignoring earlier passes
- Any change to `pin`, `pin-agents`, or the pin file format
- Raising or working around the 2000-line retention cap

## Next Steps

Audit this plan (Phase 3 gate), then design (Phase 4).

## Version History
- v1.0: Initial plan draft.
- v1.1: Audit v1 fixes from pin-agents-tail-banner.plan.audit.v1 — name the portable time
  bounder for the tail read; plus three self-corrections from reading `_orca_find`: there
  are four passes not three, the work belongs inside Pass 3's `cn > 1` branch rather than as
  a new pass, and `_agent_pv_re` needs no change because its existing regexes match both
  agents' real tails.
- v1.2: Audit v2 fixes from pin-agents-tail-banner.plan.audit.v2 — AC count corrected 13 -> 12
  (counted from the spec); test-discrimination requirement made explicit in both Success
  Criteria and Convention Prerequisites, with the reason it bites here: `cn == 1` already
  resolves today, so a careless test passes with the change reverted.
- v1.3: Source-review DRIFT (all 5 factual claims confirmed; placement refuted). The pass
  becomes a standalone step after Pass 2 and before Pass 3, gated on neither `n == 0` nor
  `lsof` — the reviewer's coupling objection was right, its "fold into Pass 2" remedy was
  not, because Pass 2 is gated on `n == 0` and an ambiguous title never reaches it.
- v1.4: Audit v4 fix — the ambiguity rule is now stated as "resolve to UNRESOLVED, never to
  a candidate". AC count corrected 12 -> 13 in the same pass after AC-3.3 was added, the
  second time that line went stale; it now carries the command that produces it.
- v1.5: Audit v5 should-fix — the exact read command is named, with `--cursor 0` justified:
  omitting it returns the newest rows while the banner is oldest, and today's panes are short
  enough that the mistake would pass a live check and surface only on a pane with history.
- v1.6: Back-propagated from impl-plan audit v7 (codex) — the plan was the surface the value sweep missed twice over: its risk table still asserted a tail proves what a pane IS RUNNING, contradicting the stale-pane behaviour spec v1.5 accepted, and its Success Criteria still said 13 ACs after AC-5.2 landed (the THIRD time that line has gone stale, on a line that already told the reader never to carry it). Both corrected, plus a new risk row for the exited-agent pane.
- v1.7: Impl-plan audit v8 (codex) — four of five must-fixes were defects in v1.5's own RED table. It was written at AC granularity while --expect-fail counts TEST NODES: two nodes carried two ACs each, putting one node in both columns and double-counting another, so the counts could never have matched a pytest run. Recast as a 35-node enumeration with one RED outcome each (24 FAIL / 11 PASS). The claim that every green-at-RED node was mutation-discriminated was FALSE - six had no proof and two were named by mutations that cannot kill them; seven mutations added (17 total), AC-4.2 withdrawn as genuinely undiscriminable. AC-6.11 gained a real test node. The live check required only that env resolve codex, which Pass 0 or an ambient pin satisfies with the feature reverted; it now requires the tail-evidence stderr marker with pins cleared and earlier passes proven blind. Blanket-RED rule back-propagated out of the design and plan.
- v1.8: Impl-plan audit v12 (codex) — two of three must-fixes were defects in v1.8's own SIGPIPE fix. AC-4.5 was VACUOUS as written: a rival-only tail fails the wanted check first and never reaches rival rejection, and putting both banners early makes the WANTED check return 141, so the expected decline happens for a reason unrelated to the branch under test - it would pass against a build with rival rejection deleted. Measured both layouts on 240,068-byte tails; only rival-first-wanted-last discriminates (broken: wanted rc 0, rival rc 141; fixed: 0/0), and the AC now specifies that exact fixture. The RED counts were stale on FOUR non-history surfaces, not the three the audit named - it missed plan.md:178 - so the sweep found one more than the finding did; all now 37/11/26. The live check ran pin-agents --clear and then verified only the ENVIRONMENT, never re-reading the pin file the clear was meant to empty: it now records the path env prints and asserts on that file. AC-6.11 claimed an exact-string root assertion while prescribing not os.path.isabs, which any relative value satisfies.
