# Handoff — Audit-prompt assembler + Orca agent-resolution hardening

**Date:** 2026-07-22
**Branch:** main
**Project:** BrightGold70/skills (`/Users/kimhawk/orca/skills`)

## Session Summary

Started from a one-line report that `<INLINE_BASE_INVARIANTS>` was showing up unfilled in dispatched audit prompts. Root cause was broader than the symptom: slot tokens were written **bracketed in prose** inside files that assembly concatenates, so a literal whole-file `replace()` could not tell a slot from a mention of one — every prompt carried both rubrics twice and still displayed a raw token. Fixing that exposed a second convention gap (three spellings of "applies only to some audit types", never resolved consistently), which led to shipping `h_mad_assemble_audit.py` so assembly stops being prose an orchestrator executes by hand. Separately, the user updated Orca; re-checking the Codex identity issue found the failure mode had **moved and got worse** — a tab-title change made an *agy* pane match `^codex`, one closed pane away from silently handing Codex's work to the wrong model. Six commits, all pushed; suite 431 → 454 passing. Everything identified is fixed except the upstream Orca gap (#9870), which is filed.

## Key Learnings

- **Orca `.title` is the pane program's OSC title if it emits one, otherwise the enclosing TAB's title** — and a tab title is shared by every leaf in that tab, so it names a tab, not a pane. Codex emits no OSC title, so *any* `.title` matching `codex` is inherited and carries zero identity information. agy does emit one. This single fact explains the whole Codex-identity class and is why title matching is disabled for Codex outright rather than merely distrusted.
- **Removing a broken matcher can expose a worse bug underneath it.** Disabling Codex's title pass made the preview pass run for the first time — and its signature included the bare token `codex`, which any pane *discussing* dispatch prints. The coordinator's own pane resolved as Codex and would have dispatched to itself. An existing test caught it. Signatures must be strings the program emits, never words a pane can render.
- **`set -euo pipefail` makes `cmd; rc=$?` abort the script** the moment `cmd` returns non-zero — exactly the case a liveness check exists to report. `if` conditions suppress `set -e`; bare sequences do not. Symptom was `verify` exiting 1 with *empty stderr*. Use `rc=0; cmd || rc=$?`.
- **A verification needle that is authored by the project cannot be hardcoded.** The preflight's duplication grep pinned `H-MAD Project Invariants — Axis B`; HemaSuite's file opens `# HPW Project Axis B Invariants`, so the check reported `0` — which reads as "the project layer was never inlined", the opposite of the truth. Derive the needle from `head -1` of the file actually inlined.
- **Design docs live in `docs/02-design/features/`, not beside spec/plan/impl-plan.** The first assembler assumed one directory and could not assemble a single real design or impl-plan audit — while its unit tests passed, because the fixture colocated all four docs. A fixture that does not mirror the real layout will certify a tool that cannot run.
- **A degraded prompt does not imply a false verdict.** The `clinical-abbreviation-hygiene` plan audit gated clean from a prompt carrying duplicate rubrics and a raw placeholder; re-running it through the fixed pipeline reproduced the same verdict with *more* evidence. Suspicion was correct to raise, wrong to assume.
- **h-mad's own base invariant on gate signalling applies to h-mad's own scripts**: a verdict the orchestrator consumes goes to stdout with exit 0; non-zero is reserved for operational errors. The assembler emits `ASSEMBLE: PASS` / `ASSEMBLE: HALT` and exits 0 for both.
- **Re-running a repair script with the same `--backup-dir` overwrites the originals with the previous pass's output.** The true as-dispatched prompts for 69 files are gone; the surviving analysis rests on a survey table captured before the first pass. Also: a freshness guard keyed on file mtime is useless after your own pass rewrote every file — read age from the backup copy, which `copy2` preserves.

## Next Steps

