# Multi-host runtime analysis

## Baseline at BASE_SHA

`BASE_SHA=3b5c4388b4f11b7011eacf7aae6f95a6445f433f`, derived as the parent of the `BASELINE: OK` commit on `feature/multi-host-runtime`.

### Calibration at BASE_SHA

Command: `bash docs/03-analysis/probes/multi-host-runtime/calibrate.sh "$BASE_SHA"`

```text
== h-mad/SKILL.md
  10 $HOME/.claude
   8 Agent(
   2 CLAUDE
   1 CLAUDE_CODE_SESSION_ID
   2 CLAUDE_CONFIG_DIR
   2 Skill(
   1 `PermissionRequest`
   2 `PostToolUseFailure`
   3 `PostToolUse`
   6 `PreToolUse`
   2 `SendMessage`
   1 `SessionStart`
  82 ~/.claude
TOTAL h-mad/SKILL.md occurrences=122 distinct=13
== handoff/SKILL.md
  19 $HOME/.claude
   1 CLAUDE
   2 CLAUDE_CODE_ENABLE_TODO_TOOLS
  18 CLAUDE_SKILLS_ROOT
   1 Skill(
   7 `TaskCreate`
   1 `TaskGet`
   3 `TaskList`
   2 `TaskUpdate`
   5 `TodoWrite`
   3 `ToolSearch`
   9 ~/.claude
TOTAL handoff/SKILL.md occurrences=71 distinct=12
CALIBRATE: OK sha=3b5c4388b4f11b7011eacf7aae6f95a6445f433f
```

### Seed coverage at BASE_SHA

Command: `/opt/anaconda3/bin/python docs/03-analysis/probes/multi-host-runtime/seed_coverage.py --sha "$BASE_SHA" --registry docs/03-analysis/probes/multi-host-runtime/seed.json`

```text
ENTRY id=subagent-call h-mad=14 handoff=0 declared=h-mad verdict=ok
ENTRY id=skill-call h-mad=2 handoff=1 declared=h-mad,handoff verdict=ok
ENTRY id=advisor h-mad=18 handoff=0 declared=h-mad verdict=ok
ENTRY id=send-message h-mad=2 handoff=0 declared=h-mad verdict=ok
ENTRY id=hook-event h-mad=21 handoff=0 declared=h-mad verdict=ok
ENTRY id=task-tools h-mad=0 handoff=24 declared=handoff verdict=ok
ENTRY id=tool-search h-mad=0 handoff=5 declared=handoff verdict=ok
ENTRY id=session-id-env h-mad=1 handoff=0 declared=h-mad verdict=ok
ENTRY id=claude-config-dir h-mad=2 handoff=0 declared=h-mad verdict=ok
ENTRY id=skill-root-env h-mad=0 handoff=18 declared=handoff verdict=ok
ENTRY id=todo-tools-optin h-mad=0 handoff=2 declared=handoff verdict=ok
ENTRY id=claude-md h-mad=2 handoff=1 declared=h-mad,handoff verdict=ok
ENTRY id=claude-skills-dir h-mad=73 handoff=18 declared=h-mad,handoff verdict=ok
ENTRY id=claude-agents-dir h-mad=6 handoff=0 declared=h-mad verdict=ok
ENTRY id=claude-hooks-dir h-mad=6 handoff=0 declared=h-mad verdict=ok
ENTRY id=claude-settings h-mad=2 handoff=1 declared=h-mad,handoff verdict=ok
ENTRY id=claude-handoffs-dir h-mad=1 handoff=7 declared=h-mad,handoff verdict=ok
ENTRY id=claude-projects-store h-mad=3 handoff=0 declared=h-mad verdict=ok
ENTRY id=claude-homunculus h-mad=0 handoff=2 declared=handoff verdict=ok
ENTRY id=claude-home-bare h-mad=3 handoff=0 declared=h-mad verdict=ok
ENTRY id=session-reset-command h-mad=4 handoff=7 declared=h-mad,handoff verdict=ok
ENTRY id=skill-slash-invocation h-mad=15 handoff=11 declared=h-mad,handoff verdict=ok
SEEDCOV: PASS entries=22 stale=0 undeclared=0
```

### Task 1 gate and premises at BASE_SHA

All readings in this section use `BASE_SHA=3b5c4388b4f11b7011eacf7aae6f95a6445f433f`. The repository commands were launched with an empty inherited environment and explicit `PATH` and `HOME`; no `CLAUDE*`, `HPW_AGENT_BACKEND`, or `HMAD_HOST` was passed to their subprocesses.

