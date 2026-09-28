# Plan: multi-host-runtime

## Executive Summary

Ship spec v1.1's host-parity layer for `h-mad` and `handoff` — a committed construct registry, a
file-reading parity gate that counts mapping rows and not mentions, a four-axis catch-all over both
`SKILL.md` files, two grok adapters, parity tables in the four existing codex/agy adapters, an
inline `HMAD_HOST` declaration that makes the context budget and claims answer cannot-judge off
Claude, two new install-check roots, and one read-only live smoke per host — built in a worktree,
rebased onto `grok-codex-fallback` and `codex-tdd-gate-defects` before the 5c baseline, with the
Claude host byte-identical.

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
- tests and mutation specs under `h-mad/tests/`;
- the committed probe sidecar `docs/03-analysis/probes/multi-host-runtime/` and the Phase-6
  documents `docs/03-analysis/multi-host-runtime.live-smoke.md` and the gap analysis
  (AC-4.5, AC-6.1, FR-11).

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
  set of failure kinds each proved by its own fixture — FR-3
- An unregistered Claude-looking construct in either `SKILL.md` fails a test, over four open axes
  with a stated residual — FR-4
- grok adapters that document only where grok diverges, and halt Phase 5 on the unverified TDD
  hook — FR-5
- The codex and agy adapters measured for their gap, then brought to parity — FR-6
- `SKILL.md` routes a grok host to its adapter — FR-7
- The context budget never reports a Claude transcript's reading on a declared non-Claude host — FR-8
- A claim never runs with its collision check silently off — FR-9
- The two new install roots are checked with the existing sibling semantics, and the agy root's
  foreign same-named skills never fail the check — FR-10
- Each host is shown, live, to follow its adapter on one read-only verb — FR-11
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

**Four independent strands, then documentation, then the smoke.** (1) The registry and parity gate
(FR-1, FR-3, FR-4) are pure file readers and land first, because every adapter edit afterwards is
checked by them. (2) The three script changes (FR-8, FR-9, FR-10) are leaves with no dependency on
the gate or on each other. (3) The six adapter tables and the grok adapters (FR-2, FR-5, FR-6) land
against a green gate, one adapter at a time, each turning its `TABLE_MISSING` red to green. (4) The
`SKILL.md` edits (FR-7, AC-9.4) land last among the tree edits, so the catch-all's AC-7.2 re-run is
the final one. The live smoke (FR-11) runs after all of that is GREEN and before merge.

**The gate is a helper plus a test module.** The owed module names are fixed here:

