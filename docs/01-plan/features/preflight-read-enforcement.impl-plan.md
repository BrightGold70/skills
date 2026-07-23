# Implementation Plan: preflight-read-enforcement

> Source: docs/02-design/features/preflight-read-enforcement.design.md (post-audit, v1.1)
> Branch target: feature/192-preflight-read-enforcement

## Executive Summary

Four tasks against one production file: Task 1 adds the receipt lifecycle to `env`, Task 2 adds the
conflict guard to `send`, Task 3 adds receipt enforcement to `send` and migrates the 12 existing
`send` tests onto the enforced path, and Task 4 updates the prose — with Tasks 1 and 2 mutually
independent and touching disjoint regions of the file.

## AC coverage map

36 of the spec's 37 ACs are covered by tests below. **AC-8.3 is deliberately uncovered**: "suite
pass/fail counts identical with and without a receipt at the default path" is a property *of* the
suite, and a test inside it cannot honestly assert it. It is verified in Phase 5f by running the
suite twice and comparing **counts only, never the summary line** — an elapsed-time difference in
that line produced a false negative on the previous feature.

| Task | ACs |
|---|---|
| Task 1 | AC-1.1–1.5, AC-2.1–2.3, AC-8.1, AC-8.2, AC-8.4 (11) |
| Task 2 | AC-7.1–7.4 (4) |
| Task 3 | AC-2.4, AC-3.1–3.4, AC-4.1–4.4, AC-5.1–5.4, AC-6.1–6.4 (17) |
| Task 4 | AC-9.1–9.4 (4) |
| — | AC-8.3 — measured in 5f, not tested |

## Task 1: receipt-lifecycle

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: Add the receipt path resolver, the fingerprint function, and the write/clear pair,
then wire them into `_cmd_env` so a passing preflight leaves a receipt and a failing one leaves
none. The receipt path defaults to the directory of the pin file in effect, which is what gives the
existing test harness isolation for free. Nothing in this task reads the receipt — enforcement is
Task 3 — so `env`'s observable stdout contract is unchanged and no existing test can regress.

**Code structure**:
```bash
# Path to the preflight receipt. Anchored to the pin file's directory so that a
# caller isolating HMAD_ORCA_PIN_FILE isolates the receipt too (test harness
# already does this per-invocation); an explicit override wins outright.
_receipt_file() {  # -> path
  printf '%s\n' "${HMAD_PREFLIGHT_RECEIPT_FILE:-$(dirname "$(_pin_file)")/preflight.receipt}"
}

# Deterministic identity of the current agent resolution. Deliberately NOT hashed:
# it is not a secret, a plain value is diagnosable by reading the file, and it
# avoids a shasum/sha256sum portability dependency. An unresolvable agent
# contributes the literal UNRESOLVED, so pinning one invalidates the receipt.
_fingerprint() {  # -> "codex=<v>;agy=<v>"
  local a v out=""
  for a in codex agy; do
    v="$(_resolve_target "$a" 2>/dev/null)" || v="UNRESOLVED"
    [ -n "$v" ] || v="UNRESOLVED"
    out="${out:+$out;}$a=$v"
  done
  printf '%s\n' "$out"
}

_receipt_write() {  # no args; writes verdict/fingerprint/ts
  local rf; rf="$(_receipt_file)"
  local dir; dir="$(dirname "$rf")"; [ -d "$dir" ] || mkdir -p "$dir"
  { printf 'verdict=PASS\n'
    printf 'fingerprint=%s\n' "$(_fingerprint)"
    printf 'ts=%s\n' "$(date +%s)"
  } > "$rf"
}

_receipt_clear() { rm -f "$(_receipt_file)"; }
```

Wiring in `_cmd_env`, immediately **after** the existing `echo "PREFLIGHT: ${verdict}${fields}"`
line so a write failure can never suppress or alter the token:

```bash
  echo "PREFLIGHT: ${verdict}${fields}"
  if [ "$verdict" = "PASS" ]; then _receipt_write; else _receipt_clear; fi
  return 0
```

