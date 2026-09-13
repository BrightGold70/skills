# Handoff — the backlog drained, and what two fresh review lanes cost

**Date:** 2026-09-14
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-13-main__archreview-oversize-floor-and-argmax.md

## Session Summary

Drained the h-mad tooling backlog: **sixteen commits, `91c1021..32789ad`, pushed, suite 3295**.
Every item actionable from this repo is closed — #18, #19, #25, #26, #27, #28, #29, #30, #31,
#37, #38, #57 — leaving only #7 (a vendored plugin cache, deliberately not handed over) and
#56 (blocked, HemaSuite's to answer). Two fresh-context review lanes on my own work returned
**15 findings, 12 of them defects I introduced while fixing**; a third of the session was
remediating them, and a second lane on the first remediation found five more. The recurring
result across the whole backlog: **carried premises failed more often than they held** — four
rows had a false premise, one deferral was priced on a cost that did not exist, and #25's
entire premise turned out to be an artifact of its own measuring instrument.

## Key Learnings

- **An instrument's over-reporting can BE the backlog row.** #25 was "judge 3 crash kills". The
  mutation harness's `crash_kill()` attributes by basename and `_PYTEST_FOOTER` read pytest's
  ordinary `<file>.py:N: AssertionError` footer as a crash — so whenever a mutation targeted a
  TEST file, every guard assertion firing counted as a crash. It manufactured **12 of the
  corpus's 25**. The function's docstring carefully documents the opposite risk (crashes it
  cannot see) and says nothing about crashes it invents.
- **"Targets `tests/`" predicts EXPOSURE to that artifact, not the artifact.** `docsections` has
  6 of 8 mutations in `tests/` and a REAL crash kill. I inferred "13 artifacts" from the
  correlation and was wrong by one spec; measuring each settled it. Two further counts of mine
  were wrong the same way this session and each was corrected only by re-measuring.
- **A hollow kill is always unrunnable code, and four here were unrunnable in four different
  ways** — a kwarg that does not exist, a function never written, a deleted regex group raising
  `IndexError`, a half-applied stringification mixing `int` and `str`. A count never shows it;
  applying the mutation and reading the message it dies on does, in about a minute each.
- **A guard whose only output is discarded cannot be tested.** `archreview`'s `score()`
  overwrote `_read_report_channel`'s four diagnostic reasons with a bare `channel=last-message`.
  That is why its `empty` mutation survived — with the branch removed, an empty file merely falls
  through to `_extract_assessment`, which also returns None, so both paths emitted the identical
  token.
- **Delegating the hard part is not the same as not re-implementing it.** For the Version History
  anchor I consciously reached for the repo's owner (`h_mad_version_history`) — and then
  hand-rolled a fence scanner three lines later, when `doc-block-exec.design.md` states in those
  words that the fence grammar has one home. A ```` wrapper, a `~~~` fence and a trailing-text
  closer all defeated my copy.
- **A "latent, not live" standing is only as wide as the corpus it was measured over.** The second
  review swept 235 files under `docs/01-plan` and `docs/02-design` and called the fence defect
  latent. Chasing an unrelated 31→26 count gap found it firing on a real document in
  `docs/archive` — this repo's own noise-floor calibration corpus, which the sweep excluded.
- **A hard-wrapped sentence is invisible to a single-line grep.** The retracted justification I
  "removed" survived at the rule's own call site, and had been quoted back at me BY LINE in the
  report I was remediating. `grep` found nothing; collapsing the wrap found it immediately.
- **A probe deferred as expensive was free.** #26 said "cost is one real dispatch, do it when a
  6a-prime cycle is running anyway". It costs nothing: `execve` fails before agy starts, so no
  tokens are spent. It sat unrun for a price it never had.
- **Running a mutation harness concurrently with anything that reads the tree produces FALSE
  anchor drift.** Self-inflicted three times. One harness process per worktree, and the
  long inventory gets its own worktree.
- **Every defect I introduced this session was caught by an instrument, none by re-reading my own
  diff** — a surviving mutation exposing a false comment, a 44-document corpus replay, a
  name-shadowing `TypeError`, a portability grep catching my own prose, and the harness's
  "caught by the wrong assertion" / "nothing bites" diagnostics.

## Next Steps

1. **`#7` bkit `hooks.json` unknown-key warning** — the only open item left here. Route as an
   upstream issue; `repo: /Users/kimhawk/.claude/plugins/cache/bkit-marketplace/bkit/2.0.8 ·
   branch: n/a (vendored plugin cache) · worktree: none`.
2. `[suggested]` **Repair the 6 documents that now FAIL precheck** — `NO_LINE_PINS` is enforced
   as of `2861fc7` and these carry 17 line pins their author contracts forbid. Either remove the
   pins or declare them: `python3.11 h-mad/scripts/h_mad_precheck_doc.py <doc> --phase <phase>
   --root .` names each. Files listed in Open Items.
