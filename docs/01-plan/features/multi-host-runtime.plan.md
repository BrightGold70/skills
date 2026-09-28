# Plan: multi-host-runtime

## Executive Summary

Ship spec v1.1's host-parity layer for `h-mad` and `handoff` — a committed construct registry, a
file-reading parity gate that counts mapping rows and not mentions, a four-axis catch-all over both
`SKILL.md` files, two grok adapters, parity tables in the four existing codex/agy adapters, an
inline `HMAD_HOST` declaration that makes the context budget and claims answer cannot-judge off
Claude, two new install-check roots, and one read-only live smoke per host — built in a worktree,
rebased onto `codex-tdd-gate-defects` and `grok-codex-fallback` before the 5c baseline, with the
Claude host byte-identical. The live smoke runs in Phase 7 after the local merge into `main` and
before the push, because that is the first moment any host loads this feature's code.

## Overview

Both skills are written in Claude Code's vocabulary, and the codex and agy adapters that translate
it are checked by nothing, so their drift is unmeasured and grok has no adapter at all. This
feature turns "the adapter covers the construct" into a test that fails, and turns the two
Claude-only measurements a non-Claude orchestrator would silently misread (the context budget and
the claim collision check) into explicit cannot-judge answers. It matters now because
`grok-codex-fallback` makes grok a dispatched agent and `codex-tdd-gate-defects` needs codex to find
h-mad under `~/.agents/skills`; neither is safe while a non-Claude host reads Claude-only
instructions unchecked.

## Scope

In scope — the systems spec v1.1 FR-1 to FR-12 touch:

- a new registry, `h-mad/references/host-constructs.json` (FR-1);
- the parity gate and its catch-all, as test code under `h-mad/tests/` (FR-3, FR-4);
- the six adapters `{h-mad,handoff}/references/{codex,agy,grok}-runtime.md`: two new, four
  extended with a `## Construct mapping` table (FR-2, FR-5, FR-6), plus FR-8 / FR-9 / FR-10 text;
- the `## Host runtime` section of `h-mad/SKILL.md` and `handoff/SKILL.md`, and the `cannot_judge`
  row of h-mad's decision-routing table (FR-7, AC-9.4);
- `h-mad/scripts/h_mad_context_budget.py` (FR-8), `h-mad/scripts/h_mad_resume_decision.py`
  (FR-9), `h-mad/scripts/h_mad_install_check.py` (FR-10);
- tests and mutation specs under `h-mad/tests/`, and one autouse fixture appended to the existing
  `h-mad/tests/conftest.py` (FR-10 hermeticity, below);
- the committed probe sidecar `docs/03-analysis/probes/multi-host-runtime/` and the Phase-6
  documents: the gap analysis (AC-4.5, AC-4.6, AC-6.1);
- the live-smoke record `docs/03-analysis/multi-host-runtime.live-smoke.md` (FR-11), written in
  Phase 7.

User-visible behaviour: an orchestrator on codex, agy or grok is routed by `SKILL.md` to its
adapter; an `HMAD_HOST=<codex|agy|grok>` call to the context budget prints
`CTXBUDGET: UNKNOWN reason=host_unsupported host=<value>` (exit 2); a claim under a declared
non-Claude host without `--session-id` prints `cannot_judge`; `h_mad_install_check.py` reports
wrong `h-mad`/`handoff` entries under `~/.agents/skills` and `~/.gemini/config/skills`. A Claude
Code session sees no change.

## Goals

- One committed vocabulary of host-specific constructs, read only by tests — FR-1
- Every adapter carries one machine-readable mapping row per construct declared for its skill — FR-2
- A gate that fails on a missing row even when the construct is mentioned in prose, with a closed
  set of failure kinds, and one fixture per disjunct of each kind — FR-3
- An unregistered Claude-looking construct in either `SKILL.md` fails a test, over four open axes
  with a stated residual — FR-4
- grok adapters that document only where grok diverges, and halt Phase 5 on the unverified TDD
  hook — FR-5
- The codex and agy adapters measured for their gap, then brought to parity — FR-6
- `SKILL.md` routes a grok host to its adapter — FR-7
- The context budget never reports a Claude transcript's reading on a declared non-Claude host,
  when the declaration reaches it (the global advisor-warn hook is a path it does not reach; see
  Risks) — FR-8
- A claim never runs with its collision check silently off — FR-9
- The two new install roots are checked with the existing sibling semantics, and the agy root's
  foreign same-named skills never fail the check — FR-10
- Each host is shown, live, to follow its adapter on one read-only verb, against the merged
  code — FR-11
- The Claude host and every existing pin are unchanged — FR-12

## Requirements

- FR-1: registry file, shape rules, 22 seed ids (re-derived at the implementation base)
- FR-2: one `## Construct mapping` table per adapter, header `| construct | status | mapping | source |`
- FR-3: parity gate with fourteen failure kinds; never invokes a host CLI
- FR-4: catch-all axes A1–A4, the six-suffix exclusion, calibration and residual r1–r6
- FR-5: `h-mad/references/grok-runtime.md`, `handoff/references/grok-runtime.md`; halt token
  `step5:grok_tdd_hook_unverified`
- FR-6: codex and agy adapters to parity; pre-change gap table
- FR-7: `## Host runtime` names all three adapters in both skills
- FR-8: `HMAD_HOST` declaration; `host_unsupported` / `unknown_host`
- FR-9: `cannot_judge` for a declared non-Claude host without `--session-id`; minted-id procedure
- FR-10: `--agents-skills-dir`, `--agy-skills-dir`, the name × state table, `AGY_SIBLING_COLLISION`
- FR-11: one read-only live smoke per host, V-11.1–V-11.5
- FR-12: full coupled suites and byte-identical Claude behaviour

## Implementation Strategy

**Four independent strands, then documentation; the smoke is a Phase-7 step.** (1) The registry
and parity gate (FR-1, FR-3, FR-4) are pure file readers and land first, because every adapter
edit afterwards is checked by them. (2) The three script changes (FR-8, FR-9, FR-10) are leaves
with no dependency on the gate or on each other. (3) The six adapter tables and the grok adapters
(FR-2, FR-5, FR-6) land one adapter at a time. (4) The `SKILL.md` edits (FR-7, AC-9.4) land last
among the tree edits, so the catch-all's AC-7.2 re-run is the final one. The live smoke (FR-11)
does not run in Phase 5 or 6 (§"Convention Prerequisites", "The live smoke").

**RED/GREEN per adapter is per test node, not per suite.** The live-tree assertion is split into
seven nodes: one per adapter file, parametrised over the six adapter paths, each asserting that no
`PARITY` line names that file; and one for the registry-level and `SKILL.md`-level kinds
(`REGISTRY_UNREADABLE`, `DUPLICATE_ID`, `BAD_PATTERN`, `STALE_ENTRY`, `UNDECLARED_SKILL`,
`UNREGISTERED`). The registry node goes GREEN at the end of strand (1). Each adapter node is RED
(`TABLE_MISSING`) from strand (1) until its own adapter lands in strand (3), and turns GREEN then;
the other adapters' nodes stay RED. AC-3.1 is the conjunction of all seven, GREEN only after the
sixth adapter. Before strand (3)'s first adapter edit, the AC-6.1 gap table is taken at `<base>`
(below); it can be rebuilt afterwards from `git show <base>:<adapter>`, and the Phase-6 document
says which sha it read.

**The gate is a helper plus a test module.** The owed module names are fixed here:

- `h-mad/tests/host_parity.py` — the checker, a plain function over explicit paths
  (registry, the two `SKILL.md` files, the six adapters) that returns a list of failures. It is not
  named `test_*`, so pytest does not collect it. It takes the catch-all axes and the exclusion
  suffixes as parameters, which is what AC-4.2 (one axis alone; one axis removed) and AC-4.3 (one
  suffix removed) require. It also exposes the branch expansion used by the seed-coverage probe
  and the branch controls (below), so there is one expansion, not two. It bounds sections with the
  existing fence-aware helper `h-mad/tests/docsections.py` (`titled_section`), never with its own
  `^## ` scan: a fence-blind bound is the measured defect that helper exists for.
- `h-mad/tests/test_host_construct_parity.py` — the live-tree nodes (AC-3.1, AC-4.1) and every
  discriminating fixture (AC-1.1, AC-1.2, AC-3.2–AC-3.4, AC-4.2–AC-4.4, the branch controls).

