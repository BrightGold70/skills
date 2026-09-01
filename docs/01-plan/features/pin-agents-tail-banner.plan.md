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

**The tail pass uses its OWN matcher, `_agent_tail_re`, for BOTH the wanted and the rival check.** `_agent_pv_re` is left untouched — it is shipped and shared with Passes 1-2 — and the tail pass
does NOT wrap it: `_agent_tail_re` carries its own bounded, line-complete grammar per agent
(a banner must consume its line, allowing only a dotted-numeric version, a `model:` field, an
effort word, a `·` and a cwd, or an effort/version parenthetical). Rival rejection in this pass
uses that same helper rather than the `$rival_re` computed for Pass 1, or a real agent pane is
suppressed for merely mentioning the other agent. **The claim that it is "hardened against prose" was FALSE and
load-bearing**: impl-plan audit v26 matched `Release notes for OpenAI Codex are available`,
`I am comparing model: gpt-5.6-terra with ours`, `The Antigravity CLI documentation changed` and
`Compare Gemini 3.1 Pro with Claude` against it, 4 for 4, and a 7-probe corpus reproduced it.
Since `$scoped` includes ordinary shell panes and tail evidence is historical, a shell that once
printed release notes was resolvable AS THE AGENT — the wrong-pane class FR-2 forbids. The regex
is hardened against the two examples that motivated it, and that was generalised into a safety
premise it does not support. Measured over 24 prose probes and 12 real banner/status lines: the shipped helper declines 0,
this grammar declines all 24, and all 12 positives still match (impl-plan AC-3.17). Both regexes were verified against the REAL panes on
2026-09-01:
`openai codex|model: *gpt-|…` matches the codex tail (`OpenAI Codex`), and
`antigravity cli|gemini [0-9]` matches the agy tail (`Antigravity CLI 1.1.22`,
`Gemini 3.1 Pro (High)`). The work is running a TAIL-ONLY matcher, `_agent_tail_re`, against
`.tail` — not the existing helper, which matches prose 24/24 — instead
of `.preview`. An earlier check of this against a hand-written reconstruction reported
"agy: NO MATCH" and was wrong — the reconstruction is not the production surface.

**What matches is the BANNER line, not the launch line** (spec v1.5 §Measured basis 3). Both
claims above are about the tail *as a whole*, which on a real pane carries both. Measured
separately with controls: `codex '--dangerously-bypass-approvals-and-sandbox'` and
`agy '--dangerously-skip-permissions'` are NO MATCH for their own agents. Do not read the
paragraph above as licensing a launch-command-only fixture.

**The read command, in full.** Each candidate is read with

    _cmd_run --timeout <s> -- orca terminal read --terminal <handle> --cursor 0 --limit <n> --json

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
it. Call `_cmd_run --timeout <s> -- <cmd…>` IN-PROCESS (exit 124 at the deadline). `_cmd_run` is
the function `main` dispatches the `hmad-dispatch run` verb to, so it is the same bounder with
the same convention; naming the verb instead would, taken literally, re-exec the wrapper by
name, which is not on the test harness's `PATH` (`_bindir:/usr/bin:/bin`) and costs a process
per candidate. If no time-bounder is reachable, halt rather than issuing an unbounded read.

Rival rejection follows Pass 1's SHAPE rather than reinventing the idea, but not its matcher —
it uses `_agent_tail_re` for the rival too (see above), because Pass 1's `$rival_re` is the
prose-unsafe shared helper. A candidate carrying the
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
| Time-bounded read via in-process `_cmd_run --timeout` | shell call form | FR-4 |
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
| A `terminal read` hangs and stalls every resolution | Medium | Bound it with in-process `_cmd_run --timeout <s> --` (NEVER an INVOCATION of `timeout`/`gtimeout`, forbidden unconditionally by the base invariant; naming them in prose is free); an unreadable candidate is excluded, and all-unreadable declines |
| Reading tails on every resolution becomes a per-call cost | Low | Conditional on 0 or >1 survivors; a clean Pass 0/1 reads nothing |
| A rival's banner in scrollback selects the wrong agent | High | Rival rejection before counting (AC-2.3) |
| The TUI/alt-screen assumption is wrong on some agent | Medium | It is an inference from n=3, stated as an assumption in the spec; if false the pass declines more often, which is safe |

## Convention Prerequisites

