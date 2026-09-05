# doc-block-exec — round eighteen decision sheet (shared facts for the r18 revision batch)

**Written 2026-09-05 evening by session d16ef45c. Freeze = HEAD at the moment this sheet was written:
`cac6edc`.** Every reading below that says "at the freeze" was taken there. Rounds 3–17 all FAILED the
5b gate; r17's result (`docs/03-analysis/doc-block-exec.gating-decision-sheet.r17.md` §"Round seventeen
gating result") stands: design 2+3, plan 2+2 (same set on both surfaces), impl-plan 2+6, union 15, plus
the plan c88 `-b` leg's must 1 (81 vs 85 — converges with both prior legs, sheet r17 C40). Documents at
the freeze: design **v1.109** / plan **v1.104** / impl-plan **v1.53** / spec **v1.63** (re-derived:
`tr '\n' ' ' < $f | /usr/bin/grep -oE -- '- v1\.[0-9]+' | tail -1`).

Reports this round answers: `docs/02-design/features/doc-block-exec.design.audit.v97.{teammate,codex}.md`,
`docs/01-plan/features/doc-block-exec.plan.audit.v88.{teammate,codex,teammate-b}.md`,
`docs/01-plan/features/doc-block-exec.impl-plan.audit.v48.{teammate,codex}.md`. The verified findings
are r17 sheet C32–C36 (codex) and C40 (`-b`); this sheet cites them by number and does not restate them.

## FACT 1 — three commits since the r17 gating freeze, and exactly what each moved

r17 gated at `fa64031`. Since then, SIX commits (`git log --oneline fa64031..cac6edc`; see C1 — the
first draft of this paragraph named three): `4f40e8d` (the r17 handoff doc, +1 file under
`docs/handoffs/`), `fbc8655` (plan c88 `-b` report + r17 sheet C40), `f81f75e` + `55b2371` (an
INBOUND handover brief from HemaSuite session `cab14393`, `docs/handoffs/…hmad-audit-loop-evidence-from-gateway-consolidation.md`,
+1 file — committed by another session on this branch while this one was working), `b39d9dc` (the #87
tooling batch — `h-mad/SKILL.md`, `scripts/hmad-dispatch.sh`, `scripts/h_mad_assemble_audit.py`, five
`agents/*.md`, two `references/*.md`, three `tests/*.py` incl. one NEW file), `cac6edc`
(`docs/learnings.md` +2 rows). Per #49t every census command the four documents publish was re-run at
each sha, not only the `h-mad`/`handoff` closure predicates; the mechanical pass ran 258 self-contained
published commands (113 skipped: stdin-fed fragments, `<placeholders>`, `$vars`). The deltas, attributed
per commit:

| census (command as the documents publish it) | `fa64031` | `fbc8655` | `b39d9dc` | `cac6edc` | moved by |
|---|---|---|---|---|---|
| `pytest h-mad/tests -q` (h-mad suite) | 2552 | 2552 | **2574** | 2574 | `b39d9dc` (+22: 4 exec, 3 assembler, 15 agent-definitions incl. parametrized) |
| `pytest --collect-only -q` from the repository root | 2814 | 2814 | **2836** | 2836 | `b39d9dc` (+22, same tests) |
| `git grep -h '^def test_' <sha> -- '*test_*.py' \| wc -l` | 1512 | 1512 | **1527** | 1527 | `b39d9dc` (+15 `def` lines; parametrize makes 22 collected) |
| `ls h-mad/tests/test_*.py \| wc -l` | 88 | 88 | **89** | 89 | `b39d9dc` (`test_h_mad_agent_definitions.py`) |
| `git ls-files -- h-mad handoff \| wc -l` | 236 | 236 | **237** | 237 | `b39d9dc` |
| `git ls-files \| wc -l` (unscoped) | 3666 | **3668** | **3670** | 3670 | `4f40e8d` (+1, handoff doc), `fbc8655` (+1), `f81f75e` (+1, inbound brief), `b39d9dc` (+1, new test file); the sheet's own commit makes it 3671 — see C1 |
| `git diff --name-only fbc2ea0 <sha> -- '*.py' \| wc -l` | 0 | 0 | **4** | 4 | `b39d9dc` (assembler + 3 test files) |
| `grep -c '^#$' h-mad/SKILL.md` | 1 | 1 | **0** | 0 | `b39d9dc` — see FACT 3 |
| 09-04 probe, GLOB: `new_only` / `titleless` / `both` | 1 / 1 / 297 | 1 / 1 / 297 | **0 / 0 / 297** | 0 / 0 / 297 | `b39d9dc` — see FACT 3 |
| `git grep -n '```bash' -- '*.py' \| wc -l` | 8 | 8 | 8 | 8 | unmoved |
| `git grep -l '```' -- '*.py' \| wc -l` | 25 | 25 | 25 | 25 | unmoved |
| `git ls-tree -r --name-only <sha> \| grep -cE 'heading_differential\|grammar_corpus'` | 3 | 3 | 3 | 3 | unmoved |
| `git ls-files '*.py' \| grep -vcE '^(h-mad\|handoff)/'` | 415 | 415 | 415 | 415 | unmoved (plan:2740 already says 415 at `fbc2ea0`) |

