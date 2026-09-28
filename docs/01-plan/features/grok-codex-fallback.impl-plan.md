# Implementation Plan: grok-codex-fallback

> Source: docs/02-design/features/grok-codex-fallback.design.md (v1.3 at `6277d703`, binding,
> including its §"Supersedes the plan on"), docs/01-plan/features/grok-codex-fallback.spec.md (v1.5
> at `02283561`, 58 ACs, binding), docs/01-plan/features/grok-codex-fallback.plan.md (v1.3: wiring
> table W1–W11 and the Phase-5 live smoke stay binding)
> Branch target: feature/216-grok-codex-fallback
> Naming: **merged §D13** is `codex-tdd-gate-defects` design §D13, "Rebase contract for
> grok-codex-fallback D2" (archived at
> `docs/archive/2026-09/codex-tdd-gate-defects/codex-tdd-gate-defects.design.md`); **grok design
> §D13** is this feature's own design section "The Phase-5 live smoke". Every reference below
> is qualified one of these two ways. Following grok design v1.3 §D2, **the fold field** is the line-level `fallback=` token and
> **the record's tag** is the fourth subfield of a `record=` word.

## Executive Summary

Seventeen tasks, each counted once: two leaf tasks with no dependency (Task 1 builds the in-skill
F0 copy, the fixture builder and the stubs; Task 2 adds the schema property); two `new-behaviour`
leaves (Task 5, `scan_grok` plus the `scan()` RecursionError catch and `agy_events` type guard; Task 8, the shell stream
readers); eight `wiring` tasks that connect each surface to its new callee (Tasks 3, 4, 6, 7, 9, 10,
11, 12, carrying W1–W11 of plan v1.3 as 14 WIRE entries); one cross-surface agreement task (13); one
task that authors and runs the 65 mutation rows in seven specs (14); the documentation (15); the full
coupled-suite gate (16); and last the live `exec grok` smoke through the worktree's own wrapper (17).
2 + 2 + 8 + 1 + 1 + 1 + 1 + 1 = 17.

**State at v1.4.** The branch was rebased onto `main` `8ef6009f`, the merge of
`codex-tdd-gate-defects`, which rewrote the Claude TDD gate around a judge
(`h-mad/scripts/h_mad_tdd_judge.py`). Tasks 1–11 and 13 are implemented and committed (HEAD
`d9574614`); Tasks 12 and 14–17 are not started. Task 12 is re-planned onto the shipped gate
(§"Deviations from design v1.2", item 5), and Task 14's Task-12 rows are re-derived with it.

**State at v1.5.** Read at HEAD `6277d703`; the gate and the judge are still byte-identical to
`8ef6009f` (`git diff --quiet 8ef6009f HEAD -- h-mad/hooks h-mad/scripts/h_mad_tdd_judge.py` exits
0). Since v1.4, grok design v1.3 (`6277d703`) owns the fold field and adds the tag agreement check,
spec v1.5 (`02283561`) restates FR-2, AC-2.2, AC-2.5 and AC-11.1 on the merged gate, and commit
`f2ff9261` re-pinned `h-mad/tests/test_h_mad_assemble_tdd_agent.py`'s own `BASE_SHA` from
`507214d` to `8ef6009f` (Preamble). Task 12 gains the agreement check (tests 17–19, rows G11 and
G12) and plans the wire registry move for its two WIREs; Task 16's allowlist accepts only each
file's stated change.

## Deviations from design v1.2

The design is binding except where the orchestrator ruled otherwise on an audit finding. Each
deviation below is recorded with its evidence. **For 5d and 5e this section overrides the design
wherever the two disagree** (design v1.2 line 877 "`scan()` is untouched", at v1.3 lines 1006 and
1026; its mutation rows, 43 at v1.2 and 49 at v1.3; and its six specs): an implementer or auditor
reading both follows this section. The heading keeps its v1.2 name because other sections cite it. Amending the design to match
is not a precondition of 5d; it is an open item for the orchestrator, named in this revision's report.
The `path:line` pins in items 1–4 are readings at `507214d`, before Tasks 5–7 edited those files;
they record why the repairs were made and are not claims about the committed tree.

1. **`scan()` is no longer untouched** (design line 877 "`scan()` is untouched"; impl-plan audit
   cycle 1, teammate must-fix; orchestrator decision 1, repair (a)). `scan()`'s
   `json.loads(line)` at `h-mad/scripts/h_mad_review_evidence.py:130` catches only
   `except (ValueError, TypeError):` (`h-mad/scripts/h_mad_review_evidence.py:131`), so a 200,000-deep line raises `RecursionError`. The
   teammate executed this on Python 3.14.7, 3.11.8 and `/opt/anaconda3/bin/python`: the CLI exits 1
   with frames `:251 → main :201 → scan :130`, and `measure_effort()` raises the same error. So
   the design's Test Plan row at line 1731, whose last clause reads "and the CLI prints F0's
   `EVIDENCE:` line (row E4)" on the malformed fixture, could not go GREEN with `scan()` untouched. Re-executed for this revision at `76b2501` (`h-mad/`
   byte-identical to `507214d`) with `/opt/anaconda3/bin/python`, no file written:
   `h_mad_review_evidence.scan(depth_line(200_000))` → `RecursionError`, and
   `h_mad_archreview_cycle._evidence_counts(...)` on the same line → `RecursionError`; the tuple
   `(ValueError, TypeError, RecursionError)` catches it. **Repair:** Task 5 changes `h_mad_review_evidence.py:131` to
   `        except (ValueError, TypeError, RecursionError):`. **Class rule:** every Python JSON
   parse that reads a dispatch transcript, under any argument name (`--log`, the evidence CLI's
   positional `log`, or a path handed in by a caller), catches `RecursionError`. The census is the
   importer grep, not an argument-name grep: `grep -rn 'import.*h_mad_review_evidence\|from
   h_mad_review_evidence' h-mad/scripts h-mad/hooks h-mad/bin` → 2 matching lines,
   `h-mad/scripts/h_mad_audit_cycle.py:17` and `h-mad/scripts/h_mad_archreview_cycle.py:117` (read
   at `01121ca7`, `h-mad/` byte-identical to `507214d`), so `scan()`'s transcript readers are the CLI
   itself and those two modules. A `--log` text grep is only a cross-check: `grep -n 'json.loads'
   h-mad/scripts/*.py` (28 matching lines in 17 files, read at `76b2501`) crossed with `grep -ln --
   '--log' h-mad/scripts/*.py` (5 files: `h_mad_archreview_cycle.py`, `h_mad_assemble_tdd.py`,
   `h_mad_audit_cycle.py`, `h_mad_resolved_model.py`, `h_mad_review_evidence.py`; in
   `h_mad_audit_cycle.py` and `h_mad_review_evidence.py` the match is in comments and help text
   only) leaves 2 files in both (`h_mad_archreview_cycle.py`, `h_mad_review_evidence.py`), and
   `h_mad_audit_cycle.py` parses its log only through `scan()`. The members:
   - `h_mad_review_evidence.py:130` `scan()` — the one parse. Its three `--log` callers are
     `h_mad_review_evidence.py:201` (`main`), `h_mad_audit_cycle.py:530` (`measure_effort`) and
     `h_mad_archreview_cycle.py:117-119` (`_evidence_counts`, which `score --log` reaches). All three
     are closed by the one `h_mad_review_evidence.py:131` change and each gets its own test: `scan()` itself Task 5 test 11,
     `_evidence_counts` Task 5 test 12, the CLI Task 6 test 7, `measure_effort` Task 7 test 12.
   - `scan_grok` (Task 5) and `grok_from_log` (Task 4) are new and already catch
     `(ValueError, RecursionError)`.
   - `h_mad_resolved_model.py`'s codex and agy paths parse no JSON (regex over the header; the module
     does not import `json` at `507214d`). `h_mad_assemble_tdd.py` only prints `--log` into a command
     block and parses no log. `h_mad_archreview_cycle.py:430` parses the state file, not a `--log`.
   - The other 26 `json.loads` lines are in 15 files that read no dispatch transcript: none of them
     imports `h_mad_review_evidence` (the importer census above), and the v1.1 delta review
     (`grok-codex-fallback.impl-plan.delta-review.v1.1.md`) read the argument surfaces of the
     line-parsing ones (`audit_origins`, `context_budget`, `response_probe`, `telemetry`,
     `wire_registry`) and found none that takes a transcript. That
     zero is load-bearing: a new transcript consumer, whatever it names its path argument, joins the
     class and needs the catch.
   **Anchors:** line 131 is in no committed anchor. The committed `h_mad_review_evidence.py` finds
   (audit_effort, codex_transcript_evidence and review_evidence_format specs) contain no `except`, and
   the new line does not contain E7's find `except (ValueError, RecursionError):` as a substring, so
   E7 still matches once. New mutation row E9 (Task 14).
2. **Wire-scoped removals are mutation rows** (orchestrator decision 3, answering codex must-fix 2).
   The design states each wire's removal direction in prose only. This plan scores all 14 of them
   (one per WIRE across the eight wiring tasks; Task 12 carries two since v1.4) as rows of a seventh
   spec, `grok_wire_reverts.json`, each with the callee intact and the task's WIRE-PIN as its `test`
   key.
3. **Mutation total 65, not the design's 49.** Grok design v1.3 names 40 rows (G1–G12, P1–P9,
   L1–L5, E1–E8, A1–A3, T1, R1–R2) plus 9 force-fires that alias no named row = 49 (design v1.2
   had 43: G1–G6 instead of G1–G12). This plan adds E9 (deviation 1), E10 (deviation 4) and 14
   wire-revert rows (deviation 2): 49 + 2 + 14 = 65, in seven specs, not six. Committed spec count after Task 14: 114 (the 107 committed specs
   read by `--check-anchors` at HEAD `d9574614`, plus 7).
4. **`scan()`'s `agy_events` membership test is type-guarded** (a second change to `scan()`; impl-plan
   audit cycle 2, codex must-fix 2; orchestrator decision 3). `h-mad/scripts/h_mad_review_evidence.py:141`
   reads `        if event.get("event") in _AGY_EVENTS:`, and `_AGY_EVENTS` is a `frozenset`
   (`h-mad/scripts/h_mad_review_evidence.py:42`), so valid JSON whose `event` value is unhashable
   raises `TypeError` there, outside the `try` that guards `json.loads`. Executed for this revision
   at `01121ca7` with `/opt/anaconda3/bin/python`, on F0 with `{"event":[]}` prepended, no file kept
   in the tree: the CLI ends `TypeError: unhashable type: 'list'`, and `measure_effort()` raises
   `TypeError unhashable type: 'list'`. The design row quoted in deviation 1 therefore also fails on a
   log that carries such a line. **Repair:** Task 5 replaces line 141 with the two lines
   `        event_name = event.get("event")` /
   `        if isinstance(event_name, str) and event_name in _AGY_EVENTS:`; the next line,
   `            agy_events += 1` (the committed anchor of `review_evidence_format.json`), stays
   byte-identical. Executed on a scratch copy of the module (deleted): the guarded `scan()` on the
   mixed log equals `scan()` on F0, `{"event":"init"}` still counts 1 and `{"event":{}}` counts 0.
   **Class rule:** every `x in <frozenset|set|dict>` whose `x` is a JSON-derived value reachable from
   a dispatch transcript is type-guarded before the membership test. Members, from a sweep of every
   ` in ` expression in the two files (read at `01121ca7`):
   - `h-mad/scripts/h_mad_review_evidence.py:141` (`scan()`, `event.get("event") in _AGY_EVENTS`) —
     the one unguarded member; repaired above, new test Task 5 test 13, new row E10.
   - `scan_grok` (Task 5, new): `isinstance(t, str) and t in _GROK_TYPES` — guarded (row E4).
     `t in ("tool_call", "tool_call_update")` and `type(value) in (int, float)` test a tuple, which
     compares by `==` and never hashes, so they are outside the class.
   - `scan_codex_text()` (`h_mad_review_evidence.py:86-87`, `kind in outcomes`) iterates regex
     matches, not JSON; `main()` makes no membership test on a parsed value.
   - `h-mad/scripts/h_mad_audit_cycle.py`: no member. It parses its log only through `scan()` (no
     `json.loads` in the file). Its ` in ` expressions on values are `_payload(line) not in
     acknowledged` (lines 680 and 691; report text, not JSON), `result.returncode not in (0, 2)`
     (741), `shape in ("missing", "unparseable")` (878) and `len(parts) not in (4, 5)` (1004); the last
     three test tuples. Task 7's new `shape not in ("parsed", "grok")` is a tuple too.
   - Outside the two swept files, for completeness: `grok_from_log` (Task 4) makes no membership test
     on a parsed value (`event.get("type") == "end"`, `sorted(usage)`).
   **Anchors:** the two new lines contain none of the 926 committed finds (907 in
   `h-mad/tests/mutation-specs/`, 19 in `h-mad/tests/specs/`) as a substring (executed: 0 hits), and
   none of this plan's `review_evidence_grok.json` finds.
5. **Task 12 is re-planned onto the merged judge gate, not design v1.2 §D2's `jq` read** (v1.4; the
   rebase contract `codex-tdd-gate-defects` design §D13, archived at
   `docs/archive/2026-09/codex-tdd-gate-defects/codex-tdd-gate-defects.design.md`, and that
   feature's impl-plan §"After Phase 5 (not tasks)"). Design v1.2 §D2 builds on a gate that no
   longer exists: the merged `h-mad/hooks/h-mad-tdd-gate.sh` contains no `jq`, no `$ACTIVE`, no
   `exit 1` and no BLOCK-CODEX `if` (it refuses through `_refuse`, whose two arguments are a kind and a text, in form `b`: one
   stderr line beginning `[H-MAD-TDD-GATE] BLOCK kind=`, the kind and `: `, a JSON deny on stdout, rc 0), and
   the committed test
   `h-mad/tests/test_h_mad_tdd_gate_judge.py::test_claude_gate_keeps_no_private_state_reader` fails
   on any `jq` or `orchestrator_state` token in the hook. The value D2 read already arrives: the
   judge's `_fallback_tag` computes each ACTIVE record's tag (`absent`, `null`, `grok`, `claude`,
   or `invalid:` and the value's compact JSON), and `format_state_line` prints it as the fourth subfield of every `record=`
   word. What this plan adds, per merged §D13's contract items 1–5:
   - **The fold, in the judge.** `_fallback_fold(records)` returns `invalid:B` for the first
     record whose tag begins `invalid:`, else `grok:B` for the first `grok` record, else `none`,
     where B is that record's 1-based chain position (for example `invalid:2` or `grok:1`). The most restrictive record wins and the outcome does not
     depend on order (merged §D13 item 2).
   - **The field, on the state line.** `format_state_line` appends ` fallback=` and the fold after
     the `records=` field. v1.4 chose the spelling because merged §D13 item 1 leaves the field's
     name, grammar and position to grok's design, and design v1.2 predated it. **Grok design v1.3
     §D2 now owns it** and adopts this spelling unchanged (name `fallback=`, kept over
     `fallback-fold=` with its reason stated there). Grammar:
     `fallback=(none|(grok|invalid):([1-9][0-9]*))`, a closed token (merged §D10's `_enc` is not
     applied).
   - **The gate reads it and applies no rule over the records of its own.** `STATE_ACTIVE_RE`
     gains the field whole-line in the same commit (merged §D13 item 5); `_read_state`
     cross-checks B ≤ `records` and captures the governing `record=` word; after the
     codex-authorship refusal (so only when codex is out, merged §D13 item 3) the gate checks that
     the fold's kind agrees with the governing record's tag, refusing `judge-error` when it does
     not (grok design v1.3 §D2 "Tag agreement"), then refuses `fallback-grok` or
     `fallback-invalid` (merged §D13 item 4). The `*)` unreadable arm of design v1.2 §D2 has no
     successor: a state read failure is refused `judge-error` by `_read_state` before this block,
     and an unknown fold token fails the ERE.
   - **The spec now states the merged gate** (spec v1.5, answering the v1.4 delta review's last
     should-fix): FR-2's table reads deny with a kind instead of "exit 1"; "the ACTIVE feature" is
     every `step5` record on the target's chain; AC-2.2 extracts the base gate with `git archive`;
     AC-2.5 has three cases (a `step3` record holding `"grok"` falls through, a second `step5`
     record holding `"grok"` blocks, an invalid record governs over `"grok"`); AC-11.1 names its
     carve-out file by file. Design v1.2 §D2's inherited no-`jq` fail-open is gone (merged spec
     AC-6.12).
   - **Committed files Task 12 migrates** (merged §D13 item 5, "in the same commit"): the grammar is
     closed, so every committed consumer of the active line moves with it. Executed on a scratch
     copy of `h-mad/` at HEAD `d9574614` with the Task 12 code below applied and the test files
     unedited (copy deleted): 25 committed items fail — 24 in `test_h_mad_tdd_judge.py` (the 14
     `test_fallback_tag` rows, the 6 `test_state_line_escape_and_blocker` rows, the 2
     `test_state_line_empty_values_encode_as_percent` rows, `test_state_line_path_with_space_decodes`
     and `test_cli_state_verb[active]`, all on `ACTIVE_RE.fullmatch`) and
     `test_h_mad_tdd_gate_judge.py::test_symlinked_hook_runs_its_own_trees_judge` (its `_tree_b`
     default state line fails the new ERE). With the two edits Task 12 names applied, the 255 items
     of the seven gate and judge test files pass and `--check-anchors` reads `ANCHORS_OK` on the
     copy.

## Preamble — where and how this plan runs

- **Worktree, not the main checkout.** `~/.claude/skills/h-mad` is a symlink into this main
  checkout (`/Users/kimhawk/orca/skills/h-mad`), and so is `~/.claude/hooks/h-mad-tdd-gate.sh`
  (`ls -la` → `-> /Users/kimhawk/orca/skills/h-mad/hooks/h-mad-tdd-gate.sh`). Every edit on the
  main checkout would change the live skill mid-run. At 5c the branch `feature/216-grok-codex-fallback`
  is created **as a git worktree** (`hmad-dispatch worktree-create` or `git worktree add`), and every
  task below runs inside that worktree. The number 216 is the next free one: the highest
  `feature/NNN-` number referenced under `docs/` at `507214d` is 215
  (`feature/215-regression-provenance-ledger`).
- **The base sha.** `BASE_SHA` is the commit the branch forks from, the parent of the 5c commit. It
  is derived once, in Task 1, as
  `git rev-parse "$(python3 ~/.claude/skills/h-mad/scripts/h_mad_baseline_sha.py --branch feature/216-grok-codex-fallback | sed -n 's/.* sha=\([0-9a-f]*\).*/\1/p')^"`
  (read the `BASELINE:` token first; only `OK` carries `sha=`; any other token, `UNVERIFIED` or
  `NONE` included, halts Task 1 with `HALT: BASELINE not OK` and nothing is derived), and written into
  `h-mad/tests/grokfixtures.py` as a 40-hex constant. The parent is used, never the 5c commit
  itself, because the parent is a `main` commit and stays reachable after any merge style. AC-2.2,
  AC-8.1 and Task 16's node-id floor compare against it. **Re-pinned after the rebase (v1.4).** The
  committed constant still reads `5a9cd8ed693202e0291a9c6d5a3a63207b1f1b14`, the pre-rebase fork
  point. The same derivation now prints `BASELINE: OK sha=4f705707…`, whose parent is
  `8ef6009f9491796d5d16b96a54e3b3185a8a6f19`, the `codex-tdd-gate-defects` merge. Task 12 re-pins
  the constant to that value. No committed reader of the constant changes result: `test_grok_fixtures.py`
  checks only its 40-hex shape, and `test_h_mad_review_evidence_grok.py` runs `git show BASE_SHA:h-mad/scripts/h_mad_review_evidence.py`,
  and `git diff --quiet 5a9cd8ed 8ef6009f -- h-mad/scripts/h_mad_review_evidence.py` exits 0.
  **The second constant (done, v1.5).** v1.4 said Task 3's `test_h_mad_assemble_tdd_agent.py`
  "pins its own `507214d` and is untouched"; that list missed it. Its module constant
  `BASE_SHA` (line 20; used by `git archive BASE_SHA h-mad` at line 77 for the no-agent comparison,
  AC-8.1) was re-pinned from `"507214d"` to `"8ef6009f"` by commit `f2ff9261`
  (`git show f2ff9261` → one line changed in that one file). It is an 8-hex prefix, not the 40-hex
  `grokfixtures.BASE_SHA`; both name `8ef6009f9491796d5d16b96a54e3b3185a8a6f19`, and Task 16
  step 3 checks that they agree. The file is not tracked at `8ef6009f` (`git cat-file -e
  8ef6009f:h-mad/tests/test_h_mad_assemble_tdd_agent.py` fails; Task 3's commit `23aa6a98` added
  it), so it is outside AC-11.1's pre-existing set.
- **Both coupled suites, per task.** Every task's GREEN verification runs, from the worktree root,
  `/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts`
  in full, never the scoped file alone. The three paths are named explicitly: they are the root
  `pytest.ini`'s `testpaths`, whose comment records that the two-path form silently dropped the
  tests in `handoff/scripts/` (5 `test_*.py` files there at `76b2501`, two of which reference
  `hmad-dispatch`), and naming them keeps every run independent of `testpaths`, including Task 16's
  base collect (which runs on the whole tree at `BASE_SHA`, `pytest.ini` included). The one
  environment-dependent failure recorded in the plan baseline,
  `h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`,
  is the only failure a task may leave, and only for its recorded reason.
- **Codex authors 5d/5e.** If codex is out during this feature's own Phase 5, the fallback is
  today's `codex_status=exhausted` path: this feature's `fallback_agent` does not exist on the live
  skill until merge.
- **The gate's judge and name map are tree-relative** (since the `codex-tdd-gate-defects` merge,
  replacing design V11's main-tree derive script). The Claude hook finds
  `h-mad/scripts/h_mad_tdd_judge.py` beside its own realpath (`_find_judge`), and the judge's
  `NAME_MAP` is `h_mad_derive_test_path.sh` in its own directory, so a worktree hook under test
  runs the worktree's judge and name map. This feature does not edit the name map.
- **Dispatched agent CLIs are not script dependencies** (`h-mad/invariants.base.md`, amended at
  `0b3f969`). No test in this plan runs a real `grok`; every grok dispatch in the suite goes through
  `h-mad/tests/stubs/grok`. Task 17 runs the real CLI once, by hand, and is not a test.

### Conventions every task follows

