DESIGN-AUTHOR: DONE version=v1.0 path=docs/02-design/features/agy-coder-fallback.design.md lines=945 sha256=b7057f78baa857fb88773a1f6c1cce4fb1bc2e2253d58a1f9d5ba453c0ed60b2

# Report: agy-coder-fallback design v1.0 (first draft)

## What was written, and why
I created the design, which settles DO-1 through DO-7:
- **DO-1/1a.** Each `TDD-STATE` record gets a fifth comma field, the author field
  (`codex|agy|peers-out|invalid:<pct>`), placed between the state file and the fallback tag. The
  header is unchanged. The hook's precedence becomes implementer-invalid, then peer, then the
  unchanged fallback fold. The hook no longer runs `command -v codex`.
- **DO-2.** The class-(a) allowlist has 11 names, checked against the 58-name `init.tools`
  inventory. The doc lists class (d)'s 41 names.
- **DO-3.** A writer `--append KEY=JSON` runs inside the existing flock'd `_mutate`. No entry can
  be lost between the read and the write, which is why this mechanism was chosen.
- **DO-4.** A stdlib RFC 3339 predicate is called from `classify`, outside the validator backend,
  so it applies on both paths. It is scoped to `implementer_switch.ts`. No library format checker
  is used, so the rfc3339-validator hazard does not bind. It is not schema-wide, so no
  `classify_store` run is owed. One reading is given anyway: 0 of 61 live records carry an FR-1 key.
- **DO-5.** 25 names move (17 functions, 8 constants) into `h_mad_target_identity.py`. The Codex
  gate re-imports all 25 under an import guard.
- **DO-6.** Tests point `HOME` at a fixture, so no override flag ships. FR-8 becomes a post-merge
  stage.
- **DO-7.** The carve-out stays applied by prose. The design gives the canonical block (extracted
  from the spec), six per-copy locators, eight control rows, and the corpus and replay designs.

## The tree contradicted the brief or the documents
1. **FR-6, "a shared module", conflicts with "existing tests pass unmodified" if the module is
   new.** This is OQ-A in the design.
   - `test_h_mad_codex_tdd_gate_judge.py` `test_codex_gate_judge_timeout_reason` builds a tree
     holding only the gate, a stub judge and a copy of the identity module.
   - Probed in a TemporaryDirectory, which was auto-removed: the unmodified gate printed a deny,
     and adding one top-level import of a new module gave rc 1 with `ModuleNotFoundError` and no
     JSON.
   - So I placed the policy in `h_mad_target_identity.py`, which is already in that tree, and
     raised OQ-A with two alternatives.
2. **`_relative_target` must stay in the Codex gate.** The same test file monkeypatches
   `module._payload_cwd_base` and then calls `module._relative_target`. Moving the caller would
   bypass the patch.
3. **agy's version is `1.4.0` now.** The spec and plan read `1.3.6`.
4. **The DO-2 inventory log carries no agy version.** Its `init` object holds only `cwd`, `tools`
   and `permission_mode`. DO-2's "with that log's agy version" therefore cannot be met from it.
5. **M-4 is 31 rows over the DO-5 set, not 19.** The 19 are a subset; the 12 extra rows come from
   the allowance functions, `_read_regular_text`, `SAFE_HMAD_SCRIPT_OPTIONS` and
   `_is_production_python`. This is an override of a carried figure, and it is deliberate: the
   census counts over a set my fix grows. Revert by restricting the move to the 10-function
   closure, but the agy gate would then have to copy the rest.
6. **The plan's "Owed → Spec FR-9 residual" bullet was not re-raised**, as instructed. I confirmed
   that spec v1.6 states it, in its "What the joined reading does not see" paragraph.

## Premises verified (all at 29ae3e7b unless noted)
- **`h-mad/` is unchanged since `a8d9ba99`:** `git diff --stat a8d9ba99 HEAD -- h-mad | wc -l` → 0.
- **The judge.** The `Record`, `_active_records`, `_fallback_fold`, `format_state_line` and `main`
  bodies were read with `sed -n`. `JUDGE_BUDGET_S = 40.0`.
- **The hook.** The bodies of `STATE_ACTIVE_RE`, `_read_state` and the authorship block were read
  with `sed`. The shebang is `#!/bin/bash` (3.2.57).
- **The grammar, by scratch probe.** Python `re` and bash 3.2 and 5.3 `[[ =~ ]]` give the same
  groups 1, 2, 3, 4 and 6. A today-shape line and an author of `grok` match nothing.
- **DO-1a census.** It reproduced 6 files, and 7 with the four-pattern variant.
- **Stub sites.** `_tree_b(` matches 9 lines (1 def and 8 calls). `_stub_outcome(` matches 6 (1 def
  and 5 calls). Every asserted outcome is reachable with `peers-out`, so no contradiction was
  reported.
- **The real-judge gate tests' PATH** is `<bin>:/usr/bin:/bin`, with no agy. `which agy` gives
  `~/.local/bin/agy`.
- **M-3** reproduced 8 rows in 3 specs, from 56 hook rows and 36 judge rows. 13 rows anchor inside
  the regions FR-3 rewrites.
