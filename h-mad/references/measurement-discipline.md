# Measurement discipline — the orchestrator's own verification errors

Thirty orchestrator verification errors were filed across nineteen document rounds on one feature
(`doc-block-exec`, 2026-09-04 → 2026-09-06) — eighteen carried the `#49` label, twelve more were
filed as DECISION letters or buried in round-result notes and had no label at all. Every single one
was caught by an author, an auditor, or by reading raw output — **none by the orchestrator that made
it.** They are not carelessness and "be more careful" does not close any of them: each is a distinct
way a command can return a number that is correct and answers a different question than the one
asked.

The pattern that makes them worth a file of their own: **the orchestrator demanded of the four
phase documents a discipline it was not applying to its own decision sheets and dispatch prompts.**
A decision sheet is read by four authors and three gating legs and is the single place a
cross-document fact is stated once — which makes it a single point of failure for an unmeasured
claim exactly as much as a single source of truth for a measured one. Three rounds running, an
author corrected a claim in the sheet.

**The standing rule, and every species below is a way of breaking it:**

> A count is evidence only against another count taken at the same **commit**, over the same
> **corpus**, in the same **grammar**, in a **shell whose state you did not inherit** — and
> derived by the command the document **defines**, not by a command that reproduces the
> document's number.

Related: SKILL.md §"The six rules that are the ORCHESTRATOR's, not the author's" (round-level
duties), §"An agent's reported numbers are a claim, not a measurement" (an agent's figures),
§"Re-measure a carried premise before working it" (a stale item's figures). This file is about
**your own**.

---

## PROVENANCE — right value, wrong commit

**Presence at a sha is not provenance.** A value observed at a commit is a fact about the tree at
that commit, never a fact about that commit. Four instances in one session, while briefing the
authors who were fixing the same class in the documents.

- `#49c` — certified "the third member IS correctly labelled" from ONE `git show`. The clause had
  shipped a revision earlier and been carried unrepaired; all three members of the list were
  mislabelled, not two. Four other provenance checks in the same pass were run correctly, which is
  why it read as verified work.
- `#49d` — published `7d8e797 53` for a design needle. `7d8e797` does not touch the design file at
  all; `53` entered at `f91a74b` and `7d8e797` merely carries it. The value was right and the
  attribution wrong.
- `#49e` — the same error, and the first to reach a commit message.
- `#49t`, second half — attributed a `pytest --collect-only` delta of +5 to the probe commit; the
  five tests were the *previous* commit's. **When a figure moves across two commits, attribute the
  delta per commit, never to the newest.**

**Rules.**

```bash
# Before publishing "<figure> at <sha>": did that commit TOUCH the file?
git rev-list <base>..<sha> -- <path>
git rev-parse <sha>:<path> <sha>~1:<path>      # identical blobs => not the provenance

# "X was introduced in revision N" needs THREE readings, not one:
git show <N-landing>:<doc>   | grep -cF '<needle>'   # present at N
git show <N-1-landing>:<doc> | grep -cF '<needle>'   # ABSENT at N-1  <- the one that gets skipped
#   plus: the counted surface is already larger at N
```

Two readings return N and N+1 alike. The predecessor negative is the only grep that separates
*shipped* from *carried*.

---

## SCOPE — right value, wrong corpus

The provenance rule does not catch these: the sha is right and the population is not.

- `#49f` — a series **defined** as head-scoped (body, everything before `## Version History`) was
  **published** whole-blob. The two agreed for four shas and diverged once Version History entries
  began quoting the label the needle matches. The gating auditor, the delta reviewer and the
  orchestrator (twice) all compared the reading to the PUBLISHED VALUE and got agreement. None ran
  the reading the DEFINITION prescribes.
- `#49h` — `cd <subdir> && pytest …` then a "repo root" run chained in the same invocation. The
  `cd` persisted; both "controls" measured the subdirectory. Root 2809 vs subdir 2547 — the figure
  being disputed was the auditor's, and the auditor was right.
- `#49n` — "`df04e8e` and `dfae038` touched only `docs/handoffs/`" was never run. `dfae038` touches
  three files. It went into the decision sheet header, four author prompts, three gating prompts
  and a commit message; an author copied it into a document, where a gating leg filed it as a must.
- `#49s`, `#49t` — an "already exists" and a "the spec says" asserted without a grep; the phrase
  was in a different document.

**Rules.**

- **When re-deriving a published figure, run the command the DOCUMENT DEFINES**, not one that
  reproduces the document's number. Agreement with a published value is evidence about arithmetic,
  never about scope. A series whose early members are scope-invariant hides a scope error until the
  corpus grows past it.
- **Every clause of the form "X touched only Y" is a measurement and takes a command.**
  `git show --stat --format='' <sha>` costs nothing. **Never compress two shas into one claim
  unless both were measured** — the compound is what hides that only one member was checked.
- **Take each control in its OWN tool invocation.** A `cd` in a chained command is not scoped to
  that command.
- An "it is new" / "it says" / "it already exists" is an ASSERTED SCOPE until a grep answers it.

---

## GRAMMAR — right string, wrong language construct

No amount of re-running at the correct sha or corpus catches these. `grep -c` answers "how many
lines contain this string", never "how many instances of this concept exist".

- `#49g` — a `pgid=` census presented as "the design carries BOTH spellings". Both design hits are
  Python constructor kwargs with a placeholder value, correctly bare, that never reach a verdict
  line. Ten of the eleven occurrences across the feature are that one kwarg. The count was
  arithmetically correct and semantically empty; two of four authors caught it independently.
- `#49r` — a markdown value sweep whose needle could not match across an inline-code delimiter:
  `handoffs/? alone` cannot match `` docs/handoffs/` alone``. Published 2 sites; the
  markup-admitting form returns 4. The author's own first sweep used the blind needle and also got
  2, so "the sheet and my run agree" was two copies of one blind reading.
- `#49j` — the same shape across a hard wrap: 12 vs 14.
- `#49v` — a shared string handed to two authors in a quote style the documents do not use; both
  wrote the other one and the delta review filed a must.

**Rules.**

- **A census over a token that can appear in more than one grammar is not a census until the
  grammars are separated.** Before publishing `<token> = N`, print the N matching lines with
  context and classify them:
  ```bash
  grep -n -o -E '.{60}<token>.{20}' <doc> | grep -v '<the construct that is not the concept>'
  ```
- **A value sweep over markdown collapses newlines AND admits the inline-code delimiters** —
  prose-stated and backtick-stated occurrences are one population:
  ```bash
  tr '\n' ' ' < <doc> | grep -o -E '<needle>.{0,2} <word>'
  ```
- **Paste a shared string in the documents' OWN spelling — derive it by EDITING the shipped
  artifact, never by retyping it.**
- Every token, line, or label a decision sheet **prescribes** is grepped against the spec's grammar
  section and against the documents' existing enumerations before it is written. A decision that
  adds a member names every enumeration that member joins.

---

## FREEZE — a commit that touches no document still moves its measurements

Rule 2 says freeze the tree for the duration of a round. What "frozen" means is the part that kept
being got wrong: the four documents being byte-identical is **not** the predicate.

- `#49r`, structural — the r16 freeze was a tooling commit under `h-mad/`. The plan publishes
  `git diff --name-only <base> <sha> -- h-mad handoff`, which had printed nothing at the previous
  base and now printed two files. That one blanket had licensed ~70 stamped readings. The suite
  floor moved too.
- `#49t` — the freeze was a probe commit under `docs/03-analysis/probes/`. It was correctly checked
  against the `h-mad`/`handoff` predicates and passed them, while moving every REPO-WIDE `*.py`
  census the spec and plan publish (fences 6→8, files 24→25, changed `.py` 0→6) because one probe
  carries ``` fences inside string literals. **A predicate that names no root is moved by a file
  anywhere.**
- **`\b` is a BACKSPACE in awk, not a word boundary.** POSIX awk has no `\b` anchor, so
  `awk '/\b88\b/'` matches a literal backspace character and screens **nothing** — it returns 0 on a
  file full of hits, which reads as a clean screen. `grep -E` and `python re` do support it, so the
  same needle behaves differently in the three tools a measurement typically passes through, and the
  awk leg is the one that fails silently. Use `grep -oE '\b<n>\b'` for the count, or an explicit
  `[^0-9]` guard in awk. Recovered 2026-09-07 from orchestrator label `#30`, which recorded the fix
  as HALF applied (`\b` closed on one needle, the trailing `[,)]` left on another) and then lost the
  reason across four handoffs; the feature it was filed against has since merged and archived, so
  what survives is the trap, not the fix.
- `#49w` — three sheet entries certified "no scoped census moved" over a commit while the design's
  OWN published trip-wire (`… | grep -vc '^docs/'   # expect 0`) read 8 there. None of the three
  ran it.

**Rules.**

- **Before naming a commit as a freeze, enumerate every census command the documents publish and
  re-run each at the candidate sha.** They are greppable — the documents state them:
  ```bash
  grep -n -E 'git (grep|ls-files|diff --name-only)|pytest --collect-only|find ' <the four documents>
  ```
- **Run every published `expect 0` screen at the sha before certifying a freeze.** A trip-wire the
  documents publish is the cheapest possible check and the one that was skipped.
- **A tooling fix landed mid-arc is a measurement event for every document that measures the
  tooling.** Merge tooling only after the round's last gating pass is collected — merging while a
  round is open silently invalidates every stamped census, and the documents are not re-audited
  afterwards.

---

## COMPLETION SIGNAL — a start-of-work signal read as end-of-work

Four uninformative signals had already been recorded as uninformative when a fifth was used to make
the same call.

- `#49k` — four version numbers all bumped, read as "all four authors are done". A version bump is
  the FIRST thing an author writes. Three authors were still writing; a gating cycle went out
  against a commit that no longer matched the tree the auditors read.
- `#49o` — a hook's `Running:` set dropped two legs, read as "both died without output". Both were
  alive and slow, and each subsequently wrote a substantive report.
- `#49q` — a report re-read on disk minutes before `git add`; a second writer overwrote the path in
  between. The commit message on `main` describes a 137-grep report and the blob is a 34-grep
  partial.

**Rules.**

- **The only valid completion signal is the author's own DONE report.** Not a version number, not a
  file mtime, not a `git status` line, not an idle hook, not absence from a running-set. Each is
  satisfiable mid-write. `git add` of a file still being written captures a torn snapshot silently.
- **Before declaring a leg dead:** check its report path AND its marker AND wait one more poll
  interval AND, where a transcript exists, read it.
- **Never re-dispatch to a path another agent was handed.** Suffix every re-dispatch's report path
  (`…teammate-b.md`). Two agents on one path is one of them overwriting the other, and an
  instruction to "write early so a partial survives" guarantees the stub sometimes lands last.
- **A stub written early must be UNSCORABLE, never `None` sections that parse as zero findings.**
  This one is now mechanical: `collect` refuses a report carrying an in-progress sentinel in its
  head or a stated `Evidence: 0`, with `COLLECT: INVALID reason=<r>`, and `combine` scores the pass
  `UNVERIFIED unscorable_report:pN` — distinct from `no_report:pN`, because a refused report and an
  absent one prescribe opposite next moves.
- **`git show :<path> | head` — the INDEX blob — immediately before `git commit`,** and compare its
  evidence line to what the commit message claims. Never describe a file in a commit message from a
  read taken before `git add`. A path with two live writers is not committable.

---

## VERIFIER — a check whose success condition cannot fire

- `#49l` — a liveness probe sent a computed product and polled for the answer. The `case` pattern
  carried a transposed digit, so the loop could not have matched a correct answer at any point and
  would have printed `NOT CONFIRMED` for an agent that was live and answering correctly. Caught
  only because the probe printed its own `expected:` line and it disagreed with the pattern.

The remedy that a false negative prescribes is expensive and would have "worked", masking the real
cause. Same family as an unrun command's empty output read as a real zero, and as
`COLLECT: MISSING` read as evidence an auditor failed: **the check failed, and the failure is
spelled identically to the answer.**

**Rules.**

- **Derive a probe's expected value in the same expression that tests for it.** Never type it
  twice.
- **A probe must be shown capable of PASSING before its failure means anything.** Run the matcher
  against a known-good input first.
- Score on the raw value read back, never on the loop's verdict.
- Assert that a mutation actually applied before reading its result — a no-op mutation and a caught
  one both print "the tests failed". Restore from a saved COPY, never `git checkout --`, which
  reverts unstaged implementation along with the mutation and makes every later "control" measure
  the same un-implemented tree (the `#49h` shape, one layer up).

---

## CHANGE SIZE — `--stat` counts lines, and a line here is not a unit of change

- `#49m` — a divergence reported to three in-flight gating legs as "17 insertions / 11 deletions,
  28 attributable lines", and used as grounds to tell them not to re-read. Measured by content:
  ~1939 / ~582 / ~2066 changed characters. A Version History entry in these documents is a SINGLE
  line of ~3000 characters, so any rewrite inside one collapses to exactly one changed line — and
  Version History entries are where the round's musts land.

**Rules.**

```bash
# Does the document contain this specific repair? -- fixed-string presence, never --stat
git show <sha>:<doc> | grep -cF '<distinctive phrase>'
# How much text changed? -- characters, not lines
git diff --word-diff=porcelain <a> <b> -- <doc>
```

Every sha comparison names **two fixed endpoints**. `HEAD`, the working tree and the current branch
are not endpoints — true when taken, false the moment the batch lands. (Residual, stated: a fixed
pair can still name the WRONG pair, and no screen catches that.)

---

## OWNERSHIP TABLES — fill from a value grep, never from where the finding was raised

- `#49u` — a cross-document ownership table's plan column read "—" for two decisions. The plan
  restates both. Its author was never told, and the next round's gating leg filed both as musts.
  The value sweep that would have caught it was run AFTER the batch and only over the new values.

**Rule.** Before writing a cross-document ownership table, grep every shared VALUE — the old token,
the old invocation, the old phrasing — across ALL FOUR documents and fill the table from the hits.
A "—" cell is a claim about the tree. And re-run the sweep after ANY reopen, not only at first
collection: a sequential wave's divergence prose expires when an earlier document is reopened
(measured — an author correctly recorded the design's state in wave 2, the design was then
reopened, and the wave-2 prose became false of the shipped bytes).

---

## SPAN — a derived claim and an underived one in the same sentence

- `#49b` — a decision sheet characterised a span as "five audit reports and one handoff". The diff
  returns seven paths. The four gated documents' byte-identity across the span had been derived
  correctly, twice; the REST of the span was narrated from memory in the next clause, and the two
  read alike.

**Rule.** A decision sheet is a gated artifact. Every claim in it about the tree carries the
command that produced it, **including the ones that are only context**. If a sentence describes
what a diff contains, it runs that diff.

---

## ABSENCE — a zero is a measurement, and a zero that is right by accident is a defect

The species that gets skipped because it does not look like a count. "No corpus instance exercises
either arm", "the corpus has none of either", "nothing in this repository", "no guard covers any of
them" — every one of those is a figure, and each was shipped without ever being run.

- Round six, impl-plan: "no corpus instance exercises either arm" — **false**, 29 space-arm fence
  openers across 4 files, one of them `h-mad/SKILL.md`. Reproduced independently twice.
- Round seven, design: "The corpus has none of either" — **false** for one arm; 8 indented fence
  markers, and the published `0` was safe only because two other constraints happen to be
  indent-bounded. Right by accident, not by measurement.

**The root cause was the orchestrator's, not the authors'.** The impl-plan wrote the correct rule
when it repaired its own instance — and wrote it **only for itself**, scoped to that document. The
round-six sheet said a figure travels with its sha and a runnable command, and never said an absence
claim *is* a figure. So a rule discovered in one document was closed in that document instead of
lifted into the sheet, and the design author, who never saw it, shipped the same shape one round
later.

**Rules.**

- Every absence or zero claim carries (i) the runnable command, (ii) the sha it was run at, and
  (iii) evidence it was **run in the revision that ships it** — not reasoned about.
- **Say WHY the zero is zero, and whether that reason is load-bearing or incidental.** A zero held
  up by an unrelated constraint is a defect waiting for that constraint to move.
- **A rule discovered inside one document is lifted into the sheet, or the other three re-derive the
  defect.** "Close the class, never the instance" applied one level up: the class here is the
  *round*, not the document.

## UNIT — a count without its unit is four different numbers

One `grep -n` produced four true figures and one wrong one in a single round, and the wrong one was
the orchestrator's: **`grep -n` output LINES were counted as occurrences.** The spec carried 7 bare
pins on 5 prose lines; the published figure was 3. Elsewhere in the same round: 22 occurrences / 19
lines / 17 distinct / 8 files, published as 21. And "19 path-qualified pins folded" was 19 *folded
paragraphs* against 49 occurrences — frozen as a contract while the revision's own edit moved the
population 47 → 49.

**Rule.** Publish every count with its unit — occurrences, matching lines, distinct values, files,
folded paragraphs — and never let a figure derived in one unit be compared against a figure derived
in another. Where a relation between two units matters, state it as a relation with a dated example
explicitly marked *not* a contract.

## PRESCRIPTION — a fix instruction is a claim about the tree, and it gets the least scrutiny

A finding has three separable parts — **facts, concern, prescription** — and they fail
independently. The prescription arrives attached to a verified fact, which is exactly why it is
relayed unchecked.

- An auditor prescribed "name the enclosing test function for `test_docsections.py:27`". **There is
  none.** That line is inside a module-level string constant beginning at `:20`; the first `def` in
  the file is at `:44`, below the hit. The orchestrator relayed it and asserted it as viable; the
  author discovered the impossibility.

**Rules.**

- Apply the three-part discipline to the **prescription** too, by whoever relays it. Relaying an
  unchecked prescription launders it into an instruction.
- **When a report offers alternatives, relay all of them.** That is the only reason the round above
  cost nothing — the author had an escape and lost no cycle. Do not narrow to the one that reads
  best.
- An interpretation you supply is a finding you authored. Adjudicating "on this axis the word means
  X" is a claim about the document, and if the document says it nowhere else and it is not derivable
  from the shipped bytes, it is not an adjudication — it is a new requirement.

## FROZEN FIGURES — a "do not disturb" list written before the revision is stale by construction

The sheet told an author "reproduced and UNMOVED — do not disturb: ledger consistent at four". The
author moved it to five **against the instruction**, announced the override, gave its reasoning and
offered the one-line revert. It was right: repairing the one routable instance *creates* the fifth
member of the class the ledger counts. Leaving it at four would have shipped exactly the defect the
audit had just caught — a repaired member the count does not reflect.

The error: the list enumerated what the auditor found in the **pre-revision** document, and it was
applied as a **post-revision** constraint.

**Rule.** A "do not disturb" list MUST separate, and say which bucket each figure is in:

- **(a) figures the revision cannot affect** — tree measurements, sibling-independent counts,
  matrix totals when no row is touched. Freeze these.
- **(b) figures the revision's own fixes will move** — any count over a **class the revision adds to
  or removes from**. These are re-derived after the fix, never frozen.

An unbucketed freeze instruction is an instruction to ship an inconsistency. And verification of a
state is not authority over a change to it: having personally checked a figure is not grounds to
forbid the revision from moving it.

**Keep the behaviour that caught this** — announce the override, give the reasoning, offer the
revert. Three of four authors in that session caught something their own dispatch got wrong. Ask for
it explicitly in every dispatch: *if the brief contradicts the tree, file it, do not work around it.*

## CONTROLS — the four ways a control can be alive and prove nothing

`§VERIFIER` covers a matcher that cannot fire. These are its siblings, and together they are the
reason the round-on-round finding count plateaued: once the documents are past feature defects, the
findings are overwhelmingly about the verification apparatus the previous round added — and
specifically about **self-descriptive claims** regarding that apparatus.

1. **A control over a COMPOSITE tests the composite, not its members.** A marker alternation had a
   boundary repair applied three times, half-applied every time, and passed its control every time,
   because **a healthy sibling branch covers a sick one** — the fixture matched the working branch
   first. Every branch must be controlled against its OWN fixture, run with that branch ALONE.
2. **A boundary, anchor or delimiter fix applies to BOTH SIDES and to EVERY sibling alternative in
   the same expression.** The same three rounds: `\b` fixed for one alternative while the trailing
   `[,)]` stayed on its neighbour, and a third branch was unbounded on both sides in the revision
   that bolded "every marker is bounded on both sides".
3. **A stated PROPERTY of a mechanism is a claim about code and must be executed, never asserted.**
   Three instances in one round, one per document: "the old fold scores 0 on this phrase" (it scored
   3 — the control sentence wrote its own needle into the document); "this screen reads both sides as
   committed blobs so no working-file edit can move it" (the shipped line is a working-tree `open()`;
   the correct `git show` form is four paragraphs away). An author who says "this screen cannot be
   moved by X" demonstrates it **by doing X and re-running**.
4. **Before believing a 0 from a check YOU wrote, run a positive control** — grep for a substring
   you know is present in the target region. A verification grep written against *assumed* phrasing
   returned 0 on text that was present; it cost nothing only because the orchestrator asked rather
   than asserted. A 0 with no positive control is a vacuous zero, applied to verification instead of
   to a shipped screen.

**Why this cannot be fixed by adding machinery:** more machinery means more self-description. It
converges only by requiring the property claim to be **executed at authoring time**.

## PARTITION — a total that reconciles proves nothing about its parts

A four-way split of 73 reconciled exactly while three of the four parts were wrong, because the
last bucket absorbed the remainder (plan-author, doc-block-exec r15). A remainder bucket cannot
fail to reconcile: it is DEFINED as the total minus the others, so the sum is an identity, not a
measurement. Reconciliation of a partition that contains a remainder carries no information about
any part.

What to publish instead:

```bash
# Every part derived by its OWN command, and the sum compared to a total derived SEPARATELY.
# Never "the rest".
a=$(grep -c '<needle A>' doc.md); b=$(grep -c '<needle B>' doc.md); c=$(grep -c '<needle C>' doc.md)
t=$(grep -cE '<needle A>|<needle B>|<needle C>' doc.md)
echo "a=$a b=$b c=$c sum=$((a+b+c)) total=$t"   # sum != total is the finding; sum == total is one check, not proof
```

A part named "other", "remaining", "the rest", or given as `total - (the named ones)` is a
remainder and must be labelled as such in the sheet — it is not a measured figure and cannot be
cited as one. If a part genuinely cannot be derived independently, the partition is two figures
(the measured ones and the total), not four.

## SELF-COUNTING SCREENS — a screen whose needle matches the prose being written runs last, per instrument

A document that states "the debt word appears **29** times" and is then revised gains a 30th
occurrence in the revision that fixes it; a screen for `\b91\b` in a document that carries the
grep command for `\b91\b` counts the command. Any screen whose needle can match text the current
revision is still producing is a **self-counting instrument**: its correct value is only known
AFTER the last edit, and a value written mid-revision is stale by construction.

The class produced 12 of 12 delta-review musts in two consecutive rounds (r18, r19) and one
document carried ten such instruments; the reopen re-ran some and not others. So the rule is a
per-instrument checklist, not a re-count:

1. Before DONE, list every self-counting instrument in the document by its needle — a count over
   the document's own body, a `grep -c` whose needle appears in the document, a "N members" over a
   list the revision edits.
2. Run each one LAST, after the final edit, and write the value it returns.
3. Re-run the whole list after ANY further edit, including the one that fixes a stale member —
   fixing one instrument's value is itself an edit the others can see.

A self-count that is stale is not a defect in the tree — the tree is unchanged by fixing it — but
it is a false claim the document makes about itself, and the next reader cannot tell it from a
true one. Name the instrument's needle beside the value so the next revision can re-run it rather
than trust it.

**The instrument list must include contracts stated ELSEWHERE in the document, not just the sites
that publish the count.** This is the extension the r-cycle-2 defect forced, and it is one level out
from the rule above: a revision appended M89–M94 and moved the mutation count 88 → 94, and the
author's own re-derivation reported "88 → 94, Exec Summary and the spec section and task rows 4 and
12 all updated" — it swept **the sites it had edited**. But Task 25's **AC-7.5d still required 88
rows**, making the acceptance criterion provably unsatisfiable against a document that enumerates
94. **Two independent arithmetic checks missed it the same way**: both verified that the
enumeration was internally consistent (`ids M1–M94 contiguous, per-task totals sum`) and neither
asked what else in the document had been promised a number.

So step 1's list is built by needle, not by edit site, and it has a second half:

1b. List every place the document states a **contract over an enumerable set it contains** — "all N
    ACs pass", "requires 88 rows", "the N members of X" — even where the current revision did not
    touch it. A count that is *correct where it is written* and *contradicted by a contract three
    sections away* is the same false self-claim, and it is harder to see precisely because the
    edited region is consistent. Grep the document for bare integers adjacent to the set's noun
    before DONE, not the sites in your own diff.

The failure mode to recognise: **an internal-consistency check cannot find this class**, because
the enumeration really is consistent. The question that finds it is "what did this document promise
about this number somewhere I did not edit?"

## THE ROUND AS AN ARTIFACT — what only the orchestrator can see, and therefore only it can get wrong

- **Collect every teammate report into `docs/` BEFORE writing the sheet or dispatching an author.**
  `audit-cycle` writes an in-process leg's report to `docs/` itself; a teammate report lands only in
  `/tmp` until `collect-report --surface teammate` runs. Skipped once, the sheet cited three paths
  that did not exist and two authors opened with a blocker. Assert every path exists before
  dispatching a single author; anything but `COLLECT: OK` is a halt, not a warning. Knowing the rule
  and having a step that enforces it are different things — this was skipped in the round *after* it
  was applied correctly, in the same session that had already invoked it.
- **A cross-document debt claim needs an orchestrator reading taken AFTER all N authors land**, not
  at the freeze. Measured: one commit repaired a field in two documents while three authors, in that
  same commit, each wrote an OWED-ELSEWHERE saying a sibling still owed it. All three false at the
  moment of commit — and the **commit message knew**: it names the repair the documents describe as
  pending. No author could have seen it; each read siblings being revised concurrently. Write the
  commit message from the post-landing reading, never from the decision sheet.
- **Do not mutate the shared decision sheet while authors are running.** A correction to it lands
  after the batch, not during — mutating shared input under running readers is orchestrator rule 4's
  staleness hazard, caused deliberately.
- **Do not carry a premise from the previous round's dispatch.** It is the most tempting source to
  copy from precisely because it is structurally identical and was correct last time. "All three
  siblings moved in `<a>..<b>`" went into two dispatches; the diff returns three files and the spec
  is unchanged at both shas — and the orchestrator had itself decided not to dispatch a spec author
  that round, so the brief contradicted its own decision. Before sending, run
  `git diff --name-only <prev-freeze> <this-freeze>` and write what it actually returns.
- **A hand-assembled list in a sheet is the same object as a transcribed number.** The rule against
  copying a figure out of an audit report applies to spans, populations and file lists the
  orchestrator assembled by hand. The sheet must apply its own rules to itself.
- **The delta review's SUBJECT is not a freeze sha.** The commit a delta diff was taken over is what
  was audited; a document's freeze sha is the last commit, the tree its tree-derived figures are
  taken over. They are different commits and a sheet that calls the first "the freeze" makes the
  batch restamp backwards into the defect it is repairing. The boundary, because the correction
  invites over-application: **every reading stamped at a BLOB stays stamped there** — only an
  entry's own freeze-sha field moves.
- **A carve-out exempting a claim from sha-stamping must name what determines the behaviour and show
  that thing is not tracked.** Otherwise it is an unfalsifiable exemption.
- **A Version History entry is a historical record. Correct it with a bracket in place, naming the
  refuting command — never by rewriting or deleting it.** An entry that was TRUE WHEN WRITTEN and
  has since been discharged is not a defect; rewriting it to satisfy a rule about the present
  falsifies a correct record. Measured twice: an auditor routed two such entries as must-fixes, and
  a separate entry was found to overclaim a repair the diff does not contain — both correctly
  handled by bracketing rather than editing.
- **An audit report that prescribes a POPULATION must derive it once and cite it twice.** One report
  gave eleven members in its must and ten in its should, and neither count included a member the
  author's own walk found.

## What this costs, and why it is worth stating in the sheet

The sheets are being caught — by fresh-context authors, by the second-family gating leg, and by
the sheet's own standing instruction that a reader's run beats a reading printed in it. That is the
union working as designed. The conclusion the ledger actually supports is narrower and less
comfortable: **the orchestrator is the least reliable measuring surface in the loop**, because it
is the only one writing claims about the tree without a second surface reading them. Say so in the
sheet — "if your run disagrees with a reading here, YOUR RUN WINS" — rather than only in a ledger
nobody in the round reads.
