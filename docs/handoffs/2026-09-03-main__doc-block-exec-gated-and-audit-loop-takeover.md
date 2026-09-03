# Handoff — doc-block-exec Phase 4 gated, Phase 5b at impl-plan v1.9 (cycle 9); audit-loop root causes + exec-agy-hang taken over

**Date:** 2026-09-03
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-03-main__hmad-audit-loop-root-causes.md, 2026-09-03-main__exec-agy-hang-after-report.md (both taken-over briefs, every item carried below), 2026-09-03-main__doc-block-exec-phase4-and-inbound-handover.md (branch predecessor; its open items carried below)

## Session Summary

`doc-block-exec` moved from an un-gated Phase 4 (design cycle 42, codex `must=1`) to **Phase 4
GATED** (design cycle 45 + plan cycle 39 clean on both surfaces at `68e9eb9`, stamped at `33b32ec`),
then into Phase 5: impl-plan v1.0 authored, and revised v1.1–v1.9 by a new fresh-context teammate
(`.claude/agents/implplan-author.md`) across **nine 5b cycles**, with design cycles 46–58 and plan
cycles 40–49 running in parallel as back-propagation. State at handoff: design v1.61, plan v1.62,
spec v1.38, impl-plan v1.9 at `14536ef`; **nothing is gated for Phase 5b yet** — impl-plan cycle 10
is owed, and one codex design-c58 must-fix is open (the delegation-revert mutant). Two HemaSuite
handover briefs were taken over and claimed (audit-loop root causes → todos #10–#17; exec-agy-hang →
#22). Findings-per-cycle analysis (why 45+ design cycles) is in Key Learnings and tasks #20/#21.
Outcome: **partial** — Phase 5b in progress; nothing implemented yet (no production code exists).

## Key Learnings

- **Why audit loops run 40–50 cycles (measured this session, 27 dual-surface cycles):** about
  half of every cycle's findings are (a) author premises a `grep` refutes before dispatch (nested
  `run_recipe`, `str.replace` ≠ `substitute`, `section_from(text, offset, level=2)`), (b) findings
  the previous cycle's fix introduced (c43 → c44 "four outcomes", c46 → c47 binding sentence), or
  (c) counts/placeholders. All three are mechanical. The other half are genuine design holes the
  reviewers only reach one per cycle (serial discovery). The `implplan-author` teammate cut class (a)
  to zero after cycle 1; the value sweep I ran caught most of (b) but missed the plan's own
  pseudocode twice.
- **A design edit re-opens the plan gate and vice versa** — every design cycle here cost a plan
  cycle too because counts (mutation rows 55→67) and shared sentences live in both. Running all three
  phases' audits in one parallel round (6 legs) is what kept wall time bounded (~6 min per round).
