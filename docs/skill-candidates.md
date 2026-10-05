# Skill Candidates

Appended by the `/handoff` automation scout, newest session last. **Status is only useful if it is
current** — reconcile a row when the thing it describes ships, the same way `docs/skill-monitoring.md`
rows are flipped.

**Verdicts:** `yes` / `maybe` / `no` (scout's initial call) · `LANDED` (shipped — name where) ·
`SUPERSEDED` (a different fix removed the need) · `DECLINED` (deliberately not doing it, with the
reason) · `done` (legacy spelling of LANDED).

**Decision of 2026-08-26 — `DECLINED` STAYS overloaded, and the bucket is now machine-readable.**
A fourth vocabulary word was considered and rejected: it would cost a rewrite of all 22 existing
`DECLINED` rows and lose the reasoning each one already carries, to fix an ambiguity that 20 of them
had already resolved in prose. Instead every `DECLINED` marker names its bucket inline —
`(triage: useful, not codable)` or `(triage: not useful)` — the three stragglers were qualified, and
`skill_candidates_census.py` now prints the split with `unqualified` as its own number so a bare
marker cannot hide inside a bucket it was never sorted into. Current split: **27 useful-not-codable,
8 not-useful, 0 unqualified**, pinned by a test against this file rather than a fixture. Re-run the
census for the live numbers rather than citing this line — it has been stale before.

**Triage of 2026-09-01 — every OPEN row sorted, and the open backlog is now 7.** All 20 rows that
were `yes`/`maybe` were read in full and put in one of the three buckets. Twelve are useful but not
codable (the row's own text usually said so: a doctrine line, a one-off git incantation, or a check
whose mechanical half already runs unconditionally) and one is not useful (the live-e2e verb sweep,
measured out of existence: 42 of 46 verbs are not unattendedly sweepable and the remaining 4 are one
shell loop that found no drift). Each carries its bucket and its reason inline. The seven left open
are the ones with a named, mechanical implementation: `632` frozen-tree guard, `744` resolved-model,
`773` pane ID by `terminal read`, `848` outbound-handover verify, `860` response-shape census, `914`
live-run check before merging a shared skill, `925` section-bounded slicing. Nothing was deleted —
a DECLINED row keeps the reasoning that a deletion would throw away.

**Reconcile of 2026-09-02 — the open backlog was 3 at reconcile time, not the 7 the line above names; this same scout then appended 3 new rows, so the live count is 6.** Four of that
seven closed between the triage and this scout; the census is the number that moved, not this prose,
which is why the count is re-run rather than cited. `skill_candidates_census.py` reads
`candidates=150 OPEN(yes+maybe)=3  LANDED=71  DECLINED=35  no=33  SUPERSEDED=7` (+5 bump rows
excluded, coverage 155/155). The three still open, each **re-verified against source in this pass**
rather than against its own label: `frozen-tree guard` (no `PreToolUse` hook exists —
`h-mad/hooks/` holds only `h-mad-advisor-warn.sh` and `h-mad-tdd-gate.sh`), `positive pane ID via
terminal read` (prerequisite still holds — `_resolve_target` at `hmad-dispatch.sh:281-303` accepts
only `codex|agy` and returns 2 on anything else, so no verb addresses a raw handle; and
`_agent_tail_re` is absent from the wrapper, i.e. the feature that would close this row is
`pin-agents-tail-banner`, still at Phase 5 on `feature/pin-agents-tail-banner`), and
`check for a live run before merging a shared skill change` (nothing reads `worktree-ps` comments
against `.h-mad/telemetry.jsonl`; `h_mad_telemetry.py` is the only consumer and it writes).

**Reconcile of 2026-09-07 — the first pass after FOUR consecutive skipped scouts; all 21 open `yes`
rows re-verified against source, 4 closed.** The open backlog had grown from the 3 the line above
records to **21 `yes` / 15 `maybe` of 193** while nobody ran the scout. Every `yes` row was probed at
HEAD `8ade1e9` against the file, never against its own label and never against the task list or a
commit message; the census now reads `candidates=193 OPEN(yes+maybe)=32 yes=17 maybe=15 LANDED=81
DECLINED=36 no=36 SUPERSEDED=7` (+6 bump rows excluded, coverage 199/199). **Four flipped to
LANDED** — `collect-report` marker near-miss, `carry-forward-sources`, the unscorable-report refusal,
and the reopen value-sweep. **Five carry a new distinction and stay open**: the RULE landed and the
MECHANISM the row actually asked for did not (suffixed re-dispatch paths, freeze closure predicates,
`expect 0` screens at the freeze sha, the measured-value lint, the detector-calibration shape). The
`2718d48` / `ce9ffe1` batches closed a dozen `#49x` items *as doctrine*, which is not the same thing
as closing the row that asked for a verb — reading a rule's arrival as a row's completion is how this
backlog would have shrunk on paper without a single check being built. The remaining twelve were
confirmed absent by probing the tree. One measurement note for the next reader: the first probe pass
of this reconciliation grepped `h-mad/bin/hmad-dispatch.sh` — the script is under `scripts/` — and a
wrong-path zero reads exactly like "already landed".

**Reconcile of 2026-09-07 evening — a SAME-DAY re-check, and the finding is that a same-day label is
not a current one.** The morning pass above ran at `d61dd93` **08:30**; twenty of that session's
twenty-one commits landed after it, through **19:31**. So every `RE-CHECKED 2026-09-07` note in this
file was written before the day's work existed, and one of them had already gone stale by nine hours:
`a delta-self-review verb` was re-checked "still open" at 08:30 and `e7b97db` shipped its mechanical
half at **17:51**. **The generalisable trap is that a date is not a timestamp** — a row stamped with
today's date reads as current to the next reader and to a `grep` for the date, and there is no signal
that the tree moved twenty commits underneath it. **Every `RE-CHECKED 2026-09-07` note in this file
has been restamped `08:30`** — all 17 came from `d61dd93`, verified by counting them in that commit —
so no re-check here carries a bare date any more, and none should again.
All 19 open `yes` rows were re-probed against the tree at `5a6ad11`: **18 confirmed still open**,
**one changed status in part** (see that row). The 18, each named so this count carries its evidence
rather than asking to be believed — eleven probed as ABSENT: `h_mad_ac_census.py` and any `ACS:`
token (R8); a `probe)` arm in `hmad-dispatch.sh` (R13); a lockfile or `MUTATION: BUSY` in the
mutation harness (R18); `Node` in `h_mad_assemble_tdd.py` (R5); markdown spec discovery — the harness
still globs `*.json` at `:470` and `git-hooks/pre-push` greps no markdown (R2); the live-shape rule in
`SKILL.md`/`invariants.base.md`/`references/` (R7); a `--verify` body-grep in `h_mad_version_history.py`,
whose only `verify` hit is `--dry-run`'s help text (R4); the live-run check against `worktree-ps` +
telemetry (R1); a RED-suite-vs-unmodified-tree diff (R3); an in-situ `*_guard` run of a prescribed
block (R6); `git cat-file -t` anywhere under `h-mad/` or `handoff/` (R10); an executed `expect 0`
screen (R17). **Four more returned grep hits that are incidental substrings, not the mechanism, and
are recorded here because a bare PRESENT would have closed them wrongly**: R9's `measured at` hits are
the PINDRIFT comments the row already counts as its partial; R12's `margin` hits are
`h_mad_context_budget.py`'s advisor ceiling plus prose at `test_h_mad_assemble_audit.py:299`; R15's
`suffix` hits are the `⟦/h-mad⟧` verdict-marker splitting at `hmad-dispatch.sh:2227-2240`, not a
report-path suffixer; R16's `freeze` hits are the Phase-5 substrate handle pin at `:900`/`:965`. The
remaining one is R11, whose noise-floor test exists for a single detector exactly as its label says.
Two adjacency notes, recorded so the next reader does not read them as closures: `h_mad_adoption_check.py`
(#11/H5) checks shared SENTENCES across sibling documents and is **not** the live-run check that
`check for a live run before merging a shared skill change` asks for; and `#142`'s parked-mutation-spec
gate in `h_mad_phase7_preconditions.py` is a *precondition* on one spec, **not** the completeness
check `a closure check that the archive is COMPLETE` asks for (that row's incident was 6 of 641 files
moved by copy). **The census read `candidates=196 OPEN(yes+maybe)=35 yes=19 maybe=16 LANDED=81
DECLINED=36 no=36 SUPERSEDED=7 done=1` at reconcile time (coverage 202/202); this same scout then
appended 5 new rows, so the live count is `candidates=201 OPEN=40 yes=23 maybe=17`** (coverage
207/207) — stated both ways because the reconcile number and the post-append number are different
questions and a reader who cites the wrong one is off by five. Note the open count ROSE 32 → 35 before
the append: the day closed nothing and opened three, which is the honest shape of a session that
shipped five gates and found six more gaps. **One defect found in this pass by the census rather than
by reading**: the note on `a delta-self-review verb` was first written as `**SUPERSEDED IN PART**`,
and `TERM` matches a terminal marker ANYWHERE in a row — so a note whose own words said "stays open"
moved the row into the closed set (`SUPERSEDED` 7→8, `yes` 22 not 23). Prose qualifying a terminal
marker does not reach the parser. Never put `LANDED`/`SUPERSEDED`/`DECLINED` in bold in a row you mean
to leave open, and re-run the census after editing a row — the delta in the counts is the check. **A hand-parse of this
file was attempted three times the same day and disagreed with itself every time** (51 flat
occurrences / 45 in-row / 44 rows; open reading 16 or 18 depending only on whether the terminal marker
must be bold) — all three were wrong, the census reads 19. Ask the census.

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

**Superseded by the 2026-09-01 triage above** (this line read `OPEN yes+maybe = 35 of 104`; it was stale). The newest is
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



**Reconcile of 2026-10-03/04 — every open row re-probed against HEAD, and only one had shipped.** Five
read-only agents probed all 50 open rows with evidence (commit sha, path:line, or the empty probe
command); each row now carries a dated `RE-PROBED 2026-10-03` note naming what remains. Result:
1 LANDED (`positive pane ID via terminal read`), 15 PARTIAL, 34 OPEN — census OPEN 50 to 49. None of
the four fixes shipped on 2026-10-04 (`25855d08`, `a1bd6a84`, `2a0cc74d`, `ffd72e4e`) closes a row
here; they came from handoff carry-forward, not from this file. Re-run the census for live numbers.
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
  — **DECLINED 2026-09-01 (triage: not useful)** — the candidate here is the sweep TOOL, and it was
  measured out of existence: 42 of the 46 verbs either mutate state or cost a real dispatch, so only
  4 are unattendedly sweepable, and sweeping those four is one shell loop that found no drift. The
  measurement is the durable part and it is already in this row; there is nothing left to build. The
  budgeted live session the other 42 would need is a decision, not a script.

## 2026-07-22 — orca-agent-resolution-hardening

- **h-mad audit-prompt assembler**: hand-wrote assemble_audit/design/implplan.py in scratchpad 3× this session to splice INLINE_* slots into audit-prompt.template.md — a bundled `scripts/h_mad_assemble_audit.py <phase>` would DRY it into the skill — recurrence: 3 — candidate: **LANDED** 2026-07-22 (`3f8ae83`) — `h-mad/scripts/h_mad_assemble_audit.py`. Duplicate of the `done` row in the next session block; kept for provenance.
- **launch+pin agent bootstrap**: `hmad-dispatch launch/pin` then verify resolve — recurrence: 2 — candidate: no (already a verb)

## 2026-07-22 — audit-assembler-agent-resolution

- **h-mad audit-prompt assembler**: SHIPPED this session as `h-mad/scripts/h_mad_assemble_audit.py` — closes the 2026-07-22 orca-agent-resolution-hardening candidate (recurrence was 3) — recurrence: 4 — candidate: done
- **staged-prompt repair sweep**: script that rewrites every `/tmp/audit_*.txt` to what the current template would emit (strip note, resolve markers, de-dupe rubrics), with backups + a freshness guard skipping in-flight prompts — recurrence: 2 — candidate: **DECLINED** (triage: not useful) (Wave 4b, 2026-07-23). Every staged prompt on disk belongs to one feature that shipped 2026-07-22; `/tmp` is scratch, and `h_mad_assemble_audit.py` regenerates any prompt in a single call. A sweep would carry backup and in-flight-freshness logic to repair files nothing will read again. Revisit only if a live run is ever blocked by a stale staged prompt.
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
  — **DECLINED 2026-08-25 (triage: not useful): the prescription is inverted and would have written a FALSE rule.** The row asked for "a SKILL.md note that `exec agy` audits use the sentinel scrape not report-file". SKILL.md already says the opposite, deliberately: §"Exception — `exec agy` on an audit phase: fill the report-file slot", because on an audit the report IS the deliverable and `agy --print` surfaces only the last message, so the scrape is one fragile channel. And the two are not alternatives — 266,342 B was confirmed answered 8 of 8 on 2026-08-22 with **every run honouring both the report-file slot and the sentinel pair**. The row's recurrence (20+) was real; its facts about what those runs did were not. A three-part failure: the observation was true, the concern was empty, the prescription was harmful.
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
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — the check is `pytest
  ~/.claude/skills/<skill>/tests/` — a path, not a tool. The re-check also narrowed it: under a
  SYMLINK install the checkout and the install path are the same inode, so the content-equality
  blindness cannot arise at all and the row needs a COPY install to have a subject. Recurrence 1,
  and the durable half is already a learning.
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
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — the mechanical half (`git rev-list
  --left-right --count @{u}...HEAD` before a push) is already run unconditionally every time and
  needs no tool; the half that saved the 1519-commit rebase was the JUDGEMENT to build in a
  throwaway worktree off `origin/main` instead of rebasing a dirty tree. No fresh recurrence across
  six pushes since.

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
  — **LANDED 2026-10-05** — reshaped from a refusing hook into a REPORT, because the editor in the recorded cases was a codex implementer or the harness itself, neither of which makes an `Edit` call. A pytest session that collects `h-mad/tests` digests the non-ignored tree (HEAD plus a hash of every path `git status -uall` lists) at start and end, and prints `SUITE: TREE_MOVED paths=… n=K` when they differ. It never blocks an edit, is quiet on ignored writes and on pytest/bytecode churn, and cannot see an edit reverted before the run ends (pinned by `test_edit_then_revert_is_not_reported`). The harness's `TREE_MOVED` now compares the same digest, not only HEAD (`tree_digest`/`moved_paths` in `h_mad_mutation_harness.py`, hooks in `h-mad/tests/conftest.py`). `test_h_mad_suite_tree_digest.py` 6 tests; spec `suite_tree_digest.json` ALL_CAUGHT 4/4.
  — **TRIAGED 2026-09-01: useful and codable — stays open.** a `PreToolUse` hook comparing the edit
  path against the paths of any live background `pytest` is mechanical, has a working precedent in
  `h-mad-tdd-gate.sh`, and the failure it catches is silent, self-inflicted, and produces a green
  you can quote and cannot defend.
  — **RE-CHECKED 2026-09-02 (scout): still open, no fresh recurrence.** Verified against source, not
  the label: `h-mad/hooks/` holds `h-mad-advisor-warn.sh` and `h-mad-tdd-gate.sh` and nothing else,
  and no hook compares an edit path against a live background `pytest`. Stays recurrence 1 — the
  2026-09-01 session ran its suites in the foreground, so again the guard had nothing to catch.
  — **RE-PROBED 2026-10-03: OPEN** — no hook compares an edit path with a live background pytest; `h-mad/hooks/` holds only the TDD gates, advisor-warn and memory-index guard. `4affd9e0` is the end-of-session leak reaper, not an edit guard.

## 2026-08-25 — timeout-premise-and-audit-cycle-dispatch

- **controlled A/B dispatch harness**: build two prompts differing in exactly ONE variable, dispatch both through `hmad-dispatch exec`, then diff an observable that is not the exit code — used twice this session (context-budget advisory with `HMAD_CONTEXT_WINDOW`; time-bound rule present vs absent) and it is what turned "the rule is present" into "the rule is causally effective". Both times the control was what made the result mean anything. — recurrence: 2 — candidate: yes
  — **LANDED 2026-08-26 (`fd7d114`)** — `h-mad/scripts/h_mad_ab_dispatch.py`. The diff is the easy part; three refusals carry the tool. `UNCONTROLLED` — the arms differ in more than the declared variable (or in nothing at all), which is the mistake a hand-run A/B actually makes and is silent: the run completes, the numbers differ, and the difference is attributed to the wrong cause. It is checked by re-deriving the template from each BUILT arm, so a value smuggling the placeholder is caught however the pair was constructed, and nothing is dispatched. `INCONCLUSIVE` — an arm produced no log or the observable never matched, because two silent arms compare equal and `SAME` is the most believable lie available. And the exit code is reported but never scored: a dispatch killed by its parent shell, a skipped test and a clean run all exit 0, and this repo has been fooled by each. `SAME` remains a finding in its own right — the rule is present and not causally effective.
- **mutation re-baseline guard**: assert the suite is GREEN before applying each mutant and re-assert after reverting, so a "KILLED" can never be credited to a mutant that changed nothing — recurrence: 4 (four mutation rounds this session, one of which produced a worthless kill on a red baseline) — candidate: maybe (may belong inside `h_mad_mutation_harness.py` rather than as a new skill; see the **mutation-mechanism verifier** row above)
  — **LANDED 2026-08-25.** When a mutation names a `test`, that test is required GREEN before the mutant is applied; a red pin is REFUSED rather than scored, because a kill credited to an already-failing pin measures nothing. This is strictly narrower than the row asked and deliberately so: the whole-suite baseline before the run and the re-run after restore already existed, and what neither could see was a SINGLE pin that was red while the suite was green — which is the case that produced the worthless kill. Per-mutant full-suite re-runs were not added; the cost is real and the end-of-run re-check already proves the restore.
- **dispatch-log improvisation scanner**: scan a dispatch's tool-call command fields for a forbidden command form (e.g. a bare `timeout <n>`) and report it beside the verdict — recurrence: 2 (written ad hoc for the task-#4 A/B, then again to sweep every log this session) — candidate: **DECLINED** (triage: not useful) — evaluated in depth on 2026-08-25 and rejected for h-mad: codex's `--log` is a plain-text transcript (its arg build carries no `--json`) that also contains the prompt, so the scan false-positives on quoted text and any fail-loud parse guard fires on every codex dispatch; base rate was 30 real dispatched commands with zero improvisations. Shipped one documentation line instead (`2f50bff`). Recorded here so it is not re-proposed without that counter-evidence.

## 2026-08-25 — candidate-batch review sweep

- **task-slicer heading awareness** *(new, from an adversarial review of `h_mad_assemble_tdd.py`)*: the impl-plan task slicer bounds a task on the NEXT task header only, so (a) the last task swallows every trailing section — `## Dependencies`, `## Glossary` — and ships it to the agent as task scope, and (b) a `## Task N` line inside a fenced code block truncates the slice early. Both are the same missing awareness: heading LEVEL and fence state. The version-history helper already learned the fence half the same day (`section_bounds` tracks ``` blocks) so the technique is in the repo — recurrence: 1 — candidate: yes — deferred deliberately rather than half-fixed: the fix wants the same treatment as `section_bounds` plus a stop at any equal-or-higher heading, and both need corpus measurement first (how many real impl-plans have trailing sections after their last task, and how many carry a fenced task header). The review's other four findings on that file were fixed the same day.
  — **LANDED 2026-08-26 (`6c34e60`)** — and the corpus measurement the row demanded came first: **19 of 20 impl-plans** carry a section after their last task, **746 lines** in total, up to 257 in a single plan. The content is not merely noise — `## Verification (all tasks)` and `## Task dependency graph` describe the whole feature and were being attributed to one task's prompt. `task_body()` now bounds on the next task OR the first equal-or-higher heading, keeping deeper sub-headings (the property the original bound existed to protect) and tracking fences, since impl-plans are full of shell blocks whose comments start at column 0. Re-measured after: 746 lines gone and all 95 task bodies in the corpus still slice to something substantive — the accept direction, which mutation testing cannot show. The fenced-task-header half of the row is covered by the same fence tracking.
- **non-J finding rows carry no machine-readable status**: `docs/skill-monitoring.md` holds 46 `J` entries governed by its own `Status:` lifecycle AND 33 further bullet rows with other prefixes (F 18, G 6, H 5, A 2, V 1, P 1) that carry no status line at all. They are per-review finding rows rather than the standing registry, so counting them as open work would be wrong — but nothing says whether any of them is still live. The census now REPORTS them (`parsed=46 row-shaped=79`) instead of filtering them out of its own denominator — recurrence: 1 — candidate: maybe — the question is editorial, not mechanical: decide whether these rows are historical (fold them under their review's heading and say so) or trackable (give them the `Status:` contract). Do not answer it by widening the parser, which would silently reclassify 33 rows as open.
  — **DECLINED 2026-08-25 (triage: useful, not codable)** — explicitly editorial: decide whether the 33 F/G/H/A/V/P rows are historical or trackable. — **DECIDED 2026-08-26: HISTORICAL.** All 33 were read. None is live open work: `F1`-`F13` have their own FIXED table in the same file ("All F1-F13 resolved"), `F14`-`F18`/`G`/`H`/`A` record resolution inline, `G5`/`H5`/`V1` are a mechanism note, a root-cause explanation and a verification record rather than work, and `P1` was explicitly declined as pre-existing. Two things that had already misled a reader are now stated in `skill-monitoring.md`'s own header: the emoji is SEVERITY at filing and never lifecycle (`F11`-`F13` are 🔴 *and* FIXED, appearing once in the table and again as bullets), and tracking something means promoting it to a `J` entry. The census now NAMES the coverage gap instead of printing a bare `33 ROW-SHAPED LINES NOT PARSED`, which read as a defect and invited exactly the parser-widening this row warns against. Pinned by three tests against the real file. The census now REPORTS them, which is the mechanical half; answering it by widening the parser would silently reclassify 33 rows as open.

## 2026-08-25 — candidate-backlog-drain (scout)

- **re-anchor a mutation spec after editing the code it mutates**: every edit to a file a spec targets can silently drift its anchors, and the harness then REFUSES (measures nothing) rather than failing — recurrence: **8 this session** (`version_history` ×2, `mutation_harness` ×2, `assemble_tdd` ×2, `census_registry` ×2) — candidate: yes — the near-miss hints landed this session make recovery cheap, but the *detection* is still "run the spec and read the refusals". Mechanical shape: for every `tests/mutation-specs/*.json`, assert each `find` matches its `file` exactly once, and report the drifted ones with their near-misses — i.e. the harness's own precheck, run over ALL specs without applying anything. Would have caught six of this session's eight before a run. Note the overlap with `post-edit identifier sweep`, which is the same failure on a different surface; build one and check whether it subsumes the other rather than shipping two greps.
  — **LANDED 2026-08-26 (`e0dd87b`)** — `h_mad_mutation_harness.py --check-anchors <spec>…`. Applies nothing and runs no tests, so it costs file reads instead of a suite per spec. The one-match rule is extracted into `anchor_status()` and shared with `run_spec`, so the cheap check and the expensive one cannot disagree — a precheck carrying its own `count(...) != 1` would be a second copy of the exact rule this harness enforces. First sweep over the 14 committed specs: **7 of 177 anchors had drifted**, and every one of those guards was unverified while its spec still printed a verdict-shaped line; two of the seven were broken by a refactor made minutes earlier in the same session. It then caught a drift caused by my own edit three hours later, before the run could report REFUSED. The subsumption question is answered NO — see the identifier-sweep row.
  — **PUSH BOUNDARY CLOSED 2026-08-27** — the LANDED note above conceded the remaining half: "the *detection* is still 'run the spec and read the refusals'". `git-hooks/pre-push` + `git-hooks/install.sh` make the sweep an obligation of `git push`, which is the boundary an ordinary refactor commit actually crosses — 5e's precheck and `--check-anchors` both require someone to be running a mutation. Specs are **discovered** (`git ls-files -- '*.json'`, classified by the harness) rather than named by a configured directory: measured here, the 19 specs sit in **three** directories, one inside an unrelated skill, so the obvious single-directory parameter would have guarded 16 of 19 and reported success. Only `ANCHORS_DRIFTED` blocks; a missing harness, `ANCHORS_NOTHING_SWEPT`, and a missing verdict line each warn and ALLOW. 14/14 mutants caught; a 15th was removed as **equivalent** and the reason recorded in the spec, since an equivalent mutant reports identically to a real coverage gap.
- **build mutation-spec anchors FROM the file, never by hand-escaping them**: three separate spec edits this session produced anchors that matched 0 times purely from backslash levels in a heredoc, one of which (`\\bJ\\d+\\b`) produced a mutant that could never match and therefore reported as a survivor — a *broken* mutant is indistinguishable from a real coverage gap — recurrence: 3 — candidate: maybe — it is a technique, not a tool: read the target file, locate the literal line, and use that string as the anchor. Possibly a line in `invariants.base.md` §"Mutation verification" beside the shared-anchor recipe rather than anything executable.
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — the row says it plainly: read the target
  file and use the literal line as the anchor. A tool cannot know which line you meant, and the
  failure it prevents (a mutant that can never match, reported as a survivor) is now covered from
  the other side by `--check-anchors`, which is executable and already exists.
- **probe a tool with its simplest invocation before declaring it broken**: two failed `exec agy` dispatches were read as "agy is down" and recorded as such in a commit body and a candidate row; a one-line ping refuted it immediately — recurrence: 1 — candidate: maybe — one occurrence, but it cost five features shipping without review. The durable half is already in the taxonomy as mode 30; a rule would live in `invariants.base.md` §"Assumption verification" beside the controlled-pair line, which is the same discipline pointed at a tool rather than a cause.
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — a one-line ping before declaring a tool
  down is doctrine, not a program — the durable half is already taxonomy mode 30, and its home is
  `invariants.base.md` §"Assumption verification".

## 2026-08-26 — loop-drain-five-tools (scout)

- **reconcile open rows with the census, never a line grep**: the scout's own reconcile step used
  `grep -nE '^- \*\*.*candidate: \**yes' | grep -v LANDED`, but a row's terminal marker is written on
  the CONTINUATION line beneath it, so the pattern sees `candidate: yes` and never the `LANDED` that
  closed it — recurrence: 2 in one session (the scout step itself, and a throwaway open-row scan I
  wrote minutes earlier that made the identical mistake) — candidate: **LANDED 2026-08-26** —
  `handoff/references/automation-scout.md` now calls `skill_candidates_census.py` as the primary and
  keeps the grep as a re-checked fallback. Measured: the grep returned **7 rows, all 7 already
  terminal** — a 100% false-positive rate against a file the census read correctly as zero open
  `yes`. The general form is worth remembering beyond this file: *a multi-line record cannot be
  classified by a single-line pattern*, and the failure is silent because the pattern still matches
  something real.
- **dogfood a new tool inside a live cycle before closing its row**: five tools shipped this session
  (`--check-anchors`, `h_mad_identifier_sweep.py`, `--gated`/`--verify-stamp`, the task-slicer bound,
  `h_mad_ab_dispatch.py`); every one is unit-tested, mutation-covered and hand-run against this repo,
  and **none has been through a real `/h-mad` phase gate** — recurrence: 5 this session — candidate:
  maybe — this is the existing `dogfood-a-bundled-prompt-live` row's shape rather than a new tool, so
  treat it as a recurrence bump on that row. The specific gap worth naming: `--verify-stamp` is
  documented in `SKILL.md` §Phase-6 step 11 and invoked by nothing, which is a wiring decision left
  open deliberately (the default gate output is byte-identical without `--gated`).
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — the row itself says this is a recurrence
  bump on `dogfood-a-bundled-prompt-live` rather than a new tool. "Run the thing inside a real cycle
  before closing its row" cannot be automated by the thing being tested.
- **pin a doc-lint against the real file, not only a fixture**: a `TRIAGE` regex written from the
  tight form (marker immediately followed by the bucket) matched 2 of 22 rows and reported the other 20 as
  unqualified, because the bucket usually sits after the date and the closing bold; a fixture built
  from that same tight form is green on the bug — recurrence: 2 (this session's DECLINED split, and
  the earlier coverage line that hardcoded `J` in its own denominator) — candidate: maybe — the
  mechanical part is one extra test per doc-lint that runs against the committed document; the
  judgement it must not automate is deciding what the correct count IS. Close to
  `corpus-sweep-before-regex-tighten`, which is the same instinct one step earlier. **Self-pollution note:** the first draft of this very row quoted a bolded terminal marker as an example and the census promptly classified the row as terminal — a row that names a vocabulary word in bold IS that word to every reader of this file. Quote it unbolded.
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — the mechanical part is one extra test per
  doc-lint, which is a convention each lint applies for itself; the part that would need a tool is
  deciding what the correct count IS, which the row explicitly rules out automating.
  `pin_agents_carry` and `read_auto_resolve` both follow it by hand.
- **6a-prime cycle driver (an `audit-cycle` for the ARCHITECTURAL gate)**: `audit-cycle` exists for
  plan/design/impl-plan, but Phase 6a-prime has no equivalent, so this session hand-assembled the
  same seven-step loop **7 times** — rebuild the prompt from
  `agy-architectural-reviewer-prompt.md`, substitute feature/BASE/HEAD/diff-stat/design, append the
  absolute-path reading instructions, re-`sed` the HEAD sha into the tail file, dispatch `exec agy`,
  run `h_mad_review_evidence.py` on the log, then `h_mad_extract_verdict.py --key ASSESSMENT` —
  candidate: yes — every step is already prescribed and mechanical, and the two easiest to skip are
  the ones with no other home: re-stamping the HEAD sha (a stale sha silently reviews the previous
  commit) and the evidence gate (`EVIDENCE: PASS tools=N`, which is what separates a review that
  read from one that only sounds like it did). The judgement it must NOT automate is whether to run
  another cycle — this run went to seven because cycle 3 was clean and cycle 4 then found a Critical
  vacuous pass. Sibling of `archreview-record-and-readback` (DECLINED as not-codable), which covers
  only the close-out; this covers the loop that precedes it.
  — **LANDED 2026-08-28** as `h_mad_archreview_cycle.py` (`stage` + `score`), NOT as an `audit-cycle` variant: that tool is a multi-pass verdict COMBINER over runs that already finished, fans out N parallel passes, and rejects any phase outside plan/design/impl-plan, whereas 6a-prime is ONE reviewer re-run sequentially after fixes emitting a word rather than counts — same name, different machine. **This row's own premise was false:** it calls `archreview-record-and-readback` "DECLINED as not-codable"; that row (L424) reads `candidate: maybe` — deferred pending a third occurrence, not declined — and its actual argument (*"the risk is skipping the read-back, not not knowing it"*) is the strongest case AGAINST building this, since a driver only helps if people run the driver. Built anyway on the counter-evidence that the loop was hand-assembled an 8th time this session precisely because no driver existed. Cheaper than the row estimated: `h_mad_baseline_sha.py` (J41) and `h_mad_review_evidence.py` already existed, so only assembly, gate ordering and the read-back were new. The judgement the row says it must not automate is enforced structurally — no `while` loop, asserted on the AST. 12 tests, 6/6 mutants caught, suite 2270.
- **`hmad-dispatch await <path>` — a bounded wait that is not a sleep ladder**: with foreground
  `sleep` blocked and a 120s tool timeout, waiting on a backgrounded `exec` was written **~25 times**
  this session as `for i in 1 2 3; do hmad-dispatch run --timeout 110 -- sleep 105; done` followed by
  a `test -f <out>` — candidate: yes — `report-wait` already does exactly this for a report path plus
  `.done` marker, so the verb exists and simply does not cover the `exec --out` case. The loop is
  pure friction, it obscures the poll's actual purpose, and getting the arithmetic wrong just wastes
  wall-clock silently. Wants the same contract as `report-wait`: poll a path, bounded by `--timeout`,
  exit non-zero on expiry, and print nothing on success.
  — **LANDED 2026-08-28** as `report-wait <path> --no-done-marker`, NOT as a new `await` verb: `hmad-dispatch await` already exists for an Orca **task id** and is gated on `_require_orca`, so that name would have put two contracts on one word. The row also under-specified the hard part — the poller is only sound because `exec --out` was made **atomic** first (J46): it was written by a `cp` and two `>` redirects, and polling a file that a redirect has just truncated returns a zero-byte or partial verdict that reads exactly like a real one. Built the other way round, this would have been a race with a friendlier interface. The flag is opt-in; defaulting it would silently strip the `.done` contract from every existing caller. Usefulness is real but narrower than the 25× suggests: a harness that notifies on background completion needs no poller at all, so this is for callers that lack one.

## 2026-08-28 — monitoring-backlog-drained (scout)

- **consumer sweep when a verdict token gains a word**: splitting `ANCHORS_UNREADABLE` out of `ANCHORS_DRIFTED` instantly un-guarded the pre-push hook built two hours earlier — it matched only `*ANCHORS_DRIFTED*`, so a deleted target fell to the catch-all and printed "Push ALLOWED" while misreporting a real verdict as broken tooling — recurrence: 1 (severe) — candidate: maybe — a *tool* here would be a grep against a curated consumer list, which is the thing that drifts; the durable half is a doctrine line beside §"Audit-gate signal discipline" saying a new verdict word is a contract change and every matcher on the old one must be swept. The concrete instance is already pinned by a test and a mutation, so this row is about the general rule, not the fix.
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — the row already reaches this verdict: a
  grep over a curated consumer list drifts exactly like the matchers it is meant to guard. The
  durable form is the doctrine line — a new verdict word is a contract change — and the concrete
  instance is pinned by a test and a mutation already.
- **re-probe a monitoring row's premise before fixing it**: four of nine carried premises were false this session (J41's `merge-base`, J34's "survivable", J35's "the wrapper needs the fix", a candidate row's "sibling DECLINED"), each false in a way that would have produced the wrong fix — recurrence: 4 — candidate: no — `h-mad/SKILL.md` §"Working a `skill-monitoring` item" step 1 **already prescribes exactly this**, and it is what caught all four. Nothing is missing; the rule worked. Recorded so the next scout does not read a high recurrence count as an unmet need.
- **structural assertion when a property has no observable trace**: atomicity is invisible from outside — `cp` + `rm` produces the same content and leaves no temp, so a mutation swapping `mv` for it left every behavioural assertion green and the guard had to name the syscall — recurrence: 1 — candidate: maybe — a technique, not a tool, and one that is normally a smell; it belongs as a sentence in `invariants.base.md` §"Test discrimination" qualifying WHEN asserting on source is legitimate (the property lives in the mechanism and racing the writer is the only behavioural alternative), so the exception does not get cited as licence.
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — asserting on source is normally a smell,
  and the exception needs a human to say why the property has no behavioural trace. A tool that
  applied it would generalise the exception into licence, which is the opposite of the row's point.
  Belongs in `invariants.base.md` §"Test discrimination".

## 2026-08-28 — silent-pass-defects (scout)

- **consumer sweep when a verdict token gains a word** (recurrence, not a new row): recurrence 1 → 2 (severe; see 2026-08-28 monitoring-backlog-drained). Second occurrence, and this time the row **prevented** the failure rather than recording it: adding `ANCHORS_UNCLASSIFIABLE` for the unparseable-spec fix would have fallen through the same hook's ordered `case` to the same catch-all `Push ALLOWED` arm. Reading the consumer first turned the fix into a fold onto the existing `ANCHORS_UNREADABLE` (`e9452d2`), needing no coordinated release. A row that changes a decision on its second sighting is worth keeping open on that evidence alone.
- **a red test can disable a whole mutation spec**: before dismissing a failing test as cosmetic, grep the mutation specs for its file in their baseline `command` — a red baseline makes the harness return `BASELINE_NOT_GREEN`, so every mutation in that spec goes unrun while the spec still looks like coverage. Measured: two `TestAtomicOutWrite` failures had silently disabled `out_wait_atomicity.json` (5 mutations) for as long as they had been red — recurrence: 1 — candidate: maybe — likely a sentence in `h-mad/SKILL.md` §"Mutation verification" rather than a tool; the check is one grep, and the hard part is remembering that a red test is not only a missing assertion.
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — the cheap form is one grep, and it only
  helps once you already know a test is red — at which point the suite has told you. The expensive
  form (re-running every spec's baseline) costs a full suite per spec. The durable half is
  remembering that a red test is not only a missing assertion.
- **validate a new checker against the live system, not only its fixtures**: `check_siblings()` passed six unit tests and still reported `INSTALL: PASS` over the real stale copy — the fixture had flattened a two-level layout, making the bug it was written for unreachable. Caught only by pointing the finished checker at the actual install — recurrence: 2 (this; and `--check-anchors` given a directory, where the real invocation shape differed from every test's) — candidate: maybe — adjacent to the DECLINED `fix-the-fixture-not-just-the-assertion`, but distinct: that one is about test DATA hiding a surviving mutation, this is about a fixture whose SHAPE cannot express the production layout. A gate that only ever sees its own fixtures measures its fixtures.
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — "point the finished checker at the real
  system" is the one step a fixture-driven harness cannot take for you; a tool doing it would need
  the production layout, which is the thing the fixture failed to express.

## 2026-08-29 — hmad-tooling-defects-closed (scout)

- **split-a-mixed-doc-change-into-atomic-commits**: when one doc (here `h-mad/SKILL.md`) carries hunks belonging to two independent fixes, `git stash push -- <file>` → `git stash show -p` → slice the hunks into two patches by `@@` line offsets → `git apply` each before its own commit. Hand-rolled the whole pipeline; the fiddly part is that later hunks' `+` offsets assume the earlier ones are already applied, so the patches must be applied in order — recurrence: 1 — candidate: maybe (one occurrence, and `git add -p` would cover it if it were not interactive-only in this harness — which is exactly why it was hand-rolled)
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — the hunk-slicing pipeline is a one-off git
  incantation for a situation the durable rule prevents — commit atomically in the first place. A
  maintained splitter would make mixing two fixes in one file cheaper, which is the wrong direction,
  and `git add -p` covers it wherever it is interactive.
- **serialise the mutation harness against any concurrent test run**: the harness edits source in place and reverts per mutation, so a backgrounded `pytest` over the same tree reads half-applied mutants and reports phantom regressions — cost two discarded full-suite runs before the results were recognised as meaningless — recurrence: 2 (both in this session) — candidate: no — **LANDED as guidance, not code**: `docs/learnings.md` 2026-08-29 entry plus the `skills-repo-verification-shape` auto-memory. It is a sequencing rule with no artifact to build; the harness cannot detect a foreign pytest without inspecting other processes.

## 2026-08-31 — codex-agy-model-inheritance

- **which model did this dispatch actually run?**: after removing the model pin, every check of "what will/did `exec` resolve" was hand-written twice per agent — for codex, `sed -n '1,9p' <log>` to read the session header's `model:`/`reasoning effort:`; for agy, a Python scan of `~/.gemini/antigravity-cli/log/cli-*.log` for `Propagating selected model override to backend: label="…"` (because `ls -t` is dead under rtk and the NDJSON stream carries no model field at all) — recurrence: 5 in one session — candidate: yes — a `hmad-dispatch resolved-model <codex|agy> [--log <f>]` verb, or a line in `env`, would answer it once per agent instead of per invocation. The value is not convenience: with nothing pinned, the resolved model is the ONLY evidence of what a 5d/5e dispatch ran, and a configured `gpt-5.6-luna` returns a well-formed `STATUS: BLOCKED` that looks exactly like a task verdict. Both extractors are one line each and both are already written in `h-mad/SKILL.md` prose, where they cannot be executed.
  — **LANDED 2026-09-01 (`7541628`)** as `h-mad/scripts/h_mad_resolved_model.py` and the `hmad-dispatch resolved-model <agent> [--log <f>]` verb; SKILL.md's helper registry documents it. (Flipped 2026-09-02 by the automation scout: the row still read TRIAGED/open while the script had shipped the same day.)
  — earlier: TRIAGED 2026-09-01: useful and codable — stays open. both extractors are already written, in
  prose, where they cannot run; `hmad-dispatch resolved-model <agent>` or a line in `env` is a
  direct port. Recurrence 5 in one session, and with nothing pinned the resolved model is the only
  evidence of what a 5d/5e dispatch actually ran.
  — **LANDED 2026-09-01** as `h_mad_resolved_model.py` + `hmad-dispatch resolved-model`, and the row's
  premise was **half false**: the codex extractor did port as one line, the agy one did not. Measured
  against the real 620-log corpus before writing it. (1) The agy log **tears mid-line** under
  concurrent writers, so the documented `label="[^"]+"` matched across a newline and produced eight
  fragments such as `GeminERROR: logging before google.Init: …` — a naive port reports one of those as
  the model, with rc=0. Bounding the capture to one line and 60 chars removes all eight and keeps
  every real label (2,670 matches, three distinct values). (2) `ls -t` was never the issue people
  thought: mtime order and NAME order **disagree**, because a long-lived agy pane and a short
  `exec agy` log side by side — so "the newest log" answers a different question depending which you
  pick, and the tool now names the file that answered and REFUSES when the two most recent disagree.
  An `exec agy --log` is stream-json with no model field; passing one is refused rather than silently
  answered from the cli corpus. `configured` and `resolved` are separate words in the output because a
  config says what will run, never what did. 10 tests, 4 mutants ALL_CAUGHT. A fifth mutant survived
  and was the useful one: it targeted a substring blacklist over the label, and measuring the corpus
  showed that guard rejected **nothing** the bound had not already excluded — so the dead guard was
  deleted rather than a fixture invented to make it bite.
- **config-flip propagation probe**: proving "changing the CLI setting moves the dispatch" needs backup → flip → probe → restore → sha256-verify-identical, run once per agent against two different config formats (TOML for codex, JSON for agy) — recurrence: 2 (one session) — candidate: maybe — the shape is general (any inherited-setting claim needs it, and current-state resolution is NOT propagation), but n=2 on one afternoon is thin, and the risky half is the restore, which a script makes no safer than a `trap … EXIT INT TERM` already does. Re-file if a third inherited setting shows up.
  — **DECLINED 2026-09-01 (triage: useful, not codable)** — the row's own analysis: the risky half is
  the restore, and a script makes that no safer than the `trap … EXIT INT TERM` already does. n=2 in
  one afternoon, across two config formats that share no code.

## 2026-08-31 — j1-launch-pane-pin (takeover probe)

Filed by the takeover of `docs/handoffs/2026-08-31-main__j1-launch-pane-pin-durability.md` (handover
from HemaSuite `feature/41-headless-nlm-auth-gating`). The item existed for at least two sessions as
TodoList `#54` and nothing else; this heading is the durable home its Next Step 2 asked for.

- **J1 "create response carries no paneKey" — premise DID NOT REPRODUCE on Orca 1.4.192**: five
  `orca terminal create --worktree <sel> --command 'sleep 300' --title j1-probe-N --json` calls
  (3× `active`, 1× `path:/Users/kimhawk/orca/HemaSuite`, 1× `branch:feature/41-headless-nlm-auth-gating`)
  each returned a `paneKey` of the form `<tabId>:<leafId>`, and each joined to exactly one live
  handle in `terminal list` — recurrence: 0/5 — candidate: **no** (nothing to build) — status:
  **DORMANT, guard retained**. Two things this probe did NOT establish, and both are why the guard at
  `h-mad/scripts/hmad-dispatch.sh:889` stays: (1) every response carried `"surface":"visible"`, so the
  documented fallback in `orca terminal create --help` — *"falls back to a background handle if the UI
  cannot adopt it"* — was never induced, and that branch remains the live hypothesis for the original
  omission; it is not reachable from the CLI on demand. (2) n=5 in one afternoon on one build cannot
  falsify a defect the brief describes as intermittent. Re-probe before removing anything.
- **the `.result.terminal.handle` half of J1 did not reproduce either — and the doc asserts it as
  settled**: `h-mad/references/agent-substrate.md:27` calls that field "a pre-adoption placeholder the
  pane never has (J1, confirmed 3×)". In all 5 probes the create-response handle was **identical** to
  the handle the pane was later adopted under, and appeared in `terminal list` exactly once — recurrence:
  5/5 contradicting — candidate: **no** (a doc correction, not a tool). The 2026-08-02 observation is
  not disputed for the build it was taken on; what is wrong is the tense. "The pane never has" reads as
  invariant and is now false, which matters because it is the stated justification for the whole
  resolve-by-paneKey path. Fold this into the open task on reconciling `agent-substrate.md:27` against
  `hmad-dispatch.sh:860`.
- **positive pane ID via `terminal read`, not previews**: `hmad-dispatch env` reported
  `codex -> UNRESOLVED` with three candidate panes it could not tell apart — Orca named none of them in
  `worktree ps` `agents[]` and all three previews were empty. `orca terminal read --terminal <h> --json`
  → `.result.terminal.tail` identified all three unambiguously on the first try (a Codex TUI banner, an
  Antigravity CLI banner, and a bare Oh-My-Zsh prompt), which resolved the pin — recurrence: 1, but it
  resolved a live UNRESOLVED that the existing fallbacks could not — candidate: maybe — a
  `pin-agents` Pass-N that greps `.tail` for each agent's banner would close the gap that the
  `agentType` join and the preview scan both leave open. The guard it must keep is the one that made
  this safe by hand: pin only when **exactly one** candidate matches, because a wrong-but-live pin
  passes the liveness check and silently leaks dispatches into a stranger's shell. Note `.tail` is the
  field name — `.content`/`.output`/`.preview` are all absent, and reading them returns nothing in a way
  that looks exactly like an empty pane.
  — **TRIAGED 2026-09-01: useful and codable — stays open.** a `pin-agents` Pass-N grepping
  `.result.terminal.tail` for each agent's banner, keeping the exactly-one guard. Confirmed live
  again on 2026-09-01: `pin-agents` still reports `codex UNRESOLVED` on this repo and the pin
  survives only because the carry fix now keeps it — auto-detect itself is still blind.
  — **prerequisite named 2026-09-01**: no wrapper verb reads an ARBITRARY handle. `hmad-dispatch read`
  resolves a pinned AGENT (`codex`/`agy`) via `_resolve_target`, so every place this skill and h-mad
  prescribe reading a candidate pane names the raw `orca terminal read` instead — which the
  handoff skill's own "never call orca directly" guard then flags. That guard was RED from
  2026-08-31 for exactly this reason and nobody saw it (see the suite-collection row). Whatever
  shape this Pass-N takes, a handle-addressed read verb is its first half.
  — **RE-CHECKED 2026-09-02 (scout): still open; the prerequisite re-measured, not assumed.**
  `_resolve_target` (`h-mad/scripts/hmad-dispatch.sh:281-303`) switches on `"$sub:$agent"` with arms
  for `codex` and `agy` only and a `*)` arm that prints `unknown agent` and returns 2 — so
  `_cmd_read` (`:3303`), which calls it before ever reaching `orca terminal read`, still cannot be
  handed a raw handle. `_agent_tail_re` does not exist in the wrapper: the feature that would close
  this row is `pin-agents-tail-banner`, live on `feature/pin-agents-tail-banner`, whose Phase 5b has
  spent 20 audit cycles without gating. **Do not build this row's Pass-N separately** — it is the
  same mechanism, and a second implementation would race the one under design.
  — **LANDED 2026-10-03** — `hmad-dispatch.sh` `_orca_tail_sig` reads `.result.terminal.tail` with an exactly-one guard (`tn -eq 1`); `3295b3d6` + `a855f5c6`, merged at `bf1c8517`; pinned by `tests/mutation-specs/tail_signature_pass.json`. The handle-addressed `read` verb the row named as a prerequisite never shipped; the pass uses an internal helper.
- **`exec-pane` was the surface with no J1 guard at all**: `_cmd_exec_pane` read
  `.result.terminal.handle` from the create response and used it directly — registering it in the
  pane pool and dispatching to it — while `_cmd_launch` refused that same field as unpinnable. The
  failure is asymmetric: a durable launch pin must be proven live, while an exec-pane dispatch is
  already running and a placeholder can only leave an inert pool entry. The cheap version was to
  reuse the existing paneKey-join helper rather than a second unconditional guard.
  — **LANDED 2026-08-31**, the cheap way the row predicted: the join loop came out of `_cmd_launch`
  into `_resolve_pane_by_key <paneKey> [timeout]` and both call sites use it. The two call sites
  **deliberately disagree on failure**, which is the part the row did not anticipate: `launch` requires
  a paneKey join or exact-handle liveness proof (its product is a durable pin, and a wrong value poisons
  every later dispatch), while `exec-pane` warns and falls back immediately (its product is a dispatch
  already running by the time the response is read — waiting or refusing would strand live work to
  protect a pool entry and a stderr line). A fail-loud
  `exec-pane` would have passed a "resolves by paneKey" test and broken every host build that omits the
  field, so the fallback is pinned as its own test, not left implicit. 3 tests, 3/3 mutants caught in
  both directions (ignore-the-join, refuse-instead-of-fall-back, never-expire). Note the first deadline
  mutant was **degenerate** — `; true` inside the command substitution produced an empty `resolved`,
  which is the fallback the test already expects, so it landed on the same behaviour and proved nothing;
  the mutant that discriminates removes the deadline `return 1` and hangs.
  — **PREMISE CORRECTED, same day.** The row above says the omission "was never induced" and that
  `surface: visible` on 5/5 left the background-handle fallback as the live hypothesis. Both halves
  are now wrong. Creating a `codex` terminal into a freshly created worktree returned
  `{"handle":"term_69165bc9…","paneKey":null,"surface":"visible"}` — the omission **reproduced**, and
  it reproduced with `surface: visible`, so that field does **not** discriminate and the
  adopt-failure hypothesis is falsified as stated. The create handle was **real** (present in
  `terminal list` once, with `tabId`/`leafId`), making this the *inverse* of the original J1 report:
  the key was missing while the handle was good, so refusing to pin would have been the wrong call
  and `exec-pane`'s fallback was the right one. Two immediate isolation probes both carried a
  paneKey — same new worktree via `path:` with a `sleep` payload, and a pre-existing worktree via
  `id:` — so neither newness nor selector form is sufficient alone. **1 omission in 8 creates.** The
  surviving untested variable is elapsed time since `worktree create` (the failing call was seconds
  after it; the succeeding one into the same worktree came later), which is n=1 and a hypothesis, not
  a finding. Handed to `BrightGold70/j1-residual-probes` with the repro. **The guard at
  `hmad-dispatch.sh` is NOT dormant — do not delete it.** Filed here rather than only in the brief
  because a session's doc is exactly where the last two versions of this item went to die.
  — **CAUSE IS COMMAND-DISCRIMINATED ON 1.4.192; FALLBACK LANDED.** The receiving lane ran matched
  immediate-create arms in fresh throwaway worktrees. Ten `sleep 300` terminals created 117–134ms
  after their worktrees each carried a paneKey; ten `codex` terminals created 115–134ms after theirs
  omitted it **10/10**; three `agy --dangerously-skip-permissions` controls carried it 3/3. Combined
  with the sender's eight probes: **codex 11/11 missing, sleep 0/16 missing, agy 0/3 missing**, plus
  one additional key-bearing id-selector control. Every one of the 31 responses said
  `surface: visible`, so neither elapsed time nor surface explains the
  omission, and `surface: background` was not inducible. Every paneKey-less codex response handle
  appeared exactly once in `terminal list`. That last fact supplies the safe path the old guard lacked:
  `launch` still prefers the paneKey join, but when the key is absent it now polls for the **exact**
  response handle and pins only if that handle independently appears live. A historical J1 placeholder
  that never appears, or an unreadable listing, still fails loud. Focused tests cover live, absent, and
  unreadable shapes; a live disposable-worktree `hmad-dispatch launch codex` pinned the validated handle.
- **`.result.split.handle` was the same shape of gap; now measured and closed**: `_cmd_exec_pane`
  (`--split <handle>`) reads a handle out of a **different** response object (`.result.split`, not
  `.result.terminal`) and pools it the same way. It was deliberately not changed with the create path:
  inventing a join for a shape nobody has seen is how a guard gets written against an imagined field.
  **CLOSED 2026-08-31, no code change.** The raw response was
  `{"split":{"handle":"term_…","tabId":"aaf3…","paneRuntimeId":1}}`: no `paneKey`, `leafId`,
  or other joinable pane identity. The response handle matched exactly one live split pane carrying the
  same `tabId`, and both panes were cleaned up. There is nothing safe to route through
  `_resolve_pane_by_key`; retaining `.result.split.handle` is the evidence-backed outcome —
  candidate: no — the measurement was the whole deliverable: there is no joinable field to route,
  so there is no guard to build. Reopen only if a host response grows a pane identity on
  `.result.split`.

## 2026-08-31 — j1-pane-pin-takeover-and-handover (scout)

- **verify an OUTBOUND handover actually landed**: after delivering, check three things that only the
  receiver can produce — the feature's `owner_session_id` in `docs/.bkit-memory.json` changed to a
  session that is not you, the target worktree comment flipped from `handover:` to `taken over:`, and
  the receiving pane's own output says so (`orca terminal read` → `.result.terminal.tail`) —
  recurrence: 1 — candidate: maybe — the sender-side counterpart to `verify-inbound-handover`
  (2026-08-03, closed as skill guidance), and the gap it fills is real: HANDOVER's own §Step 5 says
  `accepted: true` proves a live handle took bytes and **not** that anyone picked the work up, then
  §Step 6 says stop monitoring — so the skill correctly forbids *watching* and offers nothing for
  *checking once, later*. Those are different asks and only the second is cheap. Worth a row because
  this is the first handover in this repo whose landing was confirmed rather than assumed. Not
  urgent: three read-only commands, and the judgement it must not automate is what to do when the
  answer is no.
  — **TRIAGED 2026-09-01: useful and codable — stays open.** three read-only checks against three
  surfaces that already exist (`owner_session_id`, the worktree comment prefix,
  `.result.terminal.tail`). The judgement it must not automate — what to do when the answer is no —
  is outside the check, not inside it.
  — **LANDED 2026-09-01** as `handoff/scripts/handover_landed.py` + HANDOVER §Step 7, with **two** of the
  three signals, and the third named rather than quietly dropped. Implemented: the claim moved to a
  session that is not the sender, and the worktree comment flipped `handover:` -> `taken over:`. NOT
  implemented: the receiving pane's tail — no wrapper verb reads an arbitrary handle (`hmad-dispatch
  read` resolves a PINNED agent), this skill does not call `orca` directly, and a pane can echo a
  prompt it never acted on; that missing verb is the same prerequisite the pane-ID row now carries.
  The design decision the row did not anticipate: `UNKNOWN` needs its own verdict and its own exit
  code. The reader of this output has already released the claim and stopped watching, so rendering
  "I could not check" as "nobody took it" is what sends them to re-deliver work already in progress —
  two sessions on one feature, one branch, contradictory conclusions. One signal is proof rather than
  both, because off Orca the comment signal is permanently unavailable and demanding both would make
  the tool useless exactly where it has no alternative. 12 tests, 4 mutants ALL_CAUGHT.
- **response-shape census for an Orca verb**: call `orca terminal create --json` N times across
  varied selectors, tabulate one field's presence against the others, join each response to
  `terminal list`, and close every pane afterwards — hand-rolled 8 times in one session to decide
  whether a guard was dormant — recurrence: 8 — candidate: maybe — the tabulating is trivial; the
  half that actually goes wrong is **cleanup**, since a probe that leaks panes pollutes the pane pool
  and the next `pin-agents` run. A `--cleanup`-guaranteed probe loop (create → record → close in a
  trap) would make "measure a response shape" a safe thing to do casually, which matters because the
  alternative is reasoning from a doc comment. Note the finding it produced was that **5/5 said one
  thing and the 8th said the opposite** — n<8 here would have shipped the wrong conclusion, so the
  tool's value is in making a larger N cheap, not in the loop itself.
  — **TRIAGED 2026-09-01: useful and codable — stays open.** recurrence 8 in one session, and the half
  that goes wrong is cleanup, which is exactly what a create/record/close-in-a-trap loop fixes. Its
  value is making a larger N cheap: 5/5 said one thing and the 8th said the opposite.
  — **LANDED 2026-09-01** as `h_mad_response_probe.py`, built around the half the row said goes wrong.
  A `trap` is not enough and the tests say why: it does not survive a kill, and it cannot help at all
  with the window between a pane existing and the process learning its handle. So every attempt is
  journalled to disk BEFORE the create, cleanup runs from `finally` AND from installed SIGINT/SIGTERM
  handlers, `--resume <journal>` closes what an earlier run could not, and an attempt with no handle is
  reported as a POSSIBLE leak rather than dropped. Closes are journalled too, so `--resume` is
  idempotent — a second one must not close a handle the runtime has since reissued to someone else's
  pane, which would make the cleanup tool worse than the leak. Kept command-agnostic (create/close as
  argv templates) so it is testable with no runtime and is not welded to one verb. 7 tests, 5 mutants
  ALL_CAUGHT, one per escape route: no intent line, no cleanup on the normal path, a no-op `--resume`,
  unrecorded closes, and no signal handlers.
- **create the handover lane LAST, or fast-forward it**: `orca worktree create` snapshots the branch
  at that instant, so two commits pushed afterwards — including a correction to the brief's own
  central premise — never reached the receiver's checkout — recurrence: 1 — candidate: no — this is a
  sequencing rule, not a tool, and it belongs as a sentence in the handoff skill's HANDOVER §Step 5
  rather than as code. Recorded because the failure was **invisible**: the takeover succeeded anyway,
  since READ resolves the *canonical* main-worktree store rather than the lane's own, so the receiver
  read the corrected brief while its checkout held the stale one. A design property saved it, not the
  sender.

## 2026-08-31 — wire-pin-numbered-labels

- **a gate that fails CLOSED can hide for weeks**: `h_mad_wire_pin_gate.py`'s field regex allowed only
  `**`, a parenthetical qualifier, or `:` after the label word, so `**WIRE 1**:` / `**WIRE 2A**:` /
  `**WIRE-PIN 1**:` matched nothing and a two-wire task read as `wiring` shape carrying **no wire at
  all** — a blocking `missing WIRE` on a correctly-written plan — recurrence: 1 (5 wires across 2
  tasks, live) — candidate: no — a defect, not a tool; **LANDED 2026-08-31**. Filed because the
  *shape* generalises and is worth a doctrine line: the reason nobody found it is that it failed in
  the SAFE direction. A gate that emits a false PASS gets hunted; a gate that blocks correct work
  gets **worked around by hand** — here by rewriting the plan's labels to canonical pairs — and the
  workaround leaves no trace pointing at the gate. Ask of every gate not only "can it pass something
  it should fail?" but "can it fail something it should pass, and what would an author do about it?"
  The tell to look for is a hand-edit that makes a document conform to a tool rather than a fix that
  makes the tool read the document.
- **the second bug was underneath the first, and only the fix exposed it**: making the labels visible
  was half the work. `_parse_tasks` kept ONE wire slot per task, and the registry's identity is
  `(owning_feature, id)` — so two wires from one task **collide by construction** and the second
  upserts the first, while the gate still prints `registered=2`. That is the same collision shape as
  J43 (which widened the key from bare `id`), one level down, and it is strictly worse than the
  blocking FAIL it replaced: a short registry is indistinguishable from a plan that only had one
  wire, and the count agrees with it — recurrence: 1 — candidate: no — fixed by carrying the label
  suffix into the registered id (`Task 12 (WIRE 2)`); a bare `**WIRE**:` keeps the plain task id, so
  no existing record changes identity and no migration is needed. **A regex-only fix would have
  turned a loud blocker into a silent under-registration.**
- **the surviving mutant named a fixture I did not have**: `only-the-first-wire-is-obligated`
  (`task["wires"][:1]`) survived every test in the new class, because all of them put the real value
  FIRST. It is not an equivalent mutant — it differs exactly when a template placeholder occupies
  `**WIRE 1**:` and the real wire is `**WIRE 2**:`, which is the ordinary shape of a partly-filled
  plan — recurrence: 1 — candidate: no — recorded because the harness's advice ("write the
  discriminating test") was right and cheap here, and because it is the third time this week a
  survivor turned out to be a missing HOSTILE fixture rather than a missing guard. Tidy fixtures put
  the real value first; real plans do not.

## 2026-09-01 — wire-pin-gate-and-skill-upgrades (scout)

- **check for a live run before merging a shared skill change**: `~/.claude/skills/h-mad` is a
  symlink into this repo, so a merge to `main` changes the *installed* skill in every session
  immediately — including one mid-cycle. Measured from the other side this session: `3219bdd` landed
  while a HemaSuite h-mad run was in flight and, per that lane's own record, "silently invalidated a
  batch-18 decision" — nothing broke, the damage was to reasoning already done, because a verdict
  recorded as a fact had been produced by a gate that then moved — recurrence: 2 — candidate: yes —
  the check is mechanical (`hmad-dispatch worktree-ps` comments plus `.h-mad/telemetry.jsonl` for a
  feature whose last phase is recent), and the output is a one-line warning naming the lanes, not a
  block. The judgement it must not automate is whether to hold the merge. Note the *consumer*-side
  rule already exists and is the one that saved this ("re-measure tooling, never cite your own
  earlier finding"); this row is the sender-side mirror, which nothing currently prompts.
  — **TRIAGED 2026-09-01: useful and codable — stays open.** `worktree-ps` comments plus
  `.h-mad/telemetry.jsonl` are both already readable, and the output is a one-line warning naming
  the lanes rather than a block. Measured from the receiving side: `3219bdd` landed mid-cycle in
  another lane and invalidated a decision that had already been recorded as fact. **Recurrence 2, 2026-09-01**: the handoff/h-mad defect batch merged to `main` while a HemaSuite lane sat mid-Phase-5 on `feature/41`. The check was done BY HAND and it was the right call — `h_mad_do_preconditions` had been widened to score every audit at the latest cycle, so an A/B of old vs new across all 79 HemaSuite features was run before merging (0 verdict flips; probe proven sensitive by 9 pairs holding >1 live audit at the latest cycle). Doing it by hand is the evidence it is not yet mechanical.
  — **RE-CHECKED 2026-09-02 (scout): still open, still hand-run.** No consumer exists:
  `h_mad_telemetry.py` is the only file touching `.h-mad/telemetry.jsonl` and it is the writer, and
  no script joins it against `hmad-dispatch worktree-ps` comments. Measured while re-checking:
  `worktree-ps` on this machine lists 4 worktrees, and one `main` carries a live sibling stamp
  (`nlm-pin-phase3-fifteen-audit-cycles · Phase 3 OPEN · next: audit cycle 16`) — i.e. the exact
  signal the warning would print was sitting there, readable, unread by anything.
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open, still hand-run, unchanged since 09-02.**
  `grep -rln 'telemetry\.jsonl' h-mad/ handoff/` returns the writer (`h_mad_telemetry.py`), its tests
  and prose only — no reader. `worktree-ps` appears in exactly one file (`h-mad/scripts/hmad-dispatch.sh`)
  and nothing joins the two.
  — **RE-PROBED 2026-10-03: OPEN** — nothing reads `.h-mad/telemetry.jsonl` except its writer and tests, and no pre-merge step joins it with `worktree-ps`.
  — **LANDED 2026-10-04** — `h-mad/scripts/h_mad_live_runs.py` lists Orca worktrees and names every lane whose `docs/.bkit-memory.json` holds a claim with a live heartbeat (`owner_is_live`, the rule `--claim` uses). Not telemetry: measured, `.h-mad/telemetry.jsonl` records only COMPLETED features, so it cannot show a run in flight. Unreadable state or failed discovery prints `UNKNOWN`, never `NONE`. The advisory pre-commit hook prints it when a commit stages a file under a SKILL.md directory; it never blocks. Fixtures are written by the real `h_mad_state_write.py`. Specs `live_runs.json` ALL_CAUGHT 5/5, `doc_consumers.json` re-anchored plus two hook rows (ALL_CAUGHT 7/7). Live today: `NONE checked=4`.
- **section-bounded slicing for doc-rule tests**: `test_h_mad_context_budget_docs.py` sliced a fixed
  `s[i:i + 4000]` window from a heading to scope its assertions, and that window silently stopped
  covering the end of its own section the moment a paragraph was added — the pin failed for the wrong
  reason ("the test lost sight of the text", not "the doc regressed"), and had the growth been
  elsewhere it would have gone **vacuous** instead of failing — recurrence: 1 here, but the pattern is
  in every doc-rule test file that scopes by offset — candidate: maybe — the fix was six lines
  (`_titled_section`: find the heading, bound on the next `## `), and the reason it is worth sharing
  rather than re-deriving is the fence caveat the existing `_section()` in that same file already
  documents: a bash block's `#` comments end a naive section scan early. Two helpers with the same
  name now sit in one file because I did not check for the first — a shared one would have made that
  collision impossible.
  — **TRIAGED 2026-09-01: useful and codable — stays open.** a shared `_titled_section` helper is six
  lines and removes a whole class of vacuous doc-rule pin; the same file already grew two same-named
  helpers because the first was not found. Live instance still open in
  `test_handoff_read_auto_resolve.py`, which slices `RAW[i:i + 1600]`.
  — **LANDED 2026-09-01** as `h-mad/tests/docsections.py` (`titled_section` + `section_from`), and the
  row understated it: the collision was not the worst part. The other local level-aware helper, in
  `test_h_mad_wire_registry.py`, was fence-BLIND, so a `# comment` at column 0 inside a bash block
  ended the section inside its own example — measured against the real `h-mad/SKILL.md`, it bounded
  `## Phase 5 (Implementation) sub-steps` at offset 54555 where the section ends at 78825, hiding
  **24,270 characters** from three live pins. Nothing was vacuous only because every assertion there
  is positive and happened to land early; one `not in` would have passed against text it never saw.
  Migrated the three provably-defective call sites only (wire-registry, `review_evidence`'s two
  `s[i:i + 3000]` windows, and handoff's `RAW[i:i + 1600]` — the last bounded on its own closing
  fence rather than importing, so the handoff suite still runs from its install path with nothing
  beside it). The other five `_section` helpers take literal start/end bounds, which is a different
  and legitimate intent; unifying them was not the defect. 6 tests, 4 mutants ALL_CAUGHT, and the
  live-file pin is deliberate — a fixture written from the tight case is green on this bug.

## 2026-09-01 — handoff-resume-divergence-fix (scout)

- **`pin-agents` DESTROYS a still-live pin while repairing the other agent**: the pin file has two
  writers with opposite semantics, and only one of them says so. `_cmd_pin` merges — it reads the
  existing file, drops the one `^<agent>=` line, and re-appends — while `_cmd_pin_agents` resolves
  both agents FRESH into a `mktemp` and `mv`s it over the file, by design ("it never reads the pin
  file it is about to write"). That design note accounts for a *stale* pin being overwritten; it does
  not account for a **live** one being deleted. Measured live this session on Orca 1.4.192: `env`
  reported `codex -> term_f483657a…` plus `agy … STALE (no such terminal)`, `PREFLIGHT: FAIL
  stale=agy`. One `hmad-dispatch pin-agents` — run to fix `agy` — resolved `agy`, printed `codex
  UNRESOLVED`, and left the file containing exactly one line, `agy=…`. The dropped codex handle was
  **not** stale: re-pinning it by hand succeeded, and `_cmd_pin` refuses any handle absent from
  `orca terminal list`, so the pin it destroyed was valid. The loss is guaranteed rather than
  incidental for codex specifically, because the same function's own comment states auto-detect
  cannot re-find codex once its banner decays — so every `pin-agents` run after that point trades a
  working codex pin for a rediscovered agy one — candidate: yes — the fix is to seed `$tmp` from the
  existing pin file the way `_cmd_pin` does, and drop a prior line only when the agent re-resolves or
  its pinned handle is proven dead (`_orca_handle_live` is already in the file and is what `pin` and
  `env` use). Keep the loud `rc=1` on unresolved: the bug is not the exit code, it is that the
  repair had a side effect nobody asked for. The tell that this had been silently absorbed before:
  `env` names re-pinning as the remedy for a stale pin, so the operator's instinct is to run
  `pin-agents`, and the hand re-pin afterwards leaves no trace pointing back at it — the same shape
  as the wire-pin gate that blocked correct work and was worked around by rewriting the document.
  A test needs both arms: one live pin + one stale, assert the live one **survives**.
  — **LANDED 2026-09-01**, the way the row predicted, plus one thing it did not: the carry is
  **three**-way, not two. `_orca_handle_live` answers 0/1/2, and only a readable listing that lacks
  the handle (1) drops the pin — an unreadable listing (2) keeps it, because the moment the runtime
  cannot be queried is exactly the moment a pin is load-bearing. The predicted two arms are there and
  a third covers the unreadable case. The trap while writing it: `set -euo pipefail` is on and that
  helper returns non-zero as an **answer**, so the obvious `cmd; rc=$?` killed the script at the very
  branch it was meant to take — the pin file went unwritten, and the drop test then failed for the
  wrong reason and would have been 'fixed' by weakening it. The file's existing
  `{ _orca_handle_live "$h"; [ $? -eq 1 ]; }` idiom exists for exactly this. 4 mutants, ALL_CAUGHT,
  one of them pinning that idiom.
- **the "no live agent in that worktree" gate for READ Step 3.6 — proposed, specified, FALSIFIED**:
  carried out of the 2026-09-01 handoff as `[suggested]` "widen the allowlist to the fast-forwardable
  sibling; the gate would need *no live agent in that worktree*, checkable via `orca terminal read`".
  Probed before writing anything: the check cannot exist. `orca terminal read` returns a tail, and a
  tail proves an agent is **present** (a banner) and never that one is **absent** — a quiet tail is an
  idle agent between turns, and any non-Orca session in that directory (a plain shell, an editor
  terminal, another Claude Code) emits nothing an Orca-side check can see. The gate therefore answers
  "present" or "could not verify", never "absent", and Step 3.6's own fail-closed predicate then
  forbids the repair — so the gate can never legitimately pass, which is the definition of the
  never-list entry it was meant to remove. Check and pull are also not atomic. — candidate: no — the
  generalisable rule ("a gate that can never legitimately pass IS a never-list entry") and the
  falsification both landed in `handoff/SKILL.md` §Step 3.6 with 5 mutants, together with the half
  that *is* free: report the sibling with the ready command, counting from the shared ref namespace
  (`git rev-list --left-right --count refs/remotes/origin/<b>...refs/heads/<b>`) so the measurement
  never touches the lane it describes. Filed here rather than left in the handoff because a Next Step
  that is refused on inspection leaves no trace otherwise, and the idea is attractive enough to be
  had again.
- **the suite command excluded a whole test directory, and every "full suite passed" was blind to it**:
  the habitual invocation was `pytest h-mad/tests handoff/tests`, and `handoff/scripts` holds 110 more
  tests beside the scripts they pin. `test_orca_is_only_ever_reached_through_the_wrapper` had been RED
  there since **2026-08-31** — bisected, and it predates this session — while four commits and a
  handoff document's own closing verification all reported a green suite. Not a failing gate: a
  passing one that was never asked the question, which is the same shape as the fence-blind section
  bound found the same day (a bound nobody set wrong, just set narrow) — candidate: yes —
  **LANDED 2026-09-01** as `pytest.ini` with `testpaths = h-mad/tests handoff/tests handoff/scripts`
  plus `test_suite_collection.py`, which asserts COMPLETENESS WITHIN each declared skill rather than
  across the repo: this checkout also vendors three independent projects with their own dependency
  sets, and dragging them into a bare `pytest` is their owners' decision, not a side effect of this
  fix. `testpaths` applies only when pytest gets no path arguments, so an install-path run
  (`pytest ~/.claude/skills/h-mad/tests/`) is unchanged. 1 mutant, ALL_CAUGHT — it restores the exact
  pre-fix `testpaths` line, because a guard that cannot fail on the configuration that caused the bug
  is decoration. Bare `pytest` now collects **2513**, up from 2403.

## 2026-09-02 — audit-report-docs-copy-phase7

- **6a-prime prompt template: worktree citation + no-mutation rules**: three of four archreview cycles either cited files through `~/.claude/skills/h-mad` (a different checkout) or wrote probe files / ran the mutation harness inside the repo despite a per-cycle addendum forbidding it — recurrence: 3 — candidate: no (an upgrade to `references/agy-architectural-reviewer-prompt.md`, not a new skill; insertion point is the template's "How to inspect" block)
- **archreview scorer tree-diff**: `h_mad_archreview_cycle.py score` could snapshot `git status --short` before the dispatch and report any delta as a finding, closing the "audit mutated what it measured" check mechanically instead of by eye every cycle — recurrence: 2 — candidate: maybe
  — **RE-PROBED 2026-10-03: OPEN** — `h_mad_archreview_cycle.py` `score()` takes no `git status` snapshot before the dispatch.
  — **DEFERRED 2026-10-05 (triage, calibrated)** — Codable and cheap, but 0 incidents in the roughly 197 handoffs (72 skills, 125 HemaSuite) since the prompt rule `6bdcf3f7` (2026-09-02) landed; the two pre-rule incidents were the 5b audit channel (HemaSuite 2026-08-28) and 6a-prime probe files (skills 2026-09-02), and the `.done` noise that made an absolute delta useless was removed by gitignoring `*.done`. Reopen when any archreview or audit cycle after `6bdcf3f7` is found to have changed the tree; then build it in `hmad-dispatch exec` behind a `--read-only` flag, not in `score()`, so the audit and archreview channels share it.
- **execute a doc's fenced bash block as a test**: the Task 5 recipe's four review-cycle defects were only visible by EXTRACTING the fenced block and RUNNING it against fixtures (phase-hardcoded path, unimplemented halt, whitespace truncation, shell-killing exit); the extract+substitute+run harness was hand-written in the test — recurrence: 4 — candidate: maybe (a `h_mad_doc_block_exec.py` helper: extract the Nth `bash` fence under a heading, substitute `<placeholders>` from a map, run under `bash -euo pipefail` in a tmp cwd, return rc+stdout+stderr) — **LANDED** (`h-mad/scripts/h_mad_doc_block_exec.py`, 788 lines, latest `92ae93a`). Every mechanic this row asked for is present and was verified in the file rather than taken from the name: `bash -euo pipefail -c` at `:413`, a private cwd with verified cleanup at `:386`, placeholder substitution, and rc+stdout+stderr returned. **One deliberate deviation from the row, and it is the safer direction:** blocks are selected by an EXPLICIT tag in the info string, not by "the Nth `bash` fence under a heading" — an ordinal selector silently re-points at a different block when someone inserts a fence above it, which is the same drift class as a mutation anchor. Ambiguity is an error (`AmbiguousBlock`, `AmbiguousHeading`), never a first-match
- **probe the rungs below a changed branch**: after a fix on one rung of a fall-through ladder, the rung below regressed and only the next review cycle caught it; a checklist-style "enumerate every later rung and run one input through each" was done by hand — recurrence: 2 — candidate: no (discipline, captured in learnings; not a script)
## 2026-09-01 — pin-agents-tail-banner phase 5 (scout)

- **`handover_landed.py` reads a COMPLETED handover as `NOT_YET`, and the two prescribe opposite
  actions**: the tool decides pickup from two signals — a claim owned by someone other than the
  sender, and a worktree comment starting `taken over:`. It models `NOT_YET` versus `UNKNOWN`
  carefully (the distinction it was built for, row `848`) but not **DONE-and-moved-on**. Measured
  live this session: an outbound handover of the `_frame_satisfies` SIGPIPE fix was picked up,
  fixed, tested, mutation-specced and merged to `main` as `282a3a5`, and the check still printed
  `HANDOVER: NOT_YET — every checkable signal says nobody has taken it`. Both signals failed
  honestly: the receiver never wrote a claim (it just did the work, and its worktree has its own
  `docs/.bkit-memory.json` that never existed → `claim: UNKNOWN`), and it had already overwritten
  the stamp with its own completion note, `Complete: SIGPIPE wait gates fixed; main @ 282a3a5;
  h-mad 23` → `comment: NOT_YET  comment does not say taken over:`. The prescribed response to
  `NOT_YET` is to re-deliver, which here would have re-dispatched work already on `main` — two
  lanes on one feature, the exact outcome the claim protocol exists to prevent. The fix is not a
  fourth verdict word: treat a comment that names the feature at all, or a `git log` on the target
  branch, as pickup evidence, and rank "the work is visibly done" above "the stamp has the
  expected prefix". Note the sender is *told* to stop watching, so this check is the only thing
  standing between a silent success and a duplicate dispatch — candidate: yes
  — **LANDED 2026-09-01.** Both prescriptions implemented, plus one the row did not anticipate.
  The comment signal now ranks visible completion above the expected prefix: a comment that is
  neither stamp is pickup, an EMPTY one is not, and both stamp tests moved from `startswith` to
  `in` because HANDOVER Step 4 preserves a human note by APPENDING, so the sender's own stamp
  legitimately sits mid-string and a prefix test would have read it back as receiver evidence.
  A third signal reads the target branch (`--repo`/`--branch`, optional so the older invocation
  still works). What the row did not anticipate: **the branch signal can only ever say `taken`
  or `unknown`, never `not_yet`.** A merged branch and one created-and-never-committed-to are
  both level with the default and both listed by `git branch --merged`; refs cannot separate
  them. Guessing `taken` invents evidence, guessing `not_yet` is the false absence this tool
  exists to refuse — so an absent branch and a level branch are both `unknown`, and two tests
  deliberately assert the SAME verdict for the merged and untouched cases because that identity
  IS the finding. 20 tests, 8 mutants ALL_CAUGHT.

## 2026-09-01 — phase5b-twenty-audit-cycles (scout, deferred; run 2026-09-02)

The 2026-09-01 closeout hit `CTXBUDGET: HALT` at 81.6% immediately after pushing its handoff and
skipped this phase rather than half-running it. Run here on resume, before dispatching audit cycle
36. Source session: 20 impl-plan audit cycles (v16–v35) on the codex surface; every finding applied.

- **resolve a doc-embedded mutation anchor after editing the code block it points into**: the
  impl-plan carries its mutation spec *inline* — 37 `"find"` strings in
  `docs/01-plan/features/pin-agents-tail-banner.impl-plan.md` anchored to code blocks in the same
  document — and editing a block silently orphans every anchor into it. Three instances this
  session, each *after* the check had been written down in prose — recurrence: 3 — candidate: yes —
  **not covered by the existing push-boundary sweep**, and that is the whole point of a separate
  row: `h_mad_mutation_harness.py --check-anchors` plus `git-hooks/pre-push` discover specs with
  `git ls-files -- '*.json'`, so a spec living in markdown is invisible to both (verified
  2026-09-02: the 37 anchors are in a `.md` and the hook greps no markdown). Mechanical shape:
  extract every `"find"` from the plan's fenced blocks, resolve each against the block it names, and
  report the orphans — the same one-match rule `anchor_status()` already enforces, pointed at the
  other store. The session's own mitigation was to *generate* the anchors from the block, which
  removes the authoring error but not the drift that a later edit causes.
  See the LANDED `re-anchor a mutation spec after editing the code it mutates` row above for the
  JSON half; this is the markdown half it does not reach.
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** `h_mad_mutation_harness.py` discovers siblings
  with `spec_path.parent.glob("*.json")` (`:470`) — markdown is still invisible to `--check-anchors`
  and to the pre-push sweep. Adjacent but NOT this: `h-mad/scripts/h_mad_doc_block_exec.py` (the
  feature in flight on this branch) is a fence-aware Markdown block scanner, so it supplies the
  scanner half a markdown anchor resolver would need. It resolves no `"find"` anchors.

  — **DECLINED 2026-10-02 (triage: not useful)** — premise narrowed to one legacy doc: only docs/01-plan/features/pin-agents-tail-banner.impl-plan.md still embeds "find" specs (itself an un-archived leftover, see the archive-completeness row); specs are JSON now and swept by pre-push and the suite.
- **ask what a node asserts when NOTHING is implemented**: three nodes were classified `RED: FAIL`
  that the RED state itself makes pass (AC-1.5, T4's WIRE-PIN, AC-3.17) — a negative-only fixture
  almost never fails, so a node that only asserts an absence is green before the feature exists and
  its `FAIL` classification is fiction — recurrence: 3 — candidate: yes — mechanical half: for every
  authoritative row classified `RED: FAIL`, require the node to name at least one POSITIVE assertion
  (a match that only the implemented behaviour produces), or a mixed positive-plus-decoy fixture.
  Cheaper still and fully mechanical: run the RED suite against the *unmodified* tree and diff the
  actually-failing set against the rows classified `FAIL` — any row in the second set and not the
  first is this defect. That diff is exactly the 5d/5e gate's own input, so this is a check inside a
  step that already runs, not a new tool.
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** No script diffs the RED suite's actually-failing
  set against rows classified `RED: FAIL` — `grep -rln 'RED: FAIL|red_fail|unmodified tree' h-mad/scripts/`
  is empty. The 5d/5e gate still reads the classification, never the tree.
  — **RE-PROBED 2026-10-03: OPEN** — no gate runs the RED suite on the unmodified tree and diffs it against the rows classified FAIL; only a checklist line in `references/codex-implementer-prompt.md`.
  — **DECLINED 2026-10-04 (triage: not useful — calibrated, not built)** — `RED: FAIL`/`RED: PASS` classifications exist in exactly ONE document in the repo: `git grep -c -E 'RED: (FAIL|PASS)'` over every impl-plan and design returns only `pin-agents-tail-banner.impl-plan.md` (60), and no template or reference prescribes them. The general hazard — a node green before the feature exists — is already visible at 5d: `h_mad_assemble_tdd.py` refuses a RED dispatch without explicit `--expect-fail` and `--expect-pass` counts (`:296-301`), so a node passing at RED changes a count that the orchestrator has to state. Reopen if a second plan adopts the per-row RED classification.

- **grep the body for a version-history entry's claim**: four times this session a `## Version
  History` entry announced a back-propagation the body never received (design live check v1.13, plan
  Convention Prerequisites v1.7, the T2 move v1.28/v1.29, design Order+API v1.29) — and the entry
  claiming a back-propagation turned out to be **the single best predictor of the next audit
  finding** — recurrence: 4 — candidate: yes — mechanical: for each version-history entry naming a
  string or section it says it propagated, grep the body for it and report the misses. Distinct from
  the LANDED `doc-version-history-append` row, which makes *writing* an entry anchored and loud; this
  checks that what an entry claims is true of the document it sits in. Natural home is
  `h_mad_version_history.py` as a `--verify` mode, beside the writer that already parses these
  entries.
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** `h-mad/scripts/h_mad_version_history.py` exists
  (11.0K) and has no `--verify` mode and no verify function; it remains a writer only.
  — **RE-PROBED 2026-10-03: OPEN** — `h_mad_version_history.py` has no verify mode (args: path/--version/--text/--dry-run).
  — **CALIBRATED 2026-10-04, not built** — prototype over 110 committed spec/plan/design/impl-plan docs that passed audit: the LATEST entry's backticked spans miss the body 54 of 408 times (13 %), all entries 577 of 4403. Sampled misses are legitimate: removed items (`successor_pin`), audit filenames, the verification command an entry ran (`grep 'return 3|exit 3'`), line pins, renamed signatures. A span-in-body check would fail clean documents, so the mechanical form the row proposes does not survive calibration. What would: restrict to entries that CLAIM a propagation (`back-propagated`, `propagated to`, `now carries`) and to spans those clauses name — which needs the four recorded cases as positives to calibrate against. Stays open.
  — **CALIBRATED 2026-10-05, not built** — built that restricted prototype and it fails the GO rule (recall >= 3/4 AND <= 2 false positives) on both arms. The prototype takes the clause that claims a propagation, takes the backticked spans that clause names, and reports any span absent from the body above `## Version History`. It reuses `h_mad_version_history.py`'s anchor, section and entry parser. **Recall 0/4**, each positive judged at the commit that added its entry: (1) design v1.13 (`aa11a5e5`) says "both now carry the pin-FILE re-read". The claim names prose, so there is no span to check. (2) plan v1.7 (`03c66d55`) says "Blanket-RED rule back-propagated out". That is a REMOVAL claim: it asserts absence, and the entry never quotes the instruction it removed. (3) impl-plan v1.28 (`262999d8`) says "the definition now lives once, in T2". (4) design v1.29 (`22ddc7b8`) says "Added to both" (Components Changed and Implementation Order). (3) and (4) are PLACEMENT claims: `_agent_tail_re` was in the body both times, in the wrong section (inside Task 1; only in Components). A wider trigger (`now names/requires/says`, `added to`, `swept to`) and quoted spans both leave recall at 0/4. **False positives**, LATEST entry only, over 1353 unique docs (118 here + 1235 HemaSuite; 819 with a parseable history). Core trigger: 45 claim entries, 22 named spans, **6 misses, all false**. Three are audit-report filenames cited as the source (`minor-bug-sweep` plan; `unify-research-into-engine-p3b` plan and design). One is the old name the entry says was replaced (`PipelinePlugin`). One is a `path::symbol` citation whose symbol is in the body. One is a regex written into the body as prose (`^(STATUS|VERDICT):`, body: "line beginning with `STATUS:`"). Wide trigger: 19 misses in 14 docs. Each was read and none is real: they add paraphrased field names, line pins, verification commands, code changes in other files and quoted stale text. What a working detector would need is entry structure that these entries lack: (a) section scoping, mapping a named heading (`Implementation Order`, `T2` to `## Task 2`) to its section and checking the span there, which is the only form that sees (3) and (4); (b) a removal mode, which needs the removed text quoted, and (2) never quotes it; (c) document attribution, because an impl-plan clause saying "the source plan and spec … both now name `_agent_tail_re`" is a claim about two other files. Each needs a change to how entries are written. No detector change supplies them. Reopen only if entries adopt a machine-readable `propagated: <doc> §<section> <span>` form.

## 2026-09-02 — phase5b-gated-task1-green (scout)

- **AC bodies must name their test node (or the 5d assembler must carry the contract table)**: `h_mad_assemble_tdd.py` cuts §Task N only; 39 of 45 AC bodies named no node, so the first RED dispatch invented all six T1 names and would have orphaned every T1 mutation pin. Fixed by hand this session (`**Node:**` on every AC). Mechanical: the assembler appends the task's rows from the Test-name contract table, or the audit gate refuses an AC whose body lacks its node — recurrence: 1 (systemic: every task would have hit it) — candidate: yes
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** `grep -c Node h-mad/scripts/h_mad_assemble_tdd.py`
  = 0 — the assembler still cuts §Task N alone and appends no contract table, and no precheck detector
  refuses an AC body that names no node.
  — **RE-PROBED 2026-10-03: OPEN** — `h_mad_assemble_tdd.py` carries no contract table and no audit refuses an AC body without a node.
  — **DECLINED 2026-10-04 (triage: not useful — calibrated, not built)** — measured over every tracked impl-plan with `task_body`: **147 of 162** task bodies name a `test_*` node, and all 15 that do not are tasks that author no tests (docs, probes, baselines, smoke runs, mutation census). The defect needs node names kept in a separate contract table, a layout used by exactly one plan (`pin-agents-tail-banner`; its 37 `**Node:**` lines were the hand fix). A detector would have 0 hits on the corpus. Reopen if a plan again separates node names from task bodies.
- **run prescribed test-helper blocks against the live module's guards before RED**: the impl-plan prescribed `tempfile.mkdtemp(` inside `test_hmad_dispatch.py`, whose own guard asserts that literal is absent; 53 audit cycles could not see it because the block was never executed in situ. Mechanical: extract every prescribed python block whose `file` is an existing test module, append it to a scratch copy, run the module's `*_guard` tests — recurrence: 1 — candidate: yes
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** Nothing extracts a prescribed python block and
  runs it against the target module's `*_guard` tests. `h_mad_doc_block_exec.py` executes tagged SHELL
  blocks from markdown — same scanner, different payload and no in-situ append — so it is adjacency,
  not the fix.
  — **RE-PROBED 2026-10-03: OPEN** — `h_mad_doc_block_exec.py` runs tagged SHELL blocks only; no python test-helper block is appended to a scratch copy of its target module.
  — **LANDED 2026-10-04** — `h-mad/scripts/h_mad_prescribed_block_guards.py`, wired into SKILL.md §5d as a pre-RED check (`PRESCRIBED-BLOCKS: PASS|FAIL|INCOMPLETE|UNREADABLE`). It was built leaner than this row proposed, after calibrating first, and then hardened by a fresh-context `change-reviewer` round. The row's "`*_guard` tests" selector would have missed 2 of the repo's 3 self-source guards, so guards are selected by behaviour: a test that reads its own file, directly or through a module-level helper or constant. A first corpus run selected on "names `__file__`" and produced 24 false collisions in one plan, all from tests that only locate siblings. The review then found two fail-open shapes, both now pinned. (1) Rebinding `__file__` reached only the test's own globals, so a constant read at import, a helper or a decorated guard read the live file and PASSed. The child now redirects every read of the module's own path to the copy, before the import. (2) Wrapping every block as a string literal hid it from an `ast.parse` guard. The block now goes in verbatim when the module still parses with it, and is reported `WRAPPED:` otherwise. The review also found the attribution misses: template **Production file** blocks were checked against the test file, subproject-relative paths dropped a real block for a guarded module, list-indented fences were invisible, and a brace line printed at import could be read as the child's result. All are fixed. A second round found the static selection still missed four idiomatic own-file reads (`SELF = Path(__file__).resolve()`, `TESTS / "<own name>"`, `Path(__file__).open()`, a class attribute) and three attribution false positives (a new module resolved by suffix onto another sub-project's file, the Production-file rule swallowing helper blocks, a first comment that only mentions a test path). All are fixed and pinned. Selection stays static on purpose: running every fixture-less test to see which reads its file would run most of `test_hmad_dispatch.py` outside pytest, bypassing the conftest that protects the live pin file. Final corpus run over all 26 tracked impl-plans: 22 blocks attributed, 5 of them to a guarded module, 1 collision. It is real, but it was not catchable before RED: `preflight-signal-discipline` prescribed a comment that its OWN new guard bans, and the implementer broke the literal by hand (`tempfile. mkdtemp()`). No false collisions. The catchable case, the pin-agents helper, is reproduced by a test against the live module. 55 tests; `prescribed_block_guards.json` 27/27 ALL_CAUGHT.

## 2026-09-02 — pin-agents-tail-banner phase7

- **live-shape-probe-before-the-gate**: a feature whose contract is "recognise X" must be shown a REAL X, captured from the running system, before any gate scores it clean — recurrence: 1 — candidate: yes — evidence: `pin-agents-tail-banner` passed 2663 tests, 49 mutations, 53 impl-plan audit cycles and two clean audit surfaces while `_agent_tail_re` matched 0 of 5 real agent banner lines; the 12 corpus positives were all idealised. Only the Phase-5f live check found it. The plan records four earlier revisions of the same rule, each falsified by a shape the corpus lacked.
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open, and unwritten anywhere.**
  `grep -rn -i 'live shape|shown a REAL|live check' h-mad/SKILL.md h-mad/invariants.base.md h-mad/references/*.md`
  returns nothing; the only hit in the tree is a mutation-spec fixture name. The rule that cost
  `pin-agents-tail-banner` 53 audit cycles is recorded in this file and nowhere a dispatch reads.
  — **RE-PROBED 2026-10-03: OPEN** — the rule (a 'recognise X' contract needs a real captured X before any gate) is not written in SKILL.md, invariants or references.
  — **LANDED 2026-10-04** — written where every audit dispatch reads it: `h-mad/invariants.base.md` §"Assumption verification" now requires a recognise-X contract's fixture corpus to include at least one sample captured from the running system, with its capture command, and says an idealised fixture is not a sample. Carries this row's 0-of-5 case. Pinned by `test_h_mad_live_shape_invariant.py`; all 26 invariants consumer files pass (1116), prompt-size fixture included.
- **anchored-derivation-breaks-on-an-edited-key-column** (recurrence, not a new row): recurrence 1 → 2 — adding a citation after the AC id broke the per-task `^\| AC-N\.M \|` loop (T2 8/1 instead of 10/1) while the `.*` aggregate still read 45. Same shape as the two rows that briefly carried two AC labels. Cite in the proof column; re-run BOTH derivations after any table edit.
- **concurrent-suite-runs-manufacture-phantom-failures**: two pytest runs over one working tree produced 6 failures and 3 failures in DIFFERENT sets, and 0 when the file ran alone — recurrence: 1 — candidate: maybe — the failures look like regressions and are not; run the repo suite alone before believing any of it.
  — **LANDED 2026-10-05** — the suite takes the tree lock. `h-mad/tests/conftest.py` takes the SAME per-toplevel lock as the mutation harness (`tree_lock`, same holder format, same liveness and stale-take rules) at session start, so a second session over one tree prints `SUITE: BUSY holder=<pid> age=<s> what=<pytest-session|spec> lock=<file>` and exits 75 before collecting; a harness under a suite reads `MUTATION: BUSY … spec=pytest-session`. The harness exports `H_MAD_TREE_LOCK_HELD=<lock>:<pid>` to its children and a session whose token names the lock's live current holder runs, so real spec runs do not refuse themselves. `h_mad_audit_gate.py` reads the refusal as `UNREADABLE reason=suite_busy` and `h_mad_wire_registry.py` as UNREADABLE (it had scored every pin BROKEN); the TDD judge already read it as DENY `no-summary`, so it is pinned, not changed. Separate worktrees never contend. `test_h_mad_suite_lock.py` 11 tests; spec `suite_lock.json` ALL_CAUGHT 6/6. Folds in row `the pytest side of the mutation tree lock`.
  — **RE-PROBED 2026-10-03: PARTIAL** — `006f813b` locks the tree for MUTATION runs (`tree_lock`, `MUTATION: BUSY`); nothing stops a second plain pytest suite on the same tree (`h-mad/tests/conftest.py` has no lock).

  — **RE-PROBED 2026-09-14: PARTIAL.** The finding IS load-bearing in shipped behaviour — `h-mad/SKILL.md`
  §"A red suite blocks the EXIT, not the cycle" cites it as the rationale for the `--exit-check`
  streak. What has NOT shipped is the row's own prescription, "run the repo suite alone before
  believing any of it": nothing refuses a second concurrent run. Its citation was also a line pin
  that was wrong from birth; fixed at `f90a96b` to cite this row by name instead.
## 2026-09-03 — post-merge sweep and handover

- **census-script-needs-a-`__main__`-guard-and-an-import-API**: `handoff/scripts/skill_candidates_census.py` runs `main` at import, so reusing its `rows()`/`ROW`/`TERM`/`CAND` — the correct way to parse that store — requires setting `sys.argv` and redirecting stdout before the import, and exits with a usage error otherwise. That friction is why sessions keep writing ad-hoc parsers, and every one has been wrong: mine returned 270 rows / 101 open against the census's 316 / 125 (the store's rows wrap and do not all use a colon), and two more miscounted on 2026-08-28. — recurrence: 3 — candidate: yes — mechanical: wrap the CLI in `if __name__ == "__main__":` and document the three symbols a caller needs.
  — **LANDED 2026-09-03** — `handoff/scripts/skill_candidates_census.py` (`6bcdd72`): the CLI is now `main(argv=None)` behind an `if __name__ == "__main__":` guard at `:230`, so a bare import runs nothing and raises nothing. `rows()`/`ROW`/`TERM`/`CAND`/`main` are documented as the import API in `handoff/references/automation-scout.md` — beside the census invocation a session actually reads, not only in a docstring. Output on the real store is byte-identical; 4 tests added and 3 mutations; this scout pass used the import API rather than a hand parser. Two pre-existing defects surfaced while verifying: the spec's `test` keys were repo-relative against a `handoff/`-rooted command so the gate reported REFUSED for all 18 and measured NOTHING (now ALL_CAUGHT 21/21), and two anchors were indentation-sensitive.
- **pair-every-hand-rolled-probe-with-a-known-answer-control**: four probes returned false results this session and all four were caught by a control whose answer was known in advance — BSD `head -n -1` (rejected, read as an empty result), a truth table run under zsh (no word-splitting, every row took the same branch and looked consistent), the ad-hoc store parser above, and `grep -Fqx "$l"` where `$l` began with `-` (parsed as an option, every line reported ABSENT). — recurrence: 4 — candidate: **DECLINED** (triage: useful, not codable) — a discipline with no mechanical enforcement; it belongs beside the existing hand-rolled-checks guidance, not in a script. Reopen if a lint could plausibly catch the shell-dialect half.
- **monitor-change-key-must-exclude-monotonic-fields**: a poller that includes an age/elapsed/counter in its change-detection key emits on every interval, because the field moves every interval; written twice in one session (`heartbeat_age_min`, then `commit_age_min` in the replacement gate) and each would have flooded until the harness auto-stopped the monitor, taking the delivery gate down with it. Print the field, decide on it, key on the stable ones. — recurrence: 2 — candidate: maybe — a dry-run-and-count-lines step before arming is the cheap enforcement; a lint would have to understand the loop.
  — **RE-PROBED 2026-10-03: OPEN** — no rule or dry-run line-count step before arming a monitor; the incident is recorded only in a handoff.
  — **DECLINED 2026-10-05 (triage: useful, not codable, calibrated)** — Both recorded instances (`heartbeat_age_min`, `commit_age_min`) come from one session (`2026-09-03-main__post-merge-sweep-and-handover.md:47-48`), both caught before arming; 0 recurrences in about 197 later handoffs across skills and HemaSuite, and no Monitor auto-stop from a flood. Monitor scripts are inline and ephemeral in the tool call with no file to lint, a lint would have to understand the loop's key, and the rule already sits at `docs/learnings.md:212`. Reopen if monitors become file-backed in a shared helper, where a dry-run line-count check belongs.
- **gate-on-two-independent-clocks**: a single liveness/completion signal is a proxy and is routinely wrong in one direction — `phase7_report=YES` fired ~25 min before Phase 7 finished (the artifact is written partway through), and `owner_heartbeat_ts` sat 92–153 min cold while the lane shipped three tasks and a phase transition. Neither `last_completed_phase` alone (a known laggard) nor the heartbeat alone is usable; artifacts-plus-quiescence and heartbeat-or-commits both worked. — recurrence: 2 — candidate: maybe — the general rule is judgement, but an `h_mad` helper answering "is this lane quiet?" from both clocks is codable.
  — **RE-PROBED 2026-10-03: OPEN** — no lane-quiet helper; `fc2ae164` refreshes the heartbeat on `--beat`/owner `--set` (one clock), nothing combines two.
  — **LANDED 2026-10-05** — the codable liveness half. `h_mad_state_ownership.liveness_evidence()` reads four clocks against the ownership window — heartbeat, owner transcript mtime (`projects/*/<session>.jsonl`), newest lane commit, `ps` argv naming the owner (positive-only: absence proves nothing) — and prints `LIVENESS: LIVE evidence=…` on any fresh clock, `QUIET` only when every clock is readable and cold, `UNKNOWN reason=<clock>` otherwise. CLI `h-mad/scripts/h_mad_lane_liveness.py <lane> [--feature F]`, read-only. Consumers: `h_mad_live_runs.py` (a cold-heartbeat claim with a fresh clock is live; a cold one with an unreadable clock is `unjudged` → UNKNOWN, never NONE) and the `--claim` refusal that names force. `owner_is_live` and the `--claim` gate are unchanged. Spec `lane_liveness.json` ALL_CAUGHT 12/12. Live: HemaSuite `MacBookPro` reads `LIVE evidence=transcript:69s,commit:514s,heartbeat:3807s`. Completion gating (`phase7_report` before Phase 7 finishes) stays judgement.
  — **Review residuals, recorded at merge 2026-10-05** — two fresh-context rounds left must=0 and should=3, all known limits rather than regressions against the heartbeat-only check this replaces. (1) The ps clock can still be fooled by an argv that names the session id under a matching flag, such as `grep -r <id>`. (2) The commit clock reads the lane's newest non-merge commit, and a merge can import other sessions' commits into that history. (3) A Codex or agy owner effectively has two clocks, heartbeat and lane commit, because its argv never carries the minted id. Reopen if a false LIVE or QUIET is observed on any of these.
- **triage-must-re-probe-its-OPEN-rows-not-its-CLOSED-ones**: a 17-brief carry-forward triage spot-checked five CLOSED verdicts, all five held, and two false OPEN rows survived a month as "operator decisions" — both had been adjudicated on 2026-08-03, and the row's own cited grep returns the adjudication as its first hit. Verifying closures cannot detect a wrongly-open row, and a false OPEN costs a session while a false CLOSED merely hides a finding. — recurrence: 1 — candidate: maybe — mechanical half: for each OPEN row carrying a cited command, re-run it and diff the result against the row's claim.
  — **RE-PROBED 2026-10-03: OPEN** — `skill_candidates_census.py` counts rows and never re-runs an OPEN row's cited command; READ triage has no such rule either.
  — **DECLINED 2026-10-05 (triage: useful, not codable, calibrated)** — The discipline is already prose in `handoff/references/automation-scout.md` §"Reconcile the open rows FIRST" (`a27118e2`, 2026-08-03), and the open-row re-probe happens in practice (50 `RE-PROBED 2026-10-03` notes, 94 RE-PROBED/RE-CHECKED/TRIAGED/CALIBRATED notes in total). Scanning all 32 OPEN rows found 8 with a backticked command and none a re-runnable probe with a claimed result, so a re-runner has 0 inputs today; recurrence of the original failure is 1. Reopen if rows adopt a machine-readable `probe: <cmd> → <expected>` field (fan-out tooling is tracked as open row 2352).

## 2026-09-03 — doc-block-exec-phase4-and-inbound-handover (scout)

- **`audit-cycle` needs a second-surface mode**: `hmad-dispatch audit-cycle --passes N` dispatches
  `exec agy` for every pass (`hmad-dispatch.sh:2970`), so its default IS the agy+agy configuration
  this repo records as producing false gates. The codex leg — assemble with a `_codex` report path,
  `exec codex`, `collect-report --surface codex`, gate — was retyped by hand **16 times** this
  session, once per cycle, and gating on the union caught a real must-fix in three consecutive
  cycles where agy returned clean. — recurrence: 3 — candidate: yes (a `--surfaces agy,codex` flag
  on `audit-cycle` that dispatches both and reports the union; the pieces all exist, the verb just
  never composes them)
  — **LANDED 2026-09-04** — `hmad-dispatch audit-cycle --surfaces agy,codex` names the agent per pass (`3b6be6d`); the default stays agy-for-every-pass, but a same-surface run now warns on stderr that it is one surface repeated, not a union.
- **an AC count in a paired doc goes stale every time an AC is inserted**: the plan's Success
  Criteria asserted "All N ACs pass" and drifted **three times** in one feature (38→39→40→43), each
  time caught by an auditor rather than by a check, and twice the insertion also broke contiguous
  numbering (`AC-3.8b` before `AC-3.7`). Both are mechanical: re-derive with
  `grep -cE '^  - AC-[0-9]+\.[0-9]+:'` and assert per-FR contiguity. — recurrence: 3 — candidate:
  yes (a `h_mad_ac_census.py` reporting `ACS: OK count=N frs=6` or `ACS: DRIFT`, consumed by the
  audit gate the way `--verify-stamp` is)
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** `h-mad/scripts/h_mad_ac_census.py` does not exist
  and no `ACS: OK` token appears anywhere under `h-mad/`.
  — **RE-PROBED 2026-10-03: OPEN** — no `h_mad_ac_census.py`; the precheck COUNT detector is advisory and its noun list has no ACs. The prose rule is in `measurement-discipline.md` (`1c45944a`).
  — **LANDED 2026-10-04** — `h-mad/scripts/h_mad_ac_census.py <spec> [<paired doc> …]` prints `ACS: OK|DRIFT count=N frs=K`; DRIFT = a stale `All N ACs` claim, a numbering gap or duplicate, or a lettered AC without its base. Calibrated on the committed corpus before wiring (row `calibrate a new detector against artifacts that already passed`): document order fired on 4 audited specs that order by topic, so it is `ORDER (advisory):` only; tagged ACs (`AC-2.1 (layout):`, `AC-3.3 [OD-1]:`) were being missed and are now parsed. Result over 29 specs plus paired docs: one DRIFT, and it is real (`fanout-integrity-and-defects.plan.md` says 34, spec has 35). Consumed the way `--verify-stamp` is: SKILL.md §Precheck tells the orchestrator to run it before a plan/impl-plan audit. Spec `ac_census.json` ALL_CAUGHT 7/7.
- **a doc edit and its version-history bump are not atomic**: an edit heredoc's `assert` failed
  while the two following `h_mad_version_history.py` calls ran anyway, so two documents briefly
  carried `v1.15`/`v1.9` entries describing changes that had not landed. The helper refused
  correctly (`VERSION-HISTORY: UNREADABLE`); the sequencing is what failed. — recurrence: 2 —
  candidate: maybe (an `--after-edit <path> --expect <literal>` guard that refuses the bump unless
  the edit is present, or simply always bumping in the same process as the edit)
  — **RE-PROBED 2026-10-03: OPEN** — `h_mad_version_history.py` has no `--after-edit`/`--expect` guard and no edit-and-bump mode.
  — **DECLINED 2026-10-05 (triage: not-useful, calibrated)** — The "recurrence: 2" is one command sequence hitting two documents in one session (`2026-09-03-main__doc-block-exec-phase4-and-inbound-handover.md:57-61`): zsh did not word-split `set -- $v`, the helper correctly refused with `UNREADABLE`, and the following commands ran because they were not `&&`-chained. 0 further instances in 72 skills and 125 HemaSuite handoffs; the root cause is the separate zsh `set -- $var` row, and an `--expect` flag would not have been on the failing command line. The sibling verify direction (row 1349) gave 0/4 recall with 6 of 6 false misses. Reopen if a second independent session ships a version-history entry for an unlanded edit with the helper correctly chained.
- **`set -- $var` / `$CMD args` silently misfire under zsh**: zsh does not word-split an unquoted
  variable, so a loop passing `"path version text"` gets the whole string as `$1`, and
  `L="python3 script.py"; $L add …` is one command name. Broke three constructs in one session —
  a three-way version bump, a two-way report collector, and a six-call learn loop. Each failed
  loudly here, but the version-bump case wrote nothing while the *next* command still ran. —
  recurrence: 3 — candidate: no (practice, not an artefact: quote the expansion or use an array;
  captured in `docs/learnings.md` and the auto-memory store)

## 2026-09-04 — coder-teammate-audit-surface-and-5b-gating-round (scout)

Reconciled first: census reports 9 open `yes` rows. Four re-verified against source this pass and
all four are genuinely still open — `:1290` audit-cycle second-surface mode (no `--surface` in
`hmad-dispatch.sh`), `:1230` doc-embedded mutation anchor after editing its block (no rule in
`h-mad/SKILL.md`; this session hit the exact defect — a `docsections.json` `replace` naming a
variable the migrated body no longer binds), `:1257` version-history claim vs body, and `:1298` AC
count staleness. `:1298` is the interesting one: the rule it asks for ("counts are derived, never
carried") now exists — but only in `.claude/agents/{design,plan}-author.md`, which is **gitignored**,
so it does not survive a clone and the row stays open. The other five open rows were not
individually re-verified this pass; that is stated rather than left implied.

- **a measured value must carry the commit it was measured at**: hit FOUR distinct ways in one
  session — six `SKILL.md` line pins stale by 93 lines, a suite floor stale by one test (which let
  exactly one pre-existing test be deleted with the guard green), a figure *derived* from a
  measurement (`"three times the 397 s baseline"`) that did not move when the baseline was
  re-measured to 383 s, and two agents disagreeing about a file because each measured it at a
  different instant. A lint over plan/design docs for a bare numeric claim with no adjacent command
  or commit would catch the first three — recurrence: 4 — candidate: yes
  — **RE-CHECKED 2026-09-07 08:30 (scout): PARTIAL, stays open.** Case 1 of the four (stale line pins) IS
  mechanical — `h_mad_precheck_doc.py:93` lists `PINDRIFT` among `HARD_KINDS` and emits it at `:371`;
  it is live right now (`PRECHECK: FAIL issues=19`, 8 of them PINDRIFT). The doctrine landed too
  (`measurement-discipline.md` §PROVENANCE). What the row actually asked for — a lint over plan/design
  prose for a bare numeric claim with no adjacent command or commit — does not exist.
  — **RE-PROBED 2026-09-14: PARTIAL.** The half that is mechanical is the *pin*: `PINDRIFT` in
  `h_mad_precheck_doc.py` (`HARD_KINDS` at `:129`, emitted at `:656`) catches a pin into a file that
  moved since the document's own provenance commit. The half this row actually asks for — a bare
  numeric claim with no adjacent command or commit — is NOT shipped: the only numeric detector is
  `_COUNT_CLAIM` (`:239`), which fires on `N <noun>` **beside a list** and is scored by
  `_list_length_after()`. A figure standing alone in prose, which is the shape this row is about,
  triggers nothing.
  — **DECLINED 2026-10-02 (triage: not useful)** — the pin half shipped as PINDRIFT + measurement-discipline §PROVENANCE; a bare-number prose lint is the shape the calibrate-against-passed-artifacts row warns of and cannot pass a noise floor over the archive.
- **a census without its command drifts unnoticed and cannot be adjudicated**: the plan's
  extractor-census control said "21 `.py` files contain a fence literal"; two readers measuring "the
  same" thing got 3 and 23 because they ran different commands, and the document named neither. The
  fix that ended it was writing the command inline. Same shape as the row above but distinct: that
  one is about *when* a number was true, this one is about *what was counted* — recurrence: 2 —
  candidate: yes
  — **LANDED 2026-09-04** — `invariants.base.md` §"Behavioural premises carry their command" (`55672c5`) requires the command inline beside the output, and cites this row's own 3-vs-23 measurement as the reason.
- **freeze the tree for the duration of a teammate audit round**: a teammate auditor reads the
  WORKING TREE, unlike codex which reads a frozen assembled prompt. Committing mid-round made all
  three auditors return line numbers correct for what they read and mislabelled by the base commit
  they were given, and the orchestrator then relayed the wrong number onward. Belongs as a rule in
  `h-mad/SKILL.md` §5b rather than as a new skill — recurrence: 1 (but cost a full round's numbers)
  — candidate: **LANDED** — `h-mad/SKILL.md:1544`, rule 2 of §"The six rules that are the
  ORCHESTRATOR's, not the author's". Verified by reading the shipped text, not by matching a
  heading: it carries this row's own incident verbatim, `:1897` reported as `e8eaf6f` when it is
  `:1887`, and ends *"Commit before the round or after it, never during."* Cross-referenced from
  `references/measurement-discipline.md` §FREEZE, which pins what "frozen" has to mean. The row
  guessed §5b and the rule lives under the teammate-authors section instead — a different home, the
  same duty, so this is LANDED and not PARTIAL.
- **cross-check any AC that two concurrent authors touched**: three authors running in parallel,
  each correctly measuring, produced two incompatible definitions of one acceptance criterion (25 vs
  30 files). Neither could see it; it surfaced only because the orchestrator read both reports
  against each other. The file-scoping rule (one author, one document) is what keeps this tractable,
  but the cross-check has no home yet — recurrence: 1 — candidate: **LANDED** —
  `h-mad/SKILL.md:1551`, rule 3 of the same six. *"Cross-check any acceptance criterion two
  concurrent authors touched … **This duty has no other home.**"* — the row's closing complaint
  answered in the shipped rule's own words, with this row's 25-vs-30-files incident as its worked
  example. Rule 1 carries the file-scoping premise the row names as what keeps it tractable.
  — **RE-PROBED 2026-09-14: PARTIAL, and the gap is COVERAGE not capability.** The check exists and
  gates: `h_mad_precheck_doc.py:276` `_is_commit()` runs `git cat-file -t` and returns true only on
  `== "commit"`, emitting the hard `UNKNOWNSHA` at `:728`. But `PHASES = ("plan", "design",
  "impl-plan", "spec")` at `:94` is a required argument, so it only ever sees phase documents. A
  backlog row, a handover brief, or an inherited one-liner naming a sha — which is exactly where
  this row's two session-UUIDs-as-commits came from — is outside its reach.
- **`.claude/agents/` is gitignored, so agent definitions do not survive a clone**: four agents
  (`doc-auditor`, `design-author`, `plan-author`, `implplan-author`) now carry measured process
  knowledge — the failure classes that produced this session's findings — and none of it is in
  version control. Already biting: row `:1298` above stays open precisely because its rule lives
  only there. Options are tracking them under `h-mad/agents/` and symlinking, or accepting
  machine-local — recurrence: 1 — candidate: yes
  — **LANDED 2026-09-04** — the five agents are tracked at `h-mad/agents/` and registered by user-scope symlink (`6db8e50`), with the registration step added to §"Bootstrap action" and hardened after a review found it wrote five dangling links on a relative skills symlink (`2eece9f`). A project-scoped copy silently outranks the link, so bootstrap reports one rather than deleting it.
  — **RE-PROBED 2026-09-14: PARTIAL, and closer to landed than the row reads.** The practice now has
  two instances and a stated rationale rather than one docstring:
  `test_h_mad_precheck_doc.py:432` `test_noise_floor_on_documents_that_survived_eighty_cycles`, and
  `h-mad/SKILL.md:1460` applying it to a second detector — "**Calibrated before it was wired**,
  against the 152 records that already existed: every hard rule fires **zero** times on them." What
  is still missing is the row's ask proper: the shape written down where the NEXT detector's author
  will find it, rather than re-derived each time from the two places that did it.
- **verify a backlog reference resolves as a commit before trusting it**: two P3 items cited `cfc79129` and `45db0187` as commits; both are **session UUIDs** and resolve in neither repo, which is why both sat unreproduced for weeks and reached the backlog as vague one-liners — recurrence: 2 (both in one session) — candidate: yes — one command settles it (`git cat-file -t <sha>`) and it belongs at the front of any inherited defect that names a sha. Likely a rule for the handoff/h-mad docs rather than a new skill, since the fix is a habit.
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** `grep -rn 'cat-file -t' h-mad/ handoff/` returns
  nothing. The row itself says the right home is a rule in the handoff/h-mad docs rather than a new
  skill, so this is one sentence of debt, not a build.
  — **RE-PROBED 2026-10-03: OPEN** — nothing runs `git cat-file -t` on an inherited sha; `UNKNOWNSHA` (`h_mad_precheck_doc.py`) covers phase docs only. Lesson only in `docs/learnings.md`.
  — **LANDED 2026-10-04** — as the rule the row asked for: handoff TAKEOVER step 2 (premise verification, which READ Step 3.5 runs too) now says a cited sha must answer `commit` to `git cat-file -t` before it is trusted, with this row's two UUIDs as the example. Pinned by `test_handoff_takeover_mode.py::TestACitedShaIsAPremise`.
- **calibrate a new detector against artifacts that already passed, before wiring it**: every `h_mad_precheck_doc.py` detector written as a hard finding fired 104 / 49 / 48 times on the design and plan that had just passed 83 and 74 audit cycles, and every hit was correct usage — recurrence: 5 detectors in one session — candidate: yes — the reusable shape is: pick a real corpus with labelled defects, assert a noise floor on known-good artifacts, and demote anything that fires on them. Currently recorded only in one script's docstring plus a memory.
  — **RE-CHECKED 2026-09-07 08:30 (scout): MECHANISM landed for ONE detector, the reusable shape still
  owed.** `h-mad/tests/test_h_mad_precheck_doc.py` carries `test_noise_floor_on_documents_that_survived_eighty_cycles`
  — the row's "assert a noise floor on known-good artifacts", mechanized for `h_mad_precheck_doc.py`
  specifically. Nothing generalises it: `grep -rn calibrat h-mad/references/*.md h-mad/SKILL.md`
  returns one unrelated hit (`inline-protocols.md:444`, FR match rate). Still only a docstring plus a
  memory for the NEXT detector's author, which is the row's complaint.
  — **RE-PROBED 2026-10-03: PARTIAL** — done per detector (`test_noise_floor_on_documents_that_survived_eighty_cycles`; H7 in SKILL.md, `4fd01b3c`); no reusable calibration rule in `h-mad/references`.
  — **LANDED 2026-10-04** — `h-mad/references/measurement-discipline.md` §CALIBRATION: run the detector over the committed corpus that already passed, triage every known-good hit (real defect / fix the detector / demote), pin the noise floor with a test. Carries this session's two applications (`h_mad_ac_census.py`, `h_mad_archive_feature.py`) as the evidence. Pinned by `test_h_mad_measurement_calibration_doc.py`.
- **re-measure the audit-prompt size fixture on ANY template or invariants edit**: re-anchored three times in one session (2440 → 2389 → 2329 → 2320) and on two of those three the test PASSED without the re-anchor, sitting 883 B and then 1,381 B under the ceiling — recurrence: 3 — candidate: yes — the fixture's own comment predicted this ("a drift this close reads as a pass right up until it doesn't") and it came true on the very next edit. A check that prints the current margin would replace a judgement call with a number.
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** No check prints the margin. The two `margin`/
  `ceiling` hits under `h-mad/tests/` are the advisor context ceiling (`test_h_mad_advisor_warn.py`)
  and prose in `test_h_mad_assemble_audit.py:212,242` — the size fixture is still a bare re-anchored
  constant, which is the shape the row says reads as a pass right up until it does not.
  — **RE-PROBED 2026-09-14: PARTIAL, and the earlier "still open" was a TIMING artefact, not a wrong
  reading.** The margin is computed and printed:
  `h-mad/tests/test_h_mad_assemble_audit.py:322` asserts `84 * 1024 < mid <= 92_055` with the message
  carrying `margin to the 92,055 B frontier {92_055 - mid:+}B`, and `:318` states the intent —
  "'fixture drifted' alone made every re-anchor a judgement call about how much room was left".
  **It landed at `1c45944` (21:09) and the scout re-checked at 08:30 the same day**, so that
  re-check was correct when made and stale by evening. Residual: an assertion message prints only
  on failure, so nobody sees the margin while it is shrinking — which is the case the row is about.
  — *(moved here 2026-10-02 from the "verify a backlog reference resolves as a commit" row, where it was misfiled)*
  — **DECLINED 2026-10-02 (triage: not useful)** — the margin now rides the assertion message (1c45944, test_h_mad_assemble_audit.py:322); a pass-time print has no reader since a green pytest shows no output.
- **sweep EVERY mutation-spec directory, not the one you thought of**: `--check-anchors` over `tests/specs/` returned `ANCHORS_OK` while two anchors in `tests/mutation-specs/` were drifted and failing the suite — recurrence: 1 — candidate: maybe — `find h-mad -name '*.json' -path '*spec*'` is the whole fix, but nothing makes the two-directory layout discoverable to someone who checks one and stops.
  — **RE-PROBED 2026-09-14: NARROWED, not closed, and the two halves now disagree.** The PUSH
  boundary is covered: `h-mad/git-hooks/pre-push` says in so many words that which specs get swept is
  *"DISCOVERED, not hardcoded"* — it sweeps every tracked `*.json` via `git ls-files` and lets the
  harness's own classifier decide what is a spec, so both directories are reached. The SUITE-level
  check is not: `tests/test_h_mad_mutation_harness.py:1901` is
  `sorted(repo.rglob("tests/mutation-specs/*.json"))`, a hardcoded single directory, and
  `h-mad/tests/specs/` holds two real specs (`audit_cycle_connections.mutation.json`,
  `audit_cycle_gating.mutation.json`) that it therefore never asserts over. So the hazard this row
  names is closed at push time and live in the suite — which is the worse arrangement to leave
  undocumented, because a green suite is what a reader checks first and it is the half that is blind.
  — **RE-PROBED 2026-09-14: PARTIAL.** The verb does not exist. `hmad-dispatch.sh`'s dispatch table
  carries `env|resolve|verify|launch|pin|…|read|wait|alive|…` and no `probe)` arm; all 12 `probe`
  hits in the file are comments or unrelated prose. The documented HAZARDS did land (`ask` takes a
  prompt FILE, its stdout returns the pane mid-render), so a reader is warned but still has to
  hand-roll the loop — which is what produced this row's transposed-digit incident.
  — **LANDED 2026-09-14: the suite half is closed, so both halves now discover the same way.**
  `_committed_mutation_specs()` was `rglob("tests/mutation-specs/*.json")` and is now `git ls-files
  '*.json'` filtered through the harness's own `classify_spec_file` — the identical discovery the
  pre-push hook already documented as *"DISCOVERED, not hardcoded"*. That brings
  `h-mad/tests/specs/audit_cycle_connections.mutation.json` and `…gating.mutation.json` — **19
  mutations** — inside the portability and anchor guards for the first time; they were clean, which
  is why nothing had noticed. `git ls-files` rather than `rglob` on purpose: COMMITTED is the
  property under test and an untracked scratch spec is nobody else's portability problem. Two
  non-vacuity assertions pin it: the old directory must still be in the set, and
  `h-mad/tests/specs/` must be too, so a classifier change cannot quietly shrink the search back.
  This session also made the row's premise concrete a second way — splitting
  `skill_body_renderer_args.json` across `h-mad/` and `handoff/` put committed specs in two
  directories by design, and `run_spec`'s SIBLING precheck still sweeps only `spec_path.parent`.
  That last gap is narrower than this row and is left open deliberately: widening what every run
  prechecks changes which runs return `PRECHECK_FAILED`, which is a behaviour change that wants its
  own measurement rather than a late-session edit.
  — **DECIDED 2026-09-14 (next session): DO NOT WIDEN, and the measurement the deferral asked for
  says why.** The sibling sweep is `spec_path.parent` by **AC-3.5** of
  `anchor-precheck-phase-5e-wiring`, pinned by
  `test_drifted_spec_in_a_different_directory_does_not_affect_run` — so widening reverses a spec'd
  invariant rather than filling a gap. It would also buy nothing: the corpus is now **108 specs /
  980 mutations across three directories** (`h-mad/tests/mutation-specs` 99, `handoff/tests/
  mutation-specs` 7, `h-mad/tests/specs` 2) and `--check-anchors` over all three is `ANCHORS_OK
  980/980`, so **zero runs change verdict today**. The hazard is already closed tree-wide TWICE —
  the pre-push hook's `git ls-files` sweep, and
  `test_committed_mutation_harness_anchor_sweep_is_ok`, which runs `--check-anchors` over
  `_committed_mutation_specs()` (the same `git ls-files` + classifier discovery). That second one
  was **executed, not asserted**: drifting `combine-rc-guard-drop` in `h-mad/tests/specs/` turned it
  RED and restoring the file byte-identical turned it GREEN, so it discriminates and is not a sweep
  passing over an empty set. Against that, widening would couple unrelated skills (one drifted
  `handoff/` spec refusing every `h-mad/` run) and break the design's stated reason for shipping no
  opt-out flag — *"the harness's own tests avoid the precheck by construction — a single-spec
  directory has no siblings"* — because a tree-wide sweep needs a no-repo fallback for every
  `tmp_path` spec, and that fallback makes the AC-3.5 test pass **vacuously**. Residue, stated
  rather than hidden: between a drift landing and the next suite or push, one run in directory A can
  report ALL_CAUGHT while a spec in directory B is drifted. Recorded at `_sibling_specs`'s docstring,
  which is where the single-directory `glob` reads as a bug to the next reader.
- **`hmad-dispatch probe <agent>` — a computed-answer liveness verb scored on `env`'s `last=`**: measured 2026-09-05, `hmad-dispatch read agy` sat frozen on a spinner for 20+ minutes while `hmad-dispatch env` already reported `state=done last="340997"`, the correct answer to an `8317 * 41` probe. A watcher grepping the pane loops forever; two other quirks make this worth wrapping — `ask` takes a prompt FILE not a string, and its own stdout returns the pane mid-render. `candidate: yes`
  — reinforced 2026-09-05: hand-rolled the probe twice; once the match literal was a transposed digit (24265159 vs 24264959) and the loop could never pass — a live agy would have been filed dead (#49l). The verb must derive expected and matcher from ONE expression.
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** `hmad-dispatch` has no `probe` verb — the
  dispatch table at `hmad-dispatch.sh:3815-3835` lists `ask`/`exec`/`read`/`audit-cycle`/`collect-report`
  and no `probe)`; every `probe` hit in that file is a comment. Note for the next reader: the first
  pass of THIS reconciliation grepped `h-mad/bin/hmad-dispatch.sh` (wrong path — the script is under
  `scripts/`) and got a clean zero, which would have read as "landed, nothing to see".
  — **RE-PROBED 2026-10-03: OPEN** — the dispatch table has no `probe)` arm; `h_mad_response_probe.py` measures response shape, not liveness.
  — **LANDED 2026-10-04** — `hmad-dispatch probe <codex|agy> [--timeout <s>]` (orca; default 120 s). One pair of random operands is both the question and the expected answer (`M:PROBE-ONE-EXPRESSION`). It polls `_orca_identity`'s `last=` (the line `env` prints) and never reads the pane. The answer must appear as a whole token. Outcomes are `ALIVE` 0 · `NO_ANSWER` 1 · `UNREADABLE` 2, the last kept apart so an unmeasured agent is never filed as dead. Non-orca substrates refuse before sending anything. Tests: `test_hmad_dispatch_probe.py` (12) uses a fake `orca` that computes the product from the text it is sent, so an expected value that drifts from the question can never read ALIVE. Spec `dispatch_probe.json` ALL_CAUGHT 4/4. Documented in `references/agent-substrate.md`. Not yet run against a live pane.
- **`collect-report` must name the file it actually waited for, or accept `<report-basename>.done`**: measured 2026-09-05, a complete 13.7K gating report returned `COLLECT: MISSING` because the doc-auditor wrote its marker as `..._teammate.report.done` instead of `..._teammate.report.md.done`. The agy leg on the same cycle wrote the correct form, so it fires per-instance and unpredictably. The error names the REPORT path while waiting on the MARKER path, so it points at the wrong object; and `COLLECT: MISSING` is indistinguishable from "the auditor produced nothing", which is already recorded in a committed Version History entry for `plan c83`. `candidate: yes`
  — **LANDED 2026-09-07 (scout)** — `h-mad/scripts/h_mad_collect_report.py:37-44`. The marker is
  `<report>.done`, and `:42-44` adds the near-miss form the doc-auditor emitted (`a.report.md` ->
  `a.report.done`, `with_suffix('.done')`), with `:28` naming the incident in the docstring.
- **`carry-forward-sources` must return the branch's newest NON-handover handoff in addition to pending briefs**: measured 2026-09-05, an inbound handover filed under this branch's slug (`2026-09-05-main__audit-loop-never-runs-repo-suite.md`) became `latest --branch main`, and the real branch predecessor was absent from the source list entirely. A WRITE that had not run READ first would have dropped the whole branch backlog with no error — a new shape of the chain-drops-backlogs defect the field was built to prevent. `candidate: yes`
  — **LANDED 2026-09-07 (scout)** — `handoff/scripts/handoff_paths.py:204 carry_forward_sources`,
  wired as the `carry-forward-sources` subcommand at `:325`/`:357`. Field evidence at HEAD `8ade1e9`:
  this branch's newest handoff names its branch predecessor AND two taken-over briefs in one
  `**Supersedes:**` line, which is the shape the row said was unreachable.
- **a delta-self-review verb (`audit-cycle --delta` or equivalent)**: dispatched by hand six times across two rounds on 2026-09-04/05, identical shape each time — one `doc-auditor` per phase, ADVISORY, subject `git show <sha> -- <doc>` plus the reports that diff answered, reports named OUTSIDE the audit filename grammar so they cannot join the codex-leg ledger. Found fix-introduced musts in 3 of 3 passes at roughly a quarter of a gating round's cost. The naming constraint is the part a verb should enforce rather than leave to the caller. `candidate: yes`
  — **RE-CHECKED 2026-09-07 08:30 (scout): still open.** `audit-cycle` takes `--phase` and `--passes`
  only (`hmad-dispatch.sh:2969-2980`, with `_unknown_opt audit-cycle` as the fallthrough); there is no
  `--delta`. Every `delta` hit in the wrapper is `text_delta` or `tree delta`. Still six-plus hand
  dispatches per round, and the report-naming constraint the row wanted enforced is still the
  caller's to remember.
  — **PARTLY MET, STAYS OPEN — and the line above is the reason this note exists: `e7b97db` landed at
  17:51, NINE HOURS after the 08:30 re-check that called this open, so the evidence above is stale
  rather than wrong-at-the-time.** The row's "or equivalent" is met for the mechanical half:
  `h-mad/scripts/h_mad_delta_review.py` (#11/H4) re-executes the claims a revision ADDS and emits
  `DELTA: CLEAN|CLAIMS|UNREADABLE claims=N executed=E unverified=U`, prescribed as a step at
  `h-mad/SKILL.md:1284` §"Run the delta self-review as a SCRIPT before re-dispatching" and registered
  at `:2664`. **Stays open for two halves the script deliberately does not cover**, and they are not
  the same instrument: H4 checks *claims* mechanically, whereas this row asked to automate a
  `doc-auditor` **dispatch** per phase — so a run of H4 does not answer what a delta auditor answers.
  Second, the naming constraint is still the caller's: there is no `audit-cycle --delta` arm
  (re-verified at `5a6ad11`) and nothing forces a delta report OUT of the audit filename grammar, so
  it can still join the codex-leg ledger it was meant to stay out of.
  — **RE-PROBED 2026-10-03: PARTIAL** — claim half shipped (`h_mad_delta_review.py`, `e7b97db5`, prescribed at `h-mad/SKILL.md:1419`); `_cmd_audit_cycle` still parses no `--delta`. Line pins above are stale (`:1388` is now `:1419`).

  — **RE-PROBED 2026-09-14: PARTIAL, unchanged in substance from the note above and re-verified
  rather than carried.** Shipped: `h_mad_delta_review.py` exists and is a prescribed step at
  `h-mad/SKILL.md:1388` with its own `DELTA:` token. Missing: `_cmd_audit_cycle()` at
  `hmad-dispatch.sh:3163` still parses no `--delta`, so the dispatch half and the report-naming
  constraint the row wanted ENFORCED remain the caller's to remember.
  — *(moved here 2026-10-02 from the "`hmad-dispatch probe <agent>`" row, where it was misfiled)*
- **assembler HALTs on a prompt no surface can accept, and trims Version History with `--vh-tail N`**: candidate: yes · recurrence: 2 real prompts refused by codex (`input_too_large`, 1,123,643 / 1,053,882 chars) while `ASSEMBLE: PASS` was printed and the advisory said "no limit via exec" · VH was ~36% of each doc, embedded for target AND siblings
  — **LANDED 2026-09-05** at `af19d53`: `h_mad_assemble_audit.py --vh-tail N`, `MAX_PROMPT_CHARS=1048576`, `ASSEMBLE: HALT <phase>:oversize`; 5 tests, suite 2552. Owed: SKILL.md 5.5 mention.
- **`hmad-dispatch exec` surfaces `input_too_large` / `turn/start failed` as a distinct token**: candidate: yes · recurrence: 2 codex refusals + 1 agy pytest-timeout all printed the identical `EMPTY final message — agent exited 1` / `tree delta: N` / `rc=1`, so four different causes had one output; the transcript tail carried the exact error each time (#71, #77)
  — **LANDED 2026-09-05** — `h-mad/scripts/hmad-dispatch.sh` `_codex_input_too_large` / `INPUT_TOO_LARGE` branch at `b39d9dc` (7 sites); verified by `git log -S'INPUT_TOO_LARGE'` this session.
- **collect-report / the commit path refuse a report whose first line is `VERDICT: IN-PROGRESS` or whose evidence line reads `0 files opened`**: candidate: yes · recurrence: an early-write stub (`None` ×3, `0 files opened`) overwrote a completed gating report and would have scored CLEAN; the same stub was then committed and pushed under a message describing the real report (#49o, #49q)
  — **LANDED 2026-09-07 (scout)** — the MECHANISM, not only its test:
  `h-mad/scripts/h_mad_collect_report.py` imports `is_unscorable` (`:16`), gates the copy on it
  (`:138`) and prints `COLLECT: INVALID reason=… path=…` (`:143`). Discrimination proven at
  `h-mad/tests/test_h_mad_unscorable_report.py:129-134` — `in-progress-sentinel` and `zero-evidence`
  against a good report AND a stub-describing decoy, so it is not a one-sided pass. Verdict token
  specified at `h-mad/references/measurement-discipline.md:200` (`UNVERIFIED unscorable_report:pN`,
  deliberately distinct from `no_report:pN`).
- **a re-dispatched auditor gets a SUFFIXED report path, never the original's**: candidate: yes · recurrence: two re-dispatches handed the original legs' paths produced one clobber and one near-clobber; both originals were alive and slow, declared dead from a hook's `Running:` set (#49o)
  — **RE-CHECKED 2026-09-07 08:30 (scout): rule landed, enforcement owed — stays open.** The rule is
  verbatim at `h-mad/SKILL.md:1358` ("Never re-dispatch to a report path another agent was handed —
  suffix it") and in `measurement-discipline.md` §COMPLETION SIGNAL (#49o). Nothing MAKES it happen:
  `hmad-dispatch` has no re-dispatch path that suffixes, so the guard is an orchestrator's memory —
  which is the state that produced the clobber and the near-clobber this row records.
  — **RE-PROBED 2026-10-03: PARTIAL** — the rule is written (`h-mad/SKILL.md:1661`, cited above as `:1358`); nothing enforces it: `h_mad_assemble_audit.py --report-file` neither suffixes nor refuses a reused path.
  — **LANDED 2026-10-05** — claim once, never release. `h_mad_assemble_audit.py --report-file` claims the report path AND the prompt path (`--out`, derived from the report path when omitted, never equal to it) with an exclusive create in `$XDG_CACHE_HOME/h-mad/handed` (default `~/.cache/h-mad/handed`), keyed on the casefolded real path, BEFORE writing the prompt. A path that was ever handed, or already exists, HALTs `report_path_handed` and deletes nothing; the only remedy is a fresh RUN. Relative paths and an unwritable claim directory HALT too. The audit-cycle verb mints a fresh `…_run<UTC>-<pid>` stem per invocation, and every hand recipe mints a fresh RP and prompt path per dispatch and echoes them for the later shell blocks. The design took five rounds with fresh-context review. Rounds 1-2 tried to RELEASE finished paths for re-handing (a `.handed` marker cleared by `.done` or collect), and every hole found came from the release: a stale `.done` from the previous holder made a live leg read as finished; a refusal deleted the live leg's prompt; a crashed re-dispatch was credited with the old report; collect could drop a newer claim; the dead-leg remedy re-created #49o. Removing release removed all of them. Unguarded, by design and stated in SKILL.md: dispatches that bypass the assembler (6a-prime, hand-picked `Agent()` paths), sentinel mode, and hand assembly. `report_path_handed.json` 25/25 ALL_CAUGHT; full suite 5738 passed in the worktree.
- **freeze-candidate check runs the documents' OWN closure predicates, not byte-identity**: candidate: yes · recurrence: `af19d53` (assembler only) named as r16 freeze expired a plan interval closure licensing ~70 readings, moved the suite floor 7→12, and moved an impl-plan AST sweep 22→23 — in a doc whose author had already said "no reading moved" (#81). Predicate: `git diff --name-only <base> <freeze> -- h-mad handoff` must be empty, plus each doc's `_SCANNED`-style corpora.
  — **RE-CHECKED 2026-09-07 08:30 (scout): rule landed, predicate not executable — stays open.**
  `h-mad/SKILL.md:1352-1355` states it ("Byte-identical documents is not the predicate") and
  `measurement-discipline.md:160-163` gives the greppable enumeration command. The row's own
  predicate — `git diff --name-only <base> <freeze> -- h-mad handoff` must be empty, plus each doc's
  `_SCANNED`-style corpora — is run by hand every round; no script or verb takes a candidate sha.
  — **RE-PROBED 2026-10-03: OPEN** — rule only (`SKILL.md:1655`, `measurement-discipline.md:178`); no script takes a candidate sha and runs the documents' own closure predicates.
  — **DECLINED 2026-10-04 (triage: useful, not codable — calibrated, same basis as the deferred `expect 0` row)** — freeze-candidate naming is concentrated in one arc: `git grep -l -i freeze -- 'docs/archive/*.md'` counts 55 documents for `doc-block-exec` and 1–3 for each of three others. The census lines the predicate would run are untagged prose spread across six features, and running them would mean extracting shell from free text. The tagged form already has an executor, `h_mad_doc_block_exec.py`. The rule stands as written (`measurement-discipline.md` §FREEZE). Reopen when a second long freeze arc publishes TAGGED census blocks; then this is two `doc_block_exec` runs and a diff.

## 2026-09-06 — doc-block-exec-5b-exit-and-hmad-class-gate

- **run every published `expect 0` screen at the freeze sha before certifying "no census moved"**: three decision-sheet entries (C2 ii, C3 vi, C4 i) certified that a tooling commit moved no scoped census while the design's own published trip-wire read **8** at that commit; nobody ran it. The documents publish these screens with their commands, so a freeze-certification step can execute them. — recurrence: 3 sheet entries in one round, plus #49t/#81 in earlier rounds — candidate: yes
  — **RE-CHECKED 2026-09-07 08:30 (scout): rule landed, freeze-certification step owed — stays open.**
  `measurement-discipline.md:164-165` ("Run every published `expect 0` screen at the sha before
  certifying a freeze") and `SKILL.md:1352-1353` both carry it, and #49w put it in
  `audit-prompt.template.md` + `doc-auditor` 7a. The row asked for the EXECUTION half — "the documents
  publish these screens with their commands, so a freeze-certification step can execute them" — and
  no step does; every round still runs them by hand or skips them.
  — **RE-PROBED 2026-10-03: OPEN** — nothing collects and runs the published `expect 0` screens at a freeze sha. The 2026-09-14 PARTIAL note that sat under this row is about the merged-tree suite; moved 2026-10-04 to `run the full project suite on the MERGED tree`.
  — **LANDED 2026-10-05** — `h-mad/scripts/h_mad_expect_screens.py <docs> --at <sha> --project-root ROOT` reads the documents from the working tree, finds every statement in a `bash`/`sh` fence ending `# expect <N>`, and runs each qualifying block once in a throwaway detached worktree AT the sha (removed on every path; nothing runs in ROOT's tree). Per-screen stdout is captured between markers; a died or looped screen, a pipeline member exiting ≥2, empty or non-integer output, or a timeout is UNREADABLE, never PASS; no tagged screen is `EXPECT: NONE` (exit 3), not PASS. Prescribed in `measurement-discipline.md` §FREEZE; 20 tests; `expect_screens.json` 18 mutations ALL_CAUGHT. Calibration: `doc-block-exec.design.md` at the freeze `0021c77` and at `cac6edc` — `EXPECT: PASS screens=3` (`:2258`, `:2327`, `:3347`, each `got=0`); at `dadaf84` (after the archive move) all three read `UNREADABLE:exit_status=2,…` — the awk member cannot open the moved path, and without the status check each would have printed `0` and PASSED. HemaSuite `website-corpus-root` spec + plan at `6f9562f2`: `EXPECT: FAIL screens=15 failed=0 unreadable=4` — 11 `got=0 PASS`; spec `:748` / plan `:1446` `UNREADABLE:empty_output` (listing-form screens, an empty listing is not the integer 0); spec `:749` / plan `:1447` `UNREADABLE:non_integer` — `grep -rn 'add_argument' cli/ | grep -i 'corpus'` prints three `cli/_parser.py` lines (`--corpus-project-dir` ×2, `--fresh-corpus`), so that published absence claim is false at that sha. **Covers the comment-tagged class only**: the #49w trip-wire itself (`… | grep -vc '^docs/'   # the freeze: prints 8`, design `:300`) carries its expectation in prose and is not run.
  — **REVIEWED 2026-10-05 (fresh-context review of `5cba8c6b`: 5 must, 5 should, 5 nit)** — fixed in a follow-up commit. Statement boundaries now follow bash: a pipe across a trailing comment or a blank line, multi-line quotes, here-documents; `# expect` inside a quoted string is not a screen. The ERR trap records earlier failed commands, and a later screen reads `UNREADABLE:failed_command=…`. SIGTERM/SIGHUP kill the block and remove the worktree. No repo-wide `worktree prune`. `GIT_DIR`-style variables are dropped, and stdin comes from /dev/null. 45 tests; 43 mutations ALL_CAUGHT. Recalibrated: design at `0021c77`, `cac6edc` and `700c599` still `EXPECT: PASS screens=3`; at `dadaf84a` still 3× `UNREADABLE:exit_status=2,…`. HemaSuite spec + plan at `747c1944` now `EXPECT: FAIL screens=15 failed=0 unreadable=15`: every screen follows a `.venv/bin/python` command (spec `:711`, plan `:1430`) that exits 127 in a clean checkout, because `.venv` is untracked. The documents' blocks do not run at a sha as written; that is the reading, not a tool fault.
- **merge tooling that lives under the audited roots only AFTER the last gating pass is collected**: any `h-mad/` commit moves the phase documents' trip-wires and `.py` censuses; the class-gate merge had to wait for r19's three codex legs to land, and the documents are deliberately not re-stamped afterwards. A merge-order check could read the feature's phase + open gating cycle. — recurrence: 2 (this session; `af19d53` at r16) — candidate: maybe
  — **RE-PROBED 2026-10-03: OPEN** — no merge-order check reads other features' open gating cycles; the 7f blocker list has no such reason.
  — **DECLINED 2026-10-05 (triage: not-useful, calibrated)** — Both occurrences come from one feature, doc-block-exec (`af19d53b` 2026-09-05; the r19 class-gate merge), and the hazard needs freeze-sha trip-wires or `expect 0` censuses over the repo the tooling merges into: 1 of 28 archived skills features, 0 of 183 HemaSuite features, 0 recurrences since 2026-09-06. A merge-order checker would guard a population of one finished feature. Reopen if a second feature, in any repo, adopts freeze-sha trip-wires over a tree that tooling merges into while its gating cycle is open.
- **value-grep every shared string across ALL FOUR documents after any REOPEN, not only at first collection**: wave 2's divergence prose became false when the design was reopened after the impl-plan finished; the impl-plan then asserted the opposite of its sibling at three body sites. Collection-time greps ran; reopen-time greps did not. — recurrence: 2 (r18 matrix 85→86, r19 killer name) — candidate: yes
  — **LANDED 2026-09-07 (scout)** — `h-mad/references/measurement-discipline.md` §OWNERSHIP TABLES
  (:263-268): "grep every shared VALUE ... across ALL FOUR documents ... And re-run the sweep after ANY
  reopen, not only at first collection", carrying this row's own wave-2 divergence case as the
  measured example. The row asked for a habit, not a verb, so the rule closes it.
- **run the full project suite on the MERGED tree, not only on the feature branch**: `test_size_warning_fires_before_the_cliff_not_only_past_it` passed in the worktree and failed on merged main because the template it measures grew ~1 KB and is head-duplicated. — recurrence: 1 (measured) — candidate: maybe
  — **RE-PROBED 2026-09-14 (moved here 2026-10-04 from the `expect 0` screen row): PARTIAL, and the shipped half answers the question a better way than the
  row proposed.** `h_mad_phase7_integrate.py:32` argues that when the base is strictly behind,
  `git merge --no-ff` yields a tree byte-identical to the feature tip, so comparing `<base>^{tree}`
  to `<branch>^{tree}` PROVES the existing green run covers the merge — implemented at `:283`
  (`identity = behind == 0`) and re-checked against the real trees after an apply (`:404`). Missing:
  when the trees are NOT identical, nothing runs the suite on the merged result, which is precisely
  this row's measured case.
  — **RE-PROBED 2026-10-03: PARTIAL** — `0fa825c9` proves identity (`h_mad_phase7_integrate.py`, `behind == 0`); when `identity=n` it only prints 'Re-run the suite before 7e' — nothing runs it or blocks 7e.
  — **LANDED 2026-10-04** — `h_mad_phase7_integrate.py --apply --suite "<cmd>"` runs the suite on a NEW merged tree (`identity=n`) and appends `suite=PASS rc=0|FAIL rc=N` to the `MERGED` token; `suite=covered` when `identity=y` (nothing re-runs), `suite=unrun` when no command was given. SKILL.md 7f and `references/phase-table.md` 7e: push only on `identity=y` or `suite=PASS`. Not a hard block inside 7e itself — the push stays the orchestrator's step, now gated on a token rather than a printed reminder. Spec `integrate_merged_suite.json` ALL_CAUGHT 4/4.
- **`${s}:path` not `$s:path` in any per-commit zsh loop**: `$s:h-mad/SKILL.md` parses as the `:h` dirname modifier, so every `git show` read a bogus path and printed 0 — a clean-looking false result that nearly shipped as a finding. — recurrence: 1 (caught) — candidate: maybe
  — **RE-PROBED 2026-10-03: PARTIAL** — recorded as a learning (`a9e69987`) and cited for H4 in SKILL.md; no rule in `measurement-discipline.md`, no lint. Closable as lesson-only.
  — **DECLINED 2026-10-04 (triage: useful, not codable)** — lesson-only: the trap lives in ad-hoc interactive loops, not in files any lint reads; the learning (`a9e69987`) and SKILL.md's H4 citation are the durable form.

## 2026-09-07 — doc-block-exec task4-5e-gates (scout)

Reconciliation pass only — this session is a handoff READ, a claim, and this scout. No new pattern
recurred, so no candidate is appended; fabricating one to make the section look worked is the defect
this file's own header warns about. The 21 `yes` rows re-verified above are the output.

## 2026-09-07 — tooling-backlog-drained-7f-and-91 (scout)

Reconciled first: the census reads `OPEN(yes+maybe)=32` (17 `yes`, 15 `maybe`) over 193 candidates,
and **no `yes` row landed this session**. Two were *followed* rather than shipped —
`calibrate a new detector against artifacts that already passed` (:1417) was obeyed twice, for the
widened `_RATE` and for the parked-spec detector, and `a measured value must carry the commit it was
measured at` (:1376) for every figure in the handoff — but obeying a doctrine row is not landing it,
and flipping one on that basis is how this file's statuses decayed before. They stay open.

- **a tree lock around the mutation harness**: a mutation run and a pytest run over one working tree
  measure each other. This session launched a spec while still editing the files it anchors into, and
  the harness returned `REFUSED` for an anchor that was fine — a verdict about my own torn tree, not
  about the code, and indistinguishable from a real drift at the token. The harness already restores
  the tree on every path, so it knows when it holds it; a lockfile that refuses a second run (and a
  loud `MUTATION: BUSY holder=<pid>`) turns a silent wrong measurement into a wait. Recurrence: 1 —
  candidate: yes — severe, because the failure mode is a *plausible* verdict rather than an error.
  — **LANDED 2026-09-14.** `tree_lock()` in `h_mad_mutation_harness.py`, keyed on the **git toplevel**
  rather than the spec root — two specs rooted at different sub-directories of one repo write the same
  tree, so a root-keyed lock would have permitted exactly this collision while passing every
  single-spec test. A second run gets `MUTATION: BUSY holder=<pid> age=<s> spec=<path>` and exit 2.
  A lock whose holder is proven dead is taken (a crash must not wedge the repo); an UNPARSEABLE one is
  never taken, and the message names the file to delete. `os.kill(pid,0)` raising **EPERM means ALIVE**
  — folding it in with ESRCH steals a live holder's lock, the same defect recorded for `is_pid_alive`
  (#40). `--check-anchors` takes NO lock, so the cheap diagnostic and the pre-push hook (which only
  ever runs `--check-anchors` and scores `ANCHORS_*`) keep working during a run — which is also why the
  new `BUSY` word needed no consumer sweep. 5 mutations, 49/49 ALL_CAUGHT; the first draft of one was
  an EQUIVALENT MUTANT and was retargeted rather than shipped. The INTER-session half of this hazard —
  refuse a run when HEAD moved since the anchors were checked — stays open on its own row below.
- **a closure check that the archive is COMPLETE**: Phase 7c is `mv docs/…/<feature>*`, but for
  doc-block-exec it had moved **6 of 641** files — by copy, leaving the originals live. A merged
  feature's impl-plan therefore stayed in the working population and kept gating live code, and an
  unrelated tooling commit shifting three of its line-pins turned the suite red weeks later. The
  check is one command (`ls docs/0*/**/<feature>.*` after 7c) and the fix is mechanical; the reason it
  was never noticed is that nothing reads the archive for completeness. Recurrence: 1 —
  candidate: yes.
  — **RE-PROBED 2026-10-03: OPEN** — 7c is still `mv … 2>/dev/null || true` with no completeness check, and its glob never reaches `docs/03-analysis/probes/<feature>/`. Live case: `doc-block-exec` leftovers under `docs/01-plan` and `docs/03-analysis/probes/`.
  — **LANDED 2026-10-04** — `h-mad/scripts/h_mad_archive_feature.py` replaces 7c's four `mv … || true` lines (`references/inline-protocols.md` §7c): exact-name matching (`F.*`, `F-brainstorm*`, `probes/F/` — the old `${FEATURE}*` took sibling prefixes), `git mv`, never overwrites, re-checks after moving (`ARCHIVE: COMPLETE|INCOMPLETE|NOTHING`), and `--check` audits any archive. Calibrated on this repo before wiring: a probes dir read by live code is KEPT (`probes/multi-host-runtime/` is read by `test_host_runtime_docs.py`; markdown mentions do not count, and the match is path-bounded so `probes/foo-bar/` is not a reader of `probes/foo/`). Spec `archive_feature.json` ALL_CAUGHT 8/8. **Not cleaned:** `--check` over every archived feature finds 8 with live leftovers (exec-path-hardening 21, gate-blindness-hardening 17, regression-provenance-ledger 30, codex-tdd-gate-defects 20, doc-block-exec 6, grok-codex-fallback 7, pin-agents-tail-banner 116, tdd-gate-fail-opens 19) — removing them is a separate decision. **Decided 2026-10-04: all 8 archived; `--check` now reads `COMPLETE left=0` for each.** The pre-move census looked clean: the two non-markdown hits were a docstring in `test_h_mad_version_history.py` and a captured log fixture. The full suite then found two readers that the census could not see. (1) `probes/multi-host-runtime/rehearsal/cases.json` replays `../../grok-codex-fallback/*.log`, a relative path that never spells `probes/grok-codex-fallback`. `probe_readers` now also searches the probes tree for `../<feature>` with the same path boundary (2 new tests; `archive_feature.json` ALL_CAUGHT 10/10). grok-codex-fallback's probes are back in place and reported `KEPT`. (2) `test_corpus_old_fields_unperturbed` took its corpus from every tracked `*.impl-plan.md` OUTSIDE `docs/archive/`. Once archiving was complete, no live plan carried `shape`/`wire`/`pin`, so the test had only been passing because of leftovers. It now includes archived plans, which only grow. `--apply` moved 164 files after the grok probes were put back. The 65 it refused as collisions were settled one by one against the archive copy: 58 byte-identical live copies were removed. 7 live copies differed, and in every case git ancestry showed the live one was newer: post-archive fixes `c297395f`, `cc40ef2a`, and pin-agents' `9511cd8b`/`6bdcf3f7`. Those 7 replaced their archive copy rather than being dropped. Dated handoffs still cite the old paths; they are point-in-time records and were not rewritten.
- **a fresh-context review of a batch that is already green**: two rounds this session returned
  **12 and 19 findings** on trees where the suite, the mutations and the anchors were all clean —
  three CRITICAL, and two of those caused by the *previous* round's fixes. The reviewer's leverage is
  not finding what tests miss; it is reading each file's own stated doctrine against the change and
  trying the CLI with hostile inputs. Already doctrine in memory
  (`feedback_fresh_reviewer_on_a_green_batch`); a row here so the recurrence is countable.
  Recurrence: 2 — candidate: maybe.
  — **RE-PROBED 2026-10-03: OPEN** — no rule or step; the memory the row cites is no longer in any project memory dir, so its 'already doctrine' premise lapsed.
  — **LANDED 2026-10-05 (triage: already landed, calibrated)** — The 2026-10-03 re-probe looked for the OLD home (memory) and missed the new ones: `docs/learnings.md:122` ("A green batch (suite+mutations+anchors) is the INPUT to a fresh-context review, never its substitute", `735ed9f2`, 2026-09-07) and `h-mad/SKILL.md:3048-3065` §"Teammate change review" with the `h-mad/agents/change-reviewer.md` agent, dispatch block and DONE-gate (`1b8543c8`, 2026-10-04); `docs/learnings.md:16` (2026-10-05) adds fresh-reviewer-after-a-design-pivot. Skipping the review occurred once (`2026-09-10-main__hmad-gates-and-6a-prime-channel.md`), and a pre-push receipt gate would fire on every legitimately unreviewed handoff, backlog and doc push; the codable remainder is open rows 2343 (fresh-reviewer rotation) and 2368 (change-reviewer round driver).

## 2026-09-07 — hmad-fold-and-takeover-mode

- **grep the ENFORCEMENT, not the rule**: five h-mad rules that were correct, measured, argued from
  evidence and written down existed only as prose, each one skippable — the two-consecutive-clean
  streak, the suite gate, the leg set, the author REPORT contract, and the document-audit round cap.
  All five shipped as code in one session (`e54f920`, `a90c365`, `9a31357`, `96fca5f`/`6e1554a`,
  `85fe94a`). The pattern is not carelessness: writing the rule *feels* like shipping it, and nothing
  distinguishes a §section that a script executes from one that only asks — recurrence: 5 in one
  session — candidate: yes — mechanical shape, and it is cheap because the gates already announce
  themselves: every enforced h-mad gate emits a verdict token (`EXIT:`, `DELTA:`, `INTEGRATE:`,
  `PRECHECK:`, `MUTATION:`), so a lint can list each `SKILL.md` section whose text states a gate
  (MUST / refuses / blocks / never) and report the ones with no token and no script reference in the
  §. Output is a list to triage, not a block — some rules are correctly doctrine-only (H8 is, by
  decision). Deliberately NOT "every imperative sentence needs a script": that fires on the whole
  document, which is the noise floor `calibrate a new detector against artifacts that already passed`
  already measured at 104/49/48 hits.
  — **RE-PROBED 2026-09-14: PARTIAL, and the shipped guard is narrower than the row in two ways that
  both matter.** `handoff/tests/test_handoff_takeover_mode.py:224`
  `test_no_positional_shell_arg_survives_in_the_body` does exist and does bite. But its pattern is
  `\$[0-9]` — **no `$@`, no `$*`** — and it reads exactly ONE file, `handoff/SKILL.md`, resolved from
  `parents[1]`. The row asks for the lint over "any `SKILL.md` reachable as a slash command", and
  `h-mad/SKILL.md` — by far the larger body of fenced blocks — is unguarded.
  — **LANDED 2026-09-14 (both gaps), and the `$@`/`$*` half was REFUTED rather than closed.**
  `h-mad/tests/test_skill_body_renderer_args.py` lints BOTH bodies and pins the expander decoded
  from the 2.1.270 binary: `\$ARGUMENTS\[\d+\]|\$ARGUMENTS|\$\d+(?!\w)`, re-derived from the
  binary on every run (SKIP, never pass, when it cannot be read). The old `\$[0-9]` was narrow in a
  direction nobody had noticed — it is blind to `$ARGUMENTS`, the likeliest form — and `$ARGUMENTS`
  carries NO `(?!\w)` guard while `$<digits>` does, so `$ARGUMENTSX` is rewritten and `$1abc` is
  not. `$@`/`$*` are NOT rewritten: the alternation contains neither, and a census of the whole
  image found `\$\*` 0 times and `\$@` 5 times, all inside C#/F# syntax-highlighting grammars.
  `h-mad/SKILL.md:2238`'s `main "$@"; exit $?` is therefore SAFE and linting it would have been a
  change made against the tool's behaviour. Scope deliberately narrowed to this repo's two authored
  bodies — the ~300 vendored `SKILL.md` files use `$ARGUMENTS` on purpose.
- **a positional shell arg in a skill body is REWRITTEN before the agent sees it**: the
  slash-command renderer substitutes the invocation's argument into `$1`, so a documented command
  containing one silently does something else — and the rendered text gives the reader no signal.
  Measured twice on ONE line of `handoff/SKILL.md`: it reached the agent as `…": "read}` under
  `/handoff read` and `…": "takeover}` under `/handoff takeover`, while the file on disk held awk's
  whole-record variable, so the command printed the ARGUMENT instead of the matching line — recurrence:
  2 (one line, two invocations) — candidate: yes — fully mechanical and a one-pass lint: flag `$1`,
  `$2`, `$@`, `$*` inside fenced blocks in any `SKILL.md` reachable as a slash command. The fix is
  already known and applied (rewrite as a heredoc'd python block), so this is a guard against
  regression rather than a design question. Severe out of proportion to its size: the failure is a
  documented command that runs and returns a plausible wrong answer.
  — **RE-PROBED 2026-09-14: PARTIAL, and the split is instance-versus-rule.** (a) LANDED:
  `test_h_mad_audit_leg_set_gate.py:248` `test_two_legs_of_ONE_cycle_are_not_a_streak` builds two
  entries sharing `(feature, phase, cycle)` and differing only by leg, and asserts `not_two_cycles:1`
  — a fixture that can express the collision, which the distinct-by-construction ones could not.
  (b) NOT LANDED: the general rule — *for any gate that counts distinct things, require a fixture
  whose entries collide on the discriminating key* — has no home, so the next such gate starts over.
  — **LANDED 2026-09-14, and SHARPENED: the hazard is bigger than a corrupted line — it is a MODE SWITCH.**
  Observed live comparing three rendered bodies: `/loop` (contains a placeholder) had its argument
  spliced INLINE and no trailer; `/handoff read` and `/caveman ultra` (no placeholder) arrived
  unchanged with `ARGUMENTS: read` / `ARGUMENTS: ultra` APPENDED. Both `handoff` and `h-mad` route
  their mode/verb off that trailer, so one stray `$1` or `$ARGUMENTS` anywhere in either body
  suppresses the trailer entirely and the routing reads no arguments at all. Guard shipped — see the
  note on the row above.
- **a fixture that is distinct BY CONSTRUCTION cannot express the collision it guards**: `exit_check`
  certified a two-cycle clean streak from **one cycle's two legs**, and neither the 2936-test suite
  nor a purpose-written field tracer could see it — both used fixtures that were distinct cycles by
  construction (`v1.gated.json`/`v2.gated.json`, and v43/v44). The gate counts DISTINCT cycles; no
  fixture ever handed it two stamps that collide on the discriminating key, so the property under
  test was never exercised — recurrence: 1 (systemic: the same shape hid the defect from two
  independent instruments) — candidate: yes — mechanical: for any gate that counts distinct things,
  require at least one fixture whose entries COLLIDE on the discriminating key, and assert the gate
  says so. Adjacent to the LANDED `mutation-test-every-guard` (which stubs the guard) and to
  `fix-the-fixture-not-just-the-assertion`, but neither asks the question this one does — whether the
  fixture set can *represent* the failure at all.
  — **RE-PROBED 2026-09-14: PARTIAL.** (a) LANDED and re-confirmed: `anchor_status()` counts with
  `source.count(find)` (`h_mad_mutation_harness.py:695`) and `:958` refuses on `hits != 1`, verdict
  `REFUSED`, exit 2. (b) STILL ABSENT: nothing refuses a mutation whose `find` occurs inside its own
  `replace`. Searched by several spellings over the harness and found nothing. That is the mutation
  that cannot be cleanly reasoned about — the replacement re-contains the anchor, so a second
  application would compound rather than no-op.
  — **LANDED 2026-09-14 as a DIAGNOSIS, and the REFUSAL is refuted by calibration.** The row asked
  the harness to refuse a mutation whose `find` occurs inside its own `replace`. Measured against
  the corpus that already passes: **21 of 874 committed mutations are exactly that shape and every
  one is a legitimate insertion that is caught** — `order = order + order` appended to a sort,
  `default=False,` added to an argparse line, a frontmatter `name:` renamed by suffix. A refusal
  would have taken twenty-one working guards offline to prevent a failure the harness already
  reports (as SURVIVED). What was genuinely missing was the REASON, so `self_matching()` now prints
  a `self-matching:` detail line under `--check-anchors` — the half of the row that truly "needs no
  execution" — and appends the diagnosis to the `mechanism:` line of any survivor, including the
  untargeted branch, which printed a bare name and nothing else. Deliberately on DETAIL lines, not
  the summary: the `ANCHORS:` line is asserted by exact string in the suite and scored by an ordered
  substring `case` in the pre-push hook whose default arm ALLOWS the push. 5 mutations, ALL_CAUGHT
  (44/44 for the spec as a whole). The absent-`find` lint half of this row remains LANDED at
  `h_mad_mutation_harness.py:402`.
- **a mutation that can never fire reads as a passing battery**: six rows this session SURVIVED or
  were REFUSED for reasons that were properties of the SPEC, not of the code — the assertion named
  the *topic* rather than the prescription; the mutation was aimed at a line that never carried the
  property; `shlex.split` meant a canary for an executed redirect could never fire; and one mutant's
  replacement text contained the phrase the assertion greps for (`names no feature`), so the mutated
  tree still matched — recurrence: 6 — candidate: yes — two of the four are a pure spec lint needing
  no execution: refuse a mutation whose `find` string occurs in its own `replace` text (self-matching,
  can never be detected by a grep-shaped assertion), and refuse a `find` that does not occur in the
  named file at all. The other two need the run. `-s` on a file read is an optimisation, not a guard,
  and this row is the reason to say so in the spec schema rather than in a session's memory.
  — **RE-CHECKED 2026-09-10 (scout): one of the two spec lints has LANDED, the other has not — row
  stays open for the missing half.** The absent-`find` lint is live: `h_mad_mutation_harness.py:402`
  computes `hits = source.count(find)` and `:632` refuses on `hits != 1`, so a `find` that occurs
  zero times (or ambiguously, more than once) is `MUTATION: REFUSED`, exit 2 — strictly stronger than
  the row asked for, since it catches ambiguity as well as absence. The **self-matching** lint is
  still absent: three independent patterns (`find … in … replace`, the reverse, `self[-_ ]?match`)
  return NONE across the whole harness, so a mutation whose `find` string occurs inside its own
  `replace` text is still accepted and still reads as caught to a grep-shaped assertion. That is the
  half that produced the `names no feature` survivor this row was opened for.
  — **LANDED 2026-10-02** — `h-mad/scripts/h_mad_mutation_harness.py` §"Why a self-matching mutation is diagnosed and NOT refused" (`8d1edf05`) — advisory diagnosis, not the refusal asked for; calibrated: 21/874 committed mutations self-match, all caught.
- **a count is comparable only at the same COLLECTION ROOT**: the handoff suite read **155** from the
  repo root and **295** from `handoff/` — same commit, same tree, two numbers, because the root-level
  run never collects `handoff/scripts/`, where a real test lives. A floor or a regression check
  written against one of those numbers is silently measuring a different population than the reader
  assumes — recurrence: 1 — candidate: maybe — the mechanical half is small (a doc lint requiring any
  published pytest count to name the directory it was run from) but the general rule is already
  doctrine in `measurement-discipline.md`, so this may be one sentence added to the existing
  §"same commit, corpus and grammar" — the ROOT axis is the part that section does not currently name.
  — **RE-PROBED 2026-10-03: OPEN** — `measurement-discipline.md` §SCOPE has the cd-subdir rule (`#49h`) but nothing naming the collection-root axis.
  — **DECLINED 2026-10-05 (triage: useful, not codable, calibrated)** — `pytest.ini:14` `testpaths` (`e7ddcc2b`, 2026-09-01), `measurement-discipline.md:77-78` (`#49h`), `:95-96` and §UNIT `:336-348` (`2718d48f`, `ce9ffe1b`) already cover the root axis in part; re-measured today with collect-only, `pytest handoff/tests` gives 204, `pytest handoff` 344, `cd handoff && pytest` 344, bare root `pytest` 5738, so the path-argument axis is still unnamed. Cross-root misreadings that mattered: 3 in about 2 sessions, 0 recurrences in 46 skills handoffs since 2026-09-07 (every later recipe says "from the REPO ROOT"); the proposed lint would fire 65 times (103 published counts in 66 files, 38 naming a root within 200 characters) against 0 post-doctrine incidents. The remainder is one sentence in §SCOPE naming the path-argument axis next to `#49h`. Adjacent, not this row: the wire-registry rootdir mismatch (`verify()` at `h-mad/scripts/h_mad_wire_registry.py:676-735`, recurred in HemaSuite 09-01, 09-08, 09-29 and skills 09-30) belongs under HemaSuite's declined `wire-registry-invocation-needs-four-flags` row (`skill-candidates.md:475`), whose reopen condition ("recurs") is met; reopen that row, emitting `reason=rootdir_mismatch:<prefix>` when each missing pin equals a collected id minus a common directory prefix.

## 2026-09-07 — h7-origin-tagging

- **a data fixture floods the delta self-review with claims that are not the revision's**:
  running `h_mad_delta_review.py --rev 4fd01b3` over the commit that shipped H7
  returned `claims=19 executed=4 unverified=15` — and **every one of the 19 came from the 152-line
  JSONL fixture** the commit adds, not from a single line the author wrote. The spans are backticked
  fragments inside other people's finding text (`except pydantic.ValidationError as exc`,
  `grep -o 'git log -S'`), so they are command-SHAPED by construction while being data. Scoping with
  `--path` to the four authored files returns `claims=2`, both the column name `origins tagged`.
  H4's existing filter is about shape (a verb plus an argument) and cannot see this, because these
  really are commands — they are just quoted evidence rather than claims the revision makes —
  recurrence: 1 — candidate: yes — mechanical and narrow: skip added lines that are wholly inside a
  file the commit ADDS whose every line parses as JSON, or more generally treat a fixture/corpus path
  as data rather than prose. `--path` is a workaround the caller must remember, and H4's own row
  (`a delta-self-review verb`) already records that a constraint left to the caller is the half that
  does not hold. Severity is the ordinary one for this family: an alert that is 19/19 noise on a
  commit that adds a corpus gets ignored on the commit where it matters.
  — **RE-PROBED 2026-10-03: OPEN** — `h_mad_delta_review.py` `added_lines()` keeps every `+` line; no fixture/JSON filter.
  — **LANDED 2026-10-04** — `h_mad_delta_review.py` skips a file the revision ADDS whose every non-blank added line is a JSON object or array, printing `skipped data: <path> (N lines)`; the `DELTA:` token is unchanged. Narrow on purpose: an existing file, a file with one prose line, an authored multi-line JSON (mutation spec) and a file of bare quoted strings are all still reviewed. On this row's own commit `4fd01b3`: claims 19 -> 2, the two authored `origins tagged` spans. Spec `delta_review_data_files.json` ALL_CAUGHT 4/4; `delta_review.json` re-anchored to the refactor (ALL_CAUGHT 6/6).
- **a wrapped bold row name is not a row, and COVERAGE cannot see it**: `ROW` is
  `^- \*\*(.+?)\*\*`, so a row whose bolded name wraps before its closing `**` is not matched — it is
  not counted, not censused, and never appears in any open/terminal bucket. Hit while filing the row
  above: it was appended, `git diff` showed 18 inserted lines, and the census read `candidates=201`
  both before and after. **The COVERAGE line cannot catch this**, because `row-shaped` is computed
  with the same single-line regex, so a wrapped row is absent from BOTH sides and the ratio stays a
  reassuring `207/207`. That is precisely the failure the census docstring says it exists to prevent
  ("an unsupported shape reads as an empty backlog"), surviving inside the instrument built against
  it — recurrence: 3 (the row above, plus **two pre-existing rows already in this file**, at the
  `.result.terminal.handle` J1 row and the `handover_landed.py` row, which no census run has ever
  counted) — candidate: yes — two mechanical halves, and the second is the one that matters:
  (a) match a row name across a wrap by scanning to the closing `**` rather than to end-of-line;
  (b) make COVERAGE count `^- \*\*` openers independently of `ROW`, so the two numbers can DISAGREE.
  A coverage metric derived from the same pattern as the thing it audits can only ever report
  agreement with itself. Do NOT reflow the two rows as the fix — that hides the defect and leaves the
  next wrapped row equally invisible.
  ~~**RE-VERIFIED 2026-09-14 (`de50186`): STILL OPEN, both halves.**~~ **THAT RE-VERIFICATION WAS
  WRONG, and it is struck rather than deleted because the way it was wrong is the finding.** It
  argued: `skill_candidates_census.py:30` is still the single-line `ROW = re.compile(r'^- \*\*(.+?)\*\*')`,
  and COVERAGE at `:254` still derives `row-shaped` from that same pattern, so the two numbers
  cannot disagree. Both halves of that are false.
  — **LANDED, and it had already landed a week before I claimed otherwise** — `7cf6803` (2026-09-07),
  *"a wrapped bold row name is a row, and COVERAGE can now disagree with the reader"*, an ancestor of
  the very commit my note cited. (a) `NAME` at `:40` carries `re.S` *"so the name can span the wrap"*,
  and `row_name()` at `:43` joins the body before matching; unclosed openers are collected and
  printed rather than dropped. (b) COVERAGE at `:230` counts with **`OPENER`, not `ROW`**, under a
  comment saying in so many words that the two numbers must be able to disagree.
  **The method error, which is the reusable part:** I grepped for the symbol named in the row
  (`ROW`), found it still present and unchanged at `:30`, and concluded nothing had shipped. `ROW`
  *is* still there — it simply stopped being the thing that answers this question. **Grepping the
  OLD symbol can only ever tell you the old symbol did not change; it cannot see a NEW symbol doing
  the job.** The disproof was one command: a two-row fixture whose first name wraps now reads
  `candidates=2`, and before `7cf6803` would have read `candidates=1`. Executing the property beats
  reading for it, and I read for it.
- **the evidence gate counts tool CALLS, not their TARGETS**: `EVIDENCE: PASS tools=41 ok=41` is
  the same verdict whether a pass opened the module under discussion or spent all 41 calls in
  `docs/`. Measured over 32 paired agy/codex audit cycles on HemaSuite `#18` (analysis:
  `docs/03-analysis/hmad-surface-disagreement-second-mechanism.md`): the disagreement is
  **one-directional** — 27 of 32 cycles disagreed on whether any must existed and **25 of the 27
  are agy-clean-while-codex-files**, two the reverse — and the surviving discriminator is
  code-grounding, not document reading. Controlled to reports that actually filed something and
  scanning only the finding bodies, codex cites a code file in 18/29 (62 %) against agy's 4/14
  (29 %); agy refers to sibling DOCUMENTS *more* (72 % vs 36 %), so the deficit is specifically the
  code. Build-class findings on an impl-plan live in the gap between the plan and the code, so a
  document-only leg passes H6 at `tools=41` and is structurally unable to reach them — recurrence: 1
  feature, 32 cycles — candidate: yes — mechanical half: record per pass the count of DISTINCT paths
  opened, split by documents-dir versus the code the document plans, and surface it beside `tools=`.
  Not a gate yet: one feature is not enough to gate on, and the number is the input any future
  hypothesis needs. **Prerequisite, and it is a defect on its own: the transcript the evidence gate
  scores is not retained**, so no agy log survives to re-audit that `tools=41` — the gate's own
  verdict cannot be checked after the fact, which is why the mechanism above had to be inferred from
  report text rather than from what the leg opened.
  — **RE-PROBED 2026-10-03: OPEN** — `h_mad_review_evidence.py` still prints only tools/ok/failed/thinking; no distinct-path count, and pass `--log`s are still deleted per cycle.
  — **LANDED 2026-10-05** — `h_mad_review_evidence.measure_targets()` counts the distinct EXISTING
  paths a pass's calls named and the evidence line, `CODEXEVIDENCE:` and grok lines print
  `paths= code= other= unmeasured=` after the existing fields when `--project-root` is given
  (absent, never zero, without one; verdicts and exit codes unchanged, pinned by a code=0 test).
  `h_mad_audit_cycle` threads its root into `measure_effort()`, renders the figures beside `tools=`
  in `Effort:`, records them in the `.effort.json` sidecar, and COPIES each pass log to
  `<root>/.h-mad/pass-logs/<collected report>.log` with `log_sha256` (copy failure is advisory:
  `log_retained: null` + reason). Mutation spec `evidence_targets.json`. Three calibration findings
  over 12 real HemaSuite `preflight-command-aware` pass logs changed the design: (1) agy shows
  targets only on ACTIVE `tool` steps' `tool_info.parameters` (`run_command`.`CommandLine` is shell
  text; shell-split, keep existing paths: 0–18 code files per pass, a real signal); (2) the docs/
  count was 0 in all 12 passes because the assembler INLINES the documents, so the split is
  code-vs-other, not docs-vs-code as this row proposed; (3) codex text transcripts print MCP calls
  (`mcp: <server>/<tool> started`) with NO arguments, 7–22 per pass, so they count as `unmeasured`
  and only `exec` blocks are measured. **Remaining open half:** codex targets stay mostly
  unmeasured until codex transcripts are captured as `--json`; `cd` inside a command and paths
  quoted inside inline `-c` scripts are not followed (a known undercount: `code=` is a floor); and
  `.h-mad/pass-logs/` is never pruned. HemaSuite's `.gitignore` does not cover the directory, so
  the driver writes a `*` ignore file into it (review fix, follow-up commit).
  — **Review residuals, recorded at merge 2026-10-05** — two fresh-context rounds: must=0 should=0 at `5aa4817d`; 12 hand-applied fix reverts all caught; the three re-anchored grok rows each caught by their own property assertion. Two nits stay open: no size cap on the scanned transcript, and heredoc bodies are tokenized for path candidates (paths only count when they exist, so this inflates nothing that is absent). Retained pass logs under `.h-mad/pass-logs/` have no rotation yet.
- **`HARD_KINDS` is defined and read by nothing, while two tests spell the same set as literals**:
  `h_mad_precheck_doc.py:93` declares `HARD_KINDS = ("PLACEHOLDER", "LINEPIN", "PINDRIFT",
  "UNKNOWNSHA")` and no code path reads it — the verdict is `"FAIL" if findings else "PASS"`, so
  hardness is decided solely by whether a hit is appended to `findings` or to `advisories`. Found by
  mutation: a row that dropped `PINDRIFT` from the constant SURVIVED, and the survival was correct —
  the constant is inert, and the `_mechanism` I had written for that row ("the verdict silently
  becomes PASS") was a property I asserted without executing — recurrence: 1 — candidate: yes — the
  danger is not the dead line, it is that a constant with an authoritative NAME reads as the source
  of truth for anyone changing the detector set, so a future edit to it is silently a no-op while
  looking like a policy change. Two mechanical options: make the script read it where it builds the
  two lists, or delete it. As of 2026-09-07 the tests import it (`set(HARD_KINDS)` and
  `set(HARD_KINDS) - {"PINDRIFT"}`) so the name has one consumer and the two filters cannot drift
  apart, but the script still does not consult it — that half is open.
  **RE-VERIFIED 2026-09-14 (`de50186`): STILL OPEN, and the premise is sharper rather than merely
  unchanged.** The #29 review's `hard()` router DID land — `h_mad_precheck_doc.py:489`, a real emit
  router used at six sites — so the *adjacent* half closed while this half did not. `HARD_KINDS` now
  sits at `:129` and the script's only other occurrence of the name is `:105`, **inside a comment**:
  no executable line reads it, and nothing validates `hard()`'s `kind` argument against it, so a
  typo'd kind still emits. That is exactly the hazard the row names — an authoritative-looking
  constant surviving the very refactor that rewrote its neighbours.
  — **RE-PROBED 2026-10-03: PARTIAL** — the tests import `HARD_KINDS`; the script defines it (`h_mad_precheck_doc.py:129`) and `hard()` still never checks `kind` against it.
  — **LANDED 2026-10-04** — `hard()` now raises `ValueError` for any `kind` not in `HARD_KINDS`, so the constant drives the script and a typo'd kind cannot emit. Test `test_hard_refuses_a_kind_HARD_KINDS_does_not_list`; spec `h-mad/tests/mutation-specs/precheck_hard_kinds_enforced.json` ALL_CAUGHT (guard removed; guard checking a literal copy).
- **structure the 6a-prime archreview reports before any code-phase instrument is built**: measured
  across the 28 archreviews in HemaSuite (analysis:
  `docs/03-analysis/hmad-code-phase-ledger-not-warranted.md`) — median **2,114 B**, `Major` appears
  **0** times in any of them, and 14 of 28 carry no `READY_TO_MERGE`/`WITH_FIXES`/`NO` token in their
  text at all. The verdict survives only because the orchestrator extracts it into state, which
  `h_mad_phase7_preconditions.py:192` then reads fail-closed — the reports themselves are not a
  parseable surface — recurrence: 1 (28-report corpus) — candidate: yes — mechanical and small: give
  the archreview a required token line the way every other h-mad surface has one, so a report can be
  scored without a human reading it. This is the PREREQUISITE the code-phase ledger row was blocked
  on, and it is worth more than the ledger: a 2 KB free-prose report is the input no later instrument
  can use.
  — **LANDED 2026-09-10** — `h-mad/references/agy-architectural-reviewer-prompt.md` §"Report Format
  (REQUIRED — orchestrator parses this)" now carries the required token line and the refusal ("reads
  the LAST line that begins with `ASSESSMENT:` and refuses a reply that has none"), with the three
  words as a stated CLOSED set and three unfenced literals as the tail (`322a179`, form fixed at
  `84d4677`). The report is scoreable without a human: `h_mad_archreview_cycle.py:94-100` extracts the
  LAST `ASSESSMENT:` whose value is in the allowed set, and `d5d1763`/`e30e54f` gave 6a-prime a
  report-file channel (`<INLINE_REPORT_FILE>`) whose head-prepended contract repeats the three
  literals — so the surface the row called "not parseable" now is. Verified against source, not the
  label. The row's own dependant (the code-phase ledger, below) stays DECLINED on its own measurement.
- **the code-phase ledger itself**: the same origin-tagging instrument applied to Phase 5–6
  artifacts. — candidate: **DECLINED 2026-09-07 (triage: useful, not codable)** — measured out
  rather than deferred: **2 of 136** archived features ever ran a second Phase-6 analysis, so the
  code phase does not loop and there is no tail to tag. `#46 grounding-evidence-coverage`, the
  candidate named for having the strongest code-phase evidence, carries **71** document audit cycles
  against **3** Phase-6 analyses and **0** archreviews — about 24:1. A rate computed over
  single-digit events spread across months moves by whole percentage points on one record. Revisit
  only if 6b iterate rounds become routine; the row above is the prerequisite either way.

## 2026-09-10 — hmad-gates-and-6a-prime-channel (resume session)

**Reconcile of 2026-09-10 — census read `candidates=209 OPEN(yes+maybe)=45 yes=28 maybe=17` before
this pass; 28 open `yes` rows, of which 8 were probed against source.** Probed the subset the nine
commits `cf39879..e30e54f` could plausibly have closed, since those touched
`h_mad_version_history.py`, `h_mad_precheck_doc.py`, `h_mad_review_evidence.py`,
`h_mad_archreview_cycle.py` and the agy archreview prompt. Result: **one flipped to LANDED**
(`structure the 6a-prime archreview reports`), **one annotated half-landed** (`a mutation that can
never fire` — the absent-`find` lint shipped, the self-matching lint did not), and **six re-verified
still open against source rather than against their labels**: `grep the body for a version-history
entry's claim` (`h_mad_version_history.py` still has no `--verify`, only `--dry-run`, which verifies
the WRITE not the entry's claim); `calibrate a new detector against artifacts that already passed`
(the noise-floor test exists for `h_mad_precheck_doc.py` alone; nothing generalises it);
`grep the ENFORCEMENT, not the rule` (no lint script); `a positional shell arg in a skill body is
REWRITTEN` (fix applied to `handoff/SKILL.md`, regression lint never written);
`the evidence gate counts tool CALLS, not their TARGETS` (`h_mad_review_evidence.py:240` still prints
`tools=`/`ok=` only, no distinct-path split); `HARD_KINDS is defined and read by nothing`
(`h_mad_precheck_doc.py:93` still unread by any code path — only the tests import it). The remaining
20 open `yes` rows were NOT probed this pass and keep their prior status; do not read this block as a
full reconcile of the 28.

- **a census of REAL agent verdict tokens across the archived report corpus**: closing #34 required
  answering "does codex actually emit a literal `STATUS:` against this template, or does it echo the
  fenced schema?" — and the only evidence was two report files buried in `docs/archive/**`
  (`audit-report-docs-copy.5e-verify.tasks1-4.codex.md` → `STATUS: DONE`,
  `doc-block-exec.task3-red.report.md` → `STATUS: DONE_WITH_CONCERNS`, both extracting rc=0, and zero
  reports anywhere echoing `STATUS: <DONE | …>`). Nothing indexes that corpus, so a question about a
  surface's real-world reliability costs a `find`+`grep` excavation every time it is asked, and the
  deferral it settles had stood since the sender parked it — recurrence: 1 (but the corpus is the
  standing answer to a recurring class of question) — candidate: yes — mechanical: walk
  `docs/archive/**` + `docs/04-report/**` for report files, run each through
  `h_mad_extract_verdict.py`, and print a per-surface table of token / value / extraction-rc. It is
  the empirical half of every "is this prompt shape safe for agent X" argument, which this repo
  currently settles from shape and memory.
  — **DECLINED 2026-10-02 (triage: not useful)** — single use; the question it answered (#34) is closed, and the census is a find over docs/archive piped through h_mad_extract_verdict.py when next needed.
- **a backlog row should name the test that would REFUSE its proposed edit**: #34 proposed rewriting
  the two codex templates' fenced-schema exemplar. `h-mad/tests/test_h_mad_prompt_tails.py:36-50`
  PINS that exact tail for both templates, and its docstring already argues the deferral's reasoning
  ("NOT measured to fail on codex … Rewriting a prompt that demonstrably works, because it shares a
  shape with one that does not, is the failure mode this repo documents elsewhere"). So the suite
  would have refused the edit, and the argument against it was already committed — but nothing links
  the row to either — recurrence: 1 — candidate: maybe — a general "find the test that pins this
  file" lint is the noise-floor trap (`calibrate a new detector…` measured 104/49/48); the cheap
  version is a convention, not a script: when a row proposes editing a file under `references/`,
  grep `tests/` for that filename and cite what it finds in the row.
  — **RE-PROBED 2026-10-03: OPEN** — `handoff/references/automation-scout.md` §Where to write has no 'grep tests/ for the file' line.
  — **DECLINED 2026-10-05 (triage: not-useful, calibrated)** — The protective half landed after the 2026-10-03 re-probe in a symbol it could not have grepped for: `h-mad/scripts/h_mad_doc_consumers.py` (`cfe82dbd`, 2026-10-04), wired as an advisory hook at `h-mad/git-hooks/pre-commit` and installed here; on the row's own case it prints `CONSUMERS: … n=14` and `n=7`, both including `h-mad/tests/test_h_mad_prompt_tails.py` (`:52-55`), the test that would refuse the #34 rewrite, and ends with a runnable `RUN:` line. The filing-time convention in `handoff/references/automation-scout.md` is still absent, but recurrence is 1 in 37 skills and 89 HemaSuite handoffs since 2026-09-10, and no other row had an edit an existing test would refuse. Reopen if a row's pinned-file edit is again proposed blind and the commit-time consumers hook did not name the refusing test.
- **measure an instruction's position with the extractor's own rule, not `find`**: measuring how far
  from the end the 6a-prime/codex verdict line sits, I used first-match and reported 90.6% when the
  contract line was at 99.9% (tail-distance 66 chars) — a 4 KB error in the direction that made the
  prompt look safer than it is. Every h-mad contract is explicitly "the LAST line that begins with
  X", so first-match is measuring a different thing than the parser reads — recurrence: 1 — candidate:
  maybe — too small for a script and it names no recurring surface; the reusable half is a line in
  `measurement-discipline.md`, which already carries this class ("a count is evidence only at the same
  COMMIT, CORPUS and GRAMMAR" — this is the GRAMMAR case, applied to a position rather than a count).
  — **RE-PROBED 2026-10-03: OPEN** — `measurement-discipline.md` §GRAMMAR covers counts and sweeps, not positions.
  — **DECLINED 2026-10-05 (triage: useful, not codable, calibrated)** — The surface it worried about is now pinned mechanically: `h-mad/tests/test_h_mad_prompt_tails.py:52-73` asserts the verdict line is the LAST lines of each parsed-verdict template (`322a1793` 2026-09-07, `84d46775` 2026-09-09), and `h-mad/scripts/h_mad_extract_verdict.py` reads last-match. A search over both handoff dirs and both learnings files hit 14 files, none this failure (`grep -q` SIGPIPE, hook dedupe, a HemaSuite domain resolver bug); recurrence is 1, one hand measurement on 2026-09-10. At most one `measurement-discipline.md` §GRAMMAR sentence ("a contract read last-match is measured last-match"). Reopen if a second hand measurement of an instruction's position disagrees with the extractor.

## 2026-09-13 — fresh-review-lanes-and-the-wsg-takeover (second pass, same session)

**Second scout block for one session, deliberately.** The first ran mid-session and reconciled the
open rows (209→212, one flipped LANDED, one annotated half-landed, six re-verified, 20 unprobed).
Everything below came from work done AFTER it, so it appends only — the reconcile above still
stands and was not re-done. Census unchanged at `candidates=212 OPEN=47 yes=28 maybe=19`.

- **a per-mutation kill CLASSIFIER in the harness**: the harness cannot distinguish a mutant that
  died on a crash or timeout from one a guard caught — its own docstring says so (`:58-61`, `:625`,
  `:934`) — and the sole mitigation is the spec author remembering a `test` key. TWICE this session
  a battery reported `ALL_CAUGHT` while carrying a mutation nothing detected, both found only by
  re-scoring against the named key — recurrence: 2 this session plus the inherited WSG-4 finding
  and the older "6 of 11 guards bit nothing" measurement — candidate: yes — mechanical: classify
  the kill (assertion / crash / timeout / unrelated-failure) and report it, so a spec WITHOUT a
  `test` key is visibly untrusted rather than silently trusted. This is the same row the inbound
  WSG brief files as its item 4; recording it here so the candidate store carries it independently
  of that brief's lifetime.
  — **LANDED 2026-09-14** — `h-mad/scripts/h_mad_mutation_harness.py` §"crash-kill classification"
  (`66cb2e7`), corrected in `5289fc1` after a full 92-spec sweep found the classifier failing the
  OTHER way: pytest's `<file>.py:N: AssertionError` footer read as a crash whenever the mutated
  file is a test file, manufacturing 12 of the corpus's 25. Both directions are now guarded and
  both blind spots are documented in the function's own docstring.
  — **BOTH BLIND SPOTS NOW CLOSED 2026-09-14 (`64b3752`), and "documented" turned out to be the
  wrong resting place for them.** The docstring called each permanently unclassifiable; on re-reading,
  its reasoning was right about ATTRIBUTION and wrong about LOOKING, which is the reusable half:
  *unattributable* and *unreportable* are different, and a measurement that cannot say WHICH file can
  still say THAT it happened. (1) `timeout_kill` returns an **unattributed** name — pytest blames the
  test file that set the timeout, never the module that hung, so widening `_TERMINAL_LINE` would have
  manufactured a false attribution and that objection is preserved — published as `timeout_kills=N`,
  never folded into `crash_kills`, whose every entry names a file. It earns a separate count because
  it is the kill least likely to be the guard biting: a guard that fires *returns*, it does not hang.
  (2) The untargeted branch now runs the same `crash_kill` basename check, whose rule is no weaker
  without a named test, and `untargeted=N/M` reports how much of a verdict rests on the weaker
  question. **Two defects in the fix were caught by the harness itself on the first run and are
  recorded in `tests/mutation-specs/harness_blind_spots.json` rather than quietly repaired**: a
  `timeout_kills=2` FALSE POSITIVE matching fixture strings that pytest echoed into a failure block —
  the very hazard the docstring documents for `Traceback`, walked into by its own author — and a
  mutation that survived because no test asserted the property it stripped. 8 mutations, ALL_CAUGHT.
- **a "starting state the suite never reaches" prompt when a mutation SURVIVES**: both surviving
  mutations this session shared one shape — every existing test began from a state where the weak
  mutation still looked caught (no stamp on disk makes a size-only signature look correct; one
  filename stem makes a missing path-boundary look correct) — recurrence: 2 — candidate: maybe —
  not a script: the mechanical half is already the harness telling you which mutation survived. The
  reusable half is a QUESTION to put in the survivor's output ("what starting state does no current
  test reach?"), which is a one-line change to the `survived:` message rather than a new instrument.
  — **RE-PROBED 2026-10-03: OPEN** — the SURVIVED message in `h_mad_mutation_harness.py` does not ask about a starting state the suite never reaches.
  — **DECLINED 2026-10-05 (triage: useful, not codable, calibrated)** — The mechanical half exists: the SURVIVED text (`h-mad/scripts/h_mad_mutation_harness.py:2001-2007`) plus a per-survivor `mechanism:` line (`:1959-1962`, `SELF_MATCHING_NOTE` `:720-727`, `8d1edf05`). The starting-state shape appears in 1 skills session (`2026-09-13-main__fresh-review-lanes…md:27-30`, 2 survivors) and 1 arguable HemaSuite sibling (2026-08-08), both caught because the harness reported SURVIVED. The 10-04 full sweep (145 specs, 3 SURVIVED) had three different causes (a test that cannot see its mutation, a substring elsewhere in the tail, a host-bound equivalent), so a fixed question tuned to one cause would be wrong for two of three, and no check can tell a starting-state cause from the others. If wanted, a one-line wording change at `:2001-2007` needs no backlog row; reopen only if survivors repeatedly trace to a starting state the suite never reaches.
- **measure a gate instead of inferring it from commit prose**: a lane-watcher built on commit
  subjects produced four false readings (`close` matching "closeout"; non-monotonic progress; `HEAD`
  standing in for a branch ref; stall on a finished branch), while the correct signal was one
  read-only command — `h_mad_phase7_integrate.py` without `--apply` returns the real INTEGRATE
  verdict and touches nothing — recurrence: 4 failures against 1 correct instrument, one session —
  candidate: maybe — too situational for a script, but the rule generalises: when a phase tool has a
  plan-only mode, the plan-only mode IS the state query, and inferring the same state from prose is
  strictly worse. Belongs in `measurement-discipline.md` rather than as a new skill.
  — **RE-PROBED 2026-10-03: OPEN** — no rule naming a plan-only mode (e.g. `h_mad_phase7_integrate.py` without `--apply`) as the state query.
  — **DECLINED 2026-10-05 (triage: not-useful, calibrated)** — The plan-only state query exists (`h_mad_phase7_integrate.py` without `--apply`, `h-mad/SKILL.md:325`; `h_mad_archive_feature.py --check`), and `h-mad/scripts/h_mad_live_runs.py` (`10e132af`, 2026-10-04) answers lane liveness from one clock. The broad class (a proxy read as the gate) hit 3 skills sessions (09-03, 09-05, 09-13), but the specific failure, commit prose standing in for a phase tool's verdict, occurred once (09-13) and 0 times in 35 skills and 68 HemaSuite handoffs since; watchers are inline and ephemeral so there is nothing to lint. Fold the rule into the lane-liveness build (`gate-on-two-independent-clocks`) as a design requirement: phase state comes from tool tokens (`INTEGRATE:` from a plan-only `h_mad_phase7_integrate.py`, `docs/.bkit-memory.json` via the `owner_is_live` rule), never from commit subjects. Reopen if a watcher again reads commit prose as a gate after that build ships.

- **a hollow-kill detector — "did the mutant REACH the property?"**: the crash-kill classifier says
  — **still open, but ADVANCED 2026-09-14 (`43c0cc6`)**: the harness now publishes `crash_visible=M/T` beside `crash_kills=N`, so a zero can no longer be read as absence — and on its first run it surfaced a real hollow kill (a mutation dying on `NameError` because a port had removed the name its replacement used). That is the DENOMINATOR, not the detector this row asks for: knowing a mutant crashed still does not tell you whether it reached the property. Recurrence 1 → 2.
  a mutant died on an exception; it cannot say whether the exception was the guard firing or the
  mutant failing to run at all. Measured 2026-09-14 over all 92 specs: of 12 genuine crash kills,
  **4 were HOLLOW** — a kwarg that does not exist (`TypeError`), a function never written
  (`NameError`), a deleted regex group (`IndexError: no such group`), a half-applied stringification
  (`TypeError: '<=' not supported between int and str`). Each guard asserted a property its mutant
  never reached, and each read as `caught`. Recurrence: 4 in one sweep, plus the WSG-4 finding and
  the older "6 of 11 guards bit nothing" — candidate: yes — mechanical: after applying a mutation,
  import/compile the mutated module and execute the named test's target path once; report
  `REFUSED reason=mutant_does_not_execute` when the exception's traceback never enters the guard.
  The four here were all distinguishable by reading the message the test dies on, which is a
  mechanical string check, not a judgement.
  — **RE-PROBED 2026-10-03: PARTIAL** — `crash_visible=` landed (`43c0cc6`) and four hollow specs were fixed by hand (`32789ad9`); tier 2 still counts every crash as caught and never refuses `mutant_does_not_execute`.
  — **INSTRUMENT ADDED 2026-10-04, refusal not wired** — `--sweep` now forwards every crash/timeout kill as `  kill: <spec> :: <mutation> :: crash: <Exception> in <file>`, which is the corpus-wide reading the refusal needs calibrating against (row `calibrate a new detector against artifacts that already passed`). The 2026-09-14 hollow four were fixed by hand, so the current corpus's crash kills are unmeasured; wiring `REFUSED reason=mutant_does_not_execute` on message signatures (`NameError: name … is not defined`, `unexpected keyword argument`, `no such group`) before reading them would risk refusing a crash that IS the property violation, which tier 2's own comment warns about. Next: one detail sweep, triage each `kill:` line, then wire.
  — **FIRST FINDING FROM THAT INSTRUMENT, FIXED 2026-10-04** — the detail sweep's kill lines showed `audit_effort.json :: empty-log-renders-as-zeros` counted `caught` with `crash: IndentationError`. Tier 1 (a mutant that did not PARSE measured nothing) applied only on the TARGETED path; an untargeted unparseable mutant turned the whole suite red and scored as a kill. The harness now refuses it on both paths (`test_an_untargeted_mutation_that_stops_the_file_parsing_is_refused_not_caught`, row in `harness_blind_spots.json`). The spec row itself was hollow — its anchor had been narrowed to a `return` line while its replacement still opened with a 4-space `if` — and now measures the guard (ALL_CAUGHT 14/14, by a real test).
  — **CALIBRATION READING 2026-10-04 (full sweep at `cfbd2517`, 145 specs: 142 ALL_CAUGHT, 3 SURVIVED, 0 unmeasured)** — 24 forwarded kills: 18 crashes (`KeyError`, `ArgumentTypeError` x2, `ZeroDivisionError`, `UnicodeDecodeError`, `ModuleNotFoundError`, `SpecError`, `StateWriteError` x4, `TypeError` x2, `OverflowError` x2, `RegistryError`, `IndentationError` x2) and 5 timeouts. NONE carries the three signatures this row proposes refusing (`NameError … not defined`, `unexpected keyword argument`, `no such group`); the only hollow kills were the two `IndentationError`s, now refused by tier 1 on both paths. Most crashes are the guard's own exception (e.g. `StateWriteError` IS the refusal under test), which is exactly the tier-2 ambiguity. So the message-signature refusal would currently fire on nothing: keep it unbuilt until a sweep shows a signature hit, and re-read the `kill:` lines on each full sweep. The 3 survivors: 2 fixed (`02dbd0ee`, `4e591612`), 1 host-bound equivalent (`5089bb92`).
- **a corpus-wide mutation sweep verb (`--sweep`)**: the harness scores one spec per invocation, so
  "what does the whole corpus report?" is a hand-rolled shell loop nobody runs. It had covered 11
  of 92 specs; completing it on 2026-09-14 found 25 crash kills (12 of them an artifact), 2 SURVIVED
  and 1 REFUSED — three guards that did not bite, invisible for as long as the sweep was partial.
  Recurrence: 2 (this session's loop, plus the 11-spec sample it replaced) — candidate: yes —
  mechanical: iterate the spec set, print one token line per spec plus a corpus summary, and REFUSE
  to run concurrently with another harness process in the same worktree (see the tree-lock row
  above — false anchor drift was self-inflicted three times on 2026-09-14 for exactly that reason).
  — **RE-PROBED 2026-10-03: PARTIAL** — the tree lock landed (`006f813b`); `main()` still refuses more than one spec for a run — only `--check-anchors` sweeps.
  — **LANDED 2026-10-04** — `h_mad_mutation_harness.py --sweep [SPEC…]` (every committed spec when none is given) runs each spec as its own process under its own tree lock, prints one `SWEEP: <spec> <verdict>` line each and a corpus summary (`ALL_CAUGHT|NOT_ALL_CAUGHT … unmeasured=U`, `NOTHING_SWEPT`, or `INCOMPLETE` when BUSY/TREE_MOVED stops it). Exit 0 only when every spec measured something. Spec `harness_sweep.json` ALL_CAUGHT 5/5. A full-corpus run has not been made yet.

## 2026-09-14 — bkit-hooks-warning-and-upgrade (second session, same day)

Reconciliation note: the census reads OPEN(yes+maybe)=51 (30 `yes`). Those rows were reconciled by
the immediately-preceding session, whose pass is the file's last write (`ec75688`). `git log
ec75688..HEAD` is **empty** and this session committed no source to this repo, so no open row can
have changed state since — the decay this step exists to catch cannot have occurred in the interval.
Rows re-read for relevance to this session's work (the crash-kill/`--sweep` pair at lines 1843 and
1855): neither is touched by it. No row flipped.

- **which diagnostic surface shows which warning**: reproducing `bkit: hooks.json: unknown key …`
  — **SUPERSEDED 2026-09-14** — the question is retired rather than answered: the warning is a pure function of `hooks.json`, so the CC binary's own validator constants (`yko`/`_ko` at 2.1.270 offset ~169081421, byte-identical to 2.1.268) can be REPLAYED offline over every installed plugin, with the pre-patch backup as a negative control. No diagnostic surface is needed. The replay is still only in a session scratchpad — see the `plugin-hooks-validator-replay` row below.
  cost five probes — `claude -p`, `--debug`, `--debug hooks`, `plugin details`, `plugin validate` —
  all silent, because the warning renders only on the interactive TUI warn surface and
  `plugin validate` runs a *different* validator (unknown **events**, not unknown **keys**). A
  lookup of "this class of diagnostic appears on these surfaces" would have cost one. — recurrence: 1
  this session, but the same shape as the agy TUI-capture and `--help`-is-the-command-surface rows
  already in this file — candidate: maybe

- **decode a closed key-set from the shipped binary, then replay it as a local validator**:
  `strings` on the CC binary yielded `qdo=new Set(["description","hooks","modules","surface"])` and
  the matcher set `{matcher,hooks}`; replaying them over the pre-patch file reproduced the reported
  warning **verbatim**, which is what licensed trusting a before/after that no harness surface could
  produce. Same technique as the earlier `CLAUDE_CODE_ENABLE_TODO_TOOLS` binary probes. The
  generalisable half is the *discipline* (a decode is only trustworthy once its replay reproduces
  the original text character-for-character), which is now a `docs/learnings.md` entry; whether the
  mechanics deserve a skill is the open question. — recurrence: 2 across sessions — candidate: maybe
  — **SUPERSEDED** 2026-09-14 (`dfff6fd`). The open question was *"whether the mechanics deserve a
  skill"*, and it is answered: they became a committed **script**, not a skill —
  `h-mad/scripts/h_mad_check_plugin_hooks.py`, one invocation per plugin, no prompt surface. The
  discipline this row names is no longer only prose in `docs/learnings.md`: "the replay must
  reproduce the original text character-for-character" is now two executable assertions against the
  two recorded warning texts, and the decode is re-verified against the live binary on every suite
  run. Note the row's own transcription drifted — it records the set name as `qdo`; the 2.1.270
  binary spells it `yko`, which is exactly why the landed test greps Set CONTENTS and never the
  minified identifier. Recurrence 2 → 3

## 2026-09-14 — backlog-cleared-and-the-hollow-kill

- **plugin-hooks-validator-replay**: replay Claude Code's own `hooks.json` key validator offline by extracting its allowed-key Sets from the running binary, then scoring every installed plugin — closes a "TUI-only, operator must look" item without an interactive session, and re-answers it after each upgrade wipes a vendor-cache patch. Negative control (the pre-patch backup) is part of the recipe, not an extra — recurrence: 1 — candidate: **LANDED** 2026-09-14 (`dfff6fd`) — `h-mad/scripts/h_mad_check_plugin_hooks.py` + `tests/test_h_mad_check_plugin_hooks.py` + `tests/mutation-specs/check_plugin_hooks.json` (12 mutations, ALL_CAUGHT). **The negative control did NOT survive as a backup and the row's recipe is corrected here:** the pre-patch `hooks.json` was wiped by the upgrade that followed, so a test reading that vendor path would have skipped forever while reporting nothing wrong. Both recorded warning texts are pinned as literal strings against synthesised fixtures instead — including the singular/plural swap between them, which is `len(findings)` and which a mutant that hardcodes `"keys"` otherwise survives. The binary key-sets ARE re-grepped live, by Set *contents* not by the minified names, and SKIP (never pass) when the binary is unreadable. Live run: 7 installed plugins, all CLEAN, exit 0
- **calibrate-a-ranking-screen-against-known-positives**: when a corpus is too large to read and the obvious proxy is known-wrong, rank by a cheap signal and then *calibrate the ranking against the items already known to be positive* before trusting the cut-off. Used on `#56` (177 rows, 8 knowns all inside rank 61) — the screen narrows, a human read decides. Distinct from the existing calibrate-a-detector row, which is about false-positive rates on a gate, not about bounding a search — recurrence: 1 — candidate: maybe
  — **RECURRENCE 1 → 2, and the technique gained a much stronger validator than the one this row
  describes. Measured 2026-09-14 by running the screen to exhaustion on `#56` itself.** All 177 rows
  were read, in seven batches cut in ascending overlap order, by seven readers none of whom knew
  which band they held or what any other found. `DIFFERENT` density came back **monotonic in
  overlap** — 19, 7, 5, 1, 0, 1, 0 against mean overlap 0.070 → 0.905 — and the top two bands
  returned **0 of 48** between them.
  **That gradient is a better calibration than "the knowns rank inside 61", and the row should say
  so**: knowns-inside-a-cut-off is equally consistent with a screen that merely fails to be
  *anti*-correlated, whereas a monotonic gradient measured by independent readers is evidence the
  ranking tracks the property. It also doubles as a free negative control on the readers — a pool
  biased toward `DIFFERENT` would have produced a flat row.
  The upgraded recipe is therefore: rank cheaply, calibrate against knowns, **then read the whole
  corpus in rank-ordered blind bands and check the gradient is monotonic.** The cut-off is what you
  are entitled to trust only once the gradient says the ranking is real.
  Exhaustion also priced the cut-off: 33 `DIFFERENT` calls, and only **2** at rank > 70 — so the
  screen's narrowing was sound, and the tail was worth reading exactly once.
  — **RE-PROBED 2026-10-03: PARTIAL** — the rank-ordered-bands recipe exists only in `docs/learnings.md`; no rule or tool. Closable as learning-only.
  — **DECLINED 2026-10-04 (triage: useful, not codable)** — lesson-only: a reading method (rank, calibrate, read in blind bands, check the gradient), not a mechanical step; `docs/learnings.md` holds it.

## 2026-09-14 — blind-spots-closed-and-a-retraction

- **a blinded adjudication set with positive AND negative controls**: when one lane's verdicts contradict another's, the question is not "who is right" but "does this lane over-call?" — and a plain second opinion cannot answer it. Shape: take the N disputed calls, add K items already known to be positives, add K items a different reader already called negative, SHUFFLE, hand the mix to two independent readers with no indication which is which, and keep the key in a side file. Measured on `#56`: 9 disputed + 4 knowns + 9 negatives → **18/18 negative controls came back clean**, which exonerated the METHOD, while only 2 of 9 disputed calls survived, which convicted the CALLS. Neither half is available from an unblinded re-read, and publishing the 21 unadjudicated calls would have been the alternative — recurrence: 1 — candidate: yes — mechanical: a builder that takes three id lists plus a corpus and emits `(shuffled payload, key.json)`, then a scorer that reports per-tag tallies. Both were hand-written this session and thrown away.
  — **RE-PROBED 2026-10-03: OPEN** — no adjudication-set builder or per-tag scorer.
  — **DECLINED 2026-10-05 (triage: not useful — calibrated, not built)** — one use, on `#56` in the 2026-09-14 session. The sibling batch-builder row's two uses came from that same session, and none recurred in the three weeks since: `grep -ril 'blinded\|adjudicat'` over this repo's handoffs finds only that session and pointers back to it, and HemaSuite's six matching handoffs are test-level negative controls (checksum gates, `ls` controls), not blinded reader sets. The value was the method: choose positive and negative controls, keep the readers blind, read the controls' tally before the disputed calls. This row states it in full. The code is about 100 lines of shuffling and tallying. Reopen when a second session needs a blinded set; build it together with the batch-payload builder row.
- **dispatch verification as EVIDENCE-ONLY, with UNKNOWN ranked above a guess**: twelve readers were dispatched this session over two different corpora, every one told to report `path:line` evidence and never to edit, and told explicitly that "a filename matching the proposal is NOT evidence — open the file" and "an honest UNKNOWN is worth more than a wrong LANDED, because a row wrongly marked landed is invisible forever". Result: 0 UNKNOWN, 0 fabricated LANDED, and three LANDED claims that survived my own re-verification. The one contrary data point is the important one — a verifier caught a row I had personally re-probed and gotten WRONG — recurrence: 2 (row verification, AC/row judging) — candidate: yes — the reusable half is the prompt contract, not the dispatch.
  — **DECLINED 2026-10-02 (triage: useful, not codable)** — a prompt contract, not a tool; its evidence-first half already lives in h-mad/agents/doc-auditor.md and the UNKNOWN-over-guess clause belongs in that dispatch text.
- **ask whether a line pin was correct AT THE COMMIT THAT WROTE IT**: a stale pin and a pin that was never right read identically at HEAD, and they have different remedies — one is drift the author could not prevent, the other is an error that was always there and says something about how the number was produced. One command settles it: `git show <writing-sha>:<file> | grep -n <target>`. Measured: `h-mad/SKILL.md`'s only line pin cited `docs/skill-candidates.md:1277`, and at `a90c365` — the commit that wrote it — the row was at **1319**, so it was wrong by 42 lines on day one. `PINDRIFT` exists for this class but runs only on phase documents, and the pin was not past-EOF, so no structural check could see it — recurrence: 1 — candidate: maybe — the durable fix is smaller than the detector: cite the section by NAME, which cannot rot.
  — **RE-PROBED 2026-10-03: PARTIAL** — `f90a96ba` re-pinned SKILL.md by name; four pins still cite `docs/skill-candidates.md:1277` and are wrong: `h_mad_audit_gate.py:515`, `tests/test_h_mad_audit_suite_gate.py:18`, `tests/mutation-specs/audit_suite_gate.json:68`, `docs/03-analysis/hmad-gate-field-verification.md:93`.
  — **LANDED 2026-10-04** — all four re-pinned by row NAME (`concurrent-suite-runs-manufacture-phantom-failures`, now at :1384). Re-ran the row's own one-liner first: at `a90c3656` that row sat at **1319**, the same 42-line miss as SKILL.md's — never right, not drift. The detector half (PINDRIFT over non-phase docs) stays unbuilt, by the row's own reasoning. Not swept: dated historical docs (`docs/carry-forward-triage-2026-09-02.md`, `docs/01-plan/features/doc-block-exec-brainstorm.md:17`) still carry numeric pins as point-in-time records.
- **a batch-payload builder for fanning one corpus across N blind readers**: written twice this session from scratch — 173 AC/row pairs into 7 files, then 47 backlog rows into 5 — and both times the fiddly parts were the same: cap a runaway field so one entry cannot dominate a payload, keep a `(batch, item)` map so results can be scored back, and cut the batches in a ranked order so the batch index is itself a variable. That last one is what produced this session's strongest evidence by accident: the monotonic gradient across bands was a free negative control on the readers — recurrence: 2 — candidate: maybe.
  — **RE-PROBED 2026-10-03: OPEN** — no batch-payload builder in any script dir.
  — **DECLINED 2026-10-05 (triage: not useful — calibrated, not built)** — both uses came from one session (2026-09-14), the same arc as the blinded-adjudication row, and neither recurred in the three weeks since. The three fiddly parts this row names (cap a runaway field, keep a `(batch, item)` map, cut batches in ranked order so the batch index is a variable) are recorded here. Reopen together with the blinded-adjudication row if either recurs.

## 2026-09-14 — memory-index-precheck (third session, same day)

- **a guard for any cap enforced at READ rather than at WRITE**: the class is defined by its silence — the write SUCCEEDS, the file on disk is complete and correct, and the consumer truncates on every load with no error at the point of loss. `wc -c` cannot see it and neither can any post-write hook, because the hook fires on the write that crossed the line and lands in a message no later session reads. Measured on the CC memory index: caps 25000 bytes / 200 lines decoded from the binary, this machine's store 254 bytes over, an h-mad note and a whole backlog entry invisible to every session — recurrence: 1 — candidate: **LANDED** 2026-09-14 (`ae7d9a7`) as `h-mad/scripts/h_mad_check_memory_index.py`, wired as a pre-check in `handoff/references/auto-memories.md`. **Left open as a CLASS**: the same shape applies wherever a producer writes past what a consumer will read, and nothing generalises the guard. Two properties worth copying: score EVERY dimension and let the worst bind (byte-only reports healthy on a line-over index), and print the dropped TEXT rather than a count — `dropped=254` is a number, the entries it deletes are the finding.
- **detect that ANOTHER session is committing into this same working tree**: `orca/skills` is one clone reached by several symlinked paths, so a second Claude session commits into the tree you are measuring. Measured this session: `8e89db2` merged as `cbf7332` landed **nine seconds** before my own commit, and the full-suite count moved by +10 for reasons that were not mine. The green run was still true — of the MERGED tree, which is a different claim from "my work is green" — and mutation runs, which rewrite files in place, were executing while that session was live. Mechanical: before trusting a suite count, `git log --oneline <last-known>..HEAD` and attribute the delta; refuse a mutation run when HEAD moved since the anchors were checked — recurrence: 1 — candidate: maybe — closely related to the still-open `a tree lock around the mutation harness` row, which is the intra-session half of the same hazard.
  — **TRIGGER ANSWERED 2026-09-14; the row's own 'no hook can see it' is true only of POST-write
  hooks.** The claim was *"neither can any post-write hook, because the hook fires on the write that
  crossed the line and lands in a message no later session reads"* — correct, and it rules out
  `PostToolUse` specifically. Two OTHER hook points do work and are now wired as
  `h-mad/hooks/memory-index-guard.sh`: `SessionStart`, which is the moment the loss actually happens
  (the cap is enforced at LOAD, so it is the only point at which an already-truncated index is
  observable), and `PreToolUse` on `Write|Edit` filtered to `*/memory/MEMORY.md`, which is the cause
  rather than the aftermath. Advisory, exit 0 on every path, silent on a healthy index, ~0.04s; both
  events put stdout into the session so it is read rather than logged. The CLASS half of this row
  stays open — nothing generalises the guard to the next producer/consumer cap — but "it cannot be
  automated" is no longer part of why.
  — **LANDED 2026-09-14.** The run now reads `HEAD` on both sides of itself and returns
  `MUTATION: TREE_MOVED before=<sha> after=<sha> inner=<verdict>` (exit 2) when it moved. This is the
  INTER-session half that `a tree lock around the mutation harness` deliberately left open: the lock
  serialises other mutation runs and cannot stop a sibling session committing into the same clone.
  Both halves measured here on 2026-09-14 — `4915206` landed inside a full-suite run. The inner
  verdict is KEPT and printed rather than discarded (it is still the most informative thing anyone
  has about those mutations, and throwing it away makes the honest verdict cost a whole re-run), and
  an unavailable `HEAD` read is explicitly NOT a change — both reads must be present AND differ, or
  every non-repo spec in the suite would refuse. 1 mutation, spec 50/50 ALL_CAUGHT. The row's other
  prescription — attribute a suite-count delta with `git log <last-known>..HEAD` before trusting it —
  remains a habit rather than a tool, and is what this session used to reconcile 3769 + 24 mine + 3
  theirs = 3796.
- **re-grep a decoded constant from the binary on every test run, and SKIP when it is unreadable**: second use of this shape in one day (plugin hooks validator, then the memory-index caps), and both times the alternative was a transcribed number that nothing would ever re-check. The discipline has three parts and the third is the one that gets dropped: match on the VALUE in its declaring context rather than the minified name (names are per-build), assert the rendering matches how the product SPELLS it (`25000` must read as `24.4KB` or the tool and the warning disagree about one number), and make an unreadable binary a SKIP rather than a pass — recurrence: 2 — candidate: yes — mechanical: a tiny helper that resolves the running binary (`which` → `readlink -f`), caches the blob per session, and offers `assert_constant(pattern, expected)` with the skip built in.
  — **LANDED 2026-09-14 as `h-mad/tests/claudebinary.py`.** All three parts of the ask, including
  the third: `claude_binary()` resolves the running image (`which` then `readlink -f` — the shim is
  not the 208MB binary and none of these strings are in it), `_blob_or_error()` is
  `lru_cache`d so the decode is paid once per SESSION rather than once per assertion (the memory-index
  and skill-body tests together were paying it ~6 times; that slice went 18.1s to 12.6s), and
  `assert_constant(pattern, expected)` matches on the VALUE in its declaring context with the SKIP
  built in. It stringifies `expected`, because `"25000" == 25000` is silently False and a
  re-derivation that fails toward RED gets deleted as flaky. `test_h_mad_check_memory_index.py` no
  longer carries its own copy of the locator. Cache-hit behaviour, both failure directions and the
  int/str equivalence are pinned in `TestTheSharedConstantHelper`.

## 2026-09-14 — hook-guards-and-two-red-pushes (fourth session, same day)

- **name the tests that PARSE a document you are about to edit**: a doc-derived test lives next to the CONSUMER of a document, never next to the document, so editing `h-mad/SKILL.md` gives no hint that `tests/test_h_mad_context_budget_docs.py` parses one of its sections. Twice this session a commit was PUSHED on the strength of a green targeted slice plus an ALL_CAUGHT battery, and both were red in the full suite on a guard in a third file — once on a property of the committed *spec set*, once on a section-length detector that fired because 28 lines of unrelated prose had joined the section. The mutation harness cannot cover it either: it scores the specs you name, so a guard nobody's spec anchors into is invisible to `ALL_CAUGHT` — recurrence: 2 — candidate: yes — fully mechanical and one line: `grep -rln "<doc basename>" --include='*.py' */tests/` names every file that reads it. Worth wiring into the pre-commit path rather than left as advice, since the advice is exactly what a hurried session skips. The deeper rule is the one that generalises: **green on everything you thought to run is not green**, and the ordering fix is free — commit, run the bare suite, THEN push.
  — **RE-PROBED 2026-10-03: OPEN** — no pre-commit path; `h-mad/git-hooks/` holds only `pre-push`. Advice only in `docs/learnings.md`.
  — **LANDED 2026-10-04** — `h-mad/scripts/h_mad_doc_consumers.py` names every tracked test whose source reads a document (basename plus same top-level dir, or the dir named), ending in one `RUN: python3 -m pytest -q …` line; `h-mad/git-hooks/pre-commit` prints it for staged documents, advisory, never blocks; `install.sh` ships it. Dogfooded on `h-mad/SKILL.md`: 72 consumer files, 3342 passed. Spec `doc_consumers.json` ALL_CAUGHT 5/5. The deeper rule (full suite before push) stays a rule.
- **cut an inserted block on its OWN last line, never on a structural boundary**: repairing the second red push meant removing 28 lines that had been inserted into the wrong section. Bounding them on "the next `## ` heading" swept 45 lines of that section's own tail out with them, turning one defect into two. The boundary was the thing that had just been broken, so it was not a safe thing to measure with — recurrence: 1 — candidate: maybe — not obviously codable as a check, but it is a one-line rule for any script that removes text it previously added: match the first AND last line you wrote, verbatim, and assert the span is the size you expect before writing. Adjacent to `a measured value must carry the commit it was measured at`; the shared shape is that a repair must not take its bearings from the damage.
  — **RE-PROBED 2026-10-03: OPEN** — the rule is not recorded in any skill or invariant.
  — **DECLINED 2026-10-05 (triage: useful, not codable, calibrated)** — The rule is recorded only in the handoff and this row, and no script removes text it previously inserted (`grep -rn "remove_block|def remove|def strip_block|def cut" h-mad/scripts handoff/scripts` returns nothing), so there is no home for the first-and-last-line plus span-size assertion. One incident (`2026-09-14-main__hook-guards-and-two-red-pushes.md`, a 28-line block cut on the next `## ` swept away 45 lines); no second over-cut found, and the nearest hit (2026-10-04, a paragraph added to the wrong section) is the insertion half, already caught by the `test_h_mad_context_budget_docs.py` 160-line cap. Recurrence is 1 in 33 skills and 66 HemaSuite handoffs since. Reopen if a script starts removing blocks it inserted; that script and its own tests are where the check belongs.
- **assert a spec's mutation is REACHABLE before counting it caught**: two mutations written this session could never fire — one targeted a missing-binary branch that never runs where the binary exists (it SURVIVED, correctly), and one was an equivalent mutant whose removed clause was already covered by a sibling `isinstance` check (it also survived). Both were retargeted rather than shipped, but only because a survivor is loud; the same two mistakes in the CAUGHT direction would have been silent — recurrence: 2 — candidate: maybe — partially covered by the existing `a mutation that can never fire reads as a passing battery` row, which this corroborates from the other side: that row is about mutations that cannot be DETECTED, this is about mutations that cannot be REACHED. A cheap half exists: for a mutation whose `find` sits inside a branch, run the named test once with the line deleted rather than replaced — if the test still passes, the line never executed.
  — **RE-PROBED 2026-10-03: OPEN** — no delete-line reachability probe; mutations are a single `source.replace`.
  — **DEFERRED 2026-10-05 (triage, calibrated)** — No delete-line or reachability probe exists (mutations are a single `source.replace`), and `coverage`/`pytest-cov` are not installed, so a coverage check adds a dependency while a delete-line probe costs one more targeted run per mutation (1498 mutations, 1371 with a `test` key). Both incidents behind the row ended SURVIVED (loud, correct); the 2026-10-04 sweep at `cfbd2517` forwarded 24 kills (18 crashes, 5 timeouts) and the only hollow kills were 2 `IndentationError`s, now refused by tier 1 (`:1414-1420`); no documented CAUGHT mutation targets a line its named test never executes. Fold into row 2125 (hollow-kill, already deferred), and note row 2302 (host-equivalent mutants) as the host-scoped case sharing a home. Reopen when one CAUGHT mutation is shown, by re-scoring with the line deleted or by review, to target a line its named `test` never executes.

## 2026-09-14 — backlog-drain-25-through-30 (fifth session, same day)

- **reap LEAKED `exec-pane` wrapper processes, which the pane janitor does not cover**: found while checking whether a stale worktree was safe to remove — PID 97466, **PPID 1**, running `hmad-dispatch.sh exec-pane agy` for **22h 27m** at 0.0% CPU, spinning `sleep 1` children forever. Its prompt and `--cd` both pointed at `pytest-of-kimhawk/pytest-24348/test_unresolvable_panekey_fall0`, a pytest tmpdir that **no longer exists** — so a test run leaked a wrapper that then outlived its session, its target directory, and the tmpdir GC — recurrence: 1 — candidate: **LANDED** (2026-10-01, branch `fix/reap-leaked-test-processes`: `h-mad/tests/leak_reaper.py` + a session-end conftest finalizer that reaps and REPORTS every process whose argv names the run's basetemp; spec `leak_reaper.json` ALL_CAUGHT) — **this is NOT a `live-e2e-pane-janitor` recurrence and must not be filed as one.** That row LANDED as `h_mad_pane_janitor.py`, which closes *Orca panes* and settles their *dispatches* by positive `worker-list` identification. This leak has neither: it is a local bash process, it has no worker row, and `worker-list` cannot see it — so the shipped janitor would have reported it `unidentified` even if it had been looking, which it is not. The mechanical fix is small and has a positive identifier of its own: `exec-pane` already writes a slot registry at `.h-mad/panes/<handle>.cd`, and a wrapper whose `--cd` names a path that no longer exists is reapable with no inference at all. Two things make it worth wiring rather than leaving as advice — it went **22 hours** unnoticed on a developer machine, and the natural place to look (`pgrep`) is the surface this repo already records as unreliable for liveness. A conftest session-finalizer that reaps wrappers rooted in the run's own `tmp_path` would close the leak at the source, which is strictly better than reaping it afterwards.

## 2026-09-15 — two-false-task-premises (scout)

**Reconcile first — two rows re-verified against source and bumped, not flipped; one preamble line found stale.**

- `2180` **name the tests that PARSE a document you are about to edit** — **still open, verified against source**: `h-mad/hooks/` holds `h-mad-advisor-warn.sh`, `h-mad-tdd-gate.sh` and `memory-index-guard.sh`; `h-mad/git-hooks/` holds `install.sh` and `pre-push`; none of them greps for a document's consumers. Recurrence **2 → 3**, and this time in the *successful* direction: the check was run by hand before all four document edits this session (`h-mad/SKILL.md`, `docs/skill-candidates.md`, the `#56` probe, `hmad-dispatch.sh`) and **three commits went out green** where the previous session pushed two red. A row whose manual form demonstrably works is the strongest case for wiring it, not the weakest.
- `1429` **a measured value must carry the commit it was measured at** — **still open**, with a fresh instance that is not a document but a *code comment*: `hmad-dispatch.sh`'s J36 block hardcoded *"this repo carries 88"*, a property of one tree at one moment. Gitignoring `*.done` this session made it wrong the same day. Reworded at `632ecde`. Recurrence bumped; the row's scope should be read as covering comments and prose, not only published figures.
**Preamble correction (2026-09-15)** — not a row, deliberately unbulleted so the census does not read it as one: the 2026-09-02 reconcile line at `:37` says of the frozen-tree guard *"no `PreToolUse` hook exists — `h-mad/hooks/` holds only `h-mad-advisor-warn.sh` and `h-mad-tdd-gate.sh`"*. That is now **stale in its premise**: `memory-index-guard.sh` shipped 2026-09-14 and IS wired at `PreToolUse` (`Write|Edit`), so the "no such hook" half no longer holds. Whether the frozen-tree guard itself is still open was **not** re-verified here — only the reason given for it is out of date, and a stale reason is how a row gets re-litigated from scratch.

**The remaining 27 open `yes` rows were NOT reconciled this session** and are listed unverified by `--list-open`. Said plainly rather than left implied: a scout that reconciles three rows and appends new ones has not made the backlog current, and the next reader should not read this heading as though it had. (Written as "open `yes` rows" and not with the full verdict phrase on purpose — the first draft of this line spelled it out, and the census read the prose as a verdict and mis-scored the paragraph above it as an open row. The file's own fallback-grep comment already warns that prose quoting the phrase matches; it turns out the census's row-scoped reader inherits the same hazard through a row's continuation lines.)

- **read a tool's own summary line; never re-derive the figure from its output**: twice this session a hand-rolled count over a tool's stdout was wrong while the tool printed the right number one line away — `grep -c "^  orca/skills:"` over `--list-open` returned **6** against the census's own `OPEN=50`, having counted the bump-rows block; and a `.done` orphan probe reported a report ABSENT by looking in `docs/01-plan/features/` when that feature's markers live in `docs/archive/2026-09/doc-block-exec/` (corrected sweep: **0 orphans of 88**, the opposite conclusion, and a gitignore decision rested on it) — recurrence: 2 — candidate: no — **the mechanical half already exists and the defect was not reaching for it**: `skill_candidates_census.py` is import-safe and exposes `rows()`/`ROW`/`TERM`/`CAND`, and this file's own scout reference already says *"Import it — do not write a parser."* Filing it as a row would add a second copy of advice that is already written down where it belongs. The upgrade it names, if any, is to the reference: the rule is stated for the census specifically and generalises to every tool that prints a summary line.


## 2026-09-28 — parallel-lanes loop (filed mid-session)

- **audit gate counts NESTED sub-bullets as findings** — `h_mad_audit_gate.py docs/02-design/features/codex-tdd-gate-defects.design.audit.v1.teammate.md` prints `GATE: FAIL must=27 should=37 … untagged=49`, while the report's `## Must-fix` section holds exactly **3** top-level bullets (lines 6, 18, 35; re-measured 2026-09-28 at `dcb4a71e`). Every indented `  - ` evidence line under a heading is scored as its own finding. The per-cycle verdict survives (3 must is still FAIL), but the exit-check / round-cap counts do not — a 0-must cycle with nested evidence under Should-fix would still report inflated `should=`. Fix belongs in the gate's bullet reader: count only column-0 bullets under a severity heading, and carry an `untagged` count for nested ones only when they are not under a tagged parent. Workaround in use: auditor prompts now say "tag at TOP-LEVEL bullets only". — recurrence: 1 (every nested-bullet teammate report since the teammate leg shipped is affected) — candidate: yes
  — **LANDED 2026-10-02** — `h-mad/scripts/h_mad_audit_gate.py` §`_bullet_groups`/`_collapses` (`a478c242`) — collapse only when unambiguous, flat otherwise; the corpus differential is under `docs/03-analysis/probes/audit-gate-nested-bullets/`.
- **audit-prompt preflight false-HALTs on a gated document that QUOTES a slot token** — `h_mad_assemble_audit.py --phase impl-plan` for multi-host-runtime returned `ASSEMBLE: HALT impl-plan:preflight — unfilled_slot: '`<INLINE_*>` scan in `test_h_mad_skill_reviewer_prompt.py`.'` because `preflight()` scans the WHOLE assembled text for `<INLINE_`, including the inlined gated document, which legitimately names that scan. Worked around by rewording the impl-plan line (`dcb4a71e`) — the document changed to satisfy the tool, not the reverse. Fix: run the `<INLINE_` / `<AUDIT_SENTINEL>` / `<REPORT_FILE_PATH>` residual check over the TEMPLATE-derived regions only (or before the gated doc is inlined), and add a fixture where the gated doc contains each token. Note the asymmetry is safe-direction (a false HALT, never a false PASS), so this is friction, not a hole. — recurrence: 1 — candidate: maybe
  — **RE-PROBED 2026-10-03: OPEN** — `preflight()` in `h_mad_assemble_audit.py` still scans the whole assembled text, gated doc included; no fixture.
  — **LANDED 2026-10-04, as a class** — the false HALT had a sibling the row did not name: slots were filled one `str.replace` at a time, so a token QUOTED inside an already-inlined document was REWRITTEN by a later slot (the document reached the reviewer altered, silently). Same shape in all three assemblers: `h_mad_assemble_audit.py`, `h_mad_assemble_tdd.py` (impl-plan task text, then `<INLINE_REPO_ROOT>`/`<REPORT_FILE_PATH>`) and `h_mad_archreview_cycle.py` (design, then summary/report slots). All three now fill through one `fill_slots()` — one pass, returning the template residue — and run their residual scan over that residue. Fixtures put each token inside the gated document. Spec `fill_slots.json` ALL_CAUGHT 6/6; 1125 assembler-related tests pass.

## 2026-10-04 — first full-corpus sweep

- **a mutation row can be EQUIVALENT on one host and discriminating on another**: the first full `--sweep` reported `grok_env_scrub_and_beat_boundary.json :: scrub-enumerates-compgen` SURVIVED. Not a weak test: on this Mac the only bash is /bin/bash 3.2, whose `compgen -e` lists non-identifier names like `CLAUDE-HYPHEN`, so swapping `env -0` for `compgen -e` changes nothing here; the D3 leak exists only under bash 4+. The spec format has no way to say so, so the corpus can never read ALL_CAUGHT on this host and the survivor is indistinguishable from a real hole until someone re-derives the shell semantics. Mechanical half: a per-mutation `requires` probe (a command whose exit says the mutant is observable here) and a `HOST_EQUIVALENT` verdict distinct from SURVIVED, counted on the token line — recurrence: 1 — candidate: maybe
  — **DEFERRED 2026-10-05 (triage, calibrated)** — `h_mad_mutation_harness.py` has no `requires` field and no `HOST_EQUIVALENT` verdict (`_sweep` at `:1756-1804` counts only `all_caught`, `survived`, `unmeasured`); the single case is prose on the spec row `h-mad/tests/mutation-specs/grok_env_scrub_and_beat_boundary.json` `_mechanism` (`5089bb92`). The full `--sweep` has run once ever (145 specs, 142 ALL_CAUGHT, 3 SURVIVED; 1 of the 3 host-bound, the other 2 real test defects, fixed); the corpus now holds 152 specs and 1498 mutations, so host-bound mutants are 1 of 1498, HemaSuite has 0, and nothing gates on the sweep token. A `requires` probe would relabel 1 of 3 survivors correctly but fails open if wrong, and the cheaper remedy for the one row is a spec edit (make its test discriminate on bash 3.2, or retire the row), not a harness feature. Reopen when a second host-bound mutant is measured, when `--sweep` is wired into a gate (pre-push or CI), or when the sweep runs on a second host (bash 4+ or Linux). Same family as the hollow-kill row (deferred) and the reachability row (deferred 2026-10-05): if any of the three is built, build one per-mutation precondition field serving all three, not three verdicts.

## 2026-09-29 — tdd-gate closure loop (filed mid-session)

- **TDD gate fail-opens D1–D5 — follow-up h-mad feature (operator decision 2026-09-29, D1/D2 first)** — reproduced by the codex-tdd-gate-defects 6a fresh-context verifier after suite, mutation harness and agy `READY_TO_MERGE` all passed; repro commands in `docs/archive/2026-09/codex-tdd-gate-defects/codex-tdd-gate-defects.gap.v1.md` §"Defects (reproduced)". D1 HIGH: `.PY` case-variant suffix passes both gates on case-insensitive APFS (`h-mad-tdd-gate.sh` `*.py` glob; Codex gate `path.suffix != ".py"`); codex apply_patch then writes `prod.py`. D2 HIGH: Codex `PATCH_TARGET` keeps a trailing space / `\r` in the header path, so `.py `/`.py\r` is not production; codex trims and writes the file. D3 MED: symlinked `CLAUDE_PROJECT_DIR` spelling under `tests/` → `IN_ROOT=no` → `_dir_match` exempts on root ancestry (§D9 fix incomplete). D4 MED: `tests/` symlink to a prod dir — Claude gate exempts lexically, Codex gate resolves and governs. D5 LOW: `_run_bounded` post-kill `communicate()` has no timeout; a setsid grandchild holding the pipe overruns the 40 s budget. All inherited except D3's AC-6.15 angle; none a regression. candidate: yes (h-mad feature).
  — **LANDED 2026-10-02** — h-mad feature `tdd-gate-fail-opens`, `docs/archive/2026-09/tdd-gate-fail-opens/tdd-gate-fail-opens.analysis.md` §FR table (FR-1..FR-8 Complete; D5 = `h_mad_tdd_judge.py` bounded reap) (`d306820e`).
- **two suite tests mutate the tracked `h-mad/tests/conftest.py` in place** — `test_h_mad_pin_file_guard.py` (`b1f8954c`) and `test_h_mad_wire_registry.py` run `run_spec` against the live tree; `git status` mid-suite showed `M h-mad/tests/conftest.py`. Any concurrent pytest in that tree imports the mutated conftest — the likely source of every "concurrency artifact" flake (post-Task-9 wire-registry failure, 3/3 alone). Fix: point the spec's `root` at a scratch copy. candidate: **LANDED** (`5ca8f97e`, 2026-09-29).
- **grok-codex-fallback carried defects (operator decision 2026-09-29)** — D3 LOW: `hmad-dispatch.sh` scrubs `CLAUDE*` via `compgen -e`, which lists only shell identifiers, so `CLAUDE-HYPHEN=`/`CLAUDE.DOT=` names reach the grok child (FR-3 says the class is `^CLAUDE`); fix with `env -i` plus a filtered `env -0` list. D4 LOW: the heartbeat appends `#hmad-beat` to the same log grok writes, so an event written in two `write()` calls is split and a completed run reads TRUNCATED (fails closed; same mechanism as agy's path). Repros: `docs/archive/2026-09/grok-codex-fallback/grok-codex-fallback.gap.v1.md`. candidate: **LANDED** (merge `6c8a0a34`, 2026-09-29).
- **codex TDD gate denies the documented resume call** — `h_mad_resume_decision.py` is absent from `SAFE_HMAD_SCRIPT_OPTIONS` in `h-mad/hooks/h-mad-codex-tdd-gate.py`, and the adapters' `--session-id "$(cat …)"` read fails `SIMPLE_SHELL_COMMAND`. Pre-existing; latent while the codex gate is unarmed on this machine. Needs a safe-list entry plus a gate-acceptable session-id form. candidate: **folded into tdd-gate-fail-opens FR-8 / Tasks 10a–12** (2026-09-29).
- **`iterate_cycles` never reaches the telemetry row** — `h_mad_state_write.py --set iterate_cycles=N` succeeded for grok (1) and multi-host-runtime (2), yet `h_mad_telemetry.py record` printed `iterate_cycles=0` for both. **Real cause (2026-09-29):** 6b never versioned `analysis.md`, and telemetry derives the count from the versioned analysis files by design — the state key is not what it reads. candidate: **LANDED** (`0e50ce9d`).
- **A doc that names a runnable path must not carry a checkout path** — mhr's 6b D2 fix wrote the worktree's absolute path into three adapters and the tests pinned "this checkout's path", so the worktree suite passed and merged main failed 4 tests (fixed `be2f5f43`: `<HMAD_SKILL_ROOT>` placeholder + a no-`/Users|/home` test). Lesson: always run the merged-tree suite even when `identity=y` if docs moved. candidate: no (landed).

## 2026-09-30 — HemaSuite #10 handover triage: (a), (c), (d) (filed from feature/tdd-gate-fail-opens)

Source brief: `docs/handoffs/2026-09-30-main__hmad-defects-from-hemasuite.md` (Handover-From HemaSuite · main · session 7c01aa37). (b) is the TDD-gate pin drift, decided and fixed separately on `feature/tdd-gate-fail-opens` (the pin was right; the branch's Claude gate judged `$CANON_PREFIX/$NAME`). Premises re-verified 2026-09-30 against the tree and this session's dispatch outputs.

- **(a) agy report self-reporting `Evidence: 0 files opened` is scored zero-evidence even when its transcript shows real reads** — CONFIRMED. `h-mad/scripts/h_mad_audit_cycle.py` `_unscorable_reason_text` returns `"zero-evidence"` from `EVIDENCE_COUNT_RE` on the report TEXT alone; it never consults the measured tool count that `h_mad_review_evidence.scan` produces from the `--log` (imported in the same file). Evidence: HemaSuite `docs/archive/2026-09/asset-legend-native-citations/*.unscored-zero-evidence.md` (2 of 2 agy legs, `EVIDENCE: PASS` 20+ tools). The refusal itself is deliberate (row at `:1617`); this is its false-positive side. Candidate fix: when a transcript is available and `scan` reports PASS above the delivery floor, a self-reported zero is a CONTRADICTION token (`unscorable=self-report-contradicts-transcript`), not `zero-evidence` — still never a silent pass. candidate: **LANDED** (2026-10-01, branch `fix/audit-cycle-self-report-contradiction`: `unscorable:self-report-contradicts-transcript` when the leg's parsed log shows reads above the delivery floor; spec `audit_cycle_self_report.json` ALL_CAUGHT).
- **(c) Phase 5d/5e assembler never asks for a mutation spec** — HALF CONFIRMED, HALF FALSE. Confirmed: `h-mad/scripts/h_mad_assemble_tdd.py` has zero occurrences of `mutation`; every spec row on tdd-gate-fail-opens was written by the orchestrator. FALSE: "Codex's workspace-write sandbox cannot run `h_mad_mutation_harness.py`" — Codex ran the harness (scored ALL_CAUGHT itself 3x, 2026-09-30 predecessor session) and ran `--check-anchors` in this session's `f3_green.out` and `pd_green.out`. Candidate fix: assembler `--mutation-rows` section asking GREEN to propose rows (find/replace/test) for the task's guards and to run `--check-anchors`, the orchestrator still scoring. candidate: **LANDED** (2026-10-01, same branch: GREEN always asks for rows; `--mutation-spec` names the file and adds `--check-anchors`, which the Codex Phase-5 gate now admits read-only and inside the project; spec `assemble_tdd_mutation_rows.json` ALL_CAUGHT).
- **(d) Codex cannot send `worker_done` from inside `exec codex`** — CONFIRMED, 4 more instances. 6 of 16 `exec codex` outputs in session 9cfdf8ab's scratchpad report `EPERM`/`runtime_access_denied` on the Orca coordinator send; `rc` and `--out` were unaffected every time. Cause: the assembled prompt carries the `[H-MAD] worker_done coordinator handle` line on the exec path (present in `t10a_red.txt`, `t10b_red.txt`, `t11_red.txt`), and `h-mad/references/codex-implementer-prompt.md:93-96` then asks for `orca orchestration send --type worker_done`, which the exec sandbox cannot reach. The template already says "if that line is absent … skip the worker_done emission", so the smallest fix is for the assembler/`hmad-dispatch exec` path to omit the coordinator-handle line (pane dispatch keeps it). candidate: yes (h-mad assembler / hmad-dispatch). Status: open, small, parked.
  — **LANDED 2026-10-02** — `h-mad/scripts/hmad-dispatch.sh` §exec (coordinator-handle prepend; codex arm omits it) (`c820a1ac`).
- **(note, not h-mad)** graft rewriting `.gitignore` / adding `.ignore` in fresh worktrees — not filed as an h-mad row; relevant only if fanout `worktree-create` should pre-stash it.

## 2026-10-01 — backlog-cleared (scout)

**Reconciled this session: 3 rows, each flipped to LANDED with its commit** — the exec-pane
wrapper-leak row (`4affd9e0`), HemaSuite #10 (a) and (c) (`86479f73`). The census reads
`OPEN(yes+maybe)=54`; **the other 51 were NOT reconciled here** and are listed unverified.

- **`--check-anchors` should sweep every spec directory by default**: h-mad keeps mutation specs in BOTH `h-mad/tests/mutation-specs/` and `h-mad/tests/specs/`; after editing `h_mad_audit_cycle.py` the habitual `--check-anchors tests/mutation-specs/*.json` said ANCHORS_OK while three rows in `tests/specs/audit_cycle_connections.mutation.json` had drifted — caught only by a doc-derived test in the full suite. Fix: a no-argument `--check-anchors` (or `--all`) that globs both directories, and name the second directory in SKILL.md's 5e text. — recurrence: 1 — candidate: yes
  — **RE-PROBED 2026-10-03: PARTIAL** — every-directory coverage exists in the pre-push hook (`d275d7bc`) and `test_committed_mutation_harness_anchor_sweep_is_ok`; the CLI still requires a spec path and SKILL.md 5e names only `tests/mutation-specs/`.
  — **LANDED 2026-10-04** — `--check-anchors` with no spec sweeps every committed spec (`_committed_specs`: `git ls-files '*.json'` + the classifier, same discovery as the pre-push hook); a failed discovery prints `ANCHORS_UNREADABLE` rather than an empty sweep. SKILL.md 5e documents the no-arg form. Live: `ANCHORS_OK specs=139 mutations=1376`. Spec `harness_check_anchors_discovery.json` ALL_CAUGHT 4/4.
- **post-merge variant for spec-literal pre-push smoke scripts**: the mhr V-11 script halts on "integration already pushed" and its `recover()` reverts `PRE..HEAD`, so after a merge it is either unrunnable or destructive; the post-merge run had to be hand-adapted (part 2 only, no revert). A `--post-merge` mode in the probe, or a plan rule that every pre-push smoke states its post-merge form, would make a late live smoke a one-liner. — recurrence: 1 — candidate: maybe
  — **RE-PROBED 2026-10-03: OPEN** — no `--post-merge` mode and no plan rule that a pre-push smoke states its post-merge form.
  — **DECLINED 2026-10-05 (triage: not-useful, calibrated)** — Exactly one spec-literal live-smoke artifact exists in both corpora (`docs/archive/2026-09/multi-host-runtime/multi-host-runtime.live-smoke.md` and its probe `docs/03-analysis/probes/multi-host-runtime/smoke_assert.py`), so the recurrence is 1 session and 1 feature (`multi-host-runtime.live-smoke.md:7-16`, `2026-10-01-main__backlog-cleared.md:34`); the 5 HemaSuite "already pushed" hits are ordinary git prose, not smokes. The rule is already a learning (`docs/learnings.md:42`, 2026-10-01: a pre-push smoke whose `recover()` reverts PRE..HEAD must not run post-merge; run its assertion part only, no revert). A `--post-merge` flag would live in a per-feature probe no other feature reuses, and a plan rule has no consumer to enforce it. Reopen if a second feature ships a pre-push smoke with a destructive `recover()`.

## 2026-10-01 — v111-file-tool-only (scout)

**Reconciled this session: none.** No open row's work was touched. The census reads the count
above, all unverified here.

- **cache-proof mutation sweep for a probe's rehearsal**: this session ran an ad-hoc `mutsweep.py` about 12 times over `smoke_assert.py` against `rehearsal/cases.json`. It writes one module per mutant, sets no bytecode, asserts the mutant differs from the original, and counts a crashing mutant as killed. Its first version (a single `_mut.py`) reported a false kill from a stale `.pyc`. `h_mad_mutation_harness.py` is pytest-based and does not fit a rehearsal-style probe. — candidate: yes (recurrence ≈12, one session)
  — **DECLINED 2026-10-02 (triage: not useful)** — one-session, one-probe tool; the stale-.pyc false kill it worked around is fixed in h_mad_mutation_harness.py (bytecode purge around every run).
- **fresh-reviewer rotation for adversarial rounds**: the long-running reviewer's "clean" round was followed by 3 HIGH findings from a fresh-context reviewer, and every later round used a new agent. A skill or recipe could encode it: spawn a fresh reviewer per round, pass the closed-class list from a doc, and stop when a fresh round is clean. — candidate: maybe
  — **RE-PROBED 2026-10-03: OPEN** — no recipe; SKILL.md keeps audit reviewers warm for cycles 2..N, the opposite.
  — **DECLINED 2026-10-05 (triage: useful, not codable, calibrated)** — The change-review lane exists (`h-mad/agents/change-reviewer.md`, `h-mad/SKILL.md:3048-3065`, `1b8543c8`) and a warm reviewer going stale was seen in 2 sessions (`2026-10-01-main__v111-file-tool-only.md:37-38`: 3 HIGH findings from a fresh reviewer after the 11-round reviewer's first clean round; `2026-10-05-main__prescribed-blocks-claim-once.md:31`: a new reviewer found the unguarded `--out` path after a design pivot), but the same 10-05 entry and `docs/learnings.md:16` record that the resumed reviewer confirms closure of its own findings, and `SKILL.md:2317-2319` keeps doc-audit reviewers warm for cycles 2..N. The supported policy is conditional (fresh after a design pivot or before a clean verdict is trusted, resumed to confirm closure) and spawning or resuming an agent is an orchestrator action no script can enforce; an always-fresh rule would discard the closure value. The gap is one sentence of doctrine in `SKILL.md` §"Teammate change review", today only at `learnings.md:16`: a doc landing, not a tool. It is the reconciliation between this row and the change-reviewer round driver row, which resumes the same reviewer. Reopen if a doc landing is wanted.

## 2026-10-02 — v111-review-loop-closed
- **review-report-chunk-relay**: a fresh reviewer subagent is refused report-file writes and its final reply truncates at ~4 KB; every round (R18–R22) needed the same SendMessage-to-main ≤3 KB chunk protocol plus the orchestrator persisting each chunk to `review-rNN/REPORT.md` and re-running every fixture — recurrence: 5 — candidate: yes
  — **RE-PROBED 2026-10-03: OPEN** — the ≤3 KB SendMessage chunk protocol is uncodified and there is no Write-capable code-reviewer agent.
  — **LANDED 2026-10-04** — `h-mad/agents/change-reviewer.md` removes the need for the chunk protocol instead of writing it down. It is a fresh-context change reviewer with `tools: Read, Grep, Glob, Bash, Write`. It owns exactly one file, its report, and gives a `CHANGE-REVIEWER: DONE … sha256=` line first, using `doc-auditor`'s protocol (`.done` marker, digest before marker, never `advisor()`, read in slices). It is registered in all three install lists, and a new test pins every `agents/*.md` against every list (nothing did before). SKILL.md §"Teammate change review" routes change reviews to it. A first placement inside §"Which advisory channel" pushed that section past its 160-line runaway guard in `test_h_mad_context_budget_docs.py`, so it has a section of its own. `ALL_AGENTS` and the advisor/slices suite now include it. Live run: dispatched against its own change before the agent type loaded, its report (44 lines) matched the DONE line's sha256, and its 6 should-fixes were all applied. Those included 4 surviving mutants of the new tests, found by the reviewer itself. Round 2 ran on the real `change-reviewer` type, which was loaded mid-session. Its hash matched too; it confirmed all 11 round-1 items were resolved, and its single remaining finding (the orchestrator's gate sentence was not pinned) was fixed.
- **dual-interpreter mutation sweep with control**: ad-hoc `sweep.py` (one module per mutant, `sys.modules` registration, unmutated CONTROL first, run under both `python3` and pytest's `/opt/anaconda3` python, combo mutants for layered guards) rebuilt and re-anchored each round; `h_mad_mutation_harness.py` lacks the control/dual-interpreter/combo parts — recurrence: 5 — candidate: maybe (extend the existing harness)
  — **RE-PROBED 2026-10-03: PARTIAL** — the control exists (`BASELINE_NOT_GREEN`, `de48a873`; bytecode purge); a second-interpreter run and multi-pair combo mutants do not.
  — **DECLINED 2026-10-05 (triage: not-useful, calibrated)** — The control landed (`BASELINE_NOT_GREEN`, `de48a873`; `_purge_bytecode` at `h_mad_mutation_harness.py:349`); the dual interpreter and combo mutants are absent but have no demand: each spec's own `command` already pins the pytest interpreter (143 commands start `python3.11`, 2 start `/opt/anaconda3/bin/python3.11`), `_load_spec` requires one `file`/`find`/`replace` per mutation (`:290-294`) and 0 committed specs use multi-edit mutations, and no handoff in either corpus reports needing to disable two guards at once to see a kill. The "5" recurrence is 5 rounds in one session on one probe (v111 `smoke_assert.py`, `2026-10-02-main__v111-review-loop-closed.md:42-46, :111-113`), the sibling row on the same ad-hoc `sweep.py` was DECLINED 2026-10-02 as a one-session, one-probe tool, and a second interpreter cannot run the harness here (`/opt/homebrew/bin/python3` 3.14.8 and `/usr/local/bin/python3` 3.14.5 both fail with no module named pytest). Adjacent, not this row: the interpreter-divergence class does recur (07-29 pin-interpreter row, 10-02 JSON recursion under 3.11, 10-05 `Path.exists` EACCES under 3.14 at `h_mad_assemble_audit.py:508`) and all 53 shebanged `h-mad/scripts` and `handoff/scripts` modules use `#!/usr/bin/env python3` while the suite runs on 3.11, but a mutation sweep would not have caught either live case; file it as its own row ("production interpreter != test interpreter") if pursued.

## 2026-10-04 — upstream-sync-gate-fixes

- **tripwire runtime stub for "this changed nothing" tests**: proving that `<verb> --help` ran nothing needed an `orca`/`cmux` stub that appends its argv to a file and exits 1, because the shared stubs in `h-mad/tests/stubs/` answer silently and their silence cannot distinguish "not called" from "called and ignored". Written inline in `test_hmad_dispatch_verb_help.py`; a shared `tripwire_bin(tmp_path)` helper beside `_bindir` would let any no-side-effect assertion reuse it — recurrence: 1 — candidate: maybe
  — **DECLINED 2026-10-05 (triage: not-useful, calibrated)** — The shared stubs already record calls: `h-mad/tests/stubs/orca:2` appends argv to `$HMAD_STUB_CAPTURE` and `:7` exits `$HMAD_STUB_ORCA_RC` after capture (`7df8ce84` 2026-07-20, `234baeb9` 2026-08-06); 5 test files use `HMAD_STUB_CAPTURE` and 15 "nothing was called" assertions across 7 files already work this way (for example `test_hmad_dispatch_collect_report.py:110`, `test_hmad_dispatch_exec_stamp.py:251/:291/:327`, `test_grok_fixtures.py:249`). The inline `_tripwire_bin` exists in 1 file (`test_hmad_dispatch_verb_help.py:56-64`); recurrence is 1 (the 10-04 upstream-sync session), and moving it into the shared stubs saves one ten-line function. Incidental, latent, not a live hole: `h-mad/tests/stubs/cmux:3` exits on `HMAD_STUB_CMUX_RC` before the capture at `:5`, the reverse of the orca stub, so a forced-failure cmux call goes unrecorded; its only user, `test_hmad_dispatch_exec_stamp.py:576`, does not read the capture, so nothing passes vacuously today. Swapping lines 3 and 5 would make the two stubs symmetric. Reopen if a second test hand-writes a tripwire.
- **clean-worktree control for a worktree-only failure**: a suite failure seen only in `.claude/worktrees/<x>` was settled by `git worktree add --detach <tmp> HEAD` and re-running the one test there — a clean control that separates "my diff" from "the checkout path". Done by hand once; a tiny `h_mad_clean_control.py <test-node>` (create, run, remove, print `CONTROL: SAME|DIFFERS`) would make it routine — recurrence: 1 — candidate: maybe
- **fan-out backlog re-probe with file-backed results**: reconciling 50 open rows ran as 5 read-only agents of 10 rows each, and 4 of 5 final replies arrived as bare "Done." — only results written to scratchpad files survived. `skill_candidates_census.py --list-open` could emit per-batch probe prompts that name the output file, so the next reconcile is one command plus a merge — recurrence: 1 — candidate: maybe
  — **DECLINED 2026-10-05 (triage: useful, not codable, calibrated)** — The protective part is one prompt sentence already recorded at `docs/learnings.md:26` (2026-10-04: "have each write its result table to a scratchpad file as well as replying"), and it held when applied in the 10-05 session (`triage-batch1.md` 24050 B and `triage-batch2.md` 17884 B on disk; batch 2 committed as `2c975f5a`). Fan-out reconciles happened in 2 sessions (10-04, 5 agents with 4 bare "Done." replies, `0474a14d`; 10-05, batches 1-3). `skill_candidates_census.py` accepts only `--list-open`, and the row set is already mechanical through it; the batch prompts carried session-specific content no generator can derive (a skip list of handled rows, a verdict grammar, a second corpus, calibration rules), and the 10-04 failure would not have been prevented by a generator unless the prompt also said to write a file. Reopen if a second session loses fan-out results to bare replies despite the learning.


## 2026-10-04 — row-t-archive-probe-reviewer

- **`h_mad_doc_consumers.py --run`**: execute the consumer tests instead of printing a `RUN:` line. That line was copied by hand 6 times this session. Once it was skipped before a full suite, which then spent 15 minutes surfacing 25 failures that the consumer run reproduces in seconds (a SKILL.md paragraph in the wrong section tripped `test_h_mad_context_budget_docs.py`'s 160-line guard). Small: the `RUN:` list already exists; add a flag that subprocesses it and returns its exit code — recurrence: 6 — candidate: maybe

## 2026-10-05 — prescribed-blocks-claim-once

- **the pytest side of the mutation tree lock**: `tree_lock()` (LANDED 2026-09-14) makes two harness runs exclusive, but a bare `python3 -m pytest` takes no lock. So a harness started while a full suite is running still edits source under it. That happened this session: the 1666 harness ran during the full suite. It was harmless only because the harness touched just the new script, whose tests the suite had already passed. Mechanical: a session-scoped conftest fixture that checks the tree lock at start and refuses with a named error, or a harness check that refuses when a pytest is running on the same git toplevel — recurrence: 1 in this direction (2026-08-29's two discarded runs were the same hazard) — candidate: maybe
  — **LANDED 2026-10-05** — folded into `concurrent-suite-runs-manufacture-phantom-failures`: the suite session takes the harness's tree lock, so a harness started under a full suite is refused with `MUTATION: BUSY … spec=pytest-session`, and a suite started under a harness with `SUITE: BUSY`.
- **collect a worktree executor's evidence mechanically**: five times this session I re-derived a worktree executor's result by hand (branch tip, targeted tests, mutation verdict, anchors, real-cache check), because the agent's final message did not carry it. One round ended "No change." while it had committed. A verb that takes a worktree path and prints `sha · tests · MUTATION: · ANCHORS ·` from the tree itself would make the evidence independent of what the agent says — recurrence: 5 (one session) — candidate: maybe
- **change-reviewer round driver**: seven review rounds this session followed the same manual loop: hash the report against the DONE line's `sha256=`, read only Must-fix and Should-fix, relay them as a fix spec, then resume the same reviewer with "round N: per-item resolved?". The agent already writes the hash; the check and the section extraction are done by hand each time — recurrence: 7 (two rows) — candidate: maybe
  — **LANDED 2026-10-05 (triage: already landed, calibrated)** — Both codable halves existed before the row was filed: the DONE-line sha256 check is `h-mad/scripts/h_mad_done_gate.py` (`a65258df`, 2026-09-08; its `DONE_RE` at `:64` accepts `CHANGE-REVIEWER: DONE`), routed for change review at `h-mad/SKILL.md:3048-3058` (`1b8543c8`, 2026-10-04); "read only Must-fix and Should-fix" is `h_mad_audit_gate.py`, which on the 10-05 scratchpad reports gives must=2/should=8, 1/6, 1/8, 2/4, 1/6, 0/4 and agrees with an awk bullet count on every report checked. The by-hand loop was a skipped step, not a missing mechanism: 10-04 row-t used the gate (11 `h_mad_done_gate` command strings against 1 shasum), 10-05 ran `shasum|sed` 6 times against 2 `h_mad_done_gate` calls; no wrong report was read in either. The remainder (relay a fix spec, resume the same reviewer with "round N: per-item resolved?") is orchestrator agent-loop behaviour (SendMessage/Agent) that no script can enforce, and it conflicts with the fresh-reviewer-after-a-pivot evidence. Optional, not required to close: a `--sections` flag on `h_mad_done_gate.py` printing Must-fix/Should-fix after a PASS, to file only if the hand `shasum|sed` pattern recurs in another session.
