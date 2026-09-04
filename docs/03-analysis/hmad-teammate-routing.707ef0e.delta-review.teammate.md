## Summary

The delta is **not** clean. Eight of the eleven fixes close their finding cleanly, but two introduce
new defects and one leaves a residual the fix's own text claims does not exist. The bootstrap step
you flagged is wrong, though not by a directory level — it silently produces five dangling links on
a relative skills symlink, which `h_mad_install_check.py` reports as `INSTALL: PASS`. The corpus
number is wrong in both files, and that one originated in my round-1 nit rather than in your edit.
The suite still reproduces: 2486 passed in 369s under python3.11.

Evidence: 9 files opened, 14 greps run, 2 shell probes of the new bootstrap expression, 1 full suite
run. This pass only, delta-scoped.

## Must-fix

- **The new bootstrap step creates five dangling agent links whenever the skills symlink is
  relative, and nothing upstream stops it.** I evaluated the expression on this machine and in two
  constructed installs. Here it resolves correctly to `/Users/kimhawk/orca/skills/h-mad`. With a
  relative link (`ln -s ../../orca/skills/h-mad ~/.claude/skills/h-mad`), the inner `cd` runs from
  the project root that §"Bootstrap action" invokes it in, fails, `pwd` never runs, and the
  substitution collapses to `SK=/h-mad`. `ln -sfn` then exits 0 five times and writes five links to
  `/h-mad/agents/*.md`, none readable. Second case, an install directory that is a stale copy rather
  than a symlink: `readlink` prints nothing, `dirname ""` is `.`, `cd .` is the project root, and
  `SK=<project-root>/h-mad` — five more dangling links, again `ln rc=0`. The halt does not guard the
  relative case: `h_mad_install_check.py:60-61` tests `is_symlink()` then `.resolve()`, and
  `Path.resolve()` resolves a relative link against the link's own directory, so a relative install
  is `INSTALL: PASS`. Prescription: replace the derivation with `SK="$(cd -P
  ~/.claude/skills/h-mad && pwd)"`, which I verified resolves correctly in both constructed cases,
  and add a post-link verification loop that fails loudly — `for n in …; do [ -r
  ~/.claude/agents/$n.md ] || echo "DANGLING: $n"; done`. A silent dangling link is strictly worse
  than the gap this step replaced, because `head -2 ~/.claude/agents/<name>.md` (the verification
  item 3 prescribes) then reports a missing file rather than a wrong one.
  quote: h-mad/SKILL.md:169 › `SK="$(cd "$(dirname "$(readlink ~/.claude/skills/h-mad)")" && pwd)/h-mad"   # the checkout, not the symlink`

- **`31 reports` does not belong to the `c45–75` window, and the pairing is now asserted in two
  files. This defect is mine, not yours** — my round-1 nit claimed the measurement doc "scores
  window c45–c75, which it describes as 31 reports", and your edit is a faithful application of a
  wrong prescription. The source separates the two figures explicitly: the 31-report count carries
  `agy 12`, and the very next sentence says the twelfth is c76, *outside* the c45–75 window. So a
  report at c76 is inside the 31 and outside `c45–75`, and the two cannot label the same set.
  Prescription: drop the report count in both files and keep only what the source states —
  `over c45–75, agy produced 6 fabricated must-fixes out of 11 … codex 0 of 25`. Do not substitute
  `31 cycles` or any arithmetic replacement; the measurement never states a report count for that
  window, and inventing one repeats the class. Sites: `h-mad/SKILL.md:2119` and
  `h-mad/agents/doc-auditor.md:20`.
  instance of: the class is "a figure copied from a source must carry the source's own scope label,
  and two figures the source separates must not be welded into one apposition". Worth noting for the
  fix-introduced statistic you cited: this one entered one step *upstream* of the fix, in an
  unquoted round-1 nit. My round-1 nit was the only finding of eleven that carried no `quote:`
  continuation, and it is the only one that was wrong.
  quote: docs/03-analysis/hmad-audit-evidence-gate.measurement.md:25-27 › `Counts re-derived, not carried: **37 must-fix bullets over 31 reports — agy 12, codex 25.**
  Codex's 25 matches the brief exactly. agy's 12 vs the brief's 11 is **c76, one cycle outside the
  brief's c45–75 window** — settled, not a double-count.`

## Should-fix

- **The two agent-registration blocks now give opposite instructions about the same file.** Item 3
  says to delete a project-scoped copy; the bootstrap step you added says to report it and not
  delete it. Both are defensible readings, but a reader following item 3 destroys what the operator
  of step 4 was told might be a deliberate override. Prescription: keep the step-4 wording, which is
  the safer of the two, and reduce item 3 to a pointer at it.
  quote: h-mad/SKILL.md:38-39 › `A **project-scoped** `.claude/agents/<name>.md` shadows the user-scope link, so a copy left
  there is a fork that drifts silently — remove it rather than editing it.`

