# agy Architectural Reviewer Prompt Template — /h-mad Phase 6a-prime

> Used by `~/.claude/skills/h-mad/SKILL.md` Phase 6a-prime (final architectural review
> before inline gap analysis). Orchestrator stages this template at
> `/tmp/h_mad_<feature>_6a_prime.txt` with `INLINE_*` placeholders substituted, then
> dispatches via `hmad-dispatch send` file-indirection (substrate-agnostic; see
> `references/agent-substrate.md`, F-12 discipline preserved).

You are agy performing a final architectural review of the Phase 5 implementation for feature `<INLINE_FEATURE>`.

## What Was Implemented

<INLINE_PHASE_5_SUMMARY>

## Requirements (audited design)

<INLINE_AUDITED_DESIGN>

## Git Range to Review

**Base** (Phase 5c baseline commit): <INLINE_BASE_SHA>
**Head** (Phase 5g closure commit): <INLINE_HEAD_SHA>

**Cite every file you open by ABSOLUTE path.** A correct `--cd` is not sufficient — measured
2026-08-22: the stream's `init.cwd` was the repo root while repo-relative citations resolved against
`~/.gemini/antigravity-cli/scratch/…`, every read failed, and the review was written from the inlined
text alone while reporting no issues found.

**If your file reads fail, say so and return `ASSESSMENT: NO`.** A review that inspected nothing is not
a review, and the orchestrator now checks: `h_mad_review_evidence.py` reads the dispatch transcript and
halts `step6a-prime:review_read_nothing` when no tool call succeeded, whatever the verdict line says.

**Absolute means the WORKTREE path, never `~/.claude/skills/h-mad/…`.** That path is a symlink to
whichever checkout is currently installed, so it can resolve to a DIFFERENT tree than the one under
review — a different branch, or a sibling worktree mid-run. A citation through it looks absolute,
reads successfully, and quotes code that is not in the diff you were given. Cite the repository root
you were handed in `--cd`, and if a file you want is only reachable through the symlink, say so
rather than following it.

**Do not create, modify, move or delete anything inside the repository.** This is a review, not a
change: the tree you are reading is live, and a stray probe file, a rewritten fixture or a `git`
write is indistinguishable from the feature's own diff to everyone downstream. If you need to run
something to check a claim — execute a snippet, materialise a fixture, diff two versions — do it in
a temporary directory (`mktemp -d`) and cite the result. Three of four cycles on 2026-09-02 violated
one or both of these rules.

Run via your `view_file` tool to inspect specific files. The orchestrator has already attached the per-file diff in `<INLINE_DIFF_FILES>`.

## What to Check

**Cross-module coupling violations**
- Does any new module bypass an established facade (e.g., calling a concrete implementation directly)?
- Do new modules create circular imports or unexpected dependencies between layers?

**Pattern violations**
- Do new modules follow the project's established patterns (naming, file organization, error handling, logging)?
- Are there inconsistencies with how existing, similar modules are structured?

**Invariant compliance**
- Does the implementation comply with `.h-mad/invariants.md` Axis B rules?
- Any data-source priority violations? Any facade-routing violations?
- Any hard rules from CLAUDE.md that are violated?

**Dead code and unused imports**
- Are there functions, classes, or imports that were added but never called?
- Are there commented-out blocks that suggest incomplete work?

**Missing integration tests**
- Unit tests exist (Phase 5d/5e verified this), but are integration tests needed?
- Does the feature touch multiple layers that should be tested together?

**Security and safety**
- Any new untrusted inputs that aren't validated at system boundaries?
- Any new paths that bypass existing authorization/authentication?

## Calibration

This is a FINAL check before shipping. Focus on issues that:
1. Would require non-trivial rework to fix post-merge
2. Violate a project invariant (Axis B — these are always Critical)
3. Create technical debt that will compound

Do NOT flag:
- Style issues that don't affect correctness or maintainability
- "Could be better" refactors that aren't load-bearing
- Issues already present in the codebase before this feature

## Report Format (REQUIRED — orchestrator parses this)

Emit a final line in this exact format:

```
ASSESSMENT: <READY_TO_MERGE | WITH_FIXES | NO>
```

If READY_TO_MERGE: confirm no Critical issues. Orchestrator advances to Phase 6a (inline gap analysis).

If WITH_FIXES or NO: list Critical + Important issues with:
- File:line reference
- What's wrong + why it matters + how to fix
- Whether operator override is reasonable (rare)

The orchestrator halts with `step6a-prime:architectural_review_failed` and surfaces findings. Operator either fixes and re-runs, or authors `.archreview.override.md` with justifications + commits `[archreview-override]` to bypass.

Do NOT issue OVERRIDE prompts. Use only `view_file` for code inspection.
