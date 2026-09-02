# Implementation Plan: pin-agents-tail-banner

> Source: docs/02-design/features/pin-agents-tail-banner.design.md (post-audit, v1.42)
> Paired spec: docs/01-plan/features/pin-agents-tail-banner.spec.md (v1.20, 16 ACs)
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
| 1. `_orca_tail_sig` **and `_agent_tail_re`** + unit tests, incl. the matcher's direct 36/15 corpus | T2 | both helpers land together; step 2 consumes the matcher |
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
    # NOT `tempfile.mkdtemp`: this module's own guard
    # `test_no_mkdtemp_and_no_pin_file_leak_guard` asserts that literal is absent
    # from the source (measured at the first RED dispatch, 2026-09-02: 3 failed
    # instead of 2, the third being that guard). `uuid` is already imported.
    d = tmp_path / f"reads-{uuid.uuid4().hex[:8]}"
    d.mkdir()
    for handle, text in envelopes.items():
        (d / f"{handle}.json").write_text(text, encoding="utf-8")
    return str(d)
```
`json` and `uuid` are already imported at the top of the module; no new import is needed. (`tempfile` is imported too, but its `mkdtemp` is BANNED here by a live guard — see the helper's comment.)



**`Path(...)`, not `pathlib.Path(...)`.** The module's imports are `atexit, json, os, shutil,
subprocess, tempfile, time, uuid` and `from pathlib import Path` — verified in the live file —
so the bare name `pathlib` is not bound there and the dotted form raises `NameError` on the
FIRST call, before AC-1.5 tests anything about the stub. Impl-plan audit v16 caught it. Either
form is correct Python in isolation, which is exactly why a code block that is meant to be
followed verbatim has to name the binding the target module actually has.

**Acceptance Criteria**:
- [ ] AC-1.1: With `HMAD_STUB_ORCA_READ_DIR=<dir>` and `<dir>/term_x.json` present, invoking the
      **Node:** `test_tail_stub_read_dir_serves_per_handle`.
      stub as `orca terminal read --terminal term_x --cursor 0 --limit 4000 --json` writes that
      file's bytes to stdout and exits 0.
- [ ] AC-1.2: With the same variable set and `<dir>/term_y.json` **absent**, the same invocation
      **Node:** `test_tail_stub_read_dir_missing_handle_fails`.
      for `term_y` exits non-zero and writes nothing to stdout.
- [ ] AC-1.3: With the variable set, `orca terminal list --json` still returns
      **Node:** `test_tail_stub_read_dir_does_not_capture_terminal_list`.
      `HMAD_STUB_ORCA_STDOUT` verbatim — the new branch does not capture other verbs.
- [ ] AC-1.4: With `HMAD_STUB_ORCA_READ_DIR` unset, `orca terminal read … --json` behaves exactly
      **Node:** `test_tail_stub_read_unset_preserves_legacy_behaviour`.
      as before the change (`HMAD_STUB_ORCA_STDOUT` when set, else `{"ok":true,"result":{}}`).
- [ ] AC-1.5: `_orca_read_env("a", "b")` produces an envelope whose `.result.terminal.tail` is the
      **Node:** `test_tail_stub_read_helpers_shape`.
      JSON array `["a","b"]`, and `_orca_read_dir`, given a **two-handle** mapping
      (`{"h1": …, "h2": …}`), writes `h1.json` AND `h2.json`, each with its own content.

      **Two handles, not one.** `stub-read-dir-writes-one-file` truncates the loop to the first
      entry; against a one-entry fixture that mutant is EQUIVALENT and its green-at-RED proof
      survives — the seventh equivalent mutant this plan would have shipped. Impl-plan audit v32.

      **Green at RED, necessarily — it cannot be observed failing.** Both helpers are TEST-FILE
      helpers that T1's own RED patch introduces, so the node passes the moment the patch lands;
      withholding them yields a `NameError`, which is a missing-symbol failure rather than a
      behavioural one, and would force test implementation during GREEN. Classifying it `RED:
      FAIL` made T1's 3/3 split and the 29/11 aggregate unsatisfiable — a correct dispatch would
      have halted on `red_not_all_failing`. Impl-plan audit v23. It therefore carries mutation
      proof instead: `stub-read-env-not-array` and `stub-read-dir-writes-one-file`, one per
      asserted property, both pinned to this node.
- [ ] AC-1.6: The stub still appends its argv line to `HMAD_STUB_CAPTURE` for a `terminal read`
      **Node:** `test_tail_stub_read_still_captures_argv`.
      call, **including the missing-file case that exits 1** — AC-2.4, AC-3.6, AC-3.7 and AC-3.10
      all assert on that capture, and AC-3.10 in particular must be able to see that a read WAS
      attempted for a handle the stub then failed. The new branch must therefore sit below the
      existing capture line at the top of the file, not above it.

**Dependencies on other tasks**: None

---

## Task 2: orca-tail-sig-helper + tail matcher

**Task 2 also ships `_agent_tail_re`, at top level beside `_orca_tail_sig`.** Both are pure
helpers, both unit-testable alone, and neither is consumed until T3 — which is what lets T3's two
wires have a caller-observable RED (audit v30/v31). The definition belongs HERE, once; T3 carries
only the call sites.

```sh
# ONE helper, used for BOTH the wanted and the rival matcher. Two reasons, and
# the second is a defect audit v28 found: duplicating the pattern in two arms
# lets the wanted and rival rules drift, and Task 4's rival check was still
# using the SHARED `_agent_pv_re` over the whole retained tail -- so a real
# codex pane whose scrollback merely said "Compare Gemini 3.1 Pro with Claude"
# was rejected as rival-bearing. Prose is not a signature in either direction.
#
# FIVE revisions; each fell to a shape the previous corpus lacked. v1.25's
# line-complete form still took `## OpenAI Codex v0.145` (the prefix class
# allowed '#'), `OpenAI Codex v0.145-release-notes` and
# `model: gpt-5-migration-notes` (unbounded non-space version/model suffixes),
# and `Gemini 3.1 Pro (2026 release notes)` (an open numeric parenthetical).
# Now: a banner may be DECORATED -- framed by box-drawing, preceded by block
# art, or preceded by the Codex `>_` prompt glyph -- and may close with a frame
# character. A bare Markdown `>` is still NOT prefix evidence; `>_` is a unit.
# What still discriminates banner from prose is what follows the signature:
# the same per-arm version/model/effort structure, or end of line. Measured
# over 36 negatives and 15 positives: 36/36 decline, 15/15 still match.
#
# LINE-COMPLETE grammar, not a line anchor. The v1.23 anchor was falsified by
# line-LEADING prose; the v1.24 grammar was falsified by prose AFTER a
# banner-like prefix (`OpenAI Codex v0.145 release notes`,
# `gpt-5.6-terra high performance notes`, `Gemini 3.1 Pro (release notes)`).
# A banner shape must consume its WHOLE line. The continuations are PER-ARM,
# not one list -- `model:` and `·`+cwd are codex-only, the effort/version
# parenthetical is agy-only; the arms below are normative and no prose restates
# them (design v1.32 carries the per-arm table). MATCHED CASE-INSENSITIVELY:
# these literals are lowercase and real banners are capitalised, so every call
# site uses `grep -Eiq`; under `grep -E` 12 of the 15 positives decline.
# Measured over the corpus, which grew 24 -> 29 (v42) -> 35 (v45) -> 36 negatives /
# 15 positives after the Phase 5 live-banner check. On the
# THEN-24: unanchored 0/24 decline, anchored-only 7/24, leading-position 14/24,
# line-complete 19/24, that grammar 24/24. On the CURRENT 36, which adds the
# unbalanced-paren, non-dotted-version, Markdown-prefix and bare-separator
# shapes: this grammar 36/36 -- with all 15 positives matching.
_agent_tail_re() {   # <codex|agy> -> tail-only banner/status grammar
  case "$1" in
    codex) printf '%s\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\(v?[0-9]+(\.[0-9]+)+\)|v?[0-9]+(\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;
    agy)   printf '%s\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\((low|medium|high|xhigh|v?[0-9]+(\.[0-9]+)+)\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;
    *)     printf '%s\n' "^[[:space:]]*([^[:alnum:]]{0,8}[[:space:]]*)?($(_agent_pv_re "$1"))" ;;
  esac
}
```

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`
**Task shape**: `new-behaviour`

**Description**: Add the private helper `_orca_tail_sig <handle>`, which reads one pane's oldest
retained scrollback under a time bound and echoes it, or fails. It and `_agent_tail_re` are added
together — two pure helpers, neither consumed until T3 — with no
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
   non-zero (4). **Since v1.17 that guard is REDUNDANT and is kept only as defence in depth**:
   the type branch now ends `else empty`, so a `null` from an absent key is discarded there
   anyway. Measured as a controlled pair on four inputs (missing key, array tail, string tail,
   `ok:false`) — with and without `// empty` the filter is byte-identical, rc 4/0/4/4 both ways.
   It is therefore NOT independently pinned by any mutation, and impl-plan audit v21 was right to
   reject the one that claimed to pin it. Do not re-add a mutation for it without first changing
   the type branch back.
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
    # Same reason, and this one is test-only: an ambient export would opt EVERY
    # legacy `terminal read` test into the per-handle branch, so the "existing
    # 290 tests still pass" claim would depend on the developer's environment.
    e.pop("HMAD_STUB_ORCA_READ_DIR", None)
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
  # `jq -e` exits non-zero. `-e` is load-bearing, but NOT for the reason this
  # comment used to give: with `// empty` and the final `else empty` in place,
  # `jq -r` on a missing tail emits zero bytes at rc 0 (measured), not the
  # literal "null". The literal-null result belongs to the simpler
  # `.result.terminal.tail | tostring` form used in the measurement probes. The
  # hole `-e` actually closes is the rc: without it, empty output exits 0 and
  # the caller reads an unreadable pane as a readable empty one. The `// empty` itself is now REDUNDANT -- the
  # type branch ends `else empty` and discards a null anyway (measured identical
  # on four inputs) -- and is kept as defence in depth against that branch
  # changing back. No mutation pins it; see AC-6.2.
  # `.ok` FIRST. An Orca error envelope exits 0 and still carries a `result`
  # object, so rc and key-presence both say "fine" while the payload is an error
  # -- the F11 class `_cmd_worktree_rm` is already guarded against at :1639. Here
  # it is worse than a wrong rc: partial or stale tail text inside a failed
  # envelope becomes IDENTITY evidence, and this pass resolves a handle from it.
  # That is the unsafe direction; every other FR-4 case declines. Verified
  # 2026-09-01 that a real `terminal read --json` carries top-level `ok: true`.
  #
  # `else empty`, NOT `else tostring`. The measured live shape is an ARRAY, and
  # `tostring` accepted every other non-null type -- a scalar, an object, a
  # number -- so a malformed payload that merely CONTAINS a banner became
  # identity evidence by the same unsafe route the .ok gate closes. Declining an
  # unexpected shape costs a resolution that the OS-evidence pass still gets.
  printf '%s' "$raw" \
    | jq -re 'if (.ok? // false) != true then empty
              else (.result.terminal.tail? // empty) end
              | if type == "array" then join("\n") else empty end' 2>/dev/null \
    || return 1
}
```

**Acceptance Criteria**:
- [ ] AC-2.1: For a handle whose stubbed envelope carries `"tail":["alpha","beta"]`,
      **Node:** `test_tail_sig_reads_array_tail`.
      `_orca_tail_sig <h>` exits 0 and its stdout is **exactly** `"alpha\nbeta\n"` — asserted by
      equality, not by containment.

      **"Contains both, on separate lines" accepts the wrong extraction.** That was the v1.12
      wording, and it is satisfied by the very bug the code comment above warns about: a bare
      `jq -r '.result.terminal.tail'` on a pretty-printed envelope prints `alpha` and `beta` on
      separate lines too — inside JSON array punctuation — so the AC would pass against an
      implementation with no `join("\n")` at all. Equality is what discriminates the array-aware
      join from the accident that looks like it. Impl-plan audit v17.

- [ ] AC-2.2: When the stubbed `orca` exits non-zero for that handle, `_orca_tail_sig` exits 1 and
      **Node:** `test_tail_sig_read_failure_returns_1`.
      writes nothing to stdout.
- [ ] AC-2.3: For a well-formed envelope with **no** `.result.terminal.tail` key (e.g.
      **Node:** `test_tail_sig_missing_tail_key_returns_1`.
      `{"ok":true,"result":{"terminal":{"handle":"h1"}}}`), `_orca_tail_sig` exits 1 and writes
      nothing to stdout — it does not emit the string `null`.
- [ ] AC-2.4: The captured argv for the call contains `terminal read`, `--terminal <h>`,
      **Node:** `test_tail_sig_argv_carries_cursor_and_limit`.
      `--cursor 0`, `--limit 4000` and `--json`. Asserted against `HMAD_STUB_CAPTURE`, not against
      the return value.
- [ ] AC-2.5: With `HMAD_TAIL_READ_TIMEOUT` **seeded in the PARENT process environment as the
      **Node:** `test_tail_sig_timeout_default_when_env_unset`.
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
      a second AC is what kept the node table intact at the time; it is 40 now, after AC-2.9 and AC-2.10.
- [ ] AC-2.6: Assert the timeout VALUE at a function seam, not on the wall clock. Using the
      **Node:** `test_tail_sig_times_out`.
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

- [ ] AC-2.12: `_agent_tail_re` is tested DIRECTLY against the full corpus **under a
      **Node:** `test_tail_matcher_corpus_decides_prose_vs_banner`.
      case-insensitive match (`grep -Ei`, the flag every call site uses)** — all 36 negative
      probes decline and all 15 positive controls match, per agent. **The fold is load-bearing
      and was named nowhere until v1.33.** The literals are lowercase and every real banner is
      capitalised: measured 2026-09-02 by running this plan's own block over this corpus, a
      case-SENSITIVE `grep -E` still declines 36/36 negatives but declines **12 of the 15
      positives** as well — only the three all-lowercase controls survive. So the decline half of
      the corpus cannot detect the error, and an implementer who reads AC-2.11's `grep -E` as the
      match semantics ships a matcher that rejects every real banner. Design pass 2026-09-02. T2 owns the helper, so T2
      proves its semantics; AC-2.11 only proves the regex is syntactically usable, and an
      always-matching valid ERE would satisfy it. Deferring the corpus to T3 left the helper
      "proven before anything consumes it" by a check that could not see what it matched.
      Impl-plan audit v33.
- [ ] AC-2.11: `_agent_tail_re codex` and `_agent_tail_re agy` each print a regex that `grep -E`
      **Node:** `test_tail_matcher_regex_is_accepted_by_grep`.
      ACCEPTS (rc 0 or 1 on any input, never rc 2), and the printed value ends with no trailing
      literal `\n`. **`grep -E` here is deliberate and is about SYNTAX only** — pattern
      acceptance does not depend on the case-folding flag, and this AC says nothing about what
      the regex matches. The semantics are AC-2.12's, and they are measured under `grep -Ei`;
      reading this line as the match contract is what hid the fold for eleven cycles. **Executed, not eyeballed.** The v1.26 form of this helper was prescribed with
      `printf '%s\\n'` and doubled `\\(` escapes: run verbatim it appended the literal bytes `\n`
      and `grep -E` rejected the pattern outright with `repetition-operator operand invalid` (rc
      2), so the classifier every measurement in this plan describes had NEVER EXECUTED as
      written — the numbers came from separate probe scripts with different escaping. Impl-plan
      audit v30. This AC exists so the prescribed source is what gets measured.
- [ ] AC-2.9: For an envelope that exits 0 but carries `"ok":false` **together with a plausible
      **Node:** `test_tail_sig_rejects_ok_false_envelope`.
      tail** (`{"ok":false,"error":{"code":"terminal_gone"},"result":{"terminal":{"handle":"h1",
      "tail":["OpenAI Codex v1.2"]}}}`), `_orca_tail_sig` exits 1 and writes nothing — the banner
      inside a failed envelope must never become identity evidence.

      This is the only FR-4 case whose failure direction is UNSAFE. A missing key, a non-zero
      exit and an unreadable pane all decline; an accepted error envelope RESOLVES, and resolves
      to whatever handle the stale payload happens to name. `rc` and key-presence both read
      "fine" here, which is why neither AC-2.2 nor AC-2.3 covers it. Impl-plan audit v19.

- [ ] AC-2.10: For an `ok:true` envelope whose `.result.terminal.tail` is **not an array**
      **Node:** `test_tail_sig_rejects_non_array_tail`.
      (`"tail": "OpenAI Codex v1.2"`, and separately `"tail": {"0":"OpenAI Codex v1.2"}`),
      `_orca_tail_sig` exits 1 and writes nothing.

      The measured live shape is an array; `else tostring` accepted every other non-null type and
      turned a malformed payload that merely CONTAINS a banner into identity evidence — the same
      unsafe direction as the `ok:false` envelope, reached through the type branch instead of the
      envelope verdict. Declining an unexpected shape costs nothing a resolution depends on: the
      OS-evidence pass still runs. Impl-plan audit v20.

**Dependencies on other tasks**: Task 1 (must complete first)

---

## Task 3: tail-evidence-pass

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`
**Task shape**: `wiring`
**WIRE 1**: `h-mad/scripts/hmad-dispatch.sh:_orca_find` → `_orca_tail_sig`
**WIRE-PIN 1**: `h-mad/tests/test_hmad_dispatch.py::test_tail_pass_resolves_single_vendor_banner`
**WIRE 2**: `h-mad/scripts/hmad-dispatch.sh:_orca_find` → `_agent_tail_re` (wanted matcher)
**WIRE-PIN 2**: `h-mad/tests/test_hmad_dispatch.py::test_tail_pass_prose_mentioning_agent_does_not_resolve`

**The numbers are load-bearing, not decoration.** Task 3 declares TWO connections. With bare
labels the gate parses both with suffix `None`, pairs BOTH wires with the LAST pin, and registers
both under the single identity `(pin-agents-tail-banner, Task 3)` — so the `_agent_tail_re` record
upserts the `_orca_tail_sig` one and the `_orca_find → _orca_tail_sig` connection vanishes from
`.h-mad/wires.jsonl` entirely. Measured 2026-09-02 before this fix: the registry held
`Task 3 → _agent_tail_re (wanted matcher)` and `Task 4 → _agent_tail_re (rival matcher)` and NO
`_orca_tail_sig` row, while the gate printed `WIREPIN: PASS tasks=6 wiring=2 unpinned=0
mislabeled=0  registration: registered=3 skipped=0`. It fails CLOSED — a lost connection and a
green verdict are the same output. Impl-plan audit v39 (codex).

**`_agent_tail_re` ships in TASK 2, not here.** Audit v30: with callee and call site both landing
in T3, the wire's RED could only ever fail on a missing symbol, which is precisely what a
`wiring` task's caller-observable rule forbids — the same shape AC-1.5 was reclassified for at
audit v23. T2 now delivers `_orca_tail_sig` AND `_agent_tail_re` (both pure helpers, both
unit-testable alone, neither consumed until here), so T3's two wires each connect to a callee
that already exists and whose own tests stay green when the connection is removed.

**Two wires, because this task makes two connections.** Audit v29: the matcher call
`tail_re="$(_agent_tail_re "$token")"` is a second caller→callee edge and was undeclared, so the
wire gate saw one wire where there are two and the matcher connection bypassed the
caller-observable RED and the connection-only mutation the invariant requires.
`wire-wanted-matcher-disconnected` is that mutation: it removes the call while leaving
`_agent_tail_re` defined and every T2 unit test green, and only AC-3.17 sees it — an empty
`$tail_re` matches every pane — so under AC-3.17's MIXED fixture both candidates match, the
count is 2, and the pass declines on AMBIGUITY. (It does not "resolve a prose-only tail": that
was true of the prose-ONLY fixture this AC carried before v1.30, and the sentence outlived the
fixture. The mutation's own `_mechanism` already says ambiguity; this surface did not. Impl-plan
audit v40.)

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
  local tail_re rival_tail_re tail_ids="" th tout tn tail_h
  # `_agent_tail_re` is defined in TASK 2 (top level, beside `_orca_tail_sig`).
  # T3 contains only the two CALL SITES, so each wire connects to a callee that
  # already exists and whose own tests stay green when the connection is removed.
  tail_re="$(_agent_tail_re "$token")"
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
      **Node:** `test_tail_pass_resolves_single_vendor_banner`.
      agent's **vendor/model banner** (`OpenAI Codex (v0.145.0)  model: gpt-5.6-terra` /
      `Antigravity CLI`) and no other pane's, `_orca_find <agent>` prints that handle on stdout
      and returns 0, **and** stderr carries `bound <handle> by tail evidence`. Both halves are
      asserted: the stderr marker is what proves the resolution came from this pass rather than
      from a neighbour.