**AC-3.5 is met by its second arm; the import scan is direct-only.** `docsections.py` imports
`h_mad_doc_block_exec`, which imports `subprocess` (`grep -n '^import\|^from'
h-mad/tests/docsections.py h-mad/scripts/h_mad_doc_block_exec.py`, run at `4152e2be`). So
`host_parity.py` does import a launcher transitively, and the first arm ("imports no subprocess
launcher") cannot be claimed. The owning test is the stubbed-`PATH` arm: executables named
`codex`, `agy` and `grok` on a temporary `PATH` that each write a marker file and exit 99, then the
full gate run, then an assertion that no marker exists. An additional scan asserts that
`host_parity.py` itself has no direct `import subprocess` / `os.system` / `os.popen`; it is stated
as direct-only and is not offered as AC-3.5's evidence.

A search for a colliding name, run at `ae7593a`:
`ls h-mad/tests | grep -i -E 'parity|host|construct'` → 1 file, `test_h_mad_hostile_fixtures.py`
(unit: files; it matches on `host` inside `hostile`). No collision with either chosen name.

**The failure-kind message format** (owed by the spec's v1.0 report) is one line per failure, with
a fixed field order:

```text
PARITY <KIND> file=<repo-relative path> id=<construct id or -> [reason=<disjunct>] [token=<matched text>]
```

The rules, over every kind (so no kind is left without a rule):

| kind | `file=` | `id=` | `reason=` |
|---|---|---|---|
| `REGISTRY_UNREADABLE` | the registry | the element's `id` when it has a valid one, else `-` | always; one token per disjunct (below) |
| `DUPLICATE_ID`, `BAD_PATTERN` | the registry | the entry's `id` | absent |
| `STALE_ENTRY`, `UNDECLARED_SKILL` | the `SKILL.md` the hit count refers to | the entry's `id` | absent |
| `UNREGISTERED` | the `SKILL.md` | `-` | absent; `token=` carries the matched text |
| `TABLE_MISSING` | the adapter | `-` | always: `no_heading`, `no_table`, `heading_twice` |
| `TABLE_MALFORMED` | the adapter | `-` for the header; the row's trimmed first cell when it matches the FR-1 id rule, else `-` | always: `header`, `cell_count` |
| `ROW_MISSING`, `ROW_UNKNOWN_ID`, `ROW_WRONG_SKILL`, `ROW_DUPLICATE`, `STATUS_INVALID` | the adapter | the row's or entry's id | absent |
| `CELL_EMPTY` | the adapter | the row's id | always: `<mapping\|source>:<no_alnum\|tbd\|todo>` |

`<KIND>` is one of the fourteen FR-3 tokens, verbatim. `reason=` exists because four kinds are
disjunctions: a fixture that asserts only the kind cannot tell its own disjunct from a sibling one
(a "missing key" fixture that is accidentally invalid JSON still reads `REGISTRY_UNREADABLE`). The
`REGISTRY_UNREADABLE` reasons are `missing_file`, `invalid_json`, `not_object`, `no_constructs`,
`constructs_not_array`, `element_not_object`, `missing_key:<k>`, `extra_key:<k>`, `bad_id`,
`empty_description`, `empty_skills`, `bad_skill`. The live-tree nodes assert their list is empty
and print every line on failure, so one run shows every gap.

**One fixture per disjunct, and precedence rules that make "that kind alone" constructible.**
AC-3.3 requires each fixture to trigger its kind alone. Four kinds are disjunctions, and several
kinds cascade by construction, so the fixture inventory and the suppression order are fixed here:

- Fixtures, one per disjunct (unit: fixtures): `REGISTRY_UNREADABLE` 15 (missing file; invalid
  JSON; top level not an object; no `constructs` key; `constructs` not an array; an element not an
  object; missing `id`, `pattern`, `skills`, `description` — one each; an extra key; a malformed
  `id`; an empty `description`; an empty `skills`; a `skills` value outside the two names),
  `TABLE_MISSING` 3, `TABLE_MALFORMED` 2, `CELL_EMPTY` 6 (each of `mapping` and `source` × no
  `[A-Za-z0-9]`, `tbd`, `todo`; the `tbd`/`todo` fixtures are spelled in mixed case to prove the
  case-insensitive rule), and 1 each for the other ten kinds: 36 fixtures. AC-1.1's seven registry
  fixtures are members of this set, not additions. The `ROW_MISSING` fixture **is** AC-3.2's
  mention-only fixture (the adapter lacks the `advisor` row and mentions `advisor` three times in
  prose); it is not a second fixture. Each fixture asserts its produced `(kind, reason)` set equals
  exactly its own one pair. The design may split a disjunct further; it may not merge two.
- Suppression order (each rule is a guard, with its own mutation): (a) any `REGISTRY_UNREADABLE`
  stops the run after the registry stage; nothing downstream is computed. (b) An entry with
  `BAD_PATTERN` is excluded from `STALE_ENTRY` and `UNDECLARED_SKILL`, and while any entry is
  `BAD_PATTERN`, `UNREGISTERED` is not computed for the skills that entry declares (coverage is
  unknown, which is not the same as uncovered). (c) An id with `DUPLICATE_ID` is excluded from
  every `ROW_*` kind. (d) An adapter with `TABLE_MISSING`, or with `TABLE_MALFORMED reason=header`,
  yields no `ROW_*`, `STATUS_INVALID` or `CELL_EMPTY` line. (e) A row with
  `TABLE_MALFORMED reason=cell_count` counts as present for its first-cell id (so no `ROW_MISSING`
  for it) and is not checked for `STATUS_INVALID` or `CELL_EMPTY`. Residual: a fixture for a kind
  outside these rules must still be built so that it trips nothing else; the exact-set assertion
  is what catches a fixture that does.

**Controls over alternations get one fixture per branch, run with that branch alone.** The
catch-all is a union of four axes and its exclusion is a union of six suffixes. A healthy sibling
branch covers a broken one in a union test, so AC-4.2 and AC-4.3 are built as the spec states: each
axis's fixture is run with a pattern holding that axis only, and each suffix is removed from the
exclusion alone. The rule applies at every level, not only to the axes:

- **A4 is itself a three-branch alternation** (`~`, `$HOME`, `${HOME}`). The spec's single A4
  fixture `~/.claude/foo` exercises the `~` branch only, and `${HOME}` has 0 occurrences in either
  `SKILL.md` (spec FR-4 calibration). A4 therefore gets three fixtures — `~/.claude/foo`,
  `$HOME/.claude/foo`, `${HOME}/.claude/foo` — each reported `UNREGISTERED` with A4 alone, and each
  passing once its own branch is removed from A4. This goes beyond AC-4.2's text (owed to the spec,
  report). A1–A3 contain no alternation; their `(…)*` / `(…)+` groups are repetition, not branches.
- **Registry patterns.** The branch expansion, over every registry pattern: the three spellings of
  `H` (`~`, `$HOME`, `${HOME}`), every top-level `|`, every `|` inside a group, and every optional
  `(?:…)?` group taken present and absent, as a cartesian product per entry. Not branches (the
  residual): `\b`, lookarounds such as `Stop(?=-hook\b)`, character classes, and repetition. For
  each registry entry the test module holds hand-written literal samples, one per branch; a test
  asserts (i) the sample count equals the entry's branch count, (ii) each sample matches exactly
  one branch of the expansion, and (iii) the entry's full pattern matches every sample. The samples
  are written independently of the patterns, which is what makes (iii) evidence: a misspelled
  branch leaves its sample unmatched, and a dropped or added branch changes the count.
- **The seed-coverage probe reports every branch, and gates nothing.** The spec's gate is per
  entry: every entry has ≥ 1 hit in every skill it declares (`STALE_ENTRY` enforces it). The
  per-branch reading is a report, printed as every branch × declared-skill cell with its
  occurrence count and every zero cell listed; it is not a success criterion, because the zero
  cells are expected (below). Each zero branch is classified in the Phase-6 document as either a
  spelling kept deliberately for generality (its only evidence is its branch control above) or a
  branch to drop (recorded with the registry change).

**Host detection is a declaration, never a sniff.** FR-8 rejects environment-marker detection on
evidence (this Claude shell carries `CODEX_COMPANION_SESSION_ID`). One value rule, shared by both
readers: `HMAD_HOST` is compared **exactly** — no case folding, no whitespace strip. Unset and
empty (`""`) and `claude` take today's code path unchanged; `codex`, `agy`, `grok` are the declared
non-Claude hosts; every other value (including `Grok` and ` grok`) is unknown.

- `h_mad_context_budget.main` reads `HMAD_HOST` immediately after argument parsing and **before**
  the `--window` check and before any transcript lookup. A declared non-Claude host prints
  `host_unsupported` whatever `--window` is; an unknown value prints `unknown_host` whatever
  `--window` is. Reason: a declared host makes every reading impossible, and both paths exit 2.
  The spec does not state the order against `bad_window` (owed, report).
- `h_mad_resume_decision.decide` reads it as its **first statement**, before the state-file read.
  Under a declared non-Claude host with no `session_id`, `decide()` returns `cannot_judge` whatever
  the state file holds — absent, unreadable, feature absent, or feature present. This is the spec's
  literal FR-9 ("a call without `--session-id` prints `cannot_judge`"), and it is the conservative
  choice: the remedy (pass the minted id) is the same in every case. An unknown value is treated
  as a declared non-Claude host (`cannot_judge` without a session id), because falling back to the
  legacy opt-out is exactly the false clear FR-9 exists to remove. The spec does not state the
  unknown-value rule for FR-9 (owed, report).

**Regression is proven against the base, not asserted.** AC-8.3, AC-10.2's second clause and
AC-12.2 compare stdout and exit code between the `<base>` scripts and the implemented scripts on
one committed fixture argv set. That comparison is a committed sidecar probe that takes `<base>`
as an argument, checks `<base>` out into a temporary detached worktree (so each script runs with
its own sibling imports), runs both versions, diffs, and removes the temporary worktree; its
reading at `<base>` goes into the Phase-6 document. It is not a pytest: a test that resolves
`<base>` at run time compares the merged tree to itself once the feature is on `main`. `<base>` is
the commit the feature branch forks from **after** the rebase described in Convention
Prerequisites, recorded in the state record at 5c.

**What we deliberately do not touch:** `h-mad/hooks/h-mad-tdd-gate.sh`,
`h-mad/hooks/h-mad-codex-tdd-gate.py` and `h-mad/hooks/h-mad-advisor-warn.sh` (the first two owned
by the sibling features; this feature documents the grok gap for all three and halts on the TDD
one); `h-mad/scripts/hmad-dispatch.sh` (`exec grok` is consumed, not built);
`h-mad/references/agent-substrate.md` (read for `exec grok`; see Risks); any Claude spelling
inside either `SKILL.md` outside the two located edits; any script that creates, repairs or
overwrites a symlink.

## Verified premises

Each premise below was executed, not reasoned about. One reading at one sha; the command is what a
later reader re-runs. Readings that this feature's own implementation or its rebase will move are
marked **moves**, with when to re-measure. P1–P14 were first run at `ae7593a`. `main` is at
`4152e2be` as v1.1 is written; `git diff --name-only ae7593a 4152e2be -- h-mad handoff | wc -l` → 0
files (run at `4152e2be`): every commit since touches only `docs/`, so every tree premise stands
at `4152e2be`. Re-run at `4152e2be` for v1.1: P1's file diff, P4, P5, P8, the branch census, the
shared-file table, and the baseline failure.

- **P1 — the spec's calibration reproduces, because neither `SKILL.md` has changed since the
  spec measured it.** `git diff --stat 6494b3c HEAD -- h-mad/SKILL.md handoff/SKILL.md` → empty
  output. Then the spec's FR-4 command verbatim, with `HEAD` for `6494b3c`, piped to `wc -l` and to
  `sort -u | wc -l`: `h-mad/SKILL.md` 122 occurrences, 13 distinct tokens; `handoff/SKILL.md` 71
  occurrences, 12 distinct tokens (run at `ae7593a`; the files are unchanged at `4152e2be`).
  **Moves** with any edit to either `SKILL.md`: `grok-codex-fallback` lists `h-mad/SKILL.md` as a
  production file, `codex-tdd-gate-defects`' plan v1.0 edits it (registry entry and gate bullets),
  and this feature's own FR-7 / AC-9.4 edits move it. Re-measure at the post-rebase base (AC-4.6)
  and at 5g.
- **P2 — the 22 seed entries reproduce.** A scratch parser over the spec's seed table (unescape
  `\|`, expand `H`, `re.finditer` on `git show HEAD:<skill>/SKILL.md`), then deleted: 22 entries,
  0 count mismatches, 17 declaring `h-mad`, 12 declaring `handoff` (run at `ae7593a`). Its first
  run reported 2 mismatches that were the parser mis-stripping double-backtick cells, not the
  spec; that is why the probe must be **committed** (Deliverables). **Moves** with either
  `SKILL.md`; re-measure with the committed probe at the post-rebase base.
