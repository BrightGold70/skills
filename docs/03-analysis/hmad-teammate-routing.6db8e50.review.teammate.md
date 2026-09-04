## Summary

Commit `6db8e50` routes phase-document authoring to five tracked teammate agents and adds a
`doc-auditor` gating leg for when codex cannot run. The five `subagent_type:` names all resolve to
tracked files whose frontmatter `name:` matches, the user-scope symlinks exist on this machine with
no project-scope shadow, the `--surface teammate` "no code change" assertion is TRUE against every
consumer I could find, `codex_status` really is a validated enum that rejects an off-enum value, and
the commit's `2486 passed` reproduces exactly. Two defects are load-bearing: the leg that now GATES
is the only surface with no mechanical evidence check, and one of the new measured figures relabels
per-phase cycle counts as per-surface counts.

Evidence: 16 files opened, 23 greps run.

## Must-fix

- The teammate leg is escalated to **gating** while being the only surface with **no mechanical
  evidence check**, and the section that demands an evidence floor demands it only of the leg that
  does *not* gate — so the change moves the gate onto the surface whose effort nobody can measure.
  `h_mad_audit_cycle.py:373-376` renders `tools=/ok=/failed=/thinking=` and the `low-evidence` label
  from the NDJSON of passes *it* dispatches, and `h_mad_review_evidence.py` (`scan(log_text)`,
  lines 1-60) counts tool events out of a dispatch log. An `Agent(subagent_type: "doc-auditor")`
  dispatch produces neither artifact. The only evidence signal is the `Evidence: <N> files opened,
  <M> greps run.` line the agent writes about itself in `agents/doc-auditor.md:97` — which is
  precisely what §"An agent's reported numbers are a claim, not a measurement" (SKILL.md:1190)
  forbids taking at face value. Prescription: add a bullet under §"What this leg does NOT license"
  stating that this leg has no measurable `Effort:` block, that its `Evidence:` line is a claim
  rather than a measurement, and that the operator's only available check is grep-verifying the
  report's `quote:` spans and cited `path:line` locations against the tree before acting on them.
  This is a documentation prescription, not a code change.
  quote: h-mad/SKILL.md:2106-2108 › `Score the
  pass by its `Effort:` block (`h_mad_audit_cycle.py` renders `tools=/ok=/failed=/thinking=` and
  labels `low-evidence`), and treat a low-evidence pass as a **non-verdict** rather than a clean.`

- The escalation figure relabels **per-phase cycle counts as per-surface counts**, so two of the
  three numbers assert something their only source does not. The source sentence is a single
  design-phase figure across both surfaces; the SKILL.md rendering splits it into a codex count and
  an agy count, and `72`/`32` are the *plan* and *impl-plan* prior-cycle counts, not agy or
  impl-plan surface counts. Verified against
  `docs/handoffs/2026-09-04-main__coder-teammate-audit-surface-and-5b-gating-round.md:26` (`82
  codex+agy design cycles had not`) and `:13` (the round ran at `design c82 / plan c73 /
  impl-plan c33` and `found **6 must-fixes**`). Prescription: copy the handoff's wording verbatim
  rather than re-deriving new numbers — `6 confirmed must-fixes in one round that 82 codex+agy
  design cycles had missed`. Do not recompute 82 vs 81 from the `v{82,73,33}` filenames; that is the
  fix-introduced-defect class this commit exists to close.
  instance of: the class is "every measured figure the new sections quote must be traceable to one
  sentence in one source document, copied not paraphrased". The residual after fixing this one: I
  cross-checked the other eight figures and they hold — `83/74/34` (handoff:67), `~half`
  (handoff:74), `6 fabricated of 11` and `codex 0 of 25`
  (`docs/03-analysis/hmad-audit-evidence-gate.measurement.md:99`), `58` and `2` tool calls
  (handoff:32,149,152), `21 of 22` (handoff:74), `six defects … none by me re-reading`
  (handoff:53), `98` real audits (SKILL.md:2275, self-consistent).
  quote: h-mad/SKILL.md:2091-2092 › `The teammate leg was escalated to gating on **yield** — 6 confirmed must-fixes
  in one round that 82 codex + 72 agy + 32 impl-plan cycles had missed`