**Acceptance Criteria**:
- [ ] AC-1.1: After an `env` run printing `PREFLIGHT: PASS`, the receipt file exists at the resolved path.
- [ ] AC-1.2: The receipt contains a `ts` parseable as an integer and a non-empty `fingerprint` value.
- [ ] AC-1.3: Two `env` runs with an identical resolved handle set write an identical `fingerprint`.
- [ ] AC-1.4: An `env` run whose stub listing resolves a different handle writes a different `fingerprint` than AC-1.3's.
- [ ] AC-1.5: The `env` run that writes a receipt still prints `PREFLIGHT: PASS` on stdout and exits 0.
- [ ] AC-2.1: From a state with no receipt, an `env` run printing `PREFLIGHT: FAIL` (stale pin) leaves no receipt file.
- [ ] AC-2.2: With a receipt already on disk, an `env` run printing `PREFLIGHT: FAIL` removes it.
- [ ] AC-2.3: The failing `env` run still prints its `PREFLIGHT: FAIL` line including the `stale=` field, and exits 0.
- [ ] AC-8.1: With `HMAD_PREFLIGHT_RECEIPT_FILE` set, the receipt is written to that path and no file appears at the pin-file-derived default.
- [ ] AC-8.2: With `HMAD_PREFLIGHT_RECEIPT_FILE` unset, the receipt is written beside the pin file in effect.
- [ ] AC-8.4: `git check-ignore -v .h-mad/preflight.receipt` reports a matching ignore rule, so the default path is untracked without any `.gitignore` change.

**Dependencies on other tasks**: None

---

## Task 2: conflict-guard

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: Refuse a dispatch when both agents resolve to the same handle — the case `_cmd_env`
already reports at `hmad-dispatch.sh:303-306` but `_send_text` cannot see. Reads resolution only, so
it needs nothing from Task 1 and edits a different region of the file.

**Code structure**:
```bash
# Two agents cannot be one pane, so equal non-empty resolutions prove at least one
# is wrong -- the exact shape a tab-inherited title produces. Not suppressed by
# HMAD_SKIP_PREFLIGHT: that bypass exists to permit dispatching without a
# preflight, not to permit dispatching into a provably wrong pane.
_preflight_conflict_check() {  # -> 0 ok, 1 conflict (message on stderr)
  local c a
  c="$(_resolve_target codex 2>/dev/null)" || c=""
  a="$(_resolve_target agy 2>/dev/null)" || a=""
  [ -n "$c" ] && [ -n "$a" ] && [ "$c" = "$a" ] || return 0
  echo "hmad-dispatch: preflight_agent_conflict — codex and agy both resolve to $c; at least one is wrong and nothing was sent. Pin them explicitly (hmad-dispatch pin <agent> <handle>)." >&2
  return 1
}
```

Wiring in `_cmd_send`, **after** the existing missing-prompt-file check (which keeps its return 2)
and before any delivery. Placed ahead of Task 3's receipt check, because a conflict is a hard
misconfiguration whose diagnostic is more useful than "you didn't run a preflight":

```bash
_cmd_send() {
  local agent="$1" promptfile="$2"
  local max="${HMAD_SEND_INLINE_MAX:-8192}"

  if [ ! -f "$promptfile" ]; then
    echo "hmad-dispatch: no such prompt file: $promptfile" >&2
    return 2
  fi

  _preflight_conflict_check || return 1     # <-- Task 2 wiring
  # (Task 3 inserts its receipt check immediately below this line)

  local size
  size=$(wc -c < "$promptfile" | tr -d ' ')
  ...
```

**Acceptance Criteria**:
- [ ] AC-7.1: When the stub listing makes `codex` and `agy` resolve to the same non-empty handle, `send` to either agent returns non-zero and the capture file records no delivery call.
- [ ] AC-7.2: That refusal prints `preflight_agent_conflict` on stderr.
- [ ] AC-7.3: When the two agents resolve to different handles, `send` is not refused for conflict — the guard discriminates rather than refusing unconditionally.
- [ ] AC-7.4: When both agents are `UNRESOLVED`, `send` is not refused for conflict (two unresolved agents are not one pane); any refusal in that scenario must name a different reason.

**Dependencies on other tasks**: None

---

## Task 3: receipt-enforcement