- `h-mad/tests/host_parity.py` — the checker, a plain function over explicit paths
  (registry, the two `SKILL.md` files, the six adapters) that returns a list of failures. It is not
  named `test_*`, so pytest does not collect it. It takes the catch-all axes and the exclusion
  suffixes as parameters, which is what AC-4.2 (one axis alone; one axis removed) and AC-4.3 (one
  suffix removed) require. It imports no subprocess launcher (AC-3.5's first arm).
- `h-mad/tests/test_host_construct_parity.py` — the live-tree assertion (AC-3.1, AC-4.1) and every
  discriminating fixture (AC-1.1, AC-3.2–AC-3.4, AC-4.2–AC-4.4).

A search for a colliding name, run at `ae7593a`:
`ls h-mad/tests | grep -i -E 'parity|host|construct'` → 1 file, `test_h_mad_hostile_fixtures.py`
(unit: files; it matches on `host` inside `hostile`). No collision with either chosen name.

**The failure-kind message format** (owed by the spec's v1.0 report) is one line per failure:

```text
PARITY <KIND> file=<repo-relative path> id=<construct id>
PARITY UNREGISTERED file=<repo-relative path> id=- token=<matched text>
```

`<KIND>` is one of the fourteen FR-3 tokens, verbatim. `id=-` is used only where no construct id
exists (`UNREGISTERED`, and `REGISTRY_UNREADABLE` when the file does not parse). The live-tree test
asserts the list is empty and prints every line on failure, so one run shows every gap, not the
first. Each fixture test asserts the exact set of `<KIND>` values it produced, so a fixture that
triggers two kinds fails its own test (AC-3.3's "that kind alone").

**Controls over alternations get one fixture per branch, run with that branch alone.** The
catch-all is a union of four axes and its exclusion is a union of six suffixes. A healthy sibling
branch covers a broken one in a union test, so AC-4.2 and AC-4.3 are built as the spec states: each
axis's fixture is run with a pattern holding that axis only, and each suffix is removed from the
exclusion alone. The same rule applies to the registry patterns that are alternations
(`subagent-call`, `hook-event`, `task-tools`, `claude-settings`, `claude-projects-store`,
`session-reset-command`, `skill-slash-invocation`): the seed-coverage probe reports hits **per
alternative**, so an alternative that matches nothing is visible and is not hidden by its sibling.

**Host detection is a declaration, never a sniff.** FR-8 rejects environment-marker detection on
evidence (this Claude shell carries `CODEX_COMPANION_SESSION_ID`). `HMAD_HOST` is read first in
`h_mad_context_budget.py`, before any transcript lookup, and first in `h_mad_resume_decision.decide`,
before `_owned_elsewhere` (which today returns `False` on an empty session id before reading the
owner). Unset, empty and `claude` take today's code path unchanged.

**Regression is proven against the base, not asserted.** AC-8.3 and AC-12.2 compare stdout and
exit code against `git show <base>:<script>` run on the same fixtures. `<base>` is the commit the
feature branch forks from **after** the rebase described in Convention Prerequisites, recorded in
the state record at 5c.

**What we deliberately do not touch:** `h-mad/hooks/h-mad-tdd-gate.sh` and
`h-mad/hooks/h-mad-codex-tdd-gate.py` (both owned by the sibling features; this feature documents
the grok gap and halts on it); `h-mad/scripts/hmad-dispatch.sh` (`exec grok` is consumed, not
built); `h-mad/references/agent-substrate.md` (read for `exec grok`; see Risks); any Claude
spelling inside either `SKILL.md` outside the two located edits; any script that creates, repairs
or overwrites a symlink.

## Verified premises (commands run at `ae7593a`)

Each premise below was executed, not reasoned about. One reading at one sha; the command is what a
later reader re-runs. Readings that this feature's own implementation or its rebase will move are
marked **moves**, with when to re-measure. `main` advanced to `cf7e194` while this plan was written;
`git diff --name-only ae7593a cf7e194 -- h-mad handoff | wc -l` → 0 files (run at `cf7e194`): the
two commits touch only `docs/01-plan/features/codex-tdd-gate-defects.spec.md` and
`docs/01-plan/features/grok-codex-fallback.impl-plan.md`, so every tree premise below stands at
`cf7e194`. The shared-file table and the D4 risk were re-derived at `cf7e194`.

- **P1 — the spec's calibration reproduces at this sha, because neither `SKILL.md` has changed
  since the spec measured it.** `git diff --stat 6494b3c HEAD -- h-mad/SKILL.md handoff/SKILL.md`
  → empty output. Then the spec's FR-4 command verbatim, with `HEAD` for `6494b3c`, piped to
  `wc -l` and to `sort -u | wc -l`: `h-mad/SKILL.md` 122 occurrences, 13 distinct tokens;
  `handoff/SKILL.md` 71 occurrences, 12 distinct tokens. Matches the spec. **Moves** with any edit
  to either `SKILL.md`, including `grok-codex-fallback`'s (its impl-plan lists `h-mad/SKILL.md` as a
  production file) and this feature's own FR-7 / AC-9.4 edits. Re-measure at the post-rebase base
  (AC-4.6) and at 5g.
- **P2 — the 22 seed entries reproduce at this sha.** A scratch parser over the spec's seed table
  (unescape `\|`, expand `H`, `re.finditer` on `git show HEAD:<skill>/SKILL.md`), then deleted:
  22 entries, 0 count mismatches, 17 declaring `h-mad`, 12 declaring `handoff`. The first run of
  that parser reported 2 mismatches (`session-reset-command`, `skill-slash-invocation`); both were
  the parser mis-stripping the double-backtick cells, not the spec, and a direct `re.findall` of the
  two patterns gave 4 / 7 and 15 / 11 as the spec states. That parser bug is the reason the probe
  must be **committed** (Deliverables), not re-written by each reader. **Moves** with either
  `SKILL.md`; re-measure with the committed probe at the post-rebase base.
- **P3 — no adapter has a mapping table and the registry does not exist.** `grep -c '^## Construct
  mapping' h-mad/references/*-runtime.md handoff/references/*-runtime.md` → 0 in each of 4 files
  (unit: matching lines per file); `ls h-mad/references/host-constructs.json` → no such file.
  **Moves** by construction in Phase 5.
- **P4 — `exec` does not accept grok today.** `grep -c 'unknown agent' h-mad/scripts/hmad-dispatch.sh`
  → 8 matching lines; the spec records each as `(codex|agy)`. FR-11's grok smoke therefore needs
  `grok-codex-fallback` merged. **Moves** at the rebase; re-measure then.
- **P5 — the TDD gate's block form.** `grep -c 'exit 1' h-mad/hooks/h-mad-tdd-gate.sh` → 5
  matching lines; `grep -c 'TARGET_PATH" \] && exit 0' h-mad/hooks/h-mad-tdd-gate.sh` → 1 matching
  line. These are the evidence for AC-5.2 reasons (i) and (ii). **Moves** if
  `codex-tdd-gate-defects` lands (its spec v1.0 AC-6.5 switches every refusal to exit 2 or, as
  recommended, a `hookSpecificOutput` JSON deny on rc 0, and its payload read to `tool_input`);
  see Risks. Re-measure at the post-rebase base before the grok adapter is written.
- **P6 — the two script entry points the host declaration must precede.**
  `grep -n 'CLAUDE_CODE_SESSION_ID' h-mad/scripts/h_mad_context_budget.py` → one read of that
  variable; the script's `UNKNOWN` reasons today are `bad_window`, `no_transcript`, `no_usage`
  (`grep -o 'reason=[a-z_]*' h-mad/scripts/h_mad_context_budget.py | sort -u`).
  `grep -n 'def _owned_elsewhere\|if not session_id' h-mad/scripts/h_mad_resume_decision.py` shows
  the opt-out FR-9 names: with no session id, `_owned_elsewhere` returns before reading the owner.
- **P7 — the install check's current surface.** `grep -n 'add_argument\|def check' h-mad/scripts/h_mad_install_check.py`
  → options `--skills-link`, `--hook-link` and a repo option; functions `check_siblings(repo,
  skills_dir)` and `check(skills_link, hook_link, repo)`. Issue prefixes `SIBLING_NOT_SYMLINK`,
  `SIBLING_DANGLING`, `SIBLING_WRONG_CHECKOUT`, `SPLIT_INSTALL`. Existing tests:
  `grep -c 'def test_' h-mad/tests/test_h_mad_install_check.py` → 23 (unit: matching lines), 7 of
  them in `class TestSiblingSkills`, which holds `test_a_sibling_installed_as_a_copy_is_reported`.
- **P8 — the install roots on this machine.** `ls -ld ~/.agents/skills/{h-mad,handoff}
  ~/.gemini/config/skills/{h-mad,handoff}` → all four absent; `~/.claude/skills/h-mad` and
  `~/.claude/skills/handoff` are symlinks into `/Users/kimhawk/orca/skills`. Collisions with the
  checkout's top-level skill names, re-run at `ae7593a`:
  `comm -12 <(git ls-files '*/SKILL.md' | awk -F/ 'NF==2{print $1}' | sort -u) <(ls <root> | sort -u)`
  over 316 names → `~/.gemini/config/skills`: 1 name, `debugger`, a plain directory (`ls -ld`);
  `~/.agents/skills`: 0 names (unit: distinct names). Same as the spec's reading at `76b2501`. **Moves** when the operator creates the links (Convention
  Prerequisites) or agy adds a skill.
- **P9 — the located sections exist once each.** `grep -c '^## Host runtime' h-mad/SKILL.md
  handoff/SKILL.md` → 1 and 1; ``grep -c '^| `cannot_judge`' h-mad/SKILL.md`` → 1 (unit: matching
  lines). AC-7.1 and AC-9.4 locate by these, never by line.
- **P10 — the agy adapters' "typically" sentence.** `grep -n typically h-mad/references/agy-runtime.md
  handoff/references/agy-runtime.md` → one matching line in each, naming
  `~/.gemini/config/skills/<skill>` as the typical load path. It is false on this machine today
  (P8) and becomes true only once the operator creates the links. FR-6 does not name it; this plan
  carries it as a deliverable (Deliverables, "owed by the spec report").
- **P11 — bare `hmad-dispatch` resolves to the main tree.** `which hmad-dispatch` →
  `~/.claude/skills/h-mad/bin/hmad-dispatch`; `readlink -f "$(which hmad-dispatch)"` →
  `/Users/kimhawk/orca/skills/h-mad/bin/hmad-dispatch`. A worktree build is reachable only by
  absolute path (Convention Prerequisites).
- **P12 — host versions.** `grok --version` → `grok 1.0.41 (4220f3b224a6) [stable]`;
  `codex --version` → `codex-cli 0.157.1`; `agy --version` → `1.2.12`. **Moves** with any host
  upgrade; the smoke records the version it ran against (V-11 stamp).
- **P13 — the status verb is documented read-only.** `grep -n '/h-mad status' h-mad/SKILL.md`
  → the verb table row ("Auto-bootstrap if needed. Read-only.") and the rule "except under
  `/h-mad status`, which is documented read-only and must stay so". FR-11's smoke relies on that.
- **P14 — spec AC census.** `grep -oE '^  - AC-[0-9]+\.[0-9]+[a-z]?'
  docs/01-plan/features/multi-host-runtime.spec.md | sort -u | wc -l` → 50 distinct AC ids; the
  same grammar without the leading indent over the whole spec also reads 50. `grep -oE '^  -
  V-[0-9]+\.[0-9]+' … | sort -u | wc -l` → 5 distinct V ids (unit: distinct ids). Moves only if the
  spec is revised.

**Suite baseline.** Commands, at `ae7593a`, with the interpreter the sibling plan pinned
(`which pytest; head -1 "$(which pytest)"` → `/opt/anaconda3/bin/pytest`, shebang
`#!/opt/anaconda3/bin/python`):

```bash
P="/opt/anaconda3/bin/python -m pytest -p no:cacheprovider"
$P --collect-only -q h-mad/tests 2>&1 | tail -1        # 3552 tests collected
$P --collect-only -q handoff/tests 2>&1 | tail -1      # 201 tests collected
$P --collect-only -q handoff/scripts 2>&1 | tail -1    # 140 tests collected
$P --collect-only -q h-mad/tests handoff/tests handoff/scripts 2>&1 | tail -1   # 3893 tests collected
$P -q h-mad/tests handoff/tests handoff/scripts 2>&1 | tail -3
# reading at ae7593a: 1 failed, 3892 passed, 1 warning in 588.67s. The failure is
# h-mad/tests/test_h_mad_check_plugin_hooks.py::TestAgainstTheLiveBinary::test_top_level_key_set_still_matches,
# which reads the locally installed Claude Code binary; environment-dependent, not this feature's.
```

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
- **The new links couple the same checkout to two more hosts.** Once the operator creates
  `~/.agents/skills/{h-mad,handoff}` and `~/.gemini/config/skills/{h-mad,handoff}`, codex, grok and
  agy read the **main** tree too. A half-merged main is then half-installed on four hosts, not one.
  The links point at the main checkout, never at the worktree, so no host sees unmerged work.
- **Skill self-containment.** The registry lives in `h-mad/references/`, and only tests read it
  (FR-1). `handoff` gains no read of any `h-mad` file at runtime. The handoff adapters' tables name
  construct ids as strings only. Test-side cross-reads have precedent (spec Assumption A5).
- **The gate reads files only.** No test and no script invokes codex, agy or grok (spec Scope;
  `invariants.base.md` §"No new external dependency"). AC-3.5's first arm (no subprocess import in
  `host_parity.py`) is checked by an import-scan test; the stubbed-`PATH` arm is not needed if the
  first holds.
