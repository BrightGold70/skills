# Handoff — the audit loop's own machinery: P1, P2 and P3 shipped

**Date:** 2026-09-04
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-04-main__coder-teammate-audit-surface-and-5b-gating-round.md (branch predecessor; every open item carried below), 2026-09-03-main__exec-agy-hang-after-report.md (its one item is **#22**, closed this session at `bea1b60`/`3f50b95`), 2026-09-03-main__hmad-audit-evidence-gate.md (its residual is **#27**, re-emitted below unchanged)

## Session Summary

Resumed the P1–P5 backlog and shipped **P1, P2 and P3 entire** — ten items across twelve commits,
all pushed to `origin/main` at `3f50b95`. The suite went 2486 → **2546 passed**, and all 42
committed mutation specs sweep clean at 442/442 anchors. Three fresh-context review rounds ran over
the work; two found real defects in my own fixes and the third found none. Two of the P3 items had
sat unexplained for weeks because their cited "commit shas" are **session UUIDs**, not commits —
neither resolves in either repo, which is why nobody had ever reproduced them. Outcome: **done for
P1–P3**. P4 is the feature itself (doc-block-exec 5b round three onward) and is untouched; P5 is
backlog. No production code exists for doc-block-exec and 5b is still ungated.

## Key Learnings

- **Two backlog items cited "commits" that are session UUIDs.** `cfc79129` (#3) and `45db0187`
  (#22) resolve in neither repo. Both items were vague precisely because nobody could open the
  reference. `git cat-file -t <sha>` settles it in a second and should be the first move on any
  inherited defect that names a sha.
- **Calibrate a new gate against artifacts that already passed, before wiring it.** Every detector
  I wrote for the precheck (#20) as a hard finding fired dozens of times on the design and plan
  that had just passed 83 and 74 audit cycles — `PATH` 104, `LINEPIN` 49, `PLACEHOLDER` 48 — and
  every hit was correct usage. A planning document names files the feature will create; `<slot>` is
  how a design declares a grammar. What survived as hard is only what is provably wrong. Recorded
  as `feedback_calibrate_a_new_gate_against_documents_that_already_passed`.
- **The `--out` fallback was armed and dead** (#16). It passed `--after-marker` unconditionally,
  and that flag needs a dispatch boundary only the *pane* transport writes, so on every `exec`
  `--out` file extraction exited 2 and the fallback silently yielded nothing. SKILL.md said "the
  verb always arms the fallback", which was true and useless. Arming is not working.
- **`set -euo pipefail` explains the torn read's signature** (#3). A non-zero return from `main`
  exits immediately, so the post-`main` re-read never happens — which is why the reported errors
  only ever appeared *after* `codex exec rc=0`. A failing dispatch could not have shown the
  symptom. Reproduced both directions.
- **Fuzzy ack matching is not merely imprecise, it is inverted** (#15). On the real 7-bullet
  sidecar, token overlap scores the negative control (two genuinely different AC-1.4 leaks) at
  **0.180**, above both re-worded true pairs (0.089, 0.158). Every threshold that pairs the
  duplicates collapses the real findings first.
- **The size fixture needed re-anchoring three times in one day, and twice the test PASSED without
  it** — sitting 883 B and then 1,381 B under the ceiling. The comment written on 2026-09-03
  predicted exactly this ("a drift this close reads as a pass right up until it doesn't") and it
  came true on the very next edit. Re-measure on any template or invariants change; do not wait for
  red. Also corrected: the template is **not** wholly head-duplicated, so an edit costs 1×, not the
  2× the old comment assumed.
- **Of the reviewer's eleven round-one findings, the one that was wrong was the only one carrying
  no `quote:` line.** Small but clean evidence for the `quote:` contract added last week.
- **I picked the wrong lever first on #22.** Defaulting `--timeout` broke 58 tests, because that
  value flows into the *agent's* argv. The defect is in the wrapper's own wait, so the ceiling
  belongs at the watchdog. A fix whose blast radius is 58 tests is a fix aimed at the wrong thing.
- **Sweeping one mutation-spec directory is not sweeping the corpus.** I ran `--check-anchors` over
  `tests/specs/`, got `ANCHORS_OK`, and the suite still failed on two anchors in
  `tests/mutation-specs/`. There are two directories.
- **A heading replace matched inside a longer heading and split it.** Replacing
  `"## Watching a headless dispatch"` matched the last two `#` of `"### Watching …"`. Three
  doc-structure tests caught it; `git diff --numstat` on the doc is the cheap proof it is repaired
  (41 added, 0 deleted).

## Next Steps

**P4 is the feature; P1–P3 are done. The tier ordering the operator set on 2026-09-04 — the audit
loop's efficacy before the feature it audits — has now been paid down, so P4 is next by default.**

1. **[P4-a] Round three of the 5b gating loop, from a fresh full-context session.** Assemble
   design c85 / plan c76 / impl-plan c35 at `3f50b95`, dispatch a `doc-auditor` teammate per phase
   **and** the agy leg, gate on the union, tell each auditor it is gating, and **freeze the tree for
   the round**. New this session: run `h_mad_precheck_doc.py` on each document first, and use
   `audit-cycle --surfaces` rather than two agy passes. — `h-mad/SKILL.md` §"Precheck before you
   dispatch", §5b
2. **Measure the precheck on that live round** — it is proven against a historical corpus and a
   noise floor but has **never run ahead of a real dispatch**. Record findings-prevented-per-cycle,
   and must-fixes-per-cycle before/after the #17 effort contract. Both are unmeasured claims today.
3. **When codex returns 2026-09-07 11:28**, run one round with the real codex leg before stamping
   anything, and **flip `doc-block-exec.codex_status` back to `available`** —
   `python3 h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature doc-block-exec --set codex_status=available`
4. **If a round comes back clean on both surfaces at one commit:** `h_mad_audit_gate.py … --gated`
   per phase, then `h_mad_wire_pin_gate.py … --feature doc-block-exec`, then 5c
   `git checkout -b feature/doc-block-exec`. Claim `doc-block-exec` first with plain `--claim`.
5. **[P5] The remaining backlog** — #9's five unverified skill-candidate rows, #8's pytest
   agy-pane leak row, #5's 101 HemaSuite rows (foreign lane).

## Open / Blocked Items

- **doc-block-exec 5b — gate NOT met, nothing stamped, unchanged since 2026-09-04.** Design v1.93 /
  plan v1.86 / spec v1.55 / impl-plan v1.36. Claim is **released**. Ready for round three, not
  blocked. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
- **Codex quota — blocked until 2026-09-07 11:28.** The teammate substitution is the standing
  workaround and is currently **gating**, by operator decision. Unchanged.
- **`doc-block-exec.codex_status` is set to `exhausted` and must be flipped back.** I set it this
  session to author `h_mad_precheck_doc.py`, since doc-block-exec sits in `step5` and the TDD gate
  blocks Claude's production `.py` writes. The declaration is **true** until Sep 7, but **one switch
  has two effects**: it also permits Claude to author 5d/5e production code for that feature. Flip
  it before 5d.
- **The precheck (#20) and the effort contract (#17) are both unmeasured in the field.** #20 is
  proven against a historical corpus and a noise floor, never ahead of a live dispatch. #17 claims
  only that the contract is *stated*; `h_mad_ab_dispatch.py` exists for the efficacy claim and was
  not run. Next Steps 1–2 are where both get their first real number.
- **Marker-aware reaping for `exec` — owed, deliberately not built.** Reaping on `<report>.done`
  would end the wait when the work finishes rather than at the 3600 s ceiling. It needs the wrapper
  to learn the report path, which it does not know (`--out` is the verdict file; the report path
  lives inside the prompt). With a ceiling and a legible `rc=124` in place the remaining cost is one
  timeout on an intermittent fault.
- **#27 deferred evidence check — unchanged, inherited from `hmad-audit-evidence-gate`.** Step 2 was
  **measured and refused**, not skipped: no span-occurrence rule discriminates. Revisit only once
  enough cycles have run under the `quote:` contract to form a corpus of reports that carry
  `quote:` lines. — `docs/03-analysis/hmad-audit-evidence-gate.measurement.md`, commit `109a02a`
- **Evidence-gate corpus lives OUTSIDE the repo and is not backed up** — `~/.h-mad-corpora/evidence-gate/`,
  64 byte-verified prompts c45–c76 plus both measurement scripts. Verified present 2026-09-04. It is
  the only corpus behind #27's refusal.
- **#7 `docsections.py` `_fence_aware_end` dedupe — unchanged, not started.** Closes with
  doc-block-exec 5e.
- **A HemaSuite skill-candidate row is probably a duplicate of #3 — HANDED OVER, no longer this
  repo's.** Brief written and committed into their store as
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md` (`f5afb219`),
  carrying `**Handover-From:**` so their next resume picks it up. Nothing was claimed — there is no
  `docs/.bkit-memory.json` at that repo root — so no claim was released. Not delivered to a live
  lane: there is no HemaSuite session running and interrupting one to hand over a one-line
  bookkeeping item is not worth it; their READ will find it.
  `verify-dispatch-rc-not-wrapper-exit` at
  `/Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md:646` claims a wrapper bug at
  `hmad-dispatch.sh:3314` where the wrapper exits 2 on work that succeeded — almost certainly the
  torn post-`main` read closed here at `bea1b60`. The scout did **not** verify `:3314`
  independently. The skills symlink couples the CODE but not the todo stores, so this needs someone
  in HemaSuite. `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **#9 five skill-candidate rows still not individually re-verified — unchanged.** The scout that
  ran at the last closeout re-verified four of nine and stated the other five as unverified in the
  file rather than leaving it implied.
- **#5 (101 classified HemaSuite rows) and #8 (pytest leaks exec-pane agy panes) — unchanged, not
  started.** #5 is a foreign lane.
- **`.claude/agents/` question is CLOSED** (was an open operator decision): the five agents are now
  tracked at `h-mad/agents/` and registered by user-scope symlink. Recorded here because the
  predecessor left it open.
- **55 untracked `.done` markers** — deliberate, do not commit. Unchanged.

## Context for Next Session

**Files touched this session:**
- `h-mad/SKILL.md` (teammate authors + audit leg, precheck, delta self-review, ack rule, torn read,
  exec ceiling, §6.6 correction)
- `h-mad/agents/{spec,plan,design,implplan}-author.md`, `h-mad/agents/doc-auditor.md` (**new,
  tracked** — were gitignored and machine-local)
- `h-mad/scripts/h_mad_precheck_doc.py` (**new**), `h_mad_audit_cycle.py`, `h_mad_audit_gate.py`,
  `h_mad_review_evidence.py`, `h_mad_state_schema.json`, `h_mad_cycle_counts.py`, `hmad-dispatch.sh`
- `h-mad/audit-prompt.template.md`, `h-mad/invariants.base.md`
- `h-mad/tests/test_h_mad_precheck_doc.py`, `test_hmad_dispatch_torn_read.py` (**both new**), plus
  `test_h_mad_audit_cycle.py`, `test_h_mad_audit_gate.py`, `test_h_mad_assemble_audit.py`,
  `test_hmad_dispatch{,_audit_cycle}.py`, `test_h_mad_review_evidence.py`
- `h-mad/tests/specs/audit_cycle_connections.mutation.json`,
  `h-mad/tests/mutation-specs/{verb_no_self_invocation,audit_effort}.json` (re-anchored)
- `docs/03-analysis/hmad-teammate-routing.{6db8e50.review,707ef0e.delta-review}.teammate.md`,
  `hmad-p1-audit-loop.batch-review.teammate.md` (**new** — the three review reports, persisted)

**Uncommitted changes:** none besides the 55 `.done` markers (and this doc until committed).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env   # PREFLIGHT: PASS expected
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q                 # 2546 expected; bare python3 is 3.14, no pytest
grep -oE '^- v1\.[0-9]+' docs/02-design/features/doc-block-exec.design.md | tail -1   # re-derive, never trust a pin
```

**Related docs:**
- `h-mad/SKILL.md` §"Teammate authors", §"Teammate audit leg", §"Precheck before you dispatch",
  §"Delta self-review", §"Why the ack match is not fuzzy", §"A dispatch that rewrites the wrapper
  tears its own read", §"`exec` bounds itself even when you omit `--timeout`"
- Memory: `feedback_calibrate_a_new_gate_against_documents_that_already_passed` (**new**),
  `feedback_coder_teammates_beat_agy_as_second_surface` (**materially rewritten** — authors are
  teammates too, and the combiner now enforces the evidence rule),
  `feedback_audit_loop_root_causes`, `project_doc_block_exec`