- **P2b — per-branch seed coverage has zero cells, so it cannot be a gate.** A scratch script
  (the branch expansion above, hand-coded per entry; `re.finditer` on `git show
  4152e2be:<skill>/SKILL.md`; deleted after) read, at `4152e2be`: 13 entries carry branches; 45
  branches; 61 branch × declared-skill cells; 25 zero cells; 14 branches with 0 occurrences in
  every skill that declares them (units as named). The 14 are all `$HOME`/`${HOME}` spellings of
  `H` or the `.local` settings variant. The other 4 zero cells are live elsewhere: `claude-skills-dir`
  `~` in handoff, `claude-settings` `$HOME` without `.local` in handoff, `session-reset-command`
  `` `/compact`` in handoff, `skill-slash-invocation` `` `/h-mad`` in handoff. Why they are zero: the
  seed patterns spell `H` generally so that a future `SKILL.md` edit in another spelling is still
  caught — the zeros are intended, and the branch controls are their only evidence. The committed
  probe must reproduce these figures at `<base>` or explain the difference. **Moves** with either
  `SKILL.md` and with any registry change.
- **P3 — no adapter has a mapping table and the registry does not exist.** `grep -c '^## Construct
  mapping' h-mad/references/*-runtime.md handoff/references/*-runtime.md` → 0 in each of 4 files
  (unit: matching lines per file); `ls h-mad/references/host-constructs.json` → no such file (run
  at `ae7593a`). **Moves** by construction in Phase 5.
- **P4 — `exec` does not accept grok today.** `grep -cE "exec: unknown agent '[^']*' \(expected
  codex\|agy\)" h-mad/scripts/hmad-dispatch.sh` → 1 matching line, in `_cmd_exec`'s agent `case`
  (run at `4152e2be`). For context: `grep -c 'unknown agent'` on the same file → 8 matching lines,
  of which 5 carry the `(codex|agy)` / `(expected codex|agy)` list (`grep -cE "unknown agent
  '[^']*' \((expected )?codex\|agy\)"` → 5); the other three are a message with no agent list, a
  comment, and one that reads `(agy|codex)`. FR-11's grok smoke needs `grok-codex-fallback`
  merged. **Moves** at the rebase; re-measure then.
- **P5 — the TDD gate's block form and payload read.** `grep -c 'exit 1'
  h-mad/hooks/h-mad-tdd-gate.sh` → 5 matching lines; `grep -c 'TARGET_PATH" \] && exit 0'` on it →
  1; `grep -c 'permissionDecision\|tool_input'` on it → 0 (run at `4152e2be`). These are the
  evidence for AC-5.2 reasons (i) and (ii) as the spec states them today. **Moves** if
  `codex-tdd-gate-defects` lands; which way depends on its FR-0 branch (Risks). Re-measure at the
  post-rebase base before the grok adapter is written.
- **P6 — the two script entry points the host declaration must precede.**
  `grep -n 'CLAUDE_CODE_SESSION_ID' h-mad/scripts/h_mad_context_budget.py` → one read of that
  variable; the script's `UNKNOWN` reasons today are `bad_window`, `no_transcript`, `no_usage`
  (`grep -o 'reason=[a-z_]*' h-mad/scripts/h_mad_context_budget.py | sort -u`), emitted in that
  order in `main`: the `--window` check, then `resolve_transcript`, then `last_context_tokens`.
  `resolve_transcript` tries `--transcript`, then `CLAUDE_TRANSCRIPT_PATH`, then
  `CLAUDE_CODE_SESSION_ID` under `~/.claude/projects`, then the cwd-slug walk. In
  `h_mad_resume_decision.decide`, the returns in order are: `start_fresh` for an absent state
  file, `cannot_judge` for an unreadable one, `start_fresh` for an absent feature, then
  `owned_elsewhere` via `_owned_elsewhere`, which returns `False` on an empty session id before
  reading the owner (`grep -n 'return "\|if not session_id' h-mad/scripts/h_mad_resume_decision.py`).
- **P7 — the install check's current surface.** `grep -n 'add_argument\|def check'
  h-mad/scripts/h_mad_install_check.py` → options `--skills-link`, `--hook-link`, `--repo`;
  functions `check_siblings(repo, skills_dir)` and `check(skills_link, hook_link, repo)`.
  `check_siblings` iterates `repo.glob("*/SKILL.md")`, i.e. the **fixture repo's skill names**,
  and looks each up under `skills_dir`. Issue prefixes `SIBLING_NOT_SYMLINK`, `SIBLING_DANGLING`,
  `SIBLING_WRONG_CHECKOUT`, `SPLIT_INSTALL`. Existing tests: `grep -c 'def test_'
  h-mad/tests/test_h_mad_install_check.py` → 23 (unit: matching lines), 7 of them in
  `class TestSiblingSkills`, whose `_repo` helper builds skills named `h-mad` and `handoff` under a
  directory named `checkout`.
- **P8 — the install roots on this machine.** `ls -ld ~/.agents/skills/{h-mad,handoff}
  ~/.gemini/config/skills/{h-mad,handoff}` → all four absent; both parent directories exist;
  `~/.claude/skills/h-mad` and `~/.claude/skills/handoff` are symlinks into
  `/Users/kimhawk/orca/skills`. Collisions with the checkout's top-level skill names:
  `comm -12 <(git ls-files '*/SKILL.md' | awk -F/ 'NF==2{print $1}' | sort -u) <(ls <root> | sort -u)`
  over 316 names → `~/.gemini/config/skills`: 1 name, `debugger`, a plain directory;
  `~/.agents/skills`: 0 names (unit: distinct names; run at `4152e2be`). **Moves** when the
  operator creates the links (the pre-step below) or agy adds a skill.
- **P9 — the located sections exist once each.** `grep -c '^## Host runtime' h-mad/SKILL.md
  handoff/SKILL.md` → 1 and 1; ``grep -c '^| `cannot_judge`' h-mad/SKILL.md`` → 1 (unit: matching
  lines; run at `ae7593a`). AC-7.1 and AC-9.4 locate by these, never by line.
- **P10 — the agy adapters' "typically" sentence.** `grep -n typically h-mad/references/agy-runtime.md
  handoff/references/agy-runtime.md` → one matching line in each, naming
  `~/.gemini/config/skills/<skill>` as the typical load path (run at `ae7593a`). It is false on
  this machine today (P8) and becomes true only once the operator creates the links. FR-6 does not
  name it; this plan carries it as a deliverable.
- **P11 — every host loads the skill from the main checkout.** `readlink -f "$(which
  hmad-dispatch)"` → `/Users/kimhawk/orca/skills/h-mad/bin/hmad-dispatch`; `~/.claude/skills/h-mad`
  resolves into the same checkout (P8), grok lists h-mad as `user [claude]` (spec F5), and the
  adapters set `HMAD_SKILL_ROOT` from the loaded skill path. `docs/.bkit-memory.json` is
  gitignored (`git check-ignore -v docs/.bkit-memory.json` → `.gitignore` rule
  `docs/.bkit-memory.json`; `git ls-files docs/.bkit-memory.json | wc -l` → 0, run at `4152e2be`),
  so a worktree has no state file. Consequence: no host run before the local merge exercises this
  feature's skill text, and the state the status verb reads is the main checkout's.
