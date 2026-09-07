# doc-block-exec — Phase 5c baseline record

**Branch**: `feature/doc-block-exec` (created from `main` at `ce9ffe1`)
**Date**: 2026-09-06
**Session**: `93d3d858`

Phase 5b exited at `4512615` on the operator's round-cap decision (r19 = last document
round; gating-decision sheet r18 C8/C10). This file records the measurements AC-6.4
requires to be **re-measured at 5c branch time rather than copied from the impl-plan**,
and the derivations the impl-plan says are re-derived here rather than transcribed.

## 1. Full-suite green, before any RED

`/opt/anaconda3/bin/python3.11 -m pytest h-mad/tests -q -p no:cacheprovider` at `ce9ffe1`:

```
2617 passed in 384.05s (0:06:24)
```

Bare `python3` on this box is 3.14 and has no pytest; the pinned interpreter is
`/opt/anaconda3/bin/python3.11`.

## 2. AC-6.4 collection floor — re-measured, NOT copied

The impl-plan pins `2748` (repository root) and `2486` (from `h-mad/`) at `b7d0d77`,
both labelled INHERITED-UNVERIFIED there, and states the constant is re-measured at 5c.
Re-measured at `ce9ffe1`:

| cwd | command | impl-plan (`b7d0d77`) | 5c (`ce9ffe1`) |
|---|---|---|---|
| repository root | `python3.11 -m pytest --collect-only -q -p no:cacheprovider` | 2748 | **2879** |
| `h-mad/` | same command | 2486 | **2617** |

Both moved by exactly +131, which is growth in the tree between the two commits and is
**expected drift, not a finding** (the impl-plan says so in AC-6.4's own words). The
repository-root number is the constant AC-6.4's floor uses; `2617` is never a substitute
for it. `2879` is the figure a 5d/5e implementer takes forward.

## 3. Module-level glob-fed parametrize sources — re-derived

The impl-plan's AST-walk verdict (at `a8e0372` / `335f535`) is **7 module-level, 21
in-body** `.glob`/`.rglob` calls across `h-mad/tests`, `handoff/tests` and
`handoff/scripts`. Re-run here at `ce9ffe1` with the same walk (a call is module-level
when its line is not inside any `FunctionDef`/`AsyncFunctionDef`):

```
module-level 7
   h-mad/tests/test_h_mad_audit_cycle.py:18
   h-mad/tests/test_h_mad_audit_cycle.py:19
   h-mad/tests/test_h_mad_audit_cycle.py:23
   h-mad/tests/test_h_mad_portable_timeout.py:158
   h-mad/tests/test_h_mad_portable_timeout.py:159
   h-mad/tests/test_h_mad_portable_timeout.py:160
   h-mad/tests/test_h_mad_portable_timeout.py:161
in-body 21
```

Identical to the impl-plan's reading. So the two module-level glob-fed parametrize
sources are unchanged:

- `_SCANNED` (`test_h_mad_portable_timeout.py:153`), consumed by **two**
  `@pytest.mark.parametrize("path", _SCANNED, ...)` at `:165` and `:295`.
  `h-mad/scripts/*.py` holds **37** files at `ce9ffe1`; that file collects **162** nodes
  (the impl-plan read 160 at `335f535` — the delta is the two scripts added since).
  Task 1 writes `h_mad_doc_block_exec.py` into that glob, so each of the two
  parametrised tests gains one node → **+2**.
- `REAL_AUDIT_REPORTS` (`test_h_mad_audit_cycle.py:15`), sliced `[:8]` and still
  saturated → **+0**. Its globs are under `docs/`, which this feature's landed source
  does not write.

No third module-level glob-fed source has appeared. The `+ 9` derivation (6 direct + 1
new module + 2 parametrised) therefore stands at 5c; membership is still decided by the
spec's AC-6.4 rule, not by this file.

## 4. Baseline sha note

`h_mad_baseline_sha.py` derives the 5c sha as the branch's FIRST commit and vouches it
only when that commit touches an impl-plan. The impl-plan and its audit sidecars were
already committed on `main` before this branch existed, so this branch's first commit is
**this file** and the script will report `BASELINE: UNVERIFIED reason=no_impl_plan
candidate=<sha>`. That candidate IS the 5c sha: `UNVERIFIED` here reports the protocol
assumption not holding, not a wrong value. 5f and 6a-prime take the sha of the commit
that adds this file.
