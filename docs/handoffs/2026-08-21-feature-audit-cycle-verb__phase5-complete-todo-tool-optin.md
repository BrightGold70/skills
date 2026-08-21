# Handoff — audit-cycle-verb Phase 5 COMPLETE (Tasks 5–9), and the todo tool restored

**Date:** 2026-08-21
**Branch:** feature/audit-cycle-verb
**Project:** skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Took `audit-cycle-verb` from Task 5 to **Phase 5 complete**: Tasks 5–9 all shipped, 5f
`WIREREG: PASS registered=6 verified=6 broken=0 missing=0 ambiguous=0`, 5g written
(`phase = null`, TDD gate disarmed, `current_phase=6`). Scoped suite **1560 passed / 0 failed**;
after the later handoff-skill work the combined suites read **1593 passed / 0 failed**. Twelve
commits, all pushed, branch 0/0. Two skill defects were found and fixed mid-flight (J34/J35 — the
wire registry could never verify a wire), and the operator's "todos are missing" report was traced
to a Claude Code change and fixed at the root.

**The through-line worth carrying: every defect found this session was found by a lane that could
see something the others structurally could not.** A green suite, a passing revert, `ALL_CAUGHT`
mutations and a clean 5f agreed with each other four separate times while a real defect sat under
them.

## Key Learnings

- **A mutation can fail the right test for the WRONG reason, and no amount of re-running catches
  it.** Four of the twelve connection mutations were strawmen — `helper-extract-drop` left the call
  executing and only discarded its result; `helper-extract-force` short-circuited the wait, making
  it a second *drop* at a site that then had no force; `helper-gate-drop-p2` sliced `pass_specs[:1]`
  so the test failed on missing *collection*, not gating; `verb-helper-force` left the helper in
  halt mode. `MUTATION: ALL_CAUGHT survived=0 refused=0` **and** per-row isolation are both blind to
  this. The only check that sees it is asking, per row, *why* the test failed.
- **`size_status` was forgeable by the feature name, and the plan had already fixed that exact class
  once.** The `ASSEMBLE:` token embeds the prompt path, which embeds the feature. The plan moved
  `*unverified*` → `*size_status=unverified*` because `unverified-logins` would forge the bare word;
  the replacement was still forgeable (`feature=size_status=unverified` → a VERIFIED cycle reported
  unverified). Fields are space-separated, so the boundary is a leading space. 99 tests, 18
  mutations, two agy reviews, a whole-module revert and a clean 5f all passed over it.
- **`h_mad_wire_registry.py` could never verify any wire (J34).** `collect()` returns full node ids;
  `partition()` tested a *bare* pin name for set membership. Exact match can never hold, so every
  pin fell to `missing` and `verified` was structurally pinned at 0 — **5f had never verified a wire
  on any feature.** `run_pins()` carried the same root cause one function downstream (bare names
  handed to pytest as file paths) and had simply never been reached.
- **60 green tests encoded that bug.** `test_collect_returns_pytest_node_ids` asserted node ids
  while all four `partition()` tests fed bare names. Each self-consistent, mutually contradictory
  across the seam, and nothing composed `collect()` → `partition()`. **When two unit tests disagree
  about a type at a seam and no test crosses it, the seam is where the bug lives.**
- **A survived mutation caught what tests, a correct live token and review all missed.** With J34
  fixed, 80 tests green and `verified=5` on a live run, dropping the `::` from the matcher changed
  *nothing*. The pre-existing near-miss test pinned a pin *shorter* than the test name, where the
  delimiter is irrelevant; the discriminating shape is a tail-substring (`wire` vs `::test_wire`).
- **The todo tool was never removed — 2.1.236 made it opt-in.** All four names are in the 2.1.238
  binary behind `CLAUDE_CODE_ENABLE_TODO_TOOLS`. `todoFeatureEnabled` is a *different* switch (TUI
  panel), so enabling only that leaves the tools absent — the plausible half-fix. Timeline pins it:
  2.1.236 installed 2026-08-20 05:18, `TaskCreate`'s last call 2026-08-19T07:11:39Z, zero after.
- **The handoff skill actively forbade the remedy.** It said "no user config can add a built-in
  tool… don't try to re-enable anything" — refuted. That is worse than a stale claim: every reader
  whose probe came back empty degraded to a lesser sink while rung 1 was one setting away.
- **Durability and visibility are different properties.** `.omc/notepad.md` survives `/clear` and is
  invisible; a resume that writes 6 items there and reports `Todos restored: 6` is entirely truthful
  and still reads as "my todos disappeared".
- **`ToolSearch` is not deferred-only** — `select:Bash,Read,Write` returns already-loaded tools, so
  an empty `select:` result is genuine absence. Worth knowing because its own description says
  otherwise, which invites doubt about a probe that is actually sound.
- **A corpus count is point-in-time.** The skill said 465 `TaskCreate` calls; a re-count returned
  429. Neither is obviously wrong — they did not count the same thing. Nearly filed a "correction"
  that would have swapped one brittle figure for another.
- **`git check-ignore -v` exits 0 when a file matches ANY rule, including a negation.** It printed
  `!.h-mad/wires.jsonl` and I read it as "still ignored". `git status` showing `??` was the
  authoritative signal, in the same output.
- **`.h-mad/` → `.h-mad/*` is required for a negation to work at all** — git cannot re-include a
  file whose parent *directory* is excluded, so the obvious one-line `!` would silently do nothing.
- **`h_mad_mutation_harness.py` really does restore on SIGTERM** — a 10-minute shell timeout killed
  it mid-run and the tree came back intact. A claim worth having seen fire.
- **`timeout` does not exist on this machine** (again). `rc=127` reads as a failed probe when the
  probe never ran.

