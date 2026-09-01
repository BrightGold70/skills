# Implementation Plan: pin-agents-tail-banner

> Source: docs/02-design/features/pin-agents-tail-banner.design.md (post-audit, v1.11)
> Paired spec: docs/01-plan/features/pin-agents-tail-banner.spec.md (v1.5, 14 ACs)
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
consulted only when the variable is set, so all 284 existing tests keep the shared-stdout
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
    d = tmp_path / "reads"
    d.mkdir(exist_ok=True)
    for handle, text in envelopes.items():
        (d / f"{handle}.json").write_text(text, encoding="utf-8")
    return str(d)
```
`json` is already imported at the top of the module; no new import is needed.

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
   The design names the verb (`hmad-dispatch run --timeout … --`) to say *which* bounder, since
   `timeout`/`gtimeout` are forbidden unconditionally by the base invariant. Taken literally it
   would re-exec the wrapper by name, which is not on `PATH` inside the test harness
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
    body minus these lines, and calls _isolated_env(...) for the dict it used to
    assemble inline. Do NOT reimplement the scrubbing.
    """
    # (body: exactly the existing lines of run() from `e = dict(os.environ)`
    #  through the `e["PATH"] = …` assignment, unchanged)
    ...


def _run_bash(script, *, env=None, capture=None, cwd=None):
    e = _isolated_env(substrate="orca", env=env, capture=capture,
                      bindir=(env or {}).get("_BINDIR"))
    return subprocess.run(["bash", "-c", script], capture_output=True,
                          text=True, env=e, cwd=cwd)
```

`run()` then becomes `subprocess.run([...], env=_isolated_env(...))` over the same arguments it
builds today. The extraction is behaviour-preserving by construction, and the existing 284 tests
are its regression check — run them before and after and require an identical pass count.

`re` is **not** currently imported by `test_hmad_dispatch.py` (its imports are `atexit, json, os,
shutil, subprocess, tempfile, time, uuid, pathlib.Path` — verified), and AC-2.7's predicate needs
it. Add `import re` in alphabetical position.

**Code structure**:
```sh
_orca_tail_sig() {  # <handle> -> stdout: the pane's tail text; rc 0 = read ok, rc 1 = unreadable
  # Bounded via _cmd_run (the `run` verb's own function): `timeout`/`gtimeout` are
  # forbidden by the base invariant and are absent from this file. The default in
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
  printf '%s' "$raw" \
    | jq -re '(.result.terminal.tail? // empty)
              | if type == "array" then join("\n") else tostring end' 2>/dev/null \
    || return 1
}
```

**Acceptance Criteria**:
- [ ] AC-2.1: For a handle whose stubbed envelope carries `"tail":["alpha","beta"]`,
      `_orca_tail_sig <h>` exits 0 and its stdout contains both `alpha` and `beta` on separate
      lines.
- [ ] AC-2.2: When the stubbed `orca` exits non-zero for that handle, `_orca_tail_sig` exits 1 and
      writes nothing to stdout.
- [ ] AC-2.3: For a well-formed envelope with **no** `.result.terminal.tail` key (e.g.
      `{"ok":true,"result":{"terminal":{"handle":"h1"}}}`), `_orca_tail_sig` exits 1 and writes
      nothing to stdout — it does not emit the string `null`.
- [ ] AC-2.4: The captured argv for the call contains `terminal read`, `--terminal <h>`,
      `--cursor 0`, `--limit 4000` and `--json`. Asserted against `HMAD_STUB_CAPTURE`, not against
      the return value.
- [ ] AC-2.5: With `HMAD_TAIL_READ_TIMEOUT` **unset** in the child environment, the call still
      completes (rc 0 on a readable handle) rather than aborting the wrapper — the `set -u`
      default is exercised, not assumed.