3. `[suggested]` **`h_mad_version_history`'s own `section_bounds`/`ANCHOR`** still carry the naive
   fence rule and the space-optional heading. `precheck_doc` no longer depends on them; the
   version-history bumper does. `h-mad/scripts/h_mad_version_history.py:47,86`.

## Open / Blocked Items

**Carried from the 2026-09-13 predecessor — every item accounted for:**

- **`#7` bkit `hooks.json` unknown-key warning** — status: OPEN, unchanged since 2026-09-13,
  never started. `bkit: hooks.json: unknown keys "$schema", "once" in hooks.SessionStart[0]
  ignored`, every SessionStart. `repo: /Users/kimhawk/.claude/plugins/cache/bkit-marketplace/bkit/2.0.8 ·
  branch: n/a (vendored plugin cache) · worktree: none`. HANDOVER considered and deliberately NOT
  run, unchanged: a versioned vendor install is replaced wholesale on upgrade, so a brief filed
  there is destroyed. Ownership stays here; route is an upstream issue.
- **`#18` 7f unrunnable when base exists only as a remote-tracking ref** — CLOSED `34f9e69`, and
  **its premise was FALSE**. 7f refuses correctly (`base_not_a_local_branch`, `no_default_base`);
  you cannot merge into a remote-tracking ref. The real defect was SKILL.md naming 5 of 10
  blockers — and both tokens an operator hits in that scenario were among the 5 omitted.
- **`#19` the second `--help` nit** — CLOSED `a8b9e4e`, riding the #29 edit exactly as the row
  prescribed. The range claim was verified before being documented, not inherited.
- **`#20` pending-handovers re-offers every carry-forward handoff** — was already CLOSED
  `9b3c1e4`; the predecessor's body listed it as open in one place and closed in another. This
  session's `pending-handovers` scan returned RC=1, confirming closed.
- **`#22` `--vh-tail 0`**, **`#23` concurrent-writer anchor hazard** — both already completed
  before this session; the predecessor's body was stale on these too.
- **Review findings 4, 5, 7** — already fixed (`1c92f5e`, `cee5aea`).
- **`#25` two crash kills in `state_undeclared_keys`** — CLOSED, and the row inverted; see below.
- **`#26` the review never dispatched a live `exec agy`** — CLOSED `3ce1b6c`; now measured
  against the real binary.
- **Inherited WSG brief attribution, preserved:** `**Handover-From:** HemaSuite-wsg ·
  feature/website-source-grounding · session 8574638e`. Claim
  `hmad-tooling-findings-from-the-wsg-lane` was re-claimed at this session's resume and has been
  **RELEASED at closeout** (owner now `None`) — all its items are closed, and leaving it held
  would hand the next reader a lock from a stopped session.

**Closed this session:**

- **`#29` precheck_doc LINEPIN/PINDRIFT/version-history** — CLOSED across `a8b9e4e` → `5af7aaf`
  → `ad8890b`. Two review lanes, 15 findings, 12 self-introduced.
- **`#28` wire-registry cwd ambiguity** — CLOSED `b66e8fb`, following the row's refusal: the
  default is NOT relocated to the git root (that re-creates J49). The resolved path is now echoed
  and the ambiguity warned.
- **`#30` WSG-7 remainder** — #57 CLOSED `74d1144`, #38 CLOSED `f487e8b`, #37 CLOSED `c6db3dd`
  **by refusing its prescription on measurement**. #56 remains blocked, below.
- **`#27` incident-replay tests** — CLOSED `351e75d`, proven by a control/treatment pair in a
  clean worktree (`3261 passed, 2 skipped` → `3273 passed, 0 skipped`).
- **`#31` NO_LINE_PINS** — CLOSED `2861fc7` on an explicit operator decision (enforce, exempt
  `docs/archive/**`). Its carried census was stale: 6 documents / 17 pins, not 4 / 13.
- **`#26` ARG_MAX vs the real agy binary** — CLOSED `3ce1b6c`.
- **`#25` crash kills** — CLOSED `5289fc1` + `75bab19` + `32789ad`.

**Open, new, and deliberate:**

