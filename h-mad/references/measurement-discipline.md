# Measurement discipline — the orchestrator's own verification errors

Eighteen orchestrator verification errors were filed across nineteen document rounds on one
feature (`doc-block-exec`, 2026-09-04 → 2026-09-06), plus one more on the round before them. Every
single one was caught by an author, an auditor, or by reading raw output — **none by the
orchestrator that made it.** They are not carelessness and "be more careful" does not close any of
them: each is a distinct way a command can return a number that is correct and answers a different
question than the one asked.

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

Related: SKILL.md §"The four rules that are the ORCHESTRATOR's, not the author's" (round-level
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

## What this costs, and why it is worth stating in the sheet

The sheets are being caught — by fresh-context authors, by the second-family gating leg, and by
the sheet's own standing instruction that a reader's run beats a reading printed in it. That is the
union working as designed. The conclusion the ledger actually supports is narrower and less
comfortable: **the orchestrator is the least reliable measuring surface in the loop**, because it
is the only one writing claims about the tree without a second surface reading them. Say so in the
sheet — "if your run disagrees with a reading here, YOUR RUN WINS" — rather than only in a ledger
nobody in the round reads.
