---
name: h-mad
description: Orchestrate the 7-phase H-MAD (Hawk Multi-Agents Development) workflow end-to-end. Standalone — no external skill dependencies (spec-kit, b-mad, or pdca). All phase protocols are built-in. Project-agnostic; splices project-specific Axis B invariants from `<PROJECT_ROOT>/.h-mad/invariants.md` into audit prompts at dispatch time. Use when user invokes /h-mad "<feature>", /h-mad do "<feature>", /h-mad status, or /h-mad reset "<feature>".
---

# /h-mad — 7-phase H-MAD Orchestrator (v2.2, standalone)

## Activation surface

| Invocation | What you do |
|---|---|
| `/h-mad "<feature>"` | Auto-bootstrap if needed, then smart-resume via `h_mad_resume_decision.py`; act per the returned token. |
| `/h-mad do "<feature>"` | Auto-bootstrap if needed. Force-start Phase 5. Run `h_mad_do_preconditions.py` first; refuse if non-zero. |
| `/h-mad status [<feature>]` | Auto-bootstrap if needed. Read-only. Print state from `docs/.bkit-memory.json`. Surface stale `phase = "step5"` flags (heuristic: `autonomous_entry_ts > 60min` ago AND `halt_reason = null`). |
| `/h-mad reset "<feature>"` | Clear `orchestrator_state[<feature>]`. Do NOT delete docs or revert git. |
| `/h-mad bootstrap` | Explicit bootstrap (idempotent re-run). Not required as first step — feature invocations auto-bootstrap. |

## First-run auto-bootstrap

Before any feature-level operation, check:
1. Does `.h-mad/invariants.md` exist in the current working directory (project root)?
2. Does `docs/.bkit-memory.json` exist?

If either is missing → run bootstrap automatically, then continue with the requested operation.

## Bootstrap action

Run from current project root (`pwd` at invocation):

1. **Create docs structure**:
   ```bash
   mkdir -p docs/01-plan/features docs/02-design/features docs/03-analysis docs/04-report/features docs/archive .h-mad
   ```

2. **Create `docs/.bkit-memory.json` if missing**:
   ```bash
   [ -f docs/.bkit-memory.json ] || cat > docs/.bkit-memory.json <<'EOF'
   {
     "version": 1,
     "orchestrator_state": {}
   }
   EOF
   ```

3. **Copy invariants example if missing**:
   ```bash
   [ -f .h-mad/invariants.md ] || cp ~/.claude/skills/h-mad/invariants.example.md .h-mad/invariants.md
   ```

4. **Surface customize-this notice**:
   > "Bootstrap complete. Customize `.h-mad/invariants.md` with your project's Axis B invariants (currently contains a worked example — replace with your own rules). The orchestrator inlines this file as the Axis B rubric for plan/design/impl-plan audits and the Phase 6a-prime architectural review."

5. **Optionally suggest** `.gitignore` additions if user wants `docs/.bkit-memory.json` out of git.

Bootstrap does NOT touch existing files, modify git config, or author plan/design/impl-plan docs.

## Decision routing (for `/h-mad "<feature>"`)

Run: `python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature "<feature>" --session-id "<this session's id>"`

Pass `--session-id` so the collision check runs; omitting it opts out and you
will not see `owned_elsewhere`. On any token other than `owned_elsewhere`, claim
the feature before working it, and release when you stop:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature "<feature>" --claim "<session-id>"      # ... work ... then --release
```

The claim is **advisory** — it reports who holds a feature and when they were
last seen, so a second session makes a deliberate choice rather than an
accidental one. A claim older than two hours is treated as abandoned, so a
crashed session cannot own a feature permanently.

**Then check that the state still describes reality**, before acting on it:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_staleness.py \
  docs/.bkit-memory.json --feature "<feature>"
```

The schema validates a record's *shape*; this compares its *contents* against
git. Both directions have been observed on one feature in a day — a
`halt_reason` that outlived its resolution by four hours and eight shipped
modules, and a `last_completed_phase` still reading 4 after Phase 5 had merged
and pushed. The first routes a resume to `halted` and presents a solved problem
as the blocker; the second routes to `enter_autonomous` and redoes merged work.
Both records validated cleanly the whole time.

`STALENESS: CLEAN` → the state is consistent with git. `STALENESS: SUSPECT` →
each finding names what disagrees. It **reports, it does not adjudicate** —
the failure being fixed is silent confidence, not a wrong guess, so decide
yourself and correct the record with `h_mad_state_write.py`.

| Token | What you do |
|---|---|
| `owned_elsewhere` | Another session holds this feature and was seen within the staleness window. **Stop and surface it** — print the owner id and heartbeat, and ask whether to coordinate, take over (`--claim <id> --force`), or pick a different feature. Never proceed silently: two sessions on one feature produce contradictory conclusions on the same branch. |
| `start_fresh` | Initialize `orchestrator_state[<feature>]`. Enter Phase 1. |
| `resume_manual` | Print current phase + last marker. Ask "continue from phase <N>?" |
| `enter_autonomous` | Print "all manual checkpoints clear; entering autonomous block." Enter Phase 5. |
| `halted` | **Run the staleness check first** (below) — a halt that commits landed after is usually already resolved. Then print `halt_reason` + recovery hints (see `references/failure-recovery.md`). Ask "resume, retry, or reset?" |
| `complete` | Print "feature complete; see docs/archive/<YYYY-MM>/<feature>/". Exit. |

## Per-phase actions

See `references/phase-table.md` for the full gate table. Detailed inline protocols in `references/inline-protocols.md`.

1. **Brainstorm** — run inline brainstorm protocol (`references/inline-protocols.md §Phase 1`). Output: `docs/01-plan/features/<feature>-brainstorm.md`. Wait for user approval.
2. **Specify** — run inline spec protocol (`references/inline-protocols.md §Phase 2`). Output: `docs/01-plan/features/<feature>.spec.md`. Wait for user approval.
3. **Plan + Audit-Plan** — run inline plan generation (`references/inline-protocols.md §Phase 3`). Output: `docs/01-plan/features/<feature>.plan.md`. Wait for user-approved v1.0, then auto-cycle: audit-plan via agy → awk gate → if must-fix > 0 OR should-fix > 0, surface bullets + wait for user revision → re-audit. **Exit ONLY when both must-fix = 0 AND should-fix = 0.** No cycle cap — the rationale is that if errors are already known (whether breakage-level or improvement-level), shipping them is worse than burning more cycles. Operator escape at any cycle: author `.audit.v<N+1>.md` with `## Acknowledged-not-fixed` section listing the should-fix items the operator chooses to defer, commit `[audit-override]`, and the gate treats those items as cleared.
4. **Design + Audit-Design** — run inline design generation (`references/inline-protocols.md §Phase 4`). Output: `docs/02-design/features/<feature>.design.md`. Same audit cycle pattern as Phase 3. Back-propagation: if design revision invalidates a plan decision, return to Phase 3 to re-clean, then re-enter Phase 4 audit from cycle 1.
5. **Implementation (autonomous)** — see Phase 5 sub-section below.
6. **Verification (autonomous)** — run inline gap analysis (`references/inline-protocols.md §Phase 6`). If match rate < 90%, run inline iterate (`references/inline-protocols.md §Phase 6b`) — 5-cycle cap. Loop until ≥90% AND 100% test pass. Phase 6a-prime is an agy architectural review before gap analysis.
7. **Closure (autonomous)** — **run the precondition gate first; it is what makes the 6-before-7 ordering real rather than documented:**
   ```bash
   python3 ~/.claude/skills/h-mad/scripts/h_mad_phase7_preconditions.py \
     docs/.bkit-memory.json --feature <feature>
   ```
   Parse the **token**, not `$?` (exit 0 on any verdict, 2 on operational error). `PHASE7: BLOCKED` → halt `step7:verification_not_run` and address each blocker. It refuses to close a feature that never ran Phase 6, whose analysis is missing or states no match rate, whose rate is below threshold, whose 6a-prime returned `WITH_FIXES`/`NO`, or that carries an open halt. A `SKIPPED_NO_PANE` archreview is a **warning**, not a blocker — carry it into the report per §6a-prime. Then `h_mad_telemetry.py record`, inline report + archive (`references/inline-protocols.md §Phase 7`), then `git add -A && git commit && git push origin main`.