- [ ] AC-2.6: With `HMAD_TAIL_READ_TIMEOUT=1` and the stub sleeping longer
      (`HMAD_STUB_ORCA_SLEEP=3`), `_orca_tail_sig` exits **1** (the helper maps the bounder's 124
      to its own unreadable code) and the call returns in **≥ 0.5 s and < 2.5 s**, measured with
      `time.monotonic()` around the subprocess.

      Both bounds are assertions, not prose. The **lower** bound is the one that matters: without
      it the test passes when the bounder never runs at all and the stub returns instantly, which
      is precisely the "the guard was never exercised" shape. The upper bound must stay below the
      stub's own 3 s sleep or it cannot distinguish "the timeout fired" from "the sleep finished
      on its own".

      **0.5, not 1.0 — measured, because `_cmd_run` fires EARLY.** Its watchdog is built on bash's
      integer-valued `SECONDS`, so a `--timeout 1` deadline can elapse anywhere inside the current
      second. Ten trials of `hmad-dispatch run --timeout 1 -- sleep 3` across two independent
      probes: **0.89, 0.89, 0.89, 0.90, 0.90, 1.15, 1.16, 1.16** s, every one `rc=124`. A
      `>= 1.0` assertion — the v1.6 wording — would have failed on the majority of runs against a
      perfectly correct implementation, and intermittently, which is the worst way for a test to
      be wrong. 0.5 still rejects an instant return, which is the only thing the lower bound is
      for.
