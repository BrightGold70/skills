# Design: preflight-signal-discipline

## Executive Summary

Emit a `PREFLIGHT: PASS|FAIL` line as the final statement of `_cmd_env` derived from the two values
that function already computes, mandate reading it (and `ASSEMBLE:`) in `SKILL.md`, and give
`test_hmad_dispatch.py::run()` a tmp-path default for `HMAD_ORCA_PIN_FILE` so the repo's pin file can
no longer reach the suite.

## Overview

Every change is additive and local. The verdict is a *rendering* of `$stale` and the conflict
condition, not a second detection pass, so the token cannot disagree with the prose lines above it.
The exit code is untouched everywhere. The J7 fix goes in the same function F13 already hardened,
one channel over.

## Architecture Overview

```
hmad-dispatch env
  └─ _cmd_env()                     hmad-dispatch.sh:273-308
       ├─ _detect_substrate()       → non-zero ⇒ early return 1, NO token   (AC-2.3)
       ├─ per agent: _resolve_target() ─┐
       │                                ├─ _orca_handle_live()  (orca only, 3-valued)
       │                                └─ accumulates  $stale  /  $seen_codex,$seen_agy
       ├─ prints  "stale pins: …"   (existing, line 298)
       ├─ prints  "CONFLICT: …"     (existing, line 303-305)  ── sets $conflict_handle  ← NEW
       ├─ prints  "orchestration: …"(existing, line 306)
       └─ prints  "PREFLIGHT: …"    ← NEW, last line, from $stale + $conflict_handle
                                                                 exit 0 always      (FR-2)

pytest → run()                      test_hmad_dispatch.py:50-84
       ├─ pops every HMAD_ORCA_*    (F13, line 69-70)
       ├─ e.update(test's env)      (line 76)         ← explicit value lands here
       └─ e.setdefault(HMAD_ORCA_PIN_FILE, _NO_PIN_FILE)  ← NEW, after the update  (FR-6)
```

The ordering of the last two lines is the whole of FR-6's correctness: `setdefault` *after* the
update means a test that passes its own path keeps it (AC-6.3), and a test that passes none can no
longer fall through to the cwd-relative repo file.

## Detailed Design

### Component 1 — `PREFLIGHT` verdict in `_cmd_env`

**Derivation, not re-detection.** The conflict predicate already exists at `hmad-dispatch.sh:303`.
Re-testing `[ "$seen_codex" = "$seen_agy" ]` at the token site would place one rule in two locations,
which is exactly what the base "Single-source contract" invariant forbids, and the two copies would
drift the first time either is edited. Instead the **existing** conflict block records its finding:

```bash
  if [ -n "$seen_codex" ] && [ "$seen_codex" = "$seen_agy" ]; then
    conflict_handle="$seen_codex"                      # NEW — one predicate, two consumers
    echo "CONFLICT: codex and agy both resolve to $seen_codex — at least one is wrong; pin them explicitly"
  fi
```

`$stale` is likewise already accumulated by the existing loop (`stale="${stale:+$stale }$a"`); the
token reuses it verbatim.

**Emission**, appended after the `orchestration:` line and immediately before `return 0`:

```bash
  # PREFLIGHT verdict — the machine-readable form of the two lines above. Anything an
  # orchestrator must ACT on is a FAIL; anything merely un-set-up is not.
  #
  # This MUST NOT become a non-zero exit. A non-zero exit registers as a Claude Code
  # PostToolUseFailure and leaks into coexisting plugins' error handling, which is why
  # invariants.base.md §"Audit-gate signal discipline" reserves non-zero for genuine
  # operational errors only (here: no detectable substrate, handled above). GATE:/ASSEMBLE:
  # follow the same rule. Strengthen the signal by mandating a READ, never by changing $?.
  local verdict="PASS" fields=""
  if [ -n "$stale" ]; then
    verdict="FAIL"; fields=" stale=$(printf '%s' "$stale" | tr ' ' ',')"
  fi
  if [ -n "$conflict_handle" ]; then
    verdict="FAIL"; fields="$fields conflict=$conflict_handle"
  fi
  echo "PREFLIGHT: ${verdict}${fields}"
  return 0
```

Edge cases:

| Condition | Output | Why |
|---|---|---|
| nothing wrong | `PREFLIGHT: PASS` exactly, no fields | AC-1.1 requires `^PREFLIGHT: PASS$` |
| one stale agent | `PREFLIGHT: FAIL stale=codex` | AC-1.2 |
| both stale | `PREFLIGHT: FAIL stale=codex,agy` | `$stale` is space-separated; `tr` renders it comma-separated |
| conflict | `PREFLIGHT: FAIL conflict=term_x` | AC-1.3 |
| stale **and** conflict | `PREFLIGHT: FAIL stale=codex conflict=term_x` | one line, both fields (AC-1.4) |
| agent(s) `UNRESOLVED` | `PREFLIGHT: PASS` | FR-3 — `$stale` only grows on *positive* evidence of death |
| `orca terminal list` unreadable | `PREFLIGHT: PASS` | `_orca_handle_live` returns 2 (unknown); the existing `[ $? -eq 1 ]` guard is false, so `$stale` stays empty |
| no substrate | *no* `PREFLIGHT:` line, exit 1 | early `return 1` precedes all output (AC-2.3) |
| `substrate: cmux` | verdict computed the same way | `$stale` is orca-only in practice, so cmux yields `PASS` unless codex and agy share a surface |

