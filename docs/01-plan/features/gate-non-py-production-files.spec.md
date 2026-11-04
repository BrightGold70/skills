# Spec: gate-non-py-production-files

## Executive Summary
During H-MAD Phase 5, a non-Python file is TDD-judged on all three write gates (Claude, codex, agy) **if and only if** three things hold. It is code-like (not a doc/data file, see Terms). It is not exempt as a test, fixture, root-`docs/` or out-of-root path. And the active feature's impl-plan lists it on some Task's **Production file** line. It is judged by that Task's listed test files, using the same RED rule as `.py`. Unlisted non-`.py` files stay allowed. Doc/data files stay allowed **even when a Task lists them**. Wire-pin 5b stops printing its `ungated:` line. The h-mad prose that states which files the gates judge is updated to the shipped rule (FR-10).

## Goal
Bring the code that most h-mad Phase-5 Tasks touch (shell scripts such as `h-mad/scripts/hmad-dispatch.sh` and extensionless launchers such as `h-mad/bin/hmad-dispatch`) under the same test-first gate as Python. This closes row 2856's gate half (skills defect #8). It does so without making any doc/data write (`.md`, `.json` and the rest of the nine suffixes in Terms) need a test, whether a Task lists the file or not (operator ruling R-A, 2026-11-04).

## Terms used in this spec
- **Active chain.** The judge's `read_chain(root, target)` returns `value == "active"` for the target.
- **Listed.** Some canonical name of the target (see FR-3) matches an entry in some Task's `production` list, in the impl-plan of some active record. The match is the judge's existing `resolve` comparison.
- **Exempt.** The target sits under a `tests` or `fixtures` path component, or under the project root's own `docs/` first component, or outside the project root. These are the existing exemption rules of each gate, and this feature does not change them. "Exempt" is a path rule. The suffix rule is the separate term **Doc/data file** below.
- **Non-`.py`.** No canonical name of the target ends in `.py` after `h_mad_target_identity.fold_py_suffix`. This includes the `.pY`/`.Py`/`.PY` folds.
- **Doc/data suffix.** Exactly these nine strings: `.md` `.yaml` `.yml` `.json` `.toml` `.txt` `.rst` `.cfg` `.ini`. They are the first `case` arm of the Claude gate's `ALL_SUFFIX_NAMES` loop in `h-mad/hooks/h-mad-tdd-gate.sh`. That loop's second arm (`*.sh|*.bash|Makefile|Dockerfile|*.dockerignore|*.gitignore`) is **not** part of the set. This spec defines the set here, once. FR-11 requires one code-level definition that all three gates use.
  - *Matching rule.* A name has a doc/data suffix when its basename ends in one of the nine strings, compared ASCII case-insensitively. So `NOTES.MD` and `Config.Json` qualify.
  - *Why case-insensitive.* This is consistent with `fold_py_suffix`, which treats every ASCII case variant of `.py` (`.pY`, `.Py`, `.PY`) as `.py`. The rule is applied to the canonical names from `canonicalise`, never to the spelled path. So for an existing file the on-disk spelling decides, exactly as for `.py`.
  - *End-of-basename, not `Path.suffix`.* This is the semantics of today's bash `*.md` glob. `a.tar.md` qualifies, and so does a dotfile named exactly `.md`, for which `Path.suffix` is empty. `x.md.sh`, `x.mdx` and `x.jsonl` do not qualify.
  - *Change from today.* Today's Claude `case` is case-sensitive (`nocasematch` is off by default). A `NOTES.MD` therefore misses the first arm today and is allowed by the `ALL_NON_PY` allow instead. The visible verdict (ALLOW) is unchanged.
  - *Bash constraint.* `${var,,}` needs bash 4 and is not available. `shopt nocasematch` exists in `/bin/bash` 3.2.57 (measured 2026-11-04: `/bin/bash -c 'shopt nocasematch'` prints `off`). The design names the construct it uses.
- **Doc/data file.** Every canonical name of the target has a doc/data suffix. A doc/data file is allowed on every host, in every state, listed or not. It is never judged and never reaches the listing decision (FR-11). A target that has one doc/data name and one other name (for example two same-directory hard links `x.md` and `x.sh`) is not a doc/data file.
- **Code-like.** A non-`.py` target that is not a doc/data file. That covers `.sh` and `.bash`; extensionless names (`bin/launch`, `./Makefile`, `./Dockerfile`); `.gitignore` and `.dockerignore`; and every suffix outside the nine (for example `.js`, `.bats`, `.jsonl`, `.mdx`).
- **Judgeable non-`.py` target.** Code-like, not exempt, and listed. These are the only non-`.py` targets any gate sends to the judge.
- **Verdicts, per host.** These are the observable forms each hook emits today:
  - Claude (`h-mad/hooks/h-mad-tdd-gate.sh`): ALLOW is exit 0 with no stdout. DENY is a `hookSpecificOutput` JSON object with `permissionDecision: "deny"` and reason `[H-MAD-TDD-GATE] BLOCK kind=<kind>: …`.
  - codex (`h-mad/hooks/h-mad-codex-tdd-gate.py`): ALLOW is exit 0 with no stdout. DENY is the same `hookSpecificOutput` deny object, with `kind=<kind>` in the reason.
  - agy (`h-mad/hooks/h-mad-agy-tdd-gate.py`): `{"decision": "allow"}` or `{"decision": "deny", "reason": "… kind=<kind>"}`.

## Fixture used by the acceptance criteria
The fixture is a scratch git repo `R`. It contains `docs/.bkit-memory.json` holding an active Phase-5 record for feature `f` (`implementer` unset, codex and agy available), and `docs/01-plan/features/f.impl-plan.md` holding:

```markdown
## Task 1: tool
**Task shape**: `new-behaviour`
**Production file**: `scripts/tool.sh`, `bin/launch`, `README.md`, `CHANGES.MD`
**Test file**: `tests/test_tool.py`
```

These files exist: `R/scripts/tool.sh`, `R/bin/launch`, `R/scripts/other.sh`, `R/README.md` and `R/CHANGES.MD`. The last two sit at the root, not under `docs/`, and `CHANGES.MD` is spelled upper-case on disk. `CHANGES.MD` is used instead of a `NOTES.MD` because, on a case-insensitive volume, a `NOTES.MD` would be the same file as the `notes.md` that the controls write. "Test absent" means `R/tests/test_tool.py` does not exist. "Test passing" means it holds one passing pytest test. "Test failing" means it holds one test that fails on an assertion. Each host is driven through its real hook entry point with that host's write payload naming the target.

## Functional Requirements

### FR-1: The task parser records every backticked production path in `production`
- **Description**: `h_mad_wire_pin_gate._parse_tasks` adds every non-`.py` path token on a **Production file** line to `task["production"]`, alongside the `.py` tokens. Today those tokens go to `task["ungated"]`. Non-`.py` tokens are recognised by the existing `_NON_PY_PATH_RE` grammar: a backticked token with no whitespace that contains `/` or `.`. Doc/data tokens are recorded too. The parser does not apply the doc/data rule; the gates apply it (FR-11). `task["tests"]` stays `.py`-only, because the judge runs pytest. This settles Open Question (a) by widening the existing field, not by adding a sibling one. The census in §"Resolved open questions" shows the judge is the only reader of `production`, and the judge is the reader that must see these paths.
- **Acceptance Criteria**:
  - AC-1.1: The input `## Task 1: t` / `**Production files**: `h-mad/scripts/hmad-dispatch.sh`, `h-mad/scripts/a.py`, `h-mad/bin/hmad-dispatch`` parses to a `production` list that contains exactly those three strings.
  - AC-1.2: On a **Production file** line that has no non-`.py` token, `production` is unchanged in both items and order. The existing tests in `h-mad/tests/test_h_mad_parse_tasks_paths.py` (`test_paths_label_spelling`, `test_none_value_contributes_nothing`, `test_none_rule_keeps_a_real_path`, `test_label_lines_accumulate`, `test_existing_fields_unchanged`, `test_corpus_old_fields_unperturbed`) pass unmodified.
  - AC-1.3: A `none` value (the `_NONE_VALUE_RE` rule) still contributes nothing. `**Production file**: none (writes `docs/x/run.sh`)` yields `production == []`.
  - AC-1.4: A non-`.py` token on a **Test file** line contributes nothing. `**Test file**: `h-mad/tests/mutation-specs/x.json`` yields `tests == []`.
  - AC-1.5: `shape`, `wire`, `pin`, `wires`, `pins`, `path_labels`, `runner`, `runner_error` and `judge_budget` are identical for a Task with and without a non-`.py` production token.