## Should-fix

- The new leg says Phase 5 has "its own `codex_status` path" while the paragraph above says it keys
  off the "same declaration" — both cannot be true, and the tree says the second one is. The TDD
  gate reads `.orchestrator_state[$k].codex_status` (`hooks/h-mad-tdd-gate.sh:141-145`) and falls
  through on `unavailable|exhausted` for whichever feature has `phase == "step5"` (line 96-99).
  5b is inside `step5` (SKILL.md:387 is reached after 5a writes `phase = "step5"`), so a declaration
  made to route a 5b *document* audit is live for 5d/5e *production* authoring on the same feature.
  I am not filing this as a safety hazard: a codex that is quota-exhausted for auditing is
  exhausted for authoring too, so the two conditions do not normally diverge, and the declaration is
  explicit either way. The defect is the contradiction plus a missing instruction. Prescription:
  reword the bullet to say the declaration also governs 5d/5e and must be flipped back to
  `available` before 5d if codex returns, and widen the schema description at
  `scripts/h_mad_state_schema.json:145`, which currently scopes the field to the Phase-5 implementer
  alone.
  quote: h-mad/SKILL.md:2099-2101 › `- **It does not extend to Phase 5 production code.** 5d/5e authoring is governed by the TDD gate
  hook and its own `codex_status` path (§"Codex authors Phase 5"); this section covers phase
  *documents* only.`

- `HMAD_CODEX_UNAVAILABLE=1` is offered as an audit-leg declaration you "read back", but nothing in
  the audit path reads it and it leaves no record to read. A tree-wide grep finds it in exactly
  three places: `hooks/h-mad-tdd-gate.sh:140,143,150`, `tests/test_h_mad_tdd_gate_codex.py:10,92`,
  and the two SKILL.md prose sites. It is a PreToolUse-hook env override, not state, so on the audit
  side it is both unreadable and unauditable — which contradicts the same paragraph's
  "explicit and auditable, never silent". Prescription: for this section drop the env-var option and
  require the `codex_status` write, or say plainly that the env form governs only the Phase-5 hook.
  quote: h-mad/SKILL.md:2035-2037 › `or `HMAD_CODEX_UNAVAILABLE=1` for a one-off. **Falling back is explicit and auditable, never
  silent**, for the same reason it is at Phase 5: a false declaration is a visible lie in the state
  record rather than an invisible shortcut. Declare it, then read it back before you route on it`

