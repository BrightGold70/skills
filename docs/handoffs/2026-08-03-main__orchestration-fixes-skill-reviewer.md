# Handoff — Orchestration wrapper fixes, the agy skill-reviewer, and a scout that reconciles

**Date:** 2026-08-03
**Branch:** main
**Project:** /Users/kimhawk/orca/skills (symlinked as `~/.claude/skills/h-mad` and `~/.claude/skills/handoff`)

## Session Summary

Resumed from `2026-08-03-main__takeover-and-hemasuite-handover.md` and worked its two `[suggested]` Next Steps to completion. An agy review of the vendor-managed `orchestration` skill produced 3 confirmed `[OURS]` defects out of 10 findings; probing for a response field during the fix uncovered a fourth and larger one — **orchestration mode was dead at step one**, because the wrapper never bound a Run. All four shipped, plus the hazard-command sweep, the `agy-skill-reviewer` template promoted from the candidate backlog, and an automation scout that now reconciles candidate rows instead of only appending. `main` @ `b2aaf6c`, clean, in sync, 1049 + 48 green. Nothing is blocked.

## Key Learnings

- **The vendor guide is not the command surface — `--help` is.** Six flags were checked this session; four "undocumented flag" findings (`--task-title`, `--return-preamble`, `--base-branch`, `--project`) were false, every one a real flag the 388-line guide simply omits. Two of those four were mine, generated *because my review prompt named the guide as ground truth*. The prompt causes the failure class. Conversely `--workspace` really is absent from `worktree create` while present on `automations create`, so the answer is per-command and only `--help` settles it.
- **A clean auto-merge says nothing about whether the union is green.** `merge-tree` reported no conflict, `git merge` produced no markers, and the merged suite still failed: a coverage guard shipped on one branch fired on a doc that exists only on the other. Neither branch could fail alone. The integration-probe branch is what caught it — the discipline earns its keep precisely where textual merge analysis is blind.
- **A guard scoped to one site is a weak test, and it hides exactly what it was written for.** The `git add -N` fix landed at 1 of 4 sites that name the `git stash` hazard, and the existing test — which asserts one literal at one site — stayed green through all three gaps. Worst was `codex-verifier-prompt.md`, handed to an independent Codex agent that cannot see `SKILL.md`: it gave the detection and never the prevention.
- **`orchestration check` replays its oldest unacknowledged Delivery until `--ack`.** So a single un-acked call is not a wait: in a fanout, modules 2..N got module 1's batch back immediately, the taskId filter missed, and `jq '.[0] // empty'` **exited 0** — a worker that never reported read as a successful await.
- **A `no` verdict can still name an upgrade.** The scout's verdict answers "is this a new skill?", not "should an existing skill change?". One row was filed `candidate: no` with the reason *"belongs in the handoff skill's READ reconciliation"* — naming its own insertion point, which nobody routed, for a day.
- **The scout was append-only while the file it writes demands reconciliation.** `docs/skill-candidates.md` says its status "is only useful if it is current"; the scout is its only writer and never flipped a row. Result: 5 open rows, 4 describing already-shipped work. The inverse hazard shape — a rule stated in an artifact that never reaches the step obliged to act on it.
- **Dogfooding a bundled prompt found two defects in the prompt itself.** A slot mentioned *bracketed* in prose (`<INLINE_*>`) survives substitution and reaches the agent as a raw token, which SKILL.md 7.2 makes a mandatory pre-dispatch halt — present in all five reference prompts. And the reviewer, invited to run `--help` probes but never bounded, probed a *mutating* verb and wrote a junk entry into the project's permanent learnings file.
- **`--setup inherit` is not a bypass, and the review's premise was wrong.** It follows the repo's setup policy, and every repo on this host is `run-by-default`, so nothing was broken. The fix shipped anyway for a different reason — it made the guarantee depend on a per-repo setting the wrapper does not control.

## Next Steps

1. **Live e2e the full orchestration flow now that a Run binds** — `task-create → dispatch → await → gate-create/gate-wait` against a real worker. `task-create` is live-verified (`task_db36a747051a`); the ack loop, gate path, and fanout are stub-tested only. Start from `h-mad/references/orchestration-mode.md` §"the normal flow".
2. **Reproduce `run_required` from an unbound terminal** — this session's pane is now bound to `run_1632386a175a`, so the pre-fix failure cannot be re-observed here. Use a fresh Orca pane (or a second worktree) and run `orca orchestration task-list --json` before any `hmad-dispatch task-create`. This is the one half of the Run-binding fix with no live "before" evidence.
3. **Promote `orca-verb-live-reconcile`** — the closeout scout raised it to rec 3 / `candidate: yes`, which clears the file's own promotion bar (`docs/skill-candidates.md`, summary table). It is the only open row. Deliberately not promoted in the same breath as the scout that raised it. The kernel: after shipping an orca-wrapping verb, run a live create→list→remove against the real runtime — this session that probe, not the review, is what surfaced `run_required`.
4. **Decide on `worker-start` vs raw `dispatch`** — `orch_guide.txt:180` calls `worker-start` "the normal supervised path" and it composes worktree+terminal+readiness+dispatch, while `h-mad/scripts/hmad-dispatch.sh:_cmd_dispatch` uses the older primitive. Noted during the review, never actioned; not a defect, a possible simplification.

