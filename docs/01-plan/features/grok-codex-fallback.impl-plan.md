# Implementation Plan: grok-codex-fallback

> Source: docs/02-design/features/grok-codex-fallback.design.md (v1.2, binding, including its
> §"Supersedes the plan on"), docs/01-plan/features/grok-codex-fallback.spec.md (v1.4, 58 ACs,
> binding), docs/01-plan/features/grok-codex-fallback.plan.md (v1.3: wiring table W1–W11 and the
> Phase-5 live smoke stay binding)
> Branch target: feature/216-grok-codex-fallback

## Executive Summary

Seventeen tasks, each counted once: two leaf tasks with no dependency (Task 1 builds the in-skill
F0 copy, the fixture builder and the stubs; Task 2 adds the schema property); two `new-behaviour`
leaves (Task 5, `scan_grok` plus the `scan()` RecursionError catch; Task 8, the shell stream
readers); eight `wiring` tasks that connect each surface to its new callee (Tasks 3, 4, 6, 7, 9, 10,
11, 12, carrying W1–W11 of plan v1.3); one cross-surface agreement task (13); one task that authors
and runs the 57 mutation rows in seven specs (14); the documentation (15); the full coupled-suite
gate (16); and last the live `exec grok` smoke through the worktree's own wrapper (17).
2 + 2 + 8 + 1 + 1 + 1 + 1 + 1 = 17.

## Deviations from design v1.2

The design is binding except where the orchestrator ruled otherwise on an audit finding. Each
deviation below is recorded with its evidence, so the design can be amended to match.

1. **`scan()` is no longer untouched** (design line 877 "`scan()` is untouched"; impl-plan audit
   cycle 1, teammate must-fix; orchestrator decision 1, repair (a)). `scan()`'s
   `json.loads(line)` at `h-mad/scripts/h_mad_review_evidence.py:130` catches only
   `except (ValueError, TypeError):` (`h-mad/scripts/h_mad_review_evidence.py:131`), so a 200,000-deep line raises `RecursionError`. The
   teammate executed this on Python 3.14.7, 3.11.8 and `/opt/anaconda3/bin/python`: the CLI exits 1
   with frames `:251 → main :201 → scan :130`, and `measure_effort()` raises the same error. So
   design Test Plan row "the CLI prints F0's EVIDENCE line on the malformed fixture" (line 1731)
   could not go GREEN with `scan()` untouched. Re-executed for this revision at `76b2501` (`h-mad/`
   byte-identical to `507214d`) with `/opt/anaconda3/bin/python`, no file written:
   `h_mad_review_evidence.scan(depth_line(200_000))` → `RecursionError`, and
   `h_mad_archreview_cycle._evidence_counts(...)` on the same line → `RecursionError`; the tuple
   `(ValueError, TypeError, RecursionError)` catches it. **Repair:** Task 5 changes `h_mad_review_evidence.py:131` to
   `        except (ValueError, TypeError, RecursionError):`. **Class rule:** every Python JSON
   parse reachable from a `--log` catches `RecursionError`. Members, from
   `grep -n 'json.loads' h-mad/scripts/*.py` (28 matching lines in 17 files, read at `76b2501`)
   crossed with `grep -ln -- '--log' h-mad/scripts/*.py` (5 files: `h_mad_archreview_cycle.py`,
   `h_mad_assemble_tdd.py`, `h_mad_audit_cycle.py`, `h_mad_resolved_model.py`,
   `h_mad_review_evidence.py`); 2 files are in both (`h_mad_archreview_cycle.py`,
   `h_mad_review_evidence.py`), and `h_mad_audit_cycle.py` parses its log only through `scan()`:
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
   - The other 26 `json.loads` lines are in the 15 files that take no `--log` argument, so no
     `--log` reaches them; that zero follows from the argument surface, which is load-bearing: a
     new `--log` consumer joins the class and needs the catch.
   **Anchors:** line 131 is in no committed anchor. The committed `h_mad_review_evidence.py` finds
   (audit_effort, codex_transcript_evidence and review_evidence_format specs) contain no `except`, and
   the new line does not contain E7's find `except (ValueError, RecursionError):` as a substring, so
   E7 still matches once. New mutation row E9 (Task 14).
2. **Wire-scoped removals are mutation rows** (orchestrator decision 3, answering codex must-fix 2).
   The design states each wire's removal direction in prose only. This plan scores all 13 of them
   (one per WIRE across the eight wiring tasks) as rows of a seventh spec,
   `grok_wire_reverts.json`, each with the callee intact and the task's WIRE-PIN as its `test` key.
3. **Mutation total 57, not the design's 43.** 43 design rows + E9 (deviation 1) + 13 wire-revert
   rows (deviation 2) = 57, in seven specs, not six. Committed spec count after Task 14: 106.

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
  AC-8.1 and Task 16's node-id floor compare against it.