- [ ] AC-2.7 (spec AC-4.3): No line of `h-mad/scripts/hmad-dispatch.sh` **invokes**
      `timeout`/`gtimeout` as a command. The predicate is *command position*, not substring
      presence, and is implemented in Python rather than as a shell `grep`:

      ```python
      _ARITH = re.compile(r"\$\(\(.*?\)\)")           # $(( timeout * 1000 )) is not a command
      # A word boundary that a HYPHEN and an UNDERSCORE both close: that is what
      # separates an invocation from `--timeout`, `--timeout-ms` and `run_timeout`.
      # Deliberately NOT an enumeration of preceding delimiters — see below.
      _INVOKE = re.compile(r"(?<![-a-zA-Z0-9_])g?timeout\s")

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

      The predicate above was then run against the file and both probe sets: **0 hits** on the
      current file; **11 of 11** invocation probes CAUGHT (the five keyword forms above plus
      `timeout 2 orca x`, `out="$(timeout 5 orca y)"`, `gtimeout 2 orca x`, `foo && timeout 3
      bar`, `(timeout 9 orca y)`, `x=1; timeout 4 orca q`); **0 of 6** false positives
      (`--timeout`, `--timeout-ms "$(( timeout * 1000 ))"`, `local timeout=600`, the
      `case … --timeout)` arm, `run_timeout` in a message, and a comment naming both binaries).
      The `_ARITH` strip is load-bearing for the lookbehind form specifically: without it,
      `$(( timeout * 1000 ))` has whitespace on both sides and matches.
- [ ] AC-2.8: The test above fails when `  timeout 2 orca terminal list` is inserted into the
      wrapper, and passes again when it is removed. Verified by doing it, not by inspection —
      a guard whose reject direction is never exercised is decoration.

**Dependencies on other tasks**: Task 1 (must complete first)

---

## Task 3: tail-evidence-pass

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`
**Task shape**: `new-behaviour`

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
      printf '%s' "$tout" | grep -Eiq "$tail_re" || continue
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
      through, same diagnostic.
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
      printf '%s' "$tout" | grep -Eiq "$tail_re" || continue
      # Reject BEFORE counting: a pane demonstrably running the other agent is
      # neither a match nor a source of ambiguity. Same predicate Pass 2 applies
      # to .preview; $rival_re is computed once above Pass 1.
      if [ -n "$rival_re" ] && printf '%s' "$tout" | grep -Eiq "$rival_re"; then
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
- [ ] AC-4.2: A single candidate carrying only the rival's signature yields no resolution from
      this pass: no handle, no stderr marker, fall through to the OS-evidence pass.
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
2. `h-mad/SKILL.md:320` reads "`_orca_find` joins them as **Pass 0**, ahead of the title and
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
    fields must not move."""
    head = SKILL_MD_TEXT.split("\n---\n", 2)
    assert head[0].startswith("---"), "SKILL.md must still open with frontmatter"
    fm = head[0]
    assert "name: h-mad" in fm
    assert "description:" in fm


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

**Dependencies on other tasks**: Task 4 (must complete first)

---

## Task 6: tail-pass-mutation-spec

**Production file**: `h-mad/tests/mutation-specs/tail_signature_pass.json`
**Test file**: `h-mad/tests/test_hmad_dispatch.py` (the tests the spec's mutations must kill)
**Task shape**: `new-behaviour`

**Description**: Design Implementation Order step 7. Every guard this feature introduces gets a
mutation that stubs it to its permissive value, and each mutation carries a `test` node id so a
kill is credited to the guard rather than to a crash, a timeout, or an unrelated assertion. The
spec's `root` is **relative** (`"../.."`, spec-relative, resolving to the repository root), never
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
   "find": "      if [ -n \"$rival_re\" ] && printf '%s' \"$tout\" | grep -Eiq \"$rival_re\"; then",
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
   "name": "resolve-on-ge-0",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_zero_matches_declines",
   "find": "  if [ \"$tn\" -eq 1 ]; then",
   "replace": "  if [ \"$tn\" -ge 0 ]; then"
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
  }
 ]
}
```

**The last two are the base invariant's bidirectional connection requirement, and neither is
covered by the eight above.** T2→T3 is a call-site connection: `_orca_find` calls
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
| AC-2.1 | `test_tail_sig_reads_array_tail` | RED: FAIL | — |
| AC-2.2 | `test_tail_sig_read_failure_returns_1` | RED: FAIL | — |
| AC-2.3 | `test_tail_sig_missing_tail_key_returns_1` | RED: FAIL | — |
| AC-2.4 | `test_tail_sig_argv_carries_cursor_and_limit` | RED: FAIL | — |
| AC-2.5 | `test_tail_sig_timeout_default_when_env_unset` | RED: FAIL | — |
| AC-2.6 | `test_tail_sig_times_out` | RED: FAIL | — |
| AC-2.7, AC-2.8 | `test_tail_no_timeout_binary_invocation` | RED: PASS | procedure AC-2.8: insert `timeout 2 orca …`, observe RED, remove |
| AC-3.1 | `test_tail_pass_resolves_single_vendor_banner` | RED: FAIL | — |
| AC-3.2 | `test_tail_pass_launch_command_alone_does_not_resolve` | RED: PASS | mut `tail-re-widened-to-launch-line` |
| AC-3.3 | `test_tail_pass_env_reports_handle` | RED: FAIL | — |
| AC-3.4 | `test_tail_pass_two_matches_declines` | RED: PASS | mut `resolve-on-ge-1` |
| AC-3.5 | `test_tail_pass_zero_matches_declines` | RED: PASS | mut `resolve-on-ge-0` |
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
| AC-4.1 | `test_tail_pass_rejects_rival_signature` | RED: FAIL | — |
| AC-4.2 | *withdrawn* | — | subsumed by `test_tail_pass_zero_matches_declines`: a rival-only tail fails the agent's own signature and never reaches the count, so NO mutation on rival rejection can discriminate it. Number retained so AC-4.1/4.3/4.4 do not renumber. |
| AC-4.3 | `test_tail_pass_rival_rejection_symmetric` | RED: FAIL | — |
| AC-4.4 | `test_tail_pass_rival_rejected_before_counting` | RED: FAIL | — |
| AC-5.1 | `test_os_evidence_pass_renumbered_to_four` | RED: FAIL | — |
| AC-5.2, AC-5.4 | `test_skill_md_names_tail_evidence_pass` | RED: FAIL | — |
| AC-5.3 | `test_skill_md_frontmatter_unchanged` | RED: PASS | mut `skill-md-frontmatter-renamed` |
| AC-6.11 | `test_tail_mutation_spec_root_is_relative` | RED: FAIL | — |

**The selector is `-k 'test_tail_ or test_skill_md or test_os_evidence'`** — it must cover all 35
nodes, T5's three included.

Two measurements and one correction stand behind that. `-k tail` is wrong: it already collects 2
of the module's 284 tests that have nothing to do with this feature
(`test_wait_snapshots_the_full_buffer_not_a_tail`,
`test_no_verdict_remedies_say_from_start_not_a_bigger_tail`), whose failure would be reported
against this feature's guards. But the narrow `-k 'test_tail_'` was wrong too, and impl-plan audit
v10 caught it: once `skill-md-frontmatter-renamed` was added, a mutation targeted
`test_skill_md_frontmatter_unchanged`, and the paragraph here still claimed "no mutation targets
them". The widened selector collects 0 of 284 today and adds no unrelated test, so it costs
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
      `h-mad/tests/mutation-specs/` directory, run under bash, prints `ANCHORS: ANCHORS_OK` with
      `drifted=0` — the new spec's anchors match exactly once each and no sibling spec was broken
      by this feature's edits.
- [ ] AC-6.11: The spec's `root` is the relative string `"../.."`, asserted by
      `tests/test_hmad_dispatch.py::test_tail_mutation_spec_root_is_relative`, which loads the
      JSON and asserts `not os.path.isabs(spec["root"])`. It is a real node, not a description:
      neither the mutation run nor `--check-anchors` rejects an absolute root that happens to
      resolve on this machine, so nothing else can catch the regression. Observe it fail after
      changing ONLY `root` to an absolute path, then restore.
- [ ] AC-6.12 … AC-6.18: one mutation per node that is green at RED, each named in the
      §"Test-name contract" proof column — `stub-branch-swallows-terminal-list`,
      `stub-branch-ignores-env-var`, `stub-branch-above-capture`,
      `tail-re-widened-to-launch-line`, `resolve-on-ge-0`, `tail-sig-fabricates-banner-on-failure`,
      `skill-md-frontmatter-renamed`. Each must be `caught`, and its `mechanism:` line must name
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
   | T2 | 7 | 6 | 1 | `test_tail_no_timeout_binary_invocation` |
   | T3 | 15 | 9 | 6 | `…launch_command_alone_does_not_resolve`, `…two_matches_declines`, `…zero_matches_declines`, `…not_run_when_pass0_resolves`, `…pool_is_scoped`, `…all_unreadable_declines` |
   | T4 | 3 | 3 | 0 | — |
   | T5 | 3 | 2 | 1 | `test_skill_md_frontmatter_unchanged` |
   | T6 | 1 | 1 | 0 | `test_tail_mutation_spec_root_is_relative`; the harness verdicts themselves are read from the `MUTATION:` token, not from pytest counts |
   | **total** | **35** | **24** | **11** | |

   **Derive these counts at dispatch time; do not read them from the table.** The count and the
   enumeration are two surfaces that drift, and this one has drifted once already. The
   authoritative form is the enumeration in §"Test-name contract", one row per node with a single
   `RED:` outcome; run

   ```bash
   F=docs/01-plan/features/pin-agents-tail-banner.impl-plan.md
   grep -cE '^\| AC-.* \| `test_.*` \| RED: (FAIL|PASS) \|' "$F"   # 35  total nodes
   grep -cE '^\| AC-.* \| `test_.*` \| RED: PASS \|'        "$F"   # 11  --expect-pass
   grep -cE '^\| AC-.* \| `test_.*` \| RED: FAIL \|'        "$F"   # 24  --expect-fail
   ```

   Those three numbers are the dispatch inputs; a count that disagrees with the enumeration is the
   enumeration's problem, not the dispatch's.

   **The v1.6 form of these commands returned 0 and 13.** They were
   `grep -c '^| \`test_'` (0 — every row starts with `| AC-…`, not the node) and an unanchored
   `grep -c 'RED: PASS'` (13 — it also matched prose outside the table). Their difference would
   have been passed to `--expect-fail` as **-13**, making the 5d dispatch invalid. Both are
   anchored to the full row shape above and verified to return 35 / 11 / 24 against this file.

   **Every node green at RED needs a discriminating reject-direction proof**, or the base
   Test-discrimination invariant is unmet. The v1.5 claim that "every such AC is named by a
   mutation" was **false**, verified against the spec: `local-masks-helper-rc` was retargeted to
   `…call_form_is_source_pinned` and so cannot prove `…all_unreadable_declines`;
   `resolve-on-ge-1` leaves zero-match behaviour untouched and so cannot prove
   `…zero_matches_declines`; and `…does_not_capture_terminal_list`,
   `…unset_preserves_legacy_behaviour`, `…still_captures_argv`,
   `…launch_command_alone_does_not_resolve` and `…frontmatter_unchanged` had no proof at all.
   T6 gains one mutation per uncovered node (AC-6.12 … AC-6.18); the mapping is in §"Test-name
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
   1. `hmad-dispatch pin-agents --clear` first, and confirm no `HMAD_ORCA_*_TERMINAL` is exported,
      so no pin can short-circuit resolution.
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
