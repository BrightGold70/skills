# Handoff — h-mad audit gate: fabricated findings block the exit gate, and rejections reset the streak

**Date:** 2026-09-03
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session `f0b69d8d-d082-4455-a1b2-c7074bbf968b`
**Supersedes:** none — first on this topic

## Session Summary

Ownership of two h-mad defects moves to this lane. Both were measured on HemaSuite `#18
gateway-consolidation` Phase 4, cycles 45–75 of a dual-surface (agy + codex) design audit that has
run 75 cycles without meeting its two-consecutive-both-clean exit gate. **Defect 1**: the gate
scores bullets and never checks whether a finding's quoted evidence exists in the document it
names, so a fabricated must-fix blocks the gate identically to a probed one — 6 of agy's 11
must-fixes in that window were fabrications, verified against the assembled prompt each surface
actually read. **Defect 2**: recording a rejection is a documentation edit to a *gated* file, so a
rejection-only cycle changes the bytes and destroys the streak — a fabrication therefore costs two
cycles, not one. The fixes are proposed, not written; nothing in this repo has been touched.

## Key Learnings

- **The gate has the gated files in hand and never reads them for content.**
  `h-mad/scripts/h_mad_audit_gate.py` hashes each `--gated` path (`_gated_hash`, `:194`) and counts
  bullets per section (`_count_section_findings`, `:83`). Both halves of an evidence check are
  already present; nothing joins them.
- **A quote check would have caught every fabrication, mechanically.** Measured against the
  assembled prompt (the exact bytes the surface read), with a control that passes:

  | cycle | agy's quoted evidence | occurrences in the prompt |
  |---|---|---|
  | 64 | `tools/nlm_cli.py:186` · `cli/_commands.py:43` | 0 · 0 |
  | 64 | spec "Delete the pre-existing NotebookLMIntegration…" | 0 |
  | 64 | design "excluded; see B3 gap" | 0 |
  | 69 | `forwarded.pop` · `un_key` | 0 · 0 |
  | 74 | "12-line spike" · "importing nothing" | 0 · 0 |
  | — | **control:** codex c63 `preexec_fn`, codex c67 "carries a UUID" | **4 · 1** |

- **Grep the prompt, never the current document.** My first measurement of this returned 1 for
  every fabricated string and would have gone into this brief as "not reproducible" — because
  recording each rejection had written the fabricated phrase into the design's Version History.
  The prompt files under the sender's scratchpad are the only clean corpus.
- **Two of the six are not absent-quote cases and need a second rule.** c74 claimed
  `tools/notebooklm_integration.py.bak` is "untracked" while the design says **tracked** twice
  (prompt `:1366`, `:2397`) — an inverted quote, not a missing one. c72 claimed the spec was v1.38
  with seven FR-8 paths while the prompt carried v1.45 with the eighth (15 mentions); `v1.38`
  *does* appear 8 times in that prompt, referring to the **plan** and to a historical spec entry.
  A quote check catches c72 (the claimed sentence is absent); the inverted-quote case needs the
  finding to cite a line, not a paraphrase.
- **agy's failure mode changed mid-run and got more expensive.** The prior record for this surface
  was *hollow* (clean verdicts, no reads — `feedback_agy_audit_bypass`). Hollow costs nothing.
  Confabulation costs a full cycle per occurrence plus the streak. Rate over c45–75: agy 11
  must-fixes / 6 rejected; codex 25 must-fixes / 0 rejected.
- **The streak arithmetic is what makes this fatal rather than annoying.** Exit needs two
  consecutive both-clean cycles **on byte-identical documents**. Streak-1 was reached four times
  (c59, c65, c70, c73, and again at c75) and lost every time; c73→c74 was lost to a fabrication
  specifically. With a confabulation every ~2.4 cycles from one surface, the gate is close to
  unreachable no matter how good the design gets.

## Next Steps

