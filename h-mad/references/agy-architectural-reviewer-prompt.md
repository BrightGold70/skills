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

## What each verdict means

If READY_TO_MERGE: confirm no Critical issues. Orchestrator advances to Phase 6a (inline gap analysis).

If WITH_FIXES or NO: list Critical + Important issues with:
- File:line reference
- What's wrong + why it matters + how to fix
- Whether operator override is reasonable (rare)

The orchestrator halts with `step6a-prime:architectural_review_failed` and surfaces findings. Operator either fixes and re-runs, or authors `.archreview.override.md` with justifications + commits `[archreview-override]` to bypass.

Do NOT issue OVERRIDE prompts. Use `view_file` for code inspection.

**One exception, and it is not optional:** you must also WRITE your report file
(next section) with `run_command`. That is the only write you may make. An earlier
revision of this prompt said "use only `view_file`" and then asked for the file in
the next breath; the reviewer obeyed the restriction, wrote nothing, and its review
was discarded for the fifth time in a row.

## Where to write your report

Write your full report to this file with `run_command`, creating it if it does
not exist:

<INLINE_REPORT_FILE>

Write it there FIRST, before you compose your reply. The file is the channel the
orchestrator prefers; your reply is the fallback. The verdict line goes in BOTH —
the file's last line and your reply's last line, identical, character for character.

This exists because your reply is the least reliable part of this exchange. Four
dispatches of this prompt read the tree, produced substantive reviews, and were
discarded whole because the last line of the reply did not carry the verdict. The
review work was done and unrecoverable. A file you wrote cannot be lost that way.

Writing the file is not a substitute for the verdict line in your reply, and a file
you create but leave empty is treated as if it were never written.

## Report Format (REQUIRED — orchestrator parses this)

Write your findings first. Then the **very last line of your reply** must be the verdict line,
alone on its own line, with nothing after it — no closing sentence, no signature, no blank
summary, no code fence around it. The orchestrator reads the LAST line that begins with
`ASSESSMENT:` and refuses a reply that has none; a reply whose verdict is buried mid-text, or that
ends with anything else, is re-dispatched at the cost of a full cycle. Five real dispatches
omitted this line entirely while writing fluent prose above it. Two of them — 2026-09-09, the
same prompt twice — instead opened their report with `**Assessment**: YES, with minor
non-blocking drift`. That is not a verdict this can read: `YES` is not one of the three words,
it was not alone on its line, it was not last, and it carried a qualifier. Both reviews were
discarded whole, having read 11 and 19 files respectively.

Your reply ends with exactly one of the three lines below, copied character for character.
Do not bold it, do not fence it, do not prefix it with `#`/`##`/`###`, do not add a qualifier
after the word, and do not write your own wording of it — these are literals, not a template to
fill in. Nothing follows it.

**The three words are a CLOSED set.** Any other word is discarded, and the whole review with it,
however well-argued. Real replies to this prompt that were thrown away for the word alone:
`YES`, twice; and `DRIFTED`, once, written under a markdown heading marker. That last reply
borrowed its word from a DIFFERENT h-mad prompt — the 5e spec reviewer, whose contract is
`VERDICT: COMPLIANT | DRIFT` and is not this one. `DRIFT`, `DRIFTED`, `COMPLIANT`, `YES`,
`NO_GO` and `PASS` are all wrong here. If your finding is "it works, but something has to be
fixed first", the word is `WITH_FIXES` — which is what every one of those refused replies was
reaching for.

ASSESSMENT: READY_TO_MERGE
ASSESSMENT: WITH_FIXES
ASSESSMENT: NO