`local verdict fields conflict_handle` are added to the existing `local` declaration at the top of
the function; `conflict_handle` must initialise empty so the `-n` test is well-defined under
`set -u`.

### Component 2 — mandated read, Phase-5 preflight (`SKILL.md:123`)

The existing paragraph says to run `env` and halt on non-zero. It gains the assertion:

- assert the stdout contains `PREFLIGHT: PASS` before the first `send` of a run;
- on `PREFLIGHT: FAIL`, halt `<phase>:preflight_failed`, naming the `stale=`/`conflict=` field;
- re-assert after any re-pin (`pin`, `pin-agents`, `launch`);
- read the **token**, never `$?` — `env` exits 0 on both verdicts by design.

### Component 3 — mandated read, audit assembly (`SKILL.md:412`)

The block already documents `ASSEMBLE: PASS|HALT`. It gains the explicit obligation to assert
`ASSEMBLE: PASS` before dispatching, and a restatement that `HALT` is a verdict to act on rather than
a tool failure (exit 0 either way).

### Component 4 — pin-file isolation in `run()` (`test_hmad_dispatch.py`)

Module scope. The module currently imports `json, os, shutil, subprocess, pathlib.Path` — **`tempfile`
and `atexit` must be added** (both stdlib, so no new dependency):

```python
import atexit     # NEW
import tempfile   # NEW

# J7: the pin file is the second channel into this harness. F13 stripped the
# HMAD_ORCA_* env vars, but _pin_file() falls back to a CWD-RELATIVE
# ".h-mad/orca-pins.env", and pytest's cwd is the repo — so a developer who
# followed the Phase-5 preflight (which requires pin-agents) saw 17 failures in
# the repo's own suite.
#
# This path is deliberately NEVER CREATED. `_pin_file()` only ever reads it via
# `[ -f "$pf" ]`, so a non-existent path is exactly the "no pin file" state, and
# nothing has to be cleaned up. `tempfile.mkdtemp()` would be wrong here: it
# registers no cleanup, so every pytest collection would leak an empty directory.
# Path, not str — consumed via .is_absolute()/.parents/.exists(); str() at point of use.
_NO_PIN_FILE = Path(tempfile.gettempdir()) / f"hmad-tests-absent-orca-pins-{os.getpid()}.env"


@atexit.register
def _remove_stray_pin_file():
    """Defensive only. Every pin-writing test passes its own HMAD_ORCA_PIN_FILE
    (verified: all 10 `run(["pin"…])` / `pin-agents` call sites do), so nothing
    should ever create this path. If a future test forgets, `pin` would `mkdir -p`
    and write here, contaminating later tests in the same run and leaving a file
    behind — so remove it rather than trusting the convention to hold."""
    try:
        os.unlink(_NO_PIN_FILE)
    except FileNotFoundError:
        pass
```

In `run()`, immediately after the `e.update(...)` on line 76:

```python
    # AFTER the update, so a test that passes its own HMAD_ORCA_PIN_FILE keeps it.
    e.setdefault("HMAD_ORCA_PIN_FILE", str(_NO_PIN_FILE))
```

`_pin_file()` in the shell is **not** changed: it keeps honouring `HMAD_ORCA_PIN_FILE` and keeps
defaulting to `.h-mad/orca-pins.env` (AC-6.5).

### Component 5 — documentation consumers

- `references/orchestration-mode.md:215,223` — the automation precheck becomes
  `--precheck "hmad-dispatch env | grep -q 'PREFLIGHT: PASS'"`, with a sentence explaining that the
  bare form gates on the exit code and therefore cannot fail on a stale pin.
- `references/agent-substrate.md:25` — the `env` row notes the terminal `PREFLIGHT:` token.

## Components Changed / Added

