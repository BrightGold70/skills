# Brainstorm: preflight-signal-discipline

## Executive Summary

`hmad-dispatch env` already detects the two conditions that silently destroy a dispatch — a stale
pin and a codex/agy handle collision — but prints them as prose no step is required to read, so a
scripted `env && dispatch …` walks straight into them; give `env` a canonical `PREFLIGHT: PASS|FAIL`
stdout token and make reading it a mandated step, keeping exit 0 throughout.

## Problem Statement

Wave 1's remediation sequence (§Wave 2) records that `_cmd_env` prints `STALE` / `CONFLICT:` and
returns 0 unconditionally. That is *correct* per the signal invariant, but no orchestrator step is
obliged to consume it, so the detection is advisory. This is not hypothetical: it is the failure
that lost a Task-2 RED dispatch on HemaSuite — `Sent 7293 bytes` into a rotated handle, then no
error, no report file, and no tests written.

Folded in: **J7**, the same class one layer down. F13 closed the `HMAD_ORCA_*` env-var leak into
`test_hmad_dispatch.py::run()` but not the pin-**file** leak. `_pin_file()` resolves
`${HMAD_ORCA_PIN_FILE:-.h-mad/orca-pins.env}` — cwd-relative — so the suite reads the repo's real
pin file. Because SKILL.md Phase-5 preflight *requires* `pin-agents` and Phase 5f *requires* the
full suite, following the protocol guarantees failures at 5f on every run, in the repo whose own
tests they are.

**Reproduced this session** (`test_hmad_dispatch.py`, cwd = repo root):

| pin file | result |
|---|---|
| absent | 153 passed |
| present (`codex=…`, `agy=…`) | **17 failed**, 136 passed |

Matching the brief's measurement. An orchestrator that trusts the suite reads a real regression as
noise — or deletes its pins to get green and then dispatches into nothing.

## Proposed Approach

Two changes, both "make an existing signal consumable", which is why they are one feature.

**1 — `PREFLIGHT: PASS|FAIL` token on `env`.** A single terminal line matching the `GATE:` /
`ASSEMBLE:` / `STATE:` shape already in use. Exit stays 0 on both verdicts.

FAIL is raised by **STALE or CONFLICT only**. `UNRESOLVED` stays informational: an unpinned agent is
the ordinary state of any session not currently dispatching (agy is legitimately `UNRESOLVED` in
this repo right now), and a token that reads FAIL in routine use earns exactly the ignore that the
STALE line already suffers. Dispatch-readiness is separately enforced by `pin-agents`, which already
fails loud (rc=1) on an unresolved agent. So the token answers "is anything *wrong*", not "am I
ready to dispatch" — the two questions have different right answers and conflating them is what
would make the token noise.

**2 — mandated reads in `SKILL.md`.** Phase-5 preflight asserts `PREFLIGHT: PASS` before the first
dispatch of a run and re-asserts after any re-pin; §"Audit prompt assembly" 7.2 asserts
`ASSEMBLE: PASS`. `ASSEMBLE` already complies with the token shape and needs only the mandated read,
so both land under one convention rather than two half-conventions a wave apart.

**3 — J7: close the leak at the harness boundary and keep the production override.** `run()`
`setdefault`s `HMAD_ORCA_PIN_FILE` to a tmp path, so no test can reach the repo file, while the
tests that deliberately exercise pinning (which pass it explicitly) still win. This is symmetric
with what F13 did for the env vars, and it leaves `_pin_file()`'s documented default untouched.

## Alternatives Considered

- **Make `env` exit non-zero on STALE/CONFLICT** — rejected, and this is the trap the whole task is
  shaped around. `invariants.base.md:16-21` makes stdout-token + exit-0 a **base** invariant: a
  non-zero exit registers as a Claude Code `PostToolUseFailure` and leaks into coexisting plugins'
  error handling. `h_mad_audit_gate.py` already follows the rule (`GATE: FAIL` exits 0). The defect
  is an unmandated *read*, so the fix is a mandated read — not an exit code.
- **FAIL on any `UNRESOLVED` agent** — rejected. Makes `PREFLIGHT: PASS` mean "ready to dispatch to
  both agents", which is a useful question but a different one; `env` would then report FAIL in
  every ordinary session, and a token that cries wolf gets skimmed past exactly like the STALE line
  it replaces.
- **Move the production pin file out of the repo** (per-session path under `$HOME`/`$TMPDIR`) —
  rejected for this wave. It would fix J7 at the source, but changes runtime behaviour for every
  existing user and invalidates every doc naming `.h-mad/orca-pins.env`. Disproportionate to a leak
  whose blast radius is a test harness.
- **Fix J7 in the harness only, with no override honoured** — rejected as under-specified rather
  than wrong: `_pin_file()` already honours `HMAD_ORCA_PIN_FILE`, so "honour the override" is a
  statement about keeping it, and the harness change is the actual delta.
- **Split J7 into its own feature** — rejected. Both items are preflight correctness, and J7 is
  precisely what makes the Phase-5 preflight this wave strengthens produce a red suite at 5f.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| A future contributor "fixes" the weak signal by making `env` exit non-zero | M | State the prohibition *and its reason* in the code comment at the token site, not only in SKILL.md; add a test asserting exit 0 on a FAIL verdict |
| `PREFLIGHT: FAIL` becomes routine noise and gets skimmed | M | FAIL only on STALE/CONFLICT — conditions that are genuinely wrong, not merely un-set-up |
| Mandated read is documented but never performed (same failure, one level up) | M | This is the known limit of a doc-level mandate; Wave 3's dogfood run is what exercises it. Record it as a carry rather than claiming enforcement |
| Harness `setdefault` masks a test that *intended* to read a real pin file | L | `setdefault` preserves any explicit value, and the pin-exercising tests all set it explicitly today — assert that in a test |
| Token added to `env` breaks a caller parsing its current output | L | Additive line at the end; no existing line changes. Grep the repo for `env` output parsers |

## Dependencies

None. Wave 2 depends on nothing per the sequence doc, and blocks Wave 3 (whose dogfood run should
exercise the mandated reads).

## Open Questions

- Should `PREFLIGHT: FAIL` enumerate the offending agents (`stale=codex`) or stay a bare verdict?
  Leaning enumerate — the `GATE:` token carries counts and it costs nothing.
- ~~Does anything outside `SKILL.md` parse `env` output today?~~ **Resolved during brainstorm.**
  Nothing parses the *text*, but there is one behavioural consumer:
  `references/orchestration-mode.md:215` wires `--precheck "hmad-dispatch env"` into an Orca
  automation, which gates on the **exit code** — so today a scheduled run prechecks green against a
  stale pin, the automation-shaped instance of this very bug. Since the invariant forbids changing
  the exit code, the token gives that precheck a correct form for the first time:
  `--precheck "hmad-dispatch env | grep -q 'PREFLIGHT: PASS'"`. Worth updating in the same wave.
  `references/agent-substrate.md:25` documents the verb and needs the token noted. 38 test call
  sites invoke `run(["env"])`, so the token line must be **appended**, never inserted.
- J8 (`elapsed_min` ≈ 56 years) is adjacent — the writer's `started_ts` default is suspect — but it
  is filed and out of scope here. This feature passes an explicit `--started-ts` so its own record
  is sound.

## Version History
- v1.0: Initial brainstorm draft.
