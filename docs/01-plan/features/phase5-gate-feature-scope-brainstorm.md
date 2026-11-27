# Brainstorm: phase5-gate-feature-scope

## Executive Summary
Arm the Phase-5 gate for a session only when a `step5` feature is being implemented in that session's own checkout, with one shared scoping rule for every gate and a guarantee that a gated agent cannot change what arms or scopes it.

## Problem Statement
The codex and agy shell gates arm when any `docs/.bkit-memory.json` found under the repository root holds a record at `step5`, so a session working on another feature, or in another checkout that shares the state file, is limited to the Phase-5 command list. Codex orchestrator lanes then need an operator-written allow line or patch for each audit cycle (four on 2026-11-23 in HemaSuite).

## Evidence

Scratch repositories, installed hooks at `7a3cca48`, 2026-11-24. The command is one `hmad-dispatch audit-cycle`; each cell is codex / agy.

| State | Decision |
|---|---|
| Feature A not at `step5` | allow / allow |
| A not at `step5`, feature B at `step5` | deny / deny |
| A second checkout whose state file is a symlink to the first's | deny / deny |
| A copy at `step5` in a git-excluded directory | deny / deny |
| An unparsable copy in a git-excluded directory | deny / deny |
| A `step5` state file under `tests/fixtures/` | deny / deny |

Live, 2026-11-24 10:57, read only: a HemaSuite feature is at `step5` in the main checkout, and a worktree is armed through a symlinked state file although its feature is not at `step5`.

From source, not yet driven: the write judge (`read_chain`, `h-mad/scripts/h_mad_tdd_judge.py`) walks only the target's ancestor directories but collects every `step5` record in the state files it finds there.

## Proposed Approach
Operator decisions, 2026-11-24:

1. **Scope by checkout.** A `step5` record names the checkout its code is written in. The gate applies to a session only when that checkout is the session's own. A record that names none arms everywhere, as today, so existing records and older writers fail closed.
2. **Protect the arming inputs in this feature.** A gated agent must not be able to change the fields that arm or scope the gate. Supporting detail is kept outside this public repository.
3. **Root and sub-project state files only.** Keep the root file and real sub-project files. Ignore git-excluded trees, nested checkouts and test fixtures.
4. **One rule for every gate.** One shared function decides which records apply, used by the codex and agy shell gates, the write judge and the Claude hook.

5. **The shell gate arms from 5d, not 5a.** Production-code writes stay gated from 5a. This covers a feature's own orchestrator auditing its impl-plan at 5b. (Confirmed by the operator at spec approval, 2026-11-24.)

Checkout scoping is chosen because it covers both measured incidents without trusting anything the gated session says about itself.

## Alternatives Considered
- **Dispatch declaration** (the dispatcher tells the hook which feature a session serves): works inside one checkout, but hand-started and existing panes declare nothing, and hook environment inheritance is unverified. Rejected as the base rule.
- **Checkout plus declaration**: covers the most, with two mechanisms to get right. Deferred until a same-checkout incident is measured.
- **Widen the safe command list**: rejected by the operator on 2026-11-23. `audit-cycle` runs an arbitrary `--suite-cmd`, so no list can cover it.
- **Owner session id as the scope**: rejected. Implementers never own the record, and the id is only as trustworthy as whoever can write it.
- **Shell gates only, judge unchanged**: rejected; two scoping rules would drift apart.

## Scope

**In:** codex and agy shell arming; write-target arming in both; the write judge and the Claude hook; the state field naming the checkout and its writer; state-file discovery; protection of the arming inputs; the Phase 5 entry and exit documentation.

**Out:** two features implemented in one checkout (they still gate each other); widening the safe list; pre-existing gate follow-ups tracked privately; hand-started sessions that run no hook.

## Risks & Mitigations
| Risk | Likelihood | Mitigation |
|---|---|---|
| The rule opens the gate for a real implementer | M | Fail closed when the field is absent, unreadable, or names a path that does not exist; drive every case through the real hooks; diff old and new decisions |
| Protecting the inputs locks out a legitimate codex orchestrator, which must leave `step5` from a gated session | H | Open question 1; settle before the spec is approved |
| Path identity (symlink, case, linked worktree, moved checkout) is judged wrongly | M | Use the existing canonical-directory helper; hostile fixtures for each spelling |
| Ignoring excluded trees hides a real state file | M | HemaSuite's state file is itself git-ignored in places, so "ignored" alone cannot be the test; spec a rule that keeps `<root>/docs` and real sub-projects |
| The installed skill is live policy on this machine | H | All code in a linked worktree; land in one fast-forward |
| HemaSuite lanes are in `step5` while this lands | M | Records without the field behave as today, so no lane changes state on landing |

## Dependencies
- `74ba0661` (option judging), landed; it edits the same policy file.
- The state schema (`h_mad_state_schema.json`) needs one declared field.

## Open Questions
1. **How does a codex or agy orchestrator legitimately leave `step5`?** It runs gated and must clear `phase`. Matching the hook payload's session identity to the record's owner does not work as things stand: a codex owner id is a random UUID minted into the git directory (`references/codex-runtime.md:174`), unrelated to the payload. Options to weigh in the spec: make that identity comparable, allow only the writes a Phase 5 exit needs under a checkable condition, or have an ungated session do the exit.
2. **The checkout field must be written with `phase = "step5"`, at 5a.** The gate arms at 5a (`references/phase5-substeps.md:134`), while 5c creates the branch. Because a record without the field arms everywhere, writing it at 5c would leave the live case above unfixed: that HemaSuite feature is at 5b now. Open: what is written at 5a when the implementation checkout does not exist yet, and how it may change at 5c when the feature moves to a worktree.
3. **What identifies a checkout?** Canonical toplevel path, or a git-dir identity that survives a move.
4. **What is the state-file rule?** Candidate: `<root>/docs/.bkit-memory.json` plus sub-project `docs/` directories that git tracks content in, stopping at nested checkouts. This repository's own root file is git-ignored, so the file's ignored status cannot decide.
5. **What does the gate say when it is not armed only because of scope?** A silent allow hides a mis-scoped record; a note costs noise.
6. **What happens when a named checkout no longer exists?** Fail closed everywhere, or treat the record as stale.

7. **Is a feature's own orchestrator in scope?** At 5b a codex orchestrator audits its own impl-plan while its own record gates it, so checkout scoping does not help it; a feature's own orchestrator lane on 2026-11-24 is in that position, with many operator allow lines. Included as decision 5. Open: what marks 5d in the record, who may write that mark, and what stops a gated or ungated agent from implementing between 5a and 5d through the shell (the write gate covers the write tools, not arbitrary commands).

## Version History
- v1.0: Initial brainstorm draft from the 2026-11-24 handoff brief, scratch reproduction and four operator decisions. Before review: corrected the owner-identity and 5a timing questions against source, and added the own-orchestrator question.
- v1.1: Approved by the operator 2026-11-24. Added decision 5 and narrowed question 7.
- v1.2: Reworded decision 2; no change of substance.
- v1.3: Decision 5 confirmed at spec approval.
- v1.4: 2026-11-26. Public-text edits per the operator's review of 2026-11-26 (private record); no change of substance.