**Where the moved figures are published (present-tense sites the authors must re-stamp or rewrite):**
`2552` — plan:3879, plan:4221 (VH), impl-plan:3800, :3818, :3917 (VH), spec:716. `2814` — plan:3878,
:4221, impl-plan:3800, :3818, :3917, spec:715. `1512` — impl-plan:3917. `88` — plan:510. The bare-`#`
family — design:350–356 ("The one live instance **is** …"), plan:3046–3050 and :3212–3216, impl-plan
:1646–1656 (`grep -c '^#$' h-mad/SKILL.md` returns **1**). `new_only=1`: design ×4, plan ×4, impl-plan
×2; `titleless=1`: plan ×5, impl-plan ×1 (value grep at the freeze, newline-collapsed, fixed-string).

**FACT 2 clause 2 applies:** a reading stamped at `fbc2ea0` (`2552 at fbc2ea0`) stays TRUE at
`fbc2ea0` and is not rewritten. What is false at the freeze is every PRESENT-tense sentence — "the suite
is 2552", "returns 1", "the one live instance is" — and every Version History line that a future reader
will take as current. Authors re-stamp those to `cac6edc` with the new value, and leave the historic
stamps alone.

## FACT 2 — the freeze-sha rule, three clauses (carried verbatim from r16/r17)

1. **An entry's own freeze-sha field** names the last commit before the batch was authored — here
   `cac6edc`, the parent of the commit that will land this batch.
2. **A reading of a committed blob** stays stamped at that blob (`fbc2ea0`, `cb4fe99`, `fa64031`,
   `b39d9dc`, …). It does not move when the freeze moves.
3. **A reading taken over this revision's own post-edit body** is stamped to *the tree this revision
   ships* — never to `cac6edc`, which does not contain your edits.

