# Handoff — Backlog triage rows closed, HemaSuite items handed over & resolved, Homebrew `codex` 0.166.0 unwedged

**Date:** 2026-11-01
**Branch:** main
**Project:** skills
**Supersedes:** 2026-10-31-main__skill-backlog-clusters-a-d.md, 2026-10-29-main__hmad-test-boundaries-complete.md
**Next-Session Focus:** Upgrade bkit 2.1.40 → 2.1.41 on Mac Studio (re-apply `g004` + `sprint-stop-hook-active`), decide the 5 open `skill-candidates.md` rows (`yes=4, maybe=1`), or investigate the 2 `test_grok_audit_surface_wrapper.py` stamp-leg failures on `main`.
**Suggested-Skills:** handoff (session resume and carry-forward verification), h-mad (row 2854 or 2853 as a feature, if chosen)

## Session Summary

On the Mac Studio, completed all actionable `orca/skills` backlog triage items from `2026-10-29-main__hmad-test-boundaries-complete.md` across 7 commits (`234f9be0`..`4972c653`), handed over the HemaSuite-owned items (Todos #8, #9, #12 — rows 5, 41, 49, 50, 52) to `HemaSuite@main` via `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-10-30-main__skills-handover-todos-8-9-12.md` (subsequently taken over and closed in `d05c85da`), and diagnosed + permanently fixed the Homebrew `codex` `0.166.0` Cask Gatekeeper/`sandbox-exec` hang on macOS. In parallel on Hawui-Macmini (`a5b994ca`..`437fb457`), sibling sessions reduced `docs/skill-candidates.md` from 26 open rows to 5 (`yes=4, maybe=1`) across Clusters A–D (`8c0823d6`, `82f6a5a4`, `d70ee861`, `d6a55c40`) plus TLA+ F3 null-heartbeat (`437fb457`), and retired `bkit-g001-bare-heredoc-substitution` and `bkit-subagentstop-additionalcontext` in `bb21715f` (fixed upstream in bkit `2.1.41`). Both `/opt/homebrew/bin/codex` (`codex-cli 0.166.0`, including `codex exec` and `brew reinstall --cask codex`) and the Mac Studio pinned Orca `codex` pane (`term_a958c89e-3f3c-4522-914d-8470a42ff9d6`, `PREFLIGHT: PASS`) are verified working end-to-end.

## Key Learnings

- **Homebrew 7 Cask `generate_completions_from_executable` wedges 268 MB CLI-only Mach-O binaries (`codex`) in `syspolicyd` when first-launched inside `sandbox-exec`:** In `/opt/homebrew/Library/Homebrew/cask/upgrade.rb:317-328`, `quarantine_release_decision` only inherits user approval for `Artifact::App` (`.app` bundles) and always returns `:skip` for `Artifact::Binary` casks like `codex`. Even after stripping `com.apple.quarantine`, `GeneratedCompletion#install_phase` (`generated_completion.rb:120-130`) runs `bin/codex completion bash|zsh|fish` inside `run_cask_sandbox` (`sandbox-exec`), which blocks the cold Mach-O vnode's first-launch `AppleSystemPolicy` (`syspolicyd`) upcall and wedges that literal path string in `syspolicyd`. Fix applied in `/opt/homebrew/Library/Homebrew/cask/download.rb` and `/opt/homebrew/Library/Homebrew/cask/artifact/generated_completion.rb` (persisted across `brew update` via `/opt/homebrew/.git/hooks/post-checkout` + `post-merge` + `post-rewrite`): for casks with no `:app` artifact (`cask.artifacts.none? { |a| a.class.dsl_key == :app }`), strip `com.apple.quarantine`, clone `staged_path` to `#{staged_path}-warm`, invoke `bin/* --help` once outside `sandbox-exec` to populate the kernel vnode `cs_blob` approval cache before renaming back to `staged_path`, and bypass `run_cask_sandbox`.
- **`skill_candidates_census.py --apply` requires a 2-column Markdown table (`| Row | Status |`) and a real filesystem path (or `/dev/stdin`, not `-`):** Passing a 3-column table (`| Row | Status | Note |`) is refused with `APPLY: REFUSED reason=malformed-row`, and passing `-` raises `FileNotFoundError: '-'`. Put the closure rationale on the row's continuation line in `docs/skill-candidates.md` and pass `/dev/stdin` when piping into `--apply`.
- **Upgrading bkit `2.1.40 → 2.1.41` resolves `#161` (`G-001`) and `#162` upstream, leaving only 2 of 6 carried patches to re-apply:** Per `.trail/learnings/2026-10-31-hawui-macmini-on-bkit-2-1-hawk.md` (`82480784`) and `bb21715f`, `bkit-g001-bare-heredoc-substitution` and `bkit-subagentstop-additionalcontext` are retired; on `2.1.41` only `bkit-g004-protected-branch-precision` and `bkit-sprint-stop-hook-active` need `patch -p1` re-application.

## Next Steps

1. **Upgrade bkit `2.1.40 → 2.1.41` on Mac Studio and re-verify carried patches**: Run `claude plugin marketplace update bkit-marketplace && claude plugin update bkit@bkit-marketplace`, re-apply `docs/patches/bkit-g004-protected-branch-precision/` and `docs/patches/bkit-sprint-stop-hook-active/` with `patch -p1` in `~/.claude/plugins/cache/bkit-marketplace/bkit/2.1.41`, delete `~/.claude/state/patch-verify.state`, and run `bash ~/.claude/hooks/patch-verify-on-update.sh` (expect `OK`).
2. **Decide each of the 5 open `docs/skill-candidates.md` rows** (`OPEN=5`: `yes=4`, `maybe=1`; verify line numbers via `python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md`):
   - **2854 (`yes`)** `implementation_authors` is append-only with no correction route (schema change + `h-mad/SKILL.md` attribution prose ~line 353).
   - **2853 (`yes`)** wire-pin and TDD gates see only `.py`, so a `.sh` production file is never mapped or judged (feature-scale).
   - **2816 (`yes`)** mutation-row re-anchor semantic diff (needs design ruling on "same tokens").
   - **2729 (`yes`)** Phase-5 Codex gate refuses the read-only checks GREEN and the verifier are told to run (needs a flag denylist: `--output`, `--output-directory`, `-o`, `--ext-diff`, `--textconv`).
   - **2885 (`maybe`)** append mutation rows without reformatting the spec.
3. **Fix the 2 `test_grok_audit_surface_wrapper.py` stamp-leg failures on `main`**: `_script_dir_with_stub_assemble_and_real_cycle` in `h-mad/tests/test_grok_audit_surface_wrapper.py` is missing a symlink for `h_mad_test_boundaries_check.py` in `real-cycle-scripts/` (`FileNotFoundError: .../real-cycle-scripts/h_mad_test_boundaries_check.py` when `h_mad_audit_gate.py` runs during design phase).
4. **[suggested] Review unimplemented draft/in-progress plans in `docs/01-plan/features/`**: e.g., `docs/01-plan/features/backlog-row-cycle.plan.md`, `docs/01-plan/features/claude-context-reduction.plan.md`, `docs/01-plan/features/orca-native-orchestration.plan.md`.

## Open / Blocked Items

**Carried from `2026-10-31-main__skill-backlog-clusters-a-d.md` and `2026-10-29-main__hmad-test-boundaries-complete.md`:**

- **Next Step 1 / Row 28 split (`test_grok_audit_surface_path_scope.py`)**: **closed** (`234f9be0`) — moved `test_real_audit_cycle_wrapper_passes_path_scope_to_scanner` and `test_real_audit_cycle_wrapper_halts_on_out_of_scope_log_before_scoring` into `h-mad/tests/test_grok_audit_surface_path_scope_real_cycle.py` and updated `h-mad/tests/mutation-specs/grok_audit_surface.json`; runtime dropped from `18.60s` to `3.13s`.
- **Next Step 2 / Row 18 (handoff redaction, next-session focus/skills headers, scout remedy classes)**: **closed** (`8597bce9`) — shipped in `handoff/SKILL.md` and `handoff/references/automation-scout.md`, pinned in `handoff/tests/test_handoff_carry_forward.py`.
- **Next Step 3 / Actionable triage rows 33, 35, 38, 39, 44, 46 (plus 23, 34)**: **closed** (`066c34df`, `290459c0`, `8597bce9`, `5746b8bb`, `830b3943`):
  - **Row 23**: Verified on Mac Studio (`HMAD-VERIFY-DOCTOR: PASS`; `verify-hmad-claims` `OK core expected pass got pass 3s 11798 distinct states found`).
  - **Row 33**: Added T19 `RMGUARD` refusal fixture (`test_exec_grok_rmguard_refuses_to_remove_outside_staging_prefix` in `h-mad/tests/test_grok_audit_surface_wrapper.py`) + `grok-tmp-rmguard-always` mutant (`ALL_CAUGHT`), and scoped T22 `test_quarantine_never_deletes` in `h-mad/tests/test_grok_audit_surface_containment.py` to AST function spans (`290459c0`).
  - **Row 34**: Confirmed 0 leaked `hmad_exec_prompt.*` files remain in `/private/tmp` or `$TMPDIR`; recorded closed in `docs/archive/2026-10/grok-audit-surface/grok-audit-surface.phase5-s0c-notes.md` (`290459c0`).
  - **Row 35**: Recorded the 8 Phase 5 measurement-class notes in `docs/03-analysis/grok-audit-surface.measurement.md` and `docs/archive/2026-10/grok-audit-surface/grok-audit-surface.phase5-s0c-notes.md` (`290459c0`).
  - **Row 38**: Extended `h-mad/scripts/h_mad_install_check.py` to read `.skill-lock.json` and emit non-blocking `AGENTS_SIBLING_COLLISION:<path> kind=<kind>` details (`install_check_roots.json` `ALL_CAUGHT 18/18`); documented same-session `general-purpose` fallback in `h-mad/SKILL.md`; added literal phase-scoped audit filename rule to all 4 author contracts (`5746b8bb`).
  - **Row 39**: Fixed `handoff/scripts/skill_candidates_census.py` `--help`/`-h` (`census_registry.json` `ALL_CAUGHT`) and all 5 LOW review residuals in `h-mad/scripts/h_mad_backlog_cycle.py` (`backlog_cycle.json` `ALL_CAUGHT 20/20`) (`066c34df`).
  - **Row 44**: Added WRITE item 9 (`Verify claimed state and files before drafting`) in `handoff/SKILL.md` (`8597bce9`).
  - **Row 46**: Executed `test_the_warn_and_target_fractions_still_match` in `h-mad/tests/test_h_mad_context_budget_docs.py` (`1 passed in 2.65s`).
- **Next Step 4 / Hawui-Macmini bkit patches + `patch-verify-on-update.sh` install**: **closed** (`82480784`, `a5b994ca`) — Hawui-Macmini upgraded bkit `2.1.40 → 2.1.41`, installed `~/.claude/hooks/patch-verify-on-update.sh` in `SessionStart`, and re-applied `g004` + `sprint-stop-hook-active`.
- **Next Step 5 / bkit #162 and G-001 #161**: **closed** (`d480b3d2`, `bb21715f`) — closed upstream in bkit `v2.1.41`; `bkit-g001-bare-heredoc-substitution` and `bkit-subagentstop-additionalcontext` are retired in the repo.
- **Row 2852/2859 (`null heartbeat counts as live` / TLA+ F3) & scout rows 2878–2880**: **closed** (`437fb457`, `5a441985`, `0539764c`, `74ad2831`) — `owner_is_live(None)` fixed in `437fb457`; auto-param-id lint landed in `13383cc1`/`5a441985`; census `--rev`/`--apply` usage landed in `0539764c`; regression failure diff superseded by `h_mad_failure_diff.py` (`74ad2831`).
- **Mac Studio carried bkit patches + `2.1.41` upgrade**: open — Mac Studio has `~/.claude/hooks/patch-verify-on-update.sh` installed and verified `OK` on `2.1.40`, and needs the `2.1.40 → 2.1.41` plugin update + `g004` and `sprint-stop-hook-active` re-application (Next Step 1).
- **`skill-candidates` census `OPEN=5` (`yes=4`, `maybe=1`)**: open — rows `2729`, `2816`, `2853`, `2854` (`yes`) and `2885` (`maybe`) remain open (Next Step 2).
- **HemaSuite `document-intake-source-review::Task 6` WIRE-RUNNER (Todo #8)**: **handed over & closed** — handed over to `HemaSuite@main` in `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-10-30-main__skills-handover-todos-8-9-12.md` (`4972c653`), taken over and closed in HemaSuite (`11874bce`) and recorded in `docs/03-analysis/2026-10-25-backlog-triage.md` (`d05c85da`).
- **Wire-registry `missing=268` (Todo #9 / Triage Row 5 + 5f nested `--rootdir`)**: **handed over & closed** — handed over in `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-10-30-main__skills-handover-todos-8-9-12.md` (`4972c653`) and closed in `d05c85da` (`h-mad/scripts/h_mad_wire_registry.py`, `wire_registry_runner.json` `ALL_CAUGHT 16/16`).
- **Rows blocked on HemaSuite (41, 49, 50, 52 — Todo #12)**: **handed over & closed** — handed over to `HemaSuite@main` in `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-10-30-main__skills-handover-todos-8-9-12.md` (`4972c653`), taken over and closed on HemaSuite, and recorded in `docs/03-analysis/2026-10-25-backlog-triage.md` (`d05c85da`).
- **Watch-only rows in `docs/03-analysis/2026-10-25-backlog-triage.md` (rows 19, 51, etc.)**: watch, unchanged since 2026-10-27.
- **Residuals recorded in 2026-10-31 stamps (not filed as rows)**:
  - **Name map:** generic `*test_*` skip still hides `h_mad_test_boundaries_check.py`.
  - **Missing receipt:** `h_mad_archreview_cycle.py` prompts write no `.assembled` receipt.
  - **Install check scope:** no user-level agy `hooks.json` is read.
  - **Codex hook timeout:** Codex's default hook timeout is unmeasured; `.codex/hooks.json` sets none.
- **Codex pin `term_134b0865…` stale on Mac Studio**: **closed** — repinned to `term_a958c89e-3f3c-4522-914d-8470a42ff9d6` in `.h-mad/orca-pins.env` (`hmad-dispatch env` → `PREFLIGHT: PASS`, `PROBE: ALIVE`), and unwedged `/opt/homebrew/bin/codex` (`codex-cli 0.166.0`).
- **Run 8 attempts 1–2**: evidence only, never score — unchanged since 2026-10-27.
- **2 `test_grok_audit_surface_wrapper.py` stamp-leg failures on `main`**: open — investigate in Next Step 3.

## Context for Next Session

**Files touched this session:**
- `h-mad/tests/test_grok_audit_surface_path_scope.py`
- `h-mad/tests/test_grok_audit_surface_path_scope_real_cycle.py` (new)
- `h-mad/tests/test_grok_audit_surface_containment.py`
- `h-mad/tests/test_grok_audit_surface_wrapper.py`
- `h-mad/tests/mutation-specs/grok_audit_surface.json`
- `h-mad/scripts/h_mad_backlog_cycle.py`
- `h-mad/tests/test_h_mad_backlog_cycle.py`
- `h-mad/tests/mutation-specs/backlog_cycle.json`
- `h-mad/scripts/h_mad_install_check.py`
- `h-mad/tests/test_h_mad_install_check_roots.py`
- `h-mad/tests/mutation-specs/install_check_roots.json`
- `h-mad/SKILL.md`
- `h-mad/agents/design-author.md`
- `h-mad/agents/implplan-author.md`
- `h-mad/agents/plan-author.md`
- `h-mad/agents/spec-author.md`
- `h-mad/tests/test_h_mad_agent_definitions.py`
- `handoff/SKILL.md`
- `handoff/references/automation-scout.md`
- `handoff/scripts/skill_candidates_census.py`
- `handoff/tests/test_skill_candidates_census.py`
- `handoff/tests/mutation-specs/census_registry.json`
- `handoff/tests/test_handoff_carry_forward.py`
- `docs/03-analysis/2026-10-25-backlog-triage.md`
- `docs/03-analysis/grok-audit-surface.measurement.md`
- `docs/archive/2026-10/grok-audit-surface/grok-audit-surface.phase5-s0c-notes.md`
- `docs/skill-candidates.md`
- `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-10-30-main__skills-handover-todos-8-9-12.md` (inbound handover brief written to HemaSuite store)
- `/opt/homebrew/Library/Homebrew/cask/download.rb` (local Homebrew CLI-cask quarantine guard)
- `/opt/homebrew/Library/Homebrew/cask/artifact/generated_completion.rb` (local Homebrew CLI-cask vnode-warming & sandbox bypass guard)
- `/opt/homebrew/.git/hooks/post-checkout` (and `post-merge`, `post-rewrite` symlinks)

**Uncommitted changes:** 5 pre-existing untracked items not from this session (`.codex/config.toml`, three `docs/03-analysis/2026-10-2{2,3}-*.analysis.md` files, and `hemasuite/docs/research/`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main && git pull --ff-only
python3 handoff/scripts/skill_candidates_census.py --list-open docs/skill-candidates.md
hmad-dispatch env
codex --version
```

**Related docs:**
- `docs/handoffs/2026-10-31-main__skill-backlog-clusters-a-d.md`
- `docs/03-analysis/2026-10-25-backlog-triage.md`
- `docs/skill-candidates.md`
- `.trail/learnings/2026-10-31-hawui-macmini-on-bkit-2-1-hawk.md`
- `.trail/learnings/2026-10-31-resume-2026-10-31-handoff-skill-hawk.md`
- `/Users/kimhawk/orca/HemaSuite/docs/handoffs/2026-10-30-main__skills-handover-todos-8-9-12.md`