| Component | File path | Change type | Purpose |
|---|---|---|---|
| `_cmd_env` verdict emission | `h-mad/scripts/hmad-dispatch.sh` (273-308) | modify | FR-1, FR-2, FR-3 |
| `$conflict_handle` capture in existing CONFLICT block | `h-mad/scripts/hmad-dispatch.sh` (303-305) | modify | single-source predicate |
| Phase-5 preflight mandated read | `h-mad/SKILL.md` (§Phase 5 sub-steps, ~123) | modify | FR-4 |
| Audit-assembly mandated read | `h-mad/SKILL.md` (§Audit prompt assembly, ~412) | modify | FR-5 |
| `_NO_PIN_FILE` (never created) + `atexit` guard + `setdefault` | `h-mad/tests/test_hmad_dispatch.py` (module, ~76) | modify | FR-6 |
| Automation precheck example | `h-mad/references/orchestration-mode.md` (215,223) | modify | FR-7 (AC-7.1) |
| `env` row token note | `h-mad/references/agent-substrate.md` (25) | modify | FR-7 (AC-7.2) |
| Regression tests | `h-mad/tests/test_hmad_dispatch.py` | modify | all ACs |

## Implementation Order

1. **FR-6 first.** The pin-file leak makes suite runs unreliable; fixing it first means every
   subsequent step is measured against a trustworthy suite. It is also independent of the token.
2. `$conflict_handle` capture + `PREFLIGHT` emission (FR-1, FR-2, FR-3) — one shell edit.
3. Tests for FR-1/2/3 against the stub harness.
4. `SKILL.md` mandated reads (FR-4, FR-5) + doc-assertion tests.
5. `references/` consumers (FR-7) + doc-assertion tests.

## Data Model / Schema Changes

None. No state field, config key, or serialization format changes.

## API / Interface Changes

- **`hmad-dispatch env` stdout**: one additional final line, `PREFLIGHT: PASS` or
  `PREFLIGHT: FAIL[ stale=<a>[,<b>]][ conflict=<handle>]`. Additive; no existing line changes.
- **`hmad-dispatch env` exit status**: unchanged (0 on any verdict, non-zero only for no substrate).
- **`run()` test helper**: unchanged signature; supplies an `HMAD_ORCA_PIN_FILE` default.
- No new CLI flags. `--require-agents` is explicitly out of scope.

## Error Handling Strategy

- The verdict is **not** an error. `PREFLIGHT: FAIL` is a normal outcome reported on stdout with
  exit 0; the caller decides. This is the base invariant, and the design's central constraint.
- The only non-zero exit from `env` remains the pre-existing operational error "no substrate
  detected", which returns 1 before printing anything — so a `PREFLIGHT:` line and a non-zero exit
  can never co-occur.
- `_orca_handle_live`'s third state (listing unreadable) deliberately does **not** produce FAIL:
  absence of evidence is not evidence of a dead pane, and a pin exists precisely to survive a
  listing that cannot be read.
- Under `set -u`, every new variable is declared `local` with an empty initial value.

## Test Strategy

All tests are pytest against the existing stub harness in `test_hmad_dispatch.py`: `_bindir()` puts a
stub `orca` on PATH and `HMAD_STUB_ORCA_STDOUT` supplies a canned `terminal list --json` payload, so
verdicts are exercised without a live Orca. Doc-level ACs (FR-4, FR-5, FR-7) are asserted by reading
the markdown files — the same technique already used by `test_h_mad_audit_conditionals.py`.

Boundary: the shell wrapper is invoked as a subprocess (real bash), so the tests exercise the actual
emission code, not a Python re-implementation of it.

## Test Plan

| Test | Asserts | AC |
|---|---|---|
| `test_env_emits_preflight_pass_when_nothing_is_wrong` | stdout has a line `== "PREFLIGHT: PASS"` | AC-1.1, AC-1.6 |
| `test_env_preflight_fail_names_stale_agent` | `PREFLIGHT: FAIL` contains `stale=codex` | AC-1.2 |
| `test_env_preflight_fail_names_both_stale_agents` | `stale=codex,agy` | AC-1.2 |
| `test_env_preflight_fail_names_conflict_handle` | contains `conflict=term_one` | AC-1.3 |
| `test_env_preflight_reports_stale_and_conflict_together` | one line, both fields | AC-1.4 |
| `test_preflight_line_is_last_and_appends_only` | `PREFLIGHT:` is the final stdout line; `substrate:`/`orchestration:` text unchanged | AC-1.5 |
| `test_env_exits_zero_on_preflight_fail` | returncode == 0 with a FAIL verdict | AC-2.1, AC-2.2 |
| `test_env_no_substrate_exits_nonzero_without_a_token` | rc != 0 and `PREFLIGHT:` absent | AC-2.3 |
| `test_token_site_documents_the_exit_code_prohibition` | source near the emission mentions the prohibition + `PostToolUseFailure` | AC-2.4 |
| `test_unresolved_agents_still_pass` | both `UNRESOLVED` ⇒ `PREFLIGHT: PASS`; `-> UNRESOLVED` lines still printed; no `unresolved=` field | AC-3.1, AC-3.2, AC-3.3 |
| `test_unreadable_listing_does_not_fail_preflight` | garbage `HMAD_STUB_ORCA_STDOUT` ⇒ PASS | Assumptions |
| `test_skill_md_mandates_reading_preflight` | Phase-5 section names `PREFLIGHT: PASS`, re-assert, `preflight_failed`, token-not-`$?` | AC-4.1–4.4 |
| `test_skill_md_mandates_reading_assemble` | assembly section requires asserting `ASSEMBLE: PASS`; states HALT is a verdict, exit 0 | AC-5.1, AC-5.2 |
| `test_run_supplies_a_pin_file_outside_the_repo` | `run()`'s default path is not under the repo root | AC-6.4 |
| `test_explicit_pin_file_beats_the_harness_default` | a test-supplied `HMAD_ORCA_PIN_FILE` is the one used | AC-6.3 |
| `test_repo_pin_file_is_not_consulted_by_the_suite` | with a pin file written at the repo-relative default, resolution still finds nothing | AC-6.1 mechanism |
| `test_pin_file_default_and_override_unchanged` | `_pin_file()` still honours the env var and still defaults to `.h-mad/orca-pins.env` | AC-6.5 |
| `test_harness_pin_file_default_is_never_created` | the `_NO_PIN_FILE` path does not exist after a suite run, and no temp *directory* is allocated for it | audit v1 must-fix |
| `test_orchestration_mode_precheck_gates_on_the_token` | doc shows the `grep -q 'PREFLIGHT: PASS'` form | AC-7.1 |
| `test_agent_substrate_documents_the_token` | `env` row mentions `PREFLIGHT:` | AC-7.2 |

