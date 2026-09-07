# Handoff — doc-block-exec: 5c baseline + Tasks 1 and 2 shipped on `feature/doc-block-exec`; five 5d decisions recorded; Tasks 3–5 owed

**Date:** 2026-09-06
**Branch:** `feature/doc-block-exec` (created this session from `main` at `ce9ffe1`)
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-06-main__doc-block-exec-5b-exit-and-hmad-class-gate.md (the branch predecessor — see the WARNING below, it is filed under `main` and `carry-forward-sources` on THIS branch does not return it), 2026-09-05-main__audit-loop-never-runs-repo-suite.md and 2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md (taken over 09-05; re-emitted below, not re-read this session)

> **WARNING FOR THE NEXT WRITE — the predecessor is on another branch.**
> `python3 handoff_paths.py carry-forward-sources --branch feature-doc-block-exec` returns ONLY the
> two taken-over briefs. The branch predecessor is `…-main__doc-block-exec-5b-exit-…` and is
> invisible from here because the query matches the branch slug exactly. That is task **#65**
> (carry-forward displacement) firing live. Until #65 is fixed, every WRITE on this branch must ALSO
> run `carry-forward-sources --branch main` and walk what it returns, or the whole carried backlog
> leaves the chain in one hop with nothing raised.

## Session Summary