1. **Move rejections out of the gated set** — cheapest fix, biggest win. A
   `<feature>.<phase>.rejections.md` ledger that is *not* passed as `--gated`, and an h-mad
   protocol line saying a rejected finding is recorded there rather than in the design's Version
   History. A rejection-only cycle then leaves the gated bytes untouched and the streak survives.
   Touches the audit-phase protocol doc and `h-mad/SKILL.md`'s audit-cycle section; no script
   change strictly required.
2. **Add the evidence check to the gate** — `h-mad/scripts/h_mad_audit_gate.py`. For each
   blocking-section bullet, extract backtick-quoted spans; if the bullet names a gated file and a
   span does not occur in that file's bytes, score the finding `INVALID` (non-blocking, logged with
   the span and the file), not `must`. Fail closed: a gated file that cannot be read keeps the
   finding blocking, matching the existing `--gated` unreadable path (`:317`–`:324`).
3. **Tighten the audit contract to make the check possible** —
   `h-mad/scripts/h_mad_assemble_audit.py` (`:158`–`:176` is the output contract): require every
   must-fix that asserts document content to quote it verbatim in backticks and name the file. The
   contract already mandates the four headings; this is one more sentence in the same block.
4. **Mutation-test the gate change against this corpus before shipping** — the sender's audit
   reports and prompts are the ready-made fixture: the six fabrications must score `INVALID`, and
   codex's 25 must-fixes plus agy's 5 real ones must stay blocking. A change that invalidates any
   real finding is worse than the defect.
5. `[suggested]` Consider whether `--passes N` consistency (agy-only) should be gated at all while
   this is open; see `feedback_never_gate_on_one_audit_pass`.

## Open / Blocked Items

- **Both fixes — status: not started, owned by this lane.**
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
  Files: `h-mad/scripts/h_mad_audit_gate.py` (343 lines; `_count_section_findings:83`,
  `classify:132`, `_gated_hash:194`, `--gated` handling `:248`/`:317`),
  `h-mad/scripts/h_mad_assemble_audit.py` (373 lines; output contract `:158`–`:176`).
  No h-mad feature record exists for this work — checked
  `/Users/kimhawk/orca/skills/docs/.bkit-memory.json`, no `hmad-audit-evidence-gate` key, so
  **nothing was claimed and nothing was released**. Claim it on takeover.
- **Evidence corpus lives in the sender's scratchpad and is not durable** — status: copy it before
  acting if you want the fixture.
  `/private/tmp/claude-501/-Users-kimhawk-orca-HemaSuite/f0b69d8d-d082-4455-a1b2-c7074bbf968b/scratchpad/audit_gc_design_c{45..76}_{agy,codex}.txt`
  (assembled prompts — the clean corpus) and the collected reports, which **are** durable at
  `/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/02-design/features/gateway-consolidation.design.audit.v{1..75}.{agy,codex}.md`.
- **Related, already in this lane** — `exec agy` lingering after its `result` event (brief
  `2026-09-03-main__exec-agy-hang-after-report.md`, taken over by session `cd979362`) and the
  audit-loop root causes brief (`2026-09-03-main__hmad-audit-loop-root-causes.md`, taken over by
  `47c2536a`). This brief is a third, distinct defect in the same subsystem.
- **Not handed over, stays with the sender** — `#18 gateway-consolidation` itself (claim
  `f0b69d8d…`, Phase 4, cycle 76 in flight). This brief changes nothing in HemaSuite.

## Context for Next Session

**Files touched this session (in this repo):** none — only this brief.

**Uncommitted changes:** this brief, until committed.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git status --short --branch
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py \
  docs/.bkit-memory.json --feature hmad-audit-evidence-gate --claim "<this session>"
# then Next Step 1 (protocol change), 2 (gate), 3 (contract), 4 (mutation-test vs the corpus)
```

**Related docs:**
- `h-mad/references/` audit-phase protocol, and `h-mad/SKILL.md`'s audit-cycle section.
- Sender-side record of every cycle: `gateway-consolidation.design.md` Version History (v1.0–v1.70)
  names each finding, each fix, and each rejection with its evidence.
