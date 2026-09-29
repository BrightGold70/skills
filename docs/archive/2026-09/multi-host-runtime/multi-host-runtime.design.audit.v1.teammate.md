## Summary
This is a gating pass on `docs/02-design/features/multi-host-runtime.design.md` at b327e8bf. The working-tree copy is identical to the commit: `git diff b327e8bf -- <doc>` is empty. Many of the design's tree premises reproduce: DP1 gives 122/13 and 71/12. A scratch expander of the D2.7 grammar gives 22 entries, 13 of them branching with 45 branches, 54 branches in all and 25 zero cells. The per-axis catch-all leaves 0 uncovered hits. DP3 reads `ANCHORS_OK specs=3 mutations=17`, the DP11 strings reproduce 11 of 11, and DP5/DP6 event counts and the DP9 test counts also reproduce. But several load-bearing claims about the host logs and the design's own interfaces do not survive the tree:
- grok's `available_commands.commands` is a list of plain strings, not objects carrying `.name`.
- `hmad-dispatch` interleaves non-JSON `#hmad-beat` lines into every exec log.
- `split_agy_root` cannot enumerate the "checkout skill names" it keys on.
- The missing-`pattern` fixture yields two kinds under the stated stage order.
- AC-8.3's `HMAD_HOST=claude` suite run was dropped from the plan without saying so.

Axis C (spec v1.2 at b51c5b2a, 50 AC ids):

| Classification | AC ids |
|---|---|
| implemented-as-written (46) | AC-1.1, 1.2, 2.1–2.5, 3.1, 3.2, 3.4, 3.5, 4.1, 4.3–4.6, 5.1, 5.3–5.7, 6.1–6.6, 7.1–7.3, 8.1, 8.2, 8.4, 9.1–9.4, 10.1–10.6, 12.1, 12.2 |
| restated (3) | AC-3.3, AC-4.2, AC-5.2 |
| absent, in part (1) | AC-8.3 (the "every existing test passes with `HMAD_HOST=claude`" half) |

Evidence: 38 files opened, 52 greps run (including 7 executed re-derivations: calibration, D2.7 expander, per-axis coverage, check-anchors ×2, codex `strings` census, log walks).

## Must-fix
- **D10 step 3's grok check reads a field that does not exist, so every grok smoke prints `FAIL V-11.1 grok did not list h-mad` and `recover` reverts a good integration.** In the committed probe log `docs/03-analysis/probes/grok-codex-fallback/stream-json.2026-09-28.ndjson`, each `available_commands` event has keys `commands, tools, type`. `commands` is a list of 316 plain **strings**; the first is `"compact"`, and `"h-mad"` and `"handoff"` occur as bare strings. `~/.grok/docs/user-guide/14-headless-mode.md` §streaming-json also describes it as "Tool and slash command lists (`tools`, `commands`)". A `commands[].name` read either raises on `str` or finds nothing. Rehearsal R5/R1 fixtures hand-made to the design's text would carry `{"name": …}` objects and pass, so the rehearsal cannot catch this. The real-log replay stops at step 1 ("no adapter read") and never reaches step 3. Repair: test `"h-mad" in commands`. Optionally, accept either a `str` or a `{"name"}` element, and add a rehearsal case built from a line copied verbatim out of the committed probe log.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `` For grok, some `available_commands` event's `commands[].name` must include ``
- **The `missing_key:pattern` disjunct fixture yields two `(kind, reason)` pairs under D2.2's stage order, so its exact-set assertion fails.** D2.2 skips an element's *field* checks when a key is missing. `BAD_PATTERN` is a separate later step inside the same registry stage, and it fires "for each element whose `pattern` is not a `str`". An absent `pattern` (`None`) is not a `str`, so the fixture produces `REGISTRY_UNREADABLE reason=missing_key:pattern` **and** `BAD_PATTERN`. Suppression rule (a) returns only *after* the registry stage, so it does not remove the second line. The same class covers any registry step that runs after the per-element step and does not honour "missing key ⇒ skip". Today that is `BAD_PATTERN`. `DUPLICATE_ID` is already guarded by "over the ids that passed `bad_id`". Repairs, any one: (1) `BAD_PATTERN` skips every element that emitted a `missing_key:*` line; (2) `BAD_PATTERN` and `DUPLICATE_ID` are not computed once any `REGISTRY_UNREADABLE` line exists; (3) `BAD_PATTERN` applies only when the `pattern` key is present.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `` for each element whose `pattern` is not a `str`, or whose ``
- **`split_agy_root` is keyed on "each checkout skill name `n`", but its signature receives no repo and no name list, so neither the attribution rule nor the fail-closed "matches no `(n, K)` pair" rule can be implemented as written.** `check_siblings` enumerates names from `sorted(repo.glob("*/" + CHECKOUT_MARKER))` (`h-mad/scripts/h_mad_install_check.py:120`). The partitioner is handed only `lines, skills_dir, installed`. The design's own mutation killer depends on name enumeration: the "trailing space removed" mutant is killed by a fixture with `h-mad` and `h-mad-x`. That kill works only if `n` ranges over checkout names. Repairs: (a) add a `names: Iterable[str]` parameter, computed in `check()` by the same glob `check_siblings` uses; or (b) pass `sibling_repo` and glob inside. Parsing the name out of the line would make the "unattributable line" rule vacuous and needs its own control.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `` For each checkout skill name `n` and kind `K`, a line counts as that pair ``
- **D12 and the Single-source compliance claim rest on a "`host_parity` table parser" that D2.1's interface does not expose.** D2.1 lists `ParityPaths`, `Failure`, `live_paths`, `CATCH_ALL_AXES`, `A4_BRANCHES`, `EXCLUSION_SUFFIXES`, `a4_pattern`, `expand_branches`, `ParityResult` and `check`. None of them returns an adapter's rows, and `check()` returns failures only. `test_host_runtime_docs.py` must read the `advisor`, `task-tools`, `session-id-env` and `claude-projects-store` rows. With no named public function, a second parser in the doc tests is the path of least resistance, which is exactly what the invariant forbids. Repair: add something like `adapter_rows(text) -> list[Row] | TableError`, used by both `check()` and D12, and list it in §API / Interface Changes.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `` Table rows are read with `host_parity`'s table parser. ``
  quote: docs/02-design/features/multi-host-runtime.design.md › `the adapter table parser is shared by the gate and the doc tests`
