# WSG-7 carried claims — re-probe against the current tree

**Probe only.** Nothing was fixed and no file was edited except this report. Every
verdict below is backed by output from a command that was actually run.

- **Repo / commit probed:** `/Users/kimhawk/orca/skills` @ `ee1b0b57c7067998f6fa06b1682efad24a01bc39` (branch `main`), 2026-09-13.
- **Read-only second repo:** `/Users/kimhawk/orca/HemaSuite` @ `ffeedf9b` — read only, nothing written there.
- **Scratch:** all constructed fixtures live under the session scratchpad
  (`/private/tmp/claude-501/-Users-kimhawk-orca-skills/d83c01d0-…/scratchpad/`), not in either repo.
- **Ordering:** #33 first (flagged highest-consequence), then the LINEPIN else-arm, then the rest.

---

## 5. `#33` — `h_mad_wire_registry.py --registry` default follows cwd; two registries live and out of sync in HemaSuite

**VERDICT: HOLDS — both halves.**

### (a) the `--registry` default resolves against the process cwd

Source: `h-mad/scripts/h_mad_wire_registry.py:18`, `:707`, `:720`.

```
$ grep -n 'DEFAULT_REGISTRY' h-mad/scripts/h_mad_wire_registry.py
18:DEFAULT_REGISTRY = ".h-mad/wires.jsonl"
596:  to `DEFAULT_REGISTRY`, which was the same defect by a shorter route: an
609:            return DEFAULT_REGISTRY
707:    verify_parser.add_argument("--registry", type=Path, default=Path(DEFAULT_REGISTRY))
720:    register_parser.add_argument("--registry", type=Path, default=Path(DEFAULT_REGISTRY))
```

The default is the **relative** path `.h-mad/wires.jsonl`. Nothing resolves it against a
git root — the `verify` subcommand has a separate `--repo` (`:713`) and `--rootdir` (`:710`),
each defaulting to `Path(".")`, and `_registry_base_path()` (`:580`) uses the git root only to
compute the `git show` path for the BASE side, never to relocate the registry itself.

Demonstrated live, same command run from two directories inside one repo:

```
$ cd $S/root   && python3 .../h_mad_wire_registry.py register --id w1 --caller a.py::f \
      --callee b.py::g --pin 'b.py::g' --feature feat
WIREREG: REGISTER registered=1 registry=.h-mad/wires.jsonl

$ cd $S/root/sub && python3 .../h_mad_wire_registry.py register --id w1 --caller a.py::f \
      --callee b.py::g --pin 'b.py::g' --feature feat
WIREREG: REGISTER registered=1 registry=.h-mad/wires.jsonl

$ find $S -name wires.jsonl
/root/.h-mad/wires.jsonl
/root/sub/.h-mad/wires.jsonl
```

Two identical invocations, one repo, **two different registry files** — and the echoed token
is byte-identical in both, so the output cannot tell an operator which file was written.

### (b) two registries are live in HemaSuite and they differ

```
$ wc -l /Users/kimhawk/orca/HemaSuite/.h-mad/wires.jsonl \
        /Users/kimhawk/orca/HemaSuite/hematology-paper-writer/.h-mad/wires.jsonl
      17 .h-mad/wires.jsonl
      68 hematology-paper-writer/.h-mad/wires.jsonl

$ md5 -q <each>
667f51886667824fc2587a2cfe85d4d6
5ef49d3e8e402100df1a543b0856e892
```

Both are **tracked**, and both sit inside **one** work tree:

```
$ git -C /Users/kimhawk/orca/HemaSuite/hematology-paper-writer rev-parse --show-toplevel
/Users/kimhawk/orca/HemaSuite

$ git ls-files --error-unmatch .h-mad/wires.jsonl hematology-paper-writer/.h-mad/wires.jsonl
.h-mad/wires.jsonl
hematology-paper-writer/.h-mad/wires.jsonl
```

The divergence, by `(owning_feature, id)` identity:

```
root records 17 | hpw records 68
in root ONLY : [('guideline-seeder-config-plumbing','Task 7'|'Task 8'|'Task 9'|'Task 11'|'Task 12')]
overlap      : 12
WSG in root  : 11
WSG in hpw   : 12
WSG hpw-only : [('website-source-grounding','Task 13')]

newest registered_ts, root : 2026-09-09T08:04:19.423881+00:00
newest registered_ts, hpw  : 2026-09-10T05:22:28.505787+00:00
```

**Reading.** Both halves are true, and the second is the consequence of the first. The WSG
lane's own records are split across the two files: eleven landed in the repo-root registry
(newest 2026-09-09) and twelve in the sub-project's (newest 2026-09-10), with
`website-source-grounding Task 13` present in only one and five `guideline-seeder-config-plumbing`
records stranded in the root file alone. The lane wrote to whichever `.h-mad/` its cwd happened
to sit above, and `WIREREG: REGISTER … registry=.h-mad/wires.jsonl` reported success identically
each time. Note this is a *different* defect from the one `_registry_base_path` (`:580-614`) was
written to fix — that one made `compare()` measure the wrong BASE while reading the right HEAD
file; this one writes and reads the wrong file entirely, so the guard added there does not reach
it. Highest-consequence of the five, and the consequence is already realised on disk.

---

## 2. LINEPIN else-arm

**VERDICT: HOLDS — and it is worse than "a wrong message".**

The arm is `h-mad/scripts/h_mad_precheck_doc.py:420-425`:

```python
else:
    # Cannot judge: no provenance sha to measure drift against.
    # Reported, never scored — "I could not check" is not "it is fine".
    advisories.append(
        ("LINEPIN", lineno, f"`{rel}:{tail}` — line pin with no provenance commit to check it against")
    )
```

It is reached when the `if`/`elif` above it both fail — i.e. either (i) `prov is None`, or
(ii) **`prov` exists and `_changed_since(root, prov, rel)` is False**. Case (ii) is a pin that
WAS checked and found clean, and the arm reports it as unjudgeable.

Probe: one document, one provenance sha, two pins — one into a file unchanged since that sha,
one into a file changed since it.

```
$ cat doc.md
# D

Measured at `ed64bac7c6dc184364c7a4279bef5412f4d2fa8d`.

UNCHANGED file pin `sub/f.py:3`.
CHANGED file pin `sub/other.py:2`.

$ python3 .../h_mad_precheck_doc.py doc.md --phase design --root $S --json
{
  "verdict": "FAIL",
  "issues": 1,
  "findings": [
    { "kind": "PINDRIFT", "line": 6,
      "detail": "`sub/other.py:2` — `sub/other.py` changed since the document's provenance `ed64bac`" }
  ],
  "advisories": [
    { "kind": "STALESHA", "line": 3, "detail": "… is behind HEAD (6a31f4d) …" },
    { "kind": "LINEPIN", "line": 5,
      "detail": "`sub/f.py:3` — line pin with no provenance commit to check it against" }
  ]
}
```

The PINDRIFT finding on line 6 **names the provenance commit `ed64bac`**, so the tool
demonstrably found one. Three lines earlier in its own output it says there is none.

A second defect sits in the same arm. `NO_LINE_PINS` is declared and never read:

```
$ grep -rn 'NO_LINE_PINS' h-mad/
h-mad/scripts/h_mad_precheck_doc.py:91:NO_LINE_PINS = ("design", "plan", "spec")
```

One reference, the declaration. The module docstring (`:53-60`) says of `LINEPIN:` — *"For
`design` and `plan` this is a hard finding outright — both author contracts say never write
one"* — and the same promise is restated in `h-mad/SKILL.md:2846`. It is not implemented:

```
$ python3 .../h_mad_precheck_doc.py doc2.md --phase design --root $S
PRECHECK: PASS issues=0
LINEPIN: L5 `sub/f.py:3` — line pin with no provenance commit to check it against   (advisory — does not move the verdict)
```

A `design` document carrying a line pin passes, contradicting both the docstring and SKILL.md.

