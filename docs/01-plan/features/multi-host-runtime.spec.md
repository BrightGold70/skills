# Spec: multi-host-runtime

## Executive Summary

`h-mad` and `handoff` gain a grok host adapter, a committed construct registry
(`h-mad/references/host-constructs.json`) that drives a parity gate counting **mapping rows, not
mentions** across all six host adapters (`{h-mad,handoff}/references/{codex,agy,grok}-runtime.md`),
a catch-all that fails on any unregistered Claude-looking construct in either `SKILL.md`, an explicit
host declaration so the context budget and claims answer cannot-judge rather than a false verdict
on a non-Claude host, `~/.agents/skills/{h-mad,handoff}` and `~/.gemini/config/skills/{h-mad,handoff}`
symlink coverage in `h_mad_install_check.py`, and one read-only live smoke per host as a verification step.

## Goal

A session whose orchestrator host is codex, agy or grok follows the same H-MAD and handoff
contracts as a Claude Code session, and any Claude-specific construct added to either `SKILL.md`
without a per-host mapping fails a test instead of drifting silently.

## Scope, sequencing and dependencies

- **Sequencing (hard).** This feature's implementation merges **after `grok-codex-fallback`**. Both
  edit `h-mad/SKILL.md` and `h-mad/references/agent-substrate.md`. This feature also consumes
  `hmad-dispatch exec grok`, which `grok-codex-fallback` introduces (its spec FR-3, documented in
  `agent-substrate.md` §"Verbs" per its FR-10). In today's tree `exec` accepts only `codex|agy`:
  `grep -n 'unknown agent' h-mad/scripts/hmad-dispatch.sh` shows every agent `case` rejecting
  anything else with `(expected codex|agy)` or `(codex|agy)`. Implementation rebases onto
  `grok-codex-fallback` before its Phase 5c baseline, and the FR-4 calibration is re-derived at that
  base (FR-4, AC-4.6).
- **Hosts in scope (D3):** codex, agy and grok, each for both skills. Claude Code stays the reference
  host; its behaviour is unchanged (FR-12).
- **Dispatched agents (invariant).** `invariants.base.md` §"No new external dependency" lists
  `codex`, `agy` and `grok` as dispatched agents. No test and no script invokes any of them for its
  own work. The parity gate reads files only. The live smoke (FR-11) is an operator verification
  step, not a test, and reaches each host through a `hmad-dispatch` verb.

## Host facts this spec relies on

Each fact below was read in this revision. Chapters are under `~/.grok/docs/user-guide/`
(grok 1.0.41, `grok --version` → `grok 1.0.41 (4220f3b224a6) [stable]`). Section names are given
instead of line numbers.

| # | Fact | Source |
|---|---|---|
| F1 | grok's built-in tools include `todo_write` ("Create and manage task lists"), `spawn_subagent`, `run_terminal_command`, `read_file`/`search_replace`. No tool named `advisor` exists. | `01-getting-started.md` §"Tools"; `22-permissions-and-safety.md` §"Read-Only Tools" lists `todo_write` |
| F2 | `spawn_subagent` takes `prompt`, `description`, `run_in_background` (default `true`), `isolation` (`none`/`worktree`), `resume_from`, `cwd`. The model-facing schema **omits `subagent_type`**, so a child is `general-purpose` unless roles/personas resolve otherwise. A child has its own context window, independent of the parent. Nesting depth is one: a subagent's `spawn_subagent` fails. A background result is read with `get_command_or_subagent_output`. | `16-subagents.md` §"Built-in Agent Types", §"How Subagents Work", §"Spawning Subagents", and the depth-limit paragraph |
| F3 | `send_subagent_message` is off by default (`GROK_ACTIVE_AGENT_MESSAGES` / `[features] active_agent_messages`). | `16-subagents.md` §"Sending messages to subagents" |
| F4 | Skill roots: `~/.grok/skills/`, `~/.claude/skills/` (Claude compat, lowest priority, configurable), and `.agents/skills/` scanned "at each tier (alongside `.grok/`)". Deduplication is by name. | `08-skills.md` §"Skill Locations" |
| F5 | `grok inspect` in this repo lists `h-mad` and `handoff` as `user [claude]`, `Project trusted: no`, and Harness Compatibility `claude` → `skills on (default)`, `hooks on (default)`. | `grok inspect` (no model call), run in this revision |
| F6 | Compat toggles: `compat.claude.skills` / `GROK_CLAUDE_SKILLS_ENABLED`; `compat.claude.hooks` / `GROK_CLAUDE_HOOKS_ENABLED`. | `26-config-reference.md` (compat table) |
| F7 | Hooks from `~/.claude/settings.json` are global and "Always" trusted. Project hooks (`<project>/.claude/settings.json`, `<project>/.grok/hooks/*.json`) "Require trust" and are **silently skipped** until trusted. | `10-hooks.md` §"Hook Locations" |
| F8 | Hook stdin is camelCase (`toolName`, `toolInput`, `sessionId`, …). `hook_event_name` carries Claude's PascalCase value and `hookEventName` carries grok's snake_case value. In matchers, `Edit`, `Write` and `MultiEdit` alias to `search_replace`, `Bash` to `run_terminal_command`, and `Task` to `spawn_subagent`. | `10-hooks.md` §"Writing Hook Scripts" → Input; §"Tool Name Aliases"; porting notes |
| F9 | Exit `2` is an explicit deny for `PreToolUse`. **Any other non-zero exit is fail-open.** A stdout `{"decision":"deny"}` is honoured regardless of exit code. The default hook timeout is 5 s, and a timeout also fails open. | `10-hooks.md` exit-code table; §"Key Fields" (`timeout`) |
| F10 | `GROK_SESSION_ID` is a runner-injected variable **for hook processes**. The guide does not say whether it is present in a `run_terminal_command` shell. Headless `--session-id <uuid>` lets a launcher fix the id. | `10-hooks.md` §"Environment Variables"; `05-configuration.md` hooks paragraph; `14-headless-mode.md` |
| F11 | Headless `--output-format stream-json` emits a `system`/`init` line whose `skills` field lists the session's user-invocable skills. | `14-headless-mode.md` (init line description) |
| F12 | grok memory lives under `~/.grok/memory/` (`MEMORY.md` global/workspace) and not under `~/.claude/projects`. | `13-memory.md` §"Remember", §"Direct Editing" |
| F13 | agy's docs dir has 0 lines matching `session_?id\|sessionId` (case-insensitive), so agy exposes no documented session-id variable. | `grep -rn -i -E 'session_?id\|sessionId' ~/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs \| wc -l` → `0` |
| F14 | This tree holds no codex host document. The codex 0.157.1 binary contains the strings `update_plan`, `request_user_input`, `spawn_agent` and `fork_turns`. Its only `.agents/skills` string occurs in an `external-agent-migration` module context. | `strings "$(readlink -f "$(which codex)")" \| grep -c …`; see Assumption A2 |

