# Plan: agy-coder-fallback

> **Slug note.** The slug predates brainstorm v1.1. agy is a **peer** Phase-5 implementer with
> Codex's standing, not a fallback (spec §"Slug note").

Source: `docs/01-plan/features/agy-coder-fallback.spec.md` v1.2 (operator-approved), read at commit
`17d73037`. Every "currently" claim below was re-read from the tree at `17d73037`, and the command
that read it is written beside it. Commands run from the repository root unless they start with
`cd`.

## Executive Summary

Make the Phase-5 implementer a per-feature choice between two peers, `codex` and `agy`. One
resolution function in the TDD judge decides who authors. Claude's gate refuses for whichever peer
is resolved. A new agy write gate enforces test-first on agy's own tools. Every code-review leg
records whether its reviewer was also the implementer, and Phase 7 surfaces that for every
implementer, Codex included.

## Overview

Today Codex is the only Phase-5 implementer h-mad accepts. The state schema, Claude's
authorship gate, the dispatch assembler and the implementer prompt all hard-code it, and agy has no
write gate at all (spec §"Problem"). The operator wants agy usable whenever Codex is unavailable,
and selectable per feature, with no loss of the test-first guarantee and with any automatic switch
made visible. agy is already installed (`agy --version` → `1.3.6` at `17d73037`) and already
dispatched headless by `hmad-dispatch exec agy` for review legs.

## Scope

In scope, all under `h-mad/` unless noted:

- **State**: four optional fields in `h-mad/scripts/h_mad_state_schema.json` and their rows in
  `h-mad/references/state-schema.md` (FR-1).
- **Resolution**: one function and one CLI verb, `implementer`, in `h-mad/scripts/h_mad_tdd_judge.py`
  (FR-2).
- **Claude-side gate**: `h-mad/hooks/h-mad-tdd-gate.sh` reads the resolution from the judge and refuses
  per peer (FR-3).
- **agy write gate**: a new `h-mad/hooks/h-mad-agy-tdd-gate.py`, with its wiring check (FR-4, FR-5).
- **Shared shell policy**: one module imported by both the Codex gate and the agy gate (FR-6).
- **Review independence**: the state record and the Phase-7 warnings (FR-7).
- **Live tracer**: a real agy RED/GREEN under `docs/03-analysis/probes/agy-coder-fallback/`, which
  also sets the `--agent agy` default timeout (FR-8).
- **Prompt**: `h-mad/references/codex-implementer-prompt.md` becomes implementer-neutral and gains the
  WIRE-PIN new-caller rule (FR-9).
- **Docs**: SKILL.md, `h-mad/references/agy-runtime.md` and `h-mad/references/state-schema.md` (FR-10).
- **Per-project wiring**: a tracked `.agents/hooks.json` in each project that adopts the agy gate
  (D-2, D-10).

User-visible behaviour: the operator sets `implementer=codex|agy` on a feature record. The
orchestrator stages whichever peer resolves and prints any switch on the dispatch. A Phase-7 report
may now carry `review_non_independent`, `review_independence_unrecorded` or
`review_independence_malformed` warnings.

## Goals

- **G1 (FR-1).** The schema declares `implementer`, `agy_status`, `implementer_switch` and
  `review_independence` as optional. Records written before this feature validate unchanged.
- **G2 (FR-2).** Exactly one function resolves who authors a record. Both the gate and the
  `implementer` verb read it, and neither re-derives any part of it.
- **G3 (FR-3).** Claude's gate refuses for the resolved peer (`codex-authorship` /
  `agy-authorship`). It refuses `implementer-invalid` first. The `fallback_agent` fold fires only
  when both peers are out. The three existing message texts stay byte-identical.
- **G4 (FR-4, FR-6).** agy cannot write a production `.py` without a failing test during active
  step5, through any tool. Tools the gate does not know are denied, and the shell gets Codex's
  command-shape rule from the same implementation.
- **G5 (FR-5).** A project that lacks the wiring halts `step5:agy_tdd_hook_unverified` before any
  agy prompt is written. It never passes silently.
