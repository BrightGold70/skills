# h-mad reference — teammate authors and the orchestrator's review of their output

_Moved verbatim from `h-mad/SKILL.md` (row 2910); SKILL.md keeps a pointer stub under the same heading. Edit the text here. Everything below the marker line is the section body exactly as it stood in SKILL.md._

## Teammate authors — one author, one document, fresh context every time

<!-- h-mad split body: SKILL.md §"Teammate authors — one author, one document, fresh context every time" -->

**You do not author a phase document in your own loaded context.** Phases 2, 3, 4 and 5a each
dispatch a fresh-context teammate that owns exactly one file:

| Phase | Document | Agent | Definition |
|---|---|---|---|
| 2 | `docs/01-plan/features/<feature>.spec.md` | `spec-author` | `agents/spec-author.md` |
| 3 | `docs/01-plan/features/<feature>.plan.md` | `plan-author` | `agents/plan-author.md` |
| 4 | `docs/02-design/features/<feature>.design.md` | `design-author` | `agents/design-author.md` |
| 5a | `docs/01-plan/features/<feature>.impl-plan.md` | `implplan-author` | `agents/implplan-author.md` |

```
RP=/tmp/author_<feature>_<phase>_v<N>.report.md; rm -f "$RP"
Agent(subagent_type: "plan-author", prompt: "<feature>; documents: <spec> <design> <current plan>;
      audit reports for the cycle being answered: <paths>; orchestrator decisions: <none | list>;
      REPORT=$RP")
```

**Pass `REPORT=` on every author dispatch, and read the file rather than the message.** The message
transport truncates at ~4 KB and cuts the **tail**, which is where an author's report puts the owed
list, the declines with their reasons, and the text owed to sibling authors — none of which is in
the document, so losing it loses it entirely. Measured on `gateway-consolidation` c105: two of three
messages from one `design-author` run were cut mid-word, recovery cost three `SendMessage`
round-trips, and a retry explicitly scoped to "ONLY the tail, under 15 lines" was **itself**
truncated — a retry is not a workaround when the retry has the same limit. Independent prior
evidence 2026-09-06: 3 of 3 authors, always at the owed list. `doc-auditor` has carried a `REPORT`
path all along (`agents/doc-auditor.md` §"What you are given"); the authors did not, and that
asymmetry was the whole defect. This is **not** the r17 DONE-line failure and does not mean that fix
regressed: r17 targets DONE-line loss and works — the DONE line survived all three c105 messages.
`REPORT=<none>` remains legitimate for a dispatch that cannot stage a path, and the author must then
say on the line after DONE that the body is inline.

The same routing applies to a **revision**, not only a first draft. A cycle's must-fixes go to the
author that owns the document they land in; you relay findings and decisions, you do not apply
them yourself. The sites that revise are Phase 3's audit loop, Phase 4's (which inherits it), 5b's, and the
wire-pin gate's `UNSHAPED` remedy — all four re-dispatch, none of them regenerate in your context.
Phase 6b edits production files and the analysis document, never a phase document, and the
rejections ledger writes a sidecar and forbids editing the gated document, so those are not
revision sites.

**The spec has no audit phase of its own**, and that is not an oversight to correct here:
`h_mad_assemble_audit.py` binds `--phase` to `plan|design|impl-plan` as argparse `choices`, so a
spec audit cannot be assembled or collected. The spec is nonetheless revised — by findings raised
against the other three that land in it, which is how it moved v1.52 → v1.55 in one session — and
**those revisions route to `spec-author` like any other**. A spec edited by the orchestrator
because "it was only one number" is the exact path by which a value gets swept in one surface and
not another.

**Why.** The orchestrator writing a fix is the same context that wrote the defect, and it sweeps
the value it is *thinking about* rather than the value that exists. Measured on one feature:
83 design cycles, 74 plan cycles, 34 impl-plan cycles without meeting an exit gate, and roughly
**half** of all must-fixes were introduced by the previous cycle's fix. In one session six defects
in the orchestrator's own work were caught by fresh contexts and **none** by the orchestrator
re-reading its own document. Each agent file states the failure class each of its rules closes;
they are contracts, not style guides.