- [ ] AC-3.2 (spec AC-1.2): A pane whose tail carries **only the launch command**
      **Node:** `test_tail_pass_launch_command_alone_does_not_resolve`.
      (`codex '--dangerously-bypass-approvals-and-sandbox'` /
      `agy '--dangerously-skip-permissions'`) and no banner does **NOT** resolve — no handle, no
      stderr marker, fall through.

      **This AC is inverted from its v1.0–v1.3 form and the inversion is the point.** It used to
      assert that a LAUNCH-COMMAND-only tail *also* resolves, on the design's claim that "both forms are accepted
      signatures because both are in `_agent_pv_re`". Measured 2026-09-01 with passing controls:
      neither launch line matches its own agent's pattern, while all four banner and status-line
      controls do. Spec v1.5 and design v1.8 carry the correction; asserting the negative here is
      what stops a later reader from "fixing" the regex back.
- [ ] AC-3.3 (spec AC-1.3): `hmad-dispatch env` reports `codex -> <handle>` rather than
      **Node:** `test_tail_pass_env_reports_handle`.
      `UNRESOLVED` for a pane that only the tail pass can identify (generic title, empty
      preview).
- [ ] AC-3.4 (spec AC-2.1): Two candidates whose tails both match → `_orca_find` prints no handle
      **Node:** `test_tail_pass_two_matches_declines`.
      from this pass and does **not** return non-zero from the pass itself; control reaches the
      OS-evidence pass, asserted by the final `resolved to N candidates` diagnostic on stderr
      **and by the ABSENCE of the `bound … by tail evidence` marker**.

      **`N` in that diagnostic is the Pass-1/2 candidate count, NOT `tn`.** The existing message
      at `hmad-dispatch.sh:620` is untouched by this feature and reports `$n`, so under this AC's
      own fixture — two tail matches, nothing found by title or preview — it reads `resolved to 0
      candidates` while two panes carried the signature. Assert the diagnostic's PRESENCE (the
      fall-through was reached), never its number, or the assertion says something false about
      which surface declined. Carrying `tn` into that message is deliberately NOT prescribed here:
      it is the pre-existing pass's line, and changing it would put an unmutated, untested edit in
      a task whose every guard is mutation-backed. Impl-plan audit v36.
- [ ] AC-3.5 (spec AC-2.2): Zero matching candidates → declines the same way: no handle, fall
      **Node:** `test_tail_pass_zero_matches_declines`.
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
      **Node:** `test_tail_pass_not_run_when_pass0_resolves`.
      issued at all** — asserted by grepping `HMAD_STUB_CAPTURE` for `terminal read` and
      requiring zero occurrences. It is asserted on the capture, never on the resolution, or the
      test merely restates Pass 0 and passes with this whole feature reverted.

      **The fixture must also blind Passes 1 and 2**, or the mutation this node exists to kill
      survives. `wire-force-fire-after-pass0` makes Pass 0 fall through; if the pane still has a
      matching title or preview, Pass 1 or Pass 2 resolves BEFORE the tail pass, no
      `terminal read` is issued, and the mutant passes the very assertion meant to catch it. Pin
      a generic non-matching title (`"zsh"`) and an empty/non-matching preview, so under the
      mutant the only remaining route to a resolution is the tail pass and the capture
      necessarily shows a `terminal read`. Impl-plan audit v21.
- [ ] AC-3.7 (spec AC-3.2): A pane that `$scoped` excludes — a different `worktreePath`, or the
      **Node:** `test_tail_pass_pool_is_scoped`.
      coordinator's own pane — is never selected by this pass even when its tail carries a
      perfect signature, and no `terminal read` is issued for its handle (asserted on the
      capture).
- [ ] AC-3.8 (spec AC-3.3, ambiguous half): With two panes whose titles both match `^agy` in one
      **Node:** `test_tail_pass_runs_on_ambiguous_title`.
      tab (so Pass 1 yields n>1 and Pass 2 is skipped), the tail pass still runs and resolves —
      proven by the stderr marker. This is the shape no current pass reaches.
- [ ] AC-3.9 (spec AC-3.3, no-lsof half): With `lsof` absent from the harness `PATH`
      **Node:** `test_tail_pass_runs_without_lsof`.
      (`_bindir:/usr/bin:/bin`; `lsof` is `/usr/sbin/lsof` on this platform, verified 2026-09-01),
      the pass still resolves and the stderr marker is present — i.e. the resolution did not come
      from the OS-evidence pass.
- [ ] AC-3.10 (spec AC-4.1): One readable matching candidate plus one candidate whose stubbed
      **Node:** `test_tail_pass_unreadable_candidate_excluded`.
      `terminal read` fails resolves to the readable one. The unreadable pane is excluded from
      the match set rather than counted as a non-match, and a `terminal read` WAS attempted for
      it (asserted on the capture, so "excluded" is not confused with "never read").
- [ ] AC-3.11 (spec AC-4.2): When every candidate is unreadable, the pass declines by falling
      **Node:** `test_tail_pass_all_unreadable_declines`.
      through — no handle, no stderr marker, and control reaches the OS-evidence pass.
      **Fixture is fixed by its mutation, not free:** exactly ONE unreadable candidate, resolving
      the `codex` token. `tail-sig-fabricates-banner-on-failure` emits a hardcoded `OpenAI Codex`
      on the failure path, so with two unreadable candidates the mutant fabricates two matches and
      still declines on ambiguity, and with an `agy` fixture it fabricates no wanted match at all —
      in both shapes the mutant SURVIVES and this node's green-at-RED proof is void.
- [ ] AC-3.12 (spec AC-5.1): A comment at the pass states the measured 2000-line cap, that agent
      **Node:** `test_tail_pass_retention_comment_present`.
      TUIs do not normally reach it, and that a shell-heavy pane is the case that fails to
      UNRESOLVED. Asserted by reading the source section, not by a bare substring search of the
      whole file.
- [ ] AC-3.13: `_orca_find`'s stdout on a tail resolution is the bare handle and nothing else —
      **Node:** `test_tail_pass_stdout_is_bare_handle`.
      no tail text, no `[H-MAD]` line. Asserted by exact equality against `<handle>\n`. This is
      what pins the **bare** `if _orca_tail_sig "$h"` idiom out of the implementation: that form
      streams the tail into stdout, so the equality fails.
- [ ] AC-3.14: The pass's call form is asserted **on the source**, not on behaviour: the wrapper
      contains the line `if tout="$(_orca_tail_sig "$th")"; then` and does **not** contain
      `if local tout=`. Read from `WRAPPER.read_text()` with whitespace collapsed, so a reindent
      does not fail it.

      **Exact test** — added at impl-plan audit v40 (agy), so this source assertion is
      prescribed the way AC-2.7's and Task 5's are rather than left to the implementer:

      ```python
      def test_tail_pass_call_form_is_source_pinned():
          # COMMENTS ARE STRIPPED FIRST, and that is not tidiness -- see below.
          code = [ln for ln in WRAPPER.read_text().splitlines()
                  if not ln.lstrip().startswith("#")]
          flat = " ".join(" ".join(code).split())
          assert 'if tout="$(_orca_tail_sig "$th")"; then' in flat
          assert "if local tout=" not in flat
      ```

      Whitespace is collapsed with `" ".join(text.split())` so a reindent does not fail it,
      and BOTH directions are asserted: the positive alone passes on a file that also contains
      the `local` form somewhere else, and the negative alone passes on a file that dropped the
      call entirely.

      **The comment strip is load-bearing: without it this test fails against a CORRECT
      implementation.** T3's own prescribed block bans the idiom BY NAME in a comment —
      `` # `if local tout="$(...)"` returns `local`'s status … `` — so the flattened source
      always contains the literal `if local tout=` and the negative assertion can never hold.
      Measured 2026-09-02 by flattening the prescribed block: substring present `True` without
      the strip, `False` with it. The v1.40 form of this block, added to satisfy audit v40's
      should-fix, shipped without the strip and was therefore a test that could only fail —
      impl-plan audit v41 (agy). A source assertion whose forbidden string is something the file
      is REQUIRED to document has to exclude the documenting surface, or the ban and its
      rationale cannot coexist. The `local-masks-helper-rc` mutation is still killed: it rewrites
      the ACTIVE line, which survives the strip.

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
      **Node:** `test_tail_pass_long_tail_early_signature_resolves`.
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
- [ ] AC-3.17 (spec AC-1.4, FR-1): **MIXED fixture, caller-observable.** Two candidates: one
      whose tail carries a real banner (`OpenAI Codex (v0.145.0)  model: gpt-5.6-terra`) and one
      whose tail carries only PROSE naming the agent (`OpenAI Codex documentation changed`).
      `_orca_find` resolves to the FIRST handle, with the stderr marker.

      **Why mixed and not prose-only.** A prose-only fixture does not resolve at T3 RED either —
      because the pass does not exist yet — so `test_tail_pass_prose_mentioning_agent_does_not_resolve`
      would PASS before any T3 code is written, and a WIRE-PIN that passes without its wire proves
      nothing. Impl-plan audit v33; the same shape as AC-1.5 (v23) and T4's backwards pin (v30).

      **The node's NAME is historical and is deliberately not changed.** Since v1.30 it asserts a
      successful RESOLUTION — to the real-banner pane, over a prose decoy — not a non-resolution,
      so `…_does_not_resolve` reads backwards. Renaming it would move a node id that the RED
      table, four mutation `test` pins and two WIRE-PINs all reference, i.e. churn across five
      surfaces to fix a label, and a rename that misses one surface silently un-pins a mutation.
      The AC text above and the mutation mapping are explicit about what it asserts; read those,
      not the name. Impl-plan audit v38 (codex) nit, decided rather than deferred.
      The mixed fixture fails in both directions that matter: before the pass exists nothing
      resolves, and with the matcher connection removed both candidates match, the count is 2, and
      the pass declines on ambiguity. The matcher's own 36/15 corpus is tested directly in T2
      (AC-2.12), so this node tests the CONNECTION and the pass-level selection, not the grammar.

      A candidate whose tail carries the agent's tokens only inside ORDINARY
      PROSE does **not** resolve. Corpus, measured 2026-09-01 — all 36 match the UNANCHORED
      regex and none matches the current bounded banner grammar (the anchor-only revision
      declined just 7 of the then-24, which is why the anchor was replaced — see the block in Task 2,
      which is normative):

      | probe | agent |
      |---|---|
      | `Release notes for OpenAI Codex are available` | codex |
      | `I am comparing model: gpt-5.6-terra with ours` | codex |
      | `see openai codex docs` | codex |
      | `we ran gpt-5.6-terra high on that repo` | codex |
      | `The Antigravity CLI documentation changed` | agy |
      | `Compare Gemini 3.1 Pro with Claude` | agy |
      | `about antigravity cli usage` | agy |
      | `OpenAI Codex documentation changed` | codex |
      | `model: gpt-5 migration notes` | codex |
      | `## OpenAI Codex release notes` | codex |
      | `OpenAI Codex is a coding agent` | codex |
      | `Antigravity CLI documentation` | agy |
      | `Gemini 3.1 Pro compared with Claude` | agy |
      | `## Gemini 3.1 Pro release notes` | agy |
      | `OpenAI Codex v0.145 release notes` | codex |
      | `OpenAI Codex (v0.145 release notes)` | codex |
      | `gpt-5.6-terra high performance notes` | codex |
      | `Antigravity CLI v1.2.3 release notes` | agy |
      | `Gemini 3.1 Pro (release notes)` | agy |
      | `## OpenAI Codex v0.145` | codex |
      | `OpenAI Codex v0.145-release-notes` | codex |
      | `model: gpt-5-migration-notes` | codex |
      | `Antigravity CLI v1.2.3-release-notes` | agy |
      | `Gemini 3.1 Pro (2026 release notes)` | agy |
      | `OpenAI Codex (v0.145.0` | codex |
      | `OpenAI Codex v0.145.0)` | codex |
      | `OpenAI Codex 2026` | codex |
      | `Antigravity CLI 2026` | agy |
      | `Gemini 3.1 Pro (2026)` | agy |
      | `OpenAI Codex (v2026)` | codex |
      | `> OpenAI Codex` | codex |
      | `: OpenAI Codex` | codex |
      | `\| model: gpt-5.6-terra` | codex |
      | `gpt-5.6-terra high ·` | codex |
      | `> Antigravity CLI 1.1.22` | agy |
      | `\| Gemini 3.1 Pro` | agy |

      **Group D — headings, hyphenated pseudo-versions, open parentheticals.** v1.25's line-complete rule still admitted a
      markdown heading (the prefix class allowed `#`), a hyphenated word posing as a
      version or model id (`v0.145-release-notes`, `gpt-5-migration-notes` — the suffixes
      were unbounded non-space runs), and an open numeric parenthetical. Tightened: the
      prefix admits only whitespace and box-drawing characters — NOT `>`, `:` or ASCII `|`,
      which v29 admitted as "quote" characters and audit v45 measured as Markdown — a version is
      dotted-numeric, a model id requires a DOTTED release number, and a parenthetical is
      an effort word or a version. Impl-plan audit v29.

      **Group B — prose AFTER a banner-like prefix, the shape that broke the leading-position
      grammar.** That grammar required the signature to start the line and then allowed anything
      to follow, so a real version string followed by ordinary words still matched. Audit v28.
      The rule is now LINE-COMPLETE: a banner must consume its whole line, allowing only the
      structured continuations its OWN arm permits — see the `_agent_tail_re` block in Task 2,
      which is normative, and the per-arm table in design §Detailed Design. This AC does not
      re-list them: a flat list read as shared across both agents and was wrong on three of five
      rows. FOUR corpus revisions, each adding one shape the previous corpus
      lacked: mid-sentence, line-leading, banner-prefixed, then (audit v42) unbalanced parentheses
      and non-dotted pseudo-versions. Measured across the then-24 — unanchored 0/24, anchored-only
      7/24, leading-position 14/24, line-complete 19/24, that grammar 24/24; across the current 36,
      this grammar declines 36/36.

      **Group C — LINE-LEADING, and why a bare anchor is not enough.** The
      v1.23 fix anchored the shipped regex to line start and this AC claimed prose then declined.
      Audit v27 falsified that: every probe in the original corpus happened to put the token
      mid-sentence, so the anchor separated the corpus without separating the CLASS. Measured
      over the then-24: unanchored 0/24 decline, anchored-only 7/24, the banner grammar 24/24 (36/36
      over the current 36-probe corpus). A
      negative corpus is only as strong as the shapes in it, and one shape was doing all the
      work.

      Positive controls in the same test, all still matching: `OpenAI Codex (v0.145.0)  model:
      gpt-5.6-terra`, `gpt-5.6-terra high · ~/repo`, `  OpenAI Codex (v0.145.0)`,
      `│ model: gpt-5.6-terra`, `OpenAI Codex v0.145.0`, `OpenAI Codex`,
      `Antigravity CLI v1.2.3`, `Gemini 3.1 Pro`, `  Antigravity CLI v1.2.3`,
      `gpt-5.6-terra high`, `Gemini 3.1 Pro (High)`, `Antigravity CLI 1.1.22` — **12 in all**,
      matching under every
      grammar revision, so the tightening costs no true positive.

      **This is a wrong-pane class, not a tidiness one.** `$scoped` includes ordinary shell
      panes, and tail evidence is explicitly HISTORICAL — so a plain shell that once ran
      `cat CHANGELOG` or printed release notes was resolvable AS THE AGENT, contradicting
      **FR-1 / spec AC-1.4** — the wrong-pane rule. NOT FR-2, which is only the exactly-one
      CARDINALITY rule: a single prose pane matching is one match, so FR-2 is satisfied while the
      resolution is still wrong. The plan's own v1.25 history corrected this label once already
      and the body kept the old one. Impl-plan audit v40.
      The plan claimed `_agent_pv_re` was "hardened against prose"; it is hardened against the
      two examples that motivated it (`comparing gpt-5 output with ours`, `the codex agent is
      running`, both still declining) and that was generalised into a safety premise it does not
      support. Impl-plan audit v26 falsified it 4/4 and the corpus above extends it to 7/7.

      `_agent_pv_re` itself is NOT changed: it is shipped and shared with Passes 1-2, whose
      inputs are short titles and previews rather than arbitrary scrollback. The anchor is
      applied by this pass alone, so no existing behaviour moves.

- [ ] AC-3.18: `_agent_pv_re`'s OWN source comment is corrected in the same edit. It currently
      **Node:** `test_tail_agent_pv_re_comment_matches_measurement`.
      asserts of its patterns that "neither occurs in ordinary prose about a model", which audit
      v26/v27/v29 falsified 24/24, and 36/36 over the corpus as it stands. Leaving it would ship a wrapper carrying two mutually exclusive
      statements — that comment and the tail pass's, five hundred lines apart. Replace the claim
      with what is measured: the patterns exclude the BARE-TOKEN and bare-model-id prose that
      motivated them, and do NOT exclude prose naming the product; the tail pass therefore
      applies its own banner grammar, and Passes 1-2 rely on their inputs being short titles and
      previews rather than scrollback. Behaviour of `_agent_pv_re` is unchanged — comment only.

      **Exact code** (replaces the final line of `_agent_pv_re`'s comment; every line above it in
      that comment is unchanged). Impl-plan audit v40 (agy) — the prose above described the
      replacement without prescribing it, which leaves the implementer inventing the wording an
      AC then asserts:

      ```sh
        # Both are structured. They exclude the BARE-TOKEN and bare-model-id prose that
        # motivated them ("comparing gpt-5 output with ours", "the codex agent is running",
        # both still declining) and NOT prose naming the product: measured 2026-09-01,
        # `Release notes for OpenAI Codex are available` and `The Antigravity CLI
        # documentation changed` MATCH, 36 of 36 such probes. That is safe for Passes 1-2,
        # whose inputs are short titles and previews; the tail pass reads arbitrary retained
        # scrollback and therefore uses its own line-complete grammar, `_agent_tail_re`.
      ```

**Dependencies on other tasks**: Task 2 (must complete first)

---

## Task 4: tail-pass-rival-rejection

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`
**Task shape**: `wiring`
**WIRE**: `h-mad/scripts/hmad-dispatch.sh:_orca_find` → `_agent_tail_re` (rival matcher)
**WIRE-PIN**: `h-mad/tests/test_hmad_dispatch.py::test_tail_pass_rejects_rival_signature`

**The pin is the REJECTION node, not the prose node — corrected at audit v30.** v1.26 pinned
`test_tail_pass_rival_prose_does_not_suppress`, which is backwards: removing the rival-matcher
call makes the rival check match nothing, so prose stops suppressing the wanted pane and that
node goes GREEN with the wire disconnected. A pin that passes when the connection is gone proves
nothing. `test_tail_pass_rejects_rival_signature` is caller-observable in the right direction —
with the wire removed a real rival BANNER is no longer rejected. AC-4.6 is consequently green at
RED and carries `rival-re-prose-unsafe` as its reject-direction proof instead.

**`wiring`, not `new-behaviour` — corrected at audit v29.** v1.25 gave this task a second call to
`_agent_tail_re`, for the rival side, and left the shape as `new-behaviour`; the gate therefore
never asked for a WIRE, a pin, or a connection mutation on it. The pin's RED reason is
caller-observable: with the connection removed the rival check falls back to matching nothing, so
a pane carrying rival PROSE is no longer suppressed *and* a pane carrying a rival BANNER is no
longer rejected either — AC-4.6 and AC-4.1 move in opposite directions, which is what
distinguishes a real disconnect from a widened matcher.

**T4 also adds the rival TOKEN, which `_orca_find` does not have.** The existing function owns
`rival_re` — a REGEX, built from `_agent_pv_re` for Pass 1 — and nothing holds the rival's name.
`_agent_tail_re "$rival"` therefore expands an unbound variable, and the wrapper runs under
`set -euo pipefail` (line 5), so the FIRST candidate carrying the wanted signature aborts
`_orca_find` instead of performing rival rejection. Introduced at v1.25 and caught by impl-plan
audit v35. Extend the existing case rather than adding a second one:

```sh
  local rival_re="" rival=""
  case "$token" in
    codex) rival_re="$(_agent_pv_re agy)";   rival=agy   ;;
    agy)   rival_re="$(_agent_pv_re codex)"; rival=codex ;;
  esac
```

**The rival matcher is computed in PASS 3, after T3's `local` line — NOT here.** v1.35 put the
assignment in this Pass-1 case block and that was a silent, self-inflicted defect, caught by BOTH
v37 surfaces independently: T3 later executes `local tail_re rival_tail_re …`, and in bash a
`local` re-declaration RESETS the name, so the value assigned up here is wiped before the tail
pass ever reads it. `[ -n "$rival_tail_re" ]` is then false for every candidate and rival
rejection never fires — AC-4.1/4.3/4.4/4.5 cannot pass under the prescribed code, and nothing
errors. Controlled probe, run twice independently:

```
f() { rival_tail_re=COMPUTED; echo "[$rival_tail_re]"      # -> [COMPUTED]
      local tail_re rival_tail_re tail_ids=""; echo "[$rival_tail_re]"; }   # -> []
```

The v36 (agy) finding this replaces asked only for the assignment to leave the candidate LOOP;
moving it out of the tail pass entirely was my over-correction. It goes immediately below T3's
declaration and above the loop, which satisfies the once-per-call point without crossing a
`local`:

```sh
  # Pass 3. Everything above the last line is T3's, reproduced VERBATIM so the
  # context matches the source file; T4 adds only `rival_tail_re`.
  local tail_re rival_tail_re tail_ids="" th tout tn tail_h
  # `_agent_tail_re` is defined in TASK 2 (top level, beside `_orca_tail_sig`).
  # T3 contains only the two CALL SITES, so each wire connects to a callee that
  # already exists and whose own tests stay green when the connection is removed.
  tail_re="$(_agent_tail_re "$token")"
  rival_tail_re=""
  if [ -n "$rival" ]; then
    rival_tail_re="$(_agent_tail_re "$rival")"
  fi
```

The mutation anchors on this line are `    rival_tail_re="$(_agent_tail_re "$rival")"` — FOUR
spaces, because v1.54 moved the assignment inside the `if [ -n "$rival" ]` guard and re-anchored
the three mutations that point at it in the same edit. (This paragraph said "two-space, unaffected"
from v1.37 to v1.55, which was true then and false after v1.54 — the exact re-anchor discipline it
describes, applied to itself late. Impl-plan audit v50, codex.) The harness anchors on the string,
so indentation is part of the anchor.

`rival` stays empty for any other token — and that empty token must NOT reach `_agent_tail_re`.
The pre-v54 text said the `*)` arm "degrades to the shared helper"; measured 2026-09-02 it does
the opposite: `_agent_pv_re ""` prints an empty string, the arm wraps it as
`^[[:space:]]*([^[:alnum:]]{0,8}[[:space:]]*)?()`, which matches EVERY line, `[ -n "$rival_tail_re" ]`
is then true, and every candidate is rejected as a rival. The assignment is therefore guarded on
the TOKEN (`if [ -n "$rival" ]`), with an explicit `rival_tail_re=""` first — `local` alone leaves
the name UNSET, and `[ -n "$rival_tail_re" ]` on an unset name aborts under the wrapper's `set -u`.
Reachability is narrow (`_resolve_target` only ever passes `codex`/`agy`), which is why this went
unnoticed for nineteen cycles; it is fixed because the document claimed the opposite of what the
code does. Impl-plan audit v49 (agy). The rejection guard itself stays `[ -n "$rival_tail_re" ]`,
so an empty matcher still means "no rejection" and every rival-wire mutation keeps its meaning.

**Description**: Design Implementation Order step 3. A candidate whose tail carries the RIVAL
agent's signature is rejected **before** it is counted, so it can neither be selected nor create
a false ambiguity that suppresses a real resolution. The shared `$rival_re` computed above Pass 1
is NOT reused here — it is `_agent_pv_re`, which matches prose 36/36; this pass builds its own
`rival_tail_re` from `_agent_tail_re`, the same grammar as the wanted check (AC-4.6). The old
sentence said `$rival_re` was reused unchanged, which contradicted this task's own code block and
would have reproduced the false-negative. Impl-plan audit v30. The shared `$rival_re` computed in `_orca_find` is unchanged and still
used by Passes 1-2; only this pass substitutes `rival_tail_re`. Pass 2 applies the same RULE —
reject a rival-bearing candidate BEFORE counting it — to `.preview`, with its own matcher rather
than this one: saying "the identical predicate" contradicts the sentence directly above it, which
is what makes `_agent_tail_re` independent (impl-plan audit v41). It is the rule that is
inherited, not the regex, so
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
      # neither a match nor a source of ambiguity. This is the predicate Pass 2
      # applies, extended to the tail -- but built from _agent_tail_re, NOT from
      # the shared $rival_re computed above Pass 1: that one is `_agent_pv_re`,
      # which matches prose (36/36 measured), and this input is arbitrary retained
      # scrollback. Same grammar as the wanted check, or a real agent pane is
      # suppressed for merely MENTIONING the other agent -- a false negative in
      # the feature's own goal. Audit v28. HOISTED above the loop beside `tail_re`
      # (audit v36, agy): `$rival` is constant across candidates, so computing it
      # per matched candidate spawns one subshell each for the same value.
      if [ -n "$rival_tail_re" ] && grep -Eiq "$rival_tail_re" <<<"$tout"; then
        continue
      fi
      tail_ids="${tail_ids}${th}
"
    fi
```

**Acceptance Criteria**:
- [ ] AC-4.1 (spec AC-2.3): Two candidates, one carrying the agent's signature only and one
      **Node:** `test_tail_pass_rejects_rival_signature`.
      carrying BOTH that signature and the rival's, resolve to the first — the rival-carrying
      pane is rejected pre-count, so it neither wins nor makes the pass ambiguous. The stderr
      marker names the first handle.
- [ ] AC-4.2: **WITHDRAWN** — see §"Test-name contract". A rival-only tail fails the agent's
      own signature and never reaches the rejection branch, so no mutation can discriminate it;
      it is subsumed by `test_tail_pass_zero_matches_declines`. The number is retained so AC-4.1,
      AC-4.3, AC-4.4 and AC-4.5 do not renumber. **T4 has FIVE nodes** — AC-4.1, AC-4.3, AC-4.4,
      AC-4.5 and AC-4.6; the count said four until impl-plan audit v30, before AC-4.6 was added.
- [ ] AC-4.3: Rejection is symmetric — the same fixture resolved for `agy` rejects the pane whose
      **Node:** `test_tail_pass_rival_rejection_symmetric`.
      tail carries the codex banner, and vice versa. Asserted for both tokens so the test cannot
      pass against a one-sided implementation.
- [ ] AC-4.4: Rejection happens before counting, not after selection: with **two decoy candidates
      **Node:** `test_tail_pass_rival_rejected_before_counting`.
      that each carry BOTH the agent's signature AND the rival's**, plus one candidate carrying
      only the agent's, the pass still resolves to that one (count is 1, not 3). A post-count
      filter would have declined on ambiguity here.

      **The decoys must carry both signatures, and this AC is worthless if they do not.** A decoy
      carrying only the rival's signature fails the preceding `$tail_re` match and never reaches
      the count at all, so the test would pass identically whether rejection sits before or after
      counting — the exact placement this AC exists to pin. That was the v1.2 wording and it was
      vacuous.

- [ ] AC-4.5: **Two** candidates: a clean one whose tail carries only the agent's banner, and a
      **Node:** `test_tail_pass_long_tail_early_rival_rejected`.
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
- [ ] AC-4.6 (spec AC-1.4): **Green at RED — T4 depends on a completed T3, so the pass DOES exist;
      **Node:** `test_tail_pass_rival_prose_does_not_suppress`.
      the node passes because RIVAL REJECTION does not exist yet, so nothing suppresses anything.** Its reject-direction
      proof is `rival-re-prose-unsafe`. **Rival PROSE must not suppress a real resolution — both
      directions.** A codex pane whose tail carries `OpenAI Codex (v0.145.0)  model: gpt-5.6-terra`
      AND the sentence `Compare Gemini 3.1 Pro with Claude` still resolves as codex; symmetrically,
      an agy pane carrying `Antigravity CLI v1.2.3` AND `OpenAI Codex documentation changed` still
      resolves as agy. The real-rival-banner rejection (AC-4.1) is unchanged.

      Task 4 reused the SHARED `$rival_re` — that is `_agent_pv_re`, which matches prose 36/36 —
      over the whole retained tail. So the feature suppressed exactly the panes it exists to
      resolve, whenever their scrollback happened to mention the other agent. It is a false
      NEGATIVE, the mirror of the false positive AC-3.17 closes, and one matcher now serves both
      checks so they cannot drift apart. Impl-plan audit v28.

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
   **There is a SECOND site, mapped to the design's Components table since v1.33.** It was
   missing from that table when this paragraph was written, which is why the wording said so; the
   back-propagation landed and the sentence did not follow it (impl-plan audit v41). A value sweep of the
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

   **Exact code.** The replacement wording existed only inside the test's `_CODEX_CLAIM_NEW`
   constant, so the production edit was described in prose and prescribed nowhere — impl-plan
   audit v40 (agy). The markdown edit is:

   ```markdown
   never matches Codex on title — only on a fresh pane's `gpt-N` banner, which scrolls out of
   the PREVIEW once it works — the tail-evidence pass recovers it from retained scrollback.
   ```

   The test's `_CODEX_CLAIM_NEW` is the same string with the line wrap removed; both are read
   through the flattened `_SKILL_MD_FLAT`, so the wrap here is not part of the assertion.
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

**Third site — the Codex fallback sentence.** `hmad-dispatch.sh:513` reads "Codex therefore
skips Pass 1 entirely and relies on the preview signature or, properly, on a pin/launch." That
enumeration is exhaustive by construction and this feature adds a term to it — the tail signature
is precisely the evidence Codex now falls back to when the preview has decayed, which is the case
the whole feature exists for. Impl-plan audit v39 (agy).

```sh
  #     Codex therefore skips Pass 1 entirely and relies on the tail signature
  #     (Pass 3), on the preview signature, or, properly, on a pin/launch.
```

**Second site — same edit, exact code.** `hmad-dispatch.sh:1046`, the cross-reference from
`_orca_handle_live`'s neighbourhood to that same pass. AC-5.1 asserts it and the description names
it, but it had no prescribed block until v1.35; renumbering one site and not the other leaves the
file calling two different passes "Pass 3". Impl-plan audit v36 (agy).

```sh
  # would false-refuse healthy panes, the exact call `_orca_find` Pass 4 already
  # declines to make; and it protects no state, because there is none to protect.
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
    # Positive assertion, not only the negative one: deleting the false sentence
    # outright also satisfies `not in`, and the task contract is a CORRECTION,
    # not a removal. Impl-plan audit v22.
    assert "Reached when no pass above resolved exactly one handle" in src
    # The second site -- a design Components row since v1.33, not an unmapped edit.
    assert "`_orca_find` Pass 3 already" not in src
    assert "`_orca_find` Pass 4 already" in src
    # Third site: the Codex fallback enumeration, which this feature adds a term
    # to. Positive AND negative, for the same reason as the sentence above — a
    # deletion would satisfy `not in` alone while losing the enumeration.
    assert "relies on the preview signature" not in src
    assert "relies on the tail signature" in src
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
      then absent, the new phrase absent then present), and finish with `git diff --stat h-mad/SKILL.md`
      empty. **The path matters**: verification runs from the repository root and the mutated file
      is `h-mad/SKILL.md`; there is no root `SKILL.md`, so the v1.19 wording could report an empty
      diff while a failed restore sat in the real manifest. Impl-plan audit v31. Observing the test flip proves the test reacts to something; it does not prove the
      file holds what you think, and a failed restore leaves the manifest wrong in a tracked
      file. See AC-2.8.

**Dependencies on other tasks**: Task 4 (must complete first)

---

## Task 6: tail-pass-mutation-spec

**Production file**: `h-mad/tests/mutation-specs/tail_signature_pass.json`
**Test file**: `h-mad/tests/test_hmad_dispatch.py` (the tests the spec's mutations must kill)
**Task shape**: `new-behaviour`

**Description**: Design Implementation Order step 7. Every guard in the enumerated mutation table
below gets a mutation that stubs it to its permissive value, and each mutation carries a `test` node id so a
kill is credited to the guard rather than to a crash, a timeout, or an unrelated assertion. The
spec's `root` is **relative** (`"../.."`, spec-relative, resolving from
`h-mad/tests/mutation-specs/` to the `h-mad/` SKILL directory — NOT the repository root), never
absolute — an absolute root measures whichever checkout it names rather than the one under test,
and the pre-push anchor hook sweeps every tracked JSON, so a drifted or absolute anchor here
blocks unrelated pushes.

Verification for this task is the harness's own verdict, read from the `MUTATION:` token and
never `$?`, plus `--check-anchors` under **bash** (zsh does not word-split the candidate list and
reports `ANCHORS_NOTHING_SWEPT`).

**Code structure**: every `find`/`replace` value is an exact string from ONE of two sources, and
the distinction matters because only the first is pinned by this document:

1. **This plan's prescribed blocks** (T1, T2, T3, T4, T5) — the majority. An anchor here and the
   code there cannot drift, because both are the same bytes in one file.
