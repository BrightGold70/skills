# h-mad reference — Phase 5 implementation sub-steps (5a–5f)

_Moved verbatim from `h-mad/SKILL.md` (row 2910); SKILL.md keeps a pointer stub under the same heading. Edit the text here. Everything below the marker line is the section body exactly as it stood in SKILL.md._

## Phase 5 (Implementation) sub-steps

<!-- h-mad split body: SKILL.md §"Phase 5 (Implementation) sub-steps" -->

**Substrate preflight (Phase 5 + first audit dispatch).** Run `hmad-dispatch env`.
If it exits non-zero → halt `<phase>:no_substrate`. Record the printed substrate +
agent mapping into state so the run log states which environment it dispatched under:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature "<feature>" \
  --set substrate='{"name":"orca","agents":{"codex":"term_…","agy":"term_…"}}'
```

State is the carrier and `h_mad_telemetry.py record` is the reporter — it copies the
field onto the Phase-7 row it already builds from this record. Writing it here is what
makes the step executable at Phase-5 time; `record` is a close-out call and cannot
serve a Phase-5-start instruction. This is the explicit environment check (cmux vs orca) — do it
before any `send`/`read`. See `references/agent-substrate.md`.

**Dispatch enforcement.** `env` ends with a canonical `PREFLIGHT:` line and writes a
receipt when the verdict is `PASS`:

```text
PREFLIGHT: PASS
PREFLIGHT: FAIL stale=codex
PREFLIGHT: FAIL conflict=term_x
PREFLIGHT: FAIL unresolved=codex,agy
PREFLIGHT: FAIL stale=codex,agy conflict=term_x
```

`unresolved=` fires only when a coordinator resolves — i.e. the session is wired
for orchestration and is one step from dispatching, with nowhere to dispatch to.
An un-set-up session (no coordinator) keeps `PASS` with agents unresolved, since
nothing is about to dispatch there.

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
never matches Codex on title — only on a fresh pane's `gpt-N` banner, which scrolls out of
the PREVIEW once it works — the tail-evidence pass recovers it from retained scrollback.

**Identity does exist — in a different call (J16, shipped 2026-07-23).** `orca worktree ps`
returns `agents[].agentType` keyed by a `paneKey` of `<tabId>:<leafId>`, and `terminal
list` returns `.tabId`/`.leafId`. `_orca_find` joins them as **Pass 0**, ahead of the
title, preview and tail-evidence passes, which resolves the case above exactly: measured live with pins
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

**A missing report is neither pass nor fail.** This paragraph is the **pane-path** rule;
for the `exec` path there is no pane to read, so see §"A missing report on the `exec`
path" instead. If `report-wait` times out, read the
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
create`, resolves the pane's live handle by joining the create response's `paneKey` against `terminal list`, and pins that —
no title/preview dependence, no manual pin (H5). Use `launch` when h-mad owns the
agent; `pin`/`pin-agents` when adopting an existing pane.

- **5a** — arm hook, then **dispatch the `implplan-author` teammate** (§"Teammate authors"); the inline impl-plan protocol (`references/inline-protocols.md §Phase 5`) is its contract. Write `orchestrator_state.<feature>.phase = "step5"` + `autonomous_entry_ts = <now>`. Output: `docs/01-plan/features/<feature>.impl-plan.md`.
- **5b** — auto-audit impl-plan (same audit-prompt mechanism as Phases 3/4 — see §"Audit prompt assembly"; §"Never gate on one audit pass" chooses the two surfaces). Write each surface's audit to `docs/01-plan/features/<feature>.impl-plan.audit.v<N>[.<surface>].md`. Run awk gate on the union. If must-fix > 0 OR should-fix > 0, **re-dispatch `implplan-author` with both the must-fix AND should-fix bullets** (§"Teammate authors" — you relay findings, you do not regenerate the document yourself); cycle until **build-class must-fix = 0 on BOTH surfaces at one commit and every remaining finding is fixed or acknowledged** (§"Finding class — build vs measurement"). Build-class findings drive the loop up to the cap of TWO gating rounds (§"Document-audit round cap — Phase 5 is the gate"), after which an open build-class must is carried as an `OPEN-DECISION` on its Task and settled in 5d; measurement-class findings never hold the phase past the round in which build-class reached 0. Operator escape at any cycle: author `.impl-plan.audit.v<N+1>.md` with `## Acknowledged-not-fixed` listing deferred should-fix and measurement-class items, each with its re-run command, commit `[audit-override]`, gate treats those as cleared; a `class: build` bullet is refused (`ack_refused=N`). **Tag each ack bullet with a `[key]`** — `- [ac-1.4 teardown-leak] <text>` — and it keeps matching however the next cycle's reviewer re-words the finding; without one, the match survives re-formatting (emphasis, backticks, wrapping, case) but not a genuine re-wording, and you pay a cycle re-acknowledging it. **There is deliberately no fuzzy matching** (§"Why the ack match is not fuzzy").

  **Then run the wire-pin gate — 5b is the last gate that can require it.** `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/<feature>.impl-plan.md --feature <feature>`. Read the `WIREPIN:` token, never `$?` (`UNSHAPED` exits 2 because it is a cannot-judge, not a verdict). On `WIREPIN: PASS`, 5b automatically registers each passing `wiring` task in `.h-mad/wires.jsonl`; without `--feature`, registration is skipped. `UNREADABLE` → halt `step5b:impl_plan_unreadable`: the gate could not read the file at all, so nothing was parsed — this token carries **no `tasks=`/`wiring=` counts** precisely so it cannot be mistaken for a verdict or routed by a count that was never measured; the stderr `ERROR:` names the path, which is almost always wrong rather than the plan. `UNSHAPED` → **read the `tasks=` count before choosing a remedy**: `tasks=N` with N>0 → halt `step5b:impl_plan_unshaped`, the plan declares no `Task shape` at all, so a wiring task in it is indistinguishable from new behaviour — return to 5a and **re-dispatch `implplan-author`** against the current template (§"Teammate authors"; this is a revision like any other, and regenerating it in your own context is the loop that cost 34 cycles); `tasks=0` → halt `step5b:impl_plan_no_tasks`, the parser saw no task header, so nothing is missing a field — you are almost certainly pointed at a legacy `.plan.md` or the design doc rather than the `.impl-plan.md`. `FAIL` has two causes and two different remedies, so **read the detail lines, not just the verdict**: an `unpinned:` line → halt `step5b:wire_pin_missing:<task>` and return to 5a to name the `WIRE`/`WIRE-PIN`; a `mislabeled:` line → halt `step5b:wire_pin_shape_mislabel:<task>` — the fields are already filled in, so nothing is missing to add and the missing-pin remedy would read as already satisfied. An `unlabeled:` line, on any verdict, names a Task whose `**Production file**`/`**Test file**` path is absent or unfilled — fix it in 5a before 5d, whose TDD judge resolves writes from those labels (`none` is a declaration, not a gap). After 5b nothing downstream can tell a wired build from an unwired one, which is why the obligation is mechanical here and advisory nowhere.

  A shape is a self-declaration, and closing only the *absent* case leaves the plan one edited word from a PASS: demote a pinned `wiring` task to `refactor` and `wiring` drops to 0 with `unpinned=0`. The gate therefore trusts the filled-in `WIRE`/`WIRE-PIN` over the shape word — a task carrying either under a non-`wiring` shape contradicts the template, which declares both fields `wiring` shape only. Unfilled template lines and placeholders still count as declaring nothing, or the guard would refuse every plan the template generates.
  This is the 5b auto-register step: every passing `wiring` task is written to `.h-mad/wires.jsonl`. A task whose pin is not a pytest test declares `**WIRE-RUNNER**: playwright`, which is written into the record as `runner`. Registration skips the task loudly, rather than guessing, in these cases: an unknown value; a numbered or conflicting `WIRE-RUNNER` (one runner per task); or a pin that does not name a non-`.py` file as `<file>::<test>`.
