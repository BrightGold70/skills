AUDIT-multi-host-runtime-plan-v1-BEGIN
## Summary
Plan v1.0 (`docs/01-plan/features/multi-host-runtime.plan.md`, HEAD `01121ca`) was checked against the tree, not just against itself. Its premises mostly re-derive: P1 calibration (122/13 and 71/12 occurrences/distinct), all 22 seed hit counts, P3, P5, P6, P7 (23 `def test_` lines), P8 (316 names; `debugger` only), P9, P13, P14 (50 AC / 5 V distinct ids), the 3893/140 collection counts, and P11/P12. Against that, four build-class defects would ship a smoke or a floor that measures nothing: (1) the live smoke's hosts load the MAIN tree, not the worktree; (2) the worktree has no `docs/.bkit-memory.json` (it is gitignored), so the V-11.3 sha check passes on a missing file; (3) the FR-10 hermeticity premise uses the wrong axis, because the fixture skill names `h-mad`/`handoff` are exactly the names the operator links before the pre-merge suite runs; (4) the per-alternative seed-coverage criterion already fails at HEAD on several alternative × skill cells.

Axis C (plan audit, FR granularity):

| FR | classification | note |
|---|---|---|
| FR-1 | implemented-as-written | registry deliverable + AC-1.1 fixtures in `test_host_construct_parity.py` |
| FR-2 | implemented-as-written | tables in six adapters |
| FR-3 | implemented-as-written | `host_parity.py` + message format (defects below) |
| FR-4 | implemented-as-written | axes/suffixes as parameters, per-branch controls |
| FR-5 | implemented-as-written | grok adapters, halt token |
| FR-6 | implemented-as-written | tables + gap table in Phase-6 doc |
| FR-7 | implemented-as-written | `## Host runtime` edits |
| FR-8 | implemented-as-written | W1 |
| FR-9 | implemented-as-written | W2 (placement ambiguity below) |
| FR-10 | implemented-as-written | W3 (hermeticity defect below) |
| FR-11 | implemented-as-written in form | smoke block is defective as a measurement (Must-fix 1–2) |
| FR-12 | implemented-as-written | node-id floor, append-only numstat, broader than AC-12.1 (adds `handoff/scripts`) |

No FR is `restated` or `absent`.

This is a GATING pass, and my authority is limited: I have never been scored against a labelled corpus, and I share a model family with the author. I did not call `advisor()`.
Evidence: 31 files opened, 52 greps run.