2. **The LIVE file, for a mutation that targets code this feature does not prescribe** — exactly
   FOUR: `wire-force-fire-after-pass0` (Pass 0's `_orca_find_by_pane` entry),
   `stub-branch-above-capture` (the stub's pre-existing argv capture line),
   `skill-md-description-reworded` (SKILL.md's description field) and
   `skill-md-frontmatter-renamed` (SKILL.md's `name:` field — its anchor string also appears in
   this plan inside a test ASSERTION, which is why a naive blocks-or-live check counts it as
   class 1; an assertion is not a prescribed edit, and the live frontmatter is what the mutation
   rewrites. Impl-plan audit v47 (agy) caught the miscount.) These are NOT pinned by any
   block here, so an unrelated edit to `hmad-dispatch.sh`, the stub or `SKILL.md` can orphan them
   silently — the harness REFUSES on a non-matching anchor rather than failing, so the guard
   measures nothing while the spec still prints a verdict-shaped line.

   The check that covers both classes, and the one this plan actually ran at v1.46: resolve every
   `find` against the union of the prescribed blocks AND the live target file, and require 49/49.
   Impl-plan audit v45 (agy) — the previous wording claimed class 1 covered everything, which
   would have left these three unwatched.

`name`, `file` and `test` are literal.

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
   "_mechanism": "Drop `--cursor 0` from the read argv so the request returns the RETAINED VIEWPORT instead of the oldest retained scrollback. The banner this feature exists to find has already scrolled off the viewport, so the pass would read a tail that cannot contain it. Killed by `test_tail_sig_argv_carries_cursor_and_limit`, which asserts on the captured argv rather than on a resolution — a resolution assertion would pass whenever the banner happened to be in view.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_argv_carries_cursor_and_limit",
   "find": "--cursor 0 --limit 4000 --json",
   "replace": "--limit 4000 --json"
  },
  {
   "name": "jq-r-not-jq-re",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_missing_tail_key_returns_1",
   "_mechanism": "Drop the -e. jq then exits 0 on empty output, so an absent key, an ok:false envelope and a non-array payload all stop being unreadable. Re-anchored at audit v20: the .ok gate changed the filter's opening and this find matched nothing, which is silent -- an anchor that matches zero times reports the guard as enforced. Pinned node: `test_tail_sig_missing_tail_key_returns_1`.",
   "find": "| jq -re 'if (.ok? // false) != true then empty",
   "replace": "| jq -r 'if (.ok? // false) != true then empty"
  },
  {
   "name": "local-masks-helper-rc",
   "_mechanism": "Change `if tout=\"$(…)\"` to `if local tout=\"$(…)\"`. In bash `local` returns ITS OWN status, so the helper's non-zero rc is masked and an unreadable pane is treated as readable with an empty tail. Killed by `test_tail_pass_call_form_is_source_pinned`, which pins the call FORM in source rather than a behaviour, because the masked rc is invisible from outside whenever the tail is empty for legitimate reasons too.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_call_form_is_source_pinned",
   "find": "    if tout=\"$(_orca_tail_sig \"$th\")\"; then",
   "replace": "    if local tout=\"$(_orca_tail_sig \"$th\")\"; then"
  },
  {
   "name": "resolve-on-ge-1",
   "_mechanism": "Relax the uniqueness gate from `-eq 1` to `-ge 1`, so the pass resolves to the FIRST of several matching candidates instead of declining on ambiguity. Killed by `test_tail_pass_two_matches_declines`. This is the wrong-pane direction of FR-2: a wrong-but-live handle passes every liveness check afterwards.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_two_matches_declines",
   "find": "  if [ \"$tn\" -eq 1 ]; then",
   "replace": "  if [ \"$tn\" -ge 1 ]; then"
  },
  {
   "name": "wire-wanted-matcher-disconnected",
   "_mechanism": "Remove the wanted-matcher CALL, leaving _agent_tail_re defined and every T2 unit test green. $tail_re is then empty, `grep -Eiq \"\"` matches every pane, so AC-3.17's mixed fixture yields TWO matches and the pass declines on ambiguity instead of returning the banner's handle. Connection-only: the callee is intact, which is what a whole-module revert cannot establish. Pinned node: `test_tail_pass_prose_mentioning_agent_does_not_resolve`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_prose_mentioning_agent_does_not_resolve",
   "find": "  tail_re=\"$(_agent_tail_re \"$token\")\"",
   "replace": "  tail_re=\"\""
  },
  {
   "name": "wire-wanted-matcher-forced-empty",
   "_mechanism": "Force the wanted-matcher connection to produce a universal matcher instead of removing it: the call still happens, the callee is intact, but its result is discarded. Paired with wire-wanted-matcher-disconnected, this is the opposite direction the connection invariant asks for -- one proves the call is MADE, the other proves its RESULT is used. Pinned node: `test_tail_pass_prose_mentioning_agent_does_not_resolve`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_prose_mentioning_agent_does_not_resolve",
   "find": "  tail_re=\"$(_agent_tail_re \"$token\")\"",
   "replace": "  _agent_tail_re \"$token\" >/dev/null; tail_re=\".\""
  },
  {
   "name": "wire-rival-matcher-disconnected",
   "_mechanism": "Remove the rival-matcher CALL with the callee intact. Rival rejection then never fires, so a pane carrying a real rival BANNER is counted -- AC-4.1 fails. Paired with rival-re-prose-unsafe, which moves the other way: that one over-rejects, this one under-rejects, and only the two together pin the connection AND its matcher. Pinned node: `test_tail_pass_rejects_rival_signature`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_rejects_rival_signature",
   "find": "    rival_tail_re=\"$(_agent_tail_re \"$rival\")\"",
   "replace": "    rival_tail_re=\"\""
  },
  {
   "name": "wire-rival-matcher-forced-empty",
   "_mechanism": "The opposite direction for the rival wire. `wire-rival-matcher-disconnected` and `rival-re-prose-unsafe` both REMOVE the `_agent_tail_re` call from this line, so neither proves the call's RESULT is used. This one keeps the call and discards it, installing a universal matcher: every candidate then matches the rival grammar and is rejected pre-count, so the clean pane its pinned node (AC-4.6's `test_tail_pass_rival_prose_does_not_suppress`) expects to win resolves to nothing. The wanted side has carried this shape since v1.27 as `wire-wanted-matcher-forced-empty`; the rival side had no counterpart until impl-plan audit v37 (codex).",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_rival_prose_does_not_suppress",
   "find": "    rival_tail_re=\"$(_agent_tail_re \"$rival\")\"",
   "replace": "    _agent_tail_re \"$rival\" >/dev/null; rival_tail_re=\".\""
  },
  {
   "name": "rival-re-prose-unsafe",
   "_mechanism": "Restore the SHARED `_agent_pv_re` as the rival matcher over the retained tail. A real agent pane whose scrollback merely MENTIONS the other agent is then rejected as rival-bearing -- the false negative that suppresses exactly the panes this feature exists to resolve. Pinned node: `test_tail_pass_rival_prose_does_not_suppress`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_rival_prose_does_not_suppress",
   "find": "    rival_tail_re=\"$(_agent_tail_re \"$rival\")\"",
   "replace": "    rival_tail_re=\"$rival_re\""
  },
  {
   "name": "drop-rival-rejection",
   "_mechanism": "Replace the rival-rejection condition with `if false`, so a pane demonstrably running the OTHER agent is counted as a candidate. Killed by `test_tail_pass_rejects_rival_signature`. Distinct from the wire mutations on the assignment line: this one leaves `rival_tail_re` correctly computed and disables only its USE.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_rejects_rival_signature",
   "find": "      if [ -n \"$rival_tail_re\" ] && grep -Eiq \"$rival_tail_re\" <<<\"$tout\"; then",
   "replace": "      if false; then"
  },
  {
   "name": "pool-whole-listing",
   "_mechanism": "Iterate the whole `$listing` instead of `$scoped`, so candidates outside the current worktree enter the pool. Killed by `test_tail_pass_pool_is_scoped`. The failure is silent and cross-worktree: a stranger's pane resolves and every later dispatch goes to it.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_pool_is_scoped",
   "find": "$(printf '%s' \"$scoped\" | jq -r '.result.terminals[]?.handle')",
   "replace": "$(printf '%s' \"$listing\" | jq -r '.result.terminals[]?.handle')"
  },
  {
   "name": "marker-content-changed",
   "_mechanism": "Keep `>&2` intact and change the marker TEXT. Routing and content are separable guards on one line: `marker-to-stdout` proves the marker does not pollute stdout, and proves nothing about what it says. AC-3.1 and the live check both consume the exact phrase `bound <handle> by tail evidence` -- it is the only output that distinguishes a tail-pass resolution from any other pass -- so a reworded marker leaves both asserting on a string that no longer exists while stdout stays clean. Pinned node: `test_tail_pass_resolves_single_vendor_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_resolves_single_vendor_banner",
   "find": "    echo \"[H-MAD] $token: bound $tail_h by tail evidence\" >&2",
   "replace": "    echo \"[H-MAD] $token: bound $tail_h\" >&2"
  },
  {
   "name": "marker-to-stdout",
   "_mechanism": "Drop the `>&2` from the resolution marker so the human-readable line joins the handle on stdout. Killed by `test_tail_pass_stdout_is_bare_handle`. `_orca_find`'s stdout is a machine contract consumed by `_resolve_target`; a marker there corrupts the handle for every caller.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_stdout_is_bare_handle",
   "find": "    echo \"[H-MAD] $token: bound $tail_h by tail evidence\" >&2",
   "replace": "    echo \"[H-MAD] $token: bound $tail_h by tail evidence\""
  },
  {
   "name": "entry-gated-on-n-eq-0",
   "_mechanism": "Neutralise the matcher unless the title/preview passes found nothing (`[ \"$n\" -eq 0 ] || tail_re='__IMPOSSIBLE_…'`), which is the entry condition the pass must NOT have — an AMBIGUOUS title (n>1) is exactly the case this feature exists to resolve. Killed by `test_tail_pass_runs_on_ambiguous_title`. Deliberately neutralises only this pass's matcher and preserves fall-through: an earlier form used `|| return 1`, which aborted `_orca_find` and let the kill be credited to the forbidden early return rather than to the wrong entry condition (impl-plan audit v34).",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_runs_on_ambiguous_title",
   "find": "  tail_re=\"$(_agent_tail_re \"$token\")\"",
   "replace": "  tail_re=\"$(_agent_tail_re \"$token\")\"; [ \"$n\" -eq 0 ] || tail_re='__IMPOSSIBLE_MATCH__'"
  },
  {
   "name": "wire-disconnect-callee-intact",
   "_mechanism": "Remove the `_orca_tail_sig` CONNECTION while leaving the callee and its own tests intact (`if tout=\"\"; then`). Killed by `test_tail_pass_resolves_single_vendor_banner`: with no tail read, nothing carries a signature and the resolution the feature exists for never happens. The disconnect direction of the T3 wire; `wire-force-fire-after-pass0` is its force counterpart.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_resolves_single_vendor_banner",
   "find": "    if tout=\"$(_orca_tail_sig \"$th\")\"; then",
   "replace": "    if tout=\"\"; then"
  },
  {
   "name": "wire-force-fire-after-pass0",
   "_mechanism": "Force the tail pass to run even when Pass 0 already resolved exactly one handle (`if false && by_pane=…`). Killed by `test_tail_pass_not_run_when_pass0_resolves`, which asserts on `HMAD_STUB_CAPTURE` containing zero `terminal read` calls — asserting on the resolution instead would pass with the whole feature reverted, since Pass 0 resolves the same handle either way.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_not_run_when_pass0_resolves",
   "find": "  if by_pane=\"$(_orca_find_by_pane \"$token\" \"$scoped\" \"$scope_wt\")\" && [ -n \"$by_pane\" ]; then",
   "replace": "  if false && by_pane=\"$(_orca_find_by_pane \"$token\" \"$scoped\" \"$scope_wt\")\" && [ -n \"$by_pane\" ]; then"
  },
  {
   "name": "stub-read-env-not-array",
   "_mechanism": "Emit the tail as a joined STRING instead of a JSON array. The measured live shape is an array and production joins it, so a stub that models a string would let a non-array-rejecting implementation pass. Pins the first half of AC-1.5, which is green at RED because the helper is introduced by T1's own patch. Pinned node: `test_tail_stub_read_helpers_shape`.",
   "file": "tests/test_hmad_dispatch.py",
   "test": "tests/test_hmad_dispatch.py::test_tail_stub_read_helpers_shape",
   "find": "\"handle\": \"h\", \"tail\": list(lines), \"truncated\": False}}})",
   "replace": "\"handle\": \"h\", \"tail\": \"\\n\".join(lines), \"truncated\": False}}})"
  },
  {
   "name": "stub-read-dir-writes-one-file",
   "_mechanism": "Write only the FIRST mapping entry, so a handle the caller supplied is served as UNREADABLE. Several later ACs distinguish readable from unreadable candidates per handle; a stub that silently serves one would make those fixtures mean something other than what they say. Pins the second half of AC-1.5. Pinned node: `test_tail_stub_read_helpers_shape`.",
   "file": "tests/test_hmad_dispatch.py",
   "test": "tests/test_hmad_dispatch.py::test_tail_stub_read_helpers_shape",
   "find": "    for handle, text in envelopes.items():",
   "replace": "    for handle, text in list(envelopes.items())[:1]:"
  },
  {
   "name": "stub-branch-swallows-terminal-list",
   "_mechanism": "Widen the stub's read branch to match on `$1` alone, so `terminal list` is also swallowed by the per-handle read fixture. Killed by `test_tail_stub_read_dir_does_not_capture_terminal_list`. A stub that answers the wrong verb makes every downstream pool assertion measure the fixture instead of the code.",
   "file": "tests/stubs/orca",
   "test": "tests/test_hmad_dispatch.py::test_tail_stub_read_dir_does_not_capture_terminal_list",
   "find": "if [ \"${1:-}\" = \"terminal\" ] && [ \"${2:-}\" = \"read\" ] && [ -n \"${HMAD_STUB_ORCA_READ_DIR:-}\" ]; then",
   "replace": "if [ \"${1:-}\" = \"terminal\" ] && [ -n \"${HMAD_STUB_ORCA_READ_DIR:-}\" ]; then"
  },
  {
   "name": "stub-branch-ignores-env-var",
   "_mechanism": "Drop the `HMAD_STUB_ORCA_READ_DIR` guard so the new branch fires unconditionally, breaking every existing test that relies on the legacy stub path. Killed by `test_tail_stub_read_unset_preserves_legacy_behaviour` — the node that proves T1 is additive rather than a replacement.",
   "file": "tests/stubs/orca",
   "test": "tests/test_hmad_dispatch.py::test_tail_stub_read_unset_preserves_legacy_behaviour",
   "find": "&& [ -n \"${HMAD_STUB_ORCA_READ_DIR:-}\" ]; then\n  _h=\"\"",
   "replace": "; then\n  _h=\"\""
  },
  {
   "name": "stub-branch-above-capture",
   "_mechanism": "Delete the argv capture (`printf 'orca %s' \"$*\" >> $HMAD_STUB_CAPTURE` -> `true`), which is what an implementer does by placing the new branch ABOVE the capture line. Killed by `test_tail_stub_read_still_captures_argv`. Without the capture, every argv-based assertion in this plan silently measures nothing.",
   "file": "tests/stubs/orca",
   "test": "tests/test_hmad_dispatch.py::test_tail_stub_read_still_captures_argv",
   "find": "printf 'orca %s\\n' \"$*\" >> \"${HMAD_STUB_CAPTURE:-/dev/null}\"",
   "replace": "true"
  },
  {
   "name": "tail-re-cx-parens-unpaired",
   "_mechanism": "Codex arm, ONE field: make the version's parentheses independently optional again (`\\(?…\\)?`), keeping every version position dotted and everything else intact. Killed by `test_tail_matcher_corpus_decides_prose_vs_banner` on exactly `OpenAI Codex (v0.145.0` and `OpenAI Codex v0.145.0)`; all 15 positives still match, including the paired `(v0.145.0)` controls. Replaces the pre-v52 `tail-re-version-loosened`, which reverted this AND both dot rules at once and so could only prove that at least one of three guards bit — impl-plan audit v47 (codex).",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+\\(?v?[0-9]+(\\.[0-9]+)+\\)?)?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-cx-bare-version-undotted",
   "_mechanism": "Codex arm, ONE field: allow a bare (unparenthesised) version with zero dots again, parens still paired and the parenthesised form still dotted. Killed on exactly `OpenAI Codex 2026`; `OpenAI Codex v0.145.0` and `OpenAI Codex` still match. Impl-plan audit v47 (codex). Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)*))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-cx-paren-version-undotted",
   "_mechanism": "Codex arm, ONE field: allow a PARENTHESISED version with zero dots again, bare form still dotted. Killed on exactly `OpenAI Codex (v2026)` — a probe added at v1.52 because no earlier negative exercised this occurrence on its own; `OpenAI Codex (v0.145.0)` and `  OpenAI Codex (v0.145.0)` still match. Impl-plan audit v47 (codex). Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)*\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-agy-cli-version-undotted",
   "_mechanism": "Agy arm, ONE field: allow the Antigravity CLI version with zero dots again, the Gemini parenthetical still dotted. Killed on exactly `Antigravity CLI 2026`; `Antigravity CLI v1.2.3` and `Antigravity CLI 1.1.22` still match. Replaces the pre-v52 `tail-re-version-loosened-agy`, which loosened both agy positions together and so could not attribute a kill to either — impl-plan audit v47 (codex). Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-agy-paren-version-undotted",
   "_mechanism": "Agy arm, ONE field: allow the Gemini parenthetical version with zero dots again, the CLI version still dotted. Killed on exactly `Gemini 3.1 Pro (2026)`; `Gemini 3.1 Pro (High)` still matches because the effort alternative is untouched. Impl-plan audit v47 (codex). Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)*)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-prefix-box-only",
   "_mechanism": "Revert BOTH arms to the old prefix shape: whitespace plus box-drawing only, no block art and no `>_` prompt unit. The suffix grammar and closing-frame rule stay intact, so the kill is from real decorated banner positives only: the live Codex `│ >_ OpenAI Codex ... │` line and the two live Antigravity block-art lines stop matching. Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;\n    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' '^[[:space:]]*([│┃╎┆[:space:]]{0,6}[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;\n    agy)   printf '%s\\n' '^[[:space:]]*([│┃╎┆[:space:]]{0,6}[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-closing-frame-dropped",
   "_mechanism": "Revert BOTH arms to the old line ending `[[:space:]]*$`, leaving the decorated prefix unchanged. That makes framed banner tails fail when a closing box-drawing character follows the padded product line; killed by the live Codex positive `│ >_ OpenAI Codex (v0.149.1)                          │`. Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;\n    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*$)' ;;\n    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-bare-gt-prefix",
   "_mechanism": "Admit a bare `>` in BOTH arms' prefix class while keeping the real `>_` prompt unit valid. This is the guard on the guard: Markdown blockquotes are `> `, while the Codex TUI prompt glyph is `>_`; killed by the `> OpenAI Codex` negative before a bare quote can become identity evidence. Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;\n    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓>[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;\n    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓>[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-prefix-widened",
   "_mechanism": "Codex arm, ONE boundary: restore ASCII pipe and colon to the prefix class while preserving the decorated-banner prefix and the `>_` prompt unit. Everything else is preserved, so all 15 positives still match and the kill can only come from prefix-shaped prose: `: OpenAI Codex` or `| model: gpt-5.6-terra` in historical shell output becomes identity evidence, the FR-1 wrong-pane class. Killed by `test_tail_matcher_corpus_decides_prose_vs_banner` (AC-2.12), whose corpus carries those lines since impl-plan audit v45 (codex). Anchored on the whole arm so the anchor stays unique beside the prefix-only anchors the other regex mutants use. Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' '^[│|┃╎┆▄▀▐▌░▒▓:[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-cwd-optional",
   "_mechanism": "Make the cwd after `·` optional again (`[^[:space:]]*` for `+`) on the codex status-line alternative, preserving everything else. `gpt-5.6-terra high ·` -- an effort word and a bare separator, the shape a wrapped or truncated log line produces -- then matches. Killed by `test_tail_matcher_corpus_decides_prose_vs_banner` (AC-2.12); the design requires `·` PLUS a cwd, and the positive `gpt-5.6-terra high · ~/repo` matches under both forms, so the kill is from the negative alone. Impl-plan audit v45 (codex).",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-prefix-widened-agy",
   "_mechanism": "The AGY counterpart of `tail-re-prefix-widened`: restore ASCII pipe and colon to the agy arm's prefix class while preserving block-art decoration and the `>_` prompt unit, everything else preserved. All seven agy positives still match, so the kill can only come from `| Gemini 3.1 Pro` in AC-2.12's corpus. Bare `>` is pinned separately by `tail-re-bare-gt-prefix`, because `>_` is a unit and a Markdown blockquote must stay prose. Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    agy)   printf '%s\\n' '^[│|┃╎┆▄▀▐▌░▒▓:[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;"
  },
  {
   "name": "tail-re-unanchored",
   "_mechanism": "Drop the line anchor, restoring the shipped `_agent_pv_re` output as the tail matcher. All 22 CODEX-arm negatives then match (this mutant touches only the codex arm, so the 14 agy negatives are unaffected; measured 2026-09-02) and a plain shell pane that printed release notes or documentation resolves AS THE AGENT -- the wrong-pane class FR-1 / spec AC-1.4 forbids (the wrong-pane rule, NOT FR-2's cardinality rule), reachable because $scoped includes shell panes and tail evidence is historical. Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' \"$(_agent_pv_re codex)\" ;;"
  },
  {
   "name": "tail-re-unanchored-agy",
   "_mechanism": "Restore the shared `_agent_pv_re` output on the AGY arm only, leaving codex intact so the agy guard is isolated. No mutation had ever touched it, so half the classifier was unobserved (audit v32). all 14 AGY-arm negatives then match (measured 2026-09-02; the codex negatives are unaffected). Pinned node: `test_tail_matcher_corpus_decides_prose_vs_banner`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_matcher_corpus_decides_prose_vs_banner",
   "find": "    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    agy)   printf '%s\\n' \"$(_agent_pv_re agy)\" ;;"
  },
  {
   "name": "tail-re-widened-to-launch-line-agy",
   "_mechanism": "ADDITIVELY widen the AGY arm: the full banner grammar is preserved and `|^agy .--dangerously` appended, so every positive control still matches and the ONLY behaviour change is that the launch line is now accepted. A wholesale replacement (the v1.31 form) was killed because the node's positive controls failed -- an accidental kill that proves nothing about launch-line rejection. Audit v35. AC-3.2 exercises both agents. Pinned node: `test_tail_pass_launch_command_alone_does_not_resolve`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_launch_command_alone_does_not_resolve",
   "find": "    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    agy)   printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(antigravity cli([[:space:]]+v?[0-9]+(\\.[0-9]+)+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|gemini [0-9]+(\\.[0-9]+)*([[:space:]]+(pro|flash|ultra))?([[:space:]]*\\((low|medium|high|xhigh|v?[0-9]+(\\.[0-9]+)+)\\))?[[:space:]]*[│┃╎┆]?[[:space:]]*$)|^agy .--dangerously' ;;"
  },
  {
   "name": "tail-re-widened-to-launch-line",
   "_mechanism": "ADDITIVELY widen the codex arm with `|^codex .--dangerously`, preserving the whole valid banner grammar, so only the launch-line rejection is lost. Killed by `test_tail_pass_launch_command_alone_does_not_resolve`, whose AC exercises both agents. The pre-v1.32 form replaced the arm wholesale and was killed by the node's POSITIVE controls failing — an accidental kill that proved nothing about launch-line rejection (impl-plan audit v35).",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_launch_command_alone_does_not_resolve",
   "find": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)' ;;",
   "replace": "    codex) printf '%s\\n' '^[│┃╎┆▄▀▐▌░▒▓[:space:]]{0,24}(>_[[:space:]]*)?(openai codex([[:space:]]+(\\(v?[0-9]+(\\.[0-9]+)+\\)|v?[0-9]+(\\.[0-9]+)+))?([[:space:]]+model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*)?[[:space:]]*[│┃╎┆]?[[:space:]]*$|model:[[:space:]]*gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]*[│┃╎┆]?[[:space:]]*$|gpt-[0-9]+(\\.[0-9]+)+[a-z0-9-]*[[:space:]]+(low|medium|high|xhigh)([[:space:]]*·[[:space:]]*[^[:space:]]+)?[[:space:]]*[│┃╎┆]?[[:space:]]*$)|^codex .--dangerously' ;;"
  },
  {
   "name": "tail-sig-fabricates-banner-on-failure",
   "_mechanism": "Make the helper print a plausible banner and return 0 on a failed read. Killed by `test_tail_pass_all_unreadable_declines`. This is the one FR-4 direction that is UNSAFE: a missing key, a non-zero exit and an unreadable pane all decline, but a FABRICATED tail resolves — and resolves to whatever handle the failed read happened to name.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_all_unreadable_declines",
   "find": "  [ \"$rc\" -eq 0 ] || return 1",
   "replace": "  [ \"$rc\" -eq 0 ] || { printf '%s' \"OpenAI Codex\"; return 0; }"
  },
  {
   "name": "skill-md-frontmatter-renamed",
   "_mechanism": "Rename the skill's frontmatter `name:` key, which the T5 documentation edits sit beside. Killed by `test_skill_md_frontmatter_unchanged`. It exists so the doc-surface task cannot silently damage the skill's identity while editing prose in the same file.",
   "file": "SKILL.md",
   "test": "tests/test_hmad_dispatch.py::test_skill_md_frontmatter_unchanged",
   "find": "name: h-mad",
   "replace": "name: h-mad-renamed"
  },
  {
   "name": "signature-check-not-enforced",
   "_mechanism": "Turn the wanted-signature filter into a no-op (`|| true` instead of `|| continue`), so a READABLE but non-matching candidate enters `tail_ids`. Killed by `test_tail_pass_zero_matches_declines`, whose fixture is deliberately ONE readable non-matching candidate: with the filter dropped, `tn` becomes 1 and the pass resolves observably WRONG. It replaced `resolve-on-ge-0`, which was a crash mutant — with `tn=0` the relaxed branch aborts under `set -euo pipefail`, and a kill credited to an abort proves the code breaks when broken and nothing about the property.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_zero_matches_declines",
   "find": "      grep -Eiq \"$tail_re\" <<<\"$tout\" || continue",
   "replace": "      grep -Eiq \"$tail_re\" <<<\"$tout\" || true"
  },
  {
   "name": "wanted-check-back-to-pipeline",
   "_mechanism": "Revert the wanted check from a here-string to `printf … | grep -Eiq`. Under the wrapper's global `set -o pipefail` a MATCH exits grep early, the upstream printf takes SIGPIPE, and the pipeline returns 141 — so a candidate that DOES carry the signature is skipped. Killed by `test_tail_pass_long_tail_early_signature_resolves`, whose fixture puts the signature at line 1 of a long tail, which is the only shape that triggers it. Pinned to AC-3.16, a RED: FAIL node, so it is a long-tail guard discriminator rather than a green-at-RED proof.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_long_tail_early_signature_resolves",
   "find": "      grep -Eiq \"$tail_re\" <<<\"$tout\" || continue",
   "replace": "      printf '%s' \"$tout\" | grep -Eiq \"$tail_re\" || continue"
  },
  {
   "name": "rival-check-back-to-pipeline",
   "_mechanism": "The mirror of the above on the rival check: a pipeline there returns 141 on a MATCH, so a candidate carrying the RIVAL's signature fails its rejection test and is COUNTED. Killed by `test_tail_pass_long_tail_early_rival_rejected`. Pinned to AC-4.5, also a RED: FAIL node. Both directions are needed because the two checks fail in opposite ways from the same cause.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_pass_long_tail_early_rival_rejected",
   "find": "      if [ -n \"$rival_tail_re\" ] && grep -Eiq \"$rival_tail_re\" <<<\"$tout\"; then",
   "replace": "      if [ -n \"$rival_tail_re\" ] && printf '%s' \"$tout\" | grep -Eiq \"$rival_tail_re\"; then"
  },
  {
   "name": "tail-array-not-joined",
   "_mechanism": "Drop the array branch so a multi-line tail is stringified instead of joined. The measured live shape IS an array, so this is the extraction T2 exists to pin. Pinned node: `test_tail_sig_reads_array_tail`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_reads_array_tail",
   "find": "then join(\"\\n\") else empty end'",
   "replace": "then tostring else empty end'"
  },
  {
   "name": "timeout-default-dropped",
   "_mechanism": "Remove the `:-2` fallback. `set -u` is on, so the first call in a shell that never exported the variable aborts the whole wrapper rather than reading a tail. Pinned node: `test_tail_sig_timeout_default_when_env_unset`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_timeout_default_when_env_unset",
   "find": "  raw=\"$(_cmd_run --timeout \"${HMAD_TAIL_READ_TIMEOUT:-2}\" -- \\",
   "replace": "  raw=\"$(_cmd_run --timeout \"$HMAD_TAIL_READ_TIMEOUT\" -- \\"
  },
  {
   "name": "non-array-tail-accepted",
   "_mechanism": "Restore `else tostring`, so any non-array payload that survives the .ok gate is stringified and matched. A malformed tail that merely CONTAINS a banner then becomes identity evidence -- the same unsafe direction as the ok:false envelope, reached through the type branch instead. Pinned node: `test_tail_sig_rejects_non_array_tail`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_rejects_non_array_tail",
   "find": "              | if type == \"array\" then join(\"\\n\") else empty end'",
   "replace": "              | if type == \"array\" then join(\"\\n\") else tostring end'"
  },
  {
   "name": "envelope-ok-false-accepted",
   "_mechanism": "Drop the .ok gate so an exit-0 error envelope's tail is extracted. The pass then resolves an identity from a FAILED read -- the one FR-4 direction that resolves instead of declining. Pinned node: `test_tail_sig_rejects_ok_false_envelope`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_rejects_ok_false_envelope",
   "find": "    | jq -re 'if (.ok? // false) != true then empty\n              else (.result.terminal.tail? // empty) end",
   "replace": "    | jq -re '(.result.terminal.tail? // empty)"
  },
  {
   "name": "skill-md-description-reworded",
   "_mechanism": "Reword the manifest description's opening. `any(startswith(\"description:\"))` -- the v1.13 assertion -- accepts it, and accepts an empty description too, so half the manifest contract this node claims to pin was unenforced. Pinned node: `test_skill_md_frontmatter_unchanged`.",
   "file": "SKILL.md",
   "test": "tests/test_hmad_dispatch.py::test_skill_md_frontmatter_unchanged",
   "find": "description: Orchestrate the 7-phase H-MAD",
   "replace": "description: Runs the H-MAD"
  },
  {
   "name": "timeout-override-ignored",
   "_mechanism": "Hardcode the bound at 2, ignoring the caller's override. The read still succeeds on a healthy pane and still times out on a hung one, so no wall-clock window sees it reliably. AC-2.6's _cmd_run argv SEAM does: the recorded call carries --timeout 2 where 1 was asked for. v1.15 tried to discriminate this with a `< 1.5 s` threshold; v1.16 replaced that with the seam because scheduler delay can push a correct run past it. Pinned node: `test_tail_sig_times_out`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_times_out",
   "find": "  raw=\"$(_cmd_run --timeout \"${HMAD_TAIL_READ_TIMEOUT:-2}\" -- \\",
   "replace": "  raw=\"$(_cmd_run --timeout 2 -- \\"
  },
  {
   "name": "time-bound-removed",
   "_mechanism": "Call orca directly with no bounder. A hung `terminal read` then stalls every resolution -- the risk FR-4 was written against. Killed primarily by AC-2.6's argv seam, which records NO _cmd_run call at all; the loose `< 2.5 s` bound is a second, independent witness, since an unbounded call lets the stub's own 3 s sleep run to completion. Pinned node: `test_tail_sig_times_out`.",
   "file": "scripts/hmad-dispatch.sh",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_times_out",
   "find": "  raw=\"$(_cmd_run --timeout \"${HMAD_TAIL_READ_TIMEOUT:-2}\" -- \\",
   "replace": "  raw=\"$( \\"
  },
  {
   "name": "harness-ambient-timeout-not-scrubbed",
   "_mechanism": "Delete the scrub from the TEST harness. On a host exporting HMAD_TAIL_READ_TIMEOUT the child inherits it, AC-2.5 never reaches the ${:-2} default, and a build that dropped the fallback entirely would pass. Killed only because AC-2.5 seeds the ambient value 0, which the bounder rejects with rc 2 (measured): unscrubbed the helper returns 1 and the node's rc-0 assertion fails. A seed of 9 leaves both sides completing and makes this mutation EQUIVALENT -- that was the v1.14 form, caught by audit v18. Pinned node: `test_tail_sig_timeout_default_when_env_unset`.",
   "file": "tests/test_hmad_dispatch.py",
   "test": "tests/test_hmad_dispatch.py::test_tail_sig_timeout_default_when_env_unset",
   "find": "    e.pop(\"HMAD_TAIL_READ_TIMEOUT\", None)",
   "replace": "    pass"
  }
 ]
}