- **P12 — host versions.** `grok --version` → `grok 1.0.41 (4220f3b224a6) [stable]`;
  `codex --version` → `codex-cli 0.157.1`; `agy --version` → `1.2.12` (run at `ae7593a`). **Moves**
  with any host upgrade; the smoke records the version it ran against.
- **P13 — the status verb is documented read-only.** `grep -n '/h-mad status' h-mad/SKILL.md`
  → the verb table row ("Auto-bootstrap if needed. Read-only. Print state from
  `docs/.bkit-memory.json`.") and the rule "except under `/h-mad status`, which is documented
  read-only and must stay so". FR-11's smoke relies on that.
- **P14 — spec AC census.** `grep -oE '^  - AC-[0-9]+\.[0-9]+[a-z]?'
  docs/01-plan/features/multi-host-runtime.spec.md | sort -u | wc -l` → 50 distinct AC ids;
  `grep -oE '^  - V-[0-9]+\.[0-9]+' … | sort -u | wc -l` → 5 distinct V ids (run at `4152e2be`).
  Moves only if the spec is revised; §"AC ownership" lists every one of the 50.
- **P15 — the global advisor-warn hook reaches the budget script without `HMAD_HOST`.**
  `~/.claude/settings.json` registers `h-mad-advisor-warn.sh` as `PostToolUse` with matcher `"*"`
  (read with a JSON walk over `hooks`, run at `4152e2be`). The hook passes `--transcript` only from
  the payload's `transcript_path` (`grep -n 'transcript_path' h-mad/hooks/h-mad-advisor-warn.sh`),
  and `grep -n -i 'transcript' ~/.grok/docs/user-guide/10-hooks.md` shows no transcript field in
  grok's hook payload. `HMAD_HOST` is inline per script call, so it is not in the hook's
  environment. Unverified: whether grok compiles `"*"` as a matcher and fires the hook.

**Suite baseline.** Commands, at `ae7593a`, with the interpreter the sibling plan pinned
(`which pytest; head -1 "$(which pytest)"` → `/opt/anaconda3/bin/pytest`, shebang
`#!/opt/anaconda3/bin/python`):

```bash
P="/opt/anaconda3/bin/python -m pytest -p no:cacheprovider"
$P --collect-only -q h-mad/tests 2>&1 | tail -1        # reading at ae7593a: 3552 tests collected
$P --collect-only -q handoff/tests 2>&1 | tail -1      # reading at ae7593a: 201 tests collected
$P --collect-only -q handoff/scripts 2>&1 | tail -1    # reading at ae7593a: 140 tests collected
$P --collect-only -q h-mad/tests handoff/tests handoff/scripts 2>&1 | tail -1   # reading at ae7593a: 3893 tests collected
$P -q h-mad/tests handoff/tests handoff/scripts 2>&1 | tail -3
# reading at ae7593a: 1 failed, 3892 passed, 1 warning in 588.67s. The failure is
# h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches,
# which reads the locally installed Claude Code binary; environment-dependent, not this feature's.
```

That one failure was re-run alone at `4152e2be` (`$P -q <that node id>` → `1 failed`): it still
fails, asserting the binary no longer spells the key set `["description","hooks","modules","surface"]`
and that `TOP` in `h_mad_check_plugin_hooks.py` may be stale. Its repair (re-pin `TOP` against the
installed binary) belongs to whoever owns that checker, not to this feature; how it bears on
AC-12.1 is stated in Success Criteria.

`handoff/scripts` is a test root in its own right: `git ls-files handoff/scripts | grep -c 'test_'`
→ 5 files (unit: tracked paths). It is run explicitly, because a run over `h-mad/tests
handoff/tests` alone does not collect its 140 tests. Under this machine's RTK command-rewrite
hook, run collection counts through `rtk proxy` if a bare `pytest` prints a rewritten summary.
Every count here **moves by construction** — this feature adds tests, and both sibling features
add tests to `h-mad/tests` before the rebase. The floor is defined over node ids (Success
Criteria), never over these numbers; re-measure at the post-rebase 5c base and at the pre-merge
gate.

## Architecture Considerations

- **Live-skill coupling.** `~/.claude/skills/h-mad` and `~/.claude/skills/handoff` are symlinks into
  this main checkout (P8). Editing the main working tree edits the installed skill mid-run. The
  feature is built on `feature/multi-host-runtime` in a **git worktree**, and both coupled suites
  run explicitly: `h-mad/tests handoff/tests handoff/scripts`.
- **The new links couple the same checkout to two more roots.** Once the operator creates
  `~/.agents/skills/{h-mad,handoff}` and `~/.gemini/config/skills/{h-mad,handoff}`, codex, grok and
  agy read the **main** tree too. The links point at the main checkout, never at the worktree, so
  no host sees unmerged work — and, by the same fact, no host run before the local merge measures
  this feature (P11). That is why the smoke sits between 7f and 7e.
- **Skill self-containment.** The registry lives in `h-mad/references/`, and only tests read it
  (FR-1). `handoff` gains no read of any `h-mad` file at runtime. The handoff adapters' tables name
  construct ids as strings only. Test-side cross-reads have precedent (spec Assumption A5).
- **The gate reads files only.** No test and no script invokes codex, agy or grok (spec Scope;
  `invariants.base.md` §"No new external dependency"). AC-3.5 is owned by the stubbed-`PATH` test
  (Implementation Strategy).
- **Existing forbidden-token tests constrain the adapter text.** `test_h_mad_codex_runtime.py` and
  `test_handoff_codex_runtime.py` forbid Claude spellings in the codex adapters (spec FR-12,
  AC-6.6). The construct ids are kebab-case so that a mapping row never spells a forbidden token;
  the `mapping` and `source` cells must also avoid them.
- **One declaration, two scripts.** `HMAD_HOST` is read by two scripts under the one value rule in
  Implementation Strategy. One test feeds each value — unset, `""`, `claude`, `codex`, `agy`,
  `grok`, `zzz`, `Grok`, ` grok` — to both and asserts the same class from each (Claude path,
  declared non-Claude, unknown), where "unknown" means `unknown_host` for the budget and
  `cannot_judge` (without a session id) for `decide()`.
- **Install-check hermeticity is an interface, not a coincidence.** The existing tests read
  whatever the new roots' defaults resolve to. Their fixture repo's skill names are `h-mad` and
  `handoff` (P7) — exactly the two names the operator links under both new roots — so once the
  links exist, `test_the_cli_reports_a_sibling_copy_as_a_verdict_not_an_error` (CLI) would print
  extra `SIBLING_WRONG_CHECKOUT` lines, and `test_the_sibling_root_is_derived_one_level_up_from_the_link`
  would too if `check()` read the new roots by default. Both still pass (`in` / `any`), which is
  what makes the drift silent: their stdout and `issues=N` change, breaking AC-10.2 and AC-12.2.
  The rule that closes this for every existing and future test:
  - `check()` gains keyword parameters `agents_skills_dir=None` and `agy_skills_dir=None`; `None`
    means that root is not checked. Every existing direct caller of `check()` is unchanged by
    construction.
  - `main()` resolves each new option's default **at call time** from an environment override,
    `HMAD_AGENTS_SKILLS_DIR` and `HMAD_AGY_SKILLS_DIR`, falling back to `~/.agents/skills` and
    `~/.gemini/config/skills`. An explicit option always wins.
  - One autouse, function-scoped fixture appended to `h-mad/tests/conftest.py` sets both
    variables to non-existent paths under `tmp_path`. Every subprocess inherits them, so no test
    in `h-mad/tests` reads a real host root, whatever links exist.
  - A positive control proves the override is read: with `HMAD_AGENTS_SKILLS_DIR` pointed at a
    `tmp_path` root holding a wrong `h-mad` link, the CLI run with no new option reports
    `SIBLING_WRONG_CHECKOUT` naming that root. A default control, with both variables deleted
    inside the test, asserts the resolved defaults are the two documented paths.
  The env overrides are an interface the spec's FR-10 does not name, and the spec's hermeticity
  residual is measured on the wrong axis (the checkout directory name, not the fixture skill
  names); both are owed to the spec (report).

## Deliverables

| Deliverable | Target file(s) | Satisfies |
|---|---|---|
| Registry with the seed entries re-derived at the post-rebase base | `h-mad/references/host-constructs.json` (new) | FR-1 |
| Parity checker (paths, axes and exclusion suffixes as parameters; branch expansion; section bounds via `docsections.py`) | `h-mad/tests/host_parity.py` (new, not collected) | FR-3, FR-4 |
| Live-tree nodes (six adapter nodes, one registry/`SKILL.md` node); the 36 disjunct fixtures, the ROW_MISSING one being AC-3.2's; the suppression-rule fixtures; the stubbed-`PATH` AC-3.5 test; 4 axis-alone controls plus the two further A4 branch controls; 6 suffix controls; the per-branch registry sample test; the `TeamCreate` fixture; the AC-1.2 seed-id test | `h-mad/tests/test_host_construct_parity.py` (new) | FR-1, FR-3, FR-4 |
| `## Construct mapping` table in each existing adapter, plus FR-8 / FR-9 / FR-10 text | `h-mad/references/codex-runtime.md`, `h-mad/references/agy-runtime.md`, `handoff/references/codex-runtime.md`, `handoff/references/agy-runtime.md` | FR-2, FR-6, FR-8, FR-9, FR-10 |
| The "typically `~/.gemini/config/skills/<skill>`" sentence reworded to name the FR-10 install path (owed by the spec report) | `h-mad/references/agy-runtime.md`, `handoff/references/agy-runtime.md` | FR-6, FR-10 |
| grok adapters with version pin, compat toggles, trust, hooks, roles, halt token, table; the h-mad one also states that the global advisor-warn hook's `CTXBUDGET` text on grok is a Claude transcript's reading and must be ignored (P15) | `h-mad/references/grok-runtime.md`, `handoff/references/grok-runtime.md` (new) | FR-2, FR-5, FR-8 |
| `## Host runtime` names all three adapters | `h-mad/SKILL.md`, `handoff/SKILL.md` | FR-7 |
| `cannot_judge` row gains the second cause | `h-mad/SKILL.md` (decision-routing table) | FR-9 (AC-9.4) |
| `HMAD_HOST` read first in `main`, before the `--window` check; `host_unsupported`, `unknown_host` | `h-mad/scripts/h_mad_context_budget.py` | FR-8 |
| `HMAD_HOST` read as `decide()`'s first statement; `cannot_judge` without a session id under a declared or unknown host | `h-mad/scripts/h_mad_resume_decision.py` | FR-9 |
| `--agents-skills-dir`, `--agy-skills-dir` with call-time env-overridable defaults; `check()` keyword roots defaulting to `None`; the name × state rule; sorted `AGY_SIBLING_COLLISION` detail lines after the verdict block | `h-mad/scripts/h_mad_install_check.py` | FR-10 |
| Autouse fixture pointing both env overrides at non-existent `tmp_path` paths (appended; no existing line changed) | `h-mad/tests/conftest.py` | FR-10, FR-12 |
| Doc tests for AC-2.3–AC-2.5, AC-5.1–AC-5.7, AC-6.3–AC-6.5, AC-7.1, AC-7.3, AC-8.4, AC-9.3, AC-9.4, AC-10.4 and the advisor-warn note, each locating its section by heading and failing (never skipping) when the heading is absent | `h-mad/tests/test_host_runtime_docs.py` (new) | FR-5, FR-6, FR-7, FR-8, FR-9, FR-10 |
| Host-declaration tests for both scripts (below), and the shared-value-set agreement test | `h-mad/tests/test_h_mad_host_declaration.py` (new) | FR-8, FR-9 |
| Install-check root tests (AC-10.1, AC-10.3, AC-10.5, AC-10.6, the absent-roots pin, the override and default controls), passing both new options explicitly except in the two controls | `h-mad/tests/test_h_mad_install_check_roots.py` (new) | FR-10 |
| Mutation specs for the guards (Success Criteria) | `h-mad/tests/mutation-specs/` (new JSON, or new rows in `context_budget.json`, `resume_decision_cannot_judge.json`, `install_check_siblings.json`) | FR-3, FR-4, FR-8, FR-9, FR-10 |
| Probe sidecar: the FR-4 calibration command; the seed-coverage probe reporting hits per entry and per branch × declared skill with every zero cell listed; the byte-identity probe; each taking the sha as an argument | `docs/03-analysis/probes/multi-host-runtime/` (new) | FR-1, FR-4, FR-8, FR-10, FR-12 (AC-4.5, AC-4.6, AC-8.3, AC-10.2, AC-12.2) |
| Pre-change gap table (construct × adapter, `addressed`/`absent`, with its sha), the AC-4.6 record, the branch classification and the byte-identity reading | Phase-6 analysis document | FR-4, FR-6 (AC-4.5, AC-4.6, AC-6.1), FR-12 |
| Live-smoke record, one section per host | `docs/03-analysis/multi-host-runtime.live-smoke.md` (new, written and committed in Phase 7 on `main` before 7e) | FR-11 |

Host-declaration fixtures, named here because two of them are what kill W1's ordering mutants:
per host in `codex agy grok`, run separately — (a) AC-8.1's valid-transcript fixture; (b) no
resolvable transcript (`--transcript` naming a non-existent file, `CLAUDE_TRANSCRIPT_PATH` and
`CLAUDE_CODE_SESSION_ID` unset, `HOME` pointed at an empty `tmp_path`), expecting
`host_unsupported` where a check placed after the lookup prints `no_transcript`; (c) a transcript
with no usage record, expecting `host_unsupported` where a check placed after the usage read prints
`no_usage`; (d) `--window 0`, expecting `host_unsupported`. Plus `zzz`, `Grok` and ` grok` →
`unknown_host`. For `decide()`, per host: AC-9.1's pair, plus an absent state file, an unreadable
state file and an absent feature, each expecting `cannot_judge`.

The new test file names were checked against the tree at `ae7593a`:
`ls h-mad/tests/test_host_construct_parity.py h-mad/tests/test_host_runtime_docs.py
h-mad/tests/test_h_mad_host_declaration.py h-mad/tests/test_h_mad_install_check_roots.py
h-mad/tests/host_parity.py` → none exists. Existing mutation specs that cover the three touched
scripts: `ls h-mad/tests/mutation-specs | grep -i -E 'budget|resume|install'` →
`context_budget.json`, `context_budget_docs.json`, `install_check_siblings.json`,
`resume_decision_cannot_judge.json` (unit: files).

## AC ownership

Every one of the 50 spec AC ids (P14) has exactly one owner here; a test module owns it, or a
record does. An AC named nowhere is the defect this table exists to prevent.

| AC ids | Owner |
|---|---|
| AC-1.1, AC-1.2, AC-3.1–AC-3.5, AC-4.1–AC-4.4 | `test_host_construct_parity.py` (AC-1.2: a test asserting the committed registry holds every seed id, or that the AC-4.6 record names the retirement) |
| AC-2.1, AC-2.2, AC-6.2, AC-7.2 | `test_host_construct_parity.py`'s live-tree nodes (the gate's `ROW_*`, `CELL_EMPTY` and `UNREGISTERED` checks are these ACs) |
| AC-2.3–AC-2.5, AC-5.1–AC-5.7, AC-6.3–AC-6.5, AC-7.1, AC-7.3, AC-8.4, AC-9.3, AC-9.4, AC-10.4 | `test_host_runtime_docs.py` |
| AC-6.6, AC-9.2 | the existing `test_h_mad_codex_runtime.py`, `test_handoff_codex_runtime.py`, `test_h_mad_resume_decision.py`, `test_h_mad_feature_lock.py`, unchanged, in the full suite |
| AC-8.1, AC-8.2, AC-9.1 | `test_h_mad_host_declaration.py` |
| AC-8.3 | the existing `test_h_mad_context_budget.py` run twice in the full-suite gate, once with `HMAD_HOST` unset and once with `HMAD_HOST=claude` exported for that run; plus the byte-identity probe |
| AC-10.1, AC-10.3, AC-10.5, AC-10.6 | `test_h_mad_install_check_roots.py` |
| AC-10.2 | first clause: the existing `test_h_mad_install_check.py`, unchanged, under the conftest override; second clause: the byte-identity probe at `<base>`, plus a permanent pin in `test_h_mad_install_check_roots.py` that the absent-roots run prints no line naming either root and no `AGY_SIBLING_COLLISION:` line |
| AC-4.5, AC-4.6, AC-6.1 | the Phase-6 analysis document |
| AC-12.1 | the full coupled suite (Success Criteria) |
| AC-12.2 | the byte-identity probe, its reading in the Phase-6 document |

