# Handoff — two fresh-context review lanes, six h-mad fixes, and the WSG takeover

**Date:** 2026-09-13
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-10-main__hmad-gates-and-6a-prime-channel.md, 2026-09-11-main__hmad-tooling-findings-from-the-wsg-lane.md

## Session Summary

Resumed from the 2026-09-10 handoff and closed every item it left open. Two **fresh-context
review lanes** found **8 confirmed defects across 15 commits** that a green suite and
per-mutation batteries had already cleared — five in the inherited nine, three in this
session's own five. All eight are fixed and pushed (`721d6ad..eed91f0`, suite 3191, anchors
`specs=78 mutations=759 drifted=0`). Mid-session a brief arrived from the dying
`HemaSuite-wsg` lane carrying seven h-mad findings; it was claimed, four of its premises
re-probed at source, and five todos restored — **all seven are still open and are the
main backlog for the next session**. `#2` (use Phase 7f on a real closure) closed **NOT
discharged**: WSG was hand-merged, and the attempt surfaced a real gap in 7f instead.

## Key Learnings

- **A green suite plus per-mutation batteries cleared 15 commits carrying 8 real defects.**
  The only thing that found them was a separate lane with no session context. Two of the
  three in this session's own work were *made reachable* by the fixes that preceded them —
  `1b74676` made an unread report file win, which turned "non-empty" into an exploitable gap.
- **Twice a mutation battery reported `ALL_CAUGHT` while silently carrying a mutation that
  bit nothing** (`the-path-boundary-is-dropped`, `the-signature-ignores-the-clock`). Both
  were caught by the harness re-scoring against the named `test` key, never by writing the
  spec. Every other test in those files starts from a state where the weak mutation still
  looks caught — only the re-run case separates them.
- **Editing a predicate invalidated a committed mutation anchor NINE times this session**,
  three of them anchors this same session had committed hours earlier. Every one was caught
  by the harness refusing to measure (`PRECHECK_FAILED … nothing was measured`) rather than
  reporting a hollow `ALL_CAUGHT`. That refusal is the single most load-bearing behaviour in
  the mutation tooling.
- **Four watcher defects, one species: a proxy signal that read as authoritative.** `*"close"*`
  matched "close**out**" and declared closure at Task 14/19; the progress number read the most
  recently *mentioned* task (non-monotonic — 16→18→17) and produced a false "one task from the
  end"; `HEAD` stood in for the branch ref in **four** checks and produced a false "the slot has
  PASSED" about an unrelated 2-day-old commit; stall fired forever on a branch that had
  finished. The load-bearing gate — run the planner, read the token — was correct from the
  first version and never moved. **Everything added for legibility is what lied.**
- **Fixing one member of a class and leaving the rest** happened twice: the `HEAD`-vs-ref guard
  was applied to the gate check and not to the four siblings beside it; and the review's own
  `--allow-historical` finding was the same substring bug `--allow` already had (correctly NOT
  fixed there — see below).
- **A finding has three separable parts and they fail independently.** The review's F2 had
  correct *facts* and a correct *concern* but a prescription belonging to a different surface:
  copying the audit path's `.done` gate into the archreview channel would have undone #31
  entirely, because neither the agy template nor the head contract ever asks for that marker.

## Next Steps

1. **WSG-1+2, coupled — the 6a-prime evidence gate and `stage()`'s missing oversize halt.**
   The highest-value inherited item and the reason a fabricated review nearly closed a Phase-7
   gate. **Land 2 before 1** (the brief is explicit: fixing the gate alone makes 6a-prime *fail*
   rather than fabricate, which reads as a regression). Both premises verified at source:
   `h_mad_review_evidence.py` has no report-path discount; `h_mad_archreview_cycle.py` has **0**
   oversize/vh-tail guards against `h_mad_assemble_audit.py`'s 7 and 6. Remedy for 2 already
   exists one file over — route `stage()` through it.
2. **WSG-3 — the `.done` marker, attribute before fixing.** `grep -n done
   h-mad/references/agy-architectural-reviewer-prompt.md` → one hit, line 121, **prose**;
   `grep -n done h-mad/scripts/h_mad_archreview_cycle.py` → 0. Points hard at "the template
   never asks", but confirm against a live transcript — the sender saw the behaviour, this
   session only read the prompt.
3. **`#7` bkit `hooks.json` unknown-key warning** — untouched all session. Probe whether `once`
   is load-bearing and being silently dropped (the costly reading) or inert (noise). Foreign
   repo → likely a HANDOVER, not a local fix.
4. **WSG-7's `#33`** — `h_mad_wire_registry.py --registry` default follows cwd; **two registries
   are live and out of sync in HemaSuite**. Highest-consequence of the five carried backlog rows.
5. `[suggested]` **Two `--help` nits**, cosmetic, should ride the next edit touching those files:
   `--report-file` opens "Required:" on a flag with `default=None`
   (`h_mad_archreview_cycle.py:392`); `--allow-historical` says "`path:line`" without noting a
   range pin can't be declared by its first line (`h_mad_precheck_doc.py:486`).

## Open / Blocked Items

**Inherited from the WSG brief — all seven still open, claimed as
`hmad-tooling-findings-from-the-wsg-lane` (owner `0392c2be`).** Origin preserved:
**Handover-From:** HemaSuite-wsg · feature/website-source-grounding · session `8574638e`.
`repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main worktree)`.
Evidence archived to HemaSuite `feature/18-gateway-consolidation` (origin tip `85d3af6d`) under
`hematology-paper-writer/docs/archive/2026-09/website-source-grounding/` — the WSG clone itself
is being deleted.

