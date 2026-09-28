## Summary
This is a gating delta review of the `codex-tdd-gate-defects` impl-plan, v1.1 (`89a67198`) to v1.2 (`a2aca2d5`). It also covers the design v1.3 §D9 erratum (`85b81698`) and the spec/plan propagation (`8322fa04`). It judges the remediation only, against the findings in `impl-plan.audit.v2.p1.md` (3 must, 1 should) and `impl-plan.audit.v2.teammate.md` (1 must, 3 should, 4 nit).

**What I checked.** I checked every v1.2 Version-History disposition against the document and the tree, and each one claimed FIXED is present:
- Task 8 precondition 2 and OQ-I3 are lifted.
- The Source header and the Deviations heading read v1.3, and a sweep for `design v1.2`, `42 cells`, `cells=42`, `two preconditions` and `design delta owed` finds no stale site outside Version History.
- Step 4 has `RAW_TARGET`, `R` and `IN_ROOT`. Step 7 has `_dir_match` on `DIR_SUBJECT` inside the root and on both spellings outside it.
- Residual (c) is present. Items 21–23 and 34–36 are present, as are rows H15B, H18, H18B, H19, H20A and H20B.
- The support literal carries `import os`.
- S8B, G6C, G9, G10 and G11 are present, and the six `c-…` cells claim no coverage (Task 7, Task 10 and OQ-I4 agree).
- The floor test imports under `/usr/bin/python3`.
- P1B uses `git -C <REPO_ROOT>` and has non-vacuity asserts.
- The V1 fixture has a regular `pyvenv.cfg` and the oracle asserts it.
- The `_SUITE_RE` census is `-w`.
- N1–N4 are fixed.

Task 8's hook literals implement design v1.3 §D9 step 3 and step 6 exactly: membership is the quoted `"$R"/*` on the canonical target; the inside subject is `"/${TARGET_PATH#"$R"/}"`; outside the root, the exemption needs both spellings; the basename and extension blocks keep `TARGET_PATH`; and `R` is empty for root `/`.

**What I executed** (all in the session scratch dir, never the tree; `/bin/bash` 3.2.57):
- **The 126-cell differential.** I wrote the plan's step-4 and step-7 literals verbatim into a script and ran them over the 126 cells. The simulated old gate uses today's exemption blocks from `h-mad/hooks/h-mad-tdd-gate.sh:116-131` on the raw target. Active refusals: old 6/5/5, new 6/6/6. Softened: exactly the 6 relative `tests/x.py`/`fixtures/x.py` cells. Tightened: exactly the 8 cells design v1.3 names. The 6 gated cells per shape are the six that item 23 lists.
- **The seven v1.2 Claude-gate mutants** (H15, H15B, H18, H18B, H19, H20A, H20B), each applied to that script. Changed cells over the corpus: 18/9/12/0/12/0/0, matching the plan. Each mutant flips its own row's cell:
  - H15: `./tests/x.py` allow→gated
  - H15B: `fixtures/x.py` allow→gated
  - H18: `tests/x.py` allow→gated
  - H18B: the `re[p]o` root's `tests/x.py` allow→gated
  - H19: the `tests/repo` root's `x.py` gated→allow
  - H20A: `<tmp>/tests/../x.py` gated→allow
  - H20B: `../x.py` gated→allow
- **The `tdd_gate_support.py` first-contents literal.** I extracted it by awk from the plan and imported it under `/usr/bin/python3` 3.9.6 and `/opt/anaconda3/bin/python` 3.11.8. It imports cleanly. With `CLAUDE_ZZZ_PROBE=1` and `HPW_AGENT_BACKEND=claude` set, `hermetic_env(X="1")` holds neither, holds `X == "1"`, and keeps `PATH`.
- **S8 and S8B on the extracted Task 1 `_suite_summary` literal.** `E   assert '1 failed' in x` reads `None` unmutated and under S8, and `(0, 1, 0, False, {'failed'})` under S8B, so S8B is killed.
- **G9, G10, G11 and G6C on a scratch copy of today's `h-mad/hooks/h-mad-codex-tdd-gate.py`,** with Task 7's helper and G9 line applied verbatim. `_payload_cwd_base` and `venv_contained` are stubs, so these four readings are approximate. Each flips its own cell:
  - G9: `[usr-bin-python3-control]` True→False
  - G10: `[doubled-path]` False→True
  - G11: `[script-outside-scripts]` False→True
  - G6C: `[escaping-venv]` False→True
- **Other readings:**
  - The three floor imports under `/usr/bin/python3`: all `ok`.
  - `git grep -nw _SUITE_RE f6b258f0 -- h-mad handoff` gives 2 matching lines; without `-w` it gives 4, and unscoped 11.
  - The P1B corpus: 11 files at `c93da638` (0 files from `h-mad/`). `conftest.py:24` and `h_mad_mutation_harness.py:380` read as cited.
  - Item 28's trap reading: `trap rc=0`, final rc 2.