- **Existing forbidden-token tests constrain the adapter text.** `test_h_mad_codex_runtime.py` and
  `test_handoff_codex_runtime.py` forbid Claude spellings in the codex adapters (spec FR-12,
  AC-6.6). The construct ids are kebab-case so that a mapping row never spells a forbidden token;
  the `mapping` and `source` cells must also avoid them.
- **One declaration, two scripts.** `HMAD_HOST` is read by two scripts with the same value set
  (`claude`, `codex`, `agy`, `grok`, unset, empty, other). The two readers must agree on that set;
  one test feeds every value to both and asserts the same classification (Claude path, non-Claude,
  unknown).

## Deliverables

| Deliverable | Target file(s) | Satisfies |
|---|---|---|
| Registry with the seed entries re-derived at the post-rebase base | `h-mad/references/host-constructs.json` (new) | FR-1 |
| Parity checker (paths, axes and exclusion suffixes as parameters; no subprocess import) | `h-mad/tests/host_parity.py` (new, not collected) | FR-3, FR-4 |
| Live-tree parity assertion and every discriminating fixture: 14 kind fixtures, AC-3.2's mention-only fixture, 4 axis-alone controls, 6 suffix controls, the `TeamCreate` fixture | `h-mad/tests/test_host_construct_parity.py` (new) | FR-1, FR-3, FR-4 |
| `## Construct mapping` table in each existing adapter, plus FR-8 / FR-9 / FR-10 text | `h-mad/references/codex-runtime.md`, `h-mad/references/agy-runtime.md`, `handoff/references/codex-runtime.md`, `handoff/references/agy-runtime.md` | FR-2, FR-6, FR-8, FR-9, FR-10 |
| The "typically `~/.gemini/config/skills/<skill>`" sentence reworded to name the FR-10 install path (owed by the spec report) | `h-mad/references/agy-runtime.md`, `handoff/references/agy-runtime.md` | FR-6, FR-10 |
| grok adapters with version pin, compat toggles, trust, hooks, roles, halt token, table | `h-mad/references/grok-runtime.md`, `handoff/references/grok-runtime.md` (new) | FR-2, FR-5 |
| `## Host runtime` names all three adapters | `h-mad/SKILL.md`, `handoff/SKILL.md` | FR-7 |
| `cannot_judge` row gains the second cause | `h-mad/SKILL.md` (decision-routing table) | FR-9 (AC-9.4) |
| `HMAD_HOST` read before any transcript lookup; `host_unsupported`, `unknown_host` | `h-mad/scripts/h_mad_context_budget.py` | FR-8 |
| `HMAD_HOST` read in `decide()` before `_owned_elsewhere`; `cannot_judge` without `--session-id` under a non-Claude host | `h-mad/scripts/h_mad_resume_decision.py` | FR-9 |
| `--agents-skills-dir`, `--agy-skills-dir`, the name × state rule, sorted `AGY_SIBLING_COLLISION` detail lines after the verdict block | `h-mad/scripts/h_mad_install_check.py` | FR-10 |
| Doc tests for AC-5.1, AC-5.2 (halt token), AC-5.7, AC-7.1, AC-7.3, AC-8.4, AC-9.3, AC-9.4, AC-10.4, and the row-content ACs AC-2.3–AC-2.5, AC-5.3–AC-5.6, AC-6.3–AC-6.5, each locating its section by heading and failing (never skipping) when the heading is absent | `h-mad/tests/test_host_runtime_docs.py` (new) | FR-5, FR-7, FR-8, FR-9, FR-10 |
| Host-declaration tests for both scripts, and the shared-value-set agreement test | `h-mad/tests/test_h_mad_host_declaration.py` (new) | FR-8, FR-9 |
| Install-check root tests (AC-10.1, AC-10.3, AC-10.5, AC-10.6), passing both new options explicitly | `h-mad/tests/test_h_mad_install_check_roots.py` (new) | FR-10 |
| Mutation specs for the guards (Success Criteria) | `h-mad/tests/mutation-specs/` (new JSON, or new rows in `context_budget.json`, `resume_decision_cannot_judge.json`, `install_check_siblings.json`) | FR-3, FR-4, FR-8, FR-9, FR-10 |
| Probe sidecar: the FR-4 calibration command, and a seed-coverage probe that reports hits per entry **and per alternative** in each `SKILL.md`, both taking the sha as an argument | `docs/03-analysis/probes/multi-host-runtime/` (new) | FR-1, FR-4 (AC-4.5, AC-4.6) |
| Pre-change gap table (construct × adapter, `addressed`/`absent`, with its sha) | Phase-6 analysis document | FR-6 (AC-6.1) |
| Live-smoke record, one section per host | `docs/03-analysis/multi-host-runtime.live-smoke.md` (new) | FR-11 |