| Check | Command | Reading |
|---|---|---|
| Derivation | §Preamble `BL=$(/opt/anaconda3/bin/python h-mad/scripts/h_mad_baseline_sha.py --branch feature/multi-host-runtime \| grep -m1 '^BASELINE:')`, then its `case` and parent `git rev-parse` | `BASELINE: OK sha=c0f8af67ea6fcd61bd60baa4a0b7081d586d1136 branch=feature/multi-host-runtime trunk=main`; parent `3b5c4388b4f11b7011eacf7aae6f95a6445f433f`, equal to Task 0. |
| Four-link gate | The plan's `for p in ~/.agents/skills ~/.gemini/config/skills; do for k in h-mad handoff; do test -L "$p/$k"; test "$(readlink -f "$p/$k")" = "/Users/kimhawk/orca/skills/$k"; done; done` with the plan's `HALT` branches | Four `test -L` and four resolution tests passed, for both skills under both roots; no `HALT`. |
| P4 | `grep -cE "exec: unknown agent '[^']*' \\(expected codex\\|agy\\)" h-mad/scripts/hmad-dispatch.sh` | `1`; `grep -c 'unknown agent'` → `8`; wider `(expected )?codex\|agy` count → `5`. |
| P5 | `grep -c 'exit 1' h-mad/hooks/h-mad-tdd-gate.sh`; `grep -c 'TARGET_PATH" \] && exit 0' ...`; `grep -c 'permissionDecision\|tool_input' ...` | `5`; `1`; `0` (the last `grep` exits 1 because it has no match). |
| P6 budget | `grep -n 'CLAUDE_CODE_SESSION_ID' h-mad/scripts/h_mad_context_budget.py`; `grep -o 'reason=[a-z_]*' ... \| sort -u` | `83:    session = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()`; `reason=bad_window`, `reason=no_transcript`, `reason=no_usage`. |
| P6 decision | `grep -n 'return "\|if not session_id' h-mad/scripts/h_mad_resume_decision.py` | `83: if not session_id`; ordered returns at lines 98/107/111/116: `start_fresh`, `cannot_judge`, `start_fresh`, `owned_elsewhere` (then `halted`, `complete`, `enter_autonomous`, `resume_manual`). |
| P9 | `grep -c '^## Host runtime' h-mad/SKILL.md handoff/SKILL.md`; ``grep -c '^| `cannot_judge`' h-mad/SKILL.md`` | `h-mad/SKILL.md:1`, `handoff/SKILL.md:1`; `1`. |
| P15 | JSON walk of `~/.claude/settings.json` `hooks.PostToolUse` for matcher `*` and `h-mad-advisor-warn.sh`; `grep -n 'transcript_path' h-mad/hooks/h-mad-advisor-warn.sh`; `grep -n -i transcript ~/.grok/docs/user-guide/10-hooks.md` | One global registration; hook lines `54` (comment) and `68` (`path = d.get("transcript_path") or ""`). Grok guide has prose uses at lines 342, 369 and 672, but no `transcript_path` payload field. |

`git diff --name-only "$BASE_SHA" HEAD -- h-mad handoff` was empty, so the working-tree P4/P5/P6/P9 commands above read the same tracked content as `BASE_SHA`. The P15 settings file is machine-local and was read during this gate.

### Refusal form at BASE_SHA

Command: `git show "$BASE_SHA":h-mad/hooks/h-mad-tdd-gate.sh` (full hook, every refusal site). The five `BLOCK:` branches all end in `exit 1`: Codex authorship, missing derivation script, no derivable test path, missing test file, and an already passing test. There is no rc-2 denial or `hookSpecificOutput.permissionDecision` denial. **`REFUSAL_FORM_AT_BASE=exit1`**.

### Suite floor and anchors at BASE_SHA

The orchestrator ran the plan's full `env -u HMAD_HOST /opt/anaconda3/bin/python -m pytest -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts` with the additional `CLAUDE*` and `HPW_AGENT_BACKEND` removal, capturing all output in `$GD/hmad-mhr-base-suite.txt`. Its short summary is:

```text
FAILED h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches
1 failed, 3892 passed, 1 warning in 578.43s (0:09:38)
PYTEST_RC=1
```

The failure asserts that the installed live binary no longer contains the exact `new Set(["description","hooks","modules","surface"])` spelling. One `FAILED`/`ERROR` line equals the summary's one failure plus zero errors. No timing-flake node failed in this run.

