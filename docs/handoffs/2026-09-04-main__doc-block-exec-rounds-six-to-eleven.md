# Handoff — doc-block-exec 5b: rounds six through eleven, and decision Q measured

**Date:** 2026-09-04
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-04-main__doc-block-exec-5b-rounds-three-to-five.md (branch predecessor; every open item carried below)

## Session Summary

Ran **six full gating rounds** (design 87–91, plan 78–82, impl-plan 38–42), each on two surfaces,
with six author revision batches between them. **The gate was not met in any round.** Documents went
design v1.96→**v1.101**, plan v1.91→**v1.96**, spec v1.58→**v1.60**, impl-plan v1.40→**v1.45**;
eight commits pushed, **`f91a74b`** is HEAD. Outcome: **partial, but the loop is now understood.**
The union count plateaued (13 → 11 → ~10 → 12 → 8), and round ten diagnosed why: the residual
defects are **claims about the verification machinery, asserted rather than executed**. That became
**decision Q**, and round ten measured it — across three independent documents the unexecuted claims
*were* the findings and everything executed came back clean.

## Key Learnings

- **DECISION Q, and it is the session's central result.** Every stated property of a screen, control,
  sweep or probe — what it is immune to, what it cannot match, which side it reads, which branches it
  covers, what its zero means — is a **claim about code** and must be executed, never reasoned from
  the mechanism's design. Measured: plan 11 claims / 3 unexecuted → 3 musts; impl-plan 1 unexecuted →
  1 must; design ~25 checked / 6 unexecuted → must 4 + should 2. The correspondence is exact.
- **A revision can never be its own mutation range**, because its lines are uncommitted while the
  sentence describing them is being written. This is why design v1.100's falsification used the
  *previous* revision's range and still read as correct. Structural, not careless.
- **A control run over a COMPOSITE tests the composite, not its members** (decision O). One boundary
  repair was half-applied in **three consecutive revisions**, passing its control every time, because
  the control ran on the alternation where a healthy sibling covers a sick one.
- **A control's PUBLICATION must not change what it measures** (decision N). "The old fold scores 0
  on `never a census`" scored 3 — the control sentence wrote its own needle into the document.
- **An ABSENCE claim is a measurement** (decision G). A zero that is right by accident is a defect:
  say *why* it is zero and whether the reason is load-bearing or incidental.
- **Publish every count with its UNIT** (decision H). One grep yielded 22 occurrences / 19 lines /
  17 distinct pins / 8 distinct files — four true numbers for one figure.
- **The second surface was BROKEN, not low-value.** A stale agy pin cost three rounds of design
  coverage. After relaunch its first evidence-bearing run found an `os.open` mechanism defect
  (EISDIR/EOPNOTSUPP/ENXIO fire before any descriptor exists) that a 2809-test suite and two rounds
  of gating teammates all missed — invisible because the verdict is identical either way.
- **agy's dominant failure is scope/stamp/tense blindness — four occurrences.** It evaluates a
  figure that is scoped ("over the body"), stamped ("at `<sha>`") or dated (a Version History record)
  against the unscoped, current, present-tense tree. Reject the concern, keep the fact, re-measure at
  the sentence's own scope, sha and tense.
- **Authors overrode instructions four times and were right every time**, each announcing the
  override and offering the revert. The ledger freeze, two rejected findings, and a rejected
  should-fix. Ask for that behaviour explicitly: *if the brief contradicts the tree, file it.*
- **Every author closed its class wider than its auditor found it, five rounds running**, by sweeping
  **shape** rather than the quoted spellings — the ledger was five sites where the auditor found
  three; the absence-site denominator eight where it found six; the screen-two population six where
  it said four.
- **Six orchestrator errors, all caught by an agent or a later check, all the same species:** I
  applied less rigour to my own artifacts and tooling than I demanded of the documents. See
  §Open Items.

## Next Steps

