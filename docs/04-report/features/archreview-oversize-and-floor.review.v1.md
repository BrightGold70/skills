# Fresh-context adversarial review — archreview oversize halt + delivery floor

**Range reviewed:** `54a4067..d235837` (extended mid-review from `54a4067..c5a5c9c`), i.e. commits
`6fd9c20`, `c5a5c9c`, `d235837`. `77ae173` (a one-clause SKILL.md rewording) was also read and is
correct. `86b6149` landed AFTER this review and is the fix for finding 1; it is assessed at the end
rather than reviewed as an input.

**Measurement provenance.** Findings 1–5 were measured with HEAD at `c5a5c9c`; findings 6–7 with HEAD
at `d235837`. Every `path:line` below is as of the commit named in the finding. HEAD has since moved
to `86b6149`, so line numbers in `h_mad_archreview_cycle.py` have shifted; the cited symbols have not.

Findings 1 and 2 are reproduced here only by title, at the team lead's request (1 ACCEPTED + FIXED in
`86b6149`; 2 ACCEPTED, filed, not yet fixed). The second half of finding 2, which was lost to channel
truncation, is written out in full.

---

## 1. Major — CONFIRMED — ACCEPTED, FIXED in `86b6149`

`h_mad_archreview_cycle.py:516` (at `c5a5c9c`) — the size gate counted CHARACTERS against a limit
that is the agy path's ARG_MAX BYTE budget, so the largest prompt it blessed could not be delivered,
and `test_the_largest_deliverable_prompt_still_stages` asserted STAGED at exactly the payload that
fails E2BIG. Full evidence was delivered in the first report message.

## 2. Major — CONFIRMED — ACCEPTED, filed, NOT yet fixed

`h_mad_assemble_audit.py:343` — `--vh-tail 0`, the natural escalation of the remedy `OVERSIZE`
prescribes, keeps every entry, makes the prompt LARGER, and writes a note claiming the entries were
omitted. `kept = lines[entry_idx[-keep]:]` with `keep=0` is `entry_idx[-0]` == `entry_idx[0]` — the
FIRST entry — so nothing is dropped, while `omitted = len(entry_idx) - keep` (`:341`) reports the
full count.

```
keep=1  -> "3 of 4 ... omitted"  kept: v4              len 228
keep=0  -> "4 of 4 ... omitted"  kept: v1 v2 v3 v4     len 249   <-- LONGER than keep=1
keep=-1 -> "5 of 4 ... omitted"  kept: v2 v3 v4        len 243
```

End to end through the halt that prescribes it:

```
stage (no flag)   -> ARCHREVIEW: OVERSIZE chars=1225584 ... Re-run with --vh-tail N
stage --vh-tail 1 -> ARCHREVIEW: STAGED ... bytes=708
stage --vh-tail 0 -> ARCHREVIEW: OVERSIZE chars=1225783   (199 chars LARGER than no flag at all)
```

### 2b. The table-formatted Version History half — the part that was truncated

`_trim_version_history` locates the section with `marker = "\n## Version History"`
(`h_mad_assemble_audit.py:332`) and then identifies entries as lines starting with `- v`:

```python
entry_idx = [k for k, ln in enumerate(lines) if ln.startswith("- v")]
if len(entry_idx) <= keep:
    return text
```

A document whose Version History is rendered as a **markdown table** rather than a `- v…` list has
`entry_idx == []`, so `0 <= keep` short-circuits at `:339` and the text is returned **byte-identical**.
There is one such document in this repo today:

```
$ python3.11 -c '... _trim_version_history(table_vh_doc, 1, ref="docs/x.md") == table_vh_doc'
True
```

where `table_vh_doc` is the shape used by
`docs/02-design/features/hpw-csa-unified-ui.design.md`, whose history begins:

```
## Version History

| Version | Date | Changes |
|---------|------|---------|
```

**Consequence.** On such a design, the only escape hatch `ARCHREVIEW: OVERSIZE` names is a silent
no-op. The operator re-runs with `--vh-tail 1`, gets a byte-identical prompt and the identical
`OVERSIZE` token, and has no signal distinguishing "the trim ran and the design is genuinely
irreducible" from "the trim matched nothing". Combined with 2a, the two most likely operator moves
from that halt — `--vh-tail 1` on a table-history design, and escalating to `--vh-tail 0` on any
design — both produce an unchanged-or-larger prompt.

