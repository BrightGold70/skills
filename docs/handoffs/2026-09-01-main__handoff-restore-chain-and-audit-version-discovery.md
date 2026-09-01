# Handoff — the handoff chain silently drops carried backlogs (3 defects), plus the h-mad `_VERSION_RE` audit-discovery defect

**Date:** 2026-09-01
**Branch:** `main`
**Project:** orca/skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · feature/41-headless-nlm-auth-gating · session 1d372f45-8b01-441a-8495-9a927e441272

## Session Summary

A `/handoff read` on HemaSuite restored **10** todos and silently dropped a **15-item backlog** that a
prior session had explicitly taken over on 2026-08-30 (worktree stamped `taken over:`, todos restored
as tasks #25–#39). Recovering it by hand cost 4 handoff docs, 2 memory files and an 866-line findings
doc. Investigation found **three separate defects in the `handoff` skill**, each measured on the live
store, and none of which raises an error anywhere.

Bundled with them is a **fourth, independent h-mad defect** (`_VERSION_RE` blind to surface-suffixed
audits) that has been riding HemaSuite's todo list unworked and belongs to this repo.

**Ownership moves with this brief.** Nothing was claimed: `docs/.bkit-memory.json` here has no record
for `handoff-chain-carry-forward` or `h-mad-audit-version-discovery` (verified — both return
`NO SUCH FEATURE`), so there was nothing to release and nothing for you to take. Claim per-feature
when you start.

## Key Learnings

- **A `Handover-From:` fix was placed in a branch that only runs when the other branch fails.** The
  skill already carries an "Observed live 2026-08-03" note about an inbound handover being invisible
  to check 2 — and the remedy went into check 3, which the skill itself gates with "Use when this
  branch has none" (`SKILL.md:141`). The remedy is therefore unreachable in exactly the common case.
  Fixing a defect in the fallback path leaves the primary path defective.
- **An undefined field is doing load-bearing work.** `**Supersedes:**` appears in the HemaSuite
  handoff chain and truncates it; `grep -c -i supersede ~/.claude/skills/handoff/SKILL.md` → **0**.
  The skill neither defines, reads, nor audits it. A convention nobody specified became the
  mechanism by which content is dropped.
- **The decay is gradual, so no single hop looks wrong.** Backlog mentions across 8 consecutive
  feature/41 handoffs: **9 → 2 → 4 → 1 → 0 → 0 → 0 → 0**. No hop deleted 15 items; each dropped a
  few, and the doc READ loads today carries none. A diff of any adjacent pair would have looked like
  ordinary scope change.
- **My own first probe of this failed silently and would have inverted the finding.**
  `ls -1 | grep -E '^2026-08-3[01]|^2026-09'` in `docs/handoffs/` returned **empty** — rtk/rg
  intercepting the pipeline, not absence — which reads as "no handoffs since 08-30". A control
  (`/bin/ls -1 | wc -l` → 181) plus `command grep` returned **17**. Every null in this brief was
  control-tested for that reason.

## Next Steps

1. **D1 — make check 3's `Handover-From:` exception reachable.** `~/.claude/skills/handoff/SKILL.md`
   §"Step 1: Locate the doc", checks 2 and 3 (line ~141). Check 2 (branch-scoped) returning a hit
   currently short-circuits check 3, so an inbound handover filed under a different branch slug is
   never seen. Reproduce:
   ```bash
   cd /Users/kimhawk/orca/HemaSuite   # on feature/41-headless-nlm-auth-gating
   HP="$HOME/.claude/skills/handoff/scripts/handoff_paths.py"
   python3 "$HP" latest --branch "$(python3 "$HP" branch-slug)"   # -> 2026-09-01-feature-41-…
   python3 "$HP" latest                                           # -> the SAME file
   command grep -l 'Handover-From:' docs/handoffs/*.md            # 9 briefs, none reachable
   ```
   The live example: `docs/handoffs/2026-08-30-handoff-feature-66-provider-error-guard-phase4__backlog-17-item-handover.md`
   carries `**Handover-From:**` and a branch slug of `handoff-feature-66-provider-error-guard-phase4`.
   From `feature-41-…` it is unreachable by construction.
   Suggested shape: scan for unresolved `Handover-From:` briefs **in addition to** check 2, not as a
   fallback to it — and give READ a way to tell a brief that was already taken over from one that
   was not (a `taken over:` stamp is worktree-scoped and does not survive into the doc).

2. **D2 — WRITE has no carry-forward obligation and no way to acquire one.** Verified: SKILL.md has
   **zero** matches for `predecessor|carry forward|carry-forward|previous handoff|prior handoff`.
   WRITE's §"Gather context" item 2 reads the **task tool**, which is session-scoped: a session that
   did not run READ starts with an empty list, and its WRITE then truthfully reports no pending
   todos while dropping everything a prior session restored. Confirmed live — `TaskList` at the start
   of this session returned `No tasks found` while 15 items were nominally owned here.
   Suggested shape: WRITE reads the handoff it supersedes (or the branch's newest) and must either
   re-emit each unresolved Open Item or record it as closed with a reason. An item may leave the
   chain by being finished or by being handed over — never by not being mentioned.

3. **D3 — `Supersedes:` is unspecified and unaudited.** Either define it in the template with the
   carry-forward rule from (2) attached, or drop it. As it stands it is the visible marker of the
   truncation and the skill cannot see it. Measured hop: `2026-08-30-feature-41-…__phases1-5c-gated.md`
   (no `Supersedes:`, 9 backlog mentions) → `2026-08-31-feature-41-…__audit-convergence-…md`
   (`Supersedes:` present, 2 mentions).
   ```bash
   cd /Users/kimhawk/orca/HemaSuite/docs/handoffs
   for f in $(/bin/ls -1 | command grep -E '^2026-08-3[01]-feature-41|^2026-09-01-feature-41' | sort); do
     printf '%-95s sup=%s backlog=%s\n' "$f" \
       "$(command grep -c '^\*\*Supersedes:' "$f")" \
       "$(command grep -ciE 'backlog|CRIT-[1-4]|USE-[1-5]' "$f")"
   done
   ```

4. **h-mad `_VERSION_RE` — audits with a surface suffix are invisible.** Independent of D1–D3; this
   is the item that was riding HemaSuite's list as task #9.
   - `h_mad_cycle_counts._VERSION_RE` is `\.v(\d+)(?:\.p\d+)?\.md$`, so a surface-suffixed audit
     (`.design.audit.v26.codex.md`) never matches and `latest_audit_path` cannot see it. Counted on
     HemaSuite: **9 of 34** design audits and **13 of 45** impl-plan audits unseen. Consequence
     measured there: `h_mad_do_preconditions.py` reported `PRECONDITION: PASS` off an
     **eight-cycle-stale** report.
   - Separately, `latest_audit_path(..., "impl-plan")` returns `None` because `PHASE_SEGMENTS` keys
     it `impl_plan`. A dash/underscore mismatch, silent.
   - A live example of the invisible shape:
     `HemaSuite/hematology-paper-writer/docs/02-design/features/headless-nlm-auth-gating.design.audit.v26.codex.md`
   - **Re-probe both counts before designing** — they were taken on 2026-09-01 and this project's
     carried counts have gone stale within days, repeatedly.
   - TDD the regex change and mutation-test the guard; a widened `_VERSION_RE` that matches too much
     is as silent as one that matches too little.

5. **Consider whether D1–D3 warrant one feature or two.** D2 and D3 are the same defect (chain
   integrity) seen from two ends; D1 is discovery and is separable. D-4 (h-mad) shares nothing with
   them but the repo.

## Open / Blocked Items

- **All four items above are open.** This brief is the queue; status is inline.
- **No claim accompanies this handover** — `docs/.bkit-memory.json` here holds 28 features and none
  of them is these. Verified `NO SUCH FEATURE` for both proposed names. Claim before starting.
- **The receiving repo's `main` was dirty at handover time** — `pin-agents-tail-banner` has 1
  modified spec and 14+ untracked audit files in flight from another lane
  (`/Users/kimhawk/orca/skills`, branch `main`). This handover therefore targets its **own**
  worktree; do not adopt those files.
- **The symlink couples the repos.** `~/.claude/skills/{h-mad,handoff}` both resolve into
  `/Users/kimhawk/orca/skills`, so an edit here is live for every running session immediately —
  including HemaSuite sessions mid-run. Edit in a worktree and merge; run both suites before merging.
- **Not investigated:** whether D1/D2 have dropped items on any repo other than HemaSuite. The
  mechanism is repo-independent, so a sweep of `~/.claude/handoffs/INDEX.md` would say.

## Context for Next Session

**Files touched by this handover:** this brief only. No code, no state, no todo file.

**Sender's lane (coordination only, not yours to work):**
- `repo: /Users/kimhawk/orca/HemaSuite · branch: feature/41-headless-nlm-auth-gating · worktree: /Users/kimhawk/orca/HemaSuite (main worktree)`
- Sender is mid-Phase-5 on `headless-nlm-auth-gating` (8 of 9 tasks shipped) and keeps that feature.
- The 15-item HemaSuite backlog this investigation recovered stays with the sender; only the
  **skill defects** move.

**Evidence trail:**
- `HemaSuite/docs/handoffs/2026-08-30-handoff-feature-66-provider-error-guard-phase4__backlog-17-item-handover.md` — the brief that was dropped
- `HemaSuite/docs/handoffs/2026-09-01-feature-41-headless-nlm-auth-gating__phase5-eight-tasks-and-a-falsified-import-premise.md` — the doc READ loaded instead
- `HemaSuite/hematology-paper-writer/docs/e2e-findings-2026-08-29-hbv-hjy.md` — 866 lines, the backlog's source

**To pick this up:**
```bash
cd <this worktree>
command grep -n 'Use when this branch has none' ~/.claude/skills/handoff/SKILL.md   # D1 site
command grep -c -i 'supersede' ~/.claude/skills/handoff/SKILL.md                    # D3: expect 0
command grep -rn '_VERSION_RE\|PHASE_SEGMENTS' ~/.claude/skills/h-mad/scripts/h_mad_cycle_counts.py
# then, per item, RE-PROBE the premise before doing the work
```

**Related docs:**
- `~/.claude/skills/handoff/SKILL.md` §"Step 1: Locate the doc", §"Gather context before drafting"
- `~/.claude/skills/h-mad/SKILL.md` §Telemetry (the `_VERSION_RE` consumer)
