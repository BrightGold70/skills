# doc-block-exec — round seventeen decision sheet (shared facts for the r17 revision batch)

**Status:** input to FOUR parallel authors. Not a gate. Stamps nothing.
**Freeze:** `fbc2ea0` (HEAD, pushed). Checked with the documents' own closure predicates, not
byte-identity alone: `git diff --name-only af19d53 fbc2ea0 -- h-mad handoff` prints **nothing**, so every
reading the four documents stamp at `af19d53` holds at `fbc2ea0`; `git diff --name-only 74e126f fbc2ea0
-- h-mad handoff` prints the same **2** files it printed at `af19d53` (the assembler and its test). The
tracked corpora (`git ls-files -- h-mad handoff`) are unchanged. The h-mad suite at `fbc2ea0`:
**2552 passed** (`/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests/ -q -p no:cacheprovider`, 378 s).
The four documents are byte-identical from `09e9307` through `fbc2ea0`; the commits between touched
audit reports, one handoff, and `docs/03-analysis/probes/doc-block-exec/` (FACT 7).

**Inputs per author** (read every report in full — the gate needs `should=0` too, so the should column
is not optional):

| author | document | gating reports at freeze `09e9307` (must / should) |
|---|---|---|
| design-author | design v1.108 → v1.109 | `docs/02-design/features/doc-block-exec.design.audit.v96.teammate.md` (2 / 3) · `…v96.codex.md` (3 / 3) |
| plan-author | plan v1.103 → v1.104 | `docs/01-plan/features/doc-block-exec.plan.audit.v87.teammate.md` (4 / 4) · `…v87.codex.md` (2 / 2) |
| implplan-author | impl-plan v1.52 → v1.53 | `docs/01-plan/features/doc-block-exec.impl-plan.audit.v47.teammate.md` (4 / 4) · `…v47.codex.md` (6 / 2) |
| spec-author | spec v1.62 → v1.63 | no report of its own (the spec has no audit phase); it is revised by the FOUR cross-document decisions in FACT 3 — AC-2.7, AC-1.8, the NUL launch failure, the ninth seam |

**Your run outranks this sheet.** Over rounds twelve to sixteen an author refuted the orchestrator's sheet
in every round. If a fact below disagrees with your own run, your run wins and the disagreement is a
finding — report it first.

## FACT 1 — two model families, two defect populations. Route them differently.

Round sixteen was the first with codex AND the teammate leg on every phase. They found **different
things**: the teammate legs filed the standing prose class (a stamp applied wider than its condition, a
span off by one, a wrong section name, a self-reference screen red on its own text); codex filed
**engineering defects in what the documents specify** — an algorithm that returns `Xc Xc` while both
counts read 2, a `raise … from None` that suppresses context instead of selecting a fallback, a payload
that raises `ValueError: embedded null byte` with no verdict path, a `new_only=0` invariant false on the
live tree. Fix the prose class as prose. **Treat the codex class as DESIGN CHANGES**: each one moves a
contract in two or more documents at once, so the shared decision for each is stated in FACT 3 and every
author implements the same decision. A codex must whose premise does not reproduce is a finding about
codex; report it, do not apply it (two premises are already corrected in FACT 3: I6's mechanism, and the
09-03 probe version).

## FACT 2 — the freeze-sha rule, three clauses (carried verbatim from r16; it was not violated in r16)

1. **An entry's own freeze-sha field** names the last commit before the batch was authored — here
   `fbc2ea0`, the parent of the commit that will land this batch.
2. **A reading of a committed blob** stays stamped at that blob (`b3be433`, `00b961f`, `3f70eb3`,
   `af19d53`, `09e9307`, …). It does not move when the freeze moves.
3. **A reading taken over this revision's own post-edit body** is stamped to *the tree this revision
   ships* (or "the working file after the v1.NNN entry below was written") — **never** to `fbc2ea0`,
   which does not contain your edits.

## FACT 3 — the codex class: orchestrator verification and the ONE decision per item

Every author touching an item below implements the decision as written. A better decision is welcome —
but it is reported in your tail before you write it, so the sibling authors can be told; a silent
divergence is the c97 contradiction.

