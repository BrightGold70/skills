# Handover — 9 H-MAD skill defects found by HemaSuite's document-intake lane

**Date:** 2026-10-23
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · BrightGold70/hemasuite-document-workbench · session unknown (the operator relayed it through skills session 82a9e02e)
**Taken-Over-By:** skills · main · session 82a9e02e-eaf5-4b5e-b61c-b96709cd9132 · 2026-10-23
**Supersedes:** none — first on this branch

## Session Summary

HemaSuite's `document-intake-source-review` lane (Phase 5) found nine defects in the h-mad skill. It parked them as "H-MAD skill defects to file in the skills repo" in its own handoff, where no skills session reads them. h-mad lives in this repo, so ownership moves here. The operator ordered the move on 2026-10-23.

Nothing in HemaSuite is claimed or released by this move. The feature `document-intake-source-review` stays with HemaSuite.

## Key Learnings

- The source doc is **untracked** in HemaSuite (`git status` shows `??`). The items below are copied verbatim so they survive if that file does not.
- Four of the nine overlap the skills lane's own carried defects; see the mapping in Next Steps. File each defect **once**.

## Next Steps

1. File each defect below as a row in `/Users/kimhawk/orca/skills/docs/skill-candidates.md`. Reconcile the open rows first, as the automation scout does (`~/.claude/skills/handoff/references/automation-scout.md`). Merge each item with the skills lane's list (handoff `2026-10-23-main__grok-run3-agy-gate-halt.md` Next Step 4, items 1–12) where they overlap.
2. Re-probe each premise before filing. These are claims made by a session that has stopped; none were re-run at handover time.

The nine items, verbatim from the source, with a note on overlap:

1. "the codex audit leg is blind in step5". Overlaps skills #4 (agy/codex source reads refused under the Phase-5 hook).
2. "the allowlist is not consulted for the inner command of `hmad-dispatch run`". Same as skills #1 (the codex gate does not check `run --timeout` inner commands).
3. "a collection-time ImportError deadlocks the first production write". New.
4. "the path-label shape is unenforced at 5b". New.
5. "codex prompts omit the allowed read verbs". Overlaps skills #4, and the Key Learning on the dispatch preface.
6. "spec-review drift with no pinning test needs a documented test-first route". Close to skills #5 (no path for a behaviour-preserving fix past a test-passing DENY).
7. "the judge falls back to a `python3` that has no pytest". Same as skills #2.
8. "the extractor rejects a bold `STATUS`". New.
9. "assemble_tdd's `--out` naming is confusing (the dispatch output, not the prompt)". New. The source's Key Learning reads: "Its `--out` flag is the dispatch's output path. The assembled prompt lands in `/tmp/h_mad_<feature>_<module>_red.txt`."

## Open / Blocked Items

- **The nine defects above.** Status: not yet filed.
  - Origin: repo `/Users/kimhawk/orca/HemaSuite`, branch `BrightGold70/hemasuite-document-workbench`.
  - Source doc: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-10-23-BrightGold70-hemasuite-document-workbench__intake-a1-task2-red.md`, Open Items "H-MAD skill defects to file", lines 73–82, plus Key Learnings lines 20–22.
  - Worktree: the HemaSuite document-workbench worktree. Its path is not recorded here.
- **Sender-side pointer owed.** HemaSuite's next WRITE on that branch should record the list as *handed over to `skills@main`, brief `docs/handoffs/2026-10-23-main__hemasuite-hmad-skill-defects.md`* instead of carrying it again. This brief does not edit HemaSuite's tree.

## Context for Next Session

**Files touched:** this brief only.

**Uncommitted changes:** none, once this brief is committed.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
$EDITOR docs/skill-candidates.md   # file the merged defect rows
```

**Related docs:**
- `docs/handoffs/2026-10-23-main__grok-run3-agy-gate-halt.md` (skills defects 1–12)
- `~/.claude/skills/handoff/references/automation-scout.md`