**Author dispatch rules the ORCHESTRATOR owns.** Measured 2026-09-05 (r17): the design author
read a 3,500-line document whole more than once, called `advisor()` — which forwards its entire
transcript a second time — and died of context overflow (`failed: Prompt is too long`)
mid-verification. The orchestrator then spawned a successor **without ruling ownership**; the
original resumed from its transcript and kept writing, and two authors held one file for ~8
minutes, colliding only because the successor asserted-before-write and stood down. Eight rules
follow, none of which an agent file can enforce for you (the count read **four** beside five rules
from the day rule 5 landed — a stale count in the sentence that introduces the list is the cheapest
possible way to make a reader stop at rule 4):

1. **A `failed: Prompt is too long` notification is recoverable, not death.** The author can
   resume from its transcript. Before concluding it is gone, read the working file's mtime and its
   newest `- v1.N` Version History line and compare with the last DONE you have.
2. **Rule ownership explicitly before spawning a successor.** Say in the successor's prompt which
   author owns the file now, and require it to assert the file has not moved (mtime, newest
   `- v1.N` line) before every write and to stand down if it has.
3. **Authors never call `advisor()` and read in slices** — those rules live in every
   `agents/*-author.md`; do not undo them from the dispatch prompt ("read the whole design" is an
   instruction to overflow).
4. **Collect on the `DONE` line, not on the notification.** Every author's final message puts its
   `<ROLE>: DONE …` line FIRST (four r17 reports were truncated before a trailing DONE); a report
   file or a bumped Version History is the deliverable, and a DONE message that arrives ~45 minutes
   after the marker is benign.
5. **Read `$RP` after every author DONE — staging a path is not consuming it.** You passed
   `REPORT=$RP` on dispatch (§"Teammate authors"); the author's body is in that file and its message
   now carries only the DONE line and a pointer. If you act on the message alone you have read the
   pointer and not the report, and the **owed list is the part you skipped** — the declines with
   their reasons, and the verbatim text owed to sibling authors, none of which is in the document.
   That is the same loss the file deliverable was added to prevent, moved one step later. If the
   file is absent or empty while the message claims a body, say so and re-ask; an empty `$RP` beside
   a DONE is a cannot-judge, not an empty report. When the author declared `REPORT=<none>` on the
   line after DONE, the body is inline and may be truncated — treat a message that ends mid-word as
   incomplete rather than as a short report.

6. **Re-derive the artifact's sha256 and refuse a mismatch, BEFORE you read `$RP` or commit.**
   Every author's DONE line now carries `path=`, `lines=` and `sha256=` over the artifact it owns
   (`agents/*.md`, the rule beside each DONE template). Verify it with the gate, never by eye:

   ```bash
   python3 ~/.claude/skills/h-mad/scripts/h_mad_done_gate.py \
     --repo <repo> --expect-path <the document you dispatched for> \
     --done-line '<the first line of the author'"'"'s final message, verbatim>' || exit 1
   ```

   **`--done-line` is the primary form, and that is not a preference.** The author's final message
   arrives in the Agent tool result, not on disk: `$RP` holds the report BODY, and the DONE line is
   in the message. So there is no file to point `--message-file` at unless you staged one yourself,
   and a first draft of this rule prescribed `--message-file "$MSG"` with `$MSG` bound nowhere in
   this skill — a command that reads correctly and cannot be run, which is this section's own
   failure class one level down ("a documented rule is not an enforced one"). `--done-line` is also
   what the five live dispatches actually did. Use `--message-file` only when you have written the
   message to a path in this same shell; it additionally enforces DONE-first, which `--done-line`
   cannot see because you have already selected the line.

   Read the `DONEGATE:` token, never `$?` — and spell the call `|| exit 1` even so, because
   **`set -e` is inert in the Bash tool's top-level shell** (§"Your own measurements"), so a bare
   invocation that exits 1 falls through and you commit the artifact the gate just refused. `PASS`
   exits 0, `FAIL` 1, and `UNREADABLE` exits 2 because it is a cannot-judge — the message file was
   unreadable or the artifact could not be opened — and routing it like a refutation sends you to
   re-ask the author about a problem that is yours.

   **Two checks, not one, and `--expect-path` is the half that catches the likelier mistake.** An
   author that hashes the WRONG file reports a digest that verifies perfectly against the file it
   named; only comparing `path=` against the document you dispatched for can see that. A missing
   artifact is `FAIL reason=artifact_absent`, not `UNREADABLE`: the author asserted a file with
   that digest exists, and absence refutes the assertion rather than obstructing the gate.

   **What a `sha_mismatch` MEANS** — say it in the halt, because the obvious reading is wrong. It
   is almost never a lying author. A subagent's "stopped writing" is an **instant, not a state**:
   your own post-DONE dispatch (a `SendMessage`, a successor spawned on a `Prompt is too long`
   notification) can make the original resume from its transcript and write again. So a mismatch
   most often means the file moved after the author hashed it, i.e. rules 1 and 2 were skipped.
   Refuse, rule ownership, and re-ask for a DONE line derived after the last write.

   `lines=` never gates and the token reports it as `lines_check=ok|disagree|absent`. `wc -l`
   counts newlines, so an artifact with no trailing newline reads one short — a units trap, and a
   matching `sha256` already proves the bytes are identical, which is the whole claim.
   `lines_check=disagree` beside a `PASS` means the author miscounted, not that the file moved.

   `REPORT=<none>` does not weaken this. The authors hash the **document**, which exists whatever
   `REPORT` was set to; `doc-auditor` hashes its report, and it has no `<none>` variant
   (`agents/doc-auditor.md` §"What you are given"), so there is no unverifiable case on either
   side. The inline-body caveat in rule 5 is about the REPORT, and this gate is about the artifact.