### FR-2: Wire-pin 5b no longer reports listed non-`.py` files as `ungated`
- **Description**: Wire-pin 5b currently prints `  ungated: <task> (<name>): `<path>` — not .py, so no TDD judge or wire-pin covers it`. FR-4 through FR-7 make the "no TDD judge" part false for code-like files, so the line is retired, together with the `ungated` key of `check()`'s result and of the task dict. For a listed doc/data file the line's claim stays true (FR-11). This spec records that residual in §"Out-of-Scope". Wire-pin output does not repeat it (operator ruling, call 2). The `WIREPIN:` summary token, its fields and its verdicts (`PASS`, `FAIL`, `UNSHAPED`, `UNREADABLE`) are unchanged. This settles Open Question (b).
- **Acceptance Criteria**:
  - AC-2.1: `python3 h-mad/scripts/h_mad_wire_pin_gate.py <plan>` on a plan whose only Task is `new-behaviour` with **Production file** `h-mad/scripts/x.sh` prints first line `WIREPIN: PASS tasks=1 wiring=0 unpinned=0 mislabeled=0`, and no output line contains `ungated:`.
  - AC-2.2: `check(<that plan>)` returns a dict with no `ungated` key, and `_parse_tasks` returns task dicts with no `ungated` key.
  - AC-2.3: An `UNSHAPED` plan with a non-`.py` production token still returns `verdict == "UNSHAPED"`, with its other keys unchanged.
  - AC-2.4: The guarantees the retired U1 and U2 mutants protected are re-pinned on `production` (FR-1): a `.sh` token is collected and an extensionless token is collected. Every mutant in `h-mad/tests/mutation-specs/wire_pin_ungated.json` is either retired or re-pointed at a test that still exists, and a mutation run over that spec scores no mutant as SURVIVED.

### FR-3: One listing matcher, shared by the judge and all three gates, alias-closed on the target side
- **Description**: Whether a target is listed is decided by exactly one implementation: the impl-plan match inside `h_mad_tdd_judge.resolve`. That match walks each ancestor `base` of the target from its parent up to the root. For each `production` entry it compares `os.path.realpath(base / entry)` with the target's realpath.
  - The codex and agy gates reach it in-process, each through its own existing binding of the module `h_mad_tdd_judge`. Neither binding is on a code-like target's path today, so each gate needs a **new call site** for the listing decision, and the design names both:
    - *codex* (`h-mad/hooks/h-mad-codex-tdd-gate.py`) imports `_load_judge` from `h_mad_target_identity` at module level. In its per-target loop it calls `_load_judge()` only after the guard `if not production: continue`, where `production` holds the names `_is_production_python` accepts. So `_load_judge()` runs on the production-`.py` path only, and a code-like target leaves the loop at that guard before any judge call.
    - *agy* (`h-mad/hooks/h-mad-agy-tdd-gate.py`) never calls `_load_judge`. Inside `main` it prepends the hook's sibling `scripts/` directory to `sys.path` and binds `import h_mad_tdd_judge as judge`. Its T6–T7 loop calls `judge.read_chain` and `judge.judge` through that binding, again only after its own `if not production: continue` guard.
    - Both bindings load `h_mad_tdd_judge` from the same directory, `h-mad/scripts/` beside the hook (`_load_judge` resolves `Path(__file__).resolve().parents[1] / "scripts"` from `h_mad_target_identity.py`, and the agy gate resolves the same expression from `hooks/`). The new call site may use the host's existing binding or a new `_load_judge()` call; either way it reaches the one matcher.
    - The listing decision needs the active records, so on codex and agy the new call site reads the chain (`read_chain`) **before** it decides listing. FR-6 states the order.
  - The Claude gate reaches it through a judge CLI verb or flag. Its output is one line with an enumerated set of values: one for listed, one for not listed, and one for unreadable. The design must name every value.
  - The Claude gate refuses with `kind=judge-error` on zero lines, several lines, a non-zero exit or an unrecognised value, as it does for the `state` and `judge` verbs today.
  - No gate re-implements the match.
  - A gate asks for the listing decision only for a code-like target that is not exempt. A doc/data target is allowed before the decision is reached (FR-11).

  Alias spellings are closed by evaluating the predicate over the target's canonical names from `h_mad_target_identity.canonicalise`, never over the spelled path. `canonicalise` follows symlinks to the referent. For an existing file it returns the on-disk spelling, so a case-variant spelling folds. Its `names` holds every same-directory hard link. The target is listed if any of those names is listed.
- **Acceptance Criteria**:
  - AC-3.1: The codex gate, the agy gate and the Claude gate's CLI path all call the same function for the listing decision, each through the binding FR-3 names for it. A mutation that makes that function always return "not listed" turns AC-5.1, AC-6.1 and AC-7.1 from DENY to ALLOW on all three hosts. Each host has its own failing test, run with that host alone.
    That mutation is callee-scoped. Each host's **connection** to the matcher is also mutated alone, in both directions (base invariant §"Connection enforcement" in `h-mad/invariants.base.md`), with the matcher left intact. These are six mutants, two per host (Claude, codex, agy), each run with that host alone:
    - (a) *Remove.* The host's new listing call is removed, so the host treats the target as not listed without calling the matcher. The host's listed-DENY test fails: AC-5.1 (Claude), AC-6.1 (codex), AC-7.1 (agy) turns from DENY to ALLOW.
    - (b) *Force.* The host's connection reports "listed" unconditionally, without consulting the matcher's result. The host's unlisted control fails: the `scripts/other.sh` write of AC-5.4 (Claude), AC-6.3 (codex), AC-7.3 (agy) turns from ALLOW to a DENY.

    Before a mutant's result counts, the run verifies the mutation landed (base invariant §"Mutation verification"): the mutated file differs from the unmutated one at the connection site. A mutant whose landing is not verified scores neither killed nor survived. These six mutants are the connection entries AC-9.3 requires for FR-3.
  - AC-3.2 (symlink): `R/link.sh` is a symlink to `R/scripts/tool.sh`. With the test absent, a write to `link.sh` is DENY `kind=test-missing` on each host.
  - AC-3.3 (case fold, existing file, case-insensitive volume): with the test absent, a write spelled `scripts/TOOL.SH` is DENY `kind=test-missing` on each host.
  - AC-3.4 (hard link, same directory): `R/scripts/hard.sh` is a hard link to `R/scripts/tool.sh`. With the test absent, a write to `scripts/hard.sh` is DENY `kind=test-missing` on each host. The judge receives a listed name, so its resolution source is `impl-plan` and never `name-map`.
  - AC-3.5 (residual, stated, not closed): the spec names the three spellings below as known ALLOW, so no gate is expected to deny them. A test pins each one as ALLOW so that a later change to it is visible:
    1. An impl-plan entry whose case differs from the on-disk name. `resolve` realpaths the plan entry, and realpath does not fold case on macOS. Measured with `os.path.realpath` and `canonicalise` on APFS at `0cb7b9b0`: the realpath keeps `HMAD-Dispatch.SH` while `canonicalise` returns `hmad-dispatch.sh`.
    2. A not-yet-existing target spelled in a case that differs from the plan entry. For an absent leaf, `canonicalise` returns the spelled basename (`New.SH` stays `New.SH`).
    3. A hard link in a different directory. `Identity.names` lists same-directory names only.

    All three are residuals of today's `.py` path too, where the name-map fallback may still catch them. For non-`.py` there is no fallback.