- Feature branch off `main` at Phase 5c; `main` is currently clean and pushed.
- The suite is `pytest` at the repo root (`pytest.ini` testpaths, 2538 tests as of `7c6499c`).
- Anchor sweep must stay `ANCHORS_OK`; the pre-push hook enforces it.
- Live verification runs against the real Orca runtime — the panes used must be closed.
- RED-before-GREEN per the base invariant on test discrimination — **per node, NOT blanket.**
  Each new test is either observed to FAIL against the unfixed wrapper, or is a legitimately
  green-at-RED node tied to a named mutation that must be killed by that specific node. State the
  expected per-node failing/passing counts in the 5d dispatch so an unexpected result halts.
  **"Confirm each new test fails" was the wording here until impl-plan audit v19**, and it is
  unsatisfiable: preservation and negative nodes ("the legacy stub path is unchanged", "zero
  matches decline", "no read is issued when Pass 0 resolved", "frontmatter unchanged") pass
  before any code exists. An implementer following it would demand a blanket RED and trigger
  `step5d:red_not_all_failing` on a correct dispatch. The Success Criteria below and the design
  and impl-plan all state the per-node contract; v1.7's history claimed this rule had been
  back-propagated out of the plan, and it had not been — the claim lived in the changelog while
  the instruction stayed in the body.

## Success Criteria

- All 16 ACs pass automated tests (AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-2.1, AC-2.2, AC-2.3, AC-3.1, AC-3.2, AC-3.3, AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-5.1, AC-5.2 — counted from the spec by the
  ROW-ANCHORED derivation

      grep -oE '^ *- AC-[0-9]\.[0-9]' <spec> | grep -oE 'AC-[0-9]\.[0-9]' | sort -u | wc -l

  never carried; **this line has now been stale three times**, the third when spec v1.5 added
  AC-5.2 and this count was not swept. Re-run the command; do not read the number above.
  **The anchor is load-bearing and the unanchored `grep -o 'AC-[0-9]\.[0-9]' | sort -u` this
  bullet used to prescribe is wrong**: it counts every AC id the spec *mentions*, including
  IMPL-PLAN ids quoted in the spec's own version history. Measured 2026-09-01 — unanchored it
  returned 16 against 14 defined, the two extras being `AC-2.7` and `AC-3.5` in history prose,
  one of them written by the very entry recording this fix. A derivation that a document's own
  changelog can inflate is not a derivation. The impl-plan learned this at its v1.7 and anchored
  both of its RED-count commands; this one was missed.)
- **Every new test is either observed RED against the unfixed code, or carries a named
  reject-direction proof.** A test that passes against the code it was written to catch is
  decoration, and this feature is especially exposed to it: `cn == 1` already resolves today by
  OS evidence, so an AC-1.1 style test can pass with the change reverted. But a *blanket* RED
  requirement is unsatisfiable and would halt a correct 5d dispatch: preservation and negative
  nodes ("the legacy stub path is unchanged", "a launch-command-only tail does not resolve",
  "zero matches decline", "no read is issued when Pass 0 resolved", "frontmatter unchanged") are
  legitimately green before any code exists. Measured: **32 of 45 nodes RED, 13 green**, and the
  13 split **12 + 1**: twelve are each tied to a mutation that must be killed by that specific
  node, and the thirteenth, `test_tail_no_timeout_binary_invocation`, carries a
  procedure instead — insert `timeout 2 orca …`, observe RED, remove (impl-plan AC-2.8). This
  line said "each of the 11" while the count beside it said 12, leaving the twelfth node with no
  stated proof on the surface that is the declared source; impl-plan audit v24. RED observation OR a
  discriminating mutation is what distinguishes new coverage from a restatement of current
  behaviour — one or the other, never neither
- Each ENUMERATED mutation target is stubbed to its permissive value, and each mutant is confirmed to
  have LANDED — an anchor matching nothing reports the guard as enforced
- The mutation spec is ALL_CAUGHT
- **A live check that provably exercises THIS pass.** `hmad-dispatch env` resolving codex is NOT
  sufficient evidence: Pass 0, the title pass, the preview pass or an ambient pin each satisfy it
  with zero `terminal read` calls, so the check passes with the whole feature reverted. Require
  all four — (a) run against an **isolated** `HMAD_ORCA_PIN_FILE` (never the repository's real
  `.h-mad/orca-pins.env`, which holds the operator's live pins), **seed it with known dummy pins,
  confirm they are there**, then `pin-agents --clear` and **re-read the file** and confirm those
  handles are gone. Absence is evidence only where presence was established first — on a fresh
  path the file is absent whether or not the clear ever ran. Verifying that no
  `HMAD_ORCA_*_TERMINAL` is exported checks a DIFFERENT surface from the one `--clear` mutates,
  and a surviving file pin short-circuits `_orca_find` exactly as an exported one would; (b) the
  earlier passes shown not to resolve on their own — `worktree ps` does not name the pane, title
  and preview do not match; (c) `env 2>&1` carrying `bound <handle> by tail evidence`, the marker
  only this pass emits; (d) any pane created for the check closed AND the removal confirmed by
  re-listing terminals. The isolated pin file's `mktemp -d`
  directory is removed in the same step, **and its absence re-read to confirm the removal
  landed** — deleting a directory mutates state, so the command is not its own proof.
- Full suite green, anchors OK

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
- v1.9: Impl-plan audit v15 (codex) — every must-fix was a correction recorded only where it was FOUND, never on the paired surface. The counts were stale on SIX live sites across three docs (37 where the table now derives 38, 26/11 where it derives 27/11, 'T5's three' where T5 has four). The design still prescribed a subprocess 'hmad-dispatch run' and an untyped .result.terminal.tail, so an implementer following the cited source would have produced exactly the code path T2 rejects - the in-process _cmd_run call and the measured ARRAY shape are now IN the design. The plan's Success Criteria and the design's live check still required only that env resolve codex, which Pass 0 or an ambient file pin satisfies with zero terminal reads; both now carry the pin-FILE re-read (checking the environment is a different surface from the one --clear mutates), earlier-pass blindness, the tail-evidence marker and a cleanup re-list. AC-5.5 gained its exact old/new phrases and test body; _orca_read_dir now makes a fresh directory per call, since mkdir(exist_ok=True) let a previous call's handle file serve a handle the caller deliberately OMITTED. Audit-side note: the reviewer ran the wire-pin gate, which auto-registers and rewrote the wires.jsonl timestamp - it disclosed the mutation rather than reverting it, and the timestamp-only churn was discarded here.
- v1.10: Impl-plan audit v16 (codex) — two corrections, both on surfaces that contradicted the implementation contract. The read command, the portable-bounder paragraph, the deliverables row and the risk row all still prescribed `hmad-dispatch run --timeout` as a subprocess, which taken literally re-execs the wrapper by name — not on the test harness's PATH and a process per candidate — while T2 and the design require the in-process `_cmd_run`; all four now say `_cmd_run`, naming the verb only to identify which bounder. Separately, a WEAK duplicate live-check criterion sat below the strong four-part one and required only that `env` resolve codex and that a created pane be closed — satisfiable by Pass 0 or an ambient pin with zero `terminal read` calls, i.e. with the whole feature reverted. Deleted rather than strengthened: the strong criterion two bullets above already carries the pin-FILE re-read, and a document that states a gate twice at two strengths is read at the weaker one. Found while sweeping, not by the audit: the AC-count derivation this bullet prescribes was UNANCHORED (`grep -o 'AC-[0-9].[0-9]' | sort -u`) and counts every AC id the spec merely mentions, impl-plan ids in the spec's own version history included — measured 16 against 14 defined, and one of the two extras was written by the history entry recording this very fix. Now row-anchored. The count itself was correct; the command that was supposed to prove it was not, which is the worse of the two failures because it is the one that outlives the sweep.
- v1.11: Impl-plan audit v19 (codex) — node counts re-derived to 28 FAIL / 11 PASS over 39 after AC-2.9 was added (an exit-0 `ok:false` envelope was being accepted as identity evidence). Convention Prerequisites also still carried the blanket-RED instruction that v1.7's history claimed had been back-propagated out; swept to the per-node contract.
- v1.12: Impl-plan audit v20 (codex) — node counts re-derived to 29 FAIL / 11 PASS over 40 and the AC count to 15, after AC-2.10 rejected non-array tail payloads (a malformed payload containing a banner was becoming identity evidence, the same unsafe direction AC-2.9 closed for `ok:false` envelopes).
- v1.13: Impl-plan audit v21 (codex) — `// empty` is no longer described as an independently load-bearing guard; since the type branch ends `else empty` it is redundant defence in depth, measured identical with and without it, and the mutation that claimed to pin it was equivalent and has been removed.
- v1.14: Impl-plan audit v22 (codex) — the live-check criterion now requires an ISOLATED pin file that is SEEDED with known dummy pins before clearing. It previously sent the operator at the repository's real `.h-mad/orca-pins.env`, and the isolation fix that corrected that landed only in the impl-plan; on a fresh path, absence before and after proves nothing about whether the clear ran.
- v1.15: Impl-plan audit v23 (codex) — node counts re-derived to 28 FAIL / 12 PASS over 40 after AC-1.5 was reclassified green at RED: it tests only test-file helpers that T1's own RED patch introduces, so it cannot be observed failing.
- v1.16: Impl-plan audit v24 (codex) — the green-at-RED accounting said "each of the 11" beside a count of 12, leaving the twelfth node's reject direction unstated on the declared source. It is 11 + 1: eleven mutation-backed nodes, and `test_tail_no_timeout_binary_invocation`, whose proof is impl-plan AC-2.8's insert/observe/remove procedure. The live check also now removes the isolated pin file's `mktemp -d` directory.
- v1.17: Impl-plan audit v25 (codex) — the live check's `mktemp -d` cleanup now requires re-reading the path to confirm the directory is gone. Removing a directory mutates state, so the command is not its own proof; `rm -rf` on a path that was never created succeeds silently.
- v1.18: Impl-plan audit v26 (codex) — the 'hardened against prose' premise was FALSE and load-bearing. `_agent_pv_re` matches ordinary prose about the agents (7/7 probes), so with `$scoped` covering shell panes and tail evidence being historical, a shell that printed release notes was resolvable as the agent. The tail pass now anchors the matcher to line start (0/7 prose, 7/7 real banners); the shared helper is unchanged. Node counts re-derived to 29 FAIL / 12 PASS over 41.
- v1.19: Impl-plan audit v27 (codex) — the line anchor alone did not close the prose class: line-LEADING prose still matched, because the v1.18 corpus only contained mid-sentence shapes. The tail pass now applies a banner grammar (14/14 prose declines, 11/11 real banners still match). Counts re-derived to 30 FAIL / 12 PASS over 42, and the AC list gains spec AC-1.4.
- v1.20: Impl-plan audit v28 (codex) — the prose rule is now LINE-COMPLETE (19/19 decline, 12/12 real banners match) after prose following a banner-like prefix defeated the previous form, and the rival check uses the same tail-only grammar: it had been reusing the shared prose-unsafe matcher, so a real agent pane was suppressed for merely mentioning the other agent. Counts re-derived to 31 FAIL / 12 PASS over 43.
- v1.21: Impl-plan audit v29 (codex) — prose corpus re-enumerated at 24 negatives / 12 positives after a fourth shape (markdown headings and hyphenated pseudo-versions) defeated the line-complete form; the counts had drifted apart across four documents and are now derived from one list.
- v1.22: Impl-plan audit v30 (codex) — counts re-derived to 31 FAIL / 13 PASS over 44 after AC-4.6 was reclassified green at RED and the tail matcher moved to Task 2; the mutation-coverage claim narrowed to enumerated targets.
- v1.23: Impl-plan audit v31 (codex) — this document still prescribed the REJECTED matcher: a line-start wrapper around the shared `_agent_pv_re`, and rival rejection 'reused from Pass 1'. Both are the prose-unsafe path; the tail pass uses `_agent_tail_re`, with its own bounded per-agent grammar, for the wanted AND rival checks. Green-at-RED split corrected to 12 + 1 against the count of 13.
- v1.24: Impl-plan audit v32 (codex) — 'the work is running the EXISTING helper against `.tail`' was still the headline description of a feature that no longer does that; corrected to the tail-only `_agent_tail_re`. Green-at-RED split corrected to 12 + 1 against the count of 13.
- v1.25: Impl-plan audit v33 (codex) — the green-at-RED proof map assigned the AC-2.8 procedure to 'the twelfth' node immediately after stating twelve are mutation-backed, leaving the thirteenth unaccounted; it is the thirteenth. Counts re-derived to 32 FAIL / 13 PASS over 45.
