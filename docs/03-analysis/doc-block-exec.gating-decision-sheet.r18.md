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

- **C2 — appended 2026-09-05 by the dispatching session `adb05ac8`, before the r18 authors were
  spawned (a shared-facts gate: four authors fill an undecided fact four ways).**
  (i) **The h-mad suite is RED on the committed tree from `b39d9dc` through `7a56cb7`**: `pytest
  h-mad/tests -q` → `1 failed, 2573 passed` (2574 collected). FACT 1's first row (`2574`) is the
  COLLECTION count, not a green run; the prior session measured the suite before committing
  `b39d9dc`, and PINDRIFT is computed against the committed tree. The failure is
  `test_h_mad_precheck_doc.py::test_noise_floor_on_documents_that_survived_eighty_cycles[impl-plan]`:
  the precheck on the impl-plan reads 15 hard findings (> 12) — 11 `PLACEHOLDER` (the design grammar's
  `overlap:`/`intersect:`/`os_error:`/`pgid:` slots, unchanged and legitimate) plus **4 `PINDRIFT`** at
  impl-plan L217/L349/L885/L3917 pinning `h-mad/scripts/h_mad_assemble_audit.py:247`
  (`_trim_version_history`) and `:109` (`_braces_outside_fences`) against provenance `fbc2ea0`;
  `b39d9dc` edited the assembler (`DISPATCH_OVERHEAD_CHARS`, `prompt_oversize` inserted above
  `_trim_version_history`, which is at **:264** at `cac6edc`; `_braces_outside_fences` is still
  **:109**). Task #102. **Routing: impl-plan** re-pins `:247` → `:264` at every site (a stale pin that
  the moved provenance no longer flags is the #29 class — re-pin, do not merely re-stamp), re-verifies
  `:109`, and ships with `PRECHECK` hard findings ≤ 12 (the 11 grammar slots stay; `PINDRIFT` must be
  0). No other document is affected: no document publishes a present-tense "N passed" for the
  current suite (the `2747`/`2748 passed` sites are historical). Present-tense figures at `cac6edc`
  remain: **2574** collected from `h-mad/`, **2836** from the repository root, **1527** `def test_`
  lines, **89** test files. Nobody writes "2574 passed": the orchestrator re-runs the suite on the
  batch tree after collection and stamps that reading (FACT 2 clause 3). Authors do NOT run the
  full h-mad suite (four concurrent runs on one pin file); `--collect-only -q` and `git grep -h
  '^def test_'` are fine.
  (ii) **FACT 2 clause 1's parenthetical ("the parent of the commit that will land this batch") is
  stale.** The freeze field stays **`cac6edc`**; HEAD at dispatch is the commit that carries this C2
  (`git rev-parse HEAD` — the authors are told it verbatim in their prompt). `git diff --name-only
  cac6edc..HEAD` is docs-only: this sheet, `docs/handoffs/2026-09-05-main__doc-block-exec-r18-sheet.md`,
  `docs/handoffs/2026-09-05-main__hmad-audit-loop-evidence-from-gateway-consolidation.md`
  (`**Taken-Over-By:**` stamped), `docs/learnings.md`. No scoped census moved, and no document
  publishes the unscoped `git ls-files | wc -l` (value grep for 3666/3668/3670/3671: 0 in all four).
  Do not "correct" the freeze to HEAD.
  (iii) **Shared strings, decided once — paste, do not paraphrase.**
  - Tagged pair: `(kind, a, b, offset|None)`; `kind ∈ {"overlap", "intersect"}`; detail lines
    `overlap: "<a>" "<b>"` and `intersect: "<a>" "<b>" "<offset>"` are the grammar (slots stay);
    the r18 fixture instance is `intersect: "aa" "ab" "2"` for text `aaab` under keys `{aa, ab}`,
    found by the lookahead scan `re.finditer(r"(?=" + re.escape(k) + r")", text)` with span
    `(m.start(), m.start() + len(k))`.
  - AC-3.14 asserts `__cause__ is cleanup_error`; every `__suppress_context__` sentence goes
    (8 sites: design 4, impl-plan 4).
  - `LaunchFailed.__init__` err annotation: `OSError | subprocess.TimeoutExpired | ValueError`.
  - The empty-ATX-heading case (FACT 3) is exercised by a `tmp_path` fixture (the feature's tests use
    `tmp_path`, never a committed `tests/fixtures/` file — value grep: `tests/fixtures/` 0 in design
    and impl-plan, `tmp_path` 7/8): test `test_titleless_heading_is_a_new_only_member` in
    `h-mad/tests/test_h_mad_doc_block_exec.py`, writing `titleless.md` with body `before\n#\nafter\n`
    and asserting `titleless=1 new_only=1` on that file alone. Design names it; impl-plan carries it as
    a test row; spec does not mention it.
  - The FACT 3 residual, in these words: "At `cac6edc` the `new_only` set is empty, so 'each
    `new_only` member is a heading under CommonMark' is vacuously true there; it was verified
    non-vacuously at `fbc2ea0` (N=1, the `h-mad/SKILL.md` specimen removed by `b39d9dc`) and is
    exercised by `test_titleless_heading_is_a_new_only_member`."
  - The 85 mutation rows are the impl-plan's value at `cac6edc`; the plan writes **85**. If the
    impl-plan's revision moves it, the impl-plan's tail says "plan owes N" and the orchestrator
    reconciles at collection.
  (iv) **Every `:N` in this sheet is a READ locator for the author, never text to copy.** Design
  writes no line numbers (its rule 2). Impl-plan cites `h-mad/references/codex-implementer-prompt.md`
  by needle ("by construction"), never `:52`. Task #29 is a suite failure from a copied pin.