## Must-fix
- The live smoke cannot exercise this feature, because every host loads h-mad from a link into the MAIN checkout, and the smoke runs before merge. The plan says the new links "point at the main checkout, never at the worktree", and it runs the smoke "after all of that is GREEN and before merge". Resolving the *wrapper* inside the worktree only chooses which `hmad-dispatch` launches the host. The host then resolves the skill from its own skill root: grok lists h-mad as `user [claude]` (spec F5), which is `~/.claude/skills/h-mad -> /Users/kimhawk/orca/skills/h-mad` (verified with `ls -ld`), and the adapters set `HMAD_SKILL_ROOT` "from the loaded skill path" (`h-mad/references/codex-runtime.md:8-10`, `agy-runtime.md:14-16`). The project tier contributes nothing. `.agents/` does not exist, and `.claude/` is gitignored (`.gitignore:14`), so a fresh worktree has neither. Before merge, main has no `grok-runtime.md`, no FR-7 routing and no `HMAD_HOST` handling in any script. So V-11.1 ("read `references/<host>-runtime.md`") cannot hold for grok, and for codex/agy it measures the pre-feature adapter. The P11 risk row ("the smoke measures the pre-feature skill and reads as a pass") is mitigated only for the wrapper, not for the skill. Repairs, none of them checked live: (a) run the smoke after merge, as a post-merge gate that blocks the close-out rather than the merge; (b) point the host at the worktree for the smoke only, via a temporary project-tier link or the host's skill-dir config, and assert the loaded root with `readlink -f` in the transcript; (c) state that the smoke validates only the main tree, and restate FR-11/V-11.1 accordingly in the spec.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `The links point at the main checkout, never at the worktree, so no host sees unmerged work.`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `The live smoke (FR-11) runs after all of that is GREEN and before merge.`
- The smoke's V-11.3 state check is vacuous, and V-11.2 has no state to read. `docs/.bkit-memory.json` is gitignored and untracked (`git check-ignore -v` → `.gitignore:21`; `git ls-files` → empty), so a `git worktree` does not contain it, and `M="$W/docs/.bkit-memory.json"` names a missing file. `shasum` on a missing file emits nothing on stdout, and the pipeline's status is awk's 0, so `B_SHA` is empty and the post-run comparison is `"" = ""`. I executed exactly that shape against a nonexistent path and it printed a pass. With `--cd "$W"`, the status verb also reads the worktree's cwd-relative state file (SKILL.md bootstrap item 5, `h-mad/SKILL.md:59`), which is absent, so it cannot name `$F`'s `last_completed_phase` from the store the operator means. Repairs, any of which works: add `test -f "$M" || { echo "HALT no state file"; exit 1; }` and `test -n "$B_SHA" || exit 1` before the run; decide explicitly which state file the smoke reads (the main checkout's) and pass `--cd` accordingly, noting that this interacts with Must-fix 1; or copy the state file into the worktree and say that V-11.2 then compares against a copy. This is an instance of a class: every "unchanged" check in the block that hashes or diffs a possibly-absent artefact. `git status --short` is safe only because it always prints; the sha line is not.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `M="$W/docs/.bkit-memory.json"`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `test "$(shasum -a 256 "$M" | awk '{print $1}')" = "$B_SHA" || { echo "FAIL V-11.3 state moved"; exit 1; }`
- The FR-10 hermeticity premise was measured on the wrong axis, and the plan's own sequencing breaks it. `check_siblings(repo, skills_dir)` iterates the fixture repo's skill names (`h_mad_install_check.py:120-122`, `repo.glob("*/SKILL.md")`), not the checkout directory's name. `TestSiblingSkills._repo` builds skills named `h-mad` and `handoff` (`test_h_mad_install_check.py:281`). The existing tests pass no new options, so after this feature they read the real `~/.agents/skills` and `~/.gemini/config/skills`. The Convention Prerequisites have the operator create `~/.agents/skills/{h-mad,handoff}` and `~/.gemini/config/skills/{h-mad,handoff}` → main checkout before the smokes, and "Both coupled suites in full" then run before merge. From that point `test_the_cli_reports_a_sibling_copy_as_a_verdict_not_an_error` (line 337, CLI) and `test_the_sibling_root_is_derived_one_level_up_from_the_link` (line 359, `check()` directly, if W3's new roots are read inside `check`) see extra `SIBLING_WRONG_CHECKOUT` lines: real link target `/Users/kimhawk/orca/skills/h-mad` ≠ fixture `…/checkout/h-mad`. Both still pass, because they use `in`/`any`, but their stdout and `issues=N` change. That breaks AC-10.2's same-stdout clause and AC-12.2's byte-identity "on the existing tests' fixtures". The plan's Risks row ("fixture checkout name `checkout` collides with nothing") was measured when all four links were absent (P8), so it never tested the state the plan itself creates. Repairs, none checked: (a) add env overrides for the two new defaults (`HMAD_AGENTS_SKILLS_DIR`, `HMAD_AGY_SKILLS_DIR`) and set them to `tmp_path` in a new autouse fixture in `h-mad/tests/conftest.py` (a new fixture keeps the pre-existing test files append-only); (b) read the new roots only in `main()`, never in `check()`, and still solve the CLI test; (c) take the AC-10.2/AC-12.2 byte-identity readings before the operator creates the links, and restate the residual in the spec as a condition on link state. Whichever is chosen, the risk row's measurement must be redone with the links present.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `Measured before the change: the fixture checkout name `checkout` collides with nothing in either real root`
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `fixture checkouts are named like `checkout`, which collides with nothing in either real`
- The per-alternative seed-coverage Success Criterion is unsatisfiable at HEAD as written, and the plan's list of alternation entries is not the closed class. I ran `re.findall` per branch on `git show HEAD:<skill>/SKILL.md` (unit: occurrences). These cells are 0 in a declared skill while the entry and branch stay live elsewhere, so "records the retirement" does not fit them:
  - `session-reset-command` `` `/compact`` in handoff: 0;
  - `skill-slash-invocation` `` `/h-mad`` in handoff: 0;
  - `claude-settings` `settings.local.json` in both skills: 0 each, an optional group rather than a `|`;
  - H's `\$\{HOME\}` branch: 0 in h-mad and 0 in handoff (`grep -oF '${HOME}/.claude'`).

  H's branch is carried by all nine H-based entries (`claude-skills-dir`, `-agents-dir`, `-hooks-dir`, `-settings`, `-handoffs-dir`, `-projects-store`, `-homunculus`, `-home-bare`, and `claude-home-bare`'s own `(?!/)` form). The plan's seven-entry list omits six of them. Rule over the set: every alternative produced by expanding `H`, every top-level or grouped `|`, and every optional `(?:…)?` group, each counted per declared skill. Residual: `\b`/lookahead variants are not branches. Prescription: define the criterion either as ≥ 1 hit in at least one declared skill per alternative (the union), or per skill with each zero cell recorded and justified in the Phase-6 document. The probe must print the zero cells, not just a pass/fail.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `(`subagent-call`, `hook-event`, `task-tools`, `claude-settings`, `claude-projects-store`,`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `hit in each declared skill at `<base>`, or records the retirement.`