- **Axis C, AC-8.3 is partly absent. The plan's owner for its first half, the existing `test_h_mad_context_budget.py` run once more with `HMAD_HOST=claude`, was dropped without saying so.** The design never names AC-8.3: `grep -n 'AC-8.3\|exported\|HMAD_HOST=claude'` on the design gives 0 matching lines. Its Test Plan commands run the coupled suite once, under whatever `HMAD_HOST` the shell has. D8's byte-identity budget arm covers only the "sample run's stdout is byte-identical" half. The design's Overview says it "keeps every plan decision, with the exceptions listed" in §Supersedes, and this one is not listed. Repair: add `HMAD_HOST=claude python3 -m pytest -q h-mad/tests/test_h_mad_context_budget.py` (reading the pytest summary line) to the Test Plan commands, and state that the suite runs with `HMAD_HOST` explicitly unset (`env -u HMAD_HOST`).
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `once with `HMAD_HOST=claude` exported for that run`
  quote: docs/02-design/features/multi-host-runtime.design.md › `` `python3 -m pytest -q h-mad/tests handoff/tests handoff/scripts`, the full coupled suite ``
- **Axis C, AC-3.3 is restated.** The spec still says "Fourteen kinds means fourteen fixtures". The design builds 42: 36 disjuncts plus 6 splits, each asserting a `(kind, reason)` pair. The design is stricter, so this is not a defect in the design. But plan v1.2 Next Steps (4) owed this restatement to the spec, and spec v1.2's Version History records only AC-12.2 and the FR-10 residual as landed. The divergence therefore still has to land in the spec before the gate clears.
  class: measurement
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `Fourteen kinds means fourteen fixtures.`
  quote: docs/02-design/features/multi-host-runtime.design.md › `**D2.6 The 42 kind fixtures.**`
- **Axis C, AC-4.2 is restated.** The spec names one A4 fixture, `~/.claude/foo`. The design splits A4 into three branch fixtures and three branch removals. This is broader, and it is the plan-owed item (4), which the spec has not taken.
  class: measurement
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `A4 `~/.claude/foo``
  quote: docs/02-design/features/multi-host-runtime.design.md › `` `test_catch_all_axis_alone_reports_its_fixture[A1|A2|A3|A4-tilde|A4-home|A4-home-braced]` ``
