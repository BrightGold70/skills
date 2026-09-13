# Adversarial review — `a8b9e4e`

`fix(h-mad): precheck scores the L-spelling of a line pin, and stops failing documents on their own changelog`

Fresh context. Nothing in the authoring session's reasoning was taken as established.

---

## What I actually read and ran

**Read (whole or in the relevant range):**

- `h-mad/scripts/h_mad_precheck_doc.py` (552 lines) at `a8b9e4e` and at `a8b9e4e^` (`git show a8b9e4e^:…`)
- `h-mad/scripts/h_mad_assemble_audit.py` — `VH_MARKER`, `version_history_start`, `_trim_version_history`, `_vh_noop`, `assemble` (lines 300–440)
- `h-mad/scripts/h_mad_version_history.py` — `ANCHOR`, `find_anchor`, `section_bounds`, `entry_lines` (lines 40–110)
- `h-mad/scripts/h_mad_archreview_cycle.py` — `_trim_vh`, `_size_notes` (lines 195–235)
- `h-mad/tests/test_h_mad_precheck_doc.py` — the 175 added lines in full
- `h-mad/tests/mutation-specs/precheck_l_pin_and_version_history.json` (new, 7 rows), `pindrift_detector.json`, `pindrift_declared_historical.json` (edited rows)
- `h-mad/SKILL.md` §2846 (the canonical description of this gate) and §1461/1508/1637–1643
- the full `git show a8b9e4e` diff and commit message

**Ran:**

| # | command | result |
|---|---|---|
| 1 | `cd h-mad && python3.11 -m pytest tests/ -q` | `3249 passed, 2 skipped in 533.00s` (green baseline at `a8b9e4e`) |
| 2 | `cd h-mad && python3.11 -m pytest tests/test_h_mad_precheck_doc.py -q` | `48 passed in 15.39s` |
| 3 | 26 hostile fixtures executed against `h_mad_precheck_doc.py --json` in a purpose-built scratch git repo (`scratchpad/lab`, two commits, so `PINDRIFT` is live) — scripts `exp.py`, `exp2.py`, `exp3.py` |
| 4 | 6 single-edit mutations applied to the shipped source, each scored against `tests/test_h_mad_precheck_doc.py + test_h_mad_assemble_audit.py + test_h_mad_archreview_cycle.py` — script `mut.py` |
| 4b | the two SURVIVING boundary mutations re-scored **together against the full suite** (`mut_full.py`) | `3249 passed, 2 skipped in 518.98s` — byte-identical to the clean baseline |
| 5 | corpus replay: all **44** phase documents scored with the `a8b9e4e^` script and the `a8b9e4e` script, verdict+issues diffed — script `corpus.py` |
| 6 | `_trim_version_history` / `version_history_start` driven directly in-process on list- and table-shaped histories |
| 7 | uniqueness check of every `find` string in the three touched mutation specs against the shipped source |
| 8 | 16 hostile / non-ASCII tail spellings through the CLI (`exp4.py`), hunting an `int()` or regex crash |
| 9 | three candidate boundary-arithmetic fixes scored against ground truth on 12 texts (`boundary.py`) |
| 10 | `h_mad_version_history`'s own section bounds re-implemented and run over all 44 documents against the shipped boundary (`corpus2.py`) |
| 11 | the two line-numbering bases inside `scan()` compared on one document (`exp5.py`) |

