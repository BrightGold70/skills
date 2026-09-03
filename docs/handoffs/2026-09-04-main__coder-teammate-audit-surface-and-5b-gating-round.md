# Handoff — coder teammates replace the codex audit leg; 5b gating round run, gate NOT met; h-mad process debt paid down

**Date:** 2026-09-04
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-03-main__doc-block-exec-5b-parked-codex-quota.md (branch predecessor; every open item carried below), 2026-09-03-main__hmad-audit-evidence-gate.md (taken over 2026-09-03, worked to completion this session — see Open Items), 2026-09-03-main__exec-agy-hang-after-report.md (taken over by `cd979362`; its one item re-emitted below, unchanged and still not started)

## Session Summary

Resumed the parked doc-block-exec 5b loop. Codex is still quota-blocked until **2026-09-07 11:28**,
so the operator directed that a **fresh-context coder teammate replace the codex leg** — first as
an advisory surface, then, after seeing the first round's yield, as a **gating** one. Two audit
rounds ran. The first (advisory, design c82 / plan c73 / impl-plan c33) found **6 must-fixes**, all
independently re-probed and all fixed. The second (gating, c83 / c74 / c34, two surfaces per phase)
found **8 more** and the **exit gate was NOT met — nothing is stamped**. Documents advanced
design v1.90→**v1.93**, plan v1.83→**v1.86**, spec v1.52→**v1.55**, impl-plan v1.31→**v1.36**.
Separately, three h-mad process todos were closed (#10 close-the-class, #12 the 5e revert recipe,
#26 the audit-evidence-gate handover) and #21 was half-built. Outcome: **partial** — the tree is
materially cleaner and everything is pushed, but 5b is not gated and no production code exists.
**Stopped deliberately rather than opening round three**: this session is ~56% context-spent, and
its own evidence is that a loaded context reviewing its own work is the weakest link in the loop.

## Key Learnings

- **A fresh-context Claude teammate is a better document-audit surface than agy, and it found what
  82 codex+agy design cycles had not.** The headline defect: the CLI parser's `exit_on_error=False`
  made it structurally unable to emit the `BAD_ARGS` verdict its own named test asserts (a missing
  option value raises `argparse.ArgumentError` inside `_parse_known_args`, never reaches the
  overridden `error()`, and escapes `main` as a non-`DOCBLOCK` traceback). Phase 5d could not have
  reached GREEN. Contract and standing limits: memory `feedback_coder_teammates_beat_agy_as_second_surface`.
- **agy is not uniformly hollow — gate on its evidence count, don't drop it.** In one round its
  design pass ran **58** tool calls and found a real defect both teammate passes missed (missing
  trailing colons on two API signatures, `quote:` spans verified); its plan pass ran **2**, the
  report-file floor, and returned a PASS worth nothing. Same surface, same round, opposite value.
  That is the strongest data yet for todo #13, and it argues for an evidence gate rather than
  removal.
- **Hold the tree still for a teammate audit round.** Unlike codex, which reads a frozen assembled
  prompt, a teammate auditor reads the **working tree**. I committed a SKILL.md change mid-flight
  and all three auditors returned line numbers correct for what they read and mislabelled by the
  base commit I gave them (`:1897` reported "at `e8eaf6f`", which is `:1887`). I then relayed the
  wrong number onward; `implplan-author-3` caught it by measuring both commits itself.
- **Cross-check any AC that two concurrent authors touched.** Running three authors in parallel
  produced a contradiction neither could see: `design-author` added a dot-directory exclusion to
  AC-6.1 (25 files) while `implplan-author` independently repaired the same AC's rebase (30 files).
  Both measurements were correct and answered different questions. It surfaced only because I read
  the two reports against each other. The file-scoping rule (one author, one document, report what
  others owe) is what keeps this tractable — nothing gets silently harmonised — but the
  cross-check is now an orchestrator duty.
- **A teammate's view of its sibling documents goes stale mid-round.** `implplan-author-4` reported
  "nothing is owed to the spec" and "contradictions found: none new" — both false, because it had
  read the spec before my v1.55 landed. Same shape as every document defect this session: a value
  read at time T, acted on at T+n.
- **Six defects in my own work were caught by fresh contexts; none by me re-reading.** The class is
  one value swept in one surface and not another: the floor numbers twice, the provenance pins, the
  spec's number embedded inside a command comment, the design still carrying a rationale I had
  corrected only in the plan, and a figure *derived* from a measurement (`"three times the 397 s
  baseline"`) that did not move when the baseline was re-measured to 383 s. The last is a distinct
  shape worth naming — not a number stated twice, but a number computed from one that moved.
- **Three carried premises were re-probed and at least partly false**, consistent with
  `feedback_carried_repro_is_not_evidence`: the evidence-check premise (falsified outright), the 5e
  stash rationale (false, *and* its documented fix actively harmful), and an enumeration count
  (9 → 7).

## Next Steps

1. **Round three of the 5b gating loop, from a fresh full-context session.** Assemble design c85 /
   plan c76 / impl-plan c35 at `a1059e5` (numbering past the teammate cycles), dispatch a
   `doc-auditor` teammate per phase **and** the agy leg, gate on the union. Tell each auditor it is
   gating. **Freeze the tree for the duration.** Same commands as this session used —
   `h_mad_assemble_audit.py` → `Agent(subagent_type: "doc-auditor")` + backgrounded
   `hmad-dispatch audit-cycle` → `collect-report --surface teammate` → `h_mad_audit_gate.py`. —
   `h-mad/SKILL.md` §5b, `.claude/agents/doc-auditor.md`
2. **When codex returns 2026-09-07 11:28**, run one round with the real codex leg before stamping
   anything. The teammate surface has **never been scored against a labelled corpus** and shares my
   model family; the operator escalated it to gating on yield, not on validation. A codex round on
   the current tree is the cheapest available check on that decision. — memory
   `feedback_coder_teammates_beat_agy_as_second_surface`
3. **If a round comes back clean on both surfaces at one commit:** `h_mad_audit_gate.py <impl-plan
   audit> --gated docs/01-plan/features/doc-block-exec.impl-plan.md`; design `--gated design plan
   spec`; plan `--gated plan spec`; then `h_mad_wire_pin_gate.py … --feature doc-block-exec` (3
   wires; Tasks 1 and 5 are `wiring`); then 5c `git checkout -b feature/doc-block-exec`. Claim
   `doc-block-exec` first with plain `--claim`. — `h-mad/SKILL.md` §5b/5c
4. **Remaining h-mad process todos, none of which need a second surface:** #11 delta self-review,
   #14 behavioural-premise commands in `invariants.base.md`, #15 ack-sidecar softening (calibration
   data located — see Open Items), #17 reviewer effort contract, #20 impl-plan precheck, #21's
   missing `spec-author`. **#14 and #17 edit `invariants.base.md` / `audit-prompt.template.md`,
   which are inlined into every prompt and will move the size-band fixture** — re-anchor per
   `h-mad/tests/test_h_mad_assemble_audit.py`'s own rule (recalibrate the fixture, never widen the
   band).
