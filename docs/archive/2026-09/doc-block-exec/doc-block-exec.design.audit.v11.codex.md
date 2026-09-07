## Summary
All 48 source-spec acceptance criteria are addressed as written; the Axis C matrix below therefore has no `restated` or `absent` rows. The design nevertheless has three hard execution-contract gaps: an untrue permission guarantee, a planned process leak on the reap-error path, and an undefined `--subst` input grammar.

| Spec ACs | Classification | Design coverage |
|---|---|---|
| AC-1.1–AC-1.9 | implemented-as-written | Tagged, heading-scoped scan/selection and shared bounder are specified. |
| AC-2.1–AC-2.7 | implemented-as-written | Literal, counted substitution and overlap refusal are specified. |
| AC-3.1–AC-3.14 | implemented-as-written | Disposable execution, streams, preamble, UTF-8, and cleanup are specified. |
| AC-4.1–AC-4.6 | implemented-as-written | Verdict mapping and operational-error handling are specified. |
| AC-5.1–AC-5.6 | implemented-as-written | Pre-spawn validation and bounded process-group timeout handling are specified. |
| AC-6.1–AC-6.6 | implemented-as-written | The single tag, selective migration, and bidirectional wire pins are specified. |

## Must-fix
- `mkdtemp()` does not itself guarantee the required `0o700` mode — the design says `mkdtemp(0700)` / “mode 0700 by construction,” while AC-3.13 requires the actual cwd to be `0o700`. The local throwaway control `umask 777; tempfile.mkdtemp()` produced mode `0o0`; specify and test `os.chmod(cwd, 0o700)` before spawn, including the pre-spawn operational-error mapping and cleanup if that chmod fails. Otherwise the stated AC is environment-dependent and the load-bearing assumption is false.
- The specified non-ESRCH reap path and its test orphan the process they create — on `os.killpg(...)=PermissionError`, `run_block` “closes the pipes” and “does not `wait()`,” while the AC-4.6 test monkeypatches `os.killpg` to raise, so no real signal is sent. CPython `Popen.__del__` only retains a live child in its internal active list; it does not kill it. Add an explicit, verified teardown/reap strategy for this fault-injected test and define the production containment/diagnostic policy for a genuinely unsignalable group; otherwise the feature’s timeout-error test recreates the orphan-process incident it cites and leaves a launched run alive after return.
- `--subst` has no defined parser/error contract for malformed or repeated values — the CLI promises `--subst K=V` and says only unknown options or missing values may bypass `DOCBLOCK:`, but neither the verdict table nor error mapping says what `--subst K`, `--subst =V`, or two `--subst K=...` values do. A naïve split can traceback and a dict overwrite silently picks an order-dependent value. Define the exact split-once/empty-key policy and duplicate-key refusal (with a verdict, registry row, and tests) before constructing the mapping, so every supplied readable value produces the promised single verdict before reservation or spawn.

## Should-fix
None

## Nit
None