- **G6 (FR-7; D-9, D-11).** Every code-review leg records whether it was independent, for **every**
  implementer (`codex|agy|grok|claude`). Phase 7 warns on a non-independent leg, on a malformed
  entry, and — whoever implemented — on a 6a-prime leg that ran with no `leg=6a-prime` entry. These
  are warnings only, never blockers.
- **G7 (FR-8).** A real refusal by agy is observed, a real agy RED/GREEN passes the same evidence
  bar as Codex, and the default timeout is derived from measured turns.
- **G8 (FR-9, FR-10).** The prompt and the docs stop telling a non-Codex implementer it is Codex,
  and a valid new-caller RED is no longer halted as `red_wrong_reason`.

## Requirements

This plan satisfies FR-1 through FR-10 of the spec, with acceptance criteria AC-1.1, AC-2.1, AC-2.2,
AC-3.1, AC-3.2, AC-4.1, AC-4.2, AC-5.1, AC-6.1, AC-7.1, AC-7.2, AC-8.1, AC-9.1 and AC-X. The
decisions D-1..D-11 are inputs, not open questions. Two of them must be carried exactly as the
spec states them, because the brainstorm's framing was narrower:

- **D-9.** The non-independent flag fires whenever `reviewer == implementer`, Codex reviewing Codex
  included (for example the 5e anti-gaming verifier dispatched to Codex on a Codex feature).
- **D-11.** `review_independence_unrecorded` fires for **every** implementer. Its trigger is that
  a 6a-prime leg ran (`archreview` is `READY_TO_MERGE`, `WITH_FIXES` or `NO`) and there is no
  `leg=6a-prime` entry. No grandfather rule applies. No surface this feature writes may restate
  that trigger as agy-only.

## Implementation Strategy

**Order of work.** Each stage depends only on the stages before it. Each stage is one or more
impl-plan Tasks, and the full h-mad suite runs per Task (see §"Success Criteria").

1. **Schema and writer (FR-1).** Declare the four fields. Also rewrite the `fallback_agent`
   `description` in `h_mad_state_schema.json` and its row in `state-schema.md`. Both currently tie
   the field to Codex alone: the schema says it "is read only when codex is out"
   (`grep -n 'read only when codex is out' h-mad/scripts/h_mad_state_schema.json`), and the
   reference row says "Optional Phase-5 author when Codex is out"
   (`grep -n '^| .fallback_agent' h-mad/references/state-schema.md`). After FR-3 both are false:
   the field is read only when **both** peers are out. The spec does not list this surface, so this plan adds it.
2. **Resolution function and the `implementer` verb (FR-2).** The env-var and `PATH` evaluation
   moves out of the hook into the judge. The `--record` write goes through
   `h_mad_state_write.py`'s write path.
3. **Claude-side gate on the new state line (FR-3).** This rewrites the hook's state parse and
   fold, which is where the existing mutation anchors sit (see §"Risks").
4. **Shared shell-policy module (FR-6).** This is a pure move out of
   `h-mad/hooks/h-mad-codex-tdd-gate.py`. Codex-gate behaviour does not change, but the mutation rows are
   re-pointed in the same Task.
5. **agy gate (FR-4), then its wiring check and assembler enforcement (FR-5).** The gate imports
   the module from stage 4 and the judge from stage 2.
6. **Prompt and doc surfaces (FR-9, FR-10)**, including the WIRE-PIN new-caller rule on every
   surface that states the halt (see §"Architecture Considerations", the halt-surface census).
7. **Review-independence warnings (FR-7)** in `h-mad/scripts/h_mad_phase7_preconditions.py`, plus the
   SKILL.md text that tells the orchestrator to append an entry after each leg, for every
   implementer.
8. **Live tracer (FR-8)**, which also replaces the provisional timeout. It runs last because it
   needs the gate **installed**, and that interacts with the worktree (see §"Risks", R-2).

