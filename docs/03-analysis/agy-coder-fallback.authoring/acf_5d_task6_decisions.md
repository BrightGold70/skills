# agy-coder-fallback — 5d Task 6 record

Gates (outside sandbox): test file `66 passed`; `--self-check` PASS; `agy_tdd_gate.json` 16 rows
(5 Task 5 + 11 Task 6, all with `symbol`) `ANCHORS_OK`, `MUTATION: ALL_CAUGHT` 16/16, `crash_kills=0`.
Revert probe (HEAD gate) → `24 failed, 42 passed` = RED split.

Discriminators, applied by hand from the spec's find/replace:
- `od2-directory-target-check-dropped` → `test_class_b_directory_target` `dot-active`,
  `dot-unknown`, `src-active`, `src-unknown` fail by assertion (allow where deny expected); the
  two `inactive` ids pass. AC "its active ids fail" holds (and the unknown ids too).
- `fr4-class-b-target-presence-only` → exactly `number-inactive` and `list-inactive` fail, by
  assertion (deny `judge-error` where allow expected). I1 holds.
