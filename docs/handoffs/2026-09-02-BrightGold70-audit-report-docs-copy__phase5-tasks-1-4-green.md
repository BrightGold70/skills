# Handoff — audit-report-docs-copy: Phase 5 Tasks 1–4 GREEN, halted at 74% context

**Date:** 2026-09-02
**Branch:** BrightGold70/audit-report-docs-copy (worktree `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy`; the main checkout `/Users/kimhawk/orca/skills` is on `feature/pin-agents-tail-banner` with a live h-mad run — do not edit that tree)
**Project:** skills (`github.com/BrightGold70/skills`, h-mad skill)
**Supersedes:** 2026-09-02-main__audit-report-docs-copy.md (the HemaSuite handover brief, taken over this session)

## Session Summary

Took over the HemaSuite handover (the codex-leg audit report is written to `/tmp` and never copied into docs) and ran it through `/h-mad "audit-report-docs-copy"`: Phases 1–4 gated on two surfaces (plan v1.11 after 8 audit cycles, design v1.18 after 10, impl-plan v1.12 after 12), then Phase 5 Tasks 1–4 of 6 are RED→GREEN with agy 5e-reviews COMPLIANT and the full h-mad suite green (2410). Halted pre-emptively at 74% context (ceiling 80%) with the h-mad state recording the halt; Tasks 5 (SKILL.md recipe) and 6 (23-mutation spec), 5f/5g, Phase 6 and 7 remain. Branch pushed to `origin/BrightGold70/audit-report-docs-copy` at `bc1308f`.

## Key Learnings

- The brief's premise narrowed on reproduction: the agy leg was already persisted (`audit-cycle` → `collect()` → `.p<i>.md`); only the codex leg — run outside the verb via `assemble --report-file` + `exec codex` — had no docs-copy step anywhere in SKILL.md (its recipe lived only in two memory files). Brief candidate (b) named `exec --report-file`, a flag that does not exist.
- The transport grammar took four audit cycles to get right and every correction came from an executed probe: bare `*.report.md` collides with Phase-7 `<feature>.report.md`; a `_cycle<N>` stem misses hand-staged `/tmp` names (`audit_hnag_c28_agy.report.md`); `^audit_.*` overlaps a derivable docs name (`audit_f` + surface `report`). Final: `^audit_[^.]+\.report\.md$` — dot-free stem, and docs names always carry `.audit.v<N>`, so the grammars are disjoint by construction (property test, not a production assert — an assert that can never fire cannot be mutation-tested).
- Two pre-existing mutation specs (`h-mad/tests/specs/audit_cycle_*.mutation.json`) carried an ABSOLUTE `root` pointing at `/Users/kimhawk/orca/skills/h-mad`, so `--check-anchors` from a worktree silently measured the main checkout; the anchors-unique TEST (which reads the worktree file) disagreed. Fixed to `../..`. Also: invoke the harness from the worktree (`python3 h-mad/scripts/…`), not `~/.claude/skills/h-mad/scripts/…`, which is the main checkout via the symlink.
- `git stash push -- <path>` refuses an intent-to-add (`git add -N`) file ("not uptodate. Cannot merge") and the revert silently does not land; for a brand-new production file, `mv` it aside for the revert test instead.
- codex `gpt-5.6-sol` hit "Selected model is at capacity" twice mid-audit (no report, `--out` absent); `--model gpt-5.5` override worked every time after. agy audit passes were low-evidence (1–2 tool calls) in ~80% of cycles; codex (12–28 file reads) found nearly every real defect.
- codex refused a GREEN correctly twice: AC-1.5 ("one function builds `.audit.v`") was false because reader modules build the same grammar to FIND audits; and a RED test that monkeypatched `Path.write_text` forced a `write_text` implementation the design forbade. Both were test/spec defects, fixed on the test side.
- `pytest` `capsys.readouterr()` returns `CaptureResult(out, err)` — a RED test used `.stdout` and failed for the wrong reason.

## Next Steps

1. `/handoff read` then `/h-mad "audit-report-docs-copy"` — the state is `halted` (`halt_reason=step5d:context_ceiling_preemptive…`); choose resume, re-arm the TDD gate (`h_mad_state_write.py docs/.bkit-memory.json --feature audit-report-docs-copy --set phase=step5 --set halt_reason=null --claim <session>`), and continue at Task 5.
2. Task 5 (docs) — `docs/01-plan/features/audit-report-docs-copy.impl-plan.md` §Task 5: new `## Second surface — the codex leg` section in `h-mad/SKILL.md` after `## Putting \`hmad-dispatch\` on PATH` (line ~1791), pointer sentence in the audit-cycle paragraph, step-9 sentence, helper-registry entry, `collect-report` row in `h-mad/references/orchestration-mode.md`; RED via `h_mad_assemble_tdd.py --task "Task 5" --phase red --module recipe-docs --test-path h-mad/tests/test_h_mad_collect_report_docs.py`. `test_h_mad_audit_cycle_docs.py` must stay green.
3. Task 6 (mutation spec) — `h-mad/tests/mutation-specs/collect_report.json`, 23 mutations per the impl-plan table; **the table's test names are aspirational — map each to the real test names in `h-mad/tests/test_h_mad_collect_report.py` / `test_h_mad_audit_gate.py` / `test_hmad_dispatch_collect_report.py`** (e.g. `test_collected_path_surface_none_preserves_pass_index_path`, `test_cli_transport_named_report_is_invalid_before_scoring`, `test_collect_report_verb_execs_script_with_argv`) and update the impl-plan table to match; add `test_mutation_spec_shape` (AC-6.3a). Run `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/collect_report.json` → `MUTATION: ALL_CAUGHT mutations=23 caught=23 survived=0 refused=0 unreadable=0`.
4. Owed verification: the codex anti-gaming verifier (`h-mad/references/codex-verifier-prompt.md`) was NOT run for Tasks 1–4 (budget). Run it once over the four modules before 5f.
5. 5f: `h_mad_baseline_sha.py` reports UNVERIFIED by construction (branch predates 5c); the 5c sha is `f5e4afd` (also in `.h-mad/5c_sha_audit-report-docs-copy.txt`, untracked). `h_mad_wire_registry.py verify --base f5e4afd --rootdir <repo> --testpath h-mad/tests` then `challenge`. Full suite `python3.11 -m pytest h-mad/tests -q` (~5 min, run in background).
6. 5g commit, then Phase 6a-prime (`h_mad_archreview_cycle.py stage --base f5e4afd --head <5g sha>`), 6a gap analysis, Phase 7 report + archive + push. Merge to `main` is the operator's call (the main checkout's live run reads `~/.claude/skills/h-mad` → main checkout; this branch's edits reach it only at merge).