1. **Harness helpers.** Wrapper tests import `run`, `run_fn`, `_bindir` and `WRAPPER` from
   `test_hmad_dispatch` (all four are module-level there: `WRAPPER` at line 13, `run` 166, `run_fn`
   181, `_bindir` 193), in the same `from test_hmad_dispatch import …` form that
   `test_hmad_dispatch_exec.py` uses for its own four names (`SKILL_MD_TEXT, _bindir, _git_repo,
   run`). `_bindir(tmp_path, names)` symlinks `stubs/<name>` for each name and the real `jq` as
   `bin/jq`, and `run()` puts the bindir first on PATH, then `/usr/bin:/bin`. **Rule for every `jq`
   shim placed in a bindir that already links the real `jq`:** the test first reads the link's
   absolute target (`real_jq = os.path.realpath(bindir / "jq")`, taken before anything is
   unlinked), then unlinks `bin/jq` (present whenever `shutil.which("jq")` finds one) and writes the
   shim at that same path. A shim that delegates to the real `jq` execs `real_jq` by its absolute
   path, never a bare `jq`, which would now resolve to the shim itself. `/usr/bin/jq` exists on this
   host, so a shim placed anywhere else on PATH is either shadowed by the real `jq` link or shadows
   the wrong entry. The members today are three: Task 8 test 7, Task 9 test 22 and Task 10 test 9
   (non-delegating shims in `_bindir`'s bindir). Task 12's `jq` shim (v1.3 test 11) is gone with the
   re-plan: the merged gate runs no `jq`. A new shim follows the rule whether or not it is listed.
2. **Tool-absent cells run on a farm, never through `run()`.** `grokfixtures.usr_bin_farm(tmp_path,
   absent, stubs)` links the named stubs first, then every `/usr/bin` entry whose name is neither in
   `absent` nor already linked. `grokfixtures.farm_env(farm, **extra)` returns an env whose `PATH` is
   exactly `<farm>:/bin`, with `BASH_ENV` and `ENV` removed. A farm cell calls
   `subprocess.run(["bash", str(WRAPPER), …], env=cell_env)` itself, first asserts
   `subprocess.run(["bash", "-c", "command -v jq"], env=cell_env).returncode != 0` (or the named
   tool) with the same dict, and last asserts `"command not found" not in stderr`.
3. **Lazy symbol access in RED.** A test file whose target symbol does not exist yet imports the
   module, never the symbol (`import h_mad_review_evidence as ev`, then `ev.scan_grok` inside each
   test), so a RED is one failure per test, never one collection error. Task 1's tests import
   `grokfixtures` inside a function-scoped fixture `gf` for the same reason.
4. **Landed literals.** Each task's "Landed literals" block lists lines that are `find` anchors of
   Task 14's mutation rows. They land byte-for-byte as written (indentation included), each exactly
   once in its file, because the harness refuses an anchor that matches zero or two times.
5. **Committed anchors.** Every committed anchor in a file this plan edits stays byte-identical, and
   no new line contains one as a substring (design §"Existing mutation anchors", rules 1 and 2).
   `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json`
   read at `507214d`: `ANCHORS: ANCHORS_OK specs=99 mutations=907 ok=907 drifted=0 unreadable=0
   skipped=0 unclassifiable=0`; re-read for v1.4 at HEAD `d9574614` (after the rebase onto the
   judge-gate merge and Tasks 1–11, 13): `ANCHORS: ANCHORS_OK specs=107 mutations=1005 ok=1005
   drifted=0 unreadable=0 skipped=0 unclassifiable=0`.
   The committed sweep test
   `h-mad/tests/test_h_mad_mutation_harness.py::test_committed_mutation_harness_anchor_sweep_is_ok`
   runs in every task's full-suite run and enforces this.
6. **Mutation spec form.** `root` is `"../.."` (the `h-mad/` directory, as in
   `exec_last_step.json`), `file` keys are `scripts/…` / `hooks/…`, `test` keys are
   `tests/<file>.py::<name>`, `command` and `target_command` lead with `python3.11` (house form:
   `command[0]` of each `h-mad/tests/mutation-specs/*.json`, counted with `uniq -c`, reads 98
   `python3.11`, 8 `/opt/anaconda3/bin/python` and 1 `/opt/anaconda3/bin/python3.11` at `6277d703`;
   unit: files, 107 in all. The six committed specs Task 14 re-runs lead with
   `/opt/anaconda3/bin/python`, which is harmless because `python3.11` resolves to
   `/opt/anaconda3/bin/python3.11` on this host). Score on the `MUTATION:` token, never `$?`.
7. **Probes are deleted.** A scratch probe written to confirm a suspected defect is deleted after it
   answers.

---

## Task 1: grok-fixtures-and-stubs

**Production file**: `h-mad/tests/fixtures/grok-stream-json.2026-09-28.ndjson` (new, a byte copy of
F0), `h-mad/tests/grokfixtures.py` (new), `h-mad/tests/stubs/grok` (new, executable),
`h-mad/tests/stubs/codex` and `h-mad/tests/stubs/agy` (modified: one opt-in knob each). All are test
support; none is shipped behaviour.
**Test file**: `h-mad/tests/test_grok_fixtures.py`
**Task shape**: `new-behaviour`

**Description**: Copy F0 (`docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson`,
sha256 `72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569`, re-read at `507214d`)
byte-for-byte into the skill, so the suite runs from a clone holding the skill alone. Build every
spec and design fixture from that copy in one module. Add the grok stub, and the opt-in
`HMAD_STUB_CLAUDE_ENV_CAPTURE` knob to the codex and agy stubs (design Test Strategy). No
production code changes in this task, so the full suite after it is the evidence that the knob left
every existing test unchanged. `test_grok_fixture_copy_hash` lives here rather than in
`test_grok_two_instruments.py` (design Test Plan), so the copy is pinned by the task that creates it.

**Code structure**:
```python
# h-mad/tests/grokfixtures.py — stdlib only
F0_COPY: Path            # <tests>/fixtures/grok-stream-json.2026-09-28.ndjson
F0_SHA256 = "72f6258734f184ae999f84273b5abe3711202a1a8f43f392143173c8364fe569"
BASE_SHA: str            # 40-hex, derived as the Preamble states
STUBS: Path              # <tests>/stubs

def f0_lines() -> list[str]: ...        # asserts sha256(F0_COPY) == F0_SHA256 before returning
def f0_text() -> str: ...               # every builder returns text ending in one "\n"
def f_trunc() -> str: ...               # F0 minus its single `end` line
def f_trunc_nostatus() -> str: ...      # F-TRUNC minus the last three `text` events (STATUS / : / " DONE")
def f_notools() -> str: ...             # every tool_call_update.status set to null
def f_notext() -> str: ...
def f_notooltext() -> str: ...          # 83 lines
def f_decoy() -> str: ...               # spec v1.4 F-DECOY placement (design Test Plan)
def f_beat() -> str: ...                # "#hmad-beat 2026-09-28T00:00:00Z grok running 120s" + blank line between events
def f_spaced() -> str: ...              # json.dumps(json.loads(line)) per line (default separators)
def f_twomodel() -> str: ...            # end.modelUsage gains "grok-4.7-mini"
def f_shared() -> str: ...              # f0_text() + f_trunc()
def f_second_model() -> str: ...        # f0_text() + F0 whose end.modelUsage key is renamed "grok-other-build"
def f_sep(kept: str) -> str: ...        # kept in {"usage", "tool_call", "tool_call_update"}; 104 / 103 / 105 lines
def ac_4_10_stream() -> str: ...        # F-NOTOOLS minus every `text` event; 89 lines
def f0_with_completed(n: int) -> str: ...  # F0 with extra completed ids "call-extra-<i>" before `end`, n total
def agy_transcript() -> str: ...        # two agy step_update lines: view_file ACTIVE, then DONE
def mixed_agy_f0() -> str: ...          # agy_transcript() + f0_text()
def agy_init_f0() -> str: ...           # '{"event":"init"}\n' + f0_text()
def banner_then_f0() -> str: ...        # "OpenAI Codex v0.145.0\n" + f0_text()
def window_edge_log() -> str: ...       # "x" * 4095 + "\n" + "OpenAI Codex v0.145.0\n" + f0_text()
def depth_line(k: int) -> str: ...      # '{"type":"text","data":"x","n":' + "[" * k + "]" * k + "}\n"
def f_deep(k: int) -> str: ...          # F-DEEP64 / F-DEEP65 (design Test Plan)
def deep_line_200k() -> str: ...        # depth_line(200_000)
def usr_bin_farm(tmp_path: Path, absent: tuple[str, ...], stubs: tuple[str, ...]) -> Path: ...
def farm_env(farm: Path, **extra: str) -> dict[str, str]: ...
def wrapper_fn_in_env(script: str, env: dict[str, str]) -> subprocess.CompletedProcess: ...
    # run_fn's source-stripping (reuses test_hmad_dispatch.WRAPPER and _MAIN_LINE) on a caller env
```

- A line F0 carries unmodified keeps its original bytes. A line a builder modifies is re-serialized
  with `json.dumps(obj, separators=(",", ":"), ensure_ascii=False)`, so only `f_spaced()` changes
  spacing.
- `agy_transcript()` builds each line as the `_tool` helper of `test_h_mad_review_evidence.py`
  does: `json.dumps({"event": "step_update", "step_update": {"step_type": "tool", "tool_name":
  "view_file", "state": <state>, "tool_info": {"name": "view_file", "parameters": {}}}})`.
- `f0_with_completed(3)` copies F0's `search_replace` `tool_call` and its `completed`
  `tool_call_update`, rewrites both `toolCallId`s to `call-extra-3`, and inserts the pair before the
  `end` line.
- `f_deep(k)` is `f_trunc()` followed by a `text` event `DEEP`, a `tool_call_update` with
  `toolCallId` `deep` and `status` `completed`, and an `end` event with `stopReason` `deep`; each of
  the three carries an `"n"` member of k nested lists, so each event's depth is k.

The grok stub (`h-mad/tests/stubs/grok`, `#!/usr/bin/env bash`) models what the wrapper consumes:

```bash
printf 'grok %s\n' "$*" >> "${HMAD_STUB_CAPTURE:-/dev/null}"
# HPW_AGENT_BACKEND to HMAD_STUB_ENV_CAPTURE, exactly the codex/agy stubs' line
# sorted exported CLAUDE* names to HMAD_STUB_CLAUDE_ENV_CAPTURE (compgen -e + case), when set
# copy the file after --prompt-file to HMAD_STUB_GROK_PROMPT_CAPTURE at invocation, when set
# write HMAD_STUB_GROK_STREAM to stdout line by line, when set
# sleep HMAD_STUB_GROK_SLEEP after emitting, when set
exit "${HMAD_STUB_GROK_RC:-0}"
```

The codex and agy stubs each gain, after their existing `HMAD_STUB_ENV_CAPTURE` block and
touching none of its lines:

```bash
if [ -n "${HMAD_STUB_CLAUDE_ENV_CAPTURE:-}" ]; then
  for _n in $(compgen -e); do case "$_n" in CLAUDE*) printf '%s\n' "$_n" ;; esac; done \
    | sort > "$HMAD_STUB_CLAUDE_ENV_CAPTURE"
fi
```

**Tests** (12 collected items):
1. `test_grok_fixture_copy_hash` — sha256 of the copy equals `F0_SHA256`; reads nothing outside `h-mad/`.
2. `test_f0_type_counts_match_the_spec` — 110 lines; `thought` 70, `text` 21, `available_commands` 9,
   `usage` 3, `tool_call_update` 4, `tool_call` 2, `end` 1.
3. `test_derived_fixture_line_counts` — `f_notooltext` 83, `ac_4_10_stream` 89, `f_sep("usage")` 104,
   `f_sep("tool_call")` 103, `f_sep("tool_call_update")` 105, `f_trunc` 109 (unit: lines).
4. `test_depth_line_builder_gives_the_requested_depth` — for k in 64 and 65, walking `"n"` reaches an
   empty list after exactly k list levels.
5. `test_grok_stub_replays_the_stream_and_copies_the_prompt_file`
6. `test_grok_stub_exits_with_the_configured_rc`
7. `test_stub_claude_env_knob_records_names_when_set[codex|agy|grok]` (3 items) — with `CLAUDECODE`
   and `CLAUDE_EFFORT` exported, the capture file holds both names, sorted.
8. `test_stub_claude_env_knob_is_inert_when_unset[codex|agy]` (2 items) — no capture file is created.
9. `test_usr_bin_farm_hides_the_absent_tool` — in `farm_env(usr_bin_farm(tmp, ("jq",), ()))`,
   `command -v jq` fails and `command -v env` succeeds.

**Expected RED split**: 10 failing, 2 passing. **Regression guards**: both items of
`test_stub_claude_env_knob_is_inert_when_unset` (they pass before the knob exists and must keep
passing). Every other test fails at RED because `grokfixtures` or `stubs/grok` does not exist yet.

**Acceptance Criteria**:
- [ ] Spec §"Fixtures" (F0 entry): the in-skill copy's sha256 equals F0's
      (`test_grok_fixture_copy_hash`).
- [ ] Every fixture the spec names (F-TRUNC, F-NOTOOLS, F-NOTEXT, F-NOTOOLTEXT, F-DECOY, F-BEAT,
      F-SPACED, F-TWOMODEL, F-SHARED) and every design fixture above is built from the copy.
- [ ] The knob changes nothing when unset; the full suite after this task matches the base run.

**Mutation rows**: none (test support).

**Dependencies on other tasks**: None

---

## Task 2: state-schema-fallback-agent

**Production file**: `h-mad/scripts/h_mad_state_schema.json`
**Test file**: `h-mad/tests/test_h_mad_state_fallback_agent.py`
**Task shape**: `new-behaviour`

**Description**: Add the optional `fallback_agent` property directly after `codex_status` in the
per-feature record's `properties` (design D1). It is not added to `required`. The historical schema
is untouched.

**Code structure**:
```json
"fallback_agent": {
  "description": "Who covers Phase-5 authoring when Codex is out. The field is read only when codex is out: HMAD_CODEX_UNAVAILABLE non-empty, codex_status unavailable|exhausted, or codex not on PATH. Absent, null and 'claude' are equivalent: Claude covers, test-first, as before. HMAD_CODEX_UNAVAILABLE does not override 'grok'; a one-off Claude escape needs --set fallback_agent=claude. Audit-leg routing to grok (audit-cycle --surfaces agy,grok) is prose-enforced by SKILL.md, and no script reads this field for it.",
  "enum": ["grok", "claude", null]
}
```

**Tests** (8 collected items). Every test that writes first creates the state file with the two
bytes `{}` (`state = tmp_path / "state.json"; state.write_text("{}")`): `--create` means "create
the record if absent" and refuses a missing file (`ERROR: no such state file`, rc 2, executed by the
cycle-1 teammate), so without it all 8 items would fail for a reason unrelated to the schema.
1. `test_fallback_agent_set_writes_a_strict_record[grok|claude|null]` (3) — on the pre-created
   `{}` file, `h_mad_state_write.py --feature feat --create` with that path, then
   `--set fallback_agent=<v>`: rc 0, the stored value is
   `"grok"`, `"claude"` or JSON `null`, and `h_mad_state_validate.classify(record) == "strict"` (AC-1.1).
2. `test_fallback_agent_set_refuses_values_outside_the_enum[codex|agy|Grok]` (3) — rc non-zero and
   the state file byte-identical (AC-1.2).
3. `test_incident_replay_tiers_unchanged_by_fallback_agent` — for every record in
   `h-mad/tests/fixtures/state_incident_replay.json`, `classify()` under the current schema equals
   `classify()` under a temp copy of the schema with `fallback_agent` removed from `properties` by
   `properties.pop("fallback_agent", None)`, never `del` (at RED the key does not exist yet, `del`
   would raise `KeyError`, and the 4/4 split would break) (`monkeypatch.setattr` on
   `STRICT_SCHEMA`, `_schemas` and `_validators`) (AC-1.3).
4. `test_fallback_agent_description_states_the_four_facts` — the description contains
   `read only when codex is out`, `are equivalent`, `HMAD_CODEX_UNAVAILABLE does not override` and
   `prose-enforced` (AC-1.4).

**Expected RED split**: 4 failing, 4 passing. **Regression guards**: the three
`test_fallback_agent_set_refuses_values_outside_the_enum` items (today they are refused as an
undeclared key; after GREEN, by the enum) and `test_incident_replay_tiers_unchanged_by_fallback_agent`.

**Acceptance Criteria**:
- [ ] AC-1.1: `--set fallback_agent=grok|claude|null` writes, and the record validates strict.
- [ ] AC-1.2: `=codex`, `=agy`, `=Grok` are refused; the file is byte-identical.
- [ ] AC-1.3: every incident-replay record keeps its tier.
- [ ] AC-1.4: the description states the four facts.

**Mutation rows**: none (design has no schema row).

**Dependencies on other tasks**: None

---

## Task 3: assemble-tdd-agent

**Production file**: `h-mad/scripts/h_mad_assemble_tdd.py`
**Test file**: `h-mad/tests/test_h_mad_assemble_tdd_agent.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_assemble_tdd.py:main` → `command_block(agent=args.agent, timeout=timeout)`
**WIRE-PIN**: `h-mad/tests/test_h_mad_assemble_tdd_agent.py::test_agent_grok_block_names_exec_grok_with_1500`

**Description**: FR-8 / design D9 / plan W10. `--agent {codex,grok}` (default `codex`); `--timeout`
becomes presence-judged (`default=None`, resolved to 900, or 1500 for grok). `command_block` keeps
its anchored first element byte-identical and derives the grok block from it. State is never read.

