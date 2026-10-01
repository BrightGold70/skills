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
  edit `h-mad/SKILL.md`. `grok-codex-fallback` also edits `h-mad/references/agent-substrate.md`
  §"Verbs" (its FR-10); this feature **reads** that file for the `exec grok` verb and edits it
  nowhere, since no FR below names it. This feature consumes
  `hmad-dispatch exec grok`, which `grok-codex-fallback` introduces (its spec FR-3). In today's tree `exec` accepts only `codex|agy`:
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
| F9 | Exit `2` is an explicit deny for `PreToolUse`. **Any other non-zero exit is fail-open.** A stdout `{"decision":"deny"}` is honoured regardless of exit code. The decision may also be written as `hookSpecificOutput.permissionDecision` (`allow`/`deny`/`ask`/`defer`), which is canonical and decides when present; the top-level `decision` applies only when it is absent. The default hook timeout is 5 s, and a timeout also fails open. | `10-hooks.md` exit-code table; §"Output (Blocking Hooks)"; §"Key Fields" (`timeout`) |
| F10 | `GROK_SESSION_ID` is a runner-injected variable **for hook processes**. The guide does not say whether it is present in a `run_terminal_command` shell. Headless `--session-id <uuid>` lets a launcher fix the id. | `10-hooks.md` §"Environment Variables"; `05-configuration.md` hooks paragraph; `14-headless-mode.md` |
| F11 | `hmad-dispatch exec grok` (from `grok-codex-fallback`) runs grok with `--output-format streaming-json`. That format is a `type`-tagged event stream with **no** `system`/`init` line; the init line belongs to the other format, `streaming-messages-json`. `streaming-json` emits `available_commands` events whose `commands` field is a list of **plain strings**, and each tool call as a `tool_call` event (`toolName`, `rawInput`) followed by `tool_call_update` events carrying `status` (`completed` on success) and `rawOutput`. Measured in the committed log `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson` (at `1ef1a782`): 0 `system` events; 9 `available_commands` events, each with 316 `commands` strings (316 distinct, identical across the 9), `h-mad` and `handoff` among them; a `read_file` call's path is in `rawInput.target_file`, while the chapter's example uses `rawInput.path`. | `14-headless-mode.md` §"streaming-json", §"streaming-messages-json"; `grok-codex-fallback` design §D3 (`gargs`); the committed log |
| F12 | grok memory lives under `~/.grok/memory/` (`MEMORY.md` global/workspace) and not under `~/.claude/projects`. | `13-memory.md` §"Remember", §"Direct Editing" |
| F13 | agy's docs dir has 0 lines matching `session_?id\|sessionId` (case-insensitive), so agy exposes no documented session-id variable. | `grep -rn -i -E 'session_?id\|sessionId' ~/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs \| wc -l` → `0` |
| F14 | This tree holds no codex host document. The codex 0.157.1 binary contains the strings `update_plan`, `request_user_input`, `spawn_agent` and `fork_turns`. Its only `.agents/skills` string occurs in an `external-agent-migration` module context. This host's codex rollouts are observed traces an FR-2 `source` cell may cite: design DP16 reads them (operator-local, uncommitted, versions 0.116.0 to 0.144.1, none at 0.157.1), and the live smoke re-verifies any row resting on one. | `strings "$(readlink -f "$(which codex)")" \| grep -c …`; rollouts: design DP16; see Assumption A2 |

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

  A kind with more than one disjunct carries `reason=` on its failure line, naming **which
  disjunct** of its kind's `meaning` fired (for example `REGISTRY_UNREADABLE reason=bad_id`,
  `TABLE_MISSING reason=heading_twice`). A kind with one disjunct prints none, and its pair is
  `(kind, None)`. A failure is therefore always a `(kind, reason)` pair. The reason values per
  kind are enumerated by the design (§D2) and are part of the contract the AC-3.3 fixtures pin.

  "Hits" and "covered" mean regex match spans, as FR-4 defines them. The gate never invokes a host
  CLI.