- **Both coupled suites, per task.** Every task's GREEN verification runs, from the worktree root,
  `/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts`
  in full, never the scoped file alone. The three paths are named explicitly: they are the root
  `pytest.ini`'s `testpaths`, whose comment records that the two-path form silently dropped the
  tests in `handoff/scripts/` (5 `test_*.py` files there at `76b2501`, two of which reference
  `hmad-dispatch`), and Task 16's base collect runs from a `git archive` that has no `pytest.ini`. The one environment-dependent failure recorded in the plan baseline,
  `h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches`,
  is the only failure a task may leave, and only for its recorded reason.
- **Codex authors 5d/5e.** If codex is out during this feature's own Phase 5, the fallback is
  today's `codex_status=exhausted` path: this feature's `fallback_agent` does not exist on the live
  skill until merge.
- **The main-tree derive script.** The hook resolves
  `$HOME/.claude/skills/h-mad/scripts/h_mad_derive_test_path.sh`, which is the main tree even when
  the worktree's hook is under test (design V11). This feature does not edit that script.
- **Dispatched agent CLIs are not script dependencies** (`h-mad/invariants.base.md`, amended at
  `0b3f969`). No test in this plan runs a real `grok`; every grok dispatch in the suite goes through
  `h-mad/tests/stubs/grok`. Task 17 runs the real CLI once, by hand, and is not a test.

### Conventions every task follows

1. **Harness helpers.** Wrapper tests import `run`, `run_fn`, `_bindir` and `WRAPPER` from
   `test_hmad_dispatch` (all four are module-level there: `WRAPPER` at line 13, `run` 166, `run_fn`
   181, `_bindir` 193), in the same `from test_hmad_dispatch import …` form that
   `test_hmad_dispatch_exec.py` uses for its own four names (`SKILL_MD_TEXT, _bindir, _git_repo,
   run`). `_bindir(tmp_path, names)` symlinks `stubs/<name>` for each name and the real `jq` as
   `bin/jq`, and `run()` puts the bindir first on PATH, then `/usr/bin:/bin`. A test that needs a
   `jq` shim "in the test's bindir" (Task 8 test 7, Task 9 test 22, Task 10 test 9) first unlinks
   `bin/jq` (present whenever `shutil.which("jq")` finds one) and writes the shim at that same path: `/usr/bin/jq` exists on this host, so a shim placed
   anywhere else on PATH is either shadowed by the real `jq` link or shadows the wrong entry.
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
   skipped=0 unclassifiable=0`.
   The committed sweep test
   `h-mad/tests/test_h_mad_mutation_harness.py::test_committed_mutation_harness_anchor_sweep_is_ok`
   runs in every task's full-suite run and enforces this.
6. **Mutation spec form.** `root` is `"../.."` (the `h-mad/` directory, as in
   `exec_last_step.json`), `file` keys are `scripts/…` / `hooks/…`, `test` keys are
   `tests/<file>.py::<name>`, `command` and `target_command` lead with `python3.11` (house form, 98
   of 99 specs at `50560eb`). Score on the `MUTATION:` token, never `$?`.
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
`_json_deeper_than`, `scan_grok`, `CODEX_BANNER_HEAD` and `codex_banner_in_head`. One line of
`scan()` changes (§"Deviations from design v1.2", item 1): `h-mad/scripts/h_mad_review_evidence.py:131`
`        except (ValueError, TypeError):` becomes
`        except (ValueError, TypeError, RecursionError):`, and nothing else in `scan()` moves.
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
- Landed literals (Task 14 rows E1, E4–E9), each exactly once in the file:
  `        if t == "tool_call_update" and event.get("status") == "completed" and isinstance(call_id, str):`,
  `isinstance(t, str) and t in _GROK_TYPES`, `CODEX_BANNER_HEAD = 4096`, `GROK_MAX_DEPTH = 64`,
  `except (ValueError, RecursionError):`, `if _json_deeper_than(event, GROK_MAX_DEPTH):`, and
  `        except (ValueError, TypeError, RecursionError):` (E9; it does not contain E7's `find` as a
  substring, so E7 still matches once).

**Tests** (16 collected items; `import h_mad_review_evidence as ev`, symbols read inside tests):
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

**Expected RED split**: 15 failing, 1 passing. Tests 11 and 12 fail at RED on the `pytest.fail`
(today's `scan()` raises `RecursionError`). **Regression guards**: `test_scan_unchanged_on_f0`.

**Acceptance Criteria**:
- [ ] AC-6.4: `ok` comes from parsed events, never from a substring.
- [ ] AC-6.5: `scan()` on F0 is unchanged (`agy_events == 0`, `tools == 0`); the existing
      `test_h_mad_review_evidence.py` passes unchanged (Task 16).
- [ ] AC-5.2b (Python half): key order is irrelevant; a bogus type is not grok; depth 64 is an event
      and depth 65 is not.
- [ ] Deviation 1 (class rule): `scan()` and `_evidence_counts` survive a 200,000-deep line
      (`test_scan_survives_a_200k_deep_line`,
      `test_archreview_evidence_counts_survive_a_200k_deep_line`).

**Mutation rows** (Task 14, `review_evidence_grok.json`): E1, E4, E5, E6, E7, E8, E9 — 7 rows.

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

**Code structure**:
```python
# measure_effort(), after `counts = scan(text)`; the `if` and `elif` lines are byte-identical:
    if counts.get("agy_events", 0) > 0:
        counts["shape"] = "parsed"
    elif _CODEX_BANNER.search(text[:4096]):
        counts["shape"] = "codex-text"          # (existing comment block kept)
    else:
        grok = scan_grok(text)
        if grok is not None and grok["complete"]:
            return {"readable": True, "shape": "grok", "agy_events": 0,
                    "tools": grok["tools"], "ok": grok["ok"], "unresolved": grok["unresolved"],
                    "thinking": grok["thinking"], "stop_reason": grok["stop_reason"]}
        if grok is not None:
            return {"readable": True, "shape": "grok-truncated", "agy_events": 0}
        counts["shape"] = "unparseable"         # (existing comment block kept)
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
already exists once at `h-mad/scripts/h_mad_audit_cycle.py:879`; the pair is unique because its
first line is).

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
11. `test_codex_banner_pattern_is_single_sourced` — `ac._CODEX_BANNER is ev._CODEX_HEADER_RE`.
12. `test_measure_effort_survives_a_200k_deep_line` — `measure_effort` on a file holding
    `deep_line_200k() + f0_text()` equals `measure_effort` on F0 (shape `grok`), with the call wrapped
    in the same `try` / `except RecursionError` / `pytest.fail` form as Task 5 test 11, with the
    message `"measure_effort() raised RecursionError on a 200,000-deep line"` (the `measure_effort`
    member of the §"Deviations from design v1.2" class; `scan()` already catches from Task 5).