**Both halves point at the same fix, and it is not only a bounds check.** Clamping `keep` to `>= 1`
removes 2a. It does not remove 2b, because 2b is the trim reporting nothing about what it did. The
robust shape is for `_trim_version_history` to return (or log) how many entries it actually removed,
and for the caller to say so — a trim that removed 0 entries when asked to trim is a diagnosable
event, not a silent pass-through. That also makes 2b visible in `h_mad_assemble_audit`, which has the
same blindness today.

**Scope.** The bug is pre-existing in `_trim_version_history`; `h_mad_assemble_audit --vh-tail 0` has
always had it. `6fd9c20` is what promotes that helper to being the prescribed escape hatch of a hard
halt, and adds a second caller. See the answer to follow-up (b) below for where the guard belongs.

---

## 3. Minor — CONFIRMED

**`h_mad_archreview_cycle.py:526` (at `c5a5c9c`) — `OVERSIZE` writes no file, but does not clear a
STALE prompt at the same `--prompt` path, so the halt's stated safety property fails on a re-stage.**

The gate's comment ("an unwritten prompt cannot be dispatched by mistake") and the mutation spec's
own `_mechanism` for `the-oversize-prompt-is-written-anyway` ("the next copy-pasted dispatch line
finds a prompt on disk and sends it") are both claims about a prompt **on disk**. The shipped fix
establishes them only for a path that did not already exist.

```
stage small design --prompt $T/p.txt  -> ARCHREVIEW: STAGED  (82 B written, dispatch line printed)
stage big   design --prompt $T/p.txt  -> ARCHREVIEW: OVERSIZE rc=2
ls -la $T/p.txt                       -> 82 bytes, stale content intact
```

**Failure scenario.** 6a-prime is explicitly an iterated cycle against the same prompt path, and
cycle N's `hmad-dispatch exec agy <prompt>` line sits in the operator's scrollback. Cycle N+1 stages,
hits `OVERSIZE`, and the operator re-runs the command they already have. agy then reviews cycle N's
prompt — the PREVIOUS diff — and comes back clean. That is the J41-class stale-input review this
script exists to prevent, reached through the guard rather than around it.

**Severity.** Minor rather than Major because the `OVERSIZE` run prints no dispatch line of its own,
so it takes the operator reusing an older one. **Fix:** unlink the target on the refusal path, or
write the refusal reason to `<prompt>` so a stale dispatch fails loudly instead of reviewing the
wrong range.

---

## 4. Minor — CONFIRMED; the property is unmutated and untested

**`h_mad_archreview_cycle.py:407` (at `c5a5c9c`) — `ref` is computed against `Path.cwd()`, not the
repo root, so the omission note's recovery command resolves only when cwd happens to be the repo
root.**

```python
try:
    ref = str(design.resolve().relative_to(Path.cwd().resolve()))
except ValueError:
    ref = design.name
```

The comment at `:403-405` claims the ref is "relative to the repo root when it is inside one". It is
relative to **cwd**, and `relative_to` raises whenever the design is not under cwd, falling back to a
bare basename. `git show <sha>:<path>` resolves from the repo root, so only the cwd==root case works:

```
cwd=/Users/kimhawk/orca/skills        ref -> docs/02-design/features/exec-path-hardening.design.md
cwd=…/skills/h-mad                    ref -> exec-path-hardening.design.md
cwd=…/skills/docs                     ref -> 02-design/features/exec-path-hardening.design.md
cwd=/tmp                              ref -> exec-path-hardening.design.md

$ git show HEAD:docs/02-design/features/exec-path-hardening.design.md   -> OK
$ git show HEAD:exec-path-hardening.design.md                            -> FAIL
```

`…/h-mad` is not a hypothetical cwd: it is where this repo's tests and mutation specs are run from.

**The sibling it mirrors does this correctly.** `h_mad_assemble_audit.doc_text:371` uses
`path.resolve().relative_to(project_root.resolve())`. `stage()` has no `--project-root`, which is why
`cwd` was substituted; `git rev-parse --show-toplevel` would fix it without adding a flag.

**Unmutated.** I replaced the line with `ref = "COMPLETELY/WRONG/PATH.md"` and ran the whole suite:

```
3202 passed, 1 warning in 483.39s
```

Tree restored afterwards; `git status --short` clean. No test and no mutation constrains this value,
so it can be arbitrarily wrong without the suite noticing.

**Cost.** The reviewer loses the documented way back to the omitted Version History entries. It
cannot produce a false verdict, hence Minor.

---

## 5. Minor — CONFIRMED by reading

**`references/failure-recovery.md:22` — `c5a5c9c` routes a new condition into the existing halt
`step6a-prime:review_read_nothing` without updating that halt's recovery row, whose diagnosis is now
false for the new case.**

Row 22's trigger cell reads `The review returned a verdict without reading anything (EVIDENCE: NONE)`
and its body says "the reviewer judged with **no successful tool call**". An operator arriving there
now may be holding `ARCHREVIEW: LOW_EVIDENCE_CLEAN tools=1 floor=1` — a successful call demonstrably
did happen — and the row's prescribed remedy (check that the prompt cites files by ABSOLUTE path,
because agy resolves repo-relative citations against its own scratch directory) targets a different
failure. `SKILL.md` and the script's own halt text were both updated by `c5a5c9c`; this row was not.