Resumed from the 5b-exit handoff and took `doc-block-exec` from "5b exited, 5c/5d not started" to
**Tasks 1 and 2 implemented, tested, mutation-verified and committed** on a new branch. 5c created
`feature/doc-block-exec` and re-measured the AC-6.4 baselines; Task 1 (scanner, selection,
info-string grammar, and the bounder's second consumer — a `wiring` task) and Task 2 (substitution)
each went RED → GREEN with every number re-derived by the orchestrator rather than taken from the
dispatch. Eight commits, **none pushed**. Five decisions (D1–D5) were forced at 5d and are recorded
in `docs/03-analysis/doc-block-exec.5d-decisions.md`; **D3 is still OPEN and is the sole full-suite
failure**. Tasks 3–5 remain, and they carry all five `OPEN-DECISION (r19, 5d)` lines.

## Key Learnings

- **The wire-scoped revert cannot be delegated to the implementer, by construction.** codex's
  `--sandbox workspace-write` denies `.git`, so `git stash` fails for it; on the Task 1 GREEN it
  ran the revert in a temporary clone and said so in prose. `.git` IS writable from the orchestrator
  session (verified by `touch`). For a `wiring` task the one check that establishes the deliverable
  therefore belongs to the orchestrator. Running the mutation harness here is the clean way to get
  it: `docsections-delegation-reverted` is killed by the WIRE-PIN and nothing else.
- **A collection-error RED certifies nothing about the tests it collects.** Task 1's prescribed RED
  is a module-level `import h_mad_doc_block_exec`, so pytest interrupts at collection and no test
  body runs. 22 of the 46 tests carried a defect (D5) that was invisible until GREEN made the import
  succeed, and all 22 surfaced in the first second of the first GREEN run.
- **`--expect-pass` for a follow-on task is the prior task's `passed` over THAT FILE ALONE.** Task 1
  GREEN reports 53 across two files but 46 across `test_h_mad_doc_block_exec.py`. Passing 53 would
  have read as a discrepancy and stopped the dispatch on a false signal — the stated-counts STOP
  rule working exactly as designed, against the orchestrator.
- **`STATUS: DONE_WITH_CONCERNS` with no concern named is refused by `h_mad_extract_verdict.py`,
  and the refusal was right.** On the Task 1 GREEN the concern existed in the prose (the temp-clone
  revert) and not in the contract line. Had the token been `DONE`, that caveat would have passed as
  a clean wire verification.
- **codex refused twice and was right both times.** The Task 1 GREEN's `BLOCKED` named a real fixture
  defect; its *prescription* was wrong in the way the skill warns about (right symptom, wrong
  mechanism) — see D5. Verify a refusal by re-deriving it, and give it the benefit of the doubt for
  as long as the evidence does.
- **Phase 5 necessarily reds the impl-plan's own precheck noise floor.** PINDRIFT means "a pin into a
  file changed since the document's provenance", and Phase 5 changes exactly those files. The count
  only rises: 12 at `ce9ffe1` → 13 after the RED → higher as Tasks 3–5 land. See D3.

## Next Steps

1. **Task 3 RED** — `## Task 3: execution and bounding`, impl-plan `:2688`. Shape is not `wiring`, so
   counts are required: `--expect-fail` from Task 3's own "Expected RED split" bullet, `--expect-pass`
   = `/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/test_h_mad_doc_block_exec.py -q -p no:cacheprovider`
   at `d6bab5b` (**57** as of this handoff — re-run it, do not carry the number).
2. **Resolve `OPEN-DECISION (r19, 5d)` at impl-plan `:2871` and `:2873`** as Task 3 reaches them —
   the `preamble-composed-with-unsubstituted-text` seam and the `OverflowError`/timeout upper bound.
   Premises are "as filed by codex, re-derive before choosing". `:2635` (Task 2's shared key
   predicate) was implemented at `d6bab5b` — verify the shipped choice matches the decision rather
   than assuming it.
3. **Settle D3** (#114) before anything calls the suite green — three remedies are written out in
   `docs/03-analysis/doc-block-exec.5d-decisions.md`, none picked.
4. **Tasks 4 and 5**, carrying `OPEN-DECISION` `:3374` (alias-refusal unlink read-back) and `:3376`
   (`--help` bypass). Task 4 owns `test_cli_invalid_utf8_document_is_unreadable` and
   `test_cli_subst_overlap_detail_lines`, both forward-referenced from earlier tasks and NOT to be
   written before Task 4.
5. **5f** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_baseline_sha.py --branch feature/doc-block-exec --trunk main`
   reports `UNVERIFIED reason=no_impl_plan candidate=0885152`, **by design**: the impl-plan was
   already committed on `main` before this branch existed, so the first-commit rule cannot vouch.
   `0885152` IS the 5c sha. Then `h_mad_wire_registry.py verify --base 0885152 --rootdir . --testpath h-mad/tests`.
6. **5g** — per-module commits are already made; write `phase = null` ONLY after 5f, never before.

## Open / Blocked Items

**doc-block-exec (this lane) — `repo: /Users/kimhawk/orca/skills · branch: feature/doc-block-exec · worktree: /Users/kimhawk/orca/skills`**

- **Tasks 3, 4, 5 not started.** All five `OPEN-DECISION (r19, 5d)` lines are still open and live at
  impl-plan `:2635 :2871 :2873 :3374 :3376`.
- **D3 — OPEN, and it is the sole full-suite failure** (task #114).
  `test_noise_floor_on_documents_that_survived_eighty_cycles[…impl-plan]`, `PRECHECK: FAIL issues=13`
  against a floor of 12. Three remedies recorded, none chosen. **5e must not be reported green while
  this is red without naming it.**
- **Nothing is pushed.** Eight commits sit on `feature/doc-block-exec`; `main` is untouched at
  `ce9ffe1`. No PR.
- **The parked-spec restore is discharged for Tasks 1–2 but the pattern recurs**: mutation rows are
  written at each task's GREEN against source that exists, never at RED (D2). An unanchored spec
  under `h-mad/tests/mutation-specs/` reds two committed-spec sweep tests and blocks the pre-push
  hook. The parked copies stay at `docs/03-analysis/doc-block-exec.pending-mutation-specs/` as
  provenance — do not delete them.
- **An `implplan-author` revision is owed** for three things this session found and deliberately did
  not edit into the impl-plan: D2's Conventions bullet should read "write the spec at 5e" rather than
  "write it unanchored at 5d"; D5's limit of the new-module RED shape (a collection-error RED
  certifies nothing about its test bodies); and D1's `_FenceEvent` neutral-fields rule.

**Carried from the predecessor `2026-09-06-main__doc-block-exec-5b-exit-and-hmad-class-gate.md` — every item walked**

- **Phase 5b EXITED at `4512615`** on the operator's cap decision — unchanged, and this session
  built on that tree.
- **#110 5c/5d** — **CLOSED this session**: 5c at `0885152`, Task 1 and Task 2 RED+GREEN at
  `954958a`/`7548faa`/`59797b4`/`d6bab5b`.
- **#65 carry-forward-sources displacement** — **still open, and it bit this session**: see the
  WARNING at the top of this doc. Now higher priority than when it was filed, because the branch
  change makes it fire on every future WRITE here.
- **#100 taken-over H1–H9 brief** — unchanged, not started. Overlaps `hmad-audit-evidence-gate`
  (#66/#91). `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`.
- **#105 codify "self-counting screens run last, per instrument"** in `h-mad/agents/*-author.md` —
  unchanged, not started.
- **Tooling worktree `skills-hmad-gate`** (`feature/hmad-class-scored-gate` @ `2f937a3`) — still
  present, still destructive to remove, still the operator's call (#111).
- **Reviewer-side `class:` tagging / GATE-CLASS field measurement** (#112) — still owed; no feature
  has run the new gate on a real audit cycle. This session ran no audit cycle at all (5b is closed),
  so it could not have discharged it.
- **#61 `COLLECT: MISSING` marker-name defect** · **#48 Effort figures unverifiable** · **#42
  INHERITED-UNVERIFIED register** · **#36 `tree delta` baseline never 0 (88 untracked `.done`
  markers, count unchanged)** — all unchanged.
- **Evidence-gate corpus outside the repo, not backed up** (`~/.h-mad-corpora/evidence-gate/`) —
  unchanged.
- **#77 agy leg not dispatched** · **#27, #7, #30, #32, marker-aware reaping** · **#9, #5, #8 P5
  backlog** — unchanged.
- **HemaSuite skill-candidate row** — ownership already moved; brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`. Not re-checked.
- **Codex quota** — did not bind: **seven** codex dispatches this session, zero `usage limit` hits.
- **`.claude/agents/` CLOSED** · **r15 sheet's false scope clause** — unchanged.

**Taken over 09-05 by `adb05ac8` — `**Handover-From:** HemaSuite · main · session cab14393`**
(`docs/handoffs/2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md`; task **#100**)

- **H1–H9 + tooling defects A/B — owned here, NOT started, unchanged since 09-05.** Whether H1–H9 are
  subsumed by the class rule and round cap is still the open fold-or-not decision.

**Inherited — `**Handover-From:** HemaSuite · main · session 9d8394fb`**
(`docs/handoffs/2026-09-05-main__audit-loop-never-runs-repo-suite.md`; folded into
`hmad-audit-evidence-gate` as its third defect, task **#91**)

- **Phase 3–4 audit cycle never runs the project test suite** — unchanged as a skill defect. This
  session ran the full suite by hand four times, which is the workaround, not the fix.

**Related lanes, not owned here**

- **`exec agy` lingers after its `result` event** — `docs/handoffs/2026-09-03-main__exec-agy-hang-after-report.md`,
  session `cd979362`. Unchanged. `repo: /Users/kimhawk/orca/skills · branch: main`.
- **HemaSuite `#18 gateway-consolidation`** is HALTED by the operator "until the orca/skills h-mad
  update lands" (its Orca worktree comment says so). **That update landed** — `f2b3d74` plus
  `2718d48`/`d6f9f03`/`ce9ffe1`. Not acted on: it is another repo's lane and the operator's call.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_doc_block_exec.py` (new, Tasks 1–2)
- `h-mad/tests/test_h_mad_doc_block_exec.py` (new, 57 tests)
- `h-mad/tests/docsections.py` (the wire; private `_fence_aware_end` and `re.search` lookup deleted)
- `h-mad/tests/mutation-specs/doc_block_exec.json` (new, 32 rows) · `…/docsections.json` (8 rows)
- `docs/03-analysis/doc-block-exec.5c-baseline.md`, `docs/03-analysis/doc-block-exec.5d-decisions.md`
- `docs/03-analysis/doc-block-exec.pending-mutation-specs/` (provenance copies, keep)

**Uncommitted changes:** none besides the 88 untracked `.done` markers (do not commit).

**Verified figures, each re-derived by the orchestrator at the commit named:**

| what | value | at |
|---|---|---|
| full suite | `1 failed, 2676 passed` (the 1 is D3) | `d6bab5b` |
| module suite | `57 passed` | `d6bab5b` |
| mutations, new module | `ALL_CAUGHT mutations=32 caught=32 survived=0 refused=0` | `d6bab5b` |
| mutations, docsections | `ALL_CAUGHT` 8/8, each by its own named test | `7548faa` |
| anchors | `ANCHORS_OK specs=2 mutations=40 ok=40 drifted=0` | `d6bab5b` |
| collect, repo root / `h-mad/` | 2879 / 2617 | `0885152` (5c) |
| suite before any of this | `2617 passed` | `ce9ffe1` |

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/doc-block-exec      # HEAD d6bab5b, 8 commits, UNPUSHED
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json \
  --feature doc-block-exec --session-id <you>          # then --claim
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider   # expect 1 failed (D3), 2676 passed
grep -n '^\*\*OPEN-DECISION (r19, 5d):\*\*' docs/01-plan/features/doc-block-exec.impl-plan.md
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.5d-decisions.md` — **D1–D5, read before Task 3**
- `docs/03-analysis/doc-block-exec.5c-baseline.md` — the re-measured AC-6.4 figures and their derivations
- `docs/01-plan/features/doc-block-exec.impl-plan.md` v1.55 — Tasks 3–5 and the five OPEN-DECISIONs
- Commits: `0885152` `7951729` `954958a` `953e7ec` `b6e8322` `7548faa` `59797b4` `d6bab5b`
