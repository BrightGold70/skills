# Handoff — h-mad audit-loop root causes: why one Phase-3 audit took 31 cycles

**Date:** 2026-09-03
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Handover-From:** HemaSuite · main · session `082d9a0e-c783-4e35-b862-3f1189570262`
**Taken-Over-By:** skills · main · session `47c2536a-4fa9-40d5-8e26-f2240581c22a` · 2026-09-03
**Supersedes:** none — first brief on this topic

## Session Summary

HemaSuite `#18 gateway-consolidation` Phase 3 (plan audit) needed **31 dual-surface cycles** to
reach `must=0 should=0` on both surfaces (22 cycles in one session, 30 must-fix applied). Every
finding's premise was verified against source before it was applied, so the cycles were not noise —
but a post-mortem over the 22-cycle record shows **about 60% of the cycles were structurally
avoidable**, and the causes are h-mad process defects, not HemaSuite defects. Seven root causes, six
concrete h-mad changes, plus three tooling bugs measured live. Ownership of all of it moves to the
skills lane with this brief; nothing is claimed in `orca/skills`.

Evidence base: `HemaSuite/hematology-paper-writer/docs/01-plan/features/gateway-consolidation.plan.audit.v{10..31}.{agy,codex}.md`
and the plan/spec version histories (v1.10–v1.31 / v1.9–v1.28), all on `origin/main` at `e748eb78`.

## Key Learnings

### Where the 22 cycles went (measured)