Note this is row **22**, not row 49 — row 49 is the one `d235837` edited, and row 49 is fine.

**Fix:** extend row 22's trigger cell to `EVIDENCE: NONE` **or** `ARCHREVIEW: LOW_EVIDENCE_CLEAN`,
and add the second remedy, which is different: at `tools=1` the prompt reached the tree, so the
question is why the reviewer stopped after the delivery write, not whether its citations resolved.

---

## 6. Minor — CONFIRMED — `d235837`

**`references/failure-recovery.md:49` — the conclusion is right; the citation for the other half of
the rule names the wrong templates, and the sentence it should have cited is unguarded.**

The clause added by `d235837` justifies `--no-done-marker` being opt-in with: *"phases 3/4/5b DO
carry the marker in their contract (the codex implementer and verifier templates both create it, and
`h_mad_audit_cycle._has_complete_report` requires it)"*.

Row 49's own first cell is `| 3, 4, 5b, 6a-prime | \`exec agy\` returned a short last message …`.
Those are **agy** document audits. Their `.done` instruction comes from
**`h-mad/audit-prompt.template.md:252`**:

> Then (2) create the marker `<that-path>.done` (e.g. `: > "<path>.done"`).

which is the default template for that path (`h_mad_assemble_audit.py:420`,
`default=SKILL_DIR / "audit-prompt.template.md"`). It is not `prepend_output_contract` — I grepped
that function and it carries no `.done`. A `.done` census:

```
audit-prompt.template.md                        -> 1 hit, line 252, the marker instruction
references/codex-implementer-prompt.md          -> 1   (Phase 5d/5e — NOT in row 49)
references/codex-verifier-prompt.md             -> 1   (Phase 5d/5e — NOT in row 49)
references/agy-architectural-reviewer-prompt.md -> 0   (as the commit claims — correct)
h_mad_audit_cycle._has_complete_report:243-248  -> requires _done_path(...).exists()   (correct)
```

So the conclusion holds and the **consumer** cite holds; the **producer** cite does not. The codex
templates cover 5d/5e, which row 49 does not mention.

**The commit's core claim is correct — verified independently rather than taken from the brief:**

```
complete report, ASSESSMENT present, no .done marker:
  report_wait.py rp.md --timeout 4                  -> rc=1, real 6.06s
  report_wait.py rp.md --timeout 4 --no-done-marker -> rc=0, real 0.04s
```

**Two consequences beyond the wrong pointer.**

1. The same wrong attribution is now stated in **three** places, having been propagated by this
   commit: `h_mad_archreview_cycle.py:208-209` ("…only the codex VERIFIER template does"),
   `tests/test_h_mad_archreview_cycle.py:897` (same phrase), and row 49.
2. More actionable: the commit's reasoning identifies a **template sentence** as load-bearing for the
   "the others must NOT have it" branch, and leaves it unpinned. Nothing in `tests/` asserts that
   `audit-prompt.template.md:252` still asks for the marker. If that sentence is ever edited away,
   phases 3/4/5b's bare `report-wait` hangs exactly as 6a-prime's did, with no test failing. The
   delivery-floor spec DID pin its template sentence
   (`the-contract-stops-bounding-the-write-count`), so the pattern exists in this codebase and was
   applied to one side of this rule and not the other.

---

## 7. Minor — CONFIRMED — `d235837`

