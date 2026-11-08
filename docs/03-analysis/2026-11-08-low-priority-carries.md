# Low-priority carries — worked 2026-11-08

The operator chose all four buildable groups (carries #7, #19, #22, #29). Items that were standing rulings or watches are listed at the end as settled, so they stop being carried.

## A — scratch leftovers

16 named probe directories (162 MB) were deleted from the 2026-11-06/07 scratchpads and `/var/folders/…/tmp.XQvHmCxplQ`.

Kept:
- every `.md` report in the three old scratchpads (43 of them are not in `docs/`; not reviewed);
- the 6 `~/.local/state/h-mad/verify-hmad-gates/` evidence dirs, which are kept by design.

## B — Tauri `HPW_PATH` default (`d04d7fe9`)

- `lib.rs`: `resolve_tool_path()`. An `HPW_PATH`/`CSA_PATH` already set in the environment wins, and an empty one is ignored. A missing directory gets a launch warning. 3 new Rust tests; a mutant that drops the empty guard is killed.
- Running the never-run sidecar tests found a second bug. `routers/hpw.py` froze `PROJECTS_DIR` at import from a `""` default, which is the cwd. A test wrote into the source tree, and that leaked file (`sidecar/test-project/phase-1.html`) had been committed. `hpw.py` now reuses `projects._projects_dir()`.
- Results: `cargo test` 6 passed. Sidecar, excluding trio: `FAILDIFF: SAME` against HEAD. The 10 `test_build_workflow` failures are pre-existing; there is no build script.
- Environment: a native `stable-aarch64-apple-darwin` toolchain was installed and set as the rustup default. The only toolchain before was x86_64, with no Rosetta. The Tauri build needs `resources/python`, `resources/r-runtime` and `../dist` to exist; empty placeholders were used for the run and then removed.

## C — the three 2026-11-01 landing residuals (re-probed, git 2.54, codex sandbox)

| Residual | Verdict | Evidence |
|---|---|---|
| `--text` refused as a prefix of `--textconv` | **Keep the refusal; correct.** | `git cat-file --text HEAD:f` expands to `--textconv` and fired a textconv marker. On `diff`/`log`/`show` the refusal is redundant but harmless. `status`/`ls-files`/`merge-base` reject `--text` (rc 129). |
| Configured `diff.external`/textconv/fsmonitor runs under admitted `git diff` | **Real; accepted, now measured.** | Plain `git diff HEAD~1` (no flag) fired a configured textconv, as did `log -p`, `show` and `blame`. But `codex sandbox -c sandbox_mode="workspace-write"` refuses a write to `.git/config` (`Operation not permitted`), while the tree and `.gitattributes` are writable. A worker can only attach drivers that already exist, and those are operator-defined. Live config holds `filter.lfs.*` and `core.pager delta` globally, so "refuse if any driver is configured" would block every `git` call. |
| Re-anchor rule passes a rewrite that keeps the added tokens but deletes a larger unrelated region | **Stands by the 2026-11-01 ruling.** | It still reproduces: `same_delta` returns True for a find that also deletes `cleanup(a, b)` and `log(z)`. The superset allowance is the ruling, calibrated on real history (exact equality flagged 7 of 10 legitimate re-anchors). No change without a new ruling. |

## D — hard-link gate divergence (`4dbd5055`)

A listed `scripts/tool.sh` hard-linked to a same-directory test-shaped `.py` (`test_t.py`, `conftest.py`, `t_test.py`) read DENY on Claude but ALLOW on codex and agy, so the listed file was written with no RED.

- Cause: `M:CX-NOT-CODE-LIKE` / `M:AG-NOT-CODE-LIKE` skipped the listing judge when **any** name was `.py`.
- Fix: only a non-empty, all-`.py` name set skips. The `resolved.names and` keeps a directory (no names) on the doc/data skip that owns it. Without it, `all(())` is True, which made `CX-DOCDATA-DIRECTORY` equivalent; it SURVIVED on the first run.
- Tests: 9 new parametrized tests (3 hosts × 3 aliases). The kinds differ by host and are pinned as they are: codex/agy `test-missing`, Claude `no-test-resolved`.
- Mutation: new rows `CX/AG-NOT-CODE-LIKE-ALL`. `codex_gate_listing` 14/14 and `agy_gate_listing` 12/12 ALL_CAUGHT. Guard census: decision=2, anchored=2.
- Not changed: the different-directory case is ALLOW on all three hosts, so it never diverged.

## E — the 11 nits of analysis v5

| Nit | Outcome |
|---|---|
| N1: no judge-level two-readable-plan `listing()` test | **Fixed.** `test_listing_a_target_only_a_later_readable_plan_lists_is_listed`; `L-ANY-PLAN-FIRST` now points at it and is caught there. `LV-RECORDS` stays on the host test, because it mutates the verb's wiring. |
| N2: the plan's "only" vs harness `:2061` | Stamped. Archived plan; no row of the feature reaches the untargeted branch. |
| N3: design D4 "pins that" wording | Stamped. Archived design; the plan already states the caveat. |
| N4: `later_plan_fixture` out of import order | **Fixed** in the 3 host modules. |
| N5: codex `{path}: kind=` lets a path carry a second `kind=` | Stamped. No production parser reads it. Only the test helper's first-match regex (`non_py_gate_support.py:203`) could be fooled, and only by a listed path that literally contains `kind=`. |
| N6: `sh:2` says "production Python writes" | **Fixed.** The comment names listed non-`.py` files too. Nothing pins the line. The test name `test_hook_line_names_both_gates` is accurate (it checks codex and Claude), so it is kept. |
| N7: `Path.suffix` vs `.endswith` spellings | Stamped. They differ only for a file named exactly `.py`, which `_is_production_python` takes first. |
| N8: M5 reach figures | Stamped. Archived spec. |
| N9: same-directory residual has no test | **Closed by D.** |
| N10: `L-READ/MATCH-RECORD` killer's message names another property | Stamped. The value is right; only the message is cosmetic. |
| N11: `H-LIST-TARGET`/`H-DOCDATA-NO-ARM` carry `symbol` `_read_listing` | Stamped, **not** changed. For `.sh` the harness derives `symbol` as the nearest preceding `name() {` (`h_mad_mutation_harness.py:1131`, a documented proxy), and that is `_read_listing`. "Correcting" it would read as anchor drift. |

## Settled — no longer carried

- Run 8 attempts 1–2: evidence only, never scored. That is a standing rule, not a task.
- Watch-only triage rows 19 and 51: watched, with no action defined.
- `READY_TO_MERGE` under a narrowed rubric; AC-9.3 resting on v4's census; the 2026-11-06 machine-wide `pkill` disclosure; the HemaSuite restores static limit (2525 sites); autopilot `b1a99532` without a notepad closeout. Each is a recorded acceptance or a disclosure, and none has a next action.
## F — the 2026-10-31 stamp residuals

Every later handoff carried these as one line, "unchanged since 2026-10-31", with no content. The list lives only in `docs/handoffs/2026-10-31-main__skill-backlog-clusters-a-d.md:75-79`. An earlier draft of this doc (`cbef15f3`) called them unrecoverable; `0e3beea7` corrected that, and the operator then chose all four.

| Residual | Outcome |
|---|---|
| Name map: the `*test_*` skip hides `h_mad_test_boundaries_check.py` | **Fixed.** `h_mad_derive_test_path.sh` reads the basename the way `_is_production_python` does. Wider than recorded: HPW's `latest_test_data.py` was hidden too, and a pytest-collected `x_test.py` was mapped as production. 6 new parametrized tests; rows `NM-TEST-SUBSTRING`/`-SUFFIX`/`-DIR` 3/3 caught. |
| `h_mad_archreview_cycle.py` writes no `.assembled` receipt | **Fixed.** `stage` calls `stamp_assembled(prompt, residue=residue)` after writing, as the TDD assembler does. 1 new test; row `ASSEMBLED-STAMP-ARCHREVIEW` caught. There is no logged instance of the false advisory; the fix is on mechanism. |
| Install check reads no user-level agy `hooks.json` | **Fixed.** By default it also reads `<agy skills root>/../hooks.json` (`~/.gemini/config/hooks.json`, `agy-runtime.md:33`). Deriving it from the root keeps tests hermetic. Help text and `helper-scripts.md` updated. 1 new test; row `AH-GLOBAL-HOOKS` caught. The live check still reads `INSTALL: PASS`. |
| Codex default hook timeout unmeasured | **Measured** (codex-cli 0.167.0, disposable `CODEX_HOME`, `--dangerously-bypass-hook-trust`, scratch hook only; copied credentials deleted after). `timeout` is in **seconds** and honoured: `"timeout": 10` → killed at ~8–10 s, `PreToolUse Failed`. With no timeout, or `"timeout": 120`, the hook was cut at ~36–38 s with `tool call cancelled`, not `Failed`. Under `codex exec`, then, a hook running past ~38 s is cancelled whatever its timeout. A judge budget above ~38 s cannot complete there; the cancelled tool call does not run, so this fails closed. No timeout value was set. |

## Found while measuring F4 — codex likely never runs the h-mad gate (operator decision)

Codex 0.167.0 runs a hook only with a persisted trust record (`[hooks.state."<hooks.json>:<event>:<i>:<j>"]` with `trusted_hash` in `~/.codex/config.toml`) or under `--dangerously-bypass-hook-trust`.

- `~/.codex/config.toml` holds records for the 4 global graft hooks only. There is none for `~/orca/skills/.codex/hooks.json`'s PreToolUse entry, which is `h-mad-codex-tdd-gate.py`.
- A scratch project's `.codex/hooks.json` never ran, even with the project trusted.
- `hmad-dispatch exec codex` passes no bypass flag (no `hook-trust` string anywhere in h-mad).
- The gate's tests drive the hook script directly, so they cannot see this.

**Not yet proven** by a marker in a real dispatched codex run. That is the next probe. The fix is the operator's call: trust the hook once interactively so a record is persisted, or pass the bypass flag from dispatch.