### FR-4: The judge judges a listed non-`.py` target by its Task's tests only
- **Description**: `h_mad_tdd_judge.judge` handles a listed non-`.py` target the way it handles a listed `.py` one. Resolution source is `impl-plan`. Candidates are the matched Task's `tests` entries, newest first. The verdict is `ALLOW kind=red-measured` on the first failing test, and the Task's **Judge budget** applies. The judge does not apply the doc/data rule: it judges whatever it is given, and the gates never give it a doc/data target (FR-11). Two Python-only shortcuts are disabled for a non-`.py` target. The first is the name-map fallback (`h_mad_derive_test_path.sh`), which the judge must never reach for a listed target. The second is the import-failure RED shortcut, `score`'s `M:K-IMPORT-RED` arm: `target_module_names` returns an empty set for a non-`.py` target, because writing a shell script never fixes a Python `ModuleNotFoundError`. This settles Open Question (c).
- **Acceptance Criteria**:
  - AC-4.1: The fixture is used with test failing on an assertion. `judge(R, R/scripts/tool.sh, records)` returns `Verdict("ALLOW", "red-measured", …)` with source `impl-plan` and test `R/tests/test_tool.py`.
  - AC-4.2: Same with the test passing: `DENY kind=test-passing`.
  - AC-4.3: Same with the test absent: `DENY kind=test-missing`. The reason names `tests/test_tool.py`.
  - AC-4.4: The Task's **Test file** is `tests/tool.bats`, so `tests` is empty. The verdict is `DENY kind=test-missing`. A listed code-like file whose Task names no pytest file can never be written while Phase 5 is active.
  - AC-4.5: `target_module_names(R, R/scripts/tool.sh)` and `target_module_names(R, R/bin/launch)` return `frozenset()`. A failing test whose only `E` line is `E   ModuleNotFoundError: No module named 'tool'`, run against the absent target `R/scripts/tool.sh`, scores `pytest-error`, never `red-measured`. A `.py` target keeps today's behaviour, and the existing `M:K-IMPORT-*` tests pass unmodified.
  - AC-4.6: For an unlisted non-`.py` target, `judge` still returns `DENY kind=no-test-resolved`, because `h_mad_derive_test_path.sh` prints nothing for a non-`.py` path. The gates never route an unlisted target to `judge` (FR-5 to FR-7). This AC pins the fail-closed backstop.

### FR-5: Claude gate — the non-`.py` early allows become "allow doc/data, and allow code-like unless listed"
- **Description**: In `h-mad/hooks/h-mad-tdd-gate.sh`, everything before the `ALL_SUFFIX_NAMES` and `ALL_NON_PY` early allows stays in order and unchanged: the canonicalisation, the unresolvable arm, `_chain_may_hold_state`, the `.py` test-name allow, and the `tests`/`fixtures`/root-`docs/`/scratch exemptions.
  - The `ALL_SUFFIX_NAMES` early allow narrows to doc/data files: its first arm, matched by the Terms rule (case-insensitive). Its second arm (`.sh`, `.bash`, `Makefile`, `Dockerfile`, `.dockerignore`, `.gitignore`) no longer allows.
  - The doc/data allow stays before any state read, so it starts no process.
  - The `ALL_NON_PY` early allow no longer allows a listed target.
  - A code-like target that reaches it goes through four steps in order:
    1. Read state. `TDD-STATE: none` means ALLOW.
    2. Decide listing through FR-3. Not listed means ALLOW.
    3. A listed target passes through the existing implementer, peer-authorship and fallback refusals unchanged.
    4. Call the judge with the **selected listed name** (FR-6, *Selection rule*) as `--target`.
  - The `.py` path is unchanged.
- **Acceptance Criteria**:
  - AC-5.1: With the test absent, a Claude `Write` to `R/scripts/tool.sh` (with `implementer=null` so Claude is the author) is DENY `kind=test-missing`.
  - AC-5.2: Same with the test passing: DENY `kind=test-passing`. Same with the test failing: ALLOW.
  - AC-5.3: A Claude `Write` to `R/bin/launch` with the test absent is DENY `kind=test-missing`. An extensionless listed file is judged.
  - AC-5.4 (controls): a Claude `Write` to the unlisted code-like `R/scripts/other.sh` is ALLOW, in the same state as AC-5.1. This is the unlisted control. A Claude `Write` to the unlisted `R/notes.md` is also ALLOW. This is the doc/data control, and it holds by FR-11 whether or not the file is listed.
  - AC-5.5: With the default implementer (codex resolves), a Claude `Write` to `R/scripts/tool.sh` is DENY `kind=codex-authorship`. A Claude `Write` to the unlisted `R/notes.md` in that state is ALLOW, as today.
  - AC-5.6: Without `docs/.bkit-memory.json`, or with a record that is not active, a Claude `Write` to `R/scripts/tool.sh` is ALLOW.
  - AC-5.7: A listed `R/tests/helper.sh` (listed as `tests/helper.sh`) is ALLOW, by the existing `_dir_match` exemption.
  - AC-5.8 (selection observed): in the FR-6 selection fixture, a Claude `Write` to `R/scripts/tool.sh` is ALLOW in state S1 and DENY `kind=test-missing` in state S2 (AC-6.5 defines both).

### FR-6: codex gate — judge a listed code-like target
- **Description**: In `h-mad/hooks/h-mad-codex-tdd-gate.py`'s per-target loop, a doc/data target is skipped first (FR-11), before any listing decision or `read_chain`. For any other target, a name qualifies when either of two things is true:
  - `_is_production_python(relative)` is true; or
  - the target is code-like, the name's `relative` path is not exempt, and the name is listed per FR-3.

  The order, for a target that is not a doc/data file:
  1. If any name is production Python, the existing path runs unchanged: `min(production)` over the `.py` names, `_load_judge()`, `read_chain`, `judge`, deny.
  2. Otherwise, if no name is code-like and non-exempt, the target is skipped as today.
  3. Otherwise the new call site (FR-3) calls `read_chain(root, <target>)`. `unreadable` is DENY `kind=judge-error` (FR-8). A value other than `active` skips the target, as today.
  4. With `active`, the listing decision (FR-3) runs over the code-like, non-exempt names, with the chain's records. An unreadable impl-plan is DENY `kind=judge-error` (FR-8). No listed name skips the target.
  5. Otherwise `judge(root, <selected listed name>, records)` runs, and any verdict other than ALLOW is denied through the existing deny form.

  *Selection rule* (all three hosts): when several canonical names qualify, the judged name is the least one in Python `str` ordering of the basename. `canonicalise` returns `names` sorted, so this is also the first qualifying name in `names` order. It is the same name `min(production)` picks among `.py` names today, because those tuples begin with the name. The Claude gate's `--target` (FR-5 step 4) and agy's judged name (FR-7) follow this rule. Two qualifying names can resolve to different Tasks (same-directory hard links listed in different Tasks), so the choice can change the verdict; AC-5.8, AC-6.5 and AC-7.4 observe it.