**Production file**: `h-mad/scripts/hmad-dispatch.sh`
**Test file**: `h-mad/tests/test_hmad_dispatch.py`

**Description**: Validate the receipt at dispatch and refuse with a distinguishable reason, add the
TTL and the bypass, and migrate the 12 existing `send` tests so they run `env` before `send` against
a shared receipt path — exercising the enforced sequence rather than bypassing it. No suite-wide
`HMAD_SKIP_PREFLIGHT` default is introduced anywhere: that would make every assertion below vacuous.

**Code structure**:
```bash
# Validate the receipt. Prints a reason token on stdout for the caller to compose
# into its stderr message; returns 0 only when the receipt exists, says PASS, is
# within the TTL, and still matches resolution NOW.
#
# Note this compares RESOLVED VALUES, not liveness: _resolve_target consults the
# env pin, then the pin file, then auto-detect, and never calls `orca terminal
# list` when a pin exists. So an unreadable listing leaves resolution unchanged
# and cannot spuriously invalidate a receipt -- the rc=2 "unknown" contract of
# _orca_handle_live is honoured structurally, with no special case.
_receipt_valid() {  # -> 0 valid; 1 + reason token on stdout
  local rf ttl now v fp ts
  rf="$(_receipt_file)"
  [ -f "$rf" ] || { echo "preflight_not_run"; return 1; }
  v="$(grep -E '^verdict=' "$rf" 2>/dev/null | head -n 1)"; v="${v#*=}"
  [ "$v" = "PASS" ] || { echo "preflight_not_run"; return 1; }
  ts="$(grep -E '^ts=' "$rf" 2>/dev/null | head -n 1)"; ts="${ts#*=}"
  case "$ts" in ''|*[!0-9]*) echo "preflight_not_run"; return 1 ;; esac
  ttl="${HMAD_PREFLIGHT_TTL_SEC:-3600}"
  now="$(date +%s)"
  [ "$(( now - ts ))" -le "$ttl" ] || { echo "preflight_expired"; return 1; }
  # strip through the FIRST '=' only: the value itself contains '='
  fp="$(grep -E '^fingerprint=' "$rf" 2>/dev/null | head -n 1)"; fp="${fp#*=}"
  [ "$fp" = "$(_fingerprint)" ] || { echo "preflight_handles_rotated"; return 1; }
  return 0
}
```

Wiring in `_cmd_send`, after the existing prompt-file check and after the Task-2 conflict check:

```bash
  if [ -n "${HMAD_SKIP_PREFLIGHT:-}" ]; then
    echo "hmad-dispatch: HMAD_SKIP_PREFLIGHT set — dispatching without a preflight receipt." >&2
  else
    local _reason
    if ! _reason="$(_receipt_valid)"; then
      echo "hmad-dispatch: $_reason — no valid preflight receipt for this dispatch; nothing was sent. Run 'hmad-dispatch env' and confirm 'PREFLIGHT: PASS', then retry." >&2
      return 1
    fi
  fi