**Patterns followed.** Token-line CLIs that the caller reads by token, never by `$?`, as every
existing h-mad gate does. One implementation per policy, imported, never copied. A mutation row
for every new guard, scored by `MUTATION: ALL_CAUGHT` with a `test` per row. Fail-closed on
anything unparseable during active step5.

**Deliberately not touched.** The audit-leg routing in Phases 3/4/5b (`codex_status` still routes
the second audit surface, and `agy_status` has no audit consumer; D-8). The prompt's filename (FR-9
residual). The grok path beyond the fold's new trigger. `h_mad_extract_verdict.py` output (D-7).

## Architecture Considerations

**Design obligations.** The spec leaves these to Phase 4. They are listed so the design cannot skip
them. The plan does not settle them.

- **DO-1 — the `TDD-STATE:` line shape (FR-3).** The line must carry everything FR-3 steps 1 and 2
  need, so the hook never reads state or `PATH` itself. Every added field gets a closed value set.
  An unknown value matches no alternative of `STATE_ACTIVE_RE` and refuses `judge-error`.
  The design must also say what happens to every **existing literal of the line** in the tree
  (see DO-1a).
- **DO-1a — the line's existing literals.** The line is a contract with copies outside the judge
  and the hook. Command and reading at `17d73037`:
  `git ls-files -z h-mad | xargs -0 grep -l 'TDD-STATE: active'` → **6 files**:
  `h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad/scripts/h_mad_tdd_judge.py`,
  `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json`, `h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py`,
  `h-mad/tests/test_h_mad_tdd_gate_judge.py` and `h-mad/tests/test_h_mad_tdd_judge.py`. Two of those copies
  are fixtures, not assertions about the line. `test_h_mad_tdd_gate_judge.py` `_tree_b` stubs the
  judge's `state` verb with an old-shape line as its default, and
  `test_h_mad_tdd_gate_fallback_agent.py` builds stub lines from `PREFIX`. A third copy pins the
  line: `test_h_mad_tdd_judge.py` `ACTIVE_RE` is anchored with `$`, so an appended field fails it.
  This collides with AC-3.2 ("every existing `test_h_mad_tdd_gate_*.py` stays green
  **unmodified**"), which covers the two fixture files. The design must choose a shape under which
  the old-shape stub lines still reach the outcomes those tests assert. Otherwise the spec must
  relax AC-3.2 for stub fixtures. This is filed, not chosen here (§"Owed by other documents").
- **DO-2 — the read-only allowlist (FR-4 class a).** The design fixes the exact list. Anything not
  on it falls to class (d) and is denied. The list is a closed set over an open inventory, so
  the design must name the inventory it was checked against (the `init.tools` array in
  `docs/03-analysis/probes/multi-host-runtime/rehearsal/live-agy-2026-10-01.log`), with that log's
  agy version.
- **DO-3 — how a `review_independence` entry is appended (FR-7).** The spec says the orchestrator
  "appends one entry with `h_mad_state_write.py`". The writer has no append operation. Its
  `--set KEY=VALUE` replaces the whole value, and `_parse_value` JSON-decodes it
  (`grep -n 'add_argument\|def _parse_value' h-mad/scripts/h_mad_state_write.py`). Appending
  through `--set` is therefore a hand read-modify-write of the whole array, which can silently
  drop an earlier entry. The design must either add a writer operation that appends one validated
  entry under the claim/session rules, or state the read-modify-write procedure and its residual.
- **DO-4 — schema constructs.** Without `jsonschema` installed, `h_mad_state_validate.py` falls
  back to a bundled validator. That validator supports only `type`, `enum`, `required`,
  `properties`, `additionalProperties`, `items`, `minimum`, `maximum` and `minLength`, and it
  **ignores** any other keyword (`grep -n 'Deliberately supports ONLY' -A 4
  h-mad/scripts/h_mad_state_validate.py`). If the FR-1 schema used `format`, `oneOf`, `anyOf` or
  `const`, it would reject on one validator path and accept on the other. AC-1.1's reject cases
  must run on **both** paths, using the existing test seam that forces the bundled path.
- **DO-5 — the shared shell-policy module's boundary (FR-6).** The policy is more than
  `_safe_shell_command`. Its module-level call closure in `h-mad/hooks/h-mad-codex-tdd-gate.py` holds
  10 functions at `17d73037` (command below), and that closure includes `_load_judge`. The
  operator allowance (`_shell_allowance`, `SHELL_ALLOW_FILE`) sits outside it. The design names
  the exact set it moves, and the mutation-row census (R-3) is re-derived over that set.
- **DO-6 — where the agy gate reads its installed path (FR-5).** The wiring command is
  `python3 ~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py`. On this machine that is a
  symlink into this repository's **main** checkout (`ls -la ~/.gemini/config/skills | grep h-mad`
  → `h-mad -> /Users/kimhawk/orca/skills/h-mad` at `17d73037`). The design must state how the FR-5
  check and the FR-8 tracer behave in a Phase-5 **worktree**, where the new gate exists only in the
  worktree (R-2).