V-11.1–V-11.5 are owned by the live-smoke record.

## Connection enforcement

Three deliverables are connections: an existing entry point must reach a new branch. Each is a
`wiring`-shaped task with a `WIRE` / `WIRE-PIN`, and Phase 5 runs the wire-scoped revert — remove
the call site only, callee and tests intact — plus the force-fire mutation in the other direction
(`invariants.base.md` §"Connection enforcement").

| Wire | Call site → callee | `WIRE-PIN` (remove) | Force-fire must fail |
|---|---|---|---|
| W1 | `h_mad_context_budget.main` → host check, first after argument parsing | AC-8.1 fails: a Claude reading (`used=`) is printed under `HMAD_HOST=grok` | host check returns `host_unsupported` whatever the value → the existing `test_h_mad_context_budget.py` tests fail (e.g. `test_ok_below_the_ceiling` asserts `returncode == 0` and a token starting `CTXBUDGET: OK `) |
| W2 | `h_mad_resume_decision.decide` → host check, its first statement | AC-9.1 fails: the no-owner fixture routes instead of printing `cannot_judge` | host check fires with `HMAD_HOST` unset → `test_h_mad_feature_lock.py::TestResumeDecisionSurfacesOwnership::test_no_session_id_preserves_legacy_behaviour` fails |
| W3 | `h_mad_install_check.main` → `check(..., agents_skills_dir=…, agy_skills_dir=…)` → the two new root checks | AC-10.1 and AC-10.5 fail: a wrong entry under either root is not reported | the agy root's issue rule applied to every name → AC-10.5's `debugger` cells fail (`INSTALL: FAIL` where `PASS` plus one detail line is required); the agy rule applied to the `--skills-link` parent → AC-10.6 fails (no `SIBLING_NOT_SYMLINK` for `debugger`) |

