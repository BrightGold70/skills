# Implementation Plan: doc-block-exec

> Source: docs/02-design/features/doc-block-exec.design.md (post-audit, v1.97 — the revision answering design audit v87, its gating round)
> Paired spec: docs/01-plan/features/doc-block-exec.spec.md (v1.59) · paired plan: docs/01-plan/features/doc-block-exec.plan.md (v1.92)
> All three re-derived at `6f0ee85` on 2026-09-04 at the moment this revision was written, with `git show 6f0ee85:<doc> | grep -oE '^- v1\.[0-9]+' | tail -1` — read out of the **commit**, not the working tree, because the three sibling documents were being revised concurrently by their own authors while this revision was written, and a working-tree read would pin a document no commit contains. The three sibling authors are working **concurrently**, so any of these may be one behind by the time this is read — that is drift, not a finding. v1.35 pinned v1.92/v1.53/v1.85 and all three moved within the same session; v1.36 pinned v1.93/v1.55/v1.86 of which two moved again by `a8e0372`; v1.38's v1.93/v1.56/v1.87 was one behind on the design and two behind on the plan by `335f535`, with only the spec unmoved; v1.40's v1.95/v1.57/v1.90 was one behind on **all three** by `35698f9`; and v1.41's v1.96/v1.58/v1.91 was again one behind on **all three** by `6f0ee85`, all three having moved in that commit. That is the measurement behind this sentence, not a supposition.
>
> These three pins go stale the way Task 5's SKILL.md line numbers and AC-6.4's suite floor did, and for the same reason — they name a moving value in another file. **Re-derive them, never trust them**: `grep -oE '^- v1\.[0-9]+' <doc> | tail -1` gives each document's current version, and that is the check to run before acting on anything this header claims. They were last correct at the commit named above; a reviewer finding them behind is looking at expected drift, not a finding. **This header is the one place a sibling version number may appear at all** — the Conventions rule below forbids every other sentence in this document from stating what a sibling currently says, and the reason this line survives it is that it names the commit it was derived at, carries the command that re-derives it, and declares its own staleness as expected.
> Branch target: feature/doc-block-exec

## Executive Summary

One new module, `h-mad/scripts/h_mad_doc_block_exec.py`, lands in five tasks. Task 1 (`wiring`)
creates the scanner, the public bounder, extraction and selection **and, in the same task,
re-points `docsections.py` at that bounder** (the design's author-together order; the
single-source contract never has an intermediate commit with two bounders). Tasks 2–4
(`new-behaviour`) add substitution; execution + bounding; CLI + registry. Task 5 (`wiring`) tags
the Second-surface gate fence and migrates `test_h_mad_collect_report_docs.py`'s executing path.
Every guard the design names carries a mutation row bound to one named test; the three specs
(`doc_block_exec.json` 81 rows, `doc_block_exec_wire.json` 8, `docsections.json` 8) must report `ALL_CAUGHT`.

## Conventions binding every task

- **Interpreter**: `python3.11` (the pinned interpreter with pytest). Every command below runs
  from `h-mad/` unless stated. Never invoke `timeout`/`gtimeout` anywhere (AC-5.3 scans the source).
- **Test file for Tasks 1–4, plus Task 5's two tree-level tests**: `h-mad/tests/test_h_mad_doc_block_exec.py`
  (new in Task 1, extended by later tasks). API tests import the module as
  `import h_mad_doc_block_exec as dbe` with `h-mad/scripts` on `sys.path` (the same arrangement
  `test_h_mad_collect_report_docs.py` uses at its `:22` `sys.path.insert(0, str(SCRIPT_DIR))`).
- **CLI transport split** (design §Test Strategy, last paragraph): every verdict a **real input or
  a real fault** can produce is exercised through
  `subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)` where
  `REPO_ROOT = Path(__file__).resolve().parents[2]` and `SCRIPT = REPO_ROOT / "h-mad" / "scripts" / "h_mad_doc_block_exec.py"`,
  so exit codes are the real process's — marked `(subprocess)` in the ACs. A verdict that needs
  one of the **eight** fault injections — the seven module seams `_final_write`, `_close_stream`,
  `tempfile.mkdtemp`, `os.chmod`, `shutil.rmtree`, `os.killpg`, `os.unlink`, or the `Popen`
  instance wrapper for `communicate`/`wait`/`poll` —
  calls `dbe.main(argv)` **in-process** — its return value is the
  exit code and `capsys` captures the `DOCBLOCK:` and detail lines — because a `monkeypatch`
  cannot cross an exec boundary; marked `(in-process main)`. Two subprocess tests in Task 4
  (`test_cli_exit_zero_propagates`, `test_cli_exit_two_propagates`) pin that `sys.exit(main())`
  turns the return value into the process exit, so the in-process code is the real code.
- **Fixtures are hostile**: markdown strings written to `tmp_path`, with mixed heading levels,
  fences quoting fences, a path containing a space, a body with CRLF, and a key containing regex
  metacharacters.
- **Fault injections — one canonical list of eight, all via `monkeypatch` (restored on exit),
  `subprocess` never mocked** (design v1.73 §Test Strategy, stated identically there): **seven
  module-level seams** in the helper's namespace — `os.killpg` (AC-4.6 reap only), `shutil.rmtree`,
  `tempfile.mkdtemp`, `os.chmod`, `os.unlink` (AC-3.10's rollback read-back only, because a
  directory writable when the first arm creates its file cannot be made unwritable between the two
  arms of one call), the module's `_final_write(handle, text)` seam and its `_close_stream(handle)`
  seam — **plus one instance-level wrapper**: the recorded `Popen` instance's `communicate`, `wait`
  and `poll`. Those three bound methods are **one** injection, not three, so the list is eight, not
  ten. Recording pass-throughs of `subprocess.Popen` and `os.open` are observations, not
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
  `test_bare_form_duplicate_headings_refuse` the regression test on the same guard. Those two are
  the only rows in this document whose mutant reds a second named test; the docsections rows bind
  to the WIRE-PIN / their `_killed_by` / `test_docsections_imports_from_an_unrelated_cwd`, and the
  wire rows to one pin each, with `wire-revert-extract`'s and `consumer-from-import`'s collateral
  reds documented per row rather than promoted to keys) — and every `find` anchor
  matches the landed source exactly once (the harness applies one `find`/`replace` pair per row
  via `str.replace` — `h-mad/scripts/h_mad_mutation_harness.py:645`, inside `run_spec` (`:482`) —
  so a multi-site revert must be expressed as one replacement). Each task appends its rows; the file is created in Task 1. Run
  `python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/doc_block_exec.json`
  and read the `MUTATION:` token — `ALL_CAUGHT` is required before the task is GREEN.