- **5c** — baseline branch: `git checkout -b feature/NNN-<slug>`; commit impl-plan + audit files.
- **5d** — RED dispatch (see `references/codex-implementer-prompt.md`). **Stage it with `h_mad_assemble_tdd.py --phase red` rather than by hand** — it cuts §"Task N" from the impl-plan, fills the template, and prints the exact command block with the model, the scoped test path and the probed interpreter already baked in; hand-assembly produced five distinct invocation mistakes across two sessions, every one a default. It refuses a 5d without the stated counts, which is the one judgement here that must stay yours. **Before the feature's first RED dispatch, run `python3 ~/.claude/skills/h-mad/scripts/h_mad_prescribed_block_guards.py docs/01-plan/features/<feature>.impl-plan.md --repo-root <project-root>` and read its `PRESCRIBED-BLOCKS:` token**: it appends each python block the impl-plan prescribes for an existing test module to a scratch copy and runs that module's self-source guards against it. `FAIL` means the RED would come back over its stated count, one failure per distinct guard named, for a reason the plan wrote, so re-dispatch `implplan-author` with each `COLLISION:` line, unless the guard shows the block replaces code instead of adding it (a count guard over-reports there). `INCOMPLETE` checked less than it says; name what did not run. Guards the plan itself adds do not exist yet and are not checked. pin-agents-tail-banner passed 53 audit cycles carrying such a block. **Transport: default `hmad-dispatch exec codex` for a one-shot RED** — hard exit code, no scrape, monitor via `--log` (§"Exit-code dispatch for 5d/5e"); use the pane path (`send`) only for an iterative revision loop. The pane-path steps in the rest of this bullet (alive-check, context clear) apply only when you use `send`; `exec` is a fresh subprocess and needs neither. For the pane path: verify codex + agy are alive by **reading `hmad-dispatch env` and requiring `PREFLIGHT: PASS`** — do not chain `alive codex && alive agy`, which branches on `$?` and is the exact habit §"Audit-gate signal discipline" forbids (`env` deliberately returns 0 even on `PREFLIGHT: FAIL`, so a `&&` chain reads a failure as success). Refuse on anything but `PASS` → halt `step5d:no_<agent>_pane`. **Immediately after confirming each pane is alive, clear its context** (see §"Agent-pane context hygiene") so no prior-feature/prior-cycle conversation bleeds into this feature's TDD. For each module, dispatch Codex for tests; dispatch agy for coverage review. **In the dispatch, state the expected failing/passing counts for the task and label any regression guards** — tests asserting behaviour that already works, which must pass from the first run. Read each `STATUS:` with `h_mad_extract_verdict.py` (§"Reading a dispatch verdict"); no extractable verdict after a re-read and re-dispatch → halt `step5d:no_verdict:<module>`. Then verify the results **match the stated counts**; halt `step5d:red_not_all_failing` when an unlabelled test passes without implementation.

  Not every RED task is all-new behaviour. A refactor-shaped task legitimately lands with most of its tests green, and a blanket "every test must FAIL" halts a correct RED — worse, the cheapest way for an implementer to satisfy it is to weaken an assertion or assert the current buggy value, manufacturing a failure that then "passes" in 5e without anything being fixed. Stating the counts up front makes the check discriminating in both directions: an unexpected pass still halts, and an expected one does not.

  **The third task shape is `wiring`, and counts cannot gate it.** When the deliverable is a connection rather than new behaviour, carry the task's `WIRE:` and `WIRE-PIN:` lines from the impl-plan into the dispatch, and require the RED report to give the **failure mode per test, not only the count**. A test whose RED is an `ImportError`/`AttributeError`/`NameError` — the callee missing — is not a wire test: it fails for the callee's absence and goes green the moment the callee exists, wired or not. The `WIRE-PIN` test's RED must be an assertion about the **caller's** observable behaviour (the call was not made; the value did not propagate). The traceback already carries this, so the check costs nothing. A `WIRE-PIN` whose RED reason is a missing symbol → halt `step5d:red_wrong_reason:<module>`. A missing-symbol RED on the pin is valid **only** when the missing symbol is the caller the task creates, and the callee resolves at the RED base. The RED report must name both. GREEN must prove the wire by a wire-cut: delete the call only, keep the caller and the callee, and confirm the pin fails. A `wiring` task dispatched with no `WIRE-PIN` at all → halt `step5d:no_wire_pin:<module>`; do not let 5e establish GREEN for it, because nothing downstream can see the wire (`invariants.base.md` §"Connection enforcement").
- **5e** — GREEN dispatch (`references/codex-implementer-prompt.md` + `references/agy-spec-reviewer-prompt.md`). **Stage the Codex half with `h_mad_assemble_tdd.py --phase green`** (the agy spec-review half is still assembled by hand). Pass `--mutation-spec <h-mad/tests/mutation-specs/<module>.json>` so GREEN appends one mutation row per guard it writes and runs `--check-anchors` on it (the only harness mode the Codex Phase-5 gate admits); without the flag GREEN lists the rows in its final message. GREEN proposes rows and the orchestrator still runs the harness and scores them. Note the sandbox rule it enforces for you: never dispatch a pytest-running phase with `--sandbox read-only` — it kills pytest's tempdir, so the run passes without measuring anything. The same applies to the anti-gaming verifier dispatch below, which the assembler does not yet stage. **Transport: default `hmad-dispatch exec` for a one-shot GREEN + its review** (§"Exit-code dispatch for 5d/5e"); use the pane path (`send`) for the iterative revision loop where cycles 2..N reuse the warm thread — there the alive-check + context-clear below apply. For the pane path: re-verify the Codex + agy panes alive and **clear each pane's context** (§"Agent-pane context hygiene") before the first GREEN dispatch of a feature. For each module, dispatch Codex for implementation; dispatch agy for spec-compliance review. Read both verdicts with `h_mad_extract_verdict.py` (§"Reading a dispatch verdict") — never by grepping the scrape for the halt value, which turns an agent's silence into a pass. If agy returns `VERDICT: DRIFT` → halt `step5e-review:spec_drift:<module>`. If no verdict can be extracted after a re-read and re-dispatch → halt `step5e:no_verdict:<module>`. On 3rd consecutive GREEN failure → halt `step5e:green_unreachable:<module>`. **After GREEN + spec-review, run the independent anti-gaming verification** (`references/codex-verifier-prompt.md`): module count → test-discrimination audit → quote the source line for each pinned property → full suite vs the reference, and cross-check every reported count a second way. Codex GREEN says the code was written; agy says it matches the spec; this pass answers "are the tests real and does the source hold the pinned properties" — the axis a green suite and a `STATUS: DONE` cannot self-certify (an agent can emit `DONE` over a fabricated count). A false property or a suite failure → halt `step5e:verify_failed:<module>`.
  **When the agy spec review finds behaviour the design states but no test pins**, the route is test-first, the same as any new behaviour: amend RED first — re-dispatch 5d for that Task with a failing pin test for the unpinned behaviour, confirm it fails for the stated reason — then re-dispatch GREEN to make it pass. Never fix it in GREEN without a failing pin: once the Task's mapped tests all pass the TDD judge DENYs the write as `test-passing`, and a fix landed with no pin is exactly the unguarded behaviour the review just found.

  **GREEN is established by the revert test, not by "tests pass".** For the module: revert production only (tests untouched) → confirm the RED split returns EXACTLY (the same tests fail) → restore production → confirm green returns. **Verify restoration by executing the symbol** (import it / run the test), **never by grepping the source** — a field-reorder or same-mtime-second `cp` leaves stale `.pyc` bytecode running while the source reads restored. Reading a diff cannot establish this. Only then run the anti-gaming verify.

  **Use this exact sequence to revert and restore.** The production code at this point is *uncommitted*, so a careless revert destroys it permanently: `git restore` / `git checkout --` **deletes** the new implementation with no way back. Stash is the safe direction, but only in the `-u` form — `git stash push -- <paths>` **refuses an untracked path**, and `git add -N` does not rescue it but breaks it (see the measured table below):

  ```bash
  before=$(git rev-parse -q --verify refs/stash || true)
  git stash push -u -- <production-paths>   # the revert; -u is what reaches an untracked file
  mine=$(git rev-parse -q --verify refs/stash || true)
  if [ "$mine" = "$before" ]; then mine=""; echo "NOTHING WAS STASHED — the target is unchanged; do not pop"; fi
  [ ! -e <one-production-path> ] || echo "REVERT DID NOT LAND — do not trust this run"
  # ... run the module tests here; the RED split must return EXACTLY ...
  if [ -n "$mine" ]; then                   # restore ONLY the stash this step created
    ref=$(git stash list --format='%gd %H' | while read -r name sha; do [ "$sha" = "$mine" ] && { echo "$name"; break; }; done)
    if [ -n "$ref" ]; then git stash pop "$ref"; else echo "STASH $mine IS GONE — restore by hand: git stash apply $mine"; fi
  fi
  ```

  **Never pop a stash this step did not create.** When the target is unchanged, `git stash push` stashes nothing ("No local changes to save", and rtk still prints `ok stashed`), and an unconditional `pop` applies whatever sat on top. Measured: a foreign `resolved-model` stash left `UU handoff/SKILL.md`. Pop **by the stash commit this step made**, never `stash@{0}`. `refs/stash` is shared by every worktree of the repo, so another lane's push during the test window takes the top slot. A count delta cannot tell whose entry it is.

  **Assert the revert landed with an EXISTENCE check, never `git diff --quiet`.** For an untracked file `git diff --quiet` is trivially clean — measured: it reported CLEAN with the file sitting in the worktree, i.e. a *false* "revert landed" — so it is exactly the readback that cannot see this failure. A revert that never happened reports as a pass, the same class of silent no-op the mutation harness refuses an unlanded anchor for.

  **Measured on git 2.50.1 (Apple Git-155), scratch repo, one untracked `new.py`:**

  | sequence | rc | stashed | file removed |
  |---|---|---|---|
  | `git stash push -- new.py` | **1** — `error: pathspec … did not match any file(s) known to git` | 0 | no |
  | `git add -N` then `git stash push -- new.py` | **1** — `error: Entry 'new.py' not uptodate. Cannot merge.` | 0 | no |
  | `git add -N` then `git stash push -u -- new.py` | **1** — same `not uptodate` error | 0 | no |
  | **`git stash push -u -- new.py`** | **0** | 1 | **yes** (`stash pop` restores it) |

  Two corrections this table makes to what this section said before, both worth stating because the wrong version was reasoned from for weeks. First, plain `stash push` on an untracked path is **not** a silent no-op exiting 0 — it is a loud rc=1 pathspec refusal. The hazard `git add -N` was introduced to close therefore did not exist in this form. Second, `add -N` is the thing that *breaks* the stash, and `-u` does **not** rescue an `add -N`'d file: the fix is to drop `add -N`, not to add a flag beside it. A reader who keeps `add -N` and appends `-u` gets rc=1 exactly as before.

  **For a `wiring` task the whole-module revert is not sufficient — run the wire-scoped revert too.** Revert the **connection only** (the call site / import / registration / propagated argument), leaving the callee *and* the tests intact, and confirm the `WIRE-PIN` test fails. Module suite still green → halt `step5e:wire_unenforced:<module>`. The whole-module revert removes both sides, so its RED split returns identically whether or not the wire exists; it is structurally incapable of establishing the one decision a wiring task ships. **Assert the revert landed before trusting the run** — use `git stash push -u -- <paths>` (the sequence above; `-u` is what reaches an untracked file, and `git add -N` breaks it rather than enabling it) and read the result back with an **existence** check, since `git diff --quiet` is trivially clean for an untracked path and cannot see this failure. A revert that never happened reports as a pass. Then mutate the other direction: force the connection to fire unconditionally and confirm the fall-through/negative test fails. See `invariants.base.md` §"Connection enforcement". **Record authors before review:** when the orchestrator accepts a module's GREEN dispatch (reads `STATUS: DONE` or `STATUS: DONE_WITH_CONCERNS` and stops re-dispatching GREEN), run `h_mad_state_write.py docs/.bkit-memory.json --feature <feature> --session-id <owner-session-id> --append implementation_authors='{"module":"<module>","agent":"<agent>"}'` before the module's 5e spec-review leg runs. Use the accepted dispatch's resolved `TDD-IMPLEMENTER:` agent, passed as `--agent` when staging (or `claude` for the in-session fallback), as described in item 7. Every accepted fix dispatch after a 5e review or verification finding appends the same author entry before the next leg that reviews the fixed code. Encode actual values as JSON and shell-quote the complete argument. An unaccepted dispatch appends nothing; a refused append must be corrected and retried before review. An accepted GREEN's entry remains if a later verification step halts.