- **WSG-1+2 evidence gate + oversize halt** — status: open, coupled, premises verified at source.
- **WSG-3 `.done` marker** — status: open, partially attributed (see Next Step 2).
- **WSG-4 harness cannot classify a kill** — status: open. Verified at source (`:58-61`, `:625`,
  `:934`). **Corroborated by this session in both directions**: the `test`-key mitigation works
  *and* is the only thing that caught two dead mutations here.
- **WSG-5 `baseline_sha` heuristic** — status: open. NOT a token defect; `candidate=` discipline
  is correct by design (`:21-26`, `:38`). The first-commit-is-the-impl-plan heuristic is what's
  wrong. Shares a root with carried `#38`.
- **WSG-6 state file vanished, cause UNDETERMINED, did not recur** — status: open. Proposal is
  sound regardless of cause: treat an ABSENT state file as cannot-judge, not a clean read.
- **WSG-7 three `precheck_doc` findings + five carried rows (`#57 #33 #37 #38 #56`)** — status:
  open, bundle. **Re-probe each**; `h_mad_precheck_doc.py` was edited twice this session
  (`2192fcc`, `eed91f0`) without touching any of the three. `#37` may interact with the widened
  `<INLINE[^>]*>` grammar shipped in `eed91f0`.

**From this session:**

- **`#7` bkit `hooks.json` warning** — status: open, never started. Exact message:
  `bkit: hooks.json: unknown keys "$schema", "once" in hooks.SessionStart[0] ignored`, every
  SessionStart. `repo: /Users/kimhawk/.claude/plugins/cache/bkit-marketplace/bkit/2.0.8 ·
  branch: n/a (vendored plugin cache) · worktree: none`; the same file also exists at
  `~/.claude/plugins/marketplaces/bkit-marketplace/hooks/hooks.json`.
  **HANDOVER considered and deliberately NOT run.** The cache dir *is* a git work tree, so a
  brief could technically be filed there — but it is a versioned vendor install replaced
  wholesale on the next `bkit` upgrade, so the brief would be destroyed and nobody works that
  lane. Ownership stays here. Probe first, and the two readings differ in cost: `once` may be
  load-bearing and silently dropped (the hook re-fires every session when authored to run once),
  or the keys are inert and the warning is noise. If it turns out to be a real bkit defect, the
  route is an upstream issue, not a brief into a cache directory —
  cf. [[feedback_vendor_managed_skills_not_patchable]].
- **7f is unrunnable when the base exists only as a remote-tracking ref** — status: open finding,
  unfiled upstream. `SKILL.md:302` documents `--base <b>` without the local-branch requirement,
  and `base_not_a_local_branch` is absent from its enumerated blockers. A lane that *clones*
  rather than worktrees cannot reach 7f at all, and learns this only after 7c/7d.
- **The two `--help` nits** — status: deferred, cosmetic (Next Step 5).

**Closed from the 2026-09-10 predecessor — every open item accounted for:**

- **`#34` codex fenced-schema templates** — CLOSED as correctly-deferred-**with a mechanism**.
  Probe falsified the doc's hypothesis: the codex path does *not* head-prepend, and cannot
  (no `Output framing (mandatory` anchor). Closed on the empirical record instead — 2/2 real
  codex 5d/5e reports emit a literal contract-valid token, zero echo the schema. Discriminator
  is **size**: 45 KB worst-case assembled TDD prompt vs the 690 KB that broke agy.
- **`#2` Phase 7f on the next closure** — CLOSED **NOT discharged**; see above and task record.
- **This repo's automation scout** — DONE. 209→212 candidates, one flipped LANDED, one annotated
  half-landed, six re-verified open against source, 20 not probed (said so in the block).
- **No fresh-context review lane on the nine commits** — DONE, and it paid for itself: 5 findings.
- **88 untracked `.done` markers** — CLOSED as **correct as-is**. Gitignoring them is the wrong
  fix; `hmad-dispatch.sh:3057-3059` counts them to exclude from `tree delta`. My framing of this
  as an open decision was wrong.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_archreview_cycle.py` · `h_mad_precheck_doc.py` · `h_mad_audit_cycle.py` · `hmad-dispatch.sh`
- `h-mad/tests/test_h_mad_archreview_cycle.py` · `test_h_mad_precheck_doc.py` · `test_h_mad_audit_cycle.py` · `test_hmad_dispatch_exec.py`
- `h-mad/tests/mutation-specs/` — 4 new specs, 4 repointed
- `docs/skill-candidates.md` · `docs/learnings.md` · `docs/handoffs/2026-09-11-main__hmad-tooling-findings-from-the-wsg-lane.md`

**A SIBLING SESSION is active in this repo.** Session `01Y3duroj` pushed `d01c7e1` (delivered
the WSG brief) and `04c77f1` (`find_latest` returns the supersedes-chain head, not the newest
mtime — `handoff_paths.py` + a 188-line test). Not a collision: the `Taken-Over-By` stamp is
this session's alone. But **check `git log` before assuming you are the only writer here.**

**Uncommitted changes:** none tracked. `lanestate/` untracked (not this repo's), plus the
standing 88 untracked `.done` audit markers — deliberate, see above.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                   # expect 04c77f1 or later, in sync
cd h-mad && python3.11 -m pytest tests/ -q          # expect 3191 passed
# python3 here is 3.14 with NO pytest — use python3.11
python3.11 scripts/h_mad_mutation_harness.py --check-anchors tests/mutation-specs/*.json tests/specs/*.json
```

**Related docs:**
- `docs/handoffs/2026-09-11-main__hmad-tooling-findings-from-the-wsg-lane.md` — the inherited brief, stamped
- `h-mad/SKILL.md:302` — Phase 7f; the local-branch requirement it does *not* state
- `h-mad/tests/mutation-specs/` and `h-mad/tests/specs/` — BOTH are live spec stores