- 5a was rewritten to dispatch `implplan-author`, but 5b's revision loop still instructs the
  orchestrator to regenerate the document itself. That is the loop the commit message says it is
  closing, and it is the one that consumed 34 impl-plan cycles. Prescription: route 5b's
  regeneration to `implplan-author` the same way §"Teammate authors" routes a revision.
  instance of: the class is "every site that *revises* a phase document, not only the site that
  first authors it". Members: SKILL.md:248 (`wait for user revision`), :249 (`Same audit cycle
  pattern as Phase 3`, inheriting it), :387 (`regenerate impl-plan`). Phase 2's spec has no revision
  loop in this document, so that is the residual to confirm rather than assume.
  quote: h-mad/SKILL.md:387 › `If must-fix > 0 OR should-fix > 0, regenerate impl-plan with both must-fix AND should-fix bullets appended`

- Per-phase items 3 and 4 and the 5b bullet still name a **single** audit surface, which the new
  routing paragraph directly contradicts. §"Never gate on one audit pass" now says the two surfaces
  are `codex` + `agy`, or `doc-auditor` + `agy`; items 3/4/5b say the audit runs "via agy". A reader
  following the per-phase list alone runs one surface and never reaches the union rule.
  Prescription: replace "via agy" and "same agy audit-prompt mechanism" with a pointer to
  §"Never gate on one audit pass" for surface selection.
  quote: h-mad/SKILL.md:248 › `then auto-cycle: audit-plan via agy → awk gate`

- New bootstrap item 3 is a check with no action behind it. §"Bootstrap action" (SKILL.md:139-168)
  has five numbered steps and none of them registers the agents, and the routing sentence at
  SKILL.md:46 covers only items 4 and 5. So on a fresh clone the one condition the commit message
  says did not survive a fresh clone is detected by nothing and repaired by nothing; the stated
  mitigation is that `Agent(subagent_type: …)` fails loudly at dispatch time, which is accepted risk
  rather than a remedy. Prescription: add the symlink loop as a step in §"Bootstrap action" and
  include item 3 in the "run bootstrap automatically" trigger. Verified on this machine that all
  five links exist and point into this checkout, and that `.claude/agents/` in the project root does
  not exist, so nothing is currently shadowed — the gap is for a fresh clone, not for here.
  quote: h-mad/SKILL.md:46 › `If 4 or 5 is missing → run bootstrap automatically, then continue with the requested operation.`

- `doc-auditor.md`'s frontmatter advertises a **spec** phase that no tool in the pipeline accepts.
  `scripts/h_mad_assemble_audit.py:36` sets `PHASES = ("plan", "design", "impl-plan")` and binds it
  to `--phase` as argparse `choices` at line 280; `scripts/h_mad_collect_report.py` declares the same
  closed triple. SKILL.md's own dispatch template correctly writes `--phase plan|design|impl-plan`.
  A spec audit therefore cannot be assembled or collected. Prescription: either drop `spec` from the
  agent description, or add it to both `PHASES` sets and to the docs path resolution.
  quote: h-mad/agents/doc-auditor.md:3 › `Audits one H-MAD phase document (plan / design / impl-plan / spec)`

## Nit

- `over 30 cycles` for the agy fabrication figure is one short of its source. The measurement doc
  scores window c45–c75, which it describes as 31 reports, and flags that agy's own count is 12 once
  c76 is included. `agents/doc-auditor.md:20` carries the same `over 30 cycles`, so the two agree
  with each other and both disagree with the measurement by one.
  quote: h-mad/SKILL.md:2088-2090 › `agy produced 6 fabricated must-fixes out of 11 over 30 cycles on one feature, codex 0 of 25 on
  the same corpus`

- Pre-existing, not introduced by `6db8e50`: the `INSTALL: FAIL` detail-line table has **ten** rows,
  and the sentence introducing it says seven. Counting the table at SKILL.md:55-64:
  `SKILL_NOT_INSTALLED`, `SKILL_NOT_SYMLINK`, `SKILL_DANGLING`, `SKILL_NOT_A_CHECKOUT`,
  `HOOK_NOT_INSTALLED`, `HOOK_DANGLING`, `SPLIT_INSTALL`, `SIBLING_NOT_SYMLINK`, `SIBLING_DANGLING`,
  `SIBLING_WRONG_CHECKOUT`. The same ten are listed in the helper-script entry at SKILL.md:2119.
  quote: h-mad/SKILL.md:51 › `detail lines each name one remedy, and all seven have one:`

- Pre-existing, not introduced by `6db8e50`, but now stale because of it: the corpus enumeration in
  `scripts/h_mad_cycle_counts.py` lists the observed discriminator tokens as `''`, `.p1`, `.p2`,
  `.p3`, `.codex`, `.agy`, `.claude`. Six `.teammate` audit files now exist under
  `docs/01-plan/features/` and `docs/02-design/features/`. The regex is open, so nothing is broken —
  only the comment's census is out of date. Prescription: add `.teammate` to the enumerated list.