- **C3 — appended 2026-09-05 by session `adb05ac8` after the batch landed as `ccd8ebd` (design v1.110 /
  plan v1.105 / impl-plan v1.54 / spec v1.64), before gating.**
  (i) **Suite stamp (C2 i's promised reading):** `pytest h-mad/tests -q` at `ccd8ebd` → **`2574 passed in
  377.47s`**; RED span was `b39d9dc..f6849bb`. Precheck at `ccd8ebd`: spec / design / plan `PASS issues=0`;
  impl-plan `FAIL issues=11`, all 11 `PLACEHOLDER` design-grammar slots, `PINDRIFT` 0 (the noise-floor
  test asserts ≤ 12 and passes).
  (ii) **Sheet premises the authors falsified, recorded so the gating legs do not re-file them as new:**
  FACT 5 "five spec ACs never named" — **seven** (AC-1.2 and AC-3.2 as well); a value grep over five
  guessed labels was the wrong instrument, the design's AC-range expansion prints `spec 49 covered 49
  uncovered [] not-in-spec []`. FACT 5 "Task 2 nine/ten" — **eleven**, derived (twelve distinct test
  names less one Task 4 forward reference). FACT 4 (c) "AC-3.14 asserts `__suppress_context__ False`" —
  the SPEC never carried that assertion (`git show cac6edc:<spec> | grep -c __suppress_context__` → 0);
  the assertion lived in the impl-plan (1 site, now withdrawn) and the design's four sites were prose /
  a probe column / a mutation-row description (kept as prose, 10 body sites at `ccd8ebd`, with the
  assertion rule stated at AC-3.14). FACT 8 spec cell `__suppress_context__` 0 → **2 by design**: an AC
  that forbids an assertion names it. C2 iii's residual sentence was handed to the authors with SINGLE
  quotes around 'each `new_only` member …' while two of three authors wrote double quotes — plan delta
  must 3, resolved to double everywhere. **Orchestrator error #49v**: a shared string carried a quote
  style the documents do not use; a shared-facts gate must paste a string in the documents' own spelling.
  (iii) **Two collisions only the orchestrator could see (rule 3), both resolved in reopen 1:** the design
  ADDED matrix row 17 `intersect-scan-non-overlapping` (matrix 85 → **86** = 85 helper + 1 SKILL.md; the
  plan's published awk prints `total=85` at `cac6edc` and `batch total=86` on the shipped design; the
  plan and impl-plan carry 86 at this batch, 85 at `cac6edc`); and its killer test was named two ways —
  design `test_substitute_refuses_overlapping_occurrences_of_one_key`, impl-plan
  `test_intersecting_spans_need_an_overlapping_scan` — the design's name won (impl-plan renamed 2 sites;
  the old name is 0 in every body).
  (iv) **Advisory delta reviews** (`docs/03-analysis/doc-block-exec.{spec,plan,impl-plan,design}.delta-review.r18.md`,
  committed with the batch): must **2 / 3 / 2 / 5**, every one in the self-measurement or Version History
  layer, none in the substantive decisions; all closed in reopen 2. The fix round introduced the class it
  hunted (#11's premise, measured again).
  (v) **Measurable facts for the r18 gating legs (state, do not suppress):** the plan binds the word
  "freeze" to `4e4a00c` by its own convention (16 sites) and stamps every r18 reading "the measurement
  commit `cac6edc`" — `the freeze `cac6edc`` is 0 there by design; the impl-plan spells AC-3.14 as
  "`__cause__` **is** the injected cleanup error, asserted with `is`" rather than the literal
  `__cause__ is cleanup_error` (spec 1, design 3 carry the literal); the impl-plan's 11 precheck
  `PLACEHOLDER` findings are the FR-4 grammar slots (`overlap: "<a>" "<b>"`, `intersect: …`,
  `os_error: "<text>"`, `pgid: "<n>"`, `stream: "<name>"`, `<key>=…`) and are declarations; "N passed"
  in the present tense is written by nobody but this sheet (C3 i) — the documents publish COLLECTION
  counts (2574 / 2836) at `cac6edc`.
  (vi) **Freeze for gating = the commit carrying this C3** (docs-only over `ccd8ebd`: this sheet; no
  scoped census moves; no document publishes the unscoped `git ls-files | wc -l`). Design **c98** / plan
  **c89** / impl-plan **c49**, `--vh-tail 3` (`--vh-tail 1` if the assembler HALTs `oversize`), codex via
  `hmad-dispatch exec … --sandbox read-only --timeout 1800 --log` plus one `doc-auditor` GATING leg per
  phase told freeze + HEAD; no agy leg (#77).

- **C4 — appended 2026-09-06 by session `51a2b6f7` at dispatch of the r18 gating round (before any
  leg reported).** (i) **Freeze `bc4688e`, HEAD `093c3ee`**; `git diff --name-only ccd8ebd..bc4688e`
  is this sheet alone, `bc4688e..093c3ee` is the handoff doc + `docs/learnings.md`; no phase document
  moved since `ccd8ebd`. Precheck at HEAD: spec / design / plan `PASS issues=0`; impl-plan `FAIL
  issues=11`, all `PLACEHOLDER` on the FR-4 grammar slots (`overlap:` ×2, `intersect:` ×2, `os_error:`
  ×3, `pgid:`, `stream:`, `<key>=<bare>`, `<key>="<json-string>"`), `PINDRIFT` 0 — **dispatched over the
  skill's `PRECHECK: FAIL → re-dispatch the author` rule by decision**, C3 i's reading unchanged and
  the noise-floor test's ≤ 12 floor passing; the slots are grammar declarations, not unfilled
  placeholders. (ii) **The brief is IN the prompt, both surfaces alike:** a derived template (stock
  `h-mad/audit-prompt.template.md` + one 12-line "Orchestrator cycle brief" block after the
  Target/Paired lines, nothing else; `diff` verified) carries C3 v's facts, each RE-DERIVED at HEAD
  before it was written — three of them hold only body-scoped (the plan's "the freeze `cac6edc`", the
  old killer-test name, and the spec's `__suppress_context__` count each have one extra hit INSIDE a
  Version History entry: plan:4548, plan:4548, spec:1484) — and the block says in so many words that
  the facts are to weigh, not to withhold a finding; a leg that files against one tags it
  `orchestrator-stated`. (iii) **Sizes (READ before dispatch):** design `--vh-tail 3` HALTs `oversize`
  at 1,104,925 chars (r17's 1,027,802 + the batch's +384 design lines + the brief); **both design legs
  re-assembled at `--vh-tail 1`** → 980,076 chars (985,605 B); plan c89 at 3 → 629,855 chars; impl-plan
  c49 at 3 → 1,002,731 chars (1,007,799 B, 46 KB under the 1,048,576 ceiling). Same tail per phase on
  both surfaces so the union gates one prompt content. Residual preflight over all six: 0 `<INLINE_`,
  0 `{{ONLY`, brief present once, report path present. (iv) **Dispatch:** codex ×3 via
  `hmad-dispatch exec codex <prompt> --cd <root> --sandbox read-only --out … --log … --timeout 1800`
  backgrounded, stdout captured to `…_codex.stdout.txt`; `doc-auditor` GATING ×3 by prompt path
  (report-file transport). Six report paths, none shared. No agy leg (#77). Codex pin `term_f483657a`
  read `state=done` at `env`; quota state unknown at dispatch (memory: window reopens 2026-09-07
  11:28) — the codex logs are read for `usage limit` before any codex leg is called failed.
  (v) Orchestrator error caught before it cost anything: the zsh `set -- $spec` loop (C3's own
  warning) produced six `invalid choice: 'design 98'` usages on the first assembly pass; re-run with
  explicit arguments. (vi) Tree frozen for the round: this append is the only repository write until
  all six legs are collected and scored.

- **C5 — appended 2026-09-06 by session `51a2b6f7` after all six r18 gating legs were collected and every
  must re-derived by the orchestrator.** (i) **Verdicts at freeze `bc4688e` (HEAD `093c3ee`), six reports
  collected, none shared:** plan c89 codex `FAIL must=1 should=3` (via `--out`) / teammate `FAIL must=2
  should=4` (report-file, 12 files / 71 greps); design c98 codex `FAIL must=3 should=2` (`--out`) / teammate
  `FAIL must=4 should=2` (report-file, 13 / 46); impl-plan c49 codex `FAIL must=4 should=3` (`--out`) /
  teammate `FAIL must=2 should=2` (report-file, 26 / 61). All three codex legs delivered via `--out` and
  wrote no report file (read-only sandbox, as r16/r17); 0 `usage limit` hits — the 09-03 quota window
  did not bind. **ROUND FAILS on all three phases.** (ii) **Every must verified (16/16), each by an
  executed probe or a read of the shipped bytes, none by reasoning alone:** plan codex M1 — the
  `h-mad/SKILL.md` bare-`#` specimen is 0 at `1861157` (09-04 08:02) and 1 from `bea1b60` (09-04 12:14),
  so the `1861157` zero was a TRUE zero and plan:3462 mis-explains it; plan teammate M1 — the ledger
  pipelines read 87/87 at `fbc2ea0` and **88/88** at `cac6edc`, `ccd8ebd`, `bc4688e`, `093c3ee` (overlaps
  codex should 3); plan teammate M2 — plan:4340 says eight shas, the fenced series at :4359-4362 lists ten.
  Design codex M1 — the 13,104-case search publishes no command (the four `fbc2ea0` probes are other
  things; the r18 delta review reproduced 13,104/194 but a reviewer's reproduction is not the document's
  command); design codex M2 — `communicate(timeout=-1)` raises **`TimeoutExpired`** on 3.11.8 AND 3.14.7,
  design:1854's `ValueError` claim is FALSE; design codex M3 == impl-plan codex M2 — a fake `rmtree` that
  raises unconditionally raises under `ignore_errors=True` too (probed), so `cleanup-errors-ignored` is
  NOT killed by `test_cleanup_failure_carries_the_os_error` as design:1825 / design:4056 claim — **found
  independently by the codex leg in BOTH documents, the r16 pattern again**; design teammate M1 — the
  design's own trip-wire `git diff --name-only a8e0372 <sha> | grep '\.md$' | grep -vc '^docs/'` (`# expect
  0`, design:284) reads **8** at `cac6edc`/`ccd8ebd`/`bc4688e`/`093c3ee` (`h-mad/SKILL.md`, five
  `h-mad/agents/*.md`, two `h-mad/references/*.md`, all `b39d9dc`) and no reading records it; design
  teammate M2 — `git diff --name-only b39d9dc^ b39d9dc -- h-mad handoff` = 13 files incl `h-mad/SKILL.md`,
  `-- '*.py'` = 4, so "b39d9dc passed every scoped census predicate" (design:386) is FALSE; design teammate
  M3 — `shared by *any* intersecting span pair` design 1 / spec 1 / impl-plan **0**, `the two spans SHARE`
  impl-plan 3 at HEAD (:2094, :2463 body, :4146 VH) vs 2 at `cac6edc` — the batch ADDED a retired-wording
  site (same axis as impl-plan codex S3 and impl-plan teammate S1: three legs, one defect); design
  teammate M4 — `intersections` 5 whole-file (2 body :1436/:2955 + 3 in the v1.110 entry), design says 4.
  Impl-plan codex M1 — impl-plan:3178 prescribes a subprocess CLI call with a `--preamble` argument
  containing `\x00`; `subprocess.run(['/bin/echo','a\x00b'])` raises `ValueError: embedded null byte` in
  the PARENT, the test cannot reach the CLI; impl-plan codex M3 — Task 1's
  `test_invalid_utf8_document_is_unreadable` (:2334) gains its CLI half in Task 4 (:3163) while Task 4's
  RED gate (:3413) says "Tasks 1–3 stay green" and `--expect-pass` = Task 3's GREEN figure (:3388) — off by
  one in both clauses; impl-plan codex M4 — impl-plan defers a kind-selection rendering mutation row to the
  design (quote present); impl-plan teammate M1 — the committed probe
  `heading_differential.2026-09-04.b66afa9c.py` prints `TRACKED files=30 both=292 old_only=82 new_only=0`
  at HEAD while impl-plan:1701/:1703 publish 25/263/76/268 in present tense with "no round having re-run
  them" — the plan retired that figure at `cac6edc` in the SAME batch (#42 class); impl-plan teammate M2 —
  `ast.parse` over the impl-plan's fenced python blocks: 8 parse, the Task 4 code-structure block (:3120)
  raises `SyntaxError` at :3153 (three bodiless `def`s :3152-:3154). (iii) **Union:** plan 3 distinct /
  design 7 / impl-plan 6, less the rmtree pair counted once = **15 distinct musts**; the two families found
  DISJOINT must sets on the design and the impl-plan for the third round running (r16, r17, r18), and
  agreed on the plan only through a codex should. (iv) **The brief:** no report carries an
  `orchestrator-stated` tag and no leg filed against a C3 v fact; the design teammate re-ran every
  executable self-measurement the design publishes and every one reproduced — every design must is in
  the stamping/routing layer, and every codex must is a design-logic or test-discrimination claim.
  (v) **Orchestrator error #49w:** C2 ii, C3 vi and C4 i each certified "no scoped census moved" over
  `b39d9dc`, and the DESIGN's own published trip-wire (design:284) had fired to 8 at that commit; three
  sheet entries asserted a predicate the documents publish a command for, and none of them ran it. Same
  root as #49t (#81) — a tooling commit under `h-mad/` moves every scoped census — now at the sheet layer
  rather than the freeze layer. Two near-misses caught before cost: zsh `$s:h-mad/…` parsed `:h` as the
  dirname modifier and every per-sha specimen count read 0 (re-run as `${s}:`); and the C3-warned
  `set -- $spec` loop reappeared in the first assembly pass. (vi) **Routing for the r19 batch (one
  decision each, stated once):** DESIGN — (a) commit the 13,104/194 enumeration as a fifth probe under
  `docs/03-analysis/probes/doc-block-exec/` and cite it; (b) correct :1854 to `TimeoutExpired` and publish
  the paired probe; (c) **DESIGN CHANGE:** the `rmtree` fault-injection contract for `cleanup-errors-ignored`
  must honour `ignore_errors` (raise only when `ignore_errors` is falsy) or name a different discriminating
  fixture — impl-plan follows; (d) stamp the trip-wire at 8 with the eight paths and `b39d9dc`, state which
  `a8e0372`-stamped figures were re-derived; (e) :386 ground sentence — `b39d9dc` did NOT pass the scoped
  predicates, the fixture decision stands; (f) owed-elsewhere entry for the `<offset>` wording naming
  impl-plan :2094/:2463; (g) `intersections` 4 → 5 in the v1.110 self-count; (h) decide the kind-selection
  rendering row (impl-plan codex M4) — add it or state why the matrix does not carry it. PLAN — (a) :3462
  the `1861157` zero was a true zero (specimen absent until `bea1b60`), separate it from the `closing_hash`
  mis-corpus story; (b) ledger row `cac6edc` **88/88**, restamp, deixis "v1.104's measurement commit";
  (c) eight → ten (or "the shas listed below"). IMPL-PLAN — (a) the NUL `--preamble` arm goes through
  `--preamble-file`; (b) follow design (c); (c) split the CLI half of `test_invalid_utf8_document_is_unreadable`
  into its own Task 4 test, or carry the moved test in both RED counts; (d) follow design (h);
  (e) 25/263/76/268 → 30/292/82/0 stamped `cac6edc`, withdraw "no round having re-run them"; (f) ` ...` on
  :3152-:3154 and add the `ast.parse` screen beside the GNU sweep; (g) reword :2094/:2463 to the any-pair
  offset. SPEC — no findings; the any-pair offset wording already lives in it. Shoulds travel with their
  document. Freeze for the r19 batch = the commit carrying this C5.

- **C6 — appended 2026-09-06 by session `51a2b6f7` after `d27d2ce` landed the six reports (correction to
  C5 vi, and the two audit inputs made durable).** (i) **The r19 freeze moves the plan's ledger figure
  again, by the orchestrator's own commit:** the plan's two `git ls-tree` pipelines read **88/88** at
  `bc4688e` and **89/89** at `d27d2ce` (the r18 gating reports land under `docs/01-plan/features/`; the
  plan calls this figure "stale by construction the moment the next report is written"). C5 vi PLAN (b)
  is therefore: series gains `cac6edc` **88/88** AND `d27d2ce` **89/89**, headline restamped at the r19
  freeze. The design's trip-wire still reads 8 at `d27d2ce`. Body sweep for `v48`/`v88`/`v97` outside
  Version History: spec 0, plan 1, impl-plan 10, design 0 — the impl-plan's are attributions ("impl-plan
  audit v48 codex must 1"), to be re-read by its author for any present-tense "latest report" site, not
  bulk-replaced. (ii) **Instrument note (#62 class):** C5 ii says the impl-plan's fenced python blocks are
  "8 parse, one fails"; the teammate report says "nine of ten". Two fence grammars (the orchestrator's
  accepts only a bare ```` ```python ```` opener at 0–3 spaces; the auditor's counted one more block), one
  defect. The r19 impl-plan author's `ast.parse` screen must state its fence grammar and publish its own
  count. (iii) **Audit inputs now in the repo:** the 12-line orchestrator brief spliced into both
  surfaces' prompts is `docs/03-analysis/doc-block-exec.r18-gating.orchestrator-brief.md`; the
  per-must verification ledger is `docs/03-analysis/doc-block-exec.r18-gating.verification-ledger.md`.
  (iv) **Not pushed:** `d27d2ce` and this commit are local; `origin/main` is at `093c3ee` until the
  session closeout pushes.

- **C7 — appended 2026-09-06 by session `51a2b6f7` before the r19 authors were spawned: the shared-facts
  gate for the r19 revision batch (the C2 construction; every string below is pasted from the shipped
  bytes, never retyped — #49v).**
  (i) **Freeze = the commit carrying this C7** (docs-only over `c7a75eb`, which is docs-only over
  `d27d2ce`, which landed the six r18 gating reports). Authors are told the sha verbatim. FACT 2's three
  clauses apply unchanged. **Two waves:** design-author and plan-author in parallel first; implplan-author
  AFTER the design's DONE, handed the design's shipped strings for the fault-injection contract and the
  kind-selection row — the r18 rule-3 collisions (matrix 85→86, one killer test named two ways) came from
  two authors filling one undecided string at once. spec-author is not dispatched (no r18 finding lands
  in the spec; its any-pair wording is the source string below). Target versions: design **v1.111**, plan
  **v1.106**, impl-plan **v1.55**; spec stays v1.64. Authors do NOT run the full h-mad suite (concurrent
  runs on one pin file); `--collect-only -q` and `git grep` are fine; the orchestrator runs the suite on
  the committed batch tree and stamps that reading. Precheck floor: impl-plan ≤ 12 hard (the 11 grammar
  `PLACEHOLDER` slots stay), `PINDRIFT` 0; spec / design / plan `PASS issues=0`.
  (ii) **Shared strings, decided once.**
  - **The any-pair offset wording, source = spec body (`grep -nF 'any* intersecting span pair'` → spec:183):**
    `**`<offset>` is the smallest character index shared by *any* intersecting span pair of` … ; the
    design's body spelling (design:1408-1409) is `<offset>` is the **smallest character index shared by
    *any* intersecting span pair of the two keys**, 0-based into `block.text`. The impl-plan rewords its
    two body sites (`grep -nF 'the two spans SHARE'` → impl-plan:2094 and :2463; the :4146 hit is
    Version History and stays) to that form; the design adds an owed-elsewhere entry naming those two
    sites by command.
  - **The `cleanup-errors-ignored` fault-injection contract — DESIGN CHANGE, the design author writes it
    once and the impl-plan author copies the shipped sentence:** the injected `rmtree` must **honour
    `ignore_errors`** — raise the injected error only when `ignore_errors` is falsy, return silently when
    it is true — so that under the mutant (`ignore_errors=True` restored) nothing raises, nothing is
    recorded, the read-back trips and `cleanup_error` is `None`, which is what
    `test_cleanup_failure_carries_the_os_error` then discriminates. Probe (both surfaces filed it):
    a fake that raises unconditionally raises under `ignore_errors=True` too, so the row's `killed by` at
    design:1825 and the matrix row at design:4056 are not currently true. Any other discriminating
    fixture the design author prefers is acceptable; whichever it is, the impl-plan follows the design.
  - **`communicate(timeout=-1)`:** on Python 3.11.8 AND 3.14.7 it raises **`subprocess.TimeoutExpired`**
    (a normal non-positive timeout expires immediately); `timeout=1` on `sh -c 'exit 0'` returns. The
    design:1854 claim that it raises `ValueError` only after the child exists is FALSE and is corrected
    to `TimeoutExpired`; the AC-5.6 validation rule (`math.isfinite(t) and t > 0`, else `BadTimeout`)
    stands and is now grounded on "the refusal must happen before the spawn because `communicate` would
    NOT refuse it".
  - **The trip-wire reading (design:284 fence, `# expect 0`):** **8** at `cac6edc`, `ccd8ebd`, `bc4688e`,
    `093c3ee`, `d27d2ce`, `c7a75eb`; the eight are `h-mad/SKILL.md`, `h-mad/agents/design-author.md`,
    `h-mad/agents/doc-auditor.md`, `h-mad/agents/implplan-author.md`, `h-mad/agents/plan-author.md`,
    `h-mad/agents/spec-author.md`, `h-mad/references/agent-substrate.md`,
    `h-mad/references/codex-implementer-prompt.md`, all changed by `b39d9dc`. `git diff --name-only
    b39d9dc^ b39d9dc -- h-mad handoff` names 13 files including `h-mad/SKILL.md`; `-- '*.py'` names 4
    (`h-mad/scripts/h_mad_assemble_audit.py`, `h-mad/tests/test_h_mad_agent_definitions.py`,
    `h-mad/tests/test_h_mad_assemble_audit.py`, `h-mad/tests/test_hmad_dispatch_exec.py`). design:386
    "`b39d9dc` passed every scoped census predicate" is FALSE; the fixture decision it grounds stands.
  - **The heading differential at `cac6edc`, plan's spelling (plan:3401):** TRACKED `files=30 both=292
    old_only=82 new_only=0`, `setext_headings=0`; GLOB `files=35 both=297 old_only=82 new_only=0`.
    The impl-plan's 25 / **263** / `old_only=76` / **268** at impl-plan:1699-1703 and its "no round having
    re-run them" clause are replaced by that reading stamped `cac6edc`; the committed probe is
    `docs/03-analysis/probes/doc-block-exec/heading_differential.2026-09-04.b66afa9c.py`.
  - **The plan ledger pair (plan's own two `git ls-tree` pipelines at plan:4350-4355):** `fbc2ea0` 87/87 ·
    `cac6edc` **88/88** · `ccd8ebd` 88/88 · `bc4688e` 88/88 · `093c3ee` 88/88 · `d27d2ce` **89/89** ·
    `c7a75eb` 89/89 · the r19 freeze 89/89. The series at plan:4359-4362 carries TEN shas; plan:4340
    says eight.
  - **The `h-mad/SKILL.md` bare-`#` specimen by commit** (`git show "${s}:h-mad/SKILL.md" | grep -c
    '^#[[:space:]]*$'`): `a469493` 0 · `1861157` 0 (09-04 08:02) · `bea1b60` 1 (09-04 12:14) · `fbc2ea0` 1
    · `cac6edc` 0. The `1861157` zero at plan:3462 was a TRUE zero (the specimen did not yet exist), not
    "the shape had not been looked for correctly"; the `closing_hash` mis-corpus story is a different zero.
  - **The 13,104 / 194 search:** the design publishes no command (design:1516-1519 "run rather than
    reasoned"); the r18 design delta review reproduced `52 non-substring pairs × 252 texts = 13,104`,
    `194` lookahead-only refusals, `0` missed. The design commits the enumeration as a fifth probe under
    `docs/03-analysis/probes/doc-block-exec/` (the author writes the probe file — the ONE exception to
    one-author-one-file this round, stated here so nobody else touches that directory) and cites it.
  - **`intersections` in the design:** whole-file 5 (body design:1436, design:2955; three in the v1.110
    entry), body 2, `cac6edc` 0; the v1.110 self-count "on this body 4" → re-derived.
  - **impl-plan Task 4 code-structure block (impl-plan:3120 fence):** `ast.parse` raises at :3153; the
    three bodiless `def`s are :3152-:3154; ` ...` before the trailing comment, matching `_verify` at :3155.
    The ast screen the author adds MUST state its fence grammar (opener ```` ```python ```` at 0–3 spaces,
    closer a bare fence) and publish its own count — the orchestrator's instrument counted 9 fences, the
    auditor's 10; one defect, two grammars.
  - **The NUL `--preamble` arm (impl-plan:3178):** a `\x00` inside an argv element raises `ValueError:
    embedded null byte` in the PARENT (`subprocess.run(['/bin/echo','a\x00b'])`, probed) — the test never
    reaches the CLI. The second arm goes through `--preamble-file` with the NUL written into the file.
  - **Task 4 RED count (impl-plan:2334 / :3163 / :3388 / :3413):** `test_invalid_utf8_document_is_unreadable`
    is a Task 1 test that gains a CLI assertion in Task 4, so "Tasks 1–3 stay green" and `--expect-pass` =
    Task 3's GREEN figure are both off by one. Decision: the CLI half becomes its own Task 4 test (name
    chosen by the impl-plan author; value-grep it across all four documents at collection).
  - **Kind-selection rendering row (impl-plan codex M4):** the DESIGN decides — add a matrix row that
    changes only the `kind`-based prefix selection in the renderer and name its killer (the CLI
    detail-line test), or state in the matrix section why the matrix does not carry it. The impl-plan
    follows the shipped design in wave 2.
  (iii) **Every `:N` above is a READ locator, never text to copy** (C2 iv). Design writes no line
  numbers. (iv) **Reopen rule (FACT 6) and version-number rule (FACT 7) apply.** (v) **Should-fixes
  travel with their document** — plan: softened-set GLOB `closing_hash=5` claim, 81/81 at `09e9307`,
  "the register below" pointer, three repo-wide `.py` figures outside the re-run set (415 / 5 / 2,
  unchanged), changed-`.py` 6 → 8 at `cac6edc`, batch stamp now dischargeable at `ccd8ebd`; design:
  88 → 89 test files at `cac6edc`, AC fence reads the spec blob at `cac6edc` while the batch ships
  v1.64 (sets identical), `$P` 40 vs 37, the AC census command returning 0 not 7; impl-plan: the
  six-record `abc` fixture, the five-row collateral enumeration, `abc---abc` offset 1 not 7, Task 5
  "alone" scope, `overlap:` slot spelling, the discharged `intersect:` row debt. Nits with them.

- **C8 — appended 2026-09-06 by session `51a2b6f7` BEFORE any r19 verdict exists (written blind, per the
  rule it states): the finding-class rule, the r18 partition under it, and the operator's cap decision.**
  (i) **The class test, one question:** *would the code or tests a 5d/5e implementer writes differ if
  this finding were fixed?* Yes → `build`. No → `measurement`. Reviewers state it on a `class:`
  continuation line from r20 on (template + gate change on `feature/hmad-class-scored-gate`, not yet
  merged); for r19 the orchestrator applies the test to each collected must and may re-classify only
  `measurement` → `build`, never the reverse. (ii) **The r18 union under that test, 15 distinct:**
  build **6** — the `rmtree` fault-injection contract (design codex M3 = impl-plan codex M2, counted
  once), the NUL-in-argv `--preamble` arm (impl-plan codex M1), the Task 4 RED count over a modified
  Task 1 test (impl-plan codex M3), the kind-selection rendering row (impl-plan codex M4), the
  unparsable Task 4 python block (impl-plan teammate M2), the any-pair `<offset>` wording the impl-plan
  contradicts (design teammate M3); measurement **9** — the `1861157` zero's explanation (plan codex
  M1), the ledger 87/87 → 88/88 (plan teammate M1), eight vs ten shas (plan teammate M2), the
  13,104-search command (design codex M1), the `communicate(timeout=-1)` ground sentence (design codex
  M2 — the AC-5.6 rule an implementer codes against is unchanged), the trip-wire stamp (design teammate
  M1), the `b39d9dc` ground sentence (design teammate M2), `intersections` 4 → 5 (design teammate M4),
  the stale heading-differential figures (impl-plan teammate M1). Under the class rule r18 would have
  read build 6 / measurement 9, and the plan would have gated on build 0 — its only build-class item
  was the ledger, which is measurement. (iii) **Operator decision, 2026-09-06: r19 is the LAST document
  round for this feature.** Stated reason: eighteen rounds, zero code; Phase 5 (RED/GREEN, the mutation
  harness, 6a-prime) is where a defect costs minutes because pytest is the oracle. Consequences,
  decided now: (a) after the r19 batch lands, ONE gating pass — codex gates each changed document
  (design c99 / plan c90 / impl-plan c50, `--vh-tail` as the assembler requires, the OLD template);
  the doc-auditor runs the advisory delta review on each diff and does NOT run a second full gating
  pass (the delta layer is where 12 of 12 fix-introduced musts lived at r18); (b) every measurement-class
  must or should from that pass is acknowledged in a `## Acknowledged-not-fixed` sidecar
  (`.audit.v<N+1>.md`, committed `[audit-override]`) with its RE-RUN COMMAND as the ack text; (c) any
  build-class must from that pass is carried as an explicit open item in the impl-plan's Tasks
  (a design/test decision the implementer resolves in 5d, where a wrong choice is a RED failure) — it
  does NOT open a twentieth document round; (d) 5b is stamped at the commit that carries the sidecars,
  and 5c/5d begin on that tree. (iv) **Skill-side, on the branch:** a hard cap of two gating rounds
  per document audit loop, re-audit only documents that changed since their last gate, codex gates
  while the same-family surface reviews the diff, Phase 5 as the gate. These land after the r19 gating
  pass is collected (any `h-mad/` commit moves the design's trip-wire and the plan's `.py` censuses).
