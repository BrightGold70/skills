# Design: doc-block-exec

## Executive Summary

A single stdlib-only module, `h-mad/scripts/h_mad_doc_block_exec.py`, exposing `extract` / `select` / `substitute` / `run_block` / `find_heading` /
`fence_aware_end` / `main` (the seven functions in `__all__`, beside `Block`, `RunResult` and the exception hierarchy — 29 public names), which selects a bash fence by (document, heading, `hmad:exec`
tag, optional ordinal), applies an explicit substitution map, and runs the block via
`subprocess.Popen(start_new_session=True)` in a `mkdtemp` cwd — printing one `DOCBLOCK:` verdict
line and refusing on every condition under which it would measure nothing.

## Overview

The design intent is that **selection is narrow and refusal is cheap**. Every branch that cannot
produce a real measurement returns before `bash` is ever spawned, so a caller can never receive a
plausible-looking zero from a run that did not happen. The two constraints that shape the code are
the opt-in tag (no API accepts a directory, glob, or all-blocks flag) and the ban on external
time-bounders (the bound is `Popen.communicate(timeout=…)` plus `os.killpg`).

One decision worth stating up front: `h-mad/tests/docsections.py` already contains a fence-aware
section bounder (`_fence_aware_end`), and this module **does not import it**. A `scripts/` module
importing from `tests/` inverts the dependency and would break a bare clone that ships without
tests.

**That choice does not come for free, and two drafts got the price wrong before this one.** v1.0
claimed self-containment while omitting any equivalence test — the violation the Single-source
contract names. v1.2 added a differential test, which is **not achievable**: `_fence_aware_end`
toggles on any ```-prefixed line, so on an unbalanced inner quote inside a four-backtick fence it
stops early, while AC-1.6 requires the new scanner not to. Measured on the real helper:

```
balanced   4-backtick : bound reaches the closing ````   (even toggle count masks the bug)
UNBALANCED 4-backtick : bound = '\n````bash\n```bash hmad:exec\n'   <-- cut at an IN-FENCE '## Not a heading'
```

Byte-identical bounds and AC-1.6 cannot both hold, so a differential test would have failed on the
very shape AC-1.6 exists for.

**Resolution: satisfy the invariant's FIRST branch — one authoritative implementation all surfaces
call.** This module owns the bounder; `h-mad/tests/docsections.py` imports it and keeps its
`titled_section`/`section_from` signatures. The dependency that was rejected was `scripts/` →
`tests/`; `tests/` → `scripts/` is the correct direction and was available all along. **The
mechanism is the one every test in `h-mad/tests/` already uses** for `SCRIPT_DIR`: `docsections.py`
does `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))` itself, on the
line before `import h_mad_doc_block_exec as _dbe`, so the import holds when `test_docsections.py`
is collected alone and never depends on a sibling test module having inserted the path first
(the plan names the two tests that pin this); the call is module-qualified,
`_dbe.fence_aware_end(text, start, level)`, so the delegation *wire* can be discriminated by a spy
under an isolated revert of the connection (`docsections.json`'s
`docsections-delegation-reverted` — a private file-path instance of the same module replacing
the shared import, behaviour unchanged — killed by
`test_docsections_delegates_to_the_authoritative_bounder`, whose recording fake sits in
`sys.modules`, which a file-path load never consults). This also
fixes a latent bug in `docsections` rather than duplicating it, and no existing test pins the
early-exit behaviour (verified by grep before proposing the change).

## Architecture Overview

```
caller (test, or operator on the CLI)
        │
        │  (doc_path, heading, index?, subs?, timeout?)
        ▼
   extract()  ──────────►  [Block, …]          PURE SCAN, fence-aware
        │                    .text .shell .lineno .info
        ▼
   select(blocks, index) ─── POLICY: index<1 ──► BAD_INDEX ; 0 ──► NOT_FOUND ; >1 no index ──► AMBIGUOUS
        ▼ exactly one
  substitute()  ─────────►  (Block', counts)   literal replace, count each key; a NEW Block plus
                                               the per-key counts (tuple[Block, dict[str, int]])
        │  every key present?  no ──► SUBST_MISSING
        ▼ yes
   run_block()
        ├── validate timeout: finite, > 0 ──► else BAD_TIMEOUT  (BEFORE mkdtemp: nothing to clean up)
        ├── mkdtemp() + chmod(0o700) ────── cwd   (mkdtemp alone is 0700 & ~umask;
        │                                          chmod fails ──► pending LAUNCH_FAILED stage=mkdtemp,
        │                                          then the SAME finally-cleanup + read-back selection)
        ├── Popen(["bash", *flags, "-c", preamble ⊕ text'], cwd=cwd, start_new_session=True,
        │         text=True, encoding="utf-8", errors="replace")   # cwd=cwd is what makes the
        │                                                            # temp dir the block's cwd
        ├── communicate(timeout) ─── OSError ──► pending LAUNCH_FAILED stage=collect, then the SAME
        │                                        poll()/killpg/drain/close/wait sequence as a timeout
        │                                        (a non-ESRCH killpg error there replaces it with stage=reap)
        ├── communicate(timeout) ─── TimeoutExpired ──► poll() ──► killpg(SIGKILL) [ESRCH = already reaped;
        │                                                 poll() first, else a zombie-only group is EPERM on macOS]
        │                                                 ──► drain communicate(DRAIN_SECONDS)
        │                                                     [expired: close pipes, wait()] ──► TIMEOUT
        │                                                     [OSError from poll()/drain/close/wait ──► stage=collect]
        └── finally: rmtree(cwd) ──► read back: lexists? ──► CLEANUP_FAILED (outranks TIMEOUT)
        ▼
     RunResult(rc, stdout, stderr, shell)
        ▼
   main() ─────────────►  one `DOCBLOCK:` line on stdout;  exit 0 on every verdict (RAN, every
                          refusal, TIMEOUT) | 2 only on UNREADABLE / CLEANUP_FAILED / LAUNCH_FAILED
```

Refusals are ordered so that nothing irreversible happens before the last one: info-string
validation, ordinal validation, timeout validation, preamble readability and stream-path
writability are all checked **before** `bash` is spawned, and no stream artifact is truncated
before a successful run. **Exactly five non-`RAN` outcomes can follow a spawn, in this
precedence:** `CLEANUP_FAILED` (exit 2 — selected after cleanup and read-back have run, so it
outranks everything), then `LAUNCH_FAILED stage=reap` or `stage=collect` (exit 2, one rank — a
timed-out block whose group could not be signalled, or a block whose pipes the helper's own
`communicate`, drain, close or `wait` could not handle; `reap` replaces a pending `collect` when
the kill that follows it fails; it outranks the timeout it implies because an unkillable child is the
more urgent finding), then `UNREADABLE reason=stream_close_failed` (exit 2 — `main`'s backstop
close of a held stream handle failed after the block's outcome was already decided; it is selected
by `main` after its reservation `try`/`finally`, so it can only ever replace the exit-0 `TIMEOUT`
below it — any already-pending exit-2 error wins: the two outcomes above it, an alias refusal, or
a `StreamWriteFailed` raised inside its mapped region, with the close error chained as
`__context__`), then `TIMEOUT` (exit 0 — a measured fact about the block), then
`UNREADABLE reason=stream_write_failed` (exit 2 — only reachable on the path that would otherwise
print `RAN`, because streams are written only after a successful, cleaned-up run). The `mkdtemp`
and `spawn` stages of `LAUNCH_FAILED` are pre-spawn by definition and sit outside this list, and so
are the pre-spawn refusals. None
of the five carries `rc=`, and on the first four nothing is written to any artifact; nothing that ran is reported as a
measurement unless the cwd is gone *and* every promised artifact exists. **The precedence is a
control-flow design, not a hope:** `run_block` never raises from inside the timeout handler. It
records a *pending* outcome — `pending = BlockTimeout(timeout)` after the reap, or the `RunResult`
— runs cleanup in `finally` (which records an `OSError` and never raises), then, after the
`try`/`finally` has completed, reads the cwd back and **selects** the final outcome: `CleanupFailed(cwd,
cleanup_error)` raised `from pending` **if a cleanup `OSError` was recorded OR the directory
persists** — either alone (`__cause__` is the pending `BlockTimeout`/`LaunchFailed` when there is
one, else `cleanup_error`), else the pending outcome re-raised, else the result returned. The
"OR" is the rule: an `rmtree` that removed everything and then raised is still a failure
(`test_cleanup_error_after_successful_removal_is_still_a_failure` injects exactly that), because
"the tree is gone" and "the removal reported success" are different facts and the helper does not
guess which one to believe. A `raise` inside the handler would propagate straight past the
read-back — Python runs `finally` and then continues unwinding — which is exactly the ordering
bug this paragraph replaces. **Two tests drive the combined case, and the one that carries the
guard runs everywhere:** `test_cleanup_failure_outranks_timeout_injected` patches `shutil.rmtree`
to raise `OSError` under a block that is only `sleep 300` (`timeout=1`) and asserts the final
exception is `CleanupFailed`, its `__cause__` is the `BlockTimeout`, its `cleanup_error` is the
injected `OSError`, and the cwd is read back present (the test removes it in `finally`); it needs
no permissions and is the mutation's named killer. `test_cleanup_failure_outranks_timeout` is its
real-fixture sibling (`mkdir keep && chmod 000 keep && sleep 300`, `timeout=1`, `cleanup_error`
the `PermissionError`) and is skipped under `euid == 0` — the precedence guard is therefore never
undiscriminated on a root runner, because the injected test does not skip.

## Detailed Design

### Info-string grammar

An opening fence is `` ```bash `` optionally followed by whitespace-separated tokens:

```
```bash hmad:exec
```bash hmad:exec shell=plain
```

- The bare token `hmad:exec` is the opt-in marker. Its absence means the fence is invisible to
  `extract` — not an error, simply not a candidate.
- `shell=strict` (the default when absent) → `bash -euo pipefail -c`.
- `shell=plain` → `bash -c`, which is how an operator's paste actually runs.
- Any other token, or `shell=` with any other value, is `BAD_INFO` — and so is a **duplicated**
  recognised token (`hmad:exec hmad:exec`, `shell=strict shell=plain`), refused deterministically
  as `BAD_INFO key="<the repeated token>"` rather than resolved first-wins or last-wins, because a
  mode nobody unambiguously chose must not run (`test_duplicate_info_tokens_refuse`, mutation
  `duplicate-info-token-last-wins`) — but **only on a fence that carries `hmad:exec`**. Validation follows opt-in: an untagged fence is not a candidate, so its
  info string is never inspected and an unrelated ` ```bash --frozen ` elsewhere in the tree can
  never make this tool refuse. On a tagged fence it is **not** ignored: a typo'd key that silently
  falls back to a default runs the block under a mode nobody chose.

### Scanning (`extract`)

**One private scanner, two consumers.** The fence grammar below is implemented exactly once, as
a private generator `_fence_events(text)` that walks the document and yields, per line, one of
five kinds — fence `open`, fence `close`, fence `body`, ATX `heading` (with its `level`), or
`prose` — together with the line's `start`/`end` character offsets (so both public consumers return
exact offsets without a second line walk, CRLF included), the opener's marker character, run length,
indentation and info string,
and a scanner-derived `candidate` flag (a backtick opener whose first info word is `bash`), so
no consumer re-recognises a fence or a heading. **The `titled_section` migration was measured as a differential before it was prescribed** — the old
`re.search` heading regex against the new selector over every **tracked** `*.md` under `h-mad/` and
`handoff/`. **The corpus is defined by `git ls-files -- h-mad handoff` filtered to `*.md`
with `archive/` excluded — never by a filesystem glob**, which additionally returns the
gitignored `.pytest_cache/README.md` build output on any tree where pytest has run
(`h-mad/`, `h-mad/scripts/`, `h-mad/tests/`, `handoff/`, `handoff/tests/` — five of them), and
those are not neutral: each carries `# pytest cache directory #` on line 1, the closing-hash
shape at level 1. **The corpus is stated as a command, not as a figure**, because the figure
moves with every doc added to the two roots: measured at `a8e0372` the tracked corpus is
**30** files and the glob is **35**, where at `1861157` they were 25 and 30 — the very number
that once marked the *contaminated* glob is now the *tracked* count, so a reader who checks a
bare "30" against a fresh `git ls-files` gets agreement for the wrong reason.

**Every `a8e0372` figure in this document reproduces unchanged at `74e126f`**, and that is
checked rather than assumed — with the diff **scoped to the two roots the corpus is drawn from**,
which is the whole of why the conclusion holds: `git diff --name-only a8e0372 74e126f -- h-mad
handoff` names exactly two files, both `.py` (`h-mad/scripts/h_mad_assemble_audit.py` and
`h-mad/tests/test_h_mad_assemble_audit.py`), so the `*.md` corpus every measurement here runs
over — including `h-mad/SKILL.md`, which the Task 5 census reads — is byte-identical between the
two shas. **The scoped diff is also empty from `74e126f` to `35698f9`** — `git diff --name-only
74e126f 35698f9 -- h-mad handoff` prints nothing — so every **corpus-derived and scoped-diff**
figure below dated `a8e0372` or `74e126f` is byte-identically derivable at `35698f9` as well, and
those stamps need no churn sweep. The qualifier is load-bearing and no count of the stamps is
given here: a figure measured on *this document's own bytes* is **not** covered by an empty tree
diff, because this document did change. Every document-self figure below therefore carries a
`35698f9` re-run beside its `74e126f` stamp rather than relying on this sentence — the
seam-ordinal check's before/after pair and the line-pin blind-form sweep are the ones that
needed it. **The unscoped form is not the trip-wire and must never be used as one**:
it names a
*pair of integers that moves with every revision of `docs/`*, so a pair written here is stale
before the next commit — **what is stable, and what the argument actually rests on, is the
invariant**

```bash
git diff --name-only a8e0372 <sha> | grep '\.md$' | grep -vc '^docs/'   # expect 0
```

which returns `0` at `335f535`, at `74e126f`, at `35698f9`, at `6f0ee85` and at `cf3a862` alike: every `.md` the unscoped diff
names is under `docs/` — this feature's own spec, plan, design and impl-plan, which lie outside
both roots and enter no corpus measured here. **That zero is load-bearing**, and this is the label
the absence rule below requires: it is a property of where this feature keeps its documents, so it
moves the moment one of them is written outside `docs/`, and every count carrying `a8e0372` rests
on it. **Do not publish the pair.** An unscoped trip-wire
on the pair would fire on every revision of this document and train a reader to ignore it; and a
reader who re-ran a published pair would get a third number again. (Concretely, at `35698f9` the
unscoped diff from `a8e0372` names 25 files and 23 `.md`, where at `74e126f` it named 18 and 16,
at `335f535` 13 and 11, and at `6f0ee85` 31 and 29 — four shas, four pairs, one invariant.
**No fifth pair is added, and that is the point rather than an omission**: the demonstration is
that the pair moves and the invariant does not, which four shas already make, and every later
revision would otherwise append one more stale pair to a paragraph whose own instruction is not to
publish them. The invariant is stamped at each new sha instead, which is the sentence above.)
Re-run **the scoped form**
before trusting any figure below; if *it* ever names an `.md`, every count carrying `a8e0372` must
be re-derived rather than re-read.

**The same closes the `335f535` figures as a class rather than one at a time**: scoped to the two
roots, `git diff --name-only 335f535 74e126f -- h-mad handoff` is **empty**, so every figure this
document dates at `335f535` is also a `74e126f` figure and the five remaining `335f535` dates
below are honest records of when each was run, not stale pins. Three of those five were re-run
anyway as spot checks at `74e126f` and reproduce exactly: the eleven-shape ATX proxy prints the
same eleven renders on `markdown-it-py 2.2.0`, the closing-hash-run oracle still renders
`'## Text\t##'` as `<h2>Text</h2>`, and the `_second_surface` `ast` one-liner still returns eight
enclosing symbols. The two not re-run are the block-census ordinals, which read `h-mad/SKILL.md`
— a file the empty scoped diff proves unchanged.

Re-measured over the 30 tracked files: `old_only=82`, every one a `#` comment line
inside a fence the old fence-blind regex mistook for a heading, and **`new_only=1`** — so the
migration narrows the guard but not to zero, and the Guard-narrowing invariant's "account for
**every** input whose verdict softened" set is non-empty and enumerated below. Control, so the
method is not confounded with the tree: the same script over `git ls-tree -r 1861157` returns
`files=25 old_only=76 new_only=0`, reproducing this document's own earlier figures exactly, so
only the tree moved.

**The softened set is a closed class, not a list of instances, and the class is derived from the
old guard's own pattern rather than from anyone's model of ATX.** The guard being replaced is
`titled_section`'s finder in `h-mad/tests/docsections.py`:

```python
re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$", text)
```

Every token in it either matches CommonMark §4.2 or diverges from it, and enumerating the
tokens enumerates the class — there is nowhere else for a divergence to hide:

| token in the old pattern | shape it mishandles | direction | mechanism | instances (30 tracked, `a8e0372`) |
|---|---|---|---|---|
| `^` (column 0) | `␣␣## x`, 1–3 leading spaces | **softening** | recognition | 0 |
| `#+` (unbounded run) | `####### x`, a 7+ run | **tightening** — the old guard accepted it, the scanner refuses it; a tightening needs no softening account, only this row so the reader does not hunt for it | recognition | 0 |
| the single literal space | `##\tx`, a tab delimiter | **softening** | recognition | 0 |
| the single literal space | a `#` run alone on its line — no delimiter and no title | **softening** | recognition | **1** |
| the single literal space | `##␣␣␣x`, two or more spaces before the title | **softening** — the old pattern put `re.escape(heading)` flush against one space, so the extra spaces never compared equal; CommonMark strips all of them | title comparison | 0 |
| `re.escape(heading)` … `\s*$` | `## x ##`, a closing hash run | **softening** — `\s*$` does not strip a `#` run, so the raw line never equalled the requested title; the scanner strips it first | title comparison | 0 tracked (5 on the 35-file glob, one per `.pytest_cache/README.md`, each its title line) |
| `\s*$` | `## x␣␣`, trailing whitespace | **neither** — `\s*$` already tolerated it, so it is not a divergence at all and is listed to close the question | — | 0 |

So the class is **five softenings** (three at recognition, two at title comparison) plus one
tightening and one non-divergence. The mechanism column is why a reader must not hunt for the
comparison softenings inside `new_only`: only the three recognition shapes can appear there.
The figures above are the *finder*'s — `titled_section`'s unbounded `^#+ ` — and they do not
depend on which of the two old guards is meant: the *bounder*'s narrower `^#{1,6} `
(`_fence_aware_end`, the other old regex this feature replaces) gives the same
`both=292`/`old_only=82`/`new_only=1`. **That equality is a run, not a sentence**: the script
below carries both patterns two characters apart and prints one self-labelled line for each, so
a reader who runs it reaches the stated premise and its twin together rather than only one of
them. **The one live instance** is the bare `#` line in `h-mad/SKILL.md` that
sits alone, outside any fence, in the blank gap immediately above the `## Reading a dispatch
verdict` heading (it closes the section on `exec` bounding itself without `--timeout`),
introduced by `bea1b60`.
It is a real `<h1>`, not a modelling artifact: rendering the whole file through markdown-it-py
2.2.0 under the CommonMark preset emits exactly one **empty** `<h1></h1>`. (The file renders two
`<h1>` elements in all; the other is the document title, `/h-mad — 7-phase H-MAD Orchestrator
(v2.2, standalone)`. The claim is about the empty one, which is the softening.) Consequence, stated because it
is the reason the accounting matters: level 1 is shallower than every `##` section, so after
AC-1.8 `fence_aware_end` ends a section there where today's `docsections._fence_aware_end`
(`re.match(rf"^#{{1,{level}}} ", line)`, space required) does not. This is **not** a live
regression — no current `docsections` consumer bounds a section that spans that line — which is
exactly the point: only the accounting catches it.

Residual, exactly: the rows above are complete **with respect to the old pattern quoted above**,
because they enumerate its tokens rather than sample its behaviour. A further member can arise
in only two ways, and neither is a document drift: the old pattern changes (it is being deleted
by this feature, so it cannot), or CommonMark's ATX rule changes under the pinned oracles
markdown-it-py 2.2.0/4.2.0 — an oracle version bump, re-checked with §Scanning's **eleven-shape
proxy render**, which is the re-derivable command; the original fourteen-case run is not, and
§Scanning says so in those words.
The *counts* in the last column are tree state and move with the tree, which is why each carries
`a8e0372`; re-derive them, do not read them, with:

```bash
# the corpus, and the contaminated glob it must never be (35 vs 30 at a8e0372)
# the `tr -d` is not decoration: BSD `wc -l` right-pads to six columns, GNU `wc -l` does not,
# so without it the block below would be byte-exact on one platform and wrong on the other
git ls-files -- h-mad handoff | grep '\.md$' | grep -v '/archive/' | wc -l | tr -d ' '
find h-mad handoff -name '*.md' -not -path '*/archive/*' | wc -l | tr -d ' '

# the recognition differential and the ATX-shape census, over that corpus
python3 - <<'PY'
import re, subprocess
# both old guards, published side by side and two characters apart, so that the equality
# the prose above asserts is something this script RUNS rather than something it claims
FINDER  = re.compile(r"^#+ ")                     # titled_section's fence-blind heading finder
BOUNDER = re.compile(r"^#{1,6} ")                 # _fence_aware_end's bounder
NEW = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]|$)")   # CommonMark ATX
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
TITLELESS = re.compile(r"^ {0,3}#{1,6}[ \t]*$")

def inside(lines):                                # True while within a fenced block
    open_ = None
    for line in lines:
        m = FENCE.match(line)
        if open_ is None:
            if m and (m.group(1)[0] != "`" or "`" not in m.group(2)):
                open_ = (m.group(1)[0], len(m.group(1)))
                yield True
                continue
            yield False
        else:
            ch, n = open_
            if m and m.group(1)[0] == ch and len(m.group(1)) >= n and not m.group(2).strip():
                open_ = None
            yield True

paths = [p for p in subprocess.run(["git", "ls-files", "--", "h-mad", "handoff"],
         capture_output=True, text=True).stdout.split()
         if p.endswith(".md") and "/archive/" not in p]
for label, OLD in (("finder  ^#+", FINDER), ("bounder ^#{1,6}", BOUNDER)):
    both = old_only = new_only = 0
    ids = []
    for path in paths:
        lines = open(path, encoding="utf-8").read().split("\n")
        fenced = list(inside(lines))
        for i, line in enumerate(lines, 1):
            o, n = bool(OLD.match(line)), bool(NEW.match(line)) and not fenced[i - 1]
            both += o and n
            old_only += o and not n
            new_only += n and not o
            if n and not o:
                ids.append((path, TITLELESS.match(line) is not None))
    print(label, "files", len(paths), "both", both,
          "old_only", old_only, "new_only", new_only)
    print("   new_only identities (path, is_titleless):", ids)
PY
```

At `74e126f`, and again when extracted from the shipped file and re-run at `35698f9`, the whole
fence prints exactly this — the two `git ls-files`/`find` counts, then
one labelled differential line per old guard, each followed by its `new_only` identities:

```
30
35
finder  ^#+ files 30 both 292 old_only 82 new_only 1
   new_only identities (path, is_titleless): [('h-mad/SKILL.md', True)]
bounder ^#{1,6} files 30 both 292 old_only 82 new_only 1
   new_only identities (path, is_titleless): [('h-mad/SKILL.md', True)]
```

The two differential lines agree in every field, which is the equality the paragraph above
states — read off a run, not asserted.

Every count in this document over "the `*.md` files of `h-mad/` and `handoff/`" is this tracked
corpus, so a clean clone reproduces it. **Every grammar rule the scanner implements was
rendered through markdown-it-py — both the interpreter-local 2.2.0 and the 4.2.0 the spec's
tagged-fence probe used, CommonMark preset on each — before it was written down; 14 of 14 agreed
on both versions, and the transcript is in the plan's §Measurements ("Scanner grammar corpus").
That fourteen-case run is NOT re-derivable by a later reader, and this document says so plainly
rather than leaving the citation to imply otherwise**: the corpus script `grammar_corpus.py` was
a throwaway and is not in the tree (`git ls-files | grep -c grammar_corpus` → `0` at `cf3a862`;
**vacuous** — the artifact does not exist, so the zero records only that the search ran, which is
exactly why the citation is replaced below by a command a reader can execute), and 4.2.0 is
not installed on any interpreter here (`for P in python3 python3.11 python3.12 python3.13; do $P
-c 'import markdown_it; print(markdown_it.__version__)' 2>/dev/null; done` prints one line,
`2.2.0`). **The cheap proxy is the command below, and it is what a later reader should run** — it
renders the eleven ATX shapes this document's own grammar names against the interpreter-local
oracle:

```bash
python3.11 -c 'import markdown_it, re
from markdown_it import MarkdownIt
md = MarkdownIt("commonmark")
print("markdown-it-py", markdown_it.__version__)
for s in ["## x", "  ## x", "    ## x", "#hashtag", "####### x",
          "##\tx", "##", "## x ##", "## x\t##", "##   x", "## x  "]:
    print(repr(s), "->", re.sub(r"\n$", "", md.render(s + "\n")))'
```

At `335f535` it prints a version line (`markdown-it-py 2.2.0`) and then one line per shape, the
indented-code case being the one that wraps onto a second: `## x`, `␣␣## x`, `##\tx`,
`## x ##`, `## x\t##`, `##␣␣␣x` and `## x␣␣` each render `<h2>x</h2>`; `##` alone renders
`<h2></h2>`; `␣␣␣␣## x` renders a `<pre><code>` block and `#hashtag` and `####### x` render
paragraphs — which is exactly the ATX rule stated here and restated in §Detailed Design.
**Residual, exactly**: the proxy covers the ATX *heading* production and nothing else. The fence
grammar (info strings, tilde fences, a longer enclosing fence) and the Setext census are outside
it; each of those carries a named mutation row in the Test Plan instead of an oracle render, and
no oracle-render evidence for them survives in this repository. A reader who needs the 4.2.0 half
back must install that version — this document does not claim a cheap substitute for it.
`extract` consumes it to find candidates and
`fence_aware_end` consumes it to bound a section — feeding the scanner **complete source lines
from the top of the document through the line that contains `start`**, then considering a
boundary at every line whose start offset is **≥ `start`** — a line that began before a
mid-line `start` is excluded, and the line beginning exactly at `start` is included, which is the
line adjacent to a heading `find_heading` returned (`test_adjacent_heading_bounds_the_section`: a
heading immediately followed by a same-level heading that owns a tagged block yields no candidate
for the first, and the bounder returns `start` itself; mutation `adjacent-heading-skipped`, the
predicate `>` instead of `≥`, which would hand the next section's block to the wrong address);
never a `text[:start]` slice, which can cut a
line right after its marker run and make a ```` ```trailing ```` body line look like a blank-tailed
closer (hostile fixture: `start` placed immediately after the three backticks of that line inside
an open fence; the next fenced `#` must still not end the section) — and neither function carries
fence state of its own. That is what
makes the two surfaces unable to disagree by construction — a change to marker kind, run length,
indentation, the closer rule or prefix state lands in one place — and it is where every
fence-grammar mutation row anchors (`fence-run-length-ignored`, `tilde-fence-not-tracked`,
`indented-opener-accepted`, `indented-closer-accepted`, `closer-trailing-text-accepted`, `prefix-fence-state-skipped`), so
each mutant is observed by both consumers' tests. The parity guard is observable at the scanner, not through the two public APIs (which expose
only tagged candidates and one boundary offset): `test_fence_events_trace_on_every_hostile_fixture`
runs every hostile fixture (balanced and unbalanced four-backtick, tilde-quoted backtick,
backtick-in-info, indented literal, trailing-text closer, offset-inside-a-fence) through
`_fence_events` and asserts the exact event trace — which lines open, which close, which are body —
and two per-consumer tests then assert `extract`'s candidates and `fence_aware_end`'s boundary on
the same fixtures; a second scanner could not pass the trace test by accident, and the mutation
`scanner-duplicated-in-consumer` (a private fence toggle re-introduced inside `extract`) is killed
by `test_extract_has_no_fence_state_of_its_own`, a source assertion that only `_fence_events`
mentions the marker runs. The scanner carries
`in_fence`, **the opening fence's marker character (backtick or tilde) and its run length**. CommonMark fences come in both flavours, `~~~` closes only a `~~~`
fence, and a tilde fence can quote a backtick fence verbatim — measured through GitHub's renderer
in the spec's Assumptions: a `~~~` block containing ` ```bash hmad:exec ` renders as a plain code
block. Tilde fences are tracked for bounding only; a **candidate** is always a backtick fence whose
first info-string word is `bash`. A
naive "any line starting with ``` toggles" is wrong and would corrupt the state on a document this
feature must handle: CommonMark opens a fence with a run of *N* ≥ 3 backticks and closes it only
with a run of ≥ *N*, so a fence opened with four backticks legitimately contains ``` lines as
body text. This design's own documents contain exactly that shape, because they quote fenced
examples. So:

- a **backtick** opener whose info string contains a backtick is not a fence at all (CommonMark
  §4.5: "the info string of a backtick fence may not contain backticks"), so ```` ```bash hmad:exec `x` ````
  is inert prose — neither a candidate nor a `BAD_INFO` — and the next ``` line opens a fence
  rather than closing one; tilde fences carry no such rule. Measured on both renderers used for
  AC-1.6 (markdown-it-py: `<p>```bash hmad:exec <code>x</code>…`; GitHub `POST /markdown`: the same
  paragraph, with the following line opening a fence that swallowed a tilde block after it);
- an opener is recognised only when its marker run is preceded by **0–3 spaces** (CommonMark
  §4.5): four or more spaces make the line an indented code block, so a literal
  `    ```bash hmad:exec` is never an opener and never a candidate — the security boundary AC-1.6
  states, restated for indentation; the same 0–3 rule applies to a closer — a marker run preceded by
  four or more spaces inside a fence is body text, never the closer (`test_indented_closer_does_not_close`:
  a ```` ```` ```` line at four spaces inside a bash fence stays in the body and the fence ends at the
  next 0–3-space closer; mutation `indented-closer-accepted`) — and **`extract`
  normalises the body**: up to the opener's indentation is stripped from each body line (a line
  indented less than the opener loses only what it has), so the `Block.text` returned is the
  CommonMark content of the fence, not its source bytes — recognising the fence but returning
  un-normalised text is its own defect, with its own test and mutation (`body-indent-not-stripped`);
- an opening fence records its marker character and `n = len(run)`; while open, only a line
  whose leading run is of the **same character** and ≥ `n` **and** is followed by nothing but
  spaces or tabs (CommonMark: a closing fence carries no info string and no other text) closes
  it;
- while `in_fence` is true, no line is examined as a heading or as an opener.

That is what makes AC-1.6 structural rather than a special case: a body quoting
` ```bash hmad:exec ` is inside a fence and is never read as an opener, and a *longer* enclosing
fence keeps it that way.

Heading bounding: locate the heading event whose **normalized text** matches `heading` — a
heading event's text is the line after its opening hash run with the optional closing hash run
(preceded by **a space or a tab**, per CommonMark §4.2 — the rule over the axis is that *every*
`#`-run delimiter in ATX takes spaces-or-tabs, which is the same axis
`request-predicate-space-only` closes on the *opening* delimiter, and the closing run was the
one member left at space-only; oracle: on markdown-it-py 2.2.0, CommonMark preset,
`'## Text\t##\n'` renders `<h2>Text</h2>`) and trailing whitespace stripped, so `## Text ##` and
`## Text` are one and the same heading, and a document holding both has two of it — **among the
scanner's `heading` events** — a line inside any fence is never a
heading event, and this lookup is the public `find_heading(text, heading) -> tuple[int, int] | None`
(the offset just past the heading line and its level; `None` when absent; `AmbiguousHeading` on
more than one) that `extract` and `docsections.titled_section` both call. **`heading` has two
accepted forms, and each real caller uses one**: the full line form `## Text` (what `extract` and
the CLI's `--heading` pass) matches a heading event whose text after the hash run — closing hashes
stripped — equals `Text` **and** whose level equals the hash count; the bare form `Text` (what
`docsections.titled_section` passes today) matches on text at any level. **The two forms are told
apart by the request itself, full form first** (impl-plan audit v26): a request that parses as an
ATX heading line — 0–3 spaces, 1–6 `#`, then a space, a tab or end of line: **the scanner's own
ATX predicate, reused, so the dispatch cannot drift from the recognition** (impl-plan audit v27:
a space-only request predicate would leave `##\tText` and a title-less `##` selectable by the
scanner but unreachable by any request) — IS the full form, always; only a request that
does not parse as one is the bare form. So a heading whose visible title itself begins with an
ATX prefix (`### ## Text`, title `## Text`) is reachable only through its full form
(`### ## Text` → level 3, title `## Text`) and never through the bare form — the one documented
exclusion, harmless to every live caller (measured: none of `titled_section`'s targets begins
with `#`). `test_heading_form_precedence_full_wins` pins it on a document holding both
`### ## Text` and `## Text`: `find_heading(text, "## Text")` returns the level-2 `Text` heading
only, `find_heading(text, "### ## Text")` the level-3 one only, and neither raises
`AmbiguousHeading`; mutation `form-precedence-bare-first` (the bare form is tried first, or the
two matches are unioned, so the request `## Text` finds two headings and refuses) is killed by
it; `test_full_form_request_accepts_tab_and_eol` pins the shared predicate — a `##\tText` heading
requested as `##\tText` and a title-less `##` requested as `##` are both found in full form —
and mutation `request-predicate-space-only` (the request side narrowed to a space, so those two
requests fall to the bare form and miss) is killed by it — with one deliberate
tightening over the `re.search` it replaces, which took the FIRST of several same-text headings:
the bare form refuses duplicates at any level with `AmbiguousHeading(n)` exactly as the full form
does (`test_bare_form_duplicate_headings_refuse`; the same guard `duplicate-heading-takes-first`
mutates), because a first-match pick on a duplicated heading is the silent wrong-section defect
this module exists to remove. No live caller acquires the refusal — measured 2026-09-03: both
`titled_section` targets in `h-mad/SKILL.md` (`Phase 5 (Implementation) sub-steps`,
`Helper scripts (…)`) occur once, and `h-mad/SKILL.md` has 0 duplicated bare heading texts.
`test_find_heading_accepts_full_and_bare_forms` pins both and that the full form refuses a
level mismatch; mutation `heading-level-pin-ignored` (the full form matching any level).
`test_closing_hash_run_does_not_change_heading_identity` pins the identity rule from both sides:
on a document whose only heading is `## Text ##`, `find_heading(text, "## Text")` and the bare
form both find it, and on a document holding `## Text` and `## Text ##` the full form raises
`AmbiguousHeading(2)`; **its fixture carries the tab-preceded form `## Text\t##` beside the
space-preceded one**, since the delimiter is spaces-or-tabs on both runs and a space-only strip
would leave the tab form unequal to `## Text`; mutation `closing-hash-run-kept` (the scanner
leaves the closing run in the heading text, so `## Text ##` no longer satisfies `## Text` and the
pair counts one) is killed by it (design audit v63). Residual, measured at `a8e0372`: **0**
tab-preceded closing runs in the tracked corpus, so no live document or fixture outside this test
depends on it — shipping it space-only would be a silent divergence between `_fence_events` and
the renderer §Scanning's proxy render agrees with, not a current defect, which is why the
fixture rather than a corpus instance is what pins it. **Residual on the widening, stated
exactly**: CommonMark's ATX production has exactly two `#`-run delimiters — the one after the
opening run and the one before the optional closing run — and both are now spaces-or-tabs here,
so the axis has no third member and none can be added without a change to the ATX production
itself. What the widening does *not* pin: it is asserted against markdown-it-py 2.2.0 under the
CommonMark preset (`'## Text\t##\n'` → `<h2>Text</h2>`, re-run at `335f535`), so an oracle bump
is the one way it can move; and it says nothing about tab handling in the fence info-string
production, which is a separate grammar and carries its own rows. The tab-preceded fixture is
routed to the impl-plan author in this same round together with that document's two prose
statements of the delimiter — this design does not assert what that document currently holds,
only that the three sites are the routing target. So the section START is
found by one implementation exactly as its END is — so a fenced example that quotes `## <the requested heading>` cannot become the
section start and hand a later real tagged block to the wrong address
(`test_requested_heading_quoted_inside_a_fence_is_not_a_section_start`: the requested heading
appears first inside a ```` ```markdown ```` fence, then for real; the only candidate is the block
under the real heading; mutation `heading-match-ignores-fence-state`); its level is the count of
leading `#`. **A heading line is recognised by the CommonMark ATX rule (§4.2) and nothing looser**: 0–3 leading spaces, a run of 1–6 `#`, then a space, a tab or end of line, with an optional closing `#` run (preceded by a space **or a tab** — both delimiters take spaces-or-tabs, see §Scanning's heading-bounding rule) stripped before the text is compared — so `#hashtag`, a seven-`#` run, and a four-space-indented `## x` are prose, and the level is the run length of the opening hashes (`test_heading_lookalikes_are_not_headings`: each lookalike placed where it would end or start the section changes nothing; mutation `heading-lookalike-accepted`, the grammar loosened to `line.lstrip().startswith("#")`). **If more than one line matches, `extract`
raises `AmbiguousHeading(n)` rather than taking the first** — duplicate headings are real in this
tree (`h-mad/invariants.example.md` has two of them), and picking one would execute a tagged block
from the wrong section. The opt-in tag guards *which block*; it cannot guard *which section*. **This is ATX-only by design and by
limitation**: a Setext heading (text underlined with `===`/`---`) is not recognised, so a document
using them would bound wrongly rather than loudly. Every document in the migration corpus is ATX,
measured directly — the census is published as a runnable command in the block immediately after
this paragraph rather than cited, and the heading-selector differential cannot show it either
way, since both of that differential's selectors ignore Setext. After AC-1.8 `docsections.py`
calls this same bounder, so the assumption has exactly one home
and cannot drift between two implementations (the differential test an earlier draft named here
is the one this document explains is not achievable). The section ends at the next line that is a
heading of the **same or shallower** level *and* is not inside a fence. Candidates are the tagged
opening fences between those two offsets.

**The Setext census is published here as a runnable command, not cited.** The plan's
§Measurements pins its transcript at `1861157` (`files=25`/`30`), so that locator does not contain
a run at this tree; and the script it names is not in the tree either —
`git ls-files | grep -cE 'heading_differential|grammar_corpus'` returns `0` at `cf3a862`
(**vacuous** — neither script was ever committed, so nothing was screened and the zero is worth
only the statement that the search ran) — so neither the cited
run nor a re-run of it is re-derivable by a reader. That is the same condition that made the
"14 of 14" grammar-oracle premise not re-derivable, and it takes the same treatment. Fence-aware,
CommonMark §4.3 (a `===`/`---` underline immediately after a paragraph line), YAML front matter
skipped, and list, table, blockquote and indented-code lines excluded as underline bases, over
both the tracked corpus and the contaminated glob:

```bash
python3 - <<'PY'
import re, subprocess
def files(cmd):
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.split()
    return [p for p in out if p.endswith('.md') and '/archive/' not in p]
UND   = re.compile(r'^ {0,3}(=+|-+)[ \t]*$')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')
SKIP  = re.compile(r'^(    | {0,3}([-*+]|[0-9]+[.)])\s| {0,3}>| {0,3}\|| {0,3}#)')
def census(paths):
    n = 0
    for p in paths:
        lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
        i = 0
        if lines and lines[0].strip() == '---':          # YAML front matter
            j = 1
            while j < len(lines) and lines[j].strip() != '---': j += 1
            i = j + 1 if j < len(lines) else 1
        fence = None; prev = ''
        for ln in lines[i:]:
            m = FENCE.match(ln)
            if fence is None:
                if m:
                    fence = m.group(1); prev = ''; continue   # keep the RUN, not just the char
            else:
                # CommonMark §4.5: a closer must be at least as long as its opener,
                # so a ``` line inside a ```` fence does NOT close it.
                if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                    fence = None
                prev = ''; continue
            if UND.match(ln) and prev.strip() and not SKIP.match(prev): n += 1
            prev = ln
    return n
tracked = files("git ls-files -- h-mad handoff")
glob    = files("find h-mad handoff -name '*.md' -not -path '*/archive/*'")
print('tracked files', len(tracked), 'setext_headings', census(tracked))
print('glob    files', len(glob), 'setext_headings', census(glob))
PY
```

At `74e126f` and again at `35698f9` that fence prints exactly:

```
tracked files 30 setext_headings 0
glob    files 35 setext_headings 0
```

**Both controls were run before the count was published**, and both against the `census()` above
rather than a paraphrase of it: over a fixture holding one `===` heading and one `---` heading it
returns `2` (positive); over a fixture holding a thematic break, an underline inside a fence, an
underline under a list item and a table delimiter row it returns `0` (true negative — non-members
the screen declines, not members it fails to print). The null above is therefore discriminating
rather than a scan that finds nothing. **It was `0` at `1861157` too, over the 25 files tracked
then — and that sentence is itself an absence claim about a corpus, so it now carries a label,
which it did not until this revision.** Its zero decomposes exactly as the current one does,
measured rather than assumed: the differential harness below, extracted from this file and run in
a scratch clone checked out at `1861157`, prints `tracked files 25 headings shipped 0 arm1 0 arm2
0 | reached: arm1 0 lines, arm2 8 marker lines / 4 fences / 2 files, whose 9 body lines are
scanned as prose, 0 of them below 4 columns` — so arm (1) is *vacuous* and arm (2) *incidental*
there, the same pair the 30-file corpus gets below. It is an absence site the rule below counts,
and it was missed for the same reason the two census arms were: it sits inside that rule's own
needle and reads as a parenthetical about an older run rather than as prose making a claim.

**A third control, added at v1.97 because the second one was a sound true negative but did not
cover the shape AC-1.6 exists for**: a four-backtick fence containing a three-backtick line,
followed by a paragraph line and
an `===` underline. The earlier tracker closed the fence on the *marker character* alone and so
scanned the rest of the file as prose — that fixture returned `1` where CommonMark says `0`. The
run-length condition in the fence branch above is the fix, and with it the fixture returns `0`
while the positive control still returns `2` and both corpus lines are unchanged. The direction
of the old bug was safe (it could invent a Setext heading, never hide one), so no figure moved;
what is recorded here is that the census now has a control for the shape AC-1.6 exists for.
**Residual on `census()` itself, two arms, both stated**: (1) it does not model an *info string*,
so a line opening a new fence with an info string while a fence of the same character and no
greater run is already open is read as that fence's closer, where CommonMark reads it as content.
The direction is the same safe one as the bug just fixed — it can end a fence early and scan code
as prose, never hide a heading. (2) It matches a fence only at 0–3 columns of indent, so a fence
*opened inside a list item* is not recognised as a fence at all and its contents are scanned as
prose — a document that indents fences will need arm (2) built.

**An absence claim is a measurement, and each arm is measured separately.** v1.97 wrote *"the
corpus has none of either"* for both arms in one sentence. It was reasoned rather than run, and it
is **false for arm (2)**. Each arm is now screened by a *differential* — the shipped `census()`
beside a variant with that one arm repaired — and each differential carries a **positive control
that moves it**, because a `0`-versus-`0` over a shape the corpus never contains proves nothing. A
third column reports how often each arm is **reached at all**, which is what separates a `0` that
means "the screen looked and the shape is harmless here" from a `0` that means "the screen never
looked":

```bash
python3.11 - <<'PY'
import re, subprocess, tempfile, os
UND     = re.compile(r'^ {0,3}(=+|-+)[ \t]*$')          # UND, SKIP, body() as in the census above
SKIP    = re.compile(r'^(    | {0,3}([-*+]|[0-9]+[.)])\s| {0,3}>| {0,3}\|| {0,3}#)')
SHIPPED = re.compile(r'^ {0,3}(`{3,}|~{3,})')           # the shipped FENCE, verbatim
ANYIND  = re.compile(r'^ *(`{3,}|~{3,})')               # arm 2 repaired: any indent may open
def body(p):
    ls = open(p, encoding='utf-8', errors='replace').read().split('\n')
    i = 0
    if ls and ls[0].strip() == '---':
        j = 1
        while j < len(ls) and ls[j].strip() != '---': j += 1
        i = j + 1 if j < len(ls) else 1
    return ls[i:]
def census(paths, FENCE=SHIPPED, info=False):           # info=True repairs arm 1
    n = 0
    for p in paths:
        fence = None; prev = ''
        for ln in body(p):
            m = FENCE.match(ln)
            if fence is None:
                if m: fence = m.group(1); prev = ''; continue
            else:
                shut = bool(m) and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence)
                if shut and info: shut = not ln[m.end():].strip()   # a closer has no info string
                if shut: fence = None
                prev = ''; continue
            if UND.match(ln) and prev.strip() and not SKIP.match(prev): n += 1
            prev = ln
    return n
def reached(paths):      # a 0-vs-0 differential over a shape that never occurs proves nothing
    a1 = a2 = shallow = fences = bodies = 0; where = set()
    for p in paths:
        fence = deep = None
        for ln in body(p):
            m, d = SHIPPED.match(ln), ANYIND.match(ln)
            if d and not m: a2 += 1; where.add(p)
            if deep is None:
                if d and not m: deep = d.group(1); fences += 1
            elif d and d.group(1)[0] == deep[0] and len(d.group(1)) >= len(deep): deep = None
            elif ln.strip():
                bodies += 1
                if len(ln) - len(ln.lstrip(' ')) < 4: shallow += 1
            if fence is None:
                if m: fence = m.group(1)
            elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                if ln[m.end():].strip(): a1 += 1
                fence = None
    return a1, a2, fences, len(where), bodies, shallow
def files(cmd):
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.split()
    return [q for q in out if q.endswith('.md') and '/archive/' not in q]
B = '`' * 3                                             # positive controls, each must MOVE
d  = tempfile.mkdtemp()
c1 = os.path.join(d, 'c1.md'); open(c1, 'w').write(f'{B}\n{B}bash\nParagraph\n===\n{B}\n')
c2 = os.path.join(d, 'c2.md'); open(c2, 'w').write(f'- i\n\n    {B}\n    t\nParagraph\n---\n    {B}\n')
print('control arm1 shipped', census([c1]), 'repaired', census([c1], info=True))
print('control arm2 shipped', census([c2]), 'repaired', census([c2], ANYIND))
for lb, ps in (('tracked', files("git ls-files -- h-mad handoff")),
               ('glob   ', files("find h-mad handoff -name '*.md' -not -path '*/archive/*'"))):
    a1, a2, nfen, nf, bodies, shallow = reached(ps)
    print(f'{lb} files {len(ps)} headings shipped {census(ps)} arm1 {census(ps, info=True)}'
          f' arm2 {census(ps, ANYIND)} | reached: arm1 {a1} lines, arm2 {a2} marker lines /'
          f' {nfen} fences / {nf} files, whose {bodies} body lines are scanned as prose,'
          f' {shallow} of them below 4 columns')
PY
```

Run from the repository root at `6f0ee85` on python 3.11.8 / darwin 25.6.0 it prints:

```
control arm1 shipped 1 repaired 0
control arm2 shipped 1 repaired 0
tracked files 30 headings shipped 0 arm1 0 arm2 0 | reached: arm1 0 lines, arm2 8 marker lines / 4 fences / 2 files, whose 9 body lines are scanned as prose, 0 of them below 4 columns
glob    files 35 headings shipped 0 arm1 0 arm2 0 | reached: arm1 0 lines, arm2 8 marker lines / 4 fences / 2 files, whose 9 body lines are scanned as prose, 0 of them below 4 columns
```

The `headings shipped 0` column reproduces the census's own published `0` on both corpora, which
is the check that this harness is running the same screen and not a paraphrase of it.

**Both fence characters are controlled, not only the one the corpus happens to use.** `B` above is
three backticks; re-running the same two controls with `B = '~' * 3` prints the identical
`control arm1 shipped 1 repaired 0` and `control arm2 shipped 1 repaired 0`. **That run reaches
`SHIPPED` and `ANYIND` and stops there** — they are this harness's only two fence regexes — so it
is evidence about those two and about nothing else. v1.100's sentence named `$STRIP` as well,
which is a separate `awk` in the seam-ordinal pipeline in §Test Strategy carrying the same
alternation and reached by no part of this harness; that is decision O one level up, a control
over two members of a set standing in for the member it never touched. `$STRIP`'s tilde alternative is controlled
where `$STRIP` is defined, because a control belongs beside the code it moves. What this run does
establish is that `SHIPPED` and `ANYIND` both handle a tilde fence, which the corpus never asks
them to do: the tracked corpus contains **0** lines matching `^ {0,3}~{3,}` — `git ls-files --
h-mad handoff | grep '\.md$' | grep -v '/archive/' | xargs grep -chE '^ {0,3}~{3,}'` sums to `0`
over the same 30 files at `68a70d6` — so without these two arms the `~{3,}` branch would be one
no control and no corpus had ever moved, with the healthy backtick branch standing in for it. That
corpus `0` is itself an absence claim and is *vacuous*: the shape does not occur, so nothing was
exercised. It is one of the absence claims v1.101 and v1.100 add on top of the nine the
rule below stamps at `cf3a862`, each labelled where it is stated, and part of why the working-file
candidate count is the larger number that paragraph declines to freeze.

**The two zeros are zero for different reasons, and only one of them is load-bearing.** Arm (1) is
reached **0 lines**: nothing in either corpus is a same-character, long-enough would-be closer
carrying an info string, so its `0` is *vacuous* — correct today and worth nothing the moment a
document grows the shape. Arm (2) **is** reached — **8 marker lines forming 4 fences in 2 files**
(`h-mad/SKILL.md` and `handoff/SKILL.md`, every one of them a fence opened inside a list item,
verified by reading the surrounding context of both rather than inferred from the indent) — and
`census()` really does scan their **9** body lines as prose. No false heading falls out only
because **0** of those 9 sits below 4 columns, so `UND`'s `{0,3}` declines every candidate
underline and `SKIP`'s `^    ` declines the line before it. **That is a property of the corpus
bytes, not of `census()`**: incidental, not by construction. The arm-(2) control is the proof —
the same list-item fence with one column-0 line inside it turns the shipped `0` into `1`. The
two-heading positive control above cannot see this; it is a positive for the *finder*, not for
either arm.

**The rule over the absence axis**: every absence sentence in this document — *"the corpus has none"*,
*"no corpus instance"*, *"zero hits"*, *"exercises it zero times"* — carries the runnable command,
the sha it was run at, and **the reason the zero is zero, marked with one of three labels**. A
zero that is right by accident is a defect that has not fired yet. **The three labels, named here
because the rule was stated with two and applied with three, which is how a vocabulary drifts**:
*load-bearing*, the zero is a property of the mechanism under test and moves when the mechanism
does; *incidental*, the zero is a property of the corpus bytes and the mechanism would not decline
the shape if it appeared; *vacuous*, the shape does not occur at all, so nothing was exercised and
the zero is worth only the statement that the search ran. **The rule's scope, stated so the next
sweep is bounded**: it governs a claim that a shape is *absent from a corpus* — the tree, a named
set of files, or this document — and it does **not** govern a screen's expected output on this
document, which is the state the screen exists to assert rather than a finding about a corpus, and
which is labelled as such where each screen is defined. The distinction has to be drawn by reading.
The candidate sweep is ``grep -cE '[`]0[`]|expect[ ]0'`` over the head — **written in bracketed form
precisely so that this sentence is not one of its own hits**, the same publication rule the carry
screen states below. **Its value is stamped at `cf3a862`, the blob before this paragraph existed,
and is deliberately not restated for the working file**: this revision writes the labels into
several of the candidate lines, so a working-file value would be a number this paragraph moved by
being written. At `cf3a862` it raises **36** candidate lines, of which **nine** sites are absence
claims, each labelled where it is stated: the `.md`-under-`docs/` invariant (*load-bearing*); the
two untracked-script measurements (`grep -c grammar_corpus` and
`grep -cE 'heading_differential|grammar_corpus'`, both *vacuous*); the `grep -c parametrize` pair
under the floor tuple (*incidental*, at both sites that state the figure); **the arm-(1) zero and
the arm-(2) zero of the census above** (*vacuous* and *incidental* respectively); the `^ {4,}`
fence bound stated at `$STRIP` below (*vacuous*); **the `1861157` restatement in the census's
own paragraph** (*vacuous* and *incidental*, its two arms measured at that sha in v1.101); and
**the `35698f9` provenance probe at the fourth-blind-form fence** (*vacuous*, labelled there by
this revision).
**v1.99 published this denominator as four, v1.100 as seven and v1.101 as eight, and every site
all three of them dropped sits on a candidate line this sweep itself raises** — the miss was
*inside the needle* three times running, never at its margin, which is why that half of the
residual below is stated as a category and not as an example.
**The rule over that axis, and it is the one thing that closes it: the denominator is *walked*,
never recalled.** Every raised line is carried to a named disposition and the check is that **no
raised line is left over** — a site list assembled by remembering which zeros are claims is how
four, seven and eight were each published as final, and each time the dropped site was a line the
needle had already put in front of the author. Walked here over all **36** lines raised at
`cf3a862`, and published as a partition whose parts sum to the raised count rather than as an
assertion that nothing was left over: **12 + 16 + 8 = 36**. **The partition is published as a
runnable assignment and not as three addends**, because a total whose addends nobody can re-take
is the same object as the site list it replaced — and that is not a hypothetical: the partition
v1.102 published here **carried one line too many in its first part and one too few in its
second**, and its first part was *recalled off the site list* ("four of them state their figure on
two lines each") rather than counted off the raised lines, which is this very rule failing one
level up on its own repair. Three sites state their figure on two lines each, not four. **The
superseded triple is described and not reproduced**, per the rule v1.98 settled: a wrong figure
quoted at a *body* site in order to report it is a wrong figure back in the body. **The
distinction that rule turns on, stated here so a reader meeting both sites need not derive it: it
is not whether the sentence around the figure is a correction — it is whether the figure is
written in a form a reader can lift and read as current.** A superseded triple written in the
same `a + b + c` shape as the live one, three sentences from it, is exactly that; the dated record
in §Version History is not, because an entry is a record of what a revision claimed. Both of the
triples given below are live readings of the same walk, not superseded values. The assignment is carried by an alternation of **anchor strings** — a fragment of each
raised line's own text — so that no line number is written and a reader re-takes the walk instead
of trusting it:

```bash
D=docs/02-design/features/doc-block-exec.design.md
RAISE='[`]0[`]|expect[ ]0'                    # the candidate sweep, in the same bracketed form
SITE='grep -vc|335f535|grep -c grammar_corpus|heading_differential|1861157. too|is .vacuous.|turns the shipped|grep -cF "tr|6f0ee85. and|the shape is absent|grep -c parametrize'
NOCLAIM='index - 1|not an ordinal at all|0.-versus-|separates a|the screen looked|screen that has never|is weaker than|shell-timeout'
R=$(git show cf3a862:"$D" | grep -E "$RAISE")
printf 'raised  %s\n' "$(printf '%s\n' "$R" | grep -c '')"
printf 'sites   %s\n' "$(printf '%s\n' "$R" | grep -cE "$SITE")"
printf 'noclaim %s\n' "$(printf '%s\n' "$R" | grep -cE "$NOCLAIM")"
printf 'both    %s\n' "$(printf '%s\n' "$R" | grep -E "$SITE" | grep -cE "$NOCLAIM")"
printf 'neither %s\n' "$(printf '%s\n' "$R" | grep -vE "$SITE" | grep -vcE "$NOCLAIM")"
printf '%s\n' "$SITE" | tr '|' '\n' | while read -r b; do    # one anchor, one raised line
  printf '%s=%s ' "$b" "$(printf '%s\n' "$R" | grep -cE -e "$b")"; done; echo
printf '%s\n' "$NOCLAIM" | tr '|' '\n' | while read -r b; do
  printf '%s=%s ' "$b" "$(printf '%s\n' "$R" | grep -cE -e "$b")"; done; echo
```

It prints `raised 36`, `sites 12`, `noclaim 8`, `both 0`, `neither 16` — **disjoint** because
`both` is `0`, **exhaustive** because `neither` plus the two parts is the raised count, and the
`16` is derived as the remainder rather than asserted. Every `SITE` anchor selects exactly one
raised line except `grep -c parametrize`, which selects the pair of lines that state that figure,
and every `NOCLAIM` anchor selects exactly one; the branch loop prints that, so a hand-built
alternation that silently over-matched two lines with one anchor would show up as a branch
reading `2` where the walk claims one. The three sites carrying two raised lines are the ones
whose anchors come in pairs above: the `.md`-under-`docs/` invariant, the `^ {4,}` fence bound,
and the `grep -c parametrize` pair. The **16** are a fence's or a fixture's own printed output on
this document together with the prose disposing of it. The **8** are zeros making no claim about a
corpus at all: **two** are the `index` contract's ordinal and the sentence denying that `0` is an
ordinal, **one** is an AC row's `--shell-timeout` value, and **five** are rationale quoting its own
vocabulary — three in the census's arm-differential paragraph and two in the seam-ordinal check's.
**Zero raised lines sit outside the three parts**, and the sum is the check — a walk that loses a
line shows up as a sum that misses 36, which recalling a site list never could. **One assignment
inside that partition is arguable and is named rather than hidden**: the census arm-(2) line the
needle raises states the arm's *control* (a fixture turning the shipped zero into one), while the
arm's own zero is written in a shape the needle does not raise; it is the `turns the shipped`
anchor, so a reader who reads it as harness output moves that one branch from `SITE` to neither
list and gets 11 + 17 + 8 instead of 12 + 16 + 8. The total, and the conclusion, are the same
either way. **Residual on this screen, exactly**: it proves the assignment is disjoint, exhaustive
and one-anchor-one-line, and it does **not** prove that an anchor is in the right *part* — that is
still a reading. What it changes is the failure mode: a dispute is now about a named member a
reader can point at, never about a member nobody can find, which is the only defect the previous
form could hide. It is also immune to the hazard that its own needles are text: its corpus is the
frozen `cf3a862` blob, so nothing written into this document afterwards — including this fence —
can enter the scope it counts. The `$STRIP` bound carried its reason in prose and no
label until v1.100; the `1861157` restatement carried a command and a sha and no label until
v1.101; the provenance probe carried a command and a sha and no label until this revision.
**The `headings shipped 0` column is still excluded, and the carve-out now states its bound
instead of leaving it to be read off one instance**: a composite is excluded only where **its own
arms are separately stated at the same sha over the same corpus**, so the same composite restated
at another sha, or over another corpus, is a site of its own until its arms are measured there.
That is exactly what the `1861157` sentence is — a different corpus, 25 files, whose arms nothing
had measured — and it is why it counts rather than being covered. (A reader re-running the sweep
at a later sha gets a larger number: **36** at `cf3a862`, **42** at `7982c18` and at `4e4a00c`,
**50** at `06ef40f` and at the freeze sha `68a70d6` — the four shas later than the stamped one,
all four re-derived with the bracketed needle above, as was the stamped `36` itself. The delta is the labels each revision writes into candidate lines, which is why the figure
is stamped at a blob and deliberately not given for the working file: this revision writes more
labels again, so a working-file value would be a number this paragraph moved by being written.) **Residual, stated as a
category rather than as "and similar"**: these screens are two-state differentials, so an arm
whose "repair" is itself wrong would read as agreement with the shipped code; that is why each
repair must first move its control. And `ANYIND` is the arm-(2) *screen*, not the arm-(2) *fix* —
a real fix models list-item container indentation, which is why arm (2) is still owed. The
candidate sweep above is itself a *reading*, not a partition: the count is mechanical, the
nine-site classification is not, and there are **three** ways to be missed by it. The count was
two until v1.102, and it was two because it was reasoned from the misses that had happened rather
than derived from the walk; the third is the one that actually took the provenance probe.
**Outside the needle** — an absence claim written in a shape matching neither ``[`]0[`]`` nor
``expect[ ]0`` is never raised at all. **Inside the needle, mistaken for output** — a candidate
line whose zero is *about a corpus but printed by, or read off, a control harness* looks like
harness output rather than like prose making a claim, which is exactly how the two census arms
were dropped from the denominator; so a candidate line standing inside a fence's quoted output, or
in the prose disposing of that output, counts as an absence claim until it is shown not to be one.
**Inside the needle, needing no interpretation at all, and simply not enumerated** — a raised line
that is plain prose, carries its own command and sha, and reads as an absence claim on sight, left
out because the site list was assembled from memory. The `1861157` restatement and the `35698f9`
provenance probe were both missed this way, and neither is a classification failure: nothing about
either line is ambiguous. Only the walk closes it, which is why the walk and not the list is now
what the denominator rests on. **And the walk's own residual, exactly**: the
walk makes the denominator complete, not automatic — each raised line's *disposition* is still a
reading, and the one boundary it turns on is a line that quotes a harness's `0` and then
generalises it into a claim about the corpus. Such a line is both harness output and prose making
a claim, nothing mechanical separates the two, and the `1861157` restatement was exactly that
line. Where the reading is genuinely undecidable the line counts as a site, because a spurious
label costs a sentence and a dropped one has now cost three revisions.

**The rule over the axis**: every measurement this document states must either publish its command
inline or name a script `git ls-files` can find — a figure whose derivation lives in an untracked
throwaway is not re-derivable, however correct the figure happens to be. **Residual, exactly**:
this census and the eleven-shape ATX proxy close the axis for the two untracked scripts this
document has ever cited, `heading_differential.py` and `grammar_corpus.py`; any script cited in
future must pass that same `git ls-files` check before a figure derived from it is published here.

Candidate *counting* is where `extract` stops. Choosing among them is `select`'s job (see API):
`index` is 1-based and optional, and with no `index` zero candidates raise `BlockNotFound`, one
returns that block, and more than one raises `AmbiguousBlock(n)`. Ambiguity is never resolved by
taking the first, because a reordered document would then silently re-point the address at a
different block. **An `index` below 1 is validated before any lookup and raises `BadIndex(n)`**
(AC-1.9): the obvious `blocks[index - 1]` turns `0` into the *last* tagged block and a negative
value into some other one — a wrong block executed without a word, which is the failure the
explicit address exists to prevent. Past-the-end stays `BlockNotFound` (AC-1.4); that ordinal
names a block that does not exist, whereas `0` is not an ordinal at all.

### Substitution

`str.replace` — literal, never regex, so a key containing `.` or `[` behaves (AC-2.4).

**Replacement is simultaneous, and counts are taken on the original text** (AC-2.6). Every key is
counted against `block.text` as written, and the replacement is one pass over that text — a
single compiled alternation of the escaped keys, `re.sub("|".join(map(re.escape, keys)), lambda
m: subs[m.group(0)], text)` — so replaced text is never re-scanned. **An empty map short-circuits
before that line**: `substitute(block, {})` returns `(dataclasses.replace(block), {})` — a
zero-key alternation is `""`, which matches the empty string at every position and would raise
`KeyError("")` from the callback — and this is the ordinary path for a CLI invocation with no
`--subst`, so it is covered by both an API test and a zero-`--subst` CLI test
(`test_empty_substitution_map_is_a_no_op`, mutation `empty-map-not-short-circuited`). That is what makes the result
order-independent: with `A→B` and `B→C` on a block containing `A B`, the outcome is `B C`
whatever the map's iteration order, whereas the sequential count-then-replace an earlier draft
prescribed yields `C C` when `A` is replaced first and `B C` when `B` is — an outcome that
depends on dict order, exactly the surprise AC-2.7 refuses overlapping keys to avoid,
re-created one step later. Overlap refusal (below) is what makes the alternation unambiguous, so
no key can match inside another. Each reported count is the number of matches in the original
text, which is the number replaced (AC-2.5).

**Overlapping keys refuse** (AC-2.7). If any key is a substring of another, the result depends on
iteration order, and a silently order-dependent answer is the failure class this whole feature
exists to catch. `SUBST_OVERLAP keys=<n>` with a detail line per offending pair, exit 0, nothing
executed — rather than picking an order and documenting it, which only moves the surprise. `<n>`
counts the **distinct keys implicated**, not the pairs (`a`, `ab`, `abc` → `keys=3`, three pairs);
each unordered pair appears once as `overlap: "<shorter>" "<longer>"`, and the lines are sorted by
`(shorter, longer)`, so the same map always produces the same diagnostic.

Any key with a count of zero is collected; if the collection is non-empty nothing is executed and
every missing key gets its own detail line, **in the map's insertion order** — an absent key has
no position in the block, so the map (on the CLI, `--subst` argument order) is the only
deterministic order there is; `test_two_missing_keys_are_listed_in_map_order` pins it. **An empty
key is refused here, in the API** —
`BadSubstArg("")` — not only by the CLI parser: `str.replace("", v)` inserts `v` at every character
boundary, and an in-process caller must meet the same wall `main` does.

### Execution

`tempfile.mkdtemp()` **followed by `os.chmod(cwd, 0o700)`** is the cwd. `mkdtemp` alone gives
`0o700 & ~umask` — probed: under `umask 0777` it yields mode `0o0` — so "0700 by construction",
which an earlier draft claimed, was only true under the default umask; the chmod makes AC-3.13
true everywhere. **`cwd` is `None` until `mkdtemp` returns**, and cleanup and read-back run only
when it is not `None`: a `mkdtemp` that raises records `LaunchFailed("mkdtemp", err)` with no
directory to remove, so the `finally` and the read-back are skipped rather than tripping over an
unbound name (a literal "always `rmtree(cwd)`" is an `UnboundLocalError` on that path, which is a
traceback where AC-4.6 promises a verdict). **A chmod that fails is not a special rollback path**:
by then `cwd` is set, the chmod runs inside the same `try` whose `finally` removes the cwd, so a failure records `LaunchFailed("mkdtemp", err)`
as the pending outcome and falls through to the ordinary cleanup, read-back and selection —
`CleanupFailed` (with the `LaunchFailed` as `__cause__`) if the removal fails or the directory
persists, else the `LaunchFailed`. `test_chmod_rollback_failure_is_cleanup_failed` injects both
(`os.chmod` raising, `shutil.rmtree` raising) and asserts that chain. `start_new_session=True` puts the
child in its own process group, which is what makes the timeout path able to reap grandchildren
rather than orphaning them. That failure was observed in this repository this session and the
count is cited rather than recalled — four orphaned `hmad-dispatch exec-pane agy` processes, PIDs
`82161 85642 90677 91239`, PPID 1, elapsed 2d 13-15h, each a `sleep 1` poll loop surviving its
dead `pytest-9187/9132/9124/9102` run (`pgrep -fl 'exec-pane'`, reaped the same session). On
`TimeoutExpired`: **`os.killpg(proc.pid, signal.SIGKILL)`** — the pid directly, *not*
`os.getpgid(proc.pid)`. `start_new_session=True` calls `setsid()`, so the child is a group leader
and its pgid is numerically its pid; going through `getpgid` only adds a lookup that can fail.
Measured this session, and the failure is the very bug this path exists to prevent:

```
pgid == pid ?  38030 == 38030  -> True
getpgid after child exit: ProcessLookupError   <-- direct child gone, grandchild still alive
killpg(pid) after child exit: reached the group
grandchild 38032 alive_after=False
```

When the direct child has already exited but a grandchild holds the pipe open — exactly the
timeout shape — `getpgid` raises `ProcessLookupError`, the reap aborts, and the grandchild is
orphaned. `killpg(proc.pid, …)` still reaches the group.

**Two races remain on that path, and both are handled rather than left to a traceback** (AC-5.5):

1. **The group empties between `TimeoutExpired` and `killpg`.** The helper first calls
   `proc.poll()` — non-blocking, it reaps the leader if it has already exited — and only then
   `os.killpg(proc.pid, SIGKILL)`, catching `ProcessLookupError` as "already reaped". **The
   `poll()` is load-bearing, not tidiness**: a leader that exited is a zombie until reaped, and
   measured on macOS, `killpg` on a zombie-only group raises `PermissionError`, not
   `ProcessLookupError` (plan §Measurements, the naturally-emptied-group probe); after `poll()`
   the same call raises `ProcessLookupError`. Without the `poll()` the natural race would be
   misreported as `LAUNCH_FAILED stage=reap` (the `poll-before-killpg-removed` mutation).
   **The test needs no fake**: `test_timeout_survives_a_group_that_already_emptied` runs a leader
   that starts an `os.setsid()` descendant holding stdout and exits at once; `communicate` times
   out on the escapee's pipe, `poll()` reaps the zombie, `killpg` raises `ProcessLookupError`, the
   drain times out, the pipes close, `wait()` returns at once, and the verdict is `TIMEOUT` with
   the cwd gone — the test kills the escapee from its pid file in `finally`. That one real fixture
   drives both AC-5.5 races. Any other `OSError` from `killpg` *after* `poll()` (a
   `PermissionError` on a genuinely live child one cannot signal) is **not** allowed to escape as a
   traceback: the helper
   still runs the bounded drain and closes the pipes, does **not** `wait()` (a child it could not
   signal is not something to wait on unboundedly), records `LaunchFailed("reap", err)` as the
   pending outcome with `pgid: "<n>"` in its detail, and lets cleanup and the read-back run as usual
   (AC-4.6). **The same mapping covers the helper's own I/O on the child** (design audit v62): an
   `OSError` from the first `communicate(timeout)`, from the drain `communicate(timeout=DRAIN_SECONDS)`,
   from closing `proc.stdout`/`proc.stderr`, or from the `wait()` — none of which the
   `TimeoutExpired` handler sees — is `LaunchFailed("collect", err, pgid=<n>)`, and the child is then
   treated exactly as a timed-out one: `poll()`, `killpg(SIGKILL)` with `ProcessLookupError` as
   already-reaped, the bounded drain, the closes, and the `wait()` iff the group was signalled. Those
   later steps are best-effort under a pending `collect`: an `OSError` from any of them is attached
   as the pending error's `__context__` rather than replacing it, except a non-`ESRCH` `killpg`
   error, which is the `reap` stage and replaces it (the `collect` error becoming its `__context__`).
   When the pre-kill `poll()`, the drain's close or the `wait` raises under an ordinary timeout, the
   pending `BlockTimeout` is replaced by `LaunchFailed("collect", …)` with the `BlockTimeout` set
   as its `__context__` — `stage=collect` ranks with `stage=reap` in the precedence above. The
   `poll()` has its own guard (impl-plan audit v16): an `OSError` there records the `collect`
   outcome and the kill still proceeds — `killpg` is attempted without the reaped-zombie
   knowledge `poll()` would have given, so a `PermissionError` on a zombie-only group is then the
   `reap` stage, replacing `collect` with it as `__context__`, and `ProcessLookupError` is still
   already-reaped. `test_poll_oserror_is_launch_failed_collect` wraps the recorded instance's
   `poll` to raise `OSError(errno.ECHILD, …)` under a timed-out block and asserts `stage=collect`
   with a `BlockTimeout` `__context__`, `pgid:` in the detail, the cwd gone and the group gone
   (`real_killpg(pgid, 0)` → `ProcessLookupError`); mutation `poll-oserror-unmapped` (that guard
   removed, so the failure escapes as a traceback with the group unkilled) is killed by it. Cleanup and the read-back then
   run as usual, so a removal that fails is still `CLEANUP_FAILED` with the `LaunchFailed` as
   `__cause__`. Two tests, both through the AC-5.6 recording pass-through so the instance is in
   hand: `test_communicate_oserror_is_launch_failed_collect` wraps the recorded instance's bound
   `communicate` to raise `OSError(errno.EIO, …)` on its first call and pass through afterwards,
   under a block that would otherwise `RAN`, and asserts the verdict, the `os_error:` and `pgid:`
   detail lines, no `rc=`, the cwd gone, and the group gone (`real_killpg(pgid, 0)` raising
   `ProcessLookupError` — the test reaps what it launched, as the AC-4.6 reap test does);
   `test_drain_wait_oserror_is_launch_failed_collect` wraps the instance's `wait` to raise under
   a timed-out block whose group was signalled and asserts `stage=collect` with a `BlockTimeout`
   `__context__`, returned within the drain bound. Mutations `collect-oserror-unmapped` (the
   `except OSError` around the first `communicate` removed) and `drain-oserror-unmapped` (the guard
   around drain/close/wait removed) each let the traceback escape and are killed by those two tests. **Policy for a genuinely unsignalable group is diagnostic, not containment**: the
   helper has no signal that would work where `SIGKILL` to the group did not, so it reports the
   pgid and returns bounded rather than pretending; this is the one documented case in which a
   launched process may outlive the call. **The test for it must not become that case**: its fake
   `killpg` (the AC-4.6 injection, the only remaining use of the `os.killpg` seam) records the pgid
   and raises `PermissionError`. **`run_block` owns its `Popen` and exposes no handle**, so the
   test obtains one through the same recording pass-through AC-5.6 uses: `monkeypatch.setattr(dbe.subprocess, "Popen", recording_popen)`,
   where `recording_popen(*a, **kw)` calls the real
   `subprocess.Popen`, appends the instance to a list the test holds, and returns it unchanged —
   an observation of the real call, not a fault injection, restored by `monkeypatch` on exit. The
   teardown order in the test's `finally` is then exact: (1) real `os.killpg(pgid, SIGKILL)` on
   the recorded pgid; (2) `recorded.wait()` on the recorded handle, which reaps the zombie leader
   (measured: `os.kill(pid, 0)` succeeds on a zombie, so no assertion can pass before this step);
   (3) assert `os.killpg(pgid, 0)` raises `ProcessLookupError`. CPython's `Popen.__del__` never
   kills a live child, so without that teardown the fault-injected test would leave a `sleep`
   running after it returned.
2. **The post-kill drain does not finish.** After `killpg` a second `communicate` collects what
   the group wrote before dying; but a descendant that left the group (AC-5.2's `os.setsid()`
   escapee) still holds the inherited pipes, so that `communicate` can block for as long as the
   escapee lives. It is therefore bounded too — `communicate(timeout=DRAIN_SECONDS)`, a module
   constant of 5 s — and on its own `TimeoutExpired` the helper closes `proc.stdout` and
   `proc.stderr` itself, calls `proc.wait(timeout=DRAIN_SECONDS)` **only on the branch where
   `killpg` succeeded or raised `ProcessLookupError`** — the leader is then SIGKILLed or gone, so
   this normally returns at once, but a successful `killpg` is a signal delivered, not a completion
   deadline (a leader stuck in uninterruptible sleep exits when the kernel lets it), so the wait is
   bounded too (design audit v66): on its `TimeoutExpired` the pending outcome becomes
   `LaunchFailed("reap", <the TimeoutExpired>, pgid=<n>)` — the group was signalled and did not
   go, the same diagnostic-not-containment policy as an unsignalable group, ranked as every `reap`
   is, with the pending `BlockTimeout` (or `collect`) as its `__context__`; and **never on the
   `LaunchFailed("reap")` branch**, where the child could not be signalled (the state machine is:
   drain-with-timeout → close pipes → `wait(timeout=DRAIN_SECONDS)` iff the group was signalled;
   the AC-4.6 reap test asserts the bounded return, which is what proves that branch skips the
   wait). `test_wait_after_kill_is_bounded` wraps the recorded instance's `wait` to record its
   `timeout` keyword and raise `subprocess.TimeoutExpired(cmd=["bash"], timeout=DRAIN_SECONDS)` —
the constructor requires both positional arguments (measured on 3.11.8; impl-plan v1.29) — under a timed-out block on the AC-5.5
   escapee fixture — needed so the drain expires first: on a drain that succeeds, CPython's
   `communicate` calls `self.wait()` internally and the wrapper would fire on that call instead of
   the helper's own (impl-plan v1.18 derivation), and the recorded keyword is what proves which
   call was intercepted — and asserts the
   recorded keyword equals `DRAIN_SECONDS`, `LAUNCH_FAILED stage=reap` with `pgid:` in the detail,
   a `BlockTimeout` `__context__`, the cwd gone, and the return inside `timeout + 2 * DRAIN_SECONDS + 2`
   s (its `finally` reaps the real group through `real_killpg`); mutations `wait-unbounded` (the
   `timeout=` keyword dropped from that `wait`, so the recorder sees `None`) and
   `wait-expiry-unmapped` (the `except TimeoutExpired` around it removed, so the expiry escapes as
   a traceback) are both killed by it,
   and leaves the pending `BlockTimeout` in place — the `TimeoutExpired` handler records it **on
   entry, before the `poll()`**, so a later `poll()`/drain/close/`wait` failure has a pending
   outcome to replace and attach as `__context__` (impl-plan v1.17 derivation); the drain itself
   records nothing — and nothing raises inside the handler, so the post-`finally` read-back still runs. The escapee is outside the reap by AC-5.2's
   stated scope; what this bounds is the *helper's* wall time, which is now at most
   `timeout + 2 * DRAIN_SECONDS` (the drain and the bounded wait) plus process teardown, so FR-5's "every run is bounded" holds against
   an escapee rather than only against a well-behaved block. Partial output from a timed-out
   block is discarded in both cases — `TIMEOUT` is a cannot-judge and carries no streams.

**Cleanup is verified, never suppressed** (AC-3.14). `shutil.rmtree(cwd)` — *without*
`ignore_errors` — runs in `finally`, so the temp directory is removed on the normal path, the
timeout path, and an exception path alike; its `OSError`, if any, is caught and recorded there
rather than raised from inside `finally` (which would replace whatever exception was in flight).
Because the timeout handler *records* `BlockTimeout` as a pending outcome rather than raising it
(see the precedence paragraph under Architecture Overview), control always reaches the statement
after the `try`/`finally`, where the helper reads the directory back: `os.path.lexists(cwd)` must be
false. If it is not — **or** an `OSError` was recorded, whichever alone —
`CleanupFailed(cwd, cleanup_error)` is raised and `main` prints `DOCBLOCK: CLEANUP_FAILED path="<p>"`,
exit 2. **Its causal data is two named things, never one overloaded slot:** the `cleanup_error`
attribute is the recorded `OSError`, or `None` when nothing was raised and the read-back alone
caught it; `__cause__` is the *pending outcome* when there was one (the `BlockTimeout`, or a
`LaunchFailed`), else `cleanup_error`. So: normal run + cleanup failure → `__cause__ is
cleanup_error`; timeout + cleanup failure → `__cause__` is the `BlockTimeout` and `cleanup_error`
still carries the `OSError`; read-back-only retention → `cleanup_error is None`. **The
two guards are separately mutation-tested, because the read-back makes `ignore_errors` look
redundant:** `cleanup-errors-ignored` (restore `ignore_errors=True`) is killed by
`test_cleanup_failure_carries_the_os_error`, which fault-injects an `rmtree` that raises and
asserts `cleanup_error` is that error — under the mutation nothing is recorded, the read-back
trips, and `cleanup_error` is `None`; `cleanup-readback-removed` (drop the `lexists` check) is killed by
`test_cleanup_readback_catches_silent_retention`, which fault-injects an `rmtree` that does
nothing and raises nothing — under the mutation the run reports `RAN` over a retained directory. The failure is real and cheap to produce: a block that runs `mkdir keep && chmod 000 keep`
leaves a subdirectory `rmtree` cannot list, on which `rmtree` measurably raises `PermissionError`
and `rmtree(…, ignore_errors=True)` measurably retains the whole tree with no signal (probed on
the supported interpreter — python 3.11.8, darwin, euid 501; command and output in the plan's
§Measurements). That silent retention is the mutation-verification invariant's
"a completed run reported over an unverified mutation", and it is what the old `ignore_errors=True`
did. **Precedence:** a cleanup failure outranks a `BlockTimeout` on the same run — the pending
`BlockTimeout` becomes `CleanupFailed`'s `__cause__` — because a retained directory is state the
operator must act on (exit 2, an operational error) whereas the timeout is a verdict about the
block (exit 0) already implied by the retained directory's partial contents; neither carries
`rc=`. The fixture test
restores the subdirectory's mode and removes the tree in its own `finally`, so the suite does not
leak what it just proved the helper cannot remove.

`stdout` and `stderr` are captured separately (`subprocess.PIPE` each) and never merged. **The
launch names the cwd explicitly** — `Popen(…, cwd=cwd, …)`: creating and chmodding the directory
does nothing to the child's working directory by itself, and without the keyword the block runs
wherever the caller does, which is the repository (AC-3.1/3.2 fail silently); the
`cwd-not-passed` mutation pins it. **The launch is text-mode, and the policy is explicit**: `Popen(…, text=True, encoding="utf-8",
errors="replace")`, so `communicate()` returns `str` (which is what `RunResult` promises and what
the held artifact handles — opened `encoding="utf-8"` — accept), non-ASCII output round-trips, and
an undecodable byte becomes U+FFFD instead of a `UnicodeDecodeError` escaping the helper (AC-3.6).
**The bound is validated before the spawn — and before `mkdtemp`** (AC-5.6): `timeout` must
satisfy `math.isfinite(t) and t > 0`, else `BadTimeout(value)`, raised while there is nothing to
clean up, so the refusal can neither leak a directory nor need the read-back — `communicate(timeout=-1)` raises
`ValueError` only after the child exists, and `inf` is no bound at all.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `h_mad_doc_block_exec` | `h-mad/scripts/h_mad_doc_block_exec.py` | new | extract / substitute / run / CLI |
| Helper suite | `h-mad/tests/test_h_mad_doc_block_exec.py` | new | FR-1..FR-5 ACs |
| Helper mutation spec | `h-mad/tests/mutation-specs/doc_block_exec.json` | new | guards for FR-1..FR-5 — 81 mutations (81 rows: 80 of the helper's source, 1 of `h-mad/SKILL.md` — `registry-row-removed`, the only row whose mechanism names `SKILL.md` as the file the harness edits; re-derive from the matrix's mechanism column, never from this cell), each bound to its RED test, enumerated under Test Plan |
| Wire mutation spec | `h-mad/tests/mutation-specs/doc_block_exec_wire.json` | new | FR-6 connection, both directions — eight mutations: `wire-revert-extract`, `wire-revert-select`, `wire-revert-run`, `wire-revert-substitute`, `wire-unconditional`, `exec-scan-executes`, `consumer-from-import`, `hand-rolled-extraction-widened`, each bound to its `tests/test_h_mad_collect_report_docs.py::<name>` (table under Test Plan) |
| Registry entry | `h-mad/SKILL.md` (Helper scripts) | modify | contract + remedy rows (AC-4.5) |
| Tagged fence | `h-mad/SKILL.md` (Second surface) | modify | the one opt-in block (AC-6.1) |
| Migrated consumer | `h-mad/tests/test_h_mad_collect_report_docs.py` | modify | drop hand-rolled extraction (AC-6.2); calls are module-qualified (`import h_mad_doc_block_exec as dbe` → `dbe.extract`/`dbe.select`/`dbe.run_block`) so the wire spies observe them |
| Delegating bounder | `h-mad/tests/docsections.py` | modify | import the authoritative module; drop the duplicate `_fence_aware_end` **and** the local heading regex in `titled_section` — both the section start (`_dbe.find_heading`) and its end (`_dbe.fence_aware_end`) come from the scanner (AC-1.8) |
| Delegation spy test | `h-mad/tests/test_docsections.py` | modify | gains `test_docsections_delegates_to_the_authoritative_bounder`, which spies BOTH `_dbe.find_heading` and `_dbe.fence_aware_end` through a recording fake installed as `sys.modules["h_mad_doc_block_exec"]` and bound by `importlib.reload(docsections)`, and in a `finally` restores the prior `sys.modules` entry and reloads `docsections` once more so `_dbe` re-binds to the real module before any later test runs (pytest restores neither the entry nor the module global on its own), the killer of `docsections.json`'s two wire mutations and one of the floor tuple's node IDs (AC-1.8, AC-6.4); the hostile `test_titled_section_ignores_a_heading_inside_a_fence` lives in the new module beside the other docsections-side tests |
| Bounder mutation spec | `h-mad/tests/mutation-specs/docsections.json` | modify | re-point `fence-tracking-removed` and `section-no-longer-owns-its-subsections` at `scripts/h_mad_doc_block_exec.py`; the other two anchors stay in `tests/docsections.py`; all four gain a `test` key (from their `_killed_by`) under a `target_command`; a fifth, `docsections-delegation-reverted`, is the Connection-enforcement wire mutation and is **connection-only**: the shared `import h_mad_doc_block_exec as _dbe` line is replaced by a private instance of the same file, loaded through `importlib.util.spec_from_file_location` + `exec_module` and registered in `sys.modules` only under its private spec name `_h_mad_doc_block_exec_private` (the registration is required: under `from __future__ import annotations` dataclass processing dereferences `sys.modules[cls.__module__]`, so an unregistered instance fails to load — measured, `AttributeError` on 3.11.8 with a frozen-dataclass callee), never under the name the import system resolves — so there are two bounders again, byte-identical, the callee untouched and no local bounder restored, and only the wire test can see it; killed by `test_docsections_delegates_to_the_authoritative_bounder` (whose recording fake is installed in `sys.modules` and bound by `importlib.reload(docsections)` — never by the mutant's file-path load) with **every** other test green: the helper's behaviour tests, the two docsections-side hostile tests and the source guard `test_docsections_has_no_second_bounder`, whose source predicate still holds — which is what makes it the isolated-wire proof (design audit v58: the earlier local-restore revert also failed the two hostile tests, so its kill was confounded with behaviour); a sixth, `docsections-syspath-setup-removed` (the `sys.path.insert` that makes the delegating import self-contained is deleted), is killed by `tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd` — a fresh `python3 -c "import docsections"` with only the tests dir on `sys.path` and `cwd=tmp_path`, a process that has imported nothing else — so the wire's import cannot ride another module's `sys.path` side effect; a seventh, `docsections-heading-lookup-reverted` (the local heading `re.search` restored, `find_heading` untouched), is killed by the same delegation spy, whose `find_heading` recorder then sees no call; an eighth, `docsections-local-bounder-restored`, keeps that local-restore revert as its own row — the old `_fence_aware_end` toggle and `_find_heading` regex restored in `tests/docsections.py`, both call sites re-pointed, `_dbe` still imported — bound to `tests/test_h_mad_doc_block_exec.py::test_docsections_has_no_second_bounder`, so the source guard has a named RED of its own (the WIRE-PIN and the two hostile tests also go red under it, which is exactly why it cannot be the isolated-wire proof; its killer collects under the mutant because that file imports `docsections` only inside test functions) |

## Implementation Order

1. **Task 1 — scanner, selection, info-string grammar, and the bounder's second consumer.** In
   `h-mad/scripts/h_mad_doc_block_exec.py` (new): `Block`, the private `_fence_events` scanner,
   `fence_aware_end` with the full fence rule, `find_heading`, `extract`, **`select`** (the ordinal policy — `BlockNotFound`, `AmbiguousBlock`,
   `BadIndex` — without which `main` has no specified way from `list[Block]` to the one `Block`
   `substitute` and `run_block` take), tag and key validation; tests in
   `h-mad/tests/test_h_mad_doc_block_exec.py` (new) and the matching rows of
   `h-mad/tests/mutation-specs/doc_block_exec.json` (new). **In the same task**,
   `h-mad/tests/docsections.py` drops `_fence_aware_end` and its local heading regex and delegates through
   `_dbe.find_heading` and `_dbe.fence_aware_end`, `h-mad/tests/test_docsections.py` gains the delegation spy test, and
   `h-mad/tests/mutation-specs/docsections.json` is re-pointed, converted to named-test form and
   run to `ALL_CAUGHT` (the author-together ordering the plan requires). Satisfies FR-1 (incl. AC-1.8/1.9) and AC-3.7. **`wiring` shape** — it carries the docsections wire and its WIRE-PIN, so the impl-plan's one-shape rule makes it `wiring` with the new-behaviour RED split stated in prose (impl-plan audit v30).
2. **Task 2 — substitution.** `substitute` in `h-mad/scripts/h_mad_doc_block_exec.py`: simultaneous
   replacement, counts on the original text, missing-key collection, overlap and empty-key
   refusal, the empty-map no-op; its tests and mutation rows in the same two files as Task 1.
   Satisfies FR-2. Depends on Task 1 only for `Block`.
3. **Task 3 — execution and bounding.** `run_block` and **`RunResult`** in
   `h-mad/scripts/h_mad_doc_block_exec.py`: temp cwd (`mkdtemp` + `chmod`, `cwd` `None` until
   created), shell modes, preamble composition, the `poll()`-then-`killpg` process-group timeout,
   bounded drain, pending-outcome cleanup selection, and the exceptions those paths raise —
   `BadTimeout`, `BlockTimeout`, `LaunchFailed`, `CleanupFailed`; tests and mutation rows as
   above. Satisfies FR-3 and FR-5. Depends on Task 1.
4. **Task 4 — CLI and registry.** `main(argv)` in `h-mad/scripts/h_mad_doc_block_exec.py`: every
   verdict line in the table below, argument-value validation (`--index`, `--shell-timeout`,
   `--subst` syntax), the strict-UTF-8 pre-spawn read of `--preamble-file` (`PreambleUnreadable`),
   the two-arm stream reservation,
   descriptor alias check, `_final_write` with read-back verification, one closure path; and the
   Helper-scripts registry entry in `h-mad/SKILL.md` pinned bidirectionally (the two AC-4.5
   mutation rows land here — `registry-row-removed`, which mutates `SKILL.md`, and
   `detail-line-undocumented`, which mutates the **helper**; they are one pair by AC, not by file,
   and calling them "the two `SKILL.md` rows" is the 79+2 miscount this document carried).
   Satisfies FR-4, AC-3.8/3.9. Depends on 1–3.
5. **Task 5 — the wire.** Tag the Second-surface gate fence in `h-mad/SKILL.md` **and** migrate
   the executing call site in `h-mad/tests/test_h_mad_collect_report_docs.py` — a new
   `_gate_block() -> dbe.Block` resolving through `dbe.extract`/`dbe.select`, `_gate_bash_block() ->
   str` reduced to `_gate_block().text` so its two text-pin callers keep their string, and
   `run_recipe`, hoisted out of its enclosing test to a module-level
   `_run_recipe(*, phase, cycle, report, root) -> dbe.RunResult` — unpacking `subbed, _counts = dbe.substitute(block, {…})` — `substitute` returns a `(Block, counts)` tuple (AC-2.7), and only the `Block` reaches the runner — and calling `dbe.run_block(subbed, preamble=preamble, timeout=60.0)`, an explicit bound the wire pin asserts — so a wire pin can call and spy it
   (its two call sites read only `.stdout`/`.stderr`, which `RunResult` carries) — in one task, with
   `h-mad/tests/mutation-specs/doc_block_exec_wire.json`
   (new) and the six named tests in that file — **and, authored here rather than in Tasks 1–4
   because they assert post-Task-5 state, `test_exactly_one_tagged_fence_in_the_tree` (the tag
   exists only after this task) and `test_suite_floor_holds` (its floor tuple exists only
   after this task), both still living in `h-mad/tests/test_h_mad_doc_block_exec.py`**. The text scan
   inside `test_exec_codex_dispatch_carries_out_log_and_timeout`
   (`h-mad/tests/test_h_mad_collect_report_docs.py`) is deliberately untouched:
   it selects a *different*, untagged block (`exec codex`) and only inspects it, so it neither
   breaks nor belongs behind an executor.

   **The migrated address bounds a strictly smaller span than the slicer it replaces, and the
   magnitude is stated because the divergence outlives this task.** `_gate_block()` calls
   `dbe.extract(SKILL_MD, "## Second surface — the codex leg")`, which by AC-1.5 ends at the next
   **same-or-shallower ATX heading** — today `## Teammate audit leg — when codex is unavailable` —
   where `_second_surface()` ends at the *named* `## Helper scripts` anchor. Measured at `a8e0372`
   with the snippet below (swapping only the tail anchor): the executor's span is 50 lines
   holding 4 bash blocks, the named-anchor span 159 lines holding 7. **Only one of
   `_second_surface()`'s eight call sites migrates — the one inside `_gate_bash_block`**; the
   other seven are each inside a named test function, so the sites are located by enclosing
   symbol rather than by line and survive any edit that does not rename them. Derive the set,
   never read it — no line numbers on purpose, since a line pin goes stale on any insertion above
   it and gives no signal that it has.

   **This is a rule over the whole document, not a treatment of this one site, and the class is
   now closed**: *outside* §Version History, no code site in this design is addressed by a line
   number — every one names its enclosing symbol (a `def`, or the test function a statement sits
   in). **The exemption is for line pins only, and only in §Version History**, whose entries are
   dated records of what was written at the time rather than live locators — one of them (v1.93)
   quotes a line pin that was accurate when that entry was authored, and it stays. **The
   ordinal-base rule stated just below is *not* exempt there**, because it governs every ordinal
   that **indexes a span** wherever one is written, §Version History included — which is a
   narrower set than every ordinal, and the residual where that rule is stated says exactly which
   ordinals fall outside it and which rule catches them instead. **The seam-naming rule (§Test Strategy) prohibits *addressing* a
   seam by ordinal, and that prohibition is scoped outside §Version History too** — for the
   reason given where the rule is stated, which also gives the command that derives how many
   entries there carry one. **No count of those entries is written at this site**: it grows with
   every revision that records a strike, and a figure here would be a second place for it to go
   stale. Verify the line-pin class rather than trusting this sentence, with the corpus split at
   the §Version History heading:

   ```bash
   awk '/^## Version History$/{v=1} !v' docs/02-design/features/doc-block-exec.design.md \
     | grep -nE '[A-Za-z0-9_./-]+\.(py|md|json|sh):[0-9]+|`:[0-9]+`' | wc -l   # expect 0
   ```

   **Residual on the detector itself, exactly** — it is published as *proof* that the class is
   closed, so the shapes it cannot see are part of what that proof is worth. Its pattern matches
   two forms and no others: a filename-shaped token bearing an extension, followed by a colon and
   digits, and a backticked colon-plus-digits. It is blind to a pin written as the word *line* or
   *lines* plus a number, as an `L`-prefixed number, or as a colon-plus-number not preceded by a
   filename-shaped token. Those three blind forms were swept separately at `74e126f`, again
   at `35698f9` (the alternation below is in both blobs, so both runs are reproducible), and
   again on the working file this revision ships, **after the v1.103 entry**, over the same
   head-of-document corpus, with the alternation
   `line [0-9]{2,}|lines [0-9]{2,}|\bL[0-9]{3,}\b|[^A-Za-z0-9_./-]:[0-9]{2,}`, and the only hits
   are the two `lines …` fields of the block-census *output* quoted above — a printed count, not
   a locator. So the class **is** closed today and the `0` is honest; what the fence above does
   not by itself establish is that a *future* pin written in one of the three blind forms would
   be caught, and the sweep just named is what catches it.

   **A fourth blind form, and why this detector is exempt from the fold §Test Strategy imposes on
   the ordinal check**: `grep` is line-scoped and this file hard-wraps, so a detector can miss an
   instance the wrapper split. That is a live hazard for a multi-*word* target and not for this
   one — a `path:NNN` pin contains no whitespace, so no hard-wrapper can break it; only a
   hand-inserted newline inside the token could, which is why the fence above stays line-scoped
   and readable. It was checked rather than assumed — **on the working file this revision ships, after the v1.103 entry**, and the
   phrasing is deliberate: this fence does not exist in the `35698f9` blob
   (`git show 35698f9:$D | grep -cF "tr '\\n' ' '"` → `0`, against `1` at `6f0ee85`), so a bare
   sha here would send a reader to a document that does not contain the thing being validated.
   **That `0` is an absence claim about a corpus — a blob of this document — and it is the ninth
   labelled site of the absence rule, the paragraph in §Scanning (`extract`) opening "The rule
   over the absence axis": *vacuous*, because the fence does not exist in that blob at all, so
   nothing was exercised there.** Its positive is the
   paired `1` at `6f0ee85`, which is what shows the needle matches when the shape is present and
   keeps this from being a `0` a broken command could also print. It carried a command and a sha
   and no label through three sweeps because it is a *provenance* probe — an absence used to
   justify which stamp a neighbouring figure gets, rather than to establish a property — and
   nothing in the rule exempts that use; it is measured like any other zero.
   **The rule over that axis: a bare sha names a *blob*, so it belongs to a tree-derived figure; a
   document-self figure names the working file and the entry it was run after.** With a
   space-tolerant colon so that a folded pin *would* be caught:

   ```bash
   awk '/^## Version History$/{v=1} !v' docs/02-design/features/doc-block-exec.design.md \
     | tr '\n' ' ' \
     | grep -oE '[A-Za-z0-9_./-]+\.(py|md|json|sh): +[0-9]+' | wc -l | tr -d ' '   # expect 0
   ```

   It returns `0`. Its own residual: a space-tolerant colon over folded prose would also match an
   ordinary sentence of the shape "`docsections.py`: 30 files", so this form is a *screen* to be
   read, not a gate — it is the strict fence above that carries the rule.

   **Residual on the enclosing-symbol locator, exactly**: it does not distinguish two `def`s of
   the same name in one file (Python keeps the last, so a reader must too), and it goes stale
   silently if the symbol is *renamed* rather than moved. The signal for the second case is the
   ast one-liner below returning a name this document does not list — a changed set, not a
   changed line, is what a reader should look for. Locating by symbol trades a failure mode that
   is invisible (a line pin that still points at *some* line) for one that is loud (a name that
   is no longer there). The set of eight, derived and not read:

   ```bash
   python3 -c 'import ast; t=ast.parse(open("h-mad/tests/test_h_mad_collect_report_docs.py").read()); print(sorted({d.name for d in ast.walk(t) if isinstance(d, ast.FunctionDef) for c in ast.walk(d) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "_second_surface"}))'
   ```

   At `a8e0372` that returns eight enclosing symbols: `_gate_bash_block` (the one that migrates)
   and seven `test_…` functions, of which `test_exec_codex_dispatch_carries_out_log_and_timeout`
   is the one holding the deliberately untouched hand-rolled `re.findall` scan. (It returns the
   same eight at `335f535`.) Residual specific to *this* locator, on top of the general one
   above: it finds calls by the name `_second_surface`, so reaching the slicer through an alias
   makes it return fewer symbols — a shrinking count is the signal to re-derive,
   not to assume the migration widened. After this task the file therefore holds two notions of "the
   Second-surface section" side by side. The migration is correct today because the one fence
   containing `h_mad_audit_gate.py` falls inside **both** spans. **Residual, exactly**: an
   `h_mad_audit_gate.py`-bearing fence added under `## Teammate audit leg` (or under any later
   `##` section before `## Helper scripts`) would be visible to the seven survivors and invisible
   to the executor — the two would then disagree about which block gates, and only the seven would
   see the new one. Closing that divergence is out of this feature's scope; it closes when the
   remaining seven migrate. Satisfies FR-6. **Wiring shape**, not new behaviour.
   Depends on 1–4. Tag and migration cannot be split: tagging the gate fence makes
   `_gate_bash_block`'s own `re.findall` — which requires `\n` immediately after ` ```bash ` — match **one fewer block than
   the section holds**, and drops the `h_mad_audit_gate.py` filter to zero. **This is a
   behavioural premise, so it travels with its command rather than with a figure** — the figure
   moves whenever a `##` section is inserted between `_section`'s two string anchors, which is
   exactly what happened between `1861157` and `a8e0372` (commit `6db8e50` inserted
   `## Teammate audit leg — when codex is unavailable`, and the fence-blind span the named-anchor
   slicer sees grew from 50 lines to 159). Re-derive, do not read:

   ```bash
   python3 -c 'import re; t=open("h-mad/SKILL.md",encoding="utf-8").read(); s=t.index("## Second surface — the codex leg"); sec=t[s:t.index("## Helper scripts", s)]; b=re.findall(r"```bash\n(.*?)```", sec, re.S); print("lines", sec.count(chr(10)), "blocks", len(b), "gating", len([x for x in b if "h_mad_audit_gate.py" in x]))'
   ```

   (One physical line on purpose: this fence is indented inside a list item, and a heredoc form
   would carry that indentation into the Python body. Swap `"## Helper scripts"` for
   `"## Teammate audit leg"` to measure the executor's AC-1.5 span instead.)

   Measured at `a8e0372`: `lines 159 blocks 7 gating 1`; after the gate fence is tagged,
   `blocks 6 gating 0`. (At `1861157` the same command gave `lines 50 blocks 4 gating 1` → `3`/`0`,
   which is where this document's earlier figures came from — both re-derived here from the git
   blobs, not carried.) **Neither block is *selected* by position: each is addressed by a
   content predicate, in the code and in this document.**
   `_gate_bash_block` filters `[b for b in blocks if "h_mad_audit_gate.py" in b]` and asserts the
   result is exactly one; the untouched scan filters `if "exec codex" in b` and takes the first
   match. So the **content predicate is what the code uses and what the `hmad:exec` tag
   replaces** — that is the load-bearing part, and nothing here turns on an offset.

   **An ordinal over these blocks is informational, not load-bearing, and it is true**: the
   earlier revision of this paragraph over-reached by calling a positional claim a description of
   something the code does not do. It is not: the ordinals are a real, re-derivable property of
   the census output, and they are stated informationally elsewhere in this feature's document
   set. What a bare "index N" lacks is its **base**, and that is a live ambiguity rather than a
   theoretical one — two independent re-derivations of this census named the same two blocks
   under 0-based and 1-based conventions that differ by one. **So the rule over the axis is: an
   ordinal must always name both halves of its base — the index convention *and* the span it
   indexes — and it must never be given as the thing the code selects on.** **Its scope is every
   ordinal that picks a position out of an ordered span, anywhere in this document, §Version
   History included**; an ordinal over an unordered *set* has no base to name and is governed by
   the seam-naming rule instead, whose exemption and derived count are stated with it. Stated in full,
   re-derived at `335f535` with `enumerate(b, 1)` (1-based) over the **7** blocks the named-anchor
   command above returns (add `[i for i, x in enumerate(b, 1) if …]` to that one-liner to print
   them): the gate block is **4** and the `exec codex` block is **2**. Over the
   **4** blocks of the executor's AC-1.5 span (tail anchor `## Teammate audit leg`) the same two
   ordinals come out **4** and **2** as well, so on this tree the two spans happen to agree —
   which is a coincidence of where the blocks fall, not a property, and is exactly why the span
   half of the base has to be stated. **Residual, exactly**: any ordinal quoted here is tree
   state at `335f535` and moves whenever a bash fence is added, removed or reordered inside the
   Second-surface section; the content predicate does not.
   What is load-bearing here is only that the `findall` count
   drops by one while staying non-empty, and the gating count goes 1 → 0. **What goes to zero is
   the `h_mad_audit_gate.py` filter on the next line, so the loud failure is `_gate_bash_block`'s
   `assert gating`, not an empty `findall`** — an implementer looking for the latter will not find
   it and will read the RED as unexplained. It fails loudly rather than silently, which is the good
   case, but it is still a broken suite if the two are separated across tasks (plan v1.84, which
   corrected this same sentence there).

## Data Model / Schema Changes

No persisted schema. Two in-memory frozen dataclasses:

```python
@dataclass(frozen=True)
class Block:
    text: str        # fence body, no trailing newline normalisation
    shell: str       # "strict" | "plain"
    lineno: int      # 1-based line of the opening fence
    info: str        # raw info string after the language word

@dataclass(frozen=True)
class RunResult:
    rc: int          # exit code of the ONE `bash -c` spawned (block alone, or
                     # preamble+block combined) — never the tool's verdict
    stdout: str
    stderr: str
    shell: str
```

## API / Interface Changes

**Scanning and selection are separate functions, and that separation is the fix for a real
ambiguity in v1.0**: `extract` was typed `list[Block]` while the error contract had it raising on
0 or >1 candidates, which cannot both be true and left implementers unable to tell where refusal
lives. Split, each has one job:

```python
def extract(doc: str | Path, heading: str) -> list[Block]:
    """Pure scan. `doc` is a PATH (a str is converted with Path), read as
    strict UTF-8 — never document text. Returns every tagged block under `heading`, possibly empty.
    Raises DocUnreadable, BadInfoString or AmbiguousHeading — never on candidate count."""

def select(blocks: Sequence[Block], index: int | None = None) -> Block:
    """Policy. Raises BadIndex(n) (index given and < 1 — validated BEFORE any
    lookup, so 0 can never reach `blocks[index - 1]` and alias the last block),
    BlockNotFound (0 candidates, or index past the end) or AmbiguousBlock(n)
    (>1 with no index)."""

def substitute(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]:
    """Returns a NEW Block (dataclasses.replace) whose text has every key replaced,
    plus the per-key counts. run_block never substitutes: main calls this first,
    so a bad map is refused before any stream artifact is reserved."""

def run_block(block: Block, *, preamble: str | None = None,
              timeout: float = 30.0) -> RunResult:
    """Execution. Spawns exactly ONE `bash -c` (the block alone, or preamble and
    block combined) in a fresh temp cwd, bounded by `timeout` seconds. `RunResult.rc`
    is that child's exit code — never this tool's verdict. Never substitutes: the
    block it is handed is the block it runs. Raises BadTimeout, BlockTimeout,
    LaunchFailed or CleanupFailed."""

def main(argv: Sequence[str] | None = None) -> int:
    """CLI. Selection is `select(extract(...), index)`, then substitute, then
    run_block. Writes one `DOCBLOCK:` line to stdout and returns the process exit
    code: 0 on every verdict — RAN, every refusal and TIMEOUT — and 2 only on
    UNREADABLE, CLEANUP_FAILED and LAUNCH_FAILED. `--help` alone is argparse's own
    output and exit 0, the one exit-0 path that emits no `DOCBLOCK:` line."""

def fence_aware_end(text: str, start: int, level: int) -> int:
    """Offset of the next ATX heading at `level` or shallower after `start`,
    skipping fenced blocks under the full CommonMark fence rule: backtick AND
    tilde runs of >= 3, closed only by the same character at >= the opening
    length, opener and closer indented 0-3 spaces (4+ is an indented code
    block, never a fence). Fence state is established over COMPLETE lines
    from the document start through the line containing `start` (never a
    text[:start] slice, which can truncate a line after its marker run and
    fake a closer); a line is a candidate boundary iff its start offset is
    >= `start` (the line adjacent to a heading is included; a line that began
    before a mid-line `start` is not). So `start` may lie anywhere -- inside an open fence included -- and a
    fenced `#` after an arbitrary offset is never read as a heading; that is
    the contract `docsections.section_from` needs for its symbol-anchored
    offsets. The bounder `extract` uses, exported so
    `h-mad/tests/docsections.py` can delegate to it (AC-1.8)."""
```

```python
def find_heading(text: str, heading: str) -> tuple[int, int] | None:
    """Offset just past the matching ATX heading line and its level, found among
    the scanner's heading events only — never inside a fence. `heading` is either
    the full line form '## Text' (text AND level must match) or the bare 'Text'
    (any level; docsections.titled_section's contract). None when absent; raises
    AmbiguousHeading(n) when more than one matches."""
```

`__all__` names all seven functions, plus `Block`, `RunResult` and the whole `DocBlockError` hierarchy — the base class and its 19 subclasses — 29 names (`BadArgs` included); the seven-plus-two-plus-*subclasses* reading gives 28 and is the error to avoid — so a consumer catches `dbe.BlockNotFound` through the public surface (design audit v76: the impl-plan's Task 1 enumerates them). `fence_aware_end` and `find_heading` are public on purpose:
`docsections.titled_section` calls `find_heading` in place of its own `re.search` heading regex
and then `fence_aware_end` in place of the deleted `_fence_aware_end`; `docsections.section_from`
calls `fence_aware_end` with the same `(text, start, level)` arguments. A heading `find_heading`
reports absent keeps `docsections`' own loud failure (`test_a_missing_heading_fails_loudly`). Both it and `extract` are thin consumers of the private
`_fence_events(text)` generator (§Scanning), the single home of the fence grammar; the two
re-pointed `docsections.json` mutations therefore target `_fence_events`'s state transition and
`fence_aware_end`'s heading match, and every fence-grammar row of `doc_block_exec.json` anchors in
`_fence_events` too, where one mutant is seen by both consumers.

`main` is `select(extract(...), index)`. A caller that genuinely wants all candidates calls
`extract` alone — which is not a sweep, because it is still scoped to one document and one
heading and still returns only tagged blocks.

**`preamble` is the fixture boundary, and the feature does not work without it.** The block under
test is the doc's block, unmodified; a recipe that consumes a variable its surrounding prose sets
(the Second-surface gate block reads `COLLECT_OUT`) needs that value supplied from outside. The
preamble is shell text run in the same invocation immediately before the block, so a variable the
doc never claimed to define is bound before the recipe reads it — measured: without it the run still exits 0, still halts, and never reaches `GATE: PASS` — and it is deliberately a
separate parameter rather than string-concatenation by the caller, so the doc's text and the
fixture's text never blur. **Composition is `preamble.rstrip("\n") + "\n" + text′`** when a
preamble is given, and `text′` alone otherwise — where `text′` is the `.text` of the `Block`
that `substitute(block, subs)` returns,
the text that will actually run, never the unsubstituted fence body (the diagram's `text'`): the
preamble is prepended *after* substitution, so a substituted path stays substituted when a preamble
is present. Exactly one newline separates them, so a
preamble file without a trailing newline cannot fuse with the recipe's first token and one with a
trailing newline gains no blank line. **The combined invocation is what is measured** (AC-3.12): `rc`,
`stdout` and `stderr` on the returned `RunResult` describe preamble-plus-block as one `bash -c`,
so a preamble that fails is visible as that `rc` and its stderr rather than being swallowed — the
helper does not, and cannot, attribute a line to one half or the other. On the CLI it is
`--preamble-file <path>`: a file, because the real preamble contains command substitution and
quoting an inline form would corrupt it; a path that cannot be read raises `PreambleUnreadable`
in `main`'s pre-check, before the block runs.

`substitute` raises `MissingSubstitution(keys)`, `OverlappingSubstitution(pairs)` or `BadSubstArg("")`;
`run_block` raises `BadTimeout(value)`, `BlockTimeout(seconds)`, `CleanupFailed(path, cleanup_error)`
or `LaunchFailed(stage, err, pgid=None)`.
The CLI converts each to a verdict line — exceptions are the API's contract, tokens are the CLI's.

CLI:

```
h_mad_doc_block_exec.py <doc> --heading <h> [--index N] [--subst K=V]...
                              [--preamble-file PATH] [--shell-timeout SECONDS]
                              [--stdout PATH] [--stderr PATH]
```

There is deliberately **no** `--all`, no `--dir`, and no glob-accepting argument. That absence is a
requirement, not an oversight, and is pinned by a test asserting the parser rejects such input. The
parser is `argparse.ArgumentParser(allow_abbrev=False)`, so the documented spellings are the only
spellings — `--shell-t` is an error, not an alias — and a test asserts that too. **Argument values
are the contract's, argument grammar is argparse's**: `--index` and `--shell-timeout` are declared
`type=str` and validated by `main` (`BAD_INDEX` / `BAD_TIMEOUT`), so a malformed value still gets
one `DOCBLOCK:` line — **and so does a grammar error**: the parser is built with
`allow_abbrev=False` and its `error()` overridden to raise `BadArgs(message)`, a `DocBlockError`
that `main` renders as `DOCBLOCK: BAD_ARGS message="<m>"`, exit 0, because a malformed but
readable invocation is input the helper declined and the Audit-gate signal discipline admits no
non-`DOCBLOCK` exit (plan audit v67; an earlier draft left argparse's exit-2 usage error as "the
documented exception", which was a breach, not an exception). `--help` alone keeps argparse's
exit-0 help text.

**`exit_on_error` is left at its argparse default (`True`), and that is load-bearing.** An earlier
draft specified `exit_on_error=False`, which is precisely what suppresses argparse's own
`except ArgumentError: self.error(str(err))` — so a **missing option value** raised
`argparse.ArgumentError` inside `_parse_known_args` and never reached the override. `ArgumentError`
is not a `DocBlockError`, so it escaped `main` as a traceback with a non-`DOCBLOCK` exit: the exact
breach this paragraph forbids, on one of the two inputs `test_malformed_invocation_is_a_verdict`
drives. Measured on python 3.11.8 with `allow_abbrev=False` and `error()` overridden:

| grammar shape | `exit_on_error=False` | default (`True`) |
|---|---|---|
| unknown option | `BadArgs` | `BadArgs` |
| **missing option value** | **`ArgumentError` escapes** | `BadArgs` |
| missing required option | `BadArgs` | `BadArgs` |
| missing positional | `BadArgs` | `BadArgs` |
| abbreviation | `BadArgs` | `BadArgs` |

The class is closed at the default: all five grammar shapes reach the override, and `--help` still
exits 0 with its help text. The residual is anything argparse raises *outside* `error()` — nothing
in this CLI's grammar does, and a future argument type that can (a custom `type=` callable raising
something other than `ArgumentTypeError`) must route itself, since the parser will not.

`test_malformed_invocation_is_a_verdict` drives an unknown option and a missing
option value in-process and asserts one `BAD_ARGS` line each, exit 0, and no usage text on stdout;
mutation `argparse-error-unrouted` (the `error()` override removed, so argparse raises
`SystemExit(2)` and prints usage) is killed by it.

**Stream artifacts: reserved last, never truncated by an open, written through the held handle.**
The order in `main` is `extract` → `select` → `substitute` → the remaining validations (timeout,
preamble readability — the info string is validated inside `extract`, the ordinal inside
`select`, and `--subst` syntax before `substitute` is called) → **reserve** → **alias check on the
reserved descriptors** → spawn. Reservation opens `--stdout` then `--stderr` through the two-arm
`os.open` protocol below (`O_CREAT | O_EXCL` first, then `O_WRONLY | O_APPEND | O_NONBLOCK` on an
existing file), wraps each descriptor with `os.fdopen(fd, "a", encoding="utf-8")` and holds both
handles: append-mode creates or opens without emptying an existing file, so there is no moment at
which one artifact is truncated while the other is still unreserved (design audit v79: an earlier
sentence here still said plain `open(path, "a")`, which cannot establish `created` atomically). **Creation is detected atomically, not by an `exists()` check**: the
reservation is a two-arm loop: try `os.open(path, O_WRONLY | O_APPEND | O_CREAT | O_EXCL)` —
success means this call created the file and records `created=True`; on `FileExistsError` try
`os.open(path, O_WRONLY | O_APPEND | O_NONBLOCK)` **without `O_CREAT`** — success means a
pre-existing file (`created=False`). **The whole reservation stage is one mapped region**: the
two-arm loop, the `fstat` regular-file and alias checks on the descriptors, and the rollback of a
first reservation when the second fails (close, and unlink only if this call created it) sit inside
one `try`/`except OSError` mapped to `StreamPathUnwritable`, so no `OSError` from any of those calls
can escape as a traceback. `test_stream_path_under_a_regular_file_refuses` gives `--stdout` a path
whose parent is a regular file (`ENOTDIR` on both arms — a real fault, no injection, no permission
dependence) and asserts `UNREADABLE reason=stream_path_unwritable`, exit 2, no traceback, and a
side-effect block that left nothing; mutation `stream-open-oserror-unwrapped` (the region's `except
OSError` removed) turns that refusal into a traceback. `O_NONBLOCK` is what keeps the open **bounded**: on a FIFO
with no reader a blocking open never returns (no `DOCBLOCK:` line, no timeout — the block has not
even been spawned), whereas with `O_NONBLOCK` it fails at once with `ENXIO` — measured on the
supported interpreter (plan §Measurements cites the command): `OSError errno=6 (ENXIO) after
0.0000s` on python 3.11.8 / darwin, and with a reader present the open succeeds and `fstat`
reports `S_ISREG=False S_ISFIFO=True`, which is the case the regular-file check below refuses. Every descriptor from
either arm is then `fstat`ed and must be a **regular file** (`stat.S_ISREG`); a non-regular
descriptor is closed and refused as `StreamPathUnwritable`
(`UNREADABLE reason=stream_path_unwritable`), checked on the descriptor rather than the path so
there is no check-to-open race, and a file this call created that turns out non-regular cannot
exist (an exclusive create makes a regular file).

**Which non-regular kinds actually reach that check is a measurement, not a deduction, and only
two of five do.** v1.97 said *"a FIFO, socket, device or directory is closed and refused …
checked on the descriptor"*, then said two sentences later that a reader-less FIFO *"never
reaches the `fstat` check"* — the same paragraph asserting both. The five kinds were run:

```bash
python3.11 - <<'PY'
import os, socket, stat, tempfile, errno, sys, platform
d = tempfile.mkdtemp(); W = os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK
sp = os.path.join(d, 's.sock'); s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); s.bind(sp)
fp = os.path.join(d, 'f.fifo'); os.mkfifo(fp)
rp = os.path.join(d, 'r.fifo'); os.mkfifo(rp); reader = os.open(rp, os.O_RDONLY | os.O_NONBLOCK)
for label, path in (('directory', d), ('unix socket', sp), ('FIFO no reader', fp),
                    ('FIFO with reader', rp), ('char device /dev/null', '/dev/null')):
    try:
        fd = os.open(path, W)
        print(f'{label:24s} open OK    -> fstat reached, S_ISREG={stat.S_ISREG(os.fstat(fd).st_mode)}')
        os.close(fd)
    except OSError as e:
        print(f'{label:24s} open FAILS {errno.errorcode.get(e.errno)}({e.errno}) -> fstat never reached')
print(sys.version.split()[0], platform.system().lower(), platform.release())
PY
```

```
directory                open FAILS EISDIR(21) -> fstat never reached
unix socket              open FAILS EOPNOTSUPP(102) -> fstat never reached
FIFO no reader           open FAILS ENXIO(6) -> fstat never reached
FIFO with reader         open OK    -> fstat reached, S_ISREG=False
char device /dev/null    open OK    -> fstat reached, S_ISREG=False
3.11.8 darwin 25.6.0
```

**Both routes end at the same verdict, and that is why the design is unchanged by this.** A
directory, a unix socket and a reader-less FIFO never produce a descriptor at all: `os.open`
itself raises, and the reservation region's single `except OSError` maps it to
`StreamPathUnwritable` / `UNREADABLE reason=stream_path_unwritable` — the same line a reader sees
for a device. Of the five kinds measured, only a character device and a *reader-present* FIFO reach `fstat`,
and within that measured set they are the only inputs that can kill the `S_ISREG` mutant; the set
is not closed — a block device, for one, is untested here. **The rule over that axis**: for a refusal
reached by two routes, name which route each input takes and prove it by running the input — the
verdict being identical is exactly what makes the wrong route-claim invisible to every test.
**Residual, stated as a category**: this table is *per-kind and per-platform*. What is platform-
independent is the verdict; what is **not** is which kind takes which route, and it was measured
on one interpreter and one OS (named in the output above, per the same rule the `ENXIO` timing
measurement below follows). No test asserts an errno or a route, and none should — the contract is
the verdict — so a platform whose `open` accepts a directory would still refuse it at `fstat` and
still print the same line, with only this table wrong. `test_stream_path_char_device_refuses` makes
`/dev/null` the `--stdout` — a character device that `os.open(O_WRONLY | O_APPEND | O_NONBLOCK)`
opens successfully, so the `fstat` check is actually reached — and asserts the refusal and that
the block ran nothing; it kills `nonregular-stream-accepted` (the `S_ISREG` check removed).
`test_stream_path_fifo_without_reader_refuses_bounded` makes an `os.mkfifo` path the `--stdout`
and asserts the refusal arrives within a second and the block ran nothing; a reader-less FIFO
fails at the `open` itself with `ENXIO` under `O_NONBLOCK` (measured), so it never reaches the
`fstat` check and cannot kill the `S_ISREG` mutant (design audit v73 agy) — what it kills is
`stream-open-blocking` (`O_NONBLOCK` dropped, caught by timing out its own bounded wait); on `FileNotFoundError` there (the file vanished between the two opens) go back
to the exclusive-create arm. Because the second arm can never create, every file this call
creates is created by the exclusive arm and recorded as such — a plain retry with `O_CREAT`
would create a fresh file and mis-record it as pre-existing, which is exactly what a later refusal
must not leave behind. The loop is bounded (three round trips, then `StreamPathUnwritable`), and
`O_NOFOLLOW` is not used: a symlinked artifact path is legitimate and the alias check below judges
what it resolves to. The descriptor is wrapped with `os.fdopen(fd, "a", encoding="utf-8")`. If the second reservation fails, the first
handle is closed and — only if `O_EXCL` succeeded for it — unlinked, so a pre-existing artifact
keeps every byte, a refusal leaves no new empty file, and there is no window in which another
process's file could be mistaken for one this call created. **The rollback is verified, not
assumed** (impl-plan audit v15): the reservation tracks `created` per arm and the rollback runs in
its own `finally`-shaped step — close first, then unlink iff created, each guarded so a failure of
one does not skip the other — and is followed by a read-back, `os.path.lexists(created_path)`;
if the file this call created is still there, the same `stream_path_unwritable` verdict carries a
`leftover: "<path>"` detail line, so the no-new-artifact guarantee is either true or reported as
broken, never silently assumed. **Concurrent replacement of the caller's own artifact path is
outside the threat model** (design audit v76): the two stream paths are the caller's scratch
paths — the same trust AC-3.9's check-to-open note already assumes — and no seam can interpose
between two syscalls of one call. The rollback still refuses to delete what it did not create:
before the unlink it compares `os.lstat(path)`'s `(st_dev, st_ino)` with the reserved
descriptor's `fstat` identity recorded at creation and, on a mismatch, skips the unlink and
reports the path as `leftover:` (someone else's file stands there now; the inode this call
created is already gone or renamed away). That identity check is a policy constraint rather than
a mutation-backed guard: its mismatch branch cannot be reached by a test without an additional
seam between the two arms, and adding one for a stated non-goal is not warranted. `test_rollback_unlink_failure_reports_leftover` gives `--stdout`
a fresh path and `--stderr` a path under a regular file (the real `ENOTDIR`), patches `os.unlink`
in the helper's namespace to raise `PermissionError` (the `os.unlink` fault injection, §Test
Strategy), and
asserts `UNREADABLE reason=stream_path_unwritable`, exit 2, a `leftover:` line naming the stdout
path, that file present and empty, and no traceback; mutation `rollback-leftover-unreported`
(the read-back removed, so the verdict never carries `leftover:`) is killed by it. The truncation is the final write itself:
on the `RAN` path, after cleanup succeeded, each held handle gets `seek(0); truncate(); write(…);
flush(); close()` — all five inside `_final_write`, **with the `close()` in a `finally`**: if
`seek`, `truncate`, `write` or `flush` raises, the handle is still closed before the exception is
mapped, and an error from that close is caught in the same region and mapped too (the first error
wins, the close error is chained as `__context__`), so no descriptor and no traceback can escape
past `stream_write_failed` — `main`'s outer `finally` is a backstop for the alias-refusal and
timeout paths, never the mapping for a write failure. Two tests pin this, and neither can be
satisfied by the outer `finally` closing the handle later. Both go through the **`_final_write`
fault injection** (§Test Strategy) and add no new seam: the patched seam calls the real
`_final_write` with a recording proxy around the held handle (every attribute forwarded, only
`flush`/`close` overridden as the test directs, `close` marking the proxy closed and recording
the call), so `main`'s outer `finally` still closes the *real* handle and never sees the proxy.
`test_final_write_close_failure_is_mapped` makes the proxy's `close` alone raise `OSError`
(`flush` succeeds) and asserts `main` returns 2, the verdict is `stream_write_failed` with
`failed: "stdout"`, and no traceback reaches stderr — a `close()` outside the mapped region lets
that error escape as a traceback. `test_final_write_failure_before_close_still_closes` makes
**both** the proxy's `flush` and `close` raise and asserts the same verdict, no traceback, and
that the proxy's `close` **was called** — which only `_final_write`'s own `finally` can do,
because the outer `finally` holds the real handle. A `close()` moved out of the `finally` skips
the close when `flush` raises: the verdict still maps, the outer `finally` closes the real
handle, and the proxy's `close` is never called, so the assertion fails. Both tests are the kill
for mutation `final-write-close-not-in-finally`; Phase 5e runs that mutant and records its RED
in the mutation spec. It is all inside `_final_write` because a buffered `TextIOWrapper` may defer
the OS write (and even the truncate) until `flush()` or `close()`, and an `OSError` surfacing at a
close *outside* the mapped region would escape as a traceback instead of `stream_write_failed` —
so an existing artifact is overwritten, never appended. **The write is then verified, not
trusted, per stream and before the next stream is written**: immediately after a stream's
`_final_write` returns — and before stderr's write is attempted — `main` re-reads that artifact
(`Path(path).read_bytes()`) and compares those bytes to the exact bytes it wrote,
`text.encode("utf-8", errors="replace")` — byte-for-byte, never a decoded `str` comparison, so a
changed or malformed byte is a mismatch rather than a `UnicodeDecodeError` escaping the mapped
region; a missing file, an `OSError` on the read, or a mismatch is `StreamWriteFailed` with
`verify: "<stream>"` in its detail, so a writer that silently
did nothing — or an artifact that vanished between close and verdict — can never be reported as
`RAN` (the base mutation-verification rule, applied to the helper's own output; mutation
`final-write-not-verified`). Because verification is per stream, a stdout verification failure
takes the first-stream rule below exactly as a stdout write failure does: `failed: "stdout"` /
`skipped: "stderr"`, and the stderr artifact keeps its previous bytes untouched —
`test_final_write_readback_catches_a_silent_no_op` asserts both detail lines and the untouched
stderr bytes; mutation `verify-deferred-past-second-write` (both writes run, then both
verifications) writes stderr before stdout's silent no-op is diagnosed and is killed by that
assertion. On `TIMEOUT` or `CLEANUP_FAILED` nothing is
written to either handle and pre-existing artifacts are untouched. A failure *in* that final write
can therefore only be an error on an open descriptor (disk full, I/O error) and maps to
`StreamWriteFailed` → `UNREADABLE reason=stream_write_failed`, exit 2; the `rc` is not reported,
because the artifact the caller was promised does not exist. **The writes are ordered and the
partial state is reported, not rolled back**: stdout is written first, then stderr; if the second
fails, the first stays as written (its old contents were truncated in place, so there is nothing
to restore) and the detail lines read `written: "stdout"` / `failed: "stderr"`; **if the first
(stdout) fails, the second is not attempted** — its artifact keeps its previous contents, since
nothing has touched it — and the detail lines read `failed: "stdout"` / `skipped: "stderr"`. All
three detail keys (`written:`, `failed:`, `skipped:`) have registry rows (AC-4.5), and each branch
has its test (`test_first_stream_write_failure_skips_the_second`,
`test_second_stream_write_failure_leaves_the_first_as_written`). **Both writes go
through one module function, `_final_write(handle, text)`** — the seam the AC-3.8 tests
fault-inject, since no real mechanism makes a held descriptor fail deterministically on macOS
(no `/dev/full`). **Every held handle has exactly one closure primitive, `_close_stream(handle)`**, called by
`_final_write`'s `finally` and by `main`'s backstop alike: `main` holds the two
reservations in a `try`/`finally` that spans the alias check, `run_block` and the final writes,
and the `finally` closes, through `_close_stream`, any handle `_final_write` has not already closed
(closing an already-closed handle is a no-op). **The backstop never raises from the `finally`**: each
close runs under `except OSError`, the first close error is recorded as `close_error` together with
the stream name, and — exactly as `run_block` selects after its own `try`/`finally` — `main` selects
the outcome after the block has completed. **Precedence, the same rule as cleanup: an operational
error outranks a verdict, and the first operational error wins.** If a `close_error` was recorded
and the pending outcome is a `BlockTimeout` (exit 0) — or there is no pending exception at all —
`StreamCloseFailed(stream, close_error)` is raised `from` the pending outcome and printed as
`DOCBLOCK: UNREADABLE reason=stream_close_failed` + `stream: "<name>"` + `os_error: "<text>"`, exit 2; if the pending
outcome is already an exit-2 `DocBlockError` (`CleanupFailed`, `LaunchFailed`, `StreamPathsAlias`,
`StreamWriteFailed`), that error is raised unchanged and the close error is attached as its
`__context__`. (On the `RAN` path `_final_write` has closed both handles inside its own mapped
region, so the backstop is a no-op there.) Two tests, both through the `_close_stream` seam (named in
Test Strategy, never numbered): `test_backstop_close_failure_on_timeout_is_mapped` patches
`_close_stream` to raise `OSError` under `sleep 300` / `timeout=1` with `--stdout` given and asserts
`UNREADABLE reason=stream_close_failed`, exit 2, the `os_error:` line, no traceback and the cwd gone
(mutation `backstop-close-unmapped`: the `except OSError` around the backstop removed, so the
timeout run prints a traceback); `test_backstop_close_failure_does_not_outrank_a_refusal` patches
the same seam under an aliased `--stdout`/`--stderr` pair and asserts the verdict is still
`stream_paths_alias`, exit 2, no traceback (mutation `backstop-close-outranks-error`: the
selection prefers the close error over a pending exit-2 error). **This closes the class, with the
residual stated:** every OS call `main` makes on its own behalf falls in exactly one of three
mapped regions — reservation (`os.open`, `fstat`, rollback close/unlink → `stream_path_unwritable`),
final write (`seek`/`truncate`/`write`/`flush`/`close`/read-back → `stream_write_failed`), and
backstop close (→ `stream_close_failed`, or chained under the pending exit-2 error); the calls
`run_block` makes are AC-4.6's (`mkdtemp`/`chmod`/`Popen`/`killpg`/`rmtree`), and nothing else in
`main` touches the OS. So `TIMEOUT`, `CLEANUP_FAILED`, `LAUNCH_FAILED`, an alias
refusal, and an exception inside the first `_final_write` all release both descriptors before
`main` returns — a repeated CLI use in one process cannot leak descriptors and turn a later
reservation into `stream_path_unwritable`. `test_stream_handles_are_closed_on_every_path` drives
`TIMEOUT` and the first-write failure and asserts both descriptors are closed (via the recording
`os.open` count and `fstat` raising `OSError` on the closed fds). **Aliasing is judged on the opened
descriptors** (AC-3.9): once both handles are held, `os.fstat` on each gives `(st_dev, st_ino)`,
and equality is `StreamPathsAlias` — a symlink, a `./x`/`x` spelling and a **hard link** all
collapse to one inode, and because the comparison is on the descriptors there is no
check-to-open window in which two distinct strings can come to name one file. The refusal unlinks a
file this call created (an `OSError` there maps to `stream_path_unwritable`, the region's verdict)
and raises `StreamPathsAlias`; **it does not close the handles itself** — closing is the backstop
`finally`'s job through `_close_stream`, which is what lets
`test_backstop_close_failure_does_not_outrank_a_refusal` inject a failing close and still see
`stream_paths_alias` (a close inside the reservation region would map that injected error to
`stream_path_unwritable` instead). Nothing has been written. (A string-level pre-check is
therefore not needed and is not performed; the earlier resolved-path comparison was both weaker
and racy.)

Verdict lines, one per run. **Every dynamic field is rendered through one escaper, `_field(value)`**
(design audit v67): `heading="<h>"`, `arg="<raw>"`, `missing_key: "<k>"`, `duplicate_key: "<k>"`,
`overlap: …`, `os_error: "<text>"`, `path="<p>"`, `leftover: "<path>"`, `stream: "<name>"`, `value="<v>"`
and every other caller- or document-controlled value pass through it, and it renders the value as
a **double-quoted JSON string** — `json.dumps(str(value), ensure_ascii=False)`, the value stringified FIRST so an `int`/`float` is quoted too (`json.dumps(3)` alone would emit a bare `3` — design audit v72 agy), **followed by a second pass** that rewrites every remaining character of Unicode category `Cc`, `Zl` or `Zp` to its `\uXXXX` escape — `json.dumps` escapes only C0 controls, and leaves DEL, the C1 range (U+0085 NEL included) and U+2028/U+2029 literal, every one of which `str.splitlines()` treats as a line boundary (measured: a heading carrying NEL, LS, PS and DEL splits into four lines after `json.dumps` alone — design audit v73): `"` and `\` escaped,
`\r`, `\n` and every other control character escaped, everything else (spaces, `=`, non-ASCII)
verbatim inside the quotes — so no argument, key, heading or path can start a second line **or
forge a field token inside the line**: a `--heading` of `"x\nDOCBLOCK: RAN rc=0 blocks=1 shell=strict"`
yields exactly one `DOCBLOCK:` line, the `NOT_FOUND` one, with the newline visible as `\n`
inside `heading="…"`, and a `--heading` of `x rc=0` yields `heading="x rc=0"`, one quoted
value, never a bare ` rc=0` token on a refusal line (plan audit v61: AC-4.3 promises no
cannot-judge line carries `rc=`, and control-character escaping alone left that forgeable).
Helper-constrained fields — `rc=<n>`, `blocks=<n>`, `count=<n>`, `keys=<n>`, `shell=`,
`stage=`, `reason=` — are ints or enums the helper produces and stay bare; **that list is
exhaustive**: every other field is quoted, including the helper-produced numbers `seconds=` and
`pgid:` (`seconds="1.0"`, `pgid: "4242"` — quoting a number never enables a forgery and the
grammar parses it either way; impl-plan v1.22), so the line grammar is
`DOCBLOCK: <VERDICT> (<key>=<bare>|<key>="<json-string>")*` and a consumer that splits on the
quoted-string grammar recovers every field. The rule is what keeps the one-line, one-token-per-field
contract true for a machine consumer; `_field` is the only place a dynamic value is rendered.
`test_dynamic_field_cannot_forge_a_token` drives `--heading 'x rc=0'` in-process and asserts the
`NOT_FOUND` line parses under that grammar to exactly `heading` (`== "x rc=0"`) with no `rc`
field; mutation `field-quoting-removed` (`_field` escapes control characters but emits the value
bare, so the parse yields an `rc` field) is killed by it.
`test_unicode_line_separators_cannot_split_a_verdict_line` drives a `--heading` carrying U+0085,
U+2028, U+2029 and DEL and asserts `capsys` stdout `.splitlines()` has exactly one line, starting
with `DOCBLOCK:`, with the four visible as `\u0085`, `\u2028`, `\u2029`, `\u007f` inside
`heading="…"`; mutation `c1-escape-removed` (the second pass removed, so `json.dumps` alone
renders and NEL stays literal) is killed by it. `test_newline_in_dynamic_fields_cannot_forge_a_verdict_line`
drives the CLI in-process with a newline-bearing `--heading`, a `--subst` key and value carrying
`\n`, and — for the `leftover:` slot — a `--stdout` path with `\n` in its file name that the first
arm creates (a fresh path under `tmp_path`; a newline is a legal POSIX file-name byte), with
`--stderr` under a regular file so the second arm fails and `os.unlink` injected as AC-3.10's
test does, so the `stream_path_unwritable` verdict carries `leftover:` with the escaped name
(impl-plan audit v19: a first-arm `ENOTDIR` path creates nothing and has no leftover to report),
each on its own refusal path (`NOT_FOUND`, `SUBST_MISSING`/`BAD_SUBST`,
`stream_path_unwritable` with `leftover:`), and asserts that
`capsys` stdout holds exactly one line starting with `DOCBLOCK:`, that no line equals the forged
`RAN` line, and that the escaped payload appears; mutation `field-escape-removed` (`_field`
returns its input unchanged) is killed by it.

| line | exit | when |
|---|---|---|
| `DOCBLOCK: RAN rc=<n> blocks=1 shell=<strict\|plain>` | 0 | the block ran (any `rc`) |
| `DOCBLOCK: NOT_FOUND heading="<h>"` | 0 | no tagged block, or `--index` past the end |
| `DOCBLOCK: AMBIGUOUS blocks=<n> heading="<h>"` | 0 | >1 tagged block, no `--index` |
| `DOCBLOCK: AMBIGUOUS_HEADING count=<n> heading="<h>"` | 0 | >1 heading matches text+level |
| `DOCBLOCK: BAD_INDEX index="<n>"` | 0 | `--index` below 1, or not an integer |
| `DOCBLOCK: BAD_TIMEOUT value="<v>"` | 0 | `--shell-timeout` non-numeric, non-finite, or not > 0 |
| `DOCBLOCK: BAD_ARGS message="<m>"` | 0 | argparse grammar: an unknown option or a missing option value (the parser's `error()` is routed here; `--help` alone still prints help, exit 0) |
| `DOCBLOCK: BAD_SUBST arg="<raw>"` (+ `duplicate_key: "<k>"`) | 0 | a `--subst` value with no `=` or an empty key, or a key given twice |
| `DOCBLOCK: SUBST_MISSING keys=<n>` + `missing_key: "<k>"` per key, map insertion order | 0 | one or more keys are absent from the block (`n` counts them, so the line never has to pick one) |
| `DOCBLOCK: SUBST_OVERLAP keys=<n>` + `overlap: "<a>" "<b>"` per pair | 0 | one key is a substring of another |
| `DOCBLOCK: UNREADABLE reason=stream_paths_alias` | 2 | `--stdout` and `--stderr` name one inode (`fstat` on the reserved handles) |
| `DOCBLOCK: UNREADABLE reason=preamble_unreadable` | 2 | `--preamble-file` cannot be read |
| `DOCBLOCK: BAD_INFO key="<k>"` | 0 | unrecognised info-string token |
| `DOCBLOCK: TIMEOUT seconds="<n>"` | 0 | the block outran its bound (either race in AC-5.5 included) |
| `DOCBLOCK: CLEANUP_FAILED path="<p>"` + `os_error: "<text>"` when `cleanup_error` is set | 2 | the temp cwd could not be removed, or was read back present |
| `DOCBLOCK: LAUNCH_FAILED stage=<s>` + `os_error: "<text>"` (+ `pgid: "<n>"` when `stage=reap` or `stage=collect`) | 2 | the helper's own `mkdtemp`/`Popen`/`killpg`, or its `communicate`/drain/pipe-close/`wait` on the child (`stage=collect`), raised — never a traceback |
| `DOCBLOCK: UNREADABLE reason=<r>` (+ `written:`/`failed:`/`skipped:` detail lines and `verify: "<stream>"` when the read-back disagreed, for `r=stream_write_failed`; + `stream: "<name>"` and `os_error: "<text>"` when `r=stream_close_failed`; + `leftover: "<path>"` when `r=stream_path_unwritable` and the rollback read-back found the file this call created still present) | 2 | `doc_unreadable`, `stream_path_unwritable`, `stream_write_failed`, `stream_close_failed` (a backstop close of a held handle failed on a path where the final write never ran; an exit-2 error already pending wins instead) |

The order in `main` is `extract` (which validates the info string and refuses a duplicate heading)
→ `select` (which validates the ordinal) → `--subst` syntax → `substitute` → the remaining
validations that belong to no earlier step (timeout, preamble readability) → reserve both stream
handles → alias check on the reserved descriptors (`os.fstat`, the only place it *can* happen) →
spawn. Nothing is reserved until every refusal that can be made from the inputs alone has been
made; the alias refusal is the one that needs the reservation, and it still precedes the spawn.

`RAN` is the only line carrying `rc=`; `AMBIGUOUS` is the only refusal carrying `blocks=`.
`blocks=<n>`, `count=<n>`, `index="<n>"`, `value="<v>"` and `seconds="<n>"` are diagnostic values
saying *why* the tool
declined or the block did not finish, which the count rule permits — a measured-result count
(`rc=`) is what it forbids. **The exit column follows the base Audit-gate signal discipline
invariant**: every verdict — `RAN`, every refusal of readable input, and `TIMEOUT` — exits 0, so no
refusal ever registers as a tool failure in the orchestrator's harness; exit 2 is reserved for the
three operational classes the invariant's non-zero rule covers: `UNREADABLE` (input that could not
be read, a path that could not be written or reserved, a write that failed), `CLEANUP_FAILED` and
`LAUNCH_FAILED`. AC-4.2 pins that
partition row by row, and the test that walks this table is what keeps the two from drifting.

## Error Handling Strategy

The API raises; the CLI returns codes. Every exception the module defines subclasses one base,
`DocBlockError`, and `main` maps the full set — **including the two IO-shaped ones the v1.0 draft
promised in its verdict table and then omitted here**, which would have let an unreadable document
or an unwritable stream path escape as a traceback rather than a token:

| exception | raised by | verdict line |
|---|---|---|
| `DocUnreadable` | `extract` (wraps `OSError` **and `UnicodeDecodeError`** — the document is read as strict UTF-8) | `UNREADABLE reason=doc_unreadable` |
| `BadInfoString(key)` | `extract` | `BAD_INFO key="<k>"` |
| `BlockNotFound` | `select` | `NOT_FOUND heading="<h>"` |
| `AmbiguousBlock(n)` | `select` | `AMBIGUOUS blocks=<n> heading="<h>"` |
| `AmbiguousHeading(n)` | `extract` | `AMBIGUOUS_HEADING count=<n> heading="<h>"` |
| `BadIndex(n)` | `select`, and `main` for a non-integer argument | `BAD_INDEX index="<n>"` |
| `BadTimeout(value)` | `run_block` before `Popen`, and `main` for a non-numeric argument | `BAD_TIMEOUT value="<v>"` |
| `BadArgs(message)` | `main`, from the parser's overridden `error()` (argparse's default `exit_on_error=True`) | `BAD_ARGS message="<m>"` |
| `BadSubstArg(raw, duplicate_key=None)` | `main`, building the map — split once on the first `=`; no `=`, an **empty key**, or a repeat refused there, `raw` being the argument exactly as given, so `--subst =V` prints `arg="=V"` under the quoted-field grammar (design audit v75: never a bare `arg="=V"`) — **and `substitute`, for an empty key reached by an API caller** (`BadSubstArg("")`, which `main` never reaches because it refused the raw argument first; design audit v69 agy: delegating the CLI's empty key to `substitute` would lose `raw` and print `arg=`). The same predicate in both places, each pinned by its own row: `empty-key-accepted-by-api` and `cli-empty-key-delegated` | `BAD_SUBST arg="<raw>"` + `duplicate_key: "<k>"` when it is a repeat |
| `MissingSubstitution(keys)` | `substitute` | `SUBST_MISSING keys=<n>` + a `missing_key:` detail line per key |
| `OverlappingSubstitution(pairs)` | `substitute` | `SUBST_OVERLAP keys=<n>` + a detail line per pair |
| `StreamPathUnwritable(leftover=None)` | `main`'s stream reservation — the two-arm `os.open` create-or-open loop itself (raised `from` the `OSError`, which is its `__cause__`; also its bounded-retry exhaustion, with no cause); `leftover` set when the rollback read-back finds the created file still present; constructible with no arguments — the reservation region raises it bare, `from` the `OSError` (AC-4.5's subclass walk checks table membership by class and instantiates nothing; other subclasses keep their required arguments — design audit v72 agy) | `UNREADABLE reason=stream_path_unwritable` (+ `leftover: "<path>"` when set) |
| `StreamPathsAlias` | `main`, after reserving both handles — `os.fstat` `(st_dev, st_ino)` equal | `UNREADABLE reason=stream_paths_alias` |
| `PreambleUnreadable` | `main`'s pre-spawn read of `--preamble-file` (wraps `OSError` **and `UnicodeDecodeError`** — strict UTF-8, because text that will be executed is never silently repaired) | `UNREADABLE reason=preamble_unreadable` |
| `StreamWriteFailed(written, failed, skipped, verify=None)` | `main`, writing a stream to its held handle after the run, or verifying it by read-back | `UNREADABLE reason=stream_write_failed` + `written:`/`failed:`/`skipped:` detail lines from its fields, and `verify: "<stream>"` when the read-back disagreed |
| `StreamCloseFailed(stream, close_error)` | `main`, selected after its reservation `try`/`finally` when the backstop `_close_stream` raised and no exit-2 error was pending (a pending `BlockTimeout` becomes `__cause__`) | `UNREADABLE reason=stream_close_failed` + `stream: "<name>"` + `os_error: "<text>"` |
| `BlockTimeout(seconds)` | `run_block` (both AC-5.5 races end here) | `TIMEOUT seconds="<n>"` |
| `CleanupFailed(path, cleanup_error)` | `run_block`, after the `finally` read-back | `CLEANUP_FAILED path="<p>"` + `os_error: "<text>"` when `cleanup_error` is set |
| `LaunchFailed(stage, err, pgid=None)` | `run_block` — `mkdtemp`, `Popen`, a non-`ESRCH` `killpg` error, or an `OSError` from `communicate`/the drain/pipe close/`wait` (`collect`), wrapped; `pgid` set on the `reap` and `collect` stages | `LAUNCH_FAILED stage=<mkdtemp\|spawn\|reap\|collect>` + `os_error: "<text>"` (+ `pgid: "<n>"` on `reap` and `collect`) |

`main` catches `DocBlockError` and dispatches on type, so adding an exception without a verdict
line is a `KeyError` in the mapping table rather than a silent traceback — and a test asserts every
`DocBlockError` subclass appears in the table (which is also half of AC-4.5's bidirectional pin).

Nothing is logged; the verdict line and the streams are the whole output contract. A non-zero block
`rc` is **not** an error — it is the measurement.

## Test Strategy

Unit tests only, at the module boundary; no mocking of `subprocess`, because the behaviours under
test (strict vs plain, `-u`, `pipefail`, process-group reaping) are precisely what a mock would
stub out.

**Each seam is named, never numbered — here, and everywhere else in this document that refers to
one.** The eight are a *set*: the ordinal of any member changes whenever the set is reordered,
and the two enumerations in this section alone (this paragraph's and the `main(argv)` sentence
that closes it) list the same eight in different orders, so no ordinal over them is stable. That
is not hypothetical — every ordinal this rule has removed named the wrong seam as well as a
drifting one. The rule is stated ahead of both enumerations because it governs every seam
mentioned below *and* every seam mentioned in §Error Handling Strategy above.

**The rule over the axis, stated so a reader can apply it without asking**: no member of the
eight-seam set is *addressed* by ordinal anywhere in this document outside §Version History —
the seam is named instead. Verify that rather than trusting it, with the same corpus split the
line-pin check uses.

**Two properties of this file decide how such a check has to be built, and both were learnt by a
published check missing a real member** (design audit v87). (i) `grep` is line-scoped and this
document hard-wraps at ~95 columns, so **any** check whose target is a multi-*word* phrase is
blind to an instance the wrapper split — a real instance existed at `74e126f`, where a bolded
ordinal-plus-noun straddled a newline and the then-published line-scoped form scored it `0`.
**Fold paragraphs before matching.** (ii) Once folded, the check would match its own pattern
literal inside the fences below, so **exclude fenced code before folding** — and the excluder must
compare fence *run lengths*, because the pattern literal here lives in a fence that itself quotes
a shorter fence. The rule generalises past this one check: *a published detector in this document
whose target can contain a space folds first and strips fences first; a detector whose target is a
single whitespace-free token need not, because a hard-wrapper cannot split one.*

```bash
D=docs/02-design/features/doc-block-exec.design.md
O='(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|last|final|penultimate)'
N='(seams?|injections?|primitives?)'   # the plural is a sibling of the alternation, not a fourth rule
G='([^.]|\.[^ ]){0,60}'   # a dot INSIDE a token is inside the reach; a sentence break ends it
STRIP='match($0, /^ {0,3}(`{3,}|~{3,})/) {
         m = substr($0, RSTART, RLENGTH); sub(/^ +/, "", m)   # drop the indent before comparing runs
         if (f == "") { f = m }
         else if (substr(m,1,1) == substr(f,1,1) && length(m) >= length(f)) { f = "" }
         next }
       f == "" { print }'
FOLD='BEGIN { RS = "" } { gsub(/\n/, " "); print }'
awk '/^## Version History$/{v=1} !v' "$D" | awk "$STRIP" | awk "$FOLD" \
  | grep -oE "\b$O\b$G\b$N\b|\b$N\b$G\b$O\b" | wc -l | tr -d ' '   # expect 0
```

`grep -o … | wc -l` and not `grep -c`, because after the fold a paragraph is one line and two
addresses in one paragraph would count as one. `tr -d ' '` because BSD `wc` right-pads.

**`$STRIP` carries the same `^ {0,3}` fence bound as the Setext census's `FENCE`, and therefore
the same residual — this document has exactly two members of that class and the bound is named at
both.** A fence opened at four or more columns (inside a list item) is invisible to `$STRIP`, so
its body would survive the strip, be folded, and be matched as prose — the mirror of arm (2) on
`census()`. Measured rather than argued, on this document's head and on the whole file:
`grep -cE '^ {4,}(\`{3,}|~{3,})' "$D"` returns `0` at `6f0ee85` and `0` on the working file this
revision ships, **the second run made after the v1.103 entry**, so the bound is **unexercised here** — *vacuous* in the absence rule's vocabulary,
and one of the nine sites that rule counts — and, unlike `census()`'s arm (2), which is
exercised four times on the corpus it reads, this one is a `0` because the shape is absent, not
because two other guards happen to decline it. It goes live the first time this document indents
a fence, which is why the bound is stated rather than left to be rediscovered.

**`$STRIP`'s `~{3,}` alternative is moved by a control of its own, and is not carried by its
backtick sibling.** The census harness in §Scanning runs both its arms with tilde fences, but its
fence regexes are `SHIPPED` and `ANYIND`; it never reaches this `awk`, so v1.100's sentence naming
all three as controlled was a claim about a branch nothing had touched. Two one-line fixtures, run
through the shipped pipeline and through two mutations of it — `$STRIP` deleted, and `$TILDELESS`,
which is `$STRIP` with the tilde alternative removed and nothing else changed:

````bash
# $STRIP, $FOLD, $O, $G and $N as assigned in the seam-ordinal fence above, unedited.
# Writes only under /tmp, so this fence is runnable under a read-only audit contract.
TILDELESS='match($0, /^ {0,3}(`{3,})/) {
             m = substr($0, RSTART, RLENGTH); sub(/^ +/, "", m)
             if (f == "") { f = m }
             else if (substr(m,1,1) == substr(f,1,1) && length(m) >= length(f)) { f = "" }
             next }
           f == "" { print }'
score () { awk '/^## Version History$/{v=1} !v' "$1" | awk "$2" | awk "$FOLD" \
             | grep -oE "\b$O\b$G\b$N\b|\b$N\b$G\b$O\b" | wc -l | tr -d ' '; }
bare  () { awk '/^## Version History$/{v=1} !v' "$1" | awk "$FOLD" \
             | grep -oE "\b$O\b$G\b$N\b|\b$N\b$G\b$O\b" | wc -l | tr -d ' '; }
printf '~~~\nthe third seam\n~~~\n' > /tmp/tilde.md      # the fixture text is inside the printf,
printf '```\nthe third seam\n```\n' > /tmp/tick.md       # so this document grows no fence line
for f in /tmp/tilde.md /tmp/tick.md; do
  printf '%s shipped %s no-STRIP %s TILDELESS %s\n' \
    "$f" "$(score $f "$STRIP")" "$(bare $f)" "$(score $f "$TILDELESS")"; done
````

On awk version 20200816 / darwin 25.6.0 it prints
`/tmp/tilde.md shipped 0 no-STRIP 1 TILDELESS 1` and
`/tmp/tick.md shipped 0 no-STRIP 1 TILDELESS 0`. **The two rows discriminate each other, which is
what makes this a control on the tilde alternative rather than on the pipeline**: deleting
`$STRIP` moves *both* fixtures, so the strip stage is live for either character; deleting *only*
the tilde alternative moves the tilde fixture and leaves the backtick fixture at `0`, so the
movement belongs to `~{3,}` and cannot be its sibling's. No corpus can supply this —
`grep -cE '^ {0,3}~{3,}' "$D"` returns **0** on the working file this revision ships, **run after
the v1.103 entry below was written**, which is the second half of the stamping rule the
fourth-blind-form fence states and which this site carried only half of until v1.102: a
document-self figure names the working file *and* the entry it was run after, because the working
file is a moving object and the entry is what pins which version of it was measured. It is an
absence claim and *vacuous* — so a fixture is the only thing that will ever move this branch, which is
precisely the case decision O is about.

**Three controls, run before the `0` was published, because a `0` from a screen that has never
printed anything is not evidence.** *Positive*: the same pipeline over the v1.95 blob
(`git show 74e126f:$D > /tmp/v195.md`, then the pipeline with `D=/tmp/v195.md`) prints `4` — the
four ordinal-plus-noun instances that revision carried (two of them addresses, two of them
cardinality phrasings; v1.96 removed all four), including the one the wrapper had split — where
the line-scoped predecessor printed `3` on the same bytes. That gap **is** property (i), measured
on this file rather than argued. *Positive, per branch of `$N`, because a control over an
alternation tests the alternation and a healthy sibling covers a sick one*: over that same blob
the six morphological branches score `seam` `4`, `injection` `1`, and `seams`, `injections`,
`primitive`, `primitives` `0` each — so the whole `4` is one branch's, and the `s?` widening v1.99
added moved nothing anywhere in this document's own evidence. Against a one-line fixture written
for each branch (`the third <noun>`), all six score `1`, so every branch is live and the four
zeros record the corpus rather than a dead pattern. *Positive, for
the dotted form*: over a two-line fixture in which an ordinal is separated from its noun by a
backticked dotted module path *and* a newline, the pipeline prints `1`; the predecessor's
`[^.]{0,60}` gap printed `0`, and **five** of the eight seams are dotted module paths, so that was
the natural phrasing for this very set. That five is **derived here, not quoted** — fold the
document, pull the parenthesised enumeration §Test Strategy calls the canonical taxonomy, and
count the members carrying a dot:

```bash
awk 'BEGIN { RS = "" } { gsub(/\n/, " "); print }' "$D" \
  | grep -oE 'seven module-level seams \(`[^)]*`\)' | grep -oE '`[^`]+`' | tr -d '`' \
  | tee /dev/stderr | grep -c '\.'
```

At `6f0ee85` it lists the seven module-level seams and then prints `5`: `os.killpg`,
`shutil.rmtree`, `tempfile.mkdtemp`, `os.chmod` and `os.unlink` are dotted, `_final_write` and
`_close_stream` are not, and the remaining member of the eight — the instance-level `Popen`
wrapper — is not a module path at all. Most of the set is still dotted, so the blindness this
control demonstrates is unchanged; only the figure moves.

**v1.97 published `seven` at this site, taken verbatim from the audit report that raised the
finding, in the same revision whose Version History entry says no figure was carried.** The rule
over that axis: **a number that appears in an audit report is not a measurement until this
document re-derives it.** A report is a prompt to measure, never a source — it is written by a
reader of this document, so a figure quoted back out of it is this document's own claim returned
unchecked. The screen is mechanical: tokenise a revision's added lines and the report it answers,
then print every run of six or more consecutive tokens the two share.

```bash
# $D this document; $R the report the revision answers, read at $RSHA; $BASE..$HEAD its own diff.
# Both sides are read as committed BLOBS: git diff reads two trees and $R comes through git show.
# That property is not asserted here -- it is falsified-and-survived immediately below the output.
python3.11 - "$D" "$R" "$BASE" "$HEAD" "$RSHA" <<'PY'
import re, subprocess, sys
doc, rep, base, head, repsha = sys.argv[1:6]
tok = lambda s: re.findall(r"[a-z0-9][a-z0-9./_-]*", re.sub(r"[`*_]", "", s.lower()))
sh = lambda c: subprocess.run(c, shell=True, capture_output=True, text=True).stdout
raw = sh(f"git diff {base} {head} -- {doc} | grep '^+' | cut -c2-").splitlines()
seen = tok(sh(f"git show {repsha}:{rep}"))
grams = {tuple(seen[i:i + 6]) for i in range(len(seen) - 5)}
WORDS = "one two three four five six seven eight nine ten eleven twelve thirteen twenty thirty"
NUM = re.compile(r"^([0-9]+|%s)$" % "|".join(WORDS.split()))
ENTRY = re.compile(r"- v1\.[0-9]")   # an entry is one unwrapped line, so the split is per-line
def runs_of(lines):
    add, out, i = tok("\n".join(lines)), [], 0
    while i < len(add) - 5:
        if tuple(add[i:i + 6]) in grams:
            j = i
            while j < len(add) - 5 and tuple(add[j:j + 6]) in grams: j += 1
            out.append(add[i:j + 5]); i = j + 5
        else:
            i += 1
    return out
for label, keep in (("BODY", False), ("VERSION HISTORY", True)):
    rs = runs_of([l for l in raw if bool(ENTRY.match(l)) is keep])
    fig = [r for r in rs if any(NUM.match(t) for t in r)]
    print(f"{label}: {len(rs)} runs, {len(fig)} of them figure-bearing")
    # add `for r in rs: print(" *", " ".join(r))` to read the run texts, deliberately unpublished
PY
```

Run for the revision that introduced the defect — `D` this file,
`R=docs/02-design/features/doc-block-exec.design.audit.v87.teammate.md` (the v87 teammate report,
named by path so these figures are re-derivable without guessing which report was meant),
`RSHA=cf3a862`, `BASE=35698f9`, `HEAD=6f0ee85` — it prints

```
BODY: 8 runs, 3 of them figure-bearing
VERSION HISTORY: 15 runs, 8 of them figure-bearing
```

— 23 runs in total, **and the partition is computed inside the fence rather than read off by
hand, because the two sides are not the same kind of object**. A VERSION HISTORY run is a
*transcription*: an entry is supposed to quote the command, the sha pair, the fixture and the
finding it answers word for word, so a run there is evidence the entry did its job. A BODY run is
a *candidate this paragraph has to dispose of by name*: the body is this document speaking in its
own voice, and a phrase it shares with its reviewer is a figure or a claim it may not have
re-derived. **v1.98 published the split as twenty-two transcriptions and one body carry, and that
was this screen's own output taken without running it** — the shipped screen prints the dottedness
clause **twice**, once on each side of the partition
(`git diff 35698f9 6f0ee85 -- $D | grep '^+' | grep -c 'of the eight seams are dotted'` → `2` —
the needle is cut short of the wrong figure on purpose, so that publishing the check does not put
that figure back into the body), so the
decomposition is 21 + 2, and a rationale about what an *entry* may transcribe never covered the 8
body runs at all. Correcting a count and leaving the categorisation uncomputed would have left the
next carried figure to land in the body and be cleared by a Version-History excuse.

**Why this screen may quote its own numbers — falsified, not argued.** Both inputs are committed
blobs: `git diff 35698f9 6f0ee85` reads two trees, and `$R` is read with `git show cf3a862:$R`
(the file was *added* at `6f0ee85`; `cf3a862` is a sha at which it is committed, which is the only
property this needs, and stating it that way removes the "committed *in*" reading). **v1.99 stated
that property and the shipped code did not have it.** `$R` came in through
`open(rep, encoding='utf-8', errors='replace')` — a working-tree read of a path, no `git show` —
four paragraphs above a command in this same document that stamps its siblings on purpose, which
makes it a slip rather than a convention. The output was right and the reason given for trusting
it was false; that is the worst shape a control can ship in, because an unexecuted property claim
reads exactly like a verified one. So the property is now established by **doing the thing it
claims immunity from**:

```bash
# $MB..$MH is the MUTATION RANGE and is a claim of its own -- see the two rows below.
# Run this in a scratch clone, never in the tree under audit: `>> "$R"` writes to a TRACKED
# file, which the read-only contract a reviewer of this document works under forbids.
#   git clone --local --shared <this repo> /tmp/dbe && git -C /tmp/dbe checkout 68a70d6
cp "$R" /tmp/R.bak                                    # dirty the working report on purpose
git diff $MB $MH -- "$D" | grep '^+' | cut -c2- | grep -v '^+*- v1\.[0-9]' >> "$R"
# re-run the fence above; then re-run it once more with the v1.99 line
#   seen = tok(open(rep, encoding='utf-8', errors='replace').read())
# put back, so the two forms are compared on the same dirty tree
cp /tmp/R.bak "$R"; git diff --quiet -- "$R" && echo RESTORED
```

**The mutation is itself a claim, and v1.100 got its own wrong.** v1.100 wrote *"this revision's
own added body lines"* and appended `35698f9..6f0ee85` — which are the **measured** revision's
lines, v1.96 → v1.97, the very range the screen runs over — while "this revision" then meant
v1.100, `4e4a00c..06ef40f`. The demonstration ran; it did not run on what its sentence said. Both
ranges are now run and both are published, each named by range rather than by a phrase that has
to be resolved:

| `$MB..$MH` | body lines appended | `open()` form (v1.99's) | `git show` form (shipped) |
|---|---|---|---|
| `35698f9..6f0ee85` — the **measured** revision's own added body lines | 229 | `BODY: 1 runs, 1 of them figure-bearing` / `VERSION HISTORY: 49 runs, 17 of them figure-bearing` | `8`/`3` and `15`/`8` |
| `4e4a00c..06ef40f` — **v1.100's** own added body lines, the range its prose named | 161 | `BODY: 13 runs, 7 of them figure-bearing` / `VERSION HISTORY: 15 runs, 8 of them figure-bearing` | `8`/`3` and `15`/`8` |

Reproduced in a `git clone --local --shared` of this repository checked out at `68a70d6`; on a
clean tree both forms print `8`/`3` and `15`/`8`, so the repair is output-preserving and the
figures published above are the same figures, not new ones. The restore was verified rather than
assumed: `git diff --quiet -- "$R"` exits `0` after each run. **The `4e4a00c..06ef40f` mutation is
the weaker demonstration and is published anyway**: it moves the body pair only and leaves the
Version-History pair standing, so on its own it is evidence about one partition; the
`35698f9..6f0ee85` mutation moves both, and a body figure that *falls* (the appended lines merge
the whole added body into
one contiguous run) is still a mutation, since a screen immune to it prints the same number in
either direction. **The revision being written can never be its own mutation range** — v1.101's
added lines are uncommitted while this paragraph is written, so a range naming them would not
resolve — which is the mechanical reason the phrase "this revision" failed here and the reason
both rows name committed shas. That immunity is not automatic and is
the general rule for anything this document ships as a control: **measure it over bytes the
revision cannot touch — an earlier blob or a fixture file — or the act of publishing the control
changes what it measures.** And the stronger rule this instance forces, which is the one that had
been missing: **a stated property of a screen — what it is immune to, which side it reads, which
of its branches ever fire, what its zero means — is a claim about the screen's shipped text. Read
it out of the fence and execute it. Never reason it from what the screen is for.** **And the
corollary this revision had to add, because v1.100 obeyed that rule and still shipped a false
sentence: when a property is established by executing a mutation, the mutation is a claim as
well. Name the exact range, blob or input the run consumed, and show it is the one the sentence
describes — in the text, a demonstration run on the wrong input is indistinguishable from one run
on the right input, and only the range makes them different.**

**Disposition of the 8 body runs — the partition is computed, the disposition is a reading, and
that is the residual here.** Two are commands; **three** are fixture descriptions, one of those
three being a fixture's own printed result; two are phrasings of a rule and of its residual; and
**one** is the dottedness
clause corrected at the head of this paragraph, which is deliberately not re-quoted: quoting a
wrong figure to report it puts the wrong figure back in the body. Of the 3 figure-bearing body
runs, that clause is one, a fixture result standing beside the command that produces it is
another, and the third is the word `one` used as a **pronoun** — a known over-match of `NUM`'s
word list. **The over-match is in the safe direction; the under-match is not, and "never hides
them" was a one-sided property this list does not have.** Measured against the shipped tokeniser
and regex rather than read off the word list: `fifteen runs`, `forty runs` and `ninety runs` are
all scored not-figure-bearing, and so is `twenty-two runs` — `-` is inside the token class, so
`twenty-two` is one token `NUM` never matches even though `twenty` is listed. The uncovered
members named exactly: **`zero`**, `fourteen` through `nineteen`, `forty` through `ninety`,
`hundred`, `thousand`, and **every** hyphenated compound. `zero` heads that list rather than
being left implicit inside it, because an absence claim *is* a figure and this document writes
more of those than of any other kind: through the same tokeniser and regex, `zero runs` gives
tokens `['zero', 'runs']` and scores not-figure-bearing.

**The gap is exercised once at the token level on the published input, and v1.101 published that
as `0` because it added `zero` to the name set in the same edit and did not re-run the grep
afterwards.** The operand is written out here rather than left to be reconstructed from the prose,
because the name set *is* the input this defect is about:

```bash
NS='zero|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand'
git diff 35698f9 6f0ee85 -- "$D" | grep '^+' | grep -cEi "$NS"                    # 1
git diff 35698f9 6f0ee85 -- "$D" | grep '^+' | grep -cEi "${NS#zero|}"            # 0, the control arm
```

The first returns **`1`** and the second **`0`**, so the one hit is `zero`'s and nothing else's;
that second `0` is the differential's **control arm**, not an absence claim about a corpus, and is
therefore not a site of the absence rule above. The alternation covers only the *word-list*
members of the hole — every hyphenated compound is outside it, is named in the prose above, and is
screened by nothing here. The hit is an added body line reading
`as prose, never hide a heading — and the corpus exercises it zero times. (2) It matches a fence`.

**The figures above nonetheless do not move, and the route is published rather than left to be
reconstructed, because a name-set hit and a figure-bearing run are different objects and only the
second one moves a number.** A token has to fall inside a run of six or more shared consecutive
tokens before `NUM` is ever consulted about it. Re-run the shipped screen with `zero` prepended to
its `WORDS` — extract the fence's program from this file rather than retyping it, then
`sed 's/^WORDS = "one /WORDS = "zero one /'` — and against the same
`R=…design.audit.v87.teammate.md`, `RSHA=cf3a862`, `BASE=35698f9`, `HEAD=6f0ee85` it prints
`BODY: 8 runs, 3 of them figure-bearing` and `VERSION HISTORY: 15 runs, 8 of them figure-bearing`,
identical to the shipped `WORDS`. That differential is the whole of the evidence claimed here: it
says the four published counts are unchanged, and it does **not** say where the token sits, which
is a mechanism claim this run does not measure and none is made. Both of the screen's inputs are
committed blobs — `git diff` reads two trees and `git show` reads the report — so the run is
invariant to the sha checked out, and re-running it at any later commit reproduces it.

**The rule over that axis**: when a revision edits the *input* to a claim — a name set, a needle,
a `WORDS` list, a corpus list — the claim is re-run **after** the edit lands, never restated from
the run that preceded it. A property claim and its input are one object, and editing either
without executing the pair is the same defect as never running it at all. **Residual, exactly**:
this rule is about a claim whose input changed inside the same revision; it does nothing for a
claim whose input a *later* revision changes, and the only screen for that is that every figure
here carries its command inline so a reader can re-run it. Note also that this figure has left the
absence class by becoming `1`, so it is not a site of the absence rule above and is not counted
in that denominator. The list remains a candidate raiser with a stated hole, not a screen.
The 8 figure-bearing Version-History runs were re-derived at `cf3a862` rather than taken on trust:
`git diff --name-only a8e0372 74e126f` names 18 files, 16 of them `.md`; `git diff --name-only
a8e0372 335f535` names 13 and 11; and exactly 3 files under the two roots **import**
`docsections` while 5 mention it, so `import` is the load-bearing unit and is the one stated. Two
of those runs pair 13/11 with `a8e0372..74e126f`, which is *not* a fourth figure to check: it is
v1.96's false claim, quoted once in that entry and a second time inside the bracket v1.97 appended
to correct it — the v1.49 shape, where a correction cannot avoid restating what it corrects.
**Residual, exactly**: this screen finds carried *text*. A figure retyped in
different words — the same number reached by paraphrase — passes it in silence, and the only
screen for that is a derivation command standing beside the figure, which is what this document
already requires of every measurement. The screen is also scoped to one report: a figure carried
from a *sibling document* is a decision-E matter and is not what this run measures. *True negative* — a **non-member the screen declines**,
not a member it fails to print: a fixture carrying both admissible cardinality phrasings and two
block ordinals with their base, in the shapes this document actually uses, prints `0`. A fourth
run pins property (ii): dropping `$STRIP` from the pipeline turns the `0` on this file into **`6`**
— on the working file this revision ships, after the v1.103 entry. **The literal `1` stood in this
sentence unchanged at every sha from `6f0ee85` to `7d8e797` and was true only at the first two of
them, and it is the first thing the rule stated at the `NUM` residual caught**: the figure is a
property of *this document's fence bodies*, so every
revision that adds a fixture moves it, and the three revisions that added fixtures each restated
the number instead of re-running it. Re-derived over the head at eight shas with the same
unstripped fold — `2` at `35698f9`, `1` at `6f0ee85` and at `cf3a862`, `2` at `7982c18` and at
`4e4a00c`, `3` at `06ef40f` and at `68a70d6`, `6` at `7d8e797` — so the drift is visible and dated
rather than asserted. **All six are fence text, and the disposition is what the control turns on,
not the count**: two are the `O` and `N` alternations assigned in the fence above, the check
matching its own source; two are the ordinal-plus-noun fixture bodies written into the `printf`s of
the `$STRIP` tilde control below; and two are the same shape in the opening line of the `$P` and
`$W` true-negative fixtures. Not one is a live ordinal address, which is the property the run exists to
establish, and the larger number makes the control *stronger* — `$STRIP` is now shown to suppress
six lines rather than one. (It was `2` at `35698f9`, when the alternation was written out twice —
`git show 35698f9:$D | grep -cF '(first|second|third'` returns `2` against `1` at `6f0ee85`, and
the unstripped fold over that blob returns `2`, so the figure is reproducible and not a drafting
note; hoisting the alternation into a shell variable is why **at that blob** one copy remains.
**That clause is dated and not present-tense, and the reason is the sharpest instance of a hazard
this document otherwise avoids: this is its one screen whose needle is a literal string that lives
inside the scope the screen counts, so every sentence written *about* the screen is a candidate
member of what it counts.** On the working file this revision ships, **after the v1.103 entry**,
that same `-F` grep — quoted exactly once above and deliberately not re-quoted here, since a
fourth literal copy would move the figure inside the sentence stating it — returns **3**
whole-file and **2** over the head: the `O` assignment, the probe quoting it, and — the third,
which is why the whole-file figure exceeds the head one — the **v1.98** entry, which quotes the
same command in the course of *rejecting* an audit finding on evidence, an entry read here rather
than inferred from where it sits. **The rule over that axis: no screen's needle may be written
literally anywhere in the scope that screen counts — a needle under discussion is described, never
reproduced — and where one already sits there, as here, the figure is *derived at each corpus* and
never carried.** It is given at two blobs and the working file above for exactly that reason.
**Residual, as a concrete category**: this covers needles that are literal strings. A screen whose
needle is a regex *class* can still be matched by prose that never contains the literal — the
seam-ordinal screen itself is one, which is why the sentences naming its six unstripped hits were
written without reproducing the ordinal-plus-noun shape — and no mechanical check separates that
prose from a real member; only the stripped run beside the unstripped one distinguishes them.
A reader who runs an unstripped fold
and reads the hit as a live ordinal would strike a correct detector.)

**Residual, exactly three items, all stated so the next author neither strikes a legitimate line
nor leaves a real one:**

1. **§Version History is exempt for ordinals as well as for line pins.** An ordinal there is a
   dated record of what *that revision claimed*, never a live address; v1.49's entry is the proof
   that the exemption cannot be avoided by striking, since it has to quote the ordinal it struck
   in order to record the strike at all — and so does every later entry that reports one. **How
   many entries carry one is therefore a derived number and is never written here as a list**,
   because it grows by one each time a revision records a strike. Count it with the same pattern
   over the *tail*, and **without the fold** — a Version History entry is one unwrapped line, so
   line-scope and entry-scope coincide there and folding would merge entries into one paragraph:

   ```bash
   # D, O, G and N as assigned in the fence above; this stage reuses them unchanged
   awk '/^## Version History$/{v=1} v' "$D" | grep -cE "\b$O\b$G\b$N\b|\b$N\b$G\b$O\b"
   ```

   Evaluated against the blob this revision edits — `git show 35698f9:$D` piped through the same
   two stages — it prints **8**, and that output is a *screen result, not a cardinality*. Seven
   of the eight are entries recording an ordinal over the fault-injection set. The remaining one,
   v1.76's, is an ordinal over the two *arms* of a cleanup path, which merely lands inside the
   gap of one of the three nouns. Named here so the next reader does not chase it, and kept as
   the demonstration of why this number is derived and never transcribed as a list. It is still
   `8` on the working file **after the v1.103 entry**, which records its changes without quoting an
   ordinal address — and the tail command was re-run on the working file *after* the bump rather
   than before it, which is the only order in which that check means anything. Naming the entry is
   the rule this document settled on for a document-self figure ("this revision" stops resolving
   from the bytes the moment a later entry exists); the command is still what carries the claim,
   and the version says only which bytes it was run over. It rises by one on the next entry that
   has to quote the ordinal it struck.
   **This site carried `v1.101` while the document shipped v1.102, and the axis behind that is
   the naming rule's own cost, stated here once rather than repaired member by member: a stamp
   that names an entry goes stale on the very next bump, so an entry bump is itself the trigger
   to re-run and re-stamp *every* document-self figure — the version is not decoration on the
   figure, it is the corpus identifier.** The v1.102 repair closed the class it could see and
   named a screen for the rest that grepped the phrase *working file*; that screen cannot reach a
   figure which names the working file correctly and an entry that has since been superseded,
   which is what this one was. The screen is therefore the entry-naming form itself, run over the
   head with every hit read against the version this document ships, and it needs a fold because
   the wrapper splits the phrase:

   ```bash
   awk '/^## Version History$/{exit} {print}' "$D" \
     | awk 'BEGIN { RS = "" } { gsub(/\n/, " "); print }' \
     | grep -oE 'after the v1\.[0-9]+ entry' | sort | uniq -c
   ```

   Every hit must name the current entry; any other version is a stale stamp by construction.
   The pattern is not self-matching — the escaped `v1\.` in the fence is not the literal
   `v1.` the pattern needs — so the screen does not count its own definition, and its scope is
   the head while its definition sits inside a fence the fold leaves in place, which is why that
   property is stated rather than assumed. **Residual, as a concrete category and not "and
   similar"**: this reaches a document-self figure that names an entry in that exact phrasing and
   nothing else. Two neighbours are out of its reach and are covered elsewhere: a figure naming
   the working file with **no** entry at all is the v1.102 screen's business (grep the phrase
   *working file*), and a figure naming **neither** — a number with no corpus behind it — is a
   decision-G absence-rule matter and is caught by the candidate sweep above, not here.
   (This narrows v1.95's blanket "the seam-naming rule is not exempt there", which was a rule that
   revision stated and did not apply — it struck one Version History ordinal and left the rest,
   and its own entry then quoted the ordinal it struck.) **The ordinal-*base* rule is a different
   axis, and it is not exempt here either — but it governs a narrower thing than the sentence
   above it, and that scope is now stated rather than left to be inferred.** The base rule exists
   because an ordinal that *indexes a span* is ambiguous by one between the 0-based and 1-based
   conventions, which is a live ambiguity this feature actually hit; so it binds every ordinal
   that picks a position out of an ordered span, everywhere in this document including here.
   The eight tail hits are not of that kind: they are word-ordinals over a **set** whose members
   are named and never numbered, so there is no index convention for them to name and no span for
   them to index — they are the seam-naming rule's business, and that rule is the one §Version
   History is exempt from. **The span-ordinal screen v1.99 shipped beside that sentence was one
   working branch away from useless, and is replaced here rather than reworded.** It read
   `\b(index|block|blocks)[ =]+[0-9]+|--index [0-9]+`; run branch by branch over the tail,
   `index` → `0`, `block` → `0`, `blocks` → `1`, `--index [0-9]+` → `0`, so three of its four
   branches had never fired and its entire output was the fourth (decision O). It was also a false
   negative on this document's own way of writing a span ordinal —
   `printf 'the gate block is **4**\n' | grep -cE '\b(index|block|blocks)[ =]+[0-9]+|--index [0-9]+'`
   returns `0`, and §Test Strategy writes exactly that shape — so an entry stating a span ordinal
   in the document's own idiom would have been invisible to it. The class is **a span ordinal
   written as a span noun beside a number, in any shape this document writes one** — bare
   (`blocks 7`), with a copula and emphasis (`block is **4**`), with an equals sign (`blocks=2`),
   or as a flag (`--index 0`) — **over a span noun that need not be one of three**:

   ```bash
   S='index|indices|block|blocks|row|rows|line|lines|entry|entries|element|elements|position|positions|column|columns'
   P="\b($S)\b( is| =|=|:)? *\**[0-9]+|--index +[0-9]+"
   TAIL () { awk '/^## Version History$/{v=1} v' "$1"; }
   HEAD () { awk '/^## Version History$/{exit} {print}' "$1"; }
   for n in $(echo "$S" | tr '|' ' '); do          # POSITIVE, one branch at a time
     printf '%s=%s ' "$n" "$(printf 'the %s is 3\n' "$n" | grep -cE "$P")"; done; echo
   printf 'run with --index 2\n' | grep -cE "$P"   # POSITIVE, the flag branch
   printf 'the second seam\nadd no new seam\n3 blocks were added\nfour rows\n' \
     | grep -cE "$P"                               # TRUE NEGATIVE: non-members it declines
   git show cf3a862:"$D" | HEAD /dev/stdin | grep -oE "$P" | wc -l | tr -d ' '   # the head, stamped
   TAIL "$D" | grep -oE "$P" | sort | uniq -c      # the tail, the claim under test

   WO='first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|last|final|penultimate'
   W="\b($WO)\b [a-z]{0,12} ?\**\b($S)\b"          # the WORD-ordinal arm; $P is digit-only
   for o in $(echo "$WO" | tr '|' ' '); do         # POSITIVE, one branch at a time
     printf '%s=%s ' "$o" "$(printf 'the %s row\n' "$o" | grep -ciE "$W")"; done; echo
   printf 'the third **row**\nthe third matching line\n' | grep -ciE "$W"   # POSITIVE, both gaps
   printf 'the second seam\nadd no new seam\n3 blocks were added\nfour rows\nrow 6\nthe 6th row\n' \
     | grep -ciE "$W"                              # TRUE NEGATIVE for the word arm
   git show cf3a862:"$D" | HEAD /dev/stdin | grep -oiE "$W" | sort | uniq -c   # the head, stamped
   TAIL "$D" | grep -oiE "$W" | sort | uniq -c     # the tail, the claim under test
   ```

   Run on the working file this revision ships, **after the v1.103 entry** landed rather than
   before it — the entry is named rather than described, because "the entry recording this
   revision" stops resolving from the bytes the moment a later entry exists, which is the same
   reason the tail-count site above names its version:
   each of the sixteen noun branches of `$P` prints `1`, its flag
   branch prints `1`, and its true negative prints `0` — every branch fires, and the digit arm
   declines a word-ordinal over a set, a cardinality phrasing, a number standing *before* a span
   noun, and a bare word-ordinal count. **`$P` is digit-only, and that was v1.100's unstated
   property**: a span noun beside a *word* ordinal scores `0` on it, and this document writes that
   shape in both of its halves. `$W` closes it over the same noun set and a fifteen-member ordinal
   set; all fifteen ordinal branches print `1` against a one-line fixture, the emphasised-noun and
   one-word-gap positives print `2` between them, and its true negative — which also carries
   `row 6`, the digit arm's business, and `the 6th row`, which is nobody's, see the residual —
   prints `0`.

   **The head is stamped at `cf3a862`: `$P` raises 14 there and `$W` raises 6**, because this
   revision and its predecessor write span-ordinal examples into the head as controls, so a
   working-file head value would be a number this paragraph moved by being written — the same
   publication rule the candidate sweep and the carry screen state. Two of the 14 are the genuine
   span ordinals `block is **4**` and `block is **2**` in §Test Strategy, each naming its base
   (`enumerate(b, 1)`, 1-based) and its span (the named-anchor block span) in the same sentence,
   so the positive here is **live text in this document**, not only a fixture. Of the 6: two are
   `last`-anchored, and **an ordinal counted from the end carries no zero-versus-one ambiguity, so
   it needs no base — that is a closure over the whole `last`/`final`/`penultimate` end of `$WO`
   and not a per-hit excuse**; two are cardinalities rather than addresses (a walk that happens a
   second time, output that may not start one); one addresses a field of a command's printed
   output which the same paragraph quotes in full, so its span is exhibited beside it, and that
   one disposition is a *reading*; and **one was a genuine unbased address** — the
   helper-mutation-spec paragraph addressed two prescribed rows of `docsections.json` by position.
   Both are now named by key alone, the keys having stood in the same sentence all along, so the
   ordinals carried no information and one bound of ambiguity.

   **The conclusion v1.100 drew about the tail is withdrawn, because the arm that could see its
   counter-instances did not exist.** `$P` raises 12 there and every one is a printed count rather
   than a position: nine mutation-spec row totals, the two census output fields of the
   named-anchor command, and one mention of a fence indented past a column. `$W` raises 6, of
   which four are ordinals over `docsections.json`'s rows, in the entries for v1.52, v1.53, v1.58
   and v1.62. Three of the four name the row's key in the same clause, so the address resolves
   through the key and the ordinal is redundant rather than ambiguous; one names no key and is a
   bare unbased address. **None of the four resolves against the tree at all**: that spec's
   `mutations` array holds **4** rows today —
   `python3.11 -c "import json;print(len(json.load(open('h-mad/tests/mutation-specs/docsections.json'))['mutations']))"`
   → `4` at `68a70d6` — and eight is what this design *prescribes*, not what the file *has*. The
   remaining two are the cardinality and printed-output-field shapes the head also carries. So
   *"no §Version History entry states a span ordinal without its base"* is **false**. It is
   withdrawn rather than re-scoped, and the entries are not rewritten: they are dated records, and
   what this revision changes is the sentence that claimed there were none, plus the body site,
   which was exempt from nothing.

   **Residual, exactly**: the noun set is closed by enumeration, so a span noun this feature
   adopts later (`field`, `cell`, `record`, `frame`) is invisible until it is added to `$S`, and
   `$WO` is closed the same way, so `thirteenth` onward is invisible until it is added there; the
   gap in `$W` is at most one word of letters, so an ordinal separated from its noun by a
   conjunction or a parenthetical is seen only through whichever half sits adjacent — measured
   rather than supposed, `printf 'its sixth and eighth rows\n' | grep -oiE "$W"` prints one hit
   and not two, which is how the body site above was found by half; a digit ordinal written as a
   suffixed numeral (`the 6th row`) is matched by neither arm and is named here as uncovered
   rather than screened; and the disposition of the twelve digit hits and of the six word hits is
   a *reading*, exactly as the disposition of the eight seam-ordinals above it is.
2. **A cardinality statement is not an address** — "without an additional seam", "add no new
   seam" — because it refers to a hypothetical further member rather than picking one out of the
   set. Such a statement is permitted in principle, and this document phrases every one of them
   without an ordinal, which is why the expected output on the head is a bare `0`.
3. **The screen is proximity-based, so a hit is a candidate to read, not automatically a
   defect** — and it is blind in three named ways. It over-matches when an ordinal over some
   *other* set (blocks, rows, arms, tuple members) lands within the gap of one of the three
   nouns without an intervening sentence break; the v1.76 tail hit is a live instance of exactly
   that, and it is why item 2's "any hit is a finding" would be too strong a rule to carry. It
   *under*-matches an ordinal written as a digit-plus-suffix rather than a word, a noun outside
   `{seam, injection, primitive}`, and a gap longer than 60 characters. **The axis behind the
   second of those, stated once rather than patched member by member**: `\b$N\b` bounds *every*
   sibling of the alternation, so any morphological variant of a listed noun is as invisible as an
   unlisted noun. The plural was the live variant — this document writes "seams", "injections" and
   "primitives" throughout — and `$N` now carries `s?` on all three, which closes it. What remains
   uncovered is named, not waved at: a possessive (`seam's`), a hyphenated compound (`sub-seam`),
   and any noun this feature adopts later for the same set. The head returns `0` on the working
   file **after the v1.103 entry**, and re-running the same pipeline on those same bytes with `N`
   cut back to its singular-only form also returns `0` — the comparison was first made on the
   v1.100 bytes and is re-taken here, because a differential between two alternations is a
   property of the file they are run over and a bump moves it,
   so **widening the alternation changed nothing here and the blindness was never exercised on
   this file** — which is the honest statement of what the `0` is worth, and it is weaker than
   "the class is closed". That `0` is the **state under test**, not an absence measurement: it is
   what the screen exists to assert, so it carries no load-bearing/incidental label, and the
   controls above rather than the `0` itself are what show the screen can print something else.

**Eight named fault injections — seven module-level seams (`os.killpg`, `shutil.rmtree`,
`tempfile.mkdtemp`, `os.chmod`, `os.unlink`, `_final_write`, `_close_stream`) plus one
instance-level wrapper (the recorded `Popen` instance's `communicate`, `wait` and `poll`) — each
on a call whose *failure* is under test, all via pytest's `monkeypatch` (restored on exit), all
leaving `subprocess` real; this list is the canonical taxonomy, and what the spec and the impl-plan owe it is the
same **set** — membership only, never order and never position, since seams here are named and
never numbered precisely so that a reordering is not load-bearing. Nothing is claimed here about
what either sibling currently reads; a divergence is a defect in whichever document diverges and
is found by enumerating all three, not by trusting this sentence — and the enumeration is shipped
as a runnable command immediately below this paragraph, not left as an obligation:** the AC-5.5
`killpg` seam is patched only for AC-4.6's `reap` stage (`PermissionError` after `poll()`), since
the AC-5.5 race itself is reproduced by a real fixture (a leader that exits at once behind an
`os.setsid()` escapee) and needs no mock; the AC-3.14 cleanup guards are exercised by patching `shutil.rmtree`
in the helper's namespace — once to raise `OSError`, once to do nothing — because a real
permission failure is skipped under root and the two guards need mutants only one of them kills;
and AC-4.6's `mkdtemp` stage patches `tempfile.mkdtemp` to raise and, separately, `os.chmod` to
raise (AC-3.13's post-creation failure, which must remove the directory it just created). The
`spawn` stage needs no mock: the test sets `PATH` to an empty directory and `bash` is genuinely
not found. The `_final_write(handle, text)` seam is the module's own, patched to raise
`OSError` for AC-3.8's post-run write failure — the one call for which no real fault exists on
this platform — or patched to call the real `_final_write` with a recording proxy around the held
handle whose `flush`/`close` raise (the close-in-`finally` tests), which is the same seam and the
same injection, not a new one. The `_close_stream(handle)` seam is the module's own single
closure primitive — patched to raise `OSError` for the backstop-close tests on paths where the final
write never ran (a timeout, an alias refusal), because a held descriptor cannot be made to fail at
close deterministically either. The instance-level wrapper, for AC-4.6's `collect` stage, is the recorded
`Popen` instance's own bound `communicate` (first call raises `OSError(EIO)`, later calls pass
through) and, separately, its `wait` — reached through the AC-5.6 recording pass-through, which
observes the real constructor and stubs nothing, so `subprocess.Popen` itself stays real
(design audit v62); the same wrapper injects `poll` (the `poll-oserror-unmapped` row) and a
`TimeoutExpired` from `wait` (the bounded-wait rows) — one instance-level injection, three methods.
The `os.unlink` seam is patched in the helper's namespace to raise
`PermissionError` for the reservation rollback's read-back (`test_rollback_unlink_failure_reports_leftover`),
because a directory writable at create time cannot be made unwritable between the two arms of one
call. The drain race needs no mock, because a real
`os.setsid()` descendant holds the pipes open; the real permission fixture still runs wherever
`euid != 0`. Fixtures are markdown strings written to `tmp_path`, deliberately **hostile** rather than
tidy: headings at mixed levels, fences quoting fences, a path containing a space, a body with
CRLF, and a key containing regex metacharacters.

**The enumeration that contract names, shipped as a command rather than left as an obligation** —
because a contract with nothing runnable behind it is a sentence, and this document's own rule is
that every measurement publishes its command inline or names a script `git ls-files` can find. It
selects, in each of the three documents, the paragraph stating the canonical taxonomy, and prints
the set of names that paragraph carries:

```bash
SHA=cf3a862   # the two siblings are read at a sha; this document is read as the working file
SEAM='`(os\.(killpg|chmod|unlink)|shutil\.rmtree|tempfile\.mkdtemp|_final_write|_close_stream|Popen)`'
SEL='BEGIN { RS = "" }
     /instance[-]level/ && /fault[ ]injection/ && $0 !~ /^- v1\./ { gsub(/\n/, " "); print }'
for f in docs/02-design/features/doc-block-exec.design.md \
         docs/01-plan/features/doc-block-exec.spec.md \
         docs/01-plan/features/doc-block-exec.impl-plan.md; do
  case $f in *design.md) src=$(cat "$f") ;; *) src=$(git show "$SHA:$f") ;; esac
  printf '%-28s ' "${f##*/}"
  printf '%s\n' "$src" | awk "$SEL" | grep -oE "$SEAM" | tr -d '`' | sort -u | tr '\n' ' '
  printf '(sites=%s)\n' "$(printf '%s\n' "$src" | awk "$SEL" | grep -c '')"
done
```

Run after the edits this revision ships, with the siblings read at `cf3a862` because both were
being edited in the working tree at the time, it prints the identical eight-member set three
times — `_close_stream _final_write os.chmod os.killpg os.unlink Popen shutil.rmtree
tempfile.mkdtemp` — at `(sites=1)`, `(sites=1)` and `(sites=2)`. **The contract holds; nothing is
owed to either sibling, and that is a measurement rather than a reading.** Two properties are
deliberate. The selector is written so that **this fence cannot match itself**: `instance[-]level`
matches the prose spelling but not the bracketed one it is written in, which is the same
publication rule as the screen above, one level down. And `$SHA` stamps the siblings, so a
sibling being rewritten mid-round cannot silently change this output. **Residual, exactly two
items.** The selector picks by *content predicate*, not by heading, so a fourth document — or a
restatement inside one of these three — that names the same set without both marker phrases is
invisible to it; the `(sites=N)` column is printed for exactly that reason, and a site count
dropping to `0` is a broken locator, not a clean run. And the check compares **sets**, which is
all the contract asks: it is silent about order and position by design, and it is also silent
about wording, so the annotations the two siblings interleave into their lists — the impl-plan
scoping `os.killpg` to AC-4.6's reap and `os.unlink` to AC-3.10's read-back, the spec giving each
name its AC — pass it, correctly.

The CLI is exercised by `subprocess.run([sys.executable, SCRIPT, …])` so the exit codes under test
are the real process's, not a return value — the same shape `test_skill_candidates_census.py` uses —
**for every verdict a real input or a real fault can produce**. A verdict that needs one of the eight
fault injections (the seven module seams `_final_write`, `_close_stream`, `tempfile.mkdtemp`,
`os.chmod`, `shutil.rmtree`, `os.killpg`, `os.unlink`, or the `Popen` instance wrapper for
`communicate`/`wait`/`poll`) is driven in-process through `main(argv)` instead — its return value is the exit code
and `capsys` holds the lines — because a `monkeypatch` cannot cross an exec boundary; two
subprocess tests (`NOT_FOUND` → 0, an unreadable document → 2) pin that `sys.exit(main(...))` turns
that return value into the process exit, so the in-process code is the real code.

## Test Plan

`h-mad/tests/test_h_mad_doc_block_exec.py`:

**Rows address ACs by *range* as well as singly; the range separator is an en dash (`–`), not an
ASCII hyphen; and only the *lower* endpoint of a range carries the `AC-` prefix.** A reviewer
sweeping the spec's `AC-N.M` identifiers against this document must expand the ranges before
concluding anything, and a range pattern written with an ASCII hyphen expands nothing at all.
Two figures, both derived and neither carried:

```bash
SPEC=docs/01-plan/features/doc-block-exec.spec.md   # the sibling is stamped; this document is the working file
comm -23 <(git show cf3a862:$SPEC | grep -oE 'AC-[0-9]+\.[0-9]+' | sort -u) \
         <(grep -oE 'AC-[0-9]+\.[0-9]+' docs/02-design/features/doc-block-exec.design.md | sort -u) | wc -l
```

Over the whole document it prints **7** of the **49** the spec carries at `cf3a862`: seven ACs
this design addresses only inside a range and never as a literal identifier. **The sibling side is
read at a sha** — standing decisions E and F — so an edit to the spec cannot move either figure
under a reader's feet; run with the *working* spec instead, both come out `7` of `49` as well, so
the stamp hardens the claim without changing it. Narrowed to this table's leading column —
`grep -oE '^\| AC-[0-9]+\.[0-9]+[^|]*' "$D" | grep -oE 'AC-[0-9]+\.[0-9]+' | sort -u | wc -l` →
`15` — only 15 of the 49 appear literally, so a table-scoped identifier sweep reports 34 absences
where a whole-document sweep reports 7. Both figures are the same table read at two scopes, which
is why a sweep has to state which it ran.
**The seven are deliberately not listed here.** Writing them out would put each identifier into
this document and turn the command's answer into `0` — the publication rule stated at the carry
screen below, in its most literal form: a measurement over this document's own text is destroyed
by naming what it found.

| ACs | Tests |
|---|---|
| AC-1.1–1.7 | tagged-vs-untagged selection; a document containing an invalid UTF-8 byte → `UNREADABLE reason=doc_unreadable`, never a traceback; zero → `NOT_FOUND`; two → `AMBIGUOUS blocks=2 heading="<h>"`; `--index` 2 and 3; same/shallower-level bound; a fence quoting the tag, a `~~~` fence quoting the tag, and a four-space-indented literal tag (an indented code block, never an opener); **a document with two identical headings → `AMBIGUOUS_HEADING count=2`, nothing executed** (fixture mirrors `invariants.example.md`'s duplicated `###`) |
| AC-1.8 | `docsections` delegates: no second bounder implementation remains (asserted on the source), its existing `test_docsections.py` still passes unchanged, and the shared bounder handles the unbalanced four-backtick case that the old toggle got wrong, **and its own contract is pinned directly** — `test_bounder_ignores_a_heading_inside_a_tilde_fence` and `test_bounder_ignores_an_indented_literal_fence` call `fence_aware_end` on hostile text and assert the section does not end at a heading quoted inside a `~~~` block or at a four-space-indented literal fence, since `docsections` consumes it as a section bounder, not through the extractor. **The import arrangement is pinned twice**: `test_docsections_imports_when_collected_alone` runs `pytest h-mad/tests/test_docsections.py -q` as a subprocess from the repo root, and `test_docsections_imports_from_an_unrelated_cwd` runs `python3 -c "import docsections"` with only the tests dir on `sys.path` and `cwd=tmp_path` — both would fail if `docsections.py` relied on another module's `sys.path` insert |
| AC-1.9 | `--index 0` and `--index -1` → `BAD_INDEX index="<n>"`, exit 0, and the block a naive `blocks[-1]` would have chosen leaves no side effect; `select(blocks, 0)` raises `BadIndex` |
| AC-2.1–2.7 | path substitution; absent key refuses; two absent keys → two detail lines; metacharacter key; multi-occurrence count equals replacements; a value containing another key is neither re-substituted nor mis-counted, in both map orders; overlapping keys refuse with `SUBST_OVERLAP`, `keys=` counts distinct keys (`a`/`ab`/`abc` → 3) and the `overlap:` lines are one per pair in `(shorter, longer)` order |
| AC-3.1–3.10 | `pwd` outside the repo and gone after; `git status --porcelain` byte-identical across a writing block; `-u` strict-vs-plain; bare `exit 3` → rc 3 with the harness alive; `pipefail` strict-vs-plain; streams unmerged, and `str` — a block printing `é` round-trips it, a block running `printf '\xff'` yields U+FFFD (AC-3.6); `shell=fish` → `BAD_INFO`; optional stream paths; aliased `--stdout`/`--stderr` (a symlink, `./x` vs `x`, **and an `os.link` hard link**) refuse after reservation and before running, with both handles closed and a created file unlinked; unwritable stream path refuses **and the block leaves no side effect**; a pre-existing stream file is truncated, not appended; **a failed `--stderr` reservation leaves a pre-existing `--stdout` file byte-identical, and removes a `--stdout` file the call itself created**; **a timeout leaves pre-existing artifacts byte-identical** (nothing is written on that path); `_final_write` fault-injected → `UNREADABLE reason=stream_write_failed`; failing only the stderr write leaves the stdout artifact current with `written: "stdout"` / `failed: "stderr"` detail lines; `os.unlink` fault-injected on a failed second reservation → `stream_path_unwritable` with a `leftover: "<path>"` line, the created file present and empty, no traceback |
| AC-3.11–3.12 | a block reading `$FIXTURE_VAR` runs with `preamble="FIXTURE_VAR=…"` and its text is unchanged (the `Block.text` the API returns is byte-identical to the fence body); preamble **and** `subs` together — the executed text carries the substituted value, proving the preamble is composed with `text′`; the same with a preamble that has **no trailing newline**, proving the composition inserts the boundary; a preamble that fails (`false`) under strict mode is visible as the combined `rc` and stderr; `--preamble-file` on the CLI; an unreadable preamble path **and a preamble file containing an invalid UTF-8 byte** → `UNREADABLE reason=preamble_unreadable`, and the block leaves no side effect |
| AC-2.8 | `--subst K`, `--subst =V` → `BAD_SUBST arg="<raw>"`; `--subst K=a --subst K=b` → `BAD_SUBST` with `duplicate_key: K`; `--subst K=a=b` substitutes the value `a=b`; each refusal executes nothing and reserves nothing |
| AC-3.13 | the block itself runs `stat -f %Lp .` (macOS) / `stat -c %a .` (GNU) and the test asserts `700` **from the block's stdout**, so the mode is observed from inside the running block, not inferred from the API — **with `os.umask(0o777)` set around the call and restored in `finally`**, which is what proves the chmod rather than the umask produced it; the source contains no `mktemp` invocation — argv token or shell command word, the same predicate as AC-5.3 |
| AC-3.14 | a block running `mkdir keep && chmod 000 keep` → `run_block` raises `CleanupFailed(path, cleanup_error)` with `cleanup_error` the `PermissionError` and the CLI prints `CLEANUP_FAILED path="<p>"`, exit 2, no `rc=` (skipped when `euid == 0`); the test then `chmod 700`s and removes the tree in its own `finally`; `test_cleanup_failure_carries_the_os_error` and `test_cleanup_readback_catches_silent_retention` fault-inject `rmtree` (raising / no-op) and run everywhere; a normal run reads back absent (also AC-3.1) |
| AC-4.6 | `mkdtemp` fault-injected → `LAUNCH_FAILED stage=mkdtemp`, exit 2; `os.chmod` fault-injected → `LAUNCH_FAILED stage=mkdtemp` and the directory `mkdtemp` created is gone; `PATH=<empty dir>` → `LAUNCH_FAILED stage=spawn` and the cwd is gone; `os.killpg` raising `PermissionError` under a timed-out block → `LAUNCH_FAILED stage=reap` within the drain bound, cwd gone, `pgid=` in the detail — the fake records the pgid; because `dbe.os` is the process-global `os` module, the test binds `real_killpg = os.killpg` **before** `monkeypatch.setattr(dbe.os, "killpg", fake)` and its `finally` uses that bound original to send `SIGKILL` to the recorded pgid and to assert the group is gone (`real_killpg(pgid, 0)` raising `ProcessLookupError`), so neither the teardown nor the assertion goes through the fake; `communicate` fault-injected on the recorded `Popen` instance (first call raises `OSError(EIO)`, later calls pass through) under a block that would otherwise `RAN` → `LAUNCH_FAILED stage=collect`, exit 2, `pgid:` in the detail, cwd gone, group gone (`real_killpg(pgid, 0)` → `ProcessLookupError`); `proc.wait` fault-injected under a timed-out, signalled block → `stage=collect` with the `BlockTimeout` as `__context__`, within the drain bound; `proc.poll` fault-injected under a timed-out block → `stage=collect` with the `BlockTimeout` as `__context__`, the group still killed and gone; each carries an `os_error:` detail line and no `rc=` |
| AC-4.1–4.5 | `RAN` exits 0 with a non-zero block rc; **every** row of the verdict table exits with the code the table states — 0 for `RAN`, every refusal and `TIMEOUT`, 2 for `UNREADABLE`, `CLEANUP_FAILED` and `LAUNCH_FAILED` (the test enumerates the table rather than hardcoding a count, so adding or re-classing a verdict cannot leave the test stale); no cannot-judge carries `rc=`; only `AMBIGUOUS` carries `blocks=`; registry ↔ detail-line bidirectional pin; the parser rejects `--all`/`--dir` and abbreviated long options (`allow_abbrev=False`) |
| AC-5.1–5.4 | sleeping block → `TIMEOUT`; no surviving descendant after reap; **no `timeout`/`gtimeout` INVOCATION** — an argv token or shell command word, never a substring, since the source legitimately contains `timeout=`, `TimeoutExpired`, `BlockTimeout` and `--shell-timeout`; temp cwd removed after timeout |
| AC-5.6 | `--shell-timeout` `0`, `-1`, `nan`, `inf` and `abc` each → `BAD_TIMEOUT value="<v>"`, exit 0, and a block with a side effect leaves none; `run_block(block, timeout=0)` raises `BadTimeout` with no child spawned (asserted by wrapping `subprocess.Popen` in a recording pass-through that must not have been called — an observation of the real call, not a fault injection, so the named-fault-injection list in Test Strategy stands) |
| AC-5.5 | `test_timeout_survives_a_group_that_already_emptied`, **no mock**: the block is `python3 ESC_PATH & exit 0` where `ESC_PATH` is replaced through the substitution map with the absolute path of an `esc.py` the test writes under its own `tmp_path` (the AC-5.2 idiom — the child's cwd is a fresh private directory, so nothing can be placed in it beforehand; the substituted absolute path is what makes the fixture executable) and `esc.py` calls `os.setsid()`, writes its pid to an absolute path outside the cwd, and sleeps holding stdout — `communicate` times out, `poll()` reaps the zombie leader, `killpg` raises `ProcessLookupError`, the drain times out, pipes close, `wait()` returns at once → `TIMEOUT`, cwd absent, no traceback; the test kills the escapee in `finally`; `test_timeout_drain_is_bounded_against_an_escapee`: the block starts an `os.setsid()` python child that writes its pid to an absolute path (outside the cwd, via the substitution map — the AC-5.2 idiom) and sleeps holding stdout, then the leader sleeps; `run_block(timeout=1)` raises `BlockTimeout` within `1 + 2 * DRAIN_SECONDS + 2` s wall time, the cwd is absent, and the test kills the escapee from the pid file in its `finally`; `test_wait_after_kill_is_bounded`: the recorded instance's `wait` records its `timeout` keyword (`== DRAIN_SECONDS`) and raises `TimeoutExpired` → `LAUNCH_FAILED stage=reap`, `pgid:` in the detail, `BlockTimeout` as `__context__`, cwd gone, within `timeout + 2 * DRAIN_SECONDS + 2` s |
| AC-6.1–6.6 | tag present on the Second-surface fence **and exactly one tagged opener across the `*.md` files of `h-mad/` and `handoff/`, excluding `archive/`** (`test_exactly_one_tagged_fence_in_the_tree`, the plan's census sweep asserting cardinality 1). **The `*.md` restriction is load-bearing and was missing until design v1.92**: `_fence_events` is a markdown scanner, and by Task 5 the feature's own `h-mad/tests/test_h_mad_doc_block_exec.py` has landed under `h-mad/` carrying a column-0 tagged bash opener inside triple-quoted fixtures (AC-1.1, AC-1.5, AC-1.7, AC-3.7), which an unrestricted sweep counts as openers -- so the AC could not pass at Task 5 GREEN, and its RED reason ("zero tagged fences") was false for the same reason. A `.py` triple-quoted fixture is a false positive by construction, and one fixture is a deliberately unbalanced four-backtick fence, so a whole-file `.py` scan is not even additive. **The sweep excludes build output by excluding any path with a dot-directory component** (`.pytest_cache/README.md` is the live instance — five of them exist on any tree where pytest has run, and at `a8e0372` a filesystem glob without this filter returns 35 `*.md` where `git ls-files` returns 30 — both figures move with the tree and neither is a pin, which is why §Scanning states the corpus as a command; §Scanning states the same exclusion for the heading and Setext measurements, which realise it as `git ls-files` because a one-off human measurement has no reason not to). The two realisations differ on purpose: a test must still count a **newly written, not-yet-tracked** `.md` under the two roots, which is exactly the doc a `git ls-files` sweep would miss and this guard exists to catch. Residual, stated in full: a tagged fence added to a non-`.md` file is out of scope of this count by design; a `.md` file added outside `h-mad/`/`handoff/` is likewise uncounted; and a generated `.md` written under the two roots *outside* a dot-directory does enter the count — correctly, since it is then part of the executed documentation surface, but noisily if a tool starts emitting one. **Documenting the tag convention is subject to the same count**: the plan carries "`hmad:exec` fence info-string tag convention" as a deliverable and this design is its only home, so if it is ever written into an `.md` under `h-mad/` or `handoff/`, the example opener must use the four-space-indented literal (never an opener by this document's own grammar, §Scanning) or it becomes a second tagged fence and fails AC-6.1. No `re.findall(r"```bash` left on the **executing** path (`_gate_bash_block` and `_run_recipe`), and **exactly one** remaining in the file — the text scan inside `test_exec_codex_dispatch_carries_out_log_and_timeout`, which `test_exec_block_scan_performs_no_execution` pins as non-executing and `test_only_the_exec_scan_hand_rolls_extraction` pins as the only occurrence, so the exemption cannot silently widen; the four migrated behaviours still pass; **the full suite passes AND its collected count is >= the pre-change baseline plus this feature's added tests** (both halves — a passing suite that silently lost tests satisfies neither): `test_suite_floor_holds` runs `pytest --collect-only -q` in a subprocess (collection executes nothing, so the suite cannot recurse; `DOCBLOCK_FLOOR_INNER=1` makes an inner instance skip regardless) and asserts collected >= `2748` (the baseline **re-measured at `e8eaf6f`**, from the repository root with `cwd=REPO_ROOT` -- the same command run from `h-mad/` collects 2486, a different tree, not the baseline; design audit v68 agy). It was `2747`/`2485` at `6b4df35` and `b59e05e` then added a test, which left the floor asserting `>= 2747` against a real 2748 and so permitted exactly one silent deletion; **the number therefore travels with the commit it was measured at and is re-measured at 5c branch time** (plan v1.84, spec v1.53) + the collected count of `test_h_mad_doc_block_exec.py` alone + **`len(tuple)`**, where `tuple` is the floor tuple of node IDs added to *existing* files, each asserted present. **`len(tuple)` is the assertion; no total is the contract.** A literal here has gone stale twice — `+ 7` was the instance, and a `+ 9` written in its place would be the next one — so what this document carries is the expression, and any number below is a dated evaluation of it that names its sha. **Membership is spec AC-6.4's rule and is not re-worded here**; that rule's *empirical evaluation* is this document's job, and it is written as prose immediately beneath this table under **The floor tuple, evaluated** rather than in this cell — it is the densest reasoning in the document, and a single table cell renders it as one unbroken block, which is the least reviewable shape available for it.  A short `+ 7` here would have tolerated two silent deletions — exactly the weakening the floor exists to prevent; the pass half is the Phase-5f gate command run alone outside the suite — `pytest … > log; RC=$?; tail -1 log; echo "SUITE: rc=$RC"`, gated on both the `passed` line and `rc=0`, never a bare `| tail -1` whose status is `tail`'s; and the two wire directions — the AC-6.5 spies are installed with `monkeypatch.setattr(dbe, …)` on the consumer's module alias, which is why the consumer must call `dbe.extract`/`dbe.run_block` and a test pins that it has no `from h_mad_doc_block_exec import` |


**The floor tuple, evaluated.** This is the empirical evaluation the AC-6.1–6.6 row above points
to; it lives here rather than in that cell so that it can be read and diffed as prose.
**Membership is spec AC-6.4's rule and is not re-worded here**; what follows is that rule's
*empirical evaluation*, which is this document's job. **Evaluated at `74e126f` the rule yields a
nine-member tuple, seven authored and two collected.** The seven authored: six in
`test_h_mad_collect_report_docs.py` (`test_gate_block_resolves_through_doc_block_exec`,
`test_recipe_runs_through_run_block`, `test_gate_block_refuses_an_untagged_recipe`,
`test_exec_block_scan_performs_no_execution`, `test_consumer_calls_the_helper_module_qualified`,
`test_only_the_exec_scan_hand_rolls_extraction`) and
`tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`. **The two
collected are not authored by anyone and are the ones a hand-written list drops**:
`h-mad/tests/test_h_mad_portable_timeout.py` builds `_SCANNED` at module level from
`*sorted((SKILL / "scripts").glob("*.py"))` and parametrises **two** tests over it with
`ids=lambda p: p.name`, so Task 1 landing `h-mad/scripts/h_mad_doc_block_exec.py` collects
`test_no_document_or_script_emits_a_bare_timeout_command[h_mad_doc_block_exec.py]` and
`test_no_document_or_script_rests_on_an_unconditional_absence_claim[h_mad_doc_block_exec.py]`.
**Measured, not reasoned**: with a one-line stub written at that path, `pytest --collect-only
-q` gained exactly those two node IDs and no others (`… --collect-only -q | grep -c
'h_mad_doc_block_exec.py\]'` → `2`) — that probe was run at `a8e0372`, and the reason its result
still stands at `74e126f` is stated rather than assumed. **The cheap standing check, which does
not need the stub**: the only way the evaluation moves is a glob-driven `parametrize` entering a
directory this feature adds a file to, so census the `parametrize` decorators directly — `grep
-c 'parametrize("path", _SCANNED' h-mad/tests/test_h_mad_portable_timeout.py` → `2` (the two
that carry the addend), `grep -c parametrize` → `0` on both
`h-mad/tests/test_h_mad_mutation_harness.py` and `handoff/tests/test_mutation_specs_clean.py`
(**incidental**, and that is the label the absence rule requires: neither file parametrises at
all today, so the zero is a property of those two files' current bytes rather than of anything
this feature guarantees — which is precisely what the residual beginning "if a future test
parametrises" says would move it)
(the two files that glob a `mutation-specs/` directory at all — the first over
`h-mad/tests/mutation-specs/`, the one this feature adds to; the second over `handoff/`'s own,
which this feature does not touch — and in both the globbing helper is called from inside a test
body, so this feature's two new `.json` collect nothing). And the search space for a *newly
arrived* one is closed by the diff: `git diff --name-only a8e0372 74e126f` names exactly one
test file, `h-mad/tests/test_h_mad_assemble_audit.py`, whose single `parametrize` is over a
two-element literal list (`["SKILL.md", "references/orchestration-mode.md"]`), not a glob — so
no glob-driven `parametrize` has entered since the probe. **Membership is spec AC-6.4's rule,
restated by locator and not re-worded here**; the evaluation of it that this document owns is
the paragraph above, and its axis — the reason a hand-written list drops members — is that a
node can be *collected* without being *written*. The directories where that can happen for this
feature are `h-mad/scripts/` (one `.py` added) and `h-mad/tests/mutation-specs/` (two `.json`
added). Residual, exactly: if a future test parametrises over `mutation-specs/*.json`, the
evaluation grows by two and must be re-derived by the stub probe rather than by re-reading this
sentence — and because the assertion carries `len(tuple)` rather than a literal, only the
enumeration below needs the correction, never the arithmetic. **Re-derived at `74e126f`, not
carried**: the three standing counts are unchanged — `grep -c 'parametrize("path", _SCANNED'
h-mad/tests/test_h_mad_portable_timeout.py` → `2`, and `grep -c parametrize` → `0` on both
`h-mad/tests/test_h_mad_mutation_harness.py` and `handoff/tests/test_mutation_specs_clean.py`
(***incidental***, the same label the site above carries, for the same reason: neither file
parametrises at all today, so the zero is a property of those two files' current bytes) —
and `git diff --name-only a8e0372 74e126f` still names exactly one test file, so the evaluation
stands at the audited commit. **Re-run again at `cf3a862`**: `2`, `0`, `0`, and
`git diff --name-only a8e0372 cf3a862 | grep -c 'tests/'` → `1`, so it stands there too.

**Helper mutation spec — `h-mad/tests/mutation-specs/doc_block_exec.json`, entry by entry.** Every
guard below carries one mutation and the one named test that must go RED under it; the spec's
`command` is `["python3.11", "-m", "pytest", "tests/test_h_mad_doc_block_exec.py", "-q"]` and its
`target_command` is `["python3.11", "-m", "pytest", "-q"]`, `root` is `../..` (commands run from
`h-mad/`, as `docsections.json` does), and **every `test` key is the full node ID**
`tests/test_h_mad_doc_block_exec.py::<name>` — the harness runs `target_command + [test]`, and a
bare `test_*` name is a nonexistent path to pytest, so the names in the table below are the
`<name>` half and the spec carries them qualified. The same rule binds the other two specs:
`tests/test_h_mad_collect_report_docs.py::<name>` in `doc_block_exec_wire.json` (whose `command`
is `["python3.11", "-m", "pytest", "tests/test_h_mad_collect_report_docs.py", "-q"]`) and
`tests/test_docsections.py::<name>` in `docsections.json` for the **six** rows killed there — **the four originals** (the adjective "re-anchored" is deliberately dropped here, and the reason is stated as a dated reading of the siblings rather than as a present-tense claim about their bytes, which decision E forbids. **Read at `1cbddb7` with `git show 1cbddb7:<path> | grep -c 're-anchor'` over the three siblings, head and tail together: impl-plan `8`, plan `2`, spec `0`** — the design's own count is deliberately not given, because this paragraph is what moves it, the same rule the candidate sweep above states. The enumeration below is over *axes*, which is a claim about sibling bytes and so is derived rather than recalled. **Three axes, across two siblings.** The impl-plan uses the word on the *anchor-file* axis, where only two of the four rows move — `fence-tracking-removed` and `section-no-longer-owns-its-subsections` into `h-mad/scripts/h_mad_doc_block_exec.py`. The **plan** uses it on the *anchor-text* axis, "re-anchored **in place**", naming the complementary pair — `offset-anchored-bound-runs-to-end-of-file` and `missing-heading-returns-empty-instead-of-failing` — whose `file` key does *not* move and whose `find` string is rewritten. That is the collision that actually misleads: both siblings say "two re-anchored" and the two pairs are **disjoint**, so a reader reconciling them by cardinality alone gets the wrong rows. This sentence's own use was a third axis, the *`test`-key* one, over all six rows. The tree-derived half is separable and is stamped on the tree, not on a sibling: all four rows in `h-mad/tests/mutation-specs/docsections.json` carry `"file": "tests/docsections.py"` at `1cbddb7`. One word on three axes with two disjoint pairs is a collision the design cannot fix from here; it gives up the word rather than redefine it, and the sibling-to-sibling half is **reported, not edited** — this author writes one file), `docsections-delegation-reverted` and
`docsections-heading-lookup-reverted` (the local `re.search` heading regex restored in `titled_section`, `find_heading` untouched), the last two both bound to the delegation spy — while the two rows keyed
`docsections-syspath-setup-removed`, bound to `tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd`, and
`docsections-local-bounder-restored`, bound to `tests/test_h_mad_doc_block_exec.py::test_docsections_has_no_second_bounder`, bind into the new module's file (design audit v75 agy: 6 + 2 = 8) —
(a `test` key is a full node ID and may name any collectable file; the harness runs `target_command + [test]`). Exact `find` anchors are set from the
landed source in the same task that lands it (the author-together ordering the plan states for
`docsections.json`), each exact-once; the mechanism column is what the anchor must express.
`ALL_CAUGHT` is required for all three.

**Wire mutation spec — `h-mad/tests/mutation-specs/doc_block_exec_wire.json`** (the plan's FR-6
table, restated here so the design enumerates every spec it names):

| mutation | mechanism | killed by (`test` key, under `tests/test_h_mad_collect_report_docs.py::`) |
|---|---|---|
| `wire-revert-extract` | `_gate_block` resolves its block with a local, tag-tolerant `re.findall(r"```bash[^\n]*\n(.*?)```")` instead of `dbe.extract`/`dbe.select` (tag-tolerant so the mutant still resolves the tagged block and the wire, not the regex, is what fails), helper untouched | `test_gate_block_resolves_through_doc_block_exec` (AC-6.5) |
| `wire-revert-select` | `_gate_block` keeps `dbe.extract` but picks `blocks[0]` (or raises locally) instead of calling `dbe.select`, callee intact | `test_gate_block_resolves_through_doc_block_exec` (AC-6.5 — the same pin also spies `dbe.select` and asserts one call with the extracted list and `index=None`) |
| `wire-revert-run` | `_run_recipe` runs `subprocess.run(["bash", "-c", preamble + script])` inline instead of `dbe.run_block` | `test_recipe_runs_through_run_block` (AC-6.5) |
| `wire-revert-substitute` | `_run_recipe` rewrites the checkout path with `str.replace` instead of `dbe.substitute`, callee intact | `test_recipe_runs_through_run_block` (AC-6.5 — the same pin also spies `dbe.substitute` and asserts one call with the gate block and the `{installed gate path: quoted checkout path}` map) |
| `wire-unconditional` | the call site grows `dbe.extract(...) or <legacy regex>`, so an untagged gate block is still resolved | `test_gate_block_refuses_an_untagged_recipe` (AC-6.6) |
| `exec-scan-executes` | the text scan inside `test_exec_codex_dispatch_carries_out_log_and_timeout` is made to run its block through `dbe.run_block` | `test_exec_block_scan_performs_no_execution` (AC-6.2) |
| `consumer-from-import` | the consumer gains a bare `from h_mad_doc_block_exec import …` beside the alias and every helper call goes unqualified (one contiguous replacement at the call region, the alias line untouched) | `test_consumer_calls_the_helper_module_qualified` (AC-6.5 precondition) |
| `hand-rolled-extraction-widened` | a second `re.findall(r"```bash…")` appears on the executing path | `test_only_the_exec_scan_hand_rolls_extraction` (AC-6.2) |

Under the two reverts the helper's own suite must stay green — the half that proves the failing
test pins the wire, not the callee — and the harness records both runs. The three guard rows
that were once listed as "(no mutation)" now carry mutants, because a guard without a mutant is
exactly what the base Mutation verification invariant forbids.

| mutation | guard it removes (mechanism) | killed by (`test` key) |
|---|---|---|
| `tag-check-removed` | `extract` returns every ```bash fence, tagged or not | `test_untagged_fence_is_not_a_candidate` (AC-1.1/1.2) |
| `fence-run-length-ignored` | any ``` line closes a fence, regardless of run length | `test_quoted_tag_inside_longer_fence_is_not_an_opener` (AC-1.6) |
| `section-bound-ignores-level` | the section ends at the next heading of *any* level | `test_section_owns_deeper_headings` (AC-1.5) |
| `heading-lookalike-accepted` | heading recognition is loosened to `line.lstrip().startswith("#")`, so `#hashtag`, a 7-`#` run or a 4-space-indented `## x` bounds or starts a section | `test_heading_lookalikes_are_not_headings` (AC-1.5 — the section under the real heading still owns the block past each lookalike, and a lookalike never matches the requested heading) |
| `adjacent-heading-skipped` | the boundary predicate becomes `>` `start` instead of `≥`, so a same-or-shallower heading on the very next line after the requested heading is not a boundary and its tagged block is extracted under the wrong address | `test_adjacent_heading_bounds_the_section` (AC-1.5 — the first section has no candidate and `fence_aware_end(text, start, level) == start`) |
| `heading-level-pin-ignored` | `find_heading` matches the full `## Text` form on text alone, ignoring the hash count | `test_find_heading_accepts_full_and_bare_forms` (AC-1.5 — `### Text` must not satisfy `## Text`) |
| `request-predicate-space-only` | the full-form request predicate accepts only a space after the hash run while the scanner accepts a space, a tab or end of line, so `##\tText` and `##` requests fall to the bare form and cannot select their headings | `test_full_form_request_accepts_tab_and_eol` (AC-1.5) |
| `form-precedence-bare-first` | `find_heading` tries the bare form first (or unions both forms), so the request `## Text` also matches a `### ## Text` heading and refuses as ambiguous | `test_heading_form_precedence_full_wins` (AC-1.5) |
| `closing-hash-run-kept` | `_fence_events` leaves the optional closing hash run in a heading event's text, so `## Text ##` no longer matches `## Text` and a `## Text`/`## Text ##` pair counts as one | `test_closing_hash_run_does_not_change_heading_identity` (AC-1.5/1.7) |
| `heading-match-ignores-fence-state` | the heading search runs over every line instead of the scanner's `prose` lines, so a fenced `## <heading>` starts the section | `test_requested_heading_quoted_inside_a_fence_is_not_a_section_start` (AC-1.5/1.6 — the candidate must be the block under the real heading, and a tagged block under the fenced copy is never selected) |
| `duplicate-heading-takes-first` | `AmbiguousHeading` never raised; first match wins | `test_duplicate_headings_refuse` (AC-1.7 — the row's one `test` key; `test_bare_form_duplicate_headings_refuse` exercises the same guard through the bare form and is a regression test, not a second key) |
| `select-first-on-ambiguous` | `select` returns `blocks[0]` when >1 and no index | `test_two_tagged_blocks_without_index_are_ambiguous` (AC-1.3) |
| `index-below-one-accepted` | `index < 1` reaches `blocks[index - 1]` | `test_index_zero_refuses` (AC-1.9) |
| `missing-key-silently-skipped` | a zero-count key is not collected | `test_absent_key_refuses` (AC-2.2) |
| `overlap-resolved-by-order` | substring keys proceed in iteration order | `test_overlapping_keys_refuse` (AC-2.7) |
| `replacement-sequential` | replacement becomes a per-key `str.replace` loop in map order, so a value containing another key is re-scanned | `test_value_containing_another_key_is_not_rescanned` (AC-2.6 — `A→B`, `B→C` on `A B` must yield `B C` for **both** map orders; the sequential mutant yields `C C` in the `A`-first order, and both keys occur so a missing-key precheck cannot mask it) |
| `subst-split-on-every-equals` | `--subst` split on every `=` | `test_subst_value_may_contain_equals` (AC-2.8) |
| `subst-duplicate-key-last-wins` | a repeated `--subst` key overwrites instead of refusing | `test_duplicate_substitution_key_refuses` (AC-2.8) |
| `cli-empty-key-delegated` | `main` stops refusing the empty key while building the map and lets `substitute` raise `BadSubstArg("")`, so the verdict prints `arg=""` instead of the raw `arg="=V"` | `test_subst_empty_key_is_bad_subst` (AC-2.8 — `--subst =V` asserts `arg="=V"`; the impl-plan's Task 4 CLI test) |
| `empty-map-not-short-circuited` | the empty-map guard is removed, so `{}` compiles a `""` alternation | `test_empty_substitution_map_is_a_no_op` (AC-2.2) |
| `duplicate-info-token-last-wins` | a repeated recognised token overwrites instead of refusing | `test_duplicate_info_tokens_refuse` (AC-3.7) |
| `index-nonint-unmapped` | `main` lets a non-integer `--index` raise `ValueError` instead of `BAD_INDEX` | `test_non_integer_index_is_bad_index` (AC-1.9/5.6 — values are the contract's, grammar is argparse's) |
| `timeout-nonnumeric-unmapped` | `main` lets a non-numeric `--shell-timeout` raise instead of `BAD_TIMEOUT` | `test_non_numeric_timeout_is_bad_timeout` (AC-5.6) |
| `doc-decode-error-unwrapped` | the document read drops `UnicodeDecodeError` from the `DocUnreadable` wrap (or reads with `errors="replace"`) | `test_invalid_utf8_document_is_unreadable` (AC-3.12) |
| `preamble-decode-error-unwrapped` | the preamble read drops `UnicodeDecodeError` from the `PreambleUnreadable` wrap | `test_invalid_utf8_preamble_is_unreadable` (AC-3.12) |
| `unknown-info-key-ignored` | an unrecognised token falls back to strict | `test_unknown_info_key_refuses` (AC-3.7) |
| `cwd-not-passed` | `cwd=cwd` is dropped from the `Popen` call, so the block runs in the caller's cwd | `test_block_runs_in_the_temp_cwd` (AC-3.1 — `pwd` is neither the repo root nor the document's directory, and is gone afterwards) |
| `scanner-duplicated-in-consumer` | `extract` regrows a private fence toggle instead of consuming `_fence_events` | `test_extract_has_no_fence_state_of_its_own` (AC-1.8 single-source) |
| `strict-flags-dropped` | `bash -c` always, never `-euo pipefail` | `test_unset_variable_fails_under_strict` (AC-3.3) |
| `preamble-separator-dropped` | composition is `preamble + text′`, no newline | `test_preamble_without_trailing_newline_still_precedes_the_block` (AC-3.11) |
| `preamble-composed-with-unsubstituted-text` | composition uses `block.text`, not `text′` | `test_preamble_and_substitution_compose` (AC-3.11) |
| `stream-reserved-with-truncation` | the reservation's `os.open` flags gain `O_TRUNC` (or the loop is replaced by `open(path, "w")`), so reserving empties a pre-existing artifact | `test_stdout_survives_a_failed_stderr_reservation` (AC-3.8) |
| `final-write-close-not-in-finally` | `_final_write`'s `close()` is moved out of its `finally` (a plain statement after the `try`), so a failing `flush` skips the close inside the mapped region and a failing close's error escapes | `test_final_write_failure_before_close_still_closes` (AC-3.8 — the canonical `test` key: the proxy's `flush` and `close` both raise; the mutant never calls the proxy's `close` from `_final_write`, and the outer `finally` closes the real handle, not the proxy; `test_final_write_close_failure_is_mapped` — `close` alone raises, the mutant prints a traceback — also goes red and stays as a regression test on the same mutant, but the spec's one `test` key names the former) |
| `verify-deferred-past-second-write` | `main` verifies both artifacts only after both `_final_write` calls, so stderr is truncated and written before a stdout verification failure is diagnosed | `test_final_write_readback_catches_a_silent_no_op` (AC-3.8 — the detail lines must read `failed: "stdout"` / `skipped: "stderr"` and the stderr artifact's bytes must be unchanged) |
| `final-write-not-verified` | the post-close read-back and comparison of each artifact is removed | `test_final_write_readback_catches_a_silent_no_op` (AC-3.8 — `_final_write` injected as a no-op that returns normally; the verdict must still be `stream_write_failed` with `verify: "stdout"`) |
| `closer-trailing-text-accepted` | a line whose marker run is followed by non-blank text closes the fence | `test_closer_with_trailing_text_does_not_close` (AC-1.6 — a ```` ```trailing ```` line inside a quoting fence must not close it) |
| `nonregular-stream-accepted` | the `S_ISREG` check on the reserved descriptor is removed, so a FIFO/device/socket is accepted as an artifact | `test_stream_path_char_device_refuses` (AC-3.10 — `/dev/null` opens, so the check is reached; a reader-less FIFO fails at `open` and never reaches it) |
| `stream-open-blocking` | `O_NONBLOCK` is dropped from the existing-file arm, so a reader-less FIFO blocks the open forever | `test_stream_path_fifo_without_reader_refuses_bounded` (AC-3.10 — the test's own bounded wait is what makes this mutant RED rather than a hang; it runs the CLI in a subprocess with `timeout=5` and treats expiry as failure) |
| `stream-alias-check-removed` | the `fstat` `(st_dev, st_ino)` comparison is gone | `test_hard_linked_stream_paths_refuse` (AC-3.9) |
| `mktemp-invocation-planted` | `tempfile.mkdtemp()` is replaced by `subprocess.run(["mktemp", "-d"], …)` — valid Python and exactly the forbidden invocation | `test_no_mktemp_invocation_in_source` (AC-3.13 — the argv-token/command-word scan is green on the real helper and goes RED on this mutant) |
| `chmod-0700-removed` | `os.chmod(cwd, 0o700)` after `mkdtemp` is gone | `test_cwd_mode_is_0700_under_hostile_umask` (AC-3.13) |
| `cleanup-errors-ignored` | `ignore_errors=True` restored | `test_cleanup_failure_carries_the_os_error` (AC-3.14) |
| `cleanup-readback-removed` | the `lexists` read-back is gone | `test_cleanup_readback_catches_silent_retention` (AC-3.14) |
| `precedence-timeout-raised-in-handler` | `BlockTimeout` raised inside the handler instead of recorded as pending | `test_cleanup_failure_outranks_timeout_injected` (AC-3.14) |
| `argparse-error-unrouted` | the parser's `error()` override is removed, so an unknown option or a missing value exits 2 through argparse's usage text with no `DOCBLOCK:` line | `test_malformed_invocation_is_a_verdict` (AC-4.1) |
| `allow-abbrev-restored` | the parser is built with `allow_abbrev=True` (the argparse default), so `--shell-t 5` silently aliases `--shell-timeout` | `test_parser_rejects_all_dir_and_abbreviations` (AC-4.2 — the abbreviated spelling must be a `BAD_ARGS` verdict — one `DOCBLOCK:` line, exit 0, no usage text (design v1.85)) |
| `stream-write-oserror-unwrapped` | the `except OSError` mapping around `_final_write` and its read-back is removed, so a write failure escapes as a traceback | `test_stream_write_failure_after_the_run_is_a_refusal` (AC-3.8 — the injected failure must print `stream_write_failed`, exit 2, no traceback) |
| `exit-partition-flipped` | refusals exit 2 | `test_verdict_table_exit_codes` (AC-4.2) |
| `rc-leaked-into-refusal` | a refusal line carries `rc=` | `test_no_refusal_carries_rc` (AC-4.3) |
| `field-escape-removed` | `_field` returns its input unchanged, so a newline inside a heading, key, path or OS-error text starts a second `DOCBLOCK:` line | `test_newline_in_dynamic_fields_cannot_forge_a_verdict_line` (AC-4.1) |
| `c1-escape-removed` | `_field`'s second pass is removed, so DEL, C1 controls (U+0085) and U+2028/U+2029 stay literal inside the quotes and `splitlines()` sees more than one line | `test_unicode_line_separators_cannot_split_a_verdict_line` (AC-4.1) |
| `field-quoting-removed` | `_field` escapes control characters but emits the value bare, without the JSON quotes, so `--heading 'x rc=0'` renders `heading=x rc=0` and a key/value consumer reads an `rc` field on a refusal | `test_dynamic_field_cannot_forge_a_token` (AC-4.1/4.3) |
| `launch-oserror-unwrapped` | `mkdtemp`/`Popen` `OSError` propagates as a traceback | `test_mkdtemp_failure_is_a_verdict` (AC-4.6) |
| `collect-oserror-unmapped` | the `except OSError` around the first `communicate(timeout)` is removed, so a pipe-read failure escapes as a traceback with the child unreaped | `test_communicate_oserror_is_launch_failed_collect` (AC-4.6) |
| `drain-oserror-unmapped` | the guard around the post-kill drain, the pipe closes and the `wait()` is removed, so a failure there escapes past the pending `BlockTimeout` | `test_drain_wait_oserror_is_launch_failed_collect` (AC-4.6) |
| `poll-oserror-unmapped` | the guard around the pre-kill `poll()` is removed, so a `waitpid` failure escapes as a traceback with the group unkilled | `test_poll_oserror_is_launch_failed_collect` (AC-4.6) |
| `killpg-replaced-by-kill` | `proc.kill()` instead of `os.killpg(proc.pid, …)` | `test_in_group_descendant_is_reaped` (AC-5.2) |
| `poll-before-killpg-removed` | `proc.poll()` before `killpg` is gone, so the natural race reports `LAUNCH_FAILED stage=reap` (EPERM on a zombie-only group) instead of `TIMEOUT` | `test_timeout_survives_a_group_that_already_emptied` (AC-5.5) |
| `killpg-esrch-uncaught` | `ProcessLookupError` from `killpg` propagates | `test_timeout_survives_a_group_that_already_emptied` (AC-5.5) |
| `wait-unbounded` | the post-kill `wait` has no timeout, so a signalled leader that does not exit holds the helper open past `timeout + 2 * DRAIN_SECONDS` | `test_wait_after_kill_is_bounded` (AC-5.5 — the wrapped `wait` records `timeout=None`) |
| `wait-expiry-unmapped` | the `except TimeoutExpired` around the post-kill `wait` is removed, so an expiry escapes as a traceback instead of `LAUNCH_FAILED stage=reap` | `test_wait_after_kill_is_bounded` (AC-5.5) |
| `drain-unbounded` | the post-kill `communicate` has no timeout | `test_timeout_drain_is_bounded_against_an_escapee` (AC-5.5) |
| `timeout-validation-removed` | `math.isfinite(t) and t > 0` is gone | `test_nonpositive_timeout_refuses_before_spawn` (AC-5.6) |
| `chmod-failure-unwrapped` | a failing `os.chmod` propagates and the created cwd is left behind | `test_chmod_failure_is_a_verdict_and_removes_the_cwd` (AC-3.13/4.6) |
| `chmod-rollback-unguarded` | the chmod failure removes the cwd outside the `finally` selection, so a failing removal is a traceback | `test_chmod_rollback_failure_is_cleanup_failed` (AC-3.13/3.14) |
| `body-indent-not-stripped` | `extract` returns fence body lines with the opener's indentation still on them | `test_indented_fence_body_is_deindented` (AC-1.6 — exact text at 1, 2 and 3 spaces, plus a body line indented less than the opener) |
| `indented-opener-accepted` | a run preceded by 4+ spaces is treated as an opener | `test_bounder_ignores_an_indented_literal_fence` (AC-1.8 — the bounder's own contract; `test_indented_literal_tag_is_not_a_candidate` pins the extractor side of the same rule under AC-1.6) |
| `prefix-state-truncated-mid-line` | the prefix is fed as `text[:start]` instead of whole lines through the line containing `start`, so a ```` ```trailing ```` line cut after its run reads as a closer | `test_bounder_offset_after_a_marker_run_on_a_non_closing_line` (AC-1.8) |
| `prefix-fence-state-skipped` | `fence_aware_end` starts its fence state at `start` instead of scanning the lines before it | `test_bounder_from_an_offset_inside_a_fence` (AC-1.8 — `section_from` anchored inside a fenced block must not end at a fenced `#`) |
| `backtick-in-info-accepted` | `_fence_events` treats a backtick-fence line whose info string contains a backtick as an opener | `test_backtick_in_info_string_is_not_an_opener` (AC-1.6 — the line must be inert: not a candidate, not `BAD_INFO`, and the following ``` line opens a fence) |
| `tilde-fence-not-tracked` | `~~~` fences are not tracked, so a heading inside one ends a section and a quoted ```bash opener inside one is a candidate | `test_bounder_ignores_a_heading_inside_a_tilde_fence` (AC-1.8 — the bounder's own contract; `test_tag_quoted_inside_a_tilde_fence_is_not_an_opener` pins the extractor side under AC-1.6) |
| `cleanup-error-ignored-when-tree-gone` | `CleanupFailed` only when `lexists`, a recorded error alone is dropped | `test_cleanup_error_after_successful_removal_is_still_a_failure` (AC-3.14) |
| `empty-key-accepted-by-api` | `substitute` accepts `""` and calls `str.replace("", v)` | `test_empty_key_is_refused_by_the_api` (AC-2.8) |
| `indented-closer-accepted` | the scanner closes a fence on a marker run preceded by four or more spaces | `test_indented_closer_does_not_close` (AC-1.6 — the four-space ```` ```` ```` line stays body text and the fence ends at the next 0–3-space closer) |
| `rollback-leftover-unreported` | the rollback's `lexists` read-back is removed, so a first-reservation file that the failed unlink left behind is never reported on the `stream_path_unwritable` verdict | `test_rollback_unlink_failure_reports_leftover` (AC-3.10) |
| `stream-open-oserror-unwrapped` | the reservation region's `except OSError` is removed, so an `ENOTDIR`/`EACCES` on `os.open` (or an `OSError` from `fstat` or the rollback) escapes as a traceback | `test_stream_path_under_a_regular_file_refuses` (AC-3.10 — a real `ENOTDIR`, no injection; the verdict must be `stream_path_unwritable`, exit 2, no traceback) |
| `backstop-close-unmapped` | the `except OSError` around `main`'s backstop `_close_stream` is removed, so a failing close on the timeout path escapes as a traceback | `test_backstop_close_failure_on_timeout_is_mapped` (AC-3.8 — `_close_stream` injected to raise under `TIMEOUT`; the verdict must be `stream_close_failed`, exit 2) |
| `backstop-close-outranks-error` | the post-`finally` selection raises `StreamCloseFailed` even when an exit-2 error is already pending | `test_backstop_close_failure_does_not_outrank_a_refusal` (AC-3.8 — an aliased pair plus an injected close failure must still report `stream_paths_alias`) |
| `registry-row-removed` | one remedy row deleted from the `SKILL.md` Helper-scripts entry (the mutation targets `SKILL.md`) | `test_every_emittable_line_has_a_registry_row` (AC-4.5) |
| `detail-line-undocumented` | the helper renames one emitted detail line (`missing_key:` → `absent_key:`) so an emittable line has no row | `test_registry_rows_cover_only_emittable_lines` (AC-4.5) |
| `timeout-invocation-planted` | the real argv construction `["bash", *flags, "-c", script]` becomes `["timeout", "5", "bash", *flags, "-c", script]` — valid Python, valid argv, and exactly the forbidden invocation | `test_no_timeout_invocation_in_source` (AC-5.3) — the source scan is green on the real helper and goes RED on this mutant |

Eighty-one rows, eighty-one mutations — **eighty of the helper's source and exactly one of
`h-mad/SKILL.md`**. **The split is derived from the mechanism column above, never carried**: count
the rows whose mechanism names `SKILL.md` as the file the harness edits. Exactly one does
(`registry-row-removed` — "one remedy row deleted from the `SKILL.md` Helper-scripts entry"); its
AC-4.5 partner `detail-line-undocumented` mutates the **helper**, renaming an emitted detail line
(`missing_key:` → `absent_key:`) so an emittable line loses its row. The two are the
manifest-integrity guard's two directions of the bidirectional pin, but they sit in *different*
files, and the split follows the file, not the AC. (The AC-5.3 row, once described as a
fixture-copy self-check, is likewise a real argv mutation of the helper's source that the source
scan must catch.) **This paragraph previously read "seventy-nine … two of `h-mad/SKILL.md`" and was
the origin the plan and impl-plan copied**; the concrete failure mode is that a
`"file": "h-mad/SKILL.md"` anchor on `detail-line-undocumented` is an anchor the mutation harness
refuses, because the string it must replace lives in the helper. A guard added later without a
row here is what the base Mutation verification invariant forbids, and the impl-plan audit reads
this table against the landed spec.

Verification commands:

```bash
# every command bounded through the reachable dispatcher (base Portable time bounds invariant);
# `hmad-dispatch run` propagates the wrapped status and returns 124 on expiry (measured 2026-09-03)
hmad-dispatch run --timeout 600  -- python3.11 -m pytest h-mad/tests/test_h_mad_doc_block_exec.py -q
hmad-dispatch run --timeout 600  -- python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_block_exec.json
hmad-dispatch run --timeout 600  -- python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/doc_block_exec_wire.json
hmad-dispatch run --timeout 600  -- python3.11 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/docsections.json   # re-pointed anchors, named-test form: ALL_CAUGHT required
hmad-dispatch run --timeout 1200 -- python3.11 -m pytest -q -p no:cacheprovider > /tmp/doc_block_exec_suite.log; RC=$?   # full suite, run alone
tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"                           # gate on both lines; rc=124 is the wrapper's expiry, not a suite result
```

AC-5.2 is measured, not asserted by inspection: the block records its own descendant's PID before
sleeping, and after the timeout the test requires `os.kill(pid, 0)` to raise `ProcessLookupError`.
A test that only checked the direct child would pass against the orphaning bug this AC exists to
prevent.

**The AC is scoped to the process GROUP, and that bound is real rather than cautious.** A
descendant that calls `os.setsid()` leaves the group and survives any `killpg`. Measured:

```
descendant in the group       -> survived killpg? False
descendant that called setsid -> survived killpg? True
```

A first attempt used the `setsid` **binary** and showed no escape — that probe was vacuous, since
macOS ships no such binary, and reading its null as a negative would have kept an over-claim in
the spec. So the test asserts no *in-group* descendant survives; claiming more would assert
containment nothing here implements.

**The PID file must be written OUTSIDE the temp cwd.** Writing it inside — the obvious choice —
destroys the evidence on exactly the path under test, because `run_block` removes that directory
in `finally` and AC-5.4 requires it to. The test therefore passes an absolute path under pytest's
`tmp_path` into the block via the substitution map. This works *because* the temp cwd is isolation
and not a sandbox: an absolute path escapes it, which the design states plainly under Architecture
Considerations rather than relying on it silently.

**The reaping claim is measured, not assumed.** Run this session, with a control that discriminates:

```
killpg   : grandchild 304 alive_after=False   (want False)
p.kill() : grandchild 516 alive_after=True    (want True = control discriminates)
VERDICT: CONFIRMED
```

A `bash -c 'sleep 300 & echo $! > f; sleep 300'` under `start_new_session=True`, timed out, then
reaped two ways. `os.killpg(os.getpgid(p.pid), SIGKILL)` removed the grandchild; `p.kill()` alone
left it running. The control is the load-bearing half — without it, "grandchild gone" could equally
mean the probe never created one.

## Invariant Compliance

- **Skill self-containment** — complies: stdlib only, no third-party import, no import of another
  skill's internals, and specifically **no import of `h-mad/tests/docsections.py`** despite the
  overlap, because `scripts/` must not depend on `tests/`.
- **Skill manifest integrity** — complies: `SKILL.md` gains a Helper-scripts registry entry in the
  same commit that adds the module, and AC-4.5 pins the entry to the emittable detail lines in
  both directions.
- **Audit-gate signal discipline** — complies, on the invariant's own partition: one `DOCBLOCK:`
  token; **exit 0 on every verdict**, refusals and `TIMEOUT` included, so a declined run never
  registers as a tool failure; exit 2 only for genuine operational errors — `UNREADABLE` (input
  that could not be read, an artifact path that could not be written or reserved, a write that
  failed), `CLEANUP_FAILED` and `LAUNCH_FAILED` (the helper's own `mkdtemp`/`Popen`/`killpg`
  raised). A caller reads the token, never `$?`. An earlier draft exited 2 on
  every refusal after `MUTATION: PRECHECK_FAILED`; that copied the minority precedent, and the
  gate and assembler (`GATE: FAIL` / `ASSEMBLE: HALT`, both exit 0) are the rule.
- **No new external dependency** — complies: no new CLI, no package. `bash` is already assumed by
  every recipe in this skill.
- **Portable time bounds** — complies: the bound is Python's own (`Popen.communicate(timeout=…)`).
  AC-5.3 bans an **invocation**, not the substring: the source legitimately contains
  `timeout=`, `TimeoutExpired`, `BlockTimeout` and the `--shell-timeout` flag, and a substring ban
  would reject the very design that satisfies the invariant. The test asserts no `timeout`/
  `gtimeout` appears as an argv token or as a command word inside a shell string.
- **Mutation verification** — complies: every guard carries a mutation with a named `test` key, so
  a mutant killed by an unrelated assertion is reported as a survivor rather than a catch. The
  helper's own cleanup is held to the same rule: `rmtree` is read back rather than trusted, and
  restoring `ignore_errors=True` is itself a mutation the AC-3.14 test must kill.
- **Connection enforcement** — complies: FR-6 is declared a wiring task with a `WIRE`/`WIRE-PIN`
  and two-direction discrimination (AC-6.5/AC-6.6); a whole-module revert is explicitly not
  sufficient, because it removes both sides at once.
- **Single-source contract** — complies on the invariant's FIRST branch for the rule this feature
  owns: section bounding has exactly one authoritative implementation (`fence_aware_end` on
  `_fence_events`) and `h-mad/tests/docsections.py` calls it (AC-1.8), replacing both its duplicate
  `_fence_aware_end` and `titled_section`'s local heading regex. **The claim is scoped to that
  rule, and the scope is stated because the tree holds hand-rolled `##`-slicers that the consumer
  census behind it — a grep for `from docsections import` — cannot see by construction.** That
  census names three files at `35698f9` (`test_docsections.py`, `test_h_mad_review_evidence.py`,
  `test_h_mad_wire_registry.py`), so every other slicer in the two roots is invisible to it by
  construction rather than by accident.

  **The residual is given as a SCOPE RULE plus a runnable sweep, never as a cardinality**, because
  no mechanical sweep over this class is both sound and complete — measured in both directions at
  `35698f9`, and the reason a count is refused is that two differently-wrong predicates can agree
  on one. **Scope rule**: the invariant binds *a rule applied by more than one surface*; a
  test-local helper that slices one document for its own pins applies no shared rule and is
  outside it, whatever its internals. The sweep, which prints candidate bodies and is *not* a
  membership oracle:

  ````bash
  python3.11 -c "
  import ast, pathlib, re
  op = re.compile(r'\.(find|index|split|startswith|rfind|partition)\(')
  for root in ('h-mad/tests', 'h-mad/scripts', 'handoff'):
      for f in sorted(pathlib.Path(root).rglob('*.py')):
          src = f.read_text(encoding='utf-8', errors='replace')
          for n in ast.walk(ast.parse(src)):
              if isinstance(n, ast.FunctionDef) and not n.name.startswith('test'):
                  seg = ast.get_source_segment(src, n) or ''
                  if '## ' in seg and op.search(seg): print(f'{f} {n.name}')
  "
  ````

  It prints 22 lines at `35698f9`, and that is *its* output, not a count of slicers.
  **Over-count, each body read at `35698f9` rather than taken on report**: `traced_bindir` and
  `run_with_bindir` in `h-mad/tests/test_hmad_dispatch_audit_cycle.py` hold their `## ` inside a
  *stub audit-report string* (`"# Audit\n\n## Must-fix\nNone…"`) fed to a subprocess; `main` in
  `h-mad/scripts/h_mad_audit_gate.py` holds it in a comment naming the sections an input must
  have; `main` in `h-mad/scripts/h_mad_wire_pin_gate.py` holds it in an error message describing a
  header shape. None of the four slices a section — the sweep selects them because a `## ` literal
  and a `.split(`/`.find(` call co-occur in one body, which is a *shape*, not a role.
  **Under-count, one verified instance**: `def _section` in
  `h-mad/tests/test_h_mad_collect_report_docs.py` does not appear, because its `##` anchors arrive
  as *parameters* and so occur nowhere in its body — the same reason a value sweep cannot close a
  class.

  **Three examples, named because the compliance argument was actually walked over them**, each
  addressed by its own `def` per the enclosing-symbol rule stated in Task 5, so
  `grep -n 'def _titled_section' …` locates one and a `grep` that returns nothing is the signal
  that it was renamed: `def _titled_section` in `h-mad/tests/test_h_mad_context_budget_docs.py`
  (8 call sites, derived as `grep -c '_titled_section(' <that file>` minus the `def` line),
  `def section_text` in `h-mad/tests/test_h_mad_batch_doc_rules.py`, and `def _section` in
  `h-mad/tests/test_h_mad_collect_report_docs.py` (reached through `_second_surface()`). None is a
  surface applying *this* rule: each is a test-local assertion helper slicing one document for its
  own pins, and **all three are fence-blind — a property of these three, not of the class**. The
  class demonstrably contains fence-*aware* members: `def _section` in
  `h-mad/tests/test_h_mad_pane_visible_dispatch_docs.py` and `def _section` in
  `h-mad/tests/test_h_mad_context_budget_docs.py` both track fences deliberately, each with a
  comment saying why. **Residual, stated exactly rather than as "and similar"**: the compliance
  conclusion above has been argued over the three named and over no other member; the members the
  sweep prints and this bullet does not walk are *unexamined against it*, not *found compliant by
  it*. What makes that acceptable is the scope rule, which turns on whether a helper applies a
  shared rule and not on how it is written — and what would falsify it is a slicer that two
  surfaces call, which is the shape §Scanning's guards are aimed at.

  They are also not drop-ins — measured at `1861157`: `_titled_section` anchors on a substring, so
  `docsections.titled_section(SKILL_MD, "Run-context ceiling")` raises
  `AssertionError: missing section` where the real heading is
  `## Run-context ceiling — halt the run at 80%`. **Migrating them is deliberately out of this
  feature's scope**; what is in scope is that after Task 5 `_section`/`_second_surface()` no longer
  sits on the executing path — `_gate_block()` calls `dbe.extract(SKILL_MD, "## Second surface — the
  codex leg")` directly — so the one slicer that was reached by executed code is left serving text
  pins only.
- **Assumption verification** — complies: the plan's `## Measurements` section carries both cited
  commands with their observed output, and the design adds no uncited measured claim. The two
  heading measurements are re-derived here over the **tracked** corpus (§Scanning) because the
  filesystem glob behind the plan's `files=` figure is not reproducible on a clean clone. The
  plan's §Measurements carries the same differential and is owed the same sweep — **and the debt
  is named by corpus, never by figure**, because the tracked count at `a8e0372` is itself 30: a
  reader who chases a bare "30" will find the plan's number agreeing with a fresh `git ls-files`
  for the wrong reason and close the item. What the plan owes is the *definition* (`git ls-files
  -- h-mad handoff`, `*.md`, `archive/` excluded) and a re-measure at the commit it cites, not a
  different number.

## Version History

- v1.0: Initial design draft.
- v1.1: Design audit v1 (8 findings, union of codex 7 + agy 1): split extract/select, complete the exception->verdict mapping, backtick-run-aware fence scanning, move the AC-5.2 PID file outside the temp cwd, cite the reaping probe and the orphan-process count, restate AC-5.3 as an invocation ban and AC-6.4 in full.
- v1.2: Design audit v2 (agy, 1 must + 2 should; codex clean): add the differential bounder test the Single-source contract requires, make substitution counting sequential and refuse overlapping keys, document the ATX-only heading assumption.
- v1.3: Design audit v3: killpg(proc.pid) rather than killpg(getpgid(pid)) — the getpgid race was reproduced and would orphan the grandchild; scope BAD_INFO to tagged fences; enumerate the verdict table instead of hardcoding counts.
- v1.4: Design audit v4: resolve the AC-1.6/AC-1.8 incompatibility by making this module the authoritative bounder and having docsections import it; narrow the Test Plan's AC-5.3 row to an invocation ban (its fourth surface).
- v1.5: Plan re-audit v5: only the executing call site migrates — :270 and :412 select different blocks (measured, 4 blocks in the section), so the earlier 'both extractors break' claim was false and AC-6.2 was unsatisfiable; add docsections.py to Deliverables.
- v1.6: Plan re-audit v7: scope AC-5.2 to the launched process group (a setsid descendant escapes, measured); refuse aliased --stdout/--stderr (AC-3.9); correct the risk row that still claimed both extractors break.
- v1.7: Plan re-audit v8: add the fixture preamble boundary (AC-3.11/AC-3.12) — without it the gate block's COLLECT_OUT is unbound under strict bash and the FR-6 migration cannot reach GATE: PASS.
- v1.8: Plan re-audit v9: refuse duplicate headings (AC-1.7) — invariants.example.md has two; cite the controlled preamble pair, which also narrows the earlier 'aborts on unbound variable' claim to 'cannot reach GATE: PASS'.
- v1.9: Narrow the preamble's set -u wording to what the controlled pair actually measured.
- v1.10: Design audit v5 (codex must 4 + agy must 9, union): BAD_INDEX for ordinals below 1; verified cleanup with CLEANUP_FAILED and read-back, precedence over TIMEOUT; both timeout races specified (ProcessLookupError on killpg, bounded drain against an escapee, DRAIN_SECONDS); extract docstring no longer contradicts AmbiguousHeading; PreambleUnreadable mapped; AC-3.12 combined-invocation contract stated; Test Plan covers AC-1.7, 1.9, 3.11-3.14, 5.5 and the collect-alone import; docsections.json re-point; the one permitted monkeypatch named.
- v1.11: Plan re-audit v12 back-propagation: fence_aware_end signature in the API block and __all__; consumer calls module-qualified for the wire spies (Components + Test Plan).
- v1.12: Plan re-audit v13 back-propagation: --preamble-file in the CLI line; stream artifacts reserved at pre-check with overwrite semantics and StreamWriteFailed; CleanupFailed carries its cause, with the two cleanup mutations and the tests that kill them; the second named fault injection (rmtree).
- v1.13: Plan re-audit v14 back-propagation: composition rule in the preamble paragraph; allow_abbrev=False on the parser; Test Plan rows for both.
- v1.14: Design audit v6 (agy must 1, codex must 2 should 2): composition uses text-prime (substituted); Popen text=True utf-8 replace; timeout validated finite and positive before spawn (BadTimeout/BAD_TIMEOUT); stream artifacts probed for append then reserved after every check; tree-wide single-tag cardinality test; Test Plan rows for each.
- v1.15: Design audit v7 (codex must 4 should 1; agy clean): reservation last, append-mode, truncate at the final write, created-file unlink on a failed second reservation; three post-spawn exit-2 verdicts with explicit precedence; SUBST_OVERLAP keys= and ordering defined; docsections.json named-test form; computed AC-6.4 floor.
- v1.16: Design audit v8 (codex must 3 should 1, agy must 2): exit-code partition per the base invariant in the verdict table, diagram and Invariant Compliance; pending-outcome control flow so CLEANUP_FAILED really outranks TIMEOUT, with the combined test; substitute returns a new Block and run_block never substitutes; main's order corrected; floor test runs collect-only in a subprocess with an env guard and the pass half is the out-of-suite gate command; the five consumer-file node IDs enumerated.
- v1.17: Design audit v9 (codex must 3 should 1; agy clean): LaunchFailed for mkdtemp/Popen/non-ESRCH killpg with a reap stage that never waits unboundedly; alias judged on fstat of the reserved handles; CleanupFailed carries cleanup_error separately from __cause__; three named fault injections plus the real empty-PATH spawn failure; the suite gate captures RC before tail.
- v1.18: Design audit v10 (codex must 2 should 1, agy must 1): four post-spawn outcomes with LAUNCH_FAILED stage=reap placed in the precedence; the exception table names descriptor-level alias detection and the reservation open, matching the Detailed Design; DocUnreadable and PreambleUnreadable wrap UnicodeDecodeError under strict UTF-8.
- v1.19: Design audit v11 (codex must 3; agy must 1 + 2 nits): chmod 0o700 after mkdtemp with the umask probe; reap-failure policy and the test teardown that reaps the launched group; BAD_SUBST parser contract with BadSubstArg; main's order puts the alias check after reservation; substitute wording and the API raises list corrected.
- v1.20: Design audit v12 (codex must 2; agy must 3): verification commands run the docsections.json harness and the status-preserving suite gate; Invariant Compliance names LAUNCH_FAILED among the exit-2 classes.
- v1.21: Design audit v13 (codex must 2; agy clean): the helper mutation spec is enumerated — 27 entries with mechanism and the named RED test each — and the timeout-vs-cleanup precedence is carried by an injected test that runs everywhere, with the permission fixture as its root-skipped sibling.
- v1.22: Design audit v14 (codex must 5; agy must 2): timeout validated before mkdtemp in the diagram and prose; LAUNCH_FAILED in the diagram's partition; chmod-failure test and mutation (29 rows); invalid-UTF-8 document and preamble cases in the Test Plan; four named fault injections.
- v1.23: Design audit v15 (codex must 5 should 2; agy clean): tilde fences tracked with the marker character; cleanup failure on recorded error OR read-back; _final_write seam as the fifth injection with ordered writes and reported partial state; empty key refused in substitute; alias row worded on inodes; three new mutations (32 rows).
- v1.24: Design audit v16 (codex must 3; agy clean): the killpg fake models an empty group (kill, wait, then raise); duplicate-key gets its own mutation; the chmod rollback runs inside the same try/finally selection with its own mutation and test (34 rows).
- v1.25: Design audit v17 (codex must 1): 0-3 space indentation rule in the scanner, its hostile fixture and mutation (35 rows).
- v1.26: Design audit v18 (codex must 2 should 1 nit 1; agy clean): AC-4.5 gets two mutations (registry row removed, detail line undocumented); the delegation wire is module-qualified and mutation-pinned; the reap-failure branch is stated never to wait (37 rows).
- v1.27: Design audit v19 (codex must 1; agy see report): the AC-6 test row scopes the no-re.findall assertion to the executing path and pins the :412 scan as the single remaining occurrence.
- v1.28: Design audit v21 (codex must 1; agy should 3): poll() before killpg, the AC-5.5 race driven by a real fixture with no mock, the AC-4.6 reap test's teardown waits on the handle it holds; poll-before-killpg-removed mutation (38 rows); FR-4 summary names three operational classes; extract's doc is a path.
- v1.29: Design audit v22 (codex must 2; agy clean + 2 nits): the binding rule (root, command, target_command, full node IDs) stated for all three specs; the AC-5.3 row is a real argv mutation; the wire spec's three mutations enumerated.
- v1.30: Design audit v23 (codex should 1; agy must 2 should 2): the two bounder-contract tests bind the tilde and indentation mutations; fence_aware_end's docstring states the full rule; _final_write flushes and closes inside the mapped region; O_EXCL creation detection; CLEANUP_FAILED os_error detail; the stale differential-test phrase removed.
- v1.31: Design audit v24 (codex must 1 should 1; agy nit): the AC-4.6 reap test's handle seam (recording Popen pass-through) and exact teardown order; stdout-first write-failure branch; body de-indentation in extract with body-indent-not-stripped (39 rows); the three-classes sentence lists three.
- v1.32: Design audit v25 (codex must 1 should 1; agy clean): two-arm create-or-open loop (exclusive create, else open without O_CREAT, ENOENT restarts) so every created file is recorded; one closure path for both reservations across every exit, with its test.
- v1.33: Design audit v26 (codex must 1; agy must 4 should 1): cwd is None until mkdtemp returns; simultaneous single-pass substitution with the replacement-sequential mutation; os.open wording in the exception and mutation tables; closer-trailing-text rule and mutation; docsections migration assigned to Task 1; six consumer-file tests; 40 rows.
- v1.34: Design audit v27 (codex must 2; agy must 2 should 2): substitution fixture discriminates the sequential mutant; artifacts are read back and compared after close (final-write-not-verified, 41 rows); StreamWriteFailed and LaunchFailed carry the fields the dispatcher prints; pgid on the reap verdict; seven-test floor tuple.
- v1.35: Design audit v28 (codex must 1 should 2; agy must 2 should 1 + nit): empty-map short-circuit with its mutation; duplicate info tokens refused; SUBST_MISSING keys=<n>; mutation accounting (41 source + 2 SKILL.md = 43 rows); Implementation Order names select, RunResult and every exact file path.
- v1.36: Design audit v30 (codex must 1 should 1; agy must 1 should 1 + nit): read-back compares bytes, never decoded text; fence_aware_end's prefix-state contract with test and mutation; test_docsections.py tracked in Components and Task 1; Task 3 names its exceptions, Task 4 the preamble read; four main/I-O mutation rows (48 rows).
- v1.37: Design audit v31 (codex must 2): missing keys listed in map insertion order with a multi-key test; RunResult.rc is the spawned invocation's exit code.
- v1.38: Design audit v32 (both surfaces clean; agy nit): the AC-6.1 cardinality test is named.
- v1.39: Design audit v33 (codex clean; agy must 1 + nits): the API prose lists BadSubstArg and BadTimeout.
- v1.40: Design audit v34 (codex must 1; agy must 1 + nits): exec-scan-executes, consumer-from-import and hand-rolled-extraction-widened added to the wire spec (six); stray line break in the setattr call joined.
- v1.41: Design audit v35 (codex must 1; agy clean): one private fence scanner, _fence_events, consumed by both extract and fence_aware_end — the fence-grammar mutations anchor in it and a construct-complete parity test runs every hostile fixture through both consumers.
- v1.42: Design audit v36 (codex must 1; agy clean): prefix fence state from whole lines through the line containing start, boundaries only after start; hostile mid-line fixture and the prefix-state-truncated-mid-line mutation (49 rows).
- v1.43: Plan re-audit v32 back-propagation: Task 5 and the wire-revert-extract row name _gate_block.
- v1.44: Design audit v38 (codex must 1; agy clean): backtick-in-info prohibition in _fence_events, measured on both renderers, with its mutation (50 rows).
- v1.45: Design audit v39 (codex must 1; agy must 1 should 1): the existing-file reservation arm opens O_NONBLOCK and every reserved descriptor must be a regular file (a reader-less FIFO refuses bounded), with two mutations (52 rows); the two post-Task-5 tests are authored in Task 5; the wire-revert-extract row names the tag-tolerant regex.
- v1.46: Design audit v40 (codex must 2; agy clean + nits): Popen passes cwd=cwd, with the cwd-not-passed mutation; the parity guard becomes a scanner event-trace test plus a no-fence-state source assertion on extract (54 rows); _gate_block returns dbe.Block.
- v1.47: Design audit v41 (codex must 2; agy clean): _final_write closes in a finally with the close error mapped in the same region, plus its mutation (55 rows); the reader-less-FIFO ENXIO behaviour is cited from a probe on python 3.11.8/darwin.
- v1.48: Design audit v42 (codex must 1; agy clean): final-write-close-not-in-finally is killed by an injected close failure — test_final_write_close_failure_is_mapped (close alone raises → mapped, no traceback) and test_final_write_failure_before_close_still_closes now injects flush AND close on a recording proxy handed through the _final_write seam and asserts the proxy's close was called, which the outer finally (holding the real handle) cannot produce; fifth injection reused, 55 rows unchanged.
- v1.49: Design audit v43 (codex must 1; agy must 1 should 1): _close_stream(handle) is the one closure primitive and a named injection (this entry said "the sixth"; the ordinal is struck under the seam-naming rule, which governs every reference in this document — it was also wrong, that seam being seventh in Test Strategy's list); main's backstop close records instead of raising and selects afterwards — StreamCloseFailed → UNREADABLE reason=stream_close_failed (exit 2, os_error:) outranks TIMEOUT, a pending exit-2 error outranks it (__context__); the three mapped OS-call regions of main stated as the class with its residual; indented-closer-accepted and stream-open-oserror-unwrapped mutations with their tests; 59 rows (57 + 2).
- v1.50: Design audit v44 (codex must 2 should 1; agy clean, low-evidence): the post-spawn taxonomy is five outcomes with stream_close_failed between LAUNCH_FAILED stage=reap and TIMEOUT; the AC-4.6 reap test binds real_killpg before patching the process-global os; artifact verification is per stream before the next write, with verify-deferred-past-second-write and the extended read-back test; 60 rows (58 + 2).
- v1.51: Impl-plan audit v2 back-propagation (codex must 4): the heading match runs over the scanner's prose lines only, with test_requested_heading_quoted_inside_a_fence_is_not_a_section_start and mutation heading-match-ignores-fence-state (61 rows: 59 + 2); Test Strategy states the transport split — seam-injected verdicts through main(argv) in-process, every real-input verdict through the subprocess, two subprocess tests pinning sys.exit(main()).
- v1.52: Plan re-audit v40 back-propagation (codex must 1): docsections.json carries a sixth row, docsections-syspath-setup-removed, killed by test_docsections_imports_from_an_unrelated_cwd in the new module.
- v1.53: Design audit v47 (codex should 1; agy must 1) + impl-plan audit v3 back-propagation (codex must 1): the docsections.json binding sentence names the sixth row's cross-file key; the wire spec has eight mutations — wire-revert-select and wire-revert-substitute killed by the existing pins, which now also spy dbe.select and dbe.substitute.
- v1.54: Design audit v48 (codex should 1; agy clean): run_recipe is hoisted to the module-level _run_recipe in the migration, named consistently in Implementation Order and the wire table.
- v1.55: Design audit v50 (codex must 1; agy clean) + impl-plan audit v5 back-propagation: the AC-5.5 escapee fixture is an esc.py under the test's tmp_path reached through the substitution map (ESC_PATH), never a file in the child's fresh cwd; the docsections-delegation-reverted mutant is expected to trip the docsections source guard, which is stated instead of 'helper suite still green'.
- v1.56: Impl-plan audit v6 back-propagation (codex should): the ATX heading grammar is stated (CommonMark 4.2 — 0–3 spaces, 1–6 hashes, space/tab/EOL, optional closing run), with test_heading_lookalikes_are_not_headings and mutation heading-lookalike-accepted (62 rows: 60 + 2).
- v1.57: Design audit v52 (codex clean; agy should 2): the AC-4.1–4.5 test row names LAUNCH_FAILED in the exit-2 class; the CleanupFailed row carries its os_error: detail line.
- v1.58: Design audit v53 (codex must 1 should 1; agy must 1) + impl-plan audit v7 back-propagation (codex must 1 should 1): scanner event model is open/close/body/heading/prose with level and candidate; the grammar is verified against markdown-it-py 2.2.0 (14/14, plan §Measurements); find_heading is public and docsections delegates the section start as well as its end (seven public names; docsections.json seventh row docsections-heading-lookup-reverted); the alias refusal leaves closing to the backstop so the injected-close test can hold.
- v1.59: Design audit v54 (codex must 2; agy must 1 should 1): the UNREADABLE verdict row carries stream_write_failed's detail lines; Implementation Order Task 1 lists _fence_events and find_heading.
- v1.60: Plan re-audit v46 (codex must 1 should 1) + impl-plan audit v8 back-propagation (codex must 2 should 1): the boundary predicate is start-offset >= start so an adjacent heading bounds the section (test_adjacent_heading_bounds_the_section, adjacent-heading-skipped; 63 rows: 61 + 2); the titled_section migration cited as a measured differential (new_only=0, old_only=76 fenced comments); one canonical test key for final-write-close-not-in-finally; _run_recipe passes timeout=60.0.
- v1.61: Design audit v57 (codex must 1; agy must 1 should 1) + plan v48 and impl-plan v9 back-propagation: find_heading accepts the full '## Text' (level-pinned) and bare 'Text' forms with test_find_heading_accepts_full_and_bare_forms / heading-level-pin-ignored; _FenceEvent carries start/end offsets; the drain records BlockTimeout (never raises in the handler); mktemp-invocation-planted, allow-abbrev-restored and stream-write-oserror-unwrapped rows (67 rows: 65 + 2); stream: detail on stream_close_failed; the grammar corpus cited on markdown-it-py 2.2.0 and 4.2.0.
- v1.62: Design audit v58 (codex must 1; agy clean): docsections-delegation-reverted is connection-only — a private spec_from_file_location instance of the callee replaces the shared import (measured on a scratch pair: the WIRE-PIN's recorders see [] under it, behaviour unchanged), so every other test stays green, the source guard included; the local-restore revert becomes an eighth row, docsections-local-bounder-restored, bound to the source guard (docsections.json 8 rows).
- v1.63: Design audit v59 (codex should 1 nit 1; agy clean) + impl-plan audit v10 back-propagation: the delegation spy test restores sys.modules and reloads docsections in a finally (pytest restores neither); the close-backstop precedence names every pending exit-2 error that wins over it, StreamWriteFailed included.
- v1.64: Design audit v60 (codex must 1 should 1; agy clean) + impl-plan audit v11 back-propagation: the ATX-only assumption is measured directly (Setext census: 30 files, 0 Setext headings) instead of inferred from the selector differential; the bare form's duplicate refusal is stated as a deliberate tightening over the old first-match with test_bare_form_duplicate_headings_refuse (live titled_section targets measured unique); the connection-only revert registers its private instance in sys.modules under a private spec name (dataclass processing needs it — AttributeError measured without).
- v1.65: Design audit v62 (codex must 1; agy clean): an OSError from the helper's own communicate, the post-kill drain, the pipe closes or the wait is LAUNCH_FAILED stage=collect (ranked with stage=reap; the child then killed and reaped as a timed-out one) with test_communicate_oserror_is_launch_failed_collect / test_drain_wait_oserror_is_launch_failed_collect and mutations collect-oserror-unmapped / drain-oserror-unmapped — 69 rows (67 + 2).
- v1.66: Impl-plan author contradictions after v1.65: the fault-injection list is seven seams (the collect stage's instance-level communicate/wait injection added); the exception table renders pgid on reap and collect, as the verdict table already did.
- v1.67: Design audit v63 (codex must 1 should 1; agy should 1, REFUTED — REPO_ROOT is parents[2] of the test file, the skills root, so `h-mad/tests/test_docsections.py` from it is right): heading identity is the CommonMark-normalized text (closing hash run and trailing whitespace stripped) on both forms — the earlier 'exact match' sentence contradicted the §Scanning rule — with test_closing_hash_run_does_not_change_heading_identity and mutation closing-hash-run-kept (70 rows: 68 + 2); the plan's run_block API row names the collect stage.
- v1.68: Impl-plan v1.15 back-propagation: the consumer-from-import row is one contiguous replacement at the call region (a from-import added beside the alias, every call bare) — the alias line and the call sites are not contiguous under a single str.replace.
- v1.69: Design audit v64 (codex should 1 nit 1; agy must 1) + impl-plan audit v15 back-propagation: the :412 text scan is named with its file; the diagram shows substitute's (Block', counts) tuple and RunResult; the reservation rollback is verified by an lexists read-back that reports `leftover: <path>` on the stream_path_unwritable verdict, with test_rollback_unlink_failure_reports_leftover, mutation rollback-leftover-unreported and os.unlink as the eighth named seam — 71 rows (69 + 2).
- v1.70: Impl-plan v1.16 back-propagation: the verdict and exception tables carry the `leftover: <path>` detail line and StreamPathUnwritable's leftover field.
- v1.71: Design audit v65 (codex must 1; agy clean) + impl-plan audit v16 back-propagation: the design's own verification commands are bounded through hmad-dispatch run (600 s scoped/harness, 1200 s full suite); StreamPathUnwritable is StreamPathUnwritable(leftover=None), raised from the OSError; the pre-kill poll() has its own OSError guard mapped to stage=collect (test_poll_oserror_is_launch_failed_collect, mutation poll-oserror-unmapped) — 72 rows (70 + 2).
- v1.72: Impl-plan v1.17 back-propagation: the TimeoutExpired handler records the pending BlockTimeout on entry, before poll(); the drain records nothing.
- v1.73: Design audit v66 (codex must 1; agy clean) + impl-plan audit v17 back-propagation: the post-kill wait is wait(timeout=DRAIN_SECONDS), its expiry LAUNCH_FAILED stage=reap with the pending outcome as __context__ (test_wait_after_kill_is_bounded; wait-unbounded, wait-expiry-unmapped — 74 rows, 72 + 2; helper wall time at most timeout + 2·DRAIN_SECONDS); one canonical eight-item fault-injection list — seven module seams plus the Popen instance wrapper for communicate/wait/poll — repeated by the in-process main(argv) sentence.
- v1.74: Impl-plan v1.18 back-propagation: test_wait_after_kill_is_bounded runs on the escapee fixture so the helper's own wait, not communicate's internal one, is the intercepted call; the two guards on that wait are separate except clauses.
- v1.75: Design audit v67 (codex must 1, 10 tool calls; agy clean): every dynamic field in a verdict or detail line passes through one escaper, `_field`, that escapes control characters, so no input can forge a second `DOCBLOCK:` line — test_newline_in_dynamic_fields_cannot_forge_a_verdict_line, mutation field-escape-removed — 75 rows (73 + 2).
- v1.76: Design audit v68 (codex clean; agy must 1 REFUTED — 2485 is the count from h-mad/, the 2747 baseline is from the repository root; pinned in the AC-6.4 row) + impl-plan audit v19 back-propagation: the forge test's leftover case uses a newline-named stdout path the first arm creates, a second-arm ENOTDIR and the os.unlink injection, since a first-arm failure creates nothing.
- v1.77: Design audit v69 (codex clean; agy must 2 at 42 tool calls — one REFUTED: the named tests and a 'Task 6' exist in no document; one held): main refuses an empty --subst key itself while building the map, with the raw argument, and substitute keeps the API refusal — the same predicate pinned twice (cli-empty-key-delegated added, 76 rows: 74 + 2).
- v1.78: Design audit v70 (codex must 1) + plan audit v61 back-propagation: dynamic fields are rendered as double-quoted JSON strings (json.dumps, ensure_ascii=False), so a printable value cannot forge a field token either — test_dynamic_field_cannot_forge_a_token, mutation field-quoting-removed (77 rows: 75 + 2); helper-constrained int/enum fields stay bare and the line grammar is stated.
- v1.79: Impl-plan v1.22 back-propagation: the bare-field list is exhaustive; seconds= and pgid: are quoted like every other non-listed field.
- v1.80: Design audit v72 (codex should 1; agy must 2 at 3 tool calls — int quoting held, the 'type-walk' phrase was this document's own error): _field stringifies before json.dumps so numbers are quoted; StreamPathUnwritable's zero-argument construction is justified by its raise site, not by a walk that instantiates nothing; every verdict/detail example rewritten in the quoted grammar (`heading="<h>"`, `os_error: "<text>"`, `written: "stdout"`).
- v1.81: Impl-plan v1.24 back-propagation: `key=` (BAD_INFO) and both halves of `overlap:` are quoted like every non-exempt field.
- v1.82: Design audit v73 (codex must 1 should 1; agy must 1 — held, measured): _field's second pass escapes Cc/Zl/Zp (DEL, C1 incl. U+0085, U+2028/9) with test_unicode_line_separators_cannot_split_a_verdict_line and c1-escape-removed (78 rows: 76 + 2); nonregular-stream-accepted is killed by test_stream_path_char_device_refuses (/dev/null opens, the fstat check is reached; a reader-less FIFO fails at open with ENXIO); inline examples in the quoted grammar.
- v1.83: Design audit v74 (codex nit; agy clean) + impl-plan audit v25 back-propagation: duplicate-heading-takes-first has one test key (the bare-form duplicate test is a regression test on the same guard); the Executive Summary names all seven public names.
- v1.84: Design audit v75 (codex must 1; agy must 1 at 16 tool calls) + plan audit v66 / impl-plan audit v26 back-propagation: six docsections.json rows bind into test_docsections.py (4 + delegation + heading-lookup), two into the new module's file; --subst =V prints arg="=V" under the quoted grammar; find_heading's two forms are told apart by the request (full form first), a title beginning with an ATX prefix is reachable only in full form — test_heading_form_precedence_full_wins, mutation form-precedence-bare-first (79 rows: 77 + 2).
- v1.85: Design audit v76 (codex must 2; agy must 1 on the impl-plan) + plan audit v67 / impl-plan audit v27 back-propagation: __all__ is 28 names (seven functions, two dataclasses, the exception hierarchy); argparse grammar errors are BAD_ARGS verdicts, exit 0 (test_malformed_invocation_is_a_verdict, argparse-error-unrouted); the full-form request predicate is the scanner's own (space, tab or EOL) with test_full_form_request_accepts_tab_and_eol and request-predicate-space-only; concurrent replacement of the caller's artifact path is a stated non-goal with an lstat/fstat identity check before the rollback unlink — 81 rows (79 + 2).
- v1.86: __all__ is 29 names once BadArgs joins the exception hierarchy (28 was counted before v1.85 added it).
- v1.87: Design audit v77 (codex must 1; agy must 1 at 13 tool calls): Task 5 unpacks substitute's (Block, counts) tuple before run_block; the two source-scan rows say the scan is green on the real helper and RED on the mutant (the earlier wording inverted it).
- v1.88: Impl-plan v1.29 back-propagation: the bounded-wait test's TimeoutExpired is constructed with cmd and timeout (a bare constructor call raises TypeError).
- v1.89: Impl-plan audit v29 back-propagation: allow-abbrev-restored's expected outcome is a BAD_ARGS verdict, not a usage error; the unreadable-preamble test is test_unreadable_preamble_path_refuses everywhere.
- v1.90: Design audit v79 (codex must 1; agy clean at 21 tool calls) + impl-plan audit v30: the reservation summary names the two-arm os.open protocol, not plain open(path, "a"); Task 1 is the wiring shape.
- v1.91: Design audit v82 (teammate surface, advisory — codex quota-blocked). MUST: the parser's exit_on_error=False cannot emit BAD_ARGS for a missing option value — it suppresses argparse's own except ArgumentError: self.error(...), so ArgumentError escapes main as a non-DOCBLOCK traceback, on one of the two inputs test_malformed_invocation_is_a_verdict drives; measured on 3.11.8 and independently re-probed. exit_on_error now stays at the default True, with the five-shape table and the residual (anything argparse raises outside error()) stated; argparse-error-unrouted becomes true as written at the default. __all__'s enumeration said 'every DocBlockError subclass — 29' where subclasses number 19 (7+2+19=28); it now names the hierarchy (base + 19) and calls out the 28 misreading.
- v1.92: Impl-plan v1.32 back-propagation (audit v33, teammate surface). AC-6.1's tree sweep is restricted to *.md, matching the plan census it is bound to. Unrestricted it counted the feature's own test-module fixtures (a column-0 tagged bash opener inside triple-quoted strings) as openers, so the AC could not pass at Task 5 GREEN and its stated RED reason was false; the residual is now stated. Also swept here what v1.91 missed: the AC-6.1-6.6 row still carried the stale 2747/2485 floor. It is 2748/2486 at e8eaf6f, with the commit travelling with the number and re-measurement required at 5c branch time.
- v1.93: Design audit v83, gating round, two surfaces (teammate must 2 should 4; agy must 1). MUST 1 (teammate): Task 5's split rationale was measured false and contradicted the paired plan one revision after plan v1.84 corrected it — tagging the gate fence leaves :270's re.findall matching 3 of the section's 4 blocks, not zero; re-measured independently at 1861157 (before 4 blocks/1 gating, after 3/0), and the loud failure is _gate_bash_block's assert gating, since what empties is the h_mad_audit_gate.py filter. MUST 2 (teammate): every heading measurement cited a 30-file *.md corpus that is 25 tracked files plus 5 untracked, gitignored .pytest_cache/README.md artifacts, each carrying '# pytest cache directory #' — five instances of the closing-hash softening the document claims has none, so the Guard-narrowing accounting was false and files=30/old_only=76/setext_headings=0 were reproducible only after pytest had run. The corpus is now defined as git ls-files -- h-mad handoff filtered to *.md with archive/ excluded (25 files); re-measured at 1861157: new_only=0, old_only=76, setext_headings=0, both softening shapes 0 over the 25 and 5 closing-hash over the 30. AC-6.1's sweep states a dot-directory exclusion (a test must still count a newly written untracked doc, which git ls-files would miss) and its residual now names generated .md inside the roots. MUST 3 (agy): run_block and main in the API block lacked trailing colons — two invalid-Python signatures; both now carry a colon and a docstring sourced from this document's own contract, and all 3 python fences ast.parse (2 of 3 at 1861157). SHOULD: the Single-source contract is added to Invariant Compliance, naming the three test-local ##-slicers the consumer census cannot see, which branch covers them and why (measured: _titled_section is not a drop-in — titled_section cannot find 'Run-context ceiling'), and stating that after Task 5 _second_surface() leaves the executing path; the convention deliverable's AC-6.1 exposure gets its sentence at the residual. NIT: run_recipe -> _run_recipe on the post-migration executing path. MUST 4 (team lead, from plan-author): the prose contradicted the mutation matrix on the 81-row split, and this document was the origin the plan and impl-plan copied. Re-derived by counting the matrix's mechanism column at 1861157 rather than reading it: two mutation tables, the wire table at 8 rows (0 naming SKILL.md) and doc_block_exec.json at 81 rows of which exactly 1 names SKILL.md as the file the harness edits (registry-row-removed). The split is 80 + 1, not 79 + 2. Its AC-4.5 partner detail-line-undocumented mutates the HELPER (missing_key: -> absent_key:), so the pair is one by AC and not by file; a \"file\": \"h-mad/SKILL.md\" anchor on it would be an anchor the harness refuses. Fixed at the two sites named (the deliverables cell and the summary paragraph under the matrix) and at a THIRD the sweep found and the brief did not: Task 4's Implementation Order called them \"the two SKILL.md mutation rows\". Each site now states how the split is derived so the next reader re-counts. Owed elsewhere and routed, not edited here: the plan's Measurements still says files=30, the spec's AC-6.1 reaches its scope by reference to that census, the impl-plan pins the 2748 floor at b7d0d77 where three documents pin e8eaf6f, and the impl-plan's AC-6.1 sweep is spelled as a bare filesystem glob.
- v1.94: Design audit v84, gating round (teammate must 2 should 3 nit 2; agy clean at 13 tool calls and MISSED both musts, so not treated as corroboration). MUST 1: the Guard-narrowing corpus was stated as the figure 25 and its softening set was not closed as a class. Re-measured at a8e0372 over the tracked corpus (git ls-files -- h-mad handoff, *.md, archive/ excluded): files=30, glob=35, old_only=82, new_only=1 -- so the 30 that once marked the CONTAMINATED glob is now the TRACKED count and a bare figure now agrees for the wrong reason. Control at 1861157 returns files=25 old_only=76 new_only=0, reproducing this document's own earlier numbers, so only the tree moved. The corpus is now stated as a runnable command, never a figure. The softening set is closed by DERIVING it from the old guard's own pattern (h-mad/tests/docsections.py titled_section: re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$")) token by token rather than from a model of ATX -- enumerating the tokens enumerates the class, since a divergence has nowhere else to live. That gives FIVE softenings, not four: leading 1-3 space indent (0), tab delimiter (0), EMPTY TITLE (1), two-or-more spaces before the title (0, missed by the earlier grammar-shaped enumeration because re.escape(heading) sat flush against one space), and the closing hash run (0 tracked / 5 on the 35-file glob) -- plus one TIGHTENING (a 7+ hash run, which #+ accepted and #{1,6} refuses; 0 instances) and one NON-divergence (trailing whitespace, which \s*$ already tolerated), both rowed so the reader does not hunt for them. The mechanism column separates recognition softenings (the only ones that can appear in new_only) from the two title-comparison softenings (which cannot). Both differentials were re-run with the bounder's narrower ^#{1,6} shape and give the same old_only=82/new_only=1, so the figures do not depend on which of the two old guards is meant. The one live instance is the bare # line in h-mad/SKILL.md sitting alone outside any fence above the '## Reading a dispatch verdict' heading, introduced by bea1b60 and confirmed a real <h1></h1> by markdown-it-py 2.2.0 CommonMark. Residual: a further member needs either the old pattern to change (it is deleted by this feature) or CommonMark's ATX rule to change under the pinned oracles -- an oracle version bump, not a document drift. MUST 2: Task 5's block census was a behavioural premise with no command and had gone stale (6db8e50 inserted '## Teammate audit leg' between _section's two string anchors, growing the span 50->159 lines). The number is replaced by a one-physical-line command (heredoc-free on purpose: the fence is indented inside a list item) whose output at a8e0372 is 'lines 159 blocks 7 gating 1', tagging leaves 6/0, and at 1861157 gave 50/4/1 -> 3/0. POSITIONS ARE DROPPED ENTIRELY in favour of the CONTENT PREDICATE each block is actually addressed by (_gate_bash_block filters on "h_mad_audit_gate.py" in b and asserts exactly one; the untouched scan filters on "exec codex" in b and takes the first) -- a positional claim would describe something the code does not do, which is how this sentence went stale. The ambiguity was live, not theoretical: two independent re-derivations of this census named the SAME two blocks under different base conventions (0-based 1 and 3 = 1-based 2nd and 4th), so a bare "index N" is off by one depending on the reader. Both censuses are re-derived here from the git blobs at both shas rather than carried. The v1.93 conclusion is unchanged -- _gate_bash_block's assert gating is still the loud failure, not an empty findall. SHOULD: Task 5 now states the MAGNITUDE of the address narrowing (executor span 50 lines/4 blocks vs the named-anchor 159/7), that exactly one of _second_surface()'s eight call sites migrates (the one inside _gate_bash_block; the other seven are named test functions). Those sites are located by ENCLOSING SYMBOL, not by line: the eight line pins the finding used are replaced by an ast one-liner that prints the enclosing symbol set, since a line pin goes stale on any insertion above it and gives no signal that it has. It also states that the gate fence falls inside both spans today, and the exact residual (an h_mad_audit_gate.py-bearing fence added under a later ## section would be visible to the seven survivors and invisible to the executor). The closing-hash-run delimiter is corrected from space-only to spaces-or-tabs at both sites, closing the same axis request-predicate-space-only closes on the opening delimiter (oracle: markdown-it-py 2.2.0 renders '## Text\t##' as <h2>Text</h2>); test_closing_hash_run_does_not_change_heading_identity's fixture gains the tab form, with the measured residual of 0 tracked instances. Invariant Compliance's pointer to the plan now names the CORPUS and the owed action rather than a figure. NIT: the eight fault injections are named, never numbered, since an ordinal drifts whenever the set is reordered; the count-rule sentence renders index/value/seconds quoted to match the verdict table. SHARED CORRECTION, verified independently and by probe: AC-6.4's '+ 7' is short by two and is now + 9. h-mad/tests/test_h_mad_portable_timeout.py builds _SCANNED at module level from sorted((SKILL/'scripts').glob('*.py')) and parametrises TWO tests over it with ids=lambda p: p.name, so Task 1's h-mad/scripts/h_mad_doc_block_exec.py collects test_no_document_or_script_emits_a_bare_timeout_command[h_mad_doc_block_exec.py] and test_no_document_or_script_rests_on_an_unconditional_absence_claim[h_mad_doc_block_exec.py]. Measured with a one-line stub at that path: pytest --collect-only -q gains exactly 2 node IDs and no others; every other glob under h-mad/tests and handoff/tests that could see the feature's new files iterates inside a test body rather than feeding a parametrize -- checked rather than assumed for the mutation-spec directory, where this feature lands two .json: test_h_mad_mutation_harness.py has ZERO parametrize decorators and calls both of its spec-globbing helpers from inside test bodies, so the new specs collect nothing. The rule over the axis is now stated: the addend is every node the change COLLECTS, not every node it WRITES. Owed elsewhere and routed, not edited here, each checked against the tree at the time of writing: the plan's Measurements pins its differential at 1861157 (files=25 both=263 old_only=76 new_only=0 -- which reproduces this document's control exactly, so its method is sound and only its sha is behind) and owes the corpus DEFINITION plus a re-measure at HEAD, where its 25/30 pair becomes 30/35 and the bare 30 would otherwise agree with a fresh git ls-files for the wrong reason; the plan (3 sites) and the impl-plan (5 sites) still carry the seven/+7 count and owe the correction to nine. The spec carries NEITHER -- its FR-6 already states seven bash blocks and it holds no +7 -- so no census or count fix is owed there. **[Superseded by v1.95, and left otherwise intact as the dated record it is.** The `+ 9` this entry landed and the "owe the correction to nine" it routed to the plan and impl-plan are both withdrawn: the assertion is `+ len(tuple)` in every document, a total is permitted only as a dated evaluation carrying its sha, and no document owes a literal to any other. The three sites this entry names in the plan and impl-plan are not a debt. Also withdrawn from this entry: "a positional claim would describe something the code does not do" was too strong — the ordinals are true and re-derivable, only the *selection* is by content predicate. See v1.95.**]
- v1.95: Design audit v85, gating round, two surfaces (teammate must 3 should 3 nit 2; agy must 2, independently corroborating the floor-tuple count contradiction). Every premise below re-derived at 335f535, and a single sentence now states WHY the a8e0372 figures still hold: git diff --name-only a8e0372 335f535 names two files, both .py, so the *.md corpus (h-mad/SKILL.md included) is byte-identical between the shas. MUST 1 (both surfaces): AC-6.4 carried a hand-written total. The assertion is now full_collected >= baseline + new_module + len(tuple); len(tuple) occurred 0 times in this document and now carries the arithmetic. Membership is spec AC-6.4's rule, attributed by locator and not re-worded; what this document owns is the EMPIRICAL EVALUATION, stated as a dated one -- evaluated at 335f535 the rule yields a nine-member tuple, seven authored and two collected. The Components row's 'seven floor-tuple node IDs' and Task 5's 'nine-node tuple' are both replaced by 'the floor tuple'. The stub probe is not re-run (other authors hold the tree); instead the standing cheap check is published and run: grep -c 'parametrize("path", _SCANNED' test_h_mad_portable_timeout.py -> 2, grep -c parametrize -> 0 on test_h_mad_mutation_harness.py and handoff/tests/test_mutation_specs_clean.py, and the diff since a8e0372 names exactly one test file (test_h_mad_assemble_audit.py) whose single parametrize is over a two-element LITERAL list, so no glob-driven parametrize has entered. v1.94's '+ 9' and its 'owe the correction to nine' routing to the plan and impl-plan are withdrawn by a bracketed supersession on that entry. MUST 2: the absolute 'a positional claim about them would describe something the code does not do' is softened to what the mechanism actually supports -- neither block is SELECTED by position; the content predicate is what the code uses and what the tag replaces. An ordinal is informational and TRUE, and the rule over the axis is that it must name BOTH halves of its base: the index convention AND the span. Re-derived at 335f535 with enumerate(b, 1) over the 7 blocks of the named-anchor span, gate=4 and exec-codex=2; over the 4 blocks of the executor's AC-1.5 span the same two ordinals come out 4 and 2, so the spans coincide on this tree by coincidence, which is why the span half has to be stated. MUST 3: the closing-hash-run widening to spaces-or-tabs is kept (oracle re-run at 335f535: markdown-it-py 2.2.0 renders '## Text\t##' as <h2>Text</h2>) and its residual is now exact -- ATX has exactly two #-run delimiters and both are spaces-or-tabs, so the axis has no third member; the fence info-string production is a different grammar. The impl-plan's two prose delimiter statements and its test_closing_hash_run_does_not_change_heading_identity fixture row are named as the routing target WITHOUT asserting what that document currently holds. SHOULD 1: the differential fence now carries BOTH old guards two characters apart (FINDER ^#+ , BOUNDER ^#{1,6} ) and prints one self-labelled line each, so the equality the prose asserts is a run; extracted from the edited document and executed verbatim at 335f535 it prints 30 / 35 / 'finder ^#+ files 30 both 292 old_only 82 new_only 1' / 'bounder ^#{1,6} files 30 both 292 old_only 82 new_only 1', each followed by the same single new_only identity (h-mad/SKILL.md, titleless). The mislabelled comment ('the fence-blind guard being replaced' on the BOUNDER) is gone. SHOULD 2: the locate-by-enclosing-symbol rule is closed as a class instead of applied at one site. Every line pin outside Version History is converted -- :412 at three sites (Task 5 prose, the AC-6.4 cell, the exec-scan-executes mutation row) to test_exec_codex_dispatch_carries_out_log_and_timeout, :270 to _gate_bash_block, and the three Invariant-Compliance pins to their defs. Verified by a published awk check that splits the corpus at the Version History heading and greps the head: 0. Version History is exempt for LINE PINS ONLY, because its entries are dated records; the seam-naming and ordinal-base rules are NOT exempt there. Residual on the symbol locator stated: it cannot distinguish two defs of one name, and it goes stale silently on a rename -- a changed name SET, not a changed line, is the signal. SHOULD 3: the '14 of 14' grammar-oracle premise is declared not re-derivable in those words -- grammar_corpus.py is untracked (git ls-files | grep -c grammar_corpus -> 0) and 4.2.0 is on no local interpreter (only python3.11 carries markdown-it-py, at 2.2.0). A cheap proxy is published in its place and run verbatim from the edited document: eleven ATX shapes rendered on the local oracle, all agreeing with the grammar this document states. Its residual is exact -- the proxy covers the ATX heading production only; the fence grammar and the Setext census carry mutation rows instead, and no oracle-render evidence for them survives here. NIT 1: 'Each seam is named, never numbered' moves to the HEAD of Test Strategy, ahead of both enumerations, and its rationale is now demonstrated rather than asserted -- the two enumerations in that section list the same eight seams in different orders. The one live ordinal ('the sixth named injection' for _close_stream) is struck; it was drifting AND wrong, that seam being seventh in the Test Strategy list. v1.49's ordinal is struck the same way. NIT 2: the <h1> claim is narrowed to 'exactly one EMPTY <h1></h1>' -- the file renders two <h1> elements, the other being the document title. OWED ELSEWHERE, routed and not edited here: the impl-plan's three closing-hash-delimiter sites (two prose, one fixture row). NOT owed: no document owes a floor-tuple literal to any other, which reverses v1.94's routing. **[Two factual claims in this entry are corrected by v1.96, and the entry is otherwise left intact as the dated record it is. (1) "git diff --name-only a8e0372 335f535 names two files, both .py" is FALSE as written: unscoped, that diff names 13 files, 11 of them .md. The conclusion holds only under the SCOPED form `-- h-mad handoff`, which names exactly the two .py; all 11 .md are under docs/, outside both corpus roots. Version History is exempt for line pins, never for factual claims, which is why this correction sits here rather than only at the body site. (2) "the seam-naming and ordinal-base rules are NOT exempt there" was a rule this entry stated and did not apply — it struck one Version History ordinal (v1.49's) and left four standing (v1.12, v1.23, v1.48, v1.69). v1.96 scopes the seam-ordinal ADDRESS prohibition to outside Version History and states why the exemption cannot be avoided by striking; the ordinal-base rule remains non-exempt.]**
- v1.96: Design audit v86, gating round (teammate must 2 should 2 nit 2). Every figure re-derived at 74e126f. MUST 1: the published sha-equality command's stated output was FALSE and the document's own trip-wire fired on its own tree -- unscoped, git diff --name-only a8e0372 74e126f names 13 files, 11 of them .md. The command is now SCOPED to the two roots the corpus is drawn from (-- h-mad handoff), which names exactly the two .py, and the reason the conclusion survived unscoped is now stated rather than left implicit: all 11 .md are under docs/, outside both roots. The unscoped form is explicitly demoted -- it fires on every revision of this document and would train a reader to ignore the trip-wire. The identical false claim in the v1.95 Version History entry is corrected by a bracketed note there, since Version History is exempt for line pins only, never for factual claims. The 335f535 figures are closed as a CLASS in the same paragraph: git diff --name-only 335f535 74e126f -- h-mad handoff is EMPTY, so the five remaining 335f535 dates below are records of when each was run, not stale pins; three of the five were re-run anyway at 74e126f (eleven-shape ATX proxy, closing-hash-run oracle, _second_surface ast one-liner) and reproduce exactly. MUST 2: the seam-ordinal rule was closed as a class instead of one member at a time. Both surviving ordinals in Error Handling Strategy are struck -- os.unlink 'the eighth named seam' becomes 'the os.unlink fault injection', _final_write 'the fifth named injection' (the stale v1.23 ordinal) becomes 'the _final_write fault injection' -- and the two cardinality phrasings beside them ('a ninth seam', 'add no sixth') are reworded to 'an additional seam' and 'add no new seam' so that the published check has NO expected exceptions. The check is published at the head of Test Strategy and run: awk-split at the Version History heading, grep -cE over the ordinal-x-seam pattern -> 3 on v1.95 and 0 on v1.96, which is its own positive and negative control on this file. Residual stated exactly and in two numbered items: (1) Version History is exempt for ordinals as well as line pins, and v1.49's strike annotation is the proof the exemption cannot be avoided by striking, since it must quote the ordinal it struck -- as must every later entry that reports one, this one included. How many entries carry one is therefore DERIVED, never listed: the same pattern run over the tail (one entry per line) returns 7 at v1.96, and it grows by one each time a revision records a strike. This narrows v1.95's blanket 'not exempt there', a rule that revision stated and did not apply. The ordinal-BASE rule remains non-exempt. (2) A cardinality statement is not an address and is permitted in principle, but this document now carries none, so the expected output is a bare 0 and any hit is a finding. SHOULD 1: the Setext census gets the same honesty treatment '14 of 14' got. Its cited script heading_differential.py is untracked (git ls-files | grep -cE 'heading_differential|grammar_corpus' -> 0) and the plan's transcript is pinned at a different sha (1861157, files=25/30), so neither the cited run nor a re-run of it was re-derivable. A runnable fence replaces the citation and was executed verbatim from the shipped file: 'tracked files 30 setext_headings 0' / 'glob    files 35 setext_headings 0'. Both controls were run before the count was published (decision E): a positive fixture with one === and one --- heading returns 2, a negative fixture with a thematic break, a fenced underline, a list-item underline and a table delimiter row returns 0. Rule over the axis: every measurement must publish its command inline or name a script git ls-files can find. Residual: this census and the ATX proxy close the axis for the only two untracked scripts ever cited here. SHOULD 2: the awk line-pin detector now states its OWN residual -- it matches a filename-shaped token with an extension followed by colon-digits, and a backticked colon-digits, and is blind to the word line/lines plus a number, an L-prefixed number, and colon-digits not preceded by a filename-shaped token. Those three blind forms were swept separately at 74e126f over the same head-of-document corpus and the only hits are the two 'lines ...' fields of the block-census OUTPUT, a printed count and not a locator. NIT 1: the two wc -l lines in the differential fence gain | tr -d ' ' with the reason inline (BSD wc right-pads to six columns, GNU does not), so the verbatim block below is byte-exact on both platforms; the whole fence was extracted from the shipped file and re-run at 74e126f and prints that block byte-for-byte. NIT 2: the ~1,100-word AC-6.1-6.6 Test Plan cell is split -- the floor-tuple empirical evaluation moves out to a wrapped prose block beneath the table titled 'The floor tuple, evaluated', with the cell pointing to it; the cell is now 837 words. The evaluation is re-derived at 74e126f rather than carried: the three standing parametrize counts are still 2/0/0 and the diff since a8e0372 still names exactly one test file. OWED ELSEWHERE, reported and not edited here (decision F): v1.95 added a second occurrence of the four-word phrase the impl-plan uses as its needle into this document (the ordinal-base rule in Task 5's prose), taking that needle from 1 matching line at 335f535 to 2 at 74e126f and breaking a locator that was unique when it was written. Counts confirmed here, edited nowhere else; the impl-plan author is re-needling to a longer form. The needle itself is DELIBERATELY not quoted in this entry -- quoting it would add a third matching line and break the re-needling too, which is the same defect one level down. **[Two claims in this entry are corrected by v1.97; the entry is otherwise left intact as the dated record it is. (1) "unscoped, git diff --name-only a8e0372 74e126f names 13 files, 11 of them .md" is FALSE. Re-derived at 35698f9, that command names 18 files, 16 of them .md; 13/11 is the a8e0372..335f535 measurement, which v1.95's bracketed note above quotes CORRECTLY and which must not be "fixed". The pair moves with every revision of docs/, so v1.97 stops publishing a pair at the body site and publishes the invariant the argument rests on instead. (2) "3 on v1.95 and 0 on v1.96, which is its own positive and negative control" mislabels the control. A 0 on the current file is not a true negative — it is the state under test. The 3 was also a demonstrated FALSE NEGATIVE: v1.95's head carried four ordinal-plus-noun instances and the line-scoped pattern saw three, missing one the hard-wrap had split across a newline. v1.97 replaces the check with a fold-and-strip pipeline, publishes a real true-negative fixture, and states the residual.]**
- v1.97: Design audit v87, gating round, but only ONE surface produced evidence: the agy leg scored UNVERIFIED (reason=low_evidence, 1 tool call) and its "Must-fix None" is not corroboration, so nothing here rests on it. Every figure re-derived at 35698f9; none carried from the report or from the round-six decision sheet. Stated once instead of re-stamping every dated figure: git diff --name-only 74e126f 35698f9 -- h-mad handoff is EMPTY, so every CORPUS-DERIVED and SCOPED-DIFF figure dated a8e0372 or 74e126f is byte-identically derivable at the audited sha, and that sentence now sits in the same paragraph as the a8e0372 closure. The qualifier is deliberate and no count of the stamps is published: an empty TREE diff says nothing about a figure measured on THIS DOCUMENT's bytes, and this document changed, so the document-self figures (the seam-ordinal before/after pair, the line-pin blind-form sweep) each carry a 35698f9 re-run beside their 74e126f stamp instead of relying on the closure. The heading-differential fence was likewise extracted and re-run at 35698f9 and its stamp now names both shas. MUST 1: the unscoped-diff figure was the a8e0372..335f535 measurement carried into a sentence about a8e0372..74e126f. Re-derived: that command names 18 files, 16 of them .md, and at 35698f9 it names 25 and 23 -- so the published pair was never right at its own sha, and a reader who re-ran it got a third number. The pair is no longer published as the trip-wire anywhere in the body. What is published is the invariant the argument actually rests on -- git diff --name-only a8e0372 <sha> | grep '\.md$' | grep -vc '^docs/' -> 0 -- that exact three-stage command run and confirmed 0 at 335f535, at 74e126f and at 35698f9, with the three pairs named once in a single parenthesis to show why a pair is the wrong thing to pin. The v1.95 bracketed note that quotes 13/11 for a8e0372..335f535 is CORRECT at its own sha and was deliberately NOT touched; the identical false claim in the v1.96 entry is corrected by a bracketed note there, Version History being exempt for line pins only and never for factual claims. MUST 2: the seam-ordinal detector was published as proof the class is closed while carrying two unstated blind forms, one of them demonstrated on this document's own bytes. (a) grep is line-scoped and this file hard-wraps at ~95 columns, so an ordinal the wrapper separated from its noun scored 0: v1.95's head held four ordinal-plus-noun instances and the published line-scoped pattern printed 3, a FALSE NEGATIVE, which the v1.96 entry cited as its "negative control" -- inverting the meaning of the control. (b) the gap was [^.]{0,60} and seven of the eight seams are dotted module paths, so the natural phrasing for this very set scored 0 (fixture run: 0 under the old pattern, 1 under the new). The check is rebuilt as a three-stage pipeline -- split at the Version History heading, strip fenced code with a RUN-LENGTH-aware fence tracker, fold paragraphs, then match with a gap that admits a dot inside a token and stops at a sentence break -- and shipped as shell variables so the alternation is written once. grep -o | wc -l | tr -d ' ', not grep -c, because after the fold a paragraph is one line. The head returns 0, and beside it THREE controls, all executed from the shipped file: v1.95 blob 4 (positive, and the gap against the old form's 3 IS the wrap blindness); the dotted+wrapped fixture 1; a true-negative fixture carrying both admissible cardinality phrasings and two block ordinals with their base 0 -- a non-member the screen DECLINES, which is what the earlier "negative control" was not. A fourth run pins the fence-strip: dropping it turns the head's 0 into 1, that hit being the alternation's own source. The residual grows from two items to three: the third states that the screen is proximity-based and therefore a hit is a CANDIDATE, not automatically a defect, and names both directions -- it over-matches an ordinal over some other set landing inside the gap, and under-matches a digit-suffixed ordinal, a noun outside {seam, injection, primitive}, and a gap over 60 characters. Item 2's absolute "any hit is a finding" is withdrawn on that evidence. The class rule is stated over the axis rather than at the instance: a detector whose target can contain a space folds and strips first; one whose target is a single whitespace-free token need not, because no hard-wrapper can split one. The line-pin detector is the second member of that class and is settled by measurement rather than by assertion -- a space-tolerant, folded variant is published and returns 0 at 35698f9, and its own residual (it would also match prose of the shape "<name>.py: 30 files") is stated, so the strict line-scoped fence remains the rule-carrying one. Its three previously-swept blind forms were re-swept at 35698f9: same two hits, both the block-census OUTPUT's "lines ..." fields. MUST 3: two sites contradicted each other on how many Version History entries quote an ordinal, and the wrong one was spelled as an English word, invisible to a digits-only sweep. The Invariant Compliance prose said five; the derived command returns 8 against the 35698f9 blob under the new pattern and returned 6 against the 74e126f blob under the old one, so "five" was never right. The prose figure is DELETED and points at the command; no count of those entries is written at that site. The number is republished where the command lives as a screen result rather than a cardinality: seven of the eight are entries recording an ordinal over the fault-injection set and one (v1.76) is an ordinal over the two arms of a cleanup path that merely lands inside the gap -- named so the next reader does not chase it, and kept as the demonstration of why the number is derived. The tail command is deliberately NOT folded, because a Version History entry is one unwrapped line and folding would merge entries. MUST 4: the Single-source compliance claim was scoped by a closed enumeration of "three further hand-rolled ##-slicers", and the class is open. It is now a SCOPE RULE plus a runnable AST sweep and NO cardinality -- the same treatment the impl-plan reached for its own residual, and adopted here because two differently-wrong predicates agreed on one number, which is exactly the failure a cardinality hides. The sweep prints 22 lines at 35698f9 and that is labelled as ITS output, with over-count members verified by reading each body at 35698f9 rather than by carrying the report's word for it (traced_bindir and run_with_bindir in test_hmad_dispatch_audit_cycle.py hold their ## inside a stub audit-report STRING; main in h_mad_audit_gate.py in a COMMENT; main in h_mad_wire_pin_gate.py in an ERROR MESSAGE -- none slices) and one verified under-count member (def _section in test_h_mad_collect_report_docs.py, whose ## anchors arrive as parameters). The consumer census's blindness is stated by construction: only three files in the two roots import docsections at all. The three walked members are relabelled "three examples", the 8 call sites of _titled_section are given with the command that derives them, and "all three are fence-blind" is scoped to those three and immediately falsified for the class by two verified fence-AWARE members (def _section in test_h_mad_pane_visible_dispatch_docs.py and def _section in test_h_mad_context_budget_docs.py, each with a comment saying why). The residual is stated exactly, not as "and similar": the unwalked members are UNEXAMINED against the compliance conclusion, not found compliant by it, and what would falsify the scope rule is a slicer two surfaces call. SHOULD: the Setext census's fence tracker closed a fence on the marker CHARACTER alone, so a three-backtick line inside a four-backtick fence ended it and the rest of the file was scanned as prose -- the exact shape AC-1.6 exists for, and the shape the published negative control did not cover. Fixed by keeping the opener's RUN and requiring a closer at least as long (CommonMark 4.5). Direction of the old bug was safe, so no figure moved and none was re-stated on trust: the edited fence was extracted from the shipped file and re-run at 35698f9, printing "tracked files 30 setext_headings 0" / "glob files 35 setext_headings 0" byte-for-byte, and all three controls were re-run against the SHIPPED census() rather than a paraphrase -- positive 2, true negative 0, nested-fence fixture 0 where the old tracker returned 1. The earlier negative control is NOT relabelled: it was a sound true negative, it simply did not cover the shape AC-1.6 exists for. A two-arm residual on census() is added (no info-string model, so an info-string opener of the same character and no greater run reads as a closer -- same safe direction, corpus 0; and a fence indented past column 3, e.g. inside a list item, is not recognised at all). NOT edited, and deliberately: the report's third should-fix is marked "Not a defect -- recorded" and needed no change; its constraint on the MUST 2 fix is discharged by the fence-strip stage above. OWED ELSEWHERE, reported and not edited here: nothing new. The differential fence was also re-run verbatim at 35698f9 while the file was open and still prints finder/bounder 30 / 292 / 82 / 1 with the same single new_only identity. **[Two claims in this entry are corrected by v1.98; the entry is otherwise left intact as the dated record it is. (1) "seven of the eight seams are dotted module paths" is FALSE -- five of the eight are. Re-derived at 6f0ee85 from this document's own canonical taxonomy, by folding the document and counting dots in the parenthesised enumeration: os.killpg, shutil.rmtree, tempfile.mkdtemp, os.chmod and os.unlink are dotted, _final_write and _close_stream are not, and the remaining member -- the instance-level Popen wrapper -- is not a module path at all. The clause was reproduced word for word from the v87 report that raised the finding. (2) "none carried from the report or from the round-six decision sheet" is therefore FALSE for that one figure. A 6-gram screen over this revision's added lines against the report it answers prints 23 shared runs at 6f0ee85: 22 are commands, sha pairs, fixture descriptions and quotations of the finding, which a Version History entry is meant to transcribe verbatim, and the twenty-third is that clause. The four other figure-bearing runs were re-derived and all four hold -- 18/16 for a8e0372..74e126f, 13/11 for a8e0372..335f535, and exactly 3 files under the two roots importing docsections. Everything else in this entry re-derives at 6f0ee85 unchanged.]** **[The bracket immediately above is itself corrected by v1.99, and is left in place as the dated record of what v1.98 claimed. Its "22 are commands ... and the twenty-third is that clause" is wrong on the axis the bracket was written to close: the shipped screen prints the dottedness clause TWICE across the added lines of 35698f9..6f0ee85 -- git diff 35698f9 6f0ee85 -- $D | grep '^+' | grep -c 'of the eight seams are dotted' returns 2 at cf3a862, needle cut short of the wrong figure on purpose -- so the decomposition is 21 + 2. "The four other figure-bearing runs" is not derivable from the screen either; with the numeral word list the screen now carries, the counts are 3 figure-bearing of 8 BODY runs and 8 of 15 VERSION HISTORY runs. The three facts that sentence names do all still hold at cf3a862: 18/16 for a8e0372..74e126f, 13/11 for a8e0372..335f535, 3 files under the two roots importing docsections while 5 mention it.]**
- v1.98: Design audit v88 at freeze sha 6f0ee85, gating round. Both must-fixes were NEW-IN-v1.97 TEXT; that this is the fifth such round running is the orchestrator's count from the round-eight decision sheet, carried as process context and not re-derived here. MUST 1: the site justifying the dotted-gap control published "seven of the eight seams are dotted module paths", a clause reproduced WORD FOR WORD from the v87 teammate report, while the v1.97 entry claimed no figure was carried. Both statements are false and both are corrected. The true value is FIVE of the eight, derived at 6f0ee85 rather than quoted, with the derivation command shipped inline: fold the document, pull the parenthesised canonical taxonomy, count members carrying a dot -- os.killpg, shutil.rmtree, tempfile.mkdtemp, os.chmod, os.unlink dotted; _final_write and _close_stream not; the instance-level Popen wrapper not a module path at all. Most of the set is still dotted so the control the clause justifies is unchanged; only the figure moves. Closed as a CLASS, not as the instance: a number appearing in an audit report is not a measurement until this document re-derives it, because a report is written by a reader of this document and a figure quoted back out of it is this document own claim returned unchecked. A mechanical screen is shipped and RUN -- tokenise a revision added lines and the report it answers, print every run of six or more shared consecutive tokens. For 35698f9..6f0ee85 against the v87 report it prints 23 runs: 22 are commands, sha pairs, fixture descriptions and quotations of the finding, all of which an entry is meant to transcribe verbatim, and the 23rd is the dottedness clause. The wrong clause is deliberately NOT re-quoted at the body site -- quoting a wrong figure in order to report it puts the wrong figure back in the body. The four other figure-bearing runs were re-derived and ALL FOUR HOLD: a8e0372..74e126f names 18 files / 16 .md, a8e0372..335f535 names 13 / 11, and exactly 3 files under the two roots import docsections. RESIDUAL stated exactly: the screen finds carried TEXT, so a figure retyped in different words passes it in silence, and the only screen for that is a derivation command standing beside the figure; the screen is also scoped to ONE report, so a figure carried from a sibling document is a decision-E matter it does not measure. MUST 2: "The corpus has none of either" covered both arms of the census residual in one sentence, was reasoned rather than run, and is FALSE for arm (2). Rebuilt as a per-arm DIFFERENTIAL -- the shipped census() beside a variant with that one arm repaired -- each with a POSITIVE CONTROL that moves it, because a 0-versus-0 over a shape the corpus never contains proves nothing, plus a third column counting how often each arm is REACHED. Run at 6f0ee85 on python 3.11.8 / darwin 25.6.0: controls arm1 1->0 and arm2 1->0; tracked 30 files and glob 35 files, headings 0 under all three screens, arm 1 reached 0 lines, arm 2 reached 8 marker lines forming 4 fences in 2 files (h-mad/SKILL.md and handoff/SKILL.md, every one a fence opened inside a list item -- that last part verified by READING the surrounding context of both files, not derived by the counter), whose 9 body lines census() does scan as prose, 0 of them below 4 columns. The 9-line denominator is printed by the harness rather than written into the prose, because a denominator carried beside a derived numerator is the next round's contradiction. The headings-0 column reproduces the census own published 0 on both corpora, which is the check that the harness runs the same screen and not a paraphrase. The two zeros are therefore zero for DIFFERENT reasons and this is now stated: arm 1 is VACUOUS (the shape does not occur), arm 2 is INCIDENTAL -- census() really does scan those four fence bodies as prose and no false heading falls out only because UND {0,3} and SKIP ^(four spaces) both decline every line of them, a property of the corpus bytes and not of census(). Rule over the axis: every absence sentence carries the runnable command, the sha, and the reason the zero is zero marked load-bearing or incidental. RESIDUAL as a category, not "and similar": a two-state differential whose repair is itself wrong reads as agreement, which is why each repair must first move its control; and ANYIND is the arm-2 SCREEN, not the arm-2 FIX -- a real fix models list-item container indentation, so arm 2 is still owed. MUST 3 (agy leg, HELD and re-measured here; its tool count is the orchestrator's dispatch record and is not re-derived in this document, the p1 report file carrying none): the reservation prose said a FIFO, socket, device or directory is refused on the DESCRIPTOR, then said two sentences later that a reader-less FIFO never reaches fstat -- the same paragraph asserting both. Measured, all five kinds, on python 3.11.8 / darwin 25.6.0: directory EISDIR(21), unix socket EOPNOTSUPP(102), reader-less FIFO ENXIO(6) all fail at os.open and never produce a descriptor; of the five kinds measured, only a char device and a READER-PRESENT FIFO reach fstat, and within that measured set they are the only inputs that can kill the S_ISREG mutant -- the set is NOT closed and a block device, for one, is untested here. The design is unchanged by this because the reservation region single except OSError maps the open failures to the same StreamPathUnwritable / UNREADABLE reason=stream_path_unwritable line -- which is exactly why the wrong route-claim was invisible to every test. Rule over the axis: for a refusal reached by two routes, name which route each input takes and prove it by RUNNING the input. RESIDUAL as a category: the table is per-kind AND per-platform; the verdict is platform-independent, the route is not, it was measured on one interpreter and one OS, and no test asserts an errno or a route because the contract is the verdict. Also re-derived at 6f0ee85 and CONFIRMED UNMOVED: the scoped diff a8e0372..6f0ee85 -- h-mad handoff still names exactly the two .py and no .md, so every corpus figure below still holds at the shipping sha; the docs-invariant three-stage command returns 0 at 6f0ee85 as well and that sha is added to the list where it is published. The heading-census fence itself was NOT edited and is not re-asserted on trust -- what is published is the new harness reproducing its 0 on both corpora. NOT EDITED, and deliberately: the ##-slicer scope rule still ships NO cardinality; the v1.95 bracketed note quoting 13/11 for a8e0372..335f535 is correct at its own sha and was left untouched; the v87 report "Not a defect -- recorded" bullet again produced no edit. VERSION HISTORY: the v1.97 entry keeps both false claims as the dated record they are and carries a bracketed correction instead, per the practice this feature settled in round six. MUST 2, SECOND CLASS MEMBER (the teammate report's own class closure, and it is right): the seam-check's $STRIP awk carries the IDENTICAL ^ {0,3} fence bound as the census's FENCE, and stated no residual for it. The bound is now named there too, so this document has exactly two members of that class and both state it. Measured rather than argued: grep -cE '^ {4,}(`{3,}|~{3,})' over this document returns 0 at 6f0ee85 and 0 on the working file, so unlike census() arm (2) -- exercised four times on the corpus it reads -- this bound is unexercised because the shape is ABSENT, which is a different kind of zero and is labelled as one. SHOULD 1 (stamp ambiguity, held): 35698f9 was used in two incompatible senses, and at the fourth-blind-form fence the bare sha named a blob that does not contain the fence being validated -- git show 35698f9:$D | grep -cF "tr '\\n' ' '" returns 0 against 1 at 6f0ee85, re-derived here. Three document-self sites are re-phrased to 'on the working file this revision ships' (the fourth-blind-form fence, the three-blind-form re-sweep, and the head-returns-0 residual), the re-sweep additionally recording that its alternation IS in both blobs so both of its runs remain reproducible, and the rule is stated over the axis: a bare sha names a BLOB and belongs to a tree-derived figure, while a document-self figure names the working file and the entry it was run after. SHOULD 2 (REJECTED on evidence, and the rejection is the measurement): the report calls '(It was 2 before this revision, when the alternation was written out twice)' an unverifiable drafting note that exists at no commit. It reproduces. git show 35698f9:$D | grep -cF '(first|second|third' returns 2 against 1 at 6f0ee85, and the unstripped fold over the 35698f9 blob returns 2 against 1 on the working file -- both run here. The finding's premise is false and the parenthesis is NOT withdrawn; what was genuinely missing is the sha, since 'before this revision' is not a locator, and that is what was added, with both commands inline. NIT 1 (held, and widened): 'the canonical taxonomy the spec and the impl-plan repeat verbatim' overclaimed -- membership is identical in all three but the impl-plan lists the same eight in a different order, so 'verbatim' is false -- and it is also a present-tense claim about sibling bytes, which decision E forbids. Replaced by the CONTRACT rather than by a corrected state claim: the siblings owe the same SET, membership only and never order or position, a divergence is a defect in whichever document diverges, and it is found by enumerating all three rather than by trusting the sentence. No sibling repair is owed and none is asserted. NIT 2 (held): $STRIP's sub(/^ +/, "", m) now carries an inline comment saying it drops the indent before comparing runs, so the next reader does not have to decide whether it is dead. The edited fence was extracted from the SHIPPED file and re-run: head 0, and dropping $STRIP from the same shipped fence still turns that 0 into 1. OWED ELSEWHERE, reported and not edited here: nothing new to a sibling. The rejected should-fix belongs in doc-block-exec.design.rejections.md, which this author does not write. The arm (2) REAL fix -- modelling list-item container indentation in the fence tracker -- remains owed to the implementation and is stated as such in the residual; ANYIND is the screen, not the fix. **[Two claims in this entry are corrected by v1.99; the entry is otherwise left intact as the dated record it is. (1) "it prints 23 runs: 22 are commands, sha pairs, fixture descriptions and quotations of the finding ... and the 23rd is the dottedness clause", and the "four other figure-bearing runs" beside it, are BOTH counts of this screen's own output published without running it. The shipped screen prints the clause twice, once among the body-added lines and once among the Version-History-added lines: git diff 35698f9 6f0ee85 -- $D | grep '^+' | grep -c 'of the eight seams are dotted' returns 2 at cf3a862, so the split is 21 + 2. The exculpation about what an entry may transcribe is also scoped to Version History and never covered the 8 body runs, which is why v1.99 computes the partition inside the fence instead of asserting it: BODY 8 runs, 3 figure-bearing; VERSION HISTORY 15 runs, 8 figure-bearing. The three facts the sentence names all hold at cf3a862 (18/16, 13/11, 3 importers of docsections against 5 mentions). (2) NIT 1's justification, "membership is identical in all three but the impl-plan lists the same eight in a different order", is FALSE as a statement about the sibling's bytes. Enumerated at cf3a862 rather than reasoned: the canonical-taxonomy sentence in this design's Test Strategy and the impl-plan's canonical list give the seven module seams in the SAME order, and this design's in-process transport-rule sentence and the impl-plan's transport-rule sentence give them in the same (different) order as each other; the spec's list is order-identical to the canonical one too. The order never diverges. "Verbatim" is nonetheless false, for a different reason: the two siblings interleave per-AC annotations into their lists. The CHANGE that claim justified stands and is not withdrawn -- the contract is the right shape and this correction is itself an instance of why a present-tense sibling-state claim must be run -- and v1.99 ships the three-way membership enumeration as a command beside it.]**
- v1.99: Design audit v89 at freeze sha cf3a862, gating round, two surfaces (teammate must 3 should 5 nit 3; agy must 1). The design blob is byte-identical at 8909ec4 and cf3a862, verified with git diff --quiet, so the teammate report's 8909ec4 findings apply unchanged and every figure below is re-derived at cf3a862. All three teammate must-fixes are against the 6-gram carry screen v1.98 shipped -- the mechanism, not the class it closes -- and the mechanism is repaired rather than withdrawn. MUST 1: the paragraph whose whole purpose is to stop a carried figure published a count of its OWN screen's output without running it. The screen prints the dottedness clause TWICE, not once: git diff 35698f9 6f0ee85 -- $D | grep '^+' | grep -c 'of the eight seams are dotted' returns 2, the needle deliberately cut short of the wrong figure, so the decomposition is 21 + 2 and not 22 + 1. Swept to all three sites that stated it: the body site is rewritten, and the v1.97 and v1.98 entries each carry a new bracketed correction instead of being rewritten. MUST 2: the exculpation clearing the remaining runs is scoped to what a Version History entry may transcribe, but the screen never computed that partition and 8 of the 23 runs are body-added lines the rationale does not cover. The partition is now computed INSIDE the fence and printed with units -- BODY 8 runs, 3 of them figure-bearing; VERSION HISTORY 15 runs, 8 of them figure-bearing -- using the same one-unwrapped-line predicate the tail commands use, whose control is published and run: awk-split at the Version History heading, grep -c on the entry predicate over the head returns 0, so no body line is misfiled. The rule over the two sides is stated: a Version History run is a transcription, a body run is a candidate the paragraph must dispose of by name. That disposition is a READING and is labelled as one -- two commands, three fixture descriptions and one fixture's printed result, two phrasings of a rule and of its residual, and the carried clause itself, which is still not re-quoted. A numeral word list is added so a figure written as a word is caught; its over-match is named (the pronoun "one") and runs in the safe direction, since the list raises candidates and never hides them. MUST 3: the v1.98 entry justified the sibling-contract change with a present-tense claim about the impl-plan's bytes -- "lists the same eight in a different order" -- which is FALSE and was reasoned rather than run, inside the entry explaining a fix for that exact failure. Enumerated at cf3a862: the canonical-taxonomy sentences of design, spec and impl-plan give the seven module seams in one and the same order, and this design's transport-rule sentence and the impl-plan's transport-rule sentence give them in one and the same other order. "Verbatim" fails only because the two siblings interleave per-AC annotations into their lists. Corrected by a bracket on the v1.98 entry, not by a rewrite. SHOULD 1 and 2 together: "Four other runs carry a figure" carried no unit and closed under no reading, and is replaced by the screen's own derived counts; the two runs it glossed as the 13/11 measurement are re-attributed -- they are v1.96's false pairing, quoted once in that entry and once inside the bracket v1.97 appended to correct it, which is the v1.49 shape where a correction cannot avoid restating what it corrects. The three facts re-derived at cf3a862 and all holding: git diff --name-only a8e0372 74e126f names 18 files, 16 of them .md; the same command from a8e0372 to 335f535 names 13 and 11; and 3 files under the two roots IMPORT docsections while 5 mention it, so the unit is load-bearing and is the one stated. SHOULD 3: the absence rule was stated with two labels and applied with three, so all three are named -- load-bearing, incidental, vacuous -- and the rule's SCOPE is stated for the next sweep: it governs a claim that a shape is absent from a corpus, not a screen's expected output on this document, which is the state the screen exists to assert. The candidate sweep is published with both needles written in bracketed form so the sentence is not one of its own hits, and its value (36 candidate lines) is stamped at cf3a862 because this revision writes labels into several of those lines. Its four absence sites are each labelled where stated: the .md-under-docs/ invariant load-bearing and now also run at cf3a862, the two untracked-script measurements vacuous, the parametrize pair incidental with a fresh re-run at cf3a862 (2, 0, 0, and exactly one test file named since a8e0372). SHOULD 4: the seam-ordinal screen's noun alternation did not match the plurals this document writes throughout. $N now carries s? on all three nouns, the axis is stated once rather than patched member by member (the word bound applies to every sibling of the alternation, so any morphological variant of a listed noun is as invisible as an unlisted noun), and what remains uncovered is named exactly -- a possessive, a hyphenated compound, and any noun this feature adopts later for the same set. Measured both ways on the same bytes: head 0 and tail 8 under either alternation, so the blindness was never exercised here and widening it changed nothing. SHOULD 5: the sibling contract stated an obligation and shipped nothing runnable. A three-way membership enumeration is now published beside it and RUN -- it selects, in each of the three documents, the paragraph stating the canonical taxonomy, prints the set of names that paragraph carries, and prints a site count beside it. It reads the two siblings at cf3a862 because both were being edited in the working tree at the time, and this document as it ships. All three print the identical eight-member set. Two properties are deliberate and both are stated: the selector is written so that the fence publishing it cannot match itself, and the sha stamps the siblings so a mid-round rewrite cannot move the output. Residual stated exactly: the selector picks by content predicate and not by heading, so a restatement carrying neither marker phrase is invisible to it and a site count of 0 is a broken locator rather than a clean run; and the check compares SETS, so it is silent about order, position and wording by design. NIT 1: "the entry THIS revision appends" stops resolving from the bytes the moment a later entry exists; the sentence now names v1.99, per the rule v1.98 settled that a document-self figure names the working file and the entry it was run after, and the clause contradicting that rule is removed. NIT 2: no fifth unscoped file-and-md pair is added, and the reason is stated inside the paragraph whose own instruction is not to publish the pair -- the four existing pairs already make the demonstration that the pair moves while the invariant does not, and each new sha gets the INVARIANT stamped instead, which is what cf3a862 gets. NIT 3: a sentence beside the Test Plan table names the expansion a reviewer must do -- rows address ranges as well as single ACs, the separator is an en dash, and only the lower endpoint carries the AC prefix -- with two derived figures published, 7 spec ACs never written as a literal identifier anywhere in this document and only 15 of the 49 appearing literally in the table's own column. The seven are deliberately NOT listed, because writing them into this document would turn the published command's answer into 0: the publication rule in its most literal form. AGY MUST (outside the round's routed three, adopted on evidence and re-derived here): this document declared the ordinal-base rule non-exempt in Version History at two sites while entries there carry bare word-ordinals over the injection set with no base, and the tail command that counts them prints 8. Both statements were true and they contradicted. Resolved by SCOPING the base rule rather than by exempting it -- it governs an ordinal that picks a position out of an ordered SPAN, where the zero-versus-one ambiguity that motivated it is even possible, and it stays non-exempt everywhere, Version History included; a word-ordinal over a SET whose members are named and never numbered has no convention to name and no span to index, and is the seam-naming rule's business, which is the rule Version History is exempt from. Both sites stating the scope are edited so they agree, and the claim is measured rather than asserted: over the tail, a grep for the span-index shape returns 1 at cf3a862 and the single hit is a quoted census OUTPUT field, a printed count and not a position. THE PUBLICATION RULE, stated as a rule over the axis because this round hit it at the control rather than at the figure: a control measured over the document that publishes it is destroyed by being published. Every self-referential figure in this revision is therefore either stamped at a blob predating the sentence, or written with a needle the sentence cannot match, or -- for the carry screen -- run over two committed blobs no working-file edit can touch; and every one of them was re-run AFTER the edits landed rather than before. NOT RE-DERIVED, named rather than passed over in silence: the agy leg's tool count in the v1.98 entry (an orchestrator dispatch record, not derivable in this document), the plan's 1861157 Measurements transcript (files=25/30, already stated non-re-derivable where it is cited), the ENXIO 0.0000s timing, the finder-and-bounder 30/292/82/1 differential, and the 2748 suite floor. Those are INHERITED-UNVERIFIED: no round has re-run them, their absence from this round's findings is not confirmation, and nothing added here leans on any of them. OWED ELSEWHERE: nothing. The membership enumeration shows design, spec and impl-plan carrying the identical set at cf3a862, so no sibling repair is owed and none is asserted.
- v1.100: Design audit v90 at freeze sha 4e4a00c, gating round, two surfaces (teammate must 3 should 6 nit 4; agy must 1). Round ten's DECISION Q is the frame and this revision is its first test: every stated property of a screen, control, sweep or probe -- what it is immune to, what it cannot match, which side it reads, which of its branches ever fire, what its zero means -- is a CLAIM ABOUT CODE, to be read out of the shipped text and EXECUTED, never reasoned from the mechanism's design. All three teammate must-fixes were in what v1.99 ADDED, the seventh consecutive round of that pattern, and all three are property claims v1.99 asserted without running. MUST 3, Q's headline instance, executed rather than reworded: the carry screen was documented as reading BOTH sides as committed blobs, so that nothing written into the working file could move its output. It read ONE. git diff {base} {head} -- {doc} reads two trees, but the report side came in through open(rep, encoding='utf-8', errors='replace') -- a working-tree read of a path with no git show -- four paragraphs above a command in this same document that stamps its siblings on purpose, which makes it a slip and not a convention. The fence now takes RSHA and reads the report with git show {repsha}:{rep}, and R is named BY PATH for the first time (docs/02-design/features/doc-block-exec.design.audit.v87.teammate.md), which also closes the should-fix that the published figures were not re-derivable without guessing which report was meant. The immunity is then FALSIFIED-AND-SURVIVED instead of asserted: this revision's own added body lines were appended to the WORKING report and both forms re-run on that dirty tree. The v1.99 open() form moved from BODY: 8 runs, 3 of them figure-bearing / VERSION HISTORY: 15 runs, 8 of them figure-bearing to BODY: 1 runs, 1 of them figure-bearing / VERSION HISTORY: 49 runs, 17 of them figure-bearing; the shipped git show form printed 8/3 and 15/8 UNCHANGED. The body figure falls rather than rises because the appended text merges the whole added body into one contiguous run, and a screen immune to the mutation prints the same number in either direction. On a clean tree the two forms agree on all four numbers, so the repair is output-preserving and the figures published above it are the same figures. The report file was restored from a copy and git diff --quiet on it exited 0, so no file other than this design document is modified by this revision. The rule is stated over the axis where the old assertion stood, and it is the general form of Q. MUST 2: the span-ordinal control v1.99 introduced shipped WITH NO CONTROL and could not see this document's own idiom for a span ordinal. Measured branch by branch over the tail, its four branches scored 0, 0, 1 and 0, so three had never fired and its whole output was the fourth (decision O), and it scored 0 on the shape Test Strategy actually writes, a span noun with a copula and an emphasised number. Replaced by a screen over the CLASS -- a span ordinal written as a span noun beside a number, in any shape this document writes one: bare, with a copula and emphasis, with an equals sign, or as a flag -- over a sixteen-member span-noun set rather than three nouns. Every branch is fired SEPARATELY against a one-line fixture and all sixteen print 1, the flag branch prints 1, and a true negative carrying a word-ordinal over a set, a cardinality phrasing, a number standing before a span noun and a bare word-ordinal count prints 0. All three runs are published. The head is STAMPED at cf3a862 and raises 14 there, because this revision writes span-ordinal examples into the head as controls and a working-file head value would be a number the paragraph moved by being written; two of the 14 are the genuine span ordinals in Test Strategy, each naming both halves of its base in the same sentence, so the positive is LIVE TEXT in this document and not only a fixture. The tail raises 12, all printed counts and no positions, and the tail was re-run AFTER this entry landed rather than before it. Residual stated exactly: the noun set is closed by enumeration, so a span noun this feature adopts later is invisible until it is added; and the disposition of the twelve as counts-rather-than-positions is a READING, as the disposition of the eight seam-ordinals above it is. MUST 1: the absence-site set was under-derived INSIDE ITS OWN NEEDLE. The census arm (1) and arm (2) zeros are absence claims about a corpus, they sit on candidate lines the sweep itself raises, and the paragraph immediately above them had already labelled them with the rule's own words vacuous and incidental -- yet neither was among the four. The denominator is SEVEN, not four: the .md-under-docs/ invariant (load-bearing), the two untracked-script measurements (vacuous), the parametrize pair under the floor tuple (incidental), the two census arms (vacuous and incidental), and the fence-bound measurement at STRIP, which carried its reason in prose and no label until now and is labelled vacuous here. The headings-shipped-zero column is deliberately NOT an eighth, being the composite whose two arms are the two sites just added. The residual now names the two ways to be missed as CATEGORIES rather than as and-similar: OUTSIDE the needle, an absence claim in a shape matching neither of the two patterns is never raised; INSIDE the needle, a candidate line whose zero is about a corpus but printed by or read off a control harness looks like harness output rather than like prose making a claim, which is exactly how the two arms were dropped, so such a line counts as an absence claim until shown not to be one. The 36 stays stamped at cf3a862 and the working-file value is named for the first time (42 at 7982c18) with the reason the two differ. SHOULD 1: never hides them was a one-sided property the NUM word list does not have. Measured against the shipped tokeniser and regex: fifteen runs, forty runs, ninety runs and twenty-two runs are all scored not-figure-bearing, the last because the hyphen is inside the token class so twenty-two is one token even though twenty is listed. Uncovered members named exactly: fourteen through nineteen, forty through ninety, hundred, thousand, and every hyphenated compound. The gap is unexercised on the published input, so no figure moves. SHOULD 2: the widened N alternation shipped with no per-branch control. Over the v1.95 blob the six morphological branches score 4, 1, 0, 0, 0, 0, so the whole 4 is one branch's and the s? widening moved nothing anywhere in this document's own evidence; against a fixture written for each, all six score 1, so every branch is live and the four zeros record the corpus rather than a dead pattern. SHOULD 3: the tilde branch of the fence alternation had no control and no corpus reach. Re-running BOTH census controls with three tildes in place of three backticks prints the identical arm1 shipped 1 repaired 0 and arm2 shipped 1 repaired 0, and the tracked corpus contains 0 lines opening a tilde fence across the same 30 files -- an absence claim, labelled vacuous. Without that run the tilde branch of SHIPPED, ANYIND and STRIP alike was a branch no control and no corpus had ever moved, with the healthy backtick branch standing in for it. SHOULD 4: the two AC figures read the spec from the working tree with no sha. The spec side is now read with git show cf3a862, and the 49 is attributed to that blob too; run against the working spec instead, both figures come out the same, so the stamp hardens the claim without changing it. SHOULD 5: the incidental label was applied at one of the two sites stating the parametrize figure; the second now carries it. SHOULD 6 is closed inside MUST 3. NIT 1: the disposition of the 8 body runs is re-punctuated so it sums to 8 on first reading. NIT 2: committed at cf3a862 is replaced by read at cf3a862 with the note that the file was ADDED at 6f0ee85, removing the committed-in reading. NIT 3: the working-file candidate count is now named beside the stamped one. AGY MUST, REJECTED ON EVIDENCE and the rejection is the measurement: the report reads the v1.95 entry's evaluated at 335f535 against the body's Evaluated at 74e126f as a Version History entry making a false claim about the body. Both are true and neither is stale. git show 74e126f of this document prints Evaluated at 335f535 -- v1.95 was authored at freeze 335f535 and committed at 74e126f, so its entry is an accurate dated record -- and git show 0aac0b7 prints Evaluated at 74e126f, because v1.96 re-evaluated at its own freeze sha and its entry says so in those words: the evaluation is re-derived at 74e126f rather than carried. Reading a dated record as a present-tense claim about the body is the failure mode the entries-are-records convention exists for. No edit. NOT EXECUTED OR NOT RE-DERIVED, stated as contract rather than passed over: the census harness output in full was not re-run (only the two control arms in both fence flavours, the corpus size and the tilde reach); the 5 dotted-seams derivation, the dotted-form two-line fixture, the line-scoped predecessor's 3, the property-(ii) drop-STRIP differential, the named-anchor block census and the 1861157 pair, both line-pin blind-form sweeps, the seam-enumeration three-way membership run, the 14/14 markdown-it oracle and the files=25/30 Setext transcript were all left as v1.99 published them; the whole of Error Handling Strategy and the Test Plan AC table were read for contradictions with the edits above but not re-derived against the tree; and no claim about tests that do not exist yet was checked, the feature being unimplemented. Those are INHERITED-UNVERIFIED: their absence from this round's findings is not confirmation. NO PROPERTY CLAIM IS SHIPPED HERE UNEXECUTED. Every new or changed property claim in this revision was run and its output published: the two carry-screen forms on a clean tree and on a dirtied one, the seventeen span-ordinal branch firings and the true negative, the head and tail runs, the six N branch firings on the blob and on fixtures, the two tilde control arms, the tilde corpus reach, the four NUM tokeniser cases, the stamped and unstamped AC figures, and the candidate sweep at three shas. OWED ELSEWHERE: nothing. No sibling repair is asserted and none was found. **[Two claims in this entry are corrected by v1.101; the entry is otherwise left intact as the dated record it is. (1) "this revision's own added body lines were appended to the WORKING report" names the wrong bytes: what was appended is git diff 35698f9 6f0ee85, the MEASURED revision's added body lines, while "this revision" meant v1.100, whose range is 4e4a00c..06ef40f. Both were run in a scratch clone at 68a70d6 for v1.101 and both are now published by range: 35698f9..6f0ee85 appends 229 body lines and moves the open() form to BODY 1 runs / 1 figure-bearing and VERSION HISTORY 49 runs / 17 figure-bearing; 4e4a00c..06ef40f appends 161 and moves it to BODY 13 runs / 7 figure-bearing with VERSION HISTORY 15 / 8 UNMOVED; the git show form prints 8/3 and 15/8 under both. The figures published in this entry are the 35698f9..6f0ee85 mutation's and are correct for it. (2) "the working-file value is named for the first time (42 at 7982c18)" is false twice over: 7982c18 is the v1.99 blob, not a working file, and the file v1.100 shipped raises 50. Re-derived with the same bracketed needle: 36 at cf3a862, 42 at 7982c18 and at 4e4a00c, 50 at 06ef40f and at 68a70d6. v1.101 publishes the series at blobs and states why no working-file value is given.]**
- v1.101: Design audit v91 at freeze sha 68a70d6, gating round, SINGLE SURFACE -- the agy leg returned UNVERIFIED at tools=1 and certifies nothing, so this round cannot count toward the exit gate and the four must-fixes below are weighed on their evidence rather than on their gating status. All four are one shape, and it is decision Q recursing: a property claim that reads plausibly and was never run. MUST 1, and it is v1.100's own falsification of the carry screen, which is the sharpest place this could have landed: the demonstration RAN, but not on what its sentence said. "this revision's own added body lines" named v1.100 while the fence appended git diff 35698f9 6f0ee85, the MEASURED revision's added body lines. Both ranges are now run in a git clone --local --shared of this repository checked out at 68a70d6, and both are published BY RANGE in a table rather than by a phrase a reader has to resolve: 35698f9..6f0ee85 appends 229 body lines and moves the v1.99 open() form to BODY 1 runs / 1 figure-bearing and VERSION HISTORY 49 runs / 17 figure-bearing; 4e4a00c..06ef40f appends 161 and moves it to BODY 13 runs / 7 figure-bearing while VERSION HISTORY stays at 15 / 8; the shipped git show form prints 8/3 and 15/8 under both, and on a clean tree the two forms agree on all four numbers. The weaker mutation is published rather than dropped, with what makes it weaker stated in the text: it moves one partition and leaves the other standing, so on its own it is evidence about half the screen. The fence now takes MB and MH as named variables so the range cannot be left to prose, and it carries the scratch-clone recipe, because the append writes to a TRACKED file and a reviewer bound by the read-only audit contract cannot run it in the tree under audit. The rule stated over the axis: when a property is established by EXECUTING a mutation, the mutation is itself a claim -- name the exact range, blob or input the run consumed and show it is the one the sentence describes, because in the text a demonstration run on the wrong input is indistinguishable from one run on the right input. Its mechanical corollary: the revision being written can never be its own mutation range, since its lines are uncommitted while the sentence is being written, which is why "this revision" failed here. MUST 2: the absence-site denominator was under-derived INSIDE ITS OWN NEEDLE for the second round running. The census's 1861157 restatement is an absence claim about a corpus, it sits on a candidate line the sweep itself raises, and it carried a command and a sha but no label. It is labelled now and the label is MEASURED, not assumed: the differential harness was extracted from this file and run in a scratch clone at 1861157, printing tracked files 25 headings shipped 0 arm1 0 arm2 0 | reached: arm1 0 lines, arm2 8 marker lines / 4 fences / 2 files, whose 9 body lines are scanned as prose, 0 of them below 4 columns -- so arm (1) is vacuous and arm (2) incidental at that sha too, the same pair the 30-file corpus gets. The denominator at cf3a862 is EIGHT, not seven, and the composite carve-out now states its bound instead of resting on the one instance that motivated it: a composite is excluded only where its own arms are separately stated AT THE SAME SHA OVER THE SAME CORPUS, so the same composite restated at another sha, or over another corpus, is a site of its own until its arms are measured there. MUST 3: the tilde run reaches SHIPPED and ANYIND and stops -- they are the census harness's only two fence regexes -- while the sentence named STRIP as controlled as well. STRIP is a separate awk in the seam-ordinal pipeline, and this document holds 0 tilde-fence lines, so its tilde alternative was moved by no control and by no corpus, which is decision O one level up. A control now sits beside STRIP, where the code it moves is, and it discriminates MUTUALLY: two one-line fixtures, one tilde-fenced and one backtick-fenced, score shipped 0 / no-STRIP 1 / TILDELESS 1 and shipped 0 / no-STRIP 1 / TILDELESS 0 on awk version 20200816 -- deleting STRIP moves both fixtures, so the stage is live for either character, while deleting only the tilde alternative moves the tilde fixture and leaves its sibling at 0, so the movement belongs to that alternative and cannot be the backtick branch's. MUST 4: the span-ordinal screen is DIGIT-ONLY, so a span noun beside a WORD ordinal scores 0 on it, and this document writes that shape in both of its halves. A word-ordinal arm W is added over the same sixteen-noun set and a fifteen-member ordinal set; all fifteen ordinal branches fire against a one-line fixture, the emphasised-noun and one-word-gap positives fire, and the true negative -- which now also carries the digit form the other arm catches and a suffixed-numeral form neither catches -- prints 0. Stamped at cf3a862, W raises 6 on the head, and their disposition closes classes rather than cases: an ordinal counted from the end carries no zero-versus-one ambiguity and therefore needs no base, which disposes of the end-anchored pair by rule; two are cardinalities and not addresses at all; one addresses a field of a printed output the same paragraph quotes in full, and that one is a reading. ONE WAS A GENUINE UNBASED ADDRESS IN THE BODY, where no exemption reaches: the helper-mutation-spec paragraph addressed two prescribed docsections.json rows by position, and both are now named by key alone, the keys having stood in the same sentence all along, so the ordinals carried no information and one bound of ambiguity. W raises 6 on the tail as well, four of them ordinals over docsections.json's rows in the v1.52, v1.53, v1.58 and v1.62 entries; three of the four name the key in the same clause, so the address resolves through the key and the ordinal is redundant rather than ambiguous, and one names no key at all. NONE of the four resolves against the tree: that spec's mutations array holds 4 at 68a70d6, and eight is what this design PRESCRIBES, not what the file HAS. So "no Version History entry states a span ordinal without its base" is FALSE. It is WITHDRAWN rather than re-scoped; the entries are left as the dated records they are; and the residual now names the closed ordinal set, the one-word gap (measured rather than supposed -- a two-ordinal phrase joined by a conjunction yields one hit and not two, which is how the body site was found by half) and the suffixed numeral as uncovered. SHOULD 1: the v1.100 entry called 42 at 7982c18 the working-file value, and it is neither -- 7982c18 is the v1.99 blob, and the file v1.100 shipped raises 50. The series is re-derived with the same bracketed needle and published at blobs: 36 at cf3a862, 42 at 7982c18 and at 4e4a00c, 50 at 06ef40f and at 68a70d6, with the reason no working-file value is given, which is that this revision writes more labels again. Corrected by a bracket on the v1.100 entry, not by a rewrite. SHOULD 2: zero is added at the head of the NUM residual's named set and run through the shipped tokeniser (zero runs gives tokens zero and runs, scored not figure-bearing), because an absence claim IS a figure and this document writes more of those than of any other kind. NIT 1 is closed inside MUST 2 and MUST 3: the labelled absence claims v1.100 and this revision add on top of the eight stamped at cf3a862 are named where they are stated, and the working-file candidate count is explained rather than frozen. NIT 2 is closed inside MUST 1: the falsification fence names the scratch clone it must be run in. PROPERTY CLAIMS SHIPPED VERSUS EXECUTED, the standing metric this round introduces: TWENTY new or changed property claims, TWENTY executed and published, ZERO asserted. Enumerated so the count is derived and not carried -- (1) the carry screen on a clean tree in both forms; (2) it dirtied with 35698f9..6f0ee85 in both forms; (3) it dirtied with 4e4a00c..06ef40f in both forms; (4) the restore verified with git diff --quiet after each; (5) the census differential harness at 1861157; (6) the candidate sweep at cf3a862, 7982c18, 4e4a00c, 06ef40f and 68a70d6; (7) the tracked-corpus tilde reach at 68a70d6; (8) the tilde-fence count on this document; (9) the STRIP tilde control, two fixtures by three pipeline variants; (10) the fifteen W ordinal branch firings; (11) the two W gap positives; (12) the W true negative; (13) W on the head at cf3a862; (14) W on the tail, run after this entry landed; (15) P on the head at cf3a862 and P on the tail, likewise re-run after; (16) the docsections.json mutations length; (17) the one-word-gap residual; (18) the zero tokeniser case; (19) the indented-fence bound on the working file; (20) W with and without the word boundary that guards its noun group, which was added after the arm was first drafted because without it the word disposition matched the position alternative -- both forms were measured on the same bytes and both give 6 on the stamped head and 6 on the tail, so the hardening moves no published figure. That is TWENTY, not nineteen; the enumeration is the count. NOT EXECUTED AND NOT RE-DERIVED, named rather than passed over: everything v1.100 listed as INHERITED-UNVERIFIED is still inherited-unverified here -- the 5 dotted-seams derivation, the dotted-form fixture, the line-scoped predecessor's 3, the property-(ii) drop-STRIP differential, the named-anchor block census, the plan's 1861157 files=25/30 Measurements transcript, both line-pin blind-form sweeps, the seam-enumeration membership run, the 14/14 markdown-it oracle, the ENXIO timing, the finder-and-bounder 30/292/82/1 differential and the 2748 suite floor; the full census harness output on the CURRENT corpus was not re-run either, only its 1861157 counterpart and the two control arms; Error Handling Strategy and the Test Plan AC table were read for contradictions with the edits above but not re-derived against the tree; and no claim about tests that do not exist yet was checked, the feature being unimplemented. Their absence from this round's findings is not confirmation. OWED ELSEWHERE: nothing. No sibling repair is asserted and none was found. **[Corrected by v1.102: the DECISION Q metric in this entry -- "TWENTY new or changed property claims, TWENTY executed and published, ZERO asserted" -- is itself an unexecuted property claim in its last term, and the entry is otherwise left intact as the dated record it is. All twenty enumerated items were re-executed by the v92 gating audit and all twenty reproduced; what the enumeration missed is a TWENTY-FIRST new-or-changed claim, the NUM residual's "unexercised on the published input" figure, which v1.101's own edit moved by adding `zero` to the name set the grep runs over and which was restated rather than re-run. It is false on the shipped bytes: the count is `1`, not `0`. So the denominator is at least twenty-one and "ZERO asserted" is wrong. The mechanism is scoped rather than the instance patched: an enumeration assembled by listing the revision's NEW FENCES cannot see a claim changed inside a paragraph the revision was already editing, and v1.102 enumerates by new-or-changed claim instead.]**
- v1.102: Design audit v92 at freeze sha 6dcb70f, gating round, and NOTHING here is settled. The gating teammate leg found must 2 should 2 nit 2; the agy leg (doc-block-exec.design.audit.v92.p1.md) returned must=0 should=0, which is NOT a gate -- one clean surface has never been the gate on this feature -- and codex_status is exhausted until 2026-09-07 11:28, so every surface this round shares a model family with the authoring surface. No two-surface clean and no exit-gate-relevant result is claimed. All four gated documents are byte-identical from 6dcb70f to 7d8e797, verified with git diff --stat over the four paths, so every figure below was re-derived against the working tree rather than carried from the report. MUST 1, and it is DECISION Q recursing one level out: the NUM residual published `git diff 35698f9 6f0ee85 -- $D | grep '^+' | grep -cEi <name set>` as `0`, while v1.101 had itself added `zero` to that name set in the same edit and did not re-run the grep. Executed both ways here: with the set as the paragraph now names it the count is 1, with `zero` removed it is 0, so the single hit is `zero`'s and nothing else's -- the added body line reading "as prose, never hide a heading -- and the corpus exercises it zero times. (2) It matches a fence". The 1 is published and the line is named. The CONCLUSION -- that no figure above moves -- survives, and the route is now published rather than left to be reconstructed: a name-set hit and a figure-bearing run are different objects, because a token has to fall inside a run of six or more SHARED consecutive tokens before NUM is ever consulted about it. The shipped carry screen was EXTRACTED from this file with awk rather than retyped, and re-run with `zero` prepended to its WORDS via a one-character sed; against R=doc-block-exec.design.audit.v87.teammate.md, RSHA=cf3a862, BASE=35698f9, HEAD=6f0ee85 both forms print "BODY: 8 runs, 3 of them figure-bearing" and "VERSION HISTORY: 15 runs, 8 of them figure-bearing". That differential is the WHOLE of the evidence claimed: it says the four counts are unchanged, and it does NOT say where the token sits, which is a mechanism claim this run does not measure and none is made. Both of the screen's inputs are committed blobs -- git diff reads two trees and git show reads the report -- so the run is invariant to the sha checked out, which is why it reproduces at 7d8e797 what the auditor got at 68a70d6. RULE over the axis: when a revision edits the INPUT to a claim -- a name set, a needle, a WORDS list, a corpus list -- the claim is re-run AFTER the edit lands, never restated from the run that preceded it; a property claim and its input are one object. RESIDUAL, exactly: this covers a claim whose input changed inside the SAME revision and does nothing for one whose input a LATER revision changes; the only screen for that is that every figure here carries its command inline. The figure also leaves the absence class by becoming 1, so it is not a site of the absence rule and is not counted in that denominator. MUST 2, the ninth absence site: the provenance probe `git show 35698f9:$D | grep -cF "tr '\n' ' '"` -> 0, against 1 at 6f0ee85 -- both re-run here -- carried a command and a sha and no label through three sweeps. Of the two admissible repairs, LABELLING IT was chosen over carving out provenance probes, because DECISION G makes an absence claim a measurement and nothing in the rule's stated scope exempts an absence used as provenance for a neighbouring figure's stamp; the carve-out would also have needed a third way to be missed, for a weaker reason. It is labelled VACUOUS at its site -- the fence does not exist in that blob -- its positive is the paired 1 at 6f0ee85, and the denominator moves eight to nine, swept at both other sites that state it. The residual needed a third way REGARDLESS of which repair was chosen: this site was raised by the needle, is plain prose, and is not harness output, so neither of the two stated ways can account for it, and "exactly two" was false as an account of the miss that had just happened. The three ways are now: OUTSIDE THE NEEDLE; INSIDE THE NEEDLE AND MISTAKEN FOR HARNESS OUTPUT; and INSIDE THE NEEDLE, NEEDING NO INTERPRETATION AT ALL, AND SIMPLY NOT ENUMERATED -- which is how both the 1861157 restatement and this probe were missed, and which is an enumerator failure and not a classification failure. RULE over that axis: the denominator is WALKED, never recalled. Every raised line is carried to a named disposition and the check is that no raised line is left over. Walked here over all 36 lines raised at cf3a862 (re-derived, 36): nine are the sites, and each of the rest is either a fence's or a fixture's own printed output on this document together with the prose disposing of it, or a `0` making no claim about a corpus at all -- an ordinal in the index contract, a value in an AC row, or the rule quoting its own vocabulary. The walk is published as a PARTITION whose parts sum to the raised count, not as an assertion that nothing was left over: 13 + 15 + 8 = 36, the 13 being the nine sites (four state their figure on two lines each), the 15 a fence's or fixture's own printed output with the prose disposing of it, and the 8 zeros making no corpus claim at all. The sum is the check: a walk that loses a line shows up as a sum that misses 36, which recalling a site list never could. ZERO raised lines sit outside the three parts. One assignment inside the partition is arguable and is named at the site rather than hidden -- the census arm-(2) raised line states the arm's CONTROL while the arm's own zero is written in a shape the needle does not raise, so reading it as the site gives 13 + 15 + 8 and reading it as harness output gives 12 + 16 + 8; the total and the conclusion are the same either way. THE WALK'S OWN RESIDUAL, as a concrete category and not "and similar": the disposition is still a reading, and the one boundary it turns on is a line that quotes a harness's `0` and then generalises it into a claim about the corpus -- both at once, nothing mechanical separates them, and the 1861157 restatement was exactly that line; where the reading is genuinely undecidable the line counts as a site. Denominator history corrected in place: v1.99 published four, v1.100 seven, v1.101 eight, and every dropped site sat on a line the needle had already raised, so the miss was INSIDE the needle three times running. Two carried "this revision" phrases that had silently re-pointed at v1.102 were re-anchored on the revision that actually made the change. FOUND BY MY OWN DECISION-K SWEEP AND NAMED BY NEITHER AUDITOR, a third instance of the same class as MUST 1: "dropping $STRIP from the pipeline turns the 0 on this file into 1, and that one hit is the alternation assigned to O above" is FALSE on the shipped bytes. The literal 1 stood in that sentence unchanged at every sha from 6f0ee85 to 7d8e797 and was true only at the first two of them. Re-derived over the head at eight shas with the same unstripped fold: 2 at 35698f9, 1 at 6f0ee85 and cf3a862, 2 at 7982c18 and 4e4a00c, 3 at 06ef40f and 68a70d6, 6 at 7d8e797. The figure is a property of THIS DOCUMENT'S FENCE BODIES, so every revision that adds a fixture moves it, and three revisions added fixtures and each restated the number. 6 is published with all six hits disposed of by category -- two are the O and N alternations of the fence itself, two are the tilde control's printf bodies, two are the opening line of the $P and $W true-negative fixtures -- none is a live ordinal address, and the larger number makes the control STRONGER, since $STRIP is now shown to suppress six lines rather than one. The prose naming those hits was deliberately written WITHOUT reproducing the ordinal-plus-noun shape, and the stripped detector was re-run afterwards and still returns 0 on the head. SHOULD 1: the v1.101 DECISION Q metric "TWENTY / TWENTY / ZERO" is corrected by a bracketed note appended to that entry rather than by rewriting it, per this feature's practice since round six; must 1 is a twenty-first new-or-changed claim, unexecuted and false on the shipped bytes, so the denominator is at least twenty-one and "ZERO asserted" is wrong. The mechanism is scoped rather than the instance patched: an enumeration built by listing a revision's NEW FENCES cannot see a claim changed inside a paragraph the revision was already editing. SHOULD 2, the cross-document term collision on "re-anchored": this design GIVES UP the word rather than redefine it. Verified against the tree and not reasoned -- h-mad/tests/mutation-specs/docsections.json holds 4 rows, all four carrying "file": "tests/docsections.py", and the impl-plan, READ AT v1.45 / 7d8e797 and recorded as a dated reading rather than as a present-tense claim about sibling bytes (decision E), named fence-tracking-removed and section-no-longer-owns-its-subsections as the two re-anchored into h-mad/scripts/h_mad_doc_block_exec.py. The impl-plan's adjective is on the ANCHOR-FILE axis, two of four; this design's sentence was on the test-key axis, all six rows it lists. One word, two axes, two cardinalities, and the design withdraws it. NIT 1: "all four re-derived" trailing five shas now reads "the four shas later than the stamped one", with the stamped 36 named as re-derived too; all five were re-run and all five reproduce -- 36 / 42 / 42 / 50 / 50 at cf3a862 / 7982c18 / 4e4a00c / 06ef40f / 68a70d6. NIT 2: the tilde absence claim named the working file but not the entry it was run after, which is half of this document's own stamping rule. Closed as a CLASS across every document-self figure rather than at the named instance: the three-blind-form re-sweep, the fourth-blind-form fence, the ^ {4,} bound, the ~{3,} claim and the no-STRIP figure all now name the v1.102 entry, and every one was re-run on the working file AFTER this entry landed. RESIDUAL: a document-self figure whose site names no entry at all is findable only by grepping the phrase "working file"; that grep is the screen, and it is stated here rather than automated. DECISION K sweep, run after this entry landed and in the shipped order: stripped seam-ordinal head 0, unstripped 6, tail 8; ^ {4,} fence bound 0; ^ {0,3}~{3,} 0; both blind-form pin sweeps at their published expectations; $P and $W over the tail 12 and 6 with the head stamped at cf3a862 unmoved at 14 and 6. PROPERTY CLAIMS SHIPPED VERSUS EXECUTED, enumerated by new-or-changed CLAIM and not by new fence, which is should-fix 1's lesson, and the count is DERIVED by counting this list rather than carried: TWENTY-ONE new or changed, TWENTY-ONE executed and published, ZERO asserted -- (1) the name-set grep with zero, 1; (2) its control arm with zero removed, 0; (3) the hit line's text; (4) the carry screen with shipped WORDS, 8/3 and 15/8; (5) the same with zero prepended, identical; (6) the provenance probe at 35698f9, 0; (7) at 6f0ee85, 1; (8) the candidate sweep at cf3a862, 36; (9) that the provenance line is among those 36; (10) the walk partition, 13 + 15 + 8 = 36, with its 2/1/5 sub-split; (11) the sweep at the four later shas, 42/42/50/50; (12) docsections.json holding four rows all anchored at tests/docsections.py at 7d8e797; (13) the impl-plan naming two rows re-anchored into the new module, read at v1.45 / 7d8e797; (14) the no-STRIP head at eight shas, 2/1/1/2/2/3/3/6; (15) the literal 1 standing unchanged in that sentence at all seven shas from 6f0ee85 to 7d8e797, grepped verbatim; (16) the identities of the six hits; (17) the stripped head still 0 after this revision's prose landed; (18) ^ {4,} and ^ {0,3}~{3,} both 0 on the working file after this entry; (19) the tail seam-ordinal count 8; (20) $P and $W over the tail, 12 and 6, with the cf3a862 head unmoved at 14 and 6; (21) both blind-form pin sweeps, 0 and 0, with the three-blind-form alternation raising only the two lines fields of the block census. OWED ELSEWHERE, reported and NOT edited here: nothing is owed to the impl-plan by the should-fix 2 repair, since this document withdrew the colliding word; if a shared definition is wanted instead of an avoidance, that is an impl-plan matter and this author does not write it. NOT RE-DERIVED and stated so their absence is not read as confirmation: the API and Error Handling sections, the AC table, and every claim about tests that do not exist yet, the feature being unimplemented. [Corrected by v1.103, appended rather than rewritten, per this feature's practice since round six. Claim (10) above -- the walk partition -- was NOT executed. It was recalled off the site list, and its first two parts are wrong by one: the derived partition is 12 + 16 + 8 = 36, and 11 + 17 + 8 under the arm-(2) output reading, now published as a runnable anchor assignment rather than as three addends. So the metric "TWENTY-ONE new or changed, TWENTY-ONE executed and published, ZERO asserted" is itself false in the same way should-fix 1 of that round was: the correct reading for this entry is TWENTY-ONE new or changed, TWENTY executed, ONE asserted. Also corrected: three sites state their figure on two raised lines, not four.]
- v1.103: DELTA SELF-REVIEW response and NOT a gating round -- it answers doc-block-exec.design.delta-review.r13.md (must 0 / should 3 / nit 1), whose subject was the v1.101->v1.102 diff at 1cbddb7. No audit surface and no exit-gate-relevant result is claimed; the round-thirteen gating cycle runs after this batch lands. codex_status is exhausted until 2026-09-07 11:28, so every surface this round shares a model family with the authoring surface. The working tree was byte-identical to 1cbddb7 for all four gated documents before this revision. SHOULD 1, and it is the walk rule recursing onto its own repair: the 13 + 15 + 8 partition v1.102 published is WRONG BY ONE in its first two parts. It is re-walked here and published as a RUNNABLE ASSIGNMENT rather than as three addends -- an alternation of anchor strings, each a fragment of a raised line's own text, so no line number is written anywhere. It prints raised 36, sites 12, noclaim 8, both 0, neither 16; every anchor selects exactly one raised line except the parametrize anchor, which selects the pair that states that figure. The derived partition is therefore 12 + 16 + 8 = 36, and 11 + 17 + 8 under the arm-(2) output reading. v1.102's 13 came from RECALLING the site list -- its own parenthesis said four sites state their figure on two raised lines, and three do. The reviewer's independent walk reached 12 and 11 as well, so this figure changed BY DERIVATION and not on a reviewer's word; the decision sheet filed it unverified precisely because the assignment was unpublished, and publishing the assignment is what settles it. RULE over the axis: a completeness measurement is published as an assignment a reader can re-take, never as a total -- the total is the check, the assignment is the claim. RESIDUAL, a concrete category and not 'and similar': the screen proves the parts are disjoint, exhaustive and one-anchor-one-line, and it does NOT prove that an anchor sits in the right PART, which is still a reading; what changes is that a dispute is now about a named member a reader can point at rather than about a member nobody can find. The screen is also immune to its own needles being text, because its corpus is the frozen cf3a862 blob and nothing written into this document afterwards -- including that fence -- can enter the scope it counts. SHOULD 2, the document-self stamp class: v1.102 closed it at five sites and left one carrying v1.101 while the document shipped v1.102. The AXIS is the naming rule's own cost -- a stamp that names an entry goes stale on the very next bump -- so the rule is now that AN ENTRY BUMP IS ITSELF THE TRIGGER TO RE-RUN AND RE-STAMP EVERY DOCUMENT-SELF FIGURE, and all eight sites were re-run on the working file after this entry landed and re-stamped on v1.103. v1.102's residual screen grepped the phrase 'working file' and cannot reach a figure that names the working file correctly and an entry that has since been superseded, which is exactly what the missed one was; the screen is now the entry-naming form itself, FOLDED because the hard wrapper splits that phrase, with every hit read against the version the document ships. It is not self-matching -- the escaped form written in the fence is not the literal the pattern needs -- and that property is stated rather than assumed. RESIDUAL, concrete: it reaches a document-self figure in that exact phrasing and nothing else; a figure naming the working file with NO entry at all remains v1.102's grep, and a figure naming NEITHER is a decision-G matter caught by the candidate sweep. One further site was brought to the rule: it read 'the entry recording this revision', the self-describing form this document had already rejected for not resolving from the bytes. SHOULD 3, the re-anchored collision has a THIRD axis and it lives in the plan. Derived rather than reasoned -- git show 1cbddb7:<path> | grep -c 're-anchor' gives impl-plan 8, plan 2, spec 0, with the design's own count deliberately withheld because this paragraph moves it. The impl-plan's use is the anchor-FILE axis (fence-tracking-removed and section-no-longer-owns-its-subsections, into h_mad_doc_block_exec.py); the plan's is 're-anchored IN PLACE', the anchor-TEXT axis, naming the COMPLEMENTARY pair (offset-anchored-bound-runs-to-end-of-file and missing-heading-returns-empty-instead-of-failing). Both siblings say two re-anchored over DISJOINT pairs, which is the half that actually misleads a reader. This design's own use was a third axis, the test-key one, over all six rows it lists. The design still withdraws the word; the sibling-to-sibling collision is REPORTED and NOT edited, since one author writes one file. NIT: the clause saying hoisting the alternation into a shell variable is why one copy remains is now DATED to 6f0ee85, with the working-file figure published beside it -- 3 whole-file and 2 over the head, after this entry. This is THE ONE SCREEN in this document whose needle is a literal string living inside the scope it counts, and it is now named as such: the -F grep is quoted exactly once and described everywhere else, because a fourth literal copy would move the figure inside the sentence stating it. RULE over that axis: no screen's needle is written literally anywhere in the scope that screen counts, and where one already sits there the figure is derived at each corpus and never carried. RESIDUAL, concrete: this covers literal-string needles only; a regex-CLASS needle can still be matched by prose containing no literal -- the seam-ordinal screen is one of those, which is why the sentences naming its unstripped hits avoid reproducing the shape -- and nothing mechanical separates that prose from a real member, only the stripped run beside the unstripped one. v1.102's PROPERTY CLAIMS metric is corrected by a bracketed note appended to that entry rather than by rewriting it. DECISION K SWEEP, run on the working file AFTER this entry landed and re-run once more after this sentence was appended to it, in the shipped order: partition screen raised 36, sites 12, noclaim 8, both 0, neither 16, with ten SITE anchors at 1, the parametrize anchor at 2, and all eight NOCLAIM anchors at 1; candidate sweep head-scoped 36 / 42 / 42 / 50 / 50 at cf3a862 / 7982c18 / 4e4a00c / 06ef40f / 68a70d6; strict line-pin fence 0; three blind forms exactly the two block-census output fields and nothing else; fourth blind form folded 0; provenance probe 0 at 35698f9 against 1 at 6f0ee85; seam-ordinal stripped head 0, unstripped head 6, tail 8; unstripped head across nine shas 2 / 1 / 1 / 2 / 2 / 3 / 3 / 6 / 6 from 35698f9 through 1cbddb7; singular-only N on the current head 0; caret-four-space fence bound 0 and the tilde bound 0; the -F needle 3 whole-file and 2 head against 2 at 35698f9 and 1 at 6f0ee85; the new entry-naming stamp screen returning nine hits with every one naming v1.103 and no other version present; P over the tail 12 and W over the tail 6 with the cf3a862 head unmoved at 14 and 6, every P and W branch firing at 1 and both true negatives at 0; the tilde discrimination control printing shipped 0 / no-STRIP 1 / TILDELESS 1 for the tilde fixture and shipped 0 / no-STRIP 1 / TILDELESS 0 for the backtick one; the AC comm figure unmoved at 7 of 49; the seam-site fence naming all eight seams in each of the three documents; the docs-scoped .md invariant 0 at each of four shas; and the tree-derived standing counts unmoved. PRECHECK: PASS issues=0 under h_mad_precheck_doc.py --phase design; every advisory it prints is one of three deliberate classes and none lands in the head -- PATH for the files 5c through 5e create, STALESHA for shas this document stamps ON PURPOSE as historical measurements, and COUNT, all of whose hits are inside Version History where the checker pairs a figure with an unrelated neighbouring list. PROPERTY CLAIMS SHIPPED VERSUS EXECUTED, enumerated by new-or-changed CLAIM and not by new fence, with the count DERIVED by counting this list: EIGHTEEN new or changed, EIGHTEEN executed and published, ZERO asserted -- (1) raised 36; (2) sites 12; (3) noclaim 8; (4) both 0, the disjointness; (5) neither 16, the remainder that carries exhaustiveness; (6) the SITE branch loop; (7) the NOCLAIM branch loop; (8) the derived partition 12 + 16 + 8 = 36; (9) the alternative reading 11 + 17 + 8; (10) that three sites carry two raised lines and not four; (11) the entry-naming stamp screen's output on the working head; (12) that the stamp pattern does not match its own escaped definition; (13) the singular-only N re-run on the current head; (14) the -F needle whole-file; (15) the -F needle head-scoped; (16) the re-anchor counts across the three siblings at 1cbddb7; (17) the four docsections.json rows all carrying tests/docsections.py at 1cbddb7; (18) that the plan's re-anchored pair is the COMPLEMENT of the impl-plan's. OWED ELSEWHERE, reported and NOT edited here: the plan and the impl-plan each say two rows are re-anchored and name DISJOINT pairs, which is a sibling-to-sibling collision this document cannot repair by withdrawing its own use of the word, and routing it is the orchestrator's call. NOT RE-DERIVED and stated so their absence is not read as confirmation: the Setext census harness, the carry screen and the mutation-range demonstration were untouched by this revision and were not re-run; so were the API and Error Handling sections, the AC table, and every claim about tests that do not exist yet, the feature being unimplemented.
