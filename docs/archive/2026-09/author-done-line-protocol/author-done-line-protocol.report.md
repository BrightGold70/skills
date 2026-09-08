# Report — author-done-line-protocol

**Date:** 2026-09-08 · **Branch:** `BrightGold70/author-done-line-protocol` (merged to `main`)
**Base:** `6f00f8c` · **Head:** `b6a6033` (code) · `d252942` (brief) · **Substrate:** orca

## Executive Summary

An author agent's `DONE` line now carries the artifact's path, line count and sha256, and the
orchestrator refuses a mismatch before it reads the report or commits the file. The protocol
already existed and already worked — it lived only in hand-written dispatch prompts, so the next
orchestrator to skip it would have skipped it silently.

### Value Delivered

| perspective | delivered |
|---|---|
| **Problem** | A subagent's "stopped writing" is an *instant*, not a state. The orchestrator's own post-DONE dispatch — a `SendMessage`, a successor spawned on `Prompt is too long` — makes the author resume from its transcript and write again. The completion notification therefore proves nothing about the bytes on disk, and the orchestrator was committing artifacts on that evidence. |
| **Solution** | The author computes a digest over the finished artifact with a pinned command; the orchestrator re-derives it with the same command and refuses on mismatch, gated `\|\| exit 1`. Six documents carry the contract; one script enforces it. |
| **Function / UX effect** | An h-mad phase document can no longer be committed on the strength of a message. A wrong sha halts with both values and a diagnosis; a wrong *path* is caught by `--expect-path`, which is the failure the digest alone cannot see. |
| **Core value** | Echoing a sha into the log is not a gate. The gate is the comparison, and it is now the only thing standing between an author's claim and a commit. |

## PDCA provenance — read this before trusting the phase labels

**This feature has no bkit PDCA chain, and none was fabricated for this report.** There is no
`docs/00-pm/`, `01-plan`, `02-design` or `03-analysis` document for it, and `.pdca-status.json`
does not know it — verified by `find docs -name '*author-done-line*'`, which returned nothing
before this file. The work arrived as an inbound **h-mad handover brief** from `HemaSuite-wsg`
(session `4f2a4086`) and was executed under h-mad, not under Plan→Design→Do.

So there is **no gap-detector Match Rate**, and the report does not state one. The requirements of
record are the brief's four Next Steps and four Open Items; those are what §"Success criteria"
below scores against, and each traces to a line in
`docs/handoffs/2026-09-08-main__author-done-line-protocol.md`.

## What shipped

**Agent side — five files.** `agents/{spec,plan,design,implplan}-author.md` and
`agents/doc-auditor.md`. Each DONE template gains `path= lines= sha256=`, and the rule beside it
pins the derivation (`wc -l < "$F"`, `shasum -a 256 "$F" | awk '{print $1}'`) so author and
orchestrator measure the same thing rather than two plausible things.

The four authors hash the **document**, which exists whatever `REPORT` was set to — that is what
answers the brief's open question, and it is stated at each site instead of left implicit.
`doc-auditor` hashes its **report**, its own deliverable, before creating the `.done` marker, and
has no `<none>` variant, so there is no unverifiable case on either side.

**Orchestrator side — `SKILL.md` rule 6** under §"Teammate authors", running the new
`scripts/h_mad_done_gate.py` (222 lines, stdlib-only) before `$RP` is read or anything is
committed. Two checks, not one: `--expect-path` catches an author that hashed the *wrong* file and
therefore reports a digest that verifies perfectly against the file it named.

`lines=` never gates — `wc -l` counts newlines, so an artifact with no trailing newline reads one
short, and a matching sha already proves the bytes. Reported as
`lines_check=ok|disagree|absent`, with `absent` kept distinct from `ok` because one of them is
unmeasured.

## Evidence

| gate | result |
|---|---|
| brief premise, re-verified at `6f00f8c` | `grep -ciE 'sha256\|line-count\|lines='` → **0** on all five agent files, **0** in SKILL.md; HEAD control 5,5,5,5,5 / 4 |
| new tests | 47, both directions — every refusal has a matching acceptance |
| mutations | `author_done_line.json` **19/19 ALL_CAUGHT**, 0 survived; anchors 19/19 |
| per-mutation `test` keys | 19/19 — each row killed by its OWN named test, so no wrong-catcher scores as a kill |
| skills `h-mad` full suite | **3110 passed, 2 skipped** (8m18s) |
| HemaSuite HPW full suite | **9709 passed, 65 skipped, 11 xfailed, 0 failed** (7m57s) |
| delta self-review | `DELTA: CLAIMS claims=21 executed=13 unverified=8`; all 8 hand-run with controls |
| diff | 9 files, +1004 / −7 |