**Code structure**:
```python
def command_block(
    *, feature: str, module: str, phase: str, prompt: Path, out: Path,
    log: Path, timeout: int, python: str, test_path: str,
    project_root: Path, model: str | None = None, effort: str | None = None,
    agent: str = "codex",
) -> str: ...
# body: the existing list, with `return "\n".join([` changed to `block = "\n".join([`, then:
#   prefix = "hmad-dispatch exec codex "
#   if agent != "codex":
#       if not block.startswith(prefix):          # never `assert`: `python -O` strips it
#           raise RuntimeError("command block no longer starts with the codex line")
#       block = f"hmad-dispatch exec {agent} " + block[len(prefix):]
#   return block
```

Landed literals (Task 14 rows T1, W10a and WR3):
```python
    ap.add_argument("--agent", choices=("codex", "grok"), default="codex")
    ap.add_argument("--timeout", type=int, default=None)
    timeout = args.timeout if args.timeout is not None else (1500 if args.agent == "grok" else 900)
        agent=args.agent,
```
`main()`'s `print(command_block(` call (`h-mad/scripts/h_mad_assemble_tdd.py:538-542` at `507214d`)
changes `timeout=args.timeout` to `timeout=timeout` on its second argument line, and gains the line
`        agent=args.agent,` directly after
`        python=args.python, test_path=args.test_path, project_root=args.project_root,`, before
`    ))`. That line lands exactly once in the file. The anchored line
`        f"hmad-dispatch exec codex {q(str(prompt))}{over} \\",` (two rows of `assemble_tdd.json`) is
unchanged.

**Tests** (11 collected items; the CLI is driven by subprocess, as `run_cli` in
`test_h_mad_assemble_tdd.py` does, with its `PLAN` text written to `tmp_path`):
1. `test_no_agent_output_is_byte_identical_to_base` — `git archive BASE_SHA h-mad | tar -x -C <tmp>`;
   both assemblers run with identical arguments; stdout equal after replacing the base run's own
   `SKILL_DIR` prefix, and the prompt files byte-equal (AC-8.1).
2. `test_agent_grok_block_names_exec_grok_with_1500` — the block's first line begins
   `hmad-dispatch exec grok ` and contains `--timeout 1500` (AC-8.2). WIRE-PIN.
3. `test_agent_grok_explicit_timeout_wins[--timeout 600|--timeout 900|--timeout=900|--ti 900]`
   (4) — each block contains `--timeout <n>` and never `--timeout 1500` (AC-8.2).
4. `test_agent_codex_default_timeout_is_900` (AC-8.2 last clause).
5. `test_prompt_file_is_agent_independent` — equal sha256 for `--agent codex` and `--agent grok` (AC-8.3).
6. `test_unknown_agent_exits_2_and_writes_no_prompt` — `--agent gpt`: rc 2, stderr contains
   `invalid choice: 'gpt'`, no prompt file (AC-8.4).
7. `test_state_fallback_agent_is_not_read` — `docs/.bkit-memory.json` under the project root holds
   `fallback_agent: "grok"`; with no `--agent` the block names `exec codex` (AC-8.5).
8. `test_command_block_derives_grok_from_the_codex_line` — `command_block(..., agent="grok")` starts
   `hmad-dispatch exec grok ` and every later line equals the codex block's.

**Expected RED split**: 9 failing, 2 passing. **Regression guards**:
`test_no_agent_output_is_byte_identical_to_base` and `test_state_fallback_agent_is_not_read`.
**WIRE-PIN RED reason**: argparse refuses `--agent` (rc 2), so the assertion on the block's first
line fails. It is a CLI subprocess, so no import of a missing symbol is involved.
**Wire-scoped revert**: drop `agent=args.agent` from the `command_block(...)` call in `main()`
only; the pin fails because the block names `exec codex`. Executed and scored as row WR3 (Task 14,
`grok_wire_reverts.json`).
**Force-fire**: row W10a (Task 14).

**Acceptance Criteria**:
- [ ] AC-8.1: no `--agent` → stdout and prompt file byte-identical to the base.
- [ ] AC-8.2: grok block with `--timeout 1500`; explicit 600 and 900 win; codex default 900.
- [ ] AC-8.3: prompt files equal across agents.
- [ ] AC-8.4: `--agent gpt` → rc 2, usage error, no prompt file.
- [ ] AC-8.5: state `fallback_agent: "grok"` does not change the default block.

**Mutation rows** (authored and run in Task 14): T1, W10a (`assemble_tdd_agent.json`) and WR3
(`grok_wire_reverts.json`) — 3 rows.

**Dependencies on other tasks**: Task 1

---

## Task 4: resolved-model-grok

**Production file**: `h-mad/scripts/h_mad_resolved_model.py`
**Test file**: `h-mad/tests/test_h_mad_resolved_model_grok.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_resolved_model.py:main` → `grok_from_log`
**WIRE-PIN**: `h-mad/tests/test_h_mad_resolved_model_grok.py::test_grok_reads_the_model_from_the_last_end`

**Description**: FR-9 / design D10 / plan W11. `choices` gains `grok`; the `--log` help becomes
"(codex, grok)"; `grok_from_log` reads the **last** `end` event and refuses every other case through
`_fail()`. The grok branch is the first branch of `main()`. `import json` is added (the module
imports `argparse`, `glob`, `os`, `re`, `sys` and `Path` at `507214d`, not `json`).

**Code structure**:
```python
def grok_from_log(path: str | None) -> None:
    if path is None:
        _fail("a grok model is read only from its stream's `end` event; no grok config "
              "source has been probed")
    p = Path(path)
    if not p.is_file():
        _fail(f"no such grok log: {path}")
    last_end = None
    for line in p.read_text(encoding="utf-8", errors="replace").split("\n"):
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if isinstance(event, dict) and event.get("type") == "end":
            last_end = event
    if last_end is None:
        _fail(f"{path} has no `end` event (killed, still running, or copied mid-write)")
    usage = last_end.get("modelUsage")
    if not isinstance(usage, dict) or not usage:
        _fail(f"the last `end` event in {path} carries no non-empty `modelUsage` object")
    keys = sorted(usage)
    if len(keys) != 1:
        _fail(f"the last `end` event in {path} names {len(keys)} models: {', '.join(keys)}")
    _emit("grok", keys[0], "-", "resolved", path)
```

Landed literals (Task 14 rows R1, R2, W11):
```python
    ap.add_argument("agent", choices=("codex", "agy", "grok"))
    if a.agent == "grok":
            last_end = event
    if len(keys) != 1:
```
In `main()`, `    if a.agent == "grok":` / `        grok_from_log(a.log)` / `        return 0` sits
before `    if a.agent == "codex":`. The anchored `    if a.log:` + comment line
(`resolved_model.json`) is unchanged, and no new line reads `if a.log:`.

**Tests** (9 collected items, all by subprocess on the CLI, plus one through the wrapper):
1. `test_grok_reads_the_model_from_the_last_end` — on F0: stdout exactly
   `RESOLVED-MODEL agent=grok model=grok-4.7-build effort=- resolved=1 source=<the F0 path>`, rc 0
   (AC-9.1). WIRE-PIN.
2. `test_grok_refusals_exit_2_unknown[f_trunc|f_twomodel|no_log|missing_path]` (4) — rc 2, stderr
   contains `RESOLVED-MODEL: UNKNOWN`; the F-TWOMODEL message names `grok-4.7-build` and
   `grok-4.7-mini` (AC-9.2).
3. `test_grok_empty_model_usage_refuses` — a last `end` whose `modelUsage` is `{}` → rc 2, UNKNOWN.
4. `test_grok_resolves_from_the_last_end_on_a_shared_log` — F-SHARED → `model=grok-4.7-build` (AC-9.3).
5. `test_grok_second_dispatch_model_wins` — `f_second_model()` → `model=grok-other-build` (AC-9.3).
6. `test_hmad_dispatch_resolved_model_grok_passes_through` — `run(["resolved-model", "grok", "--log",
   <F0>])` prints the same line (the wrapper forwards `"$@"`, plan P10).

**Expected RED split**: 9 failing, 0 passing. **Regression guards**: none in this file; AC-9.4 is the
existing `test_h_mad_resolved_model.py` in the full-suite run.
**WIRE-PIN RED reason**: argparse refuses `grok` (rc 2, `invalid choice`), so the stdout assertion
fails. Subprocess only, no import of `grok_from_log`.
**Wire-scoped revert**: delete the three-line `if a.agent == "grok":` branch from `main()` only
(`grok_from_log` intact); `grok` falls into the agy path, which refuses `--log`, and the pin fails.
Executed and scored as row WR4 (Task 14, `grok_wire_reverts.json`), whose `find` is the three
landed lines `    if a.agent == "grok":` / `        grok_from_log(a.log)` / `        return 0`.
**Force-fire**: row W11 (Task 14).

**Acceptance Criteria**:
- [ ] AC-9.1: F0 → the exact `RESOLVED-MODEL agent=grok …` line, rc 0.
- [ ] AC-9.2: F-TRUNC, F-TWOMODEL (both keys named), no `--log`, nonexistent path → rc 2 UNKNOWN.
- [ ] AC-9.3: F-SHARED resolves from the last `end`; a second dispatch's model wins.
- [ ] AC-9.4: `test_h_mad_resolved_model.py` passes unchanged (Task 16).

**Mutation rows** (Task 14): R1, R2, W11 (`resolved_model_grok.json`) and WR4
(`grok_wire_reverts.json`) — 4 rows.

**Dependencies on other tasks**: Task 1

---

## Task 5: scan-grok

**Production file**: `h-mad/scripts/h_mad_review_evidence.py`
**Test file**: `h-mad/tests/test_h_mad_review_evidence_scan_grok.py`
**Task shape**: `new-behaviour`

**Description**: FR-6 reader / design D6: `_GROK_TYPES`, `GROK_MAX_DEPTH`, the iterative
`_json_deeper_than`, `scan_grok`, `CODEX_BANNER_HEAD` and `codex_banner_in_head`. Two places in
`scan()` change, and nothing else in `scan()` moves:
- §"Deviations from design v1.2", item 1: `h-mad/scripts/h_mad_review_evidence.py:131`
  `        except (ValueError, TypeError):` becomes
  `        except (ValueError, TypeError, RecursionError):`.
- §"Deviations from design v1.2", item 4: `h-mad/scripts/h_mad_review_evidence.py:141`
  `        if event.get("event") in _AGY_EVENTS:` becomes the two lines
  `        event_name = event.get("event")` /
  `        if isinstance(event_name, str) and event_name in _AGY_EVENTS:`, and the following
  `            agy_events += 1` stays byte-identical.
`scan_codex_text()` is untouched. `main()` is Task 6.

**Code structure**:
```python
_GROK_TYPES = frozenset({"thought", "text", "available_commands", "tool_call",
                         "tool_call_update", "usage", "end"})
GROK_MAX_DEPTH = 64
CODEX_BANNER_HEAD = 4096


def codex_banner_in_head(text: str) -> bool:
    return _CODEX_HEADER_RE.search(text[:CODEX_BANNER_HEAD]) is not None


def _json_deeper_than(value: object, bound: int) -> bool:
    stack = [(value, 0)]
    while stack:
        node, depth = stack.pop()
        if depth > bound:
            return True
        if isinstance(node, dict):
            stack.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, list):
            stack.extend((child, depth + 1) for child in node)
    return False


def scan_grok(log_text: str) -> dict | None:
    seen = False
    tools: set = set()
    ok: set = set()
    thinking = 0
    complete = False
    stop_reason = None
    for line in log_text.split("\n"):
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if not isinstance(event, dict):
            continue
        if _json_deeper_than(event, GROK_MAX_DEPTH):
            continue
        t = event.get("type")
        if not (isinstance(t, str) and t in _GROK_TYPES):
            continue
        seen = True
        call_id = event.get("toolCallId")
        if t in ("tool_call", "tool_call_update") and isinstance(call_id, str):
            tools.add(call_id)
        if t == "tool_call_update" and event.get("status") == "completed" and isinstance(call_id, str):
            ok.add(call_id)
        if t == "usage":
            usage = event.get("usage")
            value = usage.get("reasoning_tokens") if isinstance(usage, dict) else None
            if type(value) in (int, float):
                thinking += int(value)
        if t == "end":
            complete = True
            reason = event.get("stopReason")
            stop_reason = reason if isinstance(reason, str) else None
    if not seen:
        return None
    return {"tools": len(tools), "ok": len(ok), "unresolved": len(tools) - len(ok),
            "thinking": thinking, "complete": complete, "stop_reason": stop_reason}
```

- The thinking test is spelled `type(value) in (int, float)`, never `scan()`'s anchored
  `isinstance(value, (int, float)) and not isinstance(value, bool)` (anchor rule 2,
  `audit_effort.json`).
- Landed literals (Task 14 rows E1, E4–E10), each exactly once in the file:
  `        if t == "tool_call_update" and event.get("status") == "completed" and isinstance(call_id, str):`,
  `isinstance(t, str) and t in _GROK_TYPES`, `CODEX_BANNER_HEAD = 4096`, `GROK_MAX_DEPTH = 64`,
  `except (ValueError, RecursionError):`, `if _json_deeper_than(event, GROK_MAX_DEPTH):`, and
  `        except (ValueError, TypeError, RecursionError):` (E9; it does not contain E7's `find` as a
  substring, so E7 still matches once), and
  `        if isinstance(event_name, str) and event_name in _AGY_EVENTS:` (E10; it does not contain
  E4's `find` as a substring, so E4 still matches once).

**Tests** (17 collected items; `import h_mad_review_evidence as ev`, symbols read inside tests):
1. `test_scan_grok_counts_f0` — tools 2, ok 2, unresolved 0, thinking 121, complete True,
   stop_reason `end_turn`.
2. `test_scan_grok_counts_f_notools` — tools 2, ok 0, unresolved 2, complete True.
3. `test_scan_grok_marks_f_trunc_incomplete` — complete False, ok 2, tools 2, stop_reason None.
4. `test_scan_grok_is_none_without_a_grok_event[agy|codex_banner|empty|bogus_type]` (4) —
   `agy_transcript()`, `"OpenAI Codex v0.145.0\nexec\n"`, `""`, `'{"type":"bogus"}\n'` → `None`.
5. `test_scan_grok_ok_ignores_a_completed_substring_in_text` — F0 plus one `text` event whose
   `data` is `"status":"completed"` → ok 2 (AC-6.4).
6. `test_scan_grok_survives_malformed_type_lines` — F0 with `{"type":[]}`, `{"type":{}}`,
   `{"type":1}`, `{"type":null}` and `deep_line_200k()` placed before the first event and again
   between two events → counts equal F0's.
7. `test_scan_grok_depth_boundary[64|65]` (2) — `depth_line(64)` → not `None`; `depth_line(65)` → `None`.
8. `test_scan_grok_key_order_and_bogus_type` — `{"meta":1,"type":"text","data":"x"}` → not `None`;
   `{"meta":1,"type":"bogus","data":"x"}` → `None` (AC-5.2b, Python half).
9. `test_codex_banner_in_head_window_edge` — `CODEX_BANNER_HEAD == 4096`;
   `codex_banner_in_head(window_edge_log())` is False; `codex_banner_in_head(banner_then_f0())` is True.
10. `test_scan_unchanged_on_f0` — `ev.scan(f0_text())` has `agy_events == 0` and `tools == 0` (AC-6.5).
11. `test_scan_survives_a_200k_deep_line` — `ev.scan(deep_line_200k() + f0_text())` equals
    `ev.scan(f0_text())`. The call sits in a `try` block whose `except RecursionError` branch calls
    `pytest.fail("scan() raised RecursionError on a 200,000-deep line")`, so the RED and the E9 kill are an assertion in
    the test file, never an uncaught traceback ending in the mutated file (which the harness would
    classify as a crash, not a kill).
12. `test_archreview_evidence_counts_survive_a_200k_deep_line` — `import h_mad_archreview_cycle as
    ar`; `ar._evidence_counts(deep_line_200k() + f0_text())` equals `ev.scan(f0_text())`, with the
    same `pytest.fail` wrapper (the `score --log` member of the class).
13. `test_scan_survives_an_unhashable_event_value` — `ev.scan('{"event":[]}\n' + f0_text())` equals
    `ev.scan(f0_text())`. The call sits in a `try` block whose `except TypeError` branch calls
    `pytest.fail("scan() raised TypeError on an unhashable event value")`, so the RED and the E10
    kill are an assertion in the test file, never an uncaught traceback ending in the mutated file
    (§"Deviations from design v1.2", item 4; the CLI and `measure_effort()` reach this line only
    through `scan()`).

**Expected RED split**: 16 failing, 1 passing. Tests 11 and 12 fail at RED on the `pytest.fail`
(today's `scan()` raises `RecursionError`); test 13 fails at RED on its `pytest.fail` (today's
`scan()` raises `TypeError: unhashable type: 'list'`). **Regression guards**: `test_scan_unchanged_on_f0`.

**Acceptance Criteria**:
- [ ] AC-6.4: `ok` comes from parsed events, never from a substring.
- [ ] AC-6.5: `scan()` on F0 is unchanged (`agy_events == 0`, `tools == 0`); the existing
      `test_h_mad_review_evidence.py` passes unchanged (Task 16).
- [ ] AC-5.2b (Python half): key order is irrelevant; a bogus type is not grok; depth 64 is an event
      and depth 65 is not.
- [ ] Deviation 1 (class rule): `scan()` and `_evidence_counts` survive a 200,000-deep line
      (`test_scan_survives_a_200k_deep_line`,
      `test_archreview_evidence_counts_survive_a_200k_deep_line`).
- [ ] Deviation 4 (class rule): `scan()` survives an unhashable `event` value
      (`test_scan_survives_an_unhashable_event_value`).

**Mutation rows** (Task 14, `review_evidence_grok.json`): E1, E4, E5, E6, E7, E8, E9, E10 — 8 rows.

**Dependencies on other tasks**: Task 1

---

## Task 6: evidence-cli-grok

**Production file**: `h-mad/scripts/h_mad_review_evidence.py`
**Test file**: `h-mad/tests/test_h_mad_review_evidence_grok.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/h_mad_review_evidence.py:main` → `scan_grok`
**WIRE-PIN**: `h-mad/tests/test_h_mad_review_evidence_grok.py::test_cli_f0_prints_grok_evidence_pass`

**Description**: FR-6 CLI / design D6 `main()` / plan W6. Inside the existing
`if counts["agy_events"] == 0:` branch, after its `# #27` comment block and before
`codex = scan_codex_text(text)`, consult the banner, then `scan_grok`. The branch's first two lines
stay byte-identical (the anchor of `review_evidence_format.json`'s first row). The `log` argument's
help gains "or grok streaming-json".

**Code structure** (indentation as landed: the branch body is 8 spaces):
```python
        grok = None if codex_banner_in_head(text) else scan_grok(text)
        if grok is not None:
            if not grok["complete"]:
                print(f"ERROR: {path} is a grok stream with no `end` event (killed, still "
                      "running, or copied mid-write) — no counts published", file=sys.stderr)
                print("EVIDENCE: UNREADABLE reason=truncated_no_end")
                return 2
            verdict = "PASS" if grok["ok"] >= 1 else "NONE"
            line = (f"EVIDENCE: {verdict} tools={grok['tools']} ok={grok['ok']} "
                    f"unresolved={grok['unresolved']} thinking={grok['thinking']} format=grok")
            if grok["stop_reason"]:
                line += f" stop_reason={grok['stop_reason']}"
            print(line)
            return 0
```
Landed literals (Task 14 rows E2, E3, W6): the two lines
`                print("EVIDENCE: UNREADABLE reason=truncated_no_end")` / `                return 2`
(one two-line `find`), and `grok = None if codex_banner_in_head(text) else scan_grok(text)`. The
W6 row anchors the existing `if counts["agy_events"] == 0:` (count 1 at `507214d`).

**Tests** (7 collected items; CLI by subprocess, as `_run` in `test_h_mad_review_evidence.py`):
1. `test_cli_f0_prints_grok_evidence_pass` — stdout exactly
   `EVIDENCE: PASS tools=2 ok=2 unresolved=0 thinking=121 format=grok stop_reason=end_turn`, rc 0
   (AC-6.1). WIRE-PIN.
2. `test_cli_f_notools_prints_none` — `EVIDENCE: NONE tools=2 ok=0 unresolved=2 thinking=121
   format=grok stop_reason=end_turn`, rc 0 (AC-6.2).
3. `test_cli_f_trunc_is_unreadable_without_counts` — stdout `EVIDENCE: UNREADABLE
   reason=truncated_no_end`, rc 2, no `tools=` (AC-6.3).
4. `test_cli_codex_text_output_is_byte_identical_to_base` — for
   `h-mad/tests/fixtures/codex-text-0-exec.log` and `h-mad/tests/fixtures/codex-text-8-exec.log`,
   stdout and rc equal those of `git show BASE_SHA:h-mad/scripts/h_mad_review_evidence.py` run on the
   same file (AC-6.6).
5. `test_cli_banner_then_f0_keeps_codex_output` — on `banner_then_f0()` stdout and rc equal the base
   CLI's on the same bytes (a `CODEXEVIDENCE:` line, then `EVIDENCE: UNREADABLE
   reason=unsupported_format`, rc 2), and no line contains `format=grok` (AC-11.3, CLI arm).
6. `test_cli_mixed_agy_f0_equals_agy_alone` — stdout and rc on `mixed_agy_f0()` equal those on
   `agy_transcript()` (plan W6 force-fire).
7. `test_cli_malformed_type_lines_print_f0_evidence` — the Task 5 malformed fixture prints F0's
   `EVIDENCE:` line, rc 0. It can go GREEN only because Task 5 made `scan()` catch
   `RecursionError` (§"Deviations from design v1.2", item 1): the CLI calls `scan(text)` at `h-mad/scripts/h_mad_review_evidence.py:201`
   before this branch. At RED it fails on today's `EVIDENCE: UNREADABLE reason=unsupported_format`.

**Expected RED split**: 4 failing, 3 passing. **Regression guards**:
`test_cli_codex_text_output_is_byte_identical_to_base`, `test_cli_banner_then_f0_keeps_codex_output`,
`test_cli_mixed_agy_f0_equals_agy_alone`.
**WIRE-PIN RED reason**: the CLI prints today's `EVIDENCE: UNREADABLE reason=unsupported_format`
for F0; an assertion on the CLI's stdout. `scan_grok` already exists from Task 5, and the test is a
subprocess, so no missing symbol is involved.
**Wire-scoped revert**: replace `grok = None if codex_banner_in_head(text) else scan_grok(text)` with
`grok = None` only; the pin fails. Executed and scored as row WR6 (Task 14,
`grok_wire_reverts.json`).
**Force-fire**: row W6 (Task 14).

**Acceptance Criteria**:
- [ ] AC-6.1, AC-6.2, AC-6.3 as the tests state.
- [ ] AC-6.6: the codex-text fixtures print their existing lines, byte for byte.
- [ ] AC-11.3 (CLI arm): the banner wins; no `format=grok`.

**Mutation rows** (Task 14): E2, E3, W6 (`review_evidence_grok.json`) and WR6
(`grok_wire_reverts.json`) — 4 rows.

**Dependencies on other tasks**: Task 5

---

## Task 7: audit-cycle-grok-shapes

**Production file**: `h-mad/scripts/h_mad_audit_cycle.py`
**Test file**: `h-mad/tests/test_h_mad_audit_cycle_grok.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_audit_cycle.py:measure_effort` → `h_mad_review_evidence.scan_grok`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_audit_cycle_grok.py::test_measure_effort_reads_f0_as_grok`
**WIRE 2**: `h-mad/scripts/h_mad_audit_cycle.py:combine` → `grok-truncated route (low_evidence_unmeasurable)`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_audit_cycle_grok.py::test_combine_routes_hand_built_grok_truncated_to_unmeasurable`

**Description**: FR-7 Python side / design D7 / plan W7 (a) and (b). The import line becomes
`from h_mad_review_evidence import scan, scan_grok`, and a second import
`from h_mad_review_evidence import _CODEX_HEADER_RE as _CODEX_BANNER` replaces the module's own
`_CODEX_BANNER = re.compile(r"^OpenAI Codex v", re.MULTILINE)` definition (the definition is no
anchor; the anchored `elif` line that uses the name is unchanged). `measure_effort()` changes only
its `else` body. `combine()` gains two routes; `_effort_items()` gains two renderings.

**Code structure** (v1.4: as landed in `9975729f`; the `_CODEX_BANNER` definition was removed
together with its three-line comment):
```python
# measure_effort(), after `counts = scan(text)`; the `if` and `elif` lines are byte-identical:
    if counts.get("agy_events", 0) > 0:
        counts["shape"] = "parsed"
    elif _CODEX_BANNER.search(text[:4096]):
        counts["shape"] = "codex-text"          # (existing comment block kept above it)
    else:
        grok = scan_grok(text)
        if grok is not None and grok["complete"]:
            return {"readable": True, "shape": "grok", "agy_events": 0,
                    "tools": grok["tools"], "ok": grok["ok"],
                    "unresolved": grok["unresolved"], "thinking": grok["thinking"],
                    "stop_reason": grok["stop_reason"]}
        if grok is not None:
            return {"readable": True, "shape": "grok-truncated", "agy_events": 0}
        # (existing three-line "Readable, non-empty, neither an agy transcript nor a codex one"
        #  comment kept, now after the grok reads)
        counts["shape"] = "unparseable"
    return counts

# combine(): after `if shape == "empty":`'s return, before the kept floor line:
        if shape == "grok-truncated":
            return "UNVERIFIED", f"low_evidence_unmeasurable:p{result.index}"
        if shape not in ("parsed", "grok"):
            return "UNVERIFIED", f"shape_unrouted:p{result.index}"

# _effort_items(): after the anchored codex-text block's `continue`:
        if effort.get("shape") == "grok-truncated":
            items.append(f"p{result.index} not measured (grok log truncated — no end event; "
                         "counts withheld)")
            continue
        if effort.get("shape") == "grok":
            line = (f"p{result.index} tools={effort['tools']} ok={effort['ok']} "
                    f"unresolved={effort['unresolved']} thinking={effort['thinking']} format=grok")
        else:
            line = (f"p{result.index} tools={effort['tools']} ok={effort['ok']} "
                    f"failed={effort['failed']} thinking={effort['thinking']}")
        # (plan note, not source: the anchored floor-suffix block follows here unchanged)
```
Landed literals (Task 14 rows A1–A3, W7a): `        if effort.get("shape") == "grok-truncated":`,
`        if shape == "grok-truncated":`, and the two existing lines
`    elif _CODEX_BANNER.search(text[:4096]):` and `    if counts.get("agy_events", 0) > 0:` (each
count 1 at `507214d`, and kept). Rows WR7-1 and WR7-2 anchor `        grok = scan_grok(text)` and
the two-line `        if shape == "grok-truncated":` /
`            return "UNVERIFIED", f"low_evidence_unmeasurable:p{result.index}"` (the second line
occurs twice in the committed file, once for `missing`/`unparseable` and once in the new route;
the pair is unique because its first line is — WR7-2's two-line `find` counts 1 at HEAD
`d9574614`).

**Tests** (19 collected items; `from test_h_mad_audit_cycle import audit_cycle, pass_result`; a CLEAN
report is `pass_result(index=1, effort=...)` with its defaults `verdict="PASS"`, `must=0`):
1. `test_measure_effort_reads_f0_as_grok` — shape `grok`, tools 2, ok 2, unresolved 0, thinking 121,
   stop_reason `end_turn`, and no `failed` key. WIRE-PIN 1.
2. `test_measure_effort_reads_f_trunc_as_grok_truncated` — `{"readable": True, "shape":
   "grok-truncated", "agy_events": 0}` exactly.
3. `test_combine_scores_f0_against_the_floor` — `("UNVERIFIED", "low_evidence:p1")` (AC-7.2).
4. `test_combine_passes_three_completed_calls` — `f0_with_completed(3)` → `("PASS", None)` (AC-7.3).
5. `test_combine_f_trunc_is_unmeasurable` — F-TRUNC measured then combined →
   `("UNVERIFIED", "low_evidence_unmeasurable:p1")` (AC-7.4).
6. `test_combine_routes_hand_built_grok_truncated_to_unmeasurable` — effort
   `{"readable": True, "shape": "grok-truncated", "agy_events": 0}` →
   `("UNVERIFIED", "low_evidence_unmeasurable:p1")`. WIRE-PIN 2.
7. `test_combine_routes_every_shape[missing|empty|parsed|grok|grok-truncated|codex-text|unparseable|unknown]`
   (8) — hand-built dicts: `missing` and `unparseable` → `low_evidence_unmeasurable:p1`; `empty` →
   `low_evidence:p1`; `parsed` and `grok` with `ok` 0 → `low_evidence:p1`; `grok-truncated` →
   `low_evidence_unmeasurable:p1`; `codex-text` → `("PASS", None)`; shape `bogus` →
   `shape_unrouted:p1`.
8. `test_effort_items_render_grok_and_grok_truncated` — the grok dict renders
   `p1 tools=2 ok=2 unresolved=0 thinking=121 format=grok low-evidence (` (prefix match); the
   grok-truncated dict renders `p1 not measured (grok log truncated — no end event; counts withheld)`.
9. `test_measure_effort_mixed_agy_f0_is_parsed` — equal to `measure_effort` on `agy_transcript()`,
   shape `parsed` (plan W7a).
10. `test_measure_effort_banner_then_f0_is_codex_text` (AC-11.3, `measure_effort` arm).
11. `test_codex_banner_pattern_is_single_sourced` — `re.purge()`, then
    `importlib.reload(audit_cycle())`, then `reloaded._CODEX_BANNER is ev._CODEX_HEADER_RE` (v1.4, as
    landed in `39a86df9`: without the purge and reload the bare identity passes at RED, because
    `re.compile` caches an identical pattern and the module's own compile returns the same
    object).
12. `test_measure_effort_survives_a_200k_deep_line` — two assertions, both required:
    `r_deep == r_f0` and `r_deep["shape"] == "grok"`, where `r_deep` is `measure_effort` on a file
    holding `deep_line_200k() + f0_text()` and `r_f0` is `measure_effort` on F0. The second assertion
    is what fails at RED (both calls return shape `unparseable` there, so the first alone would
    pass). The `measure_effort` call on the deep file is wrapped
    in the same `try` / `except RecursionError` / `pytest.fail` form as Task 5 test 11, with the
    message `"measure_effort() raised RecursionError on a 200,000-deep line"` (the `measure_effort`
    member of the §"Deviations from design v1.2" class; `scan()` already catches from Task 5).

**Expected RED split**: 10 failing, 9 passing. Failing: tests 1, 2, 3, 4, 6, the `grok-truncated`
and `unknown` items of test 7, test 8, test 11, test 12 (at RED the deep line no longer raises,
because Task 5 landed, and the result is shape `unparseable`, not `grok`). **Regression guards** (9): test 5 (today F-TRUNC is
`unparseable`, which routes to the same reason), the `missing`, `empty`, `parsed`, `grok`,
`codex-text` and `unparseable` items of test 7, tests 9 and 10. Test 12's `RecursionError` arm cannot
be RED at Task 7 (Task 5 already closed it); that property's kill is E9, through Task 5 test 11.
**WIRE-PIN RED reasons**: pin 1 — `measure_effort(F0)` returns shape `unparseable`, an assertion on
the caller's return value; `scan_grok` exists from Task 5. Pin 2 — `combine()` sends the
hand-built `grok-truncated` dict to the floor and returns `low_evidence:p1`.
**Wire-scoped reverts**: WIRE 1 — replace `grok = scan_grok(text)` with `grok = None` only; pin 1
fails. WIRE 2 — delete the two `if shape == "grok-truncated":` lines only; pin 2 fails with
`shape_unrouted:p1`. Executed and scored as rows WR7-1 and WR7-2 (Task 14,
`grok_wire_reverts.json`). WR7-2 deletes the same `if` that A2 disables, but its `test` key is
WIRE-PIN 2, so the harness scores the pin itself failing.
**Force-fires**: rows W7a and A2 (Task 14).

**Acceptance Criteria**:
- [ ] AC-7.2: F0 pass, CLEAN report → `UNVERIFIED low_evidence:p1`, scored not skipped.
- [ ] AC-7.3: three completed ids clear the floor.
- [ ] AC-7.4: F-TRUNC → `UNVERIFIED low_evidence_unmeasurable:p1`.
- [ ] AC-7.5: `test_h_mad_audit_cycle.py` and `test_hmad_dispatch_audit_cycle.py` pass unchanged (Task 16).
- [ ] AC-11.3 (`measure_effort` arm): the banner-then-F0 log is `codex-text`.
- [ ] Deviation 1 (class rule): `measure_effort` survives a 200,000-deep line
      (`test_measure_effort_survives_a_200k_deep_line`).

**Mutation rows** (Task 14): A1, A2, A3, W7a (`audit_cycle_grok.json`) and WR7-1, WR7-2
(`grok_wire_reverts.json`) — 6 rows.

**Dependencies on other tasks**: Task 5

---

## Task 8: grok-stream-readers

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_grok_readers.py`
**Task shape**: `new-behaviour`

**Description**: FR-4 readers / design D3.4–D3.5: the shared jq line filter and depth bound, the
region helper and the four readers, placed beside `_agy_ndjson_response` / `_agy_last_step`. No
caller uses them yet (Task 9 wires them). Each is driven directly through `run_fn`.

**Code structure** (landed literally; these hold rows P1–P9, L3, L4):
```bash
_GROK_TYPES_RE='thought|text|available_commands|tool_call|tool_call_update|usage|end'
_GROK_MAX_DEPTH=64
_GROK_JQ_DEFS='def _grok_over($d): if $d > $max then true
    elif (type == "object" or type == "array") then any(.[]; _grok_over($d + 1))
    else false end;
  def _grok_obj: (fromjson? // empty) | select(type == "object")
    | select(_grok_over(0) | not);'

_grok_region() {  # <log> <pre_lines> -> the lines after pre_lines; the only place the offset is spelled
  local log="$1" pre="$2"
  case "$pre" in ''|*[!0-9]*) pre=0 ;; esac
  tail -n "+$(( pre + 1 ))" "$log" 2>/dev/null || true
}

_grok_final_message() {  # <log> <pre_lines> -> the last non-empty text segment, or nothing
  local log="$1" pre="$2"
  case "$pre" in ''|*[!0-9]*) pre=0 ;; esac
  _grok_region "$log" "$pre" | jq -nR -r --argjson max "$_GROK_MAX_DEPTH" "$_GROK_JQ_DEFS"'
    reduce (inputs | _grok_obj) as $e
      ({last: "", cur: ""};
       if $e.type == "text" then .cur += (if ($e.data | type) == "string" then $e.data else "" end)
       elif ($e.type == "tool_call" or $e.type == "tool_call_update"
             or $e.type == "usage" or $e.type == "end")
         then (if (.cur | length) > 0 then .last = .cur else . end) | .cur = ""
       else . end)
    | if (.cur | length) > 0 then .cur elif (.last | length) > 0 then .last else empty end' \
    2>/dev/null || true
}

_grok_region_state() {  # <log> <pre_lines> -> complete | truncated | nojq | jqfail
  local log="$1" pre="$2" st="" rc=0
  case "$pre" in ''|*[!0-9]*) pre=0 ;; esac
  command -v jq >/dev/null 2>&1 || { echo nojq; return 0; }
  st="$(_grok_region "$log" "$pre" | jq -nR -r --argjson max "$_GROK_MAX_DEPTH" \
    "$_GROK_JQ_DEFS"' reduce (inputs | _grok_obj | select(.type == "end")) as $_ ("truncated"; "complete")' \
    2>/dev/null)" || rc=$?
  case "$rc:$st" in
    0:complete|0:truncated) echo "$st" ;;
    *) echo jqfail ;;
  esac
}

_grok_stop_reason() {  # <log> <pre_lines> -> the last end event's stopReason, or nothing
  local log="$1" pre="$2"
  case "$pre" in ''|*[!0-9]*) pre=0 ;; esac
  _grok_region "$log" "$pre" | jq -nR -r --argjson max "$_GROK_MAX_DEPTH" "$_GROK_JQ_DEFS"'
    reduce (inputs | _grok_obj | select(.type == "end")) as $e (null; ($e.stopReason // "-") | tostring)
    | values' 2>/dev/null || true
}

_grok_last_tool() {  # <log> <pre_lines> -> "N tool calls completed; last tool: <name> <status>" or nothing
  local log="$1" pre="$2"
  case "$pre" in ''|*[!0-9]*) pre=0 ;; esac
  _grok_region "$log" "$pre" | jq -nR -r --argjson max "$_GROK_MAX_DEPTH" "$_GROK_JQ_DEFS"'
    reduce (inputs | _grok_obj
            | select(.type == "tool_call" or .type == "tool_call_update")) as $e
      ({names: {}, done: {}, seen: false, last: null};
       (if $e.type == "tool_call" then .seen = true else . end)
       | (if $e.type == "tool_call" and ($e.toolCallId | type) == "string"
          then .names[$e.toolCallId] = ($e.toolName // "?") else . end)
       | (if $e.type == "tool_call_update" and $e.status == "completed"
             and ($e.toolCallId | type) == "string"
          then .done[$e.toolCallId] = true else . end)
       | (if $e.status != null then .last = $e else . end))
    | if .seen | not then empty
      else "\(.done | length) tool calls completed; last tool: "
           + (if .last == null then "none"
              else (((.last.toolCallId | strings) as $i | .names[$i]) // "?")
                   + " " + (.last.status | tostring) end)
      end' 2>/dev/null || true
}
```

- `_grok_region_state` reduces the whole region and never stops early, so a SIGPIPE on the region
  pipe cannot turn a completed run into `jqfail` (design D3.5, V19).
- The region read `tail -n "+$(( pre + 1 ))"` is spelled differently from `_agy_last_step`'s anchored
  `tail -n +"$((pre + 1))"` and from `_agy_ndjson_response`'s `"+$(( skip + 1 ))"`
  (`grep -c 'head -c 4096\|"+$(( pre + 1 ))"' h-mad/scripts/hmad-dispatch.sh` → 0 at `507214d`).

**Tests** (21 collected items; every test asserts `r.returncode == 0` and
`"command not found" not in r.stderr` besides its value):
1. `test_grok_final_message_on_f0` → `STATUS: DONE`.
2. `test_grok_final_message_per_closer[usage|tool_call|tool_call_update]` (3) — `f_sep(kept)` →
   `STATUS: DONE`, one closer type per fixture (design §"Mutation rows", per-branch rule).
3. `test_grok_final_message_ignores_thought_decoy` — F-DECOY → `All done.`
4. `test_grok_final_message_keeps_a_multiline_segment` — a `text` event whose `data` is `"a\nb"`,
   then `end` → the two lines as one value.
5. `test_grok_region_starts_after_pre` — log `f0_text() + f0_text()`, `_grok_region "$L" 110` prints
   exactly the second copy (110 lines).
6. `test_grok_region_state_words[f0|f_trunc|empty|deep65_end]` (4) — `complete`, `truncated`,
   `truncated`, `truncated` (the last is a lone depth-65 `end` line).
7. `test_grok_region_state_reports_jq_failure` — a `jq` shim in the test's bindir that exits 5 → `jqfail`.
8. `test_grok_region_state_without_jq` — `wrapper_fn_in_env` on a farm without `jq` → `nojq`.
9. `test_grok_region_state_survives_a_sigpipe_sized_region` — one `end` line followed by 20,000
   `thought` lines → `complete`, rc 0.
10. `test_grok_stop_reason_on_f0` → `end_turn`.
11. `test_grok_last_tool_lines[f0|f_notools|ac_4_10|f_notooltext]` (4) —
    `2 tool calls completed; last tool: search_replace completed`,
    `0 tool calls completed; last tool: search_replace pending` (twice), and the empty string.
12. `test_grok_depth_boundary_readers[64|65]` (2) — `f_deep(64)`: `complete`, `DEEP`, a line
    beginning `3 tool calls completed`, stop reason `deep`; `f_deep(65)`: `truncated`,
    `STATUS: DONE`, a line beginning `2 tool calls completed`, empty stop reason.

**Expected RED split**: 21 failing, 0 passing. **Regression guards**: none. Every reader is undefined
at RED, so each call prints `command not found` and exits 127.

**Acceptance Criteria**:
- [ ] The FR-4 segmentation rule (text appends; `tool_call`, `tool_call_update`, `usage`, `end`
      close; every other type is transparent), each closer exercised alone.
- [ ] The FR-4 completion rule and the four state words, with `nojq` and `jqfail` distinct.
- [ ] N counts distinct completed ids over the whole region (the reader behind AC-4.10).
- [ ] The depth bound: a line deeper than 64 is not an event for any reader.

**Mutation rows** (Task 14, `grok_exec.json`): P1, P2, P3, P4, P5, P6, P7, P8, P9, L3, L4 — 11 rows.

**Dependencies on other tasks**: Task 1

---

## Task 9: exec-grok-arm

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_exec_grok.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/hmad-dispatch.sh:_cmd_exec` → `grok argv builder (gargs with --prompt-file)`
**WIRE-PIN 1**: `h-mad/tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_argv_carries_prompt_file_and_headless_flags`
**WIRE 2**: `h-mad/scripts/hmad-dispatch.sh:_cmd_exec` → `child_env scrub (env -u of every CLAUDE* name, HPW_AGENT_BACKEND defaulted to claude)`
**WIRE-PIN 2**: `h-mad/tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_child_env_has_no_claude_names`
**WIRE 3**: `h-mad/scripts/hmad-dispatch.sh:_cmd_exec` → `_grok_final_message (scoped by pre_lines)`
**WIRE-PIN 3**: `h-mad/tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_f0_prints_the_final_message`
**WIRE 4**: `h-mad/scripts/hmad-dispatch.sh:_cmd_exec` → `_grok_last_tool (EMPTY path)`
**WIRE-PIN 4**: `h-mad/tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_empty_path_names_the_last_tool`

**Description**: FR-3 and FR-4 / design D3, D3.1–D3.4, D3.6 / plan W1–W4. Every agent-conditional
site of `_cmd_exec` from the design's census (S1–S8, located by content, never by line) gets its
treatment. S4's `else` (agy) and S8's `else` (codex) become explicit `elif`s, so no `else` arm of an
agent conditional stands for a named agent. S2, S5 and S7 are unchanged.

**Code structure** (changes in `_cmd_exec`, in file order; v1.4: comment text as landed in
`b3e6cb70`):
```bash
# header comment:
_cmd_exec() {  # <codex|agy|grok> <promptfile> [--cd <dir>] [--model <m>] [--effort <e>] [--out <file>] [--log <file>] [--timeout <s>] [codex: --sandbox <mode>] [agy: --sandbox] [grok: --sandbox <profile>]
# S1:
  case "$agent" in codex|agy|grok) ;;
    *) echo "hmad-dispatch: exec: unknown agent '$agent' (expected codex|agy|grok)" >&2; return 2 ;;
  esac
# option comments gain:  --sandbox … ; grok: passed verbatim      --effort … ; grok: --reasoning-effort
# S3 gains:  grok)  ;;   # grok's default is applied in child_env only
# after `local heartbeat_sec="${HMAD_EXEC_HEARTBEAT_SEC:-120}"`, before the transport chain:
  local child_env=() _v grok_state="" grok_final=""
  for _v in $(compgen -e); do case "$_v" in CLAUDE*) child_env+=(-u "$_v") ;; esac; done
  child_env+=("HPW_AGENT_BACKEND=${HPW_AGENT_BACKEND:-claude}")
# S4 chain:
  if [ "$agent" = grok ]; then
    # grok: prompt by file, streaming-json appended to $log (FR-3). No OVERSIZE check here:
    # the prompt travels as a file, never as an argv element (AC-3.5).
    local gargs=(--cwd "$cd_dir" --always-approve --output-format streaming-json
                 --prompt-file "$bounded_prompt")
    [ -n "$model" ]   && gargs+=(--model "$model")
    [ -n "$effort" ]  && gargs+=(--reasoning-effort "$effort")
    [ -n "$sandbox" ] && gargs+=(--sandbox "$sandbox")
    if [ -f "$log" ]; then pre_lines="$(wc -l < "$log" 2>/dev/null | tr -d " ")"; fi
    [ -n "$pre_lines" ] || pre_lines=0
    _HMAD_EXEC_BEAT_LOG="$log"
    ( cd "$cd_dir" && _exec_run --heartbeat "$agent" "$label" "$cd_dir" "$heartbeat_sec" \
      "$wait_secs" env "${child_env[@]}" grok "${gargs[@]}" ) < /dev/null >> "$log" 2>&1 || rc=$?
    _HMAD_EXEC_BEAT_LOG=""
    grok_state="$(_grok_region_state "$log" "$pre_lines")"
    grok_final="$(_grok_final_message "$log" "$pre_lines")"
    if [ "$grok_state" = complete ] && [ -n "$grok_final" ]; then
      verdict="$grok_final"
      [ -n "$out" ] && _out_clobber_ok "$out" "$out_fp" && printf '%s\n' "$grok_final" | _write_out_atomic "$out"
      printf '%s\n' "$grok_final"
      echo "hmad-dispatch: exec: grok stopReason=$(_grok_stop_reason "$log" "$pre_lines")" >&2
      [ -n "$auto_log" ] && _render_progress "$log" 40 >&2 || true
      [ -n "$auto_log" ] && rm -f "$log"
    else
      final_empty=1
    fi
  elif [ "$agent" = codex ]; then
    # codex arm, body unchanged
  elif [ "$agent" = agy ]; then
    # agy arm, body unchanged (its ARG_MAX OVERSIZE refusal stays inside it)
  fi
# EMPTY block, after the unchanged agy #77b block (S6):
    if [ "$agent" = grok ]; then
      case "$grok_state" in
        truncated) echo "hmad-dispatch: exec: TRUNCATED — no end event in this dispatch's grok stream" >&2 ;;
        nojq)      echo "hmad-dispatch: exec: grok stream not parsed — jq not on PATH" >&2 ;;
        jqfail)    echo "hmad-dispatch: exec: grok stream not parsed — jq failed" >&2 ;;
      esac
      local grok_last
      grok_last="$(_grok_last_tool "$log" "$pre_lines")"
      [ -n "$grok_last" ] && echo "hmad-dispatch: exec: last step reached — ${grok_last}" >&2
    fi
    local recovered=""                       # (plan note: was `local recovered`; set -u, design D3)
# S8 chain:
    if [ "$agent" = agy ]; then
      # agy arm, unchanged
    elif [ "$agent" = grok ]; then
      # A grok log is recovered only through its structured stream.
      recovered="$grok_final"
      if [ -n "$recovered" ] && ! _recovered_has_verdict "$recovered"; then
        recovered=""
      fi
    elif [ "$agent" = codex ]; then
      recovered="$(_verdict_after_boundary "$log" "$boundary" "$echo_expected")"
    fi
```
Landed literals (Task 14 rows W1, W2, W3a): the two lines `  if [ "$agent" = grok ]; then` /
`    # grok: prompt by file, streaming-json appended to $log (FR-3). No OVERSIZE check here:` (one
two-line `find`, because `  if [ "$agent" = grok ]; then` alone is a substring of the EMPTY block's
and S8's lines); the existing `"$wait_secs" codex "${args[@]}"` and `resp="$(_agy_ndjson_response`
(count 1 each at `507214d`, unchanged). Rows WR9-1 to WR9-4 (the same two-line W1 `find`, then
`"$wait_secs" env "${child_env[@]}" grok "${gargs[@]}"`,
`grok_final="$(_grok_final_message "$log" "$pre_lines")"` and
`grok_last="$(_grok_last_tool "$log" "$pre_lines")"`, each landing exactly once as written above).

**Tests** (30 collected items; stub `grok` via `_bindir(tmp, ["grok"])` and `run()`, stream from
`HMAD_STUB_GROK_STREAM`, capture via `HMAD_STUB_CAPTURE`, `--log` given unless a test says otherwise;
v1.4, as landed in `10137f3b`: an autouse fixture `_clean_caller_env` deletes every ambient
`CLAUDE*` name and `HPW_AGENT_BACKEND` before each test sets its own, because a RED run inside
Claude Code inherits about 15 exported `CLAUDE*` names, which broke the exact-list guard
`test_exec_codex_and_agy_keep_claude_env` and read 25/5 instead of 23/7):
1. `test_exec_grok_argv_carries_prompt_file_and_headless_flags` — argv holds `--cwd <cd_dir>`,
   `--always-approve`, `--output-format streaming-json`, `--prompt-file <path>`, never `-p` or
   `--single`; the copied prompt (`HMAD_STUB_GROK_PROMPT_CAPTURE`) holds the caller's prompt, then
   the `===HMAD-DISPATCH-BOUNDARY===` line (AC-3.1). WIRE-PIN 1.
2. `test_exec_grok_translates_model_effort_sandbox[given|none]` (2) — `--model m1 --effort high
   --sandbox s1` → `--model m1`, `--reasoning-effort high`, `--sandbox s1`; none given → none of the
   three flags (AC-3.2).
3. `test_exec_grok_child_env_has_no_claude_names` — caller exports `CLAUDECODE`,
   `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_EFFORT`, leaves `HPW_AGENT_BACKEND`
   unset: `HMAD_STUB_CLAUDE_ENV_CAPTURE` is empty and `HMAD_STUB_ENV_CAPTURE` reads
   `HPW_AGENT_BACKEND=claude` (AC-3.3). WIRE-PIN 2.
4. `test_exec_grok_hpw_backend_default[empty|gemini]` (2) — `""` → `claude`; `gemini` → `gemini` (AC-3.3).
5. `test_exec_grok_leaves_the_wrapper_shell_env_intact` — via `run_fn`:
   `_cmd_exec grok "$P" --cd "$D" --log "$L" >/dev/null 2>&1; rc=$?; compgen -e | grep '^CLAUDE' | sort`
   prints all four names, and the capture file holds a `grok ` line and `rc` is 0 (AC-3.3, last clause).
6. `test_exec_codex_and_agy_keep_claude_env[codex|agy]` (2) — with the knob set, all four names are
   recorded, and `HPW_AGENT_BACKEND` defaults to `codex` / `gemini` (AC-3.4).
7. `test_exec_grok_oversize_prompt_is_not_refused` — a prompt of `getconf ARG_MAX` + 1 bytes: no
   `OVERSIZE`, rc not 2, and the copied prompt is at least that size (AC-3.5).
8. `test_exec_grok_without_grok_on_path_returns_2` — farm excluding nothing and linking no stub,
   precondition `command -v grok` fails in the cell env: rc 2, stderr contains
   `exec requires the grok CLI on PATH` (AC-3.6; also W1's residual precondition).
9. `test_exec_unknown_agent_names_the_three_agent_set` — `exec gpt` → rc 2, stderr names
   `codex|agy|grok` (AC-3.6).
10. `test_pane_verbs_still_refuse_grok[exec-pane|launch|pin|verify|resolve]` (5) — rc 2 and stderr
    contains `unknown agent`, unchanged from base (AC-3.7).
11. `test_exec_grok_f0_prints_the_final_message` — stdout exactly `STATUS: DONE\n`, `--out` holds the
    same bytes, rc 0, stderr contains `stopReason=end_turn` (AC-4.1). WIRE-PIN 3.
12. `test_exec_grok_beat_and_spaced_match_f0[beat|spaced]` (2) — stdout equals F0's (AC-4.2).
13. `test_exec_grok_decoys_are_not_recovered` — F-DECOY: stdout `All done.`, and
    `h_mad_extract_verdict.py <out> --key STATUS` exits 2 printing no `STATUS:` value (AC-4.3).
14. `test_exec_grok_no_text_takes_the_empty_path` — F-NOTEXT, stub rc 0: rc 3, stdout empty, stderr
    contains `EMPTY final message` (AC-4.4).
15. `test_exec_grok_truncated_recovers_the_verdict` — F-TRUNC, stub rc 0: rc 3, stderr contains
    `TRUNCATED — no end event` and `verdict recovered from log`, stdout and `--out` are
    `STATUS: DONE` (AC-4.5).
16. `test_exec_grok_empty_path_names_the_last_tool` — `f_trunc_nostatus()`: rc 3, stdout empty,
    `--out` not written, stderr contains `2 tool calls completed; last tool: search_replace completed`
    (AC-4.6). WIRE-PIN 4.
17. `test_exec_grok_reads_only_its_own_region` — `--log` pre-filled with F0; the stub appends
    `f_trunc_nostatus()`: stdout empty, rc 3 (AC-4.7).
18. `test_exec_grok_watchdog_kill_reports_recovery` — `--timeout 1`, stub emits F-TRUNC then sleeps
    (`HMAD_STUB_GROK_SLEEP=5`): rc 124, stderr contains `a verdict WAS recovered` (AC-4.8).
19. `test_exec_grok_omits_the_last_tool_line_without_tool_calls` — F-NOTOOLTEXT, stub rc 0: rc 3,
    stderr contains `EMPTY final message` and no `tool calls completed` (AC-4.9).
20. `test_exec_grok_counts_completed_not_seen_ids` — `ac_4_10_stream()`, stub rc 0: rc 3, stderr
    contains `0 tool calls completed; last tool: search_replace pending` (AC-4.10).
21. `test_exec_grok_without_jq_is_not_parsed` — farm without `jq`, stub `grok` linked, precondition
    `command -v jq` fails: stderr contains `grok stream not parsed — jq not on PATH`, no `TRUNCATED`,
    no `command not found`.
22. `test_exec_grok_with_failing_jq_is_not_parsed` — a `jq` shim exiting 127 in the test's bindir: stderr
    contains `grok stream not parsed — jq failed` and no `TRUNCATED`.

**Expected RED split**: 23 failing, 7 passing. **Regression guards** (7): both items of
`test_exec_codex_and_agy_keep_claude_env` and the five items of `test_pane_verbs_still_refuse_grok`.
At RED `exec grok` is refused as an unknown agent, so every other test fails on its assertion.
**WIRE-PIN RED reasons**: each pin asserts the dispatch's observable output (the stub's captured
argv, the captured env, stdout, stderr); at RED the wrapper returns 2 with
`unknown agent 'grok' (expected codex|agy)`. Shell has no import step, and the callees
`_grok_final_message` / `_grok_last_tool` already exist from Task 8.
**Wire-scoped reverts** (one at a time, callee and tests intact): WIRE 1 — the grok arm's
`if [ "$agent" = grok ]; then` → `if false; then`: no stub runs, pin 1 fails. WIRE 2 — drop
`env "${child_env[@]}"` from the grok launch line: `CLAUDE*` reach the stub, pin 2 fails. WIRE 3 —
`grok_final="$(_grok_final_message "$log" "$pre_lines")"` → `grok_final=""`: EMPTY path, pin 3
fails. WIRE 4 — `grok_last="$(_grok_last_tool "$log" "$pre_lines")"` → `grok_last=""`: pin 4 fails.
Executed and scored as rows WR9-1 to WR9-4 (Task 14, `grok_wire_reverts.json`); WR9-1 reuses W1's
two-line `find`, and WR9-2 anchors the landed `"$wait_secs" env "${child_env[@]}" grok "${gargs[@]}"`.
**Force-fires**: rows W1, W2, W3a, and P5 (W3b) and P7 (W4) (Task 14).

**Acceptance Criteria**:
- [ ] AC-3.1 through AC-3.7 as the tests state.
- [ ] AC-4.1 through AC-4.10 as the tests state.
- [ ] `local recovered=""`: an agent that matches no S8 arm cannot crash the EMPTY block under `set -u`.

**Mutation rows** (Task 14): W1, W2, W3a (`grok_exec.json`) and WR9-1, WR9-2, WR9-3, WR9-4
(`grok_wire_reverts.json`) — 7 rows.

**Dependencies on other tasks**: Task 1, Task 8

---

## Task 10: progress-grok-ndjson

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_progress_grok.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/hmad-dispatch.sh:_exec_log_format` → `_grok_log_has_events`
**WIRE-PIN 1**: `h-mad/tests/test_hmad_dispatch_progress_grok.py::test_progress_f0_is_grok_ndjson`
**WIRE 2**: `h-mad/scripts/hmad-dispatch.sh:_render_progress` → `grok-ndjson renderer branch`
**WIRE-PIN 2**: `h-mad/tests/test_hmad_dispatch_progress_grok.py::test_progress_f0_renders_counts_without_delta_text`

**Description**: FR-5 / design D4, D5 / plan W5. `_exec_log_format` decides in the order missing,
empty, agy grep (unchanged), `_codex_banner_in_head`, `_grok_log_has_events`, else `codex-text`; its
header lists `grok-ndjson`. `_render_progress` gains an `elif [ "$fmt" = grok-ndjson ]; then` arm
between the agy branch and the codex lens. It also makes Task 9's auto-log digest render grok logs.

**Code structure**:
```bash
_codex_banner_in_head() {  # <logfile> -> rc 0 iff a line of the first 4096 bytes begins "OpenAI Codex v"
  local h; h="$(head -c 4096 "$1" 2>/dev/null)" || h=""
  case $'\n'"$h" in *$'\n''OpenAI Codex v'*) return 0 ;; esac; return 1
}

_grok_log_has_events() {  # <logfile> -> rc 0 iff some line is a grok event (depth <= 64, type in the vocabulary)
  local log="$1" rc=0
  if command -v jq >/dev/null 2>&1; then
    jq -nR -e --argjson max "$_GROK_MAX_DEPTH" --arg re "$_GROK_TYPES_RE" \
      "$_GROK_JQ_DEFS"' ($re | split("|")) as $t
      | first(inputs | _grok_obj
              | select((.type | type) == "string") | .type as $x
              | select(any($t[]; . == $x))) | true' "$log" >/dev/null 2>&1 || rc=$?
    case "$rc" in 0) return 0 ;; 4) return 1 ;; esac
  fi
  grep -aqE "^[[:space:]]*\{.*\"type\"[[:space:]]*:[[:space:]]*\"(${_GROK_TYPES_RE})\"" "$log" 2>/dev/null
}