- **5f** — **Derive the 5c sha, never `git merge-base`.** `python3 ~/.claude/skills/h-mad/scripts/h_mad_baseline_sha.py --branch <feature-branch> [--trunk main]`, reading the `BASELINE:` token, never `$?`. 5c is `git checkout -b …; commit impl-plan + audit files`, so the 5c commit is the branch's FIRST commit and `git merge-base main <branch>` returns the commit it forked FROM — off by exactly the impl-plan commit, and off plausibly, since both are real shas on the right branch. Measured (J41): merge-base `b5c8f41` against real 5c `730cc16`, 313 lines apart — the impl-plan and its three audits, which the wrong base feeds into the review as newly-added content when they are a separate INPUT to it. `UNVERIFIED` is a verdict, not an error: the branch's first commit does not touch an impl-plan, so something was committed before 5c and the rule does not hold — find the commit by hand, and note the token reports it as `candidate=` rather than `sha=` precisely so an unvouched value cannot be scraped as the answer. Only `OK` carries `sha=`. Then, from the repository root, re-verify the registry with `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_registry.py verify --base <5c sha> --rootdir <repository-root> --testpath <project-test-root>` (for this repository, `h-mad/tests` is an example), then run `python3 ~/.claude/skills/h-mad/scripts/h_mad_wire_registry.py challenge --base <5c sha>`. `--rootdir` is the repository root (pytest's cwd), while `--testpath <project-test-root>` must name a collectable test root whose node ids are repo-relative; use both to avoid collecting this repository root's pre-existing sibling-project import mismatches (when a nested sub-project carries its own `pytest.ini` or `pyproject.toml` so pytest roots collection at the sub-project and emits sub-project-relative node ids such as `tests/test_foo.py::test_bar`, `run_pins` qualifies unambiguous sub-project node ids under `--rootdir` automatically, or pass `--rootdir <sub-project-root> --repo <repository-root> --testpath <sub-project-test-root>`). The challenge is **warning-only and verdict-neutral**: an unproven heuristic never blocks an operator. The verifier's halt reasons are `step5f:wire_regression:<feature>::<id>`, `step5f:wire_pin_missing:<feature>::<id>`, `step5f:wire_pin_ambiguous:<feature>::<id>`, `step5f:registry_untracked`, `step5f:undeclared_removal:<feature>::<id>`, and `step5f:unverified_rename:<feature>::<id>`; each is emitted with `[H-MAD]`. **`unverifiable=N` is cannot-judge, not a pass.** A record whose `runner` has no resolver here, such as a Playwright pin (only pytest is resolved), is never collected, so it would read `missing` by construction. It is counted as `unverifiable=N` on the token and named `[H-MAD] step5f:wire_pin_unverifiable:<feature>::<id> runner=<runner>`, and it is **not** a halt reason. A `PASS` carrying `unverifiable>0` says only that the judged records held: read the count, and prove each named wire another way (its wire-scoped revert at 5e). **A `pin` may be a single test or a LIST of them**, because one wiring task can wire N call sites and one pin per record could only ever prove site 1 — the rest were left to ACs and the wire-scoped revert, which the registry cannot see. A record resolves only when EVERY pin resolves to exactly one node id, and is verified only when EVERY pin passes: a partial pass would report a wire as proven while a site it names went unchecked. Ambiguity outranks absence, since a pin naming more than one test must be qualified before the record can be judged at all. **On a multi-pin record the halt reason gains a `#<pin>` suffix** — `step5f:wire_pin_missing:<feature>::<id>#<pin>` — and one line is emitted per offending pin; a single-pin record's reason is unchanged. Without the suffix two broken sites on one record emit the same line twice and name neither, which is J43's defect one level down. `register --pin` is repeatable, and stores a bare string when given exactly once, so every record written before the list form reads back unchanged. **The registry's identity is `(owning_feature, id)`, never `id` alone** — `id` is the impl-plan task number and every impl-plan numbers its tasks from 1, so a bare id names no single wire once two features have run. Keyed on the bare id, registration silently upserted one feature's wire over another's and the comparison, keyed the same way, saw the successor and reported nothing — performing exactly the removal the `status`/`removal_provenance`/`removed_by_feature` tombstone fields exist to force an author to declare. Measured before the fix: 1 of the 7 records ever registered in this repository had already been lost that way, and it was unrestorable, because re-registering it evicted the successor (J43). Then run the full test suite: `pytest <project>/tests/ -v --tb=short`. All must pass (100%). Any failure → halt.
- **5g** — `git add -A -- ':/' ':(top,exclude)*.done' && git add -u -- ':/' && git commit -m "feat(<feature>): implement <module>"` per module. **The pathspec is load-bearing, and both halves are.** The audit `.done` markers are untracked and NOT gitignored, so a bare `git add -A` commits every one of them — 88 in this repository at the time of writing, and "do not commit the markers" has ridden every handoff as a manual warning instead. Gitignoring them is the wrong fix in the other direction: `hmad-dispatch` COUNTS them (`^?? .*\.done$`) to exclude them from its `tree delta`, so an ignore would blind a measurement that currently works. `':/'` anchors the sweep at the repository root and `':(top,exclude)*.done'` anchors the exclusion there too — a CWD-relative pair silently stages only the subtree you happen to stand in, and excludes only that subtree's markers (measured: from a subdirectory, 1 of 3 changed files staged and a root marker committed). The second `git add -u` then stages any TRACKED `.done` file's real modification, which the exclusion alone would suppress forever. Write `phase = null` (disarms TDD gate hook). Emit `[H-MAD] <feature> phase5 complete`.

### Codex authors Phase 5 — enforced, not just instructed

  **Run the mutations through `h_mad_mutation_harness.py` rather than by hand.** `python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py <spec.json>`, where the spec names the suite command and each mutation as an exact `find`/`replace`. Read the `MUTATION:` token, never `$?`. The harness exists because the hard part of this pass is not choosing mutations, it is proving each one **landed**: an anchor that matches zero times mutates nothing, the suite stays green, and the run reports the guard as enforced — the failure `invariants.base.md` §"Mutation verification" names, and one every hand-rolled harness has to re-derive. It refuses any anchor not found exactly once — printing `hint:` lines with the near-miss line numbers, so a drifted anchor no longer costs a manual re-grep — restores the tree on every path including an interrupt, and re-runs the suite afterwards to prove the restore landed. The mutation run performs the sibling sweep itself before the baseline command and refuses on sibling drift with `MUTATION: PRECHECK_FAILED specs=N drifted=K unreadable=J` (exit 2), so a stale sibling spec cannot be hidden by running only the spec you happened to touch. The standalone diagnostic remains available as `python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py --check-anchors <spec.json>…` — or with **no spec at all**, which sweeps every committed spec in the repository (`git ls-files '*.json'` through the same classifier as the pre-push hook), so `h-mad/tests/specs/` and `handoff/tests/mutation-specs/` are reached without anyone remembering they exist; a habitual `tests/mutation-specs/*.json` once said ANCHORS_OK over a drifted `tests/specs/` spec — reading the `ANCHORS:` token, never `$?`; it applies nothing and runs no tests, so it costs file reads rather than a suite per spec, and it reads the same one-match rule the run does (`anchor_status`) rather than a second copy of it. `ANCHORS_DRIFTED` and `ANCHORS_UNREADABLE` are **separate verdicts because the remedy differs** — re-anchor a spec, versus restore a file that is gone — and `ANCHORS_UNREADABLE` outranks, since a spec cannot be re-anchored into a file that no longer exists (J37); `ANCHORS_UNREADABLE` also covers a swept file that is not valid JSON at all, which judged nothing for the same reason; both exit 2 and both carry `drifted=`/`unreadable=` counts, so the word chooses the FIRST action without hiding the other finding. The `MUTATION:` summary gains `unreadable=` for the same split, but keeps ONE `REFUSED` word: it has five causes and a single remedy, so five verdicts would be worse than the disease. `ANCHORS_DRIFTED` → re-anchor before trusting any verdict from that spec: a drifted anchor mutates nothing, so its run REFUSES, and a refusal measures NOTHING. A relative spec `root` is spec-relative, never cwd-relative: it resolves against the spec file's directory rather than the caller's cwd, which makes the spec portable across checkouts and correct inside a git worktree. Measured 2026-08-26: 7 of 177 anchors across 14 committed specs had drifted, and every one of those guards was unverified while its spec still reported a verdict-shaped line — two of the seven were broken by a refactor made minutes earlier in the same session.

  **To claim a prompt rule WORKS, run it against a control** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_ab_dispatch.py --template <prompt-with-{{VAR}}> --var VAR --a "<rule>" --b "" --observe '<regex with ONE capture group>' --out <dir> --run <argv token>…` (`{prompt}`, `{log}` and `{arm}` are substituted per arm — **put `{arm}` in every OTHER per-arm path you pass**, or both arms share it and arm B silently overwrites arm A, after which the comparison reads B against B and reports `SAME`, J40/F5). **It does not control the environment**: the tool holds the PROMPT constant apart from the declared variable and knows nothing about the rest — a changed file on disk, a different model default, an env var — so `UNCONTROLLED` only ever compares the two prompts, and holding everything else equal is yours to do. An unstated limit reads as a guarantee, which is why this is stated (J40/F3), reading the `AB:` token, never `$?`. One dispatch cannot distinguish a rule that steered the agent from an agent that would have done the right thing anyway, so "the rule is present" gets recorded as "the rule is causally effective". Three verdicts carry it. `UNCONTROLLED` → the arms differ in more than the declared variable (or in nothing), which is the mistake a hand-run A/B actually makes, and it is silent — the run completes, the numbers differ, and the difference is attributed to the wrong cause; nothing is dispatched. `INCONCLUSIVE` → an arm produced no log or the observable never matched, and **two silent arms compare equal**, so this must never read as `SAME`. `SAME` is itself a finding: the rule is present and not causally effective. **The exit code is reported and never scored** — a dispatch killed by its parent shell, a skipped test and a clean run all exit 0, and this repo has been fooled by each. **`--observe` takes the LAST match, not the first**, on the same rule as `h_mad_extract_verdict.py`: an agent's log carries the PROMPT before it carries the answer, so a first-match read routinely returns the observable's own name quoted back out of the instruction — and since both arms echo the same prompt, both observe the same value and the run reports `SAME`, a *finding* rather than an error (J39, measured: a log reading `RESULT: 0` as the echo and `RESULT: 42` as the answer observed `0`). The regex needs exactly one capture group and is refused at the boundary otherwise. **`--run` accepts a dash-leading token in either form** — `--run --model` and `--run=--model` both work; the space-separated form documented here used to fail with `expected one argument` for every real dispatch argv, since they all start with flags (J38).

  **Parking a mutation spec (D2), and the detector for one never moved back (#142).** Mutation rows are written at GREEN against source that exists, never at RED; a spec drafted before its source lands is *unanchored*, and an unanchored spec under `tests/mutation-specs/` reds the committed-spec sweep and blocks the pre-push hook. Park it instead as `docs/03-analysis/<feature>.pending-mutation-specs/<name>.json.pending` and restore it to `tests/mutation-specs/<name>.json` at that task's GREEN. **The parked copy stays afterwards as provenance — do not delete it.** The name match is the whole convention, so name the parked file exactly as the live one will be named. What nothing used to detect is the other case: `h_mad_phase7_preconditions.py` now blocks with `pending_mutation_spec_not_restored` when a `<name>.json.pending` has no live `<name>.json` in any `tests/mutation-specs/` directory up to two levels below the repo root (`--mutation-specs-dir` names one explicitly), and warns `pending_specs_unverified` when it finds parked specs but no such directory at all — "I could not check" is not "never moved back". A parked spec's guards were never measured, and the sibling sweep cannot see it precisely because parking moved it out of the swept directory.

  **After the LAST edit of a rename or removal, sweep the old identifier across every surface** — `python3 ~/.claude/skills/h-mad/scripts/h_mad_identifier_sweep.py <old-name>… --root <repo> [--allow <path>]…`, reading the `SWEEP:` token, never `$?`. It reports each remaining hit with its surface (code · comment · doc · test · mutation-anchor), so the surfaces that get missed unevenly are visible rather than remembered. `LEFTOVERS` is **not** a verdict that the hits are wrong: deciding explanation-vs-leftover is yours, and a deliberate one is passed with `--allow` rather than edited away — which is why the allowlist is an input and never inferred. Hits on the *stem* of a renamed file (`advisor-gate` after `advisor-gate.sh` is gone) are reported as `related:` and do not move the verdict, because prose naming the concept is both real signal and the sweep's main source of noise. The timing is the property: `a311385` renamed `hooks/h-mad-advisor-gate.sh` and shipped three stale references to a file the same commit deletes, after the sweep was started by hand mid-work and abandoned when more edits followed. Run at the end it costs a second; run during, it is unreliable in exactly the way that produced the defect. **Give every mutation a `test`** (plus a spec-level `target_command`) unless there is a reason not to: `ALL_CAUGHT` only says something went red, and a mutant killed by a crash, a timeout, or an unrelated assertion looks exactly the same as one killed by the guard. With a `test`, only that test counts as a kill and a wrong-catcher is reported as a SURVIVOR naming what actually bit. `SURVIVED` → halt `step5e:mutation_survived:<module>`: the guard does not bite, so write the discriminating test rather than weakening the mutation. `REFUSED` / `BASELINE_NOT_GREEN` / `UNREADABLE` → halt `step5e:mutation_unverified:<module>`: **nothing was measured**, which is not a pass — treat it exactly as you would a cannot-judge from any other gate.

Phase 5 implementation is **Codex's job** by default; FR-2 resolves the implementer
for each record, and Claude orchestrates, verifies, and gates while a peer authors.
Read the resolution with `h_mad_tdd_judge.py implementer`; stage it before dispatch
as described below. Authorship is enforced mechanically:

- **FR-2 — resolved implementer.** `implementer=codex|agy` selects the peer;
  absent or `null` selects `codex`. Use that peer if available, else the other peer.
  Availability requires its CLI on PATH, an empty `HMAD_<PEER>_UNAVAILABLE`, and
  its `<peer>_status` outside the escape statuses (`unavailable` or `exhausted`).
  A switch reports the first cause in order: `env`, `status`, `cli-absent`.
  Record an outage with `h_mad_state_write.py --feature <feat> --set codex_status=exhausted <state_file>`
  (or `agy_status=exhausted`), or export `HMAD_CODEX_UNAVAILABLE=1` or
  `HMAD_AGY_UNAVAILABLE=1` for a one-off outage. Only when **both** peers are out
  does `fallback_agent` select grok or Claude; absent, `null`, or `claude` means Claude.
- **FR-3 — Claude-side authorship.** The `Write|Edit` PreToolUse hook
  (`hooks/h-mad-tdd-gate.sh`) folds **every** `step5` record on the target's state
  chain, not just one `ACTIVE` feature. Any invalid `implementer` refuses first
  as `implementer-invalid`; otherwise the first resolved peer refuses Claude's
  production-`.py` write as `codex-authorship` or `agy-authorship`. Only with no
  resolved peer does the existing fallback fold apply: `fallback-invalid` outranks
  `fallback-grok`; absent, `null`, or `claude` everywhere admits Claude's test-first
  fallback. These refusals use JSON `permissionDecision: deny` with exit 0.
  Set the fallback with `h_mad_state_write.py --feature <feat> --set fallback_agent=grok|claude|null <state_file>`.
  `HMAD_CODEX_UNAVAILABLE` alone does not license Claude while agy is available,
  and does not override `fallback_agent=grok` when both peers are out.
- Peer writes run through their own processes and gates: Codex uses
  `h-mad/hooks/h-mad-codex-tdd-gate.py`; agy uses `h-mad/hooks/h-mad-agy-tdd-gate.py`
  with the wiring check and halt in `references/agy-runtime.md`. Grok writes pass
  **no write-time test-first gate**; the RED/GREEN dispatch and independent
  verification still carry the test-first obligation. A false availability or
  fallback declaration remains visible in the state record.

After any agy upgrade, re-run FR-8 step 2 and step 2a and re-take the class-(a) inventory.

Test files, docs, config, and shell are never gated; only production `.py`. A
`.py` counts as docs, and is not gated, only when the FIRST component of its
resolved path relative to the project root is `docs` (e.g. a committed probe at
`docs/03-analysis/probes/<feature>/x.py`); `src/docs/foo.py` and a top-level
`docs.py` stay gated, and a `docs/` spelling that symlinks out of `docs/` is
judged by its target. Both gates apply this same rule. The
gate stands down outside `step5` and disarms at 5g (`phase = null`).

### Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot

The pane REPL (`send`/`ask`) runs the agent as a long-lived TUI, so completion is
inferred by polling the buffer for idle and parsing a token — there is no process
to reap and no exit code. `exec` instead runs the agent headless as a real
subprocess and returns the agent's own exit code with no idle poll. **It is the
default for a one-shot 5d/5e dispatch** (see the guidance below), because the exit
code is a hard completion signal and it sidesteps most of the pane failure class —
tui-idle false-idle, scrape, identity resolution. Dispatch roles follow the
resolved implementer and the independent review assignment:

- **Stage the implementer.** Before every 5d and 5e dispatch, run from the project root:
  `python3 ~/.claude/skills/h-mad/scripts/h_mad_tdd_judge.py implementer --root . --feature "$FEATURE" --record`.
  Read the `TDD-IMPLEMENTER:` token, never `$?`, because the verb always exits 0.
  Check a line ending ` record=failed` first, whatever precedes it, before reading any other fields: **do not dispatch.** Halt `step5:implementer_switch_unrecorded` and print `[H-MAD] <feature> halt step5:implementer_switch_unrecorded`, because a switch that is not in state is the silent switch the operator decision forbids (FR-2).
  For `switch=none`, stage `h_mad_assemble_tdd.py --agent` with the resolved peer (`codex` or `agy`).
  For `switch=codex->agy` or `switch=agy->codex`, with `reason=`, stage the resolved peer and print the token line on the dispatch.
  For `switch=peers-out`, use today's fallback path (grok or Claude), unchanged.
  For `invalid field=`, fix the record and never dispatch: halt `step5:implementer_invalid` and print `[H-MAD] <feature> halt step5:implementer_invalid`.
  For `no-record` or `unreadable`, never dispatch: halt `step5:implementer_unresolved` and print `[H-MAD] <feature> halt step5:implementer_unresolved`; the feature name or root is wrong, or the state file cannot be read.

- **`exec codex`** — a resolved RED/GREEN IMPLEMENTER dispatch (writes tests + impl). Prompt
  via stdin; final message via `--output-last-message`; default `--sandbox workspace-write`.
  **Pass no `--model`/`--effort` unless you mean to override.** The one exception is
  the assembler's GREEN policy: `h_mad_assemble_tdd.py` prints `--effort medium` for a
  codex GREEN on a `new-behaviour`/`wiring` task and `--effort high` under `--escalate`
  (row 2934; see its registry entry). It is printed in the block, never applied silently. Unset, codex
  resolves both from its own `$CODEX_HOME/config.toml` (`model`,
  `model_reasoning_effort`) — the same file its TUI writes — so the model shown
  in the CLI is the model 5d/5e runs, and changing it in one place moves both.
  Nothing in h-mad injects a model. `--effort` is still accepted and reaches
  codex as `-c model_reasoning_effort=<e>` (codex has no `--effort` flag of its
  own); use it, and `--model`, only to deviate from the configured setting for
  one dispatch. **`$CODEX_HOME` is not always `~/.codex`** — under Orca it points
  at a per-account home, so read the value in the environment before concluding
  which config governs. Verify the resolution rather than assuming it: the codex
  session header at the top of `--log` names the resolved `model:` and
  `reasoning effort:`. `hmad-dispatch resolved-model codex --log <f>` reads exactly
  that, and `resolved-model codex` with no log reports the CONFIGURED value
  instead, labelled as such — a config says what will run, never what did. That check matters because a model can be configured that
  **cannot execute a single tool** (`gpt-5.6-luna`, measured): it still writes
  prose, so it comes back as a well-formed `STATUS: BLOCKED`, not as an error.
- **`exec grok`** — an explicit RED/GREEN implementer fallback when both peers are out
  and `fallback_agent=grok`. Stage with `h_mad_assemble_tdd.py --agent grok`;
  its default timeout is 1500 seconds. Grok's GREEN, mutation, and wiring are
  **unmeasured** (D4), and audit precision measured on 27 seeds: recall 12/27
  against agy's 10/27, fabrication 0/38 against agy's 0/23 (`SEEDSCORE: PASS`),
  measured with the calibration-only path-scope clause (AC-3.9)
  (`docs/03-analysis/grok-audit-surface.measurement.md`), so its verdict remains
  a claim until the independent checks run. From FR-11, `exec grok` always runs `--sandbox strict`:
  a weaker or unknown `--sandbox` value exits 2 unless
  `--allow-weaker-sandbox` is also given, which is recorded in `<log>.profile`,
  and `GROK_SANDBOX` is removed from grok's environment. In a git work tree it
  stages its prompt and `TMPDIR` under `<top level>/.h-mad/tmp/`, or under
  `<cd>/.h-mad/tmp/` when `--cd` is a subdirectory of the work tree (a nested
  sub-project), since the strict sandbox lets grok write only inside `--cd`.
  It exits 2, launching nothing, when the repository does not ignore that
  staging directory (`.h-mad/tmp/`, or `<cd>/.h-mad/tmp/` for a nested `--cd`),
  or when `git rev-parse` fails for a reason other than "not a git
  repository"; outside a work tree it uses `<cd>/.tmp/`.
- **`exec agy`** — a resolved RED/GREEN implementer dispatch, or the independent 5e-review (and Phase 3/4/5b audit) dispatch. Runs `agy --print`
  under `--output-format stream-json`, so the transcript is a live NDJSON event stream
  and the wrapper lifts the final response out of the stream's `result` event. A
  headless replacement for the agy `ask` scrape. Because it is a subprocess, it needs
  **no pane and no identity resolution** — the one thing the pane path can still fail
  at for an un-owned agent. The format switch is confined to the `--log` channel:
  `exec` stdout and `--out` still carry the response text verbatim.

Set `HMAD_EXEC_HEARTBEAT_SEC` to control the `exec` watchdog heartbeat interval in
seconds; it defaults to `120`, and `0` disables heartbeats. The feature adds
best-effort start, heartbeat, and exit worktree-comment checkpoints (mobile-visible
under Orca and a no-op on cmux), plus a best-effort desktop notification at exit.
These observability signals cannot change stdout or `rc`.

**Pass `--log` on every `exec` dispatch, background it, and poll `progress`.** Both
backends now write their transcript to `--log` while the run is in flight, so headless
is not blind — but only if you dispatch in a way that lets you look. A FOREGROUND `exec`
prints nothing until the process exits, which is what turns a 15-minute audit into a
blank screen indistinguishable from a wedged one.

**Do not use `tail -f` to watch.** It never returns, so it consumes your whole tool-call
budget and yields nothing; it is for a human at a terminal, not for you. Use
`hmad-dispatch progress <log>`, which returns immediately with a bounded digest.

```bash
# 5d/5e codex (implement), exit-code path. Background + poll:
hmad-dispatch exec codex <promptfile> --out /tmp/exec_<feature>_<module>.txt \
  --log /tmp/exec_<feature>_<module>.log --timeout 900 &
dispatch_pid=$!
hmad-dispatch progress /tmp/exec_<feature>_<module>.log --pid $dispatch_pid
wait $dispatch_pid                      # reap the dispatch
rc=$?                                   # operational: did the CLI run at all
python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_verdict.py \
  /tmp/exec_<feature>_<module>.txt --key STATUS --feature <feature> --phase 5d

# 5e-review agy (audit), exit-code path — no pane to resolve. Background it too:
hmad-dispatch exec agy <promptfile> --out /tmp/rev_<feature>_<module>.txt \
  --log /tmp/rev_<feature>_<module>.log --timeout 600 &
dispatch_pid=$!
hmad-dispatch progress /tmp/rev_<feature>_<module>.log --pid $dispatch_pid
wait $dispatch_pid
python3 ~/.claude/skills/h-mad/scripts/h_mad_extract_verdict.py \
  /tmp/rev_<feature>_<module>.txt --key VERDICT --feature <feature> --phase 5e
```

### Watching a headless dispatch

`hmad-dispatch progress <logfile> [--lines <n>] [--pid <pid>]` prints a bounded,
non-blocking snapshot: transcript format, size, **liveness** (seconds since the last
write, classified `LIVE`/`STALE`), optional process state, and a digest of the last
`n` events — one line per event, tool names and arguments included for agy, framework
`hook:` noise dropped for codex.

Read the `liveness:` line; **never branch on `progress`'s exit code**, which is 0 for
every observable state by design (a gate-shaped exit invites `progress … && continue`,
the `$?`-branching habit §"Audit-gate signal discipline" forbids). **And do not launder that exit code through a pipe**: `progress … | grep -q LIVE` reports *grep's* verdict, not `progress`'s, so a perfectly healthy poll of a LIVE log exits 1 whenever the pattern happens not to match. Measured 2026-08-27 (J35): all five observable states — fresh, dead pid, empty log, missing log, stale — return 0 from the wrapper, while `| grep -q IDLE` on a LIVE log returns 1. That non-zero was read as the wrapper's, and the row it produced blamed the wrapper. `progress` reports,
it does not decide.

- `LIVE` — the agent touched its transcript recently. Keep waiting.
- `STALE` — no write for longer than twice the heartbeat (`HMAD_EXEC_HEARTBEAT_SEC`,
  default 120s). Combined with `--pid …: exited`, that is a dead dispatch, not a slow
  one. The wrapper also writes `#hmad-beat` lines into the transcript on the heartbeat,
  so a genuinely silent-but-alive run still moves the clock — a transcript that stops
  growing entirely means the process stopped, not that the agent is thinking.
- `format: empty` vs `format: missing` — "started, nothing emitted yet" vs "never
  started, or `--log` was not passed". They demand opposite actions (wait vs
  re-dispatch); do not collapse them.