A force-fire is valid only if its named test's input contains what the mutated condition keys on;
each row above was checked against that rule by reading the named test's fixture, not by running a
mutant (the mutants cannot exist before the code does). Residual: whether each force-fire kills is a
prediction until Phase 5 runs it.

**Ordering mutants are killed by inputs that separate the orders, not by the WIRE-PIN.** Moving
W1's host check after the transcript lookup still prints `host_unsupported` on AC-8.1's fixture,
because that fixture's lookup succeeds; the mutant is equivalent there. The rule, over the class:
for every `UNKNOWN` reason the host check must precede, one fixture makes that earlier step fail
under a declared host — fixtures (b), (c), (d) above for `no_transcript`, `no_usage`,
`bad_window`. For W2 the same rule gives the absent-file, unreadable-file and absent-feature
fixtures. Each ordering mutant is run through the mutation harness, which confirms the mutant
landed (its baseline and anchor checks) before scoring it.

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| `grok-codex-fallback` and `codex-tdd-gate-defects` both edit `h-mad/SKILL.md` and may add Claude constructs | The seed registry and calibration are stale at the real base; the catch-all fails or a new token is registered wrongly | Rebase before 5c; re-run the committed calibration and seed-coverage probes at the new base (AC-4.6); a false hit is fixed by narrowing an axis with a new control, never by registering a non-construct |
| `codex-tdd-gate-defects` changes the Claude TDD gate, on one of three branches its FR-0 selects | AC-5.2's reasons (i) and (ii) may be false at `<base>`; which ones depends on the branch | Per branch, at `<base>` (sibling spec AC-6.5–AC-6.7): **`E1_BLOCKS`** (AC-6.6) and **`INCONCLUSIVE`** (AC-6.7) keep `exit 1`, so reason (i) stands as the spec states it. **`E1_DOES_NOT_BLOCK`** (AC-6.5) replaces it: form (a), rc 2, is grok's documented deny (F9), so reason (i) is false; form (b), rc 0 plus `hookSpecificOutput.permissionDecision == "deny"`, is not a grok-documented deny form (F9 documents exit 2 and a stdout `{"decision":"deny"}`), so reason (i) becomes "deny form undocumented on grok". Reason (ii): the sibling's payload read (its OD-4) reads `tool_input.file_path`, then top-level `file_path`, then argv; grok's camelCase `toolInput` (F8) supplies none of them, so reason (ii) is re-pointed, not removed. This plan does **not** restate AC-5.2. Re-run P5 at `<base>` and read the sibling's recorded FR-0 branch; if the result differs from the spec's AC-5.2 text, the spec's AC-5.2 and its doc test are revised from that measurement before Phase 5 writes the grok adapter (owed to the spec, report). The halt token `step5:grok_tdd_hook_unverified` stays in every branch |
| `codex-tdd-gate-defects` adds a shared judge script that the Claude gate calls | AC-5.2 reason (iii) (pytest inside grok's 5 s timeout) may change in cost | Re-read the gate at the post-rebase base; reason (iii) is stated against that tree |
| Sequencing with `codex-tdd-gate-defects` over `~/.agents/skills/h-mad` | That feature's spec §"Live verification" V-1 bullet says the install "is owned by feature `multi-host-runtime`, and V-1 cannot run until it lands", and its plan v1.0 §"Requirements" says V-1 "is blocked on `multi-host-runtime`", while the merge order puts that feature first — a cycle if "lands" means "merges" | Broken by the operator pre-step (Convention Prerequisites): the four links are created before, and independently of, any merge. They point at `main` and need no feature code. V-1 needs the link to exist, not this feature merged. This feature's FR-10 adds only the install-check and the adapter docs. Owed to the sibling spec and plan: V-1's dependency is restated as "needs the operator-created `~/.agents/skills/h-mad` link (pre-step in `multi-host-runtime`'s plan), not `multi-host-runtime` merged" (report) |
| The spec says this feature edits `h-mad/references/agent-substrate.md`, but no FR names it | A rebase conflict is expected where none exists, or an unplanned edit appears | `grep -n agent-substrate docs/01-plan/features/multi-host-runtime.spec.md` → only the sequencing bullet (unit: matching lines, 2; run at `ae7593a`). The plan treats the file as read-only here; raised to the spec |
| A seed pattern's branch is dead, hidden by a live sibling branch | A construct's rename goes unnoticed; the entry stays green on the other branch | The per-branch sample test (Implementation Strategy) proves every branch live against a literal sample; the probe prints every zero cell (P2b) and the Phase-6 document classifies each |
| Existing install-check tests read the real new roots | Once the operator's links exist, their stdout changes while they still pass (AC-10.2, AC-12.2 broken silently) | The conftest env override, the `None`-default `check()` keywords, and the override and default controls (Architecture Considerations). The byte-identity reading is taken with the four links present, and the Phase-6 record states `ls -ld` of all four |
| A non-Claude orchestrator omits `HMAD_HOST` (spec FR-8 residual) | The slug walk measures a Claude transcript for the same cwd | The adapters instruct the inline declaration; the live smoke checks it is followed. No mechanism detects the omission (spec Out-of-Scope) |
| On grok, the global advisor-warn hook injects a `CTXBUDGET` verdict computed from the newest Claude transcript for the cwd (P15) | FR-8's goal fails on a path the declaration does not reach: the grok orchestrator reads a Claude reading as its own | The h-mad grok adapter states it and says to ignore that text (doc test); the grok smoke records whether any `CTXBUDGET:` text appears in its log. A hook-side stand-down is out of this plan's FR set; whether the spec adds one is owed to the spec (report) |
| The smoke measures pre-feature code and reads as a pass (P11) | FR-11's evidence is about the wrong tree | The smoke runs only after 7f's local merge, and asserts `main`'s `HEAD` is that merge, that the feature tip is its ancestor, and that each host's skill link resolves to `main`'s `h-mad` (Convention Prerequisites) |
| codex does not load skills from `~/.agents/skills` (spec Assumption A2) | The codex smoke cannot find h-mad | The smoke halts, the merge is reverted, and the spec's A2 is corrected; never a pass |
| A host cannot run (absent, unauthenticated, out of quota, deadline, non-zero rc, no final message) | No evidence for that host | Each run is bounded by `--timeout`; any of these halts. Nothing is pushed on "not run" (spec FR-11); the unpushed merge is reverted |
| A failed or halted smoke leaves unverified code on `main`, which every host loads | Four host roots serve unverified skill text | `git revert -m 1` of the unpushed merge commit, never `reset --hard`; halt to the operator. Re-integration after the cause is cleared is a revert of that revert: a second 7f of the same tip reports `nothing_to_integrate` |
| The feature edits the live skill | A run in flight reads a half-built skill | Worktree; both coupled suites before merge |
| A pre-existing test is deleted or edited while the count stays green | FR-12's guarantee silently false | Node-id floor and append-only numstat check (Success Criteria) |

## Convention Prerequisites

- **Merge order (hard): `codex-tdd-gate-defects`, then `grok-codex-fallback`, then this feature.**
  The sibling plan `docs/01-plan/features/codex-tdd-gate-defects.plan.md` v1.0 states the same
  order. `git branch -a | grep -E 'grok|codex-tdd|multi-host'` → no output and `git worktree list`
  → the main checkout only (run at `ae7593a`), so both siblings are ahead in the queue, not in
  flight on a branch.
