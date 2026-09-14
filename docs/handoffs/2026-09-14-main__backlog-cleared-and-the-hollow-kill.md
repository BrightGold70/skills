# Handoff — the backlog cleared, and the instrument that caught me

**Date:** 2026-09-14
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-14-main__bkit-hooks-warning-and-upgrade.md, 2026-09-14-main__wsg-56-impl-plan-ac-enumeration.md

## Session Summary

Resumed the 2026-09-14 closeout and **drained the entire backlog** — every carried item is now closed,
plus an inbound handover taken over mid-session and finished. Fourteen commits, all pushed; the h-mad
suite is **3307 passed / 0 failed**, green for the first time in this chain. The session's shape was
less "work the list" than "the list was wrong three times": a carried remedy was the wrong command, a
brief's central premise was false, and a count I published without running anything was off by one.
The most useful artefact is not a fix but an instrument — `crash_visible=M/T` on the mutation
harness's token line — which caught a hollow kill I had myself introduced four commits earlier.

## Key Learnings

- **A finding filed into a changelog line is durable but unfindable.** `#56` bounced between two repos
  and drew one `CANNOT PROBE` on the premise that its enumeration existed nowhere. It existed — in the
  impl-plan's own **v1.12 Version History entry**, one 8485-character line, in no section and under no
  heading. Every document-level search treats a changelog as metadata and skipped it. `handoff`'s own
  `pending-handovers` reads only a doc's header block for the same reason.
- **`crash_kills=0` was never evidence, and the harness said so only in its docstring.** The token
  line — the thing a caller greps — carried the bare count. Measured by AST: **452 of 921** returncode
  assertions carry a message (49.1%), so for half the corpus a zero meant "none found in the half I
  can see". Prose in a docstring is not a report.
- **That instrument paid for itself on its first run, against me.** With `crash_visible` live,
  `version_history` reported `crash_kills=1` on an ALL_CAUGHT run. The crash was a **hollow kill I
  introduced hours earlier at `4553425`**: the fence-grammar port dropped `lines` from `find_anchor`'s
  signature, so a mutation replacing the refusal with `return len(lines)` died on `NameError` instead
  of on its named test — which that row's own `_mechanism` forbids in those words.
- **`h_mad_version_history` was planning writes into a fenced template.** `references/inline-protocols.md`
  has seven `## Version History` headings; six are indented, one is not, so the old `^##` regex took the
  seventh as "the live section". A ```` ```markdown ```` fence spans L477–511 and that heading is at
  L509. All seven are examples; the file has **no live section**. The test covering it asserted the bug
  in words ("the one unindented header is a real section").
- **A returned brief's `**Handover-From:**` names the courier, not the owner.** The rule said to prefix
  restored todos from that field while justifying it as "the work belongs where the sender said it
  does" — and on a *return* those disagree. Fixed at the source, with the reason pinned by a test,
  because an unexplained rule is the kind a later reader simplifies back.
- **The bkit 2.1.38 upgrade that closed `#7` silently turned an h-mad test red.** `bc86602` added an
  `analysis` doc type to bkit's validator; h-mad's mirror asserted set *equality* against it. The drift
  guard fired correctly and nobody saw it, because the predecessor's resume line said `expect 3295` —
  which is the **collected** count (3294 passed + 1 failed), so a red suite read as green.
- **Three of my own measurements were wrong before they were right**, each in the direction this repo
  keeps punishing: a zsh `set -- $d` that doesn't word-split reported every precheck doc as clean; a
  regex requiring a quote after the comma reported 15% assertion coverage where AST says 49%; and two
  concurrent full suites produced 11 phantom failures. In all three the instrument broke, not the tree.
- **`claude plugin prune` does not remove stale version dirs.** It targets *auto-installed dependencies*
  (`--dry-run` → "Nothing to prune"). The carried remedy for the bkit 2.0.8 orphan was simply the wrong
  command, and the only `2.0.8` strings in plugin config belong to a different plugin entirely.
- **bkit's Destructive Detector blocks every `rm -rf` form**, including the narrowly-scoped literal path
  its own message recommends. Worth knowing before planning a cleanup around it.

## Next Steps

1. **Second-opinion the four borderline `#56` rows**, each of which could be its AC's positive control
   rather than a mismatch — listed in
   `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` §"Still open".
   Task 13 r6 + Task 14 r24 (`AC-5.8`), Task 4 r3 (`AC-9.1`), Task 15 r9 (`AC-10.1`).
2. `[suggested]` **Commit the hooks-validator replay script** if this check should survive. It closed
   `#7`'s visual half offline and will be needed again — the `$schema` patch lives in a vendor cache and
   is **wiped by the next bkit upgrade**. Currently in the session scratchpad only; proposed home
   `h-mad/scripts/h_mad_check_plugin_hooks.py`, with a test pinning the two key-sets against the live
   binary.
3. `[suggested]` **Read `#56` rows 71–177** if the enumeration must be exhaustive. Calibration bounds
   the risk (all eight known mismatches ranked within 61 of 177) but does not remove it.

## Open / Blocked Items

**Carried from the two predecessors — every item accounted for:**

- **Six documents FAIL precheck** — **CLOSED `c297395`.** All six now `PASS issues=0`. Every pin checked
  was already **stale**, so the repair is a correction, not a style pass. What each meant was recovered
  by reading each file at the doc's own authoring commit, never guessed from today's tree.
- **`h_mad_version_history` naive fence rule** — **CLOSED `4553425`** (+ `cc2d7d7`, `e966691`). Ported
  onto `_fence_events`; mutation spec re-anchored, `ALL_CAUGHT` 25/25.
