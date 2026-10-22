# grok-audit-surface — Task 14d gate result

**Date:** 2026-10-23 · **SHA:** `9f8c96c68836f734fe39b904a87da59169012f53` (Tasks 14a–14c landed)
**Interpreter:** `/opt/anaconda3/bin/python3.11`, pytest 9.1.1

| AC | Result | Reading |
|---|---|---|
| AC-T14d.1 | MET | pytest 9.1.1; full `h-mad/tests`: `7300 passed, 4 warnings in 2525.46s` |
| AC-T14d.2 | MET | `MUTATION: ALL_CAUGHT mutations=421 caught=421 survived=0 refused=0 unreadable=0 crash_kills=0 … untargeted=0/421`; `ANCHORS: ANCHORS_OK specs=1 mutations=421 ok=421` |
| AC-T14d.3 | MET | anchor loop over specs naming the three scripts: `specs=34 not_ok=0` |
| AC-T14d.4 | MET | matching lines: `M:PATH-SCOPE-` assembler 2, wrapper 6; `# M:ASSEMBLER-` 19; rows 421 (378 + 6 + 10 + 27) |
| AC-T14d.5 | **NOT MET (load-sensitive)** | assembler-pin module `33 passed in 2.03s` (met). Path-scope module under `-x`: `21 passed in 36.41s` in the gate run, then `45.70s` and `17.06s` re-measured back to back at load average ~9 (other sessions' mutation harnesses running). Its two real-cycle ids measured 6.98 s and 6.92 s. |

## AC-T14d.5 — what it means

The module is ~17 s on an idle machine and crosses the judge's 40 s `JUDGE_BUDGET_S` under
concurrent load. The judge maps `h-mad/scripts/h_mad_assemble_audit.py` to this module, so a later
production write to the assembler on a loaded machine can be refused with `kind=timeout`. Per the
AC's own rule this is reported against Task 14d, not accepted for being under 40 s on a quiet run.
`hmad-dispatch.sh` (Task 14b's file) is `.sh` and not judged, so only the assembler is exposed.

Options (operator decision): (a) accept as a recorded environmental limit, since Task 14a's code is
already landed and no further assembler write is planned before Task 15; (b) split the two real-cycle
ids (~14 s together) into their own module so the judged module stays well under budget.

## Other notes from Tasks 14a–14c (for the Phase-6 reader)

- Task 14a: codex's GREEN spliced its mutation rows into the spec as a nested array with a stray
  `+`; the orchestrator flattened it, rows unchanged.
- Task 14b: two RED-commit test defects fixed at GREEN (a nonexistent script dir for `[assemble_halt]`;
  WIRE-PIN 2's prompt-path parse broke on a space, so its RED failed for that reason). The append-only
  `implementation_authors` lists `claude` last for `path_scope_wire` because of the orchestrator's
  test-parse fix — not an implementation write.
- Task 14c: first GREEN reverted after an agy DRIFT review; second GREEN COMPLIANT. Operator-accepted
  deviation: `status_dir = here.parent if here.name == "scripts" else here` (the plan's
  `git -C <here>/..` contradicts its own sha256 fixture; production `here` is always `…/h-mad/scripts`).
- Dispatch friction (tooling, todo #6): the Phase-5 gates refused codex's `graft`/`rg`/`git`/`--check-anchors`
  and agy's `read_file`/`git`/`pytest`; every dispatch needed a preface naming the admitted read path.
