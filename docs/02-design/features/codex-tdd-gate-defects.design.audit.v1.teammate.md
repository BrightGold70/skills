## Summary
Gating pass on `docs/02-design/features/codex-tdd-gate-defects.design.md` at eec0c7a6. The working tree matches the commit (`git diff --stat eec0c7a6 -- <design>` printed nothing), and no h-mad/handoff file changed between 1ef1a782 and eec0c7a6. Most tree premises check out when re-run. These match: the `_suite_summary` readings, the coloured `(1, 0)` reading, the import chain, the stale-prose per-file counts, the 4 `returncode == 1` lines, the 7 `jq` lines, the 21 named tests, the D11 locators and the audit_suite_gate.json anchors. Three blocking gaps remain. First, the "closed" summary grammar rejects pytest 9.1.1's own `subtests` summary phrases. Second, the design never mentions the grok-codex-fallback D2 conflict it creates. Third, DD-7's acknowledged softening has no Guard-narrowing differential. On the dispatch's framing: the document lists nine overrides, DD-1..DD-9, not five. Every DD row states a revert except DD-5.
Evidence: 19 files opened, 47 greps run.

## Must-fix
- The summary-line grammar's "closed word set" rejects pytest 9.1.1's core output whenever subtests run. It therefore breaks spec OD-7/FR-4 "existing callers keep their current results", and it makes the judge deny a legitimate RED test. Measured with `/opt/anaconda3/bin/python -m pytest <f> -x -q --no-header` (pytest 9.1.1) in a scratch dir:
  - a passing subtests file ends `2 passed, 2 subtests passed in 0.00s`, and a failing one ends `2 failed, 1 subtests passed in 0.02s`.
  - The design's regex, with W substituted and run under `/usr/bin/python3`, matches neither line (`False`, `False`).
  - Today's `_suite_summary('2 passed, 2 subtests passed in 0.00s')` returns `(2, 0)`, which is PASS. After the change it returns `None`, which makes `run_suite` UNREADABLE `no_summary`: a PASS→UNREADABLE flip.
  - The judge would read a RED subtests test as DENY `no-summary`, never `red-measured`.
  - instance of: pytest summary categories, which are an open set. `_pytest/terminal.py:63` defines `KNOWN_TYPES` with the three two-word entries `"subtests passed"`, `"subtests failed"` and `"subtests skipped"`. Line 1420–1422 then appends any plugin-reported category (`unknown_types`) to the summary.
  - The zero is not evidence. No test in either repo uses subtests: `git grep -l -w subtests -- h-mad handoff` returned nothing, and HemaSuite `git grep -l -w subtests -- '*.py'` returned 0 files at 3f0c9f3a. The zero rests on nobody using subtests yet, not on the grammar being right.
  - Rule over the class: a phrase is `\d+ <one or more lowercase words>`. `passed`, `failed` and `error`/`errors` are counted only when the phrase is exactly that one word, so `subtests passed` adds nothing to `passed`. Alternatively, add `subtests (passed|failed|skipped)` to W and state that plugin categories are a residual.
  - Either way, add the two measured lines as D7 grammar rows and `run_suite` table rows.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `is the closed word set`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `Their existing callers keep their current results`
- The design is silent on the grok-codex-fallback D2 conflict, and it deletes every construct that D2 is built on. `grep -ci grok <design>` → 0 matching lines, and there is no match for `fallback_agent`, `rebase` or `merge order` either.
  - What grok's design D2 builds on (worktree `/Users/kimhawk/orca/skills-grok-codex-fallback`, lines 143–228):
    - it places a `jq` read of `.orchestrator_state[$ACTIVE].fallback_agent` after the BLOCK-CODEX `fi`;
    - it refuses with `exit 1 ;;` arms (3 matching lines in that design);
    - it states the no-`jq` fail-open as an inherited, unchanged path.
  - What this design removes: DD-2 and D9's "What leaves the gate" take out `jq`, the `ACTIVE`/`head -1` read, `CODEX_STATUS` from `jq` and every `exit 1`.
  - D10's only accommodation is a one-line "extension point", and it leaves three things undecided:
    - how a type-preserving tag (`absent|null|grok|claude|invalid <json>`) is encoded in a fourth `record=` field;
    - which record governs when OD-9 allows several ACTIVE records (grok D2 reads only `$ACTIVE`);
    - which gate-side `_refuse` kinds BLOCK-GROK and BLOCK-INVALID use.
  - Why it matters now: grok's Task 12 (`tdd-gate-fallback-agent`, impl-plan line 1457) is not implemented yet (its branch head `ad2afdae` is Task 8 GREEN). Plan §Convention Prerequisites merges this feature first, and plan R2 requires grok's "new refusals must use this feature's refusal function".
  - Prescription, either:
    - (a) specify the `fallback=` record field, produced by the judge, together with its multi-record rule and kinds; or
    - (b) add an explicit "Sibling: grok-codex-fallback D2" section that routes a re-design to grok's design. That section names the three constraints (no `jq`, no `$ACTIVE`, no `exit 1`) and the grok sentence DD-2 makes false.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `A later field is appended to`
  quote: /Users/kimhawk/orca/skills-grok-codex-fallback/docs/02-design/features/grok-codex-fallback.design.md › `the hook exits 0 before this`
