# Handoff — doc-block-exec 5b: rounds three, four and five

**Date:** 2026-09-04
**Branch:** `main`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-04-main__audit-loop-p1-p3-shipped.md (branch predecessor; every open item carried below), 2026-09-03-main__exec-agy-hang-after-report.md (absorbed *through* the predecessor, which recorded its one item **#22** closed at `bea1b60`/`3f50b95`; I did not re-read it this session and carry no residual from it), 2026-09-03-main__hmad-audit-evidence-gate.md (absorbed the same way; its residual is **#27**, re-emitted below unchanged)

## Session Summary

Ran **three full gating rounds** of the doc-block-exec 5b loop (cycles design 84–86, plan 75–77,
impl-plan 35–37), each on two surfaces — a gating `doc-auditor` teammate per phase beside an agy
leg — with four author revisions between them. **The gate was not met in any round**: 9, 7 and 8
must-fixes respectively, every sampled finding verified against the tree before it reached an
author, and **zero fabrications** across nine teammate reports. Documents went design v1.93→**v1.96**,
plan v1.86→**v1.91**, spec v1.55→**v1.58**, impl-plan v1.36→**v1.40**; five commits pushed,
`0aac0b7` is HEAD, suite **2547 passed**. Outcome: **partial** — the loop is healthier and no
closer to stamping. A real codex round is still owed before anything gated by a teammate leg is
treated as settled.

## Key Learnings

- **The enforcement a revision ships is the next defect, three rounds running.** plan v1.90's class
  screen contained `\btoday\b`; in awk `\b` is a **backspace escape**, not a word boundary, so that
  term was dead code and the "after: 0" it published was measured by a screen blind to one of its
  own enumerated forms. Probed on `awk version 20200816`: `awk '/\btoday\b/'` matches nothing on
  "measured today" while `/today/` matches, and `printf 'a\bb\n' | awk '/\b/'` matches. Fix is a
  POSIX-ERE boundary; the counts had to be re-measured, not carried.
- **"Stronger" is not "correct".** I made the spec's enumeration canonical because it was the
  stronger of two. Executed against controls it failed the *same* class: its gap was `([a-z]+ )?`,
  one optional lowercase word, blind to ``Twenty-four tracked `.py` files`` — a member sitting in
  the paragraph that defines the rule. The control execution found it; the comparison did not.
  **Any checker shipped as a class closure must be run against a positive and a negative control
  before its counts are believed.**
- **A sweep that enumerates VALUES can only find members that have already drifted.** That is why
  plan v1.88's closure left survivors, along with two other causes worth keeping: the axis read
  "without the sha", so a member with a command but no sha passed; and the rule lived in a Version
  History entry rather than in the section that binds.
- **A digits-only count sweep misses word-form counts.** The spec writes most of its counts as
  words ("seven bash blocks", "Twenty-four tracked files"), so a digits-only screen misses the
  majority of its own members.
- **Locator uniqueness is COMMIT-SCOPED.** A locator verified unique when authored can be broken by
  a concurrent sibling edit in the *same* commit: `grep -n 'both halves of'` on the design was 1 hit
  at `335f535` and 2 at `74e126f` because design v1.95 added ":904 both halves of its base",
  breaking the impl-plan's locator. The spec then hit the rule on itself — publishing its needle as
  a plain substring made its own count 2, because the publishing sentence reproduced it.
- **Ordinals drift silently and are usually already wrong when you find them.** `_close_stream` was
  called "the sixth named injection" and is *seventh*; `_final_write`'s "fifth" was the stale v1.23
  value. Address by content predicate — which is what the code actually does (`_gate_bash_block`
  filters on `"h_mad_audit_gate.py" in b` and asserts exactly one) — and treat an ordinal as
  informational, naming its base.
- **Splitting one decision across a subset of authors manufactures contradictions.** I sent the
  AC-6.4 reconciliation to the plan and impl-plan authors and not to design, and an index correction
  to design alone. Two of round four's three design must-fixes were consequences. Rounds four and
  five used ONE decision sheet in identical words to all four authors, and the cross-check came back
  clean both times.
- **`\b`-style dead code and hollow reviews look identical to success.** The #13 evidence gate fired
  twice in the field this session (design c86 at `tools=2`, impl-plan c35 at `tools=1`), each time
  refusing to let a fluent clean report certify a document nobody read.
- **A low tool count is not proof of hollowness when the prompt inlines the documents.** plan c75's
  agy leg ran `tools=1` and produced three must-fixes, all verified real — a cross-document
  consistency finding needs no reads. The guard is correctly one-directional: it can refuse a clean,
  never manufacture a FAIL.
- **`git diff --name-only <a> <b>` unscoped is not the same question as scoped.** design:186 claimed
  "two files, both `.py`"; unscoped it names 13, 11 of them `.md`. The conclusion survived only
  because those 11 are under `docs/` — a reason the sentence never gave, and the document's own
  trip-wire fired on its own tree.

## Next Steps

1. **Round six of the 5b gating loop, from a fresh full-context session** — cycles design 87 /
   plan 78 / impl-plan 38 at `0aac0b7`. Freeze the tree, run the precheck on each document first
   (impl-plan needs the six `--allow` spans, below), assemble with
   `h_mad_assemble_audit.py`, dispatch a `doc-auditor` teammate per phase **and** the agy leg, tell
   each auditor it is gating, and **point each at the delta first**:
   `git diff 74e126f..0aac0b7 -- <document>`.
2. **Re-dispatch the two agy legs round five did not complete** — impl-plan c37 never ran, and
   design c86 came back `UNVERIFIED reason=low_evidence` (`tools=2`). Both are owed at their next
   cycle. — `hmad-dispatch audit-cycle --feature doc-block-exec --phase <p> --cycle <N> --passes 1 --surfaces agy --project-root /Users/kimhawk/orca/skills`
3. **When codex returns 2026-09-07 11:28**, run one round with the real codex leg before stamping
   anything, and **flip `doc-block-exec.codex_status` back to `available`** —
   `python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json --feature doc-block-exec --set codex_status=available`
4. **If a round comes back clean on both surfaces at ONE commit:** `h_mad_audit_gate.py … --gated`
   per phase, then `h_mad_wire_pin_gate.py … --feature doc-block-exec`, then 5c
   `git checkout -b feature/doc-block-exec`. Claim `doc-block-exec` first with plain `--claim`.
5. **[P5] The remaining backlog** — #9's five unverified skill-candidate rows, #8's pytest agy-pane
   leak row, #5's 101 HemaSuite rows (foreign lane).

**The impl-plan precheck invocation, needed by every future round** (its eight PLACEHOLDER hits are
all output-line grammar declarations, verified false positives — do not edit them away):

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py \
  docs/01-plan/features/doc-block-exec.impl-plan.md --phase impl-plan --root /Users/kimhawk/orca/skills \
  --allow 'stream: "<name>"' --allow 'os_error: "<text>"' --allow 'overlap: "<a>" "<b>"' \
  --allow '<key>=<bare>' --allow '<key>="<json-string>"' --allow 'pgid: "<n>"'
```

## Open / Blocked Items

- **doc-block-exec 5b — gate NOT met, nothing stamped.** Design v1.96 / plan v1.91 / spec v1.58 /
  impl-plan v1.40 at `0aac0b7`. Three rounds run this session, all FAIL. Ready for round six, not
  blocked. `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
- **The claim on `doc-block-exec` is RELEASED at the end of this session** (it was held by
  `f86738c1-9553-4970-8c3d-32e995947817`). Verify with `h_mad_resume_decision.py` before claiming.
- **Codex quota — blocked until 2026-09-07 11:28.** Unchanged. The teammate substitution is the
  standing workaround and is **gating**, by operator decision.
- **`doc-block-exec.codex_status` is still `exhausted` and must be flipped back.** Unchanged from
  the predecessor. One switch, two effects: it also permits Claude to author 5d/5e production code
  for this feature. Flip it before 5d.
- **Round four spans two commits and therefore CANNOT satisfy the exit gate, even in retrospect.**
  plan c76's agy leg ran at `2a348d7`, one commit behind that round's `335f535` freeze — the
  assembler fix landed between them. The four documents are byte-identical across that commit (it
  touched only `h_mad_assemble_audit.py` and its test) and the pass's single finding was about spec
  prose, so the finding stands. But the exit gate requires both surfaces clean **at one commit**, so
  round four must not be counted toward it later. Round five was single-commit (`74e126f`
  throughout) but is disqualified for a different reason: two of its three agy legs did not complete.
- **A gap in my own process, recorded so it is not repeated:** I stopped the round-five agy script
  believing plan c77's leg had not finished. It had — a complete report, `tools=111`, the heaviest
  pass of the session, gating FAIL must=2 — and I dispatched the revision batch without reading it.
  Its live finding had already been fixed by the plan author's independent re-derivation, which was
  luck. **Read every delivered report before dispatching a revision, and check the report file
  rather than the wrapper's END line.**
- **The precheck (#20) is now measured in the field; the effort contract (#17) is not.** #20 caught
  a dead cross-document pin before round three's prompts were assembled — 1 real finding prevented
  at ~1s against a full dual-surface cycle — and fired 8/8 false positives on the impl-plan's
  grammar declarations. #17's efficacy claim is still unmeasured; `h_mad_ab_dispatch.py` exists for
  it and was not run.
- **#13's evidence gate is measured in BOTH directions** (see Key Learnings). Recorded in the task
  list as the field measurement; no further work owed unless the low-evidence heuristic is made
  phase-aware, which needs more than the one observation this session produced.
- **Marker-aware reaping for `exec` — owed, deliberately not built.** Unchanged. Reaping on
  `<report>.done` would end the wait at completion rather than at the ceiling; it needs the wrapper
  to learn the report path, which it does not know. The legible `rc=124` shipped at `3f50b95`
  **proved its worth this session**: design c85's agy leg timed out and the message said a verdict
  had been recovered, preventing a re-dispatch over completed work.
- **#27 deferred evidence check — unchanged, inherited from `hmad-audit-evidence-gate`.** Step 2 was
  **measured and refused**, not skipped: no span-occurrence rule discriminates. Revisit only once
  enough cycles have run under the `quote:` contract to form a corpus. —
  `docs/03-analysis/hmad-audit-evidence-gate.measurement.md`, commit `109a02a`
- **Evidence-gate corpus lives OUTSIDE the repo and is not backed up** — `~/.h-mad-corpora/evidence-gate/`,
  66 files (64 prompts c45–c76 + both measurement scripts). Re-verified present 2026-09-04.
  Unchanged; still the only corpus behind #27's refusal.
- **#7 `docsections.py` `_fence_aware_end` dedupe — unchanged, not started.** Closes with 5e.
- **A HemaSuite skill-candidate row was HANDED OVER and remains theirs** — brief at
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md` (`f5afb219`),
  carrying `**Handover-From:**`. Nothing claimed, nothing released. Not re-checked this session.
  `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree: none`.
- **#9 five skill-candidate rows still not individually re-verified — unchanged, not started.**
- **#5 (101 classified HemaSuite rows) and #8 (pytest leaks exec-pane agy panes) — unchanged, not
  started.** #5 is a foreign lane.
- **`.claude/agents/` question remains CLOSED** — the five agents are tracked at `h-mad/agents/` and
  registered by user-scope symlink. Re-stated because the predecessor carried it.
- **Plan should-fixes from cycles 73/74 — CLOSED this session.** Round three's plan auditor recorded
  the cycle-73 "two leave / two stay" item rather than re-filing it, and plan v1.89 closed it: all
  four `docsections.json` anchors are rewritten, not two.
- **55 untracked `.done` markers** — deliberate, do not commit. Unchanged.

## Context for Next Session

**Files touched this session:**
- `docs/02-design/features/doc-block-exec.design.md` (v1.93 → v1.96)
- `docs/01-plan/features/doc-block-exec.plan.md` (v1.86 → v1.91)
- `docs/01-plan/features/doc-block-exec.spec.md` (v1.55 → v1.58)
- `docs/01-plan/features/doc-block-exec.impl-plan.md` (v1.36 → v1.40)
- `h-mad/scripts/h_mad_assemble_audit.py` + `h-mad/tests/test_h_mad_assemble_audit.py` (the
  inline-code-span preflight fix, `335f535`)
- 11 audit reports under `docs/01-plan/features/` and `docs/02-design/features/` (cycles 84–86,
  75–77, 35–37, `.teammate` and `.p1` surfaces)

**Uncommitted changes:** none besides the 55 `.done` markers (and this doc until committed).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
/handoff read
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env   # PREFLIGHT: PASS expected
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q                 # 2547 expected; bare python3 is 3.14, no pytest
grep -oE '^- v1\.[0-9]+' docs/02-design/features/doc-block-exec.design.md | tail -1   # re-derive, never trust a pin
```

**Related docs:**
- `h-mad/SKILL.md` §"Teammate audit leg", §"Precheck before you dispatch", §"Never gate on one
  audit pass", §"Close the class, never the instance", §"Delta self-review"
- The five commits: `a8e0372` (plan v1.87), `2a348d7` (round three), `335f535` (assembler fix),
  `74e126f` (round four), `0aac0b7` (round five)
