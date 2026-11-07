# Change review — round 2 remediation, working tree against 2c173c43 (simple-r2.diff: S1 effort env gate, S2 _enc positive control + \U escape, S3 splitlines name check, re-aimed census row) — GATING

## Evidence
- read: 6 files. The whole r2 diff (346 lines). h_mad_assemble_tdd.py 125-130, 816-818, 1068-1098, 1336-1342. h_mad_wire_pin_gate.py `_TASK_RE` 53-59. helper-scripts.md: the `effort_env_not_printable` and `diff_path_invalid` text. Both mutation specs (the touched rows). The test helpers in test_h_mad_assemble_tdd_agent.py.
- ran: 11 commands. A `git clone --shared` at 2c173c43 plus `git apply simple-r2.diff`. All 7 touched files are `cmp`-identical to the working tree.
- tests run: 14 files in the clone, `858 passed in 151.80s`. The files: test_h_mad_assemble_tdd.py, test_h_mad_assemble_tdd_agent.py, test_h_mad_guard_census.py, test_h_mad_assemble_audit.py, test_h_mad_ac_census.py, test_grok_audit_surface_assembler_pin.py, test_hmad_dispatch_exec.py, test_h_mad_tdd_gate_peers.py, test_h_mad_codex_gate_tmp_reports.py, test_h_mad_archreview_cycle.py, test_h_mad_backlog_cycle.py, test_h_mad_new_caller_carveout_copies.py, test_h_mad_codex_runtime.py and test_h_mad_agy_authorship_docs.py. This includes `test_no_agent_output_is_byte_identical_to_base`, which needs history.
- I applied 10 mutation rows by hand against their named nodes. Every `find` occurs exactly once, and every row was killed for its own reason:
  - at-effort-env-line-break-printed-raw: the run printed PASS with `--effort 'medium` / `ASSEMBLE-TDD: HALT forged' \`
  - at-halt-detail-printed-unescaped: a raw `a` / `ASSEMBLE-TDD: PASS forged…` reached stdout
  - rv-name-check-misses-unicode-line-breaks: `[untracked-line-separator]` reached PASS
  - rv-newline-dropped: `diff_path_missing` was printed where `diff_path_invalid` was expected
  - rv-bare-cr-allowed: `[untracked-carriage-return]` reached PASS
  - at-line-broken-argument-passes-the-gate, at-argument-gate-never-halts, at-argument-gate-skips-list-values: same kills as in round 1
  - path-naming-the-repo-is-a-pathspec (re-aimed): `assert ('b.py:2' in {'sub/a.py:2': …})`. The mutant drops `.` and diffs only `sub`, so it is not equivalent.
  - census-dot-excuses-an-unmatched-path: printed DONE

Scenario checks that held:
- S1 closes the round-1 scenario. The test that used to be my reproducer now halts `effort_env_not_printable` with rc 2 and no forged line. The check sits after the `policy is None` early return and inside `main`'s `try`, so its `!r` detail is printed through the shared Halt handler. A non-printable env value on a phase that ignores the env stays inert, which is correct because that value is never printed.
- S2: `test_a_halt_detail_is_printed_as_one_escaped_line` pins `\x0a`, `\x1b` and `\U000e0001` (the new 8-digit form) at the Halt-detail printer, and its row kills the unescaped printer.
- S3, real untracked names: with `--base-ref HEAD` and `--agent codex`, untracked files named `Screenshot 2026-11-07 at 10.00.00 AM.png`, `nb\xa0sp.py`, `tab\tname.py` and `zwj‍x.py` gave rc 0 PASS, and all four were `listed` in the prompt. Only names containing a `splitlines()` break or a NUL are refused.

## Must-fix
None

## Should-fix
- The gate docstring's new claim, "values read from files are escaped with _enc where they are printed", is false for two stdout lines. Values cut from the impl-plan are printed raw: `inlined-sections:` (plan headings) and `referenced-not-inlined:` (§ citations, `_REF_RE` `[^"\n]+`). I executed a RED run whose Task 1 body cites `§"Nowhere\x1b[2J\tx"`: rc 0, and stdout carried `'  referenced-not-inlined: "Nowhere\x1b[2J\tx"'` with a raw ESC and a raw TAB. The values come from `splitlines()`, so no line break and no forged token is possible; the defect is the overclaim. A reader who trusts the docstring will not look for this. Either `_enc` those two joins, or narrow the docstring to "values read from files are one line by construction (`splitlines`), and Halt details are `_enc`-escaped". The env half of the docstring ("the one environment value that is printed (HMAD_GREEN_EFFORT)") also skips two environment-derived values that print raw: `args.python` from `shutil.which` (a PATH entry) and the default `sys.executable`. Both are contrived to exploit. (`meta["task"]` is safe: it can only be the argv-gated `--task`, matched case-insensitively.)
  quote: h-mad/scripts/h_mad_assemble_tdd.py:1082 › `    read from files are escaped with _enc where they are printed."""`
  quote: h-mad/scripts/h_mad_assemble_tdd.py:1341 › `              + ", ".join(f'"{r}"' for r in meta["unresolved_refs"]))`

## Nit
- `_enc` at the agy `check_line` site and the `prompt_unwritable` OSError site is still unpinned; only the Halt-detail site has a test and a row. Neither site can carry a line break (`check_line` is a `splitlines()` product, and the OSError text quotes its filename with `repr`), so the gap is defense in depth only.
  quote: h-mad/scripts/h_mad_assemble_tdd.py:1305 › `        print(f"  {prompt}: {_enc(exc)}")`
- Carried from round 1 and kept deliberately: the argv gate refuses NBSP, U+202F and ZWJ, while the S3 name check now allows them. The two routes therefore disagree on the same characters. That is defensible, because names are files that already exist and argv is typed, but it is worth one sentence in helper-scripts.md:34 so the asymmetry reads as intended.