- **Acceptance Criteria**:
  - AC-6.1: With the test absent, a codex `apply_patch` with header `*** Update File: scripts/tool.sh` is DENY with `kind=test-missing` in the reason.
  - AC-6.2: Same with the test passing: DENY `kind=test-passing`. Same with the test failing: ALLOW.
  - AC-6.3 (controls): in the AC-6.1 state, `*** Update File: scripts/other.sh` is ALLOW (unlisted control) and `*** Add File: notes.md` is ALLOW (doc/data control).
  - AC-6.4: A patch touching both `scripts/other.sh` and `scripts/tool.sh` is DENY when the test is absent. One listed target in a multi-target patch is enough.
  - AC-6.5 (selection observed): the *selection fixture* is the fixture plus `R/scripts/hard.sh` as a hard link to `R/scripts/tool.sh`, and a second Task, `## Task 2: hard`, with **Task shape** `new-behaviour`, **Production file** `scripts/hard.sh` and **Test file** `tests/test_hard.py`. Both names are listed, by different Tasks, and `hard.sh` is the least. State S1: `tests/test_tool.py` absent, `tests/test_hard.py` failing. State S2: `tests/test_hard.py` absent, `tests/test_tool.py` failing. `*** Update File: scripts/tool.sh` is ALLOW in S1 and DENY `kind=test-missing` in S2. Judging `tool.sh` instead inverts both results, and an "allow if any listed name allows" rule turns S2 to ALLOW, so each wrong rule fails one state.

### FR-7: agy gate — judge a listed code-like target
- **Description**: `h-mad/hooks/h-mad-agy-tdd-gate.py` follows FR-6's order and *Selection rule*, doc/data skip included, in its write-class (T6–T7) loop, with its deny in agy's `{"decision": "deny", …}` form. Its new call site uses the `judge` binding FR-3 names for agy, or a new `_load_judge()` call. The existing T1–T5 checks run first and are unchanged: unresolvable, directory, outside-root, and the allowance file.
- **Acceptance Criteria**:
  - AC-7.1: With the test absent, an agy write call targeting `scripts/tool.sh` produces `{"decision": "deny", …}` with a reason ending `kind=test-missing`.
  - AC-7.2: Same with the test passing: deny `kind=test-passing`. Same with the test failing: `{"decision": "allow"}`.
  - AC-7.3 (controls): agy writes to `scripts/other.sh` (unlisted control) and `notes.md` (doc/data control) produce `{"decision": "allow"}`.
  - AC-7.4 (selection observed): in the AC-6.5 selection fixture, an agy write targeting `scripts/tool.sh` produces `{"decision": "allow"}` in S1 and a deny ending `kind=test-missing` in S2.

### FR-8: An undecidable listing fails closed
- **Description**: In some states, listing cannot be decided for a code-like, non-exempt target. Each gate then denies with `kind=judge-error` instead of allowing. The cases:
  - The chain is unreadable: `read_chain` returns `unreadable`, or the Claude gate's state line matches `STATE_UNREADABLE_RE`.
  - An active record's impl-plan exists but raises `OSError` or `UnicodeDecodeError` on read.

  An absent impl-plan, where `resolve` notes `absent`, is "not listed", so the write is ALLOW. A doc/data target is ALLOW in every one of these states: it never reaches the listing decision (FR-11), so its listing is never undecidable. This tightens today's behaviour for unlisted code-like files in exactly these states, and nowhere else. See §"Assumptions".
- **Acceptance Criteria**:
  - AC-8.1: `R/docs/01-plan/features/f.impl-plan.md` is replaced by a file with invalid UTF-8. A write to the unlisted code-like `R/scripts/other.sh` is DENY `kind=judge-error` on each host.
  - AC-8.2: `R/docs/.bkit-memory.json` is made unparsable. A write to `R/scripts/other.sh` is DENY `kind=judge-error` on each host.
  - AC-8.3: The record is active and `f.impl-plan.md` is absent. A write to `R/scripts/other.sh` is ALLOW on each host.
  - AC-8.4 (doc/data in the undecidable states): in the AC-8.1 state and again in the AC-8.2 state, a write to the unlisted `R/notes.md` and a write to `R/README.md` are ALLOW on each host. `R/README.md` is listed in the fixture, but in the AC-8.1 state that listing cannot be read.

### FR-9: End-to-end proof on every host, with a control
- **Description**: The feature is demonstrated by driving each host's real hook entry point, fed that host's real stdin payload, against scratch repos built to the fixture above. Each host is run on its own, so a healthy host cannot cover a sick one. Every DENY row has a paired control that runs the same write to an unlisted `.sh` in the same state.

  The proof follows the `verify-hmad-gates` skill's **method** (operator ruling R-B, 2026-11-04): every hook runs under a hermetic `env -i` environment, through its real stdin entry point, and every call is recorded in an evidence folder. The proof drives the **worktree's** hook files by explicit path.

  The skill's helper, `bin/hmad-verify.sh`, is not the instrument, for three reasons:
  - Its `AGY_GATE=` and `CODEX_GATE=` assignments are fixed to the installed paths `$HOME/.gemini/config/skills/h-mad/hooks/…` and `$HOME/.agents/skills/h-mad/hooks/…`, and no override variable exists.
  - Its usage header (the `#   hmad-verify.sh` comment lines) lists no Claude drive. Of its drive verbs it offers only `agy`, `codex` and `dispatch`.
  - Those installed paths resolve to another checkout (plan §"Measurements" M7). A reading taken through the helper would measure a hook that is not under test.

  The design names the driving mechanism.

  **Incident replay** (base invariant §"Incident replay" in `h-mad/invariants.base.md`: synthetic cases alone are a violation when the real motivating artifacts are reachable). The fixture above is synthetic. The real artifacts are reachable: tracked impl-plans whose Task lists the motivating dispatcher `h-mad/scripts/hmad-dispatch.sh` on its **Production file(s)** line. Located at `e4979ecd` with `git grep -n -E '^\*\*Production files?\*\*:.*hmad-dispatch\.sh' -- '*.impl-plan.md'`: 41 matching lines in 17 files (4 lines in 3 files outside `docs/archive/`). The replay uses **Task 1 (`exec-empty-output-recovery`) of `docs/01-plan/features/exec-missing-report-recovery.impl-plan.md`**, chosen because its one Production line carries both the motivating code-like target and a doc file:

  ```markdown
  **Production files**: `h-mad/scripts/hmad-dispatch.sh` (function `_cmd_exec`) and `h-mad/SKILL.md` (exec-dispatch docs — FR-6)
  **Test file**: `h-mad/tests/test_hmad_dispatch_exec.py`
  ```

  The Task has no **Task shape** line; `resolve` does not read the shape. At `e4979ecd`, `_parse_tasks` on that file gives this Task `production == []` and `ungated == ['h-mad/scripts/hmad-dispatch.sh', 'h-mad/SKILL.md']`; the backticked `_cmd_exec` holds neither `/` nor `.`, so `_NON_PY_PATH_RE` does not collect it. The replay repo holds that impl-plan **byte-for-byte** from the tracked blob, under its own name, with an active Phase-5 record whose key is `exec-missing-report-recovery` and whose authorship settings match AC-9.1's per-host rows. The files `h-mad/scripts/hmad-dispatch.sh`, `h-mad/SKILL.md` and the unlisted control `h-mad/scripts/h_mad_derive_test_path.sh` (a real tracked script that no Task of that plan lists) exist; their content is irrelevant to the verdict. Each spelling is the real one. "Before" drives the hooks as of the feature branch's base commit (`git merge-base HEAD origin/main`, `5cc9e270` at `a469d565`, re-derived at the commit under test because it moves whenever `origin/main` advances and the branch rebases), with every file under `h-mad/` taken from that commit, because each hook loads its siblings from `h-mad/scripts/`. The base is never derived from the local `main` ref. Local `main` is not an older copy of `origin/main`: it has **diverged** from it, because other lanes commit to the shared ref store and move local `main` independently of `origin/main` (check: `git merge-base --is-ancestor main origin/main` fails, and so does the reverse). The divergence moves with every such commit, so no count of it is stated here. At `bde62a42`, `git merge-base HEAD main` gives `d655d8cb`, an ancestor of `5cc9e270`. The before readings do not depend on which of the two is used. The proof is `git diff --name-only d655d8cb 5cc9e270 -- h-mad`: at `bde62a42` it lists `h-mad/references/helper-scripts.md`, `h-mad/scripts/h_mad_failure_diff.py`, `h-mad/scripts/h_mad_mutation_harness.py`, two files under `h-mad/tests/mutation-specs/` and two test files, and none of the gates' import closure: no file under `h-mad/hooks/`, and none of `h_mad_tdd_judge.py`, `h_mad_wire_pin_gate.py`, `h_mad_target_identity.py`, `h_mad_audit_gate.py` (imported by the judge and by the wire registry) or `h_mad_wire_registry.py` (imported by `h_mad_wire_pin_gate`). A four-path diff over the hooks, the judge, the wire-pin gate and target identity alone is not this proof, because it omits the last two modules. Residual: `h_mad_target_identity.py` names `h_mad_mutation_harness.py` only as a string in its safe-command table and does not import it, and no AC-9.4 row writes through a shell command. "After" drives the worktree's hooks at the commit under test.
