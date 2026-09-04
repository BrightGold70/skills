# Handoff — doc-block-exec 5b: round twelve, and decision Q's fourth confirmation

**Date:** 2026-09-04
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-04-main__doc-block-exec-rounds-six-to-eleven.md (branch predecessor, written earlier today; every open item carried below)

## Session Summary

Continues the same session. Ran **one further gating round** (design 92 / plan 83 / impl-plan 43)
at freeze `6dcb70f`, on two surfaces, with no revision batch after it — that is the next session's
first task. **Union must = 5**, the lowest of the arc, and the trend since decision Q landed is
unambiguous: **13 → 11 → ~10 → 12 → 8 → 5**. Q's correspondence held a **fourth** time, on all three
documents at once: each document's *unexecuted* property claim was its must-fix 1. Two agy legs
returned clean (design c92 and impl-plan c43, `must=0 should=0` — design's first ever) while their
gating teammates found musts on both, which is the union working rather than failing. Documents are
unchanged at design v1.101 / plan v1.96 / spec v1.60 / impl-plan v1.45; HEAD is **`934dd91`**.

## Key Learnings

- **Decision Q is now measured four times and is the only intervention between the plateau and the
  fall.** Round twelve: plan 11 claims shipped / 10 executed / 1 unexecuted → and that one *is*
  must 1; impl-plan 1 unexecuted → must 1; design 21+ changed / 20 executed / ≥1 asserted → must 1.
  design's instance is exemplary: v1.101 added `zero` to the NUM-residual name set and **did not
  re-run that set's grep** — it returns 1, not the published 0. The conclusion survives, but by a
  route the document does not state.
- **`tools=N` and every Effort-block figure is UNVERIFIABLE from the repository** (#48). `audit-cycle`
  writes the verdict to `/tmp` and only the *report* is collected into `docs/`. The plan auditor
  reconstructed `tools=113` from the run log's tool-name occurrences (they appear **twice per call**)
  and stated plainly that *"the heaviest agy pass of the arc"* — my phrase, in two commit messages —
  cannot be checked from this repo. Every `tools=` figure I have written into the permanent record
  has that provenance. **This also blocks #4**, since the thinking-per-call ratio lives only in those
  uncommitted blocks.
- **Two clean agy legs are not a gate.** design c92 and impl-plan c43 both returned `must=0
  should=0`; their teammates found 2 and 1 musts respectively. One clean surface has never been the
  gate and this round is the clearest demonstration.
- **Auditors are now closing classes rather than filing instances, unprompted.** The plan auditor
  re-derived **all eleven** `docs/`-scoped `4e4a00c`-pinned figures to establish that the codex
  ledger was the only one that moved; the design auditor swept **all 36** raised lines at `cf3a862`
  to establish that its absence claim was the only one outside both stated carve-outs.
- **A number can be unrefuted while its derivation is falsified.** AC-6.4's `2675` survived ten
  variant predicates, none reproducing it. The impl-plan states the invariance as verified and the
  absolute as unverifiable, rather than substituting a number or deleting it. That is the right
  treatment and worth copying.

## Next Steps

1. **Round twelve's REVISION BATCH — this is the immediate owed work.** Union must 5 at freeze
   `6dcb70f`, reports committed at `934dd91`. Dispatch design, plan and impl-plan authors with one
   decision sheet in identical words; the spec has nothing routed. Each must is that document's own
   unexecuted property claim, so the instruction is narrow: **execute the claim, change nothing
   else.**
2. **Check the agy pin before the next audit** — `hmad-dispatch env`; if stale, `hmad-dispatch launch
   agy`, re-assert `PREFLIGHT: PASS`, and prove liveness with a **computed-answer** probe, never an
   echo probe. plan c83 returned `UNVERIFIED reason=no_report` this round and its `.p1.md` is absent.
3. **Commit the verdict files, or stop quoting `tools=` (#48).** Cheapest fix: `git add` the verdict
   as `<phase>.audit.v<N>.<surface>.verdict.txt` in the same commit as the report.
4. **When codex returns 2026-09-07 11:28**, flip the status and run one real-codex round before
   stamping anything —
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature doc-block-exec --set codex_status=available`
5. **If a round comes back clean on both surfaces at ONE commit:** `h_mad_audit_gate.py … --gated`
   per phase, then `h_mad_wire_pin_gate.py … --feature doc-block-exec`, then 5c
   `git checkout -b feature/doc-block-exec`. Claim `doc-block-exec` first with plain `--claim`.
6. **[P5] backlog** — #9's five unverified skill-candidate rows, #8's pytest agy-pane leak row,
   #5's 101 HemaSuite rows (foreign lane).

**The impl-plan precheck invocation, needed every round** (the eight PLACEHOLDER hits are output-line
grammar specimens; the `--allow` list is an INPUT, never inferred):

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py \
  docs/01-plan/features/doc-block-exec.impl-plan.md --phase impl-plan --root /Users/kimhawk/orca/skills \
  --allow 'stream: "<name>"' --allow 'os_error: "<text>"' --allow 'overlap: "<a>" "<b>"' \
  --allow '<key>=<bare>' --allow '<key>="<json-string>"' --allow 'pgid: "<n>"'
```

## Open / Blocked Items

- **doc-block-exec 5b — gate NOT met.** design v1.101 / plan v1.96 / spec v1.60 / impl-plan v1.45 at
  `934dd91`. Seven rounds run this session, all FAIL. **Round twelve's revisions are owed.**
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
- **The three round-twelve must-fixes, carried so the revision batch has them without re-reading:**
  design — the `zero` NUM-residual grep returns 1 not 0, and an unlabelled absence claim
  (`git show 35698f9:$D | grep -cF "tr '\n' ' '"` → 0) that is the only one of 36 raised lines
  outside both carve-outs; plan — the members list mislabels v1.93's five-row table as v1.94's and
  v1.94's OS-probe register as v1.95's, contradicting its own prose four lines above, **and** the
  codex ledger was carried at `4e4a00c` past the measurement commit (teammate half is **82** at
  `68a70d6`/`6dcb70f`, not 81); impl-plan — AC-6.4's `2675`, unrefuted but with a falsified
  published derivation.
- **The claim on `doc-block-exec` is UNCLAIMED** — verified `enter_autonomous` at session start,
  never claimed. Verify with `h_mad_resume_decision.py` before claiming.
- **Codex quota — blocked until 2026-09-07 11:28**, and **`codex_status` is still `exhausted`**.
  One switch, two effects: it also permits Claude to author 5d/5e production code. Flip before 5d.
- **THE STANDING LIMIT: every surface shares a model family with the authoring surface.** All nine
  gating auditors this session volunteered it unprompted, and none has been scored against a
  labelled corpus. Nothing gated by a teammate is settled until a real codex round runs.
- **No round this session can satisfy the exit gate.** Rounds four and five were disqualified by the
  predecessor; round ten's design leg was hollow and its impl-plan leg timed out; round twelve's plan
  leg returned `no_report`.
- **SEVEN orchestrator errors this session** — see the predecessor for six (#38 missing report paths,
  #39/K frozen count, #40/L impossible prescription, #41/M guessed phrasing, #45/P stale premise,
  #47 in-flight empties, plus three wrong published figures). The seventh is #48: writing `tools=`
  figures into commit messages that no reader can verify. All the same species — **less rigour on my
  own artifacts than I demand of the documents.**
- **#13's evidence floor may be one call too low — MEASURE, do not raise it (#4).** Blocked on #48:
  the data lives only in uncommitted Effort blocks.
- **INHERITED-UNVERIFIED register (#42)** — the `2748`/`2486` pair at `b7d0d77` (needs a checkout;
  the 262 divergence *was* executed live at 2809/2547); the plan's 263/76/0 and 268/76/0 CommonMark
  oracles; the markdown-it-py 14-case corpus; the `+2/+0/+0` collect probe's deltas; the five
  OS/runtime carve-out probes; **AC-6.4's `2675` predicate — ten variants tried, none reproduces it.**
- **`tree delta: N` cannot signal agent writes in this repo (#36)** — 55 untracked `.done` markers
  make its baseline never 0.
- **Marker-aware reaping for `exec`** — owed, deliberately not built. Unchanged.
- **#27 deferred evidence check** — measured and refused; no span-occurrence rule discriminates.
  Corpus at 2026-09-04: **26 of 660** audit reports carry `quote:` lines, split teammate 18 / p1 8.
  **Do not fit a rule on that split.** `docs/03-analysis/hmad-audit-evidence-gate.measurement.md`, `109a02a`.
- **Evidence-gate corpus lives OUTSIDE the repo and is not backed up** — `~/.h-mad-corpora/evidence-gate/`,
  66 files, re-verified 2026-09-04.
- **#7 `docsections.py` `_fence_aware_end` dedupe** — unchanged, not started. Closes with 5e.
- **A HemaSuite skill-candidate row was HANDED OVER and remains theirs** — brief at
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md` (`f5afb219`).
  Not re-checked. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **#9, #5, #8** — unchanged, not started. #5 is a foreign lane.
- **`.claude/agents/` remains CLOSED** — five agents tracked at `h-mad/agents/`, user-scope symlink.
- **55 untracked `.done` markers** — deliberate, do not commit.

## Context for Next Session

**Files touched since the predecessor handoff:**
- 5 audit reports under `docs/01-plan/features/` and `docs/02-design/features/` (cycles 92, 83, 43)
- 2 straggler round-ten agy reports (`plan.audit.v82.p1.md`, `impl-plan.audit.v42.p1.md`)
- No document changed: design v1.101 / plan v1.96 / spec v1.60 / impl-plan v1.45 are as at `f91a74b`

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
- `h-mad/SKILL.md` §"Teammate audit leg", §"Precheck before you dispatch", §"Never gate on one audit pass"
- Commits this segment: `6dcb70f` (straggler agy reports), `934dd91` (round twelve audit)
- Decisions G–Q live in the session task list (#35, #39–#48) and in the commit messages from
  `6f0ee85` onward.