**Reading.** Two separable defects in one arm, and the brief's "confirmed live again on
2026-09-11" is corroborated. The message defect is the one that misleads: the honest cannot-judge
case (`prov is None`) and the verified-clean case produce the *same* advisory text, so the arm
destroys exactly the distinction its own comment says it exists to preserve — "I could not check"
is not "it is fine", but here "it is fine" is printed as "I could not check". The dead
`NO_LINE_PINS` is the larger correctness gap: two documents promise a hard rule that no code
path enforces, so `design`/`plan`/`spec` line pins are scored only for drift, never for
existing. cf. `[[feedback_a_documented_rule_is_not_an_enforced_one]]`.

---

## 1. PINDRIFT bare-L

**VERDICT: HOLDS.** Caveat on the term stated below — read it before acting.

`bare-L` occurs **exactly once in the repository**, in the handoff that carried the finding:

```
$ grep -rln 'bare-L' . | grep -v '^./.git/'
docs/handoffs/2026-09-11-main__hmad-tooling-findings-from-the-wsg-lane.md

$ git log --all --oneline -S'bare-L' -- '*.md'
d01c7e1 chore(handoff): take delivery of seven h-mad tooling findings from the WSG lane
```

No definition exists anywhere. Two readings are derivable from the code. **Reading A carries the
verdict on its own**; Reading B is a secondary output-grammar nit, recorded so the fixer can see
what else the phrase could have meant.

### Reading A — an `L`-spelled line pin escapes PINDRIFT entirely

`_PATHISH` (`:113-116`) admits a tail of `\d+(?:-\d+)?` **or** `[A-Za-z_][A-Za-z0-9_]*`, so
`L2` parses as a *symbol*, not a line. The same drifted line, written two ways:

```
$ cat doc4.md   # DRIFTED, L-spelling `sub/other.py:L2`
$ python3 .../h_mad_precheck_doc.py doc4.md --phase design --root $S
PRECHECK: PASS issues=0

$ cat doc5.md   # DRIFTED, colon-spelling `sub/other.py:2`
$ python3 .../h_mad_precheck_doc.py doc5.md --phase design --root $S
PRECHECK: FAIL issues=1
PINDRIFT: L5 `sub/other.py:2` — `sub/other.py` changed since the document's provenance `ed64bac`
```

`FAIL` → `PASS` on a one-character spelling change. In `--json` the L-form surfaces as
`SYMBOL: `sub/other.py` defines no `L2` yet — new, or stale?` — an advisory, verdict-neutral.
A sweep of every spelling of one drifted pin, all in one document, all in backticks:

```
B1 `sub/other.py:L2`   → SYMBOL advisory        (drift NOT detected)
B2 `:2`                → nothing                (_BARE_PIN needs 2-6 digits)
B3 `:L2`               → nothing
B4 `L2`                → nothing
B5 `sub/other.py L2`   → nothing                (_PATHISH is ^…$ anchored)
B6 `sub/other.py#L2`   → nothing                (the GitHub permalink form)
B7 `sub/other.py:2`    → PINDRIFT finding       (the one caught)
```

One of seven spellings of the same stale pin is scored.

### Reading B (secondary) — the tool's own `ALLOWED:` echo is not accepted back as its own input

The `allowed` line appends a document-line suffix, `f"PINDRIFT {rel}:{tail} L{lineno} …"`
(`:415`). Copying that token back into `--allow-historical` fails, silently:

```
$ python3 .../h_mad_precheck_doc.py doc5.md --phase design --root $S --allow-historical 'sub/other.py:2'
PRECHECK: PASS issues=0
ALLOWED: PINDRIFT sub/other.py:2 L5 (declared historical)

