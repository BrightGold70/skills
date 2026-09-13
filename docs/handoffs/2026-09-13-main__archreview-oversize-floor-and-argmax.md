# Handoff — the 6a-prime oversize halt, the delivery floor, and the ARG_MAX correction

**Date:** 2026-09-13
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-13-main__fresh-review-lanes-and-the-wsg-takeover.md

## Session Summary

Resumed the WSG backlog and closed **WSG-1, WSG-2 and WSG-3** — six commits,
`54a4067..201f716`. A fresh-context review lane then found **7 findings (2 Major, 5 Minor,
0 Critical, all CONFIRMED)**, two of which were defects in *this session's own fixes*, and
one of those was a test that actively defended a false boundary. Findings 1, 3 and 6 are
fixed; finding 2 is filed unfixed; **findings 4, 5 and 7 have never been read** because the
agent report channel truncated three deliveries — the full report is now committed at
`201f716` and reading it is the top Next Step. **WSG-4 is mid-flight in a subagent whose
work is verified-green in the tree but UNCOMMITTED** (see Open Items — this is the most
perishable state here).

## Key Learnings

- **Reusing a measured constant can import the other surface's UNITS along with its
  number.** WSG-2's gate reused `h_mad_assemble_audit.prompt_oversize`, which counts
  CHARACTERS against codex's stdin limit. But `exec agy` passes the prompt as one argv
  element, so the ceiling is ARG_MAX — a BYTE budget the kernel shares with `envp`.
  Measured: argv of 1,048,512 B (exactly what the char gate blessed) fails `OSError 7
  Argument list too long`; 1,037,859 B succeeds. This looked like textbook good reuse — one
  measured figure, one owner, no second constant to drift — and it was wrong.
- **A test that restates the gate's own arithmetic cannot catch arithmetic in the wrong
  unit.** My `test_the_largest_deliverable_prompt_still_stages` asserted `STAGED` at the
  payload that E2BIGs. The replacement takes what the gate blesses and hands it to the
  kernel as argv. Boundary tests should execute, not restate.
- **Every fixture in that file was ASCII, where chars == bytes and the two gates are
  indistinguishable.** That is *why* the defect shipped green. The real designs this channel
  inlines measure 1.004–1.010 bytes/char. A non-ASCII fixture was the whole discriminator.
- **Four times in one session, a carried finding's FACTS held while its PRESCRIPTION
  belonged to a different surface.** WSG-1's implied fix (discount the report path inside
  `h_mad_review_evidence.scan`) was already rejected at `h_mad_audit_cycle.py:39` with a
  measured reason. WSG-3's implied fix (make agy write `.done`) targets a gate deliberately
  not copied. The fourth was mine. Read the code's own recorded refusals before implementing
  a finding's suggestion.
- **The mutation harness refusing to measure is the most valuable thing it does.** WSG-2's
  placement mutation SURVIVED the first battery: my test sized its design against a
  slot-less template and staged against a slot-carrying one, so the extra
  `report <INLINE_REPORT_FILE>` line alone tripped the gate and discounting the contract
  still refused. `ALL_CAUGHT` would have been a lie; the harness said `SURVIVED`.
- **Two agents in one worktree produce FALSE anchor drift that blocks pushes.** A subagent's
  uncommitted edit to `hmad-dispatch.sh` made the pre-push hook report `ANCHORS_DRIFTED`,
  while a byte-exact check returned `hits=1` and three re-runs returned `ok=7/7`. I also
  wasted probes refuting a "harness resolves `root` against cwd" hypothesis — it resolves
  correctly. Give shared-file subagents `isolation: "worktree"`.
- **Subagent reports truncate at ~4 KB in transit, three times running.** The fix that
  worked: have the agent write to a file and reply only `WROTE <path> <N> findings`.

## Next Steps

1. **Read review findings 4, 5 and 7** — `docs/04-report/features/archreview-oversize-and-floor.review.v1.md`
   lines 126, 173, 247. Finding 4's heading is `Minor — CONFIRMED; the property is unmutated
   and untested`, which names a guard that bites nothing. Also read `## Follow-up (a)`
   (line 289) and `## Assessment of 86b6149's two constants` (line 354) before touching the
   ARG_MAX reserves, and `### Negatives` (line 412) so you do not re-probe what was cleared.
   Task #24.
