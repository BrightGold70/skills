# Triage — 17 taken-over carry-forward briefs

Repo `/Users/kimhawk/orca/skills`, branch `feature/pin-agents-tail-banner`, 2026-09-02.
Source list: `handoff_paths.py carry-forward-sources --branch feature-pin-agents-tail-banner` (18 paths; the `feature-pin-agents-tail-banner` entry skipped as already handled).

Read-only pass. No repo file was created, edited, or committed.

**Method note on hashes.** `git log --all --oneline -1 <hash>` unions all refs with the revision, so `-1` returns the newest commit across that union rather than the named one — every hash appears to resolve to the same tip. This is plain git semantics, not a wrapper intercepting the call; bare `git` is correct here. Every hash below was resolved with `git log --oneline --no-walk <hash>`, which is unaffected. Two hashes cited in the briefs (`58a81732`, `024bec25`) are HemaSuite commits and do not resolve in this repo; they are 8-char and are flagged where cited.

## Summary table

| file | verdict | #open | #still-open |
|---|---|---|---|
| 2026-08-03-main__exec-verdict-laundering.md | FULLY-ABSORBED | 7 | 0 |
| 2026-08-03-main__five-hmad-items-handover.md | OWES | 6 | 2 |
| 2026-08-10-main__precondition-gate-blindness.md | OWES | 6 | 1 |
| 2026-08-18-main__h-mad-phase7-preconditions-cwd-path.md | FULLY-ABSORBED | 6 | 0 |
| 2026-08-19-main__hmad-dispatch-exec-agy-flag-order.md | FULLY-ABSORBED | 6 | 0 |
| 2026-08-20-main__handoff-read-todolist-fallback.md | FULLY-ABSORBED | 7 | 0 |
| 2026-08-20-main__skill-candidate-backlog-reconcile.md | OWES | 9 | 3 |
| 2026-08-24-main__audit-dispatch-contract-integrity.md | FULLY-ABSORBED | 8 | 0 |
| 2026-08-27-main__mutation-anchor-pre-push-hook.md | FULLY-ABSORBED | 7 | 0 |
| 2026-08-28-main__stale-install-and-wire-registry-handover.md | FULLY-ABSORBED | 4 | 0 |
| 2026-08-29-main__hmad-tooling-defects.md | FULLY-ABSORBED | 6 | 0 |
| 2026-08-29-main__skill-candidates-hmad-domain-rows.md | OWES | 5 | 2 |
| 2026-08-30-main__handoff-linked-worktree-commit.md | FULLY-ABSORBED | 8 | 0 |
| 2026-08-31-BrightGold70-j1-residual-probes__split-and-surface-probes.md | FULLY-ABSORBED | 5 | 0 |
| 2026-08-31-main__j1-launch-pane-pin-durability.md | FULLY-ABSORBED | 5 | 0 |
| 2026-09-01-main__handoff-restore-chain-and-audit-version-discovery.md | OWES | 9 | 1 |
| 2026-09-02-main__audit-report-docs-copy.md | HANDED-ELSEWHERE | 7 | 0 |

**Totals:** 17 briefs · 111 open items · 9 STILL-OPEN owed to this lane · **11 FULLY-ABSORBED, 5 OWE, 1 HANDED-ELSEWHERE** (11+5+1 = 17, verified against the table above rather than carried).