## Phase 5 (Implementation) sub-steps

**Substrate preflight (Phase 5 + first audit dispatch).** Run `hmad-dispatch env`.
If it exits non-zero → halt `<phase>:no_substrate`. Record the printed substrate +
agent mapping via `scripts/h_mad_telemetry.py` so the run log states which environment
it dispatched under. This is the explicit environment check (cmux vs orca) — do it
before any `send`/`read`. See `references/agent-substrate.md`.

**Dispatch enforcement.** `env` ends with a canonical `PREFLIGHT:` line and writes a
receipt when the verdict is `PASS`:

```text
PREFLIGHT: PASS
PREFLIGHT: FAIL stale=codex
PREFLIGHT: FAIL conflict=term_x
PREFLIGHT: FAIL stale=codex,agy conflict=term_x
```

- `hmad-dispatch send` **refuses with rc=1 and sends nothing unless a valid receipt
  exists**. The receipt must say `PASS`, be within its TTL, and still match the
  current handle resolution. The refusal reason token is one of
  `preflight_not_run`, `preflight_expired`, `preflight_handles_rotated`, or
  `preflight_agent_conflict`.
- Recover `preflight_not_run` by running `hmad-dispatch env` and confirming
  `PREFLIGHT: PASS`, then retry. Recover `preflight_expired` by running `hmad-dispatch
  env` again to refresh the receipt, then retry.
- Recover `preflight_handles_rotated` by re-pin or relaunch the affected agent,
  run `hmad-dispatch env` again, and retry. Recover `preflight_agent_conflict` by
  pinning distinct handles for codex and agy, then run `hmad-dispatch env` again
  and retry. `clear` and `interrupt` remain unguarded recovery verbs.
- Re-assert `PREFLIGHT: PASS` after any re-pin (`pin`, `pin-agents`, `launch`);
  otherwise halt `<phase>:preflight_failed` and recover using the matching token.
- **Read the token, never `$?`.** `env` exits 0 on *both* verdicts by design — the base
  invariant on audit-gate signal discipline reserves a non-zero exit for genuine
  operational errors, because it registers as a `PostToolUseFailure` and leaks into
  coexisting plugins. A FAIL therefore cannot be detected by exit status, and
  `hmad-dispatch env && …` is **not** a guard. The send refusal is the enforced guard.
- `FAIL` is raised by a stale pin or a codex/agy handle collision only. An `UNRESOLVED`
  agent is *not* a failure — it is the ordinary state of a session that is not
  dispatching. Dispatch-readiness is `pin-agents`' job (it exits 1 on unresolved).

The detection has been in `env` for a while; what was missing was any step obliged to
consume it, which made a correct signal advisory. Skipping this assertion re-opens the
exact failure the token was added to close.

**Pin the agents once (Orca) — do it while identity is known.** Immediately after
a clean `env` under orca, run `hmad-dispatch pin-agents` to freeze the resolved
codex+agy handles into the session pin file, so later dispatches survive preview
decay. **Codex has no title identity at all, by construction.** Orca's `.title` is
the pane program's OSC title if it emits one and otherwise the enclosing *tab's*
title — and a tab title is shared by every leaf in that tab. Codex emits no OSC
title, so any `.title` matching `codex` was inherited and says nothing about what
runs in that pane. Observed live 2026-07-22: an **agy** pane sitting in a tab named
`Codex - skills repo` matched `^codex`; both agents return a well-formed sentinel
report, so handing Codex's work to agy would have been silent. Auto-detect therefore
never matches Codex on title — only on a fresh pane's `gpt-N` banner, which scrolls
off once it works.

**Identity does exist — in a different call (J16, shipped 2026-07-23).** `orca worktree ps`
returns `agents[].agentType` keyed by a `paneKey` of `<tabId>:<leafId>`, and `terminal
list` returns `.tabId`/`.leafId`. `_orca_find` joins them as **Pass 0**, ahead of the
title and preview passes, which resolves the case above exactly: measured live with pins
bypassed, both agents went from `UNRESOLVED` to correct. `agentType` is `antigravity`,
not `agy`. This does not retire pinning — handles still rotate, and `launch` still owns
identity best — but an un-owned pane is now recoverable. (stablyai/orca#9870, which asked
for this field, is closed as completed — it already existed in `worktree ps`.)

**A pin file records intent, not state.** Handles rotate. Measured on 2026-07-22:
every Orca handle rotated mid-run, `env` still printed the dead pins, and a dispatch
reported `Sent 7293 bytes` into a stale handle and simply vanished — no error, no
report file, no work done. **"Sent N bytes" is not delivery, and a resolvable pin is
not a live pane.** The wrapper now checks liveness at each point where a wrong handle
is cheap to catch:

| verb | behaviour on a handle the listing proves is gone |
|---|---|
| `pin` / `pin-agents` | refuses to write it (`pin --force` to pin a pane that does not exist yet) |
| `env` | prints `<handle> STALE` plus a `stale pins:` line — never as addressable |
| `send` | refuses, `terminal_handle_stale`, **nothing is sent** |
| `verify <agent>` | 0 live · 1 unresolved/`stale_pin` · 2 unknown agent |
| `resolve` | echoes the pin unverified, by design — pass `--verify` for the check |
| `worktree-rm` | refuses with `worktree_has_uncommitted_work` or `worktree_has_unmerged_commits`; pass `--force` to skip both guards |

`env` also prints `CONFLICT:` when codex and agy resolve to the **same** handle. Two
agents cannot be one pane, so identical handles prove at least one resolution is
wrong — and that is precisely the shape a tab-inherited title produces. Pin both
explicitly when you see it.

Only *positive* evidence blocks anything: if `orca terminal list` cannot be read at
all, the send still goes, because a pin has to keep working when the listing does
not. `resolve` stays listing-independent for the same reason — use `verify` when you
need the check.

