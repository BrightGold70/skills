# Plan: agy-coder-fallback

> **Slug note.** The slug predates brainstorm v1.1. agy is a **peer** Phase-5 implementer with
> Codex's standing, not a fallback (spec §"Slug note").

Source: `docs/01-plan/features/agy-coder-fallback.spec.md` v1.4, read at commit `e6610381` (v1.2 of
this plan; v1.1 read spec v1.3 at `e7730f78`).
Every "currently" claim below was read from the tree at `17d73037`, and the command that read it is
written beside it. Those readings still hold at `e7730f78` for every `h-mad/` file:
`git diff --stat 17d73037 e7730f78 -- h-mad` prints nothing. Claims first added in v1.1 are stamped
`e7730f78`. Claims first added in v1.2 are stamped `d90decc6`, and the older readings still hold
there for every `h-mad/` file: `git diff --stat 17d73037 d90decc6 -- h-mad` prints nothing.
v1.5 read spec v1.6 at `c853b207` and design v1.0 at `df46f72a`; its new readings are stamped
`200ffd52`, and `git diff --stat 29ae3e7b 200ffd52 -- h-mad` prints nothing. v1.6 mirrors spec
v1.7 at `c117a695` (D-12, D-13, D-14); `git diff --stat 200ffd52 c117a695 -- h-mad` prints nothing.
Commands run from the repository root unless they start with `cd`.

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
made visible. agy is already installed and already dispatched headless by
`hmad-dispatch exec agy` for review legs. `agy --version` → `1.4.0` at `200ffd52` (it read
`1.3.6` at `17d73037`). This reading moves with every agy upgrade, so FR-8 and the `SessionStart`
re-check stamp the version they ran against rather than citing this one.

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

This plan satisfies FR-1 through FR-10 of the spec, with the 21 acceptance criteria AC-1.1, AC-1.2,
AC-2.1, AC-2.2, AC-3.1, AC-3.2, AC-4.1, AC-4.2, AC-5.1, AC-5.2, AC-6.1, AC-7.1, AC-7.2, AC-8.1,
AC-8.2, AC-9.1, AC-9.2, AC-9.3 and AC-9.4, plus AC-X (`python3 h-mad/scripts/h_mad_ac_census.py
docs/01-plan/features/agy-coder-fallback.spec.md` → `ACS: OK count=19 frs=9` at `e8def13f`, spec v1.5, and the same at `c117a695`, spec v1.7). The
decisions D-1..D-14 are inputs, not open questions. Spec v1.7 (`c117a695`) adds three, each
mirrored where it binds:

- **D-12.** The FR-6 policy moves into the existing `h-mad/scripts/h_mad_target_identity.py`, not
  a new module (was the design's OQ-A). Stage 4, DO-5.
- **D-13.** FR-8 is a post-merge stage after Phase 7's integrate, and the feature is recorded
  COMPLETE only after it passes, with AC-8.1 and AC-8.2 (was the design's OQ-B). Stage 8, DO-6, R-2.
- **D-14.** `implementer_switch.ts` is narrowed to seconds `00`–`59`; a leap second is refused on
  both validator paths, because h-mad's writer produces `.ts` through Python `datetime`, which
  cannot hold second 60. Stage 1.

Two of the earlier decisions must be carried exactly as the spec states them, because the
brainstorm's framing was narrower:

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
   the field is read only when **both** peers are out. Spec v1.3 FR-1 now lists both surfaces.
   The schema description is pinned:
   `h-mad/tests/test_h_mad_state_fallback_agent.py` `test_fallback_agent_description_states_the_four_facts`
   asserts four substrings, `read only when codex is out`, `are equivalent`,
   `HMAD_CODEX_UNAVAILABLE does not override` and `prose-enforced`
   (`grep -n -A 14 'def test_fallback_agent_description_states_the_four_facts' h-mad/tests/test_h_mad_state_fallback_agent.py`
   at `e7730f78`). The rewrite keeps all four, or changes that test to the new fact in the same
   commit. The test is never deleted. The Task's RED names which of the two it does.
   - **The `codex_status` description and row are rewritten too (spec v1.7 FR-1, AC-1.1), on
     both surfaces.** The schema `description` says `exhausted`/`unavailable` records that Codex
     cannot author, "permitting Claude to write the fallback", and the `state-schema.md` row says
     "An unavailable or exhausted status permits a Phase-5 authoring fallback" (at `c117a695`,
     `grep -c 'permitting Claude to write the fallback' h-mad/scripts/h_mad_state_schema.json` → 1
     line and `grep -c 'permits a Phase-5 authoring fallback' h-mad/references/state-schema.md` → 1
     line). Both are false once agy is available. The rewrite states authorship as FR-2's
     resolution, Claude only when `resolved` = `claude`, and leaves the audit-routing half
     unchanged. The Task's RED pins one sentence on each surface. No test pins the old text today:
     `git ls-files -z h-mad/tests | xargs -0 grep -l 'permitting Claude to write the fallback\|permits a Phase-5 authoring fallback\|One switch, both effects\|blocked when Codex is available' | wc -l`
     → 0 files at `c117a695`. That zero is load-bearing only for this rewrite, so the Task re-runs
     the grep. `test_fallback_agent_description_states_the_four_facts` pins property ORDER
     (`fallback_agent` directly after `codex_status`), so the FR-1 fields are never inserted
     between the two.
   - **AC-1.2's leap-second fixture (D-14).** `implementer_switch.ts` = `2016-12-31T23:59:60Z` is
     its own fixture, refused on the library path and, under the existing seam that forces the
     bundled validator, on the bundled path, one run per path. The writer's form
     `%Y-%m-%dT%H:%M:%SZ` is accepted on both. The narrowing refuses nothing the writer can
     produce: `/opt/anaconda3/bin/python3 -I -c 'from datetime import datetime; datetime.fromisoformat("2016-12-31T23:59:60+00:00")'`
     raises `ValueError: second must be in 0..59` at `c117a695`.
2. **Resolution function and the `implementer` verb (FR-2).** The env-var and `PATH` evaluation
   moves out of the hook into the judge. The `--record` write goes through
   `h_mad_state_write.py`'s write path.
3. **Claude-side gate on the new state line (FR-3).** This rewrites the hook's state parse and
   fold, which is where the existing mutation anchors sit (see §"Risks"). The same Task applies
   the AC-3.2 exception (DO-1a): it re-shapes the stub literals in the two named gate test files,
   updates `test_h_mad_tdd_judge.py` `ACTIVE_RE`, and adds the fixture showing that a
   today-shape line refuses `judge-error`. The new line must also satisfy the placement
   invariants P-1..P-5 in DO-1a. Those are assertions on the judge's **real** output, not on stubs,
   so re-shaping a stub cannot satisfy them. The Task's RED names each one it expects to hold.
4. **Shared shell-policy module (FR-6).** This is a pure move out of
   `h-mad/hooks/h-mad-codex-tdd-gate.py`. The destination is `h-mad/scripts/h_mad_target_identity.py`,
   not a new module: D-12, the operator decision on the design's OQ-A (design v1.0 §"FR-6"), because a new module the gate
   imports breaks a hand-built test tree that FR-6 says passes unmodified. Codex-gate behaviour does not change. Every moved name
   that an existing test reaches stays bound on the Codex gate module, by import.
   `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py` calls `module._safe_shell_command` at 2 sites
   (`grep -n '_safe_shell_command' h-mad/tests/test_h_mad_codex_tdd_gate_judge.py` → 2 matching
   lines at `e7730f78`). The mutation rows in the moved code (M-4) are re-pointed to the new
   module in the same Task. Then each spec that holds one is gated on `MUTATION: ALL_CAUGHT`.
5. **agy gate (FR-4), then its wiring check and assembler enforcement (FR-5).** The gate imports
   the module from stage 4 and the judge from stage 2. **Exit codes follow the audit-gate signal
   discipline** (`h-mad/invariants.base.md` §"Audit-gate signal discipline": a normal verdict,
   PASS or FAIL, prints its token and exits 0; nonzero only for an operational error). Spec v1.4
   FR-5's exit-code table is the contract, and this plan mirrors it without restating the table:
   - **Verdicts exit 0.** `AGY-GATE: WIRED` and every `AGY-GATE: UNWIRED reason=…` (all seven
     reasons, `no-hooks-file` and `self-check-failed` included) exit 0 from the check. The
     assembler's `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified` on `UNWIRED` writes no prompt and
     exits 0.
   - **Operational errors exit 2.** `AGY-GATE: UNREADABLE` exits 1 from the check, and the
     assembler HALT exits 2. A check that prints no `AGY-GATE:` token gives
     `ASSEMBLE-TDD: HALT agy_tdd_hook_unverified check=no-token` with exit 2.
   - The orchestrator halts `step5:agy_tdd_hook_unverified` in every non-`WIRED` row. Callers
     read the token, never `$?`.
   - **Precedent and divergence.** `h_mad_hook_wiring.py` returns 0 on `WIRING: FAIL` and 2 on
     `WIRING: UNKNOWN reason=no_settings`
     (`grep -n 'return [02]' h-mad/scripts/h_mad_hook_wiring.py` at `d90decc6`). The agy check
     treats a missing `hooks.json` as a verdict instead, deliberately, per spec v1.4 FR-5.
   - **The assembler then carries two conventions.** Its module docstring says
     `exit 0 on PASS, 2 on any HALT`
     (`grep -n '2 on any HALT' h-mad/scripts/h_mad_assemble_tdd.py` at `d90decc6`), and its
     existing HALTs keep exit 2 (spec v1.4 FR-5 residual). The FR-5 Task rewrites that docstring
     in `h_mad_assemble_tdd.py`, in the same commit, to say which HALT exits which way. A
     grep-able sentence pins the rewrite, so a stale "2 on any HALT" fails a test.
   - **AC-5.2:** each table row gets its own fixture, which asserts the stdout token and the exit
     code **separately**. A mutation that returns 2 on `UNWIRED` must be killed
     (`MUTATION: ALL_CAUGHT`).
6. **Prompt and doc surfaces (FR-9, FR-10)**, including the WIRE-PIN new-caller rule on every
   surface that states the halt (see §"Architecture Considerations", the halt-surface census).
   That covers the `h-mad/references/failure-recovery.md` 5d row, whose token stays unchanged.
   It also covers the wiring-task header that `h-mad/scripts/h_mad_assemble_tdd.py` `assemble()`
   emits under `if shape == "wiring":`. That header is written as adjacent Python string literals
   split between `never a missing ` and `symbol.`, and the carve-out is appended after the
   existing sentence, so the literal `never a missing` stays. Three tests pin literals on these
   surfaces, and the edit keeps all three green:
   - `h-mad/tests/test_h_mad_agent_definitions.py` `test_implementer_scopes_the_import_error_red_rule_to_wiring_tasks`
     pins the sentences of RED item 1;
   - `h-mad/tests/test_h_mad_wiring_task_shape_docs.py` `HALT_TOKENS` pins the token;
   - `h-mad/tests/test_h_mad_assemble_tdd.py` `TestWiringShape.test_the_pin_is_told_what_its_red_must_be`
     pins `never a missing` in the assembled prompt
     (`git ls-files h-mad | xargs grep -ln 'never a missing'` at `9c3b799d` → 2 files, the
     assembler and this test).

   **The copies of the carve-out bind to one authority (AC-9.4, DO-7).** Spec FR-9 requires the
   carve-out worded identically on every surface: five surfaces today plus the prompt's GREEN
   variant, six copies in all. A presence pin per surface does not show that the copies agree, so
   one copy could keep a broader or narrower exception while the corpus passes. AC-9.4 offers two
   mechanisms, a shared source or an equality test, and asks the plan to name one. **The plan
   names the equality test.** The six copies sit in four files, in four markdown shapes and one
   Python form: an ordered-list item (prompt RED item 1), two plain paragraphs (the prompt's
   ``**If the dispatch carries a `WIRE:` `` paragraph and its `For GREEN phase (5e):` paragraph), a
   bullet item (the SKILL.md 5d bullet), a table cell (the `failure-recovery.md` 5d row), and
   adjacent Python string literals (the `assemble()` wiring header). A shared source would mean
   generating or templating those files, and that is restructuring this feature does not
   otherwise need. The stage ships a doc-derived equivalence test. It holds the **canonical
   carve-out block** once: all three sentences of spec FR-9's quoted block (the `**only**` when
   sentence, `The RED report must name both.`, and the wire-cut sentence). It asserts that each
   of the six copies carries that block verbatim. Hard-wrapped markdown is compared after
   collapsing whitespace runs to one space.
   **Each copy is read from its own source location, never from a text that holds more than one
   copy.** Three of the copies share `codex-implementer-prompt.md`, and the assembled wiring
   prompt is that whole template with its slots filled, so it holds four copies. A contains-check
   over either text passes while one copy is sick, because the healthy copies satisfy it. So each
   template copy is located individually, and the assembler copy is read from its own joined
   `str` constant in `assemble()`. The locators are a design obligation (DO-7). Whatever they
   are, they must make a mutation of any single copy fail the test.
   **Control:** six mutation rows, one per copy, each changing only that one copy. Each row is run
   alone and must fail the equivalence test, scored `MUTATION: ALL_CAUGHT`. A row that mutates
   two copies at once does not count, because a healthy copy can mask a sick one. The harness
   (`h-mad/scripts/h_mad_mutation_harness.py` `anchor_status`) refuses a `find` that does not
   occur exactly once in its file. The carve-out text will occur three times in the prompt and
   is worded identically, so a row's `find` cannot be the carve-out text alone. Each row's `find`
   includes surrounding context that is unique in its file (for example the `1. For each FAILING
   test` prefix, or the `For GREEN phase (5e):` prefix). The `.py` row's `find` is written
   against the source bytes, including any split between adjacent literals.

   **The teammate-audit authorship bullet (FR-10).** SKILL.md §"Teammate audit leg — when codex
   is unavailable", sub-section `### What this leg does NOT license`, holds the bullet
   `- **It does not license Claude to write Phase 5 production code — but the declaration you just`
   `made does, and that is one switch with two effects.**` It says that declaring `codex_status`
   unavailable for a 5b audit licenses Claude to author 5d/5e. Under FR-2/FR-3 that is false when
   agy is available: the resolver picks agy and Claude's gate refuses `agy-authorship`. Stage 6
   rewrites the bullet so that it separates the two things. Audit-leg selection still follows
   `codex_status` (D-8, unchanged). Phase 5 authorship is whatever `h_mad_tdd_judge.py implementer`
   resolves. Per spec v1.5 FR-10, Claude may write Phase-5 production code only when FR-2's
   `resolved` is `claude` for every ACTIVE `step5` record on the chain: both peers unavailable,
   and `fallback_agent` absent, `null` or `claude`. The replaced condition is "the `codex_status`
   declaration licenses Claude", and the new one is "`resolved` = `claude`". The rewrite keeps the
   anchor prefix and the tokens `ACTIVE`, `every`, `unavailable` and `exhausted`. **The
   replacement condition is pinned:** the FR-10 doc-derived test asserts that the bullet names
   `h_mad_tdd_judge.py implementer` and `agy-authorship`. Baseline at `9c3b799d`: 0 and 0, from
   `/opt/anaconda3/bin/python3 -I -c 'import sys; t=open("h-mad/SKILL.md",encoding="utf-8").read(); a="- **It does not license Claude to write Phase 5 production code"; b=t.split(a,1)[1].split("\n\n",1)[0]; print(sum(n in b for n in sys.argv[1:]))' 'h_mad_tdd_judge.py implementer'`
   and the same command with `'agy-authorship'` as the last argument. The locator is the one
   `test_h_mad_tdd_gate_docs.py` `_skill_gate_bullet` already uses, and that test's anchor and
   tokens are kept (doc-pin census).

   The SKILL.md heading `### Codex authors Phase 5 — enforced, not just instructed` and the
   sentence `Phase 5 implementation is **Codex's job**` are also pinned, along with every other
   test literal inside a section this stage rewrites (R-8 holds the census). FR-10's rewrites are
   gated in §"Success Criteria".

   **FR-9 relaxes a guard, so the stage carries two verifications beyond its pins.** The carve-out
   makes 5d accept a RED it used to halt as `red_wrong_reason`. Pins and a green suite show that
   the rule's sentences are present. They do not show that the relaxation is only the intended
   case (`h-mad/invariants.base.md` §"Guard narrowing", §"Incident replay").
   - **Differential corpus, old rule against new (AC-9.2).** The corpus is fixture repositories
     with real pytest REDs. It holds the four cases spec v1.4 names: `new-caller` (the missing
     symbol is the caller the task creates, and the callee exists), `missing-callee`,
     `both-missing` and `unrelated-import` (for example a missing third-party module). The plan
     adds a fifth, `other-symbol`: a missing name that is neither the caller nor the callee, such
     as a typo in the test. It probes the same boundary from the side the four do not. For each
     case the corpus records the RED's exception line, whether the callee resolves at the RED
     base, and both verdicts. The set whose verdict changed must equal `{new-caller}` exactly.
     "The callee resolves at the RED base" is decided by **executing** an import of the callee
     at that base. It is never decided by parsing the traceback text, because the guard must rest
     on a guarantee of the thing it judges. Where the rule is applied is DO-7. The corpus and its
     verdicts are committed under `docs/03-analysis/probes/agy-coder-fallback/`.
   - **Incident replay (AC-9.3).** The rule is applied to the real REDs that motivated it:
     HemaSuite `notebooklm-integration-interface` T4 WIRE-PIN 1, T5 WIRE-PIN 1 and T6 WIRE-PIN 2
     (analysis F-3). Synthetic cases do not stand in for these. Reachable at HemaSuite
     `86c3d0c8d` (`git -C /Users/kimhawk/orca/HemaSuite rev-parse --short HEAD`):
     - the task commits `531a6296b` (Task 4), `7aa0d9dec` (Task 5) and `c2d671f6b` (Task 6)
       (`git -C /Users/kimhawk/orca/HemaSuite log -1 --format='%h %s' <sha>`);
     - `docs/archive/2026-10/notebooklm-integration-interface/notebooklm-integration-interface.analysis.md`
       (F-3);
     - the same directory's `notebooklm-integration-interface.impl-plan.md`, which holds the
       wire-cut rows M4.1 and M5.1 (`grep -n 'M4.1\|M5.1'` on that file);
     - the three pins, each under `hematology-paper-writer/tests/` at its task commit. Checked at
       HemaSuite `4d7a392c5` with `git show --stat --format= <sha>` and
       `git show <sha>:<file> | grep -n 'def <test>'`, and each commit is an ancestor of that HEAD
       (`git merge-base --is-ancestor <sha> HEAD`):
       - T4 WIRE-PIN 1: `test_notebooklm_resolver.py::test_resolver_calls_registry_arm_notebook_id_once`
         at `531a6296b`;
       - T5 WIRE-PIN 1: `test_notebooklm_initialize.py::test_initialize_entry_point_resolves_through_registry_arm`
         at `7aa0d9dec`;
       - T6 WIRE-PIN 2: `test_notebooklm_status_report.py::test_status_entry_point_resolves_through_registry_arm`
         at `c2d671f6b`.

     **Which form of each pin is replayed.** T4's committed pin uses two-argument
     `getattr(integration, "resolve_registry_notebook")`, so its RED at the parent is the
     missing caller. T5 and T6 do not. Their committed pins carry the impl-plan's WIRE-PIN RED
     scaffold, a three-argument `getattr(..., None)` inside `except (Exception, SystemExit)`
     followed by a spy assertion. Their committed RED is therefore an `AssertionError`, which the
     old rule already accepts, so replaying them verbatim cannot show an old verdict of halt. For
     T5 and T6 the replay evaluates the **direct-call form**: the scaffold is replaced by a
     two-argument `getattr` on the same name (or a direct call), the `try`/`except` is removed,
     and the spy assertion is unchanged. That form's RED is the missing caller. Each caller is
     absent at its parent and present at its task commit. At HemaSuite `4d7a392c5`, counting
     `git grep -n "def <caller>" <rev> -- hematology-paper-writer/tools` matching lines gives
     parent 0 and task commit 1 for each of `resolve_registry_notebook`,
     `initialize_project_notebook` and `generate_setup_report`.

     Each RED is reproduced at its task commit's parent, in a scratch worktree or a `git archive`
     export. The live HemaSuite clone is never checked out. For each case the probe holds the
     direct-call form's RED, the old verdict on it (halt), the new verdict on it (valid), a
     wire-cut re-run at the task commit with the committed pin, in which the pin fails, and a
     citation of the original evidence (M4.1, M5.1, the WIRE 2 revert). For T5 and T6 it also
     records the committed scaffolded pin's own RED (`AssertionError`) and the old verdict on it
     (valid). It is stamped with both repositories' shas. A case that cannot be reproduced is
     recorded with its failing command and counted. It is never dropped, and it does not satisfy
     AC-9.3.
7. **Review-independence warnings (FR-7)** in `h-mad/scripts/h_mad_phase7_preconditions.py`. The
   same stage builds the add mechanism the design chooses under DO-3. The spec's requirement is
   that an add never removes or alters an earlier entry, is validated against FR-1 first, and
   leaves the store unchanged when refused. A read-modify-write must also state how it detects an
   entry lost between the read and the write. The stage also writes the SKILL.md text that tells
   the orchestrator to add an entry after each leg, for every implementer.
   - **Attribution (spec v1.7 FR-7).** An entry's `implementer` is the agent whose successful
     implementation dispatch produced the code the leg reviews, read from that dispatch. It is
     never read from `implementer_switch.to` or from the `implementer` field, which record
     routing, not authorship. Where code came from more than one agent's dispatch, `independent`
     is `false` if the reviewer is any of them. The stage carries a fixture for the case the rule
     exists for: a record whose stored `implementer_switch.to` is `agy` (Codex was out, then came
     back and was dispatched with `switch=none`), with the reviewed code from a Codex
     implementation dispatch. The attributed `implementer` is `codex`, and a Codex reviewer gets
     `independent=false`, so `review_non_independent` fires. The fixture's RED fails against an
     attribution read from `implementer_switch.to`. That attribution reports agy, and the Codex
     reviewer would then pass as independent.
8. **Live tracer (FR-8)**, which also replaces the provisional timeout. It runs last because it
   needs the gate **installed**, and that interacts with the worktree (see §"Risks", R-2).
   **D-13:** the stage runs after Phase 7's integrate, against the gate installed from main. The
   feature is recorded COMPLETE only after the stage passes, AC-8.1 and AC-8.2 included. Until
   then `step5:agy_tdd_hook_unverified` stands. **Every reading stamps the sha and
   `agy --version`** (`1.4.0` at `200ffd52`; spec v1.7 FR-8 "Version"). A reading taken under a
   different agy version from the gate's other readings is taken again, never carried over.
   **Handler timeout is a separate case: spec v1.4 FR-8 step 2a, AC-8.2.** When the gate answers a
   forbidden-write request in time, the write is denied and no handler times out. So step 2
   cannot settle the timeout path. Step 2a covers it:
   - **The delay hook.** A temporary handler goes in the project's own `.agents/hooks.json`
     (`PreToolUse`, matcher `*`), with `"timeout"` set to T. It sleeps for at least 2T, then
     prints a `deny`. It is never put in the global `~/.gemini/config/hooks.json`, which serves
     every live session. The real gate is never slowed.
   - **The dispatch.** It goes through the same `hmad-dispatch exec agy` transport. agy is told to
     write one named non-test file.
   - **Three readings, each observed independently:** whether the file exists afterwards; the wall
     time from the stream-json log; and agy's message.
   - **One outcome, from step 2a's table:** `timeout-blocks`, `timeout-allows`,
     `timeout-not-enforced` or `session-error`. A `session-error` is re-run and never counts as a
     pass.
   - **Clean-up.** The delay hook is deleted after use. The probe records the deletion, and
     records that `.agents/hooks.json` is byte-identical to its pre-probe content. Capture that
     content before the edit and compare it after: `shasum -a 256 .agents/hooks.json` both times.
   - **`timeout-allows` means agy fails open.** Then `agy-runtime.md` §"The TDD gate" carries the
     fail-open residual, and the operator question is raised before the gate is called verified
     (R-13).
   - Until an outcome is recorded, no document this feature writes describes agy's
     handler-timeout behaviour as settled.

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
  The design must also say what happens to every **existing literal of the line** in the tree,
  and its shape must satisfy the placement invariants P-1..P-5 (see DO-1a).
- **DO-1a — the line's existing literals.** The line is a contract with copies outside the judge
  and the hook. Command and reading at `17d73037`:
  `git ls-files -z h-mad | xargs -0 grep -l 'TDD-STATE: active'` → **6 files**:
  `h-mad/hooks/h-mad-tdd-gate.sh`, `h-mad/scripts/h_mad_tdd_judge.py`,
  `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json`, `h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py`,
  `h-mad/tests/test_h_mad_tdd_gate_judge.py` and `h-mad/tests/test_h_mad_tdd_judge.py`. The same
  reading holds at `d90decc6`. `test_h_mad_tdd_gate_judge.py` `_tree_b` stubs the judge's `state`
  verb with an old-shape line as its default. `test_h_mad_tdd_gate_fallback_agent.py` builds stub
  lines from `PREFIX`, **and** it asserts on the judge's real output (P-1, P-2).
  `test_h_mad_tdd_judge.py` pins the line through `ACTIVE_RE`, which is anchored with `$`, and
  through four more assertions (P-3..P-5). v1.1 said the second file held only stubs and that
  `ACTIVE_RE` was the third file's only pin. Both statements were false.

  **Placement invariants — design constraints on the new line.** Each is an assertion on
  `judge.format_state_line(...)` itself. Located by test name at `d90decc6`
  (`grep -n 'def test_format_state_line_emits\|def test_fold_outcome_round_trips\|def test_fallback_tag\|def test_state_line_escape_and_blocker\|def test_state_line_empty_values\|def test_state_line_path_with_space' h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py h-mad/tests/test_h_mad_tdd_judge.py`):
  - **P-1** (`test_h_mad_tdd_gate_fallback_agent.py` `test_format_state_line_emits_the_fallback_fold`,
    under AC-3.2's byte-identical rule). The line contains ` records=1 fallback=grok:1 record=`,
    so `records=`, `fallback=` and the first ` record=` stay adjacent. The test runs in-process
    with the **ambient** `PATH`, and `agy` is on `PATH` on this machine. So the `fallback=` value
    stays the fold over the records alone. The both-peers-out gating of FR-3 step 3 is applied
    by the hook, from other fields, and is never folded into this value. A
    `grok_wire_reverts.json` mutation row names this test as its `test`.
  - **P-2** (same file, `test_fold_outcome_round_trips_through_the_gate_ere`, byte-identical).
    The hook keeps exactly one line matching `^STATE_ACTIVE_RE='(.*)'$`. Python `re.fullmatch` of
    that literal accepts the judge's line, and `group(4)` equals the fold. The hook matches with
    bash `[[ =~ ]]`, which is POSIX ERE, and ERE has no non-capturing group: at `d90decc6`,
    `bash -c 're="^a(?:b|c)$"; [[ ac =~ $re ]]; echo $?'` prints `2`. So no parenthesised
    group may come before the `fallback=` group, and the literal must mean the same thing to
    Python `re` and to ERE.
  - **P-3** (`test_h_mad_tdd_judge.py` `test_fallback_tag`). The line's last comma-separated token
    is the last record's fallback tag (`line.rsplit(",", 1)[1] == wire`). Nothing may follow it.
  - **P-4** (`test_h_mad_tdd_judge.py` `test_state_line_escape_and_blocker`). The line contains
    `codex-escape=E blocker=B records=N` contiguously. Two `tdd_judge_chain.json` rows name this
    test as their `test`.
  - **P-5** (`test_h_mad_tdd_judge.py` `test_state_line_empty_values_encode_as_percent` and
    `test_state_line_path_with_space_decodes`). After the first ` record=`, comma fields 0, 1 and 2
    are the key, the `codex_status` and the state file. The hook reads the same positions: the key
    by `%%,*`, the file as the third field, and the tag by `##*,`
    (`grep -n 'BLOCKER_RECORD%%\|FALLBACK_RECORD##' h-mad/hooks/h-mad-tdd-gate.sh`).

  **What the invariants leave open.** This was probed at `d90decc6` with a scratch script, since
  deleted, that built one candidate line per placement and checked P-1..P-5 against it:
  - A **per-record field between the state file and the trailing fallback tag** satisfies all
    five, with a capture group of its own.
  - A **header field before `codex-escape=`** satisfies all five only without a capture group
    (a bracket expression, for example). With one, it fails P-2.
  - A **header field between `fallback=<fold>` and the first ` record=`** fails P-1.
  - A **field after the last record** fails P-3.

  Spec v1.4 FR-3 lists the same six tests as placement constraints. Its AC-3.2 now covers
  `test_h_mad_tdd_judge.py` too: `ACTIVE_RE` is the only literal there that may change, and the
  real-line assertions stay byte-identical, checked by the same diff against `a8d9ba99`. So all
  five invariants are binding, and the design chooses a shape that keeps all five. The free slot is
  per-record, between the state file and the trailing fallback tag. **Do not place a header field
  after `fallback=<fold>`**, the position plan audit v1 p2 suggested, because it breaks P-1. If
  a design finds that no shape satisfies P-1..P-5 together with FR-3's needs, that is a
  contradiction it reports, never a licence to edit an assertion.
  Residual: these are the assertions found by test name. A test that reads the line through a
  helper with another name is not covered until this census is re-run:
  `git ls-files -z h-mad | xargs -0 grep -l -e 'codex-escape=' -e ' record=' -e 'STATE_ACTIVE_RE' -e 'format_state_line'`.
  At `d90decc6` that prints 7 files: the DO-1a six, plus
  `h-mad/tests/mutation-specs/grok_wire_reverts.json`, which names P-1's test as a row `test`.
  **Settled by spec v1.3.** A line that lacks a field FR-3 steps 1 or 2 need refuses
  `judge-error`, so a line in today's shape refuses. The design may not keep old-shape stub lines
  passing by making the new fields optional, because that fails open. AC-3.2's exception applies
  instead. In the two gate test files, the string literals that stub a `TDD-STATE: active` line,
  and the constants they are composed from, are re-shaped to the new line. Every assertion,
  expected kind, reason substring, test name and parametrisation id stays byte-identical, checked
  by diffing each file against `a8d9ba99`. `test_h_mad_tdd_judge.py` `ACTIVE_RE` and the M-3 rows
  follow the line outside AC-3.2. The design owes one thing here: it reports any gate test whose
  asserted outcome no new-shape stub can reach. Such a test is a contradiction to report. It is
  never a licence to change the assertion.
- **DO-2 — the read-only allowlist (FR-4 class a).** The design fixes the exact list. Anything not
  on it falls to class (d) and is denied. The list is a closed set over an open inventory, so
  the design must name the inventory it was checked against (the `init.tools` array in
  `docs/03-analysis/probes/multi-host-runtime/rehearsal/live-agy-2026-10-01.log`). v1.4 also asked
  for "that log's agy version", which cannot be met: the log records none. Its first JSON line
  with a top-level `init` key carries an `init` object holding only `cwd`, `permission_mode` and
  `tools` (parsed at `200ffd52`), and `grep -ci 'version' <log>` matches 2 lines, both inside
  `version-history` file and feature names. So the obligation is restated: the design names the
  log and says it carries no version, and the class-(a) list is re-checked against an `init.tools`
  inventory re-captured together with `agy --version`. Design v1.0 assigns that re-capture to
  FR-8 step 1 (§"FR-8").
- **DO-3 — how a `review_independence` entry is added (FR-7).** The writer has no append
  operation. Its `--set KEY=VALUE` replaces the whole value, and `_parse_value` JSON-decodes it
  (`grep -n 'add_argument\|def _parse_value' h-mad/scripts/h_mad_state_write.py`). Spec v1.3 FR-7
  now states this and leaves the mechanism to the design, under one requirement. An add never
  removes or alters an existing entry. It is validated against FR-1 before anything is written. A
  refused add leaves the store unchanged and prints the writer's existing refusal. The spec
  prefers a writer operation that appends one entry under the claim/session rules. A
  read-modify-write procedure is acceptable only if it states how it detects an entry lost
  between the read and the write. Either way, the design names the mechanism. The spec's stated
  residual stands: a missing 5e entry has no warning of its own.
- **DO-4 — schema constructs.** Without `jsonschema` installed, `h_mad_state_validate.py` falls
  back to a bundled validator. That validator supports only `type`, `enum`, `required`,
  `properties`, `additionalProperties`, `items`, `minimum`, `maximum` and `minLength`, and it
  **ignores** any other keyword (`grep -n 'Deliberately supports ONLY' -A 4
  h-mad/scripts/h_mad_state_validate.py`). If the FR-1 schema used `oneOf`, `anyOf` or `const`,
  it would reject on one validator path and accept on the other. AC-1.1's reject cases must run
  on **both** paths, using the existing test seam that forces the bundled path.
  - **`format` is enforced on neither path.** v1.1 grouped `format` with the keywords the library
    enforces. That was false. `Draft7Validator` is built without a format checker, so `format` is
    an annotation there too. Reading at `d90decc6`:
    `rtk proxy /opt/anaconda3/bin/python3 -B -c 'import sys;sys.path.insert(0,"h-mad/scripts");import h_mad_state_validate as v;from jsonschema import Draft7Validator; s={"type":"string","format":"date-time"}; x="not-a-date";print("Draft7Validator:",Draft7Validator(s).is_valid(x)); print("bundled:",v._MiniDraft7(s).is_valid(x))'`
    prints `Draft7Validator: True` and `bundled: True`. Declaring `"format": "date-time"` on
    `implementer_switch.ts` therefore refuses nothing.
  - **The enforcement mechanism is a design obligation** (spec v1.4 FR-1, AC-1.2). The design
    picks one of three and cites the probe output: extend `_MiniDraft7` and its differential
    corpus; pass a format checker on the library path and match it in the bundled one; or check
    on the writer side before validation. Under AC-1.2, `not-a-date`, `2026-10-16` and
    `2026-02-30T00:00:00Z` are each refused on both paths, one fixture per value per path, and
    the writer's own form `%Y-%m-%dT%H:%M:%SZ` is accepted on both.
  - **Hazard.** `jsonschema` checks `date-time` only when the optional `rfc3339-validator`
    package imports. Without it, the value passes silently. A mechanism that uses the library's
    format checker therefore carries AC-1.2's package-absent fixture: `rfc3339_validator` made
    unimportable, and `not-a-date` still refused.
  - **A schema-wide mechanism has blast radius.** Three existing fields already declare
    `"format": "date-time"` (`grep -n -B3 '"format"' h-mad/scripts/h_mad_state_schema.json` → 3
    matching lines at `d90decc6`: `started_ts`, `owner_heartbeat_ts`, `halt_ts`). A mechanism
    that enforces `format` schema-wide starts refusing invalid values there too. The design then
    runs `classify_store` (`h_mad_state_validate.py`) over the live state files and reports every record that changes class
    before the mechanism ships.
- **DO-5 — the shared shell-policy module's boundary (FR-6).** The policy is more than
  `_safe_shell_command`. Its module-level call closure in `h-mad/hooks/h-mad-codex-tdd-gate.py` holds
  10 functions at `17d73037` (command below), and that closure includes `_load_judge`. The
  operator allowance (`_shell_allowance`, `SHELL_ALLOW_FILE`) sits outside it. The design names
  the exact set it moves, and the mutation-row census (R-3) is re-derived over that set. Every
  moved name that an existing test reaches stays bound on the Codex gate module, by import (spec
  v1.3 FR-6). The design names which names those are. The closure still holds those 10 functions
  at `200ffd52` (`h-mad/` is unchanged since `29ae3e7b`: `git diff --stat 29ae3e7b 200ffd52 -- h-mad`
  prints nothing). Design v1.0 fixes the set at 25 names, the closure plus 7 functions and 8
  constants, and places them in `h_mad_target_identity.py` (D-12, was OQ-A).
- **DO-6 — where the agy gate reads its installed path (FR-5).** The wiring command is
  `python3 ~/.gemini/config/skills/h-mad/hooks/h-mad-agy-tdd-gate.py`. On this machine that is a
  symlink into this repository's **main** checkout (`ls -la ~/.gemini/config/skills | grep h-mad`
  → `h-mad -> /Users/kimhawk/orca/skills/h-mad` at `17d73037`). The design must state how the FR-5
  check and the FR-8 tracer behave in a Phase-5 **worktree**, where the new gate exists only in the
  worktree (R-2). **Settled by D-13 (was OQ-B):** FR-8 runs as its own stage after the merge
  to main, and the feature is recorded COMPLETE only after that stage passes (design v1.0
  §"FR-8"). The worktree-override alternative is not taken.
- **DO-7 — where the FR-9 new-caller rule is applied.** No code applies the WIRE-PIN RED-reason
  rule today. The orchestrator applies it at 5d from SKILL.md prose, and the implementer reads it
  in the prompt. Reading at `d90decc6`:
  `git ls-files h-mad/scripts h-mad/hooks | xargs grep -ln 'red_wrong_reason'` → no files. The
  design states whether the carve-out stays prose-applied or gains a mechanical check, for
  example in `h_mad_wire_pin_gate.py`. Either way the stage-6 corpus runs against it. For prose,
  the corpus checks the rule's wording, not any one application of it, and the design states
  that residual. For code, the corpus becomes a test over that code, and the classifier gets a
  mutation row.
  **The copies bind to one authority.** The rule's six copies (the five surfaces of the FR-9
  census plus the prompt's GREEN variant) must not be able to diverge (AC-9.4). The plan names
  the mechanism, as AC-9.4 asks: a doc-derived equivalence test, not a shared source (stage 6
  gives the reason). The test holds the canonical carve-out block (all three sentences of spec
  FR-9's quoted block) once and asserts each copy carries it verbatim, with whitespace collapsed
  for hard-wrapped markdown. Each copy is read from its own source location: each template copy
  located individually, and the assembler copy from its joined `str` constant. The design owes
  those locators. What they must achieve: a mutation of any one copy makes the test fail, which
  no text holding two or more copies can give. The test carries the stage-6 control: one mutation
  row per copy, each changing only that copy and run alone, each failing the check, scored
  `MUTATION: ALL_CAUGHT`. Each row's `find` carries context that makes it unique in its file,
  because the harness refuses a non-unique anchor. The design owes the test's placement, its
  locators and the canonical block's exact text, which must match spec FR-9. Residual: the test
  shows that every copy carries the canonical block. It does not show that a copy carries no
  other, contradicting sentence beside it, or that a seventh surface exists. A seventh surface
  held in a `str` constant or in non-`.py` text is found by re-running the spec's FR-9 sweep (the
  union of the line grep and the joined-literal reading). A surface built at run time is found
  only by reading the code that builds the dispatch text.

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

**The halt-surface census for FR-9.** Spec FR-9 closes the rule's surfaces (v1.5, revised
alongside this plan). There are five today: prompt RED item 1, the prompt's WIRE-PIN paragraph,
the SKILL.md 5d bullet, the `failure-recovery.md` 5d row, and the wiring-task header in
`h-mad/scripts/h_mad_assemble_tdd.py` `assemble()`. The prompt's GREEN variant is added as a
sixth. v1.2 counted four, because its line-oriented grep cannot see a phrase split across a
physical line break, and the assembler's phrase spans two adjacent Python string literals. The
class has two members here: adjacent Python string literals, and hard-wrapped markdown. The
spec's sweep covers both. It reads every `str` constant from `ast.parse` (which joins adjacent
literals) in each `.py` file, and it collapses whitespace runs in every other file. Reading at
`9c3b799d`, regex
`missing.symbol|tests the callee|ImportError.*AttributeError|AttributeError.*ImportError`
(case-insensitive) over `git ls-files h-mad`: 7 files. They are the four surface files
(`SKILL.md`, `codex-implementer-prompt.md`, `failure-recovery.md`, `h_mad_assemble_tdd.py`),
plus `test_h_mad_agent_definitions.py`, `test_h_mad_wire_pin_gate.py` and
`h-mad/tests/fixtures/codex-text-8-exec.log`, none of which states the rule. The line grep returns
the same set without `h_mad_assemble_tdd.py` (6 files). Residual: a phrase built at run time (an
f-string field, `%` or `.format` interpolation, or a `+` join of names) is not a `str` constant,
so the sweep does not see it. A surface added later is not covered until the sweep is re-run.
**The joined-literal reading cannot see `.py` comments,** which the line grep does read, and
it has no stated behaviour for a `.py` file that fails `ast.parse`. So the line-grep set is not a
subset of the joined set by construction. The AC-9.1 re-run on the shipped tree uses the
**union** of the line grep and the joined-literal reading, and a `.py` file that fails
`ast.parse` is reported, never skipped. Reading at `5f72c2f3`, from a scratch script since
deleted (the regex above; `ast.walk` over `str` constants with whitespace collapsed; `tokenize`
`COMMENT` tokens; `git ls-files -z h-mad | xargs -0 grep -liE` with the same regex): joined
7 files, line grep 6 files, union 7 files, line grep minus joined 0 files, `ast.parse` failures
0 files, `.py` files with a comment matching the regex 0 files. Both zeros are incidental (no
comment restates the rule today, and every tracked `.py` parses), not load-bearing, which is why
the re-run takes the union. Spec v1.6 (`c853b207`) states this residual in FR-9's paragraph
"What the joined reading does not see in a `.py` file, and how the sweep covers it", and the
plan mirrors it.
The spec holds the sweep's text. The plan holds one
reading of the halt token, scoped to `h-mad/` so that this feature's own documents cannot move
it. Command at `e7730f78`: `git ls-files -z h-mad | xargs -0 grep -l 'red_wrong_reason'` →
3 files: `h-mad/SKILL.md`, `h-mad/references/failure-recovery.md` and
`h-mad/tests/test_h_mad_wiring_task_shape_docs.py`. The test pins the token in both docs. v1.0 counted
over the whole tree (4 files, one of them the spec). A tree-wide count moves whenever this
feature commits a document that names the token, and this plan names it too.