**`tests/test_h_mad_archreview_cycle.py:342+` — the new guard test matches both needles on the same
physical LINE, so it cannot tell which clause `--no-done-marker` attaches to; a later row prescribing
a bare wait passes.**

```python
rows = [ln for ln in doc.splitlines() if "6a-prime" in ln and "report-wait" in ln]
assert rows, "the 6a-prime recovery row no longer mentions report-wait — re-check this"
for row in rows:
    assert "--no-done-marker" in row, (...)
```

I mutated the real `failure-recovery.md` four ways, ran the node each time, and restored after every
round (`git status --short references/failure-recovery.md` blank each time):

| change to `failure-recovery.md` | result | direction |
|---|---|---|
| **C** — add a row: 6a-prime, bare `report-wait "$RP"`, with `--no-done-marker` mentioned about the *5b* leg in the same cell | **1 passed** | **fails OPEN** |
| D — add a row whose phase token is `step6a-prime:timeout`, bare wait, no flag | 1 failed | caught correctly |
| E — correct document, cell hard-wrapped immediately before `**For 6a-prime, that wait needs…**` | 1 failed | fails closed (false alarm on a correct doc) |
| A — correct document, cell wrapped earlier in the trigger cell | 1 passed | correct: that fragment carries the clause |

The row text used for C:

```
| 6a-prime | re-dispatch after a fix | `step6a-prime:retry` | "re-dispatch and then
`report-wait "$RP"` to collect it; do NOT pass `--no-done-marker` on the 5b leg." |
```

**Reading.** Reformatting fails closed — noisy but safe. The real hole is C: line-level co-occurrence
is not clause attribution, and a very long table cell is exactly where a flag and the prescription it
belongs to can drift apart while still sharing a physical line. The `assert rows` tripwire IS
load-bearing today — exactly one line in the file matches both needles (line 49), so the row simply
disappearing is caught.

**Fix:** anchor on the prescription rather than the line. Every occurrence of `report-wait "$RP"`
inside a cell that names 6a-prime must be followed by `--no-done-marker` within N characters, rather
than the flag appearing anywhere on the line.

---

## Follow-up (a) — argv budget components, measured

All figures from this machine (`darwin 25.6.0`, zsh), derived by bisecting the largest single argv
element `execve` accepts:

```
getconf ARG_MAX                      = 1048576
env bytes, sum(len(k)+len(v)+2)      = 9570
max single-arg payload, bare argv    = 1037995
max single-arg payload, agy argv     = 1037772
agy sibling strings incl. NUL        = 135        (11 args)
ARG_MAX - env - bare_payload         = 1011       <- fixed kernel/exec overhead
bare_payload - agy_payload           = 223        <- charged for those 11 args
per-entry surcharge                  = 8.0 bytes/arg   (= one 64-bit pointer)
```

The argv shape used for the "agy argv" row is the one `hmad-dispatch.sh:2932-2944` builds:
`--dangerously-skip-permissions --model <m> --effort <e> --sandbox --print-timeout 900s
--output-format stream-json --print <payload>`.

**The budget decomposes exactly**, with no residual fudge beyond the 1,011-byte exec overhead:

```
usable = ARG_MAX - env_bytes - Σ(len(arg)+1 for siblings) - 8*(n_argv + n_envp) - ~1011
```

The per-entry charge is precisely 8 bytes — one pointer — so `8*(n_argv + n_envp)` is the principled
term rather than an estimate. `sum(len(k)+len(v)+2 for k,v in os.environ.items())` is the right env
term: it matched the bisect to within that same 1,011-byte residue.

**One caveat that a runtime derivation must still cover.** `stage()` runs in the operator's shell;
`exec agy` runs later inside `hmad-dispatch.sh`, whose environment is a superset (it exports
`_HMAD_EXEC_T0`, `_HMAD_EXEC_BEAT_LOG`, and others). Measuring `os.environ` at staging time therefore
under-counts by a few hundred bytes, which is why a growth margin on top is correct rather than
belt-and-braces.

## Follow-up (b) — is `--vh-tail 0` reachable from the assembler's own argparse?

**Yes, equally from both, and from neither's callers. The guard belongs in
`_trim_version_history`.**

I swept every `vh_tail` / `--vh-tail` mention under `h-mad/`. No caller anywhere passes 0 or a
negative value. The only concrete values in the tree are `--vh-tail 1` (`SKILL.md:1614,1622`) and
`--vh-tail 1`/`2` in tests. The `assemble(vh_tail=…)` Python API is reached only from its own `main()`
and from tests.