**Integration points.**
- The judge runs as a child of each gate and inherits its environment. The resolution reads
  `HMAD_CODEX_UNAVAILABLE`, `HMAD_AGY_UNAVAILABLE` and `PATH` there.
- agy's hook contract: stdout `{"decision": …, "reason": …}`, handler cwd is the directory that
  holds `hooks.json`, and the default handler timeout is 30 s
  (`grep -n 'Execution timeout' -A 1 ~/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs/hooks.md`).
  The handler timeout floor is `JUDGE_BUDGET_S + 20`. `JUDGE_BUDGET_S` reads `40.0`
  (`grep -n '^JUDGE_BUDGET_S' h-mad/scripts/h_mad_tdd_judge.py` at `17d73037`). The wiring check
  must read the constant from the module and must not restate it.
- The headless transport: `hmad-dispatch exec agy` launches agy with
  `--dangerously-skip-permissions` and `--output-format stream-json`
  (`grep -n 'dangerously-skip-permissions\|output-format stream-json' h-mad/scripts/hmad-dispatch.sh`).
  Whether a `deny` still binds under `--dangerously-skip-permissions` is not stated in hooks.md.
  FR-8 step 2 settles it only because it runs through that same transport, so the tracer must not
  use a hand-built agy command line.
- agy merges hooks from several sources, and a PreToolUse output may carry `overwrite`, a
  shallow merge into the tool call's args before it runs (hooks.md §PreToolUse output). If another
  handler rewrites a path key after this gate judged it, the gate judged the wrong path. The design
  states this as a residual, or shows that agy applies `deny` before any `overwrite`.

**The halt-surface census for FR-9.** The spec names three surfaces for the new-caller rule: the
prompt's RED item 1, its WIRE-PIN paragraph, and the GREEN variant, plus the SKILL.md 5d halt
text. The halt token is stated in more places than that. Command and reading at `17d73037`:
`git ls-files -z | xargs -0 grep -l 'red_wrong_reason' | grep -v '^docs/archive/'` → 4 files:
the spec itself, `h-mad/SKILL.md`, `h-mad/references/failure-recovery.md` (its recovery-table row
for the 5d halt) and `h-mad/tests/test_h_mad_wiring_task_shape_docs.py` (which pins that the token
is in both SKILL.md and failure-recovery.md). The recovery-table row states the remedy for the
halt, so the carve-out must land there as well, worded identically. The spec does not list it, so
this plan adds it.

**Tradeoffs kept.**
- The static wiring check proves the wiring entry exists, not that agy honours it (FR-5 residual).
  Only a live refusal proves that.
- The prompt keeps its `codex` filename. The spec's command reproduced at `17d73037`:
  `git ls-files h-mad | xargs grep -ln 'codex-implementer-prompt' | wc -l` → 20 files. A rename is
  churn this feature does not need.
- Class (d) can deny a tool that a later agy version adds and that is harmless. That fails toward
  refusal, by design.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| Four optional fields in `h_mad_state_schema.json`; rows in `state-schema.md`; `fallback_agent` description corrected in both | schema | FR-1, FR-3 |
