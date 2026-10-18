# Spec: grok-audit-surface

## Executive Summary
Measure grok's audit recall and fabrication rate against agy on a fixed seeded-defect set, publish the result either way, and only if grok clears the D3 bar against agy (fabrication rate no higher, recall no lower, and recall strictly higher when the fabrication rates are equal, so a full tie does not promote), make grok a standing third leg on a document's first gating cycle (`--surfaces codex,agy,grok`), leaving revision cycles, the exit streak and the round cap as they behave today.

## Goal
Measure grok as an audit surface, ending the **unmeasured** label on its audit precision, and add a third model family to each document's first gate when, and only when, the measurement supports it.

## Decisions carried in (operator-approved 2026-10-18, binding)
- **D1 Role.** grok becomes a standing third leg on a document's FIRST gating cycle only. Revision cycles are unchanged: codex gates and the `doc-auditor` does an ADVISORY delta review. Out of scope: grok as implementer, grok as doc author, and a grok TDD write gate.
- **D2 Calibration.** A seeded-defect set built from copies of archived phase documents that have already been audited, with a ground-truth label per seed. grok and agy run on identical seeded prompts through the normal audit-cycle path, and codex runs as the reference ceiling when it is available. The scorer is a committed probe, the result is a committed measurement doc, and both can be re-run after a grok upgrade.
- **D3 Promotion bar (amended by operator decision, 2026-10-18: strict tie rule).** Compared with agy on the same seeds, grok passes only when its fabrication rate is ≤ agy's AND its recall is ≥ agy's, AND, when the two fabrication rates are equal, grok's recall is STRICTLY greater than agy's. Stated as one predicate: `(fab_grok < fab_agy AND recall_grok ≥ recall_agy) OR (fab_grok = fab_agy AND recall_grok > recall_agy)`. A full tie (equal fabrication rate and equal recall) does NOT promote. The amendment supersedes the looser reading of the original D3 (≤ and ≥ alone, under which a full tie passed) and adopts the brainstorm's Risks-row rule. Every statement of the bar in this spec (Executive Summary, AC-5.3, AC-5.5, FR-6, FR-7) refers to this predicate. On a miss grok stays fallback-only, and the numbers are still published. "Unmeasured" is retired either way. The routing change (FR-7) ships only on a pass.
- **D4 Re-smoke.** The re-smoke on grok 1.0.62 covers the AUDIT PATH ONLY. The host-mode adapter is out of scope.

## Premises verified against the tree (at `e6ce05eb`; `git diff --quiet 0be0f064..HEAD -- h-mad docs/archive docs/03-analysis` holds)
These are the facts the FRs build on. Each one was checked against the file it names. The report lists the commands.

- `h-mad/scripts/hmad-dispatch.sh` `_cmd_audit_cycle` accepts `--surfaces` as a comma list of `agy|codex|grok`. Each list must have exactly `--passes` entries. Anything else exits 2 with `--surfaces lists N agents for M passes` or `unknown agent '<x>' (agy|codex|grok)`. If no `--legs` is given, **legs default to the surfaces list**. When every pass names one surface, the wrapper warns `one surface repeated, not a union`.
- `h-mad/scripts/h_mad_audit_cycle.py` measures a pass log through `scan_grok` (imported from `h_mad_review_evidence`). A grok log that has an `end` event is shape `grok` and is floored on `ok` like an agy log (`DELIVERY_FLOOR = 2`). A grok log with no `end` event is shape `grok-truncated` and gives `AUDITCYCLE: UNVERIFIED reason=low_evidence_unmeasurable:pN`. `combine()` returns `FAIL` if ANY pass has a must-fix, so with N passes the gate is already the union of every pass's must-fixes.
- The grok event vocabulary is stated in TWO places, and both currently hold the same seven types (`thought text available_commands tool_call tool_call_update usage end`): `_GROK_TYPES_RE` in `hmad-dispatch.sh`, and `_GROK_TYPES` (a frozenset) in `h_mad_review_evidence.py`. The brainstorm names only the first.
- `h_mad_audit_gate.py` `exit_check` groups stamps by cycle (`cycle_of`) and compares the normalised leg sets (`_leg_key`, sorted and deduped) of the last two cycles. It refuses with `legs_changed:<a>|<b>` when they differ, with `legs_disagree:<phase>.v<N>` when the legs within one cycle differ, and with `not_two_cycles:<n>` when there are fewer than two cycles. `round_check` counts cycles per (feature, phase), never stamps.
- **Today's behaviour across leg sets was probed with synthetic stamps against the shipped `h_mad_audit_gate.py`, and the probe was then deleted.** A first gate stamped `agy+codex` followed by a revision stamped `codex` gives `EXIT: BLOCKED reason=legs_changed:agy+codex|codex`. A first gate stamped `agy+codex+grok` followed by a `codex` revision gives `EXIT: BLOCKED reason=legs_changed:agy+codex+grok|codex`. Two `codex` revision cycles (v2, v3) give `EXIT: READY … legs=codex`. Three stamps of v1 (p1–p3) plus one v2 stamp give `ROUNDS: OK cap=2 cycles=2`.
- `h-mad/references/grok-runtime.md` §"Version and compatibility" has exactly one version sentence, "These mappings were checked against grok 1.0.41.", and it covers the **host-mode mappings**. `grok --version` on this machine prints `grok 1.0.62 (1474f9cbdd91) [stable]`.
- `h_mad_resolved_model.py grok --log <log>` prints `RESOLVED-MODEL agent=grok model=… resolved=1 source=…`, reading the stream's `end` event.
- Every one of the three source features in FR-2 has `spec`, `brainstorm`, `plan`, `design` and `impl-plan` under `docs/archive/`, and none of them has a live copy under `docs/01-plan/features/` or `docs/02-design/features/`.