**A missing report is neither pass nor fail.** If `report-wait` times out, read the
pane before concluding anything: `terminal_handle_stale` means the dispatch never
landed, and `Selected model is at capacity` means the agent stopped after doing the
work. Check the working tree for work completed but never reported. `pin-agents` therefore **fails
loud (rc=1)** if it cannot resolve an agent, naming the missing one and the exact
env var to set; a run must not proceed with Codex unpinned. If Codex does not
auto-resolve, read its handle from `orca terminal list` and
`export HMAD_ORCA_CODEX_TERMINAL=<handle>` (ideally captured right after launching
Codex, before it works), then re-run `pin-agents`. The env-var pin always
overrides; `pin-agents --clear` resets. Skip on cmux (surface pins there).
**Zero-manual alternative**: to start a FRESH agent rather than reuse an
operator-launched pane, `hmad-dispatch launch <codex|agy>` runs `orca terminal
create` and captures the handle from the create response, pinning it at spawn —
no title/preview dependence, no manual pin (H5). Use `launch` when h-mad owns the
agent; `pin`/`pin-agents` when adopting an existing pane.

- **5a** — arm hook + generate impl-plan via inline impl-plan protocol (`references/inline-protocols.md §Phase 5`). Write `orchestrator_state.<feature>.phase = "step5"` + `autonomous_entry_ts = <now>`. Output: `docs/01-plan/features/<feature>.impl-plan.md`.
- **5b** — auto-audit impl-plan (same agy audit-prompt mechanism as Phases 3/4 — see §"Audit prompt assembly"). Write audit to `docs/01-plan/features/<feature>.impl-plan.audit.v<N>.md`. Run awk gate. If must-fix > 0 OR should-fix > 0, regenerate impl-plan with both must-fix AND should-fix bullets appended; cycle until **both must-fix = 0 AND should-fix = 0**. No cycle cap — same rationale as Phase 3 (known errors at any severity worth fixing > shipping). Operator escape at any cycle: author `.impl-plan.audit.v<N+1>.md` with `## Acknowledged-not-fixed` listing deferred should-fix items, commit `[audit-override]`, gate treats those as cleared.
- **5c** — baseline branch: `git checkout -b feature/NNN-<slug>`; commit impl-plan + audit files.
- **5d** — RED dispatch via `hmad-dispatch send` (see `references/codex-implementer-prompt.md`). Verify codex + agy alive (`hmad-dispatch alive codex` && `hmad-dispatch alive agy`); refuse if missing → halt `step5d:no_<agent>_pane`. **Immediately after confirming each pane is alive, clear its context** (see §"Agent-pane context hygiene") so no prior-feature/prior-cycle conversation bleeds into this feature's TDD. For each module, dispatch Codex for tests; dispatch agy for coverage review. **In the dispatch, state the expected failing/passing counts for the task and label any regression guards** — tests asserting behaviour that already works, which must pass from the first run. Read each `STATUS:` with `h_mad_extract_verdict.py` (§"Reading a dispatch verdict"); no extractable verdict after a re-read and re-dispatch → halt `step5d:no_verdict:<module>`. Then verify the results **match the stated counts**; halt `step5d:red_not_all_failing` when an unlabelled test passes without implementation.

  Not every RED task is all-new behaviour. A refactor-shaped task legitimately lands with most of its tests green, and a blanket "every test must FAIL" halts a correct RED — worse, the cheapest way for an implementer to satisfy it is to weaken an assertion or assert the current buggy value, manufacturing a failure that then "passes" in 5e without anything being fixed. Stating the counts up front makes the check discriminating in both directions: an unexpected pass still halts, and an expected one does not.
- **5e** — GREEN dispatch via `hmad-dispatch send` (`references/codex-implementer-prompt.md` + `references/agy-spec-reviewer-prompt.md`). Re-verify the Codex + agy panes alive and **clear each pane's context** (§"Agent-pane context hygiene") before the first GREEN dispatch of a feature. For each module, dispatch Codex for implementation; dispatch agy for spec-compliance review. Read both verdicts with `h_mad_extract_verdict.py` (§"Reading a dispatch verdict") — never by grepping the scrape for the halt value, which turns an agent's silence into a pass. If agy returns `VERDICT: DRIFT` → halt `step5e-review:spec_drift:<module>`. If no verdict can be extracted after a re-read and re-dispatch → halt `step5e:no_verdict:<module>`. On 3rd consecutive GREEN failure → halt `step5e:green_unreachable:<module>`.
- **5f** — run full test suite: `pytest <project>/tests/ -v --tb=short`. All must pass (100%). Any failure → halt.
- **5g** — `git add -A && git commit -m "feat(<feature>): implement <module>"` per module. Write `phase = null` (disarms TDD gate hook). Emit `[H-MAD] <feature> phase5 complete`.

## Phase 5 parallel fanout (Orca only)

The serial Phase 5 path above remains the default and fallback. First partition the
impl-plan: a task with `Dependencies on other tasks: None` is independent; every
other task is dependent and remains serial in topological order on the shared tree.

Engage fanout IFF `hmad-dispatch env` shows `substrate=orca` (the command displays
`substrate: orca`) AND `orchestration: on` AND there are `≥2 independent` tasks.
If any condition is unmet, use the existing serial fallback.

For each independent task, run at most `HMAD_ORCA_MAX_WORKTREES` live worktrees
(default 4). With a staged prompt, `worktree-create <module> --base
<feature-branch> --prompt-file <staged-prompt>` creates the worktree and registers
the task in one operation. It keeps stdout exactly the worktree selector and
prints `[H-MAD] worktree_task task=<id> selector=<sel>` on stderr; capture that
`<id>` as the task-id for `dispatch`, `await`, and `gate-create`. If no prompt
file is supplied, `worktree-create` registers no task: use the separate Tier-2
`task-create` then `dispatch --to <selector>` path and its returned task-id.
Then `await` the worker; stamp progress checkpoints and run the **winner-merge decision gate**
in place of a bare `git merge --no-ff` (see `references/orchestration-mode.md`
§"Winner-merge decision gate" and §"Progress checkpoints"); then `worktree-rm
<selector> --base <feature-branch>`. Tasks beyond the cap queue and log
`[H-MAD] worktree_queued module=<module>`.

**Pass `--base <feature-branch>` on fanout teardown.** The comparison base defaults to the
first of `origin/HEAD`, `main`, `master` that resolves, and a module worktree is branched
from the *feature* branch — so every commit on that feature is "not in `main`" and teardown
refuses for as long as the feature is unmerged. Measured live: a freshly created module
worktree reported 7 commits ahead of `main` and 1 ahead of its real base. With `--base` set
to the feature branch, the guard fires only on commits the feature branch does not have —
which is exactly the work that would be lost.

The gate engages only when `orchestration: on`: a clean verdict + clean merge
auto-records a `yes` decision (`[H-MAD] merge_gate auto-resolved`) without pausing,
while a `DRIFT`/non-clean verdict or a merge conflict opens a **blocking** gate for
a human decision (conflict path first runs `git merge --abort` and emits
`[H-MAD] merge_conflict module=<module>`). When orchestration is off, the merge is
the unchanged serial `git merge --no-ff`, conflict-aborted and re-dispatched serially
as before — no gate. On any Phase-5 halt during fanout, enumerate with `worktree-ps`
and run `worktree-rm` for every worktree in the fanout group. `worktree-rm`
refuses with rc=1 and removes nothing when the resolved worktree has uncommitted
work (`worktree_has_uncommitted_work`) or commits not reachable from its
comparison base (`worktree_has_unmerged_commits`); commit or merge the work
first, or pass `--force` when discarding it is intentional. `--force` skips both
guards and prints `[H-MAD] worktree-rm forced selector=<sel> — guards skipped`.
An unresolvable or ambiguous selector, or a truncated `worktree-ps` listing,
means the worktree cannot be checked and does not by itself refuse removal.
This teardown remains idempotent: a gone selector logs and no-ops.