7. **An author is not finished because it reported DONE — it is finished when you have told it to
   stop, and you prove that by re-deriving the sha a SECOND time at commit.** Rule 6 runs the gate
   when you collect; this rule runs the same gate again immediately before `git commit`, with the
   staging in between. One run proves the artifact matched when you read it. **Two runs matching,
   with your commit between them, is the only thing that proves the file did not move while you
   were preparing it** — and the window between collect and commit is exactly where your own
   post-DONE dispatch lands. Measured on another lane (HemaSuite-wsg, `24245ccc`): a spec v1.6 that
   retracts v1.5 end-to-end, 246 insertions / 147 deletions, self-reported by that lane's
   orchestrator as *"the FOURTH freeze violation on this feature, all mine: the author was still
   live and mid-revision when I committed."* Four recurrences on one feature, with the rule written
   down privately and broken again — which is why it is here and gated rather than stated.

   ```bash
   git add -- "$DOC"
   python3 ~/.claude/skills/h-mad/scripts/h_mad_done_gate.py \
     --repo "$REPO" --expect-path "$DOC" --done-line "$DONE_LINE" || exit 1
   git commit -m "$MSG_TEXT"
   ```

   `$DOC`, `$REPO`, `$DONE_LINE` and `$MSG_TEXT` are yours to bind in the same shell — `$DONE_LINE`
   is the verbatim first line of the author's final message, the same string rule 6 took. A `FAIL`
   here is not the author's error and not a reason to re-ask: it means the artifact changed after
   you read it, so **the commit you were about to make is of content nobody has reviewed.** Halt,
   rule ownership (rule 2), and re-collect. `UNREADABLE` is a cannot-judge and must not be committed
   through either — exit 2 is not a pass.

   The cheap wrong version of this rule is "check the author is not running". You cannot: a
   subagent's "stopped writing" is an **instant, not a state** (rule 6), a quiet agent is
   indistinguishable from a finished one, and nothing you can run answers *absent*. The sha answers
   a question that IS decidable — did these bytes change — and it is the same question.

8. **Act on the DOCUMENT, not on the author's report — a correct sha is not a correct claim.**
   Rules 5 and 6 make you read the report and prove the bytes are the author's. Neither one reads
   the document. Verbatim from the same lane: *"The spec author reported DONE at v1.5 and I
   committed on the strength of its report, verifying the two NEW findings while never re-reading
   the FR whose premise I had already refuted."* v1.5's AC-11.2 asserted the exact claim two agents
   had independently killed an hour earlier; the report was honest, the digest verified, and the
   committed content was wrong.

   So: **for every premise you refuted this round, re-read the section that carried it in the
   revised document before you commit** — not the report's summary of it, and not the diff, which
   shows you what moved and is silent about what an author left standing. An author revising for
   findings A and B has no duty to revisit premise C, and will not; the refutation of C is yours and
   only you know it happened. This is the exact inverse of rule 5's failure: there the report was
   never read, here it was read and was trusted **in place of** the artifact it describes.

### Run the delta self-review as a SCRIPT before re-dispatching (#11/H4)

On a revision cycle, before the audit is re-dispatched:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_delta_review.py \
  --repo <repo> --rev <the revision commit> [--path <doc> …]
