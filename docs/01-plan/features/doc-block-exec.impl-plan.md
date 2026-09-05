# Implementation Plan: doc-block-exec

> Source: docs/02-design/features/doc-block-exec.design.md (post-audit, v1.103 — the revision answering the r13 delta self-review)
> Paired spec: docs/01-plan/features/doc-block-exec.spec.md (v1.60) · paired plan: docs/01-plan/features/doc-block-exec.plan.md (v1.98)
> All three re-derived at `700c599` on 2026-09-04 at the moment v1.48 was written, with `git show 700c599:<doc> | grep -oE '^- v1\.[0-9]+' | tail -1` — read out of the **commit**, not the working tree, because the three sibling documents were being revised concurrently by their own authors while v1.48 was written, and a working-tree read would pin a document no commit contains. The three sibling authors are working **concurrently**, so any of these may be one behind by the time this is read — that is drift, not a finding. v1.35 pinned v1.92/v1.53/v1.85 and all three moved within the same session; v1.36 pinned v1.93/v1.55/v1.86 of which two moved again by `a8e0372`; v1.38's v1.93/v1.56/v1.87 was one behind on the design and two behind on the plan by `335f535`, with only the spec unmoved; v1.40's v1.95/v1.57/v1.90 was one behind on **all three** by `35698f9`; v1.41's v1.96/v1.58/v1.91 was again one behind on **all three** by `6f0ee85`, all three having moved in that commit; v1.42's v1.97/v1.59/v1.92 was one behind on **all three** at `cf3a862` — the **third consecutive** revision behind on every sibling, and `git diff --name-only 6f0ee85 cf3a862 --` names all three sibling files, so all three moved across that span too; and v1.43's v1.98/v1.60/v1.93 was one behind on the **design and the plan** at `4e4a00c` and **correct on the spec** — the first revision in six not behind on all three; v1.44's v1.99/v1.60/v1.94 was one behind on the **design and the plan** at `68a70d6` and again **correct on the spec**, two consecutive revisions not behind on all three (`git diff --name-only 4e4a00c 68a70d6 -- docs` names the design and the plan and does **not** name the spec); and v1.45's v1.100/v1.60/v1.95 is one behind on the **design and the plan** at `7d8e797` and **correct on the spec** for the third consecutive revision (`git diff --name-only 68a70d6 7d8e797 --` over the three siblings names the plan and the design and does **not** name the spec); and v1.46's v1.101/v1.60/v1.96 is one behind on the **design and the plan** at `1cbddb7` and **correct on the spec** for the fourth consecutive revision (`git diff --name-only 7d8e797 1cbddb7 --` over the three siblings names the plan and the design and does **not** name the spec); and v1.47's v1.102/v1.60/v1.97 is one behind on the **design and the plan** at `700c599` and **correct on the spec** for the fifth consecutive revision (`git diff --name-only 1cbddb7 700c599 --` over the three siblings names the plan and the design and does **not** name the spec). **The pins on the two lines above are v1.48's own re-derivation at `700c599`, not v1.47's carried forward** — and they are expected to be one behind again immediately, because the design and plan authors are revising concurrently with v1.48. Measured, not inferred: `git diff --name-only cf3a862 4e4a00c --` over the spec is **empty**, and the spec's last version line reads v1.60 at `8909ec4`, `cf3a862`, `7982c18` and `4e4a00c` alike, against v1.59 at `6f0ee85`. That is the measurement behind this sentence, not a supposition.
>
> These three pins go stale the way Task 5's SKILL.md line numbers and AC-6.4's suite floor did, and for the same reason — they name a moving value in another file. **Re-derive them, never trust them**: `grep -oE '^- v1\.[0-9]+' <doc> | tail -1` gives each document's current version, and that is the check to run before acting on anything this header claims. They were last correct at the commit named above; a reviewer finding them behind is looking at expected drift, not a finding. **This header is the one place a sibling's CURRENT version number may appear at all** — the Conventions rule below forbids every other sentence in this document from stating what a sibling currently says, and the reason this line survives it is that it names the commit it was derived at, carries the command that re-derives it, and declares its own staleness as expected. It does **not** forbid a bare provenance citation of the form "(design v1.85)", which names the revision a claim came *from* rather than the revision a sibling is *at*; the Conventions bullet below blesses those explicitly and this document carries roughly forty of them (impl-plan audit v45).
> Branch target: feature/doc-block-exec

## Executive Summary

One new module, `h-mad/scripts/h_mad_doc_block_exec.py`, lands in five tasks. Task 1 (`wiring`)
creates the scanner, the public bounder, extraction and selection **and, in the same task,
re-points `docsections.py` at that bounder** (the design's author-together order; the
single-source contract never has an intermediate commit with two bounders). Tasks 2–4
(`new-behaviour`) add substitution; execution + bounding; CLI + registry. Task 5 (`wiring`) tags
the Second-surface gate fence and migrates `test_h_mad_collect_report_docs.py`'s executing path.
Every guard the design names carries a mutation row bound to one named test; the three specs
(`doc_block_exec.json` 86 rows, `doc_block_exec_wire.json` 8, `docsections.json` 8) must report `ALL_CAUGHT`.

## Conventions binding every task

- **Interpreter**: `python3.11` (the pinned interpreter with pytest). Every command below runs
  from `h-mad/` unless stated. Never invoke `timeout`/`gtimeout` anywhere (AC-5.3 scans the source).
  **Two spellings of a test path follow from that, and both are deliberate**: a node ID quoted as a
  mutation spec's `test` key or inside a spec's `command` array is spelled the way the shipped
  specs spell it and the harness runs it, relative to `h-mad/` —
  `tests/test_h_mad_doc_block_exec.py::test_duplicate_headings_refuse`; a test **cited in prose as
  a name** rather than as a command to run is written repo-relative, like every other path pin in
  this document — `h-mad/tests/test_h_mad_precheck_doc.py`. The four citations of the standing
  `SKILL.md`-pin control below are in the second form for that reason.
- **Test file for Tasks 1–4, plus Task 5's two tree-level tests**: `h-mad/tests/test_h_mad_doc_block_exec.py`
  (new in Task 1, extended by later tasks). API tests import the module as
  `import h_mad_doc_block_exec as dbe` with `h-mad/scripts` on `sys.path` (the same arrangement
  `test_h_mad_collect_report_docs.py` uses at its `:22` `sys.path.insert(0, str(SCRIPT_DIR))`).
- **CLI transport split** (design §Test Strategy, last paragraph): every verdict a **real input or
  a real fault** can produce is exercised through
  `subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)` where
  `REPO_ROOT = Path(__file__).resolve().parents[2]` and `SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_doc_block_exec.py"`,
  so exit codes are the real process's — marked `(subprocess)` in the ACs. A verdict that needs
  one of the **nine** fault injections — the eight module seams `_final_write`, `_close_stream`,
  `tempfile.mkdtemp`, `os.chmod`, `shutil.rmtree`, `os.killpg`, `os.unlink`, `os.lstat`, or the `Popen`
  instance wrapper for `communicate`/`wait`/`poll` —
  calls `dbe.main(argv)` **in-process** — its return value is the
  exit code and `capsys` captures the `DOCBLOCK:` and detail lines — because a `monkeypatch`
  cannot cross an exec boundary; marked `(in-process main)`. Two subprocess tests in Task 4
  (`test_cli_exit_zero_propagates`, `test_cli_exit_two_propagates`) pin that `sys.exit(main())`
  turns the return value into the process exit, so the in-process code is the real code.
- **Fixtures are hostile**: markdown strings written to `tmp_path`, with mixed heading levels,
  fences quoting fences, a path containing a space, a body with CRLF, and a key containing regex
  metacharacters.
- **Fault injections — one canonical list of nine, all via `monkeypatch` (restored on exit),
  `subprocess` never mocked** (design v1.73 §Test Strategy, stated identically there; the list grew
  from eight to nine at round seventeen's decision 3c, and the design carries the identical nine):
  **eight
  module-level seams** in the helper's namespace — `os.killpg` (AC-4.6 reap only), `shutil.rmtree`,
  `tempfile.mkdtemp`, `os.chmod`, `os.unlink` (AC-3.10's rollback read-back only, because a
  directory writable when the first arm creates its file cannot be made unwritable between the two
  arms of one call), `os.lstat` (AC-3.10's rollback identity check only, because the mismatch it
  guards against is a concurrent replacement between two syscalls of one call and cannot be staged
  from outside), the module's `_final_write(handle, text)` seam and its `_close_stream(handle)`
  seam — **plus one instance-level wrapper**: the recorded `Popen` instance's `communicate`, `wait`
  and `poll`. Those three bound methods are **one** injection, not three, so the list is nine, not
  eleven. Recording pass-throughs of `subprocess.Popen` and `os.open` are observations, not
  injections, and are allowed.
- **How the instance-level wrapper is installed**: the recording `subprocess.Popen` pass-through
  itself shadows the bound method on the instance it is about to return. The test binds
  `real_popen = subprocess.Popen` **before**
  `monkeypatch.setattr(dbe.subprocess, "Popen", recording_popen)` — the same rule the `real_rmtree`
  and `real_killpg` bindings follow, and without it the pass-through recurses, because
  `dbe.subprocess` is the process-global module. Then
  `inst = real_popen(*a, **kw); inst.communicate = _raise_once(inst.communicate); return inst`
  (an instance attribute shadows the class method; `Popen` defines no `__slots__`), where
  `_raise_once(bound)` raises `OSError(errno.EIO, "Input/output error")` on its **first** call and
  delegates to `bound` on every later call. The wrap must happen inside the pass-through, because
  `run_block` calls `communicate` immediately after `Popen` returns and the test never holds the
  instance before that. `wait` is wrapped the same way for
  `test_drain_wait_oserror_is_launch_failed_collect` and `poll` for
  `test_poll_oserror_is_launch_failed_collect`. `test_wait_after_kill_is_bounded` uses a
  **record-and-raise** variant of the same shape: on its first call it records the `timeout`
  keyword it was given and raises
  `subprocess.TimeoutExpired(cmd=["bash"], timeout=dbe.DRAIN_SECONDS)`, and on every later call it delegates,
  so the test's own teardown `recorded.wait()` still passes through. That is a third use of the one
  wrapper, not a third wrapper.
- **Mutation spec** `h-mad/tests/mutation-specs/doc_block_exec.json`: `root` is `../..`,
  `command` is `["python3.11", "-m", "pytest", "tests/test_h_mad_doc_block_exec.py", "-q"]`,
  `target_command` is `["python3.11", "-m", "pytest", "-q"]`, every mutation has a `test` key that is
  the **full node ID** `tests/test_h_mad_doc_block_exec.py::<name>` — exactly ONE `test` key per
  row, even where a second test also goes red on the mutant (that test stays a regression test,
  never the spec's key: for `final-write-close-not-in-finally` the canonical key is
  `tests/test_h_mad_doc_block_exec.py::test_final_write_failure_before_close_still_closes` and
  `test_final_write_close_failure_is_mapped` is the regression test. **A second such pair exists**
  and the earlier sweep missed it (impl-plan audit v25, which is why this list is now stated
  rather than asserted as clean): `duplicate-heading-takes-first`'s canonical key is
  `tests/test_h_mad_doc_block_exec.py::test_duplicate_headings_refuse`, with
  `test_bare_form_duplicate_headings_refuse` the regression test on the same guard. **Round
  seventeen took that population from two to FIVE, and the three additions are written here rather
  than left to be re-found**: `spawn-valueerror-unmapped` (Task 3), whose canonical key is
  `tests/test_h_mad_doc_block_exec.py::test_nul_in_document_block_is_a_launch_failure` with
  `test_nul_in_preamble_is_a_launch_failure` the regression test on the same guard through the
  other composition path; and `field-quoting-removed` (Task 4), whose canonical key is
  `tests/test_h_mad_doc_block_exec.py::test_dynamic_field_cannot_forge_a_token` and which
  collaterally reds `test_newline_in_dynamic_fields_cannot_forge_a_verdict_line`,
  `test_unicode_line_separators_cannot_split_a_verdict_line` and
  `test_quote_in_dynamic_field_cannot_close_the_value`, because all three of those assert their
  payload appears inside the field's double quotes and that row strips the quotes — the only member
  of the five that reds **three** further tests; and `field-escape-removed` (Task 4), whose
  canonical key is `tests/test_h_mad_doc_block_exec.py::test_quote_in_dynamic_field_cannot_close_the_value`
  with the newline test the regression test on the same mutant. The measured matrix establishing
  both is in Task 4 beside the rows. Those five are
  the only rows in **`doc_block_exec.json`** whose mutant reds a second named test; the docsections rows bind
  to the WIRE-PIN / their `_killed_by` / `test_docsections_imports_from_an_unrelated_cwd`, and the
  wire rows to one pin each, with **`wire-revert-extract`'s, `wire-unconditional`'s and
  `consumer-from-import`'s** collateral
  reds documented per row rather than promoted to keys. **`wire-unconditional` was missing from that
  carve-out through v1.53** (impl-plan audit v48 teammate must 2): its row documents its own
  collateral red on `test_only_the_exec_scan_hand_rolls_extraction`, and an omitted member falsifies
  the completeness claim the carve-out exists to protect — the same defect this bullet repaired on the
  `doc_block_exec.json` side when round seventeen took that population from two to five. **The
  enumeration is DERIVED and the derivation rule is stated here rather than the sentence recalled**:
  read each of the 8 `doc_block_exec_wire.json` rows, the 8 `docsections.json` rows and the 86
  `doc_block_exec.json` rows for a per-row clause of the form *goes red with it* / *reds too* /
  *stays a regression test, not this row's key*, and take the members from that reading. Re-derived
  that way for v1.54, the wire side has exactly three members and the other five wire rows each name
  one killer and no collateral: `wire-revert-extract` reds
  `test_only_the_exec_scan_hand_rolls_extraction` and `test_gate_block_refuses_an_untagged_recipe`;
  `wire-unconditional` reds `test_only_the_exec_scan_hand_rolls_extraction`; `consumer-from-import`
  reds WIRE-PIN 1, WIRE-PIN 2 and `test_gate_block_refuses_an_untagged_recipe`. **Residual, stated
  exactly**: a row whose collateral is stated in a THIRD wording is invisible to that reading and is
  closed only by a reviser reading each row, exactly as the sibling-prose class beside it is) — and every `find` anchor
  matches the landed source exactly once (the harness applies one `find`/`replace` pair per row
  via `str.replace` — `h-mad/scripts/h_mad_mutation_harness.py:645`, inside `run_spec` (`:482`) —
  so a multi-site revert must be expressed as one replacement). Each task appends its rows; the file is created in Task 1. Run
  `python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/doc_block_exec.json`
  and read the `MUTATION:` token — `ALL_CAUGHT` is required before the task is GREEN.
- **When each row's payload is fixed — deliberate, not an omission** (impl-plan audit v20, whose
  must-fix asked for every `doc_block_exec.json` payload to be written here and is REFUTED on this
  ground; the file held 76 rows at that cycle and holds 86 now, and the ground is unchanged by the
  count). **The ordering is this document's own constraint**, adopted from the design's §Test Plan
  and reached by locator rather than by a claim about its content —
  `grep -n 'the mechanism column is what the anchor must express' docs/02-design/features/doc-block-exec.design.md`,
  one hit, verified at `700c599`: exact `find` anchors are set from the landed source **in the same
  task that lands it**, each exact-once, and the mechanism column is what the anchor must express.
  So for
  `doc_block_exec.json`: **the mechanism named beside each row is the contract and is fixed now**,
  as is the row's `test` key (a full node ID, fixed now); the `file`, the exact-once `find` and the
  `replace` are written **at 5e, from the landed source of the task that just went GREEN**.
  `h-mad/scripts/h_mad_doc_block_exec.py` does not exist until 5d, so quoting anchors into it now
  would mean inventing source text and then pinning mutations to text nobody has written — the
  placeholder class this document forbids, and a `find` that misses is scored a refusal, not a
  kill (`h-mad/scripts/h_mad_mutation_harness.py:609–623`, the `anchor_status` refusal branch inside
  `run_spec`, `:482`). **The axis is not which spec a row belongs to — it is whether the row's anchor file AFTER the task
  that lands its payload is a file that already exists** (impl-plan audit v34; the "after the task"
  clause added at v1.45, impl-plan audit v42). **The rule**: a row whose post-task anchor file
  exists today carries its
  `find`/`replace` payload **in this document already**, quoted exactly from that file; a row whose
  post-task anchor file is `h-mad/scripts/h_mad_doc_block_exec.py` carries its mechanism and its `test` key
  now and gets `file`, the exact-once `find` and the `replace` at 5e, from the landed source of the
  task that just went GREEN. **That clause is load-bearing and it was missing**: the earlier
  wording keyed on the anchor file *at HEAD*, and the two `docsections.json` rows Task 1
  re-anchors carry `"file": "tests/docsections.py"` in the shipped spec today — a file that does
  exist — so the rule as worded put them on the payload-now side, where the enumeration below then
  correctly forbids them. A 5e implementer who applied the rule rather than reading the list got
  two refusals out of the contradiction. The stated residual below does not cover this: it names
  the anchor-*text*-rewritten case, not the anchor-*file*-moved one. **`doc_block_exec.json`'s 86
  rows are NOT wholly on the second side, and saying so was an over-statement of this rule against
  its own row list** (impl-plan audit v47 codex should 2): **85** of them anchor in
  `h-mad/scripts/h_mad_doc_block_exec.py`, which does not exist today, and are wholly on the second
  side; the eighty-sixth is `registry-row-removed`, whose anchor file is `h-mad/SKILL.md` — a file
  that **does** exist, which is the first side's test — while the text it anchors on is the
  Helper-scripts entry Task 4 writes and nothing in the tree carries yet. So it is the
  anchor-file-exists / anchor-text-new case, the exact residual this bullet names one paragraph
  down, and it follows the second side's timing for that reason and not because its file is
  absent: mechanism and `test` key fixed now, `file`/`find`/`replace` written at 5e from Task 4's
  landed registry entry. The row list in Task 4 already annotates it, and only it, as targeting
  `h-mad/SKILL.md`, so the two statements now agree.
  `doc_block_exec_wire.json`'s 8 rows are wholly on the first (anchor:
  `h-mad/tests/test_h_mad_collect_report_docs.py`). `docsections.json` **straddles the axis**:
  **six** of its eight rows anchor in `h-mad/tests/docsections.py` and carry their payloads here —
  the eight being the population this feature ships **by 5e**, against **four** rows in the shipped
  `h-mad/tests/mutation-specs/docsections.json` at `68a70d6`, all four of which carry
  `"file": "tests/docsections.py"` today (read out of the file, not inferred) —
  `offset-anchored-bound-runs-to-end-of-file`, `missing-heading-returns-empty-instead-of-failing`,
  `docsections-delegation-reverted`, `docsections-syspath-setup-removed`,
  `docsections-heading-lookup-reverted` and `docsections-local-bounder-restored` — while **two**,
  `fence-tracking-removed` and `section-no-longer-owns-its-subsections`, are re-anchored by Task 1
  into `h-mad/scripts/h_mad_doc_block_exec.py` (the scanner's state transition and the bounder's
  heading match) and therefore follow the `doc_block_exec.json` rule exactly: mechanism and `test`
  key fixed now, `file`/`find`/`replace` written at 5e from Task 1's landed source. Carrying their
  **current** payloads forward is specifically forbidden: today's two anchors in
  `h-mad/tests/mutation-specs/docsections.json` are the local scanner's `startswith` fence test and
  the local bounder's `re.match` heading test, both of which Task 1 **deletes** from
  `h-mad/tests/docsections.py`, so each `find` would match zero times and be scored a refusal, not a
  kill (`h-mad/scripts/h_mad_mutation_harness.py:609–623`, `run_spec`), against AC-1's last bullet, which requires
  `ALL_CAUGHT` over all eight rows. **Residual, stated exactly**: the axis is file existence, so a
  row whose anchor *file* survives but whose anchor *text* a task rewrites is not covered by it —
  `offset-anchored-bound-runs-to-end-of-file` and
  `missing-heading-returns-empty-instead-of-failing` are that case, and they are covered instead by
  the separate Task 1 rule that each such row's `find` **and** `replace` are re-read against the
  migrated body in the same edit. Nothing about the `ALL_CAUGHT` evidence is weakened by
  this: every row is still one guard, one named killer, one exact-once anchor, and each task's
  GREEN gate runs the harness over every row landed so far.
- **Single source of the fence grammar**: **within the two files this feature touches —
  `h-mad/scripts/h_mad_doc_block_exec.py` and `h-mad/tests/docsections.py`, and nowhere wider** —
  marker-run **recognition** — the literals ```` ``` ```` and
  `~~~`, the run-length regex, and any `in_fence` toggle — lives in exactly one function body,
  `_fence_events`, and so does ATX heading recognition (the `heading` event kind); `extract` and
  `fence_aware_end` are thin consumers that read only the event's
  `kind`/`marker`/`run`/`indent`/`info`/`candidate`/`level`/`text` fields (Task 1, mutation `scanner-duplicated-in-consumer`).
  **The scope sentence is the contract, not any count.** The invariant has a file scope and a
  subject scope, and each one leaves a residual; both are stated below, because v1.39 closed the
  fence-BLIND half of the subject axis and left the fence-AWARE half of the file axis unswept and
  unnamed (impl-plan audit v37). The scope stated above is what the two guards actually enforce:
  `scanner-duplicated-in-consumer` mutates the helper module, and
  `test_docsections_has_no_second_bounder` is scoped to `docsections.py`. Neither reads any other
  file in the tree, and no guard anywhere does.

  **Residual (a) — the subject axis, and it is deliberate**: the rule is scoped to marker-run
  **recognition**, so a
  `##`-slicer that performs none of it is outside the rule and outside
  `test_docsections_has_no_second_bounder`, which is scoped to `docsections.py`. The residual is a
  **class** — *hand-rolled `##`-slicers that recognise no marker run* — and it is given as a scope
  rule plus a command, **never as a cardinality**, because no mechanical sweep over that class is
  both sound and complete. *Over-count*: the sweep
  below prints **23** named helpers on the tree v1.54 ships, up from **22** at `335f535` and at
  `74e126f`, under `h-mad/tests`, `h-mad/scripts` and `handoff` holding the
  substring `## ` beside a `find`/`index`/`split`/`startswith` call, and several are not section
  slicers at all (`traced_bindir`, `run_with_bindir`, `_trim_version_history` and two `main`s among
  them). **The 22 → 23 is a real move across the round-sixteen freeze and this document cleared it
  by assertion rather than by re-running** (impl-plan audit v47 must 4). Re-run against blobs with
  `git show` at each sha, the same command each time: `335f535` **22**, `74e126f` **22**, `af19d53`
  **23**, `09e9307` **23**, **23** at `cac6edc`, and **23** on the tree v1.54 ships — the sweep reads the tree and not this document, so its two v1.54 readings coincide. The new member is
  `h-mad/scripts/h_mad_assemble_audit.py:264` `_trim_version_history`, verified at `cac6edc` by
  `sed -n '264p'` reading `def _trim_version_history(text: str, keep: int | None, *, ref: str) -> str:`
  — the function the round-sixteen freeze commit itself added, which
  `git diff --name-only 3f70eb3 af19d53` names among its files. **The member's LINE moved across
  `b39d9dc` and the pin is RE-PINNED rather than re-stamped** (round-eighteen sheet C2 i): it stood at
  `:247` through `fbc2ea0`, `b39d9dc` inserted `DISPATCH_OVERHEAD_CHARS` and `prompt_oversize` above
  it, and `sed -n '247p' h-mad/scripts/h_mad_assemble_audit.py` at `cac6edc` prints an EMPTY line, so
  the old pin is provably wrong on this tree. The integer and the member are both re-derived from the
  sweep's own output rather than edited by hand: it prints
  `h-mad/scripts/h_mad_assemble_audit.py:264 _trim_version_history`. It is a **non-slicer the over-count
  admits**, exactly as `traced_bindir` and `run_with_bindir` are, so the residual's meaning is
  unchanged and only its integer moved. **The consequence for the freeze-scope check is stated
  rather than generalised**: of this bullet's instruments, the fence-state screen and the
  source-guard screen are unmoved across every sha above, and this `## `-slicer sweep is not — so
  "the AST censuses do not move with the freeze" was false of one of the two and is replaced by
  this per-screen reading. **The stamp travels with the integer and not with the paragraph**
  (impl-plan audit v47 should 3): every figure in this sentence names the tree it was read on
  inline, which is the form every other screen in this document already uses. *Under-count*:
  it cannot see `_section` (`h-mad/tests/test_h_mad_collect_report_docs.py:40`), whose two `##`
  anchors arrive as **parameters** and so appear nowhere in its body. An earlier revision of this
  bullet wrote "one such slicer is live" and named only `_titled_section`; that was a cardinality
  over an open class, and it was wrong (impl-plan audit v36).

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
                  if '## ' in seg and op.search(seg): print(f'{f}:{n.lineno} {n.name}')
  "
  ````

  Three members are named rather than left to be re-found, because a 5d or 5e reader who greps for
  `## `-slicing reaches them first. All three are **fence-blind** — none carries an `in_fence`
  toggle — all three are test-local assertion helpers slicing one document for their own pins, and
  **none is a migration target for this feature**:
  - `_titled_section` (`h-mad/tests/test_h_mad_context_budget_docs.py:69`) bounds on
    `text.index(title)` and `text.find("\n## ", start + 1)`, reached from eight call sites at
    `:301`–`:372` over `h-mad/SKILL.md` (re-derived at `74e126f`: `grep -n '_titled_section'` on
    that file gives one `def` at `:69` and eight call sites). It is not a drop-in, and the
    measurement that rules it out is located with
    ``grep -n '`_titled_section` anchors on a substring' docs/02-design/features/doc-block-exec.design.md``
    — one hit, verified at `700c599`: it anchors on a **substring**, so
    `docsections.titled_section(SKILL_MD, "Run-context ceiling")` cannot find the real heading,
    which is located by name with `grep -n '^## Run-context ceiling' h-mad/SKILL.md` — one hit,
    verified at `35698f9`, reading `## Run-context ceiling — halt the run at 80%`. **The line
    number is deliberately not written**: v1.39 wrote one here and it was the sixth recurrence of
    the stale-`SKILL.md`-pin class, caught by the standing control
    `h-mad/tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins`,
    which asserts no path-qualified `SKILL.md:`*N* pin survives this document's LINEPIN details.
    **That control is a screen for UNWRAPPED pins only, and this is a property of the shipped code,
    read out of it and executed rather than reasoned from its design** (impl-plan audit v41; the
    probe and both of its readings are published with the fold screens below). The extractor the
    control depends on is `h-mad/scripts/h_mad_precheck_doc.py`'s module-level `_CODE`, whose
    pattern excludes a newline **inside** the span, so a path-qualified pin wrapped across this
    document's ~95-column fold produces no LINEPIN detail at all and the control's `assert` passes
    on it. So the omission of the line number here is the reason this document may omit it, and the
    control is not the whole of the enforcement — the folded `SKILL.md` screen below is the half
    that covers a wrapped pin.
  - `section_text` (`h-mad/tests/test_h_mad_batch_doc_rules.py:26`) asserts exactly one
    `l.strip() == f"## {name}"` and then bounds on `lines[end].startswith("## ")`.
  - `_section` (`h-mad/tests/test_h_mad_collect_report_docs.py:40`, reached through `_second_surface`, whose own `def` is at `h-mad/tests/test_h_mad_collect_report_docs.py:49` — verified at `fbc2ea0`, and pinned here because this document lists that callee's eight call sites and named no anchor for the callee itself, impl-plan audit v47 nit) bounds on `text.find(start)`
    and `text.find(end, start_index + len(start))` over two `##` anchors passed in, and it is the
    one of the three whose **reachability this feature changes**: it lives in the consumer file
    Task 5 edits and is reached through `_second_surface()`, whose eight call sites at `335f535`
    are `:118`, `:154`, `:225`, `:248`, `:269`, `:389`, `:409` and `:431`. Exactly one — `:269`,
    inside `_gate_bash_block` — is on the executing path today, and Task 5 removes it:
    `_gate_block()` calls `dbe.extract(SKILL_MD, "## Second surface — the codex leg")` directly.
    After Task 5 `_section`/`_second_surface()` serves **text pins only**, and it is deliberately
    left in place.

  **Residual (b) — the file axis, the complement of (a), and it is the half v1.39 left unswept.**
  Residual (a) is about scanners that carry *no* fence state; this one is about scanners that carry
  fence state and are simply **outside the two files the invariant is scoped to**. Selecting on the
  toggle rather than on the `##`-slicer — a function body holding a three-backtick literal *and* a
  variable whose name contains `in_fence` or `fenced` — the sweep below prints **7** bodies at
  `74e126f`. **Exactly one is in scope**: `h-mad/tests/docsections.py:31` `_fence_aware_end`, which
  is the body Task 1 replaces with a delegating call and the reason the sweep is a usable positive
  control. The other **6** are pre-existing, none is `_fence_events`, **3 of them are
  production code under `h-mad/scripts/`**, and **no guard in this repository covers any of them**.
  That last is an absence claim, so it carries its command and its sha rather than an assertion.
  Measured at `35698f9`: a source-level guard of this class has to *read another module's text*, so
  the screen is "a `test_*` function whose body holds a three-backtick literal **and** a
  `read_text`/`getsource`/`ast.parse` call", walked over `h-mad/tests`, `h-mad/scripts`,
  `handoff/tests` and `handoff/scripts` —

  ````bash
  python3.11 -c "
  import ast, pathlib
  b = chr(96) * 3
  for root in ('h-mad/tests', 'h-mad/scripts', 'handoff/tests', 'handoff/scripts'):
      p = pathlib.Path(root)
      if not p.exists(): continue
      for f in sorted(p.rglob('*.py')):
          src = f.read_text(encoding='utf-8', errors='replace')
          for n in ast.walk(ast.parse(src)):
              if isinstance(n, ast.FunctionDef) and n.name.startswith('test'):
                  seg = ast.get_source_segment(src, n) or ''
                  if b in seg and ('read_text' in seg or 'getsource' in seg or 'ast.parse' in seg):
                      print(f'{f}:{n.lineno} {n.name}')
  "
  ````

  — and it prints **2**: `h-mad/tests/test_docsections.py:77`
  `test_the_live_phase5_section_extends_past_its_fenced_blocks` and
  `h-mad/tests/test_h_mad_version_history.py:387`
  `test_a_heading_inside_a_fenced_block_is_not_the_section_end`. **Both are behavioural** — each
  drives a bounder over a fenced document and asserts on the returned section — and neither
  asserts on the **source** of any of the six bodies, which is what a single-source guard is. So
  the absence holds, and it holds as "no *source-level* guard", not as "nothing touches these
  files": `h-mad/tests/test_h_mad_assemble_tdd.py`, `test_h_mad_precheck_doc.py` and
  `test_h_mad_version_history.py` all exercise three of the six modules' behaviour.
  **Residual on this screen**: a guard that reads a module's source through
  `inspect.getsourcefile` + `open()`, or that names the marker run as `chr(96) * 3` rather than
  writing it, is invisible to it; and it only looks at functions whose name starts with `test`, so
  a module-level `assert` or a helper-shaped guard is out of scope. The screen's own subject —
  `test_docsections_has_no_second_bounder` — does not exist yet
  (`grep -rn 'has_no_second_bounder' h-mad handoff` returns nothing at `35698f9`); Task 1 lands it,
  and it reads `docsections.py` and nothing else:
  `h-mad/scripts/h_mad_assemble_tdd.py:96` `_body_end` (toggle `fenced`, set `:114`, flipped `:118`),
  `h-mad/scripts/h_mad_precheck_doc.py:270` `scan` (`in_fence`, `:301`/`:304`),
  `h-mad/scripts/h_mad_version_history.py:86` `section_bounds` (`fenced`, `:94`/`:98`),
  `h-mad/tests/test_h_mad_context_budget_docs.py:35` `_section` (`in_fence`, `:48`/`:51`),
  `h-mad/tests/test_h_mad_hook_wiring.py:288` `_wiring_section` (`in_fence`, `:293`/`:296`) and
  `h-mad/tests/test_h_mad_pane_visible_dispatch_docs.py:26` `_section` (`in_fence`, `:50`/`:53`).
  **None of the six is a migration target for this feature** — they are named so a 5d or 5e reader
  who finds one does not read it as a defect this feature introduced, and so the next reviewer does
  not re-derive the set. **The residual, stated exactly**: after Task 1 the tree holds **one
  authoritative fence scanner and a set of unguarded hand-rolled ones outside the invariant's
  scope**; the sentence is the contract, the number is not, for the same reason residual (a) gives.

  **What this sweep still cannot see, measured rather than asserted.** It selects on the *name* of
  the state variable, so a fence-state scanner that names its state something else is invisible to
  it, and two live ones are: `h-mad/scripts/h_mad_assemble_audit.py:109` `_braces_outside_fences`
  (state `fence_char`/`fence_len`, a full CommonMark opener/closer tracker) and
  `handoff/scripts/test_handover_docs.py:534` `_fenced_blocks` (state `cur`, a `None`/list toggle).
  Both are absent from the 7 and both are genuine members of the class — which is why residual (b)
  publishes **no cardinality either**: neither sweep on this axis is complete, and the two of them
  together are still only a lower bound. It also cannot see fence state carried across function
  boundaries (a module-level variable, a class attribute, a generator's frame) or a marker literal
  that is constructed rather than written. It does not need to cover shell: at `74e126f` no `*.sh`
  file under `h-mad/` or `handoff/` contains a three-backtick literal at all
  (`grep -rln '```' --include='*.sh' h-mad handoff` returns nothing).

  ````bash
  python3.11 -c "
  import ast, pathlib
  for root in ('h-mad/tests', 'h-mad/scripts', 'handoff'):
      for f in sorted(pathlib.Path(root).rglob('*.py')):
          src = f.read_text(encoding='utf-8', errors='replace')
          for n in ast.walk(ast.parse(src)):
              if isinstance(n, ast.FunctionDef):
                  seg = ast.get_source_segment(src, n) or ''
                  names = {s.id for s in ast.walk(n) if isinstance(s, ast.Name)}
                  if chr(96) * 3 in seg and any('in_fence' in x or 'fenced' in x for x in names):
                      print(f'{f}:{n.lineno} {n.name}')
  "
  ````

  (The three-backtick literal is written `chr(96) * 3` so the command survives being pasted into a
  double-quoted shell context, where a literal backtick is command substitution.
  **A positive and a TRUE NEGATIVE control were both run at `35698f9`, and the distinction is the
  point.** *Positive*: the sweep prints `_fence_aware_end`, the one in-scope body.
  *True negative* — a **non-member the screen declines**: `_gate_bash_block`
  (`h-mad/tests/test_h_mad_collect_report_docs.py:267`) holds a three-backtick literal in its
  `re.findall(r"```bash\n(.*?)```", ...)` and carries **no fence state of any kind**, so it is not
  a member of the class, and the screen does not print it — verified by reading its body, not by
  a count. **No cardinality is published for the declined side, deliberately**: classifying a
  declined body as member or non-member needs a human read of each one, and any mechanical proxy
  for "carries fence state under another name" is exactly the blind spot this screen already has
  — `_fenced_blocks`, whose state is a variable called `cur`, would sit on the wrong side of every
  such proxy.
  **`_braces_outside_fences` and `_fenced_blocks` are known FALSE negatives, not the negative
  control**, which is what the paragraph above already says of them: they are genuine members the
  screen fails to print, so they measure the sweep's *incompleteness*, and citing either as "the
  negative" would invert the meaning of the control. That was the error in this paragraph through
  v1.40 (impl-plan audit v38).)
- **Exit-code partition** (AC-4.2): every verdict of readable input and `TIMEOUT` exit 0;
  `UNREADABLE`, `CLEANUP_FAILED` and `LAUNCH_FAILED` exit 2, and **those three are the whole of
  exit 2 — nothing reaches exit 2 without a `DOCBLOCK:` line** (design audit v81). An earlier draft of this
  bullet made argparse usage errors "the only non-`DOCBLOCK:` exit 2", which contradicted Task 4,
  the design from v1.85 on and spec AC-5.6, and would have reintroduced exactly the non-verdict
  exit that `argparse-error-unrouted` and `test_malformed_invocation_is_a_verdict` exist to
  prevent. A grammar error is a **verdict**: the parser is built at argparse's **default
  `exit_on_error` (`True`)** with its `error()` overridden to raise `BadArgs`, which `main` renders as
  `DOCBLOCK: BAD_ARGS message="<m>"` at **exit 0**. Exactly one invocation still leaves without a
  `DOCBLOCK:` line — `--help` alone, which keeps argparse's own help text — and it exits **0**,
  so it is outside exit 2 and the partition holds. No refusal line ever carries `rc=`.
- **No sentence in this document states what a sibling document currently says.** A debt or a
  clearance against the design, the plan or the spec is **cycle content, not document content**:
  it is raised in the cycle's report, paid by that document's own author inside the same cycle,
  and then outlived by this document — which nothing re-derives it against. The class has now
  recurred once per enumerated member below and every recurrence cost a full dual-surface audit
  cycle. **The count is `len(list)` and the BODY of this document writes it out in prose
  nowhere.** That is scoped to the body deliberately and it is measured, not asserted: an absence
  claim is a measurement (decision G), and v1.43 shipped this one as an unscoped absolute that its
  own next clause falsified five words later (impl-plan audit v41 — the same shape as v1.42's
  control writing its own needle). A restated integer is a second authority and a second authority
  drifts — this one did, at v1.40
  (three sites disagreeing, impl-plan audit v38) and again at v1.42, which repaired two of the
  four sites and left two saying "four" after member (5) had been added (impl-plan audit v40).
  Every reference below points **into** the enumeration by its marker rather than restating its
  size, and the marker is written **unbolded** — `member (5)` — so that a reference is never
  counted as a member. **The rule over the class**: a bolded marker of the form `**(N)**` is a
  *member of the enumeration below and nothing else*; a reference to a member is `member (N)`,
  unbolded, wherever in this document it stands.
  **The marker screen — its scope, its target and its three readings.** It is published here in
  the form the `.py:` and `SKILL` screens below already use, because it was **not**, and that is
  how the wrong reading survived: it was the one screen in this bullet shipped without a scope
  block and without its readings beside it, and every neighbouring screen that carried both
  reproduced. v1.44 published
  this screen's reading as **5** without running it, and run verbatim it returned **6** at
  `4e4a00c` and at `68a70d6` alike. The sixth hit was a *reference* to member (4), in the
  Conventions section below, written in the member form — precisely the failure the unbolding
  exists to prevent, shipped inside the sentence claiming it was prevented (impl-plan audit v42).

  ```bash
  D=docs/01-plan/features/doc-block-exec.impl-plan.md
  M='\*\*\([0-9]\)\*\*'
  awk '/^## Version History/{exit}{print}' "$D" | grep -oE "$M" | wc -l                # body
  grep -oE "$M" "$D" | wc -l                                                           # whole file
  awk '/^## Version History/{exit}{print}' "$D" | grep -oE "$M" | sort | uniq -c       # per marker
  ```

  On the tree v1.54 ships, re-run **after** v1.54's own edits landed rather than
  before them (decision K): body **5** occurrences, whole file **5** occurrences, and the third
  reading prints **five lines, each with count 1** — unmoved from v1.52's and v1.53's readings, which is a
  result and not an assumption, since v1.54 rewrites prose inside this very bullet and adds four
  acceptance criteria elsewhere. The first two must agree, since a bolded
  marker inside the Version History would be a member standing outside the enumeration.
  **The site is stamped to the revision that ships it, not to the revision whose repair last
  moved it** (impl-plan audit v45): v1.49 left this site reading `the tree v1.48 ships` while
  shipping further body edits, so the site and the Version History disagreed about which tree the
  three readings belonged to. **v1.50 and v1.51 both repeated it and this site read `the tree v1.50
  ships` through two further revisions** (impl-plan audit v46), so the rule was true and had no
  enforcement condition; it gains one here, and the condition binds every screen, control and sweep
  in this document, not this site: **a screen site's stamp is rewritten in the SAME edit that
  re-runs it**, so re-running and re-stamping cannot come apart, and a revision that re-runs a
  screen for its Version History entry and leaves the site's stamp behind has produced the defect
  rather than avoided it. **The members of that class are DERIVED, never listed** (impl-plan audit
  v47 must 2, which found the hand-written list of four short by at least two: the self-reference
  screen in Conventions below carried `the body v1.50 ships` through v1.51 *and* v1.52, and so did
  the `docs/`-sibling locator population's own reading). The derivation is a sweep of the body for
  a site publishing a reading **of this document**, keyed on the two phrases every such site uses —
  a `the tree`/`the body` v-number `ships` form, or a `re-run after` v-number form:

  ```bash
  D=docs/01-plan/features/doc-block-exec.impl-plan.md
  awk '/^## Version History/{exit}{print NR": "$0}' "$D" \
    | grep -oE '(the tree|the body) v1\.[0-9]+ ships|re-run after v1\.[0-9]+' | sort | uniq -c
  ```

  Each hit is then read, because the sweep cannot tell a live stamp from a sentence *about* an
  older one, and the rule is that a hit is a **member** only where the reading it stamps was taken
  over the shipping revision's own body. Run after v1.53's last edit landed, the sweep returns
  **15** occurrences of a v1.53 stamp across **12** lines and **9** sites, and the members are
  **eight** of those nine: this marker screen, the restated-cardinal screen, both `SKILL` screens
  (one site), the `.py:`
  series' newest chain entry, the per-needle sibling sweep, the `docs/`-sibling locator population,
  and the self-reference screen — and every one of the eight reads v1.53. **The ninth site carries
  the same stamp form and is deliberately NOT a member**: residual (a)'s `## `-slicer sweep reads
  the TREE rather than this document, so it falls outside the class's own definition; it gained an
  inline v1.53 stamp under teammate should 3 and is named here so a reader who counts nine sites
  against eight members finds the discrepancy explained rather than has to re-derive it. The **non**-members the
  same sweep returns are named so the next reviser does not re-triage them: the `.py:` series'
  four earlier chain entries (v1.44, v1.45, v1.47, v1.48), each a dated reading of the tree that
  revision shipped and correct at its own stamp; the per-needle sweep's historical series
  (v1.49/v1.50/v1.51), likewise; and the marker screen's own quotation of the v1.48 stamp it is
  narrating. **Residual, stated exactly**: the sweep keys on the two phrasings that were found
  live, so a site that stamps a reading of this document **by sha** rather than by revision word is
  invisible to it, as is one that stamps in a third wording. That residual has no live member and
  is closed only by a reviser reading, exactly as the sibling-prose class beside it is. They are unmoved by v1.49's and by v1.50's edits — and re-running
  them after the last edit landed is how that was established rather than assumed. **The
  target of the first is `len(list)`, never the literal 5**: when a sixth member is enumerated the
  target moves with it, and a target left at 5 reads a correct document as the very defect the
  screen exists to catch. The third reading needs no target at all, and that is the arm carrying
  the class — a reference written in the member form necessarily **duplicates** an existing
  member's marker, so it surfaces as a count of 2 whatever the size of the list.
  **Residual, demonstrated rather than argued**, on copies under `mktemp -d` with the repository
  untouched, each mutation named exactly, and applied as a **string** replacement rather than with
  `sed` — the mechanism has **two steps and they belong to different programs**, re-run at v1.46
  on a `mktemp -d` copy: `sed` does **not** fail silently, it exits **1** and prints
  `RE error: repetition-operator operand invalid` on stderr, echoing back the truncated `s///`
  whose search half was the fourth member's marker in its **bolded** form. That form is described
  here and deliberately **not reproduced**, under the rule stated at the end of this bullet:
  reproducing it is what broke the marker screen once already. The failure is `sed`'s own —
  `*` is a repetition operator in BRE and `sed` refuses the pattern outright; the **empty
  file** comes from the **shell**, which truncates the `>` redirect target before `sed` is ever
  executed. So the first attempt at the second mutation left a 0-byte file behind a loud non-zero
  exit, and it was caught by its
  reading of 0 markers where 5 were expected: **(a)** re-bold the `member (4)` reference in the
  Conventions section and change nothing else — the v1.44 state — and the readings are body **6**,
  file **6**, with a count of `2` against the fourth marker: both arms fire. **(b)** re-bold that
  same reference *and* unbold member (4) in the enumeration below — two independent errors
  pointing at each other — and the readings are body **5**, file **5**, every count `1`: **all
  three arms pass on a document where a reference is written as a member.** So the screen is blind
  to a cancelling pair and blind to nothing else; it is a screen a reader triages, not a gate, and
  the reading it publishes is worth nothing unless it was run on the tree that ships.
  **The rule this screen's own repair produced, and it binds every screen in this document: no
  screen's needle may appear literally anywhere in the scope that screen counts.** v1.46's repair
  of the `sed` sentence above quoted the failing invocation verbatim, and the search half of that
  invocation *was* a bolded marker, so the body reading went to **6** with a count of `2` against
  the fourth marker — the arm-(a) signature exactly, produced by a **quotation** rather than by a
  reference, and published in the same breath as **5** because the screen was **not re-run after
  that repair landed** — whether it had been run before it, or not at all, the reading cannot say,
  and neither does this sentence (delta review r13). A screen cannot tell a quotation from a
  member, and the failure is not confined to quoting a marker: a mutation string, an error message
  or a diff hunk pasted verbatim carries whatever needle it contains into the counted scope. So a
  needle that has to be discussed is **described**, never typed. **Residual, as a concrete
  category**: the rule reaches needles that are literal strings. A screen whose needle is a regex
  *class* can still be matched by prose containing no literal copy of anything — the
  restated-cardinal screen immediately below is that shape, since its pattern is a verb-plus-cardinal
  phrase and any true sentence of that shape is a hit — and nothing here detects that case; it is
  caught, if at all, by the standing requirement that every screen be re-run after the **last**
  edit lands.
  **The sweep for this exposure across the whole document, re-derived by WALKING rather than
  recalled.** The walk keys on two signatures — a body line naming this file as a scope (its path
  written out, the shell variable the fenced screens bind it to, or the angle-bracketed stand-in
  this document writes for its own path), and
  the `awk` idiom every body-scoped screen uses to stop at the Version History heading — and then
  each hit is read to decide whether it is an instrument or a provenance citation. It returns
  **nine** instruments scoped to *this document* and therefore exposed at all — **ten** with the
  screen v1.48 wrote after the walk had run, named as the tenth below; every other screen
  here counts `h-mad/`, `handoff/`, a sibling under `docs/` or a `.py` source file, where this
  document's own prose is out of scope by construction. **v1.47 published this enumeration as six,
  derived by recalling what it had repaired rather than by walking, and it was short** (impl-plan
  audit v44, which named **one** member and said in its own residual that completeness here is
  re-established by reading and not by a grep) — **short by three**, and the three is v1.48's own
  derivation rather than a figure the audit gave. An enumeration published as complete is a
  completeness measurement under decision G, and a measurement is derived, never recalled. The tenth is the self-reference screen
  v1.48 adds in Conventions below, which did not exist when the walk was run and is enumerated
  because it was written under this rule rather than found by it. The ten, and the disposition of
  each:
  **(i)** this marker screen — the live instance, repaired above; **(ii)** the restated-cardinal
  screen below — regex-class needle, the stated residual, and the reason the residual is written as
  a category rather than as a closure; **(iii)** the `.py:`-pin screens in the Conventions bullet
  below, where the seven counter-instances are **described rather than reproduced** and have been
  since v1.40, for precisely this reason; **(iv)** the two `SKILL` line-pin screens below, whose
  own probe fixture writes a single-character stand-in in place of the colon and restores it with a
  `sed` substitution *inside the probe*, so the needle never exists in this file at rest;
  **(v)** the sha-stamp screen below, whose published form writes the sha as a **pattern** rather
  than as any real one, so quoting the screen does not add a stamp to the population it counts; and
  **(vi)** the member-(5) survivorship chain's `grep -c` over this file, whose needle is a fragment
  of the offending sentence — which is why that chain **stops** at the last sha whose reading is
  still 1 and is not extended, the repair that quotes the sentence twice having driven the count to
  3 at the sha after it (the two shas are named where the chain is written);
  **(vii)** the pre-dispatch sweep in the sibling-claim bullet below, whose five needles are
  three sibling-filename-plus-colon forms, one short word naming a debt, and one regex character
  class v1.50 adds — the first four are every one of them literal, how many of them the counted
  body actually holds is a measurement and is taken per needle at the sweep itself rather than
  asserted as a universal here (delta self-review r15: v1.48 through v1.50 asserted *every one of
  them present*, and the plan-filename form reads 0 at every sha this document names in which
  this document exists — run over all of them, not over a sample), and the
  fifth cannot match itself by construction. **Its disposition is that it
  publishes no reading at all**: it is a triage aid a reviser runs and reads hit by hit, so a
  corrupted count is not its failure mode, and what the exposure costs is triage the bullet does
  not warn about rather than a wrong integer. The breakdown is derived at the bullet itself rather
  than summarised here, and it is **not** the three-of-23 an eyeball gave at `700c599`;
  **(viii)** the divergent-toolchain sweep in Task 1's AC checklist below, whose six needles are
  the six GNU-only invocations that same bullet names in prose — every one literal, every one
  inside the body it counts. **This one does publish a reading, and the reading survives only
  because each hit is triaged by name rather than compared to a target**: it returns **3**, and the
  bullet states outright that one of the three is itself, matching because it names the six tokens.
  That disclosure stood at the site and was missing from this enumeration, which is this
  enumeration's defect and not the sweep's; and
  **(ix)** the wrapped/flat probe in the `SKILL` bullet below, which runs the shipped precheck over
  two copies of this document and over this document unedited. It shares **(iv)**'s device — the
  needle written with a one-character stand-in and restored by a substitution *inside* the probe —
  and it is enumerated separately because it is a different **program**, so a repair made to the
  `grep` screens does not reach it; and
  **(x)** the self-reference screen in Conventions below, whose two needles are written as regex
  **character classes** so that the published screen cannot match itself — the only member of the
  ten whose exposure is closed by construction rather than by care, and the reason its target can
  be a hard **0** instead of a triage list.
  **The partition of the ten, with every bin's members named so the cardinals are checkable
  against the list above rather than recalled from the previous revision's sentence**: **four** had
  the rule applied before they were named — members (iii), (iv), (v) and (vi); **one** is the
  regex-class residual — member (ii); **one** is the instance that named the class — member (i);
  **one** was found by the walk *and* independently named by impl-plan audit v44 — member (vii);
  **two** were found by the walk and by nothing else — members (viii) and (ix); and **one** was
  written under the rule rather than found at all — member (x). Four, one, one, one, two, one
  sums to ten and the six bins are disjoint. **v1.48 got this sentence wrong in exactly the way
  the bullet it sits in is about**: it carried v1.47's `Four … had the rule applied` forward with
  the cardinal bumped to five over a partition that had grown a **new** bin — the member the audit
  named — and so assigned member (vii) to a bin whose defining property its own disposition four
  lines above denies it. A partition is a derived measurement under decision G no less than a
  count is, which is the argument for deriving this enumeration rather than rediscovering it a
  third time. **v1.49 then got the same bin wrong a second way, and it is recorded here rather
  than quietly corrected**: it named every bin's members — which is what made the error visible at
  all — but kept v1.48's *rather than found by the walk* clause on member (vii) while publishing
  the walk's return as **nine**, so the sentence counted nine and the partition allotted eight,
  and only one of the two halves could be true (impl-plan audit v45). **Which half is false was
  settled by re-running the walk's signatures against the member, not by preferring the more
  recent sentence**: member (vii)'s sweep line names *this document* as the scope it greps, with
  the path written out, and that is the walk's **first** signature — so the walk did reach it,
  `nine` is the half that stands, and the audit named it *independently* rather than *instead*.
  **The rule both errors break**: a bin's defining predicate is re-derived by running the walk's
  own signatures against each enumerated member, never against the previous revision's sentence
  about that member.
  **Residual of the WALK — stated as categories of what a walk of this file cannot reach, not as
  residual of the rule.** (a) An instrument that reaches this file through a **second variable
  name** — a screen that binds this document's path to some name other than the single name every
  fenced screen here uses, and greps that one. Neither signature knows it. **This category has no
  live member, and the example v1.48 gave for it was wrong on both halves.** v1.48 named the two
  `SKILL` screens and said the walk reached them only because the fence binding the variable is
  the same fence. It is not the same fence — the fence that binds the variable opens and closes
  entirely above the fence that holds the two `SKILL` screens, so the binding does not reach them
  at all, and both fences are printed in full in the `SKILL.md`-pin bullet below, so that is
  checkable by reading rather than by a grep. And they are reached regardless, because the bound
  variable is one of the spellings the walk's **first** signature accepts — signature one is *a
  body line naming this file as a scope*, and the shell variable the fenced screens bind that
  path to is one of the three forms it names — and both screen lines write it, so they are
  members of signature **one**, not a residual of it. (They are members of signature two as well,
  since both lines also write the `awk` idiom; v1.49 named signature two alone, which is the
  wrong one — signature two is the `awk` idiom and nothing else — impl-plan audit v45. The
  conclusion is unmoved: the screens are reached, and by both signatures rather than by one.)
  What (a) actually rests on is a **naming
  convention**, and nothing in this repository enforces one: a later reviser who binds a second
  name gets a screen no walk of this file finds. (The variable is deliberately not spelled out in
  this sentence. Writing it here would put the walk's own needle into the scope the walk counts,
  which is the rule this whole enumeration exists to serve; every occurrence of it in this document
  is inside a fence, and that is what keeps the walk's hit list readable.) (b) An instrument scoped to a **directory** that contains this file, so that this
  file is counted without ever being named — AC-6.1's control with its root clause deleted is live
  and does walk this document, and it is exposed to nothing only because its needle is a path glob
  rather than a string. (c) An instrument scoped to this document that lives **outside** it, which
  no walk of this file can reach at all. That category has a live member and it is named rather
  than left abstract: the standing control
  `h-mad/tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins`
  runs the shipped precheck over this document and asserts a needle form is absent from it, so a
  needle typed into this body turns a **shipped test red** rather than moving a published integer.
  It is the reason this enumeration cannot be closed from inside the document, and the reason the
  walk narrows what has to be read without replacing the reading.
  **The screen for the class, with both of its readings.** The defect is a cardinal standing beside
  a reference to this list, and the reason v1.43's "sweep for DERIVED integers" pass missed the
  live one is that it was phrased as past-perfect narrative rather than as an ordinal — so the
  screen keys on the verb, not on the shape of a number:

  ```bash
  D=docs/01-plan/features/doc-block-exec.impl-plan.md
  V='reached|holds|numbers|contains|stands at'
  N='one|two|three|four|five|six|seven|eight|nine|ten|[0-9]+'
  awk '/^## Version History/{exit}{print NR": "$0}' "$D" | grep -icE "list (had |has |now )?($V) ($N)"
  grep -icE "list (had |has |now )?($V) ($N)" "$D"
  ```

  **This screen's before/after pair could not move, and that is stated rather than presented as a
  contrast** (impl-plan audit v44). Run over every commit this document names, the body reading is
  **0** at v1.40, v1.41 and v1.42, **1** at v1.43, and **0** at v1.44 and at every revision after
  it, so **v1.44** is the last revision whose own edits moved it: on v1.44's base `4e4a00c` it read
  body **1** line / **1** occurrence against whole file **3** lines / **4** occurrences, and on the
  tree v1.44 shipped it read body **0** / **0**, whole file **2** lines / **3** occurrences. Every
  revision
  since has read the same four integers on its base as on its shipped tree, so a revision that
  publishes those two readings as a *before* and an *after* is publishing a difference its own
  edits cannot produce — the same defect decision K exists to prevent, one level up. The pair is
  therefore published as **one screen run at two points**, and the claim it carries is the
  narrower one: at `cac6edc`, the sha v1.54 is authored against, body **0** / **0** and whole file
  **2** lines / **3** occurrences; on the tree v1.54 ships, re-run after v1.54's own edits and both
  of its reopens landed rather than before them (decision K), body **0** / **0** and whole file **2**
  lines / **3**
  occurrences. **The base read `fbc2ea0` — v1.53's base — beside an after-reading that was v1.54's,
  and that is a STAMP defect rather than a figure defect**: the four integers are unmoved at
  `fbc2ea0`, at `cac6edc` and on the shipped tree alike, each re-run in its own invocation, so
  nothing published was wrong; but a before/after pair whose halves belong to different revisions is
  the same shape this document corrected at the per-needle site, and the repair is to move the base
  rather than to re-word the conclusion. What the two readings establish is that v1.54's edits did
  not reopen the class, not that they closed anything. **Both stamps are the shipping revision's, re-derived rather than
  carried** (impl-plan audit v45): v1.49 left this site naming `700c599` and `the tree v1.48
  ships` while shipping its own body edits, which made the site and the Version History disagree
  about which tree the four integers were read on. Every surviving
  occurrence is inside the Version History, dated, and pinned to the revision it records, and the
  3-over-2 is not a typo — the two lines are the **v1.41 entry**, which carries two of the three
  (its own original wording, true when v1.41 shipped, and the v1.43 bracket annotating it, which
  is itself an instance of the class and now carries a v1.44 bracket saying so), and the **v1.43
  entry**, which carries the third by quoting that same original phrase while recording the
  repair. None of the three is rewritten. **Blind arms of this screen, stated rather than left as
  a bare zero**: it
  matches only a cardinal that follows one of **five** verbs standing immediately after the word
  `list`, with at most one auxiliary in between, so
  a size restated at any greater distance from that word is invisible to it; and it cannot tell a size from
  any other cardinal, so it would fire just as readily on a true sentence counting something else
  entirely. It is a screen a reader triages, not a gate.
  The list: **(1)** v1.24's two
  quoting flags against the design, already answered eleven design revisions earlier (withdrawn
  at v1.35); **(2)** the AC-6.1 restriction flag, already landed in design v1.92 (withdrawn at v1.35);
  **(3)** the 5f note's clearance citing a drifted `spec :458` (repaired at v1.35); **(4)** the 5f note's
  **debt**, still asserted at v1.36 after spec v1.54 had paid it (withdrawn at v1.37) — the same
  class in the opposite direction, a stale clearance replaced by a stale debt; and **(5)** the
  `StreamPathUnwritable` signature sentence in the Task 4 exception block, *"The design's exception
  table agrees (v1.71, impl-plan audit v16)"*, caught by impl-plan audit v39 and repaired at v1.42
  in form (b) below.
  **Member (5) is the one that matters most, and it is why this list is incremented rather than
  scoped away.** It predates the rule — it was written at v1.17 — so it was never a *new* lapse;
  it is the class's **survivorship** arm. It outlived v1.37, the revision that wrote the rule;
  it outlived v1.39's item (9), which **reported having restated it by name** and did not touch it
  (`git diff 335f535 74e126f` on this file changes no `StreamPathUnwritable` prose, and
  `git show 74e126f:docs/01-plan/features/doc-block-exec.impl-plan.md | grep -c 'exception table agrees'`
  is 1, as at `0aac0b7`, at `35698f9` and at `6f0ee85`); and it outlived v1.41's own decision-E
  pass. **That chain deliberately stops at `6f0ee85` and is not extended to `cf3a862`, where the
  same command returns 3**: v1.42's repair quotes the offending sentence twice, once in this
  ledger entry and once in its Version History, so the count rose for the repair's own reason. It
  was a measurement of *absence of edit* while the sentence was live, and it has done its work; an
  extension would read as a break. By the time it was found, the cited design version was **26
  revisions** behind the design as of `6f0ee85`, the sha it was found at — 27 behind at `cf3a862`,
  which is the drift the header's own staleness warning describes. The lesson the members before it do not carry: **a sweep over a class with no
  detector can report a member it never edited**, so a sweep's own claim to have closed a member is
  not evidence the member moved — the diff is. ("the members before it", not "the four earlier
  members": the latter is a restated `len(list) - 1` and would drift at the next increment exactly
  as the prose ordinals did — repaired at v1.43, impl-plan audit v40.) Two forms are
  admissible in its place: **(a)** a value **this** document must carry, stated as this
  document's own constraint, with the sibling reached by a `grep -n` locator on a sentence
  unique to that sibling — for example
  ``grep -n '^| `registry-row-removed`' docs/02-design/features/doc-block-exec.design.md`` —
  verified **in the same pass** to return exactly one hit; **(b)** nothing at all. A sibling **line number** is never admissible: those
  documents are revised concurrently by their own authors, and a pin expires in under a day —
  three of this document's five design pins drifted between `1861157` and `a8e0372`.
  **The rule's axis is `docs/` siblings under concurrent authorship, and it is not a ban on line
  numbers as such** (impl-plan audit v36, which observed that the same revision adds fresh pins
  into the tree). Pins into `h-mad/` and `handoff/` source —
  `h-mad/tests/test_h_mad_portable_timeout.py:151` (`_TIMEOUT_CMD`),
  `h-mad/tests/test_h_mad_context_budget_docs.py:69` (`_titled_section`) and
  `h-mad/tests/test_h_mad_collect_report_docs.py:270` (a line *inside* `_gate_bash_block`, whose
  `def` is `:267` — it is not itself a definition, which is exactly why it needs the enclosing
  symbol written out) among them — stay admissible on two conditions: each carries its
  **repository path** *and* the **symbol name** of the definition enclosing it (`_TIMEOUT_CMD`,
  `_SCANNED`, `_ABSENCE_CLAIMS`, `_titled_section`, `_section`, `section_text`, `_second_surface`,
  `_gate_bash_block`, `run_spec`, `assemble`, `_run`, `_fence_aware_end`, `titled_section`), so a
  drifted pin self-repairs under one `grep -n` on that symbol —
  `grep -n '_TIMEOUT_CMD' h-mad/tests/test_h_mad_portable_timeout.py` is the shape — and
  the reader is never left guessing what was meant; and each is **re-derived in the revision
  that writes it** rather than carried from a report.

  **v1.40 wrote that this document "meets [these conditions] everywhere", and it did not.** Two
  surfaces found **7** counter-instances at `35698f9`, on different instances (impl-plan audit
  v38; plan audit v78's agy leg, whose finding is about this document and was routed here): 6
  directory-less `h_mad_mutation_harness.py` line pins, one directory-less `test_suite_collection.py`
  line pin, and — in this very "stay admissible" example list — a `:270` with no enclosing symbol
  beside it. (Those seven are described rather than reproduced, because writing one out in its
  broken form would make this paragraph a hit on the very grep below.) **The class is closed
  here with a SHAPE grep, never a value sweep**, because a value sweep finds only members that
  have *already* drifted, which is why sweeping the three pins known to be stale could not see any
  of these seven:

  ```bash
  awk '/^## Version History/{exit}{print NR": "$0}' \
    docs/01-plan/features/doc-block-exec.impl-plan.md | grep -E '\.py:[0-9]+'
  ```

  Every hit must be path-qualified, and the bare-filename form is the mechanically checkable half:

  ```bash
  awk '/^## Version History/{exit}{print NR": "$0}' \
    docs/01-plan/features/doc-block-exec.impl-plan.md \
    | grep -oE '(^|[^/A-Za-z0-9_.-])[A-Za-z0-9_]+\.py:[0-9]+'
  ```

  returns **nothing — 0 occurrences** — against this document at `4e4a00c`, **0** again at
  `68a70d6`, **0** again at `7d8e797`, **0** again at `1cbddb7`, the sha v1.47 is authored against
  and stamps its re-runs at,
  and **0** again
  over the revised working tree. (`4e4a00c` is the commit v1.43 was audited **at**; it is the base
  v1.44 was written **against**. That relation recurs every round — the commit a revision ships on
  does not exist while that revision is being written — so a figure names the sha it was **taken**
  on and never the sha it will ship on. **Which** shas a given revision re-ran is not asserted in
  this parenthesis and is not inferable from it; it is read off the stamp screen below.
  `4e4a00c` contains this document byte-identically as `7982c18`
  does — `git diff --name-only 7982c18 4e4a00c -- <this file>` is empty — and it is unchanged from
  `cf3a862` over `h-mad handoff`, which is the closure that lets the surviving `cf3a862` stamps
  below stand as provenance rather than be rewritten one at a time:
  `git diff --name-only cf3a862 4e4a00c -- h-mad handoff`
  is empty, so every tree figure stamped `cf3a862` is the same figure at `4e4a00c`.
  The `docs/`-facing figures are the ones that move, and **which of them a given revision actually
  re-ran is never asserted as a closure here — it is read off the stamp screen**
  (`awk '/^## Version History/{exit}{print}' <this file> | grep -oE 'at .[0-9a-f]{7,40}.' | sort | uniq -c`
  — **one command over every sha the body stamps, so the population is derived and not typed**, and
  the whole table is published in the Version History entry. An earlier form of this screen was a
  per-sha `wc -l`, which is exactly what let v1.46's residual name five of the thirteen surviving
  shas while reading as though it named all of them; a `sort | uniq -c` cannot drop a member,
  and the count of distinct shas is `wc -l` on its own output rather than a separate integer).
  v1.45 asserted such a closure and it
  was false; the rule that replaced it is stated with Task 4's mutation split. Retained for the earlier chain — `git diff --name-only 8909ec4 cf3a862 -- <this file>` is empty, as is the same diff over
  `h-mad handoff` and over all three sibling documents — so a figure re-derived at either sha is
  the same figure.) The **before**-figure, at the base the class was closed from, `35698f9`, is
  **22 occurrences across 19 lines over 8 distinct files** (`h_mad_mutation_harness.py` ×9,
  `docsections.py` ×4, `test_h_mad_portable_timeout.py` ×2, `test_h_mad_collect_report_docs.py` ×2,
  `h_mad_assemble_tdd.py` ×2, and one each of `test_suite_collection.py`,
  `test_h_mad_context_budget_docs.py`, `test_h_mad_audit_cycle.py`). **Both halves carry their own
  sha and their own unit**, which is the whole point of writing them: the after-figure is the block
  above run at `cf3a862`; the before-figure is the same block with the file read out of the base
  commit, `git show 35698f9:docs/01-plan/features/doc-block-exec.impl-plan.md | awk … | grep -oE …`,
  piped to `wc -l` for **occurrences** (22), run with `grep -E` instead of `grep -oE` and piped to
  `wc -l` for **lines** (19), and piped through `grep -oE '[A-Za-z0-9_]+\.py' | sort -u | wc -l`
  for **distinct files** (8). One `grep` yields four different true integers and a bare one is not
  a measurement.
  **Reconciling 22 against the 7 counter-instances this document reports two surfaces as having
  found**: the 7 was those two readers' *yield*, the instances they happened to name, and never a
  census. That gap — 15 members no reader reached — **is the argument for closing the class with a
  shape grep** rather than at the instances, and it is why a value sweep is the wrong instrument:
  a revision that had repaired only the reported 7 would have shipped the other 15 and read as
  closed. **Residuals on the
  shape grep, stated exactly.** (i) It matches only `.py:`*N*; a pin into a non-`.py` file, or a
  line reference written without the suffix, is invisible to it. The live instance is the
  Conventions bullet above that reaches `test_h_mad_collect_report_docs.py`'s `:22`
  `sys.path.insert(0, str(SCRIPT_DIR))` — admissible not because the grep clears it but because it
  **quotes the module-level statement verbatim**, which is a stronger anchor than a symbol name:
  the pin self-repairs on the quoted text. (ii) `grep` is line-scoped and this document hard-wraps
  at ~95 columns, so a pin split across a newline scores 0; the paragraph-folded variant
  (`awk '/^## Version History/{exit} /^$/{print b;b="";next}{b=b" "$0}END{print b}'` piped
  through `tr -s ' '` and then to
  `grep -oE '[A-Za-z0-9_./-]*\.py: ?[0-9]+'`) was re-run beside it and returns the same
  set as the line-scoped screen. The **bare-filename** half has a folded form too, and it is
  written out here rather than assumed, because the two regexes differ in exactly the place the
  fold matters: the folded bare screen is the block above with `` ` ?` `` inserted after the colon,
  `grep -oE '(^|[^/A-Za-z0-9_.-])[A-Za-z0-9_]+\.py: ?[0-9]+'`, and the screen printed earlier in
  this bullet — the one without the optional space — is the **line-scoped** bare form and allows no
  space at all. **The property is the AGREEMENT, not an integer**: all four combinations of
  {line-scoped, folded} × {bare, path-qualified} agree, both bare forms returning **0**
  occurrences and the two path-qualified populations being identical.
  **Wherever four integers are written for these four screens they are in one fixed order, and the
  order is named rather than left to be inferred from a list several lines away** (impl-plan audit
  v41 nit; every count carries its unit, and a count in a tuple also carries its identity):
  **path-qualified line-scoped / path-qualified folded / bare line-scoped / bare folded**.
  That population is a dated example and deliberately not a contract. It is stated in the form
  the before-figure is: **base commit named, measurement scoped, unit attached, and the reading
  taken on the tree the revision produces** rather than on a commit that predates it.
  **The pair immediately below is v1.44's, and it is named as v1.44's at its head rather than only
  at its end** (impl-plan audit v44 nit): it was written in the first person and disambiguated two
  sentences later, so a reader who stopped early read it as the shipping revision's. v1.44's base
  `4e4a00c` (which holds v1.43, v1.44's input, byte-identically as `7982c18` does —
  `git diff --name-only 7982c18 4e4a00c -- <this file>` is empty): **49 occurrences across 19
  folded
  paragraphs**, re-derived at v1.44 and not carried. On the working tree v1.44
  shipped — the commit for a revision does not exist while it is being written, which is why no sha
  is claimed for an after-reading — it is **49 occurrences across 20 folded paragraphs**. **The
  two halves of that pair moved differently and the difference is the point** (decision K — this
  was re-run after v1.44's edits landed, and it is the one figure v1.44's own edits changed):
  the occurrence count is unmoved at **49** and the pin population is byte-identical, checked by
  sorting both lists and diffing them (empty), because no v1.44 edit adds or removes a `.py:` pin;
  the **paragraph** count rose 19 → 20 because a fenced block that revision inserted split one
  pin-bearing paragraph in two. So 49 is the invariant, and 19/20 is a fact about today's line
  breaks rather than about the pins — which is exactly why the closure is stated as a relation.
  **Re-run at v1.45 against base `68a70d6`, which holds v1.44** (decision K again — v1.45 inserts a
  fenced block of its own, so this is a figure its own edits could move): the four screens read
  **49 / 49 / 0 / 0** at **20** folded paragraphs on the base and the same four integers at **20**
  on the tree v1.45 ships, with the pin population byte-identical between the two (both lists
  sorted and diffed, empty). v1.45's fenced block did not land inside a pin-bearing paragraph, so
  the 19 → 20 move above stays a v1.44 fact and is not restated as any later revision's.
  **Re-run at v1.47 against base `1cbddb7`, which holds v1.46** (decision K a third time — v1.47
  rewrites prose in this very bullet and appends a paragraph to it, so this is again a figure its
  own edits could move, whether or not any of them lands beside a pin):
  the four screens read **49 / 49 / 0 / 0** at **20** folded paragraphs on the base and the same
  four integers at **20** on the tree v1.47 ships, with the pin population byte-identical between
  the two (both lists sorted and diffed, empty).
  **Re-run at v1.48 against base `700c599`, which holds v1.47** (decision K a fourth time — v1.48
  rewrites prose in this very bullet and inserts sentences into it, so the folded-paragraph half is
  again a figure its own edits could move):
  the four screens read **49 / 49 / 0 / 0** at **20** folded paragraphs on the base and the same
  four integers at **20** on the tree v1.48 ships, with the pin population byte-identical between
  the two (both lists sorted and diffed, empty).
  **Re-run at v1.52 against base `af19d53`, which holds v1.51** (decision K a fifth time — v1.52
  appends this very sentence to this bullet and rewrites prose elsewhere in the document, so the
  folded-paragraph half is again a figure its own edits could move; and the enforcement condition
  the marker screen's rule gained at v1.52 makes re-running these four for a Version History entry
  without re-stamping the site the defect, which is why this member is written rather than the
  v1.48 stamp left standing as the last one):
  the four screens read **49 / 49 / 0 / 0** at **20** folded paragraphs on the base and the same
  four integers at **20** on the tree v1.52 ships, with the pin population byte-identical between
  the two (both lists sorted and diffed, empty). **Three intervening revisions are NOT claimed
  here**: v1.49, v1.50 and v1.51 did not re-stamp this series, so what this member establishes is
  that the four integers are unmoved between `700c599` and the tree v1.52 ships, not that they were
  re-derived at each revision in between.
  **Re-run at v1.53 against base `fbc2ea0`, which holds v1.52** (decision K a sixth time — v1.53
  adds `path:symbol` pins of its own to this document, so the occurrence half is a figure its own
  edits certainly move and not merely could): the four screens read **49 / 49 / 0 / 0** at **20**
  folded paragraphs on the base and **55 / 55 / 0 / 0** at **23** folded paragraphs on the tree v1.53 ships. **This is the first revision in the chain whose pin population is NOT byte-identical
  between base and shipped tree, and the three added pins are named rather than left to a diff**:
  `h-mad/scripts/h_mad_assemble_audit.py:264` (the `_trim_version_history` member residual (a)'s
  sweep gained across the round-sixteen freeze), `h-mad/tests/test_h_mad_collect_report_docs.py:49`
  (the `_second_surface` definition this document listed eight call sites for and never anchored)
  and `h-mad/scripts/h_mad_assemble_tdd.py:246` (the line that prints the expected-counts pair into
  a dispatch, cited where Task 2's RED split explains what the implementer actually compares). All
  three are path-qualified, which is why both bare screens stay at **0**, and each was read out of
  the file at the sha its own pin names — the first at `cac6edc`, where it now stands at `:264`, the other two at `fbc2ea0` — rather than transcribed. **The occurrence count rises by SIX for three new
  pins, and the doubling is this paragraph's own doing**: each of the three occurs once at the site
  that uses it and once here, in the sentence naming it — the needle-inside-scope exposure member
  (iii) already carries, arriving through a naming rather than a screen.
  **Re-run at v1.54 against base `cac6edc`, which holds v1.53** (decision K a seventh time — v1.54
  re-pins one member of this very population, so both halves are figures its own edits certainly
  move): the four screens read **55 / 55 / 0 / 0** at **23** folded paragraphs on the base and
  **56 / 56 / 0 / 0** at **23** folded paragraphs on the tree v1.54 ships, both lists sorted and
  diffed and both re-run after v1.54's last edit landed. **The population is again NOT
  byte-identical, and the delta is named rather than left to a diff**:
  the assembler's `_trim_version_history` pin occurred twice at the base as `…:247` and occurs three
  times here as `…:264` — **both spellings are written with a leading ellipsis so that this
  paragraph cannot become a hit in the screen it publishes**, the device residual (ii) already
  uses, and so that no stale `:247` is planted in a body the moved provenance would no longer flag —
  the third occurrence being this revision's own re-pin sentence naming the sweep's output line,
  the needle-inside-scope doubling exposure (iii) carries, arriving once more through a naming
  rather than through a screen. Both bare screens stay at **0** and the folded-paragraph count is
  unmoved at **23**, so the only integer that moved is the one this revision was dispatched to move.
  It is left standing rather
  than described away, because a chain entry that will not name the pins it added cannot be checked
  by reading; the cost is that the published 55 is 3 higher than the pin population a reader
  would count as distinct. The paragraph count 20 → 23 is a fact about where
  those sentences landed and not about the pins, exactly as the 19 → 20 move at v1.44 was.
  (`| wc -l` on `grep -oE` for
  occurrences, `grep -cE` for paragraphs — one `grep`, two true integers.) v1.42's own
  edits moved it from **47** to **49**, which is precisely why the closure is stated as a relation and the
  bare-filename **0**, never as a frozen count a later edit falsifies.
  **The `tr -s ' '` is a repair, not decoration, and here is the control that shows it** — the fold
  joins with a single space but **keeps the next line's leading indentation**, so a needle wrapped
  mid-phrase folds with a run of spaces in it and the unrepaired variant misses it.
  **The control is run over a fixture file, not over this document, and the fixture's needle is
  written into this document in a form no screen above can match.** That is deliberate and it is
  the defect v1.42 shipped: v1.42 published this control against its own prose, and the sentence
  publishing it wrote the needle a second time, unwrapped, which destroyed the zero the control
  reported. A control whose publication changes what it measures is not a control. The fixture,
  reproducible verbatim (run under both `bash` and `zsh`, byte-identical output). **It writes into
  a `mktemp -d` directory and removes it, never into a fixed shared path** (impl-plan audit v41
  nit): a reader who already holds the fixed path would have had it clobbered with no warning and
  no cleanup, and the whole grid below was re-run under both shells after this change because a
  fixture's path is part of the command that produces its readings:

  ```bash
  T="$(mktemp -d)"
  printf '%s\n' 'a residual reaching docsections.pyX' '  270 in _gate_bash_block' \
    | sed 's/pyX/py:/' > "$T/fold-control.txt"
  ```

  The document holds `docsections.pyX` and the substitution `s/pyX/py:/`; neither contains
  `.py:` followed by a digit, so the fixture's publication adds **0** to every figure above —
  which is checked, not assumed: the four screens over this document return the same
  **49 / 49 / 0 / 0** — in the fixed order named above,
  path-qualified line-scoped / path-qualified folded / bare line-scoped / bare folded — after this
  revision as before it. The fixture file holds the wrap. Folding it with the same
  `awk` and reading each screen gives the full **2 × 3** grid — two folds × three regexes, **6**
  readings, every one an occurrence count (`grep -oE … | wc -l`) and every one run, not inferred.
  Unrepaired fold: path-qualified **0**, bare-with-`` ` ?` `` **0**, bare-without-the-space **0**.
  `tr -s ' '` fold: path-qualified **1**, bare-with-`` ` ?` `` **1**, bare-without-the-space **0**.
  The first column's 0 → 1 is the repair, and the whole of it. The third column is the finding this
  control was extended to catch: **0 under both folds** — the repaired fold is still blind to a
  bare-filename pin that wraps between its colon and its digits unless the ` ?` goes in. Which is
  why the folded bare form above carries it and the line-scoped one does not: a line-scoped screen
  never sees a space there.
  **The bare screen's leading alternation is itself a composite, and one of its two branches had
  never fired in any published reading** (impl-plan audit v41; decision O, and this is the third
  instance of that class in this bullet). `(^|[^/A-Za-z0-9_.-])` matches either at the start of a
  line or on a non-path character before the filename. Measured over the **before**-population at
  `35698f9` — the 22 occurrences enumerated above — `grep -cE '^[A-Za-z0-9_]+\.py:[0-9]+'` is
  **0**: every one of the 22 matched through the character-class branch, and the fold fixture above
  exercises only that branch too, because its needle is preceded by a space. A second fixture fires
  the other branch, and it is a **separate** fixture rather than an extra line in the one above, so
  that the 2 × 3 grid's six readings stay exactly what they were:

  ```bash
  printf '%s\n' 'docsections.pyX270 in _gate_bash_block'  | sed 's/pyX/py:/' > "$T/col0.txt"
  printf '%s\n' ' docsections.pyX270 in _gate_bash_block' | sed 's/pyX/py:/' > "$T/col1.txt"
  ```

  Four readings, all run under both `bash` and `zsh` and byte-identical: on `col0.txt` the
  `^`-anchored form `grep -cE '^[A-Za-z0-9_]+\.py:[0-9]+'` returns **1** and the whole bare screen
  returns **1**; on `col1.txt`, identical but for one leading space, the `^`-anchored form returns
  **0** while the whole bare screen still returns **1**. The two branches therefore **discriminate
  from each other** rather than one covering for the other, which is the property a composite
  screen has to demonstrate and the one the corpus alone could never show. Both fixtures write
  `docsections.pyX` and the substitution `s/pyX/py:/`, so their publication adds **0** here on the
  same argument the fold fixture's does — checked, not assumed, by the four screens above.
  Against this document the distinction is currently inert — no `.py:` pin here wraps between its
  colon and its digits, so all four screens agree at `4e4a00c` — but "inert" is a fact about
  today's prose, and a blind form that has never been shown to fire is not a screen. That is how
  this was found, twice. (iii) The **symbol-name** half has no detector at all — the symbol may sit several words
  from the pin — so it is enforced by reading, and its recurrence is what audit v38 and plan audit
  v78 caught.
  **(iv) The four screens above cover `.py:` pins only, and the `SKILL.md`-pin class this document
  is also under has a folded half of its own.** The standing control
  `h-mad/tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins`
  is cited twice in this document as the reason a `SKILL.md` line number may be omitted, and **its
  immunity is a property of the shipped extractor, so it is executed here and not reasoned from**
  (decision Q; impl-plan audit v41). The extractor is the module-level `_CODE` in
  `h-mad/scripts/h_mad_precheck_doc.py`, whose pattern is a backtick, a run of 1–200 characters
  that are neither a backtick **nor a newline**, and a backtick. A pin wrapped across this
  document's ~95-column fold is therefore not a span at all, yields no LINEPIN detail, and the
  control's assertion passes on it. Probed in **both** directions, on copies under `mktemp -d`,
  the repository untouched:

  ```bash
  D=docs/01-plan/features/doc-block-exec.impl-plan.md
  T="$(mktemp -d)"
  for form in flat wrapped; do cp "$D" "$T/$form.md"; done
  printf '%s\n' '' 'probe `h-mad/SKILL.mdX1606` here'   | sed 's/mdX/md:/' >> "$T/flat.md"
  printf '%s\n' '' 'probe `h-mad/SKILL.mdX' '1606` here' | sed 's/mdX/md:/' >> "$T/wrapped.md"
  for form in flat wrapped; do
    printf '%-8s %s\n' "$form" \
      "$(python3 h-mad/scripts/h_mad_precheck_doc.py "$T/$form.md" --phase design --root . \
         | grep -c 'LINEPIN.*SKILL')"
  done
  printf '%-8s %s\n' unedited \
    "$(python3 h-mad/scripts/h_mad_precheck_doc.py "$D" --phase design --root . \
       | grep -c 'LINEPIN.*SKILL')"
  rm -rf "$T"
  ```

  `--phase design` is the control's own invocation, copied from it rather than chosen. It prints
  `flat 1`, `wrapped 0`, `unedited 0`, byte-identical under `bash` and `zsh`. **So the control is a
  screen for unwrapped pins only**, and the two sites that cite it now say so. The half it does not
  cover is closed the same way the `.py:` class is, with a line-scoped and a folded screen over
  this document's body, both returning **0** on the tree v1.54 ships and both re-run after
  v1.54's edits landed rather than before them (the stamp is the shipping revision's, re-derived
  and not carried — v1.49 left it at v1.48 and v1.51 left it at v1.50, both while shipping further
  edits; impl-plan audit v45 and v46. **v1.53 is the revision that most needed them re-run**: its
  guard-narrowing accounting names a line of `h-mad/SKILL.md` and reaches it by the needle
  `grep -n '^#$' h-mad/SKILL.md` for exactly this reason, so both screens staying at 0 is what
  establishes that the needle form was used and not a pin):

  ```bash
  awk '/^## Version History/{exit}{print}' "$D" | grep -oE 'SKILL\.md:[0-9]+' | wc -l
  awk '/^## Version History/{exit} /^$/{print b;b="";next}{b=b" "$0}END{print b}' "$D" \
    | tr -s ' ' | grep -oE 'SKILL\.md: ?[0-9]+' | wc -l
  ```

  **The `SKILL` screens are not blind, and that is measured on real history rather than asserted**:
  **both** forms read **1** at `74e126f`, the commit whose v1.39 shipped the sixth recurrence, and
  **0** at `335f535`, `35698f9`, `cf3a862`, `7982c18` and `4e4a00c` — six shas × two screens, every
  reading run, which is the same discrimination the `.py:` screens carry on the same axis. That
  positive is a fair test of the line-scoped form and only a partial one of the folded form,
  because v1.39's pin was **unwrapped** and so lay inside both screens' reach; the folded form's
  own distinctive arm — a pin that wraps — is what the probe above supplies, as the `wrapped`
  arm's **0** against the `flat` arm's **1**. **Residual**: neither `SKILL` screen sees a pin
  written without the `.md` suffix or into a differently named file, and the folded one shares the
  fold screens' own blind arm — a pin wrapping between the colon and the digits is caught only by
  the ` ?`, which is why it carries it.

  **The tree pins this document stamps `335f535`, `74e126f` and `35698f9` are unchanged at
  `700c599`, the sha v1.48 is authored against, and that closure is stated once here
  rather than re-stamped on ~40 pins**:
  `git diff --stat 335f535 74e126f` touches **9** files, all under `docs/`, and
  `git diff --name-only 74e126f 700c599 -- h-mad handoff` is **empty** — no file under `h-mad/` or
  `handoff/` moved anywhere across that span. The span is not short and its length is derived
  rather than described: `git log --format=%h 74e126f..700c599 | wc -l` is **16**, and the fifteen
  commits it holds below the endpoint are `0aac0b7`, `35698f9`, `6f0ee85`, `8909ec4`, `cf3a862`,
  `7982c18`, `4e4a00c`, `06ef40f`, `68a70d6`, `f91a74b`, `6ccb35b`, `6dcb70f`, `934dd91`,
  `7d8e797` and `1cbddb7` — so every `path:line`
  derived at `335f535`, `74e126f` or `35698f9` is
  byte-identical at `700c599`, and the older stamps are provenance facts rather than stale pins.
  Re-run at v1.48, not carried from an earlier revision's: the `74e126f 700c599` form is the one
  that
  matters now, because it is the only one that reaches the sha v1.48 is authored against, and it is
  still **empty** re-run at `af19d53` — a TWO-SHA closure is a dated fact and does not move when the
  freeze moves, which is the property this paragraph relies on.
  **The ONE-SIDED form is not empty any more, and v1.48 through v1.51 published it as though it
  were** (round sixteen; found by the plan's author against its own document, by neither leg on
  this one): `git diff --name-only 700c599 -- h-mad handoff` compares a sha against the **working
  tree**, so it moves with every commit touching those roots, and at `af19d53` it prints **2**
  files — `h-mad/scripts/h_mad_assemble_audit.py` and `h-mad/tests/test_h_mad_assemble_audit.py`,
  the assembler's oversize-prompt repair and its test. It printed **0** at `3f70eb3`, which is why
  three rounds of auditing read it as true. **The conclusion it carried is therefore WITHDRAWN**:
  the tree a 5d implementer reads is not byte-identical to `700c599` under `h-mad/` and `handoff/`.
  **What survives is narrower, and it is what this paragraph actually needs**: of the two files that
  moved, this document pins exactly one — `h-mad/scripts/h_mad_assemble_audit.py` at
  `_braces_outside_fences` — and that definition sits at the same offset at `dfae038`, `3f70eb3`
  and `af19d53` alike, every insertion the assembler took landing below it, while the test file is
  pinned nowhere here. So every `path:line` in this document still resolves on the tree a 5d
  implementer reads; what is retired is the stronger claim that the two trees are the same.
  **The rule, because this is a CLASS whose members have no detector**: a closure between two named
  shas is a dated fact and stays true, while a closure between a sha and the working tree is a
  reading that expires the moment anything under its roots is committed — it is re-run at every
  revision or it is not published at all. **A freeze that touches no document is not a freeze that
  touches no measurement**: `af19d53` left all four feature documents byte-identical and falsified
  this sentence anyway. The three sibling absence claims over these same two roots were re-run
  against it and all three hold at `3f70eb3` and at `af19d53` alike, at **0** each — the
  second-bounder symbol, the `_bodies` symbol, and the `*.sh` three-backtick sweep.
  Sibling `docs/` values are the ones that did move, and each of those is re-derived
  above at `700c599`, the sha v1.48 is authored against. A `docs/` pin has neither property — the
  sibling's own author may have renamed the sentence, and there is no symbol to grep for.
  **How a needle is chosen, and the hard condition on it** (added at v1.40; impl-plan audit v37).
  **This is NOT a member of the list above at all, and v1.40 wrote that it was** (impl-plan audit
  v38, which found the document then contradicting itself at three sites over the same ordinal).
  Stated as a content predicate rather than an ordinal, deliberately, because an ordinal here is
  what drifted at v1.40 and the list has since grown: **membership is decided by whether
  the sentence asserts what a sibling contains, never by position in the list**. The list above is the **prose-agreement** class — a
  sentence asserting what a sibling contains. What audit v37 found was a **form (a) locator
  breakage**: a needle that stopped returning exactly one hit. The foot of this bullet separates
  the two deliberately, because form (a) has a detector and prose agreement has none, so a single
  ordinal spanning both would count two different failures with two different remedies. **The size
  of the list above is written nowhere in the BODY of this document, here included** — the scope is
  the same one the ledger's own absence claim carries above, for the same reason and on the same
  measurement (body **0**, whole file **2** lines, all of them dated Version History entries) — it
  is `len(list)`, read
  by counting the enumerated members — because this sentence is where the drift lived: it restated
  the size beside a statement that had already made the same point, and a restatement is what goes
  stale while its source is repaired. What it uniquely carries is the membership test, and that is
  all it now carries: a sentence is a member if a sibling's author could pay it, ignore it, or have
  paid it already.
  The one-hit property is a property of **the whole sibling document**, not of the sentence being
  cited, so a sibling's author can break a needle without touching the row it points at.
  Measured: `grep -n 'both halves of'` on the design returned **one** hit at `335f535` and **two**
  at `74e126f`, because the design's round-four revision added an unrelated sentence using the
  same four English words — the needle drifted inside a **single commit**, on the same
  concurrent-authorship axis the rule already names for line pins.
  **Hard condition, and it is the one with a detector**: a locator is admissible only if it
  returns **exactly one hit at the commit the revision that writes it ships against**, re-run in
  that revision — not carried from the pass that first verified it, and not stamped at an older
  sha. `0` or `≥ 2` hits is what the next reader sees, which is the whole of the detection.
  **Selection preference, which has no detector**: choose a needle that is *lexically specific to
  its target row* — a backticked identifier, a verdict token, an anchored table-row prefix
  (`^| \`name\``), or a backticked **command** — never a bare English phrase, because a bare phrase
  is exactly as perishable as a line pin and perishes for the same reason. The fourth category was
  added at v1.43 (impl-plan audit v40): `git rev-parse --show-toplevel` was already counted among
  the 7 that satisfy the preference and is none of the first three. The needle is not the defect —
  it is lexically specific and returns exactly one hit in its target sibling — the **enumeration**
  was one category short of the set it was describing.
  **This preference is stated as a preference, not a hard rule, and the reason is measured**: at
  `cf3a862` this document carried **13** distinct `docs/`-sibling locators (7 + 6) and after v1.43
  **7** satisfied the preference; **on the tree v1.54 ships the population is 14 and the split is
  9 + 5**, the eighth being v1.50's own addition, v1.51 through v1.53 having added none, and the
  ninth being v1.54's replacement of a bare phrase that drifted (below) — a substitution inside the
  population, so the total is unmoved.
  **This site is a member of the stamp-carry class the marker screen sweeps, and it carried the
  v1.50 stamp through v1.51, v1.52 and into v1.53** (impl-plan audit v47 must 2, whose rule
  is what surfaced it — the hand-written list of four never named it). Re-run rather than
  re-stamped: all **14** needles were run again at `cac6edc` against the three siblings read out of
  that commit, one needle per invocation, and the split is still **10 design / 2 plan / 2 spec**
  with the same **two** second-target caveats and no others (`git rev-parse --show-toplevel`, whose
  target is the spec at one hit, also reads 4 in the plan; and the `sys.path.insert` needle, whose
  target is the design at one hit, also reads 1 in the plan). **ONE needle failed the hard condition
  at this freeze and it is repaired rather than reported**: the bare phrase `guard it removes` read
  **1** at `fbc2ea0` and **2** at `cac6edc`, so it is replaced by the anchored table-row prefix
  ``^| mutation | guard it removes (mechanism) | killed by``, which reads exactly **1** at both shas
  — moving that member from the bare-phrase list to the preference-satisfying one and taking the
  split from **8 + 6** to **9 + 5** at the same total of **14**. Every other needle returns exactly
  one hit in its stated target. **This is the second time a bare-phrase needle has drifted inside a
  single commit and the first time this document's own re-run caught it before an auditor did**,
  which is what the hard condition is for. The two lists below are v1.50's, with that one
  substitution. The
  **9** satisfying the preference (`` `_titled_section` anchors on a substring ``,
  ``^| `DOCBLOCK: BAD_INFO key=``, ``^| `DOCBLOCK: SUBST_OVERLAP keys=``,
  ``both halves of `overlap:` ``, ``^| `registry-row-removed` ``,
  ``^| `detail-line-undocumented` ``, `git rev-parse --show-toplevel`, and
  ``sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))``, which is the one
  that needs `grep -F`, and
  ``^| mutation | guard it removes (mechanism) | killed by``) while **5** are bare
  phrases (`the mechanism column is what the anchor must express`,
  `The sweep excludes build output`, `Heading selector differential`,
  `One node per glob-parametrised test`, `Bounds: 1200 s`). Those **five** are **retained**, because
  their target rows carry no backticked identifier to anchor on and a needle invented for the
  preference's sake would point at a row the sibling's author never wrote that way. A rule this
  document violates **five** times at the commit it ships is a rule that gets ignored, so the
  detectable half is the rule and the undetectable half is the guidance. **That cardinal was six
  through the first half of v1.54 and it is re-derived from the list above rather than decremented**:
  the member that left is the bare phrase `guard it removes`, which the hard condition failed at
  `cac6edc` — one hit at `fbc2ea0`, two at `cac6edc`, the design's own r18 revision having added an
  `awk` line that quotes the table header — so it was replaced by an anchored table-row prefix and
  moved into the preference-satisfying list, taking that split from 8 + 6 to 9 + 5 at an unchanged
  total of 14. **It left by being REPAIRED, not by being dropped**, which is why the total does not
  move and why the preference's status as guidance rather than rule is unchanged by it.
  **The residual, stated exactly**: the one-hit property is true only at the commit it was
  measured at, so it is re-established every revision or not at all.
  **Re-swept for v1.50 at `b3be433`, and the population is now FOURTEEN, not thirteen**
  (impl-plan audit v45): v1.50's
  repair of a stale prose line pin in the `h-mad/tests/docsections.py` delta block — named by its
  own header comment, which `grep -n '# h-mad/tests/docsection[s]\.py  (delta)'` reaches at exactly
  one hit, and NOT by a task ordinal, which is itself a location and moves — replaces it with a locator on the
  design's `sys.path.insert` line, which is a locator like any other and is enumerated rather than
  left uncounted. **Every one of the 14 re-run at v1.50 rather than carried from an earlier sweep
  or from any report: all 14 return exactly one hit in their stated target**, and
  the split is **10 design / 2 plan / 2 spec = 14**, with **two** caveats where a bare 14/14 shows
  none — the pre-existing one (`git rev-parse --show-toplevel`, the spec locator, also returns one
  hit in the plan) and the new one (the `sys.path.insert` needle, the design locator, also returns
  one hit in the plan, at the sentence where the plan names the same idiom), so both hold only
  under their stated target file; all 14 were run against all three siblings to establish that
  those two are the only ones. **The new locator carries a second condition the other thirteen do
  not**: its needle contains a bracket, so it must be run with `grep -F` — as a BRE the bracket is
  a character class and the search returns **0** on text that is present, which is decision M in
  one line. It satisfies the backticked-identifier preference, taking that split from 7 + 6 to
  **8 + 6**. Each needle was run against the sibling **as of
  that commit** — `git show b3be433:<sibling> | grep -c -- '<needle>'`, and `grep -Fc` for the one
  bracketed needle — and not against the working
  tree, because the three sibling authors are revising those files concurrently while v1.50
  is written, so a working-tree read would measure a document no commit contains. This was
  a real re-measurement and not a formality: **two of the three sibling documents were revised**
  between the sha this sweep was last run at and the one it is run at now —
  `git diff --name-only 700c599 b3be433 -- docs/01-plan/features/doc-block-exec.plan.md
  docs/01-plan/features/doc-block-exec.spec.md
  docs/02-design/features/doc-block-exec.design.md` names the **plan** and the **design** and does
  not name the spec, and no sibling **version
  number** is written here because the Conventions rule above reserves those for the header.
  Each needle's **target** was read out of that same commit, and the sweep records where each hit
  landed rather than only that it was one: **10** target the design, **2** the plan, **2** the spec,
  and 10 + 2 + 2 = 14. The two caveats the split makes visible and a bare 14/14 does not:
  `git rev-parse --show-toplevel` — the spec locator — also returns one hit in the **plan**, an
  unrelated occurrence of the same command; and the `sys.path.insert` needle — the design locator
  v1.50 adds — also returns one hit in the **plan**, which names the same idiom in prose. Their
  one-hit property therefore holds only under their stated target file, which is how the rule
  reads it, and both are recorded here so the next sweep
  does not read a second occurrence as a break.
  **The count moved 13 → 14 at v1.50 and the preference split 7 + 6 → 8 + 6; every earlier
  reading in the chain below is a 13 and is left as the 13 it was.** Before that, the count was
  unchanged at 13 and the 7/6 preference split with it: v1.43 added no locator —
  its two repairs are a prose-ordinal removal and a control moved onto a fixture file, neither of
  which reaches a sibling.
  v1.42's sweep at `6f0ee85` found the same 13 at one hit each.
  v1.41's sweep at `35698f9` found the same 13 at one hit each.
  v1.40's sweep at `74e126f` found the same 13 at one hit each,
  after ``both halves of `overlap:` `` replaced the one that had returned two — four consecutive
  revisions at 13/13, each re-run rather than inherited. **That is a chain of four and not a census
  of every sweep since**: it covers v1.40 through v1.43 and nothing later, and the sweep the
  document currently stands on is the one stamped at the head of this paragraph, not the last
  entry of this list. A reader who takes the chain for the whole history drops every sweep after
  v1.43.
  **What the rule does NOT cover, so the sweep is not read as forbidding it**: a bare
  **provenance** citation of the form "(design v1.85)" or "(plan audit v67)", naming the version
  or the cycle at which a decision was *made*, is a dated historical fact about a version history
  — it never expires and this document carries ~40 of them deliberately. What expires, and what
  the rule forbids, is a claim in the **present tense** about what a sibling now contains — a
  `design.md` line pin followed by "renders the detail line as …", "the spec's comment still
  reads …", "nothing is owed to the plan". **The rule covers the MODAL form too, and this is a
  widening** (impl-plan audit v36): "the spec **must** carry X" is a debt in modal dress and
  expires exactly as fast as "the spec carries X". Member (4) of the list above is the case that
  shows why. It is the 5f note's **debt**, as distinct from member (3), its clearance. It *was* a
  debt, not a description, so a rule scoped to the present tense would have let its own worst
  instance through. A sentence is inside the rule if a sibling's author could pay it, ignore
  it, or have paid it already. The header's three version pins are the one further exception, and only because they
  name the commit they were derived at, carry the command that re-derives them, and declare their
  own staleness as expected.
  **Residual, stated exactly**: only form (a) has a detector, and a weak one — a locator that has
  gone stale returns 0 or ≥2 hits, which the next reader sees the moment they run it. Prose
  agreement ("the spec says X", "nothing is owed") has **no** detector anywhere in this
  repository: no test and no precheck reads a sibling's content against this document's
  assertions about it, so **another stale prose claim** is prevented by the sentence not being
  written, not by anything catching it — a content predicate, deliberately not an ordinal, because
  an ordinal here is what drifted at v1.40. The one mechanical aid is a pre-dispatch sweep the reviser runs —
  `grep -n 'owed\|spec\.md:\|design\.md:\|plan\.md:\|line [0-9]' docs/01-plan/features/doc-block-exec.impl-plan.md`,
  read outside the Version History (which is a dated record and keeps its pins), noting that
  `owed` also matches `followed`.
  **The fifth needle is v1.50's, and it exists because the four original ones provably missed a
  live member** (impl-plan audit v45): a sibling location written as PROSE — the word for a source
  line and then an integer — rather than as filename-colon-number is invisible to all four, to the
  `.py:` shape screens and to both `SKILL` screens alike, and one such pin sat in this document,
  stale against the design's shipping bytes, until it was read out by hand. **The needle is
  deliberately SINGULAR**, because the plural spelling is a substring of `declines N` and of
  `underlines N` and would return those as confounds; and it is written as a regex **character
  class**, so the published sweep line cannot match itself — the device member (x) uses, applied
  here. **What the widening is worth is prospective, and that is stated rather than dressed up**:
  with the live member repaired, the fifth needle adds **0** hits to this body, so it buys the
  *next* such pin being triaged rather than this one being found. **Residual, as a concrete
  category, and r15 gave it a live member**: a sibling location in a further synonym — *at line N
  of*, *the Nth line* — matches neither the fifth needle nor any other instrument here.
  **A sibling location written as a SECTION REFERENCE — `§Name` — is the SAME class**, and unlike
  the two synonyms above it had a member alive in this document: a section name is a location, it
  expires exactly as a line number does, it is invisible to all five needles, and one of them was
  false at the revision it cited AND on the shipping tree (delta self-review r15; the site and its
  re-derivation are in the `h-mad/tests/docsections.py` delta block, reached by `grep -Fn` on that
  block's own header comment at one hit). **That parenthesis said *Task 3's delta block* from v1.50
  until v1.52 and the ordinal was FALSE, which is this very class committed inside the sentence
  that states the rule** (impl-plan audit v46, second leg, must 3): the block sits inside **Task 1**
  at every sha this document names, measured by comparing the block header's offset against the
  `## Task N` offsets in the same blob — `1cbddb7`, `700c599`, `b3be433`, `00b961f`, `dfae038`,
  `3f70eb3` and `af19d53`, seven for seven — so it was wrong when it was written and is not drift.
  **A task ordinal is a location and expires exactly as a section name and a source-line integer
  do**, which is why the rule below is now stated over internal references as well as sibling ones:
  the route to a block inside this document is the block's own header needle, never its task
  ordinal. **The reported ground for that finding does NOT reproduce and is recorded rather than
  smoothed**: the second leg wrote that `grep -n '§'` over Task 3's span returns nothing, and it
  returns **three** — two `§Execution` provenance citations and one `§Implementation Order` — so
  the finding's conclusion holds on a premise of its own that is false, and the conclusion was
  re-derived here rather than taken from it. **The rule over the class**: a sibling `§`-reference is admissible
  only where the content it cites is re-derived inside that section at a stated commit, or where
  it is demoted to the bare version-pinned provenance form the Conventions bullet above blesses.
  It is never this document's route to a sibling's content, because the route is always a needle.
  **Applied over the population rather than at the instance**: the members are found by reading
  the body outside the Version History for the `§` character and keeping the *sibling* references
  — the CommonMark `§4.2` citations and this document's own `§Verification` are not members, and
  neither are the two section names v1.52 writes into the paragraph above while REPORTING what a
  task span holds, which are a census description and not a route to a sibling's content; that
  exclusion is stated because a sentence about this class necessarily becomes a hit in the sweep
  for it, which is the needle-inside-scope exposure the Conventions enumeration already names — and
  at `dfae038` every one of them was re-derived by locating the content it cites inside the named
  section's line span in the shipping sibling. Exactly one failed, the one that delta block
  carried; the
  others hold. **That derivation is deliberately stated as a READING and not built as a screen**:
  a grep for `§` naming this document as its scope would be an eleventh instrument in the exposure
  enumeration above, whose cardinal and whose six-bin partition are two of the figures this
  document has already broken twice, and the class this rule closes is a prose class with no
  detector anywhere in this repository — like the sibling-agreement class it sits beside, it is
  prevented by the sentence not being written. **No cardinal of that population is written here**
  either, for the reason Task 4's `_SCANNED` bullet gives: the next `§` a reviser adds moves it
  and nothing detects that. The class is therefore widened and reduced, never closed.
  **This sweep is itself exposed to the needle-inside-scope rule stated in Conventions, and it is
  member (vii) of the enumeration there** (impl-plan audit v44). **Four of its five needles are
  literal strings; how many of them the counted body actually holds is a MEASUREMENT and is taken
  per needle rather than asserted as a universal** (delta self-review r15). **On the tree v1.54
  ships**, re-run after v1.54's last edit landed rather than before it (decision K), over the
  body, by line: the debt word **30**, `spec\.md:` **1**, `design\.md:` **1**, `plan\.md:` **0** —
  and 30 + 1 + 1 + 0 is the **32** the whole sweep returns, so no line is reached by two needles.
  **These four were re-run AFTER the reopen's last body edit and not merely after the first DONE,
  and the first attempt got that wrong**: v1.54 re-ran them before its reopen, published 29 / 1 / 1
  / 0 = 31, and the reopen then added an eighth whole-word hit of its own by putting the
  round-seventeen matrix move into the past tense — so the site shipped two integers the composition
  bullet below already contradicted at 32. **The class, and the rule that closes it**: a screen whose
  needle matches the KIND of prose the revision is still writing is not re-run once per revision but
  LAST, after the final edit, and this document carries ten such self-counting instruments, so the
  enforcement is a per-instrument pass rather than a single re-count. **Residual, stated exactly**:
  nothing mechanical pairs an instrument with the edits that can move it; a reviser who re-runs nine
  of the ten ships the tenth stale, which is what happened here and is caught only by another
  reader or by re-running all ten.
  **The label on this reading was WRONG through v1.53 and the correction is the label, not the
  integers**: it read *on the tree v1.52 ships* in the same breath as *re-run after v1.53's last
  edit landed*, which is the two-trees-one-blob defect v1.52's own must (1) closed, recurring one
  revision later at the site that closed it. The four integers v1.53 published were right for
  v1.53's tree; only the tree they were attributed to was not, and both halves now name v1.54.
  **This reading stood stamped at `dfae038` from v1.51 until v1.52 and that sha was wrong. Nothing
  was miscounted — the four integers were right and the STAMP was not** (impl-plan audit v46, both
  legs, independently): they were taken over v1.51's own post-edit body, and `dfae038` is the tree
  v1.50 ships, where the same four needles read **24** / **1** / **1** / **0** = **26**. So one
  paragraph published 25 and 26 for a single blob. Re-measured here one blob at a time, each in its
  own shell invocation, same corpus and same grammar with only the sha varying: `dfae038` **24** /
  **26**, `3f70eb3` **23** / **25**, `af19d53` **23** / **25**. **The rule that closes the class is
  the third clause of one the round-fifteen broadcast stated in two**, and it is written here
  because this document is where the missing clause had its member: an entry's own freeze-sha field
  takes the sha the batch is authored against; a reading of a committed blob keeps the sha it was
  taken at and does not move when the freeze moves; and **a reading taken over a revision's OWN
  post-edit body is stamped to the tree THAT revision ships and never to the freeze**, because the
  freeze does not contain the edits the reading counts, so a count of new text at a sha predating it
  is definitionally a different number. **The class is closed over the document and not at the
  site**: every reading here taken over its own body carries the third form as of v1.52, and the
  screen sites carrying the other half of the same error — a stamp naming a tree the reading
  was not taken on — are re-run and re-stamped with it, which is the enforcement condition the
  marker screen's rule gained in the same revision. **v1.52 named those sites as four and the
  membership was two short** (impl-plan audit v47 must 2); as of v1.53 the membership is not named
  at all but swept, by the command at the marker screen above, and the sweep's eight members and
  its non-members are published there rather than restated here.
  v1.48 through v1.50 said *every one of them present in the body it counts*, and the
  plan-filename form has never been present in that body at **any sha this document names**. That
  is a measured universal and not a rhetorical one: `git show <sha>:<this file> | awk … | grep -c`
  was run over every sha the stamp table below names and every further sha the Version History
  names, and **every one of them reads 0** — `6b4df35` alone admits no reading, because this
  document does not exist in that commit, and that is stated rather than scored as a zero. Its one
  whole-file hit sits inside the Version History, which this sweep is read outside of, so the form
  is absent under either reading. The classification below allots exactly **2** hits to the
  sibling-filename-plus-colon shape, which is the same reading reached from the other side, and
  three distinct forms cannot all be present behind two hits. **The three escaped spellings in
  this sentence contribute none of the hits**: an escaped `\.` is not the literal `.` the needle
  matches, which is the publication device the fifth needle uses one level down, applied here so
  that a per-needle reading can be published without moving itself. The fifth is the
  character-class form above and cannot match itself either. **This reading moves with every
  revision and is therefore stamped**: the sweep returns **23** body hits at `700c599`, **25** on
  the tree v1.49 ships, **26** on the tree v1.50 ships, **25** on the tree v1.51 ships, **25**
  on the tree v1.52 ships, **28** on the tree v1.53 ships and **32** on the tree v1.54 ships — so the
  round-thirteen audit's 23
  was **correct at the sha it read**, and what this document corrects is that audit's
  classification of the 23, not its count. **The fifth needle adds none of them**: the four-needle
  and five-needle forms both return 32 on this body, because the one prose pin the fifth needle
  was written for was repaired in the same revision that added it. **The composition of the 32 body
  hits on the tree v1.54 ships, re-derived by classifying every one of them MECHANICALLY rather than
  carried from the previous revision's split** (the classifier reads each hit line and asks, in
  order, whether it holds the debt word as a WHOLE word, then whether it holds it only as a
  substring, then whether it holds a sibling-filename-plus-colon needle; every hit falls in exactly
  one bin and none is left unclassified):
  **22** match only through a word that *contains* the debt word — `followed`, `allowed`,
  `narrowed` — so the confound this bullet already named is **wider than the one participle it
  names**, which is the correction; **8** write that word on its own, and **4** of those eight are
  this rule's own text (the two sentences quoting the forbidden phrasing, the sweep line above, and
  the confound note itself), leaving **4** live uses elsewhere in this document — one in the
  §Verification discharge paragraph, **two added by v1.54** in the residuals of two new acceptance
  criteria that each record a mutation row as a design-side debt, and **one added by v1.54's
  reopen** where the round-seventeen matrix move is put into the past tense; and **2** write a
  sibling-filename-plus-colon needle, both in prose recording that pins were withdrawn. So **6** of
  the 32 are the exposure, **4** are live uses, **22** are the substring confound, and **0** are the
  defect the sweep looks for. 22 + 8 + 2 = 32 and 4 + 4 = 8, so both partitions close. **One bin moved at v1.51 and only one, and it moved DOWN**: v1.50's
  residual sentence in the paragraph above ended on a participle carrying the debt word, and the
  r15 widening of that same residual rewrote the sentence without it, so the confound bin gave
  back the hit v1.50's own residual had added — the same hit, in the same sentence, entering at
  one revision and leaving at the next, while the exposure bin and the filename bin are unmoved.
  **The sweep and its split are re-derived at v1.53 rather than carried, and this time the total
  MOVED**: v1.53 writes many new sentences into this bullet, into the Conventions residuals above it
  and into all five tasks, so the sweep and its split are both figures its own edits could move; and
  re-run after the last edit landed (decision K) the total is **28**, up 3 from v1.52's 25, with the
  bins at **21 / 5 / 2** against v1.52's 18 / 5 / 2. **All three added hits are in the confound bin
  and none is the defect the sweep looks for**: v1.53's new prose carries three further participles
  containing the debt word, the third arriving in the THIRD reopen's own correction paragraph — which
  is the point of re-running this screen after the last edit rather than after the last big one. The exposure bin and the filename bin are unmoved, the live-use bin is
  unmoved at 1, and the split was re-derived by classifying all 27 hits rather than scaled from
  v1.51's. What that
  establishes is that v1.53's edits did not reopen the class, not that they closed anything.
  That is also why the classification is re-derived every revision rather than carried: a bin here
  moves on an edit made for an unrelated reason. **It publishes no
  reading**, so a corrupted count is not its failure mode; it is a triage aid read hit by hit, and
  what the exposure costs is 27 lines of triage for one real hit — which is worth stating, because
  the first pass at this sentence wrote "three are the exposure" from reading rather than from
  classifying, and under-counted by half exactly as the enumeration it was repairing had.

- **No body sentence in this document identifies the shipping revision by a RELATIVE phrase.**
  Every self-reference names its version number — `v1.44's base`, `re-swept at v1.41`, `executed
  at v1.45` — because a relative phrase is true when it is written and silently false one
  revision later, and nothing about the sentence changes when it goes stale. **The class**
  (impl-plan audit v44, which found **eight** members at `700c599`): a phrase meaning "the
  revision you are reading" carried across a revision boundary without re-labelling. The eight,
  and they sum to eight rather than to a rounder number because one bullet carried two of them:
  **three** sentences named an older base as the sha the shipping revision was authored against
  while three others named the right one; **two**, in a single AC bullet, attributed v1.41's
  toolchain sweep and the residual v1.41 added to the shipping revision; **one** attributed
  v1.44's re-read of the mutation harness; **one** wrote "before" a revision that was in fact the
  revision that had added the arm;
  and — the member that cost the most — **one** sat on the INHERITED-UNVERIFIED register's **own
  discharge claim**, presenting v1.45's execution as the shipping revision's, which is exactly the
  sentence a reader must be able to trust, since it is the sentence asserting that a figure
  stopped being inherited. **The consequence is measurable, not stylistic**: the marker screen
  above published a before/after pair whose "before" was an older revision's base, at which the
  reading was already identical to the "after" — a decision-K contrast that could not move, which
  is the defect decision K exists to prevent, one level up.
  **The screen, and it is a gate rather than a triage grep, because after the relabel there are no
  legitimate body members left**:

  ```bash
  D=docs/01-plan/features/doc-block-exec.impl-plan.md
  awk '/^## Version History/{exit}{print NR": "$0}' "$D" | grep -cE 'thi[s] revision|freez[e] sha'
  ```

  It reads **0** on the body v1.53 ships, re-run after v1.53's last edit landed. **It read 4 on
  the body v1.52 shipped, and this site is where the class it screens for kept recurring**
  (impl-plan audit v47 must 1, filed by the teammate leg and independently by codex as a should):
  v1.52 reopened this document twice after its own DONE, and the reopens' own sentences put both
  needles back into the body — the per-needle sweep's stamping paragraph and the stamping-rule
  clause, four hits at once, published beside a hard **0**. Run verbatim at `09e9307` the screen
  returns 4 and at `b3be433`, `00b961f`, `dfae038`, `3f70eb3` and `af19d53` it returns 0, so the
  four hits are v1.52's own text and nothing older. All four are relabelled at v1.53 — three to
  name the shipping revision by number, and the fourth, which states the stamping RULE and must
  stay general, rewritten to say *a revision's own post-edit body* and *the tree THAT revision
  ships*. **The stamp is the shipping revision's and was re-derived, not carried**: this site
  carried `the body v1.50 ships` through v1.51 and v1.52 while both shipped body edits, which is
  the stamp-carry class the marker screen above now sweeps for rather than lists. **The needles are
  written as regex character classes on purpose** — a literal spelling would put both of them into
  the scope this screen counts and the target could never be 0, which is the needle-inside-scope
  rule above applied rather than restated. That makes this screen **member (x)** of the exposure
  enumeration, and the only member whose disposition is that the exposure is closed by
  construction rather than by care. The Version History is deliberately outside the scope: its
  entries are dated records in which a relative self-reference means the revision that entry is
  about, which is not the defect and is not rewritten. (That sentence originally quoted the phrase
  it is about, which put a live needle into the counted scope and drove this screen to **1** in the
  same paragraph that publishes **0** — the rule above biting its own statement, caught by running
  the screen after the edit rather than before it. It is described here, not typed.)
  **Residual, as a concrete category**: the two needles are the two forms that were found live,
  and the screen sees no others. Relative *time* words — "today", "currently", "concurrently",
  "one round later" — are a different axis: they describe the **tree** rather than the revision,
  and they are covered by the tree-stamp closure above, not by this screen. A future relative
  self-reference in some third wording ("the present pass", "this batch") would read 0 here and be
  caught only by a reviser reading, exactly as the sibling-prose class is.

---

## Task 1: scanner, selection, info-string grammar, and the bounder's second consumer

**Production file**: `h-mad/scripts/h_mad_doc_block_exec.py` (new) and `h-mad/tests/docsections.py` (modified)
**Test file**: `h-mad/tests/test_h_mad_doc_block_exec.py` (new; includes the five docsections-side tests `test_docsections_has_no_second_bounder`, `test_docsections_unbalanced_four_backtick_fence`, `test_titled_section_ignores_a_heading_inside_a_fence`, `test_docsections_imports_when_collected_alone`, `test_docsections_imports_from_an_unrelated_cwd`) and `h-mad/tests/test_docsections.py` (gains exactly one test: the WIRE-PIN)
**Mutation spec**: `h-mad/tests/mutation-specs/doc_block_exec.json` (new) and `h-mad/tests/mutation-specs/docsections.json` (modified)
**Task shape**: `wiring`
**WIRE**: `h-mad/tests/docsections.py:titled_section` → `_dbe.find_heading(text, heading)` AND `_dbe.fence_aware_end(text, start, level)`; `h-mad/tests/docsections.py:section_from` → `_dbe.fence_aware_end(text, offset, level)` (imported as `import h_mad_doc_block_exec as _dbe`; `titled_section` passes the `(start, level)` `find_heading` returned, `section_from` passes its own `offset`)
**WIRE-PIN**: `h-mad/tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`

**Description — new behaviour**: Create the module with its **complete** exception hierarchy —
`DocBlockError` and its 19 subclasses (20 exception classes) with their constructors, listed in the code structure, so
`__all__` is complete and `from h_mad_doc_block_exec import *` works at Task 1 GREEN; Tasks 2–4
only reference them — the frozen `Block`
dataclass (`RunResult` is Task 3's, beside `run_block`, per the design's Implementation Order), the private fence scanner `_fence_events`, the public bounder `fence_aware_end`, the public
heading lookup `find_heading`, the pure scan `extract`, and the ordinal policy `select`. `extract` reads a **path** as strict UTF-8
(a `str` is converted with `Path`; `OSError` and `UnicodeDecodeError` both become
`DocUnreadable`), locates the heading through the public
`find_heading(text: str, heading: str) -> tuple[int, int] | None` — the offset just past the
heading line (the heading event's `end`) and its level; `None` when absent; `AmbiguousHeading(n)`
when more than one matches; found **among the scanner's `heading` events only**, so a line inside
any fence is never a heading match and a fenced example quoting the requested heading cannot become
the section start (design v1.61 §Scanning). **`heading` has two accepted forms, and each real caller
uses one**: the **full line form** `## Text` — matches a heading event whose **normalized text**
equals `Text` AND whose level equals the hash count; this is what `extract`, the CLI `--heading`,
and Task 5's `_gate_block` pass — and the **bare
form** `Text` — matches the same normalized text at any level; this is `docsections.titled_section`'s unchanged
contract. **The two forms are told apart by the request itself, full form first** (design v1.84,
impl-plan audit v26): a request that parses as an ATX heading line — 0–3 leading spaces, a run of
1–6 `#`, then **a space, a tab or end of line** — **IS** the full form, always; only a request
that does not parse as one is read as the bare form. **The predicate is literally the scanner's**,
the same one `_fence_events` applies to a document line, called rather than restated, so there is
one ATX rule in the module and the dispatch cannot drift from the recognition (design v1.85,
impl-plan audit v27). The tab and end-of-line arms are not decoration: `##\tText` and a title-less
`##` are both headings the scanner accepts, so a space-only request predicate would scan them as
headings and then refuse to address them, leaving valid sections unreachable in full form. There is exactly **one consequence worth
documenting**: a heading whose visible title itself begins with an ATX prefix — `### ## Text`,
whose title is `## Text` — is reachable only through its full form (`### ## Text`, level 3) and
never through the bare form, because the request `## Text` is claimed by the full form first. That
exclusion is harmless to every live caller, measured: none of `titled_section`'s targets begins
with `#`. Without the precedence the request `## Text` would have two incompatible meanings at
once — level-2 `Text`, and any-level `## Text` — and a document holding both would refuse as
ambiguous rather than answer either. **Normalized text** is the CommonMark §4.2 form and is what both sides of every
comparison use: the line after the opening hash run, with the optional closing hash run — preceded
by **a space or a tab** — and trailing whitespace stripped.
*Both* `#`-run delimiters in ATX take spaces-or-tabs; that is the same axis the opening delimiter's
`request-predicate-space-only` closes, and the closing run was the one member left at space-only.
Oracle: on markdown-it-py 2.2.0, CommonMark preset, `'## Text\t##\n'` renders `<h2>Text</h2>`.
The comparison is never against the raw source line,
so `## Text ##` and `## Text` are one and the same heading on **both** forms, and a document
holding both has **two** of it — `AmbiguousHeading(2)`, not one match (design v1.67 §Scanning,
design audit v63; the design's earlier "exact match" wording contradicted this and was withdrawn). `extract` maps `None` to an empty candidate list and never raises on absence — bounds the section at the next
`heading` event of the same or shallower level, and
returns every **tagged** fence between those offsets — an event with `candidate` true (a backtick
opener whose first info word is `bash`; `extract` never reads `marker`) whose info string carries the
tag — possibly an empty list,
never raising on candidate count. **A heading is recognised by the CommonMark ATX rule (§4.2) and
nothing looser**: 0–3 leading spaces, a run of 1–6 `#`, then a space, a tab or end of line; an
optional closing `#` run preceded by **a space or a tab** is stripped before the text is compared; so `#hashtag`,
a seven-`#` run and a four-space-indented `## x` are prose; the level is the run length of the
opening hashes. **The leading indent is 0–3 SPACES, literally, and a tab in it is never a
heading** — CommonMark measures indentation in **columns** with a tab advancing to the next
4-column stop, so a tab anywhere in the leading whitespace of a `##` line reaches column 4 and the
line is indented code. Oracle, same version and preset as the closing-run one above
(markdown-it-py 2.2.0, CommonMark): `'\t## x\n'`, `' \t## x\n'`, `'  \t## x\n'` and
`'   \t## x\n'` all render as an **indented code block** carrying the literal text `## x`, while
`'   ## x\n'` renders as a level-2 heading whose text is `x`.
**A literal implementation of the space-only predicate above is therefore already correct** — the
character after the 0–3 spaces is a tab, not a `#`, so it rejects every tab case for the right
answer by a different route — and this is a **latent** divergence, not a live contradiction, which
is why nothing about the grammar changes here and no mutation row is added (the matrix total is
**86** at this batch and this axis contributes none of it; a row on THIS axis, if the design wants
one, is still the design's to add — the one row the design added in its r18 revision,
`intersect-scan-non-overlapping`, is on the substitution SCAN axis and not on this one). What is added is the
fixture that stops a 5d implementer from "simplifying" the predicate to `line.lstrip()` before
matching the hash run, which would land a heading where CommonMark has a code block with every
gate still green: `test_heading_lookalikes_are_not_headings` carries `\t## x` beside `    ## x`.
**Residual, stated exactly — and it is a measured corpus figure, not an absence claim**: the
**fence opener's** 0–3-space indent is the same axis and is likewise measured in columns —
oracle, same preset: `'\t```bash\n'` renders as indented code while `'   ```bash\n'` opens a
fence. **The two arms are NOT symmetric in the corpus. v1.40 said they were, and both halves of
that sentence were wrong in opposite directions** (impl-plan audit v38, re-measured independently
by the orchestrator). Measured at `35698f9` over the tracked corpus this document defines
(`git ls-files -- h-mad handoff`, `*.md`, `archive/` excluded — **30** files), by a
**fence-state-aware** scan that counts an opener only when no fence is already open:

- the **1–3-space arm is exercised 29 times, in 4 files** — `h-mad/SKILL.md`,
  `h-mad/agents/doc-auditor.md`, `h-mad/references/inline-protocols.md` and `handoff/SKILL.md`.
  `h-mad/SKILL.md` is the file Task 5's `_gate_block()` itself scans, through
  `dbe.extract(SKILL_MD, "## Second surface — the codex leg")`. So that arm is pinned by a fixture
  **and** by 29 live corpus instances. (The individual line numbers are deliberately not written
  here: they are `SKILL.md` pins, which the standing control
  `h-mad/tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins`
  forbids this document from carrying — for an **unwrapped** pin only, which is the residual stated
  at the other site that cites this control and measured with the folded `SKILL.md` screen in
  Conventions — and the command below reproduces them.)
- the **tab arm is 0, and it is pinned by nothing at all** — no AC in this document prescribed a
  tab-indented fence opener before v1.41, the revision that added this arm. So AC-1.6's
  `test_indented_literal_tag_is_not_a_candidate` gains `\t```bash hmad:exec` beside its four-space
  case. **No mutation row follows from THIS axis**: the matrix total is **86** at this batch and
  none of it comes from here, and a row on this axis, if the design wants one, is still the design's
  to add — the same disposition as the heading axis above, and unaffected by the design's r18
  addition, which is on the substitution scan axis.

````bash
python3.11 -c "
import re, subprocess, pathlib
b = chr(96)
fs = [f for f in subprocess.run(['git', 'ls-files', '--', 'h-mad', 'handoff'],
      capture_output=True, text=True).stdout.split()
      if f.endswith('.md') and '/archive/' not in f]
op = re.compile(r'^(?P<ind>[ ]{0,3})(?P<m>' + b + r'{3,}|~{3,})(?P<info>[^' + b + r']*)$')
tab = re.compile(r'^[ \t]*\t[ \t]*(' + b + r'{3,}|~{3,})')
sp = tb = neg = 0
spf = set()
for f in fs:
    fence = None
    for line in pathlib.Path(f).read_text(errors='replace').splitlines():
        if fence is None:
            m = op.match(line)
            if m:
                fence = (m.group('m')[0], len(m.group('m')))
                if 1 <= len(m.group('ind')) <= 3:
                    sp += 1
                    spf.add(f)
                continue
            if tab.match(line):
                tb += 1
        else:
            ch, n = fence
            if re.match(r'^[ ]{0,3}' + re.escape(ch) + r'{' + str(n) + r',}[ \t]*$', line):
                fence = None
                continue
            if re.match(r'^[ ]{1,3}(' + b + r'{3,}|~{3,})', line) or tab.match(line):
                neg += 1
print('files', len(fs), 'space-arm', sp, 'in', len(spf), 'files', 'tab-arm', tb, 'declined-inside-fence', neg)
print(sorted(spf))
"
````

It prints `files 30 space-arm 29 in 4 files tab-arm 0 declined-inside-fence 2` — run verbatim
under both `bash` and `zsh` at `35698f9`, stdlib only, no `grep -P`, and the three-backtick
literal is `chr(96)` for the same double-quoting reason the Conventions sweeps give.
**Both controls were run** (the rule decision A states). *Positive* — the scan prints the 29
openers, each with the file it sits in and where in that file it sits. *True negative* — it
**declines 2** indented marker runs that sit **inside** an already-open fence, in 1 file, which
are body text and not openers, and which a scan without the fence toggle would have counted.
**That `2` is not the control's usable reading**, and the split below is (impl-plan audit v45):
**it is a composite over a two-term disjunction, and it is published split, because a total over a
disjunction is not per-branch evidence** (impl-plan audit v41; decision O). The decline predicate in the block above
is a two-term `or`: a 1–3-space-indented marker run — the same `re.match` shape the space arm
uses, with `{1,3}` where the opener regex has `{0,3}` — **or** `tab.match(line)`. Two disjuncts,
reported as one
integer. Re-run at `4e4a00c` with the disjuncts counted separately, the published line reproducing
verbatim beside them: **space-disjunct 2, tab-disjunct 0**, both in one file,
`h-mad/references/inline-protocols.md`. So the true negative is evidence that the fence-state gate
declines **space**-indented runs inside a fence, and no evidence at all about tab-indented ones.
**The tab arm is blind on both sides of this scan** — 0 openers and 0 declines — which is the same
disposition the tab arm already carries above, now stated for the negative control as well as the
positive one. **Blind forms, stated rather than left as a bare
`0`**: an opener whose marker run is built by a template rather than written literally; a `.md`
file outside `git ls-files -- h-mad handoff`, the four sibling `docs/` documents among them; and
an unbalanced fence, which leaves the scan inside a fence for the rest of that file and so
*under*-counts the space arm rather than over-counting it.

The **heading** predicate — the subject of the paragraph this residual interrupts — is implemented **once**, in `_fence_events`, which reports such a
line (outside any fence) as a `heading` event carrying `level` and the compared text — both the
heading match in `extract` and the section boundary in `fence_aware_end` consume the scanner's
verdict rather than re-recognising headings, so the single-source rule holds for headings as it
does for fences. The scanner event model is the design v1.58's exactly: `_fence_events(text)` is a
generator yielding one event per line of **five kinds** — fence `open`, fence `close`, fence
`body`, ATX `heading` (with its `level`), or `prose` — together with the line's `start`/`end`
character offsets (populated by `_fence_events` from its own cursor, so CRLF and any line width are
exact; `find_heading` returns the heading event's `end`, `fence_aware_end` tests `event.start >= start`,
and neither consumer walks lines a second time), the opener's marker character, run length,
indentation and info string, and the scanner-derived `candidate` flag. Every rule below was
rendered through markdown-it-py — both 2.2.0 (interpreter-local) and 4.2.0 (a second virtualenv,
not a second script) — before it was written down, 14 of 14 agreeing on each (plan §Measurements,
"Scanner grammar corpus"). **The script that renders them is committed and is named by path rather
than by adjective**: `docs/03-analysis/probes/doc-block-exec/grammar_corpus.2026-09-03.cd979362.py`,
which needs `markdown_it` and therefore the pinned `/opt/anaconda3/bin/python3.11` and never a bare
`python3`: a backtick or tilde run of ≥ 3
preceded by 0–3 spaces opens; a backtick opener whose info string contains a backtick is not a
fence at all (inert prose); while open, only a line whose leading run is the same character, ≥
the opening length, preceded by 0–3 spaces, and followed by nothing but spaces/tabs closes; a
marker run at 4+ spaces inside a fence is body text; no line inside a fence is examined as a
heading or opener. `fence_aware_end(text, start, level)` feeds the scanner **complete lines from
the document start through the line containing `start`** (never `text[:start]`) and considers a
boundary at every line whose start offset is **≥ `start`** — the line beginning exactly at `start`
(the line adjacent to the heading `find_heading` returned) IS a candidate, while a line that began
before a mid-line `start` is not (design v1.60 §Scanning; a `>` predicate would skip an adjacent
same-level heading and hand its tagged block to the wrong address). `extract` de-indents each body line by up
to the opener's indentation (a line indented less loses only what it has) and validates the info
string **only on a tagged fence**: tokens after `bash` are whitespace-separated; `hmad:exec` is
the tag; `shell=strict` (default) / `shell=plain`; any other token, any other `shell=` value, or
a **duplicated** recognised token raises `BadInfoString(key)` with the offending/repeated token.
An untagged fence's info string is never inspected. `select(blocks, index=None)` validates
`index < 1` → `BadIndex(n)` **before any lookup**; then 0 candidates or index past the end →
`BlockNotFound`; > 1 with no index → `AmbiguousBlock(n)`; else the block.

**Description — the wire**: In the same task, delete the private `_fence_aware_end` from
`h-mad/tests/docsections.py` (today at `h-mad/tests/docsections.py:31` `_fence_aware_end`, a `startswith("```")` toggle) **and**
`titled_section`'s local heading regex — today `h-mad/tests/docsections.py:53`, inside
`titled_section` (`:45`),
`match = re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$", text)`, a second, looser
heading grammar that would pick the section start independently of the scanner — measured as
guard-narrowing evidence in plan §Measurements "Heading selector differential" (located with
`grep -n 'Heading selector differential' docs/01-plan/features/doc-block-exec.plan.md`, one hit, verified at `700c599`).
**The corpus is the tracked 25, not a filesystem glob, and the figures are given on both because
the difference is contamination rather than noise** (plan v1.86 / design v1.93; this document
carried "over 30 files (`archive/` excluded) the old regex and `find_heading` agree on 266 headings" through v1.35, a corpus and an agreement count that match
neither reading). Over the **tracked** corpus — `git ls-files -- h-mad handoff` filtered to `*.md`
with `archive/` excluded — the old regex and
`find_heading` agree on **263** headings, `new_only=0` (nothing the old guard refused is newly
accepted) and `old_only=76`, every one a `#` comment line inside fenced code the old regex read as
a heading. Over the filesystem glob — the extras being the gitignored
`.pytest_cache/README.md` artifacts — agreement is **268** with the same `old_only=76` and
`new_only=0`. **Those four integers are a dated measurement, not a constant, and they carry the
INHERITED-UNVERIFIED label at both of the sites that USE them — here in Task 1's wire
description, and in the §Verification (Phase 5f) paragraph** — this is the site a 5d implementer
reads them from, and the register rule says the label stands at every site that uses a member, not
only where the register is written (impl-plan audit v44). **v1.48 wrote `AC-6.4` into that list
and AC-6.4 uses none of the four** (impl-plan audit v45): AC-6.4's own register sentence names
`2748`, `2486` and `2675`, and neither differential appears anywhere in that bullet — so a reader
auditing the register rule went to AC-6.4, found the figures absent, and could not tell whether
the label had been dropped there or the site had never used them. The two sites named above are
the two the 5f note itself names, and the two agree. **The class, and the rule that closes it**: a
sentence of the form *this figure carries the label at X* is a PLACEMENT measurement under
decision G exactly as a count is, and is derived by grepping X for the figure, never by recalling
where the label was last added. **Residual, as a concrete category**: nothing mechanical pairs a
register member with the sites that use it — no screen here reads a cross-reference — so a site
added later that uses one of these four and omits the label is caught by a reviser grepping the
figure, not by an instrument. Not challenged is not the same as verified: no round has re-run `263/76/0` or
`268/76/0`. They were taken at
`1861157`, when the tracked corpus was **25 files** and the glob **30**. The differential itself
is the plan's measurement, re-derived there at `1861157`; this
document transcribes it and did not re-run it at that commit, so the four integers are left stamped
at the commit they were measured on. **The script is committed and this document names it by path rather
than by adjective**: `fbc2ea0` commits every distinct version under
`docs/03-analysis/probes/doc-block-exec/` — `heading_differential.2026-09-04.b66afa9c.py`, the
TRACKED/GLOB version whose shape this paragraph publishes; `heading_differential.2026-09-03.cd979362.py`,
glob-only; `grammar_corpus.2026-09-03.cd979362.py`; and `setext_census.2026-09-04.b66afa9c.py` — so
the differential IS re-derivable here, and the paragraph below re-derives it.

**What is invariant, and what a reader re-runs, is the shape of
the differential, not its size** — and the shape is **not** the zero this document published
through v1.52. Every one of `old_only` is a `#` line inside a fence, which holds; but
`new_only=0` — *the narrowed guard accepts nothing the old regex refused* — is **false**
(impl-plan audit v47 codex must 4, round seventeen's shared decision 3f). Re-derived at
`fbc2ea0` by running the committed 09-04 probe from the repository root with the pinned
interpreter, `/opt/anaconda3/bin/python3.11 docs/03-analysis/probes/doc-block-exec/heading_differential.2026-09-04.b66afa9c.py`:
**TRACKED `files=30 both=292 old_only=82 new_only=1`, `setext_headings=0`, `titleless=1`; GLOB
`files=35 both=297 old_only=82 new_only=1`.** So the invariant is replaced by explicit accounting:
**every `new_only` member is enumerated, and each one is a heading under CommonMark.** At `fbc2ea0`
there is exactly one member.

**At the round-eighteen freeze the set is EMPTY, and the accounting model is what survives that**
(round-eighteen sheet FACT 3). `b39d9dc` removed the specimen from `h-mad/SKILL.md` as a defect in
that file — an empty `h1` — on the round-seventeen handoff's explicit instruction, and pinned the
removal with `h-mad/tests/test_h_mad_agent_definitions.py::test_skill_has_no_bare_heading_stub`. The
same committed 09-04 probe, re-run from the repository root with the pinned interpreter at
`cac6edc`, prints **TRACKED `files=30 both=292 old_only=82 new_only=0`, `setext_headings=0`,
`titleless=0`; GLOB `files=35 both=297 old_only=82 new_only=0`** — the three output lines quoted from
the run, not retyped from the first. So the accounting sentence at the freeze reads `new_only=0`, and
the model is unchanged: it was written to hold any N, and 0 is a legitimate value of it. **The
accounting is NOT weakened back to the old invariant**: `new_only=0` is now a measured reading at one
commit rather than a claimed property of the two grammars, which is the whole difference the
round-seventeen repair introduced.

**The LOCATOR RULE survives the specimen and is stated as a rule** — a `new_only` member is located
by a NEEDLE and never by a line number, even when a probe's own output line names one — because a
path-qualified `SKILL.md` line pin is the class this document has reintroduced six times and the
standing control
`h-mad/tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins`
turns red on one. The rule is what a later reviser applies to the NEXT member; it does not depend on
there being one now.

**The specimen, in the past tense.** At `fbc2ea0` the one member WAS a bare `#` on a line of its own,
sitting immediately above the `## Reading a dispatch verdict` heading of `h-mad/SKILL.md`; it was
CommonMark's empty ATX heading (§4.2 admits a hash run with no content), which the ATX predicate
accepts and the space-required regex rejects. Applying the locator rule to it,
`grep -c '^#$' h-mad/SKILL.md` returned **1** at `fbc2ea0` and returns **0** at `cac6edc`, and
`grep -n '^#$' h-mad/SKILL.md` reached it at one hit at `fbc2ea0`. **The empty-ATX-heading case is
now exercised by a FIXTURE and never again by pointing at the live corpus** (hostile-fixture rule; a
corpus specimen is a measurement, not a test): `test_titleless_heading_is_a_new_only_member` in
`h-mad/tests/test_h_mad_doc_block_exec.py` writes `titleless.md` under `tmp_path` with the body
`before\n#\nafter\n` and asserts `titleless=1 new_only=1` on that file alone.

**Residual, in these words:** At `cac6edc` the `new_only` set is empty, so "each `new_only` member is
a heading under CommonMark" is vacuously true there; it was verified non-vacuously at `fbc2ea0`
(N=1, the `h-mad/SKILL.md` specimen removed by `b39d9dc`) and is exercised by
`test_titleless_heading_is_a_new_only_member`.
**It is not NEWLY false, and "false on the live tree" understated it** (round seventeen, the plan author's run; re-derived here rather than taken). The same committed probe, run from a detached worktree at each sha in turn with the probe copied in so the instrument is constant while the corpus varies, reads `new_only=` **0** at `1861157` and **1** at `a8e0372`, `35698f9`, `cf3a862`, `4e4a00c`, `74e126f` and `fbc2ea0` alike — seven readings, one worktree each. The `1861157` run also reproduces the transcribed `files=25 both=263 old_only=76 new_only=0` exactly, which is the first re-derivation of that quadruple this document has made rather than transcribed. So the invariant has been false at **every sha after `1861157` and up to `fbc2ea0`**, through every revision that restated it, and the freeze that surfaced it did not cause it. **The series does not end there and the end is a REMOVAL rather than a return**: the same probe reads `new_only=` **0** again at `cac6edc`, not because the two grammars stopped disagreeing but because `b39d9dc` deleted the one member — which is why the accounting above publishes 0 as a dated reading and keeps the enumeration model rather than restoring the invariant. **Which probe prints WHAT, because the two versions differ and citing the wrong one is how a reader fails to reproduce this**: the **09-03** probe, `docs/03-analysis/probes/doc-block-exec/heading_differential.2026-09-03.cd979362.py`, is glob-only and is the one that prints the `NEW-ONLY` line naming the member; the **09-04** probe prints the `--- TRACKED` / `--- GLOB` pair of quadruples and its `OLD-ONLY` lines and **no** `NEW-ONLY` line at all — verified by running both at `fbc2ea0`.
**So the differential is evidence in the direction it was always claimed to be, and the softening
is not a defect**: on this member the narrowed guard is right and the old regex was wrong, and
what the earlier `new_only=0` sentence asserted was a coincidence of the smaller `1861157` corpus
rather than a property of the two grammars. **v1.53 left the line in place deliberately and
`b39d9dc` then repaired it; the WHY of the deferral is kept because it is the standing rule, and the
WHAT is corrected because the tree moved.** The deferral's reason was that editing `h-mad/SKILL.md`
moves the freeze and expires the readings three sibling documents stamp against it — which is what
happened: `b39d9dc` removed the line while those documents still described it in the present tense,
and every one of them re-stamps here. **The lesson is recorded rather than the outcome regretted**: a
CORPUS specimen is a measurement and cannot be a test, because any commit may remove it; the case it
stood for is now held by a fixture (above), which no tooling commit can move. **Residual, stated as a category**:
this accounting is a reading at one commit over one corpus, so a `new_only` member added by a
later `h-mad/` or `handoff/` edit is caught by re-running the committed probe, not by anything
standing. **The corpus relation is
invariant too, and it is the part re-derived here.** The tracked set and the dot-excluded glob
set are the *same set* (symmetric difference empty), and the glob without the dot clause is
exactly that set plus the five `.pytest_cache/README.md` paths named in AC-6.1. Re-derived at
`335f535`: `git ls-files -- h-mad handoff | grep '\.md$' | grep -v '/archive/' | wc -l` → **30**,
the dot-excluded glob → **30**, symmetric difference **empty**, the glob without the dot clause →
**35**, and the five dropped are exactly the five AC-6.1 names. The corpus grew from 25 to 30
between `1861157` and `a8e0372` — this session's own `h-mad/agents/*.md` commits — which is
precisely why the *relation* is the check and the integers travel with a commit.
`titled_section(text: str, heading: str)`
now calls `found = _dbe.find_heading(text, heading)`, keeps its own loud failure
(`assert found, f"missing section {heading!r}"` — `test_a_missing_heading_fails_loudly` still
passes), unpacks `start, level = found`, and returns `text[start:_dbe.fence_aware_end(text, start, level)]`;
`section_from(text: str, offset: int, level: int = 2)` is unchanged except that it calls
`_dbe.fence_aware_end(text, offset, level)`. The import
must work when `test_docsections.py` is collected alone (nothing else puts `h-mad/scripts` on
`sys.path`; `tests/conftest.py` does not) and when `docsections` is imported from an unrelated cwd
with only the tests dir on `sys.path`, so `docsections.py` inserts the directory containing
`docsections.py` joined with `../scripts` into `sys.path` itself (resolved from `__file__`) before
the import. Re-point `docsections.json`: `fence-tracking-removed` and
`section-no-longer-owns-its-subsections` anchor in `scripts/h_mad_doc_block_exec.py` (the
scanner's state transition and the bounder's heading match); the other two anchors
(`offset-anchored-bound-runs-to-end-of-file`, `missing-heading-returns-empty-instead-of-failing`)
stay in `tests/docsections.py`; the spec gains `"target_command": ["python3.11", "-m", "pytest", "-q"]`
and **all eight** rows gain a `test` key (the full node ID, copied from `_killed_by`, which stays).
The spec's existing whole-file `command` — `["python3.11", "-m", "pytest", "tests/test_docsections.py", "-q"]`,
read from `h-mad/tests/mutation-specs/docsections.json` and re-read there at `cf3a862` — is **left exactly as it is**,
and deliberately (impl-plan audit v34): scoring runs `target_command + [test]`
(`h-mad/scripts/h_mad_mutation_harness.py:606-607`, in `run_spec`, `:482`), so `command` never
selects a killer, and **two** of the eight
killers — `docsections-syspath-setup-removed`'s
(`tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd`) and
`docsections-local-bounder-restored`'s
(`tests/test_h_mad_doc_block_exec.py::test_docsections_has_no_second_bounder`) — live in
`test_h_mad_doc_block_exec.py`, which `command` does not collect. **Two, counted against the
eight**, re-derived at `335f535`: the four shipped rows in
`h-mad/tests/mutation-specs/docsections.json` carry `_killed_by` values all under
`tests/test_docsections.py::` (`test_a_fenced_comment_does_not_end_the_section`,
`test_a_section_owns_its_subsections`, `test_section_from_bounds_an_offset_anchored_pin`,
`test_a_missing_heading_fails_loudly`), and of the four rows Task 1 adds,
`docsections-delegation-reverted` and `docsections-heading-lookup-reverted` are both killed by the
WIRE-PIN, which lives in `test_docsections.py`. An earlier draft said "three", counting
`docsections-syspath-setup-removed` and its own binding as two members — the row **is** that
binding, so the set was double-counted. The conclusion is unchanged at two; the number is fixed
because a 5d implementer who counts finds two and reads the gap as a missing row.
**`command` has FOUR consumers, not one**, every one of them inside `run_spec`
(`h-mad/scripts/h_mad_mutation_harness.py:482`); first read at `4e4a00c`, at v1.44, and re-read
at `700c599` for v1.48 — the stamp closure above covers the span, `h-mad/` being byte-identical
from `74e126f` to `700c599` and to the working tree — and
re-derivable with one command, `grep -n 'command' h-mad/scripts/h_mad_mutation_harness.py`:
`:562`, `if not _suite_is_green(command, root):` — the **pre-run baseline gate**, whose failure
ends the whole run with the verdict `BASELINE_NOT_GREEN`;
`:679`, `suite_green, suite_output = _run(command, root)` — the **survivor-branch diagnostic**,
which asks "what else noticed" after a row carrying a `test` key already survived;
`:694`, the same call on the **fall-back scoring path** — literally the `else` of
`if scoring_command is not None:` at `:657`, which for any spec `_load_spec` accepted means the row
carries no `test` key, because `:208-212` refuses a `test` key on a spec with no `target_command`; and
`:721`, `result["baseline_green_after"] = _suite_is_green(command, root)` — the **post-restore
read-back**, whose failure is `RESTORE_FAILED`. All four bare pins are lines of `run_spec`.
**Two of the four are moot for this spec and two are the real residual, and the decision is
re-stated on that ground rather than on "costs nothing".** `:694` becomes unreachable the moment
Task 1 lands, because Task 1 gives all eight rows a `test` key **and** the `target_command` that
`_load_spec` (`h-mad/scripts/h_mad_mutation_harness.py:177`) demands beside one — it raises
`SpecError` at `:212` otherwise — so every row takes the `scoring_command` branch. The
already-red-killer hazard is separately caught **per row**, before the mutant is applied, by the
pre-mutation check at `h-mad/scripts/h_mad_mutation_harness.py:630-642` (also `run_spec`), which
runs `scoring_command`, not `command`, and refuses the row with "named test … was already failing
… so a kill would measure nothing".
**What genuinely remains is `:562` and `:721`.** With `command` scoped to
`tests/test_docsections.py`, neither the baseline gate nor the post-restore read-back ever collects
`h-mad/tests/test_h_mad_doc_block_exec.py` — the file holding the two killers named above and the
file two of the eight rows are re-anchored into. That is accepted **deliberately, and stated rather
than denied**: this spec's baseline and restore verification are scoped to
`tests/test_docsections.py`, and what that leaves unverified is a pre-existing red, or a failed
restore, inside `test_h_mad_doc_block_exec.py`. What covers it is the other spec's own run —
`doc_block_exec.json`'s `command` is
`["python3.11", "-m", "pytest", "tests/test_h_mad_doc_block_exec.py", "-q"]` (Conventions above),
so its baseline gate and its restore read-back do collect that file, and the 5f order runs both
specs.
Continuing the re-anchoring:
the two anchors that stay in `tests/docsections.py` are re-spelled to the delegating lines they now
mutate — and **each row's `replace` is re-read against the migrated body in the same edit, never
only its `find`** (four leading spaces on every payload below, the function-body indentation the
landed source has):
`offset-anchored-bound-runs-to-end-of-file` finds `    return text[offset:_dbe.fence_aware_end(text, offset, level)]`
and **keeps** its existing `replace`, `    return text[offset:]`, which binds nothing and names
nothing the migration removed;
`missing-heading-returns-empty-instead-of-failing` finds `    assert found, f"missing section {heading!r}"`
and its `replace` **changes** from today's `    if not match: return ""` to
`    if not found: return ""`. Today's spelling is verified in
`h-mad/tests/mutation-specs/docsections.json`, and the migrated `titled_section` binds `found`,
`start` and `level` and no `match` at all (the delta below), so the unchanged payload would land a
`NameError` in every `titled_section` call. The row would still be scored a kill — the named test
goes red and the `ran_and_failed` guard at `h-mad/scripts/h_mad_mutation_harness.py:660` falls
through to the kill at `:670–671`, both inside `run_spec` (`:482`) — while measuring
nothing about the loud `assert` its `_mechanism` claims to prove. **This is the same class v1.11
already fixed once**, for `docsections-heading-lookup-reverted`, whose restored regex would have
raised `NameError` because the delta had dropped the `import re`: re-pointing a row's `find`
without re-reading its `replace` against the post-migration body.
Add a fifth row `docsections-delegation-reverted`, a **connection-only** revert: the callee is
untouched and no local bounder is restored. `find` is the one line
`import h_mad_doc_block_exec as _dbe  # noqa: E402` (it matches exactly once); `replace` is
```python
import importlib.util as _ilu  # noqa: E402
_spec = _ilu.spec_from_file_location("_h_mad_doc_block_exec_private", str(Path(__file__).resolve().parents[1] / "scripts" / "h_mad_doc_block_exec.py"))
_dbe = _ilu.module_from_spec(_spec); sys.modules[_spec.name] = _dbe; _spec.loader.exec_module(_dbe)
```
(`sys` and `Path` are already imported at the top of the delta, and the replacement reuses the delta's one path idiom) — the same file, loaded as a private
instance registered in `sys.modules` only under `_h_mad_doc_block_exec_private`, a name the import
system never resolves for `h_mad_doc_block_exec`. The registration is required, not cosmetic:
under `from __future__ import annotations` dataclass processing dereferences
`sys.modules[cls.__module__]` (`dataclasses._is_type`), so an unregistered instance of a module
with a frozen `@dataclass` raises `AttributeError: 'NoneType' object has no attribute '__dict__'`
at load — measured on 3.11.8 (impl-plan audit v11); registered under the private name it loads
and the WIRE-PIN still records `[]`. So
`titled_section` and `section_from` still do the real work through a second, byte-identical
bounder. Under it the WIRE-PIN fails because its recording fake sits in `sys.modules` and the
reload re-binds `_dbe` to the private instance, not the fake — neither recorder is ever called;
**every other test stays green**: the helper's own behaviour tests
(`extract`/`select`/`fence_aware_end`/`find_heading`), the two docsections-side hostile tests
(`test_docsections_unbalanced_four_backtick_fence`, `test_titled_section_ignores_a_heading_inside_a_fence`),
the source guard `test_docsections_has_no_second_bounder` (the source still defines no
`_fence_aware_end` and scans no marker run) and both import tests — `test_docsections_imports_when_collected_alone`
because it only collects `test_docsections.py` and never runs the red pin, and
`test_docsections_imports_from_an_unrelated_cwd` because it imports the module without pytest at
all. The row's `test` key is the WIRE-PIN. Measured
2026-09-03 on a two-module scratch pair with the scaffold below and a frozen-dataclass callee under
`from __future__ import annotations`: the shared-import caller records
`['find_heading', 'fence_aware_end']`, the file-path caller records `[]`, both return the same
section. Add a sixth row
`docsections-syspath-setup-removed`: `find` is the one line
`sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))` exactly as the delta
below writes it (the design's spelling, so the anchor and the landed source cannot drift apart), `replace` is the
comment `# sys.path setup removed`; killed by
`tests/test_h_mad_doc_block_exec.py::test_docsections_imports_from_an_unrelated_cwd` (the `import` then
fails with `ModuleNotFoundError` in the subprocess). Add a seventh row
`docsections-heading-lookup-reverted`: `find` is the `found = _dbe.find_heading(text, heading)` line,
`replace` restores the local regex on that one line, carrying its own import because the delta no longer imports `re` (`import re; match = re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$", text); found = (match.end(), len(match.group("marks"))) if match else None`),
`find_heading` untouched — killed by the WIRE-PIN, whose `find_heading` record then stays empty
(the harness's single `find`/`replace` per row fits: one line becomes one line). Add an eighth row
`docsections-local-bounder-restored`, the behaviour-restoring revert the source guard exists to
refuse, as one contiguous replacement. **Both payloads are literal here** (impl-plan audit v24):
the anchor is the Task 1 delta shown below, which this document already writes out verbatim, so
nothing has to be invented at 5e. `file` is `tests/docsections.py`. `find` is exactly:
```python
def titled_section(text: str, heading: str) -> str:
    """The named section's body, bounded by the next same-or-higher heading.

    `heading` is the text after the `#`s. The section OWNS its subsections: a
    bound that stopped at any heading would cut a `##` section short at its first
    `###` and every assertion about the later part would fail for the wrong
    reason.
    """
    found = _dbe.find_heading(text, heading)
    assert found, f"missing section {heading!r}"
    start, level = found
    return text[start:_dbe.fence_aware_end(text, start, level)]


def section_from(text: str, offset: int, level: int = 2) -> str:
    """From an arbitrary offset to the next heading at `level` or higher.

    For a pin anchored on a symbol rather than a heading — the case a byte window
    is usually reached for, because the anchor is mid-section and there is no
    title to name.
    """
    return text[offset:_dbe.fence_aware_end(text, offset, level)]
```
and `replace` is exactly (**a four-backtick fence, because the restored body contains the literal
```` ``` ```` of the old toggle — a three-backtick fence would close on it**):
````python
import re


def _fence_aware_end(text: str, start: int, level: int) -> int:
    off = start
    in_fence = False
    for line in text[start:].splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and re.match(rf"^#{{1,{level}}} ", line):
            return off
        off += len(line)
    return len(text)


def _find_heading(text: str, heading: str) -> tuple[int, int] | None:
    match = re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$", text)
    return (match.end(), len(match.group("marks"))) if match else None


def titled_section(text: str, heading: str) -> str:
    """The named section's body, bounded by the next same-or-higher heading.

    `heading` is the text after the `#`s. The section OWNS its subsections: a
    bound that stopped at any heading would cut a `##` section short at its first
    `###` and every assertion about the later part would fail for the wrong
    reason.
    """
    found = _find_heading(text, heading)
    assert found, f"missing section {heading!r}"
    start, level = found
    return text[start:_fence_aware_end(text, start, level)]


def section_from(text: str, offset: int, level: int = 2) -> str:
    """From an arbitrary offset to the next heading at `level` or higher.

    For a pin anchored on a symbol rather than a heading — the case a byte window
    is usually reached for, because the anchor is mid-section and there is no
    title to name.
    """
    return text[offset:_fence_aware_end(text, offset, level)]
````
**Provenance of the two restored bodies, stated exactly** (impl-plan audit v25). They are not
both lifted verbatim, and the difference matters for anyone reviewing the revert later.
`_fence_aware_end` **is** today's function: its body is `h-mad/tests/docsections.py:33-42`
(`_fence_aware_end`, `:31`) character for
character, the `startswith("```")` toggle included; only today's one-line docstring at `:32` is
omitted, which changes nothing the source guard asserts. `_find_heading` is **not** today's text —
today's file defines no such function (`grep -c "def _find_heading"` → 0). The heading lookup
lives inline inside `titled_section` at `:53`, so the revert **lifts that inline `re.search` into
a function** to give the two re-pointed call sites a name to call. It is behaviour-identical to
today's lookup — the same pattern, the same `match.end()` offset and the same
`len(match.group("marks"))` level — returning `None` where today's inline form falls through to
its `assert`. The docstrings on `titled_section` and `section_from` are carried through unchanged
so the `find` and the delta are one literal shape. The `import h_mad_doc_block_exec
as _dbe` line is above the `find` region and stays, which is what leaves the callee untouched. Its `test` key is
`tests/test_h_mad_doc_block_exec.py::test_docsections_has_no_second_bounder`, which goes red on
the restored `_fence_aware_end` definition; the WIRE-PIN and the two hostile tests also go red
under it, which is why this row cannot serve as the isolated-wire proof and the fifth row can
(design audit v58). The killer of the sixth row must live in a file that still
**collects** under the mutant: `test_docsections.py` imports `docsections` at module level, so
there the mutant is a collection error, which the harness scores as a refusal, not a kill
(`h-mad/scripts/h_mad_mutation_harness.py:660–669`, the collection-break refusal branch inside
`run_spec`, `:482`); `test_h_mad_doc_block_exec.py` imports only `dbe` and
never imports `docsections` at module level (it reads that file's source as text), so its named
test reaches its assertion; the eighth row's killer lives in the same file for the same reason.

**Code structure**:
```python
# h-mad/scripts/h_mad_doc_block_exec.py
from __future__ import annotations
import argparse, dataclasses, io, json, math, os, re, shutil, signal, stat, subprocess, sys, tempfile, unicodedata
# ^ complete for every module-level name used across the five tasks' module code: argparse (main),
#   dataclasses.replace (substitute), io (handle annotations), math.isfinite, os, re, shutil.rmtree,
#   signal.SIGKILL, stat.S_ISREG, subprocess.Popen/PIPE/TimeoutExpired, sys.exit, tempfile.mkdtemp,
#   json.dumps and unicodedata.category — the two halves of the _field renderer: json.dumps for
#   the quoting and most escaping, unicodedata.category for the Cc/Zl/Zp second pass that
#   json.dumps leaves behind (design v1.82). The test-file
#   deltas carry their own (`sys` and `pathlib.Path` in docsections.py; `importlib, sys, types` in the
#   test_docsections.py scaffold; the consumer already imports `re, shlex, sys, Path` at its :10–:13).
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Mapping, Sequence

# `__all__` names only what is DEFINED at each task's GREEN, so a star-import works at every
# task boundary: Task 1 lists Block, extract, select, fence_aware_end, find_heading and the 20
# exception classes — DocBlockError and its 19 subclasses — for 25 names, BadArgs included
# (5 + 20 = 25; the hierarchy is enumerated below). Task 2 appends "substitute"; Task 3 appends "RunResult",
# "run_block"; Task 4 appends "main" — 29 names when complete: the seven public functions
# (extract, select, substitute, run_block, main, fence_aware_end, find_heading — "all seven",
# design §API) + Block + RunResult + 20 exceptions (BadArgs included — design v1.86 confirms 29).
__all__ = [
    "Block", "extract", "select", "fence_aware_end", "find_heading",
    "DocBlockError", "DocUnreadable", "BadInfoString", "BlockNotFound", "AmbiguousBlock",
    "AmbiguousHeading", "BadIndex",
    "BadSubstArg", "MissingSubstitution", "OverlappingSubstitution",
    "BadTimeout", "BlockTimeout", "CleanupFailed", "LaunchFailed",
    "StreamPathUnwritable", "StreamPathsAlias", "PreambleUnreadable", "StreamWriteFailed",
    "StreamCloseFailed", "BadArgs",
]

DRAIN_SECONDS = 5.0            # Task 3 uses it; declared here so the constant has one home

# The complete hierarchy: DocBlockError + 19 subclasses (6 + 3 + 4 + 5 + 1), one addend per headed
# group below, every one defined HERE (Task 1).
class DocBlockError(Exception): ...
# raised by extract / select (Task 1)                                         — 6
class DocUnreadable(DocBlockError): ...
class BadInfoString(DocBlockError):
    def __init__(self, key: str): ...
class BlockNotFound(DocBlockError): ...
class AmbiguousBlock(DocBlockError):
    def __init__(self, n: int): ...
class AmbiguousHeading(DocBlockError):
    def __init__(self, n: int): ...
class BadIndex(DocBlockError):
    def __init__(self, n: object): ...
# raised by substitute (Task 2) and the CLI's --subst parsing (Task 4)         — 3
class BadSubstArg(DocBlockError):
    def __init__(self, raw: str, duplicate_key: str | None = None): ...
class MissingSubstitution(DocBlockError):
    def __init__(self, keys: list[str]): ...                 # insertion order preserved
class OverlappingSubstitution(DocBlockError):
    def __init__(self, pairs: list[tuple[str, str, str, int | None]]): ...
    # ONE representation, and it is the design's: a single tagged `pairs` list whose members are
    # `(kind, a, b, offset|None)` with `kind` in {"overlap", "intersect"}. There is NO second
    # `intersections` argument (round-eighteen sheet FACT 4 a / C2 iii — the split this document
    # carried was one of three representations across the two documents).
    # `offset` is None on an "overlap" member and the smallest index the two spans SHARE on an
    # "intersect" member. Sorted; substring members keep their (shorter, longer) order.
# raised by run_block (Task 3)                                                 — 4
class BadTimeout(DocBlockError):
    def __init__(self, value: object): ...
class BlockTimeout(DocBlockError):
    def __init__(self, seconds: float): ...
class CleanupFailed(DocBlockError):
    def __init__(self, path: str, cleanup_error: OSError | None): ...
class LaunchFailed(DocBlockError):
    def __init__(self, stage: str, err: OSError | subprocess.TimeoutExpired | ValueError,
                 pgid: int | None = None): ...
    # attributes: .stage, .err, .pgid — all three are read by tests and by main's renderer.
    # `err` is a union because the bounded post-kill wait's expiry is carried here too
    # (design v1.73): subprocess.TimeoutExpired is a SubprocessError, NOT an OSError, so the
    # annotation must name both. It names a THIRD type for the same reason: Task 3 passes the
    # ValueError that Popen raises when an embedded NUL reaches the spawn, and a ValueError is
    # neither an OSError nor a SubprocessError, so an annotation of two would exclude an argument
    # this document's own task hands it (round-eighteen sheet FACT 4 d; codex impl-plan must 2 at
    # v48). Written as the exact three-member union rather than BaseException, which
    # would also admit KeyboardInterrupt. main renders the `os_error:` line with str(err),
    # which is correct for either type.
    # stage in {"mkdtemp", "spawn", "reap", "collect"}; pgid is set on the "reap" and "collect"
    # stages and stays None on "mkdtemp"/"spawn" (design v1.65 exception table + verdict table)
# raised by main's stream and preamble handling (Task 4)                       — 5
class StreamPathUnwritable(DocBlockError):
    def __init__(self, leftover: str | None = None): ...
    # **This document's own constraint**, in the Conventions rule's form (b) — it is NOT a report of
    # what the design now contains. The agreement was reached at design v1.71 / impl-plan audit v16,
    # which is provenance, a dated historical fact about a version history, and says nothing about
    # the present. The signature is
    # StreamPathUnwritable(leftover=None) — there is no `err` positional, and no raise site in this
    # document passes one. The default exists for its RAISE SITE, not for any test: the
    # reservation region raises it bare, `from` the OSError, and the bounded-retry exhaustion
    # raises it bare with no cause. AC-4.2's subclass walk instantiates nothing (design v1.80),
    # so no other subclass has to be zero-argument constructible. `.leftover` is the path a failed reservation rollback left
    # behind (AC-3.10 read-back); None on every other raise site, and main emits the `leftover:`
    # detail line only when it is set. The OSError travels as __cause__, not as a field: the
    # reservation raises `StreamPathUnwritable(leftover) from err`, while bounded-retry exhaustion is
    # raised with no cause.
class StreamPathsAlias(DocBlockError): ...
class PreambleUnreadable(DocBlockError): ...
class StreamWriteFailed(DocBlockError):
    def __init__(self, written: list[str], failed: str, skipped: list[str], verify: str | None = None): ...
class StreamCloseFailed(DocBlockError):
    def __init__(self, stream: str, close_error: OSError): ...
# raised by main's argument parsing (Task 4)                                    — 1
class BadArgs(DocBlockError):
    def __init__(self, message: str): ...
    # the parser's own error text, carried verbatim and rendered quoted as
    # `BAD_ARGS message="<m>"`, exit 0 (design v1.85)

@dataclass(frozen=True)
class Block:
    text: str        # de-indented fence body, no trailing-newline normalisation
    shell: str       # "strict" | "plain"
    lineno: int      # 1-based line of the opening fence
    info: str        # raw info string after the language word

@dataclass(frozen=True)
class _FenceEvent:
    lineno: int; kind: str            # "open" | "close" | "body" | "prose" | "heading"
    marker: str | None; run: int; indent: int; info: str
    start: int; end: int              # character offsets of the line [start, end) incl. its newline —
                                      # the scanner's own cursor, CRLF-safe; find_heading returns a
                                      # heading event's `end`, fence_aware_end tests `event.start >= start`
    level: int                        # heading events only (1–6, the opening-run length); 0 otherwise
    text: str                         # heading events only: the compared text (closing-run stripped)
    candidate: bool                   # scanner-derived: True only for a BACKTICK opener whose first
                                      # info word is "bash" — extract never inspects `marker` itself

def _fence_events(text: str) -> Iterator[_FenceEvent]:
    """The ONLY function that inspects marker runs. Yields one event per line."""

def fence_aware_end(text: str, start: int, level: int) -> int:
    """`event.start` of the next `heading` event at `level` or shallower with
    `event.start >= start` (the line adjacent to a heading is included;
    a line that began before a mid-line `start` is not); fence state built over
    complete lines through the line containing `start`; heading recognition is
    the scanner's, never re-derived here."""

def find_heading(text: str, heading: str) -> tuple[int, int] | None:
    """(the heading event's `end` offset, its level) for the matching heading event; None when
    absent; AmbiguousHeading(n) when more than one matches. `heading` is either the full line
    form '## Text' (normalized text AND level must match) or the bare 'Text' (normalized text at
    any level — docsections.titled_section's contract). WHICH form a request is, is decided by
    the request: if it parses as an ATX heading line by the SCANNER'S OWN predicate (0-3 leading
    SPACES -- CommonMark counts indent in columns and a tab reaches column 4, so a tab-indented
    line is code, never a heading -- then 1-6 '#', then a space, a tab or end of line) it is the
    full form, always; otherwise the
    bare form. So a heading whose title itself starts with an
    ATX prefix ('### ## Text') is reachable only in full form, never bare — the one documented
    exclusion (design v1.84). Normalized text is CommonMark §4.2: the
    optional closing hash run (preceded by a SPACE OR A TAB, like the opening run) and trailing
    whitespace are stripped, so '## Text ##', '## Text\t##' and '## Text'
    are one heading and a document holding two of them raises AmbiguousHeading(2). Searches the scanner's
    `heading` events only."""

def extract(doc: str | Path, heading: str) -> list[Block]: ...   # calls find_heading, then bounds
def select(blocks: Sequence[Block], index: int | None = None) -> Block: ...
```

```python
# h-mad/tests/docsections.py  (delta)
import sys                                            # `re` goes with the local regex it served
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import h_mad_doc_block_exec as _dbe  # noqa: E402
# ^ the design's spelling verbatim (design v1.79) and the same idiom every
#   test under h-mad/tests/ uses for SCRIPT_DIR. The design's location for that spelling is
#   written as a LOCATOR and never as a number AND NEVER AS A SECTION NAME: `grep -Fn` on the
#   insert line above, run over
#   docs/02-design/features/doc-block-exec.design.md, returns exactly one hit, re-run at `b3be433`
#   on the design's shipping bytes and again at `dfae038`.
#   The -F is load-bearing and not tidiness: the bracket makes this
#   needle a BRE character class and a plain grep returns zero on text that is present. The plan
#   carries the same line once — one hit at `b3be433` and one at `dfae038`, both by `grep -Fc`
#   on the same needle — so the one-hit property holds under the stated target file: the
#   SECOND such caveat in the locator census above, recorded there beside the first.
#   `§Scanning` stood here beside the version pin until r15 and was FALSE at BOTH ends. Re-derived
#   at `dfae038` and at the cited revision alike: the needle's one hit sits inside the design's
#   `## Overview` at each of them, above the `### Scanning` heading rather than within it — taken
#   by comparing the hit's offset against that revision's own heading offsets — and at the cited
#   revision the whole span of `### Scanning` holds no occurrence of the needle at all. So it was
#   wrong when it was written and not drift. It is REMOVED rather than corrected to the right
#   section name, because the needle is the whole of the route; a section name is a sibling
#   location and expires exactly as a line number does. The class and the rule over it are
#   stated with the pre-dispatch sweep's residual in Conventions.
#   The number that stood here named a design line that moved, and no
#   instrument this document ships could see it, because it was written as prose rather than as
#   filename-colon-number (impl-plan audit v45). Today's docsections.py imports only `re`
#   (verified: its two import lines are `from __future__ import annotations` and `import re`), and
#   `re` goes with the local regex it served — so this delta's import line is entirely new.

def titled_section(text: str, heading: str) -> str:
    """The named section's body, bounded by the next same-or-higher heading.

    `heading` is the text after the `#`s. The section OWNS its subsections: a
    bound that stopped at any heading would cut a `##` section short at its first
    `###` and every assertion about the later part would fail for the wrong
    reason.
    """
    found = _dbe.find_heading(text, heading)
    assert found, f"missing section {heading!r}"
    start, level = found
    return text[start:_dbe.fence_aware_end(text, start, level)]


def section_from(text: str, offset: int, level: int = 2) -> str:
    """From an arbitrary offset to the next heading at `level` or higher.

    For a pin anchored on a symbol rather than a heading — the case a byte window
    is usually reached for, because the anchor is mid-section and there is no
    title to name.
    """
    return text[offset:_dbe.fence_aware_end(text, offset, level)]
# The two call-site lines carry NO inline comments: `docsections-local-bounder-restored` anchors
# on this exact region, and a comment here that is absent from its `find` would make the anchor
# miss the landed source (impl-plan audit v27 agy). What those comments said belongs in the
# prose above: `find_heading` replaces today's `re.search` at `:53`, and the `assert` stays local.
# Both docstrings are today's, quoted verbatim from `h-mad/tests/docsections.py:46-52` and
# `:60-65`, and both survive the migration unchanged — `titled_section`'s still describes the bare
# form it keeps passing. They are shown here because `docsections-local-bounder-restored` anchors
# on this exact region, so the delta and that row's `find` must be one literal source shape
# (impl-plan audit v24 nit). Two blank lines between the defs, PEP-8 as the file already has them.
# `_fence_aware_end` and the local heading regex are deleted; `__all__ = ["titled_section", "section_from"]` is unchanged.
```

```python
# h-mad/tests/test_docsections.py  (delta — the RED-safe WIRE-PIN scaffold)
import importlib, sys, types
import docsections

FENCED = "## Section\n```\n# not a heading\n```\nanchor text\n## Next\n"

def test_docsections_delegates_to_the_authoritative_bounder() -> None:
    calls: list[tuple] = []
    try:
        import h_mad_doc_block_exec as _real      # importable from GREEN on (docsections put scripts on sys.path)
    except ImportError:
        _real = None                              # RED: the module does not exist yet
    def rec_find(text: str, heading: str) -> tuple[int, int] | None:
        calls.append(("find_heading", text, heading))
        return _real.find_heading(text, heading) if _real is not None else (len(text), 2)
    def rec_end(text: str, offset: int, level: int) -> int:
        calls.append(("fence_aware_end", text, offset, level))
        return _real.fence_aware_end(text, offset, level) if _real is not None else len(text)
    fake = types.ModuleType("h_mad_doc_block_exec")
    fake.find_heading = rec_find
    fake.fence_aware_end = rec_end
    saved = sys.modules.get("h_mad_doc_block_exec")
    sys.modules["h_mad_doc_block_exec"] = fake
    try:
        importlib.reload(docsections)             # re-runs the module-level import: binds the fake at GREEN; a no-op at RED
        docsections.titled_section(FENCED, "Section")   # bare form: titled_section's contract
        docsections.section_from(FENCED, FENCED.index("anchor"), 2)
    finally:
        if saved is None:
            sys.modules.pop("h_mad_doc_block_exec", None)
        else:
            sys.modules["h_mad_doc_block_exec"] = saved
        importlib.reload(docsections)             # `_dbe` rebinds to the real module; no later test sees the fake
    assert [c[0] for c in calls] == ["find_heading", "fence_aware_end", "fence_aware_end"], (
        f"docsections did not delegate both the section start and its end: {calls!r}")
    assert calls[0] == ("find_heading", FENCED, "Section")             # titled_section: start lookup
    assert calls[1][1] == FENCED and calls[1][3] == 2                  # titled_section: (text, start, level)
    assert calls[2] == ("fence_aware_end", FENCED, FENCED.index("anchor"), 2)  # section_from
```
`importlib.reload` is required because `docsections` is already imported by the time the test
body runs (the test module's own `from docsections import section_from, titled_section`), so a plain `import` would not
re-execute the module-level `import h_mad_doc_block_exec as _dbe` line. At RED (`docsections.py`
unchanged, stdlib-only) the reload is harmless and neither recorder is ever called, so the test
fails on the call-sequence assertion — never an `ImportError`/`AttributeError`. At GREEN the reload
re-executes the delegating import, which finds the fake in `sys.modules` first, so `titled_section`
hits `find_heading` then `fence_aware_end`, and `section_from` hits `fence_aware_end`.

**Acceptance Criteria** (each is one named test; in `test_h_mad_doc_block_exec.py` unless stated):
- [ ] AC-1.1 `test_tagged_fence_under_heading_is_extracted`: a section with one tagged and one untagged fence yields exactly the tagged block, `shell == "strict"`, `lineno` = the opener's 1-based line, `text` = the body verbatim.
- [ ] AC-1.2 `test_untagged_fence_is_not_a_candidate`: a section with only untagged fences yields `[]`.
- [ ] AC-1.3 `test_two_tagged_blocks_without_index_are_ambiguous`: `select` on two blocks with no index raises `AmbiguousBlock` with `n == 2`.
- [ ] AC-1.4 `test_index_selects_and_past_end_is_not_found`: `select(blocks, 2)` returns the second; `select(blocks, 3)` on two raises `BlockNotFound`.
- [ ] AC-1.5 `test_section_owns_deeper_headings`: a `##` section containing `###` sub-headings with a tagged fence under one of them yields that fence; the next `##` (and a `#`) ends it.
- [ ] AC-1.5 `test_find_heading_accepts_full_and_bare_forms`: on a document with `## Text`, `find_heading(text, "## Text")` (full form) and `find_heading(text, "Text")` (bare form) return the same `(end, 2)`; on a document whose only `Text` heading is `### Text`, `find_heading(text, "## Text")` is `None` while the bare form returns `(end, 3)`.
- [ ] AC-1.5 `test_full_form_request_accepts_tab_and_eol`: the request predicate is the scanner's, so both of the scanner's non-space arms address a heading in full form. On a document whose heading is `##\tText` (a TAB after the hash run), `find_heading(text, "##\tText")` finds it at level 2; on a document whose heading is a title-less `##` (end of line after the hash run, title the empty string), `find_heading(text, "##")` finds it at level 2. Both are ATX headings the scanner already emits as `heading` events, so a space-only request predicate would scan them and then be unable to name them — which is what `request-predicate-space-only` mutates.
- [ ] AC-1.5 `test_heading_form_precedence_full_wins`: on one document holding **both** `### ## Text` (level 3, title `## Text`) and `## Text` (level 2, title `Text`) — `find_heading(text, "## Text")` returns the **level-2** heading only, because the request parses as an ATX line and is therefore the full form, matching title `Text` at level 2; `find_heading(text, "### ## Text")` returns the **level-3** heading only, matching title `## Text` at level 3; and **neither call raises `AmbiguousHeading`**. That last clause is what discriminates: under `form-precedence-bare-first` the request `## Text` also matches the level-3 heading's bare title and the call refuses as ambiguous, so a test asserting only the two positive results would pass against the mutant.
- [ ] AC-1.5/1.7 `test_closing_hash_run_does_not_change_heading_identity`: pins the normalization rule from both sides, **on both delimiters**. On a document whose only heading is `## Text ##`, both `find_heading(text, "## Text")` (full form) and `find_heading(text, "Text")` (bare form) find it and return the same `(end, 2)` — the closing run is stripped before the comparison, so the raw line is never what is matched. **The fixture carries the tab-preceded form `"## Text\t##"` beside the space-preceded one**, asserted identically, because the closing `#`-run delimiter is spaces-or-tabs and a space-only strip would leave `## Text\t##` unequal to `Text` and so unfindable in either form. On a document holding both `## Text` and `## Text ##`, the full form raises `AmbiguousHeading` with `n == 2`, because the two lines normalize to the same heading rather than to two distinct ones (design v1.67 §Scanning, design audit v63); the tab leg is asserted the same way, on a document holding `## Text` and `## Text\t##`. **Residual, measured at `74e126f`**: over the tracked corpus — `git ls-files -- h-mad handoff`, `*.md`, `archive/` excluded — **30** files hold **0** ATX headings whose closing `#`-run is preceded by a tab. **No live document or fixture outside this test depends on that closing-run tab arm** — shipping it space-only would be a silent divergence from the renderer the scanner grammar was oracled against, not a currently failing document, which is why a fixture rather than a corpus instance is what pins it. (That conclusion sits here, adjacent to its own measurement; v1.40 inserted the toolchain paragraph below between the two and left it stranded at the end of a paragraph about `grep -P`, where "the tab arm" had no nearby antecedent — impl-plan audit v38. The axis here is the **closing `#`-run delimiter**; the fence **opener's** indent has its own, separately measured, tab arm in Task 1's residual above, and the two must not be read as one.) The command is stdlib Python, not `grep -P`, and that is the point: **every runnable command this document ships must run under the stock macOS toolchain**, which is BSD, not GNU. `python3.11 -c "import re, subprocess, pathlib; fs = [f for f in subprocess.run(['git', 'ls-files', '--', 'h-mad', 'handoff'], capture_output=True, text=True).stdout.split() if f.endswith('.md') and '/archive/' not in f]; p = re.compile(' {0,3}#{1,6}[ \t].*\t#+[ \t]*'); print(len(fs), sum(1 for f in fs if any(p.fullmatch(l) for l in pathlib.Path(f).read_text(errors='replace').splitlines())))"` prints `30 0`, and **its output is what the sentence above describes** — the `grep -cP` pipeline this replaced (v1.39) printed a per-file count, not a file count, so its own description was wrong in a second way. The reason it mattered more here than elsewhere: `/usr/bin/grep` on macOS rejects `-P` outright (`grep: invalid option -- P`, rc 2, measured), the pipeline printed nothing at all, and **this feature's own Task 1 inherits `_TIMEOUT_CMD` and `_ABSENCE_CLAIMS` — guards that exist precisely because the stock macOS toolchain is not GNU**, so shipping a GNU-only command inside it was self-contradicting. **Class, first swept at `35698f9` for v1.41, re-swept at `700c599` for v1.48, and re-swept on the tree v1.53 ships** over the GNU-vs-BSD-divergent invocations (`grep -P`, `sed -i`, `readlink -f`, `date -d`, `xargs -r`, `stat -c`) — `awk '/^## Version History/{exit}{print NR": "$0}' docs/01-plan/features/doc-block-exec.impl-plan.md | grep -nE 'grep -P|sed -i|readlink -f|date -d|xargs -r|stat -c'` — the sweep returns **3** lines outside the Version History on the tree v1.53 ships, on v1.48's shipped body and on v1.41's alike — the site's stamp is re-written in the same edit that re-runs it, which v1.52 did not do here (impl-plan audit v47 should 1: the v1.52 entry republished this reading while the site still named v1.41 and v1.48 only, and no integer was wrong, only the stamp) — one more than the **2** `35698f9` reads (that commit holds v1.40's text; v1.41's stamp names the base it was authored against, not a commit whose body reads 3): AC-3.13, whose `stat -f %Lp .` (darwin) / `stat -c %a .` (GNU) pair already writes both forms; this bullet, which matches because it names the six tokens in prose; and Task 1's fence-opener residual, added at v1.41, which matches because it says its command uses **no** `grep -P`. **No GNU-only command survives in this document** — all three hits are prose about the class, none is an invocation. **This sweep is member (viii) of the needle-inside-scope enumeration in Conventions** (impl-plan audit v44): all six of its needles are literal and all six are written into the body it counts, by this very bullet. Unlike the pre-dispatch sibling sweep it *does* publish a reading, and the reading survives only because each of the three hits is named and triaged here rather than compared to a target — a bare **3** with no member list would be indistinguishable from three real invocations. **Residual on the sweep itself**: nothing detects a GNU-only flag in a document — no test, no precheck, no CI step reads the commands this document ships — so the next one is prevented by a reviser running that six-token sweep, not by anything catching it (impl-plan audit v37).
- [ ] AC-1.5 `test_adjacent_heading_bounds_the_section`: `## A` immediately followed by `## B` whose section holds a tagged block — `extract(doc, "## A")` (full form) is `[]`, and with `start, level = find_heading(text, "## A")`, `fence_aware_end(text, start, level) == start` (the adjacent heading's line starts exactly at `start` and is a boundary).
- [ ] AC-1.5 `test_heading_lookalikes_are_not_headings`: a fixture placing `#hashtag`, `#######` (seven), `    ## x` (four-space-indented) and `\t## x` (**tab-indented — CommonMark measures the leading indent in columns and a tab reaches column 4, so this is indented code, not a heading**; the tab leg is what refuses a `line.lstrip()` "simplification" of the predicate, which would accept it) where each would end the requested section or start one — the block under the real heading is still the only candidate (the section owns the block past every lookalike), and a lookalike never matches the requested heading (asking for `# hashtag`, `## x` or the seven-run line in the full form yields no heading match; every `extract`/`find_heading` argument in this file's ACs is the full form unless it says bare).
- [ ] AC-1.5 `test_titleless_heading_is_a_new_only_member`: the EMPTY ATX heading case, held by a hostile FIXTURE rather than by the live corpus (round-eighteen sheet FACT 3 — the `h-mad/SKILL.md` specimen this document's guard-narrowing accounting enumerated at `fbc2ea0` was removed by `b39d9dc`, and a corpus specimen a tooling commit can delete is a measurement, not a test). The test writes `titleless.md` under `tmp_path` with the body `before\n#\nafter\n` and asserts `titleless=1 new_only=1` on that file alone: the scanner's ATX predicate emits the bare `#` as a level-1 heading with an empty title, and the space-required regex the guard narrows FROM emits nothing for it, so the differential's `new_only` set on that one file is exactly that heading. The two predicates are read out of the committed probe rather than described from memory: `OLD = re.compile(r"^(?P<marks>#+) (?P<title>.*?)\s*$")` requires a literal SPACE after the hash run, and `NEW_LINE = re.compile(r"^(?P<ind> {0,3})(?P<marks>#{1,6})(?P<rest>[ \t].*|)$")` admits an empty `rest`, which is the whole of the difference on this member. **It adds NO mutation row of its own and the matrix total is 86 at this batch**, for the reason `closing-hash-run-kept`'s residual already gives: the row list here MIRRORS the design's matrix, and inventing one here would put this document one above it. The 86 comes from the design's own r18 addition on the substitution scan axis, not from this one. **Residual, stated exactly**: no mutation row is dedicated to the empty-ATX arm, so this test is the fixture that keeps the accounting's claim non-vacuous rather than a killer for a row; a row for it is a DESIGN change and is owed to the design if the round wants one.
- [ ] AC-1.5/1.6 `test_requested_heading_quoted_inside_a_fence_is_not_a_section_start`: the requested heading appears first inside a ```` ```markdown ```` fence with a tagged block under that quoted copy, then for real with a tagged block under it; `extract` returns only the block under the real heading (the fenced copy is a `body` line, never a heading match, and the tagged block under it is never a candidate).
- [ ] AC-1.6 `test_quoted_tag_inside_longer_fence_is_not_an_opener`: a four-backtick fence whose body contains ` ```bash hmad:exec ` yields no candidate from the quoted line; `test_tag_quoted_inside_a_tilde_fence_is_not_an_opener`: same inside `~~~`; `test_indented_literal_tag_is_not_a_candidate`: `    ```bash hmad:exec` (four spaces) is never a candidate, **and neither is `\t```bash hmad:exec`** — one TAB, which CommonMark advances to column 4, so it is indented code and not an opener; this is the tab arm of the fence-opener indent, measured at **0** corpus instances at `35698f9` (Task 1's residual above carries the command), so this fixture is its **only** pin, and no mutation row follows from this axis — the matrix total is **86** at this batch and none of it comes from here; `test_backtick_in_info_string_is_not_an_opener`: ```` ```bash hmad:exec `x` ```` is inert — not a candidate, not `BadInfoString`, and the following ``` line opens a fence; `test_closer_with_trailing_text_does_not_close`: a ```` ```trailing ```` line inside a quoting fence does not close it; `test_indented_closer_does_not_close`: a ```` ``` ```` line at four spaces inside a bash fence stays in the body and the fence ends at the next 0–3-space closer; `test_indented_fence_body_is_deindented`: openers at 1, 2 and 3 spaces yield bodies with that indentation stripped, and a body line indented less than the opener loses only what it has.
- [ ] AC-1.7 `test_duplicate_headings_refuse`: two identical `###` headings (fixture mirrors `h-mad/invariants.example.md`), requested in the full form → `AmbiguousHeading` with `n == 2`; `test_bare_form_duplicate_headings_refuse`: `## Text` and `### Text` in one document, `find_heading(text, "Text")` (bare form) → `AmbiguousHeading` with `n == 2` — **a regression test on the same guard, not a second killer**: `duplicate-heading-takes-first`'s one `test` key is `tests/test_h_mad_doc_block_exec.py::test_duplicate_headings_refuse`, and this bare-form test exercises that guard through the other input form (design v1.83 matrix, impl-plan audit v25). It is the deliberate tightening over the old `re.search` first-match (design §Scanning; both live `titled_section` targets in `h-mad/SKILL.md` measured unique, so no caller acquires the refusal).
- [ ] AC-1.8 (bounder's own contract) `test_bounder_ignores_a_heading_inside_a_tilde_fence`, `test_bounder_ignores_an_indented_literal_fence`, `test_bounder_from_an_offset_inside_a_fence` (`start` inside an open fence; a fenced `#` after it does not end the section), `test_bounder_offset_after_a_marker_run_on_a_non_closing_line` (`start` immediately after the three backticks of a ```` ```trailing ```` body line; the next fenced `#` still does not end the section), `test_fence_events_trace_on_every_hostile_fixture` (exact event trace — kind, marker, run, indent, info, candidate, level AND the `start`/`end` offsets of every line, on LF and CRLF copies of each fixture — over: balanced and unbalanced four-backtick, tilde-quoted backtick, backtick-in-info, indented literal, trailing-text closer, offset-inside-a-fence), `test_extract_has_no_fence_state_of_its_own` (source assertion on marker-run **recognition**, **parsing the source of `h_mad_doc_block_exec.py` only** — the file scope of the Conventions invariant, and the assertion reads no other file: the literals ```` ``` ```` and `~~~`, the run-length regex, any `in_fence` toggle, and the ATX heading regex (a `#{1,6}` pattern or any `startswith("#")` test) appear in exactly one function body, `_fence_events`; consumers may read `_FenceEvent.kind`/`.marker`/`.run`/`.indent`/`.info`/`.candidate`, and `extract` selects on `.candidate`, never on `.marker`).
- [ ] AC-1.8 (the wire) `test_docsections_delegates_to_the_authoritative_bounder` (WIRE-PIN, in `test_docsections.py`, scaffold above): on the fenced fixture `titled_section` records exactly one `find_heading` call with `(text, heading)` and one `fence_aware_end` call with `(text, start, level)`, and `section_from` records one `fence_aware_end` call with `(text, offset, level)` on the `sys.modules` fake; its RED reason is the assertion on the call record, never an import error.
- [ ] AC-1.8 `test_titled_section_ignores_a_heading_inside_a_fence` (in `test_h_mad_doc_block_exec.py`, function-local `import docsections`): a document whose requested heading first appears quoted inside a ```` ``` ```` fence and then for real — `titled_section(doc, heading)` (bare form, `titled_section`'s contract) returns the real section's body (the old `re.search` at `h-mad/tests/docsections.py:53`, inside `titled_section` (`:45`), picked the fenced copy).
- [ ] AC-1.8 `test_docsections_has_no_second_bounder`: the source of `docsections.py` defines no function named `_fence_aware_end` and contains no marker-run scanning (the same source predicate as `test_extract_has_no_fence_state_of_its_own`, applied to that file).
- [ ] AC-1.8 `test_docsections_imports_when_collected_alone`: `subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "h-mad/tests/test_docsections.py"], cwd=REPO_ROOT)` exits 0 (nothing but `docsections.py` itself puts `h-mad/scripts` on `sys.path` in that run). **It is COLLECTION-only and that is load-bearing, not a speed optimisation** (impl-plan audit v47 codex must 2, round seventeen's shared decision 3d): the WIRE-PIN is added to this same file, so a run form that executes it would go red under `docsections-delegation-reverted` and make this document's two "every other test stays green" claims false, and the wire mutant would have two failing tests instead of the one the wire contract requires. `--collect-only` imports the module and enumerates every test in it, which is the whole of what this AC pins, and runs none of them, so a red WIRE-PIN cannot reach it. **Residual, stated exactly**: the pre-existing `test_docsections.py` tests are no longer RUN in isolation by any AC. They run in the full suite that AC-6.4's floor measures and in the 5e module-scoped run, and nothing else covers the narrower case of one of them failing only when that file is collected alone — a case no test ever covered, since the previous form's exit code could not distinguish it from a WIRE-PIN failure either. `test_docsections_imports_from_an_unrelated_cwd`: `subprocess.run([sys.executable, "-c", "import docsections"], env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "h-mad" / "tests")}, cwd=tmp_path)` exits 0. Both live in `test_h_mad_doc_block_exec.py`, which never imports `docsections` at module level.
- [ ] AC-1.8 the existing `test_docsections.py` tests pass unchanged, and the shared bounder handles the unbalanced four-backtick case the old toggle got wrong (`test_docsections_unbalanced_four_backtick_fence`, in `test_h_mad_doc_block_exec.py`, calling `docsections.titled_section` on the fixture through a function-local `import docsections`: a ```` ```` ```` opener followed by a ```` ``` ```` line and a `# comment` at column 0 — the toggle ends the section at the comment; the bounder does not).
- [ ] AC-1.9 `test_index_zero_refuses`: `select(blocks, 0)` and `select(blocks, -1)` raise `BadIndex` carrying the value, and no lookup happened (the blocks list may be empty).
- [ ] AC-3.7 `test_unknown_info_key_refuses` (`shell=fish`, `mode=x` → `BadInfoString` with that token) and `test_duplicate_info_tokens_refuse` (`hmad:exec hmad:exec`, `shell=strict shell=plain` → `BadInfoString` naming the repeated token); `test_untagged_fence_info_string_is_never_inspected` (` ```bash --frozen ` untagged raises nothing).
- [ ] AC-3.12 `test_invalid_utf8_document_is_unreadable`: a document file containing byte `0xff` → `DocUnreadable` (and, once Task 4 lands, `UNREADABLE reason=doc_unreadable` on the CLI — the CLI half is added in Task 4).
- [ ] `docsections.json` reports `ALL_CAUGHT` with eight rows, each with a `test` key, under `target_command` (`docsections-heading-lookup-reverted` is killed by the WIRE-PIN's empty `find_heading` record, `find_heading` itself untouched); under `docsections-delegation-reverted` the WIRE-PIN fails and **every** other test stays green — all of `test_docsections.py`'s pre-existing tests and all of `test_h_mad_doc_block_exec.py`, the source guard `test_docsections_has_no_second_bounder`, the two docsections-side hostile tests `test_docsections_unbalanced_four_backtick_fence` and `test_titled_section_ignores_a_heading_inside_a_fence`, and both import tests included — the first of those two because AC-1.8 makes it collection-only, which is the reason this sentence is true rather than an aspiration (the mutation's `test` key is the WIRE-PIN, and the mutant's failing set has exactly that one member); under `docsections-local-bounder-restored` the source guard goes red (its `test` key), as do the WIRE-PIN and the two hostile tests.

**Mutation rows added to `doc_block_exec.json`** (mechanism per the design's Test Plan table):
`tag-check-removed`, `fence-run-length-ignored`, `section-bound-ignores-level`,
`duplicate-heading-takes-first` (one `test` key,
`tests/test_h_mad_doc_block_exec.py::test_duplicate_headings_refuse`;
`test_bare_form_duplicate_headings_refuse` goes red on the same mutant through the bare form and
stays a regression test — the Conventions bullet names the one other row with this shape),
`select-first-on-ambiguous`, `index-below-one-accepted`,
`duplicate-info-token-last-wins`, `unknown-info-key-ignored`, `scanner-duplicated-in-consumer`,
`doc-decode-error-unwrapped`, `closer-trailing-text-accepted`, `body-indent-not-stripped`,
`indented-opener-accepted`, `indented-closer-accepted`, `prefix-state-truncated-mid-line`,
`prefix-fence-state-skipped`, `backtick-in-info-accepted`, `tilde-fence-not-tracked`,
`heading-match-ignores-fence-state`, `heading-lookalike-accepted` (grammar loosened to
`line.lstrip().startswith("#")`), `adjacent-heading-skipped` (boundary predicate `>` instead of
`≥`), `heading-level-pin-ignored` (the full form matching on text alone, ignoring the hash count),
`request-predicate-space-only` (the full-form request predicate is narrowed to accept only a
space after the hash run, while the scanner keeps accepting a space, a tab or end of line, so the
requests `##\tText` and `##` fall through to the bare form and no longer select the headings the
scanner emits for them; killed by
`tests/test_h_mad_doc_block_exec.py::test_full_form_request_accepts_tab_and_eol`. It is the row
that makes "the predicate is the scanner's" a checkable claim rather than a stylistic one),
`form-precedence-bare-first` (`find_heading` tries the bare form first, or unions the two forms,
so the request `## Text` also matches a `### ## Text` heading and the call refuses as ambiguous;
killed by `tests/test_h_mad_doc_block_exec.py::test_heading_form_precedence_full_wins` on its
no-`AmbiguousHeading` clause. It is discriminated from `heading-level-pin-ignored`, which makes
the full form match any level: that mutant is caught by
`test_find_heading_accepts_full_and_bare_forms`'s level-mismatch leg, and neither test goes red
under the other's mutant, because this document's other heading fixtures hold no title beginning
with an ATX prefix),
`closing-hash-run-kept` (`_fence_events` leaves the optional closing hash run in a heading event's
text, so `## Text ##` no longer satisfies a `## Text` request and a `## Text`/`## Text ##` pair
counts as one heading instead of two; killed by
`tests/test_h_mad_doc_block_exec.py::test_closing_hash_run_does_not_change_heading_identity`, which
goes red on every one of its sides — the sole `## Text ##` document stops matching, its
`## Text\t##` twin stops matching, and each mixed document stops raising `AmbiguousHeading(2)`.
**Residual, stated exactly**: this row mutates the strip *away*, so it is red under the tab leg as
well as the space leg and does not discriminate between them. A narrower mutant — stripping only a
**space**-preceded closing run — has **no row**, deliberately: the row list here is the design's
matrix and adding one would put this document's total one row above the design's. What stands in
for it is the fixture: the tab leg of `test_closing_hash_run_does_not_change_heading_identity`
fails outright under a space-only strip, because `## Text\t##` normalizes to `Text\t##` and is
findable in neither form)
— 25 rows.
**Rows in `docsections.json`** after this task: the four existing (two re-anchored) plus
`docsections-delegation-reverted`, `docsections-syspath-setup-removed`,
`docsections-heading-lookup-reverted` and `docsections-local-bounder-restored` — 8 rows.

**Dependencies on other tasks**: None.

**Expected RED split** (stated in prose; the assembler does not require counts for a wiring task):
- Every test in `test_h_mad_doc_block_exec.py` fails at RED — the module does not exist, so the file's own `import h_mad_doc_block_exec as dbe` raises `ModuleNotFoundError` at collection. That includes `test_docsections_has_no_second_bounder` (which would also fail on its source assertion), `test_docsections_unbalanced_four_backtick_fence` and `test_titled_section_ignores_a_heading_inside_a_fence` (which would also fail because the old toggle mis-bounds and the old regex picks a fenced heading) and the two import tests, which are **insensitive to the docsections delta** (they pass against the unchanged, stdlib-only `docsections.py` as soon as their file collects) and are carried as **regression guards** for the import arrangement the delegating import introduces; their teeth are the `docsections-syspath-setup-removed` mutation, not RED.
- In `test_docsections.py`: the WIRE-PIN — its only new test — fails on its call-sequence assertion (no recorder was ever called: the unchanged caller still uses its local `re.search` and its private `_fence_aware_end`).
- All pre-existing `test_docsections.py` tests are regression guards and must pass at RED.
Wire-scoped revert at 5e: apply `docsections-delegation-reverted` (the one-line replacement above:
the shared import swapped for a private `spec_from_file_location` instance of the same file, no
local bounder restored), leave the helper and the tests intact — the WIRE-PIN must fail (its
`sys.modules` fake is never bound, so no call reaches it) and **every other test stays green**,
`test_docsections_has_no_second_bounder` and the two docsections-side hostile tests included, **and
`test_docsections_imports_when_collected_alone` among them, because it collects that file rather
than running it** — under the previous run-the-file form this claim was false, which is what made
the collect-only rewrite a correctness change and not a preference; the
mutation's `test` key stays the WIRE-PIN, and the mutant's failing set is that one test exactly. The local-restore revert is the separate eighth row,
`docsections-local-bounder-restored`, and is not the 5e wire revert.

**RED gate** (run BEFORE any production code, two dispatches because at RED `test_h_mad_doc_block_exec.py` raises `ModuleNotFoundError` at **collection** and pytest then runs nothing else in that command):
`hmad-dispatch run --timeout 600 -- python3.11 -m pytest tests/test_h_mad_doc_block_exec.py -q` must report the collection error, and separately `hmad-dispatch run --timeout 600 -- python3.11 -m pytest tests/test_docsections.py -q` must show the WIRE-PIN failing on its call-sequence assertion with every pre-existing test in that file passing. Splitting the two files is what makes the second observation possible at all. Judge it on the pytest summary, never on `$?` alone, and keep the recorded output beside the task as the 5d dispatch's `--out` file; `rc=124` is the wrapper's expiry, not a RED result. This is what `h_mad_assemble_tdd.py --phase red` dispatches, with `--test-path` set to the file named above, `--expect-fail` and `--expect-pass` set to the counts this split states for a new-behaviour task and omitted for a wiring task (Tasks 1 and 5 state their RED in prose, as the assembler allows), `--out` the recorded report kept beside the task, and `--timeout 600`.

---

## Task 2: substitution

**Production file**: `h-mad/scripts/h_mad_doc_block_exec.py`
**Test file**: `h-mad/tests/test_h_mad_doc_block_exec.py`
**Task shape**: `new-behaviour`

**Description**: `substitute(block, subs)` returns a **new** `Block` (`dataclasses.replace`) and a
per-key count dict. An empty map short-circuits to `(dataclasses.replace(block), {})` before any
regex is built. Otherwise: an empty key raises `BadSubstArg("")`; then **two independent overlap
predicates run, and both refuse under the one `SUBST_OVERLAP` verdict**; then counts are
taken on the original `block.text` (`text.count(key)` per key); every key with count 0 is
collected **in the map's insertion order** and, if any, `MissingSubstitution(keys)` is raised;
replacement is one simultaneous pass — `re.sub("|".join(map(re.escape, keys)), lambda m: subs[m.group(0)], text)` —
so replaced text is never re-scanned and the result is independent of map order.

**The two overlap predicates, and why there are two** (design must 1 / impl-plan audit v47 codex
must 1, round seventeen's shared decision 3a). The class is *two keys' matches are not
independent*; the map-static substring check was one member of it and the earlier text treated it
as the whole. **Reproduced on the pinned interpreter (3.11.8) with the prescribed escaped
alternation and a recording callback**, so this is a measurement and not a reading of the
algorithm: `abc` under `{ab→X, bc→Y}` returns `Xc` while `text.count` reads `ab=1 bc=1` and the
callback fired `ab=1 bc=0`; `abc abc` returns `Xc Xc`, counts `2`/`2`, fired `2`/`0`; reversing
the map to `{bc→Y, ab→X}` returns `Xc` again with the same split, because the alternation is tried
left-to-right **at each position** and position 0 is where `ab` wins. The control
`ab bc ab bc` returns `X Y X Y`, counts `2`/`2`, fired `2`/`2`. So the reported count can exceed
the replacements performed, which spec AC-2.7's "the reported occurrence count equals the number
replaced" forbids — and the substring check does not reach it: `any(a != b and a in b)` over
`{ab, bc}` is **False**, measured.
**ONE representation carries both kinds, and it is the design's** (round-eighteen sheet FACT 4 a /
C2 iii; codex impl-plan must 3 and design must 2 at v48, filed independently from both sides). The
refusal carries a SINGLE tagged list `pairs`, whose members are `(kind, a, b, offset|None)` with
`kind ∈ {"overlap", "intersect"}`. **There is no second `intersections` argument and no second
attribute**: the split this document carried was one of three live representations across the two
documents, and an implementer following the design failed the test this document named.

- **The substring predicate** (unchanged, map-static): if any key is a substring of another, the
  refusal contributes a member `("overlap", a, b, None)` for each unordered `(shorter, longer)`
  pair, one `overlap: "<a>" "<b>"` detail line each.
- **The span-intersection predicate** (new, text-dependent) runs **beside** it, never instead of
  it — they are different predicates and each catches what the other cannot: `{a, ab}` against a
  text holding no `ab` is substring-refused and not span-refused, and `{ab, bc}` in `abc` is the
  reverse. All match spans of all keys are collected on the **original** `block.text` before any
  replacement; two spans belonging to **different** keys that share an index intersect. The
  refusal contributes a member `("intersect", a, b, offset)` — one per unordered pair of keys,
  sorted by `(offset, a, b)` within the kind — one `intersect: "<a>" "<b>" "<offset>"` detail line
  each. **The span scan enumerates OVERLAPPING occurrences and the form is pinned, because the
  obvious form is wrong** (round-eighteen sheet FACT 4 b; design codex must 2 at v97): spans come
  from `re.finditer(r"(?=" + re.escape(k) + r")", text)` with span `(m.start(), m.start() + len(k))`,
  never from `re.finditer(re.escape(k), text)`, which enumerates only NON-overlapping matches per
  key and so can miss an intersection outright. Measured on the pinned interpreter: on `aaab` the
  lookahead form yields `aa` at `[0, 2)` and `[1, 3)` and `ab` at `[2, 4)`, while the bare form
  yields `aa` at `[0, 2)` only — under keys `{aa, ab}` the bare form finds NO intersection and the
  lookahead form finds one sharing index **2**, so the emitted line is exactly
  `intersect: "aa" "ab" "2"`. That fixture is carried as a test below precisely because it
  discriminates the two scan forms, which the `abc` fixture does not. **Two determinism rules fix which triple a pair yields, and they are stated because the
  earlier wording of the second was wrong** (round seventeen, the spec author's run, which outranks
  the decision sheet): (i) within a triple, **`a` is the lexicographically SMALLER key and `b` the
  larger**, so an unordered pair has exactly one spelling; (ii) `offset` is the **smallest character
  index the two spans SHARE**, 0-based into `block.text` — **not** the start of the earlier span,
  which is what "the index of the first intersecting occurrence" was read as and which gives a
  different number on the canonical fixture. On `abc` under `{ab: X, bc: Y}` the two spans are
  `[0, 2)` and `[1, 3)`, they share index **1** and nothing lower, so the emitted line is exactly
  `intersect: "ab" "bc" "1"` — `0` would be the earlier span's start and is the value the superseded
  wording produced. **All three values are quoted**, because spec FR-4 quotes every detail-line value without
  exception and the bare-field list governs the `DOCBLOCK:` line only; `offset` is a
  helper-produced int and is quoted for the same reason `pgid:` is (design v1.79 settled the bare
  list as exhaustive).

Both refuse under the existing `SUBST_OVERLAP` head at exit 0 with nothing executed, and `keys=`
keeps counting **distinct keys implicated across both kinds**. **`OverlappingSubstitution` therefore
keeps ONE field and widens its member shape**: `def __init__(self, pairs)`, whose body binds
`self.pairs = list(pairs)` so the one field is a list at every read site, and whose members are the
tagged `(kind, a, b, offset|None)` quadruples above. **The renderer reads `kind` to choose the
detail line** — `overlap:` for a substring member, `intersect:` for a span member — which is why the
tag is on the member rather than in a second list. **The member shape is this document's spelling of
the design's decision** and not an independent one: the design states that `pairs` carries both
kinds each tagged with the kind that raised it, and this is that sentence written as a type. **Ordering against `MissingSubstitution`, stated rather than left
implicit**: the intersection scan runs immediately after the substring check and **before** the
count pass, so `SUBST_OVERLAP` outranks `SUBST_MISSING` when both conditions hold. Moving the scan
across the count pass could not change *which* pairs it finds — a key whose count is 0 contributes
no spans and so can never be a member of an intersecting pair — only which verdict wins, and that
is the choice being recorded.
**Residual, stated exactly, and the round-seventeen version of it is WITHDRAWN rather than
repeated**: a key intersecting **itself** (`aa` in `aaa`) is not an intersection between two keys
and is deliberately outside the predicate, and on `aaa` under `{aa→Z}` the reported count still
equals the replacements performed (`Za`, `text.count` reading `1`, callback fired `1`), so AC-2.7's
promise holds there. **What is withdrawn is the reason round seventeen gave for calling that safe** —
that the counts stay equal because the overlapping self-occurrence is invisible — because the same
fact that falsified the bare scan falsifies it: an overlapping self-occurrence CAN hide a cross-key
intersection, which is exactly `aa` at `[1, 3)` in `aaab`. The residual therefore stands on the
lookahead enumeration, which sees that occurrence, and not on its absence. A second uncovered shape would be a key whose matches are made to overlap by the
replacement itself, which cannot arise because the pass is simultaneous and replaced text is never
re-scanned.

**Code structure**:
```python
# raises BadSubstArg, MissingSubstitution, OverlappingSubstitution — defined in Task 1
# __all__ += ["substitute"]
def substitute(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]: ...
```

**Acceptance Criteria** (**eleven** tests — the eleven enumerated below, one per `test_` name. **The count is DERIVED from this list and the derivation is stated, because the list also NAMES a test that is not one of them**: the distinct `test_` names inside the ten bullets below are twelve, of which `test_cli_subst_overlap_detail_lines` is a Task 4 test cited as a forward reference, leaving eleven this task adds. Ten bullets, eleven tests — the bullet count is not the test count and never was, because AC-2.2 carries two):
- [ ] AC-2.1 `test_path_substitution_replaces_the_key`: `{"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": "/tmp/x y/gate.py"}` on a block containing the key yields text with the value (a path with a space) and count 1.
- [ ] AC-2.2 `test_absent_key_refuses`: a key not in the block → `MissingSubstitution` with `keys == [key]`; `test_empty_substitution_map_is_a_no_op`: `substitute(block, {})` returns an equal `Block` that is not the same object and `{}`.
- [ ] AC-2.3 `test_two_missing_keys_are_listed_in_map_order`: `{"B": "1", "A": "2"}` both absent → `keys == ["B", "A"]`.
- [ ] AC-2.4 `test_metacharacter_key_is_literal`: key `a.[b]*` replaces only the literal occurrence.
- [ ] AC-2.5 `test_multi_occurrence_count_equals_replacements`: a key occurring 3 times → count 3 and 3 replacements.
- [ ] AC-2.6 `test_value_containing_another_key_is_not_rescanned`: `{"A": "B", "B": "C"}` and `{"B": "C", "A": "B"}` on `A B` both yield `B C` with counts `{"A": 1, "B": 1}`.
- [ ] AC-2.7 (substring clause) `test_overlapping_keys_refuse`: keys `a`, `ab`, `abc` → `OverlappingSubstitution` with `pairs == [("overlap","a","ab",None),("overlap","a","abc",None),("overlap","ab","abc",None)]` (no text is needed to reach this arm and the fixture text holds no `abc`), and three distinct keys implicated. **`pairs` is the ONE field and it is a LIST**, so an assertion never has to distinguish a tuple from a list, and there is no second `intersections` attribute to assert empty; a substring member's fourth element is `None` because a substring overlap has no text offset.
- [ ] AC-2.7 (intersection clause) `test_substitute_refuses_intersecting_spans`: on a block whose text is `abc`, `substitute(block, {"ab": "X", "bc": "Y"})` raises `OverlappingSubstitution` with `pairs == [("intersect", "ab", "bc", 1)]`, two distinct keys implicated, and the block's text unchanged — nothing was replaced. **This test asserts the exception DATA and nothing about an emitted line** (round-eighteen sheet FACT 4 e; codex impl-plan must 4 at v48): `substitute` is an API that raises, the renderer that turns a member into `intersect: "ab" "bc" "1"` lands in **Task 4**, and a Task 2 test that asserted the line could not pass at Task 2's own GREEN boundary. The quadruple carries the same three determinism rules the line does — `ab` before `bc` because it is lexicographically smaller, and `1` because that is the smallest index the spans `[0, 2)` and `[1, 3)` share, `0` being the superseded wording's answer — so the assertion still discriminates the two readings; the LINE's shape is pinned by `test_cli_subst_overlap_detail_lines` in Task 4. **The true-negative arm is in the same test and is what keeps the predicate from being a blanket refusal**: on a block whose text is `ab bc ab bc` the same map substitutes to `X Y X Y` with counts `{"ab": 2, "bc": 2}`, because no two spans share an index. Both legs measured on 3.11.8 before this AC was written.
- [ ] AC-2.7 (scan-form clause) `test_substitute_refuses_overlapping_occurrences_of_one_key`: on a block whose text is `aaab`, `substitute(block, {"aa": "X", "ab": "Y"})` raises `OverlappingSubstitution` with `pairs == [("intersect", "aa", "ab", 2)]`. **This fixture exists because it DISCRIMINATES the two scan forms and the `abc` fixture does not** (round-eighteen sheet FACT 4 b): measured on 3.11.8, the prescribed lookahead enumeration `re.finditer(r"(?=" + re.escape(k) + r")", text)` yields `aa` at `[0, 2)` and `[1, 3)` and `ab` at `[2, 4)`, sharing index 2, while the bare `re.finditer(re.escape(k), text)` yields `aa` at `[0, 2)` alone and finds NO intersection — so an implementation written with the bare form passes the `abc` fixture and fails this one. **It NOW CARRIES a mutation row and the matrix total moves to 86**: the design's r18 revision added `intersect-scan-non-overlapping` for exactly this axis, so the row this AC recorded as a design-side debt through the first half of round eighteen has been added and is mirrored in `doc_block_exec.json` below. `intersect-check-removed` does NOT reach the axis — it deletes the predicate outright, which the `abc` fixture already reds — whereas this row keeps the predicate and narrows its SCAN, which only the `aaab` fixture can see. That is the discrimination this test was written for, and it is now a killer rather than a fixture standing beside an unkilled arm.
- [ ] AC-2.8 `test_empty_key_is_refused_by_the_api`: `substitute(block, {"": "v"})` → `BadSubstArg` with `raw == ""`.

**Mutation rows added here**: `missing-key-silently-skipped`, `overlap-resolved-by-order`,
`replacement-sequential`, `empty-map-not-short-circuited`, `empty-key-accepted-by-api`,
`intersect-scan-non-overlapping` (the span scan's lookahead
`re.finditer(r"(?=" + re.escape(k) + r")", text)` becomes `re.finditer(re.escape(k), text)`, so only
non-overlapping occurrences of each key are enumerated and a key that begins inside its own earlier
match is never seen; killed by
`tests/test_h_mad_doc_block_exec.py::test_substitute_refuses_overlapping_occurrences_of_one_key`,
the AC-2.7 scan-form clause above. **This row is the design's, added in its r18 revision, and it is
mirrored here rather than invented**: under the mutant the `aaab` fixture under `{aa→X, ab→Y}` finds
NO intersection and substitutes to `XY` instead of refusing with `intersect: "aa" "ab" "2"`.
**Its discrimination from `intersect-check-removed` is derived from what each mutant leaves
standing, in both directions**: that row DELETES the predicate, under which
`test_substitute_refuses_intersecting_spans` goes red on the `abc` fixture while this row's killer
also reds, so the two are not independent from that side — but this row KEEPS the predicate and
narrows only its scan, and `abc`'s two spans `[0, 2)` and `[1, 3)` are each a first occurrence of
their own key, so the bare scan finds them both and `test_substitute_refuses_intersecting_spans`
stays GREEN under it. **The `abc` fixture cannot kill this row and the `aaab` fixture can**, which is
why the two fixtures are two tests rather than one parametrisation),
`intersect-check-removed` (the span-intersection predicate deleted, the substring check left in
place, so `{ab, bc}` on `abc` substitutes to `Xc` and reports `ab=1 bc=1`; killed by
`tests/test_h_mad_doc_block_exec.py::test_substitute_refuses_intersecting_spans`. **It is
discriminated from `overlap-resolved-by-order` in both directions, which is why the two predicates
are two rows rather than one**: that row removes the substring check, under which
`test_overlapping_keys_refuse` goes red while `{ab, bc}` on `abc` is still refused by the
surviving intersection scan, so this row's killer stays green; and this row leaves the substring
check intact, so `{a, ab, abc}` still refuses and `test_overlapping_keys_refuse` stays green under
it) — **7 rows**, up from 6 with the design's r18 addition above.

**Dependencies on other tasks**: Task 1 (for `Block`).

**Expected RED split — WHOLE-FILE totals, because the RED command runs the whole accumulating
file** (impl-plan audit v47 codex must 6, round seventeen's shared decision 3h). **Failing**: the
**eleven** tests this task adds, all with `AttributeError` (`substitute` absent; its three exceptions
already exist from Task 1). **That `AttributeError` is a RED BY CONSTRUCTION and the document says so, because the implementer prompt otherwise reads it as an unwritten test.** The prompt's rule is scoped: for a `wiring` task an `ImportError`/`AttributeError`/`NameError` standing in for a behavioural assertion is not a RED, while for a task that introduces a NEW symbol the first RED is `AttributeError`/`ImportError` **by construction** (the symbol does not exist yet), acceptable only when the same test also asserts the behaviour that must hold once the symbol exists, so it stays meaningful after GREEN. That rule is located by needle rather than by line — `grep -n 'by construction' h-mad/references/codex-implementer-prompt.md`, one hit, verified at `cac6edc` — because a line pin into a REFERENCE file is unverifiable by anything standing in this repository: the precheck files it under the LINEPIN **advisory** class, which by construction does not move a verdict, so nothing catches it drifting. **The standing control is NOT the reason, and attributing the preference to it was wrong**: `test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins` asserts `"SKILL.md:" not in joined` and is blind to every other path, so it could never have caught a pin into this file; task #29 was a `SKILL.md` pin and is a different member of the same class. **Task 2 is a new-symbol task, not a wiring task**: it carries no `WIRE:`/`WIRE-PIN:` and `substitute` does not exist before it, so every one of its eleven REDs is the by-construction case, and every one of them asserts a post-GREEN behaviour in the same test — the counts, the refusals and the tagged `pairs` members above — rather than stopping at the missing attribute. **Passing**: every test Task 1 landed in
`test_h_mad_doc_block_exec.py`, one regression-guard block, none of which this task touches.
**Expected passing is therefore NOT 0**, which is what the split said through v1.52 — and the
implementer prompt directs a STOP when the stated counts and the observed ones disagree
(`references/codex-implementer-prompt.md:62`, **re-read at `cac6edc` rather than carried** — the freeze commit edited that file, one line changed in place per `git diff --stat fbc2ea0 cac6edc`, and `sed -n '62p'` still prints the expected-counts STOP rule, so the pin is re-verified at the sha this revision ships against; the assembler only prints the pair
into the prompt, at `h-mad/scripts/h_mad_assemble_tdd.py:246`, and compares nothing itself), so an
"expected passing = 0" against a file whose Task 1 tests all pass reads as exactly that
disagreement and stops the dispatch. **The integer for `--expect-pass` is derived, not written
here**: it is the `passed` figure of Task 1's own GREEN pytest summary over this file, which the
implementer holds when this dispatch is assembled. That is a value with one concrete source at the
moment it is needed; writing an integer here instead would be a count over tests nobody has yet
written, and parametrised tests later in this document make such a count wrong rather than merely
stale. `--expect-fail` is **11**, the count derived from the AC list above (twelve distinct `test_` names less the one Task 4 forward reference).

**RED gate**: `hmad-dispatch run --timeout 600 -- python3.11 -m pytest tests/test_h_mad_doc_block_exec.py -q` before any production code — the **eleven** new tests fail with `AttributeError` and every Task 1 test still passes. Judge it on the pytest summary, never on `$?` alone, and keep the recorded output beside the task as the 5d dispatch's `--out` file; `rc=124` is the wrapper's expiry, not a RED result. This is what `h_mad_assemble_tdd.py --phase red` dispatches, with `--test-path` set to the file named above, `--expect-fail` and `--expect-pass` set to the counts this split states for a new-behaviour task and omitted for a wiring task (Tasks 1 and 5 state their RED in prose, as the assembler allows), `--out` the recorded report kept beside the task, and `--timeout 600`.

---

## Task 3: execution and bounding

**Production file**: `h-mad/scripts/h_mad_doc_block_exec.py`
**Test file**: `h-mad/tests/test_h_mad_doc_block_exec.py`
**Task shape**: `new-behaviour`

**Description**: `run_block(block, *, preamble=None, timeout=30.0)` calls the shared module-level
`_validate_timeout(timeout)` first thing (`float()` conversion, `math.isfinite`, `> 0`; else
`BadTimeout(value)` carrying the raw value — before `mkdtemp`, so nothing is created; the same
validator is `main`'s pre-reservation check in Task 4, so one mutation row,
`timeout-validation-removed`, covers both call sites); then `cwd = None`; inside a `try`: `cwd = tempfile.mkdtemp()`, `os.chmod(cwd, 0o700)`
(a failure of either records `LaunchFailed("mkdtemp", err)` as the pending outcome — for `chmod`
the cwd is set, so cleanup runs), composes the script as `preamble.rstrip("\n") + "\n" + block.text`
when `preamble` is given else `block.text`, and launches **one** `bash` with
`subprocess.Popen(["bash", "-euo", "pipefail", "-c", script] if block.shell == "strict" else ["bash", "-c", script], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", start_new_session=True)`
(the guard around the `Popen` call is `except (OSError, ValueError) as err`, and either records
`LaunchFailed("spawn", err)`). **`ValueError` is in that tuple because of a real payload, and the
payload is measured rather than reasoned about** (design must 2 / impl-plan audit v47 codex must 2,
round seventeen's shared decision 3b): on 3.11.8, `Popen(["bash", "-c", "true"])` returns rc 0 and
`Popen(["bash", "-c", "true\x00"])` raises `ValueError: embedded null byte`. A NUL is valid UTF-8,
so a document carrying one decodes strictly and reaches the spawn with no verdict path at all —
the helper would exit on a traceback carrying no `DOCBLOCK:` line, against the exit-code partition
in Conventions. **The stage label is not new**: `stage=<mkdtemp|spawn|reap|collect>` is already the
declared set and `spawn` already covers "the launch did not happen", so nothing about the verdict
grammar, the `VERDICT_TABLE` or the registry moves; the only thing that widens is which exception
class the existing guard catches (round seventeen, correction C3). Nothing was executed, because
the spawn never happened; the cwd was created, so cleanup runs as on any other `spawn` failure and
the block's directory is gone. **The class is "the runtime rejects the argument vector at spawn",
and its membership is stated exactly**: for an argv whose every element is a `str`, `ValueError`
is the only member CPython 3.11 raises — a non-`str` element would raise `TypeError`, and that is
unreachable here because every element of both argv forms is composed as a `str` literal or from
`block.text`/`_compose`, which are `str` by construction. `communicate(timeout=timeout)`; on
`TimeoutExpired`: `proc.poll()` **then** `os.killpg(proc.pid, signal.SIGKILL)` — `ProcessLookupError`
means already reaped; any other `OSError` records `LaunchFailed("reap", err, pgid=proc.pid)`;
then a bounded drain `communicate(timeout=DRAIN_SECONDS)`, on whose own `TimeoutExpired` the helper
closes `proc.stdout`/`proc.stderr` itself and calls `proc.wait(timeout=DRAIN_SECONDS)` **only** if the group was
signalled or already gone (never on the `reap` branch) — **bounded, because a successful
`killpg` is a signal delivered, not a completion deadline**: a leader in uninterruptible sleep
exits when the kernel lets it, so this normally returns at once but is not guaranteed to
(design v1.73, design audit v66). On that `wait`'s own `TimeoutExpired` the pending outcome
becomes `LaunchFailed("reap", err, pgid=proc.pid)` where `err` is that `TimeoutExpired` — the group was signalled
and did not go, the same diagnostic-not-containment policy as an unsignalable group — ranked as
every `reap` is, with the pending `BlockTimeout` (or `collect`) as its `__context__`; the post-kill drain — finished or timed out
— **records nothing of its own**: the `BlockTimeout(timeout)` recorded on entry to the handler (see
the ordering note below) simply survives it, unless one of the precedence rules below has already
replaced it with a `LaunchFailed` at the `reap` or `collect` stage (design v1.61 §Execution,
as amended by v1.71).

**The helper's own I/O on the child is mapped by the same taxonomy** (design v1.65 §Execution,
design audit v62). The first `communicate(timeout=timeout)` is guarded by `except OSError as err`
beside its `except subprocess.TimeoutExpired`: the guard records
`LaunchFailed("collect", err, pgid=proc.pid)` as the pending outcome and then runs **the same
sequence the timeout path runs** — `proc.poll()`, `os.killpg(proc.pid, signal.SIGKILL)` with
`ProcessLookupError` meaning already reaped, the bounded drain `communicate(timeout=DRAIN_SECONDS)`,
and on that drain's `TimeoutExpired` the pipe closes plus `proc.wait(timeout=DRAIN_SECONDS)` **iff** the group was
signalled or already gone. **The two guards on that one `wait` call are separate `except`
clauses** — `except OSError` (rule (c) below) and `except subprocess.TimeoutExpired` (the
bounded-wait outcome above) — never merged into one `except (OSError, TimeoutExpired)`, so that
`drain-oserror-unmapped` and `wait-expiry-unmapped` each remove exactly one clause and each is
killed by exactly one test. **The pre-kill `proc.poll()` carries its own `except OSError` guard**
(design v1.71, impl-plan audit v16): the failure records the `collect` outcome and **the kill still
proceeds**, now without the reaped-zombie knowledge `poll()` would have supplied — so a
`PermissionError` from `killpg` on a zombie-only group is then the `reap` stage, replacing that
`collect` with the `collect` error as its `__context__`, while `ProcessLookupError` still means
already-reaped.

**Ordering derived from the precedence rules, not stated separately by the design**: the
`TimeoutExpired` handler records `pending = BlockTimeout(timeout)` **on entry**, before `poll()`,
rather than at the end of the drain. The design's rule that a `poll()`/close/`wait` failure
"replaces the pending `BlockTimeout`" is only satisfiable if that object already exists when the
failure happens; recording it at the end would leave `__context__` as `None` and
`test_poll_oserror_is_launch_failed_collect` would fail on it. This changes no precedence and no
verdict — an untroubled timeout path still raises the same `BlockTimeout` — only the moment the
object comes into being.

Four precedence rules govern what those later steps may do to the
pending outcome, and each `__context__` below is **assigned explicitly** (`err.__context__ = pending`),
because nothing is ever raised inside the handler and Python's implicit chaining therefore never
fires:
(a) an `OSError` from any later step under a pending `collect` is attached as that pending error's
`__context__` and does **not** replace it;
(b) a non-`ESRCH` `killpg` error is the `reap` stage and **replaces** the pending `collect`, the
`collect` error becoming the new `LaunchFailed("reap", err, pgid=proc.pid)`'s `__context__`;
(c) under an **ordinary** timeout, an `OSError` from the pre-kill `proc.poll()`, from the drain
`communicate`, from either pipe
close, or from `proc.wait(timeout=DRAIN_SECONDS)` **replaces** the pending `BlockTimeout(timeout)` with
`LaunchFailed("collect", err, pgid=proc.pid)` whose `__context__` is that `BlockTimeout`;
(d) rule (b) applies **after** a failed `poll()` exactly as it does otherwise — the kill is still
attempted, so a zombie-only group's `PermissionError` becomes `reap` and takes the just-recorded
`collect` as its `__context__`.
`stage=collect` ranks with `stage=reap` in the precedence (both exit 2, one rank, below
`CleanupFailed`), so cleanup and the read-back still run as usual and a removal that fails is still
`CleanupFailed` with the `LaunchFailed` as `__cause__`. Nothing raises
inside the handler; the pending outcome is raised only by the selection after the `finally`. The `finally`
runs `shutil.rmtree(cwd)` (no `ignore_errors`) when `cwd is not None`, recording an `OSError` as
`cleanup_error` and never raising. **After** the `try`/`finally`, select: if `cwd is not None` and
(`cleanup_error is not None` or `os.path.lexists(cwd)`) → raise `CleanupFailed(cwd, cleanup_error)`
chained **by an explicit two-branch selection**, `raise err from pending` when `pending is not
None` and `raise err from cleanup_error` otherwise; elif `pending is not None` → raise it; else return
`RunResult(rc=proc.returncode, stdout=stdout, stderr=stderr, shell=block.shell)`. `run_block` never substitutes.
**The two branches are written out because the one-line form does not do what it reads as** (design
must 5 / impl-plan audit v47 codex must 5, round seventeen's shared decision 3g). Earlier text here
said `from pending` alone, "so `__cause__` is the pending error when there is one, else
`cleanup_error`". Measured on 3.11.8: `raise RuntimeError() from None` inside an `except` block
leaves `__cause__` **None** and sets `__suppress_context__` **True**, so with `pending is None`
the one-line form does not fall back to the cleanup error — it **suppresses** the implicit context
that would otherwise have carried it, and the diagnostic the sentence promised is the one thing it
destroys. A `raise ... from` clause takes the VALUE of the expression after `from`; there is no fallback
semantics anywhere in that syntax, so the fallback has to be written as a branch. `test_cleanup_failure_after_successful_run_is_chained`
below is the pin on the `pending is None` branch and
`test_cleanup_failure_outranks_timeout_injected` is the pin on the other. **The selection DOES
carry a mutation row, `cleanup-chain-selection-flipped`, written in this task's row list below**
(round seventeen; the row is the round's answer to this document having flagged the axis as
unguarded). An earlier draft of v1.53 declined the row on the tab-arm bullet's ground — that the
row list is the design's matrix and adding a member would put this document one above it — and the
round resolved it the other way: the matrix moved to **85** at round seventeen and the design owed
the row, which is the correct direction whenever the guard is real and the only obstacle is a count.
**Round eighteen took the same direction a second time, and this time the design moved first**: it
added `intersect-scan-non-overlapping` in its r18 revision, taking the matrix to **86**, and this
document mirrors that row in Task 2 rather than declining it. The tab-arm
bullet's ground still stands for its own case, where no guard is missing and the fixture is the
whole of what is wanted.

**Code structure**:
```python
# raises BadTimeout, BlockTimeout, CleanupFailed, LaunchFailed — defined in Task 1
# __all__ += ["RunResult", "run_block"]
@dataclass(frozen=True)
class RunResult:     # lands here, beside run_block (design §Implementation Order, Task 3)
    rc: int
    stdout: str
    stderr: str
    shell: str

def _validate_timeout(value: object) -> float:
    """Shared by run_block (first thing) and main (before _reserve): float(value),
    math.isfinite, > 0; else BadTimeout(value) carrying the raw value."""

def _compose(preamble: str | None, text: str) -> str: ...
def run_block(block: Block, *, preamble: str | None = None, timeout: float = 30.0) -> RunResult: ...
```

**Acceptance Criteria** (every test here calls `dbe.run_block` in-process at the API — none goes
through the CLI; the thirteen that inject a fault are marked `(in-process, injected: ` + the seam`)` so the
transport split in the Conventions is visible per test — nine of the thirteen patch one of the eight
module-level seams, and four use the instance-level `Popen` wrapper the Conventions describe: the
three `stage=collect` tests and `test_wait_after_kill_is_bounded`. **The seam AXIS is unmoved by the ninth seam and the TEST axis is not, and the two are counted
separately because conflating them is how the twelve went stale**: `os.lstat` is patched only by
Task 4's `test_rollback_skips_unlink_on_identity_mismatch` and no Task 3 test touches it, so no
Task 3 test changes which seam it uses; but v1.53 ADDS an injected test to this task —
`test_cleanup_failure_after_successful_run_is_chained`, on the existing `shutil.rmtree` seam — so
the injected population goes 12 to **13**, the module-seam side 8 to **9**, the `real_rmtree` side
5 to **6**, and the `Popen`-wrapper side stays at **4**. 9 + 4 = 13. **Every test that patches
`dbe.shutil.rmtree` binds `real_rmtree = shutil.rmtree` BEFORE `monkeypatch.setattr(dbe.shutil, "rmtree", fake)`**
— `dbe.shutil` is the process-global module, so without the binding the teardown would call the
fake — **and removes a retained cwd with `real_rmtree(cwd)` in its `finally`**, the same pattern
as AC-4.6's `real_killpg`; the six such tests are named with `real_rmtree` below):
- [ ] AC-3.1 `test_block_runs_in_the_temp_cwd`: a `pwd` block reports a directory that is neither the repo root nor the document's directory and is gone afterwards.
- [ ] AC-3.2 `test_block_leaves_the_working_tree_untouched`: a block that creates a file leaves `git status --porcelain` byte-identical.
- [ ] AC-3.3 `test_unset_variable_fails_under_strict`: `echo $UNSET_X` → rc ≠ 0 strict, rc 0 plain.
- [ ] AC-3.4 `test_bare_exit_in_plain_mode_returns_rc`: `exit 3` under `shell=plain` → `rc == 3`, and the test process is alive.
- [ ] AC-3.5 `test_pipefail_strict_vs_plain`: `false | true` → rc ≠ 0 strict, 0 plain.
- [ ] AC-3.6 `test_streams_are_separate_str`: stdout/stderr unmerged; `é` round-trips; `printf '\xff'` yields U+FFFD.
- [ ] AC-3.11 `test_preamble_binds_a_variable_and_leaves_text_unchanged`; `test_preamble_and_substitution_compose` (preamble + a substituted key: the executed text carries the value); `test_preamble_without_trailing_newline_still_precedes_the_block`.
- [ ] AC-3.12 `test_failing_preamble_is_visible_as_the_combined_rc`: preamble `false` under strict → rc ≠ 0 and its stderr.
- [ ] AC-3.13 `test_cwd_mode_is_0700_under_hostile_umask`: with `os.umask(0o777)` around the call (restored in `finally`), a block running `stat -f %Lp .` (darwin) / `stat -c %a .` (GNU) prints `700`; `test_chmod_failure_is_a_verdict_and_removes_the_cwd` (in-process, injected: `os.chmod` injected to raise → `LaunchFailed("mkdtemp")` and the created directory is gone); `test_chmod_rollback_failure_is_cleanup_failed` (in-process, injected: `os.chmod` and `shutil.rmtree` both injected → `CleanupFailed` whose `__cause__` is the `LaunchFailed`; `real_rmtree` bound before the patch removes the retained cwd in `finally`); `test_no_mktemp_invocation_in_source`.
- [ ] AC-3.14 `test_cleanup_failure_is_reported` (`mkdir keep && chmod 000 keep` → `CleanupFailed` with `cleanup_error` a `PermissionError`; skipped when `euid == 0`; the test `chmod 700`s and removes the tree in its `finally`); `test_cleanup_failure_carries_the_os_error` (in-process, injected: `rmtree` injected to raise; `real_rmtree` bound before the patch removes the retained cwd in `finally`); `test_cleanup_readback_catches_silent_retention` (in-process, injected: `rmtree` injected as a no-op; `real_rmtree` bound before the patch removes the retained cwd in `finally`); `test_cleanup_error_after_successful_removal_is_still_a_failure` (in-process, injected: the fake calls `real_rmtree` — bound before the patch — then raises; `finally` calls `real_rmtree` under `ignore_errors=True` since the tree is already gone); `test_cleanup_failure_outranks_timeout_injected` (in-process, injected: `rmtree` raising under `sleep 300`, `timeout=1` → `CleanupFailed`, `__cause__` is the `BlockTimeout`, `cleanup_error` is the injected error, cwd read back present, removed in `finally` by `real_rmtree`, bound before the patch); `test_cleanup_failure_outranks_timeout` (real `chmod 000` fixture, skipped under root); `test_normal_run_reads_back_absent`; `test_cleanup_failure_after_successful_run_is_chained` (in-process, injected: `rmtree` injected to raise on a block that would otherwise `RAN` — `echo hi`, default `timeout`, so `pending is None` at the selection; `real_rmtree` bound before the patch removes the retained cwd in `finally`). **Its assertion is on `__cause__` IDENTITY, and that is the whole of what it adds**: the raised `CleanupFailed`'s `__cause__` **is** the injected cleanup error, asserted with `is`. **It asserts nothing about `__suppress_context__`, and the earlier `__suppress_context__ is False` clause is WITHDRAWN because it rejected the implementation this document prescribes** (round-eighteen sheet FACT 4 c / C2 iii; codex impl-plan must 1 at v48, premise probed rather than reasoned). Measured on 3.11.8: an explicit `raise err from ce` inside an `except` block sets `__cause__` to `ce` AND `__suppress_context__` to **True** — explicit chaining always suppresses the implicit context, whatever the `from` expression is — so an AC demanding False could never pass against `raise err from cleanup_error`. Cause identity is the property that actually discriminates the defect: under the collapsed selection `__cause__` is `None`, and under the correct branch it is the cleanup error. `test_cleanup_failure_carries_the_os_error` beside it asserts the `cleanup_error` **field** and would stay green under the defect this one exists to catch, which is why the two are separate tests on one seam rather than one test with two assertions.
- [ ] AC-4.6 `test_mkdtemp_failure_is_a_verdict` (in-process, injected: `tempfile.mkdtemp` injected → `LaunchFailed("mkdtemp")`, nothing to clean); `test_spawn_failure_is_a_verdict` (`PATH` = empty dir → `LaunchFailed("spawn")`, cwd gone); `test_nul_in_document_block_is_a_launch_failure` (no injection: a block whose text contains `\x00` → `LaunchFailed` with `stage == "spawn"` and `err` a `ValueError`, no `RunResult` returned, no traceback, and the block's cwd gone — read through a recording `Popen` pass-through's `cwd` keyword, which also asserts the child was never spawned because the pass-through's real `Popen` raised before returning an instance); `test_nul_in_preamble_is_a_launch_failure` (the same assertions with the `\x00` in the `preamble=` argument instead, so `_compose` is what carries it into the argv — the two tests pin the two composition paths separately, and neither is a parametrisation of the other because only the second exercises `_compose`); `test_reap_failure_is_a_verdict_within_the_drain_bound` (in-process, injected: `os.killpg`): `real_killpg = os.killpg` bound **before** `monkeypatch.setattr(dbe.os, "killpg", fake)`; `fake` records the pgid and raises `PermissionError`; `Popen` wrapped in a recording pass-through; `sleep 300` under `timeout=1` → `LaunchFailed("reap", pgid=proc.pid)` raised within `1 + 2 * DRAIN_SECONDS + 2` s; teardown in `finally`: `real_killpg(pgid, signal.SIGKILL)`, `recorded.wait()`, then assert `real_killpg(pgid, 0)` raises `ProcessLookupError`.
- [ ] AC-4.6 `test_communicate_oserror_is_launch_failed_collect` (in-process, injected: the recorded `Popen` instance's bound `communicate`): the test binds `real_killpg = os.killpg` **before** anything is patched, then installs the recording `Popen` pass-through with `monkeypatch.setattr(dbe.subprocess, "Popen", recording_popen)`, where `recording_popen` calls the real `subprocess.Popen`, appends the instance to a list the test holds, shadows `inst.communicate` with a wrapper that raises `OSError(errno.EIO, "Input/output error")` on its **first** call and delegates to the saved bound method afterwards, and returns the instance (the wrap happens inside the pass-through because `run_block` calls `communicate` immediately after `Popen` returns; the test file imports `errno`). Under a block that would otherwise `RAN` (`echo hi`, default `timeout`), `dbe.run_block` raises `LaunchFailed` with `stage == "collect"`, `err.errno == errno.EIO`, `pgid == recorded.pid` and no `RunResult` returned; the cwd — read from the pass-through's recorded `cwd` keyword argument — is gone; and the group is gone — `real_killpg(pgid, 0)` raises `ProcessLookupError`, because the helper killed and reaped the child as a timed-out one — which is the test's last substantive assertion, with a `finally` that sends `real_killpg(pgid, signal.SIGKILL)` ignoring `ProcessLookupError` so a surviving group is never left behind when the assertion fails.
- [ ] AC-4.6 `test_drain_wait_oserror_is_launch_failed_collect` (in-process, injected: the recorded `Popen` instance's bound `wait`): the same pass-through, wrapping `inst.wait` instead — first call raises `OSError(errno.EIO, "Input/output error")`, later calls delegate, so the teardown's own `recorded.wait()` passes through. The **escapee fixture is required, not optional**: `Popen.communicate()` calls `self.wait()` internally after a successful read, so under a plain `sleep 300` the wrapper would fire from inside the drain rather than from the helper's own `proc.wait(timeout=DRAIN_SECONDS)`. The block is AC-5.5's `python3 ESC_PATH PID_PATH & sleep 300` with `esc.py` and the pid path delivered through the substitution map, run at `timeout=1`: the leader is signalled, the `os.setsid()` escapee holds the pipes, the drain `communicate(timeout=DRAIN_SECONDS)` raises `TimeoutExpired` before reaching its internal wait, the helper closes both pipes and calls `proc.wait(timeout=DRAIN_SECONDS)` on the signalled branch, and that call trips the wrapper — precedence rule (c). The raised error is a `LaunchFailed` with `stage == "collect"`, `pgid == recorded.pid`, and `__context__` an instance of `dbe.BlockTimeout`, returned within `1 + 2 * DRAIN_SECONDS + 2` s wall time, with the block's cwd gone; in `finally` the test reads the pid file, sends `os.kill(pid, signal.SIGKILL)` ignoring `ProcessLookupError`, then calls `recorded.wait()`.
- [ ] AC-4.6 `test_poll_oserror_is_launch_failed_collect` (in-process, injected: the recorded `Popen` instance's bound `poll`): the same recording pass-through and the same `_raise_once` shape, wrapping `inst.poll` instead — first call raises `OSError(errno.ECHILD, "No child processes")`, later calls delegate. The wrapper intercepts exactly the helper's one call, because `Popen`'s own internals use `_internal_poll` and never `self.poll()`. Under `sleep 300` at `timeout=1` the first `communicate` raises `TimeoutExpired`, the handler records the pending `BlockTimeout`, and the guarded `poll()` then raises: the pending outcome becomes `LaunchFailed` with `stage == "collect"`, `pgid == recorded.pid` and `__context__` an instance of `dbe.BlockTimeout` (precedence rule (c)); the kill proceeds and the block's cwd is gone. **Teardown matters more here than in the other two `collect` tests**, because `poll-oserror-unmapped` leaves the group unkilled: `finally` sends `real_killpg(pgid, signal.SIGKILL)` ignoring `ProcessLookupError`, then `recorded.wait()` to reap the leader, and only then asserts `real_killpg(pgid, 0)` raises `ProcessLookupError` — the same order as the AC-4.6 reap test.
- [ ] AC-5.1 `test_sleeping_block_times_out`: `sleep 300`, `timeout=1` → `BlockTimeout` (whose CLI half prints `TIMEOUT seconds="1.0"`, quoted) within `1 + 2 * DRAIN_SECONDS + 2` s.
- [ ] AC-5.2 `test_in_group_descendant_is_reaped`: block text `sleep 300 & echo $! > PID_PATH; sleep 300`, run as `dbe.run_block(dbe.substitute(block, {"PID_PATH": str(pid_file)})[0], timeout=1)` where `pid_file` is under the test's `tmp_path` — the substitution map is how the absolute path reaches the block, because the child's cwd is a fresh private directory nothing can be placed in beforehand → after the timeout the pid read from `pid_file` is gone: `os.kill(pid, 0)` raises `ProcessLookupError`; `finally` reads the pid file if present and sends `os.kill(pid, signal.SIGKILL)` ignoring `ProcessLookupError`.
- [ ] AC-5.3 `test_no_timeout_invocation_in_source`: no argv token or shell command word `timeout`/`gtimeout` in the module source (a substring match on `timeout=`/`TimeoutExpired`/`BlockTimeout`/`--shell-timeout` must not trip it).
- [ ] AC-5.4 `test_temp_cwd_removed_after_timeout`.
- [ ] AC-5.5 both escapee tests share one fixture construction: the test writes `esc.py` under its own `tmp_path` (`os.setsid()`; write `os.getpid()` to the PID path given as `sys.argv[1]`; `time.sleep(300)` holding stdout) and passes BOTH absolute paths through the substitution map — `dbe.run_block(dbe.substitute(block, {"ESC_PATH": str(esc), "PID_PATH": str(pid_file)})[0], timeout=1)` — because the child's cwd is a fresh private directory, so `esc.py` cannot be placed there and only the substituted absolute paths make the block executable. `test_timeout_survives_a_group_that_already_emptied`: block text `python3 ESC_PATH PID_PATH & exit 0` (the leader exits at once; the group is empty when `killpg` runs) → `BlockTimeout`, no traceback, and the block's cwd is gone. `test_timeout_drain_is_bounded_against_an_escapee`: block text `python3 ESC_PATH PID_PATH & sleep 300` → `BlockTimeout` within `1 + 2 * DRAIN_SECONDS + 2` s wall time, cwd gone. Teardown for those two, in `finally`: read the pid file, `os.kill(pid, signal.SIGKILL)` ignoring `ProcessLookupError`, then assert the block's cwd (captured through a recording `Popen` pass-through's `cwd` kwarg) no longer exists. `test_wait_after_kill_is_bounded` (in-process, injected: the recorded `Popen` instance's bound `wait`, the record-and-raise variant): it uses the **same escapee fixture and for the same reason** as `test_drain_wait_oserror_is_launch_failed_collect` — `Popen.communicate()` calls `self.wait()` internally after a successful read, so only an escapee holding the pipes makes the drain expire and lets the helper's own `proc.wait(timeout=DRAIN_SECONDS)` be the call the wrapper sees. Block text `python3 ESC_PATH PID_PATH & sleep 300` at `timeout=1`; the wrapper records the `timeout` keyword it was passed and raises
`subprocess.TimeoutExpired(cmd=["bash"], timeout=dbe.DRAIN_SECONDS)` — **both arguments are
required**: `TimeoutExpired.__init__` is `(cmd, timeout, output=None, stderr=None)` and a
zero-argument construction raises `TypeError` instead of the timeout the test means to simulate
(measured on the pinned interpreter, 3.11.8). Asserts the recorded keyword `== dbe.DRAIN_SECONDS` (**the keyword is what proves the intercepted call was the helper's** — `communicate`'s internal wait passes none, and under `wait-unbounded` the recorder sees `None`), a `LaunchFailed` with `stage == "reap"`, `pgid == recorded.pid` and `__context__` an instance of `dbe.BlockTimeout`, the block's cwd gone, and a return within `1 + 2 * DRAIN_SECONDS + 2` s. Teardown in `finally`: read the pid file and `os.kill(pid, signal.SIGKILL)` ignoring `ProcessLookupError`, then `real_killpg(pgid, signal.SIGKILL)` ignoring `ProcessLookupError` and `recorded.wait()`, since the helper's own wait was made to expire and the real group is still the test's to reap.
- [ ] AC-5.6 `test_nonpositive_timeout_refuses_before_spawn`: `timeout=0`, `-1`, `math.nan`, `math.inf` → `BadTimeout` and the recording `Popen` pass-through was never called and no directory was created.

**Mutation rows added here**: `strict-flags-dropped`, `preamble-separator-dropped`,
`preamble-composed-with-unsubstituted-text`, `cwd-not-passed`, `chmod-0700-removed`,
`cleanup-errors-ignored`, `cleanup-readback-removed`, `precedence-timeout-raised-in-handler`,
`launch-oserror-unwrapped`, `killpg-replaced-by-kill`, `poll-before-killpg-removed`,
`killpg-esrch-uncaught`, `wait-unbounded` (the `timeout=` keyword dropped from the post-kill
`proc.wait`, so a signalled leader that does not exit holds the helper open past
`timeout + 2 * DRAIN_SECONDS`; the wrapped `wait` records `timeout=None` and the test fails on
that keyword), `wait-expiry-unmapped` (the `except subprocess.TimeoutExpired` around that same
`wait` removed, so the expiry escapes as a traceback instead of `LAUNCH_FAILED stage=reap`) —
both bound to `tests/test_h_mad_doc_block_exec.py::test_wait_after_kill_is_bounded`, and each
removing exactly one of the two separate `except` clauses on that call,
`drain-unbounded`, `timeout-validation-removed`,
`chmod-failure-unwrapped`, `chmod-rollback-unguarded`, `cleanup-error-ignored-when-tree-gone`,
`timeout-invocation-planted`, `mktemp-invocation-planted` (`tempfile.mkdtemp()` replaced by
`subprocess.run(["mktemp", "-d"], capture_output=True, text=True).stdout.strip()` — valid Python and
exactly the forbidden invocation; killed by `test_no_mktemp_invocation_in_source`). **Both
source-scan rows run in the green-on-real direction** (design v1.87): the real helper never
invokes `timeout`/`gtimeout` or `mktemp`, so `test_no_timeout_invocation_in_source` and
`test_no_mktemp_invocation_in_source` **pass against the landed source** and go RED only once the
mutant plants the forbidden invocation. They are the two tests in this task that pass at RED as
regression guards, which is the same fact stated from the other end,
`collect-oserror-unmapped` (the `except OSError` around the first `communicate(timeout)` removed, so
a pipe-read failure escapes as a traceback with the child unreaped; killed by
`tests/test_h_mad_doc_block_exec.py::test_communicate_oserror_is_launch_failed_collect`),
`drain-oserror-unmapped` (the guard around the post-kill drain, the two pipe closes and the `wait()`
removed, so a failure there escapes past the pending `BlockTimeout`; killed by
`tests/test_h_mad_doc_block_exec.py::test_drain_wait_oserror_is_launch_failed_collect`),
`poll-oserror-unmapped` (the guard around the pre-kill `proc.poll()` removed, so a `waitpid`
failure escapes as a traceback with the group unkilled; killed by
`tests/test_h_mad_doc_block_exec.py::test_poll_oserror_is_launch_failed_collect`),
`spawn-valueerror-unmapped` (`ValueError` dropped from the spawn guard's exception tuple, `OSError`
left in place, so a NUL in the composed script escapes as a traceback carrying no `DOCBLOCK:` line;
killed by `tests/test_h_mad_doc_block_exec.py::test_nul_in_document_block_is_a_launch_failure`,
with `test_nul_in_preamble_is_a_launch_failure` the regression test on the same guard through the
other composition path — **a member of the five-row `doc_block_exec.json` population whose mutant
reds a second named test, enumerated in the Conventions bullet**. **The bare ordinal it carried
through v1.53 is dropped rather than given a base** (impl-plan audit v48 teammate should 1): it read
"the third row in this document", and the two available bases disagree — in DOCUMENT order it is the
second, because `duplicate-heading-takes-first` (Task 1) precedes it and the three Task 4 rows
follow, while in the Conventions bullet's enumeration order it is the third. This document's own
standard is that an ordinal carries its base; naming the population instead of ranking within it
satisfies that standard without inviting the same ambiguity back. **It is discriminated from `launch-oserror-unwrapped`
in both directions**: that row drops `OSError`, under which the empty-`PATH`
`test_spawn_failure_is_a_verdict` goes red while both NUL tests stay green, because what they raise
is a `ValueError`; and this row leaves `OSError` in place, so `test_spawn_failure_is_a_verdict`
stays green under it),
`cleanup-chain-selection-flipped` (the two-branch selection collapsed to `raise err from pending`
unconditionally, so a run that SUCCEEDS and whose cleanup then fails carries `__cause__ is None`
— the cleanup error suppressed rather than selected, which is the
exact defect the two branches exist to prevent. **`__suppress_context__` is deliberately NOT named as
a property of the mutant**: measured on 3.11.8, the CORRECT implementation's
`raise err from cleanup_error` sets it True as well, so it discriminates nothing, and listing it
beside the clause that does discriminate would invite a 5e implementer to assert the very property
AC-3.14 withdrew for that reason. Only `__cause__ is None` separates mutant from original. Killed by
`tests/test_h_mad_doc_block_exec.py::test_cleanup_failure_after_successful_run_is_chained`.
**It is isolated, and that is derived from what each neighbouring test asserts rather than
assumed**: `test_cleanup_failure_outranks_timeout_injected` runs with a pending `BlockTimeout`, so
under the mutant `from pending` still yields exactly the `__cause__` it asserts and it stays green;
`test_cleanup_failure_carries_the_os_error` asserts the `cleanup_error` FIELD, which the selection
does not touch, and stays green; and every other cleanup test asserts the verdict or the exit code
rather than the chain. So this row reds one named test and adds no member to the
collateral-red population enumerated in Conventions) — 26 rows.
The three `collect` rows discriminate mutually, each staying green under the other two: the poll
test's first `communicate` raises `TimeoutExpired` rather than an `OSError`, so
`collect-oserror-unmapped` does not touch it, and its drain returns promptly once the group is
killed, so `drain-oserror-unmapped` does not either; the communicate and drain tests never wrap
`poll`, so `poll-oserror-unmapped` leaves both green; `test_wait_after_kill_is_bounded` stays green
under all three `collect` rows (its first `communicate` raises `TimeoutExpired`, its `poll` is the
real one, and its `wait` raises `TimeoutExpired` rather than an `OSError`, so removing the
`except OSError` clause does not touch it), and the three `collect` tests stay green under
`wait-unbounded` and `wait-expiry-unmapped` because none of them asserts the `timeout` keyword and
none makes that `wait` expire; and under `drain-oserror-unmapped` the
communicate test's later steps raise nothing at all, because the child is already killed and reaped
by the time the drain runs.

**Dependencies on other tasks**: Task 1 (`Block`); Task 2 only for the two
compose-with-substitution tests, which call `substitute` first.

**Expected RED split — WHOLE-FILE totals** (decision 3h, as for Task 2). **Failing**: every test
this task adds except two. **Passing**: those two plus every test Tasks 1 and 2 landed in
`test_h_mad_doc_block_exec.py` — three regression-guard blocks, named as such, none of which this
task touches: Task 1's block, Task 2's ten, and this task's own
`test_no_timeout_invocation_in_source` and `test_no_mktemp_invocation_in_source`, which pass from
the first run because the source scan finds nothing in a module that does not yet spawn. **Expected
passing is therefore not 2 but 2 plus those two blocks**; the `--expect-pass` integer is the
`passed` figure of Task 2's GREEN summary over this file plus **2**, and `--expect-fail` is the
count of this task's AC list less those two.

**RED gate**: `hmad-dispatch run --timeout 600 -- python3.11 -m pytest tests/test_h_mad_doc_block_exec.py -q` before any production code — every Task 3 test fails except the two source-scan guards, which pass, and Tasks 1–2 stay green. Judge it on the pytest summary, never on `$?` alone, and keep the recorded output beside the task as the 5d dispatch's `--out` file; `rc=124` is the wrapper's expiry, not a RED result. This is what `h_mad_assemble_tdd.py --phase red` dispatches, with `--test-path` set to the file named above, `--expect-fail` and `--expect-pass` set to the counts this split states for a new-behaviour task and omitted for a wiring task (Tasks 1 and 5 state their RED in prose, as the assembler allows), `--out` the recorded report kept beside the task, and `--timeout 600`.

---

## Task 4: CLI, stream artifacts, and the registry entry

**Production file**: `h-mad/scripts/h_mad_doc_block_exec.py` and `h-mad/SKILL.md` (Helper-scripts registry entry)
**Test file**: `h-mad/tests/test_h_mad_doc_block_exec.py`
**Task shape**: `new-behaviour`

**Description**: `main(argv)` parses with
`argparse.ArgumentParser(allow_abbrev=False)` whose `error()` is overridden to
`raise BadArgs(message)` instead of exiting: an unknown option or a missing option value is a
**verdict**, `DOCBLOCK: BAD_ARGS message="<m>"` at exit 0, not argparse's usage text at exit 2,
because the Audit-gate signal discipline admits no non-`DOCBLOCK` exit and a malformed but readable
invocation is input the helper declined (design v1.85, plan audit v67). **`exit_on_error` is left at
argparse's default (`True`), and that is load-bearing, not an omission** (design v1.91, plan v1.84,
spec v1.53). `exit_on_error=False` — which this document specified through v1.32 — suppresses
argparse's own `except ArgumentError: self.error(str(err))` wrapper around `_parse_known_args`, so a
**missing option value** raises `argparse.ArgumentError` from inside the parse, never reaches the
`error()` override, and escapes `main` as a non-`DOCBLOCK` traceback — and a missing option value is
one of the two inputs `test_malformed_invocation_is_a_verdict` drives, so the setting would have
broken the very AC it was written to serve. Re-measured on the pinned 3.11.8, `error()` overridden,
all five grammar shapes: at the default, unknown option, missing value, missing required option,
missing positional and the rejected abbreviation **all** raise `BadArgs`; under `exit_on_error=False`
four of them do and the missing value escapes as `ArgumentError`. `--help` alone keeps
argparse's own exit-0 help (measured at the default with the override installed: `SystemExit(0)`,
help text on stdout — the override is never reached, because `--help` is not an error). The parser takes:
positional `doc`, `--heading` (required), `--index` (`type=str`), `--subst` (`action="append"`),
`--preamble-file`, `--shell-timeout` (`type=str`, default `"30"`), `--stdout`, `--stderr`; no
`--all`/`--dir`/glob argument exists. Order: `extract` → `select` (a non-integer `--index` is
`BadIndex(raw)`; parsed ints go to `select`) → build the map from `--subst` (split once on the
first `=`; no `=`, an **empty key**, or a repeated key are all refused **here, by `main`**, with
`raw` the argument exactly as given: `BadSubstArg(raw)` for the first two and
`BadSubstArg(raw, duplicate_key=k)` for the repeat. **`main` never delegates the empty key to
`substitute`** (design v1.77, design audit v69 agy): `substitute` keeps its own `BadSubstArg("")`
for an API caller that passes `{"": v}` directly, but `main` has already refused the raw argument
by then, so that path is unreachable from the CLI. The difference is observable, which is why it is
pinned: `--subst =V` must print `BAD_SUBST arg="=V"` — the raw argument, `=V`, inside the quotes — whereas delegating to
`substitute` would carry only the empty key and print `arg=`. One predicate, two places, one
mutation row each: `empty-key-accepted-by-api` for `substitute` and `cli-empty-key-delegated` for
`main`)
→ `substitute` → `_validate_timeout(args.shell_timeout)` (the shared validator from Task 3:
`float()` conversion, `math.isfinite`, `> 0`, else `BadTimeout(raw)` — **before** `_reserve`, so no
artifact exists for any input-only refusal; `run_block` re-validates the float it receives, and the
existing `timeout-validation-removed` row covers both call sites — no new row) → `--preamble-file`
read as strict UTF-8 (`OSError`/`UnicodeDecodeError` → `PreambleUnreadable`) → **reserve** stdout
then stderr → alias check → `run_block` → final writes.
Reservation, per path, is a two-arm loop bounded to three round trips: `os.open(path, os.O_WRONLY|os.O_APPEND|os.O_CREAT|os.O_EXCL, 0o644)`
(created=True) else on `FileExistsError` `os.open(path, os.O_WRONLY|os.O_APPEND|os.O_NONBLOCK)`
(created=False; `FileNotFoundError` here restarts the loop); the descriptor must `fstat` as
`S_ISREG` else it is closed and refused; the handle is `os.fdopen(fd, "a", encoding="utf-8")`. If the
second reservation fails, the first handle is closed and unlinked **only if** created. The whole
stage — both loops, the `fstat` checks, the rollback — is one `try/except OSError` mapped to
`StreamPathUnwritable`, raised **`from` that `OSError`** so it travels as `__cause__` rather than as
a constructor field; loop exhaustion maps there too, raised **with no cause** because no `OSError`
attended it (design v1.71 exception table).
**The rollback is verified, not assumed** (design v1.69, impl-plan audit v15). `created` is tracked
**per arm**, so the rollback only ever unlinks a path this call brought into existence. The rollback
itself is a `finally`-shaped step rather than a straight line: **close first, then unlink iff
`created`, each guarded on its own** so a failure of the close does not skip the unlink and a
failure of the unlink does not skip having closed. It is then followed by a read-back,
`os.path.lexists(created_path)`. **The rollback also refuses to delete what it did not create**
(design v1.85): before the unlink it compares `os.lstat(path)`'s `(st_dev, st_ino)` with the
identity `fstat` recorded on the reserved descriptor at creation, and on a **mismatch** it skips
the unlink and reports the path as `leftover:` — someone else's file stands there now, and the
inode this call created is already gone or renamed away. **That identity check IS a mutation-backed
guard, and this document previously exempted it** (design must 3 / impl-plan audit v47 codex must 3,
round seventeen's shared decision 3c). The earlier text called it "a policy constraint, not a
mutation-backed guard" carrying "no test by construction", on the ground that its mismatch branch
could not be reached without a ninth seam. The premise was true and the conclusion did not follow:
`invariants.base.md` §Test discrimination, which this document inlines into every audit of itself,
admits no such exemption, and the remedy the premise named — a ninth seam — is the ordinary
mechanism this document already uses eight times. So the **ninth module-level seam is `os.lstat`**
in the helper's namespace. It is genuinely a ninth and not a restatement of one of the eight: the
canonical list is `os.killpg`, `shutil.rmtree`, `tempfile.mkdtemp`, `os.chmod`, `os.unlink`,
`_final_write`, `_close_stream` plus the instance-level `Popen` wrapper, and `os.lstat` is none of
them. The guard's pin is `test_rollback_skips_unlink_on_identity_mismatch` and its row is
`rollback-identity-check-removed`, both written in Task 4's lists below. Where the identity matches,
the unlink proceeds and the read-back follows; if the file this call created is still on disk, the **same**
`stream_path_unwritable` verdict carries a `leftover:` detail line naming that path. The verdict
and the exit code do not change — only the detail line is added — so the no-new-artifact guarantee
is either true or reported as broken, never silently assumed. `StreamPathUnwritable` therefore
gains a constructor, `def __init__(self, leftover: str | None = None)`. **The signature is this
document's own decision**: the `leftover:` detail line is fixed by the verdict grammar above, and a
field on the exception is this document's only mechanism for carrying a detail line, exactly as
`LaunchFailed.pgid` and `StreamWriteFailed.written` already are — nothing is asserted here about
what any sibling does or does not fix. The
default keeps every other raise site a valid zero-argument construction, and `main` emits
`leftover:` only when the field is set. **`leftover:` is emitted on this rollback path only**: the
alias refusal also unlinks the files this call created, and that path is unchanged and grows no
read-back of its own (design v1.69 scopes the read-back to the failed second reservation). Alias: `os.fstat` on both handles,
equal `(st_dev, st_ino)` → unlink the files **this call created** and raise `StreamPathsAlias`;
the alias check does **not** close the handles itself — closing is the backstop `finally`'s job
through `_close_stream`, because a close inside the reservation's mapped region would turn an
injected close failure into `stream_path_unwritable`, while
`test_backstop_close_failure_does_not_outrank_a_refusal` asserts `stream_paths_alias` (design
v1.58, stream artifacts). The rollback when the SECOND reservation fails is unchanged: it still
closes and unlinks the first handle inside the region. Both handles are
held in a `try`/`finally` spanning the alias check, `run_block` and the final writes. On the `RAN`
path: for stdout then stderr, `_final_write(handle, text)` — `seek(0); truncate(); write(text); flush()`
inside a `try` whose `finally` calls `_close_stream(handle)`, the whole thing inside the mapped
region (first error wins; a close error is chained as `__context__`) — then **immediately** verify:
`Path(path).read_bytes() == text.encode("utf-8", errors="replace")`; a mismatch, missing file or
`OSError` on the read is `StreamWriteFailed(written, failed, skipped, verify=stream)`. A stdout
failure (write or verify) skips stderr: `failed: "stdout"` / `skipped: "stderr"`; a stderr failure
leaves stdout written: `written: "stdout"` / `failed: "stderr"`. The backstop `finally` calls
`_close_stream` on each handle not already closed under `except OSError`, recording the first
`(stream, error)` as `close_error` and never raising; after the `try`/`finally`, select: pending
exit-2 `DocBlockError` → raise it with `close_error` attached as `__context__`; else if
`close_error` → raise `StreamCloseFailed(stream, error)` `from pending` (pending is a
`BlockTimeout` or `None`), printed as `UNREADABLE reason=stream_close_failed` plus a `stream: "<name>"` line carrying the
stream name and an `os_error: "<text>"` line carrying the error text, both quoted, so the operator learns which stream's close failed; else the pending outcome / the result. `main` catches `DocBlockError`
and prints one `DOCBLOCK:` line per the verdict table plus detail lines, returning 0 or 2 per the
partition; it never lets a `DocBlockError` or an `OSError` of its own escape. The verdict mapping
is two module-level objects: `VERDICT_TABLE: dict[str, int]`, keyed by the **emitted line head at
full granularity** (23 heads: `RAN`, `NOT_FOUND`, `AMBIGUOUS`, `AMBIGUOUS_HEADING`, `BAD_INDEX`,
`BAD_TIMEOUT`, `BAD_ARGS`, `BAD_SUBST`, `SUBST_MISSING`, `SUBST_OVERLAP`, `BAD_INFO`, `TIMEOUT`,
`CLEANUP_FAILED`, `LAUNCH_FAILED stage=mkdtemp`, `LAUNCH_FAILED stage=spawn`,
`LAUNCH_FAILED stage=reap`, `LAUNCH_FAILED stage=collect`, `UNREADABLE reason=doc_unreadable`, `UNREADABLE reason=preamble_unreadable`,
`UNREADABLE reason=stream_paths_alias`, `UNREADABLE reason=stream_path_unwritable`,
`UNREADABLE reason=stream_write_failed`, `UNREADABLE reason=stream_close_failed`) → exit code, and
`_VERDICT_FOR: dict[type[DocBlockError], Callable[[DocBlockError], str]]`, mapping each exception
class to the function that renders its head (so `LaunchFailed` renders `stage=` from its `stage`
field and each `UNREADABLE` class its own `reason=`); `main` renders the head with `_VERDICT_FOR`,
looks the exit code up in `VERDICT_TABLE`, and appends the verdict's variable fields after the
head — the complete list, derived from the design's verdict table (one entry per variable slot in a
`DOCBLOCK:` line): `rc=`/`blocks=`/`shell=` (`RAN`), `blocks=` and `heading=` (`AMBIGUOUS`),
`count=` and `heading=` (`AMBIGUOUS_HEADING`), `index=` (`BAD_INDEX`), `value=` (`BAD_TIMEOUT`),
`arg=` (`BAD_SUBST`), `message=` (`BAD_ARGS`), `keys=` (`SUBST_MISSING`, `SUBST_OVERLAP`), `key=` (`BAD_INFO`), `seconds=`
(`TIMEOUT`), `path=` (`CLEANUP_FAILED`), `stage=` (`LAUNCH_FAILED`), `reason=` (`UNREADABLE`) —
15 field names. **Of this document's 27 rendering slots — those 15 head field names plus the 12
`DETAIL_KEYS` values — exactly 20 dynamic values are rendered through one module-level renderer,
`_field(value)`, and the other 7 are rendered bare by construction — **re-derived on the tree v1.54
ships from the `DETAIL_KEYS` tuple as this revision leaves it below rather than carried: 12 members
in the tuple, 15 distinct head field names, 15 + 12 = 27 slots; 8 quoted head fields + 12 quoted detail
values = 20 through the renderer; 27 - 20 = the 7 bare. **The `_field` DOCSTRING in the code-structure
block below said 19 through v1.53 and is corrected to 20 here** (impl-plan audit v48 teammate must 1):
that block is what a 5d implementer writes verbatim into `h-mad/scripts/h_mad_doc_block_exec.py` and
what 5e quotes as exact-once mutation `find` anchors, so a wrong cardinal there lands in shipped
source and in the anchors of `field-escape-removed`, `c1-escape-removed` and `field-quoting-removed`;
19 plus the 7 bare is 26, against this document's own 27 slots, so the two sites could not both be
true. The 12-member tuple and the `8 + 12 = 20` derivation were already right and are unchanged.** (design v1.75/v1.78/v1.80,
design audits v67, v70 and v72; impl-plan audit v23; the twelfth detail key `intersect:` and the
slot moves 26 → 27 / 19 → 20 that follow from it are round seventeen's decision 3a, correction C2
— the bare list does not grow, so every value the new detail line carries is quoted). The 7 bare ones are `rc`, `blocks`, `count`,
`keys`, `shell`, `stage` and `reason`: ints and enums the helper itself produces, never derived
from a caller argument or a document, so there is nothing in them to escape. **That exemption is
exhaustive** — no other field is bare, and no bare field passes through `_field`, which is what
makes the rule checkable in one direction each way. `_field(value)` is
`json.dumps(str(value), ensure_ascii=False)` — a **double-quoted JSON string, the quotes included
in the output**. **The `str(value)` is load-bearing and comes first**: `json.dumps(3)` on its own
emits a bare `3`, not `"3"`, so an `int` or `float` passed straight to `json.dumps` would come
out unquoted and silently leave the grammar (design v1.80, design audit v72). Stringifying first
is what makes `seconds="1.0"` and `pgid: "4242"` quoted like every other non-exempt field.
**`json.dumps` is not sufficient on its own, so `_field` makes a second pass** (design v1.82,
design audit v73). Measured on this interpreter: `json.dumps(s, ensure_ascii=False)` leaves
U+0085 (NEL), U+2028 (LINE SEPARATOR), U+2029 (PARAGRAPH SEPARATOR) and U+007F (DEL) **literal**
in its output, and `str.splitlines()` breaks on the first three — a heading carrying all four
split one `DOCBLOCK:` line into **four** pieces. So after `json.dumps`, `_field` rewrites every
remaining character whose `unicodedata.category(ch)` is `Cc`, `Zl` or `Zp` to its `\uXXXX`
escape; with that pass the same line splits into **one** piece (both figures measured
2026-09-03). `unicodedata` therefore returns to the module import line beside `json`. `"` and `\` are escaped, `\r`, `\n` and every other control character are
escaped, and everything else — spaces, `=`, non-ASCII — is verbatim inside the quotes.
**The 20 quoted slots, enumerated** (the seven bare ones are listed above and are not repeated):
the head fields `heading=`, `index=`, `value=`, `arg=`, `message=`, `key=`, `seconds=`, `path=` — 8 — and every one
of the 12 detail values — `missing_key:`, `overlap:`, `intersect:`, `duplicate_key:`, `os_error:`, `pgid:`,
`written:`, `failed:`, `skipped:`, `verify:`, `stream:`, `leftover:`. 8 + 12 = 20 and 7 + 20 = 27, the slot count
this section derives. `seconds=` and `pgid:` are helper-produced numbers, and impl-plan v1.22 left
open whether they should be bare; design v1.79 **settled** it by making the bare list exhaustive,
so both are quoted and no exemption is pending.
**This document's own constraint**, re-derived at `35698f9`, with the corresponding design rows
reached **by name, never by line and never by a claim about their content**, under the Conventions
rule above. The `BAD_INFO` head is `BAD_INFO key="<k>"`, **quoted**: `key=` is the offending
info-string token — document-controlled — and is not among the seven exempt fields; the design's
verdict-table row is located with
``grep -n '^| `DOCBLOCK: BAD_INFO key=' docs/02-design/features/doc-block-exec.design.md``
(one hit, verified at `700c599`). The `SUBST_OVERLAP` detail line is `overlap: "<a>" "<b>"` with **both** halves
quoted, because both elements are caller keys; **its sibling under the same head is
`intersect: "<a>" "<b>" "<offset>"`, with all THREE quoted** — the two keys because they are
caller keys, the offset because spec FR-4 quotes every detail-line value and the exempt-bare list
governs the `DOCBLOCK:` line only (round seventeen, correction C1; the same question was settled
for `pgid:`, a helper-produced number, at design v1.79). Its row is not located by a needle here,
because the design does not carry it yet at `fbc2ea0` and this round's decision is what puts it
there; that is stated as a debt in v1.53's entry, not as a reading of a sibling. The
`overlap:` row is located with
``grep -n '^| `DOCBLOCK: SUBST_OVERLAP keys=' docs/02-design/features/doc-block-exec.design.md``
(one hit, verified at `700c599`). Impl-plan v1.24 flagged those two rows as bare and half-quoted and **design
v1.81 answered it** — located with
``grep -n 'both halves of `overlap:`' docs/02-design/features/doc-block-exec.design.md``
(one hit, verified at `700c599`) — so the flags were withdrawn at v1.35. The three `design.md:` line numbers this paragraph carried
through v1.36 had all drifted by `a8e0372`; they are dropped rather than re-pinned, which is the
Conventions rule, not a one-off repair. **All three needles were widened at v1.40 after the bare
phrase `both halves of` went from one hit to two inside a single commit** — the design's round-four
revision added a second sentence using the same English words — so each of the three now carries a
backticked identifier or an anchored table-row prefix, and each was re-run at the commit this
revision ships against. See the Conventions locator rule for the general form.
**The line grammar is therefore** `DOCBLOCK: <VERDICT> (<key>=<bare>|<key>="<json-string>")*`, and
a consumer that splits on it recovers every field. Two attacks are closed, not one. A `--heading`
of `"x\nDOCBLOCK: RAN rc=0 blocks=1 shell=strict"` cannot start a second line — the newline is
escaped inside the quotes — and a `--heading` of `x rc=0` cannot forge a **field token** either:
it renders as `heading="x rc=0"`, one quoted value, never a bare ` rc=0` on a refusal line, which
is what AC-4.3 promises (plan audit v61: control-character escaping alone left that forgeable). `_field` is **private**: it is not in
`__all__` (29 names, `BadArgs` included), it is not a `VERDICT_TABLE` head or a `DETAIL_KEYS` entry, so
AC-4.5's registry walk does not see it and `h-mad/SKILL.md` gains no row for it. The emittable detail keys are a module-level tuple `DETAIL_KEYS`, so tests can
enumerate all twelve. **`intersect:` is the twelfth and it joins in Task 2, while the registry row
that AC-4.5 requires for it lands in Task 4 with the rest of the `h-mad/SKILL.md` entry** — the
same split every other detail key already has, since `DETAIL_KEYS` is written in Task 4's code
block above and AC-4.5's bidirectional walk is a Task 4 AC. Nothing edits `h-mad/SKILL.md` before
Task 4, so the row is written from the landed source at 5d/5e and no anchor is invented here. `StreamWriteFailed`'s `written`/`skipped` lists are joined with a space
before printing and then rendered through `_field` as one quoted value (`written: "stdout"`, or
`written: "stdout stderr"` for two — never Python list syntax, and never bare).
The `h-mad/SKILL.md` Helper-scripts entry for `h_mad_doc_block_exec.py` states the CLI contract
and carries a table with one row per emittable line — every `DOCBLOCK:` token and every detail
key, `stream:` and `leftover:` included — each with a remedy, and each showing the value form the
line grammar produces (a bare int/enum for the seven helper-constrained fields, a double-quoted
JSON string everywhere else); because AC-4.5 matches **`VERDICT_TABLE` keys**, the
table carries one row per `LAUNCH_FAILED stage=` head, `LAUNCH_FAILED stage=collect` included, and a
row for the new `BAD_ARGS` head with its `message=` value form, not a
single generic row with a placeholder stage (design v1.65's verdict table shows the generic
spelling; the per-stage rows are what the impl-plan's head-granular table requires); the entry starts at the bullet ``- `h_mad_doc_block_exec.py` —`` and its
table rows are the lines beginning `| \`` up to the next `- ` bullet.
**The entry must contain no tagged opener** — no ` ```bash hmad:exec ` line at column 0 through
column 3, in its prose or in its table: it documents the tag by naming it inline, never by example
(impl-plan audit v34). `h-mad/SKILL.md` is inside AC-6.1's sweep (a tracked `*.md` under `h-mad/`,
no `archive/` and no dot-directory component), so a tagged opener here
would make `test_exactly_one_tagged_fence_in_the_tree` count 2 at Task 5 GREEN and fail it; the one
tagged opener the tree is allowed is the Second-surface fence Task 5 tags.
**The entry is also subject to the two portable-timeout guards, and this is the other half of the
class AC-6.4 closes** (impl-plan audit v36). AC-6.4's half is *a file this feature ADDS enters a
glob*, which moves the collected count; this half is *a file this feature EDITS is **already** in
the glob*, which turns an existing node red with no count change at all, so AC-6.4 cannot see it.
**Class rule: any file this feature writes to that is a member of `_SCANNED` must satisfy
`_TIMEOUT_CMD` and `_ABSENCE_CLAIMS`.** `h-mad/tests/test_h_mad_portable_timeout.py:153` builds
`_SCANNED` and `:154` puts `SKILL / "SKILL.md"` in it, so
`test_no_document_or_script_emits_a_bare_timeout_command[SKILL.md]` and
`test_no_document_or_script_rests_on_an_unconditional_absence_claim[SKILL.md]` already exist and
already constrain any text this task adds there. **Residual, derived at `335f535` from
`_SCANNED`'s source list against this feature's own file list**: the feature touches two members
and they enter by different routes — `h-mad/SKILL.md`, which this task and Task 5 **edit**, and
`h-mad/scripts/h_mad_doc_block_exec.py`, which Task 1 **creates** and which becomes a member the
moment it lands under `scripts/*.py`. Naming only the edited one is what the verb *edits* used to
hide here (delta self-review r15); the guards the created member inherits, with the two node IDs
it collects, are stated in Task 5's bullet beginning **Why the two portable-timeout nodes are
members at all** and are pointed at rather than duplicated. `h-mad/tests/docsections.py`,
`h-mad/tests/test_*.py` and `h-mad/tests/mutation-specs/*.json` are all outside `_SCANNED` (it
reaches `SKILL.md`, `invariants.base.md`, `invariants.example.md`, `audit-prompt.template.md`,
`references/*.md`, `scripts/*.sh`, `scripts/*.py` and `hooks/*.sh`, and `tests/` is in none of
them), and the feature adds nothing under `references/*.md`, `hooks/*.sh` or `scripts/*.sh` —
the three exclusions written as globs, in the same grammar as the one inclusion beside them, so
the list cannot be read as exhaustive of the glob sources. **`_SCANNED`
is GLOB-FED, so this membership statement is a reading of a tree and not a property of a list**
(impl-plan audit v45). **The rule is over the set, and NO cardinal of the glob sources is
published here** (delta self-review r15): every `_SCANNED` source spelled with `.glob(` is a tree
read, so the sources partition into literal paths and tree reads by their own spelling, and which
files a tree read admits is settled by running it. v1.50 published a cardinal of the glob sources
here and it was wrong — the enumeration two lines above already named every glob form that
cardinal undercounted, so the sentence contradicted the list it sat beside — and the repair is
the removal of the count rather than a corrected integer, because the next `.glob(` entry a
reviser adds moves it again and nothing here would see that. **The retired figure is DESCRIBED
and not quoted**, for the reason the precheck forms are described rather than quoted one bullet
family over: quoting it would put the wrong cardinal back into the body this sentence claims
carries none, which is the defect and not a record of it. The wrong value and the reading that
retired it are in the v1.50 Version History entry, the value in that entry's original prose and
the reading in the bracketed correction appended to it at v1.51 — **stated as two places and not
one, because the bracket carries the reading alone** (impl-plan audit v46, second leg): diffing
that entry between `dfae038` and `af19d53` shows the bracket was appended at v1.51 carrying
`returns **4**` and the four glob forms, while the retired value sits in the entry's original
prose several hundred characters earlier, outside the bracket. A dated record is the right place
for a retired number; the wrong place to send a reader for it is a bracket that does not hold it. A later `references/*.md` or
`scripts/*.py` file changes the membership without any instrument here noticing — the same shape
AC-6.4's suite floor has, and the same disposition. **So membership is RE-DERIVED at 5d from the
shipped sources rather than read out of this sentence**, exactly as the parametrised collection
counts below are. The live risk
is the bare shell **command** form in a remedy sentence — the word `timeout` followed by
whitespace and a bare integer. `--timeout 60` is safe, because `_TIMEOUT_CMD`'s `[^-\w]` guard
excludes the leading `-`; the same two tokens without the dashes are not, and a `BAD_TIMEOUT` row
whose remedy column reaches for them fails the guard on `h-mad/SKILL.md` rather than on the new
module. **The same rule binds Task 5**, which retags the fence in the same file.

**Code structure**:
```python
# raises StreamPathUnwritable, StreamPathsAlias, PreambleUnreadable, StreamWriteFailed,
# StreamCloseFailed — defined in Task 1
# __all__ += ["main"]
VERDICT_TABLE: dict[str, int] = {          # emitted line head → exit code; 23 entries, listed in the description
    "RAN": 0, "NOT_FOUND": 0, "AMBIGUOUS": 0, "AMBIGUOUS_HEADING": 0, "BAD_INDEX": 0, "BAD_TIMEOUT": 0,
    "BAD_ARGS": 0,
    "BAD_SUBST": 0, "SUBST_MISSING": 0, "SUBST_OVERLAP": 0, "BAD_INFO": 0, "TIMEOUT": 0,
    "CLEANUP_FAILED": 2, "LAUNCH_FAILED stage=mkdtemp": 2, "LAUNCH_FAILED stage=spawn": 2, "LAUNCH_FAILED stage=reap": 2,
    "LAUNCH_FAILED stage=collect": 2,
    "UNREADABLE reason=doc_unreadable": 2, "UNREADABLE reason=preamble_unreadable": 2,
    "UNREADABLE reason=stream_paths_alias": 2, "UNREADABLE reason=stream_path_unwritable": 2,
    "UNREADABLE reason=stream_write_failed": 2, "UNREADABLE reason=stream_close_failed": 2,
}
_VERDICT_FOR: dict[type[DocBlockError], Callable[[DocBlockError], str]] = {...}   # class → head renderer (every DocBlockError subclass)
DETAIL_KEYS: tuple[str, ...] = ("missing_key:", "overlap:", "intersect:", "duplicate_key:",
                                "os_error:", "pgid:",
                                "written:", "failed:", "skipped:", "verify:", "stream:",
                                "leftover:")   # 12

def _field(value: object) -> str:
    """The ONE renderer the 20 dynamic values pass through (the 7 bare fields never reach it):
    json.dumps(str(value), ensure_ascii=False) — a DOUBLE-QUOTED JSON string. The quotes are
    part of the output. str() FIRST: json.dumps(3) emits a bare 3, so an int or float would
    otherwise leave the grammar unquoted (design v1.80). THEN a second pass: every remaining
    character with unicodedata.category(ch) in {"Cc", "Zl", "Zp"} becomes \\uXXXX, because
    json.dumps leaves U+0085, U+2028, U+2029 and U+007F literal and str.splitlines() breaks
    on the first three (design v1.82). `"` and `\\` are escaped, every control character (\\r and \\n included)
    is escaped, and everything else — spaces, `=`, non-ASCII — is verbatim INSIDE the quotes.
    ensure_ascii=False keeps non-ASCII readable rather than \\uNNNN-escaping it. Private —
    not exported, not a registry row (design v1.78, design audit v70)."""

def _reserve(path: str) -> tuple[io.TextIOWrapper, bool]:       # (handle, created)
def _final_write(handle: io.TextIOWrapper, text: str) -> None:  # seam: seek/truncate/write/flush, close in finally
def _close_stream(handle: io.TextIOWrapper) -> None:            # seam: the one closure primitive
def _verify(path: str, text: str) -> bool: ...
def main(argv: Sequence[str] | None = None) -> int: ...
if __name__ == "__main__": sys.exit(main())
```

**Acceptance Criteria**:
- [ ] AC-1.3/1.4/1.7/1.9 CLI halves (subprocess): `test_cli_ambiguous_prints_blocks_and_heading` (the line is `AMBIGUOUS blocks=2` followed by `heading=` and the `--heading` argument rendered as a quoted JSON string — `blocks=` bare because it is a helper-produced int, `heading=` quoted and holding the argument verbatim between the quotes; exit 0), `test_cli_index_past_end_is_not_found`, `test_cli_duplicate_headings_refuse` (`AMBIGUOUS_HEADING count=2`, nothing executed), `test_cli_index_zero_and_negative_are_bad_index` (`BAD_INDEX index="0"`/`"-1"` — `index=` is quoted, since `BadIndex` carries the raw argument and a non-integer is a legal input, exit 0, no side effect), `test_non_integer_index_is_bad_index`.
- [ ] AC-2.2/2.3/2.7/2.8 CLI halves (subprocess): `test_cli_missing_keys_list_in_argument_order`, `test_cli_overlap_counts_distinct_keys`, `test_cli_no_subst_runs` (zero `--subst`), `test_subst_without_equals_is_bad_subst`, `test_subst_empty_key_is_bad_subst` (`--subst =V` → `BAD_SUBST arg="=V"`, the raw argument verbatim inside the quotes — the assertion that discriminates `main`'s own refusal from a delegated one, which would print `arg=""`, an empty quoted value; under the quoted grammar there is no bare `arg==V` form to assert on), `test_duplicate_substitution_key_refuses` (`duplicate_key: "K"`, quoted like every detail value), `test_subst_value_may_contain_equals` — each refusal executes nothing and reserves nothing (no artifact created).
- [ ] AC-3.7 (subprocess) `test_cli_unknown_info_key_is_bad_info`; AC-3.12 (subprocess) `test_invalid_utf8_document_is_unreadable` CLI half (`UNREADABLE reason=doc_unreadable`, exit 2) and `test_invalid_utf8_preamble_is_unreadable`, `test_unreadable_preamble_path_refuses` (`preamble_unreadable`, exit 2, no side effect); `test_cli_preamble_file_reaches_the_block`.
- [ ] AC-3.8 (subprocess) `test_stream_paths_receive_the_streams` (two files differ for a block writing different text); `test_streams_optional`; `test_stream_paths_truncate_an_existing_file`; `test_streams_untouched_after_a_timeout`; (in-process main, each) `test_stream_write_failure_after_the_run_is_a_refusal` (`_final_write` injected to raise → `UNREADABLE reason=stream_write_failed`, exit 2, no `rc=`); `test_first_stream_write_failure_skips_the_second` (`_final_write` injected to raise on the first handle: `failed: "stdout"` / `skipped: "stderr"`, stderr bytes unchanged); `test_second_stream_write_failure_leaves_the_first_as_written` (`_final_write` injected to raise on the second handle: `written: "stdout"` / `failed: "stderr"`); `test_final_write_close_failure_is_mapped` (seam patched to call the real `_final_write` with a recording proxy whose `close` alone raises → `stream_write_failed`, `failed: "stdout"`, exit 2, no traceback; a regression test for `final-write-close-not-in-finally`, not its `test` key); `test_final_write_failure_before_close_still_closes` (proxy's `flush` and `close` both raise → same verdict and the proxy's `close` was called; the canonical `test` key of `final-write-close-not-in-finally`); `test_final_write_readback_catches_a_silent_no_op` (`_final_write` injected as a no-op → `stream_write_failed` with `verify: "stdout"`, `failed: "stdout"` / `skipped: "stderr"`, stderr bytes unchanged); `test_backstop_close_failure_on_timeout_is_mapped` (`_close_stream` injected to raise under `sleep 300`, `--shell-timeout 1`, `--stdout` given → `UNREADABLE reason=stream_close_failed`, a `stream: "stdout"` line and an `os_error: "<text>"` line, exit 2, no traceback, cwd gone); `test_backstop_close_failure_does_not_outrank_a_refusal` (same injection under an aliased pair → still `stream_paths_alias`, exit 2, no traceback); `test_stream_handles_are_closed_on_every_path` (recording `os.open` pass-through, `_final_write` injected for the first-write-failure leg; after `TIMEOUT` and after a first-write failure, `os.fstat` on each recorded fd raises `OSError`).
- [ ] AC-3.9 (subprocess) `test_symlinked_stream_paths_refuse`, `test_dot_slash_spelling_refuses`, `test_hard_linked_stream_paths_refuse` (`os.link`): `UNREADABLE reason=stream_paths_alias`, exit 2, block not run, both handles closed (by the backstop `finally`), a created file unlinked.
- [ ] AC-3.10 (subprocess) `test_stream_path_under_a_regular_file_refuses` (parent is a regular file → `stream_path_unwritable`, exit 2, no traceback, side-effect block left nothing); `test_stream_path_char_device_refuses` (subprocess, `--stdout /dev/null`: the reservation's first arm fails `O_EXCL` with `FileExistsError`, the second arm opens it under `O_WRONLY|O_APPEND|O_NONBLOCK` successfully, and the `fstat` then reports a **character device** — `S_ISREG` false — so the descriptor is closed and refused: `UNREADABLE reason=stream_path_unwritable`, exit 2, and a side-effect block left nothing. Measured 2026-09-03: `/dev/null` opens under those flags and `stat.S_ISREG` is `False`, `S_ISCHR` `True`); `test_stream_path_fifo_without_reader_refuses_bounded` (`os.mkfifo` path, CLI run with `timeout=5` in the test's `subprocess.run`, refusal within 1 s); `test_stdout_survives_a_failed_stderr_reservation` (pre-existing stdout byte-identical; a created stdout unlinked); `test_rollback_unlink_failure_reports_leftover` (in-process main, injected: `os.unlink`): `--stdout` is a **fresh** path under `tmp_path` so the first arm's `O_EXCL` succeeds and `created` is True, `--stderr` is a path **under a regular file** so the second arm fails with a real `ENOTDIR` and no injection is needed to reach the rollback; `monkeypatch.setattr(dbe.os, "unlink", fake)` where `fake` raises `PermissionError`, bound after `real_unlink = os.unlink` so the test's own `finally` can remove the leftover the injection deliberately created — the same rule as `real_rmtree` and `real_killpg`, and note that under this test the file is left behind **by design**, which is the state being asserted. Asserts `UNREADABLE reason=stream_path_unwritable`, exit 2, a `leftover:` detail line naming the stdout path exactly, that stdout path present and **empty** (zero bytes — the rollback closed the handle before the unlink was attempted, so nothing was written), and no traceback. `test_rollback_skips_unlink_on_identity_mismatch` (in-process main, injected: `os.lstat`, the ninth seam): the same fixture shape — a **fresh** `--stdout` under `tmp_path` so the first arm creates it, a `--stderr` under a regular file so the second arm fails with a real `ENOTDIR` — with `monkeypatch.setattr(dbe.os, "lstat", fake)` where `fake` returns a result whose `(st_dev, st_ino)` differs from the identity the reservation recorded by `fstat`, and `os.unlink` replaced by a **recorder that does not remove** (bound after `real_unlink = os.unlink`, which the test's `finally` uses to clear the file). Asserts the recorder was **not called at all**, `UNREADABLE reason=stream_path_unwritable`, exit 2, and a `leftover:` detail line naming that stdout path — the mismatch branch reports `leftover:` directly rather than through the `os.path.lexists` read-back, which is what keeps this test green under `rollback-leftover-unreported`.
- [ ] AC-4.1 (subprocess) `test_ran_line_and_exit_zero_with_nonzero_rc`: `DOCBLOCK: RAN rc=3 blocks=1 shell=plain`, exit 0 — all three fields are helper-constrained and therefore bare, so this line is unchanged by the quoting rule.
- [ ] AC-4.1/4.3 `test_dynamic_field_cannot_forge_a_token` (in-process main, no injection): `--heading 'x rc=0'` on a document without that heading → the `NOT_FOUND` line. The assertion is a **parse under the line grammar**, not a substring check: split the tail after `DOCBLOCK: NOT_FOUND` into fields, each `<key>=<bare>` or `<key>="<json-string>"`, and assert the field map is exactly `{"heading": "x rc=0"}` — one field, its value the argument verbatim, and **no `rc` field at all**. A substring check would pass under the mutant (the text ` rc=0` is present either way), so the parse is what discriminates. This is the AC-4.3 promise stated positively: a cannot-judge line carries no `rc`, and a caller cannot manufacture one.
- [ ] AC-4.1/4.3 `test_quote_in_dynamic_field_cannot_close_the_value` (in-process main, no injection): `--heading 'x" rc=0'` on a document without that heading. The assertion is the same **parse under the line grammar** the forge test uses: split the tail after `DOCBLOCK: NOT_FOUND` into fields and assert the field map is exactly one entry, `heading` mapping to the argument verbatim, with **no `rc` field**; and assert the emitted value's interior carries the two characters backslash-and-quote where the caller's quote stood. **This is the isolating killer of `field-escape-removed` and it is new at v1.53** (round seventeen, and it is this document's own addition rather than the sheet's): that row's narrowed payload frees exactly `"` and `\`, so it renders `heading="x" rc=0"`, the value closes at the caller's own quote and a bare `rc` field appears — measured on 3.11.8. **It is discriminated from `test_dynamic_field_cannot_forge_a_token` by which guard each one reaches**: that test's `x rc=0` carries no quote, so `field-escape-removed` renders it byte-identically to the real renderer and it stays green; this test's payload carries one, so `field-quoting-removed` also reds it and it is a collateral red there, never that row's key.
- [ ] AC-4.1 `test_malformed_invocation_is_a_verdict` (in-process main, no injection): two malformed invocations, each its own `main(argv)` call and `capsys.readouterr()` — an **unknown option** (`--nope`) and a **missing option value** (`--heading` with nothing after it). Each yields exactly one `DOCBLOCK: BAD_ARGS message="<the parser's own text>"` line, **exit 0**, and **no usage text on stdout**. The no-usage clause is what discriminates `argparse-error-unrouted`: with the `error()` override removed argparse raises `SystemExit(2)` and prints its usage block, so a test asserting only the exit code could still pass if a caller mapped 2 onward.
- [ ] AC-4.1 `test_unicode_line_separators_cannot_split_a_verdict_line` (in-process main, no injection): a `--heading` carrying U+0085, U+2028, U+2029 and U+007F on a document without that heading → the `NOT_FOUND` line. Assert that `capsys` stdout **`.splitlines()`** holds exactly **one** line starting with `DOCBLOCK:` — `.splitlines()` rather than `.split("\n")` is the whole point, since it is the splitter that breaks on the first three — and that all four characters appear inside the quoted `heading=` value as the escapes `\u0085`, `\u2028`, `\u2029` and `\u007f`. Measured before writing: without the second pass the same line `.splitlines()` into **four** pieces, with it into **one**, so this test is red against a `json.dumps`-only `_field` and green against the specified one.
- [ ] AC-4.1 `test_newline_in_dynamic_fields_cannot_forge_a_verdict_line` (in-process main; cases (1) and (2) need no injection, case (3) is **injected: `os.unlink`**, the same module seam AC-3.10's rollback test uses — `capsys` holds the lines; in-process because the assertion is on the emitted text, and three refusal paths are exercised in one test, each with its own `main(argv)` call and its own `capsys.readouterr()`): (1) `--heading` = `"x\nDOCBLOCK: RAN rc=0 blocks=1 shell=strict"` on a document without that heading → `NOT_FOUND`; (2) a `--subst` argument whose key and value each carry a `\n` → `SUBST_MISSING` when the key is well-formed but absent from the block, and `BAD_SUBST` for the malformed spelling, whose `arg=` then carries the raw argument; (3) the `leftover:` slot, built exactly as AC-3.10's `test_rollback_unlink_failure_reports_leftover` builds it, with the newline moved into the **created** artifact's name: `--stdout` is a **fresh** path under `tmp_path` whose **file name contains `\n`** (a newline is a legal POSIX file-name byte — verified on this platform: `os.open` with `O_CREAT|O_EXCL` creates it and `os.path.lexists` finds it), so the **first** arm succeeds and `created` is True; `--stderr` is a path **under a regular file**, so the **second** arm fails with the real `ENOTDIR`; `os.unlink` is injected to raise `PermissionError` exactly as AC-3.10 does, so the rollback read-back finds the created file still present → `UNREADABLE reason=stream_path_unwritable` carrying `leftover:` with the **escaped** name. **The newline must be on the created path, not on a first-arm failure** (impl-plan audit v19): a `--stdout` under a regular file fails the first arm, creates nothing, and therefore has no leftover to report at all, so that spelling would fail against a correct implementation rather than against the mutant. For each of the three, three assertions: **exactly one** line of the captured stdout starts with `DOCBLOCK:`; **no** line equals the forged `DOCBLOCK: RAN rc=0 blocks=1 shell=strict` string; and the payload appears **escaped inside the field's double quotes** — the emitted field is `heading="x\nDOCBLOCK: RAN rc=0 blocks=1 shell=strict"` — one quoted value whose interior holds the two characters `\` and `n` where the newline was, never a real newline. Under `field-escape-removed` **only the THIRD assertion fails**, and it fails on all three cases. **The mechanism is stated per assertion because the obvious one-clause version of it is wrong**, and this bullet carried that wrong version until v1.53's own row rewrite was swept for second sites (design-author-r17b): the narrowed mutant keeps the quotes and keeps the c1 second pass, and `unicodedata.category` of LF is `Cc`, so the raw newline is escaped to `\u000a` rather than emitted — the verdict stays **one** physical line and the exactly-one-`DOCBLOCK:`-line assertion HOLDS, as does the no-forged-line assertion. What moves is the escaped SPELLING: the interior reads `\u000a` where this AC's contract spells the two characters backslash and `n`. That is a real assertion failing for a real reason and not the reason this test exists for, which is why the test is that row's **regression** test and `test_quote_in_dynamic_field_cannot_close_the_value` is its key. The third assertion is stated separately because it does not depend on how a consumer splits lines, and under this mutant it is the whole of the kill rather than a second guarantee beside a line count.
- [ ] AC-4.2 `test_verdict_table_exit_codes`: parametrised over the 23 `VERDICT_TABLE` heads with one producer each — a subprocess producer for the 17 heads a real input or real fault yields (`RAN`, `NOT_FOUND`, `AMBIGUOUS`, `AMBIGUOUS_HEADING`, `BAD_INDEX`, `BAD_TIMEOUT`, `BAD_SUBST`, `BAD_ARGS` via an unknown option, `SUBST_MISSING`, `SUBST_OVERLAP`, `BAD_INFO`, `TIMEOUT`, `LAUNCH_FAILED stage=spawn` via an empty `PATH`, `UNREADABLE reason=doc_unreadable`, `UNREADABLE reason=preamble_unreadable`, `UNREADABLE reason=stream_paths_alias`, `UNREADABLE reason=stream_path_unwritable`) and an in-process `main(argv)` producer for the 6 that need a fault injection (`CLEANUP_FAILED` via `shutil.rmtree` — `real_rmtree` bound first, retained cwd removed in `finally`, `LAUNCH_FAILED stage=mkdtemp` via `tempfile.mkdtemp`, `LAUNCH_FAILED stage=reap` via `os.killpg`, `LAUNCH_FAILED stage=collect` via the instance-level `Popen` wrapper of `test_communicate_oserror_is_launch_failed_collect` — the same `echo hi` block, the same `real_killpg` teardown, `UNREADABLE reason=stream_write_failed` via `_final_write`, `UNREADABLE reason=stream_close_failed` via `_close_stream`); either way the assertion compares the produced exit code (process exit or `main`'s return) with `VERDICT_TABLE[head]` and the emitted line starts with `DOCBLOCK: ` followed by the head; **for the `LAUNCH_FAILED stage=reap` and `LAUNCH_FAILED stage=collect` producers the captured output also carries a quoted `pgid: "<n>"` detail line** (the two stages on which `LaunchFailed` sets `pgid`; this is the only place `pgid:` is asserted at the CLI, the design's AC-4.6 row expecting it there); one assertion that `set(params) == set(VERDICT_TABLE)`; `test_every_docblockerror_subclass_has_a_verdict` (walk `DocBlockError.__subclasses__()` recursively and assert **membership by class**: each subclass is a `_VERDICT_FOR` key. **The walk instantiates nothing** — it constructs no exception and therefore imposes no constructor shape on any subclass, so the ones with required arguments keep them (design v1.80, design audit v72). Head-to-`VERDICT_TABLE` agreement is proved by `test_verdict_table_exit_codes` above, which produces each of the 23 heads for real; this test's job is only that no subclass is missing a renderer.)
- [ ] AC-4.2 exit propagation (subprocess): `test_cli_exit_zero_propagates` (a document whose section has no tagged fence → `DOCBLOCK: NOT_FOUND`, process exit 0) and `test_cli_exit_two_propagates` (a document containing byte `0xff` → `DOCBLOCK: UNREADABLE reason=doc_unreadable`, process exit 2) — both compare the process exit with `VERDICT_TABLE[head]`, pinning that `sys.exit(main())` propagates `main`'s return value.
- [ ] AC-4.1/4.3 `test_cli_subst_overlap_detail_lines` (subprocess): **the site where the `SUBST_OVERLAP` detail lines are asserted VERBATIM**, because this is the task the renderer lands in (round-eighteen sheet FACT 4 e; Task 2's AC-2.7 asserts the exception data and deliberately not the line). Two invocations of the same CLI on the same document. (1) `--subst` carrying `ab=X` and `bc=Y` against a block whose text is `abc` emits `DOCBLOCK: SUBST_OVERLAP keys=2` followed by exactly one detail line, `intersect: "ab" "bc" "1"`, at exit 0 with nothing executed — which pins all three determinism rules at once: the three-value quoted shape with no connective, `ab` before `bc` because it is lexicographically smaller, and `1` because that is the smallest index the spans `[0, 2)` and `[1, 3)` share, where the superseded wording gave `0`. (2) `--subst` carrying `a=1`, `ab=2` and `abc=3` emits `DOCBLOCK: SUBST_OVERLAP keys=3` followed by exactly three `overlap:` lines, `overlap: "a" "ab"`, `overlap: "a" "abc"` and `overlap: "ab" "abc"`, both halves quoted. **The two legs together are what pin the `kind` tag to the LINE it selects**: one tagged `pairs` list feeds one renderer, and a renderer that ignored `kind` would print the same line for both members, so each leg is red under the other's spelling. It adds no mutation row and the matrix total is **86** at this batch, none of it from this axis — `intersect-check-removed` and `overlap-resolved-by-order` already kill the two predicates, and this test's own kind-selection arm is a rendering claim the design's matrix does not carry a row for; a row for it is a DESIGN change and is owed to the design if the round wants one.
- [ ] AC-4.3 (subprocess) `test_no_refusal_carries_rc`; AC-4.4 (subprocess) `test_only_ambiguous_carries_blocks`.
- [ ] AC-4.5 `test_every_emittable_line_has_a_registry_row` (every `VERDICT_TABLE` key and every `DETAIL_KEYS` entry appears as the first backtick token of a row in the SKILL.md entry) and `test_registry_rows_cover_only_emittable_lines` (every row's first token is in that union).
- [ ] AC-4.6 (subprocess) `test_cli_nul_composition_is_a_verdict_on_both_paths`: **the CLI half of the two NUL composition paths, which Task 3 pins only at the API** (impl-plan audit v48 codex should 1: Task 3's two NUL tests both call `dbe.run_block` in-process, and the CLI launch tests reach `stage=spawn` through an empty `PATH` instead, so nothing established that a NUL-bearing input yields the promised quoted diagnostic and a clean process exit). Two real subprocess invocations of the CLI, parametrised over the two paths — a document whose tagged block body contains `\x00`, and a `--preamble` argument containing `\x00` on a clean document — each asserting `DOCBLOCK: LAUNCH_FAILED stage=spawn` (`stage=` bare) followed by an `os_error:` detail line whose single value is the `ValueError`'s text and is QUOTED under the same rule the grammar block above states for that key — the key is named here rather than its slot re-spelled, so this AC adds no new unfilled-slot finding to the precheck's floor — process exit **2**, no `rc=` field, **no traceback on stderr**, and the block's temporary cwd gone. It adds no mutation row and the matrix total is **86** at this batch, none of it from this axis: `spawn-valueerror-unmapped` already kills the guard from the API side and this test is the CLI-surface evidence for the same guard, which is the distinction the Conventions bullet draws between a killer and a regression test.
- [ ] AC-4.6 CLI halves: `test_cli_launch_failed_lines` — the `stage=spawn` leg (subprocess, empty `PATH`) and the `stage=mkdtemp` leg (in-process main, `tempfile.mkdtemp` injected), each its own `LAUNCH_FAILED stage=` head (`stage=` bare) with a quoted `os_error: "<text>"` line, exit 2, no `rc=` — reap and collect are covered in Task 3 at the API and here by the table test, which is where their `pgid:` detail line is asserted at the CLI.
- [ ] AC-5.6 (subprocess) `test_cli_bad_timeout_values`: `0`, `-1`, `nan`, `inf`, `abc` → `BAD_TIMEOUT` followed by `value=` and the argument rendered as a quoted JSON string, holding it verbatim between the quotes; exit 0, no side effect, **and with `--stdout`/`--stderr` given: a path that did not exist is still absent afterwards, and a pre-existing file keeps its bytes** (validation ran before `_reserve`); `test_non_numeric_timeout_is_bad_timeout`.
- [ ] Parser (subprocess) `test_parser_rejects_all_dir_and_abbreviations`: three rejected invocations, each yielding **one `DOCBLOCK: BAD_ARGS message="<m>"` line and exit 0** — never argparse's usage text and never a non-`DOCBLOCK` exit, because the `error()` override at argparse's **default `exit_on_error`** routes every grammar error through the verdict table — measured on 3.11.8 over all five grammar shapes, where `exit_on_error=False` would let a missing option value escape as `ArgumentError` (design v1.91) (this AC formerly promised usage/exit 2, which contradicted the declared contract, the `VERDICT_TABLE`, the paired design and `argparse-error-unrouted`; impl-plan audit v28). The three: `--all` (an option this CLI does not define), `--dir x` (likewise), and **the abbreviation case, which needs a complete otherwise-valid argv** — `[doc, "--heading", "## Second surface — the codex leg", "--shell-t", "5"]` against a real fixture document. Completing the argv is what makes the case discriminating: under `allow-abbrev-restored` the parser accepts `--shell-t` as an alias for `--shell-timeout`, every required argument is already present, so the run **proceeds to whatever verdict the fixture produces** (a `RAN` or a `NOT_FOUND`, not a `BAD_ARGS`) — a visibly different outcome. With an incomplete argv the mutant would still fail, merely later and for a missing required argument, and the row would be caught by the wrong assertion. The assertion is therefore that the emitted head **is** `BAD_ARGS` for all three, not merely that the run failed.

**Mutation rows added here**: `subst-split-on-every-equals`, `subst-duplicate-key-last-wins`,
`cli-empty-key-delegated` (`main` stops refusing the empty key while building the map and lets
`substitute` raise `BadSubstArg("")`, so the verdict prints `arg=""` — an empty quoted value —
instead of the raw `arg="=V"` (design v1.84: under the quoted grammar the discriminator is
`arg=""` versus `arg="=V"`, never a bare `arg==V`);
killed by `tests/test_h_mad_doc_block_exec.py::test_subst_empty_key_is_bad_subst`.),
`index-nonint-unmapped`, `timeout-nonnumeric-unmapped`, `preamble-decode-error-unwrapped`,
`stream-reserved-with-truncation`, `final-write-close-not-in-finally`,
`verify-deferred-past-second-write`, `final-write-not-verified`, `nonregular-stream-accepted`,
`stream-open-blocking`, `stream-alias-check-removed`, `exit-partition-flipped`,
`rc-leaked-into-refusal`, `field-escape-removed` (the `json.dumps(str(value), ensure_ascii=False)`
call is replaced by a bare double-quote wrap of `str(value)` and **the c1 second pass is kept**.
**What that frees is exactly two characters, `"` and `\`, and nothing else** — measured on 3.11.8
against the real renderer and all three `_field` mutants over four payloads, because the mechanism
this row carried through v1.52 was wrong in the same way the payload was. `unicodedata.category`
of LF and of CR is `Cc`, so the kept c1 pass escapes a raw newline to `\u000a` on its own: under
this mutant a newline in a heading does **not** start a second physical line, and any sentence
saying it does is describing a mutant this document does not specify. Its canonical `test` key is
therefore `tests/test_h_mad_doc_block_exec.py::test_quote_in_dynamic_field_cannot_close_the_value`,
the AC-4.1 test added below for exactly this row: under the mutant `--heading 'x" rc=0'` renders as
`heading="x" rc=0"`, the value closes at the caller's own quote and a bare `rc` field appears on a
refusal line, which is the AC-4.3 promise broken. `test_newline_in_dynamic_fields_cannot_forge_a_verdict_line`
is a **regression test** on the same mutant, never its key: it does go red, but only through its
escaped-payload assertion, whose contract spelling is the two characters `\` and `n` where the
emitted text reads `\u000a` — a real assertion failing for a real reason, and not the reason that
test exists for, which is the wrong-catcher shape this document already refuses at
`argparse-error-unrouted`. **The class this correction closes**: a mutation payload that removes
one call is not a payload that removes one property, because a later pass in the same function can
be a superset guard for what the removed call also did. The three `_field` rows are now separated
by PROPERTY — quoting, `"`/`\` escaping, and Zl/Zp escaping — and the property each frees is
measured rather than reasoned from the call it deletes),
`c1-escape-removed` (`_field`'s second pass is removed, leaving only `json.dumps`, so U+0085,
U+2028, U+2029 and U+007F come through literal and a heading carrying them splits one verdict
into four lines; killed by
`tests/test_h_mad_doc_block_exec.py::test_unicode_line_separators_cannot_split_a_verdict_line`),
`field-quoting-removed` (`_field` still escapes control characters but emits the value **bare**,
without the surrounding quotes, so `--heading 'x rc=0'` parses to two fields and yields an `rc`
field; killed by `tests/test_h_mad_doc_block_exec.py::test_dynamic_field_cannot_forge_a_token`),
**and the three-by-three matrix over those three rows and their three tests is stated here once,
rather than as pairwise sentences, because a pairwise claim is what went wrong**. It is a
MEASUREMENT, run on 3.11.8 against the real renderer and each mutant over four payloads before it
was written, and the fourth payload is why the matrix has a fourth column. Rows down, tests across;
`N` is the newline test, `U` the unicode test, `F` the forge test, `Q!` the quote test.

| row | property it frees | N | U | F | Q! |
|---|---|---|---|---|---|
| `field-escape-removed` | `"` and `\` only | red (regression) | green | green | **red (key)** |
| `c1-escape-removed` | U+2028 / U+2029 (Zl, Zp) | green | **red (key)** | green | green |
| `field-quoting-removed` | the surrounding quotes | red | red | **red (key)** | red |

`c1-escape-removed` is isolated: it reds exactly its own key, because `json.dumps` still escapes
the newline and still supplies the quotes, and the four line separators are the only characters it
frees. **`field-escape-removed` is isolated to its key too, and only once that key is the QUOTE
test** — under it `U` is byte-identical to the real renderer and `F` still parses to one `heading`
field; `N` reds on the escape spelling and stays a regression test, for the reason the row states.
**`field-quoting-removed` is NOT isolated and that is recorded rather than smoothed**: `N`, `U` and
`Q!` all assert their payload appears inside the field's double quotes, so stripping the quotes
reds three further tests. It is one of the rows in this document whose mutant reds a second named
test, enumerated with the others in Conventions. **Not repaired by weakening the assertions**:
dropping the quote clause from `N`, `U` and `Q!` would leave nothing pinning that the escaped
payload sits inside a quoted value rather than beside it, which is the AC-4.3 promise, so the
exposure is priced and kept.
`rollback-leftover-unreported` (the rollback's
`os.path.lexists` read-back is removed, so a first-reservation file that the failed unlink left
behind is never reported and the `stream_path_unwritable` verdict carries no `leftover:` line;
killed by `tests/test_h_mad_doc_block_exec.py::test_rollback_unlink_failure_reports_leftover`,
whose other assertions — the verdict, the exit code, the file's presence — all still hold under the
mutant, so the `leftover:` line is the only thing that discriminates it),
`rollback-identity-check-removed` (the `(st_dev, st_ino)` comparison deleted, so the rollback
unlinks unconditionally and deletes whatever now stands at the path; killed by
`tests/test_h_mad_doc_block_exec.py::test_rollback_skips_unlink_on_identity_mismatch` on its
**unlink-not-called** assertion, which is the only one that moves — the verdict, the exit code and
the `leftover:` line all still hold under the mutant because the recorder removes nothing.
**It is discriminated from `rollback-leftover-unreported` in both directions**: that row removes
the `os.path.lexists` read-back, which the mismatch branch does not use, so this row's killer stays
green under it; and this row leaves the read-back intact, so
`test_rollback_unlink_failure_reports_leftover` — whose `os.lstat` is the real one and whose
identity therefore matches — stays green under it),
`stream-open-oserror-unwrapped`, `backstop-close-unmapped`,
`backstop-close-outranks-error`, `registry-row-removed` (targets `h-mad/SKILL.md`),
`detail-line-undocumented`, `argparse-error-unrouted` (the `error()` override is removed, so argparse raises `SystemExit(2)`
and prints usage instead of the `BAD_ARGS` verdict; killed by
`tests/test_h_mad_doc_block_exec.py::test_malformed_invocation_is_a_verdict` on its no-usage and
exit-0 clauses. **This mechanism is true as written only at argparse's default `exit_on_error`**,
which is a second reason the default is load-bearing: the mutant was probed both ways on 3.11.8,
and at the default both of the killer's inputs give `SystemExit(2)` with usage on stderr, while
under `exit_on_error=False` the missing-value input gives `ArgumentError` instead — the row would
still have gone red, but on a mechanism its own description denies, which is the wrong-catcher
class. It is discriminated from `allow-abbrev-restored`, which changes which
invocations argparse rejects rather than how a rejection is reported: that row's killer feeds an
abbreviation that must be refused, and this one feeds an invocation argparse refuses either way),
`allow-abbrev-restored` (the parser built with `allow_abbrev=True`, so
`--shell-t 5` aliases `--shell-timeout`, so the otherwise-valid argv above parses and runs instead
of refusing; killed by `test_parser_rejects_all_dir_and_abbreviations` on its `BAD_ARGS` head
assertion for that third case. It is discriminated from `argparse-error-unrouted`, which changes
**how** a rejection is reported rather than **which** invocations are rejected: that row leaves
`--shell-t` refused and is caught by the missing `BAD_ARGS` head and the usage text on stdout),
`stream-write-oserror-unwrapped` (the `except OSError` mapping around `_final_write` and its
read-back removed, so a write failure escapes as a traceback; killed by
`test_stream_write_failure_after_the_run_is_a_refusal`) — 28 rows.
**Two AC-3.10 rows were re-bound this cycle** (design v1.82, design audit v73), because the FIFO
fixture cannot kill both: measured 2026-09-03, a reader-less FIFO opened `O_WRONLY|O_APPEND|O_NONBLOCK`
fails at `os.open` with **ENXIO** and never reaches the `S_ISREG` check, so it exercises the
blocking-open guard and nothing else. `nonregular-stream-accepted` (the `S_ISREG` check dropped)
is therefore killed by the new `tests/test_h_mad_doc_block_exec.py::test_stream_path_char_device_refuses`,
whose `/dev/null` **does** open and **does** reach the check; `stream-open-blocking` (the
`O_NONBLOCK` dropped from the second arm) keeps
`tests/test_h_mad_doc_block_exec.py::test_stream_path_fifo_without_reader_refuses_bounded` as its
sole killer. Each row now has one killer that actually reaches its guard.
`cli-empty-key-delegated` is discriminated from Task 2's `empty-key-accepted-by-api`, which is NOT one of the 28
above, by which side is mutated: that row removes `substitute`'s own guard and is killed by the API
test, this one removes `main`'s and is killed by the CLI test, and neither killer touches the
other's code path. With Tasks 1, 2, 3 that is
25 + 7 + 26 + 28 = **86 rows**, split **85 of the helper's source and 1 of `h-mad/SKILL.md`**.
**The move 85 → 86 is the design's r18 addition, mirrored here, and the +1 lands in TASK 2** —
`intersect-scan-non-overlapping`, which takes that task 6 → 7 while Tasks 1, 3 and 4 are unmoved at
25, 26 and 28. **86 is a reading over a SIBLING's post-edit body and is therefore stamped to the
tree THIS BATCH ships, never to `cac6edc`** (the freeze-sha rule's third clause): the design carries
85 rows at `cac6edc` and 86 in the revision landing beside this one, re-derived with the plan's
published `awk` over the design's mechanism column, which prints `total=86 skill-md-target=1` — so
the SPLIT is unmoved and only the helper-source half grew.
**The move 81 → 85 is round seventeen's shared decision and is NOT derived from any sibling's
current bytes**, which is why it is stated as a decision here rather than as a reading. The four
additions are `intersect-check-removed` (Task 2, decision 3a), `spawn-valueerror-unmapped`
and `cleanup-chain-selection-flipped` (both Task 3, decisions 3b and 3g) and
`rollback-identity-check-removed` (Task 4, decision 3c); each one is a
guard this round added and each is bound to exactly one named killer beside it. The design carries
**81** rows at `fbc2ea0` and owes the same four; that debt is recorded in v1.53's entry
and the derivation below keeps its own reading at the blob it was taken on rather than being
back-dated to 85.
**The split is derived from the mechanism column of the design's helper matrix, never copied from
any document's prose** — the prose is what was wrong. Derivation, first run at `1861157` and
**re-run at `700c599` for v1.48 rather than inherited**, because the design moved again
across exactly this span and a count over a moved table is not a carried count — the span is given
as a command rather than as a version number, which is the moving-value class the header rule
covers: `git diff --stat 1cbddb7 700c599 -- docs/02-design/features/doc-block-exec.design.md` is
**127 insertions / 25 deletions** (the two spans before it, `7d8e797`..`1cbddb7` and
`4e4a00c`..`7d8e797`, were 136 / 33 and 303 / 39). **A stamp in this document is DATED, not standing** — it records
the sha a figure was last run at, so a Version History sentence claiming that a *set* of them was
re-run is itself a property claim about this document and must be **screened, not asserted**. The
screen is the one stated in Conventions —
`awk '/^## Version History/{exit}{print}' <this file> | grep -oE 'at .[0-9a-f]{7,40}.' | sort | uniq -c`
— and it is written the same way in both places on purpose, a second spelling being a second
authority. Its **whole** table for the shipping revision is published in that revision's Version
History entry rather
than replaced by a closing sentence or by a chosen subset of the rows. **A residual of the screen's
FORM, not only of its meaning** (impl-plan audit v44): the pattern requires the literal preposition
`at` immediately before the backticked sha and matches nothing else, so a stamp introduced by
"against", "measured on" or "as of" instead
is invisible to it — the screen is a census of one spelling, which is why that spelling is
the one this document uses and why a reviser who reaches for a synonym silently shrinks the table.
v1.45's closure that "the `docs/`-facing figures were
re-run" was asserted and was **false**: the design had moved `4e4a00c` → `68a70d6` (161 insertions
/ 37 deletions) while this derivation still carried the `4e4a00c` stamp (impl-plan audit v43).
Every figure it covered was nonetheless correct, so that was a **stamp defect, not a figure
defect**, and the repair is the screen, not a new adjective. Over the data rows
of the design's helper-spec mutation matrix in `docs/02-design/features/doc-block-exec.design.md`
— the table whose second column heading is "guard it removes (mechanism)", located with
``grep -nE '^\| mutation \| guard it removes \(mechanism\) \| killed by' docs/02-design/features/doc-block-exec.design.md`` (one hit,
verified at `cac6edc`, and one hit at `fbc2ea0` too) — **the bare phrase this locator used through
v1.53 is WITHDRAWN because it went from one hit to two inside the round-seventeen batch commit**:
`grep -n 'guard it removes'` on the design reads **1** at `fbc2ea0` and **2** at `cac6edc`, the
second being an `awk` line the design's own r17 revision added that quotes the table header it
selects on. That is the needle-drifts-inside-a-single-commit class this document already names for
`both halves of`, recurring on a different needle, and the repair is the one the Conventions bullet
prescribes: an anchored table-row prefix, which is lexically specific to the row and cannot be
matched by prose about it — count those whose mechanism column names
`SKILL.md` as the file the harness edits — **81 data rows, exactly 1 of them**
(`registry-row-removed` — this document's own row list annotates it, and only it, as targeting
`h-mad/SKILL.md`; the corresponding design row is located with
``grep -n '^| `registry-row-removed`' docs/02-design/features/doc-block-exec.design.md``, one
hit, verified at `700c599`), so 80 + 1. The 81 are **81 distinct row names** — the count is over
`sort -u`'d names, not over lines, so a duplicated row could not inflate it — and every one of the
81 occurs in this document, checked at `700c599` by testing each design row name for membership in
this file: **0 missing**. **That whole derivation is a reading of a committed blob and stays
stamped at `700c599`, unchanged by v1.53** (the freeze-sha rule's second clause). What it
establishes is the SPLIT — that exactly one row in the matrix names `SKILL.md` as the file the
harness edits — and the split is what survives the count moving: the three rows round seventeen
adds are all helper-source rows, so 80 + 1 becomes 84 + 1 and the "exactly 1 of them" is untouched.
The membership check itself is **not** re-run at `fbc2ea0` and is not claimed to be: the design at
that commit still carries 81 names, so re-running it there would re-derive the same 81 and say
nothing about the three this round adds. It is re-run against the design at the commit that lands
this batch, and until then the count rests on the decision rather than on a sibling reading. **At
round eighteen the sibling reading arrived**: the design's r18 revision carries 86 rows, re-derived
here with the plan's published `awk` over its mechanism column (`total=86 skill-md-target=1`), so
the split is confirmed against a sibling's body rather than asserted — and that reading is stamped
to the tree this batch ships, since it is taken over the design's post-edit body and not over
`cac6edc`.
**`detail-line-undocumented` is a helper-source mutation, not the second `SKILL.md` row** — it
renames an emitted detail line **in the helper** (`missing_key:` → `absent_key:`) so that an
emittable line has no registry row (its design row is located with
``grep -n '^| `detail-line-undocumented`' docs/02-design/features/doc-block-exec.design.md``, one
hit, verified at `700c599`). It is `registry-row-removed`'s partner **by
AC**, both serving AC-4.5's bidirectional pin, **not by file**; reading the pair as "the two
`SKILL.md` rows" is exactly how the 79 + 2 miscount arose, here and in the design. The annotation
in the row list above already says so — only `registry-row-removed` carries "(targets
`h-mad/SKILL.md`)" — so this line and that list now agree (impl-plan audit v34, plan-author).
No design version is pinned here on purpose: a `matching design v1.NN` claim is the moving-value
class the header rule covers, and the derivation above is the check that replaces it.

**Dependencies on other tasks**: Tasks 1, 2, 3.

**Expected RED split — WHOLE-FILE totals, and the failure MODE per test** (decision 3h). **Failing**:
every test this task adds. **Passing**: every test Tasks 1, 2 and 3 landed in
`test_h_mad_doc_block_exec.py` — three regression-guard blocks, Task 1's, Task 2's ten and Task 3's,
none of which this task touches. **Expected passing is not 0**; the `--expect-pass` integer is the
`passed` figure of Task 3's GREEN summary over this file, and `--expect-fail` is the count of this
task's AC list.
**The failure mode is NOT a traceback, and the earlier text said it was** (round seventeen,
decision 3h's second half). The `__main__` block `if __name__ == "__main__": sys.exit(main())`
ships **with this task**, in the code block above, so at Task 4's RED the module file has no
entry point at all: `subprocess.run([sys.executable, SCRIPT, *args])` imports the module, executes
nothing, ignores every argument and exits **0** with empty stdout and empty stderr — measured on
3.11.8 against a module with no `__main__` guard. Per test, therefore: the **subprocess** tests
fail on their own assertions — no line starting `DOCBLOCK:` is captured, and the exit code is 0
where the verdict table says 2 — never on a traceback and never on a non-zero exit; the
**in-process `main`** tests and the API tests fail with `AttributeError` on `dbe.main`, which is
the mode the earlier text got right. **That `AttributeError` is the same RED-by-construction case
Task 2's split states**: Task 4 introduces the new symbol `main`, carries no `WIRE:`/`WIRE-PIN:`,
and every one of those tests also asserts the behaviour that must hold once `main` exists, so the
missing attribute is where the failure starts and never where the test stops.
**Every subprocess test in this task therefore asserts a `DOCBLOCK:` head positively, and two are
named because their prose reads as pure absence**: `test_no_refusal_carries_rc` (AC-4.3) and
`test_only_ambiguous_carries_blocks` (AC-4.4) each assert the expected head is emitted **and** that
the field in question is absent from it. Without the positive half they would pass vacuously at
RED against empty output, which is a green test proving nothing and the exact shape §5d's "failure
mode per test" exists to surface. No test in this task passes at RED.
`doc_block_exec.json` must report `ALL_CAUGHT` over all 86 rows
before this task is GREEN.

**RED gate**: `hmad-dispatch run --timeout 600 -- python3.11 -m pytest tests/test_h_mad_doc_block_exec.py -q` before any production code — every Task 4 test fails and Tasks 1–3 stay green. Judge it on the pytest summary, never on `$?` alone, and keep the recorded output beside the task as the 5d dispatch's `--out` file; `rc=124` is the wrapper's expiry, not a RED result. This is what `h_mad_assemble_tdd.py --phase red` dispatches, with `--test-path` set to the file named above, `--expect-fail` and `--expect-pass` set to the counts this split states for a new-behaviour task and omitted for a wiring task (Tasks 1 and 5 state their RED in prose, as the assembler allows), `--out` the recorded report kept beside the task, and `--timeout 600`.

---

## Task 5: tag the gate fence and migrate the executing consumer

**Production file**: `h-mad/SKILL.md` (Second-surface gate fence) and `h-mad/tests/test_h_mad_collect_report_docs.py`
**Test file**: `h-mad/tests/test_h_mad_collect_report_docs.py` (gains six tests) and `h-mad/tests/test_h_mad_doc_block_exec.py` (gains two)
**Mutation spec**: `h-mad/tests/mutation-specs/doc_block_exec_wire.json` (new)
**Task shape**: `wiring`
**WIRE 1**: `h-mad/tests/test_h_mad_collect_report_docs.py:_gate_block` → `dbe.extract` AND `dbe.select`
**WIRE-PIN 1**: `h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_resolves_through_doc_block_exec`
**WIRE 2**: `h-mad/tests/test_h_mad_collect_report_docs.py:_run_recipe` → `dbe.substitute` AND `dbe.run_block`
**WIRE-PIN 2**: `h-mad/tests/test_h_mad_collect_report_docs.py::test_recipe_runs_through_run_block`

**Description**: Change the Second-surface gate fence opener in `h-mad/SKILL.md` from ` ```bash `
to ` ```bash hmad:exec `. **The target is located structurally, never by line number.** Through
v1.31 this task pinned six `h-mad/SKILL.md` line numbers and every one of them went stale: the
section heading sat at `:1804` when they were written, at `:1887` at commit `e8eaf6f`, and at
`:1897` at `b7d0d77` — one commit later, a ten-line move in a single edit. `h-mad/SKILL.md` is
edited most working sessions, so *any* line number written here is stale before 5d reads it. The
axis is **where a line sits in a file that keeps growing above it**; the rule over that axis is a
content predicate, and the three parts of the locator are:

- **The window** — `h-mad/SKILL.md` from the line `## Second surface — the codex leg` up to (not
  including) the next line beginning `## `.
- **The target** — the ` ```bash ` opener of the fence in that window whose body contains
  `h_mad_audit_gate.py`. That is the same predicate the consumer's pre-migration extraction
  uses — `[b for b in blocks if "h_mad_audit_gate.py" in b]` at `:271`, binding the `blocks` the
  `re.findall` at `:270` produces; the comprehension is on the line **after** the `re.findall` and
  binds `blocks`, not the `_bodies` this document's own mutant payloads introduce (impl-plan audit
  v44; `grep -rn '_bodies' h-mad handoff` returns nothing) — and it is the one every `wire-revert-*`
  payload in this task restates, so the locator and the mutants agree by construction. That opener
  is the one line this task changes in production text.
- **The block that stays untagged** — identified by content too: the fence whose body contains
  `hmad-dispatch exec codex`. **Never by ordinal**: the content predicate is the load-bearing
  part, and an ordinal is exactly as perishable as a line number. The ordinal is recorded as
  **informational only, and it carries its base**: at `335f535` it is the **2nd of 4, 1-based**,
  counting `^```bash` openers inside the window. The base is written down because the same census
  read 0-based names a different block, and a bare "index N" is off by one depending on the
  reader.

Two invariants over that window, with **different failure actions**. *Load-bearing*: exactly one
bash fence in the window contains `h_mad_audit_gate.py`. If the resolver below finds zero or more
than one, halt and re-derive the target before editing anything — tagging a second gate-containing
fence makes `dbe.select` raise `AmbiguousBlock` at GREEN and breaks AC-6.1, and a bare first-match
would tag the wrong block. *Informational, with its base*: the window holds four bash fences and
the gating one is the **4th of 4, 1-based** — the last (re-derived at `335f535` with the two
commands below, which printed `4` and one opener line). **The residual, stated exactly**: a fifth
bash fence that does **not** contain `h_mad_audit_gate.py` changes nothing about the tagging and is
not a reason to halt — it makes only the count of four stale, which is why the count is not the
locator. The one addition that does need a decision is a fifth fence that *does* contain
`h_mad_audit_gate.py`: that breaks the load-bearing invariant, and the implementer halts rather
than guessing which fence the gate recipe means. Nothing else about the window is pinned here —
not the fences' order, not their contents, not their offsets.

Resolve the opener at 5d rather than reading a number from this document:

````bash
awk '/^## Second surface — the codex leg$/{w=1;next} w&&/^## /{exit} w' h-mad/SKILL.md \
  | grep -c '^```bash'                                        # informational: expect 4
awk '/^## Second surface — the codex leg$/{w=1;next} w&&/^## /{exit}
     w&&/^```bash/{o=NR;f=1;next} w&&f&&/^```$/{f=0;next}
     w&&f&&/h_mad_audit_gate\.py/{print o}' h-mad/SKILL.md
````

The second command prints the 1-based line number of the opener to change, and must print exactly
one line — that is the load-bearing invariant, checked mechanically. The `f` flag confines the
match to **fence bodies**, so prose in the window that merely names `h_mad_audit_gate.py` is not
counted and a halt on more than one line really does mean a second gate-*containing fence*, which
is what the halt text above claims (the section's closers are bare ``` at column 0). The number it
prints is an *output* of the resolver, not a contract, and is deliberately not written down
anywhere in this document. Both commands stay correct after the migration, because `/^```bash/`
and `'^```bash'` are prefix matches and the tagged opener is ` ```bash hmad:exec `. In the
consumer, add
`import h_mad_doc_block_exec as dbe` (module-qualified; never `from h_mad_doc_block_exec import`) after the existing
`sys.path.insert(0, str(SCRIPT_DIR))` at `:22`; replace the `:270` `re.findall` inside
`_gate_bash_block` with `_gate_block() -> dbe.Block` = `dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))` (the full line form, level-pinned — `extract`'s form),
reduce `_gate_bash_block() -> str` to `_gate_block().text` so its two text-pin callers (`:281`,
`:368`) keep their string. **Hoist** the `run_recipe` closure — today nested at `:309` inside
`test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`, returning
`subprocess.CompletedProcess[str]` from an inline `subprocess.run(["bash", "-c", preamble + script])`
and rewriting the installed gate path with `str.replace` at `:312` — to a module-level
`_run_recipe(*, phase: str, cycle: int, report: Path, root: Path) -> dbe.RunResult`. Its body:
`collector = SCRIPT_DIR / "h_mad_collect_report.py"` and `gate = SCRIPT_DIR / "h_mad_audit_gate.py"`
(the two locals the closure captured from the test, now derived inside `_run_recipe` itself from the module-level
`SCRIPT_DIR`); `block = _gate_block()`;
`subbed, _ = dbe.substitute(block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(gate))})`
(the checkout-path rewrite, now through the helper). **The tuple unpacking is required, not
stylistic** (design v1.87): `substitute` returns `(Block, dict[str, int])`, so `subbed` must be
bound from the first element and the per-key count discarded; handing the tuple itself to
`dbe.run_block(subbed, preamble=preamble, timeout=60.0)` would pass a `tuple` where a `Block` is
expected. The code structure
below writes it the same way, and WIRE-PIN 2 asserts that the block `run_block` receives **is**
the one `substitute` returned, which only holds for the unpacked form. the existing `preamble` f-string unchanged
(a `COLLECT_OUT=$(` command substitution running the real collector with `--surface codex`, the phase, cycle, report and project root, every path through `shlex.quote`; shown verbatim in the code structure); `return dbe.run_block(subbed, preamble=preamble, timeout=60.0)`.
The existing test's two callers (`:340`, `:346`) keep working unchanged: they read only
`.stdout` and `.stderr` (grep over `:294–:362` finds no `.returncode`, `.args` or `.check` read),
and `dbe.RunResult` carries both as `str`. The tagged fence defaults to `shell=strict`; the
recipe survives `-euo pipefail` because `h_mad_collect_report.py` returns 0 on `MISSING`
(`h-mad/scripts/h_mad_collect_report.py:102–111`, inside `_run`, `:48`) and the gate block's own branch is `if ! printf '%s\n' "$COLLECT_OUT" | grep -q '^COLLECT: OK '`.
The `h-mad/tests/test_h_mad_collect_report_docs.py:412` text scan — the `re.findall` inside `test_exec_codex_dispatch_carries_out_log_and_timeout` (`:403`) — is untouched (every later bare `:412` in this document pins that same line in that same file, never a line of this document). Write `doc_block_exec_wire.json` (`command` =
`["python3.11", "-m", "pytest", "tests/test_h_mad_collect_report_docs.py", "-q"]`,
`target_command` = `["python3.11", "-m", "pytest", "-q"]`, `root` = `../..`) with the eight rows below
(design v1.53 §Test Plan wire table). The two pins each spy **both** callees of their wire, so a
caller that keeps one callee and re-implements the other locally is a killed mutant, not a pass.

**Code structure**:
```python
# h-mad/tests/test_h_mad_collect_report_docs.py  (delta)
import h_mad_doc_block_exec as dbe  # noqa: E402  (after the existing sys.path.insert)

def _gate_block() -> dbe.Block:
    return dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))

def _gate_bash_block() -> str:
    return _gate_block().text

def _run_recipe(*, phase: str, cycle: int, report: Path, root: Path) -> dbe.RunResult:
    collector = SCRIPT_DIR / "h_mad_collect_report.py"
    gate = SCRIPT_DIR / "h_mad_audit_gate.py"
    block = _gate_block()
    # the doc addresses the installed skill; point the snippet at this tree
    subbed, _ = dbe.substitute(
        block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(gate))}
    )
    q = shlex.quote
    preamble = (
        f'COLLECT_OUT=$({q(sys.executable)} {q(str(collector))} --surface codex '
        f'--feature f --phase {phase} --cycle {cycle} '
        f'--report {q(str(report))} --project-root {q(str(root))})\n'
    )
    return dbe.run_block(subbed, preamble=preamble, timeout=60.0)

# test_documented_gate_recipe_halts_instead_of_gating_an_empty_path loses its nested
# `run_recipe` and calls `_run_recipe` with the same keyword arguments at the two former call sites; its assertions
# on `.stdout`/`.stderr` are unchanged.
```

**Acceptance Criteria**:
- [ ] AC-6.1 `test_exactly_one_tagged_fence_in_the_tree` (in `test_h_mad_doc_block_exec.py`): opening fences carrying `hmad:exec` equal exactly 1, counted with the module's own `_fence_events` over **`*.md` files only** — a sweep this AC states outright rather than reaching by reference: `Path(REPO_ROOT).glob('*/**/*.md')`, then `rel = p.relative_to(REPO_ROOT)`, keeping `rel.parts[0] in ('h-mad', 'handoff')`, dropping any path with `'archive'` in `rel.parts`, **and dropping any path with a dot-directory component** (`any(part.startswith('.') for part in rel.parts)`). **The filter ships THREE clauses, and each one is controlled separately — one published reading per clause, taken with that clause deleted, never one reading for the composite** (impl-plan audit v41; decision O. An earlier revision of this sentence said "two independent clauses, two independent defects, both measured", which was true of the two defects it was written about and silently left the third clause covered by nothing.) Measured at `4e4a00c` by deleting one clause at a time from the glob side and, where it appears there too, from the `git ls-files` side: **(a)** `rel.parts[0] in ('h-mad', 'handoff')` — **controlled**, 30 with the clause against **2097** without it on v1.48's working tree (2075 when the control was first taken at `4e4a00c`; the without-clause integer is not sha-reproducible and its shape is stated immediately below), and both members contribute (27 `h-mad` + 3 `handoff` = 30, re-derived on v1.48's working tree, which is byte-identical to `700c599` over these two roots — `git status --porcelain -- h-mad handoff` is empty), so neither is carried by the other. **The without-clause integer is UNBOUNDED, and that is its stated shape rather than a caveat on a number** (impl-plan audit v43): with the root clause deleted the glob walks *untracked* files, so the reading is **a property of a working tree at a moment, not of any sha** — `git show <sha>` cannot reproduce it and no re-run is expected to agree with a previous one. It **rises with untracked `docs/` writes** by the concurrent agents this phase dispatches, and falls again whenever those files are committed or cleaned, so a reader who gets a fourth number has the expected behaviour and not a defect. Datings, kept as illustration only and **deliberately frozen at four rather than extended every round**: 2075 at `4e4a00c`, **2076** at `68a70d6`, **2079** on v1.45's working tree, and **2088** on **v1.46's**, one round later. The live reading is the one at the control above, taken on the working tree that ships; extending this list each round is the treadmill the unbounded characterisation replaced, and the last entry names the revision it belongs to rather than "this" one (impl-plan audit v44). **Nothing in this AC's conclusion is a function of which one you get** — see the next sentence. Every other integer in this paragraph (30 / 30 / 35 / 0) is a function of tracked state or of the `.pytest_cache` set the AC names outright. The control's conclusion is unmoved by which of them you get — no cardinal is written for that list, because the list is open-ended by construction and a cardinal beside it is a second authority that drifts at the next dating (decision H) — the root clause separates 30 from two thousand, and the 30 side is exact at every one of them; **(b)** the dot-directory clause — **controlled**, 30 with against 35 without, the five additions being exactly the five named paths below; **(c)** `'archive' not in rel.parts` — **UNCONTROLLED, and it is a stated blind arm rather than a claim**. Deleting it moves none of the four dated integers: the `p.parts` form stays **0 → 0**, the rel-rebased dot-excluded set stays **30 → 30** against a `git ls-files` side that also stays **30 → 30** when `grep -v '/archive/'` is dropped from it, and the dot-clause-dropped count stays **35 → 35**. The reason is measurable, not inferred: at this sha `git ls-files -- h-mad handoff | grep '\.md$' | grep -c '/archive/'` is **0** and the glob's archive-drop set is `[]`, so the clause drops nothing on this tree, and it sits on **both** sides of invariant (ii)'s equality, where it cancels. **A clause that drops zero paths here cannot be positively controlled here at all** — the same disposition the tab arm gets in Conventions. So the clause is prescribed **by the definition**, not by any measurement in this document: a 5d implementer who omits or misspells it gets a byte-identical corpus at this sha and AC-6.1 still asserts exactly 1, and the first `archive/` `.md` added under either root is where that silence ends. *The rebase*: this document's `REPO_ROOT` is **absolute** (`REPO_ROOT = Path(__file__).resolve().parents[2]`, Conventions), while the plan's census walks `Path('.')` from the repository root, so the transcribed `p.parts[0] in ('h-mad', 'handoff')` read `parts[0] == '/'` here and selected **nothing** — the AC would still have predicted 0 correctly at RED and could never have reached 1 at GREEN. `'archive'` is rebased with it, or it would test the components of the absolute prefix. *The dot-directory exclusion*: without it the sweep also walks the five gitignored `.pytest_cache/README.md` artifacts that exist on any tree where pytest has run — build output, not documentation, and not something a cardinality-1 guard should count. **The check is a RELATION, not three integers** — the corpus is a growing tree and every absolute count written here is stale within a day (this AC carried 0/30/25 through v1.36; at `335f535` the same three commands print 0/35/30, moved by this session's own `h-mad/agents/*.md` commits). The three invariants, each re-derived at `335f535` from the repository root: (i) the **absolute base** keeps **zero** files — `p.parts[0]` is `'/'`, never `'h-mad'` — which is why `rel` is load-bearing; (ii) the `rel`-rebased, dot-excluded set is **identical** to `git ls-files -- h-mad handoff | grep '\.md$' | grep -v '/archive/'` (symmetric difference **empty**), an agreement of today's tree rather than of the definitions; (iii) dropping the dot clause adds **exactly** the five gitignored `h-mad/.pytest_cache/README.md`, `h-mad/scripts/.pytest_cache/README.md`, `h-mad/tests/.pytest_cache/README.md`, `handoff/.pytest_cache/README.md` and `handoff/tests/.pytest_cache/README.md` — nothing else. Re-run to check, and compare the three against each other rather than against a constant: `python3 -c "from pathlib import Path; R=Path('.').resolve(); print(len([p for p in R.glob('*/**/*.md') if (r:=p.relative_to(R)).parts[0] in ('h-mad','handoff') and 'archive' not in r.parts and not any(x.startswith('.') for x in r.parts)]))"` from the repository root must equal `git ls-files -- h-mad handoff | grep '\.md$' | grep -v '/archive/' | wc -l`; dropping the dot clause must exceed it by exactly the five named paths; and using `p.parts` in place of `r.parts` must print `0`. **Dated example, `335f535`, 2026-09-04**: those four commands printed **30**, **30**, **35** and **0**. **Re-derived at `700c599` for v1.48 rather than carried** (the tree has not moved — `git diff --name-only 74e126f 700c599 -- h-mad handoff` is empty, and `git status --porcelain -- h-mad handoff` over the working tree the readings were taken on is empty too): the same four print **30**, **30**, **35** and **0**, with the symmetric difference empty and the five dropped paths exactly the five named below. **This defect is LATENT, not live** — worth stating precisely, because a 5d implementer must not go looking for a failing test. No `.pytest_cache/README.md` carries `hmad:exec` (re-checked over all five at `335f535`: 0 hits each), so the cardinality-1 assertion passes today and would have passed at Task 5 GREEN on the dot-inclusive sweep too. What is wrong is that the **set the test walks is machine-state-dependent** — the tracked count on a clean clone, five more after anyone has run pytest (30 vs 35 at `335f535`) — so a future tool that drops a generated `.md` under those roots silently enters an assertion that is supposed to be exactly 1. **Which realisation this is, and why it differs from the other**: this feature uses the exclusion in two places and the two are deliberately not the same command. The *measurement* corpus is `git ls-files -- h-mad handoff` filtered to `*.md` with `archive/` excluded — 25 files when it was measured at `1861157`, 30 at `335f535` — because a one-off human measurement has every reason to describe the tracked tree. This AC transcribes the **guard** realisation, the dot-directory exclusion, because a test must still count a tagged fence in an `.md` that has been **written and not yet committed**, which is precisely the accident it exists to refuse and precisely what `git ls-files` would miss. The two agree on this tree and are not the same predicate: re-derived at `335f535`, the dot-excluded glob set and the `git ls-files` set are **identical** (symmetric difference empty, both 30) — an agreement of today's tree, not of the definitions, and it is the definitions the test must implement. **The `*.md` restriction is load-bearing, not tidiness.** (It is no longer stated as "the scope of the census this AC is bound to": reaching a scope by reference imports whatever the referent later becomes, which is how the dot-directory contamination arrived in this AC in the first place, so the sweep is spelled out above instead.) By Task 5, Tasks 1–4 have landed `h-mad/tests/test_h_mad_doc_block_exec.py` under `h-mad/`, and its fixtures carry ` ```bash hmad:exec ` as a column-0 line inside triple-quoted Python strings (AC-1.1's tagged/untagged pair, AC-1.5's section fixtures, AC-1.7's duplicate-heading fixture, AC-3.7's `shell=fish` and `hmad:exec hmad:exec` fixtures). By this feature's own grammar a 0–3-space marker run **is** an opener regardless of the enclosing file's suffix, so an unrestricted sweep counts every one of them and the AC could never pass at GREEN. Worse, the count would not even be the sum of the per-fixture counts: one fixture is a deliberately *unbalanced* four-backtick fence (`test_docsections_unbalanced_four_backtick_fence`), so a whole-file scan of the `.py` carries fence state across fixture boundaries. The scoping rule follows from what `_fence_events` is: a **markdown** scanner whose only inertness rules are markdown ones (a four-backtick fence, a `~~~` fence, a 4-space indent). A Python triple-quoted string is not one of them, so a non-`.md` holder of a fixture is a false positive **by construction**, not an accident of this feature. **Residual, stated exactly**: the sweep does not cover non-`.md` files under the two roots (`.py`, `.sh`, `.json`, `.txt`), `.md` files outside `h-mad/` and `handoff/` (this document and its siblings under `docs/` among them), anything under `archive/`, or anything under a dot-directory — so a tagged fence written into `.pytest_cache/` or any other dot-directory is uncounted, which is the intended trade for not counting build output. The converse is the live edge: **a generated `.md` written under the two roots *outside* a dot-directory IS counted**, correctly — it is then part of the executed documentation surface — but noisily, and if a tool ever starts emitting one this assertion is where it will surface. The guard is "exactly one tagged fence in the executed documentation surface", not "in the repository" — the right scope, because a tagged fence is only ever reachable by a consumer that scans a `.md` doc. **No clearance and no debt against a sibling is stated here** — that is cycle content, not document content (Conventions). What this AC states is its **own** constraint, with the sibling reached by a locator rather than a claim: the dot-directory exclusion is prescribed for **this sweep specifically**, and the design's Test Plan row for AC-6.1–6.6 that carries it is located with `grep -n 'The sweep excludes build output' docs/02-design/features/doc-block-exec.design.md` (one hit, verified at `700c599`). Earlier revisions carried the same scope as three separate assertions about what the design, the spec and the plan currently say; all three are dropped, because this document adopted their scope on its own terms and a sentence describing a sibling's present state expires the moment that sibling is revised. Under this restriction the RED prediction below is true as stated: re-derived at `335f535`, `grep -rn 'hmad:exec' h-mad/ handoff/` returns **0** hits, so before Task 5's SKILL.md edit the `.md` count is zero.
- [ ] AC-6.2 `test_exec_block_scan_performs_no_execution`: it installs a spy over `dbe.run_block` and a recording pass-through over `dbe.subprocess.run`, then **drives the scan by calling `test_exec_codex_dispatch_carries_out_log_and_timeout()` directly** — the `:403` test that owns the `:412` scan, which takes no fixtures and so is callable as a plain function — and asserts both recorders are empty. Calling the existing test rather than re-implementing its body is what keeps `exec-scan-executes`'s anchor valid: the mutant is applied inside that function, so a killer that re-implemented the scan locally would never see it. **This `run_block` spy is the one spy in this document that is NOT a recording pass-through**: it records `(block, kwargs)`, returns `None`, and never calls the real `dbe.run_block`. A pass-through here would execute the exec block from inside the killer itself under `exec-scan-executes`, which is exactly what the row's safety note forbids — the same class of rule as binding `real_rmtree`/`real_killpg` before their patches. **Of the two recorders, the `dbe.run_block` spy is the discriminator and carries the whole kill; the `dbe.subprocess.run` recorder is a belt that `exec-scan-executes` cannot trip**, because `run_block` spawns through `subprocess.Popen` and never through `subprocess.run` (Task 3's code structure). It stays in the assertion as a guard against a *different* mutant — one that reaches for `subprocess.run` directly from the scan — and its emptiness must never be read as evidence about this row. And `test_only_the_exec_scan_hand_rolls_extraction` (exactly one `re.findall(r"```bash` in the file's source, and it is not inside `_gate_block`/`_gate_bash_block`/`_run_recipe`).
- [ ] AC-6.3 the four existing behaviours — `COLLECT: OK` guard before gating, delivered-report `GATE: PASS`, undelivered `report_not_collected` halt without reaching the gate, no shell-killing bare `exit` — still pass, driven through the preamble boundary.
- [ ] AC-6.4 `test_suite_floor_holds` (in `test_h_mad_doc_block_exec.py`): `subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=REPO_ROOT, env={**os.environ, "DOCBLOCK_FLOOR_INNER": "1"})` — **from the repository root**, the cwd the baseline was measured in (`python3.11 -m pytest --collect-only -q -p no:cacheprovider | tail -1` → `2748 tests collected`, re-measured 2026-09-04 at commit `b7d0d77`; the same command from `h-mad/` reports 2486, a different rootdir and a different number). **The paired design, plan and spec pin this same 2748 at `e8eaf6f` and this document pins it at `b7d0d77`; that is not drift, and it is deliberate** (impl-plan audit v34, raised by the design author). `b7d0d77` is the single commit after `e8eaf6f`, and **no test function entered or left the tree across that span — the INVARIANCE is measured here and the ABSOLUTE is not, and the two are labelled separately** (impl-plan audit v43). The predicate is published, and it is **re-run at `700c599` for v1.48** against all three commits without a checkout: `git grep -hE '^\s*def test_' <sha> -- '*test_*.py' | wc -l` returns **1450 at `e8eaf6f`, 1450 at `b7d0d77`, 1450 at `1861157`** — flat, which is the whole of what the two provenances below need. **It does not return 2675.** An earlier revision of this sentence published that same command as the derivation of **2675** and called the result `verified`; the command was never run against it, and running it falsifies the derivation. **`2748`, `2486` and `2675` are therefore all three INHERITED-UNVERIFIED at this site**, which is the label the 5f note carries for them — restated *here* because this is the site a 5c/5d implementer transcribes them from, and by the rule v1.46 wrote over the class and v1.47 widened, **a figure in that register carries the label at every SITE that uses it — an AC, a gate recipe, a note, anywhere — and is described as `verified` nowhere.** The scope is "every site" and not "every AC site": the earlier wording did not reach the §Verification (Phase 5f) gate paragraph, which is the paragraph a 5f operator actually reads and which carries `2748` and `2486` as the pair it runs against. **Residual, as a category rather than as a doubt**: the predicate that does produce 2675 could not be constructed. Eight readings of "counting `def test_` across every `test_*.py` in the tree" were first run at `e8eaf6f` for v1.46 and every one of the eight re-run against that same commit for v1.48 — anchored in `test_*.py` **1450**, unanchored in `test_*.py` **2721**, anchored over all `*.py` **1455**, unanchored over all `*.py` **2748**, unanchored over `*test*.py` **2731**, unique **names 2691** — `git grep -hoE 'def (test_[A-Za-z0-9_]*)' e8eaf6f -- '*test_*.py' | sort -u | wc -l`, where the `-o` **name extraction** is what makes the reading re-runnable and is named because it is not inferable from the phrase "unique names": `sort -u` over whole *lines* gives 2697, not 2691 — `async`-inclusive **1474**, unanchored over every tracked file **2808** — and **none of the eight is 2675**. (The fourth of those readings is a **grep-hit count over `*.py` source text**, not a collected count; its numerical collision with the `2748` baseline named above is a coincidence of this tree and corroborates nothing. It is listed because an enumeration with a member quietly dropped is not an enumeration.) `grep -c '2675'` over the design, the plan and the spec at `700c599` is **0 / 0 / 0**, so nothing external corroborates it either. So 2675 is **not refuted — only its published derivation is**, and the number stands as inherited while the word `verified` is not earned by it. A function count and a collected count differ by parametrised expansion, which is why the floor is stated as a *collected* count; that relation is general and does not rest on either integer being right. Each of the four documents names the commit **it actually measured at**, which is the rule the floor exists to enforce — re-pinning this one to `e8eaf6f` would make it claim a measurement it did not run. A reviewer comparing the four should read one number with two honest provenances, not two numbers. **`2748` is the repository-root count and only the repository-root count**: `cwd=REPO_ROOT` in the call above is load-bearing, and `2486` is never a substitute for it — a reviewer who runs the baseline from `h-mad/` gets 2486 and will read the floor as wrong when it is the directory that was wrong (observed, impl-plan cycle 19). **The number is stated with the commit it was measured at, and it is RE-MEASURED at 5c branch time rather than copied from here — the same rule, and the same reason, as the SKILL.md line pins above.** A floor baseline is a count over a tree that keeps growing: 2747 was measured at `6b4df35`, `b59e05e` then added one test (`h-mad/tests/test_h_mad_assemble_audit.py`, verified: that commit adds exactly one test), and against a real 2748 the assertion `≥ 2747 + the module's own collected count + 7` (the tuple as it then stood) silently permitted **one** deletion — a floor that is stale by N tolerates N deletions, and tolerates them invisibly, which is the one failure mode this AC exists to prevent. So the residual is stated exactly: a stale-by-N floor is not a failing test, it is a **weakened** one, and nothing in the suite can detect that. The implementer re-runs both commands at 5c, writes the two numbers with the 5c sha beside them, and uses the repository-root number as the constant; if it differs from 2748 that is expected drift, not a finding. With `DOCBLOCK_FLOOR_INNER=1` making the inner instance of this test skip; asserts the collected count ≥ the 5c-measured repository-root baseline (`2748` at `b7d0d77`) + the collected count of `h-mad/tests/test_h_mad_doc_block_exec.py` alone (a second `--collect-only` from the same cwd) + **`len(tuple)`**, and that **each member of that tuple is present**. **The addend is `len(tuple)`, never a hand-written integer**: a literal is a second authority that drifts against the enumeration beside it — which is exactly how the previous `+ 7` came to disagree with its own list — while `len(tuple)` cannot. The tuple is enumerated in full here because this is a **test**, and a test needs concrete node IDs to assert on; membership, however, is not decided here (see below). The members, as full node IDs relative to the repository root:
`h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_resolves_through_doc_block_exec`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_recipe_runs_through_run_block`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_refuses_an_untagged_recipe`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_exec_block_scan_performs_no_execution`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_consumer_calls_the_helper_module_qualified`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_only_the_exec_scan_hand_rolls_extraction`,
`h-mad/tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`,
`h-mad/tests/test_h_mad_portable_timeout.py::test_no_document_or_script_emits_a_bare_timeout_command[h_mad_doc_block_exec.py]` and
`h-mad/tests/test_h_mad_portable_timeout.py::test_no_document_or_script_rests_on_an_unconditional_absence_claim[h_mad_doc_block_exec.py]`.
**This document writes no total for that tuple.** The assertion's addend is `len(tuple)` and nothing else; a written total anywhere in *this* document would be a second authority beside the enumeration above, and that is what the fix is. "Seven" was the instance and it went stale the moment a second source of members was noticed; "nine" would go stale the same way the moment this feature adds a second script. **A stated total is not forbidden in general** — it is admissible as a *dated evaluation that names the commit it was evaluated at*, a form no reader can mistake for the contract; what is inadmissible is a bare integer standing where `len(tuple)` stands. This sentence says nothing about what any sibling document contains: the earlier form of it claimed no total was written "here or anywhere", which is a present-tense claim about siblings and so the very class the Conventions rule above forbids (impl-plan audit v36 — the rule caught its own author). **Membership is decided by the spec's rule, and this document does not re-word it** — a rule stated twice in two voices is how the 25/30 corpus contradiction started. The spec's AC-6.4 states it as two sources: nodes added **directly** to a consumer file, plus **one node per glob-parametrised test per new file this feature adds under `h-mad/scripts/`**, the latter required to **pass** rather than merely be counted. Locate it with `grep -n 'One node per glob-parametrised test' docs/01-plan/features/doc-block-exec.spec.md` (one hit, verified at `700c599`); that is the authority, and the enumeration above is this document's application of it to the files Task 1 through Task 5 actually land. **The tuple is therefore re-derived at 5c, not copied from here** — the same rule already stated above for the `2748` baseline, now extended to cover membership: at 5c the implementer re-runs the glob enumeration below against the branch, and for **each** `h-mad/scripts/*.py` file the feature actually landed adds one node per glob-parametrised test over that directory. If the feature lands a second script the tuple grows by two and `len(tuple)` follows it with no edit to the assertion; if it lands none beyond `h_mad_doc_block_exec.py` the tuple is exactly the members enumerated above. That is what makes this fix survive the next increment instead of repeating at it.
**Why the two portable-timeout nodes are members at all**, re-derived at `335f535`: `h-mad/tests/test_h_mad_portable_timeout.py:40` binds `SKILL = Path(__file__).resolve().parent.parent` — **this repository's `h-mad/`**, not the installed skill — and `:160` puts `*sorted((SKILL / "scripts").glob("*.py")),` into the module-level `_SCANNED` list, which `:165` and `:295` each consume as `@pytest.mark.parametrize("path", _SCANNED, ids=lambda p: p.name)`. `python3.11 -m pytest h-mad/tests/test_h_mad_portable_timeout.py --collect-only -q -p no:cacheprovider` collects **160** nodes, **58** under each of those two test names, one per `_SCANNED` entry, against **37** files in `h-mad/scripts/*.py` today. Task 1 writes `h-mad/scripts/h_mad_doc_block_exec.py` into that glob, so `_SCANNED` becomes 59 entries and **each** parametrised test gains one node with the id `[h_mad_doc_block_exec.py]`. Both are expected to **pass** on the specified module, which is exactly why the omission mattered: `+ 7` against a true addition of 9 is not a failing test, it is a floor that tolerates **two invisible deletions** — the silent weakening this AC exists to prevent. **The 5c re-measure does not absorb it**: the 5c baseline is taken from the tree *before* Task 1 lands, so `_SCANNED` still holds 37 `scripts/*.py` when it is measured, and the `+ 9` constant is not re-measured at 5c at all.
**Task 1 therefore inherits two guards it did not have before, and both must be satisfied by the module's source** — stated here because they are invisible from Task 1's own AC list: `h_mad_doc_block_exec.py` must contain no line where the word `timeout` is followed by whitespace and a number — the shell **command** form — matched by `_TIMEOUT_CMD = re.compile(r"(?:^|[^-\w])timeout\s+\d+")` at `h-mad/tests/test_h_mad_portable_timeout.py:151` (`timeout=`, `--timeout`, `TimeoutExpired` and `BlockTimeout` are all outside it, and AC-5.3 already forbids invoking `timeout`/`gtimeout` at all), and it must match none of the seven `_ABSENCE_CLAIMS` patterns at `h-mad/tests/test_h_mad_portable_timeout.py:211` — prose asserting that macOS lacks `timeout`/`gtimeout`, which that guard accepts **only** when the word `stock` stands immediately before the claim (the patterns are not restated here, because restating one is how a document trips its own guard). A docstring copied out of the design's rationale is the way this fails at 5d.
**Class and residual, derived at `335f535`, not carried.** The class is *a pre-existing `@pytest.mark.parametrize` whose argvalues come from a filesystem glob this feature writes into*; the rule is to enumerate those globs **before** fixing the constant and add one node per (parametrised test × added file). **The residual is the enumeration of the module-level glob-fed parametrize sources, and that enumeration is complete** — it is derived by AST rather than by grep, because only a module-level call can feed a `parametrize` at collection time and only an AST walk can tell module level from a function body. Across `h-mad/tests`, `handoff/tests` and `handoff/scripts` — the whole of `testpaths` (`pytest.ini:14`) — there are exactly **seven** module-level `.glob`/`.rglob` calls, in **two** files, feeding exactly **two** sources:

````bash
python3.11 -c "
import ast, pathlib
mod, body = [], 0
for root in ('h-mad/tests', 'handoff/tests', 'handoff/scripts'):
    for f in sorted(pathlib.Path(root).rglob('*.py')):
        tree = ast.parse(f.read_text(encoding='utf-8', errors='replace'))
        inside = {id(n) for d in ast.walk(tree) if isinstance(d, ast.FunctionDef) for n in ast.walk(d)}
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('glob', 'rglob'):
                if id(n) in inside: body += 1
                else: mod.append(f'{f}:{n.lineno}')
print('module-level', len(mod), mod)
print('in-body', body)
"
````

At `335f535` that prints `module-level 7` — `h-mad/tests/test_h_mad_audit_cycle.py:18`, `:19`, `:23` (all three inside the module-level `REAL_AUDIT_REPORTS` tuple, `:15`) and `h-mad/tests/test_h_mad_portable_timeout.py:158`, `:159`, `:160`, `:161` (all four inside the module-level `_SCANNED` list, `:153`) — and `in-body 21`. The four in `test_h_mad_portable_timeout.py` build `_SCANNED` (`:153`), which contributes the `+ 2` above. The three in `test_h_mad_audit_cycle.py` build `REAL_AUDIT_REPORTS` (`:15`, consumed by a `parametrize` at `:1672`), which globs `docs/` and is sliced `[:8]` over **463** candidates at `335f535` — **saturated, so it adds 0**, and this feature's landed source writes nothing under `docs/` in any case. **The other 21 `.glob`/`.rglob` calls are all inside a function body and so add no collection node** — that is the AST walk's own verdict over the same three trees, not a hand-enumerated list, which is what makes it complete. An earlier revision of this paragraph listed eight in-body sites under the words "Every other"; a full walk finds 21, and a 5c or 5d reader who re-ran the sweep could not tell whether the other 13 were missed or excluded (impl-plan audit v36). Two of the 21 are worth naming anyway, because they look like they should matter and do not: `test_h_mad_mutation_harness.py` contains **no** `parametrize` at all and calls both of its spec-globbing helpers from inside test bodies, so `doc_block_exec.json`, `doc_block_exec_wire.json` and the re-pointed `docsections.json` add no node while still being subject to its exact-once anchor sweep; and `h-mad/tests/test_suite_collection.py:81` rglobs `test_*.py` from inside the body of `test_no_declared_skill_has_a_test_directory_left_out` (`:49`), which is where the new test module would otherwise have landed a node.
- [ ] AC-6.5 WIRE-PIN 1 (`test_gate_block_resolves_through_doc_block_exec`): `monkeypatch.setattr(dbe, "extract", spy_extract)` and `monkeypatch.setattr(dbe, "select", spy_select)`, each a recording pass-through to the real function (bound before patching) — calling `_gate_block()` must record exactly one `extract` call with `(SKILL_MD, "## Second surface — the codex leg")` and exactly one `select` call whose first argument **is** the list `extract` returned (identity, `is`) and whose `index` is `None`; the returned block is the one `select` returned. WIRE-PIN 2 (`test_recipe_runs_through_run_block`): `monkeypatch.setattr(dbe, "substitute", spy_substitute)` (a recording pass-through to the real `substitute`) and `monkeypatch.setattr(dbe, "run_block", spy_run)` where `spy_run` records `(block, kwargs)` and returns `dbe.RunResult(rc=0, stdout="", stderr="", shell="strict")` — calling `_run_recipe(phase="plan", cycle=3, report=tmp_path / "r.md", root=tmp_path)` must record exactly one `substitute` call with the gate block (`text` equal to `_gate_bash_block()`) and the one-key map `{"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(SCRIPT_DIR / "h_mad_audit_gate.py"))}`, and exactly one `run_block` call whose block **is** the block `substitute` returned, whose `preamble` contains `COLLECT_OUT=$(`, and whose `timeout == 60.0`. `test_consumer_calls_the_helper_module_qualified`: the consumer's source has no `from h_mad_doc_block_exec import`.
- [ ] AC-6.6 `test_gate_block_refuses_an_untagged_recipe`: with `dbe.extract` monkeypatched to return `[]`, `_gate_block()` raises `dbe.BlockNotFound` (no legacy fallback).
- [ ] `doc_block_exec_wire.json` reports `ALL_CAUGHT` over eight rows. **The four revert rows carry
  type-correct replacement bodies** (impl-plan audit v13): **the `test` key is the named WIRE-PIN for
  all four**, no mutant ever fails through a `NameError`, `AttributeError` or `TypeError`, the
  helper's own suite (`test_h_mad_doc_block_exec.py`) stays green under all four, and each leaves
  the three recipe regression tests green. **Collateral consumer-side failures are listed per row
  below and are expected for `wire-revert-extract` alone** (impl-plan audit v21): it necessarily
  also reds `test_only_the_exec_scan_hand_rolls_extraction` and
  `test_gate_block_refuses_an_untagged_recipe`, because a call site that hand-rolls extraction and
  no longer consults `dbe.extract` cannot satisfy either. For the other three reverts the WIRE-PIN
  is the only failure (`test_gate_block_guards_on_the_collect_token_before_gating`,
  `test_gate_block_does_not_exit_the_operators_shell`,
  `test_documented_gate_recipe_halts_instead_of_gating_an_empty_path`). Every `find` below is the
  code-structure text verbatim, indentation included, and matches the landed source exactly once
  (the harness applies one `str.replace` pair per row).
  **Reading the fenced payloads in this bullet — a rule, because getting it wrong breaks every
  anchor here** (impl-plan audit v27 agy). These blocks are nested inside a markdown list, so each
  one carries **exactly 4 spaces of list indentation that are NOT part of the payload**. Strip 4
  leading spaces from every line of a block and the result is the literal anchor text: a
  module-level payload then starts at column 0 (`def _gate_block() -> dbe.Block:`), and a
  function-body payload at column 4 (`    _bodies = re.findall(`), which is where the landed
  source has them. Verified mechanically across all ten payload blocks in this bullet: the minimum
  indent is 8 for every body payload and 4 for every module-level one, uniformly 4 more than the
  source. Copy a block without stripping and the `find` misses — scored a refusal, not a kill —
  and a `replace` lands an `IndentationError`. `dbe.Block` has **four** fields with no
  defaults (`text`, `shell`, `lineno`, `info`) and `dbe.RunResult` four (`rc`, `stdout`, `stderr`,
  `shell`), so every constructed value names all four.
  - `wire-revert-extract` — `_gate_block` resolves its block with a local, tag-tolerant regex
    instead of `dbe.extract`/`dbe.select`, the callee untouched. `find` is the one line
    `    return dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))`; `replace` is
    ```python
        _bodies = re.findall(r"```bash[^\n]*\n(.*?)```", _second_surface(), re.S)
        _gating = [b for b in _bodies if "h_mad_audit_gate.py" in b]
        assert _gating, "Second surface must contain a bash block that runs the gate"
        assert len(_gating) == 1, f"expected exactly one gating bash block, got {len(_gating)}"
        return dbe.Block(text=_gating[0], shell="strict", lineno=0, info="hmad:exec")
    ```
    The consumer already imports `re` at its `:10` and defines `_second_surface()` at its `:49`, so
    the replacement carries no import. The regex is the pre-migration one made tag-tolerant with
    `[^\n]*`, because the literal pre-migration `re.findall(r"```bash\n(.*?)```")` would simply fail
    on the tagged fence and the wire, not the regex, is what this mutant must discriminate; the
    `"h_mad_audit_gate.py" in b` filter is the pre-migration one too and is **required** — the
    section holds several ```bash fences (four at `b7d0d77`) and the gating one is not the first,
    so a bare `[0]` would return the wrong body and break
    `test_gate_block_guards_on_the_collect_token_before_gating` on its
    `block.index("h_mad_audit_gate.py")`. Returning
    a `dbe.Block` is what keeps `_gate_bash_block() -> _gate_block().text` a `str` for its two text
    pins and keeps the first argument of `_run_recipe`'s `dbe.substitute` call a `Block`. Killed by WIRE-PIN 1's
    empty `extract` record. **Two other tests go red under it by construction**, and both stay
    regression tests rather than the row's `test` key: `test_only_the_exec_scan_hand_rolls_extraction`
    (a second `re.findall(r"```bash` now exists — hand-rolled extraction is exactly what that guard
    forbids) and `test_gate_block_refuses_an_untagged_recipe` (a call site that no longer consults
    `dbe.extract` cannot honour a patched `dbe.extract` returning `[]`). No revert of this wire can
    avoid either, since both assert the absence of the thing the revert restores.
  - `wire-revert-select` — `_gate_block` keeps `dbe.extract` but applies the ordinal policy locally,
    the callee untouched. `find` is the same one line; `replace` is
    ```python
        _blocks = dbe.extract(SKILL_MD, "## Second surface — the codex leg")
        if not _blocks:
            raise dbe.BlockNotFound()
        if len(_blocks) > 1:
            raise dbe.AmbiguousBlock(len(_blocks))
        return _blocks[0]
    ```
    `BlockNotFound` takes no constructor arguments (Task 1 defines it as a bare `DocBlockError`
    subclass) and `AmbiguousBlock(n: int)` takes the count, so both raises are well-formed; mirroring
    `select`'s no-index policy is what keeps `test_gate_block_refuses_an_untagged_recipe` green
    under this row. Killed by WIRE-PIN 1's empty `select` record, and by nothing else.
  - `wire-revert-run` — `_run_recipe` runs `bash` inline instead of calling `dbe.run_block`, the
    callee untouched. `find` is the one line
    `    return dbe.run_block(subbed, preamble=preamble, timeout=60.0)`; `replace` is
    ```python
        import subprocess
        p = subprocess.run(
            ["bash", "-c", preamble + subbed.text],
            capture_output=True, text=True, timeout=60.0,
        )
        return dbe.RunResult(rc=p.returncode, stdout=p.stdout, stderr=p.stderr, shell=subbed.shell)
    ```
    The `import subprocess` is function-local because the hoisted `_run_recipe` has no module-level
    one — the current file imports `subprocess` only inside the old test at `:304`, and that body is
    replaced by `_run_recipe` calls at GREEN. The composed script is `subbed.text`, not a bare
    `script` name that does not exist in the hoisted function, and the return value is a
    `dbe.RunResult` with all four fields, so the two `.stdout`/`.stderr` reads at `:340` and `:346`
    keep working and the recipe regression stays green; the explicit `timeout=60.0` keeps the
    mutant bounded now that WIRE-PIN 2's `spy_run` no longer short-circuits the run. Killed by
    WIRE-PIN 2's empty `run_block` record.
  - `wire-revert-substitute` — `_run_recipe` rewrites the checkout path with `str.replace` instead
    of `dbe.substitute`, the callee untouched. `find` is the three lines
    ```python
        subbed, _ = dbe.substitute(
            block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(gate))}
        )
    ```
    `replace` is
    ```python
        subbed = dbe.Block(
            text=block.text.replace(
                "~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py", shlex.quote(str(gate))
            ),
            shell=block.shell,
            lineno=block.lineno,
            info=block.info,
        )
    ```
    Building a `dbe.Block` rather than assigning the replaced `str` is what keeps the following
    `dbe.run_block(subbed, preamble=preamble, timeout=60.0)` type-correct; the other three fields are carried from `block`, so the
    executed shell mode is unchanged and the recipe regression stays green. Killed by WIRE-PIN 2's
    empty `substitute` record.
  The remaining four rows keep their v1.13 mechanisms; the two that spelled their body as an
  ellipsis are made concrete here for the same reason the four reverts were.
  - `wire-unconditional` — the call site grows a fallback, so an untagged gate block is still
    resolved; the only way a call site can become tag-blind, since no helper API accepts untagged
    fences. `find` is the one line
    `    return dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))`; `replace` is
    ```python
        _blocks = dbe.extract(SKILL_MD, "## Second surface — the codex leg")
        if _blocks:
            return dbe.select(_blocks)
        _bodies = re.findall(r"```bash[^\n]*\n(.*?)```", _second_surface(), re.S)
        _gating = [b for b in _bodies if "h_mad_audit_gate.py" in b]
        assert _gating, "Second surface must contain a bash block that runs the gate"
        assert len(_gating) == 1, f"expected exactly one gating bash block, got {len(_gating)}"
        return dbe.Block(text=_gating[0], shell="strict", lineno=0, info="hmad:exec")
    ```
    Killed by `test_gate_block_refuses_an_untagged_recipe`: with `dbe.extract` patched to return
    `[]` the fallback resolves the block instead of raising `dbe.BlockNotFound`. Both WIRE-PINs stay
    green, because on the real tree `extract` returns the tagged block and `select` is still called.
    `test_only_the_exec_scan_hand_rolls_extraction` goes red with it, by construction — the fallback
    is a second `re.findall(r"```bash` — and stays a regression test, not this row's `test` key.
  - `hand-rolled-extraction-widened` — a second hand-rolled extraction appears on the executing
    path. `find` is the two lines of the landed `_gate_bash_block`
    (`def _gate_bash_block() -> str:` and `    return _gate_block().text`) — the landed function
    carries **no docstring**, unlike today's `:267` version, which is what makes that two-line
    anchor match exactly once; `replace` is
    ```python
    def _gate_bash_block() -> str:
        try:
            return _gate_block().text
        except dbe.DocBlockError:
            _bodies = re.findall(r"```bash[^\n]*\n(.*?)```", _second_surface(), re.S)
            return [b for b in _bodies if "h_mad_audit_gate.py" in b][0]
    ```
    Killed by `test_only_the_exec_scan_hand_rolls_extraction` — two `re.findall(r"```bash` now
    remain in the file rather than the one `:412` scan. Both WIRE-PINs stay green, because the
    `try` arm succeeds on the real tree.
  - `exec-scan-executes` — the `:412` text scan is made to run its selected block through
    `dbe.run_block`. `find` is the one line that follows the scan,
    `    assert exec_block, "Second surface must dispatch the codex leg via exec"` (re-verified at
    `b7d0d77`, 2026-09-04, with `grep -c` → 1: it occurs exactly once in the file, and the scan's own generator line
    `(b for b in re.findall(r"```bash\n(.*?)```", section, re.S) if "exec codex" in b)` at `:412`
    is likewise unique — the migration leaves both untouched, which is why they are still valid
    anchors at GREEN). `replace` is
    ```python
        assert exec_block, "Second surface must dispatch the codex leg via exec"
        dbe.run_block(
            dbe.Block(text=exec_block, shell="plain", lineno=0, info=""), timeout=1.0
        )
    ```
    `shell="plain"` is deliberate: the exec block is not `-euo pipefail`-safe, so `strict` would
    change the behaviour being pinned rather than only adding the execution. All four `Block` fields
    are given, so the call is type-correct and raises no `TypeError`. Killed by
    `test_exec_block_scan_performs_no_execution`, whose `dbe.run_block` spy — installed **before**
    it drives the scan — records exactly the call the guard says can never happen. **Safety, stated
    from the harness source rather than assumed**: on the expected path the harness scores with
    `target_command + [mutation["test"]]` (`h-mad/scripts/h_mad_mutation_harness.py:606–607`, in
    `run_spec`), so only the killer
    runs and its spy absorbs the call. But when a named test **passes** under its mutant the harness
    re-runs the whole-file `command` with the mutant still applied
    (`h-mad/scripts/h_mad_mutation_harness.py:679`, in `run_spec`), and in that run
    `test_exec_codex_dispatch_carries_out_log_and_timeout` (the `:403` test that owns the scan) has
    no spy installed. `timeout=1.0` is therefore the real bound on this row, not the scoring path:
    it caps the dispatch at one second if the killer is ever mis-implemented and the survivor branch
    is taken. Do not raise it, and do not apply this mutation by hand with the whole file selected.
  - `consumer-from-import` — the consumer's module alias is **bypassed, not deleted**: a bare
    `from h_mad_doc_block_exec import` is added inside the call region and every `dbe.` **call** in
    the delta is re-pointed at the imported names, while the alias import at the consumer's `:23`
    stays where it is. That is what the payload below does, and the earlier summary saying the
    alias was "replaced" contradicted it (impl-plan audit v27 agy). Bypassing is what the guard
    forbids and what makes the spies blind, so it is the right mutant; the alias must stay for the
    two `-> dbe.Block` / `-> dbe.RunResult` annotations to resolve. One replacement suffices because all four call sites are
    contiguous. **Both payloads are literal here** (impl-plan audit v24); `file` is
    `tests/test_h_mad_collect_report_docs.py`. `find` is exactly the Task 5 code-structure region:
    ```python
    def _gate_block() -> dbe.Block:
        return dbe.select(dbe.extract(SKILL_MD, "## Second surface — the codex leg"))

    def _gate_bash_block() -> str:
        return _gate_block().text

    def _run_recipe(*, phase: str, cycle: int, report: Path, root: Path) -> dbe.RunResult:
        collector = SCRIPT_DIR / "h_mad_collect_report.py"
        gate = SCRIPT_DIR / "h_mad_audit_gate.py"
        block = _gate_block()
        # the doc addresses the installed skill; point the snippet at this tree
        subbed, _ = dbe.substitute(
            block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(gate))}
        )
        q = shlex.quote
        preamble = (
            f'COLLECT_OUT=$({q(sys.executable)} {q(str(collector))} --surface codex '
            f'--feature f --phase {phase} --cycle {cycle} '
            f'--report {q(str(report))} --project-root {q(str(root))})\n'
        )
        return dbe.run_block(subbed, preamble=preamble, timeout=60.0)
    ```
    and `replace` is exactly that text with one line inserted at the top and the four calls
    re-pointed:
    ```python
    from h_mad_doc_block_exec import extract, select, run_block, substitute  # noqa: E402

    def _gate_block() -> dbe.Block:
        return select(extract(SKILL_MD, "## Second surface — the codex leg"))

    def _gate_bash_block() -> str:
        return _gate_block().text

    def _run_recipe(*, phase: str, cycle: int, report: Path, root: Path) -> dbe.RunResult:
        collector = SCRIPT_DIR / "h_mad_collect_report.py"
        gate = SCRIPT_DIR / "h_mad_audit_gate.py"
        block = _gate_block()
        # the doc addresses the installed skill; point the snippet at this tree
        subbed, _ = substitute(
            block, {"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": shlex.quote(str(gate))}
        )
        q = shlex.quote
        preamble = (
            f'COLLECT_OUT=$({q(sys.executable)} {q(str(collector))} --surface codex '
            f'--feature f --phase {phase} --cycle {cycle} '
            f'--report {q(str(report))} --project-root {q(str(root))})\n'
        )
        return run_block(subbed, preamble=preamble, timeout=60.0)
    ```
    `_gate_bash_block` sits inside the region and is carried through unchanged; the alias import at
    the consumer's `:23` is above the region and is untouched by this row, which is why the two
    `-> dbe.Block` / `-> dbe.RunResult` annotations still resolve. The two `-> dbe.Block` / `-> dbe.RunResult`
    annotations stay as they are and never break: the consumer carries
    `from __future__ import annotations` at its `:8`, so annotations are strings and are never
    evaluated, and this row leaves the alias import at `:23` in place. Behaviour is unchanged — the
    bare names are the same function objects — so every recipe regression stays green. Killed by
    `test_consumer_calls_the_helper_module_qualified` on its source predicate, the row's `test` key,
    since the file now contains `from h_mad_doc_block_exec import`. **Three other tests go red with
    it, by construction, and that collateral red is the hazard the spelling guard exists to
    prevent**: the bare names were bound at import time, so
    `monkeypatch.setattr(dbe, "extract", spy_extract)` and the other three spies are never observed,
    which reds WIRE-PIN 1 and WIRE-PIN 2; and `test_gate_block_refuses_an_untagged_recipe` reds too,
    because its patched `dbe.extract` returning `[]` is likewise bypassed, so the real `extract`
    resolves the tagged block and `dbe.BlockNotFound` is never raised. All three stay regression
    tests, not this row's key.

  All eight mechanisms are the plan's FR-6 table's, and under each of the four reverts
  `test_h_mad_doc_block_exec.py` stays green. The eight rows bind to the same six named tests as
  before (both new rows re-use the two existing pins); no new test name is introduced, so the
  AC-6.4 floor tuple gains no member from this task, and `len(tuple)` with it.

**Dependencies on other tasks**: Tasks 1–4.

**Expected RED split** (in prose). **A wiring pin's RED must be an assertion about the caller's
observable behaviour, never a missing symbol** — this document's own rule, and the one
`h-mad/scripts/h_mad_assemble_tdd.py:238-243`, the `shape == "wiring"` branch inside `assemble`
(`:174`), prints into every wiring dispatch. An earlier draft had both
WIRE-PINs failing with `NameError` because `_gate_block` and `_run_recipe` did not exist yet; that
proves the names are absent, not that the connection is (impl-plan audit v31). So Task 5's RED has
two steps.

**RED step 0 — a pure refactor, no `dbe` call, no new test, suite green; its own commit, landed
before the 5d RED dispatch.** Hoist today's legacy logic under the three new module-level names, so
the callers exist and are callable before any pin runs:

- `_gate_block() -> dbe.Block` resolves the block with today's `re.findall` over `_second_surface()`
  and today's `"h_mad_audit_gate.py" in b` filter, **keeping today's two asserts — the non-empty
  guard and the exactly-one guard — ahead of the subscript**, and wrapping the body as
  `dbe.Block(text=_gating[0], shell="strict", lineno=0, info="hmad:exec")`.
- `_gate_bash_block() -> str` returns `_gate_block().text`, so the two text pins at `:281` and
  `:368` keep their string.
- `_run_recipe(*, phase, cycle, report, root) -> dbe.RunResult` is the hoisted inline path. **Its
  source is a function nested inside a test, not a module-level one**: `run_recipe` at
  `h-mad/tests/test_h_mad_collect_report_docs.py:309`, defined inside
  `test_documented_gate_recipe_halts_instead_of_gating_an_empty_path` (`:294`) with the same
  keyword-only signature. Hoisting it makes today's `str.replace` for the checkout-path rewrite
  wrap back into a `dbe.Block`, then
  `subprocess.run(["bash", "-c", preamble + subbed.text], capture_output=True, text=True, timeout=60.0)`
  under a function-local `import subprocess`, returning
  `dbe.RunResult(rc=p.returncode, stdout=p.stdout, stderr=p.stderr, shell=subbed.shell)`.
  **One thing is added rather than moved, and it is deliberate**: the nested form calls
  `subprocess.run` with no `timeout=` at all, and the hoisted one carries `timeout=60.0`. That is
  the portable time-bounds invariant, and it is also what WIRE-PIN 2 asserts, so a 5d implementer
  who reads "pure refactor" as "copy the bytes" would land an unbounded call and fail the pin.

That scaffold is **exactly the composition of the four `wire-revert-*` bodies**, which the eight-row
bullet above already writes out literally, so nothing new is invented here. Step 0 adds
`import h_mad_doc_block_exec as dbe` — needed for the annotations and the three constructors, and
for nothing else, since no `dbe` **call** exists yet. It adds **no test**. It changes no *recipe* behaviour — the four AC-6.3 recipe behaviours pass
across it and the suite is green when it lands — but it is **not** behaviour-preserving in the
fault path, and that is forced, not accidental (impl-plan audit v34). Today's `_gate_bash_block`
carries two guards:
`assert gating, "Second surface must contain a bash block that runs the gate"`
(`h-mad/tests/test_h_mad_collect_report_docs.py:272`) and
`assert len(gating) == 1, f"expected exactly one gating bash block, got {len(gating)}"` (`:273`)
— both re-read out of the file at `cac6edc` rather than transcribed. **BOTH ARE KEPT, in the
hoisted `_gate_block` and in the mutation payloads alike** (round-eighteen sheet FACT 4 f; codex
impl-plan must 5 at v48). Earlier text here dropped them, on the ground that step 0's body must be
**literally** `wire-revert-extract`'s replacement body for the symmetry claim below to hold — and
that ground was sound while the conclusion was not: **literal symmetry is satisfied by putting the
guards in BOTH bodies, which is what the payload above now spells**, and dropping a guard to buy
symmetry narrows a guard for a formatting reason. Probed on 3.11.8 to make the consequence a
measurement rather than a reading: over zero, one and two matching bodies the unguarded form gives
`IndexError` / the body / the FIRST body, so a DUPLICATED gating fence is silently ACCEPTED, which
is precisely what the shipped consumer refuses. With the guards in place the same three cases give
`AssertionError` naming the fault / the body / `AssertionError` naming the count. There is
therefore no transient window between step 0 and Task 5 GREEN, and at GREEN `dbe.select` restates
both guards as `BlockNotFound` and `AmbiguousBlock(n)`, which is where the "exactly one gating
fence" invariant lives from then on. Step 0 also lands `_gate_bash_block` **without** today's
one-line docstring at `h-mad/tests/test_h_mad_collect_report_docs.py:268`, inside `_gate_bash_block`
(`:267`) — required, not incidental, because
`hand-rolled-extraction-widened`'s exact-once two-line `find` is `def _gate_bash_block() -> str:`
immediately followed by `    return _gate_block().text`, which an intervening docstring would break.

**Step 0 is a separate commit landed after Task 4 GREEN and before the Task 5 5d dispatch — it is
not the first half of the RED commit.** The two readings give different RED gates, so the document
picks one, and the reason is mechanical:
`h-mad/tests/test_h_mad_collect_report_docs.py` is a Task 5 **Production file** (the task header
lists it as one), and `h-mad/scripts/h_mad_assemble_tdd.py --phase red` prints "Write failing tests
only. Do not modify production code." into that same dispatch
(`h-mad/scripts/h_mad_assemble_tdd.py:230`, the `directive` dict inside `assemble`, `:174`). A refactor of that
file cannot sit inside the RED dispatch without contradicting the directive the dispatch carries.
So the order is: step 0 lands first, refactor only, suite green; then the 5d RED dispatch adds the
**eight** new tests and nothing else — the six in `h-mad/tests/test_h_mad_collect_report_docs.py`
(the two WIRE-PINs, `test_gate_block_refuses_an_untagged_recipe`,
`test_exec_block_scan_performs_no_execution`, `test_consumer_calls_the_helper_module_qualified`,
`test_only_the_exec_scan_hand_rolls_extraction`) and the two in
`h-mad/tests/test_h_mad_doc_block_exec.py` (`test_exactly_one_tagged_fence_in_the_tree`,
`test_suite_floor_holds`), which is exactly the split the task header's **Test file** line states.

**RED step 1 — the pins fail on their call records, with the callers present and working.**
WIRE-PIN 1 fails because its `extract` and `select` spies record **nothing**: `_gate_block` resolves
the block without ever consulting the helper. WIRE-PIN 2 fails the same way on its empty
`substitute` and `run_block` records. Both failures are assertions about what the caller did, which
is the contract. Alongside them: `test_gate_block_refuses_an_untagged_recipe` fails, because the
legacy path resolves a block regardless of the tag and never raises `dbe.BlockNotFound`;
`test_only_the_exec_scan_hand_rolls_extraction` fails (two `re.findall(r"```bash` remain, `:270`
and `:412`); `test_exactly_one_tagged_fence_in_the_tree` fails on **zero** tagged fences — measured
at `b7d0d77`, `grep -rn 'hmad:exec' h-mad/ handoff/` returns nothing, and under AC-6.1's `*.md`
restriction the test module's own fixtures are out of scope, so the sweep is genuinely 0 until
Task 5's SKILL.md edit lands.
`test_consumer_calls_the_helper_module_qualified` passes if the alias was written module-qualified,
which makes it a regression guard on the spelling; `test_exec_block_scan_performs_no_execution` and
`test_suite_floor_holds` are regression guards that pass (the scan never executed, and the floor
counts collected tests, which RED already adds); the four AC-6.3 behaviours are regression guards
too.

**The symmetry is the proof.** The 5e connection-only revert is literally RED step 0's scaffold
re-applied to the GREEN tree: apply all four `wire-revert-*` bodies and the consumer is back to
step 0, with the helper and every test untouched. A pin that goes red at RED for a missing call
record and red again under the revert for the same missing call record is discriminating the
**connection**, not the presence of a name. The call-record assertion of each WIRE-PIN is now the
failure mode at **both** ends — RED step 1 and the 5e revert — which is the point; it was
previously described as the revert's alone, when RED failed on a `NameError` instead. Four revert
directions, applied one at a time with helper and tests intact, each with the replacement body
spelled out in the eight-row bullet above and each type-correct at the consumer's boundary:
(1) `wire-revert-extract` — restore the tag-tolerant `re.findall` plus the `h_mad_audit_gate.py`
filter and the two asserts in `_gate_block`, returning the gating body wrapped as
`dbe.Block(text=_gating[0], shell="strict", lineno=0, info="hmad:exec")`
so the consumer still receives a `Block` (WIRE-PIN 1 fails on its `extract` record; the source-shape
guard and the untagged-refusal test go red with it, by construction, and stay regression tests);
(2) `wire-revert-select` — keep `dbe.extract` in `_gate_block` but apply the ordinal policy locally,
raising `dbe.BlockNotFound()` on none and `dbe.AmbiguousBlock(len(_blocks))` on more than one before
taking `_blocks[0]` (WIRE-PIN 1 fails on its `select` record, and nothing else does); (3)
`wire-revert-run` — restore the inline
`subprocess.run(["bash", "-c", preamble + subbed.text], capture_output=True, text=True, timeout=60.0)`
in `_run_recipe` under a function-local `import subprocess`, returning
`dbe.RunResult(rc=p.returncode, stdout=p.stdout, stderr=p.stderr, shell=subbed.shell)` (WIRE-PIN 2 fails on its `run_block`
record); (4) `wire-revert-substitute` — restore `str.replace` in `_run_recipe`, wrapped back into a
`dbe.Block` carrying `block`'s `shell`, `lineno` and `info` (WIRE-PIN 2 fails on its `substitute`
record). Under every one of the four, `test_h_mad_doc_block_exec.py` stays green and the three
recipe regression tests in the consumer stay green;
then the opposite direction (`wire-unconditional`) must fail `test_gate_block_refuses_an_untagged_recipe`.

**RED gate** (run after RED step 0's refactor commit has landed and the suite is green again — step 0 adds no test, so "green again" is unambiguous; one command per file, and both collect, since every name the tests touch already exists): `hmad-dispatch run --timeout 600 -- python3.11 -m pytest tests/test_h_mad_collect_report_docs.py -q` shows both WIRE-PINs failing **on their empty `dbe` call records** — never on a `NameError`, which is what makes this a wiring RED rather than a missing-symbol one — and `test_gate_block_refuses_an_untagged_recipe` failing because the legacy path resolves an untagged block, with the four AC-6.3 behaviours and `test_consumer_calls_the_helper_module_qualified` passing, and `hmad-dispatch run --timeout 600 -- python3.11 -m pytest tests/test_h_mad_doc_block_exec.py -q` shows `test_exactly_one_tagged_fence_in_the_tree` failing and `test_suite_floor_holds` passing. Judge both commands against the full set of failures and passes the split above lists — `test_only_the_exec_scan_hand_rolls_extraction` (failing) and `test_exec_block_scan_performs_no_execution` (passing) included — not against this shorter sketch. Judge it on the pytest summary, never on `$?` alone, and keep the recorded output beside the task as the 5d dispatch's `--out` file; `rc=124` is the wrapper's expiry, not a RED result. This is what `h_mad_assemble_tdd.py --phase red` dispatches, with `--test-path` set to the file named above, `--expect-fail` and `--expect-pass` set to the counts this split states for a new-behaviour task and omitted for a wiring task (Tasks 1 and 5 state their RED in prose, as the assembler allows), `--out` the recorded report kept beside the task, and `--timeout 600`.

---

## Verification (Phase 5f)

```bash
cd h-mad
hmad-dispatch run --timeout 600 -- python3.11 -m pytest tests/test_h_mad_doc_block_exec.py -q
hmad-dispatch run --timeout 600 -- python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/doc_block_exec.json        # MUTATION: ALL_CAUGHT mutations=86
hmad-dispatch run --timeout 600 -- python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/doc_block_exec_wire.json   # MUTATION: ALL_CAUGHT mutations=8
hmad-dispatch run --timeout 600 -- python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/docsections.json           # MUTATION: ALL_CAUGHT mutations=8
# the full suite runs at the REPOSITORY ROOT, not in h-mad/ — see the note below
( cd "$(git rev-parse --show-toplevel)" \
  && hmad-dispatch run --timeout 1200 -- python3.11 -m pytest -q -p no:cacheprovider ) > /tmp/doc_block_exec_suite.log; RC=$?
tail -1 /tmp/doc_block_exec_suite.log; echo "SUITE: rc=$RC"                                  # gate on both
```

**The two roots are different on purpose** (plan audit v62). The scoped run and the three
mutation-harness runs stay in `h-mad/`, because their arguments are `h-mad`-relative:
`tests/test_h_mad_doc_block_exec.py`, `scripts/h_mad_mutation_harness.py` and the three
`tests/mutation-specs/*.json` paths. The **full suite must run at the repository root**, because
that is the cwd the `2748` baseline was measured in and the cwd AC-6.4's floor is defined against:
the same `pytest -q -p no:cacheprovider` from `h-mad/` picks a different rootdir and collects
**2486**, so a green run there would satisfy the gate while silently measuring 262 fewer tests —
it cannot establish the pass half at all. The subshell `( cd "$(git rev-parse --show-toplevel)" && hmad-dispatch run --timeout 1200 -- python3.11 -m pytest -q -p no:cacheprovider )`
does that without disturbing the `cd h-mad` the earlier lines rely on, and the redirect and
`RC=$?` sit outside it, so the log still lands and `$?` is still the wrapper's propagated status
for pytest, not the subshell's `cd`. **The constraint this document states is its own, and it is
stated about this document only** (Conventions form (a)): this document's 5f gate uses the
root-pinned subshell shown above, and the numbers it carries are **2748** (the repository-root
count) and **2486** (the count from `h-mad/`) — the pair this document uses everywhere, and
**both are INHERITED-UNVERIFIED, labelled here as well as at AC-6.4** because this is the
paragraph a 5f operator reads and a label that lives only at the AC does not reach them here.
The third member of that register, `2675`, is not used in this paragraph.
**The pair is stamped at `b7d0d77`, the commit AC-6.4 names beside the command that produced it.**
An earlier form of this sentence stamped it at `1861157` instead — a second stamp for one
measurement, which is a second authority by this document's own rule. The two do not disagree in
value, and that was checked rather than assumed: `git grep -hE '^\s*def test_' <sha> -- '*test_*.py' | wc -l`
run against the three commits without a checkout returns **1450 at `e8eaf6f`, 1450 at `b7d0d77`,
1450 at `1861157`** — flat, so no test function entered or left the tree across that span and a
collected count taken at either commit is the same count. Only one of the two stamps carries the
command, and that is the one that stands. (1450 is *this* predicate's number, not AC-6.4's 2675.
AC-6.4 **does** publish a predicate for 2675 and reports it **falsified** — run, it returns 1450 —
so the position is not that 2675 lacks a published derivation but that its published derivation
does not produce it. What this paragraph verifies is therefore the **invariance**; the absolute is
verified neither here nor at AC-6.4.)
**Four rounds of INHERITED-UNVERIFIED here are now PARTLY DISCHARGED, and the part that is not is
named** (impl-plan audit v41 should-fix, carried at v1.44; impl-plan audit v42, which recorded a
fourth consecutive round with no surface on either leg re-running them). **First executed at
`68a70d6`, at v1.45, and re-executed at `700c599` for v1.48** — both commands run again rather than
transcribed, and the readings below are v1.48's own, not v1.45's carried forward (impl-plan audit
v44: the discharge claim is the one place a stale self-reference costs the most, because it is the
sentence that says a figure stopped being inherited):
`python3.11 -m pytest --collect-only -q -p no:cacheprovider` collected **2809** from the repository
root and **2547** from `h-mad/` at `700c599` — a divergence of exactly **262**, which is the divergence this
paragraph publishes, reproduced on a live tree. The *relation* the floor rests on is therefore
measured, not inherited. **The two ABSOLUTES are not, and both had gone stale by the round-sixteen
freeze without this paragraph noticing** (impl-plan audit v47 should 4): `af19d53` added tests
under `h-mad/tests/test_h_mad_assemble_audit.py`, and the freeze-scope check that cleared this
document across that span did not consider this pair at all. Re-run at `fbc2ea0` with the pinned
interpreter, each scope in its own invocation: **2814** with no path argument from the repository root and **2552** with `h-mad/tests` as the
path argument from that same root, a divergence of **262** again. **The two invocations are named
because the 2547 they replace was taken with `h-mad/` as the CWD**, and a divergence is evidence
only against another divergence of the same grammar. So the divergence is what this paragraph rests on and
it is invariant under an addition — which is the point the paragraph was always making — while the
two absolutes moved +5 each and are now stamped at the commit they were read on rather than left
at `700c599` under a present-tense verb. Three things are **not** verified by that run and are not laundered by it:
the historical values **2748** and **2486** at `b7d0d77`, which would need a checkout of that
commit no authoring pass through v1.48 has taken; **the `2675` function census**, whose published predicate
returns 1450 and is therefore falsified as its derivation, no predicate returning 2675 having been
constructible (AC-6.4 carries the eight readings that were tried, and the register label now stands
at that AC site as well as here); and the plan's 263/76/0 and 268/76/0 heading
differentials with their markdown-it-py CommonMark oracles, which are the plan's figures and are
only **cited**, never re-derived — the word is about the *treatment*, not the *place*: they are
used in Task 1's wire description as well as here, and the register label now stands at that site
too (impl-plan audit v44) — and remain inherited-unverified with no round having re-run them. What the live run
does establish about the historical pair is its **staleness**: the root count moved
**2748 → 2809** between `b7d0d77` and `700c599` and the `h-mad/` count **2486 → 2547**, both **+61**,
and **2809 → 2814** / **2547 → 2552** between `700c599` and `fbc2ea0`, both **+5**, and **2814 → 2836** / **2552 → 2574** between `fbc2ea0` and `cac6edc`, both **+22** (`b39d9dc`, the #87 tooling batch: 4 exec, 3 assembler and 15 agent-definition tests, parametrisation making 22 collected from 15 `def` lines) — re-run at `cac6edc` with the pinned interpreter, each scope in its own invocation, divergence **262** a third time; alongside them `git grep -hE '^\s*def test_' -- '*test_*.py' | wc -l` reads **1527** and `ls h-mad/tests/test_*.py | wc -l` reads **89**. **Every one of those four is a COLLECTION or a SOURCE census and none of them is a passing count** — this document publishes no present-tense "N passed" for the current suite, and the word is chosen rather than loose: at `cac6edc` the h-mad suite collects 2574 and does not run green, because this document's own precheck reading was the failure. By this
AC's own rule a floor stale by N tolerates N invisible deletions, which is exactly why the
constant is re-measured at 5c and never copied from here. Not challenged is still not the same as
verified: what is transcribed above is stamped at the commit it was measured at and named as owed,
never asserted. The
counterpart command in the spec is reached **by name, never by line and never as a requirement**:
`grep -n 'git rev-parse --show-toplevel' docs/01-plan/features/doc-block-exec.spec.md` returns
exactly one hit (verified at `700c599`), and that hit is the line to read. A previous
revision wrote this as "the same root-pinned subshell **must appear** in the spec's AC-6.4 gate
command, and its inline comment **must carry** 2748 and 2486" — a requirement imposed on a
sibling, which is a debt in modal dress and inside the widened Conventions rule above (impl-plan
audit v36); the locator now stands alone and states nothing about what the spec does or should
contain. No sentence here says
what the spec presently contains, and none flags a debt against it: earlier revisions did both —
first a clearance citing a `spec :458` that had already drifted, then a debt ("that comment needs
2747→2748") that spec v1.54 had already paid — and each cost an audit cycle. Under the Conventions
rule those belong in the cycle report, not in this document; three `spec.md:` line numbers went
with them.
**Every 5f command is bounded** through the `hmad-dispatch run --timeout` wrapper shown in the
block above, with the concrete bound on each line (the base Portable
time bounds invariant; `timeout`/`gtimeout` are not macOS components, and AC-5.3 forbids the helper
from invoking either — the wrapper is outside the module's source, so the source scan is unaffected).
The wrapper propagates the wrapped command's exit status and returns 124 on expiry, and it passes
stdout and stderr through unchanged — re-measured 2026-09-03: `run --timeout 5 -- sh -c 'exit 3'`
→ rc 3; `run --timeout 1 -- sleep 3` → `run_timeout`, rc 124; `run --timeout 5 -- sh -c 'echo hi'`
redirected to a file writes `hi` to that file. The full-suite line's subshell form was measured the
same way on 2026-09-03: `( cd "$(git rev-parse --show-toplevel)" && hmad-dispatch run --timeout 5 -- sh -c 'echo hi; exit 3' ) > log; RC=$?`
gave `RC=3` with `hi` in the log, so the `cd` does not swallow the status. So `RC=$?` still captures pytest's own status, the
outer `>` redirect still lands the suite log, and the `MUTATION:` and `SUITE:` tokens are read
exactly as before. Bounds: 600 s for the scoped run and for each of the three harness runs, 1200 s
for the full suite. **The baseline behind that bound is 383 s, not the 397 s this document carried
through v1.34** (impl-plan audit v34, plan-author): the suite runtime was re-measured at plan v1.84
from `2747 passed in 397.40s` at `6b4df35` to `2748 passed in 383.05s` at `e8eaf6f`, and the
derived figure did not move with it — the same class as the floor, a number in prose that outlives
the measurement it was derived from. The plan is corrected at v1.85 — its own 5f bounds
paragraph, located with `grep -n 'Bounds: 1200 s' docs/01-plan/features/doc-block-exec.plan.md` (one hit, verified at `700c599`),
not a line pin — and it names this document as the remaining site; this is that sweep. **The 1200 s bound itself is unchanged and
still reads as intended**: it was just over 3x at the old baseline (1200 / 397.40 = 3.02) and is
just over 3x at the new one (1200 / 383.05 = 3.13), so the correction gives the bound slightly more
headroom, never less, and no expiry that would have passed before now fails. Re-derive it from the
quoted suite output at 5c rather than carrying it. **`rc=124` is the wrapper's expiry, not a suite
result** — a 124 means the command was cut off with no verdict, so it is neither a pass nor a
failure to gate on; re-run it with a larger bound and investigate the hang before reading anything
into the log.

## Version History
- v1.0: Initial implementation plan draft from design v1.50 / plan v1.52 / spec v1.38.
- v1.1: Impl-plan audit v1 (codex must 5 should 1; agy must 2 should 1): docsections delegation merged into Task 1 as a wiring task with a sys.modules-fake WIRE-PIN scaffold; run_recipe hoisted to _run_recipe with dbe.substitute and timeout=60.0; section_from signature; __all__ exports the exceptions; docsections.json gains a syspath mutation (6 rows); counts corrected.
- v1.2: Impl-plan audit v2 (codex must 4; agy clean): transport split — seam-injected verdicts through main(argv) in-process, real-input verdicts through the subprocess, two exit-propagation tests; VERDICT_TABLE at emitted-head granularity (21 heads) plus _VERDICT_FOR by class; fence-aware heading match with its test and mutation (61 rows, design v1.51); suite floor measured from the repository root, the three collect-alone/unbalanced tests moved to the new module so the seven-node tuple stands.
- v1.3: Impl-plan audit v3 (codex must 1 should 1; agy clean): the two consumer pins also spy dbe.select and dbe.substitute, with wire-revert-select and wire-revert-substitute (eight wire mutations, design v1.53); the full exception hierarchy lands in Task 1 so __all__ is complete at its GREEN.
- v1.4: Impl-plan audit v4 (codex must 2 should 1; agy must 1) + design audit v49 (codex must 1, about Task 4): RunResult lands in Task 3 per the design; real_rmtree bound before every rmtree injection; the single-source predicate names marker-run recognition and _FenceEvent gains candidate; argparse imported; _validate_timeout runs before reservation in main and first in run_block, with the artifact-absence assertion in the bad-timeout CLI test.
- v1.5: Impl-plan audit v5 (codex must 1 should 1; agy clean) + design audit v50 (codex must 1, about Task 3): the escapee and in-group fixtures reach esc.py and the pid file through the substitution map (ESC_PATH/PID_PATH), never the child's fresh cwd; the delegation-revert mutant is stated to trip the docsections source guard; the gate-fence locator re-measured.
- v1.6: Impl-plan audit v6 (codex should 2; agy clean): provenance header at design v1.56 / plan v1.57; the ATX heading grammar stated and recognised once in _fence_events as a heading event, with test_heading_lookalikes_are_not_headings and heading-lookalike-accepted (62 rows).
- v1.7: Impl-plan audit v7 (codex must 1 should 1; agy clean) + design audit v53: find_heading is public and titled_section delegates the section start (WIRE-PIN records both calls; docsections.json seventh row); scanner event model stated as the design v1.58 does; the alias refusal leaves closing to the backstop; provenance at design/plan v1.58, grammar corpus cited.
- v1.8: Impl-plan audit v8 (codex must 2 should 1; agy clean): boundary predicate >= start with test_adjacent_heading_bounds_the_section and adjacent-heading-skipped (63 rows); the delegation-revert shim restores both local functions in one replacement; one canonical test key per row; heading differential cited; provenance at design/plan v1.60.
- v1.9: Impl-plan audit v9 (codex must 2 should 1; agy must 1 should 1) + design v1.61: find_heading's two input forms with heading-level-pin-ignored; _FenceEvent start/end offsets; complete variable-field list; stream: detail on stream_close_failed; mktemp/allow-abbrev/stream-write mutations (67 rows); wire-revert-run imports subprocess; the drain records, never raises.
- v1.10: Design audit v58 back-propagation (codex must 1): docsections-delegation-reverted is connection-only — find = the shared import line, replace = a private spec_from_file_location instance of the callee (measured on a scratch pair: recorders [] under the mutant, behaviour unchanged) — with every other test green, the source guard included; the old local-restore shim becomes the eighth row docsections-local-bounder-restored bound to the source guard (docsections.json 8 rows); the docsections delta drops the unused re import.
- v1.11: Impl-plan audit v10 (codex must 2 nit 1; agy clean): docsections-heading-lookup-reverted's one-line replace carries its own `import re;` (the delta dropped the import, so the restored regex would have raised NameError — a fix-introduced defect); 5f expects mutations=8 for docsections.json; version history back in ascending order.
- v1.12: Impl-plan audit v11 (codex must 1; agy must 1) + design v1.64: docsections-delegation-reverted registers its private instance as sys.modules['_h_mad_doc_block_exec_private'] before exec_module (a frozen dataclass under from __future__ annotations fails to load unregistered — reproduced on 3.11.8); RunResult built with keyword arguments; AC-1.7 gains test_bare_form_duplicate_headings_refuse.
- v1.13: Impl-plan audit v12 (codex clean; agy must 2, 44 tool calls): Task 5's wire-row bullet carries the exact tag-tolerant regex for wire-revert-extract and the mechanisms of wire-unconditional, exec-scan-executes, consumer-from-import and hand-rolled-extraction-widened inline, as the plan's FR-6 table states them.
- v1.14: Impl-plan audit v13 (codex must 1; agy clean) + design audit v62 back-propagation (design v1.65): the four Task 5 wire-revert rows carry type-correct replacement bodies with their exact find/replace text — a four-field dbe.Block from the tag-tolerant regex, a local BlockNotFound/AmbiguousBlock ordinal policy, an inline subprocess.run over subbed.text returning a four-field dbe.RunResult under a function-local import, and a str.replace wrapped back into a Block — so each mutant fails only on its WIRE-PIN's call record and the recipe regressions stay green; Task 3 gains the stage=collect mapping for the helper's own communicate/drain/close/wait with its three precedence rules and explicit __context__ assignment, the tests test_communicate_oserror_is_launch_failed_collect and test_drain_wait_oserror_is_launch_failed_collect (instance-level Popen wrapper, escapee fixture for the wait leg) and the rows collect-oserror-unmapped / drain-oserror-unmapped (Task 3 21 rows; 22 + 5 + 21 + 21 = 69, 67 of the helper's source); VERDICT_TABLE gains LAUNCH_FAILED stage=collect (22 heads, 16 subprocess + 6 in-process producers) and SKILL.md a per-stage registry row.
- v1.15: Impl-plan audit v14 (codex must 1 should 1; agy clean) + design audit v63 back-propagation (design v1.67): Task 5's exec-scan-executes and consumer-from-import rows gain exact-once find anchors and complete type-correct replace bodies — the :412 scan's assert line grows a dbe.run_block call on a four-field dbe.Block (shell=plain, timeout=1.0, safe only because the harness runs the row's test key alone with the spy installed), and the _gate_block-through-_run_recipe region becomes one replacement carrying a bare from-import with the four calls re-pointed, which reds the spelling guard and, by construction, both WIRE-PINs; AC-6.2 states that the killer drives the scan by calling test_exec_codex_dispatch_carries_out_log_and_timeout() directly; the fault-injection taxonomy is one authoritative seven (six module-level seams plus the instance-level Popen wrapper), the stale six-versus-seven deferral dropped; heading identity is the CommonMark-normalized text on both forms, with test_closing_hash_run_does_not_change_heading_identity and mutation closing-hash-run-kept (Task 1 23 rows; 23 + 5 + 21 + 21 = 70, 68 of the helper's source).
- v1.16: Impl-plan audit v15 (codex should 1 nit 1; agy clean) + plan audit v55 (codex must 1) + design v1.69 back-propagation: Task 4's failed-second-reservation rollback is verified, not assumed — created tracked per arm, close-then-unlink each guarded so one failure does not skip the other, then an os.path.lexists read-back whose leftover path rides the same stream_path_unwritable verdict as a leftover: detail line (StreamPathUnwritable gains a leftover=None constructor, DETAIL_KEYS 11, a SKILL.md row), with test_rollback_unlink_failure_reports_leftover and mutation rollback-leftover-unreported (Task 4 22 rows; 23 + 5 + 21 + 22 = 71, 69 of the helper's source) and os.unlink as the eighth named seam; every Phase 5f command is bounded through hmad-dispatch run --timeout (600 s scoped and per harness, 1200 s full suite), the wrapper's status propagation, 124-on-expiry and stdout passthrough re-measured 2026-09-03 so RC=$? and the MUTATION:/SUITE: tokens survive; the :412 scan is named with its file; the _FenceEvent comment says event.start >= start.
- v1.17: Impl-plan audit v16 (codex must 2 should 1; agy clean) + design v1.71 back-propagation: StreamPathUnwritable is confirmed as StreamPathUnwritable(leftover=None) with no err positional at any raise site, the OSError travelling as __cause__ via `raise ... from err` and bounded-retry exhaustion raised with no cause (the design's table now agrees, so the cross-document contradiction is closed); Task 3's pre-kill proc.poll() gains its own except OSError guard mapped to stage=collect, the TimeoutExpired handler records the pending BlockTimeout ON ENTRY so a poll failure has something to replace (a derivation — recording it at the end would leave __context__ None), rule (c) names poll beside drain/close/wait and a new rule (d) keeps killpg's reap precedence after a failed poll, with test_poll_oserror_is_launch_failed_collect (instance wrapper on the recorded Popen's poll, kill-then-wait-then-assert teardown because the mutant leaves the group unkilled) and mutation poll-oserror-unmapped, the three collect rows now discriminating mutually (Task 3 22 rows; 23 + 5 + 22 + 22 = 72, 70 of the helper's source; Task 3 injecting tests 11; the poll/communicate/wait wrappers are one instance-level seam, so the taxonomy stays at eight); each of Tasks 1-5 gains a bounded RED gate run before production code, judged on the pytest summary and recorded to the 5d --out file, with Task 1 split into two dispatches because its new module's ModuleNotFoundError is a collection error that would otherwise hide the docsections WIRE-PIN's RED; _run_recipe's collector and gate locals named as derived inside the function.
- v1.18: Impl-plan audit v17 (codex must 1; agy clean) + design audit v66 back-propagation (design v1.73): the fault-injection taxonomy is one canonical eight-item list stated identically to the design — seven module seams (os.killpg, shutil.rmtree, tempfile.mkdtemp, os.chmod, os.unlink, _final_write, _close_stream) plus the one Popen instance wrapper covering communicate/wait/poll — repeated verbatim by the in-process main(argv) transport rule, with the old seventh/eighth-form framing removed; the post-kill wait is proc.wait(timeout=DRAIN_SECONDS), its TimeoutExpired becoming LaunchFailed('reap', err, pgid) with err the TimeoutExpired itself with the pending BlockTimeout or collect as __context__, so LaunchFailed.err is typed OSError | subprocess.TimeoutExpired (the exact union, not BaseException) and os_error: renders str(err); helper wall time is now at most timeout + 2 * DRAIN_SECONDS, and the four existing wall-bound assertions move from 1 + DRAIN_SECONDS + 2 to 1 + 2 * DRAIN_SECONDS + 2; test_wait_after_kill_is_bounded (record-and-raise wrapper on the recorded instance's wait, escapee fixture required so the helper's own wait is the intercepted call, the recorded timeout keyword the discriminator) with rows wait-unbounded and wait-expiry-unmapped, stated as two SEPARATE except clauses on that one wait so each mutation removes exactly one (Task 3 24 rows; 23 + 5 + 24 + 22 = 74, 72 of the helper's source; Task 3 injecting tests 12; four-way mutual discrimination among the collect and bounded-wait rows).
- v1.19: Impl-plan audit v18 (codex must 1 — the reap-sequence contradiction was in the PAIRED PLAN, fixed in plan v1.73; the audit cites impl-plan.md:575-581 as one of the correct sources, so this document needed no change for it and none was made) + design audit v67 back-propagation (design v1.75): every emitted dynamic value passes through one module-level escaper, _field(value), which rewrites \r, \n and every character whose unicodedata.category is Cc to its \xNN/\uNNNN escape and leaves everything else verbatim; all 14 head field names and all 11 DETAIL_KEYS values are routed through it with NO exemption list, so the rule is auditable as 'no value reaches the output un-escaped' rather than as a per-field judgement (the caller- or document-controlled ones it actually protects are heading=, index=, value=, arg=, key=, path=, missing_key:, duplicate_key:, overlap:, os_error: and leftover:); unicodedata added to the module import line; _field is private, so __all__ stays at 28 names and AC-4.5's registry walk gains no row; test_newline_in_dynamic_fields_cannot_forge_a_verdict_line (in-process main over three refusal paths, asserting one DOCBLOCK: line, no forged RAN line, and the payload present ESCAPED — the third assertion being what makes the row discriminating) with mutation field-escape-removed placed after rc-leaked-into-refusal as the design matrix orders it (Task 4 23 rows; 23 + 5 + 24 + 23 = 75, 73 of the helper's source).
- v1.20: Impl-plan audit v19 (codex must 1; agy clean) + design v1.76 back-propagation: the forge test's case (3) is rebuilt on AC-3.10's fixture with the newline moved into the CREATED artifact's name — --stdout a fresh tmp_path file whose name contains \n (a legal POSIX file-name byte, verified on this platform with O_CREAT|O_EXCL + lexists), --stderr under a regular file for the real ENOTDIR on the second arm, os.unlink injected as AC-3.10 injects it — because the previous spelling put the newline on a FIRST-arm ENOTDIR path, which creates nothing and so has no leftover to report, and would have failed against a correct implementation rather than against the mutant; field-escape-removed's discriminator is now stated explicitly (the raw newline in heading=, missing_key: and the leftover: path each split one verdict into two physical lines, so the exactly-one-DOCBLOCK:-line assertion fails on all three cases and the escaped-payload assertion fails independently of how a consumer splits lines); AC-6.4 states that 2747 is the repository-root count and that 2485 from h-mad/ is never a substitute for it. Counts unchanged at 75 rows. The AC header now marks case (3) as injected: os.unlink (cases (1) and (2) need none), correcting a fix-introduced claim of 'no injection' that the rebuilt fixture made false.
- v1.21: Impl-plan audit v20 (codex must 1, low-evidence — REFUTED, and the ground is now pinned) + design v1.77 back-propagation: a new Conventions bullet states WHEN each doc_block_exec.json row's payload is fixed, quoting the design's §Test Plan sentence verbatim — the mechanism and the full-node-ID test key are fixed now, the file, exact-once find and replace are written at 5e from the landed source of the task that just went GREEN, because h_mad_doc_block_exec.py does not exist until 5d and quoting anchors into unwritten source would be the placeholder class this document forbids (a missed find scores a refusal, not a kill, h_mad_mutation_harness.py:609-623); docsections.json and doc_block_exec_wire.json carry payloads already only because their anchors sit in files that exist at HEAD. main refuses the empty --subst key ITSELF while building the map, with raw the argument as given, so --subst =V prints arg==V; substitute keeps BadSubstArg('') for API callers and main never reaches it; test_subst_empty_key_is_bad_subst now states that assertion and mutation cli-empty-key-delegated pins the CLI side, discriminated from Task 2's empty-key-accepted-by-api by which side is mutated (Task 4 24 rows; 23 + 5 + 24 + 24 = 76, 74 of the helper's source).
- v1.22: Impl-plan audit v21 (codex should 1; agy no report) + design v1.78 / plan audit v61 / design audit v70 back-propagation: _field now renders json.dumps(str(value), ensure_ascii=False) — a DOUBLE-QUOTED JSON string with the quotes in the output — so a printable value cannot forge a field token either, closing the gap control-character escaping alone left; of the 25 rendering slots exactly SEVEN stay bare (rc=, blocks=, count=, keys=, shell=, stage=, reason=, the design's list verbatim) and the other 18 are quoted, seconds= and pgid: among them because the design's bare list does not name them and quoting a number never enables a forgery (flagged for the next design cycle); the line grammar DOCBLOCK: <VERDICT> (<key>=<bare>|<key>="<json-string>")* is stated, json replaces unicodedata in the module imports, every example verdict line showing a dynamic value is re-spelled in quoted form, the SKILL.md registry rows show the value form, and the forge test's payload assertion moves inside the quotes; new test test_dynamic_field_cannot_forge_a_token asserts by PARSING the NOT_FOUND line under the grammar to exactly {heading: 'x rc=0'} with no rc field (a substring check would pass under the mutant), with row field-quoting-removed discriminated from field-escape-removed in both directions (Task 4 25 rows; 23 + 5 + 24 + 25 = 77, 75 of the helper's source). Task 5's wire-spec sentence no longer claims each revert's ONLY failure is its WIRE-PIN: the test key is the WIRE-PIN for all four and the helper's suite stays green under all four, but wire-revert-extract necessarily also reds test_only_the_exec_scan_hand_rolls_extraction and test_gate_block_refuses_an_untagged_recipe, which the row already documented and the summary contradicted.
- v1.23: Plan audit v62 (codex must 1, which names THIS document) + impl-plan audit v22 (codex should 1; agy clean) + design v1.79 back-propagation: the Phase-5f full-suite gate now runs at the REPOSITORY ROOT — ( cd "$(git rev-parse --show-toplevel)" && hmad-dispatch run --timeout 1200 -- python3.11 -m pytest -q -p no:cacheprovider ) > log; RC=$? — because the block's opening cd h-mad made it collect 2485 instead of the 2747 baseline AC-6.4's floor is defined against, so a green run there measured 262 fewer tests and could not establish the pass half; the scoped run and the three harness runs stay in h-mad/ since their arguments are h-mad-relative, and the subshell form was MEASURED (RC=3 propagated through the cd, log written) rather than assumed. One path idiom in the docsections delta: the design's spelling sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts")) verbatim, with the docsections-syspath-setup-removed anchor quoting that exact line and the fifth row's spec_from_file_location path using the same Path form, so os is dropped from the delta's imports and pathlib.Path added. The seconds=/pgid: quoting question v1.22 left open is closed: design v1.79 makes the bare list exhaustive and quotes both, as v1.22 had chosen. Counts unchanged at 77.
- v1.24: Impl-plan audit v23 (codex must 1 nit 1; agy clean) + design v1.80 / design audit v72 back-propagation: the universal-renderer sentence no longer contradicts the bare grammar — of the 25 rendering slots, 18 dynamic values go through _field and 7 (rc, blocks, count, keys, shell, stage, reason) are rendered bare by construction as the exhaustive exemption, stated in both directions (no other field is bare, no bare field reaches _field); _field is json.dumps(str(value), ensure_ascii=False) with the str() called out as load-bearing, since json.dumps(3) emits a bare 3 and an int would otherwise leave the grammar unquoted; AC-4.2's subclass walk asserts membership BY CLASS and instantiates nothing, so StreamPathUnwritable's leftover=None default is justified by its raise site (the reservation raises it bare, from the OSError) rather than by a test, and no other subclass is forced to be zero-argument constructible; every example verdict and detail line is rewritten in the quoted grammar (failed: "stdout", skipped: "stderr", verify: "stdout", stream: "stdout", os_error: "<text>", pgid: "<n>", seconds="1.0"), including the joined written/skipped lists; DETAIL_KEYS lets tests enumerate all ELEVEN, not three. Two design-internal disagreements surfaced rather than silently absorbed: its verdict table still shows BAD_INFO key=<k> bare and overlap: "<a>" <b> half-quoted, both of which the design's own exhaustive list contradicts, so this document quotes them and flags the two table rows for the next design cycle. Counts unchanged at 77.
- v1.25: Impl-plan audit v24 (codex must 1 nit 1; agy clean) + design v1.82 / design audit v73 back-propagation: docsections-local-bounder-restored and consumer-from-import now carry COMPLETE LITERAL find/replace payloads as fenced blocks, since both anchor in source that exists at HEAD plus deltas this document already writes out; the Task 1 delta gains titled_section's and section_from's real docstrings, quoted from docsections.py:46-52 and :60-65, so the delta and the local-bounder find are ONE literal shape (the nit). _field gains a SECOND PASS after json.dumps, rewriting every remaining Cc/Zl/Zp character to \uXXXX, because json.dumps leaves U+0085, U+2028, U+2029 and U+007F literal and str.splitlines() breaks on the first three — MEASURED here: one verdict line split into FOUR pieces without the pass and ONE with it — so unicodedata returns to the imports, with test_unicode_line_separators_cannot_split_a_verdict_line (asserting on .splitlines(), which is the splitter that breaks) and row c1-escape-removed, discriminated from field-escape-removed by character class. AC-3.10's two rows are re-bound: a reader-less FIFO fails at os.open with ENXIO and never reaches the S_ISREG check (measured), so nonregular-stream-accepted moves to the new test_stream_path_char_device_refuses (--stdout /dev/null, which opens and fstats as a character device — measured) and the FIFO test keeps stream-open-blocking alone; each row now has a killer that reaches its guard (Task 4 26 rows; 23 + 5 + 24 + 26 = 78, 76 of the helper's source). The local-bounder replace block sits in a FOUR-backtick fence: its restored toggle contains the literal ``` and a three-backtick fence closed on it, truncating the payload — caught by parsing every fenced python block in this document with ast, which is also how both find blocks were verified byte-identical to the deltas they anchor on.
- v1.26: Impl-plan audit v25 (codex must 1 should 1; agy clean) + design v1.83 back-propagation: duplicate-heading-takes-first now names ONE test key, tests/test_h_mad_doc_block_exec.py::test_duplicate_headings_refuse, with test_bare_form_duplicate_headings_refuse demoted to a regression test on the same guard, stated at the row, at the AC and in the Conventions bullet — whose earlier claim that a sweep 'found no other row naming two tests' was FALSE and is replaced by the two pairs that actually exist (this one and final-write-close-not-in-finally). The docsections-local-bounder-restored provenance is corrected: _fence_aware_end IS today's :33-42 body character for character (only its :32 docstring omitted, which the source guard does not read), but _find_heading is NOT today's text — grep -c 'def _find_heading' on today's docsections.py returns 0, the lookup being an inline re.search inside titled_section at :53 — so the revert LIFTS that inline regex into a function to give the two re-pointed call sites a name, behaviour-identical (same pattern, same match.end(), same len(match.group('marks')), None where today falls through to its assert). The payload is unchanged; only the false provenance claim was. Also flagged: the spec's AC-6.4 gate command is bounded but carries no repository-root pin, so it would collect 2485 from h-mad/ — this document's 5f block keeps the pin and the divergence is noted for back-propagation. Counts unchanged at 78.
- v1.27: Impl-plan audit v26 (codex must 1 should 1; agy clean) + design v1.84 / design audit v75 back-propagation: find_heading's two forms are told apart BY THE REQUEST, full form first — a request that parses as an ATX heading line (0-3 spaces, 1-6 #, a space) IS the full form, always, and only a non-parsing request is read as bare, using the scanner's own predicate so the dispatch cannot drift from the recognition; the one documented consequence is that a heading whose title itself begins with an ATX prefix (### ## Text) is reachable only in full form, harmless to every live caller (none of titled_section's targets begins with #, measured). Without the precedence the request ## Text had two incompatible meanings and a document holding both would refuse rather than answer. Added test_heading_form_precedence_full_wins (both lookups return their own heading and NEITHER raises AmbiguousHeading — that last clause is the discriminator, since a positives-only test would pass against the mutant) and row form-precedence-bare-first before closing-hash-run-kept, discriminated from heading-level-pin-ignored (Task 1 24 rows; 24 + 5 + 24 + 26 = 79, 77 of the helper's source). --subst =V prints arg="=V" under the quoted grammar and cli-empty-key-delegated's discriminator is arg="" versus arg="=V", never a bare arg==V. The 5f note claiming the spec lacked the repository-root pin is removed: spec v1.50 back-propagated it and :458 carries the same subshell, so the three documents agree.
- v1.28: Impl-plan audit v27 (codex must 1; agy must 1 + should 2) + design v1.85/v1.86 and plan audit v67 back-propagation. The full-form request predicate is LITERALLY the scanner's — 0-3 spaces, 1-6 #, then a space, A TAB OR END OF LINE — called rather than restated, with test_full_form_request_accepts_tab_and_eol (a ##<TAB>Text heading and a title-less ##) and row request-predicate-space-only, because a space-only predicate scanned those headings and then could not name them. The Task 1 delta drops its two inline call-site comments so the delta and docsections-local-bounder-restored's find are byte-identical (re-verified programmatically); what the comments said moved to prose. BadArgs joins the hierarchy: the parser is ArgumentParser(allow_abbrev=False, exit_on_error=False) with error() overridden to raise it, rendered DOCBLOCK: BAD_ARGS message="<m>" at exit 0 so no non-DOCBLOCK exit survives, with test_malformed_invocation_is_a_verdict (unknown option, missing value; the NO-USAGE clause is the discriminator) and row argparse-error-unrouted. Dependent counts: exceptions 19->20, __all__ 28->29 (design v1.86 and plan v1.82 already say 29, so nothing is owed upstream), verdict heads 22->23, head fields 14->15 and rendering slots 25->26 (7 bare + 19 quoted, message= quoted), plus a BAD_ARGS registry row. The rollback compares os.lstat's (st_dev, st_ino) with the created descriptor's fstat identity before unlinking and reports leftover: on mismatch — stated as a POLICY constraint with no test by construction, since reaching it needs a ninth seam for an explicit non-goal. Two agy should-fixes also fixed: consumer-from-import's summary said the alias was 'replaced' while its payload BYPASSES it, and the ten fenced payloads in the wire bullet carry exactly 4 spaces of markdown-list indentation that are not part of the anchor — measured across all ten and now stated as a rule, since copying them unstripped makes every find miss. Task 1 25 rows, Task 4 27; 25 + 5 + 24 + 27 = 81, 79 of the helper's source.
- v1.29: Impl-plan audit v28 (codex must 1 should 1 nit 1; agy must 1 should 1) + design v1.87 back-propagation. The parser AC is rewritten to the declared contract: test_parser_rejects_all_dir_and_abbreviations now asserts one DOCBLOCK: BAD_ARGS message="<m>" line and exit 0 for each of --all, --dir x and the abbreviation, where it formerly promised argparse usage at exit 2 — a direct contradiction of the VERDICT_TABLE, the design and argparse-error-unrouted. The abbreviation case gets a COMPLETE otherwise-valid argv (doc, --heading, --shell-t 5) so that under allow-abbrev-restored the alias is accepted and the run proceeds to the fixture's own verdict, a visibly different outcome; with an incomplete argv the mutant would still fail, merely later and on a missing required argument, and the row would be caught by the wrong assertion. Both teardowns that wrote a bare SIGKILL argument to real_killpg now write signal.SIGKILL (SIGKILL is not imported, so the teardown would have raised NameError and left the group alive). Both wrapper descriptions now raise subprocess.TimeoutExpired(cmd=["bash"], timeout=dbe.DRAIN_SECONDS): the constructor is (cmd, timeout, output=None, stderr=None) and a zero-argument construction raises TypeError instead of simulating the timeout — MEASURED on the pinned 3.11.8, an agy should-fix the brief did not carry. Stale counts corrected: the verdict-table test produces each of the 23 heads (not 22) and _field renders 19 dynamic values (not 18). Design v1.87 made explicit: _run_recipe's tuple unpacking of dbe.substitute into subbed and a discarded count is required because substitute returns (Block, counts) and WIRE-PIN 2 asserts identity of the unpacked block, and the two source-scan rows are green on the real helper and RED only under the mutant. Counts unchanged at 81.
- v1.30: Impl-plan audit v31 (codex must 1; agy clean) — design v1.90, spec v1.52 and plan v1.83 all clean on both surfaces this round, so this is the only document that changed. Task 5's RED is rebuilt in two steps so a wiring pin's RED is a CALLER-OBSERVABLE assertion rather than a missing symbol, which is this document's rule 5 and what h_mad_assemble_tdd.py:238-243 prints into every wiring dispatch. RED step 0 is a pure refactor with the suite green and no dbe CALL: today's legacy logic is hoisted under _gate_block (re.findall + the h_mad_audit_gate.py filter, wrapped as a four-field dbe.Block), _gate_bash_block (returning .text) and _run_recipe (str.replace back into a Block, then the inline subprocess.run returning a four-field dbe.RunResult under a function-local import) — exactly the composition of the four wire-revert-* bodies this document already spells out literally, so nothing new is invented. The RED commit adds the alias import, needed only for the annotations and the three constructors, plus the six tests. RED step 1 then has WIRE-PIN 1 failing on its empty extract/select record and WIRE-PIN 2 on its empty substitute/run_block record, with test_gate_block_refuses_an_untagged_recipe failing because the legacy path resolves an untagged block, test_only_the_exec_scan_hand_rolls_extraction and test_exactly_one_tagged_fence_in_the_tree failing, and the spelling, no-execution, floor and four AC-6.3 guards passing. The 5e connection-only revert is literally step 0's scaffold re-applied at GREEN, so each pin fails for the SAME empty call record at both ends — the symmetry is what proves the pins discriminate the connection rather than the presence of a name. The stale sentence calling that assertion the revert's failure mode 'not of RED' is corrected, and Task 5's RED gate line no longer expects NameError. Every row and count unchanged at 81.
- v1.31: Design audit v81 (codex must 1, raised against THIS document; agy clean on the impl-plan at cycle 32, the codex impl-plan leg lost to a usage limit) — design v1.90, spec v1.52 and plan v1.83 all clean, so again this is the only document that changed. The Conventions "Exit-code partition" bullet still said argparse usage errors were the only non-DOCBLOCK: exit 2, which had been false since v1.28 gave the parser exit_on_error=False and an error() override raising BadArgs: it contradicted Task 4, the design from v1.85 on and spec AC-5.6, and following it would have reintroduced precisely the non-verdict exit that argparse-error-unrouted and test_malformed_invocation_is_a_verdict exist to prevent. The bullet now states that UNREADABLE, CLEANUP_FAILED and LAUNCH_FAILED are the whole of exit 2 and that nothing reaches exit 2 without a DOCBLOCK: line, names the grammar error as a BAD_ARGS verdict at exit 0, and accounts for the single remaining output with no DOCBLOCK: line — --help alone, which exits 0 and so sits outside the exit-2 partition. Swept the whole document with grep -nE 'Exit-code partition|usage error|non-`DOCBLOCK|argparse' and again with 'only non|exit 2' outside the Version History: that bullet was the sole stale site, every other passage (Task 4's description, the two parser ACs, the argparse-error-unrouted and allow-abbrev-restored rows) already stated the BAD_ARGS/exit-0 contract. Counts unchanged at 81.
- v1.32: Impl-plan audit v33 (an ADVISORY teammate surface standing in for the quota-blocked codex leg; must 3, should 3, nit 4) — design v1.90, spec v1.52 and plan v1.83 are the team lead's this round (exit_on_error, the suite-floor baseline and the --help carve-out land there concurrently), so again only this document changed here. Task 5's WIRE target no longer pins ANY `h-mad/SKILL.md` line number: all six were stale, and the measurement is why the CLASS was closed instead of the instance — the section heading sat at `:1804` when those numbers were written, at `:1887` at `e8eaf6f` and at `:1897` at `b7d0d77` one commit later, a ten-line move in a single edit, with three more SKILL.md edits already queued. The axis is named (where a line sits in a file that keeps growing above it); the rule over it is a content predicate over a heading-to-next-H2 window — the ```bash opener whose body contains `h_mad_audit_gate.py`, which is the consumer's own pre-migration `:270` predicate and the one every `wire-revert-*` payload restates; the block that stays untagged is identified by content too (`hmad-dispatch exec codex`) rather than by ordinal, which is as perishable as a line number; and a two-command awk resolver is given, its match confined to fence bodies so the halt diagnosis is exactly true, whose printed line number is an OUTPUT, not a contract, and is deliberately written down nowhere. The residual is stated exactly: exactly-one-gate-fence-in-the-window is load-bearing and the implementer halts on 0 or more than 1; "four fences, gate last" is informational, and a fifth fence that does NOT contain the gate script is not a reason to halt. AC-6.1's sweep regains the `*.md` scope of the census it is bound to (the plan's glob and part-filters verbatim): by Task 5 the feature's own test module sits under `h-mad/` carrying column-0 ```bash hmad:exec fixtures inside triple-quoted Python strings (AC-1.1, AC-1.5, AC-1.7, AC-3.7), which by the stated grammar are openers regardless of the enclosing suffix, so the unrestricted sweep could never pass at GREEN — and one of those fixtures is a deliberately unbalanced four-backtick fence, so a whole-file scan would not even be the sum of the per-fixture counts. The scoping rule follows from what `_fence_events` IS: a markdown scanner whose only inertness rules are markdown ones, so a non-`.md` holder of a fixture is a false positive by construction. Residual named (non-`.md` files under the two roots, `.md` outside them, anything under `archive/`), and the RED reason "zero tagged fences" is now TRUE as stated — measured at `b7d0d77`, `grep -rn hmad:exec` over `h-mad/` and `handoff/` returns nothing. The DESIGN carries the same unrestricted wording and is FLAGGED for back-propagation, not edited here. `docsections.json`'s `missing-heading-returns-empty-instead-of-failing` is re-spelled on its REPLACE as well as its `find` — `    if not found: return ""` — because the migrated `titled_section` binds `found`, `start` and `level` and no `match` at all, so the shipped payload would have raised `NameError` in every call and the row would score ALL_CAUGHT while measuring nothing about the loud `assert` its mechanism claims to prove; that is the same class v1.11 fixed once for `docsections-heading-lookup-reverted`, and both re-pointed anchors now carry the four-space body indentation the landed source has. RED step 0 is disambiguated: it is its OWN commit, landed after Task 4 GREEN and BEFORE the 5d dispatch, refactor only, NO new test, suite green — because the consumer is a Task 5 Production file and `h_mad_assemble_tdd.py:230` prints "Write failing tests only. Do not modify production code." into the RED dispatch; the 5d dispatch then adds the eight new tests (six in the consumer, two in the helper module) and nothing else. Suite-floor baselines re-measured 2026-09-04 at `b7d0d77`: 2748 from the repository root and 2486 from `h-mad/`, the 262 delta unchanged. Four nits: the `__all__` comment now says 20 exception classes (5 + 20 = 25), agreeing with its own list and with the 29-name sentence two lines below; the docsections delta's "`os` is no longer needed" sentence is replaced by what the file actually imports (only `re`), since there is no `os` in the source being edited; `exec-scan-executes`'s anchor pin moves from `8599e28` to `b7d0d77` with both anchors re-verified exact-once by `grep -c`; the 76-payload reference is dated against today's 81; and AC-6.2 now names its discriminator — the `dbe.run_block` spy carries the whole kill, while the `dbe.subprocess.run` recorder is a belt `exec-scan-executes` cannot trip, because `run_block` spawns through `subprocess.Popen`. Every row and count unchanged at 81 (25 + 5 + 24 + 27), the wire spec at 8 and `docsections.json` at 8.
- v1.33: Design v1.91 / plan v1.84 / spec v1.53 back-propagation (no impl-plan audit cycle; v1.32 had already landed when this arrived, so the exit_on_error resolution is its own revision). `exit_on_error` returns to argparse's DEFAULT (`True`) at all three sites that carried `exit_on_error=False` — the Conventions exit-code partition, Task 4's parser construction and the `test_parser_rejects_all_dir_and_abbreviations` AC. `exit_on_error=False` was the defect, not the contract: it suppresses argparse's own `except ArgumentError: self.error(str(err))` around `_parse_known_args`, so a MISSING OPTION VALUE raises `argparse.ArgumentError` inside the parse, never reaches the `error()` override, and escapes `main` as a non-`DOCBLOCK` traceback — and the missing option value is one of the two inputs `test_malformed_invocation_is_a_verdict` drives, so the setting broke the AC it was written to serve. Re-probed here on the pinned 3.11.8 rather than carried: with `error()` overridden, at the default all FIVE grammar shapes (unknown option, missing value, missing required option, missing positional, rejected abbreviation) raise `BadArgs`, while under `exit_on_error=False` four do and the missing value escapes as `ArgumentError`; `--help` at the default with the override installed still exits 0 with help text, because `--help` is not an error and never reaches the override — so the exit-code partition's `--help` carve-out is unchanged. `argparse-error-unrouted` needs no rewording but gains the sentence that makes it sound: the mutant was probed BOTH ways, and its stated mechanism ("the override is removed, so argparse raises `SystemExit(2)` and prints usage") holds at the default for both of the killer's inputs, while under `exit_on_error=False` the missing-value input gives `ArgumentError` instead — the row would still have gone red, but on a mechanism its own description denies, which is the wrong-catcher class. AC-6.4's floor stops being a bare number: it is stated WITH the commit it was measured at (2748 from the repository root, 2486 from `h-mad/`, at `b7d0d77`) and is RE-MEASURED at 5c branch time rather than copied from the document — the same rule as the SKILL.md line pins, for the same reason. The measured cost of the stale one is now recorded: 2747 came from `6b4df35`, `b59e05e` added exactly one test after it (verified: that commit adds one test to `h-mad/tests/test_h_mad_assemble_audit.py`), and against a real 2748 the assertion `>= 2747 + new_module + len(tuple)` silently permitted one deletion. The residual is stated exactly — a floor stale by N is not a failing test but a WEAKENED one, tolerating N invisible deletions, and nothing in the suite can detect it; drift found at 5c is expected, not a finding. Every row and count unchanged at 81 (25 + 5 + 24 + 27), the wire spec at 8 and `docsections.json` at 8.
- v1.34: Provenance header re-pinned to design v1.92 / spec v1.53 / plan v1.84 at 93a13f4 (it trailed v1.90/v1.52/v1.83). Third instance today of one class: a pin naming a moving value in another file. Rather than re-pin and wait for the next drift, the header now carries the re-derive command and says outright that a reviewer finding it behind is seeing expected drift, not a finding — the same treatment Task 5's SKILL.md locator and AC-6.4's floor already have.
- v1.35: Impl-plan audit v34, the GATING round (teammate surface must 3 should 3 nit 2; the agy surface contributed no change to this document). Two of the three must-fixes were introduced by v1.32/v1.33's own repairs, which is why the delta was the first place looked. (1) AC-6.1's transcribed census filter selected **zero** files and so could never pass at GREEN: v1.32 rebased the plan's `p.parts[0] in ('h-mad','handoff')` predicate onto this document's **absolute** `REPO_ROOT`, where `parts[0]` is `'/'`. The filter is now written against `rel = p.relative_to(REPO_ROOT)`, the word "verbatim" is dropped, and the keep-counts are recorded beside it from a run at `1861157`: absolute-base **0**, rebased **30**, the plan's own `Path('.')` sweep **30**, the same 30 files — so nothing is owed to the plan. The class is a path predicate transcribed out of a sibling whose path base changes meaning in the copy; the rule is to re-run it in the base the consuming file actually uses and record the keep-count beside it. (2) Three back-propagation flags against the paired design were **stale at the very version this document's header pins**: the AC-6.1 restriction landed in design v1.92 (`design.md:1135`, `:1446`), and the `BAD_INFO key=` and `overlap:` quotings landed in design v1.81 (`design.md:1005`, `:1002`, `:1435`) — eleven revisions earlier, in answer to this document's own v1.24 flag. All three are withdrawn; the class is any note asserting what a sibling currently says, and the rule is that every such note is re-derived against the sibling in the same pass that re-pins the header. The fourth member of the class was the 5f note, which claimed the spec agreed and "nothing is owed" while citing a drifted `spec :458`: the pin is dropped for a by-name citation with a `grep` locator, and the one thing that **is** owed — the spec's AC-6.4 gate-command inline comment still reads 2747/2485 against the current 2748/2486 — is now flagged for the spec author. [Bracketed correction added at v1.42; the sentence above is deliberately NOT rewritten, because it is a dated record of what was true when v1.35 shipped, and stripping its tense to satisfy a rule about the present would falsify a correct record. That debt has since been PAID: read out of the freeze commit with `git show 6f0ee85:docs/01-plan/features/doc-block-exec.spec.md`, the AC-6.4 gate-command inline comment carries 2748 and 2486, and the spec's own Version History records the migration at its v1.53 and v1.54. Nothing is owed to the spec author on this point as of `6f0ee85`.] (3) The Conventions bullet fixing WHEN a mutation row's payload is written stated a per-spec partition that two of `docsections.json`'s eight rows fall outside. The axis is restated as **does the row's anchor file exist at HEAD**: six `docsections.json` rows do and carry payloads here; `fence-tracking-removed` and `section-no-longer-owns-its-subsections` are re-anchored by Task 1 into `h-mad/scripts/h_mad_doc_block_exec.py` and follow the `doc_block_exec.json` rule (mechanism and `test` key now, `file`/`find`/`replace` at 5e from the landed source), with the residual — an anchor file that survives while its anchor text is rewritten — named and routed to the existing Task 1 rule. Should-fixes: RED step 0 no longer claims to change no behaviour, and names the two `_gate_bash_block` asserts at `test_h_mad_collect_report_docs.py:272-273` that the hoist necessarily drops, the `IndexError` window that opens, and `dbe.select`'s `BlockNotFound`/`AmbiguousBlock` closing it at GREEN; Task 4's `h-mad/SKILL.md` registry entry is forbidden a tagged opener, tied to AC-6.1. Nits: step 0 also states that `_gate_bash_block` lands without today's `:268` docstring, which `hand-rolled-extraction-widened`'s two-line `find` requires, and Task 1 states that `docsections.json`'s whole-file `command` is left as it is, with the reason. No mutation row was added, removed or re-bound: every row and count is unchanged at 81 (25 + 5 + 24 + 27), the wire spec at 8 and `docsections.json` at 8; five tasks, two of them `wiring` (Tasks 1 and 5). Three further must-fixes arrived mid-revision from the sibling authors, all one class — a figure derived from a measurement, in prose, that did not move when the measurement did. (4) The 81-row **split** was `79 + 2`; it is `80 + 1`, re-derived at `1861157` by counting the rows of the design's helper matrix whose mechanism column names `SKILL.md` as the file the harness edits — exactly one, `registry-row-removed` (`design.md:1290`). `detail-line-undocumented` (`design.md:1291`) mutates the **helper**, renaming an emitted detail line; it is `registry-row-removed`'s partner by AC, not by file, and reading the pair as "the two `SKILL.md` rows" is how the miscount arose. The line now agrees with this document's own row-list annotation, which already said `80 + 1`, and the `matching design v1.86` pin is dropped as the moving-value class the header rule covers. (5) The 5f full-suite bound cited a **397 s** baseline; the suite was re-measured at plan v1.84 from `2747 passed in 397.40s` (`6b4df35`) to `2748 passed in 383.05s` (`e8eaf6f`) and the derived figure did not follow. It reads 383 s now, and the 1200 s bound is unchanged and verified still fit: 3.02x at the old baseline, 3.13x at the new, so the correction only adds headroom. Swept both values across the document (`\b79\b|\b397\b|two .{0,12}SKILL\.md|matching design v1\.` outside the Version History): those two sites were the only ones, and the design and spec carry no stale copy either. (6) The 2748/2486 floor stays pinned at `b7d0d77` here while the other three documents pin it at `e8eaf6f` — a judgement call, decided for keeping it, because each document must name the commit it actually measured at and re-pinning would claim a measurement this document did not run. The one sentence that makes it legible is added, with the evidence that the value is genuinely identical: `def test_` across every `test_*.py` in the tree counts **2675 at `e8eaf6f`, at `b7d0d77` and at `1861157`**, so no test function moved across that span.
- v1.36: Design v1.93 / spec v1.55 / plan v1.86 back-propagation, arriving while v1.35 was being written; the team lead routed it. **AC-6.1's sweep gains a dot-directory exclusion and stops reaching its scope by reference.** v1.35's rebase onto `rel = p.relative_to(REPO_ROOT)` was right and stands — the absolute-base predicate did select zero — but it kept all 30 files the glob returns, and five of those are the gitignored `.pytest_cache/README.md` artifacts that exist on any tree where pytest has run. The filter now also drops any path with a dot-directory component, and all three keep-counts are recorded so each clause is legible: measured at `1861157`, absolute base **0**, `rel`-rebased **30**, `rel`-rebased minus dot-directories **25**, with the five dropped paths named. **The defect was LATENT, not live, and is stated that way** so a 5d implementer does not hunt a failing test: no `.pytest_cache/README.md` carries `hmad:exec` (0 hits over all five at `1861157`), so the cardinality-1 assertion passed on the 30-file sweep too — what was wrong is that the set the test walks is machine-state-dependent, 25 on a clean clone and 30 after anyone runs pytest, so a future tool emitting a generated `.md` under those roots would silently enter an assertion meant to be exactly 1. **Which of the design's two realisations this is, and why they differ, is now stated**: §Scanning's *measurement* corpus is `git ls-files` (25) because a one-off human measurement should describe the tracked tree, while this *guard* takes the dot-directory exclusion because a test must still count a tagged fence in an `.md` written and not yet committed — exactly what `git ls-files` would miss. The two agree on this tree and are not the same predicate: the dot-excluded glob set and the `git ls-files` set are both 25 and identical at `1861157` (symmetric difference empty), an agreement of today's tree rather than of the definitions. The residual gains both new edges — a tagged fence inside a dot-directory is uncounted (the intended trade), and a generated `.md` under the roots outside a dot-directory IS counted, correctly but noisily. **Two sibling clearances v1.35 carried are superseded and the debt is taken rather than flagged**: "nothing is owed to the plan here" and "the design already carries this restriction and nothing is owed there" were both true against design v1.92 and false against v1.93. Nothing is owed to any sibling now, but because this document adopted their scope, not because 30 matched anything. **The stale `design.md:1135` anchor is not re-pinned to `:1165`** — it is replaced by a by-name citation with a `grep` locator (the Test Plan row for AC-6.1–6.6, `grep -n 'The sweep excludes build output'`, one hit), because a line pinned into a document under active revision is the class this document hit four times in one day. The same treatment is applied to the two other sibling citations added this session, and each locator was verified to return exactly one hit. **A fourth site the brief did not name, found by sweeping the corrected value**: the Task 1 guard-narrowing evidence read "over 30 files, agree on 266 headings", a corpus and an agreement count matching neither reading of the plan's differential. It now gives the tracked figure (25 files, both=263, `old_only=76`, `new_only=0`) with the glob figure beside it (30 files, both=268, same `old_only`/`new_only`), says plainly that the differential is the plan's measurement transcribed and not re-run here, and records what this document did verify — the corpus counts, 25 tracked and 30 globbed. No mutation row was added, removed or re-bound: 81 (25 + 5 + 24 + 27), the wire spec 8, `docsections.json` 8; five tasks, two `wiring` (Tasks 1 and 5).
- v1.37: Impl-plan audit v35, the GATING round (teammate surface must 2 should 3 nit 2; the agy surface returned CLEAN but the cycle scored it UNVERIFIED reason=low_evidence at 1 tool call, so it corroborates nothing and contributed no change). (1) MUST: AC-6.4's floor tuple was short by two and the + 7 constant with it. h-mad/tests/test_h_mad_portable_timeout.py:40 binds SKILL = Path(__file__).resolve().parent.parent -- THIS repository's h-mad/ -- and :160 puts *sorted((SKILL / 'scripts').glob('*.py')) into the module-level _SCANNED, which :165 and :295 each consume as @pytest.mark.parametrize('path', _SCANNED, ids=lambda p: p.name). Re-derived at a8e0372: the file collects 160 nodes, 58 under each of those two test names, against 37 files in h-mad/scripts/*.py. Task 1 writes h_mad_doc_block_exec.py into that glob, so each parametrised test gains one node with the id [h_mad_doc_block_exec.py]. Both PASS on the specified module, which is why it mattered: + 7 against a true addition of 9 is not a failing test, it is a floor tolerating TWO invisible deletions -- the exact silent weakening this AC exists to prevent -- and the 5c re-measure does not absorb it, because the baseline is taken before Task 1 lands and the constant is not re-measured. Now + 9, with all nine written as full node IDs including the two bracketed parametrised ones, and the derivation 6 + 1 + 2 stated. The class is a pre-existing parametrize whose argvalues come from a filesystem glob this feature writes into; the rule is to enumerate those globs before fixing the constant and add one node per (parametrised test x added file). Residual enumerated at a8e0372 across the whole of testpaths: exactly TWO module-level glob-fed parametrize sources exist -- _SCANNED (+2) and REAL_AUDIT_REPORTS (test_h_mad_audit_cycle.py:15, sliced [:8] over 460 candidates, saturated, +0, and over docs/ which this feature's source does not write) -- and every other .glob/.rglob in h-mad/tests, handoff/tests and handoff/scripts is inside a function body and adds no node, each one named. Task 1 also inherits the two guards the new module now falls under (no timeout <digits> command form; no unqualified macOS-absence claim), stated so a docstring copied from the design does not fail them at 5d. The identical + 9 correction is owed to plan.md and spec.md and was routed to their authors, not edited here. (2) MUST: the 5f note's 'One thing is therefore owed upstream' flag against the spec was FALSE at a8e0372 -- spec v1.54 had already paid it -- and three spec.md line numbers were stale with it (the subshell moved :462 to :474). This is the FOURTH recurrence of the class named at v1.35, now a stale CLEARANCE's mirror image, a stale DEBT. Not fixed as an instance: a Conventions rule now forbids EVERY sentence in this document from stating what a sibling currently says, on the ground that a debt or clearance is CYCLE content, not DOCUMENT content -- paid inside the cycle, outlived by the document, re-derived by nothing. Two forms remain admissible: a value THIS document must carry, stated as its own constraint with a grep -n locator verified in the same pass to return exactly one hit; or nothing. Sibling line numbers are never admissible. Provenance citations ('(design v1.85)') are explicitly carved out as dated historical facts, as is the header's version pin, or the rule would read as forbidding ~40 of its own citations. Residual stated exactly: only the locator form has a detector, and a weak one (0 or >=2 hits); prose agreement has NO detector anywhere in this repository -- no test and no precheck reads a sibling's content against this document's assertions about it -- so a fifth recurrence is prevented by the sentence not being written, aided only by a pre-dispatch grep the reviser runs. Applied at every site, not just the one flagged: the 5f note, the verdict-grammar paragraph's three design pins, the 80 + 1 paragraph's two, and AC-6.1's three-sibling clearance. (3) SHOULD: five design line pins replaced by by-name grep locators, each verified to return exactly one hit at a8e0372 -- 'unrecognised info-string token', 'one key is a substring of another', 'both halves of', and the two anchored table-row forms for registry-row-removed and detail-line-undocumented. Three of the five had drifted since 1861157. (4) SHOULD: docsections.json's whole-file command justification said 'three of the eight killers' live in test_h_mad_doc_block_exec.py; it is TWO -- docsections-syspath-setup-removed's and docsections-local-bounder-restored's. The row IS its binding, so listing both double-counted. Re-derived against the shipped spec (four rows, all _killed_by under tests/test_docsections.py::) plus Task 1's four (two killed by the WIRE-PIN, which lives in test_docsections.py). The conclusion survives at two; the number is fixed because a 5d implementer who counts finds two and reads the gap as a missing row. (5) SHOULD: AC-6.1's 'Re-run to check' stated three absolute integers already wrong one commit later. The check is now the RELATION -- absolute base keeps zero; the dot-excluded glob set is IDENTICAL to git ls-files (symmetric difference empty); dropping the dot clause adds exactly the five named .pytest_cache/README.md paths -- with 30/30/35/0 kept only as a dated example at a8e0372. The same treatment applied to Task 1's guard-narrowing paragraph, whose 25/30 corpus figures now read 30/35 with the 263/268 differential explicitly stamped at 1861157 as a transcription this document did not re-run and cannot re-derive. (6) NIT: the third live instance of the class Task 1 closes is now named as residual -- _titled_section at h-mad/tests/test_h_mad_context_budget_docs.py:69, no fence state, eight call sites at :301-372, verified at a8e0372 -- with the design's own contract reached by locator and the measured reason it is not a drop-in. (7) NIT: everything else the reviewer set out to falsify held, and no count moved: 81 rows (25 + 5 + 24 + 27, 80 + 1), the wire spec 8, docsections.json 8; five tasks, two wiring (Tasks 1 and 5). Header re-derived at a8e0372: design v1.93, spec v1.56, plan v1.87.
- v1.38: AC-6.4 reconciliation with spec v1.56, routed by the team lead mid-revision: the spec author declined the '+ 9' constant the lead had prescribed to all three authors and wrote a MEMBERSHIP RULE instead, and the lead accepted it. This document follows, because 'nine' is the instance and the instance is what just went stale: 'seven' was wrong the moment a second source of tuple members was noticed, and 'nine' would be wrong the moment this feature landed a second script. Three changes. (1) The assertion's addend is now len(tuple), never a hand-written integer -- a literal is a second authority that drifts against the enumeration beside it, which is precisely how the previous '+ 7' came to disagree with its own list, while len(tuple) cannot. The tuple is still enumerated in full, with all nine full node IDs including the two bracketed parametrised ones, because this is a TEST and a test needs concrete IDs to assert on; what is no longer written anywhere is a total. (2) Membership is attributed to the spec's rule rather than re-worded here -- two independently-worded versions of one rule is how the 25/30 corpus contradiction started -- and reached by locator, grep -n 'One node per glob-parametrised test' on the spec, one hit verified at a8e0372. The rule's two sources are nodes added directly to a consumer file, plus one node per glob-parametrised test per new file the feature adds under h-mad/scripts/, the latter required to PASS rather than merely be counted. (3) The re-derive-at-5c instruction, which previously covered only the 2748 baseline, now covers the tuple: at 5c the implementer re-runs the glob enumeration against the branch and adds one node per glob-parametrised test per scripts/*.py file the feature actually landed, so a second script grows the tuple by two and len(tuple) follows with no edit to the assertion. Task 5's closing line drops its own 'nine-node' restatement for the same reason. The residual enumeration is unchanged in substance but was re-derived independently rather than copied, this time by AST rather than by grep: parsing every test_*.py under h-mad/tests, handoff/tests and handoff/scripts and collecting module-level assignments whose value contains a .glob/.rglob call yields exactly TWO names in the whole of testpaths -- _SCANNED (two parametrised consumers, +2) and REAL_AUDIT_REPORTS (sliced [:8] over 460 candidates, saturated, +0, and over docs/ which this feature's source does not write). git grep -n 'glob("*.py")' -- 'h-mad/tests/*.py' independently returns the same three hits the spec's residual names, of which two loop inside a test body and add no node. handoff/scripts holds five test files with zero globs among them, so the 'whole of testpaths' claim is swept, not assumed. No mutation row, task, count or other AC moved: 81 rows (25 + 5 + 24 + 27, 80 + 1), the wire spec 8, docsections.json 8; five tasks, two wiring.
- v1.39: Impl-plan audit v36, the GATING round (teammate must 2 should 3 nit 1; the agy leg returned PASS and found neither must, so it is not corroboration and contributed no change). Re-derived at 335f535, not carried. (1) MUST: AC-6.4's 'No total is written for that tuple, here or anywhere' was itself the class this document's own new Conventions rule forbids -- 'anywhere' is a present-tense claim about siblings. Scoped to this document alone; a stated total is now explicitly admissible as a dated evaluation naming the commit it was evaluated at, inadmissible only as a bare integer standing where len(tuple) stands. (2) MUST: the Single-source residual filed ONE member of an open class. Three hand-rolled ##-slicers are live and all three are now named with the same treatment -- _titled_section (test_h_mad_context_budget_docs.py:69, eight call sites :301-:372), section_text (test_h_mad_batch_doc_rules.py:26) and _section (test_h_mad_collect_report_docs.py:40) -- and the residual is restated as a SCOPE RULE plus a runnable AST sweep, never a cardinality, because no mechanical sweep over that class is both sound and complete: measured at 335f535 the sweep over-counts (22 named helpers, several not section slicers) and under-counts (it cannot see _section, whose ## anchors arrive as parameters). _section's Task 5 relevance is stated: it lives in the consumer file Task 5 edits, reached through _second_surface(), whose eight call sites are :118 :154 :225 :248 :269 :389 :409 :431, of which exactly :269 is on the executing path and is the one Task 5 removes. (3) DECISION C, routed by the lead and owed here: the closing-hash-run delimiter is corrected from space-only to SPACES-OR-TABS at both prose sites and in the code-structure docstring, oracle-backed (markdown-it-py 2.2.0 renders '## Text<TAB>##' as an h2), and test_closing_hash_run_does_not_change_heading_identity's fixture gains the tab-preceded form on both of its legs. Residual measured at 335f535: ZERO tab-preceded closing runs in the tracked corpus, so a fixture rather than a corpus instance is what pins it; and closing-hash-run-kept mutates the strip away, so it does not discriminate the tab arm -- a narrower space-only-strip mutant has no row deliberately, since adding one would put this document at 82 against a matrix of 81. (4) DECISION B: the Task 5 fence ordinals now carry their BASE (the untagged exec-codex fence is 2nd of 4, 1-based; the gate fence 4th of 4, 1-based, re-derived at 335f535 by the two awk commands) and the content predicate is stated as the load-bearing part in both places. (5) SHOULD: the glob residual presented a partial eight-site list under the words 'Every other'; a full walk finds 21 in-body sites. Replaced by an AST sweep that separates module-level from in-body calls -- 7 module-level in 2 files feeding exactly 2 parametrize sources (_SCANNED at :153 from four globs :158-:161; REAL_AUDIT_REPORTS at :15 from three globs :18/:19/:23, sliced [:8] over 463 candidates, saturated) and 21 in-body -- with the command written out, so the enumeration is complete by construction rather than by hand. (6) SHOULD: the 5f note labelled itself Conventions form (a) while imposing a MODAL requirement on the spec. The Conventions rule is widened to cover the modal form (a sentence is inside it if a sibling's author could pay it, ignore it, or have paid it already), and the note is restated as this document's own constraint with the locator standing alone. (7) SHOULD: the adjacent half of the class AC-6.4 closes is now stated at Task 4 -- a file this feature EDITS that is ALREADY in _SCANNED turns an existing node red with no count change, so AC-6.4 cannot see it. Class rule stated; residual derived from _SCANNED's eight sources: h-mad/SKILL.md is the ONLY such file, and it binds Task 4's registry entry and Task 5's retag. (8) NIT: the sibling-line-pin rule now names its AXIS (docs/ siblings under concurrent authorship) and states why tree pins are admissible -- each carries its symbol name, so a drifted pin self-repairs under one grep, and each is re-derived in the revision that writes it. (9) Swept beyond the findings, same rule: three surviving present-tense sibling claims restated as this document's own constraints with locators (the mutation-anchor ordering, StreamPathUnwritable's signature, AC-6.1's two realisations) [Bracketed correction added at v1.42, entry left standing rather than rewritten: item (9) OVERCLAIMED on one of its three members. The StreamPathUnwritable sentence was never restated -- 'The design's exception table agrees (v1.71, impl-plan audit v16)' survived v1.39 completely untouched and then stood through v1.40 and v1.41. Re-derived at the freeze sha: `git diff 335f535 74e126f -- docs/01-plan/features/doc-block-exec.impl-plan.md | grep StreamPathUnwritable` shows no change to any StreamPathUnwritable prose, only the new Version History line itself, and `git show 74e126f:docs/01-plan/features/doc-block-exec.impl-plan.md | grep -c 'exception table agrees'` is 1, as it is at 0aac0b7 and at 35698f9 and was at 6f0ee85. The impl-plan audit v39 agy leg caught it 26 design revisions after the citation was written; v1.42 repairs it in the Conventions rule's form (b). A sweep that reports a member it did not touch is the failure mode this bracket exists to record.], and the registry-row-removed derivation no longer quotes the design's row text. RED step 0 now names _run_recipe's actual source -- the NESTED run_recipe at test_h_mad_collect_report_docs.py:309 inside the test at :294, not a module-level function -- and states that the hoist ADDS timeout=60.0, which the nested form does not carry. Counts unchanged and re-derived: 81 rows (25 + 5 + 24 + 27, 80 + 1), verified as a set against the design's 81-row matrix at 335f535 with empty difference; wire spec 8; docsections.json 8; five tasks, two wiring (Tasks 1 and 5). Header re-derived at 335f535: design v1.94, spec v1.56, plan v1.89.
- v1.40: Impl-plan audit v37, the GATING round (teammate surface must 2 should 2 nit 1). ITEM 0, and it was RED ON MAIN: v1.39's own repair of the sibling-pin rule reintroduced a path-qualified `SKILL.md`:N line pin at the _titled_section residual, which the standing control test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins asserts against; the full suite was 1 failed / 2546 passed at 74e126f. Measured: git show 335f535:<doc> | grep -c 'SKILL.md:[0-9]' -> 0, git show 74e126f:<doc> -> 1. The pin is replaced by a by-name locator, grep -n '^## Run-context ceiling' h-mad/SKILL.md, one hit verified at 74e126f, and the paragraph now names the control that catches this class so the next reviser sees the forcing function. Test run alone: 1 passed. (1) MUST: the Single-source residual closed the fence-BLIND half of its axis and left the fence-AWARE half unswept. The invariant now carries an explicit FILE SCOPE -- h_mad_doc_block_exec.py and docsections.py, and nowhere wider -- which is what its two guards actually enforce, and the residual is split in two. Residual (a) is the subject axis, unchanged, the ##-slicer class. Residual (b) is the file axis, new: an AST sweep selecting on a three-backtick literal plus an in_fence/fenced-named variable prints 7 bodies at 74e126f, exactly one in scope (docsections.py:31 _fence_aware_end, the positive control), six pre-existing and unguarded, three of them production code under h-mad/scripts/ -- h_mad_assemble_tdd.py:96 _body_end (:114/:118), h_mad_precheck_doc.py:270 scan (:301/:304), h_mad_version_history.py:86 section_bounds (:94/:98), test_h_mad_context_budget_docs.py:35 _section (:48/:51), test_h_mad_hook_wiring.py:288 _wiring_section (:293/:296), test_h_mad_pane_visible_dispatch_docs.py:26 _section (:50/:53), every toggle line re-derived here. The v1.39 sweep structurally could not see two of them because it selects on the ##-slicer axis. What the NEW sweep cannot see is stated with two live counter-examples found by running the complement: h_mad_assemble_audit.py:109 _braces_outside_fences (state fence_char/fence_len) and handoff/scripts/test_handover_docs.py:534 _fenced_blocks (state cur), both genuine members, neither name-matching -- so residual (b) publishes no cardinality either, and the scope sentence is the contract. Also swept: 0 *.sh files under the two roots hold a three-backtick literal. AC-1.8's test_extract_has_no_fence_state_of_its_own is scoped to the helper module's own source to match. Both controls were run before the paragraph was written. (2) MUST: the 'both halves of' locator returned 2 hits at 74e126f, not one -- design v1.95 added ':904 both halves of its base' inside the same commit, so a needle verified unique at 335f535 broke without its target row being touched. Re-pointed to 'both halves of `overlap:`', 1 hit at 74e126f. Not fixed as an instance: the Conventions locator rule now carries a HARD condition (exactly one hit AT THE COMMIT THE REVISION SHIPS AGAINST, re-run in that revision, never carried) and a SELECTION PREFERENCE (a backticked identifier, a verdict token, or an anchored ^| row prefix, never a bare English phrase). The preference is deliberately NOT hard, and the reason is measured: of this document's 13 distinct docs/-sibling locators, 7 satisfy it after this revision and 6 are bare phrases whose target rows carry no identifier to anchor on, and a rule a document violates 6 times at its own shipping commit is a rule that gets ignored. Two further needles widened to identifier-bearing forms while the paragraph was open ('^| `DOCBLOCK: BAD_INFO key=' and '^| `DOCBLOCK: SUBST_OVERLAP keys='), plus '`_titled_section` anchors on a substring'. ALL 13 LOCATORS RE-SWEPT AT 74e126f AND ALL 13 RETURN EXACTLY ONE HIT; every 'verified in this pass' / 'verified at 335f535' stamp is restamped 74e126f. (3) SHOULD: AC-1.5/1.7's tab-arm residual command used grep -cP, which /usr/bin/grep on macOS rejects outright (invalid option -- P, rc 2, measured) -- so the evidence command printed nothing while its stated result was right. Replaced with a stdlib-Python one-liner printing '30 0', which is also the first form whose OUTPUT matches its description (grep -c prints a per-file count, not a file count). The rule is stated -- every runnable command this document ships must run under the stock macOS toolchain, which is what this feature's own inherited _TIMEOUT_CMD/_ABSENCE_CLAIMS guards exist for -- with the six-token GNU-vs-BSD sweep beside it (grep -P, sed -i, readlink -f, date -d, xargs -r, stat -c), returning two lines at 74e126f: AC-3.13's stat -f/-c pair, which already wrote both forms, and this bullet, which matches only because it names the tokens. Residual: nothing in this repository detects a GNU-only flag in a document. (4) SHOULD: Decision C named its class as 'both #-run delimiters take spaces-or-tabs' but left the LEADING indent written as space-only and pinned by a space-only fixture. Oracle re-run here (markdown-it-py 2.2.0, CommonMark): '\t## x', ' \t## x', '  \t## x' and '   \t## x' all render <pre><code>## x while '   ## x' renders <h2>x</h2> -- indentation is counted in COLUMNS with a tab advancing to the next 4-column stop. A literal implementation of the shipped predicate already rejects every tab case, so this is LATENT, not live, and is stated that way; the grammar does not change and NO mutation row is added (81 stands; a row on this axis is the design's to add). test_heading_lookalikes_are_not_headings gains '\t## x' beside '    ## x', which is what refuses a 5d line.lstrip() simplification. Residual: the fence opener's 0-3-space indent is the same axis ('\t```bash' renders as code, '   ```bash' opens a fence) and no corpus instance exercises either arm. The docstring's predicate is corrected with it. (5) NIT: Decision C's first prose site had a ~60-word parenthesis between subject and verb; the oracle is split out into its own sentence. (6) Header re-derived at 74e126f: design v1.95, spec v1.57, plan v1.90. Measured once and stated so the ~40 tree pins stamped 335f535 need no churn sweep: git diff --stat 335f535 74e126f touches 9 files, ALL under docs/, so every path:line derived at 335f535 is byte-identical at 74e126f. (7) Everything else the reviewer attacked HELD and no count moved -- including the refusal to state a slicer cardinality, whose AST sweep the reviewer reproduced at exactly 22 with the same over-counts and the same _section miss: 81 rows (25 + 5 + 24 + 27, 80 + 1), the wire spec 8, docsections.json 8; five tasks, two wiring (Tasks 1 and 5), one shape each.
- v1.41: Impl-plan audit v38, the GATING round, answered from **two** surfaces at the freeze sha `35698f9` (teammate leg must 2 should 2 nit 3; the agy leg must 1 — real, and verified against the assembled prompt's impl-plan focus list; plus plan audit v78's agy must-fix, which is about this document and was routed here). MUST 1, and both halves of one sentence were wrong in OPPOSITE directions: v1.40's fence-opener residual claimed "no corpus instance exercises either arm, so both are pinned by fixtures and by nothing else". Re-measured from scratch at `35698f9` with a fence-state-aware scan over the tracked corpus this document defines (`git ls-files -- h-mad handoff`, `*.md`, `archive/` excluded — **30** files): the 1-3-space arm is exercised **29** times in **4** files, `h-mad/SKILL.md` among them — the very file Task 5's `_gate_block()` scans — so it is pinned by a fixture AND by 29 live instances; the tab arm is **0** and was pinned by NOTHING, no AC prescribing a tab-indented opener. The residual now ships the runnable stdlib command (verified verbatim under both `bash` and `zsh`), the sha, a positive control, a TRUE NEGATIVE (2 indented marker runs inside an open fence, declined) and its blind forms; AC-1.6's `test_indented_literal_tag_is_not_a_candidate` gains `\t```bash hmad:exec` beside its four-space case; no mutation row follows and the matrix total stays **81**. MUST 2, the recurrence ledger, which v1.40 left contradicting itself in three places (four at one site, "the FIFTH" at a second, "a fifth has not happened" at a third): resolved ONCE by scope rather than by incrementing — audit v37's finding was a **form (a) locator breakage**, not a member of the prose-agreement class, which the foot of that bullet already separates because form (a) has a detector and prose agreement has none; the list stands at four, and both the v37 site and the residual now use a **content predicate** instead of an ordinal [Bracketed correction added at v1.43, impl-plan audit v40; the entry is corrected here and NOT rewritten, because "stands at four" records correctly what was true when v1.41 shipped. The list reached five at v1.42. The reason this line is annotated rather than left alone is that it is a **restated integer**, and audit v40 measured the cost: four sites in this document carried that integer, v1.42 repaired two and left two, and a reader grepping `stands at` found the stale one first. v1.43 removes the integer from every live site — the count is `len(list)` and prose states it nowhere — and this historical one is pinned to its own revision instead.] [Second bracketed correction, added at v1.44, impl-plan audit v41: the v1.43 bracket immediately above is **itself an instance of the class it annotates** — it restates the size in prose one clause before asserting that prose states it nowhere, which is the same self-falsification the audit found in the body. Both are left standing and neither is rewritten, because both are dated records of what a shipped revision said. What changed at v1.44 is the claim's **scope**: it is now stated about the body of this document, with a published screen and two readings, and the Version History is explicitly outside it. This bracket adds no new occurrence — it names the class and points at the sentence rather than quoting it.]. DECISION C closed as a CLASS, not at the instances: 7 counter-instances at `35698f9` found by two surfaces on different instances (6 directory-less mutation-harness line pins, one directory-less `test_suite_collection` line pin, and a `:270` sitting in this document's own "stay admissible" example list without the enclosing symbol `_gate_bash_block` that makes it admissible). Every tree pin now carries its repository path AND its enclosing symbol (`run_spec`, `assemble`, `_run`, `_gate_bash_block`, `_fence_aware_end`, `titled_section`, `test_no_declared_skill_has_a_test_directory_left_out`, `test_exec_codex_dispatch_carries_out_log_and_timeout`, the module-level `_SCANNED` and `REAL_AUDIT_REPORTS`), and the class is declared closed with a **SHAPE grep** plus its bare-filename half — which returned 3 hits before this revision and **0** after [Bracketed correction added at v1.42 under decision H, publish every count with its unit; the entry is corrected here and NOT rewritten, because it records correctly what v1.41 did and only the figure it published was wrong. The before-figure **3** is wrong, and a bare integer with no unit is why it was not caught: re-derived at the base it belongs to, `35698f9`, the same published command returns **22 occurrences across 19 lines over 8 distinct files**. The after-figure **0** is correct and reproduces at `6f0ee85`. The commands for all four units, and the 22-against-7 reconciliation, are in the body's DECISION C residual.] — never a value sweep, since a value sweep only finds members that already drifted. Its three residuals are stated: non-`.py` pins, `grep`'s line-scoping against this document's ~95-column wrap (the paragraph-folded variant was run beside it and agrees), and the symbol half having no detector at all. SHOULD 1: residual (b)'s control claim is corrected — `_braces_outside_fences` and `_fenced_blocks` are known FALSE negatives, not "the negative", and a real TRUE negative was run and read (`_gate_bash_block`, a body holding a three-backtick literal with no fence state of any kind, which the screen declines). No cardinality is published for the declined side: classifying a declined body needs a human read, and every mechanical proxy for "fence state under another name" has the same blind spot the screen does — `_fenced_blocks` keeps its state in a variable called `cur`. SHOULD 2: the AC-1.5/1.7 conclusion orphaned by v1.40's toolchain insertion is moved back beside its own `30 0` measurement and its subject renamed the **closing `#`-run** tab arm, which is a different axis from the fence **opener's**. Nits: "the two files this feature owns" -> "touches"; the English-word tree-derived counts at the residual-(b) bullet and the GNU/BSD sweep are now digits (6, 3, 2). Also re-derived in this revision rather than carried: the header's three sibling versions (design v1.96 / spec v1.58 / plan v1.91, all three having moved in `0aac0b7`, so v1.40's pins were one behind on ALL THREE); all **13** `docs/`-sibling locators re-run at `35698f9`, every one returning exactly 1 hit (decision F, and a real re-measurement because two siblings moved in the shipping commit); the GNU/BSD six-token sweep, now **3** lines and not 2, the new one being this revision's own residual saying it uses no `grep -P`; and the absence claim under residual (b) ("no guard in this repository covers any of them"), which now carries a runnable AST screen returning **2** behavioural tests, neither asserting on any of the six bodies' source. The `74e126f` and `335f535` tree stamps are closed ONCE rather than re-stamped ~40 times: `git diff --name-only 74e126f 35698f9 -- h-mad handoff` is empty, so every tree `path:line` is byte-identical at the freeze sha. Unmoved: 81 rows (25 + 5 + 24 + 27, 80 + 1), the wire spec 8, `docsections.json` 8; five tasks, two wiring (Tasks 1 and 5), one shape each.
- v1.42: Impl-plan audit v39, the GATING round, answered at the freeze sha `6f0ee85` from **two** surfaces (teammate leg must 2 should 2 nit 2; the agy leg, a retry at tools=50, must 4 — of which exactly **one** was routable, the other three being Version History lines the round-eight ruling protects). Every figure below was re-derived at `6f0ee85` in this revision, none carried from a report or from the round-eight decision sheet. **(1) MUST, and it is decision H (publish every count with its unit):** the DECISION C closure published a before-figure of **3** — a bare integer, no unit — which its own published command refutes. Re-derived at the base the figure belongs to, `35698f9`: **22 occurrences across 19 lines over 8 distinct files** (`h_mad_mutation_harness.py` x9, `docsections.py` x4, `test_h_mad_portable_timeout.py` x2, `test_h_mad_collect_report_docs.py` x2, `h_mad_assemble_tdd.py` x2, and one each of `test_suite_collection.py`, `test_h_mad_context_budget_docs.py`, `test_h_mad_audit_cycle.py`), with the four commands that produce the four true integers written out beside them; the after-figure **0** is correct and was re-reproduced at `6f0ee85`. The nit that both halves were stamped `35698f9` closes with it — before at the base the before-figure belongs to, after at the freeze sha. Added, because it is the paragraph's own argument: the reconciliation of 22 against the **7** counter-instances this document reports two surfaces as having found — 7 was those readers' yield, never a census, and the 15 members no reader reached is exactly why the class is closed with a shape grep and not at the instances. The identical wrong figure in the v1.41 entry is **bracket-corrected, not rewritten**. **(2) MUST:** "The only consumer of `command` is the survivor-branch diagnostic" was a false premise about the harness. There are **four**, all inside `run_spec` (`h-mad/scripts/h_mad_mutation_harness.py:482`), re-read at `6f0ee85` and re-derivable with `grep -n 'command' h-mad/scripts/h_mad_mutation_harness.py`: `:562` the baseline gate (`BASELINE_NOT_GREEN`), `:679` the survivor diagnostic, `:694` the no-`test`-key scoring path, `:721` the post-restore read-back (`RESTORE_FAILED`). The consequence is stated **narrowed on evidence, not weakened**: `:694` becomes unreachable once Task 1 lands, because Task 1 adds the `target_command` that `_load_spec` (`h-mad/scripts/h_mad_mutation_harness.py:177`) requires beside a `test` key and raises `SpecError` at `:212` without — verified against the shipped `h-mad/tests/mutation-specs/docsections.json`, which today carries neither `target_command` nor any `test` key, so today every row takes `:694` and the pre-mutation check never runs. The already-red-killer hazard is caught **per row** by that pre-mutation check at `h-mad/scripts/h_mad_mutation_harness.py:630-641`, which runs `scoring_command`, not `command`. What is left is `:562` and `:721`: neither the baseline gate nor the restore read-back ever collects `h-mad/tests/test_h_mad_doc_block_exec.py`, which holds two of the eight killers. "Costs nothing a widened `command` would buy" is struck; the decision now names the scope it chose and what that scope leaves unverified, and names `doc_block_exec.json`'s own run — whose `command` does collect that file — as the cover. **(3) MUST, the agy leg's one routable finding:** the Task 4 exception block's *"The design's exception table agrees (v1.71, impl-plan audit v16)"* is present tense about a design **26 revisions** further on. Repaired in the Conventions rule's form **(b)**: the signature stays as this document's own constraint and the citation is re-cast as provenance, a dated historical fact. Form (b) and **not** form (a), deliberately — minting a needle into a design table row in the same round the design is being revised is how a locator arrives at 0 or 2 hits — so the locator count stays **13**. **(4) The recurrence ledger moves from four to FIVE, and the move is recorded here with its reason so a later reader does not re-file it as drift.** The round-eight decision sheet listed "ledger consistent at four" under *reproduced and UNMOVED -- do not disturb*, and that list was **stale by construction**: it described what the auditor found in the **pre-revision** document, and it was applied to a figure this revision's own fix changes. Repairing (3) above creates the fifth member, so holding the count at four would have reproduced precisely the v1.40 shape the audit caught -- a repaired member the count does not reflect. The move was raised as a departure rather than made silently, and endorsed. The general rule it yields, worth more than the integer: **never freeze a figure the same revision's fix will move.** This is the second round the ledger has been asked to move: v1.41 correctly declined (that finding was a form (a) locator breakage, a different class with a different remedy), and this time the member is genuine — the sentence in (3) asserts what a sibling contains, which is the class's definition. It is the most informative member because it is the **survivorship** arm: written at v1.17, it outlived v1.37 (the revision that wrote the rule), v1.39's item (9) — which **reported having restated it by name and did not touch it** — v1.40, and v1.41's own decision-E pass. Re-derived: `git diff 335f535 74e126f` on this file changes no `StreamPathUnwritable` prose, and `git show 74e126f:docs/01-plan/features/doc-block-exec.impl-plan.md | grep -c 'exception table agrees'` is 1, as at `0aac0b7`, at `35698f9` and at `6f0ee85`. The lesson now written into the ledger: **a sweep over a class with no detector can report a member it never edited**, so a sweep's own claim is not evidence — the diff is. The v1.39 entry is bracket-corrected on that overclaim and otherwise left standing. The form (a) bullet that used to say "NOT a fifth member" is re-stated as a **content predicate** rather than an ordinal, since the list has grown. **(5) The three agy findings that were NOT routed** are Version History lines, and they are left standing: a Version History entry is a dated record of what was true when that revision shipped, and stripping its present-tense phrasing to satisfy a rule about the present would falsify a correct record. One of them names a debt that **has since been paid** — the spec's AC-6.4 gate-command inline comment, which reads 2748/2486 when read out of the freeze commit with `git show 6f0ee85:docs/01-plan/features/doc-block-exec.spec.md`, the spec's own history recording the migration at its v1.53 and v1.54 — so that entry gains a bracketed correction. The other two ("nothing is owed to the plan", "Nothing is owed to any sibling now") could not be shown false and are left untouched, which is stated rather than left silent. **(6) SHOULD:** locator 13 of the 13 named a needle with no target file, so the hard one-hit condition the same bullet imposes could not be evaluated as written. It now carries `docs/02-design/features/doc-block-exec.design.md`, one hit at `6f0ee85`, as the other 12 do. **(7) SHOULD, a class note with no instance:** the symbol half of the tree-pin rule still has no detector; the reviewer read every pin at the freeze sha and found no counter-instance. Recorded here so the next cycle does not re-derive it and does not read the absent detector as an absent check; no edit follows. **(8) Re-derived in this revision rather than carried:** the header's three sibling versions (design v1.97 / spec v1.59 / plan v1.92), read out of the **commit** with `git show 6f0ee85:<doc> | grep -oE '^- v1\.[0-9]+' | tail -1` and not out of the working tree, because the three sibling authors are revising those files concurrently — v1.41's pins were one behind on **all three** — the fifth revision of this document whose header pins were behind by the time they were read, and the second running that all three moved at once, which the header itself enumerates (v1.35, v1.36, v1.38, v1.40, v1.41); all **13** `docs/`-sibling locators, each run as `git show 6f0ee85:<sibling> | grep -c` and each returning exactly **1** hit (decision F), three consecutive revisions now at 13/13, and each locator's own inline verification stamp moved with the measurement from `35698f9` to `6f0ee85` rather than being left behind; the bare-filename shape grep at **0** and its paragraph-folded variant agreeing — the variant itself **repaired** in this revision with `tr -s ' '`, because the fold keeps the next line's leading indentation and so missed a needle wrapped mid-phrase; found with a positive control (this document's own `never a census`, which the old form scores 0 on and the repaired form 1), which is decision A applied to a blind form that had never been shown to fire [Bracketed correction added at v1.43, impl-plan audit v40; not rewritten, because the entry records correctly what v1.42 did and only the figures it published were wrong. **The 0/1 pair is false, and it was falsified by the sentence that published it.** Measured over the body (`awk '/^## Version History/{exit}…'`) at `cf3a862`, which holds v1.42: the unrepaired fold scores **1 occurrence**, not 0, and the `tr -s ' '` fold **2**, not 1 — because v1.42's control sentence wrote the needle a second time, unwrapped, into the very text it was measuring. Over the whole file, including this entry's own two copies, `grep -o … | wc -l` on the unrepaired fold returns **3**. Neither integer carried a unit or a scope, which is decision H and is why the two readings were never reconciled. The general rule, now decision N: **a control's publication must not change what it measures.** v1.43 re-establishes the control over a **fixture file** built by a published `printf … | sed` whose needle is written into this document in a form no screen can match, so the count is independent of this document's prose; the repair itself stands — it was the evidence that did not.]; and the tree-stamp closure, extended from `35698f9` to the freeze sha — `git diff --name-only 74e126f 6f0ee85 -- h-mad handoff` is **empty**, and so is `git diff --name-only 6f0ee85 -- h-mad handoff`, so every tree `path:line` this document stamps at `335f535`, `74e126f` or `35698f9` is byte-identical both at the freeze sha and in the working tree a 5d implementer will read. **Unmoved, and re-counted from the lists rather than carried:** **81** rows (25 + 5 + 24 + 27, split 80 + 1), verified against the design's helper matrix read at `6f0ee85`, which holds **81** data rows of which exactly **1** names `SKILL.md` in its mechanism column (`registry-row-removed`); the wire spec **8** (`wire-revert-extract`, `wire-revert-select`, `wire-revert-run`, `wire-revert-substitute`, `wire-unconditional`, `hand-rolled-extraction-widened`, `exec-scan-executes`, `consumer-from-import`); `docsections.json` **8** (four shipped plus Task 1's four); five tasks, two `wiring` (Tasks 1 and 5), one shape each.
- v1.43: Impl-plan audit v40, the GATING round, answered at the freeze sha `cf3a862` from **two** surfaces (teammate leg must 2 should 2 nit 2; the agy leg PASS at tools=23, must 0 should 0 — the first clean surface of this arc, and **not** a gate: the teammate leg found two musts at the same commit, which is what the union is for). Every figure below was re-derived at `cf3a862` in this revision, none carried from a report or from the round-nine decision sheet. A closure that made the re-derivation cheap and is stated once rather than re-argued: `git diff --name-only 8909ec4 cf3a862` is empty over this document, over all three sibling documents, and over `h-mad handoff`, so every figure the audit re-derived at `8909ec4` is the same figure at `cf3a862`. **(1) MUST — the recurrence ledger contradicted itself at FOUR sites, not the three the audit named, and v1.42 had repaired two of the four one revision after fixing exactly this shape.** The four, verified at `cf3a862`: `:335` "recurred **five** times", `:474` "grown to five", `:480` "stands at **four**", `:2602` "the list stands at four" in v1.41's Version History. A fifth, of the same class and not named by either surface, was found by sweeping for derived integers rather than for the two spellings the report quoted: `:353` "the lesson **the four earlier members** do not carry", a restated `len(list) - 1`. The repair is not to increment the stale sites — that is what v1.42 did, and the count moved again. **Every live site now derives from the list**: the size of the prose-agreement list is `len(list)` and this document writes it out in prose nowhere, `:480`'s restatement is deleted (it duplicated a predicate stated seven lines above it, which is how one copy went stale while the other was repaired), "the fifth" becomes "member (5)" and "the four earlier members" becomes "the members before it" — both pointers **into** the enumeration, stable under an increment. The one historical site, v1.41's Version History, is **bracket-corrected and not rewritten**: "stands at four" records correctly what was true when v1.41 shipped. **(2) MUST, and it is decision N — a control's PUBLICATION must not change what it measures.** v1.42 published the sole evidence that its `tr -s ' '` fold repair is a repair as *"the fold as previously published scores **0** on `never a census` while the `tr -s ' '` form scores 1"*, measured against this document. The sentence stating the control wrote the needle into the document a second time, unwrapped, and destroyed the zero it reported. Re-measured at `cf3a862`, which holds v1.42, with the unit and scope v1.42 omitted (decision H): over the body, unrepaired fold **1 occurrence**, `tr -s ' '` fold **2**; over the whole file, unrepaired fold **3**. No reading yields 0, so the repair was **unevidenced**, not merely mis-numbered. Re-established by the decision-sheet's third route, a **fixture file**, combined with its second: `printf '%s\n' 'a residual reaching docsections.pyX' '  270 in _gate_bash_block' | sed 's/pyX/py:/' > /tmp/fold-control.txt` — the fixture holds the wrap, while this document holds only `docsections.pyX` and the substitution `s/pyX/py:/`, neither of which is `.py:` followed by a digit, so **publishing the control adds 0 to every figure it reports on**. That is checked and not asserted: the four screens over this document return the same **49 / 49 / 0 / 0** after this revision as at `cf3a862` before it. The full **2 × 3** grid over the fixture — two folds × three regexes, **6** readings, every one an occurrence count and every one run: unrepaired fold path-qualified **0** / bare-with-`` ` ?` `` **0** / bare-without-the-space **0**; `tr -s ' '` fold path-qualified **1** / bare-with-`` ` ?` `` **1** / bare-without-the-space **0**. Verified byte-identical under `bash` and `zsh`. **(3) SHOULD, folded in because it is the same defect one regex over:** the bare-filename half of the DECISION C closure had no published folded command and its stated reason for immunity named the **path-qualified** regex, the one with the optional space, rather than the bare one, which allows none. The folded bare command is now written out with `` ` ?` `` inserted after the colon, and the fixture's fifth integer is the demonstration that without it the repaired fold is still blind to a bare pin wrapping between colon and digits. **(4) SHOULD: the after-figures were stamped at a commit that does not contain the document they measure** — `6f0ee85` holds v1.41, not v1.42. Restated in the before-figure's own form: base `cf3a862` **49 occurrences across 19 folded paragraphs**, revised working tree **49 across 19**, unmoved, because no v1.43 edit adds or removes a `.py:` pin; the shipping commit is named as not-yet-existing rather than promised. **(5) NIT:** the pre-mutation check's span `h-mad/scripts/h_mad_mutation_harness.py:630-641` stopped one line short of the `continue` at `:642` that makes it a refusal; it is now `:630-642`, matching the three neighbouring spans in the same paragraph, all of which include their terminator. **(6) NIT:** `git rev-parse --show-toplevel` was counted among the **7** locators satisfying a selection preference the same bullet defines as "a backticked identifier, a verdict token, or an anchored table-row prefix" — it is a backticked **command**, a fourth category the enumeration omitted. The enumeration now names it; the needle is unchanged and the 7/6 split is unchanged, because the needle was never the defect. **(7) Re-derived in this revision rather than carried:** the header's three sibling versions (design v1.98 / spec v1.60 / plan v1.93), read out of the **commit** with `git show cf3a862:<doc> | grep -oE '^- v1\.[0-9]+' | tail -1` — v1.42's pins were one behind on **all three**, the **third consecutive** revision that has been, and `git diff --name-only 6f0ee85 cf3a862 --` names all three sibling files; all **13** `docs/`-sibling locators re-run as `git show cf3a862:<sibling> | grep -c -- '<needle>'`, every one returning exactly **1** hit (decision F), four consecutive revisions now at 13/13, and the sweep now records **where** each hit lands — 9 design, 2 plan, 2 spec, 9 + 2 + 2 = 13 — which surfaced a caveat a bare 13/13 hides: `git rev-parse --show-toplevel`, the spec locator, also returns one hit in the plan, so its one-hit property holds only under its stated target file; the design helper matrix re-counted at `cf3a862` (the design **moved** to v1.98 there, so this could not be inherited) at **81** data rows with exactly **1** naming `SKILL.md` in its mechanism column, `registry-row-removed`; the bare-filename shape grep at **0** on both screens and the path-qualified populations identical at **49**; and the tree-stamp closure extended from `6f0ee85` to `cf3a862` — `git diff --name-only 74e126f cf3a862 -- h-mad handoff` is **empty**, as is `git diff --name-only cf3a862 -- h-mad handoff`, so every tree `path:line` stamped at `335f535`, `74e126f` or `35698f9` is byte-identical at the freeze sha and in the working tree a 5d implementer reads. **(8) Deliberately NOT extended to the freeze sha**, and said so in the body rather than left for the next cycle to re-find: `git show 74e126f:<this file> | grep -c 'exception table agrees'` is **1**, "as at `0aac0b7`, at `35698f9` and at `6f0ee85`" — at `cf3a862` the same command returns **3**, because v1.42's repair quotes the offending sentence twice. That chain measured *absence of edit while the sentence was live*; extending it would read as a break. Same treatment for "**26** revisions behind", which is now stamped at the sha it was found at with the `cf3a862` value (27) named beside it. **(9) Inherited-unverified, named rather than passed over:** the plan's 263/76/0 and 268/76/0 heading differentials, the markdown-it-py CommonMark oracles, and the 2748/2486 suite floors were not re-run this round by either surface. **Unmoved, and re-counted from the lists rather than carried:** **81** rows (25 + 5 + 24 + 27, split 80 + 1); the wire spec **8**; `docsections.json` **8**; five tasks, two `wiring` (Tasks 1 and 5), one shape each.
- v1.44: Impl-plan audit v41, the GATING round, answered at the freeze sha `4e4a00c` from **two** surfaces (teammate leg must 3 should 3 nit 2, 18 files opened and ~150 greps, its probes run on `/tmp` copies with the repository untouched; the agy leg PASS at tools=24, must 0 should 0 — the **second consecutive** clean agy leg on this phase at real evidence levels, which is genuine and **not** a gate: the teammate leg found three musts at the same commit). This revision is written under **decision Q** — every stated property of a screen, control, sweep or probe is a claim about code, to be **executed** and never reasoned from the mechanism's design — and every figure below was re-derived at `4e4a00c` by this author, none carried from either report or from the decision sheet. The closure that makes that cheap, stated once rather than re-argued: `git diff --name-only cf3a862 4e4a00c -- h-mad handoff` is empty and `git diff --name-only 7982c18 4e4a00c` is empty over this document, so tree figures stamped `cf3a862` are the same figures at `4e4a00c`; the `docs/` siblings are what moved and every one of those is re-run below. **(1) MUST — the recurrence ledger's absence claim was falsified by its own next clause, and the audit found ONE live site where there are TWO.** The published claim was that the size of the prose-agreement enumeration is written out in prose nowhere; five words later the same sentence wrote it. Screened rather than spot-fixed: the class is a cardinal standing beside a reference to the enumeration, and the screen keys on the **verb**, which is why v1.43's "sweep for DERIVED integers" pass missed a hit phrased as past-perfect narrative. At `4e4a00c` before the edits it reads body **1** line / **1** occurrence and whole file **3** lines / **4** occurrences; on the tree this revision ships, re-run **after** the edits landed (decision K), body **0** / **0** and whole file **2** lines / **3** occurrences. The audit named the body site; the two Version History sites were found by running the screen whole-file rather than only over the scope the finding quoted. The live site now points into the enumeration by its **unbolded marker**, so a reference is never counted as a member — the marker screen reads **5** on the shipped tree. The claim is **scoped to the body** at both places it appears, with the screen and both readings published beside it, and its blind arms written out. The Version History occurrences are dated records and are **not** rewritten: v1.41's own original wording stands, and the v1.43 bracket annotating it — which is itself an instance, restating the size one clause before repeating the unscoped absolute — gains a second bracket at v1.44 that names the class and points at the sentence without quoting it, so the bracket adds no occurrence. **(2) MUST, and it is decision O: AC-6.1's corpus filter ships THREE clauses and the document controlled TWO.** The prose said "two independent clauses, two independent defects, both measured", which was true of the two defects it was written about and left the `archive` clause covered by nothing. Re-measured at `4e4a00c` by deleting one clause at a time, from the `git ls-files` side as well as the glob side wherever it appears on both: `rel.parts[0] in ('h-mad','handoff')` is **controlled** — 30 with, 2075 without, and both members contribute (27 `h-mad` + 3 `handoff`); the dot-directory clause is **controlled** — 30 with, 35 without, the five additions exactly the five named `.pytest_cache/README.md` paths; `'archive' not in rel.parts` is **UNCONTROLLED** — deleting it moves none of the four dated integers (`p.parts` **0 → 0**, rel-rebased dot-excluded **30 → 30** against a git side also **30 → 30**, dot-clause-dropped **35 → 35**), because `git ls-files -- h-mad handoff | grep '\.md$' | grep -c '/archive/'` is **0** at this sha, the glob's archive-drop set is empty, and the clause sits on both sides of invariant (ii)'s equality where it cancels. A clause that drops zero paths on this tree **cannot** be positively controlled on this tree, so it ships as a **stated blind arm** — prescribed by the definition, not by any measurement here — with the consequence spelled out: a 5d implementer who omits or misspells it gets a byte-identical corpus and AC-6.1 still asserts exactly 1. The rule is now stated for the class: one published reading per clause with that clause removed, never one reading for the composite. **(3) MUST, and it is decision Q's headline instance in this document: the standing control that enforces the `SKILL.md`-pin class is FOLD-BLIND.** The document cites `h-mad/tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins` twice as the reason it may omit a line number. That control's reach is a property of the shipped extractor — the module-level `_CODE` in `h-mad/scripts/h_mad_precheck_doc.py`, whose span may not contain a newline — so a path-qualified pin wrapped across this document's ~95-column fold produces no LINEPIN detail and the assertion passes on it. **Probed in both directions rather than argued**, on copies under `mktemp -d` with the repository untouched: the flat form yields **1**, the identical pin split across a fold yields **0**, the unedited document yields **0**, byte-identical under `bash` and `zsh`, run with the control's own `--phase design`. Both citation sites now state the residual, and the uncovered half is closed with a line-scoped and a folded `SKILL.md` screen over the body, both **0** on the shipped tree. **Those screens are shown not to be blind, on real history**: both read **1** at `74e126f` — the commit whose v1.39 shipped the sixth recurrence — and **0** at `335f535`, `35698f9`, `cf3a862`, `7982c18` and `4e4a00c`, twelve readings run. That positive is a fair test of the line-scoped form and only a partial one of the folded form, because v1.39's pin was unwrapped; the folded form's own arm is supplied by the probe's wrapped/flat pair, and this asymmetry is stated rather than glossed. **(4) SHOULD, decision O again: the fence-state scan's true negative was a disjunction reported as a total.** `declined-inside-fence 2` came from a two-term `or`. Re-run at `4e4a00c` with the disjuncts split — the published line reproducing verbatim beside them — it is **space-disjunct 2, tab-disjunct 0**, both in one file, `h-mad/references/inline-protocols.md`. So the 2 is evidence about space-indented runs and none at all about tab-indented ones; the **tab arm is now declared blind on both sides** of that scan, 0 openers and 0 declines, matching the disposition the tab arm already carried on the positive side. **(5) SHOULD, decision O a third time: the bare-filename screen's leading alternation had a branch that had never fired.** Over the before-population at `35698f9` — the 22 occurrences the document enumerates, which reproduce exactly at 22 / 19 lines / 8 files — `grep -cE '^[A-Za-z0-9_]+\.py:[0-9]+'` is **0**: all 22 matched through the character-class branch, and the fold fixture's needle is preceded by a space, so it exercises only that branch too. A **separate** column-0 fixture now fires the other branch, kept separate so the 2 × 3 grid's six readings are untouched; four readings, both shells, byte-identical: at column 0 the `^`-anchored form returns **1** and the whole screen **1**; with one leading space the `^` form returns **0** while the whole screen still returns **1** — the two branches **discriminate from each other** rather than one covering for the other. **(6) SHOULD: the inherited-unverified register is now stated AT THE SITE, not only in a Version History item.** The 2748 / 2486 suite floors and the plan's 263/76/0 and 268/76/0 heading differentials with their markdown-it-py CommonMark oracles have now gone **three consecutive rounds** with no surface on either leg re-running them, and this revision did not re-run them either — a `--collect-only` pass over the suite is not something this authoring pass took. They are labelled inherited-unverified beside the numbers themselves. **(7) NIT: the four screens' four integers now carry an ordering key** — path-qualified line-scoped / path-qualified folded / bare line-scoped / bare folded — named where the tuple is written instead of inferable from a list several lines earlier. Every count carries its unit (decision H); a count in a tuple also carries its identity. **(8) NIT: the fold fixture no longer writes to a fixed shared path.** It uses `mktemp -d` and removes it, and because a fixture's path is part of the command that produces its readings, the **whole 2 × 3 grid was re-run under both `bash` and `zsh` after the change**: unrepaired fold **0 / 0 / 0**, `tr -s ' '` fold **1 / 1 / 0**, byte-identical. **Re-derived in this revision rather than carried:** the header's three sibling versions read out of the **commit** with `git show 4e4a00c:<doc> | grep -oE '^- v1\.[0-9]+' | tail -1` — design **v1.99**, spec **v1.60**, plan **v1.94**, so v1.43's pins were one behind on the design and the plan and **correct on the spec**, breaking a three-revision run of being behind on all three (`git diff --name-only cf3a862 4e4a00c --` over the spec is empty); all **13** `docs/`-sibling locators re-run at `4e4a00c` and, this time, **each against all three siblings — 39 readings** — every one returning exactly **1** hit in its target, split 9 design / 2 plan / 2 spec = 13, with exactly one off-target hit in the whole 39 (`git rev-parse --show-toplevel`, the spec locator, also returns 1 in the plan, so its one-hit property holds only under its stated target file); the design's helper-spec mutation matrix re-counted at `4e4a00c` because the design moved v1.98 → v1.99, at **81 data rows** and **81 distinct row names**, exactly **1** naming `SKILL.md` in its mechanism column (`registry-row-removed`), so 80 + 1, with all 81 names tested for membership in this document and **0 missing**; the four `.py:` screens at **49 / 49 / 0 / 0** in the ordering key above, across **20** folded paragraphs — **19 → 20 is this revision's own edit moving a figure it published**, caught by re-running after the edits landed rather than before them (decision K): the occurrence count is unmoved at 49 and the pin population byte-identical (both lists sorted and diffed, empty), while a fenced block inserted here split one pin-bearing paragraph in two, so the paragraph count is a fact about line breaks and 49 is the invariant; the AC-6.1 corpus relation at **30 / 30 / 35 / 0** with the symmetric difference empty; **all four addends of `25 + 5 + 24 + 27` derived individually for the first time**, by intersecting each task's "Mutation rows added" block with the design's 81 row names at `4e4a00c` — Task 1 **25**, Task 2 **5**, Task 3 **24**, Task 4 **28 minus one cross-reference = 27**, the cross-reference being `empty-key-accepted-by-api`, a Task 2 row named in the Task 4 block only to discriminate `cli-empty-key-delegated` from it, exactly as the prose there already says; the four sum to **81**, the union over the four blocks is **81**, and **0** design rows are listed in no block; the tree closure `git diff --name-only 74e126f 4e4a00c -- h-mad handoff` and `git diff --name-only 4e4a00c -- h-mad handoff` both empty; **five** tasks, **two** `wiring` (Tasks 1 and 5), one shape each and no task carrying two. **Executed, not asserted** (decision Q's operative list): the LINEPIN fold probe in both directions plus its unedited control; the archive-clause deletion on both sides of the AC-6.1 relation; the fence-scan disjunct split; the `^`-branch fixture in both positions; the 2 × 3 grid re-run after the `mktemp` change under two shells; the prose-size screen before and after this revision's own edits; the `SKILL` screens across six shas; all 39 locator readings. **NOT executed and NOT re-derived this round, stated as contract rather than courtesy:** the 2748 and 2486 suite floors; the plan's 263/76/0 and 268/76/0 differentials and their CommonMark oracles; the `__all__` name counts 25 / 29 and the 20-exception hierarchy, which have no landed source to check against; and the Task 2–4 AC bodies and RED/GREEN gate commands, which were read but not run. The eight `PLACEHOLDER`-shaped precheck hits are the **output-line grammar specimens** in the Task 4 verdict-line paragraphs — the `stream`, `os_error` (×3), `overlap`, `pgid` and the two verdict-argument forms of the `DOCBLOCK:` grammar line. They are deliberate and are passed to the precheck as `--allow` substrings, never removed. **Their slot texts are deliberately NOT quoted here, and that is a measured decision, not fastidiousness**: a first draft of this entry enumerated the eight slot tokens as backticked spans, the precheck read those eight as eight fresh `PLACEHOLDER` hits, the total went 8 → 16 and `test_noise_floor_on_documents_that_survived_eighty_cycles` went **RED on the working tree** at its ceiling of 12. That is decision N one document over — the sentence describing a detector's findings became findings — and it was caught by running the suite after the entry was written rather than before it. With the entry in this form the precheck is `PRECHECK: PASS issues=0` under the eight `--allow` substrings and the file is **24 passed**.
- v1.45: Impl-plan audit v42, answered at the freeze sha `68a70d6`. **This revision does not claim a two-surface round.** The teammate leg reported must 1 / should 3 / nit 2 over 26 files and 118 commands; the agy leg's verdict file was **empty when this revision was authored**, and whether that was a failed leg or a file read while the leg was still in flight was unresolved at the time — this entry does not settle it. Either way no second-surface verdict was in hand while this was written, so nothing here counts as a clean second surface, and the findings below are weighed on their evidence rather than on their gating status. Every figure was re-derived at `68a70d6` by this author; nothing is carried from the report or from the decision sheet (decision P). The closure that makes the tree figures cheap, stated once: `git diff --name-only 4e4a00c 68a70d6 -- h-mad handoff` is **empty**, so every tree figure stamped `4e4a00c` is the same figure here; what moved across that span is `docs/` — the design, the plan, this document and four audit reports — so the `docs/`-facing figures were re-run rather than carried, and the spec is **not** in that diff. **(1) MUST, and it is decision Q's exact shape: the marker screen published a reading it had never been run to produce.** v1.44 wrote that `grep -oE` over the bolded-marker form reads **5**; run verbatim it returns **6**, at `4e4a00c` and at `68a70d6` alike, so this was a claim about a document state that never held. The sixth hit was a *reference* to member (4) in the Conventions section, written in the member form — the precise failure the unbolding was introduced to prevent, shipped inside the sentence claiming it was prevented. Fixed by executing rather than by restating: the reference is unbolded, and the screen is republished in the form its neighbours already use — an `awk`-scoped fenced block, a body reading and a whole-file reading that must agree, and a third `sort | uniq -c` arm that needs no target at all, since a reference in the member form necessarily duplicates an existing marker. **The target is now stated as `len(list)`, never the literal 5**, because a literal target reads a correct six-member document as the defect it exists to catch. **The residual is demonstrated, not argued**, on `mktemp -d` copies with the repository untouched and each mutation named exactly: re-bolding that one reference alone reproduces the v1.44 state (body 6, file 6, a count of 2 on the fourth marker, both arms firing), while re-bolding it *and* unbolding the member it points at gives body 5, file 5, every count 1 — **all three arms pass on a document where a reference is written as a member**. The screen is blind to a cancelling pair and to nothing else, and that is written at the site. All three readings were re-run **after** these edits landed (decision K). **(2) SHOULD: the mutation-payload axis misclassified two rows, and only the enumeration beside it saved them.** The axis was keyed on whether the row's anchor file exists *at HEAD*; the two `docsections.json` rows Task 1 re-anchors carry `"file": "tests/docsections.py"` in the shipped spec today, a file that does exist, so the rule as worded put them on the payload-now side where the enumeration then correctly forbids them — a 5e implementer applying the rule rather than reading the list got two refusals. The axis now reads *the anchor file **after the task that lands the payload***, with the contradiction and its blast radius written out, and the shipped file's cardinality stated beside the planned one: **four** rows in `h-mad/tests/mutation-specs/docsections.json` at `68a70d6`, all four carrying that `file` value, against the eight this feature ships by 5e. **(3) SHOULD: AC-6.1's `2075` was the one control integer that is not a function of the commit it is stamped at.** With the root clause deleted the glob walks untracked files: 2075 at `4e4a00c`, **2076** at `68a70d6`, **2079** while this entry was being written, the differences being untracked audit reports written under `docs/` by concurrent agents. It is dated rather than dropped, the other three integers (30 / 30 / 35 / 0) are all functions of tracked state or of the named `.pytest_cache` set, and the 30 side is exact at all three readings (27 `h-mad` + 3 `handoff`, re-derived at `68a70d6`). **(4) SHOULD, and it is the four-rounds-uninspected register: the AC-6.4 floors are now PARTLY DISCHARGED and the undischarged part is named.** Executed at `68a70d6` rather than transcribed, `python3.11 -m pytest --collect-only -q -p no:cacheprovider` collects **2809** from the repository root and **2547** from `h-mad/` — divergence **262**, exactly the divergence this document publishes, reproduced live. Still **not** verified, and labelled so: **2748** and **2486** at `b7d0d77`, which need a checkout of that commit this pass did not take, and the plan's 263/76/0 and 268/76/0 differentials with their markdown-it-py oracles, which are the plan's figures and are only cited here — **fourth** consecutive round with no surface re-running those. The live run does fix the staleness: 2748 → 2809 and 2486 → 2547, both **+61**, and a floor stale by N tolerates N invisible deletions, which is why the constant is re-measured at 5c. **A second-authority stamp was found while fixing this and is removed**: the Conventions site stamped the pair at `1861157` while AC-6.4 stamps it at `b7d0d77`, four commits earlier. The values do not disagree — `git grep -hE '^\s*def test_'` over `*test_*.py` at the three commits without a checkout returns **1450 / 1450 / 1450**, flat — so the stamp that carries the command is the one that stands; that predicate's 1450 is not AC-6.4's 2675, whose own predicate is unpublished, so the invariance is verified here and the absolute is not. **(5) NIT: "the eight `--allow` substrings" in the v1.44 entry mixes two units.** The precheck emits **eight** `PLACEHOLDER` hits spanning **six** distinct spans — the `os_error` specimen accounts for three of the eight — and `PRECHECK: PASS issues=0` is reached with **six** `--allow` values, reproduced at `68a70d6`. By decision H the phrase is "eight hits under six `--allow` substrings". The v1.44 entry is a dated record and is **not** rewritten; this is the correction. **(6) NIT: the sentence carrying the bolded reference separated its subject from its verb across the fold by a 26-word parenthetical** — the same shape v1.40's nit fixed one paragraph over. Split into three sentences in the same edit that unbolded the marker, which also makes the marker visible to the next reviser. **Re-derived at `68a70d6` rather than carried:** the header's three sibling pins, read out of the **commit** — design **v1.100**, spec **v1.60**, plan **v1.95** — so v1.44's pins were one behind on the design and the plan and **correct on the spec**, the second consecutive revision not behind on all three; all **13** `docs/`-sibling locators re-run against **all three** siblings, **39 readings**, every one returning exactly **1** hit in its target (9 design / 2 plan / 2 spec) with exactly one off-target hit in the whole 39, the spec's `git rev-parse --show-toplevel` locator also returning 1 in the plan, unchanged from v1.44; the design's mutation-matrix row names taken at `4e4a00c` and at `68a70d6` and **diffed**, not re-counted — the two sets are **identical** (89 names under `^| \`row\` |`, the 81 helper rows plus the 8 wire rows), which is what lets v1.44's 25 / 5 / 24 / 28 intersection, its union of **81** and its sole cross-reference `empty-key-accepted-by-api` stand without re-deriving them against a moved design; the four `.py:` screens; the prose-size screen; the `SKILL.md` screens; and the precheck. **Property-claim accounting, the standing metric.** Claims this revision ships **as measurements**: **20**. Executed at `68a70d6` by this author: **20**. Unexecuted: **0**. Shipped as *transcriptions* with the inherited-unverified label attached, which is a different category and is not counted as measured: **four** — 2748/2486 at `b7d0d77`, AC-6.4's 2675 `def test_` census, the plan's 263/76/0 and 268/76/0 with their CommonMark oracles, and the `__all__` name counts 25 / 29 with the 20-exception hierarchy, which have no landed source to check against. **NOT executed and NOT re-derived this round, stated as contract rather than courtesy:** those four, plus the Task 2–4 AC bodies and RED/GREEN gate commands, which were read but not run.
- v1.46: Impl-plan audit v43, answered at the freeze sha `6dcb70f`, with **every figure below re-derived at `7d8e797`** — the sha this revision is authored against and the sha each re-run it publishes is stamped at. The two shas hold all four gated documents byte-identically (`git diff --stat 6dcb70f 7d8e797 --` over the design, the plan, the spec and this file is empty); what moved across that span is `docs/` — `git diff --name-only 6dcb70f 7d8e797` names **seven** files, five audit reports plus one handoff and `docs/learnings.md` — which is exactly why the one figure here whose corpus is a live directory is now stated as **unbounded** rather than dated (decision K). **This revision does not claim a two-surface round.** The teammate leg reported must 1 / should 2 / nit 2 at that freeze; the agy leg reported must 0 / should 0 and **is not a gate** — one clean surface has never been the gate on this phase, and with the codex surface exhausted until 2026-09-07 both legs this round share a model family with the authoring surface. **Decision-Q accounting: one unexecuted property claim was outstanding in v1.45, it was executed, and it was the must-fix.** **(1) MUST — AC-6.4 published a predicate for its `2675` census and called the result `verified`; run, the predicate returns `1450`.** `git grep -hE '^\s*def test_' <sha> -- '*test_*.py' | wc -l` returns **1450 / 1450 / 1450** at `e8eaf6f` / `b7d0d77` / `1861157`, re-run here at `7d8e797`. The **invariance** that AC-6.4 actually needs — no test function entering or leaving the tree across that span — is therefore measured and is kept; the **absolute** `2675` is not, and the word `verified` is withdrawn from it. **The class, not the instance**: the inherited-unverified register lived only in the 5f note while AC-6.4 carried `2748`, `2486` and `2675` as the constants 5c re-measures from with no label at all. **The rule now written over it**: a figure in that register carries the label **at every AC site that uses it**, and is described as `verified` nowhere [v1.47: widened to **every site that uses it** — the AC-scoped wording did not reach the §Verification (Phase 5f) gate paragraph, which is where a 5f operator meets `2748` and `2486`; the label now stands there too]; the register itself is corrected from "two things" to **three**, `2675` being the addition. **Residual, as a category**: the predicate that produces 2675 could not be constructed — eight readings were run at `e8eaf6f` in this revision (anchored in `test_*.py` 1450, unanchored in `test_*.py` 2721, anchored over all `*.py` 1455, unanchored over all `*.py` 2748, unanchored over `*test*.py` 2731, unique names 2691, `async`-inclusive 1474, every tracked file 2808) and **none is 2675**, while `grep -c '2675'` over the design, plan and spec at `7d8e797` is **0 / 0 / 0** — so the number is inherited, not refuted, and no substitute was invented for it. The fourth of those eight collides numerically with the `2748` collected baseline and is labelled at the site as a grep-hit count so the collision cannot be read as corroboration. **(2) SHOULD — v1.45's closure that the `docs/`-facing figures "were re-run rather than carried" was asserted, not screened, and was false.** The design moved 161 insertions / 37 deletions across `4e4a00c`..`68a70d6` while the 81-row derivation still carried a `4e4a00c` stamp. The figures were all correct, so this was a **stamp defect, not a figure defect**, and the repair is the screen rather than a new adjective: `awk '/^## Version History/{exit}{print}' <this file> | grep -oE 'at .<sha>.' | wc -l`, whose readings on the shipped body are **11** for `4e4a00c`, **5** for `68a70d6` and **22** for `7d8e797`, with `verified at .4e4a00c.` at **0** against `verified at .7d8e797.` at **13**. Those 13 are re-runs, not re-stamps: all 13 sibling locators were re-run at `7d8e797` and each returns exactly one hit, split **9** design / **2** plan / **2** spec = 13, with the one caveat intact (`git rev-parse --show-toplevel` also returns one hit in the plan). The 81-row derivation was re-run at `7d8e797` over `git show 7d8e797:<design>` — **81 data rows, 81 distinct names, exactly 1 naming `SKILL.md` in its mechanism column (`registry-row-removed`), 0 of the 81 missing from this document** — against a design that moved **303 insertions / 39 deletions** since the previous stamp, and the span is now given as that command rather than as a design version number. Two further closure sentences of the same class were rewritten to point at the screen instead of asserting a set, both in the Conventions `.py:`-pin paragraph: the one naming `68a70d6` as "the commit every figure below was re-derived at", and the one asserting that each `docs/` figure "is re-derived at `4e4a00c` in this revision". (The 13-needle sweep was re-**run** and re-stamped, not rewritten; it is not one of those two.) **Residual**: the screen counts stamps, not correctness — it cannot tell a re-run stamp from a re-typed one, and it says nothing about the `4e4a00c`, `68a70d6`, `cf3a862`, `335f535` and `1861157` stamps that remain because this revision did **not** re-run what they cover (11 / 5 / 4 / 19 / 6 readings respectively); those stay dated provenance, the `68a70d6` five — the live 2809 / 2547 collection run among them — as much as the older ones. [v1.47: **those five readings are each exact and the SET was not.** The body stamps **fourteen** distinct shas, so the five named here are five of the **thirteen** non-`7d8e797` ones and eight went unnamed — an enumeration with members quietly dropped, which is the failure this document's own AC-6.4 wording names. Repaired by deriving the population rather than typing it: the screen is now published as a `sort | uniq -c` over every sha, at both of the two places it is written, and the whole table is in the v1.47 entry below.] **(3) SHOULD — AC-6.1's without-root-clause integer drifted a third time (2075 / 2076 / 2079) and now reads 2088.** It is not dated again; it is characterised: with the root clause deleted the glob walks untracked files, so the reading is **a property of a working tree at a moment and of no sha**, rising with untracked `docs/` writes by concurrent agents and falling when they are committed or cleaned. The four datings are kept as illustration and the control's conclusion is unaffected — the four sha-reproducible readings re-run here print **30 / 30 / 35 / 0** with the symmetric difference empty, on a tree byte-identical to `7d8e797` over `h-mad handoff` (`git status --porcelain -- h-mad handoff` empty). **Residual**: this document has exactly one such unbounded figure and the characterisation covers only it; a future figure whose corpus is `docs/` would need the same treatment and nothing here detects one automatically. **(4) NIT — the `sed` mechanism sentence compressed two programs' failures into one chain.** Re-run on a `mktemp -d` copy: `sed` exits **1** and prints `RE error: repetition-operator operand invalid` on stderr — loud, not silent — and the **empty file is the shell's**, which truncates the `>` target before `sed` runs. Both steps are now named. **(5) NIT — the exception-hierarchy header wrote four addends against five headed groups**; it now reads `(6 + 3 + 4 + 5 + 1)`, one addend per headed group, summing to the 19 `class …(DocBlockError)` definitions counted in the block below it. **Owed to a sibling and deliberately not acted on**: the design's audit raises a term collision with this document on "re-anchored". The design side is a **dated reading, not a present-tense claim** — `git show 7d8e797:docs/02-design/features/doc-block-exec.design.md | grep -c 'four re-anchored originals'` returned **1** at that sha, which is the reading this note was written from; this document's side is Task 3's `docsections.json` row list, "the four existing (two re-anchored)". The two phrases count different things — this document's four are the pre-existing rows, of which two are re-anchored — so the collision was real and was a **harmonisation, not a defect on one side**; it was reported to the orchestrator rather than resolved here, because the design author was revising concurrently and a unilateral edit on either side would have made the pair disagree in a new way. [v1.47: **closed, and nothing is owed.** The same command against `1cbddb7`, the commit v1.46 actually shipped in, returns **0** — the design dropped the adjective on its own side in the same batch. As first written this note stated what the design *currently* said, with no command and no sha, which is the very form this document's Conventions rule forbids in its body; a note to the orchestrator about a sibling expires exactly as a body sentence does, and an orchestrator acting on the unqualified form would have re-dispatched a harmonisation with only one side left. The rule is now explicit: a sibling's text is quoted **as a reading at a sha with the command beside it**, in the Version History as much as in the body.]
- v1.47: **DELTA SELF-REVIEW r13, not a gating round.** The subject was the *diff* `git show 1cbddb7 -- <this file>` and the findings that diff claimed to answer, on one surface (must 1 / should 4 / nit 3); the gating cycle runs after this batch lands, at the commit this batch produces. **Every figure below was re-run after this revision's LAST edit landed, and the two that a Version History edit could still move — the two whole-file readings — were re-run again after this entry was written** (decision K, and the reason the must exists). Sibling pins in the header re-derived at `1cbddb7`: design **v1.102**, plan **v1.97**, spec **v1.60** — v1.46's pins were one behind on the design and the plan and correct on the spec, the fourth consecutive revision in that shape. **(1) MUST — v1.46's own repair broke the marker screen, and the repair had been re-run BEFORE the repair rather than after it.** The `sed` mechanism sentence quoted the failing invocation verbatim and the search half of that invocation was a bolded marker, so the body reading went to 6 with a count of 2 against the fourth marker — the arm-(a) signature this document publishes — while the paragraph three above it published 5 and asserted it had been re-run after the edits; what the reading establishes is that it was **not** re-run after the repair landed, not what was or was not run before it. Repaired by describing the failing pattern instead of reproducing it; the screen now reads body **5**, whole file **5**, five per-marker lines each with count **1**. **The class, not the instance**: *a screen whose needle can be written literally inside prose that describes the screen* — a quoted mutation string, error message or diff hunk carries the needle into the counted scope and no screen can tell a quotation from a member. **The rule now written over it**: no screen's needle may appear literally anywhere in the scope that screen counts; a needle that must be discussed is described. **Residual, as a category**: this reaches literal-string needles only — a regex-class needle can be matched by prose containing no literal copy, which the restated-cardinal screen is, and nothing detects that case. **The sweep, enumerated in the body rather than asserted**: six screens are scoped to this document and are therefore exposed at all; four had the rule applied before it was named (the `.py:`-pin screens' described-not-reproduced counter-instances since v1.40; the `SKILL` probe's stand-in-plus-substitution fixture; the stamp screen's sha written as a pattern; the member-(5) chain's deliberate stop), one is the regex-class residual, and one was the instance. Every other screen here counts `h-mad/`, `handoff/`, a sibling under `docs/` or a `.py` source file, where this document's prose is out of scope by construction. **(2) SHOULD — the stamp residual's five figures were each exact and the SET was not.** The body stamps **fifteen** distinct shas after this revision, so v1.46's five named shas were five of thirteen and eight went unnamed. Repaired at the instrument, not at the sentence: the screen is now published as a `sort | uniq -c` over every sha, spelled identically at both of the two places it is written, and the whole table is here. **The table on this revision's shipped body, 109 readings over 15 shas**: `1cbddb7` 22 · `335f535` 19 · `35698f9` 12 · `4e4a00c` 11 · `b7d0d77` 9 · `74e126f` 6 · `1861157` 6 · `e8eaf6f` 5 · `68a70d6` 5 · `cf3a862` 4 · `6f0ee85` 4 · `7d8e797` 2 · `6b4df35` 2 · `8909ec4` 1 · `0aac0b7` 1. The 22 are this revision's re-runs, and they are re-runs and not re-stamps: all 13 sibling locators were re-run against `git show 1cbddb7:<sibling>` and each returns exactly one hit, split **9** design / **2** plan / **2** spec, with the single caveat intact and still the only one (the toplevel needle also returns one hit in the plan; all 13 were run against all three siblings to establish that). The 81-row derivation was re-run over `git show 1cbddb7:<design>` against a design that moved **136 insertions / 33 deletions** since the previous stamp — **81 data rows, 81 distinct names, exactly 1 naming `SKILL.md` in its mechanism column, 0 of the 81 missing from this document**. **Residual, two of them and both concrete**: the screen counts stamps, not correctness, so it cannot tell a re-run stamp from a re-typed one; and it cannot tell a **run** stamp from a **subject** stamp — the `e8eaf6f` / `b7d0d77` / `1861157` readings name the commits a figure is *about* rather than commits anything was run at, and a reader who treats the whole table as re-run provenance will over-read it by that much. The other 87 readings are dated provenance this revision did not re-run and the table names every one of them rather than a chosen five. **(3) SHOULD — a carried parenthetical in the `.py:`-pin bullet contradicted the hunk v1.46 inserted three lines above it**, asserting that "every figure here names `4e4a00c`" while the body stamped many more shas than that. Rewritten to the standing mechanism — the commit a revision ships on does not exist while it is being written, so a figure names the sha it was **taken** on — with the closure assertion removed and the question of *which* shas were re-run handed to the stamp screen, which is where the SHOULD-1 repair put it. **(4) SHOULD — the "owed to a sibling" note stated what the design CURRENTLY said**, with no command and no sha, which is the form this document's Conventions rule forbids in its body; and it was already false at the commit v1.46 shipped in. Bracketed as a dated reading with the command: the needle returned **1** at `7d8e797`, the reading the note was written from, and **0** at `1cbddb7`, the design having dropped the adjective unilaterally in the same batch. Nothing is owed; the rule is that a sibling's text is quoted as a reading at a sha in the Version History as much as in the body, because a note to an orchestrator expires exactly as a body sentence does. **(5) SHOULD — AC-6.1 listed four datings and still told the reader the conclusion was unmoved by "which of the three you get".** The cardinal is dropped rather than re-typed as four (decision H): the list is open-ended by construction — the figure is a property of a working tree at a moment — so any cardinal beside it drifts at the next dating. Re-run on this revision's working tree it reads **2091**, a fifth value in four days, which is the stated behaviour and not a defect; it is deliberately not added to the illustration list, because extending an open-ended list every round is the treadmill the characterisation replaced. **(6) NIT — the sixth of AC-6.4's eight falsification readings was the only one whose command was not reconstructible from the text.** "Unique names via `sort -u`" reproduces only as an `-o` *name extraction*; `sort -u` over whole lines gives 2697, not 2691. The extraction is now written out and the 2697 collision is named beside it so the member is re-runnable like its seven siblings. **(7) NIT — the inherited-unverified label's scope was written as "every AC site", which does not reach the §Verification (Phase 5f) gate paragraph** — the paragraph a 5f operator actually reads, and the one carrying `2748` and `2486` as the pair the gate runs against. Widened to **every site**, and the label now stands beside that pair. **(8) NIT — the 5f paragraph said "the predicate behind 2675 is not published here", which AC-6.4 no longer makes true**: AC-6.4 publishes a predicate and reports it falsified. Restated as what it is — the invariance is verified in that paragraph, the absolute is verified neither there nor at AC-6.4. **Screens and derivations re-run on the shipped body, every one after the last edit**: marker **5 / 5 / five lines each 1**; restated-cardinal body **0 lines / 0 occurrences**, whole file **2 / 3**, all three inside the Version History as before; the four `.py:` screens **49 / 49 / 0 / 0** at **20** folded paragraphs, base and shipped tree alike, pin population byte-identical; both `SKILL` screens **0 / 0**; the member-(5) chain's self-count unchanged at every sha it names; AC-6.1's four sha-reproducible commands **30 / 30 / 35 / 0** with the symmetric difference empty and the five dropped paths exactly the five named; the tagged-fence RED prediction **0**; the `def test_` triple **1450 / 1450 / 1450**; and `grep -c '2675'` over the three siblings **0 / 0 / 0**.
- v1.48: **Round-thirteen GATING audit (impl-plan audit v44), answered at the freeze sha `700c599`** — teammate leg must 2 / should 3 / nit 2 over 24 files and 128 commands. **This revision claims no gating pass, no two-surface clean and no exit gate.** `codex` is exhausted until 2026-09-07, so every surface this round shares a model family with the authoring surface; the agy leg returned `AUDITCYCLE: PASS must=0 should=0` while its gating teammate found the two musts below — the third consecutive round a clean agy leg sat beside real defects — and it is **not** cited as evidence about this document. A real codex round on this tree is still owed. Sibling pins in the header re-derived at `700c599`: design **v1.103**, plan **v1.98**, spec **v1.60** — v1.47's pins were one behind on the design and the plan and correct on the spec, the **fifth** consecutive revision in that shape (`git diff --name-only 1cbddb7 700c599 --` over the three siblings names the plan and the design and does not name the spec). **Every figure below was re-run after this revision's LAST edit landed** (decision K), and the run caught one of its own repairs: see the self-reference screen's reading of 1 below. **(1) MUST — eight body sentences attributed an earlier revision's sha or state to the revision being read, and the class reached the INHERITED-UNVERIFIED register's own discharge claim.** Three sentences called `4e4a00c` the freeze sha this revision is authored against while three others correctly named `1cbddb7`; **two**, in a single AC bullet, presented v1.41's toolchain re-sweep and the residual v1.41 added as the shipping revision's; one presented v1.44's re-read of the mutation harness as the shipping revision's; one wrote "before this revision" about an arm v1.41 had added; and one wrote "Executed at `68a70d6` in this revision" on the sentence that discharges half the register — v1.45's execution published as the shipping revision's, which is the one sentence a reader must be able to trust, because it is the sentence asserting that a figure stopped being inherited. **The measurable consequence, and it is why this was a must**: the restated-cardinal screen's before/after pair took its "before" from `4e4a00c`, where the reading is body 1 line / 1 occurrence, and published it against a v1.47 "after" of body 0 / 0 — but at `1cbddb7`, v1.47's actual base, that screen already read 0 / 0 and whole file 2 / 3, identical to the "after". A decision-K contrast whose two halves cannot differ measures nothing the revision did, which is the defect decision K exists to prevent, one level up. **The repair is not eight edits.** Every relative self-reference in the body is replaced by the version number it belongs to — `v1.44's base`, `re-swept at v1.41`, `first executed at v1.45 and re-executed for v1.48` — taking the body population from **21** to **0**. Where the label was replaced by a re-run rather than by a name, the re-run was performed: the 13 sibling locators, the stamp closure, the 81-row derivation, AC-6.1's four commands, the collect-only pair and AC-6.4's eight falsification readings were all re-executed for v1.48 — the first five stamped at `700c599`, the eight readings against `e8eaf6f`, which is the commit they are about. **The class**: a phrase meaning "the revision you are reading", carried across a revision boundary without re-labelling; nothing about such a sentence changes when it goes stale. **The rule, now written in Conventions**: no body sentence identifies the shipping revision by a relative phrase. **The screen, and it is a gate rather than the triage grep the audit's residual described**: an `awk`-scoped body sweep for the two live forms, whose needles are written as regex **character classes** so the published screen cannot match itself. It reads **0** on the shipped body. That screen is member (x) of the exposure enumeration and the only member whose exposure is closed by construction. **Residual, as a concrete category**: the screen sees exactly the two forms found live. Relative *time* words — "today", "currently", "one round later" — are a different axis, describing the tree rather than the revision, and are covered by the tree-stamp closure; a self-reference in some third wording would read 0 here and be caught only by a reviser reading. **The rule bit its own statement, and that is recorded rather than tidied away**: the sentence exempting the Version History originally quoted the phrase it was about, which put a live needle into the counted scope and drove the screen to **1** in the same paragraph that publishes **0**. It was caught by running the screen after the last edit instead of before it, which is the whole of decision K in one instance. **(2) MUST — the needle-inside-scope exposure enumeration was published as complete at six and was short by at least one.** An enumeration published as complete is a completeness measurement under decision G, and v1.47 derived it by recalling what it had repaired. Re-derived by **walking** — keying on body lines that name this file as a scope (its path, the shell variable the fenced screens bind it to, or the angle-bracketed stand-in this document writes for its own path) and on the `awk` idiom every body-scoped screen uses to stop at the Version History heading, then reading each hit to separate instruments from provenance citations — the population is **ten**, not six. The three the walk added: **(vii)** the pre-dispatch sibling-claim sweep, all four of whose needles are literal and present in the body it counts, whose 25 body hits classify as 6 exposure, 1 live use, 18 substring confound and 0 defects — the classification derived line by line, because the first pass at it wrote "three are the exposure" from reading and under-counted by half — and whose disposition is that it publishes **no reading**, so its cost is untriaged noise rather than a wrong integer; **(viii)** the six-token GNU-vs-BSD divergence sweep in Task 1's AC checklist, which *does* publish a reading — **3** — and whose reading survives only because each hit is named and triaged rather than compared to a target, a disclosure that stood at the site and was missing from the enumeration; and **(ix)** the wrapped/flat precheck probe, a different **program** over copies of this document, sharing the `SKILL` screens' stand-in device but not reached by a repair to them. The tenth is the self-reference screen this revision adds, enumerated because it was written under the rule rather than found by it. **Residual of the WALK, as concrete categories rather than of the rule** — three, and the third has a live member: an instrument whose scope reaches this file through a variable bound in an earlier paragraph and never re-named; an instrument scoped to a **directory** containing this file, which AC-6.1's control with its root clause deleted actually is, exposed to nothing only because its needle is a path glob; and an instrument scoped to this document that lives **outside** it, which no walk of this file can reach — `h-mad/tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins` runs the shipped precheck over this document and asserts a needle form is absent, so a needle typed into this body turns a **shipped test red** rather than moving a published integer. It re-runs green on the shipped body. **(3) SHOULD — the inherited-unverified label did not reach the site that USES `263/76/0` and `268/76/0`.** AC-6.4 states the rule as "every site that uses it" and the 5f paragraph puts the four integers in the register, but the site a 5d implementer reads them from is Task 1's wire description, which carried an equivalent narrative and no label. The label now stands there, with "no round has re-run them" beside it. The class had exactly two members and both are closed; the sweep behind that count is in the audit report and re-ran clean here. **(4) SHOULD — AC-6.1's last dated control reading was attributed to the shipping revision and belongs to v1.46.** It is relabelled rather than replaced, and the illustration list is **frozen at four datings** rather than extended: the without-root-clause integer is unbounded by construction, so the live reading now sits at the control site (**2097** on v1.48's working tree, a sixth value in five days, which is the stated behaviour and not a defect) and the four datings stay illustration. **(5) SHOULD — Task 5 attributed a post-migration variable name to the pre-migration source and pinned it one line short.** Opened and corrected: `h-mad/tests/test_h_mad_collect_report_docs.py:270` is `blocks = re.findall(...)` and `:271` is `gating = [b for b in blocks if "h_mad_audit_gate.py" in b]`, so the comprehension binds `blocks`, one line later; `_bodies` is the name this document's own mutant payloads introduce and `grep -rn '_bodies' h-mad handoff` returns nothing. The substance — that the locator and the mutants share the `"h_mad_audit_gate.py" in b` predicate — is unchanged. **(6) NIT — "are only cited here" read two ways**, and the false reading is the one this document's own conventions would have a reader take. Restated as "only **cited**, never re-derived", with the second site named explicitly. **(7) NIT — the v1.44 `.py:`-pin measurement was written in the first person and disambiguated only at its end.** v1.44 is now named at the head of the pair, where a reader who stops early meets it. **Screens, controls and derivations re-run on the shipped body, every one after the last edit.** Marker screen: body **5**, whole file **5**, five per-marker lines each with count **1**. Restated-cardinal: body **0** lines / **0** occurrences, whole file **2** lines / **3** occurrences, all three inside the Version History. Self-reference screen: body **0**. The four `.py:` screens: **49 / 49 / 0 / 0** at **20** folded paragraphs, on base `700c599` and on the shipped tree alike, pin population byte-identical. Both `SKILL` screens: **0 / 0**. Six-token divergence sweep: **3**, the same three prose hits. Pre-dispatch sibling sweep: **25** body lines (6 exposure / 1 live use / 18 substring confound / 0 defects), `design.md:` 1 and `spec.md:` 1. The precheck flat/wrapped/unedited probe: **1 / 0 / 0**. Stamp closure: `git diff --name-only 74e126f 700c599 -- h-mad handoff` **empty**, `git diff --name-only 700c599 -- h-mad handoff` **empty**, the span holding **16** commits by `git log --format=%h 74e126f..700c599 | wc -l`. All **13** sibling locators against `git show 700c599:<sibling>`, each exactly one hit, **9** design / **2** plan / **2** spec, with the single caveat intact and still the only one. The 81-row derivation over `git show 700c599:<design>` against a design that moved **127 insertions / 25 deletions** since the previous stamp: **81 data rows, 81 distinct names, exactly 1 naming `SKILL.md` in its mechanism column, 0 of the 81 missing from this document**. AC-6.1's four sha-reproducible commands: **30 / 30 / 35 / 0**, symmetric difference empty, the five dropped paths exactly the five named, 27 `h-mad` + 3 `handoff` = 30. AC-6.4's eight falsification readings at `e8eaf6f`: **1450 / 2721 / 1455 / 2748 / 2731 / 2691 / 1474 / 2808**, with the `sort -u` whole-line collision at **2697**, none of them 2675. The `def test_` invariance triple: **1450 / 1450 / 1450**. `grep -c '2675'` over the three siblings at `700c599`: **0 / 0 / 0**. The collect-only pair, re-executed rather than transcribed: **2809** from the repository root and **2547** from `h-mad/`, divergence **262**. `grep -rn 'hmad:exec' h-mad/ handoff/`: **0**. **The stamp table on this revision's shipped body, 115 readings over 16 shas**: `700c599` 29 · `335f535` 19 · `35698f9` 12 · `4e4a00c` 9 · `b7d0d77` 9 · `74e126f` 6 · `1861157` 6 · `e8eaf6f` 5 · `68a70d6` 4 · `cf3a862` 4 · `6f0ee85` 4 · `7d8e797` 2 · `6b4df35` 2 · `1cbddb7` 2 · `8909ec4` 1 · `0aac0b7` 1. The 29 are this revision's re-runs; the `e8eaf6f` / `b7d0d77` / `1861157` readings remain **subject** stamps rather than run stamps, as v1.47's residual states, and a **new** residual is added at the screen: the pattern matches the literal ``at `sha` `` spelling only, so a stamp written "against", "measured on" or "as of" is invisible to it and silently shrinks the table. **New coverage relative to the auditor's declared read**, stated because absence of findings outside it was declared not to be evidence: the self-reference relabel and the exposure walk both reached spans the auditor did not sweep line by line — Task 1 outside `1088`–`1130`/`1349`–`1478` (the mutation-harness re-read), the AC checklist outside 6.1/6.4 (the six-token sweep in AC-1.5/1.7), and Task 5's prose (the extraction pin). Those are new coverage, not re-checks. **Owed to a sibling: nothing.** No claim about a sibling's present content is added, and the only sibling readings taken are the 13 locators and the `2675` census, both published as readings at `700c599` with their commands.
- v1.49: **DELTA SELF-REVIEW r14, not a gating round.** The subject was the *diff* `git show 8c6539a -- <this file>` (v1.47 → v1.48) on one surface: must 2 / should 2 / nit 3. `codex` is exhausted until 2026-09-07, so the reviewing surface again shares a model family with the authoring one. **This revision claims no gating pass, no two-surface clean and no exit gate.** **Both musts were introduced by v1.48's own fixes and both sit inside the paragraph v1.48's second must rewrote** — the dispatch records this as the third consecutive delta pass with that shape — which is why every figure below was re-run after this revision's last edit landed rather than before it (decision K). **The header's sibling pins are v1.48's derivation at `700c599` and are deliberately NOT re-stamped.** Measured rather than assumed: `git show 8c6539a:<doc> | grep -oE '^- v1\.[0-9]+' | tail -1` gives design **v1.104**, plan **v1.99**, spec **v1.60**, and `git diff --name-only 700c599 8c6539a --` over the three siblings names the plan and the design and does not name the spec — so the header is one behind on the design and the plan and correct on the spec. Re-stamping the header would advertise a coverage this revision does not have: the 81-row derivation, the 13 sibling locators and the `2675` census are readings over the sibling bytes **at `700c599`**, and re-deriving them against v1.104 / v1.99 while both sibling authors are mid-revision in this same batch would produce a reading stale before the batch lands. **Re-deriving all three against the commit this batch produces is owed to the r14 gating cycle, and is named here rather than left to be discovered.** **(1) MUST — the partition closing the exposure enumeration assigned a member to a bin its own disposition denies it, by carrying the previous revision's cardinal forward over a partition that had grown a new bin.** v1.47 wrote `Four of the six had the rule applied before it was named`; v1.48 grew the enumeration to ten and wrote `Five of the ten`, while adding **no** new rule-applied member. Worked backwards, the five could only be members (iii), (iv), (v), (vi) and (vii) — and (vii) is the member impl-plan audit v44 named, whose disposition four lines above says the opposite: its needles are literal, they are present in the scope it counts, and the exposure is tolerated only because it publishes no reading. The Version History carried the other half of the same error — v1.48's entry writes "The three the walk added: **(vii)** …" while its body says only **two** were found by the walk and by nothing else, one member attributed two ways in one commit. **Both halves are repaired from one derivation.** The partition is now written with every bin's members named, so the cardinals are checkable against the list above rather than recalled from the previous revision's sentence: **four** had the rule applied before they were named — members (iii), (iv), (v), (vi); **one** is the regex-class residual — member (ii); **one** is the instance that named the class — member (i); **one** was named by the audit rather than found by the walk — member (vii); **two** were found by the walk and by nothing else — members (viii) and (ix); **one** was written under the rule — member (x). Six disjoint bins, 4 + 1 + 1 + 1 + 2 + 1 = 10. [Bracketed correction, added at v1.50, impl-plan audit v45: the bin for member (vii) is **still wrong here**, and wrong in the same way this entry is about. `rather than found by the walk` contradicts this same revision's own `nine` — the walk's return — since nine requires (vii) to be among the walk's hits. Re-derived rather than argued: (vii)'s sweep line names *this document* as the scope it greps, with the path written out, which is the walk's **first** signature. `nine` stands; the bin now reads *found by the walk and independently named by impl-plan audit v44*. This entry repaired the cardinal and left the predicate, which is the half the rule it wrote was about.] **The class**: a count or a partition restated from a previous revision with only the cardinal updated — the class both of this round's musts belong to. **The rule**: a partition of an enumeration is a derived measurement under decision G exactly as a count is, and is derived from the enumerated members, never from the previous revision's sentence. **Residual, as a concrete category**: nothing mechanical checks a partition against its list — no screen here parses prose cardinals into bins — so this stays a reader's addition, which is why every cardinal now carries its members. Two nits from the same paragraph are closed with it: the walk's return is now stated as what it returned — **nine**, ten with the self-reference screen written after it ran, where v1.48 said ten and then, three sentences later, that the tenth did not exist when the walk was run; and the **three** is no longer attributed to the audit, which named **one** member and said in its own residual that completeness here is re-established by reading and not by a grep. **(2) MUST — residual category (a) of the walk stated a false mechanism and inferred a blindness that does not follow from it.** v1.48 wrote that the walk reaches the two `SKILL` screens "only because the fence binding the variable is the same fence". Measured on the shipped body: the fence that binds the variable opens and closes entirely above the fence that holds the two screens, so they are different fences and the screens' fence binds nothing; and both screen lines write the bound variable, which **is** the walk's second signature, so both are hit directly and would be from any paragraph. They were members of signature two, not a residual of it, and the category as written **understated** what the walk misses. [Bracketed correction, added at v1.50, impl-plan audit v45: the **signature label is wrong**. Signature two is the `awk` idiom and nothing else; the bound variable is one of the three spellings signature **one** accepts — *a body line naming this file as a scope*. The conclusion is unmoved and in fact strengthened: both screen lines write the bound variable **and** the `awk` idiom, so both signatures reach them. The body sentence is corrected; this one is annotated rather than rewritten, so the mislabel is not inherited from the entry.] Rewritten: (a) is an instrument that reaches this file through a **second variable name**, which neither signature knows, and it has **no live member** in this document. **The rule over the class**: state a residual category in terms of the signature that fails, never in terms of an example the signature in fact catches. **The residual after that, as a concrete category**: the second signature rests on a **naming convention** that nothing in this repository enforces — no test and no precheck reads the screens this document ships — so a reviser who binds a second name gets a screen no walk of this file finds. **The needle is deliberately not spelled out in that sentence and the reason is given at the site**: writing it there would put the walk's own needle into the scope the walk counts, which is the rule the enumeration exists to serve. Checked rather than asserted — every occurrence of that variable in this document is inside a fence, and both fences at issue are printed in full in the `SKILL.md`-pin bullet, so the fence claim is settled by reading and not by a grep that would have to write the needle. **(3) SHOULD — the sibling sweep's composition was published with no tree or sha, and it is exactly the kind of figure that moves**: **23** body hits at `700c599`, **25** on the tree v1.49 ships. Both readings and their relation now stand at the site. **This closes an inverted framing rather than repeating it**: impl-plan audit v44's **23** was **correct at the sha it read**; what v1.48 corrected was that audit's *classification* of the 23 — the exposure there is **6**, not the three an eyeball gave — and not its count. The two extra hits are v1.48's own edits and both are substring confounds, so the disjoint line split moves 2 / 5 / **16** at `700c599` to 2 / 5 / **18** on the shipped tree, with the standalone-`owed` bin unchanged at five. **(4) SHOULD — the standing control was cited by a node ID that does not resolve from the repository root; the prescription that came with it is refuted by the tree and is not applied.** "One path convention for test node paths, repo-relative" would break the harness contract 5d executes literally: `grep -ho '"test": *"[^"]*"' h-mad/tests/mutation-specs/*.json` shows the shipped specs spelling every key in the `h-mad/`-relative `tests/` form, and `h_mad_mutation_harness.py` runs each spec's `command` with `cwd=root`. What was genuinely wrong is narrower — four **prose citations** of the standing `SKILL.md`-pin control, met by a reader as a name rather than as a command. Those four now name the file repo-relative, as `h-mad/tests/test_h_mad_precheck_doc.py`, matching the form Conventions already uses for the test **file**, and the two-convention split is now **declared** in the Interpreter bullet instead of being inferable only from "every command runs from `h-mad/` unless stated". `python3.11 -m pytest h-mad/tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins -q` prints `1 passed` on the shipped body. **Residual, as a concrete category**: every remaining bare `tests/` node ID is a spec key, a spec `command` array or a RED-gate invocation, all of which run from `h-mad/` — and nothing mechanical distinguishes a citation from an invocation, so a future prose citation written in the harness form would read correctly to every screen here and wrongly to a reader at the root. **(5) NIT recorded and not fixed** — the header's design **v1.103** / plan **v1.98** pins being one behind at `8c6539a` is the drift the header itself declares; the measured values are above. **Screens, controls and derivations re-run on the shipped body, every one after this revision's last edit.** Marker screen: body **5**, whole file **5**, five per-marker lines each with count **1**. Restated-cardinal: body **0** lines / **0** occurrences, whole file **2** lines / **3** occurrences. Self-reference screen: body **0**. The four `.py:` screens: **49 / 49 / 0 / 0** at **20** folded paragraphs, on base `700c599` and on the shipped tree alike. Both `SKILL` screens: **0 / 0**. Six-token divergence sweep: **3**, the same three prose hits. Pre-dispatch sibling sweep: **25** body lines, `design.md:` 1 and `spec.md:` 1. The wrapped/flat precheck probe, re-run in full rather than transcribed: **flat 1 / wrapped 0 / unedited 0**. The standing control: `1 passed`. **The shared document precheck**, run over this body and over `git show 8c6539a:<this file>` alike: `PRECHECK: FAIL issues=8` both times, the **same eight** findings over **six** distinct forms — a `stream:` name line, an `os_error:` text line (three occurrences), an `overlap:` pair line, a `pgid:` line, and the two key/value spellings of the verdict grammar. **None is introduced here and all six are kept deliberately**: each is the *shape* of a line the 5d implementation must print with a runtime value in it, and filling one would specify a value where the design specifies a grammar. **The forms are deliberately described here rather than quoted**, because quoting them in this entry is itself a `PLACEHOLDER` finding — measured: an earlier draft of this entry quoted them and the precheck went to `issues=15`. **The stamp table on this revision's shipped body, 116 readings over 16 shas**: `700c599` 30 · `335f535` 19 · `35698f9` 12 · `b7d0d77` 9 · `4e4a00c` 9 · `74e126f` 6 · `1861157` 6 · `e8eaf6f` 5 · `cf3a862` 4 · `6f0ee85` 4 · `68a70d6` 4 · `7d8e797` 2 · `6b4df35` 2 · `1cbddb7` 2 · `8909ec4` 1 · `0aac0b7` 1 — one more than v1.48's **115**, and the one is the `700c599` stamp finding (3) added. **Not re-run, stated rather than implied**: AC-6.4's eight readings at `e8eaf6f`, the `2748` / `2486` pair at `b7d0d77`, the collect-only pair, AC-6.1's four commands, the 81-row derivation and the 13 sibling locators — none touched by this revision's edits, all stamped where they stand, and the last two owed a re-derivation at the commit this batch produces. **Owed to a sibling: nothing.** No claim about a sibling's present content is added or changed.
- v1.50: **Round-fourteen GATING audit (impl-plan audit v45), answered at the freeze sha `b3be433`** — teammate leg must 3 / should 4 / nit 3 over 26 files opened and 180 greps run. **This revision claims no gating pass, no two-surface clean and no exit gate.** `codex` is exhausted until 2026-09-07, so the reviewing surface again shares a model family with the authoring one; the agy leg returned `PASS must=0 should=0` while its gating teammate found the three musts below — the fourth consecutive round a clean agy leg sat beside real defects — and it is **not** cited as evidence about this document. **What is new about this round, and it is the reason every repair below is a sentence rather than an integer**: the auditor re-executed every screen, control, sweep, probe and derivation this document publishes — the marker screen, the restated-cardinal screen, all four `.py:` screens, both `SKILL` screens, the self-reference screen, the six-token sweep, the pre-dispatch sibling sweep and its classification, the sha-stamp table over sixteen shas, the three AST sweeps, the wrapped/flat probe, the shared precheck, the standing control, the thirteen sibling locators and the 81-row design-matrix derivation — **and every one reproduced its published reading byte-for-byte**. Not one published figure was wrong. All three musts are prose whose referent moved: a bin label, a placement claim, and a stale sibling location. **The header's sibling pins are v1.48's derivation at `700c599` and are deliberately NOT re-stamped, for the second revision running, and the drift is now TWO behind rather than one.** Measured rather than assumed: `git show b3be433:<doc> | grep -oE '^- v1\.[0-9]+' | tail -1` gives design **v1.105**, plan **v1.100**, spec **v1.60**, against the header's design v1.103 / plan v1.98 / spec v1.60 — two behind on the design, two behind on the plan, correct on the spec for the sixth consecutive revision. The reason is unchanged and is stated rather than implied: the **81-row design-matrix derivation** is still a reading over the design's bytes at `700c599`, and `git diff --name-only 700c599 b3be433 -- docs/02-design/features/doc-block-exec.design.md` is non-empty, so the design has moved under it; re-stamping the header while that reading sits at the older commit would advertise a coverage this revision does not have. **Re-deriving the 81 rows and the header pins together, at the commit this batch produces, is owed and is named here rather than left to be discovered.** **(1) MUST — the exposure enumeration's cardinal and its partition contradicted each other, and v1.49's repair fixed the cardinal and left the predicate.** The walk's return is published as **nine**, while the partition assigned member (vii) to a bin defined as *not found by the walk* — nine by the sentence, eight by the partition, and only one of the two could be true. **Which half is false was settled by re-running the walk's signatures against the member rather than by preferring the more recent sentence**: member (vii)'s sweep line names this document as the scope it greps, with the path written out, which is the walk's **first** signature, so the walk did reach it. Re-derived at both shas: the sweep line is present in the body at `700c599`, the base the walk was run against, and on the shipped tree, in the identical spelling. `nine` stands; the bin now reads *found by the walk and independently named by impl-plan audit v44*, the audit having named it in addition to the walk rather than instead of it. The six bins stay disjoint and still sum to ten: four, one, one, one, two, one. **The class**: a bin's defining predicate carried forward from the previous revision's sentence while the cardinal beside it is re-derived — v1.48 broke it on the cardinal, v1.49 broke it on the predicate, which is the same class twice. **The rule**: a bin's defining predicate is re-derived by running the walk's own signatures against each enumerated member, never against any previous sentence about that member. **Residual, as a concrete category**: nothing mechanical parses prose bins, so this remains a reader's derivation — which is why every bin names its members and why the walk's signatures are written out where the partition can be checked against them. The v1.49 Version History entry carried the same wording and is **bracket-corrected rather than rewritten**, so the mislabel is not inherited from the entry by the next revision. **(2) MUST — the INHERITED-UNVERIFIED register's own placement claim named a site that does not use the figures.** Task 1's wire description said the four heading-differential integers carry the label "here as well as at AC-6.4 and in the §Verification (Phase 5f) paragraph", and AC-6.4 uses none of the four: its own register sentence names `2748`, `2486` and `2675`, and neither differential appears anywhere in that bullet. Measured, not read: over the body outside the Version History the four integers occur only in the wire description and in the 5f note, and the 5f note names those same two sites. `at AC-6.4` is dropped and the two real sites are named. It mattered because the register's rule is that the label stands at every site that USES a member: a reader auditing that rule went to AC-6.4, found the figures absent, and could not tell whether the label had been dropped there or the site had never used them. **The class, and the rule that closes it**: a sentence of the form *this figure carries the label at X* is a PLACEMENT measurement under decision G exactly as a count is, and is derived by grepping X for the figure, never by recalling where the label was last added. **Residual, as a concrete category**: nothing mechanical pairs a register member with the sites that use it, so a site added later that uses one of these four and omits the label is caught by a reviser grepping the figure and by nothing else. **(3) MUST — a live sibling line pin survived in a spelling no instrument this document ships can see, and it was stale on the shipping tree.** Task 3's delta block carried a design location written as prose, attached to a present-tense claim that the line is the design's spelling verbatim. [Bracketed correction, added at v1.52, round-sixteen gating audit (impl-plan audit v46, second leg): **the task ordinal is wrong, and it was wrong when this entry was written rather than having drifted.** The block is the `h-mad/tests/docsections.py` delta, reached by `grep -Fn` on its own header comment at exactly one hit, and it has sat inside **Task 1** at every sha this document names — `1cbddb7`, `700c599`, `b3be433`, `00b961f`, `dfae038`, `3f70eb3`, `af19d53` — measured by comparing the block header's offset against the `## Task N` offsets in the same blob, seven for seven. The finding this entry records is unaffected; only its internal locator is. A task ordinal is a location and expires exactly as a source-line integer and a section name do, which is why the body's rule now covers internal references as well as sibling ones. This entry is annotated rather than rewritten, the treatment this feature has used since round six.] The content claim holds; the location did not — the design's line at that number holds a bare fence marker on the shipping tree and the content sits elsewhere. **The class is exactly this**: a sibling location written as prose rather than as filename-colon-number. It is invisible to the pre-dispatch sibling sweep, whose needles were three sibling-filename-plus-colon forms and one debt word; to the `.py:` shape screens, which key on `.py:`*N*; and to both `SKILL` screens, which key on `SKILL.md:`*N*. The pin is replaced by a **locator** — `grep -Fn` on the design's `sys.path.insert` line, returning exactly one hit in the design, re-run at `b3be433` — and the class is closed at both ends: the sweep gains a fifth needle for the prose form, written as a regex character class so the published sweep line cannot match itself, and deliberately singular so that participles ending in the plural form are not returned as confounds. **The widening's value is prospective and is stated as such**: with the live member repaired the fifth needle adds **0** hits, so it buys the next such pin being triaged rather than this one being found. **Residual, as a concrete category**: a sibling location in a further synonym — *at line N of*, *the Nth line* — matches neither the fifth needle nor any other instrument here, so the class is reduced and not closed. **Two consequences of that repair are recorded rather than absorbed.** First, the new locator is a locator like any other, so the sibling-locator population moves **13 → 14** and the preference split **7 + 6 → 8 + 6**; all fourteen were re-run at `b3be433` against all three siblings, all fourteen return exactly one hit in their stated target, and the split is **10 design / 2 plan / 2 spec = 14**. Second, the sweep now records **two** caveats where it recorded one: `git rev-parse --show-toplevel`, the spec locator, also returns one hit in the plan, and the new design locator also returns one hit in the plan, which names the same idiom in prose. Both hold only under their stated target file. **The new locator also carries a condition the other thirteen do not, and it is decision M in one line**: its needle contains a bracket, so as a BRE it is a character class and a plain `grep` returns **0** on text that is present — measured in both directions, `grep -Fc` gives design 1 / plan 1 / spec 0 and plain `grep -c` gives 0 / 0 / 0. It must be run with `-F`, and the site says so. **(4) SHOULD — the walk's second signature was mislabelled where residual category (a) is argued.** The bound variable is one of the three spellings signature **one** accepts — *a body line naming this file as a scope* — and signature two is the `awk` idiom and nothing else. The conclusion is unmoved and in fact stronger: both `SKILL` screen lines write the bound variable **and** the `awk` idiom, so both signatures reach them and neither is a residual of either. Corrected in the body and bracket-corrected in the v1.49 entry, together, so the next revision does not inherit the mislabel from the entry. **(5) SHOULD — three screens published their readings stamped to the tree v1.48 ships while v1.49 shipped further body edits, and a fourth had the same defect that the audit did not name.** The marker screen, the restated-cardinal pair and both `SKILL` screens were the three; **the self-reference screen is the fourth, found by sweeping the class rather than by taking the report's list**, and it is named here as new coverage. All four are re-stamped to the revision that ships them, all four re-run after this revision's last edit, and every reading is unmoved — which is what the re-run establishes rather than what it assumes. The restated-cardinal pair's base stamp moves with it, from `700c599` to `b3be433`. **(6) SHOULD — Task 4's `_SCANNED` membership claim was derived from a glob-fed list and read as a property of it.** Three of the eight sources are globs, so a later `references/*.md` or `scripts/*.py` file changes the membership with no instrument here noticing — the same shape AC-6.4's floor has. The bullet now says what the parametrised collection counts already say: membership is re-derived at 5d from the shipped sources, not read out of this document. The conclusion is unchanged and was re-checked at the source. [Bracketed correction, added at v1.51, delta self-review r15: **the cardinal is wrong, and it is wrong against the list printed one line above it in the body**. `sed -n '153,162p' h-mad/tests/test_h_mad_portable_timeout.py | grep -c '\.glob('` returns **4** at `dfae038` — `references/*.md`, `scripts/*.sh`, `scripts/*.py` and `hooks/*.sh` are all glob reads — and the body's own enumeration names those same four forms, so this entry and the body sentence it records both contradicted a list sitting beside them. The repair v1.51 makes is NOT the corrected integer: no cardinal of the glob sources is published anywhere now, because the next `.glob(` entry a reviser adds moves it again and nothing here detects that. This entry is annotated rather than rewritten so the count is not inherited from it.] **(7) SHOULD — the sibling sweep's needle set was widened in the same edit that repaired the stale pin**, so a reviser running the triage list next round does not read a clean list over a document that still carries one. Its composition is re-derived rather than carried: **26** body hits on the shipped tree against 25 on the tree v1.49 ships and 23 at `700c599`, classifying as **6** exposure, **1** live use, **19** substring confound and **0** defects. The one hit this revision adds is its own residual sentence, reaching the sweep through a participle ending in the debt word — which is why the sentence naming it describes that participle instead of writing it. **(8) NIT — the header's "one place a sibling version number may appear" read as forbidding the bare provenance citations the Conventions bullet blesses.** Narrowed to a sibling's *current* version number, with the provenance form named at the header so the two rules are met together. **(9) NIT — a bare `:412` read as a claim about this document's line 412**, which is inside Task 1's AC checklist. Spelled as pinning that same line in that same file and never a line of this document. **(10) NIT — the fence-opener scan's true negative packed the control, the decline count and the file count into one clause**, ahead of the per-disjunct split that is the reading that matters. Split into its own sentences, with the composite marked as not the control's usable reading at the point a reader meets it. **Screens, controls and derivations re-run on the shipped body, every one after this revision's last edit** (decision K). Marker screen: body **5**, whole file **5**, five per-marker lines each with count **1**. Restated-cardinal: body **0** lines / **0** occurrences, whole file **2** lines / **3** occurrences. Self-reference screen: body **0**. The four `.py:` screens, in the fixed order the Conventions bullet names: **49 / 49 / 0 / 0** at **20** folded paragraphs, on base `b3be433` and on the shipped tree alike, with the pin population sorted and diffed between the two and the diff **empty**. Both `SKILL` screens: **0 / 0**. Six-token divergence sweep: **3**, the same three prose hits. Pre-dispatch sibling sweep: **26** body lines under the four-needle form and **26** under the five-needle form — the fifth needle adds none — `design.md:` 1 and `spec.md:` 1. The prose-line-pin sweep the fifth needle formalises: **1** hit on the shipped body, and it is a substring confound sitting inside a longer word rather than a pin, so the class has **0** live members. The wrapped/flat precheck probe, re-run in full rather than transcribed: **flat 1 / wrapped 0 / unedited 0**. The standing control: `1 passed`. **The shared document precheck**: `PRECHECK: FAIL issues=8` on this body and the **same eight** findings over the **same six** distinct forms as at `b3be433` — a stream-name line, an OS-error text line (three occurrences), an overlap-pair line, a process-group line, and the two key/value spellings of the verdict grammar. **None is introduced here and all six are kept deliberately**: each is the *shape* of a line the 5d implementation must print with a runtime value in it, and filling one would specify a value where the design specifies a grammar. **The forms are described rather than quoted**, because quoting them in this entry is itself a `PLACEHOLDER` finding — measured at v1.49, where an earlier draft that quoted them took the precheck to `issues=15`. All **14** sibling locators re-run against `git show b3be433:<sibling>`, each exactly one hit in its stated target, **10** design / **2** plan / **2** spec, with **two** caveats now rather than one, both named at the site. **The stamp table on this revision's shipped body, 118 readings over 17 shas**: `700c599` 29 · `335f535` 19 · `35698f9` 12 · `b7d0d77` 9 · `4e4a00c` 9 · `74e126f` 6 · `1861157` 6 · `e8eaf6f` 5 · `cf3a862` 4 · `6f0ee85` 4 · `68a70d6` 4 · `b3be433` 3 · `7d8e797` 2 · `6b4df35` 2 · `1cbddb7` 2 · `8909ec4` 1 · `0aac0b7` 1 — two more readings and one more sha than v1.49's 116 over 16, the new sha being this revision's own base, and one `700c599` reading having moved to it with the restated-cardinal pair's base stamp. **A stamp this screen cannot see was found while writing the table and is recorded**: the screen is line-scoped, so a stamp that falls across this document's fold is invisible to it — two of this revision's own stamps were, until the sentences were rewrapped. That is a second residual on the screen beside the spelling one v1.48 stated. **Not re-run, stated rather than implied**: AC-6.4's eight readings at `e8eaf6f`, the `2748` / `2486` pair at `b7d0d77`, the collect-only pair, AC-6.1's four commands, the three AST sweeps, and the 81-row design-matrix derivation — none touched by this revision's edits, all stamped where they stand, and the 81-row derivation owed a re-run at the commit this batch produces, over a design that has moved since the commit it was taken at. **Coverage limit carried forward rather than closed**: impl-plan audit v45 read Version History entries v1.1–v1.48 only by their opening characters plus targeted greps, and this revision did not sweep them either — the two bracketed corrections it adds are both inside the v1.49 entry, which the auditor did read in full. Absence of findings in v1.1–v1.48 remains unmeasured. **Owed to a sibling: nothing.** No claim about a sibling's present content is added; the only sibling readings taken are the 14 locators, published as readings at `b3be433` with their commands, and the version-number derivation in the header paragraph above.
- v1.51: **DELTA SELF-REVIEW r15, not a gating round.** The subject was the *diff* `git show 00b961f -- <this file>` (v1.49 → v1.50) on one surface: must 3 / should 2 / nit 2 over 9 files opened and 68 greps run. **No gating pass, no two-surface clean and no exit gate is claimed.** `codex` is exhausted until 2026-09-07 11:28, so the reviewing surface again shares a model family with the authoring one. **Answered at the freeze sha `dfae038`, and that is settled rather than assumed**: it is HEAD, it is the sha this revision is authored against, and it is the parent the batch will land on. The field is written in the same grammar the three siblings use — the sha adjacent to the words — because a cross-document consistency grep that silently misses one document is a false negative, and this entry's first draft spelled the field so that it did. `git diff 00b961f..dfae038` over the four feature documents is empty, run with the four explicit document paths rather than a wildcard, so `00b961f` is the diff's SUBJECT and `dfae038` is the tree, and every reading below is taken at `dfae038` in its own shell invocation. [Bracketed correction, added at v1.52, round-sixteen gating audit (impl-plan audit v46, second leg, must 1): **the clause that stood between the two halves of that sentence asserted a scope for the two intervening commits — that neither touched anything outside `docs/handoffs/` — and that assertion is FALSE.** It is DESCRIBED here and not quoted, the same device the v1.50 entry's bracket uses, so the false claim is not re-planted in a body that a later reviser greps. `git show --name-only --format='' dfae038` names **three** files: the handoff document, `docs/learnings.md` and `docs/skill-candidates.md`. Only `df04e8e` is confined to `docs/handoffs/`. The conclusion the sentence draws — the four feature documents are byte-identical across that interval — is independently true and is what now stands, because it is the measurement that was actually run. **The false clause was not this document's own reading and the attribution is recorded so the correction is traceable**: it originated in the orchestrator's round-fifteen decision sheet, `docs/03-analysis/doc-block-exec.delta-decision-sheet.r15.md`, where it sits unmeasured beside the same true conclusion, and it reached this entry from there. An unmeasured scope claim standing in for a measured diff is the species this document's Conventions forbid, which is why the repair is to publish the diff and not to repair the word.] **The r15 decision sheet's header said `Freeze: 00b961f`, which is correct for the delta's subject and wrong as a value to stamp**; the spec leg raised it, the orchestrator verified and broadcast it, and it is recorded here rather than silently absorbed, because a sha named in one role and read in another is the species three of this arc's verification errors already belong to. **A reading already stamped at a blob does NOT move with the freeze sha**: the fourteen sibling locators run against the three siblings at `b3be433`, and the per-sha presence readings in item (3), keep the shas they were taken at, because a blob reading is evidence about that blob and about nothing else. All three musts are prose whose referent is wrong rather than an integer, and all three sit inside a paragraph that a previous round's repair rewrote — the fourth consecutive delta pass with that property. **(1) MUST — v1.50's own new `_SCANNED` sentence published a wrong cardinal, and the class is closed by DELETING the cardinal rather than by correcting it.** The sentence said *three of the eight sources are globs*; `sed -n '153,162p' h-mad/tests/test_h_mad_portable_timeout.py | grep -c '\.glob('` returns **4** at `dfae038` — `references/*.md`, `scripts/*.sh`, `scripts/*.py`, `hooks/*.sh` — and Task 4's own enumeration one line above names those same four forms, so the sentence contradicted the list it sat beside. **The repair is not `three`→`four`**: no cardinal of the glob sources is published in the body any more, because the next `.glob(` entry a reviser adds moves the figure again and no instrument here would see that. What stands in its place is a rule over the set — *every `_SCANNED` source spelled with `.glob(` is a tree read*, so the sources partition by their own spelling and membership is settled by running them, which is what the bullet already said about 5d. The v1.50 entry below carries the same wrong figure and takes a **bracketed appended correction** rather than a rewrite, the treatment this feature has used since round six, so the count is not inherited from the entry. **The same edit pays the two glob-adjacent should/nit items**: the residual said `h-mad/SKILL.md` is the only member *this feature edits*, which is true and misleading — `h-mad/scripts/h_mad_doc_block_exec.py` is a `scripts/*.py` member the moment Task 1 **creates** it, so the sentence dodged a live member on a verb. Both members are now named with their route, and the created member points at Task 5's bullet **Why the two portable-timeout nodes are members at all**, where its two inherited guards and their node IDs already stand, instead of duplicating them. The three exclusions are spelled uniformly as globs (`references/*.md`, `hooks/*.sh`, `scripts/*.sh`) beside the one inclusion, so the list cannot be read as exhaustive of the glob sources. **(2) MUST — the sibling-location class v1.50 claimed to close survived inside the sentence that closed it, in a spelling five needles cannot see.** Task 3's delta block carried `design v1.79 §Scanning`. v1.50 removed the line number and kept the section name, then declared the location "written as a LOCATOR and never as a number" — but **a section name IS a location**, and this one was **false at both ends**. Re-derived at `dfae038` and at the revision it cited: at each of them the `grep -Fn` needle's single hit sits inside the design's `## Overview`, above the `### Scanning` heading rather than within it — taken by comparing the hit's offset against that same revision's heading offsets — and at the cited revision the whole span of `### Scanning` holds **0** occurrences of the needle. So it was wrong when it was written, not drift, and it was invisible to the fifth needle the same repair added (`grep -cE 'line [0-9]'` over the body is **0**, and a `§`-reference matches nothing in that needle set). `§Scanning` is **removed** rather than corrected to the right section name, because the needle is the whole of the route. **The class and the rule over it**: a sibling location written as a SECTION REFERENCE is the same defect as one written as a line number and expires the same way; a sibling `§`-reference is admissible only where the content it cites is re-derived inside that section at a stated commit, or where it is demoted to the bare version-pinned provenance form the Conventions bullet blesses — and it is never this document's route to a sibling's content, because the route is always a needle. The sweep's residual, which had named only *at line N of* and *the Nth line*, now names this form as the member of the category that was alive. **Applied over the population and not at the instance**: every other sibling `§`-reference in the body was re-derived at `dfae038` by locating the content it cites inside the named section's line span in the shipping sibling; the one Task 3 carried is the only one that failed and the rest hold — design `§Test Strategy` ×2, `§Test Plan` ×2, `§Scanning` ×5, `§Execution` ×2, `§API`, `§Implementation Order`, and plan `§Measurements` ×2, each located by a needle from its own sentence and checked against that section's line span. **Two of the members were found only after reading past a truncated grep**, and that is recorded rather than smoothed: the first pass at this census enumerated the population from output cut at 200 characters and would have published a universal over a set it had not finished enumerating — the same species as must (3), one level up, caught before it shipped. The CommonMark `§4.2` citations and this document's own `§Verification` are not members. **The population is deliberately NOT published as a count and the derivation is deliberately NOT built as a screen** — a grep for `§` naming this document as its scope would be an eleventh instrument in the exposure enumeration, whose cardinal and six-bin partition are figures this document has already broken twice, and the class is a prose class with no detector anywhere in this repository, prevented by the sentence not being written exactly as the sibling-agreement class beside it is. **(3) MUST — the pre-dispatch sweep published a false universal about its own needles, and v1.50 rewrote that exact clause to widen it without re-deriving it.** Both sites said the literal needles were *every one of them present in the body it counts*. Measured per needle at `dfae038` over the body outside the Version History: the debt word **23**, `spec\.md:` **1**, `design\.md:` **1**, `plan\.md:` **0** — and 23 + 1 + 1 + 0 is the **25** the whole sweep returns, so no line is reached by two needles. **The universal that replaces it is itself measured over its whole population and not over a sample**: `git show <sha>:<this file> | awk '/^## Version History/{exit}{print}' | grep -c 'plan\.md:'` was run over every sha the stamp table names and every further sha the Version History names, and **every one reads 0**; `6b4df35` alone admits no reading, because this document does not exist in that commit, and it is named rather than scored as a zero. The first draft of this repair said *at any sha this document names* while having measured four of them — the same species as the must it was repairing, caught before it shipped. Its one whole-file hit sits inside the Version History, which this sweep is read outside of, so it is absent under either reading. The document already contradicted itself two paragraphs on, where the classification allots exactly **2** hits to the sibling-filename-plus-colon shape and three distinct forms cannot all be present behind two hits. Both sites now state the reading **per needle** instead of asserting a universal, and the three spellings written into that sentence are escaped (`\.`), which the needle does not match — the same publication device the fifth needle uses one level down, applied so a per-needle reading can be published without moving itself. **(4) SHOULD — the plan clause in Task 3's delta block was an unstamped present-tense claim about a sibling's content.** The reading is right and only the stamp was missing: `grep -Fc` on the insert needle returns **1** against the plan at `b3be433` and **1** at `dfae038`, and both stamps are now written at the site, beside the design locator's. **(5) NIT — the register's placement sentence read as three sites where it names two.** "at both of the sites that USE them — here, in Task 1's wire description, and in the §Verification (Phase 5f) paragraph" loses the comma after *here*, so the pair reads as a pair. **Screens, controls and derivations re-run on the shipped body, every one after this revision's last edit and each in its own shell invocation** (decision K). Marker screen: body **5**, whole file **5**, five per-marker lines each with count **1** — unmoved. Restated-cardinal: body **0** lines / **0** occurrences, whole file **2** lines / **3** occurrences — unmoved, at `dfae038` and on the shipped body alike. Self-reference screen: body **0** — unmoved, and this entry's own relative phrasing is inside the Version History, which that screen deliberately excludes. The four `.py:` screens in the fixed order the Conventions bullet names: **49 / 49 / 0 / 0** at **20** folded paragraphs — unmoved. Both `SKILL` screens: **0 / 0**. **The pre-dispatch sibling sweep MOVED and the movement is derived rather than absorbed**: **26** body lines on the tree v1.50 ships against **25** on the tree v1.51 ships, four-needle and five-needle forms agreeing at both. Exactly one bin moved and it moved DOWN: v1.50's residual sentence ended on a participle carrying the debt word, and this revision's widening of that same residual rewrote the sentence without it, so the confound bin gave back the hit v1.50's own residual had added — the same hit, in the same sentence, entering at one revision and leaving at the next. The split is now **6** exposure, **1** live use, **18** substring confound, **0** defects, re-derived by classifying all 25 rather than by subtracting one from the previous split; the exposure and filename bins are unmoved. That a bin moves on an edit made for an unrelated reason is the argument for re-deriving the classification every revision, and it is now stated at the site. **The shared document precheck**: `PRECHECK: FAIL issues=8` on this body — the **same eight** findings over the **same six** distinct forms as at v1.50, none introduced here, and `PRECHECK: PASS issues=0` when the six are passed on `--allow`. Each is the *shape* of a line the 5d implementation must print with a runtime value in it, and filling one would specify a value where the design specifies a grammar. **The forms are described rather than quoted**, because quoting them in this entry is itself a `PLACEHOLDER` finding — measured at v1.49, where a draft that quoted them took the precheck to `issues=15`. **The stamp table on this revision's shipped body, 123 readings over 18 shas**: `700c599` 29 · `335f535` 19 · `35698f9` 12 · `b7d0d77` 9 · `4e4a00c` 9 · `74e126f` 6 · `1861157` 6 · `e8eaf6f` 5 · `dfae038` 4 · `cf3a862` 4 · `b3be433` 4 · `6f0ee85` 4 · `68a70d6` 4 · `7d8e797` 2 · `6b4df35` 2 · `1cbddb7` 2 · `8909ec4` 1 · `0aac0b7` 1 — five more readings and one more sha than v1.50's 118 over 17, the new sha being this revision's own base and all five additions being the re-derivations items (2) and (4) required. **Not re-run, stated rather than implied**: the wrapped/flat precheck probe, the standing control, the six-token divergence sweep, the prose-line-pin plural sweep, AC-6.4's eight readings at `e8eaf6f`, the `2748`/`2486` pair at `b7d0d77`, the collect-only pair, AC-6.1's four commands, the three AST sweeps, and thirteen of the fourteen sibling locators — the fourteenth, the design `sys.path.insert` locator, is re-run at `dfae038` in both its `-F` and plain forms because item (2) turns on it. **The header's sibling pins are still v1.48's derivation at `700c599`, deliberately NOT re-stamped for the third revision running**, for the reason v1.50 gives unchanged: the 81-row design-matrix derivation still sits at `700c599` while the design has moved under it, and three sibling authors are revising concurrently as this is written, so any version number read now would be stale before the batch commits. **Owed to a sibling: nothing new.** No present-tense claim about a sibling's content is added; the only sibling readings taken here are the design and plan hit counts for the one locator, both published with their command and their sha. [Bracketed correction, added at v1.52, round-sixteen gating audit (impl-plan audit v46, both legs): **three further errors in this entry, every one of them a location or a stamp rather than a count.** (a) Item (3)'s per-needle reading — the debt word **23**, the two sibling-filename needles **1** and **1**, the plan-filename needle **0**, summing to **25** — is stamped `dfae038`, and it was taken over v1.51's own post-edit body. At `dfae038` those same four needles read **24** / **1** / **1** / **0** = **26**, which is what this entry itself publishes a few sentences later as the reading on the tree v1.50 ships, so the entry gives 25 and 26 for one blob. Nothing was miscounted: a correct reading carried a sha it was not taken at, because the round-fifteen broadcast said the batch stamps `dfae038` and that instruction was applied to a reading over new bytes the sha does not contain. The three-clause rule that closes the class is written at the body site, not here. (b) Items (2) and (4), and the sibling-`§` census inside item (2), all route the reader to *Task 3's delta block*; the block is `h-mad/tests/docsections.py`'s and it sits inside **Task 1** at `1cbddb7`, `700c599`, `b3be433`, `00b961f`, `dfae038`, `3f70eb3` and `af19d53` alike, measured by comparing the block header's offset against the `## Task N` offsets in each blob. The ordinal was wrong when this entry was written and at v1.50 before it, so it is not drift. (c) The v1.50 entry is named as sitting *below* this one. The Version History ascends, so it is the entry immediately **above**. A direction word is a location and expires exactly as a section name does — the rule this same entry added one item earlier.]
- v1.52: **Round-sixteen GATING audit (impl-plan audit v46), answered at the freeze sha `af19d53`** — two legs, one model family: the first returned must 1 / should 2 / nit 2 over 27 files opened and 152 greps, the second must 3 / should 2 / nit 1 over 11 files and 48 commands, Four musts were filed across the two and exactly one is common, so the union is three distinct musts. **This revision claims no gating pass, no two-surface clean and no exit gate.** Codex returned no verdict at c46: the assembled prompt exceeded the input ceiling and was refused, which the assembler's `--vh-tail` closes as of this revision's own freeze sha, so a real codex leg is owed on this tree and the reviewing surfaces here again share a model family with the authoring one. **The freeze-sha field names `af19d53`, the parent the batch lands on**, and the four feature documents are byte-identical across `3f70eb3..af19d53` — `git diff --name-only` over the four explicit document paths is empty, run with the paths spelled out because a wildcard over `doc-block-exec.*.md` also matches this feature's audit reports and reports hundreds of lines that are not the documents. **(1) MUST — the per-needle sweep reading was published under a sha it was not taken at, and BOTH legs found it independently.** Nothing was miscounted. The four integers — the debt word **23**, the two sibling-filename needles **1** and **1**, the plan-filename needle **0**, summing to **25** — were taken over v1.51's own post-edit body and stamped `dfae038`, where the same needles read **24** / **1** / **1** / **0** = **26**; the same paragraph correctly published 26 as the reading on the tree v1.50 ships, and `dfae038` **is** that tree, so one paragraph gave two totals for one blob. Re-measured here one blob at a time, each in its own shell invocation, same corpus and same grammar with only the sha varying: `dfae038` 24 / 26, `3f70eb3` 23 / 25, `af19d53` 23 / 25. **The repair is a rule and not a sha swap.** The round-fifteen broadcast stated two clauses — an entry's freeze-sha field takes the batch sha, and a reading of a committed blob keeps the sha it was taken at — and the third was missing: **a reading taken over this revision's own post-edit body is stamped to the tree this revision ships and never to the freeze**, because the freeze does not contain the edits the reading counts. All three clauses are now written at the sweep's own site. **(2) MUST as the class-closure half of (1), and filed by the first leg as a should-fix rather than a must — the severity is stated as the report set it and the treatment is the class closure the round directed: four screen sites re-ran their readings and did not re-stamp them, so the sites and the Version History disagreed about which tree the integers belonged to.** The marker screen, the restated-cardinal screen, both `SKILL` screens and the `.py:` series all read `the tree v1.50 ships` while v1.51 shipped further body edits — the shape impl-plan audit v45 filed against v1.49, recurring at the next revision because the rule had no enforcement condition. It gains one: **a screen site's stamp is rewritten in the SAME edit that re-runs it**, so re-running and re-stamping cannot come apart. All four are re-run after this revision's last edit and re-stamped to v1.52; the `.py:` series gains an explicit member rather than leaving v1.48's as the last one, and that member states plainly that v1.49–v1.51 are not claimed. The locator census's `the tree v1.50 ships` is deliberately **not** moved: it labels its two lists as v1.50's and is a dated reading, not a re-run screen. **(3) MUST — the freeze field's justification asserted a scope for two commits that was never measured, and it is FALSE.** `git show --name-only --format='' dfae038` names three files: the handoff document, `docs/learnings.md` and `docs/skill-candidates.md`; only `df04e8e` is confined to `docs/handoffs/`. The conclusion the sentence drew — byte-identity of the four feature documents across the interval — is independently true and is what now stands, published as the diff that was actually run. **The false clause was not this document's reading and the attribution is written into the correction**: it came from the orchestrator's round-fifteen decision sheet, `docs/03-analysis/doc-block-exec.delta-decision-sheet.r15.md`, where it sits unmeasured beside the same true conclusion. An unmeasured scope claim standing in for a measured diff is the species this document's Conventions forbid. **(4) MUST — the sentence stating the new `§`-reference rule routed the reader to the wrong task for the one member the rule was written from**, which is that rule's own class committed inside the rule. The site is the `h-mad/tests/docsections.py` delta block, and that block has sat inside **Task 1** at `1cbddb7`, `700c599`, `b3be433`, `00b961f`, `dfae038`, `3f70eb3` and `af19d53` alike — measured by comparing the block header's offset against the `## Task N` offsets in each blob, seven for seven — so *Task 3* was wrong when v1.50 wrote it and wrong again when v1.51 repeated it. Three body sites are repaired — two naming the block by its own header comment, which `grep -Fn` reaches at exactly one hit, and the third by back-reference to it — and the v1.50 and v1.51 entries take bracketed corrections. **A task ordinal is a location and expires exactly as a source-line integer and a section name do**, so the rule now covers internal references as well as sibling ones. **The ground that finding was filed on does NOT reproduce, and it is recorded rather than smoothed**: the report states that Task 3's span holds no `§` character at all, and it holds three — two `§Execution` provenance citations and one `§Implementation Order`. The conclusion was re-derived here from the offsets rather than taken from the report. **(5) SHOULD — the body sent a reader to the v1.50 entry's bracketed correction for a value the bracket does not carry.** Diffing that entry between `dfae038` and `af19d53` shows the bracket was appended at v1.51 carrying the reading and the four glob forms; the retired value sits in the entry's original prose, outside it. The sentence now names both places. **(6) SHOULD — the v1.51 entry called the v1.50 entry the one *below* it.** The Version History ascends, so it is the entry immediately above; corrected in that entry's bracket, because a direction word is a location and expires like the rest. **A GRAMMAR caution, filed by the first leg about a count handed to it and re-derived here, because it will mis-calibrate the next sweep**: the loose phrase for the retired glob cardinal matches **four** Version History lines whole-file case-insensitively (v1.37, v1.45, v1.50, v1.51) and only **two** of those are that cardinal — v1.37 counts killers in `docsections.json` and v1.45 counts precheck spans for one specimen. The case-sensitive form matches only **three** of the four, because v1.50's is sentence-initial and capitalised. Nothing in the document is wrong; a sweep calibrated on any one of 2, 3 or 4 without naming its grammar reads a correct document as drifted. **Screens, controls and derivations re-run on the shipped body, every one after this revision's last edit and each in its own shell invocation** (decision K). Marker screen: body **5**, whole file **5**, five per-marker lines each with count **1** — unmoved. Restated-cardinal: at `af19d53` body **0** / **0** and whole file **2** lines / **3** occurrences, and the same four integers on the tree this revision ships — unmoved. The four `.py:` screens in the fixed order the Conventions bullet names: **49 / 49 / 0 / 0** at **20** folded paragraphs, on the base and on the shipped tree alike, pin populations sorted and diffed empty. Both `SKILL` screens: **0** / **0**. The six-token GNU-divergence sweep: **3** lines, all three prose about the class, unmoved. The pre-dispatch sibling sweep: **25** body hits on the tree v1.52 ships against 25 at `af19d53`, four-needle and five-needle forms agreeing at both, and the split re-derived by classifying all 25 rather than carried — **18** substring confound, **5** standalone of which **4** are this rule's own text, **2** sibling-filename, so **6** exposure, **1** live use, **0** defects, every bin unmoved. This revision writes new sentences into both the Conventions residual and the sweep bullet, so the total and the split are figures its own edits could have moved; that they did not is a reading, not an assumption. **Not re-run, named so the silence does not read as clearance**: the repository test suite, which this loop still never runs; the Version History's stamp table and its per-sha reading census, which both legs also named unchecked and which is deliberately **not** republished here rather than copied forward stale; the wrapped/flat precheck probe; the standing control; the fourteen sibling locators; the three AST sweeps; AC-6.1's four commands; the 2748 / 2486 suite floors and the plan's heading differentials, still inherited-unverified; and the sibling `§`-population census, whose `dfae038` stamp is a committed-blob reading and stays at its blob — **the census's exclusion list does gain a member here and that is a definition change, not a re-derivation**: item (4)'s correction reports what a task span holds and so writes two section names into the body, which are a census description and not a route to a sibling's content, and they are excluded by name so the next reviser triages them instead of re-deriving them against a sibling section. The first leg re-derived six of the roughly fifteen sibling references at both `dfae038` and the shipping tree and took the rest on the document's own reading; the second re-derived nine at `3f70eb3` with fence-aware heading spans and all nine held. Neither leg's coverage is claimed as complete here and this revision did not extend it. **The freeze moved `h-mad/`, so the tree-scoped readings were re-checked rather than assumed unmoved.** `git diff --name-only 3f70eb3..af19d53` names four files outside this feature's audit reports: two design audit reports, `h-mad/scripts/h_mad_assemble_audit.py` and its test. [v1.53 correction, impl-plan audit v47 should 2: the CATEGORY LABEL is wrong and the four files are right. That command names **8** files, of which four are this feature's impl-plan and plan audit reports and four are the ones listed — but two of those four are this feature's DESIGN audit reports, so "outside this feature's audit reports" is false of half of them. The label should read *outside the audit reports this revision answers*. The conclusion the sentence draws, byte-identity of the four documents across the span, is unaffected and reproduces.] This document pins that script once, at `_braces_outside_fences`, and the definition sits at the same line at `dfae038`, `3f70eb3` and `af19d53` alike — the assembler's changes land below it — as does the `handoff/` scanner pinned beside it. The two tracked corpora this document defines are unmoved across the interval: **30** `.md` files under `h-mad` and `handoff` with `archive/` excluded, and **127** `.py` files under `h-mad`, at both shas, because the modified test file already existed and nothing was added. The AST censuses and the corpus figures are stamped at `335f535`, `74e126f` and `1861157` and are blob readings that do not move with the freeze in any case. [v1.53 correction, impl-plan audit v47 must 4: that clearance is FALSE of one of the censuses. Residual (a)'s `## `-slicer over-count sweep moved **22 → 23** across this very freeze, the new member being the function `af19d53` itself added to `h-mad/scripts/h_mad_assemble_audit.py`. A blob reading does not move, but a sweep re-run on the shipping tree is not a blob reading, and this entry cleared a set by assertion rather than per instrument. The per-instrument readings are published at residual (a) in the body as of v1.53.] **The check FOUND one, and it is repaired rather than noted**: the body's one-sided interval closure `git diff --name-only 700c599 -- h-mad handoff` compares a sha against the working tree, printed **0** at `3f70eb3` and prints **2** at `af19d53`, so the sentence concluding that a 5d implementer reads the `700c599` tree was true when it was last audited and is false at this freeze. The reading and its conclusion are withdrawn at the site, the narrower claim that survives is stated there — the one pinned symbol in the one pinned file of the two is unmoved, so no `path:line` here is stale — and the class is given its rule: a two-sha closure is dated and stays, a sha-to-working-tree closure expires on the next commit under its roots and is re-run every revision or not published. Three sibling absence claims over the same roots were re-run and all three hold at **0** at both shas. **A freeze that touches no document is not a freeze that touches no measurement** — this one left all four feature documents byte-identical and falsified a body sentence anyway, which is why the check is published rather than skipped. **Neither leg on this document found it**; it came from the plan's author measuring the same class in a sibling, and that provenance is recorded because it is the round's one cross-document catch. **Owed to a sibling: nothing new.** No present-tense claim about a sibling's content is added. **Unchanged and re-checked rather than assumed**: five tasks, two `wiring` (Tasks 1 and 5), one shape each; 25 + 5 + 24 + 27 = **81** mutation rows, the wire spec **8**, `docsections.json` **8**. **The shared document precheck**: the same eight findings over the same six distinct forms as at v1.51, none introduced here, and `PRECHECK: PASS issues=0` when the six are passed on `--allow`. The forms are described rather than quoted, because quoting them in this entry is itself a finding.
- v1.53: **Round-seventeen GATING audit, answered at the freeze sha `fbc2ea0`** — a codex leg and a teammate leg together for the first time on this document (earlier rounds paired codex with agy, so this is a new PAIRING and not the first second family): the teammate leg (impl-plan audit v47) returned must 4 / should 4 / nit 2 over 24 files opened and 95 greps run, and the codex leg returned must 6 / should 2 / nit 0 over 13 files and 3 greps. No item is a must on both legs — the one item both raised, the self-reference screen, is the teammate's must 1 and a codex should — so the impl-plan union is **10** distinct musts. **The twelve numbered items below are those 10 plus two DESIGN musts that land here under FACT 8**, items (2) and (3), which is why their citations name a design must rather than an impl-plan one; codex's own impl-plan musts 2 and 3 are items (4) and (5). **This revision claims no gating pass, no two-surface clean and no exit gate**; the gate is c48. **REOPENED ONCE AFTER DONE, announced before the first edit, and every screen re-run before the second DONE** (the reopen rule, which this document's own round-sixteen musts produced). Six corrections arrived from the round after the first DONE. Four were already shipped and needed nothing: the three-quoted `intersect:` spelling with no connective, `DETAIL_KEYS` at twelve across all three of its sites, the 27 / 20 / 7 slot arithmetic, and `spawn` as an existing rather than a new stage label. Five were genuinely owed and are applied: **(a)** the two determinism rules for `intersect:` were NEW, and one of this document's own sentences was WRONG against them — it defined the offset as the index of the first intersecting occurrence, which on the canonical fixture reads 0, where the rule is the smallest index the two spans SHARE, which is 1; the fixture now asserts the emitted line verbatim, so the assertion discriminates the two readings instead of accepting either. **(b)** the `new_only` history, re-derived here at seven shas rather than taken from the correction. **(c)** which probe prints the `NEW-ONLY` line, verified by running both. **(d)** the probe-naming debt at two sites, one of which was a false positive of the correction's own grep — a virtualenv, not a script — and is repaired by naming the committed path rather than by deleting a word. **(e)** the three repo-wide `*.py` censuses, measured at both shas. The reopen's own new prose then broke the self-reference screen a THIRD time in one revision — the slot-arithmetic sentence it added said *this revision* of the tuple — caught by re-running rather than by assuming, and repaired before the second DONE. **Three self-breaks in one revision, all of the same needle, all caught only by the re-run, is the measurement that argues the screen's target should stay a hard 0**: a screen a reviser is tempted to trust is a screen that reads 0 right up to the sentence that breaks it. Every figure below is the post-reopen reading; the per-needle sweep and the `.py` series were re-run after the last edit and are unmoved from their pre-reopen values. **REOPENED A SECOND TIME, announced first, for one change**: the round accepted this entry's own report that the 3g selection had two named pins and no mutation row, and gave it one. `cleanup-chain-selection-flipped` lands in **Task 3**, where the selection lives, taking that task 25 to 26 and the matrix **84 to 85** — 25 + 6 + 26 + 28, split 84 helper-source and the same 1 of `h-mad/SKILL.md`, so the one-SKILL.md derivation is untouched. **The row is isolated and that is derived rather than asserted**: the mutant collapses the selection to an unconditional `from pending`, which still yields the `__cause__` that `test_cleanup_failure_outranks_timeout_injected` asserts, and `test_cleanup_failure_carries_the_os_error` reads the `cleanup_error` field rather than the chain — so exactly one named test moves and the collateral-red population stays at five. **The reopen also settles a general question this document had answered the wrong way**: an earlier draft declined the row on the tab-arm bullet's ground, that adding a member would put this document one above the design's matrix. When the guard is real and the only obstacle is a count, the count moves and the design owes the row; the tab-arm bullet's ground survives only for its own case, where nothing is unguarded. Body-scoped `81 rows` was re-swept before this edit and reads **0**, independently of the same sweep from the round, so no site was left behind at the earlier move. **REOPENED A THIRD TIME, announced first, for one sentence — and the sentence is a SECOND SITE of a mechanism this revision had already corrected once** (found by design-author-r17b). When v1.53 rewrote `field-escape-removed`'s payload it fixed the row, the matrix and the Conventions enumeration, and left AC-4.1's newline bullet describing the OLD mutant: *the raw newline splits each verdict into two physical lines*. Under the NARROWED mutant it does not — the quotes are kept, the c1 pass is kept, LF is `Cc`, so the newline is escaped and the verdict stays one line. Only the escaped-SPELLING assertion moves. The matrix cell was right and the prose beside it was wrong, which is the harder half of this class to see: a correct table does not vouch for the paragraph next to it. **The class, stated once so the next reviser gets it for free**: a mechanism corrected at the site that OWNS it must be swept for the sites that DESCRIBE it, and the sweep is by mutant name rather than by the wording being replaced, because the stale wording is exactly what a reviser will fail to recall. Run here, that sweep returns **6** `field-escape-removed` sites in the body, of which one was stale and five were already correct; the stale-phrasing screen now reads **0**. **The freeze-sha field names `fbc2ea0`, the parent the batch lands on.** The four feature documents are byte-identical across `09e9307..fbc2ea0` — `git diff --name-only 09e9307 fbc2ea0 --` over the four explicit document paths is empty — and `git diff --name-only af19d53 fbc2ea0 -- h-mad handoff` is **empty**, so every reading this document stamps over `h-mad/` or `handoff/` at `af19d53` or `09e9307` holds unchanged at `fbc2ea0`. What `fbc2ea0` adds is four files under `docs/03-analysis/probes/doc-block-exec/`, which is why the heading-differential paragraph below stops saying the probe source is absent from the tree. **Freeze-scope check, run per CENSUS and not per root** (round-seventeen correction C10, whose species is that `fbc2ea0` committed four probe scripts under `docs/03-analysis/probes/` and every REPO-WIDE `*.py` census in this feature's documents moved with them, while both `h-mad`/`handoff`-rooted closure predicates read clean). Every census command this body publishes was enumerated by sweeping it for `git grep`, `git ls-files`, `git diff --name-only`, `pytest --collect-only` and `rglob`, and each was re-run at `fbc2ea0`. All but one name `h-mad`, `handoff` or an explicit sha pair as their root, so the probe commit cannot reach them, and each reproduces: residual (b)'s fence-state sweep **7** bodies and its source-guard screen **2**, the tracked `.md` corpus **30**, and the `*.sh` three-backtick absence still empty. The one census with no root is the repository-root pytest collection, and it DID move — 2809 to **2814** — **but NOT at this freeze, and the attribution is corrected here rather than assumed from the correction that prompted the check**: pytest collects only `test_*.py` and `*_test.py`, and the four probe files are named for their measurement and their date, so `--collect-only` gathers **0** items from `docs/03-analysis/probes/` — verified at `fbc2ea0`. The +5 is `af19d53`'s, which added exactly **5** `def test_` functions to `h-mad/tests/test_h_mad_assemble_audit.py` — counted off `git diff 3f70eb3 af19d53 -- h-mad/tests`, one file, 102 insertions. So the class C10 names is real and this document has a member of it, but the member moved one freeze earlier than the commit that surfaced the class; that pair is re-measured and re-stamped in the AC-6.4 note rather than cleared by assertion, and **the probe commit moves no census this document publishes at all**. **The three REPO-WIDE `*.py` censuses the correction names DID move, and this document publishes none of them** — measured at both shas rather than assumed either way: `git diff --name-only 74e126f <sha> -- '*.py'` reads 2 at `af19d53` and **6** at `fbc2ea0`; `git grep -n '```bash' <sha> -- '*.py'` reads 6 then **8**; `git grep -l '```' <sha> -- '*.py'` reads 24 then **25** — the probe `grammar_corpus.2026-09-03.cd979362.py` carrying markdown fences inside its string literals. The one repo-wide census this document DOES publish is `git grep -hE '^\s*def test_' <sha> -- '*test_*.py'`, and it is **unmoved at 1512** across that span, because no probe file's name contains `test_` and the glob therefore never reaches them. So the qualifier every byte-identity claim in this entry carries is *under `h-mad/` and `handoff/`*, and it is meant literally rather than as a shorthand for the tree. **(1) MUST — intersecting substitution spans (codex must 1; design must 1; decision 3a).** The prescribed algorithm can report a replacement it never performs, and the map-static substring check does not reach the case. Reproduced on 3.11.8 before writing: `abc` under `{ab->X, bc->Y}` yields `Xc` with counts 1/1 and the callback firing 1/0; `abc abc` yields `Xc Xc`, 2/2, fired 2/0; the control `ab bc ab bc` yields `X Y X Y`, 2/2, fired 2/2; and `any(a != b and a in b)` over `{ab, bc}` is False. A span-intersection predicate is added BESIDE the substring one — neither subsumes the other and both directions are demonstrated — with `OverlappingSubstitution(pairs, intersections=())`, a new `intersect:` detail line whose three values are all quoted per spec FR-4 (round-seventeen correction C1; the unquoted-offset spelling the sheet first prescribed is refused by that grammar), `test_substitute_refuses_intersecting_spans` carrying both the refusing fixture and the substituting control, and the row `intersect-check-removed` discriminated from `overlap-resolved-by-order` in both directions. `intersect:` is `DETAIL_KEYS`' TWELFTH member (correction C2), so the tuple, the enumerate-all-twelve sentence and the slot accounting move together: 26 to 27 rendering slots, 19 to 20 quoted, the 7 bare unchanged, 8 + 12 = 20 and 7 + 20 = 27. Residual: a key intersecting itself is outside the predicate and needs no guard — `aaa` under `{aa->Z}` yields `Za`, count 1, fired 1, measured. **(2) MUST — a NUL in a shell payload has no verdict path (codex must 2; design must 2; decision 3b).** Measured: a `Popen` of `bash -c true` returns rc 0, and the same with a trailing NUL in the script raises `ValueError: embedded null byte`, which is valid UTF-8 and so passes strict decoding. The spawn guard becomes `except (OSError, ValueError)` and raises the EXISTING `LaunchFailed("spawn", err)`; the stage label is NOT new and the sheet's claim that it was is corrected (C3) — the four stage labels were already the declared set. Two tests, `test_nul_in_document_block_is_a_launch_failure` and `test_nul_in_preamble_is_a_launch_failure`, the second exercising `_compose`; row `spawn-valueerror-unmapped`, mutually discriminated with `launch-oserror-unwrapped`. **(3) MUST — the rollback identity guard was exempted from discrimination (codex must 3; design must 3; decision 3c).** The exemption's premise was true (the mismatch branch needs a ninth seam) and its conclusion did not follow, since a ninth seam is the ordinary mechanism this document already uses eight times, and `invariants.base.md` Test-discrimination admits no exemption. `os.lstat` becomes the ninth seam — verified not to be among the eight — with `test_rollback_skips_unlink_on_identity_mismatch` and the row `rollback-identity-check-removed`, discriminated from `rollback-leftover-unreported` in both directions because the mismatch branch reports `leftover:` directly rather than through the read-back. The canonical list is now nine, stated identically at every site that carries it. **Task 3's injected-test counts DID move and the seam axis did not, and the two are recounted separately**: `os.lstat` is patched only by the Task 4 test, so no Task 3 test changes seam; but item (7)'s new chained test injects `shutil.rmtree`, so Task 3's injected population goes 12 to **13**, its module-seam side 8 to **9**, its `real_rmtree` side 5 to **6**, and its `Popen`-wrapper side stays **4**, with 9 + 4 = 13. **(4) MUST — AC-1.8's collection test conflicted with the wire-only failure (codex; decision 3d).** The WIRE-PIN is added to `test_docsections.py` and AC-1.8 ran that whole file requiring exit 0, so under `docsections-delegation-reverted` the wire mutant had TWO failing tests and two every-other-test-stays-green claims were false. AC-1.8's test becomes collection-only, which imports the module and enumerates every test and runs none, so a red WIRE-PIN cannot reach it. All three affected sentences are repaired. Residual stated exactly: the pre-existing `test_docsections.py` tests are no longer run in isolation by any AC. **(5) MUST — `field-escape-removed` did not isolate (codex; decision 3e).** Returning the input unchanged drops quoting, control escaping and the c1 pass together, so that one mutant also red the forge test and the unicode test and both discriminated-in-both-directions sentences were false of it. The payload narrows to a bare-quote wrap with the c1 pass KEPT. **The sheet's stated MECHANISM for that payload is FALSE and is reported rather than repeated** (rule 7): `unicodedata.category` of LF is `Cc`, so the kept c1 pass escapes a raw newline on its own and under the narrowed mutant a newline does NOT start a second physical line. Measured against the real renderer and all three mutants over four payloads, the narrowed payload frees exactly `"` and `\` — and NO test in this document carried either character, so the property `json.dumps` uniquely guards had no pin at all and the row would have been killed only by the newline test's escape SPELLING, which is the wrong-catcher class. **This document therefore adds a test the sheet did not ask for**, `test_quote_in_dynamic_field_cannot_close_the_value`, and makes it the row's canonical `test` key; the newline test becomes a regression test on the same mutant. That is a `test`-key change on a design row and is named in the sibling debt below. The matrix is published once as a table with a fourth column for the new test, every cell measured. `field-quoting-removed` is NOT isolated and that is recorded rather than smoothed: it reds three further tests through their quoted-value assertions, and it is not repaired by weakening those assertions. **(6) MUST — the guard-narrowing invariant is false on the live tree (codex must 4; decision 3f).** Re-derived at `fbc2ea0` with the committed 09-04 probe: TRACKED 30/292/82/**1**, GLOB 35/297/82/**1**. The single member is located by a needle over `h-mad/SKILL.md`, one hit, verified — written as a NEEDLE and never as a path-qualified line pin, because the standing precheck control goes red on one, which is a deliberate divergence from the sheet's spelling. It is a bare hash on its own line, CommonMark's empty ATX heading, above the dispatch-verdict heading; the narrowed guard is right about it and the old regex was wrong. The zero-softening invariant is replaced by explicit accounting: every new-only member is enumerated and each is a CommonMark heading. The line is not repaired this round. The `1861157` figures keep their blob stamp. **(7) MUST — cleanup chaining with a null pending outcome (codex must 5; decision 3g).** Measured: a `raise ... from None` inside an `except` leaves `__cause__` None and sets `__suppress_context__` True, so the one-line form suppresses the cleanup error rather than selecting it. An explicit two-branch selection replaces it, with `test_cleanup_failure_after_successful_run_is_chained` pinning the null-pending branch on `__cause__` and `test_cleanup_failure_outranks_timeout_injected` the other. **The round then reopened this item to give the selection a row**, `cleanup-chain-selection-flipped` — the selection collapsed to an unconditional `from pending`, so a successful run whose cleanup fails carries `__cause__ is None` — killed by that same null-pending test. It is isolated: the pending-outcome test still gets the `__cause__` it asserts under the mutant, and the field-asserting test does not read the chain at all, so the collateral-red population stays at five. The matrix moves **84 to 85** and the earlier draft's decline is recorded at the site rather than erased. **(8) MUST — RED counts against the accumulating test file (codex must 6; decision 3h).** Codex's MECHANISM is wrong and is corrected rather than repeated: the assembler does not compare counts, it only prints the pair (`h-mad/scripts/h_mad_assemble_tdd.py:246`); the STOP lives in the implementer prompt at its line 62, read at `fbc2ea0`. The symptom is real, so Tasks 2, 3 and 4 now state WHOLE-FILE totals with every earlier task named as a regression-guard block, and the operational integer for the expected-passing flag is derived from the previous task's own GREEN summary rather than written here as a count over tests nobody has yet written. Task 4's RED failure MODE is rewritten: the entry-point block ships with Task 4, so at RED running the script exits 0 silently — measured on 3.11.8 against a module with no entry-point guard — and the subprocess tests fail on their assertions, not on a traceback. Two absence-shaped ACs are named and required to carry a positive verdict-head assertion so neither passes vacuously at RED. **(9) MUST — the self-reference screen was red on the body it shipped (teammate must 1, filed by codex as a should).** It returned **4** at `09e9307` and **0** at `b3be433`, `00b961f`, `dfae038`, `3f70eb3` and `af19d53`, so all four hits are v1.52's own text, written by two post-DONE reopens. Three are relabelled by version number; the fourth states the stamping RULE and is rewritten to stay general. **v1.53 then broke the same screen with its own new prose and caught it by re-running rather than by assuming** — one hit, in the sentence recording the stamp-carry finding, repaired before DONE. **(10) MUST — the stamp-carry enumeration was a hand list and was short (teammate must 2).** It is replaced by a sweep with its command, its nine v1.53-stamped sites of which eight are members, its named non-members and its residual; the two members the hand list missed were the self-reference screen and the sibling-locator population, both of which had carried a v1.50 stamp through two further revisions. **(11) MUST — a locator published inside the body it is scoped to (teammate must 3).** A fixed-string count on the delta block's header comment read **2** at `09e9307` against **1** at five earlier shas; v1.52's own repair spelled the needle out. It is rewritten with a character-class stand-in and run as a BRE, and the literal needle is back to **1**. **(12) MUST — the freeze-scope clearance of the AST censuses was false (teammate must 4).** Re-run against blobs at each sha with the sweep exactly as published: `335f535` 22, `74e126f` 22, `af19d53` 23, `09e9307` 23, and 23 on the tree v1.53 ships; the new member is `h-mad/scripts/h_mad_assemble_audit.py:247` `_trim_version_history`, the function the round-sixteen freeze commit itself added. Residual (a) now publishes 23 with that member named beside `traced_bindir` and `run_with_bindir`, each figure carrying its stamp inline (teammate should 3), and the v1.52 entry carries a dated correction. **Every should-fix is applied and none rejected.** The six-token GNU-divergence sweep is re-stamped in the same edit that re-runs it and still returns **3**, all three prose about the class (teammate should 1). The v1.52 entry's category label is corrected in place: that diff names 8 files, and two of the four it kept are this feature's DESIGN audit reports, so the label is false of half of them; the byte-identity conclusion is unaffected and reproduces (teammate should 2). The live collection pair is re-run at `fbc2ea0` — **2814** from the repository root and **2552** from `h-mad/tests`, divergence **262** — so the divergence the paragraph rests on is confirmed invariant while both absolutes are shown to have moved +5 and are now stamped at the commit they were read on (teammate should 4). Both nits are taken: the ambiguous four-sites clause is gone with the hand list it belonged to, and `_second_surface`'s definition is pinned at `h-mad/tests/test_h_mad_collect_report_docs.py:49`. **Mutation matrix 81 to 85 rows**, 25 + 6 + 26 + 28, split **84 of the helper's source and 1 of `h-mad/SKILL.md`**, updated at every site that states it. The 84 is this round's shared DECISION and is not derived from any sibling's current bytes; the design carries 81 at `fbc2ea0`. **Screen readings, every one re-run after the last edit landed (decision K) and stamped to the tree v1.53 ships, never to `fbc2ea0`.** Marker screen: body **5**, whole file **5**, per-marker five lines each count 1 — unmoved. Restated-cardinal: base `fbc2ea0` body 0/0 and whole file 2 lines / 3 occurrences, shipped tree the same four. Self-reference: **0**. Header-needle locator: **1**. The `.py` pin series: **55 / 55 / 0 / 0** at **23** folded paragraphs on the shipped tree against 49/49/0/0 at 20 on the base, the population NOT byte-identical for the first time in the chain; three distinct pins are added and each occurs twice, once at its use site and once in the chain entry naming it, so the occurrence count rises by six. **This figure was published as 52/52 at 22 in a draft of this entry and the draft was wrong**: the chain entry naming the three pins had not yet been written when that reading was taken, and re-running the screen after the LAST edit landed is what caught it — decision K firing on this revision's own text. Both `SKILL` line-pin screens: **0** and **0**. Six-token toolchain sweep: **3**. Per-needle sibling sweep: 26 / 1 / 1 / 0 = **28** body hits, bins **21 confound / 5 bare / 2 filename**, of the five bare four are this rule's own text and one is a live use — up 3 from v1.52's 25, all three additions in the confound bin, and the third of them arrived in the third reopen's own paragraph, which is why this figure is the post-reopen-3 reading and not the post-reopen-2 one. Sibling locators: all **14** re-run at `fbc2ea0` one needle per invocation, every one exactly one hit in its stated target, split 10 design / 2 plan / 2 spec, the same two second-target caveats and no others. Sha-stamp census on the body: `0aac0b7` 1, `1861157` 6, `1cbddb7` 2, `335f535` 19, `35698f9` 12, `3f70eb3` 2, `4e4a00c` 9, `68a70d6` 4, `6b4df35` 2, `6f0ee85` 4, `700c599` 32, `74e126f` 6, `7d8e797` 2, `8909ec4` 1, `af19d53` 4, `b3be433` 3, `b7d0d77` 9, `cf3a862` 4, `dfae038` 6, `e8eaf6f` 5, `fbc2ea0` 10. `PRECHECK: PASS issues=0` with **seven** allow-listed grammar specimens, one more than the six earlier entries used: the seventh is the new intersect detail line, and the forms are described here rather than quoted, because quoting them in this entry is itself a finding. **Sibling debt, reported and not edited**: the design owes the same four mutation rows and the 81-to-85 total, the nine-item seam list stated identically, the intersect detail-line row and its constructor-form triage alternation (already one member short at `fbc2ea0`), the narrowed `field-escape-removed` payload at its own row AND that row's `test` key, which moves to the new quote test, and the AC-1.8 row wording — the phrase the sheet attributed to the spec sits in the DESIGN's AC-1.8 row, and the spec body holds 0 of it (correction C4). The spec owes AC-2.7's second clause, the launch-failure member, the twelfth detail key and AC-1.8's collect-only wording. The plan owes the `fbc2ea0` heading-differential reading beside its `1861157` figures. Owed by nobody yet: the bare-hash line in `h-mad/SKILL.md`, deferred to the tooling batch, and nothing further on the cleanup-chaining selection, which was the one item this entry left unowned at the first DONE and now carries `cleanup-chain-selection-flipped` as row 85.
- v1.54: **Round-eighteen GATING audit (impl-plan audit v48), answered at the freeze sha `cac6edc`** — a teammate leg (must 2 / should 1 / nit 1 over 19 files opened and 150 greps run) and a codex leg (must 6 / should 2 / nit 0 over 9 files and 4 greps); no item is a must on both legs, so the impl-plan union is **8** distinct musts. **This revision claims no gating pass, no two-surface clean and no exit gate**; the gate is c49. Every reading in this entry is re-measured at `cac6edc` unless it names another sha inline, and a reading taken over this revision own post-edit body is stamped to the tree v1.54 ships. **REOPEN RULE OBSERVED**: every screen this revision's own new text can move was re-run AFTER the last body edit and re-stamped in the same edit that re-ran it, and one of those re-runs found a self-break and a live locator failure, both repaired below.
  **(1) MUST — RED ON MAIN, and it is this document that is red** (round-eighteen sheet C2 i, task #102). `b39d9dc` inserted `DISPATCH_OVERHEAD_CHARS` and `prompt_oversize` into `h-mad/scripts/h_mad_assemble_audit.py` above `_trim_version_history`, which moved from `:247` to `:264`; the precheck's `PINDRIFT` detector fired on all four of this document's pins into that file and took its hard-finding count to 15, so `test_h_mad_precheck_doc.py::test_noise_floor_on_documents_that_survived_eighty_cycles` has failed on the committed tree since that commit. **Re-pinned, not merely re-stamped** — `grep -n '^def _trim_version_history' h-mad/scripts/h_mad_assemble_audit.py` reads **264** and `sed -n '247p'` on that file at `cac6edc` prints an EMPTY line, so the old pin was provably wrong rather than merely unflagged; `_braces_outside_fences` is re-verified UNMOVED at `:109`. Precheck after this revision: `PRECHECK: FAIL issues=11`, hard findings **11**, `PINDRIFT` **0** — the eleven are the design grammar's `overlap:`, `intersect:`, `os_error:`, `pgid:`, `stream:` and bare-versus-quoted field slots, unchanged and legitimate — named by KEY here rather than re-spelled, since re-spelling one is what took this entry's own first draft to twelve. One new AC drafted here briefly took the floor to 12 by re-spelling an `os_error:` slot; it was rewritten to name the KEY instead, which is why the floor is back at the pre-existing eleven and this revision adds no hard finding. `pytest h-mad/tests/test_h_mad_precheck_doc.py -q -p no:cacheprovider -k noise_floor` → `3 passed, 21 deselected`.
  **(2) MUST — the empty-ATX-heading specimen is GONE and the accounting goes to N=0** (sheet FACT 3, operator decision #99). `b39d9dc` also removed the bare `#` from `h-mad/SKILL.md` that this document's guard-narrowing accounting enumerated as the single live `new_only` member. The repair is kept: the accounting model was written to hold any N. The committed 09-04 probe re-run at `cac6edc` prints TRACKED `files=30 both=292 old_only=82 new_only=0`, `titleless=0`; GLOB `files=35 both=297 old_only=82 new_only=0`. The `fbc2ea0` readings keep their stamp; the needle-based locator RULE survives the specimen and is now stated as a rule; the specimen moves to the past tense with `grep -c '^#$' h-mad/SKILL.md` reading **1** at `fbc2ea0` and **0** at `cac6edc`; and the case is now held by a `tmp_path` FIXTURE, `test_titleless_heading_is_a_new_only_member`, added as an AC-1.5 row. **No test or mutation row asserted the live specimen** — verified by value grep before writing — so the matrix total is UNMOVED at **85** and the plan owes nothing on it.
  **(3) MUST — `OverlappingSubstitution` has ONE representation and it is the design's** (sheet FACT 4 a; codex must 3, filed from both sides at r17). The `pairs` + `intersections` split is gone at all nine sites: one tagged `pairs` list of `(kind, a, b, offset|None)` with `kind ∈ {"overlap", "intersect"}`, and the renderer reads `kind` to choose the detail line.
  **(4) MUST — the span scan enumerates OVERLAPPING occurrences** (sheet FACT 4 b): `re.finditer(r"(?=" + re.escape(k) + r")", text)` with span `(m.start(), m.start() + len(k))`. Measured on 3.11.8: on `aaab` under `{aa, ab}` the lookahead form finds an intersection at index **2** and the bare form finds none, so `test_substitute_refuses_overlapping_occurrences_of_one_key` is added as the fixture that DISCRIMINATES the two scan forms. Round seventeen's self-intersection residual is WITHDRAWN, since the same fact falsifies its reason.
  **(5) MUST — AC-3.14 asserts `__cause__` identity, not `__suppress_context__ False`** (sheet FACT 4 c; codex must 1). Probed on 3.11.8: `raise err from ce` inside an `except` sets `__cause__` to `ce` AND `__suppress_context__` to **True**, so the old assertion rejected the prescribed implementation. **The sweep found ONE wrong site of four**: the other three `__suppress_context__` sentences describe `from None`/`from pending`-with-None and are correct.
  **(6) MUST — `LaunchFailed.__init__`'s `err` annotation is `OSError | subprocess.TimeoutExpired | ValueError`** (sheet FACT 4 d; codex must 2). Task 3's spawn guard is `except (OSError, ValueError) as err` and passes the NUL `ValueError`, which the two-member union excluded. Swept by the spelling the document uses: exactly one annotation site.
  **(7) MUST — Task 2 asserts exception DATA; the emitted detail line is asserted in Task 4** (sheet FACT 4 e; codex must 4). `test_substitute_refuses_intersecting_spans` could not meet Task 2's own GREEN boundary while asserting a Task 4 renderer's output. The line is now pinned by a new Task 4 AC, `test_cli_subst_overlap_detail_lines`, whose two legs pin the `kind` tag to the line it selects.
  **(8) MUST — Task 5's scaffold KEEPS the exactly-one-gating-fence guard** (sheet FACT 4 f; codex must 5). Probed over zero, one and two matching bodies: unguarded gives `IndexError` / the body / the FIRST body, so a DUPLICATED fence was silently accepted where the shipped consumer refuses it. Both asserts are restored in step 0 AND in both mutation payloads, which preserves the literal symmetry the old text dropped them for; the transient-window paragraph is withdrawn.
  **(9) MUST — Task 2's `AttributeError` REDs are stated as BY CONSTRUCTION** (sheet FACT 4 g; codex must 6). The tooling half landed at `b39d9dc`: the implementer prompt now scopes the unwritten-test rule to `wiring` tasks and blesses a new-symbol task's first `AttributeError` when the same test asserts post-GREEN behaviour. Cited BY NEEDLE — `grep -n 'by construction' h-mad/references/codex-implementer-prompt.md`, one hit at `cac6edc` — never by line, because a copied pin into that file is task #29. Task 4's split gains the same statement.
  **(10) MUST — `_field`'s docstring cardinal 19 → 20** (teammate must 1). The code-structure block is what 5d writes verbatim and what 5e quotes as exact-once anchors, so 19 would have landed in shipped source; 19 + 7 bare is 26 against this document's own 27 slots. Re-derived here: 12 `DETAIL_KEYS` members + 15 distinct head field names = 27 slots, 8 quoted head fields + 12 quoted detail values = 20, 27 − 20 = 7 bare.
  **(11) MUST — `wire-unconditional` joins the collateral-red carve-out** (teammate must 2), and the DERIVATION RULE is stated at that site rather than the sentence recalled. Re-derived by reading every row: the wire side has exactly three members — `wire-revert-extract`, `wire-unconditional`, `consumer-from-import` — and the other five name one killer each.
  **Should-fixes, all applied.** The baseless ordinal *the third row in this document* is dropped and the population named (teammate should 1); Task 2's stale *nine* is gone and its count is DERIVED — twelve distinct `test_` names in the AC list less the one Task 4 forward reference is **eleven**, carried to the header, to `--expect-fail` and to the RED gate (codex should 2); and `test_cli_nul_composition_is_a_verdict_on_both_paths` adds the SUBPROCESS half of the two NUL composition paths that Task 3 pinned only at the API (codex should 1). The nit is taken as prose rather than a table, since Task 3's pair is stated with mutual discrimination already.
  **Present-tense census figures re-stamped at `cac6edc`, each re-run here in its own invocation and each named as a COLLECTION or a SOURCE census rather than a passing count**: `--collect-only -q -p no:cacheprovider` reads **2836** from the repository root and **2574** from `h-mad/tests`, divergence **262** for a third consecutive freeze; `git grep -hE '^\s*def test_' -- '*test_*.py' | wc -l` reads **1527**; `ls h-mad/tests/test_*.py | wc -l` reads **89**. The `2814`/`2552` readings stamped `fbc2ea0` are blob readings and keep their stamp. **Nobody writes "2574 passed"**: at `cac6edc` the h-mad suite collects 2574 and does not run green, because this document's own precheck reading was the failure item (1) repairs.
  **Screens re-run after the last edit and re-stamped in the same edit** (the v1.52 enforcement condition): marker screen body **5** / whole file **5** with five markers at count 1, unmoved; restated-cardinal screen body **0** / **0**, whole file **2** lines / **3** occurrences, unmoved; both `SKILL` screens **0**, unmoved; the `## `-slicer sweep **23**, with its new member re-pinned; the four `.py:` screens **55 / 55 / 0 / 0** at **23** folded paragraphs on the base `cac6edc` and **56 / 56 / 0 / 0** at **23** on the tree v1.54 ships, the delta being exactly the re-pin plus its own naming sentence; the per-needle sweep **30** / **1** / **1** / **0** = **32**, re-classified mechanically as 22 confound + 8 whole-word + 2 sibling-filename [these four integers read 29 / 1 / 1 / 0 = 31 with a whole-word bin of 7 until reopen 2 corrected them — see the reopen-2 paragraph below, which is where the defect and its class are recorded]. **A SELF-BREAK was caught by that re-run and repaired before DONE**: the `.py:` screen paragraph's own first draft spelled the superseded `…:247` pin in full and so planted a stale pin the moved provenance would no longer flag — the #29 class inside the sentence describing the repair for it — and both spellings now carry the leading-ellipsis device residual (ii) already uses.
  **A LIVE LOCATOR FAILURE was found by re-running the fourteen sibling needles at `cac6edc` rather than carrying the `fbc2ea0` reading**: the bare phrase `guard it removes` read **1** at `fbc2ea0` and **2** at `cac6edc`, because the design's own round-seventeen revision added an `awk` line quoting the table header the needle selects on — the needle-drifts-inside-a-single-commit class this document names for `both halves of`, recurring on a second needle. It is replaced by the anchored table-row prefix, which reads exactly one at both shas, moving the split from **8 + 6** to **9 + 5** at the same total of **14**. Every other needle returns exactly one hit in its stated target, with the same two second-target caveats.
  **Also corrected, and it is a stamp defect rather than a figure defect**: the per-needle sweep read *on the tree v1.52 ships* while saying *re-run after v1.53's last edit landed* — the two-trees-one-blob species v1.52's own must (1) closed, recurring one revision later at the site that closed it. Both halves now name v1.54.
  **Mutation totals, derived from the per-task lists in this document and unmoved AT THE FIRST DONE** [**superseded by the first reopen below, which takes them to 86**; this sentence is the chronological record and is NOT the shipped total]: 25 + 6 + 26 + 28 = **85**, split 84 helper-source and 1 of `h-mad/SKILL.md`. Four acceptance criteria are added this revision and NONE adds a mutation row, each saying so at its own site with the reason and the design-side debt named. **Cross-document check run against the SIBLINGS' bytes at `cac6edc`, never their working files**: the spec's AC-3.14 already asserts the `__cause__` selection and never mentions `__suppress_context__`, so — contrary to the sheet's routing of FACT 4 c — the spec owes nothing there; the design's four `__suppress_context__` sites and its `OverlappingSubstitution` spelling are the design's to move.
  **REOPENED ONCE AFTER DONE, announced before the first edit, every screen re-run before the second DONE, and the version deliberately NOT bumped again** — the reopen answers an orchestrator cross-check, not a new audit cycle, so it amends this entry rather than opening v1.55. Two changes, both driven by the design's r18 revision (v1.110) read out of its WORKING body rather than out of `cac6edc`. **(a) ONE test name, and the design's spelling wins**: the AC-2.7 scan-form test carried a name of this document's own coining while the design's new row named it `test_substitute_refuses_overlapping_occurrences_of_one_key`; both spellings were new this round, and two names for one test is the cross-document defect the round exists to close. The design's wins, and this document renames its two sites. **The superseded spelling is DESCRIBED here and deliberately not quoted** — the device the v1.51 entry's bracketed correction uses — so that a later reviser grepping this body for a second live test name finds none: a residual grep for it returns **0** across the whole file, Version History included. **(b) The design ADDED the mutation row this document had recorded as a design-side debt** — `intersect-scan-non-overlapping`, mutating the span scan's lookahead back to `re.finditer(re.escape(k), text)` — so the row is now MIRRORED in Task 2's list bound to the full node ID `tests/test_h_mad_doc_block_exec.py::test_substitute_refuses_overlapping_occurrences_of_one_key`. **Its discrimination is derived in both directions rather than asserted**: `intersect-check-removed` deletes the predicate and is red on the `abc` fixture, while this row keeps the predicate and narrows only its scan, under which `abc`'s two spans are each a first occurrence of their own key and `test_substitute_refuses_intersecting_spans` stays GREEN — so the `abc` fixture cannot kill this row and the `aaab` fixture can, which is why the two fixtures are two tests. **The matrix moves 85 → 86 and the arithmetic is re-derived, not edited**: the +1 lands in Task 2, 6 → 7, with Tasks 1, 3 and 4 unmoved, so 25 + 7 + 26 + 28 = **86**, split **85 helper-source + 1 `h-mad/SKILL.md`**. **86 is a reading over a SIBLING's post-edit body and is stamped to the tree THIS BATCH ships, never to `cac6edc`** (freeze-sha rule, third clause): the plan's published `awk` over the design's mechanism column prints `total=85 skill-md-target=1` against `git show cac6edc:…design.md` and `total=86 skill-md-target=1` against the design's working body, so the split is confirmed against a sibling rather than asserted and only the helper-source half grew. **One instruction in the reopen brief is NOT followed as written, and the disagreement is reported rather than absorbed**: the brief directs that the sentences saying *no row follows … the design's to add* be rewritten because "the design DID add it this round". That is true of exactly ONE axis — the substitution scan — and the other five such sentences stand on different axes (the heading tab arm, the fence tab-indent arm, the empty-ATX arm, the space-only closing-hash strip, the renderer's kind selection, and the NUL CLI surface), for which the design added nothing. Rewriting those to claim the design supplied their row would have been false, so each keeps its own disposition and gains only the corrected total, with the scan axis named as the one that moved. Every `85` still standing in the body is a sha fragment, a `design v1.85` provenance citation, the new helper-source half of the split, or a historical stamp (`81 → 85`, `back-dated to 85`, the round-seventeen move) — checked by printing all twenty-four with context.
  **REOPENED A SECOND TIME, announced first, answering an ADVISORY delta review of this revision's own diff** (`docs/03-analysis/doc-block-exec.impl-plan.delta-review.r18.md`, must 2 / should 4 / nit 1); the version is again not bumped, because a delta pass on a revision's own diff is part of that revision. **BOTH MUSTS ARE THE SAME CLASS AND IT IS THE CLASS THIS ENTRY CLAIMED TO HAVE ENFORCED**: a self-counting instrument re-run before the last edit rather than after it. **(m1)** The per-needle sweep published `29 / 1 / 1 / 0 = 31` while the shipped body reads `30 / 1 / 1 / 0 = 32` — reopen 1's own edit, putting the round-seventeen matrix move into the past tense, added the eighth whole-word hit — and the composition bullet forty-nine lines below already read 32, so one document gave two totals for one blob, which is precisely the two-trees-one-blob shape v1.52 closed. Re-run after this reopen's last edit and published at BOTH sites, with the screen summary above corrected. **(m2)** The bare-phrase locator population moved 6 → 5 when `guard it removes` was re-anchored, and the justification three lines under its own list still reasoned from six; re-derived from the list, corrected to five, and the departing member is now named with the reason it left — repaired, not dropped, which is why the total stays 14. **All four should-fixes and the nit are applied**: the restated-cardinal screen's base moves from `fbc2ea0` to `cac6edc` so both halves of the pair belong to one revision (a stamp defect only — the four integers are unmoved at all three points, each re-run in its own invocation); item (9) no longer attributes the needle-form preference to the `SKILL.md`-scoped control, which asserts `"SKILL.md:" not in joined` and is blind to every other path, and names the LINEPIN advisory class instead; the `codex-implementer-prompt.md:62` pin is re-read at `cac6edc` rather than carried at `fbc2ea0`, since the freeze commit changed one line of that file in place and `sed -n '62p'` still prints the expected-counts STOP rule; the first-DONE mutation total carries a bracketed forward marker to the reopen that supersedes it; and `cleanup-chain-selection-flipped` drops `__suppress_context__ True` from its mutant properties, because the correct implementation sets it True too, so only `__cause__ is None` discriminates. **The rule this reopen adds, stated as a rule because a re-count is not a fix**: a screen whose needle matches the KIND of prose a reviser is still writing is run LAST, after the final edit, and this document carries ten such self-counting instruments — so the enforcement condition is a per-instrument pass and not a single re-run, since re-running nine of ten ships the tenth stale. That residual is now written at the sweep's own site.