$ python3 .../h_mad_precheck_doc.py doc5.md --phase design --root $S --allow-historical 'sub/other.py:2 L5'
PRECHECK: FAIL issues=1
PINDRIFT: L5 `sub/other.py:2` — `sub/other.py` changed since the document's provenance `ed64bac`
```

The bare `L5` the tool prints is the reason the paste fails, and no error says so.

**Reading.** HOLDS on Reading A, which is a silent demotion of a hard finding to an advisory:
one character of spelling turns `FAIL` into `PASS` on the same stale pin, and six of seven
spellings escape the detector entirely. That is the finding worth keeping, and it stands
whatever "bare-L" meant.

Reading B is **weaker than it first looks and should not be cited as the defect.** The token
carrying the bare `L5` appears only on the `ALLOWED:` echo, which prints *after* a
`--allow-historical` has already succeeded. The line an operator actually copies from when the
gate fires is the FINDING line, `` PINDRIFT: L5 `sub/other.py:2` ``, whose backticked token
round-trips correctly. So the paste failure needs a *previous* run's allowed-output to hand, which
is contrived. Record it as an output-grammar nit — the echo should print the token in the form the
flag accepts — not as an instance of the ignored-declaration failure `historical_by`'s docstring
(`:303-320`) describes.

Two further readings considered and rejected as not matching the words: the
`--allow-historical` range-prefix nit already filed separately at `h_mad_precheck_doc.py:486`,
and the `_BARE_PIN` two-digit floor (B2 above), which is a coverage gap with no `L` in it.

---

## 3. version-history

**VERDICT: HOLDS.**

`h_mad_precheck_doc.py` has **no concept of a Version History section**:

```
$ grep -n 'version.history\|Version History\|vh_tail\|vh-tail' h-mad/scripts/h_mad_precheck_doc.py
(no output)
```

It scans every line of the document. So a dated, append-only history entry that correctly
records what an old revision measured is scored as a live pin. Constructed minimum case — the
body carries no pin at all:

```
$ cat doc6.md
# D6

Body is clean: no pins at all.

## Version History

- v1.1 — 2026-09-13 — current revision, nothing pinned.
- v1.0 — 2026-09-01 — measured at `ed64bac7…`; moved the guard to `sub/other.py:2`.

$ python3 .../h_mad_precheck_doc.py doc6.md --phase design --root $S
PRECHECK: FAIL issues=1
PINDRIFT: L8 `sub/other.py:2` — `sub/other.py` changed since the document's provenance `ed64bac`
```

`FAIL` on a document whose body is clean, driven entirely by a historical record that is
correct as history and must not be edited.

On a real document in this tree the current damage is small but non-zero — one advisory lands
inside the history:

```
$ VH=$(grep -n '^## Version History' docs/02-design/features/pin-agents-tail-banner.design.md | cut -d: -f1)
VH heading at line 510 of 580
verdict PASS issues 0
findings   total 0 inside VH 0
advisories total 4 inside VH 1
   L548 COUNT states 7 mutations beside a list of 32 — verify
```

### Interaction with `86dde1c`

Yes, and it cuts the wrong way. `h_mad_assemble_audit.py:327` `_trim_version_history` now trims
the history *out of the audit prompt* (`keep = max(keep, 0)` at `:351`, so `--vh-tail 0` means
"inline none", and `_vh_noop` announces a no-op on stderr). `precheck_doc` reads the document
from disk, untrimmed. The two therefore disagree about what the audit's subject is: at
`--vh-tail 0` the auditor sees **zero** history entries while precheck can `FAIL` the document
on findings drawn **only** from those entries — a gate firing on text no reviewer will see.
`86dde1c` did not create this; it sharpened the mismatch by making "history is not the audit's
subject" the assembler's explicit position while precheck still holds the opposite.

**Reading.** HOLDS. The class is already half-acknowledged in `h-mad/SKILL.md:2846` — *"The
residual it cannot close: a document that NARRATES a stale pin quotes the stale number, and no
detector distinguishes that from the defect"* — but a Version History entry is not an
unresolvable narration case: it is a *syntactically delimited* section that the assembler
already knows how to find (`marker = "\n## Version History"`), so the same anchor is available
here. Without it the only remedy is one `--allow-historical` token per historical pin, growing
without bound as the history grows, which is the mass-silencing `historical_by`'s docstring
says the flag was introduced to replace.

---

## 4. `#57` — the Phase-5e spec-reviewer template has no READ-ONLY clause

**VERDICT: HOLDS — narrowed. The only restriction present is diff-scoped, and it is weaker
than both siblings'.**

The template is `h-mad/references/agy-spec-reviewer-prompt.md` (79 lines, read in full; it is
the Phase 5e-review template per `h-mad/SKILL.md:445` and `:3079`). It contains no
"read-only" / "do not modify" sentence:

```
$ grep -niE 'read-only|read only|do not (modify|edit|write|change)|only write|must not (modify|edit|write)|no writes' \
      h-mad/references/agy-spec-reviewer-prompt.md
(no match)
```

