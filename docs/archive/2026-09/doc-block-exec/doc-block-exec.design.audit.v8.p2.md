## Summary
The design robustly handles time bounds, shell mode enforcement, stream artifacts, and mutation verification for the doc-block-exec feature. It successfully adopts the single authoritative bounder strategy and properly isolates process groups. However, there are two `Must-fix` contradictions regarding the API signature of `run_block` and the sequential ordering of validation steps in `main` that must be resolved to ensure the implementation matches the specified stream-reservation safety guarantees.

| AC | Classification |
|---|---|
| AC-1.1 | implemented-as-written |
| AC-1.2 | implemented-as-written |
| AC-1.3 | implemented-as-written |
| AC-1.4 | implemented-as-written |
| AC-1.5 | implemented-as-written |
| AC-1.6 | implemented-as-written |
| AC-1.7 | implemented-as-written |
| AC-1.8 | implemented-as-written |
| AC-1.9 | implemented-as-written |
| AC-2.1 | implemented-as-written |
| AC-2.2 | implemented-as-written |
| AC-2.3 | implemented-as-written |
| AC-2.4 | implemented-as-written |
| AC-2.5 | implemented-as-written |
| AC-2.6 | implemented-as-written |
| AC-2.7 | implemented-as-written |
| AC-3.1 | implemented-as-written |
| AC-3.2 | implemented-as-written |
| AC-3.3 | implemented-as-written |
| AC-3.4 | implemented-as-written |
| AC-3.5 | implemented-as-written |
| AC-3.6 | implemented-as-written |
| AC-3.7 | implemented-as-written |
| AC-3.8 | implemented-as-written |
| AC-3.9 | implemented-as-written |
| AC-3.10 | implemented-as-written |
| AC-3.11 | implemented-as-written |
| AC-3.12 | implemented-as-written |
| AC-3.13 | implemented-as-written |
| AC-3.14 | implemented-as-written |
| AC-4.1 | implemented-as-written |
| AC-4.2 | implemented-as-written |
| AC-4.3 | implemented-as-written |
| AC-4.4 | implemented-as-written |
| AC-4.5 | implemented-as-written |
| AC-5.1 | implemented-as-written |
| AC-5.2 | implemented-as-written |
| AC-5.3 | implemented-as-written |
| AC-5.4 | implemented-as-written |
| AC-5.5 | implemented-as-written |
| AC-5.6 | implemented-as-written |
| AC-6.1 | implemented-as-written |
| AC-6.2 | implemented-as-written |
| AC-6.3 | implemented-as-written |
| AC-6.4 | implemented-as-written |
| AC-6.5 | implemented-as-written |
| AC-6.6 | implemented-as-written |

## Must-fix
- Contradictory `run_block` API and substitution order — The design states that `main` reserves stream artifacts "After every other refusal has passed — including substitution", meaning `substitute` (and its potential `SUBST_MISSING` / `SUBST_OVERLAP` refusals) must run before `open()`. However, the `run_block` signature accepts `subs: Mapping[str, str]` instead of the substituted text, implying `run_block` performs the substitution itself. If `run_block` does the substitution, it happens *after* `main` has reserved the streams (since `run_block` spawns the process), violating the guarantee. Fix: change `run_block` to accept the pre-substituted `text: str` instead of `subs`, so `main` can safely call `substitute` before reserving streams and pass the result to `run_block`.
- Contradictory validation sequence in `main` — The architecture overview states: "The order in main is extract → select → substitute → validate (info string, index, timeout, preamble, alias) → reserve → spawn". This presents info-string and index validation as occurring together in step 4. However, the API section correctly specifies that `BadInfoString` is raised by `extract` (step 1) and `BadIndex` is raised by `select` (step 2). Fix: correct the `main` sequence description to reflect that `info string` and `index` validation happen intrinsically during `extract` and `select`, rather than as a deferred block of validations after `substitute`.

## Should-fix
None

## Nit
None