**3a. Intersecting substitution spans — design must 1, impl-plan must 1, spec AC-2.7. VERIFIED.**
Reproduced on Python 3.11.8 with the prescribed escaped-alternation regex and a recording callback:
`abc abc` under `ab→X, bc→Y` → `Xc Xc`, `text.count` reads `ab=2 bc=2`, the callback fired `ab=2
bc=0`; `abc` → `Xc`, counts 1/1, fired 1/0; control `ab bc ab bc` → `X Y X Y`, 2/2, fired 2/2. The
map-static substring check (`any(a != b and a in b)`) is **False** for `{ab, bc}`, so AC-2.7 as written
does not reach it.
*Decision:* the span-intersection check is **added beside** the substring check, not substituted for it —
they are different predicates (`ab`/`abc` with no `abc` in the text is substring-refused and not
span-refused; `ab`/`bc` in `abc` is the reverse). Both refuse under the existing `SUBST_OVERLAP` token,
exit 0, nothing executed. `keys=<n>` keeps counting **distinct keys implicated** across both kinds.
Detail lines: the existing `overlap: "<shorter>" "<longer>"` for the substring kind; a new
`intersect: "<a>" "<b>" at <offset>` for the span kind, one per unordered pair, `<offset>` the 0-based
index into `block.text` of the FIRST intersecting occurrence, sorted by `(offset, a, b)`. The
intersection scan runs on the original `block.text` before any replacement (all match spans of all keys
collected; any two spans from different keys that share an index intersect). Spec AC-2.7 gains the second
clause; the design's token table row gains the second detail-line kind; the impl-plan adds
`test_substitute_refuses_intersecting_spans` (fixture `abc` + `{ab→X, bc→Y}` refuses; control `ab bc ab
bc` substitutes with counts 2/2) and mutation row `intersect-check-removed` killed by it. The class is
"two keys' matches are not independent"; the substring check was one member; residual stated exactly:
a key intersecting ITSELF (`aa` in `aaa`) is not an intersection between keys and `text.count`'s
non-overlapping count equals the regex's non-overlapping match count, so counts stay equal.

**3b. NUL in a shell payload — design must 2. VERIFIED.** `Popen(["bash","-c","true"])` rc 0;
`Popen(["bash","-c","true\x00"])` raises `ValueError: embedded null byte`. Valid UTF-8, passes strict
decoding, no mapped exception → traceback without the required token.
*Decision:* catch `ValueError` at the spawn call and raise `LaunchFailed("spawn", err)` — the existing
exception, the existing token, a new stage label beside `"mkdtemp"`, `"reap"`, `"collect"`. Nothing
executed (the spawn never happened). Two tests: `test_nul_in_document_block_is_a_launch_failure` and
`test_nul_in_preamble_is_a_launch_failure`; mutation row `spawn-valueerror-unmapped` (the `except
ValueError` removed) killed by the first. The spec's FR for the launch-failure verdict names this as a
member. Class: "runtime rejects the argument vector at spawn"; `ValueError` is the only member Python
3.11 raises for a `str` argv; residual: a non-`str` argv element (`TypeError`) is unreachable because
every element is composed as `str`.