| class | cycles | what happened |
|---|---|---|
| **Serial discovery** — reviewer reports one must-fix per cycle | 20 of 22 failing cycles had **exactly 1–3** codex must-fix (median 1) | The prompt asks for every must-fix; the reviewer stops at the first blocking one. Each real defect cost a full cycle (~3.5 min wall, ~1% orchestrator context). |
| **Enumeration series** — same class, one instance per cycle | **9** (c18, c20, c23, c24, c25, c26, c27, c28, c29) | Inventory-guard scanner coverage: `.py.bak` → keyword `args=` → import aliases → `os.posix_spawn` → allowlist → function-local imports → assignment aliases → transitive aliases → literal `getattr`. Closed only when the fix became **a rule over the resolved target plus an exactly-stated residual** (computed callees). A list loses one item per cycle. |
| **Fix-introduced defects** — the previous cycle's edit created the next finding | **4** (c14 "expected pass" clause from c13; c19 readback predicate from c13; c22 `JSONDecodeError` in the outer set from c21; c25's census exposed a pattern I wrote at c20 that missed `self._resolve_cli()`) | h-mad has "sweep by value" but no **adversarial re-read of the delta** before re-dispatch. |
| **Latent contradictions found late** | 5, each alive for 5–15 cycles | AC-3.5 "out of scope to change" vs FR-8 (born v1.8, found c11); `CLINotFoundException` vs FR-8 (v1.0 → c15); `query_notebook` reorder rationale wrong twice (v1.7 → c21, agy's one substantive pass); "a bare `pytest` fires `test_nlm.py`" (v1.8 → c18, **false**: `testpaths = tests`); tracked `.py.bak` executing `nlm` (v1.0 → c15). Two are cross-doc contradictions a mechanical check could flag; two are **behavioural premises stated without a command** — the Evidence-table rule covers counts only. |
| **Hollow second surface** | 21 of 22 agy passes at `ok≤2` (report-file floor) | agy read the tree once (c21, `tools=7`) and that pass found a real logic hole. Re-dispatching a hollow clean (c30b) was hollow again. The "two surfaces" property was nominal: the union gate was carried by codex alone. |
| Operator decision + formal override | 2 (c16, c17) | c16 recorded a B3 exception in prose; c17 required the `## Acknowledged-not-fixed` sidecar. One cycle lost because the skill's override mechanism was not applied at first sight. |
| Confirming clean | 2 (c30, c31) | Correct spend. |

Sum of avoidable: 9 (enumeration) + 4 (fix-introduced) + ~1 (override) ≈ **14 of 22**. The 5 latent
contradictions would have been found earlier under a substantive second surface or a cross-doc check.

### Root causes in h-mad (ordered by cycles they cost)

1. **No "close the class" rule.** When a finding is an instance of an open-ended set (launch APIs,
   alias forms, defect kinds), the audit template and the orchestrator guidance both push toward
   fixing the instance. The series ended the moment the fix was stated as a **pattern + stated
   residual**. h-mad needs that as an explicit step in §"Verifying a review finding before acting on
   it": *classify the finding as instance-of-a-class or singleton; for a class, write the rule and the
   residual, never the instance.*
2. **No delta self-review before re-dispatch.** Four findings were created by my previous fix. The
   "sweep by value" rule sweeps *copies* of a value; it does not re-read the *new paragraph* as a
   reviewer would. A cheap step: after applying a union, re-read only the diff (`git diff` of the
   plan/spec) with the same rubric before assembling the next prompt — or dispatch the diff alone to
   codex as a 30-second pre-check.
3. **Reviewer reports one blocking item and stops.** The prompt says "list every must-fix" but the
   observed behaviour is 1 per cycle. Either the template should require **"continue past the first
   blocking finding; report all you can find in this pass"** with an explicit minimum-effort contract
   (e.g. read N cited files), or the orchestrator should run two codex passes per cycle at different
   reasoning efforts and union them (the memory rule "never gate on one pass" already says so — it is
   the *agy* leg that is hollow, so the second pass should be codex, not agy).
4. **`exec agy` in `--print` mode is structurally hollow for document audits.** `ok≤2` in 21 of 22
   passes across ~110 KB prompts. The `low-evidence` caveat exists but its remedy (re-dispatch)
   does not work. Either require an **evidence-first contract** in the agy audit prompt (read and
   cite ≥N inlined-doc line ranges *before* writing the report — the prompt currently inlines the
   docs, so agy has no *reason* to call a tool) or stop counting an agy document-audit pass toward the
   two-surface gate and run codex×2 instead. Measured on `audit-cycle-verb` too (8 passes, cycle 21
   pass A at 0 tools) — this is not feature-specific.
5. **Behavioural premises are not held to the Evidence rule.** The base invariant "Assumption
   verification / Counts a dispatch reports" requires a command behind every *count*; a plan can
   state "a bare `pytest` fires it" with no command and survive 10 cycles. The false premise cost a
   cycle **and** the probe I ran to check it (`pytest --collect-only .`) fired the live NLM query
   and hung 2 minutes — the premise was dangerous to test *because* it was untested. Extend the rule:
   every *behavioural* premise in a plan carries the command that demonstrates it, run through a seam.
6. **Cross-doc contradiction has no mechanical check.** Spec AC vs spec FR (AC-3.5 vs FR-8) and
   spec vs plan (`CLINotFoundException`) contradictions lived 5–15 cycles. `h_mad_doc_shape_check.py`
   checks shape only. A cheap addition: after each revision, grep each AC's "out of scope / unchanged /
   remains" phrases against the FR descriptions and the plan's change list; report overlaps for a
   human, never gate on them.
7. **The operator-override path is brittle in two ways.** (a) The gate matches
   `## Acknowledged-not-fixed` items **byte-for-byte** against reviewer bullets, so each re-raised
   wording has to be appended verbatim — an override sidecar accretes one line per cycle; a
   substring or normalised match (strip backticks/whitespace, match on the cited path + first clause)
   would hold across rewordings. (b) SKILL.md names the sidecar mechanism but the orchestrator
   guidance for "a reviewer says B3 has no exception" is to *record* the exception in the plan — which
   codex correctly rejected as not the mechanism. Say in the template: an invariant exception is only
   the sidecar, committed `[audit-override]`.

### Tooling bugs measured live (each reproducible)

- **`git add -N` + `git stash push -- <path>` refuses on git 2.50.1** (Apple Git-155): rc=1,
  `error: Entry 'new.py' not uptodate. Cannot merge. / Cannot save the current worktree state`,
  stashes nothing. This is the documented 5e revert sequence in `h-mad/SKILL.md` §5e ("Use this exact
  sequence to revert and restore"). The file stays present, so the `git diff --quiet || echo REVERT
  DID NOT LAND` readback fires — by accident — and a reader following the prose concludes the
  revert failed rather than that the recipe is broken. Working alternative: `git stash push -u --
  <path>` (rc 0, file removed, `stash pop` restores) with an **existence** readback
  (`[ ! -e <path> ]`), since `git diff --quiet` is trivially clean for an untracked file. Probe:
  `<HemaSuite scratchpad>/stashprobe` (a scratch repo; re-create with `git init; commit --allow-empty;
  echo x > new.py; git add -N new.py; git stash push -- new.py; echo $?`).
- **`hmad-dispatch collect-report` returned `COLLECT: MISSING` while `--out` held a complete
  sentinel-bracketed report** (c17 codex: report file + `.done` never written, `--out` had
  `AUDIT-…-BEGIN … -END`). SKILL.md says the verb "always arms the `--out` fallback"; on this run it
  did not fall back. Recovered by hand with `h_mad_extract_report.py <out> --feature … --cycle …`.
  Repro inputs: `<HemaSuite scratchpad cfc…/082d9a0e…>/audit_gc_plan_c17_codex.out.txt` (2.8 KB).
- **`collect-report` leaves the trailing `AUDIT-…-END` sentinel line inside the collected agy
  report** (seen v30, v31 — `sed` removed it by hand). The gate still passed, but an agy report
  collected without that cleanup can read `GATE: INVALID` (c30b re-dispatch report did).
- **Partial-commit hazard is orchestrator-side, not tooling**, but worth a SKILL line: an
  edit-script + `git commit` pair run in one backgrounded shell committed partial docs twice when
  the script aborted on an anchor mismatch and the output was never read (HemaSuite `4b17e37a`,
  `4d508fc6`; repaired `58f252a4`). Rule: never background an edit+commit pair; assert the script's
  `ok` before `git commit`.

## Next Steps

1. **Add "close the class" to `h-mad/SKILL.md` §"Verifying a review finding before acting on it"** —
   classify each finding as singleton or instance-of-a-class; for a class, write the governing rule and
   the stated residual, and say so in the response. Cite the 9-cycle scanner series above as the measured
   cost. — `h-mad/SKILL.md`
2. **Add a delta self-review step to the Phase 3/4 revision loop** — after applying a union and before
   assembling cycle N+1: `git diff` the plan/spec, re-read the added paragraphs against the rubric (or
   dispatch the diff alone to codex, `--timeout 300`). — `h-mad/SKILL.md` §"Audit prompt assembly",
   `h-mad/audit-prompt.template.md`
3. **Fix the 5e revert recipe** — replace the `git add -N` + `stash push` block with `stash push -u` +
   existence readback; mutation-test the doc-test that pins it against a real scratch repo. —
   `h-mad/SKILL.md` §5e; check `invariants.base.md` §"Mutation verification" for a repeated copy.
4. **Make the agy document-audit pass evidence-first or drop it from the two-surface gate** — decide
   with data: dispatch one audit prompt with an added "read and cite ≥5 line ranges of the inlined
   plan via `view_file` before writing" contract vs. the current prompt, A/B via
   `h_mad_ab_dispatch.py`, observe `ok=` from `h_mad_review_evidence.py`. If it stays ≤2, the
   `audit-cycle --passes N` default should be codex×N. — `h-mad/references/…`, `h_mad_audit_cycle.py`
5. **Require a command behind behavioural premises**, not only counts — extend
   `invariants.base.md` §"Assumption verification" with the `testpaths` case. — `invariants.base.md`
6. **Soften the ack-sidecar match** in `h_mad_audit_gate.py` (`_count_section_findings` /
   `_read_ack_file`): normalise backticks/whitespace and match on cited path + first clause; keep
   exact match as the first try. Add a test with two rewordings of one item. — `h-mad/scripts/h_mad_audit_gate.py`
7. **`collect-report` `--out` fallback**: reproduce with the c17 inputs, fix, add the trailing-sentinel
   strip for agy reports. — `h-mad/scripts/hmad-dispatch.sh` (`collect-report`), `h_mad_collect_report.py`
8. **Reviewer effort contract**: add "continue past the first blocking finding" to
   `audit-prompt.template.md` and measure findings-per-cycle on the next feature. — `h-mad/audit-prompt.template.md`

## Open / Blocked Items

- All eight Next Steps — status: not started; owner: skills lane after takeover. `repo:
  /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`. Evidence lives in
  HemaSuite `origin/main` at `e748eb78` (audit reports v10–v31, plan/spec version histories,
  `docs/handoffs/2026-09-03-main__gateway-consolidation-phase3-complete.md`).
- The earlier skills-lane brief `2026-09-03-main__hemasuite-skills-lane-handover.md` (two
  `hmad-dispatch.sh` wrapper bugs, the fail-open revert invariant, 4 leaked `exec-pane` agy PIDs,
  101 classified rows) — status: **still not taken over** at HemaSuite's last resume; this brief does
  not supersede it. Take both in one `/handoff read`.
- No h-mad feature is claimed in `orca/skills` for this work; `docs/.bkit-memory.json` there was not
  touched. Nothing to release.

## Context for Next Session

**Files touched this session:** none in `orca/skills` (this brief only).

**Uncommitted changes:** this brief, until the sender commits it.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read          # pending-handovers lists this brief and the 2026-09-03 skills-lane brief
```

**Related docs:**
- HemaSuite `docs/handoffs/2026-09-03-main__gateway-consolidation-phase3-complete.md` — the session record.
- HemaSuite `docs/learnings.md` — six entries tagged `handoff:2026-09-03-gateway-consolidation-phase3-complete`.
- `h-mad/SKILL.md` §"Never gate on one audit pass", §"Verifying a review finding before acting on it", §5e.