| Resolution function in `h_mad_tdd_judge.py` | module | FR-2 |
| `h_mad_tdd_judge.py implementer --root --feature [--record]` printing `TDD-IMPLEMENTER:` | CLI verb | FR-2 |
| Extended `TDD-STATE:` line and its `STATE_ACTIVE_RE` (shape per DO-1) | contract | FR-3 |
| `h-mad-tdd-gate.sh` peer refusals `implementer-invalid` / `agy-authorship`, fold re-gated on both peers out | hook | FR-3 |
| Shared shell-policy module, imported by both gates | module | FR-6 |
| `h-mad/hooks/h-mad-agy-tdd-gate.py` with `--self-check` | hook | FR-4, FR-6 |
| Wiring check printing `AGY-GATE:` (preferably by extending `h_mad_hook_wiring.py`) | CLI | FR-5 |
| `h_mad_assemble_tdd.py --agent agy`: `choices` gains `agy`, runs the wiring check, `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified`, provisional 1500 s default | CLI flag | FR-5, FR-8 |
| A `review_independence` append path (DO-3) | CLI / procedure | FR-7 |
| `h_mad_phase7_preconditions.py` warnings `review_non_independent`, `review_independence_unrecorded`, `review_independence_malformed` | module | FR-7 |
| Tracked `.agents/hooks.json` in each adopting project, with this repository first | config | FR-5, D-2 |
| Implementer-neutral `codex-implementer-prompt.md` with the new-caller rule | prompt | FR-9 |
| SKILL.md, `agy-runtime.md`, `failure-recovery.md`, `state-schema.md` edits | docs | FR-9, FR-10 |
| `agy-runtime.md` hook-event claims re-checked against the installed agy | docs | spec §"Owed by other documents" |
| Probe directory `docs/03-analysis/probes/agy-coder-fallback/`: payload capture, real refusal, RED/GREEN with re-run, revert and mutation, each stamped with the sha and `agy --version`; derived timeout | probe | FR-8 |
| Mutation rows for every new guard, plus re-pointed existing rows (R-1, R-3) | tests | AC-X |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| **R-1 — mutation anchors on the state-line contract go stale.** Rows whose `find` **or** `replace` text quotes the state line, its regex or the fold's inputs stop applying when FR-3 rewrites them. A row that matches zero times leaves the guard intact and reads as caught-by-nothing (`step5e:mutation_unverified`). Census at `17d73037`, command below (M-3): **8 rows in 3 specs** (`claude_gate_judge_wiring.json` 5, `tdd_judge_chain.json` 2, `tdd_gate_fallback_agent.json` 1). More broadly, the files FR-3 rewrites carry 56 rows (`h-mad/hooks/h-mad-tdd-gate.sh`, 5 specs) and 36 rows (`h-mad/scripts/h_mad_tdd_judge.py`, 8 specs) (M-2). | H | The Task that changes the line re-anchors every row in the M-3 census in the **same commit**. Its GREEN runs `h_mad_mutation_harness.py` over every spec in M-2's list for the two files, and gates on `MUTATION: ALL_CAUGHT`, never `$?`. The census is re-derived after the design fixes DO-1, because the fix adds members to the class it counts. |
| **R-2 — the tracer needs the installed gate, and the installed path is main.** `~/.gemini/config/skills/h-mad` resolves to this repository's main checkout (DO-6). In a Phase-5 worktree the new gate does not exist at the installed path. So FR-5's check reads `UNWIRED` (`bad-command` or `self-check-failed`) and FR-8 cannot run before merge with the shipped wiring. | H | DO-6 makes the design pick one: run FR-8 after the merge to main as its own step, with the halt standing until then; or give the check an explicit, test-pinned override for a worktree path. A hand edit of the installed symlink is not an option, because the symlink also serves every live agy and Claude session (brainstorm risk "live symlink"). |
| **R-3 — moving the shell policy re-points the Codex gate's mutation rows.** At `17d73037`, 19 rows anchor inside the `_safe_shell_command` call closure (`codex_gate_judge_wiring.json` 17, `assemble_tdd_mutation_rows.json` 2; M-4), and their `file` is `h-mad/hooks/h-mad-codex-tdd-gate.py`. The spec's "its existing tests and mutation rows stay green" holds only if those rows are re-pointed to the new module. | M | Re-point them in the move Task. Re-derive M-4 over the set DO-5 fixes. AC-6.1's "one definition in the tree" is checked by a test that greps for a second `def` of each moved function. |
| **R-4 — old-shape stub lines vs AC-3.2's "unmodified".** See DO-1a. | M | The design resolves it, or the spec relaxes AC-3.2 (filed in §"Owed by other documents"). |
| **R-5 — `review_independence` append loses entries.** `--set` replaces the whole array (DO-3). | M | DO-3. The FR-7 fixtures include a two-entry record, and assert that both entries survive an append. |
| **R-6 — the FR-1 schema validates differently on the two validator paths.** | M | DO-4. AC-1.1 runs on both paths. |
| **R-7 — a deny does not bind under `--dangerously-skip-permissions`, or a sibling `ask` / `overwrite` changes the outcome.** | H | FR-8 step 2 runs through `hmad-dispatch exec agy` with the operator's real global `~/.gemini/config/hooks.json` loaded. At `17d73037` its `orca-status` `PreToolUse` `*` handler prints `{"decision":"ask"}` (`grep -n decision ~/.orca/agent-hooks/antigravity-hook.sh`). The halt stands until the step passes, and SKILL.md names "after any agy upgrade" as the re-run trigger (FR-5 residual). |
| **R-8 — doc-derived tests break on the doc edits.** `test_h_mad_tdd_gate_docs.py` reads `agy-runtime.md` §"The TDD gate", requires exactly one `Hook: ` line in the prompt, and anchors on a SKILL.md gate bullet. `test_h_mad_wiring_task_shape_docs.py` pins literals in the prompt and the halt tokens. At `17d73037`, 15 tracked test-side files name the prompt (M-5). | M | Run the full suite per Task, never a scoped selection: a scoped green misses a doc-derived test in another file. A FR-9/FR-10 Task's RED names which of these tests it expects to move. |
| **R-9 — the `agy-runtime.md` hook-event claim is stale on two surfaces, not one.** The spec names §"Hooks". The §"Construct mapping" `hook-event` row says the same thing ("there is no `SessionStart`"). Command at `17d73037`: `grep -n 'SessionStart' h-mad/references/agy-runtime.md` → 2 lines. Installed hooks.md lists it: `grep -c 'SessionStart' ~/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs/hooks.md` → 3 matching lines, agy `1.3.6`. | L | A Task re-checks both surfaces against the installed agy (by reading hooks.md and, if the claim matters to h-mad, by a live probe), and corrects both together. `grep -rn 'no .SessionStart' h-mad/tests` → no hits at `17d73037`, so no test pins the stale claim. |
| **R-10 — a stale suite floor lets a test be deleted while staying green.** | M | The floor is re-measured at the 5c baseline, not copied from here (M-1). |
| **R-11 — agy's writes land outside `--cd`** (brainstorm; seen for audit reports, J30). | M | FR-8 step 3 checks where files landed. The gate denies an out-of-root `.py`. |
| **R-12 — agy narrates work it did not do, or reports false counts.** | M | The tree delta, the independent re-run and the revert test are the evidence. The `STATUS:` line is a claim. |