- **Six live documents now FAIL precheck** — status: open by design, the operator's chosen
  outcome for #31, owed to their authors. 17 line pins across
  `docs/01-plan/features/exec-path-hardening.plan.md` (2),
  `docs/01-plan/features/tdd-dispatch-verification-discipline.spec.md` (4),
  `docs/02-design/features/exec-path-hardening.design.md` (2),
  `docs/02-design/features/pin-agents-tail-banner.design.md` (3),
  `docs/02-design/features/regression-provenance-ledger.design.md` (3),
  `docs/02-design/features/tdd-dispatch-verification-discipline.design.md` (2).
  (`hpw-csa-macos-app.design.md` also FAILs, on a pre-existing `TODO`, unrelated to #31.)
- **`h_mad_version_history.section_bounds` / `ANCHOR` still carry the naive fence rule** and the
  space-optional heading — status: open, filed rather than changed under #29. `precheck_doc` no
  longer depends on them; the version-history bumper still does, so the two now disagree about
  exotic fences. `h-mad/scripts/h_mad_version_history.py`.
- **`#56` eleven impl-plan rows naming a different AC** — status: **HANDED OVER to HemaSuite**,
  brief `HemaSuite:docs/handoffs/2026-09-14-main__wsg-backlog-two-items-owed-here.md`, committed
  there as `91a2fec4` and confirmed visible to that repo's `pending-handovers` scan. This entry is
  now a pointer, not a parking space. Not answerable from here: the document IS identified, but the
  eleven rows were never enumerated in either repo, and the only mechanical proxy measures a
  different property (prefix-vs-test-name, finding 1 row, not 11).
  `repo: /Users/kimhawk/orca/HemaSuite/hematology-paper-writer · branch: n/a (archived under
  docs/archive/2026-09/website-source-grounding) · worktree: none`.
  **HAZARD carried into the brief:** `#NN` keys are NOT unique in HemaSuite's handoffs — `#56` also
  names "nccn.org subdomain gap" and `#57` "Task 14 never audited" in the feature-199 handoff.
  Resolve by row TEXT.
- **HemaSuite's two divergent wire registries** — status: **HANDED OVER**, same brief. Surfaced by
  #28; the tooling half is fixed here (`b66e8fb`) and only the data question remains.
  `/Users/kimhawk/orca/HemaSuite/.h-mad/wires.jsonl` and
  `.../hematology-paper-writer/.h-mad/wires.jsonl` differ.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: n/a · worktree: none`.
  No claim was held on either item, so there was nothing to release; delivery was deliberately NOT
  pushed into a live HemaSuite pane — both are blocked data questions rather than prompts to run,
  and the brief's `**Handover-From:**` is what makes their next resume surface it.
- **The classifier blind spot, quantified** — status: open, measured not fixed. 431 of 879
  returncode assertions carry a message; **49% measurable**, so `crash_kills=0` means "none found
  in the measurable half". Remedy when it matters: add messages only in the test files named by
  specs that carry crash kills — never a bulk edit of 448.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_precheck_doc.py` — the L-spelling predicate, the `hard()` router, the
  Version History boundary over `_fence_events`, `_norm_pin`, `NO_LINE_PINS` enforcement
- `h-mad/scripts/h_mad_mutation_harness.py` — the crash-kill classifier
- `h-mad/scripts/h_mad_archreview_cycle.py` — `channel=last-message:<why>`
- `h-mad/scripts/h_mad_wire_registry.py` — `registry_notice`, resolved-path echo
- `h-mad/scripts/h_mad_baseline_sha.py` — `resolve_trunk`
- `h-mad/scripts/h_mad_assemble_audit.py` — `VH_MARKER` (dead helper removed)
- `h-mad/scripts/hmad-dispatch.sh` — the ARG_MAX refusal, the #37 measurement
- `h-mad/SKILL.md`, `h-mad/references/agy-spec-reviewer-prompt.md`
- `h-mad/tests/` — 9 test modules, 11 mutation specs, 1 new fixture
- `docs/04-report/features/precheck-version-history-boundary.review.v{1,2}.md` (new, committed)

**Uncommitted changes:** none. The standing 88 untracked `.done` audit markers (deliberate) and
untracked `lanestate/` (not this repo's) remain.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                    # expect 32789ad or later, in sync
git status --short | grep -v '\.done$'               # expect only lanestate/
cd h-mad && python3.11 -m pytest tests/ -q           # expect 3295
# python3 here is 3.14 with NO pytest — use python3.11
python3.11 scripts/h_mad_mutation_harness.py --check-anchors tests/mutation-specs/*.json tests/specs/*.json
```

**Related docs:**
- `docs/04-report/features/precheck-version-history-boundary.review.v1.md` — 10 findings on `a8b9e4e`
- `docs/04-report/features/precheck-version-history-boundary.review.v2.md` — 5 more on the fix itself
- `docs/04-report/features/wsg7-carried-claims.probe.v1.md` — the WSG-7 re-probe this session acted on
- `h-mad/scripts/h_mad_mutation_harness.py:395-470` — the crash-kill classifier and its two blind spots
- `docs/02-design/features/doc-block-exec.design.md` — "the fence grammar has one home"
