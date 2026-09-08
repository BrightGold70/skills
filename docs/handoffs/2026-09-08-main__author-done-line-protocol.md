# Handoff — h-mad author agents: require line-count + sha256 on the DONE line, and gate on it

**Date:** 2026-09-08
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite-wsg · feature/website-source-grounding · session 4f2a4086-d303-4192-9769-097903f32bc7
**Taken-Over-By:** skills · BrightGold70/author-done-line-protocol · session 7654eb03-2e40-470f-ac28-086f58dce5fa · 2026-09-08
**Supersedes:** none — first on this branch for this item

## Session Summary

h-mad's author-agent protocol has no requirement that an author's `DONE` line carry the artifact's
line count and sha256, and no rule telling the orchestrator to gate on it. The protocol works today
only because the orchestrator hand-writes it into each dispatch prompt. A HemaSuite session ran five
author dispatches with it and verified all five, which is the evidence this brief carries. **Nothing
is claimed and nothing is in flight** — this is a specification gap, not a broken build.

**This is NOT GitHub issue #24 in this repo.** That number was fixed and pushed at `6f00f8c`
("a codex transcript is NOT MEASURED, never 'measured as zero'") and is unrelated. The sending lane
carried this item labelled "#24" from an older handoff, and the number collides across at least four
distinct things. Do not re-file it under a number.

## Key Learnings

- **Measured at `6f00f8c`, and this is the whole finding**: `grep -ciE 'sha256|line-count|lines='`
  over `h-mad/agents/{spec,plan,design,implplan}-author.md` and `h-mad/agents/doc-auditor.md`
  returns **0 for all five**, and `h-mad/SKILL.md` contains **zero** occurrences of either string.
  So the requirement is nowhere in the skill.
- **The REPORT= fix is a different fix and it DID land** (`96fca5f`, `1c45944`). Do not read the
  agents' `REPORT` path as evidence this shipped — they are adjacent and separate.
- **The failure this closes**: a subagent's "stopped writing" is an **instant, not a state**. A
  post-DONE dispatch from the orchestrator can invalidate the stop, so the only durable proof that
  the file on disk is the file the author reported is the sha the author itself computed. Echoing
  the sha into the log is not a gate; the gate is `|| exit 1`.
- **n=5, zero enforcement.** In one HemaSuite session, five author dispatches (`spec-author` ×1,
  `design-author` ×2, `implplan-author` ×1, `plan-author` ×1) each returned `sha256=` and `lines=`
  on the DONE line, and the orchestrator verified every one with
  `shasum -a 256 "$F" | awk '{print $1}'` compared against the reported value, gated `|| exit 1`,
  before committing. Five for five matched. One author (`design-author`, citation dispatch) went
  further and re-asserted ownership immediately before each write — `stat -f '%m'` plus the newest
  `- v1.N` Version History row — gated with `|| { echo OWNERSHIP-DRIFT; exit 1; }`, explicitly not
  `set -e`. That is the shape worth codifying.
- **`set -e` is inert in the Bash tool's top-level shell**, which is why every gate above is an
  explicit `|| exit 1` rather than a bare `test`. Any rule written into the agent files must use the
  explicit form or it will not fire.

## Next Steps

1. **Add the DONE-line contract to each of the five agent definitions** —
   `h-mad/agents/{spec,plan,design,implplan}-author.md` and `h-mad/agents/doc-auditor.md`. The line
   must carry the artifact path, its line count and its sha256, and it must come FIRST in the final
   message (SKILL.md §"Teammate authors" rule 4 already requires DONE-first because four r17 reports
   were truncated before a trailing DONE — this extends what that line must contain).
2. **Add the orchestrator's half to `h-mad/SKILL.md` §"Teammate authors"** — the collect step must
   re-derive the sha and compare, gated `|| exit 1`, BEFORE acting on the artifact or committing it.
   Rule 5 there already says to read `$RP` rather than the message; this is the same shape one level
   down: verify the artifact, do not trust the report.
3. **Decide whether `REPORT=<none>` weakens it.** An author that declares the body inline has no
   file to hash. Either require the DONE line to carry the sha regardless (it hashes the DOCUMENT,
   not the report), or state that the inline path is unverifiable and say so at the site.
4. **Mutation-test the guard, per h-mad's own rule.** A rule in a prompt is advice; the mutation that
   matters is an author DONE line with a WRONG sha — the orchestrator must refuse. Give the mutation
   a `test` key so a wrong-catcher is not scored as a kill.

## Open / Blocked Items

- **The specification gap itself** — status: not started, blocked on nothing.
  `repo: /Users/kimhawk/orca/skills · branch: BrightGold70/author-done-line-protocol · worktree: /Users/kimhawk/orca/workspaces/skills/author-done-line-protocol`
  Artifacts: `h-mad/agents/*.md` (5 files), `h-mad/SKILL.md` §"Teammate authors".
- **No claim was released, because none exists.** The target's `docs/.bkit-memory.json` holds 35
  feature records and none matches this work. If you adopt it under a feature name, use the brief's
  slug `author-done-line-protocol` and `--create --claim` — do not invent a different name.
- **Coupling hazard, and it is why this should be done in a worktree.** `~/.claude/skills/h-mad` is a
  symlink into this checkout, so an edit here is LIVE for any h-mad run in flight anywhere on this
  machine. h-mad's own §"Editing this skill while a run is in flight" requires editing in a git
  worktree and merging when clean. The sending session has an h-mad Phase-5 run in flight right now.
  The suites are also coupled: a change here can fail a suite in a repo you did not touch — run both
  before merging.
- **Sibling repo is mid-work.** `orca/skills` main is live under another session (5 terminals, a
  monitoring agent). This brief was written into `docs/handoffs/` but deliberately **NOT committed**,
  to avoid moving HEAD under that lane. Committing it is the taking session's job — TAKEOVER requires
  it, because an uncommitted marker is one `git checkout` from being a dropped handover.

## Context for Next Session

**Files to touch:**
- `h-mad/agents/spec-author.md`
- `h-mad/agents/plan-author.md`
- `h-mad/agents/design-author.md`
- `h-mad/agents/implplan-author.md`
- `h-mad/agents/doc-auditor.md`
- `h-mad/SKILL.md` — §"Teammate authors"

**Uncommitted changes:** this brief only (untracked). Nothing else was written by the sender.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git log --oneline -1                 # expect 6f00f8c or later
for a in spec-author plan-author design-author implplan-author doc-auditor; do
  printf '%-18s ' "$a"; grep -ciE 'sha256|line-count|lines=' h-mad/agents/$a.md
done                                  # all 0 = still unshipped
grep -ciE 'sha256|line-count' h-mad/SKILL.md
```

**Related docs:**
- `h-mad/SKILL.md` §"Teammate authors" — rules 4 and 5, which this extends
- `h-mad/SKILL.md` §"An agent's reported numbers are a claim, not a measurement" — the general rule
  this is one instance of