## Functional Requirements

### FR-1: Audit-path re-smoke on grok 1.0.62 (D4)
- **Description**: Before any calibration dispatch, run one real grok audit pass through `hmad-dispatch audit-cycle --passes 1 --surfaces grok` against one seeded document from FR-2, and record what the audit path actually does on 1.0.62. The smoke covers four things: the `exec grok` audit dispatch, the NDJSON event types, `scan_grok` evidence, and report-file delivery. It covers nothing in host mode (hooks, `spawn_subagent`, the TDD gate, session id).
- **Acceptance Criteria**:
  - AC-1.1: The smoke's pass log holds at least one `end` event, and the cycle's `Effort:` block reports `format=grok` (shape `grok`), not `grok-truncated`. A `grok-truncated` reading fails the smoke. It is not retried as a pass.
  - AC-1.2: Every distinct `type` value in the live log is listed in the measurement doc and classified as in-vocabulary or out-of-vocabulary against BOTH `_GROK_TYPES_RE` (`hmad-dispatch.sh`) and `_GROK_TYPES` (`h_mad_review_evidence.py`). If the two vocabularies differ from each other at the smoke sha, the smoke fails. An out-of-vocabulary type does not fail the smoke, but it is published together with whether it carries tool or usage data. If `end`, `tool_call` or `tool_call_update` is missing, the smoke fails.
  - AC-1.3: Report delivery is shown by `COLLECT: OK`, or by a non-`none` `delivered=` field on the `AUDITCYCLE:` line, together with a `GATE:` token scored from the report file. A verdict read from grok's final message alone does not count.
  - AC-1.4: The measurement doc records the `RESOLVED-MODEL` line from `h_mad_resolved_model.py grok --log <pass log>`, the pass's wall time, and the `--timeout` chosen for FR-3. The timeout is derived as `ceil(1.5 × measured wall seconds / 60) × 60` with a floor of the wrapper's default 900 s, and the derivation is printed beside the result.
  - AC-1.5: `h-mad/references/grok-runtime.md` §"Version and compatibility" gains one sentence saying that the audit path (the `exec grok` audit leg, the event vocabulary, `scan_grok` and report delivery) was re-smoked against grok 1.0.62, and naming the measurement doc. The existing sentence "These mappings were checked against grok 1.0.41." stays **unchanged**, because the host-mode mappings it covers were not re-checked (D4).