- **Axis C, AC-5.2 is restated conditionally.** The spec fixes reasons (i) and (ii) as "`exit 1`, which grok treats as fail-open" and "the gate reads a top-level `file_path`/`path`". The design makes (i) branch-dependent and re-points (ii) to "none of the gate's read paths". The doc test pins no reason-(i) token, so the spec's form of (i) is left to review. The plan owed this to the spec (item 1). It has not landed, and the sibling's FR-0 branch is still unrecorded.
  class: measurement
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `refuses by `exit 1`, which grok treats as fail-open`
  quote: docs/02-design/features/multi-host-runtime.design.md › `Reason (i) takes the branch's wording.`

## Should-fix
- **The D10 log readers are specified as pure NDJSON or line-exact text, but `hmad-dispatch` writes non-JSON `#hmad-beat` lines into the same `--log`, and it states that a beat "can in principle land mid-line and corrupt one JSON event".** See `h-mad/scripts/hmad-dispatch.sh:2490-2506`. The committed agy log contains 2 such lines (lines 37 and 96: `#hmad-beat 00:47:54Z agy running 120s`). For codex, a beat can land between `exec` and its command line, and "the line after `exec`" is then the beat. Required rules:
  - skip lines that are not a JSON object;
  - for codex, take the first non-`#hmad-beat` line after `exec`;
  - add a rehearsal case per host with a beat interleaved.

  The real-log replay's "must not crash" would catch only the agy half of this.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `the line after each line equal to `exec``
- **The "input, never output" rule still matches text, and its residual is unstated.** A shell event whose input only *mentions* a script, for example `sed -n 1,80p h-mad/scripts/h_mad_state_write.py` or `grep h_mad_resume_decision.py h-mad/SKILL.md`, counts as step 2's "script run". Codex matches "every exec event". Before the adapter read, that prints FAIL and reverts a good integration. Conversely, a `grep codex-runtime.md h-mad/SKILL.md` exec counts as step 1's "adapter read". This is the same class as supersede item 2: an input mention is not an execution, and an input mention is not a read. Either narrow step 2 to an interpreter invocation (`python3? … h_mad_[a-z0-9_]+\.py` as the executed argument, or `hmad-dispatch` as argv[0]) with rehearsal cases for both directions, or state both residuals beside the two already listed.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `an event counts only by what the host **asked for**`
- **For grok, V-11.1's "loaded h-mad's `SKILL.md`" clause is dropped.** Step 3 checks `SKILL.md` loading for codex and agy only. For grok, a listing in `available_commands` shows the skill is *available*, not that it was loaded. The spec's grok `init` clause is an addition to the `SKILL.md` clause, not a replacement for it. Either add a grok `SKILL.md` evidence rule, or record the narrowing as spec-owed next to supersede item 1.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `The transcript shows the host loaded h-mad's `SKILL.md` and read`
  quote: docs/02-design/features/multi-host-runtime.design.md › `For codex and agy, some event's`
- **D2.4 strips backticks (step 8) only after the cell-count check (step 7) has taken the row's id.** D9.3 writes ids backticked, so a `cell_count` row whose first cell is `` `advisor` `` gets `id=-`. Rule (e) then does not count it as present, and `ROW_MISSING` fires too, so the `cell_count` fixture yields two pairs if it uses a backticked id. Repair: strip the backticks before the id rule in step 7.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `The `construct` and `status` cells may carry one surrounding pair of backticks`
- **Both agy "typically" rewrites point at "(§Install)", but D9.1 gives `handoff/references/agy-runtime.md` no `## Install` section.** Only the h-mad codex, agy and grok adapters get one. So the handoff sentence cites a section that does not exist in its file. Repair: point it at `h-mad/references/agy-runtime.md` §Install by path, or give the handoff wording without the section reference.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `(§Install), when it exists`
- **The phrase the agy rewording promises to keep is not in the tree.** `h-mad/references/agy-runtime.md:25` reads "Do not run it as a gate here". `grep -n -i 'phase gate\|as a gate'` finds no "Phase gate" in that paragraph. An implementer who keeps the design's quoted text would change the sentence, and one who searches for it will not find it.
  class: measurement
  quote: docs/02-design/features/multi-host-runtime.design.md › `It keeps "do not run it as a Phase gate here"`