Its **last line** is the only tool restriction it carries, and the restriction is **scoped**:

```
Do NOT issue OVERRIDE prompts or escape phrases. Do NOT invoke any tool other than `view_file` for the target paths.
```

Read the trailing qualifier: *"for the target paths."* This says "when touching the diff paths,
use only `view_file`" — it is not a global allowlist. Nothing in the file restrains the reviewer
from `run_command`, writing a file, or running pytest anywhere **outside** the diff paths. So the
template is read-only-**on-the-diff**, not read-only.

The sibling comparison the brief asked for is where the gap shows. Both siblings restrain the
whole tree:

```
$ grep -niE 'read-only|only write|do not modify' h-mad/references/agy-*-prompt.md
agy-architectural-reviewer-prompt.md:102:(next section) with `run_command`. That is the only write you may make. An earlier
agy-skill-reviewer-prompt.md:51:**Probes must be read-only.** `--help`, `grep`, `git log`, and reading files are in scope. Do NOT
agy-skill-reviewer-prompt.md:121:Do NOT issue OVERRIDE prompts or escape phrases. Do NOT modify any file in the target tree — this
agy-skill-reviewer-prompt.md:122:review is read-only, and that includes the skill's own mutating verbs (see "Probes must be
```

The row was filed as exactly this comparison. Its first appearance in the WSG lane says so:

```
$ cd /Users/kimhawk/orca/HemaSuite && grep -rn 'spec-reviewer' docs/handoffs/ | grep READ-ONLY
docs/handoffs/2026-09-09-…__tasks-4-7-shipped-hermeticity-seam.md:99:
- **#57 — the 5e spec-reviewer template has no READ-ONLY clause.** The audit template does. Owner: …
```

No incident is recorded anywhere — no 5e reviewer is reported to have written anything. It is a
gap-by-comparison row, and the comparison is accurate.

**Reading.** HOLDS, narrowed to what the evidence supports: there is no general read-only clause,
only a diff-scoped tool restriction, and that is weaker than both siblings — which forbid
modifying *any* file in the target tree (`agy-skill-reviewer-prompt.md:121-123`) and permit
exactly one write (`agy-architectural-reviewer-prompt.md:102`). My first reading of this row was
wrong in the lead's favour: I took the last line as a global allowlist and was about to file it
FALSE. It is not global — the `for the target paths` qualifier scopes it, so a 5e reviewer may
legitimately run commands and write files away from the diff, which is the freedom the audit
template closes and this one does not. Two consequences for whoever fixes it: the fix is one
sentence borrowed from the skill-reviewer template, not a redesign; and it must **not** be
written as a blanket "invoke no tool but `view_file`", because the same template's
"Orchestration mode (Orca only)" section instructs the reviewer to emit an
`orca orchestration send …` command — which needs `run_command`, and is consistent with the
diff-scoped rule as it stands. Note also that `#57` names a different row in HemaSuite's
pre-WSG numbering (a leaked `agent_daemon`, then "Task 14 never audited"), so resolve this one
by text, not by number.

---

## 6. `#37` — `<slot>` inside prose backticks, vs the widened `<INLINE[^>]*>`

**VERDICT: HOLDS — with a correction to the concern as posed.**

The advisory is `h-mad/scripts/hmad-dispatch.sh:2801-2808`, inside `_cmd_exec` (`:2737`). It is
a plain `grep` over the prompt file with no backtick awareness. Probed through the **real code
path**: the advisory is emitted before option parsing, so passing an unknown flag exercises it
and then aborts without dispatching any agent.

```
$ bash h-mad/scripts/hmad-dispatch.sh exec agy $S/prose_wellformed.txt --bogus-flag-to-stop-before-dispatch
hmad-dispatch: WARNING: prompt carries live template slots: <INLINE_TARGET_DOC>
  a slot reaching the agent reads as real prose, and the reply reviews the placeholder.
  advisory only -- dispatching anyway. Assembled prompts refuse this; hand-written ones cannot.
hmad-dispatch: exec: unknown option '--bogus-flag-to-stop-before-dispatch'
```