- **When each row's payload is fixed — deliberate, not an omission** (impl-plan audit v20, whose
  must-fix asked for every `doc_block_exec.json` payload to be written here and is REFUTED on this
  ground; the file held 76 rows at that cycle and holds 81 now, and the ground is unchanged by the
  count). **The ordering is this document's own constraint**, adopted from the design's §Test Plan
  and reached by locator rather than by a claim about its content —
  `grep -n 'the mechanism column is what the anchor must express' docs/02-design/features/doc-block-exec.design.md`,
  one hit, verified at `6f0ee85`: exact `find` anchors are set from the landed source **in the same
  task that lands it**, each exact-once, and the mechanism column is what the anchor must express.
  So for
  `doc_block_exec.json`: **the mechanism named beside each row is the contract and is fixed now**,
  as is the row's `test` key (a full node ID, fixed now); the `file`, the exact-once `find` and the
  `replace` are written **at 5e, from the landed source of the task that just went GREEN**.
  `h-mad/scripts/h_mad_doc_block_exec.py` does not exist until 5d, so quoting anchors into it now
  would mean inventing source text and then pinning mutations to text nobody has written — the
  placeholder class this document forbids, and a `find` that misses is scored a refusal, not a
  kill (`h-mad/scripts/h_mad_mutation_harness.py:609–623`, the `anchor_status` refusal branch inside
  `run_spec`, `:482`). **The axis is not which spec a row belongs to — it is whether the row's anchor file exists at
  HEAD** (impl-plan audit v34). **The rule**: a row whose anchor file exists at HEAD carries its
  `find`/`replace` payload **in this document already**, quoted exactly from that file; a row whose
  anchor file is `h-mad/scripts/h_mad_doc_block_exec.py` carries its mechanism and its `test` key
  now and gets `file`, the exact-once `find` and the `replace` at 5e, from the landed source of the
  task that just went GREEN. `doc_block_exec.json`'s 81 rows are wholly on the second side.
  `doc_block_exec_wire.json`'s 8 rows are wholly on the first (anchor:
  `h-mad/tests/test_h_mad_collect_report_docs.py`). `docsections.json` **straddles the axis**:
  **six** of its eight rows anchor in `h-mad/tests/docsections.py` and carry their payloads here —
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
  both sound and complete; both directions were measured at `335f535`. *Over-count*: the sweep
  below prints **22** named helpers under `h-mad/tests`, `h-mad/scripts` and `handoff` holding the
  substring `## ` beside a `find`/`index`/`split`/`startswith` call, and several are not section
  slicers at all (`traced_bindir`, `run_with_bindir` and two `main`s among them). *Under-count*:
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
    — one hit, verified at `6f0ee85`: it anchors on a **substring**, so
    `docsections.titled_section(SKILL_MD, "Run-context ceiling")` cannot find the real heading,
    which is located by name with `grep -n '^## Run-context ceiling' h-mad/SKILL.md` — one hit,
    verified at `35698f9`, reading `## Run-context ceiling — halt the run at 80%`. **The line
    number is deliberately not written**: v1.39 wrote one here and it was the sixth recurrence of
    the stale-`SKILL.md`-pin class, caught by the standing control
    `tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins`,
    which asserts no path-qualified `SKILL.md:`*N* pin survives this document's LINEPIN details.
  - `section_text` (`h-mad/tests/test_h_mad_batch_doc_rules.py:26`) asserts exactly one
    `l.strip() == f"## {name}"` and then bounds on `lines[end].startswith("## ")`.
  - `_section` (`h-mad/tests/test_h_mad_collect_report_docs.py:40`) bounds on `text.find(start)`
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
  recurred **five** times and every recurrence cost a full dual-surface audit cycle. The list, and
  the count is `len(list)`: **(1)** v1.24's two
  quoting flags against the design, already answered eleven design revisions earlier (withdrawn
  at v1.35); **(2)** the AC-6.1 restriction flag, already landed in design v1.92 (withdrawn at v1.35);
  **(3)** the 5f note's clearance citing a drifted `spec :458` (repaired at v1.35); **(4)** the 5f note's
  **debt**, still asserted at v1.36 after spec v1.54 had paid it (withdrawn at v1.37) — the same
  class in the opposite direction, a stale clearance replaced by a stale debt; and **(5)** the
  `StreamPathUnwritable` signature sentence in the Task 4 exception block, *"The design's exception
  table agrees (v1.71, impl-plan audit v16)"*, caught by impl-plan audit v39 and repaired at v1.42
  in form (b) below.
  **The fifth is the one that matters most, and it is why this list is incremented rather than
  scoped away.** It predates the rule — it was written at v1.17 — so it was never a *new* lapse;
  it is the class's **survivorship** arm. It outlived v1.37, the revision that wrote the rule;
  it outlived v1.39's item (9), which **reported having restated it by name** and did not touch it
  (`git diff 335f535 74e126f` on this file changes no `StreamPathUnwritable` prose, and
  `git show 74e126f:docs/01-plan/features/doc-block-exec.impl-plan.md | grep -c 'exception table agrees'`
  is 1, as at `0aac0b7`, at `35698f9` and at `6f0ee85`); and it outlived v1.41's own decision-E
  pass. By the time it was found, the cited design version was **26 revisions** behind the design at
  the freeze sha. The lesson the four earlier members do not carry: **a sweep over a class with no
  detector can report a member it never edited**, so a sweep's own claim to have closed a member is
  not evidence the member moved — the diff is. Two forms are
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

  returns **nothing — 0 occurrences** — against this document at `6f0ee85`, the freeze sha this
  revision is authored against and the commit every figure below was re-derived at. (`6f0ee85` is
  the commit v1.41 shipped **in**; it is the base v1.42 is written **against**, and the shipping
  commit of this revision does not exist while it is being written, which is why every figure here
  names `6f0ee85` and not a promise.) The **before**-figure, at the base the class was closed from, `35698f9`, is
  **22 occurrences across 19 lines over 8 distinct files** (`h_mad_mutation_harness.py` ×9,
  `docsections.py` ×4, `test_h_mad_portable_timeout.py` ×2, `test_h_mad_collect_report_docs.py` ×2,
  `h_mad_assemble_tdd.py` ×2, and one each of `test_suite_collection.py`,
  `test_h_mad_context_budget_docs.py`, `test_h_mad_audit_cycle.py`). **Both halves carry their own
  sha and their own unit**, which is the whole point of writing them: the after-figure is the block
  above run at `6f0ee85`; the before-figure is the same block with the file read out of the base
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
  `grep -oE '[A-Za-z0-9_./-]*\.py: ?[0-9]+'`) was re-run beside it at `6f0ee85` and returns the same
  set as the line-scoped screen. **The property is the AGREEMENT, not an integer**: both screens
  return **0** bare-filename occurrences, and their path-qualified populations are identical. That
  population is a dated example and deliberately not a contract — at `6f0ee85` *after* this
  revision it is **49 occurrences across 19 folded paragraphs** (`| wc -l` on `grep -oE` for
  occurrences, `grep -cE` for paragraphs — one `grep`, two true integers), and this revision's own
  edits moved it from **47**, which is precisely why the closure is stated as a relation and the
  bare-filename **0**, never as a frozen count a later edit falsifies.
  **The `tr -s ' '` is new at v1.42 and it is a repair, not decoration** — the fold joins with a
  single space but **keeps the next line's leading indentation**, so a needle wrapped mid-phrase
  folds with a run of spaces in it and the variant misses it. Measured with a positive control, in
  the spirit of the rule that a screen needs both halves run: this document's own phrase
  `never a census` is wrapped between `a` and `census`, and the fold **as previously published
  scores 0 on it while the `tr -s ' '` form scores 1**. The bare-filename figure is unaffected
  either way — both forms return 0 — but it was unaffected *incidentally*, because no `.py:` pin in
  this document happens to wrap between its colon and its digits, and the regex allows only **one**
  optional space there. A blind form that has never been shown to fire is not a control, which is
  how this was found. (iii) The **symbol-name** half has no detector at all — the symbol may sit several words
  from the pin — so it is enforced by reading, and its recurrence is what audit v38 and plan audit
  v78 caught.

  **The tree pins this document stamps `335f535`, `74e126f` and `35698f9` are unchanged at
  `6f0ee85`, the freeze sha this revision is authored against, and that closure is stated once here
  rather than re-stamped on ~40 pins**:
  `git diff --stat 335f535 74e126f` touches **9** files, all under `docs/`, and
  `git diff --name-only 74e126f 6f0ee85 -- h-mad handoff` is **empty** — no file under `h-mad/` or
  `handoff/` moved anywhere across that span, which contains `35698f9` — so every `path:line`
  derived at `335f535`, `74e126f` or `35698f9` is
  byte-identical at `6f0ee85`, and the older stamps are provenance facts rather than stale pins.
  Re-run in this revision, not carried from v1.41's: the `74e126f 6f0ee85` form is the one that
  matters now, because it is the only one that reaches the freeze sha, and `git diff --name-only
  6f0ee85 -- h-mad handoff` is empty too, so the working tree a 5d implementer reads is that same
  tree.
  Sibling `docs/` values are the ones that did move, and each of those is re-derived
  above at `6f0ee85`, the freeze sha this revision is authored against. A `docs/` pin has neither property — the
  sibling's own author may have renamed the sentence, and there is no symbol to grep for.
  **How a needle is chosen, and the hard condition on it** (added at v1.40; impl-plan audit v37).
  **This is NOT a member of the list above at all, and v1.40 wrote that it was** (impl-plan audit
  v38, which found the document then contradicting itself at three sites over the same ordinal).
  Stated as a content predicate rather than an ordinal, deliberately, because an ordinal here is
  what drifted at v1.40 and the list has since grown to five: **membership is decided by whether
  the sentence asserts what a sibling contains, never by position in the list**. The list above is the **prose-agreement** class — a
  sentence asserting what a sibling contains. What audit v37 found was a **form (a) locator
  breakage**: a needle that stopped returning exactly one hit. The foot of this bullet separates
  the two deliberately, because form (a) has a detector and prose agreement has none, so a single
  ordinal spanning both would count two different failures with two different remedies. The list
  above stands at **four**, and what decides membership is a **content predicate, not the
  ordinal**: a sentence is a member if a sibling's author could pay it, ignore it, or have paid it
  already.
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
  its target row* — a backticked identifier, a verdict token, or an anchored table-row prefix
  (`^| \`name\``) — never a bare English phrase, because a bare phrase is exactly as perishable as
  a line pin and perishes for the same reason.
  **This preference is stated as a preference, not a hard rule, and the reason is measured**: at
  `6f0ee85` this document carries **13** distinct `docs/`-sibling locators (7 + 6, the two lists
  below), and after this
  revision **7** satisfy the preference (`` `_titled_section` anchors on a substring ``,
  ``^| `DOCBLOCK: BAD_INFO key=``, ``^| `DOCBLOCK: SUBST_OVERLAP keys=``,
  ``both halves of `overlap:` ``, ``^| `registry-row-removed` ``,
  ``^| `detail-line-undocumented` ``, and `git rev-parse --show-toplevel`) while **6** are bare
  phrases (`the mechanism column is what the anchor must express`,
  `The sweep excludes build output`, `Heading selector differential`, `guard it removes`,
  `One node per glob-parametrised test`, `Bounds: 1200 s`). Those six are **retained**, because
  their target rows carry no backticked identifier to anchor on and a needle invented for the
  preference's sake would point at a row the sibling's author never wrote that way. A rule this
  document violates six times at the commit it ships is a rule that gets ignored, so the
  detectable half is the rule and the undetectable half is the guidance.
  **The residual, stated exactly**: the one-hit property is true only at the commit it was
  measured at, so it is re-established every revision or not at all. **Re-swept for v1.42 at
  `6f0ee85`, every one of the 13 re-run in this revision rather than carried from v1.41's sweep or
  from any report: all 13 return exactly one hit.** Each needle was run against the sibling **as of
  that commit** — `git show 6f0ee85:<sibling> | grep -c -- '<needle>'` — and not against the working
  tree, because the three sibling authors are revising those files concurrently while this
  revision is written, so a working-tree read would measure a document no commit contains. This was
  a real re-measurement and not a formality: **all three sibling documents were revised** between
  the sha v1.41 swept at and this one —
  `git diff --name-only 35698f9 6f0ee85 -- docs/01-plan/features/doc-block-exec.plan.md
  docs/01-plan/features/doc-block-exec.spec.md
  docs/02-design/features/doc-block-exec.design.md` names all three, and no sibling **version
  number** is written here because the Conventions rule above reserves those for the header.
  The **count is unchanged at 13** and the 7/6 preference split with it: v1.42 added no locator —
  the decision-E repair it made (the `StreamPathUnwritable` signature) took the Conventions rule's
  form **(b)**, not form (a), precisely so that a needle into a design row would not be minted in
  the same round the design is being revised.
  v1.41's sweep at `35698f9` found the same 13 at one hit each.
  v1.40's sweep at `74e126f` found the same 13 at one hit each,
  after ``both halves of `overlap:` `` replaced the one that had returned two — three consecutive
  revisions at 13/13, each re-run rather than inherited.
  **What the rule does NOT cover, so the sweep is not read as forbidding it**: a bare
  **provenance** citation of the form "(design v1.85)" or "(plan audit v67)", naming the version
  or the cycle at which a decision was *made*, is a dated historical fact about a version history
  — it never expires and this document carries ~40 of them deliberately. What expires, and what
  the rule forbids, is a claim in the **present tense** about what a sibling now contains — a
  `design.md` line pin followed by "renders the detail line as …", "the spec's comment still
  reads …", "nothing is owed to the plan". **The rule covers the MODAL form too, and this is a
  widening** (impl-plan audit v36): "the spec **must** carry X" is a debt in modal dress and
  expires exactly as fast as "the spec carries X" — member **(4)** of the list above, the 5f note's
  **debt** (as distinct from member (3), its clearance), *was* a debt, not a description, so a rule scoped to the present tense would have let its own
  worst instance through. A sentence is inside the rule if a sibling's author could pay it, ignore
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
  `grep -n 'owed\|spec\.md:\|design\.md:\|plan\.md:' docs/01-plan/features/doc-block-exec.impl-plan.md`,
  read outside the Version History (which is a dated record and keeps its pins), noting that
  `owed` also matches `followed`.

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
is why nothing about the grammar changes here and no mutation row is added (the matrix total stays
81; a row on this axis, if the design wants one, is the design's to add). What is added is the
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
  `tests/test_h_mad_precheck_doc.py::test_control_todays_impl_plan_dropped_the_six_stale_SKILL_pins`
  forbids this document from carrying, and the command below reproduces them.)
- the **tab arm is 0, and it is pinned by nothing at all** — no AC in this document prescribed a
  tab-indented fence opener before this revision. So AC-1.6's
  `test_indented_literal_tag_is_not_a_candidate` gains `\t```bash hmad:exec` beside its four-space
  case. **No mutation row follows**: the matrix total stays **81**, and a row on this axis, if the
  design wants one, is the design's to add — the same disposition as the heading axis above.

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
**Both controls were run** (the rule decision A states): *positive* — the scan prints the 29
openers with their files and lines; *true negative* — it **declines 2** indented marker runs that
sit **inside** an already-open fence, in 1 file, which are body text and not openers, and which a
scan without the fence toggle would have counted. **Blind forms, stated rather than left as a bare
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
rendered through markdown-it-py — both 2.2.0 (interpreter-local) and 4.2.0 (the spec's throwaway
venv) — before it was written down, 14 of 14 agreeing on each (plan §Measurements, "Scanner grammar
corpus"): a backtick or tilde run of ≥ 3
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
`grep -n 'Heading selector differential' docs/01-plan/features/doc-block-exec.plan.md`, one hit, verified at `6f0ee85`).
**The corpus is the tracked 25, not a filesystem glob, and the figures are given on both because
the difference is contamination rather than noise** (plan v1.86 / design v1.93; this document
carried "over 30 files (`archive/` excluded) the old regex and `find_heading` agree on 266 headings" through v1.35, a corpus and an agreement count that match
neither reading). Over the **tracked** corpus — `git ls-files -- h-mad handoff` filtered to `*.md`
with `archive/` excluded — the old regex and
`find_heading` agree on **263** headings, `new_only=0` (nothing the old guard refused is newly
accepted) and `old_only=76`, every one a `#` comment line inside fenced code the old regex read as
a heading. Over the filesystem glob — the extras being the gitignored
`.pytest_cache/README.md` artifacts — agreement is **268** with the same `old_only=76` and
`new_only=0`. **Those four integers are a dated measurement, not a constant**: they were taken at
`1861157`, when the tracked corpus was **25 files** and the glob **30**. The differential itself
is the plan's measurement, re-derived there at `1861157` through a throwaway script; this
document transcribes it and did not re-run it, so it is not re-derivable here and is left stamped
at the commit it was measured on. **What is invariant, and what a reader re-runs, is the shape of
the differential, not its size**: `new_only=0` — the narrowed guard accepts nothing the old regex
refused — and every one of `old_only` a `#` line inside a fence. **The corpus relation is
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
read from `h-mad/tests/mutation-specs/docsections.json` and re-read there at `6f0ee85` — is **left exactly as it is**,
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
(`h-mad/scripts/h_mad_mutation_harness.py:482`); re-read in this revision at `6f0ee85`, and
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
pre-mutation check at `h-mad/scripts/h_mad_mutation_harness.py:630-641` (also `run_spec`), which
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
(`test_docsections_unbalanced_four_backtick_fence`, `test_titled_section_ignores_a_heading_inside_a_fence`)
and the source guard `test_docsections_has_no_second_bounder` (the source still defines no
`_fence_aware_end` and scans no marker run). The row's `test` key is the WIRE-PIN. Measured
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

# The complete hierarchy: DocBlockError + 19 subclasses (6 + 3 + 4 + 6), every one defined HERE (Task 1).
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
    def __init__(self, pairs: list[tuple[str, str]]): ...   # sorted (shorter, longer)
# raised by run_block (Task 3)                                                 — 4
class BadTimeout(DocBlockError):
    def __init__(self, value: object): ...
class BlockTimeout(DocBlockError):
    def __init__(self, seconds: float): ...
class CleanupFailed(DocBlockError):
    def __init__(self, path: str, cleanup_error: OSError | None): ...