## Phase 6 (Verification) sub-steps

- **6a-prime** — architectural review via agy (`references/agy-architectural-reviewer-prompt.md`). Inputs: Phase 5 diff (BASE = 5c sha; HEAD = 5g sha) + audited design.
  **Preflight, before anything else: `hmad-dispatch alive agy`** (or read `hmad-dispatch env`). If the pane does not resolve — `agy -> UNRESOLVED`, the normal state in any session not started beside a reviewer — **halt `step6a-prime:no_reviewer_pane`**. Do not skip the step and continue to 6a. This mirrors 5d's refuse-on-missing-pane rule, and it exists because skipping is the path of least resistance and nothing else marks the omission: 6a-prime is the only pass positioned to catch design-level problems — design-vs-spec drift, an exception hierarchy that does not scale, a gate at the wrong altitude — and both the document audits and the code-level gap analysis miss those by construction.
  **A skipped review is not a pass.** If the operator elects to proceed without a reviewer, record `archreview: "SKIPPED_NO_PANE"` in `orchestrator_state[<feature>]` and carry it into the Phase 7 report, so the feature cannot close with a reader believing an architectural review happened. Never record it as `READY_TO_MERGE`.
  **Clear the agy pane's context first** (§"Agent-pane context hygiene") — 6a-prime is a fresh architectural pass, not a continuation of the plan/design audit thread. Read the `ASSESSMENT:` with `h_mad_extract_verdict.py` (§"Reading a dispatch verdict") — grepping for `WITH_FIXES`/`NO` makes an empty review indistinguishable from `READY_TO_MERGE`. Halt `step6a-prime:architectural_review_failed` on `WITH_FIXES` or `NO`; halt `step6a-prime:no_verdict` if none can be extracted after a re-read and re-dispatch.
- **6a** — run inline gap analysis. Parse match rate from `docs/03-analysis/<feature>.analysis.md`.
- **6b** — if < 90%, run inline iterate (5-cycle cap). Loop until ≥90% AND 100% test pass.

### Surfacing diffs at review gates (Orca only)

At Phase 3 plan approval, Phase 4 design approval, and Phase 6a verification, the
orchestrator MAY call `hmad-dispatch file-open-changed --mode diff` (or
`hmad-dispatch file-diff <path>`) to surface the diff in Orca's editor. This is
best-effort and non-blocking: a non-zero result (substrate≠orca or no editor) is
logged as `[H-MAD] <feature> diff_surface_skipped`, and the gate proceeds exactly
as today. Surfacing is never a gate precondition; the cmux review flow is unchanged.

HemaSuite may use `file-diff <manuscript.docx>` to surface a generated manuscript
DOCX; this is documented usage only, with no HemaSuite code in this feature.

## Reading a dispatch verdict

Every dispatch that gates a decision ends in a machine-parsed line, and each is
read off a live pane:

| Step | Key | Values |
|---|---|---|
| 5d / 5e codex | `STATUS:` | `DONE` \| `DONE_WITH_CONCERNS` \| `BLOCKED` \| `NEEDS_CONTEXT` |
| 5e-review agy | `VERDICT:` | `COMPLIANT` \| `DRIFT` |
| 6a-prime agy | `ASSESSMENT:` | `READY_TO_MERGE` \| `WITH_FIXES` \| `NO` |

**Never grep the scrape for the halt value.** The halt conditions are phrased
as "halt on `DRIFT`", "halt on `WITH_FIXES` or `NO`" — so a grep that finds
nothing looks identical to a clean pass. An agent that dispatched, went idle
and emitted nothing therefore reads as approval, and the module gets committed
on silence. A prior module's `STATUS: DONE` still in scrollback is the same
trap from the other direction.

Extract instead, which fails closed on both:

```bash
hmad-dispatch read <agent> --lines 200 > /tmp/scrape_<feature>_<module>.txt
python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_verdict.py \
  /tmp/scrape_<feature>_<module>.txt --key VERDICT \
  --feature <feature> --phase 5e
```

It takes the **last** matching line, validates the value against the contract,
and exits 2 printing nothing when the line is absent, empty, or off-contract.
Treat exit 2 as "no verdict", never as a pass: re-read with a larger `--lines`,
and if the agent genuinely produced nothing, `hmad-dispatch clear <agent>` and
re-dispatch. Repeated silence is a halt (`step5e:no_verdict:<module>`), not a
reason to proceed.

## Verifying a review finding before acting on it

A finding from agy or a code reviewer arrives verdict-shaped — a premise, a consequence, and a
prescription — and the prescription is the part you are tempted to apply. Before applying it,
**check its stated premise against the source**. If the premise is wrong, the prescription is
usually wrong in a specific and expensive way: it is aimed at a mechanism that is not there.

Measured: in one session **2 of 5 findings were right about the symptom and wrong about the cause**.
Applying either prescription verbatim would have introduced a defect while closing a real finding —
the reviewer had seen something genuine and misattributed it, so the fix moved the bug rather than
removing it.

This is not a licence to dismiss findings. A finding whose premise fails to check is still
evidence that *something* is wrong: the reviewer saw a real symptom. Re-derive the cause from the
source, then fix that — and say in the response that the premise did not hold, so the next reviewer
is not re-litigating a settled point.

Cheap and mechanical: for each finding, open the file and line it names and confirm the code says
what the finding says it says. Most premises check out in seconds, and the ones that do not are
where the expensive mistakes live.

## Agent-pane context hygiene

The codex and agy agents are **long-lived REPLs reused across every audit cycle, feature, and session**. Their conversation context accumulates: a plan-audit thread bleeds into the next design audit, one feature's TDD bleeds into the next feature's, and stale scrollback pollutes the `hmad-dispatch read` output you later grep for a verdict. Clear the context at the boundaries below so each fresh pass starts clean.

**When to clear (fresh pass) vs keep warm (continuation):**
- **Clear** at: the first cycle of each audit phase (Phase 3/4/5b cycle 1); 5d and the first 5e dispatch of a feature; 6a-prime; and whenever you confirm a pane is alive at the *start* of a new feature.
- **Keep warm** at: cycles 2..N of the *same* audit (the running revision thread — "here's the fix for your prior should-fix" — is exactly the context you want); a Codex GREEN retry within the same module.

**How to clear (per pane), then verify it took:**
```bash
# agy (Antigravity CLI) and codex both accept /clear:
hmad-dispatch clear codex
hmad-dispatch clear agy
# verify a clean prompt (no leftover input, not mid-run):
hmad-dispatch read <agent> --lines 6
```
If `/clear` is not honored or the pane is wedged (input box still shows queued text, or a 400/desync on agy), **restart the surface** instead: re-seed via the launch command (`agy --dangerously-skip-permissions` / the Codex CLI) per `AGENTS.md`, then re-confirm alive with `hmad-dispatch alive <agent>`. A restart is the hard reset; `/clear` is the cheap one. Never dispatch an audit/TDD prompt into a pane whose scrollback still shows the previous cycle's report — you will grep the wrong verdict.

**Cost note:** clearing is cheap and prevents two failure modes seen in practice — (a) an audit verdict influenced by an unrelated prior feature's discussion, and (b) `hmad-dispatch read` returning a stale prior-cycle report that the gate then parses as this cycle's result.

