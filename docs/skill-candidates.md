# Skill Candidates

Appended by the `/handoff` automation scout, newest session last. **Status is only useful if it is
current** — reconcile a row when the thing it describes ships, the same way `docs/skill-monitoring.md`
rows are flipped.

**Verdicts:** `yes` / `maybe` / `no` (scout's initial call) · `LANDED` (shipped — name where) ·
`SUPERSEDED` (a different fix removed the need) · `DECLINED` (deliberately not doing it, with the
reason) · `done` (legacy spelling of LANDED).

**Triage of 2026-08-25 — `DECLINED` here also means "not codable".** Every open row was sorted into
useful/codable, useful/NOT-codable, or not-useful, and the two non-actionable buckets were closed with
`DECLINED`, each note naming its bucket and its reason. Read those carefully: for a useful/not-codable
row `DECLINED` means **no tool will be built**, NOT that the idea was rejected — the discipline stands
and the note says where it would live if promoted (usually `invariants.base.md` or a SKILL.md section,
the way seven rows landed earlier the same day). A not-useful row is genuinely closed. Duplicate rows
of one idea were `SUPERSEDED` into the fuller one rather than declined twice. This convention exists
because the alternative was a new vocabulary word, and every counter over this file keys on the three
terminal markers already documented above.

**What counts as open:** `yes` + `maybe`. A `no` is a verdict the scout already gave, not an
undecided row — it needs no further judgement, only a reason if it is ever promoted to `DECLINED`.
A terminal marker (`**LANDED**` / `**SUPERSEDED**` / `**DECLINED**`) wins over any `candidate:`
value in the same row, because both conventions are in use here: some rows *replace* the value
(`candidate: **SUPERSEDED**`), others leave `candidate: yes` and append `— **SUPERSEDED** (…)`.

**Recurrence bumps are not candidates.** A row whose bold name is followed by
`(recurrence, not a new row)`, `(no new recurrence)`, `(existing row, recurrence bumped)`, or
`(row ~N)` is a note on an existing row. It carries no verdict of its own — the verdict lives on the
canonical row — and counting it as a candidate inflates every total. Mark them that way when
appending, and never write a bare `candidate: <value>` inside one: prose such as "still
candidate: yes" is indistinguishable from a verdict to every counter that has run over this file.

**Count with the parser, not with `grep -c`.** `handoff/scripts/skill_candidates_census.py` applies
all three rules above and prints the bump rows it excluded so the number is auditable. A single-line
`grep -cE '^- \*\*.*candidate: \**yes'` misses continuation lines, misreads appended terminal
markers, and counts bumps — it has produced a wrong census of this backlog three times.

## Open, highest recurrence first (reconciled 2026-08-20, again after Phase-5 Tasks 1-4)

**Three `candidate: yes` are open** (census: OPEN yes+maybe = 35 of 104). The newest is
`h-mad Phase-5 per-task TDD dispatch driver` (rec 8) — see the 2026-08-20 Tasks 1-4 block at the
end. The other two were re-verified against source in the same pass and neither has shipped:
no `pane-janitor` exists anywhere and `hmad-dispatch` still has no pane/dispatch cleanup verb;
`docs/patches/` still holds exactly 2 directories, so the patch kit still waits on a third.

Of the two rows the Tasks 1-4 block adds beyond that driver, one is **SUPERSEDED on arrival** by
`h_mad_mutation_harness.py` (I hand-rolled its contract 6 times anyway and hit the exact failure it
prevents), and one is a `maybe` that names its own insertion point in `h-mad/SKILL.md` rather than
asking for a skill.

**Two `candidate: yes` were open before this session**, and neither is the one that was loudest.
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

**This table is a hand-maintained snapshot and drifts.** The authority is
`handoff/scripts/skill_candidates_census.py`, which reads whole rows; the grep in the scout
reference only sees the row's FIRST line, so a reconcile note on a continuation line is invisible
to it and the row over-reports as open. As of 2026-08-25: **8 open, all codable.**

| rec | candidate | status |
|---|---|---|
| 3 | `post-edit identifier sweep` | **LANDED 2026-08-26 (`08f383c`) — `h-mad/scripts/h_mad_identifier_sweep.py`.** Re-grep a removed/renamed identifier across ALL surfaces after the LAST edit (code · comments · docs · tests · mutation-spec anchors); failed 1 of 3 tries by hand on 2026-08-24 and shipped 3 stale refs in `a311385` |
| 7 | `live-e2e-pane-janitor` | **LANDED** (2026-08-25) — `h-mad/scripts/h_mad_pane_janitor.py`. Elimination against a RECORDED baseline, and a candidate is closed only when a `worker-list` row positively identifies it; subtraction alone closes the operator's own pane |
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
  — **SUPERSEDED 2026-08-25 (triage: duplicate row)** — the same wrapper-around-the-audit-loop idea as `audit-loop-runner` below, filed a session earlier and with a lower recurrence. Both self-diagnose as "already the /h-mad skill"; keeping two rows for one idea inflated the backlog by one.

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
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — this is the `/h-mad` + review discipline itself, already a skill. There is no artifact to build; the row records that the loop pays.
- **live-e2e verb sweep against real orca**: exercise every hmad-dispatch verb + skill mechanism vs the live runtime, matrix report — recurrence: 2 — candidate: maybe
  — **RE-CHECKED 2026-08-26: measured, and the ceiling is why it stays `maybe`.** The wrapper declares **46 verbs**; only **4** (`env`, `worktree-current`, `worktree-ps`, `worktree-list`) are read-only and therefore safely sweepable unattended. All four were run against the live runtime today: rc=0, non-empty, well-formed payloads with the documented containers. The other 42 either mutate state (`worktree-create`/`-rm`/`-comment`, `automation-*`, `gate-*`) or cost a real agent dispatch (`exec`, `agy`, `codex`, `report-wait`), so a "matrix report" over them is not a script — it is a budgeted live session. That is the real reason this has sat at recurrence 2 across sessions, and it is worth recording so the next scout does not re-derive it. A 4-verb read-only sweep is cheap enough to be worth nothing as a tool: it is one shell loop, and it found no drift.

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
  — **SUPERSEDED 2026-08-25 (triage: duplicate row)** — duplicate of the later `promote-candidate-to-rule-or-verb` row, which carries the fuller reasoning.
- **verify-backlog-row-premise-vs-code**: before flipping a candidate/registry row, confirm its claim against git log -S / grep — 3 rows described already-shipped work this session, and (prior session) 4 monitoring rows were stale — recurrence: 3 — candidate: **LANDED** (2026-07-24) — folded into close-a-filed-defect step 1 (SKILL.md §Working a `skill-monitoring` item)
- **fix-the-fixture-not-just-the-assertion**: when a mutation survives after tightening an assertion, suspect the test DATA — aligned word lengths let a naive cut hit a boundary — recurrence: 1 — candidate: maybe
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — a rule about where to look when a mutation survives. Its home is `invariants.base.md` §"Test discrimination", beside the stub-must-model-the-destructive-step line landed this session.
- **compose-verb-from-existing-verbs**: build a convenience verb (ask = send+wait+read) by calling the existing command functions so their guards carry, routing sub-command chatter to stderr so stdout stays the payload — recurrence: 1 — candidate: no (one instance; the pattern is just single-source reuse)

## 2026-07-28 — orca-pin-identity-line — no candidates
## 2026-07-28 — j17-dispatch-verdict-guard — no candidates

## 2026-07-29 — task3-verify-exec-validate

- **hmad-5e-verify-recipe**: the canonical Phase-5e verification against merged/tree code — module pytest (report count) → anti-gaming test audit (name each non-discriminating test + its mitigation, or "all N discriminating") → property grep on the source (quote the line for each stated property) → full suite vs a reference number, any FAILURE is a blocker not a silent fix. Ran fully this session (25 module / 7819 full, Task 3). Recurs once per H-MAD feature — recurrence: 1 this session, high cross-session — candidate: **LANDED** (2026-07-29) — `h-mad/references/codex-verifier-prompt.md` + SKILL.md 5e (`step5e:verify_failed`), doc-test `test_h_mad_verifier_prompt.py` (mutation-verified). Absorbs the exec-transport-smoke content-crosscheck kernel.
- **find-parked-hmad-task**: locate a parked H-MAD task's repo/branch/worktree when the handoff names none — cross-reference `orca worktree list` (childWorktreeIds), scratchpad `codex_task*_*.txt`, and `.h-mad/telemetry.jsonl`; the scratchpad TDD prompts carry REPO/BRANCH/FEATURE verbatim. Recovered Task 3 (feature/191, HemaSuite) this session — recurrence: 1 — candidate: **LANDED** (2026-07-29) — fixed at the source in handoff `SKILL.md`: parked feature-work must record `repo · branch · worktree` + artifact paths (WRITE), plus a READ-mode recovery bullet for older location-less handoffs.
- **exec-transport-smoke**: validate `hmad-dispatch exec` live — read-only prompt ending in a STATUS line, peek `--log` mid-run to prove live streaming (not end-dump), extract with `h_mad_extract_verdict.py --key STATUS`, then grep the real numbers the agent quoted before trusting them (caught codex 21 vs actual 28 under a DONE line) — recurrence: 1 — candidate: **LANDED (folded)** — the content-crosscheck kernel is now the "Cross-check — do not trust your own headline numbers" section of `h-mad/references/codex-verifier-prompt.md`.

## 2026-07-29 — skill-upgrades-verifier-parked-paths

- **promote-candidate-to-rule-or-verb**: map an open candidate to a concrete insertion point (new `references/*.md` template + SKILL.md wiring, or a handoff-SKILL doc rule), TDD the doc-test → mutation-verify the guards → run BOTH coupled suites → reconcile the candidate row → commit. Ran twice more this session (h-mad 5e verifier + handoff parked-path). — recurrence: 4 (cumulative) — candidate: maybe (this IS the upgrade workflow, already documented 2026-07-24; a checklist not a script)
  — **DECLINED 2026-08-25 (triage: not useful)** — this IS the upgrade workflow, executed end to end this session across eleven rows. It is what you do with this file, not an entry in it.
  — **DECLINED 2026-08-25 (triage: not useful)** — this IS the upgrade workflow, executed end to end this session across eleven rows. It is what you do with this file, not an entry in it.
- **pin-hmad-test-interpreter**: h-mad doc-tests need `/opt/anaconda3/bin/python3` (pytest 8.3.5); bare `python3` can resolve to homebrew 3.14 without pytest, and `set -e` + a mutation loop then applies edits without ever running the tests. — recurrence: 1 — candidate: no (captured as a `docs/learnings.md` gotcha; not a skill)

## 2026-07-29 — verifier-dogfood-and-handover

- **dogfood-a-bundled-prompt-live**: after bundling a new agent-prompt template, exercise it via `hmad-dispatch exec` before trusting it — stage the `<INLINE_*>` slots against real code, run once TRUE (expect DONE) and once with a seeded FALSE property (expect BLOCKED), extract the verdict, and grep the agent's own quoted numbers. Caught that the verifier's full-suite step was impractical (codex re-runs a PTY-dots suite → timeout) → template fix. — recurrence: 3 (exec-transport-smoke; verifier template; 2026-08-03 the agy skill-reviewer — where dogfooding found TWO defects in the freshly-bundled prompt: a slot bracketed in prose across all five reference prompts, and an unbounded probe that wrote a junk entry into the project's permanent learnings file) — candidate: maybe (the discipline is real and keeps paying; overlaps the verifier template's own crosscheck)
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — a discipline — exercise a new agent-prompt template through a real dispatch before trusting it. Nothing to automate; the value is doing it, and it was done twice this session.
- **scoped-dispatch-to-isolate-a-step**: when one step of a multi-step dispatch is environmentally impractical (a 4.5-min full suite codex re-runs), re-dispatch a SCOPED prompt with that step dropped to prove the rest cleanly, then fix the step's ownership in the template — recurrence: 1 — candidate: no (a one-off debugging move, not a reusable skill)


## 2026-07-30 — dispatch-prompt-size-frontier-92kb

- **live-probe-a-claimed-limit**: when a doc asserts a size/perf ceiling ("unverified beyond N"), falsify it with a real dispatch (stage a >N prompt + sentinel, send via the actual transport, read `--from-start`, grep) before trusting or re-baking the number — reproduced the reflow-false-silence trap and raised the pane frontier 61→92 KB — recurrence: 1 — candidate: maybe (overlaps the tracer-bullet / mutation-test disciplines already documented)
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — the tracer-bullet rule applied to a documented ceiling. Already covered by the tracer-bullet and assumption-verification invariants.
- **reframe-limit-by-transport**: when one "limit" conflates independent mechanisms (transport cap vs agent-response cap), split the claim per mechanism rather than bumping a single fixed number — recurrence: 1 — candidate: no (one instance; a writing principle, not a workflow)

## 2026-07-30 — exec-missing-report-recovery-shipped

- **full-h-mad-single-fn-feature**: ran the complete 7-phase /h-mad (brainstorm→spec→plan→design→impl-plan→RED→GREEN→5e→6a-prime→gap→report→merge) for a one-function shell fix; Codex authored RED+GREEN via exec, agy audited via pane report-file — recurrence: 1 — candidate: no (this IS the /h-mad skill)
- **verify-review-finding-against-tests**: before applying a 5e/review DRIFT prescription, diff it against the RED tests + spec ACs; a finding matching the design doc but breaking tests means the design drifted, not the impl — recurrence: 2 (this + reference-relevance-ranking A-P1-4) — candidate: maybe (already an Axis-B rule "Verifying a review finding before acting"; this is a second reinforcement, not new)
  — **LANDED 2026-08-25** in `h-mad/invariants.base.md` as a NEW §"Verifying a review finding". **The row's own premise was false and that is why it stayed open:** it said this was "already an Axis-B rule", and no such section existed — a grep for the rule name returned 0 hits across all 20 sections. A row that believes it duplicates an existing rule is a row nobody ever implements. The section carries the part that actually costs time: a finding has THREE separable parts — facts, concern, prescription — which fail INDEPENDENTLY, and a prescription is tested by applying it as a mutation and reverting.

## 2026-07-31 — tdd-dispatch-verification-discipline-shipped

- **exec-terminal-mode-audit**: run a full /h-mad audit cycle via `exec agy` in terminal/sentinel mode (assemble without --report-file, --out capture, h_mad_extract_report.py) when panes are flaky — ran 20+ times this session across plan/design/impl-plan audits — recurrence: 20+ — candidate: maybe (a documented usage of existing verbs, not a new script; worth a SKILL.md note that exec agy audits use the sentinel scrape not report-file)
  — **DECLINED 2026-08-25: the prescription is inverted and would have written a FALSE rule.** The row asked for "a SKILL.md note that `exec agy` audits use the sentinel scrape not report-file". SKILL.md already says the opposite, deliberately: §"Exception — `exec agy` on an audit phase: fill the report-file slot", because on an audit the report IS the deliverable and `agy --print` surfaces only the last message, so the scrape is one fragile channel. And the two are not alternatives — 266,342 B was confirmed answered 8 of 8 on 2026-08-22 with **every run honouring both the report-file slot and the sentinel pair**. The row's recurrence (20+) was real; its facts about what those runs did were not. A three-part failure: the observation was true, the concern was empty, the prescription was harmful.
- **loop-driven-h-mad**: /loop dynamic mode driving a full 7-phase /h-mad to completion across turns, one phase-chunk per iteration with ScheduleWakeup — recurrence: 1 (this session) — candidate: no (composition of two existing skills; worked as-is)

## 2026-08-01 — hmad-dispatch-timeout-pgroup

- **test-the-shipped-function-not-a-copy**: verify a bash helper by `awk`-extracting the function from the real file into a test harness and sourcing it, instead of hand-pasting it into the test — a hand-copy silently drifts from what ships and can pass while the real code is broken — recurrence: 2 (this session: the first pass hand-copied `_run_with_timeout`, the second extracted it) — candidate: **LANDED** (2026-08-03) — `invariants.base.md` §Single-source contract already forbids it ("independent re-implementations that can silently diverge are a violation"). Also structurally moot: no test hand-copies or `awk`-extracts a bash function today; all of them drive the real script via subprocess.
- **attribute-dirty-files-by-mtime-before-committing-all**: on "commit and push all", `stat -f %m` every uncommitted path and compare against `date +%s` before staging — separates this session's work from a concurrent session's in-flight edits, and catches a test run having mutated live state — recurrence: 1 — candidate: maybe (one occurrence, but it changed the outcome here: it kept a concurrent agent's mid-write plan docs from being committed torn)
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — an mtime is a hint, not an owner. Deciding which concurrent session owns an uncommitted file is judgement, and a script that guessed would be worse than the pause it replaces.
- **check-ignore-before-force-add**: when `git add` refuses a tracked file, read the `.gitignore` rule and `git ls-files` it before reaching for `-f` — tracked-but-later-ignored files are meant to be `git rm --cached`, not force-committed — recurrence: 1 — candidate: no (this is ordinary git discipline, not a workflow worth scripting)

## 2026-08-02 — wiring-task-shape-gate

- **two-direction mutation harness**: snapshot source in memory, apply a literal mutation, assert it LANDED, run suite, restore + verify byte-identical; permissive and always-fires directions both required — recurrence: 3 (doc literals, gate code, header parser) — candidate: **LANDED** — `h-mad/scripts/h_mad_mutation_harness.py` (both directions are expressible as ordinary find/replace mutations; the harness proves each one landed)
- **doc-literal pin test**: assert distinctive contiguous whitespace-normalised literals scoped per-file, so a doc change cannot silently drop its guidance — recurrence: 3 — candidate: **LANDED** — the practice across 5 doc-test files (`_norm`-normalised literal assertions), with the rule in `invariants.base.md` §Test discrimination. Caveat learned 2026-08-03: scope the literal per *rule*, not per *site* — a one-site assertion stayed green while the same guidance was missing from three others.
- **dogfood a new gate over the shipped corpus before committing**: running the wire-pin gate over ~50 real impl-plans found a parser defect 35 unit tests missed — recurrence: 2 — candidate: maybe
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — a step in the build of any gate, not a gate of its own. Done for the wire-pin gate and for `h_mad_version_history.py` this session (564 real docs).

## 2026-08-02 — wire-pin-mislabel-merged

- **hand-craft an adversarial input before merging a guard**: write a single plan/fixture carrying the evasion the PR closes, the evasion it does NOT close, and one malformed-but-plausible variant, then run the shipped script on it — the green suite proved the closed case; the crafted file is what surfaced the full-demotion residual and the trailing-prose misread — recurrence: 1 — candidate: maybe (one occurrence, but it produced both of this session's review findings)
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — the input has to be crafted against the specific guard; that is the whole value and it cannot be generated. Recorded as a step, not a script.
- **reconcile a handoff's PR claims via `gh` before acting on them**: `gh pr view <N> --json state` plus a `git log` scan for a squash title ending in `(#N)` — the resumed doc's top Next Step was "merge PR #18" and #18 had already merged hours earlier — recurrence: 1 — candidate: no (belongs in the handoff skill's READ reconciliation, not a new skill) — **LANDED** (2026-08-03) — handoff `SKILL.md` Step 3 "PR state" bullet (`gh pr view` + squash-title fallback). The `no` verdict was correct and still named an upgrade nobody routed; see the header note.

## 2026-08-02 — wire-retro-verify-task5-parked

- **wire-scoped revert probe**: a throwaway script that severs ONE call site by exact-string replace, refuses unless the replacement landed exactly once (`hits != 1` → abort), keeps a `.py.wirebak` sidecar, and offers `cut`/`force`/`restore` verbs — used 3× this session across two wires and two directions, then deleted per skill discipline; reconstructing it each time is the friction — recurrence: 3 — candidate: **SUPERSEDED** (2026-08-03) — `h_mad_mutation_harness.py` is exactly this tool: exact-string replace, `hits != 1` → REFUSED, restore-and-verify on every path including SIGINT. Use it for wire-scoped reverts instead of rebuilding the probe.
- **retro-declaration check before trusting a gate verdict**: compare the plan/spec's edit time against the implementation's GREEN commit — a document edited after the phase it gates certifies nothing about that phase — recurrence: 1 — candidate: maybe (one occurrence, but it inverted the meaning of a PASS)
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — comparing a doc's edit time against the GREEN commit it gates is two git commands, but reading whether the edit MATTERED to that phase is judgement. Overlaps `re-gate-after-edit guard`, which is the codable half and stays open.
- **agent-availability preflight recovery chain**: `env` → read the `PREFLIGHT:` token not `$?` → `pin-agents` (not `launch`, J1) → re-assert `env` — recurrence: 2 — candidate: maybe (already prose in SKILL.md §Phase 5; a script would just enforce the ordering)
  — **SUPERSEDED 2026-08-25: already documented, verified rather than assumed.** The chain the row describes is in `SKILL.md` at three places (the `PREFLIGHT: PASS` requirement, the `preflight_expired` recovery, and the re-assert-after-any-re-pin rule) plus the Phase-5d bullet, which also spells out WHY `alive codex && alive agy` is forbidden. Nothing to add; this row's reading of its own status was correct, unlike the two beside it.

## 2026-08-03 — wire-pin-gate-hardened

- **corpus-sweep-before-regex-tighten**: Before narrowing a plan-parser regex, diff old-vs-new parse across the whole shipped-plan corpus to prove exactly which lines change — recurrence: 2 (this + prior parser work) — candidate: maybe (covered by mutation-test discipline + a learning; promote only if it recurs standalone)
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — a habit before narrowing any parser, exercised three times this session. Covered by the mutation-verification invariant; no separate artifact.
- **review→reproduce-live→RED→fix→mutate**: The escalation path that turned Task #17 from a 1-line strip into a fail-closed rewrite — recurrence: this is the h-mad Phase-5 TDD discipline already — candidate: no (already a skill/discipline)

## 2026-08-03 — agy-reviews-mutation-harness

- **agy-skill-review**: Dispatch `hmad-dispatch exec agy <prompt-file> --cd --out --log --timeout`, read the report yourself, verify EVERY finding against the file before acting, then fix + TDD + mutation-test. Ran twice this session (handoff, h-mad) with an almost identical prompt scaffold — role, target, read-in-full vs read-on-demand, depth-over-breadth cap, required Must/Should/Nice + Verdict sections — recurrence: 2 — candidate: **LANDED** (2026-08-03) — `h-mad/references/agy-skill-reviewer-prompt.md` + SKILL.md §Reviewing a skill with agy. Superseded by the recurrence-3 row below; kept for provenance.
- **integration-branch-before-batch-merge**: Before merging N open PRs, build a throwaway branch, merge all N, resolve, run the full suite, delete it — `merge-tree` clean does not mean the union is green — recurrence: 1 (but caught a real conflict + an untested union) — candidate: maybe (promote if a second multi-PR batch recurs)
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — a procedure for a situation that has arisen once. `merge-tree` clean not meaning the union is green is worth knowing; a script would be premature.
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
  — **LANDED 2026-08-25** as `h-mad/scripts/h_mad_pane_janitor.py` (`JANITOR: SNAPSHOT|PLANNED|CLEANED|NOTHING|REFUSED`, exit 0/2, **dry run unless `--apply`**), with `tests/test_h_mad_pane_janitor.py` (25 tests) and `tests/mutation-specs/pane_janitor.json` (13 mutations, ALL_CAUGHT, each born pinned). Both halves the row names are covered: panes AND their dispatches. **The elimination set is recorded rather than remembered** — `snapshot --worktree <p> --out <f>` before the probe, and a candidate is then a pane in that worktree, absent from the baseline, and not the caller's own; the caller's handle is re-read LIVE from `orca terminal show` (which with no `--terminal` returns the caller's pane) and the run REFUSES when it cannot identify itself. Dispatches are settled with `task-update --status completed` BEFORE their pane closes, and a settle that fails leaves the pane open and says so. Two live footguns found while building, neither in the row: `orca terminal close` takes `--terminal` **optionally** and a bare close kills the CALLER's pane, so every close is explicit and a mutation pins it; and `worker-list` is used rather than `task-list` because the latter answers `run_required` without a bound Run — a janitor that only works inside a bound Run cannot clean up after a probe that left one unbound. **Live e2e on a real install:** snapshot recorded the 2 panes of this worktree and excluded a concurrent agent session in a sibling worktree; a pane was then created, `plan` found exactly it, `clean --apply` closed exactly it, and the count returned to 4 with this session intact. That run also CONFIRMED the row's premise: the created pane's title came back as `~/orca/skills`, **byte-identical to a pre-existing pane in the same worktree**, so a title-based janitor had a coin-flip. Two of the 13 mutations initially survived and **both were weak tests of mine, not missing guards** — including the caller-pane guard itself, where the fixture always wrote a `self` key, so the baseline was quietly doing the work the test claimed to check. Note: **no independent review ran** — `exec agy` returned exit 0 twice with an empty log and no report, and `advisor()` was over its context ceiling (`projected=702148 ceiling=45`).
  — **CORRECTION 2026-08-25: the "agy was down" claim in the note above is FALSE, and the cause was mine.** The operator checked the agy pane: Antigravity CLI 1.1.20, Gemini 3.1 Pro (High), authenticated and idle at a prompt. A trivial `hmad-dispatch exec agy` ping then returned `VERDICT: ALIVE` with a 2,206-byte log, so neither agy nor the `exec` path was broken. **Both failed dispatches were double-backgrounded**: `hmad-dispatch exec agy … &` run INSIDE an already-backgrounded shell, so the parent exited immediately and killed the dispatch — which is exactly the evidence I had (first run: init plus one `step_update` then nothing; second: an empty log; both exit 0). I measured the wrapper's corpse and read the null as "agy is down", the same wrong-surface mistake the taxonomy already records. **Background the BLOCKING form and let the harness signal completion; never add `&` inside it.** The review the note said was unavailable was then run against the shipped code — see the row's next line.
  — **Reviewed 2026-08-25 (agy, `EVIDENCE: PASS tools=3 ok=3 thinking=3943`), and it found a real safety hole the whole build had missed.** `Candidates = Live − Baseline − Self` is subtraction, and **subtraction cannot tell the probe's panes from the operator's**: an operator who opens a pane in the worktree after the snapshot — to tail a log while the probe runs — produces a delta byte-identical to a probe pane, and neither existing guard saw it. `--max` only bounds how many get closed; the self-handle protects the one shell the janitor runs in, not the operator's other tabs. Fixed by **positive identification**: a candidate is closed only when a `worker-list` row ties it to the probe, and one without a worker row is reported `unidentified` and left alone unless `--include-unidentified` is passed. The flag exists because a pane made by `terminal create` legitimately has no worker row — that is the path the original live e2e exercised — so the escape hatch is kept, just made deliberate. The review also caught a **fraudulent test**: the stub's `deny` knob was global, so it tripped on the first orca call (`terminal show`) and `test_an_orca_that_answers_not_ok_refuses` never reached the `worker-list` payload it claimed to test. The knob is now scoped per command and a real worker-list-failure test was added. Applying the fix then **broke a previously-killed mutation**: `dry-run-closes-anyway` began surviving because its pane was now unidentified, so the dry-run branch was never reached and the test passed for a new wrong reason — three fixtures were given worker rows. Now 30 tests, 17 mutations ALL_CAUGHT, suite 1959/0, and live-re-verified: an operator-created pane was correctly left alone by default and closed only with the explicit flag. **Two of the review's three prescriptions were adopted; the third — abandon negative identification entirely and correlate creation timestamps — was not**, because `worker-list` already answers the question positively for anything `worker-start` created, and timestamps would add a second, weaker inference for the case the flag now covers.
- **two-arm-probe-before-asserting-a-cause**: when attributing an observed failure to a cause, run the *controlled pair* (with/without the one variable) before writing the cause down. I blamed pane readiness for an `injected:false` and shipped that causality in a doc + PR body; a 2-command retest on a booted pane showed the missing `--inject` flag was the whole story — recurrence: 4 (this; the title-only "no agents running" conclusion the operator corrected the same session; then BOTH carried repros in the 2026-08-03 orca-defects session, each falsified by a control that removed the blamed step) — candidate: maybe (`invariants.base.md` §"Assumption verification" already mandates executing assumptions; this is the narrower "isolate ONE variable" case and may just be a line there) — **promoted to memory instead of a skill:** `feedback_carried_repro_is_not_evidence`, which states it as "run the repro AND a control that removes the step it blames". Still worth the `invariants.base.md` line; leave open until that lands.
  — **LANDED 2026-08-25** as a line in `invariants.base.md` §"Assumption verification", the home the row itself named. Carries both halves: run the controlled PAIR rather than the repro alone (a repro confirms the symptom, never the cause), and re-run the MEASUREMENT as well as the claim, since a brief's conclusion can be right while its method is wrong.
- **stub-must-model-the-destructive-step**: a stub that replays state the real system CONSUMES makes a test pass before the fix exists. The orca stub replayed an acked delivery forever, so a sibling-cache test re-matched from the queue and pinned nothing — it passed against unmodified code — recurrence: 1 — candidate: maybe (close to `invariants.base.md` §"Test discrimination", but that rule is about asserting the right thing, not about the fixture lying)
  — **LANDED 2026-08-25** as a line in `invariants.base.md` §"Test discrimination", with the row's own distinction preserved: the surrounding rules are about asserting the right thing, this one is about the FIXTURE lying. Also folds in the cardinality case — a fake that writes a path once where production writes it twice let a verb never dispatch with 57 tests green.
- **mutation-anchor-drift-after-self-edit**: `h_mad_mutation_harness.py` REFUSED 3 runs this session with `anchor matched 0 times`, twice because my own edits had moved the anchored lines between writing the spec and running it. The verdict is correct and load-bearing (REFUSED measures nothing), but the recovery is manual re-grepping. A near-miss hint on 0 matches would close the loop — recurrence: 3 — candidate: maybe (harness enhancement, not a new skill)
  — **LANDED 2026-08-25.** A REFUSED anchor now prints `hint:` detail lines: near misses with line numbers when it matched 0 times (scored per line, so an identical line occurring twice reports BOTH locations), and the match locations when it matched more than once. The verdict is untouched — REFUSED still measures nothing — only the recovery changed. Proven on the five real drifted anchors sitting in this repo's own specs: three got an exact line number (`context_budget` pointed at both the `"OK"/"DENY"` and `"OK"/"HALT"` lines the mode split created; `hook_wiring` at the basename-match line), and two correctly reported `no near miss found` rather than guessing. It then paid for itself inside its own build: dogfooding the new harness spec produced a REFUSED whose hint named the line a rename had moved.

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
  — **LANDED 2026-08-25** as a §recipe in `invariants.base.md` §"Mutation verification", which the row said might be the whole fix. It is: vary one field, keep the anchor shared, and record the two discriminators — a first-vs-last-occurrence mutant survives whenever the sought item is last in BOTH regions, and `survived` has **four** distinct causes (missing guard, equivalent mutant, weak test, and a mutant that never ran) which the verdict token collapses into one word. The fourth was found the same day, in the harness itself.
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
  — **LANDED 2026-08-25**, as the enhancement this row itself prescribed rather than as a new skill. The two gaps it named are both closed: per-mutation `"test"` targets the named pin instead of the whole suite, and the report now says WHICH pin failed to bite via the `mechanism:` line. Note the speed half of the argument did not survive contact — every spec in this repo already scopes its `command` to one test file, so the ~105s×N figure was not the live cost; the value delivered is the discrimination, not the wall-clock.

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
  — **DECLINED 2026-08-25 (triage: not useful)** — its own text declines it — the retyping is tedious rather than error-prone, and the loop it wraps is the documented `/h-mad` Phase-3/4 protocol. Promote only if a session shows cycles going wrong AT the retyping.

## 2026-08-07 — rpl-shipped-j26-orca-13005

- **hand-rolled report-wait**: I wrote `for i in $(seq 1 N); do [ -f "$RP.done" ] && break; sleep 15; done` around **~18** `exec` dispatches this session (every 5d/5e task, every audit cycle, both 6a-prime runs) — recurrence: 18 — candidate: no — **`hmad-dispatch report-wait <path> --timeout <s>` already does exactly this** and returns the report on stdout. Proved live: marker written at t=3s, `report-wait` returned the content at t=4s. This is the file's own "a different tool can already do the job" trap, turned on the orchestrator instead of a row. The upgrade is a **usage** rule, not a skill: SKILL.md documents `report-wait` only on the pane/audit path (§"Audit prompt assembly" step 9), so the `exec` sections never tell you it is transport-agnostic — which is why hand-rolling felt necessary. Worth one sentence in §"Exit-code dispatch for 5d/5e".
- **archreview-record-and-readback**: the 6a-prime close-out — extract `ASSESSMENT:`, capture it line-scoped, write to `orchestrator_state.archreview`, then read it back and compare — is four commands that must run in order, and the read-back is the only thing that catches a dropped write (`--strict-only` cannot: `archreview` is not in `required`) — recurrence: 2 (this feature + `gate-blindness-hardening`) — candidate: maybe — SKILL.md §6a-prime already prescribes all four steps precisely; the risk is skipping the read-back, not not knowing it. Revisit if a third feature gets it wrong.
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — SKILL.md §6a-prime already prescribes all four steps precisely. The risk is skipping the read-back, which a script cannot fix — it would be one more thing to skip.
- **carried-bug-doc refile protocol**: before filing a bug doc written N sessions ago — read the current version (`/Applications/Orca.app/Contents/Info.plist` → `CFBundleShortVersionString`, since `_meta.appVersion` is gone on 1.4.175), re-run the repro, run any control the doc admits it skipped, sanitize, then re-sweep the body **as published** — recurrence: 2 (both docs this session) — candidate: no — it is a checklist, now captured in [[project_orca_upstream_bug_docs]] and the skill's own §"Filing to a public tracker". A skill would add ceremony over a five-command sequence.

## 2026-08-09 — h-mad-symlink-install-repair

- **install-path suite verification**: after (re)installing a skill, run its test suite through the *install* path (`pytest ~/.claude/skills/<skill>/tests/`) rather than the repo path, because `diff -rq` between checkout and install dir proves content equality while staying blind to links the skill expects *outside* that dir — recurrence: 1 — candidate: maybe — one observation, and it paid for itself immediately (13 failures on a missing `~/.claude/hooks/h-mad-tdd-gate.sh` that content-diff called IDENTICAL). Too thin for a skill on one sighting; the durable half is already a learning. Revisit if a second skill install repeats it.
  — **RE-CHECKED 2026-08-26: the check was RUN, and it passes.** `pytest` through the install path (`~/.claude/skills/h-mad/tests/`) — **2069 passed, 0 failed**. Both links the row is about are present and correct: `~/.claude/skills/h-mad` → the repo, and `~/.claude/hooks/h-mad-tdd-gate.sh` → `h-mad/hooks/h-mad-tdd-gate.sh`, which is the file whose absence produced the original 13 failures. Worth recording that for a **symlink** install the checkout and the install path are the same inode, so the content-equality blindness the row describes cannot arise here at all — the row's failure mode needs a COPY install. Still recurrence 1, still below the promotion bar, but no longer unverified.
- **skill-install repair sequence**: `git rev-list --left-right --count origin/main...HEAD` to rule out the repo half → read the skill's own docs for its canonical install shape → back up outside `skills/` → link → suite through the install path — recurrence: 1 — candidate: no — the shape is entirely driven by what the target skill documents about itself (here: a symlink chain, two links), so a generic wrapper would have nothing to encode beyond "read the SKILL.md first."

## 2026-08-09 — h-mad-install-followup (same session as h-mad-symlink-install-repair)

- **arming-surface verification**: after changing a `settings.json` hook registration, the check that actually proves it is a real tool call through the harness plus `python3 -m json.tool` — the target skill's own suite invokes the hook directly and never reads `settings.json`, so it stays green either way — recurrence: 1 — candidate: no — this is two commands, and the durable half is already a learning. A skill would wrap nothing.
- **commit-message-via-file**: `git commit -F <scratchpad-file>` instead of the `-m "$(cat heredoc)"` idiom, forced by the bkit ENH-310 guard — recurrence: 2 this session (blocked twice) — candidate: maybe — it will recur on **every** multi-line commit on this machine, which is a real recurrence curve, but the fix is a one-line substitution already captured as a learning. Promote only if the substitution itself starts getting forgotten.
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — a one-line substitution (`git commit -F <file>`), already a learning and used for every commit this session. Automating it would hide the guard that forces it.

## 2026-08-09 — guard-patches-and-h-mad-install-gate

- **vendored-plugin patch kit**: patch a plugin in a version-pinned cache -> save the diff, a README with a *tested* `patch -p1` recovery, and a red-green verify script in the repo, then file upstream — recurrence: 2 this session (bkit ENH-310, security-guidance) — candidate: **yes** — the two directories are near-identical in shape and the second took a fraction of the time because the first had settled the structure. The reusable part is the checklist and the verify-script skeleton (absolute expectations, patch-symbol probe, exit 1 on missing), not the diffs. Worth promoting if a third vendored patch appears.
  — **DECLINED 2026-08-25 (triage: not useful)** — its own condition was "worth promoting if a third vendored patch appears", and none has since. The reusable part — a verify-script skeleton — is thin next to the two diffs it would serve.
- **differential guard narrowing**: before shipping a change that makes a guard accept something it used to reject, run a corpus through old and new and account for every softened verdict — recurrence: 1 — candidate: no — now an Axis B invariant (`invariants.base.md` §"Guard narrowing"), which is a stronger home than a skill: it is inlined into every audit prompt and auto-classifies violations as Must-fix.
- **stale-clone push guard**: before pushing to a long-lived repo, `git fetch` and check divergence; if behind, build the change in a throwaway worktree off `origin/main` rather than rebasing a dirty tree — recurrence: 1 — candidate: maybe — it saved a 1519-commit rebase over uncommitted work and caught a commit message that had gone stale, but one sighting is thin. Revisit if another stale clone turns up.
  — **RE-CHECKED 2026-08-26: no fresh recurrence.** Six pushes this session, each preceded by `git rev-list --left-right --count @{u}...HEAD`; every one read `0\t0` or ahead-only, so the guard never had anything to catch. Stays recurrence 1.

## 2026-08-09 — j29-out-clobber-guard

- **mutation-pin the design decision, not just the behaviour**: after implementing a guard, apply the *obvious alternative reading* as a mutant and confirm a test kills it — recurrence: 2 (2026-08-09 guard-narrowing corpus; this session's `[ -s "$out" ]`-vs-change-keyed mutant) — candidate: **maybe** — the two instances share a shape: the naive reading passes every behavioural test and only the one test encoding the *rejected* alternative distinguishes them. Not yet a skill because both sightings are the same author on the same day; revisit if a third appears in a different area.
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — a rule about WHICH mutation to write — apply the rejected alternative reading — and choosing that reading is the judgement. Belongs beside the shared-anchor recipe in `invariants.base.md` §"Mutation verification".

## 2026-08-19 — headless-dispatch-visibility

Reconciled first: **`audit-cycle-background-dispatch` → LANDED** (row updated in place above; its
own stated insertion point is exactly what shipped). `live-e2e-pane-janitor` re-verified and still
open, but materially eased — see its row note. `vendored-plugin patch kit` untouched, nothing this
session bore on it.

- **live-e2e-pane-janitor** *(existing row, recurrence bumped)*: this session created and hand-closed
  ~10 Orca panes across tracer probes and live e2e runs. Recurrence: 6 → **8**. Still open on the
  canonical row above (no verdict is recorded here — see the legend), but **the hard half is now
  solved elsewhere**: `exec-pane`'s slot registry
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
  — **LANDED 2026-08-25** as `h-mad/scripts/h_mad_new_gate.py` (`SCAFFOLD: WROTE|REFUSED`, exit 0/2), with `tests/test_h_mad_new_gate.py` (20 tests) and `tests/mutation-specs/new_gate.json` (8 mutations, ALL_CAUGHT). **The row's count was stale and its reasoning was right.** Re-counted from the scripts rather than from the registry: **20** verdict tokens now, not 12, and 18 of the 20 share one contract. And the row's warning held — what the scaffold emits is the three INVARIANTS plus the tests that pin them, not argparse: a cannot-judge carrying no counts, exit 0 on any verdict, and a bidirectionally-pinned docs table. The generated suite is deliberately RED until the registry line is pasted, because the doc step is the one most easily skipped. **The proof is that the emitted mutation spec is ALL_CAUGHT out of the box** — a scaffold whose pins do not bite mass-produces the appearance of coverage, so that is asserted by a test which runs the generated suite AND the generated mutations against the generated gate. Two defects in the scaffold itself, both caught before commit: the emitted spec's `root` used the generator's own `SKILL_DIR` instead of `--skill-dir`, so every scaffolded gate's mutations would have mutated the WRONG repository; and one emitted mutation was EQUIVALENT for the very test it was pinned to (`0 if verdict == FAIL else 2` leaves a FAIL exiting 0), so it shipped as a survivor. A third was a weak assertion of mine — checking for a bare method name, which a `_test_`-renamed method still contains.

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

## 2026-08-20 — audit-cycle-verb phases 3+4

- **value-sweep-the-corrected-value**: after applying an audit fix, `grep` the corrected *value* (not the section) across every live doc in the feature, because the same claim is usually restated in 2–3 places and the fix lands in one. Caught 4 stale copies across this session that **two independent reviewers both missed** — spec FR-3's description contradicting its own AC-3.4, a plan risk row still asserting a disproven `exec` behaviour, a design cross-reference to a plan clause that had been deleted, and an AC counter that went stale twice. Roughly two-thirds of all 79 findings this session were this class — recurrence: 6 this session — candidate: maybe — **read the reason before promoting**: this is not a new skill, it is a step belonging in `h-mad/SKILL.md` §"Audit prompt assembly" between "revise" and "re-audit", and possibly a script taking a value + a doc set. The discipline is already recorded as an auto-memory (`feedback_value_sweep_not_spot_fix`); what is missing is anything mechanical.
  — **LANDED 2026-08-25** in `h-mad/SKILL.md` §"Audit prompt assembly", between revising and re-auditing exactly as the row prescribed. Records the evidence that makes it stick: ~two-thirds of one session's 79 findings were this single class, four stale copies survived TWO independent reviewers, a sweep has five surfaces (prose · code blocks · comments · ACs · the paired design), and closing a class in only one document of a pair RELOCATES it.
- **doc-version-history-append**: append a dated entry to a phase doc's `## Version History` via an assert-anchored substitution, so a failed anchor is loud rather than a silent no-op. Hand-rolled 27× this session (once per audit cycle across plan/spec/design). Twice the anchor had drifted and the assert is the only reason it was noticed — recurrence: 27 — candidate: maybe — the reusable part is the **assert**, not the append; a three-line helper that refuses when the anchor is absent or matches more than once would remove the whole class. Note the sibling failure this session hit: a multi-edit block that raised mid-way had already written some files and discarded the rest, which is why each edit now runs as its own verify-and-write (see taxonomy mode 17).
  — **LANDED 2026-08-25** as `h-mad/scripts/h_mad_version_history.py` (`VERSION-HISTORY: OK|DRY-RUN|REFUSED|UNREADABLE`, exit 0 on a write / 2 on refusal), with `tests/test_h_mad_version_history.py` (39 tests) and `tests/mutation-specs/version_history.json` (14 mutations, ALL_CAUGHT). **The row under-specified it and the corpus said so.** A sweep of 713 real `## Version History` sections across 2132 files found the three-line helper would have been wrong on its central job: of the 246 sections carrying two or more entries, 191 are ascending, **29 are descending and 26 are unsorted**, so append-at-end is wrong for 22% of them and silently so — the same failure mode the row was filed against, relocated from the anchor to the placement. Placement is therefore derived from the section; unsorted sections and the 140 table-shaped sections are refused rather than guessed or reformatted, a duplicate version is refused (27 bumps per session means re-runs happen), and every write self-checks that its own splice was insertion-only. Two premises of the build were also refuted by measurement rather than by review: the corpus scan that reported one file with 7 headers had matched on **stripped** lines while the script anchors on `^##`, so under the real anchor **no file in the corpus has more than one match** and the test asserting otherwise was wrong; and the `---`-terminator mutation survived as **corpus-equivalent** (14 rule-terminated sections, 0 where dropping the terminator moves the insertion point) until the fixture was given the bullet-after-rule case the corpus does not contain. Live-probed `--dry-run` over 564 real phase docs — 143 OK, 401 `anchor_missing` (audit reports have no such section), 11 `mixed_order`, 9 `table_shape`, zero crashes — and one live write on a real 138-line impl-plan produced `138a139`, a pure insertion, with the re-run refused as `duplicate_version`.
- **hand-run five-call audit cycle**: assemble → `exec agy` → `report-wait` → `--out` fallback → gate, twice per cycle, read both verdicts, union the findings — ran 27 times (54 dispatches) — recurrence: 27 — candidate: **no** — this *is* `audit-cycle-verb`, whose Phases 1–4 gated clean this session (`568418d`, `197ecc2`). Recorded so the recurrence count is visible against the feature rather than looking like an unmet need; flip to `**LANDED**` when Phase 7 archives.

**Reconcile pass (2026-08-20, this session):** both open `yes` rows re-checked against source and
**both remain genuinely open**. `live-e2e-pane-janitor` — no `pane-janitor` verb exists in
`hmad-dispatch.sh` (grep: 0 hits; the only git matches are edits to this file, not an
implementation), and this session used the `exec` path exclusively so no new recurrence. Its scope
note still holds: `exec-pane`'s slot registry solved the hard half, so re-scope before building.
`vendored-plugin patch kit` — `docs/patches/` holds **2** directories against its own stated
threshold of a third vendored patch; untouched this session.

## 2026-08-20 — audit-cycle-verb Phase 5 Tasks 1-4

- **h-mad Phase-5 per-task TDD dispatch driver**: assemble a codex RED (then GREEN) prompt from `<feature>.impl-plan.md` §"Task N" + `references/codex-implementer-prompt.md`, substitute the INLINE_* slots, dispatch `exec codex --model gpt-5.5` backgrounded, extract the `STATUS:` token from the report file with the `--out` fallback, then re-run pytest INDEPENDENTLY rather than trusting the verdict — recurrence: **20+ across two sessions** — 8 on 2026-08-20 (T1 RED+GREEN, T2, T3, T4, 3 fix cycles) and **12+ more on 2026-08-21** (Tasks 5-9 RED+GREEN, three GREEN fix cycles, two anti-gaming verifies, the J34/J35 fix, the size_status fix) — candidate: yes — every step is mechanical and identical per task; the only per-task input is the task number and a short list of task-specific constraints. Hand-assembling it is also where two real mistakes crept in: forgetting `--model gpt-5.5` (the config default cannot execute tools at all) and using bare `python3` (3.14, no pytest). A driver would carry both as defaults. **Reconciled 2026-08-21: still unimplemented, and the hand-assembly cost three MORE distinct mistakes in one session** — passing the prompt inline when `exec` takes a FILE PATH (`no such prompt file: <the whole prompt>`, rc=2, nothing runs); `--sandbox read-only` on a verifier, which kills pytest's tempdir so the pass measures nothing; and an unscoped `pytest` that collects the sibling project and dies with 23 pre-existing errors. All three are defaults a driver would carry. Also learned: quote the SCOPED test path in the prompt, and require the agent to report per-item mechanism, not just pass/fail. Note the one genuinely per-task judgement it must NOT automate away: labelling which existing tests are regression guards, since "guard changed" and "test weakened" are otherwise indistinguishable.
  — **LANDED 2026-08-25** as `h-mad/scripts/h_mad_assemble_tdd.py` (`ASSEMBLE-TDD: PASS|HALT`, exit 0/2), with `tests/test_h_mad_assemble_tdd.py` (36 tests) and `tests/mutation-specs/assemble_tdd.json` (14 mutations, ALL_CAUGHT, every one born pinned to its named test). It stages the prompt and prints the exact command block; **it deliberately does not dispatch** — the dispatch/poll/wait loop is SKILL.md §"Exit-code dispatch for 5d/5e", and a driver that dispatches either blocks blind for the timeout or re-implements `progress`. All five recorded mistakes are closed as defaults: `--model gpt-5.5` is baked in (confirmed NOT injected upstream — `hmad-dispatch.sh` only forwards `--model` when given); the chosen interpreter is PROBED for pytest and a failure names a working one; the prompt is passed as a path by construction; `--sandbox read-only` is refused for a phase that runs pytest; and `--test-path` is required and restated in the prompt. The judgement stays manual, as the row demands: a 5d without `--expect-fail`/`--expect-pass` is `counts_required`, never defaulted. Task slicing reuses the wire-pin gate's own `_TASK_RE`/`_parse_tasks` rather than a third parser. **v1 excludes** the agy 5e-review assembly and the codex-verifier assembly — the verifier is where mistake 4 was originally made, so the read-only rule is now written into SKILL.md §5e prose beside the verifier step as well as enforced here; the assembly of those two dispatches stays manual. **Dogfooding it found a serious defect in `h_mad_mutation_harness.py`, not in this script**: a byte-size-identical mutation applied inside the same filesystem-mtime second as the previous run reuses the stale `.pyc`, so the mutant never executes while the file on disk is genuinely mutated — a FALSE `survived`, measured 4 times in 6 trials. Fixed by purging cached bytecode around every run; the verdict is deterministic across 3 repeats now. That is a fourth cause of `survived` beyond the three this backlog already records (missing guard / equivalent mutant / weak test): **the mutant never ran at all.**
- **wire-scoped revert + force-direction mutation runner**: for a `wiring` task, cut the CALL with the callee intact and assert the WIRE-PIN fails, then force the caller past its guard and assert the converse test fails — recurrence: 6 this session (3 wiring tasks x 2 directions) — candidate: no — **SUPERSEDED** by `h-mad/scripts/h_mad_mutation_harness.py`, which already does exactly this contract (exact find/replace, refuse unless the anchor matches exactly once, restore on every path including interrupt, re-run the suite to prove the restore landed). I hand-rolled the dance 6 times anyway, and hit the failure the harness exists to prevent: one wire-scoped regex did not match, the run printed an EMPTY failing set, and an unlanded mutation plus a green suite reads as "connection enforced". The reusable gap is not a new skill — it is that Phase 5e should invoke the harness per wiring task rather than leaving it to Task 8's spec authoring.
- **design-shape end-to-end probe**: after GREEN, run the built binary directly against the design's documented output shapes (every verdict line, every field-presence rule) instead of only running the suite — recurrence: 4 this session — candidate: maybe — it found **four of Task 4's five defects**, none of which the 49-test suite or the independent reviewer saw: a hardcoded `cycle=1` behind an undeclared `--cycle`, a float/int mismatch that crashed every real wait behind 10 stubbed tests, a checklist printed on a cannot-judge verdict, and a verdict line that did not match its own AC. Probably belongs as an explicit obligation in `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps" — beside the revert test — rather than as a standalone skill, since it has no fixed command, only a fixed question: *does the running binary emit what the design says it emits?*
  — **LANDED 2026-08-25** in `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps", as the row prescribed — an obligation beside the revert test rather than a standalone skill, because it has no fixed command, only a fixed question: *does the running binary emit what the design says it emits?* Carries the count that argues for it: four of one task's five defects, none seen by a 49-test suite or an independent reviewer.

## 2026-08-21 — audit-cycle-verb Phase-4 re-audit

- **re-gate-after-edit guard**: refuse to call a document "gated" when its content hash differs from the version the last clean audit read — i.e. detect that a gated doc was edited afterwards and require a fresh cycle — recurrence: 2 (the v1.15 errata, then the cycle-22 nit fix) — candidate: maybe — this re-audit produced 9 findings on a design that had gated clean twice, and **4 of them were introduced by the edits fixing the previous cycle**, so the failure is not rare judgement but a structural property of editing after the gate. Probably a check inside `h_mad_audit_gate.py` or the forthcoming `audit-cycle` verb (record the gated content hash beside the verdict) rather than a standalone skill. Note the honest counter-argument: nits never block, so a strict version of this would force a cycle for a one-word fix — which is exactly what I chose to do here, at the cost of one extra cycle.
  — **LANDED 2026-08-26 (`1c5d89e`)** — `h_mad_audit_gate.py --gated <doc>` records a sha256 of each judged document beside the verdict; `--verify-stamp` re-hashes and answers `GATESTAMP: CURRENT | STALE | UNSTAMPED`, naming what moved. The refusals are the substance: a stamp is written only on PASS (one over a FAIL would let the readback bless a verdict that blocked), an unreadable gated file yields `GATE: UNSTAMPABLE` and writes nothing rather than recording a verdict over content the gate never saw, and `UNSTAMPED` is a cannot-judge that must never read as `CURRENT`. The token is deliberately `GATESTAMP:` and not `GATE:` so a consumer globbing the verdict line cannot conflate them. The row's counter-argument stands unchanged — the tool reports staleness and does not decide whether a one-word fix deserves a cycle.

- **mutation-mechanism verifier**: for each row of a connections/gating mutation spec, apply the mutation ALONE, run ONLY its named test, and require a one-line statement of WHY it failed — then diff that reason against the mechanism the spec's table claims. Ran this by hand ~16 times on 2026-08-21 — recurrence: 16 — candidate: yes — this is the only check that catches a mutation which fails the right test for the wrong reason. `MUTATION: ALL_CAUGHT survived=0 refused=0` and per-row isolation are BOTH structurally blind to it: 4 of 12 connection mutations in `audit-cycle-verb` passed every existing check while testing the wrong thing (one left the call executing and only discarded its result; one short-circuited a wait, becoming a second *drop* at a site that then had no force; one skipped `collect()` along with `gate()`). Found by an agy spec review, not by re-running the harness. The mechanical parts are the apply/run-one-test/restore loop and the anchor-uniqueness precheck (an anchor matching twice is `REFUSED`, which measures nothing and reads like progress); the judgement it must NOT automate is deciding whether the stated reason matches the table. **Reconciled 2026-08-22: still unimplemented, recurrence now ~33.** Seventeen more hand-run mutations this session (J38 ×2, J40 ×4, the context cap ×6, J42 ×2, J43 ×1, J18 ×2), every one checked for WHICH test caught it rather than merely that something did. That check paid twice: the J40 guard and the ctx-cap guard each had two mutations caught by two DIFFERENT tests (mutual discrimination), proving neither test was redundant — and the `--passes` guard's two mutations likewise. A harness reporting `ALL_CAUGHT` cannot distinguish that from one test catching everything. **Reconciled 2026-08-24: still unimplemented, and this session produced the row's cleanest confirmation yet — the first time the predicted failure was caught in the act.** Twelve more hand-run mutations (10 on `h_mad_offcontract_scan.py`, 2 kept on `test_verb_no_self_invocation`). On the latter the harness reported **`ALL_CAUGHT 3/3`** and **two of the three were caught by the WRONG assertion**: both died on `pids[$i]: unbound variable` and tripped `assert r.returncode == 0`, never reaching the property under test. A mutant caught by a return code proves the code crashes when broken and nothing about the property. They were discarded and the reason recorded inside the spec's `_why_only_two`, since a later reader would otherwise re-add them. Recurrence now ~45. The verifier's whole value is exactly this discrimination, and only hand-application surfaced it. **Reconciled 2026-08-24 (second session same day): still unimplemented; recurrence ~70, and this session surfaced a SECOND blindness the harness shares with the first.** Twenty-five more hand-run mutations across two new specs (`advisor_warn` 12, `audit_effort` 13). Two of them were **equivalent mutants** — `set -euo pipefail`, the CENTRAL defect in the blocking gate being replaced, is completely inert in the advisory that replaced it, and the missing-checker guard makes no observable difference. The harness reports an equivalent mutant as `survived`, which is byte-identical to a real coverage gap; only applying it and reading WHY nothing changed distinguishes them. Both were deleted from the spec with the reason recorded. In the other direction, two survivors turned out to be **weak tests of mine rather than missing guards** (a hostile path test that created the wrong parent dir; an empty-but-existing log with no test). So `survived` has at least three distinct causes — missing guard, equivalent mutant, weak test — and the verdict token collapses all three. **Reconciled 2026-08-25: still unimplemented; recurrence ~74, and this session produced a fourth data point for the same blindness — from the CAUGHT side.** Four hand-run mutations on the new `run` verb, all four killed. One of them (process-group `kill -TERM -$pid` → bare `$pid`) was caught not by the assertion it was aimed at — that no grandchild is orphaned to init — but by a **60-second `subprocess.TimeoutExpired`**: the orphan held the wrapper's stdout pipe open, so the test never reached its own assert. `ALL_CAUGHT` and a green-after-revert are both satisfied by that, and neither says the property was exercised. Same family as the 2026-08-24 `pids[$i]: unbound variable` case, but arriving through a hang rather than a crash, which is the harder one to notice: the run simply takes a minute longer. The mutation kept its place in the spec — the mechanism is real and the mutant is not equivalent — with the catching mechanism recorded alongside it, which is the whole point of the row.
  — **LANDED (mechanical half) 2026-08-25** in `h_mad_mutation_harness.py`. A mutation may now name the one test it is aimed at (`"test": "<nodeid>"`, with a spec-level `"target_command"`), which changes the scoring question from *did the suite go red* to *did THAT test bite*. A named test that PASSES while the suite goes red is reported as a **SURVIVOR** with a `mechanism:` line naming what actually bit — so the wrong-catcher case this row was filed against is now a verdict-visible finding rather than an `ALL_CAUGHT`. Untargeted mutations get the same `mechanism:` line, best-effort from the runner's `FAILED` output, so attributing an existing spec is one read instead of N re-runs. **The judgement half stays human, exactly as this row demands**: whether the mechanism that fired is the mechanism the spec claims is not automated, and `_mechanism` on a mutation is free text for that comparison. Nor does the tool distinguish the three causes of `survived` (missing guard / equivalent mutant / weak test) — it reports which of them the evidence points at and leaves the call to the author. Dogfooded immediately: the 14-mutation `version_history` spec was attributed automatically and reproduced a 4-mutant hand check from the same session exactly, and a new 13-mutation spec over the harness itself runs `ALL_CAUGHT` with every mutant killed by its NAMED test.

## 2026-08-22 — audit-cycle-verb-shipped-j-sweep

- **registry status census / lint**: count and classify the rows of a standing registry
  (`docs/skill-monitoring.md`, `docs/skill-candidates.md`) — how many carry a machine-readable
  status, which are open, which vocabulary words are used vs documented, and whether any prose
  accidentally matches the row regex — recurrence: 5 this session — candidate: yes — I hand-wrote
  five throwaway Python censuses over one file and **two of them returned confident false
  readings**: a splitter absorbed a trailing note and reported J18 open when its body said "Fixed",
  and `grep -c` exiting 1 on no match printed nothing and read as a clean zero. Then my own fix
  introduced two more: a `` `WORD` `` placeholder that matched the status regex, and a bolded
  `**J31–J33**` that manufactured a phantom J-id (`40 of 41`). Every one of those was caught only by
  re-running the census against its own output. The mechanical parts are the entry splitter (bounded
  on the row shape, never on prose), the used-vs-documented vocabulary diff, and the self-pollution
  check; the judgement it must NOT automate is deciding a row's actual status, which needs the
  source read.
  — **Reconciled 2026-08-25: HALF LANDED, and the shipped half returns a confident false clean on
  the other registry.** `handoff/scripts/skill_candidates_census.py` shipped the entry splitter and
  the bump-row exclusion, and this file's header now points at it. Two of the three mechanical parts
  are still absent: there is no used-vs-documented **vocabulary diff** and no **self-pollution
  check**. The larger gap is that the script is structurally blind to `docs/skill-monitoring.md`,
  the first registry this row names — `rows()` ends the current row on any line starting with `|`,
  and skill-monitoring is written as pipe tables (`| J1 | 🔴 | **FIXED** | …`), so every row is
  discarded the moment it begins. Measured 2026-08-25:
  `skill_candidates_census.py docs/skill-monitoring.md` prints `candidates=3 OPEN(yes+maybe)=0
  <none>=3` against a 1945-line file carrying 159 J-id occurrences, where a one-line grep over the
  table rows finds 31 status-bearing rows (25 FIXED, 2 RESOLVED, 2 DISPROVEN, 1 WONTFIX,
  1 MONITORING). That is the same "confident false reading" failure this row was filed to end, now
  shipped inside the tool meant to end it, and it is the more dangerous direction: the tool reports
  a *clean* registry, so nothing prompts a second look. Any "registry N open" claim derived from
  this script against skill-monitoring must be re-derived before it is trusted. Stays
  `candidate: yes` — the row is not done until the pipe-table shape parses and the two missing
  checks exist.
  — **LANDED 2026-08-25 (the other half).** All three mechanical parts the row named now exist in `handoff/scripts/skill_candidates_census.py`, with 23 tests and `handoff/tests/mutation-specs/census_registry.json` (9 mutations, ALL_CAUGHT, each by its named test). The **J registry parses**: entries are the `- <severity> **J<n> — title.**` bullets closed by the `Status: \`WORD\`` line the file's own header mandates, so `docs/skill-monitoring.md` reads **46 entries, 0 open** instead of `candidates=3 OPEN=0`. The **vocabulary diff** is a diff against that file's own `| \`WORD\` | meaning |` table rather than a copy that drifts. The **self-pollution check** became a COVERAGE line printed on every run — entries parsed versus row-shaped lines present — because the generalisable bug was never *pipe tables are unsupported*, it was **an unsupported shape reads as an empty backlog**, and a clean registry is the one answer nothing prompts you to re-check. **The numbers are now independently confirmed rather than assumed:** 46 rows carry 46 `Status:` lines 1:1, every word used is documented, and zero are `MONITORING` or `PLANNED` — so the carried claim that the J registry is 0 open is true, though until today it rested on a census that could not read the file at all. Two things this build got wrong first, both caught by the harness: the routing predicate used `re.search` on a `^`-anchored pattern without `MULTILINE`, so it never fired; and the first coverage metric counted J-ids mentioned ANYWHERE, which made the guard cry wolf on the header's own discussion of the deliberate J31–J33 gaps — the self-pollution failure in reverse. Candidate-store output is unchanged; the COVERAGE section is purely additive.

- **purely-additive bulk-edit assertion**: before committing a scripted edit that splices N lines
  into a long document, assert the diff is insertion-only — `git diff --numstat` shows `N 0`, every
  added line matches the expected shape, and the document's identifier set is byte-identical before
  and after — recurrence: 3 this session — candidate: maybe — used on the 31-entry status sweep and
  twice on `docs/skill-monitoring.md` edits. It is three commands rather than a skill, but it is the
  check that distinguishes a clean splice from a slice replacement that quietly ate a section, which
  is a failure this repo has shipped before. Promote only if a fourth bulk edit wants it; otherwise
  it belongs as a line in the handoff/h-mad editing guidance rather than its own skill.
  — **LANDED 2026-08-25** as a line in `h-mad/SKILL.md` §"Editing this skill while a run is in flight", the "handoff/h-mad editing guidance" the row pointed at. Adds one thing the row did not: a deletion count of zero says nothing about WHERE the insertion went, so the numstat check is paired with a grep for the value at its intended anchor. Dogfooded — every doc edit in this batch was verified `N 0` before commit.

## 2026-08-24 — j30-closed-advisor-gate-never-fires

- **hook-routing prover**: prove a PreToolUse hook actually fires before trusting it — instrument the hook to append a marker on entry at **line 1** (above every early-return, or "never entered" and "exited at the override" are the same observation), **self-test the detector** by driving the hook by hand, make one real call, read the marker, revert immediately. — recurrence: 1 (closed J44, which had been carried unverified across three handoffs) — candidate: maybe — the technique generalises to any hook whose default verdict is *allow*, because there a hook that never runs and a hook that correctly permits are byte-identical. Too few occurrences to promote yet, but the shape is worth keeping: the mid-session instrumentation is only possible because a hook FILE is re-read at every invocation. **Corrected 2026-08-24:** this row originally added "even though its registration is snapshotted at session start" — that half is FALSE on 2.1.241. A `PostToolUse` registration added to `settings.json` mid-session fired ~13 min later in the SAME session (throttle stamp keyed by the live session id, budget read from the live transcript). So registration is re-read too, and the prover can verify a hook it just wired without a relaunch — which is strictly better for this row, not worse.
  — **DECLINED 2026-08-25 (triage: not useful)** — filed against J44, which is CLOSED: `advisor` is a `server_tool_use` and no tool-scoped hook can attach. The transcript-counting technique is recorded in the taxonomy. One occurrence, and the occurrence is resolved.

- **clean-measurement worktree**: when the checkout is shared with a live sibling session, measure your own change in a throwaway worktree — `git worktree add --detach /tmp/check HEAD`, copy in only your files, run the suite there, `git worktree remove --force`. — recurrence: 2 (used twice this session: once to prove 10 failures were another session's mid-edit state, once to get a trustworthy full-suite number for my own change) — candidate: maybe — three lines of shell, so the automation win is small; the *rule* is the valuable part and it has already landed in the auto-memory taxonomy as mode 23. Revisit if Orca multi-agent-on-one-worktree keeps producing this.
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — three lines of shell, already in the taxonomy as mode 23 and used twice this session. The rule is the artifact.

## 2026-08-24 — registry-zero-j44-j49

- **post-edit identifier sweep** *(new)*: after the LAST edit of a rename/removal, re-grep the old
  identifier across every surface (code · comments · docs prose · tests · mutation-spec anchors ·
  paired reference files) and require each remaining hit to be an intentional explanation, not a
  leftover — recurrence: 3 this session (the `h-mad-advisor-gate.sh` → `-warn.sh` rename, the
  `.tmp`+`mv` advice removal, the J49 wire) — candidate: yes — **it failed once out of three and
  that is the whole argument.** I noted mid-work that two context-budget docstrings still named the
  deleted gate, went to the docs pins and the mutation spec, and never came back; `a311385` shipped
  three stale references to a file it deletes, fixed a commit later in `291a84a`. The sweep is
  reliable only when it runs AFTER the last edit rather than during, which is exactly the property
  a tool enforces and a human does not. The mechanical part is the grep-and-classify loop plus a
  hit-list diffed against an allowlist of files that legitimately explain the old name (the new
  script's header, its test's docstring); the judgement it must NOT automate is deciding whether a
  given hit is explanation or leftover. Note the mutation-spec anchors are the surface most often
  missed — they are exact-string finds against source, so a rename silently turns them into
  `REFUSED`, which measures nothing and reads like progress.
  — **LANDED 2026-08-26 (`08f383c`)** — `h-mad/scripts/h_mad_identifier_sweep.py`. Classifies every remaining hit by surface (code · comment · doc · test · mutation-anchor) and diffs against an `--allow` list. The judgement the row insists on keeping is kept: `LEFTOVERS` means *still names the old thing*, never *wrong*, and the allowlist is an input rather than inferred. Two defects that only the first LIVE run showed — 14 of 26 hits were `.bkit` machine log and 5 more were handoff/archive records, together outnumbering the 4 actionable ones; and the excerpt truncated from the line START, so on a 900-character JSON line it did not contain the identifier being swept for. Both fixed and pinned. The overlap the row flags is resolved in practice: the anchor precheck covers mutation-spec anchors mechanically, this covers prose and cross-references, and neither subsumes the other.

- **wrong-attachment-point detector** *(new, speculative)*: before trusting any hook, prove the
  harness routes the event to it at all — for a tool hook, count block TYPES in the session JSONL
  (`tool_use` vs `server_tool_use` vs `mcp_tool_use`) rather than instrumenting the hook —
  recurrence: 1 (J44) — candidate: maybe — this is the cheaper half of the existing
  `hook-routing prover` row above and probably belongs merged into it rather than standing alone.
  It needs no instrumentation, no relaunch, and no billed call: the transcript already records
  which dispatch path every tool took, so "no tool-scoped hook can attach to this" is one count
  away. Filed separately only so the *transcript-counting* technique is findable; merge on the next
  reconcile if no second occurrence appears.
  — **SUPERSEDED 2026-08-25: merged into the `hook-routing prover` row above, as this row's own text asked.** No second occurrence appeared, and the transcript-counting technique is the cheaper half of that row rather than a separate candidate — it needs no instrumentation, no relaunch and no billed call, because the transcript already records which dispatch path every tool took.

## 2026-08-25 — portable-timeout-run-verb

- **frozen-tree guard for in-flight verifications** *(new)*: while a background test run is measuring
  the working tree, refuse (or loudly warn on) an `Edit`/`Write` to any file that run covers — the
  pass count it eventually prints describes bytes that no longer exist — recurrence: 1 — candidate:
  maybe — caught by hand this session (a `set -e` cleanup landed in `hmad-dispatch.sh` while a full
  suite ran against it; the run was killed and re-run on final bytes for the 1730/0 actually
  reported). Filed `maybe` on recurrence 1, but the failure is **silent and self-inflicted**: unlike
  the sibling-session case, no "is anyone else in this checkout" check can see it, and the artifact
  is a green you can quote and cannot defend. Mechanically cheap — a `PreToolUse` hook comparing the
  edit path against the paths of any live background `pytest`. Promote on a second occurrence, or
  fold into the existing verification-hygiene rules if a home already exists.
  — **RE-CHECKED 2026-08-26: no fresh recurrence, deliberately.** Six full-suite runs this session, every
  one in the FOREGROUND with no edits in flight, so the guard had nothing to catch. That is the row's own
  mitigation working rather than evidence against it: the failure is silent and self-inflicted, and the
  only reason it did not recur is that the suite was never backgrounded. Stays recurrence 1. Note the
  shape it would need — a `PreToolUse` hook on `Edit`/`Write`, not a script — since nothing the wrapper
  offers can observe an edit as it happens.

## 2026-08-25 — timeout-premise-and-audit-cycle-dispatch

- **controlled A/B dispatch harness**: build two prompts differing in exactly ONE variable, dispatch both through `hmad-dispatch exec`, then diff an observable that is not the exit code — used twice this session (context-budget advisory with `HMAD_CONTEXT_WINDOW`; time-bound rule present vs absent) and it is what turned "the rule is present" into "the rule is causally effective". Both times the control was what made the result mean anything. — recurrence: 2 — candidate: yes
  — **LANDED 2026-08-26 (`fd7d114`)** — `h-mad/scripts/h_mad_ab_dispatch.py`. The diff is the easy part; three refusals carry the tool. `UNCONTROLLED` — the arms differ in more than the declared variable (or in nothing at all), which is the mistake a hand-run A/B actually makes and is silent: the run completes, the numbers differ, and the difference is attributed to the wrong cause. It is checked by re-deriving the template from each BUILT arm, so a value smuggling the placeholder is caught however the pair was constructed, and nothing is dispatched. `INCONCLUSIVE` — an arm produced no log or the observable never matched, because two silent arms compare equal and `SAME` is the most believable lie available. And the exit code is reported but never scored: a dispatch killed by its parent shell, a skipped test and a clean run all exit 0, and this repo has been fooled by each. `SAME` remains a finding in its own right — the rule is present and not causally effective.
- **mutation re-baseline guard**: assert the suite is GREEN before applying each mutant and re-assert after reverting, so a "KILLED" can never be credited to a mutant that changed nothing — recurrence: 4 (four mutation rounds this session, one of which produced a worthless kill on a red baseline) — candidate: maybe (may belong inside `h_mad_mutation_harness.py` rather than as a new skill; see the **mutation-mechanism verifier** row above)
  — **LANDED 2026-08-25.** When a mutation names a `test`, that test is required GREEN before the mutant is applied; a red pin is REFUSED rather than scored, because a kill credited to an already-failing pin measures nothing. This is strictly narrower than the row asked and deliberately so: the whole-suite baseline before the run and the re-run after restore already existed, and what neither could see was a SINGLE pin that was red while the suite was green — which is the case that produced the worthless kill. Per-mutant full-suite re-runs were not added; the cost is real and the end-of-run re-check already proves the restore.
- **dispatch-log improvisation scanner**: scan a dispatch's tool-call command fields for a forbidden command form (e.g. a bare `timeout <n>`) and report it beside the verdict — recurrence: 2 (written ad hoc for the task-#4 A/B, then again to sweep every log this session) — candidate: **DECLINED** — evaluated in depth on 2026-08-25 and rejected for h-mad: codex's `--log` is a plain-text transcript (its arg build carries no `--json`) that also contains the prompt, so the scan false-positives on quoted text and any fail-loud parse guard fires on every codex dispatch; base rate was 30 real dispatched commands with zero improvisations. Shipped one documentation line instead (`2f50bff`). Recorded here so it is not re-proposed without that counter-evidence.

## 2026-08-25 — candidate-batch review sweep

- **task-slicer heading awareness** *(new, from an adversarial review of `h_mad_assemble_tdd.py`)*: the impl-plan task slicer bounds a task on the NEXT task header only, so (a) the last task swallows every trailing section — `## Dependencies`, `## Glossary` — and ships it to the agent as task scope, and (b) a `## Task N` line inside a fenced code block truncates the slice early. Both are the same missing awareness: heading LEVEL and fence state. The version-history helper already learned the fence half the same day (`section_bounds` tracks ``` blocks) so the technique is in the repo — recurrence: 1 — candidate: yes — deferred deliberately rather than half-fixed: the fix wants the same treatment as `section_bounds` plus a stop at any equal-or-higher heading, and both need corpus measurement first (how many real impl-plans have trailing sections after their last task, and how many carry a fenced task header). The review's other four findings on that file were fixed the same day.
  — **LANDED 2026-08-26 (`6c34e60`)** — and the corpus measurement the row demanded came first: **19 of 20 impl-plans** carry a section after their last task, **746 lines** in total, up to 257 in a single plan. The content is not merely noise — `## Verification (all tasks)` and `## Task dependency graph` describe the whole feature and were being attributed to one task's prompt. `task_body()` now bounds on the next task OR the first equal-or-higher heading, keeping deeper sub-headings (the property the original bound existed to protect) and tracking fences, since impl-plans are full of shell blocks whose comments start at column 0. Re-measured after: 746 lines gone and all 95 task bodies in the corpus still slice to something substantive — the accept direction, which mutation testing cannot show. The fenced-task-header half of the row is covered by the same fence tracking.
- **non-J finding rows carry no machine-readable status**: `docs/skill-monitoring.md` holds 46 `J` entries governed by its own `Status:` lifecycle AND 33 further bullet rows with other prefixes (F 18, G 6, H 5, A 2, V 1, P 1) that carry no status line at all. They are per-review finding rows rather than the standing registry, so counting them as open work would be wrong — but nothing says whether any of them is still live. The census now REPORTS them (`parsed=46 row-shaped=79`) instead of filtering them out of its own denominator — recurrence: 1 — candidate: maybe — the question is editorial, not mechanical: decide whether these rows are historical (fold them under their review's heading and say so) or trackable (give them the `Status:` contract). Do not answer it by widening the parser, which would silently reclassify 33 rows as open.
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — explicitly editorial: decide whether the 33 F/G/H/A/V/P rows are historical or trackable. The census now REPORTS them, which is the mechanical half; answering it by widening the parser would silently reclassify 33 rows as open.

## 2026-08-25 — candidate-backlog-drain (scout)

- **re-anchor a mutation spec after editing the code it mutates**: every edit to a file a spec targets can silently drift its anchors, and the harness then REFUSES (measures nothing) rather than failing — recurrence: **8 this session** (`version_history` ×2, `mutation_harness` ×2, `assemble_tdd` ×2, `census_registry` ×2) — candidate: yes — the near-miss hints landed this session make recovery cheap, but the *detection* is still "run the spec and read the refusals". Mechanical shape: for every `tests/mutation-specs/*.json`, assert each `find` matches its `file` exactly once, and report the drifted ones with their near-misses — i.e. the harness's own precheck, run over ALL specs without applying anything. Would have caught six of this session's eight before a run. Note the overlap with `post-edit identifier sweep`, which is the same failure on a different surface; build one and check whether it subsumes the other rather than shipping two greps.
  — **LANDED 2026-08-26 (`e0dd87b`)** — `h_mad_mutation_harness.py --check-anchors <spec>…`. Applies nothing and runs no tests, so it costs file reads instead of a suite per spec. The one-match rule is extracted into `anchor_status()` and shared with `run_spec`, so the cheap check and the expensive one cannot disagree — a precheck carrying its own `count(...) != 1` would be a second copy of the exact rule this harness enforces. First sweep over the 14 committed specs: **7 of 177 anchors had drifted**, and every one of those guards was unverified while its spec still printed a verdict-shaped line; two of the seven were broken by a refactor made minutes earlier in the same session. It then caught a drift caused by my own edit three hours later, before the run could report REFUSED. The subsumption question is answered NO — see the identifier-sweep row.
- **build mutation-spec anchors FROM the file, never by hand-escaping them**: three separate spec edits this session produced anchors that matched 0 times purely from backslash levels in a heredoc, one of which (`\\bJ\\d+\\b`) produced a mutant that could never match and therefore reported as a survivor — a *broken* mutant is indistinguishable from a real coverage gap — recurrence: 3 — candidate: maybe — it is a technique, not a tool: read the target file, locate the literal line, and use that string as the anchor. Possibly a line in `invariants.base.md` §"Mutation verification" beside the shared-anchor recipe rather than anything executable.
- **probe a tool with its simplest invocation before declaring it broken**: two failed `exec agy` dispatches were read as "agy is down" and recorded as such in a commit body and a candidate row; a one-line ping refuted it immediately — recurrence: 1 — candidate: maybe — one occurrence, but it cost five features shipping without review. The durable half is already in the taxonomy as mode 30; a rule would live in `invariants.base.md` §"Assumption verification" beside the controlled-pair line, which is the same discipline pointed at a tool rather than a cause.
