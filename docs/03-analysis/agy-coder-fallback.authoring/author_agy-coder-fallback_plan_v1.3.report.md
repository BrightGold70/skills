PLAN-AUTHOR: DONE version=v1.3 path=/Users/kimhawk/orca/skills/docs/01-plan/features/agy-coder-fallback.plan.md lines=861 sha256=a649354654c0055b766f7a947b89dcb3bf7108b0676aa9a9804814161535d58b

# plan v1.2 -> v1.3 (final corrective revision; cycle-2 build findings A-E only)

Ownership: asserted sha c5dbae34... and newest VH v1.2 before the first write. Between my edits I
checked that the newest VH line was still v1.2 and that mtime matched my own last write. No other
writer appeared. HEAD moved 2fd8dea7 -> 9c3b799d (audit reports + sidecar) -> e8def13f (spec v1.5).
Neither touched the plan.

## What changed
- A (AC-9.4, DO-7, stage 6). The six copies of the carve-out (five FR-9 surfaces plus the GREEN
  variant) are bound to one authority. As AC-9.4 asks, **the plan names the mechanism: a
  doc-derived equivalence test.** Reason: the copies sit in 4 files and 3 formats (markdown list
  item, markdown table cell, Python literal), so a shared source would mean restructuring.
  - The test holds the canonical sentence once.
  - Markdown is compared whitespace-collapsed; the assembler copy is read from the assembled
    prompt.
  - Control: 6 mutation rows, one per copy, each run alone and each required to fail the test
    (`MUTATION: ALL_CAUGHT`). A row that mutates two copies does not count.
  - Residual stated: the test does not catch a contradicting extra sentence or a 7th surface. The
    FR-9 joined-literal sweep covers those.
  - Also added: a Deliverables row, R-14 text, and a Design-owed bullet (where the test goes, and
    canonical text = spec FR-9).
- B (stage 6, Success Criteria, doc-pin census). The SKILL.md teammate-audit bullet
  `- **It does not license Claude to write Phase 5 production code` is rewritten.
  - It now separates audit-leg selection (`codex_status`, D-8) from resolved authorship
    (Claude only when resolved = claude for every ACTIVE step5 record, mirroring spec v1.5 FR-10).
  - The anchor and the tokens ACTIVE/every/unavailable/exhausted are kept.
  - The replacement condition is pinned: the bullet must name `h_mad_tdd_judge.py implementer` and
    `agy-authorship`. Baseline 0/0.
- C (stage 6, halt-surface census). Surface 5 is added: the `assemble()` wiring header in
  h_mad_assemble_tdd.py, located by content (`if shape == "wiring":`, a phrase split across two
  literals). Its pin `test_the_pin_is_told_what_its_red_must_be` ("never a missing") is added to
  stage 6's pin list and to the doc-pin census. The census states the class (a phrase split
  across a line break; two members, adjacent Python literals and hard-wrapped markdown), the
  joined-literal sweep, and its residual (run-time-built strings, later surfaces). Following the
  coordinator's correction, `_format_wiring_pin_header` is not cited anywhere: an earlier
  parenthetical of mine was removed (`grep -c _format_wiring_pin_header` on the plan = 0).
- D (stage 6 incident replay). The single wrong file line is replaced by the three pins:
  - T4 `test_notebooklm_resolver.py::test_resolver_calls_registry_arm_notebook_id_once` @531a6296b;
  - T5 `test_notebooklm_initialize.py::test_initialize_entry_point_resolves_through_registry_arm` @7aa0d9dec;
  - T6 `test_notebooklm_status_report.py::test_status_entry_point_resolves_through_registry_arm` @c2d671f6b.

  T5/T6 are replayed in direct-call form (two-argument getattr, no try/except, same spy
  assertion). The probe also records each committed scaffolded RED (AssertionError) with its old
  verdict (valid). Old halt / new valid now apply to the direct-call RED.
- E (doc-pin census, R-8). Missed pins are added:
  - Phase-5 section: `fallback_agent`.
  - Exit-code section: `exec grok` and `--agent grok`.
  - agy-runtime TDD gate: `rc 0` plus the forbidden `exit-code protocol`.
  - Prompt: test_h_mad_tdd_gate_docs.py `_hook_block` Hook-line and bullet tokens, with the
    no-`<`/`>` constraint.
  - Teammate section: `_skill_gate_bullet` and its tokens, plus `TEAMMATE_HEADING`,
    `--surfaces agy,grok` and `unmeasured`.

  The census is now called a candidate list. Its residual axes are named (short tokens, negative
  assertions, structural locators, misfiled section), with full-suite-per-Task as the backstop.
  R-8's "Every pin inside a rewritten section is listed" over-claim is removed.