### Orchestration mode (Orca)

When `hmad-dispatch env` reports `orchestration: on` (Orca plus an `HMAD_ORCA_COORDINATOR_TERMINAL` pin), dispatch, verdict collection, and decision gates SHOULD use the structured orchestration verbs rather than screen scraping. The `send` / `read` / `wait` scrape flow remains the universal fallback for cmux or an unpinned coordinator. See `references/orchestration-mode.md`.

### Scheduling HemaSuite live-e2e as Orca automations (Orca only)

HemaSuite wiring is documented usage only: no HemaSuite code is changed by these lifecycle wrappers, and HemaSuite must execute in an Orca workspace. To schedule a nightly live-e2e, stage the prompt in a file and create the automation:

```bash
hmad-dispatch automation-create --name anemia-e2e --trigger cron --prompt-file <prompt-file> \
  --provider claude --precheck "hpw doctor" --repo HemaSuite
```

`--provider` must be a provider Orca recognizes — verified live-valid values are `claude`, `codex`, `gemini` (NOT `agent`; Orca rejects unknown providers with `invalid_argument`). Target the run with `--repo <name>` (or `--workspace`/`--project`). Note `--trigger` (`preset|cron|rrule`) and `--schedule` are mutually exclusive; a preset such as `daily` needs no `--schedule`.

Run one ad hoc with `hmad-dispatch automation-run <id>`, enumerate configured jobs with `hmad-dispatch automation-list`, and clean up with `hmad-dispatch automation-remove <id>`. The `<id>` is the automation id returned by `automation-create` (extracted from `.result.automation.id`), NOT the response envelope id.

## Halt protocol

See `references/failure-recovery.md` for per-phase routes + recovery hints.

1. Write `orchestrator_state[<feature>]`: `halt_reason = "<phase>:<sub-step>:<description>"`, `halt_ts = <now>`, `phase = null`. Pin `current_phase` + `last_completed_phase`.
2. Emit `[H-MAD] <feature> phase<N> halted reason=<reason>`.
3. `hmad-dispatch notify "/h-mad halted" "<reason>"`.
4. Print recovery hints.
5. Exit.

## What you NEVER do

- Never skip the gate (`h_mad_audit_gate.py`) after an audit.
- Never parse the gate via `$?`/exit code — parse the `GATE:` token; the gate exits 0 on a verdict by design.
- Never auto-merge on `WITH_FIXES` or `NO` from agy.
- Never write `phase = null` before Phase 5g completes (that disarms the TDD hook prematurely).
- Never run `git push --force`.
- Never invoke Codex or agy directly — always via `hmad-dispatch` (see `references/agent-substrate.md`), which also picks inline vs file-indirection delivery by prompt size, per CLAUDE.md §F-12.

## Editing this skill while a run is in flight

`~/.claude/skills/h-mad` **is a symlink into this repository**, so editing the working tree edits
the *live* skill. A run already in progress will read whatever is on disk at the moment it next
opens a file — including a half-finished edit, or a script whose test has not been written yet.

When a run is in flight, **edit in a git worktree** and merge when it is clean; the in-flight run
keeps reading the merged tree and never sees an intermediate state. `hmad-dispatch worktree-create`
already does this for fanout modules; the same applies to the operator editing by hand.

Two second-order consequences, both observed:
- The suites are coupled. A sibling repo's tests reach these scripts *through the symlink*, so a
  change here can fail a suite in a repo you did not touch. Run both before merging.
- Never run a history-rewriting git command (`reset --hard`, `checkout --`, `stash`) with
  uncommitted skill edits in the tree. Commit first — this is `## Mutation verification` applied
  to your own work, and a lost implementation is indistinguishable from one never written.

## Confirming a suspected defect before fixing it

When you suspect a hole in a resolver, guard, or parser, **confirm it empirically before designing
the fix**. Write a throwaway probe that **drives the real function through the existing test
helpers** — source the shell function, or import the harness helpers from `tests/` into a scratch
pytest — feed it the inputs you suspect, and print what actually comes back. Then **delete the
probe**; a probe that survives becomes a second, untested harness that drifts from the first.

