# Plan: install check warns when codex will skip the h-mad gate (scout row `codex-hook-trust-unseen-by-install-check`)

**Status:** APPROVED 2026-11-08 by the operator ("Approve the plan; I'll run the step-0 probe"). Drafted on Hawui-Macmini, main @ `0129b848`. Row verdict: yes (operator, 2026-11-08). Step 0 done (findings below). Steps 1–4 implemented 2026-11-08.

**Deviations from the steps below.**
- `check()` is untouched. `main()` calls `check_codex_hook_trust` directly, so no kwarg was needed.
- An env override `HMAD_CODEX_HOOKS_JSON` was added for the hooks-file default, and `conftest.py` points it at an absent path.
  - Why: the suite runs inside this repo, whose real `.codex/hooks.json` holds the gate, so GREEN printed an advisory into 13 exact-output install-check tests.
  - Choice: operator, 2026-11-08.
  - It is pinned by a test and by the mutation row `codex-trust-hooks-env-override-is-read`.
- The mutation rows are in a new spec, `install_check_codex_trust.json`: 7 rows, ALL_CAUGHT.
  - Its first row was written by hand, because `--append-row` needs an existing row to copy the layout from.
- Step 5's full-suite `FAILDIFF` has not run yet. The install-check and doc tests passed (272).
  - The 1 failure, `test_codex_hook_allows_explicit_test_command`, also fails at `0129b848`.

## Goal
`h_mad_install_check.py` reports the Claude and agy hook wiring but says nothing about codex.
Codex (0.166/0.167) runs a project hook only when `$CODEX_HOME/config.toml` holds a trust record
for it, or when `--dangerously-bypass-hook-trust` is passed. `hmad-dispatch exec codex` now passes
that flag (`_codex_hook_trust_arg`, `09c36baf`/`1d92ef9c`), but a codex started by hand gets
neither, so the Phase-5 gate silently does not run. Make that visible: one advisory detail line per
untrusted gate entry. Nothing is repaired, and the `INSTALL:` verdict does not change.

## Measured facts (2026-11-08, this Mac)
- Trust records live in `~/.codex/config.toml` as
  `[hooks.state."<abs hooks.json path>:<event_snake>:<group_idx>:<hook_idx>"]` with
  `enabled = true` and `trusted_hash = "sha256:<hex>"`. Seen only for `~/.codex/hooks.json`
  (`post_tool_use`, `session_start`, `user_prompt_submit`, `stop`), on codex-cli **0.166.0**.
  No record exists for any project `.codex/hooks.json` (skills or HemaSuite).
- The gate entry is `PreToolUse` → group 0 → hook 0, command
  `python3 $HOME/.agents/skills/h-mad/hooks/h-mad-codex-tdd-gate.py` (`.codex/hooks.json` here
  and in HemaSuite).
- What `trusted_hash` hashes is **unknown**. The plan therefore never claims a record is valid; it
  only distinguishes "no record" from "record present".
- `install_check` keeps its summary to `INSTALL: PASS|FAIL issues=N|UNREADABLE`, and consumers
  read that line by substring. New findings ride **detail lines**, the same rule the mutation
  harness applies to `unclassifiable=`/`skipped=` (`helper-scripts.md`).

## Step-0 findings (2026-11-08 18:4x, Hawui-Macmini)
- **The probe left no trace.** Neither `~/.codex/config.toml` nor the Orca account home changed:
  `diff` against `config.before.toml` is empty, and that config's mtime is 18:30, before the probe was
  set up. No `rollout-*` was newer than the snapshot. So the probe did not reach a codex home this
  check can see, or codex never asked for approval.
- **The live codex home here is Orca's per-account home, not `~/.codex`.** `CODEX_HOME=~/Library/Application Support/orca/codex-accounts/<uuid>/home`.
  `~/.codex/config.toml` is stale here (mtime 12:05). The check must read `$CODEX_HOME` and name the
  config path it read in every line. A codex started outside Orca uses `~/.codex`, so the two homes
  can disagree.
- **The project key shape is confirmed from an existing record** in the Orca home:
  `[hooks.state."/Users/kimhawk/orca/HemaSuite/.codex/hooks.json:pre_tool_use:0:0"]`. That is an
  absolute path, `pre_tool_use`, and `0:0`, which matches the Key rule.
- **That record has `trusted_hash` but NO `enabled` key.** So an absent `enabled` is not
  `enabled = false`. Design change: DISABLED only for an explicit `enabled = false`; otherwise
  RECORDED. A test pins the absent-`enabled` case.
- **HemaSuite does have a record on this Mac**, which differs from the Studio's "no record for either
  repo". The skills repo has none. Whether a record without `enabled` is honoured is unknown; the
  RECORDED line already says it is not verified.

## Design
- New function `check_codex_hook_trust(hooks_files, codex_config) -> list[str]`, stdlib only (`tomllib`).
- **Inputs.** `--codex-hooks-json` (repeatable) defaults to `<git toplevel of cwd>/.codex/hooks.json`,
  the same derivation `_codex_hook_trust_arg` uses. `--codex-config` defaults to
  `${CODEX_HOME:-~/.codex}/config.toml`. A test redirects both and never reads the real home.