```

Read the `DELTA:` token, never `$?` — `CLAIMS` is an answer and exits 0; only `UNREADABLE` (git
could not answer for that revision) exits 2. **`unverified` is a cannot-judge and appears in the
verdict line on purpose**: those spans hold shell metacharacters or a verb outside the read-only
allowlist, so they were not run, and a count of what could not be checked that is missing from the
token reads as a pass.

**Why a script and not the habit.** The hand-run version found fix-introduced defects in **3 of 3**
passes at roughly a quarter of a gating round's cost — and failed twice in one sitting, once to a
`</dev/null` on a piped helper and once to zsh applying the `:h` modifier inside `$h:hematology`. A
review whose own instrument fails silently is worse than none, because it reports clean.

**It never executes arbitrary text from a diff.** Prose backticks hold illustrative commands and
destructive examples; `h_mad_doc_block_exec.py` may execute document blocks only because they are
explicitly TAGGED, and nothing in a diff hunk is. A span is run only when it is a bare read-only verb
with no shell metacharacters — matched on the VERB, since `rm -rf / # grep` contains `grep`.

Only spans that could be commands at all are reported: a verb plus an argument. Measured on the real
commit `8af16d9`, the first version treated every backticked span as a claim and returned
`claims=15 executed=0 unverified=15` — every one an identifier (`doc-auditor`, `DIVERGED`,
`[H-MAD]`). An alert that is always wrong is worse than no alert. On `a90c365` the filtered form
returns `claims=2`, both genuine published commands.

This is ADVISORY and does not replace the second surface — see §"Delta self-review" for the round
protocol it mechanises.

### Tag every must-fix with its ORIGIN, at the moment it is verified (#11/H7)

The audit loop's largest class is defects that an earlier cycle's *fix* created, and until this
shipped nobody could say how large. Reconstructed from memory at handoff, `#18`'s ledger could only
report "at least **17 of 98** cycles carry a must-fix that an earlier cycle's fix created (seeded
from recorded evidence — a lower bound; a blank cell means *unclassified*, not *new*)". Tagged as
they were verified, the same loop's cycles 98–103 answer exactly: **51 of 152 must-fixes, 33.6%**,
the largest single class, plus 27 more (`author-self-caught`) that the revising author's own delta
review caught one step earlier. Neither number is recoverable after the fact.

After each cycle's reports are persisted, append one record per must-fix — **at the moment the
must-fix is verified, not at handoff**, which is the whole point:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_origins.py \
  --feature <feature> append --phase design --cycle 99 --leg codex \
  --item "<the finding, 80 chars>" --origin fix-introduced --by-cycle 98 \
  --verified-by-execution
python3 ~/.claude/skills/h-mad/scripts/h_mad_audit_origins.py \
  --feature <feature> summary --per-cycle
```

The eight origins are the ledger's and are not re-derived: `new-mechanism` · `new-consistency` ·
`fix-introduced` (with `--by-cycle`) · `propagation-gap` (a fix reached one document and stopped;
also `--by-cycle`) · `instrument` (the finding is about a command or count the document publishes) ·
`record-stale` (a Version-History record wrong at its own commit) · `author-self-caught` (optional
`--caught-by self|advisor|orchestrator`) · `rejected` (a false finding).

**Read the `ORIGINS:` token, never `$?`.** `OK` and `INVALID` are both answers; only `UNREADABLE`
(no sidecar, or an unreadable one) is a cannot-judge and exits 2.

**An absent sidecar is not a rate of zero**, and the tool says so rather than printing one: an
untagged feature and a feature with no fix-introduced defects are opposite findings that a bare `0`
spells identically. Same reason an unparsable line is named with its line number instead of skipped
— a dropped record makes every count smaller, and smaller reads as progress.

**The fix-introduced denominator excludes `rejected`**, and the output line states that it does.
Counting false findings would mean the cycles that filed the most noise scored best.

**This script never decides an origin.** Classifying a must-fix is a judgement about why a defect
exists, so `append` records one the orchestrator has already made. That is also why nothing hooks
it into `h_mad_audit_cycle.py`: the driver does not know the moment a finding is verified.

**Calibrated before it was wired**, against the 152 records that already existed: every hard rule
fires **zero** times on them. That bar is not ceremony — every `h_mad_precheck_doc.py` detector
first written as hard fired 104 / 49 / 48 times on documents that had just passed 83 and 74 audit
cycles, and all of those hits were correct usage.

### Shared sentences are single-sourced, and adoption is checked BEFORE the commit (#11/H5)

When two or more documents must state the same fact, the design owns the sentence and the siblings
quote it **verbatim**. Before committing a cycle that touched a shared fact, run:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_adoption_check.py \
  --sentence-file <the design's canonical line> \
  --doc <sibling1> --doc <sibling2> [--doc …]
```