- DD-7 knowingly softens the Claude gate, but the design supplies no Guard-narrowing differential for it.
  - The softening: a relative `tests/x.py` or `fixtures/x.py` was gated and is now exempt, because `$ROOT_ABS/tests/x.py` matches `*/tests/*` (hook lines 121–123).
  - The invariant §"Guard narrowing" requires an old-versus-new corpus that accounts for every softened input. The Test Plan carries the differential only for the Codex shell policy (D8/D12). DD-7 is "listed by name", and the invariant says a name is not enough.
  - Prescription: add a Claude-gate exemption differential. Run the old gate (`git show <base>:h-mad/hooks/h-mad-tdd-gate.sh`) and the new one through the positional entry point over {relative, `./`-relative, absolute} × {`tests/x.py`, `fixtures/x.py`, `sub/tests/x.py`, `test_x.py`, `x.md`, `x.py`} × {state none, active}. Publish the softened rows. Expected softened set: the relative and `./`-relative top-level `tests/…`/`fixtures/…` rows only.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `relative exemption is a second softening`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `It is listed by name`

## Should-fix
- D8 states the payload-`cwd` base rule twice, and the two statements differ.
  - `_relative_target` resolves the cwd (`Path(cwd).expanduser().resolve()`, and it must be a directory equal to or under root).
  - `_contained_venv_python` says only "the payload `cwd` when it is inside `root`", with no resolve.
  - `_project_root` returns a resolved root (hook lines 87–109). On this machine `TMPDIR=/var/folders/…` and `/var -> private/var`.
  - V-1r builds its cwd from `mktemp -d "${TMPDIR:-/tmp}/…"`. So an implementer who tests the unresolved cwd against the resolved root sends `base` to root, and `.venv/bin/python` then names `<root>/.venv/bin/python`, which does not exist. The result is a deny, and `red-shell-pytest-allows` fails.
  - Single-source prescription: one helper, `_payload_cwd_base(root, cwd)`, that both callers use.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `when it is inside`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `or lies below it`
- D9 step 9 re-implements the escape-status set in bash: the blocker is the first record whose status is not `unavailable` or `exhausted`. This contradicts D10's claim that the OD-9 rule has one implementation.
  - If the judge's `ESCAPE_STATUSES` changes, `codex-escape=no` can arrive with no blocker the gate recognises, and the hint then names an empty `--feature`.
  - Prescription, either: have the `state` line carry `blocker=<key>,<state-file>`, or have the judge order the non-escaping records first so the gate takes `record=` #1 without testing statuses.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `whose status field is not`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `The rule has one implementation, in the judge.`
- DD-1 cites the wrong document. The order "governance first, then exemptions" is written in the plan's Implementation Strategy, layer 6 steps 3→4. Spec FR-6 says only that the Codex-authorship check comes "after the exemptions". As written, DD-1 routes to the spec, and the plan sentence it actually departs from stays unrouted.
  class: measurement
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `Spec FR-6 order: governance first, then the exemptions`
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `verb decides governance. No step5 record`
- DD-2 cites only the plan's §"What we deliberately do not touch". Two other documents still list the no-`jq` fail-open as kept: spec §Out-of-Scope (line 605) and plan §"Out-of-Scope (confirmed from spec)" (line 1377). Both go false under DD-2 and neither is routed. List both in DD-2's "Departs from" cell.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `which stay as documented: no state, no`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `What we deliberately do not touch`
- Three departures are not recorded in §"Supersedes the plan or the spec on":
  - (a) Plan Architecture says pytest is bounded with `subprocess.run(timeout=…)`. D6 uses `Popen(start_new_session=True)` with `killpg`. The measured survivor justifies the change, but it is not listed.
  - (b) Spec FR-6 reads `tool_input.file_path`, then the top-level `file_path`, then the positional argument. D9 step 2 reads `$1` first and adds a `path` fallback. Reading positional first has a real reason (`cat` blocks on a tty when the hook is invoked by hand), but the design does not state it.
  - (c) Spec FR-4 rule 2 matches `No module named pytest` "in the output". D7 rule 2 narrows that to a whole line that ends with it.
  - Each needs a DD row with its reason and revert. If (b) is resolved toward the spec's order instead, it becomes a build change.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `The judge bounds pytest with`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `then the top-level`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `else from stdin JSON via the existing`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `in the output`
