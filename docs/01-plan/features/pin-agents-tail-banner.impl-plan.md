# Implementation Plan: pin-agents-tail-banner

> Source: docs/02-design/features/pin-agents-tail-banner.design.md (post-audit, v1.14)
> Paired spec: docs/01-plan/features/pin-agents-tail-banner.spec.md (v1.7, 14 ACs)
> Branch target: feature/pin-agents-tail-banner

## Executive Summary

Six tasks, all in the `h-mad` skill: a test-harness change that lets the stub `orca` answer
`terminal read` per handle (T1), the bounded single-pane read helper `_orca_tail_sig` (T2), the
tail-evidence pass itself inside `_orca_find` (T3), rival rejection on that pass (T4), the two
documentation surfaces the pass invalidates (T5), and the mutation spec that proves each guard
bites (T6). T1 is a prerequisite for every later task's tests; T2 → T3 → T4 is a strict chain;
T5 and T6 depend on T4.

## Mapping to the design's Implementation Order

The design lists seven ordered steps. This plan carries all seven and adds one prerequisite:

| design step | task | note |
|---|---|---|
| — (design §Test Strategy: "the stub must serve BOTH `terminal list` and `terminal read`") | T1 | prerequisite; no production behaviour |
| 1. `_orca_tail_sig` + unit tests | T2 | |
| 2. The pass, entered on `n != 1`, resolving on exactly one | T3 | |
| 4. Unreadable-candidate handling | T3 | **folded — see below** |
| 3. Rival rejection | T4 | |
| 5. Pass 4 comment correction | T5 | |
| 6. `h-mad/SKILL.md` prose update | T5 | |
| 7. Mutation spec | T6 | |

**Why design step 4 is folded into T3 rather than shipped as its own task.** The design's
sanctioned call form is `if out="$(_orca_tail_sig "$h")"; then … fi` (design §API / Interface
Changes). Excluding an unreadable candidate is not an addition to that form, it *is* that form:
`_orca_tail_sig` returns rc 1 and the `if` skips the candidate. A separate task for step 4 would
therefore be dispatched with its two tests (AC-4.1, AC-4.2) **already green**, which is exactly
the vacuous-pass shape the design's Test Plan warns about for test 7. The ACs are stated in T3,
where the code that earns them is written, and T3's RED counts include them.

Steps 3 and 4 are also swapped in order relative to the design (unreadable before rival). Rival
rejection is a genuinely separable predicate — removing it changes a resolution into an
ambiguity, which a test can see — so it keeps its own task, and it is sequenced after T3 because
it edits the loop body T3 introduces.

---

## Task 1: stub-orca-terminal-read

**Production file**: `h-mad/tests/stubs/orca`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`
**Task shape**: `new-behaviour`

**Description**: The stub `orca` answers a single payload from `HMAD_STUB_ORCA_STDOUT`, so a test
cannot make `terminal list` and `terminal read` return different things — and the tail pass
consumes both in one `_orca_find` call. Add an argv-discriminating branch for `terminal read`
that serves a per-handle response file out of a directory named by a new opt-in env var
`HMAD_STUB_ORCA_READ_DIR`. This follows the two existing precedents in the same file
(`HMAD_STUB_ORCA_WT_PS_STDOUT` for the J16 paneKey join, `HMAD_STUB_ORCA_CREATE_STDOUT` for the
J1 launch handle), including their rationale comments and their opt-in property: the branch is
consulted only when the variable is set, so all 290 existing tests keep the shared-stdout
behaviour they were written against.

The per-handle file holds a **full JSON envelope**, not raw tail text, because AC-2.3 needs a
response that is well-formed and *missing* the `.result.terminal.tail` key — a shape raw text
cannot express.

The branch is placed after the `terminal create` branch and before the default `--json` success
envelope, so an un-cased verb is unaffected.

**Code structure**:
```sh
# The tail-evidence pass consumes `terminal list` and `terminal read` in ONE
# _orca_find call, and a single HMAD_STUB_ORCA_STDOUT cannot express both (same
# reason as the J16 worktree-ps and J1 terminal-create overrides above). Keyed by
# handle because the pass reads EVERY candidate and each must be able to differ.
# A handle with no file is the UNREADABLE case (FR-4), not an empty tail.
if [ "${1:-}" = "terminal" ] && [ "${2:-}" = "read" ] && [ -n "${HMAD_STUB_ORCA_READ_DIR:-}" ]; then
  _h=""; _prev=""
  for _arg in "$@"; do
    [ "$_prev" = "--terminal" ] && _h="$_arg"
    _prev="$_arg"
  done
  if [ -n "$_h" ] && [ -f "$HMAD_STUB_ORCA_READ_DIR/$_h.json" ]; then
    cat "$HMAD_STUB_ORCA_READ_DIR/$_h.json"
    exit 0
  fi
  exit 1
fi
```

Test helpers added to `h-mad/tests/test_hmad_dispatch.py`, beside the existing `_orca_terms` /
`_orca_terms_paned` / `_orca_wt_ps` builders:
```python
def _orca_read_env(*lines):
    """A `terminal read --json` envelope whose .result.terminal.tail is an ARRAY.

    The array shape is the live one, measured 2026-09-01 against the pinned codex
    pane: ["codex '--dangerously-bypass-approvals-and-sandbox'", "", "…"].
    """
    return json.dumps({"ok": True, "result": {"terminal": {
        "handle": "h", "tail": list(lines), "truncated": False}}})


def _orca_read_dir(tmp_path, envelopes):
    """Write one `terminal read` response file per handle; return the dir as str.

    envelopes: {handle: envelope_json_text}. A handle ABSENT from the mapping is
    the UNREADABLE case (FR-4) — the stub exits non-zero for it — which is not
    the same as a handle mapped to an envelope carrying an empty tail.
    """
    # A FRESH directory per call: `mkdir(exist_ok=True)` on a shared name lets a
    # previous call's <handle>.json survive, so a handle the caller OMITTED (the
    # UNREADABLE case) would still be served by a stale file and the helper's
    # documented semantics would quietly be false within one tmp_path.
    d = Path(tempfile.mkdtemp(dir=tmp_path, prefix="reads-"))
    for handle, text in envelopes.items():
        (d / f"{handle}.json").write_text(text, encoding="utf-8")
    return str(d)
```
`json` and `tempfile` are already imported at the top of the module; no new import is needed.

**`Path(...)`, not `pathlib.Path(...)`.** The module's imports are `atexit, json, os, shutil,
subprocess, tempfile, time, uuid` and `from pathlib import Path` — verified in the live file —
so the bare name `pathlib` is not bound there and the dotted form raises `NameError` on the
FIRST call, before AC-1.5 tests anything about the stub. Impl-plan audit v16 caught it. Either
form is correct Python in isolation, which is exactly why a code block that is meant to be
followed verbatim has to name the binding the target module actually has.

**Acceptance Criteria**:
- [ ] AC-1.1: With `HMAD_STUB_ORCA_READ_DIR=<dir>` and `<dir>/term_x.json` present, invoking the
      stub as `orca terminal read --terminal term_x --cursor 0 --limit 4000 --json` writes that
      file's bytes to stdout and exits 0.
- [ ] AC-1.2: With the same variable set and `<dir>/term_y.json` **absent**, the same invocation
      for `term_y` exits non-zero and writes nothing to stdout.
- [ ] AC-1.3: With the variable set, `orca terminal list --json` still returns
      `HMAD_STUB_ORCA_STDOUT` verbatim — the new branch does not capture other verbs.
- [ ] AC-1.4: With `HMAD_STUB_ORCA_READ_DIR` unset, `orca terminal read … --json` behaves exactly
      as before the change (`HMAD_STUB_ORCA_STDOUT` when set, else `{"ok":true,"result":{}}`).
- [ ] AC-1.5: `_orca_read_env("a", "b")` produces an envelope whose `.result.terminal.tail` is the
      JSON array `["a","b"]`, and `_orca_read_dir` writes one file per mapping key named
      `<handle>.json`.
- [ ] AC-1.6: The stub still appends its argv line to `HMAD_STUB_CAPTURE` for a `terminal read`
      call, **including the missing-file case that exits 1** — AC-2.4, AC-3.6, AC-3.7 and AC-3.10
      all assert on that capture, and AC-3.10 in particular must be able to see that a read WAS
      attempted for a handle the stub then failed. The new branch must therefore sit below the
      existing capture line at the top of the file, not above it.

**Dependencies on other tasks**: None

---

## Task 2: orca-tail-sig-helper

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`
**Task shape**: `new-behaviour`

**Description**: Add the private helper `_orca_tail_sig <handle>`, which reads one pane's oldest
retained scrollback under a time bound and echoes it, or fails. It is added alone, with no
`_orca_find` change, so the helper is proven before anything consumes it. Placed immediately
after `_agent_pv_re` (whose signatures it exists to be matched against) and before
`_agent_proc_name`.

Three refinements to the design's stated form, each recorded here rather than left to the
implementer, because all three are silent when got wrong:

1. **`.result.terminal.tail` is a JSON ARRAY of line strings, not a string.** Measured live
   2026-09-01 against the pinned codex pane: `type == list`,
   `["codex '--dangerously-bypass-approvals-and-sandbox'", "", "…"]`. The design's cited response
   listing recorded the key as *present* and did not record its type, and `h-mad/SKILL.md`
   §"Reading a dispatch verdict" already spells it `.result.terminal.tail[]`. A bare
   `jq -r '.result.terminal.tail'` on an array prints the pretty-printed JSON — brackets, quotes
   and per-element commas — which still happens to match a signature substring, so the mistake
   would not fail any test written from the design and would ship a matcher operating on a shape
   nobody chose. Join the array explicitly.
2. **The `-e` guard must survive that join.** The design pins `jq -re` precisely so an absent key
   is a non-zero status rather than the literal string `null` at rc 0 (design §Extraction,
   measured). `.tail | join("\n")` on an absent key raises rather than exiting cleanly, and any
   `if type == "array" … else tostring end` form converts the absent key into the *string*
   `"null"` at rc 0 — reintroducing the exact defect `-e` was added to close. Guard with
   `// empty` **before** the type branch, so an absent key produces no output and `jq -e` exits
   non-zero (4).
3. **The time bound is `_cmd_run`, called in-process — not `hmad-dispatch run` as a subprocess.**
   The design, source plan and spec now all say `_cmd_run` (back-propagated after impl-plan
   audit v16 found them still prescribing the verb). They name the verb only to identify *which*
   bounder, since `timeout`/`gtimeout` are forbidden unconditionally by the base invariant.
   Taken literally the verb form would re-exec the wrapper by name, which is not on `PATH` inside the test harness
   (`_bindir:/usr/bin:/bin`) and costs a process per candidate. `_cmd_run` is the function
   `main` dispatches that verb to, so calling it directly is the same bounder with the same
   exit-124 convention. Function definitions are resolved at call time and `main "$@"` runs at
   end of file, so `_orca_find` calling a function defined below it is fine.

**The comment below names `timeout`/`gtimeout` on purpose, and stays.** Impl-plan audit v2
asked for it to be reworded so AC-2.7's regex would stop matching it. The premise was right and
the remedy was aimed at the wrong side: the regex matched 66 lines of the *existing* file, so
rewording one new comment would have left an AC that still could not pass. The predicate was
fixed instead (AC-2.7), and it strips comment lines, so prose naming the forbidden binaries is
free. Keeping it matters — it is the only place an implementer reading this function is told
why the obvious `timeout 2 orca …` is not an option.

**How to test a private shell function "alone" — this needs a harness, not just a test.** The
wrapper's last line is an unconditional `main "$@"` (verified 2026-09-01), so `source`-ing it to
reach `_orca_tail_sig` runs `main` with no arguments as a side effect. The module's existing
`run()` helper only invokes the wrapper through a public verb, and there is no verb that calls
this helper. Add one shared harness beside `run()` and use it for every T2 AC:

```python
_MAIN_LINE = 'main "$@"'


def run_fn(script, *, env=None, capture=None, cwd=None):
    """Invoke a PRIVATE wrapper function directly, with `main` never running.

    `script` is shell run after the wrapper's definitions are in scope, e.g.
    `'_orca_tail_sig term_x'`.

    The wrapper's last line is an unconditional `main "$@"`, so it must be
    REMOVED before the definitions are evaluated. Measured 2026-09-01, three
    shapes, and the two obvious ones both fail:

      * `bash -c 'source W; _orca_tail_sig h'`            -> main runs with no
        args, hits its default arm and prints `unknown verb ''`.
      * `bash -c 'source W; ...' _ _orca_tail_sig h`      -> a sourced file
        INHERITS the caller's positional parameters, so main runs with those:
        `unknown verb '_orca_tail_sig'`. (An earlier revision of this plan
        asserted this shape made main a no-arg call. It does not.)
      * `set --; source W || true`                        -> main's default arm
        `return 2` under the wrapper's own `set -e` exits the shell outright, so
        even the functions defined ABOVE main are gone: `type` reports them
        undefined.

    Stripping the final line and eval-ing the rest leaves every definition in
    scope and runs nothing. Verified: `_agent_pv_re codex` returns its regex.
    """
    src = WRAPPER.read_text(encoding="utf-8")
    lines = src.splitlines()
    assert lines[-1] == _MAIN_LINE, (
        f"wrapper no longer ends with {_MAIN_LINE!r} (last line: {lines[-1]!r}); "
        "this harness strips that line and would otherwise run main")
    body = "\n".join(lines[:-1])
    return _run_bash(f"{body}\n{script}\n", env=env, capture=capture, cwd=cwd)
```

The `assert` is the load-bearing half. If the terminal line ever moves, a silent strip-nothing
would put `main` back in the harness and every T2 test would fail with `unknown verb` — a failure
that looks like a bug in the feature rather than in the harness.

`_run_bash` is not left to interpretation — extract `run()`'s environment construction into a
shared `_isolated_env()` and have both call it. The `HMAD_ORCA_*` / `ORCA_PANE_KEY` /
`HMAD_PREFLIGHT_RECEIPT_FILE` scrubbing inside `run()` is the only reason this suite passes from
inside a live Orca session; a hand-rolled second copy would drift from it, which is the whole
point of the refactor:

```python
def _isolated_env(*, substrate=None, env=None, capture=None, bindir=None):
    """The env `run()` already builds — lifted verbatim, no behaviour change.

    Moving this out of run() is a pure extraction: run() keeps its signature and
    calls _isolated_env(...) for the dict it used to assemble inline. Do NOT
    reimplement the scrubbing.

    One line is NEW rather than lifted: the HMAD_TAIL_READ_TIMEOUT pop. See the
    note under this block.
    """
    e = dict(os.environ)
    e.pop("HMAD_SUBSTRATE", None)
    # Session markers checked by _detect_substrate() ABOVE binary presence.
    e.pop("CMUX", None)
    e.pop("CMUX_PANE", None)
    e.pop("ORCA_SESSION", None)
    e.pop("ORCA_TERMINAL_ID", None)
    e.pop("ORCA_PANE_KEY", None)
    # F13: strip every HMAD_ORCA_* pin (coordinator + agent terminal handles).
    for _k in [k for k in e if k.startswith("HMAD_ORCA_")]:
        e.pop(_k, None)
    e.pop("HMAD_PREFLIGHT_RECEIPT_FILE", None)
    # NEW in this feature: the tail read's own timeout override. Scrubbed for
    # the same reason as every line above it, and BEFORE the env update so a
    # test that sets it explicitly still wins.
    e.pop("HMAD_TAIL_READ_TIMEOUT", None)
    if substrate:
        e["HMAD_SUBSTRATE"] = substrate
    if capture:
        e["HMAD_STUB_CAPTURE"] = str(capture)
    if env:
        e.update({k: v for k, v in env.items() if k != "_BINDIR"})
    # AFTER the update, so a test that passes its own HMAD_ORCA_PIN_FILE keeps it.
    e.setdefault("HMAD_ORCA_PIN_FILE", _absent_pin_file())
    # Only the requested stubs on PATH; the ambient PATH is deliberately excluded.
    e["PATH"] = f"{bindir}:/usr/bin:/bin" if bindir else os.environ["PATH"]
    return e


def run(args, *, substrate=None, env=None, capture=None, cwd=None):
    """Invoke the wrapper with only the named stub binaries on PATH."""
    bindir = Path(env["_BINDIR"]) if env and "_BINDIR" in env else None
    e = _isolated_env(substrate=substrate, env=env, capture=capture, bindir=bindir)
    return subprocess.run(["bash", str(WRAPPER), *args], capture_output=True,
                          text=True, env=e, cwd=cwd)


def _run_bash(script, *, env=None, capture=None, cwd=None):
    e = _isolated_env(substrate="orca", env=env, capture=capture,
                      bindir=(env or {}).get("_BINDIR"))
    return subprocess.run(["bash", "-c", script], capture_output=True,
                          text=True, env=e, cwd=cwd)
```

`run()` is shown above in its post-extraction form: same signature, same call, the env dict now
sourced from `_isolated_env`. The extraction is behaviour-preserving by construction, and the
existing 290 tests are its regression check — run them before and after and require an identical
pass count. **Re-derive that number, never carry it** — `python3.11 -m pytest
h-mad/tests/test_hmad_dispatch.py -q --collect-only` printed 290 on 2026-09-01, up from the 284
this plan carried through v1.12: an unrelated SIGPIPE fix in the same wrapper (`282a3a5`, plus
the agy-recovery and cmux-alive gates) added test nodes to this very module while the plan sat
open. A module-wide count is a shared surface, so any lane touching it moves this number.

**The `HMAD_TAIL_READ_TIMEOUT` pop is load-bearing for AC-2.5, not tidiness.** `_isolated_env`
copies the ambient environment, and this feature introduces the variable, so on a host that
exports it the child inherits the host's value. AC-2.5 exercises the `${HMAD_TAIL_READ_TIMEOUT:-2}`
DEFAULT; with the variable set upstream the test passes without ever reaching the default, and a
regression that dropped the `:-2` fallback entirely would pass too. That is a Test-discrimination
breach of the same shape as the equivalent mutants above: green, and proving nothing. Impl-plan
audit v16 caught it. AC-2.6 then sets the variable explicitly to exercise the override — the
scrub is what makes those two ACs measure different things.

`re` is **not** currently imported by `test_hmad_dispatch.py` (its imports are `atexit, json, os,
shutil, subprocess, tempfile, time, uuid, pathlib.Path` — verified), and AC-2.7's predicate needs
it. Add `import re` in alphabetical position.

