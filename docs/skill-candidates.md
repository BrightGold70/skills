# Skill Candidates

Appended by the `/handoff` automation scout, newest session last. **Status is only useful if it is
current** — reconcile a row when the thing it describes ships, the same way `docs/skill-monitoring.md`
rows are flipped.

**Verdicts:** `yes` / `maybe` / `no` (scout's initial call) · `LANDED` (shipped — name where) ·
`SUPERSEDED` (a different fix removed the need) · `DECLINED` (deliberately not doing it, with the
reason) · `done` (legacy spelling of LANDED).

## Open, highest recurrence first (reconciled 2026-08-20)

**Two `candidate: yes` are open**, and neither is the one that was loudest.
`live-e2e-pane-janitor` (rec 6 → **8**) — still open, but **re-scope before building**: the hard
half (identifying which panes this session created) is now solved by `exec-pane`'s slot registry
`.h-mad/panes/<handle>.cd`, so what remains is only closing probe panes created outside that verb.
`vendored-plugin patch kit` (rec 2) — untouched. Both re-checked against source on 2026-08-20 and
still open; see that session's block below.

**`audit-cycle-background-dispatch` (rec 8) is now LANDED** (2026-08-19). It called itself right:
a SKILL.md fix, not a new skill. `h-mad/SKILL.md` now backgrounds every dispatch example, bans
`tail -f` (an orchestrator cannot run it — it never returns), and points at the new bounded
`hmad-dispatch progress <log>` instead.

**One `candidate: yes` was open at the prior reconcile: `live-e2e-pane-janitor` (rec 6, spanning two 2026-08-03 sessions).**
The "all recurrences inside one session" caveat that held it back is now **gone** — the
orca-defects session hit it twice more independently, and grew its scope: probe *dispatches* must be
settled (`task-update --status completed`) as well as panes closed, because `worker-abandon` and
`worker-stop` both fail to release one. **This now meets the re-scout promote trigger below**
(rec ≥3, `candidate: yes`, fresh recurrence in a later session block). The prior holder,
`orca-verb-live-reconcile`, was promoted 2026-08-03
to `invariants.base.md` §"Wrapper–runtime reconciliation", generalized off Orca since that file is
project-agnostic. Its recurrence count reached 5 on the day it landed: the two create-response `.id`
bugs, the live `check` probe that surfaced `run_required`, and — hours later, in the run that
promoted it — the ack key proving to be `deliveryId` while the extraction chain led with
`delivery_id` and the only test pinned the spelling the runtime never sends.

Everything else is reconciled. The 2026-07-24 sweep drained everything up to that date;
the 2026-08-03 sweep reconciled the five `yes` rows the 08-01→08-03 sessions added. Four of those
five described work that had **already shipped** — the same stale-row pattern the
`verify-backlog-row-premise-vs-code` rule exists for, and the reason status here is worth nothing
unless it is checked against source rather than read off the label. What remains are `maybe` rows
that *describe the /h-mad skill that already exists*, kept as provenance, not work.

| rec | candidate | status |
|---|---|---|
| 6 | `live-e2e-pane-janitor` | *yes* — **OPEN, and the only actionable row.** Close scratch panes by elimination AND settle their dispatches; two sessions, 2026-08-03 |
| 9 | `close-a-filed-defect cycle` | **LANDED** — SKILL.md §Working a `skill-monitoring` item |
| 27 | `H-MAD phase-doc + agy-audit-gate loop` | *maybe* — already the /h-mad skill. **+18 on 2026-08-06** (two features, 5 audit phases). The judgement is the skill; the MECHANICAL prefix is not — assemble → 4 residual-slot greps → `exec agy` → `report-wait` → gate is byte-identical every cycle |
| 6 | `audit→fix→subagent-review→merge loop` | *maybe* — already the /h-mad skill |
| 4 | `agy-skill-review` | **LANDED** (2026-08-03) — `references/agy-skill-reviewer-prompt.md` + SKILL.md §Reviewing a skill with agy |
| 3 | `test-pinned-the-defect check` | **LANDED** — invariants.base.md §Regression provenance |
| 3 | `verify-backlog-row-premise-vs-code` | **LANDED** — folded into close-a-filed-defect step 1 |
| 3 | `two-direction mutation harness` | **LANDED** — `h-mad/scripts/h_mad_mutation_harness.py` |
| 3 | `doc-literal pin test` | **LANDED** — practice across 5 doc-test files; rule in invariants.base.md §Test discrimination |
| 3 | `wire-scoped revert probe` | **SUPERSEDED** — the bundled mutation harness *is* this tool (exact-string replace, refuses unless the anchor matched exactly once, restores and verifies on every path) |
| 5 | `orca-verb-live-reconcile` | **LANDED** (2026-08-03) — `invariants.base.md` §"Wrapper–runtime reconciliation", generalized off Orca (that file is project-agnostic); pinned by `test_h_mad_invariants_layering.py` |
| 2 | `both-halves doc fix` | **LANDED** — invariants.base.md §Both halves of a doc change |
| 2 | `orca-verb-live-reconcile`, `live-e2e verb sweep` | **SUPERSEDED** — both folded into `invariants.base.md` §"Wrapper–runtime reconciliation" |
| 2 | `test-the-shipped-function-not-a-copy` | **LANDED** — invariants.base.md §Single-source contract ("independent re-implementations that can silently diverge are a violation"); also structurally moot, since every bash test drives the real script via subprocess rather than a copy |
| 1 | `differential-validator-test` | **LANDED** — invariants.base.md §Reimplementation parity |
| 1 | `reconcile a handoff's PR claims via gh` | **LANDED** (2026-08-03) — handoff SKILL.md Step 3 "PR state". Was filed `candidate: no`, but its own reason named the upgrade ("belongs in the handoff skill's READ reconciliation"); the `no` meant *not a standalone skill* and nobody routed it. |

**Re-scout trigger:** promote only when a *fresh* recurrence (rec ≥3, `candidate: yes`) appears in a
later session block. **As of the 2026-08-03 orca-defects session this has FIRED**, for
`live-e2e-pane-janitor` — see the paragraph above. It is the one actionable row; everything else
remains drained. **Re-checked 2026-08-05** (exec-verdict-laundering session): still open, still
nothing shipped — `hmad-dispatch` has no `terminal close` verb — and no new recurrence, because that
session ran entirely on stubs and created no scratch panes. Count stays 6.

**A `no` can still name an upgrade.** The verdict answers "is this a new skill?", which is not the
same question as "should an existing skill change?". Read the *reason* on every `no` and `maybe`
before concluding a row is inert — one row sat inert for a day while naming its own insertion point.


## 2026-07-20 — orca-adaptation-tiers

- **agy/codex poll-until-idle dispatch**: assemble prompt -> hmad-dispatch send -> background poll on idle marker ("? for shortcuts" present, "esc to cancel" absent) + schema token -> parse verdict — recurrence: 12+ (every audit/TDD/arch-review this session) — candidate: **LANDED** 2026-07-24 — `hmad-dispatch ask` (send + wait-idle + full-buffer read; extraction stays a separate `h_mad_extract_verdict.py` call). Live-dogfooded against agy
- **H-MAD phase-doc + agy-audit-gate loop**: write phase doc -> assemble audit prompt (template+doc+invariants) -> dispatch agy -> gate -> fix -> re-audit — recurrence: 9 (3 features x 3 phases) — candidate: maybe (already the /h-mad skill; a helper to stage+dispatch+gate in one call would cut ~40 tool calls)

## 2026-07-21 — orca-arc-complete-hemasuite-wiring

- **orca-verb-live-reconcile**: after shipping an orca-wrapping verb, run a live create→list→remove cycle against the real runtime and fix output-key extraction — recurrence: 5 (worktree-create + automation-create envelope-.id bug; 2026-08-03 probing the live `check` response for a delivery-id field is what surfaced `run_required` — orchestration mode had been dead at step one and no stub test could see it; 2026-08-03 later, the real ack key was `deliveryId` while the chain led with `delivery_id` and the only test pinned the spelling the runtime never sends) — **LANDED** (2026-08-03) — `invariants.base.md` §"Wrapper–runtime reconciliation"
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

- **dogfood-a-bundled-prompt-live**: after bundling a new agent-prompt template, exercise it via `hmad-dispatch exec` before trusting it — stage the `<INLINE_*>` slots against real code, run once TRUE (expect DONE) and once with a seeded FALSE property (expect BLOCKED), extract the verdict, and grep the agent's own quoted numbers. Caught that the verifier's full-suite step was impractical (codex re-runs a PTY-dots suite → timeout) → template fix. — recurrence: 3 (exec-transport-smoke; verifier template; 2026-08-03 the agy skill-reviewer — where dogfooding found TWO defects in the freshly-bundled prompt: a slot bracketed in prose across all five reference prompts, and an unbounded probe that wrote a junk entry into the project's permanent learnings file) — candidate: maybe (the discipline is real and keeps paying; overlaps the verifier template's own crosscheck)
- **scoped-dispatch-to-isolate-a-step**: when one step of a multi-step dispatch is environmentally impractical (a 4.5-min full suite codex re-runs), re-dispatch a SCOPED prompt with that step dropped to prove the rest cleanly, then fix the step's ownership in the template — recurrence: 1 — candidate: no (a one-off debugging move, not a reusable skill)


## 2026-07-30 — dispatch-prompt-size-frontier-92kb

- **live-probe-a-claimed-limit**: when a doc asserts a size/perf ceiling ("unverified beyond N"), falsify it with a real dispatch (stage a >N prompt + sentinel, send via the actual transport, read `--from-start`, grep) before trusting or re-baking the number — reproduced the reflow-false-silence trap and raised the pane frontier 61→92 KB — recurrence: 1 — candidate: maybe (overlaps the tracer-bullet / mutation-test disciplines already documented)
- **reframe-limit-by-transport**: when one "limit" conflates independent mechanisms (transport cap vs agent-response cap), split the claim per mechanism rather than bumping a single fixed number — recurrence: 1 — candidate: no (one instance; a writing principle, not a workflow)

## 2026-07-30 — exec-missing-report-recovery-shipped

- **full-h-mad-single-fn-feature**: ran the complete 7-phase /h-mad (brainstorm→spec→plan→design→impl-plan→RED→GREEN→5e→6a-prime→gap→report→merge) for a one-function shell fix; Codex authored RED+GREEN via exec, agy audited via pane report-file — recurrence: 1 — candidate: no (this IS the /h-mad skill)
- **verify-review-finding-against-tests**: before applying a 5e/review DRIFT prescription, diff it against the RED tests + spec ACs; a finding matching the design doc but breaking tests means the design drifted, not the impl — recurrence: 2 (this + reference-relevance-ranking A-P1-4) — candidate: maybe (already an Axis-B rule "Verifying a review finding before acting"; this is a second reinforcement, not new)

## 2026-07-31 — tdd-dispatch-verification-discipline-shipped

- **exec-terminal-mode-audit**: run a full /h-mad audit cycle via `exec agy` in terminal/sentinel mode (assemble without --report-file, --out capture, h_mad_extract_report.py) when panes are flaky — ran 20+ times this session across plan/design/impl-plan audits — recurrence: 20+ — candidate: maybe (a documented usage of existing verbs, not a new script; worth a SKILL.md note that exec agy audits use the sentinel scrape not report-file)
- **loop-driven-h-mad**: /loop dynamic mode driving a full 7-phase /h-mad to completion across turns, one phase-chunk per iteration with ScheduleWakeup — recurrence: 1 (this session) — candidate: no (composition of two existing skills; worked as-is)

## 2026-08-01 — hmad-dispatch-timeout-pgroup

- **test-the-shipped-function-not-a-copy**: verify a bash helper by `awk`-extracting the function from the real file into a test harness and sourcing it, instead of hand-pasting it into the test — a hand-copy silently drifts from what ships and can pass while the real code is broken — recurrence: 2 (this session: the first pass hand-copied `_run_with_timeout`, the second extracted it) — candidate: **LANDED** (2026-08-03) — `invariants.base.md` §Single-source contract already forbids it ("independent re-implementations that can silently diverge are a violation"). Also structurally moot: no test hand-copies or `awk`-extracts a bash function today; all of them drive the real script via subprocess.
- **attribute-dirty-files-by-mtime-before-committing-all**: on "commit and push all", `stat -f %m` every uncommitted path and compare against `date +%s` before staging — separates this session's work from a concurrent session's in-flight edits, and catches a test run having mutated live state — recurrence: 1 — candidate: maybe (one occurrence, but it changed the outcome here: it kept a concurrent agent's mid-write plan docs from being committed torn)
- **check-ignore-before-force-add**: when `git add` refuses a tracked file, read the `.gitignore` rule and `git ls-files` it before reaching for `-f` — tracked-but-later-ignored files are meant to be `git rm --cached`, not force-committed — recurrence: 1 — candidate: no (this is ordinary git discipline, not a workflow worth scripting)

## 2026-08-02 — wiring-task-shape-gate

- **two-direction mutation harness**: snapshot source in memory, apply a literal mutation, assert it LANDED, run suite, restore + verify byte-identical; permissive and always-fires directions both required — recurrence: 3 (doc literals, gate code, header parser) — candidate: **LANDED** — `h-mad/scripts/h_mad_mutation_harness.py` (both directions are expressible as ordinary find/replace mutations; the harness proves each one landed)
- **doc-literal pin test**: assert distinctive contiguous whitespace-normalised literals scoped per-file, so a doc change cannot silently drop its guidance — recurrence: 3 — candidate: **LANDED** — the practice across 5 doc-test files (`_norm`-normalised literal assertions), with the rule in `invariants.base.md` §Test discrimination. Caveat learned 2026-08-03: scope the literal per *rule*, not per *site* — a one-site assertion stayed green while the same guidance was missing from three others.
- **dogfood a new gate over the shipped corpus before committing**: running the wire-pin gate over ~50 real impl-plans found a parser defect 35 unit tests missed — recurrence: 2 — candidate: maybe

## 2026-08-02 — wire-pin-mislabel-merged

- **hand-craft an adversarial input before merging a guard**: write a single plan/fixture carrying the evasion the PR closes, the evasion it does NOT close, and one malformed-but-plausible variant, then run the shipped script on it — the green suite proved the closed case; the crafted file is what surfaced the full-demotion residual and the trailing-prose misread — recurrence: 1 — candidate: maybe (one occurrence, but it produced both of this session's review findings)
- **reconcile a handoff's PR claims via `gh` before acting on them**: `gh pr view <N> --json state` plus a `git log` scan for a squash title ending in `(#N)` — the resumed doc's top Next Step was "merge PR #18" and #18 had already merged hours earlier — recurrence: 1 — candidate: no (belongs in the handoff skill's READ reconciliation, not a new skill) — **LANDED** (2026-08-03) — handoff `SKILL.md` Step 3 "PR state" bullet (`gh pr view` + squash-title fallback). The `no` verdict was correct and still named an upgrade nobody routed; see the header note.

## 2026-08-02 — wire-retro-verify-task5-parked

- **wire-scoped revert probe**: a throwaway script that severs ONE call site by exact-string replace, refuses unless the replacement landed exactly once (`hits != 1` → abort), keeps a `.py.wirebak` sidecar, and offers `cut`/`force`/`restore` verbs — used 3× this session across two wires and two directions, then deleted per skill discipline; reconstructing it each time is the friction — recurrence: 3 — candidate: **SUPERSEDED** (2026-08-03) — `h_mad_mutation_harness.py` is exactly this tool: exact-string replace, `hits != 1` → REFUSED, restore-and-verify on every path including SIGINT. Use it for wire-scoped reverts instead of rebuilding the probe.
- **retro-declaration check before trusting a gate verdict**: compare the plan/spec's edit time against the implementation's GREEN commit — a document edited after the phase it gates certifies nothing about that phase — recurrence: 1 — candidate: maybe (one occurrence, but it inverted the meaning of a PASS)
- **agent-availability preflight recovery chain**: `env` → read the `PREFLIGHT:` token not `$?` → `pin-agents` (not `launch`, J1) → re-assert `env` — recurrence: 2 — candidate: maybe (already prose in SKILL.md §Phase 5; a script would just enforce the ordering)

## 2026-08-03 — wire-pin-gate-hardened

- **corpus-sweep-before-regex-tighten**: Before narrowing a plan-parser regex, diff old-vs-new parse across the whole shipped-plan corpus to prove exactly which lines change — recurrence: 2 (this + prior parser work) — candidate: maybe (covered by mutation-test discipline + a learning; promote only if it recurs standalone)
- **review→reproduce-live→RED→fix→mutate**: The escalation path that turned Task #17 from a 1-line strip into a fail-closed rewrite — recurrence: this is the h-mad Phase-5 TDD discipline already — candidate: no (already a skill/discipline)

## 2026-08-03 — agy-reviews-mutation-harness

- **agy-skill-review**: Dispatch `hmad-dispatch exec agy <prompt-file> --cd --out --log --timeout`, read the report yourself, verify EVERY finding against the file before acting, then fix + TDD + mutation-test. Ran twice this session (handoff, h-mad) with an almost identical prompt scaffold — role, target, read-in-full vs read-on-demand, depth-over-breadth cap, required Must/Should/Nice + Verdict sections — recurrence: 2 — candidate: **LANDED** (2026-08-03) — `h-mad/references/agy-skill-reviewer-prompt.md` + SKILL.md §Reviewing a skill with agy. Superseded by the recurrence-3 row below; kept for provenance.
- **integration-branch-before-batch-merge**: Before merging N open PRs, build a throwaway branch, merge all N, resolve, run the full suite, delete it — `merge-tree` clean does not mean the union is green — recurrence: 1 (but caught a real conflict + an untested union) — candidate: maybe (promote if a second multi-PR batch recurs)
- **cross-repo-contract-change**: When a skill script's exit code/token/flags change, update the consuming repo's tests in the same breath and run both suites — recurrence: 1 this session, but the coupling is permanent — candidate: no (already covered by the `skills symlink couples repos` memory)

## 2026-08-03 — takeover-and-hemasuite-handover

- **agy-skill-review**: `hmad-dispatch exec agy <prompt-file> --cd --out --log --timeout`, read the report yourself, verify EVERY finding against the file, then fix + TDD + mutation-test. Ran three times now (handoff, h-mad, orca-cli) with the same prompt scaffold — role, read-in-full vs read-on-demand, depth-over-breadth cap, findings classified by who can act, required Must/Should/Nice + Verdict — recurrence: 3 (4 including the 2026-08-03 `orchestration` review) — candidate: **LANDED** (2026-08-03) — `h-mad/references/agy-skill-reviewer-prompt.md` + SKILL.md §Reviewing a skill with agy. Dogfooding the bundled template found two defects in it (a slot bracketed in prose across all five reference prompts; an unbounded probe that wrote to the project's learnings file).
- **verify-inbound-handover**: On receiving a handover, run its reproduce commands before adopting any premise — 3 of 5 items were re-verified true, and the two the sender had already corrected were confirmed rather than assumed — recurrence: 1 (but now codified as TAKEOVER Step 2 in the skill) — candidate: no (shipped as skill guidance)
- **mutation-survivor-triage**: Diagnose a survivor as weak test / equivalent mutant / pre-existing weak test before acting — recurrence: 2 sessions — candidate: no (belongs to the mutation memory + harness docs, not a separate skill)

## 2026-08-03 — orchestration-fixes-skill-reviewer

- **verify-vendor-flags-against-`--help`**: before reporting a wrapped CLI's flag/subcommand as missing, unsupported, or renamed, run `<cmd> --help` and quote the real signature — the vendor's own guide lags the binary. Six flags checked this session; four "undocumented flag" findings were all real flags the 388-line guide omits, and two of those four were self-generated because the review prompt named the guide as ground truth — recurrence: 4 (one per false finding) — candidate: **LANDED** (2026-08-03) — `h-mad/references/agy-skill-reviewer-prompt.md` §"Ground truth is the binary" + SKILL.md §"Reviewing a skill with agy"; memory `feedback_vendor_managed_skills_not_patchable`
- **integration-probe-before-merging-to-main**: cut a throwaway branch from `main`, merge there, run the full suite AND re-run every mutation spec, then merge to `main` only if green. `merge-tree` clean and a marker-free `git merge` both passed while the union was red — a coverage guard on one branch fired on a file that exists only on the other, so neither branch could fail alone — recurrence: 2 (the recorded 2026-08-03 batch-merge row + this) — candidate: **LANDED as a practice** — memory `feedback_union_green_not_merge_clean`. Not scripted: the probe branch is meant to be deleted, and a permanent script would contradict that.
- **coverage-assertion-over-site-scoped-doc-test**: when a rule spans several files, assert it over *every* file (walk the tree, collect offenders, assert the list is empty) instead of pinning one literal at one site — and match instances, not mentions. A site-scoped test stayed green while the `git add -N` fix was missing from 3 of 4 places naming the hazard — recurrence: 2 (stash sites; bracketed-slot wildcard across five prompts) — candidate: **LANDED** — `invariants.base.md` §Test discrimination covers the rule; the 8th hazard is recorded in memory `feedback_mutation_test_every_guard`
- **bound-the-probes-you-invite**: a review prompt that tells an agent to run commands must say which ones are read-only. The freshly-bundled skill-reviewer invited `--help` probes without bounding them and the reviewer probed a *mutating* verb, writing a junk entry into the project's permanent learnings file — recurrence: 1 — candidate: **LANDED** (2026-08-03) — the template's "Probes must be read-only" block, mutation-guarded

## 2026-08-03 — agent-identity-and-await-correctness

- **live-e2e-pane-janitor** *(still open; partially eased 2026-08-19 — see note at end of row)*: after a live orchestration probe, enumerate panes in the worktree and close the ones this session created — by ELIMINATION against a known-good set, since `worker-start` panes inherit the worktree name and are indistinguishable by title. Hand-rolled the same `terminal list --json` → filter → `terminal close` pipeline 4× this session, each time re-typing the operator's keep-list; getting it wrong closes the operator's own agent pane — recurrence: 7 (4 on 2026-08-03 agent-identity + 2 in the 2026-08-03 orca-defects session + 1 on 2026-08-07 re-verifying the same bug docs) — candidate: yes — **scope grew: panes are only half.** The orca-defects session had to settle 5 probe *dispatches* (`task-update --status completed`) as well as close 4 panes, because an unsettled dispatch wedges its terminal permanently — `worker-abandon`/`worker-stop` both return `dispatch_not_found` for it (see `docs/orca-bug-worker-release-dispatch-not-found.md`). A janitor that closes panes without settling their dispatches leaves the Run dirty. **Confirmed again 2026-08-07 and now has an upstream issue:** the same dance ran once more (throwaway pane + `worker-start` control pane, both needing `task-update --status completed` before `terminal close`), and the underlying defect is filed as stablyai/orca#13005 — so the janitor's need is not going away by itself. Still no implementation: no `pane-janitor` anywhere, and `hmad-dispatch` has `worktree-rm` but no pane/dispatch cleanup verb.
- **two-arm-probe-before-asserting-a-cause**: when attributing an observed failure to a cause, run the *controlled pair* (with/without the one variable) before writing the cause down. I blamed pane readiness for an `injected:false` and shipped that causality in a doc + PR body; a 2-command retest on a booted pane showed the missing `--inject` flag was the whole story — recurrence: 4 (this; the title-only "no agents running" conclusion the operator corrected the same session; then BOTH carried repros in the 2026-08-03 orca-defects session, each falsified by a control that removed the blamed step) — candidate: maybe (`invariants.base.md` §"Assumption verification" already mandates executing assumptions; this is the narrower "isolate ONE variable" case and may just be a line there) — **promoted to memory instead of a skill:** `feedback_carried_repro_is_not_evidence`, which states it as "run the repro AND a control that removes the step it blames". Still worth the `invariants.base.md` line; leave open until that lands.
- **stub-must-model-the-destructive-step**: a stub that replays state the real system CONSUMES makes a test pass before the fix exists. The orca stub replayed an acked delivery forever, so a sibling-cache test re-matched from the queue and pinned nothing — it passed against unmodified code — recurrence: 1 — candidate: maybe (close to `invariants.base.md` §"Test discrimination", but that rule is about asserting the right thing, not about the fixture lying)
- **mutation-anchor-drift-after-self-edit**: `h_mad_mutation_harness.py` REFUSED 3 runs this session with `anchor matched 0 times`, twice because my own edits had moved the anchored lines between writing the spec and running it. The verdict is correct and load-bearing (REFUSED measures nothing), but the recovery is manual re-grepping. A near-miss hint on 0 matches would close the loop — recurrence: 3 — candidate: maybe (harness enhancement, not a new skill)

## 2026-08-03 — orca-defects-and-preflight-decision

- **live-e2e-pane-janitor** (recurrence, not a new row): hand-rolled scratch-terminal creation +
  `terminal close` twice more, and this time also had to settle 5 probe dispatches. See the row
  above — count is now 6 and spans two sessions.
- **mutation-spec-shares-one-anchor**: when several mutations target the SAME line with different
  replacements (exit code / stream routing / message content), the spec is five near-identical
  blocks differing only in `replace`. That shape is what proved the content assertions load-bearing
  in J22 — the two mutations that keep exit+stream and strip only the text are the ones a
  returncode-only test survives. Worth a spec-generator or a documented recipe rather than
  retyping the anchor five times — recurrence: 2 (J22, then J23 the same day with 8 mutations across
  two guards) — candidate: maybe (it is a *pattern for writing specs*, and the harness already
  exists; a §recipe in `invariants.base.md` §"Mutation verification" may be the whole fix)
  — **J23 sharpened what the recipe would have to say**, and it is not just "vary one field": the
  two mutations that SURVIVED the first pass were both weak tests of mine, and the diagnosis
  (weak test / equivalent mutant / pre-existing weak test) is the part that has no recipe yet. Also
  a concrete discriminator rule worth writing down: a first-vs-last-occurrence mutant survives
  whenever the sought item is last in BOTH regions, so the discriminating case must put the decoys
  between the markers and leave the tail empty.
- **give-the-transport-e2e-real-work**: a transport e2e whose payload is a smoke string proves the
  transport and nothing else; the same run with a real review task as its payload proved the
  transport AND falsified a bug doc I had written 20 minutes earlier. Costs nothing extra —
  recurrence: 1 — candidate: no (judgement when authoring a probe, not a pipeline; captured as a
  learning + `feedback_carried_repro_is_not_evidence`)

## 2026-08-05 — exec-verdict-laundering-fixed

- **live-e2e-pane-janitor** (no new recurrence): this session ran no orchestration probes, so it
  created no scratch panes. Row above stays open at 6, unchanged. Re-verified nothing shipped —
  `hmad-dispatch` still has no `terminal close` verb.
- **mutation-spec-shares-one-anchor** (recurrence, not a new row): second spec written the same way,
  8 mutations across two guards. Bumped to 2 above, with what J23 added to the recipe.
- **replay-the-incident-artifact-against-your-own-fix**: keep the artifact that motivated a defect
  and run the fix against it before closing. J23's boundary slice passed every RED test and still
  fabricated a verdict on the real 20,770-byte log, because that log predates the marker the fix
  keys on — a hole no test written from the same understanding as the code could have found. Note
  `invariants.base.md` §"Incident replay" already mandates replaying a fix against historical data;
  what is new is that the *artifact* has to be preserved at handover time to make it possible —
  recurrence: 1 — candidate: no (the rule exists; the gap is that briefs should name and preserve
  the artifact path, which the `exec-verdict-laundering` brief did do and is why this worked)
- **verify-a-handover-brief's-CAUSE-with-a-control**: a brief can be right about the symptom and
  wrong about the cause; only a control that removes the blamed step separates them. Both handovers
  this session carried a stated cause, and one was wrong — recurrence: 2 — candidate: no (captured
  as memory `feedback_carried_repro_is_not_evidence`, which is where it belongs; it is judgement at
  read-time, not a pipeline)

## 2026-08-06 — gate-blindness-hardening-at-phase-5

- **wire-scoped-revert-runner**: revert ONE call site (callee + tests intact), assert a NAMED pin
  test fails, restore, assert it passes again — with an anchor-matches-exactly-once guard, because a
  revert that never landed reports as a pass. Hand-rolled 8× this session (W1–W5 on
  `exec-path-hardening`, plus the glob-quoting, heartbeat and non-interference guards), and my first
  attempt at looping it silently mangled its own shell variables so every pin selected 0 tests —
  which `pytest` exits 0 for — recurrence: 8 — candidate: maybe — **largely SUPERSEDED by
  `h_mad_mutation_harness.py`**, which already does exact find/replace, refuses an anchor not
  matching exactly once, restores on every path and re-runs to prove the restore. Two real gaps
  remain: it targets the whole suite (~105 s × N, vs ~1 s for a single named pin), and it reports
  `SURVIVED` rather than naming *which* pin failed to bite. File as an enhancement to that harness
  (`--target <nodeid>`), not as a new skill.

- **live-state-replay-probe**: reproduce a suspected defect by feeding REAL production state back
  through the pure function under test, rather than a synthetic fixture. Turned "the card looks
  wrong" into a deterministic 513 → 1026 doubling in one command, and a paired glob-free control
  falsified the mechanism cleanly — recurrence: 1 — candidate: no (one occurrence, and it is
  judgement at debug-time rather than a pipeline; captured as memory
  `feedback_hostile_fixtures_over_tidy_ascii`)


## 2026-08-07 — gate-blindness-shipped-rpl-at-phase-5

- **audit-cycle-background-dispatch**: a foreground `hmad-dispatch exec agy <prompt> --timeout 900`
  is killed by the harness's 10-minute command cap, not by the dispatch's own timeout — so the
  wrapper's `--out`/`--log` never land while the **report file does**. Every audit cycle after that
  used `nohup hmad-dispatch exec agy … & ` followed by `hmad-dispatch report-wait "$RP" --timeout 540`,
  hand-rolled each time. Recurrence: 8 (plan cycles 3-5, design cycles 1-8 this session; plus the
  one foreground cycle that was killed and had to be recovered from the report file) —
  candidate: yes — **the fix is probably a SKILL.md line, not a new skill.** The insertion point is
  `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e", which already documents `--log` tailing for
  monitoring but assumes the dispatch runs in the foreground. Naming the harness cap and the
  background + `report-wait` shape there would remove the need to rediscover it per session.
  Note this is *not* the documented "missing report" recovery: the report arrived fine, it was the
  caller that was killed.
  → **LANDED** (2026-08-19) — `h-mad/SKILL.md` §"Exit-code dispatch for 5d/5e" now shows every
  example backgrounded (`… & dispatch_pid=$!`), and §"Watching a headless dispatch" bans `tail -f`
  outright ("it never returns, so it consumes your whole tool-call budget") in favour of the new
  bounded `hmad-dispatch progress <log> --pid $!`. §"Do not poll on a timer when you only need the
  result" additionally says to run the blocking form as a BACKGROUND command so the harness
  re-invokes on exit — a completion signal rather than a poll. The row called it right: it was a
  SKILL.md fix, not a new skill. Commits `e78b46a`, `d29f37e`, `83d0a33`.

- **audit-loop-runner**: the full assemble → residual-placeholder preflight → dispatch →
  `report-wait` → `h_mad_audit_gate.py` → apply fixes → bump version-history loop, run 13 times
  this session (5 plan cycles, 8 design cycles) with the same six commands retyped each round.
  Recurrence: 13 — candidate: maybe — this *is* the `/h-mad` skill's documented Phase-3/4 loop, so
  it is parked provenance rather than a new skill; what is missing is only the mechanical wrapper.
  Worth promoting only if a future session finds the retyping is where cycles actually go wrong,
  rather than merely being tedious.

## 2026-08-07 — rpl-shipped-j26-orca-13005

- **hand-rolled report-wait**: I wrote `for i in $(seq 1 N); do [ -f "$RP.done" ] && break; sleep 15; done` around **~18** `exec` dispatches this session (every 5d/5e task, every audit cycle, both 6a-prime runs) — recurrence: 18 — candidate: no — **`hmad-dispatch report-wait <path> --timeout <s>` already does exactly this** and returns the report on stdout. Proved live: marker written at t=3s, `report-wait` returned the content at t=4s. This is the file's own "a different tool can already do the job" trap, turned on the orchestrator instead of a row. The upgrade is a **usage** rule, not a skill: SKILL.md documents `report-wait` only on the pane/audit path (§"Audit prompt assembly" step 9), so the `exec` sections never tell you it is transport-agnostic — which is why hand-rolling felt necessary. Worth one sentence in §"Exit-code dispatch for 5d/5e".
- **archreview-record-and-readback**: the 6a-prime close-out — extract `ASSESSMENT:`, capture it line-scoped, write to `orchestrator_state.archreview`, then read it back and compare — is four commands that must run in order, and the read-back is the only thing that catches a dropped write (`--strict-only` cannot: `archreview` is not in `required`) — recurrence: 2 (this feature + `gate-blindness-hardening`) — candidate: maybe — SKILL.md §6a-prime already prescribes all four steps precisely; the risk is skipping the read-back, not not knowing it. Revisit if a third feature gets it wrong.
- **carried-bug-doc refile protocol**: before filing a bug doc written N sessions ago — read the current version (`/Applications/Orca.app/Contents/Info.plist` → `CFBundleShortVersionString`, since `_meta.appVersion` is gone on 1.4.175), re-run the repro, run any control the doc admits it skipped, sanitize, then re-sweep the body **as published** — recurrence: 2 (both docs this session) — candidate: no — it is a checklist, now captured in [[project_orca_upstream_bug_docs]] and the skill's own §"Filing to a public tracker". A skill would add ceremony over a five-command sequence.

## 2026-08-09 — h-mad-symlink-install-repair

- **install-path suite verification**: after (re)installing a skill, run its test suite through the *install* path (`pytest ~/.claude/skills/<skill>/tests/`) rather than the repo path, because `diff -rq` between checkout and install dir proves content equality while staying blind to links the skill expects *outside* that dir — recurrence: 1 — candidate: maybe — one observation, and it paid for itself immediately (13 failures on a missing `~/.claude/hooks/h-mad-tdd-gate.sh` that content-diff called IDENTICAL). Too thin for a skill on one sighting; the durable half is already a learning. Revisit if a second skill install repeats it.
- **skill-install repair sequence**: `git rev-list --left-right --count origin/main...HEAD` to rule out the repo half → read the skill's own docs for its canonical install shape → back up outside `skills/` → link → suite through the install path — recurrence: 1 — candidate: no — the shape is entirely driven by what the target skill documents about itself (here: a symlink chain, two links), so a generic wrapper would have nothing to encode beyond "read the SKILL.md first."

## 2026-08-09 — h-mad-install-followup (same session as h-mad-symlink-install-repair)

- **arming-surface verification**: after changing a `settings.json` hook registration, the check that actually proves it is a real tool call through the harness plus `python3 -m json.tool` — the target skill's own suite invokes the hook directly and never reads `settings.json`, so it stays green either way — recurrence: 1 — candidate: no — this is two commands, and the durable half is already a learning. A skill would wrap nothing.
- **commit-message-via-file**: `git commit -F <scratchpad-file>` instead of the `-m "$(cat heredoc)"` idiom, forced by the bkit ENH-310 guard — recurrence: 2 this session (blocked twice) — candidate: maybe — it will recur on **every** multi-line commit on this machine, which is a real recurrence curve, but the fix is a one-line substitution already captured as a learning. Promote only if the substitution itself starts getting forgotten.

## 2026-08-09 — guard-patches-and-h-mad-install-gate

- **vendored-plugin patch kit**: patch a plugin in a version-pinned cache -> save the diff, a README with a *tested* `patch -p1` recovery, and a red-green verify script in the repo, then file upstream — recurrence: 2 this session (bkit ENH-310, security-guidance) — candidate: **yes** — the two directories are near-identical in shape and the second took a fraction of the time because the first had settled the structure. The reusable part is the checklist and the verify-script skeleton (absolute expectations, patch-symbol probe, exit 1 on missing), not the diffs. Worth promoting if a third vendored patch appears.
- **differential guard narrowing**: before shipping a change that makes a guard accept something it used to reject, run a corpus through old and new and account for every softened verdict — recurrence: 1 — candidate: no — now an Axis B invariant (`invariants.base.md` §"Guard narrowing"), which is a stronger home than a skill: it is inlined into every audit prompt and auto-classifies violations as Must-fix.
- **stale-clone push guard**: before pushing to a long-lived repo, `git fetch` and check divergence; if behind, build the change in a throwaway worktree off `origin/main` rather than rebasing a dirty tree — recurrence: 1 — candidate: maybe — it saved a 1519-commit rebase over uncommitted work and caught a commit message that had gone stale, but one sighting is thin. Revisit if another stale clone turns up.

## 2026-08-09 — j29-out-clobber-guard

- **mutation-pin the design decision, not just the behaviour**: after implementing a guard, apply the *obvious alternative reading* as a mutant and confirm a test kills it — recurrence: 2 (2026-08-09 guard-narrowing corpus; this session's `[ -s "$out" ]`-vs-change-keyed mutant) — candidate: **maybe** — the two instances share a shape: the naive reading passes every behavioural test and only the one test encoding the *rejected* alternative distinguishes them. Not yet a skill because both sightings are the same author on the same day; revisit if a third appears in a different area.

## 2026-08-19 — headless-dispatch-visibility

Reconciled first: **`audit-cycle-background-dispatch` → LANDED** (row updated in place above; its
own stated insertion point is exactly what shipped). `live-e2e-pane-janitor` re-verified and still
open, but materially eased — see its row note. `vendored-plugin patch kit` untouched, nothing this
session bore on it.

- **live-e2e-pane-janitor** *(existing row, recurrence bumped)*: this session created and hand-closed
  ~10 Orca panes across tracer probes and live e2e runs. Recurrence: 6 → **8**. Still
  candidate: yes, but **the hard half is now solved elsewhere**: `exec-pane`'s slot registry
  (`.h-mad/panes/<handle>.cd`) is exactly the "known-good set" the row wanted, so identifying which
  panes are h-mad's no longer needs elimination. What remains is closing probe panes created outside
  `exec-pane` — a smaller job than the row was originally scoped for. Re-scope before building.
- **shell mutation-test loop**: hand-rolled the same scaffold 4× this session (write a python
  mutation applier keyed by name, loop: restore backup → apply → `bash -n` → run the targeted test
  file → classify KILLED/SURVIVED → restore). Recurrence: 4 — candidate: **no, verify against the
  bundled harness first**. `h-mad/scripts/h_mad_mutation_harness.py <spec.json>` already exists and
  takes a JSON spec; I did not check whether its spec format covers shell-file mutations with
  arbitrary test commands before reinventing it. That is precisely the "a different tool can already
  do the job" trap this scout warns about, committed live. **Next session: read the harness's spec
  schema and either use it or record why it does not fit — do not hand-roll a fifth time.**
- **evidence-first premise check on an inbound handover**: the inbound brief this session closed had
  a central claim that was already false when written, caught only by diffing the pre-session commit
  rather than trusting the brief. Recurrence: 1 — candidate: no. Already covered by the handoff
  skill's §"Take over handed-over work" point 2 ("Verify the premises before adopting them"); noting
  it only as a live confirmation that the step earns its place.

## 2026-08-20 — advisor-context-budget-and-hook-wiring

Open rows re-checked against source, not against their labels: `live-e2e-pane-janitor` — still
open, unchanged by this session (`grep -c pane-janitor` over `hmad-dispatch` returns 0; the only
cleanup verb is still `worktree-rm`). `vendored-plugin patch kit` — untouched, no third vendored
patch appeared. Neither flips.

- **verdict-token gate scaffold**: h-mad hand-rolls one shape over and over — `check()` + a CLI
  printing `TOKEN: PASS|FAIL issues=N`, exit 0 on a verdict / 2 on a cannot-judge that carries **no
  count**, a doc table mapping every detail line to a runnable remedy, a bidirectional docs test
  (token in script ⇔ token in SKILL.md), and a parked mutation spec. Counted from SKILL.md's own
  helper registry: **12 distinct verdict tokens** (`CTXBUDGET`, `DOC-SHAPE`, `GATE`, `INSTALL`,
  `ISSUEFIX`, `MUTATION`, `PHASE7`, `PRECONDITION`, `STATE`, `STATE-WRITE`, `WIREPIN`, `WIRING`),
  two of them written this session from scratch — recurrence: 12 — candidate: maybe — **read the
  reason before promoting.** This is not a new skill; it is a generator or a template belonging
  *inside* h-mad (`scripts/` plus the matching test + mutation-spec stubs). The parts that actually
  cost time twice today were the invariants, not the code: cannot-judge must carry no count, the
  CLI must exit 0 on a verdict, and the docs table must be pinned bidirectionally or it drifts. A
  scaffold that emits those three by construction is worth more than one that emits argparse.

- **background-poll-until**: `sleep` is blocked in the foreground, so waiting on a long job means
  `run_in_background` plus `until [ -s <outfile> ]; do sleep N; done`. Hand-rolled 4× this session
  for one 3-minute pytest suite, and got it wrong twice (an empty output file reads as "still
  running" whether the job is running or its output never landed) — recurrence: 4 — candidate: no
  — the harness already re-invokes on completion, so the correct fix is to stop polling at all and
  let the task notification arrive. Recorded because the *wrong* reflex recurred, not because a
  skill is missing.

- **mutation-spec parking**: mutation specs were being written to `/tmp` and evaporating, so a
  guard nobody could re-run was indistinguishable from one nobody had checked. Four specs now live
  at `h-mad/tests/mutation-specs/*.json` and are re-runnable by path — recurrence: 1 — candidate:
  no — this shipped as a repo convention this session; it is a note for whoever wonders where the
  specs went, not a candidate.