The new test file names were checked against the tree at `ae7593a`:
`ls h-mad/tests/test_host_construct_parity.py h-mad/tests/test_host_runtime_docs.py
h-mad/tests/test_h_mad_host_declaration.py h-mad/tests/test_h_mad_install_check_roots.py
h-mad/tests/host_parity.py` → none exists. Existing mutation specs that cover the three touched
scripts: `ls h-mad/tests/mutation-specs | grep -i -E 'budget|resume|install'` →
`context_budget.json`, `context_budget_docs.json`, `install_check_siblings.json`,
`resume_decision_cannot_judge.json` (unit: files).

## Connection enforcement

Three deliverables are connections: an existing entry point must reach a new branch. Each is a
`wiring`-shaped task with a `WIRE` / `WIRE-PIN`, and Phase 5 runs the wire-scoped revert — remove
the call site only, callee and tests intact — plus the force-fire mutation in the other direction
(`invariants.base.md` §"Connection enforcement").

| Wire | Call site → callee | `WIRE-PIN` (remove) | Force-fire must fail |
|---|---|---|---|
| W1 | `h_mad_context_budget.main` → host check, before transcript lookup | AC-8.1 fails: a Claude reading (`used=`) is printed under `HMAD_HOST=grok` | host check returns `host_unsupported` whatever the value → the existing `test_h_mad_context_budget.py` tests fail (e.g. `test_ok_below_the_ceiling` asserts `returncode == 0` and a token starting `CTXBUDGET: OK `) |
| W2 | `h_mad_resume_decision.decide` → host check, before `_owned_elsewhere` | AC-9.1 fails: the no-owner fixture routes instead of printing `cannot_judge` | host check fires with `HMAD_HOST` unset → `test_h_mad_feature_lock.py::TestResumeDecisionSurfacesOwnership::test_no_session_id_preserves_legacy_behaviour` fails |
| W3 | `h_mad_install_check.check` → the two new root checks | AC-10.1 and AC-10.5 fail: a wrong entry under either root is not reported | the agy root's issue rule applied to every name → AC-10.5's `debugger` cells fail (`INSTALL: FAIL` where `PASS` plus one detail line is required); the agy rule applied to the `--skills-link` parent → AC-10.6 fails (no `SIBLING_NOT_SYMLINK` for `debugger`) |