## Construct registry seed (measured)

These are the registry's v1 entries. Patterns use Python `re`. `H` abbreviates
`(?:~|\$HOME|\$\{HOME\})/\.claude`. Hit counts are **occurrences** (`re.finditer`) in
`git show 6494b3c:<skill>/SKILL.md`. In a table cell, `\|` is the Markdown escape for the regex
`|`.

| construct id | pattern | skills | h-mad hits | handoff hits |
|---|---|---|---|---|
| `subagent-call` | `\bAgent\(\|\bsubagent_type\b` | h-mad | 14 | 0 |
| `skill-call` | `\bSkill\(` | both | 2 | 1 |
| `advisor` | `\badvisor\(\)` | h-mad | 18 | 0 |
| `send-message` | `\bSendMessage\b` | h-mad | 2 | 0 |
| `hook-event` | `\b(?:PreToolUse\|PostToolUse\|PostToolUseFailure\|PermissionRequest\|SessionStart)\b\|\bStop(?=-hook\b)` | h-mad | 21 | 0 |
| `task-tools` | `\b(?:TaskCreate\|TaskUpdate\|TaskList\|TaskGet\|TodoWrite)\b` | handoff | 0 | 24 |
| `tool-search` | `\bToolSearch\b` | handoff | 0 | 5 |
| `session-id-env` | `\bCLAUDE_CODE_SESSION_ID\b` | h-mad | 1 | 0 |
| `claude-config-dir` | `\bCLAUDE_CONFIG_DIR\b` | h-mad | 2 | 0 |
| `skill-root-env` | `\bCLAUDE_SKILLS_ROOT\b` | handoff | 0 | 18 |
| `todo-tools-optin` | `\bCLAUDE_CODE_ENABLE_TODO_TOOLS\b` | handoff | 0 | 2 |
| `claude-md` | `\bCLAUDE\.md\b` | both | 2 | 1 |
| `claude-skills-dir` | `H/skills\b` | both | 73 | 18 |
| `claude-agents-dir` | `H/agents\b` | h-mad | 6 | 0 |
| `claude-hooks-dir` | `H/hooks\b` | h-mad | 6 | 0 |
| `claude-settings` | `H/settings(?:\.local)?\.json` | both | 2 | 1 |
| `claude-handoffs-dir` | `H/handoffs\b` | both | 1 | 7 |
| `claude-projects-store` | `H/projects\b\|\bMEMORY\.md\b` | h-mad | 3 | 0 |
| `claude-homunculus` | `H/homunculus\b` | handoff | 0 | 2 |
| `claude-home-bare` | `H\b(?!/)` | h-mad | 3 | 0 |
| `session-reset-command` | `` `/(?:clear\|compact)\b `` | both | 4 | 7 |
| `skill-slash-invocation` | `` `/(?:h-mad\|handoff)\b `` | both | 15 | 11 |

Derived counts (from the table): 22 entries. 17 declare `h-mad`: 10 are h-mad-only and 7 are
shared. 12 declare `handoff`: 5 are handoff-only and 7 are shared. With one row per declared
construct per adapter, the six adapters carry 3 × 17 + 3 × 12 = 87 rows in total. These figures are
**functions of the registry**. Every AC below is written against "every entry whose `skills`
includes X", never against 17, 12 or 87. The rebase onto `grok-codex-fallback` can change the entry
set (AC-4.6).

Every entry has ≥ 1 hit in every skill it declares and 0 hits in every skill it does not.
`grok-codex-fallback` edits `h-mad/SKILL.md`, so the implementation re-derives this at its own base.

## Functional Requirements

### FR-1: Construct registry file

- **Description**: `h-mad/references/host-constructs.json` is the single source for the vocabulary
  of host-specific constructs in both skills (OQ5: one shared file with a per-entry `skills` field).
  It is a JSON object with a `constructs` array. Each element has exactly these keys:
  - `id`: matches `^[a-z][a-z0-9-]*$` and is unique. Kebab-case, so an adapter row never has to
    spell a Claude token that an existing test forbids (FR-12).
  - `pattern`: a Python `re` pattern that compiles.
  - `skills`: a non-empty subset of `["h-mad", "handoff"]`.
  - `description`: a non-empty string.

  Only tests read the registry; no skill reads it at runtime. `handoff` therefore stays runnable
  without `h-mad`'s `references/` (`.h-mad/invariants.md` §"Skill self-containment").
- **Acceptance Criteria**:
  - AC-1.1: The committed file parses as JSON and every element satisfies the key rules above. A
    fixture violating each rule fails the gate: invalid JSON; a missing key; a duplicate `id`; an
    `id` with an uppercase letter; a pattern that does not compile; an empty `skills`; a `skills`
    value outside the two names. Each fixture fails with exactly one failure kind (FR-3):
    - a duplicate `id` → `DUPLICATE_ID`;
    - an uncompilable pattern → `BAD_PATTERN`;
    - every other fixture → `REGISTRY_UNREADABLE`.
  - AC-1.2: The committed registry contains at least the 22 seed ids in §"Construct registry
    seed", unless the AC-4.6 re-derivation retires or adds entries and records why.

### FR-2: Machine-readable mapping table in every adapter

- **Description**: Each of the six adapters has exactly one heading `## Construct mapping`: the
  four existing ones and the two new `grok-runtime.md` files. The first pipe table after that
  heading, before the next `## ` heading, is the adapter's mapping. Its header row is exactly
  `| construct | status | mapping | source |`.
  - `construct` is a registry `id`.
  - `status` is one of the closed set `mapped` or `not-applicable`.
  - `mapping` states the host's equivalent when `mapped`, and the reason when `not-applicable`.
  - `source` cites the evidence: a host-doc section, a `grok inspect` / `--help` reading, or an
    observed trace.

  Rows outside this table do not count. **A construct id mentioned anywhere else in the adapter is
  not a mapping.**
