# H-MAD remediation sequence — bugs, gaps, candidates

Derived 2026-07-23 from `docs/skill-monitoring.md`, the archived report carry items, the
2026-07-22 handoffs, and a code read of `h-mad/scripts/`. Everything F/G/H/A-numbered is
already FIXED; this sequences what remains.

## Ordering principles

1. **Fix the instrument before you measure.** A live run is the only way to close the
   doc-verified gaps, and each run is expensive. Anything that changes what a run *records*
   must land before the run that would have been its first observation.
2. **Make a signal consumable before the run that depends on it.** An unread token is not a gate.
3. **One dogfood run closes several gaps at once** — the assembler cycle, the merge gate, and
   the handoff WRITE/READ protocol are all "verbs live-verified, prose doc-verified only".
   They share a single vehicle: a real 7-phase `/h-mad` feature.

## Constraint that shapes every fix

`invariants.base.md` §"Audit-gate signal discipline": any gate whose verdict the orchestrator
consumes MUST report PASS/FAIL as a **stdout token with exit 0**. Non-zero exit is reserved for
operational errors, because a non-zero exit registers as a Claude Code `PostToolUseFailure` and
leaks into coexisting plugins. So no remediation below may "fix" a weak signal by making it exit
non-zero. Signals get *canonical tokens* and *mandated reads*.

---

## Wave 1 · Instrumentation — `audit_cycles` counter (B1) — ✅ SHIPPED `5fa96ba`

**Shipped 2026-07-23.** 100% match rate, suite 498/0. Both cycle counters now derive from
versioned artifacts instead of state fields nothing incremented.

**Blocks:** every later verification that would cite a cycle count. Must be first.

`h_mad_state_write.py:53` seeds `{"plan":0,"design":0,"impl_plan":0}`; nothing anywhere
increments it. `h_mad_telemetry.py:46-58` reports the zeros faithfully. Measured on HemaSuite
`clinical-abbreviation-hygiene`: recorded 0/0/0, actual 1/2/2. Knock-on: the drift warning at
`h_mad_telemetry.py:122` (`audit_cycles > 3` → "possible plan/design quality drift") can never
fire, and `references/state-schema.md:18` documents non-zero values the code cannot produce.

- Wire an increment at the single place an audit cycle completes (the gate-verdict consumption
  point), not at N call sites — one writer, per the single-source base invariant.
- Add a regression test asserting the counter advances across two cycles of one phase.
- Verify the telemetry drift warning can fire by feeding a synthetic 4-cycle state.

**Done when:** a two-cycle plan audit records `plan: 2`, not `0`.

## Wave 2 · Signal consumability — preflight tokens (G-c) — ✅ SHIPPED `787aecf`

**Shipped 2026-07-23** as `preflight-signal-discipline`. 100% match rate (26/26 ACs), suite 530/0.
`env` emits `PREFLIGHT: PASS|FAIL [stale=…] [conflict=…]` with the exit code untouched; `SKILL.md`
mandates asserting it and `ASSEMBLE: PASS` before dispatch; the automation precheck gates on the
token **and** on agents being resolved. **J7 resolved** — `run()` injects a per-invocation
never-created pin path, so pinning and testing are no longer mutually exclusive (530 passed
identical with and without `.h-mad/orca-pins.env`; pre-fix baseline 17 failed / 136 passed).
6a-prime: cycle 1 `WITH_FIXES` → cycle 2 `READY_TO_MERGE`.

Validated live mid-run: agy's handle rotated during this feature's own 6a-prime re-review, the
new mandated read printed `PREFLIGHT: FAIL stale=agy`, and `send` refused — the same
handle-rotation class that lost the HemaSuite Task-2 RED dispatch.

**Carry (not closed by this wave):** FR-4/FR-5 are protocol, not machinery — nothing enforces
that an orchestrator performs the read. 6a-prime confirmed this is a real residue. **Wave 3 is
the exercise.** Also open: the CONFLICT case is unguarded at `send` (two agents on one *live*
handle is undetectable there; a *stale* handle is already refused by `912b93a`).