**Why the HPW run is the treatment and not merely a baseline.** 17 HemaSuite test files name
h-mad; **five** resolve a path into it, each hardcoding
`Path.home()/.claude/skills/h-mad/scripts/` + `{h_mad_derive_test_path.sh,
h_mad_do_preconditions.py, h_mad_resume_decision.py, h_mad_state_schema.json,
h_mad_telemetry.py}`. There is no `CLAUDE_SKILLS_ROOT` override, so those tests always read
whatever the symlink resolves to. This diff touches none of the five, and all five are
byte-identical between the main checkout and the worktree — so the inputs those tests see are the
same either side of the merge.

## Success criteria — the brief's own list

| # | criterion (brief) | status | evidence |
|---|---|---|---|
| N1 | DONE-line contract in the five agent definitions | ✅ | all five grep ≥ 1; templates pinned by test |
| N2 | orchestrator's half in SKILL.md §"Teammate authors" | ✅ | rule 6, `\|\| exit 1`, before `$RP`/commit |
| N3 | decide whether `REPORT=<none>` weakens it | ✅ | option (a) — hash the document; stated at every site |
| N4 | mutation-test the guard with a per-mutation `test` key | ✅ | 19/19, each by its own key |
| O1 | the specification gap itself | ✅ | closed by N1+N2 |
| O2 | no claim existed — create and claim under the brief's slug | ✅ | `--create --claim`, later released |
| O3 | coupling hazard — run BOTH suites before merging | ✅ | 3110 and 9709, both green |
| O4 | the brief was uncommitted, committing it is the taker's job | ✅ | `655973f` (ref mode), landed as `d252942` |

**8 of 8 in scope.** No criterion was deferred or waived.

## The findings that mattered

**A rule that reads correctly and cannot be run.** The first draft of rule 6 prescribed
`--message-file "$MSG"` — and `$MSG` was bound **nowhere** in the skill. The author's final message
arrives in the Agent tool result, not on disk; `$RP` holds the report *body*, not the DONE line.
The gate existed, the rule named it, and the prescribed invocation was inert. That is this
section's own failure class — *a documented rule is not an enforced one* — reached **through** the
rule written to close it. `--done-line` is now primary, which is what the five live dispatches
actually did, and `test_rule_6_prescribes_a_COMMAND_THAT_CAN_BE_RUN` scans the fenced block for
unbound `$name` references. Scoped to the block, never the file: the prose deliberately quotes
`$MSG` to name the defect, and a file-wide ban would forbid the document from recording what went
wrong.

**A false PASS produced by the verification itself.** Checking whether the five HemaSuite-read
scripts were identical across the two trees, `for p in $READ` — **zsh does not word-split an
unquoted scalar**. The loop ran once on a single bogus path, both `shasum` calls failed, and two
empty strings compared equal and printed `IDENTICAL`. The conclusion was right and the method
could not have shown it. Re-run reading one path per line from a heredoc, with a must-DIFFER
control (`SKILL.md`) in the same command. Every figure in §Evidence above is from the corrected
run.

**A stale count in the sentence that introduces a list.** §"Teammate authors" read *"Four rules
follow"* beside five, from the day rule 5 landed, and nothing pinned it. A reader who counts stops
at rule 4 and never reaches the gate. Now six, pinned by a test that counts the numbered items.

**An untracked duplicate blocks a cherry-pick.** The brief was committed in ref mode while an
untracked copy of the same file sat in the main checkout. `git cherry-pick` refused —
*"untracked working tree files would be overwritten"* — even though the two were byte-identical.
Proved identical (with a control) before removing the untracked copy, then the pick was clean.

## Open follow-ups

None for this feature. Landed on `main` as `6f00f8c..d252942` and pushed; the h-mad claim is
released (`owner_session_id: None`); the work is live on `~/.claude/skills/h-mad` and the gate was
exercised on that path after the merge.

Worth carrying forward: the five-script coupling set above should be **re-derived**, not reused,
before any *other* h-mad change is judged safe — a diff that lands in one of those five is
genuinely coupled, and the HPW suite is then load-bearing rather than confirmatory.

## Version History

- v1.0: Closure report. Taken over from `HemaSuite-wsg` (session `4f2a4086`) as an h-mad handover
  brief, not as a bkit PDCA cycle — §"PDCA provenance" says so rather than reporting a Match Rate
  that was never computed. 8/8 of the brief's own criteria met; suites 3110 (skills) and 9709
  (HemaSuite HPW); mutations 19/19 ALL_CAUGHT with per-mutation `test` keys. Landed
  `6f00f8c..d252942` on `main` and pushed; claim released.