- **Acceptance Criteria**:
  - AC-9.1: For each of Claude, codex and agy, the run records these verdicts:
    - listed `scripts/tool.sh` with the test absent: DENY `test-missing`;
    - the same with the test failing: ALLOW;
    - the unlisted `scripts/other.sh` in the test-absent state: ALLOW.
  - AC-9.2: Each host's run records which hook file it executed, by path and sha256 at the commit under test, so the reading cannot have come from the live `~/.claude/skills/h-mad` symlink or from the helper's installed paths, which point at a different checkout.
  - AC-9.3: Every new guard in FR-1, FR-3 to FR-8 and FR-11 has a mutation-spec entry. Each mutant is killed by a test that fails for the guard's own reason. Results are scored on the pytest summary, not on `$?`.
  - AC-9.4 (incident replay, real Task): for each of Claude, codex and agy, run on its own, the replay records these verdicts, each in the host's own verdict form:

    | Write target (real spelling) | Test `h-mad/tests/test_hmad_dispatch_exec.py` | Before (base commit) | After (commit under test) |
    |---|---|---|---|
    | `h-mad/scripts/hmad-dispatch.sh` (listed, code-like) | absent | ALLOW | DENY `kind=test-missing` |
    | `h-mad/scripts/hmad-dispatch.sh` | failing on an assertion | ALLOW | ALLOW |
    | `h-mad/scripts/h_mad_derive_test_path.sh` (unlisted control) | absent | ALLOW | ALLOW |
    | `h-mad/SKILL.md` (listed doc/data, FR-11) | absent | ALLOW | ALLOW |

    The first row's before/after pair is the incident: the base gates let the motivating dispatcher be written with no RED, and the shipped gates refuse it. The before readings follow from code at the base commit (the Claude gate's `ALL_SUFFIX_NAMES` second arm admits `*.sh`; the codex and agy loops `continue` at `if not production`); the replay must observe them, not assume them. A before reading other than ALLOW is a finding against this spec's premise, never a pass.
  - AC-9.5 (replay provenance): the replay records the impl-plan's source commit and blob sha (`git rev-parse <commit>:docs/01-plan/features/exec-missing-report-recovery.impl-plan.md`; `fef08298…` at `e4979ecd`) and the sha256 of the copy it fed the hooks, and they agree. It records the base commit's sha, derived with `git merge-base HEAD origin/main` at the commit under test, and, per host and per side, the hook file's path and sha256 as AC-9.2 does. A replay whose Task text was retyped, trimmed or re-spelled does not satisfy AC-9.4.

### FR-10: The prose that states which files the gates judge states the shipped rule
- **Description**: Every h-mad prose surface that states which files the Phase-5 write gates judge, or whose writes the Claude-side authorship refusals cover, is updated to the rule this spec ships (operator ruling R-C, 2026-11-04). The rule has five parts:
  - `.py` production code is judged.
  - Code-like non-`.py` files are judged when a Task's **Production file** line lists them.
  - Doc/data files (the nine suffixes in Terms) are allowed, listed or not.
  - Unlisted code-like files are allowed.
  - The Claude-side authorship refusals (implementer, peer-authorship, fallback) cover Claude's write to a listed code-like file exactly as they cover its production `.py` write (FR-5 step 3).

  The floor of surfaces was first taken from plan §"Measurements" M6 and is re-derived here at `e4979ecd` with the AC-10.1 phrasing set (five branches). It is four surfaces in three files:
  1. In `h-mad/references/codex-implementer-prompt.md`, the bullets under its single `Hook: ` line. Their doc/data bullet names six of the nine suffixes, as words ("markdown / yaml / json / toml / txt / rst"). Their production bullet defines production code as "a `.py` suffix in any case".
  2. In `h-mad/references/codex-runtime.md`, §"Trust boundary", whose first sentence says the hook prevents "production-Python writes".
  3. In `h-mad/references/phase5-substeps.md`, the gate-scope paragraph that opens `Test files, docs, config, and shell are never gated; only production `.py`.` This states the old rule in full: it says shell is never gated. `doc_text(SKILL)` restores this file into `SKILL.md`'s text (it is in `h_mad_skill_corpus.SPLIT_REFERENCES`), so it is the `SKILL.md` statement of the rule.
  4. In `h-mad/references/phase5-substeps.md`, the bullet that opens `- **FR-3 — Claude-side authorship.**`, which says the first resolved peer "refuses Claude's production-`.py` write". After FR-5 step 3 the same refusals also cover Claude's write to a listed code-like target, so the bullet states the old scope.

  This floor is not a closure. The design re-runs the sweep with a wider phrasing set and names every surface it adds.

  **Regression provenance for surface 3** (base invariant §"Regression provenance" in `h-mad/invariants.base.md`). `h-mad/tests/test_h_mad_tdd_gate_docs.py::test_skill_states_the_docs_first_component_rule` pins surface 3 verbatim: `anchor = "Test files, docs, config, and shell are never gated; only production `.py`."`, asserted to occur exactly once in `doc_text(SKILL)`. The test then asserts five tokens in the paragraph after the anchor: `FIRST component`, `relative to the project root`, `` `docs` ``, `` `src/docs/foo.py` `` and `Both gates`. The test therefore asserts three different things:
  - The **anchor** asserts the rule this feature changes ("shell … never gated; only production `.py`"). It is a stale contract, not a regression: rewriting surface 3 makes it fail, and the change updates the anchor to the new gate-scope sentence in the same Task that rewrites surface 3.
  - The **first four tokens** (`FIRST component`, `relative to the project root`, `` `docs` ``, `` `src/docs/foo.py` ``) assert the root-`docs/` first-component exemption, which this feature does not change (Terms, *Exempt*). They are current behaviour. The updated test still asserts these four, unchanged, in the paragraph after the new anchor, and still asserts the new anchor occurs exactly once.
  - The **fifth token**, `Both gates`, is a stale contract, not current behaviour. Three gates apply the docs-first rule today: the codex gate and the agy gate both import `_is_production_python` from `h_mad_target_identity` (whose `docs` first-component check carries the marker `# M:G-DOCS`), and the Claude gate holds its bash copy (`# M:H-DOCS`). The test asserted a two-gate statement as correct. The change replaces this token with `All three gates`, both in the test and in surface 3's sentence that carries it, in the same Task that rewrites surface 3.

  Locators and their residual:
  - Surface 1 is the one line that starts `Hook: ` plus the `- ` bullets that follow it. `_hook_block` in `h-mad/tests/test_h_mad_tdd_gate_docs.py` asserts there is exactly one such line (`M:D1`), so a rename fails loudly.
  - Surface 2 is found by its `### Trust boundary` heading, which `test_locators_fail_loudly` guards.
  - Surface 3 is found by the test's anchor sentence, today's and then the updated one. The count-is-one assertion fails loudly if the sentence is reworded without the test.
  - Surface 4 is found by its bold lead `**FR-3 — Claude-side authorship.**` under the heading `### Codex authors Phase 5 — enforced, not just instructed`. No test pins it, so a rename is silent; AC-10.1's `production-.\.py.` branch is its only net.
  - Not caught by this FR: a rule statement outside all four locators that uses none of the swept phrases, and a swept phrase split across a hard line wrap, which a line-oriented `git grep` cannot see. At `e4979ecd` a newline-collapsed run of the same five-branch regex over the same corpus (`git ls-files` of the four pathspecs, whitespace runs folded to one space) finds 5 occurrences, the same 5 the line grep finds, so no wrapped instance exists there. The design's widened sweep is the only net for the first category.