- **Scope.** Only hook entries whose command is the h-mad gate are checked. A user's other hooks are
  not this skill's business. The gate command string is a second copy of `GATE` in
  `hmad-dispatch.sh`; a test pins the two equal so they cannot drift.
- **Key.** `f"{hooks_json.resolve()}:{snake(event)}:{gi}:{hi}"`, where `PreToolUse` becomes `pre_tool_use`.
- **Output.** Detail lines, outcomes kept distinct per the fail-closed rule:
  - no `.codex/hooks.json`: nothing (codex is not wired here).
  - no gate entry in it: nothing.
  - record absent: `CODEX_HOOK_UNTRUSTED:<key> — a codex started by hand skips the h-mad gate here; hmad-dispatch exec passes --dangerously-bypass-hook-trust`.
  - record present, `enabled = false`: `CODEX_HOOK_DISABLED:<key>`.
  - record present and enabled: `CODEX_HOOK_TRUST_RECORDED:<key> (hash not verified)`.
  - config or hooks.json unreadable or unparseable: `CODEX_HOOK_TRUST_UNKNOWN:<path> reason=<r>`.
    This line must never render as "trusted".
- **Verdict impact:** none. The advisories go after the issue lines and do not count toward `issues=`.
  The gap is accepted, and turning it into a `FAIL` would break every run on a host that uses
  dispatch only.

## Steps (H-MAD, test-first)
0. **Probe (operator, interactive, about 2 minutes).** In a throwaway repo with a copy of the gate's
   `hooks.json`, start `codex`, approve the hook once, and read the new `hooks.state` key. This
   confirms the `<event_snake>:<g>:<h>` shape for a project file and for `pre_tool_use`, which so far
   is inferred only from the global records. If the shape differs, the Key rule above is rewritten
   before step 1.
1. **RED.** `h-mad/tests/test_h_mad_install_check_codex_trust.py`. Cases: no record → UNTRUSTED;
   record → RECORDED (with "hash not verified"); `enabled=false` → DISABLED; an unparseable config,
   a missing config, and an unparseable hooks.json → UNKNOWN, never RECORDED; a non-gate hook →
   silent; no `.codex/` → silent; `INSTALL:` summary and `issues=` unchanged when an advisory fires;
   the gate string equals `hmad-dispatch.sh` `GATE`. One subprocess test through `main()` with
   redirected `--codex-config`/`--codex-hooks-json`.
2. **GREEN.** Implement in `h-mad/scripts/h_mad_install_check.py`. Keep `check()`'s signature
   additive (a new kwarg with default `()`), and let `main()` wire the defaults.
3. **Mutation rows.** Add them to `h-mad/tests/mutation-specs/install_check_roots.json` (or a new
   `install_check_codex_trust.json`) **with `h_mad_mutation_harness.py <spec> --append-row`**, not by
   hand. This dogfoods the row #6 pointer. Guards: absent-record branch, enabled check, unreadable
   ≠ recorded, gate-only filter, summary-unchanged. Then run `--check-anchors` over **all** specs
   (2026-11-08 learning: re-shaping a line breaks anchors in specs you did not touch).
4. **Docs.**
   - `h-mad/references/codex-runtime.md` §"That trust does not last": name the new advisory line
     after "A codex session started by hand…".
   - `h-mad/references/helper-scripts.md`: the `h_mad_install_check.py` entry.
   - The module docstring: a fourth thing the check reads.
5. **Verify.** Run the install-check tests (3 existing files plus the new one), the docs tests, and
   the full h-mad+handoff suite via `h_mad_failure_diff.py run --base <pre-change sha>` →
   `FAILDIFF: SAME` or `FIXED_ONLY`. Then live: `h_mad_install_check.py` in `~/orca/skills` prints
   `CODEX_HOOK_UNTRUSTED:` for the PreToolUse gate today.
6. **Close.** Stamp row `codex-hook-trust-unseen-by-install-check` LANDED with the sha, and confirm
   the census OPEN count drops.

## Risks
- **The trust-key format is codex-version-specific (0.166 here, 0.167 on the Studio).** If codex
  changes it, every record reads as absent and the advisory becomes always-on noise. Mitigation:
  step 0 probe, and the line names the key it looked for, so a format change is diagnosable.
- **The hash is unverifiable.** "Recorded" can still be stale after a `hooks.json` edit. The line
  says so outright and never claims the gate is enforced.
- **Worktrees.** Every Orca worktree has its own `hooks.json` path, so the advisory is correct to
  fire in each one. That is the defect itself, not noise.
- **A duplicate gate string** (Python vs shell). Mitigation: the equality test.

## Out of scope
- Writing trust records or approving hooks. The check repairs nothing (module docstring).
- Recomputing `trusted_hash`.
- Changing `hmad-dispatch` behaviour.

## Order with in-flight work
After the failure diff (#3) and the append-row pointer commit (#6), so step 3 can follow the new
pointer. Not coupled to the graft→trail commit (#8).