## Open / Blocked Items

- **Orchestration live e2e beyond `task-create`** — status: owed, not blocked. Everything downstream of task-create passed stub tests + mutation only. See Next Step 1.
- **`run_required` "before" evidence** — status: unreproducible from this session (the pane is bound). Not a defect; a verification gap. See Next Step 2.
- **Nothing parked outside this repo.** No foreign-worktree items, so no HANDOVER was needed this session. The HemaSuite Task 5 item from the previous handoff remains that lane's — it closed out on its own (`b94e0317`, `536f67da`); do not re-adopt.

## Context for Next Session

**Files touched this session (all merged to `main`):**
- `h-mad/scripts/hmad-dispatch.sh` — `_run_ensure`/`_run_bound` + `run-ensure` verb + `env` Run line; `_cmd_await` ack loop; `_cmd_worktree_create` `--workspace` removal and `--setup` default
- `h-mad/references/agy-skill-reviewer-prompt.md` — **new**; the third reviewer (skill, not feature)
- `h-mad/SKILL.md` — §"Reviewing a skill with agy", reference index, stash-hazard fix
- `h-mad/references/{codex-verifier,failure-recovery,agy-spec-reviewer,agy-architectural-reviewer,codex-implementer}-prompt.md` — `git add -N` at every hazard site; bracketed-wildcard fix
- `handoff/SKILL.md` — READ Step 3 "PR state"; default-branch resolution; INDEX.md stray-line `awk`; LEARN Step 4 example; scout pointer
- `handoff/references/automation-scout.md` — reconcile-before-append
- `docs/skill-candidates.md` — 6 rows reconciled + header note
- Tests: `h-mad/tests/test_h_mad_skill_reviewer_prompt.py` (**new**), `test_hmad_dispatch.py`, `test_h_mad_agy_review_fixes.py`, `h-mad/tests/stubs/orca`, `handoff/scripts/test_handover_docs.py`

**Uncommitted changes:** none. `main` @ `b2aaf6c`, in sync with `origin/main`.

**Branches:** `fix/orchestration-run-binding-and-hazard-docs` and `feat/agy-skill-review-scaffold` and `fix/scout-reconciles-candidates` are all merged into `main` and safe to delete.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
git checkout main                                                     # @ b2aaf6c
/opt/anaconda3/bin/python3 -m pytest h-mad/tests handoff/scripts -q   # 1049 expected

# the coupled consumer suite — the symlink means this repo's HEAD is what it runs
cd /Users/kimhawk/orca/HemaSuite/hematology-paper-writer
/opt/anaconda3/bin/python3 -m pytest tests/test_h_mad_*.py -q         # 48 expected
```
A bare `python3` is homebrew 3.14 with no pytest — use `/opt/anaconda3/bin/python3` for tests. The h-mad/handoff scripts are stdlib-only and run fine under bare `python3` (that constraint is tested).

**Reviewing a skill with agy (the transport, four runs, now bundled):**
```bash
# fill the INLINE_* slots of h-mad/references/agy-skill-reviewer-prompt.md, then:
bash ~/.claude/skills/h-mad/scripts/hmad-dispatch.sh exec agy <prompt-file> \
  --cd <repo> --out <report.md> --log <run.log> --timeout 900
```
`exec` is pane-independent, so a `PREFLIGHT: FAIL` from a stale pin does not block it — it needs only `agy` on PATH. **Verify every finding against the file before acting**: 8 findings across four reviews did not survive that check.

**The bundled mutation harness (use it; do not hand-roll one):**
```bash
python3 h-mad/scripts/h_mad_mutation_harness.py <spec.json>
# spec: {root, command:[argv], mutations:[{name,file,find,replace}]}
```

**Related docs:**
- Prior handoff (same day): `docs/handoffs/2026-08-03-main__takeover-and-hemasuite-handover.md`
- Orchestration protocol: `h-mad/references/orchestration-mode.md`
- The version-matched Orca guide (ground truth for the command surface): `orca skills get orchestration`
- The four agy reports this session were scratchpad-only and **not** persisted; their adjudications live in the PR/commit bodies for `9b493e4`, `509c4fa`, `d41ccef`, `a27118e`.
