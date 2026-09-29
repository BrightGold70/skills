## Summary
This is a gating delta review of the `multi-host-runtime` impl-plan, v1.1 (`249d9479`) to v1.2 (`f61e0d34`), together with the design v1.3 erratum (`d235db3f..212aab9d`). It judges the remediation only.

**What I checked.** I checked every v1.2 Version-History disposition against the document and the tree, and each one claimed "fixed" is present:
- Deviation 7 is resolved against design Implementation Order step 1, and the Task 0 AC is joined.
- Task 1 now keeps the full suite output, halts are no longer counted as met, and item 9 lists the four record kinds.
- Task 2 item 22 kills E1.
- Task 4 passes `env=hermetic_env(X="1")`.
- Task 14 item 7 exists, with its node.
- Task 16 expands `~`.
- Task 17 R14(a) is in the v1.3 form.
- Task 18 passes `--feature`.

**What I executed.**
- The R14(a) shape regex on the codex line returned `True`.
- The §D10 `shlex` configuration, run with both `commenters` values on both forms, reproduced the plan's token lists exactly.
- `recognition_sites` on the G4 and G5 mutants returned `{'_fence_scan'}` and `{'<module>'}`.
- `find_heading` found all four Task 14 headings, and the item-7 locator control returned 1 line.
- Every R-row anchor count held (1 link and 2 path occurrences per file × host).
- The Task 1 `FAILED`/`ERROR` parse, run on a scratch pytest run, printed 2 lines for "1 failed, 1 error".
- The wire-pin gate printed `WIREPIN: PASS tasks=19 wiring=3`.

**Recounts.** The recounts hold:
- Task 2: 125 items, 95 pass and 30 fail after GREEN.
- Task 14: 24 items, RED 18/6.
- Rows: 73 + 24 + 14 + 6 = 117 rows, of which 20 are guard rows.

**Findings.** There is no blocking defect. There are five should-fix items and four nits:
- One residual justification is false.
- One halt-timing contradiction was introduced by the new Task 1 AC.
- One guard kill depends on a scan grammar the plan never pins.
- The guard class is not closed.
- The W2 residual has the same open/decided shape that v1.2 just repaired for Deviation 7.

**Caveats.** I share a model family with the orchestrator and have never been scored against a labelled corpus, so a real codex round on this tree is still owed. Running the wire-pin gate with `--feature` upserts rows into the tracked file `.h-mad/wires.jsonl`. That file was already modified at dispatch with the same 4 `multi-host-runtime` lines, and after my run `git diff` still shows exactly those 4 lines, with no duplicates.

Evidence: 19 files opened, 34 greps run.

## Must-fix
None

## Should-fix
- **should** — Deviation 9's residual says Task 6's three `…-unreadable-file` ids "cannot be killed by any single-point mutant". That is false for the code the plan itself lands, so the stated reason for leaving three green-at-RED ids unrowed does not hold.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `cannot be killed by any single-point mutant, because two independent paths both return`
  - Task 6 lands `CANNOT_JUDGE_WITHOUT_SESSION = "cannot_judge"`, and `decide()` returns `host_verdict` whenever it is not `None`, as its first statement. Take the one-point mutant `CANNOT_JUDGE_WITHOUT_SESSION = "start_fresh"`. It makes `decide()` return `start_fresh` for every declared host without a session id, `unreadable-file` included, before the legacy `except (json.JSONDecodeError, OSError): return "cannot_judge"` branch is reached (`h-mad/scripts/h_mad_resume_decision.py:101`–`107`, read). So `[grok-unreadable-file]` fails on its assertion. This is reasoning over the plan's literals: the code does not exist yet, so I did not execute it.
  - What is true is narrower: no mutant that disables one path, and none of V2, WR2 or the committed `resume_decision_cannot_judge.json` row, kills them.
  - Repairs, any one: (a) reword the residual to "no single-path removal kills them" and keep them unrowed as matrix completeness; (b) add one guard row per id (or one row against a single id) that mutates the constant's value, which makes the count 118; (c) cite the existing V2/WR2 rows and drop the "any single-point" claim.
- **should** — The new Task 1 AC says any halt "stops 5c, and no later task starts". Item 4 still lets a `REFUSAL_FORM_AT_BASE` halt wait until Task 10. This is a contradiction that v1.2 introduced, and it decides whether Tasks 2–9 run.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `A mix of forms, or anything else, halts to the operator before Task 10 (design §D9.2)`
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `A halt on any of these is not a met criterion: it stops 5c, and no later task starts until the`
  - Design Implementation Order step 2 places the record-or-halt at 5c ("record the gate's refusal form at `<base>` as `REFUSAL_FORM_AT_BASE` (D9.2), or halt", design line 1494, read). That matches the AC and not item 4.
  - Repairs: change item 4 to "halts to the operator and stops 5c (design Implementation Order step 2)"; or exempt this halt in the AC by name, because only Task 10 consumes the constant, and say so in both places.