- **The fix closes three revision sites and adds a claim that those are all of them; a fourth site
  is in the same document.** The `UNSHAPED` remedy on the wire-pin gate instructs an impl-plan
  regeneration in the orchestrator's own context, with no re-dispatch to `implplan-author`. This is
  the residual you asked for. Prescription: route it — "return to 5a and re-dispatch
  `implplan-author` against the current template" — and then the closure claim is true as written.
  I swept the alternatives and they are clean: Phase 4's back-propagation routes through Phase 3's
  loop, which now re-dispatches; the `unpinned:` remedy on the same line already says "return to
  5a", which the 6db8e50 rewrite covers; Phase 6b iterate edits production files and
  `docs/03-analysis/<feature>.analysis.v<N>.md`, never a phase document; and the rejections ledger
  writes a sidecar file and explicitly forbids editing the gated document. So :405 is the only
  member left.
  quote: h-mad/SKILL.md:1140-1141 › `The sites that revise are Phase 3's audit loop, Phase 4's (which inherits it) and
  5b's — all three re-dispatch, none of them regenerate in your context.`

- **The rewritten schema description names a code consumer that does not exist.** I grepped
  `codex_status` across `h-mad/scripts/` and `h-mad/hooks/`, excluding the schema itself: every hit
  is in `hooks/h-mad-tdd-gate.sh` (lines 139, 142, 148, 149). No audit-path script reads the field —
  `h_mad_audit_gate.py`, `h_mad_audit_cycle.py` and `h_mad_collect_report.py` contain no reference
  to it. Consumer (2) is the orchestrator following SKILL.md prose, not "the audit gate", so a
  maintainer who greps for the second consumer finds nothing and concludes the description is stale.
  Prescription: reword to "(2) the orchestrator, when choosing the second audit surface — see
  SKILL.md §'Teammate audit leg'; no script reads it for this purpose." The rest of the rewrite is
  accurate, including the one-switch-two-effects sentence, and the file still parses as JSON with
  the enum intact. No test asserts on the description string.
  quote: h-mad/scripts/h_mad_state_schema.json:145 › `Two consumers read it.`

- **Adding item 3 to the bootstrap trigger widened an auto-fired action's blast radius from the
  project directory into the user's home config, on a verb documented as read-only.** Before
  707ef0e the trigger covered items 4 and 5, and bootstrap wrote only under the project root. Now
  any of the three invocations that "auto-bootstrap if needed" can write into `~/.claude/agents/`,
  including `/h-mad status`, which the activation table calls read-only. Compounded with the finding
  above, `/h-mad status` on a machine with a relative skills symlink silently writes five broken
  links outside the project. Prescription: fixing the `SK` derivation removes the damage; separately
  either drop "Read-only" from the status row or exempt status from item 3's trigger.
  quote: h-mad/SKILL.md:14 › `| `/h-mad status [<feature>]` | Auto-bootstrap if needed. Read-only. Print state from `docs/.bkit-memory.json`.`

## Nit

- The inline comment on the derivation is inaccurate about what it produces. `SK` is
  `<checkout>/h-mad`, which is the correct value to append `agents/` to, but the comment claims it
  is "the checkout". The checkout is the parent. Harmless today; it is the kind of comment that
  invites the next editor to strip the `/h-mad` suffix.
  quote: h-mad/SKILL.md:169 › `# the checkout, not the symlink`

- Verified rather than filed, recorded so the residual on the number class is explicit: `v1.52 →
  v1.55 in one session` in the new spec paragraph matches
  `docs/handoffs/2026-09-04-main__coder-teammate-audit-surface-and-5b-gating-round.md:16` exactly.
  The value sweep on the other two figures is complete — no `over 30 cycles` and no `all seven`
  survive anywhere in `h-mad/`, and the only remaining hits are inside the persisted round-1 report
  at `docs/03-analysis/hmad-teammate-routing.6db8e50.review.teammate.md`, where quoting the old text
  is correct. `82 codex + 72 agy + 32 impl-plan` is gone from `h-mad/` entirely, and `.teammate` is
  now in the discriminator census comment.

- The eight fixes I have not otherwise mentioned each close their finding rather than its instance,
  and I checked the class in each case: the `Effort:`/`Evidence:` limit is stated with the manual
  check that remains; the `82 codex+agy design cycles` figure is now copied verbatim from its
  source; the `HMAD_CODEX_UNAVAILABLE` paragraph correctly scopes the env var to the hook; the
  one-switch-two-effects note lands in both SKILL.md and the schema; the spec's missing audit phase
  is explained rather than papered over and its revision path is routed to `spec-author`; and the
  `ten`-row and `.teammate` census corrections match their tables.