This is cheap and it repeatedly changes the answer. Probing `_worktree_path` against the selector
grammar took one command and converted a filed defect ("this selector form is rejected", true but
harmless) into the real one ("every *documented* selector form skips the guards entirely, and one
of them silently destroyed a worktree holding an unmerged commit"). An earlier probe in the same
session turned two hypotheses into verified bugs and killed a third that was wrong.

The failure it prevents is designing against an imagined mechanism. A fix aimed at the wrong
mechanism still passes its own tests, because those tests were written from the same wrong model.

## Filing to a public tracker

Before filing an issue, comment, or reply to a **public** tracker, **grep the body against a
forbidden-term list** and fix any hit. At minimum search for **absolute paths, usernames, sibling
project names**, private slugs, internal symbol names, and hostnames.

The bodies are assembled from live diagnostics — terminal listings, error envelopes, file paths —
so leakage is the default outcome, not an unlucky one. The check is mechanical and takes one
command; do it *before* the post, because an edited issue keeps its original text in the edit
history and a deleted comment may already be in a notification email.

## Known interactions (coexisting plugins)

`/h-mad` has **zero runtime dependency** on any other plugin. It does, however, coexist with plugins that install Claude Code hooks. The notable one is **OMC** (`oh-my-claudecode`), whose `persistent-mode.mjs` produces two streams of noise during `/h-mad` runs:

- **Autopilot Stop-hook nag** — emits "Autopilot not complete" on most turns even with no autopilot state on disk (an unconditional nag, not state-driven).
- **Tool-error retry guidance** — `post-tool-use-failure.mjs` records any tool failure to `last-tool-error.json`; `persistent-mode.mjs` then injects `[TOOL ERROR - RETRY REQUIRED]` (escalating to "STOP RETRYING" at retry_count ≥ 5) on the next Stop.

The retry-guidance stream was historically triggered by the audit gate itself: the old gate used a non-zero exit (`awk … exit (c>0)`) as its FAIL signal, which the harness reported as a `PostToolUseFailure`. **This is fixed at the root** — the gate now signals via the `GATE:` token and exits 0 (Audit-gate signal discipline, base invariant), so a legitimate gate-FAIL no longer registers as a tool error. The retry-guidance noise during `/h-mad` is therefore resolved skill-side; OMC's behavior was correct given a real non-zero exit.

Workaround for the **separate** autopilot Stop-hook nag (not addressed by the gate fix): `export DISABLE_OMC=1` (or `OMC_SKIP_HOOKS=persistent-mode`) for the session. Never switch to the OMC autopilot skill mid-`/h-mad`.

## State schema

See `references/state-schema.md`. Validate with:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_validate.py docs/.bkit-memory.json
```

Validation is **two-tier**, because the v2.2 schema was never enforced at write
time and forbade extra properties, so established stores hold many one-off
shapes and a single-tier check always failed:

- `strict` — conforms to v2.2 (`h_mad_state_schema.json`).
- `historical` — conforms to `h_mad_state_schema_historical.json`: the three
  fields every observed record carries, extras allowed.
- `invalid` — neither. Genuinely broken; look at it.

Parse the **token**, not `$?` — same discipline as the audit gate, which
exits 0 on a verdict so a FAIL never registers as a tool failure:

- `STATE: PASS strict=N historical=M invalid=0` → proceed.
- `STATE: FAIL … invalid=K` → the named records are broken.

**Write state through `h_mad_state_write.py`, never by hand-editing the JSON.**
The writer validates the record against the strict schema *before* the bytes
land, replaces the file atomically, and holds an exclusive lock across the
read-modify-write:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature <feature> --set last_completed_phase=5 --set current_phase=6
```

Values are parsed as JSON when possible and kept as strings otherwise, so
`phase=null` writes `null`, `current_phase=5` writes the integer, and
`halt_reason=step5d:red_not_all_failing` stays a string. A rejected write exits
2 and leaves the store byte-identical — an invented key cannot reach disk, which
is what turns "never invent a key" from a rule the orchestrator has to remember
into one it cannot break. Only the record being written is validated; legacy
siblings are left alone, so the writer works on stores with history.

**After writing a record, verify it meets v2.2** — belt and braces, and the way
to check a record written before the writer existed:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_validate.py \
  docs/.bkit-memory.json --feature <feature> --strict-only
```

Never invent a key. If a run needs a field the schema lacks, add it to
`h_mad_state_schema.json` rather than writing it ad hoc — that is exactly how
the store accumulated five spellings of "merge sha".

## Audit prompt assembly

**Substrate preflight (once per H-MAD run — at Phase 5 start, or the first audit dispatch if earlier; skip if the substrate was already recorded this run).** Run `hmad-dispatch env`.
If it exits non-zero → halt `<phase>:no_substrate`. Record the printed substrate +
agent mapping via `scripts/h_mad_telemetry.py` so the run log states which environment
it dispatched under. This is the explicit environment check (cmux vs orca) — do it
before any `send`/`read`. See `references/agent-substrate.md`.

For each audit (Phase 3, 4, 5b), **assemble with the script** — it performs steps 1
through 7.2 below deterministically and refuses to emit a prompt that fails the preflight:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_assemble_audit.py \
  --feature <feature> --phase plan|design|impl-plan --cycle <N> \
  --project-root <PROJECT_ROOT> \
  --report-file "$RP"          # Orca only; omit for the sentinel scrape
```

It prints `ASSEMBLE: PASS <path> <size>` or `ASSEMBLE: HALT <phase>:preflight` with the
reasons, **exiting 0 either way** (a rejected prompt is a verdict, not a tool failure —
see the base invariant on audit-gate signal discipline). A halted prompt is deliberately
not written, so it cannot be dispatched by mistake. A non-zero exit means unreadable
inputs. On `HALT`, fix the template or invariants file and re-run; never hand-patch the
staged prompt.

**Assert `ASSEMBLE: PASS` before dispatching the assembled prompt** — the same mandated
read as the Phase-5 `PREFLIGHT:` assertion, for the same reason: the script exits 0 on
both verdicts, so `$?` cannot tell you which one you got, and an unread token is worth no
more than the unread `STALE` line it is modelled on.

Every defect this area has had came from doing the steps by hand: the rubrics were
inlined twice, `{Design only — cross-doc:}` reached the reviewer in 69 of 69 dispatched
prompts, and a hand-written duplication grep hardcoded a project-authored heading. None
of them raised an error. Use the script.

The steps below are what it implements — read them when debugging a `HALT`, or when
assembling by hand because the script is unavailable:

1. Start from `~/.claude/skills/h-mad/audit-prompt.template.md`, **dropping the leading orchestrator note** — every line from `<!-- ORCHESTRATOR-NOTE:START` through `ORCHESTRATOR-NOTE:END -->` inclusive. That block is assembly instructions to you, not reviewer content; left in, the prompt opens by telling the reviewer it is reading a template.
1.5. **Resolve the `{{ONLY:…}}` applicability markers** for this audit's type (`plan`,
   `design`, or `impl-plan`). A marker is an assembly directive and must never reach the
   reviewer. If the audience list contains this audit's type → delete the marker, keep the
   content. Otherwise → delete the marker **and the content it governs**. Inline form
   (`{{ONLY:design}} <content>`, possibly after a `- ` bullet) governs the rest of that line
   plus any following lines indented deeper than it; block form (marker alone on its line)
   governs down to the matching `{{END-ONLY}}`, both marker lines included.

   **Delete the whole line — never blank the slot and keep its label.** `Paired audited
   plan:` followed by nothing tells the reviewer a document is *missing*, not that it was
   inapplicable, and a design audit reading "the plan wasn't provided" discounts the
   cross-doc check it was supposed to perform.
2. Replace `<INLINE_TARGET_DOC>` with full text of the target doc (plan.md, design.md, or impl-plan.md).
3. Replace `<INLINE_BASE_INVARIANTS>` with full text of `~/.claude/skills/h-mad/invariants.base.md` (workflow-universal Axis B — always inlined, base before project, regardless of whether a project file exists).
4. Replace `<INLINE_PROJECT_INVARIANTS>` with full text of `<PROJECT_ROOT>/.h-mad/invariants.md` (domain Axis B). If the project file is absent/empty, leave the slot empty — the base layer still applies.
5. For design audits only: replace `<INLINE_PAIRED_PLAN>` with audited plan.md.
5.5. For plan and design audits: replace `<INLINE_PAIRED_SPEC>` with full text of `docs/01-plan/features/<feature>.spec.md` — the Axis C source of truth. Without it the reviewer has no AC list to reconcile against and Axis C degrades to prose review, which is the failure it exists to prevent: the paired plan carries only incidental AC references, not the enumeration. For impl-plan audits leave the slot empty; that audit contracts against the design.

   **Prompt size.** Axis C makes an already-large prompt larger, and on a big feature the total can exceed what the reviewer will answer — one measured agent emits normally at 49 KB and returns *nothing* at 53 KB (see `references/agent-substrate.md`). Measured on a real feature: design 45 KB + plan 21 KB + spec 16 KB assembled to 88 KB, and the same prompt without the spec was already 72 KB. Two things follow. First, **do not solve this by trimming the design** — showing the reviewer only its AC-bearing sections is self-defeating, since `absent` becomes undetectable and `absent` is the failure Axis C exists to catch. Inlining the spec's `## Functional Requirements` section alone rather than the whole spec is a legitimate saving (~7 KB) and loses no AC. Second, an over-long prompt is a **safe** failure: `h_mad_extract_report.py` exits 2 on a missing or empty sentinel pair, so the cycle halts instead of scoring silence as a clean gate.

   **Before treating a silent reply as a size failure, read the whole buffer.** `hmad-dispatch read <agent> --from-start`, not a tail — the TUI reflows a reply across redraw frames, and a tail-grep for a sentinel reports SILENT for prompts that answered (measured; see `references/agent-substrate.md`). Most "size failures" are this.

   **If it really is size, "split by FR group" usually will not help.** Only the spec divides; everything else is carried by every split. Measured on a real design audit totalling 50.9 KB:

   | term | size | divides on an FR split? |
   |---|---|---|
   | design | 22.4 KB | no |
   | plan | 10.3 KB | no |
   | audit template | 8.0 KB | no |
   | base + project invariants | 5.5 KB | no |
   | spec (FR-only trim) | 4.7 KB | **yes** |

   46.2 KB of 50.9 KB is fixed, so a two-way split yields ~48.5 KB per half — about 2 KB of relief for two dispatches, two audit files and two gate runs. The remedy silently assumes the *spec* is the marginal term; whenever the design dominates, which is the normal case for a detailed design, it does not work.

   The options that do work, in order:
   1. **Inline only the spec's `## Functional Requirements`** — ~7 KB, loses no AC. Already the default.
   2. **Shorten the design itself** — tighten prose and remove restated plan content. Note the constraint above: do *not* do this by showing the reviewer only AC-bearing sections.
   3. **Split the feature**, not the audit. Fewer FRs per feature shrinks the design, plan *and* spec together — it is the only division that touches the fixed terms.
   4. **Trim the rubric** as a last resort, remembering `invariants.base.md` is inlined into every audit prompt, so a rule added there is paid for by all of them.
