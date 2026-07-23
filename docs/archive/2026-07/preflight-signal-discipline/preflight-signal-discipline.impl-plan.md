# Implementation Plan: preflight-signal-discipline

> Source: docs/02-design/features/preflight-signal-discipline.design.md (post-audit, v1.2)
> Branch target: feature/191-preflight-signal-discipline

## Executive Summary

Three serial tasks: isolate the pin file inside the test harness so the suite is trustworthy, add the
`PREFLIGHT:` verdict to `_cmd_env`, then codify the mandated reads in `SKILL.md` and the two
`references/` consumers.

**Execution mode: serial.** Tasks 1 and 2 both modify `h-mad/tests/test_hmad_dispatch.py`, so
worktree fanout would produce a guaranteed merge conflict on that file. Task 1 must land first
regardless — until it does, every suite run in this repo is unreliable, which is precisely what the
later tasks are measured against.

---

## Task 1: pin-file isolation in the test harness

**Production file**: `h-mad/tests/test_hmad_dispatch.py`
**Test file**: `h-mad/tests/test_hmad_dispatch.py` (the harness is the unit under test; assertions
live beside it)

**Description**: `_pin_file()` in the shell resolves `${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}`,
a **cwd-relative** default, and pytest's cwd is the repo root — so the repo's real session pin file
is read by every test that does not set the variable. F13 previously stripped all `HMAD_ORCA_*` env
vars from `run()`, closing the env-var channel but not this one. Because SKILL.md Phase-5 preflight
*requires* `pin-agents` and Phase 5f *requires* the full suite, following the protocol guarantees
failures at 5f. Measured on this repo: **17 failed / 136 passed** with a pin file present, **153
passed** with it absent. Fix: `run()` supplies a default `HMAD_ORCA_PIN_FILE` pointing at a
never-created, PID-scoped path outside the repo, applied *after* the caller's `env` is merged so an
explicit value still wins.

**Code structure**:
```python
import atexit      # NEW module import
import tempfile    # NEW module import

# Module scope. Deliberately NEVER CREATED: _pin_file() only reads it via
# `[ -f "$pf" ]`, so a non-existent path IS the "no pin file" state and nothing
# needs cleaning up. tempfile.mkdtemp() would be wrong — it registers no cleanup,
# leaking an empty directory per pytest collection. PID-scoped because two suites
# can run concurrently on one machine.
# A Path, not a str: the RED tests pin the contract via .is_absolute() / .parents /
# .exists(), and the module already uses Path throughout (SKILL, WRAPPER, STUBS).
# str() is applied at the single point of use, since env values must be strings.
_NO_PIN_FILE = Path(tempfile.gettempdir()) / f"hmad-tests-absent-orca-pins-{os.getpid()}.env"


@atexit.register
def _remove_stray_pin_file() -> None:
    """Defensive: no test should ever create this path (all 10 pin-writing call
    sites pass an explicit HMAD_ORCA_PIN_FILE), but a future one might forget."""
    ...


def run(args, *, substrate=None, env=None, capture=None, cwd=None):
    ...
    if env:
        e.update({k: v for k, v in env.items() if k != "_BINDIR"})
    e.setdefault("HMAD_ORCA_PIN_FILE", str(_NO_PIN_FILE))   # NEW — AFTER the update
    ...
```

**Acceptance Criteria**:
- [ ] AC-6.3: A test passing `HMAD_ORCA_PIN_FILE` in its `env` receives that exact value — assert by
      running `pin` with an explicit path and confirming the file is written there, not at the default.
- [ ] AC-6.4: `_NO_PIN_FILE` is not under the repository root — the module has no `REPO_ROOT`;
      the root is `SKILL.parent`. Assert `SKILL.parent not in _NO_PIN_FILE.parents`.
