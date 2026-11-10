# Matt Pocock skills review for handoff and H-MAD

Date: 2026-10-23
Status: Review and enhancement proposals; no skill implementation changes
Package reviewed: `mattpocock-skills@mattpocock`, installed Codex version `1.3.1`
Installed Codex package: `/Users/kimhawk/.codex/plugins/cache/mattpocock/mattpocock-skills/1.3.1`
Upstream: https://github.com/mattpocock/skills
Reviewed upstream commit: `5beb35b040e3de97e54fa9e386d7e42d15c295c2`
Local scope: `handoff/` and `h-mad/` in the skills worktree

## Recommendation

Borrow selected patterns from Matt Pocock's skills while retaining H-MAD's orchestration and handoff's ownership protocol. The strongest gains are clearer instructions, better test design, and more focused handoff documents.

The installed Codex package is version 1.3.1. A Claude Code copy is also installed at version 1.3.1 under `claude-plugins-official`. The handoff, writing-for-agents, and retrospective definitions matched the reviewed upstream versions; the selected Codex and Claude package files compared during the review also matched. This is a targeted comparison, not a whole-package integrity check.

| Priority | Enhancement | Target | Confidence and scope |
| --- | --- | --- | --- |
| 1 | Load instructions by mode or phase | Both skills | Strong structural case; runtime reliability improvement unmeasured |
| 2 | Declare test boundaries and independent expected results | H-MAD | Concrete addition to existing specification and audit contracts |
| 3 | Add redaction and next-session focus | handoff | Small drafting improvement; missing from the reviewed main definition |
| 4 | Reference artifacts instead of repeating them | handoff | Useful with explicit carry-forward safeguards |
| 5 | Report specification and standards findings separately | H-MAD | Reporting refinement over existing independent reviews |
| 6 | Classify retrospective findings by remedy | handoff scout | Extends the existing scout instead of creating a parallel process |

Recommendations are architectural judgments based on source inspection. No improvement in execution quality, token use, or task completion has been measured.

## 1. Load instructions by mode or phase

### Source pattern

Matt's `writing-for-agents` distinguishes ordered steps from reference material. Branch-specific material belongs behind a pointer that states when it must be read; common actions stay inline. The same guidance favors one authoritative definition of each rule and keeping definitions, conditions, and caveats together.

Source: [writing-for-agents](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/productivity/writing-for-agents/SKILL.md).

### Local evidence and proposed adaptation

The reviewed `handoff/SKILL.md` contains approximately 1,377 lines spanning WRITE, READ, LEARN, HANDOVER, and TAKEOVER. A LEARN invocation therefore loads substantial material for unrelated modes. H-MAD also carries installation diagnostics, routing, and phase-specific details in its main definition, although it already uses several reference files.

Keep routing, host-adapter selection, shared invariants, and required reference-loading conditions in each main skill. Move mode-specific handoff procedures and selected phase-specific H-MAD procedures into references. Move historical incident narratives only when their operative guard remains explicit and mandatory at the decision point.

Preserve public section anchors, host adapters, test expectations, and existing links. A shorter file alone is not evidence of a better skill; the migration needs scenario checks demonstrating that the right material is reached before action.

