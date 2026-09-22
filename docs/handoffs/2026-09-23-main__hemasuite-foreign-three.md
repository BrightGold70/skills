# Handoff — three skills-repo items carried by HemaSuite, handed over

**Date:** 2026-09-23
**Branch:** main
**Project:** skills
**Handover-From:** HemaSuite · main · session 90b73ff2-53f5-45e9-a86a-8cc60a33dfb5
**Supersedes:** none — first on this branch for these items

## Session Summary

HemaSuite handoffs have carried three items that belong to this repo as "Foreign, ownership NOT
moved" for at least two weeks (the whitespace item since 2026-09-14). The operator decided on
2026-09-23 to hand them over. No h-mad feature record claims any of them: the skills state file has no
matching key, so no claim was released. They are backlog items with **no in-flight work**.

## Key Learnings

- **`#89` is an ID collision across lanes, not one item.** In HemaSuite handoffs dated 2026-09-09,
  `#89` means "`test_docx.py` / `test_pubmed.py` execute live side effects at import", which is a
  HemaSuite item and **stays there**. From 2026-09-23 the same number is used for "delta-self-review
  protocol, anchor-migration class", which is the item handed over here. When you search HemaSuite
  history for `#89`, read the date.

## Next Steps

1. **Whitespace-collapse claim**: `h-mad/references/measurement-discipline.md:129`. The bullet says a
   value sweep "collapses newlines" and prescribes `tr '\n' ' ' < <doc> | grep -o -E '<needle>.{0,2} <word>'`.
   `tr` *translates* each newline to one space. It does **not** squeeze runs, so a hard-wrapped line
   with indentation leaves 3+ spaces, and `.{0,2} <word>` then misses it. Reproduce:
   `printf 'a\n\n  b\tc\n' | tr '\n' ' ' | od -c` → `a`, three spaces, `b \t c`. Two independent lanes hit
   this on 2026-09-14. Fix candidate: `tr -s '[:space:]' ' '` (or `perl -0pe 's/\s+/ /g'`), plus a
   positive control in the bullet.
2. **`#89` delta-self-review protocol, anchor-migration class.** HemaSuite recorded it only as that
   one-line label. The underlying lesson is in HemaSuite memory
   `feedback_delta_self_review_finds_fix_introduced.md` (4 of 4 passes found fix-introduced defects)
   and `feedback_mutation_anchor_migrates_silently.md` (an anchor on the NEXT `def` relocates to a new
   function with the same tail line, `--check-anchors` still says ok, and the mutant reports SURVIVED).
   The owed work is to codify a delta-self-review step in h-mad that covers anchor migration. Re-derive
   scope before starting, because the label is all that was carried.
3. **`#106`: `<COORDINATOR_HANDLE>` leak and `HPW_AGENT_BACKEND` not wired into `exec`.** Also carried
   only as a label. Related HemaSuite memory: `feedback_codex_dispatch_poisons_hpw_backend_markers.md`
   (`exec codex` inherits `CLAUDE_*` markers, so HPW tests die on `Conflicting agent backend markers`).
   Probe `hmad-dispatch` / the codex exec path for the literal `<COORDINATOR_HANDLE>` placeholder
   reaching a prompt before assuming the defect is still live.

## Open / Blocked Items

- Whitespace claim: status open, premise **re-verified 2026-09-23** (command above).
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none`
- `#89`: status open, premise **NOT re-verified**; label only.
- `#106`: status open, premise **NOT re-verified**; label only.

## Context for Next Session

**Files touched this session:** none in this repo (this brief only).

**Uncommitted changes:** this repo had ` M .gitignore` and `?? .ignore` before this brief was written.
They are not the sender's and were left alone.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
sed -n 125,131p h-mad/references/measurement-discipline.md
```

**Related docs:**
- HemaSuite handoffs carrying these: `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-23-main__two-decisions-taken.md`,
  `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-09-14-main__phase5-tasks-4-8-shipped.md`