class LaunchFailed(DocBlockError):
    def __init__(self, stage: str, err: OSError | subprocess.TimeoutExpired,
                 pgid: int | None = None): ...
    # attributes: .stage, .err, .pgid — all three are read by tests and by main's renderer.
    # `err` is a union because the bounded post-kill wait's expiry is carried here too
    # (design v1.73): subprocess.TimeoutExpired is a SubprocessError, NOT an OSError, so the
    # annotation must name both. Written as the exact union rather than BaseException, which
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
# ^ the design's spelling verbatim (design v1.79 §Scanning, line 43) and the same idiom every
#   test under h-mad/tests/ uses for SCRIPT_DIR. Today's docsections.py imports only `re`
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
- [ ] AC-1.5/1.7 `test_closing_hash_run_does_not_change_heading_identity`: pins the normalization rule from both sides, **on both delimiters**. On a document whose only heading is `## Text ##`, both `find_heading(text, "## Text")` (full form) and `find_heading(text, "Text")` (bare form) find it and return the same `(end, 2)` — the closing run is stripped before the comparison, so the raw line is never what is matched. **The fixture carries the tab-preceded form `"## Text\t##"` beside the space-preceded one**, asserted identically, because the closing `#`-run delimiter is spaces-or-tabs and a space-only strip would leave `## Text\t##` unequal to `Text` and so unfindable in either form. On a document holding both `## Text` and `## Text ##`, the full form raises `AmbiguousHeading` with `n == 2`, because the two lines normalize to the same heading rather than to two distinct ones (design v1.67 §Scanning, design audit v63); the tab leg is asserted the same way, on a document holding `## Text` and `## Text\t##`. **Residual, measured at `74e126f`**: over the tracked corpus — `git ls-files -- h-mad handoff`, `*.md`, `archive/` excluded — **30** files hold **0** ATX headings whose closing `#`-run is preceded by a tab. **No live document or fixture outside this test depends on that closing-run tab arm** — shipping it space-only would be a silent divergence from the renderer the scanner grammar was oracled against, not a currently failing document, which is why a fixture rather than a corpus instance is what pins it. (That conclusion sits here, adjacent to its own measurement; v1.40 inserted the toolchain paragraph below between the two and left it stranded at the end of a paragraph about `grep -P`, where "the tab arm" had no nearby antecedent — impl-plan audit v38. The axis here is the **closing `#`-run delimiter**; the fence **opener's** indent has its own, separately measured, tab arm in Task 1's residual above, and the two must not be read as one.) The command is stdlib Python, not `grep -P`, and that is the point: **every runnable command this document ships must run under the stock macOS toolchain**, which is BSD, not GNU. `python3.11 -c "import re, subprocess, pathlib; fs = [f for f in subprocess.run(['git', 'ls-files', '--', 'h-mad', 'handoff'], capture_output=True, text=True).stdout.split() if f.endswith('.md') and '/archive/' not in f]; p = re.compile(' {0,3}#{1,6}[ \t].*\t#+[ \t]*'); print(len(fs), sum(1 for f in fs if any(p.fullmatch(l) for l in pathlib.Path(f).read_text(errors='replace').splitlines())))"` prints `30 0`, and **its output is what the sentence above describes** — the `grep -cP` pipeline this replaced (v1.39) printed a per-file count, not a file count, so its own description was wrong in a second way. The reason it mattered more here than elsewhere: `/usr/bin/grep` on macOS rejects `-P` outright (`grep: invalid option -- P`, rc 2, measured), the pipeline printed nothing at all, and **this feature's own Task 1 inherits `_TIMEOUT_CMD` and `_ABSENCE_CLAIMS` — guards that exist precisely because the stock macOS toolchain is not GNU**, so shipping a GNU-only command inside it was self-contradicting. **Class, re-swept at `35698f9` on this revision** over the GNU-vs-BSD-divergent invocations (`grep -P`, `sed -i`, `readlink -f`, `date -d`, `xargs -r`, `stat -c`) — `awk '/^## Version History/{exit}{print NR": "$0}' docs/01-plan/features/doc-block-exec.impl-plan.md | grep -nE 'grep -P|sed -i|readlink -f|date -d|xargs -r|stat -c'` — the sweep returns **3** lines outside the Version History, one more than v1.40's **2**: AC-3.13, whose `stat -f %Lp .` (darwin) / `stat -c %a .` (GNU) pair already writes both forms; this bullet, which matches because it names the six tokens in prose; and Task 1's fence-opener residual, added in this revision, which matches because it says its command uses **no** `grep -P`. **No GNU-only command survives in this document** — all three hits are prose about the class, none is an invocation. **Residual on the sweep itself**: nothing detects a GNU-only flag in a document — no test, no precheck, no CI step reads the commands this document ships — so the next one is prevented by a reviser running that six-token sweep, not by anything catching it (impl-plan audit v37).
- [ ] AC-1.5 `test_adjacent_heading_bounds_the_section`: `## A` immediately followed by `## B` whose section holds a tagged block — `extract(doc, "## A")` (full form) is `[]`, and with `start, level = find_heading(text, "## A")`, `fence_aware_end(text, start, level) == start` (the adjacent heading's line starts exactly at `start` and is a boundary).
- [ ] AC-1.5 `test_heading_lookalikes_are_not_headings`: a fixture placing `#hashtag`, `#######` (seven), `    ## x` (four-space-indented) and `\t## x` (**tab-indented — CommonMark measures the leading indent in columns and a tab reaches column 4, so this is indented code, not a heading**; the tab leg is what refuses a `line.lstrip()` "simplification" of the predicate, which would accept it) where each would end the requested section or start one — the block under the real heading is still the only candidate (the section owns the block past every lookalike), and a lookalike never matches the requested heading (asking for `# hashtag`, `## x` or the seven-run line in the full form yields no heading match; every `extract`/`find_heading` argument in this file's ACs is the full form unless it says bare).
- [ ] AC-1.5/1.6 `test_requested_heading_quoted_inside_a_fence_is_not_a_section_start`: the requested heading appears first inside a ```` ```markdown ```` fence with a tagged block under that quoted copy, then for real with a tagged block under it; `extract` returns only the block under the real heading (the fenced copy is a `body` line, never a heading match, and the tagged block under it is never a candidate).
- [ ] AC-1.6 `test_quoted_tag_inside_longer_fence_is_not_an_opener`: a four-backtick fence whose body contains ` ```bash hmad:exec ` yields no candidate from the quoted line; `test_tag_quoted_inside_a_tilde_fence_is_not_an_opener`: same inside `~~~`; `test_indented_literal_tag_is_not_a_candidate`: `    ```bash hmad:exec` (four spaces) is never a candidate, **and neither is `\t```bash hmad:exec`** — one TAB, which CommonMark advances to column 4, so it is indented code and not an opener; this is the tab arm of the fence-opener indent, measured at **0** corpus instances at `35698f9` (Task 1's residual above carries the command), so this fixture is its **only** pin, and no mutation row follows — the matrix total stays **81**; `test_backtick_in_info_string_is_not_an_opener`: ```` ```bash hmad:exec `x` ```` is inert — not a candidate, not `BadInfoString`, and the following ``` line opens a fence; `test_closer_with_trailing_text_does_not_close`: a ```` ```trailing ```` line inside a quoting fence does not close it; `test_indented_closer_does_not_close`: a ```` ``` ```` line at four spaces inside a bash fence stays in the body and the fence ends at the next 0–3-space closer; `test_indented_fence_body_is_deindented`: openers at 1, 2 and 3 spaces yield bodies with that indentation stripped, and a body line indented less than the opener loses only what it has.
- [ ] AC-1.7 `test_duplicate_headings_refuse`: two identical `###` headings (fixture mirrors `h-mad/invariants.example.md`), requested in the full form → `AmbiguousHeading` with `n == 2`; `test_bare_form_duplicate_headings_refuse`: `## Text` and `### Text` in one document, `find_heading(text, "Text")` (bare form) → `AmbiguousHeading` with `n == 2` — **a regression test on the same guard, not a second killer**: `duplicate-heading-takes-first`'s one `test` key is `tests/test_h_mad_doc_block_exec.py::test_duplicate_headings_refuse`, and this bare-form test exercises that guard through the other input form (design v1.83 matrix, impl-plan audit v25). It is the deliberate tightening over the old `re.search` first-match (design §Scanning; both live `titled_section` targets in `h-mad/SKILL.md` measured unique, so no caller acquires the refusal).
- [ ] AC-1.8 (bounder's own contract) `test_bounder_ignores_a_heading_inside_a_tilde_fence`, `test_bounder_ignores_an_indented_literal_fence`, `test_bounder_from_an_offset_inside_a_fence` (`start` inside an open fence; a fenced `#` after it does not end the section), `test_bounder_offset_after_a_marker_run_on_a_non_closing_line` (`start` immediately after the three backticks of a ```` ```trailing ```` body line; the next fenced `#` still does not end the section), `test_fence_events_trace_on_every_hostile_fixture` (exact event trace — kind, marker, run, indent, info, candidate, level AND the `start`/`end` offsets of every line, on LF and CRLF copies of each fixture — over: balanced and unbalanced four-backtick, tilde-quoted backtick, backtick-in-info, indented literal, trailing-text closer, offset-inside-a-fence), `test_extract_has_no_fence_state_of_its_own` (source assertion on marker-run **recognition**, **parsing the source of `h_mad_doc_block_exec.py` only** — the file scope of the Conventions invariant, and the assertion reads no other file: the literals ```` ``` ```` and `~~~`, the run-length regex, any `in_fence` toggle, and the ATX heading regex (a `#{1,6}` pattern or any `startswith("#")` test) appear in exactly one function body, `_fence_events`; consumers may read `_FenceEvent.kind`/`.marker`/`.run`/`.indent`/`.info`/`.candidate`, and `extract` selects on `.candidate`, never on `.marker`).
- [ ] AC-1.8 (the wire) `test_docsections_delegates_to_the_authoritative_bounder` (WIRE-PIN, in `test_docsections.py`, scaffold above): on the fenced fixture `titled_section` records exactly one `find_heading` call with `(text, heading)` and one `fence_aware_end` call with `(text, start, level)`, and `section_from` records one `fence_aware_end` call with `(text, offset, level)` on the `sys.modules` fake; its RED reason is the assertion on the call record, never an import error.
- [ ] AC-1.8 `test_titled_section_ignores_a_heading_inside_a_fence` (in `test_h_mad_doc_block_exec.py`, function-local `import docsections`): a document whose requested heading first appears quoted inside a ```` ``` ```` fence and then for real — `titled_section(doc, heading)` (bare form, `titled_section`'s contract) returns the real section's body (the old `re.search` at `h-mad/tests/docsections.py:53`, inside `titled_section` (`:45`), picked the fenced copy).
- [ ] AC-1.8 `test_docsections_has_no_second_bounder`: the source of `docsections.py` defines no function named `_fence_aware_end` and contains no marker-run scanning (the same source predicate as `test_extract_has_no_fence_state_of_its_own`, applied to that file).
- [ ] AC-1.8 `test_docsections_imports_when_collected_alone`: `subprocess.run([sys.executable, "-m", "pytest", "h-mad/tests/test_docsections.py", "-q"], cwd=REPO_ROOT)` exits 0 (nothing but `docsections.py` itself puts `h-mad/scripts` on `sys.path` in that run); `test_docsections_imports_from_an_unrelated_cwd`: `subprocess.run([sys.executable, "-c", "import docsections"], env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "h-mad" / "tests")}, cwd=tmp_path)` exits 0. Both live in `test_h_mad_doc_block_exec.py`, which never imports `docsections` at module level.
- [ ] AC-1.8 the existing `test_docsections.py` tests pass unchanged, and the shared bounder handles the unbalanced four-backtick case the old toggle got wrong (`test_docsections_unbalanced_four_backtick_fence`, in `test_h_mad_doc_block_exec.py`, calling `docsections.titled_section` on the fixture through a function-local `import docsections`: a ```` ```` ```` opener followed by a ```` ``` ```` line and a `# comment` at column 0 — the toggle ends the section at the comment; the bounder does not).
- [ ] AC-1.9 `test_index_zero_refuses`: `select(blocks, 0)` and `select(blocks, -1)` raise `BadIndex` carrying the value, and no lookup happened (the blocks list may be empty).
- [ ] AC-3.7 `test_unknown_info_key_refuses` (`shell=fish`, `mode=x` → `BadInfoString` with that token) and `test_duplicate_info_tokens_refuse` (`hmad:exec hmad:exec`, `shell=strict shell=plain` → `BadInfoString` naming the repeated token); `test_untagged_fence_info_string_is_never_inspected` (` ```bash --frozen ` untagged raises nothing).
- [ ] AC-3.12 `test_invalid_utf8_document_is_unreadable`: a document file containing byte `0xff` → `DocUnreadable` (and, once Task 4 lands, `UNREADABLE reason=doc_unreadable` on the CLI — the CLI half is added in Task 4).
- [ ] `docsections.json` reports `ALL_CAUGHT` with eight rows, each with a `test` key, under `target_command` (`docsections-heading-lookup-reverted` is killed by the WIRE-PIN's empty `find_heading` record, `find_heading` itself untouched); under `docsections-delegation-reverted` the WIRE-PIN fails and **every** other test stays green — all of `test_docsections.py`'s pre-existing tests and all of `test_h_mad_doc_block_exec.py`, the source guard `test_docsections_has_no_second_bounder` and the two docsections-side hostile tests `test_docsections_unbalanced_four_backtick_fence` and `test_titled_section_ignores_a_heading_inside_a_fence` included (the mutation's `test` key is the WIRE-PIN); under `docsections-local-bounder-restored` the source guard goes red (its `test` key), as do the WIRE-PIN and the two hostile tests.

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
matrix and adding one would put this document's total at 82 against a matrix of 81. What stands in
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
`test_docsections_has_no_second_bounder` and the two docsections-side hostile tests included; the
mutation's `test` key stays the WIRE-PIN. The local-restore revert is the separate eighth row,
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
regex is built. Otherwise: an empty key raises `BadSubstArg("")`; if any key is a substring of
another, raise `OverlappingSubstitution(pairs)` where `pairs` is the sorted list of unordered
`(shorter, longer)` tuples and the CLI's `keys=` counts **distinct keys implicated**; counts are
taken on the original `block.text` (`text.count(key)` per key); every key with count 0 is
collected **in the map's insertion order** and, if any, `MissingSubstitution(keys)` is raised;
replacement is one simultaneous pass — `re.sub("|".join(map(re.escape, keys)), lambda m: subs[m.group(0)], text)` —
so replaced text is never re-scanned and the result is independent of map order.

**Code structure**:
```python
# raises BadSubstArg, MissingSubstitution, OverlappingSubstitution — defined in Task 1
# __all__ += ["substitute"]
def substitute(block: Block, subs: Mapping[str, str]) -> tuple[Block, dict[str, int]]: ...
```

**Acceptance Criteria** (nine tests):
- [ ] AC-2.1 `test_path_substitution_replaces_the_key`: `{"~/.claude/skills/h-mad/scripts/h_mad_audit_gate.py": "/tmp/x y/gate.py"}` on a block containing the key yields text with the value (a path with a space) and count 1.
- [ ] AC-2.2 `test_absent_key_refuses`: a key not in the block → `MissingSubstitution` with `keys == [key]`; `test_empty_substitution_map_is_a_no_op`: `substitute(block, {})` returns an equal `Block` that is not the same object and `{}`.
- [ ] AC-2.3 `test_two_missing_keys_are_listed_in_map_order`: `{"B": "1", "A": "2"}` both absent → `keys == ["B", "A"]`.
- [ ] AC-2.4 `test_metacharacter_key_is_literal`: key `a.[b]*` replaces only the literal occurrence.
- [ ] AC-2.5 `test_multi_occurrence_count_equals_replacements`: a key occurring 3 times → count 3 and 3 replacements.
- [ ] AC-2.6 `test_value_containing_another_key_is_not_rescanned`: `{"A": "B", "B": "C"}` and `{"B": "C", "A": "B"}` on `A B` both yield `B C` with counts `{"A": 1, "B": 1}`.
- [ ] AC-2.7 `test_overlapping_keys_refuse`: keys `a`, `ab`, `abc` → `OverlappingSubstitution` with `pairs == [("a","ab"),("a","abc"),("ab","abc")]` and three distinct keys implicated.
- [ ] AC-2.8 `test_empty_key_is_refused_by_the_api`: `substitute(block, {"": "v"})` → `BadSubstArg` with `raw == ""`.

**Mutation rows added here**: `missing-key-silently-skipped`, `overlap-resolved-by-order`,
`replacement-sequential`, `empty-map-not-short-circuited`, `empty-key-accepted-by-api` — 5 rows.

**Dependencies on other tasks**: Task 1 (for `Block`).

**Expected RED split**: all nine tests fail with `AttributeError` (`substitute` absent; its three
exceptions already exist from Task 1); expected passing = 0; the Task 1 tests are regression guards and stay green.

**RED gate**: `hmad-dispatch run --timeout 600 -- python3.11 -m pytest tests/test_h_mad_doc_block_exec.py -q` before any production code — the nine new tests fail with `AttributeError` and every Task 1 test still passes. Judge it on the pytest summary, never on `$?` alone, and keep the recorded output beside the task as the 5d dispatch's `--out` file; `rc=124` is the wrapper's expiry, not a RED result. This is what `h_mad_assemble_tdd.py --phase red` dispatches, with `--test-path` set to the file named above, `--expect-fail` and `--expect-pass` set to the counts this split states for a new-behaviour task and omitted for a wiring task (Tasks 1 and 5 state their RED in prose, as the assembler allows), `--out` the recorded report kept beside the task, and `--timeout 600`.

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
(a `Popen` `OSError` records `LaunchFailed("spawn", err)`). `communicate(timeout=timeout)`; on
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
`from pending` (so `__cause__` is the pending `BlockTimeout`/`LaunchFailed` when there is one, else
`cleanup_error`); elif `pending is not None` → raise it; else return
`RunResult(rc=proc.returncode, stdout=stdout, stderr=stderr, shell=block.shell)`. `run_block` never substitutes.

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
through the CLI; the twelve that inject a fault are marked `(in-process, injected: ` + the seam`)` so the
transport split in the Conventions is visible per test — eight of the twelve patch one of the seven
module-level seams, and four use the instance-level `Popen` wrapper the Conventions describe: the
three `stage=collect` tests and `test_wait_after_kill_is_bounded`. **Every test that patches
`dbe.shutil.rmtree` binds `real_rmtree = shutil.rmtree` BEFORE `monkeypatch.setattr(dbe.shutil, "rmtree", fake)`**
— `dbe.shutil` is the process-global module, so without the binding the teardown would call the
fake — **and removes a retained cwd with `real_rmtree(cwd)` in its `finally`**, the same pattern
as AC-4.6's `real_killpg`; the five such tests are named with `real_rmtree` below):
- [ ] AC-3.1 `test_block_runs_in_the_temp_cwd`: a `pwd` block reports a directory that is neither the repo root nor the document's directory and is gone afterwards.
- [ ] AC-3.2 `test_block_leaves_the_working_tree_untouched`: a block that creates a file leaves `git status --porcelain` byte-identical.
- [ ] AC-3.3 `test_unset_variable_fails_under_strict`: `echo $UNSET_X` → rc ≠ 0 strict, rc 0 plain.
- [ ] AC-3.4 `test_bare_exit_in_plain_mode_returns_rc`: `exit 3` under `shell=plain` → `rc == 3`, and the test process is alive.
- [ ] AC-3.5 `test_pipefail_strict_vs_plain`: `false | true` → rc ≠ 0 strict, 0 plain.
- [ ] AC-3.6 `test_streams_are_separate_str`: stdout/stderr unmerged; `é` round-trips; `printf '\xff'` yields U+FFFD.
- [ ] AC-3.11 `test_preamble_binds_a_variable_and_leaves_text_unchanged`; `test_preamble_and_substitution_compose` (preamble + a substituted key: the executed text carries the value); `test_preamble_without_trailing_newline_still_precedes_the_block`.
- [ ] AC-3.12 `test_failing_preamble_is_visible_as_the_combined_rc`: preamble `false` under strict → rc ≠ 0 and its stderr.
- [ ] AC-3.13 `test_cwd_mode_is_0700_under_hostile_umask`: with `os.umask(0o777)` around the call (restored in `finally`), a block running `stat -f %Lp .` (darwin) / `stat -c %a .` (GNU) prints `700`; `test_chmod_failure_is_a_verdict_and_removes_the_cwd` (in-process, injected: `os.chmod` injected to raise → `LaunchFailed("mkdtemp")` and the created directory is gone); `test_chmod_rollback_failure_is_cleanup_failed` (in-process, injected: `os.chmod` and `shutil.rmtree` both injected → `CleanupFailed` whose `__cause__` is the `LaunchFailed`; `real_rmtree` bound before the patch removes the retained cwd in `finally`); `test_no_mktemp_invocation_in_source`.
- [ ] AC-3.14 `test_cleanup_failure_is_reported` (`mkdir keep && chmod 000 keep` → `CleanupFailed` with `cleanup_error` a `PermissionError`; skipped when `euid == 0`; the test `chmod 700`s and removes the tree in its `finally`); `test_cleanup_failure_carries_the_os_error` (in-process, injected: `rmtree` injected to raise; `real_rmtree` bound before the patch removes the retained cwd in `finally`); `test_cleanup_readback_catches_silent_retention` (in-process, injected: `rmtree` injected as a no-op; `real_rmtree` bound before the patch removes the retained cwd in `finally`); `test_cleanup_error_after_successful_removal_is_still_a_failure` (in-process, injected: the fake calls `real_rmtree` — bound before the patch — then raises; `finally` calls `real_rmtree` under `ignore_errors=True` since the tree is already gone); `test_cleanup_failure_outranks_timeout_injected` (in-process, injected: `rmtree` raising under `sleep 300`, `timeout=1` → `CleanupFailed`, `__cause__` is the `BlockTimeout`, `cleanup_error` is the injected error, cwd read back present, removed in `finally` by `real_rmtree`, bound before the patch); `test_cleanup_failure_outranks_timeout` (real `chmod 000` fixture, skipped under root); `test_normal_run_reads_back_absent`.
- [ ] AC-4.6 `test_mkdtemp_failure_is_a_verdict` (in-process, injected: `tempfile.mkdtemp` injected → `LaunchFailed("mkdtemp")`, nothing to clean); `test_spawn_failure_is_a_verdict` (`PATH` = empty dir → `LaunchFailed("spawn")`, cwd gone); `test_reap_failure_is_a_verdict_within_the_drain_bound` (in-process, injected: `os.killpg`): `real_killpg = os.killpg` bound **before** `monkeypatch.setattr(dbe.os, "killpg", fake)`; `fake` records the pgid and raises `PermissionError`; `Popen` wrapped in a recording pass-through; `sleep 300` under `timeout=1` → `LaunchFailed("reap", pgid=proc.pid)` raised within `1 + 2 * DRAIN_SECONDS + 2` s; teardown in `finally`: `real_killpg(pgid, signal.SIGKILL)`, `recorded.wait()`, then assert `real_killpg(pgid, 0)` raises `ProcessLookupError`.
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
`tests/test_h_mad_doc_block_exec.py::test_poll_oserror_is_launch_failed_collect`) — 24 rows.
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

**Expected RED split**: every test in this task fails (`run_block`, `RunResult` and
`_validate_timeout` absent; the four exceptions already exist from Task 1)
except `test_no_timeout_invocation_in_source` and `test_no_mktemp_invocation_in_source`, which are
**regression guards** that pass from the first run (the source scan finds nothing in a module that
does not yet spawn); expected passing = 2; Tasks 1–2 tests stay green.

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
inode this call created is already gone or renamed away. **That identity check is a policy
constraint, not a mutation-backed guard, and carries no test by construction**: concurrent
replacement of the caller's own artifact path between the two arms of one call is outside the
threat model, its mismatch branch cannot be reached without a ninth seam interposed between two
syscalls, and adding a seam for a stated non-goal is not warranted. Where the identity matches,
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
15 field names. **Of this document's 26 rendering slots — those 15 head field names plus the 11
`DETAIL_KEYS` values — exactly 19 dynamic values are rendered through one module-level renderer,
`_field(value)`, and the other 7 are rendered bare by construction** (design v1.75/v1.78/v1.80,
design audits v67, v70 and v72; impl-plan audit v23). The 7 bare ones are `rc`, `blocks`, `count`,
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
**The 19 quoted slots, enumerated** (the seven bare ones are listed above and are not repeated):
the head fields `heading=`, `index=`, `value=`, `arg=`, `message=`, `key=`, `seconds=`, `path=`, and every one
of the 11 detail values — `missing_key:`, `overlap:`, `duplicate_key:`, `os_error:`, `pgid:`,
`written:`, `failed:`, `skipped:`, `verify:`, `stream:`, `leftover:`. 7 + 19 = 26, the slot count
this section derives. `seconds=` and `pgid:` are helper-produced numbers, and impl-plan v1.22 left
open whether they should be bare; design v1.79 **settled** it by making the bare list exhaustive,
so both are quoted and no exemption is pending.
**This document's own constraint**, re-derived at `35698f9`, with the corresponding design rows
reached **by name, never by line and never by a claim about their content**, under the Conventions
rule above. The `BAD_INFO` head is `BAD_INFO key="<k>"`, **quoted**: `key=` is the offending
info-string token — document-controlled — and is not among the seven exempt fields; the design's
verdict-table row is located with
``grep -n '^| `DOCBLOCK: BAD_INFO key=' docs/02-design/features/doc-block-exec.design.md``
(one hit, verified at `6f0ee85`). The `SUBST_OVERLAP` detail line is `overlap: "<a>" "<b>"` with **both** halves
quoted, because both elements are caller keys; its row is located with
``grep -n '^| `DOCBLOCK: SUBST_OVERLAP keys=' docs/02-design/features/doc-block-exec.design.md``
(one hit, verified at `6f0ee85`). Impl-plan v1.24 flagged those two rows as bare and half-quoted and **design
v1.81 answered it** — located with
``grep -n 'both halves of `overlap:`' docs/02-design/features/doc-block-exec.design.md``
(one hit, verified at `6f0ee85`) — so the flags were withdrawn at v1.35. The three `design.md:` line numbers this paragraph carried
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
enumerate all eleven. `StreamWriteFailed`'s `written`/`skipped` lists are joined with a space
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
`_SCANNED`'s eight sources against this feature's own file list**: `h-mad/SKILL.md` is the **only**
file this feature edits that is a member — `h-mad/tests/docsections.py`,
`h-mad/tests/test_*.py` and `h-mad/tests/mutation-specs/*.json` are all outside `_SCANNED` (it
reaches `SKILL.md`, `invariants.base.md`, `invariants.example.md`, `audit-prompt.template.md`,
`references/*.md`, `scripts/*.sh`, `scripts/*.py` and `hooks/*.sh`, and `tests/` is in none of
them), and the feature adds nothing under `references/`, `hooks/` or `scripts/*.sh`. The live risk
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
DETAIL_KEYS: tuple[str, ...] = ("missing_key:", "overlap:", "duplicate_key:", "os_error:", "pgid:",
                                "written:", "failed:", "skipped:", "verify:", "stream:",
                                "leftover:")   # 11

def _field(value: object) -> str:
    """The ONE renderer the 19 dynamic values pass through (the 7 bare fields never reach it):
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
- [ ] AC-3.10 (subprocess) `test_stream_path_under_a_regular_file_refuses` (parent is a regular file → `stream_path_unwritable`, exit 2, no traceback, side-effect block left nothing); `test_stream_path_char_device_refuses` (subprocess, `--stdout /dev/null`: the reservation's first arm fails `O_EXCL` with `FileExistsError`, the second arm opens it under `O_WRONLY|O_APPEND|O_NONBLOCK` successfully, and the `fstat` then reports a **character device** — `S_ISREG` false — so the descriptor is closed and refused: `UNREADABLE reason=stream_path_unwritable`, exit 2, and a side-effect block left nothing. Measured 2026-09-03: `/dev/null` opens under those flags and `stat.S_ISREG` is `False`, `S_ISCHR` `True`); `test_stream_path_fifo_without_reader_refuses_bounded` (`os.mkfifo` path, CLI run with `timeout=5` in the test's `subprocess.run`, refusal within 1 s); `test_stdout_survives_a_failed_stderr_reservation` (pre-existing stdout byte-identical; a created stdout unlinked); `test_rollback_unlink_failure_reports_leftover` (in-process main, injected: `os.unlink`): `--stdout` is a **fresh** path under `tmp_path` so the first arm's `O_EXCL` succeeds and `created` is True, `--stderr` is a path **under a regular file** so the second arm fails with a real `ENOTDIR` and no injection is needed to reach the rollback; `monkeypatch.setattr(dbe.os, "unlink", fake)` where `fake` raises `PermissionError`, bound after `real_unlink = os.unlink` so the test's own `finally` can remove the leftover the injection deliberately created — the same rule as `real_rmtree` and `real_killpg`, and note that under this test the file is left behind **by design**, which is the state being asserted. Asserts `UNREADABLE reason=stream_path_unwritable`, exit 2, a `leftover:` detail line naming the stdout path exactly, that stdout path present and **empty** (zero bytes — the rollback closed the handle before the unlink was attempted, so nothing was written), and no traceback.
- [ ] AC-4.1 (subprocess) `test_ran_line_and_exit_zero_with_nonzero_rc`: `DOCBLOCK: RAN rc=3 blocks=1 shell=plain`, exit 0 — all three fields are helper-constrained and therefore bare, so this line is unchanged by the quoting rule.
- [ ] AC-4.1/4.3 `test_dynamic_field_cannot_forge_a_token` (in-process main, no injection): `--heading 'x rc=0'` on a document without that heading → the `NOT_FOUND` line. The assertion is a **parse under the line grammar**, not a substring check: split the tail after `DOCBLOCK: NOT_FOUND` into fields, each `<key>=<bare>` or `<key>="<json-string>"`, and assert the field map is exactly `{"heading": "x rc=0"}` — one field, its value the argument verbatim, and **no `rc` field at all**. A substring check would pass under the mutant (the text ` rc=0` is present either way), so the parse is what discriminates. This is the AC-4.3 promise stated positively: a cannot-judge line carries no `rc`, and a caller cannot manufacture one.
- [ ] AC-4.1 `test_malformed_invocation_is_a_verdict` (in-process main, no injection): two malformed invocations, each its own `main(argv)` call and `capsys.readouterr()` — an **unknown option** (`--nope`) and a **missing option value** (`--heading` with nothing after it). Each yields exactly one `DOCBLOCK: BAD_ARGS message="<the parser's own text>"` line, **exit 0**, and **no usage text on stdout**. The no-usage clause is what discriminates `argparse-error-unrouted`: with the `error()` override removed argparse raises `SystemExit(2)` and prints its usage block, so a test asserting only the exit code could still pass if a caller mapped 2 onward.
- [ ] AC-4.1 `test_unicode_line_separators_cannot_split_a_verdict_line` (in-process main, no injection): a `--heading` carrying U+0085, U+2028, U+2029 and U+007F on a document without that heading → the `NOT_FOUND` line. Assert that `capsys` stdout **`.splitlines()`** holds exactly **one** line starting with `DOCBLOCK:` — `.splitlines()` rather than `.split("\n")` is the whole point, since it is the splitter that breaks on the first three — and that all four characters appear inside the quoted `heading=` value as the escapes `\u0085`, `\u2028`, `\u2029` and `\u007f`. Measured before writing: without the second pass the same line `.splitlines()` into **four** pieces, with it into **one**, so this test is red against a `json.dumps`-only `_field` and green against the specified one.
- [ ] AC-4.1 `test_newline_in_dynamic_fields_cannot_forge_a_verdict_line` (in-process main; cases (1) and (2) need no injection, case (3) is **injected: `os.unlink`**, the same module seam AC-3.10's rollback test uses — `capsys` holds the lines; in-process because the assertion is on the emitted text, and three refusal paths are exercised in one test, each with its own `main(argv)` call and its own `capsys.readouterr()`): (1) `--heading` = `"x\nDOCBLOCK: RAN rc=0 blocks=1 shell=strict"` on a document without that heading → `NOT_FOUND`; (2) a `--subst` argument whose key and value each carry a `\n` → `SUBST_MISSING` when the key is well-formed but absent from the block, and `BAD_SUBST` for the malformed spelling, whose `arg=` then carries the raw argument; (3) the `leftover:` slot, built exactly as AC-3.10's `test_rollback_unlink_failure_reports_leftover` builds it, with the newline moved into the **created** artifact's name: `--stdout` is a **fresh** path under `tmp_path` whose **file name contains `\n`** (a newline is a legal POSIX file-name byte — verified on this platform: `os.open` with `O_CREAT|O_EXCL` creates it and `os.path.lexists` finds it), so the **first** arm succeeds and `created` is True; `--stderr` is a path **under a regular file**, so the **second** arm fails with the real `ENOTDIR`; `os.unlink` is injected to raise `PermissionError` exactly as AC-3.10 does, so the rollback read-back finds the created file still present → `UNREADABLE reason=stream_path_unwritable` carrying `leftover:` with the **escaped** name. **The newline must be on the created path, not on a first-arm failure** (impl-plan audit v19): a `--stdout` under a regular file fails the first arm, creates nothing, and therefore has no leftover to report at all, so that spelling would fail against a correct implementation rather than against the mutant. For each of the three, three assertions: **exactly one** line of the captured stdout starts with `DOCBLOCK:`; **no** line equals the forged `DOCBLOCK: RAN rc=0 blocks=1 shell=strict` string; and the payload appears **escaped inside the field's double quotes** — the emitted field is `heading="x\nDOCBLOCK: RAN rc=0 blocks=1 shell=strict"` — one quoted value whose interior holds the two characters `\` and `n` where the newline was, never a real newline. Under `field-escape-removed` **both** the first and third assertions fail on **all three** cases: the raw newline splits each verdict into two physical lines, and the escaped payload is absent. The third is stated separately because it does not depend on how a consumer splits lines, so the kill survives any change in that assumption.
- [ ] AC-4.2 `test_verdict_table_exit_codes`: parametrised over the 23 `VERDICT_TABLE` heads with one producer each — a subprocess producer for the 17 heads a real input or real fault yields (`RAN`, `NOT_FOUND`, `AMBIGUOUS`, `AMBIGUOUS_HEADING`, `BAD_INDEX`, `BAD_TIMEOUT`, `BAD_SUBST`, `BAD_ARGS` via an unknown option, `SUBST_MISSING`, `SUBST_OVERLAP`, `BAD_INFO`, `TIMEOUT`, `LAUNCH_FAILED stage=spawn` via an empty `PATH`, `UNREADABLE reason=doc_unreadable`, `UNREADABLE reason=preamble_unreadable`, `UNREADABLE reason=stream_paths_alias`, `UNREADABLE reason=stream_path_unwritable`) and an in-process `main(argv)` producer for the 6 that need a fault injection (`CLEANUP_FAILED` via `shutil.rmtree` — `real_rmtree` bound first, retained cwd removed in `finally`, `LAUNCH_FAILED stage=mkdtemp` via `tempfile.mkdtemp`, `LAUNCH_FAILED stage=reap` via `os.killpg`, `LAUNCH_FAILED stage=collect` via the instance-level `Popen` wrapper of `test_communicate_oserror_is_launch_failed_collect` — the same `echo hi` block, the same `real_killpg` teardown, `UNREADABLE reason=stream_write_failed` via `_final_write`, `UNREADABLE reason=stream_close_failed` via `_close_stream`); either way the assertion compares the produced exit code (process exit or `main`'s return) with `VERDICT_TABLE[head]` and the emitted line starts with `DOCBLOCK: ` followed by the head; **for the `LAUNCH_FAILED stage=reap` and `LAUNCH_FAILED stage=collect` producers the captured output also carries a quoted `pgid: "<n>"` detail line** (the two stages on which `LaunchFailed` sets `pgid`; this is the only place `pgid:` is asserted at the CLI, the design's AC-4.6 row expecting it there); one assertion that `set(params) == set(VERDICT_TABLE)`; `test_every_docblockerror_subclass_has_a_verdict` (walk `DocBlockError.__subclasses__()` recursively and assert **membership by class**: each subclass is a `_VERDICT_FOR` key. **The walk instantiates nothing** — it constructs no exception and therefore imposes no constructor shape on any subclass, so the ones with required arguments keep them (design v1.80, design audit v72). Head-to-`VERDICT_TABLE` agreement is proved by `test_verdict_table_exit_codes` above, which produces each of the 23 heads for real; this test's job is only that no subclass is missing a renderer.)
- [ ] AC-4.2 exit propagation (subprocess): `test_cli_exit_zero_propagates` (a document whose section has no tagged fence → `DOCBLOCK: NOT_FOUND`, process exit 0) and `test_cli_exit_two_propagates` (a document containing byte `0xff` → `DOCBLOCK: UNREADABLE reason=doc_unreadable`, process exit 2) — both compare the process exit with `VERDICT_TABLE[head]`, pinning that `sys.exit(main())` propagates `main`'s return value.
- [ ] AC-4.3 (subprocess) `test_no_refusal_carries_rc`; AC-4.4 (subprocess) `test_only_ambiguous_carries_blocks`.
- [ ] AC-4.5 `test_every_emittable_line_has_a_registry_row` (every `VERDICT_TABLE` key and every `DETAIL_KEYS` entry appears as the first backtick token of a row in the SKILL.md entry) and `test_registry_rows_cover_only_emittable_lines` (every row's first token is in that union).
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
`rc-leaked-into-refusal`, `field-escape-removed` (`_field` returns its input unchanged, so a
newline inside a heading, key, path or OS-error text starts a second `DOCBLOCK:` line; killed by
`tests/test_h_mad_doc_block_exec.py::test_newline_in_dynamic_fields_cannot_forge_a_verdict_line`.
Under the mutant each of that test's three cases emits its raw newline — inside `heading=`, inside
`missing_key:`, and inside the `leftover:` path — so each verdict becomes **two physical lines** and
the exactly-one-`DOCBLOCK:`-line assertion fails on all three; the escaped-payload assertion fails
too, which is what keeps the kill from depending on how a consumer happens to split lines. It is
the only test in this document that asserts on an escaped payload — every other test uses values
with no control characters, so all of them stay green under it),
`c1-escape-removed` (`_field`'s second pass is removed, leaving only `json.dumps`, so U+0085,
U+2028, U+2029 and U+007F come through literal and a heading carrying them splits one verdict
into four lines; killed by
`tests/test_h_mad_doc_block_exec.py::test_unicode_line_separators_cannot_split_a_verdict_line`.
It is discriminated from `field-escape-removed` by the character class each one frees: that row
frees `\r`/`\n`, which `json.dumps` escapes anyway, and this one frees exactly the four
`json.dumps` leaves behind, so neither test goes red under the other's mutant),
`field-quoting-removed` (`_field` still escapes control characters but emits the value **bare**,
without the surrounding quotes, so `--heading 'x rc=0'` parses to two fields and yields an `rc`
field; killed by `tests/test_h_mad_doc_block_exec.py::test_dynamic_field_cannot_forge_a_token`.
It is discriminated from `field-escape-removed` in both directions: this row keeps the escaping, so
the newline test's one-line assertion still holds under it, and that row keeps the quoting, so this
test's parse still yields exactly one `heading` field under it),
`rollback-leftover-unreported` (the rollback's
`os.path.lexists` read-back is removed, so a first-reservation file that the failed unlink left
behind is never reported and the `stream_path_unwritable` verdict carries no `leftover:` line;
killed by `tests/test_h_mad_doc_block_exec.py::test_rollback_unlink_failure_reports_leftover`,
whose other assertions — the verdict, the exit code, the file's presence — all still hold under the
mutant, so the `leftover:` line is the only thing that discriminates it),
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
`test_stream_write_failure_after_the_run_is_a_refusal`) — 27 rows.
**Two AC-3.10 rows were re-bound this cycle** (design v1.82, design audit v73), because the FIFO
fixture cannot kill both: measured 2026-09-03, a reader-less FIFO opened `O_WRONLY|O_APPEND|O_NONBLOCK`
fails at `os.open` with **ENXIO** and never reaches the `S_ISREG` check, so it exercises the
blocking-open guard and nothing else. `nonregular-stream-accepted` (the `S_ISREG` check dropped)
is therefore killed by the new `tests/test_h_mad_doc_block_exec.py::test_stream_path_char_device_refuses`,
whose `/dev/null` **does** open and **does** reach the check; `stream-open-blocking` (the
`O_NONBLOCK` dropped from the second arm) keeps
`tests/test_h_mad_doc_block_exec.py::test_stream_path_fifo_without_reader_refuses_bounded` as its
sole killer. Each row now has one killer that actually reaches its guard.
`cli-empty-key-delegated` is discriminated from Task 2's `empty-key-accepted-by-api`, which is NOT one of the 27
above, by which side is mutated: that row removes `substitute`'s own guard and is killed by the API
test, this one removes `main`'s and is killed by the CLI test, and neither killer touches the
other's code path. With Tasks 1, 2, 3 that is
25 + 5 + 24 + 27 = **81 rows**, split **80 of the helper's source and 1 of `h-mad/SKILL.md`**.
**The split is derived from the mechanism column of the design's helper matrix, never copied from
any document's prose** — the prose is what was wrong. Derivation, run at `1861157`: over the data rows
of the design's helper-spec mutation matrix in `docs/02-design/features/doc-block-exec.design.md`
— the table whose second column heading is "guard it removes (mechanism)", located with
`grep -n 'guard it removes' docs/02-design/features/doc-block-exec.design.md` (one hit,
verified at `6f0ee85`) — count those whose mechanism column names
`SKILL.md` as the file the harness edits — **81 data rows, exactly 1 of them**
(`registry-row-removed` — this document's own row list annotates it, and only it, as targeting
`h-mad/SKILL.md`; the corresponding design row is located with
``grep -n '^| `registry-row-removed`' docs/02-design/features/doc-block-exec.design.md``, one
hit, verified at `6f0ee85`), so 80 + 1.
**`detail-line-undocumented` is a helper-source mutation, not the second `SKILL.md` row** — it
renames an emitted detail line **in the helper** (`missing_key:` → `absent_key:`) so that an
emittable line has no registry row (its design row is located with
``grep -n '^| `detail-line-undocumented`' docs/02-design/features/doc-block-exec.design.md``, one
hit, verified at `6f0ee85`). It is `registry-row-removed`'s partner **by
AC**, both serving AC-4.5's bidirectional pin, **not by file**; reading the pair as "the two
`SKILL.md` rows" is exactly how the 79 + 2 miscount arose, here and in the design. The annotation
in the row list above already says so — only `registry-row-removed` carries "(targets
`h-mad/SKILL.md`)" — so this line and that list now agree (impl-plan audit v34, plan-author).
No design version is pinned here on purpose: a `matching design v1.NN` claim is the moving-value
class the header rule covers, and the derivation above is the check that replaces it.

**Dependencies on other tasks**: Tasks 1, 2, 3.

**Expected RED split**: every test in this task fails (`main` absent → the subprocess tests see the
CLI exit 1 with a traceback, the in-process `main` tests and the API tests raise `AttributeError`); expected passing = 0; Tasks 1–3 tests are
regression guards and stay green. `doc_block_exec.json` must report `ALL_CAUGHT` over all 81 rows
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
  `h_mad_audit_gate.py`. That is the same predicate the consumer's pre-migration `:270` extraction
  uses (`[b for b in _bodies if "h_mad_audit_gate.py" in b]`) and the one every `wire-revert-*`
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
The `h-mad/tests/test_h_mad_collect_report_docs.py:412` text scan — the `re.findall` inside `test_exec_codex_dispatch_carries_out_log_and_timeout` (`:403`) — is untouched (every later `:412` in this document is that same line in that same file). Write `doc_block_exec_wire.json` (`command` =
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
- [ ] AC-6.1 `test_exactly_one_tagged_fence_in_the_tree` (in `test_h_mad_doc_block_exec.py`): opening fences carrying `hmad:exec` equal exactly 1, counted with the module's own `_fence_events` over **`*.md` files only** — a sweep this AC states outright rather than reaching by reference: `Path(REPO_ROOT).glob('*/**/*.md')`, then `rel = p.relative_to(REPO_ROOT)`, keeping `rel.parts[0] in ('h-mad', 'handoff')`, dropping any path with `'archive'` in `rel.parts`, **and dropping any path with a dot-directory component** (`any(part.startswith('.') for part in rel.parts)`). **Two independent clauses, two independent defects, both measured** (impl-plan audit v34 and the design v1.93 back-propagation). *The rebase*: this document's `REPO_ROOT` is **absolute** (`REPO_ROOT = Path(__file__).resolve().parents[2]`, Conventions), while the plan's census walks `Path('.')` from the repository root, so the transcribed `p.parts[0] in ('h-mad', 'handoff')` read `parts[0] == '/'` here and selected **nothing** — the AC would still have predicted 0 correctly at RED and could never have reached 1 at GREEN. `'archive'` is rebased with it, or it would test the components of the absolute prefix. *The dot-directory exclusion*: without it the sweep also walks the five gitignored `.pytest_cache/README.md` artifacts that exist on any tree where pytest has run — build output, not documentation, and not something a cardinality-1 guard should count. **The check is a RELATION, not three integers** — the corpus is a growing tree and every absolute count written here is stale within a day (this AC carried 0/30/25 through v1.36; at `335f535` the same three commands print 0/35/30, moved by this session's own `h-mad/agents/*.md` commits). The three invariants, each re-derived at `335f535` from the repository root: (i) the **absolute base** keeps **zero** files — `p.parts[0]` is `'/'`, never `'h-mad'` — which is why `rel` is load-bearing; (ii) the `rel`-rebased, dot-excluded set is **identical** to `git ls-files -- h-mad handoff | grep '\.md$' | grep -v '/archive/'` (symmetric difference **empty**), an agreement of today's tree rather than of the definitions; (iii) dropping the dot clause adds **exactly** the five gitignored `h-mad/.pytest_cache/README.md`, `h-mad/scripts/.pytest_cache/README.md`, `h-mad/tests/.pytest_cache/README.md`, `handoff/.pytest_cache/README.md` and `handoff/tests/.pytest_cache/README.md` — nothing else. Re-run to check, and compare the three against each other rather than against a constant: `python3 -c "from pathlib import Path; R=Path('.').resolve(); print(len([p for p in R.glob('*/**/*.md') if (r:=p.relative_to(R)).parts[0] in ('h-mad','handoff') and 'archive' not in r.parts and not any(x.startswith('.') for x in r.parts)]))"` from the repository root must equal `git ls-files -- h-mad handoff | grep '\.md$' | grep -v '/archive/' | wc -l`; dropping the dot clause must exceed it by exactly the five named paths; and using `p.parts` in place of `r.parts` must print `0`. **Dated example, `335f535`, 2026-09-04**: those four commands printed **30**, **30**, **35** and **0**. **This defect is LATENT, not live** — worth stating precisely, because a 5d implementer must not go looking for a failing test. No `.pytest_cache/README.md` carries `hmad:exec` (re-checked over all five at `335f535`: 0 hits each), so the cardinality-1 assertion passes today and would have passed at Task 5 GREEN on the dot-inclusive sweep too. What is wrong is that the **set the test walks is machine-state-dependent** — the tracked count on a clean clone, five more after anyone has run pytest (30 vs 35 at `335f535`) — so a future tool that drops a generated `.md` under those roots silently enters an assertion that is supposed to be exactly 1. **Which realisation this is, and why it differs from the other**: this feature uses the exclusion in two places and the two are deliberately not the same command. The *measurement* corpus is `git ls-files -- h-mad handoff` filtered to `*.md` with `archive/` excluded — 25 files when it was measured at `1861157`, 30 at `335f535` — because a one-off human measurement has every reason to describe the tracked tree. This AC transcribes the **guard** realisation, the dot-directory exclusion, because a test must still count a tagged fence in an `.md` that has been **written and not yet committed**, which is precisely the accident it exists to refuse and precisely what `git ls-files` would miss. The two agree on this tree and are not the same predicate: re-derived at `335f535`, the dot-excluded glob set and the `git ls-files` set are **identical** (symmetric difference empty, both 30) — an agreement of today's tree, not of the definitions, and it is the definitions the test must implement. **The `*.md` restriction is load-bearing, not tidiness.** (It is no longer stated as "the scope of the census this AC is bound to": reaching a scope by reference imports whatever the referent later becomes, which is how the dot-directory contamination arrived in this AC in the first place, so the sweep is spelled out above instead.) By Task 5, Tasks 1–4 have landed `h-mad/tests/test_h_mad_doc_block_exec.py` under `h-mad/`, and its fixtures carry ` ```bash hmad:exec ` as a column-0 line inside triple-quoted Python strings (AC-1.1's tagged/untagged pair, AC-1.5's section fixtures, AC-1.7's duplicate-heading fixture, AC-3.7's `shell=fish` and `hmad:exec hmad:exec` fixtures). By this feature's own grammar a 0–3-space marker run **is** an opener regardless of the enclosing file's suffix, so an unrestricted sweep counts every one of them and the AC could never pass at GREEN. Worse, the count would not even be the sum of the per-fixture counts: one fixture is a deliberately *unbalanced* four-backtick fence (`test_docsections_unbalanced_four_backtick_fence`), so a whole-file scan of the `.py` carries fence state across fixture boundaries. The scoping rule follows from what `_fence_events` is: a **markdown** scanner whose only inertness rules are markdown ones (a four-backtick fence, a `~~~` fence, a 4-space indent). A Python triple-quoted string is not one of them, so a non-`.md` holder of a fixture is a false positive **by construction**, not an accident of this feature. **Residual, stated exactly**: the sweep does not cover non-`.md` files under the two roots (`.py`, `.sh`, `.json`, `.txt`), `.md` files outside `h-mad/` and `handoff/` (this document and its siblings under `docs/` among them), anything under `archive/`, or anything under a dot-directory — so a tagged fence written into `.pytest_cache/` or any other dot-directory is uncounted, which is the intended trade for not counting build output. The converse is the live edge: **a generated `.md` written under the two roots *outside* a dot-directory IS counted**, correctly — it is then part of the executed documentation surface — but noisily, and if a tool ever starts emitting one this assertion is where it will surface. The guard is "exactly one tagged fence in the executed documentation surface", not "in the repository" — the right scope, because a tagged fence is only ever reachable by a consumer that scans a `.md` doc. **No clearance and no debt against a sibling is stated here** — that is cycle content, not document content (Conventions). What this AC states is its **own** constraint, with the sibling reached by a locator rather than a claim: the dot-directory exclusion is prescribed for **this sweep specifically**, and the design's Test Plan row for AC-6.1–6.6 that carries it is located with `grep -n 'The sweep excludes build output' docs/02-design/features/doc-block-exec.design.md` (one hit, verified at `6f0ee85`). Earlier revisions carried the same scope as three separate assertions about what the design, the spec and the plan currently say; all three are dropped, because this document adopted their scope on its own terms and a sentence describing a sibling's present state expires the moment that sibling is revised. Under this restriction the RED prediction below is true as stated: re-derived at `335f535`, `grep -rn 'hmad:exec' h-mad/ handoff/` returns **0** hits, so before Task 5's SKILL.md edit the `.md` count is zero.
- [ ] AC-6.2 `test_exec_block_scan_performs_no_execution`: it installs a spy over `dbe.run_block` and a recording pass-through over `dbe.subprocess.run`, then **drives the scan by calling `test_exec_codex_dispatch_carries_out_log_and_timeout()` directly** — the `:403` test that owns the `:412` scan, which takes no fixtures and so is callable as a plain function — and asserts both recorders are empty. Calling the existing test rather than re-implementing its body is what keeps `exec-scan-executes`'s anchor valid: the mutant is applied inside that function, so a killer that re-implemented the scan locally would never see it. **This `run_block` spy is the one spy in this document that is NOT a recording pass-through**: it records `(block, kwargs)`, returns `None`, and never calls the real `dbe.run_block`. A pass-through here would execute the exec block from inside the killer itself under `exec-scan-executes`, which is exactly what the row's safety note forbids — the same class of rule as binding `real_rmtree`/`real_killpg` before their patches. **Of the two recorders, the `dbe.run_block` spy is the discriminator and carries the whole kill; the `dbe.subprocess.run` recorder is a belt that `exec-scan-executes` cannot trip**, because `run_block` spawns through `subprocess.Popen` and never through `subprocess.run` (Task 3's code structure). It stays in the assertion as a guard against a *different* mutant — one that reaches for `subprocess.run` directly from the scan — and its emptiness must never be read as evidence about this row. And `test_only_the_exec_scan_hand_rolls_extraction` (exactly one `re.findall(r"```bash` in the file's source, and it is not inside `_gate_block`/`_gate_bash_block`/`_run_recipe`).
- [ ] AC-6.3 the four existing behaviours — `COLLECT: OK` guard before gating, delivered-report `GATE: PASS`, undelivered `report_not_collected` halt without reaching the gate, no shell-killing bare `exit` — still pass, driven through the preamble boundary.
- [ ] AC-6.4 `test_suite_floor_holds` (in `test_h_mad_doc_block_exec.py`): `subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"], cwd=REPO_ROOT, env={**os.environ, "DOCBLOCK_FLOOR_INNER": "1"})` — **from the repository root**, the cwd the baseline was measured in (`python3.11 -m pytest --collect-only -q -p no:cacheprovider | tail -1` → `2748 tests collected`, re-measured 2026-09-04 at commit `b7d0d77`; the same command from `h-mad/` reports 2486, a different rootdir and a different number). **The paired design, plan and spec pin this same 2748 at `e8eaf6f` and this document pins it at `b7d0d77`; that is not drift, and it is deliberate** (impl-plan audit v34, raised by the design author). `b7d0d77` is the single commit after `e8eaf6f`, and the count is **identical** at both: verified at `1861157` by counting `def test_` across every `test_*.py` in the tree at each commit — **2675 at `e8eaf6f`, 2675 at `b7d0d77`, 2675 at `1861157`**, so no test function was added or removed across that span (the 2675/2748 difference is parametrised expansion at collection, which is why the floor is stated as a *collected* count). Each of the four documents names the commit **it actually measured at**, which is the rule the floor exists to enforce — re-pinning this one to `e8eaf6f` would make it claim a measurement it did not run. A reviewer comparing the four should read one number with two honest provenances, not two numbers. **`2748` is the repository-root count and only the repository-root count**: `cwd=REPO_ROOT` in the call above is load-bearing, and `2486` is never a substitute for it — a reviewer who runs the baseline from `h-mad/` gets 2486 and will read the floor as wrong when it is the directory that was wrong (observed, impl-plan cycle 19). **The number is stated with the commit it was measured at, and it is RE-MEASURED at 5c branch time rather than copied from here — the same rule, and the same reason, as the SKILL.md line pins above.** A floor baseline is a count over a tree that keeps growing: 2747 was measured at `6b4df35`, `b59e05e` then added one test (`h-mad/tests/test_h_mad_assemble_audit.py`, verified: that commit adds exactly one test), and against a real 2748 the assertion `≥ 2747 + the module's own collected count + 7` (the tuple as it then stood) silently permitted **one** deletion — a floor that is stale by N tolerates N deletions, and tolerates them invisibly, which is the one failure mode this AC exists to prevent. So the residual is stated exactly: a stale-by-N floor is not a failing test, it is a **weakened** one, and nothing in the suite can detect that. The implementer re-runs both commands at 5c, writes the two numbers with the 5c sha beside them, and uses the repository-root number as the constant; if it differs from 2748 that is expected drift, not a finding. With `DOCBLOCK_FLOOR_INNER=1` making the inner instance of this test skip; asserts the collected count ≥ the 5c-measured repository-root baseline (`2748` at `b7d0d77`) + the collected count of `h-mad/tests/test_h_mad_doc_block_exec.py` alone (a second `--collect-only` from the same cwd) + **`len(tuple)`**, and that **each member of that tuple is present**. **The addend is `len(tuple)`, never a hand-written integer**: a literal is a second authority that drifts against the enumeration beside it — which is exactly how the previous `+ 7` came to disagree with its own list — while `len(tuple)` cannot. The tuple is enumerated in full here because this is a **test**, and a test needs concrete node IDs to assert on; membership, however, is not decided here (see below). The members, as full node IDs relative to the repository root:
`h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_resolves_through_doc_block_exec`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_recipe_runs_through_run_block`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_gate_block_refuses_an_untagged_recipe`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_exec_block_scan_performs_no_execution`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_consumer_calls_the_helper_module_qualified`,
`h-mad/tests/test_h_mad_collect_report_docs.py::test_only_the_exec_scan_hand_rolls_extraction`,
`h-mad/tests/test_docsections.py::test_docsections_delegates_to_the_authoritative_bounder`,
`h-mad/tests/test_h_mad_portable_timeout.py::test_no_document_or_script_emits_a_bare_timeout_command[h_mad_doc_block_exec.py]` and
`h-mad/tests/test_h_mad_portable_timeout.py::test_no_document_or_script_rests_on_an_unconditional_absence_claim[h_mad_doc_block_exec.py]`.
**This document writes no total for that tuple.** The assertion's addend is `len(tuple)` and nothing else; a written total anywhere in *this* document would be a second authority beside the enumeration above, and that is what the fix is. "Seven" was the instance and it went stale the moment a second source of members was noticed; "nine" would go stale the same way the moment this feature adds a second script. **A stated total is not forbidden in general** — it is admissible as a *dated evaluation that names the commit it was evaluated at*, a form no reader can mistake for the contract; what is inadmissible is a bare integer standing where `len(tuple)` stands. This sentence says nothing about what any sibling document contains: the earlier form of it claimed no total was written "here or anywhere", which is a present-tense claim about siblings and so the very class the Conventions rule above forbids (impl-plan audit v36 — the rule caught its own author). **Membership is decided by the spec's rule, and this document does not re-word it** — a rule stated twice in two voices is how the 25/30 corpus contradiction started. The spec's AC-6.4 states it as two sources: nodes added **directly** to a consumer file, plus **one node per glob-parametrised test per new file this feature adds under `h-mad/scripts/`**, the latter required to **pass** rather than merely be counted. Locate it with `grep -n 'One node per glob-parametrised test' docs/01-plan/features/doc-block-exec.spec.md` (one hit, verified at `6f0ee85`); that is the authority, and the enumeration above is this document's application of it to the files Task 1 through Task 5 actually land. **The tuple is therefore re-derived at 5c, not copied from here** — the same rule already stated above for the `2748` baseline, now extended to cover membership: at 5c the implementer re-runs the glob enumeration below against the branch, and for **each** `h-mad/scripts/*.py` file the feature actually landed adds one node per glob-parametrised test over that directory. If the feature lands a second script the tuple grows by two and `len(tuple)` follows it with no edit to the assertion; if it lands none beyond `h_mad_doc_block_exec.py` the tuple is exactly the members enumerated above. That is what makes this fix survive the next increment instead of repeating at it.
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
  and today's `"h_mad_audit_gate.py" in b` filter, wrapping the body as
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
carries two guards the hoisted `_gate_block` does not:
`assert gating, "Second surface must contain a bash block that runs the gate"`
(`h-mad/tests/test_h_mad_collect_report_docs.py:272`) and
`assert len(gating) == 1, f"expected exactly one gating bash block, got {len(gating)}"` (`:273`).
Neither can be kept, because step 0's body must be **literally** `wire-revert-extract`'s
replacement body for the symmetry claim below to hold, and that body has neither. Between step 0
and Task 5 GREEN a missing or duplicated gating fence therefore raises `IndexError` on `_gating[0]`
instead of naming the fault. It is a transient window, not a permanent loss: at GREEN `dbe.select`
restores both guards as `BlockNotFound` and `AmbiguousBlock(n)`, and that is where the "exactly one
gating fence" invariant lives from then on. Step 0 also lands `_gate_bash_block` **without** today's
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
filter in `_gate_block`, returning the gating body wrapped as
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
hmad-dispatch run --timeout 600 -- python3.11 scripts/h_mad_mutation_harness.py tests/mutation-specs/doc_block_exec.json        # MUTATION: ALL_CAUGHT mutations=81
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
count) and **2486** (the count from `h-mad/`) — the pair this document uses everywhere. The
counterpart command in the spec is reached **by name, never by line and never as a requirement**:
`grep -n 'git rev-parse --show-toplevel' docs/01-plan/features/doc-block-exec.spec.md` returns
exactly one hit (verified at `6f0ee85`), and that hit is the line to read. A previous
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
paragraph, located with `grep -n 'Bounds: 1200 s' docs/01-plan/features/doc-block-exec.plan.md` (one hit, verified at `6f0ee85`),
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
- v1.41: Impl-plan audit v38, the GATING round, answered from **two** surfaces at the freeze sha `35698f9` (teammate leg must 2 should 2 nit 3; the agy leg must 1 — real, and verified against the assembled prompt's impl-plan focus list; plus plan audit v78's agy must-fix, which is about this document and was routed here). MUST 1, and both halves of one sentence were wrong in OPPOSITE directions: v1.40's fence-opener residual claimed "no corpus instance exercises either arm, so both are pinned by fixtures and by nothing else". Re-measured from scratch at `35698f9` with a fence-state-aware scan over the tracked corpus this document defines (`git ls-files -- h-mad handoff`, `*.md`, `archive/` excluded — **30** files): the 1-3-space arm is exercised **29** times in **4** files, `h-mad/SKILL.md` among them — the very file Task 5's `_gate_block()` scans — so it is pinned by a fixture AND by 29 live instances; the tab arm is **0** and was pinned by NOTHING, no AC prescribing a tab-indented opener. The residual now ships the runnable stdlib command (verified verbatim under both `bash` and `zsh`), the sha, a positive control, a TRUE NEGATIVE (2 indented marker runs inside an open fence, declined) and its blind forms; AC-1.6's `test_indented_literal_tag_is_not_a_candidate` gains `\t```bash hmad:exec` beside its four-space case; no mutation row follows and the matrix total stays **81**. MUST 2, the recurrence ledger, which v1.40 left contradicting itself in three places (four at one site, "the FIFTH" at a second, "a fifth has not happened" at a third): resolved ONCE by scope rather than by incrementing — audit v37's finding was a **form (a) locator breakage**, not a member of the prose-agreement class, which the foot of that bullet already separates because form (a) has a detector and prose agreement has none; the list stands at four, and both the v37 site and the residual now use a **content predicate** instead of an ordinal. DECISION C closed as a CLASS, not at the instances: 7 counter-instances at `35698f9` found by two surfaces on different instances (6 directory-less mutation-harness line pins, one directory-less `test_suite_collection` line pin, and a `:270` sitting in this document's own "stay admissible" example list without the enclosing symbol `_gate_bash_block` that makes it admissible). Every tree pin now carries its repository path AND its enclosing symbol (`run_spec`, `assemble`, `_run`, `_gate_bash_block`, `_fence_aware_end`, `titled_section`, `test_no_declared_skill_has_a_test_directory_left_out`, `test_exec_codex_dispatch_carries_out_log_and_timeout`, the module-level `_SCANNED` and `REAL_AUDIT_REPORTS`), and the class is declared closed with a **SHAPE grep** plus its bare-filename half — which returned 3 hits before this revision and **0** after [Bracketed correction added at v1.42 under decision H, publish every count with its unit; the entry is corrected here and NOT rewritten, because it records correctly what v1.41 did and only the figure it published was wrong. The before-figure **3** is wrong, and a bare integer with no unit is why it was not caught: re-derived at the base it belongs to, `35698f9`, the same published command returns **22 occurrences across 19 lines over 8 distinct files**. The after-figure **0** is correct and reproduces at `6f0ee85`. The commands for all four units, and the 22-against-7 reconciliation, are in the body's DECISION C residual.] — never a value sweep, since a value sweep only finds members that already drifted. Its three residuals are stated: non-`.py` pins, `grep`'s line-scoping against this document's ~95-column wrap (the paragraph-folded variant was run beside it and agrees), and the symbol half having no detector at all. SHOULD 1: residual (b)'s control claim is corrected — `_braces_outside_fences` and `_fenced_blocks` are known FALSE negatives, not "the negative", and a real TRUE negative was run and read (`_gate_bash_block`, a body holding a three-backtick literal with no fence state of any kind, which the screen declines). No cardinality is published for the declined side: classifying a declined body needs a human read, and every mechanical proxy for "fence state under another name" has the same blind spot the screen does — `_fenced_blocks` keeps its state in a variable called `cur`. SHOULD 2: the AC-1.5/1.7 conclusion orphaned by v1.40's toolchain insertion is moved back beside its own `30 0` measurement and its subject renamed the **closing `#`-run** tab arm, which is a different axis from the fence **opener's**. Nits: "the two files this feature owns" -> "touches"; the English-word tree-derived counts at the residual-(b) bullet and the GNU/BSD sweep are now digits (6, 3, 2). Also re-derived in this revision rather than carried: the header's three sibling versions (design v1.96 / spec v1.58 / plan v1.91, all three having moved in `0aac0b7`, so v1.40's pins were one behind on ALL THREE); all **13** `docs/`-sibling locators re-run at `35698f9`, every one returning exactly 1 hit (decision F, and a real re-measurement because two siblings moved in the shipping commit); the GNU/BSD six-token sweep, now **3** lines and not 2, the new one being this revision's own residual saying it uses no `grep -P`; and the absence claim under residual (b) ("no guard in this repository covers any of them"), which now carries a runnable AST screen returning **2** behavioural tests, neither asserting on any of the six bodies' source. The `74e126f` and `335f535` tree stamps are closed ONCE rather than re-stamped ~40 times: `git diff --name-only 74e126f 35698f9 -- h-mad handoff` is empty, so every tree `path:line` is byte-identical at the freeze sha. Unmoved: 81 rows (25 + 5 + 24 + 27, 80 + 1), the wire spec 8, `docsections.json` 8; five tasks, two wiring (Tasks 1 and 5), one shape each.
- v1.42: Impl-plan audit v39, the GATING round, answered at the freeze sha `6f0ee85` from **two** surfaces (teammate leg must 2 should 2 nit 2; the agy leg, a retry at tools=50, must 4 — of which exactly **one** was routable, the other three being Version History lines the round-eight ruling protects). Every figure below was re-derived at `6f0ee85` in this revision, none carried from a report or from the round-eight decision sheet. **(1) MUST, and it is decision H (publish every count with its unit):** the DECISION C closure published a before-figure of **3** — a bare integer, no unit — which its own published command refutes. Re-derived at the base the figure belongs to, `35698f9`: **22 occurrences across 19 lines over 8 distinct files** (`h_mad_mutation_harness.py` x9, `docsections.py` x4, `test_h_mad_portable_timeout.py` x2, `test_h_mad_collect_report_docs.py` x2, `h_mad_assemble_tdd.py` x2, and one each of `test_suite_collection.py`, `test_h_mad_context_budget_docs.py`, `test_h_mad_audit_cycle.py`), with the four commands that produce the four true integers written out beside them; the after-figure **0** is correct and was re-reproduced at `6f0ee85`. The nit that both halves were stamped `35698f9` closes with it — before at the base the before-figure belongs to, after at the freeze sha. Added, because it is the paragraph's own argument: the reconciliation of 22 against the **7** counter-instances this document reports two surfaces as having found — 7 was those readers' yield, never a census, and the 15 members no reader reached is exactly why the class is closed with a shape grep and not at the instances. The identical wrong figure in the v1.41 entry is **bracket-corrected, not rewritten**. **(2) MUST:** "The only consumer of `command` is the survivor-branch diagnostic" was a false premise about the harness. There are **four**, all inside `run_spec` (`h-mad/scripts/h_mad_mutation_harness.py:482`), re-read at `6f0ee85` and re-derivable with `grep -n 'command' h-mad/scripts/h_mad_mutation_harness.py`: `:562` the baseline gate (`BASELINE_NOT_GREEN`), `:679` the survivor diagnostic, `:694` the no-`test`-key scoring path, `:721` the post-restore read-back (`RESTORE_FAILED`). The consequence is stated **narrowed on evidence, not weakened**: `:694` becomes unreachable once Task 1 lands, because Task 1 adds the `target_command` that `_load_spec` (`h-mad/scripts/h_mad_mutation_harness.py:177`) requires beside a `test` key and raises `SpecError` at `:212` without — verified against the shipped `h-mad/tests/mutation-specs/docsections.json`, which today carries neither `target_command` nor any `test` key, so today every row takes `:694` and the pre-mutation check never runs. The already-red-killer hazard is caught **per row** by that pre-mutation check at `h-mad/scripts/h_mad_mutation_harness.py:630-641`, which runs `scoring_command`, not `command`. What is left is `:562` and `:721`: neither the baseline gate nor the restore read-back ever collects `h-mad/tests/test_h_mad_doc_block_exec.py`, which holds two of the eight killers. "Costs nothing a widened `command` would buy" is struck; the decision now names the scope it chose and what that scope leaves unverified, and names `doc_block_exec.json`'s own run — whose `command` does collect that file — as the cover. **(3) MUST, the agy leg's one routable finding:** the Task 4 exception block's *"The design's exception table agrees (v1.71, impl-plan audit v16)"* is present tense about a design **26 revisions** further on. Repaired in the Conventions rule's form **(b)**: the signature stays as this document's own constraint and the citation is re-cast as provenance, a dated historical fact. Form (b) and **not** form (a), deliberately — minting a needle into a design table row in the same round the design is being revised is how a locator arrives at 0 or 2 hits — so the locator count stays **13**. **(4) The recurrence ledger moves from four to FIVE, and the move is recorded here with its reason so a later reader does not re-file it as drift.** The round-eight decision sheet listed "ledger consistent at four" under *reproduced and UNMOVED -- do not disturb*, and that list was **stale by construction**: it described what the auditor found in the **pre-revision** document, and it was applied to a figure this revision's own fix changes. Repairing (3) above creates the fifth member, so holding the count at four would have reproduced precisely the v1.40 shape the audit caught -- a repaired member the count does not reflect. The move was raised as a departure rather than made silently, and endorsed. The general rule it yields, worth more than the integer: **never freeze a figure the same revision's fix will move.** This is the second round the ledger has been asked to move: v1.41 correctly declined (that finding was a form (a) locator breakage, a different class with a different remedy), and this time the member is genuine — the sentence in (3) asserts what a sibling contains, which is the class's definition. It is the most informative member because it is the **survivorship** arm: written at v1.17, it outlived v1.37 (the revision that wrote the rule), v1.39's item (9) — which **reported having restated it by name and did not touch it** — v1.40, and v1.41's own decision-E pass. Re-derived: `git diff 335f535 74e126f` on this file changes no `StreamPathUnwritable` prose, and `git show 74e126f:docs/01-plan/features/doc-block-exec.impl-plan.md | grep -c 'exception table agrees'` is 1, as at `0aac0b7`, at `35698f9` and at `6f0ee85`. The lesson now written into the ledger: **a sweep over a class with no detector can report a member it never edited**, so a sweep's own claim is not evidence — the diff is. The v1.39 entry is bracket-corrected on that overclaim and otherwise left standing. The form (a) bullet that used to say "NOT a fifth member" is re-stated as a **content predicate** rather than an ordinal, since the list has grown. **(5) The three agy findings that were NOT routed** are Version History lines, and they are left standing: a Version History entry is a dated record of what was true when that revision shipped, and stripping its present-tense phrasing to satisfy a rule about the present would falsify a correct record. One of them names a debt that **has since been paid** — the spec's AC-6.4 gate-command inline comment, which reads 2748/2486 when read out of the freeze commit with `git show 6f0ee85:docs/01-plan/features/doc-block-exec.spec.md`, the spec's own history recording the migration at its v1.53 and v1.54 — so that entry gains a bracketed correction. The other two ("nothing is owed to the plan", "Nothing is owed to any sibling now") could not be shown false and are left untouched, which is stated rather than left silent. **(6) SHOULD:** locator 13 of the 13 named a needle with no target file, so the hard one-hit condition the same bullet imposes could not be evaluated as written. It now carries `docs/02-design/features/doc-block-exec.design.md`, one hit at `6f0ee85`, as the other 12 do. **(7) SHOULD, a class note with no instance:** the symbol half of the tree-pin rule still has no detector; the reviewer read every pin at the freeze sha and found no counter-instance. Recorded here so the next cycle does not re-derive it and does not read the absent detector as an absent check; no edit follows. **(8) Re-derived in this revision rather than carried:** the header's three sibling versions (design v1.97 / spec v1.59 / plan v1.92), read out of the **commit** with `git show 6f0ee85:<doc> | grep -oE '^- v1\.[0-9]+' | tail -1` and not out of the working tree, because the three sibling authors are revising those files concurrently — v1.41's pins were one behind on **all three** — the fifth revision of this document whose header pins were behind by the time they were read, and the second running that all three moved at once, which the header itself enumerates (v1.35, v1.36, v1.38, v1.40, v1.41); all **13** `docs/`-sibling locators, each run as `git show 6f0ee85:<sibling> | grep -c` and each returning exactly **1** hit (decision F), three consecutive revisions now at 13/13, and each locator's own inline verification stamp moved with the measurement from `35698f9` to `6f0ee85` rather than being left behind; the bare-filename shape grep at **0** and its paragraph-folded variant agreeing — the variant itself **repaired** in this revision with `tr -s ' '`, because the fold keeps the next line's leading indentation and so missed a needle wrapped mid-phrase; found with a positive control (this document's own `never a census`, which the old form scores 0 on and the repaired form 1), which is decision A applied to a blind form that had never been shown to fire; and the tree-stamp closure, extended from `35698f9` to the freeze sha — `git diff --name-only 74e126f 6f0ee85 -- h-mad handoff` is **empty**, and so is `git diff --name-only 6f0ee85 -- h-mad handoff`, so every tree `path:line` this document stamps at `335f535`, `74e126f` or `35698f9` is byte-identical both at the freeze sha and in the working tree a 5d implementer will read. **Unmoved, and re-counted from the lists rather than carried:** **81** rows (25 + 5 + 24 + 27, split 80 + 1), verified against the design's helper matrix read at `6f0ee85`, which holds **81** data rows of which exactly **1** names `SKILL.md` in its mechanism column (`registry-row-removed`); the wire spec **8** (`wire-revert-extract`, `wire-revert-select`, `wire-revert-run`, `wire-revert-substitute`, `wire-unconditional`, `hand-rolled-extraction-widened`, `exec-scan-executes`, `consumer-from-import`); `docsections.json` **8** (four shipped plus Task 1's four); five tasks, two `wiring` (Tasks 1 and 5), one shape each.