Both argparse declarations are bare `type=int` with no lower bound, so 0 and negatives are exactly as
reachable at each:

```
h_mad_assemble_audit.py:421     ap.add_argument("--vh-tail", type=int, default=None, metavar="N", …)
h_mad_archreview_cycle.py:567   s.add_argument("--vh-tail", type=int, default=None, metavar="N", …)
```

So the flag you added is not special — the pre-existing assembler surface has the same hole, and
`h_mad_assemble_audit` already tests the *upper* no-op
(`test_vh_tail_larger_than_the_history_is_a_no_op:626`) while leaving the lower one untested.

**Therefore:** put the guard inside `_trim_version_history`, the single place that computes
`entry_idx[-keep]`. That fixes both callers and any future one, and it is also where the 2b fix has to
live (reporting how many entries were actually removed). A `type=` validator on the two argparse
declarations is worth adding on top only for the better error message, not as the fix.

---

## Assessment of `86b6149`'s two constants (requested)

`ENV_GROWTH_HEADROOM_BYTES = 8 * 1024` and `ARGV_SIBLING_RESERVE_BYTES = 4 * 1024`.

Live figures on this machine with the shipped code:

```
env 9598   reserve 21950   budget 1026626
measured true ceiling with the agy argv shape and this env: 1037772
slack: 11146 bytes  (1.1% of the budget)
```

**Verdict: the margin is right. Neither too tight nor wastefully loose, and I would not change
either number.**

Against what the reserve actually has to cover:

| component | measured need | allotted |
|---|---|---|
| agy sibling argv strings + pointers | 223 B | 4,096 B (`ARGV_SIBLING_RESERVE_BYTES`) |
| fixed kernel/exec overhead | 1,011 B | — (absorbed by the 3,873 B slack above) |
| env growth between `stage` and `exec agy` | a few hundred B | 8,192 B (`ENV_GROWTH_HEADROOM_BYTES`) |
| dispatch boundary marker | 30 B | 64 B (`DISPATCH_OVERHEAD_CHARS`) |

So the reserve over-reserves by roughly 10 KB. That costs 1.1% of a 1 MB ceiling, against a failure
mode (mid-cycle E2BIG after the operator has already paid for staging) that is expensive and
confusing. The trade is correct. It also never binds in practice: the largest prompt this channel has
confirmed answered is 266,342 B, and the pathological case that motivated the halt was ~690 KB — both
far below 1,026,626.

Two things worth knowing, neither a defect:

1. **`ENV_GROWTH_HEADROOM_BYTES` is the one constant that can still be wrong in the permissive
   direction**, because it is flat while the risk it covers is a *difference* between two shells. If
   `stage` were run under a minimal environment (a CI runner, ~2 KB) and the dispatch later happened
   from an interactive shell loaded with nvm/pyenv/direnv exports (30–60 KB is ordinary), the delta
   would exceed 8 KiB and the gate would be permissive again. 8 KiB comfortably covers the documented
   workflow, where staging and dispatch share one shell. If you ever want to close it properly, the
   move is to have the gate reserve a *proportion* of the observed environment as well as the flat
   figure, or to re-check the budget inside `hmad-dispatch.sh` immediately before `execve`, which is
   the only place the true environment is known.
2. **`budget` can in principle go negative** on a host with a pathologically large environment
   (`env_bytes > ARG_MAX - 12,352`). The token would then report a negative budget and refuse
   everything, which is the safe direction but reads as nonsense. A one-line floor would make the
   diagnosis legible.

The `os.sysconf("SC_ARG_MAX")` fallback to `1_048_576` is correctly conservative: Linux typically
reports 2,097,152, so the fallback under-promises there, and the comment says so.

---

## Count and coverage

**7 findings — 2 Major (1, 2), 5 Minor (3, 4, 5, 6, 7), 0 Critical. All CONFIRMED by execution or by
direct reading of the cited line; none PLAUSIBLE.**

Status: 1 ACCEPTED and fixed in `86b6149`; 2 ACCEPTED and filed; 3–7 open as of this writing.

### Negatives — things I checked that did NOT yield a finding