- **Acceptance Criteria**:
  - AC-10.1: `git grep -n -E 'production-Python|a .\.py. suffix in any case|never gated|only production|production-.\.py.' -- h-mad/SKILL.md h-mad/references h-mad/agents h-mad/invariants.base.md` prints no line. Control, run at `e4979ecd`: the same command prints 4 matching lines in 3 files, holding 5 occurrences. Each branch, run alone, has its own pre-change hit: `production-Python` → `codex-runtime.md` (surface 2); `a .\.py. suffix in any case` → `codex-implementer-prompt.md` (surface 1); `never gated` and `only production` → the same line of `phase5-substeps.md` (surface 3); `production-.\.py.` → `phase5-substeps.md` (surface 4). The shipped prose therefore may not use any of these five phrasings. The design may add branches. Each branch it adds needs its own pre-change hit, or a stated reason why it has none.
  - AC-10.2: `h-mad/tests/test_h_mad_tdd_gate_docs.py::test_hook_bullets_state_the_shipped_rule` keeps today's tokens and also asserts that the Hook bullets contain each of the nine doc/data suffix spellings, the phrase `Production file`, and `.sh`. Run against the `e4979ecd` bullets, the test fails on a missing token. Measured there: each of those eleven tokens matches 0 lines of the bullet block. The whole `test_h_mad_tdd_gate_docs.py` module passes after the change.
  - AC-10.3: `test_skill_states_the_docs_first_component_rule` is updated as the regression-provenance paragraph above states. Its new anchor is a sentence of surface 3 that states the shipped rule and contains the phrase `Production file` and `.sh`. It asserts that anchor occurs exactly once in `doc_text(SKILL)`, and asserts five tokens in the paragraph after it: the four docs-first tokens `FIRST component`, `relative to the project root`, `` `docs` `` and `` `src/docs/foo.py` ``, unchanged, and `All three gates` in place of `Both gates`. It no longer asserts `Both gates`. Run against the `e4979ecd` text, the updated test fails on the anchor count (0). After the change it passes.

### FR-11: Doc/data files are allowed on every host, even when listed
- **Description**: A doc/data file (Terms) is allowed by all three gates, in every Phase-5 state, whether or not a Task lists it (operator ruling R-A, 2026-11-04).
  - **Where the rule is applied.** The gates apply it, identically, before any listing decision. The judge and the parser do not apply it (FR-1, FR-4).
  - **One definition in code.** The nine suffixes and the matching rule are defined once, in a constant and predicate that the codex and agy gates import. The Claude gate either uses that same definition or holds a copy that a test pins equal to it. The design chooses which and names it.
  - **Mixed targets.** The rule is over *every* canonical name. A target with any code-like name is judged by FR-5 to FR-7.
  - **Ordering.** In the Claude gate the check stays where `ALL_SUFFIX_NAMES` is today, after the path exemptions and before any state read. In the codex and agy gates it precedes the per-name qualification and `read_chain`.

  **Residual, stated exactly:** a listed doc/data file is never judged. So a Task whose **Production file** is, for example, `h-mad/SKILL.md` or a `.json` mutation spec can be written in Phase 5 with no failing test. The reason is reach. Plan §"Measurements" M5 (reproduced at `a7bfcbe0`) counts 128 non-exempt non-`.py` token occurrences on Production lines across 29 tracked `*.impl-plan.md` files: `.md` 74, `.sh` 47, `.json` 5, extensionless 1, `.ini` 1. Of these, 80 are doc/data and are left unjudged by this rule. The other 48 (`.sh` and extensionless) are judgeable.
- **Acceptance Criteria**:
  - AC-11.1 (listed, outside `docs/`): with the test absent, a write to the listed `R/README.md` is ALLOW on each host. The control in the same state is a write to the listed `R/scripts/tool.sh`, which is DENY `kind=test-missing` (AC-5.1, AC-6.1, AC-7.1).
  - AC-11.2 (case variant): with the test absent, a write to the listed `R/CHANGES.MD` (upper-case on disk) is ALLOW on each host. A write spelled `R/changes.md` to that same file is ALLOW too. On a case-insensitive volume `canonicalise` returns the on-disk `CHANGES.MD`.
  - AC-11.3 (each member, alone): for each of the nine doc/data suffixes `S`, a fixture variant lists `x<S>` and `y<upper(S)>` at the root, and both files exist. With the test absent, a write to each is ALLOW on each host. Each suffix is its own test case, so a matcher that drops one suffix fails that suffix's case alone.
  - AC-11.4 (each excluded member, alone): with the test absent, each of the following is DENY `kind=test-missing` on each host:
    - listed `scripts/a.bash`;
    - listed `./Makefile`;
    - listed `./Dockerfile`;
    - listed `.gitignore`;
    - listed `.dockerignore`;
    - listed `x.md.sh`;
    - listed `x.mdx`.

    These are the second-arm members of today's `ALL_SUFFIX_NAMES` (`.sh` itself is covered by AC-5.1, AC-6.1 and AC-7.1) and two near-miss suffixes. Each is its own test case.
  - AC-11.5 (mixed names): `R/x.md` and `R/x.sh` are same-directory hard links, and `x.sh` is listed. With the test absent, a write to `x.md` is DENY `kind=test-missing` on each host.
  - AC-11.6 (single definition): a mutation that removes one suffix from the shared definition turns that suffix's AC-11.3 case from ALLOW to DENY on all three hosts. If the Claude gate holds a pinned copy, a mutation of the copy alone fails the equality test.