**Lesson carried into the rule this round (#49t, twice):** a sha named in advance goes stale — `b39d9dc`
was named as the r18 freeze and was superseded one commit later by a docs-only commit that an unscoped
`git ls-files` counts. The freeze is whatever `git rev-parse HEAD` says when the sheet is written, and
the authors are told THAT sha, not a predicted one.

## FACT 3 — the bare `#` in `h-mad/SKILL.md` is GONE at the freeze; the accounting goes to N=0 (operator-visible decision)

`b39d9dc` removed the lone `#` line between the `exec`-ceiling section and `## Reading a dispatch
verdict` (it arrived with `bea1b60`), on the round-seventeen handoff's explicit instruction ("repair the
bare `#` at `h-mad/SKILL.md:984`"), and pinned the removal with
`test_h_mad_agent_definitions.py::test_skill_has_no_bare_heading_stub`. The orchestrator did not know,
while landing that commit, that three documents treat that line as **the single live specimen** of an
empty ATX heading: design:353 ("The one live instance is …"), plan:3046–3050 (`titleless=1` at six shas,
"the single `new_only` member is an empty ATX heading in `h-mad/SKILL.md`"), plan:3212–3216, and the
impl-plan's accounting at :1646–1656 ("every `new_only` member is enumerated … at `fbc2ea0` there is
exactly one member … `grep -c '^#$' h-mad/SKILL.md` returns **1**"). A tooling commit moved a corpus
fact the feature's documents state in the present tense — #49t's class exactly, one level deeper: the
census predicate (`'*.py'`, `h-mad handoff`) was checked and passed, and a MARKDOWN line the documents
enumerate by content moved anyway.

**Decision: keep the repair.** The `#` was a defect in SKILL.md (an empty `h1`), the handoff asked for
it, and the impl-plan's accounting model was written to hold any N ("every `new_only` member is
enumerated, and each one is a heading under CommonMark") — N=0 is a legitimate value of it. What the
authors write:

- **design** (§ around :350–356, and the ×4 `new_only=1` sites): the specimen is historical — "was the
  one live instance at `fbc2ea0`; removed by `b39d9dc`" — and the present-tense probe reading becomes
  `new_only=0`, `titleless=0`, `both=297` GLOB / `both=292` TRACKED at `cac6edc` (re-run the committed
  09-04 probe; quote its three output lines). The empty-ATX-heading case is then covered by a
  **fixture** in the feature's own tests (hostile-fixture rule), never by pointing at the live corpus
  again — a corpus specimen is a measurement, not a test.
- **plan** (:3046–3050, :3212–3216, and the `titleless=1` ×5 sites): extend the sha list — `titleless=1`
  at the six shas named, **0 from `b39d9dc`** — and say why (the member was removed as a SKILL.md defect,
  commit `b39d9dc`), so the correction the plan describes ("the new pattern is a correction, not a
  softening") keeps its evidence: the specimen existed and was measured; it does not have to still exist.
- **impl-plan** (:1646–1656): the accounting sentence at the freeze reads `new_only=0`; the
  needle-based locator paragraph survives as the RULE (a member is located by needle, never by line pin)
  with the specimen paragraph moved to past tense. The `grep -c '^#$' h-mad/SKILL.md` → **1** reading
  is re-stamped "at `fbc2ea0`", followed by "**0** at `cac6edc`". Any test or mutation row that asserts
  the SKILL.md specimen exists is rewritten against a fixture; the row count stays 85 unless a row's
  only killer was the live specimen, in which case say so.
- **spec**: no site (value grep: `new_only`, `titleless`, "bare `#`" all 0 in the spec).

**Residual stated exactly:** with N=0 the claim "each member is a heading under CommonMark" is vacuously
true at the freeze; the documents say so in those words rather than letting a vacuous truth read as a
verified one (DECISION Q).

**Alternative, rejected unless the operator objects:** restore the `#` and drop the pin test. Rejected
because it re-introduces a SKILL.md defect to keep a measurement stable, which inverts what a
measurement is for.

## FACT 4 — the codex class (r17 C32–C36): design changes, ONE decision each, stated once

Routed per task #96; each is a decision the authors apply, not a finding to re-argue. Cross-document
values below were grepped at the freeze (FACT 8).

- **(a) `OverlappingSubstitution` — ONE representation.** The design's single tagged `pairs` list of
  `(kind, a, b, offset|None)` wins. The impl-plan's `pairs` + `intersections` split (value grep:
  `intersections` impl-plan ×9, design 0, plan 0, spec 0) and Task 1's bare pairs go. Owner: design
  states it; impl-plan conforms (9 sites); plan's single mention conforms.
- **(b) span scan enumerates OVERLAPPING occurrences** via the lookahead form `(?=…)` with
  `(m.start(), m.start()+len(k))` — `re.finditer` on a bare key misses `aa` at `[1,3)` in `aaab`
  (r17 lesson; value grep: `finditer` design ×1, `(?=` in NO document — this is new text). Fixture
  `aaab` under `{aa, ab}` → `intersect: "aa" "ab" "2"`. Withdraw sheet r17 3a's self-intersection
  residual (falsified by the same fact). Owner: design (rule + fixture), impl-plan (test), spec
  (AC-2.7 second clause names the fixture if it names any).
- **(c) AC-3.14 asserts `__cause__ is cleanup_error`**, not `__suppress_context__ False` — `raise err
  from X` always sets `__suppress_context__ = True`, so the old assertion rejects the prescribed
  implementation. Value grep: `__suppress_context__` design ×4, impl-plan ×4, plan 0, spec 0; `AC-3.14`
  spec ×7, design ×9, plan ×6, impl-plan ×1. Owner: spec (the AC), design + impl-plan (the 8
  `__suppress_context__` sites), plan (its 6 AC-3.14 mentions conform).
- **(d) `LaunchFailed.__init__` err annotation** `OSError | subprocess.TimeoutExpired | ValueError`
  (impl-plan :1973; the bare-name grep for the annotation found 0 in every document — the author sweeps
  by the spelling the document actually uses). Owner: impl-plan; design conforms if it types it.
- **(e) Task 2's intersection test asserts exception DATA; the emitted detail line is asserted in Task
  4.** Owner: impl-plan only.
- **(f) Task 5 scaffold keeps the exactly-one-gating-fence guard** (three `_gating[0]` sites). Owner:
  impl-plan only.
- **(g) Task 2's `AttributeError` REDs — TOOLING HALF LANDED at `b39d9dc`:**
  `h-mad/references/codex-implementer-prompt.md:52` now scopes the "ImportError/AttributeError is an
  unwritten test" rule to `wiring` tasks and states that a new-symbol task's first RED is
  `AttributeError` **by construction**, acceptable only with a post-GREEN assertion in the same test.
  Remaining: the impl-plan states this for Task 2's REDs and cites the prompt (value grep:
  `AttributeError` impl-plan ×6, design ×2). Owner: impl-plan.

