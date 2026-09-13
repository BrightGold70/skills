# Handoff — the cosmetic warning that was hiding a behavioural bug

**Date:** 2026-09-14
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-14-main__backlog-drained-and-two-review-lanes.md

## Session Summary

Resumed the 2026-09-14 closeout and drained its last actionable item, **`#7`**. Nothing in this
repo changed — the whole session's work landed in the bkit plugin cache and upstream. bkit was
**upgraded 2.0.8 → 2.1.38** (restart required), its `hooks.json` patched to drop the top-level
`"$schema"`, and **upstream issue [#155](https://github.com/ww-w-ai/bkit-claude-code/issues/155)**
filed for the durable half. The carried route ("route as an upstream issue") was **half stale**: the
`once` half was already fixed upstream, and — the part that changed the plan — **upgrading does not
silence the warning**, it only shortens it. The item that looked cosmetic turned out to be covering
a real behavioural bug: bkit's `once: true` sat one nesting level too high, so it was ignored and
`session-start.js` had been running on *every* SessionStart rather than once.

## Key Learnings

- **A warning naming two keys can be two different defects at two different levels.**
  `unknown keys "$schema", "once" in hooks.SessionStart[0] ignored` reads as one finding. It is
  the validator concatenating a **top-level** key rejection with a **matcher-level** one; `$schema`
  was never in `SessionStart[0]` at all. Treating it as one item is what made "upgrade will fix it"
  look plausible.
- **`once` IS a valid Claude Code hook key — one level lower than bkit put it.** It belongs on the
  *command* object (`"If true, hook runs once and is removed after execution"`), not the matcher
  object, whose closed set is `{matcher, hooks}`. So the key was silently dropped and the hook ran
  every session. A ticket filed as a cosmetic log line was sitting on top of that.
- **Replaying a decoded rule that reproduces the original text VERBATIM is the corroboration.**
  The allowed sets came out of `strings` on the CC 2.1.268 binary (`qdo=new Set(["description",
  "hooks","modules","surface"])`, matcher `new Set(["matcher","hooks"])`). Running them over the
  pre-patch file emitted the ticket's warning character-for-character. That match is what licenses
  trusting a before/after built on decompiled constants.
- **Four harness surfaces failed to reproduce it and none of them was evidence of absence.**
  `claude -p`, `--debug`, `--debug hooks`, `plugin details`, `plugin validate` — all silent. The
  warning renders on the TUI warn surface only, and `plugin validate` runs a *different* validator
  (unknown **events**, with `docLink`s — not unknown **keys**). A negative from the wrong validator
  looks identical to a pass.
- **The prediction was worth making before the upgrade, because it changed the recommendation.**
  `$schema ∉ {description,hooks,modules,surface}` predicted that v2.1.38 would still warn, just
  shorter. Confirmed exactly post-upgrade: `unknown key "$schema" ignored`. Had the upgrade been
  run first and the warning merely observed to persist, it would have read as the fix failing.
- **Two versions of one vendored plugin had different revert routes.** 2.0.8 was a real git clone
  (`git checkout hooks/hooks.json` reverts); 2.1.38 is not a repo at all. Back up *before*
  patching a vendor cache — the route that worked one version ago may not exist.
- **`node session-start.js` blocks on stdin.** A verification one-liner ending in that command hung
  the full 120s and was backgrounded; `</dev/null` returns rc=0 in 0.05s. A hook that works fine
  under the harness (which closes stdin) hangs when you invoke it by hand.
- **The GitHub remote and the issue's home are different orgs.** `git remote -v` says
  `popup-studio-ai/bkit-claude-code`; `gh issue create` followed a redirect and the issue landed at
  `ww-w-ai/bkit-claude-code#155`. Read the URL `gh` prints back rather than assuming the remote's.
- **A count gap worth chasing even though it changed nothing.** The predecessor said "17 line pins"
  across the 6 precheck-failing docs; the failures total **16**. Both are right — the 17th is an
  `ALLOWED` pin inside `## Version History` in `exec-path-hardening.design.md`. Pin *mentions* and
  *blocking* pins are different counts.

## Next Steps

1. **Restart Claude Code** to apply the bkit 2.0.8 → 2.1.38 upgrade, then confirm at the next
   interactive session start that no `hooks.json` warning appears. This is the only surface that
   shows it — see Key Learnings.
2. **Repair the 6 documents that FAIL precheck** — 16 blocking line pins their author contracts
   forbid, unchanged since `2861fc7`. Re-verified failing this session at `ec75688`. Name each with
   `python3.11 h-mad/scripts/h_mad_precheck_doc.py <doc> --phase <plan|spec|design> --root .`
   Files listed in Open Items.
3. `[suggested]` **`h_mad_version_history`'s own `section_bounds`/`ANCHOR`** still carry the naive
   fence rule and the space-optional heading. `precheck_doc` no longer depends on them; the
   version-history bumper does. `h-mad/scripts/h_mad_version_history.py`.

## Open / Blocked Items

**Carried from the 2026-09-14 predecessor — every item accounted for:**

- **`#7` bkit `hooks.json` unknown-key warning** — **CLOSED this session**, all three follow-ups
  taken on an explicit operator decision:
  1. bkit upgraded `2.0.8 → 2.1.38` via `claude plugin update bkit`. **Restart required.** Ships
     the `once` removal and `timeout 5000 → 10` for free.
  2. `"$schema"` removed (line 2) from
     `/Users/kimhawk/.claude/plugins/cache/bkit-marketplace/bkit/2.1.38/hooks/hooks.json`.
     Verified BEFORE = `unknown keys "$schema" ignored`, AFTER = clean, 21 events intact,
     `session-start.js` rc=0. **2.1.38 is NOT a git clone** — revert is
     `cp ~/.claude/backups/bkit-2.1.38-hooks.json.orig <that path>`.
  3. Upstream issue filed: https://github.com/ww-w-ai/bkit-claude-code/issues/155 — no prior
     issues existed in that repo. Covers `$schema`, and separately flags that they *deleted* `once`
     rather than relocating it to the command object, in case run-once was the intent.
- **Six live documents still FAIL precheck** — status: **OPEN, unchanged since 2026-09-14**, the
  operator's chosen outcome for `#31`, owed to their authors. Re-verified failing this session.
  16 blocking pins (17 LINEPIN lines; one is `ALLOWED` in Version History) across
  `docs/01-plan/features/exec-path-hardening.plan.md` (2),
  `docs/01-plan/features/tdd-dispatch-verification-discipline.spec.md` (4),
  `docs/02-design/features/exec-path-hardening.design.md` (2 blocking + 1 allowed),
  `docs/02-design/features/pin-agents-tail-banner.design.md` (3),
  `docs/02-design/features/regression-provenance-ledger.design.md` (3),
  `docs/02-design/features/tdd-dispatch-verification-discipline.design.md` (2).
  (`hpw-csa-macos-app.design.md` also FAILs, on a pre-existing `TODO`, unrelated to `#31`.)
- **`h_mad_version_history.section_bounds` / `ANCHOR` still carry the naive fence rule** — status:
  OPEN, unchanged since 2026-09-14. Verified present: `ANCHOR` is
  `^##[ \t]*Version History[ \t]*$` (space-optional heading) and `section_bounds` stops at
  header/`---`/EOF with no fence awareness. `precheck_doc` no longer depends on them; the
  version-history bumper still does, so the two disagree about exotic fences.
  `h-mad/scripts/h_mad_version_history.py`.
- **The classifier blind spot, quantified** — status: OPEN, unchanged since 2026-09-14, measured
  not fixed. 431 of 879 returncode assertions carry a message; **49% measurable**, so
  `crash_kills=0` means "none found in the measurable half". Remedy when it matters: add messages
  only in the test files named by specs that carry crash kills — never a bulk edit of 448.
  `h-mad/scripts/h_mad_mutation_harness.py`.
- **`#56` eleven impl-plan rows naming a different AC** — status: **HANDED OVER, and the receiver
  has PICKED IT UP.** Confirmed this session by worktree stamp on `/Users/kimhawk/orca/HemaSuite`
  @ `main`: `taken over: wsg-backlog-two-items-owed-here · item 2 falsified (root registry retired
  c8b0ed79), item 1 open · next: guideline-ingest Task 4`. Item 1 is `#56`, still open **on their
  side**. Not ours; do not restore it as a todo here. Brief:
  `HemaSuite:docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md` (`91a2fec4`).
  `repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: n/a (archived under
  docs/archive/2026-09/website-source-grounding) · worktree: none`.
  **HAZARD, carried:** `#NN` keys are NOT unique in HemaSuite's handoffs — `#56` also names
  "nccn.org subdomain gap" and `#57` "Task 14 never audited" in the feature-199 handoff. Resolve by
  row TEXT.
- **HemaSuite's two divergent wire registries** — status: **HANDED OVER, and now FALSIFIED by the
  receiver.** Same brief, item 2. The receiver's stamp records the root registry was retired at
  `c8b0ed79`, so the divergence no longer exists. Closed on their side; recorded here so the chain
  does not keep re-raising it. `repo: /Users/kimhawk/orca/HemaSuite · branch: n/a · worktree: none`.
- **Inherited WSG brief attribution, preserved:** `**Handover-From:** HemaSuite-wsg ·
  feature/website-source-grounding · session 8574638e`. Claim
  `hmad-tooling-findings-from-the-wsg-lane` confirmed still **released** this session
  (`owner=None`), unchanged since the 2026-09-14 closeout.

**Open, new this session:**

- **A dangling claim on `pin-agents-tail-banner`** — status: open, **deliberately NOT released**.
  `docs/.bkit-memory.json` has it owned by session `f70b9d62-a6d8-4e37-b68d-8841df077327`; it is
  the only one of 39 records still owned. The oracle says it is not live, so it is takeable, but it
  is not this session's feature and READ Step 3.6's allowlist covers only a claim on *this*
  feature. Release when you next pick that feature up:
  `python3 h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature pin-agents-tail-banner --release --session-id f70b9d62-a6d8-4e37-b68d-8841df077327`
- **`h_mad_resume_decision.py` returned the token `complete`** — status: open, filed not chased.
  That token is **not** in the handoff skill's deliberately-closed list
  (`owned_elsewhere` / `cannot_judge` / `enter_autonomous` / `resume_manual` / `halted` /
  `start_fresh`), whose own documentation says an unlisted token must STOP the caller. Either the
  oracle grew a token the skill does not know, or the skill's list is stale. Cheap to settle:
  `grep -n 'complete' h-mad/scripts/h_mad_resume_decision.py` against the skill's list in
  `~/.claude/skills/handoff/SKILL.md` §HANDOVER Step 2.
- **The stale bkit `2.0.8` cache dir was left in place** — status: open by choice, not a defect.
  `/Users/kimhawk/.claude/plugins/cache/bkit-marketplace/bkit/2.0.8` still exists and still carries
  the earlier `$schema` + `once` patch. Inactive. `claude plugin prune` removes it; not run, as it
  was outside what was asked.

## Context for Next Session

**Files touched this session:** none in this repo. All edits landed outside it:
- `~/.claude/plugins/cache/bkit-marketplace/bkit/2.1.38/hooks/hooks.json` — removed line 2
- `~/.claude/plugins/cache/bkit-marketplace/bkit/2.0.8/hooks/hooks.json` — removed 2 lines (now
  inactive; superseded by the upgrade)
- `~/.claude/backups/bkit-2.1.38-hooks.json.orig` — new, the pre-patch copy

**Uncommitted changes:** none. The standing 88 untracked `.done` audit markers (deliberate) and
untracked `lanestate/` (not this repo's) remain, unchanged.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                    # expect ec75688 or later, in sync
git status --short | grep -v '\.done$'               # expect only lanestate/
cd h-mad && python3.11 -m pytest tests/ -q           # expect 3295
# python3 here is 3.14 with NO pytest — use python3.11
# bkit warning check: only visible at an INTERACTIVE session start, after a restart
```

**Related docs:**
- `docs/handoffs/2026-09-14-main__backlog-drained-and-two-review-lanes.md` — the predecessor; its
  Key Learnings on instrument over-reporting remain the best context for the h-mad backlog
- https://github.com/ww-w-ai/bkit-claude-code/issues/155 — the upstream half of `#7`
- `h-mad/scripts/h_mad_precheck_doc.py` — `NO_LINE_PINS` enforcement, the 6 failing docs
- `h-mad/scripts/h_mad_mutation_harness.py` — the crash-kill classifier and its 49% blind spot