**Relay what you see.** Polling into your own context and staying silent leaves the
operator exactly as blind as before, which is the whole complaint this machinery exists
to answer. Between polls, surface one short line naming the agent, the elapsed time, and
the current step — e.g. `agy 5e-review · 4m · tool run_command (pytest -q)`. A live log
nobody reports is not observability.

**Do not poll on a timer when you only need the result.** A 30–60s poll cadence means
learning that a dispatch finished up to a minute after it did — which is pure added
latency, not observability. `exec` returns within ~1s of the agent producing its result
(measured: result at t+23.44s, `exec` returned at t+24.43s), so the delay is entirely in
how you wait. Instead:

- **Run the blocking form as a BACKGROUND command** (`exec-pane … --wait`, or
  `exec … &`) so the harness re-invokes you the moment it exits. That is a completion
  *signal*, not a poll, and it costs no context while waiting.
- **Poll `progress` only when you actually want the intermediate state** — to relay a
  status line, or to decide whether to keep waiting. Then one poll per 30–60s is right,
  and doing other work between polls is the point of backgrounding.

`--wait` itself polls the rc file at 0.5s, so it adds well under a second.

### Making a dispatch visible in Orca (zsh shell pane)

`progress` is for **you** (the orchestrator) — it costs context on every poll. When a
**human** wants to watch, run the dispatch in a real zsh pane inside Orca instead: the
pane renders in Orca's UI process, so it costs the orchestrator **zero** context and is
visible on mobile. The two are complementary; the pane is the cheaper channel whenever a
person is the audience.