- **Mutation-harness classifier blind spot (49%)** — **CLOSED `43c0cc6`.** Instrument fixed rather than
  corpus: token line now ends `crash_visible=M/T`. Prescribed remedy then applied at its stated scope
  (two named test files, 12/19 → 19/19), never a bulk edit of 469.
- **`complete` token unlisted** — **CLOSED `f297c30`.** It was the *skill's* list that was stale; the
  oracle is right. Safe only because `_owned_elsewhere` is evaluated before every `complete` return —
  that ordering is now pinned by a test.
- **Dangling claim on `pin-agents-tail-banner`** — **RELEASED.** 40 records in `docs/.bkit-memory.json`,
  **none owned**.
- **Stale bkit `2.0.8` cache dir** — **REMOVED**, on explicit operator approval, after its carried
  remedy was falsified. `2.1.38` verified intact afterwards (21 events, `$schema` patch present).
- **`#7` bkit hooks.json warning** — **CLOSED, and its visual half closed offline.** The validator was
  re-extracted from the live 2.1.270 binary (byte-identical to the predecessor's 2.1.268 constants) and
  replayed over all 28 installed plugins: 6 carry a `hooks.json`, all CLEAN. Negative control first —
  the pre-patch backup reproduces the recorded text verbatim.
- **`#56` eleven impl-plan rows** — **RETURNED to this repo, taken over, and CLOSED.** See below.
- **HemaSuite's two divergent wire registries** — **CLOSED, falsified.** Re-verified this session: the
  root `.h-mad/wires.jsonl` is gone and `c8b0ed79` exists with that message. Recorded so it does not
  re-enter the chain.
- **Inherited WSG brief attribution, preserved:** `**Handover-From:** HemaSuite-wsg ·
  feature/website-source-grounding · session 8574638e`. Claim `hmad-tooling-findings-from-the-wsg-lane`
  unchanged — still released.

**Open, new this session:**

- **Four borderline `#56` rows awaiting a second opinion** — status: open, deliberately uncounted.
  Each could be the AC's positive control rather than a different property, and my casting vote is not
  what they need. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`; sources are
  read-only in `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/archive/2026-09/website-source-grounding/`.
- **`#56` rows 71–177 unread** — status: open by choice. The measured total is **twelve, not eleven**,
  reported rather than trimmed to fit. All eight previously-known mismatches ranked within 61/177, so an
  unread one below rank 70 would be the first of its kind — bounded, not excluded.
- **The hooks-validator replay lives only in the scratchpad** — status: open, see Next Step 2. It dies
  with this session unless committed, and the patch it verifies is wiped by the next bkit upgrade.
- **`docs/skill-candidates.md` has 54 open rows and this closeout reconciled only 2** — status: open,
  and said out loud because the scout's own warning is that an unreconciled status decays until the
  backlog must be re-derived by hand. Reconciled: the bkit "which diagnostic surface shows which
  warning" row (**SUPERSEDED** — the offline replay retires the question) and the hollow-kill-detector
  row (**advanced, not landed** — `crash_visible` is the denominator, not the "did the mutant reach the
  property?" detector it asks for). The other ~52 were **not** touched: bulk-flipping rows I had not
  checked is the documented anti-pattern, and 23 of them merely *mention* surfaces this session
  touched. Census: `python3 handoff/scripts/skill_candidates_census.py docs/skill-candidates.md`.
- **Two harness blind spots remain, unchanged and documented** — the untargeted branch (no `test` key)
  is not classified at all, and a `TimeoutExpired` kill is unreachable by this design. Both stated in
  the harness docstring; neither is touched by `crash_visible`.

## Context for Next Session

**Files touched this session:**
- `handoff/SKILL.md`, `handoff/tests/test_handoff_oracle_token_coverage.py` (new),
  `handoff/tests/test_handoff_takeover_mode.py`
- `h-mad/scripts/h_mad_version_history.py`, `h_mad_precheck_doc.py`, `h_mad_assemble_audit.py`,
  `h_mad_mutation_harness.py`, `h-mad/SKILL.md`
- `h-mad/tests/test_h_mad_version_history.py`, `test_h_mad_doc_shape_check.py`,
  `test_h_mad_mutation_harness.py`, `test_h_mad_assemble_audit.py`,
  `h-mad/tests/mutation-specs/version_history.json`
- 6 precheck docs under `docs/01-plan/features/` and `docs/02-design/features/`
- `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` (new)
- `docs/handoffs/2026-09-14-main__wsg-56-impl-plan-ac-enumeration.md` (adopted + stamped)

**Uncommitted changes:** none. The standing untracked `.done` audit markers and `lanestate/` remain,
unchanged and not this session's.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                  # expect 43c0cc6 or later, in sync
git status --short | grep -v '\.done$'             # expect only lanestate/
cd h-mad && python3.11 -m pytest tests/ -q         # expect 3307 passed, 0 failed
# python3 here is 3.14 with NO pytest — use python3.11
# NEVER run two full suites at once: concurrent runs produced 11 phantom failures
#   in test_hmad_dispatch_audit_cycle.py this session. That file passes 40/40 alone.
# "3307 passed" is the PASS count, not the collected count. The predecessor's
#   "expect 3295" was the collected total and read a red suite as green.
```

**Related docs:**
- `docs/04-report/features/wsg-56-impl-plan-ac-enumeration.probe.v1.md` — the `#56` census, the eight
  recovered rows, the four new ones, and the two screens that provably do not work
- `docs/handoffs/2026-09-14-main__bkit-hooks-warning-and-upgrade.md` — the predecessor
- `docs/handoffs/2026-09-14-main__wsg-56-impl-plan-ac-enumeration.md` — the inbound brief, stamped
  `**Taken-Over-By:**` and committed at `da63499`
- `h-mad/scripts/h_mad_mutation_harness.py` — `crash_visible`, and the two blind spots it does not close