- **should** — G2 and G3 are killed only if item 19's "source scan" is textual. The plan never pins its grammar, and each mutant is an attribute reference, not a call. `_LAUNCH = os.system` / `os.popen` survives an AST scan for `Call(os.system)`, which is a natural reading of "calls no `os.system`" in the Task 2 description.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `This is a source scan: no`
  - Task 2's description says "It imports no `subprocess` and calls no `os.system` or `os.popen`". Item 19 says only "source scan", and plan AC-3.5 (`multi-host-runtime.plan.md:146`, `:154`) says only "direct-only".
  - Repairs, any one: (a) pin item 19 as substring containment of the three strings `import subprocess`, `os.system` and `os.popen` over the source text; (b) pin it as an AST walk that flags `Import`/`ImportFrom` of `subprocess` and any `Attribute` `os.system`/`os.popen`, whether called or not; (c) change G2 and G3 to put the call inside a function body (`def _l():⏎    return os.system("true")`), which never runs on import and is caught by either grammar.
  - Class residual under (a): `from subprocess import run` and `__import__("subprocess")` evade the textual form. G6 already uses the second spelling, so state that item 19 is direct-spelling only.
- **should** — Deviation 9 does not close the guard class it defines ("guards that are green before their task's change or pass without a RED of their own"). It names only members that the audit's cited instances reach.
  class: build
  instance of: new tests that pass at their task's RED (or whose only RED is the Task 2 collection error) with no mutation row naming them
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `Items 17, 19, 20 and 21 are guards whose only RED is`
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `Task 6's item 3 (`[grok]`) is V1's named test.`
  - Task 2 item 16, `test_branch_expander_refuses_unsupported_shapes[group-plus|atom-brace|unbalanced]`, is a refusal guard. Its only RED is the same collection error as items 17–21, and no design member or row names it: design lines 466/1648 name the test, and the mutation table has no refusal member (grep `UnsupportedPattern` in the design, 3 lines, none a member). Its permissive stub is `expand_branches` accepting the shape.
  - Task 6 item 3 `[codex]` and `[agy]` pass at RED (the plan: "Item 3: 3 pass (controls)"). Only `[grok]` is V1's named test, and the harness scores the named test alone (`scoring_command = list(target_command) + [mutation["test"]]`, `h-mad/scripts/h_mad_mutation_harness.py:1335`, read).
  - Candidates for the rule to decide, which I have not classified: Task 2 item 3 (`test_clean_baseline_yields_nothing`) and item 6 (`test_absent_adapter_file_reads_as_no_heading`).
  - The rule would be: every new test that is green at its task's RED, or whose RED is only a collection error and which asserts an absence or a refusal, has a named row or a stated reason. Repairs: rows for item 16's three ids (for example, the refusal `raise` → `return [pattern]`) and V1 rows for `[codex]`/`[agy]`, each moving the 117 total; or name them in the residual with a reason.
- **should** — The W2 residual in Deviation 8 is left "open for the orchestrator" with no recorded decision and no halt. Task 14's AC still ticks Axis-B "Skill manifest integrity" as met. This is the same open/decided shape that teammate S4 raised and v1.2 repaired for Deviation 7.
  class: build
  instance of: plan items left open for an orchestrator decision without an executable record or halt
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `an edit the design explicitly leaves open is the orchestrator's call, not the plan's (audit`
  quote: docs/01-plan/features/multi-host-runtime.impl-plan.md › `Axis-B "Skill manifest integrity" (design §D11 items 1–7, Deviation 8): the 14`
  - Design v1.3 Invariant Compliance calls the two W2 surfaces "the exception, open for the orchestrator". The Task 14 AC does not carry that exception, so a checked box asserts compliance that the design says is not yet reached.
  - Both surfaces are live and still carry the old cause, as the design quotes them: `h-mad/SKILL.md` "omitting it opts out", and `handoff/SKILL.md` "the state file exists and could not be READ". h-mad and handoff are unchanged `212aab9d..f61e0d34` (`git diff --stat` empty).
  - Repairs: (a) add to Task 14's AC "except the two W2 surfaces of design §D11 'Residual', open for the orchestrator", plus a Task 14 item that records the orchestrator's decision (sha or dated note) or halts without it; or (b) have the orchestrator decide now and route the result to design §D11 and Task 14 (two edits, two nodes).

## Nit
- Convention 7 still says a spec row's `file` is "`scripts/…` or `tests/…`", but the new `host_runtime_docs.json` rows use `SKILL.md` and `../handoff/SKILL.md`. Task 15 states this explicitly, but the convention now contradicts it. Add "or, for `host_runtime_docs.json`, `SKILL.md` / `../handoff/SKILL.md`".
- G6's "so G6 never starts a real `codex`" holds only while the named test kills. On a survivor, the harness runs the spec's whole `command` with the mutant applied (`_run(command, root)`, `h_mad_mutation_harness.py:1459`, read). Items 1 and 2 then call `check(live_paths(REPO_ROOT))` without the stub `PATH`, so a real `codex` would be launched. Say "never, unless G6 survives", or name the survivor path.
- Task 18's gate command now carries `--feature`, and with it the gate upserts wire rows into the tracked file `.h-mad/wires.jsonl` ("registration: registered=4", executed). Say that the run should leave that file's diff unchanged, because the rows were registered at 5b.
- Design v1.3 §D11's contract preamble still says "Each edit adds text and keeps every existing token", while its own item 2 replaces the `SIBLING_NOT_SYMLINK` remedy cell. The plan notes the conflict and follows item 2. The design sentence itself is still wrong, and fixing it belongs to the design, not to this plan.
