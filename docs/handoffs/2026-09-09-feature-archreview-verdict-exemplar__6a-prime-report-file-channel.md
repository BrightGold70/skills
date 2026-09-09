# Handoff — 6a-prime cannot deliver a verdict: give it a report-file channel

**Date:** 2026-09-09
**Branch:** `feature/archreview-verdict-exemplar`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · feature/18-gateway-consolidation · session 3954e098-067e-4136-98cc-6dfcb2b71484
**Taken-Over-By:** skills · main · session 4417a49b-c9e5-4989-bf36-cd4f73e9351a · 2026-09-09
**Supersedes:** none — first on this branch

## Session Summary

Phase 6a-prime on HemaSuite `#18 gateway-consolidation` could not produce a verdict:
**four** `exec agy` dispatches, four `ARCHREVIEW: NO_VERDICT`, all four having
demonstrably read the tree. Two increments of a prompt-side fix are committed here as
`a6ea361` (green, mutation-verified) and they measurably improved matters without
closing it. The remaining work is **structural and is not prompt tuning**: the
archreview template is the only `exec agy` path with no report-file channel, so its
deliverable rides the agent's last message alone — and every one of the four failures
is a last-message failure. Ownership of that fix, and of the merge decision for
`a6ea361`, moves to this branch. HemaSuite is blocked behind it at
`step6a-prime:no_verdict`.

## Key Learnings

- **The exemplar's FORM matters as much as its position, and #153 only fixed position.**
  The template's sole exemplar was `ASSESSMENT: <READY_TO_MERGE | WITH_FIXES | NO>` inside
  a code fence: a *schema* needing transformation, written in the same `<...>` grammar the
  file uses for orchestrator-filled slots (`<INLINE_FEATURE>`), and fenced three lines under
  prose saying "no code fence around it". The one place it showed the line it wanted read as
  somebody else's placeholder.
- **Two tests had frozen the broken form as an assertion** — `test_h_mad_prompt_tails.py`
  and `test_h_mad_archreview_cycle.py:450`, both asserting
  `tail == ["```", <schema>, "```"]` while the first *also* asserted the template says "no
  code fence around it". A gate calibrated to the defect. I found the second only because
  the full suite caught it after I had "swept" by reading one file; the subsequent value
  sweep for `ASSESSMENT: <` is what proves there were exactly two.
- **A literal exemplar is necessary but not sufficient — measured in both directions.**
  Before the fix the `ASSESSMENT:` token had *never* appeared in five dispatches. c3, the
  first run against the fixed template, emitted it immediately. Then c4 dropped it again.
  Necessity and insufficiency are separately evidenced, not inferred.
- **agy borrows vocabulary across h-mad prompts.** c3 answered `DRIFTED` — a word from the
  **5e spec reviewer's** `VERDICT: COMPLIANT | DRIFT` contract, not this one. Naming the
  wrong words explicitly is now part of the template.
- **A guard rejected my own edit and was right.** I quoted `### ASSESSMENT: DRIFTED`
  literally into the template; `test_no_instruction_follows_the_report_format_heading_except_the_verdict`
  refused it. Beyond the section rule, quoting a heading-shaped verdict hands agy an
  exemplar of the wrong form. Whatever you write, do not put a malformed verdict line
  in that file.
- **Background exit codes lie in both directions, again.** A backgrounded suite run reported
  `exit code 0` via task notification while the same command in the foreground returned
  `RUN_RC=1` on a real failure. Score pytest on its **summary line**, never on the code.
- **`docs/.bkit-memory.json` is gitignored and does NOT exist in this worktree.** The claim
  lives only in `/Users/kimhawk/orca/skills/docs/.bkit-memory.json` — see Next Step 1. A
  receiver who looks for a state file in the worktree finds none and wrongly concludes
  nothing is claimed.

## Next Steps

1. **Claim the feature — in the MAIN checkout's state file, not this worktree's.** The
   worktree has no `docs/.bkit-memory.json` at all (gitignored), so the path is absolute:
   ```bash
   python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py \
     --state /Users/kimhawk/orca/skills/docs/.bkit-memory.json \
     --feature archreview-verdict-exemplar --session-id "<your-session-id>"
   python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py \
     /Users/kimhawk/orca/skills/docs/.bkit-memory.json \
     --feature archreview-verdict-exemplar --claim "<your-session-id>"
   ```
   Released at handover, so a plain `--claim` takes it; no `--force`.
2. **Decide the merge of `a6ea361`.** It is committed on this branch and unmerged.
   `main` is not merged into because `~/.claude/skills/h-mad` symlinks into the live
   checkout and session `ea4d5233-dfcb-4bdb-ac5b-6a002e8aed26` was running there
   (`lanes_watch.sh`, 1d10h elapsed at handover) — merging changes the skill under a
   running session. Re-check that lane is idle before merging:
   ```bash
   ps -eo pid,etime,command | grep -F lanes_watch.sh | grep -v grep
   ```