_exec_log_format() {  # <logfile> -> agy-ndjson | codex-text | grok-ndjson | empty | missing
  # missing / empty / agy grep: unchanged
  elif _codex_banner_in_head "$log"; then
    printf 'codex-text'
  elif _grok_log_has_events "$log"; then
    printf 'grok-ndjson'
  else
    printf 'codex-text'
  fi
}
```

- **`_render_progress` grok arm** (design D5), landed literally. The renderer program is a second
  shell variable, defined directly after `_GROK_JQ_DEFS` (Task 8) and always used as the suffix of
  `"$_GROK_JQ_DEFS$_GROK_RENDER_PROG"`:

```bash
_GROK_RENDER_PROG='def _grok_flush: if .run == null then .
    else .out += ["  · " + (if .run == "thought" then "thinking" else "reply text" end)
                  + " (\(.k) events)"] | .run = null | .k = 0 end;
  def _grok_emit($l): _grok_flush | .out += [$l];
  [split("\n")[] | _grok_obj] as $evs
  | ([$evs[] | select(.type == "tool_call" and (.toolCallId | type) == "string")
      | {key: .toolCallId, value: (.toolName | tostring)}] | from_entries) as $names
  | reduce $evs[] as $ev ({out: [], run: null, k: 0};
      if ($ev.type | type) != "string" then .
      elif $ev.type == "thought" or $ev.type == "text" then
        (if .run == $ev.type then . else _grok_flush | .run = $ev.type end) | .k += 1
      elif $ev.type == "available_commands" then .
      elif $ev.type == "tool_call_update" and $ev.status == null then .
      elif $ev.type == "tool_call" then
        _grok_emit("  · tool \($ev.toolName) \($ev.status)"
          + (if $ev.rawInput == null then "" else " " + ($ev.rawInput | tojson | .[0:70]) end))
      elif $ev.type == "tool_call_update" then
        _grok_emit("  · tool \(($ev.toolCallId | if type == "string" then $names[.] else null end) // "?") \($ev.status)")
      elif $ev.type == "usage" then
        _grok_emit("  · turn usage (\($ev.usage.output_tokens) out, \($ev.usage.reasoning_tokens) reasoning)")
      elif $ev.type == "end" then
        _grok_emit("  · END stopReason=\($ev.stopReason) turns=\($ev.num_turns)")
      else _grok_emit("  · \($ev.type)") end)
  | _grok_flush | .out[]'

# _render_progress, between the agy branch and the codex lens's `else`:
  elif [ "$fmt" = grok-ndjson ]; then
    if ! command -v jq >/dev/null 2>&1; then
      echo "  (grok stream — jq not on PATH, cannot render)"
    else
      local grender grc=0
      grender="$(tail -n 400 "$log" 2>/dev/null \
        | jq -Rs -r --argjson max "$_GROK_MAX_DEPTH" "$_GROK_JQ_DEFS$_GROK_RENDER_PROG")" || grc=$?
      if [ "$grc" -ne 0 ]; then
        echo "  (grok stream — jq failed, cannot render)"
      elif [ -n "$grender" ]; then
        printf '%s\n' "$grender" | tail -n "$n"
      fi
    fi
```

  The algorithm, step by step (design D5 table and "What ends a run"):
  1. Split the slurped 400-line window on `"\n"`; each piece goes through `_grok_obj`, so a
     non-JSON line, a non-object, and a line deeper than `$max` vanish before anything else sees
     them. The result is the event list `$evs`.
  2. Build `$names`, the `toolCallId → toolName` map, from every `tool_call` event with a string
     `toolCallId`.
  3. Reduce `$evs` over the state `{out, run, k}`. A `thought` or `text` event extends the open run
     of its own kind, or flushes the other kind and opens its own; `k` counts the run's events. An
     `available_commands` event, a `tool_call_update` whose `status` is null, and an event whose
     `type` is not a string change nothing, so they neither end a run nor start one. Every other
     event flushes the open run as one `  · thinking (<k> events)` / `  · reply text (<k> events)`
     line, then appends its own line: `tool_call` → `  · tool <toolName> <status>` plus a space and
     the first 70 characters of `rawInput | tojson` when `rawInput` is non-null;
     `tool_call_update` → `  · tool <$names lookup, or ?> <status>`; `usage` → `  · turn usage
     (<output_tokens> out, <reasoning_tokens> reasoning)`; `end` → `  · END stopReason=<v>
     turns=<num_turns>`; any other string `type` → `  · <type>`.
  4. Flush the run still open at the end of the window, and print `out` one line per element.
     `tail -n "$n"` then keeps the last `n` lines. No `text` or `thought` `data` is ever copied into
     `out`, so no delta text reaches any line.

  The pipeline's rc is captured under the wrapper's `set -euo pipefail`, so a failing `jq` (the
  shim of test 9) prints only `  (grok stream — jq failed, cannot render)`, never a partial render.
  The `[ -n "$grender" ]` guard makes an empty render (a window whose events all render nothing,
  e.g. only `available_commands`) print nothing, where `printf '%s\n' ""` would print one blank line.
  **Executed for this revision** (jq 1.8.2, `$_GROK_JQ_DEFS` from design D3.5, no file kept): on F0
  the program prints 13 lines, among them `  · tool read_file pending …`, `  · tool read_file
  completed`, `  · tool search_replace pending …`, `  · tool search_replace completed`, three
  `  · turn usage (…)` lines and `  · END stopReason=end_turn turns=3`, which is test 4's
  expectation; on a hand-built window (a non-JSON line, a depth-65 `text` line, `{"type":"weird"}`,
  and two `thought` events separated by `available_commands`) it prints `  · weird` between two
  thinking lines and counts the two `thought` events as one run of 2. Every line of the program
  was checked as a substring against the 91 committed `hmad-dispatch.sh` finds and this plan's 19
  `grok_exec.json` finds: 0 hits, so no anchor gains a second match. It binds `$ev`, never `$e`.
- **Anchor hygiene.** The renderer binds its event as `$ev`, never `$e`, so no Task 8 row's `find`
  (all spelled with `$e.`) can match a second time inside it.
- Landed literals (Task 14 rows L1, L2, L5, W5): `elif _codex_banner_in_head "$log"`, the fallback
  `grep -aqE` line above (its `\{.*\"type\"`), `head -c 4096`, and the existing
  `  if grep -aqE '^[[:space:]]*\{[[:space:]]*"event"` (count 1 at `507214d`, unchanged).

**Tests** (15 collected items; `run(["progress", <log>, "--lines", "400"])` unless a farm cell):
1. `test_progress_f0_is_grok_ndjson` — `format: grok-ndjson` (AC-5.1). WIRE-PIN 1.
2. `test_progress_f_spaced_is_grok_ndjson` (AC-5.1).
3. `test_progress_agy_init_plus_f0_is_agy_ndjson` — `agy_init_f0()` → `format: agy-ndjson` (AC-5.1).
4. `test_progress_f0_renders_counts_without_delta_text` — exactly 2 `pending` and 2 `completed` tool
   lines matching `tool read_file|tool search_replace`, 1 `END stopReason=end_turn turns=3` line and
   3 `turn usage` lines; no output line, stripped, equals any single stripped non-empty `thought` or
   `text` `data`; neither F0 text segment occurs anywhere; no total line count is asserted (AC-5.2).
   WIRE-PIN 2.
5. `test_progress_key_order_line_is_grok_ndjson` — `{"meta":1,"type":"text","data":"x"}` →
   `format: grok-ndjson` (AC-5.2b, jq route).
6. `test_progress_bogus_type_line_is_codex_text` — `{"meta":1,"type":"bogus","data":"x"}` →
   `format: codex-text` (AC-5.2b).
7. `test_progress_key_order_line_on_the_fallback_route` — farm without `jq`, precondition asserted:
   the key-order line → `format: grok-ndjson` (AC-5.2b, fallback route).
8. `test_progress_without_jq_cannot_render` — farm without `jq`, F0: `format: grok-ndjson` and the
   line `  (grok stream — jq not on PATH, cannot render)`.
9. `test_progress_with_failing_jq_cannot_render` — `jq` shim exiting 127 in the test's bindir, F0:
   `  (grok stream — jq failed, cannot render)`.
10. `test_progress_banner_then_f0_is_codex_text` (AC-11.3, `progress` arm).
11. `test_progress_depth_boundary[64|65]` (2) — `depth_line(64)` → `format: grok-ndjson`;
    `depth_line(65)` → `format: codex-text` (AC-5.2b depth boundary).
12. `test_progress_f_deep65_prints_no_deep_end` — `f_deep(65)`: no `END stopReason=deep` line.
13. `test_exec_grok_auto_log_is_rendered_as_the_digest` — `exec grok` on F0 without `--log`: stderr
    contains `END stopReason=end_turn` and no line beginning `{"type":"` (FR-4 auto-log clause).
14. `test_window_edge_log_is_grok_ndjson` — `window_edge_log()` → `format: grok-ndjson` (its banner
    starts at byte 4096, outside the window).

**Expected RED split**: 10 failing, 5 passing. **Regression guards** (5):
`test_progress_agy_init_plus_f0_is_agy_ndjson`, `test_progress_bogus_type_line_is_codex_text`,
`test_progress_banner_then_f0_is_codex_text`, the `65` item of `test_progress_depth_boundary`, and
`test_progress_f_deep65_prints_no_deep_end`.
**WIRE-PIN RED reasons**: pin 1 — `progress` prints `format: codex-text` for F0, an assertion on the
verb's output; pin 2 — the codex lens prints `(prompt still echoing — no agent output yet)`, so the
class counts are 0. Both are subprocess runs of the verb.
**Wire-scoped reverts**: WIRE 1 — `  elif _grok_log_has_events "$log"; then` → `  elif false; then`
only: pin 1 fails. WIRE 2 — `elif [ "$fmt" = grok-ndjson ]; then` → `elif false; then` only: the
codex lens runs, pin 2 fails. Executed and scored as rows WR10-1 and WR10-2 (Task 14,
`grok_wire_reverts.json`); both `find`s land exactly once, as written in the code block above.
**Force-fire**: row W5 (Task 14).

**Acceptance Criteria**:
- [ ] AC-5.1, AC-5.2, AC-5.2b (shell half, both routes and the depth boundary) as the tests state.
- [ ] AC-5.3: `test_hmad_dispatch_progress.py`'s agy and codex rendering tests pass unchanged (Task 16).
- [ ] AC-11.3 (`progress` arm): the banner wins.

**Mutation rows** (Task 14): L1, L2, L5, W5 (`grok_exec.json`) and WR10-1, WR10-2
(`grok_wire_reverts.json`) — 6 rows.

**Dependencies on other tasks**: Task 8, Task 9

---

## Task 11: audit-cycle-surfaces-grok

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch_audit_cycle_grok.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/hmad-dispatch.sh:_cmd_audit_cycle` → `_cmd_exec grok (the --surfaces valid set)`
**WIRE-PIN**: `h-mad/tests/test_hmad_dispatch_audit_cycle_grok.py::test_audit_cycle_dispatches_the_grok_pass_through_exec_grok`

**Description**: FR-7 transport / design D8, D10 / plan W8. The `--surfaces` case becomes
`case "$_s" in agy|codex|grok) ;;` and its message `unknown agent '$_s' (agy|codex|grok)`. Nothing
else in `_cmd_audit_cycle` changes: the pass loop already dispatches `_cmd_exec "${agent[$i]}"`
with a per-pass `--log` (plan P8). The header comment of `_cmd_resolved_model` becomes
`_cmd_resolved_model() {  # <codex|agy|grok> [--log <f>] — what model actually ran` (its body
forwards `"$@"` unchanged, plan P10).