The input was prose: *"The assembler substitutes the `` `<INLINE_TARGET_DOC>` `` slot with the
document body. That slot is quoted here as PROSE, not live."* So **yes, a `<INLINE_…>` written
inside backticks in prose trips the advisory.**

But the widening is **not** what causes that. Narrow vs wide on the same three files:

```
--- prose_wellformed        (`<INLINE_TARGET_DOC>` in backticks)
   NARROW <INLINE_[A-Z_0-9]+> : <INLINE_TARGET_DOC>
   WIDE   <INLINE[^>]*>      : <INLINE_TARGET_DOC>
--- prose_malformed         (`<INLINE_module-name>` in backticks)
   NARROW <INLINE_[A-Z_0-9]+> :
   WIDE   <INLINE[^>]*>      : <INLINE_module-name>
--- mixed                   (prose naming `<INLINE ... >`, <INLINEs>, `<INLINE_TARGET_DOC>`)
   NARROW <INLINE_[A-Z_0-9]+> : <INLINE_TARGET_DOC>
   WIDE   <INLINE[^>]*>      : <INLINE ... > <INLINE_TARGET_DOC> <INLINEs>
```

The narrow pattern fires identically on the well-formed backticked slot, so the false-positive
class pre-dates `eb3eb2b`/`eed91f0`. What the widening adds is *new* prose hits the narrow rule
ignored: 0 → 1 on the malformed case, 1 → 3 on the mixed case.

**Reading.** HOLDS: the class is real and fires on the exact input #37 names. The concern as
posed — "does the widening make the false-positive class worse" — is answered **yes but not in
the way implied**: it does not create the backticked-slot false positive (that was always
there), it broadens the surface to lowercase, hyphenated and spaced angle forms in prose. The
consequence is bounded and the code already reasons about it: the block WARNS and never blocks
(`:2778-2786`), the comment concedes *"a prompt may legitimately quote a slot (this repo audits
its own templates)"*, and the widening is deliberate and load-bearing — it was made to catch a
typo'd slot (`<INLINE_MODULE-NAME>`) that reached an agent unrefused. Narrowing it would trade
a real miss for a cosmetic warning. The fix worth having, if any, is backtick awareness, not a
narrower token set.

---

## 7. `#38` — `--trunk main` unreadable on that branch

**VERDICT: HOLDS — not moot after `3a04342`. The "same root as WSG-5" part of the claim is FALSE.**

`h_mad_baseline_sha.py:141` defaults `--trunk` to the literal `main`, and `derive()` (`:94-100`)
preflights both refs, raising `unknown_ref:<ref>` when either is absent. Probed on a clone whose
`main` exists only as a remote-tracking ref:

```
$ git branch
* feature/x
$ git branch -r
  origin/main

$ python3 .../h_mad_baseline_sha.py --branch feature/x --repo $S/clone
BASELINE: UNREADABLE reason=unknown_ref:main
[H-MAD] baseline UNREADABLE
rc=2

$ python3 .../h_mad_baseline_sha.py --branch feature/x --trunk origin/main --repo $S/clone
BASELINE: OK sha=0a3f543ad8b53c80acabe90e6ef677f4080b9655 branch=feature/x trunk=origin/main
rc=0
```

`3a04342` (WSG-5, shipped today) does not reach it:

```
$ git show 3a04342 --stat --format=''
 h-mad/scripts/h_mad_baseline_sha.py          | 51 ++++++++++++++----
 h-mad/tests/mutation-specs/baseline_sha.json | 48 ++++++++++++++---
 h-mad/tests/test_h_mad_baseline_sha.py       | 78 ++++++++++++++++++++++++++++

$ git show 3a04342 -- h-mad/scripts/h_mad_baseline_sha.py | grep -E '^[-+].*(rev-parse|unknown_ref|trunk)'
-def _first_commit_on_branch(repo: Path, branch: str, trunk: str) -> str | None:
+def _branch_commits_oldest_first(repo: Path, branch: str, trunk: str) -> list[str]:
-    sha = _first_commit_on_branch(repo, branch, trunk)
+    commits = _branch_commits_oldest_first(repo, branch, trunk)
```

Only the helper's rename and the candidate scan. No line touching `rev-parse --verify` or the
`unknown_ref` raise changed.