## Non-Functional Requirements
- **Performance.** A doc/data write starts no new process on the Claude gate in any state, because its allow precedes the state read (FR-11). An unlisted code-like write whose ancestor chain holds no `docs/.bkit-memory.json` starts no new process either, because `_chain_may_hold_state` keeps its early allow. Where state exists, the Claude gate starts at most three extra short Python processes for an unlisted code-like write: the judge-path derivation (`_find_judge`'s `python3 -c` launch, marker `# M:W6`, which every state-reading path in `h-mad/hooks/h-mad-tdd-gate.sh` runs before `_read_state`), the state read, and the listing decision. The design may reduce this count, for example by deriving the judge path without Python or by merging the state read and the listing decision into one process, and names the count it ships. The pytest run is paid by listed code-like targets only.
- **Security.** There is no new allow path. Every change either turns an ALLOW into a judged decision or keeps it. Doc/data files are allowed today by `ALL_SUFFIX_NAMES` or `ALL_NON_PY` on the Claude gate, and by the non-`.py` skip on the codex and agy gates, so FR-11 keeps an existing allow. FR-8 states every case that turns an existing ALLOW into a DENY.
- **Compatibility.** The Claude gate stays runnable under macOS `/bin/bash` 3.2 (the shebang is `#!/bin/bash`). This rules out `${var,,}` for the case-insensitive match. `WIREPIN:`, `TDD-JUDGE:` and `TDD-STATE:` keep their current shapes and value sets. The `.py` behaviour of all three gates and of `judge` is byte-identical on every existing test.

## Resolved open questions (measured at `0cb7b9b0`, from PROJECT_ROOT)

**(a) Consumers of `_parse_tasks`, and what each does with a non-`.py` path.**

Commands:
- `graft callers _parse_tasks --depth all`
- `git grep -n "_parse_tasks" -- ':!docs/archive'`
- `git grep -n '"production"' -- h-mad/`

Results:
- `_parse_tasks` has 5 production call sites in 4 files, one per consumer bullet (the next five). Both commands agree.
- `h_mad_assemble_tdd.assemble` reads `id`, `shape`, `wire` and `pin` only, so a non-`.py` path changes nothing.
- `h_mad_wire_pin_gate.check` reads `shape`, `wires`, `pins`, `path_labels` and (today) `ungated`, never `production`, so nothing changes except FR-2.
- `h_mad_wire_pin_gate.main` (registration, `_register_wiring_tasks`) reads `id`, `name`, `shape`, `wires`, `pins`, `runner` and `runner_error`, so nothing changes.
- `h_mad_wire_registry.challenge` takes `tasks` but builds its claims with its own `_production_claims` line regex. That regex already sees non-`.py` values. It reads only `*.py` diffs (`changed_files` passes `-- '*.py'` to git), so nothing changes.
- `h_mad_tdd_judge.resolve` is the only reader of `task["production"]` among scripts. It gains the non-`.py` entries, which is the intended change.
- The other hits are tests (`test_h_mad_parse_tasks_paths.py`, `test_h_mad_tdd_judge.py`) and one archived probe under `docs/archive/`, which no gate executes.
- The reason this zero (no other reader) holds is load-bearing: `production` was introduced as the judge's map (comment at `_NON_PY_PATH_RE`). A future consumer that assumes `.py` must filter for itself.

**(b) `ungated:`.** FR-2: retired. `git grep -n -e "no TDD judge" -e "ungated:" -- h-mad ':!h-mad/tests'` finds the wording only in `h_mad_wire_pin_gate.py`, in the task-dict comment and the `main` print. No reference or SKILL.md surface restates it. The tests that pin it are `test_h_mad_wire_pin_gate.py`'s six `…ungated…` functions (counted with `grep -c`: 6 function definitions, one of them parametrised three ways) and the 5 mutants in `wire_pin_ungated.json` (U1 to U5, counted from its `mutations` array).

**(c) Test-path derivation from the filename.** `h_mad_derive_test_path.sh` prints nothing for any path that is not `*.py`, through its explicit non-`.py` early exit. The judge reaches it only when no impl-plan Task matched. The judge also derives `target_module_names` from the filename, by stripping any suffix, so `scripts/tool.sh` yields `{"scripts.tool", "tool"}` and `bin/launch` yields `{"bin.launch", "launch"}` today (run at `0cb7b9b0`). That is the one suffix-blind derivation, and FR-4 / AC-4.5 close it.

**(d) Every suffix filter on the write path.** Census: `git grep -n -e _is_production_python -e fold_py_suffix -e PY_SUFFIXES -- h-mad`, plus a read of each gate's decision loop.
- Judge: verbs `state` and `implementer` do not filter by suffix. Verb `judge` adds the name-map `*.py` filter and `target_module_names`.
- Identity: `PY_SUFFIXES` / `fold_py_suffix`, and `_is_production_python`, which is false for any non-`.py` suffix.
- Claude gate: `_fold_py`, the `.py` test-name allow (`ALL_TEST_NAMES`), `ALL_SUFFIX_NAMES`, `ALL_NON_PY` and the `PRODUCTION_TARGET` selection.
- codex gate: `_tmp_report_target`, where a `.py` under `/tmp` stays refused, and `_is_production_python` in the target loop.
- agy gate: `outside_allowed`, where a `.py` outside the root stays refused, and `_is_production_python` in T6.

The out-of-root rules are unaffected, because a listed target is in-root by construction: `resolve` requires `_inside(real_target, real_root)`. `h_mad_mutation_harness.py` reads `mutation-specs/` but is not on any write gate's path.

## Out-of-Scope
- Unlisted code-like files. They are allowed exactly as today, except in the FR-8 states (operator, 2026-11-03).
- Listed doc/data files. They are allowed and never judged (FR-11 residual; operator ruling R-A, 2026-11-04). A Task whose only Production file is a doc/data file gets no test-first gate in Phase 5.
- Wire-registry challenge for non-`.py` files. `changed_files` passes `-- '*.py'` to git, and `ast_targets` parses Python, so a cross-boundary call added in a `.sh` is never challenged. The census in (a) found no consumer that needs it.
- Non-pytest test runners for the judge, such as `.bats` and shell test harnesses. AC-4.4 states the consequence.
- Production tokens the `_NON_PY_PATH_RE` grammar does not capture, listed with their consequence:
  - A bare root-level name with neither `/` nor `.`, such as `` `Makefile` ``, is not collected and is not gated. Spelling it `` `./Makefile` `` collects it.
  - A directory token (`` `h-mad/scripts/` ``) or a glob token is collected, but it equals no file's realpath, so it gates nothing and is not reported.

  The parser probe at `0cb7b9b0` showed `Makefile` dropped and `h-mad/scripts/` collected.
- Writes made by a shell command that an operator allowance (`.h-mad/phase5-shell-allow`) or the safe-command list admits. Like `.py` writes by the same route, they are not judged.
- The three alias residuals of AC-3.5.
- A target with both a production-`.py` name and a listed code-like name. It is judged by its `.py` name (today's selection), so the listed Task's tests are consulted only if the `.py` name also resolves.

## Assumptions
- FR-8 refines orchestrator decision 1 ("unlisted non-`.py` files stay allowed exactly as today") for the one case where listed-ness cannot be decided for a code-like target. It fails closed, following the project-wide fail-closed invariant. The operator ruled this way on 2026-11-03 (judgement call 4, below), so "allow when undecidable" is not an open alternative. Doc/data targets are outside FR-8 (FR-11).
- Operator rulings, 2026-11-03, binding. They confirm v1.0 as drafted and change no requirement.
  - Call 1: widen `task["production"]` (FR-1).
  - Call 2: retire the `ungated:` line and the `ungated` key (FR-2).
  - Call 3: the import-failure RED shortcut is disabled for a non-`.py` target (FR-4, AC-4.5).
  - Call 4: FR-8 fails closed.
  - Call 5: the Claude gate takes its listing decision from a CLI whose values the design names (FR-3).
- Operator rulings, 2026-11-04, binding.
  - R-A: listed doc/data files are exempt and never judged. This gives the Terms *Doc/data suffix* and *Doc/data file*, FR-11, and the re-targeted FR-8.
  - R-B: FR-9 follows the `verify-hmad-gates` method but drives the worktree's hooks by explicit path. The skill's helper is not the instrument.
  - R-C: the prose surfaces are updated (FR-10).
- The impl-plan Task grammar (`_TASK_RE`, `_PATHS_FIELD_RE`, `_NON_PY_PATH_RE`, `_NONE_VALUE_RE`) is unchanged. `test_field_re_is_unchanged` keeps pinning `_FIELD_RE`.
- The `verify-hmad-gates` skill is a **method reference only**.
  - *Where it is.* It lives in the main checkout's project-scoped skills directory, `/Users/kimhawk/orca/skills/.claude/skills/verify-hmad-gates/` (it holds `SKILL.md`, `bin/` and `features/`). That directory is ignored by the `.claude/` entry in `.gitignore` and is untracked, so it is absent from this worktree. It is also absent from `~/.claude/skills`. Verified 2026-11-04 with `ls -d` on both paths and `git check-ignore -v .claude/skills/verify-hmad-gates`, which names the `.gitignore` `.claude/` rule.
  - *Why its helper is not used.* Its helper `bin/hmad-verify.sh` drives installed hook paths only. Its `hermetic()` function is the `env -i` method FR-9 adopts. Verified 2026-11-04 with `grep -nE '^(AGY|CODEX)_GATE=|^hermetic|^#   hmad-verify.sh' <helper>`, which prints the two installed-path assignments with no override variable, the `env -i` wrapper, and usage lines naming the drives `agy`, `codex` and `dispatch` but none for Claude.
  - *Consequence.* FR-9 executes none of the skill's code, and its ACs are written against the hooks' observable verdicts. A change to the skill cannot change what FR-9 requires.
- Work happens in the worktree `gate-non-py-production-files`. The live hooks under `~/.claude/skills/h-mad`, `~/.agents/skills/h-mad` and `~/.gemini/config/skills/h-mad` resolve to another checkout and are never the system under test.

## Version History
- v1.0: Initial specification draft (2026-11-03), from the approved brainstorm v1.0 and orchestrator decisions 1-3. Resolves open questions (a)-(d) from the tree at 0cb7b9b0. No audit cycle answered (first draft).
- v1.1: Corrects the `verify-hmad-gates` availability claim in §"Assumptions" (2026-11-04): the skill is present at `/Users/kimhawk/orca/skills/.claude/skills/verify-hmad-gates/`, untracked and ignored by `.gitignore` `.claude/`, so absent from this worktree only; FR-9 stays independent of the skill's internals. Records the operator rulings of 2026-11-03 (judgement calls 1-5, all confirming v1.0) and removes FR-8's open "if the ruling is instead" alternative. Operator approval of v1.0 was conditional on this correction. No audit cycle answered (orchestrator-verified finding, no audit report).
- v1.2: Applies the operator rulings of 2026-11-04 (R-A, R-B, R-C), raised by the plan v1.0 author against this spec (plan Risks R5, R6, R8; Measurements M5, M6, M7). R-A: adds Terms Doc/data suffix (nine suffixes, ASCII case-insensitive, end-of-basename), Doc/data file, Code-like and Judgeable; adds FR-11 (listed doc/data files are allowed on every host and never judged; residual stated with the M5 reach figure) with AC-11.1 to AC-11.6; extends the fixture with listed README.md and CHANGES.MD; re-targets AC-8.1 and AC-8.3 to scripts/other.sh and adds AC-8.4; relabels the notes.md controls in AC-5.4, AC-6.3, AC-7.3 as doc/data controls; updates Executive Summary, Goal, FR-1 to FR-8 descriptions, NFRs and Out-of-Scope. R-B: FR-9 follows the verify-hmad-gates method against the worktree's hook files by explicit path, and the skill's helper is not the instrument; Assumptions updated. R-C: adds FR-10 (prose surfaces state the shipped rule) with AC-10.1 (phrase sweep) and AC-10.2 (doc-test). AC count 40 to 49 (h_mad_ac_census). No audit cycle answered (operator rulings, no audit report).
- v1.3: Answers plan audit cycle 1, gate-non-py-production-files.plan.audit.v1.p1.md, gate-non-py-production-files.plan.audit.v1.p2.md and gate-non-py-production-files.plan.audit.v1.p3.md (2026-11-04), the findings that land in the spec. p3 must (transport): FR-3 now names each host's real binding of h_mad_tdd_judge (codex calls _load_judge() only after its 'if not production: continue' guard; agy binds 'import h_mad_tdd_judge as judge' inside main and never calls _load_judge) and requires a new call site on codex and agy; FR-6 states the five-step order (read_chain before the listing decision) and FR-7 adopts it; AC-3.1 names the bindings. p3 must (tie-break): FR-6 gains the Selection rule for all three hosts (least basename in Python str order, which is the first qualifying name in canonicalise's sorted names) with AC-5.8, AC-6.5 and AC-7.4 observing which name is judged; FR-5 step 4 points to it. p1 must (incident replay): FR-9 gains the replay of Task 1 of docs/01-plan/features/exec-missing-report-recovery.impl-plan.md, byte-for-byte, with AC-9.4 (before at the merge-base, after at the commit under test, unlisted control, listed doc file) and AC-9.5 (provenance). p2 must and p3 should (prose floor): FR-10's floor re-derived at e4979ecd with a five-branch phrasing set is four surfaces in three files, adding the two in h-mad/references/phase5-substeps.md; the rule gains a fifth part (authorship refusals); FR-10 states regression provenance for test_skill_states_the_docs_first_component_rule and adds AC-10.3; AC-10.1 widened to five branches with per-branch pre-change hits; AC-10.2 control re-measured at e4979ecd. AC count 49 to 55 (h_mad_ac_census).
- v1.4: Corrects FR-9's replay base (2026-11-04), owed by plan v1.2 (a469d565): the before side's base commit is `git merge-base HEAD origin/main` (5cc9e270 at a469d565), not `git merge-base HEAD main` (d655d8cb, from this worktree's stale local main ref); AC-9.5 records the base derived the same way. The gate files are identical between d655d8cb and 5cc9e270, so no AC-9.4 before reading changes. AC count unchanged at 55. No audit cycle answered (orchestrator-verified correction, no audit report).
- v1.5: Final corrective revision after the plan audit's round cap (2026-11-04), not re-audited. Answers gate-non-py-production-files.plan.audit.v2.p1.md (must 1) and the advisory delta review docs/03-analysis/gate-non-py-production-files.plan.delta-review.a469d56-20261103T233158Z.md (should-fix 2, 3, 4; nit 1). Must 1 (connection enforcement): AC-3.1 adds six connection-only mutants, two per host (Claude, codex, agy), with the matcher intact: remove the host's listing call (its listed-DENY test AC-5.1/AC-6.1/AC-7.1 fails) and force it to report listed (its unlisted control in AC-5.4/AC-6.3/AC-7.3 fails), each counted only after its landing is verified; they are AC-9.3's FR-3 connection entries. Should-fix 3: FR-10 regression provenance records the token Both gates of test_skill_states_the_docs_first_component_rule as a stale contract (three gates apply the docs-first rule today) replaced by All three gates; the other four tokens unchanged; AC-10.3 updated. Should-fix 4: NFR Performance allows at most three extra short Python processes (judge-path derivation, state read, listing decision), reducible by the design. Should-fix 2: FR-9 says local main has diverged from origin/main, not that it is stale, with no stamped count; base derivation unchanged. Nit 1: FR-9's gate-file identity proof is git diff --name-only d655d8cb 5cc9e270 -- h-mad listing none of the gates' import closure. AC count unchanged at 55 (h_mad_ac_census).