**Code structure**:
```sh
_orca_tail_sig() {  # <handle> -> stdout: the pane's tail text; rc 0 = read ok, rc 1 = unreadable
  # Bounded via _cmd_run (the `run` verb's own function): `timeout`/`gtimeout` are
  # forbidden by the base invariant and are never INVOKED here (AC-2.7's predicate is
  # command position, so naming them in this comment is legal). The default in
  # ${HMAD_TAIL_READ_TIMEOUT:-2} is load-bearing, not style: `set -u` is on, so a
  # bare "$HMAD_TAIL_READ_TIMEOUT" aborts the whole wrapper the first time this
  # runs in a shell that never exported it.
  #
  # --cursor 0 is load-bearing: without it the call returns the most RECENT rows,
  # while the launch banner sits at the START of scrollback. On a short pane the
  # mistake is invisible (head and tail coincide) and surfaces only later, on a
  # pane with history, as an UNRESOLVED nobody can explain.
  local h="$1" raw rc=0
  raw="$(_cmd_run --timeout "${HMAD_TAIL_READ_TIMEOUT:-2}" -- \
           orca terminal read --terminal "$h" --cursor 0 --limit 4000 --json 2>/dev/null)" || rc=$?
  [ "$rc" -eq 0 ] || return 1
  # `// empty` BEFORE the type branch: an absent key must produce no output so
  # `jq -e` exits non-zero. `jq -r` prints the literal "null" and exits 0, and any
  # `else tostring end` on a null does the same one step later — both bypass FR-4.
  # `.ok` FIRST. An Orca error envelope exits 0 and still carries a `result`
  # object, so rc and key-presence both say "fine" while the payload is an error
  # -- the F11 class `_cmd_worktree_rm` is already guarded against at :1639. Here
  # it is worse than a wrong rc: partial or stale tail text inside a failed
  # envelope becomes IDENTITY evidence, and this pass resolves a handle from it.
  # That is the unsafe direction; every other FR-4 case declines. Verified
  # 2026-09-01 that a real `terminal read --json` carries top-level `ok: true`.
  printf '%s' "$raw" \
    | jq -re 'if (.ok? // false) != true then empty
              else (.result.terminal.tail? // empty) end
              | if type == "array" then join("\n") else tostring end' 2>/dev/null \
    || return 1
}
```

**Acceptance Criteria**:
- [ ] AC-2.1: For a handle whose stubbed envelope carries `"tail":["alpha","beta"]`,
      `_orca_tail_sig <h>` exits 0 and its stdout is **exactly** `"alpha\nbeta\n"` — asserted by
      equality, not by containment.

      **"Contains both, on separate lines" accepts the wrong extraction.** That was the v1.12
      wording, and it is satisfied by the very bug the code comment above warns about: a bare
      `jq -r '.result.terminal.tail'` on a pretty-printed envelope prints `alpha` and `beta` on
      separate lines too — inside JSON array punctuation — so the AC would pass against an
      implementation with no `join("\n")` at all. Equality is what discriminates the array-aware
      join from the accident that looks like it. Impl-plan audit v17.

- [ ] AC-2.2: When the stubbed `orca` exits non-zero for that handle, `_orca_tail_sig` exits 1 and
      writes nothing to stdout.
- [ ] AC-2.3: For a well-formed envelope with **no** `.result.terminal.tail` key (e.g.
      `{"ok":true,"result":{"terminal":{"handle":"h1"}}}`), `_orca_tail_sig` exits 1 and writes
      nothing to stdout — it does not emit the string `null`.
- [ ] AC-2.4: The captured argv for the call contains `terminal read`, `--terminal <h>`,
      `--cursor 0`, `--limit 4000` and `--json`. Asserted against `HMAD_STUB_CAPTURE`, not against
      the return value.
- [ ] AC-2.5: With `HMAD_TAIL_READ_TIMEOUT` **seeded in the PARENT process environment as the
      string `0`** (`monkeypatch.setenv(..., "0")`) and never passed through `env=`, the call
      still completes (rc 0 on a readable handle) rather than aborting the wrapper — the `set -u`
      default is exercised, not assumed.

      **The seed must be `0`, and `9` — the v1.14 value — made the mutation EQUIVALENT.**
      `_isolated_env` pops `HMAD_TAIL_READ_TIMEOUT` so the child reaches
      `${HMAD_TAIL_READ_TIMEOUT:-2}`. With `9` seeded, BOTH sides of the mutation pass this node:
      scrubbed the child bounds at 2 and a healthy read completes; unscrubbed it bounds at 9 and
      the same healthy read completes. The node asserts rc 0, so nothing observable changes and
      `harness-ambient-timeout-not-scrubbed` is a FIFTH equivalent mutant — introduced by the very
      cycle that added the mutation to close the gap, and caught by impl-plan audit v18.

      `0` is observable because the bounder REJECTS it. Measured 2026-09-01:
      `hmad-dispatch run --timeout 0|notanumber|"" -- sleep 3` all exit **rc 2 in ~0.04 s**, never
      124 and never 0. So unscrubbed, the child inherits `0`, `_cmd_run` returns 2, the helper's
      `[ "$rc" -eq 0 ] || return 1` fires, and this node's rc-0 assertion fails; scrubbed, the
      child never sees it, bounds at the default 2, and the read succeeds. One assertion, two
      outcomes.

      Seeding also makes the test true to the failure it guards: this suite is run from inside
      live h-mad sessions, which is exactly where the variable is exported. The seed rather than
      a second AC is what kept the node table intact at the time (38 then, 39 since AC-2.9).
- [ ] AC-2.6: Assert the timeout VALUE at a function seam, not on the wall clock. Using the
      strip-`main` harness (below), shadow `_cmd_run` with a stub that appends its argv to a file
      and returns a canned readable envelope, then call `_orca_tail_sig`:

      - with `HMAD_TAIL_READ_TIMEOUT=1` in the child, the recorded argv contains `--timeout 1`;
      - with it **unset**, the recorded argv contains `--timeout 2` (the `${…:-2}` default);
      - in both cases the argv also carries `terminal read`, `--terminal <h>`, `--cursor 0`.

      Separately, against the REAL `_cmd_run` with `HMAD_TAIL_READ_TIMEOUT=1` and the stub
      sleeping longer (`HMAD_STUB_ORCA_SLEEP=3`), `_orca_tail_sig` exits **1** — it maps the
      bounder's 124 to its own unreadable code — and returns in **< 2.5 s**.

      **Why a seam and not a stopwatch.** The v1.15 form proved the override with a `< 1.5 s`
      wall-clock threshold, chosen from a measured gap: `--timeout 1` lands 0.376-1.16 s and
      `--timeout 2` lands 1.936-2.232 s. The gap is real, and it is still not a sound assertion —
      scheduler delay on a loaded machine can push a correct `--timeout 1` run past 1.5 s, and an
      intermittently-failing AC is the worst kind. Impl-plan audit v19. The seam asserts the thing
      the contract is actually about: the VALUE handed to the bounder.

      **There is NO lower bound, and its removal was a correctness fix.** The v1.14 form asserted
      `>= 0.5 s` to prove the bounder had run at all. It rejects the CORRECT implementation:
      `_cmd_run`'s watchdog is built on bash's integer-valued `SECONDS`, so a `--timeout 1`
      deadline can expire anywhere inside the current second — eight local timings ran
      0.89-1.16 s, and impl-plan audit v17's own controlled run produced a valid `rc=124` at
      **0.376 s**. A `>= 1.0` assertion (the v1.6 wording) would have failed on the majority of
      correct runs; `>= 0.5` merely failed on fewer of them. The seam is what proves the read was
      issued rather than short-circuited, deterministically and with no timing at all.

      **What each remaining assertion kills.** The seam's recorded `--timeout <n>` kills
      `timeout-override-ignored` (records 2 where 1 was asked for) and `timeout-default-dropped`
      (unset + `set -u` aborts before any call is recorded). `time-bound-removed` is killed by the
      seam too — with the bounder gone there is NO recorded call at all — and the `< 2.5 s` bound
      is kept as a second, independent witness of it, since that mutant otherwise lets the stub's
      own 3 s sleep run to completion. The 3 s sleep must stay above every bound or the test
      cannot tell "the timeout fired" from "the sleep ended".
- [ ] AC-2.7 (spec AC-4.3): No line of `h-mad/scripts/hmad-dispatch.sh` **invokes**
      `timeout`/`gtimeout` as a command. The predicate is *command position*, not substring
      presence, and is implemented in Python rather than as a shell `grep`:

      ```python
      _ARITH = re.compile(r"\$\(\(.*?\)\)")           # $(( timeout * 1000 )) is not a command
      # A word boundary that a HYPHEN and an UNDERSCORE both close: that is what
      # separates an invocation from `--timeout`, `--timeout-ms` and `run_timeout`.
      # Deliberately NOT an enumeration of preceding delimiters — see below.
      # The alternation covers the QUOTED command forms. `"timeout" 2 orca …` is a
      # real invocation and the bare pattern misses it: it requires whitespace
      # immediately after `timeout`, and there a closing quote sits instead.
      _INVOKE = re.compile(r"""(?<![-a-zA-Z0-9_])(?:g?timeout|"g?timeout"|'g?timeout')\s""")

      def _norm(line):
          if line.lstrip().startswith("#"):
              return ""                               # a comment cannot invoke anything
          return _ARITH.sub(" ", line)

      def test_tail_no_timeout_binary_invocation():
          src = WRAPPER.read_text(encoding="utf-8").splitlines()
          hits = [(i + 1, l) for i, l in enumerate(src) if _INVOKE.search(_norm(l))]
          assert hits == [], f"timeout/gtimeout invoked at {hits}"
      ```

      **Two measurements, 2026-09-01, and the second is why the predicate is a lookbehind rather
      than a list of delimiters.**

      1. The v1.0 form of this AC specified
         `grep -nE '(^|[^_[:alnum:]])g?timeout([^-[:alnum:]]|$)'`. That expression matches
         **66 lines of the current, valid file** — `--timeout` (a `-` is non-alphanumeric and not
         `_`), `local timeout=600`, `--timeout-ms`, and ordinary prose. It was an AC that could
         never pass: red before a line of feature code was written.
      2. The v1.2 form, `(?:^|[;|&(]|\$\()\s*g?timeout\s`, fixed that but enumerated the
         characters that may precede a command — and shell command position is also opened by
         *keywords*. Measured: `if timeout 2 orca z; then`, `then timeout 2 …`, `! timeout 2 …`,
         `{ timeout 2 …; }` and `do timeout 2 …` were **all MISSED, 5 of 5**. An implementer
         writing the single most natural form, `if timeout 2 orca …`, would have passed the guard
         while doing exactly the forbidden thing.

      3. The v1.14 form — the bare `(?<![-a-zA-Z0-9_])g?timeout\s` — missed the QUOTED command
         forms `"timeout" 2 orca …` and `'gtimeout' 2 orca …`, because it demands whitespace
         immediately after `timeout` and a closing quote sits there instead. Impl-plan audit v18
         found it. The obvious repair, making the quotes optional on each side
         (`["']?g?timeout["']?\s`), is WRONG and repeats mistake 1: measured, it matches **10
         lines of the current valid file** — `[ "$elapsed" -le "$timeout" ]`, `"$timeout" codex
         …`, `wargs+=(--timeout "` — because a quoted VARIABLE EXPANSION is not a command. Only
         the matched-pair alternation distinguishes them.

      The predicate above was then run against the file and both probe sets: **0 hits** on the
      current file; **13 of 13** invocation probes CAUGHT (the five keyword forms above plus
      `timeout 2 orca x`, `out="$(timeout 5 orca y)"`, `gtimeout 2 orca x`, `foo && timeout 3
      bar`, `(timeout 9 orca y)`, `x=1; timeout 4 orca q`, `"timeout" 2 orca x`,
      `'gtimeout' 2 orca x`); **0 of 7** false positives (`--timeout`,
      `--timeout-ms "$(( timeout * 1000 ))"`, `local timeout=600`, the `case … --timeout)` arm,
      `run_timeout` in a message, a comment naming both binaries, and the helper's own
      `_cmd_run --timeout "${HMAD_TAIL_READ_TIMEOUT:-2}"` line).
      The `_ARITH` strip is load-bearing for the lookbehind form specifically: without it,
      `$(( timeout * 1000 ))` has whitespace on both sides and matches.
- [ ] AC-2.8: The test above fails when `  timeout 2 orca terminal list` is inserted into the
      wrapper, and passes again when it is removed. Verified by doing it, not by inspection —
      a guard whose reject direction is never exercised is decoration.

      **Re-read the FILE after the edit and again after the restore; a test result is not state
      verification.** An insertion that silently no-ops (wrong indentation, a stale buffer, an
      editor writing elsewhere) and a restore that never lands both look exactly like success
      from the test's side — the first reports the guard as enforced when it was never
      challenged, the second leaves a forbidden invocation in a tracked file. Assert the line is
      present after inserting and absent after removing, and confirm `git diff --stat` on the
      wrapper is empty at the end. Same rule for AC-5.4 and AC-6.11. Impl-plan audit v19: this is
      the base Mutation-verification invariant, which asks for verification of the STATE, not of
      a consequence of the state.

- [ ] AC-2.9: For an envelope that exits 0 but carries `"ok":false` **together with a plausible
      tail** (`{"ok":false,"error":{"code":"terminal_gone"},"result":{"terminal":{"handle":"h1",
      "tail":["OpenAI Codex v1.2"]}}}`), `_orca_tail_sig` exits 1 and writes nothing — the banner
      inside a failed envelope must never become identity evidence.

      This is the only FR-4 case whose failure direction is UNSAFE. A missing key, a non-zero
      exit and an unreadable pane all decline; an accepted error envelope RESOLVES, and resolves
      to whatever handle the stale payload happens to name. `rc` and key-presence both read
      "fine" here, which is why neither AC-2.2 nor AC-2.3 covers it. Impl-plan audit v19.

**Dependencies on other tasks**: Task 1 (must complete first)

---

## Task 3: tail-evidence-pass

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/hmad-dispatch.sh:_orca_find` → `_orca_tail_sig`
**WIRE-PIN**: `tests/test_hmad_dispatch.py::test_tail_pass_resolves_single_vendor_banner`

**Why `wiring` and not `new-behaviour`.** This task's deliverable includes the call site
`_orca_find` → `_orca_tail_sig`; T2 ships the callee alone and nothing consumes it until here.
It was declared `new-behaviour` through v1.10, so the wire-pin gate reported `wiring=0` and the
task bypassed the `WIRE`/`WIRE-PIN` requirement, the wire registry, and the wire-specific RED
failure-mode check — while this very plan already carried `wire-disconnect-callee-intact` and
`wire-force-fire-after-pass0` as connection-direction mutants. The mutations asserted a wire the
shape denied.

**The WIRE-PIN's RED reason is caller-observable, which is why T2 must land first.** At this
task's RED `_orca_tail_sig` already EXISTS, so `test_tail_pass_resolves_single_vendor_banner`
fails because the resolution does not happen — not because a symbol is missing. A `WIRE-PIN`
whose RED is a missing callee is `step5d:red_wrong_reason`: it would go green the moment the
callee exists, wired or not.

**Description**: Insert the tail-evidence pass into `_orca_find` between the Pass 2 preview block
and the OS-evidence pass, implementing design Implementation Order steps 2 and 4 (see §Mapping
above for why 4 is here). Entry is unconditional on falling past Pass 2 — `n != 1` — with no
`n == 0` precondition and no `lsof` precondition, which is the whole reason the pass is
standalone rather than a branch inside either neighbour. The candidate pool is `$scoped`
unconditionally: Passes 1 and 2 are matchers that select, not filters that remove, so a pane they
failed to match is still a legitimate candidate, and it is exactly the pane this pass exists to
identify. Resolution requires **exactly one** surviving match; zero or more than one falls
through to the OS-evidence pass, which the pass must not short-circuit by returning non-zero.

An unreadable candidate — read error, timeout, or a response with no `.terminal.tail` — is
excluded from the match set rather than counted as a non-match. That falls out of the sanctioned
call form and is stated as an AC here because it is what the form buys.

The AC-5.1 retention comment lives at the pass (design §Components Changed), so it is written in
this task.

Two idioms are banned by name in the code comment because both are silent and both are what a
tidy implementer writes:

- `if _orca_tail_sig "$h"; then` — the helper writes the tail to **stdout**, so the bare form
  streams a pane's whole scrollback into `_orca_find`'s own stdout and corrupts the handle it
  returns to `env`, `resolve`, `send` and the pin file.
- `if local out="$(_orca_tail_sig "$h")"; then` — `local` is a COMMAND, so the compound form
  returns `local`'s status (always 0) and discards the helper's rc, silently converting every
  unreadable pane into a readable one with an empty tail.

The one `[H-MAD]` line the pass emits on a successful resolution goes to **stderr**, explicitly,
for the same stdout-contract reason (`_orca_find` returns the bare handle on stdout; every one of
this file's 104 diagnostics is already `>&2`). It is worth keeping because it is what lets an
operator tell this pass from Pass 0/1/2 in `env` output — and it is the discriminator AC-3.1 and
AC-3.2 assert on, so a resolution that happened to come from another pass cannot satisfy them.

**Code structure**:
```sh
  # Pass 3 -- TAIL evidence (feature: pin-agents-tail-banner).
  #
  # Reached whenever control falls past Pass 2, i.e. $n != 1. Deliberately gated
  # on NEITHER Pass 2's n==0 condition NOR Pass 4's lsof precondition: an
  # ambiguous title (n>1) never reaches Pass 2, and a machine without lsof never
  # reaches Pass 4, so both shapes are invisible to every other pass. Pool is
  # $scoped unconditionally -- Passes 1 and 2 SELECT, they do not remove, so a
  # pane they failed to match is still a candidate here.
  #
  # RETENTION (AC-5.1). Orca caps a pane's retained tail at 2000 lines regardless
  # of --limit. Measured 2026-09-01: a pane emitting 200 lines kept its first, one
  # emitting 2000 lost it, one emitting 20000 began at line 18001. Agent panes do
  # not normally reach the cap -- they are full-screen TUIs on the alternate
  # screen, so their output never enters normal-buffer scrollback, and a codex
  # pane dispatched to for two days still held 18 lines. The case that DOES reach
  # it is a pane where the agent exited and the operator then ran >2000 lines of
  # shell; there the signature is gone and this pass declines to UNRESOLVED. That
  # is the accepted limit of the pass, not a bug in it.
  #
  # STALE PANE (AC-5.2) -- the other side of the cap, and the likelier one. Tail
  # text is HISTORICAL: it proves what a pane once ran, never what it is running
  # now. A pane whose agent EXITED but which has since emitted fewer than 2000
  # lines of shell still carries the banner, is still a unique match, and is
  # still resolved here -- so a dispatch can land in a plain shell. Accepted
  # deliberately: Pass 1 (title) and Pass 2 (preview) are not liveness-gated
  # either, so this adds no new failure class; only Pass 0 (which names the
  # running program) and Pass 4 (which requires a live process) carry liveness.
  # Gating this pass on liveness would need lsof and would contradict AC-3.3,
  # whose whole point is the machine that has none.
  #
  # The call form below is mandatory. `if _orca_tail_sig "$h"` streams the pane's
  # scrollback into _orca_find's OWN stdout and corrupts the handle it returns;
  # `if local tout="$(...)"` returns `local`'s status (always 0) and discards the
  # helper's rc, turning every unreadable pane into a readable empty one.
  local tail_re tail_ids="" th tout tn tail_h
  tail_re="$(_agent_pv_re "$token")"
  while IFS= read -r th; do
    [ -n "$th" ] || continue
    if tout="$(_orca_tail_sig "$th")"; then
      grep -Eiq "$tail_re" <<<"$tout" || continue
      tail_ids="${tail_ids}${th}
"
    fi
  done <<EOF
$(printf '%s' "$scoped" | jq -r '.result.terminals[]?.handle')
EOF
  tn="$(printf '%s' "$tail_ids" | grep -c . || true)"
  if [ "$tn" -eq 1 ]; then
    tail_h="$(printf '%s' "$tail_ids" | grep . | head -n 1)"
    echo "[H-MAD] $token: bound $tail_h by tail evidence" >&2
    printf '%s\n' "$tail_h"; return 0
  fi
```

**Both matches use a here-string, never `printf … | grep -q`. This is not style.**
Under the wrapper's global `set -o pipefail`, `grep -q` exits the moment it matches, the
upstream `printf` takes SIGPIPE, and the pipeline returns **141** — so a candidate whose tail
DOES carry the signature is skipped by `|| continue`, and a candidate carrying the RIVAL's
signature fails its rejection test and is counted. Measured 2026-09-01 on a 240,106-byte tail
with the signature on line 1:

```
printf '%s' "$big" | grep -Eiq "$re"   -> rc=141   (match found, candidate SKIPPED)
printf '%s' "$big" | grep -Ei  "$re" >/dev/null -> rc=0
grep -Eiq "$re" <<<"$big"              -> rc=0
printf '%s' "$small" | grep -Eiq "$re" -> rc=0     (short tail — the defect is invisible)
```

The last line is why this needed its own tests. Before AC-3.16 and AC-4.5 existed, **every stub
fixture in this plan used a short tail**, so every node would have gone green over a matcher
broken on exactly the long
retained tails the 2000-line cap describes. A here-string has no pipeline, so the compound's
status is `grep`'s alone.

**Acceptance Criteria**:
- [ ] AC-3.1 (spec AC-1.1): Given a `$scoped` pool of one pane whose stubbed tail carries the
      agent's **vendor/model banner** (`OpenAI Codex (v0.145.0)  model: gpt-5.6-terra` /
      `Antigravity CLI`) and no other pane's, `_orca_find <agent>` prints that handle on stdout
      and returns 0, **and** stderr carries `bound <handle> by tail evidence`. Both halves are
      asserted: the stderr marker is what proves the resolution came from this pass rather than
      from a neighbour.
- [ ] AC-3.2 (spec AC-1.2): A pane whose tail carries **only the launch command**
      (`codex '--dangerously-bypass-approvals-and-sandbox'` /
      `agy '--dangerously-skip-permissions'`) and no banner does **NOT** resolve — no handle, no
      stderr marker, fall through.

      **This AC is inverted from its v1.0–v1.3 form and the inversion is the point.** It used to
      assert that banner-only *also* resolves, on the design's claim that "both forms are accepted
      signatures because both are in `_agent_pv_re`". Measured 2026-09-01 with passing controls:
      neither launch line matches its own agent's pattern, while all four banner and status-line
      controls do. Spec v1.5 and design v1.8 carry the correction; asserting the negative here is
      what stops a later reader from "fixing" the regex back.
- [ ] AC-3.3 (spec AC-1.3): `hmad-dispatch env` reports `codex -> <handle>` rather than
      `UNRESOLVED` for a pane that only the tail pass can identify (generic title, empty
      preview).
- [ ] AC-3.4 (spec AC-2.1): Two candidates whose tails both match → `_orca_find` prints no handle
      from this pass and does **not** return non-zero from the pass itself; control reaches the
      OS-evidence pass, asserted by the final `resolved to N candidates` diagnostic on stderr.
- [ ] AC-3.5 (spec AC-2.2): Zero matching candidates → declines the same way: no handle, fall
      through, same diagnostic. **Fixture: exactly one READABLE, non-matching candidate** — not
      zero candidates and not an unreadable one. Its proof is
      `signature-check-not-enforced`, which drops the signature filter so that readable candidate
      enters `tail_ids`, giving `tn=1` and an observably WRONG resolution.

      That mutation replaced `resolve-on-ge-0`, which was a **crash mutant**: with `tn=0` the
      relaxed branch runs `tail_h="$(printf … | grep . | head -n 1)"`, `grep` returns 1 on empty
      input, and the wrapper's `set -euo pipefail` aborts before anything resolves (reproduced:
      rc 1, no output). A kill credited to an abort proves the code breaks when broken and nothing
      about the property.
- [ ] AC-3.6 (spec AC-3.1): When Pass 0 resolves exactly one handle, **no `terminal read` is
      issued at all** — asserted by grepping `HMAD_STUB_CAPTURE` for `terminal read` and
      requiring zero occurrences. It is asserted on the capture, never on the resolution, or the
      test merely restates Pass 0 and passes with this whole feature reverted.
- [ ] AC-3.7 (spec AC-3.2): A pane that `$scoped` excludes — a different `worktreePath`, or the
      coordinator's own pane — is never selected by this pass even when its tail carries a
      perfect signature, and no `terminal read` is issued for its handle (asserted on the
      capture).
- [ ] AC-3.8 (spec AC-3.3, ambiguous half): With two panes whose titles both match `^agy` in one
      tab (so Pass 1 yields n>1 and Pass 2 is skipped), the tail pass still runs and resolves —
      proven by the stderr marker. This is the shape no current pass reaches.
- [ ] AC-3.9 (spec AC-3.3, no-lsof half): With `lsof` absent from the harness `PATH`
      (`_bindir:/usr/bin:/bin`; `lsof` is `/usr/sbin/lsof` on this platform, verified 2026-09-01),
      the pass still resolves and the stderr marker is present — i.e. the resolution did not come
      from the OS-evidence pass.
- [ ] AC-3.10 (spec AC-4.1): One readable matching candidate plus one candidate whose stubbed
      `terminal read` fails resolves to the readable one. The unreadable pane is excluded from
      the match set rather than counted as a non-match, and a `terminal read` WAS attempted for
      it (asserted on the capture, so "excluded" is not confused with "never read").
- [ ] AC-3.11 (spec AC-4.2): When every candidate is unreadable, the pass declines by falling
      through — no handle, no stderr marker, and control reaches the OS-evidence pass.
      **Fixture is fixed by its mutation, not free:** exactly ONE unreadable candidate, resolving
      the `codex` token. `tail-sig-fabricates-banner-on-failure` emits a hardcoded `OpenAI Codex`
      on the failure path, so with two unreadable candidates the mutant fabricates two matches and
      still declines on ambiguity, and with an `agy` fixture it fabricates no wanted match at all —
      in both shapes the mutant SURVIVES and this node's green-at-RED proof is void.
- [ ] AC-3.12 (spec AC-5.1): A comment at the pass states the measured 2000-line cap, that agent
      TUIs do not normally reach it, and that a shell-heavy pane is the case that fails to
      UNRESOLVED. Asserted by reading the source section, not by a bare substring search of the
      whole file.
- [ ] AC-3.13: `_orca_find`'s stdout on a tail resolution is the bare handle and nothing else —
      no tail text, no `[H-MAD]` line. Asserted by exact equality against `<handle>\n`. This is
      what pins the **bare** `if _orca_tail_sig "$h"` idiom out of the implementation: that form
      streams the tail into stdout, so the equality fails.
- [ ] AC-3.14: The pass's call form is asserted **on the source**, not on behaviour: the wrapper
      contains the line `if tout="$(_orca_tail_sig "$th")"; then` and does **not** contain
      `if local tout=`. Read from `WRAPPER.read_text()` with whitespace collapsed, so a reindent
      does not fail it.

      **Why this one is a source assertion and every other AC here is behavioural.** The
      `local`-masking form is behaviourally *indistinguishable* inside this pass, which impl-plan
      audit v3 established and which the v1.2 mutation set got wrong. Under the mutant,
      `_orca_tail_sig`'s rc 1 is masked, the `then` branch is entered with `tout=""`, the empty
      string then fails `grep -Eiq "$tail_re"`, and control reaches `|| continue` — the same
      candidate is skipped, by a different route, with the same result. A behavioural test
      therefore cannot discriminate the two forms, and the `local-masks-helper-rc` mutation as
      first written was a **degenerate mutant landing on the same behaviour**: it would have
      scored `survived` and been misread as a missing test rather than as an equivalent mutant.
      The property is real and is a source-form invariant — the design pinned it by measurement
      for exactly that reason — so it is asserted where it lives.

- [ ] AC-3.15 (spec AC-5.2): The same comment states the **stale-pane** limit — that tail text is
      historical, that an exited agent's banner below the cap still resolves, and why that is
      accepted (Passes 1 and 2 are not liveness-gated either; a liveness gate would need `lsof`
      and contradict AC-3.3). Asserted on the same source section as AC-3.12 but by its own test
      (`test_tail_pass_stale_pane_comment_present`), so a failure names which half of the comment
      is missing rather than reporting "the comment is wrong".
- [ ] AC-3.16: A candidate whose tail is **large — ≥ 200 KB delivered in ≤ 2000 LINES** — and
      carries the agent's banner on its FIRST line resolves, with the `bound … by tail evidence`
      marker. This is the SIGPIPE regression test: with the `printf | grep -q` form it fails at
      rc 141 while every short-tail node stays green.

      **BYTES are the mechanism, LINES are the constraint, and the fixture must satisfy both.**
      SIGPIPE fires on the ~64 KB pipe buffer, which is a byte threshold; Orca hard-caps
      `.terminal.tail` at 2000 lines (spec AC-5.1, the design, and the comment at the pass all
      state it), so a stub emitting 3000 lines models a state the real system cannot produce and
      breaches the base invariant that a stub model what production consumes. The probe blocks
      above used 3000 x 80 chars because they were measuring the PIPELINE, not standing in for
      Orca — that shape is fine in a probe and wrong in a fixture. Build the fixture as
      **1900 lines x ~126 chars ≈ 240 KB**: same byte size, same banner-on-line-1 layout, inside
      the cap. Impl-plan audit v17 caught the mismatch.
**Dependencies on other tasks**: Task 2 (must complete first)

---

## Task 4: tail-pass-rival-rejection

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`
**Task shape**: `new-behaviour`

**Description**: Design Implementation Order step 3. A candidate whose tail carries the RIVAL
agent's signature is rejected **before** it is counted, so it can neither be selected nor create
a false ambiguity that suppresses a real resolution. `$rival_re` is already computed above Pass 1
in `_orca_find` and is reused unchanged; Pass 2 applies the identical predicate to `.preview`, so
this is that rule extended to the new evidence surface rather than a new rule.

The rejection is placed after the signature match and before the append, and it must run even
when the candidate also matches the agent's own signature — a pane carrying both banners is
ambiguous, and the design's asymmetry (an unresolved agent costs a manual pin; a wrongly resolved
one dispatches into a stranger's shell) makes rejection the correct resolution of that
ambiguity.

**Code structure**:
```sh
    if tout="$(_orca_tail_sig "$th")"; then
      grep -Eiq "$tail_re" <<<"$tout" || continue
      # Reject BEFORE counting: a pane demonstrably running the other agent is
      # neither a match nor a source of ambiguity. Same predicate Pass 2 applies
      # to .preview; $rival_re is computed once above Pass 1.
      if [ -n "$rival_re" ] && grep -Eiq "$rival_re" <<<"$tout"; then
        continue
      fi
      tail_ids="${tail_ids}${th}
"
    fi
```

**Acceptance Criteria**:
- [ ] AC-4.1 (spec AC-2.3): Two candidates, one carrying the agent's signature only and one
      carrying BOTH that signature and the rival's, resolve to the first — the rival-carrying
      pane is rejected pre-count, so it neither wins nor makes the pass ambiguous. The stderr
      marker names the first handle.
- [ ] AC-4.2: **WITHDRAWN** — see §"Test-name contract". A rival-only tail fails the agent's
      own signature and never reaches the rejection branch, so no mutation can discriminate it;
      it is subsumed by `test_tail_pass_zero_matches_declines`. The number is retained so AC-4.1,
      AC-4.3, AC-4.4 and AC-4.5 do not renumber. **T4 has FOUR nodes, not five.**
- [ ] AC-4.3: Rejection is symmetric — the same fixture resolved for `agy` rejects the pane whose
      tail carries the codex banner, and vice versa. Asserted for both tokens so the test cannot
      pass against a one-sided implementation.
- [ ] AC-4.4: Rejection happens before counting, not after selection: with **two decoy candidates
      that each carry BOTH the agent's signature AND the rival's**, plus one candidate carrying
      only the agent's, the pass still resolves to that one (count is 1, not 3). A post-count
      filter would have declined on ambiguity here.

      **The decoys must carry both signatures, and this AC is worthless if they do not.** A decoy
      carrying only the rival's signature fails the preceding `$tail_re` match and never reaches
      the count at all, so the test would pass identically whether rejection sits before or after
      counting — the exact placement this AC exists to pin. That was the v1.2 wording and it was
      vacuous.

- [ ] AC-4.5: **Two** candidates: a clean one whose tail carries only the agent's banner, and a
      ≥ 200 KB decoy whose tail carries the **RIVAL's banner FIRST** and the agent's banner **near
      the end**. `_orca_find` resolves to the clean candidate, with the stderr marker.

      **The layout is the AC, and so is the line count.** Build the decoy the same way AC-3.16
      does — **≥ 200 KB in ≤ 2000 lines** (≈ 1900 x 126 chars), not 3000 short ones: Orca caps
      `.terminal.tail` at 2000 lines, so a taller stub models a state production cannot emit.
      The byte size is what drives the SIGPIPE; the line count is only how it is delivered.

      Measured 2026-09-01 on 240,068-byte tails, comparing the broken
      pipeline form against the here-string form:

      | decoy layout | broken: wanted-check | broken: rival-check | fixed: both |
      |---|---|---|---|
      | rival first, wanted near END | rc 0 | **rc 141** | rc 0 / rc 0 |
      | both signatures early | **rc 141** | rc 141 | rc 0 / rc 0 |

      Only the first layout discriminates. Under the broken form its rival check returns 141, so
      rejection silently does not fire, the decoy is counted, and the pass declines on ambiguity —
      whereas the fixed form rejects the decoy and resolves. The second layout fails the *wanted*
      check first, so the decline happens for a reason that has nothing to do with rival
      rejection: the test would pass against a build with rival rejection deleted entirely. That
      was the v1.8 wording of this AC and it was vacuous.

      A rival-**only** tail is likewise not usable here: it fails `$tail_re` and never reaches the
      rejection branch, which is why AC-4.2 was withdrawn rather than reused.
**Dependencies on other tasks**: Task 3 (must complete first)

---

## Task 5: pass-renumbering-docs

**Production file**: `h-mad/scripts/hmad-dispatch.sh`, `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`
**Task shape**: `refactor`

**Description**: Design Implementation Order steps 5 and 6 — the two documentation surfaces the
new pass makes false. No behaviour changes.

1. The OS-evidence pass's opening comment currently reads "Reached only when every pass above
   found nothing", which stops being true the moment a pass that can decline on *ambiguity* sits
   above it. Its header also calls it "Pass 3 (J18)" and it is now Pass 4. Both are corrected in
   the same edit, per the design's Components table.
   **There is a SECOND site the design's Components table does not name.** A value sweep of the
   old number across the file (2026-09-01) finds two, not one: `hmad-dispatch.sh:574`
   (`# Pass 3 (J18) -- OS evidence…`) and `hmad-dispatch.sh:1046`
   (`the exact call \`_orca_find\` Pass 3 already`), which is a cross-reference from
   `_orca_handle_live`'s neighbourhood to that same pass. Renumbering one and not the other
   leaves the file naming two different passes "Pass 3" — the single-surface sweep failure this
   project has shipped repeatedly. AC-5.1 asserts the string `Pass 3` no longer refers to the
   OS-evidence pass anywhere in the file.
2. **`h-mad/SKILL.md:315` — the sentence this feature actually falsifies.** It reads
   "never matches Codex on title — only on a fresh pane's `gpt-N` banner, **which scrolls off
   once it works**". Resolving after exactly that decay, from the banner retained at the START of
   tail scrollback, is the feature's whole purpose. Updating only the pass enumeration below
   would ship a SKILL.md that describes Codex as unresolvable in the case the wrapper now
   resolves — a user-facing contract contradicting changed entry behaviour, which the
   manifest-integrity invariant forbids. Amend it to say the preview banner scrolls off while the
   tail retains it, and pin the amended wording with the same doc-rule test.
3. `h-mad/SKILL.md:320` reads "`_orca_find` joins them as **Pass 0**, ahead of the title and
   preview passes" — an enumeration that is now incomplete. The design calls this out as the one
   surface no test covers and makes it an ordered step rather than a tidy-up; this task closes
   that gap by adding a doc-rule test so the prose cannot silently go stale again. The test goes
   in `h-mad/tests/test_hmad_dispatch.py`, which already loads this exact document as
   `SKILL_MD_TEXT` (module line 16) and already asserts against it (line ~4366). The sibling
   `test_h_mad_substrate_docs.py` is **not** the right home: it reads
   `references/agent-substrate.md`, a different document.

`SKILL.md` frontmatter is untouched — no entry behaviour changes, so the manifest-integrity
invariant is satisfied without a contract edit.

**Code structure**:
```sh
  # Pass 4 (J18) -- OS evidence for panes Orca did not spawn.
  #
  # Reached when no pass above resolved exactly one handle. That now includes the
  # tail-evidence pass, which declines on zero matches AND on ambiguity, so
  # "every pass above found nothing" is no longer an accurate description of how
  # control gets here.
```

```markdown
list` returns `.tabId`/`.leafId`. `_orca_find` joins them as **Pass 0**, ahead of the
title, preview and tail-evidence passes, which resolves the case above exactly: …
```

```python
# h-mad/tests/test_hmad_dispatch.py — added beside the existing SKILL.md assertion
_ENUM_OLD = "ahead of the title and preview passes"
_ENUM_NEW = "ahead of the title, preview and tail-evidence passes"
# Whitespace-collapsed, because the phrase spans a hard line wrap in SKILL.md
# ("ahead of the\ntitle and preview passes", verified 2026-09-01) and the wrap
# point moves whenever the sentence is re-flowed. Matching the raw text would
# make this test fail on a reflow that changed nothing.
_SKILL_MD_FLAT = " ".join(SKILL_MD_TEXT.split())


def test_skill_md_names_tail_evidence_pass():
    """AC-5.2: the pass enumeration in SKILL.md must name every pass ahead of
    which Pass 0 runs.

    Asserted as an exact phrase in BOTH directions rather than by slicing a
    sentence out of the document. Sentence-slicing was the v1 form and it is
    vacuous-prone: the target sentence ends in a COLON ("resolves the case above
    exactly:"), so a `.index(".")` bound overshoots into following paragraphs and
    the test then passes on any later occurrence of the word "tail" — of which
    this document has many. The phrase is located by content, never by line
    number; the line has already moved once.
    """
    assert _ENUM_NEW in _SKILL_MD_FLAT, "pass enumeration omits the tail-evidence pass"
    assert _ENUM_OLD not in _SKILL_MD_FLAT, "stale two-pass enumeration still present"


def test_skill_md_frontmatter_unchanged():
    """AC-5.3: manifest integrity — no entry behaviour changes, so the contract
    fields must not move.

    Asserted as a WHOLE LINE, not as a substring. `"name: h-mad" in fm` is a
    prefix test in disguise: `skill-md-frontmatter-renamed` rewrites the field
    to `name: h-mad-renamed`, which still CONTAINS `name: h-mad`, so the
    substring form leaves the mutant inside the accepted set. That is a FOURTH
    equivalent mutant in this plan — the mutation would score `survived`
    against a guard that holds, `MUTATION: ALL_CAUGHT` would be unreachable,
    and the green-at-RED reject-direction proof this node exists to supply
    would be vacuous. Impl-plan audit v16 measured it with the prescribed
    replacement. Line equality also needs no YAML parser and no new import.
    """
    head = SKILL_MD_TEXT.split("\n---\n", 2)
    assert head[0].startswith("---"), "SKILL.md must still open with frontmatter"
    fm = head[0]
    lines = [ln.strip() for ln in fm.splitlines()]
    assert "name: h-mad" in lines, (
        "frontmatter `name` must be exactly `h-mad`; got "
        f"{[ln for ln in lines if ln.startswith('name:')]!r}"
    )
    desc = [ln for ln in lines if ln.startswith("description:")]
    assert len(desc) == 1, f"expected one description line, got {len(desc)}"
    value = desc[0][len("description:"):].strip()
    # `any(startswith("description:"))` was the v1.13 form and it accepts an EMPTY
    # description, or wholly rewritten contract text -- half of the manifest
    # contract this node claims to pin, unenforced. Impl-plan audit v19.
    assert value.startswith("Orchestrate the 7-phase H-MAD"), f"description reworded: {value[:60]!r}"
    assert len(value) > 200, f"description truncated to {len(value)} chars"


_CODEX_CLAIM_OLD = ("only on a fresh pane's `gpt-N` banner, which scrolls off once it works")
_CODEX_CLAIM_NEW = ("only on a fresh pane's `gpt-N` banner, which scrolls out of the PREVIEW once "
                    "it works — the tail-evidence pass recovers it from retained scrollback")


def test_skill_md_codex_banner_claim_qualified():
    """AC-5.5: SKILL.md must not still say the banner is simply gone once the
    pane works. It scrolls off the PREVIEW; the tail retains it, which is the
    whole basis of Pass 3."""
    assert _CODEX_CLAIM_NEW in _SKILL_MD_FLAT, "codex-detection claim not qualified"
    assert _CODEX_CLAIM_OLD not in _SKILL_MD_FLAT, "stale unqualified claim still present"


def test_os_evidence_pass_renumbered_to_four():
    """AC-5.1: the pass below the tail pass is Pass 4, and no longer claims every
    pass above it 'found nothing' — a pass that declines on AMBIGUITY sits there
    now."""
    src = WRAPPER.read_text(encoding="utf-8")
    assert "Pass 4 (J18)" in src
    assert "Pass 3 (J18)" not in src
    assert "Reached only when every pass above found nothing" not in src
    # The second site the design's Components table does not name.
    assert "`_orca_find` Pass 3 already" not in src
    assert "`_orca_find` Pass 4 already" in src
```

**Acceptance Criteria**:
- [ ] AC-5.1: The OS-evidence pass's header comment in `h-mad/scripts/hmad-dispatch.sh` names it
      `Pass 4 (J18)`, the string `Pass 3 (J18)` is gone, the cross-reference at line ~1046 reads
      `` `_orca_find` Pass 4 already `` rather than `Pass 3`, and the file contains no comment
      claiming that pass is "Reached only when every pass above found nothing". Pinned by
      `tests/test_hmad_dispatch.py::test_os_evidence_pass_renumbered_to_four`. Both sites are
      asserted: renumbering one leaves the file naming two different passes "Pass 3".
- [ ] AC-5.5: `h-mad/SKILL.md` no longer claims Codex's banner "scrolls off once it works"
      without qualification — the amended sentence states that the PREVIEW decays while the TAIL
      retains the banner. Asserted on the same whitespace-collapsed text as AC-5.2, and pinned by
      `test_skill_md_codex_banner_claim_qualified` — its own node, separate from AC-5.2's, so a
      failure names which claim is wrong. Exact old and new phrases are in the Code structure
      block above, matched whitespace-collapsed like AC-5.2.
- [ ] AC-5.2: `h-mad/SKILL.md`'s `_orca_find` sentence names the tail-evidence pass alongside the
      title and preview passes. Asserted against the sentence containing `joins them as **Pass
      0**`, located by content rather than by line number, by
      `tests/test_hmad_dispatch.py::test_skill_md_names_tail_evidence_pass`.
- [ ] AC-5.3: `h-mad/SKILL.md` frontmatter still carries `name: h-mad` and a `description:` —
      pinning the manifest-integrity invariant, since this task must not change entry behaviour.
      Pinned by `tests/test_hmad_dispatch.py::test_skill_md_frontmatter_unchanged`.
- [ ] AC-5.4: `test_skill_md_names_tail_evidence_pass` fails when the SKILL.md sentence is
      reverted to its pre-task wording ("ahead of the title and preview passes"). Verified by
      reverting the sentence, observing the failure, and restoring — not by inspection.
      **Re-read `SKILL.md` after the revert and after the restore** (assert the old phrase present
      then absent, the new phrase absent then present), and finish with `git diff --stat SKILL.md`
      empty. Observing the test flip proves the test reacts to something; it does not prove the
      file holds what you think, and a failed restore leaves the manifest wrong in a tracked
      file. See AC-2.8.

**Dependencies on other tasks**: Task 4 (must complete first)

---

## Task 6: tail-pass-mutation-spec

**Production file**: `h-mad/tests/mutation-specs/tail_signature_pass.json`
**Test file**: `h-mad/tests/test_hmad_dispatch.py` (the tests the spec's mutations must kill)
**Task shape**: `new-behaviour`

**Description**: Design Implementation Order step 7. Every guard this feature introduces gets a
mutation that stubs it to its permissive value, and each mutation carries a `test` node id so a
kill is credited to the guard rather than to a crash, a timeout, or an unrelated assertion. The
spec's `root` is **relative** (`"../.."`, spec-relative, resolving from
`h-mad/tests/mutation-specs/` to the `h-mad/` SKILL directory — NOT the repository root), never
absolute — an absolute root measures whichever checkout it names rather than the one under test,
and the pre-push anchor hook sweeps every tracked JSON, so a drifted or absolute anchor here
blocks unrelated pushes.

Verification for this task is the harness's own verdict, read from the `MUTATION:` token and
never `$?`, plus `--check-anchors` under **bash** (zsh does not word-split the candidate list and
reports `ANCHORS_NOTHING_SWEPT`).

**Code structure**: `find`/`replace` values are the exact strings pinned in T2/T3/T4's code
blocks, so an anchor here and the code there cannot drift; `name`, `file` and `test` are literal.

```json
{
 "root": "../..",
 "target_command": [
  "python3.11",
  "-m",
  "pytest",
  "-q"
 ],
 "command": [
  "python3.11",
  "-m",
  "pytest",
  "tests/test_hmad_dispatch.py",
  "-q",
  "-k",
  "test_tail_ or test_skill_md or test_os_evidence"
 ],
 "mutations": [
  {
   "name": "drop-cursor-0",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_argv_carries_cursor_and_limit",
   "find": "--cursor 0 --limit 4000 --json",
   "replace": "--limit 4000 --json"
  },
  {
   "name": "jq-r-not-jq-re",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_missing_tail_key_returns_1",
   "find": "| jq -re '(.result.terminal.tail? // empty)",
   "replace": "| jq -r '(.result.terminal.tail? // empty)"
  },
  {
   "name": "local-masks-helper-rc",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_call_form_is_source_pinned",
   "find": "    if tout=\"$(_orca_tail_sig \"$th\")\"; then",
   "replace": "    if local tout=\"$(_orca_tail_sig \"$th\")\"; then"
  },
  {
   "name": "resolve-on-ge-1",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_two_matches_declines",
   "find": "  if [ \"$tn\" -eq 1 ]; then",
   "replace": "  if [ \"$tn\" -ge 1 ]; then"
  },
  {
   "name": "drop-rival-rejection",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_rejects_rival_signature",
   "find": "      if [ -n \"$rival_re\" ] && grep -Eiq \"$rival_re\" <<<\"$tout\"; then",
   "replace": "      if false; then"
  },
  {
   "name": "pool-whole-listing",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_pool_is_scoped",
   "find": "$(printf '%s' \"$scoped\" | jq -r '.result.terminals[]?.handle')",
   "replace": "$(printf '%s' \"$listing\" | jq -r '.result.terminals[]?.handle')"
  },
  {
   "name": "marker-to-stdout",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_stdout_is_bare_handle",
   "find": "    echo \"[H-MAD] $token: bound $tail_h by tail evidence\" >&2",
   "replace": "    echo \"[H-MAD] $token: bound $tail_h by tail evidence\""
  },
  {
   "name": "entry-gated-on-n-eq-0",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_runs_on_ambiguous_title",
   "find": "  tail_re=\"$(_agent_pv_re \"$token\")\"",
   "replace": "  tail_re=\"$(_agent_pv_re \"$token\")\"; [ \"$n\" -eq 0 ] || tail_re='__IMPOSSIBLE_MATCH__'"
  },
  {
   "name": "wire-disconnect-callee-intact",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_resolves_single_vendor_banner",
   "find": "    if tout=\"$(_orca_tail_sig \"$th\")\"; then",
   "replace": "    if tout=\"\"; then"
  },
  {
   "name": "wire-force-fire-after-pass0",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_not_run_when_pass0_resolves",
   "find": "  if by_pane=\"$(_orca_find_by_pane \"$token\" \"$scoped\" \"$scope_wt\")\" && [ -n \"$by_pane\" ]; then",
   "replace": "  if false && by_pane=\"$(_orca_find_by_pane \"$token\" \"$scoped\" \"$scope_wt\")\" && [ -n \"$by_pane\" ]; then"
  },
  {
   "name": "stub-branch-swallows-terminal-list",
   "file": "tests/stubs/orca",
   "test": "tests/test_hmad_dispatch.py::test_tail_stub_read_dir_does_not_capture_terminal_list",
   "find": "if [ \"${1:-}\" = \"terminal\" ] && [ \"${2:-}\" = \"read\" ] && [ -n \"${HMAD_STUB_ORCA_READ_DIR:-}\" ]; then",
   "replace": "if [ \"${1:-}\" = \"terminal\" ] && [ -n \"${HMAD_STUB_ORCA_READ_DIR:-}\" ]; then"
  },
  {
   "name": "stub-branch-ignores-env-var",
   "file": "tests/stubs/orca",
   "test": "tests/test_hmad_dispatch.py::test_tail_stub_read_unset_preserves_legacy_behaviour",
   "find": "&& [ -n \"${HMAD_STUB_ORCA_READ_DIR:-}\" ]; then\n  _h=\"\"",
   "replace": "; then\n  _h=\"\""
  },
  {
   "name": "stub-branch-above-capture",
   "file": "tests/stubs/orca",
   "test": "tests/test_hmad_dispatch.py::test_tail_stub_read_still_captures_argv",
   "find": "printf 'orca %s\\n' \"$*\" >> \"${HMAD_STUB_CAPTURE:-/dev/null}\"",
   "replace": "true"
  },
  {
   "name": "tail-re-widened-to-launch-line",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_launch_command_alone_does_not_resolve",
   "find": "  tail_re=\"$(_agent_pv_re \"$token\")\"",
   "replace": "  tail_re=\"$(_agent_pv_re \"$token\")|^${token} .--dangerously\""
  },
  {
   "name": "tail-sig-fabricates-banner-on-failure",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_all_unreadable_declines",
   "find": "  [ \"$rc\" -eq 0 ] || return 1",
   "replace": "  [ \"$rc\" -eq 0 ] || { printf '%s' \"OpenAI Codex\"; return 0; }"
  },
  {
   "name": "skill-md-frontmatter-renamed",
   "file": "SKILL.md",
   "test": "tests/test_hmad_dispatch.py::test_skill_md_frontmatter_unchanged",
   "find": "name: h-mad",
   "replace": "name: h-mad-renamed"
  },
  {
   "name": "signature-check-not-enforced",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_zero_matches_declines",
   "find": "      grep -Eiq \"$tail_re\" <<<\"$tout\" || continue",
   "replace": "      grep -Eiq \"$tail_re\" <<<\"$tout\" || true"
  },
  {
   "name": "wanted-check-back-to-pipeline",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_long_tail_early_signature_resolves",
   "find": "      grep -Eiq \"$tail_re\" <<<\"$tout\" || continue",
   "replace": "      printf '%s' \"$tout\" | grep -Eiq \"$tail_re\" || continue"
  },
  {
   "name": "rival-check-back-to-pipeline",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_long_tail_early_rival_rejected",
   "find": "      if [ -n \"$rival_re\" ] && grep -Eiq \"$rival_re\" <<<\"$tout\"; then",
   "replace": "      if [ -n \"$rival_re\" ] && printf '%s' \"$tout\" | grep -Eiq \"$rival_re\"; then"
  },
  {
   "name": "tail-array-not-joined",
   "_mechanism": "Drop the array branch so a multi-line tail is stringified instead of joined. The measured live shape IS an array, so this is the extraction T2 exists to pin.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_reads_array_tail",
   "find": "              | if type == \"array\" then join(\"\\n\") else tostring end'",
   "replace": "              | tostring'"
  },
  {
   "name": "tail-empty-guard-dropped",
   "_mechanism": "Remove `// empty`, so an envelope with no tail key yields null, `tostring` prints the literal \"null\", and jq exits 0 — a missing key becomes evidence. This is FR-4's bypass.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_missing_tail_key_returns_1",
   "find": "    | jq -re '(.result.terminal.tail? // empty)",
   "replace": "    | jq -re '(.result.terminal.tail?)"
  },
  {
   "name": "timeout-default-dropped",
   "_mechanism": "Remove the `:-2` fallback. `set -u` is on, so the first call in a shell that never exported the variable aborts the whole wrapper rather than reading a tail.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_timeout_default_when_env_unset",
   "find": "  raw=\"$(_cmd_run --timeout \"${HMAD_TAIL_READ_TIMEOUT:-2}\" -- \\",
   "replace": "  raw=\"$(_cmd_run --timeout \"$HMAD_TAIL_READ_TIMEOUT\" -- \\"
  },
  {
   "name": "envelope-ok-false-accepted",
   "_mechanism": "Drop the .ok gate so an exit-0 error envelope's tail is extracted. The pass then resolves an identity from a FAILED read -- the one FR-4 direction that resolves instead of declining.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_rejects_ok_false_envelope",
   "find": "    | jq -re 'if (.ok? // false) != true then empty\n              else (.result.terminal.tail? // empty) end",
   "replace": "    | jq -re '(.result.terminal.tail? // empty)"
  },
  {
   "name": "skill-md-description-reworded",
   "_mechanism": "Reword the manifest description's opening. `any(startswith(\"description:\"))` -- the v1.13 assertion -- accepts it, and accepts an empty description too, so half the manifest contract this node claims to pin was unenforced.",
   "file": "SKILL.md",
   "test": "tests/test_hmad_dispatch.py::test_skill_md_frontmatter_unchanged",
   "find": "description: Orchestrate the 7-phase H-MAD",
   "replace": "description: Runs the H-MAD"
  },
  {
   "name": "timeout-override-ignored",
   "_mechanism": "Hardcode the bound at 2, ignoring the caller's override. The read still succeeds on a healthy pane and still times out on a hung one, so only a bound that separates 1 s from 2 s can see it -- AC-2.6's `< 1.5 s`. Under v1.14's `>= 0.5 s and < 2.5 s` window both values passed and the override contract was green without being enforced.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_times_out",
   "find": "  raw=\"$(_cmd_run --timeout \"${HMAD_TAIL_READ_TIMEOUT:-2}\" -- \\",
   "replace": "  raw=\"$(_cmd_run --timeout 2 -- \\"
  },
  {
   "name": "time-bound-removed",
   "_mechanism": "Call orca directly with no bounder. A hung `terminal read` then stalls every resolution -- the risk FR-4 was written against -- and AC-2.6's upper bound is the only thing that sees it, since the unbounded call still returns the right answer whenever the pane is healthy.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_times_out",
   "find": "  raw=\"$(_cmd_run --timeout \"${HMAD_TAIL_READ_TIMEOUT:-2}\" -- \\",
   "replace": "  raw=\"$( \\"
  },
  {
   "name": "harness-ambient-timeout-not-scrubbed",
   "_mechanism": "Delete the scrub from the TEST harness. On a host exporting HMAD_TAIL_READ_TIMEOUT the child inherits it, AC-2.5 never reaches the ${:-2} default, and a build that dropped the fallback entirely would pass. Killed only because AC-2.5 seeds the ambient value 0, which the bounder rejects with rc 2 (measured): unscrubbed the helper returns 1 and the node's rc-0 assertion fails. A seed of 9 leaves both sides completing and makes this mutation EQUIVALENT -- that was the v1.14 form, caught by audit v18.",
   "file": "tests/test_hmad_dispatch.py",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_timeout_default_when_env_unset",
   "find": "    e.pop(\"HMAD_TAIL_READ_TIMEOUT\", None)",
   "replace": "    pass"
  }
 ]
}
```

**Six mutations target T2's time-and-extraction controls — five in the helper, one in the
PYTHON TEST HARNESS — and none of them is a green-at-RED proof.** The
proof column exists to discriminate nodes that pass before any code is written; these four nodes
are RED: FAIL and need no such proof. They are mutated anyway because Task 6's own claim is that
every new guard is stubbed to its PERMISSIVE value, and impl-plan audit v17 found five that were
not: the array `join("\n")`, the independent `// empty`, the `${HMAD_TAIL_READ_TIMEOUT:-2}`
default, the `_cmd_run` bound itself, and the harness's ambient-environment scrub. Audit v18 added
a sixth, `timeout-override-ignored` — the default and the bound were each mutated, but nothing
mutated the caller's OVERRIDE being honoured. The harness one is `file:
tests/test_hmad_dispatch.py`, not the wrapper: the scrub it removes lives in test code, and
saying "helper guards" of all six was wrong. Each is an
INDEPENDENT control — removing any one leaves the other four intact and the pass still resolving
a healthy pane — so a whole-helper revert cannot stand in for them. The rows above name them,
because the last time a mutation targeted a node whose proof column said `—`, the prose beside it
still claimed no mutation targeted it (v10).

**`wire-disconnect-callee-intact` and `wire-force-fire-after-pass0` are the base invariant's
bidirectional connection requirement, and neither is covered by any other mutation here.**
Named rather than placed: they were "the last two" when this paragraph was written and nine
mutations now follow them, so a positional reference had already gone stale. T2→T3 is a call-site connection: `_orca_find` calls
`_orca_tail_sig`. `invariants.base.md` §"Connection enforcement" asks for a mutation that
**disconnects the call site while leaving the callee intact**, and one that **forces the
connection to fire** where it should not.

- `wire-disconnect-callee-intact` removes the call and nothing else — `_orca_tail_sig` still
  exists, still passes every T2 unit test, and the helper-level suite stays green. Only the
  positive tail resolution (AC-3.1) can see it, which is exactly the property "the pass actually
  calls the helper" and exactly what a whole-module revert cannot establish, since that removes
  both sides at once.
- `wire-force-fire-after-pass0` makes Pass 0 fall through so the tail pass runs where it must
  not. Killed by AC-3.6, which counts `terminal read` calls in `HMAD_STUB_CAPTURE` rather than
  asserting on the resolution — the mutant still resolves the right handle, so a
  resolution-based test would pass. That is why AC-3.6 was written against the capture.

Both anchors must be confirmed to land exactly once (`--check-anchors`); an anchor that matches
zero times mutates nothing and reports the connection as enforced.

Two notes on the mutation set, both of which the harness's `mechanism:` line must confirm rather
than the author asserting them:

- `entry-gated-on-n-eq-0` reproduces the *effect* of the wrong entry condition (the pass is
  reachable but can never match when `n > 1`) rather than restructuring the block, because a
  multi-line `if … fi` wrap is not expressible as a single exact-match `find`/`replace` and an
  anchor that matches zero times mutates nothing while reporting the guard as enforced.
  The impossible pattern is the **literal** `__IMPOSSIBLE_MATCH__`, not a `(?!)` lookahead:
  lookahead is not ERE, and BSD `grep -E` answers it with
  `grep: repetition-operator operand invalid` on **stderr** at rc 2 (measured 2026-09-01, rc 2
  versus rc 1 for the literal). The mutant would still be killed, but by stderr pollution rather
  than by the missed resolution the mutation is supposed to demonstrate — a kill credited to the
  wrong mechanism, which is exactly what the per-mutation `test` field exists to prevent.
- `drop-rival-rejection` neutralises the predicate rather than deleting the block, for the same
  reason and so the surrounding `continue` stays syntactically valid.

Paths inside the spec are **`root`-relative, and `root` is the h-mad skill directory**:
`../..` from `h-mad/tests/mutation-specs/` resolves to `h-mad/`, which is why `file` reads
`scripts/hmad-dispatch.sh` and the node ids read `tests/test_hmad_dispatch.py::…`. This matches
the sibling `verb_no_self_invocation.json` exactly; do not "correct" it to a repo-root path.

**Test-name contract.** The node ids above are the names T1–T5 must create, not suggestions. Each
task's ACs name the test that pins them in the same form, so a rename in an earlier task breaks
this spec's `test` resolution rather than silently crediting a kill to the wrong assertion.
The full map, all under `h-mad/tests/test_hmad_dispatch.py`:

| AC | test node | RED | reject-direction proof when green at RED |
|---|---|---|---|
| AC-1.1 | `test_tail_stub_read_dir_serves_per_handle` | RED: FAIL | — |
| AC-1.2 | `test_tail_stub_read_dir_missing_handle_fails` | RED: FAIL | — |
| AC-1.3 | `test_tail_stub_read_dir_does_not_capture_terminal_list` | RED: PASS | mut `stub-branch-swallows-terminal-list` |
| AC-1.4 | `test_tail_stub_read_unset_preserves_legacy_behaviour` | RED: PASS | mut `stub-branch-ignores-env-var` |
| AC-1.5 | `test_tail_stub_read_helpers_shape` | RED: FAIL | — |
| AC-1.6 | `test_tail_stub_read_still_captures_argv` | RED: PASS | mut `stub-branch-above-capture` |
| AC-2.1 | `test_tail_sig_reads_array_tail` | RED: FAIL | also kills mut `tail-array-not-joined` |
| AC-2.2 | `test_tail_sig_read_failure_returns_1` | RED: FAIL | — |
| AC-2.3 | `test_tail_sig_missing_tail_key_returns_1` | RED: FAIL | also kills mut `tail-empty-guard-dropped` |
| AC-2.4 | `test_tail_sig_argv_carries_cursor_and_limit` | RED: FAIL | — |
| AC-2.5 | `test_tail_sig_timeout_default_when_env_unset` | RED: FAIL | also kills muts `timeout-default-dropped`, `harness-ambient-timeout-not-scrubbed` |
| AC-2.6 | `test_tail_sig_times_out` | RED: FAIL | also kills mut `time-bound-removed` |
| AC-2.7 | `test_tail_no_timeout_binary_invocation` | RED: PASS | procedure AC-2.8 on this same node: insert `timeout 2 orca …`, observe RED, remove |
| AC-2.9 | `test_tail_sig_rejects_ok_false_envelope` | RED: FAIL | also kills mut `envelope-ok-false-accepted` |
| AC-3.1 | `test_tail_pass_resolves_single_vendor_banner` | RED: FAIL | — |
| AC-3.2 | `test_tail_pass_launch_command_alone_does_not_resolve` | RED: PASS | mut `tail-re-widened-to-launch-line` |
| AC-3.3 | `test_tail_pass_env_reports_handle` | RED: FAIL | — |
| AC-3.4 | `test_tail_pass_two_matches_declines` | RED: PASS | mut `resolve-on-ge-1` |
| AC-3.5 | `test_tail_pass_zero_matches_declines` | RED: PASS | mut `signature-check-not-enforced` |
| AC-3.6 | `test_tail_pass_not_run_when_pass0_resolves` | RED: PASS | mut `wire-force-fire-after-pass0` |
| AC-3.7 | `test_tail_pass_pool_is_scoped` | RED: PASS | mut `pool-whole-listing` |
| AC-3.8 | `test_tail_pass_runs_on_ambiguous_title` | RED: FAIL | — |
| AC-3.9 | `test_tail_pass_runs_without_lsof` | RED: FAIL | — |
| AC-3.10 | `test_tail_pass_unreadable_candidate_excluded` | RED: FAIL | — |
| AC-3.11 | `test_tail_pass_all_unreadable_declines` | RED: PASS | mut `tail-sig-fabricates-banner-on-failure` |
| AC-3.12 | `test_tail_pass_retention_comment_present` | RED: FAIL | — |
| AC-3.13 | `test_tail_pass_stdout_is_bare_handle` | RED: FAIL | — |
| AC-3.14 | `test_tail_pass_call_form_is_source_pinned` | RED: FAIL | — |
| AC-3.15 | `test_tail_pass_stale_pane_comment_present` | RED: FAIL | — |
| AC-3.16 | `test_tail_pass_long_tail_early_signature_resolves` | RED: FAIL | — |
| AC-4.1 | `test_tail_pass_rejects_rival_signature` | RED: FAIL | — |
| AC-4.2 | *withdrawn* | — | subsumed by `test_tail_pass_zero_matches_declines`: a rival-only tail fails the agent's own signature and never reaches the count, so NO mutation on rival rejection can discriminate it. Number retained so AC-4.1/4.3/4.4 do not renumber. |
| AC-4.3 | `test_tail_pass_rival_rejection_symmetric` | RED: FAIL | — |
| AC-4.4 | `test_tail_pass_rival_rejected_before_counting` | RED: FAIL | — |
| AC-4.5 | `test_tail_pass_long_tail_early_rival_rejected` | RED: FAIL | — |
| AC-5.1 | `test_os_evidence_pass_renumbered_to_four` | RED: FAIL | — |
| AC-5.2 | `test_skill_md_names_tail_evidence_pass` | RED: FAIL | — (AC-5.4 is this same node's revert-and-observe procedure, not a second node) |
| AC-5.5 | `test_skill_md_codex_banner_claim_qualified` | RED: FAIL | — |
| AC-5.3 | `test_skill_md_frontmatter_unchanged` | RED: PASS | mut `skill-md-frontmatter-renamed` |
| AC-6.11 | `test_tail_mutation_spec_root_is_relative` | RED: FAIL | — |

**The selector is `-k 'test_tail_ or test_skill_md or test_os_evidence'`** — it must cover all 38
nodes, T5's four included.

Two measurements and one correction stand behind that. `-k tail` is wrong: it already collects 2
of the module's 290 tests that have nothing to do with this feature
(`test_wait_snapshots_the_full_buffer_not_a_tail`,
`test_no_verdict_remedies_say_from_start_not_a_bigger_tail`), whose failure would be reported
against this feature's guards. But the narrow `-k 'test_tail_'` was wrong too, and impl-plan audit
v10 caught it: once `skill-md-frontmatter-renamed` was added, a mutation targeted
`test_skill_md_frontmatter_unchanged`, and the paragraph here still claimed "no mutation targets
them". The widened selector collects 0 of 290 today and adds no unrelated test, so it costs
nothing.

**The audit's stated mechanism was wrong, and the distinction matters for anyone reading this
later.** It said `pytest` would skip the targeted test and the mutation would score `survived`.
It would not: `h_mad_mutation_harness.py:606` builds `scoring_command = target_command + [nodeid]`
and runs the named test **directly**, never through `command`'s `-k`, so the pre-check and the
kill both work regardless of the selector. What the selector genuinely governs is the whole-suite
baseline and the "named test passed but something else bit" diagnostic (`:678`) — with a T5 node
outside it, that diagnostic would be blind to exactly the file the mutation touches. The finding
was right that the selector was wrong and wrong about why; the fix is the same either way, and the
false half is recorded so the next reader does not re-derive it.

**Acceptance Criteria**:
- [ ] AC-6.1: The spec contains a mutation removing `--cursor 0` from the read command, and it is
      killed by the AC-2.4 argv test.
- [ ] AC-6.2: A mutation replacing `jq -re` with `jq -r` **and changing nothing else** is killed
      by the AC-2.3 missing-key test. The v1.4 form of this mutation also rewrote `// empty` to
      `// "null"`, which moves two independent controls at once: dropping `-e` alone already makes
      the absent-key path exit 0 with empty output, so a kill could not be attributed to the `-e`
      guard rather than to the filter. One control per mutation, or the `mechanism:` line means
      nothing.
- [ ] AC-6.3: A mutation rewriting `if tout="$(_orca_tail_sig "$th")"` to
      `if local tout="$(_orca_tail_sig "$th")"` is killed by **AC-3.14's source assertion**, not
      by a behavioural test. The two forms produce identical pass behaviour (rc masked → `then`
      entered with `tout=""` → empty fails the signature grep → `|| continue` → same candidate
      skipped), so this mutant is *equivalent* behaviourally and would score `survived` against
      AC-3.11 while the guard it targets is genuinely enforced. The `mechanism:` line must name
      `test_tail_pass_call_form_is_source_pinned`; if it names anything else, the kill is
      accidental and the spec is wrong.
- [ ] AC-6.4: A mutation relaxing `[ "$tn" -eq 1 ]` to `[ "$tn" -ge 1 ]` is killed by AC-3.4
      (two matching candidates must decline).
- [ ] AC-6.5: A mutation deleting the rival-rejection `continue` is killed by AC-4.1.
- [ ] AC-6.6: A mutation widening the candidate pool from `$scoped` to the raw listing is killed
      by AC-3.7.
- [ ] AC-6.7: A mutation redirecting the `[H-MAD] … by tail evidence` line to stdout is killed by
      AC-3.13 (stdout must equal the bare handle).
- [ ] AC-6.8: A mutation gating the pass on `[ "$n" -eq 0 ]` instead of running it whenever
      control falls past Pass 2 is killed by AC-3.8 (the ambiguous-title shape).
- [ ] AC-6.9: `h_mad_mutation_harness.py h-mad/tests/mutation-specs/tail_signature_pass.json`
      prints `MUTATION: ALL_CAUGHT` with `survived=0`, and every mutation's `mechanism:` detail
      line names the test the spec pinned rather than an unrelated failure.
- [ ] AC-6.10: `h_mad_mutation_harness.py --check-anchors` over the whole
      `h-mad/tests/mutation-specs/` directory prints `ANCHORS: ANCHORS_OK` with `drifted=0`.
      The exact command — the harness takes one or more positional spec paths and refuses with
      `ANCHORS_NOTHING_SWEPT` when given none, and **zsh does not word-split an unquoted list
      variable**, which is how that refusal is normally reached:

      ```bash
      bash -c 'python3 ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py \
        --check-anchors h-mad/tests/mutation-specs/*.json'
      ```

      Run it from the repository root, under `bash` (the explicit `bash -c` is the point), and
      read the `ANCHORS:` token, never `$?` — the new spec's anchors match exactly once each and no sibling spec was broken
      by this feature's edits.
- [ ] AC-6.11: The spec's `root` is the relative string `"../.."`, asserted by
      `tests/test_hmad_dispatch.py::test_tail_mutation_spec_root_is_relative`, which loads the
      JSON and asserts `spec["root"] == "../.."` — the exact string, not merely
      `not os.path.isabs(...)`, which any other relative value would also satisfy. It is a real node, not a description:
      neither the mutation run nor `--check-anchors` rejects an absolute root that happens to
      resolve on this machine, so nothing else can catch the regression. Observe it fail after
      changing ONLY `root` to an absolute path, then restore. **Re-read the JSON both times** —
      `json.load` it and assert `spec["root"]` is the absolute path after the edit and exactly
      `"../.."` after the restore — and finish with `git diff --stat` on the spec empty. A
      hand-edit to a JSON file can also leave it unparseable, which fails the test for a reason
      that has nothing to do with `root`. See AC-2.8.
- [ ] AC-6.12 … AC-6.20: one mutation per node that is green at RED, each named in the
      §"Test-name contract" proof column — `stub-branch-swallows-terminal-list`,
      `stub-branch-ignores-env-var`, `stub-branch-above-capture`,
      `tail-re-widened-to-launch-line`, `signature-check-not-enforced`, `tail-sig-fabricates-banner-on-failure`,
      `skill-md-frontmatter-renamed`, plus the two that revert the here-string guard —
      `wanted-check-back-to-pipeline` and `rival-check-back-to-pipeline`. Nine mutations for
      nine AC numbers. Each must be `caught`, and its `mechanism:` line must name
      the node the proof column claims — a kill by any other test means the mutation proves
      nothing about that node.

**Dependencies on other tasks**: Task 5 (must complete first)

---

## Verification (all three items the design's Success Criteria require)

1. **RED before GREEN — but NOT every test, and the difference is a 5d halt.** The blanket rule
   "every new test is observed FAILING against the unfixed wrapper" is **unsatisfiable here**, and
   stating it would guarantee `step5d:red_not_all_failing` on a correct RED. Several ACs are
   *preservation* or *negative* assertions that are already true before the feature exists: AC-1.4
   (legacy stub behaviour unchanged), AC-3.2 (a launch-command-only tail does not resolve — today
   nothing resolves), AC-3.5 (zero matches decline), AC-4.2 (a rival-only candidate declines),
   AC-5.3 (frontmatter unchanged). A test that passes at RED for those reasons is correct, not
   decoration.

   Each 5d dispatch carries the **per-task node counts** below, and
   `h_mad_assemble_tdd.py --expect-fail/--expect-pass` is given exactly these numbers.

   **The unit is a TEST NODE, not an AC** — that distinction is why the v1.5 form of this table
   was unusable. Two nodes carry two ACs each, and the AC-level table put
   `test_tail_no_timeout_binary_invocation` in the FAIL column (as AC-2.8) *and* the PASS column
   (as AC-2.7), and counted `test_tail_pass_names_tail_evidence` twice as a failure (AC-5.2 and
   AC-5.4). Counts derived from it could not have matched an actual pytest run, so the independent
   5d count check would have halted a correct dispatch. AC-2.8, AC-4.2 and AC-5.4 are therefore
   reframed below as **procedures**, not nodes.

   | task | nodes | FAIL at RED | PASS at RED | the PASS nodes |
   |---|---|---|---|---|
   | T1 | 6 | 3 | 3 | `…does_not_capture_terminal_list`, `…unset_preserves_legacy_behaviour`, `…still_captures_argv` |
   | T2 | 8 | 7 | 1 | `test_tail_no_timeout_binary_invocation` |
   | T3 | 16 | 10 | 6 | `…launch_command_alone_does_not_resolve`, `…two_matches_declines`, `…zero_matches_declines`, `…not_run_when_pass0_resolves`, `…pool_is_scoped`, `…all_unreadable_declines` |
   | T4 | 4 | 4 | 0 | — |
   | T5 | 4 | 3 | 1 | `test_skill_md_frontmatter_unchanged` |
   | T6 | 1 | 1 | 0 | `test_tail_mutation_spec_root_is_relative`; the harness verdicts themselves are read from the `MUTATION:` token, not from pytest counts |
   | **total** | **39** | **28** | **11** | |

   **Derive these counts at dispatch time; do not read them from the table.** The count and the
   enumeration are two surfaces that drift, and this one has drifted once already. The
   authoritative form is the enumeration in §"Test-name contract", one row per node with a single
   `RED:` outcome; run

   ```bash
   F=docs/01-plan/features/pin-agents-tail-banner.impl-plan.md
   grep -cE '^\| AC-.* \| `test_.*` \| RED: (FAIL|PASS) \|' "$F"   # 38  total nodes
   grep -cE '^\| AC-.* \| `test_.*` \| RED: PASS \|'        "$F"   # 11  --expect-pass
   grep -cE '^\| AC-.* \| `test_.*` \| RED: FAIL \|'        "$F"   # 28  --expect-fail
   ```

   **Those three numbers are the AGGREGATE CHECK, not the dispatch inputs.**
   `h_mad_assemble_tdd.py` cuts ONE `## Task N` and takes that task's `--expect-fail` /
   `--expect-pass`; feeding it 27/11 would guarantee `step5d:red_not_all_failing` on every task
   (T1 expects 3/3, T2 7/1, …). Derive per task from the same authoritative rows — the AC prefix
   identifies the task:

   ```bash
   F=docs/01-plan/features/pin-agents-tail-banner.impl-plan.md
   for n in 1 2 3 4 5 6; do
     row="^\| AC-$n\.[0-9]+ \| \`test_.*\` \| RED:"
     printf 'T%s  --expect-fail %s  --expect-pass %s\n' "$n" \
       "$(grep -cE "$row FAIL" "$F")" "$(grep -cE "$row PASS" "$F")"
   done
   ```

   Expected: T1 3/3 · T2 7/1 · T3 10/6 · T4 4/0 · T5 3/1 · T6 1/0, summing to 28/11 over 39 —
   and **every row carries exactly ONE AC label** so the per-task regex sees all 38. Two rows
   briefly carried `AC-2.7, AC-2.8` and `AC-5.2, AC-5.4`; the loop then matched 35 and silently
   under-counted T2 and T5. A shared node takes its PRIMARY AC, with the secondary named in the
   proof column as the procedure it is —
   run the loop, do not read those numbers. The aggregate is only how you check the per-task
   figures add up.

   **The v1.6 form of these commands returned 0 and 13.** They were
   `grep -c '^| \`test_'` (0 — every row starts with `| AC-…`, not the node) and an unanchored
   `grep -c 'RED: PASS'` (13 — it also matched prose outside the table). Their difference would
   have been passed to `--expect-fail` as **-13**, making the 5d dispatch invalid. Both are
   anchored to the full row shape above and verified to return 38 / 11 / 27 against this file.

   **Every node green at RED needs a discriminating reject-direction proof**, or the base
   Test-discrimination invariant is unmet. The v1.5 claim that "every such AC is named by a
   mutation" was **false**, verified against the spec: `local-masks-helper-rc` was retargeted to
   `…call_form_is_source_pinned` and so cannot prove `…all_unreadable_declines`;
   `resolve-on-ge-1` leaves zero-match behaviour untouched and so cannot prove
   `…zero_matches_declines`; and `…does_not_capture_terminal_list`,
   `…unset_preserves_legacy_behaviour`, `…still_captures_argv`,
   `…launch_command_alone_does_not_resolve` and `…frontmatter_unchanged` had no proof at all.
   T6 gains one mutation per uncovered node, plus two that revert the here-string guard (AC-6.12 … AC-6.20); the mapping is in §"Test-name
   contract". Any node marked `RED: PASS` that no mutation names is a coverage hole — check that
   before 5e, not after.

   The general trap this replaces still applies and is why the discriminating ACs were written:
   `cn == 1` with `lsof` present already resolves today via OS evidence, so a careless positive
   test passes with the whole feature reverted. AC-3.6, AC-3.7, AC-3.9, AC-3.10 and AC-3.13 exist
   to be immune to that.
2. **Suites and mutation.** `pytest h-mad/tests/test_hmad_dispatch.py -q -k orca_find`, then
   `pytest h-mad/tests/test_hmad_dispatch.py -q -k test_tail_`, then the full `pytest` (testpaths
   now cover `handoff/scripts`), then `h_mad_mutation_harness.py` on the new spec, then
   `--check-anchors` under bash — never zsh.
3. **Live check — it must exercise THIS pass, not merely succeed.** `hmad-dispatch env` resolving
   codex is NOT sufficient evidence: Pass 0, the title pass, the preview pass or an ambient pin
   can all satisfy it without a single `terminal read`, so the check would pass with the whole
   feature reverted — the exact vacuous-verification shape this feature's ACs were written
   against. Require all four:
   1. `hmad-dispatch pin-agents --clear` first, then **assert the mutation landed by re-reading
      the file it was supposed to remove** — `hmad-dispatch env` prints the path
      (`<repo>/.h-mad/orca-pins.env` here), so record that path and check its absence, or that it
      names neither agent, in a separate read. Also confirm no `HMAD_ORCA_*_TERMINAL` is exported.
      The env check alone is not sufficient and was the v1.8 wording: `--clear` mutates the pin
      *file*, and a pin surviving there short-circuits resolution exactly as an exported variable
      would — verifying a different surface from the one you changed is the mutation-verification
      failure this project has shipped before.
   2. Confirm the earlier passes do NOT resolve on their own — `worktree ps` does not name the
      pane (Pass 0 blind), and its title/preview do not match (Passes 1-2 blind).
   3. `hmad-dispatch env 2>&1` carries **`bound <handle> by tail evidence`**. That marker is
      emitted by this pass and by nothing else, so it is the only output that proves the tail
      pass produced the resolution.
   4. If a pane was created for the check, close it and **re-list terminals to confirm the
      removal** — asserting the cleanup landed, on the same rule that makes the mutation harness
      re-read the tree after a restore.

## Version History
- v1.0: Initial implementation plan draft.
- v1.1: Impl-plan audit v1 must-fixes — Task 6 mutation node ids made literal (the placeholders would have resolved to nothing and credited kills to a crash); Task 1 test-helper bodies and Task 5's doc-rule test written out; Task 5 retargeted from test_h_mad_substrate_docs.py (wrong document) to test_hmad_dispatch.py, and a SECOND stale 'Pass 3' cross-reference at hmad-dispatch.sh:1046 added that the design's Components table does not name.
- v1.2: Impl-plan audit v2 — AC-2.7's regex matched 66 lines of the CURRENT valid file (--timeout, local timeout=600, prose), so it was an AC that could never pass; replaced with a measured command-position predicate (0 hits on the file, 5/5 real invocations caught) and the Task 2 comment kept rather than reworded. Task 5's sentence-slice replaced by a whitespace-collapsed two-directional phrase assert (the target sentence ends in a colon, so .index('.') overshot). Mutation impossible-pattern changed from the non-ERE (?!) to a literal.
- v1.3: Impl-plan audit v3 — AC-2.7's delimiter-enumeration regex MISSED 5 of 5 keyword-position invocations (if/then/!/{/do timeout), so the most natural forbidden form passed the guard; replaced with a hyphen-and-underscore lookbehind, re-measured 11/11 caught and 0/6 false positives. The local-masks-helper-rc mutant is behaviourally EQUIVALENT inside this pass and would have scored survived, so AC-3.14 pins the call form on the SOURCE and the mutation retargets to it. AC-4.4's decoys must carry BOTH signatures or the pre-count placement is untested.
- v1.4: Impl-plan audit v5 (codex surface) — the first non-agy pass, and it broke a gate four agy cycles had passed. AC-3.1/AC-3.2 inverted after back-propagating to spec v1.5 and design v1.8: _agent_pv_re matches the BANNER and NO MATCH for either launch command (measured with controls), so the launch-only guarantee was unsatisfiable. AC-3.15 and a stale-pane comment added: tail evidence is historical, and below the 2000-line cap an exited agent's banner still resolves - accepted because Passes 1 and 2 are not liveness-gated either. Two bidirectional connection mutations added (disconnect-callee-intact, force-fire-after-pass0), both anchors verified against the live file. A run_fn harness specified because the wrapper ends in an unconditional main so the helper cannot be called alone; import re added; selector narrowed to -k test_tail_ after -k tail was measured collecting 2 unrelated tests.
- v1.5: Impl-plan audit v7 (codex) — two of the four must-fixes were defects in v1.4's own fixes. The run_fn harness description was FACTUALLY WRONG (a sourced file inherits the caller's positional parameters, so the call argv reached main; and main's default arm returns 2, which under the wrapper's set -e exits the shell and loses every definition) - replaced with a measured strip-the-terminal-main-line harness plus an assert that fails loudly if that line moves. The blanket 'every new test is RED' rule was unsatisfiable and would have halted 5d on red_not_all_failing: five ACs are preservation or negative assertions already true today, so a per-task expect-fail/expect-pass table replaces it and each green-at-RED AC is tied to the mutation that proves its reject direction. The jq mutation moved two controls at once and now isolates -re to -r. Header, AC ordering and the AC-3.15 map row corrected.
- v1.6: Impl-plan audit v8 (codex) — four of five must-fixes were defects in v1.5's own RED table. It was written at AC granularity while --expect-fail counts TEST NODES: two nodes carried two ACs each, putting one node in both columns and double-counting another, so the counts could never have matched a pytest run. Recast as a 35-node enumeration with one RED outcome each (24 FAIL / 11 PASS). The claim that every green-at-RED node was mutation-discriminated was FALSE - six had no proof and two were named by mutations that cannot kill them; seven mutations added (17 total), AC-4.2 withdrawn as genuinely undiscriminable. AC-6.11 gained a real test node. The live check required only that env resolve codex, which Pass 0 or an ambient pin satisfies with the feature reverted; it now requires the tail-evidence stderr marker with pins cleared and earlier passes proven blind. Blanket-RED rule back-propagated out of the design and plan.
- v1.7: Impl-plan audit v9 (codex, high-evidence: it ran five timing probes of its own) plus audit v10 (agy). AC-2.6's elapsed >= 1.0 assertion would have failed on the MAJORITY of correct runs - _cmd_run's watchdog uses bash's integer SECONDS, and ten trials across two independent probes measured 0.89-1.16s at rc=124; bound lowered to 0.5. The prescribed RED-count derivation commands returned 0 and 13 instead of 35 and 11 (one anchored on the wrong column, one unanchored into prose), so their difference would have been passed to --expect-fail as -13; both are now row-anchored and verified. tail-sig-swallows-failure was a THIRD equivalent mutant - return 0 with empty stdout produces the same decline - replaced by tail-sig-fabricates-banner-on-failure, which turns unreadable evidence into a MATCHING candidate. The mutation selector excluded a T5 node one of its own mutations targeted (agy's mechanism for this was wrong: named tests run via target_command + nodeid, never through -k; the selector governs the baseline and the wrong-catcher diagnostic). Design live-check back-propagation was claimed in v1.10's history but absent from the body; applied. _run_bash given a concrete extraction; AC-6.12..6.18 widened to 7 numbers for 7 mutations.
- v1.8: Impl-plan audit v11 (codex) — findings dropped 5 to 1, and the one is the sharpest of the run. T3 and T4 both specified printf '%s' "$tout" | grep -Eiq, which under the wrapper's global set -o pipefail returns 141 when grep -q exits early and printf takes SIGPIPE: a candidate whose tail DOES carry the signature is skipped, and a rival-bearing candidate fails its rejection and is COUNTED. Reproduced on a 240,106-byte tail with the signature on line 1 (rc=141), against rc=0 for the same tail short. Every stub fixture in this plan uses a short tail, so all 37 nodes would have gone green over a matcher broken on exactly the long retained tails the 2000-line cap describes. Both matches now use a here-string, which has no pipeline; drop-rival-rejection re-anchored; AC-3.16 and AC-4.5 added as long-tail regression tests (nodes 35 to 37, expect-fail 24 to 26). AC-6.10 gained the exact bash -c sweep command after verifying it returns ANCHORS_OK specs=34 mutations=342 drifted=0 and that the no-paths invocation is the documented refusal.
- v1.9: Impl-plan audit v12 (codex) — two of three must-fixes were defects in v1.8's own SIGPIPE fix. AC-4.5 was VACUOUS as written: a rival-only tail fails the wanted check first and never reaches rival rejection, and putting both banners early makes the WANTED check return 141, so the expected decline happens for a reason unrelated to the branch under test - it would pass against a build with rival rejection deleted. Measured both layouts on 240,068-byte tails; only rival-first-wanted-last discriminates (broken: wanted rc 0, rival rc 141; fixed: 0/0), and the AC now specifies that exact fixture. The RED counts were stale on FOUR non-history surfaces, not the three the audit named - it missed plan.md:178 - so the sweep found one more than the finding did; all now 37/11/26. The live check ran pin-agents --clear and then verified only the ENVIRONMENT, never re-reading the pin file the clear was meant to empty: it now records the path env prints and asserts on that file. AC-6.11 claimed an exact-string root assertion while prescribing not os.path.isabs, which any relative value satisfies.
- v1.10: Impl-plan audit v13 (codex) — all three must-fixes were mutation-discrimination gaps in this plan's own scaffolding, and the 37/11/26 counts reproduced. resolve-on-ge-0 was a CRASH mutant: with tn=0 the relaxed branch runs tail_h=$(printf … | grep . | head -n 1), grep returns 1 on empty input and set -euo pipefail aborts before anything resolves (reproduced: rc 1, no output), so a kill would be credited to an abort rather than the property. Replaced by signature-check-not-enforced, which lets a readable non-matching candidate into tail_ids and produces an observably wrong resolution; AC-3.5's fixture is pinned to exactly one readable non-matching candidate to make that kill possible. The two long-tail nodes added in v1.8 had NO mutation reverting the here-string to the pipeline, so the guard they exist for was never mutation-tested - two reverting mutations added, one per branch. tail-sig-fabricates-banner-on-failure has a fixture precondition that was unstated: its hardcoded OpenAI Codex output only changes behaviour for exactly one unreadable candidate resolving codex, so AC-3.11's fixture is now pinned. AC-4.2 was still listed as active in Task 4 while marked withdrawn elsewhere. The spec's assumption about launch-command visibility was restated in terms of the banner, which v1.5 made the only evidence.
- v1.11: Impl-plan audit v14 (codex) — the sharpest finding of the run is a SHAPE error 14 cycles old. Task 3 was declared new-behaviour while its deliverable includes the _orca_find -> _orca_tail_sig call site, so the wire-pin gate reported wiring=0 and the task bypassed WIRE/WIRE-PIN, the wire registry and the wire-specific RED failure-mode check - all while this same plan already carried wire-disconnect-callee-intact and wire-force-fire-after-pass0 as connection-direction mutants. The mutations asserted a wire the shape denied. T3 is now wiring with the pin named, and the gate reports wiring=1. The RED counts were derived as an AGGREGATE and called the dispatch inputs, but assemble_tdd cuts ONE task and takes THAT task's counts, so 27/11 would have halted every task on red_not_all_failing; a per-task loop is prescribed, and running it exposed a second defect the audit did not name - two rows still carried combined AC labels (AC-2.7, AC-2.8 and AC-5.2, AC-5.4), so the loop matched 35 of 37 and silently under-counted T2 and T5. SKILL.md:315's claim that Codex's banner scrolls off once it works is precisely what this feature falsifies; AC-5.5 added to amend and pin it (nodes 37->38).
- v1.12: Impl-plan audit v15 (codex) — every must-fix was a correction recorded only where it was FOUND, never on the paired surface. The counts were stale on SIX live sites across three docs (37 where the table now derives 38, 26/11 where it derives 27/11, 'T5's three' where T5 has four). The design still prescribed a subprocess 'hmad-dispatch run' and an untyped .result.terminal.tail, so an implementer following the cited source would have produced exactly the code path T2 rejects - the in-process _cmd_run call and the measured ARRAY shape are now IN the design. The plan's Success Criteria and the design's live check still required only that env resolve codex, which Pass 0 or an ambient file pin satisfies with zero terminal reads; both now carry the pin-FILE re-read (checking the environment is a different surface from the one --clear mutates), earlier-pass blindness, the tail-evidence marker and a cleanup re-list. AC-5.5 gained its exact old/new phrases and test body; _orca_read_dir now makes a fresh directory per call, since mkdir(exist_ok=True) let a previous call's handle file serve a handle the caller deliberately OMITTED. Audit-side note: the reviewer ran the wire-pin gate, which auto-registers and rewrote the wires.jsonl timestamp - it disclosed the mutation rather than reverting it, and the timestamp-only churn was discarded here.
- v1.13: Impl-plan audit v16 (codex) — SIX must-fixes, three of them defects in this plan's own test scaffolding rather than stale prose. `skill-md-frontmatter-renamed` was a FOURTH equivalent mutant: the test asserted `"name: h-mad" in fm`, and the mutant's `name: h-mad-renamed` still CONTAINS that substring, so the mutation would have scored `survived` against a guard that holds and ALL_CAUGHT would have been unreachable; asserted as a whole line now, verified with the prescribed replacement (substring True/True, whole-line True/False). Task 1's `_orca_read_dir` called `pathlib.Path(...)` while the module binds only `Path` via `from pathlib import Path` (verified in the live file), so following the block verbatim raised NameError before AC-1.5 tested anything. `_isolated_env` was prescribed as "not left to interpretation" while its body was a literal `...`; the extracted body is now spelled out, including `run()` in post-extraction form. That body also gained the `HMAD_TAIL_READ_TIMEOUT` pop AC-2.5 needs: `_isolated_env` copies the ambient environment and this feature INTRODUCES the variable, so on a host exporting it the default `${HMAD_TAIL_READ_TIMEOUT:-2}` is never reached and a regression dropping the fallback passes too. The time-bound contract was swept to `_cmd_run` and "no INVOCATION" across all four documents (nine sites; the nine that remain are descriptive — the ruling itself, one historical CLI measurement, and "which bounder"). Source-design citation corrected v1.12 -> v1.14 and the wire mutations named instead of placed.
- v1.14: Impl-plan audit v17 (codex) — must 6 -> 3, and two of the three were consequences of work done OUTSIDE this feature. AC-3.16 required a >= 3000-LINE stub while Orca hard-caps .terminal.tail at 2000, so the fixture modelled a state production cannot emit; bytes are the SIGPIPE mechanism and lines are the constraint, so the fixture is now >= 200 KB in <= 2000 lines (~1900 x 126 chars) and AC-4.5 takes the same shape. The probe blocks keep their 3000 x 80 form because they were measuring the pipeline, not standing in for Orca. The carried "284 existing tests" was stale on four live sites: a SIGPIPE fix in the same wrapper from an unrelated lane (282a3a5, plus the agy-recovery and cmux-alive gates) added nodes to this module while the plan sat open — re-derived to 290 by collection, with the selector re-checked at 0/290 and 2/290. Five guard mutations were missing despite Task 6 claiming every new guard is stubbed to its permissive value: the array join, the independent // empty, the ${HMAD_TAIL_READ_TIMEOUT:-2} default, the _cmd_run bound, and the harness scrub (24 mutations now). AC-2.1 was too weak to pin the first of those — "contains both on separate lines" is satisfied by the bare `jq -r` the code comment warns against, since pretty-printed JSON prints array elements on separate lines too; asserted by equality on "alpha\nbeta\n" now. AC-2.5 gained an ambient parent-env seed, without which the harness-scrub mutation is unkillable — folded into the existing node rather than added as AC-2.1b, which would have moved every count in the 38-node table. Also: the helper's own comment still said timeout/gtimeout are "absent from this file" — a site the v16 sweep missed — Task 6's first `../..` statement said repository root where the second correctly says the h-mad skill dir, the SIGPIPE rationale described the pre-AC-3.16 state as current, and AC-2.6 said "ten trials" over eight listed timings.
- v1.15: Impl-plan audit v18 (codex) — must stayed at 3 and ALL THREE were defects in the timeout scaffold this plan had just rewritten. AC-2.6's `>= 0.5 s` lower bound REJECTS the correct implementation: _cmd_run's watchdog rides bash's integer SECONDS, and the audit's own controlled run produced a valid rc-124 at 0.376 s. The lower bound is gone, replaced by an argv-capture assertion that the read was attempted -- deterministic, and it does the job the bound was reaching for. The upper bound moved 2.5 -> 1.5 s to DISCRIMINATE the override: measured, --timeout 1 lands 0.376-1.16 s and --timeout 2 lands 1.936-2.232 s, so the old window contained both and the explicit-override contract was green without being enforced; `timeout-override-ignored` is the mutation that now proves it (25 mutations). `harness-ambient-timeout-not-scrubbed` was a FIFTH equivalent mutant, introduced by v1.14 -- the cycle that added it to CLOSE a coverage gap. Seeded at 9, both sides of the mutation complete a healthy read and the node asserts only rc 0, so nothing observable changes. The seed is 0 now, which the bounder rejects outright: measured, --timeout 0|notanumber|"" all exit rc 2 in ~0.04 s, so unscrubbed the helper returns 1 and the assertion fails. AC-2.7's predicate missed the quoted command forms `"timeout" 2 orca` -- it demands whitespace after `timeout` and a closing quote sits there. The obvious repair (optional quotes each side) repeats the v1.0 mistake: measured, it matches 10 lines of the valid file, because a quoted VARIABLE EXPANSION (`"$timeout"`) is not a command. Matched-pair alternation only: 0 live hits, 13/13 invocations caught, 0/7 false positives. Task 6's prose also called all six of these 'helper guards' when one mutates the Python test harness, and the harness mutation's _mechanism still named AC-2.1b.
- v1.16: Impl-plan audit v19 (codex) — must went UP, 3 -> 5, and the first was self-inflicted: v1.15 removed AC-2.6's >= 0.5 s lower bound in the opening and left the trailing paragraph asserting "0.5 still rejects an instant return, which is the only thing the lower bound is for". Two mutually exclusive instructions in one AC; the later one reinstates the bound that the same AC proves rejects correct code. AC-2.6 is rewritten around a FUNCTION SEAM: shadow _cmd_run in the strip-main harness and assert the recorded argv carries --timeout 1 under the override and --timeout 2 unset. That is deterministic where the < 1.5 s threshold was not -- scheduler delay can push a correct --timeout 1 run past it -- and it kills timeout-override-ignored, timeout-default-dropped and time-bound-removed without any timing at all; the loose < 2.5 s bound stays as a second witness of the last. TWO safety gaps closed. _orca_tail_sig accepted an exit-0 `ok:false` envelope: rc and key-presence both read fine, so neither AC-2.2 nor AC-2.3 covered it, and a stale banner inside a FAILED read would have become identity evidence -- the one FR-4 direction that RESOLVES rather than declines. The .ok gate goes in first (verified: a real terminal read --json carries top-level ok:true, and _cmd_worktree_rm already guards this F11 class at :1639), with AC-2.9 and envelope-ok-false-accepted. And test_skill_md_frontmatter_unchanged enforced only half its contract -- `any(startswith("description:"))` accepts an EMPTY description and any rewrite -- now pinned to the exact opening and a length floor, with skill-md-description-reworded to discriminate it. 27 mutations. The three manual mutate-and-restore procedures (AC-2.8, AC-5.4, AC-6.11) now require a re-read of the FILE after the edit and after the restore plus an empty git diff --stat: observing a test flip proves the test reacts to something, not that the file holds what you think, and a silent no-op or a failed restore looks identical to success. Source plan: Convention Prerequisites still said "confirm each new test fails against the unfixed wrapper" -- a blanket RED that would trigger step5d:red_not_all_failing -- while v1.7's history claimed the rule had been back-propagated out. The claim was in the changelog and the instruction was still in the body. AC-2.9 adds a node, so the counts were re-derived from the authoritative rows, not edited: 28 FAIL / 11 PASS over 39, T2 7/1, swept through the per-task list, the derivation comment, the plan and the design.