**Tests** (2 collected items; `from test_hmad_dispatch_audit_cycle import dispatch_args,
project_with_docs, run_with_cmd_exec_stub, read_jsonl, _dispatch_artifacts_by_pass`):
1. `test_audit_cycle_dispatches_the_grok_pass_through_exec_grok` — `dispatch_args(root=root,
   passes="2")` plus `--surfaces agy,grok`: rc 0; the trace's two `cmd_exec_start` rows have
   `argv[:1] == ["agy"]` for pass 1 and `["grok"]` for pass 2, and their `--log` paths differ (AC-7.1).
   WIRE-PIN.
2. `test_audit_cycle_unknown_surface_names_agy_codex_grok` — `--surfaces agy,gpt`: rc 2, stderr
   contains `(agy|codex|grok)` (AC-7.1).

**Expected RED split**: 2 failing, 0 passing. **Regression guards**: none here; the existing
`test_hmad_dispatch_audit_cycle.py` (AC-7.5) runs in the full suite.
**WIRE-PIN RED reason**: the validation refuses `grok` (rc 2), so the rc and trace assertions fail.
**Wire-scoped revert**: the case line back to `agy|codex) ;;` only; the pin fails. Executed and
scored as row WR11 (Task 14, `grok_wire_reverts.json`), whose `find` is the landed
`case "$_s" in agy|codex|grok) ;;` (exactly once; the six-line `agy|codex|grok` census of Task 16
counts lines, and only this one carries the `case "$_s" in` prefix).
**Force-fire**: row W8 (Task 14).

**Acceptance Criteria**:
- [ ] AC-7.1: `--surfaces agy,grok` dispatches pass 2 through `_cmd_exec grok` with its own `--log`;
      `--surfaces agy,gpt` returns 2 naming `agy|codex|grok`.

**Mutation rows** (Task 14): W8 (`grok_exec.json`) and WR11 (`grok_wire_reverts.json`) — 2 rows.

**Dependencies on other tasks**: Task 9, Task 10

---

## Task 12: tdd-gate-fallback-agent

**Production file**: `h-mad/scripts/h_mad_tdd_judge.py`, `h-mad/hooks/h-mad-tdd-gate.sh`
**Test file**: `h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/h_mad_tdd_judge.py:format_state_line` → `_fallback_fold (the fallback= field of the TDD-STATE line)`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py::test_format_state_line_emits_the_fallback_fold`
**WIRE 2**: `h-mad/hooks/h-mad-tdd-gate.sh:_read_state` → `the state line's fallback= field, refused fallback-grok or fallback-invalid after the codex-authorship refusal`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py::test_block_grok_reads_the_active_features_fallback_agent`

**Description**: FR-2 / grok design v1.3 §D2 (which adopts §"Deviations from design v1.2",
item 5) onto the merged gate (merged §D13) / plan W9, which is two WIRE entries here: the
judge half (the fold) and the gate half (the read). Read at HEAD `6277d703`, where both production
files are byte-identical to `8ef6009f` (`git diff --quiet 8ef6009f HEAD -- h-mad/hooks
h-mad/scripts/h_mad_tdd_judge.py` exits 0):
- the judge: `_fallback_tag(state)` maps one record to `absent`, `null`, `grok`, `claude` or
  `invalid:` followed by `json.dumps(value, separators=(",", ":"))`, with the `isinstance(value, str)` test
  first; `_active_records` stores it in `Record.fallback` for every `step5` record;
  `format_state_line` builds `line = f"TDD-STATE: active codex-escape=… blocker={blocker}
  records={len(chain.records)}"` on the one line after the `# M:C5` line, then appends one
  `record=` word per record (key, codex_status, state file and fallback tag, comma-separated);
- the gate: `STATE_ACTIVE_RE` is a single-quoted ERE assigned after the `_chain_may_hold_state`
  fast path; `_read_state` captures `BASH_REMATCH[1..3]` into `ESCAPE`, `BLOCKER`, `RECORDS`,
  walks the `record=` words under `set -f`, cross-checks count, escape/blocker and
  `BLOCKER -le RECORDS`, and sets `BLOCKER_RECORD`; the codex-authorship refusal is the `if` whose
  condition is `[ -z "${HMAD_CODEX_UNAVAILABLE:-}" ] && [ "$ESCAPE" = no ] && command -v codex`,
  and the `JOUT=$(python3 "$JUDGE" judge …)  # M:W2` line follows its `fi`.

The fold lands in the judge, the field on the state line, and the gate block between that `fi` and
the `JOUT` line, so it runs only when codex is out (merged §D13 item 3). No committed anchor line
is edited (the edited judge line and the edited `_read_state` lines carry no `# M:` marker and are
in no committed `find`). Executed for v1.5 on a deleted scratch copy (`git archive HEAD h-mad` at
`6277d703`, the code block below and migrations 1–3 applied): `--check-anchors` on each of the six
committed specs Task 14 re-runs read `ANCHORS_OK` (37 + 6 + 8 + 6 + 3 + 6 rows), and
`test_h_mad_tdd_judge.py` with `test_h_mad_tdd_gate_judge.py` read `193 passed`.