**Expected RED split**: 10 failing, 9 passing. Failing: tests 1, 2, 3, 4, 6, the `grok-truncated`
and `unknown` items of test 7, test 8, test 11, test 12 (at RED the deep line no longer raises,
because Task 5 landed, and the result is shape `unparseable`, not `grok`). **Regression guards** (9): test 5 (today F-TRUNC is
`unparseable`, which routes to the same reason), the `missing`, `empty`, `parsed`, `grok`,
`codex-text` and `unparseable` items of test 7, tests 9 and 10.
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

**Code structure** (changes in `_cmd_exec`, in file order):
```bash
# header comment:
_cmd_exec() {  # <codex|agy|grok> <promptfile> [--cd <dir>] [--model <m>] [--effort <e>] [--out <file>] [--log <file>] [--timeout <s>] [codex: --sandbox <mode>] [agy: --sandbox] [grok: --sandbox <profile>]
# S1:
  case "$agent" in codex|agy|grok) ;;
    *) echo "hmad-dispatch: exec: unknown agent '$agent' (expected codex|agy|grok)" >&2; return 2 ;;
  esac
# --sandbox / --effort option comments add: grok: --sandbox passed verbatim; --effort -> --reasoning-effort
# S3 gains:  grok)  ;;   # grok's HPW_AGENT_BACKEND default is applied in child_env only (FR-3, OQ2)
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
    local recovered=""                       # was `local recovered` (set -u, design D3)
# S8 chain:
    if [ "$agent" = agy ]; then
      # agy arm, unchanged
    elif [ "$agent" = grok ]; then
      # Structured only (FR-4): no _verdict_after_boundary fallback on a grok log.
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
`HMAD_STUB_GROK_STREAM`, capture via `HMAD_STUB_CAPTURE`, `--log` given unless a test says otherwise):
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
      else
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

**Production file**: `h-mad/hooks/h-mad-tdd-gate.sh`
**Test file**: `h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/hooks/h-mad-tdd-gate.sh:Codex-authorship enforcement block` → `typed fallback_agent read of ACTIVE`
**WIRE-PIN**: `h-mad/tests/test_h_mad_tdd_gate_fallback_agent.py::test_block_grok_reads_the_active_features_fallback_agent`

**Description**: FR-2 / design D2 / plan W9. The new code goes between the closing `fi` of the
BLOCK-CODEX `if` and the comment `# Codex unavailable / declared exhausted → fall through: Claude may
author the`, inside the block headed `# --- Codex-authorship enforcement`. Because BLOCK-CODEX exits
whenever codex_out is false, the new read runs only when codex_out is true. BLOCK-CODEX is
byte-identical. The inherited no-`jq` exit 0 above the block is unchanged.