5. **#27 (deferred evidence check)** — revisit only once enough cycles have run under the new
   `quote:` contract to form a corpus of reports that actually carry `quote:` lines. —
   `docs/03-analysis/hmad-audit-evidence-gate.measurement.md`

## Open / Blocked Items

- **doc-block-exec 5b — gate NOT met, nothing stamped.** Round two union: design c83 must=3, plan
  c74 must=2, impl-plan c34 must=3, plus one agy finding rejected on evidence. All were fixed into
  design v1.93 / plan v1.86 / spec v1.55 / impl-plan v1.36, so the *findings* are closed but no
  round has been clean. Status: **ready for round three**, not blocked. Claim `doc-block-exec` is
  **released**. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
- **Codex quota** — blocked until **2026-09-07 11:28** (or purchased credits, the operator's call).
  The teammate substitution is the standing workaround and is currently **gating**, by operator
  decision 2026-09-04.
- **`hmad-audit-evidence-gate` (#26) — COMPLETE, with Step 2 deliberately not built.** Steps 1
  (rejections ledger out of `--gated`) and 3 (the `quote:` contract marker) shipped at `ff0a278` /
  `11a7db7`. Step 2 (an automatic evidence check in the gate) was **measured and refused**: no
  span-occurrence rule discriminates — catching 4 of 6 fabrications costs 13 of 31 real must-fixes,
  2 of 6 fabrications carry no absent span at all, and the one zero-cost rule is vacuous. Full
  numbers and the corpus: `docs/03-analysis/hmad-audit-evidence-gate.measurement.md`, commit
  `109a02a`. Carried forward as **#27**. Corpus durable at `~/.h-mad-corpora/evidence-gate/`
  (64 byte-verified prompts c45–c76 + both measurement scripts) — **outside the repo, not backed
  up**.
- **#15 ack-sidecar softening — not started, but its calibration data is located.**
  `…/HemaSuite/…/docs/01-plan/features/gateway-consolidation.plan.audit.v18.md` carries seven
  accreted ack bullets that are ~three underlying findings: items 1/4 and 2/5 are positive pairs,
  and items **6/7 are a negative control** (two genuinely different AC-1.4 leaks that a sloppy
  matcher would collapse). Over-matching here **silently suppresses a real finding**, so this must
  be mutation-tested in both directions before shipping.
- **Plan should-fixes still owed**, non-blocking, from cycles 73/74: two deferred and re-raised
  ("changes at exactly two points" was fixed; `## Scope` was fixed), plus anything round three
  raises. The extractor-census control is **resolved**: `git grep -l '```' -- '*.py'` → 21 at
  `6b4df35`, **23** today; my earlier `grep -rl '```bash' --include='*.py'` → 3 measured a
  different quantity. The command is now inline in the plan.
- **Inherited, all unchanged and not started** — #3 two `hmad-dispatch.sh` wrapper bugs (HemaSuite
  `cfc79129`); #5 101 classified skill-candidate rows in HemaSuite's stores; #7 `docsections.py`
  `_fence_aware_end` dedupe (closes with doc-block-exec 5e); #8 skill-candidate row "pytest run
  leaks exec-pane agy panes"; #9 `docs/skill-candidates.md` census — **scout skipped again this
  closeout**; #16 `collect-report --out` fallback; #22 `exec agy` hang after report (HemaSuite
  `45db0187`, taken over by `cd979362`, not reproduced in ~70 agy execs across two sessions). Same
  location block as above.