The new `# M:` markers are `F0` (the judge's state line), `F1` (the tag agreement check), `F2`
(the fold's `grok` scan), `F3` (the gate's read of the field) and `F4` (the range check). They
name lines for rows G8, G9, WR12-1 and WR12-2 and for a reader; no committed marker is `M:F*`
(`grep -rn 'M:F' h-mad` → 0 matching lines at `6277d703`).

**Code structure** (landed literally; rows G1–G12, WR12-1 and WR12-2 anchor it):
```python
# h_mad_tdd_judge.py — new function, after _active_records and before read_chain:
def _fallback_fold(records: Sequence[Record]) -> str:
    invalid = next((i for i, r in enumerate(records, 1) if r.fallback.startswith("invalid:")), 0)
    if invalid:
        return f"invalid:{invalid}"
    grok = next((i for i, r in enumerate(records, 1) if r.fallback == "grok"), 0)  # M:F2
    if grok:
        return f"grok:{grok}"
    return "none"

# format_state_line — the one `line = f"TDD-STATE: active …"` line becomes:
    line = (f"TDD-STATE: active codex-escape={'yes' if escape else 'no'} blocker={blocker} "
            f"records={len(chain.records)} fallback={_fallback_fold(chain.records)}")  # M:F0
```
```bash
# h-mad-tdd-gate.sh — STATE_ACTIVE_RE gains the field after records= (whole line, one assignment):
STATE_ACTIVE_RE='^TDD-STATE: active codex-escape=(yes|no) blocker=(0|[1-9][0-9]*) records=([1-9][0-9]*) fallback=(none|(grok|invalid):([1-9][0-9]*))( record=[^ ,]+,[^ ,]+,[^ ,]+,(absent|null|grok|claude|invalid:[^ ,]+))+$'

# _read_state — after `RECORDS=${BASH_REMATCH[3]}`; the `local` line gains frecord:
  FALLBACK=${BASH_REMATCH[4]}  # M:F3
  FALLBACK_POS=${BASH_REMATCH[6]:-0}
  local word count=0 record="" frecord=""
# inside the record= loop, after the BLOCKER line:
      if [ "$count" = "$FALLBACK_POS" ]; then frecord=${word#record=}; fi
# after `[ "$BLOCKER" -le "$RECORDS" ] || …`, around the existing BLOCKER_RECORD line:
  [ "$FALLBACK_POS" -le "$RECORDS" ] || _refuse judge-error "state fallback position out of range"  # M:F4
  BLOCKER_RECORD=$record
  FALLBACK_RECORD=$frecord

# between the codex-authorship `fi` and the `JOUT=` line:
# fallback_agent (FR-2): reached only when codex is out, because the codex-authorship refusal
# above fires in every other case. The judge folds every ACTIVE record into the state line's
# `fallback=` field (any invalid record, else any grok record, else none) and names the
# governing record by position; this block checks only that the fold's kind agrees with that
# record's tag, and applies no rule over the records of its own.
if [ "$FALLBACK" != none ]; then
  FB_KEY=$(_pct_decode "${FALLBACK_RECORD%%,*}")
  FB_FILE=${FALLBACK_RECORD#*,}; FB_FILE=${FB_FILE#*,}; FB_FILE=$(_pct_decode "${FB_FILE%%,*}")
  FB_TAG=${FALLBACK_RECORD##*,}
  case "$FALLBACK" in
    grok:*)    [ "$FB_TAG" = grok ] ;;
    invalid:*) [ "${FB_TAG#invalid:}" != "$FB_TAG" ] ;;
  esac || _refuse judge-error "state fallback=$FALLBACK disagrees with its record's tag $FB_TAG"  # M:F1
  case "$FALLBACK" in
    grok:*)
      _refuse fallback-grok "fallback_agent=grok — Phase 5 is authored by grok while codex is out, not by Claude.
Dispatch this module to grok: hmad-dispatch exec grok <promptfile>  (stage it with h_mad_assemble_tdd.py --agent grok).
HMAD_CODEX_UNAVAILABLE does not override fallback_agent=grok. For a one-off Claude escape, record it —
  python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $FB_KEY --set fallback_agent=claude \"$FB_FILE\"" ;;
    invalid:*)
      FB_VALUE=$(_pct_decode "${FB_TAG#invalid:}")
      _refuse fallback-invalid "fallback_agent=$FB_VALUE is not valid (valid: grok|claude) — refusing the write, fail-closed.
  Fix it: python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $FB_KEY --set fallback_agent=grok|claude|null \"$FB_FILE\"" ;;
  esac
fi
```
Every refusal goes through `_refuse`, so the hook keeps no `exit 1`
(`test_h_mad_tdd_gate_judge.py::test_hook_has_no_exit_1`) and no `jq` or `orchestrator_state` token
(`test_claude_gate_keeps_no_private_state_reader`). `_pct_decode` of the `invalid:` payload yields
`json.dumps(value, separators=(",", ":"))` byte for byte (merged §D13 item 4). Executed on the scratch copy
(deviation 5): `"null"` → first stderr line
`[H-MAD-TDD-GATE] BLOCK kind=fallback-invalid: fallback_agent="null" is not valid (valid: grok|claude) — refusing the write, fail-closed.`;
`{"a":[1,2]}` → `fallback_agent={"a":[1,2]}`; records `a` absent, `b` `grok`, `c` `false` →
`fallback=invalid:3`; `grok` with `HMAD_CODEX_UNAVAILABLE=1` and `codex` on PATH → `fallback-grok`;
`grok` with `codex` on PATH and nothing else → `codex-authorship`; `claude`, and an absent key beside
a `step3` `other` holding `grok` → rc 0 with empty stdout (ALLOW) when `python3` is an interpreter
with pytest.

**The tag agreement check** (grok design v1.3 §D2, "How the gate consumes it", item 4; answers the
v1.4 delta review's first should-fix). The `# M:F1` statement refuses `judge-error` when the fold
names a record whose tag is not of the fold's kind: `grok:B` needs the tag `grok`, and `invalid:B`
needs a tag beginning `invalid:`. A `case` that matches neither arm exits 0, so `fallback=none`
never reaches it (the enclosing `if` already skips it). It is the third member of the class "a
line-level summary field that names a record", beside the committed `records`-against-count and
`codex-escape`-against-`blocker` cross-checks. Executed for v1.5 on the scratch copy above, through
`_tree_b` stub state lines with `codex-escape=yes`: `fallback=invalid:1` naming a record tagged
`grok` → first stderr line
`[H-MAD-TDD-GATE] BLOCK kind=judge-error: state fallback=invalid:1 disagrees with its record's tag grok`;
`grok:1` naming `invalid:false` or `absent`, and `invalid:1` naming `claude`, → `judge-error`;
`grok:1` naming `grok` → `fallback-grok`; `invalid:1` naming `invalid:false` → `fallback-invalid`.
Each arm was then replaced by `true` alone (rows G11 and G12): the `grok:*` arm's mutant failed
exactly the two items of test 17, and the `invalid:*` arm's mutant exactly the two items of test 18.
**Residual** (grok design v1.3 §D2, stated there as (a)–(c)): the gate checks the fold only against
the one record it names, because checking any other record would re-apply the fold, which merged
§D13 item 1 forbids in the gate. A `fallback=none` while some record's tag is `grok` or begins `invalid:`
still reaches the judge verb (fail-open with respect to FR-2); a `grok:B` beside an `invalid:` record
still refuses, as `fallback-grok`; a `B` that is not the first of its kind names a later record in
the remedy. All three are judge defects, pinned on the judge side by rows G7, G8 and WR12-1 and by
tests 13–16.

**Migration edits** (committed files outside the test file; all land in the RED commit, because
they are test and spec files, and deviation 5 lists the 25 committed items they turn RED):
1. `h-mad/tests/test_h_mad_tdd_judge.py` — `ACTIVE_RE`'s second string line (line 27)
   `    r"records=([1-9][0-9]*)( record=[^ ,]+,[^ ,]+,[^ ,]+,"` becomes
   `    r"records=([1-9][0-9]*) fallback=(none|(grok|invalid):([1-9][0-9]*))( record=[^ ,]+,[^ ,]+,[^ ,]+,"`.
   **Residual (drift):** `ACTIVE_RE` is a hand-copied second spelling of the hook's
   `STATE_ACTIVE_RE`, and no committed test reads the hook's literal (`grep -rn STATE_ACTIVE_RE
   h-mad/tests` → 0 matching lines at `6277d703`). Test 16 reads the literal out of the hook, so the
   fold field is single-sourced by test from Task 12 on; the rest of `ACTIVE_RE` stays a hand copy
   that this migration keeps in step by hand. Merged §D13 item 5 asks for one round-trip row per
   fold outcome in the merged §D10 round-trip test; those rows are test 16 here rather than rows of the
   committed `test_fallback_tag`, because test 16 reads the hook's own literal.
2. `h-mad/tests/test_h_mad_tdd_gate_judge.py` — `_tree_b`'s default `state_line` gains
   ` fallback=none` after `records=1`.
3. `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json` — rows `W5BF`, `W5BF2` and `W5BF3`:
   each `replace` gains ` fallback=none` after `records=1`. Their `find` (the committed `# M:W5B`
   line) is unchanged. Without this edit the three mutants' forced state line fails the new ERE and
   is refused `judge-error`, so the rows would stay caught through the ERE instead of the governance
   path they were written for.
4. `h-mad/tests/grokfixtures.py` — line 13 `BASE_SHA = "5a9cd8ed693202e0291a9c6d5a3a63207b1f1b14"`
   becomes `BASE_SHA = "8ef6009f9491796d5d16b96a54e3b3185a8a6f19"` (Preamble, "Re-pinned after the
   rebase"). Test 6 compares against the gate at that commit. Not yet done at `6277d703`.
5. `h-mad/tests/test_h_mad_assemble_tdd_agent.py` — `BASE_SHA = "507214d"` → `BASE_SHA =
   "8ef6009f"` (line 20). **Done** by commit `f2ff9261`, before this revision; listed here because
   v1.4's list missed it (Preamble, "The second constant"). Task 12 does not touch it again.

**Test harness.** The hook under test is the worktree's (`test_h_mad_tdd_gate_judge.HOOK`,
`Path(__file__).resolve().parents[1] / "hooks" / "h-mad-tdd-gate.sh"`). The file imports
`from test_h_mad_tdd_gate_judge import _bin, _gate, _tree_b` and
`from tdd_gate_support import decision, hook_form, write_state`, and `h_mad_tdd_judge` as a module
(Convention 3: `judge._fallback_fold` is never named, so no RED is an `AttributeError`). Each cell
builds `root = tmp_path / "repo"` with `write_state(root, {"other": {...}, "feat": {...}})`, `other`
written FIRST (a `step3` record with no `fallback_agent` unless a test says otherwise; the G3
discriminator, because the G3 mutant reads the file's first record), plus
`shared/tests/test_widget.py` holding one failing test; the target `shared/widget.py` does not
exist, and the judge's name map resolves it to that test. It runs
`_gate(root, arg="shared/widget.py", bin_dir=_bin(tmp_path, codex=codex_on_path), extra_env=env)`, where `codex_on_path` and `env` are the cell's axis values:
`PATH` is `f"{bin_dir}:/usr/bin:/bin"`, where `_bin` links `python3` to the test runner's
`sys.executable` (an interpreter with pytest; a bare `python3` without it turns every FALL-THROUGH
into `pytest-missing`, executed), `dirname`, `basename`, the real `jq` whenever `shutil.which("jq")`
finds one (`_bin`'s `jq=True` default, `test_h_mad_tdd_gate_judge.py:42–55`; inert, because the
merged gate runs no `jq`), and a `codex` stub when asked; in the environment, `HOME` and
`CLAUDE_PROJECT_DIR` are set beside `PATH` and nothing else is inherited; `stdin` is `subprocess.DEVNULL` (merged §D13's
harness item). A cell with `codex` off PATH first asserts
`shutil.which("codex", path=f"{bin_dir}:/usr/bin:/bin") is None` (`/usr/bin/codex` and `/bin/codex` do not
exist on this host). Outcomes are read with `decision(result, hook_form(HOOK))`: BLOCK-CODEX is
`deny` kind `codex-authorship`; BLOCK-GROK is `deny` kind `fallback-grok`; BLOCK-INVALID is `deny`
kind `fallback-invalid`; FALL-THROUGH is `allow` (rc 0, empty stdout, the judge measured the
failing test). The stub tests (11, 12, 17, 18, 19) build `root = _root(tmp_path)` (imported from
`test_h_mad_tdd_gate_judge`, so the root holds a state file and the gate's
`_chain_may_hold_state` fast path does not allow first), run `_gate(root, arg=str(root / TARGET),
bin_dir=_bin(tmp_path), hook=hook)` with `TARGET` from the same module, and take `hook` from
`_tree_b(tmp_path, state_line=<the test's line>,
judge_line="TDD-JUDGE: ALLOW kind=red-measured source=impl-plan test=x\n")`, so a line the gate
wrongly accepts reads as `allow`, never as a stub-made `judge-error`. Their state lines all begin
`TDD-STATE: active codex-escape=yes blocker=0 records=1` (codex out by the escape), and tests
17–19 continue ` fallback=<fold> record=feat,exhausted,/x/docs/.bkit-memory.json,<tag>`.

**Tests** (192 collected items):
1. `test_gate_matrix` (80) — 4 `codex_status` × 5 `fallback_agent` (absent, `null`, `"claude"`,
   `"grok"`, `"codex"`) × 2 env × 2 PATH; the expected class comes from an in-test transcription of
   the FR-2 table (codex_out = env set, or `codex_status` in `unavailable|exhausted`, or `codex` off
   PATH), never from the hook; every cell asserts the derived test path exists as a precondition
   (AC-2.1).
2. `test_invalid_class_blocks_each_value_alone` (24) — `false`, `true`, `0`, `"null"`, `""`,
   `"Grok"`, `{}`, `[]`, each alone, under each of the three codex_out routes alone: BLOCK-INVALID,
   and stderr contains `"fallback_agent=" + json.dumps(value, separators=(",", ":"))` and `grok|claude`
   (AC-2.1b, AC-2.4).
3. `test_invalid_class_with_codex_available_is_block_codex` (8) — the same 8 values, codex_out false
   → BLOCK-CODEX (AC-2.1b).
4. `test_json_null_control_falls_through` (3) — stored JSON `null`, three routes (AC-2.1b control).
5. `test_absent_key_control_falls_through` (3) — no key, three routes (AC-2.1b control).
6. `test_absent_null_claude_match_the_base_hook` (48) — for `fallback_agent` absent, `null` and
   `"claude"`, each of the 16 cells (4 `codex_status` × 2 env × 2 PATH): rc, stdout and stderr equal,
   byte for byte, those of the base hook run the same way on the same project. The base hook is
   `base_dir / "h-mad/hooks/h-mad-tdd-gate.sh"`, where the module-scoped fixture `base_dir` (a
   `tmp_path_factory` directory) holds the output of `git -C REPO archive BASE_SHA h-mad` piped into
   `tar -x -C base_dir`, with `REPO = Path(__file__).resolve().parents[2]` and `BASE_SHA` read from
   `grokfixtures`, because the merged
   hook finds its judge beside its own realpath: a lone `git show` of the hook file finds no judge
   and refuses `judge-error` (AC-2.2, which since spec v1.5 names `git archive <base> h-mad` and
   the run from the base gate's own tree).
7. `test_block_grok_stderr_names_the_four_things` — `hmad-dispatch exec grok`, `--agent grok`,
   `--set fallback_agent=claude`, `HMAD_CODEX_UNAVAILABLE does not override fallback_agent=grok`
   (AC-2.3).
8. `test_block_grok_reads_the_active_features_fallback_agent` — `feat` holds `fallback_agent:
   "grok"`, `codex_status: "exhausted"`: BLOCK-GROK, and stderr names `--feature feat`. WIRE-PIN 2.
9. `test_other_feature_grok_does_not_change_active_outcome` — `other` (`step3`) holds `"grok"`,
   `feat` (`step5`) holds none, both `exhausted`: FALL-THROUGH (AC-2.5, first case).
10. `test_exempt_files_stay_exempt_under_grok` (7) — targets `shared/test_widget.py`,
    `shared/tests/helpers.py`, `shared/fixtures/data.py`, `docs/notes.md`, `shared/config.toml`,
    `shared/run.sh`, `shared/widget.js`, with `feat` at `"grok"` and codex_out true: `allow` (AC-2.6).
11. `test_state_stub_fallback_field_is_judge_error[missing-field|unknown-kind|position-zero]` (3) —
    stub state lines `TDD-STATE: active codex-escape=yes blocker=0 records=1 record=feat,exhausted,/x/docs/.bkit-memory.json,absent`
    (`missing-field`), and the same line with ` fallback=codex:1` (`unknown-kind`) or
    ` fallback=grok:0` (`position-zero`) inserted after `records=1`: `deny` kind `judge-error` (the
    closed grammar; the successor of v1.3's `*)` arm, merged §D13; FR-2 "Kinds").
12. `test_state_stub_fallback_position_out_of_range_is_judge_error` — the same stub with
    ` fallback=grok:2` and `records=1`: `deny` kind `judge-error` (merged §D13 item 5's `B` ≤
    `records`; FR-2 "Kinds").
13. `test_fold_invalid_record_governs_over_grok` — two `step5` records, `a` holding `"grok"` and `b`
    holding `false`, both `exhausted`: BLOCK-INVALID naming `fallback_agent=false` and
    `--feature b` (AC-2.5, third case; merged §D13 item 2).
14. `test_second_active_record_holding_grok_blocks` — `a` with no key, `b` holding `"grok"`, both
    `step5` and `exhausted`: BLOCK-GROK naming `--feature b` and `b`'s state file (AC-2.5, second
    case; merged §D13 item 2).
15. `test_format_state_line_emits_the_fallback_fold` — `judge.format_state_line(judge.read_chain(root,
    None), root)` on one `step5` record holding `"grok"` contains ` records=1 fallback=grok:1 record=`.
    WIRE-PIN 1.
16. `test_fold_outcome_round_trips_through_the_gate_ere[none|grok|invalid]` (3) — for a chain whose
    fold is `none`, `grok:1` and `invalid:2`, the `format_state_line` output fullmatches the
    `STATE_ACTIVE_RE` literal read out of the hook source (`^STATE_ACTIVE_RE='(.*)'$`, one match),
    and that match's group 4 equals the fold (merged §D13 item 5, one round-trip row per fold
    outcome; the rows live in this new file rather than in the committed `test_fallback_tag`, whose
    only edit is migration 1).
17. `test_state_stub_grok_fold_naming_a_non_grok_record_is_judge_error[invalid-false|absent]` (2)
    — stub ` fallback=grok:1` with the record's tag `invalid:false` or `absent`: `deny` kind
    `judge-error` (grok design v1.3 §D2 tag agreement, `grok:*` arm; row G11).
18. `test_state_stub_invalid_fold_naming_a_valid_record_is_judge_error[grok|claude]` (2) — stub
    ` fallback=invalid:1` with the record's tag `grok` or `claude`: `deny` kind `judge-error`, and
    for `grok` stderr contains `disagrees with its record's tag grok` (the `invalid:*` arm; row G12).
19. `test_state_stub_agreeing_fold_refuses_its_own_kind[grok|invalid]` (2) — the agreeing
    controls: ` fallback=grok:1` with the tag `grok` → `deny` kind `fallback-grok`;
    ` fallback=invalid:1` with the tag `invalid:false` → `deny` kind `fallback-invalid`, stderr
    naming `fallback_agent=false` (the check passes agreeing lines through).

**Expected RED split**: 64 failing, 128 passing (of the 192 new items), and the 25 committed items
of deviation 5 failing on migrations 1 and 2 (executed on a scratch copy at HEAD `d9574614` with
only the two test edits applied: `25 failed, 168 passed` over the two files; copy deleted).
Failing: the 28 matrix cells with codex_out true and `fallback_agent` `"grok"` or `"codex"`, the 24
invalid-class cells, tests 7 and 8, the `missing-field` item of test 11, tests 13, 14 and 15, the
3 items of test 16 (at RED the hook's ERE fullmatches the old line and group 4 is the last
`record=` word), the `grok` item of test 18 (its stderr assertion names a diagnostic the RED gate
cannot print: it reads `state verb printed no well-formed state line`), and the 2 items of test 19 (at RED the old ERE refuses the line `judge-error`).
**Regression guards** (128): the 52 other matrix cells (10 with codex_out false, 42 with codex_out
true and `fallback_agent` absent, `null` or `"claude"`), the 8 BLOCK-CODEX cells, the 3 + 3
controls, the 48 base-comparison cells (the worktree gate equals the base gate at RED), test 9, the
7 exemption cells, the `unknown-kind` and `position-zero` items of test 11, test 12, and the 2 items of
test 17 and the `claude` item of test 18 (the old ERE already rejects those lines `judge-error`; they discriminate
at GREEN, through rows G11 and G12). Tests 17–19 were executed for v1.5 as a scratch probe (deleted;
it also held one print-only item, excluded here): on the unedited hook their six items read 2
failed (test 19's) and 4 passed; on the scratch copy with the code block applied, 6 passed.
Test 17's ids are set explicitly (`ids=["invalid-false", "absent"]`), because a `:` in a
parametrize id is legal but reads as a node-id separator.
**WIRE-PIN RED reasons**: pin 1 — `format_state_line` returns a line with no ` fallback=` field,
an assertion on the caller's return value; the test names no new symbol. Pin 2 — the hook runs the
judge, which measures the failing test and allows: an assertion on the hook's decision.
**Wire-scoped reverts**: WIRE 1 — `fallback={_fallback_fold(chain.records)}` → `fallback=none` in
the `# M:F0` line only: every state line says `none`, and pin 1 fails. WIRE 2 —
`FALLBACK=${BASH_REMATCH[4]}` → `FALLBACK=none` in the `# M:F3` line only: the gate never enters
the block, and pin 2 fails. Executed and scored as rows WR12-1 and WR12-2 (Task 14,
`grok_wire_reverts.json`). Merged §D13 names forcing `Record.fallback` to `absent` as "the
equivalent revert" of v1.3's WR12. That edit severs the merged feature's own wire (`_active_records` →
`_fallback_tag`), which its committed `test_fallback_tag` rows already pin, so this plan scores the
removal of the two wires Task 12 adds instead.
**Force-fires**: rows G2 (BLOCK-GROK bypassed by the env) and G3 (the fold fed another feature's
record; design W9's alias) (Task 14).

**Wire registry move** (answers the v1.4 delta review's third should-fix; Task 12 owns it).
`.h-mad/wires.jsonl` line 38 at `6277d703` still holds v1.3's single record for this task:
`"id": "Task 12"`, `"caller": "h-mad/hooks/h-mad-tdd-gate.sh:Codex-authorship enforcement block"`,
`"callee": "typed fallback_agent read of ACTIVE"`, `"status": "active"`; both names are text the
merged gate deleted. The file has 38 lines, 13 of them `grok-codex-fallback` records (unit: matching
lines). A record's identity is `(owning_feature, id)` (`_record_key`,
`h-mad/scripts/h_mad_wire_registry.py:25`), and the wire-pin gate registers a numbered WIRE under the
id `"<task id> (WIRE <n>)"` (`h-mad/scripts/h_mad_wire_pin_gate.py:370`), so re-registration adds
`Task 12 (WIRE 1)` and `Task 12 (WIRE 2)` beside the old record and does not replace it. Deleting the
old line is not the repair: at `8ef6009f` the registry holds no `grok-codex-fallback` record, so
`compare` against that base would report nothing, which is the silent removal the tombstone fields
exist to prevent. The v1.3 record became WIRE 2 (same pin, gate half), so it is retired as
`renamed`. Task 12 runs both steps from the worktree root, as its first step, and commits
`.h-mad/wires.jsonl` in its RED commit:

```bash
python3 h-mad/scripts/h_mad_wire_pin_gate.py docs/01-plan/features/grok-codex-fallback.impl-plan.md --feature grok-codex-fallback
# read: WIREPIN: PASS tasks=17 wiring=8 unpinned=0 mislabeled=0   and   registration: registered=14 skipped=0
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, "h-mad/scripts")
import h_mad_wire_registry as reg
path = Path(".h-mad/wires.jsonl")
old = [r for r in reg.load(path) if (r["owning_feature"], r["id"]) == ("grok-codex-fallback", "Task 12")]
assert len(old) == 1 and old[0].get("status", "active") == "active", old
tomb = dict(old[0], status="removed", removal_provenance="renamed",
            removed_by_feature="grok-codex-fallback",
            successor_pin="h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py::test_block_grok_reads_the_active_features_fallback_agent")
reg.register([tomb], path)
print("TOMBSTONE: OK")
PY
```

The first command upserts all 14 WIRE records as one batch: the 12 of Tasks 3–11 keep every field
but `registered_ts`. The second keeps the old record's `caller`, `callee` and `pin`, and adds the
fields `validate_record` (`h_mad_wire_registry.py:112–123`) requires of a removed record:
`removal_provenance` in `superseded|pinned-a-defect|renamed`, `removed_by_feature`, and for
`renamed` a `successor_pin`. The `register` CLI verb cannot write them (it has no status or
provenance flag), hence the Python call. Executed for v1.5 on a scratch copy of the registry
(deleted; the tree's registry unchanged): `WIREPIN: PASS tasks=17 wiring=8 unpinned=0
mislabeled=0`, `registration: registered=14 skipped=0`, `TOMBSTONE: OK`, then 40 records, 15 of
them `grok-codex-fallback`: `Task 12` removed/renamed, `Task 12 (WIRE 1)` and `Task 12 (WIRE 2)`
active. At 5f, `partition` resolves a `renamed` record's `successor_pin` and runs it, so WIRE-PIN 2
runs twice (once for `Task 12 (WIRE 2)`, once for the tombstone); this is harmless, and it is the
same node.

**Acceptance Criteria**:
- [ ] AC-2.1: all 80 cells match the table.
- [ ] AC-2.1b: 24 BLOCK-INVALID cells, 8 BLOCK-CODEX cells, and the JSON-`null` and absent controls.
- [ ] AC-2.2: absent, `null` and `"claude"` equal the base hook (the gate at `BASE_SHA`, run from
      its own tree) in rc, stdout and stderr, in all 16 cells each.
- [ ] AC-2.3, AC-2.4, AC-2.5, AC-2.6 as the tests state.
- [ ] AC-2.7: the gate's mutation spec (Task 14) carries G1–G3, each killed by an AC-2.1 cell.
- [ ] Merged §D13 items 2 and 5: the fold is order-independent and most-restrictive (tests 13, 14),
      and the closed grammar refuses a missing, unknown or out-of-range field (tests 11, 12).
- [ ] Grok design v1.3 §D2 tag agreement: a fold whose kind disagrees with its governing record's
      tag is `judge-error`, each arm alone (tests 17, 18), and an agreeing fold refuses its own
      kind (test 19).
- [ ] The migrated committed files pass in full at GREEN: `test_h_mad_tdd_judge.py` and
      `test_h_mad_tdd_gate_judge.py` (193 items on the scratch copy), and the full coupled suite.
- [ ] `.h-mad/wires.jsonl` holds `Task 12 (WIRE 1)` and `Task 12 (WIRE 2)` active and `Task 12`
      removed with `removal_provenance` `renamed` (§"Wire registry move"), committed in the RED
      commit.

**Mutation rows** (Task 14): G1–G12 (`tdd_gate_fallback_agent.json`, 12) and WR12-1, WR12-2
(`grok_wire_reverts.json`, 2) — 14 rows. Task 14 also re-runs the six committed specs with a row on
either production file (claude_gate_judge_wiring.json and the five `tdd_judge_*.json`).

**Dependencies on other tasks**: Task 1

---

## Task 13: grok-two-instruments

**Production file**: none (this task writes one test file and no production code)
**Test file**: `h-mad/tests/test_grok_two_instruments.py`
**Task shape**: `gate`

**Description**: The cross-surface single-source tests (design Test Plan and Invariant Compliance,
base §"Single-source contract"). Each rule implemented on both sides of the shell/Python line gets
one agreement test. Nothing is implemented here: every test must pass on first run, and a failure
is a finding against the task that owns the diverging surface (halt, do not edit the test).

**Tests** (23 collected items):
1. `test_format_agreement[f0|f_spaced|f_trunc|agy|codex_banner|mixed|banner_then_f0|window_edge]`
   (8) — `progress`'s `format:` and `measure_effort()["shape"]` agree under `agy-ndjson ↔ parsed`,
   `grok-ndjson ↔ grok | grok-truncated`, `codex-text ↔ codex-text | unparseable`; `codex_banner` is
   `"OpenAI Codex v0.145.0\nexec\n"`.
2. `test_depth_bound_literals_agree` — the `_GROK_MAX_DEPTH=` literal parsed out of
   `hmad-dispatch.sh` equals `h_mad_review_evidence.GROK_MAX_DEPTH`.
3. `test_depth_boundary_agrees_across_surfaces[64|65]` (2) — `progress` format and
   `scan_grok(...) is not None` agree on `depth_line(k)`.
4. `test_f_deep_readers_agree_with_scan_grok[64|65]` (2) — on `f_deep(k)`, `_grok_region_state` is
   `complete` iff `scan_grok()["complete"]`, and the N of `_grok_last_tool` equals `scan_grok()["ok"]`.
5. `test_key_order_detection_agrees[key_order|bogus]` (2) — AC-5.2b's two lines on both surfaces.
6. `test_banner_wins_on_all_three_surfaces` — `banner_then_f0()`: `progress` → `codex-text`, the CLI
   prints no `format=grok`, `measure_effort` → `codex-text` (AC-11.3).
7. `test_window_edge_cli_and_measure_effort_agree` — `window_edge_log()`: the CLI prints a
   `format=grok` line and `measure_effort` shape is `grok`.
8. `test_completeness_and_n_single_sourced[f0|f_trunc|f_notools|f_shared_region|f_beat]` (5) — via
   `run_fn`, `_grok_region_state` is `complete` iff `scan_grok()["complete"]`, and the N in
   `_grok_last_tool`'s line equals `scan_grok()["ok"]` on the same region text (design V13 values).
9. `test_type_vocabulary_single_sourced` — the `_GROK_TYPES_RE` literal, split on `|`, equals
   `h_mad_review_evidence._GROK_TYPES` as a set.

**Expected RED split**: 0 failing, 23 passing. **Regression guards**: all 23 (the surfaces they compare
landed in Tasks 5–10).

**Acceptance Criteria**:
- [ ] AC-5.2b: the shell and Python detectors agree on both lines and at the depth boundary.
- [ ] AC-11.3 on all three surfaces in one test.
- [ ] Completeness, N, the depth bound and the vocabulary are pinned equal across surfaces.

**Mutation rows**: none of its own (its tests are informational killers for L4 and E5; the rows'
`test` keys name the owning tasks' tests).

**Dependencies on other tasks**: Task 4, Task 6, Task 7, Task 10

---

## Task 14: mutation-specs-and-force-fires

**Production file**: none (seven new JSON specs under `h-mad/tests/mutation-specs/`, no code)
**Test file**: none (the killing tests belong to Tasks 3–12)
**Task shape**: `operational`

**Description**: Author the seven spec files with exactly the 65 rows below, then for each spec run
`python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors <spec>` (read `ANCHORS:`) and
`python3 h-mad/scripts/h_mad_mutation_harness.py <spec>` (read `MUTATION:`). The pass condition is
`ANCHORS_OK` and `MUTATION: ALL_CAUGHT` for all seven; `SURVIVED` or `REFUSED` halts and is reported
against the owning task. Also run the design's W1 residual precondition
`PATH=/usr/bin:/bin command -v grok` (must fail, rc 1) before scoring row W1.

**Committed specs re-run** (v1.4). Task 12 edits `hooks/h-mad-tdd-gate.sh` and
`scripts/h_mad_tdd_judge.py`, and migrates two committed test files and one committed spec
(Task 12, "Migration edits"). Every committed spec with a row on either production file is
therefore re-run the same two ways and must read `ANCHORS_OK` and `MUTATION: ALL_CAUGHT`: the six
are `claude_gate_judge_wiring.json` (37 rows: 33 on the gate, 3 on the judge, 1 on
`tests/test_h_mad_tdd_gate_docs.py`), `tdd_judge_chain.json` (6), `tdd_judge_resolution.json` (8),
`tdd_judge_scoring.json` (6), `tdd_judge_venv.json` (3) and `tdd_judge_wiring.json` (6), read by
`file` key at HEAD `d9574614`. `codex_gate_judge_wiring.json` (all 17 rows on
`hooks/h-mad-codex-tdd-gate.py`) and `audit_suite_summary_line.json` name neither file and are not
re-run.

In the tables, `⏎` inside a `find`/`replace` stands for a newline and `\|` for a literal `|`; each cell is the raw source text,
and JSON escaping (`\"`, `\\`, `\n`) is applied when it is written into the spec. **Every row carries
its own `file` key**, because the harness requires `file` on every row
(`h-mad/scripts/h_mad_mutation_harness.py:290`) and all 907 committed rows carry one. A spec header
below naming one file gives that file to every row of its table; `tdd_gate_fallback_agent.json`'s and
`grok_wire_reverts.json`'s tables have a `file` column, because their rows name two and six
different files.

**`tdd_gate_fallback_agent.json`** (re-derived in v1.4 onto Task 12's re-planned code; every v1.3
row anchored on text the merged gate deleted; G11 and G12 added in v1.5 from grok design v1.3);
`command`
`["python3.11","-m","pytest","tests/test_h_mad_tdd_gate_fallback_agent.py","-q"]`; `target_command`
`["python3.11","-m","pytest","-q"]`.

| Row | name | file | find | replace | test |
|---|---|---|---|---|---|
| G1 | `g1-block-grok-falls-through` | `hooks/h-mad-tdd-gate.sh` | `    grok:*)⏎      _refuse fallback-grok` | `    grok:*) ;;⏎    __never__)⏎      _refuse fallback-grok` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_gate_matrix` |
| G2 | `g2-env-bypasses-block-grok` | `hooks/h-mad-tdd-gate.sh` | `      _refuse fallback-grok` | `      [ -n "${HMAD_CODEX_UNAVAILABLE:-}" ] \|\| _refuse fallback-grok` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_gate_matrix` |
| G3 | `g3-reads-another-feature` | `scripts/h_mad_tdd_judge.py` | `path, _fallback_tag(value))` | `path, _fallback_tag(next(iter(states.values()))))` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_gate_matrix` |
| G4 | `g4-block-invalid-falls-through` | `hooks/h-mad-tdd-gate.sh` | `    invalid:*)⏎      FB_VALUE` | `    invalid:*) ;;⏎    __never__)⏎      FB_VALUE` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_invalid_class_blocks_each_value_alone` |
| G5 | `g5-string-null-collapses` | `scripts/h_mad_tdd_judge.py` | `        if value in ("grok", "claude"):` | `        if value in ("grok", "claude", "null"):` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_invalid_class_blocks_each_value_alone` |
| G6 | `g6-falsy-reads-as-absent` | `scripts/h_mad_tdd_judge.py` | `    if "fallback_agent" not in state:` | `    if not state.get("fallback_agent"):` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_invalid_class_blocks_each_value_alone` |
| G7 | `g7-invalid-never-governs` | `scripts/h_mad_tdd_judge.py` | `    if invalid:` | `    if False:` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_fold_invalid_record_governs_over_grok` |
| G8 | `g8-fold-reads-the-first-record-only` | `scripts/h_mad_tdd_judge.py` | `    grok = next((i for i, r in enumerate(records, 1) if r.fallback == "grok"), 0)  # M:F2` | `    grok = 1 if records[0].fallback == "grok" else 0  # M:F2` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_second_active_record_holding_grok_blocks` |
| G9 | `g9-fallback-position-unchecked` | `hooks/h-mad-tdd-gate.sh` | `  [ "$FALLBACK_POS" -le "$RECORDS" ] \|\| _refuse judge-error "state fallback position out of range"  # M:F4` | `  :  # M:F4` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_state_stub_fallback_position_out_of_range_is_judge_error` |
| G10 | `g10-fallback-field-optional` | `hooks/h-mad-tdd-gate.sh` | ` fallback=(none\|(grok\|invalid):([1-9][0-9]*))(` | `( fallback=(none\|(grok\|invalid):([1-9][0-9]*)))?(` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_state_stub_fallback_field_is_judge_error` |
| G11 | `g11-grok-fold-tag-unchecked` | `hooks/h-mad-tdd-gate.sh` | `    grok:*)    [ "$FB_TAG" = grok ] ;;` | `    grok:*)    true ;;` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_state_stub_grok_fold_naming_a_non_grok_record_is_judge_error` |
| G12 | `g12-invalid-fold-tag-unchecked` | `hooks/h-mad-tdd-gate.sh` | `    invalid:*) [ "${FB_TAG#invalid:}" != "$FB_TAG" ] ;;` | `    invalid:*) true ;;` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_state_stub_invalid_fold_naming_a_valid_record_is_judge_error` |

(`\|` in the table is a literal `|` in the source.) G1 and G2 overlap (G2's `find` is the second
line of G1's); the harness applies one row at a time. G1, G2 and G3 are AC-2.7's three mutations,
each killed by `test_gate_matrix`: G3 feeds every record the tag of the file's first record, which
is `other` in Task 12's harness, so a `feat` holding `"grok"` falls through (executed on the scratch
copy: rc 0, empty stdout; and `other` holding `"grok"` beside a `feat` with no key blocks). G3 is
also W9's force-fire. G5 and G6 are v1.3's G5 (`"null"` collapses) and G4 (`//`, falsy reads as
absent) moved to the judge's `_fallback_tag`, which is committed code Task 12 does not edit; v1.3's
G6 (`*)` arm) has no successor, because the arm has none (Task 12, test 11). G7–G10 are new:
the fold's precedence and order, and the gate's two grammar checks. G9's mutant hands the
`fallback-grok` refusal an empty governing record, so the killing test reads kind `fallback-grok`,
not `judge-error`; G10's makes the field optional, so the `missing-field` stub line is accepted and
the stub judge allows. G11 and G12 are grok design v1.3's rows, one per arm of the tag agreement
check, each with its own test: each mutant makes its arm always true, so a disagreeing fold reaches
the refusal of its own kind (executed for v1.5 on the scratch copy: G11's mutant failed exactly
test 17's two items and G12's exactly test 18's two). Every `find` above counts 1 in the scratch
copy of Task 12's code (executed for v1.5, all twelve G rows and WR12-1, WR12-2; G7's
`    if invalid:` and G1's, G2's and G4's included). G1's and G4's two-line finds still count 1 beside
the agreement `case`, because there each arm label is followed on its own line by a test, never by
a newline.

**`grok_exec.json`** — file `scripts/hmad-dispatch.sh`; `command`
`["python3.11","-m","pytest","tests/test_hmad_dispatch_grok_readers.py","tests/test_hmad_dispatch_exec_grok.py","tests/test_hmad_dispatch_progress_grok.py","tests/test_hmad_dispatch_exec.py","tests/test_hmad_dispatch_audit_cycle.py","-q"]`;
`target_command` `["python3.11","-m","pytest","-q"]`.

| Row | name | find | replace | test |
|---|---|---|---|---|
| P1 | `p1-usage-not-a-closer` | `or $e.type == "usage" or $e.type == "end")` | `or $e.type == "end")` | `tests/test_hmad_dispatch_grok_readers.py::test_grok_final_message_per_closer` |
| P2 | `p2-tool-call-not-a-closer` | `elif ($e.type == "tool_call" or $e.type == "tool_call_update"` | `elif ($e.type == "tool_call_update"` | `tests/test_hmad_dispatch_grok_readers.py::test_grok_final_message_per_closer` |
| P3 | `p3-tool-call-update-not-a-closer` | `elif ($e.type == "tool_call" or $e.type == "tool_call_update"` | `elif ($e.type == "tool_call"` | `tests/test_hmad_dispatch_grok_readers.py::test_grok_final_message_per_closer` |
| P4 | `p4-thought-appended` | `if $e.type == "text" then .cur +=` | `if ($e.type == "text" or $e.type == "thought") then .cur +=` | `tests/test_hmad_dispatch_grok_readers.py::test_grok_final_message_ignores_thought_decoy` |
| P5 | `p5-region-unscoped` | `tail -n "+$(( pre + 1 ))"` | `tail -n +1` | `tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_reads_only_its_own_region` |
| P6 | `p6-always-complete` | `as $_ ("truncated"; "complete")` | `as $_ ("complete"; "complete")` | `tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_truncated_recovers_the_verdict` |
| P7 | `p7-last-tool-guard-dropped` | `\| if .seen \| not then empty` | `\| if false then empty` | `tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_omits_the_last_tool_line_without_tool_calls` |
| P8 | `p8-counts-seen-not-completed` | ` and $e.status == "completed"` | (empty string) | `tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_counts_completed_not_seen_ids` |
| P9 | `p9-jq-failure-reads-truncated` | `    *) echo jqfail ;;` | `    *) echo truncated ;;` | `tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_with_failing_jq_is_not_parsed` |
| L1 | `l1-banner-step-skipped` | `elif _codex_banner_in_head "$log"` | `elif false` | `tests/test_hmad_dispatch_progress_grok.py::test_progress_banner_then_f0_is_codex_text` |
| L2 | `l2-fallback-first-key-only` | `\{.*\"type\"` | `\{[[:space:]]*\"type\"` | `tests/test_hmad_dispatch_progress_grok.py::test_progress_key_order_line_on_the_fallback_route` |
| L3 | `l3-depth-bound-65` | `_GROK_MAX_DEPTH=64` | `_GROK_MAX_DEPTH=65` | `tests/test_hmad_dispatch_progress_grok.py::test_progress_depth_boundary` |
| L4 | `l4-depth-filter-dropped` | `\| select(_grok_over(0) \| not)` | (empty string) | `tests/test_hmad_dispatch_progress_grok.py::test_progress_depth_boundary` |
| L5 | `l5-banner-window-8192` | `head -c 4096` | `head -c 8192` | `tests/test_hmad_dispatch_progress_grok.py::test_window_edge_log_is_grok_ndjson` |
| W1 | `w1-grok-arm-for-every-agent` | `  if [ "$agent" = grok ]; then⏎    # grok: prompt by file, streaming-json appended to $log (FR-3). No OVERSIZE check here:` | `  if true; then⏎    # grok: prompt by file, streaming-json appended to $log (FR-3). No OVERSIZE check here:` | `tests/test_hmad_dispatch_exec.py::test_codex_exec_runs_headless_with_the_right_flags` |
| W2 | `w2-scrub-reaches-codex` | `"$wait_secs" codex "${args[@]}"` | `"$wait_secs" env "${child_env[@]}" codex "${args[@]}"` | `tests/test_hmad_dispatch_exec_grok.py::test_exec_codex_and_agy_keep_claude_env` |
| W3a | `w3a-segmenter-for-agy` | `resp="$(_agy_ndjson_response` | `resp="$(_grok_final_message` | `tests/test_hmad_dispatch_exec.py::test_agy_exec_stdout_is_the_response` |
| W5 | `w5-grok-checked-before-agy` | `  if grep -aqE '^[[:space:]]*\{[[:space:]]*"event"` | `  _grok_log_has_events "$log" && { printf 'grok-ndjson'; return 0; }⏎  if grep -aqE '^[[:space:]]*\{[[:space:]]*"event"` | `tests/test_hmad_dispatch_progress_grok.py::test_progress_agy_init_plus_f0_is_agy_ndjson` |
| W8 | `w8-every-pass-is-grok` | `_cmd_exec "${agent[$i]}"` | `_cmd_exec grok` | `tests/test_hmad_dispatch_audit_cycle.py::test_verb_two_distinct_dispatches` |

L2's `find` and `replace` carry the backslash before each quote because the fallback is a
double-quoted bash string (design V21: `\{.*\"type\"` counts 1, `\{.*"type"` counts 0). W3b is row
P5 and W4 is row P7. W1's informational second node is
`tests/test_hmad_dispatch_exec.py::test_agy_exec_runs_print_headless_prompt_as_last_arg`.

**`review_evidence_grok.json`** — file `scripts/h_mad_review_evidence.py`; `command`
`["python3.11","-m","pytest","tests/test_h_mad_review_evidence_scan_grok.py","tests/test_h_mad_review_evidence_grok.py","-q"]`;
`target_command` `["python3.11","-m","pytest","-q"]`.

| Row | name | find | replace | test |
|---|---|---|---|---|
| E1 | `e1-ok-by-substring` | `        if t == "tool_call_update" and event.get("status") == "completed" and isinstance(call_id, str):` | `        if "completed" in line:` | `tests/test_h_mad_review_evidence_scan_grok.py::test_scan_grok_ok_ignores_a_completed_substring_in_text` |
| E2 | `e2-truncated-publishes-counts` | `                print("EVIDENCE: UNREADABLE reason=truncated_no_end")⏎                return 2` | `                print(f"EVIDENCE: NONE tools={grok['tools']} ok={grok['ok']} format=grok")⏎                return 2` | `tests/test_h_mad_review_evidence_grok.py::test_cli_f_trunc_is_unreadable_without_counts` |
| E3 | `e3-banner-not-consulted` | `grok = None if codex_banner_in_head(text) else scan_grok(text)` | `grok = scan_grok(text)` | `tests/test_h_mad_review_evidence_grok.py::test_cli_banner_then_f0_keeps_codex_output` |
| E4 | `e4-membership-before-type-check` | `isinstance(t, str) and t in _GROK_TYPES` | `t in _GROK_TYPES` | `tests/test_h_mad_review_evidence_scan_grok.py::test_scan_grok_survives_malformed_type_lines` |
| E5 | `e5-banner-window-8192` | `CODEX_BANNER_HEAD = 4096` | `CODEX_BANNER_HEAD = 8192` | `tests/test_h_mad_review_evidence_scan_grok.py::test_codex_banner_in_head_window_edge` |
| E6 | `e6-depth-bound-65` | `GROK_MAX_DEPTH = 64` | `GROK_MAX_DEPTH = 65` | `tests/test_h_mad_review_evidence_scan_grok.py::test_scan_grok_depth_boundary` |
| E7 | `e7-recursion-error-uncaught` | `except (ValueError, RecursionError):` | `except ValueError:` | `tests/test_h_mad_review_evidence_scan_grok.py::test_scan_grok_survives_malformed_type_lines` |
| E8 | `e8-depth-skip-dropped` | `if _json_deeper_than(event, GROK_MAX_DEPTH):` | `if False:` | `tests/test_h_mad_review_evidence_scan_grok.py::test_scan_grok_depth_boundary` |
| E9 | `e9-scan-recursion-error-uncaught` | `        except (ValueError, TypeError, RecursionError):` | `        except (ValueError, TypeError):` | `tests/test_h_mad_review_evidence_scan_grok.py::test_scan_survives_a_200k_deep_line` |
| E10 | `e10-scan-event-membership-unguarded` | `        if isinstance(event_name, str) and event_name in _AGY_EVENTS:` | `        if event_name in _AGY_EVENTS:` | `tests/test_h_mad_review_evidence_scan_grok.py::test_scan_survives_an_unhashable_event_value` |
| W6 | `w6-grok-before-agy-in-cli` | `if counts["agy_events"] == 0:` | `if counts["agy_events"] == 0 or scan_grok(text) is not None:` | `tests/test_h_mad_review_evidence_grok.py::test_cli_mixed_agy_f0_equals_agy_alone` |

**`audit_cycle_grok.json`** — file `scripts/h_mad_audit_cycle.py`; `command`
`["python3.11","-m","pytest","tests/test_h_mad_audit_cycle_grok.py","-q"]`; `target_command`
`["python3.11","-m","pytest","-q"]`.

| Row | name | find | replace | test |
|---|---|---|---|---|
| A1 | `a1-grok-truncated-render-dropped` | `        if effort.get("shape") == "grok-truncated":` | `        if False:` | `tests/test_h_mad_audit_cycle_grok.py::test_effort_items_render_grok_and_grok_truncated` |
| A2 | `a2-grok-truncated-route-dropped` | `        if shape == "grok-truncated":` | `        if False:` | `tests/test_h_mad_audit_cycle_grok.py::test_combine_f_trunc_is_unmeasurable` |
| A3 | `a3-grok-before-banner` | `    elif _CODEX_BANNER.search(text[:4096]):` | `    elif _CODEX_BANNER.search(text[:4096]) and scan_grok(text) is None:` | `tests/test_h_mad_audit_cycle_grok.py::test_measure_effort_banner_then_f0_is_codex_text` |
| W7a | `w7a-grok-before-agy-in-effort` | `    if counts.get("agy_events", 0) > 0:` | `    if counts.get("agy_events", 0) > 0 and scan_grok(text) is None:` | `tests/test_h_mad_audit_cycle_grok.py::test_measure_effort_mixed_agy_f0_is_parsed` |

W7b is row A2.

**`assemble_tdd_agent.json`** — file `scripts/h_mad_assemble_tdd.py`; `command`
`["python3.11","-m","pytest","tests/test_h_mad_assemble_tdd_agent.py","tests/test_h_mad_assemble_tdd.py","-q"]`;
`target_command` `["python3.11","-m","pytest","-q"]`.

| Row | name | find | replace | test |
|---|---|---|---|---|
| T1 | `t1-timeout-judged-by-value` | `args.timeout is not None` | `args.timeout not in (None, 900)` | `tests/test_h_mad_assemble_tdd_agent.py::test_agent_grok_explicit_timeout_wins` |
| W10a | `w10a-grok-by-default` | `ap.add_argument("--agent", choices=("codex", "grok"), default="codex")` | `ap.add_argument("--agent", choices=("codex", "grok"), default="grok")` | `tests/test_h_mad_assemble_tdd.py::TestCli::test_a_clean_assembly_prints_pass_and_the_command_block` |

W10b ("agent read from state") has no row: it would need a state reader the assembler does not
contain, and AC-8.5 (`test_state_fallback_agent_is_not_read`) covers it (design residual).

**`resolved_model_grok.json`** — file `scripts/h_mad_resolved_model.py`; `command`
`["python3.11","-m","pytest","tests/test_h_mad_resolved_model_grok.py","tests/test_h_mad_resolved_model.py","-q"]`;
`target_command` `["python3.11","-m","pytest","-q"]`.

| Row | name | find | replace | test |
|---|---|---|---|---|
| R1 | `r1-first-of-several-models` | `    if len(keys) != 1:` | `    if not keys:` | `tests/test_h_mad_resolved_model_grok.py::test_grok_refusals_exit_2_unknown` |
| R2 | `r2-first-end-not-last` | `            last_end = event` | `            last_end = last_end or event` | `tests/test_h_mad_resolved_model_grok.py::test_grok_second_dispatch_model_wins` |
| W11 | `w11-grok-reader-for-every-agent` | `    if a.agent == "grok":` | `    if True:` | `tests/test_h_mad_resolved_model.py::test_codex_reads_the_resolved_model_out_of_its_session_header` |

W11's informational second node is
`tests/test_h_mad_resolved_model.py::test_agreement_between_the_two_newest_is_answerable`.

**`grok_wire_reverts.json`** — the wire-scoped removal direction of every WIRE (§"Deviations from
design v1.2", item 2): each row removes the caller's connection only, with the callee intact, and
its `test` key is that WIRE's WIRE-PIN, so the harness scores the pin itself failing. The rows span
six files, so its table names each row's `file` in a column; `command`
`["python3.11","-m","pytest","tests/test_h_mad_assemble_tdd_agent.py","tests/test_h_mad_resolved_model_grok.py","tests/test_h_mad_review_evidence_grok.py","tests/test_h_mad_audit_cycle_grok.py","tests/test_hmad_dispatch_exec_grok.py","tests/test_hmad_dispatch_progress_grok.py","tests/test_hmad_dispatch_audit_cycle_grok.py","tests/test_h_mad_tdd_gate_fallback_agent.py","-q"]`;
`target_command` `["python3.11","-m","pytest","-q"]`.

| Row | name | file | find | replace | test |
|---|---|---|---|---|---|
| WR3 | `wr3-assembler-drops-agent` | `scripts/h_mad_assemble_tdd.py` | `        agent=args.agent,` | (empty string) | `tests/test_h_mad_assemble_tdd_agent.py::test_agent_grok_block_names_exec_grok_with_1500` |
| WR4 | `wr4-resolver-grok-branch-deleted` | `scripts/h_mad_resolved_model.py` | `    if a.agent == "grok":⏎        grok_from_log(a.log)⏎        return 0` | (empty string) | `tests/test_h_mad_resolved_model_grok.py::test_grok_reads_the_model_from_the_last_end` |
| WR6 | `wr6-cli-never-calls-scan-grok` | `scripts/h_mad_review_evidence.py` | `grok = None if codex_banner_in_head(text) else scan_grok(text)` | `grok = None` | `tests/test_h_mad_review_evidence_grok.py::test_cli_f0_prints_grok_evidence_pass` |
| WR7-1 | `wr7-1-effort-never-calls-scan-grok` | `scripts/h_mad_audit_cycle.py` | `        grok = scan_grok(text)` | `        grok = None` | `tests/test_h_mad_audit_cycle_grok.py::test_measure_effort_reads_f0_as_grok` |
| WR7-2 | `wr7-2-grok-truncated-route-deleted` | `scripts/h_mad_audit_cycle.py` | `        if shape == "grok-truncated":⏎            return "UNVERIFIED", f"low_evidence_unmeasurable:p{result.index}"` | (empty string) | `tests/test_h_mad_audit_cycle_grok.py::test_combine_routes_hand_built_grok_truncated_to_unmeasurable` |
| WR9-1 | `wr9-1-grok-arm-never-entered` | `scripts/hmad-dispatch.sh` | `  if [ "$agent" = grok ]; then⏎    # grok: prompt by file, streaming-json appended to $log (FR-3). No OVERSIZE check here:` | `  if false; then⏎    # grok: prompt by file, streaming-json appended to $log (FR-3). No OVERSIZE check here:` | `tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_argv_carries_prompt_file_and_headless_flags` |
| WR9-2 | `wr9-2-child-env-scrub-dropped` | `scripts/hmad-dispatch.sh` | `"$wait_secs" env "${child_env[@]}" grok "${gargs[@]}"` | `"$wait_secs" grok "${gargs[@]}"` | `tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_child_env_has_no_claude_names` |
| WR9-3 | `wr9-3-final-message-never-read` | `scripts/hmad-dispatch.sh` | `grok_final="$(_grok_final_message "$log" "$pre_lines")"` | `grok_final=""` | `tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_f0_prints_the_final_message` |
| WR9-4 | `wr9-4-last-tool-never-read` | `scripts/hmad-dispatch.sh` | `grok_last="$(_grok_last_tool "$log" "$pre_lines")"` | `grok_last=""` | `tests/test_hmad_dispatch_exec_grok.py::test_exec_grok_empty_path_names_the_last_tool` |
| WR10-1 | `wr10-1-format-never-grok` | `scripts/hmad-dispatch.sh` | `  elif _grok_log_has_events "$log"; then` | `  elif false; then` | `tests/test_hmad_dispatch_progress_grok.py::test_progress_f0_is_grok_ndjson` |
| WR10-2 | `wr10-2-grok-render-arm-skipped` | `scripts/hmad-dispatch.sh` | `elif [ "$fmt" = grok-ndjson ]; then` | `elif false; then` | `tests/test_hmad_dispatch_progress_grok.py::test_progress_f0_renders_counts_without_delta_text` |
| WR11 | `wr11-surfaces-refuse-grok` | `scripts/hmad-dispatch.sh` | `case "$_s" in agy\|codex\|grok) ;;` | `case "$_s" in agy\|codex) ;;` | `tests/test_hmad_dispatch_audit_cycle_grok.py::test_audit_cycle_dispatches_the_grok_pass_through_exec_grok` |
| WR12-1 | `wr12-1-state-line-never-folds` | `scripts/h_mad_tdd_judge.py` | ` fallback={_fallback_fold(chain.records)}")  # M:F0` | ` fallback=none")  # M:F0` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_format_state_line_emits_the_fallback_fold` |
| WR12-2 | `wr12-2-gate-never-reads-the-fold` | `hooks/h-mad-tdd-gate.sh` | `  FALLBACK=${BASH_REMATCH[4]}  # M:F3` | `  FALLBACK=none  # M:F3` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_block_grok_reads_the_active_features_fallback_agent` |

WR9-1 shares W1's `find` with a different `replace` (`if false` removes the arm; W1's `if true`
force-fires it). WR7-2 removes what A2 disables, but is scored on WIRE-PIN 2 rather than on A2's
test. No row's `replace` contains its own `find`. Every row names exactly one WIRE-PIN: 14 rows for
the 14 WIRE entries of Tasks 3 (1), 4 (1), 6 (1), 7 (2), 9 (4), 10 (2), 11 (1) and 12 (2). v1.3's
WR12 (`(.orchestrator_state[$k] // {}) as $r`) anchored text the merged gate deleted; WR12-1 and
WR12-2 replace it (Task 12, "Wire-scoped reverts").

**Row count**: 12 + 19 + 11 + 4 + 2 + 3 + 14 = 65 (unit: mutation rows; the seven tables above,
in order). By owning task: Task 12 14, Task 8 11, Task 9 7, Task 10 6, Task 11 2, Task 5 8, Task 6 4,
Task 7 6, Task 3 3, Task 4 4 — sum 65. Grok design v1.3's rows are 40 named rows (G1–G12, P1–P9,
L1–L5, E1–E8, A1–A3, T1, R1–R2) plus 9 force-fires that are not aliases of a named row (W1, W2, W3a,
W5, W6, W7a, W8, W10a, W11) = 49; W3b = P5, W4 = P7, W7b = A2, W9 = G3, and W10b has no row. G1–G12
are the design's rows by mechanism, with this plan's literals. This plan adds E9, E10 and the 14
wire reverts WR3–WR11 plus WR12-1 and WR12-2: 49 + 2 + 14 = 65 (§"Deviations from design v1.2",
item 3).

**Expected RED split**: not applicable — no test is authored. The verdict is seven `ANCHORS: ANCHORS_OK` and
seven `MUTATION: ALL_CAUGHT` tokens for the new specs, the same two tokens for each of the six
committed specs re-run above, and the committed sweep test green in the full suite with 114 specs
(107 at HEAD `6277d703` + 7).

**Acceptance Criteria**:
- [ ] AC-2.7: `tdd_gate_fallback_agent.json` is committed with G1–G3, and each is killed by an
      AC-2.1 cell (`test_gate_matrix`).
- [ ] Every row lands exactly once (`ANCHORS_OK`) and every row is caught (`ALL_CAUGHT`).
- [ ] W1–W11 each have a force-fire row or a named alias row, except W10b (stated residual).
- [ ] Every WIRE's removal direction is executed and scored: the 14 `grok_wire_reverts.json` rows are
      each caught by the named WIRE-PIN (`MUTATION: ALL_CAUGHT` on that spec).
- [ ] The six committed specs with a row on `hooks/h-mad-tdd-gate.sh` or
      `scripts/h_mad_tdd_judge.py` read `ANCHORS_OK` and `MUTATION: ALL_CAUGHT` after Task 12.

**Dependencies on other tasks**: Task 3, Task 4, Task 5, Task 6, Task 7, Task 8, Task 9, Task 10,
Task 11, Task 12

---

## Task 15: grok-fallback-docs

**Production file**: `h-mad/SKILL.md`, `h-mad/references/state-schema.md`,
`h-mad/references/agent-substrate.md`
**Test file**: `h-mad/tests/test_grok_fallback_docs.py`
**Task shape**: `new-behaviour`

**Description**: FR-10 / design D11, D12, written against the shipped behaviour of Tasks 3, 9, 11
and 12. Headings verified present at `507214d` (`grep -n` on `h-mad/SKILL.md`):
`### Codex authors Phase 5 — enforced, not just instructed`,
``### Exit-code dispatch for 5d/5e (`hmad-dispatch exec`) — default for one-shot``,
`## Teammate audit leg — when codex is unavailable`, `## Never gate on one audit pass`;
`h-mad/references/agent-substrate.md` has `## Verbs`. The frontmatter of `SKILL.md` is untouched.
Re-read for v1.4 at HEAD `d9574614`: all five headings present once (`SKILL.md` lines 487, 520, 1864,
2826; `agent-substrate.md` line 22), and `grep -c grok` still reads 0 in each of the three documents.

- **Phase-5 section:** the FR-2 table with `fallback_agent`, written in the merged gate's terms
  (Task 12): the refusals are kinds `fallback-grok` and `fallback-invalid` in the gate's chosen
  refusal form, never "exit 1"; the fold is over every `step5` record on the target's chain (any
  invalid value blocks, else any `grok`), not over one `ACTIVE` feature; OQ1
  (`HMAD_CODEX_UNAVAILABLE` does not override `fallback_agent=grok`); `no write-time test-first
  gate` (codex writes pass `h-mad/hooks/h-mad-codex-tdd-gate.py`, grok writes pass nothing). v1.3's
  "inherited no-`jq` fail-open" is dropped: the merged gate runs no `jq` and a missing `jq` no
  longer stands it down (merged spec AC-6.12), so there is nothing to document.