Read the `ADOPTION:` token, never `$?` — `DIVERGED` is a verdict and exits 0; only a cannot-judge
(`UNREADABLE`: an unreadable document, an empty sentence, fewer than two documents) exits 2.

**Why this cannot be left to a reviewer.** Measured on `#18 gateway-consolidation`: two authors
independently corrected one shared fact in the same cycle, one to **18** and one to **20**. Each
document was internally consistent, so a reviewer reading any single document found nothing and a
reviewer reading both had no reason to diff one sentence out of thousands. Three of the last five
cycles' must-fixes there were propagation gaps of that shape. `doc-auditor` rule 7 already carries a
cross-document reading, but it runs in the NEXT cycle, after the divergence is committed — this
moves the same question before the commit and answers it mechanically.

Whitespace is normalised on both sides, because documents hard-wrap at different columns and a byte
comparison would report `DIVERGED` on siblings that adopted the sentence perfectly. What is **not**
normalised is the wording: this is an adoption check, not a similarity score, and h-mad has already
refused fuzzy matching once by measurement (§"Why the ack match is not fuzzy").

### Delta self-review — review the FIX before you re-dispatch the audit

An author has just changed a document to answer findings. Review **what changed**, not the
document again, before assembling the next audit prompt.

The reason is a number this repository keeps re-measuring on itself. In the last gating round on
`doc-block-exec`, **two of the three must-fixes were introduced by the previous cycle's own
repairs** — that document's own version history records it, and says the delta was the first place
looked *because* of it. Across a whole session roughly half of all must-fixes were fix-introduced,
and the gateway-consolidation Phase-4 record (durable session memory, not this tree — so cite it as recalled rather than as citable here) has four consecutive cycles where the fix produced the next defect. A cycle spent
finding a defect the last cycle created is a cycle spent twice.

**A revision that INSERTS, moves or renames a function re-runs `--check-anchors` on every spec
targeting that file, and a `migrated:` line is a finding, not a note.** This is the delta review's
code-side half and it has its own failure shape. Ordinary anchor drift changes the match count to 0
or 2+ and the harness REFUSES, which is loud. **Migration keeps the count at exactly 1** while the
match relocates into a different function, so every instrument agrees the spec is healthy and the
only symptom is a `SURVIVED` verdict — which reads as *"the guard does not bite"* and sends you to
rewrite a test that was correct. Measured in HemaSuite 2026-09-22
(`deck_guided_narrative_assets_task12.json` M3): an anchor written as
`<body tail>\n\n\ndef <next function>` identified its site **by its neighbour**; a later task inserted
a function between the two whose body ended in the byte-identical line, the anchor relocated, and
the run reported `MUTATION: SURVIVED mutations=11 caught=10 survived=1`.

A mutation may therefore pin its site with a `"symbol": "<enclosing def>"` key. `h_mad_mutation_harness.py`
derives the symbol the match actually sits in and refuses the mismatch — on the precheck as
`ANCHORS_DRIFTED` with a `migrated:` hint, and on the live run as `REFUSED`, never as a scored
mutation. The key is **optional and the coverage is published**: a sweep prints
`N of M mutations carry no symbol pin` as a detail line, because an anchor whose count was checked
and whose site was not is a different thing from one that was verified. Pin the ones whose `find`
identifies a site by its neighbour rather than by itself — that is the shape that migrates.

Two passes, cheapest first:

```bash
# 0. Code-side: did this revision move a symbol out from under an anchor?
python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py \
  --check-anchors <spec>.json          # `migrated:` is a finding

# 1. Mechanical — the greppable half, already covered by the precheck.
python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py \
  <document> --phase <phase> --root <PROJECT_ROOT>

# 2. What changed, and whether it answers what it claims to.
git diff <the commit the last cycle was audited at>..HEAD -- <document>
```

Then dispatch the diff, not the document. **Stage it with the script, never by hand** — the
report name is the part a hand dispatch gets wrong, because a delta report named inside the audit
filename grammar (§"Audit filename grammar") is counted as an audit cycle by every ledger consumer:

```bash
# 3. One ADVISORY doc-auditor delta review per phase the revision touched.
python3 ~/.claude/skills/h-mad/scripts/h_mad_delta_stage.py \
  --feature <feature> --project-root <PROJECT_ROOT> --sha <the revision> \
  --phase plan --phase design \
  --answers <the audit report this revision answers> [--answers <another> …]
```

It validates everything before it claims anything: the sha must name a commit, the sha must have
changed each phase's document (a sha that did not is a review of nothing, `<phase>:unchanged`),
and every `--answers` file must be readable and non-empty. A check it cannot evaluate — git fails,
a file cannot be read — halts like a check that failed. Then it **mints** the report name,
`docs/03-analysis/<feature>.<phase>.delta-review.<sha7>-<UTC yyyymmddTHHMMSSZ>.md`, with no flag to
override it; the tag is never `vN`, because the cycle counter reads `….v1.1.md` as a cycle. The
minted name is refused (`<phase>:name_in_audit_grammar`) if the ledger's own selectors would read
it — the cycle counter's version regex, the gate's stamp-name regex, and any `.audit.` segment,
imported from their modules rather than copied, so the check follows the grammar if it widens.
The report path and its prompt path are claimed once with the assembler's claim-once machinery
(a reused path is `<phase>:report_path_handed`, deleting nothing), the prompt file is written,
and each phase prints `DELTA-STAGE: STAGED phase=<p> report=<path> prompt=<path>` followed by the
exact `Agent(...)` call to issue. A refusal prints `DELTA-STAGE: HALT <what>:<reason>`, claims
nothing, writes nothing and exits 3 — except `prompt:unwritable`, which removes the prompts and
claims it made but may leave `docs/03-analysis` created; a usage error exits 2. Any value the
prompt interpolates (`--feature`, `--sha`, `--project-root`, each `--answers` path, the minted
paths) that carries a control character is refused first as `<arg>:control_char`: a newline in an
`--answers` path once wrote a second `REPORT=` line and steered the report into the audit grammar. Issuing the call stays yours, by
design: the script stages a dispatch, it does not make one.

**`--sha` is ONE commit, and the review sees only that commit.** Step 2 diffs a range — the last
audited commit to `HEAD` — but the subject staged here is `git show <sha>`. When the revision
answering these findings landed as more than one commit (a fix plus a follow-up), commit it as
one before staging, or stage once per commit that touched the document; otherwise the auditor
reviews half of it and nothing says so.

The prompt file it writes carries the content of the template below, with the minted `REPORT=`:

```
Agent(subagent_type: "doc-auditor", prompt:
  "PROMPT=<none — a delta review has no assembled prompt; your subject is below>
   PROJECT_ROOT=<root>  REPORT=<path>  This pass is ADVISORY.
   Subject: the diff below / `git show <sha> -- <document>`, and the findings it answers: <paths>.
   For each hunk: does it close the finding it claims, or only the instance the reviewer named?
   Did it break a claim elsewhere in this document or in a sibling — a count, a cross-reference,
   a value stated in more than one place?")
```

`doc-auditor` rule 7 already carries the cross-document check, so **do not write a new agent for
this**. What is new is only the scoping: a diff and the findings it answers, rather than a whole
document.

**It is ADVISORY and it is not a gate.** Its findings go back to the owning author as an ordinary
revision. A delta review that blocked would just be another cycle, which is the cost it exists to
avoid.

### The six rules that are the ORCHESTRATOR's, not the author's

An author cannot enforce any of these, because each one is a property of the round rather than of
a document:

1. **File scoping is the whole mechanism — one author, one document, and an author that finds
   another document owes something REPORTS it.** Nothing is silently harmonised across documents.
   That is what keeps parallel authoring tractable, and it is what creates duty 3.

2. **Freeze the tree for the duration of a round.** Unlike a codex leg, which reads a frozen
   assembled prompt, a teammate reads the **working tree**. Measured: a `SKILL.md` commit landed
   mid-round and all three auditors returned line numbers correct for what they read and
   mislabelled against the base commit they were given (`:1897` reported "at `e8eaf6f`", which is
   `:1887`) — and the orchestrator then relayed the wrong number onward. Commit before the round
   or after it, never during.