## Next Steps

1. **Phase 6a-prime** — architectural review via `hmad-dispatch exec agy` with
   `references/agy-architectural-reviewer-prompt.md`, BASE `41efe98` (5c sha) → HEAD `3cfa4fd`.
   Read `ASSESSMENT:` with `h_mad_extract_verdict.py`, write it into
   `orchestrator_state[audit-cycle-verb].archreview`, then **read it back and compare** — the field
   is not in the schema's `required` array, so `STATE: PASS` can hide a dropped write.
2. **Probe real concurrency before trusting the verb** — no lane has ever exercised it; see Open
   Items for the four specific shapes.
3. **Phase 6a gap analysis** — parse the match rate from `docs/03-analysis/audit-cycle-verb.analysis.md`;
   6b iterate (5-cycle cap) if < 90%.
4. **Live `audit-cycle` run against real agy** — the design's implementation-order step 7, due at
   6/5f: a real verdict on a real audit, not a stubbed one.
5. **Phase 7** — `h_mad_phase7_preconditions.py docs/.bkit-memory.json --feature audit-cycle-verb`
   first; it BLOCKS on a missing or `WITH_FIXES`/`NO` 6a-prime.
6. **J36** — correct "8 of 8" in the spec, design and impl-plan and re-gate (see Open Items).

## Open / Blocked Items

- **Real concurrency is untested by every lane** — status: open, highest-value gap. The stub records
  under an `fcntl` lock, so no test can exhibit: a pass dying before it is reaped · `set -e`
  semantics inside the backgrounded subshell · an empty `pids` array at `--passes 1` · two passes
  interleaving on a shared fd. The revert, mutation and 10×-repeat lanes all exercise the same
  stubbed path and agree with each other while structurally unable to see this.
- **J36 — three gated planning docs carry a false measurement** — status: filed in
  `docs/skill-monitoring.md`, not fixed. Spec (`:238`), design (`:327`) and impl-plan (`:840`) all
  say the report-file slot was "empty on 8 of 8 impl-plan cycles"; the artifacts show **17 of 18
  delivered**, only `cycle7_p1` fell back to `--out`. The plan contradicts *itself* — constraint 2b
  records that single pass. SKILL.md already carries the measured figure per operator ruling. Per
  the v1.15 precedent (an unaudited edit to a gated doc is an ungated doc), correct and re-gate
  rather than silently amend. `repo: /Users/kimhawk/orca/skills · branch: feature/audit-cycle-verb ·
  worktree: none (main)`.
- **`test_verb_no_self_invocation` is not mutation-covered** — status: accepted. The natural mutation
  (make the verb call itself) recurses without bound. It asserts the *absence* of a construct and may
  be structurally immune; agy called it "mostly decoration". Recorded rather than implied clean.
- **Anti-gaming verify for Tasks 1–4** — status: **discharged this session** by the whole-feature
  final pass (it covered Tasks 1–9 and weighted 1–4 heavily, since they had never had one).
- **`PREFLIGHT: FAIL unresolved=codex,agy`** — status: known, cosmetic. Zero candidate panes in this
  worktree; `exec` is pane-independent and was proven live. Do NOT launch panes to green it.
- **Sibling lane** — a HemaSuite `agy`/`codex` pane pair has been alive ~30h (pids 71553/71565),
  bound to another worktree. Not this session's work; do not fan out into that tree.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/hmad-dispatch.sh` (`_cmd_audit_cycle`, Tasks 5–7 + the `size_status` boundary fix)
- `h-mad/scripts/h_mad_wire_registry.py` (J34/J35)
- `h-mad/tests/test_hmad_dispatch_audit_cycle.py` (new, 35 tests)
- `h-mad/tests/test_h_mad_audit_cycle_docs.py` (new, 6 tests)
- `h-mad/tests/test_h_mad_wire_registry.py` (60 → 81 tests)
- `h-mad/tests/specs/audit_cycle_{gating,connections}.mutation.json` (new)
- `h-mad/SKILL.md`, `handoff/SKILL.md`, `handoff/tests/test_handoff_read_todo_sink.py`
- `docs/skill-monitoring.md` (J34, J35, J36), `.gitignore`, `.h-mad/wires.jsonl` (now tracked)
- `~/.claude/settings.json` — added `env.CLAUDE_CODE_ENABLE_TODO_TOOLS=1`
  (backup: `~/.claude/settings.json.bak-20260821-225731`)

**Uncommitted changes:** none. Branch level with `origin/feature/audit-cycle-verb`.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/audit-cycle-verb
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
hmad-dispatch env                                   # substrate: orca; PREFLIGHT FAIL is OK for exec
/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q      # expect 1560 passed
/opt/anaconda3/bin/python3.11 h-mad/scripts/h_mad_wire_registry.py verify \
  --base 41efe98 --rootdir /Users/kimhawk/orca/skills --testpath h-mad/tests   # WIREREG: PASS
/h-mad "audit-cycle-verb"                           # resumes at Phase 6
```

**Interpreter:** bare `python3` is 3.14 with **no pytest** — always `/opt/anaconda3/bin/python3.11`.
Bare `pytest` from the repo root collects the sibling `hematology-paper-writer/` and dies with 23
pre-existing collection errors; always scope to `h-mad/tests`.

**Related docs:**
- `docs/01-plan/features/audit-cycle-verb.impl-plan.md` — Tasks 1–9, the twelve-row connection table,
  and the measured architecture constraints (first-writer-wins `--out`, concatenation under-counting)
- `docs/skill-monitoring.md` — J34/J35 (FIXED), J36 (MONITORING)
- `h-mad/SKILL.md` §"Phase 5 (Implementation) sub-steps" — revert + mutation contracts