- **Exec section:** `exec grok` and `--agent grok` with its 1500 s default, and the D4 statement.
- **Teammate section:** grok as the preferred independent stand-in, dispatched with
  `--surfaces agy,grok`; the D4 statement (grok's GREEN, mutation, wiring and audit precision are
  `unmeasured`); the one-codex-round-owed rule; the D11 legs-change outcome (a switch from
  `doc-auditor` to `grok` resets the exit streak once, `legs_changed:`); the unchanged path when
  `fallback_agent` is absent or `claude`.
- **Never-gate section:** a cross-reference to the teammate routing naming `--surfaces agy,grok`.
- **`state-schema.md`:** `fallback_agent` and its sibling `codex_status` (plan P6).
- **`agent-substrate.md` §"Verbs":** `exec grok` with its argv, the child-only `CLAUDE*` scrub and
  `HPW_AGENT_BACKEND`, the inherited `GROK_SANDBOX`, `--always-approve` as a grant wider than codex's
  `workspace-write`, and grok tree-delta as reported, not trusted.

**Tests** (7 collected items; sections located with `docsections.titled_section(text, heading)`,
which asserts on a missing heading and never skips):
1. `test_phase5_section_documents_fallback_agent` — `fallback_agent`, `HMAD_CODEX_UNAVAILABLE`,
   `no write-time test-first gate`, `fallback-grok` (AC-10.1; the last needle, added in v1.4, ties
   the text to the merged gate's refusal kind).
2. `test_exec_section_documents_exec_grok` — `exec grok`, `--agent grok` (AC-10.1).
3. `test_teammate_section_documents_the_grok_leg` — `--surfaces agy,grok`, `unmeasured` (AC-10.1).
4. `test_never_gate_section_cross_references_the_grok_leg` — `--surfaces agy,grok` (design D12).
5. `test_state_schema_doc_names_fallback_agent` (AC-10.2).
6. `test_agent_substrate_documents_exec_grok_and_grok_sandbox` — `exec grok`, `GROK_SANDBOX` (AC-10.2).
7. `test_missing_heading_fails_not_skips` — a scratch copy of `SKILL.md` with the teammate heading
   removed makes `titled_section` raise `AssertionError` (plan Success Criteria).

**Expected RED split**: 6 failing, 1 passing. **Regression guards**:
`test_missing_heading_fails_not_skips` (docsections already asserts). At `507214d`,
`grep -c grok` reads 0 in each of the three documents, and the only `HMAD_CODEX_UNAVAILABLE` in the
Phase-5 section cannot pass test 1 alone.

**Acceptance Criteria**:
- [ ] AC-10.1: each heading located by exact text; the needles present; a missing heading fails.
- [ ] AC-10.2: `state-schema.md` names `fallback_agent`; `agent-substrate.md` names `exec grok` and
      `GROK_SANDBOX`.

**Mutation rows**: none.

**Dependencies on other tasks**: Task 3, Task 9, Task 11, Task 12

---

## Task 16: coupled-suite-and-regression-floor

**Production file**: none (read and verdict only)
**Test file**: none (runs `h-mad/tests`, `handoff/tests` and `handoff/scripts` in full)
**Task shape**: `gate`

**Description**: The pre-merge regression gate (FR-11, plan Success Criteria). Run from the worktree
root:

```bash
set -o pipefail
BASE_SHA="$(python3 -c 'import sys; sys.path.insert(0, "h-mad/tests"); import grokfixtures; print(grokfixtures.BASE_SHA)')" \
  || { echo "FAIL: cannot read grokfixtures.BASE_SHA"; exit 1; }
printf '%s' "$BASE_SHA" | grep -qE '^[0-9a-f]{40}$' || { echo "FAIL: BASE_SHA is not 40-hex: $BASE_SHA"; exit 1; }
PERMITTED='h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches'
R="$(mktemp -d)" || { echo "FAIL: mktemp"; exit 1; }
T="$(mktemp -d)" || { echo "FAIL: mktemp"; exit 1; }
echo "records: $R"
# 1. the full coupled suite, judged on pytest's rc AND its FAILED/ERROR lines
/opt/anaconda3/bin/python -m pytest -q -rfE -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts > "$R/suite.txt" 2>&1
suite_rc=$?
tail -n 1 "$R/suite.txt"
[ "$suite_rc" -eq 0 ] || [ "$suite_rc" -eq 1 ] \
  || { echo "FAIL: the suite exited $suite_rc (collection error, interrupt, internal or usage error)"; exit 1; }
if grep -q '^ERROR ' "$R/suite.txt"; then echo "FAIL: the suite reported errors"; grep '^ERROR ' "$R/suite.txt"; exit 1; fi
sed -n 's/^FAILED \([^ ]*\).*/\1/p' "$R/suite.txt" > "$R/failed.txt" || { echo "FAIL: cannot read the FAILED lines"; exit 1; }
if [ "$suite_rc" -eq 0 ]; then
  [ ! -s "$R/failed.txt" ] || { echo "FAIL: the suite exited 0 with FAILED lines"; exit 1; }
else
  [ "$(cat "$R/failed.txt")" = "$PERMITTED" ] \
    || { echo "FAIL: the suite failed beyond the one permitted node:"; cat "$R/failed.txt"; exit 1; }
fi
suite_last="$(tail -n 1 "$R/suite.txt")" || { echo "FAIL: cannot read the suite summary"; exit 1; }
case "$suite_last" in *" passed"*) ;; *) echo "FAIL: the suite summary has no passed count: $suite_last"; exit 1 ;; esac
# 2. the base collect runs on the WHOLE tree at BASE_SHA (a collection may read docs/)
git archive "$BASE_SHA" | tar -x -C "$T" || { echo "FAIL: git archive $BASE_SHA | tar"; exit 1; }
(cd "$T" && /opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts) > "$R/base.raw" 2>&1 \
  || { echo "FAIL: the base collect exited non-zero"; tail -n 5 "$R/base.raw"; exit 1; }
/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts > "$R/head.raw" 2>&1 \
  || { echo "FAIL: the head collect exited non-zero"; tail -n 5 "$R/head.raw"; exit 1; }
for s in base head; do
  last="$(tail -n 1 "$R/$s.raw")" || { echo "FAIL: cannot read the $s collect summary"; exit 1; }
  case "$last" in *[Ee]rror*) echo "FAIL: the $s collect summary names an error: $last"; exit 1 ;; esac
  case "$last" in *" collected"*) ;; *) echo "FAIL: the $s collect summary is not 'N tests collected': $last"; exit 1 ;; esac
  grep '::' "$R/$s.raw" | LC_ALL=C sort > "$R/$s.txt" || { echo "FAIL: the $s collect listed no node ids"; exit 1; }
done
LC_ALL=C comm -23 "$R/base.txt" "$R/head.txt" > "$R/gone.txt" || { echo "FAIL: comm"; exit 1; }
[ ! -s "$R/gone.txt" ] || { echo "FAIL: node ids collected at BASE_SHA are gone"; cat "$R/gone.txt"; exit 1; }
# 3. every file tracked at BASE_SHA under the three test paths, plus pytest.ini, is unmodified
git ls-tree -r --name-only "$BASE_SHA" -- h-mad/tests handoff/tests handoff/scripts pytest.ini > "$R/pre.txt" \
  || { echo "FAIL: git ls-tree $BASE_SHA"; exit 1; }
grep -qxF pytest.ini "$R/pre.txt" || { echo "FAIL: pytest.ini is not tracked at BASE_SHA"; exit 1; }
while IFS= read -r f; do
  case "$f" in
    h-mad/tests/stubs/codex|h-mad/tests/stubs/agy|h-mad/tests/test_h_mad_tdd_judge.py|h-mad/tests/test_h_mad_tdd_gate_judge.py|h-mad/tests/mutation-specs/claude_gate_judge_wiring.json)
      echo "--- permitted edit (Task 1 stub or Task 12 migration): $f"
      git --no-pager diff "$BASE_SHA" -- "$f" || { echo "FAIL: git diff $f"; exit 1; }
      git show "$BASE_SHA:$f" > "$R/base.blob" || { echo "FAIL: git show $BASE_SHA:$f"; exit 1; }
      python3 - "$f" "$R/base.blob" <<'PY' || { echo "FAIL: $f differs from BASE_SHA beyond its stated change"; exit 1; }
import sys
f, base = sys.argv[1], sys.argv[2]
CAPTURE = rb'''if [ -n "${HMAD_STUB_CLAUDE_ENV_CAPTURE:-}" ]; then
  for _n in $(compgen -e); do case "$_n" in CLAUDE*) printf '%s\n' "$_n" ;; esac; done \
    | LC_ALL=C sort > "$HMAD_STUB_CLAUDE_ENV_CAPTURE"
fi

'''
STATED = {
    "h-mad/tests/stubs/codex": (CAPTURE, 1),
    "h-mad/tests/stubs/agy": (CAPTURE, 1),
    "h-mad/tests/test_h_mad_tdd_judge.py": (b" fallback=(none|(grok|invalid):([1-9][0-9]*))", 1),
    "h-mad/tests/test_h_mad_tdd_gate_judge.py": (b" fallback=none", 1),
    "h-mad/tests/mutation-specs/claude_gate_judge_wiring.json": (b" fallback=none", 3),
}
needle, n = STATED[f]
with open(f, "rb") as h:
    head = h.read()
with open(base, "rb") as h:
    old = h.read()
ok = needle not in old and head.count(needle) == n and head.replace(needle, b"") == old
print(f"  stated change: {f} count={head.count(needle)}/{n} rest_equals_base={head.replace(needle, b'') == old}")
sys.exit(0 if ok else 1)
PY
      ;;
    *)
      git diff --quiet --exit-code "$BASE_SHA" -- "$f" \
        || { echo "FAIL: a file tracked at BASE_SHA under the test paths differs: $f"; exit 1; } ;;
  esac
done < "$R/pre.txt"
# 3b. the second base constant (feature-created, so outside pre.txt) names the same commit
ab="$(sed -n 's/^BASE_SHA = "\([0-9a-f]*\)"$/\1/p' h-mad/tests/test_h_mad_assemble_tdd_agent.py)" \
  || { echo "FAIL: cannot read test_h_mad_assemble_tdd_agent.BASE_SHA"; exit 1; }
[ "${#ab}" -ge 7 ] && [ "${BASE_SHA#"$ab"}" != "$BASE_SHA" ] \
  || { echo "FAIL: test_h_mad_assemble_tdd_agent.BASE_SHA ($ab) is not a prefix of grokfixtures.BASE_SHA"; exit 1; }
# 4. the D8 census
[ "$(grep -c 'codex|agy|grok\|agy|codex|grok' h-mad/scripts/hmad-dispatch.sh)" -eq 6 ] \
  || { echo "FAIL: the agy|codex|grok census is not 6 matching lines (design D8)"; exit 1; }
# 5. the content-classifier sweep, compared with its expected population
grep -rln 'from h_mad_review_evidence import\|agy_events\|_exec_log_format\|OpenAI Codex' \
  h-mad/scripts h-mad/hooks h-mad/bin > "$R/sweep.raw" || { echo "FAIL: the class sweep matched nothing"; exit 1; }
grep -v __pycache__ "$R/sweep.raw" | LC_ALL=C sort > "$R/sweep.txt" || { echo "FAIL: the class sweep is empty"; exit 1; }
printf '%s\n' h-mad/scripts/h_mad_archreview_cycle.py h-mad/scripts/h_mad_audit_cycle.py \
  h-mad/scripts/h_mad_review_evidence.py h-mad/scripts/hmad-dispatch.sh > "$R/sweep.expected"
diff "$R/sweep.expected" "$R/sweep.txt" \
  || { echo "FAIL: the class sweep is not its 4 expected files; a new file is a new content classifier whose FR-5 precedence must be decided and recorded before this gate re-runs"; exit 1; }
echo "FLOOR: PASS files=$(wc -l < "$R/pre.txt" | tr -d ' ') suite_rc=$suite_rc"
rm -rf "$T" "$R"
```

`BASE_SHA` is the constant in `h-mad/tests/grokfixtures.py`, which Task 12 re-pins to the rebased
fork point `8ef6009f9491796d5d16b96a54e3b3185a8a6f19` (Preamble). Run before that re-pin, this script
would fail step 3 on four files the `codex-tdd-gate-defects` merge changed under the test paths
(`test_h_mad_audit_suite_gate.py`, `test_h_mad_codex_runtime.py`, `test_h_mad_tdd_gate_codex.py`,
`test_h_mad_tdd_gate_state_resolution.py`; `git diff --stat 5a9cd8ed 8ef6009f`), none of them a
grok edit. The script runs as one script, under
`bash` or as one Bash-tool call (zsh here). `set -e` is not relied on, because it is inert in the Bash
tool's top-level shell: every command whose failure matters carries its own
`|| { echo "FAIL: …"; exit 1; }` or `if …; then …; exit 1; fi`, and `set -o pipefail` makes each
guarded pipeline (`git archive | tar`, `grep '::' | sort`, `grep -v | sort`) fail when any stage
fails, not only its last. A pytest run is never piped: each writes to a file under `$R` and its rc is
read directly. The verdict is the last line `FLOOR: PASS files=N suite_rc=R`, read as a token, never
`$?`, and it **certifies the suite**: it is reached only when the suite exited 0, or exited 1 with the
Preamble's one environment-dependent node as its only `FAILED` line and no `ERROR` line; any other rc
(2 for a collection error or interrupt, 3, 4, 5) halts first. A failed step leaves `$R` behind (its
path is printed first, on the line that begins `records:`) for the record; the pass path removes `$T` and `$R`.

**The base tree** (delta review of v1.1, must-fix; orchestrator decision 1, repair (a)). The base
collect runs on the whole tree at `BASE_SHA` (`git archive "$BASE_SHA" | tar -x -C "$T"`), because a
collection may read outside `h-mad/` and `handoff/`:
`h-mad/tests/test_h_mad_audit_cycle.py::test_premise_items_match_gate_count_real_artifacts` is
parametrized over `REAL_AUDIT_REPORTS`, globbed from `docs/`, and on the v1.1 archive (`h-mad handoff`
only) it collected as `[NOTSET]`, so v1.1's floor failed on every run. The delta reviewer executed
repair (a) at `HEAD`: `comm -23` and `comm -13` both empty. The base and head collect summaries are
each asserted to read `N tests collected` with no `error`, so a base import failure cannot quietly
shrink the floor. Read at `01121ca7` in the main checkout: the head collect exits 0 with
`3893 tests collected in 3.50s`.

**The unmodified gate** (codex cycle-1 must-fix 3, orchestrator decision 4; widened by the v1.1
delta review, should-fix 1). Every file tracked at `BASE_SHA` under the three test paths, plus the
root `pytest.ini`, is diffed against `BASE_SHA` with `git diff --quiet --exit-code "$BASE_SHA" --
<file>`, so an added skip decorator, an edited fixture, stub, helper module (`claudebinary.py:74`
calls `pytest.skip`), mutation spec or `pytest.ini`, and a deleted file all fail it. At `507214d`
that is 255 files (`git ls-tree -r --name-only 507214d -- h-mad/tests handoff/tests handoff/scripts
pytest.ini | wc -l`; unit: files): 124 `test_*.py` / `conftest.py`, 130 other tracked files under
the three paths, and `pytest.ini`. At the re-pinned `8ef6009f` the same command reads 270 files
(read for v1.4; re-read at `6277d703`, 270). Five are a named allowlist, spec v1.5 AC-11.1's
carve-out, and each is held to its **stated change only** (v1.5; answers the v1.4 delta review's
second should-fix): the arm prints the file's diff into the record, then requires that the stated
text is absent at `BASE_SHA`, occurs exactly N times at HEAD, and that deleting it from the HEAD
bytes gives the `BASE_SHA` bytes exactly. The five, with the measured size of each change
(`git diff --numstat`, unit: added and deleted lines):
- `h-mad/tests/stubs/codex` and `h-mad/tests/stubs/agy` (Task 1): the 5-line
  `HMAD_STUB_CLAUDE_ENV_CAPTURE` block including its trailing blank line, once each; `5 0` each at
  `6277d703`. They are the only two tracked files under the three paths that differ from
  `8ef6009f` at `6277d703` (`git diff --name-status 8ef6009f HEAD` filtered to non-added files);
- `h-mad/tests/test_h_mad_tdd_judge.py` (migration 1): ` fallback=(none|(grok|invalid):([1-9][0-9]*))`
  once; `1 1`;
- `h-mad/tests/test_h_mad_tdd_gate_judge.py` (migration 2): ` fallback=none` once; `1 1`;
- `h-mad/tests/mutation-specs/claude_gate_judge_wiring.json` (migration 3): ` fallback=none` three
  times, one per `replace` of `W5BF`, `W5BF2` and `W5BF3`; `3 3`.

A weakened assertion, an added line, a missing or partial migration, or any edit elsewhere in one
of the five fails the arm. **Step 3b** covers the one test file this feature re-pinned that the
loop cannot see: `h-mad/tests/test_h_mad_assemble_tdd_agent.py` is not tracked at `BASE_SHA` (Task 3
created it), so its `BASE_SHA` re-pin (`f2ff9261`, Preamble) is not an AC-11.1 carve-out; 3b
requires its 8-hex `BASE_SHA` to be a prefix of `grokfixtures.BASE_SHA`, so the two constants
cannot drift apart. No other task edits a file tracked at `BASE_SHA` under the three paths (every
other task's production and test files are new or live outside them). The node-id floor (`comm -23` empty) stays
as a second, independent check. **Residual:** a skip decided by the environment inside an unchanged
file (for example `claudebinary.py`'s probe of the Claude binary) changes no byte and no node id, so
neither check sees it; the suite's summary line is printed for the record.

**The class sweep** (codex cycle-2 should-fix). The content-classifier sweep is compared with its
expected population, the 4 files it reads at `01121ca7` (`h_mad_archreview_cycle.py`,
`h_mad_audit_cycle.py`, `h_mad_review_evidence.py`, `hmad-dispatch.sh`, all under `h-mad/scripts/`;
the same 4 as the design's reading at `0b3f969`). No task adds a sweep string to a new file under
`h-mad/scripts`, `h-mad/hooks` or `h-mad/bin`, so the expected set after Tasks 1–15 is the same 4. An
added file is a new content classifier: the gate halts until its FR-5 precedence is decided and
recorded and the expected list is extended in this plan. A removed file halts too.
The `_cmd_exec` agent-conditional census is re-measured with the design's D3 `awk` command, because
S4 and S8 moved it by construction; its reading is recorded, not compared.

**Guards proven by forced failure** (codex cycle-2 must-fix 1, orchestrator decision 2). Executed for
this revision, no file kept: the script above, byte-identical, ran in a scratch git repository that
mirrors the paths it names (a `pytest.ini`, a test under each of the three paths, a `docs/`-globbing
parametrized test, the `PERMITTED` node as an environment-switched failure, `stubs/codex` and
`stubs/agy`, a fixture, a 6-line census file and the 4 sweep files), once per scenario, under `bash`
and again under `zsh`, with the same result each time. Clean → `FLOOR: PASS files=9 suite_rc=0`;
permitted node failing alone → `FLOOR: PASS files=9 suite_rc=1`; `stubs/codex` edited →
`FLOOR: PASS` with its diff printed. Each forced failure stopped on its own first line: an extra
failing test, alone or beside the permitted one → `FAIL: the suite failed beyond the one permitted
node:`; a head collection error → `FAIL: the suite exited 2 (collection error, interrupt, internal or
usage error)`; a base collection error →
`FAIL: the base collect exited non-zero`; a `docs/` file removed → `FAIL: node ids collected at
BASE_SHA are gone`; a fixture edited, `pytest.ini` edited, a skip decorator added → `FAIL: a file
tracked at BASE_SHA under the test paths differs: <file>`; a new file carrying `agy_events` under
`h-mad/hooks` → the class-sweep line `FAIL: the class sweep is not its 4 expected files`, with its
FR-5 instruction; a census line deleted →
`FAIL: the agy|codex|grok census is not 6 matching lines (design D8)`; `BASE_SHA = "deadbeef"` →
`FAIL: BASE_SHA is not 40-hex: deadbeef`. Control, same repository: v1.1's script printed `FAIL: node
ids collected at BASE_SHA are gone` on the clean scenario (its `h-mad handoff` archive has no `docs/`),
and v1.1's script with only its archive widened printed `FLOOR: PASS` on the extra-failing-test
scenario and on the head-collection-error scenario, which is codex's finding reproduced.
**The narrowed arm and step 3b, executed for v1.5** (closing v1.4's residual that the Task 12 arm
was never run). Steps 3 and 3b, extracted byte for byte from the script above with the prelude,
ran in a scratch `git clone --shared` of the worktree at `6277d703` (deleted) with
`grokfixtures.BASE_SHA` re-pinned, once per scenario under `bash` and again under `zsh`, with the
same result each time. Migrations 1–3 applied → `PASS` (every arm printed `count=N/N
rest_equals_base=True`). Each forced failure stopped on its own line: migrations not applied →
`FAIL: h-mad/tests/mutation-specs/claude_gate_judge_wiring.json differs from BASE_SHA beyond its
stated change` (`count=0/3`); two of the three `W5BF` rows migrated → the same line (`count=2/3`);
one line appended to the migrated `test_h_mad_tdd_gate_judge.py` → its own line
(`rest_equals_base=False`); an assertion weakened in the migrated `test_h_mad_tdd_judge.py` → its
own line; a line appended to `stubs/codex` → its own line; `conftest.py` edited → `FAIL: a file
tracked at BASE_SHA under the test paths differs: h-mad/tests/conftest.py`;
`test_h_mad_assemble_tdd_agent.BASE_SHA` put back to `507214d` → `FAIL:
test_h_mad_assemble_tdd_agent.BASE_SHA (507214d) is not a prefix of grokfixtures.BASE_SHA`.

**Expected RED split**: not applicable — no test is authored.

**Acceptance Criteria**:
- [ ] AC-11.1: the full suite passes with every pre-existing test file unmodified (the one
      environment-dependent node named in the Preamble excepted, for its recorded reason), except
      spec v1.5 AC-11.1's five carve-out files, each changed by exactly its stated change (step 3's
      narrowed arm).
- [ ] AC-11.2: `test_hmad_dispatch_exec.py`, `test_hmad_dispatch_exec_completion.py`,
      `test_hmad_dispatch_exec_stamp.py`, `test_hmad_dispatch_progress.py` pass in that full run.
- [ ] AC-5.3, AC-6.5, AC-7.5, AC-9.4: the named pre-existing files pass unchanged in that run.
- [ ] Every file tracked at `BASE_SHA` under `h-mad/tests`, `handoff/tests`, `handoff/scripts`, and
      `pytest.ini`, is byte-identical to `BASE_SHA` (`git diff --quiet --exit-code` per file), except
      the five allowlisted files (two Task 1 stubs, three Task 12 migrations), whose diff is in the
      record and whose bytes equal `BASE_SHA`'s once their stated change is removed; step 3b's two
      base constants agree; the node-id floor (`comm -23` empty,
      whole-tree base collect, both collect summaries free of `error`) holds as a second check; the
      census reads 6 matching lines; the class sweep equals its 4 expected files.
- [ ] The script's last line is `FLOOR: PASS files=N suite_rc=R`, which certifies the suite verdict
      above (rc 0, or rc 1 with the permitted node as the only `FAILED` line).

**Mutation rows**: none.

**Dependencies on other tasks**: Task 13, Task 14, Task 15

---

## Task 17: exec-grok-live-smoke

**Production file**: none (runs the worktree's wrapper against the real grok CLI once)
**Test file**: none (not a test and not a D4 measurement; plan v1.3 §"Convention Prerequisites")
**Task shape**: `operational`

**Description**: The one live plumbing smoke of `exec grok`, run by the orchestrator after FR-3 and
FR-4 are GREEN (Tasks 8–10) and the suite gate (Task 16) passes, before merge. It runs the
**worktree's** wrapper by absolute path: bare `hmad-dispatch` resolves through
`~/.claude/skills/h-mad/bin/hmad-dispatch` to the main tree, whose `_cmd_exec` refuses `grok` until
merge. About $0.04 at F0's measured `total_cost_usd=0.0393`. Re-checked for v1.4 against the merged
gate: the smoke touches no gate surface. Its writes are grok's own, inside `$S`, which no Claude
PreToolUse hook sees; every `exit 1` below is the smoke script's own guard, not the gate's protocol;
and no step runs `h_mad_derive_test_path.sh`.

```bash
W="$(git -C /Users/kimhawk/orca/skills worktree list --porcelain \
  | awk '/^worktree /{p=substr($0, 10)} /^branch refs\/heads\/feature\/216-grok-codex-fallback$/{print p}')"
[ -n "$W" ] || { echo "FAIL: feature worktree not found"; exit 1; }
WR="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$W")" || { echo "FAIL: realpath of $W"; exit 1; }
D="$W/h-mad/bin/hmad-dispatch"
DR="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$D")" || { echo "FAIL: realpath of $D"; exit 1; }
case "$DR" in "$WR"/*) echo "wrapper realpath: $DR" ;; *) echo "FAIL: wrapper realpath $DR is outside the worktree $WR"; exit 1 ;; esac
S="$(mktemp -d)" || { echo "FAIL: mktemp"; exit 1; }
printf 'alpha\n' > "$S/a.txt" || { echo "FAIL: cannot write $S/a.txt"; exit 1; }
"$D" exec grok "$W/docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.prompt.txt" \
  --cd "$S" --effort low --timeout 300 --out "$S/smoke.out" --log "$S/smoke.log"
rc=$?; echo "rc=$rc"
[ "$rc" -eq 0 ] || { echo "FAIL: exec grok exited $rc"; exit 1; }
grep -q '^STATUS: DONE' "$S/smoke.out" || { echo "FAIL: --out has no line-start STATUS: DONE"; exit 1; }
[ -f "$S/b.txt" ] || { echo "FAIL: b.txt was not created in $S"; exit 1; }
[ "$(cat "$S/b.txt")" = probe ] || { echo "FAIL: b.txt holds '$(cat "$S/b.txt")', not probe"; exit 1; }
P="$("$D" progress "$S/smoke.log")" || { echo "FAIL: progress exited $?"; exit 1; }
printf '%s\n' "$P" | grep -q 'format: grok-ndjson ' || { echo "FAIL: progress does not name grok-ndjson"; exit 1; }
M="$("$D" resolved-model grok --log "$S/smoke.log")" || { echo "FAIL: resolved-model exited $?"; exit 1; }
[ "$(printf '%s\n' "$M" | grep -c '^RESOLVED-MODEL agent=grok model=')" -eq 1 ] \
  || { echo "FAIL: resolved-model did not print exactly one RESOLVED-MODEL agent=grok line"; exit 1; }
E="$(python3 "$W/h-mad/scripts/h_mad_review_evidence.py" "$S/smoke.log")" || { echo "FAIL: evidence CLI exited $?"; exit 1; }
printf '%s\n' "$E" | grep -q '^EVIDENCE: PASS .*format=grok' || { echo "FAIL: evidence CLI printed: $E"; exit 1; }
X="$(python3 -c 'import json, sys; sys.path.insert(0, sys.argv[1]); from pathlib import Path; from h_mad_audit_cycle import measure_effort; r = measure_effort(Path(sys.argv[2])); print(json.dumps(r, sort_keys=True)); sys.exit(0 if isinstance(r, dict) and r.get("shape") == "grok" else 1)' "$W/h-mad/scripts" "$S/smoke.log")" \
  || { echo "FAIL: measure_effort shape is not grok: $X"; exit 1; }
printf '%s\n' "--- out" "$(cat "$S/smoke.out")" "--- progress" "$P" "--- resolved-model" "$M" "--- evidence" "$E" "--- measure_effort" "$X"
echo "SMOKE: PASS"
```

- **Pass:** the script's last line is `SMOKE: PASS`, read as a token, never `$?`. It is reached only
  if every condition held, each asserted in order with its own `|| { echo "FAIL: …"; exit 1; }`
  guard (`set -e` is not relied on: it is inert in the Bash tool's top-level shell): the wrapper's
  realpath lies inside the worktree's realpath; rc 0; `--out` holds a line-start `STATUS: DONE`;
  `b.txt` exists in `$S` and its content, trailing newline stripped (`$(cat …)`), is `probe`;
  `progress` names `grok-ndjson`; `resolved-model` prints exactly one `RESOLVED-MODEL agent=grok`
  line; the evidence CLI prints `EVIDENCE: PASS` with `format=grok`; `measure_effort()` returns shape
  `grok`. A `STATUS: DONE` reply without the file is not a pass: the `b.txt` guards halt first. Any
  `FAIL:` line is the result, and the steps after it do not run.
- **Record:** the wrapper realpath, the command, rc, the `--out` content, the `b.txt` content, and
  the four readers' outputs go into the Phase-5 report and
  `docs/03-analysis/probes/grok-codex-fallback/exec-grok-smoke.md`. On `SMOKE: PASS`, `$S` is removed
  after the record is written. On any `FAIL:` line `$S` is kept (its `smoke.out`, `smoke.log` and
  `b.txt` are the evidence) and its path goes into the record.
- The worktree lookup takes the whole remainder of the porcelain `worktree ` line
  (`substr($0, 10)`), so a worktree path containing a space is not truncated (executed on a
  hand-built porcelain sample whose path is `/a b/c`: printed `/a b/c`).
- **Any other result halts.** A live envelope that disagrees with F0 fixes the parsers against the
  observed envelope, and the repair is not complete until all of the following hold, in order, each
  read on its own token (codex cycle-2 must-fix 3, orchestrator decision 4):
  1. The repair lands through the owning task's TDD cycle: a failing test built from the observed
     envelope first, then the parser change.
  2. Task 16's script re-runs in full, unchanged, from the worktree root (the whole coupled suite
     `h-mad/tests handoff/tests handoff/scripts`, the node-id floor, the unmodified gate, the census
     and the class sweep) and its last line is `FLOOR: PASS`.
  3. Every Task 14 spec whose rows name a repaired file re-runs, together with
     `grok_wire_reverts.json` whenever a repaired file carries one of its rows:
     `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors <spec>` reads `ANCHORS_OK` and
     `python3 h-mad/scripts/h_mad_mutation_harness.py <spec>` reads `MUTATION: ALL_CAUGHT`. The map
     from file to spec: `scripts/hmad-dispatch.sh` → `grok_exec.json` and `grok_wire_reverts.json`;
     `scripts/h_mad_review_evidence.py` → `review_evidence_grok.json` and `grok_wire_reverts.json`;
     `scripts/h_mad_audit_cycle.py` → `audit_cycle_grok.json` and `grok_wire_reverts.json`;
     `scripts/h_mad_resolved_model.py` → `resolved_model_grok.json` and `grok_wire_reverts.json`.
  4. Only then does the smoke re-run, from the top, to `SMOKE: PASS`. **If the smoke cannot run** (no key, no quota, no `grok` on
  PATH, a refusal of `--effort low`), Phase 5 halts and asks the operator; a skipped smoke never
  passes, and merge does not proceed on "not run".
- **Residual (plan):** `--model` and `--sandbox` meet only the stub and `grok --help`, never the live
  CLI. D3.4's `< /dev/null` and D3.3's `env` prefix are the two mechanisms this smoke exercises that
  no stub can falsify.

**Expected RED split**: not applicable — no test is authored.

**Acceptance Criteria**:
- [ ] Every pass condition above holds, with the record complete.
- [ ] After any live-envelope repair: Task 16's `FLOOR: PASS` and each affected spec's `ANCHORS_OK` and
      `MUTATION: ALL_CAUGHT` are re-read on the repaired tree before the smoke's `SMOKE: PASS` is.

**Mutation rows**: none.

**Dependencies on other tasks**: Task 16

---

## AC coverage

Every one of the spec's 58 distinct AC ids is owned by a task (`grep -oE '^  - AC-[0-9]+\.[0-9]+[a-z]?'
docs/01-plan/features/grok-codex-fallback.spec.md | sort -u | wc -l` → 58 at `507214d`; unit: distinct
ids). The implementation gate counts against these 58, never against plan v1.3's 55 (design
§"Supersedes the plan on", item 2).

| FR | ACs (count) | Task |
|---|---|---|
| FR-1 | AC-1.1, 1.2, 1.3, 1.4 (4) | Task 2 |
| FR-2 | AC-2.1, 2.1b, 2.2, 2.3, 2.4, 2.5, 2.6 (7); AC-2.7 (1) | Task 12; AC-2.7 Task 14 |
| FR-3 | AC-3.1–3.7 (7) | Task 9 |
| FR-4 | AC-4.1–4.10 (10) | Task 9 |
| FR-5 | AC-5.1, 5.2, 5.2b (3); AC-5.3 (1) | Task 10 (5.2b also Tasks 5, 13); AC-5.3 Task 16 |
| FR-6 | AC-6.1, 6.2, 6.3, 6.6 (4); AC-6.4, 6.5 (2) | Task 6; Task 5 (6.5 also Task 16) |
| FR-7 | AC-7.1 (1); AC-7.2, 7.3, 7.4 (3); AC-7.5 (1) | Task 11; Task 7; Task 16 |
| FR-8 | AC-8.1–8.5 (5) | Task 3 |
| FR-9 | AC-9.1, 9.2, 9.3 (3); AC-9.4 (1) | Task 4; Task 16 |
| FR-10 | AC-10.1, 10.2 (2) | Task 15 |
| FR-11 | AC-11.1, 11.2 (2); AC-11.3 (1) | Task 16; Tasks 6, 7, 10, 13 |

Sum: 4 + 8 + 7 + 10 + 4 + 6 + 5 + 5 + 4 + 2 + 3 = 58.

**Test census** (unit: collected test items introduced by this plan): Task 1 12, Task 2 8, Task 3 11,
Task 4 9, Task 5 17, Task 6 7, Task 7 19, Task 8 21, Task 9 30, Task 10 15, Task 11 2, Task 12 192,
Task 13 23, Task 15 7 — total 373, of which 187 fail at RED and 186 are regression guards or
first-run passes (the per-task splits sum to these: failing 10+4+9+9+16+4+10+21+23+10+2+63+0+6,
passing 2+4+2+0+1+3+9+0+7+5+0+129+23+1). Not in the census: the 25 committed items Task 12's
migrations turn RED (deviation 5), which are pre-existing, not introduced.

**Task graph**: Tasks 1 and 2 are independent (`Dependencies on other tasks: None`). After Task 1,
Tasks 3, 4, 5, 8 and 12 can run in parallel (they touch distinct files); Tasks 6 and 7 follow
Task 5; Task 9 follows Task 8; Task 10 follows Task 9, and Task 11 follows Task 10 (Tasks 8, 9, 10
and 11 all edit `h-mad/scripts/hmad-dispatch.sh`, so they run one after another, never in
parallel); Task 13 follows 4, 6, 7 and 10; Task 15 follows 3, 9, 11 and 12; Task 14 follows 3–12;
Task 16 follows 13, 14 and 15; Task 17 is last. At v1.4, Tasks 1–11 and 13 are done, so the
remaining order is Task 12, then Tasks 14 and 15, then 16, then 17. Wiring tasks: 3, 4, 6, 7, 9, 10,
11, 12 (8 tasks carrying W1–W11 as 14 WIRE entries: W1–W4 Task 9 (4), W5 Task 10 (2), W6 Task 6
(1), W7 Task 7 (2), W8 Task 11 (1), W9 Task 12 (2: the judge fold and the gate read), W10 Task 3
(1), W11 Task 4 (1)).

## Version History
- v1.0: Initial implementation plan draft (2026-09-28), authored at 507214d from spec v1.4, design v1.2 and plan v1.3 (no audit cycle yet). 17 tasks, 8 wiring (W1-W11), 43 mutation rows in six specs, 354 new test items, live exec grok smoke last.
- v1.1: Impl-plan audit cycle 1 answered (2026-09-28; codex p1 4 musts + 1 should, doc-auditor teammate 1 must + 2 shoulds + nits, audit commit 5b294a8), re-verified at 76b2501 (h-mad unchanged since 507214d). scan() catches RecursionError (Deviations section: class rule over every --log JSON parse, members scan/CLI/measure_effort/archreview _evidence_counts, new tests Task 5 11-12 and Task 7 12, row E9); Task 16 depends on Task 13; all 13 wire-scoped removals executed and scored as grok_wire_reverts.json rows WR3-WR12 keyed on their WIRE-PINs; Task 16 diffs each of the 124 pre-existing test files against BASE_SHA with git diff --exit-code plus the node-id floor; Task 17 smoke and Task 16 floor are guarded scripts ending in SMOKE: PASS / FLOOR: PASS; Task 10 renderer landed as _GROK_RENDER_PROG with its algorithm, executed on F0; suite paths include handoff/scripts; Task 2 pre-creates the state file and pops the key; Tasks 10 and 11 sequential. 17 tasks, 8 wiring, 57 mutation rows in seven specs, 357 new test items.
- v1.2: Impl-plan audit cycle 2 answered (2026-09-28; codex p2 3 musts + 1 should, v1.1 delta review 1 must + 5 shoulds + 6 nits), corrective and not re-audited, verified at 01121ca7 (h-mad unchanged since 507214d). Task 16 floor: base collect on the whole tree at BASE_SHA, every step guarded (pipefail, suite rc plus FAILED/ERROR lines, collect summaries free of error), unmodified gate widened to all 255 tracked files under the test paths plus pytest.ini with the two Task 1 stubs allowlisted, class sweep compared with its 4 expected files, every guard proven by forced failure under bash and zsh; scan() agy_events membership type-guarded (Deviation 4, Task 5 test 13, row E10); Task 17 re-runs Task 16 and the affected specs after any live-envelope repair; Task 7 test 12 states both assertions; Convention 1 jq-shim rule names four members; Deviations override the design for 5d/5e; nits applied. 17 tasks, 8 wiring, 58 mutation rows in seven specs, 358 new test items.
- v1.3: 5c baseline: branch feature/216-grok-codex-fallback in worktree /Users/kimhawk/orca/skills-grok-codex-fallback; 13 wires registered in .h-mad/wires.jsonl. No content change.
- v1.4: Rebase re-plan (2026-09-29), answering no audit cycle: the branch was rebased onto main 8ef6009f (merge of codex-tdd-gate-defects), and that feature's design D13 and impl-plan "After Phase 5" owe this re-plan. Verified at HEAD d9574614 (Tasks 1-11 and 13 done; gate and judge byte-identical to 8ef6009f). Changes: (1) Task 12 re-planned onto the merged judge gate (Deviation 5): _fallback_fold in h_mad_tdd_judge.py, a fallback=(none|grok:B|invalid:B) field after records= on the TDD-STATE active line (spelling chosen here, owed to the design), the gate ERE and a B<=records cross-check in _read_state, _refuse fallback-grok / fallback-invalid after the codex-authorship refusal; two WIREs (judge fold, gate read); 186 tests, RED 61/125; migration edits to test_h_mad_tdd_judge.py ACTIVE_RE, test_h_mad_tdd_gate_judge.py _tree_b default, claude_gate_judge_wiring.json W5BF/W5BF2/W5BF3 replace texts, and grokfixtures.BASE_SHA re-pinned to 8ef6009f; all executed on a deleted scratch copy (25 committed items RED without the migrations, 255 of 255 gate/judge items green with them, ANCHORS_OK). (2) Task 14: tdd_gate_fallback_agent.json re-derived as G1-G10 across the gate and judge, WR12 replaced by WR12-1 and WR12-2, six committed gate/judge specs re-run; every one of the 63 finds counts 1 on the scratch copy. (3) Task 7 code block, WR7-2 note and test 11 (re.purge plus reload) match commits 39a86df9/9975729f; Task 9 S3 and S8 comments and the _clean_caller_env fixture match 10137f3b/b3e6cb70. (4) Task 15 drops the no-jq fail-open and names the fallback-grok kind; Task 16 re-pins BASE_SHA and allowlists Task 12's three migrations (270 tracked files at 8ef6009f); Task 17 re-checked, no gate dependence; the Preamble's name-map bullet now states the tree-relative judge; Convention 1 has three jq-shim members; Convention 5 re-read ANCHORS_OK specs=107 mutations=1005. Counts: 17 tasks, 8 wiring, 14 WIREs, 63 mutation rows in seven specs (114 committed after Task 14), 367 new test items (185 RED, 182 pass).
- v1.5: Answers the impl-plan v1.4 delta review (`grok-codex-fallback.impl-plan.delta-review.v1.4.md`, advisory: 0 must, 5 should, 6 nit) and aligns with grok design v1.3 (`6277d703`) and spec v1.5 (`02283561`) (2026-09-29), verified at HEAD `6277d703` (gate and judge byte-identical to `8ef6009f`). Task 12 gains design v1.3 §D2's tag agreement check (`# M:F1`, `judge-error` when the fold's kind disagrees with its governing record's tag), tests 17–19 and rows G11/G12, executed per arm on a deleted scratch copy; it records migration 5 (`test_h_mad_assemble_tdd_agent.BASE_SHA` re-pinned to `8ef6009f` by `f2ff9261`, done) and plans the wire registry move (wire-pin gate with `--feature`, then a `renamed` tombstone of the v1.3 `Task 12` record), executed on a scratch registry. Task 14 carries G1–G12. Task 16's allowlist holds each of the five carve-out files to its stated change (count at HEAD plus exact base bytes once removed), and a new step 3b checks that the two base constants agree; both executed under bash and zsh on a scratch clone. ACs cite spec v1.5 (AC-2.2 `git archive`, AC-2.5 three cases, AC-11.1 carve-out); merged §D13 and grok design §D13 are qualified everywhere; Convention 6 re-counted; the drift residual sits beside migration 1. Counts: 17 tasks, 8 wiring, 14 WIREs, 65 mutation rows in seven specs (114 committed after Task 14), 373 new test items (187 RED, 186 pass).
- v1.5.1: Orchestrator erratum at Task 12 RED (2026-09-29). The split read 63 failing / 129 passing, counting both items of test 18 as guards; test 18's `grok` item also asserts the stderr text `disagrees with its record's tag grok`, which the RED gate cannot print (it refuses `judge-error` with `state verb printed no well-formed state line`). Codex's RED, re-run by the orchestrator under both locales: 64 failed, 128 passed; the migrated files 25 failed, 168 passed. Split corrected to 64 / 128; the guard list now names test 18's `claude` item only. No test, row or other count changes.