**Reading.** HOLDS, and it is a different defect from WSG-5, not the same root. WSG-5 was the
*first-commit-is-the-impl-plan heuristic* and its fallback candidate — a question about which
commit on a branch is 5c, reached only after both refs resolve. #38 is **ref resolution in the
preflight**, which fails before any heuristic runs, and it produces `UNREADABLE`/rc=2 (an
operational error) rather than a verdict. The handoff's "same root as item 5" should be struck.
The real sibling is the already-open row *"7f unrunnable when base exists only as a
remote-tracking ref"* — same mechanism, one phase along; they should be fixed together, and the
fix is about how a trunk ref is resolved (try `main`, then `origin/main`, or report which it
tried), not about the heuristic.

---

## 8. `#56` — eleven impl-plan rows naming a different AC

**VERDICT: CANNOT PROBE.**

I did identify the document with confidence. The row is a HemaSuite WSG-lane row; it is carried
verbatim through four handoffs there and never elsewhere:

```
$ cd /Users/kimhawk/orca/HemaSuite && grep -rn 'eleven impl-plan rows\|eleven rows whose' --exclude-dir=.git .
docs/handoffs/2026-09-10-…__phase5-closed-phase6-four-findings.md:181:- **#56 eleven impl-plan rows naming a different AC** — unowned, unchanged.
docs/handoffs/2026-09-10-…__task-14-shipped-inert-helper.md:235:- **#56 — eleven impl-plan rows whose prefix names a different AC. Unowned, unchanged.**
docs/handoffs/2026-09-10-…__tasks-15-16-shipped-task-18-red.md:194:- **#56 — eleven impl-plan rows whose prefix names a different AC. Unowned, unchanged.**
```

The earliest and fullest statement adds the only extra fact recorded anywhere:

```
docs/handoffs/2026-09-09-…__tasks-4-7-shipped-hermeticity-seam.md:134:
- **#56** Eleven impl-plan rows whose prefix names a different AC; six already shipped as test
  functions. Unowned, unchanged.

docs/handoffs/2026-09-09-…__tasks-7-13-shipped-premises-falsified.md:144:
- **#56** … Task 13's row-5/row-7 re-prefixing at v1.12 is the same class, already fixed there.
```

That pins the document to
`/Users/kimhawk/orca/HemaSuite/hematology-paper-writer/docs/archive/2026-09/website-source-grounding/website-source-grounding.impl-plan.md`
(6651 lines, 202 `AC-x.y` occurrences).

**What blocked the probe.** The eleven rows were never enumerated — not in any of the four
carriers, not in the WSG audit reports, not anywhere in either repo. The claim is
*prefix-vs-AC-semantics*: whether a row's `AC-x.y` prefix names the AC the row actually
implements. Settling that per row requires reading each row against the spec's AC text, and
without the original enumeration there is no way to know I am judging the same eleven rows the
finding meant. The mechanical proxy I could run is not the same measurement, and it does not
reproduce the count:

```
$ # lines carrying BOTH an AC-x.y and a test_ac_a_b, with no AC in common
lines carrying BOTH an AC-x.y and a test_ac_a_b with NO overlap: 3
  L3511 prefix=[(7,3),(7,9)] test=[(7,7)]   ← a real task row; its own text says
        "**moved here from Task 6 at v1.2**", i.e. a known, explained re-prefixing
  L6632 prefix=[(11,3),(7,5)] test=[(5,8)]  ← a Version History line, not a row
  L6646 prefix=[(7,5),(9,2)]  test=[(5,12)] ← a Version History line, not a row
```

One candidate task row, not eleven — which **neither confirms nor refutes** the claim, because
prefix-vs-test-name agreement is a different property from prefix-vs-AC-semantics. Reporting
"FALSE, only 1" off this would be a false refutation from the wrong instrument.

**One hazard for whoever picks this up:** the `#NN` key is not unique in HemaSuite's own
handoffs. `#56` names *"nccn.org subdomain gap"* in
`docs/handoffs/2026-08-07-feature-199-guideline-source-grounding__phase5-tasks-5-12-shipped.md:112`
and `#57` names *"Task 14 never audited"* at `:131` of the same file — different rows under the
same numbers. The backlog was renumbered at some point, so resolve these by row TEXT, never by
number. To close #56 someone needs the original enumeration; if it cannot be recovered, the
honest move is to re-derive it once against the spec and re-file with the eleven rows named.