**Code structure** (landed literally; rows G1–G6 anchor it):
```bash
# fallback_agent (FR-2): read only when codex is out (the BLOCK-CODEX `if` above exits
# otherwise). A JSON-type tag, never `//` or a bare `-r` value: `false` and "null" must not
# read as absent.
FALLBACK_TAG=$(jq -r --arg k "$ACTIVE" '
  (.orchestrator_state[$k] // {}) as $r
  | if ($r | type) != "object" or ($r | has("fallback_agent") | not) then "absent"
    else $r.fallback_agent as $v
    | if   $v == null     then "null"
      elif $v == "grok"   then "grok"
      elif $v == "claude" then "claude"
      else "invalid " + ($v | tojson) end
    end' "$STATE_FILE" 2>/dev/null) || FALLBACK_TAG=""
case "$FALLBACK_TAG" in
  absent|null|claude) ;;
  grok)
    echo "[H-MAD-TDD-GATE] BLOCK: fallback_agent=grok — Phase 5 is authored by grok while codex is out, not by Claude." >&2
    echo "Dispatch this module to grok: hmad-dispatch exec grok <promptfile>  (stage it with h_mad_assemble_tdd.py --agent grok)." >&2
    echo "HMAD_CODEX_UNAVAILABLE does not override fallback_agent=grok. For a one-off Claude escape, record it —" >&2
    echo "  python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $ACTIVE --set fallback_agent=claude \"$STATE_FILE\"" >&2
    exit 1 ;;
  "invalid "*)
    echo "[H-MAD-TDD-GATE] BLOCK: fallback_agent=${FALLBACK_TAG#invalid } is not valid (valid: grok|claude) — refusing the write, fail-closed." >&2
    echo "  Fix it: python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $ACTIVE --set fallback_agent=grok|claude|null \"$STATE_FILE\"" >&2
    exit 1 ;;
  *)
    echo "[H-MAD-TDD-GATE] BLOCK: fallback_agent=<unreadable> is not valid (valid: grok|claude) — refusing the write, fail-closed." >&2
    echo "  The fallback_agent read failed. Fix it: python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py --feature $ACTIVE --set fallback_agent=grok|claude|null \"$STATE_FILE\"" >&2
    exit 1 ;;