### FR-2: The seeded-defect set
- **Description**: Build the ground truth: N = **27** planted build-class defects across **9** seeded documents, 3 seeds per document. Each document is a copy of one archived, already-audited phase document, and each seed has a label.
- **Source documents (Q2 decision)**: the plan, design and impl-plan of these three archived features, giving 3 × 3 = 9 documents:
  - `docs/archive/2026-09/audit-report-docs-copy/` (small: about 20–37 KB per document; collected legs `codex` + `p1` on all three phases)
  - `docs/archive/2026-09/tdd-gate-fail-opens/` (medium: about 88–109 KB; legs `p1`, `p2`, `agy`)
  - `docs/archive/2026-10/agy-coder-fallback/` (larger: about 92–152 KB; legs `agy`, `p1`, `p2`)

  *Why these three:* each one was gated by at least two collected legs, so its unseeded body has already survived audit, which keeps unplanted findings down. Each has a complete paired set (spec, plan, design), which the assembler requires. Their largest assembled prompt, the agy-coder-fallback impl-plan with its paired spec, plan and design, comes to about 469 KB of documents, under half the 1,048,576-char exec ceiling. *Excluded:* `doc-block-exec`, whose documents are around 5,000 lines and whose prompts sit near the ceiling (the brainstorm's reason for deferring corpus replay). Also excluded are features with no paired spec in the archive, because the assembler cannot build their prompts.
- **Why N = 27**: one dispatch per (document, surface) keeps the cost at 9 grok + 9 agy (+ 9 codex) dispatches. 27 seeds give each surface a recall denominator in which a gap of one seed (about 3.7 points) can be published as a count, and four seed classes each appear at least 6 times. A per-phase split (9 seeds per phase) is published for observation only, and no decision reads it (see FR-7).
- **Acceptance Criteria**:
  - AC-2.1: Seed classes. The rule for a seed is that it must be `class: build` under the audit template's test, meaning a 5d/5e implementer's code or tests would differ if the defect were fixed. There are four classes:
    - **C1 contract-token**: a verdict token, reason value, exit code or CLI flag in a contract is changed so that it contradicts the paired spec or another statement of the same contract.
    - **C2 dead-reference**: a `path:symbol`, function or flag the document names is renamed to one that does not exist in the calibration tree.
    - **C3 dropped-failure-mode**: one enumerated failure mode of a contract (an error token, a cannot-judge branch, a refusal) is deleted, so the contract no longer states it.
    - **C4 unsatisfiable-requirement**: an AC is changed so that no implementation can satisfy both it and another AC or enumeration in the same document. This is the 88-vs-94 shape from SKILL.md §"Document-audit round cap".

    The residual is any defect class outside these four, for example measurement-class, prose or ordering defects. None of these is seeded, and the measurement doc says so.
  - AC-2.2: Class distribution. Number the documents 1 to 9 in the order the source list above gives them (feature order, then plan, design, impl-plan). Document k omits class `((k−1) mod 4) + 1` and carries one seed of each of the other three. That yields C1 = 6, C2 = 7, C3 = 7, C4 = 7, which sums to 27. The probe derives these counts from the ledger, never carries them, and refuses a ledger whose counts differ.
  - AC-2.3: Placement. Each seed sits in a distinct `##`/`###` section of its document and outside `## Version History`. No seed lives in the paired documents, which are byte-identical copies of the archive. Each seed's seeded span is unique within its document.
  - AC-2.4: The ledger is committed under `docs/03-analysis/probes/grok-audit-surface/` as one JSON record per seed with these fields: `id`, `source` (archive path), `phase`, `class` (C1–C4), `origin` (one of the eight `ORIGINS` in `h_mad_audit_origins.py`, naming the real must-fix shape the seed imitates), `section` (heading text), `original` (verbatim pre-seed span), `seeded` (verbatim post-seed span), and `expected` (the finding a correct auditor files, in one sentence). The probe refuses an `origin` outside `ORIGINS`.
  - AC-2.5: The seeded documents are the archive copies with the ledger's edits applied. The probe re-derives every seeded document from `source` + ledger and fails if the result differs from the committed seeded copy by even one byte.
  - AC-2.6: Leak control. Calibration runs in a scratch detached worktree of the calibration sha. In that root, each source feature's `docs/archive/*/<feature>/` directory is **removed before any dispatch**, so a reviewer with tools cannot diff a seeded document against its original. The probe checks this and refuses to dispatch if any of the three directories exists. The residual is other tracked files that mention a source feature by name (handoffs, `docs/skill-candidates.md`). They are not removed, and the measurement doc names them as a stated residual.

### FR-3: Calibration dispatch through the normal audit-cycle path
- **Description**: Each seeded document is audited once per surface, in one cycle, through `hmad-dispatch audit-cycle`. With codex available the call is `--passes 3 --surfaces codex,agy,grok`, which is the same shape as a production first gate. With codex unavailable it is `--passes 2 --surfaces agy,grok`. The project root is the FR-2 scratch worktree, and every NDJSON log is kept.
- **Acceptance Criteria**:
  - AC-3.1: Every assembly reads `ASSEMBLE: PASS`. Any other token halts the run for that document and is published, never skipped silently.
  - AC-3.2: The prompts are identical across surfaces. Within one cycle, the per-pass prompts may differ only in the per-pass report path and sentinel lines. The probe diffs them with those lines masked and fails the cycle on any other difference.
  - AC-3.3: Every pass keeps its pass log, and the measurement doc records each log's `log_sha256` from the pass's `.effort.json` sidecar.
  - AC-3.4: Re-dispatch rule. A cycle whose `AUDITCYCLE:` is `UNVERIFIED` (any `reason=`) is re-dispatched once as a fresh cycle number. The second outcome stands. A pass whose report was never delivered (`no_report`, `unscorable_report`, or `delivered=none`) counts as zero findings, so its seeds are misses for that surface. A delivered report is scored even when its pass read `low_evidence`, and the measurement doc publishes per-surface delivery and evidence outcomes as counts.
  - AC-3.5: `--timeout` is the FR-1 derived value, given explicitly, and is the same for every pass.
  - AC-3.6: The calibration sha, the grok, agy and codex versions, and each surface's `RESOLVED-MODEL` line are recorded once in the measurement doc.

### FR-4: Finding classification and fabrication confirmation (Q3 decision)
- **Description**: Every must-fix is classified **by hand**, against the calibration tree and the assembled prompt, with the reviewer surface hidden from whoever labels it. Mechanical checks do two things only: they extract findings, and they propose candidates. They never decide a label. *Why:* `docs/03-analysis/hmad-audit-evidence-gate.measurement.md` measured the best automatic span rule catching 4 of 6 fabrications while killing 13 of 31 real must-fixes, and it found two fabrications that no occurrence check can see: one quotes nothing, and one paraphrases.
- **Acceptance Criteria**:
  - AC-4.1: Extraction uses the gate's own machinery (`h_mad_audit_gate.classify_detail`, or the same section walk). For every report, the probe asserts that its extracted must-fix count equals `classify(text)["must_count"]`. A mismatch makes the run `UNREADABLE`.
  - AC-4.2: Blinding. The probe writes every must-fix to a findings file under an opaque id that does not encode the surface, in a shuffled order, and writes the id-to-surface key to a separate file. The labeler works from the findings file alone.
  - AC-4.3: Each must-fix gets exactly one label:
    - `HIT:<seed-id>`: the finding locates the seed's section, or quotes inside its `seeded` span, AND it states the seed's `expected` defect.
    - `REAL`: its premise holds against source, and it is not a seed.
    - `FABRICATED`: its premise fails against the calibration tree or the assembled prompt.
    - `UNDECIDABLE`: the labeler cannot settle it, and records one sentence saying why.

    Any other label value makes the run `UNREADABLE`.
  - AC-4.4: Candidate hints are advisory only. For a `quote:` line whose span is absent from the file it names, the probe may print a `candidate-fabrication` hint, and for a `quote:` span overlapping a seed's `seeded` span it may print a `candidate-hit:<seed-id>` hint. Hints are printed beside a finding and never written as labels. A test asserts that changing or removing every hint leaves the score unchanged.
  - AC-4.5: Counting rules. A seed hit by several findings from one surface counts once toward that surface's recall. One finding can hit at most one seed. Recall counts must-fixes only, because the gate is on must-fixes. Should-fix hits are published separately and never enter the bar.

### FR-5: The scorer probe
- **Description**: A committed, stdlib-only probe under `docs/03-analysis/probes/grok-audit-surface/` that builds the seeded documents, checks leak control, extracts and blinds findings, and computes the verdict from the ledger, the labels and the key. It is tested in the suite.
- **Acceptance Criteria**:
  - AC-5.1: The probe ends on one token line: `SEEDSCORE: PASS|MISS|INCONCLUSIVE|UNREADABLE`, with `reason=` on every verdict other than PASS. It exits 0 on PASS, MISS or INCONCLUSIVE and 2 on UNREADABLE, and callers read the token, never `$?`.
  - AC-5.2: The fields per surface are `recall=<hits>/27`, `musts=<n>`, `fabricated=<f>`, `undecidable=<u>` and `fab_rate=<f>/<n−u>`, each written as an exact fraction. A surface with no decidable must-fix (`n − u = 0`) prints `fab_rate=0/0`, which compares as zero fabrications.
  - AC-5.3: Verdict rules are computed with exact rational comparison and no rounding. "D3 holds" means the amended D3 predicate is true: `(fab_grok < fab_agy AND recall_grok ≥ recall_agy) OR (fab_grok = fab_agy AND recall_grok > recall_agy)`. Equality of fabrication rates is equality of the reduced rationals (`0/0` compares as zero, AC-5.2), so `1/4` and `2/8` are equal. A full tie on both quantities makes the predicate false.
    - **PASS**: D3 holds when every one of grok's UNDECIDABLE is counted as fabricated and every one of agy's is counted as not fabricated.
    - **MISS**: D3 fails when the opposite worst case is taken (grok's undecidables counted as not fabricated, agy's as fabricated).
    - **INCONCLUSIVE**: covers every other case. That includes `reason=undecidable_flips` and `reason=seeds_undetected`. The second applies when no surface, codex included, hit any seed, which means the seeds measure nothing.
  - AC-5.4: UNREADABLE reasons, all fail-closed:
    - `ledger_counts` (AC-2.2)
    - `ledger_origin` (AC-2.4)
    - `seed_rebuild` (AC-2.5)
    - `leak:<path>` (AC-2.6)
    - `must_count_mismatch:<report>` (AC-4.1)
    - `label:<id>` (an unknown label, an unlabeled finding, or a `HIT` naming an unknown seed)
    - `key_mismatch` (the findings ids and the key ids differ)
  - AC-5.5: Every verdict and every UNREADABLE reason has a fixture test. Each branch of an alternation gets its own fixture, run with that branch alone. The D3 predicate's two branches and its tie boundary each get a fixture with no undecidables: fabrication strictly lower with recall equal gives `PASS`; fabrication equal with recall strictly greater gives `PASS`; fabrication equal with recall equal (the full tie) gives `MISS`; fabrication equal with recall lower gives `MISS`; and fabrication equal as unreduced fractions (for example `1/4` against `2/8`) with recall equal gives `MISS`. The tests live in the suite under `h-mad/tests/`, so the probe directory is kept at archive time (`h_mad_archive_feature.py` keeps a probes directory that live code reads).

### FR-6: Measurement doc and the "unmeasured" retirement (D3)
- **Description**: The result goes into `docs/03-analysis/grok-audit-surface.measurement.md`, whatever the verdict. It holds the `SEEDSCORE:` line, the per-surface fields, the codex reference ceiling, the observational per-phase and per-class split, the FR-1 smoke result, the stated residuals, and one re-run command. The doc is stamped at one calibration sha.
- **Acceptance Criteria**:
  - AC-6.1: The doc states the transfer residual: seeds are build-class shapes from the four classes in AC-2.1, and the doc says whether a real-defect recall would match is not measured.
  - AC-6.2: In `h-mad/SKILL.md`, audit precision is removed from grok's list of unmeasured properties in two places: the `exec grok` bullet of §"Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot", and §"Teammate audit leg — when codex is unavailable". It is replaced by the measured fractions and a pointer to the measurement doc. GREEN, mutation and wiring stay **unmeasured** (D4). The existing `test_grok_fallback_docs.py` term `unmeasured` in the teammate section therefore still holds, and a new assertion pins the pointer to the measurement doc in both sections.
  - AC-6.3: This applies on PASS, MISS and INCONCLUSIVE alike. On INCONCLUSIVE the text says the bar was not decidable on this set, gives the reason, and grok stays fallback-only.
  - AC-6.4: The re-run command rebuilds the scratch root from the committed ledger at a named sha and reproduces the `SEEDSCORE:` line from the committed labels without dispatching anything. A fresh calibration, such as one after a grok upgrade, uses a new scratch root and new labels, and is recorded as a new reading. It never edits the previous one in place.

### FR-7: Routing change on PASS only (D1; Q5 decision)
- **Description**: The routing change happens only on `SEEDSCORE: PASS`, which is the amended D3 predicate holding under AC-5.3's worst case; a full tie scores `MISS` and does not route. On a pass, the first gating cycle of **every** phase document (plan, design and impl-plan) runs as ONE call, `hmad-dispatch audit-cycle --passes 3 --surfaces codex,agy,grok`, whenever codex and grok are both available. Revision cycles stay codex-gated with the doc-auditor ADVISORY delta review. The codex-unavailable route in §"Teammate audit leg" is unchanged.

  *Why all three phases, and not a subset:* the per-phase split carries 9 seeds, which is too small to separate surfaces, so a per-phase rule would be fitted to noise. The cost is one dispatch per document, paid once, because revisions are unchanged: about three extra dispatches per feature. Disjoint must sets between model families were the measured property behind the two-surface rule (SKILL.md §"Document-audit round cap"), and nothing in that measurement limits it to one phase.
- **Acceptance Criteria**:
  - AC-7.1: SKILL.md §"Never gate on one audit pass", at the bold "**Which two surfaces …**" paragraph, names `--surfaces codex,agy,grok` for the first gate with codex available and points to the measurement doc. The sentence ending "that is three reports, of which two share a model family" is reworded so that the prohibition is on two reports sharing a family, not on three reports. The teammate-full-pass-plus-codex case stays prohibited.
  - AC-7.2: Availability. If `command -v grok` fails, the first gate runs `--passes 2 --surfaces codex,agy`. The same applies when the grok pass is the `pN` named in an `UNVERIFIED reason=…:pN` on both the first run and its one re-dispatch: the cycle is then re-run as `codex,agy`. Either way the stamp records the legs that actually ran (wrapper default), so the record is the stamp. No new state field is added.
  - AC-7.3: Doc tests in the `test_grok_fallback_docs.py` style pin `--surfaces codex,agy,grok` in §"Never gate on one audit pass" and keep the existing `--surfaces agy,grok` pins.
  - AC-7.4: On MISS or INCONCLUSIVE, none of AC-7.1–7.3 ships. A test, or the measurement doc's verdict line, is the evidence the branch was taken, and §"Never gate on one audit pass" is byte-unchanged except for the FR-6 pointer, if one is placed there.

### FR-8: Union gate across three surfaces (Q4 decision)
- **Description**: Nothing changes in how the gate works. With three passes, the gate is the union of all three must-fix sets, and every grok must-fix is falsified against source before it is acted on, the same as any other leg. Promotion does not relax the evidence check on grok.
- **Acceptance Criteria**:
  - AC-8.1: A fixture three-pass cycle (codex, agy, grok) in which only the grok pass files a must-fix gives `AUDITCYCLE: FAIL`. The same cycle with all three passes clean gives `PASS`.
  - AC-8.2: A grok pass with `ok ≤ 2` in a three-pass cycle gives `UNVERIFIED reason=low_evidence:pN`, and a truncated grok log gives `low_evidence_unmeasurable:pN`, where pN is grok's index. The existing floors apply unchanged at index 3.
  - AC-8.3: The SKILL.md text at AC-7.1 says that grok must-fixes go through §"Verifying a review finding before acting on it", and that a rejected one is recorded per §"Record a rejected finding in the rejections ledger, never in a gated document".

### FR-9: Exit streak and round cap across leg sets (Q1 decision)
- **Description**: The rule is that **the exit streak counts only among consecutive cycles with an identical leg set**. A first gate stamped `agy+codex+grok` and revision cycles stamped `codex` are different sets, so the first gate never pairs with a revision. This is the same refusal class that `agy+codex → codex` already gets today (probed; see Premises). **No change to `exit_check` or `round_check`.** This feature does not change how a phase decides to exit, which remains SKILL.md §"Document-audit round cap". *Why no new rule:* the leg-set check exists so that a streak never spans two different questions (#11/H3). Exempting the first gate would reopen that case, and the probe shows the third leg adds nothing the two-leg first gate does not already trigger.
- **Acceptance Criteria**:
  - AC-9.1: A test with real-grammar stamps: v1 p1–p3 with legs `agy,codex,grok` and v2 p1 with legs `codex` gives `EXIT: BLOCKED reason=legs_changed:agy+codex+grok|codex`.
  - AC-9.2: v2 and v3 stamped `codex` give `EXIT: READY … legs=codex`.
  - AC-9.3: `--round-cap 2` over v1 p1–p3 plus v2 gives `ROUNDS: OK cap=2 cycles=2`. The three first-gate legs count as one cycle.
  - AC-9.4: Three v1 stamps on which one leg records `agy,codex` and the others `agy,codex,grok`, plus one v2 stamp with legs `codex`, give `EXIT: BLOCKED reason=legs_disagree:design.v1`. The v2 stamp is there because a single cycle on its own would give `not_two_cycles:1` before any legs are compared. This is why AC-7.1 requires the three first-gate legs to run as one wrapper call and not as separately collected legs.
  - AC-9.5: The SKILL.md bullet "**Name the reviewer legs with `--legs`…**" in §"What you NEVER do" gains one sentence: the first gate and the revisions run different leg sets by design, so the streak, when it is reached, is among revision cycles.

### FR-10: Three distinct surfaces through the wrapper, end to end
- **Description**: The brainstorm's remaining driver work: show with tests that `--passes 3 --surfaces codex,agy,grok` dispatches each surface through its own `exec`, records the right leg set, and prints no same-surface warning.
- **Acceptance Criteria**:
  - AC-10.1: With stub agents, `audit-cycle --passes 3 --surfaces codex,agy,grok` invokes `exec codex`, `exec agy` and `exec grok` once each, in that pass order, each on its own report path.
  - AC-10.2: Every stamp the cycle writes carries `legs: ["agy","codex","grok"]`, and stderr has no `one surface repeated` line.
  - AC-10.3: `--passes 3 --surfaces codex,agy` exits 2 with `--surfaces lists 2 agents for 3 passes`. This is existing behaviour, pinned at three passes.

## Non-Functional Requirements
- Performance: the calibration costs 9 grok + 9 agy dispatches, plus 9 codex when available, plus at most one re-dispatch per document (AC-3.4). The FR-1 timeout bounds each pass. In production, one more dispatch per document first gate after a PASS (FR-7). Revisions cost the same as today.
- Security: audits run read-only in a scratch worktree. The seeded documents and the scratch root are never merged into `main`. The ledger and the labels hold no secrets.
- Compatibility: no change to `exit_check`, `round_check`, `combine`, `scan_grok` or the wrapper's `--surfaces` grammar. The codex-unavailable routing and the `fallback_agent` semantics are unchanged.

## Out-of-Scope
- grok as Phase-5 implementer, as doc author, or as the subject of a TDD write gate (D1).
- The host-mode adapter: hooks, `spawn_subagent`, the TDD gate, session id and the 1.0.41 mapping line (D4).
- Replacing the doc-auditor delta review or agy with grok (brainstorm, Alternatives).
- Replaying the gateway-consolidation corpus.
- Changing the codex-unavailable route, or adding a `grok_status` state field.
- Seeding measurement-class, prose or ordering defects (AC-2.1 residual).

## Assumptions
- grok 1.0.62 and agy are on PATH at calibration time. codex is optional, and when it is absent the reference ceiling is published as not run.
- The audit template's `class:` and `quote:` contract is the one at the calibration sha, and every surface receives it identically (AC-3.2).
- The hand labeler can open the calibration tree and the assembled prompts, which FR-3 keeps.

## Version History
- v1.0: Initial specification draft from the approved brainstorm v1.0 (`0be0f064`) and operator decisions D1–D4 (2026-10-18). Resolves open questions: Q1 → FR-9, Q2 → FR-2, Q3 → FR-4, Q4 → FR-8, Q5 → FR-7.
- v1.1: Operator decision 2026-10-18 amends D3 to a strict tie rule: promotion requires fabrication rate ≤ agy's and recall ≥ agy's, with recall strictly greater when fabrication rates are equal; a full tie does not promote. Predicate stated once in D3 and applied in the Executive Summary, AC-5.3, AC-5.5 (new tie-boundary fixtures) and FR-7; the Assumptions entry recording the D3/brainstorm conflict is removed.