- **No dead mutation in any of the three specs.** `archreview_delivery_floor.json` and
  `archreview_oversize_halt.json` both `MUTATION: ALL_CAUGHT mutations=6 caught=6 survived=0
  refused=0`; `archreview_done_marker_recovery.json` `ALL_CAUGHT mutations=2 caught=2` (run in a
  throwaway worktree at `d235837`, since the tree was dirty at the time). Every mutation was killed
  by **its own named test**, not by a bystander — including the two that isolate placement from
  existence (`the-oversize-prompt-is-written-anyway`,
  `the-gate-measures-the-body-before-the-contract-prepend`) and the one that mutates the shipped
  reviewer template.
- **No other call sites.** Nothing in the tree calls `archreview_cycle.stage()` or `score()`, or
  re-implements either gate; only `SKILL.md`, `references/failure-recovery.md` and two test files
  mention the module.
- **The asymmetry claim holds.** `h_mad_audit_cycle.py` runs its FAIL loop before the
  `DELIVERY_FLOOR` check (`:846-848`, `:882`), so findings at the floor are still recorded there too.
  The archreview docstring's "this is `h_mad_audit_cycle.combine`'s asymmetry" is accurate.
- **`headroom=` reporting `DISPATCH_OVERHEAD_CHARS` was deliberate**, matching the sibling token at
  `h_mad_assemble_audit.py:459`. Not a finding.
- **Both halts leave no state.** `LOW_EVIDENCE_CLEAN` recorded nothing on *both* channels by
  execution — the state file was byte-identical after a `--review`-only run and after a
  `--report-file` run. `OVERSIZE` writes no file on a fresh path. Only the stale-path case (finding 3)
  leaks.
- **`DELIVERY_FLOOR = 1` is not over-strict on the `last-message` channel.** I considered arguing the
  floor should be 0 there and dropped it: `channel` records which surface the *scorer* read, not
  whether the reviewer's delivery write happened, so it cannot discriminate and the conservative
  uniform floor is correct.
- **`h_mad_assemble_tdd.py:397` writes a prompt with no size gate**, but `assemble()` inlines only
  `task_body(plan_text, task_id)` — one task section, not a whole document. Not a sibling of this
  size class; dropped.
- **`archreview_done_marker_recovery.json`'s second mutation uses a file path as its `test` key**
  (`tests/test_h_mad_report_wait.py`) where the other three specs in this arc use precise nodeids, and
  each spec's own `_why` states "Each mutation carries its own `test` key". The harness accepts it and
  it did kill. Weaker discrimination, not a defect — noted, not filed.
- **Suite green throughout:** 51 in `tests/test_h_mad_archreview_cycle.py`, 3202 whole-suite, before
  and after every probe. Every temporary edit I made was restored and verified with
  `git status --short`.

### What I read

The full `h_mad_archreview_cycle.py`; the complete `54a4067..77ae173` diff plus `86b6149`'s
`_argv_budget`/`_size_gate`; all three mutation specs and all three harness runs; the tests added by
the range (from the diff); `h_mad_assemble_audit.py:240-520`; `h_mad_audit_cycle.py:243-248`,
`:460-463`, `:820-885`; `hmad-dispatch.sh:2740-2950`; `h_mad_report_wait.py`;
`h_mad_assemble_tdd.py:180-410`; `audit-prompt.template.md:252`; the `SKILL.md` diffs plus an
`ARCHREVIEW:`/token grep across `SKILL.md` and `references/`; `failure-recovery.md` rows 22 and 49;
`h_mad_review_evidence.py`'s docstring and `--help`; a `.done` census across `references/` and the
prompt templates; the Version History format of every `docs/02-design/features/*.design.md`.

### What I did NOT read

The body of `references/agy-architectural-reviewer-prompt.md` — I relied on the test that pins its one
load-bearing sentence, so my acceptance of `DELIVERY_FLOOR = 1` rests on that test rather than on my
own reading of the contract. The bodies of `codex-implementer-prompt.md` and
`codex-verifier-prompt.md` beyond their `.done` counts. `h_mad_precheck_doc.py`.
`tests/test_h_mad_report_wait.py`. The pre-existing tests in `tests/test_h_mad_archreview_cycle.py`
outside the range's diff.

### What I did NOT do

I never dispatched a live `exec agy` run. Finding 1 is proven at the syscall with an agy-shaped argv
and the real environment, not against the agy binary itself, and `86b6149`'s own execution test is
the same class of evidence. If you want the last mile, one real oversize dispatch would confirm that
agy's own failure on an over-ARG_MAX argv is the kernel's E2BIG and not something agy reports
differently.