esac
```

**Test harness.** The hook under test is the worktree's,
`Path(__file__).resolve().parents[1] / "hooks" / "h-mad-tdd-gate.sh"`, never
`~/.claude/hooks/h-mad-tdd-gate.sh` (which `test_h_mad_tdd_gate_codex.py` uses, and which resolves to
the main tree). Each cell builds a temp project: `docs/.bkit-memory.json` with feature `feat` at
`phase: step5` plus a second feature `other` at `phase: step3` with no `fallback_agent` (the G3
discriminator), and `shared/tests/test_widget.py` holding one failing test. It runs
`subprocess.run(["bash", HOOK, "shared/widget.py"], cwd=project, env=cell_env)`, where `cell_env["PATH"]` is
`f"{bindir}:/usr/bin:/bin"` (the bindir links the real `jq`, plus a `codex` stub script when codex is on
PATH; `/usr/bin/codex` does not exist on this host), `HOME` = `Path.home()`, `CLAUDE_PROJECT_DIR` =
project, `HMAD_CODEX_UNAVAILABLE` set or not, and `BASH_ENV`/`ENV` absent. The FALL-THROUGH fixture
is design V5's. Outcome classes are read from stderr's first line: BLOCK-CODEX is today's
`[H-MAD-TDD-GATE] BLOCK: Phase 5 implementation must be authored by Codex, not Claude.`; BLOCK-GROK
begins `[H-MAD-TDD-GATE] BLOCK: fallback_agent=grok — `; BLOCK-INVALID contains
` is not valid (valid: grok|claude)`; FALL-THROUGH is rc 0.

**Tests** (177 collected items):
1. `test_gate_matrix` (80) — 4 `codex_status` × 5 `fallback_agent` × 2 env × 2 PATH; the expected
   class comes from an in-test transcription of the FR-2 table, never from the hook; every cell asserts
   the derived test path exists as a precondition (AC-2.1).
2. `test_invalid_class_blocks_each_value_alone` (24) — `false`, `true`, `0`, `"null"`, `""`, `"Grok"`,
   `{}`, `[]`, each alone, under each of the three codex_out routes alone: exit 1, BLOCK-INVALID,
   stderr names `fallback_agent=<json.dumps(value, separators=(",", ":"))>` and `grok|claude`
   (AC-2.1b, AC-2.4).
3. `test_invalid_class_with_codex_available_is_block_codex` (8) — the same 8 values, codex_out false
   → BLOCK-CODEX (AC-2.1b).
4. `test_json_null_control_falls_through` (3) — stored JSON `null`, three routes (AC-2.1b control).
5. `test_absent_key_control_falls_through` (3) — no key, three routes (AC-2.1b control).
6. `test_absent_null_claude_match_the_base_hook` (48) — for `fallback_agent` absent, `null` and
   `"claude"`, each of the 16 cells (4 `codex_status` × 2 env × 2 PATH): exit code and stderr equal
   those of `git show BASE_SHA:h-mad/hooks/h-mad-tdd-gate.sh` run the same way, byte for byte (AC-2.2).
7. `test_block_grok_stderr_names_the_four_things` — `hmad-dispatch exec grok`, `--agent grok`,
   `--set fallback_agent=claude`, `HMAD_CODEX_UNAVAILABLE does not override fallback_agent=grok` (AC-2.3).
8. `test_block_grok_reads_the_active_features_fallback_agent` — `feat` holds `fallback_agent: "grok"`,
   `codex_status: "exhausted"`: exit 1, BLOCK-GROK. WIRE-PIN.
9. `test_other_feature_grok_does_not_change_active_outcome` — `other` holds `"grok"`, `feat` holds
   none, codex_out true: FALL-THROUGH (AC-2.5).
10. `test_exempt_files_stay_exempt_under_grok` (7) — targets `shared/test_widget.py`,
    `shared/tests/helpers.py`, `shared/fixtures/data.py`, `docs/notes.md`, `shared/config.toml`,
    `shared/run.sh`, `shared/widget.js`, with `feat` at `"grok"` and codex_out true: exit 0 (AC-2.6).
11. `test_fallback_read_error_fails_closed` — a `jq` shim in the cell's bindir that execs the real `jq`
    unless an argument contains `fallback_agent`, where it exits 5: BLOCK-INVALID from the `*)` arm, whose first line names the unreadable-value
    marker (design "read error fails closed").

**Expected RED split**: 55 failing, 122 passing. Failing: the 28 matrix cells with codex_out true and
`fallback_agent` `"grok"` or `"codex"`, the 24 invalid-class cells, and tests 7, 8 and 11.
**Regression guards** (122): the 52 other matrix cells (10 with codex_out false, 42 with codex_out
true and `fallback_agent` absent, `null` or `"claude"`), the 8 BLOCK-CODEX cells, the 3 + 3 controls,
the 48 base-comparison cells, test 9, and the 7 exemption cells.
**WIRE-PIN RED reason**: the hook falls through and exits 0, an assertion on the hook's exit and
stderr.
**Wire-scoped revert**: `(.orchestrator_state[$k] // {}) as $r` → `({}) as $r` only: every read is
`absent`, and the pin fails. Executed and scored as row WR12 (Task 14, `grok_wire_reverts.json`);
its `find` lands once, since G3's shorter `find` `.orchestrator_state[$k] // {}` already must.
**Force-fire**: row G3 (Task 14).

**Acceptance Criteria**:
- [ ] AC-2.1: all 80 cells match the table.
- [ ] AC-2.1b: 24 BLOCK-INVALID cells, 8 BLOCK-CODEX cells, and the JSON-`null` and absent controls.
- [ ] AC-2.2: absent, `null` and `"claude"` are byte-identical to the base hook in all 16 cells each.
- [ ] AC-2.3, AC-2.4, AC-2.5, AC-2.6 as the tests state.
- [ ] AC-2.7: the gate's mutation spec (Task 14) carries G1–G3, each killed by an AC-2.1 cell.

**Mutation rows** (Task 14): G1, G2, G3, G4, G5, G6 (`tdd_gate_fallback_agent.json`) and WR12
(`grok_wire_reverts.json`) — 7 rows.

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

**Description**: Author the seven spec files with exactly the 57 rows below, then for each spec run
`python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors <spec>` (read `ANCHORS:`) and
`python3 h-mad/scripts/h_mad_mutation_harness.py <spec>` (read `MUTATION:`). The pass condition is
`ANCHORS_OK` and `MUTATION: ALL_CAUGHT` for all seven; `SURVIVED` or `REFUSED` halts and is reported
against the owning task. Also run the design's W1 residual precondition
`PATH=/usr/bin:/bin command -v grok` (must fail, rc 1) before scoring row W1.

In the tables, `⏎` inside a `find`/`replace` stands for a newline and `\|` for a literal `|`; each cell is the raw source text,
and JSON escaping (`\"`, `\\`, `\n`) is applied when it is written into the spec.

**`tdd_gate_fallback_agent.json`** — file `hooks/h-mad-tdd-gate.sh`; `command`
`["python3.11","-m","pytest","tests/test_h_mad_tdd_gate_fallback_agent.py","-q"]`; `target_command`
`["python3.11","-m","pytest","-q"]`.

| Row | name | find | replace | test |
|---|---|---|---|---|
| G1 | `g1-block-grok-falls-through` | `    exit 1 ;;⏎  "invalid "*)` | `    ;;⏎  "invalid "*)` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_gate_matrix` |
| G2 | `g2-env-bypasses-block-grok` | `    exit 1 ;;⏎  "invalid "*)` | `    [ -n "${HMAD_CODEX_UNAVAILABLE:-}" ] \|\| exit 1 ;;⏎  "invalid "*)` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_gate_matrix` |
| G3 | `g3-reads-another-feature` | `.orchestrator_state[$k] // {}` | `[.orchestrator_state \| to_entries[] \| select(.key != $k) \| .value][0] // {}` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_gate_matrix` |
| G4 | `g4-slash-slash-reintroduced` | `  \| if ($r \| type) != "object" or ($r \| has("fallback_agent") \| not) then "absent"` | `  \| if ($r \| type) != "object" or (($r.fallback_agent // null) == null) then "absent"` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_invalid_class_blocks_each_value_alone` |
| G5 | `g5-string-null-collapses` | `    \| if   $v == null     then "null"` | `    \| if   $v == null or $v == "null" then "null"` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_invalid_class_blocks_each_value_alone` |
| G6 | `g6-read-error-fails-open` | `  *)⏎    echo "[H-MAD-TDD-GATE] BLOCK: fallback_agent=<unreadable>` | `  *) ;;⏎  __never__)⏎    echo "[H-MAD-TDD-GATE] BLOCK: fallback_agent=<unreadable>` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_fallback_read_error_fails_closed` |

(`\|` in the table is a literal `|` in the source.) G1 and G2 share one `find` with different
`replace`s; the harness applies one row at a time. G3 is also W9's force-fire.

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
five files, so `file` is per row (as `review_evidence_format.json` already does); `command`
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
| WR12 | `wr12-gate-reads-no-record` | `hooks/h-mad-tdd-gate.sh` | `(.orchestrator_state[$k] // {}) as $r` | `({}) as $r` | `tests/test_h_mad_tdd_gate_fallback_agent.py::test_block_grok_reads_the_active_features_fallback_agent` |

WR9-1 shares W1's `find` with a different `replace` (`if false` removes the arm; W1's `if true`
force-fires it). WR7-2 removes what A2 disables, but is scored on WIRE-PIN 2 rather than on A2's
test. No row's `replace` contains its own `find`. Every row names exactly one WIRE-PIN: 13 rows for
the 13 WIRE entries of Tasks 3 (1), 4 (1), 6 (1), 7 (2), 9 (4), 10 (2), 11 (1) and 12 (1).