6. For impl-plan audits only: replace `<INLINE_PAIRED_DESIGN>` with audited design.md.
6.5. Replace `<AUDIT_SENTINEL>` with `AUDIT-<feature>-<phase>-v<N>` — the per-cycle stem step 9 extracts on. It must be unique per cycle; reusing a previous cycle's stem reopens the stale-scrollback trap it exists to close.
6.6. **Report-file transport (preferred under Orca).** If `hmad-dispatch env` reports `substrate: orca`, replace `<REPORT_FILE_PATH>` with an absolute staged path `RP=/tmp/audit_<feature>_<phase>_cycle<N>.report.md` (and `rm -f "$RP" "$RP.done"` first); the agent will write its report there and mark `$RP.done`. Otherwise (cmux / unpinned) leave `<REPORT_FILE_PATH>` empty and rely on the sentinel scrape. See `references/orchestration-mode.md` §"Report-file transport".
7. Stage: `cat > /tmp/audit_<feature>_<phase>_cycle<N>.txt`.
7.2. **Residual-placeholder preflight — mandatory, before any `send`.** Substitution is a
   literal string replace over the whole file, so it is silent in both failure directions: a
   slot you forgot stays in the prompt as a raw token, and a bracketed slot *mention* in prose
   gets replaced too, splicing a second copy of a rubric into the middle of a sentence. Neither
   raises an error; both reach the reviewer. Check:
   ```bash
   P=/tmp/audit_<feature>_<phase>_cycle<N>.txt
   grep -n '<INLINE_\|<AUDIT_SENTINEL>\|<REPORT_FILE_PATH>' "$P" && \
     echo "HALT <phase>:unfilled_slot" || echo "slots OK"
   grep -n '{{' "$P" && \
     echo "HALT <phase>:unresolved_conditional" || echo "conditionals OK"
   # Duplication check — each rubric must appear exactly once. Derive the needle from
   # each inlined file's own first line: the PROJECT invariants heading is written by
   # the project (HemaSuite's reads "# HPW Project Axis B Invariants"), so a hardcoded
   # heading reports a false 0 in every repo but the one it was written against.
   # Do NOT anchor to '^': a stray copy spliced into a blockquote is prefixed '> # …',
   # so an anchored grep reports a clean 1 while the prompt carries 2.
   BASE_MD=~/.claude/skills/h-mad/invariants.base.md
   PROJ_MD=<PROJECT_ROOT>/.h-mad/invariants.md
   grep -Fc "$(head -1 "$BASE_MD")" "$P"                          # must be 1
   [ -s "$PROJ_MD" ] && grep -Fc "$(head -1 "$PROJ_MD")" "$P"     # must be 1 when a project file exists
   ```
   Any hit on either grep, or a count > 1 on either rubric → halt (`<phase>:unfilled_slot` /
   `<phase>:unresolved_conditional`),
   fix the template/invariants file, re-assemble. Do **not** dispatch a prompt that still shows
   a raw `<INLINE_…>`: the reviewer reads it as an unfilled template and silently discounts the
   axis it belongs to, which scores as a clean gate on a rubric that was never delivered.

   This is a live failure, not a hypothetical: `<INLINE_BASE_INVARIANTS>` and
   `<INLINE_PROJECT_INVARIANTS>` were once written **bracketed** inside the template's own
   header blockquote and inside `invariants.base.md`'s header, so every assembled prompt carried
   both rubrics twice (measured: 2 copies of each in every `/tmp/audit_*.txt` on this machine —
   ~4–6 KB of dead bloat against the ~49–53 KB reviewer cliff in step 5.5) and still displayed a
   raw `<INLINE_BASE_INVARIANTS>` token. **Prose refers to a slot by bare name
   (`INLINE_BASE_INVARIANTS`); only a real slot is bracketed.** Keep it that way in any new
   template or invariants file.
7.5. **On cycle 1 of each audit phase (and after confirming agy is alive via `hmad-dispatch alive agy`), clear agy's context** (see §"Agent-pane context hygiene") so a prior feature's/phase's transcript can't drift the verdict or pollute the scrollback you later grep. Later cycles of the SAME audit reuse the warm context (the running revision thread is wanted).
8. Dispatch:
   ```bash
   hmad-dispatch send agy /tmp/audit_<feature>_<phase>_cycle<N>.txt
   ```
   `send` chooses its own delivery mode by size: it inlines below
   `HMAD_SEND_INLINE_MAX` (default 8192 bytes) and otherwise tells the agent to
   read the staged file by absolute path. Audit prompts run 32–61 KB, so they
   take the indirection path — no need to hand-roll it.
9. Capture the report. **Under Orca (report-file transport), skip the scrape entirely** — the agent wrote a clean file, so read it directly and jump to the gate:
   ```bash
   hmad-dispatch report-wait "$RP" --timeout 600 \
     > docs/01-plan/features/<feature>.<phase>.audit.v<N>.md
   ```
   This has no sentinel-extraction step (the file is already the report), no `wait`, and no dedent/`•`-normalize (the file is clean markdown, not a TUI render). On timeout, the agent did not honour the contract — fall back to the scrape path below.

   **Scrape fallback (cmux / unpinned, or when `report-wait` times out) — never hand a raw scrape to the gate.** The scrape holds live scrollback, so the previous cycle's report is usually still above the prompt; extracting on the first `## Summary` scores the wrong cycle:
   ```bash
   hmad-dispatch read agy --lines 200 > /tmp/scrape_<feature>_<phase>_cycle<N>.txt
   python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_report.py \
     /tmp/scrape_<feature>_<phase>_cycle<N>.txt \
     --feature <feature> --phase <phase> --cycle <N> \
     > docs/01-plan/features/<feature>.<phase>.audit.v<N>.md
   ```
   The extractor takes the **last** complete `<AUDIT_SENTINEL>-BEGIN`/`-END` pair, so neither an older cycle nor a retry within this one can win. It exits 2 and writes nothing when the pair is missing or its body is empty — that is the "dispatched, went idle, produced nothing" case, and it must halt the cycle rather than be scored. On exit 2: re-read with a larger `--lines`, and if the report genuinely never arrived, `hmad-dispatch clear agy` and re-dispatch.