**Depends on:** nothing. **Blocks:** Wave 3 (the run should exercise the mandated reads).

`_cmd_env` prints `STALE` / `CONFLICT:` and returns 0 unconditionally. Correct per the signal
invariant — but no orchestrator step is *required* to read them, so a scripted
`hmad-dispatch env && dispatch …` still walks into a stale handle. That is exactly the failure
that lost a Task-2 RED dispatch on HemaSuite: no error, no report, no tests written.

- Give `env` a canonical terminal token line — `PREFLIGHT: PASS` / `PREFLIGHT: FAIL` — matching
  the `GATE:` / `ASSEMBLE:` shape already in use. Exit stays 0.
- Add the mandated read to `SKILL.md` Phase-5 preflight: the orchestrator asserts
  `PREFLIGHT: PASS` before the first dispatch of a run, and re-asserts after any re-pin.
- `ASSEMBLE: PASS|HALT` already complies; it needs only the same mandated-read step
  (`SKILL.md` §"Audit prompt assembly" 7.2).

**Done when:** a stale pin makes the Phase-5 preflight step fail the checklist, not just print.

## Wave 3 · Dogfood run — closes G-b + G-d — ✅ SHIPPED `4111297`

**Shipped 2026-07-23** as `preflight-read-enforcement` (feature/192). 100% match rate
(9/9 FRs, 37/37 ACs), suite 530 → **550**, 6a-prime `READY_TO_MERGE`, 76.1 min.

**Vehicle:** the payload was the Wave-2 carry itself — FR-4/FR-5 shipped as protocol with no
enforcement. `env` now writes a fingerprinted receipt on `PREFLIGHT: PASS`, and `send` refuses
(rc=1, nothing sent) unless that receipt exists, is within its TTL, and still matches resolution
at dispatch time. The previously unguarded agent-conflict case is refused at `send` too. **The
Wave-2 carry is closed:** dispatching without a passing preflight is now mechanically impossible,
verified live against the real wrapper on all four refusal reasons plus the positive path.

- **G-b closed** — four audit dispatches went live through `h_mad_assemble_audit.py`: plan,
  design, and impl-plan ×2 (cycle 1 raised a real should-fix). Previously only the plan recheck
  had ever reached a live reviewer.
- **G-d closed** — the merge gate ran from the skill prose: two gates created and resolved
  against a live orchestration task, both auto-recording clean merges.