## Open / Blocked Items

- **Recipe half of HemaSuite task #33** (from `**Handover-From:** HemaSuite · main · session f15c716a-0b1b-43cc-8dc0-d67f5670a59e`) — status: in progress, Tasks 1–4 of 6 GREEN. `repo: /Users/kimhawk/orca/skills · branch: BrightGold70/audit-report-docs-copy · worktree: /Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy`. Artifacts: spec/plan/impl-plan under `docs/01-plan/features/audit-report-docs-copy.*`, design under `docs/02-design/features/`, all audits committed (`.p1.md` agy, `.codex.md` codex), TDD prompts `/tmp/tdd_audit-report-docs-copy_t{1..4}_{red,green}.txt`, reviews `/tmp/rev_audit-report-docs-copy_t*.txt`. Claim: released at closeout (see below).
- **Tasks 5–6, 5f, 5g, Phase 6, Phase 7** — status: not started (Next Steps 2–6).
- **codex anti-gaming verifier for Tasks 1–4** — status: deferred for context budget (Next Step 4).
- **Do not touch `/Users/kimhawk/orca/skills` on `feature/pin-agents-tail-banner`** — unchanged since the brief: live run, 57 dirty paths there at closeout. Work only in the worktree.
- **16 stamped handover briefs remain in `carry-forward-sources` for this repo** (2026-08-03 … 2026-09-01) — status: not consumed this session (budget); each stays in the queue until a handoff names it in `**Supersedes:**` after reading it. Not claimed here.
- **HemaSuite consumer side**: `d1e73d53` (guard) and `9e855dfa` (restore) are already on HemaSuite; nothing owed there from this lane.

## Context for Next Session

**Files touched this session:**
- `h-mad/scripts/h_mad_audit_cycle.py` (Task 1), `h-mad/scripts/h_mad_audit_gate.py` (Task 2), `h-mad/scripts/h_mad_collect_report.py` (Task 3, new), `h-mad/scripts/hmad-dispatch.sh` (Task 4)
- `h-mad/tests/test_h_mad_collect_report.py` (new), `h-mad/tests/test_h_mad_audit_gate.py`, `h-mad/tests/test_h_mad_audit_cycle.py`, `h-mad/tests/test_hmad_dispatch_collect_report.py` (new), `h-mad/tests/specs/audit_cycle_{connections,gating}.mutation.json` (root fix + re-anchor)
- `docs/01-plan/features/audit-report-docs-copy.{-brainstorm,spec,plan,impl-plan}.md` + audits v1–v12, `docs/02-design/features/audit-report-docs-copy.design.md` + audits v1–v10, `.h-mad/wires.jsonl`

**Worktree:**
- Worktree root: `/Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy` — branch: `BrightGold70/audit-report-docs-copy` (pushed, in sync at `bc1308f`)
- Main checkout: `/Users/kimhawk/orca/skills` — branch: `feature/pin-agents-tail-banner` (live run; dirty)

**Uncommitted changes:** none in the worktree (gitignored `docs/.bkit-memory.json` holds the h-mad state; `.h-mad/5c_sha_audit-report-docs-copy.txt` untracked)

**To resume:**
```bash
cd /Users/kimhawk/orca/workspaces/skills/audit-report-docs-copy
git status --short --branch            # expect clean, on BrightGold70/audit-report-docs-copy
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
python3 ~/.claude/skills/h-mad/scripts/h_mad_resume_decision.py --state docs/.bkit-memory.json --feature audit-report-docs-copy --session-id <session>   # expect halted
python3.11 -m pytest h-mad/tests/test_h_mad_collect_report.py h-mad/tests/test_h_mad_audit_gate.py h-mad/tests/test_hmad_dispatch_collect_report.py -q   # expect all green
```

**Related docs:**
- `docs/01-plan/features/audit-report-docs-copy.impl-plan.md` (v1.12 — the task contract; Task 6 table is the mutation list)
- `docs/02-design/features/audit-report-docs-copy.design.md` (v1.18, D1–D5)
- `docs/01-plan/features/audit-report-docs-copy.plan.md` (v1.11 — v1.11 line holds the AC-2.9h hand-replay transcript)
- `h-mad/SKILL.md` §"Run-context ceiling" (why this halted), §"Audit prompt assembly" (where Task 5's section goes)
