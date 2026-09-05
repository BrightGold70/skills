# Plan: doc-block-exec

## Executive Summary

Add a stdlib-only helper that runs an explicitly tagged bash block out of a markdown document, and
migrate the one existing hand-written harness onto it, so that paste-along recipes in these skills
are covered by the suite instead of by an operator discovering their defects.

## Overview

These skills document operator recipes as fenced bash blocks. Prose review and a green suite both
passed over four real defects in one such recipe — a phase-hardcoded path, an unimplemented halt,
whitespace truncation, and a bare `exit` that kills an interactive shell — and all four surfaced
only when the block was extracted and executed against fixtures. That extract-substitute-run
harness exists exactly once, inline in a test, so the next recipe worth covering pays to rewrite
it. This matters now because the recurrence counter on the candidate row reached 4, and because
the migration is cheapest while there is a single consumer to migrate.

## Scope

In scope: one new helper module with an importable API and a verdict-token CLI; one info-string
tag convention on bash fences; the tagging of exactly one existing fence; the migration of the
**one executing** call site that hand-rolls this in
`h-mad/tests/test_h_mad_collect_report_docs.py` — located structurally, since a line pin in that
file has gone stale once already: the `re.findall` inside the module-level `_gate_bash_block()`
helper, plus the `run_recipe` nested in
`test_documented_gate_recipe_halts_instead_of_gating_an_empty_path` that runs what it returns —
both re-read at `74e126f`, with the extraction half carrying its command in the extractor census
under §Measurements; and — the
scope increase the design audit forced, tagged AC-1.8 — `h-mad/tests/docsections.py` dropping its
duplicate bounder to delegate to the authoritative one, with the three deliverables that carries
(`docsections.py`, `mutation-specs/docsections.json`, `test_docsections.py`). §Deliverables and
§Implementation Strategy carry it too, and a scope increase absent from §Scope is the surface a
downstream reader — or a 5c task split — reads first.

User-visible behaviour: an operator can run a documented recipe under test by hand with a single
command; a fence carrying the tag is executable and every other fence in the tree is not.

**Transport of the three reported values.** Every invocation that judges input prints exactly one
`DOCBLOCK:` verdict line — one *physical* line whatever the inputs, with `--help` alone excepted
(it keeps argparse's exit-0 help text and emits **zero** `DOCBLOCK:` lines; the carve-out is stated
in full in the CLI-contract paragraph below): every dynamic field (`heading=`, `arg=`, `index=`, keys,
paths, OS-error text, `leftover:`) is rendered through one escaper, `_field`, as a double-quoted
JSON string (`json.dumps(str(value), ensure_ascii=False)` plus a second pass escaping every
remaining `Cc`/`Zl`/`Zp` character — DEL, the C1 range with U+0085, U+2028/U+2029; everything
else verbatim), so a caller- or document-controlled value can neither start a
second `DOCBLOCK:` line nor forge a field token inside it — `--heading 'x rc=0'` renders as
`heading="x rc=0"`, one quoted value, never a bare `rc=` on a refusal line (AC-4.3); the bare
list is `rc=`, `blocks=`, `count=`, `keys=`, `shell=`, `stage=`,
`reason=` — and every other field, the helper-produced numbers `seconds=` and `pgid:` included, is
JSON-quoted (the design states the same seven in the paragraph opening `Verdict lines, one per run.`,
addressed by that literal because it is a paragraph lead and **not** a heading —
`git show b3be433:<design> | grep -nE '^#{2,4} '` piped to `grep -i erdict` prints **nothing**,
while `grep -c 'Verdict lines, one per run.'` over the same body returns **1**, so the
`design v1.79 §Verdict lines` pointer this clause carried through v1.100 named neither a live
version nor a real section and could not be followed;
`test_newline_in_dynamic_fields_cannot_forge_a_verdict_line` drives
a newline-bearing `--heading`, `--subst` and a newline-named created `--stdout` artifact on the
AC-3.10 rollback fixture, `test_dynamic_field_cannot_forge_a_token` drives `--heading 'x rc=0'`;
mutations `field-escape-removed`, `field-quoting-removed`) — that contract is not weakened. **That
set has two halves and they are escaped for two different reasons; through v1.98 this paragraph ran
them together into one conjunction — "which `json.dumps` leaves literal *and* `splitlines()` breaks
on" — and the conjunction is false of most of the set.** Executed per code point under
§Measurements, "`json.dumps` line-breaking, per code point": `json.dumps(…, ensure_ascii=False)`
leaves **35 of 35** literal, and that 35 is *exactly* the set this paragraph names (DEL + the 32
C1 code points + U+2028 + U+2029, set-equal to the measured survivors), so the first conjunct is
true of every member. The second is true of **three** — U+0085, U+2028, U+2029 — and those three
alone are what the one-*physical*-line transport invariant above (AC-4.3) turns on. **DEL and the
other 31 C1 code points break nothing**: each yields exactly one line. They are escaped for the
separate reason that an unescaped control byte is unrenderable inside a line a human, a terminal or
a `grep` has to read, and it would let a value smuggle bytes past a reader that a machine consumer
parsing the quoted-string grammar still sees. Both reasons are load-bearing and neither implies the
other, which is why they are now stated apart. `rc` is a field on that line. The block's `stdout` and `stderr` are
**separate artifacts, not part of the verdict line**: returned as distinct fields from the
importable API, and on the CLI written to paths given by **optional** `--stdout <path>` /
`--stderr <path>` arguments. Omitted, the streams are simply not written — the API is the primary
consumer and the suite reads the fields, so requiring the flags would make every in-process caller
invent a path it never reads. A path that cannot be written is a refusal,
`DOCBLOCK: UNREADABLE reason=stream_path_unwritable`, exit 2 — checked **before** the block runs,
so a recipe is never executed only for its output to be discarded.

Left unstated, an implementation can satisfy "one verdict line" while dropping the streams, or
print the streams inline and break every consumer that parses the verdict line.

**"The bare list is exhaustive" is a claim about a set four documents state, and through v1.100
this document asserted it from one of them.** The clause read "the bare list is exhaustive and
exactly the design's" — a property of the design's `Verdict lines, one per run.` paragraph,
generalised to the feature without a census. Censused body-scoped at `b3be433` over all four
documents and **every occurrence classified**, which is the half a bare count cannot do:

```
$ for f in docs/01-plan/features/doc-block-exec.spec.md \
           docs/01-plan/features/doc-block-exec.plan.md \
           docs/02-design/features/doc-block-exec.design.md \
           docs/01-plan/features/doc-block-exec.impl-plan.md; do
    b=$(git show b3be433:$f | awk '/^## Version History/{exit}{print}')
    printf '%s  pgid= %s  of which LaunchFailed( %s   pgid: %s\n' "$(basename $f)" \
      "$(printf '%s\n' "$b" | grep -oF 'pgid=' | wc -l | tr -d ' ')" \
      "$(printf '%s\n' "$b" | grep -oE 'LaunchFailed\([^)]*pgid=' | wc -l | tr -d ' ')" \
      "$(printf '%s\n' "$b" | grep -oF 'pgid:' | wc -l | tr -d ' ')"
  done
doc-block-exec.spec.md       pgid= 1  of which LaunchFailed( 0   pgid: 0
doc-block-exec.plan.md       pgid= 0  of which LaunchFailed( 0   pgid: 1
doc-block-exec.design.md     pgid= 5  of which LaunchFailed( 4   pgid: 10
doc-block-exec.impl-plan.md  pgid= 6  of which LaunchFailed( 6   pgid: 8
```

**The token `pgid=` carries two unrelated grammars and a census that does not separate them reads
neither**: a Python keyword argument to `LaunchFailed(stage, err, pgid=…)`, which is a constructor
call and never reaches a verdict line, and a bare `=` field on the emitted line. **Ten of the
twelve** `pgid=` occurrences in the feature are the kwarg. **Both integers are the column sums of
the fence above — `1 + 0 + 5 + 6 = 12` and `0 + 0 + 4 + 6 = 10` — and are written as that arithmetic
so the check a reader runs is addition on this page and not a second measurement.** v1.101 published
`eleven` here, and the defect is not the digit: it is that a prose summary was *restated* beside a
fenced census instead of *derived* from it, after which the two surfaces drift independently and only
the prose one is unrunnable. **The class over that axis: every integer this document states about a
table or fence printed in this same document is written as the arithmetic over that surface's own
values, never as a free-standing figure.** Residual, exact: the rule makes the summary re-derivable
from the fence and says nothing about whether the fence is right — that is the census command's sha
to answer, which is why the sha sits inside the command. **Emitted-field spellings, which is the
population the exhaustiveness claim is about**: the **spec** spells it **bare**, `pgid=<n>` on the
verdict line, at AC-4.6 and nowhere else — its one occurrence, with `LaunchFailed(` accounting for
none of it. The **design** spells it **quoted** in its `_field` example and in its verdict table
(`pgid: "4242"`, `(+ pgid: "<n>" when stage=reap or stage=collect)`) and names `pgid:` as a detail
key in four further places — **and also spells it bare once**, in its own AC-4.6 row, whose
non-kwarg occurrence is the single line
`git show b3be433:<design> | awk '/^## Version History/{exit}{print}' | grep -oE '.{60}pgid=.{20}' | grep -v LaunchFailed`
returns: `` `LAUNCH_FAILED stage=reap` within the drain bound, cwd gone, `pgid=` in the detail ``.
The **impl-plan** spells it **quoted** only, as a `DETAIL_KEYS` member rendering `pgid: "4242"`;
its six `pgid=` are six kwargs. **This document carries the emitted field in neither spelling**:
its single `pgid:` is the clause above, naming it as a member of the JSON-quoted set.

**The plan row is the one row of the four that this paragraph itself moves, and that is stated
rather than left to trip a re-runner**: the census is stamped `b3be433`, where this document's row
reads `pgid= 0 / LaunchFailed( 0 / pgid: 1`. Over any later working tree it reads much higher, and
**no working-tree value is published here, because there is no fixed point to publish** — telling
the two grammars apart requires writing both of them out, and every sentence stating the new
reading raises it again, which was confirmed by running the command after each of two successive
edits. **A census whose corpus includes the document publishing it is read at a landed commit and
at no other**, which is this document's standing rule and the reason the sha sits inside the
command rather than beside it. The other three rows are of siblings and are unaffected by anything
written here, which is why they are the rows the conclusion rests on.

**So at `b3be433` the four documents did not agree, the design disagreed with itself, and there was
no consensus spelling to harmonise on** — every clause of that conclusion is past tense against that
sha, because it is drawn from the census above and a conclusion inherits its census's commit. What
this document claims is exactly what it derives: the seven bare fields above are the seven the
design's `Verdict lines, one per run.` paragraph states, and `pgid` is quoted **in this document's
own contract**. Both repairs were reported to their authors and **neither was made here**, because a
cross-document repair issued from one document is how two surfaces come to state one rule twice.

**Both landed in `00b961f` — the same commit that landed the paragraph reporting them as pending —
and that outcome is recorded here rather than left for a later round to find.** Re-derived at
`00b961f`, one command per reading: the spec's body carries **zero** bare `pgid=` and FR-4 spells
the detail key `pgid:`; the design's AC-4.6 row carries **two** `pgid:` and **zero** bare `pgid=`,
and the four `pgid=` left in its body are all `LaunchFailed(…)` constructor kwargs.

```
git show 00b961f:docs/01-plan/features/doc-block-exec.spec.md \
  | awk '/^## Version History/{exit}{print}' | grep -c 'pgid='                  # -> 0
git show 00b961f:docs/02-design/features/doc-block-exec.design.md \
  | grep '^| AC-4.6' | grep -oE 'pgid[=:]' | sort | uniq -c                     # -> 2 pgid:
git show 00b961f:docs/02-design/features/doc-block-exec.design.md \
  | awk '/^## Version History/{exit}{print}' | grep -oE '.{0,30}pgid=.{0,15}'   # -> 4, every one LaunchFailed(
```

**The class is not `pgid` and not this paragraph's subject: it is the tense of a claim about another
document.** A sentence saying a sibling *still owes* something is a measurement of a tree, and the
tree it measures is changed by the very commit that publishes the sentence — three of this feature's
four documents each recorded this same debt in `00b961f` while `00b961f` discharged it, and no
author could see it, because each read siblings being revised in the same batch. **The rule over
that axis: a claim about what another document currently states is written at a named sha and in the
past tense, and the revision's own Version History entry either names the outcome at its landing
commit or records that the landing commit was not read.** Residual, and it is not closeable from
inside one document: when the author writes the sentence the landing commit does not yet exist, so
the outcome can only be appended by the round that lands it or corrected by the next — which is what
this paragraph is. **The `00b961f` readings above are the only two `pgid` claims discharged**; the
two non-`pgid` items the v1.101 entry reported to the spec — the `2486` in AC-6.4 and the absence of
`BAD_ARGS` from AC-4.2's exit-0 enumeration — **both still reproduce at `00b961f`** and are not
swept away with them:

```
git show 00b961f:docs/01-plan/features/doc-block-exec.spec.md \
  | awk '/^## Version History/{exit}{print}' | grep -c '2486'                        # -> 1
git show 00b961f:docs/01-plan/features/doc-block-exec.spec.md \
  | awk '/^## Version History/{exit}{print}' \
  | sed -n '/^  - AC-4.2:/,/^  - AC-4.3:/p' | grep -c 'BAD_ARGS'                     # -> 0
```

**Both were discharged by spec v1.62, and the outcome is measured at `af19d53` rather than left to
the reader** — the same two commands with `af19d53` in place of `00b961f` return **2** and **2**.
The `2486` survivors are retrospective, naming it as the retired half of the `2748`/`2486` pair
rather than asserting it, and `BAD_ARGS` now sits inside `AC-4.2`'s exit-0 enumeration, which is
what the second command was written to detect the absence of. **Neither `2` is a range leak**:
`grep -c '^  - AC-4.2:'` over the same `awk`-stripped body returns **1** at both `00b961f` and
`af19d53`, so `sed` opens exactly one range. **This is the tense rule applied to this document's own
sentence rather than only stated by it**: v1.101 wrote the debt in the present tense, v1.102 recorded
its discharge as a dated observation of an uncommitted tree because that was all it could see, and
this is the first revision able to name a commit. Residual, unchanged and not closeable from inside
one document: the author of the sentence still cannot see the commit that will land it.

**Both commands are body-scoped, and the `awk` prefix on the second one is load-bearing rather than
decorative** — this was written first as a bare `sed` range over the whole file, and it returned
**1** instead of `0`: `AC-4.2` occurs again inside the spec's own §Version History, where `sed`
opened a second range that never met its `^  - AC-4.3:` terminator and printed to end of file,
dragging an unrelated `BAD_ARGS` into the count. **The class, and it is a general property of `sed`
address ranges and not of this spec: an unterminated second range prints to EOF, so a range command
over a document with a §Version History is scoped to the body before the range is applied, exactly
as every count in this document already is.** Residual: `awk`-scoping fixes the corpus and not the
range — a body that genuinely repeats the opening address twice would still print two ranges, and
that is caught by reading the range's output, which is why it is printed and not only counted.

**The class, and it is not `pgid`.** The axis is *an exhaustiveness claim about a set more than one
document states*. The rule over it: such a claim is derived by a census over **every** surface that
states the set, with every occurrence **classified by grammar before any of them is counted**, or
it is not made — an exhaustiveness claim sourced from one surface is a claim about that surface and
says nothing about the other three. **Residual, stated as a category and not as this token**: the
census needle is a **literal string**, so a surface that states a member in prose without writing
the token — "the seconds field stays bare" — is invisible to it, as is a member nobody has thought
to name. The census bounds the documents' *spellings*; it does not bound their *intent*, and it is
not a screen a later revision can run unattended, because the grammar split is read by a human.

**The CLI contract, in full.** `h_mad_doc_block_exec.py <doc> --heading <h> [--index N]
[--subst K=V]... [--preamble-file PATH] [--shell-timeout SECONDS] [--stdout PATH]
[--stderr PATH]`, and nothing else — no `--all`, `--dir` or glob argument, pinned by a
parser-rejection test. `--subst` values are split once on the first `=` (a value may contain `=`;
`K=` is an empty value); no `=`, an empty key, or a repeated key is `BAD_SUBST arg="<raw>"` (exit 0,
`duplicate_key:` detail for the repeat), judged before anything is reserved (AC-2.8). There are
**no abbreviated spellings**: the parser is built with
`allow_abbrev=False`, so `--shell-t` or `--pre` are rejected rather than silently accepted as
undocumented aliases (test: `test_parser_rejects_all_dir_and_abbreviations`). Argument *values* are
validated by `main` and map to verdict lines — `--index` non-integer or below 1 → `BAD_INDEX`,
`--shell-timeout` non-numeric, non-finite or not positive → `BAD_TIMEOUT value="<v>"` (AC-5.6), both
before any spawn; argparse grammar errors (unknown option, missing value) are routed through the
parser's overridden `error()` to `DOCBLOCK: BAD_ARGS message="<m>"`, exit 0 — there is no
non-`DOCBLOCK` exit (`--help` alone excepted: it keeps argparse's exit-0 help text and emits no
`DOCBLOCK:` line, which is why the contract is stated with that carve-out in spec AC-5.6, design
§API and impl-plan §Conventions; this document was the one of the four the v1.31 sweep missed).
**The carve-out has three surfaces in this plan, and the sweep is by claim rather than by phrase**:
this paragraph, the transport paragraph's "one *physical* line whatever the inputs" above, and
§Implementation Strategy's "the CLI prints exactly one verdict line" — every sentence that
quantifies over inputs or over emitted lines is a surface of it, which is why the v1.84 fix
grepping one phrasing landed on one of the three. The residual: `--help` is the **only** such
exception, and a second one would need the same three-surface edit.

**"Three surfaces" is a population claim over prose, and through v1.98 it was published with no
screen at all — here is one, run at the freeze, per branch, with its controls and its measured blind
spot.** It is run over `git show 700c599:<doc>` rather than over the working tree for the reason the
stamp-driven driver under §Measurements is: the alternation is written into the body it scans, so a
working-tree run counts its own needles. **The screen is paragraph-scoped, and that is the finding
rather than a detail** — surface two's own carve-out sentence wraps across a line break ("…there is
no / non-`DOCBLOCK` exit…"), so no *line*-scoped grep can reach it, and the line-scoped union
returns 5 lines that resolve to surface one, surface three and this paragraph's own quotations of
those two, with surface two absent:

```
$ D=docs/01-plan/features/doc-block-exec.plan.md
$ git show 700c599:$D | awk '/^## Version History/{exit}{print}' \
    | awk 'BEGIN{RS=""}{gsub(/\n/," ");print NR"\t"$0}' \
    | grep -cE 'exactly one .*verdict|one \*physical\* line|prints exactly one|verdict line for|no non-.DOCBLOCK. exit'
3
$ # the same alternation without the paragraph join, which is what an audit ran by hand:
$ git show 700c599:$D | awk '/^## Version History/{exit}{print}' \
    | grep -cE 'exactly one .*verdict|one \*physical\* line|prints exactly one|verdict line for|no non-.DOCBLOCK. exit'
5
```

Per branch, printing the matched paragraph's ordinal rather than a count, because the counts alone
cannot show *which* surface each branch reaches — `exactly one .*verdict` **9 11 19**,
`prints exactly one` **9 11 19**, `one \*physical\* line` **9 11**, `verdict line for` **19**,
`no non-.DOCBLOCK. exit` **11**. Read that per-branch table rather than the union: paragraphs 9 and
19 are surfaces one and three, and paragraph 11 is this one. **Three branches reach paragraph 11
only through the quotations in this sentence — they match text *about* the other two surfaces —
and exactly one branch, `no non-.DOCBLOCK. exit`, reaches paragraph 11's own carve-out claim.**
Drop that branch and the screen still returns 3 paragraphs while having read surface two's carve-out
not at all: a union that is right for the wrong reason, which is the DECISION O shape at the level
of a screen instead of a fixture. Controls, both directions, on `awk version 20200816`:

```
$ FIX='A: the CLI prints exactly one verdict line for every judged input.\n\nB: a wrapped claim, there is no\nnon-`DOCBLOCK` exit from this parser.\n\nC: the block writes one line to stdout and nothing else.\n'
$ ALT='exactly one .*verdict|one \*physical\* line|prints exactly one|verdict line for|no non-.DOCBLOCK. exit'
$ printf "$FIX" | awk 'BEGIN{RS=""}{gsub(/\n/," ");print NR"\t"$0}' | grep -E "$ALT"
1	A: the CLI prints exactly one verdict line for every judged input.
2	B: a wrapped claim, there is no non-`DOCBLOCK` exit from this parser.
$ printf "$FIX" | grep -E "$ALT"
A: the CLI prints exactly one verdict line for every judged input.
```

So the positive fires under both forms, the **wrapped** positive fires only under the paragraph-joined
form — which is the property the screen is chosen for, executed rather than asserted — and the
negative (a sentence saying "one line" while quantifying over nothing) is declined by both.
Residual, and it is why the sentence above still says the sweep is **by claim**: this is a phrase
alternation, so a fourth surface phrased in words none of the five branches carry — "at most one
line on stdout", say — is invisible to it, and the screen is a starting point for the hand sweep
rather than a replacement for it. Second residual, **measured after this revision's last edit rather
than estimated, and the estimate would have been wrong**: writing the alternation and its two
fixtures into the body makes them permanent self-matches, so the same paragraph-joined command run
over the **working tree** returns **6** where the `700c599` run above returns **3** — three added
paragraphs, this revision's screen prose and its two fenced fixtures, none of them a surface. That
is why the published reading is the freeze run and why this document's rule is that a figure whose
corpus is this document is stated at a **landed** commit; a reader re-running the screen over a
later working tree must expect the self-matches and subtract them by reading, which is the same
exposure the members table's needles carry and is closed the same way — by the commit argument, not
by paraphrase.
**`exit_on_error` stays at argparse's default `True`** — an earlier draft said `False`, which
suppresses argparse's own `except ArgumentError: self.error(...)` so a *missing option value*
raised `argparse.ArgumentError` past the override and out of `main` as a non-`DOCBLOCK` traceback;
measured on python 3.11.8, the default routes all five grammar shapes to the override (design
§API carries the table) (design v1.85; `test_malformed_invocation_is_a_verdict`, mutation
`argparse-error-unrouted`). `--preamble-file` is the CLI face of AC-3.11/3.12: `main` reads the file
**before** any spawn, and an unreadable path maps to `UNREADABLE reason=preamble_unreadable`, exit
2, block not run — for a path that cannot be read **and** for a file that is not valid UTF-8,
since the preamble is read strictly and text that will execute is never silently repaired (tests:
`test_unreadable_preamble_path_refuses` and
`test_invalid_utf8_preamble_is_unreadable` — the node ID the design's `preamble-decode-error-unwrapped` mutation binds, one name on every surface — each with a block whose side effect the
test asserts is absent; the document gets the same treatment under `doc_unreadable`). The preamble and the block are composed as
`preamble.rstrip("\n") + "\n" + text′`, with `text′` the block text *after* substitution, so the
preamble precedes what actually runs — one newline boundary, always — so a preamble file
that lacks a trailing newline cannot fuse with the recipe's first line
(test: `test_preamble_without_trailing_newline_still_precedes_the_block`, whose preamble sets a
variable and ends without `\n`, and whose block's first line reads it). The registry entry carries a detail row for that reason
like every other emittable line (AC-4.5). **Stream artifacts have overwrite semantics and are
reserved after every check, and no open ever truncates**: after extraction, selection,
substitution and every remaining pre-spawn validation (timeout, preamble readability — the info
string was validated inside `extract` and the ordinal inside `select`) have passed, both paths are
reserved with the atomic create-or-open protocol the design specifies (exclusive create records
ownership; `FileExistsError` → open the existing file *without* `O_CREAT` **and with
`O_NONBLOCK`**, so a reader-less FIFO fails at once with `ENXIO` instead of blocking before any
`DOCBLOCK:` line or timeout can exist; `ENOENT` there → restart the exclusive create, so every file
this call creates is recorded as created; every reserved descriptor is then `fstat`ed and must be
a **regular file** — a FIFO, socket, device or directory refuses `stream_path_unwritable`, judged
on the descriptor so there is no check-to-open race — tests
`test_stream_path_fifo_without_reader_refuses_bounded` (an `os.mkfifo` `--stdout`, refusal within
a second, block never run), mutations `nonregular-stream-accepted` and `stream-open-blocking`),
the handles held, and only then compared for aliasing on their descriptors — append creates a missing file
and never empties an existing one. The truncation is the final write itself — `seek(0);
truncate(); write; flush(); close()`, all five inside the module's `_final_write(handle, text)` — the `close()` in a `finally`, so an `OSError` from any earlier step still releases the descriptor before the exception is mapped, and `main`'s own `try`/`finally` around both reservations closes, through the one closure primitive `_close_stream(handle)`, whatever `_final_write` never reached — a backstop close that fails is recorded, never raised from the `finally`, and selected afterwards as `UNREADABLE reason=stream_close_failed` (exit 2, `os_error:` line) unless an exit-2 error is already pending, which wins with the close error as its `__context__` (tests `test_backstop_close_failure_on_timeout_is_mapped`, `test_backstop_close_failure_does_not_outrank_a_refusal`; mutations `backstop-close-unmapped`, `backstop-close-outranks-error`) —
because a buffered `TextIOWrapper` may defer the OS write until `flush()`/`close()` and an error
surfacing at a close outside the mapped region would be a traceback rather than
`stream_write_failed` — on those held handles after a successful run. Writes are ordered stdout
then stderr; a failure on stdout skips stderr (`failed: "stdout"` / `skipped: "stderr"`), a failure on
stderr leaves stdout as written (`written: "stdout"` / `failed: "stderr"`), and every one of those
detail lines has a registry row. **After every close the artifact is read back** and compared to
the stream text — a missing or mismatching file is `stream_write_failed` with a `verify: "<stream>"`
detail line (registry row), so a writer that silently did nothing cannot be reported as `RAN`
(mutation `final-write-not-verified`, test `test_final_write_readback_catches_a_silent_no_op`).
Tests: `test_stream_write_failure_after_the_run_is_a_refusal`,
`test_first_stream_write_failure_skips_the_second`,
`test_second_stream_write_failure_leaves_the_first_as_written`. So a failure to reserve the
second path finds the first untouched (a file this call created is unlinked again; a pre-existing
one keeps every byte), a refusal anywhere earlier touches neither, and a run ending in `TIMEOUT`
or `CLEANUP_FAILED` writes nothing to either. "Reserved, then failed the write" can therefore only
mean a write error on an already-open descriptor (disk full, I/O error), which maps to
`UNREADABLE reason=stream_write_failed`, exit 2, after the run — the block's `rc` is lost with the
artifact, which is the honest outcome, since the artifact the caller was promised does not exist.
Two paths naming one file are refused on the *opened* descriptors — `(st_dev, st_ino)` of the
two reserved handles compared before anything is written, so a hard link is caught as well as a
symlink or a spelling, and there is no check-to-open window (AC-3.9). A refusal there closes both
handles, unlinks one the call created, and touches no bytes. Tests:
`test_stream_paths_truncate_an_existing_file` (a pre-existing file is overwritten, not appended),
`test_stdout_survives_a_failed_stderr_reservation` (pre-existing `--stdout` bytes are identical
after `--stderr` names an unwritable path, and a `--stdout` file the call created is gone),
`test_streams_untouched_after_a_timeout`, and
`test_stream_write_failure_after_the_run_is_a_refusal` (the module's `_final_write(handle, text)`
seam is fault-injected to raise `OSError` — a **named** injection seam, as the backstop close's
`_close_stream` is; seams are named, never numbered, so an added seam cannot stale a count here —
because a held
descriptor cannot be made to fail deterministically on macOS, which has no `/dev/full` — and the
verdict is `UNREADABLE reason=stream_write_failed`), and
`test_second_stream_write_failure_leaves_the_first_as_written` (only the stderr write fails; the
stdout artifact is current and the detail lines say `written: "stdout"` / `failed: "stderr"`), and
`test_stream_path_under_a_regular_file_refuses` (AC-3.10 — a real `ENOTDIR`, no injection; mutation
`stream-open-oserror-unwrapped`).

**The fixture preamble is load-bearing, not a convenience.** A documented recipe may consume a
variable the surrounding prose sets rather than the block itself — the Second-surface gate block
reads `COLLECT_OUT`, supplied by a preamble that runs the real collector. **The with/without pair
that establishes this is owned by the spec's AC-3.11 and is not copied here** — a pointer to the
one surface that owns a measurement never drifts, a second copy does, and through v1.92 this
sentence was a second copy. What matters here is only what the pair rules *out*: the missing
variable is a diagnostic, not a hard abort, so "it aborts" is the wrong reason to require the
preamble and an earlier draft of this paragraph gave it. **The subject of that measurement is
tracked** — the Second-surface gate block lives in `h-mad/SKILL.md` and the collector in
`h-mad/scripts/` — so by the probe carve-out under §Measurements the owning surface must stamp it
with a sha, which is an obligation on the spec and is reported there rather than discharged here.
The limitation that matters is narrower and sufficient: without a supplied
`COLLECT_OUT` the block can never reach the delivered-report `GATE: PASS` branch, which AC-6.3
requires, so the FR-6 migration is impossible without a preamble parameter.

## Goals

- Address a block unambiguously and only by explicit opt-in — FR-1
- Make a substitution that would not apply a refusal rather than a silent no-op — FR-2
- Execute in a disposable cwd from `tempfile.mkdtemp()` — the stdlib call, never the `mktemp -d`
  shell utility — so a recipe's **ordinary relative** writes cannot reach the repository, under
  the shell mode the recipe declares — FR-3
- Report through the same verdict-token contract every other helper here uses — FR-4
- Bound every run without introducing an external time-bounder — FR-5
- Leave no hand-written copy of the harness behind — FR-6

## Requirements

- FR-1: Address a block by document, heading, and explicit tag
- FR-2: Substitute an explicit map, and refuse a substitution that would not apply
- FR-3: Execute in a disposable cwd under a declared shell mode
- FR-4: Verdict-token CLI following the established gate contract
- FR-5: Bounded execution without an external time-bounder
- FR-6: Migrate the existing inline harness onto the helper

## Implementation Strategy

One layer changes: `h-mad/scripts/` gains a module, `h-mad/tests/` gains its suite and a mutation
spec, `h-mad/SKILL.md` gains a Helper-scripts registry entry and one tagged fence, one existing
test file loses its hand-rolled extraction, and `h-mad/tests/docsections.py` loses its duplicate
bounder (with its own mutation spec and test file) — the AC-1.8 scope increase the paragraph
below states in full.

The patterns to follow are already established in this repository and are not being invented here:
a helper exposes importable functions plus a thin CLI; the CLI prints exactly one verdict line for
every invocation that judges input (`--help` alone excepted — see the CLI contract under §Scope);
every verdict — `RAN` and every refusal that judged readable input, `TIMEOUT` included — exits 0,
and exit 2 is reserved for the operational-error class the base invariant reserves non-zero for
— "missing/unreadable input" is its example; `UNREADABLE`, `CLEANUP_FAILED` and `LAUNCH_FAILED`
are this feature's members of that class; the registry entry and the emittable detail lines
are pinned to each other bidirectionally; and every guard gets a mutation that must be caught by a
named test.

**The count rule, stated precisely — the loose form contradicts AC-4.4.** A cannot-judge must
carry no count that could be read as a **measured result**: never an `rc=`, never a findings count,
because that is how "nothing was measured" gets read as "measured, and clean". It **may** carry a
*diagnostic* count explaining why it could not judge. The distinction is already load-bearing
elsewhere in this skill rather than being invented for this feature: `ANCHORS_DRIFTED` and
`ANCHORS_UNREADABLE` both carry `drifted=`/`unreadable=`, and `MUTATION: PRECHECK_FAILED` carries
`specs=`/`drifted=`/`unreadable=` — in each case so the verdict word chooses the first action
without hiding the other finding. (Those helpers also exit 2 on a cannot-judge; this feature does
**not** copy that, because the base Audit-gate signal discipline invariant reserves non-zero for
unreadable input, and the gate and assembler — the documented rule — exit 0 on a rejection. FR-4
states the partition.) `AMBIGUOUS blocks=<n>`
is that same shape: `n` is the number of candidate blocks that *made* the address ambiguous and is
the datum the operator needs to pass `--index`, not a result. So AC-4.4 stands and this sentence
was the error; AC-4.3 (no cannot-judge carries `rc=`) is the invariant that actually matters.

Deliberately untouched: every bash fence in the tree that will not carry the tag — **72 of the 73
counted at `a8e0372`** by the §Measurements census command, a number over a tree that keeps moving
and therefore stated only with the commit it was measured at (it was 67 of 68 at `a469493`) — and
the installed copy under `~/.claude/skills`; the helper is exercised against the checkout.

**One further test file does change, and it is a scope increase the design audit forced.**
`h-mad/tests/docsections.py` currently carries its own `_fence_aware_end`. Keeping both was going
to require a differential test the Single-source contract demands, and that test is unachievable:
the existing toggle stops early inside an unbalanced four-backtick fence, which AC-1.6 forbids the
new scanner from doing. So `docsections.py` imports the authoritative bounder instead — `tests/`
depending on `scripts/` is the correct direction, it removes the duplicate rather than testing
around it, and it fixes a latent bug there. Its public signatures are unchanged and no existing
test pins the old behaviour (three files import it — `test_docsections.py`,
`test_h_mad_review_evidence.py` and `test_h_mad_wire_registry.py`:
`grep -rln 'from docsections import' --include='*.py' h-mad handoff` → those **3** files at
`335f535` — and all three use only `titled_section`/`section_from`).

**The cross-directory import is specified, not implied.** `docsections.py` is imported as a
top-level module while `scripts/` is still absent from `sys.path`, so a bare
`from h_mad_doc_block_exec import …` inside it fails at collection. **The guarantee is import
ORDER, not absence** — two of the three importers *do* insert `scripts/`, just not before they
import `docsections`. Run at `74e126f`:
`grep -n 'from docsections import\|sys.path.insert' h-mad/tests/test_docsections.py h-mad/tests/test_h_mad_review_evidence.py h-mad/tests/test_h_mad_wire_registry.py`
— `test_docsections.py` shows a `from docsections import` line and **no** insert at all, and each
of the other two shows its `from docsections import` line **above** every `sys.path.insert` in the
same file, so `docsections` executes while `scripts/` is still un-importable. Residual, and it is
per-file rather than global: an import-block reorder — isort, an autoformatter, a hand edit —
silently removes the ordering in one file without touching the others, and no assertion in the
suite reads import order. The pin that catches it is the isolated one below, because it imports
the module with no test file in the picture at all — `python3 -c "import docsections"` with only
the tests directory on `sys.path` and an unrelated cwd, which is also what the
`docsections-syspath-setup-removed` mutation is scored against. The arrangement follows the
`SCRIPT_DIR` convention already present in `h-mad/tests/`, and that is a **convention to follow,
not a property of the directory** — the earlier wording here said "every test in `h-mad/tests/`",
which the tree refutes: `grep -l 'sys.path.insert(0, str(SCRIPT_DIR))' h-mad/tests/test_*.py | wc -l`
→ **13** at `35698f9`, against `ls h-mad/tests/test_*.py | wc -l` → **88** (48 carry some
`sys.path.insert`, in several spellings). The instance this feature's own consumer already carries
is the `sys.path.insert(0, str(SCRIPT_DIR))` at the head of `test_h_mad_collect_report_docs.py`,
located structurally rather than by line —
`grep -n 'sys.path.insert(0, str(SCRIPT_DIR))' h-mad/tests/test_h_mad_collect_report_docs.py` →
exactly **1** hit at `35698f9` — because a bare `path:line` pin into that file is precisely the
class §Implementation Strategy declares closed below, and a line pin in that file has gone stale
once already. `docsections.py` itself does
`sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))` immediately before
`import h_mad_doc_block_exec as _dbe`, so it is self-contained and never relies on another module
having inserted the path first — and the call is **module-qualified**, `_dbe.fence_aware_end(…)`,
for the same reason the FR-6 consumer's calls are: the delegation is a *connection*, and the
Connection-enforcement invariant wants it discriminated by an isolated wire mutation with the
callee intact, which needs a spy that a pre-bound alias would hide. **The bounder has a name and a contract**:
`fence_aware_end(text: str, start: int, level: int) -> int` — the offset of the next ATX heading
at `level` or shallower whose line starts at an offset `>= start` (the line adjacent to a heading `find_heading` returned is included; a line that began before a mid-line `start` is not — design v1.60, `adjacent-heading-skipped`), ignoring fenced blocks with CommonMark backtick-run
tracking — exported in the module's `__all__` beside `extract`/`select`/`substitute`/`run_block`,
and the same function `extract` uses to bound its own section. The two call sites replace
one-for-one: `titled_section` **binds the result before it unpacks it** —
`found = _dbe.find_heading(text, heading)`, then its own loud failure on `found is None`, and only
then `start, level = found` — because `find_heading` returns `tuple[int, int] | None` and unpacking
the call directly raises `TypeError` on absence, which bypasses the loud failure this delegation is
required to keep. The impl-plan carries the source form and already writes it this way
(`git grep -c 'found = _dbe.find_heading(text, heading)' 4e4a00c -- docs/01-plan/features/doc-block-exec.impl-plan.md`
→ **4** — its prose, its mutation `find` anchor and two pseudocode bodies); this document stated the
unsafe order through v1.94 and is the surface that was wrong. It then returns
`text[start:_dbe.fence_aware_end(text, start, level)]` — its local heading `re.search` is deleted with
`_fence_aware_end` — and `section_from` returns
`text[offset:_dbe.fence_aware_end(text, offset, level)]` — module-qualified, as the paragraph
below requires; `_fence_aware_end` is deleted. **The replacement is one-for-one at the call site,
not byte-for-byte in the returned body, and the difference is a decision rather than a 5d
discovery**: the `rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$"` that `titled_section` carries at
`74e126f` — reproduced with its `re.escape`, because a source span this document reproduces
verbatim must stay findable by a literal `grep`, and through v1.98 this one was not
(`grep -n 'P<marks>' h-mad/tests/docsections.py` → **1** hit at `74e126f`, and
`git diff --stat 74e126f 700c599 -- h-mad/tests/` is empty, so the hit stands unchanged at the
freeze) — ends its match *before* the heading line's
newline whenever a non-blank line follows immediately (with a blank line after the heading the two
agree), while `find_heading` returns the offset *past* the heading line — so the returned section
loses one leading `\n` in that case. **That last sentence is a claim about what `re` does, not about
where the regex lives, and the locator cannot support it** — a `grep -n` proves presence and says
nothing about `match.end()`. It is executed under §Measurements, at
"`re.search` end-of-match on the `titled_section` selector" — the pointer name is kept whole on one
line, because a name split across a wrap is unfindable by a literal `grep`, which is the same defect
as the `re.escape` nit repaired above and the same one that made an audit's own screen miss a
wrapped claim under §Scope. It prints `match.end()` **4** on `"## H\nBody\n"` (remainder
`'\nBody\n'`) and **5** on `"## H\n\nBody\n"` (remainder `'\nBody\n'` again — the two selectors
agree), which is what this sentence asserts. The leading newline is intentionally dropped: **every**
`titled_section`/`section_from` assertion in `h-mad/tests/test_docsections.py` is `in`, `not in`
or `pytest.raises`, and none compares exact bytes. **That is a hand reading of six functions and is
labelled one**, the way the carve-out members table's row-2 second cell says "a hand reading of that
body's eight-row table and no `grep` at all": the two counts below are *locators* and neither reads
an assertion, so the quantifier rests on reading. The reading is bounded by a census rather than by
recall — `grep -c 'assert \|pytest.raises' h-mad/tests/test_docsections.py` → **9** at `74e126f`,
nine assertion sites across the six functions, every one of which was read and every one of which
is one of the three shapes. Re-derived rather than carried at the freeze:
`git diff --stat 74e126f 700c599 -- h-mad/tests/` is empty, so the nine and the six below are
unchanged at `700c599`. The claim is quantified over *all* of them
rather than carried as a count, because a count drifts with every test added and the previous
cycle's "all five" was already false at the commit that wrote it — re-read in full and re-run at
`74e126f`, where `grep -c '^def test_' h-mad/tests/test_docsections.py` returns **6** and
`grep -c 'titled_section(\|section_from(' h-mad/tests/test_docsections.py` returns **6** call
sites. The grep is written with the trailing parenthesis on purpose: the looser
`grep -n 'titled_section\|section_from'` returns 8 lines at the same sha, because it also matches
the `from docsections import` line and the `def test_section_from_bounds_an_offset_anchored_pin`
name, and a reviewer subtracting only the import from 8 reads a contradiction that is not there.
That is what "no existing test pins the old
behaviour" above rests on. Two tests pin the **cross-directory import** — not the newline and not
the assertion set; they are the AC-1.8 collect-alone pins Success Criteria names:
`pytest h-mad/tests/test_docsections.py -q` run as a subprocess from the
repo root (collected **alone**), and an isolated `python3 -c "import docsections"` with the tests
directory on `sys.path` and an unrelated cwd. **The existing mutation spec moves with the code:**
`h-mad/tests/mutation-specs/docsections.json` carries four mutations, and **not one of their four
`find` anchors survives this change verbatim** — "two leave, two stay" is a statement about which
**`file` key** each row names, never about which anchors are untouched. Read at `a8e0372` with
`python3 -c "import json; [print(m['name'], m['file'], repr(m['find'])) for m in json.load(open('h-mad/tests/mutation-specs/docsections.json'))['mutations']]"`,
all four `file` keys are `tests/docsections.py` — re-run at `74e126f`, unchanged. Two of them
(`fence-tracking-removed`, `section-no-longer-owns-its-subsections`) anchor *inside*
`_fence_aware_end`, which is deleted, so their `file` moves to
`scripts/h_mad_doc_block_exec.py` — at its fence-state update and its heading match respectively,
the same two guards they mutate there now. The other two keep `tests/docsections.py` and are
re-anchored in place: `offset-anchored-bound-runs-to-end-of-file` mutates `section_from`'s call,
whose line becomes `text[offset:_dbe.fence_aware_end(text, offset, level)]`, and
`missing-heading-returns-empty-instead-of-failing` mutates `titled_section`'s loud failure, which
loses its `match` binding when the local `re.search` gives way to `find_heading`. Every one of the
four `find` strings is therefore re-read from the landed source and rewritten in the same task,
and the harness's exact-once
anchor rule makes a missed re-point a refusal rather than a silent survivor. **All four convert to
the harness's named-test form at the same time**: the spec carries a spec-level `command` and an
informational per-mutation `_killed_by` and nothing else the harness can run
(`python3 -c "import json; d=json.load(open('h-mad/tests/mutation-specs/docsections.json')); print(sorted(d)); print(sorted({k for m in d['mutations'] for k in m}))"`
→ `['_why', 'command', 'mutations', 'root']` and `['_killed_by', '_mechanism', 'file', 'find', 'name', 'replace']` at `74e126f`, so no `test` and no `target_command` key exists yet), which the harness does not execute — it scores "did the
suite go red", the form this repo has already seen ship a wrong-catcher as `ALL_CAUGHT`. The
conversion adds `"target_command": ["python3.11", "-m", "pytest", "-q"]` and moves each
`_killed_by` value — already a **full node ID**, `tests/test_docsections.py::<name>` for the four rows and the delegation row, the only
form the harness can run as `target_command + [test]` (`docsections-syspath-setup-removed`'s key names the new module's `test_docsections_imports_from_an_unrelated_cwd` instead) — into that mutation's `test` key
(`tests/test_docsections.py::test_a_fenced_comment_does_not_end_the_section`,
`…::test_a_section_owns_its_subsections`, `…::test_section_from_bounds_an_offset_anchored_pin`,
`…::test_a_missing_heading_fails_loudly`), so every mutation is credited only when *its* named
test goes RED. **The four connection rows added beside them are named, never numbered** — the
introduction order below is prose, so an ordinal here would restale on any reordering, and
§Deliverables already carries the total once. **`docsections-delegation-reverted` pins the wire
itself**, and is **connection-only** —
the shared `import h_mad_doc_block_exec as _dbe` line is replaced by a private instance of the
same file loaded through `importlib.util.spec_from_file_location` + `exec_module` (registered in
`sys.modules` only under its private spec name `_h_mad_doc_block_exec_private` — dataclass
processing needs `sys.modules[cls.__module__]` under `from __future__ import annotations` — and
never under the name the import system resolves), the callee untouched and no local bounder restored, so
the helper still does the real work through a second, byte-identical instance. It is killed by
`tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`, which
installs a recording fake as `sys.modules["h_mad_doc_block_exec"]`, runs
`importlib.reload(docsections)` so the module-level import re-binds `docsections._dbe` to that
fake, then calls `titled_section(...)` and `section_from(...)` and asserts the recorded call
sequence, restoring the `sys.modules` entry and reloading `docsections` again in a `finally` so
`_dbe` re-binds to the real module before any later test (pytest restores neither on its own) —
a `monkeypatch.setattr(docsections._dbe, …)` spy would not do, because it patches
whatever object `_dbe` holds, the private copy included, and so cannot see this revert. Every
other test stays green under it — the helper's own behaviour tests, the two docsections-side
hostile tests and the source guard `test_docsections_has_no_second_bounder`, whose source
predicate still holds — which is the half proving the test pins the wire and not the callee
(design audit v58: the earlier local-restore revert also failed the two hostile tests, so its
kill was confounded with behaviour). **`docsections-local-bounder-restored` keeps that
local-restore revert** — the old `_fence_aware_end` toggle and `_find_heading`
regex restored in `tests/docsections.py`, both call sites re-pointed, `_dbe` still imported —
bound to `tests/test_h_mad_doc_block_exec.py::test_docsections_has_no_second_bounder`, so the
source guard has a named RED of its own (the WIRE-PIN and the two hostile tests also go red
under it; its `test` key is the guard, whose file imports `docsections` only inside test
functions and so still collects under the mutant). The re-pointed callee mutations are the behaviour half;
this row is the connection half, and the invariant requires both. **Ordering, since the
source does not exist yet:** the module and its mutation specs are authored *together* in Phase 5 — the same task that lands `fence_aware_end` re-points `docsections.json`, re-reads the landed
lines to set each `find` to an exact-once anchor, runs `h_mad_mutation_harness.py` on both specs,
and records the named RED test in every mutation's `test` key before the task closes. A mutation
without a `test` key, or a harness run that is deferred to "later", is the silent no-op this
invariant forbids, and the 5e gate scores `ALL_CAUGHT` on the pytest summary, not on the harness's
exit code.

**`docsections-syspath-setup-removed` pins the import that carries the wire**: it deletes the `sys.path.insert` that makes `docsections.py`'s delegating import self-contained, and is killed by `tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd` — a fresh `python3 -c "import docsections"` with only the tests dir on `sys.path` and `cwd=tmp_path` — so collection can never depend on another module's `sys.path` side effect. **`docsections-heading-lookup-reverted` pins the START of the section the same way** — `titled_section`'s own `re.search(r"(?m)^(?P<marks>#+) …")` restored while `find_heading` stays intact — and is killed by the same delegation spy, which records `find_heading` as well as `fence_aware_end`.

**FR-6 is a wiring task, not a new-behaviour task, and is planned as one.** Its deliverable is a
*connection* — the migrated call sites reaching `h_mad_doc_block_exec` — and the Connection
enforcement invariant applies: a callee suite that passes proves nothing about whether the caller
still reaches the callee. The helper's own tests could stay green while
`test_h_mad_collect_report_docs.py` quietly kept its hand-rolled extraction, and every gate
downstream of 5b would report success. So FR-6 carries a `WIRE`/`WIRE-PIN` at impl-plan time, and
discrimination is required in **both** directions: reverting the connection alone (import + call
site, helper untouched) must fail a named test in the caller while the helper's own suite still
passes, and making the call site unconditional — resolving a block regardless of the tag — must
also fail a named test. Only the pair distinguishes a wire that works from one that fires always,
and neither is visible to a whole-module revert, which removes both sides at once.

**Task-level API, and how the caller changes.** The importable surface is 29 names (`BadArgs` included) in
`__all__` — the seven functions `extract`, `select`, `substitute`, `run_block`, `fence_aware_end`,
`find_heading` and `main`, plus `Block`, `RunResult` and **the whole `DocBlockError` hierarchy — the
base class and its 19 subclasses** (7 + 2 + 20 = 29; the seven-plus-two-plus-*subclasses* reading
gives 28 and is the error the design names, in `docs/02-design/features/doc-block-exec.design.md`
under `## API / Interface Changes`, in the `__all__` paragraph that follows the `find_heading`
docstring — located by text and never by line, because that citation was a line pin and went stale
by 34 lines across the single design revision v1.92 → v1.93 at b68ef48; re-find it with
`grep -n 'seven-plus-two-plus' docs/02-design/features/doc-block-exec.design.md`, exactly one hit at
the freeze `4e4a00c` (`git grep -c 'seven-plus-two-plus' 4e4a00c -- docs/02-design/features/doc-block-exec.design.md`
→ `1`; it was also `1` at `6f0ee85`, re-run in this revision because the closure above does not reach a
sibling under `docs/` and a needle unique when authored can be broken by an edit in the same commit;
the earlier label `048ef1f` was this document's HEAD~1, not its HEAD)
— and omitting the base costs callers the umbrella `except dbe.DocBlockError`), so callers
catch `dbe.BlockNotFound` through the public surface (design v1.85) — of which the functions and the two
frozen dataclasses (the design carries the full signatures; this is the contract the wire is
planned against):

| symbol | signature | returns / raises |
|---|---|---|
| `extract` | `(doc: str \| Path, heading: str) -> list[Block]` — `doc` is always a **path** (`str` accepted and converted with `Path`), read strictly as UTF-8; document *text* is never accepted, so `DocUnreadable` is deterministic for every caller | every tagged block under the heading, possibly empty; raises `DocUnreadable`, `BadInfoString`, `AmbiguousHeading` — never on count |
| `select` | `(blocks: Sequence[Block], index: int \| None = None) -> Block` | raises `BlockNotFound` (0, or past the end), `AmbiguousBlock(n)` (>1, no index), `BadIndex(n)` (index < 1) |
| `substitute` | `(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]` | a new `Block` with the substituted text (frozen dataclass, `dataclasses.replace`), plus per-key counts; raises `BadSubstArg("")` for an empty key (the API guard for in-process callers; `main` refuses the CLI's empty key itself while building the map, with the raw argument, and never reaches this one — AC-2.8, design v1.77), `MissingSubstitution`, `OverlappingSubstitution` |
| `run_block` | `(block: Block, *, preamble: str \| None = None, timeout: float = 30.0) -> RunResult` | `RunResult(rc, stdout, stderr, shell)` with `str` streams decoded UTF-8 `errors="replace"`; raises `BadTimeout` (before spawn), `LaunchFailed` (mkdtemp/chmod, spawn, reap, collect — the helper's own communicate/drain/close/wait on the child), `BlockTimeout`, `CleanupFailed` |
| `extract` body normalisation | *(rule on `extract`, not a function)* | a selected fence's body is de-indented by **up to the opener's indentation** per line, as CommonMark specifies — an opener indented 1–3 spaces yields body text with those leading spaces removed and no more; recognising the fence correctly but returning un-normalised text is the gap this row closes. Test `test_indented_fence_body_is_deindented` (exact-text fixture at 1, 2 and 3 spaces, and a body line indented *less* than the opener, **whose own fewer leading spaces are all removed** — CommonMark strips *up to* N, so a 1-space line inside a 3-space fence keeps none of its space; "left as is" is what this row said through v1.94 and it is wrong, executed under §Measurements "Fence-body de-indentation" on both renderers); mutation `body-indent-not-stripped` |
| `find_heading` | `(text: str, heading: str) -> tuple[int, int] \| None` | offset just past the matching ATX heading line and its level, found among the scanner's heading events only — never inside a fence; `None` when absent; `AmbiguousHeading(n)` on more than one. **`heading` takes one of two forms, told apart by the request itself, full form first**: a request that parses as an ATX line by the scanner's own predicate — 0–3 spaces, 1–6 `#`, then a space, a tab or end of line (`## Text`, `##\tText`, a title-less `##`; what `extract` and the CLI `--heading` pass) matches on normalized title **and** level; any other request (`Text`, what `docsections.titled_section` passes) is the bare form and matches the title at any level. A title that itself begins with an ATX prefix is reachable only in full form — the one exclusion, harmless to every live caller (design §Scanning; `test_heading_form_precedence_full_wins`, mutation `form-precedence-bare-first`) |
| `fence_aware_end` | `(text: str, start: int, level: int) -> int` | offset of the next ATX heading at `level` or shallower whose line starts at an offset `>= start` (an adjacent heading bounds the section at `start` itself), skipping fenced blocks under the full CommonMark fence rule — **backtick and tilde** runs of ≥3, closed only by the same character at ≥ the opening length **followed by nothing but spaces or tabs**, a backtick opener voided by any backtick in its info string (CommonMark; agreed by both renderers — the two `markdown-it-py` versions and the 14-case corpus are recorded once under §Measurements, "Scanner grammar corpus", and are not restated here; `backtick-in-info-accepted` / `test_backtick_in_info_string_is_not_an_opener`) (a ```` ```trailing ```` line is body text, not a closer — otherwise a quoting fence closes on paper and its quoted `hmad:exec` is read as executable; hostile fixture `test_closer_with_trailing_text_does_not_close`, mutation `closer-trailing-text-accepted`), opener and closer indented **0–3 spaces** (4+ is an indented code block, not a fence) — so a heading inside a `~~~` block never ends a section and an indented literal fence never opens one; **fence state is established over complete source lines through the line containing `start` — never a `text[:start]` slice, which can cut a line after its marker run and fake a closer — and boundaries are considered only at line starts after `start`**, so `start` may lie inside an open fence (the arbitrary offsets `docsections.section_from` passes) and a fenced `#` after it is never a boundary (`test_bounder_from_an_offset_inside_a_fence`, mutation `prefix-fence-state-skipped`); the bounder `extract` uses and `docsections` delegates to (AC-1.8). **The fence grammar has one home**: a private generator `_fence_events(text)` that both `extract` and `fence_aware_end` consume, so the two surfaces cannot diverge by construction; the fence-grammar mutations anchor in it, `test_fence_events_trace_on_every_hostile_fixture` asserts its exact event trace over every hostile fixture, and `scanner-duplicated-in-consumer` (a private fence toggle regrown inside `extract`) is killed by `test_extract_has_no_fence_state_of_its_own`, a source assertion. Bound to `test_bounder_ignores_a_heading_inside_a_tilde_fence` and `test_bounder_ignores_an_indented_literal_fence`, and to the design's `tilde-fence-not-tracked` and `indented-opener-accepted` mutations |

`h-mad/tests/test_h_mad_collect_report_docs.py` changes in the resolver and the runner only —
**stated as what does not move rather than as a count**, since the paragraph's own list runs to
five edit regions and Success Criteria adds six new test functions to the same file, so any
bare count contradicts its own enumeration. What does not move is the load-bearing claim, and it
is what makes the two text-pin callers safe: the three `_gate_bash_block()` call sites keep their
types, the **exec-codex scan** keeps its `re.findall` text scan, and `.returncode` is read nowhere
in the file, so nothing maps to `.rc`. *Exec-codex scan* is this document's name, used throughout,
for the `re.findall(r"```bash\n(.*?)```", …)` inside
`test_exec_codex_dispatch_carries_out_log_and_timeout` — **named structurally and never by line**,
which is the same policy the call sites below follow and the reason this revision stopped writing
a bare line pin for it anywhere in this document: a line pin in this file has gone stale once
already, and the enclosing `def` is what a reader can re-find. **Both halves are tree claims and carry their commands and sha**:
`grep -n '_gate_bash_block()' h-mad/tests/test_h_mad_collect_report_docs.py` → the `def` plus
exactly **3** call sites at `74e126f` (the grep prints 4 lines; the first is the `def`), one in `test_gate_block_guards_on_the_collect_token_before_gating`,
one in the nested `run_recipe` of `test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`,
and one in `test_gate_block_does_not_exit_the_operators_shell`; and
`grep -c returncode h-mad/tests/test_h_mad_collect_report_docs.py` → **0** at `74e126f`, which is
the absence claim, stated with the command that would falsify it. **That grep is cited at every
surface that states the absence, not only here** — the v1.90 fix landed it on this surface and
missed the second statement of the same claim in the migration paragraph below, which is why the
rule now reads: before declaring a member of the provenance class fixed, grep the claim's
*subject* (`returncode`, `_gate_bash_block`, `from docsections import`) across the whole body and
provenance every surface it returns. Residual on that rule, stated because it is what the subject
grep cannot reach: a claim restated in words other than its subject — "nothing maps to `.rc`" is
the live example — is invisible to it and must be caught by the shape enumeration under
§Measurements instead.

**The sibling class — a bare `path:line` pin written in prose — is declared closed by a SHAPE grep
and never by a value sweep.** A value sweep finds only the members that have *already* drifted,
which is exactly why the v1.91 sweep over the values `:270`, `:309` and `:412` could not see a pin
whose line was still correct; the axis is the *form*, not the number:

```
$ awk '/^## Version History/{exit}{print NR": "$0}' docs/01-plan/features/doc-block-exec.plan.md \
    | grep -E '\.py:[0-9]+'
```

Run against the v1.91 body at `35698f9` it returned **3** hits. Two are the recorded output of the
extractor-census command under §Measurements — outputs of a cited command, not pins, and exempt
under the rule that a recorded output is reproduced verbatim or it is not a record. The third was
prose, the `SCRIPT_DIR` citation in the cross-directory-import paragraph above, now written
structurally. **Two residuals, so this is a screen and not a verdict.** (1) A pin without the `.py`
suffix, or into a file of another extension, is invisible to it; the companion sweep is
`grep -nE '\.(md|json|sh|toml):[0-9]+'` over the same body. **It is a four-branch alternation, so
under DECISION O it is controlled branch by branch and not only as a whole** — a single-extension
fixture proves the healthy branch and says nothing about the other three, which is exactly what this
screen shipped through v1.94: its published fixture exercised `md` alone. Per-branch over the body
at the freeze, one branch at a time
(`git show 4e4a00c:<doc> | awk '/^## Version History/{exit}{print}' | grep -cE '\.<ext>:[0-9]+'`):
`md` **2**, `json` **0**, `sh` **0**, `toml` **0**, union **2**. Those three zeros are absences in
the body, not evidence about the branches, so each branch is fired against its own fixture:

```
$ printf 'see `sib.md:412` for the rule\nsee `spec.json:7` for the key\nsee `run.sh:19` for the guard\nsee `pyproject.toml:3` for the pin\nsee `sib.md` for the rule\nversion 1.2:3 is not a path\n' \
    | grep -nE '\.(md|json|sh|toml):[0-9]+'
1:see `sib.md:412` for the rule
2:see `spec.json:7` for the key
3:see `run.sh:19` for the guard
4:see `pyproject.toml:3` for the pin
```

Run with each branch alone — `grep -cE '\.md:[0-9]+'` and the same for `json`, `sh`, `toml` — the
fixture returns **1** on every one, so all four branches are shown to fire; and the two declined
lines are the negatives, a bare filename with no `:N` and a version string whose `:` is not a path
separator. So the three zeros over the body are a measured absence of that shape, not a screen that
cannot speak. The reason they are zero is **incidental, not load-bearing**: nothing has yet needed
to pin a line in a sibling document, and the moment one does the screen fires — which is why it
stays.
**Publishing the control changes the reading, and that is stated rather than left to surprise a
re-runner** — by construction, not as a measurement: the fixture line and the four output lines of
the block just above are themselves of that shape, so any body containing this control returns
**at least 5** on the union, of which `md`, `json`, `sh` and `toml` each contribute at least one —
every one of them the control's own recorded text and none of them a pin. That is why the per-branch
readings above are taken from `git show 4e4a00c:` and not from the working file: the body this
paragraph is being written into already contains the needles.
(2) It cannot tell a pin from an output, so its hits are **read**, never counted — a future
recorded output would raise the number without any pin having been written. And **every call
is module-qualified**: the file adds `import h_mad_doc_block_exec as dbe` after its existing
`sys.path.insert(0, str(SCRIPT_DIR))` and never `from h_mad_doc_block_exec import …`, because a
pre-bound alias is invisible to a spy installed on the module (`monkeypatch.setattr(dbe,
"extract", spy)` observes `dbe.extract(...)` and observes nothing through a bare `extract`). A
test asserts the consumer's source carries no `from h_mad_doc_block_exec import`, so the
discrimination cannot be lost by a later tidy-up. **The resolver splits in two so the file's
three existing callers keep their types**: a new `_gate_block() -> dbe.Block` returns
`dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))`, and the existing
`_gate_bash_block() -> str` becomes `return _gate_block().text` — so the two text-pin callers are
untouched: `test_gate_block_guards_on_the_collect_token_before_gating`'s `.index`/slicing and
`test_gate_block_does_not_exit_the_operators_shell`'s `.splitlines()`, identified at `335f535` by
`grep -n '\.index(\|\.splitlines()' h-mad/tests/test_h_mad_collect_report_docs.py` read against
the enclosing `def` lines from the previous grep — so "nothing else
in the file moves" stays true;
`run_recipe(...)`, hoisted to the module-level `_run_recipe(...)` so a pin can spy it, stops returning `subprocess.CompletedProcess[str]` and returns the helper's
`RunResult`, deriving its two script paths itself — `collector = SCRIPT_DIR / "h_mad_collect_report.py"`
and `gate = SCRIPT_DIR / "h_mad_audit_gate.py"`. **Those two are *not* locals of the nested
`run_recipe`, which is what this sentence said through v1.98 and it understates its own argument:
they are computed in the enclosing test `test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`
and `run_recipe` closes over them** — being *closure* variables rather than locals is exactly why
hoisting the nested function to module level would leave both names unbound, and therefore why the
hoisted `_run_recipe` has to derive them itself. Read at `74e126f` with
`grep -n 'collector = \|gate = \|def run_recipe\|def test_documented_gate_recipe' h-mad/tests/test_h_mad_collect_report_docs.py`,
which returns four lines in that order — the enclosing `def`, the two assignments, the nested `def`
— and `git diff --stat 74e126f 700c599 -- h-mad/tests/` is empty, so it holds at the freeze. The
hoist therefore leaves no unbound name and "nothing else in the file moves" still holds
(`SCRIPT_DIR` is already module-level) — calling `_gate_block()` and then `dbe.substitute(block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py":
shlex.quote(str(gate))})` — bound as `substituted_block, _counts = dbe.substitute(…)`, since it returns `(Block, counts)` and only the `Block` reaches the runner — and then
`dbe.run_block(substituted_block, preamble=<the COLLECT_OUT line it already builds>, timeout=60.0)` — substitution is a separate step that returns a new `Block`, so `run_block` never
substitutes and `main` can refuse a bad map before it reserves any artifact. Its four assertions
migrate field-for-field — `.stdout`/`.stderr` keep their names, and
`grep -c returncode h-mad/tests/test_h_mad_collect_report_docs.py` → **0** at `74e126f`, so
nothing maps to `.rc` — and the `subprocess` import inside the test goes. Nothing else in the file
moves; the exec-codex scan keeps `re.findall` on purpose.

**Binding, for both new mutation specs — the harness executes `target_command + [test]`, so a
bare function name is not runnable and a `test` key without `target_command` is a spec error.**
`root` is `../..` (commands run from `h-mad/`, as `docsections.json` does), `target_command` is
`["python3.11", "-m", "pytest", "-q"]`, and every `test` key is a full node ID:
`tests/test_h_mad_doc_block_exec.py::<name>` for every row of `doc_block_exec.json` (whose
`command` is `["python3.11", "-m", "pytest", "tests/test_h_mad_doc_block_exec.py", "-q"]`), and
`tests/test_h_mad_collect_report_docs.py::<name>` for every row of `doc_block_exec_wire.json`
(whose `command` is `["python3.11", "-m", "pytest", "tests/test_h_mad_collect_report_docs.py",
"-q"]`). The names in the tables below and in the design are the `<name>` half; the impl-plan
carries them fully qualified.

**FR-6 wire tests and the mutations each kills** — `h-mad/tests/mutation-specs/doc_block_exec_wire.json`:

| mutation | mechanism | killed by |
|---|---|---|
| `wire-revert-extract` | `_gate_block` resolves its block with a local `re.findall(r"```bash[^\n]*\n(.*?)```")` over `_second_surface()` instead of `dbe.extract`/`dbe.select` (and `_gate_bash_block` returns that string) (the pre-migration regex made **tag-tolerant** with `[^\n]*` — the literal pre-migration `re.findall(r"```bash\n(.*?)```")` would simply fail on the tagged fence, and the wire, not the regex, is what this mutant must discriminate; helper untouched) | `test_gate_block_resolves_through_doc_block_exec` — `monkeypatch.setattr(dbe, "extract", spy)` on the consumer's module-qualified alias, and the spy must have been called (AC-6.5) |
| `wire-revert-select` | `_gate_block` keeps `dbe.extract` but takes `blocks[0]` (or raises locally) instead of `dbe.select`, callee intact | `test_gate_block_resolves_through_doc_block_exec` — the pin also spies `dbe.select` (one call, the extracted list, `index=None`) |
| `wire-revert-run` | `_run_recipe` runs `subprocess.run(["bash", "-c", preamble + script])` inline instead of `dbe.run_block` | `test_recipe_runs_through_run_block` — the returned value is the helper's `RunResult`, and `monkeypatch.setattr(dbe, "run_block", spy)` fires (AC-6.5) |
| `wire-revert-substitute` | `_run_recipe` rewrites the installed gate path with `str.replace` instead of `dbe.substitute`, callee intact | `test_recipe_runs_through_run_block` — the pin also spies `dbe.substitute` (one call, the gate block, the one-key map) |
| `wire-unconditional` | the call site grows a fallback, `extract(...) or <legacy regex>`, so an untagged gate block is still resolved — the only way a call site can become tag-blind, since no helper API accepts untagged fences | `test_gate_block_refuses_an_untagged_recipe` — a fixture section whose gating block lacks the tag must raise `BlockNotFound` (AC-6.6) |
| `exec-scan-executes` | the exec-codex scan is made to run its block through `dbe.run_block` | `test_exec_block_scan_performs_no_execution` — the exec-codex scan asserted to call neither `run_block` nor `subprocess` (AC-6.2's exemption, pinned by a mutant that breaks it) |
| `consumer-from-import` | the consumer gains `from h_mad_doc_block_exec import extract, select, run_block, substitute` beside its alias and every helper call goes bare — one contiguous replacement at the call region, the alias line untouched (the harness applies one `str.replace` per row) | `test_consumer_calls_the_helper_module_qualified` — the source carries no `from h_mad_doc_block_exec import`, so the spies above stay observable (AC-6.5's precondition, pinned) |
| `hand-rolled-extraction-widened` | a second `re.findall(r"```bash…")` is introduced on the executing path (`_gate_bash_block` falls back to it) | `test_only_the_exec_scan_hand_rolls_extraction` — exactly one `re.findall(r"```bash` remains in the file, the exec-codex scan (AC-6.2's exemption cannot widen) |
| (bound in `docsections.json`, not here) | `docsections-heading-lookup-reverted` | `tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder` — `titled_section`'s local heading `re.search` restored with `find_heading` untouched; the spy's `find_heading` recorder sees no call |
| (bound in `docsections.json`, not here) | `docsections-syspath-setup-removed` | `tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd` — the delegating import's own `sys.path.insert` deleted; a fresh process with only the tests dir on `sys.path` must still import `docsections` (not a floor-tuple node: it lives in the new module) |
| (bound in `docsections.json`, not here) | `docsections-delegation-reverted` | `tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder` — listed here so the FR-6 table names every **authored** member of the AC-6.4 floor tuple — spec v1.56's source (1), seven node IDs. Source (2)'s members arrive in `test_h_mad_portable_timeout.py` without anyone writing a test and are not mutation-bound, so they are outside this table by construction; Success Criteria carries the rule, its current value and the probe |
| (bound in `docsections.json`, not here) | `docsections-local-bounder-restored` | `tests/test_h_mad_doc_block_exec.py::test_docsections_has_no_second_bounder` — the old local toggle and heading regex restored with `_dbe` still imported; the source guard's own named RED (not a floor-tuple node: it lives in the new module) |

Under `wire-revert-extract` and `wire-revert-run` the helper's own suite
(`test_h_mad_doc_block_exec.py`) still passes — that is the half that proves the failing test pins
the wire and not the callee, and the mutation harness records both runs.

The ordering constraint that shapes the work: the tag and the migration must land together.
Tagging the gate fence makes the **gate-block extractor**'s `re.findall` — this document's
name, used throughout, for the `re.findall(r"```bash\n(.*?)```", …)` inside the module-level
`_gate_bash_block()` helper, named structurally for the same reason as the exec-codex scan; it
requires `\n` immediately after
` ```bash ` — match **one block fewer than it matched before**, and drop the gating one.

**The Second-surface block census. This paragraph is its ONE authoritative record in this
document**; §Risks and Mitigation and the paragraph below point here and restate neither the total nor an ordinal,
because a figure stated on three surfaces drifts on two of them. It is a tree-derived count, so it
travels with a runnable command and the sha it was measured at — re-derived at `35698f9` by
importing the consumer's own `_second_surface()` and running the gate-block extractor's pattern
over it:

```
$ python3 -c 'import importlib.util,re,sys; sys.path.insert(0,"h-mad/tests"); s=importlib.util.spec_from_file_location("crd","h-mad/tests/test_h_mad_collect_report_docs.py"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); b=re.findall(r"```bash\n(.*?)```", m._second_surface(), re.S); print("blocks", len(b), "| gate", [i for i,x in enumerate(b,1) if "h_mad_audit_gate.py" in x], "| exec codex", [i for i,x in enumerate(b,1) if "exec codex" in x])'
blocks 7 | gate [4] | exec codex [2]
```

Before the tag, **7** blocks, 1 of them gating — the printed reading. After the tag it is **6**,
0 gating, and that second figure is **arithmetic on the printed output, not a second measurement**:
tagging the one gate opener makes the bare-opener pattern miss exactly that block, so the total
drops by one and the gate list empties. It was **4 → 3** at `e8eaf6f`, and `6db8e50` moved it by inserting a `##` heading between
the two string anchors `_second_surface()` bounds on — the same commit that moved the `*.md`
corpus, so this figure moves whenever `h-mad/SKILL.md` gains or loses a block in that section and
must be re-run at 5c rather than carried.
**The load-bearing claim is uniqueness under the filter, not the ordinal**, and the command prints
it directly: each bracketed list is a **singleton**. Both call sites select by a *content
predicate* — `_gate_bash_block` filters on `h_mad_audit_gate.py`, the untouched scan filters on
`exec codex` — and each predicate matches exactly one block in the section, which is the property
they depend on and the one to re-check at 5c. The ordinals inside those lists are **informational
only and carry their base**, the printed total: an inserted block would move them without touching
the uniqueness the code rests on. What goes
to zero is the
`h_mad_audit_gate.py` filter on the next line, so the loud failure is `_gate_bash_block`'s
`assert gating`, not an empty `findall` — an implementer looking for the latter will not find it.
It fails loudly rather than silently, which is the good case, but it is still a broken suite if the
two are separated across tasks.

**Only the gate-block extractor is affected, and an earlier draft of this plan claimed otherwise.**
The gate-block extractor selects the block containing `h_mad_audit_gate.py` and the exec-codex scan
selects the block containing `exec codex`; each is unique in the section under its own filter,
which is the property the two call sites actually depend on and the one to re-check at 5c, rather
than the total or the ordinal. **The numbers behind that sentence are not restated here** — the
block census above is this document's one record of them, with its command and its sha; the total
drifts and the selection does not. Only the `h_mad_audit_gate.py`
block is tagged, so the exec-codex scan keeps matching and keeps working. It is also the wrong thing to migrate — it inspects a
recipe it must never run, since running it would dispatch a real agent — so it stays a text scan
by decision rather than by omission.

## Architecture Considerations

- **The temp cwd is isolation, not a sandbox — and the plan must not claim otherwise.** A fresh
  `tempfile.mkdtemp()` cwd stops a recipe's *ordinary relative* writes from reaching the repository, and
  that is the whole of the guarantee this feature tests. A block containing an absolute path, or
  an explicit `cd`, escapes it, and no cwd choice could prevent that. Claiming "side effects
  cannot reach the repository" would assert a containment property nothing here enforces; the
  tests assert the narrower, true one.
- **The tag is the security boundary.** This helper executes shell text taken from a document, so
  the property that keeps it safe is that selection is explicit and cannot be widened. That
  constrains the API shape as much as any requirement: no parameter may accept a directory, a
  glob, or an all-blocks flag, because such a parameter is how an opt-in mechanism becomes the
  blanket sweep it was built to prevent.
- **The block's exit code and the tool's verdict are different questions**, and conflating them
  would make a recipe that correctly returns non-zero indistinguishable from a harness failure.
  This mirrors the existing split between a dispatch's rc and its status token.
- **Refusal is the default response to anything unmeasured.** Absent block, ambiguous address,
  inapplicable substitution, unknown info-string key, timeout — each returns nothing rather than a
  plausible-looking zero. The failure this repository keeps re-encountering is a measurement that
  did not happen reading as a measurement that came back clean.
- **Shell mode belongs on the fence, not in the caller.** Whether a recipe is meant to be pasted
  into an interactive shell is a property of the recipe; putting it in the test would let two
  callers disagree about one block.
- **Self-containment**: stdlib only, no import of another skill's internals, no path outside this
  skill's own directory. The helper must work from a bare clone.

## Deliverables

| Deliverable | Type | Satisfies |
|---|---|---|
| `h-mad/scripts/h_mad_doc_block_exec.py` | module + CLI | FR-1, FR-2, FR-3, FR-4, FR-5 |
| `hmad:exec` fence info-string tag convention | convention | FR-1 |
| `h-mad/tests/test_h_mad_doc_block_exec.py` | tests | FR-1..FR-5 |
| `h-mad/tests/mutation-specs/doc_block_exec.json` | mutation spec | FR-1..FR-5 — 81 mutations with a full-node-ID `test` binding each — **80 of the helper's source and 1 of `h-mad/SKILL.md`**. The split is not carried: it is re-derived from the matrix's own mechanism column, by counting the rows that name `SKILL.md` as **the mutation target**, so a row added later re-derives instead of drifting. The derivation is a command, not an adverb: ``git grep -c 'the mutation targets `SKILL.md`' 4e4a00c -- docs/02-design/features/doc-block-exec.design.md`` → **1** at the freeze `4e4a00c`, and **1** at `6f0ee85` (unit: matching lines, one row per line), and that one row is `registry-row-removed`, "one remedy row deleted from the `SKILL.md` Helper-scripts entry (the mutation targets `SKILL.md`)". The figure is derived from a **sibling under `docs/`**, so the §Measurements closure does not reach it and it is re-derived at every freeze; through v1.92 it read "Today exactly one does", a count with neither command nor sha. The AC-4.5 pin still has two directions and therefore two rows, but only one of them mutates the registry: the other, `detail-line-undocumented`, mutates the **helper** ("the helper renames one emitted detail line (`missing_key:` → `absent_key:`)"), so its `file` key is the helper's source, not `SKILL.md` — an implementer who writes `"file": "h-mad/SKILL.md"` there gets an anchor that cannot match, which the harness refuses. Each row's `test` binding is enumerated row by row — mutation name, mechanism, `tests/test_h_mad_doc_block_exec.py::<name>` — in the design's §"Test Plan", under the bolded lead-in "Helper mutation spec — `h-mad/tests/mutation-specs/doc_block_exec.json`, entry by entry" (a lead-in paragraph inside the `## Test Plan` heading, not a heading of its own), which is the authoritative matrix this row points at |
| Wire mutations for the migrated call site (both directions), in `h-mad/tests/mutation-specs/doc_block_exec_wire.json` | mutation spec | FR-6 |
| Helper-scripts registry entry in `h-mad/SKILL.md` | docs | FR-4 |
| Tag on the Second-surface gate fence in `h-mad/SKILL.md` | docs | FR-6 |
| Migrated `h-mad/tests/test_h_mad_collect_report_docs.py` (executing path only) | tests | FR-6 |
| `h-mad/tests/docsections.py` — drop its duplicate bounder, import the authoritative one | tests | FR-1 (AC-1.8) |
| `h-mad/tests/mutation-specs/docsections.json` — re-point the two bounder mutations at the authoritative module, convert every row to the named-test form (`target_command` + a full-node-ID `test` key), and add the four connection rows `docsections-delegation-reverted`, `docsections-syspath-setup-removed`, `docsections-heading-lookup-reverted`, `docsections-local-bounder-restored` — 8 rows | mutation spec | FR-1 (AC-1.8) |
| `h-mad/tests/test_docsections.py` — gains the delegation spy test that kills `docsections-delegation-reverted` | tests | FR-1 (AC-1.8), AC-6.4 |

## Risks and Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Tagging the gate fence breaks the bare-opener extractor inside `_gate_bash_block()` | High — certain if separated | Land the tag and the migration in one task; the existing assertion on a non-empty block list makes the breakage loud if they are not. **The exec-codex scan is NOT affected** — it selects a different, untagged block (`exec codex`), unique in the section under its own filter, so it keeps matching and deliberately stays a non-executing text scan. The evidence is the block census under §Implementation Strategy, which carries the runnable `_second_surface()` probe and the sha it was re-derived at; this cell points at it and restates neither the total nor the ordinal, so the two surfaces cannot disagree |
| A later convenience flag turns opt-in into a sweep | High | No API accepts a directory or glob; the exclusion is written into the spec's out-of-scope list and pinned by a test asserting the CLI rejects such input |
| A substitution anchor drifts and the replace silently no-ops | High | An absent key is a refusal naming the key; this is the single most load-bearing guard and gets its own mutation |
| A recipe's side effects reach the working tree | Medium | Every run in a fresh `tempfile.mkdtemp()` cwd **passed to the launch as `Popen(…, cwd=cwd, …)`** — creating the directory does nothing to the child's cwd by itself, so the keyword is the guarantee (mutation `cwd-not-passed`, test `test_block_runs_in_the_temp_cwd`) — removed afterwards; pinned by asserting the tree is byte-identical across a run that writes files |
| "Run under `mktemp -d`" is read as the shell utility, acquiring an external dependency | Medium | The phrase came verbatim from the candidate row and is a stdlib call here: AC-3.13 asserts `tempfile.mkdtemp()`, mode `0o700`, and no `mktemp` invocation in the source |
| A timeout leaves orphan processes, as four `exec-pane` dispatches did in this repo | Medium | The full sequence, because `killpg(proc.pid, …)` only reaches a group the launch actually created: `Popen(…, start_new_session=True)` makes the child a group leader so its pgid **is** its pid → `communicate(timeout=…)` → on `TimeoutExpired`, **`proc.poll()` first** (a leader that already exited is a zombie, and on macOS `killpg` on a zombie-only group raises `PermissionError` — measured under §Measurements — whereas after `poll()` it raises `ProcessLookupError`, the one exception read as "already reaped") → `killpg(proc.pid, SIGKILL)` (never via `getpgid`, which races once the direct child has exited) → a second bounded `communicate` to drain → `rmtree(cwd)` in `finally`. Pinned by asserting no **in-group** descendant survives; a descendant that calls `os.setsid()` escapes any group kill — measured — so AC-5.2 is scoped to the group rather than claiming containment this design cannot deliver. Two races on that path are handled, not hoped away (AC-5.5): `killpg` on a group that already emptied raises `ProcessLookupError` (measured) and is read as "already reaped"; a drain `communicate` that an escapee keeps open is itself bounded, after which the pipes are closed and the leader reaped |
| Cleanup fails and the run still reports success | Medium | `rmtree` without `ignore_errors`, a read-back that the cwd is absent, and `CLEANUP_FAILED path="<p>"` exit 2 on failure — with an `os_error: "<text>"` detail line whenever an `OSError` was recorded, so the diagnostic is never lost (AC-3.14); the fixture is an unreadable subdirectory, on which `rmtree` raises and `ignore_errors=True` retains the tree — command and output under Measurements. The permission fixture is skipped under root (`euid == 0`, where mode bits do not bind) and a deterministic fault injection runs everywhere: `shutil.rmtree` monkeypatched in the helper's namespace to raise `OSError`, and separately to silently do nothing, so both guards — the recorded error and the read-back — each have a mutation only they kill |
| The strict default hides the very defect class that motivated the feature | Medium | `shell=plain` is declarable per fence, and the shell-killing `exit` case is pinned as an explicit acceptance criterion |
| An unknown info-string key silently falls back to a default mode | Medium | Unknown keys refuse rather than default |
| The carried fence-census figure is stale | Low | Re-measured at `a8e0372` — **73 across 10 files**, control **88** — with the command and its output cited below under Measurements. It *was* 68/83 at `a469493` and `1861157`, so this row's own risk has already fired once: the mitigation is the sha beside the number, not the re-measurement, because a re-measurement without a commit is unfalsifiable |

## Measurements

Both figures below shape this plan's scope and success criteria, so the command and its observed
output are recorded here rather than only in the author's terminal — a cited output is checkable
by a reviewer, "I verified this" is not. Re-run them at implementation time; citing them makes
staleness detectable, it does not prevent it.

**Provenance rule, binding on this whole document and not only on this section.** Every count,
ordinal or absence claim about the working tree carries **both** its generating command **and**
the sha it was measured at, on the same surface as the number. A command with no sha is
unfalsifiable, because the tree moved; a sha with no command is uncheckable, because two readers
measuring "the same" thing run different commands; and `measured`, "this session" and
"today" are neither a command nor a sha. Those are **three markers across four words** — one is a
two-word phrase, which is not pedantry: it is the branch whose boundaries took three revisions to
get right, and calling it a word is what made a two-word branch read as a one-word one.
**The rule sentence and the screen's program are maintained together by convention, and nothing
checks that they agree.** Through v1.93 this sentence claimed they "are written from one list so
they cannot drift apart"; they are two independent pieces of prose, and v1.93 itself demonstrated
the drift — the marker *set* matched while the *treatment* did not, three markers named as bounded
and two of them actually bounded. The residual is stated rather than closed: the only mechanical
bind available is to derive this sentence's marker list from the program the way screen two derives
its rule from the spec's fenced block, which would make the prose an awk alternation and cost more
readability than the drift it prevents. What stands in for the missing checker is the **per-branch**
control below — each branch is run against its own fixture, so a dead or unbounded branch can no
longer be covered by a healthy sibling in the alternation.

**"Freeze" is a defined word here, and getting it wrong is how a reader lands on the wrong tree.**
The **freeze** of a round is the commit the auditors *measured*; the commit that *records* their
reports is a later, different commit. Through v1.94 this document called `cf3a862` "the audited
commit", and `cf3a862` is `docs(doc-block-exec): round eight audit -- six reports at freeze
8909ec4` — the recording commit, not the measured one. Nothing moved, because
`git diff --stat 8909ec4 cf3a862 -- <this document>` is **empty** and this document's body is
byte-identical at the two, so every figure stamped `cf3a862` stands; what was wrong was the label,
and a reader reproducing "the audited commit" checked out the wrong end of the pair. **The freeze
this document's figures are stamped at is `4e4a00c`**, which is
`round nine audit -- six reports at freeze 7982c18` and is
therefore a recording commit too — it is named as **the freeze `4e4a00c`**, never as "the audited
commit". **v1.96 did not repoint that word**, because doing so means re-typing the sixty
occurrences of `4e4a00c` the body carried at `68a70d6` — counted with its command in the closure
paragraph below, which also shows in two `git diff` commands that every one of them still holds.
The commit v1.96 was audited against is `68a70d6`, and every reading v1.96 takes on the current
body names `68a70d6` in full rather than borrowing this word.
**The label is swept by phrase, not by the surface an audit named**: every other body
surface that carried it — the fence-census re-run, the corpus-argument caveat, the tracked/glob
pair, the screen-two re-derivation rule, the both-screens rule and the codex ledger, six in all —
now says *the freeze*, and the sweep that checks it is
`awk '/^## Version History/{exit}{print NR": "$0}' <doc> | grep -n audited` — on the **word**, not
on the phrase, because the phrase hard-wraps and a phrase grep is line-scoped and would miss the
wrapped halves, which is the same line-scoping residual this document states for its two screens.
Its hits are **read, never counted** — but through v1.95 they were neither, because the sweep was
published with a triage nobody had run it against. **v1.96 runs it.** Over the body at `68a70d6`,
which is the body v1.95 shipped,
`git show 68a70d6:<doc> | awk '/^## Version History/{exit}{print NR": "$0}' | grep -c audited`
returns **8**, and the three admissible categories account for all eight when the hit list is read:
**(1) this paragraph's own text — six**, the unit being *body lines printed* as everywhere else in
this section: four lines carrying the wrong label as a quotation while it is retired, one carrying
this paragraph's quotation of the slot census's correct usage, and one carrying the sweep's own
needle `grep -n audited` inside the command above; **(2) `audited` as a verb naming the commit a
round measured — one** at that body, the slot census's "the commit **v1.93** was audited at", which
is correct usage and is the form any later "the commit vN was audited at/against" also takes;
**(3) `audited` as an ordinary verb about the
review process rather than as a label beside a sha — one**, §Next Steps' "This plan and the paired
design are audited together". Category (3) is new in v1.96 and is the reason the sweep had to be
executed: a reader running it hit a line the published triage could classify in **neither**
direction, and an unclassifiable hit in a triage that claims to cover its output is worse than an
uncounted one. The label *the audited commit* standing beside a sha outside these three is a
surface the sweep missed. **The word and not the phrase, executed rather than argued**: over that
same body the word form returns **8** where
`git show 68a70d6:<doc> | awk '/^## Version History/{exit}{print}' | grep -c 'the audited commit'`
returns **1**, so the seven the phrase form cannot see are exactly what the line-scoping residual
predicts. Both numbers are of a **landed** body and neither is claimed at "now": this paragraph
writes `audited` several more times, so the count moves when v1.96 lands and is re-taken at the
next freeze rather than carried.

**One closure, stated once instead of re-stamping every pin in this document.** Every commit in
`74e126f..68a70d6` touches only paths under `docs/`:
`git diff --name-only 74e126f 68a70d6 -- h-mad handoff` prints nothing, and
`git diff --name-only 74e126f 68a70d6 | sed 's|/.*||' | sort -u` prints `docs` alone. **The
covered set is stated as an interval and never as a list of shas**, which is the class fix: the
enumeration "stamped `74e126f`, `35698f9` **or** `6f0ee85`" that stood here through v1.94 went short
by one member on the round that added `cf3a862`, and would go short again on every round after —
so the rule is now *any* stamp in `74e126f..68a70d6` inclusive. Every
figure below that was measured over `h-mad/` or `handoff/` and carries such a stamp is provably
identical at `68a70d6`, and those stamps are deliberately left as written
rather than re-typed at every surface that carries one. A mass re-stamp is itself a defect surface,
and this closure is checkable in two commands where that many edits are not. **The interval is
re-checked, not extended by assumption**: each revision re-runs the two commands with the *new*
right-hand side, and the closure holds only as far as that run reaches. **v1.96 re-ran them and
extended the interval by two commits rather than re-typing sixty stamps**: the body carries **60**
occurrences of `4e4a00c` (`git show 68a70d6:<doc> | awk '/^## Version History/{exit}{print}' |
grep -c '4e4a00c'`), and `git diff --name-only 4e4a00c 68a70d6 -- h-mad handoff` prints nothing
while `git diff --name-only 4e4a00c 68a70d6 | sed 's|/.*||' | sort -u` prints `docs` alone, so
every one of those sixty that reads the tree is provably still true where it stands.
**v1.101 re-ran both commands again with `b3be433` as the right-hand side and the interval holds
there too**: `git diff --name-only 74e126f b3be433 -- h-mad handoff` prints nothing and
`git diff --name-only 74e126f b3be433 | sed 's|/.*||' | sort -u` prints `docs` alone, as do the same
two with `4e4a00c` on the left.
**v1.102 re-ran all four with `dfae038` as the right-hand side and the interval held there too**:
`git diff --name-only 74e126f dfae038 -- h-mad handoff` and the same with `4e4a00c` on the left both
print nothing, and both piped `sed 's|/.*||' | sort -u` forms print `docs` alone. **This closure is
re-run at each revision's measurement commit and not left at an earlier one, for a reason that is
the rule and not a courtesy: its corpus is `h-mad/` and `handoff/`, wider than the four feature
documents, and the four being byte-identical across an interval is a fact about `docs/` that says
nothing whatever about `h-mad/`.**
**AND AT `af19d53`, v1.103's measurement commit, THE CLOSURE FAILS — the blanket is retired here,
not re-asserted.** `git diff --name-only 74e126f af19d53 -- h-mad handoff` prints
`h-mad/scripts/h_mad_assemble_audit.py` and `h-mad/tests/test_h_mad_assemble_audit.py`, and the same
command with `4e4a00c` on the left prints the same two; the control at `3f70eb3` still prints
nothing, so the break is `af19d53` itself and nothing earlier. **What replaces the blanket is the
enumerated diff and a corpus reading, not a weaker assertion**: the interval changes exactly those
two paths, both `h_mad_assemble_audit`, and the tracked markdown corpus every `4e4a00c`-stamped
scanning reading is taken over is **unmoved at 30** —
`git ls-tree -r --name-only <sha> -- h-mad handoff | grep '\.md$' | grep -v '/archive/' | wc -l`
returns `30` at `74e126f`, `4e4a00c`, `3f70eb3` **and** `af19d53`. **The one body site that reads
either changed file is the suite floor in §Convention Prerequisites, and `af19d53` moved it again
by construction**: `git show <sha>:h-mad/tests/test_h_mad_assemble_audit.py | grep -c '^def test_'`
returns `7` at `74e126f`, `4e4a00c` and `3f70eb3`, and `12` at `af19d53` — five new tests, the
**second** time that one file has moved the floor, which is why that bullet's re-measure-at-branch
residual is a live obligation and not a formality.
**The class**: an emptiness closure over a directory is a figure with a right-hand sha, and it
expires at the next commit touching that directory — **including a commit that touches nothing this
feature owns**, which is the case that was never going to be caught by watching the four documents.
When it expires it is replaced by the enumerated diff and the corpus reading, never by re-running
it against an earlier right-hand side until it comes back empty. Residual: the enumeration says
which files moved and cannot say whether a reading *depends* on one; that is settled per site, and
here it is settled for the one site that names either file.
The body carries **70** occurrences of `4e4a00c` at `b3be433`
by the `awk`-prefixed form above — **unmoved at `1cbddb7`, `700c599` and `8c6539a`, where it was
also 70**, up from the **60** v1.97 read at `7d8e797` because v1.97's own
edit added ten — **which is the paragraph's own point restated as a measurement rather than as an
argument**: the corpus of this figure is this document, so the figure moves with every revision and
is re-taken at each freeze rather than carried. **That it did not move across three revisions is
not evidence it need not be re-taken**, and the two figures beside it both did move across the same
span — the `the freeze` triple to `37`/`21`/`16`, **in this section**, and the codex-leg ledger's
teammate half to `84`, **in §Next Steps**. **Each is named with the section that holds it, because
v1.101 wrote "beside it in this section" for both and the ledger is not in this section**: the
§Measurements closure explicitly excludes the ledger's corpus — the clause reading "the interval
closure covers `h-mad/` and `handoff/`, and this document is neither", and the sentence stating that
the closure "does **not** reach figures derived from **this** document or from its three siblings
under `docs/`" — so the ledger is not merely elsewhere in the file, it is definitionally outside the
closure this sentence belongs to. **Those two clauses are addressed by quotation and not by
direction, which is this paragraph's own class rule applied to itself**: the first draft of this
repair said "two paragraphs above", and both clauses are in fact *below* the sentence pointing at
them — the retired phrasing is quoted here so the sweep that retires it has something to find.
**The class: a placement claim is a claim about a heading, and this document locates by heading and
never by proximity** — "beside it", "above", "below" and "in this section" are all readings of a
layout that the next revision moves, and the check is
`grep -nE '^#{2,4} ' <doc>` against the site's own position. Residual, and it is why this is a rule
rather than a screen: nothing detects a *wrong* section name, only a missing one; a reader verifies
by running that `grep` and locating the figure between two headings. **The phrase
*the freeze* in this document means `4e4a00c` throughout and is deliberately not repointed** —
every reading v1.96 takes on the current body names `68a70d6` explicitly and never says "the
freeze", because a phrase with two referents in one body is the drift this section exists to
refuse. **Residual, and it is carried here rather than closed here:** the three self-counts stamped
`4e4a00c` in this paragraph are readings of the v1.94 body and are *not* claimed at any later
commit, `b3be433` included; the interval closure covers `h-mad/` and `handoff/`, and this document
is neither. **The register below is where that residual is discharged, and this sentence is its
pointer rather than a second home for it** — v1.97 entered the three in the register and left this
sentence unchanged, so the register's account of it read in the past tense while both surfaces were
live. This paragraph owns the three integers and their commands; the register owns their
*unverified* status.
**No count of the surfaces this covers is offered**, and the offer was withdrawn in v1.93 rather
than corrected. The numbers below are **body-scoped**, and the command printed is the one that
produces them — a bare `grep -c '74e126f'` over the whole file returns **30** at `4e4a00c`, because
§Version History carries the sha too, and publishing a body figure beside a whole-file command is
the unrunnable-cell defect this document closed in the carve-out table one revision earlier:
`awk '/^## Version History/{exit}{print}' <doc> | grep -c '74e126f'` returns **27** at `6f0ee85`,
**26** at `cf3a862` and **26** at `4e4a00c`, but `grep` is
line-scoped and this document hard-wraps, so a sha and the `h-mad`/`handoff` path it belongs to
routinely sit on different lines — the count cannot be narrowed to the closure's stated subject by
co-occurrence (the narrowed form
`awk '/^## Version History/{exit}{print}' <doc> | grep '74e126f' | grep -cE 'h-mad|handoff'`
returns **10** at `6f0ee85`, **11** at `cf3a862` and **11** at `4e4a00c`, and no integer in this
sentence is the number of covered figures). It also counts this
paragraph's own prose and the very lines the next sentence puts *outside* the closure. The
argument does not need a number; the two `git diff` commands are the whole evidence.
**Every reading here is of a body that existed before this revision's edit, and that is the only
reason they can be published at all**: this paragraph is inside the corpus it counts, so a reading
taken after the edit would be a number the act of writing it had already moved. The rule the shas
encode: a figure whose corpus is this document is stated at a **landed** commit, never at "now",
and it is re-taken at each freeze rather than carried. The closure
does **not** reach figures derived from **this** document or from its three siblings under
`docs/`: those files did change, so every such figure carries a **standing** re-derivation
obligation. **That obligation names a sha and never the word *the freeze*, and v1.97 exists partly
because v1.96 wrote it the other way**: v1.96 pinned *the freeze* to `4e4a00c` while separately
naming `68a70d6` as the commit it was measured at, which detached every "re-derived at the freeze"
sentence from the round's own measurement commit and let one `docs/`-scoped figure — the codex-leg
ledger in §Next Steps — go stale inside the sentence that forbids carrying it: its teammate half
read `81` at `4e4a00c` and had already moved to `82` at `68a70d6`, v1.96's own freeze, and to `83`
at `7d8e797`. **The same half went stale the same way again in v1.99 and v1.100, which is why this
is a rule and not a repair**: it moved to `84` at `8c6539a`, the commit v1.100 was authored
against, and neither entry re-measured it — the recurrence is written up at the ledger itself under
§Next Steps.
**The rule: a `docs/`-scoped figure is re-derived at the commit the revision is measured at, that
commit is named once per revision, and every such re-derivation carries the sha inside the command
rather than the phrase beside it. v1.103 is measured at `af19d53`, and at nothing else.**
**One revision, one measurement commit — the pair is abolished rather than reconciled.** v1.102
answered *measured at* twice: `dfae038` in this paragraph and `00b961f` at the codex-leg ledger's
own site in §Next Steps, which is the site telling a re-runner the without-exception rule was
obeyed. **Both gating legs filed it, and the repair is the rule, not the reconciliation**: a second
sha is admissible in this document only as **the stamp on an inherited or historical reading**, and
never as a second answer to *measured at*. So every reading v1.103 takes is run at `af19d53` with
the sha inside the command, and every reading it inherits keeps the blob it was stamped at —
`b3be433` for v1.101's, `00b961f` and `dfae038` for v1.102's — and does not move.
Residual: nothing detects a *second* revision's sha used correctly as an inherited stamp being
misread as a measurement commit; only the count of answers to *measured at* is checkable, and it
is one.
**The four documents are byte-identical across `3f70eb3..af19d53`**
(`git diff --stat 3f70eb3 af19d53 -- <plan> <spec> <impl-plan> <design>` is empty), **and this
document is byte-identical from `59cc2ad`, its own v1.102 landing commit, through `af19d53`**
(`git diff --stat 59cc2ad <sha> -- <doc>` is empty at `7b182b0`, `3f70eb3`, `4c1c3a5`, `b442a80`,
`7b9d174` and `af19d53` alike). **That is a fact about blobs and is deliberately not used as a
licence to skip a re-run**: what it licenses is reading an inherited stamp, and nothing more.
**v1.102's version of this paragraph carried a claim this document never measured, and it is
corrected here rather than quietly dropped.** It said the two commits between `00b961f` and
`dfae038` touched `docs/handoffs/` *alone*. They did not:
`git show --name-only --format='' dfae038` returns
`docs/handoffs/2026-09-05-main__doc-block-exec-rounds-twelve-to-fourteen.md`, `docs/learnings.md`
**and** `docs/skill-candidates.md`, while `git show --name-only --format='' df04e8e` returns its
handoff file alone. **The claim entered this document from the round-fifteen orchestrator decision
sheet, which asserted it without measuring it**, and the provenance is named so the correction is
attributable rather than anonymous. **The conclusion it was used for is unaffected and is not
over-repaired**: `00b961f` is still the only commit in that interval touching any of the four
feature documents, checked per commit, so v1.102's byte-identity argument and the register's
interval argument both stand. **The word was wrong; the argument was not.**
**The class**: `sed 's|/[^/]*$||'` collapses a path list to directories and cannot distinguish a
top-level file directly under `docs/` from one in a subdirectory, so a claim about *which files* a commit touches is read
off `--name-only` **unpiped**, and a claim about directories says directories. v1.102's own printed
output was already the evidence against its sentence — the `docs` element it printed *was*
`docs/learnings.md` and `docs/skill-candidates.md`. Residual: the class covers the collapse and not
the corpus, so a `--name-only` restricted by a pathspec still answers only for that pathspec.
**v1.103 re-derives no `docs/`-scoped figure that v1.101 stamped at `b3be433` or that v1.102
stamped at `00b961f` or `dfae038`, and does not re-stamp them either**: those commits are immutable
and those readings are correct there, so a mass re-stamp would replace a set of true sentences with
a set of newly-taken ones and add a defect surface for no argument. **The readings v1.103 *does*
take are listed, never counted** — a cardinal over a prose list is the population-short-by-N claim
this section writes a rule against, and this list is prose. They fall in two kinds, and the kinds
are what matters: readings that **replace** a value that was wrong, expired or unrunnable — the
codex-leg ledger and the standing codex debt it rests on, the `h-mad/`/`handoff/` interval closure,
and the `handoffs/`-alone path claim above — and readings that are **new**, settling a state no
earlier revision measured: the `ten of the eleven` sweep in both grammars, the `df04e8e`/`dfae038`
per-commit path lists, and the status at `af19d53` of the two spec commands v1.101 reported as
owed. Each is published at its own site with its own command. *The freeze* keeps its meaning —
`4e4a00c`, v1.95's freeze and the sha the phrase stayed pinned to through v1.96 even though v1.96's
own round was frozen at `68a70d6` — and it stays a **past-tense label on readings already taken**. Body-scoped at `b3be433` the phrase sits on **37** lines, **21** of them carrying
`4e4a00c` on the same line
(`git show b3be433:<doc> | awk '/^## Version History/{exit}{print}' | grep 'the freeze' | grep -c '4e4a00c'`);
**it read `32`/`21` at `1cbddb7` and at `700c599`, and v1.99's edit moved the total to `37` at
`8c6539a` with the `4e4a00c` half unchanged — a figure this document publishes twice went stale
between the revision that took it and the revision that shipped beside it**, the same shape as the
ledger and the reason the standing obligation names the measurement commit rather than a phrase.
Those twenty-one are readings with their sha beside them and are deliberately not re-typed, since a
mass re-stamp is a larger defect surface than the standing sentences this rule repoints. Residual,
stated because no screen closes it: a *future* standing obligation written with the bare phrase is
caught only by reading, and the shape filter that narrows the reading — the same command with
`grep -vc` — returns the other **16** at `b3be433` and is a *shape* filter and never a verdict,
because this document hard-wraps and most of those sixteen carry their sha on the adjacent line.
**The triple is a reading of a landed body and it has moved on three of the last four landings** —
`32`/`20`/`12` at `7d8e797`, `32`/`21`/`11` at `1cbddb7` and at `700c599`, `37`/`21`/`16` at
`8c6539a` and again at `b3be433` — so it is re-taken at each revision's own measurement commit and
never carried, which is this rule applied to itself, and v1.99 and v1.100 are the two revisions
that did not apply it.

**The `docs/`-scoped figures this revision re-derived, stated as one closure rather than as one
re-stamp per member.** The members are **listed, never counted**, and that distinction is the point:
v1.97 led this paragraph with a cardinal over the list in the sentence immediately before the
sentence forbidding one, which is the defect and not merely an inconsistency: this
population is prose, so a cardinal over it would be exactly the population-short-by-N claim the
paragraph above writes a rule against. Every member below is stamped `4e4a00c` and was re-run at
`b3be433`, **v1.101's measurement commit — named by revision number, because through v1.102 this
clause read "the commit *this revision* is measured at", which was true when v1.101 wrote it and
two revisions stale by `af19d53`.** It is the same class MUST 4 of the round-fifteen gating audit
found at the codex-leg ledger: **a commit is identified by the revision it belongs to, never by a
deixis, and exactly one commit per revision answers "measured at".** Each member below
**returned exactly its published value**, so its `4e4a00c` stamp is left as written —
the design's `seven-plus-two-plus` locator (**1**), the design mutation-target derivation (**1**),
the **49** AC anchors with the duplicate check silent (**0** lines from the `uniq -c | awk '$1>1'`
form), AC-6.1's two spec greps (**1** and **0**), the spec's `len(tuple)` (**2**), the spec
`^  $ awk ` locator (**1**, with the design and the impl-plan **0** each), the "Residual on the
enumeration itself" needle (**1**), the spec opener census (**21** openers over **11** distinct
tokens, distribution unchanged), the impl-plan's `found = _dbe.find_heading(text, heading)` (**4**),
and the spec-immobility premise the opener census rests on
(`git diff --stat cf3a862 b3be433 -- <spec>` empty, as `cf3a862 1cbddb7`, `cf3a862 7d8e797` and
`cf3a862 4e4a00c` were — the spec is still at v1.60 at `b3be433`, read from its own Version
History). **That last premise is RETIRED at `00b961f` and is not carried past it**: `00b961f` ships
spec v1.61, and `git diff --stat cf3a862 00b961f -- <spec>` reports **41 insertions, 15 deletions**,
so there is no longer an immobility argument to rest the opener census on. **The census *value*
survives the loss of its argument and is re-derived rather than inferred** —
`git show 00b961f:<spec> | grep -oE '^  \$ [a-zA-Z0-9._-]+' | sort | uniq -c` still gives **21**
openers over **11** distinct tokens with the distribution unchanged — which is the point: an
immobility premise licenses *not* re-deriving, so when it dies the reading is re-taken and never
argued. **The class: a premise that a sibling has not moved is itself a figure with a right-hand sha,
and it expires at the next commit that touches that sibling** — including this document's own
landing commit, which is where it expired both times. **The screen used to
find them cannot establish that the list is complete, and is published as a starting point rather
than as a verdict**: `git show <sha>:<doc> | awk '/^## Version History/{exit}{print}' | grep '4e4a00c' | grep -Ei 'spec|design|impl-plan'`
is line-scoped while this document hard-wraps, so a member whose sha and whose sibling name land on
different lines is invisible to it — AC-6.1's two spec greps are exactly that case and were found by
reading, not by the screen. **The whole closure also drifts by construction and must be re-run every
round**: the design, the spec and the impl-plan are revised in the same rounds this document is, so
a walk that holds at `b3be433` says nothing about the next freeze — it is re-taken there, not
extended by assumption, exactly as the `h-mad`/`handoff` interval above is.
Nor does the interval closure reach a figure stamped at a commit *older* than `74e126f`; those are
re-run where this revision touches them and left at their own sha otherwise.
**The preamble's completeness promise is now discharged member by member rather than asserted**,
because through v1.94 it promised "every such figure is re-derived" while four were not. The four
that were outside it are re-derived at `4e4a00c` on their own surfaces in this revision — the
design's `seven-plus-two-plus` locator (**1**), the mutation-target derivation
``git grep -c 'the mutation targets `SKILL.md`' 4e4a00c -- <design>`` (**1**), the **49** AC anchors
with their duplicate check silent, and the codex-leg ledger's **72** — and the four premises behind
§Success Criteria's "re-run at" sentence are re-run there. Anything a later reader finds still
outside the closure and outside the register below is a defect in the register, not a licensed gap.

**What this revision did NOT re-run, named rather than passed over in silence.** A figure no round
challenged is not a verified figure, and an auditor's silence about it is not evidence either way;
the register is kept here so the next reader can tell "reproduced" from "nobody
looked". **Its population is derived by a walk over two named sources and never by recall: every row
of the carve-out table below, and every figure the two closure paragraphs above hold by *argument*
rather than by *execution*** — a closure establishes that a reading still holds, never that it was
taken again, so a closed figure is an un-re-run figure and belongs here. **v1.97 stated the carve-out
table as the sole driver and that was already false in the same revision**: the member it added, the
`74e126f` self-counts, is not a carve-out row — `74e126f` appears in **0** of the eight rows, the rows selected by the one thing every one of them
carries and no other line in the body does
(``git show 1cbddb7:<doc> | awk '/^## Version History/{exit}{print}' | grep '^| .*`git ls-files ' ``
returns the **8** rows, and piping those to `grep -c '74e126f'` returns **0**) — and neither are the `doc-auditor.md` fence-toggle readings,
the Setext differential or the six screen-two legs. Residual, stated because nothing closes it: the
walk is the author's and no screen bounds it, so a figure that neither source names is invisible to
both, which is why the register is not offered as complete. The single-source statement was
introduced against a real defect and the defect stands — v1.94's register
said "the three OS probes" while that table listed **five** OS- or runtime-determined probes it had
not re-run, which is the same population-short-by-two shape the table itself was repaired for one
revision earlier. **That shape was present in the body at v1.93, v1.94 and v1.95 — three
consecutive revisions — so it is written as a rule over its axis rather than repaired a third time
on the named member.**

**The axis is *which revision shipped a short cardinal versus which merely carried or repaired it*,
and the rule over it is: a member is addressed by the EARLIEST landed commit at which BOTH of two
greps hold — the surface that states the cardinal carries it, and the surface that cardinal counts
walks to a larger number — with the PREDECESSOR revision returning the needle absent. Three greps
per member, never recall and never the revision number alone.** Each grep does a job the others
cannot. The first locates the claim. The second is what makes the cardinal *short*, and without it
there is no defect to date at all. **The third is the one that dates it**, and it is not optional:
the first two are true at every revision that CARRIES the defect, so on their own they return a
range and not a revision — `four screen-two legs` is present body-scoped at **both** `7982c18` and
`06ef40f`, and both bodies walk to six, so only the predecessor negative at `8909ec4` says which of
the two shipped it. Through v1.96 this list was recall-driven and was wrong on **all three** labels;
v1.97 re-derived every member, and the cardinal *three* survives while every label moves:

| Member | Shipped in | Landing commit | 1 — the short cardinal, body-scoped | 2 — the surface that cardinal counts, same commit | 3 — predecessor negative | Repaired in |
|---|---|---|---|---|---|---|
| The carve-out table published as five rows | **v1.93** | `8909ec4` | `Five members` → **1** | the v1.94 stamp driver — **not** the `grep -cF` form; the one command is published under §Measurements in the block introduced as *the stamp-driven driver*, and is pointed at rather than re-typed here — run body-scoped over that same body → **13** matching lines (whole-file **16**), resolving to **seven** distinct probes. **The resolution is published rather than left as a reading**, because a partition nobody can re-derive is not checkable whatever its total. Each probe contributes the stamp on its prose and the stamp inside its recorded output, which is why most contribute two: argparse's `exit_on_error` **2** lines, the `awk` boundary probe **2**, `rmtree` on `0o000` **2**, the reader-less FIFO **2**, the naturally emptied group **2**, the AC-5.2 group-kill-and-escape **1**, the markdown-it-py grammar corpus **1** — **seven** probes over **12** lines — plus **1** line that is prose *about* the stamp form (`python: 3.11.8 \| darwin` quoted inside the carve-out's own wording) and is no probe at all. Assignment by hand, as the owning paragraph says it must be; it cannot drift, because `8909ec4` is a landed commit | `Five members` → **0** at `6f0ee85` (v1.92) | v1.94, `7982c18` — `Seven members` → **1** |
| The register said three OS probes | **v1.94** | `7982c18` | `three OS probes` → **1** | the carve-out table's OS/runtime rows at `7982c18` → **five** (argparse `exit_on_error`, group kill and escape AC-5.2, `rmtree` on `0o000`, the reader-less FIFO, the naturally emptied group). **A hand reading of that body's eight-row table and no `grep` at all**, said here because a cell that looks like the others but is not runnable as one is the unrunnable-cell defect: the other three of the eight are the `awk` boundary probe, the scanner grammar corpus and the wrapper | `three OS probes` → **0** at `8909ec4` (v1.93) | v1.95, `06ef40f` — `**five** OS- or runtime-determined probes` → **1** |
| The screen-two clause said four legs | **v1.94**, then carried unrepaired through v1.95 (`06ef40f`, same clause, same four-leg enumeration, same six executed legs) | `7982c18` | `four screen-two legs` → **1** | §Measurements' executed screen-two legs at `7982c18` → **six**: the four the sentence names plus the multi-word-gap probe and the cardinal-alternation probe, both already in that body (`three importing test files` → **1**, `printf 'zero files` → **1**; **what these two cells claim is presence, not count** — any value ≥ **1** establishes the probe was in that body and the six-leg walk turns on nothing else, so a later reader who measures a different integer at a different commit has not falsified the row) | `four screen-two legs` → **0** at `8909ec4` (v1.93) | v1.96, `f91a74b` — `**six** screen-two legs` |

**Every cell above written in `<needle> → N` form is that one command,
`git show <commit>:<doc> | awk '/^## Version History/{exit}{print}' | grep -cF '<needle>'` — and
the scoping is deliberate, because two cells are not in that form and v1.97 claimed the blanket.**
The two exceptions are named at their cells rather than left for the reader to discover: column 2 of
row 1 runs the stamp-driven `-E` alternation, not `-F`, and column 2 of row 2 is a hand reading of
an eight-row table and involves no `grep` at all. Two details of the `-F` form are load-bearing
rather than tidy. **`-F`**, because two of these needles
carry `**` and an unescaped `*` is a repetition operator to a BRE — run without `-F` the
`**five** OS- or runtime-determined probes` cell does not return a wrong number, it **fails**:
`grep: repetition-operator operand invalid`, measured on the `06ef40f` body under
`grep (BSD grep, GNU compatible) 2.6.0-FreeBSD`. **The stamp is on the message, not on the failure,
and the difference was executed rather than assumed**: an interactive shell here resolves `grep` to
`ugrep`, which rejects the same pattern with `error at position 4 ... empty (sub)expression` instead
— so the load-bearing half (it **fails** rather than returning a wrong number) is implementation-
independent and the quoted text is not. Every `-cF` cell above and the `-cE` driver of row 1 column
2 return identical values under both implementations, checked one by one. **The `awk` prefix**, because
§Version History quotes every cardinal it repairs, so the whole-file form double-counts —
`three OS probes` returns **2** over the whole file at `7982c18` and **1** body-scoped.
**Every cell in this table is a property claim under DECISION Q and is re-run whenever the table is
edited, not carried from the revision that wrote it** — v1.97 shipped a cell reading `2` that no
scope returns at the commit the cell names, because the reading was taken at `f91a74b` and
attributed to `7982c18`, which is the very defect the table exists to close, committed inside the
table. Residual, stated because the rule does not reach it: a cell whose command differs from the
stated `-F` form is outside a check written against that form, which is why the two exceptions above
are named rather than absorbed.
**A further residual, and it is a property of every cell here rather than of any one of them: each
needle in this table appears literally in this document's body, so each cell is a member of the
corpus its own screen counts.** What makes the cells stable is not the awk prefix but the commit
argument — every cell's commit (`6f0ee85`, `8909ec4`, `7982c18`, `06ef40f`, `f91a74b`) predates the
revision in which its needle was first quoted in this table, so no cell counts its own quotation.
Executed rather than asserted: `three importing test files` is **1** body-scoped at `7982c18` and
**4** at `1cbddb7`, and one of the four is this table's own cell — the drift is real and the commit
argument is what refuses it. **The rule this generalises to, and it binds every *counting* screen
this document publishes, not just these cells: a screen whose published value is a count of members
may not have its needle appear literally inside the scope it counts, and where it unavoidably does —
a self-counting document — the scope is pinned to a commit that predates the quotation.**
**The scoping to *counting* screens is not a hedge and the exception is named**: a **detector**
screen, whose published result is the *set of lines it prints* rather than a cardinal, expects its
needle in scope by construction and discriminates by co-occurrence instead — screen one below is
exactly that, its `[Mm]easured` branch matches this document's prose dozens of times deliberately,
and what makes it a screen at all is the `!/[0-9a-f]{7}/` filter, not the absence of the needle.
Residual, and it is the whole discriminating power of that class: a detector screen is only as good
as its co-occurrence filter, so a line that carries the marker and an unrelated seven-hex-digit token
is declined for the wrong reason and nothing here catches it. Second residual, on the counting rule:
it covers needles that are literal strings; a screen whose needle is a regex class can be matched by
prose that contains no literal, and nothing here detects that — the stamp-driven `-E` driver of row 1
column 2 is exactly such a screen, and it is pinned by the same commit argument for the same reason.
**Three residuals, and none of them is closed by the rule.** (1) A revision's landing commit is not
derivable from its number without the log, so each member carries its commit in the table; the
derivation is `git log --oneline --reverse -S'- v1.NN:' -- <doc> | head -1`, which returns
`8909ec4`, `7982c18`, `06ef40f`, `f91a74b` and `1cbddb7` for v1.93 through v1.97. **The needle is
the Version History entry's leading token and nothing narrower, because a narrower one dates only
the entries that happen to share its wording**: through v1.97 this was published as
`-S'- v1.NN: Plan audit'`, which returns the same five commits but returns nothing for a revision
whose entry does not open *Plan audit* — v1.98's does not. Residual: a revision that has not landed
has no landing commit and the derivation correctly returns nothing, which is indistinguishable from
a needle that does not match, so the reader checks that the entry exists before reading the silence. (2) The
predecessor negative dates the *needle*, not the *defect*: a revision that shipped the same
population-short claim in different words is invisible to it, and only re-reading the predecessor
finds that. (3) **The rule provably cannot see a population understated in prose with no number at
all** — a sentence saying "the OS probes" rather than "the three OS probes" is short by exactly the
same amount and there is nothing to grep for; that category is caught only by walking the counted
surface, which is the obligation the paragraph below puts on the author. The table is **not offered
as complete**: every member in it was found by an audit rather than by this document, and a fourth
that no round has looked for is invisible to a rule about members already named — which is the
argument for the rule and not against it. **Every cardinal this document fixes over one of its own surfaces — "the six
screen-two legs", "Seven members at `cf3a862`", "the **five** OS- or runtime-determined probes",
"thirteen rows … twelve exempt probes" over the carve-out population as v1.99 extends it, "five
members" of the stdlib-premise class closed under §Measurements,
"the three admissible categories" — is a completeness measurement under DECISION G, and is derived by walking the
surface it counts and counting the stamped legs, never by recall or by carrying the previous
revision's cardinal.** **Each member of that list is a quotation of a surface this document
actually carries, and through v1.100 one of them was not**: `"admissible are …"` occurred **once**
in the whole file — the list entry itself — so a reader told to go and check it had nowhere to go.
It is replaced by `the three admissible categories`, and the class is closed by a check every
member now passes rather than by repairing the one: **each needle must return ≥ 2 over the
paragraph-joined body**, once as the list entry and at least once at the surface it quotes.
Run at `b3be433` with
`awk '/^## Version History/{exit}{print}' <doc> | tr '\n' ' ' | grep -oF <needle> | wc -l`,
the joined form being required because this document hard-wraps and a needle can straddle a
newline: `the six screen-two legs` **2**, ``Seven members at `cf3a862` `` **2**,
`five** OS- or runtime-determined probes` **5**, `twelve exempt probes` **2**, `five members`
**2**, and the sixth — the one this repair introduced — **1**.
**That sixth member FAILS the `≥ 2` check at the sha the check is stamped at, and it fails it
precisely because it is the member being repaired**: at `b3be433` the list still carried the broken
`"admissible are …"` entry, so the replacement phrase existed only at the real surface it quotes and
had no list entry yet to be its second occurrence. **v1.101 published `2` for it, which is a value
the command does not return at that sha or at any of the three before it** — `1` at `1cbddb7`,
`700c599`, `8c6539a` and `b3be433` alike, line-scoped and joined alike. **The class, and it is the
reason this is written out rather than quietly corrected: a check introduced by a repair is
evaluated against the body the repair produces, never against the body it repaired, and where the
two differ the check publishes both readings and names which is which.** A `≥ 2` reading taken at
the pre-repair sha is a measurement of the defect, not of the fix.

**The post-repair reading is therefore stamped at `00b961f`, the commit v1.101 landed at, and not at
"the body this revision produces"** — an unlanded self-count is re-derivable by nobody, which is this
document's own standing rule and was broken here by the sentence stating it. At `00b961f` the six
read **3, 3, 6, 3, 3** and **4**: `+1` for the first five, because the sentence listing the needles
quotes each of them once, and **`+3`** for the sixth, whose three added occurrences are its entry in
the cardinal list above, the sentence recording what it replaced, and its appearance in that same
needle list. **v1.101's "every one of them reads exactly one higher" was true of five members and
false of the one the whole paragraph is about**, which is the self-match this document measures
everywhere else, mis-generalised from the five that behaved to the one that did not. **v1.102 moves
all six again and its own readings are re-taken at its landing commit rather than published here.**
**Residual, and it is why this is a rule and not a screen**: no shape filter can
count a population whose members are prose paragraphs, so the obligation sits on the author and the
reader's check is to walk the counted section and match its stamped legs against the cardinal. A
second residual on the ≥ 2 check itself: it establishes that the needle is *findable*, never that
the surface it finds is the one the cardinal is about — a needle quoted a second time in an
unrelated sentence passes it.
Inherited-unverified at `af19d53`, the commit v1.103 is measured at — re-stamped from v1.102's
`dfae038` rather than carried, because a register that names a commit older than the revision's own
measurement commit is the same detachment the closure paragraph above repairs, **and v1.100 left it
at `700c599` while being measured at `8c6539a`, which is that detachment happening again in the
paragraph that defines it**. **The v1.102→v1.103 move is discharged by the interval argument run
rather than recalled**: `git rev-list --oneline dfae038..af19d53` returns exactly **seven** commits,
of which **three** — `59cc2ad`, `7b182b0` and `3f70eb3` — touch any of the four feature documents,
by `git diff --name-only <sha>^ <sha> -- <plan> <spec> <impl-plan> <design>` run per commit. Those
three are the landings of the round-fifteen batch (this document's own v1.102, plus spec v1.62,
impl-plan v1.51 and design v1.107), and **each of those revisions' Version History entries
enumerates its re-runs and names every member of this register under `NOT RE-RUN`** — so no member
was re-run inside the interval and the stamp moves. The other four — `4c1c3a5`, `b442a80`,
`7b9d174` and `af19d53` — touch only audit reports under `docs/01-plan/features/` and
`docs/02-design/features/`, and `h-mad/scripts/` and `h-mad/tests/`. **This is deliberately not
argued from byte-identity, which would be false for three of the seven.** Residual, and it is the
one `af19d53` makes concrete rather than hypothetical: this argument covers members re-run by a
*revision*, and `af19d53` is a commit no revision of these documents produced — it changed
`h-mad/` under the register, which is why the `h-mad/`/`handoff/` closure in §Measurements had to
be retired at this stamp rather than carried.
**The v1.101→v1.102 move this one replaces was discharged the same way**: `git rev-list --oneline
b3be433..dfae038` returns exactly **three** commits,
of which only `00b961f` (v1.101's own landing) touches any of the four feature documents — `df04e8e`
touches a handoff file alone, and `dfae038` touches
`docs/handoffs/2026-09-05-main__doc-block-exec-rounds-twelve-to-fourteen.md`, `docs/learnings.md`
and `docs/skill-candidates.md`, per `git show --name-only --format='' <sha>` on each.
**v1.102 wrote "`docs/handoffs/` alone" for both, inherited from the round-fifteen orchestrator
decision sheet and never measured here; the correction is the word and not the argument**, which is
stated in full at the measurement-commit paragraph in §Measurements. `00b961f`'s Version History entry
enumerates its re-runs and names the
register's contents under `NOT RE-RUN`, with no member of this register among them — except the six
screen-two legs, which that revision *did* execute and which are therefore entered above stamped to
it rather than covered by the interval. Not argued from byte-identity, which would be false:
`git diff --shortstat b3be433 00b961f -- <doc>` reports **348 insertions, 91 deletions**.
**The v1.99→v1.101 move before that was discharged the same way**: `git rev-list --oneline
700c599..b3be433` returns exactly **two** commits, `8c6539a`
(v1.99's own landing) and `b3be433` (v1.100's), and both revisions' Version History entries
enumerate their re-runs — no member carried into this register is among them, both entries instead
naming the register's own contents under `NOT RE-RUN` — so the stamp moves. Stated so the arithmetic is not mistaken for
byte-identity: the document did change across that interval,
`git diff --shortstat 700c599 b3be433 -- <doc>` reports **482 insertions, 13 deletions**.
**The interval argument covers only the members that were already in the register when the stamp
moved, and this revision both adds and removes members**, so the blanket is replaced by a
per-member statement: **every member below names the revision, the commit, *or* — for a carve-out
probe that no repository sha determines — the runtime or renderer version its last execution is
stamped at**, and "inherited-unverified" means exactly that no member's last-execution revision is
v1.103. **The predicate names one revision — this one — and never a span**: v1.101 executed one
member, the six screen-two legs, so "no member's last execution is v1.101" would be false for
exactly that bullet, and v1.102 executed none, so it could be added and next round a third could,
and the lead would grow by one name per revision until it drifted. **The class, and it is why the
bullets below no longer enumerate the revisions that did *not* run a member**: a predicate over the
revisions since a member's last execution is stated once, here, as a property of *this* revision,
and each bullet states only the revision and commit its own last execution is stamped at. Residual:
that leaves "which revisions ran nothing" derivable only by walking the Version History entries,
which is the derivation this document has already found unreliable twice — the register buys
non-execution as of one named revision and does not buy a history.
**The disjunction is exact and v1.100 through v1.101 wrote it as a conjunction
("the revision *and* the commit"), which four of v1.101's six members falsified on sight** — only two of those six named
an executing revision, and the `markdown-it-py` bullet names **neither** a revision nor a sha, being
stamped `2.2.0` and `4.2.0`. **The class: a lead sentence asserting a uniform property of a list is
checked against every member of that list before it is written, and where the property does not hold
uniformly the lead states the disjunction rather than the strongest case.** Residual, and it is the
reason the third disjunct exists at all: a version stamp dates the *runtime* a probe ran on and not
the *revision* that ran it, so for that member the register can say the reading is not v1.103's
and cannot say which revision took it. **This is the register's only lead**; v1.101 carried a second
one, in the sentence that now opens "No member's status is stated with a deixis", saying the same
thing with the other quantifier, and two leads for one list are
the copy-that-drifts shape this document argues against everywhere else — they had already drifted.
A member entered by this revision is covered by its own stamp and not by the interval,
because the interval says nothing about a figure that was outside the register while it ran.
**The justification for moving the stamp is about the interval, and the interval must contain the
stamp being replaced — v1.97's did not.** v1.97 replaced `68a70d6` and justified it with
"byte-identical across `f91a74b..7d8e797`", a span that *excludes* `68a70d6`
(`git merge-base --is-ancestor 68a70d6 f91a74b` succeeds, and `git diff --stat 68a70d6 f91a74b -- <doc>`
is **149 insertions, 30 deletions**), so the reader was sent to check a span the old stamp is not
in. **The axis is what the lead stamp asserts, and it asserts non-execution and never a value**: it
says these figures had not been re-run *as of* the commit named, so moving it forward is a claim
about the half-open interval `(old stamp, new stamp]` — here `(7d8e797, 1cbddb7]`, which contains
`7d8e797`'s successor and nothing else — and it is wrong only if some member *was* re-run inside it.
The only commit in that interval is v1.97's own landing, whose re-runs are enumerated in the closure
paragraph above and in its Version History entry, and no register member is among them. **This is
deliberately not argued from byte-identity, which would be false here**: this document *did* change
across `7d8e797..1cbddb7` (`git diff --shortstat 7d8e797 1cbddb7 -- <doc>` reports **158 insertions,
32 deletions**), and byte-identity was never the right premise anyway — a member's value can be
moved by a sibling's edit without this document changing at all. Residual, stated because no screen
reaches it: "no member was re-run in the interval" is knowable to the author of the revisions in it
and to a reader of their Version History entries, and by nothing else; a member re-run by a
*sibling* document's revision is invisible to both.

**No member's status is stated with a deixis** — the stamp rule itself is stated once, in the lead
above, and is deliberately not restated here. Through v1.100 **three** status assignments in this register
turned on the words *this revision* — the `cf3a862` probes' membership, the `700c599` probes'
**non**-membership, and the triage categories' — and a deixis names a different revision every time
the document is revised. The `700c599` one was therefore false the moment v1.100 shipped without
re-running what v1.99 had run: that is the softer failure this register exists to close, committed
by the register itself. **The axis is a status assignment whose subject is a revision, and the rule
over it is that the revision is named by number and never by *this* one.** Residual, stated because
the phrase is not banned: `this revision` reads **32** body-scoped at `b3be433`
(`grep -ciF 'this revision'` over the `awk`-prefixed body) and most of those are legitimate —
a revision describing its own act at the moment it acts. **A value sweep on the phrase is the wrong
screen**; what is repaired is the narrower class of sentences that assign a *status a later reader
will read*, and those are found by walking this register and nothing else. The members:

- The `doc-auditor.md` fence-toggle `8`/`4` readings — stamped `35698f9` at their own site.
- The Setext differential and its `files=25`/`files=30` printouts — stamped `1861157` at their own
  site; the bullet stating them already marks them as not re-run.
- The markdown-it-py **14-case** grammar corpus — stamped `markdown-it-py 2.2.0` and `4.2.0` and
  by no sha, being a carve-out probe; it needs a throwaway venv. The fence-body de-indentation
  probe added in **v1.95** was run on both renderers and is *not* part of that fourteen, so the
  fourteen stay unverified here.
- The **five** OS- or runtime-determined probes of the carve-out table's **`cf3a862` block** —
  stamped `python 3.11.8 | darwin` and read at `cf3a862`. They are argparse's `exit_on_error` routing (§Scope), `rmtree`
  on a `0o000` directory (AC-3.14), the reader-less FIFO (AC-3.10), the naturally emptied group
  (AC-5.5) and the AC-5.2 group-kill-and-escape probe. **The block scoping is load-bearing now that
  the table has a second block**: "five of the carve-out table" would read as a claim about
  **twelve** exempt probes, and the other seven of the twelve sit in different register positions —
  the five in the **bullet immediately below**, plus the `awk` boundary probe and the scanner
  grammar corpus, each handled in its own bullet further down.
- The **five stdlib probes of the carve-out table's `700c599` block** — last executed **v1.99**, at
  `700c599`. **The revisions since are not enumerated here** — that enumeration read "v1.100 or
  v1.101" through v1.102, which did not re-run them either, so it was already a round stale when it
  shipped and would need extending every round; the lead's predicate covers every revision since by
  construction. **They are members now and were not before, and
  the reason is the deixis and not a new measurement**: through v1.100 they were held out of the
  register on the words "executed in this revision", which was true of v1.99 and false of every
  revision after it — v1.100's own Version History entry lists `the five 700c599 stdlib probes' own
  outputs` under `NOT RE-RUN` while this paragraph still said they were not members. A carve-out
  probe leaves the register **only for the revision that executes it** and re-enters at the next
  revision that does not, which is why membership is now stated against a revision number.
- The **three `74e126f` self-counts** the closure paragraph above states — entered in **v1.97**, by
  pointer and not by copy; stamped `4e4a00c` on the surface that owns them.
- The **six screen-two legs** — last executed **v1.101**, at `b3be433`; the revisions since are
  covered by the lead's predicate and not listed, for the reason the stdlib bullet gives.
  **They left this register for v1.101 alone and re-entered in v1.102**, by the same rule the
  `700c599` stdlib bullet states: a leg leaves the register only for the revision that executes
  it. Their outputs are published at their own site under §Measurements, which owns the values; this
  entry owns their status. The checker they were run against — the spec's enumeration — moved in
  `00b961f`, and that motion is diffed rather than assumed at the site that states the legs.

**Residual on the last-execution stamps, stated rather than papered over**: three of the seven
entries above name an executing *revision* (`v1.99` for the stdlib block, `v1.97` for the
self-counts, `v1.101` for the screen-two legs); three name the **commit** their reading is stamped
at; and one — the `markdown-it-py` corpus — names **neither**, carrying only its two renderer
versions, which is the third disjunct the lead states. **The cardinal is `seven` because the list
above was walked and its bullets counted for this sentence** — re-walked for v1.103 and not carried
from v1.102's `seven`, even though the value did not move: v1.103 neither adds nor removes a member,
which is a *reason the count is unchanged* and not a licence to skip counting it, and a cardinal
over a list this revision edits is the exact shape §Measurements writes a rule against. That is what
this document records for them, and reconstructing a revision number from
a stamp is the recall the register exists to refuse. A stamp is enough for the register's purpose —
it says the reading is not v1.103's — named by number; a deixis here would
name a different revision at every future revision, which is the exact defect this register was
rewritten to close — and it is not enough to say *which* revision last took it. Closing that would
mean walking the Version History for each, which is the one derivation this document has already
found unreliable twice.

**Left the register in v1.101**: the **six** screen-two legs named below, all six re-executed at
`b3be433` against the spec's enumeration *as that document ships it at `b3be433`* and all six
reproducing — outputs published at their own site. They re-enter at the next revision that does not
re-run them, by the rule stated in the bullets above, **and v1.102 is such a revision: it re-ran no
leg, so all six are back in this register, last executed v1.101 at `b3be433`.**
**The checker those legs were run against moved in `00b961f`, and the scoping clause is therefore
discharged by comparison rather than left standing**: the spec went to v1.61 in that commit, and
`diff <(git show b3be433:<spec> | grep -A14 -E '^  \$ awk ') <(git show 00b961f:<spec> | grep -A14 -E '^  \$ awk ')`
returns a **single** changed line, `v1.60 draft` → `v1.61 draft`, in prose *below* the fence; the
enumeration program itself is byte-identical and `grep -cE '^  \$ awk '` returns **1** on the spec at
both shas. So the six readings survive their checker's revision — but they survive it *measured*, not
*assumed*, which is the only reason the clause is retired rather than repeated. **The class: a leg
run against a checker that lives in another document carries the checker's sha too, and a revision
that moves that document either re-runs the legs or diffs the checker and says which.**

**On the `74e126f` self-counts specifically, and the head noun is repeated rather than left to the
nearest antecedent**: the three self-counts' integers, their commands and their
`4e4a00c` stamp stay on the one surface that owns them, because this document's rule is that a
pointer to the owning surface never drifts and a second copy does — **and v1.97's copy had already
drifted in the one respect a copy can drift without changing a digit**: it labelled all three
"body-scoped" when one of the three is by construction a whole-file count, a distinction the owning
paragraph makes load-bearing. **That last member is here because the register's population
statement admits no exception**: through v1.96 those three were handled by an inline residual
sentence in the closure paragraph and nothing else, and an inline residual is not a register entry,
so they sat outside both the interval closure and this list — which the paragraph above defines as a
defect in the register rather than a licensed gap. That inline sentence is retained deliberately and
now points here, so the two surfaces state one arrangement rather than two: it owns the integers,
this entry owns their status. **It is described here by its role and not by quoting its opening
words** — a quotation of another surface's text is a copy that drifts silently the moment that
surface is edited, and v1.97's quotation of it is exactly the copy that would have gone stale in
**v1.98**, the revision that wrote this sentence and that said *this revision* where it meant a
revision number. **They are entered as unverified rather than
re-published, and that is deliberate**: the paragraph states in as many words that no integer in it
is the number of covered figures and that the two `git diff` commands are the whole evidence, so a
fourth stamped triple would add three maintained figures and no argument. **The carve-out table's
two other exempt rows are stated one per line, because through
v1.95 they were joined by a flat "not in this register" that was wrong for one of them and only
half-true for the other:**

- The **`awk` boundary probe** row is **out** of this register: v1.96 re-ran all five of its legs,
  published above as one command per leg on `awk version 20200816`. Through v1.95 this row was
  kept out on the strength of an `awk --version` stamp and the three per-branch controls, and this
  section says in as many words that those controls are not this probe — so the row was out of the
  register on evidence that did not cover it.
- The **scanner grammar corpus** row is **in** this register for its fourteen and out for its
  fifteenth: only the one new case was run. Its fourteen are the register entry named above as
  *the markdown-it-py 14-case grammar corpus* — addressed by that name and never by a sentence or
  paragraph ordinal, for the same reason the carve-out table's rows are. Nothing about that row is
  claimed beyond the one case.

Also carried rather than re-run, and stated against a revision number for the same reason as the
bullets above: the **membership** of the five triage categories below, which the v80 audit
re-derived at `8909ec4` — v1.94 re-ran only their *total*, and **v1.101 re-ran neither**. Three of the six
revisions in between say so at their own entries and three are silent, which is derivable rather
than recalled: `awk '/^## Version History/{f=1} f && /^- v/{n=$2} f && /triage categor/{print n}'`
over this document returns `v1.94 v1.95 v1.96 v1.99` plus this revision's own entry, so v1.97,
v1.98 and v1.100 name it nowhere and their silence is not a claim in either direction — **which is
the register's own argument applied to the register's own evidence**. The self-match is stated for
the same reason it is one bullet up: the command matches the entry that publishes it. **The register is
itself a completeness
claim and is therefore not offered as complete**: it lists what **the revision whose number is on
the lead stamp** knows it did not run,
and the honest residual is that a figure nobody has thought to name is invisible to it. What the
register does close is the softer failure — a figure that *was* named by an audit as unverified and
then quietly acquired the freeze sha anyway.

**A checker this document publishes is executed against a positive and a negative control before
any count derived from it is published.** A screen that has never been shown to fire, and never
been shown to stay silent, is an assertion wearing a command's clothes; the rule below exists
because exactly that failed here, in the revision that introduced it.

**Two rules over that one, because the machinery kept being right while its self-description was
wrong.** (1) **Per branch, not per composite.** A control run over an alternation tests the
alternation; a healthy branch covers a sick one, and this document half-applied one boundary repair
in three consecutive revisions while passing its own alternation-level control every time. So every
published alternation is fired **one branch at a time**, against a fixture carrying one line per
property that branch claims. Residual, and it is why this is a rule and not a screen: an alternation
can also be spelled as two greps in a pipe, or as two separate commands in one paragraph, and no
shape filter over `(a|b|c)` sees either form — the obligation is on the author writing the
alternation, and the reader's check is to find every branch named in the control beside it.
(2) **Every *property* a screen claims is a claim about code and is executed, never reasoned.**
What it is immune to, what it cannot match, which side of a boundary it reads, what its zero means:
each of those is executed by *doing the thing it claims immunity from* and showing the number did
not move. Where a property could not be executed it is written as **unexecuted**, because an
unexecuted property claim reads as a verified one and is worse than no claim at all.

**Why this class survived its first sweep, which is the reusable half.** The sweep at v1.88
enumerated *values* — `67`, `68`, `25/30`, "five hits" — and every member it found had already
drifted, so the members whose value had **not** moved were invisible to it: the importing test
files (`grep -rln 'from docsections import' --include='*.py' h-mad handoff` → **3** at `74e126f`),
the `_gate_bash_block()` call sites
(`grep -n '_gate_bash_block()' h-mad/tests/test_h_mad_collect_report_docs.py` → the `def` plus
**3** at `74e126f`), and the absent `.returncode` reads
(`grep -c returncode h-mad/tests/test_h_mad_collect_report_docs.py` → **0** at `74e126f`) — every
one arithmetically right then and still right now, and every one unprovenanced then. This
paragraph carries those three commands rather than pointing at the paragraphs above, because the
rule admits no carve-out for explanatory prose: a re-derivation paragraph that restates tree counts
without them is itself a member, which is precisely how v1.89 wrote a fresh member into the one
paragraph whose stated purpose was re-derivation. The sweep also stated the axis as "without the
sha", which let a member carrying a command but no sha read as compliant, and it recorded the rule
only in a Version History entry, so the rule governed nothing written afterwards. All three
failures are failures of a *value* sweep, so the two screens below filter by **shape** instead, and
live in the document body where the next author reads them.

**Screen one — the provenance markers the rule names. This document owns it.**

```
$ awk '/^## Version History/{exit} /(^|[^[:alnum:]_])[Mm]easured([^[:alnum:]_]|$)|(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)|(^|[^[:alnum:]_])[Tt]his [Ss]ession([^[:alnum:]_]|$)/ && !/[0-9a-f]{7}/{print NR": "$0}' \
      docs/01-plan/features/doc-block-exec.plan.md
```

**Every marker is bounded on both sides and folded on its INITIAL letters only, and each of those
is a repair with a member behind it.** The alternation has exactly three branches, one per marker
the rule names, and none of them is anchored on neighbouring punctuation or on a following word.
Through v1.92 there were five branches: `\(measured\)`, `measured[,)]` and `measured with` for one
marker plus a lowercase-only `today` and a lowercase-only `this session`. See below for what each
repair reached.
**"Case-folded" was the wrong word for it through v1.94, and the difference is executed rather than
argued.** Each branch folds only the word-initial letters — `[Mm]`, `[Tt]`, and `[Tt]`/`[Ss]` for
the two-word marker — so an ALL-CAPS marker is **not** matched:

```
$ printf 'MEASURED\nTODAY\nTHIS SESSION\n' \
    | awk '/(^|[^[:alnum:]_])[Mm]easured([^[:alnum:]_]|$)|(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)|(^|[^[:alnum:]_])[Tt]his [Ss]ession([^[:alnum:]_]|$)/'
$
```

Nothing printed — **the alternation** declines all three. The fixture is piped through the bare
three-branch alternation alone, which is the per-branch rule's own form of evidence; it carries
neither the `/^## Version History/{exit}` stage nor the `!/[0-9a-f]{7}/` stage the shipped screen
adds, so calling this a run of *the screen* would be the same conflation this section spends two
paragraphs undoing for the `\b` probe and the six-line widening fixture. That is a **stated
residual, not a defect being
fixed here**: the ALL-CAPS form does not occur in this body, executed rather than assumed —
`git show 4e4a00c:<doc> | awk '/^## Version History/{exit}{print}' | grep -cE '(^|[^[:alnum:]_])(MEASURED|TODAY|THIS SESSION)([^[:alnum:]_]|$)'`
→ **0** at the freeze, and the same grep fed `printf 'stamped TODAY with no sha\n'` returns **1**,
which is the positive half proving the zero is an absence and not a dead pattern. The zero is
stated at `4e4a00c` and not at "now" because this paragraph writes all three ALL-CAPS forms into
the body, so a post-edit run returns at least three, every one of them this control's own text.
Folding every
letter would need `[Tt][Hh][Ii][Ss] [Ss][Ee][Ss][Ss][Ii][Oo][Nn]` per branch and buys nothing
against a shape that has never appeared; if one ever does, the absence grep above is what finds it.

**The boundary form is POSIX-ERE and not `\b`, and that is a correction rather than a style
choice.** Through v1.90 the `today` branch was written `\btoday\b`. In awk `\b` is a
**backspace escape**, not a word boundary, so that branch could only ever match a line
carrying a literal 0x08 — one of the three markers the rule names was unenforceable, a third of
this screen was dead code, and the before/after pair v1.90 published was produced by a filter blind
to one of its own enumerated forms. That is why no count from before v1.91 is carried forward here.
Probed on the interpreter this repository runs — `awk --version` → `awk version 20200816`, the
macOS default — over a two-line fixture written by
`printf 'measured today\nremeasured todayish\n'`: the `\b` form prints **nothing**; a bare `/today/`
prints **both** lines, which is the positive control showing the fixture is reachable at all;
`printf 'a\bb\n' | awk '/\b/'` **matches**, which is the second positive control and is what proves
`\b` is a literal backspace rather than a construct that never matches anything; and
`awk '/(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)/'` — **the `today` branch alone, not the
alternation**, which is what makes this a single-branch control under the rule above — prints the
**first line only**, which is the discrimination the rule wanted and the negative control the `\b`
form could not produce. The case half of the branch is controlled on its own line, since the
two-line fixture is lowercase throughout and would have passed a lowercase-only branch:
`printf 'Today it was measured\n' | awk '/(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)/'` prints its
line. This is an interpreter-behaviour probe, so it is stamped
with its interpreter under the carve-out below rather than with a repository sha — and for exactly
that reason it is the **`awk` boundary probe** row of the carve-out sweep's table, named rather than
numbered because that table is swept and reordered.

**All five legs re-run in v1.96, because through v1.95 the register said this probe "was re-run
here" and cited evidence that was not this probe.** The evidence it cited — `awk --version`
returning `awk version 20200816`, plus the three per-branch controls further down — is a
*re-confirmed interpreter stamp* and three controls the same section explicitly says are **not**
this probe. A stamp is not a run. Below: the interpreter stamp on its own first line, then the
**five** legs, one command per leg, each carrying the exact fixture the sentence above names — so
the block holds six commands and the cardinal *five* counts legs, not lines:

```
$ awk --version
awk version 20200816
$ printf 'measured today\nremeasured todayish\n' | awk '/\btoday\b/'
$ printf 'measured today\nremeasured todayish\n' | awk '/today/'
measured today
remeasured todayish
$ printf 'a\bb\n' | awk '/\b/' | wc -l
       1
$ printf 'measured today\nremeasured todayish\n' \
    | awk '/(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)/'
measured today
$ printf 'Today it was measured\n' \
    | awk '/(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)/'
Today it was measured
```

Five legs, and every one reproduces what the prose above claims: the `\b` form
prints nothing, the bare `/today/` prints both lines, the literal-backspace positive matches
(counted with `wc -l` rather than printed, because its one output line carries a raw `0x08` that no
fence can render honestly — the count is the observation, and `0` would be the falsification), the
POSIX `today` branch alone prints the first line only, and the initial-capital case line prints.
**The mutation each leg applies is named in the leg itself**: the fixture string is written inline
in every command, so the input a reader reproduces is the input this paragraph describes, and no
leg's evidence is a different leg's. Because this is an interpreter probe the run is stamped
`awk version 20200816` and not by a repository sha; nothing in it reads the tree.

**The `measured` branch was repaired on one side only, and v1.93 repairs the other.** Through
v1.90 that branch required a comma immediately *before* the marker — `, measured[,)]` — so
`— measured, it selects a different, untagged block`, the em-dashed form this document's Risks
table actually writes, was invisible to it. v1.91 removed the **leading** anchor and left the
**trailing** one: `measured[,)]` still demands a `,` or a `)` in the very next column, so a
sentence writing `measured on the supported interpreter` or `measured 2026-09-03,` fell through.
That is a **half-fixed boundary, and it passes the test written for the half that was fixed** —
v1.91 verified the em-dashed member and closed the class on it. The rule the two failures share is
one rule: **a marker branch must not be anchored on neighbouring punctuation in either direction,
nor on a following word, nor on case**, because all four are house style that changes per sentence
while the class does not. So the three `measured` branches collapse into one both-sides POSIX
form, and the same both-sides treatment is applied to *every* sibling branch in the expression in
the same edit rather than to the branch an audit happened to name.

**v1.93 wrote that sentence and applied it to two branches of three, which is the third
half-application on this one expression in three revisions — and v1.94 repairs the mechanism, not
just the branch.** The three are: v1.91 replaced `\b` on `today` only; v1.92 added a leading anchor
and left the trailing one; v1.93 gave `[Mm]easured` and `[Tt]oday` both-sides POSIX boundaries and
left `[Tt]his session` with **none**, while the paragraph above it asserted in bold that every
marker was bounded on both sides and case-folded. Measured on the published v1.93 program, quoted
out of the committed body rather than retyped:

```
$ printf 'in this sessionless mode\nThis Session capitalised\nxthis session glued\nthis session\n' \
    | awk '/(^|[^[:alnum:]_])[Mm]easured([^[:alnum:]_]|$)|(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)|[Tt]his session/'
in this sessionless mode
xthis session glued
this session
```

Two substring false positives on both sides, and `This Session capitalised` declined — so the
branch was unbounded *and* not case-folded past its first letter, the exact two properties the
sentence claimed for it. The repaired branch on the same fixture returns the two members and
neither substring:

```
$ printf 'in this sessionless mode\nThis Session capitalised\nxthis session glued\nthis session\n' \
    | awk '/(^|[^[:alnum:]_])[Tt]his [Ss]ession([^[:alnum:]_]|$)/'
This Session capitalised
this session
```

**Why three revisions in a row could half-apply one rule and still pass their own control: the
control was run on the alternation, where a healthy sibling covers a sick one.** Every published
fixture line until now carried `measured` or `today` as well, so the `this session` branch was
never the reason any line printed and its state was unobservable through the whole screen. The
rule over that axis, which is what this revision actually ships: **each branch of a published
alternation is controlled against its own fixture, run with that branch alone, positive and
negative** — the alternation-level control is kept, but it is no longer evidence about any single
branch.

**v1.94 shipped that rule and its own three per-branch fixtures were one-sided on two branches of
three, which is a fourth half-application inside the revision that diagnosed half-application.**
`[Tt]oday`'s fixture carried a *trailing*-glued negative (`todayish`) and no leading-glued one;
`[Mm]easured`'s carried *leading*-glued negatives (`unmeasured`, `remeasured`) and no
trailing-glued one; only `[Tt]his [Ss]ession` carried both. Both regexes were in fact correct — so
the **controls** were the defect, and as published they would have stayed green through a
regression on the unexercised side. The rule over that axis: **a per-branch fixture carries one line
per property the branch claims** — a bounded positive, an initial-capital positive, a
leading-glued negative and a trailing-glued negative — and the check is that the fixture has
exactly those four lines and prints exactly the two positives. All three, run at the freeze on
`awk version 20200816`, each with its branch alone:

```
$ printf 'measured, x\nMeasured at dawn\nanything unmeasured\nmeasuredly so\n' \
    | awk '/(^|[^[:alnum:]_])[Mm]easured([^[:alnum:]_]|$)/'
measured, x
Measured at dawn
$ printf 'it ran today, twice\nToday it ran\nxtoday here\ntodayish drift\n' \
    | awk '/(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)/'
it ran today, twice
Today it ran
$ printf 'this session\nThis Session capitalised\nxthis session glued\nin this sessionless mode\n' \
    | awk '/(^|[^[:alnum:]_])[Tt]his [Ss]ession([^[:alnum:]_]|$)/'
this session
This Session capitalised
```

Three branches, three fixtures, four lines each, two positives out of each — and the block above is
the whole correspondence, one fenced command per branch, so checking it is a scan rather than a
parse of three clauses in one sentence (which is how it was written through v1.94). The two other
controls this screen carries are **not** per-branch boundary controls and are no longer cited as
such: the `\b`-versus-POSIX pair, named **the `awk` boundary probe** in the carve-out table below —
addressed by that name and never by a paragraph ordinal, because paragraphs get inserted — is an
*interpreter* probe about what `\b` means in awk, and the six-line `[Mm]easured` fixture further
below is the *widening* comparison between the v1.92 and v1.93 forms. Both are kept for what they
measure; neither is evidence about a branch's boundaries. Residual, stated
because it is not closed: nothing enforces that a *newly added* branch arrives with its own
fixture, and no screen can check it — the obligation lives in this sentence, and the reader's check
is to read the alternation and find each branch's fixture in the block above.

**The repair changes no published reading, and that was measured rather than assumed.** Over the
v1.92 body as `6f0ee85` shipped it, the v1.94 program returns the same **32** lines as the v1.93
program and the two outputs are byte-identical —
`diff <(git show 6f0ee85:<doc> | awk '<v1.93 program>') <(git show 6f0ee85:<doc> | awk '<v1.94 program>')`
prints nothing, on `awk version 20200816`. So the 9/32 widening, the 23, and the five triage
categories below are untouched by this edit and are not re-derived from scratch. Live impact on the
*current* body is likewise zero, and it is stated as zero rather than inflated: over the body at
`cf3a862`, `awk '/^## Version History/{exit} /[Tt]his session/ && !/[0-9a-f]{7}/{print NR": "$0}'`
prints **2** lines and **both** are also matched by the `[Mm]easured` or `[Tt]oday` branches
(the same command with
`&& !/(^|[^[:alnum:]_])[Mm]easured([^[:alnum:]_]|$)|(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)/`
appended prints **nothing**), so no hit in the triage below ever depended on this branch. Both
readings are of the body at `cf3a862`, which predates this revision's edit — this paragraph writes
`this session` into the document several more times, so a reading taken after the edit would be a
number this paragraph had itself moved.

**The widening is measured, and both halves of the control are run.** Over the v1.92 body as
`6f0ee85` shipped it, the v1.92 screen returns **9** lines and the v1.93 screen returns **32** —
so **23** lines were invisible to the published form and had never been triaged. The v1.94 screen
above returns the **same 32 lines, byte-identical**, over that same body, which is the measurement
recorded with the boundary repair; the readings below are therefore of a program the repair did not
move. All three readings are
by `awk version 20200816`, all three are of a committed body, and each is reproducible with
`git show 6f0ee85:docs/01-plan/features/doc-block-exec.plan.md | awk '<the program>'`. The unit is
**body lines printed**, not occurrences or distinct claims: one wrapped sentence can print twice
and one line can carry two markers. Case-folding alone accounts for four of the twenty-three
(`[Mm]easured` three, `[Tt]oday` one), and it is not cosmetic — the single line `[Tt]oday` adds is
a real member, an unstamped count derived from a sibling document under `docs/`.

**The `[Mm]easured` branch's WIDENING comparison** — what the v1.93 form reaches that the v1.92 form
did not, run at `6f0ee85` over one fixture with the branch alone. It is **not** this branch's
boundary control; that is the four-line fixture in the per-branch block above, and citing this
six-line one as the boundary control is what let a missing trailing-glued negative survive v1.94:

```
$ printf 'anything unmeasured\nremeasured today\nmeasured, x\n(measured)\nmeasured with care\nMeasured at dawn\n' \
    | awk '/(^|[^[:alnum:]_])[Mm]easured([^[:alnum:]_]|$)/'
measured, x
(measured)
measured with care
Measured at dawn
```

Four positives, and the two negatives are the point: `anything unmeasured` and `remeasured today`
are **declined**, because `d` and `e` are alnum characters and the leading boundary refuses them —
so the widening buys reach without buying substring noise. Fed the same fixture, the v1.92 form
returns only the first three, missing `Measured at dawn` entirely; that missing line is the
case-fold member. `remeasured today` is returned by the `[Tt]oday` branch when the whole
expression is run, which is correct and is why the fixture is read line by line rather than
counted.

**The repair for a claim stated without provenance is a pointer, and that generalisation came out
of this same screen.** The one member v1.91's half-repair did surface was the Risks row asserting
the exec-codex scan is unaffected by the tag — an absence claim carrying the marker, no command and
no sha. Its first repair was itself the next defect: it gained a sha, but one no recorded run of
that probe carried, and pointed at a section name this document does not have. The row now carries
no measurement of its own at all and points at the block census under §Implementation Strategy — a
real heading of this document, and the one surface that records the probe with a runnable command
and the sha it was re-derived at. A **pointer to the single surface that owns it** never drifts;
a second copy of the provenance does.

**Screen two — the counted-noun enumeration. This document does not own it, and does not restate
it.** A shape enumeration over counted nouns is one class rule, and the paired spec already
implements it; a second wording of one rule here is the hazard §Success Criteria names below in the
floor-tuple paragraph, and it is what produced the corpus contradiction v1.88 had to unwind. So
this plan runs the spec's enumeration **verbatim**, substituting only this document's path for the
spec's. **The address is the line-anchored one that document designates, not a prose phrase** — a
prose needle sits mid-line, so a §Version History entry quoting it takes the count to 2, while the
anchored form cannot be inflated that way:
`grep -cE '^  \$ awk ' docs/01-plan/features/doc-block-exec.spec.md` → **1** at `6f0ee85`, **1**
at `cf3a862` and **1** at the freeze `4e4a00c`.
Re-checked in the revision that ships it rather than trusted from the commit it was authored at,
because a locator that was unique when written can be broken by a concurrent sibling edit landing
in the **same** commit — which in this feature's rounds is not hypothetical. **Two residuals here,
and they are the spec's three merged rather than a disagreement about how many there are**: what
that document splits into "file-scoped" and "pins the block, not the clause" is one sentence here.
(1) It is file-scoped and pins the fenced block, not any clause inside it, so a claim about
one alternation of that program must say so in words. (2) A second fence in that file opening a
line with two spaces and `$ awk ` makes it 2. **The slot census is published at both shas, because
it moved between them and one number under one stamp would read as a standing property.** One
command —
`grep -oE '^  \$ [a-zA-Z0-9._-]+' docs/01-plan/features/doc-block-exec.spec.md | sort | uniq -c` —
run over `git show 35698f9:`, `git show 6f0ee85:`, `git show cf3a862:` and `git show 4e4a00c:`. At `35698f9`:
**9 openers** over
**5 distinct tokens** — `awk` ×1, `curl` ×1, `git` ×5, `printf` ×1, `python3.11` ×1. At `6f0ee85`,
the commit **v1.93** was audited at: **20 openers** over **11 distinct tokens** — `awk` ×1,
`curl` ×1, `git` ×7, `pairs` ×1, `printf` ×2, `python3.11` ×1, `RULE` ×1, `S` ×1, `sed` ×1,
`split_only` ×3, `while` ×1. At `cf3a862`, the commit v1.94 was authored against:
**21 openers** over **11 distinct tokens** — the same distribution with `sed` ×**2**, the spec's
v1.60 having added one — and at the freeze `4e4a00c`: **21 openers** over **11 distinct tokens**,
that same distribution unchanged, because the spec did not move in the interval
(`git diff --stat cf3a862 4e4a00c -- docs/01-plan/features/doc-block-exec.spec.md` is empty) — a
premise stated with the command that would falsify it, since "the sibling moved" is exactly the kind
of carried claim this feature's rounds have already got wrong in both directions. **Every label here is a past-tense sha and none of them describes the
commit the reader is standing in**: a sibling-derived census can
only ever be stamped at a *landed* commit, and when all four documents move together the commit a
revision lands in is by construction not the commit its sibling figures were read at, so any
present-tense self-description goes false the moment the revision lands — v1.93 carried one and it
did. The sha is the label; there is nothing for prose to add. The units are
*occurrences of a line-opening command token* and
*distinct such tokens*, both from that one command; neither is a count of fenced blocks.
**`awk` ×1 at all three**, so the conclusion the needle rests on survived both moves: a new `awk` fence
there is still the one edit that breaks it, and the census moving while the conclusion did not is
why the two are stated separately. This is the hazard named two sentences above — a sibling
revised in the same commit that audits this one — realised rather than hypothetical, so the census
is re-derived at every freeze and never carried. This plan is also the only document of the
four that attributes to that enumeration: `grep -cE '^  \$ awk '` over
`docs/02-design/features/doc-block-exec.design.md` and
`docs/01-plan/features/doc-block-exec.impl-plan.md` returns **0** on each at `6f0ee85`, at
`cf3a862` and again at the freeze `4e4a00c`, where the same grep on the spec returns **1** at all
three.

Its hit count is deliberately **not** stated here: it is a procedure rather than a measurement, and
any edit to this document changes it, so a number would falsify itself every cycle. Controls are
published instead, since a filter whose output is not published must be shown to discriminate some
other way. Every leg below was first run at `6f0ee85` **by v1.93**, since every one of them depends
either on this document or on the spec, and the closure above reaches neither. **v1.94 through
v1.100 have none of them re-run these legs; six of the seven say so at their own entries and
v1.100 is silent, which is derivable and not recalled** —
`awk '/^## Version History/{f=1} f && /^- v/{n=$2} f && /screen-two leg/{print n}'` over this
document returns every entry from `v1.94` to `v1.99`, plus this revision's own, and **no
`v1.100`** — so the one revision that did not name them is the one immediately before this. The
`v1.101` hit is this revision's entry and is stated so the reader is not left to wonder whether the
command has a self-match: it does, by construction, and the load-bearing reading is the absence. **Silence is the failure mode the naming
exists to prevent**, and it is recorded here rather than smoothed over. The two spec
locators in this section are re-derived on the surfaces that state them — at `4e4a00c` by v1.95 and
v1.96, at `7d8e797` by v1.97, at `1cbddb7` by v1.98 and at `b3be433` by v1.101, returning **1** at every one — and
the **six**
screen-two legs below — the `335f535` positive, the true-negative leg (two declined sentences, one
leg), the blind form, the over-reach, the **multi-word-gap** leg (the "three importing test files"
sentence declined by the spec's block as `74e126f` held it and returned by the form the same block
holds at `6f0ee85`) and the **cardinal-alternation** leg (`printf 'zero files\n'` returning nothing
while `printf 'one file\n'` matches) — were carried at `6f0ee85` through v1.100 and are
**re-executed at `b3be433` by v1.101**, all six reproducing, which is what takes them out of the
inherited-unverified register for this revision only. The re-run is against the spec's block **as
it ships at `b3be433`** and not against the `6f0ee85` form, which is the point of doing it: the
paragraph below records that this checker has already moved once. **The cardinal is six because the section below was walked and its stamped legs counted,
not because the previous revision's four was carried**: through v1.95 this clause said four and
left the last two — both stated below with a `6f0ee85` stamp and neither re-run — outside the
closure and outside the register at once, which the register says cannot happen. This is the third
member of the population-short-by-N shape and the reason it is now a rule there rather than a third
instance repair. They are all named here
because the alternative is silence, and silence reads as verification. **One thing carried with
them that a later reader should not have to rediscover**: the spec's enumeration itself moved
between `6f0ee85` and `68a70d6` — its closing noun alternation gained `lines?|pins?`
(`git show 6f0ee85:<spec>` versus `git show 68a70d6:<spec>`, the block addressed by
`grep -cE '^  \$ awk '`) — so "carried at `6f0ee85`" is carried against a checker that is no longer
byte-identical, which makes re-running the six at a later freeze worth more than the register's
wording alone suggests.

**Positive — a real member of this document, and the screen prints it.** The scripts-directory
count as `335f535` wrote it, a bare `37` with the adverb the provenance rule forbids and no sha, is
returned when the enumeration is run against
`git show 335f535:docs/01-plan/features/doc-block-exec.plan.md`; the line it prints reads, at `335f535`, `` `h-mad/scripts/*.py` is 37 files today; `` — quoted as data, which is why the sha shares its line.

**True negative — a non-member the screen declines**, and deliberately one carrying a noun from the
closing alternation, so the decline costs the screen something: `Shell mode belongs on the fence,
not in the caller.`, verbatim from §Architecture Considerations, states no count and is **not**
returned. `The tag is the security boundary.`, from the same section, is likewise declined.

**A blind form, named as such rather than offered as the negative.** The same scripts-directory
claim as this body now writes it — `ls h-mad/scripts/*.py | wc -l` → **37** at `335f535` — is also
not returned, and **provenance plays no part in that**: the enumeration is a `grep -Ei` over an
`awk`-numbered body and has no sha stage anywhere in it. Fed the same sentence with the counted
noun restored and the sha left in place, it **matches**. What filters the live form is the
counted-noun shape — `**37** at` puts no noun of the closing alternation within the allowed gap of
the cardinal — so this is a **false negative** of the screen, evidence of incompleteness, and
citing it as "the negative" (as this paragraph did through v1.91) inverts the meaning of the
control. Provenance on this document is **screen one's** job, through its marker plus the
`!/[0-9a-f]{7}/` reading; screen two finds counted nouns and its output is then read by a human.

**The two screens share one blind spot, and it is this exact shape.** Screen one fires only on a
marker word; screen two fires only on a cardinal with a noun of its alternation nearby. A claim
written `→ **37** at`, carrying no marker word, no adjacent noun and no sha, is reachable by
**neither** — and that is the shape the live scripts-directory sentence takes. It is compliant only
because it carries its command and its sha by hand, not because a screen would have caught it
otherwise. Neither screen is a gate; both are aids to a human reading the body, and the provenance
rule at the head of this section is what actually binds.

**One over-reach, measured on this body rather than reasoned:** `Refusal is the default response to
anything unmeasured.` **is** returned, because the case-insensitive `measured` alternative matches
as a substring inside `unmeasured`. That sentence states no count. It is the cost a shape filter
pays for reach, and the reason its output is read line by line rather than counted. **This
over-reach is screen two's and stays screen two's**: it is a `grep -Ei` with no boundary stage, and
the v1.93 widening of screen one did not create it and does not remove it — screen one declines
`unmeasured` by construction, because `n` is an alnum character and its leading boundary refuses
one, which the fixture above shows directly. Two screens, two behaviours on the same sentence, and
saying so is cheaper than a later reader deciding one of them is broken.

**Residual on both screens, stated so the next sweep is checkable rather than trusted.** Each is a
*shape* filter and never a verdict, and each tests for a sha on the **same line**, so a claim whose
sha sits in the same sentence wrapped onto the next line reads as a hit and must be **read**, not
counted.

**Screen two's own residual enumeration belongs to the document that owns the checker, and is not
restated here** — a sibling can be revised in the same commit that audits this one, so a sentence
saying what it currently lists is false the moment that happens, and this paragraph made exactly
that mistake through v1.91. The address is
`grep -c 'Residual on the enumeration itself' docs/01-plan/features/doc-block-exec.spec.md` → **1**
at `6f0ee85`, **1** at `cf3a862` and **1** at the freeze `4e4a00c`. What is recorded here is only what running the checker against **this** body measured,
which is this document's own fact:

- **The multi-word gap no longer misses a member of this document, and that changed under this
  document's feet.** The re-derivation paragraph above reads "three importing test files". Fed to
  the `grep -Ei` half as the spec's fenced block held it at `74e126f`
  (`git show 74e126f:docs/01-plan/features/doc-block-exec.spec.md`) it is **not** returned; fed to
  the form the same block holds at `6f0ee85` it **is**. So the miss this plan reported through
  v1.91 was real when written and is closed at the freeze sha — closed by the spec author in commit
  `0aac0b7`, not by a report from here, which is why "reported to the spec author rather than
  patched here" no longer describes what happened and is gone.
- **The cardinal alternation still declines `zero`, and this half of the v1.91 residual stands.**
  At `6f0ee85`, `printf 'zero files\n'` fed to the `grep -Ei` half returns nothing while
  `printf 'one file\n'` matches. An absence claim written as "zero …" is therefore invisible to
  screen two and has to be caught by screen one or by reading.
- **The line-break miss stands**, and it is the first residual above: `grep` is line-scoped and
  this document hard-wraps, so the claim that wrapped across a newline missed for that reason
  independently of the other two. **This bullet is a third reason the first bullet's member was
  missed, not a seventh screen-two leg** — it carries no command and no fixture, and it names the
  same sentence ("three importing test files") the multi-word-gap bullet names, so a reader walking
  this section to check the cardinal **six** must not count it. Said in words rather than left to
  inference, because a reader re-walking the six had to reconstruct it from the closing line below.

One member missed in three different ways at once is the argument for reading hits rather than
counting them, and for re-running both screens at every freeze — decision F binds the
enumeration exactly as it binds the needle that addresses it.

**A reading is a reading *of a screen*, and the screen changed, so the two eras are stated
separately and never as one series.** Through v1.92 this section published a triple by the
v1.91-repaired screen — **21** lines over `git show 335f535:docs/01-plan/features/doc-block-exec.plan.md`,
**18** over the v1.90 body as `74e126f` shipped it, **9** over the v1.91 body as `35698f9` shipped
it — and that triple is historically correct and is left as written. It is **not** comparable to
anything below it: the v1.92 screen could not see a marker that was not followed by a comma or a
closing paren, so its numbers are readings by a filter now known to be partial, exactly as the
v1.90 pair (six lines then four) was superseded by it for the same reason one revision earlier.
Two supersessions on one screen in three revisions is itself the argument for stating the reading
and the screen together, always.

**The current reading, by the v1.93 screen, over the v1.92 body as `6f0ee85` shipped it.** Both
programs run over `git show 6f0ee85:docs/01-plan/features/doc-block-exec.plan.md`, so either is
reproducible without a working tree: the v1.92 screen returns **9** body lines and the v1.93 screen
returns **32**. The **23** in the gap had never been read. They are triaged by **category**, not by
line number, because line numbers go stale and categories do not, and the five categories partition
all **32** — every line lands in exactly one, and the five counts sum to 32, which is the check
that no line was quietly dropped:

- **9 — permanent self-matches.** The provenance-rule sentence, the screen's own command line, the
  boundary-probe fixture line, and the paragraphs that quote the old and new marker forms. All nine
  quote the markers as *data* and will match for as long as the rule is stated at all.
- **8 — a marker word with no tree count, ordinal or absence anywhere in the sentence.** What a
  cannot-judge verdict line may carry; what MUST be re-measured at 5c; a narration of a past
  failure to re-measure. This is the over-reach a shape filter pays for reach, and the reason its
  output is read rather than counted.
- **5 — references to OS- or interpreter-behaviour probes recorded in full below**, under the
  carve-out stated at the end of this section, which the same revision narrowed and re-swept.
- **5 — claims whose command and sha sit on the surface that owns them**, reached either by an
  explicit pointer (the Risks row that says "measured under §Measurements") or by the same sentence
  wrapping onto the next line, which is the first residual below and the reason hits are read.
- **5 — actual members, every one repaired in this revision.** All five are provenance defects on
  claims that are factually true, and **all five sat in the 23**: not one of them was in the nine
  the v1.92 screen printed, which is the measurement that makes the boundary repair load-bearing
  rather than tidy. They are: the
  5f wrapper probe stamped with a calendar date under a carve-out its subject does not qualify for;
  the collected count taken from `h-mad/` as cwd, which carried no sha at all; the mutation-spec
  split introduced by "Today", a count derived from a sibling under `docs/`; the fence-grammar
  cell's "measured on both renderers" with no renderer version on it; and the fixture-preamble
  paragraph, which points at the spec's AC-3.11 and then restates the result anyway.

**Re-run both screens at the commit that lands each revision, and read the delta.** No reading of
the v1.93 body this revision writes is published here, because that body is readable at no commit
until it lands and a working-tree count carries no sha the next reader can check. Every reading
above moves on any edit to this document by construction, so each is a reading of a commit and
never a standing property.

**The obligation was un-discharged for two consecutive revisions and is discharged here, with the
delta read rather than the count published as a result.** Neither v1.99's nor v1.100's Version
History records running either screen. Run at `b3be433`, screen one's published program returns
**92** body lines, against **84** at `1cbddb7` and at `700c599` and **92** at `8c6539a` — so the
**+8** landed with v1.99 and v1.100 added none. **The 92 is not itself a finding and is not a
count of defects**: this section states that screen one's hits are read and never counted, its
`[Mm]easured` branch matches this document's own prose by design, and the discriminating stage is
the `!/[0-9a-f]{7}/` co-occurrence filter. What the obligation exists to prevent is exactly what
happened — **sixty lines accumulated across the v1.93→v1.99 span with no round reading them**, the
last published triage being over the `6f0ee85` body where the program returned **32**. **The eight
v1.99 added were read line by line rather than counted**, isolated with
`diff <(<program> 700c599) <(<program> 8c6539a) | grep '^>'`, and all eight are **hard-wrapped
continuation lines of sentences whose subject is measurement itself** — "set-equal to the measured
survivors", "run at the freeze, per branch, with its controls and its measured blind", "measured
after this revision's last edit", "committed inside a `measured:` citation", "Measured … differ
between `awk` and any `splitlines()`-based reader", "measured at two commits into one table",
"the freeze this revision is measured at", "measured on the surface screen and is stated rather
than hidden". Not one is an un-stamped provenance claim; every one is either the screen matching
this document's own prose about screens, or the first residual below — a sha sitting on the
adjacent line of a hard-wrapped sentence. **That is a reading, not a clean bill**: the residual it
rests on is the residual this section already publishes, and it is the reason the obligation is to
read the delta and never to compare two totals. The ALL-CAPS control still holds and still returns its own text:
`grep -cE '(^|[^[:alnum:]_])(MEASURED|TODAY|THIS SESSION)([^[:alnum:]_]|$)'` over the body at
`b3be433` returns **3**, all three the control's own fixture written into this section, while the
same grep fed `printf 'stamped TODAY with no sha\n'` returns **1**.

**Screen two was re-run at `b3be433` too, and all six of its legs with it** — against the spec's
enumeration *as the spec ships it at `b3be433`*, which matters because that enumeration has moved
once before under this document's feet. The line-anchored address the spec designates,
`grep -cE '^  \$ awk '`, returns **1** on the spec at `6f0ee85`, `1cbddb7`, `700c599`, `8c6539a`
and `b3be433`, and **0** on the design and the impl-plan at `b3be433`, so the address still
resolves to one block. Run over this document's body with only the path substituted, the
enumeration returns **122** lines at `6f0ee85`, **225** at `1cbddb7`, **228** at `700c599`, **262**
at `8c6539a` and **271** at `b3be433` — published as a delta and **not** as a measurement of
anything, for the reason this section already gives: screen two's hit count is a procedure, any
edit moves it, and a number stated as a property would falsify itself every cycle. The six legs
each reproduced at `b3be433`, and the outputs are at their own sites: the `335f535` positive
returns its line, the two true negatives return nothing, the blind form returns nothing while the
same sentence with the counted noun restored returns one, the over-reach returns its one line,
`three importing test files` is declined by the `74e126f` form of the block and returned by the
`b3be433` form, and `printf 'zero files\n'` returns nothing while `printf 'one file\n'` matches.
`grep -c 'Residual on the enumeration itself'` on the spec returns **1** at `b3be433`, as at the
four earlier shas. **They therefore leave the inherited-unverified register for v1.101 and re-enter
at the next revision that does not re-run them**, which is the rule that register now states.

Deliberately out of class, by construction rather than by exception: Version History entries,
which record their own era's numbers and are excluded by the `exit`; design-derived counts of
artifacts that do **not exist yet** (`29` names, `81` mutations, `8` rows), which are contract
values this plan must match rather than tree measurements; and OS- or interpreter-behaviour probes,
which are stamped with their interpreter and platform in the recorded probe output
(`python: 3.11.8 | darwin`) instead of with a sha.

**The probe carve-out is narrower than "it is behaviour", and v1.93 narrowed it after the wider
wording licensed a false exemption.** Through v1.92 the carve-out read "which no repository sha
determines" and listed the `timeout` wrapper's `124` beside `killpg`. That premise is false for the
wrapper: `hmad-dispatch` is **tracked repository code**, not OS behaviour —
`git ls-files h-mad/bin/hmad-dispatch h-mad/scripts/hmad-dispatch.sh` returns both paths at
`6f0ee85` — and `3f50b95`, dated 2026-09-04 and titled "make rc=124 legible", landed on the exact
behaviour the probe measures **one day after** the calendar date it was stamped with
(`git log --oneline -2 -- h-mad/bin/hmad-dispatch h-mad/scripts/hmad-dispatch.sh` →
`3f50b95` and `bea1b60`, "the wrapper tore its own read"). The rule over the axis:

> **A probe carries a sha whenever the thing whose behaviour it measures is a tracked repository
> artifact. The carve-out is for behaviour determined entirely outside this repository — the OS,
> the kernel, the language runtime, or a third-party package this repository does not vendor.**
> Naming the determining thing is part of the claim; if it is not named, the exemption is not
> established.

**The list in that rule is a gloss on the test, not a second condition, and v1.94 says so because
the narrower v1.93 wording ("the OS, the kernel or the language runtime") had no room for a probe
whose subject is a third-party renderer.** `git ls-files <the artifact the probe names>` is the
whole test. What exempts the markdown-it-py grammar corpus is the same property that exempts
`argparse` — nothing in this tree determines the behaviour, so no sha of this tree can date it, and
a version stamp is what stands in for the sha. Enumerating *kinds* of outside-thing invites the
next kind to be argued about; the test does not care what kind it is.

**The test is one command and its residual is that no screen can run it for you**:
`git ls-files <the artifact the probe names>` — non-empty means the probe needs a sha. A shape
filter cannot apply it, because deciding *what* a probe's subject is requires reading the probe.
So the carve-out population is swept by hand, and the sweep is published rather than asserted.

**v1.93 published this table as a complete population — "five members, all five checked" — and it
was two members short, because the sweep was driven by recall.** The rule over the population, which
is what v1.94 actually adds: **every probe in this document that is stamped with a version or a
platform instead of a sha is a row in this table**, and the sweep is driven by **the stamp**, not by
which probes an author remembers or an audit names. Under that rule two members fall out
immediately — the `awk` boundary probe of §Measurements above, whose stamp is `awk version
20200816`, and the markdown-it-py grammar corpus under §Measurements, stamped `2.2.0` and `4.2.0`.
Both are genuinely exempt, so the v1.93 *verdict* was right and its *sweep* was not; a completeness
claim is a measurement under the provenance rule, and this one had not been measured.

The stamp-driven driver, run over the body at `cf3a862` — before this revision's edit, since the
rows it produces are written into the corpus it scans:

```
$ git show cf3a862:docs/01-plan/features/doc-block-exec.plan.md \
    | awk '/^## Version History/{exit}{print}' \
    | grep -cE '(python3?[.:]? ?[0-9]+\.[0-9]+\.[0-9]+|awk version [0-9]|markdown-it-py [0-9])'
13
```

Those 13 lines resolve to **seven** distinct probes — the five v1.93 listed, plus the two above —
because a probe's stamp appears both on its table row and in its recorded output. The mapping is a
hand read, which is the point: the grep finds candidate stamps, and deciding which probe a stamp
belongs to still requires reading the probe.

**That driver shipped in v1.94 with no control of any kind — not positive, not negative, not
per-branch — so its `13` supported nothing, and it is a three-branch alternation.** Per-branch over
the same body at `cf3a862`: the python-version branch **10**, `awk version [0-9]` **2**,
`markdown-it-py [0-9]` **1**, summing to the published 13 with no line matching two branches. **The
number drifts by construction and is therefore also given at the freeze**: over the body at
`4e4a00c` — that is, the v1.94 body, which added the table and its prose — the same three branches
read **10**, **4**, **3**, union **17**. Neither number is a property of the feature; both are
readings of a document that grows, which is why the sweep obligation lives in the rule above and
not in an integer. The three branches are fired against one fixture, positives and negatives
together:

```
$ printf 'stamped python 3.11.8 darwin\nstamped python: 3.11.8 | darwin\nstamped awk version 20200816\nstamped markdown-it-py 2.2.0\nstamped darwin, no version digits\nmeasured 2026-09-03\n' \
    | grep -nE '(python3?[.:]? ?[0-9]+\.[0-9]+\.[0-9]+|awk version [0-9]|markdown-it-py [0-9])'
1:stamped python 3.11.8 darwin
2:stamped python: 3.11.8 | darwin
3:stamped awk version 20200816
4:stamped markdown-it-py 2.2.0
```

Run one branch at a time the readings are python-version **2** (both spellings, bare and colon),
`awk version` **1**, `markdown-it-py` **1**, so every branch is shown to fire; and lines 5 and 6 are
the negatives, which are exactly the driver's two blind spots and are both declined.

**Seven members at `cf3a862`, each checked with its own command, and the argument is in the row so
the row is runnable without scrolling up**:

| Probe | `git ls-files` argument | Result | Verdict |
|---|---|---|---|
| argparse's `exit_on_error` routing (§Scope) | `git ls-files argparse` | empty | exempt; stamped `python 3.11.8` |
| The `awk` boundary probe (§Measurements, screen one) | `git ls-files awk` | empty | exempt; stamped `awk version 20200816` |
| Group kill and escape (AC-5.2) | `git ls-files os.py signal.py` | empty | exempt; **was missing its platform line and ran under `python3` — repaired below** |
| `shutil.rmtree` on a `0o000` directory (AC-3.14) | `git ls-files shutil.py` | empty | exempt; stamped `python: 3.11.8 \| darwin` |
| Reader-less FIFO `O_NONBLOCK` (AC-3.10) | `git ls-files os.py` | empty | exempt; stamped `python 3.11.8 darwin` |
| Naturally emptied group (AC-5.5) | `git ls-files os.py signal.py` | empty | exempt; stamped `python 3.11.8 darwin` |
| Scanner grammar corpus (§Measurements) | `git ls-files markdown_it markdown-it-py` | empty | exempt; stamped `markdown-it-py 2.2.0` and `4.2.0` |
| The `run --timeout` wrapper's `124` (the 5f bound under §Success Criteria) | `git ls-files h-mad/bin/hmad-dispatch h-mad/scripts/hmad-dispatch.sh` | **two paths** | **not exempt — carries a sha, below** |

The table is eight rows because the wrapper is listed with the seven it does not belong among; that
is the point of publishing it. **The argument column is not cosmetic**: through v1.93 the middle
column held the probe's *subject* rather than the command's *argument*, and the wrapper row read
`h-mad/bin/hmad-dispatch` beside the result "two paths" — an audit at `cf3a862` ran the single-path
form the cell named, got one path, and filed the row as false. The verdict was right and the cell
was unrunnable; a result cell whose command is stated three paragraphs away is a result nobody can
reproduce.

Three residuals, and none is closed:
- **A probe stamped with a PLATFORM and no version digits is invisible to the driver above**, and
  the rule it implements admits exactly that stamp — "a version **or a platform** instead of a
  sha". The driver has no platform branch: `printf 'exempt; stamped darwin\n'` fed to the published
  `grep -cE` returns **0**, the fifth line of the fixture above. So a probe stamped `darwin` or
  `linux` alone is missed for the same structural reason the calendar date is, and v1.94 stated
  only one of the two gaps — the rule sentence and the program maintained as two independent pieces
  of prose, which is the drift this document already names for screen one, recurring on the new
  driver. Every current member happens to carry version digits beside its platform (`python 3.11.8
  darwin`), so the gap has not yet cost anything; that is a property of the present population and
  not of the driver.
- **A probe stamped with a calendar date is invisible to the driver above**, which greps for
  version strings only. The wrapper row is the proof — the stamp it carried was
  `measured 2026-09-03`, a calendar date, still readable at
  `git show 6f0ee85:docs/01-plan/features/doc-block-exec.plan.md | grep -n '2026-09-0'` → one hit,
  and no version grep would find it. That member was caught by reading, not by the
  driver, and the driver is an aid to the hand sweep rather than a replacement for it.
- The sweep is a snapshot of the probes this document carries at `cf3a862`. A probe added later is
  caught only by a reader running the driver and then `git ls-files` on each subject, so the
  obligation lives in the rule above rather than in the integer seven.

**The fence census — 73 at `a8e0372`, and the number is inseparable from the commit.** Every
surface of this document that states it (§Scope, §Out-of-Scope, the Risks row above) carries the
same sha, because the value moves with any documentation edit under the two roots and has already
moved once: it was **68** at `a469493` and at `1861157`, and is **73** at `a8e0372`. Counted over
`h-mad/` and `handoff/`, excluding `archive/`, matching
opening fences only (a line *starting* ` ```bash `, so a closing fence or an indented mention is
not counted). Tests and hidden files are **not** excluded — a broad grep re-run by a reviewer will
therefore agree with this number:

```
$ python3 - <<'PY'
from pathlib import Path
tot=0; files=0
for p in sorted(Path('.').glob('*/**/*.md')):
    if 'archive' in p.parts or p.parts[0] not in ('h-mad','handoff'): continue
    n=sum(1 for l in p.read_text(encoding='utf-8',errors='replace').split('\n')
          if l.startswith('```bash'))
    if n: tot+=n; files+=1
print(f"bash fences: {tot} across {files} files")
PY
bash fences: 73 across 10 files
```

Control, to show the counter is not under-matching — the same sweep counting opening fences of
*every* language must return a strictly larger number, and does: **88** at `a8e0372`, re-run and
still **73 across 10 files** / **88** at `335f535`, at `35698f9`, at `cf3a862`, and again at the freeze **`4e4a00c`** — the number and its sha kept on one physical line each, because a hard wrap that
puts `73`/`88` on one line and its sha on the next is the line-scoping hazard this document states
elsewhere as its reason for the rule, and the v1.94 re-stamp reintroduced it here
(**83** at `a469493`/`1861157`) — the same script with the counting line replaced by
`if l.startswith('```') and len(l) > 3 and l[3].isalpha()` (an opener with any language word). The
freeze-sha re-run is recorded because both figures are stamped at commits *older* than `74e126f`,
which the closure in the preamble does not reach **and cannot be made to reach by extending its
right-hand side** — extending the interval moves its end, not its start, so the only thing that
re-verifies an older-stamped figure is running it again, which is what this sentence records.

**This census is corpus-invariant, and that was measured rather than assumed — re-measured at
`a8e0372`, not carried.** The script above walks a filesystem glob, which returns more `*.md`
files than the tracked corpus §Scanning defines (35 against 30 at the freeze `4e4a00c`, at
`cf3a862` and at `a8e0372`;
30 against 25 at
`1861157` — the pair moved because `6db8e50` added five `h-mad/agents/*.md`, verified with
`git diff-tree --no-commit-id --name-only -r --diff-filter=A 6db8e50 -- h-mad/agents` → 5, which is
the addition-scoped form; the tracked-versus-glob bullet later in this section owns the reason the
plainer `--stat` form does not answer this claim, and this sentence points at it rather than
restating it). Run at `a8e0372` over **both** corpora: `73 across 10 files`, control
`88`, **identical on each**, and identical again at `1861157` at `68`/`83`. The reason holds
independently of either number: the `.pytest_cache/README.md` artifacts under the two roots carry
no fence at all (`find h-mad handoff -name README.md -path '*pytest_cache*'` → **5** files at `74e126f`,
and `grep -c '^```' ` on each → `0` at `74e126f`; the sweep is scoped to `h-mad` and `handoff`
because a repository-root run also returns `./.pytest_cache/README.md`, which is outside the
corpus §Scanning defines and would contradict the tracked/glob arithmetic above),
and neither do the five new agent documents (`grep -c '^```bash' h-mad/agents/*.md` → `0` on each
at `a8e0372`), so unlike the heading counts this one never depended on which corpus was walked.
Residual: invariance is a property of the *current* extra files, not a theorem — a future untracked
or generated `.md` under the two roots that does carry a bash fence would break it, so the two-corpus
run is part of the re-measurement, not a one-off.

**AC-6.1's tree sweep is deliberately NOT this filter, and must not be harmonised with it.** The
spec **spells AC-6.1's sweep out in full rather than reaching it by reference** — spec v1.55,
AC-6.1: `*.md` files under `h-mad/` and `handoff/`, excluding any `archive/` path and any
dot-directory. Both greps re-run in this revision at the freeze `4e4a00c` — one hit and none,
unchanged from `cf3a862` and `6f0ee85` — because the closure above does not
reach a sibling under `docs/`:
`grep -n 'stated here rather than by reference' docs/01-plan/features/doc-block-exec.spec.md`
returns one hit and `grep -n 'same sweep as the plan' docs/01-plan/features/doc-block-exec.spec.md`
returns none — an earlier revision of this paragraph asserted the reference and quoted "the same
sweep as the plan's fence census" as the spec's wording; `git log -S` shows that phrase left the
spec at `b68ef48`, the very commit that produced plan v1.86, so the premise was stale the moment it
was written. The conclusion it supported is unaffected and is *why the paragraph stays*: the two
realisations differ on purpose, and each document must be able to state that alone, since a reader
who harmonises them breaks the guard. The
census is a one-off human measurement and may use `git ls-files`, but AC-6.1's sweep is a **test**
that must still count a newly written, not-yet-tracked `.md` under the two roots — precisely the
document a `git ls-files` sweep would miss and the guard exists to catch. It therefore excludes
build output by excluding any path with a **dot-directory component** instead (design v1.93
§AC-6.1). Two realisations of one exclusion, on purpose.

**The census must be run from the repository root, and a subdirectory run silently returns a
different number.** At `a469493` from the root it was `68 across 10 files`, control `83`; at
`a8e0372` it is `73`/`88` (above). A plan audit reported `49 across 2 files` (27 in `h-mad/SKILL.md`, 22 in
`handoff/SKILL.md`); that is the count the script returns when run from a **subdirectory**, where
`p.parts[0]` is no longer `h-mad`/`handoff` for the nested references and only the two top-level
`SKILL.md` files survive the filter. The script is correct from the root, which is where its
`Path('.')` assumes it runs; a reviewer re-running it must do so from the root.

**The extractor census — 2, re-run at the freeze `4e4a00c`.** The consumers that would break when a
fence is tagged — the narrow census returns the same **2** hits at `4e4a00c` as at `cf3a862`,
`35698f9`, `a8e0372` and
`1861157`, and the two line numbers below are its command's own **output**, reproduced verbatim
rather than transcribed, which is why they are not pins and are exempt from the shape grep under
§Implementation Strategy. **Its corpus is `.` — the whole repository, not the two roots — so the
§Measurements closure does not reach it and its stamp rests on nothing but this re-run**, which is
the same defect v1.93 repaired for the three `h-mad`/`handoff` censuses and left standing on this
one, one paragraph above the sentence that states the caveat for its sibling grep.

**The census pattern is a three-branch alternation, and two of its branches had never been shown to
fire.** Per-branch at the freeze, in **matching lines** (not files — the file-count form reads `1`
for a branch with two hits and mixing the two units beside one figure is its own defect):
`git grep -nE '<branch>' 4e4a00c -- '*.py' | wc -l` gives `findall.*```bash` **2**,
`split.*```bash` **0**, `re\.compile.*```bash` **0**, union **2** — so both hits come from the
`findall` branch alone and the paragraph's "the consumers that would break" claim rested on a
pattern two thirds of which had never been observed alive. The alternation-level control below
(**24** `.py` files carrying a fence literal of any language) is an *under-matching* check on the
whole pattern and is not evidence about any branch. Each branch is therefore fired against its own
fixture:

```
$ printf 'a = re.findall(r"```bash\\n(.*?)```", s)\nb = s.split("```bash")\nc = re.compile(r"```bash")\nd = re.findall(r"(?m)^# ", s)\ne = s.split(",")\nf = re.compile(r"^AC-")\n' \
    | grep -nE 'findall.*```bash|split.*```bash|re\.compile.*```bash'
1:a = re.findall(r"```bash\n(.*?)```", s)
2:b = s.split("```bash")
3:c = re.compile(r"```bash")
```

Run one branch at a time over that fixture — `grep -cE 'findall.*```bash'` and the same for the
other two — each returns **1**, so all three branches fire; and lines 4–6 are the negatives, the
same three verbs with no fence literal, every one declined. The three zeros over `*.py` are
therefore an absence in the tree, not a dead branch. **By construction this fixture writes all three
branch shapes into this document**, which is why every per-branch reading here is taken from
`git grep … 4e4a00c -- '*.py'` — a corpus that excludes `docs/` entirely — rather than from a body
scan.

**The sweep for the provenance class is driven off the command's CORPUS, not off its spelling**, and
v1.94's driver was driven off the spelling: `grep -oE "grep -r[a-z]* '[^']*' --include='\*\.py' \."`
finds only the `grep -r … --include` form, so a `git grep … -- '*.py'` census with no `--include`
was invisible to it, and one — the **24**/**4** control below — sat outside the closure with a
stale stamp for four revisions. The driver is now the corpus shape, a three-branch alternation of
its own, read over the body at `4e4a00c`:

```
$ git show 4e4a00c:docs/01-plan/features/doc-block-exec.plan.md \
    | awk '/^## Version History/{exit}{print NR": "$0}' \
    | grep -nE "\-\-include='\*\.py'|\-\- '\*\.py'|ls-files '[^']*\*\.py'"
```

Per-branch at `4e4a00c`: `--include='*.py'` **5**, `-- '*.py'` **4**, `ls-files '…*.py'` **2**,
union **11**. Read by hand rather than counted, the eleven partition by corpus: **two** are the
`docsections` import censuses over `h-mad handoff`, which the closure does reach; **six** are
repo-wide (`.` or an unrestricted `-- '*.py'`) — this census, the broad bare-literal grep, the
per-file split, their two `git grep` cross-checks, and the `git ls-files '*.py'` scale figure — and
every one is re-derived at `4e4a00c` on the surface that states it; **two** are the **24**/**4**
control, likewise repo-wide, now re-stamped below; and **one** is
`git ls-files 'h-mad/scripts/*.py'` under §Success Criteria, whose corpus is inside `h-mad/` but
whose stamp `335f535` is *older* than the closure's left edge, so it is re-run there too.
**Residual, and it is why the driver is an aid and not a gate**: an alternation can be spelled as
two greps in a pipe or as two commands in adjacent sentences, and no shape screen over `(a|b|c)`
sees either form — as this very driver's own three branches show, the shape has to be written the
way the screen expects or the member is missed. **Second residual, by construction**: this paragraph
writes all three branch shapes into the body, so a post-edit run returns more than eleven and the
surplus is this paragraph's own text — which is why the reading is stamped `4e4a00c` and why the
next revision re-runs it at its own freeze rather than comparing against the eleven.

```
$ grep -rn 'findall.*```bash\|split.*```bash\|re\.compile.*```bash' --include='*.py' .
./h-mad/tests/test_h_mad_collect_report_docs.py:270:    blocks = re.findall(r"```bash\n(.*?)```", section, re.S)
./h-mad/tests/test_h_mad_collect_report_docs.py:412:        (b for b in re.findall(r"```bash\n(.*?)```", section, re.S) if "exec codex" in b),
```

A broader grep for the bare literal — `grep -rn '```bash' --include='*.py' .` —
returns **6** at the freeze `4e4a00c`, **6** at `cf3a862` and **6** at `6f0ee85` (it returned five
at `1861157`). **This corpus is
the whole repository, not the two roots**, so the §Measurements closure does not reach it —
`git ls-files '*.py' | grep -vcE '^(h-mad|handoff)/'` → **411** at `6f0ee85`, **411** at
`cf3a862` and **411** at `4e4a00c` — and it is re-derived on this surface at every
freeze instead. **`grep -r .` also walks untracked and generated files, which the tracked
form cannot**, so both censuses are cross-checked against a sha-addressable command that excludes
them: `git grep -nE 'findall.*```bash|split.*```bash|re\.compile.*```bash' 4e4a00c -- '*.py'` → the
same **2**, and `git grep -nE '```bash' 4e4a00c -- '*.py'` → the same **6**. The two forms agreeing
is what licenses reading the `grep -r` output as a statement about the repository rather than about
one working tree; if they ever disagree, the `git grep` form is the one with a sha on it.

**That last sentence is a property claim about the two commands, so it is EXECUTED rather than
argued** — the failure this document keeps hitting is a mechanism that works while its
self-description is wrong. The thing the tracked form claims immunity from is an untracked file, so
one was created, both forms were run, and it was removed again:

```
$ printf 'x = "```bash"\n' > ./_q_untracked_probe.py    # untracked; `git status --porcelain` shows `?? _q_untracked_probe.py`
$ grep -rn '```bash' --include='*.py' . | wc -l ; git grep -n '```bash' -- '*.py' | wc -l
7
6
$ rm -f ./_q_untracked_probe.py
$ grep -rn '```bash' --include='*.py' . | wc -l ; git grep -n '```bash' -- '*.py' | wc -l
6
6
```

The `grep -r` form moved 6 → 7 and back; the `git grep` form did not move at all, and
`git grep -n '```bash' 4e4a00c -- '*.py' | wc -l` is **6** throughout. So the immunity is measured,
not asserted, and the probe file is gone — the last two lines are the read-back that says so.
Digits,
and on one physical line with
its sha: the English-word form split its number from its sha across the wrap, where `grep` is
line-scoped and cannot see either half of the pair, and a digits-only staleness sweep cannot see a
count spelled as a word at all. The per-file split, by
`grep -rc '```bash' --include='*.py' . | grep -v ':0$'`, re-run at the freeze `4e4a00c` and
unchanged from `cf3a862`:
`h-mad/scripts/h_mad_precheck_doc.py` 1, `h-mad/tests/test_docsections.py` 1,
`h-mad/tests/test_h_mad_assemble_tdd.py` 2, `h-mad/tests/test_h_mad_collect_report_docs.py` 2 —
the last pair being the two extractors above. The four that are not extractors are the one inline
fixture string in `test_docsections.py`, the two in `test_h_mad_assemble_tdd.py`, and a prose
comment in `h_mad_precheck_doc.py` that quotes the literal while describing a document. None of the
four extracts anything. Control —
**the command, not just the number**, because this was the one figure in this plan carried without
one, and that is what let it drift unnoticed:

```
$ git grep -l '```' 4e4a00c -- '*.py' | wc -l
24
```

**24** `.py` files contain **a fence literal of any language** at the freeze `4e4a00c`, re-run here
and unchanged from `cf3a862`, `6f0ee85`, `35698f9` and `a8e0372` (**23** at `1861157`;
the quantity is deliberately the broad one — `git grep -l '```bash' 4e4a00c -- '*.py' | wc -l`
returns
**4** at `4e4a00c`, `cf3a862`, `6f0ee85`, `35698f9` and `a8e0372`, and **3** at `1861157`, the *bash* fence literal, a different and narrower
measurement, and either serves the argument, so the one meant is named). So the narrow pattern is
not under-matching. **Its corpus is the whole repository, not the two roots**, so the
§Measurements closure does not reach it — at `4e4a00c`, **5** of the 24 sit outside `h-mad/` and
`handoff/` (`git grep -l '```' 4e4a00c -- '*.py' | sed 's/^4e4a00c://' | grep -vcE '^(h-mad|handoff)/'`) — and through v1.94 both figures carried a `6f0ee85` stamp that
nothing re-derived, because the corpus-argument driver above was driven off the `grep -r … --include`
spelling and this member is a `git grep … -- '*.py'` form with no `--include`. That is the member
the corpus-shape driver was rewritten to reach, and it is the reason the rewrite was a must and not
a tidy-up. This control has now drifted twice and its conclusion has survived both times,
which is exactly why the command travels with it: it was a bare `21` at `6b4df35`, `b59e05e` — the
same commit that moved the suite floor from 2747 to 2748 — took it to 23 with only the floor
re-measured, and the new hit at `a8e0372` is the `h_mad_precheck_doc.py` comment above, not an
extractor. Re-run the command rather than trusting the number. One further
consumer reads `SKILL.md` and was checked directly rather than inferred — `h-mad/tests/docsections.py`
bounds fences with `stripped.startswith("```")`, a **prefix** match, so an info-string tag does not
disturb it. Located structurally rather than by line, because a line pin here has no provenance to
check it against: `grep -n 'startswith("```")' h-mad/tests/docsections.py` → exactly one hit at
`335f535`, inside `_fence_aware_end`. Residual: if that helper ever grows a second fence test the
grep returns two and the "one prefix match" reading must be re-read, not re-counted.

**The process-group reap (AC-5.2), both legs and a control.** The claim the timeout design rests
on is that `killpg(proc.pid, SIGKILL)` reaches every descendant still in the launched group, and
that a descendant which leaves the group escapes it — so AC-5.2 is scoped to the group. Both
halves were measured with the script below, which also proves the descendant existed before the
kill (the control that stops "gone" from meaning "never started") and refuses with
`PROBE VACUOUS` rather than reading a null as a negative. The last two lines are the two facts the
design's race handling (AC-5.5) depends on: macOS ships no `setsid` binary, so a binary-based
escape probe measures nothing, and `killpg` on a group that has already emptied raises
`ProcessLookupError`:

```
$ python3.11 -u - <<'PY'
import os, signal, subprocess, sys, tempfile, time
def alive(pid):
    try: os.kill(pid, 0); return True
    except ProcessLookupError: return False
def leg(escape):
    d = tempfile.mkdtemp(); pidf = os.path.join(d, "pid"); child = os.path.join(d, "child.py")
    open(child, "w").write("import os,time\n" + ("os.setsid()\n" if escape else "")
                           + f"open({pidf!r},'w').write(str(os.getpid()))\ntime.sleep(300)\n")
    p = subprocess.Popen(["bash", "-c", f"{sys.executable} {child} & sleep 300"],
                         start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(200):
        if os.path.exists(pidf) and open(pidf).read().strip(): break
        time.sleep(0.05)
    else: raise SystemExit("PROBE VACUOUS: descendant never wrote its pid")
    gc = int(open(pidf).read()); assert alive(gc), "control: descendant alive before the kill"
    try: p.communicate(timeout=0.5)
    except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL)
    time.sleep(0.3); survived = alive(gc)
    if survived: os.kill(gc, signal.SIGKILL)
    return gc, survived
print("python:", sys.version.split()[0], "|", sys.platform)
p = subprocess.Popen(["sleep", "5"], start_new_session=True)
print("pgid == pid under start_new_session:", os.getpgid(p.pid) == p.pid); p.kill(); p.wait()
print("in-group descendant %d: survived killpg? %s   (want False)" % leg(False))
print("os.setsid() descendant %d: survived killpg? %s   (want True: escapes the group)" % leg(True))
print("setsid binary on PATH:", subprocess.run(["which", "setsid"], capture_output=True, text=True).stdout.strip() or "NONE")
p = subprocess.Popen(["true"], start_new_session=True); p.wait()
try: os.killpg(p.pid, signal.SIGKILL); print("killpg on an already-reaped group: no error")
except ProcessLookupError: print("killpg on an already-reaped group: ProcessLookupError")
PY
python: 3.11.8 | darwin
pgid == pid under start_new_session: True
in-group descendant 90513: survived killpg? False   (want False)
os.setsid() descendant 90537: survived killpg? True   (want True: escapes the group)
setsid binary on PATH: NONE
killpg on an already-reaped group: ProcessLookupError
```

Re-run in v1.93 under `python3.11`, the supported interpreter, with the platform line added. It
ran under `python3` through v1.92 and printed no interpreter or platform at all, so it was the one
carve-out member that claimed the exemption without publishing the stamp the exemption is granted
in exchange for — the same defect as the wrapper probe's, on the other half of the rule. The pids
move on every run and are output, not pins.

**The cleanup fixture (AC-3.14).** The fixture block is `mkdir keep && chmod 000 keep`, and the
claim the AC rests on is that `shutil.rmtree` raises on the result while `ignore_errors=True`
retains it silently. Measured on the supported interpreter, as an unprivileged user:

```
$ python3.11 -u - <<'PY'
import os, shutil, subprocess, sys, tempfile
d = tempfile.mkdtemp()
r = subprocess.run(["bash", "-euo", "pipefail", "-c", "mkdir keep && chmod 000 keep"], cwd=d)
print("fixture block rc:", r.returncode, "| euid:", os.geteuid(), "| python:", sys.version.split()[0], "|", sys.platform)
try:
    shutil.rmtree(d); print("rmtree(d): removed with no error")
except OSError as e:
    print("rmtree(d) raised:", type(e).__name__, "on", os.path.basename(e.filename))
print("retained after the raise:", os.path.lexists(d))
shutil.rmtree(d, ignore_errors=True)
print("retained after rmtree(d, ignore_errors=True):", os.path.lexists(d), "<- silent")
os.chmod(os.path.join(d, "keep"), 0o700); shutil.rmtree(d); print("cleaned by the test's finally:", not os.path.lexists(d))
PY
fixture block rc: 0 | euid: 501 | python: 3.11.8 | darwin
rmtree(d) raised: PermissionError on keep
retained after the raise: True
retained after rmtree(d, ignore_errors=True): True <- silent
cleaned by the test's finally: True
```

Under root the mode bits do not bind and the raise does not occur, so the test skips the
permission fixture there and the fault-injected variants carry the AC (Risks table).

**The reader-less FIFO (AC-3.10).** The reservation's existing-file arm opens with `O_NONBLOCK`
because a blocking open of a FIFO with no reader never returns; the claim that the non-blocking
open fails *at once* with `ENXIO`, and that a FIFO which does have a reader is still refused by
the regular-file check, was measured on the supported interpreter:

```
$ python3.11 -u - <<'PY'
import os, stat, sys, tempfile, time, errno
d = tempfile.mkdtemp(); p = os.path.join(d, "out.fifo"); os.mkfifo(p)
t0 = time.monotonic()
try:
    fd = os.open(p, os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK); os.close(fd); print("O_NONBLOCK open on a reader-less FIFO: SUCCEEDED (unexpected)")
except OSError as e:
    print("O_NONBLOCK open on a reader-less FIFO: %s errno=%d (%s) after %.4fs" % (type(e).__name__, e.errno, errno.errorcode[e.errno], time.monotonic() - t0))
r = os.open(p, os.O_RDONLY | os.O_NONBLOCK)      # a reader now exists, so the writer open succeeds -> the S_ISREG check must refuse it
fd = os.open(p, os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK); st = os.fstat(fd)
print("with a reader present: open succeeds; S_ISREG=%s S_ISFIFO=%s -> refused by the regular-file check" % (stat.S_ISREG(st.st_mode), stat.S_ISFIFO(st.st_mode)))
os.close(fd); os.close(r); os.unlink(p); os.rmdir(d); print("python", sys.version.split()[0], sys.platform)
PY
O_NONBLOCK open on a reader-less FIFO: OSError errno=6 (ENXIO) after 0.0000s
with a reader present: open succeeds; S_ISREG=False S_ISFIFO=True -> refused by the regular-file check
python 3.11.8 darwin
```

**The naturally emptied group (AC-5.5), and why `poll()` comes first.** The race the design
handles — the group is already gone when the reap runs — was assumed to surface as
`ProcessLookupError`. Measured, it does not on macOS unless the leader is reaped first: a leader
that has exited is a zombie, and `killpg` on a zombie-only group raises `PermissionError`; after
`proc.poll()` reaps it the same call raises `ProcessLookupError`. The fixture is a leader that
starts an `os.setsid()` descendant holding stdout and exits at once — no mock — and the same run
shows the drain timing out on the escapee's pipe and `wait()` returning immediately (the probe's
bare `p.wait()` is the measurement; the helper's own call is `wait(timeout=DRAIN_SECONDS)`, below):

```
$ python3.11 -u - <<'PY'
import os, signal, subprocess, sys, tempfile, time
d = tempfile.mkdtemp(); child = os.path.join(d, "esc.py"); pidf = os.path.join(d, "pid")
open(child, "w").write(f"import os,time\nos.setsid()\nopen({pidf!r},'w').write(str(os.getpid()))\ntime.sleep(300)\n")
p = subprocess.Popen(["bash", "-c", f"{sys.executable} {child} & exit 0"], start_new_session=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
for _ in range(200):
    if os.path.exists(pidf) and open(pidf).read().strip(): break
    time.sleep(0.05)
esc = int(open(pidf).read())
try: p.communicate(timeout=1.0)
except subprocess.TimeoutExpired:
    print("TimeoutExpired (escapee %d holds the pipe; leader exited)" % esc)
    try: os.killpg(p.pid, signal.SIGKILL); print("killpg BEFORE poll: no error")
    except OSError as e: print("killpg BEFORE poll:", type(e).__name__)
    rc = p.poll(); print("poll() reaped the zombie leader, rc =", rc)
    try: os.killpg(p.pid, signal.SIGKILL); print("killpg AFTER poll: no error")
    except OSError as e: print("killpg AFTER poll:", type(e).__name__, "<- group empty")
    t0 = time.monotonic()
    try: p.communicate(timeout=1.0); print("drain finished")
    except subprocess.TimeoutExpired:
        p.stdout.close(); p.stderr.close(); p.wait(); print("drain timed out at %.1fs -> pipes closed, wait() returned rc %s at once" % (time.monotonic()-t0, p.returncode))
os.kill(esc, signal.SIGKILL); print("escapee reaped by the probe; python", sys.version.split()[0], sys.platform)
PY
TimeoutExpired (escapee 96921 holds the pipe; leader exited)
killpg BEFORE poll: PermissionError
poll() reaped the zombie leader, rc = 0
killpg AFTER poll: ProcessLookupError <- group empty
drain timed out at 1.0s -> pipes closed, wait() returned rc 0 at once
escapee reaped by the probe; python 3.11.8 darwin
```

So the reap sequence is `poll()` → `killpg` (catch `ProcessLookupError`) → bounded drain → close
pipes → `wait(timeout=DRAIN_SECONDS)`, taken only when the group was signalled: a delivered
`SIGKILL` is not a completion deadline, so the wait is bounded like the drain, and its
`TimeoutExpired` becomes `LAUNCH_FAILED stage=reap` with the pending `BlockTimeout` as
`__context__` — the helper's wall time is at most `timeout + 2 * DRAIN_SECONDS` plus teardown
(`test_wait_after_kill_is_bounded`; mutations `wait-unbounded`, `wait-expiry-unmapped` — design
v1.73). Without the `poll()` the natural race reports `LAUNCH_FAILED stage=reap` instead
of `TIMEOUT`, which is the mutation `poll-before-killpg-removed` and the test that kills it.

**That measurement stands and is no longer the whole story:** a later design cycle found the same
toggle mis-tracks an unbalanced inner quote inside a four-backtick fence, which is why
`docsections.py` now appears under Deliverables and Implementation Strategy — it drops its
duplicate bounder and imports the authoritative one. The tag was never the reason to change it;
the duplicate bounder is.

- **The corpus for every `*.md`-scoped measurement below is the tracked one**, defined as design
  v1.93 §Scanning defines it — `git ls-files -- h-mad handoff` filtered to `*.md` with `archive/`
  excluded — and **not** a filesystem glob. **The definition is the `git ls-files` command; the
  file count is a measurement and never the definition**, because the two drift apart and a reader
  who matches a re-run number against the wrong figure inverts the whole bullet. At `a8e0372` the
  pair is **30 tracked / 35 glob**; at `1861157`, the sha the heading and Setext figures below were
  measured at, it was **25 / 30**; re-run at `335f535`, at `35698f9`, at `cf3a862` and again at the freeze `4e4a00c` it is **30 / 35** still — re-run at the freeze for the same reason as the census above, since `a8e0372` and `335f535` both predate the closure's window. The pair moved because `6db8e50` added five `h-mad/agents/*.md`
  (`git diff-tree --no-commit-id --name-only -r --diff-filter=A 6db8e50 -- h-mad/agents` lists
  exactly those five paths and nothing else; the plainer `git show --stat 6db8e50` was cited here
  through v1.93 and lists **six** rows, because that commit also modified `h-mad/SKILL.md` — the
  claim was "five new files" and the command was "everything the commit touched", which is a
  command that does not answer the claim rather than a wrong number), and it will move again with any
  `.md` added under the two roots.

  ```
  $ git ls-files -- h-mad handoff | grep '\.md$' | grep -v '/archive/' | wc -l    # 30 at 4e4a00c, cf3a862 and a8e0372; 25 at 1861157
  30
  ```

  **What is invariant is the structure, not the pair**: the glob is exactly the tracked set plus
  the untracked, gitignored `.pytest_cache/README.md` artifacts, which exist only on a tree where
  pytest has run and each carry `# pytest cache directory #`. Re-derived at `a8e0372` by
  differencing the two sets: the surplus is exactly five files —
  `h-mad/.pytest_cache/README.md`, `h-mad/scripts/.pytest_cache/README.md`,
  `h-mad/tests/.pytest_cache/README.md`, `handoff/.pytest_cache/README.md`,
  `handoff/tests/.pytest_cache/README.md` — and the tracked set has no member the glob misses.
  Those five are build output, they are not documents this feature reads, and they made the heading
  measurements irreproducible on a clean clone. Every figure below is therefore given on both
  corpora, so the contamination is visible rather than assumed away. **Residual**: the figures
  below carry `files=25`/`files=30` because that is what the script printed at `1861157`, the sha
  named beside them, and they are **not** re-run here. What the five new `h-mad/agents/*.md` were
  inspected for at `a8e0372` — inspection, not a re-run of the differential — is exactly the
  conclusion that would be at risk: none of them carries any of the three softening shapes
  (closing hash 0, tab form 0, title-less 0 on each of the five), so **`new_only=0` still holds**
  and the Guard-narrowing accounting below is unaffected. **`both` and `old_only` will move, and
  are re-measured at 5c rather than predicted here**: `h-mad/agents/doc-auditor.md` alone carries
  four `#`-prefixed lines *inside* fenced blocks, and the other four `h-mad/agents/*.md` carry
  none. **The command is written out rather than described** — a description of a one-liner is not
  a one-liner, and this figure is load-bearing for the `old_only` prediction below. Re-derived at
  `35698f9`:

  ```
  $ awk 'FNR==1{infence=0} /^ *(```|~~~)/{infence=!infence; next} infence && /^ *#/{print FILENAME": "$0}' h-mad/agents/*.md
  h-mad/agents/doc-auditor.md: ## Summary
  h-mad/agents/doc-auditor.md: ## Must-fix
  h-mad/agents/doc-auditor.md: ## Should-fix
  h-mad/agents/doc-auditor.md: ## Nit
  $ awk 'FNR==1{infence=0} /^ *(```|~~~)/{infence=!infence; n[FILENAME]++; tot++; next} END{print "markers", tot; for (f in n) print f, n[f]}' h-mad/agents/*.md
  markers 8
  h-mad/agents/spec-author.md 2
  h-mad/agents/implplan-author.md 2
  h-mad/agents/doc-auditor.md 4
  ```

  The printed lines **are** the positive control — four, all named by the command itself rather
  than by a count in prose. The **true negative** is the part a bare "0 on the other four" would
  hide: `implplan-author.md` and `spec-author.md` each hold a balanced fence **and** carry
  `#`-prefixed lines (4 each by `grep -c '^ *#'` at `35698f9`), and the screen declines every one
  of them, so it is discriminating on fence state and not merely on the absence of `#`;
  `design-author.md` and `plan-author.md` hold no fence at all and are declined trivially.
  **Residual, since this toggle is not the scanner the feature ships**: it flips on any fence
  marker line without checking run length, marker character or info string, so a three-backtick
  line quoted inside a four-backtick fence would close that fence early and drop real hits. It
  cannot fire on this corpus — the second command above, the same toggle tallying the marker lines
  it fires on instead of printing headings, reports **8** at `35698f9`, every one a bare
  three-backtick run and an even count in each file, so the state is balanced everywhere it
  matters — but that is a property of the corpus as it stands at `35698f9` and must be re-checked,
  not assumed, at 5c. It is
  also broader than the old selector on the other side: `/^ *#/` matches any `#`-prefixed line
  while the old `titled_section` regex required `#+ `. Both directions are stated because the
  figure below rests on them, and this is precisely the shape `old_only` counts, so a 5c run should report
  `old_only` above 76 — larger, which strengthens the "the migration narrows the guard"
  conclusion rather than weakening it, but it is a prediction and the number below is not.

- **Heading selector differential** — the old `docsections.titled_section` regex
  (`^(?P<marks>#+) …\s*$`) against the CommonMark ATX selector `find_heading` implements, fence-aware
  on the new side (throwaway `heading_differential.py`, one `re.match` per line per selector),
  re-derived at `1861157` over both corpora:

  ```
  $ python3.11 heading_differential.py
  --- TRACKED (git ls-files)
  files=25 both=263 old_only=76 new_only=0
  softening shapes: closing_hash=0 tab_form=0 titleless=0
  --- GLOB (filesystem)
  files=30 both=268 old_only=76 new_only=0
  softening shapes: closing_hash=5 tab_form=0 titleless=0
  OLD-ONLY h-mad/SKILL.md 83 # WIRING: PASS
  OLD-ONLY h-mad/SKILL.md 84 # WIRING: FAIL issues=1  +  detail lines
  OLD-ONLY h-mad/SKILL.md 85 # WIRING: UNKNOWN reason=no_settings      (exit 2 — nothing was read)
  ```

  `new_only=0` and `old_only=76` hold on **both** corpora, so the differential's two load-bearing
  conclusions never depended on the contamination. `old_only=76`: all 76 are `#` comment lines
  inside fenced code the old regex read as headings; the migration narrows the guard.

  **The `new_only=0` justification did depend on it, and is restated correctly.** The base
  Guard-narrowing invariant's "every softened outcome" set is about heading *identity*, not about
  which lines are recognised — a `## x ##` line is a heading to both selectors and lands in `both`,
  never in `new_only`, while only the new selector strips the closing run and so answers a request
  for `x`. Counted as identities, both readings at `1861157`: over the tracked 25 there the
  softened shapes are `closing_hash=0
  tab_form=0 titleless=0`, so the set is genuinely empty. Over the glob 30 there, `closing_hash=5` — the
  five `# pytest cache directory #` lines, one per `.pytest_cache/README.md`. The old text claimed
  `## x ##` "occurs nowhere" while measuring a corpus in which it occurred five times; the claim is
  true of the corpus this feature actually reads, and was false of the corpus that was measured.

  **`both` moved 266 → 268 on the glob (261 → 263 tracked), and nothing is wrong with either.**
  The `266` was correct when recorded at `1f5b30e`; `h-mad/SKILL.md` has since gained exactly two
  `###` headings — "Close the class, never the instance" (`e8eaf6f`) and "Record a rejected finding
  in the rejections ledger, never in a gated document" (`ff0a278`/`11a7db7`) — measured by diffing
  the heading lines between the two revisions. `both` is not a conclusion this plan rests on; it
  drifts with any documentation edit under the two roots, which is why the command is recorded
  beside it and the number is not to be carried.
- **Setext census** — the ATX-only assumption measured directly rather than through the selector
  differential (both of whose selectors ignore Setext): a fence-aware scan for a `===`/`---`
  underline line immediately after a paragraph line (CommonMark §4.3; YAML front matter skipped;
  list, table, blockquote and indented-code lines are not paragraphs) over the same corpus, run in
  the same script as the differential above and re-derived at `1861157` on both readings of it:

  ```
  $ python3.11 heading_differential.py
  --- TRACKED (git ls-files)
  files=25 setext_headings=0
  --- GLOB (filesystem)
  files=30 setext_headings=0
  ```

  So no document `docsections` or the helper reads bounds wrongly under the ATX-only grammar;
  a Setext heading that arrives later is still unrecognised silently, which the design carries as a
  limitation rather than a guard.
- **Scanner grammar corpus** — every fence and ATX rule the scanner implements, rendered through
  markdown-it-py 2.2.0 (interpreter-local) AND 4.2.0 (the spec's throwaway-venv version, installed
  with `pip install --target` for this run), CommonMark preset on both, 14 of 14 agreeing on each; the
  script is a throwaway (`grammar_corpus.py`, one `md.render(src)` per case, a needle asserted on
  the HTML), and its output is what the design's §Scanning cites:

  ```
  $ python3.11 -c "import markdown_it; print(markdown_it.__version__)"
  2.2.0
  $ python3.11 grammar_corpus.py
  OK  opener at 3 spaces IS a fence                | '<pre><code class="language-bash">X\n</code></pre>'
  OK  opener at 4 spaces is NOT a fence            | '<pre><code>```bash\n</code></pre>\n<p>X</p>'
  OK  closer shorter than opener does not close    | '<pre><code>X\n```\nY\n</code></pre>'
  OK  closer with trailing text does not close     | '<pre><code>X\n``` trailing\nY\n</code></pre>'
  OK  closer at 4 spaces does not close            | '<pre><code>X\n    ```\nY\n</code></pre>'
  OK  tilde does not close a backtick fence        | '<pre><code>X\n~~~\nY\n</code></pre>'
  OK  body de-indented by opener indent (2)        | '<pre><code>a\nb\n c\n</code></pre>'
  OK  #hashtag is not a heading                    | '<p>#hashtag</p>'
  OK  seven hashes is not a heading                | '<p>####### x</p>'
  OK  4-space-indented ## is not a heading         | '<pre><code>## x\n</code></pre>'
  OK  3-space-indented ## IS a heading             | '<h2>x</h2>'
  OK  closing hashes are stripped                  | '<h2>x</h2>'
  OK  tab after hashes IS a heading                | '<h2>x</h2>'
  OK  heading inside a fence is not a heading      | '<pre><code>## x\n</code></pre>'
  ```

- **Fence-body de-indentation, the one case this revision ran** — added because the `extract`
  body-normalisation row under §Implementation Strategy asserted that a body line indented *less*
  than the opener is "left as is", and CommonMark says the opposite: up to N spaces are removed
  from **each** line, so a line with fewer than N loses all of them. The claim was a property of a
  third-party renderer stated from the design rather than executed, which is what makes it this
  round's instance of the class. Executed on both renderer versions, the interpreter-local 2.2.0
  and the throwaway-target 4.2.0 (`pip install --target`), CommonMark preset on both, agreeing:

  ```
  $ python3.11 - <<'PY'
  import markdown_it
  md = markdown_it.MarkdownIt("commonmark")
  src = "   ```bash\n   a\n b\nc\n     d\n   ```\n"     # opener at 3; body at 3, 1, 0, 5
  print("markdown-it-py", markdown_it.__version__, "->", repr(md.render(src)))
  PY
  markdown-it-py 2.2.0 -> '<pre><code class="language-bash">a\nb\nc\n  d\n</code></pre>\n'
  $ PYTHONPATH=<throwaway target> python3.11 <same script>
  markdown-it-py 4.2.0 -> '<pre><code class="language-bash">a\nb\nc\n  d\n</code></pre>\n'
  ```

  The 1-space line came back with **no** leading space and the 5-space line with **two** (5 − 3), so
  the rule is "strip up to the opener's indent, per line" on both renderers and "left as is" was
  false. **This case is NOT one of the fourteen above** — that corpus was not re-run in this
  revision and stays in the inherited-unverified register; this is a fifteenth, run alone. It is
  covered by the scanner-grammar-corpus row of the carve-out table below rather than by a row of its
  own, because its subject and stamp are the same (`git ls-files markdown_it markdown-it-py` →
  empty; stamped `markdown-it-py 2.2.0` and `4.2.0`), and adding a row would restale the table's
  own eight-row and seven-member figures for nothing.

**A premise whose subject is a stdlib or OS call is a probe, even when it is written as one clause
of a prose sentence.** The axis, stated so the rule is over it rather than over the two members an
audit named: *a sentence that names a language-, library- or OS-level call and asserts what that
call does, published in the body as settled fact, carrying no executed command and no recorded
output.* This document already discharged the class for every premise whose subject is an
**explicitly named probe** — argparse's `exit_on_error`, `killpg` on a zombie group, the reader-less
FIFO's `ENXIO`, `rmtree` on `0o000`, the markdown-it-py corpus, the fence-body de-indentation case —
each with a fenced command, its printed output and a carve-out row. What it did not reach through
v1.98 is the premise whose subject is a stdlib call *inside a sentence about something else*, where
the provenance a reviewer sees is a **locator** (`grep -n` proving the code is there) standing in
for a **behaviour** command. **The rule that closes it: a sentence naming a stdlib or OS call and
asserting what it does takes a probe's treatment — a fenced command, its output and its
version-or-sha stamp — or the sentence says `unexecuted` in as many words.** Five members were
found: the two the round-thirteen audit filed and the three it read but did not run and filed as the
class's residual rather than as findings. **All five are executed below, so this revision leaves the
class with no `unexecuted` member and nothing promoted to a finding on a reading.** Residual, and no
screen reaches it: the carve-out sweep below is driven off **stamps**, so a premise that carries no
stamp at all is invisible to it for the same structural reason the calendar-date member was; a
fourth driver branch keyed on stdlib symbol names (`json.dumps`, `splitlines`, `re.search`,
`fstat`, `TextIOWrapper`) would help and is deliberately not built, because it would screen the
symbols this document happens to use at this revision and the class is not about those symbols. The honest
position is that this class is swept by reading. Every one of the five is stamped `python 3.11.8`
on `darwin`, so under the population rule stated with the carve-out table each is a row of it, and
they are added there as a separately-headed block rather than mixed into the eight `cf3a862` rows.

- **`json.dumps` line-breaking, per code point** — the escaper premise at the head of §Scope. The
  claim under test was a conjunction over the whole set: "which `json.dumps` leaves literal **and**
  `splitlines()` breaks on". Run one code point at a time rather than over the set:

  ```
  $ python3.11 - <<'PY'
  import json, sys, unicodedata
  cat = lambda cp: unicodedata.category(chr(cp))
  lines = lambda s: len(json.dumps(s, ensure_ascii=False).splitlines())
  lit = [cp for cp in range(0x110000)
         if cat(cp) in ('Cc', 'Zl', 'Zp')
         and chr(cp) in json.dumps('a' + chr(cp) + 'b', ensure_ascii=False)]
  named = {0x7F} | set(range(0x80, 0xA0)) | {0x2028, 0x2029}
  print("python", sys.version.split()[0], "| platform", sys.platform)
  print("Cc/Zl/Zp total", sum(1 for cp in range(0x110000) if cat(cp) in ('Cc', 'Zl', 'Zp')),
        "| left literal by json.dumps", len(lit),
        "| set-equal to DEL+C1+LS+PS:", set(lit) == named)
  print("of those, splitlines() breaks on:",
        [f"U+{cp:04X}" for cp in lit if lines('a' + chr(cp) + 'b') > 1])
  print("DEL U+007F ->", lines('a' + chr(0x7F) + 'b'), "line")
  print("C1 U+0080-U+009F that break:",
        [f"U+{cp:04X}" for cp in range(0x80, 0xA0) if lines('a' + chr(cp) + 'b') > 1],
        "= 1 of 32; the other 31 ->",
        sorted({lines('a' + chr(cp) + 'b') for cp in range(0x80, 0xA0) if cp != 0x85}), "line")
  PY
  python 3.11.8 | platform darwin
  Cc/Zl/Zp total 67 | left literal by json.dumps 35 | set-equal to DEL+C1+LS+PS: True
  of those, splitlines() breaks on: ['U+0085', 'U+2028', 'U+2029']
  DEL U+007F -> 1 line
  C1 U+0080-U+009F that break: ['U+0085'] = 1 of 32; the other 31 -> [1] line
  ```

  So the first conjunct holds for **35 of 35** and the second for **3 of 35**. The `set-equal` line
  is the part that makes the arithmetic checkable rather than plausible: the 35 survivors are
  *exactly* the set §Scope names, so no member is being counted twice or missed. **DEL contributes
  nothing to line-breaking and neither do 31 of the 32 C1 code points**; §Scope now states the two
  reasons apart.

- **The composite fixture that could not see it — run per member, which is DECISION O applied to a
  fixture this document inherited.** The evidence cited for the conjunction is a heading carrying
  NEL, LS, PS and DEL that splits into four lines after `json.dumps` alone. It reproduces. It is
  also insensitive to the one member it was read as covering:

  ```
  $ python3.11 - <<'PY'
  import json
  lines = lambda s: len(json.dumps(s, ensure_ascii=False).splitlines())
  NEL, LS, PS, DEL = chr(0x85), chr(0x2028), chr(0x2029), chr(0x7F)
  comp = "## H" + NEL + "e" + LS + "a" + PS + "d" + DEL + "s"
  for label, ch in (("nothing   ", ""), ("DEL U+007F", DEL), ("NEL U+0085", NEL),
                    ("LS  U+2028", LS), ("PS  U+2029", PS)):
      print("composite minus " + label + " ->", lines(comp.replace(ch, "")), "lines")
  PY
  python 3.11.8
  composite minus nothing    -> 4 lines
  composite minus DEL U+007F -> 4 lines
  composite minus NEL U+0085 -> 3 lines
  composite minus LS  U+2028 -> 3 lines
  composite minus PS  U+2029 -> 3 lines
  ```

  Removing DEL changes nothing; removing any one of the other three costs a line. **Four lines is
  what three breaking characters produce, so the composite is consistent with DEL being inert and a
  reader cannot tell the two apart from its output** — the healthy branch masking the sick one,
  committed inside a `measured:` citation, which is the one place a reader stops checking. **The
  behaviour is unaffected and the guard must not be weakened**:
  `test_unicode_line_separators_cannot_split_a_verdict_line` drives U+0085, U+2028, U+2029 **and**
  U+007F. **Both sibling readings this bullet used to publish were misassigned, by one mechanism:
  a whole-file `grep -c` over a sibling, attributed to a site it does not read.** The axis is
  cross-document verification, and the rule over it is that a sibling census is *scoped to the
  sibling's body* and *each hit is classified* before it is described — never counted and then
  narrated. Both are re-run under that rule at `8c6539a`, the commit this revision is authored
  against.

  **Impl-plan.** The needle returns **3** whole-file, which is the figure this bullet used to
  publish; body-scoped it returns **2**, and the two body hits are not the same kind of line. The
  third is a Version History entry — the hazard this document states against itself in the
  spec-enumeration paragraph above ("a §Version History entry quoting it takes the count to 2") and
  then walked into here:

  ```
  $ python3 - <<'PY'
  import re, subprocess
  NEEDLE = "U+0085, U+2028, U+2029 and U+007F"
  SHA = "8c6539a:docs/01-plan/features/doc-block-exec.impl-plan.md"
  lines = subprocess.run(["git", "show", SHA], capture_output=True,
                         text=True, check=True).stdout.split("\n")
  vh = next(i for i, ln in enumerate(lines) if ln.startswith("## Version History"))

  def walk(pat, strict):            # strict: closer bare, same char, >= opener length
      op, inside = None, []
      for ln in lines:
          m = re.match(pat, ln)
          if m:
              tok = m.group(1)
              if op is None:
                  op = tok; inside.append(True); continue
              if not strict or (tok[0] == op[0] and len(tok) >= len(op) and ln.strip() == tok):
                  op = None; inside.append(True); continue
          inside.append(op is not None)
      return inside

  hits = [i for i, ln in enumerate(lines) if NEEDLE in ln]
  body = [i for i in hits if i < vh]
  aware = walk(r"^ {0,3}(`{3,}|~{3,})", True)
  print("hits", len(hits), "| body", len(body),
        "| fenced", sum(aware[i] for i in body),
        "| prose", sum(not aware[i] for i in body))
  for label, pat, strict in (("any-indent, loose close", r"^ *(`{3,})", False),
                             ("mixed-run class        ", r"^ {0,3}([`~]{3,})", True)):
      print("control:", label, "calls", sum(walk(pat, strict)[i] for i in body), "of the 2 fenced")
  PY
  hits 3 | body 2 | fenced 1 | prose 1
  control: any-indent, loose close calls 1 of the 2 fenced
  control: mixed-run class         calls 2 of the 2 fenced
  ```

  So the assignment is **one prose line and one code payload**, not "two prose restatements": the
  prose line is the AC-4.1 checklist row, which is the acceptance criterion the test is written
  against and is what carries the claim; the fenced line is the `_field` docstring reproduced inside
  Task 1's delta, which is *source this plan's sibling is specifying*, not a restatement of the
  criterion. **Residual, and it is why the classification is run rather than read**: fencedness here
  is instrument-sensitive, so a bare line-scoped `grep` cannot produce this partition at all. The
  second control above is a live disagreement, not a decoration — the mixed-run character class
  opens a phantom fence on a prose line carrying a run of backticks and tildes together, and calls **2 of 2**
  fenced where the one-character-run walk calls **1**. Any cross-document census over this sibling
  that is not fence-aware in that specific way misreports code payloads as prose.

  **Design.** The needle this bullet used to publish, `'U+2028, U+2029 and DEL'`, returns **1**
  body-scoped at `700c599` and **1** at `8c6539a` — but that hit is the AC-4.1 prose sentence, not
  the `c1-escape-removed` mutation row it was cited for. The row is read by a needle taken from the
  row itself: `git show 8c6539a:docs/02-design/features/doc-block-exec.design.md | awk '/^## Version
  History/{exit}{print}' | grep -c 'DEL, C1 controls (U+0085) and U+2028/U+2029 stay literal'` →
  **1**, and **1** at `700c599` as well, so the needle is stable across the design's own v1.104
  rewrite of that row's second half. Re-measure it if that row is reworded again. So
  `c1-escape-removed` is still killed through NEL whatever DEL does. This is a documentation defect,
  not a behaviour defect.

  **The design owns the origin of the conjunction, and it was repaired there in the same commit that
  carried this bullet** — design v1.104 at `8c6539a`, not work still owed:
  `git show 8c6539a --format="" -- docs/02-design/features/doc-block-exec.design.md | grep -c '^+.*The second pass covers one set for two different reasons'`
  → **1**. **The two repairs were written independently and their residuals differ on purpose, in
  both directions**: this document publishes the set-equality check (the 35 code points `json.dumps`
  leaves literal are set-*equal* to the set named here) which the design does not, and the design
  states a residual this document does not carry — a code point some consumer treats as a boundary
  but which lies outside `Cc`/`Zl`/`Zp`, a bidi control, is neither escaped by the second pass nor
  reached by the census; `git show 8c6539a:docs/02-design/features/doc-block-exec.design.md | awk '/^## Version History/{exit}{print}' | grep -c 'Cf'`
  → **1** body-scoped (**2** whole-file, the second a Version History entry — the same scoping trap
  again, in the reading that establishes the point). Neither document adopts the other's residual, so
  a reader reconciling the two needs both. A matching absence count over *this* document is
  deliberately not published: the needle would have to be written into the sentence publishing it,
  which is the self-match this revision measures elsewhere.
  **No literal U+0085, U+2028, U+2029 or U+007F byte is written into this document**: every fixture
  above builds its characters with `chr()`, because a literal one would make this file's own line
  count differ between `awk` and any `splitlines()`-based reader, including the precheck. Measured
  after this revision's last edit — `python3 -c` counting those four code points in the file → **0**.

- **`re.search` end-of-match on the `titled_section` selector** — the premise the FR-6 paragraph's
  leading-newline decision rests on, which was carried with a `grep -n` locator and no behaviour
  command:

  ```
  $ python3.11 - <<'PY'
  import re, sys
  print("python", sys.version.split()[0])
  for text in ("## H" + chr(10) + "Body" + chr(10),
               "## H" + chr(10) + chr(10) + "Body" + chr(10)):
      m = re.search(r"(?m)^(?P<marks>#+) H\s*$", text)
      print(repr(text), "-> match.end() =", m.end(), "| remainder", repr(text[m.end():]))
  PY
  python 3.11.8
  '## H\nBody\n' -> match.end() = 4 | remainder '\nBody\n'
  '## H\n\nBody\n' -> match.end() = 5 | remainder '\nBody\n'
  ```

  `\s*$` stops at the end of the heading *line*, before its newline, so with a non-blank line
  following the section keeps a leading `\n` that `find_heading`'s past-the-line offset does not —
  and with a blank line after the heading the two remainders are identical, which is the
  "they agree" half. The conclusion the paragraph drew was correct; only its provenance was a
  locator.

- **A buffered `TextIOWrapper` defers the OS write until `flush()`/`close()`, and `(st_dev, st_ino)`
  on the opened descriptors catches a hard link** — two premises of the stream-reservation paragraph
  under §Scope, run together because they share a fixture directory:

  ```
  $ python3.11 - <<'PY'
  import os, sys, tempfile
  print("python", sys.version.split()[0], "| platform", sys.platform)
  d = tempfile.mkdtemp()
  p = os.path.join(d, "buf.txt")
  h = open(p, "w"); h.write("x" * 100)
  print("after write(100), os.stat().st_size =", os.stat(p).st_size)
  h.flush()
  print("after flush(),    os.stat().st_size =", os.stat(p).st_size)
  h.close()
  a, b, s, c = (os.path.join(d, n) for n in ("a", "b", "s", "c"))
  open(a, "w").close(); os.link(a, b); os.symlink(a, s); open(c, "w").close()
  key = lambda fh: (os.fstat(fh.fileno()).st_dev, os.fstat(fh.fileno()).st_ino)
  ha, hb, hs, hc = open(a), open(b), open(s), open(c)
  print("hard link  a vs b:", key(ha) == key(hb), " (distinct paths, no symlink)")
  print("symlink    a vs s:", key(ha) == key(hs))
  print("unrelated  a vs c:", key(ha) == key(hc), "  <- negative control")
  PY
  python 3.11.8 | platform darwin
  after write(100), os.stat().st_size = 0
  after flush(),    os.stat().st_size = 100
  hard link  a vs b: True  (distinct paths, no symlink)
  symlink    a vs s: True
  unrelated  a vs c: False   <- negative control
  ```

  The 100 bytes are invisible to `os.stat` until `flush()`, which is why an `OSError` can first
  surface at a close outside the mapped region and why the backstop close exists. The alias key is
  equal for a hard link — two independent directory entries, neither a symlink — and the unrelated
  file is the negative that shows the key discriminates at all rather than comparing equal to
  everything.

- **Unpacking `find_heading`'s result directly raises `TypeError` on absence** — the premise the
  bind-then-check ordering in the FR-6 paragraph rests on:

  ```
  $ python3.11 - <<'PY'
  import sys
  print("python", sys.version.split()[0])
  def find_heading(text, heading):      # the None branch, which is the one at issue
      return None
  try:
      start, level = find_heading("doc", "## H")        # unpack the call directly
  except TypeError as exc:
      print("unpack-first  ->", type(exc).__name__ + ":", exc)
  found = find_heading("doc", "## H")                   # bind, then check
  if found is None:
      print("bind-then-check -> found is None, the loud failure is reachable")
  PY
  python 3.11.8
  unpack-first  -> TypeError: cannot unpack non-iterable NoneType object
  bind-then-check -> found is None, the loud failure is reachable
  ```

  The `TypeError` escapes before any `assert` can run, which is what bypasses the loud failure this
  delegation is required to keep; binding first makes the `None` branch reachable. The stub returns
  `None` unconditionally because the `None` branch is the whole premise — a real `find_heading` would
  make the negative case unreachable and prove nothing about it.

**The five probes above are members of the carve-out population under the rule stated with the table,
and are entered as a separate block rather than appended to the eight `cf3a862` rows** — mixing rows
measured at two commits into one table is how a result cell acquires the wrong stamp. The eight rows
above are untouched and their `cf3a862` readings stand; the table below is read at `700c599`,
**v1.99's measurement commit** — named by revision number rather than by the deixis it carried
through v1.102 ("the freeze *this revision* is measured at"), which was four revisions stale by
`af19d53` and is the same class as the two repairs above. All five share one subject family (the CPython standard
library) and one stamp, and each is still given its own row, because a single row covering five
probes is the composite this section exists to argue against:

| Probe (all under §Measurements, above) | `git ls-files` argument | Result | Verdict |
|---|---|---|---|
| `json.dumps` line-breaking, per code point | `git ls-files json json.py` | empty | exempt; stamped `python 3.11.8 \| darwin` |
| The composite fixture run per member | `git ls-files json json.py` | empty | exempt; stamped `python 3.11.8` |
| `re.search` end-of-match on the `titled_section` selector | `git ls-files re re.py` | empty | exempt; stamped `python 3.11.8` |
| Buffered `TextIOWrapper` deferral **and** the `(st_dev, st_ino)` alias key | `git ls-files io.py _pyio.py os.py` | empty | exempt; stamped `python 3.11.8 \| darwin` |
| Unpacking `None` raises `TypeError` | `git ls-files '*/json.py' '*/re.py' '*/io.py' '*/os.py'` → **0** | no module to shadow | exempt; stamped `python 3.11.8` |

The last row's argument is deliberately not a module name: its subject is CPython's unpacking
protocol, which is the interpreter itself and has no stdlib file a repository could shadow, so the
runnable question is whether this repository vendors *any* file named like a stdlib module at all —
it does not, and that whole-tree `git ls-files` is the check. **With this block the population is
thirteen rows: the eight at `cf3a862` (seven exempt probes plus the non-exempt wrapper) and the five
here at `700c599`, twelve exempt probes in all and one not.** **Thirteen is screenable, and the
sentence this replaces asserted that it was not: the row selector the register paragraph above
already publishes returns exactly the thirteen rows, headers excluded.** That paragraph reads it
over the eight-row population as "the one thing every one of them carries and no other line in the
body does", and it still holds over the extended one —
(``git show <sha>:<doc> | awk '/^## Version History/{exit}{print}' | grep -c '^| .*`git ls-files ' ``)
returns **8** at `1cbddb7`, **8** at `700c599`, **13** at `8c6539a` and **13** at `b3be433`: the eight rows before this
block, the thirteen after it. It separates rows from the two header rows with no special case,
because the selector requires a space after the verb — every row goes on to give arguments, and both
header cells close their code span immediately after `ls-files`. **Residual, stated as the category
rather than as this table**: the selector is anchored at line start, so it counts *any* line
beginning `| ` that carries the row form — a row quoted verbatim at line start, in prose or inside a
fence, would be counted as a row. At this revision there is none, which is why the 13 it returns
*is* the thirteen rows rather than a bound on them, and it is the thing to re-check when a later
revision quotes a row. The hand count of the two tables is kept beside it as an independent
cross-check, not as the reason.

Two coarser readings are published as well, and the property the previous sentence claimed for both
holds of only one of them. `grep -cE '\`git ls-files [^\`]'` is **unanchored** and does count this
paragraph's own mentions: it reads **24** at `8c6539a` and **25** at `b3be433`, and it will move
by construction whenever this paragraph is reworded — it read **26** at one point during this
revision's editing, when the repair below was first written with the command spelled out in full
rather than described, and returned to **25** when that spelling was replaced by a description.
**That excursion is recorded as process and not as a figure**, because a reading of an
uncommitted intermediate tree is re-derivable by nobody; it is recorded at all because it is direct
evidence for the sentence above. **v1.100 stamped it "to a working tree and to nothing else",
which discouraged a check that is in fact available**: v1.100's working tree landed as `b3be433`
and its **25** reproduces there, by the same command with `git show b3be433:<doc> |` in front of
the `awk`. So the figure is stamped to **the working tree each revision produces, which lands as
that revision's landing commit** — checkable at a sha the round *after* it is taken, and not
before. A reader comparing it against any *other* landed commit is still comparing two different
bodies, which was the true half of the v1.100 sentence.
**The excursion above is this paragraph doing exactly what it says it does, and it was measured
rather than predicted**: naming the command in full moved the figure this paragraph publishes, and
the move was found by re-running after the edit and not by reasoning about it, which is the only
reason it can be reported at all.
`grep -cE '^\| .*git ls-files'` returns **15**, at `8c6539a`, at `b3be433` and over this working tree alike, and
counts **no prose line at all** — the thirteen rows plus the two header rows, nothing else — because
it is line-start anchored, the same property that makes the row selector above work. That 15 is a
**superset** of the rows and is what the `74e126f` check is
run over, which is sound in the direction that matters: `74e126f` appears in **0** of those 15
lines, so it appears in 0 of the 13 rows, which re-derives over the whole population the reading
the closure paragraph above states over "the eight rows".
The fence-body de-indentation case is still *not* a row
— its subject and stamp coincide with the scanner-grammar-corpus row, which is the condition the
bullet above gives for sharing a row, and none of these five shares a subject with an existing row.

**The stamp-driven driver is re-run over the extended population, because the rule it implements is
what put these five here and the next reader's first move is to run it.** Both readings are
published, since one of them is of a body that only exists in a working tree — per branch and then
the union, body-scoped, at the freeze and over this revision's working tree:
python-version **15 → 26**, `awk version [0-9]` **11 → 12**, `markdown-it-py [0-9]` **8 → 8**,
union **32 → 44**. **Those working-tree readings are of the body as it stood *before this paragraph
was written*, and this paragraph then moved them, which is the same self-match this revision
measured on the surface screen and is stated rather than hidden**: writing the resolution out quotes
two further python-version stamps and one further awk-version stamp, so re-run after v1.99's
last edit the same commands read python-version **28**, awk-version **13**,
markdown-it-py **8**, union **47**. The **44** is the number the assignment below partitions;
the **47** is the reading of v1.99's working tree, and the three-line
difference is this paragraph. **The 47 landed and reproduces at a sha** — `8c6539a` and `b3be433`
both return `28`/`13`/`8`/`47`, so it is checkable rather than stamped to a vanished tree, and
v1.100 moved none of the four. **v1.101's own working-tree reading is deliberately NOT published,
and the reason is a measurement rather than a preference**: two register bullets rewritten this
round each name a probe by its interpreter or renderer stamp, which the driver counts, and the
sentence assigning those two would have to quote the same stamps a third and fourth time — each
publication moves the figure it publishes, so there is no fixed point to state. Neither addition is
a new probe or a new carve-out row, so the **44** partition is untouched; what moves is the count
of *lines quoting a stamp*, which is what this driver measures and what it will keep doing every
time the register names a probe by its stamp. **The landed reading is the one to run**, and this
revision's is checkable at the commit that lands it, not before — the same rule this document
applies to every figure whose corpus is itself. **The twelve added lines are assigned by hand, published rather than left as a
reading**, exactly as the `cf3a862` resolution is and for the same reason — a partition nobody can
re-derive is not checkable whatever its total. Each of the five probes contributes **two**: its
table row and the `python 3.11.8` line inside its own recorded output (`| platform darwin` on the
census and the streams pair, bare on the other three) — **ten**. The remaining two are **not** probe
contributions: one is the class paragraph's prose about the stamp form ("Every one of the five is
stamped `python 3.11.8`"), the analogue of the single such line the `cf3a862` resolution already
sets aside, and one is the `awk version 20200816` stamp on the surface-carve-out screen's controls
under §Scope. **That last one is deliberately not a new row**: its subject is the `awk` build, which
is the existing `awk` boundary probe row's subject, and the screen it stamps is a screen over *this
document* and therefore carries a sha (`700c599`) as well — a probe carrying a sha is outside the
carve-out by the rule's own test. **One legible difference from the seven above, said so a reader
does not mis-assign**: those seven each stamp their prose *and* their output, while these five carry
no inline stamp on their individual prose — the class paragraph stamps all five at once — so the
count per probe is two by a different route and the eleventh line is what makes the arithmetic
close.

## Convention Prerequisites

- Feature branch created at Phase 5c before any implementation commit.
- Verdict-token discipline: read the token, never `$?`; every verdict exits 0 and only
  `UNREADABLE`/`CLEANUP_FAILED`/`LAUNCH_FAILED` exit 2 (FR-4, AC-4.2); a refusal carries no count readable
  as a **measured result** (never `rc=`), though it may carry a diagnostic count saying why it
  could not judge — see the count rule under Implementation Strategy, and AC-4.3/AC-4.4.
- Every guard mutation-tested with a per-mutation named test, scored on the pytest summary.
- Registry entry and emittable detail lines pinned bidirectionally.
- Full suite run alone before the Phase 5f gate; scoped green is not suite green.
- **Portable time bounds, and why `hmad-dispatch run --timeout` is not the mechanism here.** The
  invariant forbids the shell forms `timeout <s> <cmd>` / `gtimeout <s> <cmd>`, because both rest
  on coreutils that macOS does not ship, and prescribes `hmad-dispatch run --timeout` as the
  replacement **for a shell-command time bound**. This helper is not a shell command: it is a
  stdlib Python module whose bound is `Popen.communicate(timeout=…)` — neither forbidden form, and
  no external CLI. Routing it through `hmad-dispatch` would make a module the design requires to
  run from a bare clone depend on a wrapper script, which is the very dependency the same
  invariant family exists to prevent (§"Skill self-containment", §"No new external dependency").
  So the invariant is satisfied, not waived. Recorded explicitly because the plan previously said
  only "the bound is Python's own", which cannot be distinguished from having overlooked the rule.
- No new external dependency; no `timeout`/`gtimeout` **invocation** — the source legitimately
  contains `timeout=`, `TimeoutExpired`, `BlockTimeout` and `--shell-timeout`, and a substring
  ban would reject the design that satisfies the invariant (AC-5.3).

## Success Criteria

- Every AC in the spec passes an automated test — **49** anchors, re-derived at spec v1.60 /
  the freeze `4e4a00c` by
  `git show 4e4a00c:docs/01-plan/features/doc-block-exec.spec.md | grep -cE '^  - AC-[0-9]+\.[0-9]+:'`
  (it was **49** at spec v1.59 / `6f0ee85` too), and each is
  unique: the same body through `grep -oE '^  - AC-[0-9]+\.[0-9]+:' | sort | uniq -c | awk '$1>1'`
  prints nothing at the freeze. The unit is *body-line AC anchors*, not ACs mentioned — a bare `AC-6.4` appears
  many times over in that document's §Version History. **The grep is
  the assertion, not this sentence**: the count went stale three times when it was carried as a
  bare number, so it is re-derived on every spec bump — but a spec bump that leaves the count at
  49 does not stale this line, which records the last version at which the re-derivation was
  done and the command that does it.
  **Every `spec v1.NN` label in this document is read the same way** — it records the spec revision
  at which the premise beside it was last re-derived, never a claim that the spec still ships that
  version. Three different labels therefore sit in this body legitimately, and all three premises
  were re-run at the freeze `4e4a00c`, each with its own command rather than as one assertion:
  AC-6.1's spelled-out sweep (v1.55) — `grep -c 'stated here rather than by reference'` on the spec
  → **1** and `grep -c 'same sweep as the plan'` → **0**; AC-6.4's two-source tuple rule and
  its `len(tuple)` floor (v1.56) — `grep -c 'len(tuple)'` on the spec → **2**, the rule and the
  floor, which is why that label is cited twice; and this AC count (now v1.60) — the **49** above.
  Through v1.94 the three were re-stamped together on the strength of the AC count alone; they are
  three separate premises and are now re-run as three.
- FR-6's wire is discriminated in both directions: reverting the connection alone fails a named
  caller test while the helper's own suite still passes, and an unconditional call site fails a
  named test too.
- All three mutation specs (`doc_block_exec.json`, `doc_block_exec_wire.json`, `docsections.json`)
  report `ALL_CAUGHT`, each mutation killed by its own named `test`, scored on the pytest summary.
- The full suite passes at no lower a count than the pre-change baseline plus this feature's tests.
  **The baseline is cited, not remembered, and it is cited WITH the commit it was measured at,
  because it drifts.** Re-measured at `e8eaf6f`, before any implementation commit, from the repo
  root:

  ```
  $ python3.11 -m pytest --collect-only -q | tail -1
  2748 tests collected in 0.40s
  $ python3.11 -m pytest -q -p no:cacheprovider | tail -1
  2748 passed in 383.05s (0:06:23)
  ```

  It was `2747` at `6b4df35`; `b59e05e` then added one test to
  `h-mad/tests/test_h_mad_assemble_audit.py` and the plan was not re-measured, so for a while the
  floor asserted `>= 2747 + …` against a real 2748 — which let **exactly one** pre-existing test be
  deleted with the floor still green, falsifying the no-hidden-deletion guarantee this bullet
  exists to make. That is the failure mode of a remembered number, and it recurs by construction:
  **any** commit landing a test outside this feature moves it again. So the number here is the
  value at the named commit and nothing more, and the residual is stated rather than implied — the
  floor MUST be re-measured at 5c branch time and the two numbers below updated in the same commit
  that creates the branch. A floor carried across an unmeasured interval proves nothing. **The
  drift is live, not theoretical**: the same collect command at `a8e0372` returns `2808 tests
  collected`, sixty above the `e8eaf6f` baseline. That number is deliberately **not** adopted here
  — the baseline has to be measured at the 5c branch commit, not at whatever HEAD an audit cycle
  happened to sit on, or the floor once again asserts a value from a commit nobody branched from.

  The second command is quoted as it was run for the baseline; as a **gate** it is written so the
  exit status survives — a bare pipe reports `tail`'s status and would let a red suite print as
  success:

  ```
  ( cd "$(git rev-parse --show-toplevel)" && hmad-dispatch run --timeout 1200 -- python3.11 -m pytest -q -p no:cacheprovider ) > /tmp/doc_block_exec_suite.log; RC=$?   # from the REPOSITORY ROOT, as the spec's AC-6.4 spells it
  tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"      # gate on BOTH lines; rc=124 is the wrapper's expiry, not a suite result
  ```

  **Every 5f command is bounded** through `hmad-dispatch run --timeout <s> -- …` (the base Portable
  time bounds invariant; `timeout`/`gtimeout` are not macOS components): the wrapper propagates
  the wrapped command's exit status and reports 124 on expiry. **This probe carries a sha, not a
  date, because its subject is tracked** — see the carve-out sweep under §Measurements; a stamp of
  `2026-09-03` stood here through v1.92 and `3f50b95` changed this exact behaviour the next day.
  Re-run at `6f0ee85` against `h-mad/bin/hmad-dispatch` (the tracked script, invoked by path, not
  whatever `hmad-dispatch` resolves to on `PATH`):

  ```
  $ h-mad/bin/hmad-dispatch run --timeout 5 -- sh -c 'exit 3'; echo "rc=$?"
  rc=3
  $ h-mad/bin/hmad-dispatch run --timeout 1 -- sleep 3; echo "rc=$?"
  hmad-dispatch: run_timeout after 1s — sleep 3
  rc=124
  ```

  So the captured status and the `SUITE:`/`MUTATION:` tokens survive it. Bounds: 1200 s for the
  full suite — **derived as three times the 383 s baseline, 1149 s, rounded up to 1200**, and the
  rounding is stated because "three times 383" is 1149: an exact-multiple wording made this
  sentence assert a derivation that does not produce its own number, and the slack above 1149 is
  deliberate ceiling, not arithmetic (the baseline is the **383 s** quoted above at `e8eaf6f` — `2748 passed in
  383.05s`; the bound was written as "three times the 397 s baseline" when the baseline was
  `2747 passed in 397.40s` at `6b4df35`, and the v1.84 re-measurement updated the quoted output
  without sweeping this sentence, which is exactly the number-corrected-in-prose-but-stale-beside-
  its-command class the floor fix set out to close — re-derive it from the quoted output at 5c
  rather than carrying it), 600 s for the scoped run and for each mutation-harness
  invocation. **What the impl-plan currently carries is deliberately not stated here** — a sibling
  is revised in the same commit as this document, and this clause previously asserted a stale
  `397 s` there, an assertion that outlived the defect it reported. The 5f wrapped commands live in
  the impl-plan; whether its derivation matches this one is a question for the round that audits
  both, not a claim this document can carry.

  So AC-6.4's floor is 2748 collected and the same number passing (at `e8eaf6f`; re-measure at 5c), plus every test this feature
  adds — and "every test this feature adds" is computed, not estimated: the collected count of
  `h-mad/tests/test_h_mad_doc_block_exec.py` run through the collector alone (the floor test itself
  runs `pytest --collect-only -q` in a subprocess with `cwd=REPO_ROOT`, the repository root the
  baseline was taken from — a different cwd is a different tree), plus a fixed tuple
  of the node IDs added to existing files.

  **The cwd is load-bearing, so the pair proving it is stated at one sha, with its unit.** At
  `6f0ee85`, `python3.11 -m pytest --collect-only -q -p no:cacheprovider | tail -1` returns
  **2809 tests collected** from the repository root and **2547** from `h-mad/`. Through v1.92 this
  was a bare `2486` with no command and no sha: it does not reproduce, and carrying no sha it could
  not be shown ever to have been right, which is the whole reason the provenance rule exists. Both
  figures move with the suite and are re-derived rather than carried. The root figure was `2808` at
  `a8e0372` in the probe below, and the `+1` is accounted for rather than shrugged at — the only
  commit touching `h-mad/` or `handoff/` between those two commits is `335f535`, and
  `git show 335f535 -- 'h-mad/tests/*' | grep -c '^+def test_'` → **1**.

  **The tuple's membership is fixed by a rule the spec
  owns, and this plan enumerates the rule's current members rather than restating the rule** — two
  independently-worded versions of one rule is how the corpus contradiction above started. Spec
  v1.56, AC-6.4 states it: the tuple is (1) nodes added directly to a consumer file, plus (2) **one
  node per glob-parametrised test, per new file this feature adds under `h-mad/scripts/`**, and the
  nodes from (2) must *pass*, not merely be counted. The spec deliberately carries no total, and
  the floor is written `len(tuple)` there. **Evaluated at `335f535` the rule yields nine** — a
  dated evaluation of the spec's rule, never the contract, which is and stays `len(tuple)` — and
  the derivation is written out so the next reader re-derives instead of carrying the number:
  `ls h-mad/scripts/*.py | wc -l` → **37** at `335f535` and **37** again at the freeze `4e4a00c`
  (the glob is the operative command,
  because that is the shape `_SCANNED` itself uses; `git ls-files 'h-mad/scripts/*.py' | wc -l` →
  **37** too at both, which is the build-artifact control — no untracked `.py` is
  inflating it. The freeze re-run is recorded because `335f535` predates the closure's left edge
  `74e126f`, so the closure cannot reach this figure however far its right-hand side is extended —
  it is the eleventh hit of the corpus-shape driver above and the one that surfaced only when that
  driver stopped keying on the command's spelling); `test_h_mad_portable_timeout.py` builds `_SCANNED` at
  module level from members including `*sorted((SKILL / "scripts").glob("*.py"))` and parametrises
  over it twice (`grep -c 'parametrize("path", _SCANNED' h-mad/tests/test_h_mad_portable_timeout.py`
  → **2** at `335f535`); Task 1 adds one file under that directory, so source (2) contributes
  2 × 1 = **2**, and source (1) contributes the **7** consumer-file nodes below. Nine is the
  rule's value at a commit, not a constant: **re-derive it at 5c**, in the same commit that
  re-measures the `2748` floor above and for the same reason — a second new script, or a third
  glob-parametrised test over that directory, changes it. **The members are addressed by their
  SOURCE and never by an ordinal**, which is the same rule §FR-6 applies to the injection seams and
  to the four `docsections.json` connection rows: an ordinal over an enumeration the paragraph
  above says will move restales on any addition or removal, and keying by source does not. The
  members at `335f535`. **Source (1), authored in
  `h-mad/tests/test_h_mad_collect_report_docs.py`**: `test_gate_block_resolves_through_doc_block_exec`, `test_recipe_runs_through_run_block`, `test_gate_block_refuses_an_untagged_recipe`, `test_exec_block_scan_performs_no_execution`, `test_consumer_calls_the_helper_module_qualified`, `test_only_the_exec_scan_hand_rolls_extraction`. **Source (1), authored in `h-mad/tests/test_docsections.py`**: `test_docsections_delegates_to_the_authoritative_bounder` (it must live beside the module it spies on, which is where `docsections.json` binds it).
  **Source (2) is written by nobody** — its two members are:
  `h-mad/tests/test_h_mad_portable_timeout.py::test_no_document_or_script_emits_a_bare_timeout_command[h_mad_doc_block_exec.py]`
  and
  `h-mad/tests/test_h_mad_portable_timeout.py::test_no_document_or_script_rests_on_an_unconditional_absence_claim[h_mad_doc_block_exec.py]`.
  Per the spec's rule these must **pass**, which is an obligation on Task 1's source and not merely
  on the floor arithmetic: the new module must carry no bare `timeout <n>` form and no
  unconditional absence claim (§Convention Prerequisites already requires the first; this is where
  the requirement becomes a named node).

  **The plan's own contribution here is the empirical check of the spec's rule, not a second
  statement of it.** The rule predicts that exactly one of this feature's three new-artifact
  classes moves an existing file's collected count, and by two. Probed at `a8e0372`:

  ```
  # baseline
  $ python3.11 -m pytest --collect-only -q -p no:cacheprovider | tail -1
  2808 tests collected in 0.44s
  # (a) a scratch h-mad/scripts/*.py, collect, delete
  2810 tests collected in 0.42s        # +2, both ids `[<scratch>.py]` in test_h_mad_portable_timeout.py
  # (b) a scratch h-mad/tests/test_*.py holding no test functions AND
  # (c) a scratch h-mad/tests/mutation-specs/*.json, both present in ONE run, collect, delete
  2808 tests collected in 0.41s        # +0 for (b) and (c) together, so +0 for each
  ```

  The prediction holds: `+2` for a new `h-mad/scripts/*.py`, `+0` for the other two classes. That
  is the spec's residual measured rather than reasoned — it distinguishes a glob in `parametrize`
  argvalues from a glob looping inside a test body, which is the distinction the whole rule turns
  on and which a grep for `glob(` alone cannot make. **Re-run this probe at 5c**, in the same
  commit that re-measures the floor and re-derives the tuple: a glob-fed parametrisation landed in
  the meantime changes the membership, and the probe is what detects it.
  Each member of the tuple is asserted to exist by node ID. Every other new test — FR-1..5, AC-1.8's source assertion and
  collect-alone pins, the CLI table walk — lives in the new module and is counted by the collector.
  `test_suite_floor_holds` asserts `full_collected >= 2748 + new_module + len(tuple)` — written as
  `len(tuple)` and not as a literal, exactly as spec v1.56 writes it, so the assertion cannot go
  stale when the enumeration above is re-derived; evaluating the enumeration above at `335f535`
  gives `len(tuple)` = **9**, which is a dated reading of the assertion and not the assertion — from a
  `--collect-only` subprocess, which never executes tests and so cannot recurse (an env guard
  `DOCBLOCK_FLOOR_INNER=1` also makes any inner instance skip); the *pass* half is the Phase-5f
  gate command run alone, outside the suite, and recorded in the report. A deleted pre-existing
  test cannot hide behind the additions.
- `git status --porcelain` is unchanged across a run of a block that writes files.
- No hand-written ` ```bash ` extraction remains on the **executing** path of
  `h-mad/tests/test_h_mad_collect_report_docs.py` — the gate-block extractor and `run_recipe` (hoisted to `_run_recipe`) both route through
  the helper. The exec-codex scan keeps its text scan **by decision**: it selects a different, untagged block
  (`exec codex`) that must never be run, so an executor which returns only tagged blocks cannot
  serve it. A test asserts the exec-codex scan performs no execution, so the exemption is pinned rather than
  assumed.
- Exactly one fence in the tree carries the tag at the end of this feature.

## Out-of-Scope (confirmed from spec)

- Any blanket or directory-wide sweep of the bash fences under `h-mad/` and `handoff/` — **73 at
  `a8e0372`** by the §Measurements census, 68 at `a469493`; the exclusion is of the *sweep*, so no
  scope call here turns on the count, which is precisely why this surface goes unswept when the
  number moves and why the sha is written beside it.
- Tagging any fence beyond the Second-surface gate block.
- A `name=` addressing key on the info string.
- A `--list` mode enumerating tagged blocks.
- Languages other than bash.
- Executing blocks in another repository or in the installed skills copy rather than the checkout.

## Next Steps

This plan and the paired design are audited together, each cycle on **two different surfaces**,
until **both** documents gate `must=0 should=0` on the **same** commit — the plan is a gated
document of the design's stamp, so a plan edit re-opens the design and vice versa.
**The criterion is stated structurally rather than by naming the legs**, because the legs are
routed by availability and a named pair stales the moment the routing changes — which it already
has, and this sentence named the superseded pair while the round that would stamp it ran on
another. Two conditions, both of which any admissible pair must meet: the pair is two *different*
surfaces per `h-mad/SKILL.md` §"Never gate on one audit pass" (never two passes of one surface),
and **at least one of them reads the working tree in the cycle it reports on** — a plan whose
substance is tree-derived counts cannot be gated by consistency-checking alone. Which concrete
surfaces satisfy that is SKILL.md's to route and this document's to obey; naming them here, or
asserting what each one does, is what went stale.
**The standing debt this ledger existed to track is DISCHARGED at `af19d53`, and the paragraph is
rewritten in the past tense rather than deleted, because the gap it records is the evidence for the
rule.** From cycle **72** through cycle **85** every audit of this document ran on the substitute
leg alone; **`4c1c3a5` landed the cycle-86 `codex` report**
(`git log --oneline --diff-filter=A -- docs/01-plan/features/doc-block-exec.plan.audit.v86.codex.md`),
so at `af19d53` both halves read `86`. **Whether the halves were ever equal before `af19d53` is not
claimed here — it was not measured**, and the series below reports only the eight shas it was run
at. The rule the debt motivated does not lapse with the debt. This figure's corpus is `docs/01-plan/features/`, which the §Measurements closure
explicitly excludes, and — unlike every other figure in this document — **that corpus is one this
very round writes into**, because the round's own audit report lands in it. So the figure is not
merely re-derivable at a sha; it is **stale by construction the moment the next report is written**,
and it must be re-measured on every revision, without exception. **Both halves, re-derived by v1.103
at `af19d53` — this revision's one measurement commit — with the
sha inside the command so the reading is reproducible without a working tree:**

```
git ls-tree -r --name-only af19d53 -- docs/01-plan/features/ \
  | grep -E 'doc-block-exec\.plan\.audit\.v[0-9]+\.codex\.md$' \
  | sed 's/.*audit\.v//;s/\.codex\.md//' | sort -n | tail -1      # -> 86
git ls-tree -r --name-only af19d53 -- docs/01-plan/features/ \
  | grep -E 'doc-block-exec\.plan\.audit\.v[0-9]+\.teammate\.md$' \
  | sed 's/.*audit\.v//;s/\.teammate\.md//' | sort -n | tail -1    # -> 86
```

**codex `86` against teammate `86` at `af19d53`.** `00b961f` appears below only as the stamp on the
reading v1.102 took; it is **not** a second answer to which commit this revision is measured at,
and v1.102 named it that way at this site while naming `dfae038` in §Measurements — two answers in
one revision, filed by both gating legs, and the repair is stated in full at the measurement-commit
paragraph there.
The series, one run of the command above per sha, is the whole argument, extended and with no row
re-stamped: `1cbddb7` **72/83** ·
`700c599` **72/83** · `8c6539a` **72/84** · `b3be433` **72/84** · `00b961f` **72/85** ·
`dfae038` **72/85** · `3f70eb3` **72/85** · `af19d53` **86/86**.
**Every attribution below is a pointer into that series and not a restatement of it**, which is the
repair of a defect both gating legs filed: v1.102 wrote "v1.101's published pair was `72`/`83`"
four lines above the row saying otherwise. Read off the series: **v1.101 published `72`/`84`,
stamped `b3be433`** — correct where it stood, and outrun by v1.101's own landing commit `00b961f`.
**`72`/`83` stamped at `1cbddb7` is what v1.99 and v1.100 published**, and it is those two
revisions, not v1.101, that carried a half already wrong at the commit each was authored against —
which is what "without exception" was written to prevent. **The class, widened from v1.102's
integers rule to attributions**: any claim this document makes about which revision published which
value, where the series is printed on the same page, is written as a pointer into that series and
never as a free-standing restatement, so the reader's check is reading the row. Residual: the rule
makes the summary re-derivable from the series and says nothing about whether the series is right,
which is why every row of it was re-run at its own sha for this revision.
v1.99 landed at `8c6539a` and
v1.100 was measured there; the v84 gating report is the file that moved the teammate half to `84`
in that same commit, so the figure went stale *inside the round that carried it* and neither the
v1.99 nor the v1.100 Version History entry mentions the ledger at all. Earlier motion is the same
mechanism: `72`/`82` at `6dcb70f`, and through v1.96 the pair was carried at `4e4a00c` (`72`/`81`)
inside the sentence saying it must not be carried. **The class, stated over the axis rather than
over this figure**: a figure whose corpus is a directory the round itself writes into cannot be
carried across a revision under any argument, because the commit that lands the revision is also
the commit that lands the report — so the rule is that this pair is re-run at the commit each
revision is measured at and the reading is published, **or the revision's own entry records that it
was not run**, the register below being the only other place a non-run is admissible. **Residual,
and it is exact**: even a reading taken at the round's own measurement commit is correct only until
that round's reports are committed. **v1.101's own reading was outrun exactly as its residual
predicted** — it published `84` at `b3be433` while the two v85 reports sat uncommitted beside it, and
`00b961f` landed them and took the half to `85`, which is why v1.102's pair was stamped there and
not carried. **v1.102's reading was outrun the same way and its own entry predicted it**: `72`/`85`
was correct at `00b961f`, `dfae038` and `3f70eb3`, and `4c1c3a5` landed the round-fifteen reports
and took the pair to `86`/`86`. **That is three consecutive revisions outrun by their own round's
reports, which is the residual being right three times and not a new defect.** The same prediction
applies to the reading above: `86`/`86` is correct at `af19d53` and stops being correct the moment
round sixteen's own reports are committed, so v1.104 re-runs it at its own measurement commit rather
than reading this line.
**Three further residuals, each a way the figure has actually gone wrong or provably can.** (1) **The unit is the highest cycle number, not a
file count**, and the two forms disagree: the same pipeline with `grep -c` in place of the
`sed | sort | tail` returns **72** codex / **12** teammate at `b3be433`, **72**/**13** at
`00b961f` and **73**/**14** at `af19d53` — the codex reports ran `1..72` contiguously and cycle
`86` is the first since, so at `af19d53` a reader who takes the published `86`/`86` for a file
count is off by `86 - 73` on the codex half and `86 - 14` on the teammate half, the arithmetic
being over the two pairs printed in this sentence rather than a free-standing figure. (2) **The
`ls`-based form this paragraph carried through v1.96 reads the *working tree*, not a commit**, so it
diverges from any sha whenever an uncommitted report sits in that directory. **The divergence is
demonstrable at a pair of shas and is demonstrated that way, because a working-tree reading is
re-derivable by nobody**: the two v85 reports were uncommitted while v1.101 was being written and
landed in `00b961f`, so an `ls`-based reading taken in that window returned `85` against a
`git ls-tree b3be433` reading of `84`, and the two agree again at `00b961f` where both read `85`.
**The two `ls-tree` endpoints are measured; the `ls`-based `85` in between is an inference from when
the reports were written and when they landed, not a reading anyone took at each moment of the
window, and it is labelled as one rather than published as a series.**
**v1.101 published this as `git status --porcelain … | grep -c` returning `2` "right now", and that
is not a figure**: `git status --porcelain` has no form that runs at a sha, so no reader could
reproduce the `2` at any commit, and run as written after the reports landed it returns `0` — the
same command, the same repository, a different answer, with nothing in the sentence saying which
tree the reader is in. **The class, and it is the subject of this residual applied to the sentence
stating it: a reading of an uncommitted working tree is recorded as a dated observation and never
published as a figure**, exactly as the `25`→`26`→`25` editing excursion two sections above is
recorded; where the divergence itself is the point, it is shown by pairing two `git ls-tree`
readings at two shas, which is what the sentence above now does. Residual on that: a pair of
`ls-tree` readings shows that the halves *did* diverge across an interval and cannot show that they
are diverging at the moment of reading, and nothing re-derivable can.
The `git ls-tree` form is the one with a sha on it and is the one to run. (3) The comparison says
nothing about *quality*: a codex cycle numbered `72` and a teammate cycle numbered `84` are both
just filenames, and the gap is a statement about which surface ran, never about what either found. A
`must=0 should=0` reached without codex is provisional until one real codex round runs on the
landed document. Recorded here rather than in a Version History entry, because that is where the
last standing rule went to be ignored. When both stamps read `CURRENT`, Phase 5 begins with the impl-plan (5a),
which pins the exact mutation anchors and node IDs this plan and the design's matrix name.

## Version History

- v1.0: Initial plan draft.
- v1.1: Audit v1 fixes: cite both measurements in a Measurements section, plan FR-6 as a wiring task with two-direction discrimination, state the stdout/stderr transport, narrow the temp-cwd isolation claim.
- v1.2: Audit v2 fixes: state the count rule precisely so it no longer contradicts AC-4.4, and specify the stdout/stderr arguments as optional with a pre-run refusal.
- v1.3: Audit v3 fixes: the count rule's third surface in Convention Prerequisites (my v1.2 sweep grepped one phrasing and missed it); name the FR-6 wire mutation spec path.
- v1.4: Track the spec's AC count to 38 after design audit v2 added AC-1.8, AC-2.6 and AC-2.7.
- v1.5: Design audit v3: the paired-plan surface of the AC-5.3 invocation-versus-substring fix.
- v1.6: Design audit v4 back-propagation: docsections.py is now in scope, replacing its duplicate bounder with an import of the authoritative one.
- v1.7: Plan re-audit v5: only the executing call site migrates — :270 and :412 select different blocks (measured, 4 blocks in the section), so the earlier 'both extractors break' claim was false and AC-6.2 was unsatisfiable; add docsections.py to Deliverables.
- v1.8: Plan re-audit v6: same, plus a risk row recording where the mktemp-d wording came from.
- v1.9: Plan re-audit v7: the AC count went stale a third time; anchor it to the spec version and record how to re-derive it.
- v1.10: Plan re-audit v7: scope AC-5.2 to the launched process group (a setsid descendant escapes, measured); refuse aliased --stdout/--stderr (AC-3.9); correct the risk row that still claimed both extractors break.
- v1.11: Plan re-audit v8: the Success Criteria still demanded removal of every hand-written extraction, contradicting the FR-6 decision that :412 keeps its non-executing text scan.
- v1.12: Plan re-audit v8: add the fixture preamble boundary (AC-3.11/AC-3.12) — without it the gate block's COLLECT_OUT is unbound under strict bash and the FR-6 migration cannot reach GATE: PASS.
- v1.13: Plan re-audit v9: track the AC count to 43 after the duplicate-heading refusal.
- v1.14: Plan re-audit v10: state why the portable-time-bounds prescription does not transfer to a stdlib module (its premise about this helper does not hold); name the full launch/reap/cleanup sequence; correct the preamble causal claim on its seventh surface.
- v1.15: Plan re-audit v10 (agy): reconcile the docsections measurement with the later decision to change that file — the tag was never the reason, the duplicate bounder is.
- v1.16: Plan re-audit v11: specify the tests/->scripts/ import (self-contained sys.path insert, collect-alone test, docsections.json re-point); cite the AC-5.2 in-group/escape/ProcessLookupError probe with its command and output; add the task-level API and caller map; name the FR-6 wire tests and the mutation each kills; track the AC count to 46 (spec v1.13); add the cleanup-verification risk row.
- v1.17: Plan re-audit v12 (codex must 2 should 1; agy clean): name the bounder fence_aware_end(text, start, level) -> int and its two call replacements in docsections; make every consumer call module-qualified (dbe.*) so the wire spies observe it, pinned by a no-from-import test; cite the collected and passing baseline (2747/2747 at 6b4df35) with commands.
- v1.18: Plan re-audit v13 (codex must 3 should 1; agy clean): state the full CLI contract including --preamble-file and its pre-spawn refusal; cite the AC-3.14 cleanup probe (python3.11, euid 501) and add the root-skip plus fault-injected fallbacks; replace 'anchors pinned at impl-plan time' with the author-together / re-read / harness / named-RED ordering; define stream overwrite and reservation semantics (stream_write_failed).
- v1.19: Plan re-audit v14 (codex must 1 should 1; agy clean): preamble/block composition rule with its no-final-newline test; allow_abbrev=False with an abbreviated-option rejection test.
- v1.20: Design audit v6 back-propagation: composition with the substituted text; probe-then-reserve stream artifacts; BAD_TIMEOUT and the values-vs-grammar CLI policy; RunResult streams are UTF-8/replace str.
- v1.21: Design audit v7 back-propagation: append-mode reservation after every check with truncation at the final write, and its four tests; docsections.json converts all four mutations to the named-test form; the AC-6.4 floor is computed by test_suite_floor_holds.
- v1.22: Design audit v8 back-propagation: exit-code partition per the base invariant; substitute returns a new Block and run_block takes no subs; the five named consumer-file tests enumerated; floor test topology (collect-only subprocess, env guard, pass half outside the suite); main's order corrected (info string in extract, ordinal in select).
- v1.23: Design audit v9 back-propagation: descriptor-level alias check; the suite gate command captures the exit status; AC count 48 (spec v1.19).
- v1.24: Design audit v11 back-propagation: --subst contract in the CLI paragraph; alias check after reservation; LaunchFailed in the run_block row; AC count 49 (spec v1.21).
- v1.25: Design audit v13 back-propagation: Deliverables and Success Criteria name all three mutation specs and point at the design's enumeration; the FR-6 pseudocode unpacks substitute's (Block, counts) tuple (agy nit).
- v1.26: Design audit v14 back-propagation: helper mutation spec is 28 mutations plus the AC-5.3 self-check.
- v1.27: Design audit v15 back-propagation: LAUNCH_FAILED named in both partition summaries; the stream-write-failure tests name the _final_write seam and the partial-write case; 31 mutations plus the self-check.
- v1.28: Design audit v16 back-propagation: 33 mutations plus the self-check.
- v1.29: Design audit v17 back-propagation: 34 mutations plus the self-check.
- v1.30: Design audit v18 (codex must 2 should 1 nit 1; agy clean): docsections delegates through a module-qualified alias and carries its own wire mutation (docsections-delegation-reverted); importer census corrected to three files with the command; 36 mutations plus the self-check.
- v1.31: Plan re-audit v16 (codex clean + 1 nit; agy must 1 + 1 nit): substitute's row names BadSubstArg; five functions, not four; AC anchor cites spec v1.26.
- v1.32: Plan re-audit v17 (codex must 2 should 1; agy clean) + design audit v21: fence_aware_end's contract names tilde runs and the 0-3 indentation rule with its tests and mutations; mutation-spec binding rule (root, command, target_command, full node IDs) for both new specs; extract's doc is a path; the naturally-emptied-group probe cited with poll()-first; five functions plus main; 37 mutations.
- v1.33: Plan re-audit v18 (codex must 1; agy clean): docsections.json test keys are full node IDs; 38 source mutations; FR-4 summary states the invariant's class rather than claiming it names the tokens.
- v1.34: Plan re-audit v19 (both surfaces clean; agy nit): the delegation spy is installed on docsections._dbe.
- v1.35: Plan re-audit v20 (codex must 2; agy clean): the body de-indentation rule on extract with its test and mutation; _final_write flushes and closes inside the mapped region; both stream-failure branches; invalid-UTF-8 preamble test; CLEANUP_FAILED os_error detail; 39 mutations.
- v1.36: Plan re-audit v21 (codex must 2 should 1, one must REFUTED — the census re-measures 68/10 from the root, the reported 49/2 is a subdirectory run; agy clean + nit): the reservation protocol carried into the plan; the mutation matrix pointed at by section; _dbe. prefix in the docsections pseudocode.
- v1.37: Plan re-audit v22 (codex should 1 + nit; agy clean): closer must be followed only by blanks, with its fixture and mutation; control census command cited; docsections.json is two-leave-two-stay; six consumer-file tests; 40 mutations.
- v1.38: Plan re-audit v23 (both surfaces clean) + design audit v27 back-propagation: seven-test floor tuple incl. the docsections delegation spy; the wire-revert-extract regex is tag-tolerant by intent; 41 mutations.
- v1.39: Plan re-audit v24 (codex must 1; agy clean): the post-close read-back verification carried into the stream paragraph; mutation accounting names the two SKILL.md rows.
- v1.40: Plan re-audit v25 (codex must 1 should 1; agy nit) + design audit v29 (codex must 1; agy must 3): the mutation count is re-derived from the design's matrix (43 = 41 + 2); the FR-6 table names all seven floor-tuple node IDs; Next Steps state the dual-surface same-commit gate; AC anchor at spec v1.34.
- v1.41: Plan re-audit v26 (codex must 1; agy clean) + design audit v30 back-propagation: fence_aware_end establishes fence state over the prefix; 48 mutations (46 + 2) after the four main/I-O rows and the prefix row.
- v1.42: Plan re-audit v28 (codex must 1 should 2; agy should 1): the timeout risk row requires poll() before killpg; _final_write closes in a finally; the AC count line records its re-derivation (49 at spec v1.35) and no longer stales on a count-preserving spec bump.
- v1.43: Plan re-audit v29 (both surfaces clean) + design audit v33 (agy must 1 + nits): the invalid-UTF-8 preamble test carries the matrix's node ID on every surface; select's Sequence[Block] hint; PATH placeholder.
- v1.44: Plan re-audit v30 (both surfaces clean) + design audit v34 (codex must 1; agy must 1 + nits): the three wire guards get mutants (six wire mutations); test_docsections.py in Deliverables; run_block's keyword type hints.
- v1.45: Plan re-audit v31 (both surfaces clean) + design audit v36 back-propagation: the bounder's prefix state is built from complete lines through the line containing start; 49 mutations.
- v1.46: Plan re-audit v32 (codex must 1; agy clean): the resolver splits into _gate_block() -> Block and _gate_bash_block() -> str (= .text), so the file's two text-pin callers keep their type and nothing else moves; the wire mutation targets _gate_block.
- v1.47: Design audit v38 back-propagation: the bounder rule names the backtick-in-info prohibition; 50 mutations.
- v1.48: Design audit v39 back-propagation: 52 mutations (50 + 2).
- v1.49: Plan re-audit v35 (codex must 1; agy see report): the reservation paragraph carries O_NONBLOCK on the existing-file arm and the regular-file check with its FIFO test and two mutations; the stale 'third stays' fragment removed; 54 mutations.
- v1.50: Plan re-audit v36 (codex must 2; agy clean): the launch passes cwd=cwd with its mutation; the one-private-scanner rule (_fence_events) with its trace test and mutation; the reader-less-FIFO probe cited; 55 mutations.
- v1.51: Design audit v43 back-propagation (spec v1.38): _close_stream backstop with the stream_close_failed selection and its two tests/mutations; the ENOTDIR reservation test; 59 mutations (57 + 2).
- v1.52: Design audit v44 back-propagation: 60 mutations (58 + 2).
- v1.53: Design v1.51 back-propagation: 61 mutations (59 + 2).
- v1.54: Plan re-audit v40 (codex must 1; agy clean): docsections.json gains docsections-syspath-setup-removed bound to test_docsections_imports_from_an_unrelated_cwd (six rows).
- v1.55: Design v1.53 back-propagation: docsections.json binding sentence; eight wire mutations (wire-revert-select, wire-revert-substitute).
- v1.56: Plan re-audit v42 (codex must 1 should 1, both answered by impl-plan v1.3; agy clean) + design v1.54 back-propagation: _run_recipe naming.
- v1.57: Design v1.56 back-propagation: 62 mutations (60 + 2).
- v1.58: Design v1.58 back-propagation: scanner grammar corpus in §Measurements (markdown-it-py 2.2.0, 14/14); find_heading (seven public names); docsections.json seventh row.
- v1.59: Plan re-audit v45 (codex must 1) + design v1.59 back-propagation: titled_section's replacement calls find_heading for (start, level); find_heading in the API table.
- v1.60: Plan re-audit v46 (codex must 1 should 1; agy clean): heading selector differential in §Measurements (30 files, new_only=0, old_only=76); run_block timeout=60.0 in the migration; 63 mutations.
- v1.61: Plan re-audit v47 (codex must 2; agy clean): the bounder wording and its API row carry the >= start predicate; the delegation-revert claim names the source-guard exception.
- v1.62: Plan re-audit v48 (codex must 1 should 1; agy clean) + design v1.61 back-propagation: 67 mutations; test_parser_rejects_all_dir_and_abbreviations named on both surfaces; corpus on both renderer versions.
- v1.63: Design v1.62 back-propagation (design audit v58 codex must 1): docsections-delegation-reverted is connection-only (a private spec_from_file_location instance replaces the shared import); the WIRE-PIN's mechanism is stated as the impl-plan has it — a sys.modules fake bound by importlib.reload, since a setattr spy on docsections._dbe cannot see this revert; eighth row docsections-local-bounder-restored bound to the source guard.
- v1.64: Plan re-audit v50 clean (both surfaces) + design v1.63 back-propagation: the WIRE-PIN's finally-path restoration of sys.modules and the docsections reload is stated here too.
- v1.65: Design v1.64 back-propagation: Setext census added to §Measurements (files=30 setext_headings=0); the connection-only revert's private sys.modules registration stated.
- v1.66: Plan re-audit v52 (codex clean; agy should 1): the docsections.json deliverables row names the named-test conversion and the four connection rows (8 rows).
- v1.67: Plan re-audit v53 clean (both surfaces) + design v1.65 back-propagation: 69 mutations (67 of the helper's source) after the two collect-stage rows.
- v1.68: Plan re-audit v54 clean (both surfaces) + design v1.67 back-propagation: run_block's API row lists the collect stage; 70 mutations (68 of the helper's source).
- v1.69: Impl-plan v1.15 back-propagation: consumer-from-import stated as one contiguous replacement at the call region, alias line untouched.
- v1.70: Plan re-audit v55 (codex must 1; agy clean): every 5f command is bounded through hmad-dispatch run --timeout (rc propagates, 124 on expiry — measured); 71 mutations (69 of the helper's source) after the rollback read-back row.
- v1.71: Plan re-audit v56 (codex should 1; agy clean) + design v1.71 back-propagation: the hoisted _run_recipe derives collector/gate from SCRIPT_DIR itself; 72 mutations (70 of the helper's source).
- v1.72: Plan re-audit v57 clean (both surfaces) + design v1.73 back-propagation: 74 mutations (72 of the helper's source) after the bounded-wait rows.
- v1.73: Plan re-audit v58 (codex must 1) + impl-plan audit v18 back-propagation: the reap sequence and its probe prose carry the bounded wait(timeout=DRAIN_SECONDS) and its stage=reap expiry; 75 mutations (73 of the helper's source) with the field-escape row.
- v1.74: Plan re-audit v60 (codex must 1): FR-4's transport paragraph carries the one-physical-line escaping rule, its test and mutation from design v1.75; 76 mutations (74 of the helper's source).
- v1.75: Plan re-audit v61 (codex must 3 nit 1): the substitute API row and FR-4 carry the two-layer empty-key rule; FR-4 carries the quoted-JSON field rule with test_dynamic_field_cannot_forge_a_token and field-quoting-removed; AC-6.4's floor test runs with cwd=REPO_ROOT; the __all__ seven are listed; 77 mutations (75 of the helper's source).
- v1.76: Plan re-audit v62 (codex must 2; agy clean) + design audit v71 nit: the bare-field list is the design's exhaustive seven (reason= included; seconds=/pgid: quoted); the docsections ordering paragraph is un-spliced (the sixth/seventh-row sentences now follow it as their own paragraph).
- v1.77: Design v1.80 back-propagation: verdict/detail examples rewritten in the quoted-field grammar.
- v1.78: Design v1.81 back-propagation: `key=` and both `overlap:` elements quoted.
- v1.79: Plan re-audit v64 clean (both surfaces) + design v1.82 back-propagation: _field's second escaping pass; 78 mutations (76 of the helper's source).
- v1.80: Plan re-audit v66 (codex must 1; agy clean): find_heading's API row states both input forms and their precedence; 79 mutations (77 of the helper's source).
- v1.81: Plan re-audit v67 (codex must 1; agy must 1): BAD_ARGS routing; __all__ is 28 names; find_heading's request predicate is the scanner's; the AC-6.4 gate block runs from the repository root as the spec spells it; 81 mutations (79 of the helper's source).
- v1.82: __all__ is 29 names (BadArgs included).
- v1.83: Plan re-audit v69 (codex must 1; agy clean) + impl-plan audit v29: FR-6's caller pseudocode binds substituted_block from substitute's tuple; the unreadable-preamble test is test_unreadable_preamble_path_refuses.
- v1.84: Plan audit v73 (teammate surface, advisory). MUST 1: the AC-6.4 suite-floor baseline was stale by one — 2747/2485 measured at 6b4df35, but b59e05e added a test and the real counts at e8eaf6f are 2748/2486, so the floor asserted >= 2747 + … against a real 2748 and exactly one pre-existing test could be deleted with the floor green, falsifying the bullet's own no-hidden-deletion guarantee. Re-measured, and the drift is now closed as a class rather than a number: the count travels with the commit it was measured at and MUST be re-measured at 5c branch time. MUST 2: this was the one document of four stating the exit-code contract without the --help carve-out (the impl-plan swept it at v1.31, the plan was not swept with it); carve-out added, plus exit_on_error at the default per design v1.91. Also: 'tagging makes re.findall match zero blocks' is measured false — 4 blocks before, 3 after, and what empties is the h_mad_audit_gate.py filter, so the loud failure is _gate_bash_block's assert gating.
- v1.85: Plan audit v74 (teammate surface; the agy leg returned PASS at tools=2, the report-file floor, so it contributed nothing). MUST 1: the doc_block_exec.json deliverable row split its 81 rows 79 helper-source + 2 SKILL.md, but the design matrix it names as the authoritative list has exactly ONE row whose mechanism names SKILL.md as the mutation target (registry-row-removed at design :1256) — counted independently: 81 data rows at design :1178-1258, 1 naming SKILL.md. The second AC-4.5 direction, detail-line-undocumented, mutates the HELPER ('the helper renames one emitted detail line'), so its file key is the helper's source and "h-mad/SKILL.md" there is an anchor the harness refuses. Split corrected to 80 + 1, and the split is now re-derived from the matrix's mechanism column rather than carried. The design's own summary paragraph under the matrix still says 79 + 2 and contradicts its matrix; the impl-plan carries the same pair at :1234/:1268 — reported to the orchestrator, not edited here. MUST 2 (rule 7, this document's own instance): the 5f bound cited 'three times the 397 s baseline' while the baseline quoted eleven lines above had been re-measured at v1.84 to '2748 passed in 383.05s' — 397.40s was the value at 6b4df35, so the number was corrected in the quoted command output and left stale in the prose that derives from it. Now 383 s with the drift named; the impl-plan carries the same stale 397 s at :1796. CENSUS (rule 2): the extractor-census control was the one figure in this plan with no command; it is now cited as `git grep -l '```' -- '*.py' | wc -l` -> 23 at 1861157 (21 at 6b4df35; b59e05e, the same commit that moved the suite floor, moved this too), with the narrower bash-literal reading (3) named so the quantity meant is unambiguous. SHOULD: 'changes at exactly two points' replaced by what does NOT move (the three _gate_bash_block callers keep their types, :412 keeps re.findall, .returncode is read nowhere), since the paragraph's own list runs to five regions; Scope names the AC-1.8 docsections scope increase and its three deliverables, and the Implementation Strategy opening sentence carried the same omission and is fixed with it; __all__'s enumeration reads 'the whole DocBlockError hierarchy — the base class and its 19 subclasses' per design :689, since the seven-plus-two-plus-subclasses reading gives 28; the --help carve-out swept by claim to all three surfaces (transport, CLI contract, Implementation Strategy) with the residual stated. NITS: titled_section's replacement is one-for-one at the call site and intentionally drops one leading newline; the design's matrix is a bolded lead-in, not a heading. Also re-derived: AC count 49 at spec v1.53, fence census 68/10 with control 83, extractor census 2 hits / 5 bare-literal hits — all unchanged.
- v1.86: Design v1.93 back-propagation (raised by design-author-1, verified by the orchestrator): every *.md-scoped heading measurement in Measurements cited a 30-file corpus that is 25 tracked files plus 5 untracked, gitignored .pytest_cache/README.md artifacts — build output that exists only where pytest has run, so files=30/both=266/setext_headings=0 were not reproducible on a clean clone, and the plan contradicted the design from v1.93 on. The corpus is now defined as the design's: git ls-files -- h-mad handoff filtered to *.md with archive/ excluded, 25 files, with the command cited. Re-derived independently at 1861157 (throwaway heading_differential.py, one re.match per line per selector, fence-aware on the new side), both corpora reported side by side so the contamination stays visible: TRACKED files=25 both=263 old_only=76 new_only=0 setext_headings=0, softening closing_hash=0 tab_form=0 titleless=0; GLOB files=30 both=268 old_only=76 new_only=0 setext_headings=0, softening closing_hash=5 tab_form=0 titleless=0. So the two load-bearing conclusions (new_only=0, old_only=76) hold on BOTH corpora and never depended on the contamination — but the new_only=0 JUSTIFICATION did: the old text said '## x ##' occurs nowhere while measuring a corpus holding five of them ('# pytest cache directory #', one per README). Restated correctly: the Guard-narrowing 'softened outcome' set is about heading IDENTITY, not line recognition — a '## x ##' line is a heading to both selectors and lands in both, never new_only, and only the new selector strips the closing run; counted as identities the set is empty over the tracked 25 and is 5 over the glob 30. The both=266 -> 268 delta chased rather than carried: 266 was correct at 1f5b30e, and h-mad/SKILL.md has since gained exactly two ### headings, 'Close the class, never the instance' (e8eaf6f) and 'Record a rejected finding in the rejections ledger, never in a gated document' (ff0a278/11a7db7), measured by diffing the heading lines between the revisions; both is not a conclusion this plan rests on and drifts with any doc edit, so its command travels with it. Also swept by value rather than fixing the two named instances: the fence census (68 across 10 files, control 83) is the third *.md-scoped count and was re-run on both corpora — identical on each, because the five artifacts carry no fence, so it is corpus-invariant and that is now measured rather than assumed. NOT harmonised, deliberately: AC-6.1's tree sweep is not git ls-files, so the plan now states why the two realisations differ, namely that a test must still count a newly written, not-yet-tracked .md under the two roots (exactly what git ls-files misses and the guard exists to catch), and excludes build output by a dot-directory component instead. [Corrected at v1.88: this entry originally added "the spec reaches its scope by reference to this census" as the reason. That was already false when written — spec v1.55, produced by this same commit b68ef48, states AC-6.1's sweep in full rather than by reference. The conclusion the clause supported is untouched; only the premise was wrong.]
- v1.87: Pre-dispatch precheck repair before the round-three audit, raised by h_mad_precheck_doc.py (hard, PINDRIFT), re-verified here against the tree. The plan's one cross-document line pin into the design — the citation for the seven-plus-two-plus-subclasses reading — resolved to a blank line: sed on the pinned line printed empty, grep for the phrase found it 34 lines lower, and the shift came from the design's revision to v1.93 at b68ef48, after the sha this plan measured at. NOT re-pinned to the new line, and that is the point: the precheck scores PINDRIFT at FILE level, so any design.md line pin fires while the design has changed since this plan's provenance 1861157 — a scratch copy re-pinned to the new line still returned PRECHECK FAIL issues=1, proving the number was never the defect. The citation is now a structural locator (the design's API / Interface Changes heading, the __all__ paragraph after the find_heading docstring, plus the grep that finds it, one hit at HEAD 048ef1f), so the class is closed and no future design revision can stale it. Sweep, rule 7: grep -nE for a path:line form over the whole plan returns exactly one design pin (this one, fixed) and one .py pin, the docsections fence-prefix consumer — that one is verified UNCHANGED since 1861157 and correct at HEAD, so it is advisory, left alone and reported to the orchestrator with the bare :NNN pins into the collect-report test module. No measurement sha re-pinned: 1861157, a469493 and e8eaf6f stand because no measurement behind them was re-run, and a behind-HEAD measurement sha is the normal condition the precheck scores as advisory.
- v1.88: Plan audit v75, gating round, two surfaces (teammate must 5 should 3 nit 3; agy must 3, of which 2 land in the spec and are routed there). MUST 1, found INDEPENDENTLY BY BOTH SURFACES: the paragraph justifying "AC-6.1's tree sweep is deliberately NOT this filter" asserted that the spec reaches AC-6.1's scope BY REFERENCE to this census and quoted 'the same sweep as the plan's fence census' as the spec's wording. Re-verified at a8e0372: grep for that phrase in the spec returns NOTHING, grep for 'stated here rather than by reference' returns one hit, and git log -S shows the phrase left the spec at b68ef48 — the same commit that produced plan v1.86, the revision that wrote the sentence, so the premise was stale the moment it was written. Premise and phantom quotation replaced with what the spec actually says (spec v1.55, AC-6.1: *.md under the two roots, archive/ and any dot-directory excluded) plus the two greps that establish it; the CONCLUSION is untouched and is why the paragraph stays — the two realisations differ on purpose and each document must be able to say so alone. The v1.86 Version History entry repeated the dead premise and now carries an inline correction. MUST 2, a CLASS closed over its axis rather than at its five instances: a tree-derived count restated WITHOUT the sha it was measured at. Every one was correct when written and every one is false at a8e0372, and the anchor had drifted into a number COLLISION that inverted its own paragraph — the corpus-definition bullet said tracked 25 / glob 30 and carried the only command block in Measurements with no sha, while at a8e0372 the cited command returns 30 and the glob returns 35, so a reviewer re-running it reads 30, matches it to the plan's stated GLOB figure and concludes the plan defines its corpus as the contaminated glob, which is exactly the contradiction plan v1.86 existed to remove. Re-derived by me at a8e0372, not carried from the report: tracked 30 / glob 35 (25/30 at 1861157, moved by 6db8e50 which adds exactly five h-mad/agents/*.md, git show --stat); the bullet now states the git ls-files COMMAND as the definition and the count as a measurement with its sha, and the invariant claim is restated structurally — the glob is the tracked set plus exactly five .pytest_cache/README.md files, re-derived by differencing the two sets, with the tracked set having no member the glob misses. Instances swept, each now carrying a8e0372: Scope's 67 bash fences -> 72 of 73; Out-of-Scope's 68 -> 73; the fence census header, its quoted output and its control -> 73 across 10 files, control 88 (68/83 at a469493 and 1861157), re-run on BOTH corpora at a8e0372 and identical on each, with the invariance reason re-established rather than carried (grep -c '^```bash' h-mad/agents/*.md -> 0 on each of the five new files) and a residual stating that invariance is a property of the current extra files, not a theorem; the extractor census's 'five hits' -> SIX at a8e0372 (grep -rn '```bash' --include='*.py' .), the fourth non-extractor being a prose comment in h-mad/scripts/h_mad_precheck_doc.py, located structurally and NOT line-pinned; its control git grep -l '```' -- '*.py' | wc -l -> 24 at a8e0372 (23 at 1861157, 21 at 6b4df35), the narrow bash reading 4 (3 at 1861157); and the risk row whose mitigation read 'Re-measured this session' — the only mitigation cell a reviewer could not check — now names the sha and states that the sha, not the re-measurement, IS the mitigation. The extractor census's two narrow hits are unchanged at a8e0372, the one figure here that has not moved. SHARED CORRECTION, stated identically to the spec and impl-plan authors: AC-6.4's floor tuple is NINE, not seven, and the floor is 2748 + new_module + 9. h-mad/tests/test_h_mad_portable_timeout.py builds a module-level _SCANNED list containing *sorted((SKILL / 'scripts').glob('*.py')) and two @pytest.mark.parametrize decorators consume it, so Task 1's new module adds a node to each. MEASURED rather than reasoned, at a8e0372, across all three artifact classes this feature creates: a scratch h-mad/scripts/*.py moves the full collect 2808 -> 2810, +2, both ids in test_h_mad_portable_timeout.py; a scratch h-mad/tests/test_*.py with no test functions and a scratch h-mad/tests/mutation-specs/*.json each leave it at 2808, +0. The axis is named (a pre-existing parametrize whose argvalues come from a filesystem glob this feature writes into), the probe is written inline as the rule, and the residual says why grepping for glob( alone is insufficient — the mutation-spec and test-module globs elsewhere sit in function bodies, not in argvalues, which is what (b) and (c) measure. Re-run the probe at 5c with the floor. As written, '+ 7' tolerated two invisible deletions, the exact weakening AC-6.4 exists to prevent. SHOULD 1: 'all five titled_section/section_from assertions' — there are six test functions and six call sites (grep -c '^def test_' -> 6 at a8e0372), and the count arrived by copying the v74 report's wording, the previous-cycle's-fix pattern again; the claim is now quantified over EVERY such assertion rather than over a count, since the conclusion (none pins bytes, re-read in full and confirmed) does not depend on how many there are. SHOULD 2: 'Two tests pin it' had no recoverable antecedent and the nearest reading contradicted the sentence before it; the referent is named — the cross-directory import, the AC-1.8 collect-alone pins. SHOULD 3, cycle-73's open item closed: docsections.json's 'two leave / two stay' is a statement about which FILE key each row names, and NOT ONE of the four find anchors survives verbatim — read at a8e0372 with a one-line json dump, all four file keys are tests/docsections.py today, two anchor inside the deleted _fence_aware_end and move to scripts/, and the two that keep the file are still re-anchored (section_from's call gains the _dbe. prefix, titled_section's assert loses its match binding). NITS: the design-grep label 048ef1f was this document's HEAD~1 and is now a8e0372 with the count re-run (one hit); the sixth/seventh docsections rows are introduced in order; the 5f bound's derivation is stated as three times 383 s = 1149 s rounded up to 1200, since an exact-multiple wording asserted a derivation that does not produce its own number. Also re-derived at a8e0372 and unchanged: AC count 49 (now anchored at spec v1.55), the two narrow extractor hits, and the full-suite collect 2808 — recorded beside the e8eaf6f baseline as evidence the floor's re-measurement residual is live, and deliberately NOT adopted, since the baseline must be measured at the 5c branch commit. OWED ELSEWHERE, reported not edited: the design carries the same tracked-25/glob-30 pair in its Scanning measurement and inside its AC-6.1-6.6 matrix row, and both the design and the impl-plan carry the seven-node floor tuple and '+ 7'.
- v1.89: AC-6.4 reconciliation with spec v1.56, plus one instance of the v1.88 count class that the v75 audit did not name and I found while reconciling. RECONCILIATION: the team lead prescribed the constant NINE and '+ 9' to all three authors; the spec author instead removed the total from AC-6.4 and fixed a MEMBERSHIP RULE over the axis — (1) nodes added directly to a consumer file, plus (2) one node per glob-parametrised test per new h-mad/scripts/ file, with source (2)'s nodes required to PASS and not merely be counted — and the lead accepted it. They are right: nine is the instance, the rule is the class, and 'nine' goes stale on any second script exactly as 'seven' just did, which is this feature's own 'close the class, never the instance' applied to the prescription itself. This plan now ATTRIBUTES the rule to spec v1.56 rather than re-wording it (two independently-worded versions of one rule is how the 25/30 corpus contradiction started) and enumerates the rule's current members with the derivation beside them: h-mad/scripts/*.py is 37 files at a8e0372; grep -c 'parametrize("path", _SCANNED' h-mad/tests/test_h_mad_portable_timeout.py -> 2 at a8e0372; Task 1 adds one file, so source (2) contributes 2 and source (1) the 7 consumer-file nodes, len(tuple) = 9 at a8e0372, RE-DERIVED at 5c in the same commit that re-measures the 2748 floor and for the same reason. The floor assertion is now written full_collected >= 2748 + new_module + len(tuple), the form spec v1.56 uses, so the assertion itself cannot go stale when the enumeration is re-derived — v1.88's literal '+ 9' would have been the next '+ 7'. The +2/+0/+0 probe stays but is reframed as what it is: the EMPIRICAL CHECK of the spec's rule, not a second statement of it — it measures the one distinction the rule turns on, a glob in parametrize argvalues versus a glob looping inside a test body, which a grep for glob( alone cannot make. Source (2)'s 'must pass' half is recorded as an obligation on Task 1's SOURCE (no bare timeout <n> form, no unconditional absence claim), not merely on the floor arithmetic. The FR-6 table's cross-reference now says it names every AUTHORED member (spec source (1), seven node IDs) and that source (2)'s members are outside that table by construction, rather than asserting a total. NEW INSTANCE OF THE v1.88 CLASS, found by me, not filed by either audit surface: the Second-surface BLOCK CENSUS. The plan said 'the section holds four bash blocks' with no sha at the point of use, and '3 of the section's 4 blocks instead of 4' at e8eaf6f. Re-measured at a8e0372 by importing the consumer's own _second_surface() and running the :270 pattern over it: SEVEN blocks before the tag, 1 gating; simulating the tag on the gate opener, SIX blocks, 0 gating. 6db8e50 moved it by inserting a ## heading between the two string anchors _second_surface() bounds on — the same commit that moved the *.md corpus from 25 to 30, so one commit produced two instances of this class in this document. The ORDINALS did not move: the gate block is still block 4 of 7 and the exec-codex block still block 2 of 7 at a8e0372, and each is unique in the section under its own filter [Corrected at v1.90: this entry originally called the ordinals 'the load-bearing part'. They are informational only and now carry their base; the load-bearing claim is the uniqueness-under-filter clause that follows, which is what the two content-predicate call sites actually depend on. The conclusion is untouched; only the emphasis was wrong.] (exactly one block holds h_mad_audit_gate.py, exactly one holds exec codex) — that uniqueness, not the total, is what the two call sites depend on and what is re-checked at 5c. The spec author found the same drift in FR-6's Description independently and landed it in spec v1.56; the two documents now agree at a8e0372. Also re-verified before writing, because the spec was being edited concurrently and my v1.88 MUST-1 fix rests on it: grep -c 'stated here rather than by reference' on the spec -> 1 and grep -c 'same sweep as the plan' -> 0 at the current spec state, so the AC-6.1 premise still holds.
- v1.90: Plan audit v76, gating round, two surfaces (doc-auditor teammate must 2 should 1 nit 2, teammate gating; agy must 1, which lands in the SPEC and is routed there). MUST 1, the sha-less tree-derived-count class re-closed over its axis after surviving the v1.88 sweep, with the reason it survived recorded because that is the reusable half: the v1.88 sweep enumerated VALUES (67, 68, 25/30, 'five hits') and every member it found had already drifted, so members whose value had NOT moved were invisible to it - three importing test files, three _gate_bash_block() call sites, zero .returncode reads, all arithmetically correct at 335f535 and all unprovenanced; it stated the axis as 'without the sha', which let a member carrying a command but no sha read as compliant; and it recorded the rule only in a Version History entry, so the rule governed nothing written afterwards and v1.89 wrote a fresh member into the very paragraph whose stated purpose was re-derivation. Fixed by a PROVENANCE RULE binding on the whole document (every tree count, ordinal or absence claim carries both its generating command AND its sha, on the same surface as the number; '(measured)', 'measured this session' and 'today' are neither), placed in the Measurements preamble where the next author reads it, with a two-part SHAPE screen written inline as its checker and a residual recording both readings - before the fix 6 hits with 4 real members and 3 with 1; after, 4 and 2 with none - so the screen is shown to discriminate rather than asserted to. All four members fixed at 335f535: 'h-mad/scripts/*.py is 37 files today' now carries ls h-mad/scripts/*.py | wc -l -> 37 with git ls-files 'h-mad/scripts/*.py' | wc -l -> 37 beside it as the build-artifact control; 'three files import it' gains its sha; the three _gate_bash_block() call sites and the .returncode absence are stated with grep -n and grep -c plus sha, and the call sites are now named by their ENCLOSING TEST FUNCTION rather than by line, since a line pin in that file has gone stale once already. DECISION B applied: the second-surface ordinals are demoted to informational and carry their base ('block 4 of 7', 'block 2 of 7'); the load-bearing claim is restated as uniqueness under the CONTENT PREDICATE each call site filters on, and the v1.89 Version History entry that called the ordinals 'the load-bearing part' carries an inline correction. DECISION D applied: the seam ordinals at the _final_write injection go, replaced by the seam names, since seams are named and never numbered. DECISION A: both AC-6.4 totals re-derived and re-pinned to 335f535 and re-worded so each reads as a dated evaluation of the spec's rule and never as the contract, which remains len(tuple). SHOULD 1: Next Steps stated this document's own stamp criterion over a named pair of surfaces that the routing has since replaced, naming the superseded pair immediately before the stamp; the criterion is now STRUCTURAL - two DIFFERENT surfaces per SKILL.md 'Never gate on one audit pass', at least one of which reads the working tree in the cycle it reports on - with the per-surface behavioural claims dropped alongside the names, plus a standing debt recording that the last codex-carrying cycle on this document is v72 and a must=0 should=0 reached without codex is provisional. NITS: the four docsections connection mutation rows drop their ordinals and are named, closing the reordering axis rather than the one out-of-order instance; the fourth in-fence heading in h-mad/agents/doc-auditor.md is named (## Nit), with the other four agent documents confirmed to carry none. Also re-derived at 335f535 and unchanged, so re-pinned where I ran them: fence census 73 across 10 files with control 88, corpus 30 tracked / 35 glob, second-surface 7 blocks with the gate block unique at 4 and exec codex unique at 2. NOT re-run and therefore left at their own shas: the +2/+0/+0 collect probe, the extractor census, the 2748 floor. OWED ELSEWHERE, reported not edited: the design's 'seven floor-tuple node IDs' and its 'the plan's census sweep' description of AC-6.1.
- v1.91: Plan audit v77, gating round, doc-auditor teammate surface (must 4 should 3 nit 3). The auditor RAN the v1.90 screen at both commits and its published before/after numbers reproduced exactly - and the finding was the thing the screen could not see. MUST 1, THE SCREEN WAS PARTLY DEAD CODE: in awk \b is a BACKSPACE ESCAPE, not a word boundary, so the \btoday\b alternative could only ever match a line carrying a literal 0x08 and one of the three markers the rule names was unenforceable. Re-probed by me at 74e126f on awk version 20200816 (the macOS default, awk --version) over printf 'measured today\nremeasured todayish\n': the \b form prints NOTHING, a bare /today/ prints BOTH lines, printf 'a\bb\n' | awk '/\b/' MATCHES (the control proving \b is a literal backspace rather than a never-matching construct), and the POSIX form (^|[^[:alnum:]_])today([^[:alnum:]_]|$) prints the first line only. Replaced with the POSIX form. A SECOND narrowing was then found by running the repaired screen and READING its output: the marker alternative was anchored on a preceding comma (, measured[,)]) so the em-dashed '- measured, it selects a different, untagged block' form this document's Risks table actually writes was invisible; widened to measured[,)] with no leading punctuation, which surfaced exactly one member (the Risks row asserting the exec-codex scan is unaffected - an absence claim with the marker, no command, no sha) and two non-members. Axis stated: a marker alternative must not be anchored on neighbouring punctuation, which is a per-sentence house-style choice while the class is not. ALL v1.90 COUNTS DISCARDED, NOT CARRIED, because they were produced by a blind filter; the repaired screen's readings are published as a TRIPLE so the middle term is legible - 21 lines at 335f535, 18 over the v1.90 body at 74e126f, 9 over the v1.91 body in the working tree at 74e126f, the 9 triaged by CATEGORY (5 permanent self-matches, 2 OS/interpreter-probe references under the stated carve-out, 2 sentences using a marker word while stating no tree count at all) with ZERO members. MUST 2, a FIFTH surviving member of the class v1.90 declared closed at four: the .returncode absence restated in the migration paragraph with the marker, no command and no sha, while the same claim in the paragraph above had been repaired in the same revision. Both surfaces now carry grep -c returncode h-mad/tests/test_h_mad_collect_report_docs.py -> 0 at 74e126f, and the rule is stated over the axis (before declaring a member fixed, grep the claim's SUBJECT across the whole body and provenance every surface) with its residual (a claim restated in words other than its subject - 'nothing maps to .rc' - is unreachable by a subject grep and must be caught by the shape screen). MUST 3, plan:234's sys.path premise was FALSE against the tree: both h-mad/tests/test_h_mad_review_evidence.py and h-mad/tests/test_h_mad_wire_registry.py DO insert h-mad/scripts into sys.path. Verified by me at 74e126f with grep -n 'from docsections import|sys.path.insert' over all three importers: the conclusion survives on IMPORT ORDER, not absence - the from docsections import line precedes every insert in those two files and the third has no insert at all. Premise rewritten as order, with the per-file residual (an import-block reorder silently removes it in one file without touching the others) and the pin that catches it named - the isolated python3 -c 'import docsections' with an unrelated cwd, which is also what docsections-syspath-setup-removed is scored against. MUST 4 / DECISION E, ONE RULE ONE CHECKER: the plan's counted-noun screen was a second, strictly weaker wording of a rule the spec already implements. Deleted and replaced by an ATTRIBUTION to spec section 'How the members are found - an enumeration, because a value sweep cannot find them all', run verbatim with this document's path substituted; grep -c on that locator -> 1 at 74e126f, with DECISION F recorded as the reason to re-check it at every audited commit rather than trusting the commit it was authored at. Its hit count is deliberately NOT published, for the spec's own stated reason (it is a procedure, not a measurement); a positive/negative control pair is published instead, run at 74e126f - the scripts-directory count as 335f535 wrote it IS returned, the same claim as this body now writes it (ls h-mad/scripts/*.py | wc -l -> 37 at 335f535) is filtered. DECISION E's general rule is stated at the head of the section: a checker this document publishes is EXECUTED against a positive and a negative control before any count derived from it is published. THE AUDITOR'S ONE UNREPRODUCED CLAIM, reported not adopted: the report says spec:695's enumeration 'is what surfaces plan:554'. I ran it against this document at 74e126f and 553-554 are NOT in its output - the enumeration allows exactly one word between cardinal and noun, its cardinal list has no 'zero', and the claim wraps across a line break, so it misses on all three counts. The finding stands and is fixed; only the mechanism was wrong, and the three misses are now recorded as the enumeration's residual on THIS document and reported to the spec author. SHOULD 1: plan:264's command did not reproduce its own number - grep -n 'titled_section|section_from' returns 8 lines, not six call sites; narrowed to grep -c 'titled_section(|section_from(' -> 6 at 74e126f with the two non-call lines named, and grep -c '^def test_' -> 6 re-stamped at 74e126f. SHOULD 2: the paragraph explaining why the class survived was itself an unprovenanced member; all three of its counts now carry their commands and 74e126f inline, with the reason stated (the rule admits no carve-out for explanatory prose). SHOULD 3 / DECISION D extended: the floor tuple's members are addressed by SOURCE, never by ordinal - 'A seventh' and 'The eighth and ninth' are gone, and the self-granted 'numbered within this enumeration of nine and nowhere else' licence with them. NITS: the screen-two self-match sentence dissolved with screen two; 'inline fixture strings' -> one string (grep -c '```bash' h-mad/tests/test_docsections.py -> 1 at 74e126f); the pytest_cache half of the corpus-invariance claim gains its command, SCOPED to h-mad and handoff (find h-mad handoff -name README.md -path '*pytest_cache*' -> 5 at 74e126f) because a repository-root run also returns ./.pytest_cache/README.md, which is outside the corpus and would contradict the tracked/glob arithmetic on the same page. ALSO SWEPT, not in the report but the same class the document declares closed one line earlier: prose line pins into h-mad/tests/test_h_mad_collect_report_docs.py, EIGHTEEN occurrences across FIFTEEN body lines (7 x :270, 1 x :309, 10 x :412; counted at 74e126f by piping the body through awk '/^## Version History/{exit}{print}' and grepping the three backticked tokens), while the sentence beside several of them says call sites are named by their enclosing function because a line pin in that file has gone stale once already. Zero remain in the v1.91 body by the same count. Replaced by two structural nicknames defined once - the GATE-BLOCK EXTRACTOR (the re.findall inside the module-level _gate_bash_block() helper) and the EXEC-CODEX SCAN (the re.findall inside test_exec_codex_dispatch_carries_out_log_and_timeout) - both re-read at 74e126f. Recorded command outputs that print line numbers are untouched, since those are outputs and not pins. RE-DERIVED AT 74e126f AND UNCHANGED, so re-stamped where I ran them: 3 importers, the def plus 3 _gate_bash_block() call sites, 0 returncode, ls/git ls-files h-mad/scripts/*.py 37/37, parametrize 2, docsections.json's four file keys all tests/docsections.py, its key sets (no test and no target_command key exists yet), grep -n 'P<marks>' h-mad/tests/docsections.py -> 1. OWED ELSEWHERE, reported not edited: the spec should add 'zero' to its cardinal alternation and 'call sites|importers|node IDs' to its noun alternation, and should consider allowing more than one word between cardinal and noun.
- v1.92: Plan audit v78, gating round, doc-auditor teammate surface (must 5 should 3 nit 3), at freeze sha 35698f9. Every one of the five must-fixes was a PROVENANCE or CITATION defect on a claim that is factually true; the auditor re-derived all of them at the freeze sha and they reproduce, so the conclusions are untouched and only the provenance is repaired. CLOSURE STATED ONCE INSTEAD OF FORTY RE-STAMPS: both commits between 74e126f and 35698f9 touch only docs/ (git diff --name-only 74e126f 35698f9 -- h-mad handoff prints nothing; the same diff piped through sed 's|/.*||' | sort -u prints docs alone), so every h-mad/handoff-scoped figure stamped 74e126f is provably identical at 35698f9 and is left as written - a mass re-stamp is itself a defect surface. The Measurements preamble now says so, and says what the closure does NOT reach: figures derived from this document or from its three siblings under docs/, which did change, and figures stamped older than 74e126f. MUST 1, and the fix for it is a POINTER rather than a second copy: the Risks row's provenance pointed at a section this document does not have (grep -n '^#{1,4} ' returns no Second surface heading; the only '## Second surface - the codex leg' is in h-mad/SKILL.md, the probe's SUBJECT) and stamped 74e126f while the two surfaces that record the probe both stamped 335f535. The block census now has ONE authoritative record, in Implementation Strategy, carrying a runnable one-liner and re-derived by me at 35698f9 - python3 -c importing the consumer's own _second_surface() and running the gate-block extractor's pattern over it prints 'blocks 7 | gate [4] | exec codex [2]', the two SINGLETON lists being the load-bearing uniqueness claim and the ordinals inside them informational. The 'only the gate-block extractor is affected' paragraph and the Risks cell are now pointers that restate neither the total nor an ordinal (SHOULD 2, same edit). Generalisation recorded: the repair for a claim stated without provenance is a pointer to the single surface that owns it, never a second copy, because two copies drift and a pointer cannot. MUST 2 / DECISION E: the residual on screen two was FALSE at the freeze sha because the spec was widened in the SAME commit - at 74e126f the gap between cardinal and noun was ([a-z]+ )? and at 35698f9 it is ([^ ]+ ){0,3}, landed by the spec author in 0aac0b7. Rather than restate what a sibling currently says, this document now records only what running the checker against ITS OWN body measured: fed as 74e126f held it, 'three importing test files' is NOT returned; fed as 35698f9 holds it, it IS - so the miss was real when written and is closed, and 'reported to the spec author rather than patched here' is gone because the spec author patched it. The half that stands is stated the same way: printf 'zero files' returns nothing at 35698f9 while printf 'one file' matches, so the cardinal alternation still declines zero. The line-break miss stands as the first residual. The spec's own residual enumeration is addressed, not restated - grep -c 'Residual on the enumeration itself' on the spec -> 1 at 35698f9. MUST 3 / DECISION A: the published negative control attributed the filtering to a stage the checker does not have. Run verbatim the enumeration has NO sha stage anywhere in it, and I proved provenance plays no part by feeding the same claim with the counted noun restored AND the sha left in place - it MATCHES. What filters the live form is the counted-noun shape ('**37** at' puts no noun of the closing alternation within the allowed gap). So it is a FALSE NEGATIVE, named as such, and calling it 'the negative' inverted the control. A real true negative is published in its place, deliberately one carrying a noun from the alternation so the decline costs something: 'Shell mode belongs on the fence, not in the caller.' verbatim from Architecture Considerations, declined; 'The tag is the security boundary.' likewise. One over-reach is published too: 'Refusal is the default response to anything unmeasured.' IS returned, because -i matches 'measured' as a substring of 'unmeasured'. Provenance on this document is screen ONE's job, via marker plus the !/[0-9a-f]{7}/ reading. MUST 4 / DECISION C: a bare path:line pin into h-mad/tests/test_h_mad_collect_report_docs.py survived in prose because the v1.91 sweep enumerated VALUES (:270/:309/:412) and this one had not drifted. Replaced by the structural form, and the class is now declared closed by a SHAPE grep written into the body - awk '/^## Version History/{exit}{print NR": "$0}' <doc> | grep -E '\.py:[0-9]+' - which returned 3 on the v1.91 body at 35698f9 (two recorded outputs, exempt, plus the one prose pin) and returns exactly the two recorded outputs on this body. Both residuals stated and MEASURED: the companion grep -nE '\.(md|json|sh|toml):[0-9]+' returns 0 at 35698f9, and the shape grep cannot tell a pin from an output so its hits are read, never counted. A PREMISE THE TREE REFUTED, found by me while fixing that sentence and not in any report: the same sentence claimed the arrangement is the one EVERY test in h-mad/tests/ already uses for SCRIPT_DIR. It is 13 of 88 - grep -l 'sys.path.insert(0, str(SCRIPT_DIR))' h-mad/tests/test_*.py | wc -l -> 13, ls h-mad/tests/test_*.py | wc -l -> 88, 48 carrying some sys.path.insert, all at 35698f9. Rewritten as a convention to follow, not a property of the directory. MUST 5 / DECISION D: a tree-derived count carried a DESCRIPTION of its command ('a fence-toggling one-liner'), which invariants.base.md makes a Must and forbids downgrading. The actual awk one-liner is now pasted with its output, re-derived at 35698f9 - four in-fence # lines in h-mad/agents/doc-auditor.md, printed by the command itself rather than counted in prose, and none in the other four. Per DECISION A it ships with a TRUE NEGATIVE, not a bare zero: implplan-author.md and spec-author.md each hold a balanced fence AND carry 4 #-prefixed lines each, every one declined, so the screen discriminates on fence state and not on the absence of #; design-author.md and plan-author.md hold no fence and are declined trivially. Two residuals: the toggle ignores run length, marker character and info string (it cannot fire here - the same run tallies 8 markers at 35698f9, all bare three-backtick runs, even per file - but that is a property of this corpus, not a theorem), and /^ *#/ is broader than the old #+ selector. SHOULD 1: screen two's address is now the LINE-ANCHORED needle the spec designates rather than a prose phrase - grep -cE '^  \$ awk ' on the spec -> 1 at 35698f9 - with both of its residuals stated and the ^  $ opener distribution re-derived (awk x1, curl x1, git x5, printf x1, python3.11 x1), and with the fact that this plan is the sole attributing document measured rather than asserted (the same anchored grep returns 0 on the design and 0 on the impl-plan at 35698f9). SHOULD 3: screen one's third leg was stamped 'the v1.91 body in the working tree at 74e126f', wrong on both halves - the v1.91 body is committed, and at 35698f9. All three legs now read COMMITTED bodies and were re-derived by me at 35698f9: 21 over git show 335f535:, 18 over the v1.90 body at 74e126f, 9 over the v1.91 body at 35698f9, and the 9-line triage is exact by category (5 permanent self-matches, 2 OS/interpreter-probe references, 2 sentences using a marker word while stating no count) with zero members. NO reading of the v1.92 body is published, because that body is readable at no commit until it lands. NITS: the Risks row's bolded clause regains its capital ('The exec-codex scan is NOT affected'); the six-hits sentence no longer splits its number from its sha across the wrap and is re-derived in DIGITS at 35698f9 - grep -rn '```bash' --include='*.py' . -> 6, split 1 h_mad_precheck_doc.py / 1 test_docsections.py / 2 test_h_mad_assemble_tdd.py / 2 test_h_mad_collect_report_docs.py by grep -rc; the pytest_cache re-stamp the report asked for is subsumed by the closure above rather than done as a separate edit. ALSO RE-DERIVED AT 35698f9 BECAUSE THE CLOSURE DOES NOT REACH A SIBLING UNDER docs/: the AC count, 49, now anchored at spec v1.58 rather than v1.55; the design's seven-plus-two-plus locator, grep -c -> 1; and both AC-6.1 premise greps on the spec, 'stated here rather than by reference' -> 1 and 'same sweep as the plan' -> 0. TWO FURTHER DECISION-E INSTANCES FOUND BY ME, not in the report: the 5f bound's parenthetical said the impl-plan 'carries the stale 397 s too' - it does not at 35698f9, that document fixed it, so the assertion outlived the defect it reported and the sibling claim is dropped rather than re-worded; and the Next Steps standing debt carried 'four revisions of this text', a figure that grows by one every round, now replaced by the derivation that produces it (ls of the codex audit reports piped through sed/sort/tail -> 72 at 35698f9, to be compared against the teammate series by the same derivation). ALSO RE-RUN AT 35698f9 AND UNCHANGED, so re-stamped where I ran them: the extractor census, 2 hits, with its recorded output now reproduced verbatim including the ./ prefix and labelled an OUTPUT so the shape grep's exemption is stated rather than assumed; its control, git grep -l '```' -- '*.py' | wc -l -> 24 with the narrow bash reading 4. OWED ELSEWHERE, reported not edited: nothing new beyond what the round-six decision sheet already routes.
- v1.93: Plan audit v79 at freeze sha 6f0ee85, two surfaces (doc-auditor teammate: must 2 should 4 nit 3, 26 files / 110 commands; agy: must 1, REJECTED on evidence below). Both must-fixes were provenance defects on claims that are factually true, which is now five rounds running. THE agy MUST-FIX WAS WRONG AND MY FIGURE STANDS: it called the spec-opener distribution "demonstrably false" after measuring at 6f0ee85, while the sentence stamps 35698f9. Re-derived by me at both: git show 35698f9:<spec> | grep -oE '^  \$ [a-zA-Z0-9._-]+' | sort | uniq -c gives 9 openers over 5 tokens (awk 1, curl 1, git 5, printf 1, python3.11 1) - exactly what the sentence says - and the same command at 6f0ee85 gives 20 openers over 11 tokens. A wrong-commit measurement is not a falsification. MUST 1 / DECISION J, A CARVE-OUT WHOSE PREMISE THE TREE REFUTES: the 5f wrapper probe was stamped 'measured 2026-09-03' under a carve-out reading 'which no repository sha determines'. hmad-dispatch is tracked repository code - git ls-files h-mad/bin/hmad-dispatch h-mad/scripts/hmad-dispatch.sh returns BOTH paths at 6f0ee85 - and 3f50b95, dated 2026-09-04 and titled 'make rc=124 legible', landed on that exact behaviour ONE DAY AFTER the stamp (bea1b60 is a second). Probe re-run live by me at 6f0ee85 invoking the tracked script BY PATH: h-mad/bin/hmad-dispatch run --timeout 5 -- sh -c 'exit 3' -> rc=3; run --timeout 1 -- sleep 3 -> 'hmad-dispatch: run_timeout after 1s - sleep 3', rc=124. Conclusion unchanged, provenance replaced: sha, not date, with the recorded output pasted. THE CLASS IS CLOSED OVER THE AXIS, NOT THE INSTANCE: the rule is now 'a probe carries a sha whenever the thing whose behaviour it measures is a tracked repository artifact; the carve-out is only for behaviour the OS, kernel or language runtime alone determines, and naming the determining thing is part of the claim'. Its test is one command, git ls-files <the probe's subject>, and its residual is stated - no shape filter can apply it, because deciding what a probe's subject IS requires reading the probe. The whole carve-out population was then swept BY HAND and the sweep is PUBLISHED as a six-row table, five exempt plus the one that is not: argparse exit_on_error (CPython argparse, empty, stamped python 3.11.8), AC-5.2 group kill/escape (os.killpg/os.setsid, empty), AC-3.14 rmtree on 0o000 (shutil, empty), AC-3.10 reader-less FIFO (os.open, empty), AC-5.5 emptied group (killpg, empty), and the 5f wrapper (h-mad/bin/hmad-dispatch, TWO PATHS, not exempt). A SECOND MEMBER FOUND BY THAT SWEEP: the AC-5.2 probe was correctly OS-scoped but claimed the exemption without paying for it - it ran under python3 -u, not the supported python3.11 -u, and printed no interpreter or platform line at all. Re-run by me under python3.11 with print('python:', sys.version.split()[0], '|', sys.platform) added; its recorded output now opens 'python: 3.11.8 | darwin' and the new pids are output, not pins. MUST 2 / DECISION I, A HALF-FIXED BOUNDARY PASSES THE TEST WRITTEN FOR THE HALF THAT WAS FIXED: v1.91 removed the LEADING comma from the measured branch and left the TRAILING [,)], so 'measured on the supported interpreter' and 'measured 2026-09-03,' fell straight through the screen this document calls its own provenance filter - which is exactly why the 5f defect above was invisible to it. The repair is over the axis and reaches EVERY sibling branch in the same expression, not the branch the audit named: five branches collapse to three, each a both-sides POSIX word boundary, each case-folded - (^|[^[:alnum:]_])[Mm]easured([^[:alnum:]_]|$)|(^|[^[:alnum:]_])[Tt]oday([^[:alnum:]_]|$)|[Tt]his session. Measured by me over the COMMITTED v1.92 body at 6f0ee85 (git show 6f0ee85:<doc> | awk '<program>'): the v1.92 screen returns 9 body lines, the v1.93 screen returns 32, so 23 lines had never been triaged. Unit stated: body lines printed, not occurrences and not distinct claims. Case-folding alone accounts for 4 of the 23 and is not cosmetic - the one line [Tt]oday adds is a real member. BOTH CONTROL HALVES RUN AND PUBLISHED, over one printf fixture: four positives (measured, x / (measured) / measured with care / Measured at dawn) and two true negatives ('anything unmeasured' and 'remeasured today' are DECLINED, because the leading boundary refuses an alnum), with the v1.92 form on the same fixture returning only the first three - the missing 'Measured at dawn' being the case-fold member itself. THE 23 WERE TRIAGED AND THEY CONTAINED FIVE REAL MEMBERS, ALL FIVE INVISIBLE TO THE OLD SCREEN (the intersection of the five with the nine the v1.92 screen printed is EMPTY, which is what makes the boundary repair load-bearing rather than tidy), all five repaired in this revision: (a) the 5f wrapper stamp above; (b) the collected count taken from h-mad/ as cwd, published as a bare 2486 with NO command and NO sha - it does not reproduce and, carrying no sha, could never be shown to have been right; replaced by a same-sha pair re-derived by me at 6f0ee85 with python3.11 -m pytest --collect-only -q -p no:cacheprovider | tail -1, 2809 tests collected from the repository root and 2547 from h-mad/, plus the accounting for the 2808 -> 2809 move (the only commit touching h-mad or handoff since a8e0372 is 335f535, and git show 335f535 -- 'h-mad/tests/*' | grep -c '^+def test_' -> 1); (c) the mutation-spec 80/1 split introduced by the word 'Today' - a count derived from a SIBLING under docs/, which the Measurements closure explicitly does not reach - now derived by grep -c 'the mutation targets `SKILL.md`' on the design -> 1 at 6f0ee85, unit stated as matching lines; (d) the fence-grammar table cell's 'measured on both renderers' with no renderer version anywhere on it, repaired by POINTER to the one surface that records the markdown-it-py versions and the 14-case corpus rather than by a second copy; (e) the fixture-preamble paragraph, which points at the spec's AC-3.11 and then restates the result anyway - now a pointer only, with the note that its subject (the h-mad/SKILL.md gate block and the collector) is TRACKED, so the owning surface owes it a sha. The full 32 are published as five categories that PARTITION them and sum to 32 (9 permanent self-matches, 8 marker-word-with-no-count, 5 carve-out probe references, 5 claims whose provenance sits on the owning surface via pointer or a line-wrap, 5 members), by category and never by line number. THE 21/18/9 TRIPLE IS NOT CARRIED FORWARD AS A SERIES: it is left as written and explicitly labelled a reading by the SUPERSEDED v1.91-v1.92 screen, because a reading is a reading of a screen and this screen has now been superseded twice in three revisions. SHOULD 1: the closure paragraph offered grep -c '74e126f' as the derivation of its own scope; I reproduce 27 at 6f0ee85, but that command counts this paragraph's own prose AND the very lines the next sentence puts outside the closure, and it cannot be narrowed by co-occurrence because grep is line-scoped and this document hard-wraps (the narrowed form returns 10, and neither integer is the number of covered figures). The offer is WITHDRAWN rather than corrected - the two git diff commands are the whole evidence. THE CLOSURE ITSELF IS EXTENDED AND RE-RUN, not assumed: git diff --name-only 74e126f 6f0ee85 -- h-mad handoff prints nothing and the piped form prints docs alone, so every h-mad/handoff figure stamped 74e126f OR 35698f9 is provably identical at 6f0ee85, and the paragraph now says the interval is re-checked against the NEW audited commit each revision rather than extended by assumption. SHOULD 2 / DECISION A IN MIRROR FORM: the companion sweep grep -nE '\.(md|json|sh|toml):[0-9]+' published a bare 0 and had never been shown to fire on anything - a POSITIVE half never run, in the revision that established a bare zero is not a control. A constructed positive is now published beside it and was run by me; the 0 is re-derived at both 35698f9 and 6f0ee85 and its reason is stated as INCIDENTAL, not load-bearing. The control changes the reading and that is said out loud: the same grep over THIS body returns 2, both hits the control's own recorded output. The fixture path is deliberately synthetic rather than a real sibling pin, so the shared precheck does not read a control as a pin. SHOULD 3 / DECISION F: the opener census is now published at BOTH shas with its units (occurrences of a line-opening command token, and distinct such tokens - one grep yields both), 9/5 at 35698f9 and 20/11 at 6f0ee85, with awk x1 at BOTH so the load-bearing conclusion survived a move the census did not; the anchored needle is re-stamped 1 at 6f0ee85 and the sole-attributor claim re-run there (0 on the design, 0 on the impl-plan, 1 on the spec). The fourth should-fix is a cross-document ruling routed to the spec and is not a plan defect; it produced no edit here. NITS: the two residuals on the needle are now stated as the spec's three MERGED, so a reader comparing counts does not read a contradiction that is not there; every 'spec v1.NN' label is defined once as the revision at which the premise beside it was last re-derived, and all three premises were re-run at 6f0ee85 (AC-6.1's spelled-out sweep at v1.55, AC-6.4's two-source tuple rule and len(tuple) floor at v1.56, and the AC count now re-derived at spec v1.59 / 6f0ee85 - 49 body-line anchors, with the uniqueness check printing nothing); the triage gloss that called a line 'prescribing how a report must read' is gone with the rewritten triage - it prescribes what a CANNOT-JUDGE VERDICT LINE may carry; and the screen-two -i over-reach on 'unmeasured' is now labelled screen two's and stays screen two's, with the note that screen one declines it by construction. ALSO SWEPT PER RULE 7, because collapsing five branches to three shifts every ordinal: the body no longer addresses any branch by ordinal ('the third alternative', 'the second alternative') - each is named by its marker word, which cannot drift when the alternation changes. RE-RUN AT 6f0ee85 AND UNCHANGED: the .py:N shape grep returns exactly the two recorded outputs on this body; the 49 AC anchors; both AC-6.1 premise greps (1 and 0); AC-6.4's len(tuple) at 2 hits. Shared precheck run on this revision: PRECHECK: PASS issues=0. THE CLOSURE'S OWN PROMISE WAS THEN SWEPT RATHER THAN ASSERTED, because the paragraph now says every figure derived from this document or a sibling under docs/ is re-derived at 6f0ee85: I ran awk '/^## Version History/{exit}{print NR": "$0}' <doc> | grep '35698f9' and triaged all of them. Seven were sibling- or spec-derived and are re-run by me at 6f0ee85 and RE-STAMPED, every one unchanged in value: the design's seven-plus-two-plus locator (grep -c -> 1); the address grep -c 'Residual on the enumeration itself' on the spec -> 1; both AC-6.1 premise greps (1 and 0); the whole screen-two control set, whose RULE is extracted from the spec's own fenced block (positive 'the 37 files today line at 335f535' returned; true negatives 'Shell mode belongs on the fence, not in the caller.' and 'The tag is the security boundary.' declined; the live '**37** at' form declined as the named FALSE negative; 'Refusal is ... unmeasured.' returned as the named over-reach; printf 'zero files' declined while printf 'one file' matches); the multi-word-gap comparison, where 'three importing test files' is DECLINED by the spec's rule as 74e126f held it and MATCHES as 6f0ee85 holds it; and the codex-leg ledger (ls | sed | sort -n | tail -1 -> 72). A GAP THE SWEEP FOUND THAT NO REPORT NAMED: three .py censuses (6 bash-fence lines, 24 files with any fence literal, 4 with the bash literal) are REPO-WIDE, not scoped to the two roots, so the closure never reached them and their 35698f9 stamps rested on nothing - git ls-files '*.py' | grep -vcE '^(h-mad|handoff)/' -> 411 at 6f0ee85. All three re-run by me at 6f0ee85, all three unchanged, all three re-stamped, and the corpus difference is now stated on the surface that states them. TWO SECTION POINTERS IN THE NEW CARVE-OUT TABLE WERE CHECKED BEFORE SHIPPING, because v1.92's MUST 1 was a pointer to a heading this document does not have: grep -nE '^#{1,4} ' returns no Approach and no 5f heading, so the table reads Scope and 'the 5f bound under Success Criteria', both of which resolve. OWED ELSEWHERE, reported not edited: the spec owes AC-3.11's with/without pair a command and a sha, since its subject is tracked; the spec's own opener mis-stamp is routed there by the decision sheet.
- v1.94: Plan audit v80 at freeze sha cf3a862, two surfaces (doc-auditor teammate: must 3 should 3 nit 3, 8 files / 64 greps; agy: must 9, split five ways below - 3 scope/stamp rejected, 3 unquotable rejected, 3 acted on). All three teammate must-fixes are ONE shape: a new rule reaching further than the sweep run for it. MUST 1, THE THIRD HALF-APPLIED BOUNDARY REPAIR ON ONE EXPRESSION IN THREE REVISIONS: screen one's [Tt]his session branch carried NO boundary on either side and no case-fold, while the paragraph above it asserted in bold that every marker is bounded on both sides and case-folded. Measured on the published v1.93 program over a four-line fixture: it returns 'in this sessionless mode' and 'xthis session glued' (substring hits on both sides) and DECLINES 'This Session capitalised'. Branch repaired to (^|[^[:alnum:]_])[Tt]his [Ss]ession([^[:alnum:]_]|$); the same fixture now returns the two real members and neither substring. The MECHANISM is what v1.94 actually fixes: all three half-applications passed their own control because the control was run on the ALTERNATION, where a healthy sibling covers a sick one - every published fixture line carried 'measured' or 'today' as well, so this branch's state was unobservable through the whole screen. New rule over that axis: EACH BRANCH OF A PUBLISHED ALTERNATION IS CONTROLLED AGAINST ITS OWN FIXTURE, RUN WITH THAT BRANCH ALONE, positive and negative. All three branches now have one and they are named in a list so the correspondence is checkable without counting fences; the today branch's probe is re-stated as a single-branch run and gains a case control (printf 'Today it was measured' -> returned), since its two-line fixture was lowercase throughout and would have passed a lowercase-only branch. Residual stated: nothing enforces that a NEWLY ADDED branch arrives with its own fixture. NO PUBLISHED READING MOVED, and that was measured rather than assumed: over the v1.92 body as 6f0ee85 shipped it the v1.94 program returns the same 32 lines as the v1.93 program, BYTE-IDENTICAL under diff, so the 9/32 widening, the 23 and the five triage categories are untouched. Live impact zero and stated as zero: over the body at cf3a862 the branch alone prints 2 lines and BOTH are also matched by the measured/today branches, so no triage hit ever depended on it. MUST 2, THE CARVE-OUT SWEEP WAS DRIVEN BY RECALL AND WAS TWO MEMBERS SHORT: 'Five members at 6f0ee85, all five checked' omitted the awk boundary probe (which this document explicitly places under that carve-out three paragraphs earlier) and the markdown-it-py grammar corpus. git ls-files awk -> 0 and git ls-files markdown_it markdown-it-py -> 0, so both are genuinely exempt and the VERDICT was right while the SWEEP was not - and a completeness claim is a measurement under decision G. Class closed rather than the two instances filed: EVERY PROBE STAMPED WITH A VERSION OR PLATFORM INSTEAD OF A SHA IS A ROW IN THIS TABLE, and the sweep is driven by THE STAMP. Driver published and run over the body at cf3a862 (before this revision's rows were written into the corpus it scans): grep -cE '(python3?[.:]? ?[0-9]+\.[0-9]+\.[0-9]+|awk version [0-9]|markdown-it-py [0-9])' -> 13 lines resolving to seven distinct probes. Table now eight rows (seven exempt plus the non-exempt wrapper). The carve-out's prose list is demoted to a GLOSS on git ls-files rather than a second condition, because the v1.93 narrowing ('the OS, the kernel or the language runtime') had no room for a third-party renderer; enumerating kinds of outside-thing invites the next kind to be argued about. Residual: A PROBE STAMPED WITH A CALENDAR DATE IS INVISIBLE TO THE DRIVER - the wrapper is the proof, its stamp was 'measured 2026-09-03' and git show 6f0ee85:<plan> | grep -n '2026-09-0' -> one hit. NIT applied in the same edit and it is load-bearing: the middle column now carries the git ls-files ARGUMENT, not the probe's subject. Through v1.93 the wrapper row read 'h-mad/bin/hmad-dispatch' beside 'two paths'; the audit ran the single-path form the cell named, got one path, and filed the row as false. The verdict was right and the cell was unrunnable. MUST 3, A FOURTH REPO-WIDE .py CENSUS: the extractor census's corpus is '.' with --include, the whole repository and not the two roots, so the Measurements closure never reached it and its 35698f9 stamp rested on nothing - the same defect this feature repaired for the three h-mad/handoff censuses one paragraph above the sentence that states the caveat for its own sibling grep. Re-run at cf3a862: same 2 hits, output verbatim. Sweep driven off THE COMMAND'S CORPUS ARGUMENT rather than off which numbers an audit named; the driver grep -oE "grep -r[a-z]* '[^']*' --include='\*\.py' \." over the body at cf3a862 returns 3 (this one, the bare-literal grep -> 6, and the per-file split), all three now stamped at the freeze, and the h-mad handoff form returns 2. Both censuses gain a TRACKED-CORPUS CROSS-CHECK that excludes untracked and generated files and carries a sha: git grep -nE '...' cf3a862 -- '*.py' -> the same 2, git grep -E '```bash' cf3a862 -- '*.py' -> the same 6; if the two forms ever disagree, the git grep form is the one with a sha on it. 411 re-derived at both shas. SHOULD 1: the opener census label 'the commit this revision is audited at' went false the moment v1.93 landed. Census now published at three shas - 9/5 at 35698f9, 20/11 at 6f0ee85 (the commit v1.93 was audited at), 21/11 at cf3a862 with sed x1 -> x2 - and the rule is stated: a sibling-derived census can only be stamped at a LANDED commit, so the label is past tense by construction. awk x1 at all three, so the needle the conclusion rests on survived both moves. SHOULD 2: 'the rule and the screen are written from one list so they cannot drift apart' asserted a guarantee nothing enforces, in the paragraph whose sibling defect is exactly that drift; restated as a convention with the residual, and the reason the mechanical bind is declined (deriving prose from an awk alternation costs more readability than the drift it prevents). SHOULD 3: the closure's right-hand side re-checked and extended to cf3a862 with both commands re-run (git diff --name-only 74e126f cf3a862 -- h-mad handoff prints nothing; the piped form prints 'docs' alone), and 6f0ee85-stamped two-root figures are now inside it. The fence census and the tracked/glob pair are stamped OLDER than 74e126f, which extending the interval cannot help - moving its end does not move its start - so both were RE-RUN instead: 73 across 10 files / control 88 at cf3a862, and 30 tracked / 35 glob at cf3a862, with the embedded shell comment carrying the new sha alongside the old ones. NIT: 'those three words' -> three markers across four words, with why the miscount mattered (it is the two-word branch whose boundaries took three revisions). THE agy LEG'S NINE, EACH ADJUDICATED RATHER THAN DISMISSED IN A BLOCK, and the accounting is written as a five-way split because the round-nine sheet's blanket 'reject the count findings' would have buried three real ones. (a) THREE are the SCOPE/STAMP error a third and fourth time - the '27 at 6f0ee85' body count, the narrowed '10', and the '20 openers at 6f0ee85' distribution, each evaluated against the unscoped current tree; the quoted text exists, the figures reproduce at their stated sha, REJECTED on evidence. (b) THREE quote text that IS NOT IN THIS DOCUMENT AT ANY SHA, checked at cf3a862, 6f0ee85, 35698f9, 74e126f, 0aac0b7, a8e0372 and 335f535 with grep -c returning 0 at every one: 'Every 35698f9 in the body mentions both', 'and every 6f0ee85 in the body mentions both', and 'the only caller is h-mad/tests/test_docsections.py' - REJECTED as unquotable, and the stale-source check was run before saying so, because a fabrication verdict on a quote that merely moved would itself be a defect. The document in fact publishes THREE importing test files, re-derived: grep -rln 'from docsections import|import docsections' --include='*.py' h-mad handoff -> test_docsections.py, test_h_mad_review_evidence.py, test_h_mad_wire_registry.py. (c) THREE WERE ACTED ON: the 6db8e50 --stat claim above (UPHELD outright, and agy alone found it); the carve-out 'two paths' row, where agy's own number was wrong but the reason it got a wrong number was a real defect - the cell named a subject and not the command's argument - so the CELL is fixed rather than the figure; and the [Tt]his session branch, corroborated by the teammate leg and by the sheet, which is must 1 above. NOTHING OWED ELSEWHERE ON 6db8e50: grep -c '6db8e50' returns 3 on the spec, 2 on the design and 0 on the impl-plan, and grep -c 'git show --stat 6db8e50' returns 0 on all three, so no sibling repeats the claim. Within this document the --stat form now survives once, in the sentence that explains why it does not answer the claim, and the addition-scoped form appears at both surfaces that state the five (grep -c 'diff-filter=A 6db8e50' -> 2). NEW: an INHERITED-UNVERIFIED REGISTER in Measurements naming what this revision did NOT re-run (doc-auditor fence-toggle 8/4, the Setext differential, the markdown-it-py 14-case corpus, the three OS probes, the four screen-two legs, and the MEMBERSHIP of the five triage categories - only their total was re-run), because an auditor's silence about a figure is not evidence either way; the register is itself a completeness claim and is not offered as complete. DECISION N APPLIED THROUGHOUT: every reading of this document's own body is taken at a LANDED commit that predates this revision's edit and says so, because a control that publishes its own needle destroys the number it reports.
- v1.95: Plan audit v81 at freeze sha 4e4a00c, two surfaces (doc-auditor teammate: must 4 should 4 nit 3, 12 files / 96 greps, all 12 quote: spans machine-verified; agy: must 1 should 1 nit 1, tools=3). The auditor reproduced every figure it challenged at the sentence own scope and sha and found NO figure arithmetically wrong, so this round is claims and coverage. DECISION Q first pass, and its two rules are now written into the body above the screens: (1) per branch, never per composite; (2) every stated PROPERTY of a screen is a claim about code and is executed by doing the thing it claims immunity from. EXECUTED this revision: fence-body de-indentation on markdown-it-py 2.2.0 AND 4.2.0 (an opener at 3 spaces with body lines at 3/1/0/5 renders a/b/c/2-space-d), which falsifies the extract row wording "a body line indented less than the opener, which is left as is" — CommonMark strips up to N per line, so the 1-space line keeps none; the untracked-file immunity of git grep versus grep -r (a probe .py created, grep -r 6 to 7 while git grep stayed 6, probe removed, read-back recorded); ALL-CAPS on screen one (declines MEASURED/TODAY/THIS SESSION, so "case-folded" was wrong and the claim is narrowed to initial-letter folding with the ALL-CAPS absence measured at 0 over the 4e4a00c body plus a positive showing the grep can fire); three per-branch boundary fixtures each carrying a leading-glued AND a trailing-glued negative plus a case line, replacing v1.94 one-sided pair; per-branch positives for the extractor-census alternation (findall/split/re.compile), the sibling path:line sweep (md/json/sh/toml) and the carve-out stamp driver (python-version/awk version/markdown-it-py), every branch shown to fire against its own fixture. RE-DERIVED at 4e4a00c: closure both commands (nothing, and docs alone) and the closure is now stated as the INTERVAL 74e126f..4e4a00c rather than as a list of shas that went short by one every round; 74e126f body-scoped 26 and narrowed 11, published with the awk body prefix that produces them (a bare grep -c returns 30 over the whole file); design seven-plus-two-plus 1; mutation-target 1; AC anchors 49 with the duplicate check silent; AC-6.1 spec greps 1 and 0; spec len(tuple) 2; spec awk locator 1 with design and impl-plan 0; Residual-on-the-enumeration needle 1; spec opener census 21 over 11 with sed x2 and awk x1, the spec not having moved in cf3a862..4e4a00c (git diff --stat empty); fence census 73 across 10 files control 88 on both corpora; tracked/glob 30/35; 411; extractor census 2 and broad 6 with the per-file split unchanged; the 24 and 4 py-fence controls, re-stamped from 6f0ee85 after the corpus-argument driver was replaced by a CORPUS-SHAPE driver that reaches them (per-branch 5/4/2, union 11, all eleven classified by corpus); ls h-mad/scripts/*.py 37 with git ls-files 37; codex ledger 72 against teammate 81. RELABELLED: freeze is now a defined word — cf3a862 was the commit that RECORDS the round-eight audit whose freeze was 8909ec4, the plan body is byte-identical at the two so no figure moves, and the six body surfaces saying "the audited commit" now say "the freeze"; 4e4a00c is a recording commit too and is never called the audited commit. Also: titled_section binds the find_heading result and checks None BEFORE unpacking (unpacking first raises TypeError and bypasses the loud failure; the impl-plan already writes it this way, 4 hits); the register is driven by the carve-out table and names FIVE OS/runtime probes not re-run, not three; the platform-stamp blind spot is stated beside the calendar-date one (the driver returns 0 on a darwin-only stamp); the 73/88 re-stamp no longer splits its number from its sha across the wrap. NOT EXECUTED and named as contract: the markdown-it-py 14-case grammar corpus (only the new 15th case was run), the five OS/runtime probes of the carve-out table, the Setext differential and its files=25/files=30, the doc-auditor.md 8/4 fence-toggle readings, the pytest collect counts 2809/2547 and the 2748 floor, the live hmad-dispatch run --timeout probe, the four screen-two legs, and the MEMBERSHIP of the five triage categories summing to 32 (neither total nor membership re-run here). PRECHECK: PASS issues=0; every advisory kept deliberately — five STALESHA on a8e0372/335f535/e8eaf6f where the older sha is the point and the freeze re-run sits beside it, PATH advisories for artifacts Phase 5 has not written yet, and every COUNT advisory inside this Version History, which the body declares out of class by construction.
- v1.96: Plan audit v82 at 68a70d6, TWO SURFACES (doc-auditor teammate: must 3 should 2 nit 1, 6 documents at 5 shas, 128 commands, all 9 quote: spans machine-verified; agy p1: AUDITCYCLE PASS must=0 should=0 passes=1, tools=113 ok=113 failed=0 thinking=39906, report committed as doc-block-exec.plan.audit.v82.p1.md and finding nothing). THE ROUND BRIEF SAID THE agy LEG WROTE AN EMPTY VERDICT FILE AND PRODUCED NO VERDICT, AND THAT PREMISE IS FALSE: the verdict file carries a complete AUDITCYCLE line and the p1 report is on disk, so the empty read was of a file still being written. Recorded because a wrong gating status is the same class of defect this revision is fixing - a claim about the machinery, stated in the paragraph that decides what needs re-running. The union is the teammate's three musts; the agy leg is a CLEAN that found none of them, which is a datum about that leg and not evidence about this document. THIS SENTENCE RETRACTS A COMMIT SUBJECT LINE, and the commit is named because history is immutable and git log shows the false premise while only this document carries the correction: 68a70d6 is titled "docs(doc-block-exec): round ten audit -- DECISION Q measured; agy produced no usable verdict", and that is wrong - the leg produced a usable verdict of must=0 should=0 nit=0. Checked rather than asserted, at 7d8e797: docs/01-plan/features/doc-block-exec.plan.audit.v82.p1.md is tracked (git ls-files) and its three headed sections all read None. A reader who trusts the commit subject over this entry is reading the retracted claim. The auditor re-derived every figure at its own scope and sha and found NO FIGURE ARITHMETICALLY WRONG, and reproduced all three of v1.95's self-falsifications independently (the de-indent oracle on markdown-it-py 2.2.0 AND 4.2.0, the untracked probe 6->7->6 against git grep 6->6->6 with the tree left clean, the ALL-CAPS decline). DECISION Q measured: of the 11 property claims v1.95 shipped, 8 were executed and reproduced and 3 were UNEXECUTED - and those three ARE the three must-fixes. So v1.96 executes exactly those three and changes no correct figure. MUST 1 / MUST 2, THE awk BOUNDARY PROBE WAS KEPT OUT OF THE REGISTER ON EVIDENCE THAT WAS NOT THAT PROBE: v1.95 wrote 'the awk boundary probe was re-run here' and cited awk --version plus the three per-branch controls, which the same section says in as many words are NOT this probe. A stamp is not a run. All five legs are now published as one fenced command per leg on awk version 20200816 with the fixture written inline in each, so the mutation each leg applies is named in the leg itself: printf 'measured today\nremeasured todayish\n' | awk '/\btoday\b/' prints nothing; the same fixture through a bare /today/ prints both lines; printf 'a\bb\n' | awk '/\b/' | wc -l returns 1 (counted rather than printed because its one output line carries a raw 0x08 no fence can render, and 0 would be the falsification); the same two-line fixture through the POSIX today branch ALONE prints the first line only; and printf 'Today it was measured\n' through that branch prints its line. Every leg reproduces what the prose above it claims. The register's flat 'the table's remaining two exempt rows are not in this register' is replaced by one bullet per row, which also discharges the NIT: the awk row is OUT (re-run in full), the scanner grammar corpus row is IN for its fourteen and OUT for its fifteenth, addressed by name and never by a sentence ordinal. MUST 3, THE SCREEN-TWO POPULATION WAS SHORT BY TWO AND THIS IS THE THIRD MEMBER OF THE SHAPE: v1.95 named four legs carried at 6f0ee85 while Measurements publishes SIX - the four named plus the multi-word-gap leg ('three importing test files' declined by the spec block as 74e126f held it, returned by the form the same block holds at 6f0ee85) plus the cardinal-alternation leg (printf 'zero files\n' returns nothing while printf 'one file\n' matches, stated At 6f0ee85). Both were outside the closure AND outside the register at once, which the register says cannot happen. Corrected to six at BOTH surfaces (the register and the screen-two clause), derived by WALKING the section and counting its stamped legs. CLASS RULE written over the axis rather than a third instance repair: every cardinal this document fixes over one of its own surfaces is a completeness measurement under DECISION G and is derived by walking the surface it counts, never by recall or by carrying the previous revision's cardinal; residual stated, no shape filter can count a population whose members are prose paragraphs. Its members so far are v1.94's carve-out table (five, was seven), v1.95's register (three OS probes, table listed five) and v1.95's screen-two clause (four legs, six exist), and that list is itself recall-driven and not offered as complete. SHOULD 1, THE audited-WORD SWEEP WAS PUBLISHED WITH A TRIAGE NOBODY HAD RUN IT AGAINST, now EXECUTED at 68a70d6: git show 68a70d6:<doc> | awk '/^## Version History/{exit}{print NR": "$0}' | grep -c audited returns 8, and the three admissible categories account for all eight when the hit list is read - (1) this paragraph's own text, SIX, being the wrong label quoted four times while it is retired, this paragraph's quotation of the slot census, and the sweep's own needle grep -n audited; (2) audited as a verb naming the commit a round measured, ONE, the slot census's 'the commit v1.93 was audited at'; (3) NEW IN v1.96, audited as an ordinary verb about the review process, ONE, Next Steps' 'This plan and the paired design are audited together', which the published triage could classify in NEITHER direction. The word-not-phrase choice is executed too: 8 for the word against grep -c 'the audited commit' 1 over the same body. Both numbers are of a LANDED body and are re-taken at the next freeze, since this paragraph writes the word several more times. SHOULD 2: the ALL-CAPS fixture pipes through the bare three-branch alternation with neither the Version History exit stage nor the !/[0-9a-f]{7}/ stage the shipped screen carries, so 'the screen declines all three' is narrowed to 'the alternation declines all three' with the conflation named. ALSO RE-DERIVED AT 68a70d6, because the document's own rule says each revision re-runs the closure with the new right-hand side: git diff --name-only 74e126f 68a70d6 -- h-mad handoff prints nothing and the piped sed/sort form prints docs alone, so the interval is extended to 74e126f..68a70d6; git diff --name-only 4e4a00c 68a70d6 -- h-mad handoff likewise prints nothing; the body carries 60 occurrences of 4e4a00c (git show 68a70d6:<doc> | awk '/^## Version History/{exit}{print}' | grep -c '4e4a00c'), so THE WORD 'the freeze' IS DELIBERATELY NOT REPOINTED - it means 4e4a00c throughout, a mass re-stamp of sixty surfaces is itself a defect surface, and every reading v1.96 takes on the current body names 68a70d6 in full instead. Residual stated: the closure covers h-mad/ and handoff/ and this document is neither, so the body-scoped self-counts stamped 4e4a00c are readings of the v1.94 body and are NOT claimed at 68a70d6. REPORTED, NOT SILENTLY REPAIRED: the spec's enumeration MOVED between 6f0ee85 and 68a70d6 - its closing noun alternation gained lines?|pins? - so 'carried at 6f0ee85' is carried against a checker that is no longer byte-identical, which is recorded beside the six legs. Also corrected: 'the fence-body de-indentation probe added in this revision' said v1.95's revision and would have read as v1.96's, now stamped v1.95. STANDING METRIC, property claims shipped versus executed: v1.96 ships 8 new property claims and EXECUTES ALL 8 (the five-leg awk probe; the audited sweep's 8 and its phrase-form 1; the six-leg walk of Measurements; the closure's two commands at 74e126f..68a70d6; the same two at 4e4a00c..68a70d6; the 60-occurrence count; the 06ef40f/68a70d6 body-identity diff; and the spec enumeration's between-sha drift), with ZERO unexecuted. NOT RE-RUN and named as contract, unchanged from v1.95 except where stated: the six screen-two legs, the five OS/runtime probes of the carve-out table, the markdown-it-py 14-case corpus, the Setext differential and its files=25/files=30, the doc-auditor.md 8/4 fence-toggle readings, the MEMBERSHIP of the five triage categories, the pytest collect counts and the suite floor, the live hmad-dispatch run --timeout probe, and every body-scoped figure stamped 4e4a00c.
- v1.97: Plan audit v83, freeze sha 6dcb70f, authored against 7d8e797 (the four gated documents are byte-identical across that span: git diff --stat 6dcb70f 7d8e797 over all four prints nothing). EVERY docs/-SCOPED FIGURE THIS REVISION RE-DERIVED AT THE ROUND'S MEASUREMENT COMMIT IS MEASURED AT 7d8e797 AND NOT AT THE FREEZE SHA - which is a claim about that population and not about every figure in the revision, since the members table's cells are stamped at 8909ec4, 7982c18, 06ef40f and f91a74b and the closure list's members at 4e4a00c, each carrying its own sha inside its own command. The two round shas are not interchangeable for one figure: the codex-leg ledger's teammate half is 82 at 6dcb70f and 83 at 7d8e797, so a reader who re-derives at the freeze this entry names gets a different number [clause added in v1.98, which found the entry naming two shas without saying which the figures belong to]. ONE surface produced a verdict: the doc-auditor teammate leg (must 2 should 3 nit 1, 25 files / 131 greps). The agy leg produced NO REPORT - docs/01-plan/features/doc-block-exec.plan.audit.v83.p1.md does not exist on disk - so it is neither clean nor failed and this round is NOT a two-surface result; codex_status is exhausted until 2026-09-07, so nothing here is exit-gate-relevant. DECISION Q for v1.97: 22 property/population claims shipped, 21 executed and ONE NOT [corrected in v1.98 from '22 executed'; the unexecuted one is the members table's 'three importing test files' cell, whose 2 is the reading at f91a74b published against 7982c18, where the stated command returns 1 - the conclusion survives, since presence is all the cell claims, but the self-score did not] - 20 by a published command re-run for this revision, and two (the third residual bullet is not a seventh screen-two leg; the finder screen for docs/-scoped figures misses AC-6.1's spec greps to line-scoping) by reading the prose they are about, which is the only way a prose-population claim can be established and is stated as such at both sites. MUST 1, THE MEMBERS LIST WAS RECALL-DRIVEN AND WRONG ON ALL THREE LABELS, in the paragraph whose entire subject is that such populations are derived by walking: v1.96 read 'v1.94's carve-out table, v1.95's register, v1.95's screen-two clause'. Re-derived body-scoped, every label moves and the cardinal three survives. The carve-out table shipped its short cardinal in v1.93 (8909ec4 carries 'Five members'; the v1.94 stamp driver run over that same body returns 13 matching lines resolving to seven distinct probes) and v1.94 REPAIRED it (7982c18, 'Seven members'). The register's three-OS-probes claim shipped in v1.94 (7982c18 carries 'three OS probes' while that body's carve-out table lists five OS/runtime rows - argparse exit_on_error, AC-5.2 group kill and escape, rmtree on 0o000, the reader-less FIFO, the naturally emptied group) and v1.95 repaired it (06ef40f, 'five OS- or runtime-determined probes'). THE THIRD LABEL IS WRONG IN THE AUDIT REPORT TOO, AND THE TREE SETTLED IT: the screen-two clause shipped in v1.94, not v1.95 - 7982c18 carries 'four screen-two legs' body-scoped AND already contains all six executed legs (the multi-word-gap probe and the cardinal-alternation probe are both in that body: 'three importing test files' 1 [corrected in v1.98 from 2, which is the reading at f91a74b], printf 'zero files' 1; presence is the claim, so any value >= 1 carries it) - and was CARRIED unrepaired through v1.95 (06ef40f, identical clause and identical four-leg enumeration) until v1.96 (f91a74b) made both surfaces read six. The audit report and the round-twelve brief both labelled it v1.95's on the strength of one grep at 68a70d6; the grep hits at 7982c18 as well. CLASS CLOSED, NOT THE TWO LABELS: the axis is which revision SHIPPED a short cardinal versus which merely CARRIED or REPAIRED it, and the rule is that a member is addressed by the EARLIEST landed commit at which both the surface stating the cardinal carries it AND the surface it counts walks to a larger number, with the PREDECESSOR revision returning the needle absent. THREE greps per member, not two, and the third is what dates it: the first two are true at every revision that CARRIES the defect, so on their own they return a range - four screen-two legs is present and the body walks to six at BOTH 7982c18 and 06ef40f - and only the predecessor negative says which shipped it. All three predecessor negatives measured body-scoped and all three are 0: Five members at 6f0ee85, three OS probes at 8909ec4, four screen-two legs at 8909ec4. The list is now a table, one row per member, each carrying its landing commit and all three greps. THREE RESIDUALS: (1) a landing commit is not derivable from a version number without git log --oneline --reverse -S'- v1.NN: Plan audit', so each row carries it; (2) the predecessor negative dates the NEEDLE and not the DEFECT - a revision that shipped the same population-short claim in different words is invisible to it and only re-reading the predecessor finds that; (3) THE RULE PROVABLY CANNOT SEE A POPULATION UNDERSTATED WITH NO NUMBER AT ALL - 'the OS probes' is short by the same amount and there is nothing to grep for. Two details of the published command are load-bearing and both were measured: the awk body prefix, because Version History quotes every cardinal it repairs, so 'three OS probes' returns 2 whole-file at 7982c18 and 1 body-scoped; and -F, because two needles carry ** and without it the cell does not return a wrong number, it FAILS with 'grep: repetition-operator operand invalid'. The table is not offered as complete. MUST 2, THE CODEX-LEG LEDGER WAS CARRIED AT 4e4a00c INSIDE THE SENTENCE FORBIDDING IT, and the prescribed replacement was ALREADY STALE when prescribed. Re-derived at 7d8e797 with the sha inside the command: codex 72, teammate 83. The audit report prescribed 72/82 measured at 6dcb70f; the v83 teammate report is itself the file that moved 82 to 83, which is the point - THE CORPUS OF THIS FIGURE IS A DIRECTORY THIS VERY ROUND WRITES INTO, so it is stale by construction the moment the next report lands and must be re-measured on every revision without exception, which the body now says at the site. The ls-based form v1.96 published is replaced by git ls-tree -r --name-only <sha> with the pattern and the sed/sort/tail pipeline, so the reading is reproducible without a working tree. THREE RESIDUALS, each a way this figure has gone wrong or provably can: the unit is the HIGHEST CYCLE NUMBER and not a file count, and the two forms disagree (grep -c returns 72 for codex, which runs 1..72 contiguously, but only 11 for teammate); the ls form reads the WORKING TREE and diverges from any sha whenever an uncommitted report sits in that directory, agreeing today only because git status --porcelain on that directory filtered to this feature's plan audits returns 0, a property of the moment and not of the derivation; and the comparison says nothing about quality, only about which surface ran. CLASS BEHIND IT, CLOSED: v1.96 pinned 'the freeze' to 4e4a00c while naming 68a70d6 as its measurement commit, detaching every 're-derived at the freeze' obligation from the round's own measurement commit. The rule is now that a docs/-scoped figure is re-derived at THE COMMIT THE REVISION IS MEASURED AT, that commit is named once per revision (v1.97 is measured at 7d8e797), and every such re-derivation carries the sha INSIDE the command. 'The freeze' keeps its meaning - 4e4a00c, which is v1.95's freeze and NOT v1.96's: v1.96's own entry records its round at 68a70d6, so the phrase was already naming a commit one round behind the round that used it - as a past-tense label on readings already taken; body-scoped at 7d8e797 the phrase sits on 32 lines, 20 of them carrying 4e4a00c on the same line, and those twenty are deliberately not re-typed because a mass re-stamp is a larger defect surface than the two standing sentences repointed. Residual: a FUTURE standing obligation written with the bare phrase is caught only by reading, and the shape filter that narrows it (the same grep with -vc) returns the other 12 at 7d8e797 and is a shape filter and never a verdict, since this document hard-wraps and most of the twelve carry their sha on the adjacent line. SHOULD 1, THE docs/-SCOPED FIGURES NOW HAVE A CLOSURE OF THEIR OWN, AND ITS MEMBERS ARE LISTED AND NEVER COUNTED - a cardinal over a prose population is exactly the must-1 defect, so the auditor's 'ten sibling-derived figures' is deliberately not transcribed as a number. Every member is stamped 4e4a00c, was RE-RUN at 7d8e797 and returned its published value, so its stamp is left as written rather than re-typed: design seven-plus-two-plus 1, design mutation-target 1, 49 AC anchors with the duplicate check printing nothing, AC-6.1's two spec greps 1 and 0, spec len(tuple) 2, the spec awk-opener locator 1 with design and impl-plan 0 each, the Residual-on-the-enumeration needle 1, the spec opener census 21 openers over 11 distinct tokens with the distribution unchanged, the impl-plan's found = _dbe.find_heading(text, heading) 4, and - found by me, in neither the audit report nor the brief - the spec-immobility premise the opener census rests on, git diff --stat cf3a862 7d8e797 on the spec being empty as cf3a862 4e4a00c was. THE FINDER SCREEN IS PUBLISHED AS A STARTING POINT AND NOT AS A VERDICT, with the reason measured: grep '4e4a00c' piped to grep -Ei 'spec|design|impl-plan' over the body is LINE-SCOPED while this document hard-wraps, so a member whose sha and whose sibling name land on different lines is invisible to it - AC-6.1's two spec greps are exactly that case and were found by reading. STATED AT THE SITE: this closure DRIFTS BY CONSTRUCTION and must be re-run every round, because the three siblings are revised in the same rounds this document is. The interval closure was re-run too, with 7d8e797 as the new right-hand side from both 74e126f and 4e4a00c (h-mad handoff prints nothing; the piped form prints docs alone), and the body still carries 60 occurrences of 4e4a00c there, this document not having moved in f91a74b..7d8e797. SHOULD 1(b) AND SHOULD 2 TOGETHER: the body-scoped 74e126f self-counts (whole-file 30, body 26, narrowed 11, all three readings of the v1.94 body at 4e4a00c) are now a REGISTER MEMBER instead of an inline residual, because an inline residual is not a register entry and the register's population statement admits no exception. They are entered as UNVERIFIED rather than re-published, and the auditor's endorsement of that restraint is the reason: the paragraph states that no integer in it is the number of covered figures and that the two git diff commands are the whole evidence, so a fourth stamped triple would add three maintained figures and no argument. I re-ran them for the report and they move exactly as the auditor found (30/26/11 at 4e4a00c, 34/29/10 at 68a70d6, 36/30/10 at 6dcb70f and again at 7d8e797) - which is why they belong in the register rather than in the body. The register lead is re-stamped from 68a70d6 to 7d8e797 for the same reason must 2 exists. SHOULD 3: the third residual bullet now says in words that it is a third reason the first bullet's member was missed and NOT a seventh screen-two leg - it carries no command and no fixture and names the same sentence - so a reader walking the section to check the cardinal six does not have to reconstruct that from the closing line. NIT: the v1.96 entry's account of the agy leg now NAMES THE COMMIT WHOSE SUBJECT LINE IT RETRACTS - 68a70d6 is titled 'round ten audit -- DECISION Q measured; agy produced no usable verdict' and that is wrong; the leg returned must=0 should=0 nit=0. Verified at 7d8e797: the v82 agy report is tracked (git ls-files) and its three headed sections all read None. History is immutable, so the pointer is the remedy. PRECHECK: PASS issues=0; every advisory kept deliberately - 12 PATH for artifacts Phase 5 has not written yet, 3 LINEPIN at the sentence that names the values :270/:309/:412 precisely to explain why a value sweep is the WRONG screen, 10 STALESHA where the older sha is the point and the re-run sits beside it (two of them new here, 4e4a00c and 7982c18, both historical stamps with their re-derivation in the same sentence), and all 55 COUNT advisories inside this Version History, which the body declares out of class by construction - zero COUNT advisories fall in the body.
- v1.98: Round-thirteen DELTA SELF-REVIEW of the v1.97 diff (doc-auditor teammate on the diff only: must 2 should 5 nit 2). NOT A GATING ROUND and it stamps nothing; the gating cycle runs after this batch lands. ONE SHA, NOT TWO: freeze and measurement commit are both 1cbddb7, so the two-referent hazard v1.97's own entry created does not arise here, and v1.97's entry is amended in place to say which of its two shas its figures belong to. MUST 1, A CELL PUBLISHING A READING TAKEN BEFORE THE EDIT THAT MOVED IT, inside the table built to close exactly that: row 3 column 2 published 'three importing test files' 2 at 7982c18. Under the command the table states for every cell, git show <commit>:<doc> | awk '/^## Version History/{exit}{print}' | grep -cF <needle>, the readings are 8909ec4 1, 7982c18 1, 06ef40f 1, f91a74b 2, 1cbddb7 4, whole-file at 7982c18 4 - no scope returns 2 at 7982c18, and 2 is the reading at f91a74b. The conclusion survives because presence is all the cell claims, and the cell now says so: any value >= 1 establishes the probe was in that body and the six-leg walk turns on nothing else. The other eight cells were re-run and all eight reproduce (Five members 1 at 8909ec4 and 0 at 6f0ee85; Seven members 1 at 7982c18; three OS probes 1 at 7982c18 and 0 at 8909ec4; five OS- or runtime-determined probes 1 at 06ef40f; four screen-two legs 1 at 7982c18, 1 at 06ef40f and 0 at 8909ec4; six screen-two legs 1 at f91a74b; printf 'zero files 1 at 7982c18). CLASS, NOT THE CELL: the table's own cells are property claims under DECISION Q, so the rule is now that every cell in this table is re-run whenever the table is edited and never carried from the revision that wrote it, with the residual stated that a cell whose command differs from the stated -F form is outside a check written against that form - which is why the two such cells are now named at their cells. THE D-3 SWEEP, RUN OVER THIS WHOLE DOCUMENT AND CLOSED BY A DIFFERENT MECHANISM THAN THE ONE PRESCRIBED: every needle in the members table appears literally in this body, so each cell is a member of the corpus its own screen counts. Paraphrasing the needles would break the cells, so the closure is the commit argument instead - every cell's commit predates the revision in which its needle was first quoted in the table, and that is now written as a rule over every screen this document publishes. Executed, not asserted: three importing test files is 1 body-scoped at 7982c18 and 4 at 1cbddb7, and one of the four is this table's own cell. Residual: the rule covers literal-string needles; a regex-class needle can be matched by prose containing no literal, and the stamp-driven -E driver of row 1 column 2 is exactly such a screen, pinned by the same commit argument. MUST 2, A CARDINAL OVER A LIST IN THE SENTENCE BEFORE THE SENTENCE FORBIDDING ONE: the docs/-scoped closure paragraph led with 'as ten re-stamps' and then said its members are listed and never counted because a cardinal there would be the population-short-by-N claim the paragraph above writes a rule against. The numeral is dropped rather than corrected - it is ten or eleven depending on whether AC-6.1's two spec greps count as one member or two, and a figure that must be maintained on every future edit to the list buys nothing. SHOULD 1: the blanket 'every grep cell above is one command' was false for two cells, and both are now named at the cell - row 1 column 2 runs the stamp-driven -E alternation and is pointed at its owning block rather than re-typed, row 2 column 2 is a hand reading of an eight-row table and involves no grep at all. Row 1 column 2's 13 lines are re-derived (whole-file 16) and THE ASSIGNMENT OF THE THIRTEEN IS NOW PUBLISHED rather than left as an unre-derivable reading, and MY FIRST WRITING OF IT WAS WRONG AND THE RE-RUN CAUGHT IT: I assigned by pattern-matching the stamp text and had to read each line's enclosing block instead, which moved four of the seven. The assignment is argparse exit_on_error 2, awk boundary 2, rmtree on 0o000 2, reader-less FIFO 2, naturally emptied group 2, AC-5.2 group-kill-and-escape 1, markdown-it-py corpus 1 - seven probes over twelve lines - plus one line of prose about the stamp form. Most contribute two because a probe stamps both its prose and its recorded output. It cannot drift, because 8909ec4 is landed. SHOULD 2: the register's population statement claimed a single driver, the carve-out table, and that was already false in the revision that wrote it - the member v1.97 added is not a carve-out row, 74e126f appears in 0 of the eight rows, and neither are the doc-auditor.md fence-toggle readings, the Setext differential or the six screen-two legs. The driver is restated as a walk over two sources - every carve-out row, and every figure the two closure paragraphs hold by ARGUMENT rather than by EXECUTION, since a closure establishes that a reading still holds and never that it was taken again. Residual: the walk is the author's and no screen bounds it. SHOULD 3 AND NIT 1 TOGETHER: the register's copy of the three 74e126f self-counts is replaced by a pointer to the paragraph that owns them, per this document's own rule that a pointer never drifts and a copy does - and the copy had already drifted in the one way a copy can drift without changing a digit, labelling all three body-scoped when one is by construction a whole-file count. SHOULD 4: v1.97's entry named a freeze sha and a measurement sha without saying which its figures belong to, and the ledger reads 82 at the freeze against 83 at the measurement commit; that entry now carries the clause. SHOULD 5: the register's stamp move was justified with an interval that EXCLUDED the stamp being replaced - 68a70d6 is an ancestor of f91a74b and the document changed 149 insertions / 30 deletions across that span. The axis is what the lead stamp asserts, and it asserts NON-EXECUTION and never a value, so the justification is over the half-open interval (old stamp, new stamp] which contains the old stamp by construction; byte-identity is explicitly refused as the premise, since this document did change across 7d8e797..1cbddb7 (158 insertions / 32 deletions) and a member's value can move by a sibling's edit with this document unchanged. Residual: 'no member was re-run in the interval' is knowable from the Version History entries of the revisions in it and by nothing else; a member re-run by a sibling is invisible. NIT 2: the inline residual and the register entry were both live with the register describing the inline one in the past tense; the inline sentence is retained deliberately and now points at the register, the register describes it by role instead of quoting its opening words, and the quotation it used to carry is exactly the copy that would have gone stale in this revision. THE MEASUREMENT COMMIT IS RE-STAMPED TO 1cbddb7 AND EVERY docs/-SCOPED FIGURE WAS RE-RUN THERE, because this document's own rule says a docs/-scoped figure is re-derived at the commit the revision is measured at: the interval closure holds from both 74e126f and 4e4a00c (h-mad handoff empty, the piped form prints docs alone); the body carries 70 occurrences of 4e4a00c at 1cbddb7, up from 60 at 7d8e797 because v1.97's edit added ten, which is the paragraph's point restated as a measurement; 'the freeze' sits on 32 lines, 21 with 4e4a00c on the same line and 11 without, moved from 32/20/12 at 7d8e797 by one line crossing the filter; every closure member returns its published value at 1cbddb7 (design seven-plus-two-plus 1, design mutation-target 1, 49 AC anchors with the duplicate check printing nothing, AC-6.1's two spec greps 1 and 0, spec len(tuple) 2, the spec awk-opener locator 1 with design and impl-plan 0 each, the Residual-on-the-enumeration needle 1, the spec opener census 21 openers over 11 distinct tokens, the impl-plan's find_heading call 4, and the spec-immobility premise with git diff --stat cf3a862 1cbddb7 on the spec empty); and the codex ledger re-derives as codex 72 against teammate 83 at 1cbddb7, unmoved from 7d8e797 only because this round's reports are not committed there - it read 72/82 one commit earlier at 6dcb70f and moves again when they land, which is why the site says without exception. WITHDRAWN, AND RECORDED SO IT IS NOT RE-LITIGATED: I reported to the orchestrator that the v83 teammate report was internally inconsistent on eleven versus ten sibling-derived figures. It is consistent - eleven is ten plus the ledger. No body sentence made that claim, so nothing was owed here, verified by grep for eleven, inconsisten, contradict and self-contradic over the whole document. THREE MORE FOUND WHILE RE-RUNNING, NONE REPORTED BY ANY SURFACE. (a) SCREEN ONE IS A DETECTOR AND THE D-3 RULE AS FIRST WRITTEN CONDEMNED IT: its [Mm]easured branch matches this document's prose by design and its discriminating power is the seven-hex-digit co-occurrence filter, not the absence of the needle - so the rule is scoped to COUNTING screens, whose published value is a count of members, and the detector exception is named with its own residual, that a line carrying the marker and an unrelated seven-hex token is declined for the wrong reason. Screen one was also re-run live rather than reasoned about: it prints 84 lines over the body at 1cbddb7 and 84 over the shipped body of this revision, the two differing only in one line's version number. It printed 85 over an intermediate draft of mine, a state that was never committed and whose reading is therefore not re-derivable and is recorded as process and not as a figure; the extra line was a rule sentence of mine using the bare marker word, reworded to measurement commit. (b) THE LANDING-COMMIT DERIVATION NO LONGER FOUND MY OWN ENTRY: -S'- v1.NN: Plan audit' returns 8909ec4, 7982c18, 06ef40f, f91a74b and 1cbddb7 for v1.93 through v1.97 but nothing for an entry that does not open Plan audit, and this one does not; the needle is generalised to the entry's leading token, verified to return the same five, with the residual that an unlanded revision and an unmatched needle both return silence. (c) the -F property claim quoted an error message without naming the implementation that produces it. An interactive shell here resolves grep to ugrep, which rejects the same pattern with a different message; the load-bearing half, that it FAILS rather than returning a wrong number, holds under both, and the message is now stamped BSD grep 2.6.0-FreeBSD. Every -cF cell and the -cE driver were re-run one by one under both implementations and return identical values, so no published integer depends on which grep the reader has. PRECHECK: PASS issues=0; every advisory kept deliberately - 12 PATH for artifacts Phase 5 has not written yet, 3 LINEPIN at the one sentence that names those values precisely to explain why a value sweep is the wrong screen, 11 STALESHA where the older sha is the point and the re-run sits beside it, and every COUNT advisory inside this Version History with zero falling in the body, which the body declares out of class by construction.
- v1.99: Round-thirteen GATING audit v84 at freeze 700c599 (doc-auditor teammate: must 2 should 3 nit 1). NOT A GATING PASS, no two-surface clean, no exit gate: codex is exhausted until 2026-09-07 11:28 so every surface shares a model family with the authoring surface, and the agy leg returned PASS must=0 should=0 beside two musts one of which the orchestrator verified by execution - the third consecutive round a clean agy leg sat beside real defects, so it is not cited as evidence about this document. MUST 1, CROSS-DOCUMENT AND THE DESIGN OWNS THE ORIGIN: the _field escaper's rationale attached 'which json.dumps leaves literal AND splitlines() breaks on' to a whole set (DEL, the C1 range with U+0085, U+2028/U+2029) and the conjunction is false of most of it. Executed per code point on python 3.11.8 darwin and published under Measurements as 'json.dumps line-breaking, per code point': of 67 Cc/Zl/Zp code points json.dumps leaves 35 literal, and those 35 are SET-EQUAL to the set this document names (DEL + 32 C1 + LS + PS), which is the part that makes the arithmetic checkable; splitlines() breaks on 3 of the 35 (U+0085, U+2028, U+2029); DEL yields 1 line and 31 of the 32 C1 code points yield 1 line. Scope now states the two reasons apart - the three breakers are what the one-physical-line transport invariant AC-4.3 turns on, DEL and the rest of C1 are escaped because an unescaped control is unrenderable inside a verdict line. THE COMPOSITE FIXTURE THE DESIGN CITES IS RUN PER MEMBER, which is DECISION O applied to an inherited fixture: the NEL+LS+PS+DEL heading does split into 4 lines, and minus DEL it still returns 4 while minus NEL, minus LS and minus PS each return 3 - so four lines is what three breaking characters produce and the composite cannot see DEL's (nil) contribution. THE GUARD IS NOT WEAKENED: test_unicode_line_separators_cannot_split_a_verdict_line drives all four (grep -c 'U+0085, U+2028, U+2029 and U+007F' on the impl-plan -> 3 at 700c599, the AC-4.1 row plus two prose restatements, assigned by reading; grep -c 'U+2028, U+2029 and DEL' on the design -> 1), so c1-escape-removed is still killed through NEL. This is a documentation defect, not a behaviour defect, and the design's copy is REPORTED not edited. MUST 2, PROVENANCE ONLY, ONE EDIT: the titled_section end-of-match premise carried a LOCATOR (grep -n 'P<marks>' -> 1) where the paragraph turns on BEHAVIOUR. CLOSED AS A CLASS, not as two members: a sentence naming a stdlib or OS call and asserting what it does is a probe and takes a probe's treatment - a fenced command, its output and its version-or-sha stamp - or it says unexecuted in as many words. FIVE members found and ALL FIVE EXECUTED rather than labelled, so the class ships with no unexecuted member and nothing promoted to a finding on a reading: the json census above; re.search end-of-match, match.end() 4 on '## H\nBody\n' and 5 on '## H\n\nBody\n' with remainder '\nBody\n' both times; a buffered TextIOWrapper deferring the OS write (os.stat st_size 0 after write(100), 100 after flush()); the (st_dev, st_ino) alias key on the OPENED descriptors catching a hard link True and a symlink True with an unrelated file False as the negative control; and unpacking a None result raising TypeError 'cannot unpack non-iterable NoneType object' while bind-then-check reaches the loud failure. RESIDUAL, stated because no screen reaches it: the carve-out sweep is driven off STAMPS, so a premise carrying no stamp at all is invisible to it for the same structural reason the calendar-date member was; a stdlib-symbol driver branch is deliberately NOT built because it would screen the symbols this document happens to use rather than the class. CARVE-OUT POPULATION EXTENDED UNDER ITS OWN RULE: all five probes are stamped python 3.11.8 on darwin, so each is a row, added as a SEPARATELY HEADED BLOCK read at 700c599 rather than mixed into the eight cf3a862 rows, which are untouched and whose readings stand. Population is now thirteen rows, twelve exempt probes and one not; thirteen is a HAND COUNT of two tables and says so, because no row selector separates a row from a sentence quoting one (working-tree body-scoped, counting this sentence's own mentions: the backtick-space form 24, the row-shape form 15 = 13 rows + 2 headers). 74e126f appears in 0 of those 15 lines, a SUPERSET of the rows, which re-derives over the whole population the reading the closure paragraph states over the eight. The fence-body de-indentation case is still not a row - it shares a subject and stamp with the scanner-grammar-corpus row and none of these five shares a subject with an existing row. REGISTER STAMP MOVED 1cbddb7 -> 700c599 by the interval argument RUN rather than recalled: git rev-list --oneline 1cbddb7..700c599 returns exactly one commit, 700c599 itself, and v1.98's entry enumerates its re-runs with no register member among them; not argued from byte-identity, git diff --shortstat 1cbddb7 700c599 reports 157 insertions / 56 deletions. The register's 'five OS- or runtime-determined probes' is re-scoped to the carve-out table's cf3a862 BLOCK, because 'five of the carve-out table' would now read as a claim about twelve exempt probes; the five added at 700c599 were all executed this revision and are not register members. SHOULD 1: collector and gate are NOT locals of the nested run_recipe - they are computed in the enclosing test test_documented_gate_recipe_halts_instead_of_gating_an_empty_path and run_recipe CLOSES OVER them, which is exactly why hoisting to module level would leave them unbound, so the old wording understated its own argument; read by grep -n on the four def/assignment forms at 74e126f, with git diff --stat 74e126f 700c599 on h-mad/tests empty so it holds at the freeze. SHOULD 2: the quantified assertion-shape claim is now LABELLED a hand reading of six functions, bounded by a census rather than by recall (grep -c 'assert |pytest.raises' -> 9 at 74e126f, nine assertion sites across the six functions, every one read). SHOULD 3, AND THE AUDITOR'S OWN SCREEN DID NOT REPRODUCE: its line-scoped grep returns 5 lines that resolve to surface one, surface three and this paragraph's quotations of those two - surface TWO's own carve-out sentence wraps across a line break ('there is no / non-DOCBLOCK exit') and is unreachable by ANY line-scoped grep, which is the same mechanism that made a spec enumeration miss a wrapped claim in v1.91. The screen published instead is PARAGRAPH-scoped and run at the freeze: union 3 paragraphs = the three surfaces, per branch 'exactly one .*verdict' 9/11/19, 'prints exactly one' 9/11/19, 'one *physical* line' 9/11, 'verdict line for' 19, 'no non-DOCBLOCK exit' 11 - so exactly ONE branch reaches surface two's own claim and dropping it leaves a union that is right for the wrong reason. Controls both directions on awk version 20200816: the plain positive fires under both forms, the WRAPPED positive only under the paragraph-joined form, the negative declined by both. Residual: it is a phrase alternation, so a fourth surface worded differently is invisible and the sweep stays by claim; second residual MEASURED AFTER THE LAST EDIT and the estimate would have been wrong - the working-tree run returns 6 where the freeze run returns 3, three added paragraphs being this revision's own screen prose and its two fixtures. NIT: the titled_section regex is reproduced with its re.escape, since a source span this document reproduces verbatim must stay findable by a literal grep. NO LITERAL U+0085, U+2028, U+2029 OR U+007F BYTE IS WRITTEN INTO THIS DOCUMENT - every fixture builds its characters with chr(), because a literal one would make this file's line count differ between awk and any splitlines()-based reader including the precheck; measured after the last edit, python3 counting those four code points in the file -> 0. NOT RE-RUN and named rather than passed over: the markdown-it-py 14-case corpus, the five cf3a862 OS/runtime probes, the doc-auditor.md 8/4 fence-toggle readings, the Setext differential, the six screen-two legs, the three 74e126f self-counts, the pytest collect counts and the 2748 floor, the live hmad-dispatch run --timeout probe, and the membership of the five triage categories. PRECHECK: PASS issues=0; every advisory kept deliberately - 14 STALESHA where the older sha is the point and the freeze re-run sits beside it, 12 PATH for artifacts Phase 5 has not written yet, 3 LINEPIN on the paragraph that quotes replaced line pins as DATA, and every COUNT advisory inside this Version History, which the body declares out of class by construction - the COUNT total is deliberately NOT published, because this entry is itself inside the corpus the precheck scans and a figure that its own publication moves is the self-match defect this revision measured twice elsewhere. ALSO IN THIS REVISION, not in the report: the STAMP-DRIVEN DRIVER is re-run over the extended population, because the rule it implements is what put the five new rows there - per branch, body-scoped, freeze -> working tree, python-version 15 -> 26, awk-version 11 -> 12, markdown-it-py 8 -> 8, union 32 -> 44, with the twelve added lines ASSIGNED BY HAND (each probe contributes its table row plus the interpreter line inside its own recorded output = ten; the eleventh is the class paragraph's prose about the stamp form and the twelfth is the awk-version stamp on the surface screen's controls, which is deliberately NOT a new row because its subject is the awk build the existing awk boundary probe row already owns and the screen it stamps carries a sha). The working-tree readings are of the body BEFORE the resolution paragraph was written and that paragraph then moved them, so the post-last-edit readings are published beside them: 28 / 13 / 8, union 47, the three-line difference being the resolution paragraph itself. And the pointer to the re.search probe is reflowed onto one line - it wrapped, so a literal grep for the pointer name returned 2 where the name occurs 3 times, which is the same defect as the re.escape nit one paragraph away. OWED ELSEWHERE, reported not edited: the design must split the same set by reason and replace its measured: composite citation with the per-member run, in its own words.
- v1.100: Round-fourteen DELTA self-review of the 8c6539a diff (delta reviewer: must 2 should 4 nit 2). ADVISORY AS A GATE, NOT ADVISORY AS FINDINGS - both musts are defects on main and both were introduced by the v1.99 fix, in the paragraph the round-thirteen must rewrote. NO GATING CLAIM, NO TWO-SURFACE CLEAN, NO EXIT GATE: codex is exhausted until 2026-09-07 11:28 and every surface that read this revision shares a model family with the surface that wrote it. Authored against the working tree at 8c6539a, byte-identical to origin/main for this path (git status --porcelain on it returns nothing). MUST 1, THE TWO CROSS-DOCUMENT VERIFICATION GREPS DID NOT READ THE SITES THEY WERE CITED FOR. The axis is cross-document census, not either member, and the rule now written over it is that a sibling census is SCOPED to the sibling's body and EVERY hit is CLASSIFIED before it is described. IMPL-PLAN, re-derived at BOTH shas because the reviewer read 700c599 and the orchestrator read 8c6539a and their line numbers disagree while their KINDS agree: whole-file 3, which is what v1.99 published, body-scoped 2; the three are the _field docstring, the AC-4.1 checklist row and a Version History entry (the v1.25 entry), at both shas. So v1.99's assignment 'the AC-4.1 checklist row plus two prose restatements' is wrong on both non-checklist members - one sits OUTSIDE the body, which is the exact hazard this document states against itself in the spec-enumeration paragraph and then walked into here, and one is a CODE PAYLOAD, the _field docstring reproduced inside Task 1's delta rather than a restatement of the criterion. Fencedness is not readable by a line-scoped grep, so it is published as a fence-aware walk with TWO negative controls, one of which LIVE-DISAGREES: the one-character-run walk calls 1 of the 2 body hits fenced, an any-indent loose-close variant also 1, and a mixed backtick/tilde character class calls 2 of 2, because a prose line carrying a run of both opens a phantom fence. Residual as a category: any cross-document census over this sibling that is not fence-aware in that specific way misreports code payloads as prose. DESIGN: the needle v1.99 published, 'U+2028, U+2029 and DEL', returns 1 body-scoped at 700c599 and 1 at 8c6539a, but that hit is the AC-4.1 PROSE SENTENCE and never touched the c1-escape-removed mutation row it was cited for. Re-pointed at a needle taken from the row itself, 'DEL, C1 controls (U+0085) and U+2028/U+2029 stay literal', which returns 1 body-scoped at both shas and is therefore stable across the design's own v1.104 rewrite of that row's second half; re-measure it if the row is reworded again. The conclusion is unchanged - c1-escape-removed is still killed through NEL whatever DEL does. MUST 2, THE 'UNSCREENABLE' REASON GIVEN FOR A HAND COUNT IS REFUTED BY A SELECTOR THIS DOCUMENT ALREADY PUBLISHES. v1.99 said thirteen is a hand count because no row selector this document could publish separates a row from a sentence quoting one; the register paragraph publishes exactly such a selector and describes it as the one thing every row carries and no other line in the body does. Body-scoped, the line-anchored row form with the backtick-space verb returns 8 at 1cbddb7, 8 at 700c599 and 13 at 8c6539a - the eight rows before the new block, the thirteen after it, headers excluded with no special case because a row goes on to give arguments while both header cells close their span immediately after ls-files. Published with its residual stated as a category: the selector is line-start anchored, so a row quoted verbatim at line start, in prose or inside a fence, would be counted as a row; none exists at this revision, which is why the 13 IS the thirteen rows rather than a bound on them, and that is the thing to re-check when a later revision quotes a row. The hand count of the two tables is kept beside it as an independent cross-check, not as the reason. The same sentence's second half was also false: 'both readings count this sentence's own mentions' holds ONLY of the unanchored backtick-space form; the row-shape form returns 15 = 13 rows + 2 headers and counts NO prose line at all, by the same line-start anchoring that makes the row selector work. MEASURED AFTER THE LAST EDIT, every figure this revision touches or could have moved. Row selector 13 body-scoped over the post-edit working tree, unchanged from 8c6539a because it is line-anchored and this revision adds no line beginning with a pipe; row-shape form 15 at 8c6539a and 15 post-edit, with 74e126f in 0 of those 15. The unanchored backtick-space form moved 24 to 25 BY CONSTRUCTION, because the new paragraph quotes the needle once more - published as 25 with that reason, stamped to a working tree and to nothing else, and flagged as moving again whenever the paragraph is reworded. NOT MOVED, re-run rather than assumed: the stamp-driven driver per branch and body-scoped reads python-version 15 / awk-version 11 / markdown-it-py 8 / union 32 at 700c599 and 28 / 13 / 8 / 47 at 8c6539a AND over this working tree, so v1.99's post-last-edit readings reproduce exactly and the twelve-added-lines partition is untouched; the paragraph-scoped surface screen reads 6 at 8c6539a and 6 post-edit with per-branch ordinals identical (9 11 13 14 15 24 / 9 11 13 14 15 24 / 9 11 / 13 14 15 24 / 11 13 14 15), line-scoped 16 and 16; and python3 counting U+0085, U+2028, U+2029 and U+007F in the file still returns 0. SELF-INTRODUCED DEFECT CAUGHT BEFORE SHIPPING, recorded because the measured failure mode of this loop is that the fix introduces the next finding: the first fence walk written for the impl-plan classification used a mixed backtick/tilde character class and reported 2 of 2 body hits fenced. It is wrong - a prose line in the impl-plan carrying a backtick followed by three tildes opens a phantom fence - and it was caught only by diffing it against a second walk written earlier in the same session, not by reading it. The wrong variant now SHIPS AS A CONTROL beside the correct one rather than being deleted, because a classification whose instrument two reasonable readers implement differently needs its disagreement published. CROSS-DOCUMENT STALENESS THE ROUND ITSELF INTRODUCED, taken from the reviewer's should: v1.99 routed the _field defect to the design's author as work not done here, but the design was repaired in the SAME commit as v1.99. The sentence now names design v1.104 at 8c6539a and publishes the diff grep that shows it (git show 8c6539a --format='' on the design path piped to grep -c on the added split sentence returns 1). HARMONISATION ASYMMETRY STATED RATHER THAN RESOLVED, on the decision sheet's instruction: the two repairs were written independently and agree on every figure and on the two-reason split, but their residuals differ in BOTH directions - this document publishes the set-equality check the design does not, and the design states a residual this document does not carry, a boundary-treated code point outside Cc/Zl/Zp; body-scoped grep -c 'Cf' on the design returns 1, whole-file 2 with the second a Version History entry, which is the same scoping trap again inside the very reading that establishes the point. Neither document adopts the other's residual, so a reader reconciling them needs both. A matching absence count over THIS document is deliberately NOT published, because the needle would have to be written into the sentence publishing it, which is the self-match this revision measures elsewhere. NOT TAKEN and named: the reviewer's three remaining shoulds and both nits. The design's two unexecuted decomposition figures are the design's to fix; the carve-out row covering two premises and the deictic 'this one' in the surface-screen paragraph are left for the gating cycle to weigh, because editing either would move a paragraph population the reviewer re-ran byte-for-byte this round and the decision sheet asks that it not be disturbed. NOT RE-RUN and named rather than passed over: the markdown-it-py 14-case corpus, the five cf3a862 OS/runtime probes, the five 700c599 stdlib probes' own outputs, the doc-auditor.md fence-toggle readings, the Setext differential, the three 74e126f self-counts, the pytest collect counts and the 2748 floor, and the live hmad-dispatch run --timeout probe. PRECHECK: PASS issues=0; advisories 15 STALESHA / 12 PATH / 3 LINEPIN, every one kept deliberately - the STALESHA count rose by one because this revision deliberately cites 1cbddb7 and 700c599 beside 8c6539a, which is the whole point of a reading taken at two shas, and every COUNT advisory sits inside this Version History, which the body declares out of class by construction. OWED ELSEWHERE, reported not edited: nothing new falls to the design or the impl-plan from this revision's two musts, since the design's copy of the _field rationale was already repaired at 8c6539a; the design still owes its two prose decomposition figures (4 lines with DEL removed, 1 with DEL alone) either as executed prints or as a citation of this plan's measurement.
- v1.101: Round-fourteen GATING revision on audit v85 at freeze b3be433 (doc-auditor teammate: must 3 should 4 nit 2). NO GATING CLAIM, NO TWO-SURFACE CLEAN, NO EXIT GATE: codex is exhausted until 2026-09-07 11:28, and the agy leg returned PASS must=0 should=0 on this document while the gating teammate found three musts - the fourth consecutive round of that pattern, so that leg is not cited as evidence about this document in either direction. Measured at b3be433, which is v1.100's landing commit and is byte-identical to the working tree for this path (git status --porcelain on it prints nothing). EVERY PROPERTY CLAIM v1.100 SHIPPED WAS RE-EXECUTED BY THE AUDITOR AND ALL OF THEM REPRODUCED; none is disturbed here. All three musts were in OLDER text and all three are the same shape - a sentence whose referent moved. MUST 1, THE CODEX-LEG LEDGER WENT STALE INSIDE THE SENTENCE SAYING IT MUST NOT, FOR THE SECOND TIME. Re-derived with the document's own published command, one run per sha: 1cbddb7 72/83, 700c599 72/83, 8c6539a 72/84, b3be433 72/84. The teammate half moved to 84 at 8c6539a - the commit v1.100 was authored against - so the published 83 was already wrong there, and neither the v1.99 nor the v1.100 entry mentions the ledger at all. Re-stamped to 72/84 at b3be433 and the whole series published, because the series is the argument. THE CLASS, NOT THE FIGURE: a figure whose corpus is a directory the round itself writes into cannot be carried across a revision under any argument, since the commit that lands the revision also lands the report; the rule is now re-run at the revision's measurement commit and publish, or the entry records the non-run, the register being the only other admissible place. RESIDUAL AND IT IS ALREADY OUTRUN: this round's two v85 reports exist uncommitted at b3be433 and take the teammate half to 85 when they land. Residual (2) is no longer hypothetical either - git status --porcelain on docs/01-plan/features/ filtered to this feature's plan audits returned 0 when v1.98 wrote that sentence and returns 2 now, so the ls-based working-tree form reads 85 where the sha'd form reads 84, which is the divergence that residual predicted [corrected in v1.102: 2 is not a figure. git status --porcelain has no form that runs at a sha, so no reader could reproduce it at any commit, and run as written after the two v85 reports landed in 00b961f it returns 0 - same command, same repository, opposite answer. v1.102 replaces it with the pair of git ls-tree readings that shows the same divergence re-derivably, 84 at b3be433 against 85 at 00b961f]. Residual (1) re-run: the grep -c form returns 72 for codex and 12 for teammate at b3be433, up from 11 at 1cbddb7. The value was swept: the second surface stating the ledger, in the docs/-scoped rule paragraph, carried the series to 83 at 7d8e797 and now records the 84 recurrence; the quality residual's copy of 83 was 84-ed. MUST 2, THE REGISTER WAS STAMPED OLDER THAN ITS OWN MEASUREMENT COMMIT AND EXCLUDED FIVE FIGURES ON A DEIXIS. Re-derived rather than taken from the report: the lead read Inherited-unverified at 700c599, the commit v1.99 is measured at, while v1.100 was measured at 8c6539a - the same detachment the paragraph above it repairs, happening in the paragraph that defines it. Re-stamped to b3be433 with the interval argument RUN: git rev-list --oneline 700c599..b3be433 returns exactly two commits, 8c6539a and b3be433, and both entries enumerate their re-runs with no carried member among them, both instead naming the register's contents under NOT RE-RUN; not argued from byte-identity, git diff --shortstat 700c599 b3be433 reports 482 insertions / 13 deletions. THE INTERVAL ARGUMENT IS NOW EXPLICITLY SCOPED to members already in the register when the stamp moved, because this revision both adds and removes members and the interval says nothing about a figure that was outside the register while it ran. THE DEIXIS IS THE REAL DEFECT: three status assignments turned on the words this revision - the cf3a862 probes membership, the 700c599 probes NON-membership, and the triage categories - and the 700c599 one was false the moment v1.100 shipped, since v1.100's own entry lists the five 700c599 stdlib probes' own outputs under NOT RE-RUN while the register still said they were not members at all. THE FIVE 700c599 STDLIB PROBES ARE ENTERED AS MEMBERS, last executed v1.99 at 700c599, with the rule that a carve-out probe leaves the register only for the revision that executes it and re-enters at the next revision that does not. The members are now a bulleted list, one per line, each carrying the revision or the commit its last execution is stamped at. RESIDUAL PUBLISHED RATHER THAN PAPERED OVER: only two of the six entries name an executing REVISION and the other four name the commit or version their reading is stamped at, because that is what this document records for them and reconstructing a revision number from a stamp is the recall the register refuses. A value sweep on the phrase this revision is the WRONG screen and is said so - it reads 32 body-scoped at b3be433 and most are legitimate; the repaired class is the narrower one of status assignments a later reader will read. MUST 3, THE EXHAUSTIVENESS CLAIM WAS ASSERTED FROM ONE SURFACE AND IS NOW DERIVED FROM FOUR - AND THE AUDIT REPORT'S SHAPE FOR IT IS WRONG. It filed spec pgid=<n> against three siblings' quoted form. Censused body-scoped at b3be433 with EVERY OCCURRENCE CLASSIFIED, the token pgid= carries TWO UNRELATED GRAMMARS - a Python keyword argument to LaunchFailed(stage, err, pgid=...) and a bare field on the emitted verdict line - and ten of the eleven pgid= occurrences in the feature are the kwarg [corrected in v1.102 to ten of the TWELVE: the census three lines up in this same entry sums 1 + 0 + 5 + 6 = 12 and its LaunchFailed( column 0 + 0 + 4 + 6 = 10, so eleven is no reading of the table at any sha. The same wrong denominator is in the 00b961f commit message, which is pushed and takes a bracketed correction in the next commit message, exactly as 8c6539a's did]. Occurrence-level: spec pgid= 1 of which LaunchFailed( 0, pgid: 0; plan 0/0, pgid: 1; design 5 of which LaunchFailed( 4, pgid: 10; impl-plan 6 of which LaunchFailed( 6, pgid: 8. So the emitted-field picture is THREE-WAY and the design DISAGREES WITH ITSELF: the spec spells it bare at AC-4.6 only; the design spells it quoted in its _field example and its verdict table and names pgid: as a detail key four more times, AND spells it bare once in its own AC-4.6 row (the single non-kwarg hit, isolated by grep -oE on a 60/20 window piped to grep -v LaunchFailed); the impl-plan is quoted-only; and this document carries the emitted field in NEITHER spelling. There is no consensus spelling to harmonise on and nothing cross-document is repaired here. What this document now claims is what it derives: the seven bare fields are the seven the design's Verdict lines, one per run. paragraph states, and pgid is quoted in this document's own contract. THE POINTER WAS ALSO BROKEN AND NO AUDIT FILED IT: design v1.79 SECTION-Verdict lines named neither a live version nor a real section - the design has NO heading carrying the word verdict (a heading scan piped to grep -i erdict prints nothing) while grep -c on the paragraph's opening literal returns 1 - so it is re-addressed by that literal. CLASS: an exhaustiveness claim about a set more than one document states is derived by a census over every surface that states it with every occurrence classified by grammar before any is counted, or it is not made. Residual: the needle is a literal string, so a surface stating a member in prose without the token is invisible, and the census bounds spellings and never intent. SHOULD 3 AND ITS CLASS: the cardinal list's member "admissible are ..." occurred ONCE in the whole file, its own list entry, so a reader had nowhere to check; replaced by the three admissible categories, and the class closed by a check every member now passes - each needle returns at least 2 over the PARAGRAPH-JOINED body (tr newline to space, because this document hard-wraps): six screen-two legs 2, Seven members at cf3a862 2, five** OS- or runtime-determined probes 5, twelve exempt probes 2, five members 2, the three admissible categories 2 [corrected in v1.102 to 1, measured at 1cbddb7, 700c599, 8c6539a and b3be433 alike with the entry's own command. That member FAILS the >= 2 check at the sha it is stamped at, and fails it because it is the member being repaired - at b3be433 the list still carried the broken entry, so the replacement phrase existed only at the surface it quotes. The same error breaks the next sentence: over the body v1.101 landed, at 00b961f, the six read 3/3/6/3/3/4, which is +1 for five members and +3 for this one]. Second residual on that check: it establishes findability and never that the surface found is the one the cardinal is about. SHOULD 4, BOTH SCREENS RE-RUN AND THE DELTA READ, un-discharged for two revisions. Screen one returns 92 body lines at b3be433, 92 at 8c6539a, 84 at 1cbddb7 and at 700c599 - so the +8 landed with v1.99 and v1.100 added none - against the last published TRIAGE of 32 over the 6f0ee85 body. The eight were isolated with diff of the program at the two shas and READ LINE BY LINE: all eight are hard-wrapped continuation lines of sentences whose subject is measurement itself, not one an un-stamped provenance claim. ALL-CAPS control re-run: 3 body-scoped at b3be433, all three the control's own fixture, and the same grep on printf 'stamped TODAY with no sha' returns 1. Screen two re-run against the spec's enumeration AS THE SPEC SHIPS IT AT b3be433, which matters because that checker has moved once before under this document's feet: the anchored address returns 1 on the spec at all five shas and 0 on the design and impl-plan at b3be433; over this body the enumeration returns 122 at 6f0ee85, 225 at 1cbddb7, 228 at 700c599, 262 at 8c6539a, 271 at b3be433, published as a DELTA and never as a measurement. ALL SIX LEGS RE-EXECUTED AT b3be433 AND ALL SIX REPRODUCE - the 335f535 positive returns its line, both true negatives return nothing, the blind form returns nothing while the noun-restored form returns 1, the over-reach returns 1 while screen one declines the same sentence, three importing test files is declined by the 74e126f form and returned by the b3be433 form, and printf 'zero files' returns nothing while printf 'one file' matches; Residual on the enumeration itself returns 1 on the spec at b3be433. The six therefore LEAVE the register for v1.101 only. v1.100 named the six nowhere, which is derivable: an awk over the Version History for screen-two leg returns every entry v1.94 to v1.99 plus this one and NO v1.100. NIT 1 CLOSED STRUCTURALLY: the five-name enumeration now sits immediately after its head noun as a bullet, with the twelve-probes aside moved after it, so it can no longer attach to the nearer five. NIT 2: the 25 reading was stamped to a working tree and to nothing else, which discouraged a check that exists - that working tree landed as b3be433 and the 25 reproduces there. It reads 24 at 8c6539a and 25 at b3be433, and it EXCURSED TO 26 AND BACK DURING THIS REVISION'S EDITING: writing the repair with the command spelled out in full added a twenty-sixth match, replacing that spelling with a description returned it to 25, and both moves were found by re-running after each edit rather than by reasoning. The excursion is recorded as PROCESS and not as a figure, an uncommitted intermediate tree being re-derivable by nobody. ALSO MEASURED AFTER THE LAST EDIT AND DELIBERATELY NOT PUBLISHED AS A FIGURE: the stamp-driven driver's working-tree union, because two register bullets rewritten this round each name a probe by its interpreter or renderer stamp, which the driver counts, so the sentence assigning them would have to quote the same stamps again - each publication moves the figure it publishes and there is no fixed point. The 44 partition is untouched, neither addition being a probe or a row, and the landed 28/13/8/47 reproduces at 8c6539a AND at b3be433, so the driver is checkable at a sha whatever a working tree reads. THE SAME SELF-MATCH IS STATED AT THE CARDINAL-LIST CHECK: its six needles read 2/2/5/2/2/2 at b3be433 and one higher over the body this revision ships, because the sentence publishing the check quotes each needle once. FOUND BY ME, IN NEITHER THE REPORT NOR THE BRIEF, AND THE SAME CLASS AS MUST 1: the once-per-revision measurement-commit declaration still read v1.98 is measured at 1cbddb7, three revisions stale, and the freeze-phrase triple beside it read 32/21/11 when the tree gives 37/21/16 - it moved to 37 at 8c6539a with the 4e4a00c half unchanged, so a figure this document publishes twice went stale between the revision that took it and the revision that shipped beside it. Both repaired at b3be433. EVERY docs/-SCOPED FIGURE RE-RUN AT b3be433 AND EVERY ONE REPRODUCED: seven-plus-two-plus 1, mutation-target 1, 49 AC anchors with the duplicate check printing nothing, AC-6.1's two spec greps 1 and 0, spec len(tuple) 2, the spec awk-opener locator 1 with design and impl-plan 0 each, Residual on the enumeration itself 1, the spec opener census 21 openers over 11 distinct tokens with the distribution unchanged, the impl-plan find_heading call 4, and the spec-immobility premise (git diff --stat cf3a862 b3be433 on the spec empty, spec still v1.60). Interval closure re-run from both 74e126f and 4e4a00c with b3be433 as the right-hand side: h-mad handoff prints nothing, the piped form prints docs alone; the body carries 70 occurrences of 4e4a00c, UNMOVED across 1cbddb7, 700c599 and 8c6539a, which is not evidence it need not be re-taken since the two figures beside it both moved. Row selector 8/8/13 extended to 13 at b3be433; the row-shape 15 form holds at b3be433. NOT RE-RUN and named rather than passed over: the markdown-it-py 14-case corpus, the five cf3a862 OS/runtime probes, the five 700c599 stdlib probes' own outputs, the doc-auditor.md fence-toggle readings, the Setext differential, the three 74e126f self-counts, the membership of the five triage categories, the pytest collect counts and the 2748 floor, and the live hmad-dispatch run --timeout probe. OWED ELSEWHERE, REPORTED NOT EDITED: the spec owes its AC-4.6 pgid spelling and the 2486 in its AC-6.4 gate command and BAD_ARGS in AC-4.2's exit-0 enumeration; the design owes the bare pgid= in its own AC-4.6 row, which contradicts its own exhaustiveness paragraph [corrected in v1.102: BOTH pgid items were discharged by 00b961f, the very commit that landed this entry, and were therefore false the moment this sentence was committed. At 00b961f the spec body carries 0 bare pgid= and FR-4 spells pgid:, and the design's AC-4.6 row carries 2 pgid: and 0 bare pgid=, its four remaining pgid= all being LaunchFailed( kwargs; the three commands are published in the body. Neither author was at fault and neither could have seen it: design v1.106 wrote the mirror-image debt against the spec in the same commit, and this document wrote that the class was open across the feature - three documents recording one debt that one commit discharged. The other TWO items in this list are NOT discharged and still reproduce at 00b961f: the spec's 2486 in AC-6.4 (1 body-scoped) and the absence of BAD_ARGS from AC-4.2's exit-0 enumeration (0 in the AC-4.2..AC-4.3 range)].
- v1.102: ADVISORY delta-review revision on the r15 delta report of 00b961f (must 6 should 3 nit 1). NO GATING CLAIM, NO TWO-SURFACE CLEAN, NO EXIT GATE: this answers an advisory review, not an audit cycle, and codex is exhausted until 2026-09-07 11:28. MEASUREMENT COMMIT AND WHY IT IS A PAIR: v1.102 is measured at dfae038, and 00b961f also appears in its readings; the two are not assumed interchangeable but measured to be - git diff --stat 00b961f dfae038 over the four feature documents is EMPTY, the two intervening commits touching docs/handoffs/ alone [FALSE, corrected in v1.103: df04e8e touches a handoff file alone but dfae038 touches docs/learnings.md and docs/skill-candidates.md as well, per git show --name-only --format='' dfae038; the sed directory-collapse below cannot distinguish a top-level file directly under docs/ from one in a subdirectory, the claim came in from the round-fifteen orchestrator decision sheet, and the byte-identity conclusion it supports is unaffected] (git diff --name-only 00b961f dfae038 | sed 's|/[^/]*$||' | sort -u prints docs and docs/handoffs). So a reading whose corpus is one of the four documents is stamped 00b961f, the commit those bytes landed at; a reading whose corpus is wider is stamped dfae038. FIVE OF THE SIX MUSTS SIT IN TEXT v1.101 ITSELF WROTE, which is the fourth consecutive round of that pattern, and TWO of them falsify that round's own headline claims. MUST 1, A PUBLISHED FIGURE THAT DOES NOT REPRODUCE AT THE SHA IT IS STAMPED AT. The cardinal-list >= 2 check published 2 for the one member the check was written to repair; the document's own command (awk to strip Version History, tr newline to space, grep -oF, wc -l) returns 1 at 1cbddb7, 700c599, 8c6539a and b3be433 alike, line-scoped and joined alike, while the other five reproduce exactly at 2/2/5/2/2. Published as 1, with the reason stated rather than the digit quietly swapped: that member FAILS the >= 2 check at the stamped sha BECAUSE it is the member being repaired - at b3be433 the list still carried the broken entry, so the replacement phrase existed only at the real surface it quotes and had no list entry to be its second occurrence. THE CLASS: a check introduced by a repair is evaluated against the body the repair produces, never against the body it repaired, and where the two differ both readings are published and named. THE FOLLOWING SENTENCE WAS BROKEN THE SAME WAY and is corrected with it: v1.101 claimed all six read exactly one higher over its own body; re-derived at 00b961f the six read 3, 3, 6, 3, 3 and 4, which is +1 for five members and +3 for the sixth, whose three added sites are its cardinal-list entry, the sentence recording what it replaced, and its appearance in the needle list. That delta is now stamped at 00b961f rather than at the body this revision produces, because an unlanded self-count is re-derivable by nobody - which is this document's own rule, broken by the sentence stating it. v1.102 moves all six again and does not publish its own body's readings. MUST 2, THE pgid DENOMINATOR CONTRADICTED THE CENSUS THREE LINES ABOVE IT. The fenced census re-run byte-for-byte at b3be433 reproduces exactly and sums 1 + 0 + 5 + 6 = 12 pgid= across the four documents, of which LaunchFailed( accounts for 0 + 0 + 4 + 6 = 10. Ten of the TWELVE, not eleven; no reading of the table yields 11. Corrected in the body and BOTH integers rewritten as the arithmetic over the fence's own columns, which is the class: every integer this document states about a table or fence printed in this same document is written as the arithmetic over that surface's values, never as a free-standing figure, so the check a reader runs is addition on the page. Residual: the rule makes the summary re-derivable from the fence and says nothing about whether the fence is right. THE VALUE WAS SWEPT ON ALL THREE SURFACES IT SITS ON: the body (edited), the v1.101 Version History entry (bracketed correction), and the 00b961f COMMIT MESSAGE, which is pushed and cannot be amended - it takes a bracketed correction in the next commit message, exactly as 8c6539a's did, and that is flagged to the orchestrator rather than fixable here. Sweep command, newline-collapsed because this document hard-wraps: tr '\n' ' ' < <doc> | grep -oiF 'ten of the eleven' | wc -l returns 1, the surviving hit being the bracketed Version History entry [WRONG FIGURE AND WRONG SURVIVOR SET, corrected in v1.103: that command run at af19d53 returns 3, not 1 - the v1.101 bracketed correction, this sweep command's own needle, and this entry's closing sentence, two of the three being the sweep's self-matches; the substantive claim is the body-scoped reading, awk to strip Version History then tr then grep -oiF then wc -l, which returns 0 at af19d53. The 1 was a reading of an uncommitted intermediate tree, which is this same entry's MUST 6 class broken in the entry that states it]. MUST 3, THE PARAGRAPH'S CONCLUSION WAS FALSE AT THE COMMIT THAT LANDED IT. v1.101 wrote that the emitted-pgid spelling is open across the feature until the spec's AC-4.6 and the design's AC-4.6 row each settle their text. 00b961f settled BOTH, in the same commit that landed the sentence. Re-derived at 00b961f, one command per reading, all three published in the body: the spec body carries 0 bare pgid= and FR-4 spells pgid:; the design's AC-4.6 row carries 2 pgid: and 0 bare pgid=; the design's four remaining body pgid= are ALL LaunchFailed( constructor kwargs. The census stays stamped at b3be433 and its conclusion is re-stated in the PAST TENSE against that sha, with the landing-commit outcome named beside it. THE CLASS IS THE TENSE OF A CLAIM ABOUT ANOTHER DOCUMENT: a sentence saying a sibling still owes something is a measurement of a tree that the very commit publishing it changes, and THREE of this feature's four documents each recorded this same debt in 00b961f while 00b961f discharged it - no author could see it, each having read siblings revised in the same batch. The rule: such a claim is written at a named sha and in the past tense, and the revision's own entry names the outcome at its landing commit or records that the landing commit was not read. Residual, not closeable from inside one document: when the author writes the sentence the landing commit does not yet exist. THE TWO NON-pgid ITEMS ON THAT OWED LIST ARE NOT SWEPT AWAY WITH IT and both reproduce at 00b961f, verified rather than assumed: the spec's 2486 in AC-6.4 (grep -c over the awk-stripped body returns 1) and the absence of BAD_ARGS from AC-4.2's exit-0 enumeration (0 over the AC-4.2..AC-4.3 sed range). AN ERROR I MADE AND CAUGHT WHILE WRITING THAT SECOND COMMAND, RECORDED BECAUSE IT IS A GENERAL PROPERTY AND NOT A TYPO: written first as a bare sed range over the whole file it returned 1, not 0, because AC-4.2 recurs in the spec's own Version History where sed opened a second range that never met its terminator and printed to EOF. Class: an unterminated sed address range prints to end of file, so a range command over a document with a Version History is awk-scoped to the body BEFORE the range is applied. The shipped command is the scoped one and its range output is printed, not only counted. MUST 4, A PLACEMENT CLAIM REFUTED BY THIS DOCUMENT 39 LINES BELOW IT. v1.101 wrote that the two figures beside the 4e4a00c self-count are beside it in this section; the paragraph is inside Measurements while the codex-leg ledger is published in Next Steps, whose corpus the Measurements closure explicitly excludes - so the ledger is not merely elsewhere, it is definitionally outside. Each of the two is now named with the section that holds it. CLASS: a placement claim is a claim about a heading; beside it, above, below and in this section are all readings of a layout the next revision moves, and the check is grep -nE '^#{2,4} ' against the site's own position. Residual: nothing detects a WRONG section name, only a missing one. MUST 5 PLUS THE NIT, ONE CONJUNCTION AND ONE DUPLICATED LEAD. The register's per-member lead claimed every member names the revision AND the commit; four of its six bullets falsified that on sight and the register's own residual denied it 63 lines down, which discloses the gap without discharging it. The lead is now the exact disjunction - revision, commit, OR, for a carve-out probe no repository sha determines, the runtime or renderer version - which admits the markdown-it-py bullet's NEITHER case that or alone still over-claims for. CLASS: a lead asserting a uniform property of a list is checked against every member before it is written, and states the disjunction where the property does not hold uniformly. THE SECOND LEAD IS DELETED rather than also corrected: v1.101 carried two leads for one list 23 lines apart with different quantifiers, which is the copy-that-drifts shape this document argues against everywhere else, and they had already drifted. MUST 6, A FIGURE PUBLISHED IN A GRAMMAR THAT HAS NO SHA, IN THE SENTENCE WHOSE SUBJECT IS WORKING-TREE-VERSUS-COMMIT CONFUSION. Residual (2) demonstrated its own point with git status --porcelain ... | grep -c returning 2 right now. That command has no form that runs at a sha, so no reader could reproduce the 2 at any commit, and run as written at dfae038 it returns 0 because the two v85 reports landed in 00b961f - same command, same repository, opposite answer, with nothing saying which tree the reader is in. Replaced by the pair of git ls-tree readings that shows the same divergence re-derivably: 84 at b3be433 against an ls-based 85 for the whole interval the reports sat uncommitted, both agreeing at 85 at 00b961f. The ls-based form's value ACROSS that interval is an inference from when the reports were written and when they landed, not a reading anyone took at each intermediate moment, and it is stated as such rather than as a series. CLASS: a reading of an uncommitted working tree is recorded as a dated observation and never published as a figure, exactly as the 25-26-25 editing excursion two sections away already is. Residual: a pair of ls-tree readings shows the halves DID diverge across an interval and cannot show they are diverging at the moment of reading, and nothing re-derivable can. THE LEDGER ITSELF IS RE-RUN AT THIS REVISION'S MEASUREMENT COMMIT, as its own without exception rule requires and as two consecutive revisions failed to do: codex 72 against teammate 85, run at BOTH 00b961f and dfae038 and identical at each, with the sha inside the command. The series is extended rather than re-stamped: 1cbddb7 72/83, 700c599 72/83, 8c6539a 72/84, b3be433 72/84, 00b961f 72/85. v1.101's residual predicted exactly this and was right; the same prediction is now stated against THIS reading, which stops being correct the moment round fifteen's own reports are committed. SHOULD 1, A PREMISE RETIRED BY THE REVISION'S OWN COMMIT. The spec-immobility premise the opener census rests on is true at b3be433 and dead at 00b961f, which ships spec v1.61: git diff --stat cf3a862 00b961f on the spec reports 41 insertions / 15 deletions. The census VALUE survives and is re-derived rather than inferred - git show 00b961f:<spec> | grep -oE '^  \$ [a-zA-Z0-9._-]+' | sort | uniq -c still gives 21 openers over 11 distinct tokens, distribution unchanged - which is the point: an immobility premise licenses NOT re-deriving, so when it dies the reading is re-taken and never argued. CLASS: a premise that a sibling has not moved is a figure with a right-hand sha and expires at the next commit touching that sibling, including this document's own landing commit, which is where it expired both times. SHOULD 2, A CHECKER THAT MOVED UNDER SIX LEGS. The six screen-two legs were re-executed at b3be433 against the spec's enumeration as that document ships it at b3be433, and the spec moved at 00b961f. Diffed rather than assumed: diff of the fenced enumeration and its 14 following lines between b3be433 and 00b961f returns a SINGLE changed line, v1.60 draft to v1.61 draft, in prose BELOW the fence; the program is byte-identical and grep -cE '^  \$ awk ' returns 1 on the spec at both shas. The six readings survive their checker's revision, measured and not assumed. CLASS: a leg run against a checker living in another document carries that checker's sha too, and a revision moving that document either re-runs the legs or diffs the checker and says which. THE SIX ALSO RE-ENTER THE REGISTER, because v1.102 did not re-run them and the register's own rule is that a leg leaves it only for the revision that executes it - the same deixis defect v1.101 fixed for the stdlib probes, which would have recurred here by silence. The register's member cardinal moved from six to seven and was re-derived by WALKING the bullets rather than incremented, and its residual arithmetic moved with it: three of the seven now name an executing revision, three name a commit, one names neither. SHOULD 3, the register residual's it says the reading is not this revision's is replaced by the number: not v1.102's. v1.101 is DELIBERATELY NOT in that predicate, at both the lead and the residual - v1.101 DID execute one member, the six screen-two legs, so a lead saying no member's last execution is v1.101 would be false for exactly the bullet this revision re-entered. Caught before shipping by reading the lead against every bullet, which is the same check MUST 5 writes a rule about. REGISTER STAMP MOVED from b3be433 to dfae038 with the interval argument RUN, not recalled: git rev-list --oneline b3be433..dfae038 returns exactly three commits, of which only 00b961f touches any of the four feature documents (df04e8e and dfae038 touch docs/handoffs/ alone, checked per commit) [FALSE, corrected in v1.103: dfae038 also touches docs/learnings.md and docs/skill-candidates.md; the parenthetical asserted a per-commit check that was not run, and only 00b961f touching any of the four feature documents - the claim this sentence needs - is unaffected]; 00b961f's entry enumerates its re-runs and names the register's contents under NOT RE-RUN with no member among them except the six screen-two legs, which it DID execute and which are therefore entered stamped to it rather than covered by the interval. Not argued from byte-identity, which would be false: git diff --shortstat b3be433 00b961f on this document reports 348 insertions / 91 deletions. WHAT v1.102 DID NOT RE-RUN, named rather than passed over: every docs/-scoped figure v1.101 stamped at b3be433 is left at that stamp and NOT re-measured - b3be433 is immutable and those readings are correct there, so a mass re-stamp would replace true sentences with newly-taken ones and add a defect surface for no argument. The readings v1.102 DOES take are LISTED, NEVER COUNTED - a cardinal over a prose list is the population-short-by-N claim this document writes a rule against, and a first draft of that sentence said three and named three while the transcript holds more. They fall in two kinds: readings that REPLACE a b3be433 value that was wrong, expired or unrunnable (the codex-leg ledger, the retired spec-immobility premise, the cardinal-list post-repair delta, residual (2)'s divergence pair), and readings that are NEW, settling a cross-document state no earlier revision measured (the three pgid discharge commands, the two still-owed spec commands, the spec enumeration diff, and the h-mad//handoff interval closure). THE CLOSURE WAS ADDED AFTER A CROSS-DOCUMENT CORRECTION from the orchestrator moved this batch's freeze sha to dfae038, and it is the one reading that rule caught which I had missed: its corpus is h-mad/ and handoff/, WIDER than the four feature documents, so this revision's own stamp rule sends it to dfae038, while v1.101 had run it only at b3be433. Re-run at dfae038 and it HOLDS - git diff --name-only 74e126f dfae038 -- h-mad handoff and the same with 4e4a00c on the left both print nothing, and both piped sed 's|/.*||' | sort -u forms print docs alone. Left at b3be433 it would have been carried across two commits on the strength of the four documents being byte-identical across them, which is a fact about docs/ and says NOTHING about h-mad/. THIS ENTRY STAMPS NO SEPARATE FREEZE FIELD and never carried one - it names dfae038 as its measurement commit, which is the same sha the correction settles as this batch's freeze. FOUND WHILE VERIFYING THIS VERY ADDITION, and recorded because it is the document's own hazard biting its author: my first replacement needle for the body sentence returned 0 because the phrase straddles a hard wrap (the spec / enumeration diff), which is exactly why every count in this document collapses newlines first. Also not re-run: the markdown-it-py 14-case corpus, the five cf3a862 OS/runtime probes, the five 700c599 stdlib probes' own outputs, the doc-auditor.md fence-toggle readings, the Setext differential, the three 74e126f self-counts, the six screen-two legs, the membership of the five triage categories, the pytest collect counts and the suite floor, and the live hmad-dispatch run --timeout probe. OWED ELSEWHERE, REPORTED NOT EDITED, and STAMPED rather than stated in the present tense - which is this entry's own MUST 3 rule applied to the sentence that would otherwise have broken it one round after writing it. AT 00b961f, two of v1.101's four items had been discharged (both pgid) and two reproduced: the spec's 2486 in AC-6.4 and the absence of BAD_ARGS from AC-4.2's exit-0 enumeration, by the two commands published in the body. OBSERVED LATER, IN AN UNCOMMITTED WORKING TREE AND THEREFORE RECORDED AS A DATED OBSERVATION AND NOT AS A FIGURE (the MUST 6 rule, same round): while the r15 batch was still being authored the spec reached an uncommitted v1.62 in which BOTH remaining items are discharged - BAD_ARGS now sits in AC-4.2's exit-0 enumeration (the range opens exactly once in that body, checked, so the reading is not a range leak), and the only two surviving 2486 hits are retrospective, naming it as the retired half of the 2748/2486 pair. So this document's OWED ELSEWHERE list is EMPTY as of that observation, and empty at no sha yet. The next revision re-derives it at a commit rather than carrying this sentence, because a working tree is re-derivable by nobody - which is the whole content of MUST 6. The 00b961f commit message owes a bracketed correction for ten of the eleven in the next commit message.
- v1.103: GATING revision, answering the c86 audit that FAILED on BOTH surfaces at freeze 3f70eb3: the teammate leg must=4 should=4 nit=2 and the codex leg must=4 should=1, a DIFFERENT MODEL FAMILY, neither having seen the other, and the two must sets are IDENTICAL one-for-one. NO GATING CLAIM, NO TWO-SURFACE CLEAN, NO EXIT GATE is claimed by this entry - it answers an audit, it is not one. ONE MEASUREMENT COMMIT AND NO PAIR: v1.103 is measured at af19d53. v1.102 named two commits as the one it was measured at - dfae038 in the closure paragraph and 00b961f at the ledger's own site - which is MUST 4 on both legs, and the repair is not to reconcile the pair but to ABOLISH it: every reading v1.103 takes is run at af19d53 with the sha inside the command, and a reading inherited from an earlier revision keeps the blob it was stamped at and does not move. CLASS: one revision, one measurement commit; a second sha appears only as the stamp on an inherited or historical reading, never as a second answer to measured at. The four documents are byte-identical 3f70eb3 through af19d53 (git diff --stat 3f70eb3 af19d53 over the four is empty) and this plan is byte-identical from 59cc2ad, its own landing commit, through af19d53 (git diff --stat 59cc2ad af19d53 on this path is empty at 7b182b0, 3f70eb3, 4c1c3a5, b442a80, 7b9d174 and af19d53 alike) - stated as an inherited-blob fact, not as a licence to skip a re-run. MUST 1, AN ATTRIBUTION RESTATED BESIDE THE SERIES IT SUMMARISES INSTEAD OF DERIVED FROM IT. The ledger's prose said v1.101's published pair was 72/83; v1.101 published 72/84. Re-derived two ways at the same commit: git show 00b961f:<plan> | tr newline to space | grep -oE 'codex .72. against teammate .[0-9]+. at .[a-z0-9]+.' returns codex 72 against teammate 84 at b3be433, and the same command at b3be433 and at 8c6539a both return 72/83 at 1cbddb7 - so 72/83 is what v1.99 and v1.100 published, stamped at 1cbddb7, and the whole recurrence clause that followed the attribution belongs to those two revisions and not to v1.101. Rewritten to name the revisions by their rows in the series printed three lines below, so the reader's check is reading the table rather than trusting the sentence. CLASS, and it is the same axis as v1.102's own MUST 2 widened from integers to attributions: any claim this document makes about which revision published which value, where the series is printed on the same page, is written as a pointer into that series and never as a free-standing restatement. Residual: the rule makes the summary re-derivable from the series and says nothing about whether the series is right, which is why every row of it was re-run for this revision. MUST 2, A WORD THIS DOCUMENT NEVER MEASURED, INHERITED FROM AN ORCHESTRATOR SHEET. Three sites said df04e8e and dfae038 touch docs/handoffs/ alone. FALSE, and the command printed beside two of them refutes it: git show --name-only --format='' dfae038 returns docs/handoffs/2026-09-05-main__doc-block-exec-rounds-twelve-to-fourteen.md, docs/learnings.md AND docs/skill-candidates.md, while git show --name-only --format='' df04e8e returns its handoff file alone. PROVENANCE, recorded because the correction is otherwise unattributable: the sentence originated in the ORCHESTRATOR's round-fifteen decision sheet, which asserted it without measuring it, and the round-sixteen sheet's FACT 3 records that it propagated to eight surfaces across four documents. THE CONCLUSION IS UNAFFECTED AND IS NOT OVER-REPAIRED: only 00b961f touches any of the four feature documents in that interval, verified per commit, so both the byte-identity argument and the register's interval argument stand unchanged; only the word alone is wrong. THE SWEEP WAS BY VALUE ACROSS EVERY SURFACE, newline-collapsed because this document hard-wraps, AND THE NEEDLE HAD TO ADMIT MARKUP: tr newline to space | grep -oE 'handoffs/.{0,2} alone' | wc -l returns 4 at af19d53 - two in the body, where the phrase is written docs/handoffs/ inside backticks, and TWO MORE inside the v1.102 Version History entry, where the same entry strips them. All four are corrected or bracketed. AN ERROR I MADE AND CAUGHT WHILE SWEEPING, recorded because it is the general property and not a typo: my first needle was 'handoffs/? alone', which cannot match across the closing backtick and returns 2 at af19d53 - and 2 is exactly what the r16 decision sheet publishes for this document, so the sheet's count and my first count were the same MARKUP-BLIND reading rather than two agreeing measurements. CLASS, and it is the sibling of the hard-wrap rule this document already carries: a value sweep over a markdown document collapses newlines AND admits the inline-code delimiters around the value, because the surfaces that state a value in prose and the surfaces that state it inside backticks are the same population and only one of them is visible to a bare needle. Residual: the .{0,2} form admits a delimiter and cannot admit an arbitrary one, so a value split across a link or an emphasis run is still invisible; the falsifier is to run the needle without the collapse and without the delimiter class and compare the three counts, which is what caught this. CLASS: a set claim derived from a path list collapsed to directories by sed 's|/[^/]*$||' cannot distinguish a top-level file directly under docs/ from one in a subdirectory, so a claim about WHICH FILES a commit touches is read off --name-only unpiped, and a claim about directories says directories. MUST 3, A SELF-COUNTING SWEEP THAT PUBLISHED A NUMBER FROM AN UNCOMMITTED TREE. The v1.102 entry published its ten of the eleven sweep as returning 1. Re-run exactly as written at af19d53, whole-file and newline-collapsed: 3. Body-scoped, which is the reading that carries the substantive claim: awk to strip Version History, tr newline to space, grep -oiF, wc -l returns 0. Both readings are now published with the grammar that produced each, stamped at af19d53 - a commit that predates this entry, which is what makes them re-derivable at all, since the needle appears literally inside this entry too. The three whole-file hits are all Version History records: the v1.101 entry carrying its own bracketed correction, the v1.102 entry's sweep command, and the v1.102 entry's closing sentence. THEY ARE NOT REPAIRED - they are dated records of what those revisions published, and rewriting them would destroy the provenance the corrections exist to carry. CLASS: a screen whose published value counts occurrences of its own needle is stamped at a commit that predates the text stating it, and its body-scoped and whole-file readings are BOTH published, because they answer different questions and only one of them is the claim. MUST 4 is the measurement-commit collision, closed above. SHOULD 1, A PRESENT-TENSE DEBT DISCHARGED BY A SIBLING. The two still-owed spec commands was written with no sha and in the present tense, which is the exact form v1.102's own MUST 3 writes the rule against. Both are discharged at af19d53 by spec v1.62 and the readings are published rather than asserted: body-scoped 2486 returns 2 at af19d53 against 1 at 00b961f, both survivors retrospective, and BAD_ARGS inside the awk-scoped AC-4.2..AC-4.3 range returns 2 at af19d53 against 0 at 00b961f, with the range's opening address occurring exactly ONCE in that body at both shas, so neither reading is a range leak. The site now names the pair by what it measures and stamps its status. FOUND WHILE RE-RUNNING, NOT ROUTED BY ANY LEG, AND THE LARGEST MOVE IN THIS REVISION: THE STANDING CODEX DEBT IS DISCHARGED. The ledger's premise - the last audit of this document carrying a codex leg is cycle 72, every cycle since running on the substitute - is dead at af19d53. Re-run at af19d53 with the sha inside the command, both halves read 86: codex 86 against teammate 86, up from 72/85 at 00b961f, dfae038 and 3f70eb3. The v86 codex report landed in 4c1c3a5. The series is extended and no row re-stamped: 1cbddb7 72/83, 700c599 72/83, 8c6539a 72/84, b3be433 72/84, 00b961f 72/85, dfae038 72/85, 3f70eb3 72/85, af19d53 86/86. v1.102's residual predicted exactly this and was right for the third consecutive revision; the same prediction is restated against this reading, which stops being correct the moment round sixteen's own reports are committed. The standing-debt paragraph is rewritten in the PAST TENSE at its shas rather than deleted, because the thirteen-cycle gap it records is the evidence for the rule. SECOND FINDING, AND IT BREAKS A CLOSURE THIS DOCUMENT HAS CARRIED SINCE v1.95: THE h-mad//handoff INTERVAL IS NO LONGER EMPTY. git diff --name-only 74e126f af19d53 -- h-mad handoff prints h-mad/scripts/h_mad_assemble_audit.py and h-mad/tests/test_h_mad_assemble_audit.py, and so does the same command with 4e4a00c on the left; the control at 3f70eb3 still prints nothing, so the break is af19d53 itself. The blanket every 4e4a00c-stamped tree reading is provably still true is therefore RETIRED and replaced by a named two-file exception: the interval changes exactly two paths, both h_mad_assemble_audit, and the tracked markdown corpus those readings are taken over is unmoved - git ls-tree -r --name-only <sha> -- h-mad handoff | grep '\.md$' | grep -v '/archive/' | wc -l returns 30 at 74e126f, 4e4a00c, 3f70eb3 AND af19d53. The one body site that reads either changed file is the suite-floor bullet, and af19d53 moved it again by construction: def test_ in test_h_mad_assemble_audit.py goes 7 at 74e126f, 4e4a00c and 3f70eb3 to 12 at af19d53, five new tests, which is the SECOND time that same file has moved the floor and the reason the bullet's re-measure-at-5c-branch-time residual is not theoretical. CLASS: an emptiness closure over a directory is a figure with a right-hand sha and expires at the next commit touching that directory, INCLUDING a commit that touches nothing this feature owns; when it expires it is replaced by the enumerated diff and not by a re-assertion. REGISTER STAMP MOVED from dfae038 to af19d53 with the interval argument RUN rather than recalled: git rev-list --oneline dfae038..af19d53 returns seven commits, of which three - 59cc2ad, 7b182b0 and 3f70eb3 - touch the four feature documents, and those three are the landings of the v1.102/v1.107/v1.51/v1.62 batch whose own Version History entries enumerate their re-runs and name every member of this register under NOT RE-RUN. The other four touch only audit reports and h-mad/. So no member was re-run inside the interval and the stamp moves; NOT argued from byte-identity, which would be false for three of the seven. The register's non-execution enumerations are COLLAPSED rather than extended: bullets that read not re-run in v1.100 or v1.101 grow by one entry per round and were already one round stale, so each now names its last execution and defers non-execution to the lead's predicate, which covers every revision since by construction. WHAT v1.103 DID NOT RE-RUN, named rather than passed over: every docs/-scoped figure v1.101 stamped at b3be433 and every figure v1.102 stamped at 00b961f or dfae038 is left at its stamp and NOT re-measured, those commits being immutable and those readings correct there. Also not re-run: the markdown-it-py 14-case corpus, the five cf3a862 OS/runtime probes, the five 700c599 stdlib probes' own outputs, the doc-auditor.md fence-toggle readings, the Setext differential, the three 74e126f self-counts, the six screen-two legs, the membership of the five triage categories, the pytest collect counts and the suite floor itself, the live hmad-dispatch run --timeout probe, and the whole span between the carve-out sweep table and the ledger, which the teammate leg explicitly marked unverified rather than clean and which this revision did not touch. OWED ELSEWHERE, REPORTED NOT EDITED: nothing to the spec - both items are discharged at af19d53, measured above. To the ORCHESTRATOR: the 00b961f commit message's bracketed correction for ten of the eleven is still owed in a future commit message and cannot be made from inside this document; the r16 decision sheet's FACT 3 publishes 2 plan sites where a markup-admitting needle gives 4, which is the same blind reading my own first sweep took and is reported as a shared grammar defect rather than as a sheet error; the r15 sheet is the origin of the alone claim; and af19d53 itself, which no revision of these documents produced, is what broke the h-mad//handoff closure and moved the suite floor, so a future round changing only h-mad/ still expires figures in here.