Of the 9 STILL-OPEN, **4 are decisions an operator can settle in minutes** (brief 2's `#68` and `#86`, brief 3's issue filing, brief 7's summary tables) and **5 are work sessions**.

The 17th brief carries 5 open items that are **not this lane's to work** — the `BrightGold70/audit-report-docs-copy` lane is committing right now (its tip moved `5b6c7b6` → `b551ca0` inside a minute). Its items are reported below and excluded from the still-open count.

---

## 1. `2026-08-03-main__exec-verdict-laundering.md`

- **handover_from:** HemaSuite · feature/196-grounding-shadow-measurement · session d185c497-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — fixed in `c5f6084`

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Fix Defect 1: exec log-recovery greps prompt echo, launders a verdict into `--out` | CLOSED | `c5f6084` "exec stops laundering its own prompt into a verdict"; `_verdict_after_boundary` at `h-mad/scripts/hmad-dispatch.sh:2677` |
| 2 | Fix Defect 2: `tree delta` counts whole repo, needs `-- .` pathspec | CLOSED | `hmad-dispatch.sh:2696` `git -C "$cd_dir" status --porcelain -- .`, J23 comment at `:2689` |
| 3 | Correct SKILL text claiming `exec` sidesteps prompt-echo | CLOSED | `h-mad/SKILL.md:781` "Prompt echo is NOT one of the things `exec` sidesteps — it is handled" |
| 4 | Mutation-verify both guards; run both suites | CLOSED | `h-mad/tests/test_hmad_dispatch_exec.py:756` records a `tail -1`→`head -1` mutant that survived and the test written to catch it |
| 5 | (OI) Both defects unstarted, ownership here | CLOSED | same as 1–2 |
| 6 | (OI) No claim to release — verified zero live `owner_session_id` | CLOSED | `docs/.bkit-memory.json`: 31 features, only `pin-agents-tail-banner` owned (this session) |
| 7 | (OI) Not reproduced on a healthy agent; one probe worth doing | CLOSED | `test_hmad_dispatch_exec.py:740` exercises a truncated-echo failure with no auth error and asserts no verdict is emitted |

**verdict:** FULLY-ABSORBED

---

## 2. `2026-08-03-main__five-hmad-items-handover.md`

- **handover_from:** HemaSuite · feature/196-grounding-shadow-measurement · session d185c497-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — waves 1–5, e.g. `5f9ec7c`, `787aecf`

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | `#67` TDD gate resolves state file at repo root, no-ops in sub-project layouts | CLOSED | `dde1c7a` "TDD gate finds its state file in sub-project layouts (#67) (#28)"; `_resolve_state_file` at `h-mad/hooks/h-mad-tdd-gate.sh:80` |
| 2 | `#66` item 2: `phase_counter_behind` false-fires on a live mid-Phase-5 record | CLOSED | `5c8428d` "phase_counter_behind no longer fires mid-phase (#66 item 2) (#29)"; `mid_phase` suppression at `h-mad/scripts/h_mad_state_staleness.py:99-101` |
| 3 | `#68` decide: amend the shipped spec with the size-ceiling finding, or close as covered | **STILL-OPEN** | `grep -c '92,055\|size ceiling\|size_status\|ARG_MAX' docs/01-plan/features/tdd-dispatch-verification-discipline.spec.md` → **0**; `git log --all --grep` and `grep -rn '#68'` over `docs/learnings.md`, `docs/skill-candidates.md`, `docs/skill-monitoring.md` find no decision |
| 4 | `#86` close as a duplicate of `#67`/`#66`/`#68` | **STILL-OPEN** | `grep -rn '#86' docs/` hits only this brief; `#NN` were HemaSuite TodoList numbers, and that list is gone (see brief 15's finding). No closure record anywhere |
| 5 | `#40` re-scope, or close skills `#38` (pane-path guard unreachable from `exec` default) | CLOSED | `docs/skill-monitoring.md:1005` "Adjudication 2026-08-03 — `#40` re-scoped; `#38`'s guard kept, on better evidence than the one proposed" |
| 6 | (OI) No claim to release | CLOSED | state file has no owner for any of these |

**verdict:** OWES — `#68` (spec amendment or documented close), `#86` (close as duplicate).

---

## 3. `2026-08-10-main__precondition-gate-blindness.md`

- **handover_from:** HemaSuite · feature/78-guideline-seeder-config-plumbing · session f0151733-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — merged as `379b881`

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Add `has_gate_sections` guard to the precondition path so the Phase-5 gate stops failing open | CLOSED | `379b881` "Merge feature/214: gate-blindness-hardening"; `h_mad_do_preconditions.py:70` `if not has_gate_sections(path.read_text())` |
| 2 | Decide the verdict token for the unreadable case | CLOSED | `h_mad_do_preconditions.py:70-74` returns `INVALID:{path}`, deliberately distinct from `DIRTY:` per the docstring at `:66-68` |
| 3 | TDD it with a fixture lacking literal headings; mutation-verify the guard | CLOSED | `h-mad/tests/test_h_mad_do_preconditions_gate_blindness.py:120` `test_guard_routes_through_has_gate_sections`, described in-file as mutation-style |
| 4 | Sweep sibling consumers of `classify()` for the same bypass | CLOSED | `grep -rn 'classify(' h-mad/scripts/*.py`: the only audit-gate consumer outside `h_mad_audit_gate.py` is `h_mad_do_preconditions.py:53`, which now routes through the guard; the other `classify` symbols are unrelated (`h_mad_pane_janitor.py:137`, `h_mad_state_validate.py:167`) |
| 5 | (OI) Not filed as a GitHub issue — sanitize absolute paths first | **STILL-OPEN** | `git log --all --grep='gate-blindness'` and `grep -rn 'gate-blindness' docs/` show only the fix and handoffs, no issue reference. Explicitly deferred to the operator by the brief; the fix shipped without it |
| 6 | (OI) No fix attempted at handover time — deliberate | CLOSED | discharged by item 1 |

**verdict:** OWES — the GitHub issue was never filed. This is an operator call the brief deliberately deferred, not code work; the underlying defect is fixed.

---

## 4. `2026-08-18-main__h-mad-phase7-preconditions-cwd-path.md`

- **handover_from:** HemaSuite · main · session 18ecfc0f-…
- **taken_over_by:** skills · main · session 86c6aded-… · 2026-09-01

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Reproduce the two-CWD verdict divergence | CLOSED | superseded by the fix and its regression test (items 2–3) |
| 2 | Resolve the analysis path against the state file's parent, not CWD | CLOSED | `d820a64` "anchor the Phase-7 analysis path to the state file, not the CWD"; `resolve_analysis_path` at `h-mad/scripts/h_mad_phase7_preconditions.py:134`, called at `:189` with `args.state_file` |
| 3 | Regression test: two CWDs, one state file, identical verdict | CLOSED | `h-mad/tests/test_h_mad_phase7_analysis_anchor.py` plus mutation spec `h-mad/tests/mutation-specs/phase7_analysis_anchor.json` |
| 4 | Sweep sibling scripts taking a state-file arg then opening a relative doc path | CLOSED | `d820a64` also touches `resolve_docs_root` (`h-mad/scripts/h_mad_telemetry.py:29`), the one sibling of that shape; `git log --oneline -S'resolve_docs_root'` returns only `d820a64` and `d5a833f` |
| 5 | (OI) The cwd-relative resolution itself — diagnosed, not fixed | CLOSED | same as 2 |
| 6 | (OI) `~/.claude/skills` is a live symlink — context, not a task | CLOSED | brief labels it "context, not a task" |

**verdict:** FULLY-ABSORBED

---

## 5. `2026-08-19-main__hmad-dispatch-exec-agy-flag-order.md`

- **handover_from:** HemaSuite · feature/71-run-report-seam-restoration · session 679a9622-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — CLOSED, no fix needed; premise already false when written

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Fix flag order: booleans before `--print`, or pass prompt via `--prompt` | CLOSED | `h-mad/scripts/hmad-dispatch.sh:2599` builds `args=(--dangerously-skip-permissions)` first; comment at `:2595-2598` states `--print` must come last, adjacent to the prompt |
| 2 | Check `--cd` is still accepted by the `exec` verb | CLOSED | same block, `:2589-2590` — "cwd is agy's workspace root, so cd there"; `--cd` handled by the wrapper, not passed to agy |
| 3 | Add a doc-test / smoke check that argv puts booleans ahead of `--print` | CLOSED | `h-mad/tests/test_hmad_dispatch_exec.py:444` `test_agy_exec_runs_print_headless_prompt_as_last_arg`, asserting `--dangerously-skip-permissions` in argv at `:451` |
| 4 | Cross out the corresponding HemaSuite todo | CLOSED | sender recorded closure in HemaSuite `2026-08-19-main__exec-agy-flag-order-closed-no-fix-needed.md` (named in the Taken-Over-By stamp) |
| 5 | (OI) Nothing is claimed | CLOSED | verified — no record for this work in the state file |
| 6 | (OI) Not delivered to an agent lane — pick it up from here | CLOSED | discharged by items 1–3 |

**verdict:** FULLY-ABSORBED

---

## 6. `2026-08-20-main__handoff-read-todolist-fallback.md`

- **handover_from:** HemaSuite · main · session 603da342-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — fixed in `2ce26d3` and `b79b036`

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Rewrite READ Step 4 as a three-rung fallback ladder; it must never no-op | CLOSED | `2ce26d3` "READ Step 4 assumed a todo tool that this install does not have"; ladder at `handoff/SKILL.md:395` (rung 1 task tool), `:396` (rung 2 OMC notepad), `:378` "this step must never be a no-op" |
| 2 | Name the sink in the Step 5 report | CLOSED | `handoff/SKILL.md:413` `**Todos restored to:** <task tool \| .omc/notepad.md \| this report only>` |
| 3 | Soften the `description:` frontmatter's hard dependency | CLOSED | `handoff/SKILL.md:3` now reads "restoring the todo list (a task tool where one exists, else …, else an inline checklist)"; `git log -S'else an inline checklist'` → `2ce26d3` |
| 4 | Sweep the skills tree for other unconditional tool assumptions | CLOSED | `grep -rn 'TodoList\|TaskCreate\|TodoWrite' --include=SKILL.md` over the repo: only `handoff/SKILL.md` (all hedged, `:378-395`) and `benchling-integration/SKILL.md:236` (an unrelated `WorkflowTaskCreate` SDK symbol) |
| 5 | (OI) This item — handed over, unstarted | CLOSED | same as 1–4 |
| 6 | (OI) No h-mad claim to release | CLOSED | state file has no record for `handoff-read-todolist-fallback` |
| 7 | (OI) Not reproducible from config — won't-fix by design | CLOSED | superseded: `b79b036` "the todo opt-in applies mid-session, not at launch" documents `CLAUDE_CODE_ENABLE_TODO_TOOLS` at `handoff/SKILL.md:385-391`, correcting the brief's "no user config can add a built-in tool" |

**verdict:** FULLY-ABSORBED

---

## 7. `2026-08-20-main__skill-candidate-backlog-reconcile.md`

- **handover_from:** HemaSuite · main · session 97490faf-…
- **taken_over_by:** skills · main · session 86c6aded-… · 2026-09-01 — all four stores re-measured

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Re-measure the four stores before anything else | CLOSED | census re-run this triage: `skill_candidates_census.py docs/skill-candidates.md` → 155 candidates, OPEN=8; HemaSuite main store → 314 candidates, OPEN=125 |
| 2 | Follow the automation-scout reconcile protocol | CLOSED | `handoff/references/automation-scout.md` §"Reconcile the open rows FIRST" is the standing contract; applied in items 3 and 4 |
| 3 | Start with this repo's own ~97 rows | CLOSED | `docs/skill-candidates.md` census: 155 candidates, 113 terminal, **8 open**. Note the divergence: the `Taken-Over-By` stamp recorded "3 open of 150" on 2026-09-01, so 8 does **not** confirm 3 — either the scout appended rows since, or one of the two runs counted differently. Open either way, and small either way |
| 4 | Then the three HemaSuite stores (~245 rows) | **STILL-OPEN** | census on `/Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md` → **125 open of 314** (85 maybe, 40 yes). The store grew rather than drained |
| 5 | Update the summary table at the top of each file in the same pass | **STILL-OPEN** | tied to item 4; cannot be complete while 125 rows are unreconciled |
| 6 | (OI) The 245 HemaSuite rows — open, needs judgement | **STILL-OPEN** | same measurement as item 4 |
| 7 | (OI) This repo's 97 rows | CLOSED | same as item 3 |
| 8 | (OI) No h-mad claim to release | CLOSED | verified in `docs/.bkit-memory.json` |
| 9 | (OI) Two rows deliberately left open on the merits | CLOSED | deliberate by design, not owed work |

**verdict:** OWES — the HemaSuite-store reconcile (125 open rows) and its summary tables.

---

## 8. `2026-08-24-main__audit-dispatch-contract-integrity.md`

- **handover_from:** HemaSuite · feature/201-grounding-evidence-coverage · session a7f5968f-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — all three shipped

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Claim the feature before starting | CLOSED | moot — work shipped; no live owner in `docs/.bkit-memory.json` |
| 2 | D-2: `_count_section_findings` sentinel is punctuation-intolerant, false-FAILs on `None.` | CLOSED | `_is_none_sentinel` at `h-mad/scripts/h_mad_audit_gate.py:51`, applied at `:94`; docstring at `:79` names `None.` and `**None**` |
| 3 | D-3: drop/condition the `.tmp`+`mv` advice; add the `result.status` caveat | CLOSED | `grep -c '\.tmp' h-mad/scripts/h_mad_assemble_audit.py` → **0**; `result.status` caveat present 3× in `h-mad/SKILL.md`, 2× in `h-mad/references/orchestration-mode.md` |
| 4 | D-1: emit the output-framing contract at the head as well as the tail | CLOSED | `h_mad_assemble_audit.py:143` "!!! READ THIS BLOCK FIRST AND OBEY IT LAST !!!" and `:152` the END-CONTRACT separator; `:161` makes a template that cannot carry a head contract a HALT verdict |
| 5 | Optional: surface thinking-tokens + tool-call count beside the gate verdict | CLOSED | `h-mad/scripts/h_mad_audit_cycle.py:242` emits `tools=… ok=… failed=… thinking=…`, with a `low-evidence` flag at `:244`; mutation spec `h-mad/tests/mutation-specs/audit_effort.json` |
| 6 | (OI) All three defects — not started, unclaimed | CLOSED | items 2–4 |
| 7 | (OI) Evidence in a volatile `/private/tmp` scratchpad | CLOSED | moot — the fixes landed; the brief inlines what was needed |
| 8 | (OI) Unverified that D-1's fix belongs in the assembler rather than the template | CLOSED | resolved in favour of the assembler — the head-emit lives in `h_mad_assemble_audit.py:143`, not a template |

**verdict:** FULLY-ABSORBED

---

## 9. `2026-08-27-main__mutation-anchor-pre-push-hook.md`

- **handover_from:** /Users/kimhawk/orca/HemaSuite · main · session 676e7f12-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — shipped

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Port the HemaSuite pre-push hook into the h-mad skill, parameterised | CLOSED | `d275d7b` "guard mutation-anchor drift at the push boundary"; `h-mad/git-hooks/pre-push` (6.2K) + `h-mad/git-hooks/install.sh` (4.1K). Source `58a81732` is a HemaSuite hash and does not resolve here, as expected |
| 2 | Install it in this repo and prove both directions | CLOSED | `.git/hooks/pre-push` → symlink to `/Users/kimhawk/orca/skills/h-mad/git-hooks/pre-push`; reject direction pinned by `h-mad/tests/mutation-specs/prepush_anchor_hook.json` |
| 3 | Fix the `find` fail-open in `handoff/SKILL.md` (two sites) | CLOSED | `handoff/SKILL.md:242` and `:560` now use `command find` with stderr to a file, not `2>/dev/null`; `:559` "`command find`, and NO `2>/dev/null` — both deliberate"; `:589` explains the rc read |
| 4 | Decide whether the hook belongs in `h-mad/hooks/` or a new top-level dir | CLOSED | decided — `h-mad/git-hooks/` exists as its own directory, separate from `h-mad/hooks/` (Claude Code hooks), exactly the separation the brief suggested |
| 5 | (OI) The port itself — not started, unclaimed | CLOSED | item 1 |
| 6 | (OI) `gate-blindness-hardening` holds a stale claim (21 days) | CLOSED | `docs/.bkit-memory.json`: `gate-blindness-hardening` `owner_session_id` is `None` |
| 7 | (OI) Whether `h_mad_wire_registry.py` still exists — unverified | CLOSED | it exists at `h-mad/scripts/h_mad_wire_registry.py`; the absence was a truncated install, per brief 10 |

**verdict:** FULLY-ABSORBED

---

## 10. `2026-08-28-main__stale-install-and-wire-registry-handover.md`

- **handover_from:** HemaSuite · main · session ce0dd6d0-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — all three closed

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | An UNCLASSIFIABLE spec is invisible at push time — pick a visible signal | CLOSED | the visible-count option was taken: `h-mad/scripts/h_mad_mutation_harness.py:22-25` documents `unclassifiable=N` on every `ANCHORS:` summary line, and `:25` makes `unclassifiable>0` produce `ANCHORS_UNREADABLE` |
| 2 | Multi-pin support for `h_mad_wire_registry.py` — unblocked, un-started | CLOSED | `3219bdd` "wire-pin gate reads numbered WIRE labels, and registers every wire"; `pin_labels` at `h-mad/scripts/h_mad_wire_registry.py:60`, `unresolved_pins` at `:74`, both used at `:662` and `:666` |
| 3 | `gate-blindness-hardening` stale claim — needs an owner decision | CLOSED | `docs/.bkit-memory.json` → `owner_session_id: None` |
| 4 | `wip/check-anchors-local-4aeee78` — safe to delete | CLOSED | `git branch -a --list '*check-anchors-local*'` returns nothing; branch gone |

**verdict:** FULLY-ABSORBED

---

## 11. `2026-08-29-main__hmad-tooling-defects.md`

- **handover_from:** HemaSuite · feature/202-guideline-claim-like-visibility · session f419d046-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — `90fce10`, `e87fe24`, merged `2b569da`

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | `h_mad_wire_registry.py verify` compares two registries in a nested project | CLOSED | `e87fe24` "verify compared two different registries in a nested project" |
| 2 | Stop the Phase-5 flow writing undeclared keys that brick the record | CLOSED | `90fce10` "an ad-hoc key must not brick the record it lands on"; brief itself records no Phase-5 writer existed — the fix landed at the guard, with `--drop-undeclared` as the sanctioned repair |
| 3 | Suggested: a regression test for each (nested-project fixture; undeclared-key refusal) | CLOSED | `h-mad/tests/test_h_mad_state_write.py:318` `test_a_write_that_introduces_an_undeclared_key_is_still_refused` and `:346`; mutation specs `state_undeclared_keys.json` and `wire_registry_base_path.json` |
| 4 | (OI) `#48` ad-hoc state fields brick the record — marked DONE in-brief | CLOSED | `90fce10`, merged `2b569da` |
| 5 | (OI) `#49` verify compares two registries — marked DONE in-brief | CLOSED | `e87fe24`, merged `2b569da` |
| 6 | (OI) Nothing is claimed | CLOSED | verified in both `.bkit-memory.json` files |

**verdict:** FULLY-ABSORBED

---

## 12. `2026-08-29-main__skill-candidates-hmad-domain-rows.md`

- **handover_from:** HemaSuite · main · session f419d046-…
- **taken_over_by:** skills · main · session 86c6aded-… · 2026-09-01 — all 36 re-derived by name; HemaSuite `6529a94f`

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Confirm the 36 rows are h-mad-domain, then work them under scout rules | **STILL-OPEN** | re-derived all 36 by name against `/Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md`: 20 now terminal (LANDED/DECLINED), **16 still open** (`yes`/`maybe`), 0 missing |
| 2 | Sweep for sibling re-filings before flipping any row | CLOSED | discharged inside the 2026-09-01 pass — rows were re-derived by name, not by the stale line numbers, which is the stronger form of the sweep |
| 3 | Write the flips into HemaSuite's file and commit there | CLOSED (partial by design) | 20 of 36 carry terminal verdicts in that file today; the remainder is item 1, not a separate write |
| 4 | (OI) 36 h-mad-domain rows — handed over, parked | **STILL-OPEN** | the 16: `h-mad-phase-state-bump`, `h-mad-post-compile-port`, `staged audit-prompt assembler with size guard`, `audit-report-must-be-gate-legible`, `two-pass-review-with-disjoint-angles`, `atomic-state-write-refuses-on-one-bad-key`, `mutation-spec-per-module`, `wire-scoped-revert-via-harness`, `realpath-before-routing-a-todo`, `five-surface-correction-sweep`, `mutual-discrimination-mutation-run`, `read-the-diff-after-a-dispatch-timeout`, `mutation-anchor-preverify`, `shell-probe-failure-must-not-look-like-absence`, `contract-tests-must-track-tool-output-shapes`, `derive-dispatch-counts-only-where-the-plan-fixes-them` |
| 5 | (OI) Two rows overlap the `hmad-tooling-defects` brief; may close off its back | CLOSED | this item asked only whether the two rows could close off that brief. One did: `wire-registry-invocation-needs-four-flags` is now `**DECLINED**` off `e87fe24`. The other, `atomic-state-write-refuses-on-one-bad-key`, could not and stays `maybe` — it is already one of the 16 counted in item 4, so it is not a separate still-open item here |

**verdict:** OWES — 16 of the 36 rows remain open in HemaSuite's store (items 1 and 4, the same set counted once).

---

## 13. `2026-08-30-main__handoff-linked-worktree-commit.md`

- **handover_from:** HemaSuite · main · session 756df57f-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — merged as `4a86ed3`

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Reproduce first from a linked worktree: WRITE's doc gets zero commits | CLOSED | superseded by the fix; `4a86ed3` "WRITE no longer orphans its own doc" |
| 2 | Pick the destination — (a) disposable worktree, (b) conditional main-tree commit, (c) stage and say so | CLOSED | decided and implemented: `handoff/scripts/handoff_commit.py` (434 lines) added by `4a86ed3` |
| 3 | Guarantee no path through WRITE ends with an unreferenced file | CLOSED | `4a86ed3` also adds `handoff/scripts/test_handoff_commit.py` (327 lines) covering the paths |
| 4 | Pin it with a doc-test in `test_handover_docs.py` | CLOSED | `4a86ed3` adds 79 lines to `handoff/scripts/test_handover_docs.py` |
| 5 | (OI) The fix itself — not started, scoped only | CLOSED | items 2–4 |
| 6 | (OI) Destination decision blocked on an operator call | CLOSED | resolved — `handoff_commit.py` exists and ships the chosen shape |
| 7 | (OI) `orca/skills` 2 commits behind origin — informational | CLOSED | informational only, long since moved on |
| 8 | (OI) Symlink couples this repo to live behaviour — standing constraint | CLOSED | labelled a standing constraint, not a task |

**verdict:** FULLY-ABSORBED

---

## 14. `2026-08-31-BrightGold70-j1-residual-probes__split-and-surface-probes.md`

- **handover_from:** skills · main · session dbb07b5d-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — merged as `016120f`

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Probe the `.result.split` response shape; route or close the row either way | CLOSED | `docs/skill-candidates.md:952-968`: "**CLOSED 2026-08-31, no code change.**" — raw response `{"split":{"handle":…,"tabId":…,"paneRuntimeId":1}}`, no `paneKey`/`leafId`, so nothing joinable to route |
| 2 | Attempt to induce `surface: background`; record "not inducible" if so | CLOSED | `docs/skill-candidates.md:944-950`: all 31 responses `surface: visible`, "`surface: background` was not inducible"; guard retained |
| 3 | Reconcile `docs/skill-candidates.md` under the j1 heading with both probe results | CLOSED | the `## 2026-08-31 — j1-launch-pane-pin (takeover probe)` section at `docs/skill-candidates.md:852` carries both outcomes |
| 4 | (OI) Both items — not started, not blocked | CLOSED | `016120f` "validate paneKey-less codex launch handles"; codex 11/11 missing, sleep 0/16, agy 0/3 |
| 5 | (OI) Claim on `j1-launch-pane-pin-durability` was released; claim on takeover | CLOSED | `docs/.bkit-memory.json` → `j1-launch-pane-pin-durability` `owner_session_id: None` |

**verdict:** FULLY-ABSORBED

---

## 15. `2026-08-31-main__j1-launch-pane-pin-durability.md`

- **handover_from:** HemaSuite · feature/41-headless-nlm-auth-gating · session e66079ba-…
- **taken_over_by:** skills · main · session unknown · backfilled 2026-09-01 — merged as `016120f`

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Decide whether the upstream `paneKey` omission premise still holds | CLOSED | measured and settled: `h-mad/references/agent-substrate.md:27` records `sleep 300` 16/16 present, agy 3/3 present, codex 11/11 absent, every response `surface: visible` |
| 2 | File it durably in `docs/skill-candidates.md`, not a TodoList number | CLOSED | `docs/skill-candidates.md:852` `## 2026-08-31 — j1-launch-pane-pin (takeover probe)`, explicitly "the durable home its Next Step 2 asked for" |
| 3 | Reconcile `agent-substrate.md:27` against `hmad-dispatch.sh:860` — the two disagreed | CLOSED | `cb4f046` "date-scope the J1 placeholder claim across all five sites"; `agent-substrate.md:27` now says "It is **intermittent, not invariant**" and describes the paneKey-primary + validated-handle fallback that `hmad-dispatch.sh` implements |
| 4 | (OI) Upstream `paneKey` omission — premise unverified, not blocking | CLOSED | `016120f`; fallback validates the exact response handle against `terminal list` |
| 5 | (OI) Unrelated stale claim on `handoff-linked-worktree-commit` — FYI | CLOSED | `docs/.bkit-memory.json` → `owner_session_id: None` |

**verdict:** FULLY-ABSORBED

---

## 16. `2026-09-01-main__handoff-restore-chain-and-audit-version-discovery.md`

- **handover_from:** HemaSuite · feature/41-headless-nlm-auth-gating · session 1d372f45-…
- **taken_over_by:** skills · BrightGold70/handoff-restore-chain · session 86c6aded-… · 2026-09-01

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | D1: make check 3's `Handover-From:` exception reachable, not a fallback | CLOSED | `c3cc0dc` "merge: handoff restore chain + h-mad audit surface discovery"; `_HANDOVER_FROM_RE` at `handoff/scripts/handoff_paths.py:128`, `pending-handovers` and `carry-forward-sources` subcommands at `:282`, `:314`; mutation spec `handoff/tests/mutation-specs/pending_handovers.json` |
| 2 | D2: WRITE has no carry-forward obligation | CLOSED | `handoff/SKILL.md:983` §"Carry the predecessor's open items forward" — "walk **every** entry … this handoff must do exactly one of"; gather step at `:857-862`; `handoff/tests/test_handoff_carry_forward.py` (206 lines) |
| 3 | D3: `Supersedes:` is unspecified and unaudited — define or drop | CLOSED | defined at `handoff/SKILL.md:904` in the required-template table and `:916`; rationale at `:908` |
| 4 | D4: `_VERSION_RE` blind to surface-suffixed audits; `impl-plan` key mismatch | CLOSED | `h-mad/scripts/h_mad_cycle_counts.py:41` `\.v(\d+)(?:\.[A-Za-z0-9][A-Za-z0-9_-]*)?\.md$`; dash/underscore alias map at `:21`, used at `:135`; `h-mad/tests/test_h_mad_audit_surface_discovery.py` (257 lines) + `mutation-specs/audit_surface_discovery.json` |
| 5 | Decide whether D1–D3 are one feature or two | CLOSED | decided — shipped as one merge, `c3cc0dc`, covering all four |
| 6 | (OI) All four items above are open | CLOSED | items 1–4 |
| 7 | (OI) No claim accompanies this handover | CLOSED | verified in `docs/.bkit-memory.json` |
| 8 | (OI) Receiving repo's `main` was dirty; symlink couples the repos | CLOSED | handover targeted its own worktree, as instructed; standing constraint |
| 9 | (OI) Not investigated: whether D1/D2 dropped items on repos other than HemaSuite | **STILL-OPEN** | `grep -rn 'INDEX.md' docs/handoffs/*.md` and `git log --all --grep='INDEX'` find no cross-repo sweep; the brief's suggested probe (`~/.claude/handoffs/INDEX.md`) was never run |

**verdict:** OWES — the cross-repo sweep for dropped items outside HemaSuite.

---

## 17. `2026-09-02-main__audit-report-docs-copy.md`

- **handover_from:** HemaSuite · main · session f15c716a-…
- **taken_over_by:** skills · BrightGold70/audit-report-docs-copy · session session_01K1d48W2pVLpA3yJ8V6LjrB · 2026-09-02

**This brief belongs to a LIVE foreign lane. Do not adopt its items and do not read them as abandoned.** The receiving branch `BrightGold70/audit-report-docs-copy` is checked out in the linked worktree `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy` and is committing as this triage runs — its tip moved from `5b6c7b6` to `b551ca0` inside a minute, both `docs(audit-report-docs-copy): impl-plan … 5b audit cycle`. The lane has reached Phase 5b (impl-plan under audit); no production code has shipped yet, which is the expected state at 5b, not a stall.

Items below are reported for visibility and are excluded from this triage's still-open count.

| # | open item (≤20w) | status | evidence |
|---|---|---|---|
| 1 | Reproduce the `/tmp`-vs-docs gap on the live `nlm-cli-version-pin` corpus | HANDED-ELSEWHERE | live lane, tip `b551ca0` "impl-plan v1.3 after 5b audit cycle 3" — planning stage, no reproduce artefact committed yet |
| 2 | Read the recipe surfaces: SKILL step 6.6/step 9, `h_mad_report_wait.py`, `h_mad_extract_report.py` | HANDED-ELSEWHERE | preparatory; no landed change on any of them, consistent with 5b |
| 3 | Choose the fix: step 9 copies before gating, or `--persist-to`, or `report_wait` blocks on the copy | HANDED-ELSEWHERE | `grep -rn 'persist-to\|persist_to' h-mad/scripts/hmad-dispatch.sh h-mad/SKILL.md` → **no hits**; the choice is the lane's to make at 5c/5d |
| 4 | Pin it both directions: a `/tmp`-only report must not gate; the copy must be byte-identical | HANDED-ELSEWHERE | no report-persistence spec under `h-mad/tests/mutation-specs/` yet; that lands at 5d/5e in this lane |
| 5 | Consumer-side reference guard in HemaSuite | CLOSED | not work this repo owed — a pointer. The brief records the consumer half as already fixed: HemaSuite `d1e73d53` (guard) and `9e855dfa` (restore). Both are 8-char HemaSuite hashes and do not resolve here, as expected |
| 6 | (OI) Recipe half of HemaSuite task #33 — not started | HANDED-ELSEWHERE | branch carries `docs/` planning commits `d12ec34` → `b551ca0`; the lane owns it and is active |
| 7 | (OI) Do not touch `/Users/kimhawk/orca/skills` on `feature/pin-agents-tail-banner` | CLOSED (honoured) | work is confined to the linked worktree; this triage made no repo edits |

**verdict:** HANDED-ELSEWHERE — foreign lane, live and progressing. Nothing here is owed by this lane; re-check at that branch's next handoff rather than re-triaging it.

---

## Cross-cutting observations

- **12 of 17 briefs need nothing from this lane** — 11 fully absorbed, plus the live foreign lane. The 2026-09-01 cold-start triage that backfilled the `Taken-Over-By:` stamps was accurate on every claim spot-checked here: every hash it cited resolves, and every code claim it made holds at HEAD.
- **The two skill-candidate briefs are the largest residue.** Between them, 125 open rows in HemaSuite's main store and 16 of the 36 handed-over h-mad-domain rows. Both are judgement work in another repo, not code owed here.
- **Nothing in the 17 briefs holds a live claim.** `docs/.bkit-memory.json` carries 31 features and exactly one live `owner_session_id` — `pin-agents-tail-banner`, held by the current session.
- **Two stale claims the briefs flagged are both released**: `gate-blindness-hardening` and `handoff-linked-worktree-commit` are `owner_session_id: None`.

---

## Retirement decision (session f70b9d62, 2026-09-02)

`carry_forward_sources` lists every `**Taken-Over-By:**` brief that no handoff anywhere names in
`**Supersedes:**`. Retirement is therefore repo-wide and belongs to a WRITE, not a READ. Store-wide
only four documents are currently named in any `Supersedes`, which is why this queue only grows.

Who may name each brief, from its own `Taken-Over-By` value:

| lane | count | may this branch name it? |
|---|---|---|
| `skills · main` (this lane's chain) | 15 | **Yes**, once its still-open items are re-emitted. |
| `skills · BrightGold70/handoff-restore-chain` | 1 | **Yes** — lane is dead (branch deleted, merged `c3cc0dc`, contained in `main`, absent from `worktree-ps`). Orphaned: nobody else will ever retire it. |
| `skills · BrightGold70/audit-report-docs-copy` | 1 | **No, never.** Lane is LIVE and committing (`b551ca0`, 5b audit cycle 3). Naming it retires it repo-wide and evaporates their backlog. Leaving it listed is correct. |

**The 9 still-open items this branch owes** — re-emit every one in the next WRITE's Open / Blocked
Items. Four are operator decisions; five are work sessions.

1. `#68` — decide whether to amend the shipped `tdd-dispatch-verification-discipline` spec with the
   prompt-size-ceiling finding, or close it as covered. No decision recorded anywhere. *Decision.*
2. `#86` — close as a duplicate of `#67`/`#66`/`#68`. The `#NN` numbers were HemaSuite TodoList ids
   and that list is gone, so this needs a judgement call, not a lookup. *Decision.*
3. gate-blindness — never filed as a GitHub issue; absolute paths need sanitising first. Explicitly
   deferred to the operator by the brief; the code fix itself shipped. *Decision.*
4. Cross-repo sweep of `~/.claude/handoffs/INDEX.md` to see whether the handoff-drop mechanism hit
   repos other than HemaSuite. The probe the brief suggested was never run. (This is the orphaned
   restore-chain brief's residue — this lane is the only one that can carry it.)
5. HemaSuite `docs/skill-candidates.md` reconcile — **re-measured 2026-09-02 with
   `handoff/scripts/skill_candidates_census.py`: 125 open (85 maybe, 40 yes) of 314.**
6. The per-file summary tables, in the same pass as item 5. *Decision, once the rows are done.*
7. The same HemaSuite reconcile restated as that brief's own Open Item.
8. The 16 still-open h-mad-domain rows of the 36 handed over (20 are now terminal). Named in
   section 12 of this ledger.
9. The same 36-row set restated as that brief's Open Item.

Items 5-9 live in `repo: /Users/kimhawk/orca/HemaSuite · branch: main · worktree:
/Users/kimhawk/orca/HemaSuite`. Foreign repo — a HANDOVER candidate, not code owed in this tree.

This repo's own store re-measured the same day: **8 open (6 yes, 2 maybe) of 155**. The predecessor
recorded "0 yes, 3 open of 150" on 2026-09-01, so it has grown; do not carry either number. The
census script lives at `handoff/scripts/skill_candidates_census.py`, not under `h-mad/scripts/`, and
the store is a bullet list rather than a table — an ad-hoc pipe-row parser returns 0 and reads as an
empty file.

The 17th brief's 5 open items belong to the live sibling lane and are reported in section 17 for
visibility only. They are excluded from the 9 above.

**Verification of the ledger.** Five CLOSED verdicts were spot-checked against the tree and all five
held: `_verdict_after_boundary` at `h-mad/scripts/hmad-dispatch.sh:2677`; the `-- .` pathspec at
`:2696`; the corrected prompt-echo sentence at `h-mad/SKILL.md:781`; the multi-pin keys in
`h_mad_wire_registry.py`; `--check-anchors` in `h-mad/git-hooks/pre-push`. The `#68` still-open
verdict was confirmed by re-running its grep (0 hits).

**Count history, because two commit messages carry superseded figures.** `6f9b479` says 15 still-open
and 12 fully-absorbed; `a29c1d6` corrects the first to 14 but leaves the verdict split wrong. Both
were derived by hand from drafts of the table that the triage agent revised while this session was
reading it. The verified figures are the ones in the Totals line above — 9 still-open owed here,
11 fully-absorbed, 5 owing, 1 handed elsewhere — and they are checkable by counting the table's own
rows rather than trusting any prose, including this paragraph.
