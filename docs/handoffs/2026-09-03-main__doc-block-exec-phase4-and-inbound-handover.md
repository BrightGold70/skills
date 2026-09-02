# Handoff — doc-block-exec through Phase 4 (not gated), predecessor backlog drained, inbound HemaSuite handover absorbed

**Date:** 2026-09-03
**Branch:** `main`
**Project:** skills (`github.com/BrightGold70/skills`)
**Supersedes:** `2026-09-03-main__post-merge-sweep-and-handover.md`, `2026-09-03-main__hemasuite-skills-lane-handover.md`

## Session Summary

Resumed from the post-merge-sweep handoff, drained all six of its restored todos (five closed, the
sixth became this session's feature), and ran `doc-block-exec` — a helper that executes an
explicitly tagged bash block out of a markdown doc — through H-MAD Phases 1–4. **Phase 4 is NOT
gated**: sixteen audit cycles across two surfaces are still returning must-fixes, and the six
outstanding ones are quoted verbatim in `docs/03-analysis/doc-block-exec.outstanding-findings.md`.
Stopped deliberately at that boundary on an operator decision rather than entering Phase 5 with
too little context to finish it. Separately, an inbound HemaSuite handover landed mid-session; its
four items are absorbed below, one of them already closed by this session's work. Three commits
pushed, `origin/main` at `e58ef3a`, working tree clean.

## Key Learnings

- **The two audit surfaces answer different questions and neither subsumes the other.** codex reads
  the tree — it caught uncited measurements, an unsatisfiable AC, a self-defeating test design and
  a missing API parameter. agy reads for internal contradiction — it caught an `extract` return-type
  conflict, an unproven reaping assumption and a Single-source-contract omission. Three consecutive
  plan cycles had agy clean while codex found a real must-fix; design cycle 1 went codex 7 + agy 5 →
  8 distinct. Gating on the union was correct every cycle.
- **`audit-cycle --passes N` dispatches agy for every pass** (`hmad-dispatch.sh:2970`), so the verb's
  default is agy+agy — the configuration this repo already records as producing a false gate. The
  codex leg has to be run alongside it by hand, per SKILL.md §"Second surface".
- **`low-evidence` on the Effort block is the signal, not the verdict.** Every agy plan pass ran at
  1–3 tool calls; the stream shows `turns=1` and a single `cat > report` heredoc with **zero reads**.
  agy reviews the inlined prompt and cannot check a claim against the tree at all. Its cleans are
  not evidence about reality; its cleans about *consistency* are.
- **A probe that measures nothing reads exactly like a negative.** Probing whether `setsid` escapes
  `killpg` returned "no escape" — because macOS ships no `setsid` binary. The portable form
  (`os.setsid()` in a Python child) confirms the escape. I nearly refuted a correct finding with a
  vacuous probe I wrote myself.
- **Four over-claims of one shape, each caught by measuring instead of arguing**: a temp cwd
  "cannot reach the repository" (it is isolation, not a sandbox); AC-5.3 banning the *substring*
  `timeout` (which rejects `TimeoutExpired` and `--shell-timeout`); "no descendant survives" (a
  group kill is not process-tree containment); and "aborts on unbound variable" (it exits 0 and
  halts — the real limit is that it can never reach `GATE: PASS`). Each time the strong,
  natural-sounding property was not the one the implementation delivers.
- **`killpg(os.getpgid(pid))` is a race, and it was in the drafted design.** Once the direct child
  exits, `getpgid` raises `ProcessLookupError` and the reap aborts, orphaning the grandchild — the
  exact bug AC-5.2 exists to prevent. `killpg(proc.pid, …)` is race-free because
  `start_new_session=True` makes pgid == pid (measured: `38030 == 38030`).
- **A carried premise's *wording* can smuggle in a requirement.** The candidate row said "run under
  `mktemp -d`" and that phrase went verbatim into spec and plan. `mktemp -d` is a shell utility, so
  both documents could be satisfied by shelling out — a new external dependency — while reading as
  consistent, because "mktemp" and "mkdtemp" look like the same word.
- **The value sweep is the weak step, not the audit.** One finding (AC-5.3's substring-vs-invocation
  ban) needed fixing on *four* surfaces and the FR-6 scope correction on *six*; a sweep grepping
  `carrying no counts` missed a surface saying `carries no counts`. Sweep by concept, never by the
  phrase you happened to write.
- **zsh does not word-split an unquoted variable**, so `for v in "a b c"; do set -- $v` silently
  passes the whole string as `$1`. It broke a three-way version bump and a two-way report collector
  in this session alone. `h_mad_version_history.py` refused with `UNREADABLE` rather than writing
  garbage — but the *following* commands still ran, so two docs briefly carried version-history
  entries describing edits that had not landed.

## Next Steps

1. **Resume `doc-block-exec` at the Phase 4 audit** — `/h-mad "doc-block-exec"` routes to
   `resume_manual` at `current_phase=4`. Work the six findings in
   `docs/03-analysis/doc-block-exec.outstanding-findings.md` first; they are quoted verbatim so
   nothing needs re-deriving.
2. **Shrink the design audit prompt before the next design cycle** — cycle 5 assembled past the
   confirmed-answered frontier (`size_status=unverified`, agy returned `must=9`, not comparable
   with earlier passes). Inline only the spec's `## Functional Requirements` per SKILL.md
   §"Audit prompt assembly" step 5.5.
3. **Re-locate the two `hmad-dispatch.sh` wrapper bugs** — the inbound brief cites `:3619` and
   `:3597`; re-checked this session and **both have moved** (3597 is blank, 3619 is a comment).
   The brief predicted exactly this. Find them by symptom: a dispatch that logs `codex exec rc=0`
   and then exits 2 or 127 while its report lands.
4. **Correct the h-mad revert-sequence invariant** — `git add -N` + `git stash push` no-ops on a
   tree where the entry is not up to date (`Entry not uptodate`), and the prescribed
   `git diff --quiet` guard then prints `revert landed` anyway: a guard that fails OPEN. The form
   that works is explicit `mv` aside → assert absent → run → `mv` back. This repo's own store
   already carries `committed-file-revert-helper` describing the same trap.
5. **Decide the 101 classified skill-candidate rows** — 29 TOOL-CANDIDATE, 72 PRACTICE, annotated
   in place in HemaSuite's three stores. The eight named in the brief as "shortest path from
   classified to built" are the place to start. Re-run the census before trusting any number.
6. **[suggested]** Consider whether `audit-cycle` should grow a second-surface mode — running the
   codex leg by hand alongside every cycle was the single most repeated manual step this session,
   and the row `no --report-file or dual-surface mode in h_mad_audit_cycle.py` is already open in
   the inbound brief's list.

## Open / Blocked Items

- **`doc-block-exec` Phase 4 not gated** — status: in progress, blocked on six audit findings.
  Both surfaces still FAIL (plan cycle 11: codex `must=2 should=2`, agy PASS; design cycle 5:
  codex `must=4 should=1`, agy `must=9` at `size_status=unverified`). Findings quoted verbatim in
  `docs/03-analysis/doc-block-exec.outstanding-findings.md`. State: `current_phase=4`,
  `last_completed_phase=3`, claimed by session `023f6eeb-e188-431b-9dfb-785e80736304` —
  **the claim was NOT released**, deliberately, because this is a resume of the same lane rather
  than a handover; a fresh session takes it with a plain `--claim` once the two-hour staleness
  window passes, and `h_mad_resume_decision.py` will say so.
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`
- **Two `hmad-dispatch.sh` wrapper bugs** — status: open, inherited.
  **Handover-From:** HemaSuite · main · session `cfc79129-d676-4858-9792-3069dbdd2283`.
  `repo: /Users/kimhawk/orca/skills · branch: main · worktree: /Users/kimhawk/orca/skills`.
  Premise partially falsified this session: the cited line numbers have moved (Next Step 3).
- **The h-mad revert-sequence invariant is wrong as documented** — status: open, inherited, same
  origin and location as above. Not re-probed this session.
- **101 classified skill-candidate rows awaiting an authoring-or-decline decision** — status: open,
  inherited, same origin. The rows live in HemaSuite's three stores
  (`/Users/kimhawk/orca/HemaSuite/docs/skill-candidates.md` and the two sub-project stores);
  the *decision* is this repo's. Census at handover: 443 candidates, OPEN 189, verdict-less 0 —
  **do not carry that number, re-run it.**
- **4 leaked `exec-pane agy` PIDs — CLOSED this session.** The inbound brief's item 3. Reaped as
  todo #28 after confirming each was a `sleep 1` poll loop with a deleted pytest cwd; re-verified
  gone while writing this handoff (`ps -p` returns nothing for all four). The brief's more
  interesting half stands and is not closed: *a pytest run leaks panes at all* — no row filed.
- **`h-mad/tests/docsections.py` is in `doc-block-exec`'s scope** — status: planned, not started.
  It will drop its duplicate `_fence_aware_end` and import the authoritative bounder. Flagged
  because it is a file outside the obvious blast radius of a new helper.
- **55 untracked `.done` markers** — status: deliberate, unchanged since 2026-09-01. Do not commit.
- **`docs/skill-candidates.md` open rows** — status: open, unchanged since the predecessor. This
  session's scout has not run yet (it runs after this doc). Re-run the census; never carry a count.
- **Predecessor items, all CLOSED this session:** remote branch `feature/pin-agents-tail-banner`
  deleted (verified merged at `bf1c851` first); the redundant HemaSuite `refs/handoffs/…` ref
  dropped (after diffing it against `main` to prove the ref copy was a strict subset); the four
  orphan PIDs reaped; `MEMORY.md` compacted 23082 → 18869 bytes with all 167 pointers intact and
  five pre-existing markup corruptions repaired; the census `__main__` guard shipped (`6bcdd72`).

## Context for Next Session

**Files touched this session:**
- `handoff/scripts/skill_candidates_census.py` — `main(argv)` + `__main__` guard; output byte-identical
- `handoff/tests/test_skill_candidates_census.py` — +4 tests
- `handoff/tests/mutation-specs/census_registry.json` — re-rooted 18 `test` keys, +3 mutations
- `handoff/references/automation-scout.md` — the import-API paragraph
- `docs/01-plan/features/doc-block-exec.{spec,plan}.md`, `docs/02-design/features/doc-block-exec.design.md`
- `docs/01-plan/features/doc-block-exec-brainstorm.md`, 40 audit reports across both surfaces
- `docs/03-analysis/doc-block-exec.outstanding-findings.md`
- `docs/handoffs/2026-09-03-main__hemasuite-skills-lane-handover.md` — stamped `**Taken-Over-By:**`
- `~/.claude/projects/-Users-kimhawk-orca-skills/memory/MEMORY.md` — user-global, not committed

**Uncommitted changes:** none but the 55 deliberate `.done` markers.

**To resume:**
```bash
cd /Users/kimhawk/orca/skills
export PATH="$HOME/.claude/skills/h-mad/bin:$PATH"
git status --short --branch          # expect: main...origin/main, clean bar 55 ?? .done
/h-mad "doc-block-exec"              # -> resume_manual at phase 4
cat docs/03-analysis/doc-block-exec.outstanding-findings.md
python3.11 -m pytest -q              # expect 2747 passed; run ALONE
```

**Related docs:**
- `docs/03-analysis/doc-block-exec.outstanding-findings.md` — the six blocking findings, verbatim
- `docs/01-plan/features/doc-block-exec.spec.md` — 43 ACs over 6 FRs, five measured probes cited
- `docs/handoffs/2026-09-03-main__hemasuite-skills-lane-handover.md` — the inbound brief, now stamped
- `h-mad/SKILL.md` §"Second surface — the codex leg" — the manual codex leg every audit cycle needs