This is NOT a return to the pane dispatch path. That path failed on **agent identity
resolution** (which pane holds agy vs codex — orca#9870), tui-idle false-idle, and TUI
scraping. A *shell* pane has none of those: the handle comes back from `terminal
split`/`terminal create` at creation, a shell command genuinely completes, and the verdict
still comes from `--out` — a file — not from a scrape. The pane is a **viewport**, never a
transport.

Use the **`exec-pane`** verb — do not hand-assemble this. It builds the in-pane
digest loop and the rc capture for you, which is what makes the three traps below
unreachable rather than merely documented.

```bash
# SAME SURFACE: split the pane you are in (uses ORCA_TERMINAL_HANDLE, set by Orca).
hmad-dispatch exec-pane agy <prompt> --cd <repo> --out <o> --log <l> --timeout 900 --split
# → returns immediately; stdout is the new pane's handle.

# OWN TAB (the default — no guessing which pane to split):
hmad-dispatch exec-pane agy <prompt> --cd <repo> --out <o> --title "5e-review agy"

# DROP-IN for `exec`: blocks until done, stdout = the response, rc = the dispatch's.
hmad-dispatch exec-pane agy <prompt> --cd <repo> --out <o> --wait --wait-timeout 1200
```

**Panes are pooled and reused.** By default `exec-pane` looks for an idle pane it
created earlier in the same worktree and dispatches into that one, so you end up with a
single h-mad pane per worktree rather than a new tab per dispatch piling up until you
close them by hand. Only panes this verb created are ever reused: each registers and
releases its own slot from inside itself, so a pooled pane is provably a shell and
provably idle. Foreign panes are never probed — proving one is an idle shell is not
possible from Orca metadata (there is no busy/idle field), and probing by sending text
would type into an agent's TUI if the guess were wrong. `--no-reuse` forces a fresh pane;
`--split`/`--new-tab` bypass the pool entirely. A pooled pane is registered under the handle
resolved by joining the create response's `paneKey` against `terminal list`, not the
`.result.terminal.handle` the response carries — that field has been observed to be a
pre-adoption placeholder (J1), and pooling one would hand the next dispatch a handle Orca
has never heard of. Unlike `launch`, a response with no `paneKey` is not fatal here: the
dispatch is already running by then, so it falls back to the response handle with a
warning (`HMAD_PANE_RESOLVE_TIMEOUT`, default 5s, bounds the join). Slot state lives in files under
`.h-mad/panes/` (override with `HMAD_PANE_SLOT_DIR`) rather than in the tab title,
because the shell rewrites the title via OSC on every prompt — a pane renamed to
`h-mad slot · idle` reads back as `~/orca/skills` the moment it reaches a prompt.

`--wait` still returns the moment the rc file lands, ~1-2s before the pane finishes its
last digest and releases the slot — the verdict must not wait on cosmetics. A dispatch
fired inside that gap used to create a second pane; it no longer does. A pane drops a
`.finishing` marker as soon as its dispatch completes, and a claim that finds nothing idle
waits (default 8s, `--reuse-wait`, or `HMAD_PANE_REUSE_WAIT_SEC`) **only** for a slot
carrying that marker. A busy slot without one is genuinely working, so it is never waited
on — which is what keeps Phase 5 parallel fanout from paying the wait on every dispatch.
The wait costs no verdict latency: it happens before the dispatch starts, not after it
ends. It also refreshes its view of which panes are live as it waits, so a pane that dies
mid-wait ends the wait instead of running it out, and its stale marker is reaped.

`--split` with no value means **this** terminal — the only unambiguous reading of "the
same surface". It refuses rather than guessing a pane from `terminal list`: guessing
reopens the identity-resolution problem this verb exists to avoid, and could drop a
shell into an *agent's* tab. Pass `--split <handle>` for a specific pane, `--new-tab` to
force a tab. Outside Orca the verb **refuses** instead of quietly running headless — a
silent fallback leaves you watching for a pane that never appears, with a success exit
code on top. Also: `--direction horizontal|vertical`, `--poll <sec>` (in-pane digest
interval, default 6), `--focus` (new tab only), and `--model/--timeout/--sandbox/--effort`
passed through to `exec`.

**Two output contracts, deliberately different.** Without `--wait`, stdout is the pane
handle — the useful value while the run is in flight. With `--wait`, stdout is the
response, matching `exec` so the verb is a drop-in. `--wait` blocks on the rc **file**
and clears any stale rc first: `--out` paths are templated per feature+module and the
`no_verdict` remedy re-dispatches to the same path, so a leftover rc would otherwise
hand back the *previous* run's exit code instantly.

Three findings, each measured live on 2026-08-19. `exec-pane` closes all three in code;
they are recorded here because anyone assembling a pane command by hand will hit them,
and because the verb's shape is otherwise hard to justify:

1. **A pane running `exec` bare is BLIND.** `exec` redirects the agent's stream into
   `--log`, so the pane shows only the echoed command line and then nothing until the run
   ends — the exact blindness this whole section exists to cure, relocated somewhere
   prettier. Measured: at t+14s the pane held one line while `--log` already had three
   events. **The pane must tail or digest the log itself**, which is why
   `exec-pane` always provisions a `--log` and always builds the digest loop. (`tail -f <l>` also works here and is the one place it is appropriate — a human
   pane, never an orchestrator tool call.)

2. **`orca terminal wait --for exit` does NOT carry the command's exit code.** A pane
   running `sleep 2; exit 9` reported `{"satisfied":true,"status":"exited","exitCode":0}`.
   Reading that as the dispatch rc turns **every failure into a success** — the same
   `$?`-shaped defect §"Audit-gate signal discipline" forbids elsewhere. Capture rc from
   the command itself (`echo $? > <o>.rc`, verified returning 3 and 7 correctly), or use
   `report-wait`, which polls a path plus a `.done` marker and is transport-agnostic. **For a backgrounded `exec`, poll its `--out` with `report-wait <out> --no-done-marker`** rather than a sleep ladder — waiting on one was written ~25 times in a single session as `for i in 1 2 3; do hmad-dispatch run --timeout 110 -- sleep 105; done` plus a `test -f`, whose purpose is invisible to the next reader and whose arithmetic, when wrong, wastes wall-clock silently. The flag is opt-in because the `.done` marker is what keeps a half-written report unreadable for every other caller, and it is only sound at all because `exec` writes `--out` **atomically** (temp + rename): a `cp` or a `>` redirect can put a partial — or, for a redirect, a zero-byte — file under a poller checking existence, and a truncated verdict reads exactly like a real one. Note the verb name: `await` is already taken by the Orca task-id wait and answers a different contract.
   `exec-pane` never calls `terminal wait` at all.

3. **`wait --for exit` is unusable here in both directions.** End the command with `exit`
   and the shell dies: `wait` satisfies, the code is still wrong, and the scrollback goes
   with it. Let it return to a prompt (what you want — the scrollback is the point) and
   `wait --for exit` **times out**, because the shell is still alive. Neither shape gives
   a completion signal, so do not build one on it.

The verdict path is untouched by any of this: `--out` still holds the response, `--log`
still holds the stream, and `h_mad_extract_verdict.py` still reads the file. Never scrape
the pane for a verdict.

### Dispatch channels and their guarantees

The verdict comes from `--out` (the `--output-last-message` file / captured response),
which only lands at completion — so `--out` is NOT tailable. `--log` is: it streams
the live transcript to `<file>` as it runs — plain text for codex, the NDJSON event
stream for agy — without disturbing the verdict on stdout or the exit code. Watch it
with `hmad-dispatch progress`, never `tail -f` (see §"Watching a headless dispatch").
`--log` appends on both backends, so a caller-supplied log retains its prior content.

**Give every dispatch its own `--out`.** It is last-writer-wins: two dispatches
sharing one path both exit `0` and the file keeps only the second answer, so a
lost verdict is indistinguishable from a dispatch that never ran (J29). As a
backstop `exec` refuses to overwrite an `--out` whose content changed
while it ran — the other dispatch's file is preserved, this one's answer still
reaches stdout and `--log`, a `REFUSING to overwrite --out` line goes to stderr,
and `rc` is untouched (it answers "did the CLI run", nothing else). A stale
`--out` left by *this* caller's own failed attempt is unchanged since start and
so is still overwritten — which is what keeps the `no_verdict` re-dispatch remedy
(`references/failure-recovery.md`) working against its templated path. An
`--out` that cannot be written at all (e.g. a directory that does not exist) fails
the same soft way: a `cannot write --out` line on stderr, the answer still on stdout
and in `--log`, `rc` untouched (J56).

**`rc` and the token are different questions.** `rc` is operational (`0` = the CLI
completed, `124` = watchdog timeout, non-zero = crash/abort); it does **not** mean
the TDD task passed. Read the `STATUS:`/`VERDICT:` token exactly as the pane path
does (§"Reading a dispatch verdict") — exit 0 with `STATUS: BLOCKED` is still a halt,
and Codex GREEN still needs the anti-gaming verify. `rc` replaces the *idle poll*,
not the *verdict extraction*.

An `exec` with an empty primary channel returns **rc 3** when the agent exited 0;
the wrapper recovers the last `STATUS:`/`VERDICT:` line from the transcript when
present and reports the working-tree delta, so check the tree and verify the code
before treating the dispatch as complete. Exec dispatches use terminal/last-message
mode: leave the report-file slot empty. Report-file mode belongs to the pane path
(`send`/`report-wait`), not to `exec`.

**Exception — `exec agy` on an audit phase: fill the report-file slot.** That rule is
codex-shaped, where `--output-last-message` *is* the deliverable. On an audit the report
is the deliverable, and `agy --print` surfaces only the agent's **last** message, so the
report has exactly one fragile channel for the DELIVERABLE. (Since `exec agy` moved to
`--output-format stream-json` the `--log` stream does retain earlier turns' text, which is
a recovery route — see `references/failure-recovery.md`. It is not a second delivery
channel, so fill the report slot anyway.) Measured 2026-08-01,
`grounding-shadow-measurement` design cycle 2: 358 bytes of narration ("I have completed
the audit and output the results as requested") naming the two Must-fix items it had
actually found, with no `<AUDIT_SENTINEL>` pair — `h_mad_extract_report.py` exit 2. Cycle
1 of the same feature on the same config delivered a clean 2.9 KB sentinel report, so the
empty slot is not itself the defect — it is intermittent. **Two mechanisms fit the
evidence and this data cannot separate them:** either the report was emitted and a later
summarizing turn became the last message, or it was never emitted and the agent narrated
having done so — the latter is catalogued as **F-10 claim-execution divergence**
(`AGENTS.md`; agy's self-narrative diverging from actual execution, rule: never trust the
narrative, verify the artifact). Discriminating them needs the agy-side trace, and the
remedy is the same either way, so do not spend a cycle on it. Fill the path and block on
`report-wait "$RP"` — the verb polls a path
and a `.done` marker, so it is transport-agnostic and works behind `exec … &` just as it
does behind `send`. A file cannot be overwritten by a later turn.

**A missing report on the `exec` path — recover from `--log` and the working tree, never
from the pane.** The pane-path rule above ("A missing report is neither pass nor fail")
tells you to *read the pane*; on `exec` there is no pane, so that recovery does not
apply and the step used to have none. Measured 2026-07-30 on a real 5e GREEN: the
`exec codex` dispatch wrote **neither** its report file nor the `.done` marker, the
process was gone, and the wrapper's own captured stdout was empty — while the working
tree held **both** artifacts, complete and correct (a one-line production edit plus a
new test module). Read in the wrong order that is a `step5e:no_verdict` halt over
finished work; read as "DONE because the tree changed" it is an unverified pass.

Recover in this order:

1. **`--log`** — it survived when `--out` and the report file did not, and it holds the
   live transcript, including the diffs the agent applied. This is the strongest reason
   to pass `--log` on every `exec` dispatch: it is the one channel observed to outlive
   the others. It appends on both backends, so a caller-supplied log retains prior
   content. **This used to be pointless for `exec agy` and no longer is.** While agy ran
   in text mode the two channels were byte-identical (verified on both cycles of a real
   design audit — `diff` clean at 2.9 KB and at 358 B), so reading `--log` after a short
   agy exec was the same bytes twice. Under `--output-format stream-json` the log holds
   the whole event stream — every tool call, its arguments, its duration — while `--out`
   holds only the final response. So on an agy exec that came back short, `--log` now
   carries strictly more than `--out`: read it, and read it with
   `hmad-dispatch progress`, which digests the stream instead of dumping raw NDJSON.
2. **`git status` / `git diff`** — enumerate what actually landed. Artifacts present with
   no report means the work happened and the reporting channel failed, which is a
   different situation from a crash before any write.
3. **Verify from the code, not from a self-report.** Re-derive the verdict yourself: run
   the module's tests, run the acceptance test the task was gated on, and execute the
   mutations the task required. A missing report is in one respect an advantage — there
   are no claimed counts to anchor on, so the anti-gaming pass is forced rather than
   optional. In the measured case the work was correct **and** its required mutations had
   never been executed; the tests pinned them, but pinning is not the same as having run
   them.

Do **not** re-dispatch before step 2. A re-dispatch onto a tree that already carries the
work is how a second, conflicting implementation gets written over a correct one.

**All three steps are scoped to an implementer dispatch — do not apply them to `exec
agy`.** They exist because a codex RED/GREEN leaves artifacts in the working tree, which
is both the thing to recover from and the reason a blind re-dispatch is destructive. An
audit writes nothing to the tree, so steps 2–3 have no delta to enumerate and no code to
re-derive a verdict from. **Step 1 is the exception and it now carries real weight:** it
used to be the same bytes twice, but under `--output-format stream-json` an agy `--log`
holds the whole event stream, so it is worth reading on its own before anything else.
A short or sentinel-less agy exec is therefore a plain `<phase>:no_verdict` halt whose
documented route is the opposite of this one — read the stream with
`hmad-dispatch progress <log> --lines 50` first, and only if the report is genuinely
absent, re-read, then `hmad-dispatch clear agy` and re-dispatch (audits are idempotent,
so that is safe). Never score the narration: the 358 B
case named real findings and would have read as a substantive review to a human skimming
it, while carrying no schema the gate can count.

**Output loss is not agent-specific.** In the same session a backgrounded `pytest` run
also completed while its captured output came back empty, so treat "process gone, output
empty" as a transport symptom rather than evidence about the work. When a long run's
result matters to a gate, redirect it to a file you name yourself (`> /tmp/<run>.log 2>&1`)
instead of relying on the harness capture, and re-run rather than inferring the result.

**Default for a one-shot 5d/5e dispatch is `exec`.** A single self-contained RED/GREEN
or a single audit cycle has no prior-cycle conversation to preserve, and the exit code
is a hard completion signal — so `exec` sidesteps most of the pane failure class at once:
no tui-idle false-idle, no scrape, no identity resolution. Monitor it
by tailing `--log` (above); headless is not blind.

**Prompt echo is NOT one of the things `exec` sidesteps — it is handled, which is a
different claim.** `codex exec … -` echoes the piped prompt into its transcript, so the
`exec` *failure* path reads a log that contains your own prompt. This shipped a real
false verdict on 2026-08-03: a dispatch that died on revoked auth returned
`STATUS: NEEDS_CONTEXT` — the last option of the prompt's own contract block — and wrote
it to `--out`, where `h_mad_extract_verdict.py` accepted it. `exec` now appends the same
`===HMAD-DISPATCH-BOUNDARY===` that `send` does and recovers only from after its last
occurrence; for codex, a transcript with no boundary at all (a truncated echo) recovers
**nothing** rather than guessing. Two consequences for you:

- **A recovered verdict is still not a reported verdict.** Recovery reads a transcript,
  not the agent's final message. Treat it as a hint for triage, never as the gate input.
- **`tree delta: N changed in <dir>` is scoped to `--cd`** (it was whole-repo until the
  same date, so a stale file elsewhere read as "the work landed"). A zero delta plus no
  verdict is the honest signature of a dispatch that never ran — re-dispatch it.

**Switch to the pane path when** the running revision thread matters — cycles 2..N of
the *same* 5e ("here's the fix for your prior should-fix"), where `exec`'s fresh session
each call would re-send the whole context — or when a human wants to watch/intervene in
the Orca pane live. In short: **one-shot → `exec`; iterative revision loop → pane.**

Codex sandbox defaults to `workspace-write` (5d/5e write test + impl files); its
prompt is delivered on stdin, so the 8192-byte keystroke inline cap and the pane-path
size frontier both do not apply — but stdin is **not uncapped**: codex refuses any
prompt past **1,048,576 characters** with `input_too_large` before running a turn
(measured 2026-09-05 on two real gating prompts — the full-history design and
impl-plan audits — and re-measured the same day with a 1,111,089-char probe: rc=1,
an empty last message, one `Error: turn/start … "input_error_code":"input_too_large"`
transcript line). agy runs `--print --dangerously-skip-permissions` (headless must
auto-approve or a tool request blocks); its prompt is an arg, bounded by `ARG_MAX` —
the same 1,048,576 figure. **That bound is the KERNEL's, and agy never sees an oversize prompt at all**: measured 2026-09-13 against agy 1.2.2, a 1,100,047 B argv raises `OSError 7 Argument list too long` at `execve`. agy does not truncate it and reports no limit of its own, which is what makes the assembler's halt message true rather than merely plausible. `exec` now refuses such a prompt ITSELF — `hmad-dispatch: exec: OVERSIZE prompt bytes=N budget=M arg_max=A reserve=R` at rc 2 — because `exec` takes any file and has no assembler gate, and because the exec redirects the child's stderr to `/dev/null`, so the kernel's reason used to vanish and the wrapper reported `EMPTY final message — agent exited 126`: a statement about an agent that was never entered, sending the operator after a timeout or an empty reply instead of a smaller prompt. Audit prompts run 16–90 KB (a large design audit
assembles to ~88 KB), and **266,342 B (260.1 KB) was confirmed answered 8 of 8 on
2026-08-22** (agy 1.1.18), every run honouring both the report-file slot and the
sentinel pair — so at the sizes audits reach, the `exec` path has no transport
limit, only the receiving model's context budget. Do not trim an audit for size when
dispatching via `exec`. When a prompt does run past the ceiling — a full-history
design or impl-plan inline can — `h_mad_assemble_audit.py` HALTs `oversize` and
writes nothing, and the **first remedy is `--vh-tail N`** (body verbatim, only the
last N Version History entries of each embedded document inlined; the rest stay
reachable via `git show <sha>:<doc>`), never a trimmed document. If a refused prompt
does reach codex, `hmad-dispatch exec` reports `INPUT_TOO_LARGE` with
`max_chars=`/`actual_chars=` on its own stderr line and skips verdict recovery and
the tree-delta read — it used to flatten the refusal into the generic `EMPTY final
message` and then print a `tree delta` the recovery protocol reads as "the work
landed". (The pane path is separately confirmed answered to 92,055 B — see
`references/agent-substrate.md` §"Prompt size".)

**After GREEN, run the built binary against the design's documented output shapes** — every verdict
line, every field-presence rule — rather than only running the suite. There is no fixed command,
only a fixed question: *does the running binary emit what the design says it emits?* On one task
this found **four of five defects that neither the 49-test suite nor an independent reviewer saw**:
a hardcoded `cycle=1` behind an undeclared `--cycle`, a float/int mismatch that crashed every real
wait behind ten stubbed tests, a checklist printed on a cannot-judge verdict, and a verdict line
that did not match its own AC. Stubs are what make this necessary — a suite can be green about a
binary that never runs.