Node-id command: `/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests handoff/tests handoff/scripts 2>&1 | grep '::' | sort`. Reading: **3,893 node IDs**. The sandbox could not write the specified `$GD/hmad-mhr-base-nodeids.txt`; the complete sorted output is staged at `/private/tmp/hmad-mhr-base-nodeids.txt` for the orchestrator to place in the git directory before Task 18.

| Command | Reading |
|---|---|
| `/opt/anaconda3/bin/python h-mad/scripts/h_mad_mutation_harness.py --check-anchors h-mad/tests/mutation-specs/*.json` | `ANCHORS: ANCHORS_OK specs=99 mutations=907 ok=907 drifted=0 unreadable=0 skipped=0 unclassifiable=0` |
| `/opt/anaconda3/bin/python h-mad/scripts/h_mad_mutation_harness.py --check-anchors handoff/tests/mutation-specs/*.json` | `ANCHORS: ANCHORS_OK specs=7 mutations=69 ok=69 drifted=0 unreadable=0 skipped=0 unclassifiable=0` |

With an extra ambient `CLAUDE_ZZZ_PROBE=1`, the stripped child environment printed `CLAUDE_KEYS=[]` and `HPW_AGENT_BACKEND=None`; `seed_coverage.py --sha "$BASE_SHA" --registry docs/03-analysis/probes/multi-host-runtime/seed.json` still printed `SEEDCOV: PASS entries=22 stale=0 undeclared=0` with the same 22 entry lines.

### AC-6.1 pre-change adapter gap table

Source command for each column: `git show "$BASE_SHA":<adapter path>`; SHA is `3b5c4388b4f11b7011eacf7aae6f95a6445f433f`. `addressed` means the existing prose discusses the construct or its host substitute; it does not claim an FR-2 mapping row. Section names in parentheses identify the prose. `absent` means it does not. All 22 seed entries are included against all four existing adapters, including entries declared for the other skill.

| Construct | h-mad codex | h-mad agy | handoff codex | handoff agy |
|---|---|---|---|---|
| `subagent-call` | addressed (Collaboration mapping) | addressed (Author and reviewer roles) | addressed (Codex tool mapping) | addressed (agy tool mapping) |
| `skill-call` | absent | absent | addressed (Codex tool mapping) | addressed (agy tool mapping) |
| `advisor` | absent | absent | absent | absent |
| `send-message` | absent | addressed (Author and reviewer roles) | absent | absent |
| `hook-event` | addressed (Package and project roots; Trust boundary) | addressed (Hooks) | absent | absent |
| `task-tools` | absent | absent | addressed (Codex tool mapping) | addressed (agy tool mapping) |
| `tool-search` | absent | absent | absent | absent |
| `session-id-env` | absent | absent | absent | absent |
| `claude-config-dir` | absent | absent | absent | absent |
| `skill-root-env` | absent | absent | addressed (Resolve the skill package) | addressed (Resolve the skill package) |
| `todo-tools-optin` | absent | absent | absent | absent |
| `claude-md` | absent | absent | absent | absent |
| `claude-skills-dir` | absent | addressed (Package and project roots) | addressed (Resolve the skill package) | addressed (Resolve the skill package) |
| `claude-agents-dir` | addressed (Package and project roots) | addressed (Author and reviewer roles) | absent | absent |
| `claude-hooks-dir` | absent | absent | absent | absent |
| `claude-settings` | absent | addressed (Hooks) | absent | absent |
| `claude-handoffs-dir` | absent | absent | absent | absent |
| `claude-projects-store` | absent | addressed (Memory index) | absent | addressed (Mode routing) |
| `claude-homunculus` | absent | absent | absent | absent |
| `claude-home-bare` | absent | absent | absent | absent |
| `session-reset-command` | absent | absent | addressed (Mode routing) | addressed (Mode routing) |
| `skill-slash-invocation` | absent | absent | addressed (Codex tool mapping) | addressed (agy tool mapping) |

### AC-4.6 registry change record

Command: `bash docs/03-analysis/probes/multi-host-runtime/calibrate.sh "$BASE_SHA"`; the full reading is in §Calibration above. Comparison command: `bash docs/03-analysis/probes/multi-host-runtime/calibrate.sh 6494b3c`. The 13 distinct h-mad tokens and 12 distinct handoff tokens, including their counts, are identical in the two readings. **New distinct tokens: none.** Thus there are no new Claude constructs and no false hits to classify. `seed_coverage.py --sha "$BASE_SHA" --registry docs/03-analysis/probes/multi-host-runtime/seed.json` prints `verdict=ok` for every one of the 22 entries and `SEEDCOV: PASS entries=22 stale=0 undeclared=0`; **non-ok entries: none**. Resulting registry changes by kind: **add none; retire none; amend `skills` none; amend `pattern` none**. Task 3 can build the registry directly from `seed.json`.