```

**FIVE mutations target T2's time-and-extraction controls — four in the wrapper, one in the
PYTHON TEST HARNESS — pinned to THREE nodes, and none of them is a green-at-RED proof.**

| mutation | file | node |
|---|---|---|
| `tail-array-not-joined` | wrapper | AC-2.1 |
| `timeout-default-dropped` | wrapper | AC-2.5 |
| `harness-ambient-timeout-not-scrubbed` | `tests/test_hmad_dispatch.py` | AC-2.5 |
| `time-bound-removed` | wrapper | AC-2.6 |
| `timeout-override-ignored` | wrapper | AC-2.6 |

The proof column exists to discriminate nodes that pass before any code is written; these three
nodes are RED: FAIL and need no such proof. They are mutated anyway because Task 6's own claim is
that every ENUMERATED guard in the table above is stubbed to its PERMISSIVE value. (The claim used
to be "every new guard", which is stronger than the inventory: several independently asserted
controls — the missing-file `exit 1`, the retention of `--limit 4000` and `--json` — carry no
mutation. They are RED: FAIL nodes and so still satisfy the base discrimination rule, but the
deliverable should not read as broader than what it lists. Impl-plan audit v26.) Audit v17 found
four that were not stubbed: the array `join("\n")`, the `${HMAD_TAIL_READ_TIMEOUT:-2}` default, the `_cmd_run` bound
itself, and the harness's ambient-environment scrub. Audit v18 added `timeout-override-ignored` —
the default and the bound were each mutated, but nothing mutated the caller's OVERRIDE being
honoured. A sixth, targeting `// empty`, was removed at audit v21: v1.17's `else empty` made it
EQUIVALENT.