## Convention Prerequisites

- **Phase 5 runs in a worktree** and merges when clean. `~/.claude/skills/h-mad` and
  `~/.gemini/config/skills/h-mad` both symlink into this checkout (`ls -la ~/.claude/skills/h-mad
  ~/.gemini/config/skills/h-mad` at `17d73037`), so an edit on main reaches every live session. See
  R-2 for the consequence this has for the tracer.
- **D-10, per clone.** Each clone and each project that adopts the agy gate needs `/.agents/skills/`
  in `.git/info/exclude`, **not** `/.agents/`. `.git/info/exclude` is local and unversioned. In
  this clone, at `17d73037`: `grep -n agents .git/info/exclude` → `/.agents/skills/`, and
  `git check-ignore -v .agents/hooks.json` prints nothing (not ignored). Linked worktrees share the
  main clone's `info/exclude`. Where the narrowing is missing, the file cannot be tracked without
  `git add -f`, and FR-5's check reads `UNWIRED reason=no-hooks-file` in a worktree that lacks
  it. That is a halt, not a silent pass.
- **Interpreter.** The h-mad suite runs under `/opt/anaconda3/bin/python3`. At `17d73037` the bare
  `python3` on `PATH` (Homebrew 3.15) has no `pytest`.
  Run measurement commands through `rtk proxy`. The rtk rewrite of a bare `pytest` printed
  `No tests collected` for a tree that collects thousands.
