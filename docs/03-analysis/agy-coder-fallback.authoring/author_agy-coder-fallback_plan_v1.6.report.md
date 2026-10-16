PLAN-AUTHOR: DONE version=v1.6 path=docs/01-plan/features/agy-coder-fallback.plan.md lines=997 sha256=3c7585207ebf2f68bc6218a04b20464f3d875bf7fc06503c2224da6802dcb46c

# Report: agy-coder-fallback plan v1.5 -> v1.6 (mirrors spec v1.7, per the coordinator's mid-task message)

Before each write I checked the plan's sha256 (b5143219...) and its newest Version History entry (v1.5). Neither had moved. Spec v1.7 was read at c117a695, sha256 390c4771...

## Changes
- **Header.** Added that v1.6 mirrors spec v1.7 at c117a695. `git diff --stat 200ffd52 c117a695 -- h-mad` prints nothing.
- **Decisions list.** "D-1..D-11" becomes "D-1..D-14". There is one bullet each for D-12, D-13 and D-14, and each names where it binds. The AC census was re-run: `python3 h-mad/scripts/h_mad_ac_census.py <spec>` gives `ACS: OK count=19 frs=9` at c117a695, and the plan records that reading.
- **Stage 1, new item: the `codex_status` description and row rewrite.** It covers both surfaces, the schema description and the state-schema.md row. The old text was confirmed by grep: each phrase matched 1 line at c117a695. A tracked-tests grep for the four old phrases gives 0 files. That zero holds for this rewrite only, and the Task re-runs the grep. The property-order pin was verified at `test_h_mad_state_fallback_agent.py`: `index("fallback_agent") == index("codex_status") + 1`.
- **Stage 1, new item: AC-1.2 leap-second fixture.** `2016-12-31T23:59:60Z` runs once on each validator path, and the writer's own form is accepted on both. Verified that Python `datetime.fromisoformat` raises `ValueError: second must be in 0..59` under /opt/anaconda3 python.
- **Stage 4, DO-5, DO-6 and R-2.** These now cite D-12 and D-13 rather than "operator decision OQ-A/OQ-B".
- **Stage 7: FR-7 Attribution rule plus its fixture.** The fixture stores `implementer_switch.to=agy` with code from a Codex dispatch. Expected: implementer=codex, a Codex reviewer gets independent=false, and `review_non_independent` fires. The fixture must be RED against attribution read from `switch.to`.
- **Stage 8.** D-13 is now stated in full: post-merge, COMPLETE only after the stage passes with AC-8.1 and AC-8.2, and `step5:agy_tdd_hook_unverified` stands until then. Every reading stamps the sha and `agy --version` (1.4.0 at 200ffd52). A reading taken under a different version is taken again.
- **Owed → Spec.** The section now records that v1.7 answers the design-cycle items.
- **Version History.** v1.6 added: `VERSION-HISTORY: OK ... version=v1.6 ... placement=append`.
- **Precheck.** `PRECHECK: PASS issues=0`. The advisories are the same set kept in v1.5: stale header stamps, paths to new files or files relative to `h-mad/`, and COUNT false positives.

## Where the tree or documents disagree
- **Spec AC-7.1/AC-7.2 do not name the Attribution fixture.** Only FR-7 prose carries the rule. The plan carries the fixture in stage 7. Spec owes an AC if it should be gated as one; this is flagged in the plan's Owed section.
- **Minor: the spec's quoted `ValueError` wording.** Spec FR-1 quotes `ValueError: second must be in 0..59, not 60`. The repo interpreter prints `second must be in 0..59`, without ", not 60". The wording differs by Python version, and no claim depends on it. Spec may want to drop the suffix.

## Owed by other documents
- **Spec.** The AC for the Attribution fixture (see above). The optional `ValueError` wording fix.
- **Impl-plan.** Unchanged from v1.5: committed probes for M-4, M-3 and DO-1a. The AC-1.2 leap-second fixture runs on both paths.

## Probes
None created in this pass.

---
# Previous pass (v1.5) report follows

# Report: agy-coder-fallback plan v1.4 -> v1.5

Before writing I checked the file against the brief. Its sha256 was d6766d45... and its newest Version History entry was v1.4, both matching. No other writer touched it during my run. The digest above was computed after my last write.

## What changed, and why (decision sheet P1-P4 plus the brief)
- **P1, M-4.** Re-derived at 200ffd52 over design v1.0's DO-5 set (25 names). Result: 31 of 62 rows, in 4 specs. The M-4 procedure now lists the full set inline. R-3 is restated to 31 rows and gives the per-spec split. The figure 19 is kept only as the reproduced closure-only subset and is marked retired. I re-derived the number myself and did not copy the design's 31. I also fixed a false statement in R-3: v1.4 wrote the rows' `file` as `h-mad/hooks/...`, but every row actually carries `hooks/h-mad-codex-tdd-gate.py`, relative to `h-mad/`.
- **P2, DO-2.** v1.4 asked for "that log's agy version". That cannot be met, and DO-2 now says why: the log records no version. The obligation is restated as: name the log, say it has no version, and re-check class (a) against an `init.tools` inventory captured again together with `agy --version`. That matches design FR-8 step 1.
- **P3, OQ-A and OQ-B.** Both decisions are now in the plan. OQ-A is in stage 4 (destination `h-mad/scripts/h_mad_target_identity.py`) and in DO-5. OQ-B is in DO-6 and in R-2's mitigation, replacing v1.4's "design picks one" wording.
- **P4, agy version.** The Overview and R-9 now read `1.4.0` at 200ffd52, keeping the earlier `1.3.6` reading at 17d73037. The Overview states that this number drifts with every agy upgrade.
- **Stale owed bullet.** The "Spec FR-9 residual" owed text is gone. The FR-9 census paragraph said the residual "is being added to spec FR-9 alongside this revision". It now cites spec v1.6's paragraph "What the joined reading does not see in a `.py` file, and how the sweep covers it". I verified that text with `git show c853b207:<spec> | grep -n 'What the joined reading does not see'`.
- **Owed section.**
  - The spec items are now: agy 1.4.0 and stamping the version FR-8 and the re-check ran against; FR-6/AC-6.1 naming `h_mad_target_identity.py`; and an OQ-B record.
  - The Design bullet notes that v1.0 (df46f72a) addresses DO-1..DO-7.
  - The Impl-plan bullet adds the M-4 committed probe.