1. Run one full `/h-mad` audit cycle end-to-end through the shipped assembler — assembly is smoke-tested for all three phases but only the plan recheck was actually dispatched to a reviewer. `python3 h-mad/scripts/h_mad_assemble_audit.py --feature <f> --phase design --project-root <root> --report-file "$RP"` then `hmad-dispatch send agy <staged>`.
2. Watch [stablyai/orca#9870](https://github.com/stablyai/orca/issues/9870) for a per-leaf identity field (`titleSource`, launch argv, or agent id). When it lands, replace the heuristics in `_orca_find` — `h-mad/scripts/hmad-dispatch.sh:131-275` — with the real field; the tab-sharing and rival-banner rules exist only because that field does not.
3. Confirm orchestrators actually act on the new preflight signals: `env` now prints `STALE` and `CONFLICT:` lines, and `h_mad_assemble_audit.py` prints `ASSEMBLE: HALT`. These are stdout tokens, so they are only load-bearing if the Phase-5 checklist is followed — `h-mad/SKILL.md` §"Audit prompt assembly" step 7.2.
4. Re-pin agents before the next dispatch-heavy run: `hmad-dispatch launch <agent>` (preferred) or `pin`, then `hmad-dispatch env` and confirm no `STALE`/`CONFLICT`. agy currently resolves UNRESOLVED here because no agy pane is running.

## Open / Blocked Items

- **Orca per-terminal identity (#9870)** — status: blocked on upstream. Every resolution rule shipped this session is a workaround for the missing field. Follow-up comment filed with repro, field inventory, and three concrete API options.
- **agy auto-detect resolves UNRESOLVED in this repo** — status: expected, not a defect. No agy pane is running; it resolves normally when one is.
- **Original as-dispatched copies of the 69 staged audit prompts** — status: lost (pass-2 backup overwrote pass-1). Historical only; the regenerated prompts are clean and idempotent.
- **Plan backlog carries no `status:` frontmatter** — status: deferred. `docs/01-plan/features/*.plan.md` has no machine-readable state, so the handoff scout can surface no backlog signal from it. Mostly HemaSuite-facing product plans, not this repo's work.

## Context for Next Session

**Files touched this session:**
- `h-mad/SKILL.md`
- `h-mad/audit-prompt.template.md`
- `h-mad/invariants.base.md`
- `h-mad/scripts/h_mad_assemble_audit.py` (new)
- `h-mad/scripts/hmad-dispatch.sh`
- `h-mad/scripts/h_mad_report_wait.py`
- `h-mad/tests/test_h_mad_assemble_audit.py` (new)
- `h-mad/tests/test_h_mad_audit_conditionals.py` (new)
- `h-mad/tests/test_h_mad_invariants_layering.py`
- `h-mad/tests/test_hmad_dispatch.py`

**Commits (all pushed to `origin/main`):**
- `5af37bb` stop audit-prompt slot tokens leaking and double-inlining rubrics
- `4a7bb51` one resolvable convention for audit-prompt applicability markers
- `7d5e698` derive preflight duplication needle from the invariants file itself
- `3f8ae83` stop Codex resolving to the wrong agent; ship the audit assembler
- `912b93a` treat a pin as intent, not state — check liveness where it is cheap
- `e4bc4e4` close the remaining agent-resolution holes

**Uncommitted changes:** none (clean tree at `e4bc4e4`).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main
pytest h-mad/tests/ -q            # expect 454 passed
hmad-dispatch env                 # check substrate + STALE/CONFLICT lines
```

**Related docs:**
- `h-mad/SKILL.md` §"Audit prompt assembly" — the assembler is now step 0; the manual steps below it are the debugging reference
- `h-mad/audit-prompt.template.md` — `{{ONLY:…}}` convention lives in the stripped orchestrator note
- [stablyai/orca#9870](https://github.com/stablyai/orca/issues/9870) — upstream identity gap + this session's follow-up comment
- Auto-memory `project_orca_agent_identity.md` — updated with the post-update behaviour and the mitigation commit
