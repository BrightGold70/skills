DESIGN-AUTHOR: DONE version=v1.2 path=docs/02-design/features/agy-coder-fallback.design.md lines=1325 sha256=499e771974d8b98e941c637cb7eed364f015baae6d74554728f9967c6f14ddc1

# design v1.2 report (agy-coder-fallback)

Start state: sha 9f2d8ace… and newest VH line v1.1 both matched. Before each batch of writes I checked `git diff --stat` (it showed only my own edits) and the newest VH line (still v1.1 until my bump). VH bumped with h_mad_version_history.py: `VERSION-HISTORY: OK … version=v1.2`. Precheck --phase design: `PRECHECK: PASS issues=0`. All advisories are kept on purpose: every PATH advisory names a new file or fixture path, and every COUNT advisory is phrasing, not a count ("FR-5 and FR-7 Tasks", "8 files" in VH/owed text). Mid-task I took in the coordinator's spec v1.8 message and reverted a draft FR-1 field (see E2).

## Per finding
- **E1.** Step 5 (`workspacePaths`) and class (c)'s missing/non-str `CommandLine` now fire only under S = {active, unknown}. I closed the class with a 16-row "Every deny" table (deny, when, kind). I counted the rows with an awk over the table: 16. Unconditional rows: malformed payload, unresolvable root, exception/finally. T7 (unreadable chain, judge) runs whatever the status is, per M:G5 and spec v1.8 "activity reading". I also defined "malformed payload" exactly; a non-dict `args` is read as `{}`, as Codex `_targets` does.
- **E5.** Class (b) targets are the recognised values that are a non-empty str. Anything else counts as no path key, and "" is never canonicalised (spec v1.8 Target keys). The truthy non-str arm is listed as a deliberate difference, because Codex stringifies it.
- **E6.** Closed kind set: see "Kinds" below. Corrected the false claim "unknown denies judge-error, as the Codex gate does". The Codex reason has no kind.
- **E3.** The T4 row's fixture is now `artifactDirectoryPath: 5` under inactive. The rule allows; the mutant (`adp is not None`) reaches Path(5), raises TypeError and denies judge-error. The "" arm is declared an equivalent mutant: the step-3 chdir makes Path("") the root, and T3 has already routed away every in-root target. That arm is listed as an unpinned residual.
- **E4.** Authors = the accepted 5e GREEN dispatch plus accepted fix dispatches. A 5d RED dispatch never counts.
- **E2.** The complete set is kept in the procedure (the orchestrator's list of accepted dispatches) and is never rebuilt from entries. v1.1's read-back is withdrawn. If the list is lost, no entry is written (spec v1.8 rule), and the residual is stated. **OPEN-DECISION OD-E2:** spec AC-7.3's "multi-author, recovered" fixture expects an agy 6a-prime to be recorded `implementer=agy`/false after the context is discarded. That cannot pass without a durable author record, because the assembler's prompt, out and log files are under /tmp and the slug carries no agent. Options: (a) an FR-1 record field of `{module, agent}` per accepted dispatch; (b) amend the fixture to "no entry". I wrote neither into the design; per the coordinator's message, the FR-1 field draft was reverted.
- **S5.** Wording now matches spec v1.8: when the reviewer is none of the authors, `implementer` = the author of the latest accepted implementation dispatch.
- **E7.** Re-anchor `assemble_tdd_agent.json` `w10a-grok-by-default`: new find `ap.add_argument("--agent", choices=("codex", "grok", "agy"), default="codex")`, replace with `default="grok"`, same test. Three things are kept by stated line forms rather than re-anchored:
  - `t1-timeout-judged-by-value`: the timeout line keeps `args.timeout is not None` exactly once.
  - `wr3-assembler-drops-agent`: no second `        agent=args.agent,` line.
  - The two `heartbeat_beat.json` rows: `merge_fields.apply` keeps its statements byte for byte, and the appends run after them.

  Rule: `--check-anchors` runs per Task, and any row an edit breaks is re-anchored in that Task.
- **E8.** `property_valid` calls `_semantic_ok({"implementer_switch": value})`, so None and other non-dicts go to the schema only. Added a mutation row.
- Nit: the stale "plan-author is revising… uncommitted plan" note is replaced (plan v1.6 has landed).

## Kinds (E6), verbatim for the spec to mirror
`judge-error`, `tool-not-admitted`, `target-outside-root` (T4), `allowance-file-write` (T5), `shell-not-admitted` (class (c) policy refusal), plus at T7 only the judge's `verdict.kind` passed through. That kind is a member of `h_mad_tdd_judge.py` KINDS, which holds 12 names at cff71b49. `_shell_allowance` returning a str (unreadable or unparsable allowance file) is `judge-error`, and so are class (c) and (d) under unknown.

## Premises verified (command, at cff71b49; h-mad unchanged since 200ffd52 by `git diff --stat 200ffd52 cff71b49 -- h-mad | wc -l` = 0)
- Codex gate deny sites and kinds: `grep -n '_deny(' h-mad/hooks/h-mad-codex-tdd-gate.py`, plus reading `_main_guarded`. 13 call sites; 6 kindless (lines for state unreadable, allowance, shell policy, no target, outside, allowance write). This agrees with spec v1.8.
- Codex `_targets` `str(args.get("file_path") or …)` and `[path] if path else []`: sed of `_targets`.
- KINDS: the 12 names, read with sed on h_mad_tdd_judge.py.
- `_shell_allowance` returns a str on unreadable/parse error, and `_path_within` uses `Path.cwd()`: sed.
- `Path(5)`, `Path([1])`, `Path({})`, `Path(True)` raise TypeError: scratch `python3 -c`, nothing written to disk.
- Assembler `--agent` line, the timeout line (the only `args.timeout is not None`), `--phase` choices red/green, prompt/out/log under /tmp, slug = feature, module, phase: grep -n on h_mad_assemble_tdd.py.
- `merge_fields.apply` body and its heartbeat `if`; `beat` has the other two heartbeat anchors: sed/grep on h_mad_state_write.py.
- `For GREEN phase (5e):` in codex-implementer-prompt.md: grep. Test `test_agent_grok_explicit_timeout_wins` exists: grep.
- Mutation-spec sweep: a python pass over all 160 specs. For rows whose `file` the design edits, it printed each find and its enclosing heading. SKILL.md anchors are on the 5f bullet and inside Phase 7 item 7, outside the edited spans (grep -n -F). There are no rows on state_validate, the schema, or codex-implementer-prompt.md.
- Harness exactly-once semantics: grep `source.count(find)` and `--check-anchors` in h_mad_mutation_harness.py.
- Value sweeps on the design: grep for `accepted at 5d|successful dispatch|latest successful|as the Codex gate does for a shell|workspacePaths|read back|falsy` and for `four propert` (the Components "four properties" is correct again after the revert). Every `kind=` token in the document is in the set or is judge-timeout in the FR-6 Codex-test context: `grep -o 'kind=[a-z-]*' | sort | uniq -c`.

## Tree or brief contradictions
- Spec AC-7.3 multi-author vs. spec FR-7 "no new field": these cannot both be met. Filed as OD-E2.
- The agy report's claim that "" canonicalises to root with names=() was not probed by me. The design attributes it to the audit and fixes the class by rule instead.

## Owed by others
- **Spec:** mirror the kind list above if desired, and resolve OD-E2 (field, or amend the fixture).
- **Impl-plan:**
  - OD-E2 and AC-7.3's code surface (attribution is prose).
  - E7 re-anchors in the FR-5 Task; heartbeat row checks in the FR-7 Task.
  - The new mutation rows: step-5 S, class (c) S, the target test, the three design kinds, the dict guard, T4 non-str.
  - Open, not added: "." as a TargetFile (a directory target) was not analysed.
- **Plan:** nothing contradicts v1.6. Plan stage 7 carries only the first of AC-7.3's four fixtures.