A force-fire is valid only if its named test's input contains what the mutated condition keys on;
each row above was checked against that rule by reading the named test's fixture, not by running a
mutant (the mutants cannot exist before the code does). Residual: whether each force-fire kills is a
prediction until Phase 5 runs it.

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| `grok-codex-fallback` edits `h-mad/SKILL.md` and adds Claude constructs | The seed registry and calibration are stale at the real base; the catch-all fails or a new token is registered wrongly | Rebase before 5c; re-run the committed calibration and seed-coverage probes at the new base (AC-4.6); a false hit is fixed by narrowing an axis with a new control, never by registering a non-construct |
| `codex-tdd-gate-defects` changes the Claude TDD gate's block form and its payload read | Its spec v1.0 (at `cf7e194`) finds the Claude gate inert because it "never reads `tool_input.file_path`", and its AC-6.5 recommends form (b): rc 0 plus one stdout JSON object carrying `hookSpecificOutput.permissionDecision == "deny"`. After the rebase, AC-5.2 reason (i) ("`exit 1`, which grok treats as fail-open") is false, and reason (ii) (top-level `file_path`) is re-pointed at `tool_input.file_path`, which grok's camelCase `toolInput` (F8) may still miss | Re-run P5 at the post-rebase base, plus `grep -c 'permissionDecision\|tool_input' h-mad/hooks/h-mad-tdd-gate.sh`, before writing the grok adapter. F9 documents two grok deny forms, exit 2 and a stdout `{"decision":"deny"}`; whether grok honours `hookSpecificOutput.permissionDecision` is not in the guide, so under form (b) reason (i) becomes "deny form undocumented on grok", not "fail-open". The spec's AC-5.2 text is revised before Phase 5 writes the adapter (owed, see Next Steps). The halt token `step5:grok_tdd_hook_unverified` stays in every branch |
| `codex-tdd-gate-defects` D1 changes how the Claude gate derives the test path | AC-5.2 reason (iii) (pytest inside grok's 5 s timeout) may change in cost | Re-read the gate at the post-rebase base; reason (iii) is stated against that tree |
| Sequencing cycle with `codex-tdd-gate-defects` | That feature's brainstorm says its live check "needs the `~/.agents/skills/h-mad` install from `multi-host-runtime`, which sets the order", while this plan merges after it | The link itself is an operator act (FR-10: no script links anything), not a merge artifact of this feature. The operator can create `~/.agents/skills/h-mad` before either feature merges; what this feature adds is the check. Raised to the orchestrator as a contradiction (Next Steps) |
| The spec says this feature edits `h-mad/references/agent-substrate.md`, but no FR names it | A rebase conflict is expected where none exists, or an unplanned edit appears | `grep -n agent-substrate docs/01-plan/features/multi-host-runtime.spec.md` → only the sequencing bullet (unit: matching lines, 2). The plan treats the file as read-only here; raised to the spec |
| A seed pattern that is an alternation has a dead branch hidden by a live sibling | A construct's rename goes unnoticed; the entry stays green on the other branch | The seed-coverage probe reports hits per alternative; a zero-hit alternative is recorded and either dropped or justified in the Phase-6 document |
| Existing install-check tests read the real `~/.agents/skills` and `~/.gemini/config/skills` (spec FR-10 hermeticity residual) | An operator installing a skill named like a fixture checkout changes an existing test's stdout | New tests pass both options explicitly; the residual is stated, not closed. Measured before the change: the fixture checkout name `checkout` collides with nothing in either real root (P8 lists the real entries) |
| A non-Claude orchestrator omits `HMAD_HOST` (spec FR-8 residual) | The slug walk measures a Claude transcript for the same cwd | The adapters instruct the inline declaration; the live smoke checks it is followed. No mechanism detects the omission (spec Out-of-Scope) |
| The smoke runs the main tree instead of the worktree (P11) | The smoke measures the pre-feature skill and reads as a pass | The smoke's command resolves the wrapper by absolute path inside the worktree and halts when `readlink -f` lies outside it (Convention Prerequisites) |
| codex does not load skills from `~/.agents/skills` (spec Assumption A2) | The codex smoke cannot find h-mad | The smoke halts to the operator with the reason, and the spec's A2 is corrected; never a pass |
| A host cannot run (absent, unauthenticated, out of quota, non-zero rc, no final message) | No evidence for that host | Halt to the operator with the reason; merge does not proceed on "not run" (spec FR-11) |
| The feature edits the live skill | A run in flight reads a half-built skill | Worktree; both coupled suites before merge |
| A pre-existing test is deleted or edited while the count stays green | FR-12's guarantee silently false | Node-id floor and append-only numstat check (Success Criteria) |

## Convention Prerequisites

- **Merge order (hard).** This feature merges **after** `grok-codex-fallback` and
  `codex-tdd-gate-defects`. Neither has a branch or worktree at `ae7593a` (`git branch -a | grep -E
  'grok|codex-tdd|multi-host'` → no output; `git worktree list` → the main checkout only), so both
  are ahead in the queue, not in flight on a branch.
- **Shared files.** Derived at `ae7593a` from the sibling documents, not from memory:
  `grok-codex-fallback` from its impl-plan (`git show HEAD:docs/01-plan/features/grok-codex-fallback.impl-plan.md
  | grep -oE '\*\*(Production|Test) file\*\*:.*' | grep -oE '`[^`]+`' | tr -d '`' | sort -u`);
  re-run at `cf7e194` with `grep -v '/tests'`, the production set is unchanged;
  `codex-tdd-gate-defects` from its spec v1.0 at `cf7e194`
  (`grep -oE '`h-mad/[^`]+`|`handoff/[^`]+`' docs/01-plan/features/codex-tdd-gate-defects.spec.md
  | sort -u`; it names neither `h-mad/SKILL.md` nor `agent-substrate.md`:
  `grep -c 'SKILL.md\|agent-substrate'` on it → 0 matching lines). It has no plan yet, so its column
  **moves** when its plan lands. Its other named files (`h_mad_derive_test_path.sh`,
  `h_mad_wire_pin_gate.py`, `h_mad_audit_gate.py`) are not touched or documented by this feature.

  | File | This feature | `grok-codex-fallback` | `codex-tdd-gate-defects` |
  |---|---|---|---|
  | `h-mad/SKILL.md` | edits (FR-7, AC-9.4) | edits (production file) | not named |
  | `h-mad/references/codex-runtime.md` | edits (FR-2, FR-6, FR-8–FR-10) | not named | edits §"Trust boundary" (D2) |
  | `h-mad/hooks/h-mad-tdd-gate.sh` | reads; the grok adapter states its behaviour (AC-5.2) | edits (production file) | edits (shared judge; blocking form per its AC-6.5) |
  | `h-mad/hooks/h-mad-codex-tdd-gate.py` | reads; the codex adapter's hook rows cite it | not named | edits (shared judge, interpreter trust, summary scoring) |
  | `h-mad/scripts/hmad-dispatch.sh` | reads; FR-11 consumes `exec grok` | edits (production file) | not named |
  | `h-mad/references/agent-substrate.md` | reads (`exec grok` verb docs) | edits §"Verbs" per its spec FR-10 (not listed as an impl-plan production file) | not named |
  | `h-mad/tests/` | adds files | adds files | adds files |

  The textual overlaps are `h-mad/SKILL.md` and `h-mad/references/codex-runtime.md`. The
  semantic overlaps — files this feature documents but does not edit — are the two hooks,
  `hmad-dispatch.sh` and `agent-substrate.md`; a rebase shows no conflict there, so each is
  re-read at the new base (P4, P5).
- **Rebase, then baseline.** Branch `feature/multi-host-runtime` as a **git worktree**
  (`hmad-dispatch worktree-create` or `git worktree add`). Before the 5c baseline, rebase onto
  `main` after both siblings have merged, record that fork sha as `<base>`, and at `<base>`:
  re-run P1 (calibration, via the committed probe), P2 (seed coverage, via the committed probe),
  P4, P5, P9 and the suite baseline; write the AC-4.6 record into the Phase-6 document; and
  capture the node-id list for the floor.
- **Operator acts before the smokes.** The operator creates `~/.agents/skills/{h-mad,handoff}` and
  `~/.gemini/config/skills/{h-mad,handoff}` as symlinks into the main checkout, using the `ln -s`
  commands the adapters state (AC-10.4), and never over an existing non-symlink. The agy smoke
  cannot find h-mad until then (P8: all four absent at `ae7593a`). After the links exist,
  `python3 h-mad/scripts/h_mad_install_check.py` from the worktree, with both new options at their
  defaults, must print `INSTALL: PASS`; the one expected detail line on this machine is
  `AGY_SIBLING_COLLISION:… kind=NOT_SYMLINK` for `debugger` (P8). Re-run P8 immediately before, since
  agy may add a skill.
- **Codex authors Phase 5 under the TDD gate**, RED before GREEN per module. The grok adapter's
  halt token applies to a grok-hosted Phase 5, not to this feature's own build.
- **No AC and no pytest test makes a live model call.** The smoke is a verification step (FR-11).
- **The live smoke.** After every Phase-5 task is GREEN and `grok-codex-fallback` has merged, for
  each host in `codex agy grok`, run one read-only `/h-mad status <feature>` through the
  **worktree's** wrapper by absolute path. Every pass condition is an executable assertion that
  stops on failure; `set -e` is inert in the Bash tool's top-level shell, so each carries an
  explicit `|| exit 1`:

  ```bash
  W=<absolute path of the feature worktree>; H=<codex|agy|grok>; F=<feature in orchestrator_state>
  S=$(mktemp -d); D="$W/h-mad/bin/hmad-dispatch"   # then write $S/prompt.txt (below)
  R=$(readlink -f "$D"); echo "wrapper=$R"
  case "$R" in "$W"/*) ;; *) echo "HALT wrapper outside worktree"; exit 1;; esac
  M="$W/docs/.bkit-memory.json"
  B_SHA=$(shasum -a 256 "$M" | awk '{print $1}'); (cd "$W" && git status --short) > "$S/before"
  "$D" exec "$H" "$S/prompt.txt" --cd "$W" --out "$S/out" --log "$S/log" || { echo "HALT rc=$?"; exit 1; }
  test -s "$S/out" || { echo "HALT no final message"; exit 1; }
  (cd "$W" && git status --short) > "$S/after"
  cmp -s "$S/before" "$S/after" || { echo "FAIL V-11.3 tree moved"; exit 1; }
  test "$(shasum -a 256 "$M" | awk '{print $1}')" = "$B_SHA" || { echo "FAIL V-11.3 state moved"; exit 1; }
  grep -q -F "$F" "$S/out" || { echo "FAIL V-11.2 feature not named"; exit 1; }
  ```

  `prompt.txt` asks the host to declare `HMAD_HOST=$H` inline, print read-only whether its
  session-id candidate variable is set, and run `/h-mad status $F`. The exact `exec` options are
  whatever the post-rebase wrapper documents for `$H` (re-read `agent-substrate.md` §"Verbs" at
  `<base>`); the block above fixes only the assertions. V-11.1 (the adapter was read before any
  script; for grok, `h-mad` in the stream-json `init` line's `skills`) and V-11.2's
  `last_completed_phase` / `halt_reason` equality are checked against the log and against
  `docs/.bkit-memory.json` read directly, each as its own `|| exit 1` line written once the
  post-rebase log format is known. The record — `readlink -f` path, host version, tree sha,
  command, rc, `--out`, the session-id probe (V-11.4) and cost where reported (V-11.5) — goes into
  `docs/03-analysis/multi-host-runtime.live-smoke.md`. A host that cannot run halts to the operator
  and is never a pass.
- **Every guard mutation-verified** with `h_mad_mutation_harness.py`; score on its `MUTATION:`
  token, never on `$?`. `SURVIVED` / `REFUSED` halts.
- **Every wire** in §"Connection enforcement" declared `wiring`-shaped with `WIRE` / `WIRE-PIN`.
- **Both coupled suites in full** — `h-mad/tests handoff/tests handoff/scripts` — before merge.
- **Probes that confirm a suspected defect are deleted** after they answer. The committed sidecar
  probes are deliverables, not scratch.

## Success Criteria

- All 50 spec ACs across FR-1–FR-12 pass automated tests, except those the spec itself marks as
  verification artifacts or records (AC-4.5, AC-4.6, AC-6.1), which are satisfied by the Phase-6 document, and the
  five V-11 criteria, which are satisfied by the live-smoke record. (Count: P14; unit: distinct
  ids.)
- **Node-id floor.** Every test node id collected from `h-mad/tests`, `handoff/tests` and
  `handoff/scripts` at `<base>` is collected at HEAD and passes, except any failure recorded in the
  `<base>` baseline that still fails for the same reason. Command at `<base>` and at HEAD:
  `/opt/anaconda3/bin/python -m pytest --collect-only -q -p no:cacheprovider h-mad/tests
  handoff/tests handoff/scripts 2>&1 | grep '::' | sort > <file>`, then `comm -23 base.txt head.txt`
  must print nothing. A count floor is not used, because a deletion and an addition cancel in a
  count.
- Pre-existing test files are append-only: `git diff --numstat <base> -- <each pre-existing test
  file touched>` shows `0` in the deleted column. In particular `test_h_mad_codex_runtime.py`,
  `test_handoff_codex_runtime.py`, `test_h_mad_context_budget.py`, `test_h_mad_resume_decision.py`,
  `test_h_mad_feature_lock.py` and `test_h_mad_install_check.py` keep every assertion (FR-12).
- AC-8.3 and AC-12.2 byte-identity is shown against `git show <base>:<script>` on the same fixtures.
- AC-3.3: fourteen kind fixtures, each asserting its produced kind set equals `{<its kind>}`.
- AC-4.2 and AC-4.3: each axis and each suffix proved alone, and each proved to discriminate by its
  removal.
- The seed-coverage probe, committed, reports every registry entry and every alternative with ≥ 1
  hit in each declared skill at `<base>`, or records the retirement.
- Mutation verification `ALL_CAUGHT` for: each FR-3 kind's detection (a kind's check disabled is
  killed by its fixture); each catch-all axis dropped; each exclusion suffix widened to match
  everything; the `HMAD_HOST` check moved after the transcript lookup (W1); the `cannot_judge`
  branch removed (W2); the agy root's name split inverted (W3).
- Each of W1–W3 fails its `WIRE-PIN` under a wire-scoped revert, and each force-fire fails its
  named test.
- The live smoke passed for codex, agy and grok with complete records, each run through the
  worktree's wrapper; a halted host is a halt, not a pass.
- Both coupled suites green in full before merge.

## Out-of-Scope (confirmed from spec)

- Fixing `h-mad-tdd-gate.sh` for grok (exit-code protocol, payload shape, timeout); this feature
  documents the gap and halts on it (AC-5.2).
- The codex TDD gate defects D1–D3; this feature absorbs only the install half of that brief.
  Re-arming HemaSuite's gate is an operator act.
- Whether the Claude-side gate's `exit 1` blocks on Claude Code (`codex-tdd-gate-defects` D4).
- Extending the catch-all's corpus to `references/`, `hooks/` or `scripts/` (residual r6).
- A standalone grok install with its own `~/.grok` hooks (rejected by D1).
- Detecting an omitted `HMAD_HOST` (FR-8 residual).
- Rewriting any Claude path in `SKILL.md`; adapters override, `SKILL.md` keeps the Claude spelling.

## Next Steps

Operator review and approval of v1.0, then the plan audit cycle. Before Phase 4, the orchestrator
settles three items this plan cannot: (1) how the spec's AC-5.2 reasons (i) and (ii) are restated
once `codex-tdd-gate-defects` changes the gate's blocking form and payload read (Risks); (2) the sequencing cycle between
this feature and `codex-tdd-gate-defects` over the `~/.agents/skills` install (Risks); (3) the
spec's sequencing bullet naming `agent-substrate.md` as edited by this feature when no FR edits it.
The committed probe sidecar (Deliverables) should land before the design is audited, so the design
can cite it rather than inline the commands.

## Version History
- v1.0: Initial plan draft (2026-09-28) from spec v1.1 at ae7593a. Premises P1-P14 and the coupled-suite baseline (h-mad/tests handoff/tests handoff/scripts: 3893 collected; 1 env-dependent failure) executed at ae7593a; the spec's calibration and 22-entry seed reproduce there. Names the parity checker (h-mad/tests/host_parity.py) and test module (test_host_construct_parity.py), fixes the PARITY <KIND> file= id= [token=] message format, adds a per-alternative seed-coverage probe to the committed sidecar, a shared-file table and rebase-then-baseline order after grok-codex-fallback and codex-tdd-gate-defects, operator link creation before the smokes, a worktree-wrapper live smoke with explicit || exit 1 assertions, W1-W3 wiring, and a node-id suite floor. Raises three open items: AC-5.2(i) vs codex-tdd-gate-defects D4, the install sequencing cycle, and the spec's agent-substrate.md edit claim.