**Row count**: 6 + 19 + 10 + 4 + 2 + 3 + 13 = 57 (unit: mutation rows; the seven tables above,
in order). By owning task: Task 12 7, Task 8 11, Task 9 7, Task 10 6, Task 11 2, Task 5 7, Task 6 4,
Task 7 6, Task 3 3, Task 4 4 — sum 57. The design's rows are 34 named rows (G1–G6, P1–P9, L1–L5,
E1–E8, A1–A3, T1, R1–R2) plus 9 force-fires that are not aliases of a named row (W1, W2, W3a, W5,
W6, W7a, W8, W10a, W11) = 43; W3b = P5, W4 = P7, W7b = A2, W9 = G3, and W10b has no row. This plan
adds E9 and WR3–WR12 (13 rows): 43 + 1 + 13 = 57 (§"Deviations from design v1.2", item 3).

**Expected RED split**: not applicable — no test is authored. The verdict is seven `ANCHORS: ANCHORS_OK` and
seven `MUTATION: ALL_CAUGHT` tokens, plus the committed sweep test green in the full suite with 106
specs (99 at `507214d` + 7).

**Acceptance Criteria**:
- [ ] AC-2.7: `tdd_gate_fallback_agent.json` is committed with G1–G3, and each is killed by an
      AC-2.1 cell (`test_gate_matrix`).
- [ ] Every row lands exactly once (`ANCHORS_OK`) and every row is caught (`ALL_CAUGHT`).
- [ ] W1–W11 each have a force-fire row or a named alias row, except W10b (stated residual).
- [ ] Every WIRE's removal direction is executed and scored: the 13 `grok_wire_reverts.json` rows are
      each caught by the named WIRE-PIN (`MUTATION: ALL_CAUGHT` on that spec).

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