- **Anchor-uniqueness is scoped to "the three existing mutation specs", but strand 4 edits both `SKILL.md` files, which many more specs anchor on.** At HEAD, 14 spec files under `h-mad/tests/mutation-specs/` have mutations with `file: SKILL.md`, among them `tail_signature_pass.json`, `context_budget_docs.json` and `hook_wiring.json`. So do 3 files under `handoff/tests/mutation-specs/`: `read_auto_resolve.json`, `takeover_mode.json` and `skill_body_renderer_args.json`. I did not check that the harness resolves those to `handoff/SKILL.md`. The Test Plan's `--check-anchors h-mad/tests/mutation-specs/*.json` covers the h-mad 99 but omits the handoff directory. Rule over the class: every spec whose `file` names a file this feature edits, which is `h-mad/tests/mutation-specs/*.json` plus `handoff/tests/mutation-specs/*.json`. The h-mad 99 read `ANCHORS_OK mutations=907` today.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `The three existing mutation specs over the touched`
  quote: docs/02-design/features/multi-host-runtime.design.md › `--check-anchors h-mad/tests/mutation-specs/*.json`
- **Strand 1's RED reasons are impossible in the stated order.** The test module is written first and `host_parity.py` second. Until `host_parity.py` exists the module fails at import, which is a collection error, not "RED with `REGISTRY_UNREADABLE reason=missing_file`". Nor can an adapter node be "RED on its vacuity guard" yet. Either write a stub `host_parity.py` first, or state the RED as an ImportError at collection and move the stated failure reasons to after the module lands.
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `The registry node is RED with`
- **D12 pins the bare token `none` for the codex and agy budget substitute. That is too weak to discriminate.** Any sentence in that section containing the word "none" (for example, one saying the host has "none" of a documented session-id variable) satisfies it, so a section that never states the budget substitute can still pass (unchecked against real adapter text, which does not exist yet). Pin a phrase such as `substitute: none` (see `invariants.base.md` §"Test discrimination").
  class: build
  quote: docs/02-design/features/multi-host-runtime.design.md › `and `/context` (grok) or `none` (codex, agy)`
- **DP2's "61 branch × declared-skill cells" is measured over the 13 *branching* entries.** The probe D8 defines prints "every branch × declared-skill cell" across all 54 branches, and my run of the D2.7 grammar at `6478b8b5` gives 72 cells for that population. The zero count agrees at 25, because non-branching entries have no zero cells. The Phase-6 comparison the plan requires ("reproduce these figures at `<base>` or explain the difference") will mismatch on scope alone. State the population, or publish both numbers.
  class: measurement
  quote: docs/02-design/features/multi-host-runtime.design.md › `61 branch × declared-skill cells, of which 25 are zero`
- **Implementation Order step 1 (commit `calibrate.sh`, `seed.json` and `seed_coverage.py` before the design audit) has not happened.** `docs/03-analysis/probes/multi-host-runtime/` does not exist at b327e8bf, so this audit runs against scratch-derived DP1/DP2 readings rather than the committed instruments the plan asked the design to cite.
  class: measurement
  quote: docs/02-design/features/multi-host-runtime.design.md › `commit `calibrate.sh`, `seed.json` and`
- **Several spec divergences sit outside the AC grammar, and the design delegates them to an "author's report" that this audit cannot see:**
  - FR-8's table writes `host=<value>`, while D4 prints `json.dumps(host_value)`;
  - FR-8's order against `bad_window` (plan-owed item 3);
  - FR-9's unknown-value rule, which the design and AC-9.4's appended sentence both extend to "declared or unknown";
  - spec F11 and the V-11.1 grok clause (supersede item 1).

  None of these has landed in spec v1.2. List them in the design, or in a committed owed-wording section, so that the spec revision can be checked against a named set.
  class: measurement
  quote: docs/02-design/features/multi-host-runtime.design.md › `wording is listed in the author's report, not here.`
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `` `CTXBUDGET: UNKNOWN reason=unknown_host host=<value>` ``

## Nit
- D1 says `seed.json` is described in "(D11)". D11 is the `SKILL.md` edits, and the sidecar is D8.
- D12 pins `fail-open` in the grok `## The TDD gate` section, but D9.2's prescribed reason-(iii) wording is "fails open". Copying D9.2 verbatim therefore fails the D12 test.
- D8 defines no `UNREADABLE` stdout token for `smoke_assert.py`. When it crashes, `r` is empty, and `stop "$r"` halts with an empty reason.
- No fixture pins the order of the unknown-host check against `--window 0`. Fixture (d) covers declared hosts only.
- The agy `task-tools` gist in the D9.3 matrix omits `.omc/notepad.md`, which D12 pins for that row.
- The codex `send-message` source cell "[DP11: no such string checked]" cites a check that DP11 did not run.