**The doc-pin census for stages 6 and 7 (R-8).** A test that locates or bounds a doc span by an
exact substring, or pins an exact sentence, breaks when the sentence is rewritten. v1.1 named the
heading pins and missed the end anchor beside them. That is one member of a class, so the plan
sweeps the class for every section this feature rewrites. The list below is the sweep's result
plus the pins the cycle-2 audit found by reading. It is a candidate list, not a closed one.

The census was swept at `d90decc6` with a scratch script, since deleted. It took every string
constant of at least 16 characters, containing a space, from each `git ls-files 'h-mad/tests/*.py'`
file that names the doc, and matched it verbatim inside the section. Residual: a shorter literal,
one with no space, or one built at run time is missed. The short locators below were added by a
second pass at 8 characters. **The literal matcher misses more than short strings.** The v1.3
additions show the axes it cannot see:
- short single-word tokens checked by a loop (`rc 0`, `exec grok`, `fallback_agent`, the Hook
  line's `Write`/`Edit`);
- **negative assertions** (`"exit-code protocol" not in section`, `"<" not in hook_line`). These
  forbid text, so no literal of theirs occurs in the doc;
- **structural locators** that are not section-scoped (`_hook_block`'s `Hook: ` line and its
  `- ` bullets);
- a bullet the census filed under the wrong section (`_skill_gate_bullet`, which lives in the
  teammate-audit section).

So the census does not certify that every pin is listed. The backstop is R-8's: each doc-editing
Task runs the full h-mad suite, never a scoped selection, and any pin that fails there is added
to that Task's RED before the Task closes. File-level reading at `9c3b799d` for the prompt:
`git ls-files 'h-mad/tests/*.py' | xargs grep -l 'codex-implementer-prompt'` → 14 files. Eleven
carry a pin listed below: nine from the literal matcher, and two found by reading
(`test_h_mad_extract_verdict.py` and `test_h_mad_portable_timeout.py`, filed under the prompt
below). The other three (`test_h_mad_assemble_tdd_agent.py`, `test_h_mad_install_check.py`,
`test_h_mad_verifier_prompt.py`) returned no match from the literal matcher and have not been
read by hand, so they are unclassified, not pin-free. A committed probe for this census is owed under
`docs/03-analysis/probes/agy-coder-fallback/`. Each entry can be checked with
`grep -n '<literal>' h-mad/tests/<file>`.
- **SKILL.md §"Codex authors Phase 5 — enforced, not just instructed":**
  - `test_grok_fallback_docs.py` `PHASE5_HEADING` (the full heading), plus
    `no write-time test-first gate`, `fallback-grok`, `HMAD_CODEX_UNAVAILABLE` and
    `fallback_agent` inside the section (`test_phase5_section_documents_fallback_agent`).
  - `test_h_mad_mutation_harness.py` `_phase_5e_text`. It slices from `### Codex authors Phase 5`
    to `Phase 5 implementation is **Codex's job**` with `str.index`, so a rewrite that drops
    either literal raises `ValueError` in `test_skill_documents_the_precheck_is_automatic`.
    FR-10 makes this section implementer-neutral, so the end anchor is the sentence most likely
    to go.
  - `test_h_mad_tdd_gate_docs.py`: the anchor sentence
    ``Test files, docs, config, and shell are never gated; only production `.py`.``, and the
    tokens `FIRST component`, `relative to the project root`, `` `src/docs/foo.py` `` and
    `Both gates`.
- **SKILL.md §"Exit-code dispatch for 5d/5e":**
  - `test_grok_fallback_docs.py` pins the full heading, and `exec grok` and `--agent grok` inside
    the section (`test_exec_section_documents_exec_grok`);
  - `test_h_mad_context_budget_docs.py` pins `hmad-dispatch exec agy`;
  - `test_h_mad_assemble_tdd.py` pins `hmad-dispatch exec codex`.
- **SKILL.md Phase-7 closure step**, which is list item 7 under `## Per-phase actions` and not a
  heading:
  - `test_h_mad_archreview_pane_halt.py` slices from `7. **Closure (autonomous)**` to
    `\n## Phase 5`, and pins its `SKIPPED_NO_PANE` sentence;
  - `test_h_mad_phase7_integrate_docs.py` pins `must name a LOCAL branch` and
    `git branch main origin/main`.
- **SKILL.md §"Teammate audit leg — when codex is unavailable", the bullet
  `- **It does not license Claude to write Phase 5 production code`** (rewritten by stage 6):
  - `test_h_mad_tdd_gate_docs.py` `_skill_gate_bullet` requires that anchor exactly once in
    SKILL.md (`text.count(anchor) == 1`), slices the bullet up to the next blank line, and
    `test_skill_gate_bullet_states_the_every_record_rule` pins `ACTIVE`, `every`, `unavailable`
    and `exhausted` inside it. The audit report filed this pin under §"Codex authors Phase 5". At
    `9c3b799d` the bullet is inside the teammate-audit section and outside §"Codex authors
    Phase 5" (both checked with `titled_section`), so it is listed here;
  - `test_grok_fallback_docs.py` `TEAMMATE_HEADING` (the full heading), plus `--surfaces agy,grok`
    and `unmeasured` inside the section.
- **`h_mad_assemble_tdd.py` wiring-task header** (FR-9 surface 5):
  `test_h_mad_assemble_tdd.py` `test_the_pin_is_told_what_its_red_must_be` pins `never a missing`
  in the assembled prompt.
- **SKILL.md 5d wiring bullet:** `test_h_mad_wiring_task_shape_docs.py` pins
  ``The third task shape is `wiring`, and counts cannot gate it.`` and
  `failure mode per test, not only the count`.
- **`agy-runtime.md` §"The TDD gate":** `test_h_mad_tdd_gate_docs.py` locates it with
  `titled_section(..., "The TDD gate")` and pins `h-mad-codex-tdd-gate.py`, `h-mad-tdd-gate.sh`
  and `permissionDecision`. Under refusal form b, `test_tdd_gate_section_names_the_chosen_form`
  also pins `rc 0` and forbids `exit-code protocol` in the section. §"Hooks" and
  §"Construct mapping" carry no pin.
- **`failure-recovery.md` 5d row:** `test_h_mad_wiring_task_shape_docs.py` `HALT_TOKENS` pins
  `step5d:red_wrong_reason:<module>`.
- **The prompt (`codex-implementer-prompt.md`, whole file):** 23 distinct literals across 8 test
  files: `test_h_mad_agent_definitions.py`, `test_h_mad_assemble_tdd.py`,
  `test_h_mad_preflight_docs.py`, `test_h_mad_prompt_tails.py`,
  `test_h_mad_tdd_dispatch_discipline_prompt.py`, `test_h_mad_wiring_task_shape_docs.py`,
  `test_hmad_dispatch.py` and `test_hmad_dispatch_exec.py`. That figure is the ≥16-character
  sweep's, at `d90decc6`. The sweep missed a ninth file, `test_h_mad_tdd_gate_docs.py`, which
  pins the prompt structurally. `_hook_block` requires exactly one line starting `Hook: ` and
  takes the `- ` bullets that follow it. `test_hook_line_names_both_gates` pins
  `h-mad-codex-tdd-gate.py`, `apply_patch`, `shell`, `h-mad-tdd-gate.sh`, `Write` and `Edit` on
  that line, and `test_hook_bullets_state_the_shipped_rule` pins `impl-plan`, `name map`,
  `summary`, `N failed`, `test_*.py`, `*_test.py` and `conftest*.py` in the bullets. Both tests
  forbid `<` and `>` on the line and in the bullets, so FR-9's implementer-neutral rewrite of the
  Hook block may not introduce a `<slot>` placeholder or an ASCII `->` arrow. Two more files pin
  the prompt by whole-file read, found by the plan-v1.3 delta review's reading and confirmed at
  `5f72c2f3` with `grep -n '<test name>' h-mad/tests/<file>`:
  - `test_h_mad_extract_verdict.py` `test_both_codex_prompts_spell_the_label` (parametrized over
    `codex-implementer-prompt.md` and `codex-verifier-prompt.md`) requires `` `Concerns:` `` in
    the prompt, and `prose` and `contentless` after it;
  - `test_h_mad_portable_timeout.py`, three tests parametrized over
    `references/codex-implementer-prompt.md`: `test_the_rule_reaches_every_surface_that_can_improvise`
    (`run --timeout` and `gtimeout`), `test_every_rule_surface_keeps_the_halt` (`halt` inside the
    window after a `gtimeout` mention), and
    `test_every_rule_surface_accounts_for_the_coreutils_present_case` (`coreutils` inside that
    window, with a term that says why the form stays forbidden).

  The 23-literal count has not been re-derived with these added.

**Rule over the class.** A rewrite either keeps each pinned literal, or changes that test's
literal in the same commit to text the rewrite keeps, with the test's assertions otherwise
unchanged. The Task's RED names every pin it moves. A pin is never deleted. A new locator uses a
precedent that fits the target's structure: `titled_section` for an ATX heading, and the
`str.index` slice above for a list item.

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
| A `review_independence` add mechanism that never removes or alters an entry (DO-3) | CLI / procedure | FR-7 |
| Doc-derived pins for FR-10's SKILL.md and `agy-runtime.md` rewrites (§"Success Criteria") | tests | FR-10 |
| `h_mad_phase7_preconditions.py` warnings `review_non_independent`, `review_independence_unrecorded`, `review_independence_malformed` | module | FR-7 |
| Tracked `.agents/hooks.json` in each adopting project, with this repository first | config | FR-5, D-2 |
| Implementer-neutral `codex-implementer-prompt.md` with the new-caller rule | prompt | FR-9 |
| SKILL.md, `agy-runtime.md`, `failure-recovery.md`, `state-schema.md` edits | docs | FR-9, FR-10 |
| `agy-runtime.md` hook-event claims re-checked against the installed agy | docs | spec §"Owed by other documents" |
| Probe directory `docs/03-analysis/probes/agy-coder-fallback/`: payload capture, real refusal, forced handler timeout with its outcome and the delay hook's removal, RED/GREEN with re-run, revert and mutation, each stamped with the sha and `agy --version`; derived timeout | probe | FR-8, AC-8.2 |
| FR-9 differential corpus (fixture repositories with real REDs, old and new verdicts) and HemaSuite incident replay, stamped with both repositories' shas | probe | FR-9, AC-9.2, AC-9.3 |
| Equivalence test over the six copies of the FR-9 carve-out, with one mutation row per copy | tests | FR-9, AC-9.4 |
| `implementer_switch.ts` refusal on both validator paths (DO-4 mechanism) | module / tests | FR-1, AC-1.2 |
| FR-5 exit-code split, with the `h_mad_assemble_tdd.py` docstring rewritten | CLI / tests | FR-5, AC-5.2 |
| Mutation rows for every new guard, plus re-pointed existing rows (R-1, R-3) | tests | AC-X |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| **R-1 — mutation anchors on the state-line contract go stale.** Rows whose `find` **or** `replace` text quotes the state line, its regex or the fold's inputs stop applying when FR-3 rewrites them. A row that matches zero times leaves the guard intact and reads as caught-by-nothing (`step5e:mutation_unverified`). Census at `17d73037`, command below (M-3): **8 rows in 3 specs** (`claude_gate_judge_wiring.json` 5, `tdd_judge_chain.json` 2, `tdd_gate_fallback_agent.json` 1). More broadly, the files FR-3 rewrites carry 56 rows (`h-mad/hooks/h-mad-tdd-gate.sh`, 5 specs) and 36 rows (`h-mad/scripts/h_mad_tdd_judge.py`, 8 specs) (M-2). | H | The Task that changes the line re-anchors every row in the M-3 census in the **same commit**. Its GREEN runs `h_mad_mutation_harness.py` over every spec in M-2's list for the two files, and gates on `MUTATION: ALL_CAUGHT`, never `$?`. The census is re-derived after the design fixes DO-1, because the fix adds members to the class it counts. |
| **R-2 — the tracer needs the installed gate, and the installed path is main.** `~/.gemini/config/skills/h-mad` resolves to this repository's main checkout (DO-6). In a Phase-5 worktree the new gate does not exist at the installed path. So FR-5's check reads `UNWIRED` (`bad-command` or `self-check-failed`) and FR-8 cannot run before merge with the shipped wiring. | H | Settled by D-13 (was OQ-B; DO-6): FR-8 runs after the merge to main as its own stage, with the halt standing until then, and the feature is recorded COMPLETE only after it passes. The test-pinned worktree override is not taken. A hand edit of the installed symlink is not an option, because the symlink also serves every live agy and Claude session (brainstorm risk "live symlink"). |
| **R-3 — moving the shell policy re-points the Codex gate's mutation rows.** Over the DO-5 set design v1.0 fixes (25 names), 31 of the 62 rows naming the Codex gate anchor inside a moved definition, in 4 specs (`codex_gate_judge_wiring.json` 21, `codex_gate_shell_allowance.json` 6, `assemble_tdd_mutation_rows.json` 2, `tdd_gate_differential.json` 2; M-4, at `200ffd52`). Their `file` is `hooks/h-mad-codex-tdd-gate.py`, relative to `h-mad/` as every row's `file` is (v1.4 wrote it from the repository root). The v1.4 figure, 19 rows over the 10-function closure alone, is a subset and is retired: the census counts over the set the move fixes, so it grows with that set. A row left on the old file matches zero times and reads as `step5e:mutation_unverified` (spec v1.3 FR-6). | M | Re-point them in the move Task, then gate each spec that holds one on `MUTATION: ALL_CAUGHT` (AC-6.1). Re-derive M-4 over the set DO-5 fixes. Keep the moved names an existing test reaches bound on the Codex gate module. AC-6.1's "one definition in the tree" is checked by a test that greps for a second `def` of each moved function. |
| **R-4 — old-shape stub lines vs AC-3.2.** Settled by spec v1.3 (DO-1a): the stub literals are re-shaped, and assertions stay byte-identical against `a8d9ba99`. What is left is the edit growing past the exception. | M | The FR-3 Task diffs each of the two gate test files against `a8d9ba99`. Every changed hunk must be a stub literal or a constant it is composed from. Every other `test_h_mad_tdd_gate_*.py` shows an empty diff. `test_h_mad_tdd_judge.py` diffed against `a8d9ba99` shows `ACTIVE_RE` as its only changed literal, so P-3..P-5 stay byte-identical (spec v1.4 AC-3.2). A test whose outcome no new-shape stub reaches goes back to the design. |
| **R-5 — a `review_independence` add loses or alters entries.** `--set` replaces the whole array (DO-3). | M | DO-3's mechanism. Per AC-7.1, the fixture adds to a record that already holds two entries and asserts both stay byte-identical. A refused entry leaves the store unchanged. |
| **R-6 — the FR-1 schema validates differently on the two validator paths, or `format` enforces nothing on either.** `format: date-time` is accepted for `not-a-date` on both paths at `d90decc6` (DO-4). | M | DO-4's mechanism, chosen by the design. AC-1.1 and AC-1.2 run on both paths, with AC-1.2's package-absent fixture where the library's format checker is used. |
| **R-7 — a deny does not bind under `--dangerously-skip-permissions`, or a sibling `ask` / `overwrite` changes the outcome.** | H | FR-8 step 2 runs through `hmad-dispatch exec agy` with the operator's real global `~/.gemini/config/hooks.json` loaded. At `17d73037` its `orca-status` `PreToolUse` `*` handler prints `{"decision":"ask"}` (`grep -n decision ~/.orca/agent-hooks/antigravity-hook.sh`). The halt stands until the step passes, and SKILL.md names "after any agy upgrade" as the re-run trigger (FR-5 residual). |
| **R-8 — doc-derived tests break on the doc edits.** `test_h_mad_tdd_gate_docs.py` reads `agy-runtime.md` §"The TDD gate", requires exactly one `Hook: ` line in the prompt, and anchors on a SKILL.md gate bullet. `test_h_mad_wiring_task_shape_docs.py` pins literals in the prompt and the halt tokens. At `17d73037`, 15 tracked test-side files name the prompt (M-5). The SKILL.md heading FR-10 makes implementer-neutral is pinned by two tests: `git ls-files -z h-mad/tests | xargs -0 grep -l 'Codex authors Phase 5'` → 2 files at `e7730f78`, `h-mad/tests/test_grok_fallback_docs.py` (`PHASE5_HEADING`) and `h-mad/tests/test_h_mad_mutation_harness.py` (`skill.index`). The same `_phase_5e_text` also ends its slice at `Phase 5 implementation is **Codex's job**`, the sentence FR-10's neutral rewrite is most likely to drop. §"Architecture Considerations", the doc-pin census, lists the pins found inside each rewritten section. It is a candidate list, not a closed one: its matcher misses short tokens, negative assertions and structural locators, and the full-suite run below is the backstop. | M | Run the full suite per Task, never a scoped selection: a scoped green misses a doc-derived test in another file. A FR-9/FR-10 Task's RED names every census pin it expects to move. Each pinned literal is kept, or the test's literal is changed in the same commit to text the rewrite keeps, with its assertions otherwise unchanged. A pin is never deleted. |
| **R-9 — the `agy-runtime.md` hook-event claim is stale on two surfaces, not one.** The spec names §"Hooks". The §"Construct mapping" `hook-event` row says the same thing ("there is no `SessionStart`"). Command at `17d73037`: `grep -n 'SessionStart' h-mad/references/agy-runtime.md` → 2 lines. Installed hooks.md lists it: `grep -c 'SessionStart' ~/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs/hooks.md` → 3 matching lines, agy `1.3.6`; still 3 under agy `1.4.0` at `200ffd52`. | L | A Task re-checks both surfaces against the installed agy (by reading hooks.md and, if the claim matters to h-mad, by a live probe), and corrects both together. `grep -rn 'no .SessionStart' h-mad/tests` → no hits at `17d73037`, so no test pins the stale claim. |
| **R-10 — a stale suite floor lets a test be deleted while staying green.** | M | The floor is re-measured at the 5c baseline, not copied from here (M-1). |
| **R-11 — agy's writes land outside `--cd`** (brainstorm; seen for audit reports, J30). | M | FR-8 step 3 checks where files landed. The gate denies an out-of-root `.py`. |
| **R-12 — agy narrates work it did not do, or reports false counts.** | M | The tree delta, the independent re-run and the revert test are the evidence. The `STATUS:` line is a claim. |
| **R-13 — agy fails open when a handler overruns its timeout.** hooks.md does not say what agy does with a late handler, and FR-8 step 2 cannot observe it. | H | Stage 8, step 2a (AC-8.2). If the outcome is `timeout-allows`, the gate's write guarantee rests on finishing within its timeout. `agy-runtime.md` §"The TDD gate" then states that residual, and the operator question is raised before the gate is called verified. |
| **R-14 — the FR-9 carve-out admits more than the new-caller case.** | H | Stage 6: the differential corpus (AC-9.2), with the changed set equal to `{new-caller}`, and the incident replay (AC-9.3). The six copies are held equal by the equivalence test (AC-9.4), so one copy cannot carry a broader exception. DO-7 says where the rule is applied. |

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

- Every AC in the spec passes: AC-1.1, AC-1.2, AC-2.1, AC-2.2, AC-3.1, AC-3.2, AC-4.1, AC-4.2,
  AC-5.1, AC-5.2, AC-6.1, AC-7.1, AC-7.2, AC-9.1, AC-9.2 and AC-X as automated tests, and
  AC-8.1, AC-8.2 and AC-9.3 as committed probes under `docs/03-analysis/probes/agy-coder-fallback/`.
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
- **FR-10 has no AC of its own, so the plan gates it here.** The FR-10 Task adds a doc-derived
  test that pins each rewrite below. It never locates a span by a line number. Each locator fits
  its target's structure:
  - A section under an ATX heading is located with `h-mad/tests/doc_sections.py`
    `titled_section`. `test_h_mad_tdd_gate_docs.py` and `test_grok_fallback_docs.py` follow this
    pattern.
  - The Phase-7 closure step is **list item 7 under `## Per-phase actions`, not a heading**.
    `titled_section` delegates to `h_mad_doc_block_exec.find_heading`, which matches ATX headings
    only, so it would fail with `missing section`. Locate the step with the existing precedent,
    `test_h_mad_archreview_pane_halt.py`: a `str.index` slice from `7. **Closure (autonomous)**`
    to `\n## Phase 5`.

  Each pin is mutation-checked: deleting the pinned sentence fails it, scored
  `MUTATION: ALL_CAUGHT`. Every baseline below is a count of matching lines, read at `d90decc6`
  with the command beside it, and each must be non-zero after the Task. `$Q` stands for this
  counter, which uses the same locator the test will use:
  `Q='import sys; sys.path.insert(0,"h-mad/tests"); import docsections as d; t=open(sys.argv[1],encoding="utf-8").read(); s=d.titled_section(t,sys.argv[2]); print(sum(any(n in l for n in sys.argv[3:]) for l in s.splitlines()))'`
  - SKILL.md §"Codex authors Phase 5 — enforced, not just instructed" (or the heading the Task
    leaves, per R-8) states FR-2/FR-3. It names `agy-authorship` and the
    `h_mad_tdd_judge.py implementer` verb. Baseline: 0 and 0, from
    `/opt/anaconda3/bin/python3 -I -c "$Q" h-mad/SKILL.md 'Codex authors Phase 5 — enforced, not just instructed' 'agy-authorship'`
    and the same command with `'h_mad_tdd_judge.py implementer'` as the last argument.
  - SKILL.md §"Exit-code dispatch for 5d/5e" lists `exec agy` as an implementer dispatch.
    Baseline: 2 lines name `exec agy`. One is the bullet "the 5e-review (and Phase 3/4/5b audit)
    dispatch", and the other is a command example. 0 lines name it together with an implementer
    role. The needle is a line that contains `exec agy` and `implement`, case-insensitive.
    Commands:
    `` /opt/anaconda3/bin/python3 -I -c "$Q" h-mad/SKILL.md 'Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot' 'exec agy' ``
    → 2, and
    `` /opt/anaconda3/bin/python3 -I -c 'import sys; sys.path.insert(0,"h-mad/tests"); import docsections as d; t=open("h-mad/SKILL.md",encoding="utf-8").read(); s=d.titled_section(t,"Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot"); print(sum("exec agy" in l and "implement" in l.lower() for l in s.splitlines()))' ``
    → 0.
  - The SKILL.md Phase-7 closure step says the report carries every `WARNING` line that
    `h_mad_phase7_preconditions.py` prints. Baseline: 0, from
    `/opt/anaconda3/bin/python3 -I -c 'import sys; t=open("h-mad/SKILL.md",encoding="utf-8").read(); i=t.index("7. **Closure (autonomous)**"); s=t[i:t.index("\n## Phase 5", i)]; print(sum("WARNING" in l for l in s.splitlines()))'`.
    The whole file also reads 0 (`grep -c 'WARNING' h-mad/SKILL.md`).
  - `h-mad/references/agy-runtime.md` §"The TDD gate" names `h-mad-agy-tdd-gate.py` and the
    `AGY-GATE:` check, and it keeps the halt. Baseline: 0, from
    `/opt/anaconda3/bin/python3 -I -c "$Q" h-mad/references/agy-runtime.md 'The TDD gate' 'h-mad-agy-tdd-gate' 'AGY-GATE'`.
  - The SKILL.md teammate-audit bullet `- **It does not license Claude to write Phase 5 production code`
    separates audit-leg selection from resolved authorship, and names
    `h_mad_tdd_judge.py implementer` and `agy-authorship`. Baseline: 0 and 0 at `9c3b799d`. The
    commands and the locator are in stage 6.

  These baselines do not drift on their own, because `h-mad/` has not moved since `17d73037`.
  Re-measure them only if a commit touches SKILL.md or `agy-runtime.md` before the FR-10 Task.

  The `state-schema.md`, schema-JSON and `failure-recovery.md` parts of FR-10 are already gated,
  by AC-1.1 and AC-9.1. The residual is that the pins check presence, not meaning. A wrong
  sentence that contains the needle passes, and each pin is read by hand at 5e.

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
- **M-4 — Codex-gate rows inside the moved set** (over DO-5's set as design v1.0 fixes it; re-derive
  if the design changes that set): parse `h-mad/hooks/h-mad-codex-tdd-gate.py` with `ast`. The set
  is the transitive closure of module-level functions called by name from `_safe_shell_command`
  (10 functions), plus `_shell_allowance`, `_operator_allowed`, `_is_shell_allowance`,
  `_read_regular_text`, `_state_status`, `_any_phase5_status` and `_is_production_python`, plus the
  module-level assignments `SIMPLE_SHELL_COMMAND`, `READ_ONLY_COMMANDS`, `SAFE_DISPATCH_VERBS`,
  `SAFE_HMAD_SCRIPT_OPTIONS`, `TEMP_OUTPUT_OPTIONS`, `SHELL_ALLOW_FILE`, `TRUSTED_BIN_DIRS` and
  `MALFORMED_WORKDIR`. Over every spec in `git ls-files 'tests/mutation-specs/*.json'` (run from
  `h-mad/`), count the rows whose `file` is `hooks/h-mad-codex-tdd-gate.py` and whose `find` text's
  first occurrence starts on a line inside one of those nodes' `lineno..end_lineno` spans. Reading
  at `200ffd52`, units are rows: 62 rows name the hook; 31 qualify (21 in
  `codex_gate_judge_wiring.json`, 6 in `codex_gate_shell_allowance.json`, 2 in
  `assemble_tdd_mutation_rows.json`, 2 in `tdd_gate_differential.json`); 0 rows have a `find`
  absent from the file and 0 a `find` that occurs more than once. The same procedure restricted to
  the 10-function closure gives 19 rows (17 and 2), the v1.4 figure, reproduced. The scratch probe
  that produced both readings was deleted; its committed form under
  `docs/03-analysis/probes/agy-coder-fallback/` is owed by the impl-plan (design v1.0 §"Owed by
  other documents"). Re-derive after the move Task, since the move changes which file the rows
  name.
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

- **Spec.** Spec v1.4 (`e6610381`) answers the plan-audit cycle-1 items it owns: F1 (FR-5's exit
  table, AC-5.2), F2 (FR-1's RFC 3339 refusal on both paths, AC-1.2), F3 and F4 (FR-9's corpus and
  replay, AC-9.2, AC-9.3), F5 (FR-8 step 2a, AC-8.2) and F6 (FR-3's placement constraints, and
  AC-3.2 extended to `test_h_mad_tdd_judge.py`). The six v1.0 items stay answered, as v1.1
  recorded. FR-8 step 2 now settles two unknowns and leaves handler timeout to step 2a
  (`grep -n 'settles two unknowns' docs/01-plan/features/agy-coder-fallback.spec.md` at
  `e6610381`). FR-10 still has no AC of its own, but the plan gates it in §"Success Criteria". Spec
  v1.5 (`e8def13f`) answers the plan-audit cycle-2 items it owns: the teammate-audit bullet in
  FR-10's surface list (B), FR-9 surface 5 and the joined-literal sweep (C), the three pin files
  and the direct-call replay of T5/T6 in AC-9.3 (D), and AC-9.4 for the six copies (A). Spec v1.7
  (`c117a695`) answers the items design v1.0 and its audit cycle 1 left with the spec: agy
  `1.4.0` with every FR-8 reading stamping its version, D-12 (OQ-A), D-13 (OQ-B), D-14 (leap
  second), the `codex_status` surfaces in FR-1, and FR-7's Attribution rule. Open for the spec:
  AC-7.1 and AC-7.2 do not name the Attribution fixture (stored `implementer_switch.to=agy`,
  Codex-authored code, Codex reviewer → `independent=false`). The plan carries it in stage 7. If
  it should be an acceptance criterion, the spec owes it.
- **Design.** DO-1 through DO-7. Design v1.0 (`df46f72a`) addresses all seven; its audit cycle 1
  findings are the design's own revision and are not restated here:
  - choose the `TDD-STATE:` shape: no optional peer fields, the five placement invariants
    P-1..P-5 held, and any gate test whose asserted outcome no new-shape stub can reach reported
    (DO-1, DO-1a);
  - name the `review_independence` add mechanism and, for a read-modify-write, its lost-entry
    detection (DO-3);
  - pick the `.ts` refusal mechanism, cite the probe, carry the `rfc3339-validator` hazard, and
    if the mechanism is schema-wide, run `classify_store` over the live state files (DO-4);
  - fix the moved-name set and keep the names an existing test reaches bound on the Codex gate
    module (DO-5);
  - say whether the FR-9 carve-out stays prose-applied or gains a check, and state the corpus
    residual that follows. Place the AC-9.4 equivalence test, which the plan has named, give each
    of the six copies its own locator so that a single-copy mutation fails the test, and fix its
    canonical carve-out block (all three sentences) to spec FR-9's text (DO-7).
- **Impl-plan.** Each FR-9/FR-10 Task's RED names the doc-pin census entries it moves (R-8). The
  doc-pin census, the DO-1a line census and the M-4 row census become committed probes under
  `docs/03-analysis/probes/agy-coder-fallback/`.
- **A later feature.** Classify the assembler's existing `ASSEMBLE-TDD: HALT` reasons as verdict
  or operational error (spec v1.4 FR-5 residual).

## Next Steps

The Phase-3 audit cycle runs on two surfaces, and revisions go back to `plan-author`. The
operator then reviews and approves. The design obligations DO-1..DO-7 are inputs to Phase 4.

## Version History
- v1.0: Initial plan (2026-10-16) from spec v1.2 at 17d73037. Carries D-9/D-11 for every implementer, D-10 per-clone prerequisite, design obligations DO-1..DO-6 (state-line shape and its literals, read-only allowlist, review_independence append, schema constructs on both validator paths, shell-policy module boundary, installed-path vs worktree), mutation re-anchoring risks R-1/R-3, and six items owed by the spec.
- v1.1: Re-synced to spec v1.3 at e7730f78 (2026-10-16). DO-1a/R-4 closed to the AC-3.2 stub-line exception (missing field = judge-error; the keep-old-stubs branch is removed). DO-3, stage 7 and R-5 now carry FR-7's add requirement. DO-5, stage 4 and R-3 keep the moved names bound on the Codex gate module, with rows re-pointed then ALL_CAUGHT. Stage 6 adds the failure-recovery.md 5d row and the test_h_mad_agent_definitions.py pin. Stage 1 adds the four pinned fallback_agent substrings. R-8 adds the two SKILL.md heading pins. Success Criteria now gate FR-10. The halt-token census is re-scoped to h-mad/ (3 files). All spec items under Owed are marked answered.
- v1.2: Plan audit cycle 1 and spec v1.4 at e6610381 (2026-10-16). F1: stage 5 mirrors the FR-5 exit table and AC-5.2 (verdicts exit 0, UNREADABLE and no-token exit 2; token and exit code pinned separately; assembler docstring rewritten). F2: DO-4 premise corrected (format is enforced on neither path, probed at d90decc6); the mechanism is a design obligation, with the rfc3339-validator hazard, the AC-1.2 fixtures and classify_store for a schema-wide mechanism. F3/F4: stage 6 adds the old/new differential corpus (AC-9.2, changed set = {new-caller}) and the HemaSuite T4/T5/T6 incident replay (AC-9.3); new DO-7 says where the rule is applied. F5: stage 8 adds step 2a, the forced handler timeout (AC-8.2), and R-13. F6: DO-1a corrected; placement invariants P-1..P-5 over 6 tests, probed; the per-record slot is free and no header field may follow fallback=. F7: the Phase-7 locator is a str.index slice, not titled_section; the doc-pin census covers every rewritten section, including the _phase_5e_text end anchor; R-8 is rewritten. S1: each FR-10 baseline carries its command, re-run at d90decc6. ACs are now 18.
- v1.3: Final corrective revision after the plan audit round cap: cycle-2 build findings only, and spec v1.5 at e8def13f (2026-10-16). A: stage 6 and DO-7 bind the six copies of the FR-9 carve-out to one authority (AC-9.4). The plan names the equivalence test and carries a one-copy-per-row mutation control. B: stage 6 rewrites the SKILL.md teammate-audit bullet to separate audit-leg selection from resolved authorship (resolved = claude), and pins the replacement condition (baseline 0/0 at 9c3b799d); Success Criteria lists it. C: the FR-9 census adds surface 5, the h_mad_assemble_tdd.py assemble() wiring header, and its pin in test_h_mad_assemble_tdd.py. The census states the split-across-a-line-break class and its joined-literal sweep (7 files at 9c3b799d). D: the incident replay names the three pin files and commits, and replays T5/T6 in direct-call form, recording the scaffolded RED. E: the doc-pin census adds the missed pins from test_h_mad_tdd_gate_docs.py and test_grok_fallback_docs.py, files the _skill_gate_bullet pin under the teammate section, and becomes a candidate list with stated residuals; the R-8 over-claim is removed. ACs are now 19.
- v1.4: Answers the advisory delta review of v1.3 (2026-10-16), no new scope. Must-fix 1 and Should-fix 1: stage 6 and DO-7 no longer read the assembler copy from the assembled wiring prompt; each of the six copies is read from its own source location (each template copy located individually, the .py copy from its joined str constant), the locators are a DO-7 obligation that must make a single-copy mutation fail the test, and each mutation row's find carries context unique in its file because the harness refuses a non-unique anchor. Should-fix 2: canonical carve-out sentence becomes the canonical carve-out block (all three sentences of spec FR-9's block) at stage 6, DO-7 and the Design owed line. Should-fix 3: the FR-9 census states that the joined-literal reading cannot see .py comments or parse failures, the AC-9.1 re-run takes the union with the line grep, re-measured at 5f72c2f3 (union 7 files, comment hits 0, parse failures 0), and the spec item is listed as owed. Should-fix 4: DO-7's residual now matches the census (a run-time-built surface is found only by reading the dispatch-building code). Should-fix 5: the doc-pin census files test_h_mad_extract_verdict.py and test_h_mad_portable_timeout.py under the prompt (eleven of 14 carry a pin; three stay unclassified). Nit: the copies' formats are restated (four markdown shapes and one Python form).
- v1.5: Answers the plan items of the design audit cycle 1 decision sheet (design v1.0 at df46f72a), no new scope (2026-10-16). P1: M-4 re-derived at 200ffd52 over the DO-5 set design v1.0 fixes (25 names): 31 of 62 Codex-gate rows in 4 specs; the 10-function closure alone reproduces the retired 19; R-3 restated, its row file corrected to hooks/h-mad-codex-tdd-gate.py. P2: DO-2 no longer asks for the inventory log agy version, which the log does not record; the class-(a) list is re-checked against an init.tools inventory re-captured with agy --version (design: FR-8 step 1). P3: OQ-A (policy in h_mad_target_identity.py) mirrored in stage 4 and DO-5; OQ-B (post-merge FR-8 stage, COMPLETE only after it) mirrored in DO-6 and R-2. P4: agy 1.4.0 at 200ffd52 in the Overview and R-9. The stale spec FR-9 residual owed item is dropped (spec v1.6 states it) and the FR-9 census paragraph cites it; the spec owed list now carries the agy version, OQ-A naming and OQ-B record.
- v1.6: Mirrors spec v1.7 at c117a695 (2026-10-16), no new scope. D-12 (policy in h_mad_target_identity.py, was OQ-A), D-13 (FR-8 post-merge stage; COMPLETE only after it, AC-8.1 and AC-8.2 included, was OQ-B) and D-14 (implementer_switch.ts narrowed to seconds 00-59) added to the decisions list and cited in stage 4, stage 8, DO-5, DO-6 and R-2. Stage 1 gains the codex_status description and state-schema.md row rewrite (both surfaces; 0 test pins at c117a695) and the AC-1.2 leap-second fixture 2016-12-31T23:59:60Z on both validator paths. Stage 7 gains the FR-7 Attribution rule and its fixture (stored implementer_switch.to=agy, Codex-authored code: implementer=codex, Codex reviewer independent=false). Stage 8 stamps every reading with the sha and agy --version (1.4.0 at 200ffd52) and re-takes a reading made under a different version. The spec owed list now records v1.7 as answering the design-cycle items; AC-7.x not naming the Attribution fixture is flagged to the spec. AC census re-run at c117a695: ACS OK count=19 frs=9.