- **Phase-5 section:** the FR-2 table with `fallback_agent`; OQ1 (`HMAD_CODEX_UNAVAILABLE` does not
  override `fallback_agent=grok`); `no write-time test-first gate` (codex writes pass
  `h-mad/hooks/h-mad-codex-tdd-gate.py`, grok writes pass nothing); the inherited no-`jq` fail-open.
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
   `no write-time test-first gate` (AC-10.1).
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
BASE_SHA="$(python3 -c 'import sys; sys.path.insert(0, "h-mad/tests"); import grokfixtures; print(grokfixtures.BASE_SHA)')"
printf '%s' "$BASE_SHA" | grep -qE '^[0-9a-f]{40}$' || { echo "FAIL: BASE_SHA is not 40-hex: $BASE_SHA"; exit 1; }
/opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts
T="$(mktemp -d)" || { echo "FAIL: mktemp"; exit 1; }
git archive "$BASE_SHA" h-mad handoff | tar -x -C "$T" || { echo "FAIL: git archive $BASE_SHA"; exit 1; }
(cd "$T" && /opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts 2>&1 | grep '::' | sort) > "$T/base.txt"
/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts 2>&1 | grep '::' | sort > "$T/head.txt"
[ -s "$T/base.txt" ] || { echo "FAIL: the base collect listed no node ids"; exit 1; }
[ -z "$(comm -23 "$T/base.txt" "$T/head.txt")" ] \
  || { echo "FAIL: node ids collected at BASE_SHA are gone"; comm -23 "$T/base.txt" "$T/head.txt"; exit 1; }
git ls-tree -r --name-only "$BASE_SHA" -- h-mad/tests handoff/tests handoff/scripts \
  | grep -E '(^|/)(test_[^/]*\.py|conftest\.py)$' > "$T/pre.txt"
[ -s "$T/pre.txt" ] || { echo "FAIL: no pre-existing test file listed at BASE_SHA"; exit 1; }
while IFS= read -r f; do
  git diff --exit-code "$BASE_SHA" -- "$f" || { echo "FAIL: pre-existing test file differs from BASE_SHA: $f"; exit 1; }
done < "$T/pre.txt"
[ "$(grep -c 'codex|agy|grok\|agy|codex|grok' h-mad/scripts/hmad-dispatch.sh)" -eq 6 ] \
  || { echo "FAIL: the agy|codex|grok census is not 6 matching lines (design D8)"; exit 1; }
grep -rln 'from h_mad_review_evidence import\|agy_events\|_exec_log_format\|OpenAI Codex' \
  h-mad/scripts h-mad/hooks h-mad/bin | grep -v __pycache__                 # the design's class sweep, recorded
echo "FLOOR: PASS files=$(wc -l < "$T/pre.txt" | tr -d ' ')"
rm -rf "$T"
```

`BASE_SHA` is the constant in `h-mad/tests/grokfixtures.py`. The script runs as one `bash` script
(or one Bash-tool call); `set -e` is not relied on, because it is inert in the Bash tool's top-level
shell, so every check carries its own `|| { echo "FAIL: …"; exit 1; }`, and the verdict is the last
line `FLOOR: PASS files=N`, never `$?`. The suite's own verdict is read from pytest's summary line
(`N passed`, with the Preamble's one environment-dependent failure the only permitted `failed`).

**The unmodified gate** (codex cycle-1 must-fix 3, orchestrator decision 4). Every pre-existing test
file, meaning every `test_*.py` and `conftest.py` tracked at `BASE_SHA` under the three test paths
(124 files at `507214d`: `git ls-tree -r --name-only 507214d -- h-mad/tests handoff/tests
handoff/scripts | grep -E '(^|/)(test_[^/]*\.py|conftest\.py)$' | wc -l`, unit: files), is diffed
against `BASE_SHA` directly with `git diff --exit-code "$BASE_SHA" -- <file>`, which must print
nothing and exit 0 for each file, so an added skip decorator, an added line, or a deleted file all
fail it. The v1.0 `--numstat` check only caught deleted lines. The node-id floor (`comm -23` empty)
stays as a second, independent check. Task 1's edits to `h-mad/tests/stubs/codex` and
`h-mad/tests/stubs/agy` are test support, not test files, and are outside this list by its filter. The class sweep's reading at `0b3f969`
was 4 files; a new file in its output is a new content classifier that needs the FR-5 precedence.
The `_cmd_exec` agent-conditional census is re-measured with the design's D3 `awk` command, because
S4 and S8 moved it by construction; its reading is recorded, not compared.

**Expected RED split**: not applicable — no test is authored.

**Acceptance Criteria**:
- [ ] AC-11.1: the full suite passes with every pre-existing test unmodified (the one
      environment-dependent node named in the Preamble excepted, for its recorded reason).
- [ ] AC-11.2: `test_hmad_dispatch_exec.py`, `test_hmad_dispatch_exec_completion.py`,
      `test_hmad_dispatch_exec_stamp.py`, `test_hmad_dispatch_progress.py` pass in that full run.
- [ ] AC-5.3, AC-6.5, AC-7.5, AC-9.4: the named pre-existing files pass unchanged in that run.
- [ ] Every pre-existing test file (`test_*.py` / `conftest.py` tracked at `BASE_SHA` under
      `h-mad/tests`, `handoff/tests`, `handoff/scripts`) is byte-identical to `BASE_SHA`
      (`git diff --exit-code` per file); the node-id floor (`comm -23` empty) holds as a second
      check; the census reads 6 matching lines; the script's last line is `FLOOR: PASS files=N`.

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
merge. About $0.04 at F0's measured `total_cost_usd=0.0393`.

```bash
W="$(git -C /Users/kimhawk/orca/skills worktree list --porcelain \
  | awk '/^worktree /{p=$2} /^branch refs\/heads\/feature\/216-grok-codex-fallback$/{print p}')"
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
  `docs/03-analysis/probes/grok-codex-fallback/exec-grok-smoke.md`. `$S` is removed after the record
  is written.