- **Acceptance Criteria**:
  - AC-2.1: The table has exactly one row for every registry entry whose `skills` includes the
    adapter's skill (`h-mad/references/*` → `h-mad`, `handoff/references/*` → `handoff`), and no
    other rows.
  - AC-2.2: A cell counts as empty when it contains no `[A-Za-z0-9]` character, or when its trimmed
    text equals `tbd` or `todo` (case-insensitive). Every `mapping` cell and every `source` cell is
    non-empty by that rule. A `not-applicable` row's `mapping` states the reason.
  - AC-2.3: The `advisor` row is `not-applicable` in all three h-mad adapters (codex, agy, grok).
    Each such row names its substitute, per FR-5 AC-5.3 and FR-6 AC-6.3.
  - AC-2.4: The `task-tools` row in each of the three handoff adapters names that host's rung-1 task
    tool, or states that there is none and restoration falls to rung 2 (`.omc/notepad.md`) and then
    rung 3 (the inline checklist).
  - AC-2.5: In each h-mad adapter the `session-id-env` row names the host's session-id source, or
    states that there is none (FR-9).

### FR-3: Parity gate — mappings, not mentions

- **Description**: A pytest module under `h-mad/tests/` reads the registry, both `SKILL.md` files
  and the six adapters. It fails with a message naming the **failure kind**, the file and the
  construct id. The failure kinds form a closed set, and each has its own discriminating fixture:

  | kind | meaning | caller's action |
  |---|---|---|
  | `REGISTRY_UNREADABLE` | the registry is missing, is invalid JSON, or breaks an FR-1 shape rule: a missing or extra key, a malformed `id`, an empty `description`, or an empty or out-of-set `skills` | fix the registry |
  | `DUPLICATE_ID` | two entries share an `id` | merge or rename them |
  | `BAD_PATTERN` | a pattern does not compile | fix the pattern |
  | `STALE_ENTRY` | an entry has 0 hits in a `SKILL.md` it declares | drop the skill from `skills`, or retire the entry and its rows |
  | `UNDECLARED_SKILL` | an entry has ≥ 1 hit in a `SKILL.md` it does not declare | add the skill and that skill's three rows |
  | `UNREGISTERED` | a catch-all hit (FR-4) is covered by no entry declared for that skill | register the construct and add its rows |
  | `TABLE_MISSING` | the adapter has no `## Construct mapping` heading, or no table under it, or has the heading twice | add the table |
  | `TABLE_MALFORMED` | the header row differs from the contract, or a row has the wrong cell count | fix the table |
  | `ROW_MISSING` | a construct declared for the adapter's skill has no row | add the row |
  | `ROW_UNKNOWN_ID` | a row names an id that is not in the registry | fix or remove the row |
  | `ROW_WRONG_SKILL` | a row names a construct not declared for this adapter's skill | remove the row, or declare the skill |
  | `ROW_DUPLICATE` | two rows share one id | keep one |
  | `STATUS_INVALID` | `status` is neither `mapped` nor `not-applicable` | fix the status |
  | `CELL_EMPTY` | a `mapping` or `source` cell is empty by AC-2.2 | fill it |

  "Hits" and "covered" mean regex match spans, as FR-4 defines them. The gate never invokes a host
  CLI.
- **Acceptance Criteria**:
  - AC-3.1: On the implemented tree the gate passes with zero failures.
  - AC-3.2 (mention is not a mapping): Take a fixture adapter whose table lacks the `advisor` row
    but whose prose mentions `advisor` three times. The gate fails with `ROW_MISSING` for
    `advisor`.
  - AC-3.3: Each remaining kind in the table has a fixture that triggers **that kind alone**, and
    the gate reports that kind for it. Fourteen kinds means fourteen fixtures. None of them is a
    fixture that triggers two kinds, where a healthy sibling kind could mask a broken one.
  - AC-3.4: Two fixtures cover `STALE_ENTRY` and `UNDECLARED_SKILL`: a registry entry with 0 hits
    in a declared skill, and an entry with hits in an undeclared skill. They report those kinds.
  - AC-3.5: The gate completes without executing any process named `codex`, `agy` or `grok`. The
    module imports no subprocess launcher, or a stubbed `PATH` in which those names fail loudly
    shows zero invocations.

### FR-4: Catch-all for unregistered Claude-looking constructs