## Should-fix
- The kinds that are themselves disjunctions get one fixture each, so a healthy disjunct masks a broken one. This violates the plan's own rule, which reads "Controls over alternations get one fixture per branch, run with that branch alone." FR-3 defines these kinds as ORs:
  - `REGISTRY_UNREADABLE`: missing file, invalid JSON, missing key, extra key, malformed id, empty description, empty skills, out-of-set skills;
  - `TABLE_MISSING`: no heading, no table, heading twice;
  - `TABLE_MALFORMED`: header differs, wrong cell count;
  - `CELL_EMPTY`: no alnum, `tbd`, `todo`, across `mapping` and `source`.

  The Deliverables inventory is "14 kind fixtures", and the Success Criteria mutate "each FR-3 kind's detection" per kind. AC-1.1's seven registry fixtures are not counted, and FR-3's "extra key" and "empty description" rules have no fixture anywhere. Prescription: one fixture per disjunct, and one mutation per disjunct.
  instance of: controls over alternations
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `14 kind fixtures, AC-3.2's mention-only fixture`
- Exact-kind-set fixtures need precedence and suppression rules, and the plan does not state them. Each fixture must assert its produced kind set equals `{kind}`, but several kinds cascade by construction:
  - `TABLE_MISSING` would also yield `ROW_MISSING` for every declared construct;
  - `BAD_PATTERN` leaves hits uncomputable, which yields `STALE_ENTRY`, and yields `UNREGISTERED` if that entry was the one covering a live token;
  - `REGISTRY_UNREADABLE` makes every downstream check meaningless;
  - `DUPLICATE_ID` makes row-to-entry mapping ambiguous.

  The checker's API has to encode these rules, and the fixtures depend on them. Prescription: state the suppression order, e.g. registry kinds short-circuit everything; `BAD_PATTERN` entries are skipped for hit-based kinds and coverage; table kinds suppress row kinds for that adapter.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `Each fixture test asserts the exact set of `<KIND>` values it produced`