- **Any other result halts.** A live envelope that disagrees with F0 fixes the parsers against the
  observed envelope and the smoke re-runs. **If the smoke cannot run** (no key, no quota, no `grok` on
  PATH, a refusal of `--effort low`), Phase 5 halts and asks the operator; a skipped smoke never
  passes, and merge does not proceed on "not run".
- **Residual (plan):** `--model` and `--sandbox` meet only the stub and `grok --help`, never the live
  CLI. D3.4's `< /dev/null` and D3.3's `env` prefix are the two mechanisms this smoke exercises that
  no stub can falsify.

**Expected RED split**: not applicable — no test is authored.

**Acceptance Criteria**:
- [ ] Every pass condition above holds, with the record complete.

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
Task 4 9, Task 5 16, Task 6 7, Task 7 19, Task 8 21, Task 9 30, Task 10 15, Task 11 2, Task 12 177,
Task 13 23, Task 15 7 — total 357, of which 178 fail at RED and 179 are regression guards or
first-run passes (the per-task splits sum to these: failing 10+4+9+9+15+4+10+21+23+10+2+55+0+6,
passing 2+4+2+0+1+3+9+0+7+5+0+122+23+1).

**Task graph**: Tasks 1 and 2 are independent (`Dependencies on other tasks: None`). After Task 1,
Tasks 3, 4, 5, 8 and 12 can run in parallel (they touch distinct files); Tasks 6 and 7 follow
Task 5; Task 9 follows Task 8; Task 10 follows Task 9, and Task 11 follows Task 10 (Tasks 8, 9, 10
and 11 all edit `h-mad/scripts/hmad-dispatch.sh`, so they run one after another, never in
parallel); Task 13 follows 4, 6, 7 and 10; Task 15 follows 3, 9, 11 and 12; Task 14 follows 3–12;
Task 16 follows 13, 14 and 15; Task 17 is last. Wiring tasks: 3, 4, 6, 7, 9, 10,
11, 12 (8 tasks carrying W1–W11: W1–W4 Task 9, W5 Task 10, W6 Task 6, W7 Task 7, W8 Task 11, W9
Task 12, W10 Task 3, W11 Task 4).

## Version History
- v1.0: Initial implementation plan draft (2026-09-28), authored at 507214d from spec v1.4, design v1.2 and plan v1.3 (no audit cycle yet). 17 tasks, 8 wiring (W1-W11), 43 mutation rows in six specs, 354 new test items, live exec grok smoke last.
- v1.1: Impl-plan audit cycle 1 answered (2026-09-28; codex p1 4 musts + 1 should, doc-auditor teammate 1 must + 2 shoulds + nits, audit commit 5b294a8), re-verified at 76b2501 (h-mad unchanged since 507214d). scan() catches RecursionError (Deviations section: class rule over every --log JSON parse, members scan/CLI/measure_effort/archreview _evidence_counts, new tests Task 5 11-12 and Task 7 12, row E9); Task 16 depends on Task 13; all 13 wire-scoped removals executed and scored as grok_wire_reverts.json rows WR3-WR12 keyed on their WIRE-PINs; Task 16 diffs each of the 124 pre-existing test files against BASE_SHA with git diff --exit-code plus the node-id floor; Task 17 smoke and Task 16 floor are guarded scripts ending in SMOKE: PASS / FLOOR: PASS; Task 10 renderer landed as _GROK_RENDER_PROG with its algorithm, executed on F0; suite paths include handoff/scripts; Task 2 pre-creates the state file and pops the key; Tasks 10 and 11 sequential. 17 tasks, 8 wiring, 57 mutation rows in seven specs, 357 new test items.