- **The M-4 closure** is 10 functions (an `ast` walk). Over the DO-5 set it is 31 of 62 Codex gate
  rows, in 4 specs, with 0 absent and 0 multi.
- **Names tests reach** (found with a grep per moved name): `_safe_shell_command`,
  `_payload_cwd_base`, `SIMPLE_SHELL_COMMAND` and `SAFE_HMAD_SCRIPT_OPTIONS`.
- **The `format` probe** gives `Draft7Validator: True` and `bundled: True`. `rfc3339_validator`
  imports under anaconda 3.11.8. Homebrew 3.15.0 has no `jsonschema`.
- **The predicate, by scratch probe,** gave the same results on both interpreters.
- **The writer.** The `_mutate` flock, `merge_fields`, the `--set` handling and `_parse_value` were
  read.
- **`classify` and `_FORCE_FALLBACK`** were read, and so was the historical schema
  (`additionalProperties` true).
- **Inventory.** 58 names. 11 + 5 + 1 + 41 = 58, all asserted present, with no duplicates.
- **Path keys.** `TargetFile` appears in `tool_info.parameters` in 4 logs. `Cwd` appears in 4 of
  630 `run_command` parameter objects; the first draft said "2 of 172", which counted files, and
  that was corrected before the final digest.
- **hooks.md.** The handler cwd, the 30 s default, the shallow `overwrite`, and that `*` and `""`
  match all tools. The global hooks hold only `orca-status`, whose `PreToolUse` is `ask`.
- **The symlink and the exclude.** `~/.gemini/config/skills/h-mad` → the main checkout.
  `.git/info/exclude` holds `/.agents/skills/`. `check-ignore` on `.agents/hooks.json` gives rc 1.
- **The carve-out contexts each occur once** (Python `str.count`). The L3 selection gives 1 block.
  The failure-recovery row has 0 escaped pipes. The spec's canonical block was extracted from its
  `>` lines.
- **The harness.** `anchor_status`, and `.md`-aware `enclosing_symbol` and `symbol` pins.
- **Assembler and dispatcher.** The assembler's choices, timeout default, `Halt` exit 2 and
  `command_block` prefix rewrite were read. `exec agy` accepts `--model`, `--effort` and
  `--timeout`.
- **HemaSuite.** `HEAD` is `77fb16f51`. All three task commits are ancestors.
- **`_parse_tasks`** returns `WIRE` as one string (probed).
- **State files.** `docs/.bkit-memory.json` is untracked in both repositories.

## Precheck and sweep
- **Precheck:** `PRECHECK: PASS issues=0`.
  - One hard `LINEPIN` (a bare `:60`) was fixed by rewording.
  - The PATH advisories are deliberate: they name new files (the agy gate, the new tests and spec,
    `.agents/hooks.json`, the `HOME`-fixture path).
  - The COUNT advisories are deliberate: "2 files" is a grep result, "56 rows" has no list, and
    "25 names" is the sum of the three sub-lists (10 + 7 + 8, each counted).
- **Sweep, over the whitespace-collapsed doc.** Class (d) lists 41 names and class (a) 11. The
  repeated figures read: 19 ×2, 31 ×4, "25 names" ×3, 17 ×2, 58 ×4, 41 ×3, "13 rows" ×2,
  "8 rows" ×3, 1.3.6 ×2, 1.4.0 ×3. No `file:N` pins.
- **Version History** went through `h_mad_version_history.py`: `VERSION-HISTORY: OK`, with the
  mtime checked before the write.

## Probes
Four scratch scripts under the session scratchpad were deleted: `ts.py`, `line.py`, `m3.py` and
`m4.py`. The B-tree probe used a TemporaryDirectory. An unrelated `mrows.py` is in the scratchpad.
I did not create it, and I left it alone.

## Owed by other documents (none edited)
- **Spec FR-1 and FR-10.** Add the `codex_status` schema description and its `state-schema.md` row
  to the surfaces rewritten. Both say an unavailable Codex lets Claude author, which is false once
  agy is available. The design rewrites them.
- **Spec and plan.** The agy version is now 1.4.0. FR-8 and the SessionStart re-check stamp the
  version they ran against.
- **Spec FR-6 / AC-6.1, if OQ-A takes the recommendation.** "Shared module" =
  `h_mad_target_identity.py`.
- **Plan.** M-4 is 31 rows, and DO-2's version condition cannot be met from the log.
- **Impl-plan.** Committed probes for the M-3/M-4 censuses, the class inventory, the FR-9 corpus
  reading and the replay. FR-8's post-merge stage includes a `PATH_KEYS` commit made RED then GREEN.

## Open questions (for the operator, via the orchestrator)
- **OQ-A**, the policy placement. Recommended: the identity module.
- **OQ-B**, the post-merge FR-8 stage, with the feature recorded COMPLETE only after it.
- **Not resolved:** how Phase 5c provisions state in a worktree. The design states this as
  unclaimed. If the worktree has no state file, all three gates stand down there. That is
  pre-existing, not introduced by this feature.