- **Acceptance Criteria**:
  - AC-3.1: On the implemented tree the gate passes with zero failures.
  - AC-3.2 (mention is not a mapping): Take a fixture adapter whose table lacks the `advisor` row
    but whose prose mentions `advisor` three times. The gate fails with `ROW_MISSING` for
    `advisor`.
  - AC-3.3 (one fixture per disjunct): Every disjunct of every kind's `meaning` has its own
    fixture, and each fixture asserts that the gate's produced set of `(kind, reason)` pairs
    **equals exactly its own one pair**. The unit is the disjunct, not the kind: a kind whose
    meaning is an alternation gets one fixture per alternative, because a single fixture per kind
    lets a healthy sibling disjunct mask a broken one. At the design's reason inventory that is
    42 kind fixtures: 36 disjunct fixtures (`REGISTRY_UNREADABLE` 15, `TABLE_MISSING` 3,
    `TABLE_MALFORMED` 2, `CELL_EMPTY` 6, and 1 for each of the other 10 kinds) plus 6 split
    fixtures, each of which pins a type or shape case that the disjunct's single fixture leaves
    open. A disjunct may be split into more fixtures; two disjuncts are never merged into one.
    AC-3.2's fixture and AC-3.4's two fixtures are among the 36. Every fixture is one edit to a
    shared clean baseline, and a test asserts that the baseline alone yields no pair, which is
    what makes "exactly its own pair" mean "this edit alone". The count 42 is a **function of the
    reason inventory**: it moves when a reason is added or retired, and the rule, not the number,
    is the AC.
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
  - AC-4.2 (per-branch controls): A4 is itself a three-branch alternation (`~`, `$HOME`,
    `${HOME}`), so the branches controlled are A1, A2, A3 and each of A4's three branches:
    - **Six fixtures, each run with its own branch alone as the whole pattern** and reported
      `UNREGISTERED` against an empty registry: A1 `Foobar(`, A2 `` `FooBar` ``, A3 `CLAUDE_FOO`,
      and the A4 branch fixtures `~/.claude/foo` (A4 with only the `~` branch),
      `$HOME/.claude/foo` (only `$HOME`) and `${HOME}/.claude/foo` (only `${HOME}`).
    - **Removals, with the full union:** removing any one of A1, A2, A3 or A4 makes its own
      fixtures pass (for A4, all three branch fixtures); and each of the **three branch
      removals** (one A4 branch dropped, the other two kept) makes that branch's fixture pass while
      the other two A4 fixtures are still reported.

    That shows each branch discriminates on its own and no healthy sibling covers for it. The
    same rule applies to any axis later rewritten as an alternation: each alternative gets its own
    fixture and its own removal.
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
    5 s default timeout. It also carries the **advisor-warn note**: `h-mad-advisor-warn.sh` is
    registered in the global `~/.claude/settings.json` as a `PostToolUse` hook with matcher `"*"`,
    and it calls `h_mad_context_budget.py` without `HMAD_HOST` (the declaration is inline per
    script call, so it never reaches the hook's environment). Any `CTXBUDGET` text that hook
    injects into a grok session is therefore a Claude transcript's reading, and the orchestrator
    ignores it. The hook does **not** stand down on grok in this feature: it is left unchanged
    (Out-of-Scope). Whether grok fires a `"*"`-matcher hook at all is unverified; the grok smoke
    records how many `CTXBUDGET:` lines its log carries (V-11.5).
  - **Author and reviewer roles.** `spawn_subagent` cannot select `spec-author` or the other
    teammate files by name (F2). The role is carried by putting the agent file's text from
    `$HMAD_SKILL_ROOT/agents/<name>.md` into `prompt`. Its result is collected with
    `get_command_or_subagent_output`. Recursion is capped at one level by the host.
- **Acceptance Criteria**:
  - AC-5.1: Both files exist, contain the string `1.0.41`, and contain `compat.claude.skills`. The
    h-mad file also contains `compat.claude.hooks`.
  - AC-5.2 (TDD gate, h-mad): The grok h-mad adapter contains the halt token
    `step5:grok_tdd_hook_unverified`. It states that Phase 5 halts with that token until a grok
    refusal of a production write has been observed. Its reasons are written from the gate
    **measured at the implementation base `<base>`** (after the rebase, Scope), never from this
    spec's reading of today's tree, because feature `codex-tdd-gate-defects` changes the gate's
    refusal form on a branch its FR-0 selects (its AC-6.5–AC-6.7). Each reason is stated with its
    evidence:
    - (i) **The refusal form, one of three, measured at `<base>`** from the gate's refusal sites
      (`grep -c '^\s*exit 1\s*$' h-mad/hooks/h-mad-tdd-gate.sh`, and a read of each refusal
      site), together with the sibling's recorded FR-0 branch:

      | refusal form at `<base>` | when (sibling FR-0 branch) | reason (i) as written | token the doc test pins |
      |---|---|---|---|
      | `exit 1` (today's form: 5 matching lines at `1ef1a782`) | the sibling has not merged, or `INCONCLUSIVE` (its AC-6.7 leaves the gate unchanged) | the gate refuses by `exit 1`, which grok treats as fail-open (F9) | `exit 1` |
      | (a) rc 2 (`exit 2`), reason on stderr | `E1_BLOCKS` or `E1_DOES_NOT_BLOCK` with only form (a) proven | none: rc 2 (`exit 2`) is grok's documented `PreToolUse` deny (F9). The adapter says so, and the halt rests on (ii) and (iii) | `exit 2` |
      | (b) rc 0, stdout `hookSpecificOutput.permissionDecision == "deny"` | either blocking branch with form (b) proven | none: `hookSpecificOutput.permissionDecision` is grok's canonical decision field (F9, `10-hooks.md` §"Output (Blocking Hooks)"). The adapter says so, and the halt rests on (ii) and (iii) | `permissionDecision` |

      Any other reading at `<base>` (a mix of forms across refusal sites, or a form not in this
      table) halts to the operator before the grok adapter is written; it is never mapped to the
      nearest row. This reason is about grok only. Whether `exit 1` blocks on Claude Code is not
      asserted by this spec: that question is D4 of feature `codex-tdd-gate-defects`
      (`docs/01-plan/features/codex-tdd-gate-defects-brainstorm.md`, commit `76b2501`).
    - (ii) **Holds on every row:** grok nests tool input under camelCase `toolInput` (F8), which
      supplies none of the paths the gate reads. At `1ef1a782` the gate reads a positional
      argument, else a top-level `file_path`/`path` from stdin; on the sibling's branches it reads
      `tool_input.file_path`, then top-level `file_path`, then the positional argument (its spec
      §FR-6 "Payload"). An empty target path takes
      the gate's `[ -z "$TARGET_PATH" ] && exit 0` allow branch. The reason is re-derived from the
      read paths at `<base>`.
    - (iii) **Holds on every row:** the gate may run `pytest` inside grok's 5 s default timeout,
      and a timeout fails open (F9).

    The doc test pins `step5:grok_tdd_hook_unverified`, `toolInput`, `pytest`, and the one
    reason-(i) token of the row measured at `<base>`, which the test module's docstring cites with
    the `<base>` sha.
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
  | any other value | `CTXBUDGET: UNKNOWN reason=unknown_host host=<encoded value>` | 2 |

  - **The value rule** (one rule, shared by this script and FR-9's reader). The comparison is
    **exact**: no whitespace strip and no case fold. Unset, `""` and `claude` are the Claude path;
    exactly `codex`, `agy` or `grok` is a declared host; every other value is unknown, including
    `Grok`, ` grok`, `grok ` and a value holding a newline.
  - **The encoded value** (unknown host only). The value is printed **bare** when the whole value
    matches `^[A-Za-z0-9._-]+$`, tested as a whole-value match (Python `re.fullmatch`, or `\Z` in
    place of `$`): Python's `$` also matches before a trailing newline, so `re.match` with `^…$`
    accepts `zzz\n` and would print a second stdout line. Every other value is printed
    **JSON-encoded** with Python's `json.dumps` defaults: double-quoted, with `"`, `\`, control
    characters and non-ASCII escaped, so the output is always one line and the `host=` token
    never contains a space. So `zzz` prints `host=zzz`, `Grok` prints `host=Grok`, ` grok` prints
    `host=" grok"`, and `zzz` followed by a newline prints `host="zzz\n"`. An unknown value is never
    empty (empty is the Claude path), so the bare form is never `host=`. A declared host is
    always printed bare, as AC-8.1 requires.
  - **Order against the other `UNKNOWN` reasons.** The host check runs immediately after argument
    parsing: before the ceiling default, before the `--window` check that emits `bad_window`, and
    before `resolve_transcript` and `last_context_tokens` (`no_transcript`, `no_usage`). A
    declared or unknown host therefore prints its host line whatever `--window`, `--mode`,
    `--ceiling` or `--transcript` hold, and `bad_window` is reachable only on the Claude path.
    Residual (measured at `1ef1a782`): failures raised **while parsing**, before any statement of
    `main` runs, precede the host check on every host and are unchanged. They are a non-integer
    `--window` (argparse usage error, exit 2, no `CTXBUDGET` line), a non-integer
    `HMAD_CONTEXT_WINDOW` (a `ValueError` traceback while the parser is built, exit 1), an
    invalid `--mode`, a non-float `--ceiling` and an unrecognised option (argparse, exit 2). A
    caller reads the `CTXBUDGET:` token and treats its absence as `UNKNOWN`, never `$?`.

  Host detection by environment markers is rejected on evidence. This Claude Code shell carries
  `CODEX_COMPANION_SESSION_ID`, a plugin variable. A `CODEX_*` marker therefore does not identify
  a codex host, and an inherited `CLAUDECODE` does not identify a Claude one.
- **Acceptance Criteria**:
  - AC-8.1: Set `HMAD_HOST=grok` with a valid Claude JSONL present at the cwd slug and passed via
    `--transcript`. The output is exactly `CTXBUDGET: UNKNOWN reason=host_unsupported host=grok`,
    the exit is 2, and no `used=` substring appears. The same holds per host for `codex` and
    `agy`: one fixture each, run separately.
  - AC-8.2 (unknown value and its encoding): each of these is its own fixture, and each yields
    exactly one stdout line and exit 2: `HMAD_HOST=zzz` → `CTXBUDGET: UNKNOWN reason=unknown_host
    host=zzz` (bare); `HMAD_HOST=Grok` → `host=Grok` (bare; case is not folded); `HMAD_HOST=' grok'`
    → `host=" grok"` (JSON; whitespace is not stripped); `HMAD_HOST` set to `zzz` plus a trailing
    newline → `host="zzz\n"` (JSON; the whole-value-match control that `^…$` under `re.match`
    fails).
  - AC-8.3: The **full existing** `h-mad/tests/test_h_mad_context_budget.py` module runs twice,
    each run read by its pytest summary line: once with `HMAD_HOST` removed from the environment
    (`env -u HMAD_HOST python3 -m pytest -q h-mad/tests/test_h_mad_context_budget.py`) and once
    with `HMAD_HOST=claude` (`HMAD_HOST=claude python3 -m pytest -q …` on the same module). A run
    passes when its summary reports no `failed` and no `error`, and both runs report the same
    `passed` count; a run that collects nothing fails. In addition, the byte-identity probe's
    budget arm shows a sample run's stdout byte-identical to the pre-change script's under both
    values. The probe does not replace the module runs.
  - AC-8.4: Each h-mad non-Claude adapter tells the orchestrator how to read the run-mode ceiling
    on that host. `UNKNOWN` is never read as `OK`. The 80% ceiling is unenforced there, and the
    adapter states whether a **model-accessible** substitute indicator exists:
    - codex and agy: none is documented, and the adapter says so.
    - grok: **no model-accessible indicator exists**, and the adapter says so. The operator's
      `/context` (`04-slash-commands.md` §"`/context`") shows the context window split, but it is
      an interactive slash command the model cannot run or read. The adapter names it as a
      **separate manual action**: the orchestrator may ask the operator to run `/context` and
      report the figure, and it never presents that as an indicator it read itself.
  - AC-8.5 (order against `bad_window`): `HMAD_HOST=grok --window 0` prints
    `reason=host_unsupported host=grok`, and `HMAD_HOST=zzz --window 0` prints
    `reason=unknown_host host=zzz`, each exit 2 and neither printing `bad_window`. With `HMAD_HOST`
    unset, `--window 0` still prints `CTXBUDGET: UNKNOWN reason=bad_window` (today's behaviour).
  - Residual: an orchestrator on a non-Claude host that omits `HMAD_HOST` gets today's behaviour.
    The slug-walk fallback can then measure a Claude transcript for the same cwd. The live smoke
    (FR-11) checks that the adapter's instruction is followed. No mechanism in this feature
    detects the omission itself.
  - Residual (the advisor-warn hook): the global `h-mad-advisor-warn.sh` reaches this script
    without `HMAD_HOST` on every host (FR-5 §"Hooks"), so on grok its `CTXBUDGET` text is a Claude
    transcript's reading. This feature does not change the hook; the grok adapter tells the
    orchestrator to ignore that text, and the grok smoke records its count.

### FR-9: Claims on hosts without a session id

- **Description**: A claim must never run with its collision check silently disabled.
  `h_mad_resume_decision.py` treats a missing `--session-id` as an opt-out and never reports
  `owned_elsewhere` in that case, which is a false clear. Under a declared non-Claude
  `HMAD_HOST`, a call without `--session-id` prints `cannot_judge`, the existing
  not-a-decision token, instead of a routing token.

  - **Value rule.** `HMAD_HOST` is classified by FR-8's exact value rule, shared with the budget
    script. An **unknown** value is treated like a declared non-Claude host here: without a
    session id it prints `cannot_judge`. Falling back to the Claude path would re-open the false
    clear for exactly the caller who mistyped the declaration.
  - **An empty id is no id.** `--session-id ""` is treated as absent, the same truth test the
    existing `_owned_elsewhere` applies.
  - **Order.** The host check is `decide()`'s first statement, before the state-file read, so
    under a declared or unknown host without a session id the answer is `cannot_judge` whatever
    the state file holds: absent, unreadable, feature absent, or feature present. The remedy is
    the same in every case: pass the id.

  The session-id source per host:

  | host | source |
  |---|---|
  | Claude | `CLAUDE_CODE_SESSION_ID` |
  | grok | `GROK_SESSION_ID` when the live smoke has recorded it present in the orchestrator's shell; otherwise a minted id |
  | codex, agy | a minted id |

  A minted id is one `python3 -c 'import uuid; print(uuid.uuid4())'` value, created once at
  bootstrap and written to one file, `"$(git rev-parse --absolute-git-dir)/h-mad-session-id.<feature>"`
  (per checkout and per feature, inside the git directory, so `git status --short` never lists
  it). Every later call reads it from that file inline, so no call relies on a shell variable
  surviving between two host tool calls (design OD-5). The mint runs under `set -C` and never
  overwrites: an existing file prints `SID: NOT_MINTED`, a halt to the operator. The id is used
  for the whole session: as the **value** of `--claim` (`h_mad_state_write.py
  --claim SESSION_ID` takes the id itself), as `--session-id` on every `--beat`, `--set` and
  `--release`, and as `--session-id` on every `h_mad_resume_decision.py` call. Its
  failure modes are stated and conservative: a session that loses its file sees its own claim as
  `owned_elsewhere` until the staleness window lapses, and never gets a false clear; an
  unreadable file reads as an empty id, which is no id, so the oracle answers `cannot_judge`.
- **Acceptance Criteria**:
  - AC-9.1: With `HMAD_HOST=grok` and no `--session-id`, a state file holding a feature owned by a
    live foreign session yields `cannot_judge`. So does a state file with no owner. Each is a
    separate fixture, and `codex` and `agy` each get the same pair. An unknown value
    (`HMAD_HOST=zzz`) gets the same pair, and so does `HMAD_HOST=grok` with `--session-id ""`.
  - AC-9.2: With `HMAD_HOST` unset, every existing `test_h_mad_resume_decision.py` and
    `test_h_mad_feature_lock.py` test passes unchanged. That includes the legacy opt-out
    `test_no_session_id_preserves_legacy_behaviour`.
  - AC-9.3: Each h-mad non-Claude adapter's `session-id-env` row states the minted-id procedure
    and its failure mode.
  - AC-9.4: `h-mad/SKILL.md`'s routing table row for `cannot_judge` already says to stop and not
    initialise. But it names only one cause, a state file that exists and could not be read. The
    row gains the second cause: a declared or unknown non-Claude `HMAD_HOST` value, called
    without a (non-empty) `--session-id`. The
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

  Both new roots are documented host install locations under `.h-mad/invariants.md` §"Skill
  self-containment" as amended at commit `76e7af19` (operator decision): its path exception names
  `~/.claude/...` for Claude Code, `~/.agents/skills/...` for Codex and
  `~/.gemini/config/skills/...` for agy, "each overridable by its documented environment
  variable". `HMAD_AGENTS_SKILLS_DIR` and `HMAD_AGY_SKILLS_DIR` below are those variables.

  The install is a documented operator command in the codex, grok and agy adapters. No script
  links anything: `h_mad_install_check.py` "repairs nothing". `h_mad_install_check.py` gains two
  options, each with the same sibling-repo derivation as today. **Resolution rule** for each
  option's value, applied at call time:
  1. an explicit option on the command line wins, whatever the environment holds;
  2. otherwise, when the override variable (`HMAD_AGENTS_SKILLS_DIR` for
     `--agents-skills-dir`, `HMAD_AGY_SKILLS_DIR` for `--agy-skills-dir`) is **present** in the
     environment, its value replaces the default **even when empty**;
  3. otherwise the home default below.

  A value that is empty after whitespace strip, from either source, is `INSTALL: UNREADABLE`
  (AC-10.3); an empty override variable is never read as "unset, use the default".
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
    `INSTALL: UNREADABLE`, exit 2. The same holds, one fixture each, with no option passed and
    `HMAD_AGENTS_SKILLS_DIR=""`, and with `HMAD_AGY_SKILLS_DIR=""`. An explicit option pointing at
    a `tmp_path` fixture wins over an override variable pointing elsewhere (one fixture per
    option).
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
  - V-11.1: The host's log shows, from its **input events** (what the host asked a tool for,
    never the text a tool returned), both of these:
    - **Adapter read, on every host.** An observed **successful content read** of
      `references/<host>-runtime.md` occurs before the first h-mad script run. A read is an
      observed, successful content read: the host's file-read tool, or `cat`, `head`, `tail`,
      `nl` or a print-only `sed` with the file as an operand. Its event must show success, and
      its returned text must contain the file's first `# ` heading line. On grok the read tool is
      `read_file`, whose `tool_call` names the path in `rawInput` and whose success is a later
      `tool_call_update` with `status` `completed` (F11); codex and agy show success in their own
      log shapes (design §D10). A command that only names the file, such as `test -f`, `echo`,
      `grep -l` or `ls`, is not a read, and neither is a search whose result lists the path. A
      script run is an **execution** of an `h_mad_*.py` script or of `hmad-dispatch` through the
      host's shell tool (an interpreter or direct invocation of the script, design §D10), never a
      mention of its name; a read, `sed` or `grep` whose input merely mentions a script name is
      not a run. At least one run of an `h_mad_*.py` script carries the inline declaration
      `HMAD_HOST=<host>` (none → `FAIL`); an `export HMAD_HOST=…` statement does not count,
      because every adapter asks for the inline form. Residual: a partial read
      whose returned text holds the first `# ` heading line counts as a content read; the smoke
      proves the adapter was opened, not that every line was read. A read through a glob such as
      `references/*.md` does not name the file and fails, which is the conservative direction.
      **Amended 2026-10-01 (operator decision): only a file-read tool proves a read.** Shell
      reads (`cat`, `head`, `sed`, …) above no longer count. What zsh does with a command line
      cannot be bounded from its text: fourteen fresh review rounds kept finding commands that ran
      code or assigned variables through syntax rated read-only (math-evaluated subscripts, glob
      qualifiers, assigning expansions, `printf %d`, `[ -v 'x[N=5]' ]`, …). So:
      - **Codex has no file-read tool**, and its verdict is always
        `UNVERIFIED V-11.1 codex has no file-read tool` (or a shape error). The live codex run was
        already `UNVERIFIED`.
      - **agy `view_file` and grok `read_file` are the only reads credited.** A path names the
        file only if, lexically normalised, it equals `<root>/h-mad/<file>`, or `<link>/<file>`
        for a host loader link passed as `--link`. The smoke verifies every link with
        `readlink -f` before the run, and the live grok run read through the codex link. Nothing
        is resolved on the scoring machine, and no symlink is followed, so a log scores the same
        anywhere. `--home` only expands `~` in `--link` values. A `--link` that is neither
        absolute nor `~/…` is ignored, because it would resolve against the scorer's cwd.
        - A file tool expands neither `~` nor variables; such a spelling is a relative path under
          the root and cannot match.
        - `..` is refused, because through a symlinked component it leaves the directory it
          lexically names.
        - For `view_file`, only `FilePath`/`AbsolutePath` are path parameters, and every one
          present must name the file.
      - **Every credited read needs an untouched filesystem.** Nothing that may have written or
        re-pointed the file can have been *issued* before the read *completed*. Hosts run tools in
        parallel, so a write issued after the read but finished first is still in time. **Every
        shell command counts as a possible write**, because which ones write cannot be bounded
        from command text: process substitution behind a redirect, or glued to `cd;`, was the last
        of many. Unmapped tools, and grok row types or agy event kinds not seen in real logs,
        count as possible writes too. Only file-tool reads and grok's read-only `grep` search are
        exempt, and the taint never resets. In practice the skill and adapter must be read
        through the file tool before the host's first shell command, which is what the adapter
        instructions ask.
      - **Shell commands still decide the ordering and the declaration.** A script or dispatch
        before the adapter read FAILs. `bash`/`zsh -c` is followed only when every argument before
        `-c` is a short option cluster with no `o`/`O` (those take the next word); a `+` or long
        option stops it. For python, `-W`/`-X` take the next word, a short cluster holding `c` or
        `m` ends the search for a script operand, and a long option is not followed. The declaration is judged from text only where text is unambiguous. A
        script's exact prefix token `HMAD_HOST=<value>` counts: another value FAILs, and at least
        one must name this host. Every other occurrence of `HMAD_HOST` in shell text (`env`,
        `export`, `+=`, `read`, even a grep for it) makes the declaration `UNVERIFIED`. `python3 -` and `python3 -c` make an `h_mad_*.py` name a plain argument.

        **Amended 2026-10-01 (operator decision, review round 19): a declaration counts only
        from one canonical event.** Rounds 18 and 19 found command lines that `classify` read as a
        declared run but that never ran the script:
        - text that never runs: a comment, a heredoc body, `false && …`;
        - interpreter options: `python3 -V`/`-h`/`-X`, `bash -n`/`-D`/`-r`/`-o -c`;
        - lines the shell rejects before running anything: `;;`, a leading `;`;
        - a script path that is not h-mad's.

        Round 18's interim rule, that every shell event must be plain, also made the retained
        live grok run `UNVERIFIED`, since real hosts run pipes, heredocs and `$(…)`. So the
        declaration now counts only from a shell event whose **entire text** is

            HMAD_HOST=<host> python3 <script> <args>

        That means single spaces, no interpreter option, no wrapper, no second command, and only
        the characters `A–Z a–z 0–9 _ . / = : , + -` in `<script>` and `<args>`, with no word
        beginning with `=` (zsh expands `=name` and aborts the line when it finds no such command). `<script>` is
        bound the way reads are: lexically it must be `<root>/h-mad/scripts/h_mad_*.py`, or
        `<link>/scripts/h_mad_*.py` for a `--link`, and the file must exist in the checkout. The
        event must also have completed: a grok `completed` update, or an agy `DONE` row.
        - The canonical event must itself be a declaring run: the same event's text must also read
          as an `h_mad_*.py` run carrying `HMAD_HOST=<host>` (amended at review round 20). Matched
          across events, one event satisfying the template while running a `.sh` or `.json` file
          and another event supplying the declaration was a fail-open. Other declaring events may
          take any form. Real hosts also run the adapter's multi-command `$SKILL_ROOT/scripts/…`
          calls, so requiring every declaration to be canonical would make every realistic log
          `UNVERIFIED`.
        - A declaration with no completed canonical declaring event gives
          `UNVERIFIED V-11.1 declaration not in the canonical form`. For codex and agy, a missing
          skill read is still `FAIL`.
        - Another host named in any script's prefix still FAILs.
        - Any other `HMAD_HOST` mention still gives `UNVERIFIED … HMAD_HOST used outside an exact
          declaration`.
        - **Residual:** what other shell events did to the environment, or to how `python3`
          resolves, or to the shell's working directory, is trusted like the starting
          environment. Examples are a function, alias, export or `cd` in a persistent shell. Rehearsal case `R19-residual-prior-event-function` pins
          this, and the mention count still catches a literal `HMAD_HOST` in them.
      - **Event shape is checked.** Each violation is `UNVERIFIED`:
        - a grok `toolCallId` reused across `tool_call`s, or one that is not a string;
        - a grok `tool_call_update` that comes before the `tool_call` it updates (one that never
          has a `tool_call` is an orphan, below);
        - a non-tool agy step on a tool step's index;
        - a non-tool agy step that carries `tool_name` or `tool_info`;
        - an agy `step_update` whose payload is not an object;
        - an agy `step_index` that is not an integer (a boolean is not an integer);
        - an agy tool step whose `DONE` row comes before its `ACTIVE` row;
        - a `view_file` whose `FilePath` or `AbsolutePath` is present but not a string;
        - a shell call carrying a parameter not seen in real logs: an agy `run_command` whose
          parameters are not exactly `CommandLine`, or a grok `run_terminal_command` whose
          `rawInput` has a key other than `command` and `description`. A per-call working
          directory, for one, would change what a relative script path names;
        - a grok `tool_call_update` carrying `rawInput`, or a call with more than one terminal
          (`completed`/`failed`) update (real logs end each call with exactly one);
        - an agy tool step with no index, or with an index reused by a different step.

        A log row that is not UTF-8, is not JSON, repeats a key in any object, or holds an integer
        past Python's digit limit, or nests deeper than 200 levels (so the verdict does not depend on
        how deep the interpreter's decoder can recurse) gives `UNVERIFIED V-11.1 unparseable line N`; for codex it gives
        `codex input shape unobserved`. Rows are split on `\n` only, since JSON may carry U+2028,
        U+2029 or U+0085 raw. Shell text that `shlex` cannot split (an apostrophe in a comment,
        say) is one unknown command. It still taints the filesystem and still counts for the
        ordering, so a read-based `FAIL` stands.

        An agy tool step with no `ACTIVE` row (real logs always pair `ACTIVE` then `DONE`) has no
        known issue time, so it counts as issued at the start of the log.

        An orphan grok `tool_call_update`, of any status, is unmapped.
      - **Lazy exception.** A call need not read the adapter when every event is a file-read tool
        call. Rows that carry no action are allowed too: grok `available_commands`, `thought`,
        `text`, `usage` and `end` rows; agy `init` and `result` events; and agy steps of type
        `agent_response`, `user_input`, `checkpoint` or `system_message`. Its verdict is
        `PASS V-11.1 lazy (no script ran)`, and it still requires the skill load below.
      - **Residuals:**
        - a partial read (grok `offset`/`limit`, agy line ranges) whose output holds the heading
          counts. This is the original V-11.1 residual: it proves the file was opened, not that
          every line was read;
        - the session's starting environment (a login profile sourced before the first event)
          is outside the log and is trusted;
        - a relative file-tool path is taken to be workspace-relative to `--root`.

      Rehearsed by `rehearsal/cases.json`; the history is in the live-smoke addendum.
    - **Skill load.** For codex and agy: an observed successful content read of h-mad's
      `SKILL.md`, by the same predicate; none observed → `FAIL`. For grok: `h-mad` listed in some
      `available_commands` event's `commands` (a list of plain strings, F11) is a
      **precondition only** (not listed → `FAIL`); it shows the skill was offered, not loaded. The
      proof of load is an observed successful read of h-mad's `SKILL.md` in grok's input events,
      by the same predicate. If grok loads the skill in a way its log does not show as such a read,
      the grok arm is **`UNVERIFIED`**: it halts to the operator and never passes.

    The verdict is exactly one of `PASS`, `FAIL` (with the failed clause), `UNVERIFIED` or
    `UNREADABLE`. `UNVERIFIED` is printed for grok's skill load (no observed `SKILL.md` read;
    codex and agy get `FAIL` for the same miss) and for a log the classifier cannot read as keeping
    or breaking the contract: an unparseable line or command, an unobserved input or output shape,
    or an unclassified command that mentions a script before the adapter read. `UNREADABLE`
    (exit 2) means that no verdict exists. Every token except `PASS` halts the smoke for that
    host, and none of the four is read from `$?`. Rehearsal (Phase 6) runs one committed
    hand-made log per clause and direction, including a filename-only mention of the adapter before a script run (→ `FAIL`), a
    `SKILL.md` read whose output mentions a script before the adapter read (→ `PASS`), and a grok
    log listing `h-mad` with no `SKILL.md` read (→ `UNVERIFIED`).
  - V-11.2: The status output names the feature and its `last_completed_phase` / `halt_reason`.
    These equal what `docs/.bkit-memory.json` holds for it, read directly.
  - V-11.3: The run is read-only: `git status --short` (tracked **and** untracked) is identical
    before and after, and the sha256 of `docs/.bkit-memory.json` is unchanged.
  - V-11.4: The session-id probe result is recorded. For grok it decides AC-5.5's branch, present
    or minted.
  - V-11.5: Cost, where the host reports it, is recorded. For grok, the number of lines in its log
    that contain `CTXBUDGET:` is recorded too (the advisor-warn note, FR-5 §"Hooks").

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
- A stand-down of the global `h-mad-advisor-warn.sh` hook on grok, or any other change to that
  hook. The grok adapter tells the orchestrator to ignore its `CTXBUDGET` text (FR-5 §"Hooks",
  FR-8 residual); a hook that detects grok is a separate feature.
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
- A3: codex's rung-1 task tool is unknown at 0.157.1. `update_plan` appears in the binary (F14)
  but has no documentation here, and `codex features list` at 0.157.1 has 0 lines matching
  `todo`, `update_plan` or `task`. It is observed as a call in this host's codex rollouts, but
  only in rollouts of 0.142.0 and older (design DP16: 9 files, 25 `function_call` occurrences),
  so it stays a lead. It becomes the codex `task-tools` mapping only with a cited doc or an
  observed trace at the version the adapter pins.
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
- v1.3: Adopts design v1.0 and design-audit cycle 1 Axis C restatements plus plan v1.2 Next Steps items (2026-09-28, premises at 1ef1a782). F11 and V-11.1: grok evidence is exec grok streaming-json (no init line); available_commands lists h-mad as a precondition only, skill load proven by an observed SKILL.md read or the grok arm is UNVERIFIED; adapter read on every host is an observed successful content read before the first script run, filename-only mentions excluded. AC-3.3: one fixture per disjunct with (kind, reason) pairs, 42 at the design inventory (36 disjunct + 6 splits). AC-4.2: three A4 branch fixtures and three branch removals. AC-5.2: reason (i) from the refusal form measured at base (exit 1 / rc 2 / permissionDecision), doc test pins that row token; F9 adds grok hookSpecificOutput.permissionDecision. FR-8: exact value rule, unknown host bare when the whole value matches ^[A-Za-z0-9._-]+$ else JSON-encoded, host check before bad_window (AC-8.5), AC-8.3 full module twice, AC-8.4 grok has no model-accessible indicator. FR-9: unknown value and empty id give cannot_judge; --claim takes the id as its value. FR-10: env-override resolution rule. Advisor-warn hook does not stand down (Out-of-Scope, V-11.5 records CTXBUDGET lines). Sequencing: agent-substrate.md is read, not edited.
- v1.4: Propagation of design v1.2 (2026-09-28, 34c0e962; no new audit, Phase 4 exited at its round cap). V-11.1: four verdict tokens PASS/FAIL/UNVERIFIED/UNREADABLE, UNVERIFIED for grok's missing SKILL.md read (codex/agy FAIL) and for logs the classifier cannot read, UNREADABLE exit 2 = no verdict; a read is an observed successful content read (file-read tool, cat/head/tail/nl or print-only sed) whose returned text holds the file's first # heading line; at least one h_mad_*.py run carries inline HMAD_HOST=<host>, export does not count. FR-3: reason= only on multi-disjunct kinds, single-disjunct pair is (kind, None). AC-5.2 form (a) reads rc 2 (exit 2). F14 may cite DP16 codex rollouts; A3: update_plan observed only in 0.142.0-and-older rollouts, still a lead. FR-10 cites the amended .h-mad/invariants.md Skill self-containment exception (76e7af19). FR-9: minted id persisted to the git-dir file h-mad-session-id.<feature> under set -C, read inline (OD-5).