- **Description**: The gate runs a catch-all regex over each `SKILL.md`. It is the union of four
  axes, each an open class rather than a list of instances:
  - **A1, call syntax**: a PascalCase identifier immediately followed by `(`:
    `\b[A-Z][a-z]+([A-Z][a-z]+)*\(`.
  - **A2, backticked compound PascalCase**: at least two humps inside backticks:
    `` `[A-Z][a-z]+([A-Z][a-z]+)+` ``.
  - **A3, Claude environment**: `\bCLAUDE[A-Z0-9_]*\b`.
  - **A4, Claude home path**: `(~|\$HOME|\$\{HOME\})/\.claude\b`.

  An A2 hit is excluded when it ends in a Python exception-class suffix:
  `` (Error|Exception|Warning|Expired|Exit|Interrupt)`$ ``. Every hit that remains must overlap
  the match span of at least one registry pattern for an entry declared for that skill. If not,
  the gate fails with `UNREGISTERED`, naming the token.

  **Calibration (measured, 0 false hits).** Command, at `6494b3c`:

  ```bash
  CA='\b[A-Z][a-z]+([A-Z][a-z]+)*\(|`[A-Z][a-z]+([A-Z][a-z]+)+`|\bCLAUDE[A-Z0-9_]*\b|(~|\$HOME|\$\{HOME\})/\.claude\b'
  EX='(Error|Exception|Warning|Expired|Exit|Interrupt)`$'
  for f in h-mad/SKILL.md handoff/SKILL.md; do
    git show 6494b3c:$f | grep -o -E "$CA" | grep -v -E "$EX" | sort | uniq -c
  done
  ```

  Reading, in **occurrences** (`grep -o` emits one line per match):
  - `h-mad/SKILL.md`: 122 occurrences over 13 distinct tokens: `~/.claude` 82, `$HOME/.claude`
    10, `Agent(` 8, `` `PreToolUse` `` 6, `` `PostToolUse` `` 3, `Skill(` 2, `CLAUDE_CONFIG_DIR`
    2, `CLAUDE` 2, `` `SendMessage` `` 2, `` `PostToolUseFailure` `` 2, `CLAUDE_CODE_SESSION_ID`
    1, `` `SessionStart` `` 1, `` `PermissionRequest` `` 1.
  - `handoff/SKILL.md`: 71 occurrences over 12 distinct tokens: `$HOME/.claude` 19,
    `CLAUDE_SKILLS_ROOT` 18, `~/.claude` 9, `` `TaskCreate` `` 7, `` `TodoWrite` `` 5,
    `` `ToolSearch` `` 3, `` `TaskList` `` 3, `CLAUDE_CODE_ENABLE_TODO_TOOLS` 2,
    `` `TaskUpdate` `` 2, `Skill(` 1, `CLAUDE` 1, `` `TaskGet` `` 1.

  Every one of the 25 distinct tokens is a Claude construct. Each bare `CLAUDE` is the stem of
  `CLAUDE.md`: all three contexts were read. That makes 0 false hits. With the seed registry,
  0 hits are `UNREGISTERED` in either file.

  The exclusion removes 9 occurrences in h-mad (`AttributeError` 2, `TimeoutExpired` 2,
  `ImportError`, `IndentationError`, `NameError`, `SyntaxError`, `TabError` 1 each) and 1 in
  handoff (`KeyError`). Without it the catch-all has 10 false hits, so the exclusion is
  load-bearing.

  **Residual (not caught by the catch-all; stated exactly):**
  - (r1) single-hump PascalCase names that are not followed by `(`, such as `` `Agent` ``, "the
    Agent tool", `` `Skill` ``, `` `Bash` `` or `` `Stop` ``. The shape cannot be told apart from a
    capitalised English word or a table header: the corpus has `Agent-pane` and an `Agent` column
    header.
  - (r2) compound PascalCase that is not backticked, for example a bare `PreToolUse` in prose.
  - (r3) lowercase or snake_case constructs, such as `advisor()`, `subagent_type` or a new keyword
    argument.
  - (r4) slash commands, such as `/clear` or `/compact`.
  - (r5) Claude constructs whose name ends in one of the six excluded suffixes.
  - (r6) constructs in `references/*.md`, `hooks/*` or `scripts/*`, which lie outside the
    two-file corpus. For example, `handoff/references/auto-memories.md` names `SessionStart` and
    `PreToolUse`.

  (r1)–(r4) are gated for the seed instances only, through their registry entries. The catch-all
  does not see a new member of those classes.
- **Acceptance Criteria**:
  - AC-4.1: On the implemented tree, the catch-all yields 0 `UNREGISTERED` in both `SKILL.md`
    files.
  - AC-4.2 (per-branch controls): There is one fixture per axis, each run with **that axis alone**
    in the pattern: A1 `Foobar(`, A2 `` `FooBar` ``, A3 `CLAUDE_FOO`, A4 `~/.claude/foo`. Each is
    reported `UNREGISTERED` against an empty registry. Then, with the full union, removing any one
    axis makes its own fixture pass. That shows each branch discriminates on its own and no
    healthy sibling covers for it.
  - AC-4.3 (exclusion controls): There is one fixture per exclusion suffix: `` `FooError` ``,
    `` `FooException` ``, `` `FooWarning` ``, `` `FooExpired` ``, `` `FooExit` ``,
    `` `FooInterrupt` ``. Each is **not** reported, and each is reported once the suffix is removed
    from the exclusion. The corpus exercises only `Error` and `Expired`. The other four suffixes
    have no corpus instance, so their fixtures are their only evidence.
  - AC-4.4: A fixture `SKILL.md` that adds `` `TeamCreate` `` fails with `UNREGISTERED` naming
    `TeamCreate`. After a registry entry for it is added, together with its rows in the three
    adapters of that skill, the fixture passes.
  - AC-4.5: The calibration command and its reading appear in the Phase 6 analysis document at
    the implementation's base sha.
  - AC-4.6: After the rebase onto `grok-codex-fallback`, the calibration command is re-run at the
    new base. The following are recorded: the reading; any new distinct token and its
    classification (Claude construct, or false hit); and the resulting registry changes. A false
    hit is fixed by narrowing an axis or its exclusion, which is recorded with a new control, and
    never by adding a registry entry for a non-construct.

### FR-5: grok host adapters (delta over Claude compatibility, D1)

- **Description**: `h-mad/references/grok-runtime.md` and `handoff/references/grok-runtime.md`
  document only where grok diverges from Claude Code. They name the grok version they were
  verified against (1.0.41) and the compat toggles they rely on (F5, F6), with the verification
  command `grok inspect` § "Harness Compatibility". Beyond the FR-2 table, each adapter states:
  - **Package root.** `HMAD_SKILL_ROOT` / `HANDOFF_SKILL_ROOT` resolve from the loaded skill path.
    Today grok loads both skills from `~/.claude/skills` through `compat.claude.skills` (F4, F5).
    After FR-10, `~/.agents/skills` provides the same checkout as well.
  - **Project trust.** The TDD, advisor-warn and memory-guard hooks are wired in the global
    `~/.claude/settings.json`, so they need no trust. Any project-level Claude hook is silently
    skipped until `/hooks-trust` or `--trust` (F7).
  - **Hooks** (h-mad only): the payload differences (F8), the exit-code semantics (F9) and the
    5 s default timeout.
  - **Author and reviewer roles.** `spawn_subagent` cannot select `spec-author` or the other
    teammate files by name (F2). The role is carried by putting the agent file's text from
    `$HMAD_SKILL_ROOT/agents/<name>.md` into `prompt`. Its result is collected with
    `get_command_or_subagent_output`. Recursion is capped at one level by the host.
- **Acceptance Criteria**:
  - AC-5.1: Both files exist, contain the string `1.0.41`, and contain `compat.claude.skills`. The
    h-mad file also contains `compat.claude.hooks`.
  - AC-5.2 (TDD gate, h-mad): The grok h-mad adapter contains the halt token
    `step5:grok_tdd_hook_unverified`. It states that Phase 5 halts with that token until a grok
    refusal of a production write has been observed. It gives three reasons, each with its
    evidence:
    - (i) `h-mad/hooks/h-mad-tdd-gate.sh` refuses by `exit 1`, which grok treats as fail-open
      (F9). `grep -n 'exit 1' h-mad/hooks/h-mad-tdd-gate.sh` shows every BLOCK branch. This
      reason is about grok only. Whether `exit 1` blocks on Claude Code is not asserted by this
      spec: that question is D4 of feature `codex-tdd-gate-defects`
      (`docs/01-plan/features/codex-tdd-gate-defects-brainstorm.md`, commit `76b2501`).
    - (ii) the gate reads a top-level `file_path`/`path` from stdin, while grok nests tool input
      under `toolInput` (F8). An empty target path takes the gate's `[ -z "$TARGET_PATH" ] && exit
      0` allow branch.
    - (iii) the gate may run `pytest` inside grok's 5 s default timeout, and a timeout fails open
      (F9).
  - AC-5.3 (OQ1, advisor): The `advisor` row is `not-applicable`. The grok guide lists no advisor
    tool (F1). A `spawn_subagent` child does not inherit the parent transcript (F2), so it is not
    a transcript-forwarding advisor. The row names the substitutes:
    - a dispatched independent reviewer, `hmad-dispatch exec codex|agy|grok <promptfile>`;
    - a `spawn_subagent` child whose `prompt` carries everything the review needs.
  - AC-5.4 (OQ2, task sink): The handoff grok adapter's `task-tools` row is `mapped` to
    `todo_write`, citing F1. It notes that the todo pane is user-visible (`16-subagents.md`
    mentions the separate todo pane, toggled with `Ctrl+T`), which is what rung 1 requires.
  - AC-5.5 (OQ3, session id): The `session-id-env` row names `GROK_SESSION_ID`. It states that
    the variable is documented for hook processes only (F10), and that its presence in the
    orchestrator's shell is recorded by the live smoke (FR-11). Until the smoke records it as
    present, FR-9's minted-id rule applies.
  - AC-5.6: The `claude-projects-store` row is `not-applicable`. It names grok's own store (F12)
    and forbids pointing `h_mad_check_memory_index.py` at `~/.claude/projects` from a grok
    session, on the same reasoning as the agy adapter's §"Memory index".
  - AC-5.7: Every `source` cell of both grok tables names a chapter file matching
    `\b\d\d-[a-z-]+\.md\b`, or the literal `grok inspect`, or begins with `observed:`. The test
    checks only the format. Chapter existence is checked in review, because a test must not read
    `~/.grok` (FR-3, AC-3.5).

### FR-6: codex and agy adapters brought to parity (D3)

- **Description**: The four existing adapters gain the FR-2 table. The gap is measured **before**
  the tables are written: for each construct and each adapter, record whether the adapter's
  current prose addresses it (`addressed`, naming its section) or not (`absent`), at the
  pre-change sha. OQ1–OQ3 are answered per host from host evidence only.
- **Acceptance Criteria**:
  - AC-6.1: The Phase 6 analysis document contains the pre-change gap table (construct ×
    adapter, `addressed`/`absent`) with its sha. This is a verification artifact, not a pytest AC.
  - AC-6.2: All four adapters pass FR-3.
  - AC-6.3 (OQ1): The `advisor` row is `not-applicable` in the codex and agy h-mad adapters. Each
    names its substitutes:
    - codex: `hmad-dispatch exec agy|grok`, or `collaboration.spawn_agent` with
      `fork_turns: "all"`. That inherits the transcript, which is the nearest analogue to advisor's
      forwarding.
    - agy: `hmad-dispatch exec codex|grok`, or `define_subagent` / `invoke_subagent` with the
      review context in the prompt.
  - AC-6.4 (OQ2): The agy handoff `task-tools` row states that there is no rung 1 and names the
    fall to rung 2/3. It carries forward the adapter's existing `manage_task` reasoning. The codex
    handoff `task-tools` row cites evidence for its rung 1. Otherwise it states "none → rung 2" (see
    Assumption A3: `update_plan` is a lead, not evidence).
  - AC-6.5 (OQ3): The codex and agy `session-id-env` rows state that the host exposes no
    documented session-id variable (F13, F14), and that FR-9's minted-id rule applies.
  - AC-6.6: The existing negative assertions still pass unchanged. The codex adapters still
    contain none of `Agent(subagent_type:`, `AskUserQuestion`, `TodoWrite` (both skills) or
    `Skill(skill:` (handoff) (FR-12).

### FR-7: Host routing names grok

- **Description**: The `## Host runtime` section of each `SKILL.md` (the text from that heading
  to the next `## ` heading) lists grok among the supported hosts. It instructs a grok host to
  read `references/grok-runtime.md` before bootstrap (h-mad) or before acting (handoff). It keeps
  the existing rule: adapt a new host by adding an adapter, never by rewriting the Claude spelling
  in place.
- **Acceptance Criteria**:
  - AC-7.1: In both files, the located `## Host runtime` section contains
    `references/grok-runtime.md`, `references/codex-runtime.md` and `references/agy-runtime.md`.
  - AC-7.2: The edit adds no `UNREGISTERED` hit (FR-4 re-run).
  - AC-7.3: If the `## Host runtime` heading is renamed or duplicated, AC-7.1 fails loudly and
    does not match a different section. The locator's residual: it pins the heading text, not the
    section's position.

### FR-8: Host declaration; the context budget answers cannot-judge off Claude

- **Description**: Every non-Claude adapter instructs the orchestrator to declare its host inline
  on each h-mad script call: `HMAD_HOST=<codex|agy|grok> python3 …`. It is inline so that it does
  not depend on whether the host's shell persists exports between calls.
  `h_mad_context_budget.py` reads `HMAD_HOST` before any transcript lookup:

  | `HMAD_HOST` | output | exit |
  |---|---|---|
  | unset, empty, or `claude` | today's behaviour, byte-identical | unchanged |
  | `codex`, `agy` or `grok` | `CTXBUDGET: UNKNOWN reason=host_unsupported host=<value>`, no `used=` field. `--transcript` does not override this. | 2 |
  | any other value | `CTXBUDGET: UNKNOWN reason=unknown_host host=<value>` | 2 |

  Host detection by environment markers is rejected on evidence. This Claude Code shell carries
  `CODEX_COMPANION_SESSION_ID`, a plugin variable. A `CODEX_*` marker therefore does not identify
  a codex host, and an inherited `CLAUDECODE` does not identify a Claude one.
- **Acceptance Criteria**:
  - AC-8.1: Set `HMAD_HOST=grok` with a valid Claude JSONL present at the cwd slug and passed via
    `--transcript`. The output is exactly `CTXBUDGET: UNKNOWN reason=host_unsupported host=grok`,
    the exit is 2, and no `used=` substring appears. The same holds per host for `codex` and
    `agy`: one fixture each, run separately.
  - AC-8.2: `HMAD_HOST=zzz` yields `reason=unknown_host`, exit 2.
  - AC-8.3: With `HMAD_HOST` unset, and again with it set to `claude`, every existing
    `test_h_mad_context_budget.py` test passes unchanged, and a sample run's stdout is
    byte-identical to the pre-change script's.
  - AC-8.4: Each h-mad non-Claude adapter tells the orchestrator how to read the run-mode ceiling
    on that host. `UNKNOWN` is never read as `OK`. The 80% ceiling is unenforced there, and the
    adapter names what the orchestrator uses instead (the host's own context indicator), or states
    that there is none.
  - Residual: an orchestrator on a non-Claude host that omits `HMAD_HOST` gets today's behaviour.
    The slug-walk fallback can then measure a Claude transcript for the same cwd. The live smoke
    (FR-11) checks that the adapter's instruction is followed. No mechanism in this feature
    detects the omission itself.

### FR-9: Claims on hosts without a session id

- **Description**: A claim must never run with its collision check silently disabled.
  `h_mad_resume_decision.py` treats a missing `--session-id` as an opt-out and never reports
  `owned_elsewhere` in that case, which is a false clear. Under a declared non-Claude
  `HMAD_HOST`, a call without `--session-id` prints `cannot_judge`, the existing
  not-a-decision token, instead of a routing token.

  The session-id source per host:

  | host | source |
  |---|---|
  | Claude | `CLAUDE_CODE_SESSION_ID` |
  | grok | `GROK_SESSION_ID` when the live smoke has recorded it present in the orchestrator's shell; otherwise a minted id |
  | codex, agy | a minted id |

  A minted id is one `python3 -c 'import uuid; print(uuid.uuid4())'` value, created once at
  bootstrap and passed on every `--claim`, `--beat`, `--set` and `--release` in that session. Its
  failure mode is stated and conservative: a session that loses the id after a restart sees its
  own claim as `owned_elsewhere` until the staleness window lapses. It never gets a false clear.
- **Acceptance Criteria**:
  - AC-9.1: With `HMAD_HOST=grok` and no `--session-id`, a state file holding a feature owned by a
    live foreign session yields `cannot_judge`. So does a state file with no owner. Each is a
    separate fixture, and `codex` and `agy` each get the same pair.
  - AC-9.2: With `HMAD_HOST` unset, every existing `test_h_mad_resume_decision.py` and
    `test_h_mad_feature_lock.py` test passes unchanged. That includes the legacy opt-out
    `test_no_session_id_preserves_legacy_behaviour`.
  - AC-9.3: Each h-mad non-Claude adapter's `session-id-env` row states the minted-id procedure
    and its failure mode.
  - AC-9.4: `h-mad/SKILL.md`'s routing table row for `cannot_judge` already says to stop and not
    initialise. But it names only one cause, a state file that exists and could not be read. The
    row gains the second cause: a declared non-Claude host called without `--session-id`. The
    remedy for that cause is to pass the id, not to repair the file. Locate the row by its first
    cell `` `cannot_judge` `` in the decision-routing table. The residual: if that table is
    restructured, find the row by the token.

### FR-10: `~/.agents/skills` and agy skill-root install and install-check coverage

- **Description**: Hosts get `h-mad` and `handoff` as **symlinks into this checkout**, never
  copies, at two roots:
  - `~/.agents/skills/h-mad` and `~/.agents/skills/handoff`;
  - `~/.gemini/config/skills/h-mad` and `~/.gemini/config/skills/handoff` (the agy root; operator
    decision on v1.0).

  Readers of each root:
  - `~/.agents/skills`: grok (F4, user tier) and codex (Assumption A2, unverified locally).
  - `~/.claude/skills`: Claude Code, and grok through `compat.claude.skills` (F4, F5).
  - `~/.gemini/config/skills`: agy. agy reads that root and a workspace `.agents/`, not
    `~/.agents` (its adapter).

  The install is a documented operator command in the codex, grok and agy adapters. No script
  links anything: `h_mad_install_check.py` "repairs nothing". `h_mad_install_check.py` gains two
  options, each with the same sibling-repo derivation as today:
  - `--agents-skills-dir` (default `~/.agents/skills`). It applies the existing `check_siblings`
    semantics to that directory unchanged:
    - a present-but-wrong entry is an issue, reported as `SIBLING_NOT_SYMLINK`,
      `SIBLING_DANGLING` or `SIBLING_WRONG_CHECKOUT`;
    - an absent entry is not an issue.
  - `--agy-skills-dir` (default `~/.gemini/config/skills`). Every entry under it whose name is
    one of this checkout's top-level skills is classified into exactly one of four states:
    absent, correct symlink, or one of the three present-but-wrong kinds (`NOT_SYMLINK`,
    `DANGLING`, `WRONG_CHECKOUT`, with the same definitions as the `SIBLING_*` tokens). The
    outcome depends only on whether the name is one this feature installs there:
    | name | absent | correct symlink | present-but-wrong |
    |---|---|---|---|
    | `h-mad` or `handoff` | nothing | nothing | **issue**: `SIBLING_<KIND>:<link> …`, counted in `issues=N`, verdict `FAIL` |
    | any other checkout skill name | nothing | nothing | **detail line only**: `AGY_SIBLING_COLLISION:<link> kind=<KIND>`, never counted, verdict unaffected |

    Why the axis is the name and not the kind: agy ships its own skills in that root, and some
    share a name with a checkout skill. A same-named plain directory is then agy's own skill, not
    a stale copy of ours, and the check cannot tell the two apart. Only `h-mad` and `handoff` are
    names the operator is told to link there, so only they can be wrong in a way this feature
    owns. The same rule covers every other name, including collisions agy adds later; none of
    them can turn the verdict to `FAIL`.

    Detail lines are printed after the verdict block (after `OK` on `PASS`, after the issue
    lines on `FAIL`), one per colliding name, sorted by name. They never start with `INSTALL:`
    or `SIBLING_`, so the one-token invariant and any caller that counts `SIBLING_` lines are
    unaffected. `issues=N` counts issues only.

    Residual (stated, not closed): a stale plain-directory copy of any checkout skill other than
    `h-mad` or `handoff` under the agy root is reported and never fails. That is the price of not
    failing on agy's own same-named skills.

  The existing `SIBLING_*` semantics for the `~/.claude/skills` root (the directory holding
  `--skills-link`) are unchanged: there, every present-but-wrong checkout name is an issue,
  whatever the name. The name split above applies to the agy root only.

  The verdict tokens are unchanged: `INSTALL: PASS`, exit 0; `INSTALL: FAIL issues=N`, exit 0;
  `INSTALL: UNREADABLE`, exit 2. An empty `--agents-skills-dir` or `--agy-skills-dir` is
  `UNREADABLE`, like the two existing path options.

  Measured at `76b2501`, each root intersected with this checkout's 316 top-level skill names
  from `git ls-files '*/SKILL.md' | awk -F/ 'NF==2{print $1}' | sort -u`:
  - `~/.agents/skills`: 0 colliding names.
  - `~/.gemini/config/skills`: 1 colliding name, `debugger`, a plain directory. It is agy's own
    skill. Under the rule above it prints one `AGY_SIBLING_COLLISION:… kind=NOT_SYMLINK` detail
    line. `h-mad` and `handoff` are absent there, and absence passes.

  The check therefore reads `PASS` on the day it lands, with one detail line on this machine.
- **Acceptance Criteria**:
  - AC-10.1: Fixtures under `tmp_path` cover the following, with `h-mad` and `handoff` in the
    agents dir:
    - a correct symlink → no agents-dir issue;
    - a plain directory → `SIBLING_NOT_SYMLINK`;
    - a dangling link → `SIBLING_DANGLING`;
    - a link into another checkout → `SIBLING_WRONG_CHECKOUT`;
    - the entry absent → no issue.
  - AC-10.2: Every existing `test_h_mad_install_check.py` test passes unchanged. The run with
    the agents dir absent entirely yields the same stdout as today.
  - AC-10.3: `--agents-skills-dir ""` → `INSTALL: UNREADABLE`, exit 2. `--agy-skills-dir ""` →
    `INSTALL: UNREADABLE`, exit 2.
  - AC-10.4: The codex and grok h-mad adapters state the two `~/.agents/skills` `ln -s` commands.
    The agy h-mad adapter states the two `~/.gemini/config/skills` `ln -s` commands. Each states
    that an existing non-symlink at either path is an operator decision and is never overwritten.
    The codex and grok adapters also state that creating the link does **not** re-arm HemaSuite's
    codex TDD gate: that project's tracked `.codex/hooks.json` reads `{"hooks": {}}` in this
    revision.
  - AC-10.5 (agy root, one fixture per cell): fixtures under `tmp_path`, passed through
    `--agy-skills-dir`, cover each cell of the FR-10 table separately:
    - `h-mad` as a correct symlink → no issue, no detail line;
    - `h-mad` as a plain directory, as a dangling link, and as a link into another checkout →
      `SIBLING_NOT_SYMLINK`, `SIBLING_DANGLING`, `SIBLING_WRONG_CHECKOUT` respectively, and
      `INSTALL: FAIL`;
    - `handoff` in the same three wrong states → the same three tokens, each in its own fixture;
    - `h-mad` and `handoff` absent → `INSTALL: PASS`;
    - a non-installed checkout name (fixture name `debugger`) as a plain directory, as a dangling
      link, and as a link into another checkout → `INSTALL: PASS` with exactly one
      `AGY_SIBLING_COLLISION:` line whose `kind=` is `NOT_SYMLINK`, `DANGLING`, `WRONG_CHECKOUT`
      respectively, and no `SIBLING_` line;
    - a wrong `h-mad` plus a colliding `debugger` together → `INSTALL: FAIL issues=1`, one
      `SIBLING_` line and one `AGY_SIBLING_COLLISION:` line.
  - AC-10.6 (regression, `~/.claude/skills` root unchanged): with the same plain directory named
    `debugger` placed in the `--skills-link` parent directory instead, the result is
    `SIBLING_NOT_SYMLINK` and `INSTALL: FAIL`, exactly as today, and no `AGY_SIBLING_COLLISION:`
    line is printed. Every existing sibling test (the class holding
    `test_a_sibling_installed_as_a_copy_is_reported`) passes unchanged.
  - Residual: absence passes at both new roots. That is the existing sibling rule, so a host that
    needs `~/.agents/skills/h-mad` or `~/.gemini/config/skills/h-mad` and lacks it is caught by the
    live smoke (FR-11), not by this check.
  - Residual (test hermeticity): the existing tests do not pass the new options, so they read the
    real `~/.agents/skills` and `~/.gemini/config/skills`. Their fixture repos ship skills named
    `h-mad` and `handoff`, exactly the names the operator links under both roots, so at the real
    defaults they print `SIBLING_WRONG_CHECKOUT` lines once the links exist. Tests are hermetic
    through the `HMAD_AGENTS_SKILLS_DIR` / `HMAD_AGY_SKILLS_DIR` overrides, which a conftest
    autouse fixture sets to absent paths. New tests pass both options explicitly.

### FR-11: One read-only live smoke per host (D4). This is a verification step, not a test.

- **Description**: For each of codex, agy and grok, run one headless `/h-mad status <feature>`
  through `hmad-dispatch exec <host> <promptfile>`. `exec grok` requires `grok-codex-fallback`.
  `<feature>` is one present in `docs/.bkit-memory.json` `orchestrator_state` at smoke time.

  The prompt asks the host to:
  - declare `HMAD_HOST`;
  - print, read-only, whether its session-id candidate variable is set: `GROK_SESSION_ID` for
    grok, and for codex/agy any variable its adapter names;
  - run the status verb.

  No pytest AC requires a live model call. **A host that cannot run halts to the operator with the
  reason, and it never counts as a pass.** A host cannot run when any of these holds: the CLI is
  absent from `PATH`; it is unauthenticated; its quota is exhausted; `exec` returns a non-zero rc,
  or no final message.
- **Verification criteria** (recorded in `docs/03-analysis/multi-host-runtime.live-smoke.md`, one
  section per host, each stamped with the host version and the tree sha):
  - V-11.1: The transcript shows the host loaded h-mad's `SKILL.md` and read
    `references/<host>-runtime.md` before running any script. For grok, the stream-json `init`
    line's `skills` list contains `h-mad` (F11).
  - V-11.2: The status output names the feature and its `last_completed_phase` / `halt_reason`.
    These equal what `docs/.bkit-memory.json` holds for it, read directly.
  - V-11.3: The run is read-only: `git status --short` (tracked **and** untracked) is identical
    before and after, and the sha256 of `docs/.bkit-memory.json` is unchanged.
  - V-11.4: The session-id probe result is recorded. For grok it decides AC-5.5's branch, present
    or minted.
  - V-11.5: Cost, where the host reports it, is recorded.

### FR-12: Regression — the Claude host and existing pins are unchanged

- **Acceptance Criteria**:
  - AC-12.1: The full `h-mad/tests` and `handoff/tests` suites pass, not a scoped subset. That
    includes `test_h_mad_codex_runtime.py` and `test_handoff_codex_runtime.py` with their
    forbidden-token assertions unchanged.
  - AC-12.2: `h_mad_context_budget.py`, `h_mad_resume_decision.py` and `h_mad_install_check.py`
    produce byte-identical stdout and exit codes with `HMAD_HOST` unset and both new roots pointed
    at absent paths (`HMAD_AGENTS_SKILLS_DIR`, `HMAD_AGY_SKILLS_DIR`), on the existing tests'
    fixtures. At the real default roots with the four operator links present, exit codes are
    identical and the only stdout differences are the new roots' `SIBLING_*` lines for those
    links, `AGY_SIBLING_COLLISION:` lines for names already present under
    `~/.gemini/config/skills`, and the verdict line they change.

## Non-Functional Requirements

- Performance: The parity gate reads 9 files (1 registry, 2 `SKILL.md`, 6 adapters) and compiles
  22 + 1 patterns. It must add under 2 s to the suite on this machine. N/A beyond that.
- Security: Symlink installation is an operator act. No script creates, repairs or overwrites a
  link. The grok adapter states the no-filesystem-jail posture for any delegated dispatch, as the
  agy adapter does: diff `git status --short`, tracked and untracked, after each one.
- Compatibility: The Claude host is byte-identical (FR-12). `~/.claude/skills/h-mad` is a symlink
  into this repo, so both coupled suites run before merge. The feature adds no Python package and
  no CLI (invariant).

## Out-of-Scope

- Fixing `h-mad-tdd-gate.sh` for grok (exit-code protocol, payload shape, timeout). This feature
  documents the gap and halts on it (AC-5.2). A grok-speaking gate is a separate feature.
- The codex TDD gate defects D1–D3 in `docs/handoffs/2026-09-28-main__codex-tdd-gate-defects.md`.
  This feature absorbs only that brief's install half. Re-arming HemaSuite's gate is an operator
  act.
- Whether the Claude-side TDD gate's `exit 1` actually blocks on Claude Code. That is D4 of
  feature `codex-tdd-gate-defects` (commit `76b2501`); this spec makes no claim either way.
- Extending the catch-all's corpus to `references/`, `hooks/` or `scripts/` (residual r6).
- A standalone grok install with its own `~/.grok` hooks (rejected by D1).
- Detecting an omitted `HMAD_HOST` (FR-8 residual).
- The `claude-home-bare` and path-construct rows do not rewrite any Claude path in `SKILL.md`.
  Adapters override; `SKILL.md` keeps the Claude spelling (its §"Host runtime" rule).

## Assumptions

- A1: grok 1.0.41's documented behaviour (F1–F12) holds at implementation time. Each grok adapter
  pins the version, and the live smoke re-verifies. A newer grok at smoke time is recorded, not
  silently accepted.
- A2: codex 0.157.1 loads user skills from `~/.agents/skills`. **Not verified against any host
  document in this environment.** The evidence is a single `.agents/skills` string inside an
  `external-agent-migration` context in the codex binary (F14), plus the HemaSuite brief's report
  that a codex hook path under `~/.agents/skills` was consulted. A hook path is not a skill root.
  The codex live smoke (V-11.1) decides. If codex does not load h-mad from there, the smoke halts
  to the operator and this assumption is corrected in the spec.
- A3: codex's rung-1 task tool is unknown. `update_plan` appears in the binary (F14) but has no
  documentation here. It becomes the codex `task-tools` mapping only with a cited doc or an
  observed trace.
- A4: The seed counts and the FR-4 reading are at `6494b3c`. They move with any edit to either
  `SKILL.md`, including `grok-codex-fallback`'s. They are re-derived at the implementation base
  (AC-4.6) and are never carried.
- A5: Tests may read a sibling skill's files. There is precedent: `h-mad/tests/test_skill_body_renderer_args.py`
  reads `handoff/SKILL.md`, and `handoff/tests/test_handoff_oracle_token_coverage.py` reads
  `h-mad/scripts/h_mad_resume_decision.py`. The registry is never read at skill runtime.

## Version History
- v1.0: Initial specification draft (2026-09-28) from the operator-approved brainstorm (D1–D4). Resolves OQ1–OQ5 against host docs; seeds a 22-entry construct registry and calibrates the catch-all at 6494b3c.
- v1.1: Operator decision on the v1.0 agy question (2026-09-28): FR-10 installs and checks the agy root ~/.gemini/config/skills/{h-mad,handoff} via --agy-skills-dir; a present-but-wrong h-mad/handoff there FAILs, any other colliding checkout name (measured: debugger) prints an AGY_SIBLING_COLLISION detail line and never FAILs (AC-10.5); ~/.claude/skills SIBLING_* semantics pinned unchanged (AC-10.6). agy smoke residual V-11.6 and the Owed decisions section removed. AC-5.2(i) and Out-of-Scope point Claude-side exit-1 blocking to codex-tdd-gate-defects D4 (76b2501).
- v1.2: Wording owed by plan v1.2 (2026-09-28, e32ffe5c): AC-12.2 now states byte-identity with both new roots pointed at absent paths (HMAD_AGENTS_SKILLS_DIR, HMAD_AGY_SKILLS_DIR) and, at the real defaults with the four operator links present, identical exit codes and a closed stdout diff (new-root SIBLING_* lines, AGY_SIBLING_COLLISION: lines, the verdict line). FR-10 hermeticity residual corrected: the fixture repos ship h-mad and handoff, the names the operator links, so hermeticity is the env override set by a conftest autouse fixture, not the fixture name. Premises re-run against the tree; nothing else changed.