3. **Cross-check any acceptance criterion two concurrent authors touched.** Running authors in
   parallel produces contradictions neither can see. Measured: `design-author` added a
   dot-directory exclusion to AC-6.1 (25 files) while `implplan-author` independently repaired the
   same AC's rebase (30 files). Both measurements were correct and answered different questions. It
   surfaced only because the two reports were read against each other. This duty has no other home.

4. **A teammate's view of its sibling documents goes stale mid-round.** An author that read the
   spec before your revision of it landed will report "nothing is owed to the spec" and
   "contradictions: none" in good faith, and be wrong. Re-state what moved, or re-dispatch, rather
   than believing a sibling-document claim made against a version you have since replaced.

5. **Collect every teammate report into `docs/` BEFORE you write the sheet or dispatch an author.**
   `audit-cycle` writes an in-process leg's report to `docs/` itself; a teammate report lands only
   in `/tmp` until `collect-report --surface teammate` runs. Skipped once, the sheet cited three
   paths that did not exist and two authors opened with a blocker. Assert every path exists before
   dispatching a single author — anything but `COLLECT: OK` is a halt, not a warning.

6. **Take the cross-document reading AFTER all N authors land, and write the commit message from
   THAT.** Duty 3 cross-checks a shared AC; this is its other half — a debt claim *about a sibling*.
   Measured: one commit repaired a field in two documents while three authors, in that same commit,
   each wrote an OWED-ELSEWHERE saying a sibling still owed it. All three false at the moment of
   commit, and the **commit message knew** — it names the repair the documents call pending. No
   author could have seen it; each read siblings being revised concurrently. And do **not** mutate
   the shared decision sheet while authors are running: that is duty 4's staleness hazard caused
   deliberately. A correction to the sheet lands after the batch.

### Your own measurements — `references/measurement-discipline.md`

The six duties above are about the round. This one is about the decision sheet and the dispatch
prompts you write, and it is not optional reading: **thirty orchestrator verification errors were
filed across nineteen rounds on one feature — eighteen labelled `#49`, twelve more filed as DECISION
letters with no label — every one caught by an author, an auditor, or by reading raw output, and
none by the orchestrator that made it.** Three rounds running, an author corrected a claim in the
sheet. A sheet is read by four authors and three gating legs, which makes it a single point of
failure for an unmeasured claim exactly as much as a single source of truth for a measured one.

> A count is evidence only against another count taken at the same **commit**, over the same
> **corpus**, in the same **grammar**, in a **shell whose state you did not inherit** — and derived
> by the command the document **defines**, not by a command that reproduces the document's number.

The reference sorts the eighteen into the species that each need a different countermeasure —
PROVENANCE, SCOPE, GRAMMAR, FREEZE, COMPLETION SIGNAL, VERIFIER, CHANGE SIZE, OWNERSHIP TABLE,
SPAN — with the command that closes each. The four that cost the most wall clock:

- **Before naming a commit as a freeze, run every census the four documents publish at that sha**,
  and every `expect 0` screen among them. Byte-identical documents is not the predicate: a tooling
  commit under `h-mad/` and a probe commit under `docs/03-analysis/probes/` each moved censuses the
  documents had stamped, and each passed the check that was actually run.
- **The only valid completion signal is an author's own DONE report.** A version bump is the first
  thing an author writes, not the last.
- **Never re-dispatch to a report path another agent was handed** — suffix it. Enforced for legs
  staged through `h_mad_assemble_audit.py --report-file` and the `audit-cycle` verb: every staged
  report path and its prompt path are claimed once and never handed again, and the recipes and the
  verb mint a fresh pair per dispatch. Hand assembly (steps 6.6–8 without the script), dispatches
  that bypass the assembler (6a-prime, an `Agent()` given a hand-picked path) and sentinel mode
  (empty `--report-file`) are not guarded.
- **A claim about the tree in a sheet carries the command that produced it, including the ones that
  are only context.**

Say in the sheet that a reader's run beats a reading printed in it. The ledger's honest conclusion
is that the orchestrator is the least reliable measuring surface in the loop, because it is the
only one writing claims about the tree with no second surface reading them.

### The measurement layer lives in probes, not in the phase document