10. Design audits write to `docs/02-design/features/` instead; adjust the redirect above.
11. Run the gate — the verdict unit counts bullets in BOTH `## Must-fix` AND `## Should-fix` (excluding the bare-`None` sentinel, a stray `- None`, and any `## Acknowledged-not-fixed` items in the same file or a sidecar `.audit.v<N+1>.md` passed via `--ack-file`):
    ```bash
    python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py <audit-file>
    ```
    The gate **prints a verdict token and always exits 0** on a verdict (a non-zero exit is reserved for operational errors such as a missing file — never for a FAIL, so the gate never registers as a tool failure). Parse the **token**, not `$?`:
    - `GATE: PASS must=0 should=0` → gate passes (must-fix=0 AND should-fix=0). Proceed.
    - `GATE: FAIL must=N should=M` (N or M > 0) → gate fails. Surface the bullets, revise, re-audit.
    The gate emits a `[H-MAD] <feature> gate <verdict>` marker line. Nits never block. If the `GATE:` token is absent from stdout (unexpected), treat it as an operational error and halt `step<N>:gate_token_missing` with a `[H-MAD]` marker — never silently treat a missing token as PASS.

## Putting `hmad-dispatch` on PATH

This file spells the wrapper as a bare `hmad-dispatch <verb>`. Put the skill's
`bin/` on PATH once so those commands work verbatim instead of needing the
absolute path to `scripts/hmad-dispatch.sh` (which differs per install and per
checkout):

```bash
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
```

## Helper scripts (all in `~/.claude/skills/h-mad/scripts/`)

- `h_mad_extract_verdict.py` — read the last `STATUS:`/`VERDICT:`/`ASSESSMENT:` line off a scrape, validated against its contract; exit 2 (printing nothing) when absent, empty, or off-contract, so silence can never read as approval
- `h_mad_extract_report.py` — pull the reviewer's report out of a pane scrape on the last `AUDIT-<feature>-<phase>-v<N>-BEGIN`/`-END` pair; exit 2 (writing nothing) when the pair is missing or empty
- `h_mad_audit_gate.py` — audit-gate verdict unit (single source of truth): `classify()` + CLI printing `GATE: PASS|FAIL` + `[H-MAD]` marker, exit 0 on verdict / 2 on operational error; `--must-only` for the `/h-mad do` precondition. Imported by `h_mad_do_preconditions.py`.
- `h_mad_resume_decision.py` — smart-resume decision
- `h_mad_do_preconditions.py` — `/h-mad do` prereq verifier (uses `h_mad_audit_gate.classify`)
- `h_mad_derive_test_path.sh` — production-path → test-path mapper
- `h_mad_emit_marker.sh` — `[H-MAD]` marker writer
- `h_mad_state_schema.json` — jsonschema for `orchestrator_state` (v2.2, strict tier)
- `h_mad_state_schema_historical.json` — permissive tier for pre-v2.2 records
- `h_mad_phase7_preconditions.py` — Phase 7 gate: `check()` + CLI printing `PHASE7: READY|BLOCKED`, exit 0 on verdict / 2 on operational error. Enforces 6-before-7 by reading state and the gap analysis.
- `h_mad_state_staleness.py` — compares state against git and reports disagreement (`STALENESS: CLEAN|SUSPECT`); catches a record that is well-formed and no longer true.
- `h_mad_state_write.py` — the orchestrator_state write path: `create_feature()` / `set_fields()` + CLI printing `STATE-WRITE: OK`, exit 0 on success / 2 on refusal. Validates the record against the strict schema before writing, replaces the file atomically, and serialises concurrent writers on a lock sidecar. Use this instead of hand-editing state.
- `h_mad_state_validate.py` — two-tier state validator: `classify()` + CLI printing `STATE: PASS|FAIL` + `[H-MAD]` marker, exit 0 on verdict / 2 on operational error; `--strict-only` enforces v2.2 on a record you just wrote
- `h_mad_telemetry.py` — Phase 7 cycle count recorder + summary
- `h_mad_issue_fix_gate.py` — file-issue-then-fix-under-TDD linkage gate: printing `ISSUEFIX: PASS|FAIL issue=N …`, exit 0 on verdict / 2 on operational error. Checks that issue N is tied to a test file that names it AND to a `Closes|Fixes|Resolves #N` trailer. `--suggest` prints the `gh` commands for the operator; the gate never invokes `gh` (§"No new external dependency").

### file-issue-then-fix-under-TDD

The loop, when a measurement turns into a defect:

1. **File the issue with the measurement in it** — the number, the command that produced it, the expected value. An issue that says "X is broken" without the observation cannot be verified closed. Sanitize first (§"Filing to a public tracker").
2. **One test file per issue**, and the file **names the issue** (`# pins #42`). This is the link that survives; six weeks on, a test whose motivation lives only in the author's head reads as arbitrary and gets deleted.
3. **RED before GREEN.** Confirm the new test fails against the unfixed code — a test that passes against the code it was written to catch is decoration.
4. **Fix, then close via the trailer** — `Closes #42` in the commit body.
5. **Gate the linkage**: `h_mad_issue_fix_gate.py --issue 42 --test <path>`. It catches the two failures that actually happen — a fix with no test naming the issue, and a test with no trailer closing it.

Steps 1–4 are the discipline; step 5 is the only part a script can check, which is why the script checks that and nothing else.

## Telemetry

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_telemetry.py record \
  --feature <feature> \
  --state docs/.bkit-memory.json \
  --out .h-mad/telemetry.jsonl
```

Non-fatal: if record fails, emit warning and continue to report.

**The cycle counts are derived from the artifacts on disk, not read from orchestrator state.**
`audit_cycles` is `max(N)` over each phase's `<feature>.<phase>.audit.v<N>.md` files, and
`iterate_cycles` is `max(N) - 1` over `<feature>.analysis.v<N>.md` — both via
`scripts/h_mad_cycle_counts.py`, searching the live `docs/` feature directories and
`docs/archive/*/<feature>/`. The `audit_cycles` and `iterate_cycles` fields still exist in the
state schema; they are simply no longer what telemetry reports. Nothing increments them, which is
why they read `0/0/0` on every feature before this changed, and why both drift warnings below
were unreachable.

`--docs-root PATH` (optional, on both subcommands) sets the tree that is searched. **Default**:
the parent of the `--state` file when that parent is named `docs`, else `docs/` relative to the
current directory — so the invocation above needs no change.

Ad-hoc summary: `python3 ~/.claude/skills/h-mad/scripts/h_mad_telemetry.py summary`

`summary` recomputes both counts from disk as it prints, so features recorded before this change
report their real numbers without `.h-mad/telemetry.jsonl` — an append-only log — being rewritten.
A feature whose artifacts are absent falls back to its stored row values, so a deleted or
never-archived docs tree cannot silently zero a real recorded number. The `audit_cycles > 3` and
`iterate_cycles > 3` drift warnings are computed from the displayed values.

## References

- `references/inline-protocols.md` — **Inline protocols for all phases (standalone, no external skills)**
- `references/phase-table.md` — full phase gate table
- `references/failure-recovery.md` — halt routes + recovery hints
- `references/state-schema.md` — state schema details
- `references/agent-substrate.md` — Agent dispatch substrate (cmux | orca) — hmad-dispatch verbs, detection, identity pins, pane launch
- `references/orchestration-mode.md` — Orca structured orchestration and Phase-5 worktree fanout protocol
- `references/codex-implementer-prompt.md` — Phase 5d/5e Codex dispatch template
- `references/agy-spec-reviewer-prompt.md` — Phase 5e-review agy dispatch template
- `references/agy-architectural-reviewer-prompt.md` — Phase 6a-prime agy dispatch template