- The message format has no rule for kinds that carry no construct id. `id=-` is reserved for `UNREGISTERED` and parse failures, but `TABLE_MISSING`, `TABLE_MALFORMED` (bad header), and `REGISTRY_UNREADABLE` for a missing or malformed `id` also have no valid construct id. `STALE_ENTRY`/`UNDECLARED_SKILL` would need `file=` to name the `SKILL.md`, not an adapter. Tests assert these lines, so the format is a contract.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `exists (`UNREGISTERED`, and `REGISTRY_UNREADABLE` when the file does not parse).`
- The W1 mutation named in the Success Criteria has no planned killing fixture. With the host check moved after the transcript lookup, AC-8.1's fixture still prints `host_unsupported`, because it passes a valid `--transcript`. Only a fixture with `HMAD_HOST=grok` and no resolvable transcript separates original (`host_unsupported`) from mutant (`no_transcript`). The same applies to `--window 0`: today `bad_window` precedes the lookup (`h_mad_context_budget.py:157-160`), so precedence between `bad_window` and `host_unsupported` is also unspecified. Prescription: add the no-transcript fixture per host, and state the `bad_window` ordering.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `the `HMAD_HOST` check moved after the transcript lookup (W1)`
- The placement of the host check in `decide()` is ambiguous, and it changes behaviour. The plan says the check is read "first in `h_mad_resume_decision.decide`" and also "before `_owned_elsewhere`". `decide()` returns `start_fresh` on a missing state file or feature before it reaches `_owned_elsewhere` (`h_mad_resume_decision.py:97-111`), so the two placements differ for those inputs. AC-9.1's fixtures both have the feature present, so neither placement is pinned. Separately, the value-set agreement test names an "unknown" class, but neither spec nor plan says what `decide()` prints for `HMAD_HOST=zzz` without `--session-id`: `cannot_judge` or legacy. Case and whitespace (`Grok`, ` grok`) are also unspecified. Prescription: fix the placement, add missing-file and missing-feature fixtures, and define the unknown-value and normalisation rules for both readers.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `first in `h_mad_resume_decision.decide`,`
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `asserts the same classification (Claude path, non-Claude,`
- On grok, the global advisor-warn hook would still report a Claude transcript's reading. `h-mad-advisor-warn.sh` is registered globally in `~/.claude/settings.json:232` as PostToolUse with matcher `"*"`. The spec says global hooks run on grok untrusted-free (F7, FR-5). The hook passes `--transcript` only from the payload's snake_case `transcript_path` (`h-mad-advisor-warn.sh:68,98-99`), and grok's hook docs document no transcript field (`grep -i transcript ~/.grok/docs/user-guide/10-hooks.md`). The call then falls to the slug walk, and `HMAD_HOST`, being inline per script call, is not in the hook's environment. The hook would inject a `CTXBUDGET: DENY` computed from the newest Claude transcript for the cwd, via `additionalContext`, which grok honours for PostToolUse (10-hooks.md §"PostToolUse Output"). That contradicts the plan's Goal for FR-8, and neither document mentions it. **Unverified**: whether grok compiles `"*"` as a matcher regex and actually fires this hook. Prescription: a grok-adapter note plus a live check in the smoke, or have the hook stand down when the payload carries grok's camelCase fields.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `The context budget never reports a Claude transcript's reading on a declared non-Claude host`
  quote: docs/01-plan/features/multi-host-runtime.spec.md › `The TDD, advisor-warn and memory-guard hooks are wired in the global`