Local sources: [handoff routing](../../handoff/SKILL.md#mode-routing--decide-first), [H-MAD activation](../../h-mad/SKILL.md#activation-surface), and [H-MAD Codex adapter](../../h-mad/references/codex-runtime.md).

## 2. Make test boundaries explicit within existing approvals

### Source pattern

Matt's TDD skill identifies the public interface exercised by a test, what that boundary catches, and what it leaves uncovered. It favors observable behavior, independently derived expected results, and mocks at system boundaries. It rejects assertions that simply reproduce the implementation's calculation.

Sources: [TDD](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/tdd/SKILL.md), [test examples](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/tdd/tests.md), and [mocking guidance](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/tdd/mocking.md).

### Existing coverage and gap

H-MAD already requires testable acceptance criteria, a design test strategy, mock boundaries, meaningful RED evidence, and checks against vacuous or weakened tests. The useful change is to make boundary selection and test-oracle quality first-class specification and audit inputs, reusing those existing checks.

Add a small test-boundaries table to the specification or design:

| Field | Purpose |
| --- | --- |
| Public interface | Where behavior is exercised and observed |
| Acceptance criteria | Which requirements this test proves |
| Expected result source | Spec, independent worked example, known-good fixture, or another defensible oracle |
| Mocked dependencies | External or system boundary being substituted |
| Exclusions | Important behavior the test does not establish |

Approve this through the existing Phase 2–4 checkpoints. Matt requires separate confirmation before testing; importing that literally would interrupt H-MAD's autonomous Phase 5. Keep H-MAD's RED/GREEN gates, mutation checks, and bounded implementation-task semantics intact.

Local sources: [specification and design protocols](../../h-mad/references/inline-protocols.md) and [implementer evidence contract](../../h-mad/references/codex-implementer-prompt.md).

## 3. Add focused drafting checks to handoff WRITE

Matt's handoff tailors the document to the next session's purpose, suggests relevant skills, and explicitly redacts sensitive information. Those checks are absent from the reviewed local main handoff definition.

Add optional next-session focus and suggested-skills fields. Suggested skills should name the intended installed capability and explain its purpose. Treat them as recommendations; the receiving session still applies current instructions, checks availability, and chooses its authorized route. Avoid assuming that every host exposes Claude's `Skill` tool.

Add a redaction check before saving, indexing, stamping comments, or delivering handoff content. Preserve references to credential names or secret locations when needed for resumption, rather than copying secret values from commands or logs. The check should cover transferred briefs as well as ordinary closeouts.

Source: [Matt's handoff](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/productivity/handoff/SKILL.md).

Local sources: [required template](../../handoff/SKILL.md#required-template), [writing guidance](../../handoff/SKILL.md#writing-guidance), and [host mapping](../../handoff/references/codex-runtime.md).

## 4. Reduce duplication without losing obligations

Matt's handoff references existing specs, plans, ADRs, issues, commits, and diffs instead of copying their contents. Apply that rule to explanatory material and artifact bodies.

Every inherited open item must still retain an entry with its status, origin, location, and next action or closure evidence. The existing carry-forward protocol addresses observed backlog loss. A pointer to a previous handoff is not sufficient accounting for all of its obligations.

Keep `Supersedes` semantics and the rule that sources are retired only after their items have actually been consumed. The goal is less repeated narrative, not a smaller apparent backlog.

Sources: [Matt's handoff](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/productivity/handoff/SKILL.md) and [local carry-forward contract](../../handoff/SKILL.md#carry-the-predecessors-open-items-forward).

## 5. Separate specification and standards findings in H-MAD reviews

Matt's review distinguishes behavioral fidelity from repository standards and evaluates those concerns independently. H-MAD already has a fresh-context change reviewer, architectural review, specification coverage analysis, and project invariants.

Refine the existing review rubric and reporting rather than adding another mandatory review stage:

- **Specification:** requirement and acceptance-criterion traceability, omissions, wrong behavior, and scope creep.
- **Standards:** repository conventions, project invariants, and a small advisory baseline for maintainability problems.

Keep verified specification or invariant violations blocking. Keep stylistic observations advisory unless an existing project rule makes them mandatory. Distinct reporting should clarify evidence, not flatten H-MAD's existing finding classes or create a new approval hierarchy.

Sources: [Matt's code review](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/code-review/SKILL.md), [local change reviewer](../../h-mad/agents/change-reviewer.md), and [verification protocol](../../h-mad/references/inline-protocols.md).

## 6. Improve the existing scout's remedy selection

Matt's retrospective distinguishes navigation problems, missing or unwired checks, judgment-based standards, and tool inefficiency. For mechanical failures, it favors a deterministic check over another prompt instruction and first checks whether the required mechanism already exists.

The local automation scout already records recurring patterns and reconciles its candidate backlog against source. Extend that process with remedy categories: navigation pointer, existing-tool repair, deterministic check, judgment-based review rule, tool improvement, or skill candidate. Preserve its recurrence threshold, existing-candidate reconciliation, and bounded output.

Sources: [Matt's retrospective](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/retro/SKILL.md) and [local automation scout](../../handoff/references/automation-scout.md).

## Additional lower-priority candidates

The independent H-MAD comparison identified two useful design checks that should remain advisory until actual task plans demonstrate the need:

- **Demonstrable vertical slices:** H-MAD already has a task DAG, dependencies, acceptance criteria, and file/test paths. Add an end-to-end behavior and verification scenario where a module-shaped task would otherwise hide a horizontal implementation step. Do not require every operational or controlled-refactor task to pretend it is independently demoable.
- **Interface value:** for a proposed new adapter or boundary, ask what varies across it now and whether its interface is simpler than the complexity it hides. Use this during design review instead of adding abstractions to satisfy a vocabulary.

Sources: [Matt's ticket decomposition](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/to-tickets/SKILL.md), [module design](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/codebase-design/SKILL.md), and [local implementation-plan protocol](../../h-mad/references/inline-protocols.md).

## Contracts to retain

| Upstream pattern | Local adaptation boundary |
| --- | --- |
| Temporary-directory handoff | Retain the durable main-worktree document store, branch-qualified discovery, and historical chain |
| Per-ticket branches and worktrees | Retain H-MAD feature claims, dispatch ownership, and existing integration/closure rules |
| Separate test-boundary confirmation | Resolve boundaries in existing manual checkpoints; preserve Phase 5 autonomy |
| One test followed by implementation; refactoring deferred to review | Retain H-MAD's established RED/GREEN gates and permitted post-GREEN work; redesigning the loop needs a separate evaluation |
| Generic or automatic skill composition | Use host adapters and actual installed capabilities; preserve fresh author/reviewer contexts |
| Concise handoff through artifact references | Preserve explicit accounting for every inherited obligation and its origin |

Both packages expose a skill named `handoff`. Invocation must select the intended package through the host's supported namespacing or explicit installed skill path. Do not assume unqualified invocation resolves to the local ownership-aware workflow.

Source: [upstream naming policy](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/.out-of-scope/harness-name-collisions.md).

## Follow-up checks before implementation

- [ ] Define which sections remain inline and which move behind mandatory mode/phase pointers; preserve anchors and test consumers.
- [ ] Verify READ still halts in a loaded context while TAKEOVER retains its permitted mid-session behavior.
- [ ] Verify branch selection, ownership transfer, carry-forward accounting, and origin attribution survive any document reorganization.
- [ ] Verify draft redaction across ordinary WRITE, transfer briefs, comments, and delivery without removing actionable credential references.
- [ ] Check that next-session focus and suggested skills do not override current user instructions or silently start another workflow.
- [ ] Add test-boundary and oracle fields within existing specification/design approvals; verify no new Phase 5 confirmation gate appears.
- [ ] Pilot separate Spec and Standards reporting using existing reviewers and finding classes before making it a mandatory rubric.
- [ ] Verify scout classifications reuse existing checks and tools before proposing new instructions or skills.
- [ ] Compare a small set of actual invocations before and after progressive disclosure; measure correct reference loading and preservation of gate behavior, not just document length.

## Validation limits

The review used installed package files, pinned upstream sources, and local skill/reference inspection. A separate read-only reviewer compared the H-MAD implementation patterns and identified existing coverage, gaps, and conflicts. No reviewed workflow was invoked, no runtime tests were run, and no package was installed or updated for this review.

Graft and OneContext execution remained blocked by the active H-MAD Phase 5 shell policy. Plain read-only file access and the GitHub connector supplied the evidence. Prior conversation history was not independently retrieved, and no hook policy or workflow state was changed.