---

## Summary

| # | Item | Verdict |
|---|---|---|
| 1 | PINDRIFT bare-L | **HOLDS** (term undefined in-repo; carried by Reading A alone) |
| 2 | LINEPIN else-arm | **HOLDS** (two defects: false cannot-judge + dead `NO_LINE_PINS`) |
| 3 | version-history | **HOLDS** (and `86dde1c` sharpens the mismatch) |
| 4 | #57 — 5e spec-reviewer READ-ONLY clause | **HOLDS, narrowed** (only a diff-scoped restriction) |
| 5 | #33 — `--registry` default follows cwd | **HOLDS** (both halves; divergence realised on disk) |
| 6 | #37 — `<slot>` in prose backticks | **HOLDS** (but the widening is not its cause) |
| 7 | #38 — `--trunk main` unreadable | **HOLDS** (not moot; "same root as WSG-5" is FALSE) |
| 8 | #56 — eleven impl-plan rows naming a different AC | **CANNOT PROBE** |

**7 HOLDS · 0 FALSE · 1 CANNOT PROBE.** No premise was refuted outright — unusual for this
repo's carry-forward record, and worth noting against the four-of-five prior rate.

Two *sub-claims* inside the eight were refuted and should be struck from the carry:

1. **"#38 shares a root with WSG-5"** — false. Ref resolution in the preflight vs the
   first-commit heuristic; `3a04342` touched only the latter.
2. **"the `<INLINE[^>]*>` widening made the `<slot>`-in-backticks class worse"** — the class
   pre-dates the widening and fires identically under the narrow pattern. The widening does
   broaden the surface, but it did not create the class #37 names.

One defect was found that the carried claims did not name: **`NO_LINE_PINS` is dead code**
(item 2) — a hard rule promised by both the module docstring and `SKILL.md` with no code path
enforcing it.

**Two of my own readings were wrong and were corrected before filing**, both caught by a review
pass rather than by a probe, and both in the direction of over-claiming: I read #57's scoped
`for the target paths` as a global tool allowlist and was about to file it FALSE, and I gave item
1's Reading B equal weight with Reading A when the `ALLOWED:`-echo scenario is contrived. Any
reader who wants only the load-bearing claims should read §5, §2 and §3.

## What I could not probe and why

- **`#56` (item 8) — the only CANNOT PROBE.** Document identified; the eleven rows were never
  enumerated in either repo, and the claim is a semantic prefix-vs-AC match that cannot be
  settled without that enumeration. Detail and the failed proxy measurement are in §8. Do not
  read my proxy's "3 lines / 1 row" as a refutation.
- **The meaning of "bare-L" (item 1)** — not recoverable from the repo: one occurrence, no
  definition. I probed both code-derivable readings and both HOLD, so the verdict is safe, but
  the *intent* is unconfirmed and the fixer should choose deliberately.
- **`#37` was probed through the real `_cmd_exec` advisory but with no agent dispatched** — I
  passed an unknown flag so the code aborts after warning. The warning text and slot extraction
  are the real ones; what is unprobed is the downstream behaviour of an agent actually receiving
  such a prompt, which no offline probe can reach.
- **A review pass WAS run, after the first draft was written and durable.** It changed two
  verdicts' substance: #57 went from FALSE to HOLDS-narrowed (I had over-read a diff-scoped
  restriction as a global tool allowlist), and item 1's Reading B was demoted to a secondary nit.
  Both corrections are folded in above; the numbers in the summary table are post-review. Worth
  recording that neither error was reachable by any probe I ran — a probe confirms what a command
  prints, not whether I read an English qualifier correctly. cf.
  `[[feedback_fresh_reviewer_on_a_green_batch]]`.
- **Nothing in `/Users/kimhawk/orca/HemaSuite` was modified.** All reads. Both registry files
  were opened read-only and their mtimes are unchanged (`Sep 11 07:28:03 2026`).