- **`.claude/agents/` is gitignored**, so `doc-auditor`, `design-author`, `plan-author` and
  `implplan-author` are **machine-local and do not survive a fresh clone**. Four agents now carry
  real measured process knowledge and none of it is in version control. Worth deciding whether that
  is acceptable.
- **55 untracked `.done` markers** — deliberate, do not commit.

## Context for Next Session

**Files touched this session:**
- `h-mad/SKILL.md` (close-the-class rule; rejections-ledger protocol; the 5e revert recipe + its
  measured table), `h-mad/audit-prompt.template.md` (`quote:` contract marker),
  `h-mad/references/{failure-recovery,codex-verifier-prompt}.md`,
  `h-mad/tests/test_h_mad_agy_review_fixes.py` (both stash guards inverted + mutation-tested),
  `h-mad/tests/test_h_mad_assemble_audit.py` (size fixture re-anchored 2645/2945 → 2440/2740)
- `docs/02-design/features/doc-block-exec.design.md` (v1.90→v1.93),
  `docs/01-plan/features/doc-block-exec.{plan,spec,impl-plan}.md` (v1.83→v1.86, v1.52→v1.55,
  v1.31→v1.36), `docs/01-plan/features/doc-block-exec.impl-plan.rejections.md` (**new**)
- Nine audit reports: `…audit.v{82,73,33}.teammate.md`, `…audit.v{83,74,34}.{teammate,p1}.md`
- `docs/03-analysis/hmad-audit-evidence-gate.measurement.md` (**new**)
- `.claude/agents/{doc-auditor,design-author,plan-author}.md` (**new, gitignored**)

**Uncommitted changes:** none besides the 55 `.done` markers (and this doc until committed).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env   # PREFLIGHT: PASS expected
grep -oE '^- v1\.[0-9]+' docs/02-design/features/doc-block-exec.design.md | tail -1   # re-derive, never trust a pin
```

**Related docs:**
- `h-mad/SKILL.md` §"Close the class, never the instance", §"Record a rejected finding in the
  rejections ledger, never in a gated document", §"Never gate on one audit pass", §5b, §5e
- Memory: `feedback_coder_teammates_beat_agy_as_second_surface`, `project_doc_block_exec`,
  `feedback_audit_loop_root_causes`, `feedback_value_sweep_not_spot_fix`,
  `feedback_carried_repro_is_not_evidence`, `feedback_mutation_test_every_guard` (**corrected this
  session — its stash mechanism did not reproduce**), `feedback_docs_name_hazard_withhold_command`
  (**corrected this session**)