**3c. Rollback identity guard exempt from discrimination — design must 3. Premise VERIFIED** (design
`:1985–1987` says exactly what codex quotes); the exemption contradicts `invariants.base.md` §Test
discrimination, which the design inlines into every audit of itself.
*Decision:* the identity check becomes a **mutation-backed guard**. Ninth module seam `os.lstat` in the
helper's namespace (it is not among the eight — verified: `os.killpg, shutil.rmtree, tempfile.mkdtemp,
os.chmod, os.unlink, _final_write, _close_stream` + the Popen wrapper). Test
`test_rollback_skips_unlink_on_identity_mismatch`: patch `os.lstat` to return an `(st_dev, st_ino)` that
differs from the recorded `fstat` identity, patch `os.unlink` to record; assert unlink NOT called and
`leftover:` reported for that path. Mutation row `rollback-identity-check-removed` (the comparison
deleted, unlink unconditional) killed by it. The "one canonical eight-item list stated identically to the
design" (impl-plan v1.18) becomes a **nine-item** list, stated identically in design AND impl-plan; the
spec names the seam wherever it enumerates seams. The `:1985–1987` sentence is rewritten to say the
guard IS discriminated and how.

**3d. AC-1.8's collection test conflicts with the wire-only failure — impl-plan must 2. VERIFIED by
reading:** the WIRE-PIN is added to `test_docsections.py` (impl-plan `:2090`); AC-1.8
`test_docsections_imports_when_collected_alone` runs that whole file via subprocess and requires exit 0
(`:2033`); under the `docsections-delegation-reverted` mutant the WIRE-PIN fails, so the subprocess exits
non-zero and AC-1.8's test fails too — "every other test stays green" (`:1628`, `:2095`) is false, and
spec `:82` / design `:3071` say the existing file "still passes unchanged" while a test is being added to
it.
*Decision:* AC-1.8's test becomes **collection-only**: `[sys.executable, "-m", "pytest",
"--collect-only", "-q", "-p", "no:cacheprovider", "h-mad/tests/test_docsections.py"]` exits 0. It proves
the module imports and every test collects when the file is collected alone; it runs nothing, so a red
WIRE-PIN cannot fail it. Residual stated exactly: the pre-existing `test_docsections.py` tests are no
longer RUN in isolation by AC-1.8 — they run in the full suite (AC-6.4's floor) and in the 5e
module-scoped run. Spec `:82` and design `:3071` wording: "its existing tests still collect and pass in
the full suite" (not "passes unchanged" — the file changes by one added test). The impl-plan's wire
mutant then has exactly ONE failing test, the WIRE-PIN, and the two "every other test stays green" claims
become true.

**3e. `field-escape-removed` does not isolate — impl-plan must 3, design `:3231` carries the same row.
VERIFIED by reading:** "`_field` returns its input unchanged" drops `json.dumps` quoting, `json.dumps`
control escaping AND the c1 second pass together, so `test_dynamic_field_cannot_forge_a_token` (quoting)
and `test_unicode_line_separators_cannot_split_a_verdict_line` (c1) both go red under it — the two
"discriminated in both directions" sentences (`:2673`, `:2679`) are false.
*Decision:* the payload becomes `json.dumps(str(value), ensure_ascii=False)` → `'"' + str(value) + '"'`,
with the c1 second pass KEPT. Under it: newline test red (raw `\n` inside the quotes starts a second
line), forge test green (quotes kept, `x rc=0` stays one field), unicode test green (c1 pass kept). State
that matrix in both documents identically; the row COUNT does not change.

**3f. Guard-narrowing invariant `new_only=0` false on the live tree — impl-plan must 4. VERIFIED** with
the plan's own probe: `python3.11 docs/03-analysis/probes/doc-block-exec/heading_differential.2026-09-04.b66afa9c.py`
at `fbc2ea0` → `TRACKED files=30 both=292 old_only=82 new_only=1 … titleless=1`, `NEW-ONLY
h-mad/SKILL.md 984 #`. `sed -n 984p h-mad/SKILL.md` is a bare `#`: CommonMark's empty ATX heading, which
the ATX predicate accepts and the space-required regex rejects.
*Decision:* **the line is NOT repaired this round** — touching `h-mad/` moves the freeze and expires ~70
plan readings (#49r); it is repaired in the tooling batch after c97/c88/c48. The impl-plan replaces the
zero-softening invariant with explicit accounting: `new_only` at `fbc2ea0` is **1**, its member is
`h-mad/SKILL.md:984`, an empty ATX heading that IS a heading under CommonMark, so the narrowed guard is
right and the old regex was wrong about it; the invariant becomes "every `new_only` member is enumerated
and each is a CommonMark heading". The plan's §Measurements figures stamped at `1861157` stay at
`1861157` (FACT 2 clause 2); the plan adds the `fbc2ea0` reading beside them.

**3g. Cleanup chaining `from pending` with `pending=None` — impl-plan must 5. VERIFIED:** `raise
RuntimeError() from None` inside an `except Cleanup` → `__cause__ is None`, `__suppress_context__ True`;
the cleanup error is suppressed, not selected.
*Decision:* explicit selection: `raise err from pending if pending is not None else raise err from
cleanup_error` (or the equivalent two-branch form the author prefers). Test
`test_cleanup_failure_after_successful_run_is_chained` — a run that succeeds, then `shutil.rmtree`
(existing seam) raises: the raised exception's `__cause__` IS the cleanup error. The prose at the
`:from pending` site is rewritten to match.

**3h. RED counts vs the accumulating test file — impl-plan must 6. Premise WRONG, concern VALID.**
Codex says "the assembler compares actual pytest totals with `--expect-pass`". It does not:
`h_mad_assemble_tdd.py` only PRINTS `**Expected after this dispatch:** N failing, M passing.` into the
prompt (`:246`). The stop lives in `references/codex-implementer-prompt.md:62` — "If the stated counts
and what you observe disagree, STOP and report". So the mechanism is the implementer, not the assembler,
and the symptom is real: Task 2's "expected passing = 0" against a file whose Task 1 tests pass reads as
a disagreement.
*Decision:* every task's Expected RED split states **whole-file totals** — failing = this task's new
tests, passing = the sum of all earlier tasks' tests in that file, each earlier task named as the
regression-guard block. The "traceback" half is VERIFIED separately: the `__main__` block ships with
Task 4 (`:2627`), so at Task 4 RED `subprocess.run([sys.executable, SCRIPT, *args])` (`:38`) exits 0
silently; the subprocess tests fail on their assertions (no `DOCBLOCK:` line, rc 0), not on a traceback.
Rewrite `:2776–2777` to name that failure mode per test (§5d "failure mode per test").

**3i. Probes absent from the tree — plan must 1 (codex). Premise VERIFIED, and CLOSED at `fbc2ea0`
(FACT 7).** The plan cites which version by shape, not by name: the 09-04 `heading_differential` prints
the `--- TRACKED / --- GLOB` shape the plan publishes at `:2745`; the 09-03 one is glob-only. Plan-author:
cite the committed paths, attribute each published figure to the version that produced it, and
**reproduce the published `files=25 both=263 old_only=76 new_only=0` at `1861157`** via `git worktree
add /tmp/wt-1861157 1861157` and running the 09-04 probe from that root — NOT at HEAD, where the corpus
has grown (30/292/82/1). `grammar_corpus` needs `markdown_it` → `/opt/anaconda3/bin/python3.11`, never
bare `python3` (3.14, no packages): 14/14 OK at `fbc2ea0`. `setext_census`: tracked 30 / glob 35, 0
Setext headings at `fbc2ea0`.

**3j. `49 across 2 files` attributed to a subdirectory run — plan must 2 (codex). VERIFIED by
reasoning:** from `h-mad/` the script cannot see `handoff/SKILL.md` at all, and `Path('.')`'s
`parts[0]` from inside `h-mad/` is `SKILL.md`/`references`, never `h-mad`, so the filter yields 0 — codex
measured `0 / 0` from each subdirectory and `73 / 10` from the root. A subdirectory run cannot produce
27 + 22 across the two top-level files.
*Decision:* keep the historical observation, delete the asserted cause, mark it `cause unrecovered — the
invocation that produced 49/2 is not in any preserved artifact`.

## FACT 4 — the teammate class: what the orchestrator re-derived at `fbc2ea0`

Re-derived and TRUE: plan must 1 (`plan.audit.v72.codex.md` exists at `af19d53` → the span starts at
73); plan must 2 (`git show 59cc2ad:` spec `v1.62` and design `v1.107` entries each contain **0** `NOT
RE-RUN`); plan must 3 (line 3296 sits under `## Success Criteria`); impl-plan must 1 (self-reference
screen reads **4** on the body); impl-plan must 2 (`body v1.50 ships` still present, **1** hit);
impl-plan must 3 (`grep -Fc '# h-mad/tests/docsections.py  (delta)'` → **2**).
NOT re-derived by the orchestrator (auditor-claimed; verify before applying, report if it fails): design
must 1 (18 stamp sites vs a condition reaching 5 — the 11 head lines are listed in the report), design
must 2 (the `DETAIL_KEYS` bound sentence carries no blob/working-file pair — the auditor says the claim
is currently TRUE and the defect is the missing reading), plan must 4 (the bare `sed` range property —
checked by the auditor at ten shas with the system binaries), impl-plan must 4 (`22 → 23` across
`af19d53`, `_trim_version_history` the new member — the freeze commit's own function).

## FACT 5 — the reopen rule (new; from impl-plan r16 musts 1 and 3, both fix-introduced by a reopen)

**A post-DONE reopen re-runs every screen its own new text can move**, before the second DONE. Round
sixteen's impl-plan reopened twice after DONE (each announced first, correctly); the reopens' own
sentences put the self-reference needle back into the body (must 1: `0` → `4`) and spelled a one-hit
locator a second time (must 3: `1` → `2`). A screen that reads `0` is a screen your next sentence can
break. If you reopen: announce, edit, re-run the screens, THEN the second DONE.

## FACT 6 — the version-number rule (carried from r16, #49k)

A version bump is the FIRST thing you write. **Bump when you start, send DONE once when you finish,
write nothing after DONE** without a prior message saying so. The orchestrator will read `git show
:<path>` back before any commit and compare it to what the commit message will claim; a path with a
live writer is not committed.

## FACT 7 — what `fbc2ea0` added, and what it did NOT touch

`fbc2ea0` adds four files under `docs/03-analysis/probes/doc-block-exec/` and nothing else:
`heading_differential.2026-09-03.cd979362.py`, `heading_differential.2026-09-04.b66afa9c.py`,
`grammar_corpus.2026-09-03.cd979362.py`, `setext_census.2026-09-04.b66afa9c.py` — every distinct
scratchpad version, verbatim, named by date and writing session. It does not touch `h-mad/`, `handoff/`,
any of the four documents, or the tracked corpora (`git ls-files -- h-mad handoff`). Any document that
says "no probe source is in the tree" is now wrong and says where it is.

## FACT 8 — cross-document ownership this round (who edits what; nobody edits a sibling)

| decision | spec | design | plan | impl-plan |
|---|---|---|---|---|
| 3a intersecting spans | AC-2.7 second clause | §Substitution rule + token table detail line | — | test + mutation row `intersect-check-removed` |
| 3b NUL → `LaunchFailed("spawn")` | launch-failure FR names it | exception mapping + stage label | — | two tests + row `spawn-valueerror-unmapped` |
| 3c ninth seam `os.lstat` | seam enumeration if any | nine-item list + guard sentence | — | nine-item list + test + row `rollback-identity-check-removed` |
| 3d AC-1.8 collect-only | AC-1.8 wording | `:3071` row wording | — | `:2033`, `:1628`, `:2095` |
| 3e `field-escape-removed` payload | — | `:3231` row | — | `:2660–2682` |
| 3f `new_only=1` accounting | — | — | §Measurements adds `fbc2ea0` reading | invariant → accounting |
| 3g `from pending` selection | — | — | — | the site + test |
| 3h whole-file RED totals | — | — | — | every task's Expected RED split |
| 3i / 3j probes, `49/2` | — | — | `:2741–2808`, `:2343–2346` | — |
| mutation matrix count | — | 81 → **84** rows wherever stated | — | 81 → **84** (83 helper + 1 SKILL.md), `:19`, `:131`, `:2723`, `:2778` |

Each author re-runs the cross-document check for the rows above against the SIBLINGS' bytes at
`fbc2ea0`, not at the sibling's working file — the sibling is being rewritten under you and your view
of it goes stale mid-round (orchestrator rule 4). Report "sibling owes X" in your tail; never edit it.

## Standing constraints

1. One author, one document. A sibling that owes something is REPORTED in your tail, not edited.
2. The tree is frozen at `fbc2ea0` until all four DONE messages arrive. Nothing commits under you.
3. Close the CLASS, never the instance — name the axis, write the rule, state the residual exactly.
4. A count is evidence only against another count at the same commit, same corpus, same grammar, in a
   shell whose state you did not inherit. Collapse newlines before counting a phrase (`tr '\n' ' '`);
   admit inline-code delimiters in the needle; check which language construct a token sits in; use
   `/usr/bin/grep` — `ugrep` shadows `grep` in this shell and fails loudly on ordinary regexes.
5. Run `h_mad_precheck_doc.py` on your document before DONE and paste its `PRECHECK:` line. impl-plan
   uses the six `--allow` grammar specimens.
6. Claim **no two-surface clean and no exit gate** in any entry. This round is FAIL → revision; the gate
   is c97/c88/c48.

## Corrections (appended during the round; lines above are left as written)

- **C1 — 3a detail-line spelling.** `intersect: "<a>" "<b>" at <offset>` violates spec FR-4, which quotes every
  detail-line value without exception (the bare-field list governs the VERDICT line only; v1.61 `pgid`
  precedent). The round's spelling is **`intersect: "<a>" "<b>" "<offset>"`**. Found by spec-author-r17;
  relayed to design-author-r17 and implplan-author-r17. Orchestrator error: the grammar was not checked
  against the spec before the line was prescribed.
- **C2 — `intersect:` is the TWELFTH detail key**, absent from FACT 8. Spec FR-4's enumeration goes eleven →
  twelve; the impl-plan's `DETAIL_KEYS` tuple and its count follow; the design's constructor-form triage
  alternation follows AND was already one member short (ten vs eleven) at `fbc2ea0`; the `h-mad/SKILL.md`
  registry row is deferred to 5d/5e via AC-4.5's walk (SKILL.md is not edited this round).
- **C3 — 3b: `spawn` is NOT a new stage label.** Spec and design at `fbc2ea0` already carry
  `stage=<mkdtemp|spawn|reap|collect>`. Only the exception class moves (`ValueError` → `LaunchFailed`).
  Orchestrator error: asserted without a grep.
- **C4 — 3d: "still passes unchanged" is in the DESIGN's AC-1.8 row (`:3071`), not spec `:82`.** Spec
  body collapsed and grepped for `passes unchanged` → 0. Orchestrator error: a phrase attributed to a
  document it is not in.
- **C5 — the connective.** design-author-r17 independently found the quoting rule and proposed
  `intersect: "<a>" "<b>" at "<offset>"`. Ruled: the spec's connective-free form
  **`intersect: "<a>" "<b>" "<offset>"`** is final for all four documents — it mirrors
  `overlap: "<shorter>" "<longer>"` and the spec is the reference. Two authors converging on the quoting
  rule from two documents is the shared-facts gate working; the connective is the residual it caught.
- **C6 — twelfth-key arithmetic (design-author-r17, from the impl-plan at `fbc2ea0`).** `DETAIL_KEYS`
  eleven → twelve moves the impl-plan's rendering-slot sentence: **26 → 27 slots, 19 → 20 through
  `_field`, 7 bare unchanged**. Relayed to implplan-author-r17 to re-derive, not copy.
- **C7 — teammate design must 1 partition is 13 of 18, not 11 of 16** (the auditor walked only the
  sixteen line-scoped sites; the two wrap-split sites are uncovered too). design-author-r17 takes the
  one-pass option: all eighteen re-stamped to v1.109, exemption over zero sites.
- **C8 — two determinism rules the sheet omitted (spec-author-r17).** `<a>` is the lexicographically
  smaller key, `<b>` the larger. `<offset>` is the **smallest character index the two match spans share**,
  0-based into `block.text` — "first intersecting occurrence" admitted two readings (`0` = start of the
  earlier span, `1` = first shared index) and they differ. Canonical: `abc` under `ab→X, bc→Y` → spans
  `[0,2)` and `[1,3)` → **`intersect: "ab" "bc" "1"`**. Relayed to design + impl-plan.
- **C9 — two carried figures re-measured at `fbc2ea0` (spec-author-r17).** The impl-plan owes
  `intersect` at THREE sites (tuple, `# 11` comment, "all eleven" prose), not one. The design's triage
  alternation is already ELEVEN and complete — spec v1.62's "ten, missing `duplicate_key`" report was
  stale at the freeze (closed before it); C2's "already one member short" repeats that stale report and
  is withdrawn. The design owes only the twelfth member.
- **C10 — the freeze moved REPO-WIDE censuses (spec-author-r17; re-derived by the orchestrator).** FACT 7
  checked the `h-mad`/`handoff` closures and the tracked corpora and was right about them — but
  `grammar_corpus.2026-09-03.cd979362.py` carries markdown fences in string literals, so every census
  scoped to the whole repo or to `'*.py'` moved at `fbc2ea0`: `git diff --name-only 74e126f fbc2ea0 --
  '*.py' | wc -l` → **6** (0 at `af19d53`); `git grep -n '```bash' -- '*.py' | wc -l` → **8** (6);
  `git grep -l '```' -- '*.py' | wc -l` → **25** (24); root pytest collection **2814** (`h-mad/` alone
  2552, unchanged). #49r one level over: a freeze whose closure predicates pass for the roots it names can
  still move a census that names no root. Relayed to design, plan and impl-plan authors.
- **C11 — spec DONE v1.63, readback 250/101 (author's first report said 243/101: a figure measured before
  its last three edits — the author corrected it unprompted).** Deliberately UNROUTED this round and owed
  to r18: spec AC-1.8's universal "every test in `h-mad/tests/`", which the design's codex leg measured
  false at 13 of 88 files (design v96 codex should-list). Left for the c97/c88/c48 gate to file or clear.
- **C12 — 3f misattributed a printed line (plan-author-r17; re-derived).** `NEW-ONLY h-mad/SKILL.md 984 #`
  was printed by the **09-03** probe; the 09-04 probe prints only the `new_only=1` count and `OLD-ONLY`
  lines (`grep -c NEW-ONLY` → 0 in the 09-04 source, 1 in the 09-03). Also from the plan author's
  worktree runs: `new_only` is **1 at `a8e0372`, `35698f9`, `cf3a862`, `4e4a00c`, `74e126f`, `fbc2ea0`**
  and **0 only at `1861157`** — the invariant was false at every later sha, not newly at the freeze; and
  the published GLOB `30/268` at `1861157` does not reproduce (probe gives `25/263/76/0` for both
  TRACKED and GLOB there). Orchestrator error: I ran both probe versions in one call and attributed the
  union of their output to the version the plan cites.
- **C13 — probe-naming debt in three siblings (plan-author-r17; re-derived at `fbc2ea0` and on the
  working files):** `grep -cE 'throwaway|heading_differential\.py|grammar_corpus\.py'` → design **6**,
  impl-plan **2**, spec **1**. All still call the probes throwaways or name them by bare filename.
  Relayed to design + impl-plan (running) and a one-site reopen requested from the spec author (DONE).
- **Plan DONE v1.104**: readback `PRECHECK: PASS issues=0`, numstat 669/146. Teammate must 4's mechanism
  was RECOVERED (the leak is the bare-token address, not the anchored one), not marked unexecuted.
  Register 7 → 10 members from codex should 1.
- **C14 — C10's collection figure was misattributed (plan-author-r17).** The +5 in pytest collection
  (root 2809→2814, `h-mad/` 2547→2552) is **`af19d53`'s five assembler-audit tests**, not the probe
  commit: `git show fbc2ea0 | grep -c '^+def test_'` → 0; `pytest --collect-only` over the probes dir
  collects nothing; `git show af19d53 -- 'h-mad/tests/*' | grep -c '^+def test_'` → 5. `fbc2ea0` moved
  only the `*.py` fence and file censuses. Plan reopened after DONE for the C10 sweep (announced first,
  per FACT 5).
- **C15 — C13's spec hit is a throwaway VIRTUALENV, not a probe (spec-author-r17).** The needle's
  `throwaway` arm fired on `markdown-it-py 4.2.0, throwaway venv:`; the two filename arms return 0 on the
  spec. The real defect is wider than the word: markdown-it-py claims cite an environment nobody can
  reconstruct while `grammar_corpus.2026-09-03.cd979362.py` is now committed. Fix: cite the probe only at
  claims its 14 cases cover; uncovered claims stay their own measurement and become r18 debt.
- **C16 — C10 stated a figure at a sha where it was not run (plan-author-r17; re-derived).**
  `git diff --name-only 74e126f <sha> -- '*.py' | wc -l` is **0 at `dfae038`, 2 at `af19d53`** (the
  assembler script + its test), **6 at `fbc2ea0`** (4 probes + those 2). C10 wrote "0 at
  `af19d53`" by extending the spec author's `dfae038` reading one commit without running it. The `.py`
  interval closure broke at `af19d53` and no round noticed until now. Plan second DONE, still v1.104
  (reopen recorded in the entry), `PRECHECK: PASS issues=0`.
- **C17 — 3e's mechanism was FALSE (implplan-author-r17; re-derived).** The c1 second pass escapes every
  `Cc`/`Zl`/`Zp` code point and `unicodedata.category("\n")` is `Cc`, so under the narrowed
  `field-escape-removed` (quoting kept, `json.dumps` escaping dropped, c1 pass kept) a raw newline is
  STILL escaped and the newline test stays green. The mutant frees exactly `"` and `\` (`Po`), which no
  test carried — the row had no isolating killer. New test
  **`test_quote_in_dynamic_field_cannot_close_the_value`** is the row's `test` key; matrix (newline red /
  forge green / unicode green) is replaced by (quote-test red, all three others green). **Design-row key
  change** — relayed to design-author-r17. Orchestrator error: I asserted the escaping matrix from the
  row names without reading `_field`'s second pass.
- **C18 — 3g had a test and no mutation row (implplan-author-r17 flagged it unowned).** Decision: add
  row **`cleanup-chain-selection-flipped`** (the two-branch selection collapsed to `from pending`
  unconditionally) killed by `test_cleanup_failure_after_successful_run_is_chained`. Matrix **84 → 85**
  (84 helper + 1 SKILL.md). Impl-plan reopen requested; design told. Also from the impl-plan: 3f's
  literal `h-mad/SKILL.md:984` would turn a shipped line-pin guard test red (#29) — written as a needle,
  never as a `path:line`; the design must do the same if it names the site.
- **C19 — spec second DONE v1.63, readback 282/106, `PRECHECK: PASS issues=0`, body needle 0.** The
  markdown-it-py claims cited **4.2.0** in an unrecorded venv; the committed probe's interpreter carries
  **2.2.0** and no interpreter on this machine has 4.2.0. The author re-measured all six renderer claims
  at 2.2.0 (identical) and now publishes both readings; the probe is cited at three sites with what it
  does NOT cover stated (AC-1.6's case absent; AC-1.7 covers only the closing-hash strip). Citing the
  probe's interpreter for a 4.2.0 reading would have been a false substitution — the routing's needle
  found the site, not the defect.
- **Impl-plan reopen announced** (six corrections: determinism rules, C12 attribution + `new_only`
  history, probe naming, byte-identity qualifier, and — queued — row 85). Already in v1.53 before the
  messages arrived: the three-quoted `intersect:` line, `DETAIL_KEYS` twelve at three sites, 27/20/7,
  `spawn` not new, C14's collection attribution.
- **C20 — spec third DONE v1.63, 289/106 (matches readback).** The author declined one routed word,
  correctly: uncovered markdown-it-py claims are NOT "irreproducible" — every one is re-measured at 2.2.0
  through the committed probe's interpreter; what is missing is a probe CASE. **r18 debt (tree frozen
  this round): five cases for `grammar_corpus`** — backtick-in-info-string, tab-before-closing-run,
  no-space closing hashes, trailing info-string word, outer-tilde quoting a backtick fence — plus
  AC-1.8's "every test in `h-mad/tests/`" universal (C11).
- **C21 — impl-plan second DONE v1.53 (556/146) applied the determinism rules (test asserts
  `intersect: "ab" "bc" "1"` verbatim), the `new_only` history at seven shas, probe attribution and
  naming; its one repo-wide census (`def test_` over `*test_*.py`, **1512**) is unmoved. Row 85 was NOT
  in it — the request arrived after the reopen's edit window (`grep -c cleanup-chain-selection-flipped`
  → 0; body `84 rows` ×3). Third reopen requested for that one item. The self-reference needle broke a
  THIRD time in this revision and was caught only by the re-run — FACT 5 measured three times in one
  document.
- **C22 — design-author-r17 DIED of context overflow ("Prompt is too long") at 14:32**, mid-verification
  of "three false claims in my own entry", after an advisor() call. Working file measured at 14:33 (last
  edit 14:27:45; v1.109 entry present; PRECHECK PASS; 542/132): DONE — collect-only ×6, `passes
  unchanged` ×0, `LaunchFailed("spawn"` ×1, no `SKILL.md:984` literal. OPEN — `at <offset>` ×4 and the
  three-quoted form ×0; `test_quote_in_dynamic_field…` ×0; `84 rows` ×1; "eight module seams" ×1;
  probe-naming needle ×5, committed path ×0; 18-site re-stamp unverified; the entry's three false claims
  unknown. **design-author-r17b** spawned to FINISH the working file (no revert, no v1.110, no advisor,
  sliced reads). Lesson for the agent definitions: an author that reads a 3,500-line document whole more
  than once and then calls advisor() overflows; authors must read in slices and never call advisor.
- **C23 — impl-plan third DONE v1.53, 85 rows** (row `cleanup-chain-selection-flipped` in Task 3; 25/6/26/28;
  84 helper + 1 SKILL.md). Readback: row ×4, body `85 rows` ×3 / `84 rows` ×0, numstat 573/146. The
  seven `--allow` grammar specimens, recovered from the bare precheck's own PLACEHOLDER lines:
  `overlap: "<a>" "<b>"` · `intersect: "<a>" "<b>" "<offset>"` · `stream: "<name>"` ·
  `os_error: "<text>"` · `<key>=<bare>` · `<key>="<json-string>"` · `pgid: "<n>"`. With them the
  orchestrator reproduces `PRECHECK: PASS issues=0`. Design now owes FOUR rows and 81 → 85.
- **C24 — ownership REVERSED to design-author-r17.** r17 resumed from its transcript at 14:37 (a
  "failed: Prompt is too long" notification is recoverable) and had already landed most of the open list
  by 14:41:35 (three-quoted `intersect:`, canonical `"1"`, quote test, 85 rows, row name, probe needle
  clear) before the stand-down reached it; r17b asserted-before-write, found the file moving, made ZERO
  edits and stood down. Two authors on one file for ~8 minutes with no collision — by r17b's assert, not
  by luck. Orchestrator error: spawned a successor without first ruling ownership explicitly.
- **C25 — C17's matrix was WRONG about the newline test (design-author-r17b).** Under the narrowed
  `field-escape-removed` the newline test goes **RED as a regression** — it asserts the escaped
  spelling `\n` appears, and the payload is one line with a raw LF. Final matrix, identical in design
  and impl-plan: quote test RED (isolating killer) · newline test RED (regression, spelling assertion
  only) · forge GREEN · unicode GREEN. The impl-plan's row already says `red (regression)`; its PROSE
  mechanism ("splits into two physical lines") is wrong — one-sentence reopen requested. Also from
  r17b: design body's sibling numstats stale (spec `243` → 289/106; plan `601` ×2 → 689/146); the
  18 `v1.106` hits are historical references, not stamp sites.
- **C26 — impl-plan fourth DONE v1.53 (three announced reopens).** AC-4.1 bullet's mechanism corrected
  per assertion (one-line assertion HOLDS under the narrowed mutant; only the escaped-spelling assertion
  fails); sweep keyed on the mutant NAME found 1 stale of 6 sites; the reopen's own participle moved the
  per-needle sweep 27 → 28 and was caught by the re-run. Final: 85 rows, 25/6/26/28, PRECHECK PASS with
  the C23 specimens (orchestrator reproduced).
- **C27 — two orchestrator checklist items in C22 were WRONG (design-author-r17b, zero edits, DONE).**
  "eight module seams ×1 still present" is correct text: the file now reads "one of the NINE fault
  injections (the EIGHT module seams … `os.lstat`, or the `Popen` instance wrapper)" — my needle fired on
  the fixed sentence. "18 `v1.106` hits, re-stamp unverified": the re-stamp happened; the stamp needle is
  `after the v1.NNN entry` → 21 folded / 17 flat, all v1.109, exemption untaken (teammate must 1 closed).
  r17 write timeline observed: 14:41:35 → 14:50:03, seven writes, one 3.5-minute gap that looked like
  death. Still stale at 14:50:03 md5 88b5cbd0: spec numstat `243/101` ×2 (true 289/106), plan
  `601/140` ×2 (true 689/146) — both already in r17's queue.
- **C28 — the design DOES publish an unscoped repo-wide census, and C10 lands on it (design-author-r17b;
  re-derived).** `git ls-tree -r --name-only <sha> | grep -cE 'heading_differential|grammar_corpus'`:
  **0 at `cf3a862`, 3 at `fbc2ea0`**. Three body sentences false at the freeze (~L642, ~L644,
  ~L647/L1213: "not in the tree", "never committed", "not re-derivable") plus ~L876 "vacuous" for both
  untracked-script measurements. r17's C10 answer covered only the scoped `rglob` sweep. **Sweep
  lesson (orchestrator error, same class as the hard-wrap miss one spelling down):** the probe-naming
  needle carried `.py`; nine body sites spell the names WITHOUT the extension inside grep alternations
  in prose — `grep -cE 'heading_differential|grammar_corpus'` → 9, with `\.py` → 0. A value sweep
  must try the bare identifier as well as its filename form. Routed to r17's open reopen. r17b released
  for good, zero edits.
- **C29 — design r17 report at 669/147: items 1–4 landed; matrix rescored at ASSERTION level, "each
  mutant has exactly one RED column" WITHDRAWN** (quoting-removed reds newline+forge+quote; escape-removed
  reds newline+quote; c1-removed reds unicode; red sets pairwise distinct, one isolating observation
  each). C28's sites were NOT yet applied (message crossed its edit window) — reopen requested. ONE
  cross-document cell disputed: **unicode test under `field-quoting-removed`** — impl-plan row says red
  (collateral), design grid says GREEN. Routed to r17 to MEASURE against the test's actual assertion and
  report which document is wrong. Remaining `243 added` is inside the v1.109 entry (L4186 > VH start
  L4075), quoting the withdrawn value — history, stays.
- **C30 — cross-document shared-value sweep (body-scoped, newline-collapsed) over the three FINAL
  documents + the near-final design, 27 needles.** Every FACT 3 / C-correction value agrees across all
  four where the value applies: three-quoted `intersect:` (spec 1 / impl 2 / design 2; `at <offset>`
  0 everywhere), canonical `"1"`, `LaunchFailed("spawn"`, `os.lstat`, collect-only, row/test names for
  3a/3b/3c/3g, `85 rows` (impl 3 / design 1; `84`/`81` 0 everywhere), `passes unchanged` 0 except the
  spec's negated quotation of it (L118, correct). Plan's six `throwaway` hits are the markdown-it-py
  VENV and one history sentence, not probe scripts. Spec says "nine named fault injections". Design still
  carries the C28 sites and the disputed unicode cell (C29) — pending r17's reopen.
- **C31 — design DONE v1.109 (697/154).** The disputed unicode cell was the DESIGN's error: the unicode
  test asserts the four escapes inside `heading="…"`, and the design's probe modelled it as a line count.
  Rescored grid is cell-for-cell the impl-plan's: quoting-removed reds N/U/F/Q; escape-removed reds N (regression) + Q (key); c1-removed reds U alone. `field-quoting-removed` is NOT isolated — recorded, not smoothed. Three passes over one matrix; the error survived two passes of one author and died at the first cross-document diff. **All four documents DONE**: spec v1.63 (289/106), plan v1.104 (689/146), impl-plan v1.53 (575/147), design v1.109 (697/154). Batch committed with this sheet; the freeze-sha field of every entry is `fbc2ea0`, the parent of that commit.