```

**Acceptance Criteria**:
- [ ] AC-2.4: A `send` attempted immediately after an `env` run that printed `PREFLIGHT: FAIL` is refused.
- [ ] AC-3.1: With no receipt at the resolved path, `send` returns non-zero.
- [ ] AC-3.2: With no receipt, the `HMAD_STUB_CAPTURE` file records **no** delivery call — asserted against the absence of the call, not merely the exit code.
- [ ] AC-3.3: The refusal names `preflight_not_run` when the receipt is absent, `preflight_expired` when past the TTL, and `preflight_handles_rotated` on fingerprint mismatch — each on stderr, each distinct.
- [ ] AC-3.4: With a valid receipt, `send` delivers, and the size-based inline-vs-file-indirection selection is unchanged (a small prompt inlines, one over `HMAD_SEND_INLINE_MAX` sends the read-this-path instruction).
- [ ] AC-4.1: After a valid `env`, changing the stub listing so an agent resolves to a different handle causes the next `send` to be refused with `preflight_handles_rotated`.
- [ ] AC-4.2: A receipt written while `agy` was `UNRESOLVED` is invalidated once `agy` is pinned to a handle.
- [ ] AC-4.3: Re-running `env` after the change writes a receipt that permits the dispatch, with no manual edit of the receipt file.
- [ ] AC-4.4: With handles unchanged between `env` and `send`, the dispatch is **not** refused — the guard discriminates.
- [ ] AC-5.1: A receipt whose `ts` is older than the TTL causes refusal with `preflight_expired`.
- [ ] AC-5.2: A receipt within the TTL whose fingerprint matches permits the dispatch.
- [ ] AC-5.3: `HMAD_PREFLIGHT_TTL_SEC` is honoured — a receipt older than a small explicit TTL is refused, and the same receipt passes under a large one.
- [ ] AC-5.4: With `HMAD_PREFLIGHT_TTL_SEC` unset, a receipt aged 3500s is accepted and one aged 3700s is refused, demonstrating the 3600 default rather than an error or an unbounded window.
- [ ] AC-6.1: With `HMAD_SKIP_PREFLIGHT=1` and no receipt present, `send` delivers.
- [ ] AC-6.2: A bypassed `send` prints a notice naming the bypass on stderr.
- [ ] AC-6.3: With `HMAD_SKIP_PREFLIGHT` unset **and** with it set to the empty string, `send` is enforced — the default is fail-closed and an empty assignment does not enable the bypass.
- [ ] AC-6.4: With `HMAD_SKIP_PREFLIGHT=1` set **and** both agents resolving to one handle, `send` is still refused with `preflight_agent_conflict`.

**Dependencies on other tasks**: Task 1 (needs `_receipt_file`/`_fingerprint`/`_receipt_write`), Task 2 (shares the `_cmd_send` call site)

---

## Task 4: docs-machinery

**Production file**: `h-mad/SKILL.md`
**Test file**: `h-mad/tests/test_h_mad_preflight_docs.py`

**Description**: Update the Phase-5 preflight prose so it states the enforced behavior rather than a
mandated-read obligation the code now guarantees, and document the receipt plus its three
environment variables in `references/agent-substrate.md`. Assertions extend the existing
doc-mandate test module added by Wave 2.

**Code structure**:
```python
# Extends h-mad/tests/test_h_mad_preflight_docs.py, whose existing module
# constants are reused rather than redefined.
def test_skill_states_send_refuses_without_receipt() -> None: ...
def test_skill_documents_each_refusal_reason_and_recovery() -> None: ...
def test_agent_substrate_documents_receipt_and_env_vars() -> None: ...
def test_skill_frontmatter_still_valid() -> None: ...
```

**Acceptance Criteria**:
- [ ] AC-9.1: `h-mad/SKILL.md` states that a dispatch refuses without a valid receipt and names all four reason tokens (`preflight_not_run`, `preflight_expired`, `preflight_handles_rotated`, `preflight_agent_conflict`).
- [ ] AC-9.2: For each of those four tokens, `SKILL.md` gives an actionable recovery step.
- [ ] AC-9.3: `h-mad/references/agent-substrate.md` documents the receipt artifact and all three variables (`HMAD_PREFLIGHT_RECEIPT_FILE`, `HMAD_PREFLIGHT_TTL_SEC`, `HMAD_SKIP_PREFLIGHT`).
- [ ] AC-9.4: `h-mad/SKILL.md` frontmatter still parses with non-empty `name` and `description` (project Axis B, skill manifest integrity).

**Dependencies on other tasks**: Task 1, Task 2, Task 3 (the prose must name the tokens as shipped)

---

## Version History
- v1.0: Initial implementation plan draft.
- v1.1: Cycle-1 audit response. **Should-fix:** added the explicit `_cmd_send` wiring block to
  Task 2, which previously described its call site in prose while Tasks 1 and 3 showed theirs —
  the snippet also fixes the guard ordering relative to Task 3 in one place rather than leaving it
  implied. **Nit:** `head -1` → `head -n 1` (3 occurrences) for POSIX-standard syntax. Note the
  wrapper already contains 4 `head -1` sites (`hmad-dispatch.sh:65,102,173,574`); those are left
  untouched as out of scope, so new code is POSIX-strict while pre-existing code is unchanged.
