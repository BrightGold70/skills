# Handoff — doc-block-exec: Task 4 code COMPLETE and pushed; the two 5e gates are the whole remaining debt

**Date:** 2026-09-07
**Branch:** `feature/doc-block-exec` — clean, `0 behind / 0 ahead`, HEAD `ddd4d12`
**Project:** skills (`/Users/kimhawk/orca/skills`)
**Supersedes:** 2026-09-06-feature-doc-block-exec__task4-green-91-rows.md (branch predecessor, written hours earlier and already reconciled in place through `ddd4d12`), 2026-09-05-main__audit-loop-never-runs-repo-suite.md and 2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md (taken over 09-05; re-emitted below, not re-read)

> **Delta doc on purpose.** The predecessor is from the same working session and was corrected in
> place after the push, so it is accurate, not stale — read it for the full narrative, the seven
> orchestrator measurement errors, and the per-figure evidence table. This doc exists because the
> date rolled and because **everything the predecessor listed as in-flight has now closed**, which
> changes what the next session should pick up first.

## Session Summary

Everything the predecessor left running finished cleanly. The 91-row harness returned
`ALL_CAUGHT mutations=91 caught=91 survived=0`, the working tree restored, restoration was verified
by executing the shipped entry point, the claim was released, and all twelve commits are pushed.
**Task 4's code is done; Task 4's 5e is not.** The two gates that prove the tests are real — the
revert test and the independent anti-gaming verification — were never run, and that is now the
entire remaining debt on this task.

## Key Learnings

- **A running mutation harness and the pre-push anchor hook are mutually exclusive.** The hook
  sweeps anchors over the WORKING TREE; the harness deliberately mutates the working tree. Run
  concurrently they produce a guaranteed false `ANCHORS_DRIFTED` — measured: `drifted=2` on
  `drain-unbounded` and `drain-oserror-unmapped`, neither of which had drifted. The hook was right
  to block. **The tempting response, `--no-verify`, would push a tree whose guards are genuinely
  unverified at that instant.** Wait for the harness, confirm restoration, push then.
- **`module_from_spec` without `sys.modules` registration is not a broken module.** Probing the
  restored helper that way raises `AttributeError: 'NoneType' object has no attribute '__dict__'`
  from inside `@dataclass`, because dataclasses resolves `sys.modules.get(cls.__module__)`. That is
  the probe's bug. It is exactly the shape that panics someone checking a mutation harness's
  cleanup, which is when you are least inclined to doubt your own instrument.
- **Writing a claim before its action succeeds is the same defect as a carried measurement.** The
  predecessor was edited to say "pushed at closeout" and then the push was attempted and blocked.
  Corrected at `81c0f36`. Seven of this session's errors were measurements; this was the eighth and
  it was an action, which suggests the rule generalises past numbers.

## Next Steps

1. **The 5e revert test for Task 4 — the top item, never run.** Production is committed, so
   `git stash push -u` is not the destructive case §5e warns about, but follow it exactly: revert
   production only, confirm the RED split returns EXACTLY `62 failed, 98 passed`, restore, confirm
   green returns. **Assert the revert LANDED with an existence check** — `git diff --quiet` is
   trivially clean for an untracked path and structurally cannot see this failure. Verify the
   restore by EXECUTING the symbol, never by grepping the source.
2. **The independent anti-gaming verification** — `references/codex-verifier-prompt.md`. Module
   count, test-discrimination audit, quote the source line for each pinned property, full suite vs
   the reference, every reported count cross-checked a second way. Never dispatched.
3. **Task 5**, then **5f**: `h_mad_baseline_sha.py --branch feature/doc-block-exec --trunk main`
   reports `UNVERIFIED reason=no_impl_plan candidate=0885152` **by design**; `0885152` IS the 5c sha.
   Then `h_mad_wire_registry.py verify --base 0885152 --rootdir . --testpath h-mad/tests`. Task 5
   writes `doc_block_exec_wire.json`, absent until then — the design labels that absence as
   schedule, not defect.
4. **5g** — the D3 provenance bump lands here and nowhere earlier; `phase = null` ONLY after 5f.
   State still reads `phase: step5`, correctly.
5. **Claim before touching anything** — `owner: None` as of this writing.
6. **Run the automation scout EARLY** (see Open Items) — it is now FOUR consecutive skips.

## Open / Blocked Items

**doc-block-exec — `repo: /Users/kimhawk/orca/skills · branch: feature/doc-block-exec · worktree: /Users/kimhawk/orca/skills`**

- **5e INCOMPLETE — the only thing standing between Task 4 and done.** Next Steps 1 and 2. The code
  and tests are committed and green; the gates that prove the tests discriminate are not run.