- DD-5's revert cell, "None needed", is not a revert. A different way to make the list total exists: rule 8 → `no-summary`. That keeps FR-1's table meaning for `no-tests-ran` ("The summary is `no tests ran`"), which DD-5 stretches to cover `3 skipped` and `1 xfailed`. State that alternative as the revert and route the kind-table wording to the spec.
  class: measurement
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `None needed; this totalises the spec's list`
- D1's premise command cannot produce the output the design attributes to it. I re-ran the exact command under `/usr/bin/python3` in `h-mad/scripts`: rc 0 and no output, because the command has no `print`. The recorded "3.9.6 ok" therefore came from some other command. Record the command that was actually run, for example with `print(sys.version.split()[0], "ok")` appended.
  class: measurement
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `3.9.6 ok`
- The claim that no test pins the Codex gate's reason text is a false absence. The zero comes from searching only for the old full phrases.
  - `git grep -n 'permissionDecisionReason"\]' -- h-mad/tests handoff` → 6 matching lines, all in `test_h_mad_codex_runtime.py`. They pin these substrings:
    - `failing test` at lines 98 and 125;
    - `apply_patch` at line 153;
    - `exit 1` at line 316;
    - `identify` at line 361;
    - `state` at line 373.
  - By reading, D8's new strings keep "failing test" and "state", the "apply_patch" and "identify" messages are unchanged, and line 316 is AC-5.3's named change. So nothing breaks, but the premise should list these six and say why each survives.
  class: measurement
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `No test pins the Codex gate's reason text`
- D3 and D7 leave a gap when some candidate test files exist and others do not.
  - `test-missing` is specified only for the case where no candidate exists.
  - With a mix, a missing candidate either:
    - is skipped, or
    - is run, and pytest then prints `ERROR: file or directory not found` plus `no tests ran`, which classifies as `no-tests-ran` and outranks `test-passing` in the D7 precedence.
  - Prescription, either: skip non-regular candidates and name them `missing` in the reason, or score a missing candidate as `test-missing` ahead of the others. Add an AC-2.4-style fixture for the chosen rule.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `If no candidate is a regular file, the verdict is`
- D12 does not name the interpreter that builds the fixture venv, yet the plan's spelling axis includes `.venv/bin/python3.14`. That name exists only if the venv is built by Python 3.14.
  - `/opt/anaconda3/bin/python --version` → 3.11.8. `/opt/homebrew/bin/python3` is 3.14.7 (plan P3).
  - Pin the interpreter, or derive the versioned name from whichever interpreter builds the venv. Otherwise that row silently stops testing a versioned name.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `is made by`
- D9 step 3 lets `ROOT_ABS` be empty when `CLAUDE_PROJECT_DIR` cannot be entered. Steps 8 and 10 then pass `--root ""`, and the judge would take the process cwd as root. This is unspecified. Prescription, either: refuse `judge-error` when `ROOT_ABS` is empty after the fast path finds a state file, or have the CLI reject an empty `--root` with a usage error (the gate then refuses `judge-error`).
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `This is string work only.`
- The Codex-authorship hint regresses. It now takes the state-file path from the D10 `record=` field, which is percent-encoded and root-relative. Today the hint prints the absolute `$STATE_FILE` inside the `h_mad_state_write.py … "<file>"` remedy (hook line 149). After the change, a path containing a space prints `%20`, and a relative path is wrong from any cwd other than the root. Prescription: unquote and re-absolutise the path before printing, or have the `state` verb also emit the raw absolute path in a field used only for the hint.
  class: build
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `and the state file in the hint`
  quote: docs/02-design/features/codex-tdd-gate-defects.design.md › `Paths are root-relative`

## Nit
- D2's residual names only a dangling symlink. The class is any non-regular state path:
  - a directory, which fails `-f` in the Claude fast path and makes `read_text` raise `IsADirectoryError`;
  - a FIFO, which makes `read_text` block, and `_any_phase5_status` blocks on it first on the Codex side.
  
  State the rule (`S_ISREG` on `os.stat`, else `unreadable`) and its residual.
- DD-7's claim of parity with `_is_production_python` is partial. The Claude exemption matches `*/tests/*` against the whole absolute path, including the root prefix. The Codex gate tests only root-relative parts. So a project rooted under a `tests/` directory is fully exempt on the Claude side only. This is pre-existing for absolute targets and should be stated as a residual.
- D9 shows `SOUT=$(…) || SRC=$?` and `JOUT=$(…) || JRC=$?` without initialising `SRC` or `JRC`. Under `set -u`, the success path would then fail with nounset, fall into the trap, and refuse every governed write. Show `SRC=0` and `JRC=0`.
- The `Hook:` line that FR-7 uses as a locator in `codex-implementer-prompt.md` names `~/.claude/hooks/h-mad-tdd-gate.sh`, the Claude gate. The prompt is dispatched to Codex, whose writes hit the Codex gate. That line is stale too, and D11 rewrites only the bullets under it.
- Both AC-1.2 `timeout` fixtures run at the default budget of about 40 s each, so they add at least 80 s to a suite already measured at 605 s. Say so, or run the gate-level `timeout` through a shim that is slow only past the budget.
