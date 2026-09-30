# Live smoke: multi-host-runtime (FR-11, V-11.1–V-11.5)

**Date:** 2026-10-01
**HEAD:** `58344684` (main; mhr merged and pushed 2026-09-29)
**Operator approval:** 2026-10-01, post-merge variant, all three hosts.

## Why a post-merge variant

The plan's smoke script (plan §"The smoke script") was written as a pre-push gate. Its part 1
halts on `integration already pushed`, and its `recover()` reverts every commit in `PRE..HEAD`.
After the merge and push, part 1 cannot pass, and running `recover()` would revert `main`.

The variant keeps part 2 as written: the pinned prompt, the `hmad-dispatch exec` call, and the
V-11.3/V-11.2/V-11.1 assertions in the same order. It also keeps part 1's host checks: the loader
symlink resolves to this `h-mad`, the adapter exists, and the prompt does not name the adapter.
It drops the pre-merge preconditions and `recover()`, so a failure reverts nothing.

The script was run from the session scratchpad and not committed. It is `smoke_postmerge.sh`
(plan part 2 with those removals).

## Results

| Host | Version | rc | Elapsed | V-11.3 tree + state sha | V-11.2 status | V-11.1 adapter read | V-11.4 session id | V-11.5 cost |
|---|---|---|---|---|---|---|---|---|
| codex | codex-cli 0.159.0 | 0 | 77 s | PASS | PASS | **UNVERIFIED**: codex input shape unobserved | `CODEX_THREAD_ID` set | 102,937 tokens |
| agy | 1.2.14 | 0 | 436 s | PASS | PASS | **FAIL**: no adapter read | `ANTIGRAVITY_CONVERSATION_ID` set | not reported |
| grok | 1.0.41 (4220f3b224a6) | 0 | 232 s | PASS | PASS | PASS | `GROK_SESSION_ID` set | 1,538 in / 1,913 out (93,952 cache read) |

All three hosts ended with the required line, which matches the state record:
`HMAD-STATUS feature=multi-host-runtime last_completed_phase=7 halt_reason=null`.

The tree was clean before and after every run. **None of the three changed the tree or the
state file**, so V-11.3 passed on every host.

## Reading the two non-passes

- **codex V-11.1 UNVERIFIED.** This is the residual the design documents. The codex log does
  not record which inputs codex read, so `smoke_assert.py v111` returns UNVERIFIED rather than
  PASS or FAIL. The mhr report records that a codex fix which invented a log format for this
  was discarded, and the residual was pinned instead. Unchanged.
- **agy V-11.1 FAIL `no adapter read`.** This is the verdict the mhr rehearsal predicted: see the
  mhr report §"The replay-agy rehearsal verdict", rated CHANGED/LOW. The live output shows why.
  agy answered by reading `docs/.bkit-memory.json` directly and never loaded
  `h-mad/references/agy-runtime.md`. The status it reported was still correct, and it made no
  writes. The open question is whether agy should be required to load its adapter for a
  read-only status call. It is a design question, not a regression.

## Verdict

FR-11 is exercised live on all three hosts:

- 3 of 3 are read-only: V-11.3 passed everywhere.
- 3 of 3 report the status correctly: V-11.2 passed everywhere.
- 3 of 3 report their session-id variable: V-11.4.
- Cost is reported where the host provides it: V-11.5.
- V-11.1 (adapter read) passed on grok only. It is unverifiable on codex by design, and it fails
  on agy exactly as the rehearsal predicted.