## FACT 5 — the routing gaps and the prose class (r17 C32; task #97)

- **plan**: AC-1.8 pin → `--collect-only` (value grep `collect-only`: spec 5 / design 10 / plan 9 /
  impl-plan 18 — the plan's pin is the one that names the wrong flag); `81 mutations` → **85** at both
  plan sites (value grep: `81 mutations` plan ×2, nowhere else; `85 rows` design ×2 impl-plan ×4);
  register statuses and the closure chronology (both broke at `af19d53`; #42 — Setext re-run recorded
  but listed un-re-run); plan:510's `88` → 89 (FACT 1).
- **design**: `at "0"` at the AC-matrix row (:3548; value grep `at "0"` design ×1, `at <offset>`
  design ×1 spec ×1 — the spec's is the grammar placeholder and stays); `22` → 23 slicer sweep; stale
  `29`/`69`/"prints nothing" self-measurements; five spec ACs never named — 2.3, 3.4, 3.5, 4.4, 6.3
  (value grep at the freeze: `AC-2.3` design 0, `AC-3.4` 0, `AC-3.5` 0, `AC-4.4` 0, `AC-6.3` 0 —
  confirmed absent).
- **impl-plan**: `_field` docstring 19 → 20; wire-row carve-out gains `wire-unconditional` (value grep:
  design ×2 plan ×1 impl-plan ×4); Task 2 nine/ten count; `1512` → 1527 and `88`-class figures per
  FACT 1.
- **spec**: no r17 must lands in it; it conforms to (b)/(c) above and re-stamps its `2552`/`2814`
  (spec:715–716) per FACT 1.

## FACT 6 — the reopen rule (carried from r17 FACT 5)

**A post-DONE reopen re-runs every screen its own new text can move**, before the second DONE. A
screen that reads `0` is a screen your next sentence can break. Announce, edit, re-run the screens,
THEN the second DONE.

## FACT 7 — the version-number rule (carried from r16/r17, #49k) and the r18 author-dispatch rules

A version bump is the FIRST thing you write. Bump when you start, send DONE once when you finish, write
nothing after DONE without a prior message saying so. The orchestrator reads `git show :<path>` back
before any commit.

**New this round, from r17 C22/C24 and landed in every `h-mad/agents/*.md` at `b39d9dc`** (restated in
each dispatch prompt because definitions may be cached at session start): never call `advisor()`; read
in slices (`grep -n` to locate, `Read` ≤ ~400 lines per call, never a 3,500-line document whole); the
`<ROLE>: DONE version=v1.N` line is the FIRST line of the final message; before every write, assert
the file's mtime and newest `- v1.N` line still match what you last read, and stop-and-report if not.
Orchestrator side (SKILL.md §"Teammate authors"): a "Prompt is too long" notification is recoverable;
rule ownership explicitly before any successor; collect on the DONE line and the `.done` marker, not
on the notification.

## FACT 8 — cross-document ownership, built from a VALUE grep (C32/#49u), not from which document a finding was raised against

Counts are occurrences at the freeze, newline-collapsed, fixed-string. A `0` is a measured absence,
never a "—"; the r17 sheet's "—" cells hid two plan musts.

| value / decision | spec | design | plan | impl-plan | who edits |
|---|---|---|---|---|---|
| `OverlappingSubstitution` (a) | 0 | 3 | 1 | 7 | design decides; plan + impl-plan conform |
| `intersections` (a, goes) | 0 | 0 | 0 | 9 | impl-plan |
| `(?=` lookahead (b, new) | 0 | 0 | 0 | 0 | design + impl-plan add; spec names fixture |
| `__suppress_context__` (c) | 0 | 4 | 0 | 4 | spec AC-3.14; design + impl-plan rewrite 8 sites |
| `AC-3.14` | 7 | 9 | 6 | 1 | all four conform to (c) |
| `collect-only` / AC-1.8 pin | 5 | 10 | 9 | 18 | plan fixes its pin; others verified by author |
| `81 mutations` → 85 | 0 | 0 | 2 | 0 | plan |
| `at "0"` (design) / `at <offset>` (spec grammar) | 0 / 1 | 1 / 1 | 0 / 0 | 0 / 0 | design rewrites its instantiated row; spec placeholder stays |
| `wire-unconditional` | 0 | 2 | 1 | 4 | impl-plan carve-out; design/plan verified |
| `AttributeError` by construction (g) | 0 | 2 | 0 | 6 | impl-plan states; cites `codex-implementer-prompt.md` |
| `2552` → 2574 | 1 | 0 | 4 | 3 | spec, plan, impl-plan re-stamp present-tense sites |
| `2814` → 2836 | 1 | 0 | 2 | 4 | spec, plan, impl-plan |
| `1512` → 1527 | 0 | 0 | 0 | 1 | impl-plan |
| `88` test files → 89 | 0 | 0 | 1 | 0 | plan:510 |
| `new_only=1` → 0 (FACT 3) | 0 | 4 | 4 | 2 | design, plan, impl-plan |
| `titleless=1` → 0 (FACT 3) | 0 | 0 | 5 | 1 | plan, impl-plan |
| bare `#` / "one live instance" (FACT 3) | 0 | 1+2 | 2 | 1 | design, plan, impl-plan |
| `^#$` returns 1 → 0 (FACT 3) | 0 | 0 | 0 | 3 | impl-plan |
| five unnamed ACs (2.3, 3.4, 3.5, 4.4, 6.3) in design | — | 0 each | — | — | design |

Spellings the grep could not confirm (the author sweeps every form the document uses before claiming
zero): `LaunchFailed.__init__` (0 everywhere as spelled), `_gating[0]`, "nine/ten". A zero from ONE
spelling is not an absence (r17 lesson: `heading_differential.py` vs the bare name; `<offset>` vs
`at "0"`).

Each author re-runs the cross-document check for their rows against the SIBLINGS' bytes at `cac6edc`,
not at the sibling's working file. Report "sibling owes X" in the tail; never edit a sibling.

## Standing constraints

- 5b gate NOT met; no entry claims a two-surface clean. The gate stamps only on a both-surfaces-clean
  round at ONE commit (#14).
- Gating after this batch: design **c98** / plan **c89** / impl-plan **c49**, assembled with
  `--vh-tail 3` (design was 1,027,802 chars at r17, 20 KB under the 1,048,576 ceiling that the
  assembler now reserves 64 chars of headroom against; `--vh-tail 1` if it grows). Two model families
  per phase: codex via `hmad-dispatch exec codex … --sandbox read-only --timeout 1800` backgrounded with
  `--log`, and a `doc-auditor` teammate told the freeze sha AND the actual HEAD. Delta self-review on
  the diff before dispatch. No agy leg until #77 is addressed.
- Nobody edits a sibling. The spec is revised only by findings that land in it (FACT 4 b/c).
- `.done` markers stay untracked.

## Corrections (appended during the round; lines above are left as written)

- **C1 — FACT 1's first draft named THREE commits since `fa64031`; `git log --oneline fa64031..cac6edc`
  names SIX (orchestrator error, #49-class: an attribution written from memory of one's own commits,
  not from `git log`).** Hidden: `4f40e8d` (the r17 handoff doc — it sits between `fa64031` and
  `fbc8655`, so the table's first column already absorbed its +1 file), and `f81f75e`/`55b2371` — an
  inbound handover brief from another session, landed on this branch between this session's resume
  and its first commit. Neither touches `h-mad/`, `handoff/`, `*.py`, or the four documents, so no
  scoped census moved; the unscoped `git ls-files` row is re-attributed above. Two consequences.
  (i) The sheet's freeze `cac6edc` is still correct — it is HEAD at writing — but "what moved" was
  under-attributed for one column. (ii) The inbound brief (`**Handover-From:** HemaSuite · main ·
  session cab14393`) is NOT taken over by this session; `pending-handovers` reports it, and the next
  resume's Step 3.5 owns that decision. Rule for r19+: the commit list in FACT 1 is pasted from
  `git log --oneline <prior-freeze>..<freeze>`, never typed.