The worktree was at `91c1021` (the commit's parent) on arrival; I detached it at `a8b9e4e` before measuring. All `python3.11`.

**10 findings — Critical: 0 · Major: 6 · Minor: 4.** Seven (F1–F6, F8) are introduced by this change; F9 is an omission by it; F7 and F10 are pre-existing patterns this change extends.

---

## Major

### F1 — CONFIRMED — the Version History boundary silently swallows lines **above** the heading whenever the document contains a non-`\n` line break

`version_history_start` computes the line number by counting `"\n"`:

```python
return text.count("\n", 0, i) + 2
```

`scan()` numbers lines with `str.splitlines()`, which additionally breaks on `\x0b` `\x0c` `\x1c` `\x1d` `\x1e` `\x85` `U+2028` `U+2029`. Every such character above the heading makes the computed `vh_start` **one line too small**, so `in_vh()` returns `True` for real body lines and their hard findings are demoted to `allowed`.

Command and real output (`exp2.py`, and the six-character sweep):

```
# body:  HDR + <CHAR> + "X\nTBD right above the heading.\n## Version History\n\n- v1\n"
FF \x0c            verdict=PASS issues=0  allowed=['PLACEHOLDER TBD L7 (in `## Version History`)']
VT \x0b            verdict=PASS issues=0  allowed=['PLACEHOLDER TBD L7 (in `## Version History`)']
LS U+2028          verdict=PASS issues=0  allowed=['PLACEHOLDER TBD L7 (in `## Version History`)']
PS U+2029          verdict=PASS issues=0  allowed=['PLACEHOLDER TBD L7 (in `## Version History`)']
NEL U+0085         verdict=PASS issues=0  allowed=['PLACEHOLDER TBD L7 (in `## Version History`)']
FS \x1c            verdict=PASS issues=0  allowed=['PLACEHOLDER TBD L7 (in `## Version History`)']
none (control)     verdict=FAIL issues=1  allowed=[]
```

The leak scales with the number of such characters — three form feeds demote three separate body lines:

```
CASE e12_leak_3ff  -> PASS issues=0
   ALLOW PLACEHOLDER TBD L9 / L10 / L11 (in `## Version History`)
CASE e12_control_3ff -> FAIL issues=3
   FIND PLACEHOLDER L6 / L7 / L8
```

Failure scenario: an impl-plan that picked up a `U+2028` from a pasted web quote, or a `\x0c` from a pasted source listing, above its `## Version History`. Its last genuine unfilled slot / stale pin before the history is demoted, and the gate prints `PRECHECK: PASS issues=0`.

**Latent, not live today.** On all 44 corpus documents the shipped arithmetic equals the true heading line (`corpus2.py`, see F2) — no phase document currently carries one of these characters above its history.

`_version_history_start`'s docstring reasons carefully about **one** error direction and stops there:

> An import failure returns `None`… That direction is deliberate: the demotion NARROWS what this gate fails on, so losing it fails CLOSED — … never a document that should have failed getting a silent PASS.

That sentence is true of the `ImportError` arm, which does fail closed. The point is that it is the *only* failure mode the author reasoned about. An error in the **arithmetic** runs the other way — `vh_start` too small widens the demotion — and there is nothing in the function, the tests (F5) or the comments that notices the second direction exists.

`\r` and `\r\n` are **safe** — `Path.read_text()` universal-newline-translates them before either function sees the text (verified: `e12_leak_CR` still reported `FIND PLACEHOLDER L9`). So this is narrower than "any CR document", and I say so rather than overclaiming.

**Fix — executed, not proposed.** The prefix must include the marker's own newline, so that the count is of *completed* lines:

```python
return len(text[:i + 1].splitlines()) + 1
```

I ran all three candidates against the ground truth (`scratchpad/boundary.py`). The obvious-looking `len(text[:i].splitlines()) + 1` is **wrong** — it is short by one whenever a blank line precedes the heading, which is the standard markdown shape and the shape of every fixture in this test file:

```
text                                     truth  cur     fixA    fixB
'a\n\n## Version History\n'              3      3       2  <<   3
'body\n\n## Version History\n\n- v1\n'   3      3       2  <<   3
'a\x0cb\n## Version History\n'           3      2  <<   3       3
'a\x0cb\n\n## Version History\n'         4      3  <<   3  <<   4
'a<U+2028>b\n\n## Version History\n' 4      3  <<   3  <<   4
'a\x0c\x0c\x0cb\nc\n## Version History\n' 6      3  <<   6       6
'## Version History\n'                   1      None<<  None<<  None<<
```

`fixB` (`text[:i + 1]`) is exact on every case; the line-1 case stays `None` in all three, which is the documented and intended behaviour.

**Why the fix is not quite one line, though — `scan()` carries TWO line-numbering bases, and `in_vh()` is applied to both.** The per-line loop numbers with `enumerate(lines, 1)` (`splitlines()`); the provenance-sha loop at :587 numbers with `text.count("\n", 0, m.start("sha")) + 1` — the same `\n` basis as `vh_start`. In one document the two disagree (`exp5.py`):

```
control      true: TBD@L6 SHA@L7    reported: {'PLACEHOLDER': 6, 'UNKNOWNSHA': 7}
one \x0c     true: TBD@L7 SHA@L8    reported: {'PLACEHOLDER': 7, 'UNKNOWNSHA': 7}  <<<
three \x0c   true: TBD@L9 SHA@L10   reported: {'UNKNOWNSHA': 7, 'PLACEHOLDER': 9}  <<<
```

So no single `vh_start` can be correct for all six `hard()` call sites: moving it to `splitlines()` fixes five and breaks the sixth. The sha loop's line number was merely *printed* before this commit — wrong output, nobody's verdict. `hard()` promotes it to a **verdict input**. Fix both: make the sha loop use the same basis (`len(text[:m.start("sha")].splitlines()) + 1`) as well as correcting `version_history_start`.

---

### F2 — CONFIRMED — the section has no **end**, so every `##` section after the Version History is silenced too, and a second heading is ignored

`version_history_start` + `in_vh(lineno) → lineno >= vh_start` makes the section run to EOF, and `text.find` takes the **first** occurrence. Both are documented as deliberate ("first occurrence, section runs to end of text, no fence awareness") on the grounds that the assembler does the same.

But this repo already owns a third, far more careful notion of the same heading, in the script whose entire job is this section — `h-mad/scripts/h_mad_version_history.py`:

```python
ANCHOR = re.compile(r"^##[ \t]*Version History[ \t]*$", re.IGNORECASE)

def find_anchor(lines):
    """...More than one is worse: a substitution picks the
    first, which for `references/inline-protocols.md` (7 headers, the only
    such file in the corpus) is a template example rather than the live log."""
    hits = [i for i, ln in enumerate(lines) if ANCHOR.match(ln)]
    if not hits:   raise Refusal("anchor_missing")
    if len(hits) > 1: raise Refusal("anchor_ambiguous", f"matches={len(hits)}")

def section_bounds(lines, anchor):
    """Half-open body range after `anchor`, stopping at header, `---`, or EOF.
    Fenced blocks are tracked because ..."""
```

The new code does precisely the two things that script refuses to do. Executed (`exp3.py`):

```
CASE a_next_section  -> PASS issues= 0      # `## Next Steps` AFTER the history
   ALLOW PLACEHOLDER TBD L13 (in `## Version History`)
   ALLOW PINDRIFT src/target.py:2 L14 (in `## Version History`)
CASE a_control_no_vh -> FAIL issues= 2      # same two lines, no history heading
   FIND PLACEHOLDER L9 TBD — unresolved slot
   FIND PINDRIFT L10 `src/target.py:2` — … changed since the document's provenance

CASE b_rule_closes   -> PASS issues= 0      # `---` closes the section for h_mad_version_history
CASE c_two_headings  -> PASS issues= 0      # template VH at top, live VH at bottom
   ALLOW PLACEHOLDER TBD L11 (in `## Version History`)   # <- this is inside `## Task 1`
   ALLOW PINDRIFT src/target.py:2 L12 (in `## Version History`)
```

`c_two_headings` is the shape `h_mad_version_history.find_anchor` raises `anchor_ambiguous` for, and `test_h_mad_version_history.py:158-160` already fixtures it ("Template example" then "The live log"). `a_next_section` is the shape `h_mad_assemble_tdd.py:100` names in prose — "everything after it — `## Version History`, `## Verification (all tasks)`".

**Not currently firing — measured, not assumed.** I re-implemented `h_mad_version_history`'s own bounds (`^#{1,6} ` header or `^\s*---+\s*$` rule, fence-aware) and ran it over all 44 phase documents against the shipped boundary (`corpus2.py`):

```
docs: 44
documents where the shipped boundary differs from h_mad_version_history's: 0
```

No corpus document has any header (`#` through `######`), any `---` rule, or a second `## Version History` after its history heading, and the shipped arithmetic equals the true line on every one. So F1 and F2 are both **latent, not live**. But this is one `## Open Questions` appended after a history away from silencing a whole tail of a document, with no test (F5) and no verdict change to warn anyone.

---

### F3 — CONFIRMED — the *shared-anchor / "the two agreeing is the whole point"* justification is false; the corpus measurement beside it is true and I reproduced it

The commit rests the Version History rule on two legs and is explicit that it is **not** resting it on a third:

> The anchor is shared with the assembler … which is the point: the two disagreeing about where the section starts IS the defect, not a risk of it.
> The justification is the assembler's recorded position … plus the measurement — NOT "text no reviewer will see", which is false.

The **measurement** leg holds: I replayed all 44 documents and reproduced the stated delta exactly (see *Checked and found correct*). The retracted leg is correctly retracted. What fails is the **anchor-sharing leg** — the one the commit calls "the point" — and it fails four separable ways, each falsifiable by a command. I am not attacking the version the author already conceded; (c) below is about the conclusion drawn *from* that concession, not the concession.

**(a) `VH_MARKER`'s own comment overstates what the assembler does.** It says:

> `_trim_version_history` omits everything from here on from the audit prompt

Executed with the maximum trim, `keep=0`:

```
ASSEMBLER on a `- v` history, --vh-tail 0 -> does it omit EVERYTHING from the heading on?
'\n## Version History\n\n<!-- h-mad assembler: 2 of 2 Version History entries omitted … -->\n\n## Notes\n\nafter\n'
  heading still present? True
```

The heading, any preamble, the note, and **everything after the last `- v` entry** all survive. It omits the *entries*, not "everything from here on". The precheck demotes everything from here on. They do not agree.

**(b) For a table-formatted history the assembler omits *nothing at all*.** `_trim_version_history`'s own comment says: *"Real documents in this repo render their history as a markdown TABLE, and for those this function returns byte-identical text."* Executed:

```
ASSEMBLER on a TABLE-formatted history, --vh-tail 0:
  identical to input? True
  version_history_start -> 7
```

So for the document shape the assembler itself names as the real one, the assembler trims zero characters while the precheck demotes every hard finding in the section. "The two agreeing is the whole point" is false for exactly that shape.

**(c) `--vh-tail` defaults to `None`, a strict no-op** — verified (`keep=None (default) is a no-op? True`). The commit message states this correctly and then draws the opposite conclusion from it: by default the assembler makes **no decision at all** about this section, while the precheck applies the demotion **unconditionally**, with no flag.

**(d) There was never *one* anchor.** `h_mad_version_history.ANCHOR` (F2) is a third notion — case-insensitive, full-line-anchored, multiplicity-refusing, header/rule-bounded, fence-aware. The commit unified the two loosest and left the strict one out, while the comment claims singularity ("The ONE anchor for 'where the Version History section begins'"). Executed disagreement on case:

```
CASE e_lowercase -> FAIL issues= 1     # `## version history` — matched by ANCHOR (IGNORECASE), not by VH_MARKER
```

---

### F4 — CONFIRMED — the `--allow-historical` help text makes a claim the code does not honour: the two line spellings are **not** interchangeable

New help text, shipped in this commit:

> The two line spellings are interchangeable — `:12` and `:L12` declare the same pin.

Only one direction works. Normalisation (`_line_digits`) is applied to the **document's** tail and never to the **operator's flag**:

```python
if (historical_by(f"{rel}:{tail}")
        or historical_by(f"{rel}:{digits}")
        or historical_by(rel)):
```

Executed:

```
CASE e2b extra= ['--allow-historical', 'src/target.py:2']     # document writes :L2
  verdict=PASS issues=0
   ALLOW PINDRIFT src/target.py:L2 L5 (declared historical)

CASE e2a extra= ['--allow-historical', 'src/target.py:L2']    # document writes :2
  verdict=FAIL issues=1
   FIND {'kind': 'PINDRIFT', 'line': 5, 'detail': "`src/target.py:2` — … changed since the document's provenance `1ca1d10`"}
```

Failure scenario: the operator copies the pin out of a *report* or an older revision that wrote `:L2`, the document has since been rewritten to `:2`, and the declaration is ignored **without an error** — which is verbatim the failure the comment added three lines above it says it is closing:

> a flag that accepts only the form the document did not use is ignored WITHOUT AN ERROR, which is the failure the anchor comment above already names.

The accompanying test does not bite on this. `test_either_line_spelling_declares_the_same_historical_pin` exercises only the working direction, and its docstring states the narrower contract ("A declaration written `:1` must cover a document that writes `:L1`") while the shipped help states the symmetric one. The test restates the implementation; the help states the intent; they differ.

Fix: normalise the flag as well — add `historical_by(f"{rel}:L{digits}")`, or apply `_line_digits` to `a` inside `historical_by`.

The sibling claim in the same help paragraph — *"A RANGE is declared by the whole range: `foo.py:10` does NOT cover `foo.py:10-40`"* — is **TRUE** (`historical_by` is `/`-anchored suffix/equality, not substring). Verified: `CASE e3 … verdict=FAIL issues=1`.

---

### F5 — CONFIRMED — the new boundary has no test that bites; three single-edit mutations survive

Scored at the mutation spec's own `target_command` — `python3.11 -m pytest -q` over the whole suite — not just at the files that name the symbols.

```
baseline (clean a8b9e4e)                  3249 passed, 2 skipped in 533.00s
with BOTH boundary mutations applied      3249 passed, 2 skipped in 518.98s   <- identical
```

The two applied together were `version_history_start` returning `+ 1` instead of `+ 2`, and `VH_MARKER = "Version History"`. Not one test of 3251 moved. (Consistent with the call graph: `grep -rn` across the tree excluding `.git` finds no reference to either symbol outside the two scripts and the mutation spec's own `find` string.)

The first-pass scoring, over the three files that name the symbols, with live controls:

```
mutation                              verdict   suite
boundary-leaks-3-lines-upward         CAUGHT    2 failed, 152 passed   <- control, harness is live
line-tail-drops-the-range-arm         CAUGHT    1 failed, 153 passed   <- control
line-digits-is-identity               CAUGHT    4 failed, 150 passed   <- control
boundary-off-by-one-upward            SURVIVED  154 passed
boundary-off-by-one-downward          SURVIVED  154 passed
marker-loses-the-hash-prefix          SURVIVED  154 passed
```

- `boundary-off-by-one-upward`: `version_history_start` returns `+ 1` instead of `+ 2`. The demotion begins **one line above the heading** — this is exactly the F1 leak, shipped as a permanent off-by-one, and the **full** suite is green.
- `boundary-off-by-one-downward`: returns `+ 3`. The heading line itself falls out of the section. Green.
- `marker-loses-the-hash-prefix`: `VH_MARKER = "Version History"`. Any document that merely *mentions* the words silences everything from that point on, **and** corrupts the assembler's `_trim_version_history` at the same time — the single-anchor design turns one mutation into two broken consumers. Green on the **full** suite. This is the sharpest one: the commit's stated benefit of a single shared literal is that a change to it is caught once rather than drifting; in fact a change to it is caught **nowhere**.

The spec's only boundary row is `the-version-history-demotion-covers-the-whole-document`, which replaces `in_vh`'s body with `return True`. A maximal mutation does not test a boundary; it tests that the boundary exists. `test_a_body_pin_still_fails_when_the_document_has_a_version_history` places its body pin far from the heading, so nothing pins the adjacency.

Add a test asserting a hard finding on the line **immediately** above the heading still fails, and a mutation on the `+ 2`.

---

### F6 — CONFIRMED — a document can now silence its own gate by adding a heading, which is the thing `historical_by` exists to refuse

```
CASE e8_silencer -> PASS issues= 0
   # doc = header, then `## Version History` at L6, then TBD + stale pin + `timeout=…`
   ALLOW PLACEHOLDER TBD L9 / PINDRIFT src/target.py:2 L10 / PLACEHOLDER timeout=… L11

CASE e5_fenced   -> PASS issues= 0
   # `## Version History` inside a ``` fence near the top; real body below
   ALLOW PLACEHOLDER TBD L9 / PINDRIFT src/target.py:2 L10
```

`historical_by`'s docstring, in the same file, unchanged by this commit:

> deliberately a CLI flag rather than a marker in the document, because a document that can mark its own pins historical can silence its own gate permanently and silently, which is the masking this was raised to fix rather than a cure for it.

The new rule is a document-side marker with **strictly wider reach** than the thing that refusal protects against: it covers all four hard kinds rather than `PINDRIFT` alone, it needs no operator input at all, and — unlike `--allow-historical`, which names one pin — one heading covers an unbounded region (F2). The in-code rebuttal ("here the precheck follows a decision the ASSEMBLER already made about the same section") is the claim F3 falsifies.

Two things make this less than Critical and I record them honestly: every demotion still prints under `ALLOWED:`, and the `## Version History` heading in a *phase* document is written by the same author under an existing contract. But the fence case is not author intent at all — it is a code block being read as document structure, in a scanner that **already tracks fences** (`in_fence`, computed at :441 and used at :572 for the sha detector) and does not consult that state here.

---

## Minor

### F7 — CONFIRMED — `_version_history_start` leaks `sys.path` entries and shadows the import path

```python
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from h_mad_assemble_audit import version_history_start
except ImportError:
    return None
```

The insert is unconditional, outside the `try`, and never removed. Executed:

```
sys.path len before=8 after 5 calls=13
sys.path[0:3]= ['…/h-mad/scripts', '…/h-mad/scripts', '…/h-mad/scripts']
```

`scan()` is an in-process API (the tests import it), so a caller that scans N documents grows `sys.path` by N and leaves the h-mad scripts directory at **position 0** for every subsequent import in the process — shadowing any stdlib or site module with a colliding name. `h_mad_archreview_cycle._trim_vh` does the same thing, so this is house style rather than a novelty, but the new call site is per-`scan()` rather than per-process. Guard with `if p not in sys.path`, or use `importlib.util.spec_from_file_location`.

### F8 — CONFIRMED — the rationale the commit declares false still ships in the test and in the mutation spec

The commit message and both source comments go out of their way to retract one justification:

> NOT "text no reviewer will see", which is false: `--vh-tail` defaults to None, a strict no-op, so the history is inlined by default.

It is still the opening sentence of the test that encodes the behaviour, `test_a_pin_inside_the_version_history_does_not_fail_the_document`:

> *"The assembler omits the Version History from the audit prompt, so a hard finding drawn only from it fails the document on text no reviewer will see."*

and of the new mutation spec's `_why`, `precheck_l_pin_and_version_history.json`:

> *"pins inside `## Version History` were scored live, failing a document on text the assembler already omits from the audit prompt (§3)"*

Three artifacts carry the rationale; two carry the version the author declared false in the same commit. A reader reaching the rule through the test — which is how a mutation spec's `test` key routes them — reads the retracted argument.

### F9 — SKILL.md §2846, the canonical description of this gate, was not updated

`h-mad/SKILL.md:2846` enumerates the hard/advisory split in full and is the operator-facing contract for `h_mad_precheck_doc.py`. It gains no mention of the Version History demotion — a new whole-class rule that changes what the gate fails on. In the same paragraph it asserts:

> `--allow` is an input, never inferred.

directly beside a new demotion that is **entirely inferred from the document's own content**. The commit message cites `SKILL.md:2846` by line for a *different* residual, so the line was read in this session and left stale.

The operator-facing usage section says the same thing in the same direction (`SKILL.md:1637-1650`): *"`--allow <substring>` records a deliberate hit; it is an INPUT and is never inferred."* `grep -n "Version History" h-mad/SKILL.md` returns 9 hits, none of them in either precheck section. An operator reading the documented contract cannot learn that a `PASS` may now be a demoted `FAIL`.

### F10 — CONFIRMED — mixed range spellings parse asymmetrically, and the unparsed one is silent

```
CASE e9_rev -> FAIL issues= 3
   FIND LINEPIN  L5 `src/target.py:L00012` past_eof — the file has 4 lines
   FIND PINDRIFT L5 `src/target.py:L2-L1`     (reversed range: no crash, first=2)
   FIND PINDRIFT L5 `src/target.py:L0`        (line 0: accepted as a pin)
   # `src/target.py:2-L9`, `src/target.py:L2-`, `src/target.py:L` produce NOTHING
```

`_PATHISH`'s new branch is `L\d+(?:-L?\d+)?`, so `L2-9` and `L2-L9` parse but `2-L9` matches no branch at all — `_PATHISH` fails outright and the span is dropped with no advisory. Given the help now advertises the two spellings as interchangeable, the mixed order that is entirely invisible is the surprising one. `:L` and `L0` are pre-existing shapes (`:0` behaved identically before), and `L00012` normalises correctly.

**No crash vector found, and I looked hard for one.** 16 hostile tails executed (`exp4.py`), zero non-zero exits:

- `L` + 5000 digits and 5000 bare digits → no finding at all. `_CODE = re.compile(r"`([^`\n]{1,200})`")` caps a span at 200 characters, so Python 3.11's 4300-digit `int()` limit is unreachable through this path. At 150 digits (inside the cap) `int()` handles it and a normal `LINEPIN past_eof` is emitted.
- Non-ASCII digits: `:٣`, `:٣-٥`, `:L٣`, `:L٣-L٥`, `:１２`, `:L１２`, `:𝟚` all parse and score. Python's `re.\d` matches exactly the Unicode `Nd` category and `int()` accepts exactly that category, so the two can never disagree. Behaviour is identical to `a8b9e4e^` (the old `tail.isdigit()` was also true for these).
- `:L2<ZWSP>`, `:L²`, `:L-1`, `:L+2`, `:L 2`, `:L2:3` → no `_PATHISH` match, dropped; `:L2_3` → `SYMBOL` advisory. None manufacture a finding.

---

## Checked and found correct — recorded so the absence of a finding is not silence

- **The headline fix works.** `path.py:2` and `path.py:L2` now produce identical `PINDRIFT` findings (`e1_parity`, `FAIL issues=2`, one per spelling), and the finding prints the spelling the document used.
- **The `hard()` router claim is exact.** `grep -n "findings.append\|hard(" h_mad_precheck_doc.py` → exactly **one** `findings.append`, at :391 inside `hard()`, and **six** call sites (:452 :460 :465 :506 :534 :598). I diffed each against `a8b9e4e^`: no message text, no kind, and no destination list changed at any of the six. The commit's "six sites, one router" claim holds.
- **The corpus delta claim reproduces exactly.** 44 phase documents scored with both scripts:
  ```
  gate-blindness-hardening.impl-plan.md      FAIL issues=2  -> PASS issues=0
  regression-provenance-ledger.impl-plan.md  FAIL issues=11 -> FAIL issues=9
  ```
  and nothing else moved — matching the commit message line for line, including the four demoted tokens all printing under `ALLOWED:`.
- **The four demoted findings really are narration, and I read them rather than taking the claim.** `gate-blindness-hardening.impl-plan.md:467` is *"**TBD placeholders removed.** Every `"detail": ...` is now the exact string"* and `:471` is *"**`<v>` placeholder** in the stub's error message replaced with `${HMAD_STUB_HOSTILE}`"*; `regression-provenance-ledger.impl-plan.md:457` names two halt ids inside a *"resolved in v1.7"* entry. All four are `- v1.N` history bullets describing a fix already made. The premise of the change is sound; my findings are about its *boundary* and its *justification*, not its intent.
- **The `ALLOWED:` echo really prints** (`main()` :663, `for a in allowed: print(f"ALLOWED: {a}")`), so "demoted, never dropped" is true.
- **The over-correction guard holds.** `src/target.py:Loader` still reads as a `SYMBOL` advisory (`PASS`); both `_PATHISH` and `_LINE_TAIL` require a digit after the `L`.
- **The range non-coverage claim is true** (F4, closing paragraph).
- **All 14 `find` strings** in the three touched mutation specs resolve to exactly one occurrence in the shipped source — no silently-no-op mutation row.
- **`h_mad_archreview_cycle._trim_vh` precedent claim is accurate** — it does reach into `h_mad_assemble_audit` rather than copying, with the same `sys.path.insert` pattern.
- **Boundary at `+ 2` is arithmetically correct for LF-only text** — I drove `version_history_start` directly: `"a\n## VH"`→2, `"a\nb\n## VH"`→3, both matching `splitlines()`. The heading-at-line-1 → `None` case behaves as documented.
- **Suite is green at `a8b9e4e`**: `3249 passed, 2 skipped in 533.00s`. (The commit message says "suite 3251 passed"; the real shape is 3249 passed + 2 skipped = 3251 collected. Noted for accuracy, not filed as a finding.)

---

## Suggested order of repair

1. **F4** — one extra `historical_by` arm, or normalise inside `historical_by`. Smallest fix, and it closes a shipped false statement in user-facing help.
2. **F1** — compute `vh_start` from `splitlines()` so the two agree by construction. Two lines.
3. **F5** — a test on the line immediately above the heading, plus a `+ 2` mutation row. This is what would have caught F1 before it shipped.
4. **F2** — bound the section at the next `##`/`---` the way `h_mad_version_history.section_bounds` already does, and consult `in_fence`; or, if the loose boundary is genuinely wanted, say so against `h_mad_version_history`'s recorded refusal rather than against the assembler.
5. **F3 / F8 / F9** — bring the three surviving prose accounts (comment, test docstring, spec `_why`) and `SKILL.md:2846` into line with what the code does.
6. **F6** is the design question the above resolve or sharpen; **F7** and **F10** are cheap and independent.