1. **Round twelve** — cycles design 92 / plan 83 / impl-plan 43 at freeze `f91a74b`. Collect the
   teammate reports into `docs/` **before** dispatching any author (#38). Ask each auditor for its
   property-claims-shipped-versus-executed count; that is now a standing metric.
2. **Check the agy surface first** — `hmad-dispatch env`; if the pin is stale, `hmad-dispatch launch
   agy`, re-assert `PREFLIGHT: PASS`, and prove liveness with a **computed-answer** probe, never an
   echo probe. design c91 was hollow (tools=1) and impl-plan c42 timed out (tools=8) in round ten.
3. **When codex returns 2026-09-07 11:28**, flip the status and run one real-codex round before
   stamping anything —
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature doc-block-exec --set codex_status=available`
4. **If a round comes back clean on both surfaces at ONE commit:** `h_mad_audit_gate.py … --gated`
   per phase, then `h_mad_wire_pin_gate.py … --feature doc-block-exec`, then 5c
   `git checkout -b feature/doc-block-exec`. Claim `doc-block-exec` first with plain `--claim`.
5. **[P5] backlog** — #9's five unverified skill-candidate rows, #8's pytest agy-pane leak row,
   #5's 101 HemaSuite rows (foreign lane).

**The impl-plan precheck invocation, needed every round** (its eight PLACEHOLDER hits are output-line
grammar specimens; the `--allow` list is an INPUT, never inferred):

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py \
  docs/01-plan/features/doc-block-exec.impl-plan.md --phase impl-plan --root /Users/kimhawk/orca/skills \
  --allow 'stream: "<name>"' --allow 'os_error: "<text>"' --allow 'overlap: "<a>" "<b>"' \
  --allow '<key>=<bare>' --allow '<key>="<json-string>"' --allow 'pgid: "<n>"'
```

## Open / Blocked Items

- **doc-block-exec 5b — gate NOT met, nothing stamped.** design v1.101 / plan v1.96 / spec v1.60 /
  impl-plan v1.45 at `f91a74b`. Six rounds run this session, all FAIL. Ready for round twelve.
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
- **The claim on `doc-block-exec` is UNCLAIMED** — verified `enter_autonomous` at session start and
  never claimed. Verify with `h_mad_resume_decision.py` before claiming.
- **Codex quota — blocked until 2026-09-07 11:28.** Unchanged. The teammate substitution is the
  standing workaround and is gating by operator decision.
- **`doc-block-exec.codex_status` is still `exhausted`.** Unchanged. One switch, two effects: it also
  permits Claude to author 5d/5e production code. Flip before 5d.
- **No round this session can satisfy the exit gate**, and not only for the model-family reason:
  round ten's design leg was hollow and its impl-plan leg timed out. Rounds four and five remain
  disqualified from the predecessor.
- **THE STANDING LIMIT: every surface shares a model family with the authoring surface.** All six
  gating auditors volunteered this unprompted, and none has been scored against a labelled corpus.
  Nothing gated by a teammate is settled until a real codex round runs.
- **SIX ORCHESTRATOR ERRORS this session, recorded so they are not repeated** — dispatched four
  authors at report paths that did not exist (#38); froze a count the revision's own fix moved
  (#39, decision K); relayed a prescription impossible against the tree (#40, decision L); ran a
  verification grep against guessed phrasing (#41, decision M); carried a stale premise between
  briefs (#45, decision P); and **read in-flight empty verdict files as completed failures**, which
  was published into commit `68a70d6`'s message and withdrawn in `f91a74b`'s (#47). Three published
  figures were also wrong, all from running a **variant** of the shipped artifact and reporting its
  numbers as the artifact's: 21 vs 22, 3 vs 7 bare pins, 12/38 vs 9/32.
- **#13's evidence floor may be one call too low — MEASURE, do not raise it (#4).** plan c81 ran
  tools=3 with 35,677 thinking tokens, the same hollowness signature as design c87 (21,031 / 1). But
  plan c75 ran tools=1 and produced three verified-real must-fixes, so a raised floor would have
  refused that. A thinking-per-call ratio is the better proxy and every Effort block already holds
  the data to test it across the corpus.
- **INHERITED-UNVERIFIED register (#42)** — figures no round has re-run, kept explicit so that
  surviving N rounds unchallenged does not read as verified: the `2748`/`2486` floors at `b7d0d77`
  (four rounds stale; the 262 divergence *was* executed live at 2809/2547); the plan's 263/76/0 and
  268/76/0 heading differentials at `1861157`; the markdown-it-py 14-case grammar corpus; the
  `+2/+0/+0` collect probe's deltas. **AC-6.4's `2675` absolute is NOT REPRODUCIBLE** — its predicate
  was never published; the invariance is verified and the absolute is now labelled unverifiable.
- **`tree delta: N` cannot signal agent writes in this repo (#36)** — 55 untracked `.done` markers
  make its baseline never 0, so the documented "honest no-run = no verdict AND tree delta 0"
  heuristic cannot fire here. Check `git status --short` filtered of `.done`, plus `git log -1`.
- **Marker-aware reaping for `exec` — owed, deliberately not built.** Unchanged.
- **#27 deferred evidence check — unchanged.** Step 2 was measured and refused; no span-occurrence
  rule discriminates. Gate condition measured 2026-09-04: **26 of 660** audit reports carry `quote:`
  lines, 183 lines, split teammate 18 / p1 8. **Do not fit a rule on that split** — it is dominated
  by one model family. A real codex round would fill the thin arm.
  `docs/03-analysis/hmad-audit-evidence-gate.measurement.md`, commit `109a02a`.
- **Evidence-gate corpus lives OUTSIDE the repo and is not backed up** — `~/.h-mad-corpora/evidence-gate/`,
  66 files recursive, re-verified 2026-09-04. Unchanged.
- **#7 `docsections.py` `_fence_aware_end` dedupe — unchanged, not started.** Closes with 5e.
- **A HemaSuite skill-candidate row was HANDED OVER and remains theirs** — brief at
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md` (`f5afb219`).
  Not re-checked this session. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **#9 five skill-candidate rows still not individually re-verified — unchanged, not started.**
- **#5 (101 classified HemaSuite rows) and #8 (pytest leaks exec-pane agy panes) — unchanged.**
  #5 is a foreign lane.
- **`.claude/agents/` question remains CLOSED** — five agents tracked at `h-mad/agents/`, registered
  by user-scope symlink.
- **55 untracked `.done` markers** — deliberate, do not commit. Unchanged.

## Context for Next Session

**Files touched this session:**
- `docs/02-design/features/doc-block-exec.design.md` (v1.96 → v1.101)
- `docs/01-plan/features/doc-block-exec.plan.md` (v1.91 → v1.96)
- `docs/01-plan/features/doc-block-exec.spec.md` (v1.58 → v1.60)
- `docs/01-plan/features/doc-block-exec.impl-plan.md` (v1.40 → v1.45)
- 18 audit reports under `docs/01-plan/features/` and `docs/02-design/features/` (cycles 87–91,
  78–82, 38–42, `.teammate` and `.p1` surfaces)

**Uncommitted changes:** none besides the 55 `.done` markers (and this doc until committed).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env   # check for a stale agy pin
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q                 # bare python3 is 3.14, no pytest
grep -oE '^- v1\.[0-9]+' docs/02-design/features/doc-block-exec.design.md | tail -1   # re-derive, never trust a pin
```

**Related docs:**
- `h-mad/SKILL.md` §"Teammate audit leg", §"Precheck before you dispatch", §"Never gate on one audit
  pass", §"Close the class, never the instance"
- The eight commits: `6f0ee85` (round six), `8909ec4` (round seven), `cf3a862` (round eight audit),
  `7982c18` (round eight revisions), `4e4a00c` (round nine audit), `06ef40f` (round nine revisions),
  `68a70d6` (round ten audit + the Q measurement), `f91a74b` (round ten revisions)
- Decision sheets G–Q are in the session task list (#35, #39–#47) and in the commit messages above.