- **G-a closed early (Wave 4's target)** — the Phase-5 worktree fanout ran for real for the
  first time: two Codex workers on independent modules in isolated Orca worktrees,
  `worktree-create → dispatch → commit → merge gate → merge → rm`, both merged clean.

**`audit_cycles` was NOT 0/0/0** — the expectation above was wrong. Wave 1 works, and this run
recorded `plan 1 / design 1 / impl_plan 2, iterate 1` with **`elapsed_min: 76.1`**. That is
Wave 4's done-when ("non-zero `audit_cycles` **and** a plausible `elapsed_min`") already
satisfied — achieved by passing `--started-ts` explicitly, since J8 is still unfixed.

**Five defects surfaced by running it** (`docs/skill-monitoring.md`), all filed unfixed:
J11 an unexecutable telemetry instruction · J12 `ASSEMBLE: PASS` returned for a prompt the script
predicts will fail — the same defect class Wave 2 fixed · J13 the oversize remedy that does not
reduce size when the design dominates · J14 the fanout dispatch/await path conflict ·
**J15 🔴 nothing tells a fanout worker to commit**, so the gate would merge an empty branch,
auto-record success, and `worktree-rm` would destroy the only copy of the work.

**Also measured:** the ~49 KB reviewer cliff did not reproduce — a 52,168 B prompt delivered by
file indirection was answered normally. The original measurement did not distinguish TUI paste
from agent-side file reads.

**Carry:** Wave-2's FR-5 (the `ASSEMBLE: PASS` mandated read) remains protocol, held out of scope
because this run dogfooded the assembler and changing the instrument mid-measurement would have
invalidated both. J12 now records a concrete defect in it.

## Wave 4 · Instrument slice ✅ SHIPPED `ab3657e` · candidates batch ✅ SHIPPED (Wave 4b)

**Depends on:** Wave 3 — now shipped. **Why combined:** the candidates decompose into
independent, non-conflicting files — the natural payload for the parallel fanout.

**Instrument slice shipped 2026-07-23** as `fanout-integrity-and-defects` (feature/193). 100%
match rate (9/9 FRs, 35/35 ACs), suite 550 → **592**, 6a-prime `READY_TO_MERGE`, 70.9 min.
J15, J14, J8 and J10 are all **fixed**:

- **J15** — `worktree-rm` refuses to remove a worktree holding uncommitted changes
  (`worktree_has_uncommitted_work`) or unmerged commits (`worktree_has_unmerged_commits`);
  `--force` overrides and says so. Guards the *irreversible* step rather than instructing the
  worker, because both Wave-3 workers had already been told to self-review and neither committed.
  **Validated against a real Orca worktree** in the exact Wave-3 shape: the worktree and the work
  both survived. **Fanout teardown must now pass `--base <feature-branch>`** — the default base
  resolves to `main`, so a module worktree branched from a feature branch reports every feature
  commit as unmerged (measured: 7 ahead of `main`, 1 ahead of its real base).
- **J14** — `worktree-create --prompt-file` registers a task and emits
  `[H-MAD] worktree_task task=<id> selector=<sel>` on stderr; stdout stays byte-identical.
- **J8** — `started_ts` defaults to `now(UTC)`. Verified live: a feature created without
  `--started-ts` now reports `elapsed_min 0.0` instead of ~29,744,612.
- **J10** — a contentless `DONE_WITH_CONCERNS` exits 2 instead of returning a verdict. The
  detector was replayed against the 13 real reports on this machine: **7 of 13 name no concern**,
  so J10 is the majority case, not the one-off it was filed as.

**Two guards were found VACUOUS by mutation testing and fixed** — the `--prompt-file` gate (the
suite passed whether or not it existed) and the `--base` documentation test (passed with the
guidance deleted). Neither was visible to review or to a green run.

**Wave 4b SHIPPED 2026-07-23** (feature/196). Suite 608 → **619**. Run directly rather than
via fanout: Wave 3 already closed G-a by running the fanout live, so it was no longer needed as
proof, and Phases 1–4 have user-approval gates that would stall an unattended run. Every item
below is mutation-tested — four assertions initially reported "enforced" against a harness that
had silently done nothing, because the phrases are line-wrapped and a literal `.replace()` matched
zero times while exiting 0. That is `## Mutation verification` catching its own commit.

| candidate | rec | landed as |
|---|---|---|
| `verify-the-mutation-not-the-command` | 3 | `invariants.base.md` §Mutation verification |
| `replay-the-incident-against-the-fix` | 4 | `invariants.base.md` §Incident replay (merged with `replay-detector-against-history`, rec 3) |
| `file-issue-then-fix-under-TDD` | 14 | `h_mad_issue_fix_gate.py` + SKILL.md protocol |
| `worktree-for-live-skill-edits` | 2 | SKILL.md §Editing this skill while a run is in flight |
| `sanitize-before-public-filing` | 2 | SKILL.md §Filing to a public tracker |
| `throwaway stub-harness probe` | 3 | SKILL.md §Confirming a suspected defect — as a **practice**, not a script |
| `staged-prompt repair sweep` | 2 | **DECLINED** — see below |

`staged-prompt repair sweep` was declined rather than deferred: every staged prompt on disk belongs
to one feature that shipped 2026-07-22, `/tmp` is scratch, and `h_mad_assemble_audit.py` regenerates
any prompt in one call. Building backup + in-flight-freshness logic to repair files nothing will
read again is cost without a beneficiary. Recorded in `docs/skill-candidates.md`.

`file-issue-then-fix-under-TDD` could not be scripted end-to-end: §"No new external dependency"
forbids the skill acquiring a new CLI, and `gh` is not one of its dependencies. The gate therefore
checks the **linkage** (issue ↔ test ↔ closing trailer) and prints `gh` commands without invoking
them — steps 1–4 stay discipline, step 5 is the only part a script can honestly check.

**Not in this batch** — five newer `candidate: yes` items accumulated after this plan was written
(`mutation-test-every-guard` rec 7, `verify-review-premise-before-acting` rec 4,
`tracer-bullet-design-assumptions` rec 4, `discriminating-regression-test` rec 3,
`label-guards-in-red-dispatch` rec 3). They are a Wave 4c decision, not silent scope creep.

Original payload, for provenance:

Payload, triaged by kind:

**Discipline → `invariants.base.md` (Axis B).** These two are the exact failure modes that bit
both repos repeatedly; they belong in the rubric that audits read, not in prose:
- `verify-the-mutation-not-the-command` (recurrence 3) — re-read resulting state after any
  git/shell mutation; caught two silent zsh no-ops that both looked like success.
- `replay-the-incident-against-the-fix` (recurrence 4) — validate against the historical data
  that motivated the fix, not only unit stubs; caught a wrong heuristic that unit tests passed.

**Tooling → scripts:**
- `file-issue-then-fix-under-TDD` (recurrence 14, verdict yes) — the highest-recurrence
  candidate on the list.
- `staged-prompt repair sweep` (2, maybe) — rewrite stale `/tmp/audit_*.txt` to current
  template output, with backups + an in-flight freshness guard.
- `throwaway stub-harness probe` (2, maybe) — scratch pytest importing dispatch-test helpers to
  confirm a suspected resolver hole before fixing it.

**Defects → scripts (folded in 2026-07-23 from Wave 2's findings).** Both are diagnosed to a
line and neither depends on Wave 3, so they can be pulled forward if the dogfood run slips:

- **J8 — `started_ts` defaults to the epoch.** `h_mad_state_write.py:138` reads
  `record["started_ts"] = started_ts or "1970-01-01T00:00:00Z"`, so any feature created without an
  explicit `--started-ts` is stamped with a hardcoded epoch sentinel and every telemetry row reports
  `elapsed_min ≈ 29744612` (≈56 years), overflowing its `:>9` column. Confirmed against
  `.h-mad/telemetry.jsonl`: the four pre-Wave-2 rows carry `started_ts='1970-01-01T00:00:00Z'`, while
  `preflight-signal-discipline` — created with `--started-ts` passed explicitly — carries a real
  timestamp and a sane `110.3m`. Fix: default to `now(UTC)`. **The transferable lesson belongs in the
  commit message:** a sentinel that is itself a *valid* timestamp cannot be distinguished from real
  data downstream, which is why this read as "the reader must be broken" for as long as it did.
  Existing rows stay wrong — the log is append-only history.
- **J10 — `DONE_WITH_CONCERNS` with no concerns stated.** A Codex dispatch returned that verdict
  while naming no concern anywhere in its report, handing the orchestrator a doubt it could neither
  act on nor distinguish from `DONE`. The verdict is machine-parsed and gates the module; reached for
  conservatively without content it degrades to noise and forces the full independent verification it
  exists to avoid. Two-sided fix: make the concern mandatory in
  `references/codex-implementer-prompt.md` ("if you cannot name one, report `DONE`"), and have
  `h_mad_extract_verdict.py` treat a contentless `DONE_WITH_CONCERNS` as an operational error rather
  than a verdict, so silence cannot masquerade as nuance.

**Prose notes → `SKILL.md`:**
- `worktree-for-live-skill-edits` (2) — edit a symlinked live skill in a worktree so an
  in-flight run keeps reading the merged tree.
- `sanitize-before-public-filing` (2) — grep issue bodies against a forbidden-term list
  (project names, slugs, local paths) before filing publicly.

**Done when:** the candidate items have landed. J8 and J10 are done, and the original telemetry
done-when was met by Wave 3. J8 is now fixed at the source, so a feature created *without*
`--started-ts` reports a real elapsed rather than ~56 years — the caveat in the previous version of
this line no longer applies.

## Wave 5 · ~~Blocked upstream~~ — **moot; closed by J16 (2026-07-23)**

**The join shipped and this wave no longer has content.** `_orca_find` now resolves identity in
Pass 0 by joining `orca worktree ps`'s `agents[].agentType` (keyed by `paneKey` = `<tabId>:<leafId>`)
to `terminal list`'s `.tabId`/`.leafId`. Verified live on the exact listing that motivated the wave:
with pins bypassed, both agents previously resolved to **0 candidates** and now resolve correctly —
including a pane whose `.title` reads `"Codex - skills repo"` while actually running Antigravity.
See `docs/skill-monitoring.md` §J16.

**[stablyai/orca#9870](https://github.com/stablyai/orca/issues/9870) — CLOSED 2026-07-23 as
completed.** The premise ("Orca exposes no field naming the running program") was true only of
`terminal list`; `worktree ps` had carried the field all along. Reported upstream with the
before/after measurement and closed. Nothing in this repo waits on it.

One residual gap was stated in the closing comment rather than tracked: a plain `terminal create`
shell is absent from `agents[]` (verified), but whether a **human-adopted** pane — someone typing
`codex` into an already-open shell — registers there was not established. If it does not, an
Orca-side `titleSource: "osc"|"tab"|"assigned"` discriminator would still have standalone value.
That would be a new, narrower issue, not this one.

The pre-existing mitigations remain the durable path and are unchanged: `hmad-dispatch launch
<agent>` captures the handle at t=0 from the create response, and `pin`/`pin-agents` fail loud for
an operator-launched pane. Owning the launch still beats resolving after the fact; Pass 0 is what
makes an *un-owned* pane recoverable instead of UNRESOLVED.

Do not sequence work behind #9870.

---

## Explicitly dropped

- **Stale cmux surface map** — already fixed. `hmad-dispatch.sh:77-87` does title-token matching
  with n-candidate ambiguity and a fail-loud pin message; the hardcoded `codex→surface:5` /
  `agy→surface:2` no longer exists.
- **`ASSEMBLE: HALT` exits 0** — deliberate, documented at `h_mad_assemble_audit.py:13-17` and
  required by the signal-discipline base invariant. Not a defect.
- **`hmad-dispatch env` stale-pin bug** — FIXED by `912b93a`; the HemaSuite handoff's
  "file upstream" step is obsolete for this half.
- **Plan-doc `status:` frontmatter** — deferred. `docs/01-plan/features/*.plan.md` carries none,
  so the handoff scout surfaces no backlog signal, but those are HemaSuite-facing product plans,
  not this repo's work.

## Sequence at a glance

| Wave | Work | Closes | Gate to next |
|---|---|---|---|
| 1 | `audit_cycles` counter | B1 | counter advances in a test |
| 2 | `PREFLIGHT:` token + mandated reads | G-c | stale pin fails the checklist |
| 3 | dogfood `/h-mad` on Waves 1–2 ✅ `4111297` | G-b, G-d, **G-a**, **B1 proof** | done — 4 live audits, 2 merge gates, fanout ran live, telemetry 1/1/2 + 76.1m |
| 4a ✅ `ab3657e` | J15/J14/J8/J10 — the instrument | defects | done; fanout is now safe |
| 4b ✅ | candidates batch (run directly) | 6 candidates landed, 1 declined | done; suite 619 |
| 5 | ~~watch #9870~~ — **moot**, J16 paneKey join shipped | H5 residual, J16 | done; #9870 closed as completed |