- Requirements: 19 ACs including AC-9.4. The Owed-by-spec bullet now records spec v1.5's answers.
- VH v1.3 added via h_mad_version_history.py -> `VERSION-HISTORY: OK ... version=v1.3`.
- Precheck: `PRECHECK: PASS issues=0`. I fixed one PATH advisory I had introduced (now
  `h-mad/tests/fixtures/codex-text-8-exec.log`). The remaining advisories (planned new files,
  HemaSuite-relative archive path, STALESHA on e6610381/e7730f78, COUNT heuristics on VH lines)
  were already there and are kept deliberately: they are measurement stamps (M-class, out of
  scope) or new artifacts.

## Measurements re-run (command -> result)
- `python3 h-mad/scripts/h_mad_ac_census.py docs/01-plan/features/agy-coder-fallback.spec.md` at e8def13f -> `ACS: OK count=19 frs=9`.
- `git show e8def13f:<spec> | shasum -a 256` -> 7324587ee979... (matches coordinator).
- Joined-literal sweep: ast `str` constants for .py, whitespace-collapsed text otherwise. Regex
  `missing.symbol|tests the callee|ImportError.*AttributeError|AttributeError.*ImportError` (-i)
  over `git ls-files h-mad` at 9c3b799d -> 7 files. Line grep -> 6 files: the same set minus
  h_mad_assemble_tdd.py. Matches the spec.
- `git ls-files h-mad | xargs grep -ln 'never a missing'` -> 2 files (assembler and its test).
- `git grep -n '_format_wiring_pin_header' h-mad` -> 0 lines.
- Teammate-bullet baselines: the stage-6 python one-liner gives 'h_mad_tdd_judge.py implementer'
  -> 0 and 'agy-authorship' -> 0. Positive control: the same counter with 'ACTIVE' -> 1.
- `grep -c -- '- **It does not license Claude to write Phase 5 production code' h-mad/SKILL.md`
  -> 1. titled_section check: the bullet is inside "Teammate audit leg — when codex is
  unavailable" (True) and not inside "Codex authors Phase 5 ..." (False).
- `git ls-files 'h-mad/tests/*.py' | xargs grep -l 'codex-implementer-prompt'` -> 14 files.
  9 carry listed pins; 5 are unclassified (not read by hand).
- HemaSuite at 4d7a392c5: all 3 task commits are ancestors of HEAD (merge-base --is-ancestor).
  Per `git show --stat`, the pin files are as listed. Callers by
  `git grep -n "def <caller>" <rev> -- hematology-paper-writer/tools`: parent 0 and task commit 1
  for each of resolve_registry_notebook, initialize_project_notebook and generate_setup_report.
  T5/T6 carry `getattr(..., None)` + `except (Exception, SystemExit)`; T4 uses two-argument
  getattr.
- `git diff --name-only 17d73037 HEAD -- h-mad | wc -l` -> 0. h-mad is unmoved, so the existing
  FR-10 baselines' no-drift claim still holds.

## Tree contradicted
- The p2 report files `_skill_gate_bullet` under SKILL.md §"Codex authors Phase 5". It actually
  lives in §"Teammate audit leg" (titled_section probe). It is the same bullet that B rewrites,
  which is why B and E intersect.
- `_format_wiring_pin_header` does not exist; the text is in `assemble()` (coordinator also
  corrected this).
- The plan's HemaSuite stamp `86c3d0c8d` (stage 6, the "Reachable at" line) is now behind HEAD
  4d7a392c5. I left it as it was (measurement class) and stamped my new claims at 4d7a392c5.

## Owed / open
- Design: place the AC-9.4 equivalence test and fix its canonical sentence to spec FR-9's text
  (DO-7). The prose-vs-mechanical choice stays with the design.
- Impl-plan: the doc-pin census probe must also cover negative assertions and structural
  locators, and must classify the 5 unread prompt-naming test files.
- I did not re-derive the "23 distinct literals" figure with the 9th file added; it is stated as
  not re-derived.
- No probe files were created; all probes were inline heredocs, so nothing was left to delete.