A phase document states a **claim** and the path of the **committed probe** that derives it
(`docs/03-analysis/probes/<feature>/<name>.<date>.<session>.py`), plus **one** reading stamped at one
sha. It does not publish sha-series of its own readings, ledgers of its own audit reports, trip-wires
over `h-mad/`, counts of its own sections, or any figure that a commit *of this feature's own
artifacts* moves. Measured on `doc-block-exec`: the design at `--vh-tail 1` assembled to 980,076 of
the 1,048,576-character `exec` ceiling, the plan carried a ten-sha ledger that the gating reports
landing advanced by one every round, and 9 of the 15 r18 musts were in that layer. A number that
lives in a probe is re-derived by running it; a number that lives in the document is re-stamped by
an author, and the re-stamp is the next round's must.

Two consequences. **Do not restructure a document mid-flight** — extracting the layer is itself a
revision batch that spawns two more rounds; apply the rule to the next feature, and to a document
whose audit prompt no longer fits (`ASSEMBLE: HALT <phase>:oversize` at `--vh-tail 1` is the trigger
that makes it mandatory, because the audit itself has become impossible). **A measurement-class
finding on an existing document is acknowledged with its re-run command**, never re-stamped by hand
(§"Finding class — build vs measurement").

### Precheck before you dispatch — never spend a cycle on a greppable premise

Before `h_mad_assemble_audit.py` for **any** phase audit (3, 4, 5b), run the document
through the precheck — and on a revision cycle run §"Delta self-review" first, which
covers this and the half a grep cannot reach. A dual-surface cycle costs two dispatches and roughly four minutes
of wall clock to discover a claim a `grep` refutes in a second, and then a second cycle
to fix it:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_precheck_doc.py \
  <document> --phase plan|design|impl-plan|spec --root <PROJECT_ROOT>
```

Read the `PRECHECK:` token, never `$?` — it exits 0 on both verdicts, and 2 only when the
document cannot be read. `PRECHECK: FAIL` → **re-dispatch the owning author with the detail
lines and do not assemble the prompt.** `PRECHECK: UNREADABLE` is a cannot-judge, not a pass.

**Auditing a plan or impl-plan? Re-derive the AC count first.** A Success Criteria line saying
"All N ACs pass" went stale three times in one feature, each caught by an auditor instead of a
check:

```bash
python3 ~/.claude/skills/h-mad/scripts/h_mad_ac_census.py \
  <feature>.spec.md <feature>.plan.md <feature>.impl-plan.md
```

`ACS: DRIFT` (a `CLAIM:`, `GAP:` or `DUPLICATE:` line) goes back to the owning author like a
`PRECHECK: FAIL`. `ORDER (advisory):` lines never move the verdict.

**Read the advisories too, even on a PASS.** They are the larger half and they are advisory
because no rule can decide them, not because they are unimportant: a `PATH:` or `SYMBOL:`
line is either a file the feature creates or a citation that has gone stale, and only you
know which. `--allow <substring>` records a deliberate hit; it is an INPUT and is never
inferred.

**What is hard is only what is provably wrong** — an unfilled slot, a pin past end-of-file,
a pin into a file that changed since the document's own provenance commit, a provenance sha
that names no commit here. That split was measured, not chosen: every detector filed as hard
on first cut fired dozens of times on the design and plan that had just passed 83 and 74
audit cycles — 104 `PATH:` hits, then 49 `LINEPIN:`, then 48 `PLACEHOLDER:` — and each time
the hits were correct usage rather than defects. **A gate that fails a clean document is not
a gate**, and finding that out costs one test run here against a full cycle in the loop.

### Why the ack match is not fuzzy

Softening the `## Acknowledged-not-fixed` match stops at canonicalisation plus an explicit
operator `[key]`. No text-similarity rule is applied, and that is measured rather than timid.

On the real 7-bullet sidecar of HemaSuite's `gateway-consolidation.plan.audit.v18` — which
accreted seven bullets over about three underlying findings — token overlap scores the **negative
control above both true pairs**:

| pair | what it is | jaccard |
|---|---|---|
| 1 ~ 4 | the same finding, re-worded | 0.089 |
| 2 ~ 5 | the same finding, re-worded | 0.158 |
| **6 ~ 7** | **two genuinely different AC-1.4 process-group leaks** | **0.180** |

The ordering is inverted, so every threshold that pairs the re-worded duplicates collapses the two
distinct leaks *first* — and a collapsed ack silently clears a real finding, which is strictly
worse than the re-acknowledging cost it was meant to save. Same shape as the refused evidence check
(#27): the rule that would help does not discriminate, and the rule that discriminates is vacuous.
**The `[key]` tag is the escape**, because it is stated by the operator rather than inferred.

