# Handoff — author subagents lose their OWED LIST to a ~4 KB transit truncation; the shipped mitigation saves the DONE line and not the body

**Date:** 2026-09-07
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session `4c403027-215f-45ab-bb87-d04619e228a5`
**Taken-Over-By:** skills · main · session e07f76b9 · 2026-09-07
**Supersedes:** none — first on this topic

## Session Summary

One item moves from the HemaSuite lane to this one: **the four h-mad author agents have no file
deliverable for their report, so the report body travels through a transport that truncates at
~4 KB, and what is lost is always the tail — the owed list.** Measured today on
`gateway-consolidation` cycle 105: **two of three** messages from a single `design-author` run were
truncated mid-word, and extracting one report cost **three** round-trips of `SendMessage`.

It belongs here because the fix is a two-line change to agent contracts that live in this
repository (`h-mad/agents/*.md`), and because **the symmetric contract already exists here** —
`doc-auditor` has a `REPORT` path and the authors do not. Nothing in this repository was touched by
the sending session. HemaSuite is not the right owner: it consumes these agents, it does not define
them.

## Key Learnings

- **The shipped mitigation works, and it is not this defect.** All five agent files carry a rule
  put in after r17 — *"Four r17 author reports were truncated before a trailing DONE and were read
  as unfinished, so the DONE line … is the FIRST line of your final message"*
  (`h-mad/agents/design-author.md:72-73`, and the same at `plan-author.md:72`, `spec-author.md:88`,
  `implplan-author.md:58`, `doc-auditor.md:192`). It targets **DONE-line loss** and it succeeded:
  in all three messages today the DONE line arrived intact and the run was never misread as
  unfinished. The body was still cut. **Do not read this brief as a report that the r17 fix
  regressed — it did not. It fixed a different failure.**

- **The asymmetry is the finding, and it is one line wide.** `h-mad/agents/doc-auditor.md:40`
  gives the auditor `` `REPORT`: path to write your report to `` and `:192` says *"your report file
  is the deliverable"*. The four author files have no such parameter; `design-author.md:120` says
  *"report short; the document is the deliverable"* — true of the **document**, but the report also
  carries the owed list, the declines with their reasons, and the verbatim text owed to sibling
  authors, none of which is in the document. So the auditor's body cannot be lost and the authors'
  body routinely is. Verified by reading all five files, not inferred from behaviour.

- **What is cut is never random.** Both cuts today landed mid-word inside the tail — at `"Restr"`
  (first item of a Declined list) and at `"naming the **ov"` (mid-bullet). The transport appends
  `[result truncated — ask the agent for the rest via SendMessage]`. The surviving half is always
  the part written first, and the h-mad report format puts the owed list last. Two structures
  compounding: a transport that truncates the tail, and a report convention that puts the load-
  bearing part there.

- **The recovery is not free and is not reliable.** Three round-trips, each one a full agent
  wake-up, and the second retry — explicitly scoped to "send ONLY the tail, under 15 lines" —
  **was itself truncated**. A retry is not a workaround when the retry is subject to the same limit.

- **Prior evidence agrees and is independent.** HemaSuite's memory records the same failure on
  2026-09-06: 3 of 3 authors, always at the owed list, with the ad-hoc mitigation "cap reports at
  ~60 lines, SendMessage the cut point for the tail only". Today's run followed that advice and
  still lost the tail twice. **The prose cap is not sufficient**; it lowers the rate, not the class.

## Next Steps

1. Read the two contracts side by side and confirm the asymmetry before designing anything:
   ```bash
   cd /Users/kimhawk/orca/skills
   /usr/bin/grep -n -i 'report file\|write your report\|REPORT`' h-mad/agents/doc-auditor.md
   /usr/bin/grep -n -i 'final message\|deliverable' h-mad/agents/design-author.md
   ```
   Expect `doc-auditor.md:40` and `:192` to have it and `design-author.md` to have nothing
   equivalent. If that is no longer true, this brief's premise has expired — say so and stop.

2. **The candidate fix, which is yours to accept or reject:** give the four author agents a
   `REPORT` path exactly as `doc-auditor.md:40` already defines one, and change their final-message
   contract to *DONE line + report path*, leaving the body on disk. The transport then carries a
   couple of hundred bytes and cannot truncate anything load-bearing. It reuses a contract that
   already exists in the same directory rather than inventing one.
   Files: `h-mad/agents/{design,plan,spec,implplan}-author.md`. The dispatching side is
   `h-mad/SKILL.md`'s author-dispatch sections, which must pass the path.

3. **Two things to check before adopting it**, both of which could sink it:
   - the orchestrator currently *reads* the author's prose report; moving it to a file means the
     orchestrator must read that file, so the token cost moves rather than vanishing — is that
     acceptable, or does the DONE line need to carry a summary too?
   - `doc-auditor`'s `REPORT` path is supplied by the dispatcher. Confirm the author dispatch sites
     can supply one without a scratchpad-path assumption that breaks under `isolation: worktree`.

4. Decide whether the rule belongs in the four agent files, in `h-mad/SKILL.md`'s dispatch
   protocol, or both. Today all five files carry the r17 rule as **duplicated prose**, which is the
   "four copies of one regex in four agent files" shape `design-author.md:56` already complains
   about.

## Open / Blocked Items

- **The truncation defect itself** — status: handed over, not started.
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`.
  Evidence lives in the sending session's transcript and in the two files named above; no artifact
  was written to this repository.

- **No claim was released, because none existed.** `h_mad_resume_decision.py --state
  ./docs/.bkit-memory.json --feature subagent-report-truncation` returns `start_fresh`. The store
  has 34 records and **one** owner.

- **`pin-agents-tail-banner` is owned by session `f70b9d62-a6d8-4e37-b68d-8841df077327`**,
  heartbeat `2026-09-02T02:44:21Z`, `current_phase=7`. Five days stale, so the oracle would not
  call it live — but it is **not part of this handover** and was not touched. Left exactly as
  found.

- **This repository was dirty when the brief was written**, and the sending session deliberately
  did not touch any of it: `h-mad/SKILL.md`, `h_mad_audit_gate.py`,
  `tests/mutation-specs/audit_{leg_set,suite}_gate.json`,
  `tests/test_h_mad_audit_{leg_set,suite}_gate.py` all modified, plus ~90 untracked `.done`
  markers under `docs/01-plan/features/` and `docs/archive/2026-09/`. Newest commit `070281b`.
  **If that work is live, this brief is the only thing the sender added** — a path-scoped commit of
  this file alone.

## Context for Next Session

**Files touched this session:** this brief only, in this repository.

**Uncommitted changes:** this brief, until committed — plus the six modified files and the
untracked `.done` markers listed above, which belong to whoever was working here and were left
alone.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
/usr/bin/grep -n 'REPORT' h-mad/agents/doc-auditor.md
/usr/bin/grep -c 'Four r17 author reports were truncated' h-mad/agents/*.md
```

**Related docs:**
- `h-mad/agents/doc-auditor.md:40,192` — the contract to copy.
- `h-mad/agents/{design,plan,spec,implplan}-author.md` rule 10 / rule 8 — the r17 mitigation that
  works and is not this.
- HemaSuite memory `feedback_subagent_reports_truncate_in_transit.md` — the 2026-09-06
  observation, 3 of 3 authors.