- **The full suite runs per Task, in the foreground.** Gate on the pytest summary line, never `$?`.

## Success Criteria

- Every AC in the spec passes as an automated test: AC-1.1, AC-2.1, AC-2.2, AC-3.1, AC-3.2,
  AC-4.1, AC-4.2, AC-5.1, AC-6.1, AC-7.1, AC-7.2, AC-8.1, AC-9.1 and AC-X.
- Every new guard has a mutation row that bites, and every re-anchored row in R-1 and R-3 still
  bites, each scored `MUTATION: ALL_CAUGHT`.
- **Suite floor.** No Task ends with fewer collected tests than the 5c baseline plus the tests that
  Task adds, and none fails. Reading at `17d73037` (M-1): 6042 tests collected. This number drifts
  by construction, since every Task adds tests. It is **not** the floor. The floor is the 5c
  reading.
- FR-8's probe exists. Its real refusal passed. The default `--agent agy` timeout in
  `h_mad_assemble_tdd.py` equals `max(900, 3 × slower turn)` rounded up to a multiple of 60, over
  the readings the probe names.
- No surface edited by this feature states the `review_independence_unrecorded` trigger as
  agy-only. Check: `git grep -n 'review_independence_unrecorded'` over the edited files, each hit
  read by hand.

### Measurements

Each is one reading at one sha. Where the number moves by construction, the re-measure point is
named. The committed probes for these belong under `docs/03-analysis/probes/agy-coder-fallback/`.
This plan does not write them.

- **M-1 — suite collection** (re-measure at 5c):
  `rtk proxy /opt/anaconda3/bin/python3 -m pytest h-mad/tests --collect-only -q -p no:cacheprovider | tail -1`
  → `6042 tests collected` at `17d73037`.
- **M-2 — mutation rows per file this feature edits** (re-measure after each Task that edits one):

  ```bash
  cd h-mad && python3 -c 'import json,subprocess,sys,collections as C
  c=C.Counter();s=C.defaultdict(set)
  for p in subprocess.check_output(["git","ls-files","tests/mutation-specs/*.json"],text=True).split():
   for r in json.load(open(p)).get("mutations",[]):
    f=r.get("file")
    if f in sys.argv[1:]: c[f]+=1; s[f].add(p)
  [print(f,c[f],len(s[f])) for f in sys.argv[1:]]' hooks/h-mad-tdd-gate.sh scripts/h_mad_tdd_judge.py hooks/h-mad-codex-tdd-gate.py scripts/h_mad_assemble_tdd.py scripts/h_mad_phase7_preconditions.py scripts/h_mad_hook_wiring.py
  ```

  At `17d73037` (rows, specs): `h-mad-tdd-gate.sh` 56, 5. `h_mad_tdd_judge.py` 36, 8.
  `h-mad-codex-tdd-gate.py` 62, 5. `h_mad_assemble_tdd.py` 60, 6.
  `h_mad_phase7_preconditions.py` 12, 2. `h_mad_hook_wiring.py` 10, 1.