- **Operator pre-step, independent of any merge: the four install links.** The operator creates
  `~/.agents/skills/h-mad`, `~/.agents/skills/handoff`, `~/.gemini/config/skills/h-mad` and
  `~/.gemini/config/skills/handoff` as symlinks to `/Users/kimhawk/orca/skills/h-mad` and
  `/Users/kimhawk/orca/skills/handoff`, with `ln -s`, never over an existing non-symlink (re-run P8
  first, since agy may add a skill). The links point at `main` and need no feature code, so they
  can be created before any of the three features merges; `codex-tdd-gate-defects`' V-1 needs only
  that they exist. Once they exist, codex and agy load `main`'s pre-feature adapters; that is the
  operator's call. This feature ships the install-check for them (FR-10) and the documented
  commands in the adapters (AC-10.4); it creates nothing. Observed verification that the pre-step
  was done: `ls -ld` of the four paths shows four symlinks, and `readlink -f` of each prints the
  matching `/Users/kimhawk/orca/skills/<skill>`.
- **Shared files.** Derived from the sibling documents, not from memory, at `4152e2be`:
  `grok-codex-fallback` from its impl-plan (`grep -oE '\*\*(Production|Test) file\*\*:.*'
  docs/01-plan/features/grok-codex-fallback.impl-plan.md | grep -oE '`[^`]+`' | tr -d '`' | sort -u
  | grep -v /tests` → 10 paths); `codex-tdd-gate-defects` from its plan v1.0's file table (the
  table rows starting `` | `h-mad/`` in `docs/01-plan/features/codex-tdd-gate-defects.plan.md`,
  first two columns). Rows below are the files this feature touches or reads:

  | File | This feature | `grok-codex-fallback` | `codex-tdd-gate-defects` |
  |---|---|---|---|
  | `h-mad/SKILL.md` | edits (FR-7, AC-9.4) | edits (production file) | edits (registry entry for its judge; gate prose) |
  | `h-mad/references/codex-runtime.md` | edits (FR-2, FR-6, FR-8–FR-10) | not named | edits §"Trust boundary" |
  | `h-mad/references/agy-runtime.md` | edits (FR-2, FR-6, the "typically" sentence) | not named | edits one sentence (if its form (b)) |
  | `h-mad/hooks/h-mad-tdd-gate.sh` | reads; the grok adapter states its behaviour (AC-5.2) | edits (production file) | edits (payload read, judge call, blocking form) |
  | `h-mad/hooks/h-mad-codex-tdd-gate.py` | reads; the codex adapter's hook rows cite it | not named | edits (imports the shared judge) |
  | `h-mad/hooks/h-mad-advisor-warn.sh` | reads (P15) | not named | not named |
  | `h-mad/scripts/hmad-dispatch.sh` | reads; FR-11 consumes `exec grok` | edits (production file) | not named |
  | `h-mad/references/agent-substrate.md` | reads (`exec grok` verb docs) | edits §"Verbs" per its spec FR-10 (not listed as an impl-plan production file) | not named |
  | `h-mad/tests/` | adds files; appends to `conftest.py` | adds files | adds files |

  Textual overlaps: `h-mad/SKILL.md` (all three), `h-mad/references/codex-runtime.md` and
  `h-mad/references/agy-runtime.md` (this feature and `codex-tdd-gate-defects`). Semantic overlaps
  — files this feature documents but does not edit — are the two TDD hooks, `hmad-dispatch.sh` and
  `agent-substrate.md`; a rebase shows no conflict there, so each is re-read at the new base (P4,
  P5). The sibling plan notes this plan's v1.0 table said it does not name `h-mad/SKILL.md`; the
  row above is re-derived from its plan and corrects that.
- **Rebase, then baseline.** Branch `feature/multi-host-runtime` as a **git worktree**
  (`hmad-dispatch worktree-create` or `git worktree add`). Before the 5c baseline, rebase onto
  `main` after both siblings have merged, record that fork sha as `<base>`, and at `<base>`:
  re-run P1 (calibration, via the committed probe), P2 and P2b (seed coverage, via the committed
  probe), P4, P5 (with the sibling's recorded FR-0 branch), P6, P9, P15 and the suite baseline;
  write the AC-4.6 record into the Phase-6 document; take the AC-6.1 gap table; and capture the
  node-id list for the floor.
- **Codex authors Phase 5 under the TDD gate**, RED before GREEN per test node. The grok adapter's
  halt token applies to a grok-hosted Phase 5, not to this feature's own build.
- **No AC and no pytest test makes a live model call.** The smoke is a verification step (FR-11).
- **The live smoke — Phase 7, after 7f's local merge and before 7e's push.** Hosts load h-mad
  through links into the main checkout (P11), so only once 7f has merged the feature branch into
  local `main` does a host run exercise this feature's code; no earlier smoke tests this feature.
  Order: 7d commit → 7f integrate with `--route merge --apply` → if 7f reports `identity=n`, the
  full coupled suite on `main` → the smoke for each host in `codex agy grok` → the smoke record
  written and committed on `main` (docs only) → 7e push. The Phase-7 gate runs before 7d and does
  not see the smoke; the smoke block below is its own gate. Every pass condition is an executable
  assertion that stops on failure; `set -e` is inert in the Bash tool's top-level shell, so each
  carries an explicit `|| … exit 1`:

  ```bash
  REPO=/Users/kimhawk/orca/skills; H=<codex|agy|grok>; F=multi-host-runtime
  MERGE=<7f merge commit sha>; TIP=<feature branch tip sha>; S=$(mktemp -d)
  D="$REPO/h-mad/bin/hmad-dispatch"   # then write $S/prompt.txt (below)
  test "$(git -C "$REPO" rev-parse HEAD)" = "$MERGE" || { echo "HALT main is not at the 7f merge"; exit 1; }
  git -C "$REPO" merge-base --is-ancestor "$TIP" HEAD || { echo "HALT feature tip not merged"; exit 1; }
  test -z "$(git -C "$REPO" branch -r --contains "$MERGE")" || { echo "HALT merge already pushed"; exit 1; }
  case "$H" in codex) L=~/.agents/skills/h-mad;; agy) L=~/.gemini/config/skills/h-mad;; grok) L=~/.claude/skills/h-mad;; esac
  test "$(readlink -f "$L")" = "$REPO/h-mad" || { echo "HALT $L does not load $REPO/h-mad"; exit 1; }
  test -f "$REPO/h-mad/references/$H-runtime.md" || { echo "HALT adapter absent from main"; exit 1; }
  M="$REPO/docs/.bkit-memory.json"; test -f "$M" || { echo "HALT no state file"; exit 1; }
  rec() { python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))["orchestrator_state"][sys.argv[2]], sort_keys=True))' "$M" "$F"; }
  B_REC=$(rec) && test -n "$B_REC" || { echo "HALT feature record unreadable"; exit 1; }
  git -C "$REPO" status --short > "$S/before" || { echo "HALT git status"; exit 1; }
  "$D" exec "$H" "$S/prompt.txt" --cd "$REPO" --out "$S/out" --log "$S/log" --timeout 900; RC=$?
  test "$RC" -eq 0 || { echo "HALT rc=$RC (124 = deadline)"; exit 1; }
  test -s "$S/out" || { echo "HALT no final message"; exit 1; }
  git -C "$REPO" status --short > "$S/after" || { echo "HALT git status"; exit 1; }
  cmp -s "$S/before" "$S/after" || { echo "FAIL V-11.3 tree moved"; exit 1; }
  A_REC=$(rec) && test "$A_REC" = "$B_REC" || { echo "FAIL V-11.3 feature record moved or unreadable"; exit 1; }
  grep -q -F "$F" "$S/out" || { echo "FAIL V-11.2 feature not named"; exit 1; }
  ```

  The V-11.3 state observable is `orchestrator_state[$F]` in the main checkout's
  `docs/.bkit-memory.json`, canonically serialised, before and after — a file that exists there
  (P11) and is guarded by `test -f` and a non-empty read, so a missing file or record halts instead
  of comparing empty to empty. It is scoped to this feature's record, so another feature's
  heartbeat does not move it. Residual: a writer other than the host touching this record or the
  main tree during the run (the orchestrator must not beat while the smoke runs) yields a false
  FAIL, which is the conservative direction. `--timeout 900` is a bound chosen, not measured.
  `prompt.txt` asks the host to declare `HMAD_HOST=$H` inline, print read-only whether its
  session-id candidate variable is set, and run `/h-mad status $F`. The exact `exec` options beyond
  those shown are whatever the merged wrapper documents for `$H` (`agent-substrate.md` §"Verbs").
  Written as their own `|| exit 1` lines once the merged log format is known, and never omitted:
  V-11.1 (the host read `references/<host>-runtime.md` before any script; for grok, `h-mad` in the
  stream-json `init` line's `skills`); and V-11.2's `last_completed_phase` / `halt_reason` values
  from the same record, each grepped in `$S/out` when non-null, with a null value printed as "not
  compared: null in record" rather than skipped silently. For grok, the record also states whether
  `grep -c 'CTXBUDGET:' "$S/log"` is non-zero (P15). The record — `readlink -f` of `$L`, host
  version, `MERGE`, command, rc, `--out`, the session-id probe (V-11.4) and cost where reported
  (V-11.5) — goes into `docs/03-analysis/multi-host-runtime.live-smoke.md`.
  **On any `HALT` or `FAIL`:** do not run 7e; `git -C "$REPO" revert -m 1 --no-edit "$MERGE"`
  (never `reset --hard`); halt to the operator with the host and the line that stopped. A host
  that cannot run is a halt, never a pass.
- **Every guard mutation-verified** with `h_mad_mutation_harness.py`; score on its `MUTATION:`
  token, never on `$?`. Anything but `ALL_CAUGHT` halts (the harness's other tokens, from `grep -o
  'MUTATION: [A-Z_]*' h-mad/scripts/h_mad_mutation_harness.py | sort -u`, are `SURVIVED`,
  `REFUSED`, `BASELINE_NOT_GREEN`, `PRECHECK_FAILED`, `RESTORE_FAILED`, `TREE_MOVED`, `UNREADABLE`
  and `BUSY`; run at `4152e2be`).
- **Every wire** in §"Connection enforcement" declared `wiring`-shaped with `WIRE` / `WIRE-PIN`.
- **Both coupled suites in full** — `h-mad/tests handoff/tests handoff/scripts` — before 7f, and
  again on `main` after 7f when it reports `identity=n`.
- **Probes that confirm a suspected defect are deleted** after they answer. The committed sidecar
  probes are deliverables, not scratch.

## Success Criteria

- Every spec AC passes through its owner in §"AC ownership": the test-owned ones by their named
  tests, AC-4.5, AC-4.6 and AC-6.1 by the Phase-6 document, AC-8.3, AC-10.2 and AC-12.2 by their
  tests plus the byte-identity reading, and V-11.1–V-11.5 by the live-smoke record.
- **AC-12.1 means the full coupled suite passes, with no exception.** The one failure recorded at
  `ae7593a` (`test_top_level_key_set_still_matches`, still failing at `4152e2be`) is not this
  feature's, and it is not waived: if it still fails at the pre-merge gate, AC-12.1 is not met, 7f
  does not run, and the orchestrator halts to the operator naming that node id and its owner. The
  node-id floor's exception below is a regression floor, never evidence for AC-12.1.
- **Node-id floor.** Every test node id collected from `h-mad/tests`, `handoff/tests` and
  `handoff/scripts` at `<base>` is collected at HEAD and passes, except any failure recorded in the
  `<base>` baseline that still fails for the same reason. Command at `<base>` and at HEAD:
  `/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests
  handoff/tests handoff/scripts 2>&1 | grep '::' | sort > <file>`, then `comm -23 base.txt head.txt`
  must print nothing. A count floor is not used, because a deletion and an addition cancel in a
  count.
- Pre-existing test files and `h-mad/tests/conftest.py` are append-only: `git diff --numstat
  <base> -- <each pre-existing file touched>` shows `0` in the deleted column. In particular
  `test_h_mad_codex_runtime.py`, `test_handoff_codex_runtime.py`, `test_h_mad_context_budget.py`,
  `test_h_mad_resume_decision.py`, `test_h_mad_feature_lock.py` and `test_h_mad_install_check.py`
  keep every assertion (FR-12).
- AC-8.3, AC-10.2's second clause and AC-12.2 byte-identity is shown by the byte-identity probe at
  `<base>`, with the four install links present.
- AC-3.3: the 36 disjunct fixtures, each asserting its produced `(kind, reason)` set equals its own
  one pair; each suppression rule (a)–(e) has a fixture that would yield two kinds without it.
- AC-4.2 and AC-4.3: each axis, each A4 branch and each suffix proved alone, and each proved to
  discriminate by its removal.
- The per-branch registry sample test passes for every entry; the seed-coverage probe's per-entry
  reading shows ≥ 1 hit in every declared skill at `<base>` (the spec's gate), and its per-branch
  reading is recorded with every zero cell classified in the Phase-6 document.
- Mutation verification `ALL_CAUGHT` for: each disjunct's detection disabled alone (killed by its
  own fixture); each suppression rule removed; each catch-all axis dropped; each A4 branch dropped;
  each exclusion suffix widened to match everything; a registry pattern's branch removed (killed by
  the sample count); the `HMAD_HOST` check moved after the transcript lookup, after the usage read,
  and after the `--window` check (W1, killed by fixtures (b), (c), (d)); the host check in
  `decide()` moved after the state-file read and after the feature lookup (W2, killed by the
  absent-file and absent-feature fixtures); the `cannot_judge` branch removed (W2); the agy root's
  name split inverted (W3); the env-override read dropped from `main()` (killed by the override
  control).
- Each of W1–W3 fails its `WIRE-PIN` under a wire-scoped revert, and each force-fire fails its
  named test.
- The live smoke passed for codex, agy and grok with complete records, each run on `main` after
  7f and before 7e, with `main`'s `HEAD` equal to the unpushed merge; a halted host is a halt, not a
  pass, and reverts the merge.
- Both coupled suites green in full before 7f.

## Out-of-Scope (confirmed from spec)

- Fixing `h-mad-tdd-gate.sh` for grok (exit-code protocol, payload shape, timeout); this feature
  documents the gap and halts on it (AC-5.2).
- The codex TDD gate defects D1–D3; this feature absorbs only the install-check half of that brief.
  Re-arming HemaSuite's gate is an operator act.
- Whether the Claude-side gate's `exit 1` blocks on Claude Code (`codex-tdd-gate-defects` D4).
- Extending the catch-all's corpus to `references/`, `hooks/` or `scripts/` (residual r6).
- A standalone grok install with its own `~/.grok` hooks (rejected by D1).
- Detecting an omitted `HMAD_HOST` (FR-8 residual).
- Rewriting any Claude path in `SKILL.md`; adapters override, `SKILL.md` keeps the Claude spelling.
- Creating any install link by script; the four links are an operator pre-step.

## Next Steps

Operator review of v1.1, then the next plan audit cycle. Before Phase 4, the spec owes: (1) AC-5.2
revised from the gate measured at `<base>` if the sibling's FR-0 branch makes its text false
(Risks); (2) FR-10's hermeticity residual re-measured on the fixture-skill-name axis and the two
env overrides named; (3) FR-8's order against `bad_window` and FR-9's unknown-value and
normalisation rule; (4) AC-4.2's two further A4 branch controls, and AC-3.3's "fourteen kinds means
fourteen fixtures" restated as one fixture per disjunct (36 here) with the `reason=` field; (5) whether the advisor-warn hook
stands down on grok; (6) the sequencing bullet naming `agent-substrate.md` as edited by this
feature when no FR edits it. The sibling `codex-tdd-gate-defects` spec and plan owe the restated V-1
dependency (Risks). The committed probe sidecar (Deliverables) should land before the design is
audited, so the design can cite it rather than inline the commands.

## Version History
- v1.0: Initial plan draft (2026-09-28) from spec v1.1 at ae7593a. Premises P1-P14 and the coupled-suite baseline (h-mad/tests handoff/tests handoff/scripts: 3893 collected; 1 env-dependent failure) executed at ae7593a; the spec's calibration and 22-entry seed reproduce there. Names the parity checker (h-mad/tests/host_parity.py) and test module (test_host_construct_parity.py), fixes the PARITY <KIND> file= id= [token=] message format, adds a per-alternative seed-coverage probe to the committed sidecar, a shared-file table and rebase-then-baseline order after grok-codex-fallback and codex-tdd-gate-defects, operator link creation before the smokes, a worktree-wrapper live smoke with explicit || exit 1 assertions, W1-W3 wiring, and a node-id suite floor. Raises three open items: AC-5.2(i) vs codex-tdd-gate-defects D4, the install sequencing cycle, and the spec's agent-substrate.md edit claim.
- v1.1: Cycle-1 audit repairs (2026-09-28, 80870996: codex p1 5 must/3 should, teammate 4 must/11 should/4 nit), premises re-run at 4152e2be. Live smoke moved to Phase 7 between 7f local merge and 7e push (hosts load main via links; no pre-merge smoke tests this feature); asserts HEAD=unpushed merge, tip ancestry, per-host skill link -> main h-mad, --timeout 900; failure reverts the unpushed merge (never reset --hard) and halts. V-11.3 state check now reads orchestrator_state[F] of main's docs/.bkit-memory.json with test -f and non-empty guards (was vacuous: gitignored, absent in a worktree). Operator creates the four install links as a pre-step independent of any merge, breaking the cycle with codex-tdd-gate-defects V-1; merge order codex-tdd-gate-defects, grok-codex-fallback, this. FR-1 seed gate kept per entry as the spec states; per-branch coverage reported (P2b: 45 branches, 25 zero cells) and proven by per-branch literal samples. AC-5.2 not restated: per-branch framing over the sibling FR-0 outcome, spec revised from the measurement at base. FR-10 hermeticity: env-overridable defaults, None-default check() roots, conftest autouse override plus controls. One fixture per disjunct (36) with reason= field, suppression order, message rules per kind, W1/W2 ordering-mutant killing fixtures, decide() host check first, exact-match HMAD_HOST rule, AC-3.5 via stubbed PATH (docsections transitive subprocess), advisor-warn grok note (P15), AC ownership table over all 50 ACs, byte-identity as a sidecar probe, AC-12.1 not waived for the env-dependent failure, full harness halt set, shared-file table re-derived from the sibling plan.