**Recounts:**
- Task 8: 36 terms sum to 80, with RED 75/5. The six new items each fail at RED on the old verdicts I simulated.
- New items: 38+23+80+17+16+19+18+80+11 = 302.
- Mutation rows by table: 15/8/3/6/6/6/17/37 = 98, with Task 8's list at 36.

I found no blocking defect. There are two should-fix findings, both measurement-class, and three nits.

**Caveats.** I share a model family with the orchestrator and have never been scored against a labelled corpus, so a real codex round on this tree is still owed. I did not run the wire-pin gate, because `--feature` upserts into the tracked `.h-mad/wires.jsonl`, which was already modified at dispatch.

Evidence: 13 files opened, 31 greps run (plus 12 executed probes).

## Must-fix
None

## Should-fix
- **should** — The design v1.3 propagation into the spec (FR-6) and the plan (Claude-gate bullet) at `8322fa04` overstates the rule. Both say a root beneath `tests/` or `fixtures/` never exempts a target. Design v1.3 §D9 step 3, which the impl-plan implements correctly, still exempts an outside-root target when both of its spellings match. So a root's ancestry does exempt writes elsewhere under that ancestor.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.plan.md › `exemptions match the root-relative remainder only, so a root`
  quote: docs/01-plan/features/codex-tdd-gate-defects.spec.md › `so the root's own ancestors (a root beneath `tests/` or `fixtures/`) never make a target exempt`
  - I executed this. With root `<tmp>/tests/repo` and `$1` `<tmp>/tests/other/x.py`, the plan's step 4+7 literals return `allow`, and so does today's gate. The target is outside the root, and both the canonical and raw spellings match `*/tests/*`. Design v1.3 §D9 "Residual, stated" records this outside-root difference from the Codex gate.
  - The impl-plan is correct, so no code or test changes. The two upstream sentences are simply false for outside-root targets. An implementer reading FR-6 alone would expect a refusal that item 35's neighbours do not assert.
  - Repairs, any one: (a) scope both sentences to "inside the root", e.g. "…so a root beneath `tests/` or `fixtures/` exempts no target inside the root; outside it the exemption needs both spellings (design v1.3 §D9 step 3)"; or (b) append the outside-root clause to each. Route the fix to both documents.
- **should** — P1B's published non-vacuity figure "105 such lines" does not reproduce under the plan's own definition, a removed line "whose value holds a `.py` token". The plan's `_PY_TOKEN_RE` finds such a token in 104 path-label lines at `c93da638` (11 files, all 11 contributing). 105 is the count of values containing the substring `.py`.
  class: measurement
  quote: docs/01-plan/features/codex-tdd-gate-defects.impl-plan.md › `the corpus reads 11 files and 105 such lines across all 11`
  - Derivation: `git ls-tree -r --name-only c93da638`, filtered to `*.impl-plan.md` without `/archive/` (11 files). Each file is read with `git show`, matched with the plan's `_PATHS_FIELD_RE` literal, and its value tested with `_PY_TOKEN_RE.search`. That gives 104 matching lines; testing for `".py" in value` gives 105. The same numbers hold at HEAD.
  - The one extra line is `docs/01-plan/features/multi-host-runtime.impl-plan.md:2026`, `**Test file**: none (verified by `smoke_assert.py rehearse`)`. Its backticked span does not end in `.py`, so `_PY_TOKEN_RE` does not match it (and `_NONE_VALUE_RE` would drop it anyway).
  - The test re-reads the figure rather than freezing it, so only the published number is wrong. Repair: publish 104, and state the rule as `_PY_TOKEN_RE.search(value)`. The Version History restates 105 and needs the same fix.

## Nit
- Deviation 16 says Task 8 lands the membership decision "(step 3, after the normalization)". In Task 8's "Script order" it is step 4 ("Canonical target and root membership"); step 3 is the design's numbering. Say "design §D9 step 3 / Task 8 step 4".
- Since v1.2, Task 7 item 5 (`test_venv_token_still_obeys_the_argv_rules`, row G8) is named "AC-3.4's discrimination claim" in Version History, Task 7 and OQ-I4. However, Task 7's AC checklist ("AC-3.4: item 1.") and the AC-coverage row `| AC-3.4 | Task 7, test_shell_venv_token[…] |` do not list item 5. Add it to both, or drop "AC-3.4's" from the claim.
- Item 36 (`test_root_name_glob_characters_are_literal`) states no `codex` stub and no `codex_status`, so it inherits the default `exhausted` fixture. Under H18B the write then reaches the judge rather than `codex-authorship`. The row is still killed, because any judge verdict except `red-measured` denies where the test expects allow. Still, the kill path differs from the executed reading in step 7, which printed only `gated`. Stating "`codex` stub on PATH, `codex_status` absent", as items 34 and 35 do, would make the kill path the one that was executed.