- **M-3 — rows over the state-line contract** (re-derive after DO-1): the M-2 loop, restricted to
  rows whose `find` + `"\n"` + `replace` matches
  `TDD-STATE:|STATE_ACTIVE_RE|codex-escape|ESCAPE_STATUSES|command -v codex|HMAD_CODEX_UNAVAILABLE`
  (Python `re.search`). At `17d73037`: 8 rows, 3 specs. The pattern is a proxy for "quotes the
  contract", so its residual is any row that anchors on the fold through a different literal. The
  re-anchoring Task reads every row whose `file` is one of the two FR-3 files, not just these 8.
- **M-4 — Codex-gate rows inside the shell-policy closure** (re-derive over DO-5's set): parse
  `h-mad/hooks/h-mad-codex-tdd-gate.py` with `ast`. Take the transitive closure of module-level functions
  called by name from `_safe_shell_command`. Count the rows (`file` = that hook) whose `find` text
  starts inside one of those functions' `lineno..end_lineno` spans. At `17d73037`: 10 functions,
  19 rows (17 in `codex_gate_judge_wiring.json`, 2 in `assemble_tdd_mutation_rows.json`), and 0
  rows whose `find` text is absent from the file.
- **M-5 — test-side files naming the prompt:**
  `git ls-files -z h-mad/tests | xargs -0 grep -l 'codex-implementer-prompt' | wc -l` → 15 files at
  `17d73037`.

## Out-of-Scope (confirmed from spec)

- Per-task implementer selection. It can come later on the same field.
- Refusing a peer's production write in that peer's own gate when the other peer is the resolved
  implementer, for example a Codex verifier dispatch writing production code under
  `implementer=agy`. Residual: the test-first judge still applies, and the per-dispatch
  `git status --short` diff shows it.
- A write-time gate for grok, and authorship rules for agy as the orchestrating host.
- Routing audit legs by `agy_status`.
- A liveness probe for either peer (D-5).
- A project-level default implementer (D-6).

## Owed by other documents

None of these are edited by this plan.

- **Spec, AC-3.2 vs FR-3.** The existing `test_h_mad_tdd_gate_*.py` stub fixtures carry the old
  `TDD-STATE:` shape (DO-1a). If the design cannot keep them passing unmodified, AC-3.2 needs a
  stated exception for stub-line fixtures. Separately, `test_h_mad_tdd_judge.py` `ACTIVE_RE` will
  change with the line. AC-3.2 does not cover that file, and no AC says it must.
- **Spec, FR-7 "appends … with `h_mad_state_write.py`".** The writer has no append (DO-3).
- **Spec, FR-6 "its existing … mutation rows stay green".** This holds only with the rows
  re-pointed to the shared module (R-3).
- **Spec, FR-9 / AC-9.1 surface list.** It omits the `failure-recovery.md` recovery row for
  `step5d:red_wrong_reason:<module>` (the halt-surface census).
- **Spec, FR-1 / FR-10.** They omit the `fallback_agent` description in `h_mad_state_schema.json`
  and in `state-schema.md`, which becomes false under FR-3 (Implementation Strategy, stage 1).
- **Spec §"Owed by other documents".** The stale `SessionStart` claim is on two `agy-runtime.md`
  surfaces, not one (R-9).
- **Design.** DO-1 through DO-6.

## Next Steps

The operator reviews and approves v1.0. The Phase-3 audit cycle then runs on two surfaces, and
revisions go back to `plan-author`. The design obligations DO-1..DO-6 and the owed spec items are
inputs to Phase 4.

## Version History
- v1.0: Initial plan (2026-10-16) from spec v1.2 at 17d73037. Carries D-9/D-11 for every implementer, D-10 per-clone prerequisite, design obligations DO-1..DO-6 (state-line shape and its literals, read-only allowlist, review_independence append, schema constructs on both validator paths, shell-policy module boundary, installed-path vs worktree), mutation re-anchoring risks R-1/R-3, and six items owed by the spec.