2. **Collect `wsg4-crashkill`'s WSG-4 work and commit it** — see Open Items. Verify with
   `cd h-mad && python3.11 -m pytest tests/ -q` and
   `python3.11 scripts/h_mad_mutation_harness.py --check-anchors tests/mutation-specs/*.json tests/specs/*.json`
   before committing anything you did not author. Task #15.
3. **Fix `--vh-tail 0`** — `h_mad_assemble_audit.py:343`, `entry_idx[-0] == entry_idx[0]`
   keeps every entry while claiming omission, making the prompt LARGER. Guard belongs inside
   `_trim_version_history` (both argparse surfaces are equally reachable; no caller passes
   0). Same task covers the table-formatted Version History silent no-op. Task #22.
4. **One-line cite fix in `references/failure-recovery.md`** — it still credits the codex
   implementer/verifier templates for phases 3/4/5b's `.done`; the real producer is
   `h-mad/audit-prompt.template.md:252`. Blocked only on the subagent releasing that file.
   Task #24B.
5. **WSG-5+6 and WSG-7** — the last untouched WSG items. Tasks #16, #17.
6. `[suggested]` **`#7` bkit `hooks.json`** (task #7) and **`#18` 7f remote-tracking-ref
   blocker** — both untouched for two sessions.

## Open / Blocked Items

**MOST PERISHABLE — `wsg4-crashkill` subagent work is UNCOMMITTED in this tree.** It was
still `running` at 02:10Z after ~40 min. Its WSG-4 crash-kill classification is verified
green (`tests/test_h_mad_mutation_harness.py` → 115 passed; full tree 3221 passed; anchors
`ANCHORS_OK specs=87 mutations=844 drifted=0`) and its classifier is already live enough to
score my batteries (`crash_kills=0`, `(assertion: no traceback from …)`). Files it holds:
`h-mad/SKILL.md`, `h-mad/references/codex-verifier-prompt.md`,
`h-mad/references/failure-recovery.md`, `h-mad/scripts/h_mad_mutation_harness.py`,
`h-mad/tests/mutation-specs/mutation_harness.json`,
`h-mad/tests/test_h_mad_mutation_harness.py`, plus untracked
`h-mad/tests/mutation-specs/mutation_crash_kill_classification.json`.
`repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main worktree)`.
**If that agent is gone, this work is one `git checkout` from being lost.** Its brief
required a per-spec `crash_kills` measurement table which has NOT been reported — do not
mark #15 done without it. Status: in progress, ownership ambiguous.

**Inherited from the WSG brief (origin preserved).**
**Handover-From:** HemaSuite-wsg · feature/website-source-grounding · session `8574638e`.
Claimed as `hmad-tooling-findings-from-the-wsg-lane`, owner re-claimed this session as
`d83c01d0` (previous owner `0392c2be`, heartbeat 2026-09-10, oracle `resume_manual`).
`repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main worktree)`.

- **WSG-1** — CLOSED `c5a5c9c`. `DELIVERY_FLOOR = 1`, asymmetric (only `READY_TO_MERGE` held
  to it). Battery 6/6.
- **WSG-2** — CLOSED `6fd9c20`, then CORRECTED by `86b6149` and `fae30f3` after review.
- **WSG-3** — CLOSED `d235837`. The missing `.done` was correct and expected; the real defect
  was `failure-recovery.md` prescribing a wait that cannot succeed. One cite still owed (#24B).
- **WSG-4** — in flight, uncommitted. See the block above.
- **WSG-5 `baseline_sha` heuristic** — status: open, UNTOUCHED this session. NOT a token
  defect; the first-commit-is-the-impl-plan heuristic is what's wrong. Shares a root with
  carried `#38`. Task #16.
- **WSG-6 state file vanished, cause UNDETERMINED, did not recur** — status: open, UNTOUCHED.
  Proposal sound regardless of cause: treat an ABSENT state file as cannot-judge. Task #16.
- **WSG-7 three `precheck_doc` findings + five carried rows (`#57 #33 #37 #38 #56`)** —
  status: open, UNTOUCHED. Re-probe each. Task #17.

**From this session:**

- **Review findings 4, 5, 7 never read** — status: blocked on reading the committed report.
  The review is NOT discharged. Task #24.
- **Finding 2 `--vh-tail 0` + table-format no-op** — status: open, CONFIRMED, not fixed.
  Deferred because `h_mad_assemble_audit.py` is shared and was held. Task #22.
- **Concurrent-writer anchor hazard** — status: open, documented. Task #23.
- **The review never dispatched a live `exec agy`** — finding 1 is proven at the syscall with
  an agy-shaped argv, not against the agy binary. One real oversize dispatch is the last
  mile and is genuinely owed.

**Carried forward unchanged from the 2026-09-13 predecessor:**

- **`#7` bkit `hooks.json` unknown-key warning** — status: open, never started, unchanged
  since 2026-09-13. `bkit: hooks.json: unknown keys "$schema", "once" in hooks.SessionStart[0]
  ignored`, every SessionStart. `repo: /Users/kimhawk/.claude/plugins/cache/bkit-marketplace/bkit/2.0.8 ·
  branch: n/a (vendored plugin cache) · worktree: none`. HANDOVER considered and deliberately
  NOT run — a versioned vendor install is replaced wholesale on upgrade, so a brief filed
  there is destroyed. Ownership stays here; route is an upstream issue.
- **7f unrunnable when the base exists only as a remote-tracking ref** — status: open,
  unfiled upstream, unchanged. `SKILL.md:302` documents `--base <b>` without the local-branch
  requirement. Task #18.
- **The second `--help` nit** — `h_mad_precheck_doc.py:486`, `--allow-historical` says
  `path:line` without noting a range pin cannot be declared by its first line. Status:
  deferred, cosmetic. The first nit (`--report-file` "Required:") was fixed in `6fd9c20`.
  Task #19.
- **`pending-handovers` re-offers every carry-forward handoff forever** — status: open, found
  during this session's resume. `handoff_paths.py:183` matches `^\*\*Handover-From:\*\*`
  anywhere in the body, and the skill's own carry-forward rule REQUIRES that line in Open
  Items. So this very document will be reported as an unadopted brief. Task #20.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_archreview_cycle.py` — the floor, the byte/ARG_MAX gate, `--vh-tail`, stale-prompt removal
- `h-mad/tests/test_h_mad_archreview_cycle.py` — 56 tests (was 45)
- `h-mad/tests/mutation-specs/archreview_oversize_halt.json` (12 mutations), `archreview_delivery_floor.json` (6), `archreview_done_marker_recovery.json` (2)
- `h-mad/SKILL.md`, `h-mad/references/failure-recovery.md`
- `docs/04-report/features/archreview-oversize-and-floor.review.v1.md` (new, committed)

**Uncommitted changes:** the `wsg4-crashkill` subagent's WSG-4 work — 6 modified files plus
1 untracked spec (listed in Open Items). Plus the standing 88 untracked `.done` audit markers
(deliberate) and untracked `lanestate/` (not this repo's).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                   # expect 201f716 or later, in sync
git status --short | grep -v '\.done$'              # FIRST: is wsg4's work still uncommitted?
cd h-mad && python3.11 -m pytest tests/ -q          # expect 3221 with wsg4's work present
# python3 here is 3.14 with NO pytest — use python3.11
python3.11 scripts/h_mad_mutation_harness.py --check-anchors tests/mutation-specs/*.json tests/specs/*.json
```

**Related docs:**
- `docs/04-report/features/archreview-oversize-and-floor.review.v1.md` — the 7-finding review; 4, 5, 7 unread
- `docs/handoffs/2026-09-11-main__hmad-tooling-findings-from-the-wsg-lane.md` — the original WSG brief, stamped
- `h-mad/scripts/h_mad_audit_cycle.py:31-40` — `DELIVERY_FLOOR = 2` and the rule that a floor is derived from the CONTRACT, never from tool names
- `h-mad/audit-prompt.template.md:252` — the `.done` producer for agy audits, now pinned by a test