3. **Build the report-file channel for 6a-prime** — the actual fix. Three parts, mirroring
   what the audit path already does:
   - a `<REPORT_FILE_PATH>` slot in
     `h-mad/references/agy-architectural-reviewer-prompt.md`
   - `--report-file` on `h_mad_archreview_cycle.py stage`, substituted into that slot
   - `score` reading the report file, with the `--out` last message as fallback
   Mirror `h_mad_collect_report.py` / `hmad-dispatch collect-report`, which already solve
   exactly this for Phases 3/4/5b.
4. **Verify it the only way that counts** — re-dispatch the real HemaSuite 6a-prime and
   require a recorded `archreview`. Everything needed is staged and unchanged:
   ```bash
   python3 ~/.claude/skills/h-mad/scripts/h_mad_archreview_cycle.py stage \
     --feature gateway-consolidation \
     --template <this worktree>/h-mad/references/agy-architectural-reviewer-prompt.md \
     --base 0afdb8bb07882cd2e6be57bf0ed5b17647fbb9ec --head 2f27bc93 \
     --design /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/02-design/features/gateway-consolidation.design.md \
     --diff-files "$(cat /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.archreview.diff-files.txt)" \
     --summary /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.archreview.phase5-summary.md \
     --prompt /tmp/archreview_c5.txt
   ```
   Both inputs were copied out of the sender's tmp scratchpad into HemaSuite's
   `docs/03-analysis/` at handover, so they survive; they are UNCOMMITTED there.
   `…diff-files.txt` is 62 absolute paths: the base..head diff with `docs/handoffs/**`
   and `docs/03-analysis/**` filtered out, because those 58 files state this feature's
   conclusions and handing them to the reviewer removes its reason to read (#153).
5. **Then unblock HemaSuite** — its `#18` sits at `step6a-prime:no_verdict` with
   `archreview` unrecorded. Clearing it is a HemaSuite action, not this branch's; just say
   the channel landed.

## Open / Blocked Items

- **The report-file channel** — status: not started, this is the handed-over work.
  `repo: /Users/kimhawk/orca/skills · branch: feature/archreview-verdict-exemplar · worktree: /Users/kimhawk/orca/skills-archreview-exemplar`
  Constraint that shapes the design: the existing test
  `test_no_instruction_follows_the_report_format_heading_except_the_verdict` forbids any
  `## ` heading after `## Report Format`, so **the slot must go ABOVE that section**. Needs
  its own TDD + mutation ledger; `h-mad/tests/mutation-specs/archreview_verdict_exemplar.json`
  is the pattern to copy (7 mutations, each with its own `test` key).
- **Merge decision for `a6ea361`** — status: blocked on your judgement that the live
  `orca/skills` lane is idle. Suite on this branch: **3166 passed, 2 skipped**. Clean up
  with `git worktree remove` once merged.
- **`--slug`/scope caveat on the codex templates** — status: deliberately not done.
  `codex-implementer-prompt.md` and `codex-verifier-prompt.md` carry the same fenced-schema
  shape and were left alone: codex emits `STATUS:` reliably in this repo's record, and
  rewriting a working prompt on a shape argument is the documented failure mode. If you
  touch them, get evidence first.
- **HemaSuite `#18` halted** — status: blocked on Next Step 3, not on this branch's other
  work. `repo: /Users/kimhawk/orca/HemaSuite · branch: feature/18-gateway-consolidation · worktree: none`
  Ownership of `#18` stays with HemaSuite; only the h-mad defect moved here.

## Context for Next Session

**Commits on this branch:** `a6ea361` (1, unmerged, unpushed) on top of `0f7ad05`.

**Files touched by `a6ea361`:**
- `h-mad/references/agy-architectural-reviewer-prompt.md`
- `h-mad/tests/test_h_mad_verdict_exemplar.py` (new, 6 tests)
- `h-mad/tests/mutation-specs/archreview_verdict_exemplar.json` (new, 7 mutations)
- `h-mad/tests/test_h_mad_prompt_tails.py`, `h-mad/tests/test_h_mad_archreview_cycle.py`
- `h-mad/SKILL.md` (the dispatch-count claim, swept in the same commit)

**Numbers to re-derive, never quote:** suite 3166/2 skipped · mutations 7/7 ALL_CAUGHT ·
c1/c2/c3/c4 tool counts 11/19/31/23.

**The interpreter matters:** `python3` here is 3.14 with **no pytest**. Use `python3.11`
(pytest 8.3.5). A bare `python3 -m pytest` fails with `No module named pytest`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills-archreview-exemplar
git status --short --branch          # expect feature/archreview-verdict-exemplar, clean
cd h-mad && python3.11 -m pytest tests/ -q --no-header   # expect 3166 passed, 2 skipped
```

**Related docs — the four dispatch artifacts, preserved in HemaSuite:**
- `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/03-analysis/gateway-consolidation.archreview.c1.offcontract-recovered.md`
- `…/gateway-consolidation.archreview.c1.premise-verification.md` — one finding refuted
- `…/gateway-consolidation.archreview.c3.drifted.md` — the substantive review
- `…/gateway-consolidation.archreview.c3.premise-verification.md` — F3 rejected, F1/F4 open
- `…/gateway-consolidation.archreview.c4.no-verdict.md`