- **`collect-report --out` fallback did not fire (task #16, reproduced):** design c58 codex wrote
  a 0-byte report file + `.done` while `--out` held the full sentinel-bracketed report; `COLLECT:
  MISSING`. Recovered with `h_mad_extract_report.py <out> --feature … --phase design --cycle 58`.
- **agy `exec` died at t=0 once** (`RESULT status=ERROR turns=0`, design c51) — a plain re-dispatch
  succeeded. Agy passes were `low-evidence` in 24 of 30 dispatches; the substantive ones (c43: 5
  tools, c58: 16 tools, impl-plan c9: 18 tools) each found something real.
- **Renderer corpus settles grammar arguments in one command:** 14 scanner rules × markdown-it-py
  2.2.0 and 4.2.0 = 14/14 both; the old `docsections` heading regex vs the new selector over 30 docs
  gave `new_only=0, old_only=76` (all fenced `#` comments) — the "guard narrowing" objection had an
  empty softened set. Both are cited in plan §Measurements.
- **Custom agent definitions load without a restart:** `.claude/agents/implplan-author.md` written
  mid-session was immediately dispatchable via `Agent(subagent_type: "implplan-author")`, and
  `SendMessage` to its name continued it with context across nine revisions.
- **`hmad-dispatch run --timeout N -- sleep M`** is the portable wait (no `timeout` binary).

## Next Steps

1. **Impl-plan v1.10 then 5b cycle 10.** Send the author (or edit directly) the open design-c58
   codex must-fix: make `docsections-delegation-reverted` a *connection-only* revert — `docsections.py`
   binds `_dbe` to the real module loaded by file path via `importlib.util.spec_from_file_location`
   (bypassing `sys.modules`, so the WIRE-PIN's fake is never seen) instead of restoring local
   functions; then every behaviour test AND the source guard stay green and only the WIRE-PIN fails.
   Update the design (§Components docsections.json row, the "except the source guard" clauses),
   plan (§"A fifth mutation pins the wire"), and impl-plan Task 1 to that wording. Then dispatch
   design c59 + plan c50 + impl-plan c10 in one round:
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py --feature doc-block-exec --phase <plan|design|impl-plan> --cycle N --project-root . --report-file /tmp/audit_doc-block-exec_<phase>_cycleN_codex.report.md --out /tmp/audit_doc-block-exec_<phase>_cycleN_codex.txt` → `hmad-dispatch exec codex … --timeout 1800 &` and `hmad-dispatch audit-cycle --feature doc-block-exec --phase <phase> --cycle N --passes 1 --project-root /Users/kimhawk/orca/skills --timeout 1800 &`; collect with `hmad-dispatch collect-report --surface codex …`; gate with `h_mad_audit_gate.py`. — `docs/01-plan/features/doc-block-exec.impl-plan.md`, `docs/02-design/features/doc-block-exec.design.md:~441`
2. **When all three gate:** `h_mad_audit_gate.py <impl-plan audit> --gated <impl-plan>` and re-stamp
   design (`--gated design plan spec`) + plan (`--gated plan spec`); `h_mad_wire_pin_gate.py <impl-plan> --feature doc-block-exec`
   (already `WIREPIN: PASS tasks=5 wiring=2`, 3 wires registered in `.h-mad/wires.jsonl` at `14536ef`);
   then 5c: `git checkout -b feature/doc-block-exec` and commit the impl-plan + audits there. — `h-mad/SKILL.md` §5b/5c
3. **5d/5e per task** via `h_mad_assemble_tdd.py --phase red|green` — Task 1 is `wiring` shape
   (WIRE-PIN uses a `sys.modules` fake); Tasks 2–4 `new-behaviour` with stated RED splits; Task 5
   `wiring` (two pins, `timeout=60.0`). Interpreter `python3.11`; suite floor baseline `2747`
   measured from the REPO ROOT (from `h-mad/` it is 2485). — `docs/01-plan/features/doc-block-exec.impl-plan.md`
4. **After 5g (TDD gate no longer blocks prod writes):** task #16/#22 in `hmad-dispatch.sh` —
   `collect-report` `--out` fallback (reproduce with `/tmp/audit_doc-block-exec_design_cycle58_codex.{out.txt,report.md}`)
   and `exec agy` completion detection (brief's Next Steps 1–3). — `h-mad/scripts/hmad-dispatch.sh`, `h-mad/scripts/h_mad_collect_report.py`
5. **h-mad process changes** (tasks #10–#17, #20, #21): close-the-class rule, delta self-review,
   5e revert recipe (`stash push -u`), agy evidence-first or codex×2, behavioural-premise commands,
   ack-sidecar normalised match, reviewer effort contract, pre-dispatch impl-plan precheck script,
   author teammates for Phases 2–4. — `h-mad/SKILL.md`, `h-mad/invariants.base.md`, `h-mad/audit-prompt.template.md`, `.claude/agents/`

## Open / Blocked Items

- **doc-block-exec Phase 5b not gated** — status: in progress. impl-plan v1.9 answered cycles 1–9;
  cycle 10 not dispatched. Open must-fix: design c58 codex (delegation-revert mutant, resolution in
  Next Step 1). Design c58 agy clean; plan c49 clean apart from the then-stale impl-plan. Claims
  **released** at handoff for `doc-block-exec` and `exec-agy-hang-after-report` (take with plain
  `--claim`). State: `current_phase=5`, `last_completed_phase=4`, `phase=step5`, substrate recorded.
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
- **Design c58 codex report was recovered by hand** (report file 0 bytes + `.done`; `--out` full) —
  `docs/02-design/features/doc-block-exec.design.audit.v58.codex.md` is that extraction. Task #16.
- **Inherited from `hmad-audit-loop-root-causes` (Handover-From HemaSuite 082d9a0e; taken over
  2026-09-03 by 47c2536a):** all eight items — status: not started, unchanged; todos #10–#17. Location
  block: `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`;
  evidence HemaSuite `origin/main` `e748eb78`. That brief's own open item "skills-lane brief not
  taken over" is **withdrawn** — it was stamped before this session (pending-handovers = none).
- **Inherited from `exec-agy-hang-after-report` (Handover-From HemaSuite 45db0187; taken over
  2026-09-03 by cd979362, claim released at handoff):** status: not started; todo #22; brief's Next
  Steps 1–3 stand; not reproduced in this session's ~30 agy execs (all 3–5 min, rc=0) — intermittent.
  Same location block as above.
- **Carried from the branch predecessor** (all unchanged): #3 two `hmad-dispatch.sh` wrapper bugs
  (inherited HemaSuite cfc79129); #5 101 classified skill-candidate rows in HemaSuite's stores
  (decision is this repo's; re-run the census, never carry 443/189); #7 `docsections.py`
  `_fence_aware_end` dedupe — **now inside doc-block-exec Task 1** (closes with 5e, keep the todo
  until then); #8 file a skill-candidate row "pytest run leaks exec-pane agy panes"; #9
  `docs/skill-candidates.md` census — scout skipped this closeout too (`--skip-scout`, context 68%).
  55 untracked `.done` markers — deliberate, do not commit.
- **`pending-handovers` returned rc=2 once** (an unreadable brief somewhere in the store) after the
  exec-agy takeover stamp; it printed no `UNREADABLE:` path on re-run — re-check at next resume.
- **#19 closed by this doc**: the six learnings committed at `227da1d` are tagged with this
  handoff's slug.

## Context for Next Session

**Files touched this session:**
- `docs/02-design/features/doc-block-exec.design.md` (v1.47 → v1.61), `docs/01-plan/features/doc-block-exec.plan.md` (v1.50 → v1.62), `docs/01-plan/features/doc-block-exec.spec.md` (v1.37 → v1.38)
- `docs/01-plan/features/doc-block-exec.impl-plan.md` (new, v1.9) and 30+ audit reports `doc-block-exec.{design.audit.v42–58,plan.audit.v38–49,impl-plan.audit.v1–9}.*`
- `.claude/agents/implplan-author.md` (new), `.h-mad/wires.jsonl` (3 wires), `docs/.bkit-memory.json` (two features), `docs/learnings.md`
- `docs/handoffs/2026-09-03-main__hmad-audit-loop-root-causes.md` (read), `…__exec-agy-hang-after-report.md` (Taken-Over-By stamped)

**Uncommitted changes:** none besides `.done` markers (this doc until committed).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
/h-mad do doc-block-exec          # PRECONDITION will FAIL until impl-plan cycle 10 gates; work Next Step 1 first
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env   # PREFLIGHT: PASS expected (pins codex term_f483657a…, agy term_a3b4c1dd…)
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.outstanding-findings.md` (historical), `docs/01-plan/features/doc-block-exec.plan.md` §Measurements ("Scanner grammar corpus", "Heading selector differential")
- `h-mad/SKILL.md` §"Never gate on one audit pass", §"Verifying a review finding before acting on it", §5b wire-pin gate
- Memory: `project_doc_block_exec.md`, `feedback_audit_loop_root_causes.md`
