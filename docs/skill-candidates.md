# Skill Candidates

Appended by the `/handoff` automation scout, newest session last. **Status is only useful if it is
current** — reconcile a row when the thing it describes ships, the same way `docs/skill-monitoring.md`
rows are flipped.

**Verdicts:** `yes` / `maybe` / `no` (scout's initial call) · `LANDED` (shipped — name where) ·
`SUPERSEDED` (a different fix removed the need) · `DECLINED` (deliberately not doing it, with the
reason) · `done` (legacy spelling of LANDED).

## Open, highest recurrence first (reconciled 2026-07-24)

**No `candidate: yes` with rec ≥3 remains unlanded.** Every actionable candidate shipped in the
2026-07-24 skill-candidate-upgrades session (verified against source, not the label — see below).
What remains are `maybe` rows that *describe the /h-mad skill that already exists*, kept as
provenance, not work.

| rec | candidate | status |
|---|---|---|
| 9 | `close-a-filed-defect cycle` | **LANDED** — SKILL.md §Working a `skill-monitoring` item |
| 9 | `H-MAD phase-doc + agy-audit-gate loop` | *maybe* — already the /h-mad skill |
| 6 | `audit→fix→subagent-review→merge loop` | *maybe* — already the /h-mad skill |
| 3 | `test-pinned-the-defect check` | **LANDED** — invariants.base.md §Regression provenance |
| 3 | `verify-backlog-row-premise-vs-code` | **LANDED** — folded into close-a-filed-defect step 1 |
| 2 | `both-halves doc fix` | **LANDED** — invariants.base.md §Both halves of a doc change |
| 2 | `orca-verb-live-reconcile`, `live-e2e verb sweep` | *maybe* — not yet needed |
| 1 | `differential-validator-test` | **LANDED** — invariants.base.md §Reimplementation parity |

**Re-scout trigger:** promote only when a *fresh* recurrence (rec ≥3, `candidate: yes`) appears in a
later session block. As of 2026-07-24 there is none — the backlog is drained of actionable items.


## 2026-07-20 — orca-adaptation-tiers

- **agy/codex poll-until-idle dispatch**: assemble prompt -> hmad-dispatch send -> background poll on idle marker ("? for shortcuts" present, "esc to cancel" absent) + schema token -> parse verdict — recurrence: 12+ (every audit/TDD/arch-review this session) — candidate: **LANDED** 2026-07-24 — `hmad-dispatch ask` (send + wait-idle + full-buffer read; extraction stays a separate `h_mad_extract_verdict.py` call). Live-dogfooded against agy
- **H-MAD phase-doc + agy-audit-gate loop**: write phase doc -> assemble audit prompt (template+doc+invariants) -> dispatch agy -> gate -> fix -> re-audit — recurrence: 9 (3 features x 3 phases) — candidate: maybe (already the /h-mad skill; a helper to stage+dispatch+gate in one call would cut ~40 tool calls)

## 2026-07-21 — orca-arc-complete-hemasuite-wiring

- **orca-verb-live-reconcile**: after shipping an orca-wrapping verb, run a live create→list→remove cycle against the real runtime and fix output-key extraction — recurrence: 2 (worktree-create + automation-create both had the envelope-.id bug) — candidate: maybe
- **hmad-full-cycle-driver**: the repeated author-docs→agy-audit(2cyc)→Codex-TDD→verify→agy-5e→6a-prime→ship sequence ran 4× this session — recurrence: 4 — candidate: no (already the /h-mad skill)

## 2026-07-22 — h-mad-fourteen-issues-shipped

- **file-issue-then-fix-under-TDD**: file a GitHub issue capturing the measurement, then fix it RED→GREEN with a test file per issue, closing via a `Closes #N` trailer. Ran 14 times this session with an identical shape. — recurrence: 14 — candidate: **LANDED** (Wave 4b) — `h_mad_issue_fix_gate.py` + SKILL.md protocol
- **verify-the-mutation-not-the-command**: after any git/shell mutation, re-read the resulting state rather than trusting exit codes. Caught two silent zsh no-ops (backtick execution in `-m`, leading-dash paths) that both looked like success. — recurrence: 3 — candidate: **LANDED** (Wave 4b) — `invariants.base.md` §Mutation verification
- **replay-the-incident-against-the-fix**: validate a protocol fix by running it against the historical data that motivated it, not only unit stubs. Caught a wrong commit-count heuristic that unit tests passed. — recurrence: 4 — candidate: **LANDED** (Wave 4b) — `invariants.base.md` §Incident replay (merged with `replay-detector-against-history`, recurrence 3)
- **worktree-for-live-skill-edits**: when editing a skill whose working tree is symlinked as the live `~/.claude/skills/<name>`, work in a git worktree so an in-flight run keeps reading the merged tree. — recurrence: 2 — candidate: **LANDED** (Wave 4b) — SKILL.md §Editing this skill while a run is in flight
- **sanitize-before-public-filing**: grep issue bodies against a forbidden-term list (project names, slugs, local paths, private symbols) before filing to a public tracker. — recurrence: 2 — candidate: **LANDED** (Wave 4b) — SKILL.md §Filing to a public tracker

## 2026-07-22 — orca-skills-hardening

- **audit→fix→subagent-review→merge loop**: repeated 6× this session (F/G/188/189 + 2), each catching a real bug — recurrence: 6 — candidate: maybe (this IS the /h-mad + review discipline; already a skill)
- **live-e2e verb sweep against real orca**: exercise every hmad-dispatch verb + skill mechanism vs the live runtime, matrix report — recurrence: 2 — candidate: maybe

## 2026-07-22 — orca-agent-resolution-hardening

- **h-mad audit-prompt assembler**: hand-wrote assemble_audit/design/implplan.py in scratchpad 3× this session to splice INLINE_* slots into audit-prompt.template.md — a bundled `scripts/h_mad_assemble_audit.py <phase>` would DRY it into the skill — recurrence: 3 — candidate: **LANDED** 2026-07-22 (`3f8ae83`) — `h-mad/scripts/h_mad_assemble_audit.py`. Duplicate of the `done` row in the next session block; kept for provenance.
- **launch+pin agent bootstrap**: `hmad-dispatch launch/pin` then verify resolve — recurrence: 2 — candidate: no (already a verb)

## 2026-07-22 — audit-assembler-agent-resolution

- **h-mad audit-prompt assembler**: SHIPPED this session as `h-mad/scripts/h_mad_assemble_audit.py` — closes the 2026-07-22 orca-agent-resolution-hardening candidate (recurrence was 3) — recurrence: 4 — candidate: done
- **staged-prompt repair sweep**: script that rewrites every `/tmp/audit_*.txt` to what the current template would emit (strip note, resolve markers, de-dupe rubrics), with backups + a freshness guard skipping in-flight prompts — recurrence: 2 — candidate: **DECLINED** (Wave 4b, 2026-07-23). Every staged prompt on disk belongs to one feature that shipped 2026-07-22; `/tmp` is scratch, and `h_mad_assemble_audit.py` regenerates any prompt in a single call. A sweep would carry backup and in-flight-freshness logic to repair files nothing will read again. Revisit only if a live run is ever blocked by a stale staged prompt.
- **throwaway stub-harness probe**: import `tests/test_hmad_dispatch.py` helpers into a scratch pytest to empirically confirm a suspected resolver hole *before* fixing it, then delete — turned two hypotheses into verified bugs and killed a third — recurrence: 3 — candidate: **LANDED as a practice** (Wave 4b) — SKILL.md §Confirming a suspected defect before fixing it. Deliberately NOT scripted: the artifact is meant to be thrown away, so a permanent script would contradict the thing being taught. Recurrence bumped to 3 — it is what turned J17 from a rejected selector into the guard bypass.

## 2026-07-23 — wave2-preflight-shipped

- **discriminating-regression-test**: before keeping a regression test, revert the fix and confirm it fails — a test that passes against the code it was written to catch is decoration — recurrence: 3 — candidate: **LANDED** (Wave 4c) — `invariants.base.md` §Test discrimination (merged with `mutation-test-every-guard`)
- **label-guards-in-red-dispatch**: state expected fail/pass counts and mark regression guards explicitly when a TDD task is refactor-shaped; "every test must FAIL" makes the implementer manufacture failures — recurrence: 3 — candidate: **LANDED** (Wave 4c) — `codex-implementer-prompt.md` §Your Job + SKILL.md 5d (the old blanket "Verify all tests FAIL" halt was itself the harmful instruction)
- **verify-review-premise-before-acting**: check a review finding's stated premise against source before applying its prescription; 2 of 5 findings this session were right in substance and wrong in direction — recurrence: 4 — candidate: **LANDED** (Wave 4c) — SKILL.md §Verifying a review finding before acting on it
- **content-probe-agent-pane**: identify an Orca agent pane by its launch banner via `terminal read --cursor 0`, never by title — recurrence: 5 — candidate: **SUPERSEDED** by J16 (main `bf9c4c3`). `_orca_find` Pass 0 joins `worktree ps` `agents[].paneKey` to `terminal list` `tabId:leafId`, which is exact where content-probing is heuristic — and content-probing itself *failed* on 2026-07-23 when both panes had reset buffers. Order is now paneKey → content → never title.

## 2026-07-23 — wave3-wave4a-shipped

- **mutation-test-every-guard**: after implementing a guard, stub it to its permissive value and re-run the suite; zero failures means the guard is unenforced, not that it is safe — caught 2 vacuous guards this session that review and a green run both missed — recurrence: 7 — candidate: **LANDED** (Wave 4c) — `invariants.base.md` §Test discrimination
- **replay-detector-against-history**: validate a new detector/heuristic against the real artifacts already on disk, not only synthetic cases — 14 handcrafted cases passed while the real label `Working-tree concern:` was rejected — recurrence: 3 — candidate: **LANDED** (Wave 4b) — merged into `invariants.base.md` §Incident replay
- **panekey-join-agent-identity**: resolve an Orca agent handle by joining `worktree ps` `agents[].paneKey` to `terminal list` `tabId:leafId`, rather than title or preview or content — recurrence: 2 — candidate: **LANDED** (J16, main `bf9c4c3`) — `_orca_find` Pass 0; closed orca#9870
- **tracer-bullet-design-assumptions**: run each load-bearing design assumption as a throwaway shell/git command before writing it into the design — confirmed the `--porcelain` boundary and the base-ref chain, and found a truncation hole, all before any code existed — recurrence: 4 — candidate: **LANDED** (Wave 4c) — `invariants.base.md` §Assumption verification
- **assert-literal-instruction-in-doc-tests**: anchor documentation tests on the literal instruction string; asserting that two component words appear "somewhere" passes with the guidance deleted — recurrence: 2 — candidate: **LANDED implicitly** (Waves 4b+4c) — every doc test added in both waves asserts the literal sentence against a whitespace-normalised copy, and each was mutation-tested. Covered by `invariants.base.md` §Test discrimination; no separate rule needed.

## 2026-07-23 — monitoring-registry-drained

- **close-a-filed-defect cycle**: read entry → verify its stated premise against source → reproduce
  live → TDD the fix → mutation-test every guard → dogfood live → flip the registry row with
  evidence. Ran 9× this session (J1–J5, J11–J13, J17) with an identical shape, and the
  premise-check step changed the fix in 4 of them — recurrence: 9 — candidate: **LANDED** (2026-07-24) — SKILL.md §Working a `skill-monitoring` item
- **test-pinned-the-defect check**: when a fix breaks an existing test, first ask whether the test
  asserted the bug as an acceptance criterion rather than adjusting the fix — J17's forwarded
  selector, J1's create-response handle, J2's AC-6.5 pin path — recurrence: 3 — candidate: **LANDED** (2026-07-24) — `invariants.base.md` §Regression provenance
- **snapshot-live-state-before-mutation-testing**: mutating a path-resolution branch redirects the
  suite onto real files; snapshot the target (or sandbox the cwd) first — recurrence: 1 —
  candidate: **LANDED** (J18) — `h-mad/tests/conftest.py::_protect_live_pin_file` snapshots and
  restores the live pin file and fails loudly; `invariants.base.md` §"Test discrimination" carries
  the caveat.
- **differential-validator-test**: when replacing a library with a bundled implementation, assert
  verdict-equality against the library across a construct-complete corpus AND the real artifacts on
  disk, rather than testing the replacement alone — recurrence: 1 — candidate: **LANDED** (2026-07-24) — `invariants.base.md` §Reimplementation parity
- **both-halves doc fix**: when deleting an unexecutable instruction, assert in the same test that
  the executable replacement landed — a "is it gone" assertion passes for a deletion that lost the
  capability (J11) — recurrence: 2 — candidate: **LANDED** (2026-07-24) — `invariants.base.md` §Both halves of a doc change

## 2026-07-24 — skill-candidate-upgrades

- **promote-candidate-to-rule-or-verb**: reconcile skill-candidates by mapping each open row to a concrete insertion point (Axis-B rule / SKILL playbook / new verb), then TDD+mutation+dogfood like any fix — ran across 4 candidates this session — recurrence: 2 — candidate: maybe (this IS the upgrade workflow; a checklist, not a script)
- **verify-backlog-row-premise-vs-code**: before flipping a candidate/registry row, confirm its claim against git log -S / grep — 3 rows described already-shipped work this session, and (prior session) 4 monitoring rows were stale — recurrence: 3 — candidate: **LANDED** (2026-07-24) — folded into close-a-filed-defect step 1 (SKILL.md §Working a `skill-monitoring` item)
- **fix-the-fixture-not-just-the-assertion**: when a mutation survives after tightening an assertion, suspect the test DATA — aligned word lengths let a naive cut hit a boundary — recurrence: 1 — candidate: maybe
- **compose-verb-from-existing-verbs**: build a convenience verb (ask = send+wait+read) by calling the existing command functions so their guards carry, routing sub-command chatter to stderr so stdout stays the payload — recurrence: 1 — candidate: no (one instance; the pattern is just single-source reuse)

## 2026-07-28 — orca-pin-identity-line — no candidates
## 2026-07-28 — j17-dispatch-verdict-guard — no candidates

## 2026-07-29 — task3-verify-exec-validate

- **hmad-5e-verify-recipe**: the canonical Phase-5e verification against merged/tree code — module pytest (report count) → anti-gaming test audit (name each non-discriminating test + its mitigation, or "all N discriminating") → property grep on the source (quote the line for each stated property) → full suite vs a reference number, any FAILURE is a blocker not a silent fix. Ran fully this session (25 module / 7819 full, Task 3). Recurs once per H-MAD feature — recurrence: 1 this session, high cross-session — candidate: **LANDED** (2026-07-29) — `h-mad/references/codex-verifier-prompt.md` + SKILL.md 5e (`step5e:verify_failed`), doc-test `test_h_mad_verifier_prompt.py` (mutation-verified). Absorbs the exec-transport-smoke content-crosscheck kernel.
- **find-parked-hmad-task**: locate a parked H-MAD task's repo/branch/worktree when the handoff names none — cross-reference `orca worktree list` (childWorktreeIds), scratchpad `codex_task*_*.txt`, and `.h-mad/telemetry.jsonl`; the scratchpad TDD prompts carry REPO/BRANCH/FEATURE verbatim. Recovered Task 3 (feature/191, HemaSuite) this session — recurrence: 1 — candidate: **LANDED** (2026-07-29) — fixed at the source in handoff `SKILL.md`: parked feature-work must record `repo · branch · worktree` + artifact paths (WRITE), plus a READ-mode recovery bullet for older location-less handoffs.
- **exec-transport-smoke**: validate `hmad-dispatch exec` live — read-only prompt ending in a STATUS line, peek `--log` mid-run to prove live streaming (not end-dump), extract with `h_mad_extract_verdict.py --key STATUS`, then grep the real numbers the agent quoted before trusting them (caught codex 21 vs actual 28 under a DONE line) — recurrence: 1 — candidate: **LANDED (folded)** — the content-crosscheck kernel is now the "Cross-check — do not trust your own headline numbers" section of `h-mad/references/codex-verifier-prompt.md`.

## 2026-07-29 — skill-upgrades-verifier-parked-paths

- **promote-candidate-to-rule-or-verb**: map an open candidate to a concrete insertion point (new `references/*.md` template + SKILL.md wiring, or a handoff-SKILL doc rule), TDD the doc-test → mutation-verify the guards → run BOTH coupled suites → reconcile the candidate row → commit. Ran twice more this session (h-mad 5e verifier + handoff parked-path). — recurrence: 4 (cumulative) — candidate: maybe (this IS the upgrade workflow, already documented 2026-07-24; a checklist not a script)
- **pin-hmad-test-interpreter**: h-mad doc-tests need `/opt/anaconda3/bin/python3` (pytest 8.3.5); bare `python3` can resolve to homebrew 3.14 without pytest, and `set -e` + a mutation loop then applies edits without ever running the tests. — recurrence: 1 — candidate: no (captured as a `docs/learnings.md` gotcha; not a skill)

## 2026-07-29 — verifier-dogfood-and-handover

- **dogfood-a-bundled-prompt-live**: after bundling a new agent-prompt template, exercise it via `hmad-dispatch exec` before trusting it — stage the `<INLINE_*>` slots against real code, run once TRUE (expect DONE) and once with a seeded FALSE property (expect BLOCKED), extract the verdict, and grep the agent's own quoted numbers. Caught that the verifier's full-suite step was impractical (codex re-runs a PTY-dots suite → timeout) → template fix. — recurrence: 2 (exec-transport-smoke + this) — candidate: maybe (the discipline is real; overlaps the verifier template's own crosscheck)
- **scoped-dispatch-to-isolate-a-step**: when one step of a multi-step dispatch is environmentally impractical (a 4.5-min full suite codex re-runs), re-dispatch a SCOPED prompt with that step dropped to prove the rest cleanly, then fix the step's ownership in the template — recurrence: 1 — candidate: no (a one-off debugging move, not a reusable skill)


## 2026-07-30 — dispatch-prompt-size-frontier-92kb

- **live-probe-a-claimed-limit**: when a doc asserts a size/perf ceiling ("unverified beyond N"), falsify it with a real dispatch (stage a >N prompt + sentinel, send via the actual transport, read `--from-start`, grep) before trusting or re-baking the number — reproduced the reflow-false-silence trap and raised the pane frontier 61→92 KB — recurrence: 1 — candidate: maybe (overlaps the tracer-bullet / mutation-test disciplines already documented)
- **reframe-limit-by-transport**: when one "limit" conflates independent mechanisms (transport cap vs agent-response cap), split the claim per mechanism rather than bumping a single fixed number — recurrence: 1 — candidate: no (one instance; a writing principle, not a workflow)

## 2026-07-30 — exec-missing-report-recovery-shipped

- **full-h-mad-single-fn-feature**: ran the complete 7-phase /h-mad (brainstorm→spec→plan→design→impl-plan→RED→GREEN→5e→6a-prime→gap→report→merge) for a one-function shell fix; Codex authored RED+GREEN via exec, agy audited via pane report-file — recurrence: 1 — candidate: no (this IS the /h-mad skill)
- **verify-review-finding-against-tests**: before applying a 5e/review DRIFT prescription, diff it against the RED tests + spec ACs; a finding matching the design doc but breaking tests means the design drifted, not the impl — recurrence: 2 (this + reference-relevance-ranking A-P1-4) — candidate: maybe (already an Axis-B rule "Verifying a review finding before acting"; this is a second reinforcement, not new)