Each is an INDEPENDENT control — removing any one leaves the other four intact and the pass still
resolving a healthy pane — so a whole-helper revert cannot stand in for them. **The counts in this
paragraph are the ones that went stale**: it said six mutations, five in the helper, four nodes,
while its own "the other four" implied five, and impl-plan audit v24 caught the contradiction. The
table above is now the enumeration, so the numbers and the list cannot drift apart. The rows above
also name each mutation, because the last time one targeted a node whose proof column said `—`,
the prose beside it still claimed no mutation targeted it (v10).

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
| AC-1.5 | `test_tail_stub_read_helpers_shape` | RED: PASS | muts `stub-read-env-not-array`, `stub-read-dir-writes-one-file` |
| AC-1.6 | `test_tail_stub_read_still_captures_argv` | RED: PASS | mut `stub-branch-above-capture` |
| AC-2.1 | `test_tail_sig_reads_array_tail` | RED: FAIL | also kills mut `tail-array-not-joined` |
| AC-2.2 | `test_tail_sig_read_failure_returns_1` | RED: FAIL | — |
| AC-2.3 | `test_tail_sig_missing_tail_key_returns_1` | RED: FAIL | — (the `// empty` mutation was removed at audit v21 as equivalent) |
| AC-2.4 | `test_tail_sig_argv_carries_cursor_and_limit` | RED: FAIL | — |
| AC-2.5 | `test_tail_sig_timeout_default_when_env_unset` | RED: FAIL | also kills muts `timeout-default-dropped`, `harness-ambient-timeout-not-scrubbed` |
| AC-2.6 | `test_tail_sig_times_out` | RED: FAIL | also kills mut `time-bound-removed` |
| AC-2.7 | `test_tail_no_timeout_binary_invocation` | RED: PASS | procedure AC-2.8 on this same node: insert `timeout 2 orca …`, observe RED, remove |
| AC-2.9 | `test_tail_sig_rejects_ok_false_envelope` | RED: FAIL | also kills mut `envelope-ok-false-accepted` |
| AC-2.10 | `test_tail_sig_rejects_non_array_tail` | RED: FAIL | also kills mut `non-array-tail-accepted` |
| AC-2.11 | `test_tail_matcher_regex_is_accepted_by_grep` | RED: FAIL | — |
| AC-2.12 | `test_tail_matcher_corpus_decides_prose_vs_banner` | RED: FAIL | also kills muts `tail-re-unanchored`, `tail-re-unanchored-agy` |
| AC-3.1 | `test_tail_pass_resolves_single_vendor_banner` | RED: FAIL | also kills mut `marker-content-changed` |
| AC-3.2 | `test_tail_pass_launch_command_alone_does_not_resolve` | RED: PASS | muts `tail-re-widened-to-launch-line`, `tail-re-widened-to-launch-line-agy` |
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
| AC-3.17 | `test_tail_pass_prose_mentioning_agent_does_not_resolve` | RED: FAIL | also kills mut `tail-re-unanchored` |
| AC-3.18 | `test_tail_agent_pv_re_comment_matches_measurement` | RED: FAIL | — |
| AC-4.1 | `test_tail_pass_rejects_rival_signature` | RED: FAIL | — |
| AC-4.2 | *withdrawn* | — | subsumed by `test_tail_pass_zero_matches_declines`: a rival-only tail fails the agent's own signature and never reaches the count, so NO mutation on rival rejection can discriminate it. Number retained so AC-4.1/4.3/4.4 do not renumber. |
| AC-4.3 | `test_tail_pass_rival_rejection_symmetric` | RED: FAIL | — |
| AC-4.4 | `test_tail_pass_rival_rejected_before_counting` | RED: FAIL | — |
| AC-4.5 | `test_tail_pass_long_tail_early_rival_rejected` | RED: FAIL | — |
| AC-4.6 | `test_tail_pass_rival_prose_does_not_suppress` | RED: PASS | muts `rival-re-prose-unsafe`, `wire-rival-matcher-forced-empty` |
| AC-5.1 | `test_os_evidence_pass_renumbered_to_four` | RED: FAIL | — |
| AC-5.2 | `test_skill_md_names_tail_evidence_pass` | RED: FAIL | — (AC-5.4 is this same node's revert-and-observe procedure, not a second node) |
| AC-5.5 | `test_skill_md_codex_banner_claim_qualified` | RED: FAIL | — |
| AC-5.3 | `test_skill_md_frontmatter_unchanged` | RED: PASS | muts `skill-md-frontmatter-renamed`, `skill-md-description-reworded` |
| AC-6.11 | `test_tail_mutation_spec_root_is_relative` | RED: FAIL | — |

**The selector is `-k 'test_tail_ or test_skill_md or test_os_evidence'`** — it must cover all 45
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
- [ ] AC-6.5: A mutation NEUTRALISING the rival-rejection condition (`drop-rival-rejection`
      replaces it with `if false`, keeping the block and its `continue` intact) is killed by
      AC-4.1. It is written that way deliberately: deleting the `continue` would also change the
      loop's control flow, and the kill could then be credited to that rather than to the
      missing rejection. Impl-plan audit v40.
- [ ] AC-6.6: A mutation widening the candidate pool from `$scoped` to the raw listing is killed
      by AC-3.7.
- [ ] AC-6.7: A mutation redirecting the `[H-MAD] … by tail evidence` line to stdout is killed by
      AC-3.13 (stdout must equal the bare handle).
- [ ] AC-6.8: A mutation gating the pass on `[ "$n" -eq 0 ]` instead of running it whenever
      control falls past Pass 2 is killed by AC-3.8 (the ambiguous-title shape).
- [ ] AC-6.9: `python3 h-mad/scripts/h_mad_mutation_harness.py h-mad/tests/mutation-specs/tail_signature_pass.json`
      prints `MUTATION: ALL_CAUGHT` with `survived=0`, and every mutation's `mechanism:` detail
      line names the test the spec pinned rather than an unrelated failure.
- [ ] AC-6.10: `python3 h-mad/scripts/h_mad_mutation_harness.py --check-anchors` over the whole
      `h-mad/tests/mutation-specs/` directory prints `ANCHORS: ANCHORS_OK` with `drifted=0`.
      The exact command — the harness takes one or more positional spec paths and refuses with
      `ANCHORS_NOTHING_SWEPT` when given none, and **zsh does not word-split an unquoted list
      variable**, which is how that refusal is normally reached:

      ```bash
      bash -c 'python3 h-mad/scripts/h_mad_mutation_harness.py \
        --check-anchors h-mad/tests/mutation-specs/*.json'
      ```

      The harness path is **repo-relative**, like every other verification command here. It read
      `~/.claude/skills/h-mad/scripts/…` until v1.42, which resolves on this machine only because
      `~/.claude/skills` is a symlink INTO this repo — so the command worked while being wrong,
      and would fail for any checkout that is not the symlink target. Impl-plan audit v41 (agy);
      same class as the absolute mutation-spec roots AC-6.11 pins.

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
**What the proof column is, and is not.** It names the mutation(s) that make a GREEN-AT-RED node
discriminating — 13 rows. It is NOT an index of the 49 mutations (re-derived from the embedded JSON, not carried — it read
38, 39, 41, 43, 46, then 49 as v1.45/v1.49/v1.50 added revert-mutants, v1.52 split two of them, and the Phase 5 live-banner check added three): a `RED: FAIL` node needs no
proof (it already fails without the feature) and carries `—`, and every mutation is pinned by its
own `test` field regardless. Impl-plan audit v42 read the column as an index and filed the 16
uncited mutations as an omission; that part does not hold. What DID hold is narrower and is fixed:
three mutations pin to green-at-RED nodes while their rows named only one proof each
(`tail-re-widened-to-launch-line-agy` on AC-3.2, `wire-rival-matcher-forced-empty` on AC-4.6,
`skill-md-description-reworded` on AC-5.3), so a second guard on those nodes was unaccounted for
in the one table that is supposed to account for them.

- [ ] AC-6.12 … AC-6.20: **nine AC numbers covering ELEVEN mutations** — the range was sized when
      the count was nine and kept its numbering when two second proofs were added; the numbers are
      identifiers, not a tally. Two kinds — the distinction matters because only the first kind is a
      green-at-RED proof. **The §"Test-name contract" table is the ONLY inventory of green-at-RED
      proofs** — 13 green rows, 16 mutations pinned to them as of v1.53, re-derived from the table
      and the JSON, never from this paragraph. What THIS AC range enumerates is a SUBSET: the seven
      nodes whose proof was added as a distinct AC number, plus the two second proofs those nodes
      later gained (`tail-re-widened-to-launch-line-agy` on AC-3.2, `skill-md-description-reworded`
      on AC-5.3). The other green-at-RED proofs — `stub-read-env-not-array`,
      `stub-read-dir-writes-one-file`, `resolve-on-ge-1`, `wire-force-fire-after-pass0`,
      `pool-whole-listing`, `rival-re-prose-unsafe`, `wire-rival-matcher-forced-empty` — are owned
      by their own ACs (6.1–6.11, AC-4.6) and appear in the table; an earlier wording of this
      paragraph read as a competing total and was not (impl-plan audit v48, codex).
      The seven primary proofs, each named in that same column:
      `stub-branch-swallows-terminal-list`, `stub-branch-ignores-env-var`,
      `stub-branch-above-capture`, `tail-re-widened-to-launch-line`, `signature-check-not-enforced`,
      `tail-sig-fabricates-banner-on-failure`, `skill-md-frontmatter-renamed`. **Plus two
      independent SIGPIPE guard mutations**, `wanted-check-back-to-pipeline` and
      `rival-check-back-to-pipeline`, which revert the here-string form and are pinned to
      AC-3.16 and AC-4.5 — both RED: FAIL nodes, so they are not proofs of anything being
      legitimately green; they exist because a long-tail guard has no other discriminator. Each must be `caught`, and its `mechanism:` line must name
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
   (as AC-2.7), and counted `test_skill_md_names_tail_evidence_pass` twice as a failure (AC-5.2 and
   AC-5.4). Counts derived from it could not have matched an actual pytest run, so the independent
   5d count check would have halted a correct dispatch. AC-2.8, AC-4.2 and AC-5.4 are therefore
   reframed below as **procedures**, not nodes.

   | task | nodes | FAIL at RED | PASS at RED | the PASS nodes |
   |---|---|---|---|---|
   | T1 | 6 | 2 | 4 | `…does_not_capture_terminal_list`, `…unset_preserves_legacy_behaviour`, `…still_captures_argv`, `…helpers_shape` |
   | T2 | 11 | 10 | 1 | `test_tail_no_timeout_binary_invocation` |
   | T3 | 18 | 12 | 6 | `…launch_command_alone_does_not_resolve`, `…two_matches_declines`, `…zero_matches_declines`, `…not_run_when_pass0_resolves`, `…pool_is_scoped`, `…all_unreadable_declines` |
   | T4 | 5 | 4 | 1 | `test_tail_pass_rival_prose_does_not_suppress` |
   | T5 | 4 | 3 | 1 | `test_skill_md_frontmatter_unchanged` |
   | T6 | 1 | 1 | 0 | `test_tail_mutation_spec_root_is_relative`; the harness verdicts themselves are read from the `MUTATION:` token, not from pytest counts |
   | **total** | **45** | **32** | **13** | |

   **Derive these counts at dispatch time; do not read them from the table.** The count and the
   enumeration are two surfaces that drift, and this one has drifted once already. The
   authoritative form is the enumeration in §"Test-name contract", one row per node with a single
   `RED:` outcome; run

   ```bash
   F=docs/01-plan/features/pin-agents-tail-banner.impl-plan.md
   grep -cE '^\| AC-.* \| `test_.*` \| RED: (FAIL|PASS) \|' "$F"   # 45  total nodes
   grep -cE '^\| AC-.* \| `test_.*` \| RED: PASS \|'        "$F"   # 13  --expect-pass
   grep -cE '^\| AC-.* \| `test_.*` \| RED: FAIL \|'        "$F"   # 32  --expect-fail
   ```

   **Those three numbers are the AGGREGATE CHECK, not the dispatch inputs.**
   `h_mad_assemble_tdd.py` cuts ONE `## Task N` and takes that task's `--expect-fail` /
   `--expect-pass`; feeding it 32/13 would guarantee `step5d:red_not_all_failing` on every task
   (T1 expects 2/4, T2 10/1, …). Derive per task from the same authoritative rows — the AC prefix
   identifies the task:

   ```bash
   F=docs/01-plan/features/pin-agents-tail-banner.impl-plan.md
   for n in 1 2 3 4 5 6; do
     row="^\| AC-$n\.[0-9]+ \| \`test_.*\` \| RED:"
     printf 'T%s  --expect-fail %s  --expect-pass %s\n' "$n" \
       "$(grep -cE "$row FAIL" "$F")" "$(grep -cE "$row PASS" "$F")"
   done
   ```

   Expected: T1 2/4 · T2 10/1 · T3 12/6 · T4 4/1 · T5 3/1 · T6 1/0, summing to 32/13 over 45 —
   and **every row carries exactly ONE AC label** so the per-task regex sees all 45. Two rows
   briefly carried `AC-2.7, AC-2.8` and `AC-5.2, AC-5.4`; the loop then matched 35 and silently
   under-counted T2 and T5. A shared node takes its PRIMARY AC, with the secondary named in the
   proof column as the procedure it is —
   run the loop, do not read those numbers. The aggregate is only how you check the per-task
   figures add up.

   **The v1.6 form of these commands returned 0 and 13.** They were
   `grep -c '^| \`test_'` (0 — every row starts with `| AC-…`, not the node) and an unanchored
   `grep -c 'RED: PASS'` (13 — it also matched prose outside the table). Their difference would
   have been passed to `--expect-fail` as **-13**, making the 5d dispatch invalid. Both are
   anchored to the full row shape above and verified to return 45 / 13 / 32 against this file.

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
2. **Suites and mutation.** `pytest h-mad/tests/test_hmad_dispatch.py -q -k orca_identity`
   (**24 of 290 collected** — assert a non-zero collected count, because pytest exits 5 on an
   empty selection and a zero-collection step measures nothing while looking like a pass; the
   selector here was `-k orca_find` until v1.34 and collected 0/290, and no planned node name
   contains `orca_find`), then
   `pytest h-mad/tests/test_hmad_dispatch.py -q -k test_tail_`, then the full `pytest` (testpaths
   now cover `handoff/scripts`), then `python3 h-mad/scripts/h_mad_mutation_harness.py` on the new spec
   (repo-relative and via `python3` — the script is not executable and not on `PATH`, so the
   bare basename exits 127 and can never print `MUTATION: ALL_CAUGHT`; audit v52), then
   `--check-anchors` under bash — never zsh.
3. **Live check — it must exercise THIS pass, not merely succeed.** `hmad-dispatch env` resolving
   codex is NOT sufficient evidence: Pass 0, the title pass, the preview pass or an ambient pin
   can all satisfy it without a single `terminal read`, so the check would pass with the whole
   feature reverted — the exact vacuous-verification shape this feature's ACs were written
   against. Require all four:
   1. **Run the whole live check against an ISOLATED pin file**: `export
      HMAD_ORCA_PIN_FILE="$(mktemp -d)/orca-pins.env"` before anything else, and confirm with
      `hmad-dispatch env` that its `pin file:` line names that path. The repository's real
      `.h-mad/orca-pins.env` holds the operator's live coordinator and agent pins; clearing it
      to verify a feature destroys state that has nothing to do with the feature, and a check
      that succeeds while doing that has still done damage. Impl-plan audit v21. If an isolated
      path cannot be used, snapshot the real file first (`cp`), and restore it at the end with a
      separate re-read confirming the restore landed — the same rule AC-2.8 applies to tracked
      files.

      **SEED the isolated file before clearing it.** A fresh `mktemp` path names a file that
      does not exist, so running `--clear` and then observing absence proves nothing: the same
      observation holds if the clear path is broken, or never ran at all. That is a verification
      of a NO-OP dressed as a mutation check — the exact failure this step was rewritten to
      avoid, reintroduced by the isolation fix itself. Impl-plan audit v22. So: write known dummy
      pins into the isolated file (both agents, recognisable handles), re-read it and confirm
      they are THERE, then `hmad-dispatch pin-agents --clear`, then re-read again and confirm
      those specific handles are GONE. Absence is only evidence when presence was established
      first. Also confirm no `HMAD_ORCA_*_TERMINAL` is exported.
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
      re-read the tree after a restore. Remove the isolated pin file's `mktemp -d`
      directory in the same step, or each run leaves an empty temporary directory behind —
      **and re-read to confirm it is gone.** Keep the path in a variable and assert it no longer
      exists after the removal. Deleting a directory mutates filesystem state, so treating the
      command as its own proof is the same failure AC-2.8 rejects for a file edit and audit v22
      rejected for the pin clear: `rm -rf` on a path that was never created, or that a later
      step recreated, succeeds silently. Impl-plan audit v25.

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
- v1.17: Impl-plan audit v20 (codex) — all three must-fixes were consequences of v1.16's own edits. Adding the `.ok` gate changed the filter's opening line, and `jq-r-not-jq-re` and `tail-empty-guard-dropped` still anchored on the OLD prefix: both would have matched ZERO times after implementation, which is silent — an anchor that matches nothing reports its guard as enforced. Re-anchored (the first onto the new `jq -re 'if ...` opening, the second onto the inner `else (...) end`), and a check now exists that resolves every mutation's `find` against the prescribed helper body; it passes 10/10 for the helper anchors, the two misses being the `_orca_find` and Python-harness mutations, which live elsewhere by design. The count sweep was also incomplete: `all 38`, `38 total nodes`, `sees all 38` and `verified to return 38 / 11 / 27` survived three phrasing variants my greps did not cover. Second safety gap of the same family as AC-2.9: `else tostring` accepted every non-null non-array payload, so a malformed tail merely CONTAINING a banner became identity evidence — `else empty` now, with AC-2.10 and `non-array-tail-accepted` (28 mutations). The `.ok` rule and the exact extraction are back-propagated to the design, FR-4 is explicit in the spec as AC-4.4 (neither case reads as an error to the checks that catch the rest: rc is 0 and the key is present), and the source-design citation is corrected. Two stale `_mechanism` strings still described the `< 1.5 s` window the v1.16 seam replaced. Counts re-derived, not edited: 29 FAIL / 11 PASS over 40, T2 8/1, spec 15 ACs.
- v1.18: Impl-plan audit v21 (codex) — a SIXTH equivalent mutant, and v1.17 created it. Changing the type branch to `else empty` made `tail-empty-guard-dropped` behaviourally identical to the unmutated filter: a null from an absent key is discarded at the type branch whether or not `// empty` catches it first. Verified as a controlled pair on four inputs (missing key, array tail, string tail, ok:false) — byte-identical output and rc 4/0/4/4 both ways. The mutation is removed rather than re-anchored, `// empty` is now documented as defence in depth rather than an independently pinned guard, and the claim that it was one is corrected in the plan and the design (27 mutations). The count sweep missed a FIFTH time — `# 38  total nodes` annotating the very command that returns 40, and a worked example feeding `27/11`. Design was stale on two cross-document surfaces: its Components table still said 14 ACs and its Test Plan had no row for spec v1.8's AC-4.4; both fixed. Two should-fixes taken: the live check now runs against an ISOLATED HMAD_ORCA_PIN_FILE, because clearing the repository's real pin file destroys the operator's live coordinator and agent pins to verify a feature that has nothing to do with them; and AC-3.6's fixture must blind Passes 1 and 2, or `wire-force-fire-after-pass0` survives — with Pass 0 forced to fall through, a matching title or preview resolves before the tail pass and no `terminal read` is ever issued, so the mutant passes the assertion written to catch it.
- v1.19: Impl-plan audit v22 (codex) — must 3 -> 1, and the one is v1.18's own isolation fix verifying a NO-OP. `HMAD_ORCA_PIN_FILE="$(mktemp -d)/orca-pins.env"` names a file that does not exist, so running `pin-agents --clear` and then observing absence proves nothing: the same observation holds if the clear path is broken or never ran. The step now SEEDS the isolated file with known dummy pins, confirms they are present, clears, and confirms those specific handles are gone — absence is evidence only where presence was established first. That is the seventh consecutive cycle whose finding was created by the previous cycle's fix. The isolation itself had also landed only here, so the plan's Success Criteria and the design still sent an operator at the ambient pin file; both back-propagated. `test_os_evidence_pass_renumbered_to_four` asserted only the ABSENCE of the false sentence, which a deletion satisfies as well as the prescribed correction does; a positive assertion on the replacement wording is added. AC-6.12..AC-6.20 called all nine of its mutations green-at-RED proofs when the last two are pinned to AC-3.16 and AC-4.5, both RED: FAIL — seven proofs plus two independent SIGPIPE guard mutations, now stated that way. Source-design citation corrected. The audit independently re-derived the 290-test baseline, the 40-node table and the 27-mutation count and found all three correct.
- v1.20: Impl-plan audit v23 (codex) — must 1, and it is a RED CLASSIFICATION that could not hold. AC-1.5 was marked `RED: FAIL` while `test_tail_stub_read_helpers_shape` tests only `_orca_read_env` and `_orca_read_dir`, both TEST-FILE helpers that T1's own RED patch introduces: the node passes the moment the patch lands, and withholding the helpers yields a NameError, which is a missing-symbol failure rather than a behavioural one and would force test implementation during GREEN. T1's 3/3 split and the 29/11 aggregate were therefore unsatisfiable and a correct dispatch would have halted on red_not_all_failing. Reclassified green at RED with two discriminating mutations, one per asserted property — `stub-read-env-not-array` (the measured live shape is an array and production joins it) and `stub-read-dir-writes-one-file` (a handle the caller supplied must not be served as unreadable). Counts re-derived, not edited: 28 FAIL / 12 PASS over 40, T1 2/4, swept through the impl-plan, plan and design. 29 mutations. The design's `$scoped` justification was also backwards — it claimed a wider pool 'can only turn a resolution into a decline', when adding one uniquely banner-matching pane turns a decline INTO a resolution, which is this feature's whole point; the safety is now grounded where it actually lives (the scope boundary, the wanted/rival predicates, and exactly-one), not in a false monotonicity claim. Nit: the live check now removes its `mktemp -d` directory.
- v1.21: Impl-plan audit v24 (codex) — both must-fixes were stale PROSE left behind by my own earlier edits, not new defects. Task 6's control-family paragraph still said six mutations, five in the helper, and four nodes, after v1.19 deleted the equivalent `// empty` mutation; its own sentence "removing any one leaves the other four" already implied five. Verified against the spec: FIVE mutations, FOUR in the wrapper and one in the Python harness, pinned to THREE nodes (AC-2.1, AC-2.5, AC-2.6). The paragraph now carries a mutation/file/node TABLE, so the count and the enumeration are one surface and cannot drift apart again — the same remedy the RED table already uses. The source plan was also one proof short: it reported 12 green-at-RED nodes and then said "each of the 11" is tied to a mutation, leaving `test_tail_no_timeout_binary_invocation` with no stated proof on the surface that is the declared source. It is 11 + 1 — eleven mutation-backed, and one carrying AC-2.8's insert/observe/remove procedure. The isolated pin file's `mktemp -d` cleanup, added here at v1.20, is back-propagated to the plan and design.
- v1.22: Impl-plan audit v25 (codex) — a SIXTH sweep miss, and it is the class the v1.21 self-check was written to catch: a LIVE dispatch instruction still said the row commands were 'verified to return 40 / 11 / 29' where the table immediately above it, and the commands themselves, give 40 / 12 / 28. Prose carrying a count it does not enumerate stays the dominant failure here. Second, `marker-to-stdout` mutated only the STREAM ROUTING of the success marker; routing and content are separable guards on one line, and AC-3.1 and the live check both consume the exact phrase `bound <handle> by tail evidence`, so a reworded marker left both asserting on a string that no longer exists while stdout stayed clean. Added `marker-content-changed`, pinned to AC-3.1, and verified as a controlled triple that unmutated / routing / content each produce a DIFFERENT observable (stderr full marker, stdout full marker, stderr truncated marker) — neither mutant is equivalent. 30 mutations. Third, the `mktemp -d` cleanup added at v1.20-v1.21 was itself unverified: removing a directory mutates filesystem state, so the command is not its own proof, and `rm -rf` on a path never created succeeds silently. All three live-check surfaces now retain the path and assert its absence. Source-design citation corrected v1.18 -> v1.21.
- v1.23: Impl-plan audit v26 (codex) — the first finding of this run that falsifies a SAFETY PREMISE rather than a document claim. The plan, design and spec all treated `_agent_pv_re` as 'hardened against prose' and rested the unique-match safety argument on it. It is not: measured 4/4 by the audit and 7/7 by the corpus now in AC-3.17, ordinary sentences like `Release notes for OpenAI Codex are available` and `Compare Gemini 3.1 Pro with Claude` MATCH it. Since `$scoped` includes ordinary shell panes and tail evidence is explicitly historical, a plain shell that once printed release notes or documentation was resolvable AS THE AGENT — the wrong-pane class FR-2 forbids. The regex is hardened against the two examples that motivated it (both still declining), and that was generalised into a premise it does not support. Fix: the TAIL PASS anchors the matcher to line start; `_agent_pv_re` itself is untouched because it is shipped and shared with Passes 1-2, whose inputs are short titles and previews rather than arbitrary scrollback. Measured anchored: 0 of 7 prose probes match, 7 of 7 real banner and status lines still do. AC-3.17 carries the corpus and the positive controls; `tail-re-unanchored` is the mutation. Changing the `tail_re` line also broke two existing mutation anchors that referenced it — re-anchored in the SAME edit, which is the c20 lesson applied prospectively for once. Counts re-derived: 41 nodes, 29 FAIL, 12 PASS, T3 11/6; 31 mutations. Two shoulds: the literal-`null` explanation for `jq -r` was true of the simpler probe filter and false of the shipped one (measured: zero bytes at rc 0, so `-e` closes the RC hole, not a null-printing hole), corrected on both surfaces; and Task 6's 'every new guard is mutated' was broader than its own inventory — narrowed to the enumerated table, noting that the unmutated controls are RED: FAIL nodes and so still discriminated.
- v1.24: Impl-plan audit v27 (codex) — the v1.23 anchor fix was INCOMPLETE and the reason is worth keeping: every negative probe in that corpus put the agent token mid-sentence, so a line-start anchor separated the CORPUS without separating the CLASS. Line-LEADING prose — `OpenAI Codex documentation changed`, `## Gemini 3.1 Pro release notes`, `model: gpt-5 migration notes` — still matched, and a shell pane in $scoped still resolved as the agent. A negative corpus is only as strong as the shapes in it, and one shape was doing all the work. Replaced with a BANNER GRAMMAR: the discriminator is what FOLLOWS the signature — a banner ends its line or continues with version/model/effort structure, prose continues with words. Measured over 14 prose probes and 11 real banner/status lines: unanchored 0/14 decline, anchored-only 7/14, grammar 14/14, with all 11 positives matching under every form. Rewriting the matcher moved THREE mutation anchors; re-anchoring them onto the `case` opener produced syntactically broken mutants (orphaned arms, and later arms overwriting the mutated value), so they are anchored on the codex ARM and on the `local` line instead — re-anchoring is not done until the mutant is still valid AND still meaningful. The rule was also missing from the paired SPEC, which still presented `_agent_pv_re` as a banner discriminator: spec AC-1.4 now carries the tail-only matcher constraint and the prose-rejection criterion (16 ACs). AC-3.18 added so Task 3 corrects `_agent_pv_re`'s OWN comment, which still claims its strings cannot occur in ordinary prose — shipping both statements five hundred lines apart would leave the wrapper self-contradictory. Counts re-derived: 42 nodes, 30 FAIL, 12 PASS, T3 12/6; 31 mutations. Citations corrected to design v1.23 and spec v1.9.
- v1.25: Impl-plan audit v28 (codex) — THIRD revision of the prose rule, and a mirror defect the first two hid. The v1.24 grammar required the signature to lead the line and then allowed anything after it, so `OpenAI Codex v0.145 release notes`, `gpt-5.6-terra high performance notes` and `Gemini 3.1 Pro (release notes)` still matched — prose after a banner-like PREFIX, the third shape this corpus lacked (mid-sentence, then line-leading, now banner-prefixed). The rule is LINE-COMPLETE now: a banner consumes its whole line and only structured continuations are allowed (version, `model:` field, effort word, `·` and cwd, bounded parenthetical). Measured across 19 prose probes and 12 real banner/status lines: unanchored 0/19 decline, anchored-only 7/19, v1.24 grammar 14/19, this one 19/19, all 12 positives matching under every form. The mirror defect: Task 4's rival check still used the SHARED `$rival_re` (`_agent_pv_re`) over the retained tail, so a real codex pane whose scrollback merely said `Compare Gemini 3.1 Pro with Claude` was rejected as rival-bearing — the feature suppressing exactly the panes it exists to resolve. Both checks now go through ONE helper, `_agent_tail_re`, which is also what audit v28's should-fix asked for: the two arms were duplicating a pattern that could drift. AC-4.6 pins both directions and `rival-re-prose-unsafe` restores the unsafe matcher (32 mutations). The design still described the rejected anchor-only rule and diagrammed the pass as `tail via _agent_pv_re`, so an implementer following the declared source would have rebuilt the defect; architecture, matcher rule, rival rule and test plan all back-propagated. AC-3.17's traceability label corrected from FR-2 (cardinality) to spec AC-1.4 under FR-1. Counts re-derived: 43 nodes, 31 FAIL, 12 PASS, T4 5/0.
- v1.26: Impl-plan audit v29 (codex) — FOURTH revision of the prose rule plus three structural findings. The line-complete form still took a markdown heading (the prefix class allowed `#`), a hyphenated word posing as a version or model id (`OpenAI Codex v0.145-release-notes`, `model: gpt-5-migration-notes` — both suffixes were unbounded non-space runs), and an open numeric parenthetical (`Gemini 3.1 Pro (2026 release notes)`). Tightened: prefix is whitespace and box-drawing/quote only, a version is dotted-numeric, a model id needs a DOTTED release number, a parenthetical is an effort word or a version. Corpus is now 24 negatives / 12 positives, enumerated ONCE and synchronised across spec, design, impl-plan and every comment — the counts had drifted to 19/12 here, 19/12 in the design, 14/11 in the spec and '11 in all' inside the AC that owns the list. Measured: unanchored 0/24, anchored-only 7/24, leading-position 14/24, line-complete 19/24, this grammar 24/24, 12/12 positives under every revision. STRUCTURAL: the two `_agent_tail_re` calls were undeclared wires — the gate saw `wiring=1` where there are two connections, so both matcher edges bypassed the caller-observable RED and the connection-only mutation the invariant requires. T3 now declares a second WIRE/WIRE-PIN for the wanted matcher and T4 is reclassified `wiring` for the rival matcher, each with a disconnect-callee-intact mutation; the gate reports `wiring=2 registered=3`. The two rival mutations are deliberately opposed — `wire-rival-matcher-disconnected` under-rejects and `rival-re-prose-unsafe` over-rejects — so together they pin the connection AND its matcher. AC-3.18's node was named `test_agent_pv_re_...`, which the `-k test_tail_ or test_skill_md or test_os_evidence` selector does NOT match, leaving a named feature test outside the mutation baseline; renamed with the `test_tail_` prefix, and the only names now outside the selector are the two unrelated module tests the plan already documents as excluded. Task 6's 'every guard this feature introduces' narrowed to the enumerated table. 34 mutations.
- v1.27: Impl-plan audit v30 (codex) — the worst finding of the run, and it is mine: **the prescribed matcher had never executed.** The `_agent_tail_re` arms were written with `printf '%s\\n'` and doubled `\\(` escapes, so run verbatim the helper appended the literal bytes `\n` and `grep -E` rejected the pattern outright — `repetition-operator operand invalid`, rc 2, on every input including the positive controls. Every 24/24 figure this plan reported came from separate probe scripts with different escaping; the doc carried a DIFFERENT, non-functional regex. Fixed, and the corpus is now run through the doc's own block (24/24 negatives decline, 12/12 positives match), with AC-2.11 added so the prescribed source is what gets measured — a regex the plan prints must be one `grep -E` accepts. Three more structural corrections. T4's WIRE-PIN was backwards: disconnecting the rival matcher makes rival prose stop suppressing the wanted pane, which is exactly what `test_tail_pass_rival_prose_does_not_suppress` asserts, so the pin went GREEN with the wire removed; `test_tail_pass_rejects_rival_signature` is the caller-observable direction, and AC-4.6 is now green at RED with `rival-re-prose-unsafe` as its proof. T3's wanted-matcher wire could not meet its own caller-observable rule while callee and call site both landed in T3 — the AC-1.5 shape again — so `_agent_tail_re` ships in TASK 2, and a `wire-wanted-matcher-forced-empty` mutation supplies the opposite direction (one proves the call is made, the other that its result is used). And the normative surfaces still said the tail pass reuses `_agent_pv_re`: T4's description claimed `$rival_re` was reused unchanged while its own code forbids it, and both executive summaries named the shared helper — all now name `_agent_tail_re`. Counts re-derived: 44 nodes, 31 FAIL, 13 PASS, T2 9/1, T4 4/1; 35 mutations; AC-3.17's positive list was one short of the 12 it claimed. Corpus groups are named by SHAPE now, not relative position.
- v1.28: Impl-plan audit v31 (codex) — every finding is a consequence of v1.27's own fixes, and one repeats a lesson I had written down twice. Correcting the matcher's shell escaping ORPHANED the two JSON anchors that pointed at it: decoded, `tail-re-unanchored` and `tail-re-widened-to-launch-line` matched ZERO times, so both mutants would have mutated nothing while reporting their guards as enforced. Anchors are now GENERATED from the block itself rather than retyped, which is the only form that cannot drift. The T2/T3 split was announced and not performed — v1.27 said `_agent_tail_re` ships in T2 while the definition still sat inside T3's `_orca_find` block, so following the tasks literally either loses the helper or defines it twice (and duplicate arms would make the exact anchors non-unique). The definition now lives once, in T2, and T3 carries only the two call sites. The source plan and spec still prescribed the OLD matcher — a line-start wrapper around the shared helper, and rival rejection 'reused from Pass 1' — which is the prose-unsafe path the impl-plan rejects; both now name `_agent_tail_re` and its bounded grammar. AC-5.4's restore check ran `git diff --stat SKILL.md` from the repository root, where no such file exists: it could report clean while a failed restore sat in `h-mad/SKILL.md`. And the plan's green-at-RED split still read '12 = 11 + 1' beside a count of 13, while `tail-re-unanchored`'s mechanism still cited 'all seven prose probes' against a 24-probe corpus. Should-fixes: `_isolated_env` now scrubs `HMAD_STUB_ORCA_READ_DIR` too — an ambient export would opt every legacy `terminal read` test into the per-handle branch, making the 290-test regression claim environment-dependent — and T4's spliced sentence about `$rival_re` is repaired.
- v1.29: Impl-plan audit v32 (codex) — the T2 move I reported at v1.28 had landed the matcher inside TASK 1: the block sat between Task 1's helper prose and the `## Task 2` heading, so a Task 1 dispatch would have received code Task 1 declares no production file for, and AC-2.11 would have been green before Task 2's RED. Third instance of announcing a structural change and not performing it — the block is now physically below the Task 2 heading, asserted by index rather than by prose. Two guard gaps: NO mutation had ever touched the AGY arm, so half the classifier was unobserved while AC-3.2 asserts both agents reject their launch line — `tail-re-unanchored-agy` and `tail-re-widened-to-launch-line-agy` added (37 mutations); and `stub-read-dir-writes-one-file` is EQUIVALENT against a one-entry fixture, so AC-1.5 now requires a two-handle mapping with per-handle content assertions — the seventh equivalent mutant this plan would have shipped. The matcher contract was still contradictory in four CURRENT bodies despite histories claiming otherwise: T4 said `$rival_re` is 'reused unchanged', the spec said `_agent_tail_re` WRAPS the shared helper while AC-1.4 says its arms are independent literals, the source plan said the work is 'running the EXISTING helper against .tail', and the design still carried the superseded 0-of-7 anchored account. All four now say the same thing. AC-4.6's green-at-RED reason was wrong (the pass DOES exist at T4; rival rejection does not), and Task 2 still said `_orca_tail_sig` 'is added alone'.
- v1.30: Impl-plan audit v33 (codex) — must 5 -> 4, and the audit independently re-derived the three things this plan most depends on: the prescribed matcher EXECUTES correctly over the 24/12 corpus, the mutation JSON parses at 37 entries, and the module still collects 290. The blocking finding is a RED classification that could not hold, the third of its shape (AC-1.5 at v23, T4's pin at v30): AC-3.17 was `RED: FAIL` and T3's WIRE-PIN while its fixture was prose-ONLY — which does not resolve at T3 RED either, because the pass does not exist yet, so the node passes before any T3 code is written and a pin that passes without its wire proves nothing. Reshaped to a MIXED fixture: one real-banner candidate plus one prose decoy, expecting the banner's handle. That fails before the pass exists AND when the matcher connection is removed (both candidates then match, count is 2, the pass declines on ambiguity). The matcher's own corpus moved to T2 as AC-2.12, where the helper is owned — AC-2.11 only proved the regex was syntactically usable, which an always-matching ERE would satisfy, so the helper was 'proven before anything consumes it' by a check that could not see what it matched. Cross-document: spec AC-1.1 still defined the match in terms of `_agent_pv_re` while AC-1.4 measures that helper matching prose 24/24 — two ACs admitting different candidate sets, one of them the wrong-pane class; the design never listed `_agent_tail_re` in Components, API or Implementation Order despite requiring it at step 2; and the plan's Success Criteria assigned the procedure to 'the twelfth' after saying twelve nodes are mutation-backed, leaving the thirteenth unaccounted. Counts re-derived: 45 nodes, 32 FAIL, 13 PASS, T2 10/1.
- v1.31: Impl-plan audit v34 (codex) — must 4 -> 3; the RED table, the 37-mutation JSON and the 290-node module all re-derived correctly again. Two mutation-discrimination defects, both introduced by earlier re-anchoring. `entry-gated-on-n-eq-0` had been re-anchored at v1.28 onto the `local` line with `[ "$n" -eq 0 ] || return 1`, which ABORTS `_orca_find` and suppresses the OS-evidence pass behind it — so the mutant could be killed by the forbidden early return rather than by the wrong entry condition, which is the mechanism its own rationale describes. It now neutralises only this pass's matcher and preserves fall-through. And the two per-arm AGY mutants were pinned to `test_tail_pass_prose_mentioning_agent_does_not_resolve`, whose fixture is Codex-only by construction (AC-3.17 uses an OpenAI Codex banner and Codex prose), so an AGY-arm mutation would have SURVIVED its designated test and ALL_CAUGHT been unreachable; all three grammar mutants now target AC-2.12's node, which is where the per-agent corpus lives. Third: design v1.29's history claimed Implementation Order and API had been updated for `_agent_tail_re` and they had not — step 1 still shipped only `_orca_tail_sig` while step 2 consumed the missing matcher, and the API section still said 'One new private shell function'. Both fixed, plus the helper's interface block. That is the fourth instance of a history entry claiming a back-propagation the body did not receive.
- v1.32: Impl-plan audit v35 (codex) — must 3 -> 2, third consecutive drop, and the RED table (45/32/13), the 37-mutation JSON and the 290-node module re-derived correctly for the third cycle running. Both findings are real defects in code this plan prescribes. `_agent_tail_re "$rival"` expanded an UNBOUND variable: `_orca_find` owns `rival_re`, a regex built for Pass 1, and nothing holds the rival's NAME — under the wrapper's `set -euo pipefail` (line 5, verified) the first candidate carrying the wanted signature would abort `_orca_find` instead of performing rival rejection. Introduced at v1.25 when the rival check moved to the tail grammar and unnoticed for ten cycles. T4 now extends the existing case with `rival=agy` / `rival=codex`, and an empty token falls to the `*)` arm rather than aborting. Second: the launch-line mutants REPLACED their arm wholesale, so the kill came from the node's positive controls failing — an accidental kill that proves nothing about launch-line rejection. Both are additive now (full grammar preserved, `|^<agent> .--dangerously` appended) and pinned to AC-3.2's node, which exercises both agents; the corpus node keeps the three prose mutants. Also: `wire-wanted-matcher-disconnected`'s mechanism still described AC-3.17's old prose-only fixture, and the spec and design still implied the grammar is layered ON TOP of `_agent_pv_re` rather than being independent literals.
- v1.33: Design pass 2026-09-02, chosen by the operator over a 36th audit cycle: 20 cycles had never reached must=0 and the residual class was one grammar restated as a flat list on five surfaces across three documents. Two real defects fell out of writing it down once. (1) THE MATCH IS CASE-INSENSITIVE AND NO DOCUMENT SAID SO. The literals are lowercase, every real banner is capitalised, and every call site uses `grep -Eiq`; measured 2026-09-02 by running the plan's own block over the full corpus, a case-sensitive `grep -E` still declines 24/24 negatives but declines 9 of the 12 POSITIVES too — only the three all-lowercase controls survive. The decline half of the corpus cannot see the error, and AC-2.11's `grep -E` (a syntax check) reads as the match contract. (2) THE CONTINUATIONS ARE PER-ARM, and the flat list was wrong on three of five rows: the `model:` field and the `·`-plus-cwd are codex-only, the effort/version parenthetical is agy-only. Durable half: the `_agent_tail_re` block in impl-plan Task 2 is the single normative statement, design carries the one per-arm description, and plan/spec/AC-3.17 now POINT at it instead of restating it. AC-2.12 now names `grep -Ei`, AC-2.11 says explicitly that it covers syntax only, the code-block comment carries the per-arm and fold rules, and AC-3.17's Group B stops re-listing the continuations. No mutation anchor targets the comment prose (verified: 0 of 37 finds).
- v1.34: Impl-plan audit v36 (codex) — all 6 findings applied; both musts independently re-measured before acting. MUST 1: Task 2's normative `_agent_tail_re` block was not a valid fence — `}` and the closing backticks shared one line, so the ```sh fence opened at :173 stayed open to :308 and swallowed the production/test fields and the run_fn Python as shell. Confirmed by parity: 27 fence lines (odd) before, 28 after; the block re-extracts and re-measures 24/24 + 12/12 under grep -Ei. MUST 2: verification prescribed `pytest -k orca_find`, which collects 0 of 290 (pytest exits 5 on an empty selection, so the step measured nothing and looked like a pass) and no planned node name contains orca_find; replaced on BOTH surfaces with `-k orca_identity` (24/290 collected, measured) plus an explicit non-zero-collection assertion. Provenance corrected to design v1.32 / spec v1.17 — the plan already depended on the design pass's case-fold and per-arm rules while citing revisions that predate them. Task 6's boundary promise narrowed to the enumerated table it already narrows to later. AC-3.4 now says N in the fall-through diagnostic is the Pass-1/2 count, NOT tn — under its own fixture it reads 'resolved to 0 candidates' while two panes carried the signature — so the assertion is on the diagnostic's PRESENCE plus the absence of the tail-evidence marker; carrying tn into that pre-existing line is deliberately not prescribed. Nit: the spliced $rival_re sentence in T4 (same edit-collision shape the design pass fixed). Re-verified after: WIREPIN PASS tasks=6 wiring=2, 37 mutation finds intact, test_hmad_dispatch.py 290 passed.
- v1.35: Impl-plan audit v36 (agy, SECOND surface, dispatch rc=124 at the 1500s bound with no end sentinel — report structurally complete but completeness UNVERIFIED, and it audited v1.33). All 3 findings verified against the document and applied. MUST: T5 named a SECOND renumber site (hmad-dispatch.sh:1046, the cross-reference from _orca_handle_live's neighbourhood) and AC-5.1 asserts it, but the Code structure block prescribed only :574 — renumbering one and not the other leaves the file calling two different passes 'Pass 3'. Exact code for the second site added. SHOULD: rival_tail_re was computed INSIDE the candidate loop although $rival is constant across candidates — hoisted above the loop beside tail_re (the local declaration at T3 already covers it), and the two mutations anchored on that line were re-anchored to its new indentation IN THE SAME EDIT, since an anchor left at the old two-space-deeper form matches 0 times and the harness REFUSES rather than measuring. NIT: 4 regex mutations replaced a 4-space case arm with a 6-space one; indentation normalised, 0 mismatches remain across all 36 find/replace pairs. Re-verified: fence parity 30 (even), the embedded JSON still parses, 37 finds intact, WIREPIN PASS tasks=6 wiring=2, corpus 24/24 + 12/12 under grep -Ei.
- v1.36: Impl-plan audit v37, BOTH surfaces on the same bytes (codex must=2 should=1, agy must=1 should=0), both completed runs with end sentinels. The blocking finding is MINE and both surfaces found it independently: v1.35's hoist put rival_tail_re="$(_agent_tail_re "$rival")" in the Pass-1 case block, and T3 later runs `local tail_re rival_tail_re …` — in bash a local re-declaration RESETS the name, so the value was wiped before the tail pass read it, [ -n "$rival_tail_re" ] was false for every candidate, rival rejection NEVER fired, and nothing errored. AC-4.1/4.3/4.4/4.5 could not pass under the prescribed code. Controlled probe run twice: assignment then `local` prints [COMPUTED] then []. The v36 (agy) finding only asked the assignment to leave the LOOP; moving it out of the tail pass entirely was the over-correction. It now sits immediately below T3's local and above the loop — once per call, no local crossed — and the mutation anchors are unaffected because the line's text and indentation are unchanged. Second must (codex): the rival wire had NO force-direction connection mutation — wire-rival-matcher-disconnected and rival-re-prose-unsafe both REMOVE the _agent_tail_re call, so neither proved its result is USED; added wire-rival-matcher-forced-empty on the shared anchor (call kept, result discarded, universal matcher installed -> every candidate rejected pre-count), pinned to test_tail_pass_rival_prose_does_not_suppress, mirroring wire-wanted-matcher-forced-empty. 37 -> 38 mutations; no live count statement in the body needed sweeping. Should: the second Pass-3-to-Pass-4 cross-reference site (:1046) back-propagated to the design's Components table, which named only the pass header. Nit: the ungrammatical 'Same predicate Pass 2 applies NOT the shared' comment fragment. Re-verified: fence parity 34 (even), embedded JSON parses, 38 finds, 0 indent mismatches, WIREPIN PASS tasks=6 wiring=2, corpus 24/24 + 12/12.
- v1.37: Impl-plan audit v38, both surfaces on the same bytes (v1.36): agy GATE PASS must=0 should=0 — the first clean verdict since the design pass — and codex must=0 should=2. MUST IS NOW 0 ON BOTH SURFACES; the disagreement is entirely shoulds, and codex breaking agy's clean is the fifth time that has happened on this branch, which is why one pass is never the gate. Both shoulds verified true and applied: the header still cited design v1.32 after the v38 back-propagation took the design to v1.33 (my own drift, one cycle old), and plan.md attributed the direct 24/12 matcher corpus to AC-3.17 when v1.30 moved it to AC-2.12 — AC-3.17 is the caller-connection node with a mixed fixture, so the stale pointer sent verification to the wrong test surface. Both nits also closed: T4's context block now reproduces T3's three comment lines verbatim so the context matches the source file (agy), and the misleading node name test_tail_pass_prose_mentioning_agent_does_not_resolve is documented as historical and deliberately NOT renamed (codex) — since v1.30 it asserts a successful resolution over a prose decoy, but the id is referenced by the RED table, four mutation test pins and two WIRE-PINs, so a rename is churn across five surfaces where a miss silently un-pins a mutation. Re-verified: fence parity 34 (even), JSON parses, 38 finds, WIREPIN PASS tasks=6 wiring=2, corpus 24/24 + 12/12.
- v1.38: Impl-plan audit v39 (agy) — must=1 should=1, and agy's OWN v38 clean broke one cycle later, which is the agreement-is-not-a-stopping-signal rule demonstrated on a single surface rather than across two. MUST: AC-6.12 … AC-6.20 requires each of nine mutations to carry a mechanism line naming the node its proof column claims, and the embedded spec omitted the key entirely for those nine. Measured: 18 of 38 entries had no _mechanism at all. All 18 written, not just the nine the AC names, each naming its pinned test node and what the mutation removes — the AC's nine are covered and the other nine predated the convention. Verified after: 38/38 entries carry _mechanism, and every one of the new 18 names its own test node. SHOULD: hmad-dispatch.sh:513 reads 'Codex therefore skips Pass 1 entirely and relies on the preview signature or, properly, on a pin/launch' — an exhaustive enumeration that this feature adds a term to, since the tail signature is exactly what Codex falls back to once the preview has decayed. Added as T5's THIRD documentation site with exact code, plus positive AND negative assertions in AC-5.1's test block (a deletion satisfies the negative alone). Re-verified: fence parity 36 (even), JSON parses at 38 mutations, WIREPIN PASS tasks=6 wiring=2, corpus 24/24 + 12/12.
- v1.39: Impl-plan audit v39 (codex) — must=2 should=2 nit=1 against v1.37. TWO of its four findings (the 18 missing mutation mechanisms, and the hmad-dispatch.sh:513 Codex fallback enumeration) were the SAME defects agy raised in the same cycle and were already applied at v1.38 — independent convergence on both surfaces, which is the strongest evidence either produces. NEW MUST, and it is the wire-pin numbered-label defect recurring: Task 3 declares TWO connections with BARE **WIRE**/**WIRE-PIN** labels, so the gate parses both with suffix None, pairs both wires with the LAST pin, and registers both under the single identity (pin-agents-tail-banner, Task 3) — the _agent_tail_re record upserts the _orca_tail_sig one and the _orca_find -> _orca_tail_sig connection vanishes from .h-mad/wires.jsonl. Measured before the fix: the registry held only Task 3 -> _agent_tail_re (wanted) and Task 4 -> _agent_tail_re (rival), NO _orca_tail_sig row, while the gate printed WIREPIN: PASS ... registration: registered=3 skipped=0. It fails CLOSED: a lost connection and a green verdict are the same output. Labels numbered WIRE 1/WIRE-PIN 1 and WIRE 2/WIRE-PIN 2; after re-registration the registry carries Task 3 (WIRE 1) -> _orca_tail_sig with its own pin, and the stale collapsed record was removed after proving a superseding row with the same caller/callee/pin exists. NEW SHOULD: AC-3.17 said none of the 24 probes matches 'the anchored one' two paragraphs before reporting that the anchor-only revision declines 7 of 24 — rewritten to name the current bounded grammar and point at the normative block. NIT NOT REPRODUCED: the stray closing ** after 'both directions' in AC-4.6 is not present in these bytes (line 943 is clean); it was fixed in an earlier cycle and the report is describing a version that no longer exists. Re-verified: fence parity 36, 38/38 mutations carry _mechanism, WIREPIN PASS, corpus 24/24 + 12/12, test_hmad_dispatch.py 290 passed.
- v1.40: Impl-plan audit v40 (agy) — must=1 should=1, all three sites applied. MUST: two production edits were DESCRIBED in prose and prescribed nowhere, which breaks the exact-code invariant by leaving the implementer to invent wording an AC then asserts. (a) AC-3.18 mandates correcting _agent_pv_re's own source comment — the claim 'neither occurs in ordinary prose about a model', falsified 24/24 — but gave no replacement text; exact sh block added, replacing only the comment's final line and naming the two prose examples that still decline. (b) T5's SKILL.md:315 amendment existed ONLY inside the test's _CODEX_CLAIM_NEW constant, so the production markdown edit was unprescribed; exact markdown block added and verified to flatten to exactly _CODEX_CLAIM_NEW, since both are read through _SKILL_MD_FLAT. SHOULD: AC-3.14 required a source-pinned call-form assertion with whitespace collapsed but supplied no test block, unlike AC-2.7 and Task 5; exact python added, asserting BOTH directions — the positive alone passes on a file that also carries the local form elsewhere, the negative alone passes on a file that dropped the call. Re-verified: 50 fence markers (even, counting INDENTED blocks — the line-anchored count used in earlier cycles saw only unindented ones and had been reporting on a subset), 38/38 mutations carry _mechanism, WIREPIN PASS tasks=6 wiring=2, corpus 24/24 + 12/12.
- v1.41: Impl-plan audit v40 (codex) — must=1 should=3 nit=2 against v1.39. Its MUST was the same unprescribed-exact-code defect agy raised in the same cycle, already applied at v1.40. CORRECTION: at v1.39 I recorded codex's AC-4.6 stray-marker nit as NOT REPRODUCED and that was WRONG — the stray closing ** sits on the line AFTER the words 'both directions', so a single-line grep for the phrase plus the marker found nothing and I read absence of a match as absence of the defect. The same report raised it twice and was right twice. Fixed by opening the sentence with the matching marker. SHOULD 1: Task 3's wire rationale still said an empty tail_re makes 'a prose-only tail resolve' — true of the prose-ONLY fixture AC-3.17 carried before v1.30, and the sentence outlived the fixture; with the MIXED fixture both candidates match, the count is 2, and the pass declines on AMBIGUITY. The mutation's own _mechanism already said ambiguity; this surface did not. SHOULD 2: AC-3.17 called the prose false positive a violation of FR-2, but FR-2 is only the exactly-one CARDINALITY rule — a single prose pane matching is ONE match, so FR-2 is satisfied while the resolution is still wrong. It is FR-1 / spec AC-1.4, the wrong-pane rule, as v1.25's own history says. Swept by VALUE: the same mislabel sat inside tail-re-unanchored's _mechanism, and 0 stale FR-2 references remain. SHOULD 3: the design's Components inventory omitted both T5 sites the plan now requires (hmad-dispatch.sh:513, SKILL.md:315), so the plan's claim to map all work onto design steps was broader than the declared source; two rows added. NIT: AC-6.5 described a mutation deleting the rival-rejection continue, while drop-rival-rejection keeps the block and replaces its condition with 'if false' — corrected, with the reason recorded (deleting the continue also changes control flow, so the kill could be credited to that instead). Re-verified: 50 fence markers, 38/38 mechanisms, WIREPIN PASS, corpus 24/24 + 12/12.
- v1.42: Impl-plan audit v41 (agy) — must=2 should=0, and BOTH musts are defects in work from the last two cycles. MUST 1: test_tail_pass_call_form_is_source_pinned, which I ADDED at v1.40 to satisfy audit v40's should-fix, would fail against a CORRECT implementation — it asserts 'if local tout=' not in the flattened wrapper source, but T3's own prescribed block bans that idiom BY NAME in a comment, so the forbidden substring is something the file is REQUIRED to document. Measured by flattening the prescribed block: present True without a comment strip, False with it. The test now strips comment lines first and the reason sits beside it; local-masks-helper-rc is still killed because it rewrites the ACTIVE line, re-checked. The general rule: a source assertion whose forbidden string is something the file must also explain has to exclude the explaining surface, or the ban and its rationale cannot coexist. MUST 2: AC-6.10 prescribed the harness as ~/.claude/skills/h-mad/scripts/h_mad_mutation_harness.py while every other verification command here is repo-relative — it resolves on this machine ONLY because ~/.claude/skills is a symlink INTO this repo, so the command worked while being wrong and would fail for any other checkout. Now relative, and swept as a CLASS: no absolute ~/ or /Users path remains in any prescribed command across spec, plan, impl-plan or design, the spec root is still '../..' and no mutation names an absolute file. Re-verified: both assertions hold against the prescribed block, 38/38 mechanisms, WIREPIN PASS, corpus 24/24 + 12/12.
- v1.43: Impl-plan audit v41 (codex) — must=2 should=3. BOTH musts were identical to agy's on the same bytes and already applied at v1.42 (the self-falsifying source assertion; the absolute harness path): two surfaces, one cycle, the same two findings. SHOULD 1 is the value-sweep lesson landing on me twice in two cycles: at v1.41 I corrected 'the wrong-pane class FR-2 forbids' in THIS document and its mutation mechanisms and stopped there, leaving the identical sentence in the source plan (:85) and the design (:126) — the paired-surface half the sweep exists for. Both corrected to FR-1 / spec AC-1.4 with the reason stated (one prose pane matching is exactly ONE match, so FR-2's cardinality rule holds while the resolution is wrong), and the plan's goals list, which mapped 'never resolve to the wrong pane' to FR-2 alone, now names both halves. The only surviving instance is inside the v1.23 history entry, which is a record rather than a live claim. SHOULD 2: the header cited design v1.33 while the design is v1.34, and T5 still said the design's Components table 'does not name' the :1046 cross-reference — a row that has been there since v1.33 because this plan's own audit put it there; the back-propagation landed and the sentence describing its absence did not follow. Prose and the test-block comment both corrected. SHOULD 3: T4 said Pass 2 applies 'the identical predicate' to .preview one sentence after establishing that Passes 1-2 use prose-permissive _agent_pv_re while this pass uses _agent_tail_re — reworded so what Pass 2 shares is the RULE (reject a rival-bearing candidate before counting it), not the regex. Re-verified: WIREPIN PASS, 50 fences, 38/38 mechanisms, corpus 24/24 + 12/12.
- v1.44: Impl-plan audit v42 (agy) — must=5, and FOUR DO NOT REPRODUCE. The report describes NameErrors inside three test bodies (test_tail_pass_prose_mentioning_agent_does_not_resolve, test_tail_sig_times_out, test_tail_stub_read_helpers_shape) naming undeclared STUB_ORCA_READ_DIR / STUB_ORCA and missing tmp_path parameters. Measured: this plan contains SIX 'def test_' blocks and none is any of the three, and h-mad/tests/test_hmad_dispatch.py defines none of them either — the feature is at Phase 5 RED, so those node names exist only in the RED table and as mutation pins. There is no source anywhere for the bodies quoted. Verifying before acting is the only reason four phantom fixes were not applied; a confident report is not evidence. The fifth is PARTLY true. Its premise is wrong — the proof column names what makes a GREEN-AT-RED node discriminating (13 rows), not an index of all 38 mutations; a RED: FAIL node carries '—' and every mutation is pinned by its own test field, so 16 uncited mutations are uncited BY CONTRACT. But three of them pin to green-at-RED nodes whose rows named only one proof each — tail-re-widened-to-launch-line-agy on AC-3.2, wire-rival-matcher-forced-empty on AC-4.6, skill-md-description-reworded on AC-5.3 — leaving a second guard unaccounted for in the one table meant to account for it. All three added; re-checked mechanically, zero green-at-RED mutations are now missing from their proof column. The contract is now stated beside AC-6.12 so this is answered in the document rather than re-filed. Also corrected: wire-rival-matcher-forced-empty's _mechanism named AC-4.1's fixture while it pins AC-4.6's node. Re-verified: 45 rows, 38 mutations, WIREPIN PASS, corpus 24/24 + 12/12.
- v1.45: Impl-plan audit v42 (codex) — must=1 should=1, and the must is a real semantic widening of the normative grammar. Executed the prescribed block: 'OpenAI Codex (v0.145.0', 'OpenAI Codex v0.145.0)', 'OpenAI Codex 2026', 'Antigravity CLI 2026' and 'Gemini 3.1 Pro (2026)' ALL MATCHED, although the design states a version is dotted-numeric with paired parens. The codex arm made ( and ) independently optional and used (dot-digits)* ; both agy version positions allowed zero dots. A release-notes heading was therefore identity evidence — the FR-1 / spec AC-1.4 wrong-pane class, and the fifth demonstration that this corpus is only as strong as the shapes in it. Both arms tightened (paired forms as alternatives; every version position requires at least one dot); measured after, the 5 shapes decline and all 12 positives still match. DELIBERATELY NOT tightened: bare 'gemini <N>' with no dot — requiring one would decline a future 'Gemini 4 Pro' banner, a false negative on a real banner, and the dotted rule governs VERSION continuations rather than the product's own model number. Corpus 24 -> 29, swept by VALUE across all four documents, and only one of the two distinct 24s moved: _agent_pv_re's prose-match figure was RE-MEASURED over the new corpus (29/29) rather than edited, the superseded-grammar comparisons are labelled 'then-24' instead of silently renumbered, and the unrelated '24 of 290 collected' selector count was left alone. New mutation tail-re-version-loosened reverts the tightening on the codex arm ALONE so the 12 positives survive and the kill can only come from the closed shapes — proven discriminating: applied, the corpus reports exactly 3 wrong negatives and 0 wrong positives. 38 -> 39 mutations, 39/39 with _mechanism. SHOULD: provenance cited design v1.34 (actual v1.35), and the design-step mapping row described step 1 as '_orca_tail_sig + unit tests' while the design ships both helpers there — the design was correct and the mapping row was the stale surface.
- v1.46: Impl-plan audit v43 (agy) — must=3, two real and both mine. The paired codex v43 run FAILED on infrastructure (RUN_RC=1, 'ERROR: Selected model is at capacity', no report), so there is no codex verdict for v1.45 and none is inferred from its absence; re-dispatched. MUST 1: the v42 tightening moved both arms of the normative block and ORPHANED the four mutation anchors pointing into them — tail-re-unanchored, tail-re-unanchored-agy, tail-re-widened-to-launch-line and tail-re-widened-to-launch-line-agy still carried the pre-v42 (dot-digits)* form. The harness REFUSES on a non-matching anchor rather than failing, so those four guards would have measured nothing while the spec still printed a verdict-shaped line. This is the exact class filed as a scout candidate two days ago ('editing a code block orphans the anchors pointing into it'), committed one cycle after writing it down. Re-anchored and then resolved every anchor MECHANICALLY against both the doc's code blocks and the live target files: 39/39 resolve, 0 nowhere. tail-re-version-loosened deliberately still carries the OLD form as its REPLACE and its find still resolves — checked separately so the re-anchoring could not silently neuter the mutant that proves the tightening. MUST 2: WIRE-PIN declarations named tests/test_hmad_dispatch.py while every WIRE beside them is repo-relative; now h-mad/tests/..., registry re-registered with repo-relative pins on all three rows. NOT REPRODUCED: 'stub-branch-ignores-env-var's find is missing ; _prev=""' — the find is a partial-line anchor ending at _h="" and the block reads _h=""; _prev="", so it matches as a substring; verified resolving. Re-verified: 39/39 anchors, WIREPIN PASS, corpus 29/29 + 12/12.
- v1.47: Impl-plan audit v44 — agy GATE PASS must=0 should=0 nit=0, codex must=1 should=1, both on v1.46. codex breaking an agy clean is the SIXTH time on this branch, and both of its findings are carried counts of mine rather than new defects. MUST: the proof-column explanation added at v1.44 said 'not an index of the 38 mutations' and v1.45 then added tail-re-version-loosened, making it 39 — a live count carried across a change I made myself one cycle earlier, which is the invariant this project has broken most often. Re-derived from the embedded JSON (39) rather than edited to match the report, and the sentence now names the transition so the historical 38 references stay readable. SHOULD: the provenance header cited design v1.35 and spec v1.17 while both had moved to v1.36 and v1.18 in the same v42 commit that this plan's matcher tightening depends on. Re-derived after: 39 mutations, 45 nodes (32 FAIL / 13 PASS), WIREPIN PASS tasks=6 wiring=2, corpus 29/29 + 12/12. The only surviving live '38' is the parenthetical recording the transition.
- v1.48: Impl-plan audit v45 (agy) — must=1 should=1 nit=1, and agy's own v44 clean broke one cycle later for the second time (v38 -> v39 was the first). All three trace to my recent edits. MUST: T6 claimed every find/replace value is 'the exact strings pinned in T2/T3/T4's code blocks, so an anchor here and the code there cannot drift'. False for three mutations that target code this feature does NOT prescribe — wire-force-fire-after-pass0 (Pass 0's _orca_find_by_pane entry), stub-branch-above-capture (the stub's pre-existing argv capture) and skill-md-description-reworded (SKILL.md's description field). Those anchor into LIVE files, so an unrelated edit orphans them silently and the harness REFUSES rather than failing. The claim now names both classes, names the three, and cites the check that actually covers them — resolve every find against the union of the prescribed blocks AND the live target file, requiring 39/39, which is what v1.46 ran. SHOULD: AC-6.12…AC-6.20 said 'Seven proofs, one per node' while AC-3.2 and AC-5.3 have carried a SECOND proof each since v1.32/v1.44 (tail-re-widened-to-launch-line-agy, skill-md-description-reworded) — required by the JSON and by the Test-name contract table but missing from the task's own enumeration. Now nine proofs across seven nodes. NIT: the Verification section named test_tail_pass_names_tail_evidence, a node that has never existed; the real one is test_skill_md_names_tail_evidence_pass. Re-verified: 39/39 anchors resolve against blocks-or-live, 0 references to the phantom node name, WIREPIN PASS tasks=6 wiring=2, corpus 29/29 + 12/12.
- v1.49: Impl-plan audit v45 (codex) — must=1, real. The normative grammar accepted two shapes the paired design excludes; executing the block matched '> OpenAI Codex', ': OpenAI Codex', '| model: gpt-5.6-terra', 'gpt-5.6-terra high ·' and the agy mirrors. The prefix class admitted ASCII pipe, colon and > — a v29 revision called them 'quote' characters and this document's comment said so, while the design said whitespace or box-drawing ONLY; the surfaces disagreed and the block followed the looser one, so a shell that printed a README blockquote naming the agent was identity evidence (FR-1 wrong-pane class). And 'a · and a cwd' was enforced as [^[:space:]]*, so a bare separator matched. Both closed; six shapes decline, 12/12 positives still match. The boundaries live in five mutation strings as well as the block and four encode the box-drawing characters as JSON escapes, so a text replace found 4 of 9 — done in DECODED space per entry, then all anchors resolved against blocks-or-live: 41/41. Corpus 29 -> 35, swept by value across four documents; _agent_pv_re re-MEASURED (35/35), then-24 comparisons kept, the unrelated 29/11 node aggregate left alone. Two revert-mutants anchored on the whole codex arm line, proven discriminating: prefix-widened -> exactly 3 wrong negatives / 0 wrong positives, cwd-optional -> exactly 1. 39 -> 41 mutations, 41/41 mechanisms; version-loosened still reverts to the pre-v42 form. Re-verified: 35/35 + 12/12, WIREPIN PASS, 41/41 anchors, 50 fences.
- v1.50: Impl-plan audit v46 — agy GATE PASS must=0 should=0 nit=0 (its third clean: v38, v44, v46), codex must=1 should=2, both on v1.49; the SEVENTH time codex has broken an agy clean. All three findings are consequences of my v45/v49 edits. MUST: the revert-mutants I added were scoped to 'the codex arm alone' — prefix-widened and version-loosened — while the agy arm encodes the SAME boundaries independently and the corpus carries agy negatives for them ('> Antigravity CLI 1.1.22', '| Gemini 3.1 Pro', 'Antigravity CLI 2026', 'Gemini 3.1 Pro (2026)'); no mutant could attribute a kill to those, since tail-re-unanchored-agy replaces the whole arm. Added tail-re-prefix-widened-agy and tail-re-version-loosened-agy, positive-preserving, anchored on the whole agy arm, pinned to AC-2.12; proven discriminating — each kills on exactly its two agy negatives and 0 positives. The version mutant loosens BOTH agy version positions together, because loosening one would be killed by one negative and prove nothing about the other. 41 -> 43 mutations, 43/43 anchors resolve, 43/43 mechanisms. The design paragraph that named only the codex pair now states the per-arm rule. SHOULD 1: AC-6.12…AC-6.20 said 'nine mutations for nine AC numbers' while enumerating eleven (nine proofs + two SIGPIPE) — the numbers are identifiers, not a tally, and the AC now says so. SHOULD 2: provenance cited design v1.36 / spec v1.18, actual v1.37 / v1.19. Re-verified: corpus 35/35 + 12/12, WIREPIN PASS tasks=6 wiring=2.
- v1.51: Impl-plan audit v47 (agy) — must=2 should=0, and agy's own v46 clean broke one cycle later for the THIRD time (v38->39, v44->45, v46->47). One real, one not reproduced. MUST (real): T6's class-2 list — mutations anchoring into LIVE files rather than prescribed blocks — said 'exactly three' and omitted skill-md-frontmatter-renamed. Its anchor 'name: h-mad' does appear in this plan, but only inside a TEST ASSERTION in AC-5.3's block, which is why the blocks-or-live check I ran at v1.48 counted it as class 1; an assertion is not a prescribed edit, and the live SKILL.md frontmatter is what the mutation rewrites. Re-derived by classifying each anchor's python block as prescribed helper vs test: three others (stub-read-env-not-array, stub-read-dir-writes-one-file, harness-ambient-timeout-not-scrubbed) sit in T1's prescribed _orca_read_env / _isolated_env helpers and are class 1; only the frontmatter one is class 2. Now 'exactly four', with the reason the naive check misclassifies it. NOT REPRODUCED: 'Task 1 states its insertion point is IMMEDIATELY AFTER _hostile_comment (before [ "$1" = "worktree" ])' — that text does not exist in this plan. T1's actual landmark is 'after the terminal create branch and before the default --json success envelope', verified against the live stub: terminal create at :103, the default envelope at :112. Re-verified: corpus 35/35 + 12/12, WIREPIN PASS.
- v1.52: Impl-plan audit v47 (codex) — must=2 should=1 nit=1, all four traceable to my v49/v50 edits. MUST 1 (fair): the two version revert-mutants changed several independently-encoded guards at once — tail-re-version-loosened unpaired the codex parens AND loosened both dot rules, tail-re-version-loosened-agy loosened both agy positions — so a corpus kill proved only that at least one guard bit, against the plan's own one-control-per-mutation rule. Split into FIVE single-field mutants on the shared arm anchors (cx-parens-unpaired, cx-bare-version-undotted, cx-paren-version-undotted, agy-cli-version-undotted, agy-paren-version-undotted), each measured to kill on exactly its own negative(s) with 0 wrong positives. The codex parenthesised-version field had no negative exercising it alone, so 'OpenAI Codex (v2026)' was added: corpus 35 -> 36, swept across four documents, _agent_pv_re re-measured 36/36. 43 -> 46 mutations, 46/46 anchors, 46/46 mechanisms. MUST 2: the unanchored mechanisms carried false counts — codex claimed all 35 negatives although it touches only the codex arm; agy said 10 from a corpus that has grown since. Measured by applying each: codex 22/22 of its arm's negatives, agy 14/14, 0 cross-arm, 0 positives. SHOULD: provenance design v1.37 -> v1.38. NIT: the design's case-fold paragraph said 'all three wire mutations'; there are four (wanted/rival × disconnect/force). The design's per-arm paragraph now names the five single-field mutants. Re-verified: corpus 36/36 + 12/12, WIREPIN PASS tasks=6 wiring=2.
- v1.53: Impl-plan audit v48 — agy GATE PASS must=0 should=0 nit=0 (fourth clean: v38, v44, v46, v48) and codex must=0 should=2 nit=1, BOTH on v1.52: must=0 on both surfaces for the second time (v38 was the first). The codex run took three attempts — the first two died on 'Selected model is at capacity' with no report and were not scored. SHOULD 1: provenance one revision behind again (design v1.38 -> v1.39, spec v1.19 -> v1.20); the header lags every time a paired document is bumped in the same commit, and it is re-derived from the two version-history tails here. SHOULD 2: the AC-6.12…AC-6.20 paragraph said 'NINE proofs across seven nodes' and read as a competing inventory against the Test-name contract table (13 green-at-RED rows, 16 mutations pinned to them); it now states that the table is the ONLY inventory, that this range enumerates a SUBSET, and names the seven other green-at-RED proofs and the ACs that own them. NIT: AC-3.2's rationale said the old form asserted 'banner-only also resolves' — banner-only is SUPPOSED to resolve; the old assertion was about a LAUNCH-COMMAND-only tail. Re-verified: corpus 36/36 + 12/12, WIREPIN PASS.
- v1.54: Impl-plan audit v49 (agy) — must=1, a real logic defect in the prescribed code that survived nineteen cycles because it is unreachable through _resolve_target. T4's text claimed that for a token other than codex/agy, rival stays empty and '_agent_tail_re "" falls to the *) arm, so the guard degrades to the shared helper'. Measured 2026-09-02: _agent_pv_re "" prints an EMPTY string, the *) arm wraps it as ^[[:space:]]*([^[:alnum:]]{0,8}[[:space:]]*)?() which matches EVERY line, [ -n "$rival_tail_re" ] is then true, and every candidate is rejected as a rival — the opposite of the claim. Fix: the assignment is guarded on the TOKEN (if [ -n "$rival" ]) with an explicit rival_tail_re="" first, because local alone leaves the name UNSET and the guard would abort under set -u. The rejection guard itself stays [ -n "$rival_tail_re" ], so an empty matcher still means 'no rejection' and wire-rival-matcher-disconnected keeps its meaning. The three mutations anchored on the assignment line were re-anchored to its new 4-space indentation in the same edit; 46/46 anchors resolve, each rival anchor exactly once. Proven: under set -u, empty rival -> guard false, candidate kept, no abort. Re-verified: corpus 36/36 + 12/12, WIREPIN PASS.
- v1.55: Impl-plan audit v49 (codex) — must=0 should=1 on v1.53 (agy v49 must=1 on the same bytes, applied at v1.54). Both surfaces at must=0 or the single v1.54 fix on v1.53. SHOULD: the paired design's Verification item 2 omitted the '-k test_tail_' selector and the MUTATION: ALL_CAUGHT / ANCHORS: ANCHORS_OK stdout-token checks that this plan's Verification and AC-6.9/AC-6.10 require, while claiming to list the same Success Criteria; aligned in the design (v1.40). Provenance here re-derived: design v1.40.
- v1.56: Impl-plan audit v50 — agy GATE PASS must=0 should=0 nit=0 (fifth clean), codex must=0 should=1, both on v1.55. SHOULD: T4's anchor paragraph still said the rival-assignment anchors are 'unaffected … two-space indentation' — written at v1.37 and true then, false since v1.54 moved the assignment inside the if [ -n "$rival" ] guard and re-anchored the three mutations to four spaces. The spec was already correct; the explanation was the stale surface, and it is the re-anchor discipline it describes applied to itself late. Corrected. Re-verified: all three rival anchors are the four-space form, corpus 36/36 + 12/12, WIREPIN PASS.
- v1.57: Impl-plan audit v51 — agy GATE PASS (sixth clean, second consecutive), codex must=1 should=1 nit=1, both on v1.56. MUST: AC-6.9 and AC-6.12…AC-6.20 require each mutation's mechanism line to name its pinned node, and 24 of 46 _mechanism strings did not carry the exact node id from their own test field — the 18 I wrote at v1.38 did, the 20 that predate the convention and 6 later ones did not. Amended mechanically from each entry's test field (the truth), appending 'Pinned node: <id>'; 46/46 now carry it, re-derived. SHOULD: the design said 'no config' and 'None user-facing' while telling operators to lower HMAD_TAIL_READ_TIMEOUT; classified in the design as an operator override of the HMAD_SNAPSHOT_LINES kind (code comment + design, NOT SKILL.md) — and my first wording of that claimed 'none of the sibling knobs appear in SKILL.md', which was FALSE: HMAD_CONTEXT_WINDOW appears three times, HMAD_SNAPSHOT_LINES zero; the classification now states the split and which side this knob is on. NIT: 'All all 14 AGY-arm negatives' — a duplicate word my v52 count sweep produced. Provenance re-derived to design v1.41. Re-verified: 46/46 anchors, corpus 36/36 + 12/12, WIREPIN PASS.
- v1.58: Impl-plan audit v52 — agy GATE PASS (seventh clean, third consecutive), codex must=1 nit=1, both on v1.57. MUST: three verification sites invoked h_mad_mutation_harness.py by BASENAME (AC-6.9, the AC-6.10 prose head, Verification item 2) and one in the paired design; the script is not on PATH and not executable (mode rw-r--r--), so the bare form exits 127 and can never print MUTATION: ALL_CAUGHT — the mutation-verdict step was unexecutable as written, and it contradicted AC-6.10's own repo-relative rule one paragraph below. All four now 'python3 h-mad/scripts/h_mad_mutation_harness.py'; verified the repo-relative form runs (--help prints usage). The :606 source reference is a citation, not a command, and stays. NIT: Task 2's comment stated the prefix rule twice in one sentence after the v45/v47 edits appended to it instead of rewriting it; consolidated into one ordered list of the four constraints. Provenance re-derived to design v1.42. Re-verified: corpus 36/36 + 12/12, WIREPIN PASS.
- v1.59: Phase 5d, Task 1 RED, first dispatch — STATUS: BLOCKED, and both causes are defects in THIS document that 53 audit cycles could not see because the tests did not exist yet (the tracer-bullet class). (1) T1's _orca_read_dir helper prescribed tempfile.mkdtemp(dir=tmp_path, prefix='reads-') inside the test module, and the module's own guard test_no_mkdtemp_and_no_pin_file_leak_guard asserts that literal is ABSENT from the source — the scoped run gave 3 failed / 293 passed instead of the expected 2, the third being that guard; verified by re-running myself. The fresh-directory-per-call property is kept with tmp_path / f'reads-{uuid.uuid4().hex[:8]}' (uuid already imported), and the helper's comment names the guard. (2) Codex named all six T1 tests differently from the Test-name contract table (test_orca_stub_terminal_read_dir_serves_handle_file for test_tail_stub_read_dir_serves_per_handle, etc.), which would have orphaned every T1 mutation pin and WIRE-PIN — because the 5d assembler cuts §Task N only and 39 of 45 AC bodies did not name their node; the names lived solely in a table outside every task section. Every AC body now carries **Node:** <name>, derived mechanically from the table (36 added; 6 already named theirs), so a task-scoped dispatch carries its contract. The dispatched test file was reverted (git checkout) rather than kept under invented names. Re-verified: both stub-read mutation anchors still resolve in the T1 helper block, corpus 36/36 + 12/12, WIREPIN PASS.
- v1.60: Phase 5 live-banner check: added the three real retained-tail lines to the corpus and updated the normative _agent_tail_re block. A banner may be DECORATED -- framed by box-drawing, preceded by block art, or preceded by the ">_" prompt glyph -- and may close with a frame character; what still separates banner from prose is the per-arm version/model/effort structure, or end of line. Corpus is now 36 negatives / 15 positives; mutation spec is now 49 mutations with new prefix-box-only, closing-frame-dropped, and bare-gt-prefix guards.