### Registry branch coverage at BASE_SHA

The Task 3 registry contains the 22 seed constructs unchanged, as recorded in the AC-4.6 change record above. The §Preamble derivation returned `BASE_SHA=3b5c4388b4f11b7011eacf7aae6f95a6445f433f`, matching this document's baseline.

Command: `/opt/anaconda3/bin/python docs/03-analysis/probes/multi-host-runtime/seed_coverage.py --sha "$BASE_SHA" --registry h-mad/references/host-constructs.json --branches`

```text
ZERO id=claude-skills-dir branch="~/\\.claude/skills\\b" skill=handoff hits=0
ZERO id=claude-skills-dir branch="\\$\\{HOME\\}/\\.claude/skills\\b" skill=h-mad hits=0
ZERO id=claude-skills-dir branch="\\$\\{HOME\\}/\\.claude/skills\\b" skill=handoff hits=0
ZERO id=claude-agents-dir branch="\\$\\{HOME\\}/\\.claude/agents\\b" skill=h-mad hits=0
ZERO id=claude-hooks-dir branch="\\$\\{HOME\\}/\\.claude/hooks\\b" skill=h-mad hits=0
ZERO id=claude-settings branch="~/\\.claude/settings\\.local\\.json" skill=h-mad hits=0
ZERO id=claude-settings branch="~/\\.claude/settings\\.local\\.json" skill=handoff hits=0
ZERO id=claude-settings branch="\\$HOME/\\.claude/settings\\.local\\.json" skill=h-mad hits=0
ZERO id=claude-settings branch="\\$HOME/\\.claude/settings\\.local\\.json" skill=handoff hits=0
ZERO id=claude-settings branch="\\$HOME/\\.claude/settings\\.json" skill=handoff hits=0
ZERO id=claude-settings branch="\\$\\{HOME\\}/\\.claude/settings\\.local\\.json" skill=h-mad hits=0
ZERO id=claude-settings branch="\\$\\{HOME\\}/\\.claude/settings\\.local\\.json" skill=handoff hits=0
ZERO id=claude-settings branch="\\$\\{HOME\\}/\\.claude/settings\\.json" skill=h-mad hits=0
ZERO id=claude-settings branch="\\$\\{HOME\\}/\\.claude/settings\\.json" skill=handoff hits=0
ZERO id=claude-handoffs-dir branch="\\$HOME/\\.claude/handoffs\\b" skill=h-mad hits=0
ZERO id=claude-handoffs-dir branch="\\$HOME/\\.claude/handoffs\\b" skill=handoff hits=0
ZERO id=claude-handoffs-dir branch="\\$\\{HOME\\}/\\.claude/handoffs\\b" skill=h-mad hits=0
ZERO id=claude-handoffs-dir branch="\\$\\{HOME\\}/\\.claude/handoffs\\b" skill=handoff hits=0
ZERO id=claude-projects-store branch="\\$HOME/\\.claude/projects\\b" skill=h-mad hits=0
ZERO id=claude-projects-store branch="\\$\\{HOME\\}/\\.claude/projects\\b" skill=h-mad hits=0
ZERO id=claude-homunculus branch="\\$\\{HOME\\}/\\.claude/homunculus\\b" skill=handoff hits=0
ZERO id=claude-home-bare branch="\\$HOME/\\.claude\\b(?!/)" skill=h-mad hits=0
ZERO id=claude-home-bare branch="\\$\\{HOME\\}/\\.claude\\b(?!/)" skill=h-mad hits=0
ZERO id=session-reset-command branch="`/compact\\b" skill=handoff hits=0
ZERO id=skill-slash-invocation branch="`/h-mad\\b" skill=handoff hits=0
SEEDCOV-BRANCHES: entries=22 branches=54 cells=72 zero=25 dead=14
```

These 25 `ZERO` cells are the Phase-6 branch-classification inputs.

### Task 16 byte-identity probe readings

The orchestrator ran the first three arms at `BASE_SHA=3b5c4388b4f11b7011eacf7aae6f95a6445f433f` before this probe correction:

```text
BYTE-IDENTITY: PASS arm=budget cases=14
BYTE-IDENTITY: PASS arm=decision cases=18
BYTE-IDENTITY: PASS arm=install-a cases=9
```

Arm `install-b`: **to be re-run by the orchestrator after the `closed_diff()` fix**. This worker's sandbox cannot run the probe's `git worktree add`, so this document does not claim an arm-B pass. The plan's old-base budget negative control also needs an orchestrator run for the same reason.

The `closed_diff()` unit check used the diagnosed base payload `INSTALL: PASS\nOK\n` and a current payload with `INSTALL: FAIL issues=4` plus the four permitted real-root `SIBLING_WRONG_CHECKOUT:` lines. Its negative control added an unrelated, unfiltered issue:

```text
CLOSED_DIFF: PASS permitted_sibling_issues=4 base_trailing_OK=1
CLOSED_DIFF: PASS negative_unfiltered_issue=rejected
```

The in-sandbox missing-links negative control used an empty temporary `HOME` and returned:

```text
LINKS_ABSENT: BYTE-IDENTITY: UNREADABLE reason=links_absent exit=2
```

### Task 17 smoke-assertion rehearsal readings

Command: `CLAUDE_ZZZ_PROBE=1 env -i PATH=/opt/anaconda3/bin:/usr/bin:/bin HOME=/Users/kimhawk /opt/anaconda3/bin/python docs/03-analysis/probes/multi-host-runtime/smoke_assert.py rehearse`. Every `cases.json` expectation matched: **92 cases, 0 mismatches**. Key output:

```text
codex-R3: FAIL V-11.1 no adapter read
agy-R3: FAIL V-11.1 no adapter read
grok-R3: FAIL V-11.1 no adapter read
codex-R7-sed: PASS V-11.1
agy-R7-sed: PASS V-11.1
grok-R7-sed: PASS V-11.1
agy-R15: UNVERIFIED V-11.1 agy output shape unobserved
grok-R15: UNVERIFIED V-11.1 grok output shape unobserved
replay-agy: FAIL V-11.1 no adapter read
replay-codex: FAIL V-11.1 no adapter read
REHEARSAL: PASS n=92
```

R14(a)'s codex fixture has exactly one line matching `echo x # c; python3 h-mad/scripts/h_mad_state_write.py`; it matches `^\S+ -lc .* in \S+$` and holds no command newline. The agy and grok fixture JSON strings contain `\n`, which decodes to a real newline. The tokenizer control classified a script on every host with `commenters=""` and none with `commenters="#"`:

```text
R14(a) BYTE codex: grep_count=1 shape=True one_line=True
R14(a) BYTE agy: json_backslash_n=True decoded_newline=True
R14(a) BYTE grok: json_backslash_n=True decoded_newline=True
R14(a) COMMENTER host=codex commenters='' script_classified=True
R14(a) COMMENTER host=codex commenters='#' script_classified=False
R14(a) COMMENTER host=agy commenters='' script_classified=True
R14(a) COMMENTER host=agy commenters='#' script_classified=False
R14(a) COMMENTER host=grok commenters='' script_classified=True
R14(a) COMMENTER host=grok commenters='#' script_classified=False
```

The missing-heading control copied `h-mad/SKILL.md` and `codex-runtime.md` into a temporary checkout root, removed every `# ` heading from the adapter copy, and ran `v111` on `codex-R1.log`:

```text
NO_NEEDLE: UNREADABLE V-11.1 reason=no_needle exit=2
```

**Deviation:** `replay-agy` was predicted in the implementation plan and originally expected in `cases.json` to report `a script ran before the adapter was read`. The committed replay log has a script execution but no adapter read attempt. Design §D10's R2/R3 distinction therefore requires `FAIL V-11.1 no adapter read`. `cases.json` now records that verdict; the plan and design were not edited.

### Task 16 — orchestrator-run readings (codex sandbox cannot `git worktree add`)

Run 2026-09-29 from the worktree after the `closed_diff()` fix, BASE_SHA `3b5c4388`:
- `--arm install-b` (real default roots, all four links present) → `BYTE-IDENTITY: PASS arm=install-b cases=10`.
- Negative control 5, `env HOME=<empty scratch>` → `BYTE-IDENTITY: UNREADABLE reason=links_absent`, exit 2.
- Negative control 6, `--base 9df441ca --arm budget` → `BYTE-IDENTITY: FAIL arm=budget case=run-ok-unset`.