- **CLOSED since the predecessor**, so the next session does not re-check them: the 91-row harness
  (`ALL_CAUGHT 91/91 survived=0`, orchestrator's own run) · tree restoration (verified by executing
  `--help` → 0, `--nope` → `DOCBLOCK: BAD_ARGS`, `VERDICT_TABLE` = 23 heads) · the claim (released)
  · the push (`ddd4d12`, `0/0`) · the 91st mutation row (`MATRIX-NOT-ON-DISK = []`).
- **D3 — SETTLED at remedy 3; obligation live through 5g.** `assert 19 <= 12`. Full suite at the
  GREEN tree `1 failed, 2782 passed`; impl-plan `PRECHECK: FAIL issues=19` (8 PINDRIFT + 11
  PLACEHOLDER), unmoved by this session's work.
- **FOUR consecutive handoffs have now skipped the automation scout** — context budget each time,
  this one at 83%. It is the only writer of `docs/skill-candidates.md`; 4 of 5 open rows described
  already-shipped work the last time anyone looked. Task #49. **Run it first next session.**
- **#146 — two orchestrator errors in §D11, both bracket-corrected**: "30 of the 42 specs" (it is
  41) and "in any argv position" (false; the axis is *recognised as an option* — `-h` works,
  `d.md --heading --help` is a VALUE, `-- --help` is the positional). Spec ships the correct form.
- **#145 AC-1.8 spec debt** — over-broad universal the design's codex leg filed as false; reported
  and unrouted since spec v1.63, now four rounds. Route it into the next spec dispatch.
- **#142 D2 residual** — nothing detects a parked `.json.pending` spec never moved back.
- **#126 heartbeat that does not beat** — OPEN, diagnosed to `h_mad_state_write.py:286` (the only
  heartbeat writer), not implemented.
- **#129 partition-parts** · **#105 self-counting screens** — owed to
  `h-mad/references/measurement-discipline.md`. This session added two worked examples: the
  spelled-out-total trap ("Ninety-one rows" is invisible to `\b91\b`) and the wrong-path zero.
- **#100 taken-over H1–H9 brief** — unchanged, not started. `repo: /Users/kimhawk/orca/skills ·
  branch: main · worktree: none`. **Handover-From:** HemaSuite · main · session cab14393.
- **#91 inherited** — "Phase 3–4 audit cycle never runs the project test suite", a skill defect.
  **Handover-From:** HemaSuite · main · session 9d8394fb. Unchanged.
- **#111 tooling worktree** — `../skills-hmad-gate @ feature/hmad-class-scored-gate` still present;
  removal is the operator's: `git worktree remove ../skills-hmad-gate && git branch -d feature/hmad-class-scored-gate`.
- **#112 · #48 · #42 · #77 · #27 · #20 · #9/#5/#8 · #7 (closes with 5e) · #143** — unchanged.
- **Evidence-gate corpus** at `~/.h-mad-corpora/evidence-gate/` — outside the repo, not backed up.
- **HemaSuite skill-candidate row** — ownership already moved; brief
  `HemaSuite/docs/handoffs/2026-09-04-main__wrapper-rc-row-is-probably-a-duplicate.md`. Not re-checked.
- **Codex quota** — did not bind; five dispatches all completed. `codex_status: available`.

**Related lanes, not owned here:** `exec agy` lingers after its `result` event (agy not dispatched
this session) · HemaSuite `#18 gateway-consolidation`, HALTED by the operator.

## In-Flight Processes

**None.** The predecessor's one entry — the 91-row harness — completed with
`MUTATION: ALL_CAUGHT mutations=91 caught=91 survived=0 refused=0 unreadable=0` and restored the
tree. Recorded as closed rather than deleted, so a reader can tell a finished job from one that was
never started.

## Context for Next Session

**Files touched since the predecessor:** only the predecessor handoff itself (reconciled) and
`docs/learnings.md`.

**Uncommitted changes:** none, besides the 88 untracked `.done` markers (do not commit).

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout feature/doc-block-exec          # ddd4d12, clean, 0/0
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"; hmad-dispatch env
python3 ~/.claude/skills/h-mad/scripts/h_mad_state_write.py docs/.bkit-memory.json \
  --feature doc-block-exec --claim <your-session-id>
# then Next Step 1: the 5e revert test
```

**Related docs:**
- The predecessor — full narrative, the seven measurement errors, the per-figure evidence table
- `docs/03-analysis/doc-block-exec.5d-decisions.md` — §D10 (merge), §D11/§D12 (settled; D11 carries
  two bracketed corrections), §D13 (the 91st row, settled on killer reachability)
