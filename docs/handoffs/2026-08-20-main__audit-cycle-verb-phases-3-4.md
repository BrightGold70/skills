# Handoff — audit-cycle-verb: Phases 3 and 4 gated, Phase 5 not started

**Date:** 2026-08-20
**Branch:** main
**Project:** skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Rebuilt the skill-upgrade todo list from the 249-row candidate backlog, then took the
highest-value item — `hmad-dispatch audit-cycle` — through H-MAD Phases 1–4. Plan and design are
both gated clean (`GATE: PASS must=0 should=0` on two independent agy passes each) and committed as
`568418d` and `197ecc2`. **Phase 5 has not started: no implementation code exists yet.** 27 audit
cycles, 54 agy dispatches, 79 findings, zero deferrals. The feature is unclaimed and ready to
resume at Phase 5.

## Key Learnings

- **The two-pass union earned its default, measurably.** Across 27 cycles the two independent agy
  passes agreed on ~4 of 79 findings. From design-cycle 8 onward, *every* cycle had one pass gate
  clean while the other found real defects — and the clean pass **alternated sides**. A single-pass
  gate would have shipped defects in at least six separate cycles. This reproduces
  `HemaSuite:403`'s 10-cycle measurement on a different feature in a different repo.
- **Roughly two-thirds of all findings were a fix not fully propagated, not a wrong decision.** The
  design decisions held from cycle 4 onward; what kept failing was the second and third place each
  decision was written down. Twice the stale copy was in the *same paragraph* as its replacement
  (spec AC-4.1 carried both "requires `.done`" and "only an empty or absent file" for a full
  revision). Grepping the corrected **value** across both docs after each cycle caught what two
  independent reviewers missed, more than once.
- **Findings arrive independently; fixes interact.** Three times, two individually-correct
  prescriptions composed into a new defect neither described: cycle-1's "absent token is an
  operational error" became a `combine()` that crashed on every missing report; cycle-4's fixes
  created cycle-5's boundary contradiction; cycles 6+7 applied literally re-created the
  two-extractor drift cycle 7 had just warned about. **Reconcile findings against each other before
  applying them**, not one at a time.
- **Three findings had correct facts and a backwards prescription.** `--project-root` is not a flag
  on `h_mad_extract_report.py` (the *plan* was wrong, not the design — forwarding it would abort the
  fallback); a `## Should-fix`-only report is `INVALID`, not a clean pass; the gate does **not**
  auto-resolve a sidecar. Each was fixed for the measured reason and the refutation recorded in the
  doc so the next reviewer does not re-derive it from the same wrong premise.
- **Probing an exit code found a race no reviewer asked about.** Two findings questioned the exit
  codes in a triage table; measuring them incidentally revealed that collection step 1 accepted a
  non-empty report **without its `.done` marker** — a torn write gated as a complete report. The
  agent writes the report then marks `.done`; `report_wait` blocks on exactly that marker.
- **`GATE: INVALID` carries `must=0 should=0` it never measured.** The gate itself violates the
  cannot-judge-carries-no-counts rule the rest of h-mad follows, so any consumer must key on the
  verdict word, never the counts. Exit 2 there is a *verdict*, not an operational error.
- **Concatenating two audit reports under-counts.** Measured: a prose-only finding plus a bulleted
  finding gate to `must=1` against a true total of 2, because `_count_section_findings` applies its
  prose fall-back only when a section has **no** bullets. This is why the verb gates per pass.
- **`exec` on a shared `--out` is first-writer-wins with an explicit refusal, not last-writer-wins.**
  So a shared path leaves pass 2's file holding pass 1's *report* — plausible and wrong, which is
  worse than empty.

## Next Steps

