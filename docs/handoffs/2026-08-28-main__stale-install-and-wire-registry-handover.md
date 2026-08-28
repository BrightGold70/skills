# Handoff — inbound: a truncated `~/.claude/skills` install, plus two carried-over items

**Date:** 2026-08-28
**Branch:** main
**Project:** /Users/kimhawk/orca/skills
**Handover-From:** HemaSuite · main · session ce0dd6d0-80d3-41f1-9c06-37545cdcd8e1

## Session Summary

Handover from a HemaSuite session that set out to install the mutation-anchor pre-push hook and
found it inert. Root cause was **not** in this repo's code: `~/.claude/skills/h-mad/` held **7 of
24 scripts**, and the HemaSuite clone of this repo was **189 commits stale**, so
`h_mad_mutation_harness.py` had no `--check-anchors` locally. Both were re-synced from
`origin/main` (`2f57cf6`) and the hook is now live and verified in HemaSuite. **No change is owed
to this repo's code** — `anchor-precheck-phase-5e-wiring` (`713f9ad`) had already shipped exactly
what was needed. Three items are handed over: one design question on the sweep's silent output,
and two pre-existing items this session surfaced but did not touch.

## What was verified about this repo (no action needed)

- `--check-anchors` works as shipped. Against HemaSuite's real corpus:
  `ANCHORS: ANCHORS_OK specs=20 mutations=127 ok=127 drifted=0 unreadable=0` in **0.035s**.
- All four verdicts drive the consuming hook correctly: `ANCHORS_OK` → allow; `ANCHORS_DRIFTED`,
  `ANCHORS_UNREADABLE`, `ANCHORS_NOTHING_SWEPT` → block.
- The 2026-08-27 pre-push-hook handover **was** picked up and discharged here
  (`2026-08-27-main__anchor-precheck-shipped.md`). The originating HemaSuite handoff recorded it as
  "unclaimed"; that was written before the pickup and is now stale — no follow-up owed.

## Handed-over items

### 1. `[question]` An UNCLASSIFIABLE spec is invisible at push time

`--check-anchors` reports a malformed `.json` as a per-file
`ANCHORS: <file> UNCLASSIFIABLE — not valid JSON: …` line but still returns `ANCHORS_OK` when the
real specs swept clean. That is a deliberate call (`867218d`, "skipped files are reported, not
fatal") and this session did **not** override it — not every file under `docs/mutations/` is a
spec.

The consequence is worth a decision, though: a consumer that prints harness output **only on a
blocking verdict** — which the HemaSuite hook does, to stay quiet on success — shows the operator
nothing. A genuinely broken spec can sit in the tree indefinitely, announced on a line nobody
renders. Options, in the repo that owns the contract:

- leave as-is and document that consumers must surface `UNCLASSIFIABLE` themselves;
- add a distinct non-blocking-but-visible signal (e.g. a count on the `ANCHORS_OK` summary line,
  so `unclassifiable=1` is legible without changing the verdict);
- treat it as `unreadable` when the file is under a directory the sweep was pointed at explicitly.

Verified reproduction: put `{ bad` in any file under a swept directory and run the sweep.

### 2. `[carried over]` Multi-pin support for `h_mad_wire_registry.py`

Was recorded in HemaSuite's 2026-08-27 handoff as "the file is not in
`~/.claude/skills/h-mad/scripts/` — re-probe the premise before acting". **The premise was false**:
the file exists at `h-mad/scripts/h_mad_wire_registry.py` and was simply missing from the truncated
install. The original multi-pin work is therefore unblocked and un-started. Related and already
landed here: `024bec25` in HemaSuite, "restore 7 wire records lost to the registry id collision".

### 3. `[carried over]` `gate-blindness-hardening` holds a stale claim

`docs/.bkit-memory.json` — `owner_session_id: session_01RGtJc4nHZmhZu6nYkG5Ksa`, heartbeat
`2026-08-06T00:50:32Z`, now **22 days** stale. Surfaced in the 2026-08-27 HemaSuite handoff and
deliberately untouched twice, because releasing another session's claim was outside both
handovers' scope. It is in this repo, so the release decision belongs here.

## Open / Blocked Items

- Item 1 — status: open question, no code owed until a decision is made.
- Item 2 — status: unblocked, un-started.
- Item 3 — status: needs an owner decision, not a code change.
- `wip/check-anchors-local-4aeee78` — status: **safe to delete**. A local, unpushed
  re-implementation of `--check-anchors` written before the staleness was discovered. Kept only so
  the discarded work was not destroyed; it is strictly worse than what shipped here (447 lines vs
  883, no `ANCHORS_NOTHING_SWEPT`, `DRIFTED` exiting 0 instead of 2). Nothing depends on it.

## Context for Next Session

**Files touched in this repo this session:** none. `main` was moved from a local commit back to
`origin/main` (`2f57cf6`); the working tree is clean and in sync.

**Uncommitted changes:** none.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
# the discarded local attempt, if it is ever wanted:
git log --oneline -1 wip/check-anchors-local-4aeee78
```

**Related docs:**
- Originating handoff: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-08-28-main__anchor-guard-live-stale-clone-sync.md`
- What already shipped here: `docs/handoffs/2026-08-27-main__anchor-precheck-shipped.md`
- The consuming hook: `/Users/kimhawk/orca/HemaSuite/scripts/git-hooks/pre-push` (HemaSuite `6aa00407`)