- [ ] AC-6.1 (mechanism): With a pin file written at the repo-relative default
      `.h-mad/orca-pins.env`, a `run(["resolve","agy"])` with no explicit pin file resolves
      `UNRESOLVED` rather than reading that file. Test must create the repo-relative file in a
      `tmp_path` cwd and pass `cwd=` so it never writes into the real repo.
- [ ] AC-6.5: `_pin_file()` in `h-mad/scripts/hmad-dispatch.sh` is unchanged — still
      `${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}`. Assert by reading the script text.
- [ ] Audit-v1 must-fix: no `tempfile.mkdtemp()` appears in the module, and `_NO_PIN_FILE` does not
      exist on disk after the suite runs.

**Dependencies on other tasks**: None

---

## Task 2: `PREFLIGHT:` verdict token in `_cmd_env`

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: `_cmd_env` (lines 273–308) already computes everything the verdict needs: `$stale`
accumulates agents whose handle the listing proves is gone (line 290), and the `CONFLICT:` block
(303–305) detects codex and agy resolving to one pane. Both are printed as prose that no orchestrator
step is obliged to read. Add a canonical terminal token line derived from those two existing values —
**not** a second detection pass. The existing conflict block additionally records
`conflict_handle="$seen_codex"` so the predicate lives in exactly one place (base "Single-source
contract"). Exit status is untouched: 0 on both verdicts, non-zero reserved for the pre-existing
"no substrate" operational error.

**Code structure**:
```bash
_cmd_env() {
  # existing: local a t stale="" seen_codex="" seen_agy=""
  local a t stale="" seen_codex="" seen_agy="" conflict_handle="" verdict="PASS" fields=""
  ...
  if [ -n "$seen_codex" ] && [ "$seen_codex" = "$seen_agy" ]; then
    conflict_handle="$seen_codex"        # NEW — one predicate, two consumers
    echo "CONFLICT: codex and agy both resolve to $seen_codex — at least one is wrong; pin them explicitly"
  fi
  if _orchestration_active; then echo "orchestration: on"; else echo "orchestration: off"; fi

  # NEW — must stay a TOKEN, never an exit code. A non-zero exit registers as a
  # Claude Code PostToolUseFailure and leaks into coexisting plugins' error
  # handling; invariants.base.md §"Audit-gate signal discipline" reserves non-zero
  # for genuine operational errors. Strengthen the signal by mandating a READ.
  [ -z "$stale" ] || { verdict="FAIL"; fields=" stale=$(printf '%s' "$stale" | tr ' ' ',')"; }
  [ -z "$conflict_handle" ] || { verdict="FAIL"; fields="$fields conflict=$conflict_handle"; }
  echo "PREFLIGHT: ${verdict}${fields}"
  return 0
}
```

**Acceptance Criteria**:
- [ ] AC-1.1: With nothing wrong, stdout contains a line exactly equal to `PREFLIGHT: PASS`.
- [ ] AC-1.2: With one agent pinned to a handle absent from the stub listing, stdout contains a line
      starting `PREFLIGHT: FAIL` and containing `stale=codex`; with both, `stale=codex,agy`.
- [ ] AC-1.3: With codex and agy pinned to the same handle, the line contains `conflict=<handle>`.
- [ ] AC-1.4: With both conditions, one single `PREFLIGHT: FAIL` line contains both `stale=` and
      `conflict=`.
- [ ] AC-1.5: `PREFLIGHT:` is the **last** line of stdout, and the `substrate:` / `orchestration:` /
      `-> ` lines are byte-identical to before the change.
- [ ] AC-1.6: Exactly one line matching `^PREFLIGHT:` per invocation.
- [ ] AC-2.1 / AC-2.2: `returncode == 0` for a PASS verdict **and** for a FAIL verdict.
- [ ] AC-2.3: With no detectable substrate, returncode is non-zero and stdout contains no
      `PREFLIGHT:` line.
- [ ] AC-2.4: The source within 15 lines above the `echo "PREFLIGHT:` statement mentions both that
      the verdict must not become a non-zero exit and the string `PostToolUseFailure`.
- [ ] AC-3.1: Both agents `UNRESOLVED`, nothing stale, no conflict ⇒ `PREFLIGHT: PASS`.
- [ ] AC-3.2: The `<agent> -> UNRESOLVED` lines are still printed.
- [ ] AC-3.3: No `PREFLIGHT: FAIL` line ever contains `unresolved=`.
- [ ] Design edge case: an unreadable `orca terminal list` (garbage `HMAD_STUB_ORCA_STDOUT`) yields
      `PREFLIGHT: PASS`, because `_orca_handle_live` returns "unknown", not "dead".

**Dependencies on other tasks**: Task 1 (must complete first — same test file, and Task 1 is what
makes the suite result trustworthy)

---

## Task 3: mandated reads in `SKILL.md` and the `references/` consumers

**Production file**: `h-mad/SKILL.md`, `h-mad/references/orchestration-mode.md`,
`h-mad/references/agent-substrate.md`
**Test file**: `h-mad/tests/test_h_mad_preflight_docs.py` (new)

**Description**: The token is only worth adding if some step is obliged to read it — an unread token
is the same defect as an unread `STALE` line. Add the obligation to `SKILL.md`'s Phase-5 preflight
(assert `PREFLIGHT: PASS` before the first dispatch of a run; re-assert after any re-pin; halt
`<phase>:preflight_failed`; read the token, not `$?`) and to §"Audit prompt assembly" for
`ASSEMBLE: PASS`. Then fix the one behavioural consumer: `references/orchestration-mode.md:215,223`
wires `--precheck "hmad-dispatch env"` into an Orca automation, which gates on the **exit code** and
therefore cannot fail on a stale pin — the automation-shaped instance of this very bug. It becomes a
token test. `references/agent-substrate.md:25` documents the new output line.

**Code structure**:
```python
# h-mad/tests/test_h_mad_preflight_docs.py — doc-contract assertions, mirroring
# the technique already used by test_h_mad_audit_conditionals.py
SKILL_MD = REPO_ROOT / "h-mad" / "SKILL.md"
ORCH_MD  = REPO_ROOT / "h-mad" / "references" / "orchestration-mode.md"
SUBS_MD  = REPO_ROOT / "h-mad" / "references" / "agent-substrate.md"

def _phase5_preflight_section() -> str:
    """The Phase-5 substrate-preflight block of SKILL.md."""
    ...
```

**Acceptance Criteria**:
- [ ] AC-4.1: The Phase-5 preflight section instructs asserting `PREFLIGHT: PASS` before the first
      dispatch of a run.
- [ ] AC-4.2: The same section states the re-assert-after-re-pin requirement.
- [ ] AC-4.3: The same section names the halt `preflight_failed`.
- [ ] AC-4.4: The same section states the verdict is read from the token, not `$?`.
- [ ] AC-5.1: §"Audit prompt assembly" requires asserting `ASSEMBLE: PASS` before dispatching an
      assembled prompt.
- [ ] AC-5.2: That section states `ASSEMBLE: HALT` is a verdict to act on, not a tool failure, and
      that the exit code is 0 either way.
- [ ] AC-7.1: `references/orchestration-mode.md` contains no bare `--precheck "hmad-dispatch env"`;
      the precheck form present tests for `PREFLIGHT: PASS`.
- [ ] AC-7.2: The `env` row in `references/agent-substrate.md` mentions `PREFLIGHT:`.

**Dependencies on other tasks**: None (touches no file that Tasks 1 or 2 touch)

---

## Version History
- v1.1: 5d coverage review — strengthened the AC-6.1 assertion to name WHY resolution failed
  (rc=1 + empty stdout is also what a crashing wrapper yields), and pinned `_NO_PIN_FILE` as a
  `Path` rather than a `str`. The reviewer proposed casting inside the tests; that inverts TDD by
  treating the plan as authoritative over the test, so the implementation contract was changed
  instead.
- v1.0: Initial implementation plan draft.