1. **Claim the feature and enter Phase 5** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature audit-cycle-verb --session-id "<sid>"` (expect `enter_autonomous`; `last_completed_phase=4`), then `--claim "<sid>"`.
2. **Write the impl-plan (5a)** from `docs/02-design/features/audit-cycle-verb.design.md` §"Implementation Order" — it lists seven steps and every deliverable already has an exact path.
3. **Run the 5b impl-plan audit + wire-pin gate** — `h_mad_wire_pin_gate.py docs/01-plan/features/audit-cycle-verb.impl-plan.md --feature audit-cycle-verb`, reading the `WIREPIN:` token.
4. **Phase 5d/5e via `exec codex`** (transport decided at Phase 1; `codex` is on PATH). Six connection mutations are specified in the plan's Architecture Considerations — every one mutates the **caller**, leaving the callee intact.
5. **Do not let the two stub-exempt tests use a stub** — `test_prose_plus_bullet_not_concatenated` and `test_premise_items_match_gate_count` must invoke the real `h_mad_audit_gate.py`. Stubbing is via `HMAD_AUDIT_CYCLE_SCRIPT_DIR`, never `PATH` (an absolute `__file__`-relative path bypasses `PATH` entirely).
6. **Push the two unpushed commits** — `git push origin HEAD` (2 ahead of `origin/main`).

## Open / Blocked Items

- **Phase 5–7 of audit-cycle-verb** — status: not started, unblocked. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: none (main worktree)`. Artifacts: `docs/01-plan/features/audit-cycle-verb.{spec,plan}.md`, `docs/02-design/features/audit-cycle-verb.design.md`, 27 audit reports under `docs/0{1,2}-*/features/audit-cycle-verb.*.audit.v*.p*.md`.
- **h-mad claim** — status: released at closeout. This session held it (`owner_session_id 1329af3b`); released so the next session claims fresh rather than inheriting a lock from a stopped session.
- **`PREFLIGHT: FAIL unresolved=codex,agy`** — status: known, not blocking. Pane pins are unresolved in this repo; `exec` is pane-independent and both CLIs are on PATH, so all 54 dispatches this session worked. Only the `send`/pane path is affected.
- **Design prompts exceed the pane frontier** — status: informational. Design audits assembled to 94–130 KB (`size_status=unverified`, past the 92,055 B confirmed pane limit). Fine on `exec`, which is uncapped; do not switch these to the pane path without re-checking.
- **The 249-row skill-candidate reconcile** — status: open, untouched this session. See `docs/handoffs/2026-08-20-main__skill-candidate-backlog-reconcile.md`. The five rows this feature closes (HemaSuite:268/349/346/403, skills:97) should be stamped `**LANDED**` once Phase 7 archives.
- **Carry-forward from the earlier resume** — advisor-gate live-fire (`HMAD_CONTEXT_WINDOW=1000 claude`), wiring-checker sanity vs a broken matcher, `HMAD_CONTEXT_WINDOW` derived-vs-defaulted, and the 4-file task-tool sweep (`pr-create:19`, `writing-skills:598`, `executing-plans:22`, `using-superpowers:36-52`). All in `.omc/notepad.md`.

## Context for Next Session

**Files touched this session:**
- `docs/01-plan/features/audit-cycle-verb-brainstorm.md`
- `docs/01-plan/features/audit-cycle-verb.spec.md` (v1.17)
- `docs/01-plan/features/audit-cycle-verb.plan.md` (v1.11)
- `docs/02-design/features/audit-cycle-verb.design.md` (v1.14)
- 27 × `audit-cycle-verb.{plan,design}.audit.v<N>.p<i>.md`
- `docs/.bkit-memory.json` (gitignored — state only)

**Uncommitted changes:** none. Two commits unpushed (`568418d`, `197ecc2`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
hmad-dispatch env                      # expect substrate: orca; PREFLIGHT FAIL is OK for exec
python3 ~/.claude/skills/h-mad/scripts/h_mad_context_budget.py
/h-mad "audit-cycle-verb"              # routes to enter_autonomous at Phase 5
```

**Related docs:**
- `docs/02-design/features/audit-cycle-verb.design.md` — §"Implementation Order", §"Test Plan" (18 tests), §"Invariant Compliance" (all 10 rules)
- `docs/01-plan/features/audit-cycle-verb.plan.md` — §"Architecture Considerations" carries the three probe transcripts and the six-row connection-mutation table
- `h-mad/SKILL.md` §"Audit prompt assembly" — the hand-run cycle this verb replaces; §6.6 is the report-file guidance FR-9 corrects