**AC-6.1 / AC-6.2 are verified at Phase 6 by measurement, not only by unit test.** The claim is about
the *whole suite* under a real repo-root pin file, which a unit test cannot assert about itself. The
procedure is the A/B already run at brainstorm time: write `.h-mad/orca-pins.env`, run
`h-mad/tests/`, remove it, run again, and require identical pass/fail counts. Baseline to beat:
**17 failed / 136 passed** with the file present.

## Invariant Compliance

**Base — Audit-gate signal discipline**: complies, and is the design's governing constraint. The
verdict travels as a stdout token with exit 0 for both PASS and FAIL; the only non-zero exit is the
pre-existing "no substrate" operational error. The prohibition is additionally encoded as a comment
at the emission site and asserted by a test (AC-2.4), because the invariant's consequence is
invisible from the call site.

**Base — Single-source contract**: complies. The conflict predicate stays at its existing site and
publishes `$conflict_handle` for the token to consume, rather than being re-evaluated; `$stale` is
reused verbatim. `_orca_handle_live()` remains the sole liveness oracle.

**Base — Standalone / no plugin dependency**: complies. No new runtime dependency; the shell change
uses builtins plus `tr`, and the test change uses stdlib `tempfile`/`os`.

**Base — No new external dependency**: complies. No new package or CLI.

**Base — Doc-template superset compliance**: complies. `SKILL.md` sections are extended, none
removed; frontmatter untouched.

**Base — Operator-override preservation**: complies. `HMAD_ORCA_PIN_FILE` remains an honoured
override in production and now also inside the harness; the env-var pins keep their precedence.

**Base — Backward compatibility**: complies. The token is appended, so the 38 existing
`run(["env"])` call sites and any line-oriented reader keep working. The one behavioural consumer
(the automation precheck) is updated in the same wave (FR-7).

**Base — Marker discipline**: complies. No `[H-MAD]` marker is added or changed; `PREFLIGHT:` is a
verdict token in the established `GATE:`/`ASSEMBLE:`/`STATE:` family, not a marker.

**Project — Skill self-containment**: complies. All edits are inside `h-mad/`; no cross-skill import
and no hardcoded path outside the skill or the documented `~/.claude/...` locations.

**Project — Skill manifest integrity**: complies. `SKILL.md`'s frontmatter `name`/`description` are
unchanged, and its documented entry behaviour is extended in-place rather than altered — the verb
`env` keeps its contract and gains an output line.

## Version History
- v1.0: Initial design draft.
- v1.3: 5d coverage review — `_NO_PIN_FILE` is a `Path` (the RED tests consume it as one);
  `str()` applied where it enters the env dict.
- v1.2: Audit v2 nit (non-blocking, taken) — PID-scope `_NO_PIN_FILE` so concurrent suite runs on
  one machine cannot collide. Not hypothetical: two sessions ran this repo's suite on 2026-07-22.
- v1.1: Audit v1 must-fix — replaced module-scope `tempfile.mkdtemp()` (which registers no
  cleanup, leaking an empty directory per collection) with a never-created static path plus an
  `atexit` guard. Verified first that all 10 pin-writing call sites pass an explicit
  `HMAD_ORCA_PIN_FILE`, so nothing writes the default; the guard is defensive against a future test
  that forgets. Added a regression row to the Test Plan.