- **Header.** Added a provenance sentence: v1.5 read spec v1.6 at c853b207 and design v1.0 at df46f72a, and its new stamps are 200ffd52.
- **Version History.** Bumped to v1.5. Tool output: `VERSION-HISTORY: OK ... version=v1.5 ... placement=append`.

## Measurements re-run (all at HEAD 200ffd52)
- `git diff --stat 29ae3e7b 200ffd52 -- h-mad` printed nothing, so `h-mad/` is unchanged since plan v1.4.
- **M-4.** I ran a scratch probe from `h-mad/` with `/opt/anaconda3/bin/python3 -I`, then deleted it.
  - Method: `ast` over the hook; the closure is module-level functions called by name from `_safe_shell_command`, plus the design's 7 functions and 8 module-level assignments. For each row in `git ls-files 'tests/mutation-specs/*.json'` whose `file` is `hooks/h-mad-codex-tdd-gate.py`, it takes the line of the first occurrence of `find` and checks whether it falls in a node's `lineno..end_lineno` span.
  - Closure: 10 functions, the same names as the design lists. None of the 15 extra names were missing from the hook.
  - Results, in rows: 62 rows name the hook.
    - DO-5 set: 31 rows (`codex_gate_judge_wiring` 21, `codex_gate_shell_allowance` 6, `assemble_tdd_mutation_rows` 2, `tdd_gate_differential` 2).
    - Closure only: 19 rows (17 and 2).
    - 0 anchors absent from the file, and 0 that match more than once.
- `agy --version` printed `1.4.0`.
- **DO-2 log.** Ran `git ls-files --error-unmatch` on `docs/03-analysis/probes/multi-host-runtime/rehearsal/live-agy-2026-10-01.log`, so the log is tracked. Its first JSON line with an `init` key has top-level keys conversation_id, event and init, and its `init` keys are cwd, permission_mode and tools. `grep -ci 'version' <log>` gave 2 lines, both inside `version-history` names. The log carries no version.
- **R-9.** `grep -c 'SessionStart' ~/.gemini/antigravity-cli/builtin/skills/agy-customizations/docs/hooks.md` gave 3 lines under agy 1.4.0, the same as before.
- **OQ-A premise.** `grep -n` found `test_codex_gate_judge_timeout_reason` in `h-mad/tests/test_h_mad_codex_tdd_gate_judge.py`, and that test copies `scripts/h_mad_target_identity.py` into its tree. Confirmed.
- **Value sweep.** I collapsed newlines with `tr '\n' ' '`, then grepped for `19 rows|1\.3\.6|pick one|that log.s agy|sweep residual|OQ-[AB]`. Every remaining hit is intended: a historical reading that is marked as such, or a new statement.
- **Precheck.** `python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py <plan> --phase plan --root /Users/kimhawk/orca/skills` printed `PRECHECK: PASS issues=0` with 18 advisories, which I kept on purpose:
  - STALESHA on the header's historical stamps (e6610381, e7730f78). They are provenance, not current claims.
  - PATH on files this feature creates (the agy gate, `.agents/hooks.json`), on examples (`src/docs/foo.py`), on an archive path, and on two `hooks/...` paths relative to `h-mad/`. R-3 now says they are relative; M-4 says to run from `h-mad/`.
  - COUNT on Version History lines and on one prose line. These are false positives in text I did not change.

## Where the tree disagreed with the documents
- The plan's agy version (1.3.6) is stale; the tree shows 1.4.0.
- DO-2's version condition could not be met, because the log has no version.
- The plan's R-3 `file` path was wrong (`h-mad/hooks/...`); rows use `hooks/...`.
- The M-4 figure of 19 was correct for the closure but is the wrong unit now that the design fixes a larger set.

## Owed by other documents (I did not edit any of these)
- **Spec.**
  - agy `1.4.0`, with FR-8 and the SessionStart re-check stamping the version they ran against.
  - FR-6/AC-6.1 "shared module" = `h_mad_target_identity.py` (OQ-A).
  - Record OQ-B as an operator decision.
  - This is sheet item S3. A concurrent spec revision is in progress, and `git status` shows the spec modified.
- **Impl-plan.** Committed probes for M-4 and the M-3/DO-1a censuses under `docs/03-analysis/probes/agy-coder-fallback/`. That directory now exists untracked, apparently from the design author (sheet M1). I did not touch it.
- **Plan follow-up.** When the concurrent spec revision lands (v1.7), the header's "read spec v1.6" stamp will be one version behind. Re-stamp it in the next plan revision; it changes no claim.

## Declined
Nothing declined. Every P item's premise held when I checked it against the tree.

## Probes
I created `m4.py` in the session scratchpad and deleted it. `mrows.py` is also in the scratchpad; it was there before me and I left it alone.