- The section locators may duplicate an existing helper, and the import scan's scope is undefined. `h-mad/tests/docsections.py` already exists as the single fence-aware section bounder; 4 test files import it. It exists because a fence-blind `^## ` bound cut `## Phase 5` short by 24,270 chars (its docstring). The plan's doc tests and the parity table locator ("first pipe table after that heading, before the next `## `") do not say whether they reuse it. Reusing it from `host_parity.py` transitively imports `subprocess` (`docsections.py` → `h_mad_doc_block_exec.py:13`). AC-3.5's "imports no subprocess launcher" then depends on whether the import scan is direct-only or transitive, and the plan does not say.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `It imports no subprocess launcher (AC-3.5's first arm).`
- The risk row states a sibling-branch outcome as unconditional. codex-tdd-gate-defects' AC-6.5 is only the `E1_DOES_NOT_BLOCK` branch. AC-6.6 (`E1_BLOCKS`) keeps `exit 1` with rc = 1 tests, and AC-6.7 (`INCONCLUSIVE`) ships neither (`codex-tdd-gate-defects.spec.md:365-380`). So "After the rebase, AC-5.2 reason (i) … is false" holds on one branch of three, and P5's "switches every refusal to exit 2 or … JSON deny" has the same gap. The re-measure at `<base>` mitigates this, but the adapter-text decision (Next Steps item 1) should be framed per branch.
  class: build
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `After the rebase, AC-5.2 reason (i) ("`exit 1`, which grok treats as fail-open") is false`
- The sequencing-cycle risk cites only the brainstorm, but the sibling spec makes it hard. `codex-tdd-gate-defects.spec.md:406-408`, at the current tree, says V-1 "needs `~/.agents/skills/h-mad` … owned by feature `multi-host-runtime`, and V-1 cannot run until it lands". The plan's resolution, that the operator links before either feature merges, answers "the link exists", not "the feature lands". The plan should cite the spec line and state which wording the sibling spec must adopt.
  class: measurement
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `That feature's brainstorm says its live check`
- P4 over-reads its own census. `grep -n 'unknown agent' h-mad/scripts/hmad-dispatch.sh` gives 8 matching lines, but only 5 carry `(codex|agy)` / `(expected codex|agy)`: 873, 985, 1060, 2761, 3604. Of the other three, 301 has no agent list, 871 is a comment, and 3275 reads `(agy|codex)`. The premise's conclusion (exec rejects grok, line 2761) holds.
  class: measurement
  quote: docs/01-plan/features/multi-host-runtime.plan.md › `the spec records each as `(codex|agy)``
- Two spec ACs have no owning test in the plan, yet the Success Criteria say all non-artifact ACs "pass automated tests". A script over spec ids vs plan text shows 8 ids never named in the plan. Six are covered implicitly: AC-2.1/2.2/6.2 by the live-tree gate, AC-8.2 and AC-9.2 by the host-declaration and existing tests, and AC-12.1 by the full suite. The two with no evident owner are AC-1.2 (the committed registry holds ≥ the 22 seed ids) and AC-10.2's second clause ("the run with the agents dir absent entirely yields the same stdout as today"). Name the test for each.
  class: build

## Nit
- The mutation-harness halt rule names only `SURVIVED` / `REFUSED`. The harness also emits `BASELINE_NOT_GREEN`, `PRECHECK_FAILED`, `RESTORE_FAILED`, `TREE_MOVED`, `UNREADABLE` and `BUSY` (`grep -o 'MUTATION: [A-Z_]*'`). "Anything but `ALL_CAUGHT` halts" is the complete rule.
- "14 kind fixtures, AC-3.2's mention-only fixture" double-counts against the spec's AC-3.3 ("Each remaining kind … Fourteen kinds means fourteen fixtures"). State whether the `ROW_MISSING` fixture is the AC-3.2 fixture or an additional one.
- The AC-6.1 gap table must be measured "before the tables are written". Strand (3) does not sequence it. It is reconstructable from `git show <pre-change sha>:`, but say so.
- A4 (`(~|\$HOME|\$\{HOME\})/\.claude\b`) is itself a three-branch alternation, and the spec's single A4 fixture `~/.claude/foo` exercises the `~` branch only. The `$HOME` and `${HOME}` branches have no control, and `${HOME}` has 0 corpus occurrences in either `SKILL.md`.
AUDIT-multi-host-runtime-plan-v1-END
